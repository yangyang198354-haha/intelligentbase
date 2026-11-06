# MOD-R29-16 / implements IFC-R29-160..164 / depends MOD-R29-01, 02
"""保存期外部授权校验与项目视图。

保存期与调用期共用同一判定函数 `ib.mcp.rules.admission_reason`（防漂移）。仅对"相对已发布版本新增"的 mcp__ 授权
做严格校验（ADR-R29-12 方案 B）；存量失效授权容忍并经 `grant_statuses` 标注。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Sequence

from ib.core.ports import McpStores
from ib.core.types import (
    EXTERNAL_TOOL_PREFIX,
    McpDenyReason,
    McpGovernance,
    McpServer,
    McpToolRecord,
    ToolGrantSpec,
    ValidationErrorItem,
)

from .result import sanitize_external
from .rules import admission_reason

__all__ = [
    "GrantStatus",
    "validate_external_grants",
    "grant_statuses",
    "visible_servers",
    "visible_tools",
    "catalog_external_tools",
    "EXTERNAL_PARAM_NAMES",
]

_log = logging.getLogger("ib.mcp")
EXTERNAL_PARAM_NAMES = ("mcp_timeout_s", "mcp_max_calls_per_turn")
_CODE_OF: dict[str, str] = {
    "tool_missing": "mcp_tool_unknown",
    "tool_not_enabled": "mcp_tool_not_enabled",
    "tool_needs_rereview": "mcp_tool_needs_rereview",
    "tool_offline": "mcp_tool_offline",
    "server_disabled": "mcp_server_unavailable",
    "server_unverified": "mcp_server_unavailable",
    "server_missing": "mcp_server_unavailable",
    "credential_missing": "mcp_server_unavailable",
    "server_not_open": "mcp_server_not_open",
    "risk_not_waived": "mcp_risk_not_waived",
    "tool_stale": "mcp_tool_not_enabled",
}
_MSG_OF: dict[str, str] = {
    "mcp_tool_unknown": "外部工具不存在",
    "mcp_tool_not_enabled": "外部工具未启用",
    "mcp_tool_needs_rereview": "外部工具待复审，暂不可新增授权",
    "mcp_tool_offline": "外部工具已下线",
    "mcp_server_unavailable": "外部工具所属服务不可用（未启用 / 未验证 / 凭证未配置）",
    "mcp_server_not_open": "外部工具所属服务未对本项目开放",
    "mcp_risk_not_waived": "该外部工具有副作用或风险未知，需管理员对本项目放行",
}


def _ext_pairs(grants: Sequence[ToolGrantSpec]) -> set[tuple[str, str]]:
    return {(g.expert_name, t) for g in grants for t in g.tool_names if t.startswith(EXTERNAL_TOOL_PREFIX)}


def _bound_fp(adm: Any) -> str:
    return adm.tool.approved.fingerprint if adm is not None and adm.tool.approved is not None else ""


def _reason(stores: McpStores, project_id: str, local_name: str) -> McpDenyReason | None:
    adm = stores.tools.read_admission(project_id, local_name)
    return admission_reason(adm, bound_fingerprint=_bound_fp(adm), enabled=True)


def _eff(gov_v: int, srv_v: int | None) -> int:
    return gov_v if srv_v is None else min(gov_v, srv_v)


def validate_external_grants(
    project_id: str,
    new_grants: Sequence[ToolGrantSpec],
    prior_grants: Sequence[ToolGrantSpec],
    *,
    stores: McpStores,
    gov: McpGovernance,
) -> tuple[ValidationErrorItem, ...]:
    """IFC-R29-160。读取失败 ⇒ 单条 mcp_store_unavailable（保存 fail-closed，仅当存在新增外部授权 / 参数变更）。"""
    new_pairs = _ext_pairs(new_grants)
    prior_pairs = _ext_pairs(prior_grants)
    added = new_pairs - prior_pairs
    prior_params = {(g.expert_name, pv.name): pv.value for g in prior_grants for pv in g.param_values}
    errors: list[ValidationErrorItem] = []
    try:
        for expert, tool in sorted(added):
            code = None
            r = _reason(stores, project_id, tool)
            if r is not None:
                code = _CODE_OF.get(r, "mcp_tool_not_enabled")
            if code:
                errors.append(
                    ValidationErrorItem(
                        path=f"tool_grants[{expert}].tool_names[{tool}]", code=code, message=_MSG_OF.get(code, "外部工具不可授权")
                    )
                )
        for g in new_grants:
            for pv in g.param_values:
                owner = pv.name.split(".", 1)[0] if "." in pv.name else ""
                if not owner.startswith(EXTERNAL_TOOL_PREFIX):
                    continue
                if (g.expert_name, owner) not in new_pairs:
                    continue  # 归属工具未授权：由既有 build_authorized_tools 路径判定
                changed = (g.expert_name, owner) in added or prior_params.get((g.expert_name, pv.name)) != pv.value
                if not changed:
                    continue
                path = f"tool_grants[{g.expert_name}].param_values[{pv.name}]"
                bare = pv.name.split(".", 1)[1]
                if bare not in EXTERNAL_PARAM_NAMES:
                    errors.append(ValidationErrorItem(path=path, code="mcp_param_forbidden",
                                                      message="外部工具仅允许配置超时与每轮调用次数两个限制参数"))
                    continue
                rec = stores.tools.get_by_local_name(owner)
                srv = stores.servers.get(rec.server_id) if rec is not None else None
                if rec is None or srv is None:
                    continue  # 工具缺失已在上方（新增）或容忍（存量）
                upper = (
                    _eff(gov.call_timeout_s, srv.limits.call_timeout_s)
                    if bare == "mcp_timeout_s"
                    else _eff(gov.max_calls_per_turn, srv.limits.max_calls_per_turn)
                )
                try:
                    val = int(float(pv.value))
                except (TypeError, ValueError):
                    errors.append(ValidationErrorItem(path=path, code="mcp_limit_exceeds_upper", message="取值须为整数"))
                    continue
                if val < 1 or val > upper:
                    errors.append(
                        ValidationErrorItem(path=path, code="mcp_limit_exceeds_upper", message=f"取值须在 1..{upper}（不得高于上层上限）")
                    )
    except Exception:  # noqa: BLE001 - 台账不可读 ⇒ fail-closed
        _log.warning("mcp grant validation store unavailable")
        return (
            ValidationErrorItem(path="tool_grants", code="mcp_store_unavailable", message="外部工具台账暂不可用，无法保存外部工具授权"),
        )
    return tuple(errors)


@dataclass(frozen=True, slots=True)
class GrantStatus:
    local_name: str
    expert_name: str
    valid: bool
    reason: McpDenyReason | None


def grant_statuses(project_id: str, grants: Sequence[ToolGrantSpec], *, stores: McpStores) -> tuple[GrantStatus, ...]:
    """IFC-R29-161：配置页失效标注（与调用期同一判定函数）。"""
    out: list[GrantStatus] = []
    for expert, tool in sorted(_ext_pairs(grants)):
        try:
            r: McpDenyReason | None = _reason(stores, project_id, tool)
        except Exception:  # noqa: BLE001
            r = "admission_unreadable"
        out.append(GrantStatus(tool, expert, r is None, r))
    return tuple(out)


def _is_visible(s: McpServer, project_id: str, open_ids: set[str]) -> bool:
    return bool(s.open_all or project_id in open_ids or s.owner_project == project_id)


def visible_servers(project_id: str | None, *, stores: McpStores) -> tuple[McpServer, ...]:
    """IFC-R29-162：None = 全局主体（全部）；否则 open_all ∨ 开放行 ∨ owner_project。"""
    servers = stores.servers.list_all()
    if project_id is None:
        return servers
    return tuple(s for s in servers if _is_visible(s, project_id, set(stores.servers.open_projects(s.server_id))))


def visible_tools(
    project_id: str | None, *, stores: McpStores, server_id: str | None = None
) -> tuple[McpToolRecord, ...]:
    """IFC-R29-163。项目侧不含 excluded。"""
    allowed = {s.server_id for s in visible_servers(project_id, stores=stores)}
    if server_id is not None:
        if server_id not in allowed:
            return ()
        allowed = {server_id}
    tools = []
    for sid in sorted(allowed):
        for t in stores.tools.list(server_id=sid):
            if project_id is not None and t.state == "excluded":
                continue
            tools.append(t)
    return tuple(tools)


def catalog_external_tools(project_id: str, *, stores: McpStores, gov: McpGovernance) -> list[dict[str, Any]]:
    """IFC-R29-164：config catalog 的 external_tools 载荷（仅已启用 Server 下 enabled + 已审核的工具；含 param specs）。"""
    out: list[dict[str, Any]] = []
    for srv in visible_servers(project_id, stores=stores):
        if srv.admin_state != "enabled":
            continue
        for t in stores.tools.list(server_id=srv.server_id):
            if t.state != "enabled" or t.approved is None:
                continue
            adm = stores.tools.read_admission(project_id, t.local_name)
            waived = bool(adm is not None and adm.waiver_active)
            grantable = t.risk == "read_only" or waived
            eff_t = _eff(gov.call_timeout_s, srv.limits.call_timeout_s)
            eff_c = _eff(gov.max_calls_per_turn, srv.limits.max_calls_per_turn)
            out.append(
                {
                    "local_name": t.local_name,
                    "display_name": t.display_name,
                    "server_id": srv.server_id,
                    "risk": t.risk,
                    "grantable": grantable,
                    "invalid_reason": None if grantable else "risk_not_waived",
                    "description": sanitize_external(t.llm_description or t.approved.description, max_chars=300),
                    "param_specs": [
                        {"name": f"{t.local_name}.mcp_timeout_s", "type": "int", "default": str(eff_t),
                         "minimum": 1, "maximum": eff_t, "choices": None},
                        {"name": f"{t.local_name}.mcp_max_calls_per_turn", "type": "int", "default": str(eff_c),
                         "minimum": 1, "maximum": eff_c, "choices": None},
                    ],
                }
            )
    return out
