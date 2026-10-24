# MOD-001 / implements IFC-014（资料库目录：名称规则、name_key、目录相关类型与错误码；纯函数 + 类型，无 IO）
"""资料库（云盘式目录）核心契约：名称校验、同目录唯一性比较键、自动改名与目录相关值类型。

framework-free：仅用 stdlib（`unicodedata`）。本模块不做 IO、不读写台账。
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Collection, Final, Literal, Mapping

from .errors import ConflictError, ValidationError

__all__ = [
    "ROOT_FOLDER_ID",
    "NAME_MAX_LEN",
    "EntryKind",
    "ConflictAction",
    "EntryNameError",
    "validate_entry_name",
    "name_key_of",
    "next_free_name",
    "EntryRef",
    "FolderRecord",
    "NameClash",
    "EntryLocation",
    "LibraryConflictError",
    "LibraryValidationError",
]

#: 根目录的 folder_id（空串）。
ROOT_FOLDER_ID: Final[str] = ""
#: 条目展示名最大长度（字符数）。
NAME_MAX_LEN: Final[int] = 255

EntryKind = Literal["folder", "file"]
ConflictAction = Literal["overwrite", "skip", "rename"]


class EntryNameError(ValidationError):
    """条目名称非法。`code` ∈ {name_empty, name_illegal_char, name_too_long}。"""

    code = "name_empty"

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message, field="name")
        self.code = code


def validate_entry_name(name: str) -> str:
    """strip 后返回规范展示名。

    空/仅空白 → `name_empty`；含 '/' 或 '\\'、控制字符，或名称恰为 '.' / '..' → `name_illegal_char`；
    长度 > 255 → `name_too_long`。
    """
    if not isinstance(name, str):
        raise EntryNameError("名称必须是字符串", code="name_empty")
    cleaned = name.strip()
    if not cleaned:
        raise EntryNameError("名称不能为空", code="name_empty")
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        raise EntryNameError("名称不能包含 / 或 \\，也不能是 . 或 ..", code="name_illegal_char")
    if any(unicodedata.category(ch) == "Cc" for ch in cleaned):
        raise EntryNameError("名称不能包含控制字符", code="name_illegal_char")
    if len(cleaned) > NAME_MAX_LEN:
        raise EntryNameError(f"名称过长（上限 {NAME_MAX_LEN} 个字符）", code="name_too_long")
    return cleaned


def name_key_of(name: str) -> str:
    """同目录唯一性的比较键：NFC 规范化 + casefold（ADR-002）。"""
    return unicodedata.normalize("NFC", name.strip()).casefold()


def _split_ext(name: str) -> tuple[str, str]:
    dot = name.rfind(".")
    if dot <= 0:
        return name, ""
    return name[:dot], name[dot:]


def next_free_name(name: str, taken_keys: Collection[str], *, is_file: bool) -> str:
    """文件 'a.pdf' → 'a (2).pdf'，文件夹 'A' → 'A (2)'；序号顺延至 name_key 不在 taken_keys 中。

    结果长度超过 255 时截断主名、保留扩展名。原名本身未被占用时原样返回。
    """
    if name_key_of(name) not in taken_keys:
        return name
    stem, ext = _split_ext(name) if is_file else (name, "")
    counter = 2
    while True:
        suffix = f" ({counter})"
        room = NAME_MAX_LEN - len(suffix) - len(ext)
        candidate = f"{stem[: max(1, room)]}{suffix}{ext}"
        if name_key_of(candidate) not in taken_keys:
            return candidate
        counter += 1


@dataclass(frozen=True, slots=True)
class EntryRef:
    kind: EntryKind
    entry_id: str


@dataclass(frozen=True, slots=True)
class FolderRecord:
    folder_id: str
    project_id: str
    parent_id: str  # '' = 根
    name: str
    name_key: str
    depth: int  # 根下一级 = 1
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class NameClash:
    """被冲突方（库中已存在的条目）。"""

    kind: EntryKind
    entry_id: str
    name: str


@dataclass(frozen=True, slots=True)
class EntryLocation:
    doc_id: str
    name: str
    folder_id: str
    folder_path: tuple[str, ...]  # 目录名链，根起，不含文件名

    @property
    def path(self) -> str:
        """'/'.join((*folder_path, name))；根目录文件仅 name。"""
        return "/".join((*self.folder_path, self.name))


class LibraryConflictError(ConflictError):
    """同名冲突 / 更新冲突。code ∈ {name_conflict, update_in_progress, doc_busy, unresolved_conflict}。"""

    code = "name_conflict"

    def __init__(
        self,
        message: str,
        *,
        code: str = "name_conflict",
        clashes: tuple[NameClash, ...] = (),
        details: Mapping[str, object] | None = None,
        initiators: tuple[NameClash, ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.clashes = tuple(clashes)
        self.details = details
        #: 与 `clashes` 按下标对应的发起条目（移动场景；上传/更新场景为空）。IFC-014 的增量扩展。
        self.initiators = tuple(initiators)


class LibraryValidationError(ValidationError):
    """目录/批量上传的校验失败。

    code ∈ {depth_exceeded, move_into_self, ext_change_not_allowed, limit_files,
            limit_total_bytes, confirm_required, bad_request}。
    """

    code = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str = "bad_request",
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details
