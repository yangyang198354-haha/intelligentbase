# MOD-R29-02 / implements IFC-R29-010..013, 016 / depends MOD-R29-01
"""命名、指纹与发现期合规规则：所有"可由输入确定"的规则集中为纯函数（发现期 / 保存期 / 调用期共用，防漂移）。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import AbstractSet, Any, Mapping

from ib.core.types import (
    EXTERNAL_TOOL_PREFIX,
    McpAdmission,
    McpDenyReason,
    McpDiscoveredTool,
    McpExcludedTool,
    McpGovernance,
    McpRisk,
    McpToolSnapshot,
)

from .schema_lite import SchemaUnsupportedError, inline_local_refs, x_mcp_header_violation

__all__ = [
    "RESERVED_PARAM_NAMES",
    "validate_server_id",
    "local_tool_name",
    "display_tool_name",
    "is_external_name",
    "canonical_json",
    "tool_fingerprint",
    "check_discovered_tool",
    "suspect_tenant_params",
    "inference_risk",
    "admission_reason",
]

_SERVER_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,23}$")
_REMOTE_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,128}$")
_SEGMENT_BAD = re.compile(r"[^A-Za-z0-9_\-]")
_TENANT_RE = re.compile(r"tenant|project|user|account|org|customer", re.IGNORECASE)
_LOCAL_NAME_MAX = 64  # [ASSUMPTION A-R29-2]：LLM 函数名上限按 OpenAI 兼容通例；目标机契约探针待验证（[UNSOURCED] 见出处表）

#: 平台保留的两个限制参数名；远端 schema 含同名属性的工具在发现期被排除（param_name_reserved）
RESERVED_PARAM_NAMES: tuple[str, ...] = ("mcp_timeout_s", "mcp_max_calls_per_turn")


def validate_server_id(raw: str) -> str:
    if not isinstance(raw, str) or not _SERVER_ID_RE.match(raw):
        raise ValueError("server_id_invalid")
    return raw


def local_tool_name(server_id: str, remote_name: str) -> str:
    """mcp__<server>__<segment>，≤64；超长截断 + `_` + 8 位 sha256。"""
    segment = _SEGMENT_BAD.sub("_", remote_name)
    prefix = f"{EXTERNAL_TOOL_PREFIX}{server_id}__"
    name = prefix + segment
    if len(name) <= _LOCAL_NAME_MAX:
        return name
    digest = hashlib.sha256(remote_name.encode("utf-8")).hexdigest()[:8]
    room = max(1, _LOCAL_NAME_MAX - len(prefix) - 9)
    return f"{prefix}{segment[:room]}_{digest}"


def display_tool_name(server_id: str, remote_name: str) -> str:
    return f"mcp.{server_id}.{remote_name}"


def is_external_name(name: str) -> bool:
    return isinstance(name, str) and name.startswith(EXTERNAL_TOOL_PREFIX)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def tool_fingerprint(raw: Mapping[str, Any]) -> str:
    """IFC-R29-011：name/title/description/inputSchema/outputSchema/annotations 的规范化 JSON sha256。"""
    payload = {
        "name": raw.get("name"),
        "title": raw.get("title"),
        "description": raw.get("description"),
        "inputSchema": raw.get("inputSchema"),
        "outputSchema": raw.get("outputSchema"),
        "annotations": raw.get("annotations"),
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _depth_exceeds(node: Any, limit: int, depth: int = 0) -> bool:
    if depth > limit:
        return True
    if isinstance(node, Mapping):
        return any(_depth_exceeds(v, limit, depth + 1) for v in node.values())
    if isinstance(node, list):
        return any(_depth_exceeds(v, limit, depth + 1) for v in node)
    return False


def check_discovered_tool(
    raw: Mapping[str, Any],
    *,
    server_id: str,
    gov: McpGovernance,
    taken_local_names: AbstractSet[str],
) -> McpDiscoveredTool | McpExcludedTool:
    """IFC-R29-012：发现期合规。违规 ⇒ McpExcludedTool(reason)，永不抛未预期异常。"""
    name = raw.get("name") if isinstance(raw, Mapping) else None
    shown = name if isinstance(name, str) else ""
    shown = shown[:128]
    try:
        if not isinstance(name, str) or not _REMOTE_NAME_RE.match(name):
            return McpExcludedTool(shown, "name_invalid")
        desc = raw.get("description")
        if desc is None:
            desc = ""
        title = raw.get("title")
        if not isinstance(desc, str) or (title is not None and not isinstance(title, str)):
            return McpExcludedTool(name, "schema_invalid")
        if len(desc) > gov.max_description_chars:
            return McpExcludedTool(name, "over_limit")
        schema = raw.get("inputSchema")
        if not isinstance(schema, Mapping) or schema.get("type") != "object":
            return McpExcludedTool(name, "schema_invalid")
        try:
            size = len(canonical_json(schema).encode("utf-8"))
        except (TypeError, ValueError):
            return McpExcludedTool(name, "schema_invalid")
        if size > gov.max_schema_bytes or _depth_exceeds(schema, gov.max_schema_depth):
            return McpExcludedTool(name, "over_limit")
        try:
            inline_local_refs(schema, max_depth=gov.max_schema_depth, max_bytes=gov.max_schema_bytes)
        except SchemaUnsupportedError:
            return McpExcludedTool(name, "schema_unsupported")
        out_schema = raw.get("outputSchema")
        if out_schema is not None and not isinstance(out_schema, Mapping):
            return McpExcludedTool(name, "schema_invalid")
        annotations = raw.get("annotations")
        if annotations is None:
            annotations = {}
        if not isinstance(annotations, Mapping):
            return McpExcludedTool(name, "schema_invalid")
        props = schema.get("properties")
        if isinstance(props, Mapping) and any(p in props for p in RESERVED_PARAM_NAMES):
            return McpExcludedTool(name, "param_name_reserved")
        if x_mcp_header_violation(schema) is not None:
            return McpExcludedTool(name, "x_mcp_header_invalid")
        local = local_tool_name(server_id, name)
        if local.lower() in {t.lower() for t in taken_local_names}:
            return McpExcludedTool(name, "name_collision")
        snap = McpToolSnapshot(
            title=title,
            description=desc,
            input_schema=json.loads(canonical_json(schema)),
            output_schema=json.loads(canonical_json(out_schema)) if out_schema is not None else None,
            annotations=json.loads(canonical_json(annotations)),
            fingerprint=tool_fingerprint(raw),
        )
        return McpDiscoveredTool(name, snap)
    except RecursionError:
        return McpExcludedTool(shown, "over_limit")
    except Exception:  # noqa: BLE001 - 纯函数契约：不抛未预期异常
        return McpExcludedTool(shown, "schema_invalid")


def suspect_tenant_params(
    schema: Mapping[str, Any], *, hidden: AbstractSet[str], fixed: AbstractSet[str]
) -> tuple[str, ...]:
    """IFC-R29-013：必填且名称疑似租户 / 项目 / 用户标识、且未被固定 / 屏蔽的参数。"""
    req = schema.get("required") if isinstance(schema, Mapping) else None
    if not isinstance(req, list):
        return ()
    return tuple(r for r in req if isinstance(r, str) and _TENANT_RE.search(r) and r not in hidden and r not in fixed)


def inference_risk(annotations: Mapping[str, Any]) -> McpRisk:
    """仅显式 `destructiveHint is True` → side_effect，其余一律 unknown，永不推定 read_only（注解不可信）。
    [WEB: https://modelcontextprotocol.io/specification/2026-07-28/schema，2026-11-05]"""
    if isinstance(annotations, Mapping) and annotations.get("destructiveHint") is True:
        return "side_effect"
    return "unknown"


def admission_reason(adm: McpAdmission | None, *, bound_fingerprint: str, enabled: bool) -> McpDenyReason | None:
    """IFC-R29-016：准入纯判定；None = 放行。保存期（grants）与调用期（runtime）共用同一实现。"""
    if not enabled:
        return "feature_disabled"
    if adm is None:
        return "tool_missing"
    server, tool = adm.server, adm.tool
    if server.admin_state == "disabled":
        return "server_disabled"
    if server.admin_state != "enabled":
        return "server_unverified"
    if not adm.project_open:
        return "server_not_open"
    state = tool.state
    if state == "needs_rereview":
        return "tool_needs_rereview"
    if state == "offline":
        return "tool_offline"
    if state != "enabled":
        return "tool_not_enabled"
    if tool.approved is None or tool.approved.fingerprint != bound_fingerprint:
        return "tool_stale"
    if tool.risk != "read_only" and not adm.waiver_active:
        return "risk_not_waived"
    if server.auth_kind != "none" and not adm.credential_present:
        return "credential_missing"
    return None
