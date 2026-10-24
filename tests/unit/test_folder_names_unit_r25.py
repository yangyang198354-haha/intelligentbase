"""[R25 / GROUP_D] 单元 —— 名称规则、同名比较键、自动改名（MOD-001 / IFC-014）。

溯源：US-016（AC-016-01/02/03）、US-011（AC-011-02/05）、US-004（AC-004-02）。
纯函数，无 IO。
"""

from __future__ import annotations

import pytest

from ib.core.library import (
    NAME_MAX_LEN,
    EntryNameError,
    EntryLocation,
    name_key_of,
    next_free_name,
    validate_entry_name,
)


@pytest.mark.parametrize(
    "raw,code",
    [
        ("", "name_empty"),
        ("   ", "name_empty"),
        ("a/b", "name_illegal_char"),
        ("a\\b", "name_illegal_char"),
        (".", "name_illegal_char"),
        ("..", "name_illegal_char"),
        ("a\x00b", "name_illegal_char"),
        ("x" * (NAME_MAX_LEN + 1), "name_too_long"),
    ],
)
def test_TC_UNIT_R25_001_invalid_names_rejected_with_stable_code(raw, code):
    """[TC-UNIT-R25-001] AC-016-01：空白 / 含 / 或 \\ / 超过 255 字符 → 拒绝并给出稳定错误码。"""
    with pytest.raises(EntryNameError) as err:
        validate_entry_name(raw)
    assert err.value.code == code


def test_TC_UNIT_R25_002_valid_names_accepted_and_stripped():
    """[TC-UNIT-R25-002] AC-016-02：合法名称（含空格、中文、恰 255 字符）通过，且 strip 后返回展示名。"""
    assert validate_entry_name("2026 规范 v2") == "2026 规范 v2"
    assert validate_entry_name("  设计  ") == "设计"
    assert validate_entry_name("x" * NAME_MAX_LEN) == "x" * NAME_MAX_LEN


def test_TC_UNIT_R25_003_name_key_is_case_and_unicode_insensitive():
    """[TC-UNIT-R25-003] AC-016-03 / AC-011-05：`Design`/`design`/`DESIGN`、`A.pdf`/`a.pdf` 同键；NFC 等价同键；不同名不同键。"""
    assert name_key_of("Design") == name_key_of("design") == name_key_of("DESIGN")
    assert name_key_of("A.pdf") == name_key_of("a.pdf")
    # 非 ASCII：ß / SS、组合字符 é 与预组合 é 在 casefold+NFC 下同键（SQLite NOCASE 做不到，ADR-002）
    assert name_key_of("Straße") == name_key_of("STRASSE")
    assert name_key_of("é") == name_key_of("é")
    assert name_key_of("a.pdf") != name_key_of("b.pdf")


def test_TC_UNIT_R25_004_next_free_name_sequence_for_files_and_folders():
    """[TC-UNIT-R25-004] AC-011-02：文件 `a.pdf` → `a (2).pdf`，被占用则 `a (3).pdf`；文件夹 `A` → `A (2)`；原名未占用原样返回。"""
    assert next_free_name("a.pdf", set(), is_file=True) == "a.pdf"
    assert next_free_name("a.pdf", {name_key_of("a.pdf")}, is_file=True) == "a (2).pdf"
    taken = {name_key_of("a.pdf"), name_key_of("a (2).pdf")}
    assert next_free_name("a.pdf", taken, is_file=True) == "a (3).pdf"
    assert next_free_name("A", {name_key_of("a")}, is_file=False) == "A (2)"
    # 大小写变体同样视为占用（AC-011-05：上传 a.pdf 遇 A.pdf → a (2).pdf）
    assert next_free_name("a.pdf", {name_key_of("A.pdf")}, is_file=True) == "a (2).pdf"


def test_TC_UNIT_R25_005_next_free_name_respects_length_cap_keeping_extension():
    """[TC-UNIT-R25-005] 边界：改名后超 255 字符时截断主名、保留扩展名与序号（结果仍 ≤255）。"""
    long_name = "x" * 251 + ".pdf"  # 255 字符
    out = next_free_name(long_name, {name_key_of(long_name)}, is_file=True)
    assert len(out) <= NAME_MAX_LEN and out.endswith(" (2).pdf")


def test_TC_UNIT_R25_006_entry_location_path_root_has_no_prefix():
    """[TC-UNIT-R25-006] AC-014-01/02：目录路径 `a/b/文件`；根目录文件仅文件名，无空前缀或多余 `/`。"""
    nested = EntryLocation("d1", "方案.pdf", "f2", ("技术文档", "设计"))
    assert nested.path == "技术文档/设计/方案.pdf"
    root = EntryLocation("d2", "根文件.txt", "", ())
    assert root.path == "根文件.txt" and not root.path.startswith("/")
