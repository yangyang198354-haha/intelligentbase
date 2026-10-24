"""MOD-001 core — pure word-frequency logic (implements IFC-001…006)."""
from __future__ import annotations

import collections
import pathlib
import re

_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str, *, ignore_case: bool = False, min_length: int = 1) -> list[str]:
    """IFC-001: extract words (Unicode letters/digits), optional case folding."""
    if ignore_case:
        text = text.lower()
    words = _TOKEN.findall(text)
    if min_length > 1:
        words = [word for word in words if len(word) >= min_length]
    return words


def count_words(
    text: str, *, ignore_case: bool = False, min_length: int = 1
) -> collections.Counter[str]:
    """IFC-002: count every token produced by IFC-001."""
    return collections.Counter(
        tokenize(text, ignore_case=ignore_case, min_length=min_length)
    )


def top_words(
    counter: collections.Counter[str], top: int = 10
) -> list[tuple[str, int]]:
    """IFC-003: count desc, then word asc; non-positive ``top`` yields nothing."""
    if top <= 0:
        return []
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:top]


def format_report(items: collections.abc.Sequence[tuple[str, int]]) -> str:
    """IFC-004: one ``word<TAB>count`` line per item, no trailing newline."""
    return "\n".join(f"{word}\t{count}" for word, count in items)


def read_text(path: pathlib.Path) -> str:
    """IFC-005: read UTF-8; OSError / UnicodeDecodeError propagate to IFC-008."""
    return path.read_text(encoding="utf-8")


def run(
    path: str | pathlib.Path,
    *,
    top: int = 10,
    ignore_case: bool = False,
    min_length: int = 1,
) -> str:
    """IFC-006: read, count, rank and format in one call."""
    counter = count_words(
        read_text(pathlib.Path(path)),
        ignore_case=ignore_case,
        min_length=min_length,
    )
    return format_report(top_words(counter, top))
