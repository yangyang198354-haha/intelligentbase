# MOD-R29-15 / implements IFC-R29-140..144 / depends MOD-R29-01, 06, 14, ib.confsvc (单向)
"""管理服务：Server CRUD、凭证、开放范围、固定入参、放行、治理参数、内网允许名单、GrantIndex / GrantCleaner。

所有失败以 `McpRequestError(code, http, details)` 表达（视图层映射状态码；消息不回显凭证 / 配置值）。
"""

from __future__ import annotations

import ipaddress
import logging
import re
import time
from dataclasses import dataclass, field, replace
from typing import AbstractSet, Any, Callable, Literal, Mapping, Sequence

from ib.core.errors import NotFoundError
from ib.core.ports import McpStores, SecretCipher
from ib.core.types import (
    MCP_AUTH_KINDS,
    MCP_DATA_CATEGORIES,
    MCP_HARD_MAX,
    MCP_TRANSPORT_KINDS,
    McpGovernance,
    McpServer,
    McpServerLimits,
)
from ib.webtools.netguard import NEVER_ALLOW_NETWORKS, DomainRules, Resolver, UrlGuard, WebBlocked

from .auditing import audit_record, safe_record
from .catalog import McpCatalogService, VerificationFailed
from .crypto import SecretKeyError, validate_credential_input, validate_header_name
from .rules import validate_server_id
from .schema_lite import SchemaUnsupportedError, inline_local_refs, validate_args
from .wire import plain_http_allowed

__all__ = [
    "McpRequestError",
    "ServerInUse",
    "ServerCreate",
    "ServerPatch",
    "ServerUpdateResult",
    "DeleteOutcome",
    "CredentialStatusDto",
    "InternalAllowResult",
    "CleanupOutcome",
    "McpAdminService",
    "GrantIndex",
    "GrantCleaner",
    "UNSET",
]

_log = logging.getLogger("ib.mcp")
_HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9\-.]{0,251}[a-z0-9])?$")
_LIMIT_FIELDS = {
    "call_timeout_s": "call_timeout_s",
    "max_calls_per_turn": "max_calls_per_turn",
    "max_result_bytes": "max_result_bytes",
    "max_concurrency": "max_concurrency_per_server",
    "breaker_threshold": "breaker_threshold",
    "breaker_cooldown_s": "breaker_cooldown_s",
    "discover_timeout_s": "discover_timeout_s",
}
UNSET: Any = object()


class McpRequestError(Exception):
    """code 为稳定短码；http 为建议状态码；details 不含凭证 / 配置值。"""

    def __init__(self, code: str, http: int = 400, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.http = http
        self.details = dict(details or {})


class ServerInUse(McpRequestError):
    def __init__(self, references: Mapping[str, Any]) -> None:
        super().__init__("server_in_use", 409, {"references": dict(references)})
        self.references = dict(references)


@dataclass(frozen=True, slots=True)
class ServerCreate:
    server_id: str
    description: str
    transport: str
    endpoint_url: str
    auth_kind: str
    auth_header_name: str | None
    credential_scope: str
    scope_kind: str
    owner_project: str | None
    data_categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ServerPatch:
    description: Any = UNSET
    endpoint_url: Any = UNSET
    auth_kind: Any = UNSET
    auth_header_name: Any = UNSET
    data_categories: Any = UNSET
    limits: Any = UNSET  # McpServerLimits
    credential_scope: Any = UNSET
    transport: Any = UNSET


@dataclass(frozen=True, slots=True)
class ServerUpdateResult:
    server: McpServer
    identity_changed: bool
    tools_marked_rereview: int


@dataclass(frozen=True, slots=True)
class DeleteOutcome:
    deleted: bool
    cleaned_projects: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CredentialStatusDto:
    scope: str
    project_id: str | None
    configured: bool
    updated_at: str
    updated_by: str


@dataclass(frozen=True, slots=True)
class InternalAllowResult:
    host: str
    port: int
    effective: bool


@dataclass(frozen=True, slots=True)
class CleanupOutcome:
    project_id: str
    removed: tuple[str, ...]
    failed: bool
    error: str | None = None


# --------------------------------------------------------------------------- #
# GrantIndex / GrantCleaner
# --------------------------------------------------------------------------- #


class GrantIndex:
    """IFC-R29-143：遍历活动项目（以台账 / 注册表为准，M-PM-010）的当前已发布快照，一次遍历建引用映射。"""

    def __init__(self, *, projects: Any, snapshot_of: Callable[[str], Any]) -> None:
        self._projects = projects
        self._snapshot_of = snapshot_of

    def active_project_ids(self) -> tuple[str, ...]:
        return tuple(p.project_id for p in self._projects.list_active())

    def references(self) -> Mapping[str, tuple[tuple[str, str], ...]]:
        out: dict[str, list[tuple[str, str]]] = {}
        try:
            for pid in self.active_project_ids():
                snap = self._snapshot_of(pid)
                for g in snap.definition.tool_grants:
                    for t in g.tool_names:
                        if t.startswith("mcp__"):
                            out.setdefault(t, []).append((pid, g.expert_name))
        except Exception as exc:  # noqa: BLE001 - 引用信息不完整时不得放行删除
            raise McpRequestError("grant_index_unavailable", 503) from exc
        return {k: tuple(v) for k, v in out.items()}


class GrantCleaner:
    """IFC-R29-144：经既有发布服务移除项目定义文档里的外部授权（审计动作 mcp.grant_cleanup）。"""

    def __init__(
        self, *, publish: Any, clock: Callable[[], str], head_of: Callable[[str], int] | None = None
    ) -> None:
        self._publish = publish
        self._clock = clock
        self._head_of = head_of

    def _head(self, project_id: str) -> int:
        if self._head_of is not None:
            return int(self._head_of(project_id))
        return int(self._publish._versions.head(project_id).published_version)  # noqa: SLF001

    def remove_tools(
        self, project_id: str, local_names: AbstractSet[str], *, actor: str = "system:mcp-cleanup"
    ) -> CleanupOutcome:
        from ib.confsvc import PublishError, PublishRequest

        names = set(local_names)
        for attempt in range(2):  # 冲突重试 1 次
            try:
                snap = self._publish.current(project_id)
                doc = snap.definition
                grants = tuple(
                    replace(
                        g,
                        tool_names=tuple(t for t in g.tool_names if t not in names),
                        param_values=tuple(pv for pv in g.param_values if pv.name.split(".", 1)[0] not in names),
                    )
                    for g in doc.tool_grants
                )
                if grants == tuple(doc.tool_grants):
                    return CleanupOutcome(project_id, tuple(sorted(names)), False)
                req = PublishRequest(
                    project_id=project_id, actor=actor, base_version=self._head(project_id),
                    document=replace(doc, tool_grants=grants), prompts={}, message="mcp grant cleanup",
                    audit_action="mcp.grant_cleanup", audit_fields=("tool_grants",),
                )
                self._publish.publish(req)
                return CleanupOutcome(project_id, tuple(sorted(names)), False)
            except PublishError as exc:
                if exc.code == "no_changes":
                    return CleanupOutcome(project_id, tuple(sorted(names)), False)
                if exc.code == "conflict" and attempt == 0:
                    continue
                return CleanupOutcome(project_id, (), True, str(exc.code))
            except Exception:  # noqa: BLE001 - 失败返回 failed 而非抛出
                return CleanupOutcome(project_id, (), True, "cleanup_error")
        return CleanupOutcome(project_id, (), True, "conflict")


# --------------------------------------------------------------------------- #
# 管理服务
# --------------------------------------------------------------------------- #


def _norm_host(host: str) -> str:
    h = str(host).strip().lower().rstrip(".")
    try:
        return str(ipaddress.ip_address(h.strip("[]")))
    except ValueError:
        pass
    try:
        h = h.encode("idna").decode("ascii")
    except UnicodeError:
        raise McpRequestError("host_invalid") from None
    if len(h) > 253 or not _HOST_RE.match(h):
        raise McpRequestError("host_invalid")
    return h


class McpAdminService:
    def __init__(
        self,
        *,
        stores: McpStores,
        cipher: SecretCipher,
        catalog: McpCatalogService,
        audit: Any,
        grant_index: GrantIndex,
        grant_cleaner: GrantCleaner,
        runtime_refresher: Callable[[str], None],
        clock: Callable[[], str],
        resolver: Resolver | None = None,
    ) -> None:
        self._s = stores
        self._cipher = cipher
        self._catalog = catalog
        self._audit = audit
        self._index = grant_index
        self._cleaner = grant_cleaner
        self._refresh_runtime = runtime_refresher
        self._clock = clock
        self._resolver = resolver

    # -- 公共校验 ----------------------------------------------------------- #
    def _allow_set(self) -> frozenset[tuple[str, int]]:
        return frozenset((a.host, a.port) for a in self._s.servers.list_internal_allow())

    def _check_endpoint(self, url: Any, auth_kind: str) -> None:
        """AC-008-05：公网明文 http 先于 DNS 拒绝；其后经 UrlGuard 预检（地址被拒 ⇒ address_blocked）。"""
        if not isinstance(url, str) or not url.strip() or len(url) > 2048:
            raise McpRequestError("endpoint_url_invalid")
        allow = self._allow_set()
        low = url.strip().lower()
        if not (low.startswith("http://") or low.startswith("https://")):
            raise McpRequestError("endpoint_url_invalid")
        if not plain_http_allowed(url, allow):
            raise McpRequestError("plain_http_public_forbidden")
        if auth_kind == "none":
            from urllib.parse import urlsplit

            parts = urlsplit(url.strip())
            port = parts.port if parts.port is not None else (443 if parts.scheme.lower() == "https" else 80)
            if ((parts.hostname or "").lower().rstrip("."), port) not in allow:
                raise McpRequestError("auth_none_requires_internal_allow")
        guard = UrlGuard(DomainRules((), ()), resolver=self._resolver, allowed_ports=None, internal_allow=allow)
        try:
            guard.check(url.strip(), deadline=time.monotonic() + 5.0)
        except WebBlocked:
            raise McpRequestError("address_blocked") from None

    def _check_common(
        self, *, transport: Any, description: Any, auth_kind: Any, header: Any, credential_scope: Any,
        categories: Any,
    ) -> None:
        if transport not in MCP_TRANSPORT_KINDS:
            raise McpRequestError("transport_not_supported")  # AC-001-06：不创建、不启动进程
        if not isinstance(description, str) or len(description) > 500:
            raise McpRequestError("description_invalid")
        if auth_kind not in MCP_AUTH_KINDS:
            raise McpRequestError("auth_kind_invalid")
        if auth_kind == "header":
            try:
                validate_header_name(header)
            except ValueError as exc:
                raise McpRequestError(str(exc)) from None
        elif header not in (None, ""):
            raise McpRequestError("auth_header_name_not_applicable")
        if credential_scope not in ("shared", "project"):
            raise McpRequestError("credential_scope_invalid")
        if (
            not isinstance(categories, (list, tuple))
            or not (1 <= len(categories) <= 4)
            or any(c not in MCP_DATA_CATEGORIES for c in categories)
            or len(set(categories)) != len(categories)
        ):
            raise McpRequestError("data_categories_invalid")
        if auth_kind in ("bearer", "header") and not self._cipher.configured:
            raise McpRequestError("secret_key_missing", 409)  # AC-006-06

    def _active_ids(self) -> tuple[str, ...]:
        return self._index.active_project_ids()

    def _affected_projects(self, server_id: str, extra: Sequence[str] = ()) -> list[str]:
        names = {t.local_name for t in self._s.tools.list(server_id=server_id)}
        refs = self._index.references()
        pids = {p for n in names for (p, _e) in refs.get(n, ())}
        pids.update(extra)
        return sorted(pids)

    def refresh_projects(self, server_id: str, extra: Sequence[str] = ()) -> None:
        """对引用该 Server 工具的项目触发后台重编译（单飞，失败保留旧快照）。尽力而为。"""
        try:
            for pid in self._affected_projects(server_id, extra):
                try:
                    self._refresh_runtime(pid)
                except Exception:  # noqa: BLE001
                    _log.warning("mcp runtime refresh failed project=%s", pid)
        except McpRequestError:
            _log.warning("mcp runtime refresh skipped (grant index unavailable)")

    def _audit_admin(self, action: str, actor: str, server_id: str = "", reason: str = "", **kw: Any) -> None:
        safe_record(self._audit, audit_record(self._clock, action=action, actor=actor, server_id=server_id, reason=reason, **kw))

    def _get(self, server_id: str) -> McpServer:
        s = self._s.servers.get(server_id)
        if s is None:
            raise NotFoundError("server_not_found")
        return s

    # -- Server CRUD -------------------------------------------------------- #
    def register(self, spec: ServerCreate, *, actor: str) -> McpServer:
        """IFC-R29-140：校验 → create（admin_state='registered'）→ 审计。"""
        self._check_common(
            transport=spec.transport, description=spec.description, auth_kind=spec.auth_kind,
            header=spec.auth_header_name, credential_scope=spec.credential_scope, categories=spec.data_categories,
        )
        try:
            validate_server_id(spec.server_id)
        except ValueError:
            raise McpRequestError("server_id_invalid") from None
        if spec.scope_kind not in ("platform", "project"):
            raise McpRequestError("scope_kind_invalid")
        if spec.scope_kind == "project":
            if not spec.owner_project or spec.owner_project not in self._active_ids():
                raise McpRequestError("project_unknown")
        elif spec.owner_project:
            raise McpRequestError("owner_project_not_applicable")
        self._check_endpoint(spec.endpoint_url, spec.auth_kind)
        now = self._clock()
        server = McpServer(
            server_id=spec.server_id, description=spec.description, transport=spec.transport,
            endpoint_url=spec.endpoint_url.strip(), auth_kind=spec.auth_kind,
            auth_header_name=spec.auth_header_name or None, credential_scope=spec.credential_scope,
            scope_kind=spec.scope_kind, owner_project=spec.owner_project or None, open_all=False,
            data_categories=tuple(spec.data_categories), admin_state="registered", health="unknown",
            health_checked_at=None, protocol_era=None, protocol_version=None, supports_list_changed=False,
            last_verify_at=None, last_verify_result=None, identity_epoch=0, limits=McpServerLimits(),
            created_at=now, created_by=actor, updated_at=now, updated_by=actor,
        )
        from ib.core.errors import ConflictError

        try:
            created = self._s.servers.create(server)
        except ConflictError:
            raise McpRequestError("server_id_exists") from None
        self._audit_admin("server.register", actor, spec.server_id)
        return created

    def update(
        self, server_id: str, patch: ServerPatch, *, expected_updated_at: str, actor: str
    ) -> ServerUpdateResult:
        cur = self._get(server_id)
        if cur.updated_at != expected_updated_at:
            raise McpRequestError("stale_update", 409)
        new = cur
        changes: dict[str, Any] = {}
        for f in ("description", "endpoint_url", "auth_kind", "auth_header_name", "data_categories", "credential_scope"):
            v = getattr(patch, f)
            if v is not UNSET:
                changes[f] = v
        transport = cur.transport if patch.transport is UNSET else patch.transport
        merged = replace(cur, **{k: (tuple(v) if k == "data_categories" else v) for k, v in changes.items()})
        self._check_common(
            transport=transport, description=merged.description, auth_kind=merged.auth_kind,
            header=merged.auth_header_name, credential_scope=merged.credential_scope,
            categories=merged.data_categories,
        )
        if patch.limits is not UNSET:
            lim = patch.limits
            if not isinstance(lim, McpServerLimits):
                raise McpRequestError("limits_invalid")
            for fld, gov_name in _LIMIT_FIELDS.items():
                v = getattr(lim, fld)
                lo, hi = MCP_HARD_MAX[gov_name]
                if v is not None and (isinstance(v, bool) or not isinstance(v, int) or not (max(1, lo) <= v <= hi)):
                    raise McpRequestError("limits_invalid", details={"field": fld})
            merged = replace(merged, limits=lim)
        identity_changed = (
            merged.endpoint_url != cur.endpoint_url
            or merged.auth_kind != cur.auth_kind
            or (merged.auth_header_name or None) != (cur.auth_header_name or None)
        )
        if "endpoint_url" in changes or "auth_kind" in changes:
            self._check_endpoint(merged.endpoint_url, merged.auth_kind)
        merged = replace(
            merged,
            endpoint_url=merged.endpoint_url.strip(),
            auth_header_name=merged.auth_header_name or None,
            admin_state="registered" if identity_changed else merged.admin_state,
            updated_at=self._clock(),
            updated_by=actor,
        )
        updated = self._s.servers.update(merged, expected_updated_at=expected_updated_at)
        marked = 0
        if identity_changed:
            marked = self._s.tools.mark_identity_changed(server_id, now=self._clock())
            self.refresh_projects(server_id)
        self._audit_admin("server.update", actor, server_id, reason=f"identity_changed={int(identity_changed)}")
        return ServerUpdateResult(self._get(server_id) if identity_changed else updated, identity_changed, marked)

    def enable(self, server_id: str, *, actor: str) -> McpServer:
        self._get(server_id)
        out = self._catalog.verify(server_id, actor=actor)
        if not out.ok:
            raise McpRequestError("verification_failed", 409, {"category": out.category})
        s = self._s.servers.set_admin_state(server_id, "enabled", actor=actor, now=self._clock())
        try:
            self._catalog.refresh(server_id, actor=actor)
        except VerificationFailed:
            pass  # 已启用；清单刷新失败由 supervisor 重试，不回滚启用
        self._audit_admin("server.enable", actor, server_id)
        self.refresh_projects(server_id)
        return self._get(server_id) if s else s

    def disable(self, server_id: str, *, actor: str) -> McpServer:
        s = self._s.servers.set_admin_state(server_id, "disabled", actor=actor, now=self._clock())
        self._audit_admin("server.disable", actor, server_id)
        self.refresh_projects(server_id)
        return s

    def delete(self, server_id: str, *, confirm: str, force: bool, actor: str) -> DeleteOutcome:
        """IFC-R29-141。"""
        self._get(server_id)
        if confirm != server_id:
            raise McpRequestError("confirm_mismatch")
        names = {t.local_name for t in self._s.tools.list(server_id=server_id)}
        refs = {n: r for n, r in self._index.references().items() if n in names}
        if refs and not force:
            raise ServerInUse(refs)
        cleaned: list[str] = []
        if refs:
            self._s.servers.set_admin_state(server_id, "disabled", actor=actor, now=self._clock())  # 先停用：调用即刻被拒
            per_project: dict[str, set[str]] = {}
            for n, rr in refs.items():
                for pid, _e in rr:
                    per_project.setdefault(pid, set()).add(n)
            failed = []
            for pid, ns in sorted(per_project.items()):
                out = self._cleaner.remove_tools(pid, ns, actor="system:mcp-cleanup")
                (failed if out.failed else cleaned).append(pid)
            if failed:
                self._audit_admin("server.delete", actor, server_id, outcome="failed", reason="cleanup_failed")
                raise McpRequestError("cleanup_failed", 409, {"projects": failed})
        self._s.servers.delete_cascade(server_id)
        self._audit_admin("server.delete", actor, server_id, reason=f"force={int(bool(force))};cleaned={len(cleaned)}")
        for pid in cleaned:
            try:
                self._refresh_runtime(pid)
            except Exception:  # noqa: BLE001
                pass
        return DeleteOutcome(True, tuple(cleaned))

    # -- 凭证 --------------------------------------------------------------- #
    def _scope_key(self, s: McpServer, scope: str, project_id: str | None) -> str:
        if scope == "shared":
            if s.credential_scope != "shared":
                raise McpRequestError("credential_scope_mismatch")
            return "@shared"
        if s.credential_scope != "project":
            raise McpRequestError("credential_scope_mismatch")
        if scope == "discovery":
            return "@discovery"
        if scope == "project":
            if not project_id or project_id not in self._active_ids():
                raise McpRequestError("project_unknown")
            return project_id
        raise McpRequestError("credential_scope_invalid")

    def set_credential(
        self, server_id: str, scope: Literal["shared", "discovery", "project"], project_id: str | None, secret: str, *, actor: str
    ) -> CredentialStatusDto:
        s = self._get(server_id)
        key = self._scope_key(s, scope, project_id)
        if not self._cipher.configured:
            raise McpRequestError("secret_key_missing", 409)
        try:
            plain = validate_credential_input(secret, auth_kind=s.auth_kind, header_name=s.auth_header_name)
        except ValueError as exc:
            raise McpRequestError("credential_invalid", details={"reason": str(exc)}) from None
        try:
            token, key_id = self._cipher.encrypt(plain)
        except SecretKeyError as exc:
            raise McpRequestError("secret_key_missing" if exc.reason == "secret_key_missing" else "credential_invalid", 409) from None
        now = self._clock()
        self._s.credentials.put(server_id, key, token, key_id, actor=actor, now=now)
        self._audit_admin("credential.set", actor, server_id, reason=f"scope={scope}")
        return CredentialStatusDto(scope, project_id if scope == "project" else None, True, now, actor)

    def clear_credential(self, server_id: str, scope: str, project_id: str | None, *, actor: str) -> None:
        s = self._get(server_id)
        key = self._scope_key(s, scope, project_id)
        self._s.credentials.delete(server_id, key)
        self._audit_admin("credential.clear", actor, server_id, reason=f"scope={scope}")

    # -- 开放 / 固定入参 / 放行 ---------------------------------------------- #
    def set_open(self, server_id: str, *, open_all: bool, project_ids: Sequence[str], actor: str) -> None:
        self._get(server_id)
        active = set(self._active_ids())
        pids = tuple(dict.fromkeys(str(p) for p in project_ids))
        if len(pids) > 200 or any(p not in active for p in pids):
            raise McpRequestError("project_unknown")
        before = set(self._s.servers.open_projects(server_id))
        self._s.servers.set_open(server_id, open_all=bool(open_all), project_ids=pids, actor=actor, now=self._clock())
        self._audit_admin("server.open", actor, server_id, reason=f"open_all={int(bool(open_all))};projects={len(pids)}")
        self.refresh_projects(server_id, extra=sorted(before - set(pids)))

    def _tool(self, tool_id: int) -> Any:
        t = self._s.tools.get(tool_id)
        if t is None:
            raise NotFoundError("tool_not_found")
        return t

    def put_fixed_args(self, tool_id: int, project_id: str, fixed_args: Mapping[str, Any], *, actor: str) -> None:
        t = self._tool(tool_id)
        if t.approved is None:
            raise McpRequestError("tool_not_reviewed", 409)
        if project_id not in self._active_ids():
            raise McpRequestError("project_unknown")
        if not isinstance(fixed_args, Mapping):
            raise McpRequestError("fixed_args_invalid")
        props = t.approved.input_schema.get("properties") if isinstance(t.approved.input_schema, Mapping) else None
        props = props if isinstance(props, Mapping) else {}
        unknown = [k for k in fixed_args if k not in props]
        if unknown:
            raise McpRequestError("fixed_args_key_unknown", details={"keys": unknown[:10]})
        import json

        try:
            if len(json.dumps(dict(fixed_args), ensure_ascii=False).encode("utf-8")) > 8192:
                raise McpRequestError("fixed_args_too_large")
            flat = inline_local_refs(
                {"type": "object", "properties": dict(props), **({"$defs": t.approved.input_schema["$defs"]} if "$defs" in t.approved.input_schema else {})},
                max_depth=16, max_bytes=1_048_576,
            )
        except (TypeError, ValueError, SchemaUnsupportedError):
            raise McpRequestError("fixed_args_invalid") from None
        viol = validate_args(flat, dict(fixed_args), max_depth=16)
        if viol:
            raise McpRequestError(
                "fixed_args_invalid", details={"items": [{"path": v.path, "code": v.code} for v in viol[:10]]}
            )
        self._s.tools.put_binding(tool_id, project_id, dict(fixed_args), actor=actor, now=self._clock())
        self._audit_admin(
            "tool.fixed_args", actor, t.server_id, reason=f"keys={len(fixed_args)}", tool_name=t.local_name,
            display_name=t.display_name, project_id=project_id,
        )
        try:
            self._refresh_runtime(project_id)
        except Exception:  # noqa: BLE001
            pass

    def grant_waiver(self, tool_id: int, project_id: str, *, reason: str, actor: str) -> None:
        t = self._tool(tool_id)
        r = str(reason or "").strip()
        if not (1 <= len(r) <= 500):
            raise McpRequestError("waiver_reason_invalid")
        if t.risk not in ("side_effect", "unknown"):
            raise McpRequestError("waiver_not_applicable")
        if project_id not in self._active_ids():
            raise McpRequestError("project_unknown")
        self._s.tools.grant_waiver(tool_id, project_id, reason=r, actor=actor, now=self._clock())
        self._audit_admin("waiver.grant", actor, t.server_id, reason="granted", tool_name=t.local_name,
                          display_name=t.display_name, project_id=project_id)

    def revoke_waiver(self, tool_id: int, project_id: str, *, actor: str) -> None:
        t = self._tool(tool_id)
        self._s.tools.revoke_waiver(tool_id, project_id, actor=actor, now=self._clock())
        self._audit_admin("waiver.revoke", actor, t.server_id, reason="revoked", tool_name=t.local_name,
                          display_name=t.display_name, project_id=project_id)

    # -- 治理 / 允许名单 ----------------------------------------------------- #
    def set_governance(self, g: McpGovernance, *, actor: str) -> McpGovernance:
        try:
            out = self._s.governance.set(g, actor=actor)
        except ValueError as exc:
            raise McpRequestError("governance_invalid", details={"reason": str(exc)}) from None
        self._audit_admin("governance.set", actor)
        return out

    def add_internal_allow(self, host: str, port: int, *, actor: str) -> InternalAllowResult:
        if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
            raise McpRequestError("port_invalid")
        h = _norm_host(host)
        effective = True
        try:
            ip = ipaddress.ip_address(h)
            effective = not any(ip.version == n.version and ip in n for n in NEVER_ALLOW_NETWORKS)
        except ValueError:
            pass
        self._s.servers.add_internal_allow(h, int(port), actor=actor, now=self._clock())
        self._audit_admin("internal_allow.add", actor, reason=f"effective={int(effective)}")
        return InternalAllowResult(h, int(port), effective)

    def remove_internal_allow(self, host: str, port: int, *, actor: str) -> bool:
        if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
            raise McpRequestError("port_invalid")
        ok = self._s.servers.remove_internal_allow(_norm_host(host), int(port))
        self._audit_admin("internal_allow.remove", actor)
        return ok
