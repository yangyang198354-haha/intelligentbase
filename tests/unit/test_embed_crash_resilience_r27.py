"""REV-27 ib-embed SIGILL 排查后的两处加固：

* 语义路由范例装载失败后冷却一段时间再自动重试（原先永久穿透到进程重启）；
* ib-embed 启动后先在主线程预热一次推理。
"""

from __future__ import annotations

from ib.core import Scope
from ib.routing.semantic import SemanticRouter


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _scope(project_id: str = "New") -> Scope:
    return Scope(project_id=project_id)


def _router(state: dict, clock: _Clock, retry_s: float = 300.0) -> SemanticRouter:
    def embed(texts: list[str]) -> list[list[float]]:
        state["calls"] += 1
        if state["down"]:
            raise ConnectionError("ib-embed down")
        return [[1.0, 0.0] if "退货" in t else [0.0, 1.0] for t in texts]

    return SemanticRouter(
        embed_texts=embed,
        exemplars_provider=lambda pid: {"customer-service-agent": ["我想退货"], "kb-agent": ["制度规定"]},
        failure_retry_s=retry_s,
        clock=clock,
    )


def test_router_retries_after_cooldown_when_embed_recovers():
    state = {"calls": 0, "down": True}
    clock = _Clock()
    router = _router(state, clock)

    assert router.route("我想退货", scope=_scope()) is None  # 装载失败 → 穿透
    calls_after_failure = state["calls"]

    # 冷却期内：不再打远端，直接穿透
    state["down"] = False
    clock.now += 299
    assert router.route("我想退货", scope=_scope()) is None
    assert state["calls"] == calls_after_failure

    # 冷却期过后：自动重试并恢复语义路由
    clock.now += 2
    assert router.route("我想退货", scope=_scope()) == "customer-service-agent"
    assert state["calls"] > calls_after_failure


def test_router_failure_is_per_project_and_invalidate_clears_it():
    state = {"calls": 0, "down": True}
    clock = _Clock()
    router = _router(state, clock)
    assert router.route("我想退货", scope=_scope("A")) is None

    state["down"] = False
    # 另一个项目不受 A 的失败影响
    assert router.route("我想退货", scope=_scope("B")) == "customer-service-agent"
    # invalidate 立即清掉 A 的冷却
    router.invalidate("A")
    assert router.route("我想退货", scope=_scope("A")) == "customer-service-agent"


def test_ib_embed_startup_warmup_runs_inference_and_tolerates_failure(caplog):
    from ib_embed import server
    from ib_embed.config import load_config

    cfg = load_config({"IB_EMBED_MODEL_PATH": "/opt/bge-m3"})
    seen: list[list[str]] = []

    class _Ok:
        def embed(self, texts, *, batch_size, max_tokens):
            seen.append(list(texts))

    assert server._startup_warmup(_Ok(), cfg) is True
    assert seen == [list(server.WARMUP_TEXTS)]

    class _Broken:
        def embed(self, texts, *, batch_size, max_tokens):
            raise RuntimeError("boom")

    caplog.set_level("WARNING")
    assert server._startup_warmup(_Broken(), cfg) is False  # 不抛出
    assert any("warmup_failed" in r.getMessage() for r in caplog.records)
    assert not any("boom" in r.getMessage() for r in caplog.records)


def test_ib_embed_healthz_reports_warm_after_startup_warmup():
    from ib_embed.config import load_config
    from ib_embed.runtime import FakeRuntime
    from ib_embed.server import EmbedService

    cfg = load_config({"IB_EMBED_MODEL_PATH": "/opt/bge-m3", "IB_EMBED_MODEL_ID": "fake-bge-m3"})
    runtime = FakeRuntime()
    runtime.load()
    assert EmbedService(cfg, runtime).healthz().body["warm"] is False
    assert EmbedService(cfg, runtime, warm=True).healthz().body["warm"] is True
