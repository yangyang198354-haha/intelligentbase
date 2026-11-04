# MOD-R28-10 / implements IFC-R28-016（纯函数） / depends MOD-R28-01
"""事实保真守卫（ADR-R28-09）：抽取“保护片段”并核对最终文本；网页引用长度上限。"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal, Sequence

__all__ = ["protected_spans", "check_fidelity", "exceeds_quote_limit", "retry_instruction", "ApologyReason"]

#: 仅用于日志 / 断言；不是 degrade_reason，对外响应不可见。
ApologyReason = Literal["summary_failed", "fidelity_failed"]

_URL = r"https?://[^\s<>\"'，。；、）)】》]+"
_NUMBER = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|\d+(?:\.\d+)?%?"
_BOOK = r"《[^》\n]{1,80}》"
_POSITION = r"第\s*[0-9一二三四五六七八九十百零]+\s*[条页节章]"
_SPAN_RE = re.compile("|".join(f"(?:{p})" for p in (_URL, _BOOK, _POSITION, _NUMBER)))


def _norm(text: str) -> str:
    """全角 / 半角与空白归一（NFKC + 去空白）。"""
    return "".join(unicodedata.normalize("NFKC", text).split())


def protected_spans(texts: Sequence[str]) -> tuple[str, ...]:
    """数字串（含小数 / 千分位 / 百分号）、《…》、第N条/页/节、http(s) 网址；去重保序。"""
    seen: dict[str, None] = {}
    for t in texts:
        for m in _SPAN_RE.finditer(t or ""):
            span = m.group(0).rstrip(".,;:")
            if span and span not in seen:
                seen[span] = None
    return tuple(seen)


def check_fidelity(upstream_texts: Sequence[str], final_text: str) -> tuple[str, ...]:
    """返回最终文本中缺失的保护片段（空 = 通过；全半角 / 空白归一后比较）。"""
    final = _norm(final_text or "")
    final_plain = final.replace(",", "")
    missing: list[str] = []
    for span in protected_spans(upstream_texts):
        n = _norm(span)
        if n in final or n.replace(",", "") in final_plain:
            continue
        missing.append(span)
    return tuple(missing)


def exceeds_quote_limit(web_texts: Sequence[str], final_text: str, *, max_span: int = 200) -> bool:
    """最终文本与网页正文存在连续 ≥ max_span 字符的逐字重叠 ⇒ True（AC-018-04）。"""
    final = " ".join((final_text or "").split())
    if len(final) < max_span:
        return False
    for w in web_texts:
        src = " ".join((w or "").split())
        if len(src) < max_span:
            continue
        for i in range(0, len(final) - max_span + 1):
            if final[i : i + max_span] in src:
                return True
    return False


def retry_instruction(missing: Sequence[str]) -> str:
    items = "、".join(missing)
    return f"以下信息必须原样保留：{items}"
