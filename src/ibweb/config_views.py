"""
@module MOD-R26-15
@implements IFC-R26-140 ~ IFC-R26-153（配置 HTTP 端点族：status / definition / validate / preview / publish /
            versions / rollback / adopt-drift / drafts / access / trial）；旧端点退化为发布包装的共用助手（IFC-R26-132）
@depends MOD-R26-03（档位）, MOD-R26-14（组合根）

纪律（沿用既有视图层）：
  * 项目归属只认服务端结论 `ctx.authz.project_id`，请求体里的项目标识一律忽略；
  * 档位判定集中在 `require_level`（纯函数 `ib.config.access`），不足 → 403 `permission_denied` + `required_level`；
  * 校验 / 保存失败逐条回执 `path` / `code` / `message`，不回显提示词正文与凭据；
  * 所有响应手写 DTO（不用 `asdict` 自动展开），提示词 / 关键词等不可信文本只作为 JSON 字符串返回。
"""

from __future__ import annotations

import json
from typing import Any, Callable

from rest_framework import status

from ib.config.access import REQUIRED_LEVEL, allows, config_level_of
from ib.core import (
    ConfigAuditEntry,
    ConfigError,
    DependencyUnavailableError,
    IbError,
    NotFoundError,
    PromptLayers,
    ScopeViolationError,
    ValidationError,
)
from ibweb import composition
from ibweb.accounts import GLOBAL_PROJECT

__all__ = [
    "LevelDenied",
    "require_level",
    "denied_response",
    "get_definition",
    "catalog_endpoint",
    "publish_legacy_definition",
    "publish_legacy_prompt",
    "status_endpoint",
    "validate_endpoint",
    "preview_endpoint",
    "publish_endpoint",
    "versions_endpoint",
    "version_detail_endpoint",
    "version_diff_endpoint",
    "rollback_endpoint",
    "adopt_drift_endpoint",
    "drafts_endpoint",
    "draft_detail_endpoint",
    "access_endpoint",
    "access_detail_endpoint",
    "trial_endpoint",
]

CONFIG_BODY_MAX_BYTES = 8 * 1024 * 1024
_PROMPT_BODY_LAYER_MAX = 1024 * 1024  # 单层文本的硬上限（防内存放大）；业务上限 20000 字符由 validate_prompt_texts 裁决
_MAX_PROMPT_EXPERTS = 200


# --------------------------------------------------------------------------- #
# 档位
# --------------------------------------------------------------------------- #


class LevelDenied(Exception):
    def __init__(self, required: str) -> None:
        super().__init__(required)
        self.required = required


def _views() -> Any:
    from ibweb import views  # 惰性导入：views 反向惰性导入本模块，避免模块级环

    return views


def require_level(request: Any, action: str) -> Any:
    """按动作所需档位判定；不足抛 `LevelDenied`（→ 403，响应含所需档位名）。返回请求上下文。"""
    ctx = _views()._ctx_of(request)
    if not allows(config_level_of(ctx.authz), action):  # type: ignore[arg-type]
        raise LevelDenied(REQUIRED_LEVEL.get(action, "manage"))
    return ctx


def denied_response(exc: LevelDenied) -> Any:
    return _views()._json(
        {
            "error": {
                "code": "permission_denied",
                "message": f"当前账号的配置权限不足（需要“{exc.required}”档）",
                "required_level": exc.required,
            }
        },
        status.HTTP_403_FORBIDDEN,
    )


def _project_id(ctx: Any) -> str:
    pid = ctx.authz.project_id
    if not pid or pid == GLOBAL_PROJECT:
        raise ScopeViolationError("未选定项目（管理员请先通过 X-IB-Project 选定项目）")
    return pid


# --------------------------------------------------------------------------- #
# DTO
# --------------------------------------------------------------------------- #


def _err_dto(i: Any) -> dict[str, Any]:
    return {"path": i.path, "code": i.code, "message": i.message}


def _diff_dto(i: Any) -> dict[str, Any]:
    return {"kind": i.kind, "object_id": i.object_id, "field": i.field, "before": i.before, "after": i.after}


def _receipt_dto(r: Any) -> dict[str, Any]:
    return {
        "base_version": r.base_version,
        "head_version": r.head_version,
        "base_available": r.base_available,
        "conflicts": [{"kind": c.kind, "object_id": c.object_id, "fields": list(c.fields)} for c in r.conflicts],
    }


def _record_dto(r: Any) -> dict[str, Any]:
    return {
        "version": r.version,
        "parent_version": r.parent_version,
        "kind": r.kind,
        "rolled_back_to": r.rolled_back_to,
        "actor": r.actor,
        "created_at": r.created_at,
        "summary": r.summary,
    }


def _draft_dto(r: Any) -> dict[str, Any]:
    return {
        "draft_id": r.draft_id,
        "label": r.label,
        "base_version": r.base_version,
        "created_at": r.created_at,
        "payload_bytes": r.payload_bytes,
    }


def _doc_dto(doc: Any) -> dict[str, Any]:
    """v2 文档的忠实序列化（含 graph / status / max_steps / knowledge_scope）。"""
    from ib.config import document_to_json

    return json.loads(document_to_json(doc))


def _graph_dto(doc: Any) -> dict[str, Any]:
    """图的显示 DTO：v2 取文档的图；v1 取规范化默认图（只读展示，文件不动）。"""
    from ib.config.definition import upgrade_to_v2

    d = doc if doc.schema_version == 2 and doc.graph is not None else upgrade_to_v2(doc)
    return _doc_dto(d)["graph"]


def _layers_summary(snapshot: Any) -> dict[str, Any]:
    return {name: pl for name, pl in snapshot.prompts}


def _agents_summary(doc: Any, snapshot: Any) -> list[dict[str, Any]]:
    layers = _layers_summary(snapshot)
    grants = {g.expert_name: g for g in doc.tool_grants}
    out = []
    for e in doc.experts:
        pl = layers.get(e.name, PromptLayers(None, None))
        main = pl.main or ""
        g = grants.get(e.name)
        out.append(
            {
                "name": e.name,
                "prompt_main_present": bool(main.strip()),
                "prompt_main_head": main[:120],
                "prompt_fallback_present": bool((pl.fallback or "").strip()),
                "tool_count": len(g.tool_names) if g else 0,
                "nondefault_param_count": len(g.param_values) if g else 0,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# 请求解析
# --------------------------------------------------------------------------- #


def _body(request: Any) -> dict[str, Any]:
    raw = request.body or b""
    if len(raw) > CONFIG_BODY_MAX_BYTES:
        raise ValidationError("请求体过大", field="body_too_large")
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("请求体不是合法 JSON") from exc
    if not isinstance(data, dict):
        raise ValidationError("请求体必须是 JSON 对象")
    return data


def _base_version(body: dict[str, Any], key: str = "base_version") -> int:
    v = body.get(key)
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ValidationError(f"{key} 必须是不小于 0 的整数", field=key)
    return v


def _parse_document(project_id: str, raw: Any) -> Any:
    from ib.config import document_from_json

    if not isinstance(raw, dict):
        raise ValidationError("缺少 document（JSON 对象）", field="document")
    try:
        return document_from_json(project_id, json.dumps(raw, ensure_ascii=False))
    except ConfigError as exc:
        raise ValidationError(f"定义文档格式不合法：{str(exc.message)[:200]}", field="document") from exc
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"定义文档格式不合法（{type(exc).__name__}）", field="document") from exc


def _parse_prompts(raw: Any) -> dict[str, PromptLayers]:
    if raw is None:
        return {}
    if not isinstance(raw, dict) or len(raw) > _MAX_PROMPT_EXPERTS:
        raise ValidationError("prompts 必须是 {专家名: {main?, fallback?}}（≤200 个专家）", field="prompts")
    out: dict[str, PromptLayers] = {}
    for name, layers in raw.items():
        if not isinstance(name, str) or not name or len(name) > 48 or not isinstance(layers, dict):
            raise ValidationError("prompts 条目不合法", field="prompts")
        vals: dict[str, str | None] = {}
        for k in ("main", "fallback"):
            v = layers.get(k)
            if v is not None and (not isinstance(v, str) or len(v) > _PROMPT_BODY_LAYER_MAX):
                raise ValidationError("提示词层必须是字符串（或 null 表示不变）", field=f"prompts.{name}.{k}")
            vals[k] = v
        out[name] = PromptLayers(vals["main"], vals["fallback"])
    return out


def _message(body: dict[str, Any]) -> str | None:
    m = body.get("message")
    if m is None:
        return None
    if not isinstance(m, str) or len(m) > 200:
        raise ValidationError("message 必须是不超过 200 字符的字符串", field="message")
    return m


def _publish_request(body: dict[str, Any], ctx: Any, project_id: str, *, with_message: bool = True) -> Any:
    from ib.confsvc import PublishError, PublishRequest
    from ib.config.definition import submitted_temperature_items

    # DEF-R26-002 / AC-021-03：请求体里主动提交的 temperature → 400 field_not_editable，不落盘、不写版本，写 rejected 审计。
    temp_items = submitted_temperature_items(body.get("document"))
    if temp_items:
        _views()._audit_definition_save(
            composition.get_deps(), project_id, str(ctx.authz.actor_id), (), "rejected", temp_items,
            action="config.publish",
        )
        raise PublishError("validation_error", "存在不可编辑字段的变更（temperature）", items=temp_items)
    return PublishRequest(
        project_id=project_id,
        actor=str(ctx.authz.actor_id),
        base_version=_base_version(body),
        document=_parse_document(project_id, body.get("document")),
        prompts=_parse_prompts(body.get("prompts")),
        message=_message(body) if with_message else None,
    )


# --------------------------------------------------------------------------- #
# 错误映射
# --------------------------------------------------------------------------- #


def _publish_error_response(exc: Any) -> Any:
    v = _views()
    code = exc.code
    msg = str(exc.message)
    if code == "validation_error":
        return v._json(
            {"error": {"code": "validation_error", "message": msg, "items": [_err_dto(i) for i in exc.items]}},
            status.HTTP_400_BAD_REQUEST,
        )
    if code == "conflict":
        return v._json(
            {"error": {"code": "conflict", "message": msg, "receipt": _receipt_dto(exc.receipt) if exc.receipt else None}},
            status.HTTP_409_CONFLICT,
        )
    http = {
        "config_busy": status.HTTP_409_CONFLICT,
        "no_changes": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "apply_failed": status.HTTP_503_SERVICE_UNAVAILABLE,
        "version_not_found": status.HTTP_404_NOT_FOUND,
        "drift_detected": status.HTTP_409_CONFLICT,
    }.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return v._json({"error": {"code": code, "message": msg}}, http)


def _run(request: Any, table: dict[str, tuple[str, Callable[..., Any]]], **kw: Any) -> Any:
    """统一入口：开关 → 方法 → 档位 → 业务；异常集中映射（同视图层单点映射纪律）。"""
    from ib.confsvc import PublishError
    from ib.runtime import ConfigVersionExpiredError, TrialBusyError, ValidationFailed

    v = _views()
    if not v._visual_config_enabled():
        return v._json({"error": {"code": "not_found", "message": "可视化配置未启用"}}, status.HTTP_404_NOT_FOUND)
    entry = table.get(request.method)
    if entry is None:
        return v._json({"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
                       status.HTTP_405_METHOD_NOT_ALLOWED)
    action, handler = entry
    try:
        ctx = require_level(request, action)
        # 旧端点（GET definition）未选定项目时沿用既有的 fail-closed 503（定义文档不可读），不改为 403
        pid = ctx.authz.project_id if kw.pop("lenient_project", False) else _project_id(ctx)
        deps = composition.get_deps()
        if getattr(deps, "publish_service", None) is None:
            raise DependencyUnavailableError("配置发布服务未装配", dependency="config")
        return handler(deps, ctx, pid, request, **kw)
    except LevelDenied as exc:
        return denied_response(exc)
    except PublishError as exc:
        return _publish_error_response(exc)
    except ValidationFailed as exc:
        return v._json(
            {"error": {"code": "validation_error", "message": "草稿配置校验未通过",
                       "items": [_err_dto(i) for i in exc.items]}},
            status.HTTP_400_BAD_REQUEST,
        )
    except TrialBusyError as exc:
        return v._json({"error": {"code": "trial_busy", "message": str(exc.message)}}, 429)
    except ConfigVersionExpiredError as exc:
        return v._json({"error": {"code": exc.code, "message": str(exc.message)}}, status.HTTP_409_CONFLICT)
    except ConfigError:
        return v._read_failure_response()
    except IbError as exc:
        return v.error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return v.error_response(exc)


def _ok(payload: Any, code: int = status.HTTP_200_OK) -> Any:
    return _views()._json(payload, code)


def _result_dto(res: Any) -> dict[str, Any]:
    return {
        "version": res.version,
        "previous_version": res.previous_version,
        "content_hash": res.content_hash,
        "applied": True,
    }


# --------------------------------------------------------------------------- #
# IFC-R26-140 status
# --------------------------------------------------------------------------- #


def _status(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    head = deps.version_store.head(pid)
    err: str | None = None
    try:
        deps.runtime_cache.acquire(pid)  # 保证已冷编译（失败则如实报 apply_failed，不返回空）
    except Exception as exc:  # noqa: BLE001
        err = str(getattr(exc, "code", "") or type(exc).__name__)[:60]
    st = deps.runtime_cache.status(pid)
    doc = deps.publish_service.current(pid).definition
    return _ok(
        {
            "version": head.published_version,
            "applied_version": st.applied_version,
            "apply_state": "apply_failed" if err else st.state,
            "drift": st.drift,
            "pending": head.pending_version is not None,
            "schema_version": doc.schema_version,
            "legacy": doc.schema_version == 1,
            "level": config_level_of(ctx.authz),
            **({"last_error_code": err} if err else {}),
        }
    )


def status_endpoint(request: Any) -> Any:
    return _run(request, {"GET": ("read", _status)})


# --------------------------------------------------------------------------- #
# IFC-R26-141 definition（既有端点的扩展读）
# --------------------------------------------------------------------------- #


def get_definition(request: Any) -> Any:
    """`GET /api/config/definition`：既有响应的超集（追加 version / level / graph / agents / 工具与目录清单）。"""
    from ibweb.serializers import DefinitionDocumentSerializer, definition_derived_summary

    v = _views()

    def _h(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
        doc = deps.definition_store.load(pid)  # IFC-IB-288
        view = deps.definition_store.derive(doc)  # IFC-IB-291
        snapshot = deps.publish_service.current(pid)
        if doc.schema_version == 2:
            derived = {
                "capability_digest": view.capability_digest,
                "expert_names": [e.name for e in doc.experts if getattr(e, "status", "active") == "active"],
                "nodes": [], "conditional_edges": [], "edges": [],
                "experts": [{"name": e.name, "cn_label": e.cn_label, "is_default": bool(e.is_default)}
                            for e in doc.experts],
            }
            document = _doc_dto(doc)
        else:
            derived = definition_derived_summary(view)  # IFC-IB-393：v1 沿用既有投影
            document = DefinitionDocumentSerializer().to_representation(doc)
        if doc.schema_version == 2:
            derived["agents"] = _agents_summary(doc, snapshot)  # IFC-R26-141：仅 v2 追加；v1 沿用 ADR-52 投影
        head = deps.version_store.head(pid)
        return _ok(
            {
                "document": document,
                "derived": derived,
                "editable_fields": sorted(deps.definition_store.editable_field_whitelist()),
                "config_key_names": ["IB_DEFINITION_DOC_PATH", "IB_VISUAL_CONFIG_ENABLED"],
                "version": head.published_version,
                "level": config_level_of(ctx.authz),
                "graph": _graph_dto(doc),
            }
        )

    return _run(request, {"GET": ("read", _h)}, lenient_project=True)


def _catalog(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    """`GET /api/config/catalog`：配置页的选项来源（既有工具 / 参数规格 / 资料目录 / 各 agent 摘要）。只读，不含凭据。"""
    v = _views()
    doc = deps.definition_store.load(pid)
    snapshot = deps.publish_service.current(pid)
    try:
        folders = [{"folder_id": fid, "path": p} for fid, p in composition._project_folder_index(deps, pid).items()]
    except Exception:  # noqa: BLE001 - 目录不可读不影响配置读取
        folders = []
    return _ok(
        {
            "available_tools": list(composition.known_tool_names()),
            "tool_param_specs": [v._tool_param_spec_payload(s) for s in composition.known_tool_param_specs()],
            "folders": folders,
            "agents": _agents_summary(doc, snapshot),
            "schema_version": doc.schema_version,
        }
    )


def catalog_endpoint(request: Any) -> Any:
    return _run(request, {"GET": ("read", _catalog)})


# --------------------------------------------------------------------------- #
# IFC-R26-142 ~ 144 validate / preview / publish
# --------------------------------------------------------------------------- #


def _validate(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    body = _body(request)
    req = _publish_request({**body, "base_version": 0}, ctx, pid, with_message=False)
    errors = deps.publish_service.validate(req)
    return _ok({"ok": not errors, "errors": [_err_dto(i) for i in errors]})


def validate_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("validate", _validate)})


def _preview(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    req = _publish_request(_body(request), ctx, pid, with_message=False)
    p = deps.publish_service.preview(req)
    return _ok(
        {
            "base_version": p.base_version,
            "head_version": p.head_version,
            "items": [_diff_dto(i) for i in p.items],
            "layout_only": p.layout_only,
            "errors": [_err_dto(i) for i in p.errors],
        }
    )


def preview_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("preview", _preview)})


def _publish(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    req = _publish_request(_body(request), ctx, pid)
    return _ok(_result_dto(deps.publish_service.publish(req)))


def publish_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("publish", _publish)})


# --------------------------------------------------------------------------- #
# IFC-R26-145 ~ 149 versions / rollback / adopt-drift
# --------------------------------------------------------------------------- #


def _versions(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    raw_limit = request.GET.get("limit")
    limit = 50
    if raw_limit not in (None, ""):
        try:
            limit = int(raw_limit)
        except ValueError:
            raise ValidationError("limit 必须是整数", field="limit") from None
        if not 1 <= limit <= 50:
            raise ValidationError("limit 须在 1..50", field="limit")
    before: int | None = None
    if request.GET.get("before") not in (None, ""):
        try:
            before = int(request.GET["before"])
        except ValueError:
            raise ValidationError("before 必须是整数", field="before") from None
    items = deps.version_store.list_versions(pid, limit=limit, before_version=before)
    return _ok({"head": deps.version_store.head(pid).published_version, "items": [_record_dto(r) for r in items]})


def versions_endpoint(request: Any) -> Any:
    return _run(request, {"GET": ("read", _versions)})


def _get_version_or_404(deps: Any, pid: str, n: int) -> Any:
    found = deps.version_store.get_version(pid, int(n))
    if found is None:
        raise NotFoundError("版本不存在、已被修剪或不属于本项目")
    return found


def _version_detail(deps: Any, ctx: Any, pid: str, request: Any, *, n: int) -> Any:
    record, snap = _get_version_or_404(deps, pid, n)
    body: dict[str, Any] = {
        "record": _record_dto(record),
        "document": _doc_dto(snap.definition),
        "prompts_summary": [
            {"expert": name, "main_len": len(pl.main or ""), "fallback_len": len(pl.fallback or "")}
            for name, pl in snap.prompts
        ],
    }
    if request.GET.get("include") == "prompts":  # 查看档可见提示词全文（OQ-R26-07=A）
        body["prompts"] = {name: {"main": pl.main, "fallback": pl.fallback} for name, pl in snap.prompts}
    return _ok(body)


def version_detail_endpoint(request: Any, n: int) -> Any:
    return _run(request, {"GET": ("read", _version_detail)}, n=n)


def _version_diff(deps: Any, ctx: Any, pid: str, request: Any, *, n: int) -> Any:
    from ib.config.versioning import diff_snapshots, is_layout_only

    against = request.GET.get("against") or "head"
    target_rec, target = _get_version_or_404(deps, pid, n)
    if against == "head":
        m = deps.version_store.head(pid).published_version
    else:
        try:
            m = int(against)
        except ValueError:
            raise ValidationError("against 必须是版本号或 head", field="against") from None
    if m <= 0:
        base_snap = deps.publish_service.current(pid)
    else:
        _rec, base_snap = _get_version_or_404(deps, pid, m)
    items = diff_snapshots(base_snap, target)
    return _ok({"from": m, "to": target_rec.version, "items": [_diff_dto(i) for i in items],
                "layout_only": is_layout_only(items)})


def version_diff_endpoint(request: Any, n: int) -> Any:
    return _run(request, {"GET": ("read", _version_diff)}, n=n)


def _rollback(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    body = _body(request)
    target = _base_version(body, "target_version")
    res = deps.publish_service.rollback(
        pid, str(ctx.authz.actor_id), target_version=target, base_version=_base_version(body), message=_message(body)
    )
    return _ok(_result_dto(res))


def rollback_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("rollback", _rollback)})


def _adopt(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    from ib.confsvc import PublishError

    body = _body(request)
    try:
        res = deps.publish_service.adopt_drift(pid, str(ctx.authz.actor_id), base_version=_base_version(body))
    except PublishError as exc:
        if exc.code == "no_changes":
            return _views()._json({"error": {"code": "no_drift", "message": "文件态与已发布版本一致，无漂移"}},
                                  status.HTTP_409_CONFLICT)
        raise
    return _ok(_result_dto(res))


def adopt_drift_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("adopt_drift", _adopt)})


# --------------------------------------------------------------------------- #
# IFC-R26-150 drafts
# --------------------------------------------------------------------------- #


def _drafts_list(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    items = deps.draft_service.list(pid, str(ctx.authz.actor_id))
    return _ok({"items": [_draft_dto(r) for r in items]})


def _drafts_create(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    body = _body(request)
    label = body.get("label")
    if not isinstance(label, str) or not 1 <= len(label.strip()) <= 60:
        raise ValidationError("label 须为 1..60 字符", field="label")
    doc = body.get("document")
    if not isinstance(doc, dict):
        raise ValidationError("缺少 document（JSON 对象）", field="document")
    _parse_prompts(body.get("prompts"))  # 只校验形状
    payload = json.dumps({"document": doc, "prompts": body.get("prompts") or {}}, ensure_ascii=False)
    try:
        rec = deps.draft_service.save(
            pid, str(ctx.authz.actor_id), label=label, base_version=_base_version(body), payload_json=payload
        )
    except ValidationError as exc:
        field = getattr(exc, "field", None) or "draft"
        return _views()._json(
            {"error": {"code": "draft_quota" if field == "draft_quota" else "validation_error",
                       "message": str(exc.message), "field": field}},
            status.HTTP_400_BAD_REQUEST,
        )
    return _ok(_draft_dto(rec), status.HTTP_201_CREATED)


def drafts_endpoint(request: Any) -> Any:
    return _run(request, {"GET": ("draft", _drafts_list), "POST": ("draft", _drafts_create)})


def _draft_get(deps: Any, ctx: Any, pid: str, request: Any, *, draft_id: str) -> Any:
    found = deps.draft_service.load(pid, str(ctx.authz.actor_id), draft_id)
    if found is None:
        raise NotFoundError("草稿不存在")  # 他人草稿与不存在同码
    rec, payload = found
    data = json.loads(payload)
    return _ok({"record": _draft_dto(rec), "document": data.get("document"), "prompts": data.get("prompts") or {}})


def _draft_delete(deps: Any, ctx: Any, pid: str, request: Any, *, draft_id: str) -> Any:
    if not deps.draft_service.delete(pid, str(ctx.authz.actor_id), draft_id):
        raise NotFoundError("草稿不存在")
    from django.http import HttpResponse

    return HttpResponse(status=204)


def draft_detail_endpoint(request: Any, draft_id: str) -> Any:
    return _run(request, {"GET": ("draft", _draft_get), "DELETE": ("draft", _draft_delete)}, draft_id=draft_id)


# --------------------------------------------------------------------------- #
# IFC-R26-151 access
# --------------------------------------------------------------------------- #


def _access_list(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    rows = deps.account_levels.list_project_levels(pid)
    return _ok({"items": [
        {"user_id": uid, "username": name, "config_level": lv, "status": st} for uid, name, lv, st in rows
    ]})


def _access_put(deps: Any, ctx: Any, pid: str, request: Any, *, user_id: str) -> Any:
    from ib.config.access import can_grant
    from ib.context import utc_now_iso

    body = _body(request)
    level = body.get("config_level")
    if level not in ("view", "edit", "manage"):
        raise ValidationError("config_level 只能为 view / edit / manage", field="config_level")
    if not can_grant(ctx.authz, grantor_project_id=pid, target_project_id=pid):
        raise LevelDenied("manage")
    rows = {uid: (name, lv, st) for uid, name, lv, st in deps.account_levels.list_project_levels(pid)}
    if user_id not in rows:
        raise NotFoundError("账号不存在或不在本项目")
    name, current, st = rows[user_id]
    is_admin = "admin" in ctx.authz.roles
    if current == "manage" and level != "manage" and not is_admin:
        managers = [u for u, (_n, lv, s) in rows.items() if lv == "manage" and s == "active"]
        if managers == [user_id]:
            return _views()._json(
                {"error": {"code": "last_manager", "message": "不能降级本项目最后一个“管理”档账号"}},
                status.HTTP_409_CONFLICT,
            )
    now = utc_now_iso()
    # 权限变更与审计同一事务（CR-009 / REQ-NFUNC-006）：审计写失败则档位不变并返回错误
    ok = deps.account_levels.set_config_level(
        user_id, level, now=now,
        audit=ConfigAuditEntry(
            timestamp=now, project=pid, actor=str(ctx.authz.actor_id), action="access.grant",
            changed_field_names=("config_level",), result="saved", detail_code=None,
            object_summary=(f"user:{user_id}", f"from:{current}", f"to:{level}"),
        ),
    )
    if not ok:
        raise NotFoundError("账号不存在或不在本项目")
    return _ok({"user_id": user_id, "username": name, "config_level": level, "status": st})


def access_endpoint(request: Any) -> Any:
    return _run(request, {"GET": ("grant_access", _access_list)})


def access_detail_endpoint(request: Any, user_id: str) -> Any:
    return _run(request, {"PUT": ("grant_access", _access_put)}, user_id=user_id)


# --------------------------------------------------------------------------- #
# IFC-R26-152 trial（SSE）
# --------------------------------------------------------------------------- #


def _trial(deps: Any, ctx: Any, pid: str, request: Any) -> Any:
    from ib.context import utc_now_iso
    from ibweb.sse import streaming_sse_response

    body = _body(request)
    query = body.get("query")
    session_id = body.get("session_id")
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 2000:
        raise ValidationError("query 须为 1..2000 字符", field="query")
    if not isinstance(session_id, str) or not 1 <= len(session_id) <= 64 or ":" in session_id:
        raise ValidationError("session_id 须为 1..64 字符且不含 ':'", field="session_id")
    req = _publish_request({**body, "base_version": 0}, ctx, pid, with_message=False)
    snapshot = deps.publish_service.candidate(req)
    events = deps.trial_runner.run(pid, snapshot, query.strip(), ctx=ctx, session_id=session_id)  # 校验 / 限流 / 编译在此完成
    composition.record_config_audit(
        ConfigAuditEntry(
            timestamp=utc_now_iso(), project=pid, actor=str(ctx.authz.actor_id), action="config.trial",
            changed_field_names=(), result="saved", detail_code=None, object_summary=("trial",),
        ),
        deps=deps,
    )
    return streaming_sse_response(events)


def trial_endpoint(request: Any) -> Any:
    return _run(request, {"POST": ("trial", _trial)})


# --------------------------------------------------------------------------- #
# 旧端点退化为发布包装（IFC-R26-132）
# --------------------------------------------------------------------------- #


def publish_legacy_definition(
    deps: Any, project_id: str, actor: str, submitted: Any, current: Any, expected: str | None, changed: tuple[str, ...]
) -> Any:
    """`PUT /api/config/definition` 的写入段：保持旧响应形状（SaveResult + `version`），但经发布协议落盘并热生效。"""
    from ib.confsvc import PublishError, PublishRequest
    from ib.config.definition import content_hash_conflict_item
    from ib.core import SaveResult
    from ibweb.serializers import SaveResultSerializer

    v = _views()
    if expected and expected != current.content_hash:  # 旧乐观并发：语义哈希对不上 ⇒ 409，未覆盖
        res = SaveResult(ok=False, content_hash=current.content_hash, conflict=True,
                         errors=(content_hash_conflict_item(expected, current.content_hash),))
        v._audit_definition_save(deps, project_id, actor, changed, "rejected", res.errors,
                                 detail_code="content_hash_conflict")
        return v._json(
            {"error": {"code": "conflict", "message": "定义文档已被他处修改（乐观并发冲突，未覆盖）",
                       "receipt": SaveResultSerializer().to_representation(res)}},
            status.HTTP_409_CONFLICT,
        )
    head = deps.version_store.head(project_id)
    req = PublishRequest(
        project_id=project_id, actor=actor, base_version=head.published_version, document=submitted, prompts={},
        audit_action="definition.save", audit_fields=tuple(changed),
    )
    try:
        out = deps.publish_service.publish(req)
    except PublishError as exc:
        if exc.code == "no_changes":  # 与旧行为一致：保存与现状相同的文档仍视为成功
            res = SaveResult(ok=True, content_hash=current.content_hash, conflict=False, errors=())
            return v._json({**SaveResultSerializer().to_representation(res), "version": head.published_version},
                           status.HTTP_200_OK)
        return _publish_error_response(exc)
    res = SaveResult(ok=True, content_hash=out.content_hash, conflict=False, errors=())
    return v._json({**SaveResultSerializer().to_representation(res), "version": out.version}, status.HTTP_200_OK)


def publish_legacy_prompt(
    deps: Any, project_id: str, actor: str, expert: str, layer: str, content: str, expected: str | None
) -> Any:
    """`PUT /api/config/prompts/{expert}/{layer}` 的写入段：乐观并发哈希核对后经发布协议落盘并热生效。"""
    from ib.confsvc import PublishError, PublishRequest
    from ib.config.prompts import prompt_content_hash
    from ib.core import PromptSaveResult

    v = _views()
    store = (deps.prompt_stores or {}).get(project_id)
    refs = {(r.expert_name, r.layer): r for r in store.list_refs()}
    ref = refs.get((expert, layer))
    current_hash = ref.content_hash if ref is not None and ref.exists else ""
    if expected is not None and expected != current_hash:
        # 哈希不一致：`save_layer` 在乐观并发分支返回 `saved=False` 且不落盘 → 与旧回执同形
        result = store.save_layer(expert, layer, content, expected_hash=expected)
        return v._json(
            {"error": {"code": "conflict", "message": "提示词已被他处修改（乐观并发冲突，未覆盖）",
                       "receipt": v._prompt_result_body(result)}},
            status.HTTP_409_CONFLICT,
        )
    doc = deps.definition_store.load(project_id)
    patch = {expert: PromptLayers(content if layer == "main" else None, content if layer == "fallback" else None)}
    head = deps.version_store.head(project_id)
    req = PublishRequest(
        project_id=project_id, actor=actor, base_version=head.published_version, document=doc, prompts=patch,
        audit_action="prompt.save", audit_fields=(f"prompt[{expert}].{layer}",),
    )
    try:
        deps.publish_service.publish(req)
    except PublishError as exc:
        if exc.code == "no_changes":
            pass
        elif exc.code == "validation_error":
            return v._validation_failure_response(exc.items, "提示词保存未生效")
        else:
            return _publish_error_response(exc)
    new_hash = prompt_content_hash(content)
    result = PromptSaveResult(saved=True, ref=ref, content_hash=new_hash, errors=())  # type: ignore[arg-type]
    return v._json(v._prompt_result_body(result), status.HTTP_200_OK)
