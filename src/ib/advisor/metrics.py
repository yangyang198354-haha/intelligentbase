# MOD-R28-10 / implements IFC-R28-017（纯函数） / depends MOD-R28-01
"""评测指标：意图 top-1 准确率、混淆矩阵、话题 F1、指代消解准确率、专业问题误判为通用并联网外发比例。"""

from __future__ import annotations

from typing import Sequence

__all__ = [
    "intent_top1_accuracy",
    "confusion_matrix",
    "topic_f1",
    "resolution_accuracy",
    "knowledge_to_web_rate",
]


def _check_len(a: Sequence, b: Sequence) -> None:
    if len(a) != len(b):
        raise ValueError("gold 与 pred 长度不一致")


def intent_top1_accuracy(gold: Sequence[str], pred: Sequence[str]) -> float:
    _check_len(gold, pred)
    if not gold:
        return 0.0
    return sum(1 for g, p in zip(gold, pred) if g == p) / len(gold)


def confusion_matrix(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]) -> dict[str, dict[str, int]]:
    _check_len(gold, pred)
    m = {g: {p: 0 for p in labels} for g in labels}
    for g, p in zip(gold, pred):
        if g in m and p in m[g]:
            m[g][p] += 1
    return m


def topic_f1(gold: Sequence[str], pred: Sequence[str], *, positive: str = "switch") -> float:
    _check_len(gold, pred)
    tp = sum(1 for g, p in zip(gold, pred) if g == positive and p == positive)
    fp = sum(1 for g, p in zip(gold, pred) if g != positive and p == positive)
    fn = sum(1 for g, p in zip(gold, pred) if g == positive and p != positive)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def resolution_accuracy(gold: Sequence[str], pred: Sequence[str]) -> float:
    """指代消解准确率：按归一化（去空白）后逐字相等计。"""
    _check_len(gold, pred)
    if not gold:
        return 0.0
    norm = lambda s: "".join((s or "").split())  # noqa: E731
    return sum(1 for g, p in zip(gold, pred) if norm(g) == norm(p)) / len(gold)


def knowledge_to_web_rate(gold: Sequence[str], pred_intents: Sequence[Sequence[str]]) -> float:
    """专业问题（gold == knowledge）被判为通用（含 general 且不含 knowledge/delegate/unknown）的比例。"""
    _check_len(gold, pred_intents)
    pro = [(g, p) for g, p in zip(gold, pred_intents) if g == "knowledge"]
    if not pro:
        return 0.0
    bad = sum(
        1
        for _g, p in pro
        if "general" in p and not any(x in ("knowledge", "delegate", "unknown") for x in p)
    )
    return bad / len(pro)
