"""
@module MOD-R26-16
@implements IFC-R26-160 ~ IFC-R26-163（Agent Builder HTTP 端点：draft / evaluate / optimize / review-existing）
@depends MOD-R26-03（档位）, MOD-R26-11（BuilderService）, MOD-R26-14（组合根）

纪律：
  * 最低“编辑”档，不足 → 403 且**不向云端发出任何请求**（在调用 `BuilderService` 之前判定）；
  * 本模块只调用 `BuilderService`（其类型层无任何写配置的端口）——响应里只有草案，**从不写入配置**（REQ-FUNC-021）；
  * 所有失败路径：不产生草案、不改配置、版本号不变；错误文案可读、不含凭据；
  * 空白表单与克隆**不经这里**（前端组装草稿后走 `POST /api/config/validate`），LLM 不可用时手工方式照常可用。
"""

from __future__ import annotations

import json
from typing import Any, Callable

from rest_framework import status

from ib.builder.rubric import LLM_CHECK_IDS
from ib.builder.types import (
    AdaptationNote,
    AgentDraft,
    BuilderBusy,
    BuilderUnavailable,
    EgressRejected,
    ExpertNotFound,
    FieldChange,
    RubricResult,
)
from ib.core import ConfigError, DependencyUnavailableError, IbError, ValidationError
from ibweb import composition
from ibweb.config_views import LevelDenied, denied_response, require_level

__all__ = [
    "builder_draft_endpoint",
    "builder_evaluate_endpoint",
    "builder_optimize_endpoint",
    "builder_review_existing_endpoint",
]

_BODY_MAX_BYTES = 1024 * 1024
_STR_MAX = 20000
_EGRESS_MESSAGES = {
    "egress_secret_detected": "内容疑似包含密钥 / 口令，已拒绝外发",
    "egress_payload_too_large": "外发内容过大，已拒绝",
    "requirement_empty": "需求描述不能为空",
    "requirement_too_long": "需求描述 / 修改意见过长",
}


def _views() -> Any:
    from ibweb import views

    return views


def _draft_dto(d: AgentDraft) -> dict[str, Any]:
    return {
        "name": d.name, "cn_label": d.cn_label, "main_prompt": d.main_prompt, "fallback_prompt": d.fallback_prompt,
        "keywords": list(d.keywords), "exemplars": list(d.exemplars), "is_data_expert": d.is_data_expert,
        "is_delegating": d.is_delegating, "tool_names": list(d.tool_names),
        "tool_params": [[n, v] for n, v in d.tool_params], "knowledge_folder_ids": list(d.knowledge_folder_ids),
        "max_steps": d.max_steps, "source": d.source,
    }


def _note_dto(n: AdaptationNote) -> dict[str, Any]:
    return {"code": n.code, "field": n.field, "message": n.message}


def _rubric_dto(r: RubricResult) -> dict[str, Any]:
    return {
        "rubric_version": r.rubric_version, "total": r.total, "grade": r.grade,
        "dimension_scores": dict(r.dimension_scores),
        "deductions": [
            {
                "dimension": d.dimension, "check_id": d.check_id, "field": d.field, "points": d.points,
                "evidence": d.evidence,
                "llm_judged": d.check_id in LLM_CHECK_IDS,  # A04：界面标注哪些分数来自 LLM 判定
            }
            for d in r.deductions
        ],
        "llm_check_ids": list(LLM_CHECK_IDS),
        "coverage": r.coverage, "cache_hit": r.cache_hit,
    }


def _change_dto(c: FieldChange) -> dict[str, Any]:
    return {"field": c.field, "before": c.before, "after": c.after, "note": c.note}


def _body(request: Any) -> dict[str, Any]:
    raw = request.body or b""
    if len(raw) > _BODY_MAX_BYTES:
        raise ValidationError("请求体过大", field="body_too_large")
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("请求体不是合法 JSON") from exc
    if not isinstance(data, dict):
        raise ValidationError("请求体必须是 JSON 对象")
    return data


def _s(d: dict[str, Any], key: str, *, low: int = 0, high: int = _STR_MAX) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not low <= len(v) <= high:
        raise ValidationError(f"{key} 必须是 {low}..{high} 字符的字符串", field=key)
    return v


def _str_list(d: dict[str, Any], key: str, *, max_items: int, max_len: int = 200) -> tuple[str, ...]:
    v = d.get(key, [])
    if not isinstance(v, list) or len(v) > max_items or any(not isinstance(x, str) or len(x) > max_len for x in v):
        raise ValidationError(f"{key} 必须是不超过 {max_items} 项的字符串数组", field=key)
    return tuple(v)


def _draft_of(raw: Any) -> AgentDraft:
    """请求里的草案 DTO → `AgentDraft`（字段长度 / 条数上限同 `AgentDraft`；非法 → 400）。"""
    if not isinstance(raw, dict):
        raise ValidationError("缺少 draft（JSON 对象）", field="draft")
    params_raw = raw.get("tool_params", [])
    if not isinstance(params_raw, list) or len(params_raw) > 50:
        raise ValidationError("tool_params 不合法", field="tool_params")
    params: list[tuple[str, str | int | float | bool]] = []
    for item in params_raw:
        if not (isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], str)
                and isinstance(item[1], (str, int, float, bool))):
            raise ValidationError("tool_params 条目须为 [名称, 值]", field="tool_params")
        params.append((item[0], item[1]))
    steps = raw.get("max_steps", 4)
    if isinstance(steps, bool) or not isinstance(steps, int):
        raise ValidationError("max_steps 必须是整数", field="max_steps")
    source = raw.get("source", "generated")
    if source not in ("generated", "optimized", "cloned", "blank"):
        raise ValidationError("source 不合法", field="source")
    return AgentDraft(
        name=_s(raw, "name", high=48), cn_label=_s(raw, "cn_label", high=32),
        main_prompt=_s(raw, "main_prompt"), fallback_prompt=_s(raw, "fallback_prompt"),
        keywords=_str_list(raw, "keywords", max_items=20, max_len=32),
        exemplars=_str_list(raw, "exemplars", max_items=10, max_len=200),
        is_data_expert=bool(raw.get("is_data_expert", False)), is_delegating=bool(raw.get("is_delegating", False)),
        tool_names=_str_list(raw, "tool_names", max_items=20, max_len=64), tool_params=tuple(params),
        knowledge_folder_ids=_str_list(raw, "knowledge_folder_ids", max_items=200, max_len=64),
        max_steps=steps, source=source,
    )


def _run(request: Any, handler: Callable[..., Any]) -> Any:
    v = _views()
    if not v._visual_config_enabled():
        return v._json({"error": {"code": "not_found", "message": "可视化配置未启用"}}, status.HTTP_404_NOT_FOUND)
    if request.method != "POST":
        return v._json({"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
                       status.HTTP_405_METHOD_NOT_ALLOWED)
    try:
        ctx = require_level(request, "builder")  # 先判档位：不足 → 403，且根本不进入 BuilderService（出站载荷数 = 0）
        pid = ctx.authz.project_id
        from ibweb.accounts import GLOBAL_PROJECT

        if not pid or pid == GLOBAL_PROJECT:
            raise ValidationError("未选定项目（管理员请先通过 X-IB-Project 选定项目）")
        deps = composition.get_deps()
        service = getattr(deps, "builder_service", None)
        if service is None:
            raise DependencyUnavailableError("Agent Builder 未装配", dependency="builder")
        return handler(deps, service, ctx, pid, _body(request))
    except LevelDenied as exc:
        return denied_response(exc)
    except EgressRejected as exc:
        return v._json(
            {"error": {"code": "egress_rejected", "message": _EGRESS_MESSAGES.get(exc.code, "外发被拒绝"),
                       "reason": exc.code}},
            status.HTTP_400_BAD_REQUEST,
        )
    except BuilderBusy:
        return v._json({"error": {"code": "builder_busy", "message": "Agent Builder 繁忙，请稍后再试"}}, 429)
    except BuilderUnavailable as exc:
        if exc.reason == "timeout":
            return v._json(
                {"error": {"code": "builder_timeout", "message": "Agent Builder 调用超时，请稍后重试或改用手工创建",
                           "reason": "timeout"}},
                status.HTTP_504_GATEWAY_TIMEOUT,
            )
        return v._json(
            {"error": {"code": "builder_unavailable", "message": str(exc) or "Agent Builder 暂不可用",
                       "reason": exc.reason}},
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except ExpertNotFound:
        return v._json({"error": {"code": "not_found", "message": "agent 不存在或已停用"}},
                       status.HTTP_404_NOT_FOUND)
    except ConfigError:
        return v._read_failure_response()
    except IbError as exc:
        return v.error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return v.error_response(exc)


# --------------------------------------------------------------------------- #


def _draft(deps: Any, service: Any, ctx: Any, pid: str, body: dict[str, Any]) -> Any:
    requirement = body.get("requirement")
    if not isinstance(requirement, str):
        raise ValidationError("requirement 必须是字符串", field="requirement")
    draft, notes, rating = service.generate(pid, str(ctx.authz.actor_id), requirement)
    return _views()._json(
        {"draft": _draft_dto(draft), "notes": [_note_dto(n) for n in notes], "evaluation": _rubric_dto(rating)},
        status.HTTP_200_OK,
    )


def builder_draft_endpoint(request: Any) -> Any:
    return _run(request, _draft)


def _evaluate(deps: Any, service: Any, ctx: Any, pid: str, body: dict[str, Any]) -> Any:
    rating = service.evaluate(pid, str(ctx.authz.actor_id), _draft_of(body.get("draft")))
    return _views()._json({"evaluation": _rubric_dto(rating)}, status.HTTP_200_OK)


def builder_evaluate_endpoint(request: Any) -> Any:
    return _run(request, _evaluate)


def _instruction(body: dict[str, Any]) -> str | None:
    v = body.get("instruction")
    if v is None:
        return None
    if not isinstance(v, str) or len(v) > 1000:
        raise ValidationError("instruction 必须是不超过 1000 字符的字符串", field="instruction")
    return v


def _optimize(deps: Any, service: Any, ctx: Any, pid: str, body: dict[str, Any]) -> Any:
    draft, notes, before, after, changes = service.optimize(
        pid, str(ctx.authz.actor_id), _draft_of(body.get("draft")), _instruction(body)
    )
    return _views()._json(
        {
            "draft": _draft_dto(draft), "notes": [_note_dto(n) for n in notes],
            "before": _rubric_dto(before), "after": _rubric_dto(after), "changes": [_change_dto(c) for c in changes],
        },
        status.HTTP_200_OK,
    )


def builder_optimize_endpoint(request: Any) -> Any:
    return _run(request, _optimize)


def _review_existing(deps: Any, service: Any, ctx: Any, pid: str, body: dict[str, Any]) -> Any:
    expert = _s(body, "expert", low=1, high=48)
    mode = body.get("mode")
    if mode not in ("evaluate", "optimize"):
        raise ValidationError("mode 必须是 evaluate 或 optimize", field="mode")
    published = deps.publish_service.current(pid)  # 已发布（文件态）配置；服务端不写任何配置
    rating, proposal, changes = service.review_existing(
        pid, str(ctx.authz.actor_id), expert, mode, _instruction(body), published=published
    )
    return _views()._json(
        {
            "evaluation": _rubric_dto(rating),
            "proposal": _draft_dto(proposal) if proposal is not None else None,
            "changes": [_change_dto(c) for c in changes],
        },
        status.HTTP_200_OK,
    )


def builder_review_existing_endpoint(request: Any) -> Any:
    return _run(request, _review_existing)
