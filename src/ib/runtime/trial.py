# MOD-R26-12 / implements IFC-R26-113 / depends MOD-R26-12(compile), 10
"""保存前试运行（REQ-FUNC-023）：用**草稿快照**编译一份一次性的运行时配置，与正式会话 / 在用版本完全隔离。

* 校验不过 → `ValidationFailed`（调用方在打开 SSE 之前转 400，且不会调用 LLM）；
* 独立 `MemorySessionStore`、会话键 `<project>:<actor>:trial-<session_id>`，不进入正式会话列表；
* 运行记录 `config_version = -1`；并发 / 频率受限，超限 `TrialBusyError`（429，不排队）；
* 编译结果按清单哈希做小型 TTL 缓存（连续提问不重复编译）。
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterator

from ib.core import ConfigSnapshot, DependencyUnavailableError, IbError, ValidationErrorItem
from ib.runtime.compile import RuntimeDeps, compile_project_config

__all__ = ["TrialLimits", "TrialBusyError", "ValidationFailed", "TrialRunner"]


@dataclass(frozen=True)
class TrialLimits:
    per_project_concurrency: int = 1
    global_concurrency: int = 2
    per_actor_turns_per_10min: int = 20  # [ESTIMATE]
    draft_max_bytes: int = 1024 * 1024
    cache_size: int = 4
    cache_ttl_s: float = 600.0


class TrialBusyError(DependencyUnavailableError):
    """试运行并发 / 频率超限 ⇒ 429 `trial_busy`。"""

    def __init__(self, message: str = "试运行繁忙，请稍后再试") -> None:
        super().__init__(message, dependency="trial")
        self.code = "trial_busy"


class ValidationFailed(IbError):
    def __init__(self, items: tuple[ValidationErrorItem, ...]) -> None:
        super().__init__("草稿配置校验未通过", code="validation_error")
        self.items = items


class TrialRunner:
    def __init__(
        self,
        *,
        deps: RuntimeDeps,
        validator: Callable[[ConfigSnapshot], tuple[ValidationErrorItem, ...]],
        limits: TrialLimits = TrialLimits(),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        from ib.streaming import MemorySessionStore

        self._deps = replace(deps, sessions=MemorySessionStore(max_sessions=200, idle_ttl_s=1800))
        self._validator = validator
        self._limits = limits
        self._clock = clock
        self._lock = threading.Lock()
        self._active_global = 0
        self._active_project: dict[str, int] = {}
        self._actor_hits: dict[str, deque] = {}
        self._cache: "OrderedDict[tuple[str, str], tuple[float, Any]]" = OrderedDict()

    def validate(self, snapshot: ConfigSnapshot) -> tuple[ValidationErrorItem, ...]:
        return tuple(self._validator(snapshot))

    # ------------------------------------------------------------------ #

    def _admit(self, project_id: str, actor: str) -> None:
        now = self._clock()
        with self._lock:
            hits = self._actor_hits.setdefault(actor, deque())
            while hits and now - hits[0] > 600.0:
                hits.popleft()
            if (
                self._active_global >= self._limits.global_concurrency
                or self._active_project.get(project_id, 0) >= self._limits.per_project_concurrency
                or len(hits) >= self._limits.per_actor_turns_per_10min
            ):
                raise TrialBusyError()
            hits.append(now)
            self._active_global += 1
            self._active_project[project_id] = self._active_project.get(project_id, 0) + 1

    def _release(self, project_id: str) -> None:
        with self._lock:
            self._active_global = max(0, self._active_global - 1)
            self._active_project[project_id] = max(0, self._active_project.get(project_id, 0) - 1)

    def _compiled(self, project_id: str, snapshot: ConfigSnapshot) -> Any:
        from ib.config.versioning import manifest_hash

        key = (project_id, manifest_hash(snapshot))
        now = self._clock()
        with self._lock:
            hit = self._cache.get(key)
            if hit is not None and now - hit[0] <= self._limits.cache_ttl_s:
                self._cache.move_to_end(key)
                return hit[1]
        compiled = compile_project_config(project_id, -1, snapshot, deps=self._deps, source="snapshot", trial=True)
        with self._lock:
            self._cache[key] = (now, compiled)
            while len(self._cache) > self._limits.cache_size:
                self._cache.popitem(last=False)
        return compiled

    def run(
        self, project_id: str, snapshot: ConfigSnapshot, query: str, *, ctx: Any, session_id: str
    ) -> Iterator[Any]:
        """校验 → 限流 → 编译（均在返回迭代器**之前**完成，使调用方能在打开 SSE 前转成 4xx/429）。"""
        from ib.context import session_key as ib_session_key
        from ib.core import StreamEventKind
        from ib.streaming import StreamEvent

        errors = self.validate(snapshot)
        if errors:
            raise ValidationFailed(errors)
        actor = str(ctx.authz.actor_id)
        self._admit(project_id, actor)
        try:
            compiled = self._compiled(project_id, snapshot)
            # 主体标识可能含 ":"（如 actor:<project>），会话键各段不得含冒号 ⇒ 仅在试运行键里替换为 "_"
            key = ib_session_key(project_id, actor.replace(":", "_"), f"trial-{session_id}")
        except BaseException:
            self._release(project_id)
            raise

        def _events() -> Iterator[Any]:
            try:
                yield StreamEvent(StreamEventKind.REASONING, "试运行（草稿配置，不影响在用版本）")
                yield from compiled.orchestrator.run(query, ctx=ctx, session_key=key)
            finally:
                self._release(project_id)

        return _events()
