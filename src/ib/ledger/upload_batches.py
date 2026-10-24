# MOD-003 / implements IFC-016（UploadBatchStore：上传批次与逐项状态的持久化；SQLite + 内存替身）
"""上传批次存储（ADR-003）：服务端权威地记录“清单计划 + 逐文件结果”，按 TTL 清理。

存储层不做鉴权；所有方法限定 `scope.project_id`，批次不属于该项目 → `None` / `NotFoundError`。
SQLite 实现复用 `SqliteLedgerRepository` 的线程局部连接与写事务（同一台账文件、同一迁移 007）。
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, replace
from typing import Any, Literal, Protocol, Sequence

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import NotFoundError, Scope

__all__ = [
    "ItemAction",
    "ItemState",
    "BatchItemPlan",
    "BatchItem",
    "BatchRecord",
    "BatchSummary",
    "UploadBatchStore",
    "SqliteUploadBatchStore",
    "MemoryUploadBatchStore",
    "build_upload_batch_store",
]

ItemAction = Literal["create", "update", "skip"]
ItemState = Literal["planned", "accepted", "skipped", "failed"]
_TERMINAL = frozenset({"accepted", "skipped"})


@dataclass(frozen=True, slots=True)
class BatchItemPlan:
    client_idx: int
    rel_path: str  # 客户端提交的相对路径（含文件名）
    final_rel_path: str | None  # 服务端定稿（含自动改名）；skip 为 None
    action: ItemAction
    declared_size: int
    target_doc_id: str | None  # action='update' 时的旧 doc_id
    reason_code: str | None  # action='skip' 时的跳过原因


@dataclass(frozen=True, slots=True)
class BatchItem:
    batch_id: str
    client_idx: int
    rel_path: str
    final_rel_path: str | None
    action: ItemAction
    declared_size: int
    target_doc_id: str | None
    state: ItemState
    reason_code: str | None
    doc_id: str | None


@dataclass(frozen=True, slots=True)
class BatchRecord:
    batch_id: str
    project_id: str
    target_folder_id: str
    planned_files: int
    planned_bytes: int
    created_at: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class BatchSummary:
    batch: BatchRecord
    total: int
    accepted: int
    skipped: int
    failed: int
    pending: int  # state='planned'
    items: tuple[BatchItem, ...]


class UploadBatchStore(Protocol):
    def create_batch(
        self, scope: Scope, *, target_folder_id: str, items: Sequence[BatchItemPlan], ttl_hours: int
    ) -> BatchRecord: ...
    def get_batch(self, scope: Scope, batch_id: str) -> BatchRecord | None: ...
    def get_item(self, scope: Scope, batch_id: str, client_idx: int) -> BatchItem | None: ...
    def mark_item(
        self,
        scope: Scope,
        batch_id: str,
        client_idx: int,
        *,
        state: ItemState,
        reason_code: str | None,
        doc_id: str | None,
        final_rel_path: str | None,
    ) -> BatchItem: ...
    def summarize(self, scope: Scope, batch_id: str) -> BatchSummary: ...
    def purge_expired(self, now_iso: str) -> int: ...


def _summary(batch: BatchRecord, items: Sequence[BatchItem]) -> BatchSummary:
    ordered = tuple(sorted(items, key=lambda i: i.client_idx))
    count = lambda state: sum(1 for i in ordered if i.state == state)  # noqa: E731
    return BatchSummary(
        batch=batch,
        total=len(ordered),
        accepted=count("accepted"),
        skipped=count("skipped"),
        failed=count("failed"),
        pending=count("planned"),
        items=ordered,
    )


def _check_plans(items: Sequence[BatchItemPlan]) -> None:
    seen: set[int] = set()
    for plan in items:
        if plan.client_idx < 0 or plan.client_idx >= len(items) or plan.client_idx in seen:
            raise ValueError("client_idx 必须唯一且位于 [0, planned_files)")
        seen.add(plan.client_idx)


_BATCH_COLS = "batch_id, project_id, target_folder_id, planned_files, planned_bytes, created_at, expires_at"
_ITEM_COLS = (
    "batch_id, client_idx, rel_path, final_rel_path, action, declared_size, target_doc_id,"
    " state, reason_code, doc_id"
)


def _item_of(row: Sequence[Any]) -> BatchItem:
    return BatchItem(row[0], int(row[1]), row[2], row[3], row[4], int(row[5]), row[6], row[7], row[8], row[9])


class SqliteUploadBatchStore:
    """SQLite 实现（复用台账连接与 `BEGIN IMMEDIATE` 写事务）。"""

    def __init__(self, ledger: Any) -> None:
        self._ledger = ledger

    def _c(self) -> Any:
        return self._ledger._conn()

    def create_batch(
        self, scope: Scope, *, target_folder_id: str, items: Sequence[BatchItemPlan], ttl_hours: int
    ) -> BatchRecord:
        _check_plans(items)
        now = utc_now_iso()
        record = BatchRecord(
            batch_id=uuid.uuid4().hex,
            project_id=scope.project_id,
            target_folder_id=target_folder_id,
            planned_files=len(items),
            planned_bytes=sum(i.declared_size for i in items if i.action != "skip"),
            created_at=now,
            expires_at=iso_plus_seconds(int(ttl_hours) * 3600),
        )
        with self._ledger._write() as conn:
            self._purge(conn, now)
            conn.execute(
                f"INSERT INTO upload_batches ({_BATCH_COLS}) VALUES (?,?,?,?,?,?,?)",
                (record.batch_id, record.project_id, record.target_folder_id, record.planned_files,
                 record.planned_bytes, record.created_at, record.expires_at),
            )
            conn.executemany(
                f"INSERT INTO upload_batch_items ({_ITEM_COLS}, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (record.batch_id, p.client_idx, p.rel_path, p.final_rel_path, p.action, p.declared_size,
                     p.target_doc_id, "skipped" if p.action == "skip" else "planned", p.reason_code, None, now)
                    for p in items
                ],
            )
        return record

    def get_batch(self, scope: Scope, batch_id: str) -> BatchRecord | None:
        row = self._c().execute(
            f"SELECT {_BATCH_COLS} FROM upload_batches WHERE project_id = ? AND batch_id = ?",
            (scope.project_id, batch_id),
        ).fetchone()
        return None if row is None else BatchRecord(row[0], row[1], row[2], int(row[3]), int(row[4]), row[5], row[6])

    def get_item(self, scope: Scope, batch_id: str, client_idx: int) -> BatchItem | None:
        if self.get_batch(scope, batch_id) is None:
            return None
        row = self._c().execute(
            f"SELECT {_ITEM_COLS} FROM upload_batch_items WHERE batch_id = ? AND client_idx = ?",
            (batch_id, int(client_idx)),
        ).fetchone()
        return None if row is None else _item_of(row)

    def mark_item(
        self,
        scope: Scope,
        batch_id: str,
        client_idx: int,
        *,
        state: ItemState,
        reason_code: str | None,
        doc_id: str | None,
        final_rel_path: str | None,
    ) -> BatchItem:
        with self._ledger._write() as conn:
            batch = conn.execute(
                "SELECT 1 FROM upload_batches WHERE project_id = ? AND batch_id = ?",
                (scope.project_id, batch_id),
            ).fetchone()
            row = conn.execute(
                f"SELECT {_ITEM_COLS} FROM upload_batch_items WHERE batch_id = ? AND client_idx = ?",
                (batch_id, int(client_idx)),
            ).fetchone()
            if batch is None or row is None:
                raise NotFoundError("批次或批次项不存在")
            current = _item_of(row)
            if current.state in _TERMINAL:
                return current  # 终态幂等
            conn.execute(
                "UPDATE upload_batch_items SET state = ?, reason_code = ?, doc_id = ?,"
                " final_rel_path = COALESCE(?, final_rel_path), updated_at = ?"
                " WHERE batch_id = ? AND client_idx = ?",
                (state, reason_code, doc_id, final_rel_path, utc_now_iso(), batch_id, int(client_idx)),
            )
            return replace(
                current,
                state=state,
                reason_code=reason_code,
                doc_id=doc_id,
                final_rel_path=final_rel_path or current.final_rel_path,
            )

    def summarize(self, scope: Scope, batch_id: str) -> BatchSummary:
        batch = self.get_batch(scope, batch_id)
        if batch is None:
            raise NotFoundError("批次不存在")
        rows = self._c().execute(
            f"SELECT {_ITEM_COLS} FROM upload_batch_items WHERE batch_id = ? ORDER BY client_idx", (batch_id,)
        ).fetchall()
        return _summary(batch, [_item_of(r) for r in rows])

    @staticmethod
    def _purge(conn: Any, now_iso: str) -> int:
        conn.execute(
            "DELETE FROM upload_batch_items WHERE batch_id IN"
            " (SELECT batch_id FROM upload_batches WHERE expires_at < ?)",
            (now_iso,),
        )
        return int(conn.execute("DELETE FROM upload_batches WHERE expires_at < ?", (now_iso,)).rowcount)

    def purge_expired(self, now_iso: str) -> int:
        with self._ledger._write() as conn:
            return self._purge(conn, now_iso)


class MemoryUploadBatchStore:
    """内存替身（语义与 SQLite 实现对齐）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._batches: dict[str, BatchRecord] = {}
        self._items: dict[str, dict[int, BatchItem]] = {}

    def create_batch(
        self, scope: Scope, *, target_folder_id: str, items: Sequence[BatchItemPlan], ttl_hours: int
    ) -> BatchRecord:
        _check_plans(items)
        with self._lock:
            self.purge_expired(utc_now_iso())
            record = BatchRecord(
                batch_id=uuid.uuid4().hex,
                project_id=scope.project_id,
                target_folder_id=target_folder_id,
                planned_files=len(items),
                planned_bytes=sum(i.declared_size for i in items if i.action != "skip"),
                created_at=utc_now_iso(),
                expires_at=iso_plus_seconds(int(ttl_hours) * 3600),
            )
            self._batches[record.batch_id] = record
            self._items[record.batch_id] = {
                p.client_idx: BatchItem(
                    record.batch_id, p.client_idx, p.rel_path, p.final_rel_path, p.action, p.declared_size,
                    p.target_doc_id, "skipped" if p.action == "skip" else "planned", p.reason_code, None,
                )
                for p in items
            }
            return record

    def get_batch(self, scope: Scope, batch_id: str) -> BatchRecord | None:
        with self._lock:
            batch = self._batches.get(batch_id)
            return batch if batch is not None and batch.project_id == scope.project_id else None

    def get_item(self, scope: Scope, batch_id: str, client_idx: int) -> BatchItem | None:
        with self._lock:
            if self.get_batch(scope, batch_id) is None:
                return None
            return self._items.get(batch_id, {}).get(int(client_idx))

    def mark_item(
        self,
        scope: Scope,
        batch_id: str,
        client_idx: int,
        *,
        state: ItemState,
        reason_code: str | None,
        doc_id: str | None,
        final_rel_path: str | None,
    ) -> BatchItem:
        with self._lock:
            current = self.get_item(scope, batch_id, client_idx)
            if current is None:
                raise NotFoundError("批次或批次项不存在")
            if current.state in _TERMINAL:
                return current
            updated = replace(
                current,
                state=state,
                reason_code=reason_code,
                doc_id=doc_id,
                final_rel_path=final_rel_path or current.final_rel_path,
            )
            self._items[batch_id][int(client_idx)] = updated
            return updated

    def summarize(self, scope: Scope, batch_id: str) -> BatchSummary:
        with self._lock:
            batch = self.get_batch(scope, batch_id)
            if batch is None:
                raise NotFoundError("批次不存在")
            return _summary(batch, list(self._items.get(batch_id, {}).values()))

    def purge_expired(self, now_iso: str) -> int:
        with self._lock:
            gone = [bid for bid, b in self._batches.items() if b.expires_at < now_iso]
            for bid in gone:
                self._batches.pop(bid, None)
                self._items.pop(bid, None)
            return len(gone)


def build_upload_batch_store(ledger: Any) -> UploadBatchStore:
    """按台账实现选择批次存储后端（组合根单点调用）。"""
    if hasattr(ledger, "_write") and hasattr(ledger, "_conn"):
        return SqliteUploadBatchStore(ledger)
    return MemoryUploadBatchStore()
