# MOD-R29-14 / implements IFC-R29-130..133 / depends MOD-R29-01, 02, 06, 10
"""目录服务：校验 + 发现 + 差异应用、审核、启停、状态机（ADR-R29-08）。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from ib.core.errors import NotFoundError, ValidationError
from ib.core.ports import McpStores, SecretCipher
from ib.core.types import (
    MCP_RISKS,
    McpDiscoveryDiff,
    McpGovernance,
    McpNegotiated,
    McpServer,
    McpToolRecord,
    McpToolSnapshot,
)

from .auditing import audit_record, safe_record
from .client import McpClient, McpClientError, McpTarget
from .crypto import Secret, SecretKeyError
from .rules import suspect_tenant_params

__all__ = ["McpCatalogService", "VerifyOutcome", "ToolDiff", "VerificationFailed", "discovery_credential"]


class VerificationFailed(Exception):
    """连接验证 / 刷新失败（HTTP 层映射 409 verification_failed）。category 为失败类别。"""

    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


@dataclass(frozen=True, slots=True)
class VerifyOutcome:
    ok: bool
    category: str
    negotiated: McpNegotiated | None


@dataclass(frozen=True, slots=True)
class ToolDiff:
    tool_id: int
    changed_fields: tuple[str, ...]
    approved: McpToolSnapshot | None
    observed: McpToolSnapshot | None


def _eff(gov_v: int, srv_v: int | None) -> int:
    return gov_v if srv_v is None else min(gov_v, srv_v)


def discovery_credential(stores: McpStores, cipher: SecretCipher, server: McpServer) -> tuple[Secret | None, str | None]:
    """校验 / 刷新 / 探测的凭证选择：shared 用 `@shared`（缺失 ⇒ credential_missing）；
    project 仅用 `@discovery`（缺失 ⇒ 以无凭证尝试，失败按 auth_failed）。返回 (secret, 失败类别)。"""
    if server.auth_kind == "none":
        return None, None
    key = "@shared" if server.credential_scope == "shared" else "@discovery"
    got = stores.credentials.get_ciphertext(server.server_id, key)
    if got is None:
        return (None, "credential_missing") if server.credential_scope == "shared" else (None, None)
    try:
        return cipher.decrypt(got[0]), None
    except SecretKeyError as exc:
        return None, "secret_key_missing" if exc.reason != "token_invalid" else "credential_missing"


class McpCatalogService:
    def __init__(
        self,
        *,
        stores: McpStores,
        cipher: SecretCipher,
        client: McpClient,
        audit: Any,
        clock: Callable[[], str],
        gov_reader: Callable[[], McpGovernance],
        on_tools_changed: Callable[[str], None],
    ) -> None:
        self._s = stores
        self._cipher = cipher
        self._client = client
        self._audit = audit
        self._clock = clock
        self._gov = gov_reader
        self._on_changed = on_tools_changed

    # -- 工具 -------------------------------------------------------------- #
    def _server(self, server_id: str) -> McpServer:
        s = self._s.servers.get(server_id)
        if s is None:
            raise NotFoundError("server_not_found")
        return s

    @staticmethod
    def _target(s: McpServer) -> McpTarget:
        return McpTarget(
            s.server_id, s.endpoint_url, s.auth_kind, s.auth_header_name, s.protocol_era, s.protocol_version,
            bool(s.supports_list_changed),
        )

    def _deadline(self, s: McpServer, gov: McpGovernance) -> float:
        return time.monotonic() + max(1, _eff(gov.discover_timeout_s, s.limits.discover_timeout_s))

    def _notify(self, server_id: str) -> None:
        try:
            self._on_changed(server_id)
        except Exception:  # noqa: BLE001 - 刷新通知失败不回滚已提交的状态迁移
            pass

    # -- 验证 / 刷新 -------------------------------------------------------- #
    def verify(self, server_id: str, *, actor: str) -> VerifyOutcome:
        """IFC-R29-130：probe → record_probe；失败原因类别见 McpFailureKind（另有 credential_missing / no_tools_capability）。"""
        s = self._server(server_id)
        gov = self._gov()
        cred, miss = discovery_credential(self._s, self._cipher, s)
        now = self._clock()
        if miss is not None:
            self._s.servers.record_probe(server_id, health="down", checked_at=now, verify_result=miss)
            safe_record(self._audit, audit_record(self._clock, action="server.verify", actor=actor, server_id=server_id, outcome="failed", reason=miss))
            return VerifyOutcome(False, miss, None)
        # 验证总是重新探测时代（身份变更 / 重新启用后协商结果可能变化）
        target = McpTarget(s.server_id, s.endpoint_url, s.auth_kind, s.auth_header_name, None, None)
        res = self._client.probe(target, cred, deadline=self._deadline(s, gov))
        if res.ok and res.negotiated is not None:
            self._s.servers.record_probe(server_id, health="up", checked_at=now, verify_result="ok", negotiated=res.negotiated)
            safe_record(self._audit, audit_record(self._clock, action="server.verify", actor=actor, server_id=server_id, reason="ok"))
            return VerifyOutcome(True, "ok", res.negotiated)
        cat = res.failure or "protocol_error"
        self._s.servers.record_probe(
            server_id, health="down", checked_at=now, verify_result=cat, negotiated=res.negotiated
        )
        safe_record(self._audit, audit_record(self._clock, action="server.verify", actor=actor, server_id=server_id, outcome="failed", reason=cat))
        return VerifyOutcome(False, cat, res.negotiated)

    def refresh(self, server_id: str, *, actor: str) -> McpDiscoveryDiff:
        """IFC-R29-131：list_tools → apply_discovery（CAS）→ 审计差异；失败 ⇒ VerificationFailed。"""
        s = self._server(server_id)
        gov = self._gov()
        cred, miss = discovery_credential(self._s, self._cipher, s)
        if miss is not None:
            raise VerificationFailed(miss)
        taken = {t.local_name for t in self._s.tools.list() if t.server_id != server_id}
        try:
            d = self._client.list_tools(
                self._target(s), cred, gov=gov, deadline=self._deadline(s, gov), taken_local_names=taken
            )
        except McpClientError as exc:
            self._s.servers.record_probe(server_id, health="down", checked_at=self._clock())
            safe_record(self._audit, audit_record(self._clock, action="server.refresh", actor=actor, server_id=server_id, outcome="failed", reason=str(exc.kind)))
            raise VerificationFailed(str(exc.kind)) from None
        now = self._clock()
        diff = self._s.tools.apply_discovery(server_id, d, now=now)
        self._s.servers.record_probe(server_id, health="up", checked_at=now, negotiated=d.negotiated)
        summary = (
            f"added={len(diff.added)};changed={len(diff.changed)};offline={len(diff.offline)};"
            f"reappeared={len(diff.reappeared)};excluded={len(diff.excluded)};unchanged={diff.unchanged}"
        )
        safe_record(self._audit, audit_record(self._clock, action="server.refresh", actor=actor, server_id=server_id, reason=summary))
        if diff.changed or diff.offline or diff.reappeared:
            self._notify(server_id)
        return diff

    # -- 审核 / 状态 -------------------------------------------------------- #
    def _tool(self, tool_id: int) -> McpToolRecord:
        t = self._s.tools.get(tool_id)
        if t is None:
            raise NotFoundError("tool_not_found")
        return t

    def approve(
        self,
        tool_id: int,
        *,
        expected_fingerprint: str,
        risk: str,
        hidden_params: Sequence[str],
        llm_description: str | None,
        ack_tenant_params: bool,
        actor: str,
    ) -> McpToolRecord:
        """IFC-R29-132：指纹不符 ⇒ ConflictError(fingerprint_changed)；租户参数嫌疑未确认 ⇒ ValidationError。
        approve 对 side_effect / unknown 不自动放行（放行是独立动作）。"""
        t = self._tool(tool_id)
        if risk not in MCP_RISKS:
            raise ValidationError("risk_invalid", field="risk")
        if t.observed is None:
            raise ValidationError("tool_has_no_observed_snapshot", field="tool_id")
        props = t.observed.input_schema.get("properties") if isinstance(t.observed.input_schema, dict) else None
        names = set(props) if isinstance(props, dict) else set()
        hidden = tuple(dict.fromkeys(str(h) for h in hidden_params))
        if any(h not in names for h in hidden):
            raise ValidationError("hidden_param_unknown", field="hidden_params")
        if llm_description is not None and len(llm_description) > 1000:
            raise ValidationError("llm_description_too_long", field="llm_description")
        suspects = suspect_tenant_params(t.observed.input_schema, hidden=set(hidden), fixed=set())
        if suspects and not ack_tenant_params:
            raise ValidationError("tenant_params_unacked", field="ack_tenant_params")
        rec = self._s.tools.approve(
            tool_id,
            expected_fingerprint=expected_fingerprint,
            risk=risk,  # type: ignore[arg-type]
            hidden_params=hidden,
            llm_description=llm_description or None,
            actor=actor,
            now=self._clock(),
        )
        safe_record(
            self._audit,
            audit_record(
                self._clock, action="tool.approve", actor=actor, server_id=t.server_id, tool_name=t.local_name,
                display_name=t.display_name, fingerprint=expected_fingerprint,
                reason=f"risk={risk};hidden={len(hidden)};tenant_ack={int(bool(suspects) and ack_tenant_params)}",
            ),
        )
        self._notify(t.server_id)
        return rec

    def reject(self, tool_id: int, *, actor: str) -> McpToolRecord:
        t = self._tool(tool_id)
        rec = self._s.tools.reject(tool_id, actor=actor, now=self._clock())
        safe_record(self._audit, audit_record(self._clock, action="tool.reject", actor=actor, server_id=t.server_id, tool_name=t.local_name, display_name=t.display_name))
        self._notify(t.server_id)
        return rec

    def set_tool_enabled(self, tool_id: int, enabled: bool, *, actor: str) -> McpToolRecord:
        t = self._tool(tool_id)
        rec = self._s.tools.set_enabled(tool_id, bool(enabled), actor=actor, now=self._clock())
        safe_record(
            self._audit,
            audit_record(
                self._clock, action="tool.enable" if enabled else "tool.disable", actor=actor, server_id=t.server_id,
                tool_name=t.local_name, display_name=t.display_name,
            ),
        )
        self._notify(t.server_id)
        return rec

    def tool_diff(self, tool_id: int) -> ToolDiff:
        """IFC-R29-133：approved vs observed 字段级差异。"""
        t = self._tool(tool_id)
        a, o = t.approved, t.observed
        if a is None or o is None:
            return ToolDiff(tool_id, (), a, o)
        fields = []
        for name in ("title", "description", "input_schema", "output_schema", "annotations"):
            if getattr(a, name) != getattr(o, name):
                fields.append(name)
        return ToolDiff(tool_id, tuple(fields), a, o)
