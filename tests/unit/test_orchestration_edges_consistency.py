"""单元测试层 —— 种子定义文档 ↔ 运行期编排图 **一致性闸**（防漂移护栏，无 AC 派生）。

文件：`tests/unit/test_orchestration_edges_consistency.py`

## 为什么需要这个文件

`OrchestrationSpecInput.edges` 是**描述性**的：运行期拓扑仍由
`ib/orchestration/__init__.py::_compile_graph` 里硬编码的 `add_edge` 决定
（REQ-FUNC-IB-26 ②「拓扑运行期不可编辑」）。**描述**（`ibweb/composition.py` 的种子文档）
与**实现**（`ib/orchestration` 的 `add_edge`）分处两个文件，由不同的人在
不同的时间为不同的目的修改 —— 二者极易**悄悄漂移**：

* 文档**多画**一条边 → 配置页向用户展示一张并不存在的图（界面撒谎）；
* 文档**少画**一条边 → `gate` / `aggregate` 渲染成孤立方块（这正是本次补 `edges` 的起因）。

两者都不会让任何既有用例转红，所以必须有这道闸。

## 闸门为什么是「真比对」而非「复述期望值」

本文件**直接 introspect** `builder.compile()` 产出的图的边（`get_graph().edges`），
而不是把硬编码的 `add_edge` 抄成第二份硬编码清单 —— 后者只要有人同时改两处就永远绿，
闸门形同虚设。仅当该 introspection API 在锁定的 langgraph 版本上不可用时，才退回
兜底清单，**并同时断言种子文档与兜底清单一致**（该分支本身是一个可观测的降级信号）。

## 命名说明

本文件**不含 TC 编号**：它不是由某条验收标准派生的用例，而是防漂移的**护栏**，
与 `tests/unit/test_sse_timeout.py` 的 5 条防护用例同一性质（该文件亦无 TC 编号）。

离线纪律：全程无 I/O、无网络、无凭据；`llm` / `experts` 传 `None` 即可 ——
节点闭包在**编译期**不执行，图结构只由 `add_node` / `add_edge` 决定。
"""

from __future__ import annotations

from ib.core import RESERVED_GRAPH_ENDPOINTS, GraphConfig, Scope

#: 运行期图里 START / END 的内部哨兵名 → 定义文档的**保留合成端点**名。
_SENTINEL_TO_ENDPOINT = {"__start__": "START", "__end__": "END"}

#: introspection 不可用时的兜底期望（逐条对应 `_compile_graph` 的 `add_edge`）。
#: 注意 `general` **绕过** `gate` 直连 `aggregate` —— 确认门只作用于 expert 支路。
_FALLBACK_SPINE: frozenset[tuple[str, str]] = frozenset(
    {
        ("START", "route"),
        ("expert", "gate"),
        ("gate", "aggregate"),
        ("general", "aggregate"),
        ("aggregate", "END"),
    }
)

#: 兜底期望的条件边分支目标（`route -> expert | general`）。
_FALLBACK_BRANCH_TARGETS: frozenset[str] = frozenset({"expert", "general"})

#: 兜底期望的节点集合（`_compile_graph` 的 5 个 `add_node`，不含哨兵）。
_FALLBACK_NODES: frozenset[str] = frozenset({"route", "expert", "general", "gate", "aggregate"})


def _seed_document():
    """内置种子定义文档（未配置 `IB_DEFINITION_DOC_PATH` 时的默认文档）。"""
    from ibweb.composition import _default_definition_document

    # `cfg` 在该函数体内未被使用（只读专家/路由模块级默认值），故传 `None` 即可。
    return _default_definition_document("p_alpha", None)


def _runtime_graph():
    """编译**一次**运行期图（纯结构；节点闭包在编译期不执行，故 `llm` / `experts` 可为 `None`）。"""
    from ib.orchestration import _compile_graph

    return _compile_graph(
        llm=None,
        experts=None,
        tools=[],
        config=GraphConfig(max_expert_steps=8),
        scope=Scope(project_id="p_alpha", kb_ids=None),
        tools_by_expert={},
    )


def _introspect() -> tuple[frozenset[tuple[str, str]], frozenset[str], frozenset[tuple[str, str]]] | None:
    """`(普通边, 节点名, 条件边)` —— 端点哨兵已翻成 `START`/`END`；API 不可用时返回 `None`。

    走 `get_graph()`（langgraph 的 DrawableGraph）而非读源码文本：前者是**编译器眼中的图**，
    后者只是**源码长什么样**——两者的差别正是本闸要覆盖的那一类漂移。
    """
    try:
        drawable = _runtime_graph().get_graph()
        edges = list(drawable.edges)
        nodes = list(drawable.nodes)
    except AttributeError:  # pragma: no cover - 锁定的 langgraph 版本上不会走到
        return None

    def _name(raw: str) -> str:
        return _SENTINEL_TO_ENDPOINT.get(raw, raw)

    plain = frozenset(
        (_name(e.source), _name(e.target)) for e in edges if not e.conditional
    )
    conditional = frozenset(
        (_name(e.source), _name(e.target)) for e in edges if e.conditional
    )
    return plain, frozenset(_name(n) for n in nodes), conditional


def _declared_plain_edges(doc) -> frozenset[tuple[str, str]]:
    return frozenset((e.from_node, e.to_node) for e in doc.orchestration.edges)


def _declared_branch_targets(doc) -> frozenset[tuple[str, str]]:
    """`(from_node, target)` 集合 —— 条件边的实际落点（展开 `branch_map`）。"""
    return frozenset(
        (ce.from_node, target) for ce in doc.orchestration.conditional_edges for _key, target in ce.branch_map
    )


# --------------------------------------------------------------------------- #
# 1. 普通边：种子文档 == 运行期图
# --------------------------------------------------------------------------- #


def test_seed_plain_edges_mirror_runtime_graph_exactly():
    """种子文档的 `orchestration.edges` 与运行期图的无条件边**集合相等**（不多不少）。"""
    doc = _seed_document()
    declared = _declared_plain_edges(doc)

    introspected = _introspect()
    if introspected is None:  # pragma: no cover - 锁定的 langgraph 版本上不会走到
        # 降级不静默：既要种子文档等于兜底清单（护栏仍生效），也把降级本身暴露出来。
        assert declared == _FALLBACK_SPINE, (
            "introspection 不可用，且种子文档 != 兜底清单；两边都不可信，需人工核对："
            f"declared={sorted(declared)}"
        )
        return

    runtime_plain, _nodes, _conditional = introspected
    missing = runtime_plain - declared
    phantom = declared - runtime_plain
    assert declared == runtime_plain, (
        "定义文档的普通边与运行期图不一致（描述与实现漂移）：\n"
        f"  文档漏画（运行期有、文档无）={sorted(missing)}\n"
        f"  文档多画（文档有、运行期无）={sorted(phantom)}"
    )
    assert declared, "种子文档的普通边不得为空 —— 空则 gate/aggregate 在配置页渲染成孤立方块"


# --------------------------------------------------------------------------- #
# 2. 节点：种子文档 == 运行期图（哨兵除外）
# --------------------------------------------------------------------------- #


def test_seed_nodes_match_runtime_nodes():
    """种子文档的 `orchestration.nodes` 与运行期图的节点名**集合相等**（`__start__`/`__end__` 除外）。"""
    doc = _seed_document()
    declared = frozenset(doc.orchestration.nodes)

    introspected = _introspect()
    if introspected is None:  # pragma: no cover - 锁定的 langgraph 版本上不会走到
        assert declared == _FALLBACK_NODES, sorted(declared)
        assert RESERVED_GRAPH_ENDPOINTS.isdisjoint(declared)
        return

    _plain, runtime_nodes, _conditional = introspected
    runtime_nodes = frozenset(n for n in runtime_nodes if n not in {"START", "END"})
    assert declared == runtime_nodes, (
        f"节点集合漂移：文档={sorted(declared)} 运行期={sorted(runtime_nodes)}"
    )

    # 保留合成端点**只**作为边的端点出现，**不得**混进 `nodes`
    assert RESERVED_GRAPH_ENDPOINTS.isdisjoint(declared), (
        f"保留合成端点混入 nodes：{sorted(RESERVED_GRAPH_ENDPOINTS & declared)}"
    )


# --------------------------------------------------------------------------- #
# 3. 条件边：种子文档 == 运行期图
# --------------------------------------------------------------------------- #


def test_seed_conditional_edges_mirror_runtime_graph_exactly():
    """种子文档条件边展开后的**落点**与运行期条件边相等；且分支目标必须是**真实节点**。"""
    doc = _seed_document()
    declared = _declared_branch_targets(doc)

    introspected = _introspect()
    if introspected is None:  # pragma: no cover - 锁定的 langgraph 版本上不会走到
        assert frozenset(t for _f, t in declared) == _FALLBACK_BRANCH_TARGETS, sorted(declared)
        return

    _plain, _nodes, runtime_conditional = introspected
    assert declared == runtime_conditional, (
        "条件边落点漂移：\n"
        f"  文档漏画={sorted(runtime_conditional - declared)}\n"
        f"  文档多画={sorted(declared - runtime_conditional)}"
    )

    # 条件边**不得**落到保留合成端点：`START`/`END` 只能作普通边端点
    reserved_targets = {t for _f, t in declared} & RESERVED_GRAPH_ENDPOINTS
    assert not reserved_targets, f"条件边分支目标不得是保留合成端点：{sorted(reserved_targets)}"
    assert declared, "种子文档的条件边不得为空 —— 空则路由分支在配置页不可见"


# --------------------------------------------------------------------------- #
# 4. 一致性闸自身的负向自证（防止闸门空转）
# --------------------------------------------------------------------------- #


def test_gate_is_not_vacuous_on_a_drifted_document():
    """负向对照：把种子文档的普通边改掉一条 → 闸门的比较表达式必须为**假**。

    若不跑这一条，上面三条断言可能因为「两边都恰好取到同一个空集合」而恒真，
    闸门就成了装饰。此处直接在比较层自证其载荷性（不改 `src/`、不改真实文档）。
    """
    from dataclasses import replace

    doc = _seed_document()
    assert doc.orchestration.edges, "种子文档普通边为空，负向自证无从谈起"

    drifted = replace(
        doc,
        orchestration=replace(doc.orchestration, edges=tuple(doc.orchestration.edges)[:-1]),
    )
    assert _declared_plain_edges(drifted) != _declared_plain_edges(doc)

    introspected = _introspect()
    if introspected is None:  # pragma: no cover - 锁定的 langgraph 版本上不会走到
        return
    runtime_plain, _nodes, _conditional = introspected
    assert _declared_plain_edges(drifted) != runtime_plain, "闸门对漏画一条边竟判为一致（空转）"
