"""单元测试层 —— REV-19 增量（每项目专家集隔离 / 定义文档目录化 / 新项目种子 / 三专家属 demo）。

覆盖 `architecture_design.md` ADR-43 ~ ADR-47 与 `module_design.md` IFC-IB-378 ~ IFC-IB-388 的
**纯函数 / 结构 / 语义**层（离线，无 HTTP、无外部 IO）：

  * `ExpertRegistryView`（IFC-IB-379）的**类型层不变量**（`default_expert` 必填非空、无跨项目字段）；
  * `resolve_expert_registry`（IFC-IB-380）**fail-closed**（空集 / 缺默认 / 默认非唯一 → `ExpertRegistryError`，
    **无跨项目 / 全局回退**）—— AC-IB-41-02 / AC-IB-41-05；
  * `builtin_default_registry`（IFC-IB-381）新建项目种子 = **恰 1 个** KB agent（内置不可删）—— AC-IB-44-04；
  * `builtin_expert_registry` = `demo` 三对齐专家 —— AC-IB-45-01；
  * `IntentRouter(experts=…)`（IFC-IB-382）**只在本项目专家集内**路由、永不无人应答、
    非 demo 项目不调用三专家 —— AC-IB-43-01 / 43-02 / 43-03 / 45-03；
  * `FileDefinitionDocumentStore` 目录化 `_path_for` 与按项目 round-trip（IFC-IB-383）—— AC-IB-42-02 / 42-03 / 42-04；
  * `migrate_legacy_definition_file`（IFC-IB-384，C-IB-46）—— AC-IB-42-04；
  * `migrate_expert_history`（IFC-IB-386，C-IB-47）归属改写 + 记录保留 + 幂等 —— AC-IB-45-04；
  * `seed_project`（IFC-IB-385）按项目落地 + 单一默认编排流 —— AC-IB-44-01 / 44-03 / 44-06。

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
    DEMO_EXPERT_NAMES,
    ExpertRegistryView,
    builtin_default_registry,
    builtin_expert_registry,
    resolve_expert_registry,
)

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

    # 回退面不存在：单专家项目解析结果**恰为**该专家，而非内置三专家（全局默认）。
    ok = resolve_expert_registry("p_ok", view=_view(_spec("solo", is_default=True)))
    assert ok.names() == ("solo",)
    assert not (set(ok.names()) & set(DEMO_EXPERT_NAMES)), "解析不得注入全局 / 其他项目的专家"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-003 —— AC-IB-44-04 / AC-IB-44-02：新建项目种子 = 恰 1 个 KB agent（非全局）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_003_builtin_default_seed_is_single_non_global_kb_agent() -> None:
    """US-IB-44 / AC-IB-44-04、AC-IB-44-02；OQ-IB-33(a) / ADR-45 / IFC-IB-381。

    新建项目种子视图 = **恰 1 个** 内置不可删 KB 问答 agent（`is_default=True`），
    且**不是**全局 `EXPERT_SPECS`（三对齐专家）—— 默认专家被喂以「本项目」专家集。
    """
    seed = builtin_default_registry()
    assert len(seed.experts) == 1, "新建项目种子必须恰 1 个专家"
    assert seed.experts[0].is_default is True, "种子专家必须 is_default=True（内置不可删兜底）"
    assert seed.default_name() == "kb-agent"
    # AC-IB-44-02：非全局 EXPERT_SPECS（三专家）。
    assert seed.names() != DEMO_EXPERT_NAMES
    assert not (set(seed.names()) & set(DEMO_EXPERT_NAMES))


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-004 —— AC-IB-45-01：demo 项目含三对齐专家
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_004_demo_registry_has_three_aligned_experts() -> None:
    """US-IB-45 / AC-IB-45-01；REQ-FUNC-IB-53 / 42 / ADR-45。

    `demo` 项目专家集 = `freeark-expert` / `inspection-expert` / `sanheng-knowledge`
    （与 FreeArk 100% 对齐），默认专家 = `freeark-expert`。
    """
    demo = builtin_expert_registry()
    assert demo.names() == DEMO_EXPERT_NAMES == (
        "freeark-expert",
        "inspection-expert",
        "sanheng-knowledge",
    )
    assert demo.default_name() == "freeark-expert"


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-005 —— AC-IB-45-02：非 demo 项目专家集不含三专家（全隐藏）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_005_non_demo_registry_excludes_three_experts() -> None:
    """US-IB-45 / AC-IB-45-02；OQ-IB-35(a) / ADR-45。

    由「新建项目种子」解析出的非 demo 项目视图**不含**三专家中任何一个 —— 由**种子差异**
    在结构上保证「三专家属 demo」，而非任何 UI 约定。
    """
    non_demo = builtin_default_registry()
    assert not (set(non_demo.names()) & set(DEMO_EXPERT_NAMES)), "非 demo 项目不得出现三专家"
    # 与 demo 视图逐项不同（隐藏 ≠ 只是「不可见」，而是**不在集合内**）。
    assert set(non_demo.names()) != set(builtin_expert_registry().names())


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
# TC-UNIT-R19-008 —— AC-IB-43-03 / AC-IB-45-03：非 demo 不调用三专家
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_008_router_does_not_invoke_demo_experts_in_non_demo() -> None:
    """US-IB-43 / AC-IB-43-03；US-IB-45 / AC-IB-45-03；OQ-IB-34(a) / ADR-43。

    在非 demo 项目中提一个「本应由 demo 专属专家处理」的问题（命中 `巡检` / `三恒` / `能耗`）——
    **不调用** demo 专家，由本项目专家集处理；对照组（未注入视图的 legacy 路由器）会命中
    `inspection-expert`，证明该问句本可触发 demo 专家。
    """
    from ib.routing import IntentRouter

    view = builtin_default_registry()  # 非 demo：仅 kb-agent
    d = IntentRouter(experts=view).classify_experts("巡检一下 PLC 故障", scope=Scope(project_id="p_x"))
    assert not (set(d.experts) & set(DEMO_EXPERT_NAMES)), f"非 demo 项目调用了 demo 专家：{d.experts}"
    assert d.experts == ["kb-agent"]

    # 对照组：同一问句在未注入视图（内置默认三专家）下确实命中 demo 专家。
    legacy = IntentRouter().classify_experts("巡检一下 PLC 故障", scope=Scope(project_id="p_x"))
    assert legacy.experts == ["inspection-expert"], "对照问句应能触发 demo 专家"


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

    引用 demo 三专家的历史会话归属改写为 `demo`（记录保留，不删除）；非 demo 项目因此
    失去可见；未引用三专家的会话不动；重复执行幂等（`applied=False`）。
    """
    import ib.streaming as streaming
    from ib.core import MigrationReport, SessionState

    store = streaming.MemorySessionStore()
    store.save("legacy:s1", SessionState(last_expert="freeark-expert", project_id="legacy"))
    store.save("legacy:s2", SessionState(last_expert="unrelated", project_id="legacy"))
    store.save("demo:s3", SessionState(last_expert="inspection-expert", project_id="demo"))
    before = len(store)

    report = streaming.migrate_expert_history("demo", sessions=store)
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
    again = streaming.migrate_expert_history("demo", sessions=store)
    assert again.applied is False and again.affected_sessions == 0


# --------------------------------------------------------------------------- #
# TC-UNIT-R19-013 —— AC-IB-44-01 / AC-IB-44-03：创建期种子按项目落地（文档 + 提示词目录）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R19_013_seed_project_lands_per_project(tmp_path) -> None:
    """US-IB-44 / AC-IB-44-01、AC-IB-44-03；OQ-IB-32(b) / ADR-45 / IFC-IB-385。

    `seed_project` 写 `<dir>/<pid>.json`（该项目专家集）+ 提示词目录骨架
    `<root>/<pid>/<expert>/`；非 demo = 内置默认单例；幂等（已存在不覆盖）。
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
