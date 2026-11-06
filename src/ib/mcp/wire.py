# MOD-R29-03 / implements IFC-R29-020..024 / depends MOD-R29-01
"""MCP JSON-RPC 报文与 Streamable HTTP 头的构造 / 解析（纯函数，不含网络）。

协议事实出处（module_design「领域与外部依赖出处」）：
  [WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http.md，2026-11-05]
  [WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/index.md，2026-11-05]
  [WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning.md，2026-11-05]
  [WEB: https://modelcontextprotocol.io/specification/2026-07-28/server/discover.md，2026-11-05]
  [WEB: https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle.md、…/basic/transports.md，2026-11-05]
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping
from urllib.parse import urlsplit  # 纯字符串解析，非网络

from ib.core.types import MCP_LEGACY_VERSION, MCP_MODERN_VERSION, McpEra

from .schema_lite import x_mcp_header_violation

if TYPE_CHECKING:  # 仅类型：避免 wire ↔ crypto 的运行期依赖
    from .crypto import Secret

__all__ = [
    "McpHttpRequest",
    "McpHttpResponse",
    "JsonRpcOutcome",
    "WireFailure",
    "ProtocolError",
    "ResponseTooLarge",
    "McpTransportError",
    "AUTH_SLOT_HEADER",
    "CLIENT_INFO",
    "build_discover",
    "build_initialize",
    "build_initialized",
    "build_list",
    "build_listen",
    "build_call",
    "x_mcp_headers",
    "validate_x_mcp_header_annotations",
    "iter_sse_events",
    "parse_jsonrpc_response",
    "classify_http_failure",
    "encode_header_value",
    "plain_http_allowed",
    "ERR_METHOD_NOT_FOUND",
]

CLIENT_INFO: Mapping[str, str] = {"name": "intelligentbase", "version": "1"}
_META_VERSION = "io.modelcontextprotocol/protocolVersion"  # [WEB: …/2026-07-28/basic/index.md]
_META_CAPS = "io.modelcontextprotocol/clientCapabilities"
_META_INFO = "io.modelcontextprotocol/clientInfo"
_ACCEPT = "application/json, text/event-stream"
_JSON = "application/json"
#: 修订 2026-07-28 的 JSON-RPC 错误码 [WEB: …/2026-07-28/basic/index.md]
ERR_HEADER_MISMATCH = -32020
ERR_MISSING_CAPABILITY = -32021
ERR_UNSUPPORTED_VERSION = -32022
ERR_METHOD_NOT_FOUND = -32601
_MODERN_CODES = (ERR_HEADER_MISMATCH, ERR_MISSING_CAPABILITY, ERR_UNSUPPORTED_VERSION)


class ProtocolError(Exception):
    """报文不符合协议（未知 resultType、id 不匹配、非 JSON 等）。消息不含服务方原文。"""


class ResponseTooLarge(Exception):
    """响应超过字节上限。"""


class McpTransportError(Exception):
    """传输层失败（HttpMcpTransport / FakeMcpTransport 共用）。kind ∈ {timeout, unreachable, address_blocked}；
    消息不含地址 / 头值 / 内部拓扑。"""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


#: 传输层内部约定：请求头里的鉴权槽（不会被发出）。值 = `bearer` 或 `header:<头名>`；
#: 由 transport 以 Secret.reveal() 展开为真实鉴权头。
AUTH_SLOT_HEADER = "X-IB-Auth-Slot"


@dataclass(frozen=True, slots=True)
class McpHttpRequest:
    url: str
    headers: Mapping[str, str]
    body: bytes
    credential: "Secret | None"  # 仅在 transport 内展开为鉴权头；repr 不含值（Secret 自身脱敏）

    def __repr__(self) -> str:  # 日志 / 异常不含头值与载荷
        return f"McpHttpRequest(url=<{len(self.url)} chars>, body=<{len(self.body)} bytes>)"


@dataclass(frozen=True, slots=True)
class McpHttpResponse:
    status: int
    headers: Mapping[str, str]  # 小写键
    chunks: Iterator[bytes]
    close: Callable[[], None]


@dataclass(frozen=True, slots=True)
class JsonRpcOutcome:
    result: Mapping[str, Any] | None
    error: Mapping[str, Any] | None
    result_type: str = "complete"


@dataclass(frozen=True, slots=True)
class WireFailure:
    kind: str  # auth_failed | address_blocked | unreachable | protocol_error | modern_error
    modern_code: int | None = None
    supported: tuple[str, ...] = ()
    era_fallback: bool = False  # 400/404/405 且非可识别 modern 错误 ⇒ 尝试 legacy



def plain_http_allowed(url: str, internal_allow: frozenset[tuple[str, int]]) -> bool:
    """纯字符串判定（先于 DNS 与任何出站，AC-008-05）：`https` 恒可；`http` 仅当 (小写主机, 端口) 精确命中允许名单。"""
    try:
        parts = urlsplit(url.strip())
        scheme = (parts.scheme or "").lower()
        if scheme == "https":
            return True
        if scheme != "http":
            return False
        host = (parts.hostname or "").lower().rstrip(".")
        port = parts.port if parts.port is not None else 80
    except ValueError:
        return False
    return (host, port) in internal_allow


# --------------------------------------------------------------------------- #
# 头值编码
# --------------------------------------------------------------------------- #


def _check_header(name: str, value: str) -> None:
    if any(c in name for c in "\r\n\0:") or any(c in value for c in "\r\n\0"):
        raise ValueError("header_injection")


def encode_header_value(value: str) -> str:
    """非安全 ASCII（含空白首尾 / 非可打印 / 非 ASCII）按哨兵 Base64 编码 `=?base64?…?=`。
    [WEB: …/2026-07-28/basic/transports/streamable-http.md，2026-11-05]"""
    safe = (
        bool(value)
        and all(0x20 <= ord(c) <= 0x7E for c in value)
        and value == value.strip()
        and not value.startswith("=?base64?")
    )
    if safe:
        return value
    enc = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"=?base64?{enc}?="


def _meta() -> dict[str, Any]:
    return {_META_VERSION: MCP_MODERN_VERSION, _META_CAPS: {}, _META_INFO: dict(CLIENT_INFO)}


def _body(obj: Mapping[str, Any]) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _modern_headers(method: str, name: str | None = None) -> dict[str, str]:
    h = {
        "Content-Type": _JSON,
        "Accept": _ACCEPT,
        "MCP-Protocol-Version": MCP_MODERN_VERSION,
        "Mcp-Method": method,
    }
    if name is not None:
        h["Mcp-Name"] = encode_header_value(name)
    return h


def _legacy_headers(session_id: str | None, *, versioned: bool = True) -> dict[str, str]:
    h = {"Content-Type": _JSON, "Accept": _ACCEPT}
    if versioned:
        h["MCP-Protocol-Version"] = MCP_LEGACY_VERSION
    if session_id:
        h["MCP-Session-Id"] = session_id
    return h


# --------------------------------------------------------------------------- #
# 请求构造
# --------------------------------------------------------------------------- #


def build_discover(era_hint: McpEra, request_id: int) -> tuple[Mapping[str, str], bytes]:
    """IFC-R29-020：modern `server/discover`（era_hint 仅占位：探测总是先发 modern）。"""
    body = {"jsonrpc": "2.0", "id": request_id, "method": "server/discover", "params": {"_meta": _meta()}}
    return _modern_headers("server/discover"), _body(body)


def build_initialize(request_id: int) -> tuple[Mapping[str, str], bytes]:
    """legacy `initialize`（protocolVersion=2025-11-25，capabilities={}）。[WEB: …/2025-11-25/basic/lifecycle.md]"""
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {"protocolVersion": MCP_LEGACY_VERSION, "capabilities": {}, "clientInfo": dict(CLIENT_INFO)},
    }
    return _legacy_headers(None, versioned=False), _body(body)


def build_initialized(session_id: str | None) -> tuple[Mapping[str, str], bytes]:
    body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    return _legacy_headers(session_id), _body(body)


def build_list(
    era: McpEra, cursor: str | None, request_id: int, *, session_id: str | None
) -> tuple[Mapping[str, str], bytes]:
    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor
    if era == "modern":
        params["_meta"] = _meta()
        headers = _modern_headers("tools/list")
    else:
        headers = _legacy_headers(session_id)
    body = {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": params}
    return headers, _body(body)


def build_listen(request_id: int) -> tuple[Mapping[str, str], bytes]:
    """modern `subscriptions/listen`（请求 notifications.toolsListChanged）。
    [WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions.md，2026-11-05]"""
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "subscriptions/listen",
        "params": {"notifications": {"toolsListChanged": True}, "_meta": _meta()},
    }
    return _modern_headers("subscriptions/listen"), _body(body)


def x_mcp_headers(input_schema: Mapping[str, Any], arguments: Mapping[str, Any]) -> dict[str, str]:
    """IFC-R29-022：把 `x-mcp-header` 标注的参数镜像为 `Mcp-Param-{name}` 头（值取最终入参）。"""
    out: dict[str, str] = {}
    props = input_schema.get("properties") if isinstance(input_schema, Mapping) else None
    if not isinstance(props, Mapping):
        return out
    for pname, prop in props.items():
        if not isinstance(prop, Mapping):
            continue
        hname = prop.get("x-mcp-header")
        if not isinstance(hname, str) or pname not in arguments:
            continue
        v = arguments[pname]
        if isinstance(v, bool):
            sv = "true" if v else "false"
        elif isinstance(v, (int, float)):
            sv = str(v)
        elif isinstance(v, str):
            sv = v
        else:
            continue
        out[f"Mcp-Param-{hname}"] = encode_header_value(sv)
    return out


def validate_x_mcp_header_annotations(input_schema: Mapping[str, Any]) -> str | None:
    """违规返回原因；None 合规。"""
    return x_mcp_header_violation(input_schema)


def build_call(
    era: McpEra,
    remote_name: str,
    arguments: Mapping[str, Any],
    request_id: int,
    *,
    session_id: str | None,
    input_schema: Mapping[str, Any],
) -> tuple[Mapping[str, str], bytes]:
    """IFC-R29-021：`tools/call`。remote_name 1–128；头值禁 CR/LF。"""
    if not isinstance(remote_name, str) or not (1 <= len(remote_name) <= 128):
        raise ValueError("remote_name_invalid")
    params: dict[str, Any] = {"name": remote_name, "arguments": dict(arguments)}
    if era == "modern":
        params["_meta"] = _meta()
        headers = _modern_headers("tools/call", remote_name)
        headers.update(x_mcp_headers(input_schema, arguments))
    else:
        headers = _legacy_headers(session_id)
    for k, v in headers.items():
        _check_header(k, v)
    body = {"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": params}
    return headers, _body(body)


# --------------------------------------------------------------------------- #
# 响应解析
# --------------------------------------------------------------------------- #


def iter_sse_events(chunks: Iterable[bytes], *, max_bytes: int) -> Iterator[bytes]:
    """逐事件产出 `data` 负载（注释行忽略）；累计超过 max_bytes ⇒ ResponseTooLarge。"""
    total = 0
    buf = b""
    for chunk in chunks:
        total += len(chunk)
        if total > max_bytes:
            raise ResponseTooLarge()
        buf += chunk
        buf = buf.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        while b"\n\n" in buf:
            raw, buf = buf.split(b"\n\n", 1)
            data = _event_data(raw)
            if data is not None:
                yield data
    if buf.strip():
        data = _event_data(buf)
        if data is not None:
            yield data


def _event_data(raw: bytes) -> bytes | None:
    parts: list[bytes] = []
    for line in raw.split(b"\n"):
        if not line or line.startswith(b":"):
            continue
        if line.startswith(b"data:"):
            v = line[5:]
            if v.startswith(b" "):
                v = v[1:]
            parts.append(v)
    return b"\n".join(parts) if parts else None


def parse_jsonrpc_response(payload: bytes, *, expect_id: int) -> JsonRpcOutcome:
    """result | error；resultType 缺省视为 complete；未知 resultType ⇒ ProtocolError。"""
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ProtocolError("not_json") from None
    if not isinstance(obj, dict) or obj.get("jsonrpc") != "2.0":
        raise ProtocolError("not_jsonrpc")
    if obj.get("id") != expect_id or isinstance(obj.get("id"), bool):
        raise ProtocolError("id_mismatch")
    err = obj.get("error")
    if isinstance(err, dict):
        return JsonRpcOutcome(result=None, error=err)
    res = obj.get("result")
    if not isinstance(res, dict):
        raise ProtocolError("no_result")
    rtype = res.get("resultType", "complete")
    if rtype not in ("complete", "input_required"):  # 未知值必须视为无效 [WEB: …/2026-07-28/basic/index.md]
        raise ProtocolError("unknown_result_type")
    return JsonRpcOutcome(result=res, error=None, result_type=str(rtype))


def classify_http_failure(status: int, body: bytes) -> WireFailure:
    """IFC-R29-024。"""
    if 300 <= status < 400:
        return WireFailure("address_blocked")
    if status in (401, 403):
        return WireFailure("auth_failed")
    code: int | None = None
    supported: tuple[str, ...] = ()
    try:
        obj = json.loads(body.decode("utf-8")) if body else None
        err = obj.get("error") if isinstance(obj, dict) else None
        if isinstance(err, dict) and isinstance(err.get("code"), int):
            code = err["code"]
            data = err.get("data")
            sup = data.get("supported") if isinstance(data, dict) else None
            if isinstance(sup, list):
                supported = tuple(str(x) for x in sup if isinstance(x, str))
    except (UnicodeDecodeError, ValueError):
        code = None
    if status == 400:
        if code in _MODERN_CODES:
            return WireFailure("modern_error", modern_code=code, supported=supported)
        return WireFailure("protocol_error", era_fallback=True)
    if status in (404, 405):
        return WireFailure("protocol_error", modern_code=code, era_fallback=code != ERR_METHOD_NOT_FOUND)
    if status >= 500 or status == 429:
        return WireFailure("unreachable")
    return WireFailure("protocol_error")
