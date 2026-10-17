"""单元测试层 —— REV-21 编排图「专家节点实显」显示投影展开（IFC-IB-393；ADR-52）。

覆盖用户故事：**US-IB-51**（编排图实显本项目实际配置的专家）、**US-IB-52**（专家集合变更
后图随之更新、图仍只读）、**US-IB-53**（边 / 结构节点与运行期拓扑一致且可区分）、
**US-IB-54**（n 专家规模下可读且完整）。
对应验收标准：AC-IB-51-01/02/03/04、AC-IB-52-01/02/03、AC-IB-53-01/02/03、AC-IB-54-01/02。

分层依据（`test_plan.md` §2）：被测对象是**单一模块**里的**纯函数** ——
`ibweb.serializers._expand_expert_nodes` / `definition_derived_summary`，
输入仅为已派生只读视图（`DerivedView`），无 I/O、无跨模块协作 ⇒ **单元级**。
跨模块接缝（端点 / 装配 / 信封键）见 `tests/integration/test_definition_config_rev21_int.py`；
完整用户旅程见 `tests/e2e/test_rev21_expert_graph_journeys.py`。

离线纪律：全程内存替身（`derive` 纯函数 + 临时构造的定义文档），无外部网络、无凭据。
**被测源码 `src/**` 全程只读**（缺陷只登记、不代改）。
"""

from __future__ import annotations

import pytest

from ib.config import build_definition_document, derive
from ib.core import (
    RESERVED_GRAPH_ENDPOINTS,
    ConditionalEdgeSpec,
    ConfigError,
    EdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
)
from ibweb.serializers import definition_derived_summary

#: 结构节点名（ADR-52 决定 1 / 5）——**不**代表某一专家的固定节点。
_STRUCTURAL = {"route", "general", "gate", "aggregate"}

#: 定义文档编排拓扑中代表「全部专家」的单一占位节点（ADR-52 决定 1 / 3 / 4）。
_PLACEHOLDER = "expert"


# --------------------------------------------------------------------------- #
# 构造助手
# --------------------------------------------------------------------------- #


def _expert(name: str, cn_label: str, *, is_default: bool = False) -> ExpertSpecInput:
    """构造一位专家（`keywords` 随 `name` 派生，保证互不撞车 —— 仅夹具数据，不涉断言语义）。"""
    return ExpertSpecInput(
        name=name,
        cn_label=cn_label,
        keywords=(f"k{name}",),
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _placeholder_orchestration() -> OrchestrationSpecInput:
    """**内置默认编排流**（与 `ibweb/composition.py::_definition_document_from_specs` 逐条一致）。

    该形态**未**逐专家声明节点：专家以一个字面量占位节点 `expert` 表达，专家集合由
    `experts[]` 承载（`orchestration` schema 本轮一字未动）。
    """
    return OrchestrationSpecInput(
        nodes=("route", _PLACEHOLDER, "general", "gate", "aggregate"),
        conditional_edges=(
            ConditionalEdgeSpec("route", ((_PLACEHOLDER, _PLACEHOLDER), ("general", "general"))),
        ),
        edges=(
            EdgeSpec("START", "route"),
            EdgeSpec(_PLACEHOLDER, "gate"),
            EdgeSpec("gate", "aggregate"),
            EdgeSpec("general", "aggregate"),
            EdgeSpec("aggregate", "END"),
        ),
    )


def _per_expert_orchestration(names: tuple[str, ...]) -> OrchestrationSpecInput:
    """**逐专家声明**节点的编排流（既有合法文档形态之一 —— 未经占位节点）。"""
    return OrchestrationSpecInput(
        nodes=("route", *names, "general", "gate", "aggregate"),
        conditional_edges=(
            ConditionalEdgeSpec(
                "route",
                (*( (n, n) for n in names ), ("general", "general")),
            ),
        ),
        edges=(
            EdgeSpec("START", "route"),
            *(EdgeSpec(n, "gate") for n in names),
            EdgeSpec("gate", "aggregate"),
            EdgeSpec("general", "aggregate"),
            EdgeSpec("aggregate", "END"),
        ),
    )


def _doc(experts: tuple[ExpertSpecInput, ...], orchestration: OrchestrationSpecInput):
    """由给定专家集合与编排流构造定义文档（`content_hash` 由内容决定）。"""
    return build_definition_document(
        project_id="p_alpha",
        experts=experts,
        route=RouteSpecInput(
            tau=0.65, margin=0.05, max_expert_steps=8, default_expert=experts[0].name
        ),
        orchestration=orchestration,
        tool_grants=(),
    )


def _summary(experts: tuple[ExpertSpecInput, ...], orchestration=None):
    """构造派生视图摘要（纯函数链：`build_definition_document` → `derive` → `definition_derived_summary`）。"""
    orch = orchestration if orchestration is not None else _placeholder_orchestration()
    return definition_derived_summary(derive(_doc(tuple(experts), orch)))


_TWO = (_expert("a", "标签a", is_default=True), _expert("b", "标签b"))


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-001 —— AC-IB-51-01：多专家项目逐专家成节点、占位节点不残留
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_001_multi_experts_become_per_expert_nodes():
    """[TC-UNIT-R21-001] US-IB-51 / AC-IB-51-01：n 个专家 ⇒ n 个专家节点，**不出现**字面量占位节点。

    Given 定义文档配置 n 个专家；When 派生摘要展开；Then 节点集合含**每个**专家 `name`，
    且**不含**字面量 `expert`（单一占位节点不得残留）。
    """
    s = _summary(_TWO)
    assert "a" in s["nodes"] and "b" in s["nodes"], f"专家节点缺失：{s['nodes']}"
    assert _PLACEHOLDER not in s["nodes"], f"占位节点 `expert` 残留于 nodes：{s['nodes']}"
    assert s["expert_names"] == ["a", "b"]
    # 专家节点数与专家集合规模一致（AC-IB-54-02 的口径在单元层同验）
    expert_nodes = [n for n in s["nodes"] if n in {"a", "b"}]
    assert len(expert_nodes) == len(s["expert_names"]) == 2


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-002 —— AC-IB-51-02：仅含默认单专家的项目 ⇒ 恰一个专家节点
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_002_single_default_expert_yields_exactly_one_node():
    """[TC-UNIT-R21-002] US-IB-51 / AC-IB-51-02：唯一 kb-agent 项目 ⇒ 图上恰一个专家节点。"""
    single = (_expert("kb-agent", "知识库助手", is_default=True),)
    s = _summary(single)
    assert "kb-agent" in s["nodes"]
    assert _PLACEHOLDER not in s["nodes"]
    assert sum(1 for n in s["nodes"] if n == "kb-agent") == 1
    # 恰一个专家节点：结构节点不重复计入，专家节点计数 == 专家集合规模 == 1
    expert_nodes = [n for n in s["nodes"] if n not in _STRUCTURAL]
    assert expert_nodes == ["kb-agent"]
    assert s["experts"] == [
        {"name": "kb-agent", "cn_label": "知识库助手", "is_default": True}
    ]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-003 —— AC-IB-51-03：三专家项目分别出现三个对应节点
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_003_three_experts_appear_separately():
    """[TC-UNIT-R21-003] US-IB-51 / AC-IB-51-03：三专家（历史 demo 等）分别成节点，而非一个占位。"""
    three = (
        _expert("freeark-expert", "FreeArk", is_default=True),
        _expert("inspection-expert", "巡检"),
        _expert("sanheng-knowledge", "三恒知识"),
    )
    s = _summary(three)
    for name in ("freeark-expert", "inspection-expert", "sanheng-knowledge"):
        assert name in s["nodes"], f"专家 {name} 未成节点：{s['nodes']}"
    assert _PLACEHOLDER not in s["nodes"]
    assert s["expert_names"] == ["freeark-expert", "inspection-expert", "sanheng-knowledge"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-004 —— AC-IB-51-04：标识取自定义文档专家集合（cn_label 为主）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_004_identifiers_come_from_definition_expert_set():
    """[TC-UNIT-R21-004] US-IB-51 / AC-IB-51-04：`experts[]` 含 `cn_label` / `name` / `is_default`，
    且**不含**任何与配置无关的通用字面量（如字面 `expert`）。

    标签字段口径（OQ-IB-53=A）：`cn_label` 为主、`name` 次级；默认专家带可辨识标记
    （此处以 `is_default=True` 表达，前端据此渲染「（默认）」）。
    """
    s = _summary(_TWO)
    assert len(s["experts"]) == 2
    for entry in s["experts"]:
        assert set(entry) == {"name", "cn_label", "is_default"}, entry
        assert entry["name"] and entry["cn_label"], entry
    assert s["experts"][0]["is_default"] is True
    assert s["experts"][1]["is_default"] is False
    # 通用字面量不得出现在专家标识里
    assert all(e["name"] != _PLACEHOLDER for e in s["experts"]), s["experts"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-005 —— AC-IB-53-01：条件边仍为一条，分支覆盖逐专家 + general
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_005_single_conditional_edge_expands_branch_map():
    """[TC-UNIT-R21-005] US-IB-53 / AC-IB-53-01：条件边**仍为 1 条**；`branch_map` 由
    `(expert,expert)` 改为**逐专家** `(name,name)`，并保留 `(general,general)`。

    呈现与运行期「路由按并行分派（fan-out）择一 / 多专家并行」语义一致：一条条件边、
    多个分支落点，不给每位专家各画一条条件边。
    """
    s = _summary(_TWO)
    assert len(s["conditional_edges"]) == 1, s["conditional_edges"]
    ce = s["conditional_edges"][0]
    assert ce["from_node"] == "route"
    assert ce["branch_map"] == [["a", "a"], ["b", "b"], ["general", "general"]], ce["branch_map"]
    # 字面量占位不得作为条件边落点
    assert all(t != _PLACEHOLDER for _k, t in ce["branch_map"])


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-006 —— AC-IB-53-02：结构节点保留，且与专家节点可区分
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_006_structural_nodes_retained_and_distinguishable():
    """[TC-UNIT-R21-006] US-IB-53 / AC-IB-53-02：`route` / `general` / `gate` / `aggregate`
    **保留**在 `nodes` 内；结构节点名与专家节点名**不相交**（视觉可区分的前提）。

    `START` / `END` 为合成端点，**不**进 `nodes`（只作边端点）。
    """
    s = _summary(_TWO)
    for name in ("route", "general", "gate", "aggregate"):
        assert name in s["nodes"], f"结构节点 {name} 被丢失：{s['nodes']}"
    assert _STRUCTURAL.isdisjoint({e["name"] for e in s["experts"]})
    assert RESERVED_GRAPH_ENDPOINTS.isdisjoint(s["nodes"]), s["nodes"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-007 —— AC-IB-53-03 / AC-IB-52-03：运行期拓扑未被改变
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_007_runtime_topology_unchanged():
    """[TC-UNIT-R21-007] US-IB-53 / AC-IB-53-03（+ AC-IB-52-03）：**运行期** LangGraph 拓扑
    仍为**单一默认编排流**，含**占位节点 `expert`** —— 与本轮显示投影的展开结果形成对照：
    展开只发生在显示投影层，运行期节点 / 边**一字未动**。

    判据直接 introspect 运行期编译器产出的图（`get_graph()`），不复述硬编码清单 ——
    「描述」与「实现」的漂移正是本闸要覆盖的那一类。
    """
    from ib.core import GraphConfig, Scope
    from ib.orchestration import _compile_graph

    graph = _compile_graph(
        llm=None,
        experts=None,
        tools=[],
        config=GraphConfig(max_expert_steps=8),
        scope=Scope(project_id="p_alpha", kb_ids=None),
        tools_by_expert={},
    )
    drawable = graph.get_graph()

    def _name(raw: str) -> str:
        return {"__start__": "START", "__end__": "END"}.get(raw, raw)

    # 合成端点（`__start__` / `__end__`）是图入口 / 出口的哨兵，**不**计入可编排节点。
    nodes = {_name(n) for n in drawable.nodes} - RESERVED_GRAPH_ENDPOINTS
    plain = {
        (_name(e.source), _name(e.target)) for e in drawable.edges if not e.conditional
    }
    conditional_targets = {
        (_name(e.source), _name(e.target)) for e in drawable.edges if e.conditional
    }

    # 运行期节点：仍是 5 个固定节点（含占位 `expert`），未因 REV-21 增删
    assert nodes == {"route", "expert", "general", "gate", "aggregate"}, nodes
    # 运行期普通边：仍是单默认主干（`general` 绕过 gate 直连 aggregate）
    assert plain == {
        ("START", "route"),
        ("expert", "gate"),
        ("gate", "aggregate"),
        ("general", "aggregate"),
        ("aggregate", "END"),
    }, plain
    # 运行期条件边落点：仍是占位 `expert` + `general` —— 未被逐专家展开
    assert conditional_targets == {("route", "expert"), ("route", "general")}, conditional_targets


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-008 —— AC-IB-52-01：新增专家 ⇒ 图上新出现对应节点
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_008_adding_expert_adds_node():
    """[TC-UNIT-R21-008] US-IB-52 / AC-IB-52-01：专家集合新增一位 ⇒ 展开后新出现该专家节点，
    节点总数与专家集合一致（单一真源：节点来源 = `experts[]`，非第二真源）。
    """
    base = _summary(_TWO)
    grown = _summary((*_TWO, _expert("c", "标签c")))
    assert "c" not in base["nodes"]
    assert "c" in grown["nodes"]
    assert len(grown["nodes"]) == len(base["nodes"]) + 1
    # 条件边分支与普通边同步增长（逐专家镜像）
    assert ["c", "c"] in grown["conditional_edges"][0]["branch_map"]
    assert {"from_node": "c", "to_node": "gate"} in grown["edges"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-009 —— AC-IB-52-02 / AC-IB-54-02：删除专家 ⇒ 节点随之消失；节点数 == 专家集规模
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_009_removing_expert_removes_node_and_count_matches():
    """[TC-UNIT-R21-009] US-IB-52 / AC-IB-52-02 + US-IB-54 / AC-IB-54-02：删除一位专家 ⇒
    其节点 / 条件边分支 / 普通边**不再出现**，且**专家节点数恒等于专家集合规模**。
    """
    three = (*_TWO, _expert("c", "标签c"))
    s3 = _summary(three)
    s2 = _summary(_TWO)
    assert "c" in s3["nodes"] and {"from_node": "c", "to_node": "gate"} in s3["edges"]
    assert "c" not in s2["nodes"]
    assert ["c", "c"] not in s2["conditional_edges"][0]["branch_map"]
    # 「图仍满足可读 + 完整」：删除后主干边与原结构节点仍在
    for name in _STRUCTURAL:
        assert name in s2["nodes"]
    for edge in (
        {"from_node": "START", "to_node": "route"},
        {"from_node": "gate", "to_node": "aggregate"},
        {"from_node": "general", "to_node": "aggregate"},
        {"from_node": "aggregate", "to_node": "END"},
    ):
        assert edge in s2["edges"], edge
    # 专家节点数 == 专家集合规模
    assert sorted(n for n in s2["nodes"] if n not in _STRUCTURAL) == sorted(
        e["name"] for e in s2["experts"]
    ) == ["a", "b"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-010 —— 冲突负例：专家名 = 结构节点 / 合成端点 ⇒ ConfigError，不静默改名
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("conflict", ["route", "gate", "general", "aggregate", "START", "END"])
def test_TC_UNIT_R21_010_conflicting_expert_name_raises_configerror(conflict: str):
    """[TC-UNIT-R21-010] US-IB-51/53 / AC-IB-51-01 + AC-IB-53-02：专家名与**结构节点**
    （`route` / `general` / `gate` / `aggregate`）或**合成端点**（`START` / `END`）同名 ⇒
    **抛 `ConfigError`**，**绝不**隐式改名（改名会静默改变图上的身份）。

    要求各 ≥1 例：本条参数化覆盖 6 个冲突名。
    """
    with pytest.raises(ConfigError) as exc:
        _summary((_expert(conflict, "冲突标签", is_default=True),))
    message = str(exc.value)
    # 错误信息须**指明**冲突名（可读回执），以便运维定位
    assert conflict in message, message
    assert "同名" in message, message
    # **不静默改名**：命名不得出现「加后缀 / 前缀」的变体
    assert f"{conflict}_" not in message
    assert f"x-{conflict}" not in message


def test_TC_UNIT_R21_010b_no_silent_output_for_conflict():
    """[TC-UNIT-R21-010b] 上条的**行为面**：冲突时函数**不返回**任何可用摘要（无兜底输出）。

    若实现改为「改名后照常返回」，上条仍可能通过（消息里恰好含原名）—— 本条断言
    「要么抛错、要么什么都拿不到」，堵住「静默改名后继续渲染」的形态。
    """
    produced = None
    try:
        produced = _summary((_expert("START", "冲突标签", is_default=True),))
    except ConfigError:
        produced = None
    assert produced is None, f"冲突竟产出摘要（疑似静默改名）：{produced}"


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-011 —— AC-IB-52-01（OQ-IB-55=A）：逐专家声明的既有文档 ⇒ 无操作（零迁移）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_011_per_expert_document_expansion_is_noop():
    """[TC-UNIT-R21-011] US-IB-52 / AC-IB-52-01：若文档**本就逐专家声明**节点（未用占位节点），
    展开为**无操作** —— `derived.nodes` / 条件边 / 普通边与文档编排**逐项一致**（既有定义文档零迁移）。
    """
    orch = _per_expert_orchestration(("a", "b"))
    s = _summary(_TWO, orch)
    assert s["nodes"] == list(orch.nodes), s["nodes"]
    assert s["edges"] == [{"from_node": e.from_node, "to_node": e.to_node} for e in orch.edges]
    assert s["conditional_edges"] == [
        {"from_node": ce.from_node, "branch_map": [[k, t] for k, t in ce.branch_map]}
        for ce in orch.conditional_edges
    ]


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-012 —— [ARCH-ASSUMPTION-A16]：既有 5 键键名不变；新增 experts 不含工具摘要
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_012_arch_assumption_a16_additive_contract():
    """[TC-UNIT-R21-012] [ARCH-ASSUMPTION-A16]：`derived` 既有 **5 键键名不变**（仅新增 `experts`），
    且 `experts` 条目**不含**工具授权摘要（OQ-IB-53=A）—— 既有消费者不受影响。

    这是**加成式**契约：新增键不改变既有键名 / 语义，故前端与任何既有消费方无需改动即可继续工作。
    """
    s = _summary(_TWO)
    existing_five = {"capability_digest", "expert_names", "nodes", "conditional_edges", "edges"}
    assert existing_five <= set(s), f"既有键缺失：{existing_five - set(s)}"
    assert set(s) == existing_five | {"experts"}, f"键集合超出预期（非加成式变更）：{set(s)}"
    # experts 条目只承载显示元数据；**不含**任何工具授权摘要字段
    for entry in s["experts"]:
        assert set(entry) == {"name", "cn_label", "is_default"}, entry
        assert not {"tools", "tool_names", "tool_grants", "capability_digest"} & set(entry)
    # 工具摘要只保留在既有键 `capability_digest`（口径未变）
    assert isinstance(s["capability_digest"], str)


# --------------------------------------------------------------------------- #
# TC-UNIT-R21-013 —— AC-IB-54-01：n 较大时节点与边完整可见（不漏）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R21_013_many_experts_all_nodes_and_edges_present():
    """[TC-UNIT-R21-013] US-IB-54 / AC-IB-54-01：含较多专家（n = 6）时，**全部**专家节点与
    其边完整可见 —— 每位专家恰一条 `route→name` 条件分支与一条 `name→gate` 普通边，不漏。
    """
    names = ("e1", "e2", "e3", "e4", "e5", "e6")
    experts = tuple(_expert(n, f"标签{n}", is_default=(i == 0)) for i, n in enumerate(names))
    s = _summary(experts)

    for name in names:
        assert name in s["nodes"], f"专家节点 {name} 丢失：{s['nodes']}"
    branch = s["conditional_edges"][0]["branch_map"]
    assert [n for n in names if [n, n] in branch] == list(names)
    assert branch[-1] == ["general", "general"]
    mirrored = [e for e in s["edges"] if e["from_node"] in names]
    assert len(mirrored) == len(names), f"逐专家普通边不完整：{mirrored}"
    assert all(e["to_node"] == "gate" for e in mirrored)
    # 结构节点与主干边齐全（「完整」）
    for name in _STRUCTURAL:
        assert name in s["nodes"]
    assert len(s["nodes"]) == len(names) + len(_STRUCTURAL)
