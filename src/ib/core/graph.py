# MOD-R26-01 / IFC-R26-001：图规格值对象（framework-free，仅 stdlib）。
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

NodeKind = Literal["start", "end", "route", "agent", "condition", "join", "confirm"]
InputMode = Literal["query_only", "with_upstream"]

#: 分支的兜底键（route / condition 的 `__else__` 出边）。
ELSE_BRANCH: Final[str] = "__else__"
#: 层归一化插入的无操作中继节点 id 前缀。
RELAY_PREFIX: Final[str] = "__relay__"
GRAPH_MAX_NODES: Final[int] = 60  # [ASSUMPTION A-R26-02]
GRAPH_MAX_EDGES: Final[int] = 200
#: 结构节点 id 规则；agent 节点 id = 专家 name（沿用 ExpertSpec 命名规则）。
NODE_ID_PATTERN: Final[str] = r"^[a-z0-9][a-z0-9_-]{0,47}$"
POSITION_ABS_MAX: Final[float] = 100000.0


@dataclass(frozen=True, slots=True)
class ConditionBranch:
    key: str  # 1..32 字符，不得为 ELSE_BRANCH
    keywords: tuple[str, ...] = ()  # kind="keyword" 时 >=1 条，每条 1..32 字符，<=20 条


@dataclass(frozen=True, slots=True)
class ConditionPredicate:
    # OQ-R26-A03：仅关键词与上游降级两种谓词，无表达式 / 代码执行。
    kind: Literal["keyword", "upstream_degraded"]
    branches: tuple[ConditionBranch, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    kind: NodeKind
    x: float = 0.0  # 展示信息
    y: float = 0.0
    expert: str | None = None  # kind="agent" 必填且 == id
    input_mode: InputMode = "query_only"
    predicate: ConditionPredicate | None = None  # kind="condition" 必填
    message: str = ""  # kind="confirm" 必填，1..200 字符


@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: str
    source: str
    target: str
    branch_key: str | None = None  # None = 无条件边；route / condition 出边必须有值


@dataclass(frozen=True, slots=True)
class GraphSpec:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


__all__ = [
    "ELSE_BRANCH",
    "GRAPH_MAX_EDGES",
    "GRAPH_MAX_NODES",
    "NODE_ID_PATTERN",
    "POSITION_ABS_MAX",
    "RELAY_PREFIX",
    "ConditionBranch",
    "ConditionPredicate",
    "GraphEdge",
    "GraphNode",
    "GraphSpec",
    "InputMode",
    "NodeKind",
]
