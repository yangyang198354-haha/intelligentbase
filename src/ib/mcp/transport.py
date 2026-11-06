# MOD-R29-08 / implements IFC-R29-070 (HttpMcpTransport) / depends MOD-R29-01, 03, 04
"""HTTP 传输：`ib.mcp` 中**唯一**允许网络导入（http.client / socket / ssl / urllib）的文件。

每次 `post`：新建 `UrlGuard`（任意端口 + 内网允许名单）→ 重新解析 → 钉 IP 连接；不跟随重定向（3xx ⇒ address_blocked，
不读 Location）；禁用环境代理（http.client 直连钉定 IP）；不发 Cookie；`Accept-Encoding: identity`；
鉴权头只在此处由 `Secret.reveal()` 展开；日志 / 异常 / repr 不含头值。
"""

from __future__ import annotations

import http.client
import socket
import ssl
import time
from typing import Callable, Iterator, Mapping

from ib.webtools.fetch import PinnedHTTPConnection, PinnedHTTPSConnection
from ib.webtools.netguard import DomainRules, Resolver, UrlGuard, WebBlocked

from .wire import AUTH_SLOT_HEADER, McpHttpRequest, McpHttpResponse, McpTransportError, plain_http_allowed

__all__ = ["HttpMcpTransport"]

_URL_MAX = 2048
_BLOCK = 8192


def _map_blocked(exc: WebBlocked) -> McpTransportError:
    return McpTransportError("unreachable" if exc.kind == "resolve_failed" else "address_blocked")


class HttpMcpTransport:
    def __init__(
        self,
        *,
        rules_factory: Callable[[], tuple[DomainRules, frozenset[tuple[str, int]]]],
        resolver: Resolver | None = None,
        ca_bundle_path: str | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._rules_factory = rules_factory
        self._resolver = resolver
        self._ca = ca_bundle_path or None
        self._clock = clock

    def __repr__(self) -> str:
        return "HttpMcpTransport()"

    def _ssl_context(self) -> ssl.SSLContext:
        return ssl.create_default_context(cafile=self._ca) if self._ca else ssl.create_default_context()

    def post(self, req: McpHttpRequest, *, deadline: float) -> McpHttpResponse:
        if not isinstance(req.url, str) or not req.url or len(req.url) > _URL_MAX:
            raise McpTransportError("address_blocked")
        for k, v in req.headers.items():
            if any(c in str(k) + str(v) for c in "\r\n\0"):
                raise McpTransportError("address_blocked")
        try:
            rules, internal_allow = self._rules_factory()
        except Exception:  # noqa: BLE001
            raise McpTransportError("unreachable") from None
        if not plain_http_allowed(req.url, frozenset(internal_allow)):
            raise McpTransportError("address_blocked")  # 公网明文 http / 非 http(s)：先于 DNS
        guard = UrlGuard(
            rules,
            resolver=self._resolver,
            allowed_ports=None,
            internal_allow=frozenset(internal_allow),
        )
        # UrlGuard 的 deadline 口径 = time.monotonic()；本传输的 clock 默认同源
        try:
            target = guard.check(req.url, deadline=deadline)
        except WebBlocked as exc:
            raise _map_blocked(exc) from None
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise McpTransportError("timeout")
        timeout = max(0.1, remaining)
        if target.scheme == "https":
            conn: http.client.HTTPConnection = PinnedHTTPSConnection(
                target.pinned_ip, target.port, target.host, timeout
            )
            conn._pin_ctx = self._ssl_context()  # type: ignore[attr-defined]  # connect() 使用该上下文（含私有 CA）
        else:
            conn = PinnedHTTPConnection(target.pinned_ip, target.port, timeout)
        default_port = 443 if target.scheme == "https" else 80
        host_header = target.host if target.port == default_port else f"{target.host}:{target.port}"
        headers = dict(req.headers)
        slot = headers.pop(AUTH_SLOT_HEADER, None)
        try:
            conn.putrequest("POST", target.path_query, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", host_header)
            conn.putheader("Accept-Encoding", "identity")
            for k, v in headers.items():
                if k.lower() in ("host", "content-length", "cookie", "accept-encoding", "authorization"):
                    continue
                conn.putheader(k, v)
            if req.credential is not None and slot:
                secret = req.credential.reveal()  # 仅此处展开
                if slot == "bearer":
                    conn.putheader("Authorization", f"Bearer {secret}")
                elif slot.startswith("header:"):
                    conn.putheader(slot[7:], secret)
            conn.putheader("Content-Length", str(len(req.body)))
            conn.endheaders(req.body)
            sock = conn.sock  # DEF-R29-006：close-delimited 响应时 getresponse 会把 conn.sock 置 None，须先留底层 socket
            resp = conn.getresponse()
        except socket.timeout:
            conn.close()
            raise McpTransportError("timeout") from None
        except (OSError, http.client.HTTPException, ssl.SSLError, ValueError):
            conn.close()
            raise McpTransportError("unreachable") from None
        except Exception:  # noqa: BLE001
            conn.close()
            raise McpTransportError("unreachable") from None
        if 300 <= resp.status < 400:  # 不跟随；不读 Location
            conn.close()
            raise McpTransportError("address_blocked")
        clock = self._clock

        def _chunks() -> Iterator[bytes]:
            while True:
                left = deadline - clock()
                if left <= 0:
                    raise McpTransportError("timeout")
                try:
                    if sock is not None:
                        sock.settimeout(max(0.1, left))
                    # DEF-R29-007：read1 = 有多少读多少（read(N) 会阻塞到凑满 N 字节或 EOF，小事件会滞留）
                    block = resp.read1(_BLOCK)
                except socket.timeout:
                    raise McpTransportError("timeout") from None
                except (OSError, http.client.HTTPException, ValueError, AttributeError):
                    # ValueError / AttributeError：另一线程 close() 与读取竞态（fp 已置 None / 文件已关闭）
                    raise McpTransportError("unreachable") from None
                if not block:
                    return
                yield block

        def _close() -> None:
            # DEF-R29-006：先 shutdown 唤醒另一线程中阻塞的读取（仅 close 不能打断），再关闭响应与连接；幂等
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            for closer in (resp.close, conn.close):
                try:
                    closer()
                except Exception:  # noqa: BLE001
                    pass

        hdrs: Mapping[str, str] = {k.lower(): v for k, v in resp.getheaders()}
        return McpHttpResponse(status=resp.status, headers=hdrs, chunks=_chunks(), close=_close)
