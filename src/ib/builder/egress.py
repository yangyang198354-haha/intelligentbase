# MOD-R26-11 / implements IFC-R26-101：Builder 外发的单点（白名单载荷 + 秘钥拦截 + 审计先行 + 限时）
"""云端调用的唯一出口（REQ-NFUNC-014，C-R26-11）。

* 载荷类型 `OutboundPayload` 的字段集就是白名单——类型里没有会话 / 资料正文 / 账号 / 审计 / 其他项目字段；
* 顺序固定：规模 / 秘钥模式检查（`EgressRejected`）→ 写审计（失败 → `BuilderUnavailable(audit_failed)`，**不发送**）→
  线程池提交 → `future.result(timeout)`；线程池满 → `BuilderBusy`；
* 本包其他模块不得直接引用 provider 的补全方法（selfcheck `builder_single_egress`）。
"""

from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import asdict, dataclass
from typing import Any, Callable, Final, Literal, Protocol

from ib.core import ConfigAuditEntry

from .types import AgentDraft, BuilderBusy, BuilderUnavailable, EgressRejected, ProjectContext

__all__ = [
    "BUILDER_REQUIREMENT_MAX_CHARS",
    "BUILDER_INSTRUCTION_MAX_CHARS",
    "EGRESS_PAYLOAD_MAX_BYTES",
    "OutboundPayload",
    "BuilderCompleter",
    "EgressGuard",
    "contains_secret_pattern",
    "check_requirement",
]

BUILDER_REQUIREMENT_MAX_CHARS: Final[int] = 2000
BUILDER_INSTRUCTION_MAX_CHARS: Final[int] = 1000
EGRESS_PAYLOAD_MAX_BYTES: Final[int] = 64 * 1024

EgressKind = Literal["generate", "judge", "optimize", "review_existing"]

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*\S{4,}"),
)


def contains_secret_pattern(text: str) -> bool:
    """秘钥 / 令牌 / 口令模式扫描（纯函数；宁可误拦，不外发）。"""
    return any(p.search(text) for p in _SECRET_PATTERNS)


def check_requirement(text: str) -> str:
    """需求文本的入口校验：去首尾空白后 1..2000 字符。返回规整后的文本。"""
    t = (text or "").strip()
    if not t:
        raise EgressRejected("requirement_empty")
    if len(t) > BUILDER_REQUIREMENT_MAX_CHARS:
        raise EgressRejected("requirement_too_long")
    return t


@dataclass(frozen=True, slots=True)
class OutboundPayload:
    kind: EgressKind
    requirement_text: str | None = None
    instruction_text: str | None = None
    project_digest: ProjectContext | None = None
    selected_agent: AgentDraft | None = None
    rubric_items: tuple[str, ...] = ()


class BuilderCompleter(Protocol):
    def __call__(self, system: str, user: str, *, temperature: float, timeout_s: float) -> str: ...


def _categories(p: OutboundPayload) -> list[str]:
    cats: list[str] = []
    if p.requirement_text is not None:
        cats.append("requirement_text")
    if p.instruction_text is not None:
        cats.append("instruction_text")
    if p.project_digest is not None:
        cats.append("project_digest")
    if p.selected_agent is not None:
        cats.append("selected_agent")
    if p.rubric_items:
        cats.append("rubric_items")
    return cats


def render_user_message(p: OutboundPayload) -> str:
    """载荷 → 用户消息（仅白名单字段；JSON，便于模型当数据读取）。"""
    body: dict[str, Any] = {"kind": p.kind}
    if p.requirement_text is not None:
        body["requirement"] = p.requirement_text
    if p.instruction_text is not None:
        body["instruction"] = p.instruction_text
    if p.project_digest is not None:
        d = asdict(p.project_digest)
        d.pop("project_id", None)  # 项目标识不外发
        body["project"] = d
    if p.selected_agent is not None:
        body["agent"] = asdict(p.selected_agent)
    if p.rubric_items:
        body["rubric_items"] = list(p.rubric_items)
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


def _texts_of(p: OutboundPayload) -> list[str]:
    out: list[str] = []
    for t in (p.requirement_text, p.instruction_text):
        if t:
            out.append(t)
    if p.selected_agent is not None:
        a = p.selected_agent
        out.extend([a.main_prompt, a.fallback_prompt, a.cn_label, *a.keywords, *a.exemplars])
    if p.project_digest is not None:
        for ag in p.project_digest.agents:
            out.extend([ag.cn_label, *ag.keywords, *ag.exemplars])
    out.extend(p.rubric_items)
    return out


class EgressGuard:
    def __init__(
        self,
        *,
        completer: BuilderCompleter,
        audit: Any,
        clock: Callable[[], str],
        timeout_s: float = 60.0,
        pool_size: int = 2,
    ) -> None:
        self._completer = completer
        self._audit = audit
        self._clock = clock
        self._timeout_s = float(timeout_s)
        self._pool = ThreadPoolExecutor(max_workers=max(1, int(pool_size)), thread_name_prefix="ib-builder")
        self._slots = threading.BoundedSemaphore(max(1, int(pool_size)))

    def send(self, payload: OutboundPayload, *, system: str, project_id: str, actor: str) -> str:
        # 1) 规模 / 秘钥模式（先于任何副作用）
        user = render_user_message(payload)
        if len(user.encode("utf-8")) > EGRESS_PAYLOAD_MAX_BYTES:
            raise EgressRejected("egress_payload_too_large")
        if any(contains_secret_pattern(t) for t in _texts_of(payload)):
            raise EgressRejected("egress_secret_detected")
        # 2) 审计先行：写不进审计就不发送
        try:
            self._audit.record(
                ConfigAuditEntry(
                    timestamp=self._clock(),
                    project=project_id,
                    actor=actor,
                    action="builder.egress",
                    changed_field_names=(),
                    result="saved",
                    detail_code=None,
                    object_summary=(
                        f"kind:{payload.kind}",
                        *[f"cat:{c}" for c in _categories(payload)],
                        f"bytes:{len(user.encode('utf-8'))}",
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise BuilderUnavailable("audit_failed", "审计写入失败，已取消外发") from exc
        # 3) 限时调用（线程池满 → busy）
        if not self._slots.acquire(blocking=False):
            raise BuilderBusy()
        try:
            future = self._pool.submit(self._completer, system, user, temperature=0.0, timeout_s=self._timeout_s)
        except Exception:
            self._slots.release()
            raise
        future.add_done_callback(lambda _f: self._slots.release())
        try:
            return future.result(timeout=self._timeout_s)
        except FutureTimeout as exc:
            raise BuilderUnavailable("timeout", "Agent Builder 调用超时") from exc
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc


def _classify(exc: BaseException) -> BuilderUnavailable:
    name = type(exc).__name__.lower()
    text = str(exc)
    if "未配置" in text:
        return BuilderUnavailable("llm_unconfigured", "尚未配置 LLM Key，无法使用 Agent Builder 的 AI 生成")
    if "timeout" in name or "timed out" in text.lower():
        return BuilderUnavailable("timeout", "Agent Builder 调用超时")
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and 400 <= status < 500:
        return BuilderUnavailable("rejected", "云端拒绝了本次请求")
    return BuilderUnavailable("network", "无法连接云端模型服务")
