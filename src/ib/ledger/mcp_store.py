# MOD-R29-07 / implements IFC-R29-061..065 (McpServerStore/McpToolStore/McpCredentialStore/McpGovernanceStore/McpAuditStore) / depends MOD-R29-01
"""MCP 外部工具的台账存储（SQLite 与"内存替身"两种后端，共用同一份 DDL 与同一套 SQL）。

* DDL 单源：`ib.ledger.schema.MCP_DDL_STATEMENTS`（= `010_mcp.sql`）。
* 内存替身 = 共享的 `:memory:` SQLite 连接 + 全局锁 —— 与 Sqlite 实现**同源同语义**（端口一致性由构造保证）。
* SQL 全部参数化；写入 `BEGIN IMMEDIATE`；文件后端的连接按线程缓存（`threading.local`，同 web_governance 手法）。
* 凭证表只存密文；审计表类型层无凭证 / 完整入参字段。
* `read_admission` 无缓存：管理动作提交后下一次读取即可见（REQ-NFUNC-010）。
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import replace
from typing import Any, Callable, Iterator, Literal, Mapping

from ib.context import utc_now_iso
from ib.core.errors import ConflictError, DependencyUnavailableError, NotFoundError
from ib.core.ports import McpStores
from ib.core.types import (
    MCP_DEFAULTS,
    MCP_HARD_MAX,
    McpAdmission,
    McpAuditRecord,
    McpCredentialStatus,
    McpDiscovery,
    McpDiscoveryDiff,
    McpGovernance,
    McpInternalAllow,
    McpNegotiated,
    McpServer,
    McpServerLimits,
    McpToolRecord,
    McpToolSnapshot,
)
from ib.ledger.schema import ensure_schema, missing_mcp_tables
from ib.mcp.rules import display_tool_name, inference_risk, local_tool_name

__all__ = [
    "SqliteMcpServerStore",
    "MemoryMcpServerStore",
    "SqliteMcpToolStore",
    "MemoryMcpToolStore",
    "SqliteMcpCredentialStore",
    "MemoryMcpCredentialStore",
    "SqliteMcpGovernanceStore",
    "MemoryMcpGovernanceStore",
    "SqliteMcpAuditStore",
    "MemoryMcpAuditStore",
    "build_mcp_stores",
    "validate_mcp_governance",
    "excluded_local_name",
]


def _j(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _unavailable(exc: Exception) -> DependencyUnavailableError:
    return DependencyUnavailableError("MCP 存储不可用", dependency="ledger")


class _Db:
    """连接提供者：文件后端 = 线程局部连接；内存后端 = 单连接 + RLock。"""

    def __init__(self, factory: Callable[[], Any] | None = None, *, memory: bool = False) -> None:
        self._memory = memory
        self._lock = threading.RLock()
        self._local = threading.local()
        if memory:
            conn = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
            ensure_schema(conn)
            self._shared = conn
            self._factory = None
        else:
            assert factory is not None
            self._shared = None
            self._factory = factory

    @classmethod
    def memory(cls) -> "_Db":
        return cls(memory=True)

    def _conn(self) -> Any:
        if self._shared is not None:
            return self._shared
        c = getattr(self._local, "conn", None)
        if c is None:
            c = self._factory()  # type: ignore[misc]
            self._local.conn = c
        return c

    def query(self, sql: str, params: tuple = ()) -> list[tuple]:
        try:
            if self._memory:
                with self._lock:
                    return self._conn().execute(sql, params).fetchall()
            return self._conn().execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    @contextmanager
    def tx(self) -> Iterator[Any]:
        """`BEGIN IMMEDIATE` … `COMMIT`（异常回滚）。sqlite3.Error（含 IntegrityError）原样外抛，由调用方映射。"""
        if self._memory:
            self._lock.acquire()
        try:
            conn = self._conn()
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        finally:
            if self._memory:
                self._lock.release()


def _as_db(source: Any) -> _Db:
    if isinstance(source, _Db):
        return source
    return _Db(source)


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #

_SERVER_COLS = (
    "server_id, description, transport, endpoint_url, auth_kind, auth_header_name, credential_scope, scope_kind, "
    "owner_project, open_all, data_categories, admin_state, health, health_checked_at, protocol_era, "
    "protocol_version, supports_list_changed, last_verify_at, last_verify_result, identity_epoch, "
    "limit_call_timeout_s, limit_max_calls_per_turn, limit_max_result_bytes, limit_max_concurrency, "
    "limit_breaker_threshold, limit_breaker_cooldown_s, limit_discover_timeout_s, "
    "created_at, created_by, updated_at, updated_by"
)
_SERVER_COL_LIST = tuple(c.strip() for c in _SERVER_COLS.split(","))


def _row_server(r: tuple) -> McpServer:
    return McpServer(
        server_id=r[0], description=r[1], transport=r[2], endpoint_url=r[3], auth_kind=r[4],
        auth_header_name=r[5], credential_scope=r[6], scope_kind=r[7], owner_project=r[8],
        open_all=bool(r[9]), data_categories=tuple(json.loads(r[10])), admin_state=r[11], health=r[12],
        health_checked_at=r[13], protocol_era=r[14], protocol_version=r[15], supports_list_changed=bool(r[16]),
        last_verify_at=r[17], last_verify_result=r[18], identity_epoch=int(r[19]),
        limits=McpServerLimits(*(None if v is None else int(v) for v in r[20:27])),
        created_at=r[27], created_by=r[28], updated_at=r[29], updated_by=r[30],
    )


def _limits_tuple(lim: McpServerLimits) -> tuple:
    return (
        lim.call_timeout_s, lim.max_calls_per_turn, lim.max_result_bytes, lim.max_concurrency,
        lim.breaker_threshold, lim.breaker_cooldown_s, lim.discover_timeout_s,
    )


class SqliteMcpServerStore:
    def __init__(self, source: Any) -> None:
        self._db = _as_db(source)

    def create(self, s: McpServer) -> McpServer:
        row = (
            s.server_id, s.description, s.transport, s.endpoint_url, s.auth_kind, s.auth_header_name,
            s.credential_scope, s.scope_kind, s.owner_project, int(s.open_all), _j(list(s.data_categories)),
            s.admin_state, s.health, s.health_checked_at, s.protocol_era, s.protocol_version,
            int(s.supports_list_changed), s.last_verify_at, s.last_verify_result, int(s.identity_epoch),
            *_limits_tuple(s.limits), s.created_at, s.created_by, s.updated_at, s.updated_by,
        )
        try:
            with self._db.tx() as c:
                c.execute(
                    f"INSERT INTO mcp_servers ({_SERVER_COLS}) VALUES ({','.join('?' * len(_SERVER_COL_LIST))})", row
                )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc).upper() or "PRIMARY" in str(exc).upper():
                raise ConflictError("server_id_exists") from None
            raise ValueError("server_row_invalid") from None
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        return s

    def get(self, server_id: str) -> McpServer | None:
        rows = self._db.query(f"SELECT {_SERVER_COLS} FROM mcp_servers WHERE server_id = ?", (server_id,))
        return _row_server(rows[0]) if rows else None

    def list_all(self) -> tuple[McpServer, ...]:
        rows = self._db.query(f"SELECT {_SERVER_COLS} FROM mcp_servers ORDER BY server_id")
        return tuple(_row_server(r) for r in rows)

    def update(self, s: McpServer, *, expected_updated_at: str) -> McpServer:
        # identity_epoch 不在此写入：只经 McpToolStore.mark_identity_changed 递增（同事务联动工具状态）
        try:
            with self._db.tx() as c:
                cur = c.execute(
                    "UPDATE mcp_servers SET description=?, transport=?, endpoint_url=?, auth_kind=?, auth_header_name=?, "
                    "credential_scope=?, scope_kind=?, owner_project=?, data_categories=?, admin_state=?, "
                    "limit_call_timeout_s=?, limit_max_calls_per_turn=?, limit_max_result_bytes=?, "
                    "limit_max_concurrency=?, limit_breaker_threshold=?, limit_breaker_cooldown_s=?, "
                    "limit_discover_timeout_s=?, updated_at=?, updated_by=? "
                    "WHERE server_id=? AND updated_at=?",
                    (
                        s.description, s.transport, s.endpoint_url, s.auth_kind, s.auth_header_name,
                        s.credential_scope, s.scope_kind, s.owner_project, _j(list(s.data_categories)), s.admin_state,
                        *_limits_tuple(s.limits), s.updated_at, s.updated_by, s.server_id, expected_updated_at,
                    ),
                )
                if cur.rowcount == 0:
                    exists = c.execute("SELECT 1 FROM mcp_servers WHERE server_id=?", (s.server_id,)).fetchone()
                    if exists is None:
                        raise NotFoundError("server_not_found")
                    raise ConflictError("stale_update")
        except sqlite3.IntegrityError:
            raise ValueError("server_row_invalid") from None
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        got = self.get(s.server_id)
        assert got is not None
        return got

    def set_admin_state(self, server_id: str, state: str, *, actor: str, now: str) -> McpServer:
        try:
            with self._db.tx() as c:
                cur = c.execute(
                    "UPDATE mcp_servers SET admin_state=?, updated_at=?, updated_by=? WHERE server_id=?",
                    (state, now, actor, server_id),
                )
                if cur.rowcount == 0:
                    raise NotFoundError("server_not_found")
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        got = self.get(server_id)
        assert got is not None
        return got

    def record_probe(
        self,
        server_id: str,
        *,
        health: str,
        checked_at: str,
        verify_result: str | None = None,
        negotiated: McpNegotiated | None = None,
    ) -> None:
        sets = ["health=?", "health_checked_at=?"]
        params: list[Any] = [health, checked_at]
        if verify_result is not None:
            sets += ["last_verify_at=?", "last_verify_result=?"]
            params += [checked_at, verify_result]
        if negotiated is not None:
            sets += ["protocol_era=?", "protocol_version=?", "supports_list_changed=?"]
            params += [negotiated.era, negotiated.version, int(negotiated.supports_list_changed)]
        params.append(server_id)
        try:
            with self._db.tx() as c:
                c.execute(f"UPDATE mcp_servers SET {', '.join(sets)} WHERE server_id=?", tuple(params))
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def set_open(self, server_id: str, *, open_all: bool, project_ids: tuple[str, ...], actor: str, now: str) -> None:
        try:
            with self._db.tx() as c:
                cur = c.execute(
                    "UPDATE mcp_servers SET open_all=?, updated_at=?, updated_by=? WHERE server_id=?",
                    (int(open_all), now, actor, server_id),
                )
                if cur.rowcount == 0:
                    raise NotFoundError("server_not_found")
                c.execute("DELETE FROM mcp_server_projects WHERE server_id=?", (server_id,))
                for pid in dict.fromkeys(project_ids):
                    c.execute(
                        "INSERT INTO mcp_server_projects (server_id, project_id, created_at, created_by) VALUES (?,?,?,?)",
                        (server_id, pid, now, actor),
                    )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def open_projects(self, server_id: str) -> tuple[str, ...]:
        rows = self._db.query(
            "SELECT project_id FROM mcp_server_projects WHERE server_id=? ORDER BY project_id", (server_id,)
        )
        return tuple(r[0] for r in rows)

    def delete_cascade(self, server_id: str) -> None:
        try:
            with self._db.tx() as c:
                ids = "SELECT tool_id FROM mcp_tools WHERE server_id=?"
                c.execute(f"DELETE FROM mcp_tool_bindings WHERE tool_id IN ({ids})", (server_id,))
                c.execute(f"DELETE FROM mcp_risk_waivers WHERE tool_id IN ({ids})", (server_id,))
                c.execute("DELETE FROM mcp_tools WHERE server_id=?", (server_id,))
                c.execute("DELETE FROM mcp_server_projects WHERE server_id=?", (server_id,))
                c.execute("DELETE FROM mcp_credentials WHERE server_id=?", (server_id,))
                c.execute("DELETE FROM mcp_servers WHERE server_id=?", (server_id,))
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def list_internal_allow(self) -> tuple[McpInternalAllow, ...]:
        rows = self._db.query("SELECT host, port, created_at, created_by FROM mcp_internal_allow ORDER BY host, port")
        return tuple(McpInternalAllow(r[0], int(r[1]), r[2], r[3]) for r in rows)

    def add_internal_allow(self, host: str, port: int, *, actor: str, now: str) -> None:
        try:
            with self._db.tx() as c:
                c.execute(
                    "INSERT OR IGNORE INTO mcp_internal_allow (host, port, created_at, created_by) VALUES (?,?,?,?)",
                    (host.lower(), int(port), now, actor),
                )
        except sqlite3.IntegrityError:
            raise ValueError("internal_allow_invalid") from None
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def remove_internal_allow(self, host: str, port: int) -> bool:
        try:
            with self._db.tx() as c:
                cur = c.execute("DELETE FROM mcp_internal_allow WHERE host=? AND port=?", (host.lower(), int(port)))
                return cur.rowcount > 0
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc


class MemoryMcpServerStore(SqliteMcpServerStore):
    def __init__(self, db: _Db | None = None) -> None:
        super().__init__(db or _Db.memory())


# --------------------------------------------------------------------------- #
# Tool
# --------------------------------------------------------------------------- #

_TOOL_COLS = (
    "tool_id, server_id, remote_name, local_name, display_name, state, risk, exclusion_reason, "
    "observed_title, observed_description, observed_input_schema, observed_output_schema, observed_annotations, "
    "observed_fingerprint, observed_at, approved_title, approved_description, approved_input_schema, "
    "approved_output_schema, approved_annotations, approved_fingerprint, approved_at, approved_by, approved_epoch, "
    "llm_description, hidden_params, offline_at, offline_reason"
)


def excluded_local_name(server_id: str, remote_name: str) -> str:
    """被排除工具的占位 local_name（保证 UNIQUE(local_name)；含 `!` 故永不是合法函数名，不会被授权 / 注册）。"""
    import hashlib

    return f"mcp__{server_id}__!x{hashlib.sha256(remote_name.encode('utf-8')).hexdigest()[:12]}"


def _snap(title: Any, desc: Any, ins: Any, outs: Any, ann: Any, fp: Any) -> McpToolSnapshot | None:
    if fp is None:
        return None
    return McpToolSnapshot(
        title=title,
        description=desc or "",
        input_schema=json.loads(ins) if ins else {},
        output_schema=json.loads(outs) if outs else None,
        annotations=json.loads(ann) if ann else {},
        fingerprint=fp,
    )


def _row_tool(r: tuple) -> McpToolRecord:
    return McpToolRecord(
        tool_id=int(r[0]), server_id=r[1], remote_name=r[2], local_name=r[3], display_name=r[4], state=r[5],
        risk=r[6], exclusion_reason=r[7],
        observed=_snap(r[8], r[9], r[10], r[11], r[12], r[13]), observed_at=r[14],
        approved=_snap(r[15], r[16], r[17], r[18], r[19], r[20]), approved_at=r[21], approved_by=r[22],
        approved_epoch=None if r[23] is None else int(r[23]), llm_description=r[24],
        hidden_params=tuple(json.loads(r[25] or "[]")), offline_at=r[26], offline_reason=r[27],
    )


def _obs_params(s: McpToolSnapshot) -> tuple:
    return (
        s.title, s.description, _j(s.input_schema), None if s.output_schema is None else _j(s.output_schema),
        _j(s.annotations), s.fingerprint,
    )


class SqliteMcpToolStore:
    def __init__(self, source: Any) -> None:
        self._db = _as_db(source)

    # -- 发现 ------------------------------------------------------------- #
    def apply_discovery(self, server_id: str, d: McpDiscovery, *, now: str) -> McpDiscoveryDiff:
        added: list[str] = []
        changed: list[str] = []
        offline: list[str] = []
        reappeared: list[str] = []
        excluded: list[str] = []
        unchanged = 0
        try:
            with self._db.tx() as c:
                if c.execute("SELECT 1 FROM mcp_servers WHERE server_id=?", (server_id,)).fetchone() is None:
                    raise NotFoundError("server_not_found")
                existing = {
                    r[0]: (r[1], r[2], r[3], r[4])
                    for r in c.execute(
                        "SELECT remote_name, state, observed_fingerprint, approved_fingerprint, tool_id "
                        "FROM mcp_tools WHERE server_id=?",
                        (server_id,),
                    ).fetchall()
                }
                listed: set[str] = set()
                for t in d.tools:
                    listed.add(t.remote_name)
                    local = local_tool_name(server_id, t.remote_name)
                    disp = display_tool_name(server_id, t.remote_name)
                    obs = _obs_params(t.snapshot)
                    prev = existing.get(t.remote_name)
                    if prev is None:
                        c.execute(
                            "INSERT INTO mcp_tools (server_id, remote_name, local_name, display_name, state, risk, "
                            "observed_title, observed_description, observed_input_schema, observed_output_schema, "
                            "observed_annotations, observed_fingerprint, observed_at, hidden_params) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (server_id, t.remote_name, local, disp, "pending_review",
                             inference_risk(t.snapshot.annotations), *obs, now, "[]"),
                        )
                        added.append(t.remote_name)
                        continue
                    state, obs_fp, appr_fp, _tid = prev
                    sets = [
                        "observed_title=?", "observed_description=?", "observed_input_schema=?",
                        "observed_output_schema=?", "observed_annotations=?", "observed_fingerprint=?", "observed_at=?",
                    ]
                    params: list[Any] = [*obs, now]
                    new_state = state
                    kind = "unchanged"
                    if state == "excluded":
                        new_state = "needs_rereview" if appr_fp else "pending_review"
                        sets += ["local_name=?", "display_name=?", "exclusion_reason=NULL"]
                        params += [local, disp]
                        kind = "added"
                    elif state == "offline":
                        new_state = "needs_rereview" if appr_fp else "pending_review"
                        sets += ["offline_at=NULL", "offline_reason=NULL"]
                        kind = "reappeared"
                    elif state == "enabled" and appr_fp and appr_fp != t.snapshot.fingerprint:
                        new_state = "needs_rereview"
                        kind = "changed"
                    elif obs_fp != t.snapshot.fingerprint:
                        kind = "changed"
                    if new_state != state:
                        sets.append("state=?")
                        params.append(new_state)
                    c.execute(
                        f"UPDATE mcp_tools SET {', '.join(sets)} WHERE server_id=? AND remote_name=?",
                        (*params, server_id, t.remote_name),
                    )
                    if kind == "added":
                        added.append(t.remote_name)
                    elif kind == "reappeared":
                        reappeared.append(t.remote_name)
                    elif kind == "changed":
                        changed.append(t.remote_name)
                    else:
                        unchanged += 1
                for x in d.excluded:
                    listed.add(x.remote_name)
                    excluded.append(x.remote_name)
                    prev = existing.get(x.remote_name)
                    xl = excluded_local_name(server_id, x.remote_name)
                    if prev is None:
                        c.execute(
                            "INSERT INTO mcp_tools (server_id, remote_name, local_name, display_name, state, risk, "
                            "exclusion_reason, hidden_params, observed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (server_id, x.remote_name, xl, display_tool_name(server_id, x.remote_name), "excluded",
                             "unknown", x.reason, "[]", now),
                        )
                    else:
                        c.execute(
                            "UPDATE mcp_tools SET state='excluded', exclusion_reason=?, local_name=?, observed_at=? "
                            "WHERE server_id=? AND remote_name=?",
                            (x.reason, xl, now, server_id, x.remote_name),
                        )
                for remote, (state, _o, _a, _t) in existing.items():
                    if remote in listed:
                        continue
                    if state == "excluded":
                        c.execute("DELETE FROM mcp_tools WHERE server_id=? AND remote_name=?", (server_id, remote))
                    elif state != "offline":
                        c.execute(
                            "UPDATE mcp_tools SET state='offline', offline_at=?, offline_reason='not_listed' "
                            "WHERE server_id=? AND remote_name=?",
                            (now, server_id, remote),
                        )
                        offline.append(remote)
        except sqlite3.IntegrityError:
            raise ConflictError("tool_name_conflict") from None
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        return McpDiscoveryDiff(
            added=tuple(added), changed=tuple(changed), offline=tuple(offline), reappeared=tuple(reappeared),
            excluded=tuple(excluded), unchanged=unchanged,
        )

    # -- 读 --------------------------------------------------------------- #
    def get(self, tool_id: int) -> McpToolRecord | None:
        rows = self._db.query(f"SELECT {_TOOL_COLS} FROM mcp_tools WHERE tool_id=?", (int(tool_id),))
        return _row_tool(rows[0]) if rows else None

    def get_by_local_name(self, local_name: str) -> McpToolRecord | None:
        rows = self._db.query(f"SELECT {_TOOL_COLS} FROM mcp_tools WHERE local_name=?", (local_name,))
        return _row_tool(rows[0]) if rows else None

    def list(self, *, server_id: str | None = None, state: str | None = None, risk: str | None = None) -> tuple[McpToolRecord, ...]:
        where, params = [], []
        for col, val in (("server_id", server_id), ("state", state), ("risk", risk)):
            if val is not None:
                where.append(f"{col}=?")
                params.append(val)
        sql = f"SELECT {_TOOL_COLS} FROM mcp_tools" + (" WHERE " + " AND ".join(where) if where else "")
        rows = self._db.query(sql + " ORDER BY server_id, remote_name", tuple(params))
        return tuple(_row_tool(r) for r in rows)

    # -- 审核 / 状态 -------------------------------------------------------- #
    def _load(self, c: Any, tool_id: int) -> McpToolRecord:
        r = c.execute(f"SELECT {_TOOL_COLS} FROM mcp_tools WHERE tool_id=?", (int(tool_id),)).fetchone()
        if r is None:
            raise NotFoundError("tool_not_found")
        return _row_tool(r)

    def approve(
        self,
        tool_id: int,
        *,
        expected_fingerprint: str,
        risk: str,
        hidden_params: tuple[str, ...],
        llm_description: str | None,
        actor: str,
        now: str,
    ) -> McpToolRecord:
        try:
            with self._db.tx() as c:
                rec = self._load(c, tool_id)
                if rec.state not in ("pending_review", "needs_rereview", "disabled") or rec.observed is None:
                    raise ConflictError("tool_state_invalid")
                if rec.observed.fingerprint != expected_fingerprint:
                    raise ConflictError("fingerprint_changed")
                epoch = c.execute("SELECT identity_epoch FROM mcp_servers WHERE server_id=?", (rec.server_id,)).fetchone()
                if epoch is None:
                    raise NotFoundError("server_not_found")
                c.execute(
                    "UPDATE mcp_tools SET state='enabled', risk=?, approved_title=observed_title, "
                    "approved_description=observed_description, approved_input_schema=observed_input_schema, "
                    "approved_output_schema=observed_output_schema, approved_annotations=observed_annotations, "
                    "approved_fingerprint=observed_fingerprint, approved_at=?, approved_by=?, approved_epoch=?, "
                    "llm_description=?, hidden_params=? WHERE tool_id=?",
                    (risk, now, actor, int(epoch[0]), llm_description, _j(list(hidden_params)), int(tool_id)),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        got = self.get(tool_id)
        assert got is not None
        return got

    def reject(self, tool_id: int, *, actor: str, now: str) -> McpToolRecord:
        try:
            with self._db.tx() as c:
                rec = self._load(c, tool_id)
                if rec.state not in ("pending_review", "needs_rereview"):
                    raise ConflictError("tool_state_invalid")
                c.execute("UPDATE mcp_tools SET state='disabled' WHERE tool_id=?", (int(tool_id),))
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        got = self.get(tool_id)
        assert got is not None
        return got

    def set_enabled(self, tool_id: int, enabled: bool, *, actor: str, now: str) -> McpToolRecord:
        try:
            with self._db.tx() as c:
                rec = self._load(c, tool_id)
                if enabled:
                    if rec.state == "enabled":
                        pass
                    elif rec.state != "disabled" or rec.approved is None or rec.observed is None:
                        raise ConflictError("needs_review")
                    else:
                        epoch = c.execute(
                            "SELECT identity_epoch FROM mcp_servers WHERE server_id=?", (rec.server_id,)
                        ).fetchone()
                        if (
                            rec.observed.fingerprint != rec.approved.fingerprint
                            or epoch is None
                            or rec.approved_epoch != int(epoch[0])
                        ):
                            raise ConflictError("needs_review")
                        c.execute("UPDATE mcp_tools SET state='enabled' WHERE tool_id=?", (int(tool_id),))
                else:
                    if rec.state == "enabled":
                        c.execute("UPDATE mcp_tools SET state='disabled' WHERE tool_id=?", (int(tool_id),))
                    elif rec.state != "disabled":
                        raise ConflictError("tool_state_invalid")
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        got = self.get(tool_id)
        assert got is not None
        return got

    def mark_identity_changed(self, server_id: str, *, now: str) -> int:
        try:
            with self._db.tx() as c:
                cur = c.execute(
                    "UPDATE mcp_servers SET identity_epoch = identity_epoch + 1 WHERE server_id=?", (server_id,)
                )
                if cur.rowcount == 0:
                    raise NotFoundError("server_not_found")
                cur = c.execute(
                    "UPDATE mcp_tools SET state='needs_rereview' WHERE server_id=? "
                    "AND state IN ('enabled','disabled') AND approved_fingerprint IS NOT NULL",
                    (server_id,),
                )
                return int(cur.rowcount)
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    # -- 绑定 / 放行 -------------------------------------------------------- #
    def put_binding(self, tool_id: int, project_id: str, fixed_args: Mapping[str, Any], *, actor: str, now: str) -> None:
        try:
            with self._db.tx() as c:
                self._load(c, tool_id)
                c.execute(
                    "INSERT INTO mcp_tool_bindings (tool_id, project_id, fixed_args, updated_at, updated_by) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(tool_id, project_id) DO UPDATE SET fixed_args=excluded.fixed_args, "
                    "updated_at=excluded.updated_at, updated_by=excluded.updated_by",
                    (int(tool_id), project_id, _j(dict(fixed_args)), now, actor),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def get_binding(self, tool_id: int, project_id: str) -> Mapping[str, Any]:
        rows = self._db.query(
            "SELECT fixed_args FROM mcp_tool_bindings WHERE tool_id=? AND project_id=?", (int(tool_id), project_id)
        )
        return json.loads(rows[0][0]) if rows else {}

    def grant_waiver(self, tool_id: int, project_id: str, *, reason: str, actor: str, now: str) -> None:
        try:
            with self._db.tx() as c:
                self._load(c, tool_id)
                c.execute(
                    "INSERT INTO mcp_risk_waivers (tool_id, project_id, reason, granted_by, granted_at, revoked_at) "
                    "VALUES (?,?,?,?,?,NULL) ON CONFLICT(tool_id, project_id) DO UPDATE SET reason=excluded.reason, "
                    "granted_by=excluded.granted_by, granted_at=excluded.granted_at, revoked_at=NULL",
                    (int(tool_id), project_id, reason, actor, now),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def revoke_waiver(self, tool_id: int, project_id: str, *, actor: str, now: str) -> bool:
        try:
            with self._db.tx() as c:
                cur = c.execute(
                    "UPDATE mcp_risk_waivers SET revoked_at=? WHERE tool_id=? AND project_id=? AND revoked_at IS NULL",
                    (now, int(tool_id), project_id),
                )
                return cur.rowcount > 0
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def waiver_projects(self, tool_id: int) -> tuple[str, ...]:
        """（实现扩展）某工具当前有效放行的项目；供管理页展示，不属端口。"""
        rows = self._db.query(
            "SELECT project_id FROM mcp_risk_waivers WHERE tool_id=? AND revoked_at IS NULL ORDER BY project_id",
            (int(tool_id),),
        )
        return tuple(r[0] for r in rows)

    def bindings_for(self, tool_id: int) -> Mapping[str, Mapping[str, Any]]:
        """（实现扩展）某工具各项目的固定入参；仅 admin 详情使用，不属端口。"""
        rows = self._db.query("SELECT project_id, fixed_args FROM mcp_tool_bindings WHERE tool_id=?", (int(tool_id),))
        return {r[0]: json.loads(r[1]) for r in rows}

    # -- 准入（热路径） ------------------------------------------------------ #
    def read_admission(self, project_id: str, local_name: str) -> McpAdmission | None:
        tcols = ", ".join("t." + c.strip() for c in _TOOL_COLS.split(","))
        scols = ", ".join("s." + c.strip() for c in _SERVER_COLS.split(","))
        sql = (
            f"SELECT {tcols}, {scols}, "
            "(s.open_all = 1 OR EXISTS (SELECT 1 FROM mcp_server_projects p WHERE p.server_id = s.server_id AND p.project_id = ?) "
            " OR (s.scope_kind = 'project' AND s.owner_project = ?)), "
            "EXISTS (SELECT 1 FROM mcp_risk_waivers w WHERE w.tool_id = t.tool_id AND w.project_id = ? AND w.revoked_at IS NULL), "
            "(SELECT b.fixed_args FROM mcp_tool_bindings b WHERE b.tool_id = t.tool_id AND b.project_id = ?), "
            "EXISTS (SELECT 1 FROM mcp_credentials cr WHERE cr.server_id = s.server_id AND cr.scope_key = "
            " CASE s.credential_scope WHEN 'shared' THEN '@shared' ELSE ? END) "
            "FROM mcp_tools t JOIN mcp_servers s ON s.server_id = t.server_id WHERE t.local_name = ?"
        )
        rows = self._db.query(sql, (project_id, project_id, project_id, project_id, project_id, local_name))
        if not rows:
            return None
        r = rows[0]
        n_t = len(_TOOL_COLS.split(","))
        n_s = len(_SERVER_COLS.split(","))
        tool = _row_tool(r[:n_t])
        server = _row_server(r[n_t : n_t + n_s])
        extra = r[n_t + n_s :]
        try:
            gov_rows = self._db.query(_GOV_SELECT)
            gov = _row_gov(gov_rows[0]) if gov_rows else McpGovernance()
        except DependencyUnavailableError:
            gov = McpGovernance()  # 保守默认（审计由调用方在 admission 之外记 governance_unreadable）
        return McpAdmission(
            server=server,
            tool=tool,
            project_open=bool(extra[0]),
            waiver_active=bool(extra[1]),
            fixed_args=json.loads(extra[2]) if extra[2] else {},
            credential_present=True if server.auth_kind == "none" else bool(extra[3]),
            governance=gov,
        )


class MemoryMcpToolStore(SqliteMcpToolStore):
    def __init__(self, db: _Db | None = None) -> None:
        super().__init__(db or _Db.memory())


# --------------------------------------------------------------------------- #
# Credential
# --------------------------------------------------------------------------- #


class SqliteMcpCredentialStore:
    def __init__(self, source: Any) -> None:
        self._db = _as_db(source)

    def put(self, server_id: str, scope_key: str, ciphertext: bytes, key_id: str, *, actor: str, now: str) -> None:
        try:
            with self._db.tx() as c:
                if c.execute("SELECT 1 FROM mcp_servers WHERE server_id=?", (server_id,)).fetchone() is None:
                    raise NotFoundError("server_not_found")
                c.execute(
                    "INSERT INTO mcp_credentials (server_id, scope_key, ciphertext, key_id, updated_at, updated_by) "
                    "VALUES (?,?,?,?,?,?) ON CONFLICT(server_id, scope_key) DO UPDATE SET ciphertext=excluded.ciphertext, "
                    "key_id=excluded.key_id, updated_at=excluded.updated_at, updated_by=excluded.updated_by",
                    (server_id, scope_key, bytes(ciphertext), key_id, now, actor),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def get_ciphertext(self, server_id: str, scope_key: str) -> tuple[bytes, str] | None:
        rows = self._db.query(
            "SELECT ciphertext, key_id FROM mcp_credentials WHERE server_id=? AND scope_key=?", (server_id, scope_key)
        )
        return (bytes(rows[0][0]), rows[0][1]) if rows else None

    def status(self, server_id: str) -> tuple[McpCredentialStatus, ...]:
        rows = self._db.query(
            "SELECT scope_key, updated_at, updated_by FROM mcp_credentials WHERE server_id=? ORDER BY scope_key",
            (server_id,),
        )
        return tuple(McpCredentialStatus(r[0], True, r[1], r[2]) for r in rows)

    def delete(self, server_id: str, scope_key: str) -> bool:
        try:
            with self._db.tx() as c:
                cur = c.execute("DELETE FROM mcp_credentials WHERE server_id=? AND scope_key=?", (server_id, scope_key))
                return cur.rowcount > 0
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc


class MemoryMcpCredentialStore(SqliteMcpCredentialStore):
    def __init__(self, db: _Db | None = None) -> None:
        super().__init__(db or _Db.memory())


# --------------------------------------------------------------------------- #
# Governance（单行）
# --------------------------------------------------------------------------- #

_GOV_FIELDS = tuple(MCP_DEFAULTS.keys())
_GOV_SELECT = f"SELECT {', '.join(_GOV_FIELDS)}, updated_at, updated_by FROM mcp_governance WHERE id = 1"


def _row_gov(r: tuple) -> McpGovernance:
    vals = {k: int(r[i]) for i, k in enumerate(_GOV_FIELDS)}
    return McpGovernance(**vals, updated_at=str(r[len(_GOV_FIELDS)]), updated_by=str(r[len(_GOV_FIELDS) + 1]))


def validate_mcp_governance(g: McpGovernance) -> None:
    """非 int / bool / 越界 ⇒ ValueError（消息只含字段名与范围）。"""
    for name in _GOV_FIELDS:
        v = getattr(g, name)
        lo, hi = MCP_HARD_MAX[name]
        if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
            raise ValueError(f"{name} 须为 {lo}..{hi} 的整数")


class SqliteMcpGovernanceStore:
    def __init__(self, source: Any) -> None:
        self._db = _as_db(source)

    def get(self) -> McpGovernance:
        rows = self._db.query(_GOV_SELECT)  # 读失败 ⇒ DependencyUnavailableError（调用方回落保守默认）
        return _row_gov(rows[0]) if rows else McpGovernance()

    def set(self, g: McpGovernance, *, actor: str) -> McpGovernance:
        validate_mcp_governance(g)
        now = utc_now_iso()
        cols = ", ".join(_GOV_FIELDS)
        marks = ", ".join("?" * (len(_GOV_FIELDS) + 3))
        upd = ", ".join(f"{k}=excluded.{k}" for k in (*_GOV_FIELDS, "updated_at", "updated_by"))
        try:
            with self._db.tx() as c:
                c.execute(
                    f"INSERT INTO mcp_governance (id, {cols}, updated_at, updated_by) VALUES ({marks}) "
                    f"ON CONFLICT(id) DO UPDATE SET {upd}",
                    (1, *(getattr(g, k) for k in _GOV_FIELDS), now, str(actor)),
                )
        except sqlite3.IntegrityError:
            raise ValueError("governance_out_of_range") from None
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc
        return replace(g, updated_at=now, updated_by=str(actor))


class MemoryMcpGovernanceStore(SqliteMcpGovernanceStore):
    def __init__(self, db: _Db | None = None) -> None:
        super().__init__(db or _Db.memory())


# --------------------------------------------------------------------------- #
# Audit（追加型）
# --------------------------------------------------------------------------- #

_AUDIT_COLS = (
    "call_id, ts, kind, action, actor, project_id, server_id, tool_name, display_name, outcome, reason, "
    "duration_ms, args_digest, args_summary, fingerprint, confirm, trial"
)


def _row_audit(r: tuple) -> McpAuditRecord:
    return McpAuditRecord(
        call_id=r[0], ts=r[1], kind=r[2], action=r[3], actor=r[4], project_id=r[5], server_id=r[6], tool_name=r[7],
        display_name=r[8], outcome=r[9], reason=r[10], duration_ms=None if r[11] is None else int(r[11]),
        args_digest=r[12], args_summary=r[13], fingerprint=r[14], confirm=bool(r[15]), trial=bool(r[16]),
    )


class SqliteMcpAuditStore:
    def __init__(self, source: Any) -> None:
        self._db = _as_db(source)

    def _insert(self, r: McpAuditRecord) -> None:
        try:
            with self._db.tx() as c:
                c.execute(
                    f"INSERT INTO mcp_audit ({_AUDIT_COLS}) VALUES ({','.join('?' * 17)})",
                    (
                        r.call_id, r.ts, r.kind, r.action, r.actor, r.project_id, r.server_id, r.tool_name,
                        r.display_name, r.outcome, r.reason, r.duration_ms, r.args_digest, r.args_summary,
                        r.fingerprint, int(r.confirm), int(r.trial),
                    ),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    def begin_call(self, r: McpAuditRecord) -> None:
        self._insert(r)  # 失败 ⇒ 抛异常（调用方据此不发送，audit_failed）

    def record(self, r: McpAuditRecord) -> None:
        self._insert(r)

    def finish_call(self, call_id: str, *, outcome: str, reason: str, duration_ms: int) -> None:
        try:
            with self._db.tx() as c:  # 回填一次：仅 outcome='pending' 的行
                c.execute(
                    "UPDATE mcp_audit SET outcome=?, reason=?, duration_ms=? WHERE call_id=? AND outcome='pending'",
                    (outcome, reason, int(duration_ms), call_id),
                )
        except sqlite3.Error as exc:
            raise _unavailable(exc) from exc

    @staticmethod
    def _where(server_id, tool_name, project_id, kind, ts_from, ts_to) -> tuple[str, list[Any]]:
        where, params = [], []
        for col, op, val in (
            ("server_id", "=", server_id), ("tool_name", "=", tool_name), ("project_id", "=", project_id),
            ("kind", "=", kind), ("ts", ">=", ts_from), ("ts", "<=", ts_to),
        ):
            if val is not None:
                where.append(f"{col} {op} ?")
                params.append(val)
        return (" WHERE " + " AND ".join(where)) if where else "", params

    def query(
        self,
        *,
        server_id: str | None = None,
        tool_name: str | None = None,
        project_id: str | None = None,
        kind: str | None = None,
        ts_from: str | None = None,
        ts_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[McpAuditRecord, ...]:
        w, p = self._where(server_id, tool_name, project_id, kind, ts_from, ts_to)
        lim = max(1, min(int(limit), 200))
        rows = self._db.query(
            f"SELECT {_AUDIT_COLS} FROM mcp_audit{w} ORDER BY ts DESC, rowid DESC LIMIT ? OFFSET ?",
            (*p, lim, max(0, int(offset))),
        )
        return tuple(_row_audit(r) for r in rows)

    def count(
        self,
        *,
        server_id: str | None = None,
        tool_name: str | None = None,
        project_id: str | None = None,
        kind: str | None = None,
        ts_from: str | None = None,
        ts_to: str | None = None,
    ) -> int:
        w, p = self._where(server_id, tool_name, project_id, kind, ts_from, ts_to)
        return int(self._db.query(f"SELECT COUNT(*) FROM mcp_audit{w}", tuple(p))[0][0])


class MemoryMcpAuditStore(SqliteMcpAuditStore):
    def __init__(self, db: _Db | None = None) -> None:
        super().__init__(db or _Db.memory())


# --------------------------------------------------------------------------- #
# 装配
# --------------------------------------------------------------------------- #


def build_mcp_stores(
    connection_factory: Callable[[], Any] | None, *, backend: Literal["sqlite", "memory"]
) -> McpStores:
    """五个存储共用一个连接提供者。sqlite 后端须先保证表已建（调用方先 ensure_schema）；
    表缺失 ⇒ DependencyUnavailableError（fail-closed，不静默降级为内存）。"""
    if backend == "memory":
        db = _Db.memory()
    else:
        assert connection_factory is not None
        probe = connection_factory()
        try:
            missing = missing_mcp_tables(probe)
        finally:
            try:
                probe.close()
            except Exception:  # noqa: BLE001
                pass
        if missing:
            raise DependencyUnavailableError("MCP 表结构不完整", dependency="ledger")
        db = _Db(connection_factory)
    return McpStores(
        servers=SqliteMcpServerStore(db),
        tools=SqliteMcpToolStore(db),
        credentials=SqliteMcpCredentialStore(db),
        governance=SqliteMcpGovernanceStore(db),
        audit=SqliteMcpAuditStore(db),
    )
