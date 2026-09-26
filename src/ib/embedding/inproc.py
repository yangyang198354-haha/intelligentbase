"""
@module MOD-IB-09
@implements IFC-IB-275 `InProcessBgeM3Embedder`（第三种适配器形态；IFC-IB-090~096 的端口实现）
@depends MOD-IB-01
@author software-developer

进程内 bge-m3 Embedder（`IB_EMBED_BACKEND=inproc`；契约 §8「形态可逆」）。

**为什么带一份「看起来重复」的运行时加载逻辑**：本文件**必须位于 MOD-IB-09 之内**，
且**必须不 import MOD-IB-26** —— 否则产生 `09 → 26` 的非法反向依赖边（MOD-IB-26 是
「不被任何模块 import」的服务端模块，见 module_design §4.2 R2 补句与 C8）。
这份加载逻辑因此**有意**与 `ib_embed/runtime.py` 平行实现，而**非**共享代码：
共享会把两者绑成一个模块，反而破坏「形态可逆」（进程内形态不得依赖服务端进程）。
两者的**行为一致性**由契约 §8 要求的**三形态端口一致性测试**守住（descriptor 五字段、
`dim` / `normalized` 一致；有真模型时同文本余弦 ≈ 1）。

**本地权重目录**：取环境变量 `IB_EMBED_MODEL_PATH`（该键名**早已登记**于服务端键清单，
见 tech_stack.md §1.2 —— 此处复用同一键名的同一语义，**不新增键**）。缺失/不可导入 →
`descriptor()` / 首次 `embed_*` 抛**可读**的 `DependencyUnavailableError`（**不**在 import 期崩溃）。

**默认仍为 `http`**（契约 §8）：进程内形态的「模型内存 × worker 数」与「与 onnxruntime
同进程」的叠加峰值（[TBD-T4']）尚未实测，故本类只在显式配置时启用。
"""

from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Mapping, Sequence

from ib.core import (
    DependencyUnavailableError,
    EmbedderDescriptor,
    HealthStatus,
    Vector,
)

__all__ = ["InProcessBgeM3Embedder"]

#: 权重目录键（复用服务端已登记键名，语义一致：本地权重目录）。
MODEL_PATH_KEY = "IB_EMBED_MODEL_PATH"

#: 运行时候选顺序（与 `ib_embed.runtime._CANDIDATES` 有意保持一致）。
_CANDIDATES: tuple[str, ...] = ("flagembedding", "sentence_transformers", "onnxruntime")


def _l2(vec: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(float(v) * float(v) for v in vec))
    if norm == 0.0:
        return [float(v) for v in vec]
    return [float(v) / norm for v in vec]


def _masked_mean_pool(array: Any, mask: Any) -> list[list[float]]:
    rows: list[list[float]] = []
    for index in range(len(array)):
        row = array[index]
        if mask is None:
            rows.append([float(v) for v in row])
            continue
        weights = [float(v) for v in mask[index]]
        dim = len(row[0]) if len(row) else 0
        acc = [0.0] * dim
        total = 0.0
        for position, weight in enumerate(weights):
            if weight <= 0.0:
                continue
            total += weight
            vector = row[position]
            for column in range(dim):
                acc[column] += float(vector[column]) * weight
        if total > 0.0:
            acc = [value / total for value in acc]
        rows.append(acc)
    return rows


class InProcessBgeM3Embedder:
    """在**本进程内**加载 bge-m3 并做推理（IFC-IB-090~096 / IFC-IB-275）。

    与 `LocalHttpEmbedder` 的**端口契约完全等价**：相同的 7 个方法、相同的冷/热参数语义、
    相同的失败类型（`DependencyUnavailableError`）。差异仅在承载方式（无 HTTP）。

    加载是**惰性**的：`__init__` 不做任何重库 import，也不读权重；首次需要时才加载，
    使「配置了 inproc 但权重缺失」表现为**可读的运行时错误**而非 import 期崩溃。
    """

    def __init__(
        self,
        *,
        model_id: str = "bge-m3",
        dim: int = 1024,
        model_path: str | None = None,
        max_tokens: int = 8192,
        cold_batch_size: int = 16,
        cold_timeout_s: float = 120.0,
        cold_max_retries: int = 3,
        hot_timeout_s: float = 3.0,
        hot_max_retries: int = 1,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        source = os.environ if environ is None else environ
        self._model_path = (model_path or source.get(MODEL_PATH_KEY) or "").strip()
        self._model_id = model_id
        self._dim = dim
        self._max_tokens = max_tokens
        self._cold_batch = max(1, cold_batch_size)
        self._cold_timeout = cold_timeout_s
        self._cold_retries = max(1, cold_max_retries)
        self._hot_timeout = hot_timeout_s
        self._hot_retries = max(1, hot_max_retries)
        self._engine: Any = None
        self._kind: str | None = None
        self._reason: str | None = None
        self._lock = threading.Lock()

    # --- 加载 --- #

    def _fail(self, reason: str) -> DependencyUnavailableError:
        self._reason = reason
        return DependencyUnavailableError(reason, dependency="embedder")

    def _load(self) -> None:
        """加载权重（幂等）。失败抛可读 `DependencyUnavailableError`。"""
        with self._lock:
            if self._engine is not None:
                return
            if not self._model_path:
                raise self._fail(
                    f"进程内形态缺少本地权重目录（环境变量 {MODEL_PATH_KEY} 未设置）"
                )
            reasons: list[str] = []
            for candidate in _CANDIDATES:
                try:
                    engine = self._build(candidate)
                except DependencyUnavailableError as exc:
                    reasons.append(f"{candidate}: {exc}")
                    continue
                self._engine = engine
                self._kind = candidate
                self._reason = None
                return
            raise self._fail("进程内推理运行时均不可用（" + "；".join(reasons) + "）")

    def _build(self, candidate: str) -> dict[str, Any]:
        if candidate == "flagembedding":
            try:
                from FlagEmbedding import BGEM3FlagModel  # 惰性
            except ImportError as exc:
                raise self._fail("未安装推理运行时依赖（FlagEmbedding 不可导入）") from exc
            try:
                model = BGEM3FlagModel(self._model_path, use_fp16=False, device="cpu")
            except Exception as exc:  # noqa: BLE001
                raise self._fail(
                    f"模型权重加载失败（FlagEmbedding；{type(exc).__name__}）"
                ) from exc
            return {"kind": "flagembedding", "model": model}
        if candidate == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer  # 惰性
            except ImportError as exc:
                raise self._fail("未安装推理运行时依赖（sentence-transformers 不可导入）") from exc
            try:
                model = SentenceTransformer(self._model_path, device="cpu")
            except Exception as exc:  # noqa: BLE001
                raise self._fail(
                    f"模型权重加载失败（sentence-transformers；{type(exc).__name__}）"
                ) from exc
            return {"kind": "sentence_transformers", "model": model}
        if candidate == "onnxruntime":
            try:
                import onnxruntime
                from transformers import AutoTokenizer
            except ImportError as exc:
                raise self._fail(
                    "未安装推理运行时依赖（onnxruntime / transformers 不可导入）"
                ) from exc
            model_file = os.path.join(self._model_path, "model.onnx")
            if not os.path.isfile(model_file):
                raise self._fail("onnxruntime 路径缺少本地 ONNX 权重文件")
            try:
                session = onnxruntime.InferenceSession(
                    model_file, providers=["CPUExecutionProvider"]
                )
                tokenizer = AutoTokenizer.from_pretrained(self._model_path)
            except Exception as exc:  # noqa: BLE001
                raise self._fail(
                    f"模型权重加载失败（onnxruntime；{type(exc).__name__}）"
                ) from exc
            return {"kind": "onnxruntime", "session": session, "tokenizer": tokenizer}
        raise self._fail(f"未知运行时候选：{candidate}")

    # --- 推理内核 --- #

    def _infer(self, texts: Sequence[str]) -> list[Vector]:
        self._load()
        engine = self._engine
        kind = self._kind
        try:
            if kind == "flagembedding":
                out = engine["model"].encode(
                    list(texts), batch_size=len(texts), max_length=self._max_tokens
                )
                dense = out["dense_vecs"] if isinstance(out, dict) else out
                return [_l2([float(x) for x in row]) for row in dense]
            if kind == "sentence_transformers":
                matrix = engine["model"].encode(
                    list(texts), batch_size=len(texts), normalize_embeddings=True
                )
                return [_l2([float(x) for x in row]) for row in matrix]
            if kind == "onnxruntime":
                encoded = engine["tokenizer"](
                    list(texts),
                    padding=True,
                    truncation=True,
                    max_length=self._max_tokens,
                    return_tensors="np",
                )
                inputs = {
                    spec.name: encoded[spec.name]
                    for spec in engine["session"].get_inputs()
                    if spec.name in encoded
                }
                outputs = engine["session"].run(None, inputs)
                return [_l2(row) for row in _masked_mean_pool(outputs[0], encoded.get("attention_mask"))]
        except DependencyUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - 推理层异常统一转「依赖不可用」
            raise DependencyUnavailableError(
                f"进程内推理失败（{type(exc).__name__}）", dependency="embedder"
            ) from exc
        raise self._fail("进程内运行时处于未知状态")

    def _guard_dim(self, vectors: list[Vector]) -> list[Vector]:
        for vec in vectors:
            if len(vec) != self._dim:
                raise DependencyUnavailableError(
                    f"进程内推理维度 {len(vec)} 与声明 {self._dim} 不符", dependency="embedder"
                )
        return vectors

    # --- 端口方法（IFC-IB-090~096）--- #

    def dim(self) -> int:
        return self._dim

    def model_id(self) -> str:
        return self._model_id

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        timeout_s: float,
        max_retries: int,
        batch_size: int,
    ) -> list[Vector]:
        """**冷路径**：分批（`batch_size` 仅用于分批粒度；进程内无网络重试语义）。"""
        if not texts:
            return []
        effective_batch = max(1, min(batch_size or self._cold_batch, self._cold_batch))
        results: list[Vector] = []
        for start in range(0, len(texts), effective_batch):
            batch = list(texts[start : start + effective_batch])
            results.extend(self._infer(batch))
        return self._guard_dim(results)

    def embed_query(self, text: str, *, timeout_s: float) -> Vector:
        """**热路径**：单条。失败抛 `DependencyUnavailableError`（由 MOD-IB-15 转 `degraded`）。"""
        return self._guard_dim(self._infer([text]))[0]

    def health(self) -> HealthStatus:
        """**永不抛**（健康检查不得打挂调用方）。未加载**不等于**不健康 —— 惰性加载下
        「未加载」是正常态，故此处不主动触发加载：只报告当前可用性。"""
        started = time.perf_counter()
        if self._engine is not None:
            return HealthStatus(
                ok=True, detail=f"in-process {self._kind}", latency_ms=0
            )
        # 未加载：判定「重量级依赖是否可导入」以给出可读结论，但不真的载权重（可能数百 MB）
        try:
            self._probe(candidate=_CANDIDATES[0])
            detail = "in-process 运行时依赖可用（权重未加载）"
            ok = True
        except DependencyUnavailableError as exc:
            detail = f"in-process 运行时不可用：{exc}".split("：", 1)[-1]
            ok = False
        elapsed = int((time.perf_counter() - started) * 1000)
        return HealthStatus(ok=ok, detail=detail, latency_ms=elapsed)

    @staticmethod
    def _probe(*, candidate: str) -> None:
        """只探测「依赖是否可导入」，不加载权重（避免健康检查变成一次冷启动）。"""
        if candidate == "flagembedding":
            try:
                import FlagEmbedding  # noqa: F401
            except ImportError as exc:
                raise DependencyUnavailableError(
                    "未安装推理运行时依赖（FlagEmbedding 不可导入）", dependency="embedder"
                ) from exc
            return
        raise DependencyUnavailableError("未知运行时候选", dependency="embedder")

    def warmup(self) -> None:
        """触发权重加载。失败只记 WARN（不得阻塞启动 —— 启动期由 `health()` 报告）。"""
        try:
            self._load()
        except DependencyUnavailableError:
            from ib.observability import get_logger

            get_logger("embedding").warn(
                "warned", error_code="embed_warmup_failed", model_id=self._model_id
            )

    def descriptor(self) -> EmbedderDescriptor:
        """模型自述。**可用性优先**：已加载则以真实引擎为准，未加载则回落配置声明值。

        与 `LocalHttpEmbedder.descriptor()` 的回落语义一致 —— 三形态的 `descriptor()`
        必须逐字段一致（契约 §8 / AC-IB-06-05）。
        """
        dim = self._dim
        if self._engine is not None:
            dim = self._engine_dim() or dim
        return EmbedderDescriptor(
            model_id=self._model_id,
            dim=dim,
            normalized=True,
            max_tokens=self._max_tokens,
            device="cpu",
        )

    def _engine_dim(self) -> int | None:
        engine = self._engine
        kind = self._kind
        try:
            if kind == "flagembedding":
                hidden = getattr(
                    getattr(getattr(engine["model"], "model", None), "config", None),
                    "hidden_size",
                    None,
                )
                return int(hidden) if isinstance(hidden, int) and hidden > 0 else None
            if kind == "sentence_transformers":
                getter = getattr(engine["model"], "get_sentence_embedding_dimension", None)
                value = getter() if callable(getter) else None
                return int(value) if isinstance(value, int) and value > 0 else None
            if kind == "onnxruntime":
                shape = engine["session"].get_outputs()[0].shape
                if len(shape) >= 2 and isinstance(shape[-1], int) and shape[-1] > 0:
                    return int(shape[-1])
                return None
        except Exception:  # noqa: BLE001 - 自述失败不影响可用性
            return None
        return None
