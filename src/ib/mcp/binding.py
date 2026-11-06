# MOD-R29-13 / implements IFC-R29-120..122 / depends MOD-R29-01, 02, 05, 12
"""外部工具注册器：把"已审核快照"注册成 `ToolSpec` + 闭包（编译期）；能否调用由 `McpInvoker` 每次实时判定。

闭包签名**不含** `scope` / `retrieval` / `knowledge` 参数名，使 `bind_scope` / `build_agent_tools` 不向其注入
（selfcheck `mcp_callable_signature_guard`）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ib.core.ports import McpStores
from ib.core.types import McpGovernance, McpServer, McpToolRecord, ToolParamSpec, ToolResult, ToolSpec
from ib.tools import ToolNameConflictError, ToolRegistry, derive_tool_param_specs

from .result import sanitize_external
from .runtime import ExternalToolBinding, McpInvoker
from .schema_lite import SchemaUnsupportedError, project_llm_schema

__all__ = [
    "ExternalRegistration",
    "ExternalRegistrationError",
    "make_registrar",
    "external_tool_spec",
    "external_param_specs_for",
]

_log = logging.getLogger("ib.mcp")
_DESC_MAX = 1000


class ExternalRegistrationError(Exception):
    """台账不可读等：compile 据此失败（ADR-R29-09，fail-closed 且可见）。"""


@dataclass(frozen=True, slots=True)
class ExternalRegistration:
    registered: tuple[str, ...]
    dropped_dangling: tuple[str, ...]  # 无审核快照 / 不存在的授权名（容忍并告警）


def _eff(*vals: int | None) -> int:
    return min(v for v in vals if v is not None)


def external_tool_spec(
    tool: McpToolRecord, gov: McpGovernance, server: McpServer, fixed_keys: frozenset[str] | set[str] = frozenset()
) -> ToolSpec:
    """IFC-R29-121。tool.approved 必须非空。"""
    assert tool.approved is not None
    raw_desc = tool.llm_description or tool.approved.description or ""
    desc = sanitize_external(raw_desc, max_chars=_DESC_MAX) or f"外部工具 {tool.display_name}"
    params = project_llm_schema(
        tool.approved.input_schema, hidden=set(tool.hidden_params), fixed=set(fixed_keys), desc_max=300
    )
    eff_t = max(1, _eff(gov.call_timeout_s, server.limits.call_timeout_s))
    eff_c = max(1, _eff(gov.max_calls_per_turn, server.limits.max_calls_per_turn))
    return ToolSpec(
        name=tool.local_name,
        description=desc,
        needs_scope=False,
        parameters=params,
        config_parameters={
            "mcp_timeout_s": {"type": "integer", "default": eff_t, "minimum": 1, "maximum": eff_t},
            "mcp_max_calls_per_turn": {"type": "integer", "default": eff_c, "minimum": 1, "maximum": eff_c},
        },
        timeout_param="mcp_timeout_s",
        route_visible=False,
        external=True,
    )


def make_registrar(
    *, stores: McpStores, invoker: McpInvoker, gov_reader: Callable[[], McpGovernance]
) -> Callable[[str, ToolRegistry, frozenset[str]], ExternalRegistration]:
    """IFC-R29-120：即 `RuntimeDeps.external_tool_registrar`。"""

    def registrar(project_id: str, registry: ToolRegistry, names: frozenset[str]) -> ExternalRegistration:
        try:
            gov = gov_reader()
        except Exception as exc:  # noqa: BLE001
            raise ExternalRegistrationError("governance_unreadable") from exc
        registered: list[str] = []
        dropped: list[str] = []
        for name in sorted(names):
            try:
                rec = stores.tools.get_by_local_name(name)
                server = stores.servers.get(rec.server_id) if rec is not None else None
                fixed = set(stores.tools.get_binding(rec.tool_id, project_id)) if rec is not None else set()
            except Exception as exc:  # noqa: BLE001
                raise ExternalRegistrationError("store_unreadable") from exc
            if rec is None or rec.approved is None or server is None:
                dropped.append(name)
                continue
            try:
                spec = external_tool_spec(rec, gov, server, fixed)
            except SchemaUnsupportedError:
                dropped.append(name)
                continue
            binding = ExternalToolBinding(
                project_id=project_id, local_name=rec.local_name, display_name=rec.display_name,
                server_id=rec.server_id, remote_name=rec.remote_name, bound_fingerprint=rec.approved.fingerprint,
                input_schema=rec.approved.input_schema, trial=False,
            )
            cfg = spec.config_parameters or {}
            d_timeout = int(cfg["mcp_timeout_s"]["default"])
            d_calls = int(cfg["mcp_max_calls_per_turn"]["default"])

            def _fn(*, mcp_timeout_s: int = d_timeout, mcp_max_calls_per_turn: int = d_calls, _b=binding, **llm_args: Any) -> ToolResult:
                return invoker.invoke(_b, llm_args, mcp_timeout_s=mcp_timeout_s, mcp_max_calls_per_turn=mcp_max_calls_per_turn)

            try:
                registry.register_external(spec, _fn)
            except ToolNameConflictError:
                pass  # 同一注册表重复登记同名外部工具：保持首次登记，不覆盖
            registered.append(name)
        if dropped:
            _log.warning("mcp dangling grants dropped count=%d project=%s", len(dropped), project_id)
        return ExternalRegistration(tuple(registered), tuple(dropped))

    return registrar


def external_param_specs_for(registry: ToolRegistry) -> tuple[ToolParamSpec, ...]:
    """IFC-R29-122：= derive_tool_param_specs(registry)（含外部 mcp_* 规格）。"""
    return derive_tool_param_specs(registry)
