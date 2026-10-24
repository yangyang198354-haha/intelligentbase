# MOD-007 / implements IFC-020（批量上传编排：清单计划 -> 批次 -> 逐文件受理）
"""批量上传编排服务（ADR-003）：服务端权威的“计划 + 逐文件受理”。

* `plan`：校验限额（条数 → 总大小 → 目录深度）、逐项分类、同名冲突检测；dry_run 只返回计划，
  commit 才落批次。**任何 4xx 都不产生批次、目录或文件**；目录延迟到首个文件受理时才与文件同事务创建。
* `accept_item`：幂等；以实际字节数核对声明大小（声明和 <= 总上限、实际 <= 声明 => 累计实际 <= 总上限）。
* 不访问 `cfg.projects`；`kb_id == project_id`（与上传入口约定一致）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, BinaryIO, Literal, Mapping, Sequence

from ib.core import (
    DependencyUnavailableError,
    NotFoundError,
    RequestContext,
    Scope,
    ValidationError,
)
from ib.core.library import (
    ConflictAction,
    EntryKind,
    EntryNameError,
    LibraryConflictError,
    LibraryValidationError,
    NameClash,
    name_key_of,
    next_free_name,
    validate_entry_name,
)
from ib.ledger.tree import EntryTreeStore
from ib.ledger.upload_batches import BatchItemPlan, BatchSummary, UploadBatchStore
from ib.lifecycle import DocumentPlacement, RejectedUpload

__all__ = [
    "ManifestEntry",
    "UploadLimits",
    "PlannedItem",
    "PlanConflict",
    "UploadPlan",
    "UploadItemResult",
    "UploadBatchService",
]

_MAX_REL_PATH = 4096
_MAX_DECLARED_SIZE = 2**40


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    client_idx: int
    rel_path: str  # '/' 分隔；末段为文件名
    size: int


@dataclass(frozen=True, slots=True)
class UploadLimits:
    max_files: int
    max_total_bytes: int
    max_depth: int
    max_file_bytes: int


@dataclass(frozen=True, slots=True)
class PlannedItem:
    client_idx: int
    rel_path: str
    final_rel_path: str | None
    action: Literal["create", "update", "skip"]
    reason_code: str | None  # skip 原因：UNSUPPORTED_TYPE|EMPTY_FILE|TOO_LARGE|NAME_INVALID|USER_SKIPPED|CONFLICT_UNRESOLVED
    target_doc_id: str | None


@dataclass(frozen=True, slots=True)
class PlanConflict:
    rel_path: str  # 文件：完整相对路径；文件夹：冲突的目录前缀
    kind: EntryKind
    existing_id: str
    existing_name: str


@dataclass(frozen=True, slots=True)
class UploadPlan:
    batch_id: str | None  # dry_run 为 None
    total: int
    limits: UploadLimits
    items: tuple[PlannedItem, ...]
    conflicts: tuple[PlanConflict, ...]
    accepted_count: int
    skipped_count: int


@dataclass(frozen=True, slots=True)
class UploadItemResult:
    client_idx: int
    state: Literal["accepted", "skipped", "failed"]
    reason_code: str | None  # skip 原因 + MAGIC_MISMATCH | SIZE_MISMATCH | NAME_CONFLICT | CONTENT_UNCHANGED | DOC_BUSY ...
    doc_id: str | None
    final_rel_path: str | None


@dataclass(slots=True)
class _DirState:
    mode: Literal["existing", "new", "skip", "unresolved"]
    folder_id: str | None  # existing 时为台账目录 id；new 时 None
    final_name: str


class UploadBatchService:
    def __init__(
        self,
        *,
        tree: EntryTreeStore,
        batches: UploadBatchStore,
        lifecycle: Any,
        limits: UploadLimits,
        batch_ttl_hours: int,
    ) -> None:
        self._tree = tree
        self._batches = batches
        self._lifecycle = lifecycle
        self._limits = limits
        self._ttl = int(batch_ttl_hours)

    # ================================================================== #
    # plan
    # ================================================================== #

    def plan(
        self,
        ctx: RequestContext,
        scope: Scope,
        *,
        target_folder_id: str,
        entries: Sequence[ManifestEntry],
        resolutions: Mapping[str, ConflictAction],
        commit: bool,
    ) -> UploadPlan:
        from ib.parsing import SUPPORTED_EXTS, ext_of

        lim = self._limits
        count = len(entries)
        if count == 0:
            raise LibraryValidationError("上传清单为空", code="bad_request")
        # 1) 条数 → 2) 总大小 → 3) 目录深度 → 4) 逐项分类 → 5) 同名冲突
        if count > lim.max_files:
            raise LibraryValidationError(
                "单次上传文件数超出上限", code="limit_files", details={"limit": lim.max_files, "actual": count}
            )
        indexes = {e.client_idx for e in entries}
        if len(indexes) != count or any(not 0 <= i < count for i in indexes):
            raise LibraryValidationError("client_idx 必须唯一且位于 [0, 总数)", code="bad_request")
        for entry in entries:
            if (
                isinstance(entry.size, bool)
                or not isinstance(entry.size, int)
                or not 0 <= entry.size <= _MAX_DECLARED_SIZE
                or not isinstance(entry.rel_path, str)
                or not 0 < len(entry.rel_path) <= _MAX_REL_PATH
            ):
                raise LibraryValidationError("清单项非法（size / rel_path）", code="bad_request")
        total_bytes = sum(e.size for e in entries)
        if total_bytes > lim.max_total_bytes:
            raise LibraryValidationError(
                "单次上传总大小超出上限",
                code="limit_total_bytes",
                details={"limit": lim.max_total_bytes, "actual": total_bytes},
            )
        target = self._tree.get_folder(scope, target_folder_id) if target_folder_id else None
        if target_folder_id and target is None:
            raise NotFoundError("目标目录不存在或不在当前项目内")
        base_depth = target.depth if target else 0

        ordered = sorted(entries, key=lambda e: e.client_idx)
        parsed: dict[int, tuple[list[str], str]] = {}
        skip: dict[int, str] = {}
        for entry in ordered:
            try:
                segments = [validate_entry_name(seg) for seg in entry.rel_path.split("/")]
            except EntryNameError:
                skip[entry.client_idx] = "NAME_INVALID"
                continue
            parsed[entry.client_idx] = (segments[:-1], segments[-1])
            ext = ext_of(segments[-1])
            if not ext or ext not in SUPPORTED_EXTS:
                skip[entry.client_idx] = "UNSUPPORTED_TYPE"
            elif entry.size <= 0:
                skip[entry.client_idx] = "EMPTY_FILE"
            elif entry.size > lim.max_file_bytes:
                skip[entry.client_idx] = "TOO_LARGE"
        deepest = max(
            (base_depth + len(parsed[i][0]) for i in parsed if i not in skip), default=base_depth
        )
        if deepest > lim.max_depth:
            raise LibraryValidationError(
                "目录层级已达上限", code="depth_exceeded", details={"limit": lim.max_depth, "actual": deepest}
            )

        planner = _Planner(self._tree, scope, target_folder_id, resolutions)
        planned: list[PlannedItem] = []
        by_idx = {e.client_idx: e for e in ordered}
        for entry in ordered:
            idx = entry.client_idx
            if idx in skip:
                planned.append(PlannedItem(idx, entry.rel_path, None, "skip", skip[idx], None))
                continue
            dirs, name = parsed[idx]
            planned.append(planner.plan_file(entry, dirs, name))
        conflicts = tuple(planner.conflicts)
        accepted_count = sum(1 for p in planned if p.action != "skip")
        result = UploadPlan(
            batch_id=None,
            total=count,
            limits=lim,
            items=tuple(planned),
            conflicts=conflicts,
            accepted_count=accepted_count,
            skipped_count=count - accepted_count,
        )
        if not commit:
            return result
        if conflicts:
            raise LibraryConflictError(
                "存在尚未选择处理方式的同名冲突",
                code="unresolved_conflict",
                clashes=tuple(NameClash(c.kind, c.existing_id, c.existing_name) for c in conflicts),
                details={"rel_paths": [c.rel_path for c in conflicts]},
            )
        record = self._batches.create_batch(
            scope,
            target_folder_id=target_folder_id,
            items=[
                BatchItemPlan(
                    client_idx=p.client_idx,
                    rel_path=p.rel_path,
                    final_rel_path=p.final_rel_path,
                    action=p.action,
                    declared_size=by_idx[p.client_idx].size,
                    target_doc_id=p.target_doc_id,
                    reason_code=p.reason_code,
                )
                for p in planned
            ],
            ttl_hours=self._ttl,
        )
        return UploadPlan(
            batch_id=record.batch_id,
            total=result.total,
            limits=lim,
            items=result.items,
            conflicts=(),
            accepted_count=accepted_count,
            skipped_count=result.skipped_count,
        )

    # ================================================================== #
    # accept_item
    # ================================================================== #

    def accept_item(
        self,
        ctx: RequestContext,
        scope: Scope,
        batch_id: str,
        client_idx: int,
        *,
        filename: str,
        size_bytes: int,
        head: bytes,
        data: BinaryIO,
    ) -> UploadItemResult:
        batch = self._batches.get_batch(scope, batch_id)
        item = self._batches.get_item(scope, batch_id, client_idx) if batch is not None else None
        if batch is None or item is None:
            raise NotFoundError("批次或批次项不存在")
        if item.state in ("accepted", "skipped"):
            return UploadItemResult(client_idx, item.state, item.reason_code, item.doc_id, item.final_rel_path)

        def finish(
            state: Literal["accepted", "skipped", "failed"],
            reason: str | None,
            doc_id: str | None = None,
        ) -> UploadItemResult:
            stored = self._batches.mark_item(
                scope, batch_id, client_idx, state=state, reason_code=reason, doc_id=doc_id,
                final_rel_path=item.final_rel_path,
            )
            return UploadItemResult(client_idx, stored.state, stored.reason_code, stored.doc_id, stored.final_rel_path)

        if int(size_bytes) > item.declared_size:
            return finish("skipped", "SIZE_MISMATCH")
        final_rel = item.final_rel_path or item.rel_path
        *dirs, name = final_rel.split("/")
        verdict = self._lifecycle.classify_upload(name, int(size_bytes), head)
        if isinstance(verdict, RejectedUpload):
            return finish("skipped", verdict.reason.value)
        kb_id = scope.project_id
        try:
            if item.action == "update" and item.target_doc_id:
                outcome = self._lifecycle.submit_revision(
                    ctx, item.target_doc_id, verdict, data=data, new_name=name, on_conflict="fail"
                )
                if not outcome.changed:
                    return finish("skipped", "CONTENT_UNCHANGED", outcome.live.doc_id)
                return finish("accepted", None, outcome.live.doc_id)
            record = self._lifecycle.submit_library_document(
                ctx,
                verdict,
                kb_id,
                placement=DocumentPlacement(
                    folder_id=batch.target_folder_id, rel_dirs=tuple(dirs), name=name, on_conflict="fail"
                ),
                data=data,
            )
            return finish("accepted", None, record.doc_id)
        except LibraryConflictError as exc:
            return finish("skipped", "DOC_BUSY" if exc.code in ("doc_busy", "update_in_progress") else "NAME_CONFLICT")
        except LibraryValidationError as exc:
            return finish("skipped", "DEPTH_EXCEEDED" if exc.code == "depth_exceeded" else "INVALID_FILE")
        except NotFoundError:
            return finish("skipped", "TARGET_MISSING")
        except DependencyUnavailableError:
            self._batches.mark_item(
                scope, batch_id, client_idx, state="failed", reason_code="SERVER_ERROR", doc_id=None,
                final_rel_path=item.final_rel_path,
            )
            raise
        except EntryNameError:
            return finish("skipped", "NAME_INVALID")
        except ValidationError:
            return finish("skipped", "INVALID_FILE")

    def summary(self, scope: Scope, batch_id: str) -> BatchSummary:
        return self._batches.summarize(scope, batch_id)


class _Planner:
    """冲突感知的路径规划（一次 `plan` 调用一个实例）。"""

    def __init__(
        self, tree: EntryTreeStore, scope: Scope, target_folder_id: str, resolutions: Mapping[str, ConflictAction]
    ) -> None:
        self._tree = tree
        self._scope = scope
        self._root: str | None = target_folder_id
        self._resolutions = resolutions
        self._dirs: dict[tuple[str, ...], _DirState] = {}
        self._used: dict[Any, set[str]] = {}
        self._targets: set[str] = set()
        self._cache: dict[tuple[str, str], NameClash | None] = {}
        self.conflicts: list[PlanConflict] = []

    def _clash(self, parent_id: str, name: str) -> NameClash | None:
        key = (parent_id, name_key_of(name))
        if key not in self._cache:
            self._cache[key] = self._tree.find_name_clashes(self._scope, parent_id, [name]).get(key[1])
        return self._cache[key]

    def _free_name(self, parent_id: str | None, token: Any, name: str, *, is_file: bool) -> str:
        """在 (现有目录 ∪ 本次计划已占用) 中取第一个不冲突的名称。"""
        reserved = self._used.setdefault(token, set())
        taken = set(reserved)
        while True:
            candidate = next_free_name(name, taken, is_file=is_file)
            if parent_id is not None and self._clash(parent_id, candidate) is not None:
                taken.add(name_key_of(candidate))
                continue
            return candidate

    def _decide_dir(
        self, parent: _DirState | None, token: Any, seg: str, prefix_text: str
    ) -> _DirState:
        parent_id = self._root if parent is None else parent.folder_id
        if parent_id is None:  # 父目录是本次新建的：不可能已有同名
            name = self._free_name(None, token, seg, is_file=False)
            self._used[token].add(name_key_of(name))
            return _DirState("new", None, name)
        clash = self._clash(parent_id, seg)
        reserved = self._used.setdefault(token, set())
        if clash is None and name_key_of(seg) not in reserved:
            reserved.add(name_key_of(seg))
            return _DirState("new", None, seg)
        if clash is None:  # 与本次计划内另一条目同名（清单内重复）：自动改名
            name = self._free_name(parent_id, token, seg, is_file=False)
            reserved.add(name_key_of(name))
            return _DirState("new", None, name)
        action = self._resolutions.get(prefix_text)
        if action is None:
            self.conflicts.append(PlanConflict(prefix_text, clash.kind, clash.entry_id, clash.name))
            return _DirState("unresolved", None, seg)
        if action == "skip":
            return _DirState("skip", None, seg)
        if action == "overwrite" and clash.kind == "folder":  # 文件夹覆盖 = 合并
            return _DirState("existing", clash.entry_id, clash.name)
        name = self._free_name(parent_id, token, seg, is_file=False)  # rename（跨类 overwrite 亦按改名）
        reserved.add(name_key_of(name))
        return _DirState("new", None, name)

    def plan_file(self, entry: ManifestEntry, dirs: list[str], name: str) -> PlannedItem:
        idx, rel = entry.client_idx, entry.rel_path
        parent: _DirState | None = None
        final_dirs: list[str] = []
        token: Any = self._root
        for i, seg in enumerate(dirs):
            key_path = tuple(name_key_of(s) for s in dirs[: i + 1])
            state = self._dirs.get(key_path)
            if state is None:
                state = self._decide_dir(parent, token, seg, "/".join(dirs[: i + 1]))
                self._dirs[key_path] = state
            if state.mode == "skip":
                return PlannedItem(idx, rel, None, "skip", "USER_SKIPPED", None)
            if state.mode == "unresolved":
                return PlannedItem(idx, rel, None, "skip", "CONFLICT_UNRESOLVED", None)
            parent = state
            final_dirs.append(state.final_name)
            token = state.folder_id if state.folder_id is not None else ("new", *final_dirs)
        parent_id = self._root if parent is None else parent.folder_id
        reserved = self._used.setdefault(token, set())
        key = name_key_of(name)
        clash = self._clash(parent_id, name) if parent_id is not None else None
        action: Literal["create", "update"] = "create"
        target: str | None = None
        final_name = name
        if clash is None and key not in reserved:
            pass
        elif clash is None:  # 清单内重复
            final_name = self._free_name(parent_id, token, name, is_file=True)
        else:
            resolution = self._resolutions.get(rel)
            if resolution is None:
                self.conflicts.append(PlanConflict(rel, clash.kind, clash.entry_id, clash.name))
                return PlannedItem(idx, rel, None, "skip", "CONFLICT_UNRESOLVED", None)
            if resolution == "skip":
                return PlannedItem(idx, rel, None, "skip", "USER_SKIPPED", None)
            if resolution == "overwrite" and clash.kind == "file" and clash.entry_id not in self._targets:
                action, target = "update", clash.entry_id
                self._targets.add(clash.entry_id)
            else:
                final_name = self._free_name(parent_id, token, name, is_file=True)
        reserved.add(name_key_of(final_name))
        return PlannedItem(idx, rel, "/".join([*final_dirs, final_name]), action, None, target)
