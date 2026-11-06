"""[REV-29 / GROUP_D] 单元：MCP 台账存储——内存与文件型 SQLite 同套用例（端口一致性）、凭证只存密文、级联删除、治理范围、审计过滤、迁移 010 幂等 / 单源。

分层：unit（SQLite 内存 / 临时文件；无外部依赖）。溯源：US-005 / 006 / 007 / 026（AC-005-04、AC-006-01、AC-026-02/03）。
"""

from __future__ import annotations

import re
import sqlite3

import pytest
from mcp_r29_support import CANARY_TOKEN, SECRET_KEY, tool

from ib.core import ConflictError
from ib.core.types import (
    McpAuditRecord,
    McpDiscovery,
    McpGovernance,
    McpNegotiated,
    McpServer,
    McpServerLimits,
)
from ib.ledger.mcp_store import build_mcp_stores
from ib.ledger.schema import ensure_schema, mcp_ddl_script, missing_mcp_tables
from ib.mcp.crypto import Secret
from ib.mcp.double import ReversibleTestCipher
from ib.mcp.rules import check_discovered_tool


def _server(sid="crm", **kw) -> McpServer:
    base = dict(server_id=sid, description="d", transport="streamable_http", endpoint_url=f"https://{sid}.example.com/mcp", auth_kind="bearer",
                auth_header_name=None, credential_scope="shared", scope_kind="platform", owner_project=None, open_all=False,
                data_categories=("query_text",), admin_state="registered", health="unknown", health_checked_at=None, protocol_era=None,
                protocol_version=None, supports_list_changed=False, last_verify_at=None, last_verify_result=None, identity_epoch=0,
                limits=McpServerLimits(), created_at="t0", created_by="a", updated_at="t0", updated_by="a")
    base.update(kw)
    return McpServer(**base)


def _disc(*names):
    items = [check_discovered_tool(tool(n), server_id="crm", gov=McpGovernance(), taken_local_names=set()) for n in names]
    return McpDiscovery(tuple(items), (), McpNegotiated("modern", "2026-07-28", True, False))


@pytest.fixture(params=["memory", "sqlite_file"])
def st(request, tmp_path):
    if request.param == "memory":
        return build_mcp_stores(None, backend="memory")
    path = str(tmp_path / "ledger.db")
    boot = sqlite3.connect(path, isolation_level=None)
    ensure_schema(boot)
    boot.close()

    def factory():
        c = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        return c

    return build_mcp_stores(factory, backend="sqlite")


def test_TC_UNIT_R29_500_server_create_get_duplicate_conflict_AC_001_02(st):
    st.servers.create(_server())
    with pytest.raises(ConflictError):
        st.servers.create(_server())  # 标识名重复
    assert st.servers.get("crm").endpoint_url == "https://crm.example.com/mcp" and st.servers.get("nope") is None
    assert [s.server_id for s in st.servers.list_all()] == ["crm"]


def test_TC_UNIT_R29_501_update_optimistic_concurrency_AC_004_01(st):
    import dataclasses

    st.servers.create(_server())
    cur = st.servers.get("crm")
    st.servers.update(dataclasses.replace(cur, description="新说明", updated_at="t1"), expected_updated_at="t0")
    with pytest.raises(ConflictError):  # 旧版本再写 ⇒ 冲突
        st.servers.update(dataclasses.replace(cur, description="覆盖", updated_at="t2"), expected_updated_at="t0")
    assert st.servers.get("crm").description == "新说明"


def test_TC_UNIT_R29_502_open_projects_set_and_replace_AC_007_02(st):
    st.servers.create(_server())
    st.servers.set_open("crm", open_all=False, project_ids=("p_alpha", "p_beta"), actor="a", now="t")
    assert set(st.servers.open_projects("crm")) == {"p_alpha", "p_beta"}
    st.servers.set_open("crm", open_all=False, project_ids=("p_alpha",), actor="a", now="t2")
    assert st.servers.open_projects("crm") == ("p_alpha",)


def test_TC_UNIT_R29_503_credentials_store_ciphertext_only_AC_006_01(st):
    """AC-006-01：库中只有密文——整库序列化后明文命中数 = 0。"""
    st.servers.create(_server())
    c = ReversibleTestCipher(SECRET_KEY)
    tok, kid = c.encrypt(Secret(CANARY_TOKEN))
    st.credentials.put("crm", "@shared", tok, kid, actor="a", now="t")
    got = st.credentials.get_ciphertext("crm", "@shared")
    assert got is not None and CANARY_TOKEN.encode() not in got[0] and c.decrypt(got[0]).reveal() == CANARY_TOKEN
    status = st.credentials.status("crm")
    assert len(status) == 1 and CANARY_TOKEN not in repr(status)
    assert st.credentials.delete("crm", "@shared") is True and st.credentials.get_ciphertext("crm", "@shared") is None
    assert st.credentials.delete("crm", "@shared") is False


def test_TC_UNIT_R29_504_delete_cascade_removes_tools_bindings_waivers_open_credentials_AC_005_04(st):
    st.servers.create(_server())
    st.tools.apply_discovery("crm", _disc("a", "b"), now="t")
    rec = st.tools.get_by_local_name("mcp__crm__a")
    st.tools.put_binding(rec.tool_id, "p_alpha", {"q": "x"}, actor="a", now="t")
    st.servers.set_open("crm", open_all=False, project_ids=("p_alpha",), actor="a", now="t")
    tok, kid = ReversibleTestCipher(SECRET_KEY).encrypt(Secret("v"))
    st.credentials.put("crm", "@shared", tok, kid, actor="a", now="t")
    st.audit.record(McpAuditRecord("c1", "t", "admin", "server.register", "a", "", "crm", "", "", "ok", "", 0, "", "", "", False, False))
    st.servers.delete_cascade("crm")
    assert st.servers.get("crm") is None and st.tools.list(server_id="crm") == () and st.credentials.get_ciphertext("crm", "@shared") is None
    assert st.servers.open_projects("crm") == () and st.tools.get_binding(rec.tool_id, "p_alpha") == {}
    assert st.audit.count(server_id="crm") == 1, "审计与历史调用记录保留可查（AC-005-04 / AC-026-02）"


def test_TC_UNIT_R29_505_governance_defaults_range_and_roundtrip_AC_020_04(st):
    assert st.governance.get() == McpGovernance()  # 行缺失 ⇒ 保守默认
    out = st.governance.set(McpGovernance(max_calls_per_turn=3, call_timeout_s=20), actor="a")
    assert out.max_calls_per_turn == 3 and st.governance.get().call_timeout_s == 20 and st.governance.get().updated_by == "a"
    for bad in (dict(max_calls_per_turn=0), dict(max_calls_per_turn=21), dict(call_timeout_s=121), dict(max_result_bytes=10),
                dict(listener_max=9), dict(health_interval_s=-1)):
        with pytest.raises(ValueError):
            st.governance.set(McpGovernance(**bad), actor="a")
    assert st.governance.get().max_calls_per_turn == 3, "越界写入不得落库"


def test_TC_UNIT_R29_506_audit_filters_and_ordering_AC_026_02_03(st):
    def rec(i, sid, pid, ts):
        return McpAuditRecord(f"c{i}", ts, "call", "call", "u", pid, sid, "mcp__x__y", "mcp.x.y", "ok", "", 5, "d", "s", "fp", False, False)

    for i, (sid, pid, ts) in enumerate([("crm", "p_alpha", "2026-11-01T00:00:00Z"), ("crm", "p_beta", "2026-11-02T00:00:00Z"),
                                       ("kb", "p_alpha", "2026-11-03T00:00:00Z")]):
        st.audit.record(rec(i, sid, pid, ts))
    assert st.audit.count() == 3 and st.audit.count(server_id="crm") == 2
    assert {r.project_id for r in st.audit.query(project_id="p_alpha", limit=50, offset=0)} == {"p_alpha"}  # AC-026-03：只本项目
    assert [r.call_id for r in st.audit.query(server_id="crm", ts_from="2026-11-02T00:00:00Z", limit=50, offset=0)] == ["c1"]
    assert len(st.audit.query(limit=2, offset=0)) == 2 and len(st.audit.query(limit=2, offset=2)) == 1


def test_TC_UNIT_R29_507_audit_begin_then_finish_backfills_once(st):
    r = McpAuditRecord("cx", "t", "call", "call", "u", "p", "crm", "mcp__crm__s", "mcp.crm.s", "pending", "", None, "d", "s", "fp", False, False)
    st.audit.begin_call(r)
    assert st.audit.query(limit=5, offset=0)[0].outcome == "pending"
    st.audit.finish_call("cx", outcome="ok", reason="", duration_ms=12)
    done = st.audit.query(limit=5, offset=0)[0]
    assert done.outcome == "ok" and done.duration_ms == 12


def test_TC_UNIT_R29_508_internal_allow_add_remove_idempotent_AC_027_03(st):
    st.servers.add_internal_allow("10.0.0.8", 9000, actor="a", now="t")
    st.servers.add_internal_allow("10.0.0.8", 9000, actor="a", now="t2")
    assert [(a.host, a.port) for a in st.servers.list_internal_allow()] == [("10.0.0.8", 9000)]
    assert st.servers.remove_internal_allow("10.0.0.8", 9000) is True and st.servers.remove_internal_allow("10.0.0.8", 9000) is False


def test_TC_UNIT_R29_509_apply_discovery_is_idempotent_and_reports_diff(st):
    st.servers.create(_server())
    d1 = st.tools.apply_discovery("crm", _disc("a", "b"), now="t1")
    d2 = st.tools.apply_discovery("crm", _disc("a", "b"), now="t2")
    assert set(d1.added) == {"a", "b"} and d2.added == () and d2.unchanged == 2


def test_TC_UNIT_R29_510_read_admission_single_snapshot(st):
    st.servers.create(_server(auth_kind="none"))
    st.tools.apply_discovery("crm", _disc("a"), now="t")
    rec = st.tools.get_by_local_name("mcp__crm__a")
    st.tools.approve(rec.tool_id, expected_fingerprint=rec.observed.fingerprint, risk="read_only", hidden_params=(), llm_description=None, actor="a", now="t")
    adm = st.tools.read_admission("p_alpha", "mcp__crm__a")
    assert adm is not None and adm.project_open is False and adm.tool.state == "enabled" and adm.governance == McpGovernance()
    assert st.tools.read_admission("p_alpha", "mcp__crm__nope") is None


# --------------------------------------------------------------------------- #
# 迁移 010（幂等 / 单源 / 老库升级）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R29_520_migration_010_replay_idempotent_and_single_source():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    sql = (root / "src/deploy/migrations/010_mcp.sql").read_text(encoding="utf-8")
    norm = lambda s: "".join(s.split())
    assert norm(mcp_ddl_script()) in norm(sql), "010_mcp.sql 必须与 mcp_ddl_script() 单源一致"
    con = sqlite3.connect(":memory:", isolation_level=None)
    ensure_schema(con)
    con.executescript(sql)
    con.executescript(sql)  # 重放无副作用
    assert missing_mcp_tables(con) == ()
    # 无可执行 DROP（去掉注释后）
    code = "\n".join(re.sub(r"--.*$", "", ln) for ln in sql.splitlines())
    assert not re.search(r"\bDROP\b", code, re.I)
    for old in range(1, 10):
        assert list((root / "src/deploy/migrations").glob(f"{old:03d}_*.sql")), f"{old:03d} 迁移须保留"


def test_TC_UNIT_R29_521_old_db_upgrade_creates_tables_and_transport_check_streamable_only_AC_001_06():
    con = sqlite3.connect(":memory:", isolation_level=None)
    con.execute("CREATE TABLE documents (doc_id TEXT PRIMARY KEY)")  # 模拟老库
    con.executescript(mcp_ddl_script())
    assert missing_mcp_tables(con) == () and con.execute("SELECT name FROM sqlite_master WHERE name='documents'").fetchone()
    ins = ("INSERT INTO mcp_servers (server_id, description, transport, endpoint_url, auth_kind, credential_scope, scope_kind, "
           "open_all, data_categories, admin_state, health, supports_list_changed, identity_epoch, created_at, created_by, updated_at, updated_by) "
           "VALUES ('x','d','{t}','u','none','shared','platform',0,'[]','registered','unknown',0,0,'t','a','t','a')")
    con.execute(ins.format(t="streamable_http"))  # 正例：合法传输可写入
    with pytest.raises(sqlite3.IntegrityError):  # 库层 CHECK：stdio 传输拒绝（第二道防线）
        con.execute(ins.replace("'x'", "'y'").format(t="stdio"))


def test_TC_UNIT_R29_522_missing_tables_fail_closed_not_silent_memory(tmp_path):
    from ib.core.errors import DependencyUnavailableError

    path = str(tmp_path / "empty.db")
    sqlite3.connect(path).close()
    with pytest.raises(DependencyUnavailableError):
        build_mcp_stores(lambda: sqlite3.connect(path, check_same_thread=False), backend="sqlite")


def test_TC_UNIT_R29_523_ledger_file_bytes_contain_no_plaintext_secret_nor_master_key_AC_006_01(tmp_path):
    """AC-006-01：落盘介质以明文形式命中数 = 0；主密钥在台账文件中的命中数 = 0（经真实 SQLite 文件，含 WAL / 日志字节）。"""
    import glob

    path = str(tmp_path / "ledger.db")
    boot = sqlite3.connect(path, isolation_level=None)
    ensure_schema(boot)
    boot.close()
    st = build_mcp_stores(lambda: sqlite3.connect(path, check_same_thread=False, isolation_level=None), backend="sqlite")
    st.servers.create(_server())
    c = ReversibleTestCipher(SECRET_KEY)
    tok, kid = c.encrypt(Secret(CANARY_TOKEN))
    st.credentials.put("crm", "@shared", tok, kid, actor="a", now="t")
    st.audit.record(McpAuditRecord("c1", "t", "admin", "credential.set", "a", "", "crm", "", "", "ok", "scope=shared", 0, "", "", "", False, False))
    blob = b"".join(open(f, "rb").read() for f in glob.glob(path + "*"))
    assert CANARY_TOKEN.encode() not in blob and SECRET_KEY.encode() not in blob
    assert tok in blob, "非平凡：密文确实落了盘"
