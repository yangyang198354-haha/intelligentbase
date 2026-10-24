# MOD-006 / implements IFC-019（目录管理服务：浏览 / 建 / 改名 / 移动 / 分步删除；与权限无关的业务编排）
"""资料库目录管理服务。

纯 Python、不依赖 Django；权限由调用方（`ibweb.library_views`）前置。不访问 `cfg.projects`
（运行期新建项目不在其中，M-SA-018）：项目维度只来自 `Scope` 与台账。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from ib.core import DocumentRecord, IbError, NotFoundError, Scope
from ib.core.library import ConflictAction, EntryRef, FolderRecord, validate_entry_name
from ib.ledger.tree import EntryTreeStore, MoveOutcome
from ib.observability import get_logger, log_event

__all__ = [
    "FolderCrumb",
    "FileEntryView",
    "BrowsePage",
    "FolderDetail",
    "FailedDelete",
    "FolderDeleteStep",
    "LibraryService",
]

_PAGE_SIZE_MAX = 100


@dataclass(frozen=True, slots=True)
class FolderCrumb:
    folder_id: str
    name: str


@dataclass(frozen=True, slots=True)
class FileEntryView:
    record: DocumentRecord
    searchable: bool  # status=='indexed' ∧ indexed_collection_version == 项目 active 版本
    update_state: Literal["updating", "update_failed"] | None
    update_error_code: str | None


@dataclass(frozen=True, slots=True)
class BrowsePage:
    folder: FolderRecord | None  # None = 根
    breadcrumb: tuple[FolderCrumb, ...]
    folders: tuple[FolderRecord, ...]
    files: tuple[FileEntryView, ...]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class FolderDetail:
    folder: FolderRecord
    subtree_folders: int
    subtree_files: int


@dataclass(frozen=True, slots=True)
class FailedDelete:
    doc_id: str
    name: str
    path: str
    error_code: str  # 稳定码，不含异常文本


@dataclass(frozen=True, slots=True)
class FolderDeleteStep:
    done: bool
    deleted_files: int
    deleted_folders: int
    failed: tuple[FailedDelete, ...]
    remaining_files: int


def _error_code(exc: BaseException) -> str:
    """异常 → 稳定码（只用 IbError 的 code 或固定值，绝不带异常文本，FM-8）。"""
    return str(exc.code) if isinstance(exc, IbError) else "internal_error"


class LibraryService:
    def __init__(
        self,
        *,
        tree: EntryTreeStore,
        lifecycle: Any,
        ledger: Any,
        max_depth: int,
        delete_step_max_files: int = 100,
        delete_step_budget_s: float = 20.0,
    ) -> None:
        self._tree = tree
        self._lifecycle = lifecycle
        self._ledger = ledger
        self._max_depth = int(max_depth)
        self._step_max_files = max(1, int(delete_step_max_files))
        self._step_budget_s = float(delete_step_budget_s)

    # ---- 浏览 ---- #

    def browse(self, scope: Scope, folder_id: str, *, page: int, page_size: int) -> BrowsePage:
        page = max(1, int(page))
        size = min(_PAGE_SIZE_MAX, max(1, int(page_size)))
        folder = self._tree.get_folder(scope, folder_id)
        if folder_id and folder is None:
            raise NotFoundError("目录不存在或不在当前项目内")
        chain = self._tree.folder_chain(scope, folder_id) if folder_id else ()
        children = self._tree.list_children(scope, folder_id, page=page, page_size=size)
        active = self._active_version(scope)  # 台账一次取值，不逐文件查
        folders: list[FolderRecord] = []
        files: list[FileEntryView] = []
        for item in children.items:
            if isinstance(item, FolderRecord):
                folders.append(item)
            else:
                files.append(self._file_view(scope, item, active))
        return BrowsePage(
            folder=folder,
            breadcrumb=tuple(FolderCrumb(f.folder_id, f.name) for f in chain),
            folders=tuple(folders),
            files=tuple(files),
            total=children.total,
            page=page,
            page_size=size,
        )

    def _active_version(self, scope: Scope) -> str | None:
        try:
            return str(self._ledger.active_collection_version(scope.project_id))
        except Exception:  # noqa: BLE001 - 取不到则一律“不可检索”（保守），不让浏览整页失败
            return None

    def file_view(self, scope: Scope, record: DocumentRecord) -> FileEntryView:
        """单个文件的对外视图（改名 / 更新响应复用 `browse` 的同一口径）。"""
        return self._file_view(scope, record, self._active_version(scope))

    def _file_view(self, scope: Scope, record: DocumentRecord, active: str | None) -> FileEntryView:
        searchable = (
            record.status == "indexed" and active is not None and record.indexed_collection_version == active
        )
        revision = self._tree.get_revision_of(scope, record.doc_id)
        state: Literal["updating", "update_failed"] | None = None
        code: str | None = None
        if revision is not None:
            if revision.status == "failed":
                state, code = "update_failed", revision.error_code
            else:  # pending / parsing / 已索引待晋升
                state = "updating"
        return FileEntryView(record, bool(searchable), state, code)

    def folder_detail(self, scope: Scope, folder_id: str) -> FolderDetail:
        folder = self._tree.get_folder(scope, folder_id)
        if folder is None:
            raise NotFoundError("目录不存在或不在当前项目内")
        count = self._tree.count_subtree(scope, folder_id)
        return FolderDetail(folder, count.folders, count.files)

    # ---- 变更 ---- #

    def create_folder(self, scope: Scope, parent_id: str, name: str) -> FolderRecord:
        return self._tree.create_folder(scope, parent_id, validate_entry_name(name), max_depth=self._max_depth)

    def rename_folder(self, scope: Scope, folder_id: str, name: str) -> FolderRecord:
        return self._tree.rename_folder(scope, folder_id, validate_entry_name(name))

    def rename_file(self, scope: Scope, doc_id: str, name: str) -> DocumentRecord:
        return self._tree.rename_document(scope, doc_id, validate_entry_name(name))

    def move(
        self,
        scope: Scope,
        entries: Sequence[EntryRef],
        target_folder_id: str,
        resolutions: Mapping[str, ConflictAction],
    ) -> MoveOutcome:
        outcome = self._tree.move_entries(
            scope, entries, target_folder_id, resolutions, max_depth=self._max_depth
        )
        if outcome.overwritten_doc_ids:
            # 被覆盖文件的物理清理已入队；这里 best-effort 立即排空（失败留给 worker；存活过滤保证期间不可检索）
            self._lifecycle.drain_purge_queue()
        return outcome

    # ---- 分步删除（ADR-008）---- #

    def delete_folder_step(
        self, scope: Scope, folder_id: str, *, max_files: int | None = None
    ) -> FolderDeleteStep:
        if not folder_id or self._tree.get_folder(scope, folder_id) is None:
            raise NotFoundError("目录不存在或不在当前项目内")
        limit = max(1, int(max_files)) if max_files else self._step_max_files
        deadline = time.monotonic() + self._step_budget_s
        deleted_files = 0
        failed: list[FailedDelete] = []
        for doc in self._tree.list_subtree_documents(scope, folder_id, limit=limit):
            if time.monotonic() > deadline:
                break
            try:
                self._lifecycle.delete_document(scope, doc.doc_id)
                deleted_files += 1
            except NotFoundError:
                continue  # 已被并发删除：目标状态已达成，不算失败
            except Exception as exc:  # noqa: BLE001 - 逐文件失败隔离：记入 failed 并继续
                failed.append(FailedDelete(doc.doc_id, doc.doc_name, self._path_of(scope, doc), _error_code(exc)))
                get_logger("deletion").warn("failed", error_code=_error_code(exc), doc_id=doc.doc_id)
        # 本步结束后，对“已无文档且已无子目录”的目录自底向上删除（失败文件及其目录链保留）
        subtree_ids = [f.folder_id for f in self._tree.list_subtree_folders(scope, folder_id)] + [folder_id]
        deleted_folders = self._tree.delete_empty_folders(scope, subtree_ids)
        still_there = self._tree.get_folder(scope, folder_id) is not None
        remaining = self._tree.count_subtree(scope, folder_id).files if still_there else 0
        log_event("deletion", "folder_step", project_id=scope.project_id, count=deleted_files)
        return FolderDeleteStep(
            done=not still_there,
            deleted_files=deleted_files,
            deleted_folders=deleted_folders,
            failed=tuple(failed),
            remaining_files=remaining,
        )

    def _path_of(self, scope: Scope, doc: DocumentRecord) -> str:
        try:
            located = self._tree.resolve_live(scope.project_id, [doc.doc_id]).get(doc.doc_id)
        except Exception:  # noqa: BLE001
            located = None
        return located.path if located is not None else doc.doc_name
