"""
@module MOD-IB-10
@implements IFC-IB-100 ensure_collection / 101 collection_info / 102 list_collections
            IFC-IB-103 delete_by_collection / 104 upsert / 105 query / 106 delete_by_doc
            IFC-IB-107 delete_by_scope / 108 count / 109 health / 110 flush
            （扩展位）supports_hybrid_search -> False，**显式声明不支持**而非静默失败
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

VectorStore 端口与适配（module_design.md §3 MOD-IB-10 / ADR-01）。

两个适配器，**同一套端口语义**（AC-IB-06-05 要求二者通过同一套端口一致性测试）：
  * `QdrantVectorStore` —— 生产（`qdrant-client`，gRPC 主 / REST 回退与健康）；延迟导入；
  * `InMemoryVectorStore` —— 替身（**暴力余弦**，与本基座同度量），**纯 stdlib**、离线可跑。

隔离纪律（FM-1 / FM-3）在本文件被落实为三条实现约束：
  1. 所有读写方法的 `scope` **必填**，无默认值；
  2. 内部构造的 filter **恒含 `project_id`**（即便调用方传了 `PointFilter`，也与 `scope` 求交）；
  3. `delete_by_*` 一律以 `(project_id[, kb_ids], doc_id)` 限定，**绝不按名称删除**。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Sequence

from ib.core import (
    CollectionInfo,
    CollectionSpec,
    DependencyUnavailableError,
    HealthStatus,
    PointFilter,
    PointPayload,
    Scope,
    ScopeViolationError,
    ScoredPoint,
    StartupError,
    UpsertResult,
    Vector,
    VectorPoint,
)
from ib.embedding import COLLECTION_PREFIX, cosine

__all__ = ["InMemoryVectorStore", "QdrantVectorStore", "build_vector_store", "point_id_for"]


def point_id_for(doc_id: str, chunk_index: int) -> str:
    """向量点幂等键（§6.2）：`doc_id` + `chunk_index`。

    重跑覆盖同一批点，**不产生重复** —— 这是「delete-then-write」之外的第二重幂等保障。
    """
    return f"{doc_id}#{chunk_index}"


def _version_key(collection: str) -> tuple[int, str]:
    """按 collection 名的版本号数值排序（避免 `v10` 被字符串序排在 `v9` 之前）。"""
    tail = collection.rsplit("_v", 1)[-1]
    try:
        return (int(tail), collection)
    except ValueError:
        return (-1, collection)


def _matches(payload: PointPayload, *, project_id: str, kb_ids: tuple[str, ...] | None, doc_ids: tuple[str, ...] | None) -> bool:
    """payload 过滤的唯一内核。**`project_id` 恒为必判条件**（FM-1 的纵深防御层）。"""
    if payload.project_id != project_id:
        return False
    if kb_ids is not None and payload.kb_id not in kb_ids:
        return False
    if doc_ids is not None and payload.doc_id not in doc_ids:
        return False
    return True


@dataclass
class _Collection:
    spec: CollectionSpec
    points: dict[str, tuple[list[float], PointPayload]]


class InMemoryVectorStore:
    """进程内暴力余弦向量库（IFC-IB-100~110 的替身实现）。

    * **纯 stdlib**：无第三方依赖，属离线可测路径（AC-IB-14-05 / AC-IB-15-01）；
    * 与 Qdrant 使用**同一余弦度量**，因此二者结果可互校（ADR-01 Consequences）；
    * 线程安全（锁保护全部读写）—— 与 SQLite / Qdrant 的并发语义保持可比。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._collections: dict[str, _Collection] = {}
        self._bound_collection: str | None = None

    # --- 组合根注入点（与 QdrantVectorStore 同名同语义 —— 端口一致性要求） --- #

    def bind_collection(self, collection: str) -> None:
        """注入当前 collection 名（必须来自 `CollectionResolver.resolve()`）。"""
        if not collection or not collection.startswith(COLLECTION_PREFIX):
            raise ScopeViolationError("collection 名必须来自 CollectionResolver.resolve()（前缀 ib_）")
        self._bound_collection = collection

    def _require_collection(self) -> str:
        if not self._bound_collection:
            raise StartupError(
                "InMemoryVectorStore 未绑定 collection 名；必须由组合根经 bind_collection(...) 注入（FM-5）"
            )
        return self._bound_collection

    # --- collection 生命周期 --- #

    def ensure_collection(self, spec: CollectionSpec) -> CollectionInfo:
        with self._lock:
            existing = self._collections.get(spec.collection)
            if existing is None:
                self._collections[spec.collection] = _Collection(spec=spec, points={})
                return CollectionInfo(name=spec.collection, dim=spec.dim, distance=spec.distance, points_count=0)
            if existing.spec.dim != spec.dim:
                # 维度不一致必须显式报错（重建流程依赖此语义，FM-4）
                raise ValueError(
                    f"collection {spec.collection} 已存在且维度为 {existing.spec.dim}，"
                    f"与请求的 {spec.dim} 不符"
                )
            return CollectionInfo(
                name=spec.collection,
                dim=existing.spec.dim,
                distance=existing.spec.distance,
                points_count=len(existing.points),
            )

    def collection_info(self, spec: CollectionSpec) -> CollectionInfo | None:
        with self._lock:
            existing = self._collections.get(spec.collection)
            if existing is None:
                return None
            return CollectionInfo(
                name=existing.spec.collection,
                dim=existing.spec.dim,
                distance=existing.spec.distance,
                points_count=len(existing.points),
            )

    def list_collections(self) -> list[str]:
        with self._lock:
            return sorted(self._collections)

    def delete_by_collection(self, collection: str) -> bool:
        with self._lock:
            return self._collections.pop(collection, None) is not None

    # --- 写入 --- #

    def upsert(self, points: Sequence[VectorPoint], *, wait: bool) -> UpsertResult:
        with self._lock:
            collection = self._collections.get(self._require_collection())
            if collection is None:
                raise DependencyUnavailableError(
                    "已绑定的 collection 尚未创建（请先 ensure_collection）", dependency="vectorstore"
                )
            count = 0
            for point in points:
                payload = point.payload
                if not self._bound_collection.startswith(f"{COLLECTION_PREFIX}{payload.project_id}_v"):
                    raise ScopeViolationError(
                        f"向量点的 project_id 与已绑定 collection 不一致（collection={self._bound_collection}，"
                        f"point.project_id={payload.project_id}），拒绝写入"
                    )
                if len(point.vector) != collection.spec.dim:
                    raise ValueError(
                        f"向量维度 {len(point.vector)} 与 collection {collection.spec.collection} 的 "
                        f"{collection.spec.dim} 不符"
                    )
                collection.points[point.id] = ([float(v) for v in point.vector], payload)
                count += 1
            return UpsertResult(upserted=count, elapsed_ms=0)

    # --- 查询 --- #

    def query(
        self,
        vector: Vector,
        *,
        scope: Scope,
        top_k: int,
        score_threshold: float,
        filter: PointFilter | None,
    ) -> list[ScoredPoint]:
        """相似度检索。**`scope` 必填**；filter 与 scope 求交（恒含 project_id）。"""
        if filter is not None and filter.project_id != scope.project_id:
            # 显式拒绝：filter 与 scope 指向不同项目，是「错绑 scope」的信号（FM-2）
            raise ScopeViolationError("PointFilter.project_id 与 scope.project_id 不一致，拒绝执行查询")
        kb_ids = scope.kb_ids if scope.kb_ids is not None else (filter.kb_ids if filter else None)
        doc_ids = filter.doc_ids if filter else None

        with self._lock:
            collection = self._collections.get(self._require_collection())
            if collection is None:
                # **刻意不返回空列表**（与生产 Qdrant 对齐）：`query_points` 打到不存在的
                # 集合会抛错，而这里静默返回 `[]` 会让「集合缺失」伪装成「知识库为空」——
                # 两者的用户措辞与运维动作完全不同（AC-IB-14-02 的核心区分）。
                # 集合的存在性由组合根在启动期 `ensure_collection` 保证；
                # 运行期缺失即视为存储层异常，由 MOD-IB-15 转为 degraded。
                raise DependencyUnavailableError(
                    "已绑定的 collection 不存在（启动期 ensure_collection 未执行或集合被删）",
                    dependency="vectorstore",
                )
            if collection.spec.dim != len(vector):
                raise ValueError(
                    f"查询向量维度 {len(vector)} 与 collection {collection.spec.collection} 的 "
                    f"{collection.spec.dim} 不符"
                )
            hits: list[tuple[float, str, PointPayload]] = []
            for point_id, (stored_vector, payload) in collection.points.items():
                if not _matches(payload, project_id=scope.project_id, kb_ids=kb_ids, doc_ids=doc_ids):
                    continue
                score = cosine(vector, stored_vector)
                if score_threshold is not None and score < score_threshold:
                    continue
                hits.append((score, point_id, payload))
            hits.sort(key=lambda item: (-item[0], item[1]))
            limited = hits[: max(0, top_k)]
            return [ScoredPoint(id=pid, score=score, payload=payload) for score, pid, payload in limited]

    # --- 删除 --- #

    def _delete_where(self, scope: Scope, doc_ids: tuple[str, ...] | None) -> int:
        """删除内核：**只作用于已绑定的 collection**（跨版本残留由重建流程负责）。"""
        with self._lock:
            collection = self._collections.get(self._require_collection())
            if collection is None:
                return 0
            doomed = [
                pid
                for pid, (_vec, payload) in collection.points.items()
                if _matches(payload, project_id=scope.project_id, kb_ids=scope.kb_ids, doc_ids=doc_ids)
            ]
            for pid in doomed:
                collection.points.pop(pid, None)
            return len(doomed)

    def delete_by_doc(self, scope: Scope, doc_id: str) -> int:
        """按文档删除。**`scope` 必填**，filter 恒含 `project_id`（FM-3）。"""
        return self._delete_where(scope, (doc_id,))

    def delete_by_scope(self, scope: Scope) -> int:
        return self._delete_where(scope, None)

    def count(self, scope: Scope) -> int:
        with self._lock:
            collection = self._collections.get(self._require_collection())
            if collection is None:
                return 0
            return sum(
                1
                for _pid, (_vec, payload) in collection.points.items()
                if _matches(payload, project_id=scope.project_id, kb_ids=scope.kb_ids, doc_ids=None)
            )

    # --- 健康 / flush / 扩展位 --- #

    def health(self) -> HealthStatus:
        return HealthStatus(ok=True, detail="in-memory vector store", latency_ms=0)

    def flush(self) -> None:
        """替身为内存实现：写入本就即时可见，flush 是空操作（**不是**未实现）。"""
        return None

    def supports_hybrid_search(self) -> bool:
        """v1 **显式不支持**混合检索（OQ-IB-05 已评估未采纳）。

        返回 `False` 而非抛异常，也不静默降级 —— 调用方据此可给出明确提示。
        """
        return False


class QdrantVectorStore:
    """Qdrant 适配（IFC-IB-100~110 的生产实现；ADR-01）。

    * `qdrant_client` **延迟导入**：缺失时报 `DependencyUnavailableError`（含安装指引），
      不使本模块在离线环境不可导入；
    * gRPC `:6334` 为主通道，REST `:6333` 用于健康与回退（tech_stack §1）；
    * payload 一律由 `PointPayload.to_dict()` 生成 —— **字段名与契约逐字对齐**，
      避免「映射层悄悄改名」导致检索侧读不到（ADR-01 Consequences 的已知成本）。
    """

    def __init__(
        self,
        *,
        url: str,
        grpc_port: int = 6334,
        api_key: str | None = None,
        prefer_grpc: bool = True,
        timeout_s: float = 10.0,
    ) -> None:
        self._url = url.rstrip("/")
        self._grpc_port = grpc_port
        # 凭据只存内存中的私有属性，**绝不写日志、绝不进异常文本**（FM-8）
        self._api_key = api_key
        self._prefer_grpc = prefer_grpc
        self._timeout_s = timeout_s
        self._client: Any = None
        self._lock = threading.RLock()

    # --- 内部 --- #

    def _qdrant(self) -> Any:
        """惰性构造客户端。"""
        if self._client is not None:
            return self._client
        with self._lock:
            if self._client is None:
                try:
                    from qdrant_client import QdrantClient
                except ImportError as exc:
                    raise DependencyUnavailableError(
                        "qdrant-client 未安装（pip install qdrant-client）", dependency="qdrant"
                    ) from exc
                self._client = QdrantClient(
                    url=self._url,
                    grpc_port=self._grpc_port,
                    api_key=self._api_key,
                    prefer_grpc=self._prefer_grpc,
                    timeout=self._timeout_s,
                )
        return self._client

    def _models(self) -> Any:
        try:
            from qdrant_client import models
        except ImportError as exc:  # pragma: no cover - 与 _qdrant 同源
            raise DependencyUnavailableError("qdrant-client 未安装", dependency="qdrant") from exc
        return models

    def _build_filter(
        self, *, project_id: str, kb_ids: tuple[str, ...] | None, doc_ids: tuple[str, ...] | None
    ) -> Any:
        """构造 payload filter —— **全类唯一的 filter 构造点**。**`project_id` 恒在**（FM-1）。

        收敛成单点而非各方法各写一份：过滤器是隔离正确性的最后一道（也是唯一运行时）防线，
        复制粘贴式散落是 FM-1 这类缺陷的典型成因。
        """
        models = self._models()
        conditions = [
            models.FieldCondition(key="project_id", match=models.MatchValue(value=project_id)),
        ]
        if kb_ids is not None:
            conditions.append(models.FieldCondition(key="kb_id", match=models.MatchAny(any=list(kb_ids))))
        if doc_ids is not None:
            conditions.append(models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids))))
        return models.Filter(must=conditions)

    def _require_collection(self) -> str:
        """取装配期注入的 collection 名。

        **未绑定即报错**，绝不回退到 `ib_<project>_v1`：重建后 active 版本可能已是 `v2`，
        静默回退会把写入打到一个**已废弃的版本**上，表现为「入库成功但检索不到」这类极难定位的
        缺陷（FM-5）。宁可在装配期硬失败。
        """
        if not self._bound_collection:
            raise StartupError(
                "QdrantVectorStore 未绑定 collection 名；必须由组合根经 bind_collection("
                "CollectionResolver.resolve(...)) 注入（FM-5）"
            )
        return self._bound_collection

    def _assert_point_in_bound_collection(self, payload: PointPayload) -> None:
        """纵深防御：待写点的 `project_id` 必须与已绑定 collection 的项目一致（FM-1/FM-2）。"""
        collection = self._require_collection()
        if not collection.startswith(f"ib_{payload.project_id}_v"):
            raise ScopeViolationError(
                f"向量点的 project_id 与已绑定 collection 不一致（collection={collection}，"
                f"point.project_id={payload.project_id}），拒绝写入"
            )

    # --- collection 生命周期 --- #

    def ensure_collection(self, spec: CollectionSpec) -> CollectionInfo:
        client = self._qdrant()
        models = self._models()
        existing = self.collection_info(spec)
        if existing is not None:
            return existing
        client.create_collection(
            collection_name=spec.collection,
            vectors_config=models.VectorParams(
                size=spec.dim,
                distance=models.Distance.COSINE,
                on_disk=spec.on_disk_vectors,
            ),
            hnsw_config=models.HnswConfigDiff(
                m=spec.hnsw.m,
                ef_construct=spec.hnsw.ef_construct,
            ),
        )
        return CollectionInfo(name=spec.collection, dim=spec.dim, distance=spec.distance, points_count=0)

    def collection_info(self, spec: CollectionSpec) -> CollectionInfo | None:
        client = self._qdrant()
        try:
            info = client.get_collection(spec.collection)
        except Exception:  # noqa: BLE001 - 不存在即返回 None（Qdrant 抛 404 类异常）
            return None
        vectors = getattr(info.config.params, "vectors", None)
        dim = getattr(vectors, "size", spec.dim) if vectors is not None else spec.dim
        distance = getattr(vectors, "distance", "cosine")
        return CollectionInfo(
            name=spec.collection,
            dim=int(dim),
            distance=str(getattr(distance, "value", distance)).lower(),
            points_count=int(getattr(info, "points_count", 0) or 0),
        )

    def list_collections(self) -> list[str]:
        client = self._qdrant()
        response = client.get_collections()
        return sorted(item.name for item in response.collections)

    def delete_by_collection(self, collection: str) -> bool:
        client = self._qdrant()
        try:
            client.delete_collection(collection)
            return True
        except Exception:  # noqa: BLE001
            return False

    # --- 写入 --- #

    def upsert(self, points: Sequence[VectorPoint], *, wait: bool) -> UpsertResult:
        client = self._qdrant()
        models = self._models()
        if not points:
            return UpsertResult(upserted=0, elapsed_ms=0)
        collection = self._require_collection()
        for point in points:
            self._assert_point_in_bound_collection(point.payload)
        structs = [
            models.PointStruct(id=point.id, vector=[float(v) for v in point.vector], payload=point.payload.to_dict())
            for point in points
        ]
        started = time.perf_counter()
        client.upsert(collection_name=collection, points=structs, wait=wait)
        elapsed = int((time.perf_counter() - started) * 1000)
        return UpsertResult(upserted=len(structs), elapsed_ms=elapsed)

    # --- 查询 --- #

    def query(
        self,
        vector: Vector,
        *,
        scope: Scope,
        top_k: int,
        score_threshold: float,
        filter: PointFilter | None,
    ) -> list[ScoredPoint]:
        if filter is not None and filter.project_id != scope.project_id:
            raise ScopeViolationError("PointFilter.project_id 与 scope.project_id 不一致，拒绝执行查询")
        client = self._qdrant()
        collection = self._require_collection()
        kb_ids = scope.kb_ids if scope.kb_ids is not None else (filter.kb_ids if filter else None)
        doc_ids = filter.doc_ids if filter else None
        response = client.query_points(
            collection_name=collection,
            query=[float(v) for v in vector],
            query_filter=self._build_filter(project_id=scope.project_id, kb_ids=kb_ids, doc_ids=doc_ids),
            limit=max(0, top_k),
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        )
        out: list[ScoredPoint] = []
        for hit in response.points:
            out.append(
                ScoredPoint(id=str(hit.id), score=float(hit.score), payload=PointPayload.from_dict(hit.payload or {}))
            )
        return out

    # --- 删除 --- #

    def _delete_by(self, scope: Scope, doc_id: str | None) -> int:
        client = self._qdrant()
        models = self._models()
        collection = self._require_collection()
        count_filter = self._build_filter(
            project_id=scope.project_id, kb_ids=scope.kb_ids, doc_ids=((doc_id,) if doc_id is not None else None)
        )
        try:
            before = client.count(collection_name=collection, count_filter=count_filter, exact=True).count
            client.delete(
                collection_name=collection,
                points_selector=models.FilterSelector(filter=count_filter),
                wait=True,
            )
            after = client.count(collection_name=collection, count_filter=count_filter, exact=True).count
        except Exception as exc:  # noqa: BLE001 - 删除失败必须显式暴露（否则出现「幽灵文档」）
            raise DependencyUnavailableError(
                f"Qdrant 删除失败：{type(exc).__name__}", dependency="qdrant"
            ) from exc
        # 删除后同名 filter 的计数应归零；差额即被删除的点数（Qdrant 无 delete 返回值）
        return max(0, int(before) - int(after))

    def delete_by_doc(self, scope: Scope, doc_id: str) -> int:
        return self._delete_by(scope, doc_id)

    def delete_by_scope(self, scope: Scope) -> int:
        return self._delete_by(scope, None)

    def count(self, scope: Scope) -> int:
        client = self._qdrant()
        collection = self._require_collection()
        try:
            result = client.count(
                collection_name=collection,
                count_filter=self._build_filter(
                    project_id=scope.project_id, kb_ids=scope.kb_ids, doc_ids=None
                ),
                exact=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise DependencyUnavailableError(
                f"Qdrant count 失败：{type(exc).__name__}", dependency="qdrant"
            ) from exc
        return int(result.count)

    def health(self) -> HealthStatus:
        started = time.perf_counter()
        try:
            client = self._qdrant()
            client.get_collections()
            elapsed = int((time.perf_counter() - started) * 1000)
            return HealthStatus(ok=True, detail="qdrant", latency_ms=elapsed)
        except Exception as exc:  # noqa: BLE001 - 健康检查给出结论而非异常
            elapsed = int((time.perf_counter() - started) * 1000)
            return HealthStatus(ok=False, detail=f"qdrant 不可达：{type(exc).__name__}", latency_ms=elapsed)

    def flush(self) -> None:
        """Qdrant 的写入在其服务端落盘；客户端侧无需 flush（`wait=True` 已保证可见性）。"""
        return None

    def supports_hybrid_search(self) -> bool:
        """v1 **显式不支持**（OQ-IB-05）。"""
        return False

    # --- 组合根注入点 --- #

    def bind_collection(self, collection: str) -> None:
        """由组合根在装配期注入 collection 名（`IFC-IB-104/105/106/108` 签名不带该参数）。

        只能填入 `CollectionResolver.resolve()` 的产物：前缀必须是 `ib_`（FM-5）。
        """
        if not collection or not collection.startswith(COLLECTION_PREFIX):
            raise ScopeViolationError(
                "collection 名必须来自 CollectionResolver.resolve()（前缀 ib_）"
            )
        self._bound_collection: str | None = collection


def build_vector_store(cfg: Any) -> Any:
    """按配置构造 VectorStore（组合根单点调用）。"""
    if cfg.vectorstore.backend == "memory":
        return InMemoryVectorStore()
    from ib.config import read_secret

    return QdrantVectorStore(
        url=cfg.vectorstore.url,
        grpc_port=cfg.vectorstore.grpc_port,
        # 凭据经环境变量读取；值不进日志、不进异常文本
        api_key=read_secret("IB_QDRANT_API_KEY"),
    )
