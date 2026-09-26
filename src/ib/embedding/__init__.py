"""
@module MOD-IB-09
@implements IFC-IB-090 dim / 091 model_id / 092 embed_documents(冷) / 093 embed_query(热)
            IFC-IB-094 health / 095 warmup / 096 descriptor
            IFC-IB-098 CollectionResolver.resolve（**唯一** collection 名解析入口）
            IFC-IB-275 InProcessBgeM3Embedder（R2 第三种适配器形态；见 `inproc.py`）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

Embedding 端口与适配（module_design.md §3 MOD-IB-09 / ADR-02）。

**冷 / 热双路径是硬性契约**（AC-IB-07-03），不是实现细节：

| 路径 | 方法 | 批量 | 超时 | 重试 | 失败语义 |
|------|------|------|------|------|---------|
| 冷（入库） | `embed_documents` | 分批 | 长（默认 120s） | 多（默认 3） | 抛 `DependencyUnavailableError` -> 文档 `failed` |
| 热（查询） | `embed_query` | 单条 | 短（默认 3s） | 少（默认 1） | 抛 `DependencyUnavailableError` -> MOD-IB-15 转 `degraded` |

**三形态可逆**（R2 / IFC-IB-274 / IFC-IB-275）—— 由 `IB_EMBED_BACKEND` 选择，上层无感：

| 值 | 适配器 | 承载 |
|----|--------|------|
| `http`（默认） | `LocalHttpEmbedder` | 独立常驻进程 `ib-embed`（MOD-IB-26，只走线协议） |
| `inproc` | `InProcessBgeM3Embedder` | **本进程内**载权重（**不** import MOD-IB-26，避免 `09 → 26` 非法边） |
| `fake` | `FakeEmbedder` | 离线 / 测试 |

三形态必须通过**同一套端口一致性测试**（descriptor 五字段、`dim` / `normalized` 一致）。
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from typing import Any, Iterable, Sequence

from ib.core import (
    CollectionSpec,
    DependencyUnavailableError,
    EmbedderDescriptor,
    HealthStatus,
    HnswParams,
    ProjectRecord,
    Scope,
    ScopeViolationError,
    Vector,
)

from .inproc import InProcessBgeM3Embedder

__all__ = [
    "CollectionResolver",
    "FakeEmbedder",
    "InProcessBgeM3Embedder",
    "LocalHttpEmbedder",
    "build_embedder",
    "cosine",
    "l2_normalize",
    "collection_spec_for",
]

#: collection 名前缀（FM-5：启动期断言此前缀与 project_id 一致）。
COLLECTION_PREFIX = "ib_"


# --------------------------------------------------------------------------- #
# 向量工具（纯函数，供替身与自测复用）
# --------------------------------------------------------------------------- #


def l2_normalize(values: Sequence[float]) -> list[float]:
    """L2 归一化。零向量原样返回（不产生 NaN）。"""
    norm = math.sqrt(sum(float(v) * float(v) for v in values))
    if norm == 0.0:
        return [float(v) for v in values]
    return [float(v) / norm for v in values]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """余弦相似度。长度不等抛 `ValueError`（维度不一致必须显式暴露）。"""
    if len(a) != len(b):
        raise ValueError(f"向量维度不一致：{len(a)} vs {len(b)}")
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        fx = float(x)
        fy = float(y)
        dot += fx * fy
        na += fx * fx
        nb += fy * fy
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


# --------------------------------------------------------------------------- #
# CollectionResolver（IFC-IB-098）—— FM-5 的单一收敛点
# --------------------------------------------------------------------------- #


class CollectionResolver:
    """`Scope` + `ProjectRecord` -> collection 名（IFC-IB-098）。

    命名规则（ADR-04 / DR-06）：**`ib_<project_id>_v<collection_version>`**。

    三条强制性质：
      1. **唯一入口**：全仓（MOD-IB-10/13/14/15/23）只允许经此方法得到 collection 名；
         任何「外部传入的 collection 名」都被拒绝（FM-5）。
      2. **项目即 collection（硬隔离）**：不同项目天然落在不同 collection，
         跨项目不可见是**结构性事实**，不依赖各处 filter 写对（AC-IB-11-02）。
      3. **可升级**：若未来要求「知识库级硬隔离」，改动只发生在本方法内部（`resolve` 返回值
         带上 kb 维度），调用方零改动 —— 这正是把 `resolve()` 收敛成单入口的目的。
    """

    def resolve(self, scope: Scope, project: ProjectRecord) -> str:
        """解析 collection 名。`scope.project_id` 与 `project.project_id` 不一致即拒绝。"""
        if scope.project_id != project.project_id:
            raise ScopeViolationError(
                "Scope.project_id 与 ProjectRecord.project_id 不一致，拒绝解析 collection 名（FM-5）"
            )
        if not project.project_id or ":" in project.project_id:
            raise ScopeViolationError("project_id 非法（不得为空或含 ':'）")
        version = project.active_collection_version or "1"
        return f"{COLLECTION_PREFIX}{project.project_id}_v{version}"

    def assert_prefix(self, collection: str, project_id: str) -> None:
        """启动期一致性断言（FM-5 / AC-IB-12-03）：collection 前缀必须与项目匹配。"""
        expected = f"{COLLECTION_PREFIX}{project_id}_v"
        if not collection.startswith(expected):
            raise ScopeViolationError(
                f"collection 前缀与项目不一致：期望以 {expected!r} 开头（FM-5）"
            )


def collection_spec_for(
    project: ProjectRecord, *, on_disk_vectors: bool = False, hnsw: HnswParams | None = None
) -> CollectionSpec:
    """由项目记录派生 `CollectionSpec`（维度取自项目，**不硬编码**，支持项目间异构维度）。"""
    return CollectionSpec(
        collection=f"{COLLECTION_PREFIX}{project.project_id}_v{project.active_collection_version or '1'}",
        dim=project.dim,
        distance="cosine",
        on_disk_vectors=on_disk_vectors,
        hnsw=hnsw or HnswParams(),
    )


# --------------------------------------------------------------------------- #
# FakeEmbedder（离线替身）
# --------------------------------------------------------------------------- #


class FakeEmbedder:
    """确定性伪向量（IFC-IB-090~096 的测试替身）。

    设计要点：
      * **确定性**：同一文本恒得同一向量（不依赖随机数）；
      * **语义近似性**：以「字符二元组」散列投影到 dim 维，使**共享词组的文本余弦更高** ——
        这样离线端到端链路（入库 → 检索 → 命中）能真实跑通，而不是退化成随机噪声；
      * **三态可编排**：`unavailable=True` 模拟不可达；`timeout=True` 模拟超时；
        二者均抛 `DependencyUnavailableError`，供 AC-IB-07-03 / AC-IB-14-01 使用。
    """

    def __init__(
        self,
        *,
        dim: int = 1024,
        model_id: str = "fake-bge-m3",
        unavailable: bool = False,
        timeout: bool = False,
        latency_ms: int = 0,
    ) -> None:
        self._dim = dim
        self._model_id = model_id
        self._unavailable = unavailable
        self._timeout = timeout
        self._latency_ms = latency_ms

    def _guard(self) -> None:
        if self._latency_ms:
            time.sleep(self._latency_ms / 1000.0)
        if self._unavailable:
            raise DependencyUnavailableError("FakeEmbedder: 依赖不可达（模拟）", dependency="embedder")
        if self._timeout:
            raise DependencyUnavailableError("FakeEmbedder: 热路径超时（模拟）", dependency="embedder")

    def _vector(self, text: str) -> list[float]:
        """字符二元组袋 -> dim 维散列投影 -> L2 归一化。确定性且对词组重叠敏感。"""
        acc = [0.0] * self._dim
        normalized = " ".join(text.lower().split())
        grams: Iterable[str]
        if len(normalized) < 2:
            grams = [normalized or " "]
        else:
            grams = (normalized[i : i + 2] for i in range(len(normalized) - 1))
        for gram in grams:
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            acc[bucket] += sign
        return l2_normalize(acc)

    # --- 端口方法 --- #

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
        self._guard()
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str, *, timeout_s: float) -> Vector:
        self._guard()
        return self._vector(text)

    def health(self) -> HealthStatus:
        if self._unavailable:
            return HealthStatus(ok=False, detail="fake embedder marked unavailable", latency_ms=0)
        return HealthStatus(ok=True, detail="fake embedder", latency_ms=0)

    def warmup(self) -> None:
        try:
            self._vector("warmup")
        except DependencyUnavailableError:
            pass

    def descriptor(self) -> EmbedderDescriptor:
        return EmbedderDescriptor(
            model_id=self._model_id,
            dim=self._dim,
            normalized=True,
            max_tokens=8192,
            device="cpu",
        )


# --------------------------------------------------------------------------- #
# LocalHttpEmbedder（生产实现：-> ib-embed）
# --------------------------------------------------------------------------- #


class LocalHttpEmbedder:
    """经 HTTP 访问本基座 `ib-embed` 服务的 Embedder（IFC-IB-090~096）。

    * 仅使用 stdlib `urllib.request`（无额外 HTTP 客户端依赖，保持组成面最小）；
    * **冷路径**：按 `batch_size` 分批 + 长超时 + 多重试（指数退避）；
    * **热路径**：单条 + 短超时 + 少重试；超时 / 不可达抛 `DependencyUnavailableError`；
    * `warmup()` 触发服务端权重加载（冷启动一次性成本移出热路径，ADR-02 缓解手段 2）。
    """

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str = "bge-m3",
        dim: int = 1024,
        cold_timeout_s: float = 120.0,
        cold_max_retries: int = 3,
        cold_batch_size: int = 16,
        hot_timeout_s: float = 3.0,
        hot_max_retries: int = 1,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._model_id = model_id
        self._dim = dim
        self._cold_timeout = cold_timeout_s
        self._cold_retries = max(1, cold_max_retries)
        self._cold_batch = max(1, cold_batch_size)
        self._hot_timeout = hot_timeout_s
        self._hot_retries = max(1, hot_max_retries)
        self._descriptor: EmbedderDescriptor | None = None

    # --- HTTP 内核 --- #

    def _post(self, path: str, payload: dict[str, Any], *, timeout_s: float, retries: int) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        url = f"{self._base}{path}"
        last_error: Exception | None = None
        for attempt in range(retries):
            request = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310 - 内网固定端点
                    raw = response.read()
                parsed = json.loads(raw.decode("utf-8"))
                if not isinstance(parsed, dict):
                    raise DependencyUnavailableError(f"ib-embed 返回非法载荷：{path}", dependency="embedder")
                return parsed
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code < 500:
                    # 4xx 是调用方错误，重试无意义
                    break
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                last_error = exc
            if attempt < retries - 1:
                time.sleep(min(0.5 * (2**attempt), 4.0))
        raise DependencyUnavailableError(
            f"ib-embed 不可达或超时（{type(last_error).__name__ if last_error else 'unknown'}）",
            dependency="embedder",
        )

    def _vectors_from(self, parsed: dict[str, Any], expected: int) -> list[list[float]]:
        vectors = parsed.get("vectors")
        if not isinstance(vectors, list) or len(vectors) != expected:
            raise DependencyUnavailableError("ib-embed 返回的向量数量与请求不符", dependency="embedder")
        out: list[list[float]] = []
        for vec in vectors:
            out.append([float(v) for v in vec])
        for vec in out:
            if len(vec) != self._dim:
                raise DependencyUnavailableError(
                    f"ib-embed 返回维度 {len(vec)} 与声明 {self._dim} 不符", dependency="embedder"
                )
        return out

    # --- 端口方法 --- #

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
        """**冷路径**：分批 + 长超时 + 多重试。空输入返回空列表（不发起请求）。"""
        if not texts:
            return []
        effective_batch = max(1, min(batch_size or self._cold_batch, self._cold_batch))
        effective_timeout = timeout_s or self._cold_timeout
        effective_retries = max(max_retries, self._cold_retries)
        results: list[Vector] = []
        for start in range(0, len(texts), effective_batch):
            batch = list(texts[start : start + effective_batch])
            parsed = self._post(
                "/embed",
                {"texts": batch, "model": self._model_id, "mode": "document"},
                timeout_s=effective_timeout,
                retries=effective_retries,
            )
            results.extend(self._vectors_from(parsed, len(batch)))
        return results

    def embed_query(self, text: str, *, timeout_s: float) -> Vector:
        """**热路径**：单条 + 短超时 + 少重试；超时即抛（由 MOD-IB-15 转 degraded）。"""
        parsed = self._post(
            "/embed",
            {"texts": [text], "model": self._model_id, "mode": "query"},
            timeout_s=timeout_s or self._hot_timeout,
            retries=self._hot_retries,
        )
        vectors = self._vectors_from(parsed, 1)
        return vectors[0]

    def health(self) -> HealthStatus:
        """探测 `/healthz`。失败返回 `ok=False`（**不抛异常** —— 健康检查不得打挂调用方）。"""
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(f"{self._base}/healthz", timeout=2.0) as response:  # noqa: S310
                raw = json.loads(response.read().decode("utf-8"))
            elapsed = int((time.perf_counter() - started) * 1000)
            ok = bool(raw.get("ok", True))
            return HealthStatus(ok=ok, detail=str(raw.get("detail", "ib-embed")), latency_ms=elapsed)
        except Exception as exc:  # noqa: BLE001 - 健康检查必须给出结论而非异常
            elapsed = int((time.perf_counter() - started) * 1000)
            return HealthStatus(ok=False, detail=f"ib-embed 不可达：{type(exc).__name__}", latency_ms=elapsed)

    def warmup(self) -> None:
        """触发服务端权重加载。失败只记 WARN（不得阻塞启动 —— 启动期由 health 报告）。"""
        from ib.observability import get_logger

        try:
            self._post("/warmup", {"model": self._model_id}, timeout_s=max(self._cold_timeout, 300.0), retries=1)
        except DependencyUnavailableError:
            get_logger("embedding").warn("warned", error_code="embed_warmup_failed", model_id=self._model_id)

    def descriptor(self) -> EmbedderDescriptor:
        """模型自述。首次调用向后端 `/descriptor` 询问，失败则退回配置声明值。

        维度是**写入正确性的前提**（`dim` 不符会写坏 collection），故此处优先信任服务端真实值。
        """
        if self._descriptor is not None:
            return self._descriptor
        try:
            parsed = self._post("/descriptor", {"model": self._model_id}, timeout_s=5.0, retries=1)
            self._descriptor = EmbedderDescriptor(
                model_id=str(parsed.get("model_id", self._model_id)),
                dim=int(parsed.get("dim", self._dim)),
                normalized=bool(parsed.get("normalized", True)),
                max_tokens=int(parsed.get("max_tokens", 8192)),
                device=str(parsed.get("device", "cpu")),
            )
        except (DependencyUnavailableError, TypeError, ValueError):
            self._descriptor = EmbedderDescriptor(
                model_id=self._model_id,
                dim=self._dim,
                normalized=True,
                max_tokens=8192,
                device="cpu",
            )
        return self._descriptor


def build_embedder(cfg: Any) -> Any:
    """按配置构造 Embedder（组合根单点调用）。

    R2（IFC-IB-274）：值域由 `{http, fake}` 扩展为 `{http, inproc, fake}`。
    **键名与默认值 `http` 不变**，`http` 仍是默认落点（`inproc` 只影响此处一行装配）。
    """
    if cfg.embedding.backend == "fake":
        return FakeEmbedder(dim=cfg.embedding.dim, model_id=cfg.embedding.model_id)
    if cfg.embedding.backend == "inproc":
        # 进程内形态：本地权重目录取自 `IB_EMBED_MODEL_PATH`（已登记键名，非新增键）。
        return InProcessBgeM3Embedder(
            model_id=cfg.embedding.model_id,
            dim=cfg.embedding.dim,
            cold_batch_size=cfg.embedding.cold_batch_size,
            cold_timeout_s=cfg.embedding.cold_timeout_s,
            cold_max_retries=cfg.embedding.cold_max_retries,
            hot_timeout_s=cfg.embedding.hot_timeout_s,
            hot_max_retries=cfg.embedding.hot_max_retries,
        )
    return LocalHttpEmbedder(
        base_url=cfg.embedding.url,
        model_id=cfg.embedding.model_id,
        dim=cfg.embedding.dim,
        cold_timeout_s=cfg.embedding.cold_timeout_s,
        cold_max_retries=cfg.embedding.cold_max_retries,
        cold_batch_size=cfg.embedding.cold_batch_size,
        hot_timeout_s=cfg.embedding.hot_timeout_s,
        hot_max_retries=cfg.embedding.hot_max_retries,
    )
