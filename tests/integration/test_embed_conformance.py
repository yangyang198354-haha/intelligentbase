"""集成测试层 6/N —— Embedder 三形态一致性（含真实回环对拍）+ ib_embed 零耦合（C8）。

覆盖 AC-IB-07-01/02（形态可逆/一致）、C8（ib_embed 不 import 任何 ib.*）；
`http` 形态经**本机回环真 HTTP** 与 `ib_embed.server` 对拍 —— 无外部依赖。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", "src"))


def _cfg(backend, **overrides):
    from ib.config import DictConfigurationSource, resolve_global_config

    raw = {"offline_mode": False, "embedding": {"backend": backend, "model_id": "bge-m3", "dim": 1024, **overrides}}
    return resolve_global_config(DictConfigurationSource(raw).load())


def test_TC_INT_049_three_form_descriptor_consistency():
    """[TC-INT-049] http/inproc/fake 三形态经同一 `build_embedder` 产出**同构**描述子（AC-IB-07-01）。"""
    from ib.embedding import build_embedder

    seen = {}
    for backend in ("http", "inproc", "fake"):
        embedder = build_embedder(_cfg(backend))
        desc = embedder.descriptor()
        assert set(desc.__dataclass_fields__) == {"model_id", "dim", "normalized", "max_tokens", "device"}
        assert embedder.dim() == 1024
        assert desc.dim == 1024
        assert desc.normalized is True
        # 端口方法齐备（形态可逆的结构前提）
        for method in ("embed_documents", "embed_query", "health", "warmup", "descriptor", "dim", "model_id"):
            assert hasattr(embedder, method), f"{backend} 形态缺方法 {method}"
        seen[backend] = type(embedder).__name__
    assert len(set(seen.values())) == 3, f"三形态未落到三个不同实现：{seen}"


def test_TC_INT_050_ib_embed_zero_ib_coupling():
    """[TC-INT-050] C8：干净解释器里导入 ib_embed 全部模块，不得带入任何 `ib.*`（零耦合）。"""
    code = (
        "import ib_embed.server, ib_embed.config, ib_embed.runtime;"
        "import sys;"
        "bad=sorted(m for m in sys.modules if m=='ib' or m.startswith('ib.'));"
        "print(' '.join(bad) if bad else 'CLEAN')"
    )
    env = dict(os.environ, PYTHONPATH=_SRC, PYTHONUTF8="1")
    proc = subprocess.run([sys.executable, "-X", "utf8", "-c", code], capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "CLEAN", f"ib_embed 引入了基座依赖：{proc.stdout.strip()}"


class _Server:
    def __init__(self, cfg, runtime):
        from ib_embed.server import build_http_server

        self.httpd = build_http_server(cfg, runtime, host="127.0.0.1", port=0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def test_TC_INT_051_http_embedder_against_real_server():
    """[TC-INT-051] 冷/热两路径经回环 HTTP 对拍服务端：保序、维度、warmup、健康（AC-IB-07-02）。"""
    from ib.embedding import LocalHttpEmbedder
    from ib_embed.config import load_config
    from ib_embed.runtime import FakeRuntime

    runtime = FakeRuntime(dim=1024, model_id="bge-m3")
    server_cfg = load_config(
        {"IB_EMBED_MODEL_PATH": "/tmp/x", "IB_EMBED_MODEL_ID": "bge-m3", "IB_EMBED_DIM": "1024"}
    )
    with _Server(server_cfg, runtime) as server:
        embedder = LocalHttpEmbedder(
            base_url=f"http://127.0.0.1:{server.port}", model_id="bge-m3", dim=1024, hot_timeout_s=5.0
        )
        # 健康：未加载 → ok=False（可读），但**不抛**
        health_before = embedder.health()
        assert health_before.ok is False and health_before.detail
        # warmup 触发服务端加载
        embedder.warmup()
        # 冷路径：保序 + 维度
        docs = embedder.embed_documents(["甲段", "乙段", "丙段"], timeout_s=5.0, max_retries=1, batch_size=2)
        assert len(docs) == 3 and all(len(v) == 1024 for v in docs)
        # 热路径：与冷路径对齐同一文本 → 向量一致（同空间）
        hot = embedder.embed_query("甲段", timeout_s=5.0)
        assert hot == docs[0], "冷/热路径对同一文本产出不一致向量"
        # 描述子来自服务端实测值
        desc = embedder.descriptor()
        assert desc.dim == 1024 and desc.model_id == "bge-m3"
        assert embedder.health().ok is True


def test_TC_INT_052_http_embedder_fails_open_on_unreachable():
    """[TC-INT-052] 服务端不可达 → `DependencyUnavailableError`（由 MOD-IB-15 转 degraded，非崩溃）。"""
    from ib.core import DependencyUnavailableError
    from ib.embedding import LocalHttpEmbedder

    embedder = LocalHttpEmbedder(base_url="http://127.0.0.1:1", model_id="bge-m3", dim=1024)
    with pytest.raises(DependencyUnavailableError):
        embedder.embed_query("x", timeout_s=1.0)
    # 健康检查则**不抛**，只给结论
    assert embedder.health().ok is False


def test_TC_INT_053_embed_backend_env_domain_closed():
    """[TC-INT-053] `IB_EMBED_BACKEND` 值域闭集 {http,inproc,fake}；越界值被校验拒绝。"""
    from ib.config import ConfigurationResolver, DictConfigurationSource

    for bad in ("onnx", ""):
        resolver = ConfigurationResolver(
            DictConfigurationSource({"offline_mode": False, "embedding": {"backend": bad}})
        )
        errors = resolver.validate(env={})
        assert errors, f"非法嵌入后端 {bad!r} 未被拒"
        joined = " ".join(str(e) for e in errors)
        assert "IB_EMBED_BACKEND" in joined or "embedding" in joined
