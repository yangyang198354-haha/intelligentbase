"""单元测试层 —— REV-19 增量（每项目专家集隔离 / 定义文档目录化 / 新项目种子）
**REV-20 修订**（ADR-48 / ADR-50 / ADR-51）：默认三专家机制退役、内置注册表收敛为唯一
通用 `kb-agent`、`seed_project` 新增提示词落盘子步。

覆盖 `architecture_design.md` ADR-43 ~ ADR-47（REV-20 由 ADR-48/50/51 修订承接）与
`module_design.md` IFC-IB-378 ~ IFC-IB-392 的**纯函数 / 结构 / 语义**层（离线，无 HTTP、无外部 IO）：

  * `ExpertRegistryView`（IFC-IB-379）的**类型层不变量**（`default_expert` 必填非空、无跨项目字段）；
  * `resolve_expert_registry`（IFC-IB-380）**fail-closed**（空集 / 缺默认 / 默认非唯一 → `ExpertRegistryError`，
    **无跨项目 / 全局回退**）—— AC-IB-41-02 / AC-IB-41-05；
  * `builtin_default_registry`（IFC-IB-381）新建项目种子 = **恰 1 个** KB agent（内置不可删）—— AC-IB-44-04；
  * **契约翻转（REV-20 / ADR-50）**：`builtin_expert_registry` 与 `builtin_default_registry`
    **同值** = 唯一 `kb-agent`（原 demo 三专家退役）；
  * `IntentRouter(experts=…)`（IFC-IB-382）**只在本项目专家集内**路由、永不无人应答、
    不再存在「demo 专属专家」这一概念 —— AC-IB-43-01 / 43-02 / 43-03；
  * `FileDefinitionDocumentStore` 目录化 `_path_for` 与按项目 round-trip（IFC-IB-383）—— AC-IB-42-02 / 42-03 / 42-04；
  * `migrate_legacy_definition_file`（IFC-IB-384，C-IB-46）—— AC-IB-42-04；
  * `migrate_expert_history`（IFC-IB-386，C-IB-47）归属改写 + 记录保留 + 幂等
    （**REV-20：默认 `experts=()` 空元组，迁移口径停用，仅保留显式调用的能力**）—— AC-IB-45-04；
  * `seed_project`（IFC-IB-385 / 390）按项目落地 + 提示词落盘 + 单一默认编排流 —— AC-IB-44-01 / 44-03 / 44-06。

凭据纪律：全程无任何真实 token / key / 口令；定义文档只含键名 / 专家名。
离线纪律：`tempfile` 临时目录 + 内存替身，不触网、不碰生产路径。
"""

from __future__ import annotations

import dataclasses
import os
from dataclasses import fields

import pytest

from ib.core import (
    DerivedView,
    ExpertRegistryError,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    Scope,
)
from ib.experts import (
    ExpertRegistryView,
    builtin_default_registry,
    builtin_expert_registry,
    resolve_expert_registry,
)

#: REV-20（ADR-50）**已退役**的三专家（FreeArk 对齐集）——
#: 仅用于「已退场」的反向断言，与 ADR-46 迁移能力的显式参数。
_RETIRED_DEMO_EXPERTS = ("freeark-expert", "inspection-expert", "sanheng-knowledge")

#: 一份最小可用的编排规格（路由纯函数不消费它以做决策，仅需合法占位）。
_GRAPH = OrchestrationSpecInput(nodes=("START", "END"), conditional_edges=(), edges=())


def _spec(name: str, *, is_default: bool = False, keywords: tuple[str, ...] = ()) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}",
        keywords=keywords,
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _view(*specs: ExpertSpecInput) -> DerivedView:
    return DerivedView(experts=tuple(specs), capability_digest="", graph_config=_GRAPH)


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-001 —— AC-IB-41-03：「本项目专家集恰好一个默认专家」为类型层事实
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_001_project_registry_view_invariants() -> None:
    """US-IB-41 / AC-IB-41-03；ADR-43 / C-IB-45 / IFC-IB-379。

    「默认专家恰好一个」不依赖任何运行期校验放行 —— `default_expert` 是**必填非空字段**
    （无默认值、类型非 `Optional`），且 `resolve_expert_registry` 对「非唯一/缺失」fail-closed。
    """
    flds = {f.name: f for f in fields(ExpertRegistryView)}
    # 字段集固定：不存在指向「其他项目 / 全局」的字段（硬隔离的结构证据）。
    assert set(flds) == {"project_id", "experts", "default_expert", "by_name"}, flds
    # default_expert 必填（无默认值）且类型非 Optional。
    assert flds["default_expert"].default is dataclasses.MISSING, "default_expert 不得有默认值"
    assert "None" not in str(flds["default_expert"].type), "default_expert 不得可空"

    # 合法派生视图 → 恰一个默认专家，且不变量成立。
    view = resolve_expert_registry("p_solo", view=_view(_spec("solo", is_default=True)))
    assert view.default_name() == "solo"
    assert view.default_expert.name in set(view.names())
    assert view.names() == ("solo",)

    # 内置种子视图同样满足「恰一个」。
    seed = builtin_default_registry()
    assert sum(1 for e in seed.experts if e.is_default) == 1
    assert seed.default_expert.name in set(seed.names())


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-002 —— AC-IB-41-02 / AC-IB-41-05：专家域 fail-closed，无跨项目 / 全局回退
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_002_resolve_registry_failclosed_without_fallback() -> None:
    """US-IB-41 / AC-IB-41-02、AC-IB-41-05；REQ-NFR-IB-21 / ADR-47 / IFC-IB-380。

    三类非法派生视图一律抛 `ExpertRegistryError`（携带项目上下文 + 结构化 reason），
    **绝不**回退到全局默认（内置三专家）或其他项目 —— 这是「硬隔离、无显式共享通道」的要求。
    """
    cases = (
        ((), "empty_expert_set"),
        ((_spec("a"), _spec("b")), "default_expert_missing"),
        ((_spec("a", is_default=True), _spec("b", is_default=True)), "default_expert_not_unique"),
    )
    for specs, reason in cases:
        with pytest.raises(ExpertRegistryError) as ei:
            resolve_expert_registry("p_probe", view=_view(*specs))
        assert ei.value.project_id == "p_probe", "错误必须携带项目标识"
        assert ei.value.reason == reason, f"reason 应为结构化类别 {reason}"

    # 回退面不存在：单专家项目解析结果**恰为**该专家，而非任何全局 / 内置专家。
    ok = resolve_expert_registry("p_ok", view=_view(_spec("solo", is_default=True)))
    assert ok.names() == ("solo",)
    assert not (set(ok.names()) & set(_RETIRED_DEMO_EXPERTS)), "解析不得注入全局 / 其他项目的专家"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-003 —— AC-IB-44-04 / AC-IB-44-02：新建项目种子 = 恰 1 个 KB agent（非全局）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_003_builtin_default_seed_is_single_non_global_kb_agent() -> None:
    """US-IB-44 / AC-IB-44-04、AC-IB-44-02；OQ-IB-33(a) / ADR-45 / IFC-IB-381。

    新建项目种子视图 = **恰 1 个** 内置不可删 KB 问答 agent（`is_default=True`），
    且**不是**「三对齐专家」—— 默认专家被喂以「本项目」专家集。
    """
    seed = builtin_default_registry()
    assert len(seed.experts) == 1, "新建项目种子必须恰 1 个专家"
    assert seed.experts[0].is_default is True, "种子专家必须 is_default=True（内置不可删兜底）"
    assert seed.default_name() == "kb-agent"
    # AC-IB-44-02：不与已退役三专家重叠（REV-20 / ADR-50）。
    assert not (set(seed.names()) & set(_RETIRED_DEMO_EXPERTS))


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-004 —— **契约翻转（REV-20 / ADR-50）**：demo 三专家机制退役，
#                     `builtin_expert_registry` 与 `builtin_default_registry` 同值
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_004_builtin_expert_registry_equals_default_single_kb_agent() -> None:
    """US-IB-45（原「demo 项目含三对齐专家」）；**REV-20 / OQ-IB-46=B / OQ-IB-47=C / ADR-50**。

    契约翻转：原 REV-19/ADR-31 口径下 `demo` 项目专家集 = FreeArk 三对齐专家；REV-20 起
    「默认三专家」机制**整体退役**，`builtin_expert_registry()` 与 `builtin_default_registry()`
    **同值** = 唯一通用 `kb-agent`（`demo` 亦改 kb-agent），且不再含任何业务域专家。
    """
    demo = builtin_expert_registry()
    assert demo.names() == builtin_default_registry().names() == ("kb-agent",)
    assert demo.default_name() == "kb-agent"
    # 已退役三专家不得出现在任何内置视图。
    assert not (set(demo.names()) & set(_RETIRED_DEMO_EXPERTS))


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-005 —— AC-IB-45-02：内置视图不含业务域专家（全隐藏）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_005_builtin_views_contain_no_business_domain_experts() -> None:
    """**契约翻转（REV-20 / OQ-IB-48=C / ADR-50）**：原口径「非 demo 项目专家集不含三专家，
    由种子差异保证三专家属 demo」；三专家退役后，本判据强化为「**任何**内置视图都不含
    业务域专家」—— 断言两个内置视图同值且与已退役集不相交。
    """
    non_demo = builtin_default_registry()
    assert not (set(non_demo.names()) & set(_RETIRED_DEMO_EXPERTS)), "内置视图不得出现业务域专家"
    # 两个内置视图逐项相同（demo 与非 demo 不再有专家集差异）。
    assert set(non_demo.names()) == set(builtin_expert_registry().names()) == {"kb-agent"}


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-006 —— AC-IB-43-01 / AC-IB-41-01：路由只在本项目专家集内
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_006_router_routes_within_project_set_only() -> None:
    """US-IB-43 / AC-IB-43-01；US-IB-41 / AC-IB-41-01；ADR-43 / IFC-IB-382。

    `IntentRouter(experts=本项目视图)` 的合法集 = 本项目专家集；无论问句命中哪类关键词，
    返回的专家恒 ∈ 本项目集（不跨项目）。
    """
    from ib.routing import IntentRouter

    view = builtin_default_registry()  # 仅 kb-agent
    router = IntentRouter(experts=view)
    for q in ("帮我查知识库的资料", "巡检 PLC 故障", "三恒恒温原理", "能耗看板", "随便聊聊"):
        d = router.classify_experts(q, scope=Scope(project_id="p_new"))
        assert d.experts, "路由不得返回空（本项目必有一个默认专家）"
        assert set(d.experts) <= set(view.names()), f"路由越出本项目专家集：{d.experts}"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-007 —— AC-IB-43-02：任一级失败 → 回落本项目默认专家（绝不无人应答）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_007_router_never_without_answer_falls_back_to_project_default() -> None:
    """US-IB-43 / AC-IB-43-02；REQ-FUNC-IB-19 / C-IB-45。

    零信号问句（无关键词命中、无粘性）→ 回落**本项目**默认专家，**绝不返回空**。
    """
    from ib.routing import IntentRouter

    view = builtin_default_registry()
    router = IntentRouter(experts=view)  # 无 llm / 无语义 → 强制走默认兜底
    d = router.classify_experts("今天天气真好随便聊聊", scope=Scope(project_id="p_new"))
    assert d.experts == [view.default_name()], f"应回落本项目默认专家，实为 {d.experts}"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-008 —— AC-IB-43-03：路由不调用任何业务域专家（三专家已退役）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_008_router_never_invokes_business_domain_experts() -> None:
    """**契约翻转（REV-20 / ADR-50）**：原口径「非 demo 项目不调用 demo 三专家，
    对照组（未注入视图）会命中 `inspection-expert`」；三专家退役后，对照组的全局注册表
    亦只有 `kb-agent`，故**注入与未注入都恒为 kb-agent**（不再存在业务域专家可命中）。
    """
    from ib.routing import IntentRouter

    view = builtin_default_registry()  # 唯一 kb-agent
    d = IntentRouter(experts=view).classify_experts("巡检一下 PLC 故障", scope=Scope(project_id="p_x"))
    assert not (set(d.experts) & set(_RETIRED_DEMO_EXPERTS)), f"调用了已退役三专家：{d.experts}"
    assert d.experts == ["kb-agent"]

    # 对照组：未注入视图（进程级内置注册表）同样只有 kb-agent —— 无业务域专家可命中。
    legacy = IntentRouter().classify_experts("巡检一下 PLC 故障", scope=Scope(project_id="p_x"))
    assert legacy.experts == ["kb-agent"], "全局注册表亦不含业务域专家"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-009 —— AC-IB-42-04：定义文档目录化（键名不变，值语义 = 目录）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_009_file_store_directory_semantics_path_for() -> None:
    """US-IB-42 / AC-IB-42-04；OQ-IB-32(b) / C-IB-46 / ADR-44 / IFC-IB-383。

    `FileDefinitionDocumentStore` 构造形参语义 = **目录根**；`_path_for(pid)` = `<dir>/<pid>.json`
    （一项目一文档），消除「`load(project_id)` 无视 `project_id`」的 F5 偏差。
    """
    from ib.config import FileDefinitionDocumentStore

    store = FileDefinitionDocumentStore(os.path.join("base", "defs"), known_tools=frozenset())
    p = store._path_for("proj_x")
    assert os.path.basename(p) == "proj_x.json"
    assert os.path.dirname(p) == os.path.join("base", "defs")
    # 不同项目 → 不同文件（按项目落地）。
    assert store._path_for("proj_x") != store._path_for("proj_y")


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-010 —— AC-IB-42-03 / AC-IB-42-02：按项目 round-trip 无漂移 + 写入不串项目
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_010_file_store_roundtrip_and_isolation(tmp_path) -> None:
    """US-IB-42 / AC-IB-42-03、AC-IB-42-02；REQ-FUNC-IB-25 / IFC-IB-383。

    保存项目 X 后重新载入 → 语义哈希一致（round-trip 无漂移）；项目 Y 的文件不被牵连。
    """
    from ib.config import FileDefinitionDocumentStore, build_definition_document

    def _doc(pid: str) -> object:
        return build_definition_document(
            project_id=pid,
            experts=(_spec("e1", is_default=True),),
            route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="e1"),
            orchestration=OrchestrationSpecInput(
                nodes=("route", "e1"),
                conditional_edges=(),
                edges=(),
            ),
        )

    store = FileDefinitionDocumentStore(str(tmp_path), known_tools=frozenset())
    doc_x = _doc("proj_x")
    store.save("proj_x", doc_x, expected_content_hash=None)
    loaded = store.load("proj_x")
    assert loaded.content_hash == doc_x.content_hash, "round-trip 出现漂移"

    # 项目 Y 独立：X 的写入不产生 / 不影响 Y。
    assert (tmp_path / "proj_x.json").is_file()
    assert not (tmp_path / "proj_y.json").exists()
    doc_y = _doc("proj_y")
    store.save("proj_y", doc_y, expected_content_hash=None)
    assert store.load("proj_y").content_hash == doc_y.content_hash
    assert store.load("proj_x").content_hash == doc_x.content_hash, "写入 Y 不得影响 X"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-011 —— AC-IB-42-04：C-IB-46 旧单文件 → <dir>/demo.json（含 fail-closed）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_011_migrate_legacy_definition_file(tmp_path) -> None:
    """US-IB-42 / AC-IB-42-04；C-IB-46 / ADR-44 / IFC-IB-384。

    旧单文件迁移为 `<dir>/demo.json`：先备份、再移动（非复制）；目标已存在 → **fail-closed**
    不覆盖；源缺失（已迁移）→ 幂等空跑。
    """
    from ib.config import migrate_legacy_definition_file

    legacy = tmp_path / "definition.json"
    legacy.write_text("{}", encoding="utf-8")

    res = migrate_legacy_definition_file(str(tmp_path), target_project_id="demo")
    assert res.applied is True
    assert (tmp_path / "demo.json").is_file(), "迁移产物应为 <dir>/demo.json"
    assert (tmp_path / "definition.json.bak").is_file(), "应先备份旧文件（可回滚）"
    assert not legacy.exists(), "迁移是移动，不留第二副本（单一真源）"

    # 目标已存在 → fail-closed（不静默覆盖）。
    again_src = tmp_path / "definition2.json"
    again_src.write_text("{}", encoding="utf-8")
    res2 = migrate_legacy_definition_file(
        str(tmp_path), target_project_id="demo", legacy_file=str(again_src)
    )
    assert res2.applied is False
    assert "target_exists_fail_closed" in res2.notes

    # 源缺失 → 幂等空跑。
    res3 = migrate_legacy_definition_file(str(tmp_path), target_project_id="demo")
    assert res3.applied is False and "legacy_file_absent" in res3.notes


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-012 —— AC-IB-45-04：三专家历史归属迁移（改写 + 保留 + 幂等 + 非 demo 失去可见）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_012_migrate_expert_history_reassign_retain_idempotent() -> None:
    """US-IB-45 / AC-IB-45-04；OQ-IB-40(b) / DR-23 / C-IB-47 / ADR-46 / IFC-IB-386。

    **REV-20（ADR-50）修订**：`migrate_expert_history` 的 `experts` 默认值改为**空元组**
    （迁移口径**停用** —— 三专家退役后不再有「默认待迁移集」）；本用例**显式**传入已退役
    三专家，验证**能力仍在**（显式调用时行为不变）：归属改写 + 记录保留 + 未引用者不动 + 幂等。

    引用三专家的历史会话归属改写为 `demo`（记录保留，不删除）；非 demo 项目因此失去可见；
    未引用三专家的会话不动；重复执行幂等（`applied=False`）。
    """
    import ib.streaming as streaming
    from ib.core import MigrationReport, SessionState

    store = streaming.MemorySessionStore()
    store.save("legacy:s1", SessionState(last_expert="freeark-expert", project_id="legacy"))
    store.save("legacy:s2", SessionState(last_expert="unrelated", project_id="legacy"))
    store.save("demo:s3", SessionState(last_expert="inspection-expert", project_id="demo"))
    before = len(store)

    # 默认 experts=() → 空跑（迁移口径停用）
    default_run = streaming.migrate_expert_history("demo", sessions=store)
    assert default_run.applied is False and default_run.affected_sessions == 0

    report = streaming.migrate_expert_history(
        "demo", sessions=store, experts=_RETIRED_DEMO_EXPERTS
    )
    assert isinstance(report, MigrationReport)
    assert report.applied is True and report.affected_sessions == 1
    assert report.target_project_id == "demo"
    assert len(store) == before, "迁移不得删除任何会话（隐藏 ≠ 删除）"
    # 归属改写 + 非 demo 失去可见。
    assert store.load("demo:s1") is not None and store.load("demo:s1").project_id == "demo"
    assert store.load("legacy:s1") is None, "非 demo 项目不再能看到该历史"
    # 未引用三专家的会话不动。
    assert store.load("legacy:s2") is not None
    # 幂等。
    again = streaming.migrate_expert_history(
        "demo", sessions=store, experts=_RETIRED_DEMO_EXPERTS
    )
    assert again.applied is False and again.affected_sessions == 0


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-013 —— AC-IB-44-01 / AC-IB-44-03：创建期种子按项目落地（文档 + 提示词目录）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_013_seed_project_lands_per_project(tmp_path) -> None:
    """US-IB-44 / AC-IB-44-01、AC-IB-44-03；OQ-IB-32(b) / ADR-45 / ADR-51 / IFC-IB-385 / 390。

    `seed_project` 写 `<dir>/<pid>.json`（该项目专家集）+ **提示词落盘**
    `<root>/<pid>/kb-agent/main.md`（REV-20 新增子步，IFC-IB-390）；非 demo = 内置默认单例；
    幂等（已存在不覆盖）。
    """
    from ib.config import FileDefinitionDocumentStore
    from ibweb.composition import seed_project

    defs = tmp_path / "defs"
    prompts = tmp_path / "prompts"
    res = seed_project("proj_p", definition_dir=str(defs), prompt_root=str(prompts))
    assert res.created is True
    assert res.expert_names == ("kb-agent",)
    assert (defs / "proj_p.json").is_file(), "种子须按项目落地 <dir>/<pid>.json"
    assert (prompts / "proj_p" / "kb-agent").is_dir(), "提示词目录骨架为 <root>/<pid>/<expert>/"
    # REV-20（IFC-IB-390）：创建期即落盘提示词正文（提示词正文唯一来源 = 项目目录）
    main_file = prompts / "proj_p" / "kb-agent" / "main.md"
    assert main_file.is_file(), "创建期须落盘 main.md（否则装配期 prompt_missing fail-closed）"
    assert main_file.read_text(encoding="utf-8").strip(), "落盘内容不得为空"

    doc = FileDefinitionDocumentStore(str(defs), known_tools=frozenset()).load("proj_p")
    assert [e.name for e in doc.experts] == ["kb-agent"]
    assert doc.project_id == "proj_p"

    # 幂等：第二次不覆盖。
    res2 = seed_project("proj_p", definition_dir=str(defs), prompt_root=str(prompts))
    assert res2.created is False and "already_seeded" in res2.notes


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-014 —— AC-IB-44-06：单一默认编排流（无自定义 DAG 入口）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_014_seed_has_single_default_orchestration(tmp_path) -> None:
    """US-IB-44 / AC-IB-44-06；OQ-IB-36(a) / OOS-21 / ADR-45。

    新建项目种子只携带**单一默认编排流**（`orchestration == "default"`），无用户自定义 DAG 入口。
    """
    from ibweb.composition import seed_project

    res = seed_project("proj_q", definition_dir=str(tmp_path / "d"), prompt_root=str(tmp_path / "p"))
    assert res.orchestration == "default", "种子编排必须是单一默认流"
    # 种子文档只有一个 `orchestration`（结构上不存在「多流 / DAG 列表」表达）。
    assert not hasattr(res, "orchestrations")


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-015 —— AC-IB-43-04：用本项目默认编排流程且不暴露内部分工
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_015_project_default_flow_and_hidden_internal_division() -> None:
    """US-IB-43 / AC-IB-43-04；OQ-IB-36(a) / REQ-FUNC-IB-18。

    本项目默认编排流程以**本项目默认专家**为兜底（默认流程锚点）；面向用户的流式事件
    白名单**不含**任何内部分工类别（route / expert / general 等内部节点不外流）。
    """
    from ib.streaming import USER_VISIBLE_KINDS

    view = builtin_default_registry()
    # 默认编排流程锚定本项目默认专家（不是全局 / 其他项目）。
    assert view.default_name() == "kb-agent"
    assert view.default_name() in set(view.names())

    internal = {"route", "expert", "general", "gate", "aggregate", "subtask", "plan"}
    assert not (set(USER_VISIBLE_KINDS) & internal), (
        f"面向用户的事件白名单暴露了内部分工类别：{set(USER_VISIBLE_KINDS) & internal}"
    )
