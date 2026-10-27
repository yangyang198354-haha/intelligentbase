"""[REV-26 / GROUP_D] MOD-R26-02 `layerize_graph` / `canonical_graph_from_experts`（纯函数）。

溯源：US-011（AC-011-05 汇聚语义前提）、US-020（AC-020-01/03 旧项目规范化等价）、US-012（AC-012-02 位置不影响语义）。
层级：单元。
"""

from __future__ import annotations

import pytest
from config_r26_support import agent_node, edge, expert, graph, node, route_graph

from ib.config.graph import canonical_graph_from_experts, layerize_graph, validate_graph
from ib.core import ELSE_BRANCH, RELAY_PREFIX


def test_TC_UNIT_R26_030_every_planned_edge_spans_exactly_one_level():
    """ADR-57：层归一化后每条边恰好跨 1 层（长边插入中继）。"""
    nodes = [node("start", "start"), node("route-1", "route"), node("end", "end"),
             agent_node("a"), agent_node("b"), node("j", "join")]
    edges = [edge("e0", "start", "route-1"), edge("r1", "route-1", "a", "a"), edge("r2", "route-1", "b", "b"),
             edge("r3", "route-1", "a", ELSE_BRANCH), edge("e1", "a", "b"), edge("e2", "a", "j"),
             edge("e3", "b", "j"), edge("e4", "j", "end")]
    g = graph(nodes, edges)
    plan = layerize_graph(g)
    lv = dict(plan.levels)
    for r in plan.relays:
        lv[r.id] = r.level
    assert plan.edges and all(lv[pe.target] - lv[pe.source] == 1 for pe in plan.edges)
    assert plan.relays, "a→j 跨两层，必须插入中继"
    assert all(r.id.startswith(RELAY_PREFIX) for r in plan.relays)


def test_TC_UNIT_R26_031_branch_key_only_on_first_hop():
    """分支键只带在原边的第一跳；其余中继跳无分支键。"""
    nodes = [node("start", "start"), node("route-1", "route"), node("end", "end"), agent_node("a"), agent_node("b")]
    edges = [edge("e0", "start", "route-1"), edge("r1", "route-1", "a", "a"), edge("r2", "route-1", "b", "b"),
             edge("r3", "route-1", "end", ELSE_BRANCH), edge("m", "a", "b"), edge("o", "b", "end")]
    plan = layerize_graph(graph(nodes, edges))
    # route-1(1) → end(4)：跨 3 层 ⇒ 2 个中继；仅第一跳带 __else__
    hops = [pe for pe in plan.edges if pe.origin_edge_id == "r3"]
    assert len(hops) == 3
    assert hops[0].branch_key == ELSE_BRANCH and all(h.branch_key is None for h in hops[1:])


def test_TC_UNIT_R26_032_layerize_rejects_cycle_and_missing_start():
    """前置条件违反 → ValueError（编程错误，非用户输入路径）。"""
    cyc = graph([node("start", "start"), agent_node("a"), agent_node("b")],
                [edge("1", "start", "a"), edge("2", "a", "b"), edge("3", "b", "a")])
    with pytest.raises(ValueError):
        layerize_graph(cyc)
    with pytest.raises(ValueError):
        layerize_graph(graph([agent_node("a")], []))


def test_TC_UNIT_R26_033_canonical_graph_matches_legacy_topology_and_is_valid():
    """US-020 / AC-020-03：v1 → 规范化默认图 = START → route-1 → 每个启用专家 → END，且通过校验。"""
    experts = (expert("kb", default=True), expert("x"), expert("off", status="disabled"))
    g = canonical_graph_from_experts(experts, "kb")
    kinds = {n.id: n.kind for n in g.nodes}
    assert kinds == {"start": "start", "route-1": "route", "kb": "agent", "x": "agent", "end": "end"}
    keys = {e.target: e.branch_key for e in g.edges if e.source == "route-1"}
    assert keys == {"kb": "kb", "x": "x"} or ELSE_BRANCH in {e.branch_key for e in g.edges if e.source == "route-1"}
    else_edges = [e for e in g.edges if e.source == "route-1" and e.branch_key == ELSE_BRANCH]
    assert [e.target for e in else_edges] == ["kb"], "__else__ 回落到默认专家"
    assert validate_graph(g, experts=experts, default_expert="kb") == ()


def test_TC_UNIT_R26_034_canonical_graph_is_deterministic_and_keeps_positions():
    """US-012 / AC-012-02：位置只影响展示，不改变拓扑；给定 positions 原样保留。"""
    experts = (expert("kb", default=True), expert("x"))
    plain = canonical_graph_from_experts(experts, "kb")
    moved = canonical_graph_from_experts(experts, "kb", positions={"kb": (10.0, 20.0)})
    assert canonical_graph_from_experts(experts, "kb") == plain
    assert {(e.source, e.target, e.branch_key) for e in plain.edges} == {(e.source, e.target, e.branch_key) for e in moved.edges}
    assert next(n for n in moved.nodes if n.id == "kb").x == 10.0
    assert next(n for n in moved.nodes if n.id == "kb").y == 20.0


def test_TC_UNIT_R26_035_canonical_default_fallback_when_default_not_active():
    """边界：默认专家不在启用集合时，__else__ 回落到第一个启用专家（不产生悬空边）。"""
    experts = (expert("a", default=False), expert("b"))
    g = canonical_graph_from_experts(experts, "ghost")
    else_target = [e.target for e in g.edges if e.branch_key == ELSE_BRANCH]
    assert else_target == ["a"]
