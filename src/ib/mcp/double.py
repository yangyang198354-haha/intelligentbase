# MOD-R29-09 / implements IFC-R29-080..083 / depends MOD-R29-01, 03, 06 (仅 Secret / SecretKeyError)
"""离线替身：可编排的 FakeMcpServer + FakeMcpTransport（无套接字，记录请求）+ FakeResolver + ReversibleTestCipher。

本文件无任何网络导入（selfcheck `mcp_egress_single_exit` 断言）。仅离线 / 测试使用：
非离线模式下 `IB_MCP_TRANSPORT=fake` 启动失败；组合根的 `make_secret_cipher` 非离线永不返回 `ReversibleTestCipher`。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from ib.core.types import MCP_LEGACY_VERSION, MCP_MODERN_VERSION, McpEra
from ib.webtools.netguard import DomainRules, Resolver, UrlGuard, WebBlocked

from .crypto import Secret, SecretKeyError
from .wire import AUTH_SLOT_HEADER, McpHttpRequest, McpHttpResponse, McpTransportError, plain_http_allowed

__all__ = [
    "RecordedRequest",
    "FakeMcpServer",
    "FakeMcpTransport",
    "FakeResolver",
    "ReversibleTestCipher",
]


@dataclass(frozen=True, slots=True)
class RecordedRequest:
    method: str
    name: str | None
    arguments: Mapping[str, Any] | None
    headers: Mapping[str, str]  # 小写键；不含鉴权槽
    auth: str | None  # 收到的鉴权值（测试用，断言"服务方确实收到 / 未收到"）
    session_id: str | None


@dataclass
class _Script:
    result: Mapping[str, Any] | None = None
    is_error: bool = False
    delay_s: float = 0.0
    status: int | None = None
    malformed: bytes | None = None
    sse: bool = False
    input_required: bool = False


class FakeMcpServer:
    """IFC-R29-080：可编排行为的 MCP Server 替身。"""

    def __init__(
        self,
        *,
        era: McpEra = "modern",
        tools: Sequence[Mapping[str, Any]] = (),
        page_size: int = 100,
        required_bearer: str | None = None,
        list_changed: bool = False,
    ) -> None:
        self.era = era
        self._tools: list[dict[str, Any]] = [dict(t) for t in tools]
        self.page_size = max(1, int(page_size))
        self.required_bearer = required_bearer
        self.list_changed = list_changed
        self._scripts: dict[str, _Script] = {}
        self._log: list[RecordedRequest] = []
        self._lock = threading.Lock()
        self._sessions: set[str] = set()
        self._session_seq = 0
        self.session_required = True  # legacy：是否要求会话头
        self._listeners: list[Callable[[], None]] = []

    # -- 编排 ------------------------------------------------------------- #
    def script(
        self,
        remote_name: str,
        *,
        result: Mapping[str, Any] | None = None,
        is_error: bool = False,
        delay_s: float = 0.0,
        status: int | None = None,
        malformed: bytes | None = None,
        sse: bool = False,
        input_required: bool = False,
    ) -> None:
        self._scripts[remote_name] = _Script(result, is_error, delay_s, status, malformed, sse, input_required)

    def mutate_tool(self, remote_name: str, **fields: Any) -> None:
        with self._lock:
            for t in self._tools:
                if t.get("name") == remote_name:
                    t.update(fields)
                    return

    def add_tool(self, tool: Mapping[str, Any]) -> None:
        with self._lock:
            self._tools.append(dict(tool))

    def remove_tool(self, remote_name: str) -> None:
        with self._lock:
            self._tools = [t for t in self._tools if t.get("name") != remote_name]

    def emit_list_changed(self) -> None:
        for cb in list(self._listeners):
            cb()

    def expire_sessions(self) -> None:
        self._sessions.clear()

    @property
    def request_log(self) -> tuple[RecordedRequest, ...]:
        return tuple(self._log)

    def script_for(self, name: str) -> _Script | None:
        return self._scripts.get(name)

    # -- 处理 ------------------------------------------------------------- #
    def _rpc(self, rid: Any, *, result: Any = None, error: Any = None) -> bytes:
        obj: dict[str, Any] = {"jsonrpc": "2.0", "id": rid}
        if error is not None:
            obj["error"] = error
        else:
            obj["result"] = result
        return json.dumps(obj, ensure_ascii=False).encode("utf-8")

    def handle(self, headers: Mapping[str, str], body: bytes, auth: str | None) -> tuple[int, dict[str, str], bytes, _Script | None]:
        """返回 (status, 响应头, 响应体, 本次命中的脚本)。"""
        h = {k.lower(): v for k, v in headers.items()}
        try:
            msg = json.loads(body.decode("utf-8"))
        except ValueError:
            msg = {}
        method = str(msg.get("method", "")) if isinstance(msg, dict) else ""
        params = msg.get("params") if isinstance(msg, dict) and isinstance(msg.get("params"), dict) else {}
        rid = msg.get("id") if isinstance(msg, dict) else None
        name = params.get("name") if method == "tools/call" else None
        args = params.get("arguments") if method == "tools/call" else None
        rec = RecordedRequest(method, name, args, {k: v for k, v in h.items()}, auth, h.get("mcp-session-id"))
        with self._lock:
            self._log.append(rec)
        if self.required_bearer is not None and auth != f"Bearer {self.required_bearer}":
            return 401, {}, b'{"error":"unauthorized"}', None
        if self.era == "modern":
            return self._handle_modern(h, method, params, rid, name, args)
        return self._handle_legacy(h, method, params, rid, name)

    def _modern_err(self, rid: Any, code: int, msg: str, data: Any = None) -> tuple[int, dict[str, str], bytes, None]:
        err: dict[str, Any] = {"code": code, "message": msg}
        if data is not None:
            err["data"] = data
        return 400, {}, self._rpc(rid, error=err), None

    def _handle_modern(self, h, method, params, rid, name, args):
        if h.get("mcp-protocol-version") != MCP_MODERN_VERSION:
            return self._modern_err(rid, -32022, "unsupported version", {"supported": [MCP_MODERN_VERSION]})
        if h.get("mcp-method") != method:
            return self._modern_err(rid, -32020, "header mismatch")
        if method == "tools/call":
            if h.get("mcp-name") != name and not (h.get("mcp-name", "").startswith("=?base64?")):
                return self._modern_err(rid, -32020, "header mismatch")
            tool = next((t for t in self._tools if t.get("name") == name), None)
            if tool is not None and isinstance(args, dict):
                props = (tool.get("inputSchema") or {}).get("properties") or {}
                for pname, prop in props.items():
                    hn = prop.get("x-mcp-header") if isinstance(prop, dict) else None
                    if hn and pname in args and f"mcp-param-{hn}".lower() not in h:
                        return self._modern_err(rid, -32020, "header mismatch")
        if method == "server/discover":
            res = {
                "supportedVersions": [MCP_MODERN_VERSION],
                "capabilities": {"tools": {"listChanged": bool(self.list_changed)}},
                "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "fake", "version": "0"}},
            }
            return 200, {}, self._rpc(rid, result=res), None
        if method == "tools/list":
            return 200, {}, self._rpc(rid, result=self._list_result(params, "complete")), None
        if method == "tools/call":
            return self._call(rid, name, args, "complete")
        return 404, {}, self._rpc(rid, error={"code": -32601, "message": "Method not found"}), None

    def _handle_legacy(self, h, method, params, rid, name):
        if method == "server/discover" or h.get("mcp-protocol-version") == MCP_MODERN_VERSION:
            return 400, {}, b'{"error":"bad request"}', None
        if method == "initialize":
            self._session_seq += 1
            sid = f"sess-{self._session_seq}"
            self._sessions.add(sid)
            res = {
                "protocolVersion": MCP_LEGACY_VERSION,
                "capabilities": {"tools": {"listChanged": bool(self.list_changed)}},
                "serverInfo": {"name": "fake", "version": "0"},
            }
            return 200, ({"mcp-session-id": sid} if self.session_required else {}), self._rpc(rid, result=res), None
        if self.session_required and h.get("mcp-session-id") not in self._sessions:
            return 404, {}, b'{"error":"session not found"}', None
        if method == "notifications/initialized":
            return 202, {}, b"", None
        if method == "tools/list":
            return 200, {}, self._rpc(rid, result=self._list_result(params, None)), None
        if method == "tools/call":
            return self._call(rid, name, params.get("arguments"), None)
        return 200, {}, self._rpc(rid, error={"code": -32601, "message": "Method not found"}), None

    def _list_result(self, params: Mapping[str, Any], rtype: str | None) -> dict[str, Any]:
        cursor = params.get("cursor")
        start = int(cursor) if isinstance(cursor, str) and cursor.isdigit() else 0
        with self._lock:
            page = self._tools[start : start + self.page_size]
            more = start + self.page_size < len(self._tools)
        res: dict[str, Any] = {"tools": [dict(t) for t in page]}
        if more:
            res["nextCursor"] = str(start + self.page_size)
        if rtype:
            res["resultType"] = rtype
        return res

    def _call(self, rid: Any, name: Any, args: Any, rtype: str | None):
        sc = self._scripts.get(str(name))
        if sc is not None and sc.status is not None:
            return sc.status, {}, b"", sc
        if sc is not None and sc.malformed is not None:
            return 200, {}, sc.malformed, sc
        if not any(t.get("name") == name for t in self._tools):
            return 200, {}, self._rpc(rid, error={"code": -32602, "message": "Unknown tool"}), sc
        if sc is not None and sc.input_required:
            res: dict[str, Any] = {"content": [], "isError": False, "resultType": "input_required"}
        elif sc is not None and sc.result is not None:
            res = dict(sc.result)
            res.setdefault("isError", bool(sc.is_error))
            if rtype:
                res.setdefault("resultType", rtype)
        else:
            res = {"content": [{"type": "text", "text": f"ok:{name}"}], "isError": bool(sc.is_error) if sc else False}
            if rtype:
                res["resultType"] = rtype
        return 200, {}, self._rpc(rid, result=res), sc


class FakeResolver:
    """IFC-R29-082：host → 地址表；可模拟 DNS 先公后私重绑（`sequence`）。可作为 `Resolver` 直接调用。"""

    def __init__(self, table: Mapping[str, Sequence[str]] | None = None) -> None:
        self._table = {k.lower(): tuple(v) for k, v in (table or {}).items()}
        self._seq: dict[str, list[tuple[str, ...]]] = {}
        self.calls: list[str] = []

    def set(self, host: str, addrs: Sequence[str]) -> None:
        self._table[host.lower()] = tuple(addrs)

    def sequence(self, host: str, steps: Sequence[Sequence[str]]) -> None:
        """第 n 次解析返回 steps[n]（越界取最后一项）：先公后私即重绑。"""
        self._seq[host.lower()] = [tuple(s) for s in steps]

    def __call__(self, host: str, port: int, timeout_s: float) -> tuple[str, ...]:
        h = host.lower()
        self.calls.append(h)
        seq = self._seq.get(h)
        if seq:
            return seq.pop(0) if len(seq) > 1 else seq[0]
        if h in self._table:
            return self._table[h]
        raise WebBlocked("resolve_failed")


def _default_rules() -> tuple[DomainRules, frozenset[tuple[str, int]]]:
    return DomainRules((), ()), frozenset()


class FakeMcpTransport:
    """IFC-R29-081：url → FakeMcpServer；经同一 UrlGuard（注入 FakeResolver）；无套接字。"""

    def __init__(
        self,
        servers: Mapping[str, FakeMcpServer],
        *,
        resolver: Resolver,
        rules_factory: Callable[[], tuple[DomainRules, frozenset[tuple[str, int]]]] = _default_rules,
    ) -> None:
        self._servers = {k.rstrip("/"): v for k, v in servers.items()}
        self._resolver = resolver
        self._rules_factory = rules_factory
        self.attempts = 0  # 通过 UrlGuard 后真正"发出"的请求数

    def add_server(self, url: str, server: FakeMcpServer) -> None:
        self._servers[url.rstrip("/")] = server

    def post(self, req: McpHttpRequest, *, deadline: float) -> McpHttpResponse:
        rules, allow = self._rules_factory()
        allow = frozenset(allow)
        if not plain_http_allowed(req.url, allow):
            raise McpTransportError("address_blocked")
        guard = UrlGuard(rules, resolver=self._resolver, allowed_ports=None, internal_allow=allow)
        try:
            guard.check(req.url, deadline=deadline)
        except WebBlocked as exc:
            raise McpTransportError("unreachable" if exc.kind == "resolve_failed" else "address_blocked") from None
        key = req.url.split("?", 1)[0].rstrip("/")
        server = self._servers.get(key)
        if server is None:
            raise McpTransportError("unreachable")
        headers = dict(req.headers)
        slot = headers.pop(AUTH_SLOT_HEADER, None)
        auth: str | None = None
        if req.credential is not None and slot:
            secret = req.credential.reveal()
            if slot == "bearer":
                auth = f"Bearer {secret}"
            elif slot.startswith("header:"):
                auth = secret
                headers[slot[7:]] = secret
        self.attempts += 1
        status, rh, body, sc = server.handle(headers, req.body, auth)
        if sc is not None and sc.delay_s > 0:
            remaining = deadline - time.monotonic()
            if sc.delay_s >= remaining:
                raise McpTransportError("timeout")
            time.sleep(sc.delay_s)
        rh = {k.lower(): v for k, v in rh.items()}
        if sc is not None and sc.sse and status == 200 and sc.malformed is None:
            rh["content-type"] = "text/event-stream"
            body = b": keep-alive\n\n" + b"data: " + body + b"\n\n"
        else:
            rh.setdefault("content-type", "application/json")
        return McpHttpResponse(status=status, headers=rh, chunks=iter([body] if body else []), close=lambda: None)


class ReversibleTestCipher:
    """IFC-R29-083：`SecretCipher` 端口的可逆替身——可逆但**非加密**，仅离线 / 测试。
    令牌 = b"TESTCIPHER:" + 十六进制(明文 XOR 密钥流) + 8 位校验；不含明文子串（供"明文命中数 = 0"断言）。"""

    configured = True
    _PREFIX = b"TESTCIPHER:"

    def __init__(self, primary_key: str, previous_keys: Sequence[str] = ()) -> None:
        self._keys = [k for k in (primary_key, *previous_keys) if k]

    @staticmethod
    def _stream(key: str, n: int) -> bytes:
        out = b""
        i = 0
        while len(out) < n:
            out += hashlib.sha256(f"{key}:{i}".encode("utf-8")).digest()
            i += 1
        return out[:n]

    @staticmethod
    def _mac(key: str, plain: bytes) -> str:
        return hashlib.sha256(key.encode("utf-8") + b"|" + plain).hexdigest()[:8]

    def encrypt(self, plain: Secret) -> tuple[bytes, str]:
        if not self._keys:
            raise SecretKeyError("secret_key_missing")
        key = self._keys[0]
        raw = plain.reveal().encode("utf-8")
        x = bytes(a ^ b for a, b in zip(raw, self._stream(key, len(raw))))
        return self._PREFIX + x.hex().encode("ascii") + b"." + self._mac(key, raw).encode("ascii"), "test"

    def decrypt(self, token: bytes) -> Secret:
        try:
            tok = bytes(token)
            if not tok.startswith(self._PREFIX):
                raise ValueError
            body, _, mac = tok[len(self._PREFIX) :].partition(b".")
            x = bytes.fromhex(body.decode("ascii"))
            for key in self._keys:
                raw = bytes(a ^ b for a, b in zip(x, self._stream(key, len(x))))
                if self._mac(key, raw) == mac.decode("ascii"):
                    return Secret(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            pass
        raise SecretKeyError("token_invalid")
