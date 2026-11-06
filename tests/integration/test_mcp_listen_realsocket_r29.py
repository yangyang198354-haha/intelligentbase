"""[REV-29 / GROUP_D 缺陷回流第 1 轮；第 2 轮翻转为 AC 原口径] 集成：监听流在真实 socket 上的停止行为（A12 / GR-C-004 条件）。

仅在本机 127.0.0.1 随机端口起临时 HTTP 服务（测试内启停，不出网）：对 `subscriptions/listen` 返回 200 + text/event-stream 后
**保持连接阻塞、不发送任何事件**（安静的长连接）；客户端用真实 HttpMcpTransport + 真实 McpClient.listen。
验证 stop 置位后监听线程在超时内结束（resp.close() 能打断另一线程中阻塞的 socket 读取）。

分层：integration（真实 socket + 真实 http.client 传输 + 真实 McpClient.listen；服务端为测试内回环替身）。
溯源：US-013（AC-013-01 变更通知通道）；DEF-R29-003 / A12。
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ib.mcp.client import McpClient, McpTarget
from ib.mcp.transport import HttpMcpTransport
from ib.webtools.netguard import DomainRules


class QuietSseServer:
    """subscriptions/listen → 200 text/event-stream 后阻塞（直到 release 置位或客户端断开）；可选先推一条 list_changed 事件。"""

    def __init__(self, *, first_event: bool = False, chunked: bool = False):
        self.release = threading.Event()
        self.listen_seen = threading.Event()
        self.client_gone = threading.Event()
        outer = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n)
                try:
                    method = json.loads(body.decode("utf-8")).get("method")
                except Exception:  # noqa: BLE001
                    method = None
                if method != "subscriptions/listen":
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                if chunked:
                    self.send_header("Transfer-Encoding", "chunked")
                else:
                    self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                if first_event:
                    ev = b'data: {"jsonrpc":"2.0","method":"notifications/tools/list_changed"}\n\n'
                    self.wfile.write((b"%x\r\n" % len(ev)) + ev + b"\r\n" if chunked else ev)
                self.wfile.flush()
                outer.listen_seen.set()
                # 安静：不再发送任何字节，直到被释放；用 send 探测对端是否已断开
                while not outer.release.wait(0.1):
                    try:
                        self.connection.setblocking(False)
                        data = self.connection.recv(1, __import__("socket").MSG_PEEK)
                        if data == b"":
                            outer.client_gone.set()
                            return
                    except BlockingIOError:
                        pass
                    except OSError:
                        outer.client_gone.set()
                        return
                if chunked:  # 被释放：正常结束 chunked 流（终止块），使客户端读到干净 EOF
                    try:
                        self.connection.setblocking(True)
                        self.wfile.write(b"0\r\n\r\n")
                        self.wfile.flush()
                    except OSError:
                        pass

        class _Quiet(ThreadingHTTPServer):
            def handle_error(self, request, client_address):
                pass

        self.httpd = _Quiet(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def close(self):
        self.release.set()
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(3)


def _client(srv: QuietSseServer) -> McpClient:
    allow = frozenset({("127.0.0.1", srv.port)})
    return McpClient(HttpMcpTransport(rules_factory=lambda: (DomainRules((), ()), allow)))


def _start_listen(c: McpClient, srv: QuietSseServer):
    stop = threading.Event()
    changed: list[int] = []
    errors: list[BaseException] = []

    def run():
        try:
            c.listen(McpTarget("crm", srv.url, "none", None, "modern", None), None, on_changed=lambda: changed.append(1), stop=stop)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    th = threading.Thread(target=run, daemon=True, name="ib-mcp-test-listen-real")
    th.start()
    return th, stop, changed, errors


import pytest


@pytest.mark.parametrize("chunked", [False, True], ids=["close-delimited", "chunked"])
def test_TC_INT_R29_720_real_socket_quiet_sse_stream_stop_ends_listener_and_closes_client_A12(chunked):
    """A12（DEF-R29-006 已修复）：真实 socket 上，stop 置位后监听线程在超时预算（3 s）内退出（is_alive()==False），
    服务端观察到客户端断开（client_gone），监听线程内无异常泄漏（errors == []）。close-delimited 与 chunked 两种形态均验证。
    正例：stop 之前监听线程确实阻塞在安静流上、客户端仍连着。"""
    srv = QuietSseServer(chunked=chunked)
    try:
        th, stop, changed, errors = _start_listen(_client(srv), srv)
        assert srv.listen_seen.wait(5), "服务端应收到 subscriptions/listen"
        time.sleep(0.5)
        assert th.is_alive(), "正例：stop 之前监听线程阻塞在安静流上"
        assert not srv.client_gone.is_set(), "正例：stop 之前客户端仍连着"
        stop.set()
        th.join(3.0)
        assert not th.is_alive(), "stop 后 3 s 内监听线程应退出"
        assert srv.client_gone.wait(3.0), "服务端应观察到客户端断开"
        assert errors == [], errors
        assert changed == []
    finally:
        srv.close()


@pytest.mark.parametrize("chunked", [False, True], ids=["close-delimited", "chunked"])
def test_TC_INT_R29_721_real_socket_list_changed_event_delivered_once_within_2s_while_stream_open_AC_013_01(chunked):
    """AC-013-01 / A12（DEF-R29-007 已修复）：真实 socket 上，服务端推送 list_changed 后流仍保持打开，
    on_changed 在 2 s 内恰好回调一次；流继续打开期间不重复回调；服务端关闭连接后线程退出且无错误。"""
    srv = QuietSseServer(first_event=True, chunked=chunked)
    try:
        th, stop, changed, errors = _start_listen(_client(srv), srv)
        assert srv.listen_seen.wait(5)
        t0 = time.monotonic()
        while not changed and time.monotonic() - t0 < 2.0:
            time.sleep(0.02)
        assert changed == [1], "流仍开着时 2 s 内 on_changed 应回调恰好一次"
        assert th.is_alive() and not srv.release.is_set(), "回调发生时流仍保持打开（线程仍在监听）"
        time.sleep(0.5)
        assert changed == [1], "流保持打开期间不应重复回调"
        srv.release.set()  # 服务端关闭连接 ⇒ 线程应正常结束
        th.join(5.0)
        assert not th.is_alive() and errors == [], errors
        assert changed == [1], "服务端关闭后仍恰好一次"
    finally:
        srv.close()
