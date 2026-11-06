"""[REV-29 / GROUP_D / 缺陷回流第 3 轮] 集成：DEF-R29-008 —— MCP supervisor 只在 ib-web 进程入口（build_application）启动，
ib-worker 路径（django.setup → apps.ready → build_deps，永不调用 build_application）不得出现 `ib-mcp-supervisor` 线程。

分层：integration（真实非离线装配 composition ↔ 真实 McpSupervisor ↔ 持久化 SQLite 台账 ↔ Django apps.ready / worker._setup_django）。
溯源：US-024（AC-024-01 周期探测归属于 ib-web）、US-025（AC-025-03 重启 ib-web 不阻塞）；module_design.md:866“supervisor 仅在 ib-web 进程内”。
成对原则（M-PM-001）：不启动的负例（worker 路径）与启动的正例（web 路径）同夹具成对；负例强度不低于缺陷原描述
（“ib-worker 进程里存在名为 ib-mcp-supervisor 的线程”）：这里断言整个进程内“新增的 ib-mcp* 线程数 = 0”且 supervisor 内部未持有线程。
不触网：套接字 connect / getaddrinfo / create_connection 打桩，尝试数必须为 0；不 monkeypatch 被测函数。
"""

from __future__ import annotations

import socket
import threading

import pytest

SUP = "ib-mcp-supervisor"


@pytest.fixture()
def net_spy(monkeypatch):
    attempts: list[str] = []

    def spy(name):
        def f(*a, **k):
            attempts.append(name)
            raise AssertionError(f"测试期间不得有网络尝试：{name}")
        return f

    monkeypatch.setattr(socket.socket, "connect", spy("connect"))
    monkeypatch.setattr(socket, "getaddrinfo", spy("getaddrinfo"))
    monkeypatch.setattr(socket, "create_connection", spy("create_connection"))
    yield attempts
    assert attempts == [], f"网络尝试 {attempts}"


def _raw(monkeypatch, tmp_path, **extra):
    from conftest import R13_ADMIN_PASSWORD, offline_raw

    for k, v in (("IB_ACCOUNT_BACKEND", "memory"), ("IB_AUTHZ_POLICY_MODULE", "ibweb.accounts.policy"), ("IB_DEFAULT_ADMIN_PASSWORD", R13_ADMIN_PASSWORD)):
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("IB_MCP_SECRET_KEY", raising=False)
    raw = offline_raw()
    raw.update(offline_mode=False, llm={"backend": "fake", "base_url": "https://api.deepseek.com/v1"}, ledger_backend="sqlite",
               project_registry_backend="memory", llm_key_backend="sqlite", ledger_path=str(tmp_path / "ledger.sqlite3"),
               web_governance_backend="memory")
    raw.update(extra)
    return raw


def _seed_unreachable_server(deps) -> None:
    """让 supervisor 若被启动就“有活可干”：台账里持久化一个已启用但不可达的 Server（.invalid，永不解析）。"""
    from ib.core.types import McpServer, McpServerLimits

    deps.mcp.stores.servers.create(McpServer("dead0", "d", "streamable_http", "https://dead0.invalid/mcp", "none", None, "shared", "platform", None,
                                             True, ("query_text",), "enabled", "up", None, "modern", "2026-07-28", True, None, None, 0,
                                             McpServerLimits(), "t", "a", "t", "a"))


def _mcp_threads(before: set) -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name.startswith("ib-mcp") and t.is_alive() and t.ident not in before]


def _sup_threads(before: set) -> list[threading.Thread]:
    return [t for t in _mcp_threads(before) if t.name == SUP]


@pytest.fixture()
def deps_pair(monkeypatch, tmp_path, django_ready, net_spy):
    """非离线 + MCP 启用的真实装配；yield (raw, before_idents, 已建 deps 列表)；teardown 一律 close 并确认无残留。"""
    from ibweb.composition import build_deps

    raw = _raw(monkeypatch, tmp_path)
    d0 = build_deps(raw, force=True)
    _seed_unreachable_server(d0)
    d0.close()
    before = {t.ident for t in threading.enumerate()}  # 按线程标识比较：前序用例可能遗留同名线程
    built: list = []
    yield raw, before, built
    for d in built:
        d.close()
    import time

    time.sleep(0.2)
    assert [t.name for t in _mcp_threads(before)] == [], "teardown 后不得有 ib-mcp* 线程残留"


def test_TC_INT_R29_1100_worker_path_build_deps_and_django_ready_starts_no_supervisor_thread_DEF_R29_008_AC_025_03(deps_pair):
    """负例（ib-worker 路径）：非离线 + MCP 启用，只走 build_deps，再走 worker 的 _setup_django → apps.ready 等价路径 ——
    进程内不存在名为 ib-mcp-supervisor 的线程（缺陷原描述），也没有 ib-mcp-probe / ib-mcp-listen-* 等任何新增 ib-mcp* 线程；supervisor 对象存在但未持有线程。"""
    from ibweb import worker
    from ibweb.composition import build_deps, get_deps

    raw, before, built = deps_pair
    d = build_deps(raw, force=True)
    built.append(d)
    # 前置：真实装配确实带了 supervisor（排除“根本没装配 MCP 所以自然没线程”的假通过）
    assert d.mcp is not None and d.mcp.supervisor is not None and type(d.mcp.transport).__name__ == "HttpMcpTransport"
    assert [s.server_id for s in d.mcp.stores.servers.list_all()] == ["dead0"]
    # 动作 1：只有 build_deps
    assert _sup_threads(before) == [] and _mcp_threads(before) == []
    # 动作 2：worker 入口的 Django 初始化（django.setup → IbWebConfig.ready，已装配则只记录）
    worker._setup_django()
    from django.apps import apps

    apps.get_app_config("ibweb").ready()
    assert get_deps(required=False) is d
    assert [t.name for t in _mcp_threads(before)] == [], "worker 路径不得启动任何 MCP 后台线程"
    assert d.mcp.supervisor._thread is None, "supervisor 未被 start()"
    # 给“若被启动则已起线程”的缺陷实现一个观察窗口（线程启动是同步的，这里只是防御式再采样）
    import time

    time.sleep(0.3)
    assert not any(t.name == SUP for t in threading.enumerate() if t.ident not in before)


def test_TC_INT_R29_1101_web_path_build_application_starts_exactly_one_supervisor_idempotent_and_close_stops_it_AC_025_03(deps_pair):
    """正例（ib-web 路径）：build_application → 恰好 1 个存活的 daemon ib-mcp-supervisor 线程；再调一次（同 deps）仍为 1（幂等）；
    close() 后线程退出、无 ib-mcp* 残留；启动非阻塞。"""
    import time

    from ibweb.composition import build_application, build_deps

    raw, before, built = deps_pair
    d = build_deps(raw, force=True)
    built.append(d)
    assert _sup_threads(before) == []  # 装配后、build_application 前：0
    t0 = time.monotonic()
    app = build_application(d)
    assert time.monotonic() - t0 < 20 and callable(app)
    ths = _sup_threads(before)
    assert len(ths) == 1 and ths[0].daemon is True and d.mcp.supervisor._thread is ths[0]
    build_application(d)  # 幂等
    assert len(_sup_threads(before)) == 1 and _sup_threads(before)[0] is ths[0]
    d.close()
    ths[0].join(timeout=5)
    time.sleep(0.2)
    assert not ths[0].is_alive() and _mcp_threads(before) == [], "close() 后线程退出且无 ib-mcp* 残留"


def test_TC_INT_R29_1102_same_deps_pair_worker_then_web_zero_then_one_AC_024_01(deps_pair):
    """成对（同一份 deps）：先走 worker 路径（0 个线程），再走 web 路径（恰好 1 个）——证明区分点在入口而非装配内容。"""
    from ibweb import worker
    from ibweb.composition import build_application, build_deps

    raw, before, built = deps_pair
    d = build_deps(raw, force=True)
    built.append(d)
    worker._setup_django()
    assert _sup_threads(before) == []
    build_application(d)
    assert len(_sup_threads(before)) == 1


def test_TC_INT_R29_1103_start_mcp_supervisor_true_and_idempotent_on_enabled_deps_AC_024_01(deps_pair):
    """start_mcp_supervisor 的返回值契约：MCP 启用 ⇒ True（可重复调用，线程恒为 1）；deps 为 None / 无 mcp 属性 ⇒ False，不抛。"""
    from ibweb.composition import build_deps, start_mcp_supervisor

    raw, before, built = deps_pair
    d = build_deps(raw, force=True)
    built.append(d)
    assert start_mcp_supervisor(d) is True and start_mcp_supervisor(d) is True
    assert len(_sup_threads(before)) == 1
    assert start_mcp_supervisor(None) is False and start_mcp_supervisor(object()) is False
    assert len(_sup_threads(before)) == 1


def test_TC_INT_R29_1104_offline_assembly_returns_false_and_no_thread_even_via_build_application_AC_025_01(monkeypatch, tmp_path, django_ready, net_spy):
    """边界（离线）：离线装配 deps.mcp 无 supervisor ⇒ start_mcp_supervisor 返回 False，build_application 后也无 ib-mcp* 线程。"""
    from conftest import offline_raw
    from ibweb.composition import build_application, build_deps, start_mcp_supervisor

    before = {t.ident for t in threading.enumerate()}
    d = build_deps(offline_raw(), force=True)
    try:
        assert getattr(getattr(d.mcp, "supervisor", None), "start", None) is None, "离线装配不带 supervisor"
        assert start_mcp_supervisor(d) is False
        build_application(d)
        assert _mcp_threads(before) == []
    finally:
        d.close()


def test_TC_INT_R29_1105_mcp_disabled_switch_returns_false_and_no_thread_AC_025_01(monkeypatch, tmp_path, django_ready, net_spy):
    """边界（IB_MCP_ENABLED=0，dict 配置源下即 raw 键 mcp_enabled=False）：非离线装配但总开关关闭 ⇒ deps.mcp 为 None、
    start_mcp_supervisor 返回 False、build_application 后无线程；同样的非离线装配开关打开时才有线程（成对，防“非离线装配本来就不起线程”的假通过）。"""
    from ibweb.composition import build_application, build_deps, start_mcp_supervisor

    before = {t.ident for t in threading.enumerate()}
    d = build_deps(_raw(monkeypatch, tmp_path, mcp_enabled=False), force=True)
    try:
        assert d.mcp is None, "总开关关闭 ⇒ MCP 运行时不装配"
        assert start_mcp_supervisor(d) is False
        build_application(d)
        assert _mcp_threads(before) == []
    finally:
        d.close()
    (tmp_path / "on").mkdir()
    d2 = build_deps(_raw(monkeypatch, tmp_path / "on"), force=True)
    try:
        assert d2.mcp is not None and d2.mcp.supervisor is not None
        build_application(d2)
        assert len(_sup_threads(before)) == 1
    finally:
        d2.close()
