"""
@module MOD-IB-26
@implements IFC-IB-270（权重加载 / 幂等预热，服务端侧）
            IFC-IB-271（`/descriptor` 的权威值与 `EmbedderDescriptor` 五字段一致）
            IFC-IB-272（单条截断保前缀 —— 由运行时上报 `truncated_indices`）
            IFC-IB-274（形态可逆的**运行时**一侧：库可替换，装配可切换）
@depends —
@author software-developer

bge-m3 推理运行时（**可替换端口** + **惰性加载**）。

为什么必须是「端口 + 惰性」而不是「直接 import 一个库」：

1. **库选型未定**（契约 §10 / tech_stack §1 R2 改写）：`FlagEmbedding` / `sentence-transformers`
   / 直接 `onnxruntime` 三选一，须在目标机以 [TBD-T1/T3/T4/T18] 实测后才拍板。
   任何在 import 期就 `import torch` 的写法都会把「未定」写成「既成事实」。
2. **缺库不得启动崩溃**：本模块**全部**第三方 import 都在函数体内（`_try_*`），
   import 期只依赖标准库。缺库 → 运行时进入 `unavailable` 态，`/healthz` 给出**可读**原因，
   `/embed` 返回 `503 model_not_ready` —— 服务本身照样起得来、探得通（可观测优先）。
3. **不在测试中联网下载权重**（C5）：三候选的构造一律以 `IB_EMBED_MODEL_PATH` 指向的
   **本地目录**为入参；本模块**不**出现任何模型标识符的网络拉取（不调 `from_pretrained("BAAI/…")`
   之外的名字，且名字取自本地路径）。

**内部形态常量 `RUNTIME_BACKEND`（不是配置键）**：契约 §10 要求「最终择一须可切换」，
但**不得**为服务端新增配置键（§9 键清单是封闭的）。故此处用模块级常量切换，
GROUP_C 实测后改这一行即可；`"auto"` 依许可与内存面优先 `FlagEmbedding`。
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any, Protocol, Sequence, runtime_checkable

from .config import EmbedConfig

__all__ = [
    "RUNTIME_BACKEND",
    "InferenceUnavailable",
    "RuntimeBatch",
    "RuntimeDescriptor",
    "RuntimePort",
    "FakeRuntime",
    "UnavailableRuntime",
    "load_runtime",
]

#: 运行时选择开关（**代码级**，非配置键）。可选值见 `_CANDIDATES`。
#: 契约 §10：最终择一须目标机实测后定 —— 改这一行即可切换，不动任何上层模块。
RUNTIME_BACKEND: str = "auto"

#: 候选顺序：许可与内存面优先（FlagEmbedding MIT，BAAI 官方，抽象层最少）。
_CANDIDATES: tuple[str, ...] = ("flagembedding", "sentence_transformers", "onnxruntime")


class InferenceUnavailable(RuntimeError):
    """运行时不可用（缺库 / 权重缺失 / 维度不符）。**消息可读、不含凭据、不含正文**。"""


@dataclass(frozen=True, slots=True)
class RuntimeDescriptor:
    """运行时自述。字段名与 MOD-IB-01 `EmbedderDescriptor` **逐字段一致**（IFC-IB-271）。"""

    model_id: str
    dim: int
    normalized: bool
    max_tokens: int
    device: str


@dataclass(frozen=True, slots=True)
class RuntimeBatch:
    """一次推理的产出。

    * `vectors`：与入参**逐位置对应**（保序契约，IFC-IB-266 §3.2）；
      **绝不**允许「部分向量」——要么整批都在，要么由上层整体报错。
    * `truncated_indices`：仅当发生单条截断时非空（IFC-IB-272）；只标注、不失败。
    """

    vectors: tuple[tuple[float, ...], ...]
    truncated_indices: tuple[int, ...] = ()


@runtime_checkable
class RuntimePort(Protocol):
    """可替换的推理运行时端口（服务端内部，**不是**对外契约）。"""

    def load(self) -> int:
        """加载权重并返回耗时毫秒。**幂等**：已加载则立即返回（不重复加载）。"""
        ...

    def is_loaded(self) -> bool: ...

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch: ...

    def descriptor(self) -> RuntimeDescriptor: ...


def _l2(vec: Sequence[float]) -> tuple[float, ...]:
    """L2 归一化（契约 §3.2：`normalized` 恒 `true`；在此二次保证，不依赖库的默认行为）。"""
    norm = math.sqrt(sum(float(v) * float(v) for v in vec))
    if norm == 0.0:
        return tuple(float(v) for v in vec)
    return tuple(float(v) / norm for v in vec)


# --------------------------------------------------------------------------- #
# 候选一：FlagEmbedding（MIT，BAAI 官方）
# --------------------------------------------------------------------------- #


class _FlagEmbeddingRuntime:
    def __init__(self, cfg: EmbedConfig) -> None:
        self._cfg = cfg
        self._model: Any = None
        self._device = "cpu"
        self._lock = threading.Lock()

    def load(self) -> int:
        with self._lock:
            if self._model is not None:
                return 0
            started = time.perf_counter()
            try:
                from FlagEmbedding import BGEM3FlagModel  # 惰性：仅在真正加载时 import
            except ImportError as exc:  # 缺库 → 可读原因，不崩溃
                raise InferenceUnavailable("未安装推理运行时依赖（FlagEmbedding 不可导入）") from exc
            try:
                self._model = BGEM3FlagModel(self._cfg.model_path, use_fp16=False, device="cpu")
            except Exception as exc:  # noqa: BLE001 - 权重/驱动层异常统一转可读原因
                raise InferenceUnavailable(
                    f"模型权重加载失败（FlagEmbedding；{type(exc).__name__}）"
                ) from exc
            return int((time.perf_counter() - started) * 1000)

    def is_loaded(self) -> bool:
        return self._model is not None

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        if self._model is None:
            raise InferenceUnavailable("模型权重尚未加载完成")
        out = self._model.encode(
            list(texts), batch_size=max(1, batch_size), max_length=int(max_tokens)
        )
        dense = out["dense_vecs"] if isinstance(out, dict) else out
        vectors = tuple(_l2([float(x) for x in row]) for row in dense)
        return RuntimeBatch(vectors=vectors, truncated_indices=self._truncated(texts, max_tokens))

    def _truncated(self, texts: Sequence[str], max_tokens: int) -> tuple[int, ...]:
        """best-effort 截断标注：拿得到 tokenizer 才算，拿不到就**不谎报**。"""
        tokenizer = getattr(self._model, "tokenizer", None)
        if tokenizer is None:
            return ()
        hits: list[int] = []
        for index, text in enumerate(texts):
            try:
                length = len(tokenizer.encode(text))
            except Exception:  # noqa: BLE001 - 标注失败不影响推理结果
                return ()
            if length > max_tokens:
                hits.append(index)
        return tuple(hits)

    def descriptor(self) -> RuntimeDescriptor:
        dim = 0
        model = self._model
        if model is not None:
            dense = getattr(model, "model", None)
            hidden = getattr(getattr(dense, "config", None), "hidden_size", None)
            if isinstance(hidden, int) and hidden > 0:
                dim = hidden
        return RuntimeDescriptor(
            model_id=self._cfg.model_id,
            dim=dim or self._cfg.dim,
            normalized=True,
            max_tokens=self._cfg.max_tokens,
            device=self._device,
        )


# --------------------------------------------------------------------------- #
# 候选二：sentence-transformers（Apache-2.0）
# --------------------------------------------------------------------------- #


class _SentenceTransformersRuntime:
    def __init__(self, cfg: EmbedConfig) -> None:
        self._cfg = cfg
        self._model: Any = None
        self._device = "cpu"
        self._lock = threading.Lock()

    def load(self) -> int:
        with self._lock:
            if self._model is not None:
                return 0
            started = time.perf_counter()
            try:
                from sentence_transformers import SentenceTransformer  # 惰性
            except ImportError as exc:
                raise InferenceUnavailable(
                    "未安装推理运行时依赖（sentence-transformers 不可导入）"
                ) from exc
            try:
                self._model = SentenceTransformer(self._cfg.model_path, device="cpu")
            except Exception as exc:  # noqa: BLE001
                raise InferenceUnavailable(
                    f"模型权重加载失败（sentence-transformers；{type(exc).__name__})"
                ) from exc
            return int((time.perf_counter() - started) * 1000)

    def is_loaded(self) -> bool:
        return self._model is not None

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        if self._model is None:
            raise InferenceUnavailable("模型权重尚未加载完成")
        self._model.max_seq_length = int(max_tokens)
        matrix = self._model.encode(
            list(texts), batch_size=max(1, batch_size), normalize_embeddings=True
        )
        vectors = tuple(_l2([float(x) for x in row]) for row in matrix)
        return RuntimeBatch(vectors=vectors, truncated_indices=self._truncated(texts, max_tokens))

    def _truncated(self, texts: Sequence[str], max_tokens: int) -> tuple[int, ...]:
        tokenizer = getattr(self._model, "tokenizer", None)
        if tokenizer is None:
            return ()
        hits: list[int] = []
        for index, text in enumerate(texts):
            try:
                length = len(tokenizer.encode(text))
            except Exception:  # noqa: BLE001
                return ()
            if length > max_tokens:
                hits.append(index)
        return tuple(hits)

    def descriptor(self) -> RuntimeDescriptor:
        dim = 0
        model = self._model
        if model is not None:
            getter = getattr(model, "get_sentence_embedding_dimension", None)
            if callable(getter):
                value = getter()
                if isinstance(value, int) and value > 0:
                    dim = value
        return RuntimeDescriptor(
            model_id=self._cfg.model_id,
            dim=dim or self._cfg.dim,
            normalized=True,
            max_tokens=self._cfg.max_tokens,
            device=self._device,
        )


# --------------------------------------------------------------------------- #
# 候选三：直接 onnxruntime（MIT，无 torch；tokenizer 取自 transformers）
# --------------------------------------------------------------------------- #


class _OnnxRuntime:
    """`onnxruntime` + `transformers` tokenizer 的 bge-m3 路径。

    注意：本路径须**自实现池化与归一化**（契约 §10 已登记该风险：错误实现会静默降低
    检索质量）。此处采用 bge 系列的标准做法 —— **attention-mask 加权的 mean pooling**
    再 L2 归一化；`CLS` 首向量不作为稠密输出。

    `model.onnx` / `tokenizer.json` 由 `IB_EMBED_MODEL_PATH` 指向的本地目录提供；
    **不联网下载**（C5）。
    """

    def __init__(self, cfg: EmbedConfig) -> None:
        self._cfg = cfg
        self._session: Any = None
        self._tokenizer: Any = None
        self._device = "cpu"
        self._lock = threading.Lock()

    def load(self) -> int:
        import os

        with self._lock:
            if self._session is not None:
                return 0
            started = time.perf_counter()
            try:
                import onnxruntime  # 惰性
                from transformers import AutoTokenizer  # 惰性
            except ImportError as exc:
                raise InferenceUnavailable(
                    "未安装推理运行时依赖（onnxruntime / transformers 不可导入）"
                ) from exc
            model_file = os.path.join(self._cfg.model_path, "model.onnx")
            if not os.path.isfile(model_file):
                raise InferenceUnavailable("onnxruntime 路径缺少本地 ONNX 权重文件")
            try:
                options = onnxruntime.SessionOptions()
                options.intra_op_num_threads = int(self._cfg.threads)
                options.inter_op_num_threads = 1
                self._session = onnxruntime.InferenceSession(
                    model_file, sess_options=options, providers=["CPUExecutionProvider"]
                )
                self._tokenizer = AutoTokenizer.from_pretrained(self._cfg.model_path)
            except Exception as exc:  # noqa: BLE001
                raise InferenceUnavailable(
                    f"模型权重加载失败（onnxruntime；{type(exc).__name__})"
                ) from exc
            return int((time.perf_counter() - started) * 1000)

    def is_loaded(self) -> bool:
        return self._session is not None

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        if self._session is None or self._tokenizer is None:
            raise InferenceUnavailable("模型权重尚未加载完成")
        encoded = self._tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=int(max_tokens),
            return_tensors="np",
        )
        inputs: dict[str, Any] = {}
        for name in self._session.get_inputs():
            if name.name in encoded:
                inputs[name.name] = encoded[name.name]
        outputs = self._session.run(None, inputs)
        array = outputs[0]
        mask = encoded.get("attention_mask")
        pooled = _masked_mean_pool(array, mask)
        vectors = tuple(_l2(row) for row in pooled)
        lengths = encoded.get("attention_mask")
        truncated: tuple[int, ...] = ()
        if lengths is not None:
            hits = [
                index
                for index, row in enumerate(lengths)
                if int(sum(int(v) for v in row)) >= int(max_tokens)
            ]
            truncated = tuple(hits)
        return RuntimeBatch(vectors=vectors, truncated_indices=truncated)

    def descriptor(self) -> RuntimeDescriptor:
        dim = 0
        if self._session is not None:
            shapes = self._session.get_outputs()[0].shape
            if len(shapes) >= 2 and isinstance(shapes[-1], int) and shapes[-1] > 0:
                dim = int(shapes[-1])
        return RuntimeDescriptor(
            model_id=self._cfg.model_id,
            dim=dim or self._cfg.dim,
            normalized=True,
            max_tokens=self._cfg.max_tokens,
            device=self._device,
        )


def _masked_mean_pool(array: Any, mask: Any) -> list[list[float]]:
    """attention-mask 加权 mean pooling（bge 稠密向量的标准后处理）。"""
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


# --------------------------------------------------------------------------- #
# 不可用替身（缺库/缺权重时的**可读**终局）
# --------------------------------------------------------------------------- #


class UnavailableRuntime:
    """加载失败后的终局运行时：`is_loaded()` 恒 `False`，任何 `embed` 抛可读原因。

    存在的意义：让服务**起得来、探得通、报得出**，而不是「配置文件写错 → 进程起不来 →
    只能靠读 systemd 日志猜」。`/healthz` 的 `detail` 直接取自 `reason`。
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def load(self) -> int:
        raise InferenceUnavailable(self.reason)

    def is_loaded(self) -> bool:
        return False

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        raise InferenceUnavailable(self.reason)

    def descriptor(self) -> RuntimeDescriptor:
        raise InferenceUnavailable(self.reason)


class FakeRuntime:
    """离线替身（**仅供自测**）：确定性伪向量，语义近似性对齐 `ib.embedding.FakeEmbedder`。

    `C5` 要求「服务端测试不得联网下载权重」—— 本替身即该约束下的运行时落点。
    """

    def __init__(self, *, dim: int = 1024, model_id: str = "fake-bge-m3") -> None:
        self._dim = dim
        self._model_id = model_id
        self._loaded = False
        self._fail_load = False
        self._truncated_at: int | None = None

    # --- 测试编排钩子 --- #
    def fail_next_load(self) -> None:
        self._fail_load = True

    def mark_truncation(self, index: int) -> None:
        self._truncated_at = index

    # --- 端口方法 --- #

    def load(self) -> int:
        if self._fail_load:
            raise InferenceUnavailable("fake runtime: 模拟权重加载失败")
        self._loaded = True
        return 1

    def is_loaded(self) -> bool:
        return self._loaded

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        if not self._loaded:
            raise InferenceUnavailable("模型权重尚未加载完成")
        vectors = tuple(self._vector(text) for text in texts)
        truncated = () if self._truncated_at is None else (self._truncated_at,)
        return RuntimeBatch(vectors=vectors, truncated_indices=truncated)

    def descriptor(self) -> RuntimeDescriptor:
        return RuntimeDescriptor(
            model_id=self._model_id,
            dim=self._dim,
            normalized=True,
            max_tokens=8192,
            device="cpu",
        )

    def _vector(self, text: str) -> tuple[float, ...]:
        import hashlib

        acc = [0.0] * self._dim
        normalized = " ".join(text.lower().split())
        grams = [normalized or " "] if len(normalized) < 2 else [
            normalized[i : i + 2] for i in range(len(normalized) - 1)
        ]
        for gram in grams:
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            acc[bucket] += sign
        return _l2(acc)


def _build(candidate: str, cfg: EmbedConfig) -> RuntimePort:
    if candidate == "flagembedding":
        return _FlagEmbeddingRuntime(cfg)
    if candidate == "sentence_transformers":
        return _SentenceTransformersRuntime(cfg)
    if candidate == "onnxruntime":
        return _OnnxRuntime(cfg)
    raise InferenceUnavailable(f"未知运行时候选：{candidate}")


class _CascadingRuntime:
    """`RUNTIME_BACKEND="auto"` 的选型器：**按候选顺序逐个试加载**，首个成功者胜出。

    为什么把选型推迟到 `load()`：`auto` 语义要求「装了哪个用哪个」，而探测「装没装」
    唯一可靠的方法是 import（有副作用、有耗时），所以唯一合理的时点就是真正要加载权重时。
    """

    def __init__(self, cfg: EmbedConfig, candidates: Sequence[str]) -> None:
        self._cfg = cfg
        self._candidates = tuple(candidates)
        self._active: RuntimePort | None = None
        self._reasons: list[str] = []
        self._lock = threading.Lock()

    def load(self) -> int:
        with self._lock:
            if self._active is not None:
                return self._active.load()
            self._reasons = []
            for candidate in self._candidates:
                try:
                    runtime = _build(candidate, self._cfg)
                    loaded_ms = runtime.load()
                except InferenceUnavailable as exc:
                    self._reasons.append(f"{candidate}: {exc}")
                    continue
                self._active = runtime
                return loaded_ms
        raise InferenceUnavailable("所有运行时候选均不可用（" + "；".join(self._reasons) + "）")

    def is_loaded(self) -> bool:
        return self._active is not None and self._active.is_loaded()

    def embed(self, texts: Sequence[str], *, batch_size: int, max_tokens: int) -> RuntimeBatch:
        active = self._active
        if active is None:
            raise InferenceUnavailable("模型权重尚未加载完成")
        return active.embed(texts, batch_size=batch_size, max_tokens=max_tokens)

    def descriptor(self) -> RuntimeDescriptor:
        active = self._active
        if active is None:
            raise InferenceUnavailable("模型权重尚未加载完成")
        return active.descriptor()


def load_runtime(cfg: EmbedConfig) -> RuntimePort:
    """构造运行时。**惰性**：此处不加载权重（不 import 任何重库），只选实现类。

    选类失败（`RUNTIME_BACKEND` 被改成未知值）返回 `UnavailableRuntime`，
    由 `/healthz` 报出可读原因；**绝不**在 import/构造期抛到调用方之外。
    """
    backend = RUNTIME_BACKEND
    order = _CANDIDATES if backend == "auto" else (backend,)
    if len(order) == 1 and backend != "auto":
        try:
            return _build(order[0], cfg)
        except InferenceUnavailable as exc:
            return UnavailableRuntime(str(exc))
    return _CascadingRuntime(cfg, order)
