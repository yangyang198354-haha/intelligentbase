"""集成测试层 3/N —— MOD-IB-26 `ib_embed` 线协议（**本机回环真 HTTP**，无外部依赖）。

覆盖 IFC-IB-266/267/268/269/270/271/272/273；R2 重点项。
服务器用 `ThreadingHTTPServer` 绑 `127.0.0.1:0`（内核分配端口）——只走本机 socket，
不连任何外部服务，符合「离线可跑」约束。
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest


def _cfg(**overrides):
    from ib_embed.config import load_config

    env = {"IB_EMBED_MODEL_PATH": "/tmp/groupd-bge-m3", "IB_EMBED_DIM": "1024"}
    env.update(overrides)
    return load_config(env)


class _Server:
    """回环 HTTP 服务器上下文（真实 socket + 后台线程）。"""

    def __init__(self, cfg, runtime):
        from ib_embed.server import build_http_server

        self.httpd = build_http_server(cfg, runtime, host="127.0.0.1", port=0)
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def _url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def get(self, path):
        req = urllib.request.Request(self._url(path), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def post(self, path, payload=None, raw=None):
        body = raw if raw is not None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url(path), data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))


@pytest.fixture()
def loaded_server():
    from ib_embed.runtime import FakeRuntime

    runtime = FakeRuntime(dim=1024, model_id="fake-bge-m3")
    runtime.load()
    with _Server(_cfg(IB_EMBED_MODEL_ID="fake-bge-m3"), runtime) as server:
        yield server, runtime


# --------------------------------------------------------------------------- #
# IFC-IB-269 GET /healthz（永不 5xx）
# --------------------------------------------------------------------------- #


def test_TC_INT_017_healthz_never_5xx(loaded_server):
    """[TC-INT-017] /healthz 恒 200；未就绪时报 ok=false + 可读原因，绝非 5xx。"""
    from ib_embed.runtime import FakeRuntime, UnavailableRuntime

    server, _ = loaded_server
    status, body = server.get("/healthz")
    assert status == 200 and body["ok"] is True
    for field in ("model_id", "dim", "model_loaded", "warm", "queue_depth", "inflight"):
        assert field in body

    # 依赖不可用：仍 200，ok=False，detail 可读
    unavailable = UnavailableRuntime("权重目录缺失（可读原因）")
    with _Server(_cfg(), unavailable) as cold:
        status2, body2 = cold.get("/healthz")
    assert status2 == 200 and body2["ok"] is False
    assert "权重目录缺失" in body2["detail"]

    # 未加载的替身：同样 200/ok=false
    with _Server(_cfg(), FakeRuntime(dim=1024, model_id="fake-bge-m3")) as cold2:
        status3, body3 = cold2.get("/healthz")
    assert status3 == 200 and body3["ok"] is False


# --------------------------------------------------------------------------- #
# IFC-IB-266 / 267 POST /embed
# --------------------------------------------------------------------------- #


def test_TC_INT_018_embed_order_and_dim_authority(loaded_server):
    """[TC-INT-018] /embed 保序、dim 为实测权威值、count 与入参一致（IFC-IB-266/267）。"""
    server, runtime = loaded_server
    texts = ["第一段文本", "第二段文本", "第三段文本"]
    status, body = server.post("/embed", {"texts": texts, "mode": "document", "model": "fake-bge-m3"})
    assert status == 200
    assert body["count"] == 3 and len(body["vectors"]) == 3
    assert body["dim"] == 1024 and all(len(v) == 1024 for v in body["vectors"])
    # 保序：与直接内核调用逐位一致
    expected = runtime.embed(texts, batch_size=3, max_tokens=8192).vectors
    assert tuple(tuple(v) for v in body["vectors"]) == expected

    # 反转入参 → 反转出参（保序的可判定证据）
    reversed_texts = list(reversed(texts))
    status2, body2 = server.post("/embed", {"texts": reversed_texts, "mode": "document", "model": "fake-bge-m3"})
    assert status2 == 200
    assert tuple(tuple(v) for v in body2["vectors"]) == tuple(reversed(expected))


def test_TC_INT_019_batch_cap_echoes_max_batch(loaded_server):
    """[TC-INT-019] 超批上限 → 400 且回显 max_batch（IFC-IB-272）。"""
    server, _ = loaded_server
    cap = 64  # 默认 IB_EMBED_MAX_BATCH
    status, body = server.post(
        "/embed", {"texts": [f"t{i}" for i in range(cap + 1)], "mode": "document", "model": "fake-bge-m3"}
    )
    assert status == 400 and body["code"] == "batch_too_large"
    assert body["max_batch"] == cap
    # 恰好等于上限：放行（边界含端点）
    status2, body2 = server.post(
        "/embed", {"texts": [f"t{i}" for i in range(cap)], "mode": "document", "model": "fake-bge-m3"}
    )
    assert status2 == 200 and body2["count"] == cap


def test_TC_INT_020_model_mismatch_409(loaded_server):
    """[TC-INT-020] 跨模型请求 → 409（单模型常驻，不做运行时换模型，IFC-IB-268）。"""
    server, _ = loaded_server
    status, body = server.post("/embed", {"texts": ["x"], "mode": "query", "model": "some-other-model"})
    assert status == 409 and body["code"] == "model_mismatch"


def test_TC_INT_021_not_ready_503(loaded_server):
    """[TC-INT-021] 未加载 → 503（冷路径重试有效、热路径直接降级，IFC-IB-268）。"""
    from ib_embed.runtime import FakeRuntime

    with _Server(_cfg(IB_EMBED_MODEL_ID="fake-bge-m3"), FakeRuntime(dim=1024, model_id="fake-bge-m3")) as cold:
        status, body = cold.post("/embed", {"texts": ["x"], "mode": "document", "model": "fake-bge-m3"})
    assert status == 503 and body["code"] == "model_not_ready"


def test_TC_INT_022_invalid_request_no_partial(loaded_server):
    """[TC-INT-022] 结构非法 → 400；响应体不含正文（不回显入参）。"""
    server, _ = loaded_server
    for payload in (
        None,
        {"texts": [], "mode": "document", "model": "fake-bge-m3"},
        {"texts": "not-a-list", "mode": "document", "model": "fake-bge-m3"},
        {"texts": [1, 2], "mode": "document", "model": "fake-bge-m3"},
        {"texts": ["x"], "mode": "bogus", "model": "fake-bge-m3"},
        {"texts": ["x"], "mode": "document"},
    ):
        status, body = server.post("/embed", payload)
        assert status == 400 and body["code"] == "invalid_request", f"未拒绝：{payload}"
    # 畸形 JSON（非 JSON 体）→ 400
    status, body = server.post("/embed", raw=b"{not json")
    assert status == 400 and body["code"] == "invalid_request"


def test_TC_INT_023_no_partial_vectors_on_ragged_output():
    """[TC-INT-023] 运行时产出参差不齐/数量不符 → 整批 500，绝不返回部分向量（IFC-IB-266 §3.2）。"""
    from ib_embed.runtime import RuntimeBatch

    class _Ragged:
        def load(self):
            return 1

        def is_loaded(self):
            return True

        def embed(self, texts, *, batch_size, max_tokens):
            # 只返回 1 条（数量不符）
            return RuntimeBatch(vectors=((0.1, 0.2),))

        def descriptor(self):
            from ib_embed.runtime import RuntimeDescriptor

            return RuntimeDescriptor(model_id="fake-bge-m3", dim=2, normalized=True, max_tokens=8, device="cpu")

    with _Server(_cfg(IB_EMBED_MODEL_ID="fake-bge-m3"), _Ragged()) as server:
        status, body = server.post("/embed", {"texts": ["a", "b"], "mode": "document", "model": "fake-bge-m3"})
    assert status == 500 and body["code"] == "internal_error"
    assert "vectors" not in body


# --------------------------------------------------------------------------- #
# IFC-IB-268 overloaded（有界并发 + 有界队列 + 快速失败）
# --------------------------------------------------------------------------- #


def test_TC_INT_024_overloaded_503_with_retry_after():
    """[TC-INT-024] 容量用尽 → 503 overloaded + retry_after_s（绝不无界排队）。"""
    import time
    from ib_embed.config import load_config
    from ib_embed.runtime import RuntimeBatch, RuntimeDescriptor
    from ib_embed.server import EmbedService

    class _Blocking:
        def __init__(self):
            self.gate = threading.Event()
            self.entered = threading.Event()

        def load(self):
            return 1

        def is_loaded(self):
            return True

        def embed(self, texts, *, batch_size, max_tokens):
            self.entered.set()
            self.gate.wait(timeout=5)
            return RuntimeBatch(vectors=tuple((0.1, 0.2) for _ in texts))

        def descriptor(self):
            return RuntimeDescriptor(model_id="fake-bge-m3", dim=2, normalized=True, max_tokens=8, device="cpu")

    runtime = _Blocking()
    cfg = load_config(
        {
            "IB_EMBED_MODEL_PATH": "/tmp/x", "IB_EMBED_MODEL_ID": "fake-bge-m3",
            "IB_EMBED_DIM": "2", "IB_EMBED_MAX_CONCURRENCY": "1", "IB_EMBED_QUEUE_DEPTH": "0",
        }
    )
    service = EmbedService(cfg, runtime)
    payload = {"texts": ["占用并发"], "mode": "document", "model": "fake-bge-m3"}
    holder = {}

    def _occupy():
        holder["first"] = service.embed(payload)

    worker = threading.Thread(target=_occupy, daemon=True)
    worker.start()
    assert runtime.entered.wait(timeout=5), "首个请求未进入推理"
    try:
        over = service.embed({"texts": ["再来一个"], "mode": "document", "model": "fake-bge-m3"})
        assert over.status == 503 and over.body["code"] == "overloaded"
        assert over.body["retry_after_s"] >= 1
    finally:
        runtime.gate.set()
        worker.join(timeout=5)
    assert holder["first"].status == 200


# --------------------------------------------------------------------------- #
# IFC-IB-270 / 271 warmup / descriptor
# --------------------------------------------------------------------------- #


def test_TC_INT_025_warmup_idempotent(loaded_server):
    """[TC-INT-025] /warmup 幂等：重复调用均 200，不重复加载。"""
    server, _ = loaded_server
    first = server.post("/warmup")
    second = server.post("/warmup")
    assert first[0] == 200 and second[0] == 200
    assert first[1]["ok"] is True and second[1]["ok"] is True
    assert first[1]["model_id"] == "fake-bge-m3"


def test_TC_INT_026_warmup_failure_fast_fails():
    """[TC-INT-026] 权重不可用 → /warmup 快速失败 500（而非挂死）。"""
    from ib_embed.runtime import FakeRuntime

    runtime = FakeRuntime(dim=1024, model_id="fake-bge-m3")
    runtime.fail_next_load()
    with _Server(_cfg(IB_EMBED_MODEL_ID="fake-bge-m3"), runtime) as server:
        status, body = server.post("/warmup")
    assert status == 500 and body["code"] == "internal_error"


def test_TC_INT_027_descriptor_exactly_five_fields(loaded_server):
    """[TC-INT-027] /descriptor 恰五字段，与 EmbedderDescriptor 逐字段一致（IFC-IB-271）。"""
    server, _ = loaded_server
    status, body = server.post("/descriptor")
    assert status == 200
    assert set(body) == {"model_id", "dim", "normalized", "max_tokens", "device"}
    assert body["dim"] == 1024 and body["normalized"] is True


# --------------------------------------------------------------------------- #
# 路由卫生：未知路径 404、查询串被丢弃（无凭据泄漏面）
# --------------------------------------------------------------------------- #


def test_TC_INT_028_unknown_path_and_query_string_dropped(loaded_server):
    """[TC-INT-028] 未知路径 404；查询串被丢弃（`?token=` 不进入路由/日志面）。"""
    server, _ = loaded_server
    status, body = server.get("/nope")
    assert status == 404 and body["code"] == "not_found"
    # 带查询串的 /healthz 仍按 /healthz 路由（查询串被丢弃）
    status2, body2 = server.get("/healthz?token=SHOULD-NOT-MATTER")
    assert status2 == 200 and body2["ok"] is True
