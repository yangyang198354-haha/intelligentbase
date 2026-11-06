# MOD-R29-19 / implements IFC-R29-200..218 / depends MOD-R29-01, 12, 14, 15, 16
"""`/api/mcp/*` 端点族（REV-29：agent 工具调用的 MCP 适配）。

通用约定：
  * 鉴权 = `Authorization` 头（`AuthMiddleware`）；`?token=` 等出现在查询串由中间件统一 400（本模块不为此开例外）；
  * 写操作先鉴权后解析请求体（无副作用的 401/403）；
  * `IB_MCP_ENABLED=0`（`Deps.mcp is None`）⇒ 写端点 `503 mcp_disabled`；
  * 错误体 `{"error": {"code", "message", "details"?}}`，**不回显**凭证 / 配置值；列表接口 `{items: [...]}`。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Callable

from rest_framework import status

from ib.core import (
    ConflictError,
    DependencyUnavailableError,
    IbError,
    NotFoundError,
    ScopeViolationError,
    ValidationError,
)
from ib.core.types import MCP_HARD_MAX, McpGovernance, McpServer, McpServerLimits, McpToolRecord
from ibweb import composition

__all__ = [
    "servers_endpoint", "server_endpoint", "server_action_endpoint", "server_credentials_endpoint",
    "server_open_endpoint", "tools_endpoint", "tool_endpoint", "tool_review_endpoint", "tool_state_endpoint",
    "tool_binding_endpoint", "tool_waiver_endpoint", "governance_endpoint", "internal_allow_endpoint",
    "audit_endpoint",
]

_TOKEN = re.compile(r"^[a-z][a-z0-9_]*$")
_MESSAGES = {
    "mcp_disabled": "外部工具功能未启用",
    "transport_not_supported": "传输类型不受支持",
    "plain_http_public_forbidden": "公网目标禁止明文 http",
    "address_blocked": "地址被拒",
    "secret_key_missing": "凭证主密钥未配置",
    "server_id_invalid": "标识名不合法",
    "server_id_exists": "标识名已存在",
    "stale_update": "数据已被他处修改，请刷新后重试",
    "verification_failed": "连接验证未通过",
    "fingerprint_changed": "工具内容已变化，请重新查看后审核",
    "needs_review": "工具需先通过审核",
    "server_in_use": "该服务仍被项目授权引用",
    "cleanup_failed": "清理授权失败，服务已停用但未删除",
    "confirm_mismatch": "确认标识名不一致",
    "tenant_params_unacked": "存在疑似租户 / 项目 / 用户标识的必填参数，须显式确认",
    "project_unknown": "项目不存在或未启用",
    "unknown_field": "请求包含不支持的字段",
    "field_required": "缺少必填字段",
    "field_invalid": "字段取值不合法",
    "not_found": "资源不存在或不在可见范围内",
}
_SERVER_CREATE_KEYS = (
    "server_id", "description", "transport", "endpoint_url", "auth_kind", "auth_header_name",
    "credential_scope", "scope_kind", "owner_project", "data_categories",
)
_PATCH_KEYS = (
    "description", "endpoint_url", "auth_kind", "auth_header_name", "data_categories", "limits",
    "credential_scope", "transport",
)
_LIMIT_KEYS = (
    "call_timeout_s", "max_calls_per_turn", "max_result_bytes", "max_concurrency", "breaker_threshold",
    "breaker_cooldown_s", "discover_timeout_s",
)
_GOV_KEYS = tuple(MCP_HARD_MAX.keys())
_ACTIONS = ("verify", "enable", "disable", "refresh")
_STATUS_LABEL = {"registered": "待验证", "enabled": "已启用", "disabled": "已停用"}


def _v() -> Any:
    from ibweb import views

    return views


def _err(code: str, http: int, details: Any = None, message: str | None = None) -> Any:
    body: dict[str, Any] = {"code": code, "message": message or _MESSAGES.get(code, "请求无效")}
    if details:
        body["details"] = details
    return _v()._json({"error": body}, http)


def _bundle(*, write: bool) -> Any:
    deps = composition.get_deps()
    b = getattr(deps, "mcp", None)
    if b is None and write:
        raise _Respond(_err("mcp_disabled", status.HTTP_503_SERVICE_UNAVAILABLE))
    return b


class _Respond(Exception):
    def __init__(self, response: Any) -> None:
        super().__init__("respond")
        self.response = response


def _run(request: Any, methods: tuple[str, ...], handler: Callable[[Any], Any]) -> Any:
    """统一异常 → 响应映射；方法不允许 405。"""
    if request.method not in methods:
        return _err("method_not_allowed", status.HTTP_405_METHOD_NOT_ALLOWED, message="不支持的方法")
    try:
        return handler(request)
    except _Respond as r:
        return r.response
    except Exception as exc:  # noqa: BLE001 - 单点映射
        return _map_exc(exc)


def _map_exc(exc: BaseException) -> Any:
    from ib.mcp.admin import McpRequestError
    from ib.mcp.catalog import VerificationFailed
    from ibweb import config_views

    if isinstance(exc, McpRequestError):
        return _err(exc.code, exc.http, exc.details or None)
    if isinstance(exc, VerificationFailed):
        return _err("verification_failed", status.HTTP_409_CONFLICT, {"category": exc.category})
    if isinstance(exc, config_views.LevelDenied):
        return config_views.denied_response(exc)
    if isinstance(exc, (ValidationError, ConflictError)) and _TOKEN.match(str(exc.message)):
        http = status.HTTP_400_BAD_REQUEST if isinstance(exc, ValidationError) else status.HTTP_409_CONFLICT
        return _err(str(exc.message), http)
    if isinstance(exc, NotFoundError):
        return _err("not_found", status.HTTP_404_NOT_FOUND)
    if isinstance(exc, ScopeViolationError):
        return _v()._json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_403_FORBIDDEN)
    if isinstance(exc, (DependencyUnavailableError, IbError)):
        return _v().error_response(exc)
    return _v().error_response(exc)


def _body(request: Any) -> dict[str, Any]:
    raw = request.body or b""
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        raise _Respond(_err("field_invalid", 400, message="请求体不是合法 JSON")) from None
    if not isinstance(data, dict):
        raise _Respond(_err("field_invalid", 400, message="请求体必须是 JSON 对象"))
    return data


def _admin(request: Any) -> tuple[Any, str]:
    ctx = _v()._require_admin(request)
    return ctx, str(ctx.authz.actor_id)


def _is_admin(request: Any) -> bool:
    """与 `views._require_admin` 同口径：以主体自身（非"当前选定项目"）判定全局 admin。"""
    from ibweb.accounts import is_global
    from ibweb.authz import get_authz, get_policy

    ctx = _v()._ctx_of(request)
    authz = get_authz(request)
    return bool(authz is not None and is_global(authz) and get_policy(request).can_manage(ctx.authz))


def _reader(request: Any) -> tuple[bool, str | None]:
    """(是否全局 admin, 项目 id)。项目侧主体须有 config_level ≥ view。"""
    from ibweb import config_views

    ctx = _v()._ctx_of(request)
    if _is_admin(request):
        return True, None
    config_views.require_level(request, "read")
    return False, str(ctx.authz.project_id)


def _check_keys(body: dict[str, Any], allowed: tuple[str, ...], required: tuple[str, ...] = ()) -> None:
    unknown = sorted(k for k in body if k not in allowed)
    if unknown:
        raise _Respond(_err("unknown_field", 400, {"items": [{"path": k, "code": "unknown_field", "message": "不支持的字段"} for k in unknown[:20]]}))
    missing = [k for k in required if k not in body]
    if missing:
        raise _Respond(_err("field_required", 400, {"items": [{"path": k, "code": "field_required", "message": "缺少必填字段"} for k in missing]}))


# --------------------------------------------------------------------------- #
# DTO
# --------------------------------------------------------------------------- #


def _limits_dto(lim: McpServerLimits) -> dict[str, Any]:
    return {k: getattr(lim, k) for k in _LIMIT_KEYS}


def _server_dto(s: McpServer, b: Any, project: str | None = None) -> dict[str, Any]:
    counts = {k: 0 for k in ("pending_review", "enabled", "disabled", "needs_rereview", "offline", "excluded")}
    for t in b.stores.tools.list(server_id=s.server_id):
        counts[t.state] = counts.get(t.state, 0) + 1
    cred = {"shared": {"configured": False, "updated_at": None}, "discovery": {"configured": False, "updated_at": None}, "projects": []}
    for c in b.stores.credentials.status(s.server_id):
        if c.scope_key == "@shared":
            cred["shared"] = {"configured": True, "updated_at": c.updated_at}
        elif c.scope_key == "@discovery":
            cred["discovery"] = {"configured": True, "updated_at": c.updated_at}
        elif project is None or c.scope_key == project:  # 项目侧主体只见本项目的专属凭证状态（不枚举他项目）
            cred["projects"].append({"project_id": c.scope_key, "configured": True, "updated_at": c.updated_at})
    label = _STATUS_LABEL.get(s.admin_state, s.admin_state)
    if s.admin_state == "enabled" and s.health == "down":
        label += "（不可达）"
    return {
        "server_id": s.server_id, "description": s.description, "transport": s.transport, "endpoint_url": s.endpoint_url,
        "auth_kind": s.auth_kind, "auth_header_name": s.auth_header_name, "credential_scope": s.credential_scope,
        "scope_kind": s.scope_kind, "owner_project": s.owner_project, "open_all": s.open_all,
        "data_categories": list(s.data_categories), "admin_state": s.admin_state, "health": s.health,
        "status_label": label, "protocol_era": s.protocol_era, "protocol_version": s.protocol_version,
        "supports_list_changed": s.supports_list_changed, "last_verify_at": s.last_verify_at,
        "last_verify_result": s.last_verify_result, "tool_counts": counts, "credential": cred,
        "limits": _limits_dto(s.limits), "updated_at": s.updated_at,
    }


def _snap_dto(sn: Any) -> dict[str, Any] | None:
    if sn is None:
        return None
    return {
        "title": sn.title, "description": sn.description, "input_schema": sn.input_schema,
        "output_schema": sn.output_schema, "annotations": sn.annotations, "fingerprint": sn.fingerprint,
    }


def _tool_dto(t: McpToolRecord, b: Any, refs: dict[str, Any] | None = None) -> dict[str, Any]:
    recent = {"ok": 0, "failed": 0, "denied": 0, "error": 0}
    try:
        for r in b.stores.audit.query(tool_name=t.local_name, kind="call", limit=200):
            if r.outcome in recent:
                recent[r.outcome] += 1
    except Exception:  # noqa: BLE001
        recent = {}
    obs = t.observed
    return {
        "tool_id": t.tool_id, "server_id": t.server_id, "remote_name": t.remote_name, "local_name": t.local_name,
        "display_name": t.display_name, "state": t.state, "risk": t.risk, "exclusion_reason": t.exclusion_reason,
        "description": (obs.description if obs else (t.approved.description if t.approved else "")),
        "annotations": (obs.annotations if obs else {}),
        "annotations_note": "服务方自报，未经核实",
        "observed_fingerprint": obs.fingerprint if obs else None,
        "approved_fingerprint": t.approved.fingerprint if t.approved else None,
        "approved_at": t.approved_at, "approved_by": t.approved_by, "hidden_params": list(t.hidden_params),
        "llm_description": t.llm_description, "offline_at": t.offline_at, "offline_reason": t.offline_reason,
        "grants": [{"project_id": p, "expert_name": e} for p, e in (refs or {}).get(t.local_name, ())],
        "recent_calls": recent,
    }


def _visible_server(b: Any, server_id: str, project: str | None) -> McpServer:
    from ib.mcp.grants import visible_servers

    for s in visible_servers(project, stores=b.stores):
        if s.server_id == server_id:
            return s
    raise NotFoundError("not_found")  # "不存在"与"不属于你"同码


# --------------------------------------------------------------------------- #
# /api/mcp/servers
# --------------------------------------------------------------------------- #


def _parse_create(body: dict[str, Any]) -> Any:
    from ib.mcp.admin import McpRequestError, ServerCreate

    if "transport" in body and body["transport"] != "streamable_http":
        raise McpRequestError("transport_not_supported")  # AC-001-06：先于其他校验，且不创建
    _check_keys(body, _SERVER_CREATE_KEYS, ("server_id", "transport", "endpoint_url", "auth_kind", "data_categories"))
    cats = body["data_categories"]
    if not isinstance(cats, list):
        raise McpRequestError("data_categories_invalid")
    for k in ("server_id", "endpoint_url", "auth_kind"):
        if not isinstance(body[k], str):
            raise McpRequestError("field_invalid", details={"items": [{"path": k, "code": "field_invalid", "message": "须为字符串"}]})
    return ServerCreate(
        server_id=body["server_id"], description=body.get("description", ""), transport=body["transport"],
        endpoint_url=body["endpoint_url"], auth_kind=body["auth_kind"], auth_header_name=body.get("auth_header_name"),
        credential_scope=body.get("credential_scope", "shared"), scope_kind=body.get("scope_kind", "platform"),
        owner_project=body.get("owner_project"), data_categories=tuple(cats),
    )


def servers_endpoint(request: Any) -> Any:
    """IFC-R29-200 `GET /api/mcp/servers` / IFC-R29-201 `POST /api/mcp/servers`。"""

    def handle(request: Any) -> Any:
        if request.method == "GET":
            b = _bundle(write=False)
            if b is None:
                _reader(request)
                return _v()._json({"items": []}, 200)
            is_admin, project = _reader(request)
            from ib.mcp.grants import visible_servers

            return _v()._json({"items": [_server_dto(s, b, project) for s in visible_servers(project, stores=b.stores)]}, 200)
        _ctx, actor = _admin(request)  # 先鉴权，后解析请求体
        b = _bundle(write=True)
        spec = _parse_create(_body(request))
        s = b.admin.register(spec, actor=actor)
        return _v()._json(_server_dto(s, b), status.HTTP_201_CREATED)

    return _run(request, ("GET", "POST"), handle)


def server_endpoint(request: Any, server_id: str) -> Any:
    """IFC-R29-202 GET / IFC-R29-203 PATCH / IFC-R29-208 DELETE。"""

    def handle(request: Any) -> Any:
        if request.method == "GET":
            b = _bundle(write=False)
            is_admin, project = _reader(request)
            if b is None:
                raise NotFoundError("not_found")
            s = _visible_server(b, server_id, project)
            dto = _server_dto(s, b, project)
            refs = b.admin._index.references() if is_admin else {}
            names = {t.local_name for t in b.stores.tools.list(server_id=server_id)}
            projects = sorted({p for n in names for (p, _e) in refs.get(n, ())})
            dto["references_count"] = {"projects": len(projects), "agents": sum(len(refs.get(n, ())) for n in names)} if is_admin else None
            if is_admin:
                dto["references"] = {n: [{"project_id": p, "expert_name": e} for p, e in refs[n]] for n in names if n in refs}
                dto["open_projects"] = list(b.stores.servers.open_projects(server_id))
            return _v()._json(dto, 200)
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if request.method == "PATCH":
            return _patch(request, b, server_id, actor)
        # DELETE
        confirm = request.GET.get("confirm")
        force = request.GET.get("force", "0")
        if not confirm or force not in ("0", "1"):
            raise _Respond(_err("confirm_mismatch", 400))
        b.admin.delete(server_id, confirm=confirm, force=(force == "1"), actor=actor)
        return _no_content()

    return _run(request, ("GET", "PATCH", "DELETE"), handle)


def _no_content() -> Any:
    from django.http import HttpResponse

    return HttpResponse(status=204)


def _patch(request: Any, b: Any, server_id: str, actor: str) -> Any:
    from ib.mcp.admin import UNSET, McpRequestError, ServerPatch

    body = _body(request)
    if "transport" in body and body["transport"] != "streamable_http":
        raise McpRequestError("transport_not_supported")
    _check_keys(body, (*_PATCH_KEYS, "expected_updated_at"), ("expected_updated_at",))
    exp = body["expected_updated_at"]
    if not isinstance(exp, str):
        raise McpRequestError("field_invalid")
    kw: dict[str, Any] = {}
    for k in _PATCH_KEYS:
        if k in body:
            kw[k] = body[k]
    if "limits" in kw:
        lim = kw["limits"]
        if not isinstance(lim, dict) or any(x not in _LIMIT_KEYS for x in lim):
            raise McpRequestError("limits_invalid")
        kw["limits"] = McpServerLimits(**{x: lim.get(x) for x in _LIMIT_KEYS})
    if "data_categories" in kw and isinstance(kw["data_categories"], list):
        kw["data_categories"] = tuple(kw["data_categories"])
    before = b.stores.servers.get(server_id)
    if before is None:
        raise NotFoundError("not_found")
    res = b.admin.update(server_id, ServerPatch(**kw), expected_updated_at=exp, actor=actor)
    return _v()._json(
        {"server": _server_dto(res.server, b), "identity_changed": res.identity_changed,
         "tools_marked_rereview": res.tools_marked_rereview},
        200,
    )


def server_action_endpoint(request: Any, server_id: str, action: str) -> Any:
    """IFC-R29-204 verify / 205 enable / 206 disable / 207 refresh（POST，admin，空体）。"""

    def handle(request: Any) -> Any:
        if action not in _ACTIONS:
            raise NotFoundError("not_found")
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if b.stores.servers.get(server_id) is None:
            raise NotFoundError("not_found")
        if action == "verify":
            out = b.catalog.verify(server_id, actor=actor)
            payload: dict[str, Any] = {"ok": out.ok, "category": out.category}
            if out.negotiated is not None:
                payload.update(
                    protocol_version=out.negotiated.version, era=out.negotiated.era,
                    supports_list_changed=out.negotiated.supports_list_changed,
                    tools_capability=out.negotiated.tools_capability,
                )
            return _v()._json(payload, 200)  # 失败类别：200 + ok=false，不是 5xx
        if action == "enable":
            return _v()._json(_server_dto(b.admin.enable(server_id, actor=actor), b), 200)
        if action == "disable":
            return _v()._json(_server_dto(b.admin.disable(server_id, actor=actor), b), 200)
        d = b.catalog.refresh(server_id, actor=actor)
        return _v()._json(
            {"diff": {"added": list(d.added), "changed": list(d.changed), "offline": list(d.offline),
                      "reappeared": list(d.reappeared), "excluded": list(d.excluded), "unchanged": d.unchanged}}, 200)

    return _run(request, ("POST",), handle)


def server_credentials_endpoint(request: Any, server_id: str) -> Any:
    """IFC-R29-209 `PUT|DELETE /api/mcp/servers/{id}/credentials`——响应永不含值。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if request.method == "PUT":
            body = _body(request)
            _check_keys(body, ("scope", "project_id", "secret"), ("scope", "secret"))
            if not isinstance(body["secret"], str) or body["scope"] not in ("shared", "discovery", "project"):
                raise _Respond(_err("field_invalid", 400))
            pid = body.get("project_id")
            out = b.admin.set_credential(server_id, body["scope"], pid if isinstance(pid, str) else None, body["secret"], actor=actor)
            return _v()._json(
                {"scope": out.scope, "project_id": out.project_id, "configured": True,
                 "updated_at": out.updated_at, "updated_by": out.updated_by}, 200)
        scope = request.GET.get("scope", "")
        if scope not in ("shared", "discovery", "project"):
            raise _Respond(_err("field_invalid", 400))
        b.admin.clear_credential(server_id, scope, request.GET.get("project_id"), actor=actor)
        return _no_content()

    return _run(request, ("PUT", "DELETE"), handle)


def server_open_endpoint(request: Any, server_id: str) -> Any:
    """IFC-R29-210 `PUT /api/mcp/servers/{id}/open`。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        body = _body(request)
        _check_keys(body, ("open_all", "project_ids"), ("open_all", "project_ids"))
        if not isinstance(body["open_all"], bool) or not isinstance(body["project_ids"], list) or len(body["project_ids"]) > 200:
            raise _Respond(_err("field_invalid", 400))
        b.admin.set_open(server_id, open_all=body["open_all"], project_ids=[str(p) for p in body["project_ids"]], actor=actor)
        return _v()._json({"open_all": body["open_all"], "project_ids": list(b.stores.servers.open_projects(server_id))}, 200)

    return _run(request, ("PUT",), handle)


# --------------------------------------------------------------------------- #
# /api/mcp/tools
# --------------------------------------------------------------------------- #


def tools_endpoint(request: Any) -> Any:
    """IFC-R29-211。"""

    def handle(request: Any) -> Any:
        b = _bundle(write=False)
        is_admin, project = _reader(request)
        if b is None:
            return _v()._json({"items": []}, 200)
        from ib.core.types import MCP_RISKS, MCP_TOOL_STATES
        from ib.mcp.grants import visible_tools

        state = request.GET.get("state")
        risk = request.GET.get("risk")
        granted = request.GET.get("granted")
        if (state and state not in MCP_TOOL_STATES) or (risk and risk not in MCP_RISKS) or (granted not in (None, "", "0", "1")):
            raise _Respond(_err("field_invalid", 400))
        tools = visible_tools(project, stores=b.stores, server_id=request.GET.get("server_id") or None)
        refs = dict(b.admin._index.references()) if is_admin or granted else {}
        if granted in ("0", "1"):
            tools = tuple(t for t in tools if bool(refs.get(t.local_name)) == (granted == "1"))
        out = [
            _tool_dto(t, b, refs if is_admin else None)
            for t in tools
            if (not state or t.state == state) and (not risk or t.risk == risk)
        ]
        return _v()._json({"items": out}, 200)

    return _run(request, ("GET",), handle)


def _visible_tool(b: Any, tool_id: int, project: str | None) -> McpToolRecord:
    t = b.stores.tools.get(tool_id)
    if t is None:
        raise NotFoundError("not_found")
    _visible_server(b, t.server_id, project)
    if project is not None and t.state == "excluded":
        raise NotFoundError("not_found")
    return t


def tool_endpoint(request: Any, tool_id: int) -> Any:
    """IFC-R29-212。"""

    def handle(request: Any) -> Any:
        b = _bundle(write=False)
        is_admin, project = _reader(request)
        if b is None:
            raise NotFoundError("not_found")
        t = _visible_tool(b, tool_id, project)
        refs = dict(b.admin._index.references()) if is_admin else {}
        dto = _tool_dto(t, b, refs if is_admin else None)
        diff = b.catalog.tool_diff(tool_id)
        dto["observed"] = _snap_dto(t.observed)
        dto["approved"] = _snap_dto(t.approved)
        dto["diff"] = list(diff.changed_fields)
        if t.observed is not None:
            from ib.mcp.rules import suspect_tenant_params

            fixed = set()
            if is_admin:
                for _p, fa in b.stores.tools.bindings_for(tool_id).items():  # type: ignore[attr-defined]
                    fixed |= set(fa)
            dto["suspect_tenant_params"] = list(
                suspect_tenant_params(t.observed.input_schema, hidden=set(t.hidden_params), fixed=fixed)
            )
        if is_admin:  # 固定值可能含租户标识：仅 admin 详情可见
            dto["bindings"] = {p: dict(fa) for p, fa in b.stores.tools.bindings_for(tool_id).items()}  # type: ignore[attr-defined]
            dto["waivers"] = list(b.stores.tools.waiver_projects(tool_id))  # type: ignore[attr-defined]
        return _v()._json(dto, 200)

    return _run(request, ("GET",), handle)


def tool_review_endpoint(request: Any, tool_id: int) -> Any:
    """IFC-R29-213。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        body = _body(request)
        _check_keys(
            body, ("decision", "expected_fingerprint", "risk", "hidden_params", "llm_description", "ack_tenant_params"),
            ("decision",),
        )
        if b.stores.tools.get(tool_id) is None:
            raise NotFoundError("not_found")
        if body["decision"] == "reject":
            return _v()._json(_tool_dto(b.catalog.reject(tool_id, actor=actor), b), 200)
        if body["decision"] != "approve":
            raise _Respond(_err("field_invalid", 400))
        hidden = body.get("hidden_params", [])
        desc = body.get("llm_description")
        if (
            not isinstance(body.get("expected_fingerprint"), str) or not isinstance(body.get("risk"), str)
            or not isinstance(hidden, list) or len(hidden) > 50 or any(not isinstance(h, str) for h in hidden)
            or (desc is not None and (not isinstance(desc, str) or len(desc) > 1000))
            or not isinstance(body.get("ack_tenant_params", False), bool)
        ):
            raise _Respond(_err("field_invalid", 400))
        rec = b.catalog.approve(
            tool_id, expected_fingerprint=body["expected_fingerprint"], risk=body["risk"], hidden_params=hidden,
            llm_description=desc, ack_tenant_params=bool(body.get("ack_tenant_params", False)), actor=actor,
        )
        return _v()._json(_tool_dto(rec, b), 200)

    return _run(request, ("POST",), handle)


def tool_state_endpoint(request: Any, tool_id: int) -> Any:
    """IFC-R29-214。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        body = _body(request)
        _check_keys(body, ("enabled",), ("enabled",))
        if not isinstance(body["enabled"], bool):
            raise _Respond(_err("field_invalid", 400))
        if b.stores.tools.get(tool_id) is None:
            raise NotFoundError("not_found")
        return _v()._json(_tool_dto(b.catalog.set_tool_enabled(tool_id, body["enabled"], actor=actor), b), 200)

    return _run(request, ("POST",), handle)


def tool_binding_endpoint(request: Any, tool_id: int, project_id: str) -> Any:
    """IFC-R29-215：回显键名，不回显值。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        body = _body(request)
        _check_keys(body, ("fixed_args",), ("fixed_args",))
        if not isinstance(body["fixed_args"], dict):
            raise _Respond(_err("field_invalid", 400))
        b.admin.put_fixed_args(tool_id, project_id, body["fixed_args"], actor=actor)
        return _v()._json({"fixed_keys": sorted(body["fixed_args"])}, 200)

    return _run(request, ("PUT",), handle)


def tool_waiver_endpoint(request: Any, tool_id: int, project_id: str) -> Any:
    """IFC-R29-216。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if request.method == "PUT":
            body = _body(request)
            _check_keys(body, ("reason",), ("reason",))
            if not isinstance(body["reason"], str):
                raise _Respond(_err("field_invalid", 400))
            b.admin.grant_waiver(tool_id, project_id, reason=body["reason"], actor=actor)
            return _v()._json({"tool_id": tool_id, "project_id": project_id, "waived": True}, 200)
        b.admin.revoke_waiver(tool_id, project_id, actor=actor)
        return _no_content()

    return _run(request, ("PUT", "DELETE"), handle)


# --------------------------------------------------------------------------- #
# 治理 / 允许名单 / 审计
# --------------------------------------------------------------------------- #


def _gov_dto(g: McpGovernance) -> dict[str, Any]:
    out: dict[str, Any] = {k: getattr(g, k) for k in _GOV_KEYS}
    out["hard_max"] = {k: {"min": lo, "max": hi} for k, (lo, hi) in MCP_HARD_MAX.items()}
    out["updated_at"] = g.updated_at
    out["updated_by"] = g.updated_by
    return out


def governance_endpoint(request: Any) -> Any:
    """IFC-R29-217 `GET|PUT /api/mcp/governance`。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if request.method == "GET":
            try:
                g = b.stores.governance.get()
            except Exception:  # noqa: BLE001 - fail-closed：不以默认值冒充
                raise DependencyUnavailableError("治理参数存储不可用", dependency="ledger") from None
            return _v()._json(_gov_dto(g), 200)
        body = _body(request)
        _check_keys(body, _GOV_KEYS, _GOV_KEYS)
        for k in _GOV_KEYS:
            lo, hi = MCP_HARD_MAX[k]
            v = body[k]
            if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
                raise _Respond(_err("field_invalid", 400, {"items": [{"path": k, "code": "out_of_range", "message": f"须为 {lo}..{hi} 的整数"}]}))
        g = b.admin.set_governance(McpGovernance(**{k: body[k] for k in _GOV_KEYS}), actor=actor)
        return _v()._json(_gov_dto(g), 200)

    return _run(request, ("GET", "PUT"), handle)


def internal_allow_endpoint(request: Any) -> Any:
    """IFC-R29-217 `GET|POST|DELETE /api/mcp/internal-allow`。"""

    def handle(request: Any) -> Any:
        _ctx, actor = _admin(request)
        b = _bundle(write=True)
        if request.method == "GET":
            from ib.mcp.admin import McpAdminService  # noqa: F401
            import ipaddress

            from ib.webtools.netguard import NEVER_ALLOW_NETWORKS

            items = []
            for a in b.stores.servers.list_internal_allow():
                eff = True
                try:
                    ip = ipaddress.ip_address(a.host)
                    eff = not any(ip.version == n.version and ip in n for n in NEVER_ALLOW_NETWORKS)
                except ValueError:
                    pass
                items.append({"host": a.host, "port": a.port, "effective": eff, "created_at": a.created_at, "created_by": a.created_by})
            return _v()._json({"items": items}, 200)
        if request.method == "POST":
            body = _body(request)
            _check_keys(body, ("host", "port"), ("host", "port"))
            if not isinstance(body["host"], str):
                raise _Respond(_err("field_invalid", 400))
            r = b.admin.add_internal_allow(body["host"], body["port"], actor=actor)
            return _v()._json({"host": r.host, "port": r.port, "effective": r.effective}, status.HTTP_201_CREATED)
        host = request.GET.get("host", "")
        try:
            port = int(request.GET.get("port", ""))
        except ValueError:
            raise _Respond(_err("field_invalid", 400)) from None
        if not b.admin.remove_internal_allow(host, port, actor=actor):
            raise NotFoundError("not_found")
        return _no_content()

    return _run(request, ("GET", "POST", "DELETE"), handle)


def _iso(value: str | None, name: str) -> str | None:
    if not value:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise _Respond(_err("field_invalid", 400, {"items": [{"path": name, "code": "iso8601", "message": "须为 ISO8601"}]})) from None
    return value


def audit_endpoint(request: Any) -> Any:
    """IFC-R29-218：admin 全量；项目侧须 read_audit 档且强制 project_id = 本项目；终端用户 403。"""

    def handle(request: Any) -> Any:
        from ibweb import config_views

        ctx = _v()._ctx_of(request)
        if _is_admin(request):
            project = request.GET.get("project_id") or None
        else:
            config_views.require_level(request, "read_audit")
            project = str(ctx.authz.project_id)
        b = _bundle(write=False)
        if b is None:
            return _v()._json({"items": [], "total": 0}, 200)
        try:
            limit = int(request.GET.get("limit", "50"))
            offset = int(request.GET.get("offset", "0"))
        except ValueError:
            raise _Respond(_err("field_invalid", 400)) from None
        if not (1 <= limit <= 200) or offset < 0:
            raise _Respond(_err("field_invalid", 400))
        kind = request.GET.get("kind") or None
        if kind not in (None, "admin", "call", "system"):
            raise _Respond(_err("field_invalid", 400))
        flt = dict(
            server_id=request.GET.get("server_id") or None, tool_name=request.GET.get("tool") or None,
            project_id=project, kind=kind, ts_from=_iso(request.GET.get("from"), "from"),
            ts_to=_iso(request.GET.get("to"), "to"),
        )
        try:
            rows = b.stores.audit.query(limit=limit, offset=offset, **flt)
            total = b.stores.audit.count(**flt)
        except Exception:  # noqa: BLE001 - fail-closed：不以空集冒充
            raise DependencyUnavailableError("审计存储不可用", dependency="ledger") from None
        items = [
            {"call_id": r.call_id, "ts": r.ts, "kind": r.kind, "action": r.action, "actor": r.actor,
             "project_id": r.project_id, "server_id": r.server_id, "tool_name": r.tool_name,
             "display_name": r.display_name, "outcome": r.outcome, "reason": r.reason, "duration_ms": r.duration_ms,
             "args_digest": r.args_digest, "args_summary": r.args_summary, "fingerprint": r.fingerprint,
             "confirm": r.confirm, "trial": r.trial}
            for r in rows
        ]
        return _v()._json({"items": items, "total": total}, 200)

    return _run(request, ("GET",), handle)
