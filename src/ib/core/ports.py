"""
@module MOD-IB-01
@implements 14 个端口 Protocol（IFC-IB-021~022 / 032~033 / 051~053 / 061~063 / 071 /
            081~082 / 090~096 / 098 / 100~110 / 120~131 / 131~134 / 211~215 / 221~223 /
            287~292（R7 第 14 个端口 DefinitionDocumentStore））
@depends (none)
@author software-developer

**全部端口的唯一定义处**（module_design.md §2：「类型化契约与端口（定义于 MOD-IB-01）」）。
各端口的「契约段落」落在 `module_design.md §3` 对应 MOD 小节，见各方法 docstring 标注。

为什么端口集中在此：端口是**依赖倒置的枢轴**（ADR-01 / ADR-09）——
上层模块 import 端口，下层适配器实现端口，二者互不认识。
把端口放在 framework-free 的 `ib.core` 内，使「核心契约零第三方依赖」成为结构性事实。

签名纪律（module_design.md §1.4）：
  * `scope` 参数 **无默认值** —— 漏传即类型检查期报错，而非运行期静默全库检索。
  * 检索类返回类型回显 `scope` 供审计。
"""

from __future__ import annotations

from typing import BinaryIO, Protocol, Sequence, runtime_checkable

from .enums import DocStatus
from .types import (
    AuthzContext,
    BlobRef,
    ChunkImageRecord,
    ChunkRecord,
    ChunkingSpec,
    CollectionInfo,
    CollectionSpec,
    DefinitionDocument,
    DerivedView,
    DocumentRecord,
    EmbedderDescriptor,
    EgressDescriptor,
    ExpertSpec,
    HealthStatus,
    LlmRole,
    OcrDescriptor,
    ParsedChunk,
    ParsedDocument,
    PointFilter,
    RawConfig,
    RetrievalResult,
    SaveResult,
    Scope,
    ScoredPoint,
    SessionState,
    UpsertResult,
    ValidationReport,
    Vector,
    VectorPoint,
)

__all__ = [
    "ConfigurationSource",
    "AuthzPolicy",
    "DocumentParser",
    "OcrEngine",
    "Chunker",
    "PageRenderer",
    "Embedder",
    "CollectionResolver",
    "VectorStore",
    "LedgerRepository",
    "BlobStore",
    "LlmProvider",
    "SessionStore",
    "DefinitionDocumentStore",
]


# =========================================================================== #
# MOD-IB-02 配置
# =========================================================================== #


@runtime_checkable
class ConfigurationSource(Protocol):
    """配置源（IFC-IB-021，module_design.md §3 MOD-IB-02）。

    `load()` 只做**合并**（文件 + 环境变量），不做 schema 校验；
    校验由 `validate_required` 承担，以便「只报键名、不回显值」。
    """

    def load(self) -> RawConfig:
        """读取并合并配置。失败抛 `ConfigError`（只报键名）。"""
        ...


# =========================================================================== #
# MOD-IB-03 请求上下文与鉴权
# =========================================================================== #


@runtime_checkable
class AuthzPolicy(Protocol):
    """鉴权策略端口（IFC-IB-032~033，module_design.md §3 MOD-IB-03）。

    基座**不内置**业务鉴权模型；默认实现为 `DenyAllPolicy`（恒拒绝），
    且组合根在**未注入**该端口时**启动失败**（AC-IB-11-05：401/403 而非静默）。
    """

    def can_manage(self, ctx: AuthzContext) -> bool:
        """是否允许管理动作（上传 / 删除 / 重试 / 重建）。"""
        ...

    def can_query(self, ctx: AuthzContext) -> bool:
        """是否允许问答 / 检索。"""
        ...


# =========================================================================== #
# MOD-IB-05 解析器
# =========================================================================== #


@runtime_checkable
class DocumentParser(Protocol):
    """格式解析器（IFC-IB-051~053，module_design.md §3 MOD-IB-05）。

    OCR 与渲染以**参数注入**（不静态依赖 MOD-IB-06/08），避免横向耦合（§4.3）。
    """

    def supports(self, ext: str) -> bool:
        """本解析器是否处理该扩展名（小写，不含点）。"""
        ...

    def parse(
        self,
        source: BinaryIO,
        *,
        ocr: "OcrEngine",
        renderer: "PageRenderer",
        spec: ChunkingSpec,
    ) -> ParsedDocument:
        """解析为 `ParsedDocument`。整篇不可解析时抛 `ValidationError`；

        单页 / 单图失败**不得**抛异常，须降级为 `warnings` + 跳过该页（AC-IB-04-07）。
        """
        ...


# =========================================================================== #
# MOD-IB-06 OCR
# =========================================================================== #


@runtime_checkable
class OcrEngine(Protocol):
    """OCR 引擎端口（IFC-IB-061~063，module_design.md §3 MOD-IB-06）。"""

    def available(self) -> bool:
        """引擎是否可用（依赖已装且模型已就绪）。"""
        ...

    def recognize(self, image: bytes, fmt: str) -> str:
        """图像字节 -> 文本。`fmt ∈ {"png","jpeg"}`；**不可用时返回 `""`**（不抛异常）。"""
        ...

    def descriptor(self) -> OcrDescriptor:
        """引擎自述（进启动日志与 `/healthz/deps`）。"""
        ...


# =========================================================================== #
# MOD-IB-07 切分器
# =========================================================================== #


@runtime_checkable
class Chunker(Protocol):
    """切分器端口（IFC-IB-071，module_design.md §3 MOD-IB-07）。纯 CPU、纯逻辑、可离线单测。"""

    def split(self, doc: ParsedDocument, spec: ChunkingSpec) -> list[ParsedChunk]:
        """滑窗切分并过滤空块。"""
        ...


# =========================================================================== #
# MOD-IB-08 页面渲染
# =========================================================================== #


@runtime_checkable
class PageRenderer(Protocol):
    """PDF 页渲染端口（IFC-IB-081~082，module_design.md §3 MOD-IB-08）。"""

    def available(self) -> bool:
        """渲染能力是否可用。"""
        ...

    def render_page(self, source: BinaryIO, page_index: int, dpi: int) -> bytes | None:
        """渲染为 PNG 字节；**不可用 / 超限返回 `None`**（不抛异常）。"""
        ...


# =========================================================================== #
# MOD-IB-09 Embedding 与 collection 命名解析
# =========================================================================== #


@runtime_checkable
class Embedder(Protocol):
    """向量化端口（IFC-IB-090~096，module_design.md §3 MOD-IB-09）。

    **冷 / 热双路径刻意分离**（AC-IB-07-03）：
      * 冷路径 `embed_documents`：批量、长超时、多重试（入库可慢，但必须成批）；
      * 热路径 `embed_query`：单条、短超时、少重试（超时即抛 `DependencyUnavailableError`，
        由 MOD-IB-15 转 `degraded`）。
    """

    def dim(self) -> int:
        """向量维度。"""
        ...

    def model_id(self) -> str:
        """模型标识（进 `EmbedderDescriptor` 与 collection 指纹）。"""
        ...

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        timeout_s: float,
        max_retries: int,
        batch_size: int,
    ) -> list[Vector]:
        """**冷路径**：批量向量化。"""
        ...

    def embed_query(self, text: str, *, timeout_s: float) -> Vector:
        """**热路径**：单条向量化；超时 / 不可达抛 `DependencyUnavailableError`。"""
        ...

    def health(self) -> HealthStatus:
        """健康探测。"""
        ...

    def warmup(self) -> None:
        """预热（加载权重 / 建连）。失败不抛（记为 WARN）。"""
        ...

    def descriptor(self) -> EmbedderDescriptor:
        """模型自述；写入前须与 `CollectionSpec.dim` 断言一致。"""
        ...


@runtime_checkable
class CollectionResolver(Protocol):
    """collection 名解析 —— **唯一入口**（IFC-IB-098，FM-5 防护）。

    命名规则 `ib_<project_id>_v<collection_version>`。上层模块**禁止**自行拼接 collection 名。
    升级路径（若未来要求知识库级硬隔离）已收敛到本方法内部，不改调用方。
    """

    def resolve(self, scope: Scope, project: ProjectRecord) -> str:
        """把 (scope, project) 映射为 collection 名。"""
        ...


# =========================================================================== #
# MOD-IB-10 VectorStore
# =========================================================================== #


@runtime_checkable
class VectorStore(Protocol):
    """向量库窄端口（IFC-IB-100~110，**11 方法**，module_design.md §3 MOD-IB-10 / ADR-01-R1）。

    `scope` **必填无默认值**；filter **恒含** `project_id`（defense-in-depth，FM-1）。
    高级能力（混合检索）经**显式扩展方法**渐进暴露，且须声明「不支持」而非静默失败。
    """

    def ensure_collection(self, spec: CollectionSpec) -> CollectionInfo:
        """幂等创建 collection。"""
        ...

    def collection_info(self, spec: CollectionSpec) -> CollectionInfo | None:
        """查询 collection 现状；不存在返回 `None`。"""
        ...

    def list_collections(self) -> list[str]:
        """列出全部 collection（供启动期前缀一致性断言，FM-5）。"""
        ...

    def delete_by_collection(self, collection: str) -> bool:
        """整库删除（重建后清理旧版本）。"""
        ...

    def upsert(self, points: Sequence[VectorPoint], *, wait: bool) -> UpsertResult:
        """写入向量点；幂等键 = `doc_id` + `chunk_index`。"""
        ...

    def query(
        self,
        vector: Vector,
        *,
        scope: Scope,
        top_k: int,
        score_threshold: float,
        filter: PointFilter | None,
    ) -> list[ScoredPoint]:
        """相似度检索。**`scope` 必填**。"""
        ...

    def delete_by_doc(self, scope: Scope, doc_id: str) -> int:
        """按文档删除。**`scope` 必填**，filter 恒含 `project_id`。"""
        ...

    def delete_by_scope(self, scope: Scope) -> int:
        """按 scope 删除（项目级 / 知识库级）。"""
        ...

    def count(self, scope: Scope) -> int:
        """计数（**`scope` 必填**）。"""
        ...

    def health(self) -> HealthStatus:
        """健康探测。"""
        ...

    def flush(self) -> None:
        """把缓冲的写入落盘（IFC-IB-110；R1 更正后的第 11 个方法）。"""
        ...

    # --- 扩展位（v1 不实现，须显式声明「不支持」而非静默失败，OQ-IB-05）--- #
    def supports_hybrid_search(self) -> bool:
        """v1 恒返回 `False` —— 混合检索已评估未采纳（OQ-IB-05），端口预留扩展位。"""
        ...


# =========================================================================== #
# MOD-IB-11 台账
# =========================================================================== #


@runtime_checkable
class LedgerRepository(Protocol):
    """台账端口（IFC-IB-120~131，12 方法，module_design.md §3 MOD-IB-11）。

    台账是**可见性的唯一权威**。生产实现为 `SqliteLedgerRepository`（stdlib sqlite3，
    WAL + busy_timeout，**不经 Django ORM**，ADR-07-R1）。

    编号留痕：`IFC-IB-131` 在本端口（`list_chunks` / `list_orphan_doc_ids`）与
    `BlobStore.put` 处**重复使用**（上游文档编号算术缺陷）。本文件以 `MOD-IB-11:` 前缀消歧。
    """

    def create_document(
        self,
        scope: Scope,
        doc_name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        blob_ref: str | None,
    ) -> DocumentRecord:
        """登记文档（`status=pending`）。[MOD-IB-11: IFC-IB-120]"""
        ...

    def get_document(self, scope: Scope, doc_id: str) -> DocumentRecord | None:
        """按 scope 取文档；跨 scope 视为不存在。[MOD-IB-11: IFC-IB-121]"""
        ...

    def list_documents(
        self,
        scope: Scope,
        *,
        page: int,
        page_size: int,
        status: DocStatus | None,
    ) -> tuple[list[DocumentRecord], int]:
        """分页列表。返回 `(items, total)`。[MOD-IB-11: IFC-IB-122]"""
        ...

    def set_status(
        self,
        scope: Scope,
        doc_id: str,
        status: DocStatus,
        *,
        error_code: str | None,
    ) -> None:
        """状态迁移（状态机见 §6.1）。[MOD-IB-11: IFC-IB-123]"""
        ...

    def claim_pending(
        self, lease_owner: str, lease_seconds: int, limit: int
    ) -> list[DocumentRecord]:
        """条件 UPDATE 认领（多 worker 不重复处理）。[MOD-IB-11: IFC-IB-124]"""
        ...

    def renew_lease(self, doc_id: str, lease_owner: str, lease_seconds: int) -> bool:
        """续租；租约已易主返回 `False`。[MOD-IB-11: IFC-IB-125]"""
        ...

    def reap_expired_leases(self, now: str) -> int:
        """回收过期租约（崩溃任务回到 `pending`）。[MOD-IB-11: IFC-IB-126]"""
        ...

    def mark_indexed(
        self, scope: Scope, doc_id: str, collection_version: str, chunk_count: int
    ) -> None:
        """置 `indexed` + 记录版本与块数。**必须在向量落库成功之后**（ADR-07 写序）。"""
        ...

    def mark_deleted(self, scope: Scope, doc_id: str) -> None:
        """逻辑删除（删除重放对账用）。[MOD-IB-11: IFC-IB-128]"""
        ...

    def active_collection_version(self, project_id: str) -> str:
        """读路径的**唯一**版本真源（FM-4）。[MOD-IB-11: IFC-IB-129]"""
        ...

    def activate_collection_version(self, project_id: str, version: str) -> None:
        """原子切换 active 版本（重建「切换即完整」的落点）。[MOD-IB-11: IFC-IB-129]"""
        ...

    def assert_kb_in_project(self, project_id: str, kb_id: str) -> None:
        """归属断言；失败抛 `ScopeViolationError` -> HTTP **403**。[MOD-IB-11: IFC-IB-130]"""
        ...

    def list_chunks(self, scope: Scope, doc_id: str) -> list[ChunkRecord]:
        """列出某文档的块元数据。[MOD-IB-11: IFC-IB-131]"""
        ...

    def list_orphan_doc_ids(self, project_id: str, existing: list[str]) -> list[str]:
        """台账有记录但向量库已无对应点的文档（对账）。[MOD-IB-11: IFC-IB-131]"""
        ...

    # --- R2（M-02）：页面图 ↔ 文块关联行 ------------------------------------ #
    #
    # 三条方法的**归属**说明：它们服务 IFC-IB-278（写入）与 IFC-IB-283（读图端点），
    # 但类型与端口按 §2.1 纪律定义在 **MOD-IB-01**（若把这些签名放到 MOD-IB-13，
    # 会产生 `11 → 13` 的非法反向边，见 `ChunkImageRecord` docstring）。
    # 内存替身与 SQLite 实现**必须同步实现**（`port_conformance` 自检按参数名对拍）。

    def upsert_chunk_images(
        self, scope: Scope, doc_id: str, records: Sequence[ChunkImageRecord]
    ) -> int:
        """幂等写入页面图关联行（IFC-IB-278）。[MOD-IB-13: IFC-IB-278]

        语义与 `upsert_chunks` 同构：**先删后写（同 `doc_id`）**，故：
          * 重跑（重建 / 重试）不产生重复行（幂等键见 `ChunkImageRecord`）；
          * 新一次解析若产出**更少**的图，旧行不会成为「孤儿关联」而被残留。
        时机由 MOD-IB-13 保证：**向量写入成功之后、台账置 `indexed` 之前** ——
        使「`indexed` ⇒ 关联已就绪」成立（ADR-07 写序）。
        """
        ...

    def list_chunk_images(self, scope: Scope, doc_id: str) -> list[ChunkImageRecord]:
        """列出某文档的全部页面图关联行（按 `page_or_section` 升序）。[MOD-IB-23: IFC-IB-283]

        调用方（检索读路径 / 图片端点）**必须**先经本方法做 scope 过滤 ——
        跨 scope 一律视为**不存在**（返回空列表，而非报错），避免存在性探测。
        """
        ...

    def get_chunk_image(
        self, scope: Scope, doc_id: str, image_id: str
    ) -> ChunkImageRecord | None:
        """按 `(doc_id, image_id)` 取单行；跨 scope / 不存在一律返回 `None`。[MOD-IB-23: IFC-IB-283]"""
        ...


# =========================================================================== #
# MOD-IB-12 BlobStore
# =========================================================================== #


@runtime_checkable
class BlobStore(Protocol):
    """原文件存储端口（IFC-IB-131~134，4 方法，module_design.md §3 MOD-IB-12）。

    布局 `<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`（ADR-05）：
    三级目录使删除与隔离都可按前缀处理。

    编号留痕：本端口 4 条契约在上游文档编号为 `IFC-IB-131~134`，
    其中 `131` 与 `LedgerRepository.list_chunks` 冲突；以 `MOD-IB-12:` 前缀消歧。
    """

    def put(self, scope: Scope, doc_id: str, data: BinaryIO, ext: str) -> BlobRef:
        """内容寻址落盘。返回 `BlobRef(sha256, rel_path, size_bytes)`。[MOD-IB-12: IFC-IB-131]"""
        ...

    def get(self, blob_ref: BlobRef) -> bytes | None:
        """按 `BlobRef` 读取；不存在返回 `None`。[MOD-IB-12: IFC-IB-132]"""
        ...

    def delete(self, scope: Scope, doc_id: str) -> int:
        """按 (scope, doc_id) 前缀删除，返回删除文件数。[MOD-IB-12: IFC-IB-133]"""
        ...

    def exists(self, blob_ref: BlobRef) -> bool:
        """是否已存在（内容寻址去重）。[MOD-IB-12: IFC-IB-134]"""
        ...


# =========================================================================== #
# MOD-IB-20 LLM
# =========================================================================== #


@runtime_checkable
class LlmProvider(Protocol):
    """LLM 端点端口（IFC-IB-211~215，module_design.md §3 MOD-IB-20 / ADR-08）。

    路由 / 专家 / 聚合三个角色在端口**内部**构造，provider 细节不外泄到编排层。
    """

    def build_router(self) -> LlmRole:
        """路由分类角色（**temperature=0**，确定性，AC-IB-09-07）。"""
        ...

    def build_expert(self, spec: ExpertSpec) -> LlmRole:
        """专家作答角色。"""
        ...

    def build_aggregator(self) -> LlmRole:
        """结果聚合角色。"""
        ...

    def health(self) -> HealthStatus:
        """健康探测。"""
        ...

    def describe_egress(self) -> EgressDescriptor:
        """数据外发边界声明（AC-IB-12-05）。"""
        ...


# =========================================================================== #
# MOD-IB-21 会话
# =========================================================================== #


@runtime_checkable
class SessionStore(Protocol):
    """会话状态端口（IFC-IB-221~223，module_design.md §3 MOD-IB-21）。

    语义 fail-closed：`load` 遇 `session_key` 前缀与当前 `project_id` 不符时**拒绝**
    （返回 `None`），而不是返回他项目会话（FM-7）。
    """

    def load(self, session_key: str) -> SessionState | None:
        """读取会话状态。"""
        ...

    def save(self, session_key: str, state: SessionState) -> None:
        """写入会话状态。"""
        ...

    def delete(self, session_key: str) -> None:
        """删除会话状态。"""
        ...


# =========================================================================== #
# MOD-IB-02 定义文档（R7 增量，第 14 个端口）
# =========================================================================== #


@runtime_checkable
class DefinitionDocumentStore(Protocol):
    """定义文档存储端口（IFC-IB-287~292，module_design.md §2.2 R7 增记 / §3 MOD-IB-02）。

    **单一真源的可替换边界**（ADR-15 第三层）：定义文档的「装载 / 校验 / 派生 / 写回」
    全经由本端口，生产实现为 `FileDefinitionDocumentStore`（本地文件 + 原子替换 + 语义哈希
    乐观并发），测试替身为 `InMemoryDefinitionDocumentStore`。

    纪律：
      * `validate` / `derive` 必须是**纯函数**（同输入同输出、无副作用、离线可测）。
      * `load` 遇缺失 / 不可解析文件时**不得**静默回退为空文档 —— 抛 `ConfigError`（可读错误）。
      * `save` 先写临时文件再**原子替换**；`expected_content_hash` 不匹配时**拒绝覆盖**。
    """

    def load(self, project_id: str) -> DefinitionDocument:
        """装载定义文档（IFC-IB-288）。

        缺失 / 不可解析 → 抛 `ConfigError`（只报可读原因，**不静默回退空文档**）。
        """
        ...

    def save(
        self,
        project_id: str,
        doc: DefinitionDocument,
        *,
        expected_content_hash: str | None,
    ) -> SaveResult:
        """原子写回定义文档（IFC-IB-289）。

        临写 + 原子替换；`expected_content_hash` 与当前不一致 → `SaveResult(conflict=True)`
        且**不覆盖**（乐观并发）。
        """
        ...

    def validate(self, doc: DefinitionDocument) -> ValidationReport:
        """完备性校验（IFC-IB-290）。**纯函数**，≥7 类校验项，framework-free。"""
        ...

    def derive(self, doc: DefinitionDocument) -> DerivedView:
        """派生只读视图（IFC-IB-291）。**纯函数**；结果**不落盘、不可反写**。"""
        ...

    def editable_field_whitelist(self) -> frozenset[str]:
        """可编辑字段白名单（IFC-IB-292）。白名单外字段界面**不得写入**。"""
        ...
