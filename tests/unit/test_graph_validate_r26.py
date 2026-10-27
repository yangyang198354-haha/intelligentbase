"""[REV-26 / GROUP_D] MOD-R26-02 `validate_graph`：图合法性校验（纯函数）。

溯源：US-013（AC-013-01~06）、US-011（AC-011-03/06）、US-005（AC-005-03）、US-021（兜底）。
层级：单元（framework-free 纯函数，无 I/O）。
"""

from __future__ import annotations

import pytest
from config_r26_support import (
    agent_node,
    edge,
    error_codes,
    expert,
    graph,
    keyword_pred,
    node,
    route_graph,
)

from ib.config.graph import validate_graph
from ib.core import ELSE_BRANCH
from ib.core.graph import GRAPH_MAX_EDGES, GRAPH_MAX_NODES

EXPERTS = (expert("a", default=True), expert("b"))


def _validate(g, experts=EXPERTS, default="a"):
    return validate_graph(g, experts=experts, default_expert=default)


def test_TC_UNIT_R26_001_valid_route_graph_has_no_errors():
    """US-013 / AC-013-06：合法图 → 错误列表为空。"""
    assert _validate(route_graph("a", "b")) == ()


def test_TC_UNIT_R26_002_cycle_lists_cycle_nodes():
    """US-013 / AC-013-01：环 A→B→A → graph_cycle，消息含环上节点 a、b。"""
    base = route_graph("a", "b")
    g = graph(list(base.nodes), [e for e in base.edges if e.id not in ("e-o0", "e-o1")] + [
        edge("x1", "a", "b"), edge("x2", "b", "a"), edge("x3", "b", "end")])
    errs = _validate(g)
    cyc = [e for e in errs if e.code == "graph_cycle"]
    assert len(cyc) == 1
    assert "a" in cyc[0].message and "b" in cyc[0].message


def test_TC_UNIT_R26_003_unconnected_node_unreachable_from_start():
    """US-013 / AC-013-02：新增节点 x 未连线 → graph_unreachable_from_start 指向 x。"""
    base = route_graph("a", "b")
    errs = _validate(graph(list(base.nodes) + [node("x", "join")], list(base.edges)))
    hits = [e for e in errs if e.code == "graph_unreachable_from_start"]
    assert [e.path for e in hits] == ["graph.nodes[x]"]


def test_TC_UNIT_R26_004_node_without_path_to_end():
    """US-013 / AC-013-03：节点 b 无通向 end 的路径 → graph_no_path_to_end 指向 b。"""
    base = route_graph("a", "b")
    errs = _validate(graph(list(base.nodes), [e for e in base.edges if e.id != "e-o1"]))
    hits = [e for e in errs if e.code == "graph_no_path_to_end"]
    assert [e.path for e in hits] == ["graph.nodes[b]"]


def test_TC_UNIT_R26_005_default_expert_edge_removed_reports_unreachable():
    """US-013 / AC-013-04：删除默认专家与开始节点之间的连线 → 默认专家不可达。

    把 a 的唯一入边（route-1 → a 与 __else__ → a）都删掉后，a 既不可达，默认专家也不可达。
    """
    base = route_graph("a", "b", default="b")
    g = graph(list(base.nodes), [e for e in base.edges if e.id != "e-r0"])
    codes = error_codes(_validate(g))
    assert "graph_unreachable_from_start" in codes  # a 不可达
    g2 = graph(list(base.nodes), [e for e in base.edges if e.id not in ("e-r0", "e-else")] + [edge("e-else", "route-1", "b", ELSE_BRANCH)])
    assert "graph_default_expert_unreachable" in error_codes(_validate(g2, default="a"))


def test_TC_UNIT_R26_006_default_expert_not_in_graph():
    """AC-013-04 边界：默认专家没有 agent 节点 → graph_default_expert_missing。"""
    g = route_graph("b")  # 只有 b
    assert "graph_default_expert_missing" in error_codes(_validate(g, default="a"))


def test_TC_UNIT_R26_007_route_without_else_branch():
    """US-006 / AC-006-02：路由节点缺 __else__ 出边 → graph_branch_else_missing，路径指向该节点。"""
    base = route_graph("a", "b")
    errs = _validate(graph(list(base.nodes), [e for e in base.edges if e.id != "e-else"]))
    hits = [e for e in errs if e.code == "graph_branch_else_missing"]
    assert [e.path for e in hits] == ["graph.nodes[route-1]"]


def test_TC_UNIT_R26_008_condition_without_else_branch():
    """US-006 / AC-006-02：条件分支节点同样要求 __else__。"""
    nodes = [node("start", "start"), node("end", "end"), agent_node("a"), agent_node("b"),
             node("cond", "condition", predicate=keyword_pred(billing=("发票",)))]
    edges = [edge("e1", "start", "cond"), edge("e2", "cond", "a", "billing"), edge("e3", "a", "end"),
             edge("e4", "b", "end")]
    errs = _validate(graph(nodes, edges))
    assert "graph_branch_else_missing" in error_codes(errs)


def test_TC_UNIT_R26_009_join_needs_two_incoming():
    """US-011 / AC-011-03：汇聚节点入边 <2 → graph_join_inputs。"""
    base = route_graph("a", "b")
    nodes = list(base.nodes) + [node("j", "join")]
    edges = [e for e in base.edges if e.id != "e-o0"] + [edge("x1", "a", "j"), edge("x2", "j", "end")]
    assert "graph_join_inputs" in error_codes(_validate(graph(nodes, edges)))


def test_TC_UNIT_R26_010_valid_join_two_agents():
    """US-011 / AC-011-03：两个 agent 连入汇聚、再连结束 → 校验通过。"""
    nodes = [node("start", "start"), node("route-1", "route"), node("end", "end"), node("j", "join"),
             agent_node("a"), agent_node("b")]
    edges = [edge("e0", "start", "route-1"), edge("e1", "route-1", "a", "a"), edge("e2", "route-1", "b", "b"),
             edge("e3", "route-1", "a", ELSE_BRANCH), edge("e4", "a", "j"), edge("e5", "b", "j"),
             edge("e6", "j", "end")]
    assert _validate(graph(nodes, edges)) == ()


@pytest.mark.parametrize(
    "mutate,code",
    [
        ("dup_node", "graph_node_id_duplicate"),
        ("bad_kind", "graph_node_kind_unknown"),
        ("two_start", "graph_start_end_count"),
        ("start_in", "graph_start_has_incoming"),
        ("end_out", "graph_end_has_outgoing"),
        ("self_loop", "graph_edge_self_loop"),
        ("dup_edge", "graph_edge_duplicate"),
        ("dangling", "graph_edge_endpoint_missing"),
        ("bad_edge_id", "graph_edge_id_invalid"),
        ("branch_on_plain", "graph_branch_source_invalid"),
        ("reserved_id", "graph_node_id_reserved"),
        ("unknown_expert", "graph_agent_expert_unknown"),
        ("route_bad_target", "graph_route_branch_target_invalid"),
        ("always_from_route", "graph_always_edge_from_branching_node"),
        ("dup_else", "graph_branch_else_multiple"),
        ("confirm_empty", "graph_confirm_message_invalid"),
        ("cond_no_pred", "graph_condition_predicate_missing"),
        ("pos_inf", "graph_position_invalid"),
    ],
)
def test_TC_UNIT_R26_011_error_code_matrix(mutate, code):
    """US-013 / AC-013-05：服务端对各类结构错误逐条给出稳定错误码（接口与界面同一函数）。"""
    base = route_graph("a", "b")
    nodes, edges = list(base.nodes), list(base.edges)
    if mutate == "dup_node":
        nodes.append(node("start", "start"))
    elif mutate == "bad_kind":
        nodes.append(node("z", "bogus"))
    elif mutate == "two_start":
        nodes.append(node("start2", "start"))
    elif mutate == "start_in":
        edges.append(edge("x", "a", "start"))
    elif mutate == "end_out":
        edges.append(edge("x", "end", "a"))
    elif mutate == "self_loop":
        edges.append(edge("x", "a", "a"))
    elif mutate == "dup_edge":
        edges.append(edge("x", "route-1", "a", "a"))
    elif mutate == "dangling":
        edges.append(edge("x", "a", "ghost"))
    elif mutate == "bad_edge_id":
        edges.append(edge("BAD ID", "a", "end"))
    elif mutate == "branch_on_plain":
        edges.append(edge("x", "a", "b", "oops"))
    elif mutate == "reserved_id":
        nodes.append(node("__sneaky", "join"))
    elif mutate == "unknown_expert":
        nodes.append(node("ghost", "agent", expert="ghost"))
    elif mutate == "route_bad_target":
        edges.append(edge("x", "route-1", "end", "zzz"))
    elif mutate == "always_from_route":
        edges.append(edge("x", "route-1", "end", None))
    elif mutate == "dup_else":
        edges.append(edge("x", "route-1", "b", ELSE_BRANCH))
    elif mutate == "confirm_empty":
        nodes.append(node("c", "confirm", message="   "))
    elif mutate == "cond_no_pred":
        nodes.append(node("c", "condition"))
    elif mutate == "pos_inf":
        nodes[0] = node("start", "start", x=float("inf"))
    assert code in error_codes(_validate(graph(nodes, edges)))


def test_TC_UNIT_R26_012_agent_mismatch_disabled_duplicate():
    """US-005：agent 节点 id≠专家名 / 引用已停用专家 / 同一专家两个节点，各有专属错误码。"""
    experts = (expert("a", default=True), expert("b", status="disabled"), expert("c"))
    base = route_graph("a")
    nodes = list(base.nodes) + [node("zz", "agent", expert="c"), agent_node("b"), node("a2", "agent", expert="a")]
    codes = error_codes(_validate(graph(nodes, list(base.edges)), experts=experts))
    assert {"graph_agent_id_mismatch", "graph_agent_expert_disabled", "graph_agent_duplicate"} <= set(codes)


def test_TC_UNIT_R26_013_condition_predicate_rules():
    """US-006 / A03：条件谓词只接受 keyword / upstream_degraded；非法分支键、重复键、空关键词被拒。"""
    def cond(pred):
        nodes = [node("start", "start"), node("end", "end"), agent_node("a"), node("c", "condition", predicate=pred)]
        edges = [edge("e1", "start", "c"), edge("e2", "c", "a", ELSE_BRANCH), edge("e3", "a", "end")]
        return error_codes(_validate(graph(nodes, edges), experts=(expert("a", default=True),)))

    from ib.core import ConditionBranch, ConditionPredicate

    assert "graph_condition_branch_invalid" in cond(ConditionPredicate(kind="keyword", branches=()))
    assert "graph_condition_branch_invalid" in cond(keyword_pred(**{ELSE_BRANCH: ("x",)}))
    assert "graph_condition_branch_invalid" in cond(
        ConditionPredicate(kind="keyword", branches=(ConditionBranch("k", ("x",)), ConditionBranch("k", ("y",)))))
    assert "graph_condition_branch_invalid" in cond(keyword_pred(k=("  ",)))
    assert "graph_condition_branch_invalid" in cond(keyword_pred(k=("x" * 33,)))
    assert "graph_condition_branch_invalid" in cond(ConditionPredicate(kind="upstream_degraded", branches=(ConditionBranch("k", ("x",)),)))
    # 未知谓词种类（例如试图塞表达式）同样被拒，且没有任何执行入口
    assert "graph_condition_branch_invalid" in cond(ConditionPredicate(kind="expression", branches=()))  # type: ignore[arg-type]


def test_TC_UNIT_R26_014_graph_size_limit_short_circuits():
    """US-022 / REQ-NFUNC-009：节点 >60 或边 >200 → 单条 graph_too_large，不做后续全量检查。"""
    nodes = [node("start", "start"), node("end", "end")] + [agent_node(f"n{i}") for i in range(GRAPH_MAX_NODES)]
    errs = _validate(graph(nodes, []))
    assert error_codes(errs) == ["graph_too_large"]
    many_edges = [edge(f"e{i}", "start", "end") for i in range(GRAPH_MAX_EDGES + 1)]
    assert error_codes(_validate(graph([node("start", "start"), node("end", "end")], many_edges))) == ["graph_too_large"]


def test_TC_UNIT_R26_015_boundary_31_nodes_58_edges_validates_fast():
    """US-022 / AC-022-02：31 节点 / 58 边（约 30/60 规模）的合法图校验通过，且纯函数耗时远小于 2 秒（离线下界；目标机另验）。"""
    import time

    names = [f"a{i}" for i in range(28)]
    experts = tuple(expert(n, default=(i == 0)) for i, n in enumerate(names))
    g = route_graph(*names)
    assert len(g.nodes) == 31 and len(g.edges) == 58
    t0 = time.monotonic()
    assert validate_graph(g, experts=experts, default_expert="a0") == ()
    assert time.monotonic() - t0 < 2.0


def test_TC_UNIT_R26_016_errors_do_not_echo_prompt_or_secret_text():
    """US-019 / AC-019-03：校验消息不回显节点文案之外的正文（确认话术含密钥样式串时消息不含该串）。"""
    secret_like = "sk-" + "A" * 30
    n = node("c", "confirm", message=secret_like * 20)  # 超长触发错误
    base = route_graph("a", "b")
    errs = _validate(graph(list(base.nodes) + [n], list(base.edges)))
    assert any(e.code == "graph_confirm_message_invalid" for e in errs)
    assert all(secret_like not in e.message and secret_like not in e.path for e in errs)


def test_TC_UNIT_R26_017_validate_is_deterministic():
    """REQ-NFUNC-013：同输入同输出。"""
    base = route_graph("a", "b")
    g = graph(list(base.nodes) + [node("x", "join")], list(base.edges))
    assert _validate(g) == _validate(g)
