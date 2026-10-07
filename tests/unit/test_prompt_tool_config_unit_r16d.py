"""[REV-16-2 / GROUP_D] 提示词分层 · 工具授权与参数 · 两域装配闸门 · FreeArk 对齐。

本文件为**测试工程师（GROUP_D）独立补充**的单元级用例（对照 GROUP_C 的
`test_prompt_layers_r16.py`，不复述其已覆盖点），逐条溯源至 `user_stories.md`
的 AC-IB-30-* / 31-* / 32-* / 33-* / 34-* 与 `requirements_spec.md` 的
ADR-29 / ADR-30 / ADR-31 / ADR-32 / ADR-16 / ADR-15-R1 / [ARCH-ASSUMPTION-A10]。

分层依据（test_plan §2）：单函数 / 单模块纯行为 → **单元级**；不启 HTTP、不连网。
"""

from __future__ import annotations

import inspect
import os
import pathlib

import pytest

import ib.config as cfg
import ib.core as core
from ib.tools import (
    ToolRegistry,
    _bare_param,
    _param_belongs,
    build_authorized_tools,
    derive_tool_param_specs,
)
from ibweb.composition import admit, admit_two_domains

# 旧标识（硬改名前的 slug / cn_label）以「拼接 + Unicode 转义」构造，使本文件自身
# 不含这些字面量 —— 于是 §TC-UNIT-122 的仓库级扫描可把本文件也纳入而不自证其罪。
_OLD_SLUGS = ("data" + "-expert", "knowledge" + "-expert")
_OLD_LABELS = (
    "".join(map(chr, (0x6570, 0x636E, 0x7BA1, 0x5BB6))),   # 旧 cn_label：数据专家
    "".join(map(chr, (0x77E5, 0x8BC6, 0x5E93, 0x95EE, 0x7B54))),  # 旧 cn_label：知识问答
)

# --------------------------------------------------------------------------- #
# 测试夹具：一份**结构合法**的定义文档（专家名与 FreeArk 对齐后的名字一致）
# --------------------------------------------------------------------------- #


def _experts():
    # REV-17（ADR-36）：ExpertSpecInput 已不含 fallback_prompt。
    return (
        core.ExpertSpecInput(
            name="freeark-expert",
            cn_label="系统管家",
            keywords=("数据", "报表"),
            exemplars=("示例一",),
            is_data_expert=True,
            is_delegating=False,
            is_default=True,
        ),
        core.ExpertSpecInput(
            name="sanheng-knowledge",
            cn_label="三恒知识",
            keywords=("知识", "问答"),
            exemplars=("示例二",),
            is_data_expert=False,
            is_delegating=False,
            is_default=False,
        ),
    )


def _doc(*, project_id: str = "p1", grants: tuple = (), experts=None):
    experts = experts if experts is not None else _experts()
    route = core.RouteSpecInput(
        tau=0.65, margin=0.05, max_expert_steps=8, default_expert=experts[0].name
    )
    orchestration = core.OrchestrationSpecInput(
        nodes=("route", "freeark-expert", "sanheng-knowledge"),
        conditional_edges=(
            core.ConditionalEdgeSpec(
                from_node="route",
                branch_map=(("freeark-expert", "freeark-expert"), ("sanheng-knowledge", "sanheng-knowledge")),
            ),
        ),
        edges=(),
    )
    return cfg.build_definition_document(
        project_id=project_id,
        experts=experts,
        route=route,
        orchestration=orchestration,
        tool_grants=grants,
    )


def _store(doc):
    return cfg.InMemoryDefinitionDocumentStore(
        initial=doc, known_tools=frozenset({"search_knowledge"})
    )


def _two_tool_registry():
    """两台工具**共享**同名裸参数 `top_k`（用于验证跨工具参数名隔离）。"""
    registry = ToolRegistry()

    def _alpha(*, top_k: int = 3, **_: object) -> core.ToolResult:
        return core.ToolResult(ok=True, content=f"alpha:top_k={top_k}")

    def _beta(*, top_k: int = 4, **_: object) -> core.ToolResult:
        return core.ToolResult(ok=True, content=f"beta:top_k={top_k}")

    for name, impl in (("alpha", _alpha), ("beta", _beta)):
        registry.register(
            core.ToolSpec(
                name=name,
                description=f"{name} 工具",
                needs_scope=False,
                parameters={
                    "type": "object",
                    "properties": {
                        "top_k": {"type": "integer", "default": impl.__kwdefaults__["top_k"], "minimum": 1, "maximum": 50}
                    },
                    "required": [],
                },
            ),
            impl,
        )
    return registry, derive_tool_param_specs(registry)


# --------------------------------------------------------------------------- #
# ADR-31：聚合禁止标签 = 派生只读视图（结构 + 旧并新过渡并集 + cn_map）
# 溯源：AC-IB-34-01 / AC-IB-34-02（专家改名后编排图不得把专家画成聚合块）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_109_forbidden_labels_derived_view_with_transition_union():
    from ib.orchestration import AGGREGATION_FORBIDDEN_LABELS, forbidden_labels

    labels = forbidden_labels({})
    # 过渡并集：旧 ∪ 新 五个中文标签必须全部在禁止集内（改名过渡期双向拦截）
    for label in (_OLD_LABELS[0], _OLD_LABELS[1], "巡检诊断", "系统管家", "三恒知识"):
        assert label in labels
    # 结构词恒在（与业务无关）
    for structural in ("路由到", "专家", "聚合"):
        assert structural in labels

    # 派生：cn_map 的取值并入（未来再改名无需手改常量）
    assert "自定义标签" in forbidden_labels({"x": "自定义标签"})
    # 去重 + 顺序稳定（同一输入两次调用恒等；作为只读派生视图，不是可变全局态）
    assert labels == forbidden_labels({})
    assert len(labels) == len(set(labels))
    # 兼容常量即结构 ∪ 过渡并集（旧常量仍可用）
    assert set(AGGREGATION_FORBIDDEN_LABELS) == set(labels)


# --------------------------------------------------------------------------- #
# ADR-16：ValidationReport 在类型层无法表达「带病继续」
# 溯源：AC-IB-30-04（校验拒绝）、AC-IB-31-03（拒绝且既有配置不变）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_110_validation_report_has_no_bypass_fields():
    fields = set(core.ValidationReport.__dataclass_fields__)
    assert fields == {"ok", "errors"}
    for forbidden in ("force", "ignore", "warn_only", "warnOnly", "allow_partial"):
        assert forbidden not in fields


def test_TC_UNIT_111_admit_signature_frozen_and_two_domain_gate_present():
    # 既有闸门 {doc, store} 逐字冻结（保护「无 force/ignore 绕过」这一事实）
    assert set(inspect.signature(admit).parameters) == {"doc", "store"}
    # 两域聚合闸门存在且带 prompt_refs / tool_specs
    params = set(inspect.signature(admit_two_domains).parameters)
    assert {"doc", "store", "prompt_refs", "tool_specs"} <= params
    assert not (params & {"force", "ignore", "warn_only"})


# --------------------------------------------------------------------------- #
# ADR-16 / IFC-IB-353：两域聚合闸门——孤儿 / 缺兜底 / 未知参数 / 越界 / 未授权带参
# 溯源：AC-IB-30-04、AC-IB-31-03
# --------------------------------------------------------------------------- #


def test_TC_UNIT_112_admit_two_domains_rejects_cross_domain_violations():
    doc = _doc()
    store = _store(doc)

    # (a) 孤儿提示词文件：目录含未登记专家 → 拒绝
    orphan = (
        core.ExpertPromptDocumentRef(
            expert_name="ghost",
            layer="main",
            rel_path=os.path.join("root", "p1", "ghost", "main.md"),
            content_hash="",
            exists=True,
        ),
    )
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(doc, store=store, prompt_refs=orphan, tool_specs=())
    assert "prompt_orphan_file" in {i.code for i in ei.value.validation_items}

    # (b) 缺兜底：目录无 fallback.md **且** 该专家无内置兜底 → 拒绝。
    #     REV-17（ADR-36）：判据已不再来自定义文档字段（该字段已删），而来自注入的内置兜底。
    #     正常装配下 `builtin_fallbacks` 恒覆盖每个专家，故这里显式注入空映射来触发它 ——
    #     该错误码因此退化为「提示词域注入残缺」的防御性断言。
    doc_b = _doc()
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(
            doc_b, store=_store(doc_b), prompt_refs=(), tool_specs=(), builtin_fallbacks={}
        )
    assert "prompt_fallback_missing" in {i.code for i in ei.value.validation_items}

    # (b2) 反之：有内置兜底、无 fallback.md → **通过**（这正是 REV-17 要放行的场景）
    view_b = admit_two_domains(
        doc_b,
        store=_store(doc_b),
        prompt_refs=(),
        tool_specs=(),
        builtin_fallbacks={"freeark-expert": "BI", "sanheng-knowledge": "BI"},
    )
    assert all(b.resolved_from == "builtin_fallback" for b in view_b.prompt_bundles)

    # (c) 未知工具参数（spec 未声明）→ 拒绝
    bad_param = _doc(
        grants=(core.ToolGrantSpec("freeark-expert", ("search_knowledge",), (core.ToolParamValue("search_knowledge.nope", "1"),)),)
    )
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(bad_param, store=_store(bad_param), prompt_refs=(), tool_specs=())
    assert "tool_param_unknown" in {i.code for i in ei.value.validation_items}

    # (d) 越界 → 拒绝
    spec = core.ToolParamSpec(name="alpha.top_k", type="int", default="3", minimum=1.0, maximum=5.0, choices=None)
    oob = _doc(grants=(core.ToolGrantSpec("freeark-expert", ("alpha",), (core.ToolParamValue("alpha.top_k", "9"),)),))
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(oob, store=_store(oob), prompt_refs=(), tool_specs=(spec,))
    assert "tool_param_out_of_range" in {i.code for i in ei.value.validation_items}

    # (e) 未授权工具带参 → 拒绝
    unauth = _doc(grants=(core.ToolGrantSpec("freeark-expert", ("beta",), (core.ToolParamValue("alpha.top_k", "2"),)),))
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(unauth, store=_store(unauth), prompt_refs=(), tool_specs=(spec,))
    assert "tool_param_unauthorized_tool" in {i.code for i in ei.value.validation_items}


def test_TC_UNIT_113_admit_two_domains_clean_passes_and_derives_bundles():
    doc = _doc()
    view = admit_two_domains(doc, store=_store(doc), prompt_refs=(), tool_specs=())
    by = {b.expert_name: b for b in view.prompt_bundles}
    assert set(by) == {"freeark-expert", "sanheng-knowledge"}
    # 无提示词文件 → 退回**代码内置兜底**（REV-17 / ADR-36），且生效提示词恒非空（ADR-29）
    assert all(b.resolved_from == "builtin_fallback" for b in by.values())
    assert all(b.effective_prompt.strip() for b in by.values())
    # 两个专家名都在 `_DEFAULT_SPECS` 中 → 兜底取自各自的内置提示词（非通用安全网）
    from ib.experts import BUILTIN_FALLBACK_DEFAULT, builtin_fallback_for

    assert by["freeark-expert"].effective_prompt == builtin_fallback_for("freeark-expert")
    assert by["freeark-expert"].effective_prompt != BUILTIN_FALLBACK_DEFAULT


# --------------------------------------------------------------------------- #
# ADR-30：跨工具参数名隔离（限定名 `<tool>.<param>`）+ 调用方显式实参优先
# 溯源：AC-IB-31-04（工具参数随授权保存）+ REQ-FUNC-IB-39（既有工具集）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_114_cross_tool_param_name_isolation():
    registry, specs = _two_tool_registry()
    assert {s.name for s in specs} == {"alpha.top_k", "beta.top_k"}

    # 同名裸参数在两台工具间**不得串味**：只给 alpha 传值，beta 必须用自己的默认
    grants = (core.ToolGrantSpec("e", ("alpha", "beta"), (core.ToolParamValue("alpha.top_k", "9"),)),)
    by = {t.name: t for t in build_authorized_tools(grants, registry=registry, specs=specs)}
    assert by["alpha"].callable().content == "alpha:top_k=9"
    assert by["beta"].callable().content == "beta:top_k=4"  # 未泄漏 alpha 的 9

    # 反向：只给 beta 传值，alpha 用默认
    grants2 = (core.ToolGrantSpec("e", ("alpha", "beta"), (core.ToolParamValue("beta.top_k", "7"),)),)
    by2 = {t.name: t for t in build_authorized_tools(grants2, registry=registry, specs=specs)}
    assert by2["alpha"].callable().content == "alpha:top_k=3"
    assert by2["beta"].callable().content == "beta:top_k=7"

    # 调用方显式实参优先于注入值
    assert by["alpha"].callable(top_k=1).content == "alpha:top_k=1"

    # 归属谓词直证
    assert _bare_param("alpha.top_k") == "top_k"
    assert _bare_param("top_k") == "top_k"
    alpha_spec, beta_spec = registry.get("alpha").spec, registry.get("beta").spec
    assert _param_belongs("alpha.top_k", alpha_spec) is True
    assert _param_belongs("alpha.top_k", beta_spec) is False


# --------------------------------------------------------------------------- #
# [ARCH-ASSUMPTION-A10] / ADR-15-R1：提示词域开关与目录契约
# 溯源：AC-IB-33-01 / 33-02（未启用时明确提示，不静默丢失）、AC-IB-30-06
# --------------------------------------------------------------------------- #


def test_TC_UNIT_115_prompt_domain_enabled_env_toggle(monkeypatch):
    monkeypatch.delenv(cfg.EXPERT_PROMPT_ENABLED_KEY, raising=False)
    assert cfg.prompt_domain_enabled() is True  # 默认开（键名已登记）
    for off in ("false", "0", "off", "OFF", " no "):
        monkeypatch.setenv(cfg.EXPERT_PROMPT_ENABLED_KEY, off)
        assert cfg.prompt_domain_enabled() is False, off
    for on in ("1", "true", "yes", "on"):
        monkeypatch.setenv(cfg.EXPERT_PROMPT_ENABLED_KEY, on)
        assert cfg.prompt_domain_enabled() is True, on


def test_TC_UNIT_116_load_prompt_directory_base_is_file_raises(tmp_path):
    root = tmp_path / "promptroot"
    root.mkdir()
    (root / "p1").write_text("not a dir", encoding="utf-8")  # 存在但非目录
    with pytest.raises(core.DependencyUnavailableError):
        cfg.load_prompt_directory(str(root), "p1")
    # 目录不存在 → 合法空（首次运行），不是错误（区分「读不到」与「本就为空」）
    assert cfg.load_prompt_directory(str(root), "p_absent") == ()


def test_TC_UNIT_117_fs_store_save_is_atomic_and_transactional(tmp_path):
    store = cfg.FsExpertPromptStore(str(tmp_path), "p1")
    first = store.save_layer("freeark-expert", "fallback", "兜底内容", expected_hash=None)
    assert first.saved is True

    fallback_path = tmp_path / "p1" / "freeark-expert" / "fallback.md"
    main_path = tmp_path / "p1" / "freeark-expert" / "main.md"

    # 并发冲突（错误 expected_hash）→ 不保存、不落地、无 .tmp 残留
    stale = store.save_layer("freeark-expert", "main", "主内容", expected_hash="sha256:deadbeef")
    assert stale.saved is False
    assert not main_path.exists()
    leftovers = [p.name for p in (tmp_path / "p1" / "freeark-expert").iterdir() if p.name != "fallback.md"]
    assert leftovers == [], leftovers

    # 空兜底非法 → 原文件内容不变（原子性：失败不改既有文件）
    empty = store.save_layer("freeark-expert", "fallback", "   ", expected_hash=None)
    assert empty.saved is False
    assert fallback_path.read_text(encoding="utf-8") == "兜底内容"
    assert not [p for p in (tmp_path / "p1" / "freeark-expert").iterdir() if p.suffix == ".tmp"]

    # 成功替换：内容更新且无临时残留
    ok = store.save_layer("freeark-expert", "main", "主内容v1", expected_hash=None)
    assert ok.saved is True and main_path.read_text(encoding="utf-8") == "主内容v1"
    assert not [p for p in (tmp_path / "p1" / "freeark-expert").iterdir() if p.suffix == ".tmp"]

    # 目录穿越（expert_name 含 ..）→ 拒绝
    with pytest.raises(Exception):
        store.save_layer("../escape", "main", "x", expected_hash=None)


# --------------------------------------------------------------------------- #
# 单一真源纪律：工具参数参与内容哈希 + 可编辑白名单 + 数据层可往返
# 溯源：AC-IB-30-02 / AC-IB-31-02（重新读取与编辑内容一致）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_118_semantic_hash_and_whitelist_include_param_values():
    plain = _doc(grants=(core.ToolGrantSpec("freeark-expert", ("search_knowledge",)),))
    with_param = _doc(
        grants=(
            core.ToolGrantSpec(
                "freeark-expert",
                ("search_knowledge",),
                (core.ToolParamValue("search_knowledge.query", "默认查询"),),
            ),
        )
    )
    # 参数取值进入语义哈希 → 乐观并发可感知参数变更
    assert cfg.semantic_hash(plain) != cfg.semantic_hash(with_param)
    # 参数取值在白名单内（可编辑字段）
    assert "tool_grants[].param_values" in cfg.editable_field_whitelist()
    # 数据层往返保真
    rt = cfg.document_from_json("p1", cfg.document_to_json(with_param))
    assert rt.tool_grants[0].param_values == (
        core.ToolParamValue("search_knowledge.query", "默认查询"),
    )
    assert rt.content_hash == cfg.semantic_hash(with_param)
    # 旧文档（无 param_values）向后兼容 → 空元组、不报错
    legacy = cfg.document_from_json(
        "p1",
        '{"schema_version": 1, "project_id": "p1", "experts": [], "tool_grants": '
        '[{"expert_name": "x", "tool_names": ["search_knowledge"]}]}',
    )
    assert legacy.tool_grants[0].param_values == ()


# --------------------------------------------------------------------------- #
# ADR-31：专家注册表与 FreeArk 严格对齐（含专家名）+ 旧 slug 彻底退场
# 溯源：AC-IB-34-01 / 34-02 / 34-04（demo = 对齐后默认专家集）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_119_experts_registry_freeark_aligned_and_old_slugs_gone():
    import ib.experts as experts

    assert experts.names() == ("freeark-expert", "inspection-expert", "sanheng-knowledge")
    assert experts.cn_map() == {
        "freeark-expert": "系统管家",
        "inspection-expert": "巡检诊断",
        "sanheng-knowledge": "三恒知识",
    }
    assert experts.default_expert() == "freeark-expert"
    by = {s.name: s for s in experts.EXPERT_SPECS}
    # 旧 slug 必须彻底消失（硬改名，ADR-31）
    assert all(s not in by for s in _OLD_SLUGS)
    # is_data_expert 语义随名字迁移：freeark 承接「数据专家」语义
    assert by["freeark-expert"].is_data_expert is True
    assert by["sanheng-knowledge"].is_data_expert is False
    assert by["inspection-expert"].is_data_expert is True
    # 每位专家兜底恒非空（ADR-29：生效提示词永不空白）
    assert all(s.fallback_prompt.strip() for s in experts.EXPERT_SPECS)


def test_TC_UNIT_120_load_prompt_bundle_ref_exists_but_file_missing_falls_back():
    ref = core.ExpertPromptDocumentRef(
        expert_name="freeark-expert",
        layer="main",
        rel_path=os.path.join("does", "not", "exist", "main.md"),
        content_hash="sha256:stale",
        exists=True,  # 引用声称存在，但文件实际已缺（例如被外部删除）
    )
    bundle = cfg.load_prompt_bundle("freeark-expert", refs=(ref,), builtin_fallback="内置兜底")
    assert bundle.resolved_from == "builtin_fallback"
    assert bundle.effective_prompt == "内置兜底"
    assert bundle.main_prompt is None


def test_TC_UNIT_121_editing_main_layer_keeps_fallback_layer():
    store = cfg.InMemoryExpertPromptStore("p1")
    store.save_layer("freeark-expert", "fallback", "兜底v1", expected_hash=None)
    m1 = store.save_layer("freeark-expert", "main", "主v1", expected_hash=None)
    refs1 = {r.layer: r for r in store.list_refs() if r.expert_name == "freeark-expert"}
    assert refs1["main"].exists and refs1["fallback"].exists
    fb_hash_before = refs1["fallback"].content_hash

    # 仅编辑主层（AC-IB-30-03：另一层保持原值，不互相覆盖）
    m2 = store.save_layer("freeark-expert", "main", "主v2", expected_hash=m1.content_hash)
    assert m2.saved is True
    refs2 = {r.layer: r for r in store.list_refs() if r.expert_name == "freeark-expert"}
    assert refs2["fallback"].content_hash == fb_hash_before  # 兜底层未被触碰
    bundle = store.load_bundle("freeark-expert", builtin_fallback="内置")
    assert bundle.main_prompt == "主v2" and bundle.fallback_prompt == "兜底v1"
    assert bundle.resolved_from == "main_file"


# --------------------------------------------------------------------------- #
# ADR-31 改名的**仓库级证据**：旧 slug / 旧 cn_label 归零
# 溯源：AC-IB-34-01 / 34-02（严格对齐 = 旧标识不得残留）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_122_repo_grep_zero_old_slugs_and_labels():
    repo = pathlib.Path(__file__).resolve().parents[2]
    skip_dirs = {
        "node_modules", "dist", "__pycache__", ".git", ".pytest_cache",
        ".mypy_cache", ".groupd_blobs", "build", ".venv", "venv", "coverage",
    }
    code_suffixes = {".py", ".ts", ".js", ".vue", ".json", ".md", ".txt", ".html", ".css", ".yml", ".yaml", ".sh"}

    def _iter(root: pathlib.Path):
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in skip_dirs for part in p.parts):
                continue
            if p.suffix.lower() not in code_suffixes:
                continue
            yield p

    # 允许的仅有的两处：selfcheck 的反向断言（证明「旧值已退场」）+ 编排过渡并集
    slug_allowed = {repo / "src" / "scripts" / "selfcheck.py"}
    label_allowed = {
        repo / "src" / "scripts" / "selfcheck.py",
        repo / "src" / "ib" / "orchestration" / "__init__.py",
    }

    slug_offenders: list[str] = []
    label_offenders: list[str] = []
    for root in (repo / "src", repo / "tests"):
        for p in _iter(root):
            text = p.read_text(encoding="utf-8", errors="ignore")
            if any(s in text for s in _OLD_SLUGS) and p not in slug_allowed:
                slug_offenders.append(str(p.relative_to(repo)))
            if any(lbl in text for lbl in _OLD_LABELS) and p not in label_allowed:
                label_offenders.append(str(p.relative_to(repo)))

    assert slug_offenders == [], f"旧 slug 残留：{slug_offenders}"
    assert label_offenders == [], f"旧 cn_label 残留：{label_offenders}"

    # 例外不是「空洞豁免」：被允许的站点确实含旧值（反向断言/过渡并集名副其实）
    selfcheck_text = (repo / "src" / "scripts" / "selfcheck.py").read_text(encoding="utf-8")
    assert all(s in selfcheck_text for s in _OLD_SLUGS)
    assert _OLD_LABELS[0] in selfcheck_text
