"""Unit tests for MOD-001 core (IFC-001…006)."""
from __future__ import annotations

import pytest

from wordfreq.core import (
    count_words,
    format_report,
    read_text,
    run,
    tokenize,
    top_words,
)


@pytest.mark.unit
def test_tokenize_and_count_basic() -> None:
    """TC-UNIT-001 / AC-001-01."""
    counter = count_words("apple banana apple")
    assert counter == {"apple": 2, "banana": 1}
    assert top_words(counter) == [("apple", 2), ("banana", 1)]


@pytest.mark.unit
def test_empty_text_yields_empty_report() -> None:
    """TC-UNIT-002 / AC-001-02."""
    assert count_words("") == {}
    assert format_report([]) == ""


@pytest.mark.unit
def test_top_words_respects_limit_and_short_input() -> None:
    """TC-UNIT-003 / AC-002-01, AC-002-02."""
    counter = count_words("e d c b a")
    assert top_words(counter, 2) == [("a", 1), ("b", 1)]
    assert len(top_words(counter, 5)) == 5
    assert top_words(counter, 0) == []
    assert top_words(counter, -3) == []


@pytest.mark.unit
def test_ignore_case_folds_tokens() -> None:
    """TC-UNIT-004 / AC-003-01, AC-003-02."""
    text = "Apple apple APPLE banana"
    assert top_words(count_words(text, ignore_case=True)) == [
        ("apple", 3),
        ("banana", 1),
    ]
    assert top_words(count_words(text)) == [
        ("APPLE", 1),
        ("Apple", 1),
        ("apple", 1),
        ("banana", 1),
    ]


@pytest.mark.unit
def test_min_length_filters() -> None:
    """TC-UNIT-005 / AC-004-01, AC-004-02."""
    text = "a bb ccc dd eee"
    assert top_words(count_words(text, min_length=3)) == [("ccc", 1), ("eee", 1)]
    assert len(tokenize(text)) == 5
    assert top_words(count_words(text, min_length=0)) == [
        ("a", 1),
        ("bb", 1),
        ("ccc", 1),
        ("dd", 1),
        ("eee", 1),
    ]


@pytest.mark.unit
def test_tie_break_is_lexicographic() -> None:
    """TC-UNIT-006 / AC-005-01."""
    assert top_words(count_words("b a b a c")) == [("a", 2), ("b", 2), ("c", 1)]


@pytest.mark.unit
def test_punctuation_separates_words() -> None:
    """TC-UNIT-007 / AC-005-02."""
    assert top_words(count_words("foo,bar.baz;foo")) == [
        ("foo", 2),
        ("bar", 1),
        ("baz", 1),
    ]


@pytest.mark.unit
def test_unicode_words_and_format_contract() -> None:
    """TC-UNIT-008 / AC-007-02（并锁定 IFC-004 输出契约）."""
    items = top_words(count_words("中文 中文 测试"))
    assert items == [("中文", 2), ("测试", 1)]
    assert format_report(items) == "中文\t2\n测试\t1"


@pytest.mark.unit
def test_read_text_is_utf8_and_raises_on_missing(tmp_path) -> None:
    """TC-UNIT-009 / AC-006-01（core 侧契约）."""
    sample = tmp_path / "sample.txt"
    sample.write_bytes("café café".encode("utf-8"))
    assert count_words(read_text(sample)) == {"café": 2}
    with pytest.raises(FileNotFoundError):
        read_text(tmp_path / "missing.txt")


@pytest.mark.unit
def test_run_composes_pipeline(tmp_path) -> None:
    """TC-UNIT-010 / AC-001-01, AC-002-02."""
    sample = tmp_path / "sample.txt"
    sample.write_text("one two two three three three", encoding="utf-8")
    assert run(sample, top=2) == "three\t3\ntwo\t2"
