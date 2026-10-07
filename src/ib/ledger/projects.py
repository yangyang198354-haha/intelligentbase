"""
@module MOD-IB-11
@implements IFC-IB-370 SqliteProjectRegistryStore / MemoryProjectRegistryStore（项目注册表适配器）
            IFC-IB-367 ProjectRegistryStore 端口（5 方法）的 SQL / 内存两实现
@depends MOD-IB-01（端口与结构）, MOD-IB-11（schema）
@author software-developer

项目注册表的持久化（REV-18 增量；module_design.md §3 MOD-IB-11；ADR-37 / IFC-IB-370）。

## 同一 SQLite 台账、同一手写 scoped 迁移机制

`SqliteProjectRegistryStore` 与 `SqliteLedgerRepository` / `SqliteAccountStore` /
`SqliteConfigAuditStore` 指向**同一** `IB_LEDGER_PATH`（ADR-37：不引入第二个存储后端）。
它复用的是既有 `projects` 物理表的一个**列子集投影**：

  * 台账侧列（`active_collection_version` / `embedding_model_id` / `dim`）由
    `_seed_projects` / `upsert_project` 写入（部署期固定）；
  * 注册表侧列（`status` / `updated_at`）由本模块承载（运行期可变：CRUD + 软删 / 停用）。

`status` 列的**前向扩展**由 `ib.ledger.schema.ensure_schema()` 的幂等补列落实
（DDL 单源 = 手写迁移 `005_projects.sql`，IFC-IB-377）。

## 软删 = 置 `status="disabled"`（不删行）

`disable()` **只**改状态列；数据保留、可恢复（OOS-19 已把物理级联删除移出范围）。

## 装配期幂等首次播种

`seed()` 以 `IB_CONFIG_FILE.projects.<id>` 为初始数据，`INSERT ... ON CONFLICT DO NOTHING`
（**不覆盖既有注册表行** —— 运行期改名 / 停用的项目在重启后不被配置回滚）。**非端口方法**。

## 纪律

  * **WAL + `busy_timeout` 必开**（沿用 MOD-IB-11 既有约束）；
  * 表内**只承载项目标识 / 名称 / 状态 / 时间戳**，**不承载任何凭据 / 配置取值**；
  * 线程局部连接（与 `SqliteConfigAuditStore` 同构）。
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Iterable

from ib.context import utc_now_iso
from ib.core import (
    ConflictError,
    DependencyUnavailableError,
    ProjectRegistryEntry,
    StartupError,
)
from ib.ledger.schema import ensure_schema, missing_project_registry_columns

__all__ = [
    "SqliteProjectRegistryStore",
    "MemoryProjectRegistryStore",
    "build_project_registry_store",
]

#: 查询列（与 `_row_to_entry` 一一对应；集中一处避免 `SELECT *` 漂移）。
_P_COLUMNS = ("project_id", "name", "status", "created_at", "updated_at")


def _row_to_entry(row: Any) -> ProjectRegistryEntry:
    project_id, name, status, created_at, updated_at = row
    return ProjectRegistryEntry(
        project_id=str(project_id),
        name=str(name),
        status="disabled" if str(status) == "disabled" else "active",
        created_at=str(created_at),
        updated_at=str(updated_at or ""),
    )


class SqliteProjectRegistryStore:
    """`ProjectRegistryStore` 的 SQLite 实现（与台账共用同一 SQLite 文件；IFC-IB-370）。"""

    def __init__(
        self,
        path: str,
        *,
        embedding_model_id: str = "",
        dim: int = 0,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self._path = path or ":memory:"
        self._busy_timeout_ms = busy_timeout_ms
        # 运行期新建项目时台账侧列的默认值（部署期全局嵌入规格）——使新项目在
        # **下一次装配**即得到一个可用（非空）的 collection 规格，而非 dim=0。
        self._embedding_model_id = embedding_model_id
        self._dim = int(dim)
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()
        if self._path != ":memory:":
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._bootstrap()

    # --- 连接管理（与 config_audit / accounts 同构） --- #

    def _connect(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            uri = "file:ib_project_registry_mem?mode=memory&cache=shared"
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
        # 连接级 PRAGMA（每条新连接都要设置一次）。`journal_mode=WAL` 是库级持久设置，
        # 已在 `ensure_schema` 落地一次，此处刻意不重跑。
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
                    f"项目注册表连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        connection = self._conn()
        try:
            ensure_schema(connection)  # 含 PROJECT_REGISTRY_DDL_STATEMENTS + 幂等补列
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"项目注册表初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_project_registry_columns(connection)
        if missing:
            tables = "；".join(f"{t}:{','.join(cols)}" for t, cols in missing.items())
            raise StartupError(
                f"项目注册表结构不完整（缺少列）：{tables}。"
                "请先执行 `python -m ibweb.bootstrap --ensure-schema`。"
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

    # --- ProjectRegistryStore（恰好 5 方法） --- #

    def load(self, project_id: str) -> ProjectRegistryEntry | None:
        row = self._conn().execute(
            f"SELECT {', '.join(_P_COLUMNS)} FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        return None if row is None else _row_to_entry(row)

    def list_active(self) -> tuple[ProjectRegistryEntry, ...]:
        rows = self._conn().execute(
            f"SELECT {', '.join(_P_COLUMNS)} FROM projects WHERE status = 'active' "
            "ORDER BY project_id ASC"
        ).fetchall()
        return tuple(_row_to_entry(row) for row in rows)

    def create(self, entry: ProjectRegistryEntry) -> ProjectRegistryEntry:
        now = entry.created_at or utc_now_iso()
        try:
            self._conn().execute(
                "INSERT INTO projects (project_id, name, active_collection_version, "
                "embedding_model_id, dim, created_at, status, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.project_id,
                    entry.name,
                    # 台账侧列：新项目取部署期全局嵌入规格 + 初始 collection 版本。
                    "1",
                    self._embedding_model_id,
                    self._dim,
                    now,
                    entry.status,
                    entry.updated_at or now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"项目已存在：{entry.project_id}") from exc
        created = self.load(entry.project_id)
        return created if created is not None else entry

    def update(self, entry: ProjectRegistryEntry) -> ProjectRegistryEntry | None:
        now = entry.updated_at or utc_now_iso()
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                "UPDATE projects SET name = ?, status = ?, updated_at = ? WHERE project_id = ?",
                (entry.name, entry.status, now, entry.project_id),
            )
            changed = cursor.rowcount
        finally:
            cursor.close()
        if not changed:
            return None
        return self.load(entry.project_id)

    def disable(self, project_id: str) -> ProjectRegistryEntry | None:
        now = utc_now_iso()
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                "UPDATE projects SET status = 'disabled', updated_at = ? WHERE project_id = ?",
                (now, project_id),
            )
            changed = cursor.rowcount
        finally:
            cursor.close()
        if not changed:
            return None
        return self.load(project_id)

    # --- 装配期播种（非端口方法；组合根 / 自测） --- #

    def seed(self, entries: Iterable[ProjectRegistryEntry]) -> int:
        """幂等首次播种：`INSERT ... ON CONFLICT DO NOTHING`（**不覆盖既有行**）。

        返回新增条数。既有行的名称 / 状态在重启后**不被配置文件回滚**（运行期 CRUD
        的成果得以保留）。
        """
        inserted = 0
        cursor = self._conn().cursor()
        try:
            for entry in entries:
                now = entry.created_at or utc_now_iso()
                cursor.execute(
                    "INSERT INTO projects (project_id, name, active_collection_version, "
                    "embedding_model_id, dim, created_at, status, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(project_id) DO NOTHING",
                    (
                        entry.project_id,
                        entry.name,
                        "1",
                        self._embedding_model_id,
                        self._dim,
                        now,
                        entry.status,
                        entry.updated_at or now,
                    ),
                )
                inserted += cursor.rowcount or 0
        finally:
            cursor.close()
        return inserted


class MemoryProjectRegistryStore:
    """`ProjectRegistryStore` 的内存实现（离线 / 测试替身，IFC-IB-370）。

    * **纯 stdlib**、进程内、线程安全（单锁）；
    * 语义与 `SqliteProjectRegistryStore` **对齐**（同一套端口一致性自检）：
      软删仍为 `status="disabled"`、`create` 冲突抛 `ConflictError`、
      `seed` 不覆盖既有行。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: dict[str, ProjectRegistryEntry] = {}

    def load(self, project_id: str) -> ProjectRegistryEntry | None:
        with self._lock:
            return self._entries.get(project_id)

    def list_active(self) -> tuple[ProjectRegistryEntry, ...]:
        with self._lock:
            active = [e for e in self._entries.values() if e.status == "active"]
        return tuple(sorted(active, key=lambda e: e.project_id))

    def create(self, entry: ProjectRegistryEntry) -> ProjectRegistryEntry:
        with self._lock:
            if entry.project_id in self._entries:
                raise ConflictError(f"项目已存在：{entry.project_id}")
            now = entry.created_at or utc_now_iso()
            stored = ProjectRegistryEntry(
                project_id=entry.project_id,
                name=entry.name,
                status=entry.status,
                created_at=now,
                updated_at=entry.updated_at or now,
            )
            self._entries[entry.project_id] = stored
            return stored

    def update(self, entry: ProjectRegistryEntry) -> ProjectRegistryEntry | None:
        with self._lock:
            existing = self._entries.get(entry.project_id)
            if existing is None:
                return None
            now = entry.updated_at or utc_now_iso()
            stored = ProjectRegistryEntry(
                project_id=existing.project_id,
                name=entry.name,
                status=entry.status,
                created_at=existing.created_at,
                updated_at=now,
            )
            self._entries[entry.project_id] = stored
            return stored

    def disable(self, project_id: str) -> ProjectRegistryEntry | None:
        with self._lock:
            existing = self._entries.get(project_id)
            if existing is None:
                return None
            stored = ProjectRegistryEntry(
                project_id=existing.project_id,
                name=existing.name,
                status="disabled",
                created_at=existing.created_at,
                updated_at=utc_now_iso(),
            )
            self._entries[project_id] = stored
            return stored

    def seed(self, entries: Iterable[ProjectRegistryEntry]) -> int:
        inserted = 0
        with self._lock:
            for entry in entries:
                if entry.project_id in self._entries:
                    continue
                now = entry.created_at or utc_now_iso()
                self._entries[entry.project_id] = ProjectRegistryEntry(
                    project_id=entry.project_id,
                    name=entry.name,
                    status=entry.status,
                    created_at=now,
                    updated_at=entry.updated_at or now,
                )
                inserted += 1
        return inserted


def build_project_registry_store(
    cfg: Any,
    *,
    ledger_path: str,
) -> Any:
    """按配置构造项目注册表存储（组合根单点调用；IFC-IB-369）。

    后端键 = `IB_PROJECT_REGISTRY_BACKEND`（`sqlite` 默认 / `memory`）。`sqlite` 后端
    构造失败**不静默降级**为内存实现 —— 注册表不可用必须 fail-closed。
    """
    from ib.core.ports import ProjectRegistryStore  # noqa: F401  (端口一致性自证)

    if getattr(cfg, "project_registry_backend", "sqlite") == "memory":
        return MemoryProjectRegistryStore()
    embedding = getattr(cfg, "embedding", None)
    return SqliteProjectRegistryStore(
        ledger_path,
        embedding_model_id=str(getattr(embedding, "model_id", "") or ""),
        dim=int(getattr(embedding, "dim", 0) or 0),
    )
