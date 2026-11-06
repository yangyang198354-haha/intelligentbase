"""[REV-29 / GROUP_D] 集成：HttpMcpTransport 回环契约（GR-C-003 条件 2）。

仅在本机 127.0.0.1 随机端口起临时 HTTP 服务（测试内启动、测试后关闭），**不出网**；服务端行为由产品自带的 FakeMcpServer 提供，
这里只补一层真实 HTTP 套接字外壳。覆盖：modern / legacy 时代探测、重定向不跟随、公网明文 http 拒绝（字符串判定先于 DNS）、
钉 IP 连接（Host 头保留、每次请求重新解析）、读取上限 / 超时（真实时钟）、鉴权头只在传输层展开、无 Cookie / 代理 / 压缩。

分层：integration（真实 socket + 真实 http.client 传输 + 真实 McpClient；服务端为替身）。
溯源：US-002 / 008 / 019 / 020 / 027（AC-002-01/02、008-01/02/03/05、019-04/06、020-01、027-02）。
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from mcp_r29_support import CANARY_TOKEN, tool

from ib.core.types import MCP_LEGACY_VERSION, MCP_MODERN_VERSION, McpCallRequest, McpGovernance
from ib.mcp.client import McpClient, McpClientError, McpTarget
from ib.mcp.crypto import Secret
from ib.mcp.double import FakeMcpServer
from ib.mcp.transport import HttpMcpTransport
from ib.mcp.wire import McpHttpRequest, McpTransportError
from ib.webtools.netguard import DomainRules


class Loopback:
    """127.0.0.1 临时 HTTP 服务：把请求交给 FakeMcpServer.handle；记录每次到达（路径、方法、头）。"""

    def __init__(self, server: FakeMcpServer, *, redirect_to: str | None = None, big: int = 0):
        self.server, self.redirect_to, self.big = server, redirect_to, big
        self.hits: list[dict] = []
        outer = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):  # 静默
                pass

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n)
                hdrs = {k.lower(): v for k, v in self.headers.items()}
                outer.hits.append({"path": self.path, "headers": hdrs, "body": body})
                if outer.redirect_to:
                    self.send_response(302)
                    self.send_header("Location", outer.redirect_to)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                auth = hdrs.get("authorization")
                status, rh, rbody, sc = outer.server.handle({k: v for k, v in hdrs.items() if k != "authorization"}, body, auth)
                if outer.big and b"tools/call" in body:
                    rbody = json.dumps({"jsonrpc": "2.0", "id": json.loads(body)["id"],
                                        "result": {"content": [{"type": "text", "text": "x" * outer.big}], "isError": False}}).encode()
                    status = 200
                if sc is not None and sc.delay_s > 0:
                    time.sleep(sc.delay_s)
                ctype = "application/json"
                if sc is not None and sc.sse and status == 200:
                    ctype = "text/event-stream"
                    rbody = b"data: " + rbody + b"\n\n"
                self.send_response(status)
                for k, v in rh.items():
                    self.send_header(k, v)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(rbody)))
                self.end_headers()
                try:
                    self.wfile.write(rbody)
                except OSError:
                    pass

        class _QuietServer(ThreadingHTTPServer):
            def handle_error(self, request, client_address):  # 客户端提前断开（读取上限 / 超时用例）属预期，静默
                pass

        self.httpd = _QuietServer(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(3)


@pytest.fixture()
def loops():
    made: list[Loopback] = []

    def make(server=None, **kw):
        lb = Loopback(server or FakeMcpServer(tools=[tool("search")], required_bearer=CANARY_TOKEN), **kw)
        made.append(lb)
        return lb

    yield make
    for lb in made:
        lb.close()


def _client(lbs, *, resolver=None, extra_allow=()):
    allow = frozenset({("127.0.0.1", lb.port) for lb in lbs} | set(extra_allow))
    tr = HttpMcpTransport(rules_factory=lambda: (DomainRules((), ()), allow), resolver=resolver)
    return McpClient(tr), tr


def _target(url, era=None, auth="bearer", header=None):
    return McpTarget("crm", url, auth, header, era, None)


def _dl(s=10.0):
    return time.monotonic() + s


def test_TC_INT_R29_700_modern_probe_list_call_over_real_socket_AC_002_01_019_01(loops):
    lb = loops(FakeMcpServer(era="modern", tools=[tool("search"), tool("get")], required_bearer=CANARY_TOKEN, list_changed=True))
    c, _ = _client([lb])
    tg = _target(lb.url)
    pr = c.probe(tg, Secret(CANARY_TOKEN), deadline=_dl())
    assert pr.ok and pr.negotiated.era == "modern" and pr.negotiated.version == MCP_MODERN_VERSION and pr.negotiated.supports_list_changed is True
    disc = c.list_tools(_target(lb.url, "modern"), Secret(CANARY_TOKEN), gov=McpGovernance(), deadline=_dl(), taken_local_names=set())
    assert {t.remote_name for t in disc.tools} == {"search", "get"}
    res = c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}),
                      input_schema={"type": "object", "properties": {"q": {"type": "string"}}}, max_bytes=32768, deadline=_dl())
    assert res.is_error is False and res.content[0]["text"] == "ok:search"
    first = lb.hits[0]
    assert first["headers"]["mcp-protocol-version"] == MCP_MODERN_VERSION and first["headers"]["mcp-method"] == "server/discover"
    assert first["headers"]["authorization"] == f"Bearer {CANARY_TOKEN}"  # AC-008-01：Bearer 头
    assert all(CANARY_TOKEN not in h["path"] for h in lb.hits), "令牌不得出现在 URL 中"
    assert all("cookie" not in h["headers"] for h in lb.hits) and all(h["headers"].get("accept-encoding") == "identity" for h in lb.hits)


def test_TC_INT_R29_701_legacy_era_probe_falls_back_to_initialize_with_session_AC_002_01(loops):
    lb = loops(FakeMcpServer(era="legacy", tools=[tool("search")], required_bearer=CANARY_TOKEN))
    c, _ = _client([lb])
    pr = c.probe(_target(lb.url), Secret(CANARY_TOKEN), deadline=_dl())
    assert pr.ok and pr.negotiated.era == "legacy" and pr.negotiated.version == MCP_LEGACY_VERSION
    disc = c.list_tools(_target(lb.url, "legacy"), Secret(CANARY_TOKEN), gov=McpGovernance(), deadline=_dl(), taken_local_names=set())
    assert [t.remote_name for t in disc.tools] == ["search"]
    methods = [json.loads(h["body"]).get("method") for h in lb.hits]
    assert methods[0] == "server/discover" and "initialize" in methods and "notifications/initialized" in methods
    after = [h for h, m in zip(lb.hits, methods) if m == "tools/list"]
    assert after and all(h["headers"].get("mcp-session-id", "").startswith("sess-") for h in after), "legacy 请求须带会话头"


def test_TC_INT_R29_702_pagination_over_http_AC_010_01(loops):
    lb = loops(FakeMcpServer(tools=[tool("a"), tool("b"), tool("c")], page_size=2, required_bearer=CANARY_TOKEN))
    c, _ = _client([lb])
    d = c.list_tools(_target(lb.url, "modern"), Secret(CANARY_TOKEN), gov=McpGovernance(), deadline=_dl(), taken_local_names=set())
    assert {t.remote_name for t in d.tools} == {"a", "b", "c"} and sum(1 for h in lb.hits if b"tools/list" in h["body"]) == 2


def test_TC_INT_R29_703_redirect_not_followed_private_side_receives_zero_AC_008_03(loops):
    """302 → 另一个回环端口（模拟私有地址侧）：不跟随、不读 Location；私有侧请求数 = 0；结果为 address_blocked。"""
    private_side = loops(FakeMcpServer(tools=[tool("search")], required_bearer=None))
    lb = loops(redirect_to=private_side.url)
    c, tr = _client([lb, private_side])  # 即使私有侧在名单里，也不应被访问
    pr = c.probe(_target(lb.url), Secret(CANARY_TOKEN), deadline=_dl())
    assert pr.ok is False and pr.failure == "address_blocked"
    assert len(lb.hits) == 1 and len(private_side.hits) == 0
    with pytest.raises(McpTransportError) as ei:
        tr.post(McpHttpRequest(lb.url, {"Content-Type": "application/json"}, b"{}", None), deadline=_dl())
    assert ei.value.kind == "address_blocked" and len(private_side.hits) == 0


def test_TC_INT_R29_704_public_plaintext_http_refused_before_dns_AC_008_05():
    """字符串判定先于 DNS：公网明文 http 不触发任何解析与出站；https 才会进入解析阶段（正例）。"""
    calls: list[str] = []

    def resolver(host, port, timeout):
        calls.append(host)
        return ("127.0.0.1",)

    tr = HttpMcpTransport(rules_factory=lambda: (DomainRules((), ()), frozenset()), resolver=resolver)
    with pytest.raises(McpTransportError) as ei:
        tr.post(McpHttpRequest("http://crm.example.com/mcp", {}, b"{}", None), deadline=_dl())
    assert ei.value.kind == "address_blocked" and calls == []
    with pytest.raises(McpTransportError) as ei2:  # https：进入解析阶段，解析为回环 ⇒ 地址被拒（仍无任何连接）
        tr.post(McpHttpRequest("https://crm.example.com/mcp", {}, b"{}", None), deadline=_dl())
    assert ei2.value.kind == "address_blocked" and calls == ["crm.example.com"]


@pytest.mark.parametrize("url", [
    "http://user:pass@127.0.0.1:{port}/mcp", "file:///etc/passwd", "ftp://127.0.0.1/", "http://169.254.169.254/latest/meta-data/",
    "http://127.0.0.1:{other}/mcp", "http://0x7f000001:{port}/mcp", "http://2130706433:{port}/mcp", "javascript:alert(1)",
])
def test_TC_INT_R29_705_dangerous_urls_refused_with_zero_hits_AC_008_02_027_02(loops, url):
    lb = loops()
    _, tr = _client([lb], extra_allow=[("169.254.169.254", 80)])  # 元数据地址即使在名单里也不放行
    with pytest.raises(McpTransportError) as ei:
        tr.post(McpHttpRequest(url.format(port=lb.port, other=lb.port + 1), {}, b"{}", None), deadline=_dl())
    assert ei.value.kind == "address_blocked" and lb.hits == []


def test_TC_INT_R29_706_pinned_ip_connect_keeps_host_header_and_re_resolves_each_request_AC_027_02(loops):
    """主机名只由假解析器解析（系统 DNS 无此名）→ 能连上就证明连接了钉定 IP；Host 头保留原主机名；
    每次请求重新解析：第二次解析为元数据地址（重绑到绝不放行集，即使主机名在名单内）⇒ 被拒；公网主机先公后私的重绑见 TC-UNIT-R29-122。"""
    lb = loops(FakeMcpServer(tools=[tool("search")], required_bearer=None))
    answers = [("127.0.0.1",), ("169.254.169.254",)]

    def resolver(host, port, timeout):
        return answers[0] if len(answers) == 1 else answers.pop(0)

    allow = frozenset({("pinned.test", lb.port)})
    tr = HttpMcpTransport(rules_factory=lambda: (DomainRules((), ()), allow), resolver=resolver)
    resp = tr.post(McpHttpRequest(f"http://pinned.test:{lb.port}/mcp", {"Content-Type": "application/json"},
                                  json.dumps({"jsonrpc": "2.0", "id": 1, "method": "server/discover"}).encode(), None), deadline=_dl())
    assert resp.status in (200, 400) and lb.hits[0]["headers"]["host"] == f"pinned.test:{lb.port}"
    resp.close()
    with pytest.raises(McpTransportError) as ei:
        tr.post(McpHttpRequest(f"http://pinned.test:{lb.port}/mcp", {}, b"{}", None), deadline=_dl())
    assert ei.value.kind == "address_blocked" and len(lb.hits) == 1


def test_TC_INT_R29_707_auth_failed_and_custom_header_auth_AC_002_02(loops):
    lb = loops(FakeMcpServer(tools=[tool("search")], required_bearer="right-token"))
    c, _ = _client([lb])
    assert c.probe(_target(lb.url), Secret("wrong-token"), deadline=_dl()).failure == "auth_failed"
    assert c.probe(_target(lb.url), None, deadline=_dl()).failure == "auth_failed"
    assert c.probe(_target(lb.url), Secret("right-token"), deadline=_dl()).ok
    # 自定义头鉴权：值进入指定头，不进 Authorization
    lb2 = loops(FakeMcpServer(tools=[tool("search")], required_bearer=None))
    c2, _ = _client([lb2])
    assert c2.probe(_target(lb2.url, auth="header", header="X-Api-Key"), Secret("hdr-secret"), deadline=_dl()).ok
    h = lb2.hits[0]["headers"]
    assert h.get("x-api-key") == "hdr-secret" and "authorization" not in h and "x-ib-auth-slot" not in h  # 内部槽位头不外泄


def test_TC_INT_R29_708_read_limit_response_too_large_AC_019_06(loops):
    lb = loops(big=300_000)
    c, _ = _client([lb])
    sch = {"type": "object", "properties": {"q": {"type": "string"}}}
    with pytest.raises(McpClientError) as ei:
        c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}),
                    input_schema=sch, max_bytes=1000, deadline=_dl())
    assert ei.value.kind == "response_too_large"
    ok = c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}),
                     input_schema=sch, max_bytes=400_000, deadline=_dl())
    assert len(ok.content[0]["text"]) == 300_000  # 正例：上限放宽后完整读取


def test_TC_INT_R29_709_timeout_enforced_on_real_clock_AC_020_01(loops):
    """服务方 5 秒才返回、调用超时 1 秒：在 1 ± 1 秒内终止并返回“超时”（AC-020-01 的 30 秒口径按比例缩放到 1 秒，机制同一）。"""
    srv = FakeMcpServer(tools=[tool("search")], required_bearer=CANARY_TOKEN)
    lb = loops(srv)
    c, _ = _client([lb])
    c.probe(_target(lb.url), Secret(CANARY_TOKEN), deadline=_dl())  # 先协商时代
    srv.script("search", delay_s=5.0)
    t0 = time.monotonic()
    with pytest.raises(McpClientError) as ei:
        c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}),
                    input_schema={"type": "object", "properties": {"q": {"type": "string"}}}, max_bytes=32768, deadline=time.monotonic() + 1.0)
    el = time.monotonic() - t0
    assert ei.value.kind == "timeout" and 0.5 <= el <= 2.0, el


def test_TC_INT_R29_710_http_5xx_and_garbage_map_to_fixed_kinds_AC_019_04(loops):
    srv = FakeMcpServer(tools=[tool("search")], required_bearer=CANARY_TOKEN)
    lb = loops(srv)
    c, _ = _client([lb])
    c.probe(_target(lb.url), Secret(CANARY_TOKEN), deadline=_dl())
    sch = {"type": "object", "properties": {"q": {"type": "string"}}}
    srv.script("search", status=503)
    with pytest.raises(McpClientError) as e1:
        c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}), input_schema=sch, max_bytes=32768, deadline=_dl())
    assert e1.value.kind == "unreachable"
    srv.script("search", malformed=b"<html>not json</html>")
    with pytest.raises(McpClientError) as e2:
        c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}), input_schema=sch, max_bytes=32768, deadline=_dl())
    assert e2.value.kind == "protocol_error"
    srv.script("search", sse=True)  # SSE 响应形态（正例）
    ok = c.call_tool(_target(lb.url, "modern"), Secret(CANARY_TOKEN), McpCallRequest("crm", "search", {"q": "x"}), input_schema=sch, max_bytes=32768, deadline=_dl())
    assert ok.content[0]["text"] == "ok:search"


def test_TC_INT_R29_711_connection_refused_is_unreachable_and_proxy_env_ignored(loops, monkeypatch):
    """目标端口无人监听 ⇒ unreachable；环境代理变量不影响（直连钉定 IP，不走代理）。"""
    lb = loops(FakeMcpServer(tools=[tool("search")], required_bearer=None))
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    c, tr = _client([lb])
    assert c.probe(_target(lb.url, auth="none"), None, deadline=_dl()).ok  # 代理变量被忽略，直连成功
    dead = lb.port + 1
    allow = frozenset({("127.0.0.1", dead)})
    tr2 = HttpMcpTransport(rules_factory=lambda: (DomainRules((), ()), allow))
    with pytest.raises(McpTransportError) as ei:
        tr2.post(McpHttpRequest(f"http://127.0.0.1:{dead}/mcp", {}, b"{}", None), deadline=_dl())
    assert ei.value.kind == "unreachable"


def test_TC_INT_R29_712_header_injection_and_oversize_url_refused(loops):
    lb = loops()
    _, tr = _client([lb])
    for hdr in ({"X-A": "v\r\nInjected: 1"}, {"X\r\n": "v"}, {"X-A": "v\0"}):
        with pytest.raises(McpTransportError) as ei:
            tr.post(McpHttpRequest(lb.url, hdr, b"{}", None), deadline=_dl())
        assert ei.value.kind == "address_blocked"
    with pytest.raises(McpTransportError):
        tr.post(McpHttpRequest("http://127.0.0.1:%d/%s" % (lb.port, "a" * 3000), {}, b"{}", None), deadline=_dl())
    assert lb.hits == []
