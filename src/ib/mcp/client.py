# MOD-R29-10 / implements IFC-R29-090..093 / depends MOD-R29-01, 02, 03 (transport 经端口注入，不 import MOD-08)
"""MCP 客户端（协议层）：时代探测、握手、`tools/list` 分页、`tools/call`、legacy 会话缓存、变更监听。

ADR-R29-04：支持集合 = {2026-07-28 (modern), 2025-11-25 (legacy)}；每次请求一条短连接；
legacy 404 带会话 ⇒ 重新初始化**一次**；服务端在流内发的请求不应答；`resultType=input_required` ⇒ 失败。
"""

from __future__ import annotations

import hashlib
import itertools
import json
import threading
import time
from dataclasses import dataclass
from typing import AbstractSet, Any, Callable, Mapping

from ib.core.ports import McpTransport
from ib.core.types import (
    MCP_LEGACY_VERSION,
    MCP_MODERN_VERSION,
    McpCallRequest,
    McpDiscovery,
    McpExcludedTool,
    McpFailureKind,
    McpGovernance,
    McpNegotiated,
    McpRawCallResult,
)

from .crypto import Secret
from .rules import check_discovered_tool
from .wire import (
    AUTH_SLOT_HEADER,
    ERR_METHOD_NOT_FOUND,
    JsonRpcOutcome,
    McpHttpRequest,
    McpTransportError,
    ProtocolError,
    ResponseTooLarge,
    build_call,
    build_discover,
    build_initialize,
    build_initialized,
    build_list,
    build_listen,
    classify_http_failure,
    iter_sse_events,
    parse_jsonrpc_response,
)

__all__ = ["McpTarget", "McpProbeResult", "McpClient", "McpClientError"]

_MAX_PAGES = 50
_LIST_MAX_BYTES = 4 * 1024 * 1024
_ERR_BODY_MAX = 65536
_LISTEN_WINDOW_S = 300.0


class McpClientError(Exception):
    """面向内部；message 不含凭证 / 内部拓扑。kind 为 McpFailureKind。"""

    def __init__(self, kind: McpFailureKind | str) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True, slots=True)
class McpTarget:
    server_id: str
    url: str
    auth_kind: str
    auth_header_name: str | None
    era: str | None  # 缓存的时代；None = 需探测
    version: str | None
    supports_list_changed: bool = False  # DEF-R29-003：验证期协商结果（已知时代时随 target 带入，refresh 不得覆盖）


@dataclass(frozen=True, slots=True)
class McpProbeResult:
    ok: bool
    negotiated: McpNegotiated | None = None
    failure: str | None = None  # McpFailureKind 或 no_tools_capability


@dataclass(frozen=True, slots=True)
class _Reply:
    status: int
    headers: Mapping[str, str]
    outcome: JsonRpcOutcome | None
    body: bytes  # 仅非 2xx 时填充（截断）


class McpClient:
    def __init__(
        self,
        transport: McpTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        session_ttl_s: float = 600.0,
    ) -> None:
        self._t = transport
        self._clock = clock
        self._ttl = float(session_ttl_s)
        self._ids = itertools.count(1)
        self._sessions: dict[tuple[str, str], tuple[str | None, float]] = {}
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return "McpClient()"

    # -- 传输 -------------------------------------------------------------- #
    def _request(
        self, target: McpTarget, cred: Secret | None, headers: Mapping[str, str], body: bytes
    ) -> McpHttpRequest:
        h = dict(headers)
        use = cred if (cred is not None and target.auth_kind in ("bearer", "header")) else None
        if use is not None:
            h[AUTH_SLOT_HEADER] = "bearer" if target.auth_kind == "bearer" else f"header:{target.auth_header_name}"
        return McpHttpRequest(url=target.url, headers=h, body=body, credential=use)

    def _exchange(
        self,
        target: McpTarget,
        cred: Secret | None,
        built: tuple[Mapping[str, str], bytes],
        rid: int | None,
        deadline: float,
        max_bytes: int,
    ) -> _Reply:
        headers, body = built
        try:
            resp = self._t.post(self._request(target, cred, headers, body), deadline=deadline)
        except McpTransportError as exc:
            raise McpClientError(exc.kind) from None
        try:
            if resp.status >= 300:
                buf = b""
                try:
                    for ch in resp.chunks:
                        buf += ch
                        if len(buf) >= _ERR_BODY_MAX:
                            break
                except McpTransportError:
                    pass
                return _Reply(resp.status, resp.headers, None, buf[:_ERR_BODY_MAX])
            if rid is None or resp.status in (202, 204):
                for _ in resp.chunks:  # 排空（上限内）
                    break
                return _Reply(resp.status, resp.headers, None, b"")
            return _Reply(resp.status, resp.headers, self._read_outcome(resp, rid, max_bytes), b"")
        except McpTransportError as exc:
            raise McpClientError(exc.kind) from None
        except ResponseTooLarge:
            raise McpClientError("response_too_large") from None
        except ProtocolError:
            raise McpClientError("protocol_error") from None
        finally:
            try:
                resp.close()
            except Exception:  # noqa: BLE001
                pass

    def _read_outcome(self, resp: Any, rid: int, max_bytes: int) -> JsonRpcOutcome:
        ctype = str(resp.headers.get("content-type", "")).lower()
        if "text/event-stream" in ctype:
            for data in iter_sse_events(resp.chunks, max_bytes=max_bytes):
                try:
                    obj = json.loads(data.decode("utf-8"))
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("id") == rid and ("result" in obj or "error" in obj):
                    return parse_jsonrpc_response(data, expect_id=rid)
                # 服务端在流内发的请求 / 通知：不应答，忽略
            raise ProtocolError("no_response_in_stream")
        buf = b""
        for ch in resp.chunks:
            buf += ch
            if len(buf) > max_bytes:
                raise ResponseTooLarge()
        return parse_jsonrpc_response(buf, expect_id=rid)

    # -- 会话 -------------------------------------------------------------- #
    @staticmethod
    def _skey(target: McpTarget, cred: Secret | None) -> tuple[str, str]:
        tag = hashlib.sha256(cred.reveal().encode("utf-8")).hexdigest()[:8] if cred is not None else ""
        return (target.server_id, tag)

    def _session(self, target: McpTarget, cred: Secret | None) -> str | None:
        with self._lock:
            ent = self._sessions.get(self._skey(target, cred))
            if ent and ent[1] > self._clock():
                return ent[0]
        return None

    def _has_session_entry(self, target: McpTarget, cred: Secret | None) -> bool:
        with self._lock:
            ent = self._sessions.get(self._skey(target, cred))
            return bool(ent and ent[1] > self._clock())

    def _init_legacy(
        self, target: McpTarget, cred: Secret | None, deadline: float
    ) -> tuple[McpNegotiated, str | None]:
        rid = next(self._ids)
        rep = self._exchange(target, cred, build_initialize(rid), rid, deadline, 262144)
        self._raise_http(rep, era_probe=False)
        oc = rep.outcome
        if oc is None or oc.error is not None or oc.result is None:
            raise McpClientError("protocol_incompatible")
        res = oc.result
        if res.get("protocolVersion") != MCP_LEGACY_VERSION:
            raise McpClientError("protocol_incompatible")
        caps = res.get("capabilities") if isinstance(res.get("capabilities"), Mapping) else {}
        tools_cap = isinstance(caps.get("tools"), Mapping)
        listc = bool(tools_cap and caps["tools"].get("listChanged") is True)
        sid = rep.headers.get("mcp-session-id") or None
        rep2 = self._exchange(target, cred, build_initialized(sid), None, deadline, 4096)
        if rep2.status >= 300:
            self._raise_http(rep2, era_probe=False)
        with self._lock:
            self._sessions[self._skey(target, cred)] = (sid, self._clock() + self._ttl)
        return McpNegotiated("legacy", MCP_LEGACY_VERSION, tools_cap, listc), sid

    # -- 失败映射 ----------------------------------------------------------- #
    def _raise_http(self, rep: _Reply, *, era_probe: bool) -> None:
        if rep.status < 300:
            return
        f = classify_http_failure(rep.status, rep.body)
        if f.kind == "auth_failed":
            raise McpClientError("auth_failed")
        if f.kind == "address_blocked":
            raise McpClientError("address_blocked")
        if f.kind == "unreachable":
            raise McpClientError("unreachable")
        raise McpClientError("protocol_error")

    # -- 探测 -------------------------------------------------------------- #
    def probe(self, target: McpTarget, cred: Secret | None, *, deadline: float) -> McpProbeResult:
        """先发 modern `server/discover`；按响应回退 legacy `initialize`。"""
        try:
            return self._probe(target, cred, deadline)
        except McpClientError as exc:
            return McpProbeResult(False, None, str(exc.kind))

    def _probe(self, target: McpTarget, cred: Secret | None, deadline: float) -> McpProbeResult:
        rid = next(self._ids)
        rep = self._exchange(target, cred, build_discover("modern", rid), rid, deadline, 262144)
        fallback = False
        if rep.status >= 300:
            f = classify_http_failure(rep.status, rep.body)
            if f.kind == "modern_error":
                if MCP_MODERN_VERSION in f.supported:
                    raise McpClientError("protocol_error")
                if MCP_LEGACY_VERSION in f.supported:
                    fallback = True
                else:
                    raise McpClientError("protocol_incompatible")
            elif f.era_fallback:
                fallback = True
            else:
                self._raise_http(rep, era_probe=True)
        else:
            oc = rep.outcome
            if oc is None:
                fallback = True
            elif oc.error is not None:
                code = oc.error.get("code")
                if code == ERR_METHOD_NOT_FOUND or code == -32022:
                    sup = (oc.error.get("data") or {}).get("supported") if isinstance(oc.error.get("data"), Mapping) else None
                    if isinstance(sup, list) and MCP_LEGACY_VERSION not in sup and MCP_MODERN_VERSION not in sup:
                        raise McpClientError("protocol_incompatible")
                    fallback = True
                else:
                    raise McpClientError("protocol_error")
            else:
                res = oc.result or {}
                versions = res.get("supportedVersions")
                if isinstance(versions, list) and MCP_MODERN_VERSION in versions:
                    caps = res.get("capabilities") if isinstance(res.get("capabilities"), Mapping) else {}
                    tools_cap = isinstance(caps.get("tools"), Mapping)
                    listc = bool(tools_cap and caps["tools"].get("listChanged") is True)
                    neg = McpNegotiated("modern", MCP_MODERN_VERSION, tools_cap, listc)
                    return McpProbeResult(tools_cap, neg, None if tools_cap else "no_tools_capability")
                if isinstance(versions, list) and MCP_LEGACY_VERSION in versions:
                    fallback = True
                else:
                    raise McpClientError("protocol_incompatible")
        if not fallback:
            raise McpClientError("protocol_error")
        neg, _sid = self._init_legacy(target, cred, deadline)
        return McpProbeResult(neg.tools_capability, neg, None if neg.tools_capability else "no_tools_capability")

    # -- tools/list -------------------------------------------------------- #
    def list_tools(
        self,
        target: McpTarget,
        cred: Secret | None,
        *,
        gov: McpGovernance,
        deadline: float,
        taken_local_names: AbstractSet[str],
    ) -> McpDiscovery:
        """IFC-R29-091：分页至取完 / 页数 ≤50 / 工具数 ≤ 上限；逐项 check_discovered_tool。"""
        pr = self._probe(target, cred, deadline) if target.era is None else None
        if pr is not None:
            if pr.negotiated is None or not pr.ok:
                raise McpClientError(pr.failure or "protocol_incompatible")
            neg = pr.negotiated
        else:
            neg = McpNegotiated(str(target.era), str(target.version or ""), True, bool(target.supports_list_changed))
        era = neg.era
        sid = self._session(target, cred) if era == "legacy" else None
        if era == "legacy" and not self._has_session_entry(target, cred):
            _n, sid = self._init_legacy(target, cred, deadline)
        taken = {n.lower() for n in taken_local_names}
        tools = []
        excluded: list[McpExcludedTool] = []
        cursor: str | None = None
        reinit_used = False
        total = 0
        for _page in range(_MAX_PAGES):
            rid = next(self._ids)
            rep = self._exchange(
                target, cred, build_list(era, cursor, rid, session_id=sid), rid, deadline, _LIST_MAX_BYTES  # type: ignore[arg-type]
            )
            if era == "legacy" and rep.status == 404 and not reinit_used:
                reinit_used = True
                _n, sid = self._init_legacy(target, cred, deadline)
                continue
            self._raise_http(rep, era_probe=False)
            oc = rep.outcome
            if oc is None or oc.error is not None or oc.result is None:
                raise McpClientError("protocol_error")
            raw_tools = oc.result.get("tools")
            if not isinstance(raw_tools, list):
                raise McpClientError("protocol_error")
            for raw in raw_tools:
                total += 1
                if total > gov.max_tools_per_server:
                    nm = raw.get("name") if isinstance(raw, Mapping) and isinstance(raw.get("name"), str) else ""
                    excluded.append(McpExcludedTool(nm[:128], "over_limit"))
                    continue
                if not isinstance(raw, Mapping):
                    excluded.append(McpExcludedTool("", "name_invalid"))
                    continue
                item = check_discovered_tool(raw, server_id=target.server_id, gov=gov, taken_local_names=taken)
                if isinstance(item, McpExcludedTool):
                    excluded.append(item)
                else:
                    from .rules import local_tool_name

                    taken.add(local_tool_name(target.server_id, item.remote_name).lower())
                    tools.append(item)
            nxt = oc.result.get("nextCursor")
            if isinstance(nxt, str) and nxt and total <= gov.max_tools_per_server + 1000:
                cursor = nxt
                continue
            break
        return McpDiscovery(tools=tuple(tools), excluded=tuple(excluded), negotiated=neg)

    # -- tools/call -------------------------------------------------------- #
    def call_tool(
        self,
        target: McpTarget,
        cred: Secret | None,
        req: McpCallRequest,
        *,
        input_schema: Mapping[str, Any],
        max_bytes: int,
        deadline: float,
    ) -> McpRawCallResult:
        """IFC-R29-092：调用路径不重探测时代（era 为 None ⇒ protocol_incompatible）。"""
        if target.era not in ("modern", "legacy"):
            raise McpClientError("protocol_incompatible")
        era = str(target.era)
        sid = self._session(target, cred) if era == "legacy" else None
        if era == "legacy" and not self._has_session_entry(target, cred):
            _n, sid = self._init_legacy(target, cred, deadline)
        reinit_used = False
        while True:
            rid = next(self._ids)
            try:
                built = build_call(
                    era, req.remote_name, req.arguments, rid, session_id=sid, input_schema=input_schema  # type: ignore[arg-type]
                )
            except ValueError:
                raise McpClientError("bad_arguments") from None
            # DEF-R29-002：读取上限留出余量（≥ 4 倍结果上限），使合法的超长文本交由 render_result 截断 + 标注，而非直接降级
            rep = self._exchange(target, cred, built, rid, deadline, max(int(max_bytes) * 4, int(max_bytes) + 65536))
            if era == "legacy" and rep.status == 404 and not reinit_used:
                reinit_used = True
                _n, sid = self._init_legacy(target, cred, deadline)
                continue
            break
        self._raise_http(rep, era_probe=False)
        oc = rep.outcome
        if oc is None:
            raise McpClientError("protocol_error")
        if oc.error is not None:
            code = oc.error.get("code")
            raise McpClientError("bad_arguments" if code == -32602 else "protocol_error")
        res = oc.result or {}
        if oc.result_type == "input_required":
            raise McpClientError("input_required")
        content = res.get("content")
        items = tuple(c for c in content if isinstance(c, Mapping)) if isinstance(content, list) else ()
        return McpRawCallResult(
            is_error=res.get("isError") is True,
            content=items,
            structured=res.get("structuredContent"),
            result_type=oc.result_type,
        )

    # -- 监听 -------------------------------------------------------------- #
    def listen(
        self,
        target: McpTarget,
        cred: Secret | None,
        *,
        on_changed: Callable[[], None],
        stop: threading.Event,
    ) -> None:
        """IFC-R29-093：仅 modern；`subscriptions/listen {toolsListChanged:true}`；
        收到 `notifications/tools/list_changed` 只回调（不在此刷新）；关闭流即取消。"""
        if target.era != "modern":
            raise McpClientError("protocol_incompatible")
        rid = next(self._ids)
        headers, body = build_listen(rid)
        deadline = self._clock() + _LISTEN_WINDOW_S
        try:
            resp = self._t.post(self._request(target, cred, headers, body), deadline=deadline)
        except McpTransportError as exc:
            raise McpClientError(exc.kind) from None
        done = threading.Event()

        def _closer() -> None:  # DEF-R29-003：stop 置位即关闭监听流，使阻塞在安静流上的读取立刻结束
            while not (stop.is_set() or done.is_set()):
                done.wait(0.2)
            if stop.is_set():
                try:
                    resp.close()
                except Exception:  # noqa: BLE001
                    pass

        threading.Thread(target=_closer, daemon=True, name="ib-mcp-listen-close").start()
        try:
            if resp.status >= 300:
                self._raise_http(_Reply(resp.status, resp.headers, None, b""), era_probe=False)
            for data in iter_sse_events(resp.chunks, max_bytes=1 << 20):
                if stop.is_set():
                    return
                try:
                    obj = json.loads(data.decode("utf-8"))
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("method") == "notifications/tools/list_changed":
                    on_changed()
        except McpTransportError as exc:
            if not stop.is_set():
                raise McpClientError(exc.kind) from None
        except ResponseTooLarge:
            raise McpClientError("response_too_large") from None
        finally:
            done.set()
            try:
                resp.close()
            except Exception:  # noqa: BLE001
                pass
