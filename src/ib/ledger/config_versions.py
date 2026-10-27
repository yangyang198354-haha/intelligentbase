# MOD-R26-06 / implements IFC-R26-050, IFC-R26-051：配置版本 / 草稿 / 评审缓存存储（SQLite + 内存两实现）
"""配置版本存储（ADR-55 / ADR-59）。

* `ConfigVersionStore`：`begin_publish`（BEGIN IMMEDIATE 内核对 head、占 pending）/ `commit_publish` /
  `abort_publish` / `claim_stale_pending`（CAS，仅一个调用方得到版本号）/ `prune_all`；
* `ConfigDraftStore`：每账号每项目草稿副本（owner 隔离，配额与大小限制）；
* `BuilderEvalCache`：自评 LLM 项缓存（OQ-R26-A04）。

快照序列化 / 清单哈希来自纯函数模块 `ib.config.versioning`（惰性导入；该模块只依赖 `ib.core`）。
SQLite 实现沿用 `SqliteConfigAuditStore` 的纪律：线程局部连接 + WAL + busy_timeout；
所有 SQL 参数化，表 / 列名为模块常量。
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from ib.core import (
    BeginResult,
    ConfigAuditEntry,
    ConfigSnapshot,
    ConflictError,
    DependencyUnavailableError,
    DraftRecord,
    HeadState,
    NewVersion,
    StartupError,
    ValidationError,
    VersionRecord,
)
from ib.ledger.schema import ensure_schema, missing_config_version_columns

__all__ = [
    "SqliteConfigVersionStore",
    "MemoryConfigVersionStore",
    "SqliteConfigDraftStore",
    "MemoryConfigDraftStore",
    "SqliteBuilderEvalCache",
    "MemoryBuilderEvalCache",
    "build_config_version_store",
    "build_config_draft_store",
    "build_builder_eval_cache",
    "DRAFT_MAX_BYTES",
]

DRAFT_MAX_BYTES = 1024 * 1024
_ISO = "%Y-%m-%dT%H:%M:%SZ"
_V_COLS = (
    "project_id, version, parent_version, status, kind, rolled_back_to, actor, created_at, "
    "summary, manifest_hash, snapshot_bytes"
)


def _age_s(now: str, then: str) -> float:
    try:
        a = datetime.strptime(now, _ISO).replace(tzinfo=timezone.utc)
        b = datetime.strptime(then, _ISO).replace(tzinfo=timezone.utc)
    except ValueError:
        return float("inf")  # 时间戳不可解析：视为陈旧，交恢复路径处理（fail-safe）
    return (a - b).total_seconds()


def _versioning():
    from ib.config import versioning  # 惰性导入：纯函数模块，避免包初始化期循环

    return versioning


def _record(row: Any) -> VersionRecord:
    return VersionRecord(
        project_id=row[0],
        version=int(row[1]),
        parent_version=int(row[2]),
        status=row[3],
        kind=row[4],
        rolled_back_to=None if row[5] is None else int(row[5]),
        actor=row[6],
        created_at=row[7],
        summary=row[8],
        manifest_hash=row[9],
        snapshot_bytes=int(row[10]),
    )


# --------------------------------------------------------------------------- #
# SQLite 公共连接基类
# --------------------------------------------------------------------------- #


class _SqliteBase:
    _MEM_SEQ = 0

    def __init__(self, path: str, *, busy_timeout_ms: int = 5000) -> None:
        self._path = path or ":memory:"
        self._busy_timeout_ms = busy_timeout_ms
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()
        if self._path == ":memory:":
            _SqliteBase._MEM_SEQ += 1
            self._mem_name = f"ib_cfgver_mem_{os.getpid()}_{_SqliteBase._MEM_SEQ}"
        else:
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            connection = sqlite3.connect(
                f"file:{self._mem_name}?mode=memory&cache=shared",
                uri=True,
                check_same_thread=False,
                isolation_level=None,
                timeout=self._busy_timeout_ms / 1000.0,
            )
        else:
            connection = sqlite3.connect(
                self._path,
                check_same_thread=False,
                isolation_level=None,
                timeout=self._busy_timeout_ms / 1000.0,
            )
        connection.execute(f"PRAGMA busy_timeout={int(self._busy_timeout_ms)}")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    def _conn(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            try:
                connection = self._connect()
            except sqlite3.Error as exc:
                raise DependencyUnavailableError(
                    f"配置版本存储连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        connection = self._conn()
        try:
            ensure_schema(connection)
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"配置版本存储初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_config_version_columns(connection)
        if missing:
            tables = "；".join(f"{t}:{','.join(cols)}" for t, cols in missing.items())
            raise StartupError(
                f"配置版本表结构不完整（缺少列）：{tables}。请先执行 `python -m ibweb.bootstrap --ensure-schema`。"
            )

    def close(self) -> None:
        with self._connections_lock:
            connections = list(self._connections)
            self._connections.clear()
        for connection in connections:
            try:
                connection.close()
            except sqlite3.Error:
                pass
        self._local = threading.local()

    def _begin(self) -> sqlite3.Connection:
        connection = self._conn()
        connection.execute("BEGIN IMMEDIATE")
        return connection


# --------------------------------------------------------------------------- #
# 版本存储
# --------------------------------------------------------------------------- #


class SqliteConfigVersionStore(_SqliteBase):
    """`ConfigVersionStore` 的 SQLite 实现。"""

    def head(self, project_id: str) -> HeadState:
        row = self._conn().execute(
            "SELECT published_version, pending_version, updated_at FROM config_head WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            return HeadState(project_id, 0, None, "")
        return HeadState(project_id, int(row[0]), None if row[1] is None else int(row[1]), row[2])

    def get_version(self, project_id: str, version: int) -> tuple[VersionRecord, ConfigSnapshot] | None:
        row = self._conn().execute(
            f"SELECT {_V_COLS}, snapshot_json FROM config_versions "
            "WHERE project_id = ? AND version = ? AND status = 'published'",
            (project_id, int(version)),
        ).fetchone()
        if row is None:
            return None
        return _record(row), _versioning().snapshot_from_json(row[11])

    def list_versions(
        self, project_id: str, *, limit: int, before_version: int | None
    ) -> tuple[VersionRecord, ...]:
        lim = max(0, min(int(limit), 500))
        if before_version is None:
            rows = self._conn().execute(
                f"SELECT {_V_COLS} FROM config_versions WHERE project_id = ? AND status = 'published' "
                "ORDER BY version DESC LIMIT ?",
                (project_id, lim),
            ).fetchall()
        else:
            rows = self._conn().execute(
                f"SELECT {_V_COLS} FROM config_versions WHERE project_id = ? AND status = 'published' "
                "AND version < ? ORDER BY version DESC LIMIT ?",
                (project_id, int(before_version), lim),
            ).fetchall()
        return tuple(_record(r) for r in rows)

    def begin_publish(
        self,
        project_id: str,
        *,
        base_version: int,
        new: NewVersion,
        snapshot: ConfigSnapshot,
        extra_baseline: ConfigSnapshot | None,
        now: str,
        stale_after_s: float,
    ) -> BeginResult:
        vz = _versioning()
        snap_json = vz.snapshot_to_json(snapshot)
        base_json = vz.snapshot_to_json(extra_baseline) if extra_baseline is not None else None
        connection = self._begin()
        try:
            head = connection.execute(
                "SELECT published_version, pending_version FROM config_head WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            published = int(head[0]) if head else 0
            pending = None if head is None or head[1] is None else int(head[1])
            if pending is not None:
                # 未陈旧 → busy；已陈旧也不在此处自动回收（须先走 recover：还原文件后 abort），故同样回执 busy。
                connection.execute("ROLLBACK")
                return BeginResult("busy", None, published, pending)
            if published != int(base_version):
                connection.execute("ROLLBACK")
                return BeginResult("stale_base", None, published, None)
            max_row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM config_versions WHERE project_id = ?", (project_id,)
            ).fetchone()
            next_version = int(max_row[0]) + 1
            parent = published
            if base_json is not None and published == 0:
                bh = vz.manifest_hash(extra_baseline)  # type: ignore[arg-type]
                connection.execute(
                    "INSERT INTO config_versions (project_id, version, parent_version, status, kind, "
                    "rolled_back_to, actor, created_at, summary, manifest_hash, snapshot_json, snapshot_bytes) "
                    "VALUES (?, ?, 0, 'published', 'baseline', NULL, 'system', ?, ?, ?, ?, ?)",
                    (project_id, next_version, now, "升级前基线", bh, base_json, len(base_json.encode("utf-8"))),
                )
                parent = next_version
                next_version += 1
            connection.execute(
                "INSERT INTO config_versions (project_id, version, parent_version, status, kind, "
                "rolled_back_to, actor, created_at, summary, manifest_hash, snapshot_json, snapshot_bytes) "
                "VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    project_id, next_version, parent, new.kind, new.rolled_back_to, new.actor, now,
                    new.summary[:200], new.manifest_hash, snap_json, len(snap_json.encode("utf-8")),
                ),
            )
            connection.execute(
                "INSERT INTO config_head (project_id, published_version, pending_version, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(project_id) DO UPDATE SET "
                "published_version = excluded.published_version, pending_version = excluded.pending_version, "
                "updated_at = excluded.updated_at",
                (project_id, parent, next_version, now),
            )
            connection.execute("COMMIT")
            return BeginResult("ok", next_version, parent, next_version)
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    def commit_publish(
        self, project_id: str, version: int, *, now: str, keep: int, audit: ConfigAuditEntry | None = None
    ) -> HeadState:
        """提交 pending 版本。`audit` 非空时，审计行与“置 published / 更新 head / 修剪”**同一事务**写入（CR-009）：
        审计写失败 → 整个事务回滚、异常上抛（版本仍为 pending，由调用方 abort 并还原文件）。"""
        from ib.ledger.config_audit import insert_audit_row

        connection = self._begin()
        try:
            cur = connection.execute(
                "UPDATE config_versions SET status = 'published' "
                "WHERE project_id = ? AND version = ? AND status = 'pending'",
                (project_id, int(version)),
            )
            if cur.rowcount != 1:
                raise ConflictError("待提交的配置版本不存在或不处于 pending 状态")
            connection.execute(
                "UPDATE config_head SET published_version = ?, pending_version = NULL, updated_at = ? "
                "WHERE project_id = ? AND pending_version = ?",
                (int(version), now, project_id, int(version)),
            )
            if audit is not None:
                insert_audit_row(connection, audit)
            self._prune(connection, project_id, int(version), max(1, int(keep)))
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        return self.head(project_id)

    @staticmethod
    def _prune(connection: sqlite3.Connection, project_id: str, head_version: int, keep: int) -> int:
        keep_rows = connection.execute(
            "SELECT version FROM config_versions WHERE project_id = ? AND status = 'published' "
            "ORDER BY version DESC LIMIT ?",
            (project_id, keep),
        ).fetchall()
        keep_set = {int(r[0]) for r in keep_rows} | {head_version}
        pend = connection.execute(
            "SELECT pending_version FROM config_head WHERE project_id = ?", (project_id,)
        ).fetchone()
        if pend and pend[0] is not None:
            keep_set.add(int(pend[0]))
        rows = connection.execute(
            "SELECT version FROM config_versions WHERE project_id = ?", (project_id,)
        ).fetchall()
        removed = 0
        for (v,) in rows:
            if int(v) not in keep_set:
                connection.execute(
                    "DELETE FROM config_versions WHERE project_id = ? AND version = ?", (project_id, int(v))
                )
                removed += 1
        return removed

    def abort_publish(self, project_id: str, version: int, *, reason_code: str, now: str) -> bool:
        connection = self._begin()
        try:
            row = connection.execute(
                "SELECT summary FROM config_versions WHERE project_id = ? AND version = ?",
                (project_id, int(version)),
            ).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                return False
            connection.execute(
                "UPDATE config_versions SET status = 'aborted', summary = ? "
                "WHERE project_id = ? AND version = ? AND status IN ('pending', 'aborted')",
                (f"[aborted:{reason_code[:40]}] {row[0]}"[:200], project_id, int(version)),
            )
            cur = connection.execute(
                "UPDATE config_head SET pending_version = NULL, updated_at = ? "
                "WHERE project_id = ? AND pending_version = ?",
                (now, project_id, int(version)),
            )
            connection.execute("COMMIT")
            return bool(cur.rowcount)
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    def claim_stale_pending(self, project_id: str, *, now: str, stale_after_s: float) -> int | None:
        """CAS：把陈旧 pending 行标 aborted（仅一个调用方成功）；head.pending 仍保留到 `abort_publish` 清除。"""
        connection = self._begin()
        try:
            head = connection.execute(
                "SELECT pending_version FROM config_head WHERE project_id = ?", (project_id,)
            ).fetchone()
            if head is None or head[0] is None:
                connection.execute("ROLLBACK")
                return None
            version = int(head[0])
            row = connection.execute(
                "SELECT created_at FROM config_versions WHERE project_id = ? AND version = ? AND status = 'pending'",
                (project_id, version),
            ).fetchone()
            if row is None or _age_s(now, row[0]) < float(stale_after_s):
                connection.execute("ROLLBACK")
                return None
            cur = connection.execute(
                "UPDATE config_versions SET status = 'aborted' "
                "WHERE project_id = ? AND version = ? AND status = 'pending'",
                (project_id, version),
            )
            connection.execute("COMMIT")
            return version if cur.rowcount == 1 else None
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    def prune_all(self, *, keep: int) -> int:
        connection = self._begin()
        try:
            projects = [r[0] for r in connection.execute("SELECT DISTINCT project_id FROM config_versions")]
            removed = 0
            for pid in projects:
                head = connection.execute(
                    "SELECT published_version FROM config_head WHERE project_id = ?", (pid,)
                ).fetchone()
                removed += self._prune(connection, pid, int(head[0]) if head else 0, max(1, int(keep)))
            connection.execute("COMMIT")
            return removed
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise


class MemoryConfigVersionStore:
    """`ConfigVersionStore` 的内存替身（离线 / 内存态存储；同一套语义）。"""

    def __init__(self, audit_sink: Any = None) -> None:
        self._lock = threading.RLock()
        self._rows: dict[str, dict[int, tuple[VersionRecord, str]]] = {}
        self._heads: dict[str, HeadState] = {}
        self._audit_sink = audit_sink

    def head(self, project_id: str) -> HeadState:
        with self._lock:
            return self._heads.get(project_id, HeadState(project_id, 0, None, ""))

    def get_version(self, project_id: str, version: int) -> tuple[VersionRecord, ConfigSnapshot] | None:
        with self._lock:
            item = self._rows.get(project_id, {}).get(int(version))
        if item is None or item[0].status != "published":
            return None
        return item[0], _versioning().snapshot_from_json(item[1])

    def list_versions(
        self, project_id: str, *, limit: int, before_version: int | None
    ) -> tuple[VersionRecord, ...]:
        with self._lock:
            recs = [r for r, _ in self._rows.get(project_id, {}).values() if r.status == "published"]
        recs.sort(key=lambda r: -r.version)
        if before_version is not None:
            recs = [r for r in recs if r.version < int(before_version)]
        return tuple(recs[: max(0, min(int(limit), 500))])

    def begin_publish(
        self,
        project_id: str,
        *,
        base_version: int,
        new: NewVersion,
        snapshot: ConfigSnapshot,
        extra_baseline: ConfigSnapshot | None,
        now: str,
        stale_after_s: float,
    ) -> BeginResult:
        vz = _versioning()
        with self._lock:
            head = self._heads.get(project_id, HeadState(project_id, 0, None, ""))
            if head.pending_version is not None:
                return BeginResult("busy", None, head.published_version, head.pending_version)
            if head.published_version != int(base_version):
                return BeginResult("stale_base", None, head.published_version, None)
            rows = self._rows.setdefault(project_id, {})
            nxt = (max(rows) if rows else 0) + 1
            parent = head.published_version
            if extra_baseline is not None and head.published_version == 0:
                bj = vz.snapshot_to_json(extra_baseline)
                rows[nxt] = (
                    VersionRecord(
                        project_id, nxt, 0, "published", "baseline", None, "system", now, "升级前基线",
                        vz.manifest_hash(extra_baseline), len(bj.encode("utf-8")),
                    ),
                    bj,
                )
                parent = nxt
                nxt += 1
            sj = vz.snapshot_to_json(snapshot)
            rows[nxt] = (
                VersionRecord(
                    project_id, nxt, parent, "pending", new.kind, new.rolled_back_to, new.actor, now,
                    new.summary[:200], new.manifest_hash, len(sj.encode("utf-8")),
                ),
                sj,
            )
            self._heads[project_id] = HeadState(project_id, parent, nxt, now)
            return BeginResult("ok", nxt, parent, nxt)

    def commit_publish(
        self, project_id: str, version: int, *, now: str, keep: int, audit: ConfigAuditEntry | None = None
    ) -> HeadState:
        with self._lock:
            rows = self._rows.get(project_id, {})
            item = rows.get(int(version))
            if item is None or item[0].status != "pending":
                raise ConflictError("待提交的配置版本不存在或不处于 pending 状态")
            if audit is not None:
                # 审计先于状态翻转写入：写失败 → 抛出且版本仍为 pending（与 SQLite 实现的整体回滚等价）。
                # `audit_sink` 由组合根注入（同一份内存审计存储）；独立使用（无 sink）时没有可写的审计后端。
                if self._audit_sink is None:
                    raise DependencyUnavailableError("未配置审计后端，拒绝提交带审计的发布", dependency="ledger")
                self._audit_sink.record(audit)
            rows[int(version)] = (replace(item[0], status="published"), item[1])
            head = self._heads[project_id]
            if head.pending_version == int(version):
                self._heads[project_id] = HeadState(project_id, int(version), None, now)
            self._prune(project_id, int(version), max(1, int(keep)))
            return self._heads[project_id]

    def _prune(self, project_id: str, head_version: int, keep: int) -> int:
        rows = self._rows.get(project_id, {})
        pub = sorted((v for v, (r, _) in rows.items() if r.status == "published"), reverse=True)[:keep]
        keep_set = set(pub) | {head_version}
        pend = self._heads.get(project_id)
        if pend and pend.pending_version is not None:
            keep_set.add(pend.pending_version)
        gone = [v for v in rows if v not in keep_set]
        for v in gone:
            del rows[v]
        return len(gone)

    def abort_publish(self, project_id: str, version: int, *, reason_code: str, now: str) -> bool:
        with self._lock:
            rows = self._rows.get(project_id, {})
            item = rows.get(int(version))
            if item is None:
                return False
            if item[0].status in ("pending", "aborted"):
                rows[int(version)] = (
                    replace(item[0], status="aborted", summary=f"[aborted:{reason_code[:40]}] {item[0].summary}"[:200]),
                    item[1],
                )
            head = self._heads.get(project_id)
            if head and head.pending_version == int(version):
                self._heads[project_id] = HeadState(project_id, head.published_version, None, now)
                return True
            return False

    def claim_stale_pending(self, project_id: str, *, now: str, stale_after_s: float) -> int | None:
        with self._lock:
            head = self._heads.get(project_id)
            if head is None or head.pending_version is None:
                return None
            item = self._rows.get(project_id, {}).get(head.pending_version)
            if item is None or item[0].status != "pending" or _age_s(now, item[0].created_at) < float(stale_after_s):
                return None
            self._rows[project_id][head.pending_version] = (replace(item[0], status="aborted"), item[1])
            return head.pending_version

    def prune_all(self, *, keep: int) -> int:
        with self._lock:
            return sum(
                self._prune(pid, self._heads.get(pid, HeadState(pid, 0, None, "")).published_version, max(1, int(keep)))
                for pid in list(self._rows)
            )


# --------------------------------------------------------------------------- #
# 草稿副本
# --------------------------------------------------------------------------- #


def _check_draft(label: str, payload_json: str) -> int:
    size = len(payload_json.encode("utf-8"))
    if not (1 <= len(label.strip()) <= 60):
        raise ValidationError("草稿名称须为 1..60 字符", field="label")
    if size > DRAFT_MAX_BYTES:
        raise ValidationError("草稿超过 1 MiB 上限", field="payload")
    return size


class SqliteConfigDraftStore(_SqliteBase):
    def save(
        self, project_id: str, owner: str, *, label: str, base_version: int, payload_json: str, now: str,
        max_per_owner: int,
    ) -> DraftRecord:
        size = _check_draft(label, payload_json)
        connection = self._begin()
        try:
            n = connection.execute(
                "SELECT COUNT(*) FROM config_drafts WHERE project_id = ? AND owner = ?", (project_id, owner)
            ).fetchone()[0]
            if int(n) >= int(max_per_owner):
                raise ValidationError("草稿数量已达上限，请先删除旧草稿", field="draft_quota")
            draft_id = uuid.uuid4().hex
            connection.execute(
                "INSERT INTO config_drafts (draft_id, project_id, owner, label, base_version, payload_json, "
                "payload_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (draft_id, project_id, owner, label.strip(), int(base_version), payload_json, size, now),
            )
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        return DraftRecord(draft_id, project_id, owner, label.strip(), int(base_version), now, size)

    def list(self, project_id: str, owner: str) -> tuple[DraftRecord, ...]:
        rows = self._conn().execute(
            "SELECT draft_id, project_id, owner, label, base_version, created_at, payload_bytes "
            "FROM config_drafts WHERE project_id = ? AND owner = ? ORDER BY created_at DESC, draft_id",
            (project_id, owner),
        ).fetchall()
        return tuple(DraftRecord(r[0], r[1], r[2], r[3], int(r[4]), r[5], int(r[6])) for r in rows)

    def load(self, project_id: str, owner: str, draft_id: str) -> tuple[DraftRecord, str] | None:
        r = self._conn().execute(
            "SELECT draft_id, project_id, owner, label, base_version, created_at, payload_bytes, payload_json "
            "FROM config_drafts WHERE project_id = ? AND owner = ? AND draft_id = ?",
            (project_id, owner, draft_id),
        ).fetchone()
        if r is None:
            return None
        return DraftRecord(r[0], r[1], r[2], r[3], int(r[4]), r[5], int(r[6])), r[7]

    def delete(self, project_id: str, owner: str, draft_id: str) -> bool:
        cur = self._conn().execute(
            "DELETE FROM config_drafts WHERE project_id = ? AND owner = ? AND draft_id = ?",
            (project_id, owner, draft_id),
        )
        return cur.rowcount == 1

    def purge_older_than(self, cutoff_iso: str) -> int:
        cur = self._conn().execute("DELETE FROM config_drafts WHERE created_at < ?", (cutoff_iso,))
        return int(cur.rowcount or 0)


class MemoryConfigDraftStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rows: dict[str, tuple[DraftRecord, str]] = {}

    def save(
        self, project_id: str, owner: str, *, label: str, base_version: int, payload_json: str, now: str,
        max_per_owner: int,
    ) -> DraftRecord:
        size = _check_draft(label, payload_json)
        with self._lock:
            mine = [r for r, _ in self._rows.values() if r.project_id == project_id and r.owner == owner]
            if len(mine) >= int(max_per_owner):
                raise ValidationError("草稿数量已达上限，请先删除旧草稿", field="draft_quota")
            rec = DraftRecord(uuid.uuid4().hex, project_id, owner, label.strip(), int(base_version), now, size)
            self._rows[rec.draft_id] = (rec, payload_json)
            return rec

    def list(self, project_id: str, owner: str) -> tuple[DraftRecord, ...]:
        with self._lock:
            mine = [r for r, _ in self._rows.values() if r.project_id == project_id and r.owner == owner]
        return tuple(sorted(mine, key=lambda r: (r.created_at, r.draft_id), reverse=True))

    def load(self, project_id: str, owner: str, draft_id: str) -> tuple[DraftRecord, str] | None:
        with self._lock:
            item = self._rows.get(draft_id)
        if item is None or item[0].project_id != project_id or item[0].owner != owner:
            return None
        return item

    def delete(self, project_id: str, owner: str, draft_id: str) -> bool:
        with self._lock:
            item = self._rows.get(draft_id)
            if item is None or item[0].project_id != project_id or item[0].owner != owner:
                return False
            del self._rows[draft_id]
            return True

    def purge_older_than(self, cutoff_iso: str) -> int:
        with self._lock:
            gone = [k for k, (r, _) in self._rows.items() if r.created_at < cutoff_iso]
            for k in gone:
                del self._rows[k]
            return len(gone)


# --------------------------------------------------------------------------- #
# Builder 评审缓存
# --------------------------------------------------------------------------- #


class SqliteBuilderEvalCache(_SqliteBase):
    def get(self, cache_key: str) -> str | None:
        r = self._conn().execute(
            "SELECT result_json FROM builder_eval_cache WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return None if r is None else r[0]

    def put(self, cache_key: str, *, rubric_version: str, result_json: str, now: str) -> None:
        self._conn().execute(
            "INSERT INTO builder_eval_cache (cache_key, rubric_version, result_json, created_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(cache_key) DO NOTHING",  # 先写者赢：缓存期内同输入同分
            (cache_key, rubric_version, result_json, now),
        )

    def purge(self, *, keep: int, older_than_iso: str) -> int:
        connection = self._begin()
        try:
            a = connection.execute(
                "DELETE FROM builder_eval_cache WHERE created_at < ?", (older_than_iso,)
            ).rowcount
            b = connection.execute(
                "DELETE FROM builder_eval_cache WHERE cache_key NOT IN ("
                "SELECT cache_key FROM builder_eval_cache ORDER BY created_at DESC, cache_key LIMIT ?)",
                (max(0, int(keep)),),
            ).rowcount
            connection.execute("COMMIT")
            return int(a or 0) + int(b or 0)
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise


class MemoryBuilderEvalCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rows: dict[str, tuple[str, str, str]] = {}

    def get(self, cache_key: str) -> str | None:
        with self._lock:
            item = self._rows.get(cache_key)
        return None if item is None else item[1]

    def put(self, cache_key: str, *, rubric_version: str, result_json: str, now: str) -> None:
        with self._lock:
            self._rows.setdefault(cache_key, (rubric_version, result_json, now))

    def purge(self, *, keep: int, older_than_iso: str) -> int:
        with self._lock:
            fresh = {k: v for k, v in self._rows.items() if v[2] >= older_than_iso}
            ordered = sorted(fresh.items(), key=lambda kv: (kv[1][2], kv[0]), reverse=True)[: max(0, int(keep))]
            removed = len(self._rows) - len(ordered)
            self._rows = dict(ordered)
            return removed


# --------------------------------------------------------------------------- #
# 工厂（组合根单点调用）
# --------------------------------------------------------------------------- #


def build_config_version_store(
    cfg: Any, *, ledger_path: str, file_backed: bool = True, audit_sink: Any = None
) -> Any:
    """`file_backed=False`（定义 / 提示词存储为内存态）或台账为内存后端 → 内存替身；否则 SQLite（与台账同文件）。

    `audit_sink`：内存替身提交带审计的发布时写入的审计存储（SQLite 实现与审计表同库同事务，不需要它）。
    """
    if not file_backed or getattr(cfg, "ledger_backend", "sqlite") == "memory":
        return MemoryConfigVersionStore(audit_sink=audit_sink)
    return SqliteConfigVersionStore(ledger_path)


def build_config_draft_store(cfg: Any, *, ledger_path: str) -> Any:
    if getattr(cfg, "ledger_backend", "sqlite") == "memory":
        return MemoryConfigDraftStore()
    return SqliteConfigDraftStore(ledger_path)


def build_builder_eval_cache(cfg: Any, *, ledger_path: str) -> Any:
    if getattr(cfg, "ledger_backend", "sqlite") == "memory":
        return MemoryBuilderEvalCache()
    return SqliteBuilderEvalCache(ledger_path)
