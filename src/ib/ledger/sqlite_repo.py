"""
@module MOD-IB-11（生产实现）
@implements IFC-IB-120~131 + RebuildJobStore（SQLite 落地）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04, MOD-IB-11（schema / 状态机）
@author software-developer

SQLite 台账（ADR-10；tech_stack §3）。

三个关键实现决定：
  1. **线程局部连接**：Waitress 线程池 + worker 线程并发访问同一 SQLite 文件，
     每线程一条连接（开 `WAL` + `busy_timeout`），避免跨线程共享连接的状态错乱；
  2. **认领必须是单条条件 UPDATE**：先 `SELECT` 再 `UPDATE` 在并发下会双认领（ADR-10 明确禁止）；
  3. **多语句写操作走 `BEGIN IMMEDIATE`**：显式取写锁，避免「读事务升级为写事务」时的
     `SQLITE_BUSY` 死锁（SQLite 的经典陷阱）。

**所有读写都带 `project_id` 条件**（FM-3）：删除/更新绝不只凭 `doc_id`。
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import (
    ChunkImageRecord,
    ChunkRecord,
    DependencyUnavailableError,
    DocStatus,
    DocumentRecord,
    KbRecord,
    NotFoundError,
    ProjectRecord,
    Scope,
    ScopeViolationError,
    StartupError,
)
from ib.ledger import (
    TERMINAL_REBUILD_STATES,
    RebuildJobRow,
    _assert_transition,
    assert_no_half_state,
)
from ib.ledger.schema import ensure_schema, missing_columns

__all__ = ["SqliteLedgerRepository"]

#: `documents` 表列顺序（与 `_row_to_document` 的索引一一对应；集中定义避免漂移）。
_DOC_COLUMNS = (
    "doc_id",
    "project_id",
    "kb_id",
    "doc_name",
    "ext",
    "size_bytes",
    "content_sha256",
    "blob_ref",
    "status",
    "error_code",
    "chunk_count",
    "indexed_collection_version",
    "target_collection_version",
    "lease_owner",
    "lease_expires_at",
    "created_at",
    "updated_at",
)

_CHUNK_COLUMNS = (
    "chunk_id",
    "doc_id",
    "project_id",
    "kb_id",
    "chunk_index",
    "content_hash",
    "locator",
    "source_kind",
    "page_or_section",
    "indexed_model",
    "indexed_dim",
)

_JOB_COLUMNS = (
    "job_id",
    "project_id",
    "from_version",
    "to_version",
    "target_collection",
    "doc_count",
    "state",
    "lease_owner",
    "lease_expires_at",
    "created_at",
    "updated_at",
)

#: R2（M-02）`chunk_image` 表列顺序（与 `_row_to_chunk_image` 索引一一对应）。
_IMAGE_COLUMNS = (
    "image_row_id",
    "project_id",
    "kb_id",
    "doc_id",
    "page_or_section",
    "image_id",
    "source_kind",
    "locator",
    "blob_ref",
    "doc_name",
    "created_at",
)


def image_row_id(
    project_id: str, kb_id: str, doc_id: str, page_or_section: str, image_id: str
) -> str:
    """幂等键的物化形式（IFC-IB-279）：定长拼接，与 `chunks.chunk_id` 的做法同构。

    为什么不用自增/随机主键：主键一旦非确定，重跑就会**新增行**而非覆盖行，
    「幂等」只能在应用层靠「先删后写」补救 —— 而先删后写若中途失败，就会留下空窗。
    确定性主键让「同一关联 = 同一行」成为**表结构层面**的事实。
    分隔符用 `\\x1f`（单元分隔符）：不会出现在 id / 页码里，避免拼接歧义。
    """
    return "\x1f".join((project_id, kb_id, doc_id, page_or_section, image_id))


def _image_row(record: ChunkImageRecord) -> tuple[Any, ...]:
    return (
        image_row_id(
            record.project_id,
            record.kb_id,
            record.doc_id,
            record.page_or_section,
            record.image_id,
        ),
        record.project_id,
        record.kb_id,
        record.doc_id,
        record.page_or_section,
        record.image_id,
        record.source_kind,
        record.locator,
        record.blob_ref,
        record.doc_name,
        record.created_at,
    )


#: SQLite 单条语句的变量上限（默认 999）。`kb_id IN (...)` 超过它就必须改查询策略。
_SQLITE_MAX_VARIABLES = 999


class SqliteLedgerRepository:
    """`LedgerRepository` + `RebuildJobStore` 的 SQLite 实现。

    `path` 为 `":memory:"` 时使用进程内共享缓存（`file::memory:?cache=shared`），
    以便多线程共用同一个内存库（自测便利；生产一律用文件路径）。
    """

    def __init__(self, path: str, *, busy_timeout_ms: int = 5000) -> None:
        self._path = path or ":memory:"
        self._busy_timeout_ms = busy_timeout_ms
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()
        if self._path != ":memory:":
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._bootstrap()

    # ------------------------------------------------------------------ #
    # 连接管理
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        # `isolation_level=None` = 自动提交：显式 `BEGIN IMMEDIATE` 才不会与 Python 的隐式
        # 事务管理叠加（叠加会得到 "cannot start a transaction within a transaction"）。
        if self._path == ":memory:":
            # 共享缓存内存库：多线程连接同一库（生产不用，仅供离线自测）
            uri = "file:ib_ledger_mem?mode=memory&cache=shared"
            connection = sqlite3.connect(
                uri,
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
        # 连接级 PRAGMA（每条新连接都要设置一次）：busy_timeout / synchronous / foreign_keys。
        # 刻意**不**在此处执行 `PRAGMA journal_mode=WAL`：它是数据库级持久设置，
        # 已在 `ensure_schema`（`schema.PRAGMA_DB_LEVEL`）初始化时落地一次；每条新连接
        # 重跑会冗余地去抢排它锁，是「worker 首请求 30~90s 阻塞」的根因（见部署报告）。
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _conn(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            try:
                connection = self._connect()
            except sqlite3.Error as exc:
                raise DependencyUnavailableError(
                    f"台账连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        """建表 + PRAGMA + 结构校验（缺失列即启动失败，不带着残缺结构运行）。"""
        connection = self._conn()
        try:
            ensure_schema(connection)
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"台账初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_columns(connection)
        if missing:
            # **不回显表结构细节之外的任何数据**；键名级信息足够定位迁移缺失。
            raise StartupError(
                "台账表结构不完整（缺失列）：" + "; ".join(f"{table}:{','.join(cols)}" for table, cols in missing.items())
            )

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        """写事务：`BEGIN IMMEDIATE` 显式取写锁，异常回滚。"""
        connection = self._conn()
        try:
            connection.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            raise DependencyUnavailableError(
                f"台账写锁获取失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    # ------------------------------------------------------------------ #
    # 播种（组合根 / 自测；非端口方法）
    # ------------------------------------------------------------------ #

    def upsert_project(self, project: ProjectRecord) -> None:
        with self._write() as connection:
            connection.execute(
                """
                INSERT INTO projects (project_id, name, active_collection_version, embedding_model_id, dim, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name=excluded.name,
                    embedding_model_id=excluded.embedding_model_id,
                    dim=excluded.dim
                """,
                (
                    project.project_id,
                    project.name,
                    project.active_collection_version,
                    project.embedding_model_id,
                    project.dim,
                    project.created_at or utc_now_iso(),
                ),
            )

    def get_project(self, project_id: str) -> ProjectRecord | None:
        row = self._conn().execute(
            "SELECT project_id, name, active_collection_version, embedding_model_id, dim, created_at "
            "FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        return ProjectRecord(
            project_id=row[0],
            name=row[1],
            active_collection_version=row[2],
            embedding_model_id=row[3],
            dim=int(row[4]),
            created_at=row[5],
        )

    def upsert_kb(self, kb: KbRecord) -> None:
        with self._write() as connection:
            if connection.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", (kb.project_id,)
            ).fetchone() is None:
                raise ScopeViolationError("知识库所属项目未登记")
            connection.execute(
                """
                INSERT INTO kbs (kb_id, project_id, name, created_at) VALUES (?, ?, ?, ?)
                ON CONFLICT(kb_id) DO UPDATE SET name=excluded.name
                """,
                (kb.kb_id, kb.project_id, kb.name, kb.created_at or utc_now_iso()),
            )

    def list_kbs(self, project_id: str) -> list[KbRecord]:
        rows = self._conn().execute(
            "SELECT kb_id, project_id, name, created_at FROM kbs WHERE project_id = ? ORDER BY kb_id",
            (project_id,),
        ).fetchall()
        return [KbRecord(kb_id=r[0], project_id=r[1], name=r[2], created_at=r[3]) for r in rows]

    # ------------------------------------------------------------------ #
    # 归属断言与作用域
    # ------------------------------------------------------------------ #

    def assert_kb_in_project(self, project_id: str, kb_id: str) -> None:
        row = self._conn().execute(
            "SELECT 1 FROM kbs WHERE kb_id = ? AND project_id = ?", (kb_id, project_id)
        ).fetchone()
        if row is None:
            raise ScopeViolationError("知识库不属于该项目（归属断言失败）")

    @staticmethod
    def _scope_clause(scope: Scope, *, prefix: str = "AND") -> tuple[str, list[Any]]:
        """构造 `project_id`（+ 可选 `kb_id IN (...)`) 子句 —— **全类唯一的 scope 下推点**。

        FM-3 的实现落点：任何读/写/删都必须经此拼装，避免某个方法漏掉 `project_id`。
        """
        clauses = ["project_id = ?"]
        params: list[Any] = [scope.project_id]
        if scope.kb_ids is not None:
            if len(scope.kb_ids) >= _SQLITE_MAX_VARIABLES:
                # 显式拒绝而非拼出必然报错的 SQL：超限说明「按 kb 列表过滤」这一形状本身不适用，
                # 应改用 project 级 scope（`kb_ids=None`）或改查询策略。
                raise ScopeViolationError(
                    f"scope.kb_ids 数量 {len(scope.kb_ids)} 超出单条 SQL 变量上限；"
                    "请改用项目级 scope（kb_ids=None）"
                )
            placeholders = ",".join("?" for _ in scope.kb_ids)
            clauses.append(f"kb_id IN ({placeholders})")
            params.extend(scope.kb_ids)
        return f" {prefix} " + " AND ".join(clauses), params

    # ------------------------------------------------------------------ #
    # 文档 CRUD
    # ------------------------------------------------------------------ #

    def create_document(
        self,
        scope: Scope,
        doc_name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        blob_ref: str | None,
    ) -> DocumentRecord:
        kb_id = scope.kb_ids[0] if scope.kb_ids else ""
        self.assert_kb_in_project(scope.project_id, kb_id)
        doc_id = uuid.uuid4().hex
        now = utc_now_iso()
        with self._write() as connection:
            connection.execute(
                f"INSERT INTO documents ({','.join(_DOC_COLUMNS)}) VALUES ({','.join('?' for _ in _DOC_COLUMNS)})",
                (
                    doc_id,
                    scope.project_id,
                    kb_id,
                    doc_name,
                    ext,
                    int(size_bytes),
                    content_sha256,
                    blob_ref,
                    "pending",
                    None,
                    0,
                    None,
                    None,
                    None,
                    None,
                    now,
                    now,
                ),
            )
        record = self.get_document(scope, doc_id)
        if record is None:  # pragma: no cover - 刚插入即读不到 = 台账不可信
            raise DependencyUnavailableError("新建文档后立即读取失败（台账不可信）", dependency="ledger")
        return record

    def get_document(self, scope: Scope, doc_id: str) -> DocumentRecord | None:
        clause, params = self._scope_clause(scope)
        row = self._conn().execute(
            f"SELECT {','.join(_DOC_COLUMNS)} FROM documents WHERE doc_id = ?{clause}",
            [doc_id, *params],
        ).fetchone()
        return _row_to_document(row) if row is not None else None

    def list_documents(
        self, scope: Scope, *, page: int, page_size: int, status: DocStatus | None
    ) -> tuple[list[DocumentRecord], int]:
        clause, params = self._scope_clause(scope)
        where = [clause.strip()[4:]]  # 去掉前导 "AND "
        values = list(params)
        if status is not None:
            where.append("status = ?")
            values.append(str(status))
        where_sql = " WHERE " + " AND ".join(where)
        connection = self._conn()
        total = int(
            connection.execute(f"SELECT COUNT(*) FROM documents{where_sql}", values).fetchone()[0]
        )
        limit = max(1, int(page_size))
        offset = max(0, (max(1, int(page)) - 1) * limit)
        rows = connection.execute(
            f"SELECT {','.join(_DOC_COLUMNS)} FROM documents{where_sql} "
            "ORDER BY created_at DESC, doc_id DESC LIMIT ? OFFSET ?",
            [*values, limit, offset],
        ).fetchall()
        return [_row_to_document(row) for row in rows], total

    def set_status(
        self, scope: Scope, doc_id: str, status: DocStatus, *, error_code: str | None
    ) -> None:
        target = str(status)
        clause, params = self._scope_clause(scope)
        # 读 + 判 + 写在同一写事务内完成：状态判定与更新之间不能有窗口，
        # 否则并发 worker 会各自基于旧状态通过校验（TOCTOU）。
        with self._write() as connection:
            current = connection.execute(
                f"SELECT status FROM documents WHERE doc_id = ?{clause}", [doc_id, *params]
            ).fetchone()
            if current is None:
                raise NotFoundError("文档不存在或不在当前作用域内")
            _assert_transition(current[0], target, doc_id=doc_id)
            connection.execute(
                f"UPDATE documents SET status = ?, error_code = ?, updated_at = ?,"
                f" lease_owner = CASE WHEN ? = 'parsing' THEN lease_owner ELSE NULL END,"
                f" lease_expires_at = CASE WHEN ? = 'parsing' THEN lease_expires_at ELSE NULL END"
                f" WHERE doc_id = ?{clause}",
                [target, error_code, utc_now_iso(), target, target, doc_id, *params],
            )

    def mark_indexed(
        self, scope: Scope, doc_id: str, collection_version: str, chunk_count: int
    ) -> None:
        clause, params = self._scope_clause(scope)
        with self._write() as connection:
            current = connection.execute(
                f"SELECT status FROM documents WHERE doc_id = ?{clause}", [doc_id, *params]
            ).fetchone()
            if current is None:
                raise NotFoundError("文档不存在或不在当前作用域内")
            _assert_transition(current[0], "indexed", doc_id=doc_id)
            connection.execute(
                "UPDATE documents SET status = 'indexed', error_code = NULL, chunk_count = ?,"
                " indexed_collection_version = ?, target_collection_version = NULL,"
                " lease_owner = NULL, lease_expires_at = NULL, updated_at = ?"
                f" WHERE doc_id = ?{clause}",
                [int(chunk_count), collection_version, utc_now_iso(), doc_id, *params],
            )
        record = self.get_document(scope, doc_id)
        if record is not None:
            assert_no_half_state(record)

    def mark_deleted(self, scope: Scope, doc_id: str) -> None:
        clause, params = self._scope_clause(scope)
        with self._write() as connection:
            cursor = connection.execute(
                f"DELETE FROM documents WHERE doc_id = ?{clause}", [doc_id, *params]
            )
            if cursor.rowcount <= 0:
                raise NotFoundError("文档不存在或不在当前作用域内")

    # ------------------------------------------------------------------ #
    # 租约（ADR-10）
    # ------------------------------------------------------------------ #

    def claim_pending(self, lease_owner: str, lease_seconds: int, limit: int) -> list[DocumentRecord]:
        """认领（ADR-10）：**条件 UPDATE**，且「选候选」与「置位」在同一写事务内。

        为什么这样写就够安全：`BEGIN IMMEDIATE` 在整个事务期间持有 RESERVED 写锁，
        并发的第二个认领者会在 `BEGIN` 处等待（`busy_timeout` 内），因此「先选后写」不会
        双认领；而它与「非事务的先查后写」的区别正是**写锁的持有范围**。
        置位条件里仍保留 `status='pending'` 判定，作为不依赖锁语义的第二道保险。
        """
        if limit <= 0:
            return []
        now = utc_now_iso()
        expires = iso_plus_seconds(lease_seconds)
        with self._write() as connection:
            candidates = connection.execute(
                """
                SELECT doc_id FROM documents
                 WHERE status = 'pending'
                   AND (lease_expires_at IS NULL OR lease_expires_at < ?)
                 ORDER BY created_at, doc_id
                 LIMIT ?
                """,
                (now, int(limit)),
            ).fetchall()
            ids = [str(row[0]) for row in candidates]
            if not ids:
                return []
            placeholders = ",".join("?" for _ in ids)
            connection.execute(
                f"UPDATE documents SET status = 'parsing', lease_owner = ?, lease_expires_at = ?,"
                f" updated_at = ? WHERE doc_id IN ({placeholders}) AND status = 'pending'",
                [lease_owner, expires, now, *ids],
            )
            rows = connection.execute(
                f"SELECT {','.join(_DOC_COLUMNS)} FROM documents WHERE doc_id IN ({placeholders})"
                " ORDER BY created_at, doc_id",
                ids,
            ).fetchall()
        return [_row_to_document(row) for row in rows]

    def renew_lease(self, doc_id: str, lease_owner: str, lease_seconds: int) -> bool:
        with self._write() as connection:
            cursor = connection.execute(
                "UPDATE documents SET lease_expires_at = ?, updated_at = ? "
                "WHERE doc_id = ? AND lease_owner = ?",
                (iso_plus_seconds(lease_seconds), utc_now_iso(), doc_id, lease_owner),
            )
            return cursor.rowcount > 0

    def reap_expired_leases(self, now: str) -> int:
        """回收过期租约：文档 `parsing -> pending`，重建任务 `running -> planned`（§6.3）。"""
        with self._write() as connection:
            reaped = connection.execute(
                "UPDATE documents SET status = 'pending', lease_owner = NULL, lease_expires_at = NULL,"
                " updated_at = ? WHERE status = 'parsing' AND lease_expires_at IS NOT NULL"
                " AND lease_expires_at < ?",
                (utc_now_iso(), now),
            ).rowcount
            reaped += connection.execute(
                "UPDATE rebuild_jobs SET state = 'planned', lease_owner = NULL, lease_expires_at = NULL,"
                " updated_at = ? WHERE state = 'running' AND lease_expires_at IS NOT NULL"
                " AND lease_expires_at < ?",
                (utc_now_iso(), now),
            ).rowcount
        return int(reaped)

    # ------------------------------------------------------------------ #
    # collection 版本
    # ------------------------------------------------------------------ #

    def active_collection_version(self, project_id: str) -> str:
        row = self._conn().execute(
            "SELECT active_collection_version FROM projects WHERE project_id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise StartupError("项目未登记（请检查项目配置）")
        return str(row[0])

    def activate_collection_version(self, project_id: str, version: str) -> None:
        """**原子切换**（ADR-05）：单条 UPDATE 即「切换瞬间」，无混合读窗口。"""
        with self._write() as connection:
            cursor = connection.execute(
                "UPDATE projects SET active_collection_version = ? WHERE project_id = ?",
                (version, project_id),
            )
            if cursor.rowcount <= 0:
                raise StartupError("项目未登记（请检查项目配置）")

    # ------------------------------------------------------------------ #
    # 块元数据
    # ------------------------------------------------------------------ #

    def upsert_chunks(self, scope: Scope, doc_id: str, chunks: Sequence[ChunkRecord]) -> int:
        """先删后写（IFC-IB-131 组内扩展，见 deviation D-07）。"""
        clause, params = self._scope_clause(scope)
        with self._write() as connection:
            exists = connection.execute(
                f"SELECT 1 FROM documents WHERE doc_id = ?{clause}", [doc_id, *params]
            ).fetchone()
            if exists is None:
                raise NotFoundError("文档不存在或不在当前作用域内")
            connection.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            connection.executemany(
                f"INSERT INTO chunks ({','.join(_CHUNK_COLUMNS)}) VALUES ({','.join('?' for _ in _CHUNK_COLUMNS)})",
                [
                    (
                        chunk.chunk_id,
                        chunk.doc_id,
                        chunk.project_id,
                        chunk.kb_id,
                        int(chunk.chunk_index),
                        chunk.content_hash,
                        chunk.locator,
                        chunk.source_kind,
                        chunk.page_or_section,
                        chunk.indexed_model,
                        int(chunk.indexed_dim),
                    )
                    for chunk in chunks
                ],
            )
        return len(chunks)

    def list_chunks(self, scope: Scope, doc_id: str) -> list[ChunkRecord]:
        clause, params = self._scope_clause(scope)
        rows = self._conn().execute(
            f"SELECT {','.join(_CHUNK_COLUMNS)} FROM chunks WHERE doc_id = ?{clause}"
            " ORDER BY chunk_index",
            [doc_id, *params],
        ).fetchall()
        return [_row_to_chunk(row) for row in rows]

    def list_orphan_doc_ids(self, project_id: str, existing: list[str]) -> list[str]:
        """台账存在而向量侧不存在的文档 id（删除重放对账）。

        刻意**不用** `NOT IN (?)` 分批：分批的 `NOT IN` 会把「在后续批次里」的文档误判为孤儿
        （每批只看得到本批）。改为「取全量 + 内存求差」，正确性优先；
        `documents` 量级是「每项目文档数」，不是 chunk 量级，全量可接受。
        """
        connection = self._conn()
        known = set(existing)
        rows = connection.execute(
            "SELECT doc_id FROM documents WHERE project_id = ?", (project_id,)
        ).fetchall()
        return sorted(str(row[0]) for row in rows if str(row[0]) not in known)

    # ------------------------------------------------------------------ #
    # 页面图关联（R2 / M-02：IFC-IB-278 / IFC-IB-283）
    # ------------------------------------------------------------------ #

    def upsert_chunk_images(
        self, scope: Scope, doc_id: str, records: Sequence[ChunkImageRecord]
    ) -> int:
        """先删后写（同 `doc_id`）—— 与 `upsert_chunks` 同构，保证重跑不产生重复行。

        删除**不带** scope 子句而是先做 scope 断言：与 `upsert_chunks` 一致（同一文档
        不可能跨 scope，断言已足够；带上子句反而让「删了零行」被静默忽略）。
        """
        clause, params = self._scope_clause(scope)
        with self._write() as connection:
            exists = connection.execute(
                f"SELECT 1 FROM documents WHERE doc_id = ?{clause}", [doc_id, *params]
            ).fetchone()
            if exists is None:
                raise NotFoundError("文档不存在或不在当前作用域内")
            connection.execute("DELETE FROM chunk_image WHERE doc_id = ?", (doc_id,))
            if records:
                connection.executemany(
                    f"INSERT INTO chunk_image ({','.join(_IMAGE_COLUMNS)}) "
                    f"VALUES ({','.join('?' for _ in _IMAGE_COLUMNS)})",
                    [_image_row(record) for record in records],
                )
        return len(records)

    def list_chunk_images(self, scope: Scope, doc_id: str) -> list[ChunkImageRecord]:
        clause, params = self._scope_clause(scope)
        rows = self._conn().execute(
            f"SELECT {','.join(_IMAGE_COLUMNS)} FROM chunk_image WHERE doc_id = ?{clause}"
            " ORDER BY page_or_section, image_id",
            [doc_id, *params],
        ).fetchall()
        return [_row_to_chunk_image(row) for row in rows]

    def get_chunk_image(
        self, scope: Scope, doc_id: str, image_id: str
    ) -> ChunkImageRecord | None:
        clause, params = self._scope_clause(scope)
        row = self._conn().execute(
            f"SELECT {','.join(_IMAGE_COLUMNS)} FROM chunk_image"
            f" WHERE doc_id = ? AND image_id = ?{clause}",
            [doc_id, image_id, *params],
        ).fetchone()
        return None if row is None else _row_to_chunk_image(row)

    # ------------------------------------------------------------------ #
    # 重建任务（RebuildJobStore）
    # ------------------------------------------------------------------ #

    def create_rebuild_job(
        self,
        *,
        project_id: str,
        from_version: str,
        to_version: str,
        target_collection: str,
        doc_count: int,
    ) -> RebuildJobRow:
        existing = self.find_rebuild_job(project_id, to_version)
        if existing is not None:
            return existing
        job_id = uuid.uuid4().hex
        now = utc_now_iso()
        with self._write() as connection:
            connection.execute(
                f"INSERT OR IGNORE INTO rebuild_jobs ({','.join(_JOB_COLUMNS)}) "
                f"VALUES ({','.join('?' for _ in _JOB_COLUMNS)})",
                (
                    job_id,
                    project_id,
                    from_version,
                    to_version,
                    target_collection,
                    int(doc_count),
                    "planned",
                    None,
                    None,
                    now,
                    now,
                ),
            )
        found = self.find_rebuild_job(project_id, to_version)
        if found is None:  # pragma: no cover
            raise DependencyUnavailableError("重建任务写入失败", dependency="ledger")
        return found

    def get_rebuild_job(self, job_id: str) -> RebuildJobRow | None:
        row = self._conn().execute(
            f"SELECT {','.join(_JOB_COLUMNS)} FROM rebuild_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        return _row_to_job(row) if row is not None else None

    def find_rebuild_job(self, project_id: str, to_version: str) -> RebuildJobRow | None:
        row = self._conn().execute(
            f"SELECT {','.join(_JOB_COLUMNS)} FROM rebuild_jobs WHERE project_id = ? AND to_version = ?",
            (project_id, to_version),
        ).fetchone()
        return _row_to_job(row) if row is not None else None

    def set_rebuild_state(
        self,
        job_id: str,
        state: str,
        *,
        lease_owner: str | None = None,
        lease_seconds: int | None = None,
    ) -> None:
        sets = ["state = ?", "updated_at = ?"]
        values: list[Any] = [state, utc_now_iso()]
        if lease_owner is not None:
            sets.append("lease_owner = ?")
            values.append(lease_owner)
        sets.append("lease_expires_at = ?")
        values.append(iso_plus_seconds(lease_seconds) if lease_seconds is not None else None)
        values.append(job_id)
        with self._write() as connection:
            cursor = connection.execute(
                f"UPDATE rebuild_jobs SET {', '.join(sets)} WHERE job_id = ?", values
            )
            if cursor.rowcount <= 0:
                raise NotFoundError("重建任务不存在")

    def claim_rebuild_job(self, job_id: str, lease_owner: str, lease_seconds: int) -> bool:
        """条件 UPDATE 认领（与文档租约同构）：**终态任务不可认领**。

        终态集合来自 `ib.ledger.TERMINAL_REBUILD_STATES`（与内存实现共用一处定义，
        避免两份实现各自维护一份终态清单而语义漂移）。
        """
        placeholders = ",".join("?" for _ in TERMINAL_REBUILD_STATES)
        with self._write() as connection:
            cursor = connection.execute(
                f"UPDATE rebuild_jobs SET state = 'running', lease_owner = ?, lease_expires_at = ?,"
                f" updated_at = ? WHERE job_id = ? AND state NOT IN ({placeholders})",
                (lease_owner, iso_plus_seconds(lease_seconds), utc_now_iso(), job_id, *sorted(TERMINAL_REBUILD_STATES)),
            )
            return cursor.rowcount > 0

    def list_rebuild_jobs(self, project_id: str) -> list[RebuildJobRow]:
        rows = self._conn().execute(
            f"SELECT {','.join(_JOB_COLUMNS)} FROM rebuild_jobs WHERE project_id = ? ORDER BY created_at",
            (project_id,),
        ).fetchall()
        return [_row_to_job(row) for row in rows]

    def reset_documents_for_rebuild(self, project_id: str, to_version: str) -> int:
        """重建启动：把该项目下 `indexed`/`failed` 文档重置回 `pending` 并标记目标版本。

        为什么必须显式重置：`claim_pending` 只认领 `status='pending'` 的行，而重建是
        「用新配置重跑一遍入库」。若不把已 `indexed` 的文档清回 `pending`，worker 永远
        找不到待处理文档，`step_rebuild` 的 `done` 判据还会因旧 `indexed` 计数误判为
        「已完成」（D-4b 的根因）。同时写入 `target_collection_version`，把此前从未落
        非空值的死列变成重建的目标锚点。

        `parsing`/`pending` 行**不动**：它们本就待处理，重置只会覆盖其租约与错误信息。
        """
        with self._write() as connection:
            cursor = connection.execute(
                "UPDATE documents SET status = 'pending', error_code = NULL,"
                " target_collection_version = ?, lease_owner = NULL, lease_expires_at = NULL,"
                " updated_at = ? WHERE project_id = ? AND status IN ('indexed', 'failed')",
                (to_version, utc_now_iso(), project_id),
            )
            return int(cursor.rowcount)

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """关闭本对象创建过的全部连接（测试与优雅停机用）。"""
        with self._connections_lock:
            connections = list(self._connections)
            self._connections.clear()
        for connection in connections:
            try:
                connection.close()
            except sqlite3.Error:  # pragma: no cover - 关闭失败不影响正确性
                pass
        self._local = threading.local()


# --------------------------------------------------------------------------- #
# 行映射（集中在此，避免各处按索引取值而错位）
# --------------------------------------------------------------------------- #


def _row_to_document(row: Sequence[Any]) -> DocumentRecord:
    return DocumentRecord(
        doc_id=row[0],
        project_id=row[1],
        kb_id=row[2],
        doc_name=row[3],
        ext=row[4],
        size_bytes=int(row[5]),
        content_sha256=row[6],
        blob_ref=row[7],
        status=row[8],
        error_code=row[9],
        chunk_count=int(row[10]),
        indexed_collection_version=row[11],
        target_collection_version=row[12],
        lease_owner=row[13],
        lease_expires_at=row[14],
        created_at=row[15],
        updated_at=row[16],
    )


def _row_to_chunk(row: Sequence[Any]) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=row[0],
        doc_id=row[1],
        project_id=row[2],
        kb_id=row[3],
        chunk_index=int(row[4]),
        content_hash=row[5],
        locator=row[6],
        source_kind=row[7],
        page_or_section=row[8],
        indexed_model=row[9],
        indexed_dim=int(row[10]),
    )


def _row_to_chunk_image(row: Sequence[Any]) -> ChunkImageRecord:
    """`chunk_image` 行 -> 不可变记录（列序见 `_IMAGE_COLUMNS`）。"""
    return ChunkImageRecord(
        project_id=row[1],
        kb_id=row[2],
        doc_id=row[3],
        page_or_section=row[4],
        image_id=row[5],
        source_kind=row[6],
        locator=row[7],
        blob_ref=row[8],
        doc_name=row[9],
        created_at=row[10],
    )


def _row_to_job(row: Sequence[Any]) -> RebuildJobRow:
    return RebuildJobRow(
        job_id=row[0],
        project_id=row[1],
        from_version=row[2],
        to_version=row[3],
        target_collection=row[4],
        doc_count=int(row[5]),
        state=row[6],
        lease_owner=row[7],
        lease_expires_at=row[8],
        created_at=row[9],
        updated_at=row[10],
    )
