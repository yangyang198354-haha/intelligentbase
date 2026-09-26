"""
@module MOD-IB-18
@implements IFC-IB-191 score_experts / 192 decide / 193 SemanticRouter.route
@depends MOD-IB-01, MOD-IB-09, MOD-IB-16
@author sub_agent_software_developer

语义路由（module_design.md §3 MOD-IB-18 / §7.2 的 L1 层；REQ-FUNC-IB-19）。

## 它在四级路由里的位置：**关键词与 LLM 之间的高置信中间层**

```
L0 关键词唯一命中 ──（够不着/多义）──▶ L1 语义高置信 ──（不够自信）──▶ L2 LLM 分类 ──▶ L3 关键词多重
```

L0 是确定性的但「只认字面」；L2（LLM）理解力强但要花一次云端调用、且遇到极短提问会摇摆。
L1 正好补这两者之间的空档：**用向量近邻判断「这句话像不像某专家的历史提问」**，
只在**非常自信**时才短路（跳过 LLM 调用，省钱又降延迟），否则**穿透**给 L2。

`decide()` 的两个门限不可省：
  * `tau`（下限）：连最高分都没到阈值 → 根本不像任何专家，穿透；
  * `margin`（分差）：最高分与次高分太接近 → 这是**复合意图**（同时像两个专家），
    必须交给 LLM 并行扇出，而不是武断二选一。

## fail-open 是硬要求

`route()` **恒不抛异常**，任何情况（embedding 不可达、范例未装载、维度不符、超时）
一律返回 `None` = 「我不确定，交给下一级」。理由：L1 是**可选的加速层**，
它的失败绝不该让问答失败 —— 而 `None` 恰好是「正常穿透」的语义，故失败与「不确定」
可以共用同一出口，无需额外的错误传播机制。

## 范例按 `project_id` 分区（FM-6）

不同项目的领域词汇完全不同（一栋楼问「三恒原理」，另一栋问「水泵台账」）。
若共用一份范例，A 项目的提问可能因**字面相似**而被路由到 B 项目语义的专家上。
故范例以 `project_id` 为键分区，且查不到该项目的范例时**返回 `None`**（穿透），
绝不回落到「所有项目的范例」。
"""

from __future__ import annotations

import math
import threading
from typing import Any, Callable, Iterable, Sequence

from ib.core import Scope

__all__ = [
    "score_experts",
    "decide",
    "SemanticRouter",
    "DEFAULT_TAU",
    "DEFAULT_MARGIN",
    "cosine",
]

#: 高置信阈值（"top 分数 ≥ tau"）。源自 FreeArk Phase-0 PoC 标定的 0.65 —— 保守取值：
#: 宁可不短路（多花一次 LLM 调用），也不要误短路（错误路由影响正确性）。
DEFAULT_TAU = 0.65

#: 分差阈值（"top 与次高之差 ≥ margin"）。0.05 同样偏保守：复合意图宁可交给 LLM。
DEFAULT_MARGIN = 0.05


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    """余弦相似度（两端都为零向量时返回 0.0，**不除零**）。

    embedding 通常已归一化，此处仍完整计算：语义路由的范例可能来自未归一化的适配器，
    假设「已归一化」会静默给出错误分数（分数被模长放大），且很难发现。
    """
    if len(left) != len(right):
        raise ValueError(f"向量维度不一致：{len(left)} vs {len(right)}")
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


# --------------------------------------------------------------------------- #
# IFC-IB-191 / 192 纯函数（离线单测主战场，AC-IB-15-03）
# --------------------------------------------------------------------------- #


def score_experts(
    query_vec: Sequence[float], exemplars: dict[str, list[Sequence[float]]]
) -> dict[str, float]:
    """[IFC-IB-191] **纯函数**：每个专家取「其全部范例与 query 的最大余弦」。

    为什么取 **max** 而不是平均：专家的范例本身就是**异质**的（一个专家的历史提问覆盖
    多种说法），平均会被无关范例拉低分数，导致「明明很像」却没过阈值。
    取 max 的语义是「只要像其中任意一种问法，就说明像这个专家」。

    返回 `dict`（契约规定）：分数**未经排序**，排序是 `decide` 的职责 ——
    分开的好处是打分逻辑可以独立测（不依赖排序稳定性）。
    """
    out: dict[str, float] = {}
    for expert, vectors in exemplars.items():
        if not vectors:
            # 空范例的专家不参与打分（给 0 会与「真的不像」混淆）
            continue
        best = None
        for vector in vectors:
            score = cosine(query_vec, vector)
            if best is None or score > best:
                best = score
        out[expert] = float(best)  # type: ignore[arg-type]
    return out


def decide(scores: dict[str, float], tau: float, margin: float) -> str | None:
    """[IFC-IB-192] **纯函数**：`top ≥ tau` 且 `top - second ≥ margin` → 返回 top 专家；否则 `None`。

    平票处理（关键细节）：分数相同时按**专家名的稳定顺序**决出，而不是依赖 `dict` 迭代顺序。
    否则同一句提问在不同进程/不同 Python 版本上可能路由到不同专家（`dict` 保序但构建顺序
    可能来自集合），产生「无法复现的路由」—— 但注意：**平票时分差为 0 < margin（正值），
    实际会返回 `None` 穿透**，故该稳定性主要用于「margin ≤ 0 的极端配置」下仍保持确定性。
    """
    if not scores:
        return None
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top_expert, top_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    if top_score >= tau and (top_score - second_score) >= margin:
        return top_expert
    return None


# --------------------------------------------------------------------------- #
# IFC-IB-193 路由器
# --------------------------------------------------------------------------- #


class SemanticRouter:
    """进程内语义路由器（范例向量懒装载 + 缓存）。

    `embed_texts` 由组合根注入（通常包一层 `Embedder.embed_documents`），
    于是本模块**不静态依赖** MOD-IB-09 的任何具体实现；`exemplars_provider`
    按 `project_id` 返回范例**文本**（FM-6 分区）。
    """

    def __init__(
        self,
        *,
        embed_texts: Callable[[list[str]], list[list[float]]],
        exemplars_provider: Callable[[str], dict[str, list[str]]],
        tau: float = DEFAULT_TAU,
        margin: float = DEFAULT_MARGIN,
    ) -> None:
        self._embed_texts = embed_texts
        self._exemplars_provider = exemplars_provider
        self.tau = float(tau)
        self.margin = float(margin)
        self._lock = threading.Lock()
        #: project_id -> {expert: [vector, ...]}（**已按项目分区**，FM-6）
        self._cache: dict[str, dict[str, list[list[float]]]] = {}
        #: 装载失败的项目（避免每次请求都重试一次必然失败的远端调用）
        self._failed: set[str] = set()

    def route(self, query: str, *, scope: Scope) -> str | None:
        """[IFC-IB-193] 高置信单专家或 `None`。**fail-open：任何异常 → `None`**。"""
        try:
            exemplars = self._exemplars_for(scope.project_id)
            if not exemplars:
                return None
            # 用同一适配器向量化查询（与范例同空间是语义相似的前提）
            vectors = self._embed_texts([query])
            if not vectors:
                return None
            scores = score_experts(vectors[0], exemplars)
            return decide(scores, self.tau, self.margin)
        except Exception:  # noqa: BLE001 - L1 是加速层，失败必须穿透而非中断问答
            return None

    def scores_for(self, query: str, *, scope: Scope) -> dict[str, float]:
        """打分视图（供 MOD-IB-19 的误路由护栏使用）。失败返回 `{}`（等同无信号）。"""
        try:
            exemplars = self._exemplars_for(scope.project_id)
            if not exemplars:
                return {}
            vectors = self._embed_texts([query])
            if not vectors:
                return {}
            return score_experts(vectors[0], exemplars)
        except Exception:  # noqa: BLE001
            return {}

    # ------------------------------------------------------------------ #

    def _exemplars_for(self, project_id: str) -> dict[str, list[list[float]]]:
        """取（并缓存）该项目的范例向量。**只读该项目的分区**（FM-6）。"""
        with self._lock:
            cached = self._cache.get(project_id)
            if cached is not None:
                return cached
            if project_id in self._failed:
                return {}
        texts = self._exemplars_provider(project_id) or {}
        if not texts:
            with self._lock:
                self._cache[project_id] = {}
            return {}
        built: dict[str, list[list[float]]] = {}
        try:
            for expert, items in texts.items():
                if not items:
                    continue
                built[expert] = self._embed_texts(list(items))
        except Exception:  # noqa: BLE001 - 装载失败 → 该项目永久穿透（不反复重试）
            with self._lock:
                self._failed.add(project_id)
            return {}
        with self._lock:
            self._cache[project_id] = built
        return built

    def invalidate(self, project_id: str | None = None) -> None:
        """清缓存（范例集变更后调用）。刻意**不自动失效**：自动过期会让路由在
        「刚重建过范例」的瞬间不可预测。"""
        with self._lock:
            if project_id is None:
                self._cache.clear()
                self._failed.clear()
            else:
                self._cache.pop(project_id, None)
                self._failed.discard(project_id)
