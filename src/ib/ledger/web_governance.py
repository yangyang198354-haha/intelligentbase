# MOD-R28-06 / implements IFC-R28-008, WebGovernanceStore 端口（SQLite + 内存两实现）
"""联网全局用量上限存储（ADR-R28-07）。

单行表 `web_governance`（`CHECK (id = 1)`）：行缺失 ⇒ 读取返回默认值（保守默认）。
`set` 校验三个整数非 bool 且落在 [下界, 硬上限]，违规 ⇒ ValueError（HTTP 层映射 400）。
SQL 全部参数化；SQLite 写入用 `BEGIN IMMEDIATE` + 单条 upsert。
"""

from __future__ import annotations

import os
import sqlite3
import threading
from dataclasses import replace
from typing import Any, Callable

from ib.context import utc_now_iso
from ib.core import (
    WEB_BYTES_HARD_MAX,
    WEB_CALLS_HARD_MAX,
    WEB_SECONDS_HARD_MAX,
    DependencyUnavailableError,
    WebGovernance,
)
from ib.ledger.schema import ensure_schema, missing_web_governance_columns

__all__ = [
    "SqliteWebGovernanceStore",
    "MemoryWebGovernanceStore",
    "build_web_governance_store",
    "validate_web_governance",
]

_BYTES_MIN = 10_000


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_web_governance(caps: WebGovernance) -> None:
    """越界 / 非整数 / bool ⇒ ValueError（消息只含字段名与范围，不含值以外信息）。"""
    checks = (
        ("max_calls_per_turn", caps.max_calls_per_turn, 1, WEB_CALLS_HARD_MAX),
        ("max_fetch_bytes_per_turn", caps.max_fetch_bytes_per_turn, _BYTES_MIN, WEB_BYTES_HARD_MAX),
        ("max_seconds_per_turn", caps.max_seconds_per_turn, 1, WEB_SECONDS_HARD_MAX),
    )
    for name, value, lo, hi in checks:
        if not _is_int(value) or not (lo <= value <= hi):
            raise ValueError(f"{name} 须为 {lo}..{hi} 的整数")


class MemoryWebGovernanceStore:
    """离线替身；与 Sqlite 实现过同一套端口一致性测试。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._row: WebGovernance | None = None

    def get(self) -> WebGovernance:
        with self._lock:
            return self._row if self._row is not None else WebGovernance()

    def set(self, caps: WebGovernance, *, actor: str) -> WebGovernance:
        validate_web_governance(caps)
        row = replace(caps, updated_at=utc_now_iso(), updated_by=str(actor))
        with self._lock:
            self._row = row
        return row


class SqliteWebGovernanceStore:
    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        self._factory = connection_factory
        self._local = threading.local()

    def _conn(self) -> Any:
        c = getattr(self._local, "conn", None)
        if c is None:
            c = self._factory()
            self._local.conn = c
        return c

    def get(self) -> WebGovernance:
        try:
            cur = self._conn().execute(
                "SELECT max_calls_per_turn, max_fetch_bytes_per_turn, max_seconds_per_turn, updated_at, updated_by "
                "FROM web_governance WHERE id = 1"
            )
            row = cur.fetchone()
            cur.close()
        except sqlite3.Error as exc:
            raise DependencyUnavailableError("联网上限存储不可用", dependency="ledger") from exc
        if row is None:
            return WebGovernance()
        return WebGovernance(int(row[0]), int(row[1]), int(row[2]), str(row[3]), str(row[4]))

    def set(self, caps: WebGovernance, *, actor: str) -> WebGovernance:
        validate_web_governance(caps)
        now = utc_now_iso()
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "INSERT INTO web_governance (id, max_calls_per_turn, max_fetch_bytes_per_turn, "
                    "max_seconds_per_turn, updated_at, updated_by) VALUES (1, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET max_calls_per_turn = excluded.max_calls_per_turn, "
                    "max_fetch_bytes_per_turn = excluded.max_fetch_bytes_per_turn, "
                    "max_seconds_per_turn = excluded.max_seconds_per_turn, "
                    "updated_at = excluded.updated_at, updated_by = excluded.updated_by",
                    (caps.max_calls_per_turn, caps.max_fetch_bytes_per_turn, caps.max_seconds_per_turn, now, str(actor)),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        except sqlite3.Error as exc:
            raise DependencyUnavailableError("联网上限存储不可用", dependency="ledger") from exc
        return replace(caps, updated_at=now, updated_by=str(actor))


def build_web_governance_store(cfg: Any, *, ledger_path: str) -> Any:
    """按配置构造存储（组合根单点调用）。后端键 = `IB_WEB_GOVERNANCE_BACKEND`（sqlite 默认 / memory）。

    sqlite 后端构造失败不静默降级为内存实现（fail-closed）。
    """
    # 后端：显式 memory，或台账本身为 memory（跟随台账后端，同 build_config_audit_store 的纪律）⇒ 内存替身
    if (
        getattr(cfg, "web_governance_backend", "sqlite") == "memory"
        or getattr(cfg, "ledger_backend", "sqlite") == "memory"
    ):
        return MemoryWebGovernanceStore()
    path = ledger_path or ":memory:"
    if path != ":memory:":
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
    bootstrap = sqlite3.connect(path, isolation_level=None, timeout=5.0)
    try:
        ensure_schema(bootstrap)
        if missing_web_governance_columns(bootstrap):
            raise DependencyUnavailableError("web_governance 表结构不完整", dependency="ledger")
    finally:
        bootstrap.close()

    def _factory() -> sqlite3.Connection:
        c = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=5.0)
        c.execute("PRAGMA busy_timeout=5000")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    return SqliteWebGovernanceStore(_factory)
