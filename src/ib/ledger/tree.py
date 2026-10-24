# MOD-002 / implements IFC-015（EntryTreeStore：目录树与条目台账存储；SQLite + 内存两实现，同一份业务逻辑）
"""目录树与条目台账存储（ADR-001 / ADR-002 / ADR-004 / ADR-007）。

结构：业务逻辑只写一份（`_TreeLogic`），两个后端只实现一组很薄的“数据原语”
（`_p_*` 读、`_w_*` 写、`_txn` 事务）。因此 `SqliteEntryTree` 与 `MemoryEntryTree`
的语义一致由构造保证（M-SA-001），端口一致性测试对两者跑同一套断言。

并发（ADR-002）：SQLite 后端的每个变更方法都在 `SqliteLedgerRepository._write()`
（`BEGIN IMMEDIATE`）内“先检查后写入”，部分唯一索引是第二道保险
（`IntegrityError` → `LibraryConflictError`）。内存后端以台账的 RLock 串行化，并在异常时
整体回滚快照，使“全有全无”与 SQLite 一致。

包内协作：`SqliteEntryTree` 复用 `SqliteLedgerRepository` 的连接与写事务（访问其私有
`_conn` / `_write`），`MemoryEntryTree` 复用 `InMemoryLedgerRepository` 的存储与锁。
存储层不做鉴权；所有方法都要求 `Scope`，project 条件显式下推；资源不存在与不属于本项目
一律 `NotFoundError`（不区分，M-SA-007）。
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Any, Iterator, Literal, Mapping, Protocol, Sequence

from ib.context import utc_now_iso
from ib.core import (
    DependencyUnavailableError,
    DocumentRecord,
    NotFoundError,
    Scope,
)
from ib.core.library import (
    ConflictAction,
    EntryLocation,
    EntryRef,
    FolderRecord,
    LibraryConflictError,
    LibraryValidationError,
    NameClash,
    name_key_of,
    next_free_name,
    validate_entry_name,
)
from ib.ledger import _assert_transition

__all__ = [
    "ChildrenPage",
    "SubtreeCount",
    "MoveOutcome",
    "CreatedDocument",
    "PromoteOutcome",
    "PurgeItem",
    "EntryTreeStore",
    "SqliteEntryTree",
    "MemoryEntryTree",
    "build_entry_tree",
]


# --------------------------------------------------------------------------- #
# IFC-015 值类型
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ChildrenPage:
    items: tuple[FolderRecord | DocumentRecord, ...]  # 文件夹在前；(类别, name_key, id) 稳定升序；不含修订行
    total: int


@dataclass(frozen=True, slots=True)
class SubtreeCount:
    folders: int  # 不含自身
    files: int  # 存活文件（不含修订行）


@dataclass(frozen=True, slots=True)
class MoveOutcome:
    moved: tuple[EntryRef, ...]
    skipped: tuple[EntryRef, ...]
    renamed: tuple[tuple[EntryRef, str], ...]  # (条目, 新名称)
    overwritten_doc_ids: tuple[str, ...]  # 已在本事务内移出台账，已入清理队列


@dataclass(frozen=True, slots=True)
class CreatedDocument:
    record: DocumentRecord
    created_folders: tuple[FolderRecord, ...]  # 本次事务新建的目录链（供补偿用）


@dataclass(frozen=True, slots=True)
class PromoteOutcome:
    kind: Literal["promoted", "ready"]  # ready = 已索引但推迟晋升（ADR-007）
    record: DocumentRecord  # promoted: 晋升后的存活行；ready: 修订行本身
    retired_doc_id: str | None  # promoted 时的旧 doc_id（已入清理队列）
    renamed_to: str | None  # 晋升时因重名自动改名后的显示名


@dataclass(frozen=True, slots=True)
class PurgeItem:
    doc_id: str
    project_id: str
    kb_id: str
    reason: str
    attempts: int


class EntryTreeStore(Protocol):
    # ---- 浏览 ----
    def list_children(self, scope: Scope, folder_id: str, *, page: int, page_size: int) -> ChildrenPage: ...
    def get_folder(self, scope: Scope, folder_id: str) -> FolderRecord | None: ...
    def folder_chain(self, scope: Scope, folder_id: str) -> tuple[FolderRecord, ...]: ...
    def count_subtree(self, scope: Scope, folder_id: str) -> SubtreeCount: ...
    def list_subtree_documents(self, scope: Scope, folder_id: str, *, limit: int) -> list[DocumentRecord]: ...
    def list_subtree_folders(self, scope: Scope, folder_id: str) -> list[FolderRecord]: ...  # 增量

    # ---- 目录变更 ----
    def create_folder(self, scope: Scope, parent_id: str, name: str, *, max_depth: int) -> FolderRecord: ...
    def rename_folder(self, scope: Scope, folder_id: str, new_name: str) -> FolderRecord: ...
    def rename_document(self, scope: Scope, doc_id: str, new_name: str) -> DocumentRecord: ...
    def move_entries(
        self,
        scope: Scope,
        entries: Sequence[EntryRef],
        target_folder_id: str,
        resolutions: Mapping[str, ConflictAction],
        *,
        max_depth: int,
    ) -> MoveOutcome: ...
    def delete_empty_folders(self, scope: Scope, folder_ids: Sequence[str]) -> int: ...

    # ---- 文档落库（带目录）----
    def create_document_in(
        self,
        scope: Scope,
        *,
        folder_id: str,
        rel_dirs: Sequence[str],
        name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        on_conflict: Literal["fail", "rename"],
        max_depth: int,
    ) -> CreatedDocument: ...
    def find_name_clashes(
        self, scope: Scope, folder_id: str, names: Sequence[str]
    ) -> dict[str, NameClash]: ...

    # ---- 修订（更新）----
    def create_revision(
        self,
        scope: Scope,
        live_doc_id: str,
        *,
        new_name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        on_conflict: Literal["fail", "rename"],
    ) -> tuple[DocumentRecord, tuple[DocumentRecord, ...]]: ...
    def get_revision_of(self, scope: Scope, live_doc_id: str) -> DocumentRecord | None: ...
    def promote_revision(
        self,
        scope: Scope,
        revision_doc_id: str,
        *,
        collection_version: str,
        chunk_count: int,
        active_version: str,
    ) -> PromoteOutcome: ...
    def list_ready_revisions(
        self, project_id: str, *, active_version: str, limit: int
    ) -> list[DocumentRecord]: ...
    def promote_ready(
        self, scope: Scope, revision_doc_id: str, *, active_version: str
    ) -> PromoteOutcome | None: ...

    # ---- 存活解析 ----
    def resolve_live(self, project_id: str, doc_ids: Sequence[str]) -> dict[str, EntryLocation]: ...

    # ---- 清理队列 ----
    def enqueue_purge(self, project_id: str, kb_id: str, doc_id: str, reason: str) -> None: ...
    def list_purge(self, limit: int) -> list[PurgeItem]: ...
    def ack_purge(self, doc_id: str) -> None: ...
    def bump_purge(self, doc_id: str) -> None: ...  # 增量：失败时 attempts+1（队列项保留）


# --------------------------------------------------------------------------- #
# 业务逻辑（后端无关）
# --------------------------------------------------------------------------- #

_NOT_FOUND = "目录或文件不存在，或不在当前项目内"
_MAX_CHAIN = 256  # 父链遍历的硬上限（防环）


def _clash_error(clashes: Sequence[NameClash]) -> LibraryConflictError:
    return LibraryConflictError("同目录下已存在同名条目", clashes=tuple(clashes))


class _TreeLogic:
    """EntryTreeStore 的业务逻辑；子类提供 `_p_*` / `_w_*` / `_txn` 原语。"""

    # ---- 原语（子类实现）---- #

    def _txn(self):  # pragma: no cover - 抽象
        raise NotImplementedError

    def _p_folder(self, pid: str, folder_id: str) -> FolderRecord | None:  # pragma: no cover
        raise NotImplementedError

    def _p_child_folders(self, pid: str, parent_id: str) -> list[FolderRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_live_docs(self, pid: str, folder_id: str) -> list[DocumentRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_page_children(
        self, pid: str, folder_id: str, offset: int, limit: int
    ) -> tuple[list[FolderRecord | DocumentRecord], int]:  # pragma: no cover
        raise NotImplementedError

    def _p_doc(self, pid: str, doc_id: str) -> DocumentRecord | None:  # pragma: no cover
        raise NotImplementedError

    def _p_revision_of(self, pid: str, live_id: str) -> DocumentRecord | None:  # pragma: no cover
        raise NotImplementedError

    def _p_descendants(self, pid: str, folder_id: str) -> list[FolderRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_docs_in_folders(
        self, pid: str, folder_ids: Sequence[str], *, include_revisions: bool
    ) -> list[DocumentRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_clashes(
        self,
        pid: str,
        folder_id: str,
        keys: Sequence[str],
        *,
        exclude_doc: str | None = None,
        exclude_folder: str | None = None,
    ) -> dict[str, NameClash]:  # pragma: no cover
        raise NotImplementedError

    def _p_taken_keys(self, pid: str, folder_id: str, *, exclude_doc: str | None = None) -> set[str]:  # pragma: no cover
        raise NotImplementedError

    def _p_live_docs_by_ids(self, pid: str, doc_ids: Sequence[str]) -> dict[str, DocumentRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_folders_by_ids(self, pid: str, folder_ids: Sequence[str]) -> dict[str, FolderRecord]:  # pragma: no cover
        raise NotImplementedError

    def _p_ready_revisions(self, pid: str, version: str, limit: int) -> list[DocumentRecord]:  # pragma: no cover
        raise NotImplementedError

    def _w_insert_folder(self, rec: FolderRecord) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_update_folder(self, folder_id: str, **fields: Any) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_delete_folder(self, pid: str, folder_id: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_insert_doc(self, rec: DocumentRecord) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_update_doc(self, doc_id: str, **fields: Any) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_delete_doc(self, pid: str, doc_id: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_set_image_doc_name(self, doc_id: str, name: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def _w_enqueue_purge(self, pid: str, kb_id: str, doc_id: str, reason: str) -> None:  # pragma: no cover
        raise NotImplementedError

    # ---- 通用小工具 ---- #

    def _require_folder(self, pid: str, folder_id: str) -> FolderRecord | None:
        """根（''）→ None；不存在或不属于本项目 → NotFoundError。"""
        if not folder_id:
            return None
        folder = self._p_folder(pid, folder_id)
        if folder is None:
            raise NotFoundError(_NOT_FOUND)
        return folder

    def _chain(self, pid: str, folder_id: str) -> tuple[FolderRecord, ...]:
        chain: list[FolderRecord] = []
        current = folder_id
        while current:
            folder = self._p_folder(pid, current)
            if folder is None or len(chain) >= _MAX_CHAIN:
                raise NotFoundError(_NOT_FOUND)
            chain.append(folder)
            current = folder.parent_id
        chain.reverse()
        return tuple(chain)

    # ---- 浏览 ---- #

    def list_children(self, scope: Scope, folder_id: str, *, page: int, page_size: int) -> ChildrenPage:
        pid = scope.project_id
        self._require_folder(pid, folder_id)
        size = max(1, int(page_size))
        offset = max(0, (max(1, int(page)) - 1) * size)
        items, total = self._p_page_children(pid, folder_id, offset, size)
        return ChildrenPage(items=tuple(items), total=total)

    def get_folder(self, scope: Scope, folder_id: str) -> FolderRecord | None:
        return self._p_folder(scope.project_id, folder_id) if folder_id else None

    def folder_chain(self, scope: Scope, folder_id: str) -> tuple[FolderRecord, ...]:
        return self._chain(scope.project_id, folder_id)

    def count_subtree(self, scope: Scope, folder_id: str) -> SubtreeCount:
        pid = scope.project_id
        self._require_folder(pid, folder_id)
        descendants = self._p_descendants(pid, folder_id)
        ids = [folder_id, *(d.folder_id for d in descendants)]
        files = sum(1 for _ in self._p_docs_in_folders(pid, ids, include_revisions=False))
        return SubtreeCount(folders=len(descendants), files=files)

    def list_subtree_folders(self, scope: Scope, folder_id: str) -> list[FolderRecord]:
        """folder_id 的全部后代目录（不含自身；按 depth 升序）。IFC-015 的增量扩展。"""
        pid = scope.project_id
        self._require_folder(pid, folder_id)
        return self._p_descendants(pid, folder_id)

    def list_subtree_documents(self, scope: Scope, folder_id: str, *, limit: int) -> list[DocumentRecord]:
        pid = scope.project_id
        start = self._require_folder(pid, folder_id)
        descendants = self._p_descendants(pid, folder_id)
        depth_of = {d.folder_id: d.depth for d in descendants}
        depth_of[folder_id] = start.depth if start is not None else 0
        docs = self._p_docs_in_folders(pid, list(depth_of), include_revisions=True)
        docs.sort(key=lambda d: (d.revision_of is None, -depth_of.get(d.folder_id, 0), d.doc_id))
        return docs[: max(0, int(limit))]

    # ---- 目录变更 ---- #

    def create_folder(self, scope: Scope, parent_id: str, name: str, *, max_depth: int) -> FolderRecord:
        pid = scope.project_id
        clean = validate_entry_name(name)
        key = name_key_of(clean)
        with self._txn():
            parent = self._require_folder(pid, parent_id)
            depth = (parent.depth if parent else 0) + 1
            if depth > max_depth:
                raise LibraryValidationError(
                    "目录层级已达上限", code="depth_exceeded", details={"limit": max_depth}
                )
            clashes = self._p_clashes(pid, parent_id, [key])
            if key in clashes:
                raise _clash_error([clashes[key]])
            now = utc_now_iso()
            rec = FolderRecord(uuid.uuid4().hex, pid, parent_id, clean, key, depth, now, now)
            self._w_insert_folder(rec)
            return rec

    def rename_folder(self, scope: Scope, folder_id: str, new_name: str) -> FolderRecord:
        pid = scope.project_id
        clean = validate_entry_name(new_name)
        key = name_key_of(clean)
        with self._txn():
            folder = self._p_folder(pid, folder_id) if folder_id else None
            if folder is None:
                raise NotFoundError(_NOT_FOUND)
            if key != folder.name_key:
                clashes = self._p_clashes(pid, folder.parent_id, [key], exclude_folder=folder_id)
                if key in clashes:
                    raise _clash_error([clashes[key]])
            now = utc_now_iso()
            self._w_update_folder(folder_id, name=clean, name_key=key, updated_at=now)
            return replace(folder, name=clean, name_key=key, updated_at=now)

    def rename_document(self, scope: Scope, doc_id: str, new_name: str) -> DocumentRecord:
        from ib.parsing import ext_of

        pid = scope.project_id
        clean = validate_entry_name(new_name)
        key = name_key_of(clean)
        with self._txn():
            doc = self._p_doc(pid, doc_id)
            if doc is None or doc.revision_of is not None:
                raise NotFoundError(_NOT_FOUND)
            if ext_of(clean) != (doc.ext or "").lower():
                raise LibraryValidationError(
                    "不允许修改文件扩展名", code="ext_change_not_allowed", details={"ext": doc.ext}
                )
            if key != doc.name_key:
                clashes = self._p_clashes(pid, doc.folder_id, [key], exclude_doc=doc_id)
                if key in clashes:
                    raise _clash_error([clashes[key]])
            now = utc_now_iso()
            self._w_update_doc(doc_id, doc_name=clean, name_key=key, updated_at=now)
            self._w_set_image_doc_name(doc_id, clean)
            return replace(doc, doc_name=clean, name_key=key, updated_at=now)

    def delete_empty_folders(self, scope: Scope, folder_ids: Sequence[str]) -> int:
        pid = scope.project_id
        deleted = 0
        with self._txn():
            found = [f for f in (self._p_folder(pid, fid) for fid in dict.fromkeys(folder_ids) if fid) if f]
            for folder in sorted(found, key=lambda f: -f.depth):  # 自底向上
                if self._p_child_folders(pid, folder.folder_id):
                    continue
                if self._p_docs_in_folders(pid, [folder.folder_id], include_revisions=True):
                    continue
                self._w_delete_folder(pid, folder.folder_id)
                deleted += 1
        return deleted

    # ---- 移动 ---- #

    def move_entries(
        self,
        scope: Scope,
        entries: Sequence[EntryRef],
        target_folder_id: str,
        resolutions: Mapping[str, ConflictAction],
        *,
        max_depth: int,
    ) -> MoveOutcome:
        pid = scope.project_id
        refs = list(dict.fromkeys(entries))
        moved: list[EntryRef] = []
        skipped: list[EntryRef] = []
        renamed: list[tuple[EntryRef, str]] = []
        overwritten: list[str] = []
        if not refs:
            return MoveOutcome((), (), (), ())
        with self._txn():
            target = self._require_folder(pid, target_folder_id)
            base_depth = target.depth if target else 0
            target_chain = {f.folder_id for f in self._chain(pid, target_folder_id)}

            # ---- 1) 读取与校验（只读，任何失败都不改台账）----
            loaded: list[tuple[EntryRef, FolderRecord | None, DocumentRecord | None, str, str]] = []
            for ref in refs:
                if ref.kind == "folder":
                    folder = self._p_folder(pid, ref.entry_id) if ref.entry_id else None
                    if folder is None:
                        raise NotFoundError(_NOT_FOUND)
                    if folder.folder_id in target_chain:
                        raise LibraryValidationError("不能移动到自身或其子目录", code="move_into_self")
                    sub = self._p_descendants(pid, folder.folder_id)
                    deepest = max([folder.depth, *(d.depth for d in sub)])
                    if base_depth + 1 + (deepest - folder.depth) > max_depth:
                        raise LibraryValidationError(
                            "目录层级已达上限", code="depth_exceeded", details={"limit": max_depth}
                        )
                    loaded.append((ref, folder, None, folder.name, folder.name_key))
                else:
                    doc = self._p_doc(pid, ref.entry_id)
                    if doc is None or doc.revision_of is not None:
                        raise NotFoundError(_NOT_FOUND)
                    loaded.append((ref, None, doc, doc.doc_name, doc.name_key or name_key_of(doc.doc_name)))

            existing = self._p_clashes(pid, target_folder_id, [item[4] for item in loaded])
            planned: dict[str, NameClash] = {}
            plan: list[tuple[Any, str, NameClash | None]] = []
            unresolved: list[tuple[NameClash, NameClash]] = []
            for item in loaded:
                ref, folder, doc, name, key = item
                parent = folder.parent_id if folder else (doc.folder_id if doc else "")
                if parent == target_folder_id:
                    plan.append((item, "noop", None))
                    continue
                clash = existing.get(key)
                intra = False
                if clash is None and key in planned:
                    clash, intra = planned[key], True
                if clash is None:
                    plan.append((item, "move", None))
                    planned[key] = NameClash(ref.kind, ref.entry_id, name)
                    continue
                action = resolutions.get(ref.entry_id)
                if action is None:
                    unresolved.append((NameClash(ref.kind, ref.entry_id, name), clash))
                    continue
                if action not in ("overwrite", "skip", "rename"):
                    raise LibraryValidationError("不支持的冲突处理方式", code="bad_request")
                if action == "overwrite" and (intra or clash.kind != ref.kind):
                    raise LibraryValidationError("文件与文件夹之间不能互相覆盖", code="bad_request")
                plan.append((item, action, clash))
            if unresolved:
                raise LibraryConflictError(
                    "目标目录存在同名条目，需先选择处理方式",
                    clashes=tuple(c for _, c in unresolved),
                    initiators=tuple(r for r, _ in unresolved),
                )

            # ---- 2) 应用（同一写事务）----
            taken: set[str] | None = None
            now = utc_now_iso()
            for item, action, clash in plan:
                ref, folder, doc, name, key = item
                if action == "noop" or action == "skip":
                    skipped.append(ref)
                    continue
                new_name = name
                if action == "rename":
                    if taken is None:
                        taken = self._p_taken_keys(pid, target_folder_id) | set(planned)
                    new_name = next_free_name(name, taken, is_file=ref.kind == "file")
                    taken.add(name_key_of(new_name))
                    renamed.append((ref, new_name))
                elif action == "overwrite" and clash is not None:
                    if ref.kind == "file":
                        overwritten.extend(self._remove_live_doc(pid, clash.entry_id, "overwritten"))
                    else:
                        self._merge_folder(pid, ref.entry_id, clash.entry_id, overwritten, now)
                        moved.append(ref)
                        continue
                if folder is not None:
                    self._move_folder(pid, folder, target_folder_id, base_depth + 1, new_name, now)
                elif doc is not None:
                    self._move_doc(doc, target_folder_id, new_name, now)
                moved.append(ref)
        return MoveOutcome(tuple(moved), tuple(skipped), tuple(renamed), tuple(overwritten))

    def _move_doc(self, doc: DocumentRecord, target_folder_id: str, new_name: str, now: str) -> None:
        fields: dict[str, Any] = {"folder_id": target_folder_id, "updated_at": now}
        if new_name != doc.doc_name:
            fields.update(doc_name=new_name, name_key=name_key_of(new_name))
            self._w_set_image_doc_name(doc.doc_id, new_name)
        self._w_update_doc(doc.doc_id, **fields)
        revision = self._p_revision_of(doc.project_id, doc.doc_id)
        if revision is not None:  # 修订行跟随存活行的目录
            self._w_update_doc(revision.doc_id, folder_id=target_folder_id)

    def _move_folder(
        self, pid: str, folder: FolderRecord, target_id: str, new_depth: int, new_name: str, now: str
    ) -> None:
        fields: dict[str, Any] = {"parent_id": target_id, "depth": new_depth, "updated_at": now}
        if new_name != folder.name:
            fields.update(name=new_name, name_key=name_key_of(new_name))
        delta = new_depth - folder.depth
        descendants = self._p_descendants(pid, folder.folder_id)
        self._w_update_folder(folder.folder_id, **fields)
        if delta:
            for d in descendants:
                self._w_update_folder(d.folder_id, depth=d.depth + delta)

    def _remove_live_doc(self, pid: str, doc_id: str, reason: str) -> list[str]:
        """把存活文档（及其修订行）移出台账并入清理队列；返回被移出的 doc_id 列表。"""
        removed: list[str] = []
        revision = self._p_revision_of(pid, doc_id)
        for row in ([revision] if revision is not None else []) + [self._p_doc(pid, doc_id)]:
            if row is None:
                continue
            self._w_delete_doc(pid, row.doc_id)
            self._w_enqueue_purge(pid, row.kb_id, row.doc_id, reason)
            removed.append(row.doc_id)
        return removed

    def _merge_folder(self, pid: str, src_id: str, dst_id: str, overwritten: list[str], now: str) -> None:
        """文件夹“覆盖”= 合并：src 的内容并入 dst；同名文件按覆盖处理，同名文件夹递归合并，跨类同名自动改名。"""
        taken = self._p_taken_keys(pid, dst_id)
        dst = self._p_folder(pid, dst_id)
        dst_depth = dst.depth if dst else 0
        for child in self._p_child_folders(pid, src_id):
            clash = self._p_clashes(pid, dst_id, [child.name_key]).get(child.name_key)
            if clash is None:
                self._move_folder(pid, child, dst_id, dst_depth + 1, child.name, now)
                taken.add(child.name_key)
            elif clash.kind == "folder":
                self._merge_folder(pid, child.folder_id, clash.entry_id, overwritten, now)
            else:
                new_name = next_free_name(child.name, taken, is_file=False)
                taken.add(name_key_of(new_name))
                self._move_folder(pid, child, dst_id, dst_depth + 1, new_name, now)
        for doc in self._p_live_docs(pid, src_id):
            clash = self._p_clashes(pid, dst_id, [doc.name_key]).get(doc.name_key)
            if clash is None:
                self._move_doc(doc, dst_id, doc.doc_name, now)
                taken.add(doc.name_key)
            elif clash.kind == "file":
                overwritten.extend(self._remove_live_doc(pid, clash.entry_id, "overwritten"))
                self._move_doc(doc, dst_id, doc.doc_name, now)
            else:
                new_name = next_free_name(doc.doc_name, taken, is_file=True)
                taken.add(name_key_of(new_name))
                self._move_doc(doc, dst_id, new_name, now)
        self._w_delete_folder(pid, src_id)

    # ---- 文档落库 ---- #

    def find_name_clashes(self, scope: Scope, folder_id: str, names: Sequence[str]) -> dict[str, NameClash]:
        pid = scope.project_id
        self._require_folder(pid, folder_id)
        return self._p_clashes(pid, folder_id, [name_key_of(n) for n in names])

    def create_document_in(
        self,
        scope: Scope,
        *,
        folder_id: str,
        rel_dirs: Sequence[str],
        name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        on_conflict: Literal["fail", "rename"],
        max_depth: int,
    ) -> CreatedDocument:
        pid = scope.project_id
        kb_id = scope.kb_ids[0] if scope.kb_ids else ""
        segments = [validate_entry_name(seg) for seg in rel_dirs]
        clean = validate_entry_name(name)
        key = name_key_of(clean)
        created: list[FolderRecord] = []
        with self._txn():
            start = self._require_folder(pid, folder_id)
            # ---- 先规划（只读）：沿既有目录走到第一个缺失处，其后全部需新建 ----
            current_id = folder_id
            current_depth = start.depth if start else 0
            index = 0
            while index < len(segments):
                seg_key = name_key_of(segments[index])
                clash = self._p_clashes(pid, current_id, [seg_key]).get(seg_key)
                if clash is None:
                    break
                if clash.kind != "folder":
                    raise _clash_error([clash])
                current_id = clash.entry_id
                current_depth += 1
                index += 1
            missing = segments[index:]
            if current_depth + len(missing) > max_depth:
                raise LibraryValidationError(
                    "目录层级已达上限", code="depth_exceeded", details={"limit": max_depth}
                )
            final_name = clean
            if not missing:
                clashes = self._p_clashes(pid, current_id, [key])
                if key in clashes:
                    if on_conflict == "fail":
                        raise _clash_error([clashes[key]])
                    final_name = next_free_name(clean, self._p_taken_keys(pid, current_id), is_file=True)
            # ---- 再应用 ----
            now = utc_now_iso()
            for seg in missing:
                rec = FolderRecord(
                    uuid.uuid4().hex, pid, current_id, seg, name_key_of(seg), current_depth + 1, now, now
                )
                self._w_insert_folder(rec)
                created.append(rec)
                current_id, current_depth = rec.folder_id, rec.depth
            doc = DocumentRecord(
                doc_id=uuid.uuid4().hex,
                project_id=pid,
                kb_id=kb_id,
                doc_name=final_name,
                ext=ext,
                size_bytes=int(size_bytes),
                content_sha256=content_sha256,
                blob_ref=None,
                status="pending",
                error_code=None,
                chunk_count=0,
                indexed_collection_version=None,
                target_collection_version=None,
                lease_owner=None,
                lease_expires_at=None,
                created_at=now,
                updated_at=now,
                folder_id=current_id,
                name_key=name_key_of(final_name),
                uploaded_at=now,
            )
            self._w_insert_doc(doc)
        return CreatedDocument(record=doc, created_folders=tuple(created))

    # ---- 修订 ---- #

    def get_revision_of(self, scope: Scope, live_doc_id: str) -> DocumentRecord | None:
        return self._p_revision_of(scope.project_id, live_doc_id)

    def create_revision(
        self,
        scope: Scope,
        live_doc_id: str,
        *,
        new_name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        on_conflict: Literal["fail", "rename"],
    ) -> tuple[DocumentRecord, tuple[DocumentRecord, ...]]:
        pid = scope.project_id
        clean = validate_entry_name(new_name)
        key = name_key_of(clean)
        with self._txn():
            live = self._p_doc(pid, live_doc_id)
            if live is None or live.revision_of is not None:
                raise NotFoundError(_NOT_FOUND)
            if live.status not in ("indexed", "failed"):
                raise LibraryConflictError("文件正在处理，暂不能更新", code="doc_busy")
            old = self._p_revision_of(pid, live_doc_id)
            if old is not None and old.status == "parsing":
                raise LibraryConflictError("该文件正在更新中", code="update_in_progress")
            final_name = clean
            clashes = self._p_clashes(pid, live.folder_id, [key], exclude_doc=live_doc_id)
            if key in clashes:
                if on_conflict == "fail":
                    raise _clash_error([clashes[key]])
                taken = self._p_taken_keys(pid, live.folder_id, exclude_doc=live_doc_id)
                final_name = next_free_name(clean, taken, is_file=True)
            replaced: tuple[DocumentRecord, ...] = ()
            if old is not None:
                self._w_delete_doc(pid, old.doc_id)
                replaced = (old,)
            now = utc_now_iso()
            revision = DocumentRecord(
                doc_id=uuid.uuid4().hex,
                project_id=pid,
                kb_id=live.kb_id,
                doc_name=final_name,
                ext=ext,
                size_bytes=int(size_bytes),
                content_sha256=content_sha256,
                blob_ref=None,
                status="pending",
                error_code=None,
                chunk_count=0,
                indexed_collection_version=None,
                target_collection_version=None,
                lease_owner=None,
                lease_expires_at=None,
                created_at=now,
                updated_at=now,
                folder_id=live.folder_id,
                name_key="",
                uploaded_at=live.uploaded_at,
                revision_of=live_doc_id,
            )
            self._w_insert_doc(revision)
        return revision, replaced

    def _promote_in_txn(
        self, pid: str, rev: DocumentRecord, live: DocumentRecord, now: str
    ) -> PromoteOutcome:
        """晋升事务体：删旧存活行 → 修订行成为存活行 → 旧 doc_id 入清理队列。"""
        self._w_delete_doc(pid, live.doc_id)
        self._w_enqueue_purge(pid, live.kb_id, live.doc_id, "replaced")
        name = rev.doc_name
        renamed_to: str | None = None
        if name_key_of(name) in self._p_clashes(pid, live.folder_id, [name_key_of(name)]):
            name = next_free_name(name, self._p_taken_keys(pid, live.folder_id), is_file=True)
            renamed_to = name
        self._w_update_doc(
            rev.doc_id,
            revision_of=None,
            doc_name=name,
            name_key=name_key_of(name),
            folder_id=live.folder_id,
            uploaded_at=live.uploaded_at,
            created_at=live.created_at,
            content_updated_at=now,
        )
        self._w_set_image_doc_name(rev.doc_id, name)
        record = self._p_doc(pid, rev.doc_id)
        if record is None:  # pragma: no cover - 刚写入
            raise DependencyUnavailableError("晋升后读取台账失败", dependency="ledger")
        return PromoteOutcome("promoted", record, live.doc_id, renamed_to)

    def promote_revision(
        self,
        scope: Scope,
        revision_doc_id: str,
        *,
        collection_version: str,
        chunk_count: int,
        active_version: str,
    ) -> PromoteOutcome:
        pid = scope.project_id
        with self._txn():
            rev = self._p_doc(pid, revision_doc_id)
            if rev is None or rev.revision_of is None:
                raise NotFoundError(_NOT_FOUND)
            _assert_transition(rev.status, "indexed", doc_id=revision_doc_id)
            now = utc_now_iso()
            self._w_update_doc(
                revision_doc_id,
                status="indexed",
                error_code=None,
                chunk_count=int(chunk_count),
                indexed_collection_version=collection_version,
                target_collection_version=None,
                lease_owner=None,
                lease_expires_at=None,
                updated_at=now,
                indexed_at=now,
            )
            rev = replace(
                rev,
                status="indexed",
                error_code=None,
                chunk_count=int(chunk_count),
                indexed_collection_version=collection_version,
                indexed_at=now,
                updated_at=now,
            )
            if collection_version != active_version:
                return PromoteOutcome("ready", rev, None, None)
            live = self._p_doc(pid, rev.revision_of or "")
            if live is None or live.revision_of is not None:
                raise NotFoundError("被更新的文件已不存在")
            return self._promote_in_txn(pid, rev, live, now)

    def list_ready_revisions(self, project_id: str, *, active_version: str, limit: int) -> list[DocumentRecord]:
        return self._p_ready_revisions(project_id, active_version, max(0, int(limit)))

    def promote_ready(self, scope: Scope, revision_doc_id: str, *, active_version: str) -> PromoteOutcome | None:
        pid = scope.project_id
        with self._txn():
            rev = self._p_doc(pid, revision_doc_id)
            if (
                rev is None
                or rev.revision_of is None
                or rev.status != "indexed"
                or rev.indexed_collection_version != active_version
            ):
                return None
            live = self._p_doc(pid, rev.revision_of)
            if live is None or live.revision_of is not None:
                # 孤儿修订行（存活行已被删）：移出台账并入清理队列，不再晋升
                self._w_delete_doc(pid, rev.doc_id)
                self._w_enqueue_purge(pid, rev.kb_id, rev.doc_id, "orphan_revision")
                return None
            return self._promote_in_txn(pid, rev, live, utc_now_iso())

    # ---- 存活解析 ---- #

    def resolve_live(self, project_id: str, doc_ids: Sequence[str]) -> dict[str, EntryLocation]:
        unique = list(dict.fromkeys(d for d in doc_ids if d))
        if not unique:
            return {}
        docs = self._p_live_docs_by_ids(project_id, unique)
        cache: dict[str, FolderRecord] = {}
        pending = {d.folder_id for d in docs.values() if d.folder_id}
        guard = 0
        while pending and guard < _MAX_CHAIN:
            guard += 1
            fetched = self._p_folders_by_ids(project_id, sorted(pending))
            cache.update(fetched)
            pending = {f.parent_id for f in fetched.values() if f.parent_id and f.parent_id not in cache}
        out: dict[str, EntryLocation] = {}
        for doc in docs.values():
            names: list[str] = []
            current, ok = doc.folder_id, True
            hops = 0
            while current:
                folder = cache.get(current)
                hops += 1
                if folder is None or hops > _MAX_CHAIN:
                    ok = False
                    break
                names.append(folder.name)
                current = folder.parent_id
            if not ok:
                continue  # 目录链损坏（不应发生）：视为不可解析，宁缺勿错
            names.reverse()
            out[doc.doc_id] = EntryLocation(doc.doc_id, doc.doc_name, doc.folder_id, tuple(names))
        return out

    # ---- 清理队列 ---- #

    def enqueue_purge(self, project_id: str, kb_id: str, doc_id: str, reason: str) -> None:
        with self._txn():
            self._w_enqueue_purge(project_id, kb_id, doc_id, reason)


# --------------------------------------------------------------------------- #
# SQLite 后端
# --------------------------------------------------------------------------- #

_FOLDER_COLS = "folder_id, project_id, parent_id, name, name_key, depth, created_at, updated_at"
_IN_BATCH = 400


def _folder_of(row: Sequence[Any]) -> FolderRecord:
    return FolderRecord(row[0], row[1], row[2], row[3], row[4], int(row[5]), row[6], row[7])


class SqliteEntryTree(_TreeLogic):
    """SQLite 实现：复用 `SqliteLedgerRepository` 的线程局部连接与 `BEGIN IMMEDIATE` 写事务。"""

    def __init__(self, ledger: Any) -> None:
        self._ledger = ledger
        from ib.ledger.sqlite_repo import _DOC_COLUMNS, _row_to_document, find_name_clashes_sql

        self._doc_cols = ",".join(_DOC_COLUMNS)
        self._doc_cols_d = ",".join(f"d.{c}" for c in _DOC_COLUMNS)
        self._allowed_cols = frozenset(_DOC_COLUMNS)
        self._row_to_doc = _row_to_document
        self._clash_sql = find_name_clashes_sql

    # -- 事务与连接 -- #

    @contextmanager
    def _txn(self) -> Iterator[None]:
        try:
            with self._ledger._write():
                yield
        except sqlite3.IntegrityError as exc:
            raise LibraryConflictError("同目录下已存在同名条目（并发冲突）") from exc

    def _c(self) -> sqlite3.Connection:
        return self._ledger._conn()

    # -- 读原语 -- #

    def _p_folder(self, pid: str, folder_id: str) -> FolderRecord | None:
        row = self._c().execute(
            f"SELECT {_FOLDER_COLS} FROM folders WHERE project_id = ? AND folder_id = ?", (pid, folder_id)
        ).fetchone()
        return _folder_of(row) if row else None

    def _p_child_folders(self, pid: str, parent_id: str) -> list[FolderRecord]:
        rows = self._c().execute(
            f"SELECT {_FOLDER_COLS} FROM folders WHERE project_id = ? AND parent_id = ?"
            " ORDER BY name_key, folder_id",
            (pid, parent_id),
        ).fetchall()
        return [_folder_of(r) for r in rows]

    def _p_live_docs(self, pid: str, folder_id: str) -> list[DocumentRecord]:
        rows = self._c().execute(
            f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND folder_id = ?"
            " AND revision_of IS NULL ORDER BY name_key, doc_id",
            (pid, folder_id),
        ).fetchall()
        return [self._row_to_doc(r) for r in rows]

    def _p_page_children(
        self, pid: str, folder_id: str, offset: int, limit: int
    ) -> tuple[list[FolderRecord | DocumentRecord], int]:
        conn = self._c()
        n_folders = int(
            conn.execute(
                "SELECT COUNT(*) FROM folders WHERE project_id = ? AND parent_id = ?", (pid, folder_id)
            ).fetchone()[0]
        )
        n_docs = int(
            conn.execute(
                "SELECT COUNT(*) FROM documents WHERE project_id = ? AND folder_id = ? AND revision_of IS NULL",
                (pid, folder_id),
            ).fetchone()[0]
        )
        items: list[FolderRecord | DocumentRecord] = []
        if offset < n_folders:
            rows = conn.execute(
                f"SELECT {_FOLDER_COLS} FROM folders WHERE project_id = ? AND parent_id = ?"
                " ORDER BY name_key, folder_id LIMIT ? OFFSET ?",
                (pid, folder_id, limit, offset),
            ).fetchall()
            items.extend(_folder_of(r) for r in rows)
        room = limit - len(items)
        if room > 0:
            rows = conn.execute(
                f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND folder_id = ?"
                " AND revision_of IS NULL ORDER BY name_key, doc_id LIMIT ? OFFSET ?",
                (pid, folder_id, room, max(0, offset - n_folders)),
            ).fetchall()
            items.extend(self._row_to_doc(r) for r in rows)
        return items, n_folders + n_docs

    def _p_doc(self, pid: str, doc_id: str) -> DocumentRecord | None:
        row = self._c().execute(
            f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND doc_id = ?", (pid, doc_id)
        ).fetchone()
        return self._row_to_doc(row) if row else None

    def _p_revision_of(self, pid: str, live_id: str) -> DocumentRecord | None:
        row = self._c().execute(
            f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND revision_of = ?", (pid, live_id)
        ).fetchone()
        return self._row_to_doc(row) if row else None

    def _p_descendants(self, pid: str, folder_id: str) -> list[FolderRecord]:
        rows = self._c().execute(
            "WITH RECURSIVE sub(folder_id) AS ("
            " SELECT folder_id FROM folders WHERE project_id = ? AND parent_id = ?"
            " UNION ALL SELECT f.folder_id FROM folders f JOIN sub s ON f.parent_id = s.folder_id"
            " WHERE f.project_id = ?)"
            f" SELECT {_FOLDER_COLS} FROM folders WHERE folder_id IN (SELECT folder_id FROM sub)"
            " ORDER BY depth, folder_id",
            (pid, folder_id, pid),
        ).fetchall()
        return [_folder_of(r) for r in rows]

    def _p_docs_in_folders(
        self, pid: str, folder_ids: Sequence[str], *, include_revisions: bool
    ) -> list[DocumentRecord]:
        out: list[DocumentRecord] = []
        ids = list(folder_ids)
        for start in range(0, len(ids), _IN_BATCH):
            batch = ids[start : start + _IN_BATCH]
            marks = ",".join("?" for _ in batch)
            extra = "" if include_revisions else " AND revision_of IS NULL"
            rows = self._c().execute(
                f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND folder_id IN ({marks}){extra}",
                [pid, *batch],
            ).fetchall()
            out.extend(self._row_to_doc(r) for r in rows)
        return out

    def _p_clashes(
        self,
        pid: str,
        folder_id: str,
        keys: Sequence[str],
        *,
        exclude_doc: str | None = None,
        exclude_folder: str | None = None,
    ) -> dict[str, NameClash]:
        return self._clash_sql(
            self._c(), pid, folder_id, keys, exclude_doc_id=exclude_doc, exclude_folder_id=exclude_folder
        )

    def _p_taken_keys(self, pid: str, folder_id: str, *, exclude_doc: str | None = None) -> set[str]:
        conn = self._c()
        keys = {
            r[0]
            for r in conn.execute(
                "SELECT name_key FROM folders WHERE project_id = ? AND parent_id = ?", (pid, folder_id)
            ).fetchall()
        }
        for r in conn.execute(
            "SELECT doc_id, name_key FROM documents WHERE project_id = ? AND folder_id = ?"
            " AND revision_of IS NULL AND name_key <> ''",
            (pid, folder_id),
        ).fetchall():
            if r[0] != exclude_doc:
                keys.add(r[1])
        return keys

    def _p_live_docs_by_ids(self, pid: str, doc_ids: Sequence[str]) -> dict[str, DocumentRecord]:
        out: dict[str, DocumentRecord] = {}
        ids = list(doc_ids)
        for start in range(0, len(ids), _IN_BATCH):
            batch = ids[start : start + _IN_BATCH]
            marks = ",".join("?" for _ in batch)
            rows = self._c().execute(
                f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND revision_of IS NULL"
                f" AND doc_id IN ({marks})",
                [pid, *batch],
            ).fetchall()
            for r in rows:
                rec = self._row_to_doc(r)
                out[rec.doc_id] = rec
        return out

    def _p_folders_by_ids(self, pid: str, folder_ids: Sequence[str]) -> dict[str, FolderRecord]:
        out: dict[str, FolderRecord] = {}
        ids = list(folder_ids)
        for start in range(0, len(ids), _IN_BATCH):
            batch = ids[start : start + _IN_BATCH]
            marks = ",".join("?" for _ in batch)
            rows = self._c().execute(
                f"SELECT {_FOLDER_COLS} FROM folders WHERE project_id = ? AND folder_id IN ({marks})",
                [pid, *batch],
            ).fetchall()
            for r in rows:
                rec = _folder_of(r)
                out[rec.folder_id] = rec
        return out

    def _p_ready_revisions(self, pid: str, version: str, limit: int) -> list[DocumentRecord]:
        rows = self._c().execute(
            f"SELECT {self._doc_cols} FROM documents WHERE project_id = ? AND status = 'indexed'"
            " AND revision_of IS NOT NULL AND indexed_collection_version = ?"
            " ORDER BY indexed_at, doc_id LIMIT ?",
            (pid, version, limit),
        ).fetchall()
        return [self._row_to_doc(r) for r in rows]

    # -- 写原语 -- #

    def _w_insert_folder(self, rec: FolderRecord) -> None:
        self._c().execute(
            f"INSERT INTO folders ({_FOLDER_COLS}) VALUES (?,?,?,?,?,?,?,?)",
            (rec.folder_id, rec.project_id, rec.parent_id, rec.name, rec.name_key, rec.depth,
             rec.created_at, rec.updated_at),
        )

    def _w_update_folder(self, folder_id: str, **fields: Any) -> None:
        allowed = {"parent_id", "name", "name_key", "depth", "updated_at"}
        assert set(fields) <= allowed
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._c().execute(f"UPDATE folders SET {sets} WHERE folder_id = ?", [*fields.values(), folder_id])

    def _w_delete_folder(self, pid: str, folder_id: str) -> None:
        self._c().execute("DELETE FROM folders WHERE project_id = ? AND folder_id = ?", (pid, folder_id))

    def _w_insert_doc(self, rec: DocumentRecord) -> None:
        cols = self._doc_cols.split(",")
        self._c().execute(
            f"INSERT INTO documents ({self._doc_cols}) VALUES ({','.join('?' for _ in cols)})",
            [getattr(rec, c) for c in cols],
        )

    def _w_update_doc(self, doc_id: str, **fields: Any) -> None:
        assert set(fields) <= self._allowed_cols
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._c().execute(f"UPDATE documents SET {sets} WHERE doc_id = ?", [*fields.values(), doc_id])

    def _w_delete_doc(self, pid: str, doc_id: str) -> None:
        conn = self._c()
        # 显式清子表（不依赖外键级联是否开启），再删文档行。
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM chunk_image WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE project_id = ? AND doc_id = ?", (pid, doc_id))

    def _w_set_image_doc_name(self, doc_id: str, name: str) -> None:
        self._c().execute("UPDATE chunk_image SET doc_name = ? WHERE doc_id = ?", (name, doc_id))

    def _w_enqueue_purge(self, pid: str, kb_id: str, doc_id: str, reason: str) -> None:
        self._c().execute(
            "INSERT INTO doc_purge_queue (doc_id, project_id, kb_id, reason, attempts, created_at)"
            " VALUES (?,?,?,?,0,?) ON CONFLICT(doc_id) DO NOTHING",
            (doc_id, pid, kb_id, reason, utc_now_iso()),
        )

    # -- 清理队列 -- #

    def list_purge(self, limit: int) -> list[PurgeItem]:
        rows = self._c().execute(
            "SELECT doc_id, project_id, kb_id, reason, attempts FROM doc_purge_queue"
            " ORDER BY attempts, created_at, doc_id LIMIT ?",
            (max(0, int(limit)),),
        ).fetchall()
        return [PurgeItem(r[0], r[1], r[2], r[3], int(r[4])) for r in rows]

    def ack_purge(self, doc_id: str) -> None:
        with self._txn():
            self._c().execute("DELETE FROM doc_purge_queue WHERE doc_id = ?", (doc_id,))

    def bump_purge(self, doc_id: str) -> None:
        with self._txn():
            self._c().execute("UPDATE doc_purge_queue SET attempts = attempts + 1 WHERE doc_id = ?", (doc_id,))


# --------------------------------------------------------------------------- #
# 内存后端（离线替身）
# --------------------------------------------------------------------------- #


class MemoryEntryTree(_TreeLogic):
    """内存实现：存储与锁取自 `InMemoryLedgerRepository`；事务 = RLock + 异常时整体回滚快照。"""

    def __init__(self, ledger: Any) -> None:
        self._ledger = ledger

    @contextmanager
    def _txn(self) -> Iterator[None]:
        ledger = self._ledger
        with ledger._lock:
            snapshot = (
                dict(ledger._documents),
                dict(ledger._folders),
                dict(ledger._purge),
                dict(ledger._chunks),
                dict(ledger._chunk_images),
            )
            try:
                yield
            except BaseException:
                (ledger._documents, ledger._folders, ledger._purge, ledger._chunks,
                 ledger._chunk_images) = snapshot
                raise

    # -- 读原语 -- #

    def _p_folder(self, pid: str, folder_id: str) -> FolderRecord | None:
        f = self._ledger._folders.get(folder_id)
        return f if f is not None and f.project_id == pid else None

    def _p_child_folders(self, pid: str, parent_id: str) -> list[FolderRecord]:
        rows = [f for f in self._ledger._folders.values() if f.project_id == pid and f.parent_id == parent_id]
        return sorted(rows, key=lambda f: (f.name_key, f.folder_id))

    def _p_live_docs(self, pid: str, folder_id: str) -> list[DocumentRecord]:
        rows = [
            d for d in self._ledger._documents.values()
            if d.project_id == pid and d.folder_id == folder_id and d.revision_of is None
        ]
        return sorted(rows, key=lambda d: (d.name_key, d.doc_id))

    def _p_page_children(
        self, pid: str, folder_id: str, offset: int, limit: int
    ) -> tuple[list[FolderRecord | DocumentRecord], int]:
        with self._ledger._lock:
            combined: list[FolderRecord | DocumentRecord] = [
                *self._p_child_folders(pid, folder_id),
                *self._p_live_docs(pid, folder_id),
            ]
        return combined[offset : offset + limit], len(combined)

    def _p_doc(self, pid: str, doc_id: str) -> DocumentRecord | None:
        d = self._ledger._documents.get(doc_id)
        return d if d is not None and d.project_id == pid else None

    def _p_revision_of(self, pid: str, live_id: str) -> DocumentRecord | None:
        for d in self._ledger._documents.values():
            if d.project_id == pid and d.revision_of == live_id:
                return d
        return None

    def _p_descendants(self, pid: str, folder_id: str) -> list[FolderRecord]:
        out: list[FolderRecord] = []
        frontier = [folder_id]
        while frontier and len(out) < 1_000_000:
            nxt: list[str] = []
            for parent in frontier:
                for f in self._p_child_folders(pid, parent):
                    out.append(f)
                    nxt.append(f.folder_id)
            frontier = nxt
        return sorted(out, key=lambda f: (f.depth, f.folder_id))

    def _p_docs_in_folders(
        self, pid: str, folder_ids: Sequence[str], *, include_revisions: bool
    ) -> list[DocumentRecord]:
        wanted = set(folder_ids)
        return [
            d for d in self._ledger._documents.values()
            if d.project_id == pid and d.folder_id in wanted and (include_revisions or d.revision_of is None)
        ]

    def _p_clashes(
        self,
        pid: str,
        folder_id: str,
        keys: Sequence[str],
        *,
        exclude_doc: str | None = None,
        exclude_folder: str | None = None,
    ) -> dict[str, NameClash]:
        wanted = {k for k in keys if k}
        found: dict[str, NameClash] = {}
        for f in self._ledger._folders.values():
            if (f.project_id == pid and f.parent_id == folder_id and f.name_key in wanted
                    and f.folder_id != exclude_folder):
                found[f.name_key] = NameClash("folder", f.folder_id, f.name)
        for d in self._ledger._documents.values():
            if (d.project_id == pid and d.folder_id == folder_id and d.revision_of is None
                    and d.name_key in wanted and d.doc_id != exclude_doc):
                found.setdefault(d.name_key, NameClash("file", d.doc_id, d.doc_name))
        return found

    def _p_taken_keys(self, pid: str, folder_id: str, *, exclude_doc: str | None = None) -> set[str]:
        keys = {f.name_key for f in self._ledger._folders.values()
                if f.project_id == pid and f.parent_id == folder_id}
        keys |= {
            d.name_key for d in self._ledger._documents.values()
            if d.project_id == pid and d.folder_id == folder_id and d.revision_of is None
            and d.name_key and d.doc_id != exclude_doc
        }
        return keys

    def _p_live_docs_by_ids(self, pid: str, doc_ids: Sequence[str]) -> dict[str, DocumentRecord]:
        out: dict[str, DocumentRecord] = {}
        for doc_id in doc_ids:
            d = self._ledger._documents.get(doc_id)
            if d is not None and d.project_id == pid and d.revision_of is None:
                out[doc_id] = d
        return out

    def _p_folders_by_ids(self, pid: str, folder_ids: Sequence[str]) -> dict[str, FolderRecord]:
        return {
            fid: f for fid in folder_ids
            if (f := self._ledger._folders.get(fid)) is not None and f.project_id == pid
        }

    def _p_ready_revisions(self, pid: str, version: str, limit: int) -> list[DocumentRecord]:
        rows = [
            d for d in self._ledger._documents.values()
            if d.project_id == pid and d.status == "indexed" and d.revision_of is not None
            and d.indexed_collection_version == version
        ]
        rows.sort(key=lambda d: (d.indexed_at or "", d.doc_id))
        return rows[:limit]

    # -- 写原语 -- #

    def _w_insert_folder(self, rec: FolderRecord) -> None:
        for f in self._ledger._folders.values():  # 对齐 SQLite 唯一索引（第二道保险）
            if f.project_id == rec.project_id and f.parent_id == rec.parent_id and f.name_key == rec.name_key:
                raise LibraryConflictError("同目录下已存在同名条目（并发冲突）")
        self._ledger._folders[rec.folder_id] = rec

    def _w_update_folder(self, folder_id: str, **fields: Any) -> None:
        self._ledger._folders[folder_id] = replace(self._ledger._folders[folder_id], **fields)

    def _w_delete_folder(self, pid: str, folder_id: str) -> None:
        f = self._ledger._folders.get(folder_id)
        if f is not None and f.project_id == pid:
            del self._ledger._folders[folder_id]

    def _w_insert_doc(self, rec: DocumentRecord) -> None:
        self._ledger._documents[rec.doc_id] = rec

    def _w_update_doc(self, doc_id: str, **fields: Any) -> None:
        self._ledger._documents[doc_id] = replace(self._ledger._documents[doc_id], **fields)

    def _w_delete_doc(self, pid: str, doc_id: str) -> None:
        d = self._ledger._documents.get(doc_id)
        if d is not None and d.project_id == pid:
            del self._ledger._documents[doc_id]
            self._ledger._chunks.pop(doc_id, None)
            self._ledger._chunk_images.pop(doc_id, None)

    def _w_set_image_doc_name(self, doc_id: str, name: str) -> None:
        rows = self._ledger._chunk_images.get(doc_id)
        if rows:
            self._ledger._chunk_images[doc_id] = [replace(r, doc_name=name) for r in rows]

    def _w_enqueue_purge(self, pid: str, kb_id: str, doc_id: str, reason: str) -> None:
        self._ledger._purge.setdefault(
            doc_id,
            {"project_id": pid, "kb_id": kb_id, "reason": reason, "attempts": 0, "created_at": utc_now_iso()},
        )

    # -- 清理队列 -- #

    def list_purge(self, limit: int) -> list[PurgeItem]:
        with self._ledger._lock:
            rows = sorted(
                self._ledger._purge.items(), key=lambda kv: (kv[1]["attempts"], kv[1]["created_at"], kv[0])
            )
            return [
                PurgeItem(doc_id, v["project_id"], v["kb_id"], v["reason"], int(v["attempts"]))
                for doc_id, v in rows[: max(0, int(limit))]
            ]

    def ack_purge(self, doc_id: str) -> None:
        with self._ledger._lock:
            self._ledger._purge.pop(doc_id, None)

    def bump_purge(self, doc_id: str) -> None:
        with self._ledger._lock:
            item = self._ledger._purge.get(doc_id)
            if item is not None:
                self._ledger._purge[doc_id] = {**item, "attempts": int(item["attempts"]) + 1}


def build_entry_tree(ledger: Any) -> EntryTreeStore:
    """按台账实现选择目录树后端（组合根单点调用）。"""
    if hasattr(ledger, "_write") and hasattr(ledger, "_conn"):
        return SqliteEntryTree(ledger)
    return MemoryEntryTree(ledger)
