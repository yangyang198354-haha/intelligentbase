# MOD-R29-12 / implements IFC-R29-110..114 / depends MOD-R29-01, 02, 06, 10, 11
"""运行时：准入 / 熔断 / 回合预算 / 并发闸 / 调用器。

`McpInvoker.invoke` 的固定顺序（任一步失败即返回，且此前步骤不产生出站；永不抛）：
  ① enabled → ② 回合作用域 + reserve → ③ read_admission + admission_reason → ④ 断路器 / 健康 →
  ⑤ 并发闸（非阻塞）→ ⑥ 构造入参（丢弃屏蔽 / 固定键、叠加固定值、体积与 schema 预检）→ ⑦ 凭证解密 →
  ⑧ audit.begin_call（失败不发送）→ ⑨ client.call_tool → ⑩ 断路器记录 + finish_call → ⑪ render_result。
无确认步（HITL 已移出，OOS-R29-12）。日志只含枚举原因、server_id、耗时。
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Mapping

from ib.core.ports import SecretCipher
from ib.core.types import (
    MCP_HARD_MAX,
    McpAuditRecord,
    McpCallRequest,
    McpGovernance,
    ToolResult,
)

from .client import McpClient, McpClientError, McpTarget
from .crypto import SecretKeyError
from .result import phrase_for, render_result, sanitize_external
from .rules import admission_reason, canonical_json
from .schema_lite import validate_args

__all__ = [
    "admission_reason",
    "BreakerEvent",
    "McpBreaker",
    "McpTurnBudget",
    "bind_mcp_turn",
    "current_mcp_turn",
    "current_mcp_info",
    "ExternalToolBinding",
    "McpInvoker",
    "COUNTED_FAILURES",
]

_log = logging.getLogger("ib.mcp")
#: "计入类"失败：不可达 / 超时 / 协议错误 / 鉴权失败（5xx 经 unreachable）；不计入：isError、入参校验、准入拒绝、回合限额
COUNTED_FAILURES = frozenset({"unreachable", "timeout", "protocol_error", "auth_failed", "protocol_incompatible"})
_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime(_FMT)


def _parse_utc(s: str | None) -> float | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, _FMT).replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# 断路器
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class BreakerEvent:
    server_id: str
    from_state: str
    to_state: str


class McpBreaker:
    """内存态：closed → open（连续 N 次"计入类"失败）→ half_open（冷却 T 秒后放行恰一次探测）→ closed/open。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._s: dict[str, dict[str, Any]] = {}

    def _get(self, server_id: str) -> dict[str, Any]:
        return self._s.setdefault(server_id, {"state": "closed", "fails": 0, "opened_at": 0.0, "probing": False})

    def state(self, server_id: str) -> str:
        with self._lock:
            return str(self._get(server_id)["state"])

    def allow(self, server_id: str, *, now: float, threshold: int, cooldown_s: int) -> bool:
        with self._lock:
            st = self._get(server_id)
            if st["state"] == "closed":
                return True
            if st["state"] == "open":
                if now - st["opened_at"] >= cooldown_s:
                    st["state"], st["probing"] = "half_open", True
                    return True
                return False
            if st["probing"]:  # half_open：恰放行一次
                return False
            st["probing"] = True
            return True

    def record(
        self, server_id: str, *, ok: bool, counted: bool, now: float, threshold: int, cooldown_s: int
    ) -> BreakerEvent | None:
        with self._lock:
            st = self._get(server_id)
            prev = str(st["state"])
            if ok:
                st["fails"] = 0
                st["probing"] = False
                if prev != "closed":
                    st["state"] = "closed"
                    return BreakerEvent(server_id, prev, "closed")
                return None
            if not counted:
                st["probing"] = False  # 释放半开探测名额，不改变计数
                return None
            st["fails"] += 1
            st["probing"] = False
            if prev == "half_open" or (prev == "closed" and st["fails"] >= max(1, threshold)):
                st["state"], st["opened_at"] = "open", now
                return BreakerEvent(server_id, prev, "open")
            return None

    def reset(self, server_id: str | None = None) -> None:
        with self._lock:
            if server_id is None:
                self._s.clear()
            else:
                self._s.pop(server_id, None)


# --------------------------------------------------------------------------- #
# 回合预算（按 turn_id，跨 agent、跨外部工具合计）
# --------------------------------------------------------------------------- #


class McpTurnBudget:
    def __init__(self, turn_id: str) -> None:
        self.turn_id = turn_id
        self._lock = threading.Lock()
        self._total = 0
        self._by_server: dict[str, int] = {}

    def reserve(self, server_id: str, *, total_limit: int, server_limit: int | None) -> bool:
        """共享累计值 ≥ 发起调用的 agent 的有效上限即拒（AC-020-02）；拒绝不增加计数。"""
        with self._lock:
            if self._total >= int(total_limit):
                return False
            if server_limit is not None and self._by_server.get(server_id, 0) >= int(server_limit):
                return False
            self._total += 1
            self._by_server[server_id] = self._by_server.get(server_id, 0) + 1
            return True

    @property
    def total(self) -> int:
        with self._lock:
            return self._total

    def server_count(self, server_id: str) -> int:
        with self._lock:
            return self._by_server.get(server_id, 0)


_TTL_S = 900.0
_REG_LOCK = threading.Lock()
_REGISTRY: dict[str, tuple[McpTurnBudget, float]] = {}
_CTX: contextvars.ContextVar[tuple[McpTurnBudget, Mapping[str, Any]] | None] = contextvars.ContextVar(
    "ib_mcp_turn", default=None
)


@contextmanager
def bind_mcp_turn(info: Mapping[str, Any]) -> Iterator[McpTurnBudget]:
    """IFC-R29-113：contextvars + 进程级 TTL 登记簿（同 bind_web_turn 手法）。同一 turn_id 取得同一预算。"""
    turn_id = str(info.get("turn_id") or uuid.uuid4().hex)
    now = time.monotonic()
    with _REG_LOCK:
        for k in [k for k, (_b, exp) in _REGISTRY.items() if exp < now]:
            del _REGISTRY[k]
        ent = _REGISTRY.get(turn_id)
        budget = ent[0] if ent else McpTurnBudget(turn_id)
        _REGISTRY[turn_id] = (budget, now + _TTL_S)
    token = _CTX.set((budget, dict(info)))
    try:
        yield budget
    finally:
        _CTX.reset(token)


def current_mcp_turn() -> McpTurnBudget | None:
    cur = _CTX.get()
    return cur[0] if cur else None


def current_mcp_info() -> Mapping[str, Any] | None:
    cur = _CTX.get()
    return cur[1] if cur else None


# --------------------------------------------------------------------------- #
# 调用器
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ExternalToolBinding:
    """注册时固定的闭包数据（编译期快照）。"""

    project_id: str
    local_name: str
    display_name: str
    server_id: str
    remote_name: str
    bound_fingerprint: str
    input_schema: Mapping[str, Any]
    trial: bool


def _args_summary(args: Mapping[str, Any]) -> str:
    """只含键名与类型 / 长度，不含值。"""
    parts = []
    for k in sorted(args)[:20]:
        v = args[k]
        n = len(v) if isinstance(v, (str, list, tuple, dict)) else 0
        parts.append(f"{str(k)[:40]}:{type(v).__name__}({n})")
    return ",".join(parts)[:300]


def _low(*vals: int | None) -> int:
    return min(v for v in vals if v is not None)


class McpInvoker:
    def __init__(
        self,
        *,
        stores: Any,
        cipher: SecretCipher,
        client: McpClient,
        breaker: McpBreaker,
        clock: Callable[[], float] = time.monotonic,
        enabled: bool = True,
    ) -> None:
        self._stores = stores
        self._cipher = cipher
        self._client = client
        self._breaker = breaker
        self._clock = clock
        self._enabled = bool(enabled)
        self._sem_lock = threading.Lock()
        self._server_sems: dict[str, tuple[int, threading.BoundedSemaphore]] = {}
        self._global_sem: tuple[int, threading.BoundedSemaphore] | None = None

    def __repr__(self) -> str:
        return "McpInvoker()"

    # -- 内部工具 ----------------------------------------------------------- #
    def _gov(self) -> McpGovernance:
        try:
            return self._stores.governance.get()
        except Exception:  # noqa: BLE001 - 读取失败 ⇒ 保守默认（不放大权限）
            _log.warning("mcp governance unreadable (reason=governance_unreadable)")
            return McpGovernance()

    def _acquire(self, server_id: str, per_server: int, global_cap: int) -> list[threading.BoundedSemaphore] | None:
        with self._sem_lock:
            if self._global_sem is None or self._global_sem[0] != global_cap:
                self._global_sem = (global_cap, threading.BoundedSemaphore(global_cap))
            ent = self._server_sems.get(server_id)
            if ent is None or ent[0] != per_server:
                ent = (per_server, threading.BoundedSemaphore(per_server))
                self._server_sems[server_id] = ent
            g, s = self._global_sem[1], ent[1]
        if not g.acquire(blocking=False):
            return None
        if not s.acquire(blocking=False):
            g.release()
            return None
        return [g, s]

    def _audit_system(self, binding: ExternalToolBinding, action: str, outcome: str, reason: str) -> None:
        try:
            self._stores.audit.record(
                McpAuditRecord(
                    call_id=uuid.uuid4().hex, ts=_utc_now(), kind="call", action=action, actor="system",
                    project_id=binding.project_id, server_id=binding.server_id, tool_name=binding.local_name,
                    display_name=binding.display_name, outcome=outcome, reason=reason, duration_ms=0,
                    args_digest="", args_summary="", fingerprint=binding.bound_fingerprint, confirm=False,
                    trial=binding.trial,
                )
            )
        except Exception:  # noqa: BLE001 - 拒绝记录为尽力而为；真正出站前的 begin_call 才是硬前置
            pass

    def _deny(self, binding: ExternalToolBinding, reason: str, detail: str = "") -> ToolResult:
        _log.info("mcp call denied reason=%s server=%s", reason, binding.server_id)
        self._audit_system(binding, "call.denied", "denied", reason)
        text = phrase_for(reason)
        if detail:
            text = f"{text}：{detail}"
        return ToolResult(ok=False, content=text)

    # -- 入口 --------------------------------------------------------------- #
    def invoke(
        self,
        binding: ExternalToolBinding,
        llm_args: Mapping[str, Any],
        *,
        mcp_timeout_s: int,
        mcp_max_calls_per_turn: int,
    ) -> ToolResult:
        """永不抛；失败 → ToolResult(ok=False, content=固定短语)。"""
        try:
            return self._invoke(binding, llm_args, mcp_timeout_s, mcp_max_calls_per_turn)
        except Exception:  # noqa: BLE001
            _log.warning("mcp invoke unexpected failure server=%s", binding.server_id)
            return ToolResult(ok=False, content=phrase_for("tool_error"))

    def _invoke(self, binding: ExternalToolBinding, llm_args: Any, mcp_timeout_s: Any, mcp_max_calls: Any) -> ToolResult:
        # ① 总开关
        if not self._enabled:
            return self._deny(binding, "feature_disabled")
        # ② 回合作用域 + 预算
        budget = current_mcp_turn()
        if budget is None:
            return self._deny(binding, "no_turn_scope")
        gov0 = self._gov()
        try:
            agent_cap = int(mcp_max_calls)
        except (TypeError, ValueError):
            agent_cap = gov0.max_calls_per_turn
        total_limit = _low(gov0.max_calls_per_turn, agent_cap, MCP_HARD_MAX["max_calls_per_turn"][1])
        if not budget.reserve(binding.server_id, total_limit=max(1, total_limit), server_limit=None):
            return self._deny(binding, "turn_limit")
        # ③ 一次读取准入快照
        try:
            adm = self._stores.tools.read_admission(binding.project_id, binding.local_name)
        except Exception:  # noqa: BLE001
            return self._deny(binding, "admission_unreadable")
        reason = admission_reason(adm, bound_fingerprint=binding.bound_fingerprint, enabled=self._enabled)
        if reason is not None:
            return self._deny(binding, reason)
        assert adm is not None
        server, tool, gov = adm.server, adm.tool, adm.governance
        lim = server.limits
        srv_calls = lim.max_calls_per_turn
        if srv_calls is not None and budget.server_count(binding.server_id) > srv_calls:
            return self._deny(binding, "turn_limit")
        thr = _low(gov.breaker_threshold, lim.breaker_threshold)
        cool = _low(gov.breaker_cooldown_s, lim.breaker_cooldown_s)
        now = self._clock()
        # ④ 断路器 / 健康
        if not self._breaker.allow(binding.server_id, now=now, threshold=thr, cooldown_s=cool):
            return self._deny(binding, "circuit_open")

        def _release_breaker() -> None:
            self._breaker.record(binding.server_id, ok=False, counted=False, now=self._clock(), threshold=thr, cooldown_s=cool)

        if server.health == "down" and gov.health_interval_s > 0:
            checked = _parse_utc(server.health_checked_at)
            if checked is not None and time.time() - checked <= 3 * gov.health_interval_s:
                _release_breaker()
                return self._deny(binding, "server_down")
        # ⑤ 并发闸（非阻塞）
        sems = self._acquire(
            binding.server_id, _low(gov.max_concurrency_per_server, lim.max_concurrency), gov.max_inflight_global
        )
        if sems is None:
            _release_breaker()
            return self._deny(binding, "busy")
        try:
            return self._call(binding, llm_args, mcp_timeout_s, adm, gov, thr, cool)
        finally:
            for s in sems:
                try:
                    s.release()
                except ValueError:
                    pass

    def _call(self, binding: ExternalToolBinding, llm_args: Any, mcp_timeout_s: Any, adm: Any, gov: McpGovernance, thr: int, cool: int) -> ToolResult:
        server, tool = adm.server, adm.tool
        lim = server.limits

        def _fail_early(reason: str, detail: str = "") -> ToolResult:
            self._breaker.record(binding.server_id, ok=False, counted=False, now=self._clock(), threshold=thr, cooldown_s=cool)
            return self._deny(binding, reason, detail)

        # ⑥ 构造入参
        if not isinstance(llm_args, Mapping) or tool.approved is None:
            return _fail_early("bad_arguments")
        drop = set(tool.hidden_params) | set(adm.fixed_args)
        # DEF-R29-004（AC-027-04 / REQ-NFUNC-009）：仅保留已审核 inputSchema.properties 中声明且未被屏蔽 / 固定的键
        _props = tool.approved.input_schema.get("properties") if isinstance(tool.approved.input_schema, Mapping) else None
        declared = set(_props) if isinstance(_props, Mapping) else set()
        args: dict[str, Any] = {
            k: v for k, v in llm_args.items() if isinstance(k, str) and k in declared and k not in drop
        }
        args.update(adm.fixed_args)
        try:
            size = len(canonical_json(args).encode("utf-8"))
        except (TypeError, ValueError):
            return _fail_early("bad_arguments")
        if size > gov.max_arg_bytes:
            return _fail_early("bad_arguments")
        viol = validate_args(tool.approved.input_schema, args, max_depth=gov.max_schema_depth)
        if viol:
            detail = "；".join(
                sanitize_external(f"{v.path} {v.code}", max_chars=80) for v in viol[:5]
            )
            return _fail_early("bad_arguments", detail)
        # ⑦ 凭证
        cred = None
        if server.auth_kind != "none":
            scope_key = "@shared" if server.credential_scope == "shared" else binding.project_id
            try:
                got = self._stores.credentials.get_ciphertext(server.server_id, scope_key)
            except Exception:  # noqa: BLE001
                return _fail_early("admission_unreadable")
            if got is None:
                return _fail_early("credential_missing")
            try:
                cred = self._cipher.decrypt(got[0])
            except SecretKeyError:
                return _fail_early("secret_key_missing")
        # ⑧ 审计先行
        call_id = uuid.uuid4().hex
        info = current_mcp_info() or {}
        t0 = self._clock()
        try:
            self._stores.audit.begin_call(
                McpAuditRecord(
                    call_id=call_id, ts=_utc_now(), kind="call", action="call", actor=str(info.get("actor_id", "unknown")),
                    project_id=binding.project_id, server_id=binding.server_id, tool_name=binding.local_name,
                    display_name=binding.display_name, outcome="pending", reason="", duration_ms=None,
                    args_digest=hashlib.sha256(canonical_json(args).encode("utf-8")).hexdigest()[:16],
                    args_summary=_args_summary(args), fingerprint=binding.bound_fingerprint, confirm=False,
                    trial=binding.trial,
                )
            )
        except Exception:  # noqa: BLE001
            return _fail_early("audit_failed")
        # ⑨ 出站
        try:
            timeout = _low(int(mcp_timeout_s), gov.call_timeout_s, lim.call_timeout_s)
        except (TypeError, ValueError):
            timeout = gov.call_timeout_s
        max_bytes = _low(gov.max_result_bytes, lim.max_result_bytes)
        target = McpTarget(
            server_id=server.server_id, url=server.endpoint_url, auth_kind=server.auth_kind,
            auth_header_name=server.auth_header_name, era=server.protocol_era, version=server.protocol_version,
        )
        kind: str | None = None
        raw = None
        try:
            raw = self._client.call_tool(
                target, cred, McpCallRequest(server.server_id, tool.remote_name, args),
                input_schema=tool.approved.input_schema, max_bytes=max_bytes,
                deadline=self._clock() + max(1, timeout),
            )
        except McpClientError as exc:
            kind = str(exc.kind)
        except Exception:  # noqa: BLE001
            kind = "tool_error"
        # ⑩ 记录
        dur = int((self._clock() - t0) * 1000)
        ok_transport = kind is None
        counted = kind in COUNTED_FAILURES if kind else False
        ev = self._breaker.record(
            binding.server_id, ok=ok_transport, counted=counted, now=self._clock(), threshold=thr, cooldown_s=cool
        )
        if ev is not None:
            self._audit_system(binding, f"breaker.{ev.to_state}", "info", ev.to_state)
        try:
            if kind is not None:
                self._stores.audit.finish_call(call_id, outcome="failed", reason=kind, duration_ms=dur)
            else:
                self._stores.audit.finish_call(
                    call_id, outcome="error" if raw.is_error else "ok", reason="tool_error" if raw.is_error else "", duration_ms=dur  # type: ignore[union-attr]
                )
        except Exception:  # noqa: BLE001
            _log.warning("mcp audit finish failed server=%s", binding.server_id)
        if kind is not None:
            return ToolResult(ok=False, content=phrase_for(kind))
        # ⑪ 转换
        rr = render_result(raw, max_bytes=max_bytes)  # type: ignore[arg-type]
        return ToolResult(ok=not rr.is_error, content=rr.text)
