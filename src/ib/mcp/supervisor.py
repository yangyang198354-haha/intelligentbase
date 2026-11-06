# MOD-R29-17 / implements IFC-R29-170 / depends MOD-R29-01, 12, 14
"""supervisor：ib-web 进程内 daemon 线程（健康探测、周期复核、变更监听、去抖刷新）。

契约：线程名 `ib-mcp-supervisor`；探测池 `ib-mcp-probe`（2 线程）；监听线程 `ib-mcp-listen-<server_id>`
（≤ listener_max，仅 modern 且 supports_list_changed）；任何异常只写 WARN 与系统审计，不外抛；
`health_interval_s=0` ⇒ 不做健康探测，`revalidate_interval_s=0` ⇒ 不复核。失败**永不影响调用路径**的正确性。
"""

from __future__ import annotations

import logging
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

from ib.core.ports import McpStores, SecretCipher
from ib.core.types import McpGovernance, McpServer

from .auditing import audit_record, safe_record
from .catalog import McpCatalogService, VerificationFailed, discovery_credential
from .client import McpClient, McpClientError, McpTarget
from .runtime import McpBreaker

__all__ = ["McpSupervisor"]

_log = logging.getLogger("ib.mcp")
_FMT = "%Y-%m-%dT%H:%M:%SZ"
_DEBOUNCE_S = 5.0
_BACKOFF_MAX_S = 60.0


def _iso() -> str:
    return datetime.now(timezone.utc).strftime(_FMT)


class McpSupervisor:
    def __init__(
        self,
        *,
        stores: McpStores,
        catalog: McpCatalogService,
        client: McpClient,
        cipher: SecretCipher,
        breaker: McpBreaker,
        gov_reader: Callable[[], McpGovernance],
        audit: Any,
        clock: Callable[[], float] = time.monotonic,
        tick_s: float = 5.0,
        inline: bool = False,
    ) -> None:
        self._s = stores
        self._catalog = catalog
        self._client = client
        self._cipher = cipher
        self._breaker = breaker
        self._gov = gov_reader
        self._audit = audit
        self._clock = clock
        self._tick_s = float(tick_s)
        self._inline = bool(inline)  # 测试：任务就地同步执行
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._pool: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()
        self._last_health: dict[str, float] = {}
        self._last_reval: dict[str, float] = {}
        self._dirty: dict[str, float] = {}
        self._inflight: set[str] = set()
        self._listeners: dict[str, tuple[threading.Thread, threading.Event]] = {}

    def __repr__(self) -> str:
        return "McpSupervisor()"

    # -- 生命周期 ----------------------------------------------------------- #
    def start(self, *, initial_delay_s: float | None = None) -> None:
        """非阻塞；已启动再调用为 no-op。"""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ib-mcp-probe")
            delay = random.uniform(5.0, 30.0) if initial_delay_s is None else float(initial_delay_s)
            self._thread = threading.Thread(
                target=self._run, args=(delay,), name="ib-mcp-supervisor", daemon=True
            )
            self._thread.start()

    def stop(self, *, timeout_s: float = 2.0) -> None:
        """Deps.close() 调用。"""
        self._stop.set()
        with self._lock:
            th, pool = self._thread, self._pool
            listeners = list(self._listeners.values())
            self._listeners = {}
        for _t, ev in listeners:
            ev.set()  # 监听线程的 watcher / client.listen 据此关闭监听流（DEF-R29-003）
        if th is not None and th.is_alive():
            th.join(timeout=max(0.0, timeout_s))
        end = time.monotonic() + max(0.0, timeout_s)
        for lt, _ev in listeners:  # 带超时 join 监听线程，避免线程残留（CR-008）
            if lt.is_alive():
                lt.join(timeout=max(0.0, end - time.monotonic()))
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)

    def mark_dirty(self, server_id: str) -> None:
        """监听回调 / 管理员触发；5 秒去抖后 refresh。"""
        with self._lock:
            self._dirty[server_id] = self._clock()

    # -- 主循环 ------------------------------------------------------------- #
    def _run(self, delay: float) -> None:
        if self._stop.wait(max(0.0, delay)):
            return
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # noqa: BLE001 - 永不外抛
                _log.warning("mcp supervisor tick failed")
            if self._stop.wait(self._tick_s):
                return

    def tick(self) -> None:
        """一次调度（公开便于离线测试直接驱动）。"""
        try:
            gov = self._gov()
            servers = [s for s in self._s.servers.list_all() if s.admin_state == "enabled"]
        except Exception:  # noqa: BLE001
            _log.warning("mcp supervisor store unavailable")
            return
        now = self._clock()
        live = {s.server_id for s in servers}
        for s in servers:
            sid = s.server_id
            if gov.health_interval_s > 0 and now - self._last_health.get(sid, -1e9) >= gov.health_interval_s:
                self._last_health[sid] = now
                self._submit(("health", sid), lambda s=s: self._probe(s))
            if gov.revalidate_interval_s > 0 and now - self._last_reval.get(sid, -1e9) >= gov.revalidate_interval_s:
                self._last_reval[sid] = now
                self._submit(("reval", sid), lambda sid=sid: self._refresh(sid))
        with self._lock:
            due = [sid for sid, t in self._dirty.items() if now - t >= _DEBOUNCE_S]
            for sid in due:
                self._dirty.pop(sid, None)
        for sid in due:
            if sid in live:
                self._submit(("reval", sid), lambda sid=sid: self._refresh(sid))
        self._sync_listeners(servers, gov)

    def _submit(self, key: tuple[str, str], fn: Callable[[], None]) -> None:
        with self._lock:
            if key in self._inflight:
                return
            self._inflight.add(key)

        def _job() -> None:
            try:
                fn()
            except Exception:  # noqa: BLE001
                _log.warning("mcp supervisor job failed kind=%s server=%s", key[0], key[1])
            finally:
                with self._lock:
                    self._inflight.discard(key)

        if self._inline or self._pool is None:
            _job()
        else:
            try:
                self._pool.submit(_job)
            except RuntimeError:  # 池已关闭
                with self._lock:
                    self._inflight.discard(key)

    # -- 任务 -------------------------------------------------------------- #
    def _probe(self, s: McpServer) -> None:
        gov = self._gov()
        cred, miss = discovery_credential(self._s, self._cipher, s)
        prev = s.health
        if miss is not None:
            health = "down"
        else:
            target = McpTarget(s.server_id, s.endpoint_url, s.auth_kind, s.auth_header_name, s.protocol_era, s.protocol_version)
            res = self._client.probe(target, cred, deadline=time.monotonic() + max(1, gov.discover_timeout_s))
            health = "up" if res.ok else "down"
        self._s.servers.record_probe(s.server_id, health=health, checked_at=_iso())  # type: ignore[arg-type]
        if health != prev:
            safe_record(
                self._audit,
                audit_record(_iso, action="health.change", actor="system:mcp-supervisor", server_id=s.server_id, reason=f"{prev}->{health}"),
            )

    def _refresh(self, server_id: str) -> None:
        try:
            self._catalog.refresh(server_id, actor="system:mcp-supervisor")
        except VerificationFailed as exc:
            safe_record(
                self._audit,
                audit_record(_iso, action="server.revalidate", actor="system:mcp-supervisor", server_id=server_id, outcome="failed", reason=exc.category),
            )

    # -- 监听 -------------------------------------------------------------- #
    def _sync_listeners(self, servers: list[McpServer], gov: McpGovernance) -> None:
        want = [s for s in servers if s.protocol_era == "modern" and s.supports_list_changed]
        want_ids = {s.server_id for s in want}
        with self._lock:
            for sid in [k for k in self._listeners if k not in want_ids or not self._listeners[k][0].is_alive()]:
                th, ev = self._listeners.pop(sid)
                ev.set()
            running = len(self._listeners)
        if self._inline or gov.listener_max <= 0:
            return
        for s in want:
            if running >= gov.listener_max:
                break
            with self._lock:
                if s.server_id in self._listeners:
                    continue
                ev = threading.Event()
                th = threading.Thread(
                    target=self._listen_loop, args=(s.server_id, ev), name=f"ib-mcp-listen-{s.server_id}", daemon=True
                )
                self._listeners[s.server_id] = (th, ev)
            th.start()
            running += 1

    def _listen_loop(self, server_id: str, ev: threading.Event) -> None:
        backoff = 1.0
        while not self._stop.is_set() and not ev.is_set():
            try:
                s = self._s.servers.get(server_id)
                if s is None or s.admin_state != "enabled":
                    return
                cred, miss = discovery_credential(self._s, self._cipher, s)
                if miss is not None:
                    raise McpClientError("auth_failed")
                target = McpTarget(s.server_id, s.endpoint_url, s.auth_kind, s.auth_header_name, s.protocol_era, s.protocol_version)
                both = threading.Event()

                def _watch() -> None:  # 任一停止信号 ⇒ 结束监听流
                    while not (self._stop.is_set() or ev.is_set() or both.is_set()):
                        time.sleep(0.5)
                    both.set()

                threading.Thread(target=_watch, daemon=True, name=f"ib-mcp-listen-watch-{server_id}").start()
                try:
                    self._client.listen(target, cred, on_changed=lambda sid=server_id: self.mark_dirty(sid), stop=both)
                finally:
                    both.set()  # 结束监听 ⇒ 释放 watcher
                backoff = 1.0
            except Exception:  # noqa: BLE001
                _log.warning("mcp listener error server=%s", server_id)
            if self._stop.wait(backoff) or ev.is_set():
                return
            backoff = min(_BACKOFF_MAX_S, backoff * 2)
