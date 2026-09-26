"""
@module MOD-IB-18 / MOD-IB-19（包入口）
@implements 见 ib.routing.semantic（IFC-IB-191~193）与 ib.routing.intent（IFC-IB-201~203）
@depends MOD-IB-01, MOD-IB-09, MOD-IB-16, MOD-IB-17
@author sub_agent_software_developer

路由包的**统一出口**。分成两个子模块而非一个，是因为两者变更频率与可测性完全不同：

  * `semantic.py`（MOD-IB-18）：**纯数学 + 一次远端向量化**。除向量化外全是纯函数，
    阈值调优时只改这里，且可在无网络环境下全量单测（AC-IB-15-03）。
  * `intent.py`（MOD-IB-19）：**策略与兜底顺序**。这里定义「谁优先、谁兜底」，
    改动直接影响用户能否得到回答，需要更谨慎的评审与更长的观测期。

把「打分」与「策略」放在同一个文件里，会让阈值调优的 diff 与兜底顺序变更的 diff 混在一起，
评审时难以区分「这是调参还是改行为」—— 分开后两种改动的风险等级一目了然。
"""

from __future__ import annotations

from ib.routing.intent import (
    MAX_ROUTE_EXPERTS,
    IntentRouter,
    current_query,
    guard_against_misroute,
    parse_route_output,
)
from ib.routing.semantic import (
    DEFAULT_MARGIN,
    DEFAULT_TAU,
    SemanticRouter,
    cosine,
    decide,
    score_experts,
)

__all__ = [
    # semantic（MOD-IB-18）
    "SemanticRouter",
    "score_experts",
    "decide",
    "cosine",
    "DEFAULT_TAU",
    "DEFAULT_MARGIN",
    # intent（MOD-IB-19）
    "IntentRouter",
    "parse_route_output",
    "guard_against_misroute",
    "current_query",
    "MAX_ROUTE_EXPERTS",
]
