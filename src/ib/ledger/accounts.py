"""
@module MOD-IB-11
@implements IFC-IB-313 SqliteAccountStore（+ 账户/会话 DDL 单源）
            IFC-IB-314 默认管理员幂等种子 seed_default_admin
            IFC-IB-315 MemoryAccountStore（离线替身）
            IFC-IB-310 AccountStore 端口（13 方法）的 SQL / 内存两实现
@depends MOD-IB-01（端口与结构）, MOD-IB-02（配置）, MOD-IB-04（日志白名单）, MOD-IB-11（schema）
@author software-developer

账户与会话的持久化（R13 增量；module_design.md §3 MOD-IB-11 / ADR-18 / ADR-26）。

## 与台账共用同一个 SQLite 文件

`SqliteAccountStore` 与 `SqliteLedgerRepository` 指向**同一** `IB_LEDGER_PATH`：账户体系
内建、**不新增 systemd 单元**（DR-09）。表结构单源见 `ib.ledger.schema`（= 迁移
`003_accounts.sql`），由 `--ensure-schema` 一并应用。

## 凭据纪律（C-IB-09 / REQ-NFR-IB-15，硬约束）

  * 口令**只**经 `hash_password`（bcrypt）落库；`password_hash` 列只承载摘要；
  * 会话**只**存 `token_digest`（sha256）—— 服务端从不把令牌原文写盘；
  * `username` / `user_id` **不写入日志**（字段白名单）；本模块自身不调用日志；
  * 校验口令用 `verify_password`（bcrypt 常量时间比较），失败一律返回 `False`。

## 与 `LedgerRepository` 一样的两条实现约束

  1. **线程局部连接 + WAL + `busy_timeout`**（Waitress 线程池并发；见 `sqlite_repo` 的同一理由）；
  2. **写操作用条件 UPDATE / INSERT**，不做「先查后写」的竞态动作。
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from typing import Any, Sequence

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import (
    AccountStatus,
    ConflictError,
    DependencyUnavailableError,
    NotFoundError,
    SessionRecord,
    StartupError,
    UserRecord,
    UserRole,
)
from ib.ledger.schema import ensure_schema, missing_account_columns

__all__ = [
    "hash_password",
    "verify_password",
    "SqliteAccountStore",
    "MemoryAccountStore",
    "seed_default_admin",
    "build_account_store",
]

#: `users` 表列顺序（与 `_row_to_user` 索引一一对应；集中定义避免漂移）。
_U_COLUMNS = (
    "user_id",
    "username",
    "password_hash",
    "role",
    "project_id",
    "status",
    "must_change_password",
    "failed_login_count",
    "locked_until",
    "created_at",
    "updated_at",
)

#: `sessions` 表列顺序（与 `_row_to_session` 索引一一对应）。
_S_COLUMNS = (
    "token_digest",
    "user_id",
    "project_id",
    "issued_at",
    "expires_at",
    "last_seen_at",
    "revoked_at",
)


# --------------------------------------------------------------------------- #
# bcrypt 口令哈希 / 校验（IFC-IB-313）
# --------------------------------------------------------------------------- #


def _bcrypt() -> Any:
    """惰性取 `bcrypt` 模块（缺失即给**可读**的启动错误，而非 AttributeError）。"""
    try:
        import bcrypt  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise DependencyUnavailableError(
            "缺少 bcrypt 依赖（口令哈希）。只登记包名，不回显其它信息。",
            dependency="bcrypt",
        ) from exc
    return bcrypt


def hash_password(password: str) -> str:
    """口令 → bcrypt 摘要（IFC-IB-313）。**只返回摘要，绝不返回明文**。

    bcrypt 自带盐（`gensalt`），且成本因子内嵌于摘要串 —— 无需额外存盐列。
    """
    b = _bcrypt()
    return b.hashpw(password.encode("utf-8"), b.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """bcrypt 校验口令（常量时间比较）；任何异常（如损坏摘要）一律 `False`（fail-closed）。"""
    if not password or not password_hash:
        return False
    b = _bcrypt()
    try:
        return bool(b.checkpw(password.encode("utf-8"), password_hash.encode("ascii")))
    except Exception:  # noqa: BLE001 — 摘要损坏 / 非 bcrypt 串：一律视为不匹配
        return False


# --------------------------------------------------------------------------- #
# 行映射
# --------------------------------------------------------------------------- #


def _row_to_user(row: Sequence[Any]) -> UserRecord:
    return UserRecord(
        user_id=row[0],
        username=row[1],
        password_hash=row[2],
        role=row[3],
        project_id=row[4],
        status=row[5],
        must_change_password=bool(row[6]),
        failed_login_count=int(row[7]),
        locked_until=row[8],
        created_at=row[9],
        updated_at=row[10],
    )


def _row_to_session(row: Sequence[Any]) -> SessionRecord:
    return SessionRecord(
        token_digest=row[0],
        user_id=row[1],
        project_id=row[2],
        issued_at=row[3],
        expires_at=row[4],
        last_seen_at=row[5],
        revoked_at=row[6],
    )


def _u_values(record: UserRecord) -> tuple[Any, ...]:
    return (
        record.user_id,
        record.username,
        record.password_hash,
        record.role,
        record.project_id,
        record.status,
        1 if record.must_change_password else 0,
        record.failed_login_count,
        record.locked_until,
        record.created_at,
        record.updated_at,
    )


def _replace(record: Any, **changes: Any) -> Any:
    from dataclasses import replace

    return replace(record, **changes)


# --------------------------------------------------------------------------- #
# SQLite 实现（IFC-IB-313）
# --------------------------------------------------------------------------- #


class SqliteAccountStore:
    """`AccountStore` 的 SQLite 实现（与台账共用同一 SQLite 文件）。"""

    def __init__(
        self,
        path: str,
        *,
        busy_timeout_ms: int = 5000,
        max_failures: int = 0,
        lock_seconds: int = 0,
    ) -> None:
        self._path = path or ":memory:"
        self._busy_timeout_ms = busy_timeout_ms
        #: 登录失败阈值 / 锁定窗口（**由装配期注入**；0 = 不启用限速，OQ-IB-12 / ADR-27）。
        self._max_failures = max(0, int(max_failures))
        self._lock_seconds = max(0, int(lock_seconds))
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()
        if self._path != ":memory:":
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._bootstrap()

    # --- 连接管理（与 sqlite_repo 同构） --- #

    def _connect(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            uri = "file:ib_accounts_mem?mode=memory&cache=shared"
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
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _conn(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            try:
                connection = self._connect()
            except sqlite3.Error as exc:
                raise DependencyUnavailableError(
                    f"账户存储连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        connection = self._conn()
        try:
            ensure_schema(connection)  # 含 ACCOUNT_DDL_STATEMENTS（幂等）
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"账户存储初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_account_columns(connection)
        if missing:
            tables = "；".join(f"{t}:{','.join(cols)}" for t, cols in missing.items())
            raise StartupError(
                f"账户表结构不完整（缺少列）：{tables}。请先执行 `python -m ibweb.bootstrap --ensure-schema`。"
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

    # --- AccountStore（13 方法） --- #

    def get_user_by_username(self, username: str) -> UserRecord | None:
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                f"SELECT {', '.join(_U_COLUMNS)} FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
        return _row_to_user(row) if row else None

    def get_user(self, user_id: str) -> UserRecord | None:
        cursor = self._conn().cursor()
        try:
            cursor.execute(
                f"SELECT {', '.join(_U_COLUMNS)} FROM users WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
        return _row_to_user(row) if row else None

    def _require_user(self, user_id: str) -> UserRecord:
        record = self.get_user(user_id)
        if record is None:
            raise NotFoundError("账户不存在")
        return record

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: UserRole,
        project_id: str | None,
    ) -> UserRecord:
        now = utc_now_iso()
        record = UserRecord(
            user_id=uuid.uuid4().hex,
            username=username,
            password_hash=password_hash,
            role=role,
            project_id=project_id,
            status="active",
            must_change_password=True,  # 新建账户一律首登强制改密（ADR-20）
            failed_login_count=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        connection = self._conn()
        placeholders = ", ".join("?" for _ in _U_COLUMNS)
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"INSERT INTO users ({', '.join(_U_COLUMNS)}) VALUES ({placeholders})",
                _u_values(record),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            # 唯一约束（username）或 CHECK（role / project 绑定）失败 → 409 / 400。
            if "username" in str(exc).lower() or "unique" in str(exc).lower():
                raise ConflictError("用户名已存在") from exc
            raise
        finally:
            cursor.close()
        return record

    def set_status(self, user_id: str, status: AccountStatus) -> UserRecord:
        self._require_user(user_id)
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET status = ?, updated_at = ? WHERE user_id = ?",
                (status, utc_now_iso(), user_id),
            )
            connection.commit()
        finally:
            cursor.close()
        return self._require_user(user_id)

    def set_password(
        self, user_id: str, password_hash: str, *, must_change: bool
    ) -> UserRecord:
        self._require_user(user_id)
        connection = self._conn()
        cursor = connection.cursor()
        try:
            # 改密同时清零失败计数 / 解锁：否则「被锁定的账户即使改密也进不来」，
            # 与「改密可恢复访问」的直觉相悖（重置口令是唯一的管理员恢复手段）。
            cursor.execute(
                "UPDATE users SET password_hash = ?, must_change_password = ?, "
                "failed_login_count = 0, locked_until = NULL, updated_at = ? WHERE user_id = ?",
                (password_hash, 1 if must_change else 0, utc_now_iso(), user_id),
            )
            connection.commit()
        finally:
            cursor.close()
        return self._require_user(user_id)

    def list_users(self, project_id: str | None) -> list[UserRecord]:
        cursor = self._conn().cursor()
        try:
            if project_id is None:
                cursor.execute(
                    f"SELECT {', '.join(_U_COLUMNS)} FROM users ORDER BY username"
                )
            else:
                cursor.execute(
                    f"SELECT {', '.join(_U_COLUMNS)} FROM users WHERE project_id = ? "
                    "ORDER BY username",
                    (project_id,),
                )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [_row_to_user(row) for row in rows]

    def record_login_failure(self, user_id: str, *, now: str) -> UserRecord:
        self._require_user(user_id)
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET failed_login_count = failed_login_count + 1, "
                "updated_at = ? WHERE user_id = ?",
                (now, user_id),
            )
            connection.commit()
            record = self._require_user(user_id)
            # 阈值与锁定窗口**由构造期注入**（OQ-IB-12 未裁决时 `_max_failures=0` → 永不锁定）。
            if self._max_failures and record.failed_login_count >= self._max_failures:
                cursor.execute(
                    "UPDATE users SET locked_until = ?, updated_at = ? WHERE user_id = ?",
                    (iso_plus_seconds(self._lock_seconds), now, user_id),
                )
                connection.commit()
                record = self._require_user(user_id)
        finally:
            cursor.close()
        return record

    def reset_login_failures(self, user_id: str) -> None:
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET failed_login_count = 0, locked_until = NULL WHERE user_id = ?",
                (user_id,),
            )
            connection.commit()
        finally:
            cursor.close()

    def issue_session(
        self, user_id: str, token_digest: str, *, expires_at: str
    ) -> SessionRecord:
        now = utc_now_iso()
        cursor = self._conn().cursor()
        try:
            cursor.execute("SELECT project_id FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            project_id = row[0] if row else None
            cursor.execute(
                "INSERT INTO sessions "
                "(token_digest, user_id, project_id, issued_at, expires_at, last_seen_at, revoked_at) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (token_digest, user_id, project_id, now, expires_at, now),
            )
            self._conn().commit()
        finally:
            cursor.close()
        return SessionRecord(
            token_digest=token_digest,
            user_id=user_id,
            project_id=project_id,
            issued_at=now,
            expires_at=expires_at,
            last_seen_at=now,
            revoked_at=None,
        )

    def resolve_session(self, token_digest: str, *, now: str) -> SessionRecord | None:
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"SELECT {', '.join(_S_COLUMNS)} FROM sessions "
                "WHERE token_digest = ? AND revoked_at IS NULL AND expires_at > ?",
                (token_digest, now),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            record = _row_to_session(row)
            # 刷新 last_seen_at（尽力而为）：失败**不得**改变「会话有效」这一结论。
            try:
                cursor.execute(
                    "UPDATE sessions SET last_seen_at = ? WHERE token_digest = ?",
                    (now, token_digest),
                )
                connection.commit()
            except sqlite3.Error:
                pass
        finally:
            cursor.close()
        return _replace(record, last_seen_at=now)

    def renew_session(
        self, token_digest: str, *, new_expires_at: str, now: str
    ) -> SessionRecord | None:
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET expires_at = ?, last_seen_at = ? "
                "WHERE token_digest = ? AND revoked_at IS NULL AND expires_at > ?",
                (new_expires_at, now, token_digest, now),
            )
            changed = cursor.rowcount
            connection.commit()
            if not changed:
                return None
        finally:
            cursor.close()
        return self.resolve_session(token_digest, now=now)

    def revoke_session(self, token_digest: str, *, now: str) -> None:
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token_digest = ? AND revoked_at IS NULL",
                (now, token_digest),
            )
            connection.commit()
        finally:
            cursor.close()

    def purge_expired_sessions(self, *, now: str) -> int:
        connection = self._conn()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM sessions WHERE revoked_at IS NOT NULL OR expires_at <= ?", (now,)
            )
            removed = cursor.rowcount
            connection.commit()
        finally:
            cursor.close()
        return int(removed or 0)

    # --- 组内扩展（非端口方法；用途同 `LedgerRepository.upsert_chunks` 的先例） --- #

    def revoke_sessions_for_user(
        self, user_id: str, *, now: str, keep_digest: str | None = None
    ) -> int:
        """撤销某账户**全部**（或除 `keep_digest` 外）的会话；返回撤销条数。

        端口只有单条 `revoke_session`；停用（IFC-IB-321）/ 改密（IFC-IB-319）需要
        「撤销该用户其余会话」，故补一个**组内扩展**方法（不扩端口，13 方法不变）。
        """
        connection = self._conn()
        cursor = connection.cursor()
        try:
            if keep_digest:
                cursor.execute(
                    "UPDATE sessions SET revoked_at = ? "
                    "WHERE user_id = ? AND revoked_at IS NULL AND token_digest != ?",
                    (now, user_id, keep_digest),
                )
            else:
                cursor.execute(
                    "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                    (now, user_id),
                )
            changed = cursor.rowcount
            connection.commit()
        finally:
            cursor.close()
        return int(changed or 0)


# --------------------------------------------------------------------------- #
# 内存实现（IFC-IB-315，离线替身）
# --------------------------------------------------------------------------- #


class MemoryAccountStore:
    """`AccountStore` 的内存实现（离线 / 测试替身）。

    * **纯 stdlib**、进程内、线程安全（单锁）；
    * 语义与 `SqliteAccountStore` **对齐**（同一套端口一致性自检）；
    * 可注入「过期 / 已撤销 / 停用 / 须改密」四态（直接构造对应 `UserRecord` / `SessionRecord`
      或调用端口方法即可）用于离线验证 REQ-NFR-IB-18。
    """

    def __init__(self, *, max_failures: int = 0, lock_seconds: int = 0) -> None:
        self._lock = threading.RLock()
        self._users: dict[str, UserRecord] = {}
        self._by_username: dict[str, str] = {}
        self._sessions: dict[str, SessionRecord] = {}
        self._max_failures = max(0, int(max_failures))
        self._lock_seconds = max(0, int(lock_seconds))

    def get_user_by_username(self, username: str) -> UserRecord | None:
        with self._lock:
            user_id = self._by_username.get(username)
            return self._users.get(user_id) if user_id else None

    def get_user(self, user_id: str) -> UserRecord | None:
        with self._lock:
            return self._users.get(user_id)

    def create_user(
        self, username: str, password_hash: str, role: UserRole, project_id: str | None
    ) -> UserRecord:
        with self._lock:
            if username in self._by_username:
                raise ConflictError("用户名已存在")
            if role != "admin" and project_id is None:
                raise ConflictError("ops 账户必须绑定项目")
            now = utc_now_iso()
            record = UserRecord(
                user_id=uuid.uuid4().hex,
                username=username,
                password_hash=password_hash,
                role=role,
                project_id=project_id,
                status="active",
                must_change_password=True,
                failed_login_count=0,
                locked_until=None,
                created_at=now,
                updated_at=now,
            )
            self._users[record.user_id] = record
            self._by_username[username] = record.user_id
            return record

    def _require(self, user_id: str) -> UserRecord:
        record = self._users.get(user_id)
        if record is None:
            raise NotFoundError("账户不存在")
        return record

    def set_status(self, user_id: str, status: AccountStatus) -> UserRecord:
        with self._lock:
            record = self._require(user_id)
            updated = _replace(record, status=status, updated_at=utc_now_iso())
            self._users[user_id] = updated
            return updated

    def set_password(
        self, user_id: str, password_hash: str, *, must_change: bool
    ) -> UserRecord:
        with self._lock:
            record = self._require(user_id)
            updated = _replace(
                record,
                password_hash=password_hash,
                must_change_password=must_change,
                failed_login_count=0,
                locked_until=None,
                updated_at=utc_now_iso(),
            )
            self._users[user_id] = updated
            return updated

    def list_users(self, project_id: str | None) -> list[UserRecord]:
        with self._lock:
            items = [
                record
                for record in self._users.values()
                if project_id is None or record.project_id == project_id
            ]
            return sorted(items, key=lambda item: item.username)

    def record_login_failure(self, user_id: str, *, now: str) -> UserRecord:
        with self._lock:
            record = self._require(user_id)
            count = record.failed_login_count + 1
            locked_until = record.locked_until
            if self._max_failures and count >= self._max_failures:
                locked_until = iso_plus_seconds(self._lock_seconds)
            updated = _replace(
                record, failed_login_count=count, locked_until=locked_until, updated_at=now
            )
            self._users[user_id] = updated
            return updated

    def reset_login_failures(self, user_id: str) -> None:
        with self._lock:
            record = self._users.get(user_id)
            if record is not None:
                self._users[user_id] = _replace(
                    record, failed_login_count=0, locked_until=None
                )

    def issue_session(
        self, user_id: str, token_digest: str, *, expires_at: str
    ) -> SessionRecord:
        with self._lock:
            record = self._require(user_id)
            now = utc_now_iso()
            session = SessionRecord(
                token_digest=token_digest,
                user_id=user_id,
                project_id=record.project_id,
                issued_at=now,
                expires_at=expires_at,
                last_seen_at=now,
                revoked_at=None,
            )
            self._sessions[token_digest] = session
            return session

    def resolve_session(self, token_digest: str, *, now: str) -> SessionRecord | None:
        with self._lock:
            session = self._sessions.get(token_digest)
            if session is None or session.revoked_at is not None or session.expires_at <= now:
                return None
            updated = _replace(session, last_seen_at=now)
            self._sessions[token_digest] = updated
            return updated

    def renew_session(
        self, token_digest: str, *, new_expires_at: str, now: str
    ) -> SessionRecord | None:
        with self._lock:
            session = self._sessions.get(token_digest)
            if session is None or session.revoked_at is not None or session.expires_at <= now:
                return None
            updated = _replace(session, expires_at=new_expires_at, last_seen_at=now)
            self._sessions[token_digest] = updated
            return updated

    def revoke_session(self, token_digest: str, *, now: str) -> None:
        with self._lock:
            session = self._sessions.get(token_digest)
            if session is not None and session.revoked_at is None:
                self._sessions[token_digest] = _replace(session, revoked_at=now)

    def purge_expired_sessions(self, *, now: str) -> int:
        with self._lock:
            stale = [
                digest
                for digest, session in self._sessions.items()
                if session.revoked_at is not None or session.expires_at <= now
            ]
            for digest in stale:
                self._sessions.pop(digest, None)
            return len(stale)

    def revoke_sessions_for_user(
        self, user_id: str, *, now: str, keep_digest: str | None = None
    ) -> int:
        with self._lock:
            changed = 0
            for digest, session in list(self._sessions.items()):
                if session.user_id != user_id or session.revoked_at is not None:
                    continue
                if keep_digest and digest == keep_digest:
                    continue
                self._sessions[digest] = _replace(session, revoked_at=now)
                changed += 1
            return changed


# --------------------------------------------------------------------------- #
# 默认管理员幂等种子（IFC-IB-314）
# --------------------------------------------------------------------------- #


def seed_default_admin(
    store: Any, *, username: str, password_hash: str
) -> UserRecord:
    """幂等播种默认管理员（IFC-IB-314）。

    * `role="admin"`、`project_id=None`（全局）、`must_change_password=True`、`status="active"`；
    * **幂等**：用户名已存在则**不覆盖**既有口令（`create_user` 抛 `ConflictError` 即视为已存在）；
    * 口令 hash 由 `IB_DEFAULT_ADMIN_PASSWORD`（0600 EnvironmentFile）经 `hash_password`
      产生；**本函数不接收也不回显明文口令**。
    """
    existing = store.get_user_by_username(username)
    if existing is not None:
        return existing
    try:
        return store.create_user(username, password_hash, "admin", None)
    except ConflictError:
        # 竞态：另一进程刚插入同名账户 —— 幂等语义下视为成功。
        record = store.get_user_by_username(username)
        if record is None:  # pragma: no cover - 理论上不可达
            raise
        return record


# --------------------------------------------------------------------------- #
# 组合根构造（IFC-IB-325 的存储侧）
# --------------------------------------------------------------------------- #


def build_account_store(cfg: Any, *, ledger_path: str) -> Any:
    """按 `IB_ACCOUNT_BACKEND` 构造账户存储（默认 `sqlite`；`memory` = 离线替身）。

    与 `build_ledger` 同一条纪律：`sqlite` 后端构造失败**不静默降级**为内存实现 ——
    账户体系不可用必须 fail-closed。

    限速阈值 / 锁定窗口经 `IB_LOGIN_MAX_FAILURES` / `IB_LOGIN_LOCK_SECONDS` 读取；
    **二者未设置时默认 0（不启用，ADR-27 / OQ-IB-12 未裁决）**。
    """
    backend = os.environ.get("IB_ACCOUNT_BACKEND", "").strip()
    if not backend:
        # 未显式声明时跟随台账后端：离线（memory 替身）→ memory；生产 → sqlite（默认）。
        backend = (
            "memory"
            if getattr(cfg, "ledger_backend", "sqlite") == "memory"
            else "sqlite"
        )
    max_failures = _env_int("IB_LOGIN_MAX_FAILURES", 0)
    lock_seconds = _env_int("IB_LOGIN_LOCK_SECONDS", 0)
    if backend == "memory":
        return MemoryAccountStore(max_failures=max_failures, lock_seconds=lock_seconds)
    if backend != "sqlite":
        raise StartupError(
            f"未知的 IB_ACCOUNT_BACKEND 取值（期望 sqlite / memory）。只登记键名，不回显值。"
        )
    return SqliteAccountStore(
        ledger_path, max_failures=max_failures, lock_seconds=lock_seconds
    )


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise StartupError(f"环境变量 {name} 必须为整数（只登记键名，不回显值）") from exc
