"""
@module MOD-IB-11
@implements IFC-IB-358 SqliteConfigAuditStore（+ 配置审计 DDL 单源）
            IFC-IB-357 ConfigAuditStore 端口（2 方法）的 SQL / 内存两实现
@depends MOD-IB-01（端口与结构）, MOD-IB-11（schema）
@author software-developer

配置审计的持久化（REV-16-4 增量；module_design.md §3 MOD-IB-11 / ADR-34）。

## 只读审计，不是第二真源（ADR-34）

本模块**只**做两件事：**追加**一条审计记录（`record`）与**按项目回放**（`list_by_project`）。
**没有** update / delete 路径 —— 审计记录一经写入即不可变（append-only 台账）。
**任何**上层模块**不得**从这里回读配置来驱动行为；配置真源恒为定义文档
（`IB_DEFINITION_DOC_PATH` 指向的文件 / 内存种子）与提示词目录。

## 与台账共用同一个 SQLite 文件

`SqliteConfigAuditStore` 与 `SqliteLedgerRepository` / `SqliteAccountStore` 指向**同一**
`IB_LEDGER_PATH`（ADR-34：不引入第二个存储后端）。表结构单源见 `ib.ledger.schema`
（= 迁移 `004_config_audit.sql`），由 `--ensure-schema` 一并应用。审计表**独立成块**
（module_design §3 MOD-IB-11 建议「审计表与文档/账户台账逻辑分区」），**不加外键**到
`projects`（审计记录须在项目被删后仍可考）。

## 凭据纪律（SC-3，硬约束）

  * `changed_field_names` **只含字段名**；`detail_code` **只含字段名 / 错误码**；
  * 本模块**从不**接收、存储或回显任何凭据值 / 字段值 —— 入参 `ConfigAuditEntry`
    由调用方在**写库之前**完成脱敏（只保留字段名与错误码）。

## 与 `SqliteAccountStore` 一样的两条实现约束

  1. **线程局部连接 + WAL + `busy_timeout`**（Waitress 线程池并发）；
  2. **写操作用 INSERT**，不做「先查后写」的竞态动作。
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any

from ib.core import (
    ConfigAuditEntry,
    ConfigAuditResult,
    DependencyUnavailableError,
    StartupError,
)
from ib.ledger.schema import ensure_schema, missing_config_audit_columns

__all__ = [
    "SqliteConfigAuditStore",
    "MemoryConfigAuditStore",
    "build_config_audit_store",
]

#: 查询列（与 `_row_to_entry` 一一对应；集中一处避免 `SELECT *` 漂移）。
_A_COLUMNS = (
    "timestamp",
    "project",
    "actor",
    "action",
    "changed_field_names",
    "result",
    "detail_code",
)


class SqliteConfigAuditStore:
    """`ConfigAuditStore` 的 SQLite 实现（与台账共用同一 SQLite 文件）。

    恰好两个方法（`record` / `list_by_project`），**无 update / delete**（IFC-IB-357）。
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

    # --- 连接管理（与 sqlite_repo / accounts 同构） --- #

    def _connect(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            uri = "file:ib_config_audit_mem?mode=memory&cache=shared"
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
        # 连接级 PRAGMA（每条新连接都要设置一次）。刻意**不**在此处执行
        # `PRAGMA journal_mode=WAL`：它是数据库级持久设置，已在 `ensure_schema` 落地一次。
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
                    f"配置审计存储连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        connection = self._conn()
        try:
            ensure_schema(connection)  # 含 CONFIG_AUDIT_DDL_STATEMENTS（幂等）
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"配置审计存储初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_config_audit_columns(connection)
        if missing:
            tables = "；".join(f"{t}:{','.join(cols)}" for t, cols in missing.items())
            raise StartupError(
                f"配置审计表结构不完整（缺少列）：{tables}。"
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

    # --- ConfigAuditStore（恰好 2 方法） --- #

    def record(self, entry: ConfigAuditEntry) -> None:
        """追加一条审计记录（IFC-IB-360）。**只 INSERT**，不提供更新 / 删除。"""
        column_list = ", ".join(_A_COLUMNS)
        placeholders = ", ".join("?" for _ in _A_COLUMNS)
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                f"INSERT INTO config_audit ({column_list}) VALUES ({placeholders})",
                (
                    entry.timestamp,
                    entry.project,
                    entry.actor,
                    entry.action,
                    # 只存**字段名**的 JSON 数组；永不存字段值（SC-3）。
                    json.dumps(list(entry.changed_field_names), ensure_ascii=False),
                    entry.result,
                    entry.detail_code,
                ),
            )
        finally:
            cursor.close()

    def list_by_project(
        self,
        project_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[ConfigAuditEntry, ...]:
        """按项目回放审计记录（IFC-IB-359），稳定升序（`entry_id` 追加序）。"""
        safe_limit = max(0, int(limit))
        safe_offset = max(0, int(offset))
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                f"SELECT {', '.join(_A_COLUMNS)} FROM config_audit "
                "WHERE project = ? ORDER BY entry_id ASC LIMIT ? OFFSET ?",
                (project_id, safe_limit, safe_offset),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return tuple(_row_to_entry(row) for row in rows)


class MemoryConfigAuditStore:
    """`ConfigAuditStore` 的内存实现（离线 / 测试替身，IFC-IB-357）。

    * **纯 stdlib**、进程内、线程安全（单锁）；
    * 语义与 `SqliteConfigAuditStore` **对齐**（同一套端口一致性自检）；
    * 同样**只**暴露 `record` / `list_by_project`（无 update / delete）。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[ConfigAuditEntry] = []

    def record(self, entry: ConfigAuditEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def list_by_project(
        self,
        project_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[ConfigAuditEntry, ...]:
        with self._lock:
            matched = [e for e in self._entries if e.project == project_id]
        safe_limit = max(0, int(limit))
        safe_offset = max(0, int(offset))
        return tuple(matched[safe_offset : safe_offset + safe_limit])


def _row_to_entry(row: Any) -> ConfigAuditEntry:
    """行 → `ConfigAuditEntry`（`changed_field_names` 由 JSON 数组还原为元组）。"""
    (
        timestamp,
        project,
        actor,
        action,
        changed_field_names_json,
        result,
        detail_code,
    ) = row
    try:
        changed = tuple(json.loads(changed_field_names_json or "[]"))
    except (json.JSONDecodeError, TypeError):
        # 列内容被外部损坏：不静默丢弃该记录，退回「无字段名」的空元组（记录本身仍在）。
        changed = ()
    return ConfigAuditEntry(
        timestamp=str(timestamp),
        project=str(project),
        actor=str(actor),
        action=str(action),
        changed_field_names=tuple(str(name) for name in changed),
        result=_coerce_result(result),
        detail_code=str(detail_code) if detail_code is not None else None,
    )


def _coerce_result(raw: Any) -> ConfigAuditResult:
    """把存储层取值收敛到 `ConfigAuditResult`（CHECK 已兜底；此处只做类型收敛）。"""
    text = str(raw)
    return "saved" if text == "saved" else "rejected"


def build_config_audit_store(cfg: Any, *, ledger_path: str) -> Any:
    """按台账后端构造配置审计存储（组合根单点调用）。

    与 `build_ledger` / `build_account_store` 同一条纪律：`sqlite` 后端构造失败
    **不静默降级**为内存实现 —— 审计不可用必须 fail-closed（由调用方发结构化 WARN）。

    后端选择**跟随台账后端**（`cfg.ledger_backend`）：`memory` → 内存替身；否则 →
    与台账同一 SQLite 文件的 `SqliteConfigAuditStore`（ADR-34：不引入第二个存储后端）。
    """
    if getattr(cfg, "ledger_backend", "sqlite") == "memory":
        return MemoryConfigAuditStore()
    return SqliteConfigAuditStore(ledger_path)
