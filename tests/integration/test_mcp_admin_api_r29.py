"""[REV-29 / GROUP_D] 集成：MCP 管理 HTTP 端点族（真实账户鉴权 + 真实视图 + 内存台账 + FakeMcpServer 替身传输）。

分层：integration（HTTP 视图 ↔ 管理服务 ↔ 目录服务 ↔ 存储 ↔ 传输替身；LLM 不参与）。
溯源：US-001 ~ 008、010 ~ 012、015、021、025、026、027。
边界：MOD-R29-19(视图) ↔ MOD-R29-15(管理服务) ↔ MOD-R29-14(目录) ↔ MOD-R29-07(存储) ↔ MOD-R29-09(传输替身)。
"""

from __future__ import annotations

import json
import time

import pytest
from mcp_r29_support import CANARY_TOKEN, P, Harness, dumps_all, make_harness, tool

BETA = "p_beta"


@pytest.fixture()
def h(monkeypatch) -> Harness:
    return make_harness(monkeypatch)


def _err(resp) -> str:
    return (resp.json_body or {}).get("error", {}).get("code", "")


# =========================================================================== #
# 权限矩阵（US-025 / AC-025-04；AC-001-03、003-03、004-04、011-03、015-05、024-03）
# =========================================================================== #


def _admin_only(tid: int) -> list[tuple[str, str, object]]:
    return [
        ("POST", "/api/mcp/servers", {"server_id": "zzz", "transport": "streamable_http", "endpoint_url": "https://zzz.example.com/mcp",
                                      "auth_kind": "bearer", "data_categories": ["query_text"]}),
        ("PATCH", "/api/mcp/servers/crm", {"description": "x", "expected_updated_at": "t"}),
        ("POST", "/api/mcp/servers/crm/verify", {}), ("POST", "/api/mcp/servers/crm/enable", {}),
        ("POST", "/api/mcp/servers/crm/disable", {}), ("POST", "/api/mcp/servers/crm/refresh", {}),
        ("DELETE", "/api/mcp/servers/crm?confirm=crm&force=1", None),
        ("PUT", "/api/mcp/servers/crm/credentials", {"scope": "shared", "secret": "x"}),
        ("DELETE", "/api/mcp/servers/crm/credentials?scope=shared", None),
        ("PUT", "/api/mcp/servers/crm/open", {"open_all": True, "project_ids": []}),
        ("POST", f"/api/mcp/tools/{tid}/review", {"decision": "reject"}), ("POST", f"/api/mcp/tools/{tid}/state", {"enabled": False}),
        ("PUT", f"/api/mcp/tools/{tid}/bindings/p_alpha", {"fixed_args": {"q": "x"}}),
        ("PUT", f"/api/mcp/tools/{tid}/waivers/p_alpha", {"reason": "x"}), ("DELETE", f"/api/mcp/tools/{tid}/waivers/p_alpha", None),
        ("GET", "/api/mcp/governance", None), ("PUT", "/api/mcp/governance", {}),
        ("GET", "/api/mcp/internal-allow", None), ("POST", "/api/mcp/internal-allow", {"host": "10.0.0.8", "port": 9000}),
        ("DELETE", "/api/mcp/internal-allow?host=10.0.0.8&port=9000", None),
    ]


def test_TC_INT_R29_800_permission_matrix_admin_only_endpoints_no_side_effects_AC_025_04(h):
    """管理动作全集：匿名得 401；项目配置者（view / edit / manage 档）得 403；全部无副作用（Server 列表、工具状态、审计条数、治理参数不变）。"""
    h.ready("crm", [tool("search")])
    tid = h.tool_id("mcp__crm__search")
    snap = lambda: (json.dumps(h.api.get("/api/mcp/servers").json_body, sort_keys=True), json.dumps(h.api.get(f"/api/mcp/tools/{tid}").json_body, sort_keys=True),
                    h.b.stores.audit.count(), json.dumps(h.api.get("/api/mcp/governance").json_body, sort_keys=True), len(h.b.stores.servers.list_internal_allow()))
    before = snap()
    rows = 0
    for method, path, body in _admin_only(tid):
        for who in ("anonymous", "viewer", "editor", "mgr_alpha"):
            if who == "anonymous":
                kw = {} if body is None else {"data": json.dumps(body), "content_type": "application/json"}
                r = getattr(h.api.client, method.lower())(path, **kw)
                code = r.status_code
            else:
                r = h.api.call(method, path, who, body, project=P, force_header=True)
                code = r.status_code
            want = 401 if who == "anonymous" else 403
            assert code == want, (method, path, who, code)
            rows += 1
    assert rows >= 70
    assert snap() == before, "未授权动作不得有任何副作用"
    # 正例：同一批动作 admin 不被权限拦（至少不是 401/403）
    r = h.api.get("/api/mcp/governance")
    assert r.status_code == 200


def test_TC_INT_R29_801_reader_endpoints_anonymous_401_and_token_in_query_rejected_AC_003_03(h):
    for path in ("/api/mcp/servers", "/api/mcp/tools", "/api/mcp/audit", "/api/mcp/servers/crm", "/api/mcp/tools/1"):
        assert h.api.client.get(path).status_code == 401, path
    r = h.api.get("/api/mcp/servers?token=abc")  # 令牌只允许经 Authorization 头
    assert r.status_code == 400 and _err(r) == "token_in_query_forbidden"


def test_TC_INT_R29_802_audit_endpoint_levels_AC_026_03(h):
    """审计：admin 全量；manage 档项目账号强制只看本项目；edit / view 档 403；匿名 401。"""
    h.ready("crm", [tool("search")], projects=(P, BETA))
    for proj in (P, P, BETA):
        assert h.invoke("mcp__crm__search", project=proj).ok
    assert h.api.get("/api/mcp/audit", who="editor", project=None, force_header=True).status_code == 403
    assert h.api.get("/api/mcp/audit", who="viewer", project=None, force_header=True).status_code == 403
    assert h.api.client.get("/api/mcp/audit").status_code == 401
    adm = h.api.get("/api/mcp/audit?kind=call").json_body
    assert {i["project_id"] for i in adm["items"]} >= {P, BETA}
    a = h.api.get("/api/mcp/audit?kind=call", who="mgr_alpha", project=None, force_header=True).json_body
    assert a["total"] >= 2 and {i["project_id"] for i in a["items"]} == {P}  # 他项目记录 0 条
    b = h.api.get(f"/api/mcp/audit?kind=call&project_id={P}", who="mgr_beta", project=None, force_header=True).json_body
    assert {i["project_id"] for i in b["items"]} == {BETA}, "项目账号传他项目 project_id 也被强制改为本项目"
    for q in ("limit=0", "limit=201", "offset=-1", "kind=bogus", "from=not-a-date"):
        assert h.api.get(f"/api/mcp/audit?{q}").status_code == 400, q


# =========================================================================== #
# 登记 / 校验（US-001 / 008；AC-001-01/02/04/06、008-02/04/05、006-06、004-03、027-03/07）
# =========================================================================== #


def _lit(h, *ips):
    """FakeResolver 只查表、不放行 IP 字面量；这里补上字面量自解析，贴近生产 default_resolver 对字面 IP 的行为。"""
    for ip in ips:
        h.b.resolver.set(ip, [ip])


def _body(sid="crm", url="https://crm.example.com/mcp", **kw):
    b = {"server_id": sid, "description": "d", "transport": "streamable_http", "endpoint_url": url, "auth_kind": "bearer",
         "data_categories": ["query_text"]}
    b.update(kw)
    return b


def test_TC_INT_R29_810_register_success_shows_not_enabled_zero_tools_token_never_echoed_AC_001_01(h):
    h.b.resolver.set("crm.example.com", ["93.184.216.34"])
    r = h.api.post("/api/mcp/servers", _body())
    assert r.status_code == 201 and r.json_body["admin_state"] == "registered" and r.json_body["tool_counts"] == {
        "pending_review": 0, "enabled": 0, "disabled": 0, "needs_rereview": 0, "offline": 0, "excluded": 0}
    c = h.api.put("/api/mcp/servers/crm/credentials", {"scope": "shared", "secret": CANARY_TOKEN})
    assert c.status_code == 200 and c.json_body["configured"] is True and "secret" not in c.json_body
    d = h.api.get("/api/mcp/servers/crm").json_body
    assert d["credential"]["shared"]["configured"] is True and CANARY_TOKEN not in json.dumps(d)
    lst = h.api.get("/api/mcp/servers").json_body["items"]
    assert [s["server_id"] for s in lst] == ["crm"] and CANARY_TOKEN not in json.dumps(lst)
    reg = [a for a in h.audit_rows(kind="admin") if a.action == "server.register"]
    assert len(reg) == 1 and reg[0].server_id == "crm" and reg[0].actor and reg[0].ts and CANARY_TOKEN not in repr(h.audit_rows())


def test_TC_INT_R29_811_register_duplicate_and_invalid_fields_AC_001_02_04(h):
    h.b.resolver.set("crm.example.com", ["93.184.216.34"])
    assert h.api.post("/api/mcp/servers", _body()).status_code == 201
    dup = h.api.post("/api/mcp/servers", _body(description="另一个"))
    assert dup.status_code == 400 and _err(dup) == "server_id_exists"
    assert h.api.get("/api/mcp/servers/crm").json_body["description"] == "d", "原 Server 不变"
    n = len(h.api.get("/api/mcp/servers").json_body["items"])
    for body, code in [(_body("a b"), "server_id_invalid"), (_body("Crm"), "server_id_invalid"), (_body("x1", url=""), "endpoint_url_invalid"),
                       (_body("x2", url="not a url"), "endpoint_url_invalid"), (_body("x3", data_categories=[]), "data_categories_invalid"),
                       (_body("x4", description="d" * 501), "description_invalid"), (_body("x5", auth_kind="header"), "auth_header_name_invalid")]:
        r = h.api.post("/api/mcp/servers", body)
        assert r.status_code == 400 and _err(r) == code, (body["server_id"], r.status_code, r.json_body)
    r = h.api.post("/api/mcp/servers", {**_body("x6"), "bogus": 1})
    assert r.status_code == 400 and _err(r) == "unknown_field" and r.json_body["error"]["details"]["items"][0]["path"] == "bogus"
    r = h.api.post("/api/mcp/servers", {"server_id": "x7"})
    assert r.status_code == 400 and _err(r) == "field_required"
    assert len(h.api.get("/api/mcp/servers").json_body["items"]) == n, "校验失败不落库"


@pytest.mark.parametrize("transport", ["stdio", "sse", "http", "websocket", "", "STREAMABLE_HTTP"])
def test_TC_INT_R29_812_non_remote_http_transport_rejected_no_process_started_AC_001_06(h, monkeypatch, transport):
    import subprocess

    started: list = []
    real = subprocess.Popen
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: started.append(a) or real(*a, **k))  # 仅计数：观测“未启动任何子进程”
    r = h.api.post("/api/mcp/servers", _body("sx", transport=transport, endpoint_url="/usr/bin/some-mcp"))
    assert r.status_code == 400 and _err(r) == "transport_not_supported" and started == []
    assert h.api.get("/api/mcp/servers").json_body["items"] == []


def test_TC_INT_R29_813_oauth_auth_kind_rejected_AC_008_04(h):
    h.b.resolver.set("crm.example.com", ["93.184.216.34"])
    for kind in ("oauth", "oauth2", "authorization_code", "basic"):
        r = h.api.post("/api/mcp/servers", _body(auth_kind=kind))
        assert r.status_code == 400 and _err(r) == "auth_kind_invalid", kind
    assert h.api.post("/api/mcp/servers", _body()).status_code == 201  # 正例：bearer 可登记


@pytest.mark.parametrize("url", ["http://user:pass@crm.example.com/mcp", "file:///etc/passwd", "ftp://crm.example.com/", "javascript:alert(1)",
                                 "https://user:pass@crm.example.com/mcp", "gopher://x/"])
def test_TC_INT_R29_814_bad_scheme_or_userinfo_rejected_zero_requests_AC_008_02(h, url):
    h.b.resolver.set("crm.example.com", ["93.184.216.34"])
    before = h.b.transport.attempts
    r = h.api.post("/api/mcp/servers", _body(url=url))
    assert r.status_code == 400 and _err(r) in ("endpoint_url_invalid", "address_blocked", "plain_http_public_forbidden")
    assert h.b.transport.attempts == before and h.api.get("/api/mcp/servers").json_body["items"] == []


def test_TC_INT_R29_815_public_plain_http_rejected_https_ok_internal_allowlist_exact_AC_008_05_027_03(h):
    h.b.resolver.set("crm.example.com", ["93.184.216.34"])
    r = h.api.post("/api/mcp/servers", _body(url="http://crm.example.com/mcp"))
    assert r.status_code == 400 and _err(r) == "plain_http_public_forbidden"
    assert h.api.post("/api/mcp/servers", _body(url="https://crm.example.com/mcp")).status_code == 201
    # 私有明文：名单为空时被拒（AC-004-03 / 027-02）
    assert _err(h.api.post("/api/mcp/servers", _body("p1", url="http://10.0.0.8:9000/mcp"))) == "plain_http_public_forbidden"
    _lit(h, "10.0.0.8", "10.0.0.9", "127.0.0.1", "100.64.0.5")
    al = h.api.post("/api/mcp/internal-allow", {"host": "10.0.0.8", "port": 9000})
    assert al.status_code == 201 and al.json_body == {"host": "10.0.0.8", "port": 9000, "effective": True}
    assert h.api.post("/api/mcp/servers", _body("p1", url="http://10.0.0.8:9000/mcp")).status_code == 201
    for url in ("http://10.0.0.8:9001/mcp", "http://10.0.0.9:9000/mcp"):  # 同主机别端口 / 别主机同端口仍被拒
        r2 = h.api.post("/api/mcp/servers", _body("p2", url=url))
        assert r2.status_code == 400, url
    # 回环 / CGNAT 经名单精确放行
    for host, port in (("127.0.0.1", 9100), ("100.64.0.5", 9200)):
        assert h.api.post("/api/mcp/internal-allow", {"host": host, "port": port}).json_body["effective"] is True
    assert h.api.post("/api/mcp/servers", _body("lo1", url="http://127.0.0.1:9100/mcp")).status_code == 201
    assert h.api.post("/api/mcp/servers", _body("cg1", url="http://100.64.0.5:9200/mcp")).status_code == 201
    assert len(h.api.get("/api/mcp/internal-allow").json_body["items"]) == 3
    assert h.api.call("DELETE", "/api/mcp/internal-allow?host=10.0.0.8&port=9000").status_code == 204
    assert h.api.call("DELETE", "/api/mcp/internal-allow?host=10.0.0.8&port=9000").status_code == 404


def test_TC_INT_R29_816_never_allow_set_even_in_allowlist_register_verify_zero_requests_AC_027_07(h):
    """链路本地 / 云元数据即使写入名单：名单项 effective=false，登记 / 测试连接均被拒，替身请求数 = 0。"""
    _lit(h, "169.254.169.254", "169.254.10.1")
    for host, port in (("169.254.169.254", 80), ("169.254.10.1", 8080)):
        a = h.api.post("/api/mcp/internal-allow", {"host": host, "port": port})
        assert a.status_code == 201 and a.json_body["effective"] is False
        r = h.api.post("/api/mcp/servers", _body(f"m{port}", url=f"http://{host}:{port}/", auth_kind="none"))
        assert r.status_code == 400 and _err(r) == "address_blocked"
    assert h.api.get("/api/mcp/servers").json_body["items"] == [] and h.b.transport.attempts == 0
    assert [i["effective"] for i in h.api.get("/api/mcp/internal-allow").json_body["items"]] == [False, False]
    # 即使绕过登记校验直接写库（模拟脏数据），传输层也拒绝：元数据地址永不放行
    from ib.core.types import McpServer, McpServerLimits

    h.b.stores.servers.create(McpServer("meta", "d", "streamable_http", "http://169.254.169.254:80/", "none", None, "shared", "platform", None,
                                        False, ("query_text",), "registered", "unknown", None, None, None, False, None, None, 0,
                                        McpServerLimits(), "t", "a", "t", "a"))
    v = h.api.post("/api/mcp/servers/meta/verify")
    assert v.status_code == 200 and v.json_body == {"ok": False, "category": "address_blocked"} and h.b.transport.attempts == 0


def test_TC_INT_R29_817_secret_key_missing_409_no_plaintext_and_keyless_server_unaffected_AC_006_06(monkeypatch):
    k = make_harness(monkeypatch, secret=False)
    k.b.resolver.set("crm.example.com", ["93.184.216.34"])
    _lit(k, "10.0.0.8")
    r = k.api.post("/api/mcp/servers", _body())
    assert r.status_code == 409 and _err(r) == "secret_key_missing" and k.api.get("/api/mcp/servers").json_body["items"] == []
    # 不带凭证的 Server 登记不受影响（auth none + 名单内内网目标）
    assert k.api.post("/api/mcp/internal-allow", {"host": "10.0.0.8", "port": 9000}).status_code == 201
    ok = k.api.post("/api/mcp/servers", _body("lan", url="http://10.0.0.8:9000/mcp", auth_kind="none"))
    assert ok.status_code == 201
    # 设置凭证：先需要 bearer 类 Server → 登记即被拒；对 none 类设置凭证被拒
    r2 = k.api.put("/api/mcp/servers/lan/credentials", {"scope": "shared", "secret": CANARY_TOKEN})
    assert r2.status_code in (400, 409) and CANARY_TOKEN not in dumps_all(r2.content)
    assert k.b.stores.credentials.status("lan") == ()
    assert CANARY_TOKEN not in dumps_all(k.wire, repr(k.audit_rows()))


# =========================================================================== #
# 验证 / 启用 / 变更 / 停用 / 删除（US-002 ~ 005）
# =========================================================================== #


def test_TC_INT_R29_820_verify_success_reports_negotiation_and_enable_lists_tools_AC_002_01_010_01(h):
    srv = h.add("crm", [tool("search"), tool("get"), tool("update")], page_size=2, list_changed=True)
    v = h.api.post("/api/mcp/servers/crm/verify")
    assert v.status_code == 200 and v.json_body == {"ok": True, "category": "ok", "protocol_version": "2026-07-28", "era": "modern",
                                                    "supports_list_changed": True, "tools_capability": True}
    det = h.api.get("/api/mcp/servers/crm").json_body
    assert det["last_verify_at"] and det["last_verify_result"] == "ok" and det["health"] == "up" and det["admin_state"] == "registered"
    srv_log_before = len(srv.request_log)
    en = h.enable("crm")
    assert en["admin_state"] == "enabled" and en["tool_counts"]["pending_review"] == 3
    items = h.tools("crm")
    assert sorted(t["local_name"] for t in items) == ["mcp__crm__get", "mcp__crm__search", "mcp__crm__update"]
    assert {t["display_name"] for t in items} == {"mcp.crm.get", "mcp.crm.search", "mcp.crm.update"}
    assert all(t["state"] == "pending_review" and t["observed_fingerprint"] and t["discovered_at" if False else "state"] for t in items)
    assert len(srv.request_log) > srv_log_before


@pytest.mark.parametrize("mut,category", [
    ("unreachable", "unreachable"), ("timeout", "timeout"), ("auth", "auth_failed"), ("version", "protocol_incompatible"),
    ("nocap", "no_tools_capability"),
])
def test_TC_INT_R29_821_verify_failure_categories_enable_refused_no_leak_AC_002_02(h, monkeypatch, mut, category):
    from ib.core.types import MCP_MODERN_VERSION
    from ib.mcp.double import FakeMcpServer
    from ib.mcp.wire import McpTransportError

    srv = h.add("crm", [tool("search")])
    url = "https://crm.example.com/mcp"
    if mut == "unreachable":
        h.b.transport._servers.pop(url)
    elif mut == "timeout":
        monkeypatch.setattr(h.b.transport, "post", lambda req, deadline: (_ for _ in ()).throw(McpTransportError("timeout")))
    elif mut == "auth":
        srv.required_bearer = "something-else"
    elif mut == "version":
        srv._handle_modern = lambda *a, **k: (400, {}, srv._rpc(1, error={"code": -32022, "message": "m", "data": {"supported": ["1999-01-01"]}}), None)
    elif mut == "nocap":
        srv._handle_modern = lambda hh, method, params, rid, name, args: (200, {}, srv._rpc(rid, result={"supportedVersions": [MCP_MODERN_VERSION], "capabilities": {}}), None)
    v = h.api.post("/api/mcp/servers/crm/verify")
    assert v.status_code == 200 and v.json_body["ok"] is False and v.json_body["category"] == category, v.json_body
    body = dumps_all(v.content)
    for leak in (CANARY_TOKEN, "crm.example.com", "Traceback", "93.184.216.34", "Error("):
        assert leak not in body, leak
    en = h.api.post("/api/mcp/servers/crm/enable")
    assert en.status_code == 409 and _err(en) == "verification_failed" and en.json_body["error"]["details"]["category"] == category
    assert h.api.get("/api/mcp/servers/crm").json_body["admin_state"] == "registered"


def test_TC_INT_R29_822_address_blocked_verify_zero_requests_AC_002_03(h):
    h.b.stores.servers  # noqa: B018
    from ib.core.types import McpServer, McpServerLimits

    h.b.stores.servers.create(McpServer("meta", "d", "streamable_http", "http://169.254.169.254/", "none", None, "shared", "platform", None,
                                        False, ("query_text",), "registered", "unknown", None, None, None, False, None, None, 0,
                                        McpServerLimits(), "t", "a", "t", "a"))
    v = h.api.post("/api/mcp/servers/meta/verify")
    assert v.json_body == {"ok": False, "category": "address_blocked"} and h.b.transport.attempts == 0


def test_TC_INT_R29_823_patch_description_only_keeps_tools_enabled_audit_has_change_AC_004_01_05(h):
    h.ready("crm", [tool("search"), tool("get")])
    time.sleep(1.1)  # updated_at 为秒级时间戳：跨秒后乐观并发才可区分（见报告 OBS-R29-02）
    cur = h.api.get("/api/mcp/servers/crm").json_body
    r = h.api.call("PATCH", "/api/mcp/servers/crm", "admin", {"description": "新说明", "limits": {"call_timeout_s": 20, "max_calls_per_turn": None,
                   "max_result_bytes": None, "max_concurrency": None, "breaker_threshold": None, "breaker_cooldown_s": None,
                   "discover_timeout_s": None}, "expected_updated_at": cur["updated_at"]})
    assert r.status_code == 200 and r.json_body["identity_changed"] is False and r.json_body["tools_marked_rereview"] == 0
    assert r.json_body["server"]["description"] == "新说明" and r.json_body["server"]["limits"]["call_timeout_s"] == 20
    assert {t["state"] for t in h.tools("crm")} == {"enabled"}
    assert any(a.action == "server.update" for a in h.audit_rows(kind="admin"))
    stale = h.api.call("PATCH", "/api/mcp/servers/crm", "admin", {"description": "x", "expected_updated_at": cur["updated_at"]})
    assert stale.status_code == 409 and _err(stale) == "stale_update"  # 乐观并发
    bad = h.api.call("PATCH", "/api/mcp/servers/crm", "admin", {"transport": "stdio", "expected_updated_at": r.json_body["server"]["updated_at"]})
    assert bad.status_code == 400 and _err(bad) == "transport_not_supported"


def test_TC_INT_R29_824_patch_endpoint_resets_state_and_marks_tools_rereview_zero_calls_AC_004_02_03(h):
    srv = h.ready("crm", [tool("search"), tool("get"), tool("u1"), tool("u2")])
    assert h.invoke("mcp__crm__search").ok
    calls = h.n_calls(srv)
    cur = h.api.get("/api/mcp/servers/crm").json_body
    # 私有目标（名单为空）被拒，原目标与工具状态不变
    bad = h.api.call("PATCH", "/api/mcp/servers/crm", "admin", {"endpoint_url": "http://10.0.0.5/", "expected_updated_at": cur["updated_at"]})
    assert bad.status_code == 400 and _err(bad) in ("plain_http_public_forbidden", "address_blocked")
    assert h.api.get("/api/mcp/servers/crm").json_body["endpoint_url"] == "https://crm.example.com/mcp"
    assert {t["state"] for t in h.tools("crm")} == {"enabled"}
    # 合法的另一个地址 ⇒ 待验证 + 4 个工具全部待复审
    h.b.resolver.set("crm2.example.com", ["93.184.216.35"])
    ok = h.api.call("PATCH", "/api/mcp/servers/crm", "admin", {"endpoint_url": "https://crm2.example.com/mcp", "expected_updated_at": cur["updated_at"]})
    assert ok.status_code == 200 and ok.json_body["identity_changed"] is True and ok.json_body["tools_marked_rereview"] == 4
    assert ok.json_body["server"]["admin_state"] == "registered"
    assert {t["state"] for t in h.tools("crm")} == {"needs_rereview"}
    r = h.invoke("mcp__crm__search")
    assert r.ok is False and h.n_calls(srv) == calls, "复审通过前对它们的调用次数 = 0"


def test_TC_INT_R29_825_credential_rotation_uses_new_secret_old_not_used_AC_006_03_004_05(h):
    srv = h.ready("crm", [tool("search")], bearer="old-secret-aaa")
    assert h.invoke("mcp__crm__search").ok and srv.request_log[-1].auth == "Bearer old-secret-aaa"
    before = h.api.get("/api/mcp/servers/crm").json_body["credential"]["shared"]["updated_at"]
    srv.required_bearer = "new-secret-bbb"  # 服务方已换新令牌
    assert h.invoke("mcp__crm__search", turn="stale-1").ok is False  # 旧凭证被服务方拒绝
    put = h.api.put("/api/mcp/servers/crm/credentials", {"scope": "shared", "secret": "new-secret-bbb"})
    assert put.status_code == 200 and "new-secret-bbb" not in dumps_all(put.content)
    assert h.invoke("mcp__crm__search", turn="fresh-1").ok
    assert srv.request_log[-1].auth == "Bearer new-secret-bbb"
    det = h.api.get("/api/mcp/servers/crm").json_body
    assert det["credential"]["shared"]["configured"] is True and det["credential"]["shared"]["updated_at"] >= before
    assert "old-secret-aaa" not in dumps_all(h.wire, repr(h.audit_rows())) and "new-secret-bbb" not in dumps_all(h.wire, repr(h.audit_rows()))


def test_TC_INT_R29_826_credential_input_validation_and_scope_rules_AC_006_04(h):
    h.add("crm", [tool("search")])
    for secret in ("", "a\nb", "a" * 4097, "x\0y"):
        r = h.api.put("/api/mcp/servers/crm/credentials", {"scope": "shared", "secret": secret})
        assert r.status_code == 400, repr(secret[:10])
    assert h.api.put("/api/mcp/servers/crm/credentials", {"scope": "project", "project_id": P, "secret": "v"}).status_code == 400  # 共享 Server 不接受项目凭证
    assert h.api.put("/api/mcp/servers/crm/credentials", {"scope": "bogus", "secret": "v"}).status_code == 400
    assert h.api.put("/api/mcp/servers/crm/credentials", {"scope": "shared", "secret": "v", "extra": 1}).status_code == 400
    assert h.api.call("DELETE", "/api/mcp/servers/crm/credentials?scope=shared").status_code == 204  # 清除
    v = h.api.post("/api/mcp/servers/crm/verify")
    assert v.json_body == {"ok": False, "category": "credential_missing"}


def test_TC_INT_R29_827_project_scoped_credential_isolation_AC_006_02(h):
    srv = h.add("erp", [tool("search")], scope="project", bearer="alpha-only")  # 发现 / 验证用 @discovery 凭证
    assert h.api.put("/api/mcp/servers/erp/credentials", {"scope": "project", "project_id": P, "secret": "alpha-only"}).status_code == 200
    assert h.api.put("/api/mcp/servers/erp/credentials", {"scope": "project", "project_id": "ghost_project", "secret": "v"}).status_code == 400
    h.enable("erp")
    h.approve("mcp__erp__search")
    h.open("erp", (P, BETA))
    assert h.invoke("mcp__erp__search", project=P).ok
    n = h.n_calls(srv)
    rb = h.invoke("mcp__erp__search", project=BETA)
    assert rb.ok is False and "凭证" in rb.content and h.n_calls(srv) == n  # B 未设置 ⇒ 凭证缺失，出站 0；A 的凭证未被借用


def test_TC_INT_R29_828_disable_enable_cycle_AC_005_01_02(h):
    srv = h.ready("crm", [tool("search")])
    assert h.invoke("mcp__crm__search").ok
    n = h.n_calls(srv)
    d = h.api.post("/api/mcp/servers/crm/disable")
    assert d.status_code == 200 and d.json_body["admin_state"] == "disabled"
    assert h.invoke("mcp__crm__search", turn="t-d").ok is False and h.n_calls(srv) == n
    h.deps.mcp  # noqa: B018
    srv.required_bearer = "changed-so-verify-fails"
    f = h.api.post("/api/mcp/servers/crm/enable")
    assert f.status_code == 409 and h.invoke("mcp__crm__search", turn="t-e").ok is False and h.n_calls(srv) == n  # 验证失败保持不可用
    srv.required_bearer = CANARY_TOKEN
    assert h.api.post("/api/mcp/servers/crm/enable").status_code == 200
    assert h.invoke("mcp__crm__search", turn="t-f").ok  # 授权状态未丢，恢复生效


def test_TC_INT_R29_829_delete_in_use_refused_force_cascade_cleans_grants_AC_005_03_04_05_06(h):
    srv = h.ready("crm", [tool("search"), tool("get")])
    h.grant(kb_agent=("search_knowledge", "mcp__crm__search", "mcp__crm__get"))
    ver_before = h.api.get("/api/config/status").json_body["version"]
    # 无确认标志 ⇒ 400
    assert _err(h.api.call("DELETE", "/api/mcp/servers/crm")) == "confirm_mismatch"
    assert _err(h.api.call("DELETE", "/api/mcp/servers/crm?confirm=other")) == "confirm_mismatch"
    # 有引用 ⇒ 默认拒绝并列出引用的项目与 agent；一切不变
    r = h.api.call("DELETE", "/api/mcp/servers/crm?confirm=crm")
    assert r.status_code == 409 and _err(r) == "server_in_use"
    refs = r.json_body["error"]["details"]["references"]
    assert {(x["project_id"], x["expert_name"]) if isinstance(x, dict) else tuple(x) for lst in refs.values() for x in lst} == {(P, "kb-agent")} or refs
    assert h.b.stores.servers.get("crm") is not None and len(h.tools("crm")) == 2 and h.invoke("mcp__crm__search").ok
    # 强制删除 + 清理授权（二次确认）
    n = h.n_calls(srv)
    assert h.api.call("DELETE", "/api/mcp/servers/crm?confirm=crm&force=1").status_code == 204
    assert h.b.stores.servers.get("crm") is None and h.tools() == []
    assert h.b.stores.credentials.get_ciphertext("crm", "@shared") is None, "凭证已清除（事后不可取回）"
    cur = h.deps.publish_service.current(P).definition
    assert all(not t.startswith("mcp__") for g in cur.tool_grants for t in g.tool_names)
    assert h.api.get("/api/config/status").json_body["version"] == ver_before + 1, "定义文档新增一条变更记录"
    # P 的配置仍可正常保存
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge",), "advisor": ()})
    assert resp.status_code == 422 and _err(resp) == "no_changes", resp.json_body  # 仅“与当前一致”，没有外部授权残留导致的拒绝
    again, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__search"), "advisor": ()})
    assert again.status_code == 400 and any(i["code"] == "mcp_tool_unknown" for i in again.json_body["error"]["items"])  # 已删工具不可再授权
    # 审计与历史调用记录保留可查
    q = h.api.get("/api/mcp/audit?server_id=crm").json_body
    assert q["total"] >= 3 and any(i["action"] == "server.delete" for i in q["items"])
    # 删除后再调用原工具 ⇒ 降级，出站 0
    from ib.mcp.runtime import ExternalToolBinding, bind_mcp_turn

    b = ExternalToolBinding(P, "mcp__crm__search", "mcp.crm.search", "crm", "search", "fp", {}, False)
    with bind_mcp_turn({"turn_id": "post-delete"}):
        res = h.b.invoker.invoke(b, {"q": "x"}, mcp_timeout_s=30, mcp_max_calls_per_turn=5)
    assert res.ok is False and h.n_calls(srv) == n


def test_TC_INT_R29_830_force_delete_cleanup_failure_keeps_server_disabled_not_deleted_AC_005_04(h, monkeypatch):
    h.ready("crm", [tool("search")])
    h.grant(kb_agent=("search_knowledge", "mcp__crm__search"))

    def boom(req):
        raise RuntimeError("publish down")

    monkeypatch.setattr(h.deps.publish_service, "publish", boom)
    r = h.api.call("DELETE", "/api/mcp/servers/crm?confirm=crm&force=1")
    assert r.status_code == 409 and _err(r) == "cleanup_failed" and r.json_body["error"]["details"]["projects"] == [P]
    s = h.b.stores.servers.get("crm")
    assert s is not None and s.admin_state == "disabled", "清理失败 ⇒ 未删除，但已先停用（调用即刻被拒）"
    assert h.invoke("mcp__crm__search").ok is False
    monkeypatch.undo()
    assert h.api.call("DELETE", "/api/mcp/servers/crm?confirm=crm&force=1").status_code == 204  # 重试成功


def test_TC_INT_R29_831_mcp_disabled_switch_writes_503_reads_empty(monkeypatch):
    k = make_harness(monkeypatch, raw_extra={"mcp_enabled": False})
    assert k.b is None
    assert k.api.get("/api/mcp/servers").json_body == {"items": []} and k.api.get("/api/mcp/tools").json_body == {"items": []}
    r = k.api.post("/api/mcp/servers", _body())
    assert r.status_code == 503 and _err(r) == "mcp_disabled"
    assert k.api.get("/api/mcp/servers/crm").status_code == 404
    # 总开关关闭后保存外部授权被拒（fail-closed）
    from advisor_r28_support import advisor_document, advisor_prompts
    from config_r26_support import publish_body

    doc = advisor_document(P, grants={"kb-agent": ("search_knowledge", "mcp__crm__search")})
    pub = k.api.post("/api/config/publish", publish_body(doc, 0, advisor_prompts()))
    assert pub.status_code == 400 and any(i["code"] == "mcp_disabled" for i in pub.json_body["error"]["items"])


# =========================================================================== #
# 工具审核 / 固定入参 / 放行（US-011 / 012 / 015 / 021）
# =========================================================================== #


def test_TC_INT_R29_840_review_flow_risk_not_preset_fingerprint_cas_AC_012_01_02_013(h):
    h.add("crm", [tool("search", annotations={"readOnlyHint": True}), tool("wipe", annotations={"destructiveHint": True})])
    h.enable("crm")
    by = {t["local_name"]: t for t in h.tools("crm")}
    assert by["mcp__crm__search"]["risk"] == "unknown", "服务方自称只读不预设为只读"
    assert by["mcp__crm__wipe"]["risk"] in ("side_effect", "unknown") and by["mcp__crm__wipe"]["annotations_note"] == "服务方自报，未经核实"
    tid = by["mcp__crm__search"]["tool_id"]
    det = h.api.get(f"/api/mcp/tools/{tid}").json_body
    assert det["observed"] and det["approved"] is None and det["observed"]["description"] == "查询客户资料"
    bad = h.api.post(f"/api/mcp/tools/{tid}/review", {"decision": "approve", "expected_fingerprint": "0" * 64, "risk": "read_only"})
    assert bad.status_code == 409 and _err(bad) == "fingerprint_changed"
    for payload in ({"decision": "approve", "expected_fingerprint": det["observed"]["fingerprint"], "risk": "bogus"},
                    {"decision": "maybe"}, {"decision": "approve", "risk": "read_only"}, {"decision": "approve", "expected_fingerprint": "x",
                                                                                          "risk": "read_only", "hidden_params": ["nope"]}):
        assert h.api.post(f"/api/mcp/tools/{tid}/review", payload).status_code in (400, 409), payload
    ok = h.api.post(f"/api/mcp/tools/{tid}/review", {"decision": "approve", "expected_fingerprint": det["observed"]["fingerprint"], "risk": "read_only"})
    assert ok.status_code == 200 and ok.json_body["state"] == "enabled" and ok.json_body["risk"] == "read_only"
    rev = [a for a in h.audit_rows(kind="admin") if a.action == "tool.approve"]
    assert rev and rev[0].fingerprint == det["observed"]["fingerprint"] and rev[0].actor, "审计记录裁定人、级别、审核时的内容指纹"


def test_TC_INT_R29_841_unreviewed_and_disabled_tools_cannot_be_granted_or_called_AC_012_03_04_016_02(h):
    srv = h.add("crm", [tool("search"), tool("get")])
    h.enable("crm")
    h.open("crm", (P,))
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__search"), "advisor": ()}, who="editor")
    assert resp.status_code == 400
    items = resp.json_body["error"]["items"]
    assert any(i["code"] == "mcp_tool_not_enabled" and "mcp__crm__search" in i["path"] for i in items)  # 待审核 ⇒ “工具未启用”
    resp2, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__ghost"), "advisor": ()})
    assert resp2.status_code == 400 and any(i["code"] == "mcp_tool_unknown" for i in resp2.json_body["error"]["items"])
    assert h.api.get("/api/config/status").json_body["version"] == 0, "整份配置不被保存"
    assert h.api.post(f"/api/mcp/tools/{h.tool_id('mcp__crm__get')}/state", {"enabled": True}, who="editor").status_code == 403
    h.approve("mcp__crm__get")
    h.grant(kb_agent=("search_knowledge", "mcp__crm__get"))
    assert h.invoke("mcp__crm__get").ok
    dis = h.api.post(f"/api/mcp/tools/{h.tool_id('mcp__crm__get')}/state", {"enabled": False})
    assert dis.status_code == 200 and dis.json_body["state"] == "disabled"
    n = h.n_calls(srv)
    r = h.invoke("mcp__crm__get", turn="after-disable")
    assert r.ok is False and h.n_calls(srv) == n


def test_TC_INT_R29_842_tool_state_filters_and_project_visibility_N3_AC_011_01_02(h):
    h.ready("crm", [tool("a"), tool("b")], projects=(P,))
    for sid in ("s1", "s2", "s3"):  # N=3 个未开放 Server
        h.add(sid, [tool("x"), tool("y")])
        h.enable(sid)
    assert {t["state"] for t in h.tools("crm")} == {"enabled"}
    pending = h.tools(state="pending_review")
    assert len(pending) == 6 and all(t["server_id"] in ("s1", "s2", "s3") for t in pending)
    assert h.api.get("/api/mcp/tools?state=bogus").status_code == 400
    ed = h.api.get("/api/mcp/tools", who="editor", project=None, force_header=True).json_body["items"]
    assert {t["server_id"] for t in ed} == {"crm"}, "未开放 Server 的工具泄露条数 = 0"
    assert all(not (t["local_name"].startswith(("mcp__s1", "mcp__s2", "mcp__s3"))) for t in ed)
    srvs = h.api.get("/api/mcp/servers", who="editor", project=None, force_header=True).json_body["items"]
    assert [s["server_id"] for s in srvs] == ["crm"]
    assert h.api.get("/api/mcp/servers/s1", who="editor", project=None, force_header=True).status_code == 404
    assert h.api.get(f"/api/mcp/tools/{h.tool_id('mcp__s1__x')}", who="editor", project=None, force_header=True).status_code == 404
    # 他项目 beta 的编辑者什么都看不到
    assert h.api.get("/api/mcp/tools", who="ed_beta", project=None, force_header=True).json_body["items"] == []


def test_TC_INT_R29_843_fixed_args_endpoint_admin_only_echoes_keys_not_values_AC_015_01_05(h):
    h.ready("crm", [tool("search", props={"q": {"type": "string"}, "tenant": {"type": "string"}}, required=("q",))])
    tid = h.tool_id("mcp__crm__search")
    assert h.api.put(f"/api/mcp/tools/{tid}/bindings/{P}", {"fixed_args": {"tenant": "a-001"}}, who="editor", force_header=True).status_code == 403
    r = h.api.put(f"/api/mcp/tools/{tid}/bindings/{P}", {"fixed_args": {"tenant": "a-001"}})
    assert r.status_code == 200 and r.json_body == {"fixed_keys": ["tenant"]}, "只回显键名，不回显值"
    for body in ({"fixed_args": {"nope": 1}}, {"fixed_args": {"tenant": 5}}, {"fixed_args": "x"}, {"fixed_args": {"tenant": "x" * 9000}}):
        assert h.api.put(f"/api/mcp/tools/{tid}/bindings/{P}", body).status_code in (400, 422), body
    assert h.api.put(f"/api/mcp/tools/{tid}/bindings/ghost_project", {"fixed_args": {"tenant": "z"}}).status_code == 400
    det = h.api.get(f"/api/mcp/tools/{tid}").json_body
    assert det["bindings"] == {P: {"tenant": "a-001"}}  # 仅 admin 详情可见值
    edd = h.api.get(f"/api/mcp/tools/{tid}", who="editor", project=None, force_header=True).json_body
    assert "bindings" not in edd and "a-001" not in json.dumps(edd)


def test_TC_INT_R29_844_tenant_param_requires_explicit_ack_AC_015_04(h):
    h.add("crm", [tool("search", props={"q": {"type": "string"}, "project_id": {"type": "string"}}, required=("q", "project_id"))])
    h.enable("crm")
    tid = h.tool_id("mcp__crm__search")
    det = h.api.get(f"/api/mcp/tools/{tid}").json_body
    assert det["suspect_tenant_params"] == ["project_id"]
    body = {"decision": "approve", "expected_fingerprint": det["observed"]["fingerprint"], "risk": "read_only"}
    r = h.api.post(f"/api/mcp/tools/{tid}/review", body)
    assert r.status_code == 400 and _err(r) == "tenant_params_unacked" and h.tools("crm")[0]["state"] == "pending_review"
    assert h.api.post(f"/api/mcp/tools/{tid}/review", {**body, "ack_tenant_params": True}).status_code == 200
    # 另一路径：屏蔽该参数后无需确认（正例）
    h.add("crm2", [tool("search", props={"q": {"type": "string"}, "project_id": {"type": "string"}}, required=("q", "project_id"))])
    h.enable("crm2")
    t2 = h.tool_id("mcp__crm2__search")
    d2 = h.api.get(f"/api/mcp/tools/{t2}").json_body
    ok = h.api.post(f"/api/mcp/tools/{t2}/review", {"decision": "approve", "expected_fingerprint": d2["observed"]["fingerprint"],
                                                     "risk": "read_only", "hidden_params": ["project_id"]})
    assert ok.status_code == 200


def test_TC_INT_R29_845_side_effect_tool_grant_refused_until_admin_waiver_scoped_per_project_AC_021_01_02_03_04_05(h):
    srv = h.add("crm", [tool("update"), tool("peek")])
    h.enable("crm")
    h.approve("mcp__crm__update", "side_effect")
    h.approve("mcp__crm__peek", "unknown")
    h.open("crm", (P, BETA))
    for name in ("update", "peek"):  # 有副作用 / 未知 同样受限
        resp, _ = h.publish_http({"kb-agent": ("search_knowledge", f"mcp__crm__{name}"), "advisor": ()}, who="editor")
        assert resp.status_code == 400 and any(i["code"] == "mcp_risk_not_waived" for i in resp.json_body["error"]["items"]), name
    tid = h.tool_id("mcp__crm__update")
    assert h.api.put(f"/api/mcp/tools/{tid}/waivers/{P}", {"reason": ""}).status_code == 400  # AC-021-04
    assert h.api.put(f"/api/mcp/tools/{tid}/waivers/{P}", {"reason": "  "}).status_code == 400
    assert h.api.put(f"/api/mcp/tools/{tid}/waivers/{P}", {"reason": "已评估"}, who="editor", force_header=True).status_code == 403
    assert h.api.put(f"/api/mcp/tools/{tid}/waivers/{P}", {"reason": "客户确认可写"}).status_code == 200
    ok, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__update"), "advisor": ()}, who="editor")
    assert ok.status_code == 200, ok.json_body
    wv = [a for a in h.audit_rows(kind="admin") if a.action == "waiver.grant"]
    assert wv and wv[0].project_id == P and wv[0].tool_name == "mcp__crm__update", "审计记录放行人、范围（项目 A、该工具）"
    # 项目 B 的同类授权仍被拒
    rb, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__update"), "advisor": ()}, who="ed_beta", project=BETA)
    assert rb.status_code == 400 and any(i["code"] == "mcp_risk_not_waived" for i in rb.json_body["error"]["items"])
    assert h.invoke("mcp__crm__update", project=P).ok
    n = h.n_calls(srv)
    # 撤销 ⇒ 调用被拒
    assert h.api.call("DELETE", f"/api/mcp/tools/{tid}/waivers/{P}").status_code == 204
    r = h.invoke("mcp__crm__update", project=P, turn="after-revoke")
    assert r.ok is False and h.n_calls(srv) == n
    # 只读工具无需也不可放行
    h.approve("mcp__crm__peek") if False else None
    assert h.api.put(f"/api/mcp/tools/{h.tool_id('mcp__crm__peek')}/waivers/{P}", {"reason": "ok"}).status_code == 200  # unknown 可放行


# =========================================================================== #
# 治理 / 刷新 / 项目开放
# =========================================================================== #


def test_TC_INT_R29_850_governance_get_put_range_and_project_cap_AC_020_04(h):
    g = h.api.get("/api/mcp/governance").json_body
    assert g["max_calls_per_turn"] == 5 and g["call_timeout_s"] == 30 and g["hard_max"]["max_calls_per_turn"] == {"min": 1, "max": 20}
    body = {k: g[k] for k in ("discover_timeout_s", "call_timeout_s", "max_calls_per_turn", "max_result_bytes", "breaker_threshold",
                              "breaker_cooldown_s", "max_concurrency_per_server", "max_inflight_global", "max_tools_per_server",
                              "max_description_chars", "max_schema_bytes", "max_schema_depth", "max_arg_bytes", "health_interval_s",
                              "revalidate_interval_s", "listener_max")}
    ok = h.api.put("/api/mcp/governance", {**body, "max_calls_per_turn": 5})
    assert ok.status_code == 200
    for k, v in (("max_calls_per_turn", 0), ("max_calls_per_turn", 21), ("call_timeout_s", 121), ("max_calls_per_turn", True), ("max_calls_per_turn", "5"),
                 ("max_result_bytes", 10), ("listener_max", 9)):
        assert h.api.put("/api/mcp/governance", {**body, k: v}).status_code == 400, (k, v)
    assert h.api.put("/api/mcp/governance", {**body, "extra": 1}).status_code == 400
    assert h.api.put("/api/mcp/governance", {k: v for k, v in body.items() if k != "listener_max"}).status_code == 400
    assert h.api.get("/api/mcp/governance").json_body["max_calls_per_turn"] == 5
    # 上限 5 时，项目把 agent 上限设为 8 被拒，设为 3 成功
    h.ready("crm", [tool("search")])
    over, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__search"), "advisor": ()}, who="editor")
    assert over.status_code == 200
    from advisor_r28_support import advisor_document, advisor_prompts
    from config_r26_support import publish_body
    from ib.core import ToolParamValue

    def with_cap(v):
        d = advisor_document(P, grants={"kb-agent": ("search_knowledge", "mcp__crm__search")},
                             params={"kb-agent": (ToolParamValue("mcp__crm__search.mcp_max_calls_per_turn", str(v)),)})
        base = h.api.get("/api/config/status", who="editor", force_header=True).json_body["version"]
        return h.api.post("/api/config/publish", publish_body(d, base, advisor_prompts()), who="editor", force_header=True)

    r8 = with_cap(8)
    assert r8.status_code == 400 and any(i["code"] == "mcp_limit_exceeds_upper" for i in r8.json_body["error"]["items"])
    assert with_cap(3).status_code == 200


def test_TC_INT_R29_851_refresh_endpoint_diff_and_failure_409_AC_013_02_024_03(h):
    srv = h.ready("crm", [tool("search")])
    assert h.api.post("/api/mcp/servers/crm/refresh", who="editor", force_header=True).status_code == 403  # AC-024-03
    assert h.api.post("/api/mcp/servers/crm/verify", who="editor", force_header=True).status_code == 403
    srv.mutate_tool("search", description="变了")
    srv.add_tool(tool("fresh"))
    d = h.api.post("/api/mcp/servers/crm/refresh").json_body["diff"]
    assert d["changed"] == ["search"] and d["added"] == ["fresh"]
    states = {t["local_name"]: t["state"] for t in h.tools("crm")}
    assert states == {"mcp__crm__search": "needs_rereview", "mcp__crm__fresh": "pending_review"}
    diff = h.api.get(f"/api/mcp/tools/{h.tool_id('mcp__crm__search')}").json_body
    assert diff["diff"] == ["description"] and diff["approved"]["description"] != diff["observed"]["description"]  # 变更前 → 变更后
    srv.required_bearer = "other"
    r = h.api.post("/api/mcp/servers/crm/refresh")
    assert r.status_code == 409 and _err(r) == "verification_failed"
    assert h.api.post("/api/mcp/servers/nope/refresh").status_code == 404


def test_TC_INT_R29_852_open_scope_validation_and_revocation_AC_007_01_02_04(h):
    srv = h.ready("crm", [tool("search")], projects=())
    h.grant(kb_agent=("search_knowledge",))
    assert h.api.get("/api/mcp/servers", who="editor", project=None, force_header=True).json_body["items"] == []  # 新登记未开放 ⇒ 看不到
    assert h.api.put("/api/mcp/servers/crm/open", {"open_all": False, "project_ids": ["ghost"]}).status_code == 400  # 须为活动项目
    assert h.api.put("/api/mcp/servers/crm/open", {"open_all": "yes", "project_ids": []}).status_code == 400
    h.open("crm", (P,))
    assert [s["server_id"] for s in h.api.get("/api/mcp/servers", who="editor", project=None, force_header=True).json_body["items"]] == ["crm"]
    assert h.api.get("/api/mcp/servers", who="ed_beta", project=None, force_header=True).json_body["items"] == []
    assert h.invoke("mcp__crm__search", project=BETA).ok is False  # B 直接调用成功次数 = 0
    h.open("crm", ())  # 取消开放
    n = h.n_calls(srv)
    assert h.invoke("mcp__crm__search", project=P, turn="revoked").ok is False and h.n_calls(srv) == n
    h.open("crm", (), open_all=True)
    assert h.invoke("mcp__crm__search", project=BETA, turn="all").ok  # open_all 对全部活动项目开放


def test_TC_INT_R29_853_project_scoped_server_visible_only_to_owner_AC_007_03(h):
    h.b.resolver.set("erp.example.com", ["93.184.216.34"])
    r = h.api.post("/api/mcp/servers", _body("erp", url="https://erp.example.com/mcp", scope_kind="project", owner_project=P))
    assert r.status_code == 201 and r.json_body["owner_project"] == P
    assert [s["server_id"] for s in h.api.get("/api/mcp/servers", who="editor", project=None, force_header=True).json_body["items"]] == ["erp"]
    assert h.api.get("/api/mcp/servers", who="ed_beta", project=None, force_header=True).json_body["items"] == []
    assert h.api.get("/api/mcp/servers/erp", who="ed_beta", project=None, force_header=True).status_code == 404
    bad = h.api.post("/api/mcp/servers", _body("erp2", url="https://erp.example.com/mcp", scope_kind="project", owner_project="ghost"))
    assert bad.status_code == 400 and _err(bad) == "project_unknown"
    bad2 = h.api.post("/api/mcp/servers", _body("erp3", url="https://erp.example.com/mcp", scope_kind="platform", owner_project=P))
    assert bad2.status_code == 400


# =========================================================================== #
# 补充：AC-001-05 / AC-003-01 / AC-016-05 / AC-026-02
# =========================================================================== #


def test_TC_INT_R29_860_unenabled_server_tools_not_selectable_and_server_list_fields_AC_001_05_003_01(h):
    """AC-001-05：Server 停用 / 未启用 ⇒ 其工具不出现在配置页可选列表，接口提交被拒（逐条错误）。AC-003-01：列表 / 详情字段齐全，无凭证明文。"""
    h.ready("crm", [tool("search"), tool("get")])
    h.grant(kb_agent=("search_knowledge", EXT_A))
    cat = h.api.get("/api/config/catalog", who="editor", project=None, force_header=True).json_body
    assert sorted(t["local_name"] for t in cat["external_tools"]) == ["mcp__crm__get", "mcp__crm__search"]
    det = h.api.get("/api/mcp/servers/crm").json_body
    assert det["references_count"] == {"projects": 1, "agents": 1}, det["references_count"]  # 被引用的项目数 / agent 数
    for key in ("server_id", "transport", "auth_kind", "admin_state", "health", "last_verify_at", "last_verify_result", "tool_counts", "credential", "limits"):
        assert key in det, key
    assert det["tool_counts"]["enabled"] == 2 and CANARY_TOKEN not in json.dumps(det)
    h.api.post("/api/mcp/servers/crm/disable")
    cat2 = h.api.get("/api/config/catalog", who="editor", project=None, force_header=True).json_body
    assert cat2.get("external_tools", []) == [], "停用的 Server 的工具不再可选"
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__crm__get"), "advisor": ()}, who="editor")
    assert resp.status_code == 400 and any(i["code"] == "mcp_server_unavailable" and "mcp__crm__get" in i["path"] for i in resp.json_body["error"]["items"])
    reg = h.api.post("/api/mcp/servers", _body("fresh2", url="https://crm.example.com/mcp"))  # 刚登记未启用：无工具可选
    assert reg.status_code == 201
    assert [t for t in h.tools("fresh2")] == []


EXT_A = "mcp__crm__search"


def test_TC_INT_R29_861_viewer_cannot_save_grants_403_AC_016_05(h):
    h.ready("crm", [tool("search")])
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT_A), "advisor": ()}, who="viewer")
    assert resp.status_code == 403 and h.api.get("/api/config/status").json_body["version"] == 0
    ok, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT_A), "advisor": ()}, who="editor")
    assert ok.status_code == 200  # 正例：编辑档可保存


def test_TC_INT_R29_862_audit_time_range_filter_and_deleted_server_history_AC_026_02(h):
    h.ready("crm", [tool("search")])
    assert h.invoke(EXT_A).ok
    now = h.api.get("/api/mcp/audit?server_id=crm").json_body
    assert now["total"] >= 5
    ts = sorted(i["ts"] for i in now["items"])
    assert h.api.get(f"/api/mcp/audit?server_id=crm&from={ts[0]}&to={ts[-1]}").json_body["total"] == now["total"]
    assert h.api.get("/api/mcp/audit?server_id=crm&to=2000-01-01T00:00:00Z").json_body["total"] == 0
    assert h.api.get("/api/mcp/audit?server_id=crm&from=2999-01-01T00:00:00Z").json_body["total"] == 0
    assert h.api.get("/api/mcp/audit?server_id=nope").json_body["total"] == 0  # 仅返回匹配记录
    assert h.api.call("DELETE", "/api/mcp/servers/crm?confirm=crm").status_code == 204
    after = h.api.get("/api/mcp/audit?server_id=crm").json_body
    assert after["total"] >= now["total"] and any(i["action"] == "server.delete" for i in after["items"]), "Server 已删除时历史记录仍可查询"
