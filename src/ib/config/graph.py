"""
@module MOD-R26-02
@implements IFC-R26-010 (validate_graph) / IFC-R26-011 (canonical_graph_from_experts)
            IFC-R26-012 (layerize_graph) / IFC-R26-013 (evaluate_condition)
@depends MOD-R26-01

图纯函数（REQ-NFUNC-013）：framework-free、无 I/O、同输入同输出，可离线穷举单测。
非法输入一律以校验错误项返回，不抛异常（`layerize_graph` 的前置条件违反除外）。
"""

from __future__ import annotations

import math
import re
from collections import deque
from dataclasses import dataclass
from typing import Mapping

from ib.core import (
    ELSE_BRANCH,
    RELAY_PREFIX,
    ConditionBranch,
    ConditionPredicate,
    ExpertSpecInput,
    GraphEdge,
    GraphNode,
    GraphSpec,
    ValidationErrorItem,
)
from ib.core.graph import GRAPH_MAX_EDGES, GRAPH_MAX_NODES, NODE_ID_PATTERN, POSITION_ABS_MAX

__all__ = [
    "validate_graph",
    "canonical_graph_from_experts",
    "layerize_graph",
    "evaluate_condition",
    "RelayNode",
    "PlannedEdge",
    "LayerPlan",
    "DEGRADED_BRANCH",
]

#: `upstream_degraded` 谓词的固定分支键（不由用户配置）。
DEGRADED_BRANCH = "degraded"

_NODE_KINDS = ("start", "end", "route", "agent", "condition", "join", "confirm")
_ID_RE = re.compile(NODE_ID_PATTERN)
_BRANCH_KEY_MAX = 32
_KEYWORD_MAX = 32
_KEYWORDS_PER_BRANCH_MAX = 20
_CONFIRM_MESSAGE_MAX = 200


def _err(path: str, code: str, message: str) -> ValidationErrorItem:
    return ValidationErrorItem(path=path, code=code, message=message)


# --------------------------------------------------------------------------- #
# IFC-R26-010 validate_graph
# --------------------------------------------------------------------------- #


def validate_graph(
    graph: GraphSpec,
    *,
    experts: tuple[ExpertSpecInput, ...],
    default_expert: str,
) -> tuple[ValidationErrorItem, ...]:
    """图合法性校验。返回空元组 = 合法。O(V+E)，不抛异常，message 不回显提示词 / 凭据。"""
    if len(graph.nodes) > GRAPH_MAX_NODES or len(graph.edges) > GRAPH_MAX_EDGES:
        return (
            _err(
                "graph",
                "graph_too_large",
                f"图规模超限：节点 {len(graph.nodes)}/{GRAPH_MAX_NODES}，边 {len(graph.edges)}/{GRAPH_MAX_EDGES}",
            ),
        )
    errs: list[ValidationErrorItem] = []
    by_name = {e.name: e for e in experts}

    # ---- 节点 ----
    ids: dict[str, GraphNode] = {}
    kind_ok: set[str] = set()
    for n in graph.nodes:
        p = f"graph.nodes[{n.id}]"
        if n.id in ids:
            errs.append(_err(p, "graph_node_id_duplicate", f"节点 id 重复：{n.id}"))
            continue
        ids[n.id] = n
        if n.kind not in _NODE_KINDS:
            errs.append(_err(p, "graph_node_kind_unknown", "节点类型未知"))
            continue
        kind_ok.add(n.id)
        if n.kind != "agent":
            if n.id.startswith("__") or n.id == ELSE_BRANCH:
                errs.append(_err(p, "graph_node_id_reserved", "节点 id 使用了保留前缀"))
            elif not _ID_RE.match(n.id):
                errs.append(_err(p, "graph_node_id_invalid", "节点 id 须匹配 [a-z0-9][a-z0-9_-]{0,47}"))
        elif n.id.startswith("__"):
            errs.append(_err(p, "graph_node_id_reserved", "节点 id 使用了保留前缀"))
        if not (
            isinstance(n.x, (int, float))
            and isinstance(n.y, (int, float))
            and math.isfinite(n.x)
            and math.isfinite(n.y)
            and abs(n.x) <= POSITION_ABS_MAX
            and abs(n.y) <= POSITION_ABS_MAX
        ):
            errs.append(_err(p, "graph_position_invalid", "节点坐标须为有限数且绝对值不超过 100000"))

    starts = [n for n in graph.nodes if n.kind == "start"]
    ends = [n for n in graph.nodes if n.kind == "end"]
    if len(starts) != 1 or len(ends) != 1:
        errs.append(
            _err("graph", "graph_start_end_count", f"开始 / 结束节点须各恰好一个（当前 {len(starts)} / {len(ends)}）")
        )

    agent_seen: set[str] = set()
    for n in graph.nodes:
        p = f"graph.nodes[{n.id}]"
        if n.id not in kind_ok or ids[n.id] is not n:
            continue
        if n.kind == "agent":
            exp = n.expert
            if exp is None or exp not in by_name:
                errs.append(_err(p, "graph_agent_expert_unknown", "agent 节点引用的专家不存在"))
            else:
                if exp != n.id:
                    errs.append(_err(p, "graph_agent_id_mismatch", "agent 节点 id 须等于其专家名"))
                if by_name[exp].status != "active":
                    errs.append(_err(p, "graph_agent_expert_disabled", "agent 节点引用了已停用的专家"))
                if exp in agent_seen:
                    errs.append(_err(p, "graph_agent_duplicate", "同一专家只能对应一个 agent 节点"))
                agent_seen.add(exp)
        elif n.kind == "confirm":
            if not (1 <= len(n.message.strip()) and len(n.message) <= _CONFIRM_MESSAGE_MAX):
                errs.append(_err(p, "graph_confirm_message_invalid", "人工确认话术须为 1..200 字符"))
        elif n.kind == "condition":
            errs.extend(_check_predicate(n, p))

    # ---- 边 ----
    edge_ids: set[str] = set()
    pair_seen: set[tuple[str, str, str | None]] = set()
    good_edges: list[GraphEdge] = []
    for e in graph.edges:
        p = f"graph.edges[{e.id}]"
        if not _ID_RE.match(e.id):
            errs.append(_err(p, "graph_edge_id_invalid", "边 id 须匹配 [a-z0-9][a-z0-9_-]{0,47}"))
        if e.id in edge_ids:
            errs.append(_err(p, "graph_edge_id_duplicate", f"边 id 重复：{e.id}"))
        edge_ids.add(e.id)
        if e.source not in ids or e.target not in ids:
            errs.append(_err(p, "graph_edge_endpoint_missing", "边的端点节点不存在"))
            continue
        if e.source == e.target:
            errs.append(_err(p, "graph_edge_self_loop", "边不得自环"))
            continue
        key = (e.source, e.target, e.branch_key)
        if key in pair_seen:
            errs.append(_err(p, "graph_edge_duplicate", "存在重复的边"))
            continue
        pair_seen.add(key)
        good_edges.append(e)

    out_of: dict[str, list[GraphEdge]] = {i: [] for i in ids}
    in_of: dict[str, list[GraphEdge]] = {i: [] for i in ids}
    for e in good_edges:
        out_of[e.source].append(e)
        in_of[e.target].append(e)

    for n in graph.nodes:
        if n.id not in kind_ok or ids[n.id] is not n:
            continue
        p = f"graph.nodes[{n.id}]"
        outs, ins = out_of[n.id], in_of[n.id]
        if n.kind == "start" and ins:
            errs.append(_err(p, "graph_start_has_incoming", "开始节点不得有入边"))
        if n.kind == "end" and outs:
            errs.append(_err(p, "graph_end_has_outgoing", "结束节点不得有出边"))
        if n.kind == "join" and len(ins) < 2:
            errs.append(_err(p, "graph_join_inputs", "汇聚节点至少需要两条入边"))
        if n.kind in ("route", "condition"):
            errs.extend(_check_branching(n, outs, ids, by_name))
        else:
            for e in outs:
                if e.branch_key is not None:
                    errs.append(
                        _err(
                            f"graph.edges[{e.id}]",
                            "graph_branch_source_invalid",
                            "只有路由 / 条件分支节点的出边可以携带分支键",
                        )
                    )

    # ---- 结构：环 / 可达 ----
    cyc = _cycle_nodes(list(ids), good_edges)
    if cyc:
        errs.append(_err("graph", "graph_cycle", "图中存在环：" + ", ".join(sorted(cyc))))
    if len(starts) == 1:
        reach = _reach({starts[0].id}, out_of)
        for nid in ids:
            if nid not in reach:
                errs.append(
                    _err(f"graph.nodes[{nid}]", "graph_unreachable_from_start", "节点从开始节点不可达")
                )
    else:
        reach = set()
    if len(ends) == 1:
        rev: dict[str, list[GraphEdge]] = {i: [] for i in ids}
        for e in good_edges:
            rev[e.target].append(e)
        back = _reach({ends[0].id}, {k: [GraphEdge(x.id, x.target, x.source) for x in v] for k, v in rev.items()})
        for nid in ids:
            if nid not in back:
                errs.append(_err(f"graph.nodes[{nid}]", "graph_no_path_to_end", "节点无法到达结束节点"))

    # ---- 默认专家 ----
    if default_expert not in agent_seen or default_expert not in by_name:
        errs.append(
            _err("graph", "graph_default_expert_missing", "默认专家必须作为 agent 节点出现在图中")
        )
    elif len(starts) == 1 and default_expert not in reach:
        errs.append(
            _err("graph", "graph_default_expert_unreachable", "默认专家从开始节点不可达")
        )
    return tuple(errs)


def _check_predicate(n: GraphNode, p: str) -> list[ValidationErrorItem]:
    pr = n.predicate
    if pr is None:
        return [_err(p, "graph_condition_predicate_missing", "条件分支节点缺少判定谓词")]
    if pr.kind == "upstream_degraded":
        if pr.branches:
            return [_err(p, "graph_condition_branch_invalid", "上游降级谓词不接受自定义分支")]
        return []
    if pr.kind != "keyword" or not pr.branches:
        return [_err(p, "graph_condition_branch_invalid", "关键词谓词至少需要一个分支")]
    out: list[ValidationErrorItem] = []
    seen: set[str] = set()
    for b in pr.branches:
        bad = (
            not b.key
            or len(b.key) > _BRANCH_KEY_MAX
            or b.key == ELSE_BRANCH
            or b.key in seen
            or not (1 <= len(b.keywords) <= _KEYWORDS_PER_BRANCH_MAX)
            or any((not k.strip()) or len(k) > _KEYWORD_MAX for k in b.keywords)
        )
        seen.add(b.key)
        if bad:
            out.append(_err(p, "graph_condition_branch_invalid", "条件分支键或关键词不合法"))
            break
    return out


def _check_branching(
    n: GraphNode,
    outs: list[GraphEdge],
    ids: Mapping[str, GraphNode],
    by_name: Mapping[str, ExpertSpecInput],
) -> list[ValidationErrorItem]:
    out: list[ValidationErrorItem] = []
    p = f"graph.nodes[{n.id}]"
    keys: dict[str, int] = {}
    for e in outs:
        ep = f"graph.edges[{e.id}]"
        if e.branch_key is None:
            out.append(_err(ep, "graph_always_edge_from_branching_node", "分支节点的出边必须带分支键"))
            continue
        keys[e.branch_key] = keys.get(e.branch_key, 0) + 1
        if n.kind == "route" and e.branch_key != ELSE_BRANCH:
            tgt = ids.get(e.target)
            if tgt is None or tgt.kind != "agent" or tgt.expert != e.branch_key or e.branch_key not in by_name:
                out.append(
                    _err(ep, "graph_route_branch_target_invalid", "路由分支键须为目标 agent 的专家名或 __else__")
                )
        if n.kind == "condition" and n.predicate is not None and e.branch_key != ELSE_BRANCH:
            pr = n.predicate
            allowed = {DEGRADED_BRANCH} if pr.kind == "upstream_degraded" else {b.key for b in pr.branches}
            if e.branch_key not in allowed:
                out.append(_err(ep, "graph_condition_branch_invalid", "分支键不在谓词声明的分支内"))
    if ELSE_BRANCH not in keys:
        out.append(_err(p, "graph_branch_else_missing", "分支节点必须有 __else__ 出边"))
    for k, c in keys.items():
        if c > 1:
            code = "graph_branch_else_multiple" if k == ELSE_BRANCH else "graph_branch_key_duplicate"
            out.append(_err(p, code, "分支键重复" if k != ELSE_BRANCH else "__else__ 出边出现多次"))
    return out


def _reach(seed: set[str], out_of: Mapping[str, list[GraphEdge]]) -> set[str]:
    seen = set(seed)
    dq = deque(seed)
    while dq:
        cur = dq.popleft()
        for e in out_of.get(cur, ()):
            if e.target not in seen:
                seen.add(e.target)
                dq.append(e.target)
    return seen


def _cycle_nodes(ids: list[str], edges: list[GraphEdge]) -> set[str]:
    indeg = {i: 0 for i in ids}
    adj: dict[str, list[str]] = {i: [] for i in ids}
    for e in edges:
        indeg[e.target] += 1
        adj[e.source].append(e.target)
    dq = deque(i for i, d in indeg.items() if d == 0)
    done = 0
    while dq:
        cur = dq.popleft()
        done += 1
        for t in adj[cur]:
            indeg[t] -= 1
            if indeg[t] == 0:
                dq.append(t)
    if done == len(ids):
        return set()
    return {i for i, d in indeg.items() if d > 0}


# --------------------------------------------------------------------------- #
# IFC-R26-011 canonical_graph_from_experts
# --------------------------------------------------------------------------- #


def canonical_graph_from_experts(
    experts: tuple[ExpertSpecInput, ...],
    default_expert: str,
    *,
    positions: Mapping[str, tuple[float, float]] | None = None,
) -> GraphSpec:
    """规范化默认图：START → route-1 → 每个启用专家(agent, query_only) → END。"""
    active = [e for e in experts if e.status == "active"]
    pos = positions or {}

    def at(node_id: str, dx: float, dy: float) -> tuple[float, float]:
        return pos.get(node_id, (dx, dy))

    nodes: list[GraphNode] = []
    sx, sy = at("start", 0.0, 0.0)
    nodes.append(GraphNode(id="start", kind="start", x=sx, y=sy))
    rx, ry = at("route-1", 220.0, 0.0)
    nodes.append(GraphNode(id="route-1", kind="route", x=rx, y=ry))
    for i, e in enumerate(active):
        ax, ay = at(e.name, 460.0, 110.0 * i)
        nodes.append(GraphNode(id=e.name, kind="agent", x=ax, y=ay, expert=e.name, input_mode="query_only"))
    ex, ey = at("end", 700.0, 0.0)
    nodes.append(GraphNode(id="end", kind="end", x=ex, y=ey))

    edges: list[GraphEdge] = [GraphEdge(id="e-start", source="start", target="route-1")]
    names = [e.name for e in active]
    for i, nm in enumerate(names):
        edges.append(GraphEdge(id=f"e-r{i + 1}", source="route-1", target=nm, branch_key=nm))
    else_target = default_expert if default_expert in names else (names[0] if names else "end")
    edges.append(GraphEdge(id="e-else", source="route-1", target=else_target, branch_key=ELSE_BRANCH))
    for i, nm in enumerate(names):
        edges.append(GraphEdge(id=f"e-o{i + 1}", source=nm, target="end"))
    return GraphSpec(nodes=tuple(nodes), edges=tuple(edges))


# --------------------------------------------------------------------------- #
# IFC-R26-012 layerize_graph
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RelayNode:
    id: str  # f"{RELAY_PREFIX}{edge_id}_{k}"
    edge_id: str
    level: int


@dataclass(frozen=True, slots=True)
class PlannedEdge:
    source: str
    target: str
    branch_key: str | None  # 仅原边第一跳携带分支键
    origin_edge_id: str


@dataclass(frozen=True, slots=True)
class LayerPlan:
    levels: Mapping[str, int]
    relays: tuple[RelayNode, ...]
    edges: tuple[PlannedEdge, ...]
    max_level: int


def layerize_graph(graph: GraphSpec) -> LayerPlan:
    """按最长路径定层，并对跨多层的边插入无操作中继节点，使每条边恰好跨 1 层（ADR-57）。

    前置条件：`validate_graph` 返回空；违反抛 ValueError（编程错误，非用户输入路径）。
    """
    ids = [n.id for n in graph.nodes]
    idset = set(ids)
    starts = [n.id for n in graph.nodes if n.kind == "start"]
    if len(starts) != 1:
        raise ValueError("layerize_graph: 前置条件违反（开始节点数 != 1）")
    indeg = {i: 0 for i in ids}
    adj: dict[str, list[GraphEdge]] = {i: [] for i in ids}
    for e in graph.edges:
        if e.source not in idset or e.target not in idset:
            raise ValueError("layerize_graph: 前置条件违反（边端点不存在）")
        indeg[e.target] += 1
        adj[e.source].append(e)
    level = {i: 0 for i in ids}
    dq = deque(i for i in ids if indeg[i] == 0)
    done = 0
    while dq:
        cur = dq.popleft()
        done += 1
        for e in adj[cur]:
            level[e.target] = max(level[e.target], level[cur] + 1)
            indeg[e.target] -= 1
            if indeg[e.target] == 0:
                dq.append(e.target)
    if done != len(ids):
        raise ValueError("layerize_graph: 前置条件违反（图中有环）")
    relays: list[RelayNode] = []
    planned: list[PlannedEdge] = []
    for e in graph.edges:
        span = level[e.target] - level[e.source]
        prev = e.source
        for k in range(1, span):
            rid = f"{RELAY_PREFIX}{e.id}_{k}"
            relays.append(RelayNode(id=rid, edge_id=e.id, level=level[e.source] + k))
            planned.append(PlannedEdge(prev, rid, e.branch_key if k == 1 else None, e.id))
            prev = rid
        planned.append(PlannedEdge(prev, e.target, e.branch_key if span <= 1 else None, e.id))
    return LayerPlan(
        levels=level,
        relays=tuple(relays),
        edges=tuple(planned),
        max_level=max(level.values()) if level else 0,
    )


# --------------------------------------------------------------------------- #
# IFC-R26-013 evaluate_condition
# --------------------------------------------------------------------------- #


def evaluate_condition(
    predicate: ConditionPredicate,
    *,
    query: str,
    upstream_degraded: bool,
) -> str:
    """返回命中的分支键，否则 ELSE_BRANCH。无表达式 / 代码执行（OQ-R26-A03）。"""
    if predicate.kind == "upstream_degraded":
        return DEGRADED_BRANCH if upstream_degraded else ELSE_BRANCH
    q = query.strip().lower()
    for b in predicate.branches:
        for kw in b.keywords:
            k = kw.strip().lower()
            if k and k in q:
                return b.key
    return ELSE_BRANCH
