# MOD-R26-12 / implements IFC-R26-111, IFC-R26-112 / depends MOD-R26-01, 05, 06(port)
"""项目运行时缓存：head 探测（节流）、单飞后台编译、原子换引用、钉旧版（ADR-53 / ADR-54）。

* `acquire`：热路径。节流窗口内直接返回当前引用；越过节流读 head，版本不一致 → 触发后台单飞编译，**本次仍返回旧版**
  （一次提问只绑定一个版本，REQ-NFUNC-003）。冷启动（无快照）阻塞式编译，失败抛出（fail-closed，绝不用半成品服务）。
* `install`：发布进程提交后立即换引用（一次引用赋值，原子）；`acquire_version`：恢复挂起会话时钉住开始时的版本。
* 编译失败：旧快照继续服务，状态标 `apply_failed`，退避 5 s 起 ×2、上限 60 s。
* `source="files"`（冷启动）时比对文件态与 head 版本行的 `manifest_hash`：不一致 ⇒ 改以 head 快照编译并标 `drift=True`
  （有人绕过系统直接改了文件；ADR-55 的有意取舍：以已发布版本为准，由管理档“采纳漂移”后才生效）。
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Literal

from ib.core import ConfigSnapshot, ConflictError, HeadState
from ib.runtime.compile import CompiledProjectConfig, RuntimeDeps, compile_project_config

__all__ = [
    "RuntimeState",
    "RuntimeStatus",
    "RuntimeLease",
    "ConfigVersionExpiredError",
    "ProjectRuntimeCache",
]

RuntimeState = Literal["ok", "applying", "apply_failed"]
_BACKOFF_START_S = 5.0
_BACKOFF_MAX_S = 60.0


class ConfigVersionExpiredError(ConflictError):
    """挂起会话所绑定的旧版本已被修剪 ⇒ 409 `config_version_expired`（fail-closed，不新建会话重跑）。"""

    def __init__(self, message: str = "会话所绑定的配置版本已过期，无法恢复") -> None:
        super().__init__(message, code="config_version_expired")


@dataclass(frozen=True)
class RuntimeStatus:
    applied_version: int
    head_version: int
    state: RuntimeState
    drift: bool
    last_error_code: str | None


@dataclass(frozen=True)
class RuntimeLease:
    """不可变引用；持有即“本次提问绑定该版本”。"""

    compiled: CompiledProjectConfig


class _Entry:
    __slots__ = ("current", "recent", "last_check", "building", "state", "drift", "error", "backoff_s", "retry_at", "head_seen")

    def __init__(self) -> None:
        self.current: CompiledProjectConfig | None = None
        self.recent: "OrderedDict[int, CompiledProjectConfig]" = OrderedDict()
        self.last_check = float("-inf")
        self.building = False
        self.state: RuntimeState = "ok"
        self.drift = False
        self.error: str | None = None
        self.backoff_s = 0.0
        self.retry_at = 0.0
        self.head_seen = 0


class ProjectRuntimeCache:
    def __init__(
        self,
        *,
        versions: Any,
        loader: Any,
        deps: RuntimeDeps,
        check_interval_s: float = 1.0,
        keep_recent: int = 3,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._versions = versions
        self._loader = loader
        self._deps = deps
        self._interval = max(0.0, float(check_interval_s))
        self._keep = max(1, int(keep_recent))
        self._clock = clock
        self._lock = threading.RLock()
        self._entries: dict[str, _Entry] = {}

    # ------------------------------------------------------------------ #
    # 热路径
    # ------------------------------------------------------------------ #

    def acquire(self, project_id: str) -> RuntimeLease:
        entry = self._entry(project_id)
        if entry.current is None:
            self._cold_compile(project_id, entry)
            assert entry.current is not None
            return RuntimeLease(entry.current)
        # 先记快照再触发后台编译：本次调用只绑定触发前的版本，不受编译线程时序影响。
        snap = entry.current
        now = self._clock()
        if now - entry.last_check >= self._interval:
            entry.last_check = now
            head = self._read_head(project_id)
            if head is not None and head.published_version > 0 and head.published_version != snap.version:
                self.refresh_async(project_id)
        return RuntimeLease(snap)

    def acquire_version(self, project_id: str, version: int) -> RuntimeLease:
        entry = self._entry(project_id)
        if entry.current is None:
            self._cold_compile(project_id, entry)
        assert entry.current is not None
        if int(version) == entry.current.version:
            return RuntimeLease(entry.current)
        with self._lock:
            hit = entry.recent.get(int(version))
        if hit is not None:
            return RuntimeLease(hit)
        found = self._versions.get_version(project_id, int(version))
        if found is None:
            raise ConfigVersionExpiredError()
        compiled = compile_project_config(
            project_id, int(version), found[1], deps=self._deps, source="snapshot"
        )
        self._remember(entry, compiled)
        return RuntimeLease(compiled)

    def install(self, compiled: CompiledProjectConfig) -> None:
        """发布进程提交后立即换引用（单次赋值）。"""
        entry = self._entry(compiled.project_id)
        with self._lock:
            self._remember(entry, compiled)
            entry.current = compiled
            entry.state, entry.error, entry.drift = "ok", None, False
            entry.backoff_s, entry.retry_at = 0.0, 0.0
            entry.last_check = self._clock()

    def refresh_async(self, project_id: str) -> None:
        """后台单飞编译 head 版本；失败保留旧快照并退避。"""
        entry = self._entry(project_id)
        with self._lock:
            if entry.building or self._clock() < entry.retry_at:
                return
            entry.building = True
            entry.state = "applying"
        threading.Thread(
            target=self._refresh, args=(project_id, entry), name=f"ib-cfg-refresh-{project_id}", daemon=True
        ).start()

    def refresh_now(self, project_id: str) -> None:
        """同步版刷新（后台线程与测试共用）。"""
        entry = self._entry(project_id)
        with self._lock:
            if entry.building:
                return
            entry.building = True
            entry.state = "applying"
        self._refresh(project_id, entry)

    def status(self, project_id: str) -> RuntimeStatus:
        entry = self._entry(project_id)
        head = self._read_head(project_id)
        applied = entry.current.version if entry.current is not None else -1
        return RuntimeStatus(
            applied_version=applied,
            head_version=head.published_version if head is not None else -1,
            state=entry.state,
            drift=entry.drift,
            last_error_code=entry.error,
        )

    def invalidate(self, project_id: str | None = None) -> None:
        """丢弃缓存（`reload_projects` 调用）：下一次 `acquire` 冷编译。"""
        with self._lock:
            if project_id is None:
                self._entries.clear()
            else:
                self._entries.pop(project_id, None)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #

    def _entry(self, project_id: str) -> _Entry:
        with self._lock:
            entry = self._entries.get(project_id)
            if entry is None:
                entry = self._entries[project_id] = _Entry()
            return entry

    def _read_head(self, project_id: str) -> HeadState | None:
        try:
            return self._versions.head(project_id)
        except Exception:  # noqa: BLE001 - head 不可读：保持当前版本，状态由 status() 体现
            return None

    def _remember(self, entry: _Entry, compiled: CompiledProjectConfig) -> None:
        with self._lock:
            entry.recent[compiled.version] = compiled
            entry.recent.move_to_end(compiled.version)
            while len(entry.recent) > self._keep:
                entry.recent.popitem(last=False)

    def _cold_compile(self, project_id: str, entry: _Entry) -> None:
        """冷启动：阻塞式编译。失败原样抛出（fail-closed）。"""
        with self._lock:
            if entry.current is not None:
                return
        head = self._versions.head(project_id)
        files: ConfigSnapshot = self._loader.load_files(project_id)
        source: Literal["files", "snapshot"] = "files"
        snapshot = files
        version = head.published_version
        drift = False
        if head.published_version > 0:
            found = self._versions.get_version(project_id, head.published_version)
            if found is not None:
                from ib.config.versioning import manifest_hash

                if manifest_hash(found[1]) != manifest_hash(files):
                    snapshot, source, drift = found[1], "snapshot", True
        compiled = compile_project_config(project_id, version, snapshot, deps=self._deps, source=source)
        with self._lock:
            if entry.current is None:
                entry.current = compiled
                self._remember(entry, compiled)
                entry.drift = drift
                entry.state, entry.error = "ok", None
                entry.last_check = self._clock()

    def _refresh(self, project_id: str, entry: _Entry) -> None:
        try:
            head = self._versions.head(project_id)
            ver = head.published_version
            if ver <= 0:
                return
            found = self._versions.get_version(project_id, ver)
            if found is None:
                raise ConfigVersionExpiredError()
            compiled = compile_project_config(project_id, ver, found[1], deps=self._deps, source="snapshot")
            with self._lock:
                self._remember(entry, compiled)
                if entry.current is None or compiled.version >= entry.current.version:
                    entry.current = compiled
                entry.state, entry.error, entry.drift = "ok", None, False
                entry.backoff_s, entry.retry_at = 0.0, 0.0
        except Exception as exc:  # noqa: BLE001 - 编译失败：旧快照继续服务
            with self._lock:
                entry.state = "apply_failed"
                entry.error = str(getattr(exc, "code", "") or type(exc).__name__)[:60]
                entry.backoff_s = min(_BACKOFF_MAX_S, entry.backoff_s * 2 if entry.backoff_s else _BACKOFF_START_S)
                entry.retry_at = self._clock() + entry.backoff_s
            try:
                from ib.observability import log_event

                log_event("runtime", "compile_failed", project_id=project_id, error_code=entry.error, level="ERROR")
            except Exception:  # noqa: BLE001
                pass
        finally:
            with self._lock:
                entry.building = False
