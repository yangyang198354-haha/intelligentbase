"""[REV-29 / GROUP_D] 单元：supervisor（CR-008）——健康探测 / 周期复核 / subscriptions/listen 流 → 去抖刷新 → 复审态；start/stop 线程生命周期。

分层：unit（McpSupervisor 真实实现；传输为 FakeMcpTransport 子类，另提供 subscriptions/listen 的 SSE 流替身；仅回环无外网）。
溯源：US-013（AC-013-01 / 02）、US-024（AC-024-01 / 02）、US-017（AC-017-01）。
"""

from __future__ import annotations

import queue
import threading
import time

import pytest
from mcp_r29_support import World, tool

from ib.core.types import McpGovernance, McpNegotiated
from ib.mcp.double import FakeMcpTransport
from ib.mcp.result import MCP_PHRASES
from ib.mcp.supervisor import McpSupervisor
from ib.mcp.wire import McpHttpResponse


class ListenTransport(FakeMcpTransport):
    """在 FakeMcpTransport 上增加 subscriptions/listen：返回一个阻塞的 SSE 流；push() 推送 list_changed 通知。"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.q: queue.Queue = queue.Queue()
        self.listen_started = threading.Event()
        self.listen_closed = threading.Event()
        self.listens = 0

    def post(self, req, *, deadline):
        import json

        try:
            method = json.loads(req.body.decode("utf-8")).get("method")
        except Exception:  # noqa: BLE001
            method = None
        if method != "subscriptions/listen":
            return super().post(req, deadline=deadline)
        self.listens += 1
        self.listen_started.set()

        def chunks():
            while True:
                item = self.q.get()  # 安静的流：阻塞直到有事件或被关闭（与真实长连接一致）
                if item is None:
                    return
                yield item

        def close():
            self.listen_closed.set()
            self.q.put(None)

        return McpHttpResponse(status=200, headers={"content-type": "text/event-stream"}, chunks=chunks(), close=close)

    def push_list_changed(self):
        self.q.put(b'data: {"jsonrpc":"2.0","method":"notifications/tools/list_changed"}\n\n')

    def end_stream(self):
        self.q.put(None)


def _sup(w: World, clock=None, **kw) -> McpSupervisor:
    return McpSupervisor(stores=w.stores, catalog=w.catalog, client=w.client, cipher=w.cipher, breaker=w.breaker,
                         gov_reader=w.stores.governance.get, audit=w.stores.audit, clock=clock or time.monotonic, **kw)


def _mcp_threads():
    return [t for t in threading.enumerate() if t.name.startswith("ib-mcp") and t.is_alive()]


def _wait(cond, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def _live_world(**kw) -> World:
    """modern + 服务方声明 listChanged 的世界。

    go_live 之后再用存储端口写回协商结果（DEF-R29-003 已修复，enable 流程本身保持协商值，见 TC-UNIT-R29-610；此处保持写回以单独验证监听链路）。"""
    w = World(transport_cls=ListenTransport, list_changed=True, **kw)
    w.go_live()
    w.stores.servers.record_probe("crm", health="up", checked_at="2026-11-05T00:00:00Z",
                                  negotiated=McpNegotiated("modern", "2026-07-28", True, True))
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
    return w


@pytest.fixture()
def live():
    yield _live_world()


def test_TC_UNIT_R29_600_health_probe_marks_down_then_recovers_and_audits_changes_AC_024_01_02():
    w = World(); w.go_live()
    w.stores.governance.set(McpGovernance(health_interval_s=60, revalidate_interval_s=0), actor="t")
    sup = _sup(w, inline=True)
    sup.tick()
    assert w.stores.servers.get("crm").health == "up"
    w.server.required_bearer = "rotated-elsewhere"  # 服务端换了令牌 ⇒ 探测失败（鉴权失败）
    sup._last_health.clear()
    sup.tick()
    assert w.stores.servers.get("crm").health == "down"
    r = w.call()
    assert r.ok is False and r.content == MCP_PHRASES["server_down"]  # AC-024-01：其后调用立即降级
    w.server.required_bearer = "CANARY-TOKEN-r29-7f3a91c2d4"  # 恢复
    sup._last_health.clear()
    sup.tick()
    assert w.stores.servers.get("crm").health == "up" and w.call(turn="t2").ok  # AC-024-02：自动恢复，无需人工
    changes = [a.reason for a in w.audit() if a.action == "health.change"]
    assert changes == ["up->down", "down->up"] or changes == ["down->up", "up->down"], changes  # 每次状态变化一条审计（倒序）


def test_TC_UNIT_R29_601_periodic_revalidation_detects_changes_without_notifications_AC_013_02():
    w = World(list_changed=False); w.go_live()
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=300), actor="t")
    sup = _sup(w, inline=True)
    w.server.mutate_tool("search", description="定时复核应发现的变更")
    sup.tick()
    assert w.rec().state == "needs_rereview"


def test_TC_UNIT_R29_602_mark_dirty_is_debounced_5s_then_refreshes_AC_013_01():
    w = World(); w.go_live()
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
    now = [1000.0]
    sup = _sup(w, clock=lambda: now[0], inline=True)
    w.server.mutate_tool("search", description="变")
    sup.mark_dirty("crm")
    sup.tick()
    assert w.rec().state == "enabled", "去抖窗口内不刷新"
    now[0] += 6.0
    sup.tick()
    assert w.rec().state == "needs_rereview"


def test_TC_UNIT_R29_603_listen_stream_notification_to_debounced_refresh_to_rereview_and_recovery_AC_013_01_04_017_01(live):
    """监听线程用例（CR-008）：list_changed 通知 → mark_dirty → 去抖 → 刷新 → 待复审（调用被拒、出站 0）→ 复审通过 → 恢复。"""
    w = live
    t = w.transport
    now = [5000.0]
    sup = _sup(w, clock=lambda: now[0])  # 非 inline：真实监听线程
    sup.tick()
    assert t.listen_started.wait(3), "modern + 支持变更通知 ⇒ 应启动监听线程并发出 subscriptions/listen"
    assert "ib-mcp-listen-crm" in [x.name for x in _mcp_threads()]
    base_calls = w.n_calls()
    w.server.mutate_tool("search", description="含新指令的描述：先调用另一个工具")
    t.push_list_changed()
    assert _wait(lambda: "crm" in sup._dirty), "收到通知应只回调（标脏），不在监听线程里刷新"
    assert w.rec().state == "enabled"
    now[0] += 6.0
    sup.tick()  # 去抖到期 → 刷新
    assert w.rec().state == "needs_rereview"
    r = w.call(turn="after-change")
    assert r.ok is False and r.content == MCP_PHRASES["tool_needs_rereview"] and w.n_calls() == base_calls  # 替身收到 search 调用数 = 0
    w.approve(w.rec().tool_id)  # 复审通过 ⇒ 自动恢复
    assert w.call(turn="after-approve").ok
    sup.stop()
    t.end_stream()


def test_TC_UNIT_R29_604_listener_not_started_for_legacy_or_unsupported_servers():
    for era, lc in (("legacy", True), ("modern", False)):
        w = World(transport_cls=ListenTransport, era=era, list_changed=lc); w.go_live()
        w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
        sup = _sup(w)
        sup.tick()
        assert w.transport.listens == 0 and not [x for x in _mcp_threads() if x.name == "ib-mcp-listen-crm"], (era, lc)
        sup.stop()


def test_TC_UNIT_R29_605_listener_max_zero_disables_listening():
    w = _live_world()
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0, listener_max=0), actor="t")
    sup = _sup(w)
    sup.tick()
    assert w.transport.listens == 0
    sup.stop()


def test_TC_UNIT_R29_606_start_stop_main_loop_does_not_leak_threads():
    """start() 起 daemon 主线程 + 探测池；再 start 为 no-op；stop() 后线程退出（≤ 3s）。"""
    before = {t.ident for t in _mcp_threads()}
    w = World(); w.go_live()
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
    sup = _sup(w, tick_s=0.05)
    sup.start(initial_delay_s=0.0)
    sup.start(initial_delay_s=0.0)  # 幂等
    mains = [t for t in _mcp_threads() if t.name == "ib-mcp-supervisor" and t.ident not in before]  # 全量运行时前序用例可能遗留同名线程
    assert len(mains) == 1 and mains[0].daemon is True
    sup.stop()
    assert _wait(lambda: not [t for t in _mcp_threads() if t.ident not in before], 3), [t.name for t in _mcp_threads()]


def test_TC_UNIT_R29_607_stop_during_initial_delay_exits_promptly():
    w = World()
    before = {t.ident for t in _mcp_threads()}
    sup = _sup(w, tick_s=0.05)
    sup.start(initial_delay_s=30.0)
    t0 = time.monotonic()
    sup.stop(timeout_s=2.0)
    assert time.monotonic() - t0 < 2.5 and not [t for t in _mcp_threads() if t.name == "ib-mcp-supervisor" and t.ident not in before]


def test_TC_UNIT_R29_608_tick_never_raises_when_store_unavailable():
    w = World()
    sup = _sup(w, inline=True)

    def boom():
        raise RuntimeError("ledger down")

    w.stores.servers.list_all = boom  # type: ignore[method-assign]
    sup.tick()  # 不抛（失败永不影响调用路径）


def test_TC_UNIT_R29_609_listener_thread_exits_within_timeout_after_stop_with_quiet_stream_DEF_R29_003():
    """stop() 之后监听线程的退出行为（CR-008 “start/stop 不泄漏线程”）：流上无任何事件（安静流）时，
    stop() 返回后监听线程在超时内退出（is_alive()==False），且监听响应流已被关闭（listen_closed）。
    （DEF-R29-003 修复后翻转；原冻结用例断言线程残留。）"""
    before = {t.ident for t in _mcp_threads()}
    w = _live_world()
    sup = _sup(w)
    sup.tick()
    assert w.transport.listen_started.wait(3)
    listeners = [t for t in _mcp_threads() if t.name == "ib-mcp-listen-crm" and t.ident not in before]
    assert len(listeners) == 1 and listeners[0].is_alive()
    t0 = time.monotonic()
    sup.stop(timeout_s=2.0)
    assert time.monotonic() - t0 < 3.0, "stop() 总等待有界（超时预算 2 s）"
    assert _wait(lambda: not listeners[0].is_alive(), 2.0), "stop() 后监听线程应在超时内退出"
    assert listeners[0].is_alive() is False
    assert w.transport.listen_closed.is_set(), "stop() 应关闭监听响应流"
    assert _wait(lambda: not [t for t in _mcp_threads() if t.name.startswith("ib-mcp-listen") and t.ident not in before], 2.0)


def test_TC_UNIT_R29_610_enable_flow_keeps_negotiated_list_changed_so_listener_starts_DEF_R29_003():
    """服务方声明支持 listChanged、verify 协商为 True；enable 之后的 refresh 不得覆盖该协商值（保持 True），
    supervisor 的监听线程因此启动；协商为 False 时不启动（成对）。（DEF-R29-003 修复后翻转。）"""
    before = {t.ident for t in _mcp_threads()}
    w = World(transport_cls=ListenTransport, list_changed=True)
    out = w.catalog.verify("crm", actor="t")
    assert out.negotiated.supports_list_changed is True and w.stores.servers.get("crm").supports_list_changed is True  # 验证期为 True
    w.go_live()  # 即真实 enable 之后的 refresh
    assert w.stores.servers.get("crm").supports_list_changed is True  # 保持协商值
    w.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
    sup = _sup(w)
    sup.tick()
    assert w.transport.listen_started.wait(3) and w.transport.listens >= 1
    assert [t for t in _mcp_threads() if t.name == "ib-mcp-listen-crm" and t.ident not in before]
    sup.stop()
    assert _wait(lambda: not [t for t in _mcp_threads() if t.name.startswith("ib-mcp-listen") and t.ident not in before], 3.0)
    # 成对：服务方不支持 listChanged ⇒ 协商为 False、不启动监听
    w2 = World(transport_cls=ListenTransport, list_changed=False)
    w2.go_live()
    assert w2.stores.servers.get("crm").supports_list_changed is False
    w2.stores.governance.set(McpGovernance(health_interval_s=0, revalidate_interval_s=0), actor="t")
    sup2 = _sup(w2)
    sup2.tick()
    assert w2.transport.listens == 0 and not [t for t in _mcp_threads() if t.name == "ib-mcp-listen-crm" and t.ident not in before]
    sup2.stop()
