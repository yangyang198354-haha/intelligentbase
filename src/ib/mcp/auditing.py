# MOD-R29-14 辅助：管理 / 系统审计记录构造（类型层无凭证 / 入参字段）
from __future__ import annotations

import logging
import uuid
from typing import Any

from ib.core.types import McpAuditRecord

__all__ = ["audit_record", "safe_record"]

_log = logging.getLogger("ib.mcp")


def audit_record(
    clock: Any,
    *,
    action: str,
    actor: str,
    server_id: str = "",
    tool_name: str = "",
    display_name: str = "",
    project_id: str = "",
    outcome: str = "ok",
    reason: str = "",
    fingerprint: str = "",
) -> McpAuditRecord:
    kind = "system" if str(actor).startswith("system") else "admin"
    return McpAuditRecord(
        call_id=uuid.uuid4().hex, ts=clock(), kind=kind, action=action, actor=str(actor)[:80], project_id=project_id,
        server_id=server_id, tool_name=tool_name, display_name=display_name, outcome=outcome, reason=str(reason)[:200],
        duration_ms=None, args_digest="", args_summary="", fingerprint=fingerprint, confirm=False, trial=False,
    )


def safe_record(audit: Any, rec: McpAuditRecord) -> None:
    """管理审计写入失败不阻断管理动作主流程（调用审计的"先行"硬前置在 McpInvoker），只告警。"""
    try:
        audit.record(rec)
    except Exception:  # noqa: BLE001
        _log.warning("mcp admin audit write failed action=%s", rec.action)
