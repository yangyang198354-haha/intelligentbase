"""
@module MOD-IB-01
@implements 17 个端口 Protocol（IFC-IB-021~022 / 032~033 / 051~053 / 061~063 / 071 /
            081~082 / 090~096 / 098 / 100~110 / 120~131 / 131~134 / 211~215 / 221~223 /
            287~292（R7 第 14 个端口 DefinitionDocumentStore）/
            310（R13 第 15 个端口 AccountStore）/
            339（REV-16-2 第 16 个端口 ExpertPromptStore）/
            357（REV-16-4 第 17 个端口 ConfigAuditStore））
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
from .errors import ConflictError, NotFoundError
from .types import (
    AccountStatus,
    AuthzContext,
    BlobRef,
    ChunkImageRecord,
    ChunkRecord,
    ChunkingSpec,
    CollectionInfo,
    CollectionSpec,
    ConfigAuditEntry,
    DefinitionDocument,
    DerivedView,
    DocumentRecord,
    EmbedderDescriptor,
    EgressDescriptor,
    ExpertPromptBundle,
    ExpertPromptDocumentRef,
    ExpertSpec,
    HealthStatus,
    LlmRole,
    OcrDescriptor,
    ParsedChunk,
    ParsedDocument,
    PointFilter,
    PromptDirectoryLayout,
    PromptLayer,
    PromptSaveResult,
    RawConfig,
    RetrievalResult,
    SaveResult,
    Scope,
    ScoredPoint,
    SessionRecord,
    SessionState,
    UpsertResult,
    UserRecord,
    UserRole,
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
    "AccountStore",
    "ExpertPromptStore",
    "ConfigAuditStore",
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


# =========================================================================== #
# MOD-IB-01 R13 增量（第 15 个端口，IFC-IB-310）
# =========================================================================== #
#
# 与 `LedgerRepository`（IFC-IB-120~131，第 4 个端口）的**区别是工件不同**：
#   * `LedgerRepository` 管**项目 / 知识库 / 文档 / 块**的元数据与状态机；
#   * `AccountStore` 管**账户与会话**（用户记录 + 会话摘要）。
# 二者共用同一 SQLite 文件与同一手写 scoped 迁移机制（ADR-18 / ADR-26），
# 但**只存凭据摘要**：口令 bcrypt 摘要、令牌 sha256 摘要（绝不存原文）。
#
# 所有需要「按会话令牌取主体」的路径**不得**各自校验，一律经组合根装配的
# `PrincipalResolver`（`SessionTokenResolver`，IFC-IB-322）唯一入口（ADR-22）。


@runtime_checkable
class AccountStore(Protocol):
    """账户与会话存储端口（IFC-IB-310，**恰好 13 个方法**，module_design.md §3 MOD-IB-01）。

    签名纪律（与基座既有端口一致）：
      * 时间一律以**定长 UTC 字符串**（`YYYY-MM-DDTHH:MM:SSZ`）传入，比较用字符串序；
        「当前时间」由调用方显式注入（`now=`），使时间成为**可测输入**而非环境副作用。
      * 阈值 / 窗口 / TTL 等策略参数由**调用方**计算，端口只做持久化的机械动作
        （例如 `record_login_failure` 只自增计数并回写 `locked_until`，不判阈值）。
      * 凭据摘要只进不出：本端口**没有**任何返回令牌原文或口令明文的方法。

    **fail-closed 语义**（REQ-NFR-IB-18）：`resolve_session` 对「已撤销 / 已过期 /
    不存在」的令牌一律返回 `None`；调用方据此拒绝，不得退化为「放行」。
    """

    def get_user_by_username(self, username: str) -> UserRecord | None:
        """按用户名取账户；不存在返回 `None`。"""
        ...

    def get_user(self, user_id: str) -> UserRecord | None:
        """按 `user_id` 取账户；不存在返回 `None`。"""
        ...

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: UserRole,
        project_id: str | None,
    ) -> UserRecord:
        """新建账户；用户名已存在抛 `ConflictError`（→ HTTP 409）。

        `password_hash` 必须是 **bcrypt 摘要**；本方法**不接收**也不回显口令明文。
        """
        ...

    def set_status(self, user_id: str, status: AccountStatus) -> UserRecord:
        """改账户状态（`active` / `disabled`）；不存在抛 `NotFoundError`。

        停用时**调用方**须同时 `revoke_session` 撤销该账户全部会话（IFC-IB-321）。
        """
        ...

    def set_password(
        self, user_id: str, password_hash: str, *, must_change: bool
    ) -> UserRecord:
        """改口令摘要（bcrypt）；不存在抛 `NotFoundError`。

        `must_change` 为 `True` 即置改密态（首登强制改密，ADR-20）。
        本方法**不接收**也不回显口令明文。
        """
        ...

    def list_users(self, project_id: str | None) -> list[UserRecord]:
        """列账户；`project_id=None` 表示 **admin 视角全量**，否则只列该项目绑定账户。"""
        ...

    def record_login_failure(self, user_id: str, *, now: str) -> UserRecord:
        """登录失败：自增 `failed_login_count` 并回写 `locked_until`（由调用方计算），返回更新后记录。

        **阈值与锁定窗口由调用方计算**（OQ-IB-12 未裁决前不启用，ADR-27）。
        """
        ...

    def reset_login_failures(self, user_id: str) -> None:
        """登录成功：清零失败计数与锁定态。"""
        ...

    def issue_session(
        self, user_id: str, token_digest: str, *, expires_at: str
    ) -> SessionRecord:
        """签发会话：写入**令牌摘要**（非原文）与到期时间，返回会话记录。"""
        ...

    def resolve_session(self, token_digest: str, *, now: str) -> SessionRecord | None:
        """按令牌摘要解析会话；**已撤销 / 已过期 / 不存在 → `None`**（fail-closed）。

        解析成功时（可选地）刷新 `last_seen_at`；刷新失败**不得**改变「有效」结论。
        """
        ...

    def renew_session(
        self, token_digest: str, *, new_expires_at: str, now: str
    ) -> SessionRecord | None:
        """续期：仅对「未撤销且未过期」的会话生效，返回更新后记录；否则 `None`（fail-closed）。"""
        ...

    def revoke_session(self, token_digest: str, *, now: str) -> None:
        """撤销单个会话（登出 / 改密 / 停用时按需批量调用）。幂等。"""
        ...

    def purge_expired_sessions(self, *, now: str) -> int:
        """清理已过期 / 已撤销的会话行，返回清理条数（维护任务用）。"""
        ...


# =========================================================================== #
# MOD-IB-01 REV-16-2 增量（第 16 个端口，IFC-IB-339）
# =========================================================================== #
#
# 与 `DefinitionDocumentStore`（IFC-IB-287，第 14 个端口）的**区别是工件不同**：
#   * `DefinitionDocumentStore` 管**结构与配置域**（专家元数据 / 路由 / 编排 / 工具授权）；
#   * `ExpertPromptStore` 管**提示词域**（主 / 兜底提示词 markdown）。
# 两域真源**按域唯一、内容不得重叠**（ADR-15-R1）；所有需要「按专家取提示词 / 合并派生」
# 的上层模块**不得**各自读目录或各自解析，一律由组合根在**装配期**经该端口取得并合并注入。
# 实现实例**按项目**构造（`<root>/<project_id>/` 一项目一目录树，[ARCH-ASSUMPTION-A10]）。
# 提示词目录根路径经 `IB_EXPERT_PROMPT_DIR` 注入（**只登记键名，不含值**）。


@runtime_checkable
class ExpertPromptStore(Protocol):
    """独立提示词目录存储端口（IFC-IB-339，**第 16 个端口**，**恰好 5 个方法**）。

    生产实现为 `FsExpertPromptStore`（本地 markdown 目录 + 原子替换 + 语义哈希乐观并发），
    离线替身为 `InMemoryExpertPromptStore`。契约段落落在 `module_design.md §3 MOD-IB-01/02`。

    纪律：
      * `load_bundle` **永不返回空白的系统提示词**：主缺失 → 回退兜底；兜底为空即非法（ADR-29）；
      * `save_layer` 先写临时文件再**原子替换**；`expected_hash` 不匹配 → `saved=False` 且
        **拒绝覆盖**（乐观并发，同 IFC-IB-289 精神）；保存失败**不破坏在用配置**（fail-safe）；
      * 错误体**只出** `path` / `code` / `message`，**不回显**提示词正文或任何凭据值。
    """

    def load_bundle(self, expert_name: str, *, doc_fallback: str) -> ExpertPromptBundle:
        """按专家取「主 / 兜底 / 生效」分层合并结果（IFC-IB-343）。

        `doc_fallback` 是定义文档侧的兜底字段（结构与配置域）；当提示词目录内
        `fallback.md` 缺失时作为兜底层的来源。**两者皆空 → 抛 `PromptNotFoundError`**。
        """
        ...

    def save_layer(
        self,
        expert_name: str,
        layer: PromptLayer,
        content: str,
        *,
        expected_hash: str | None,
    ) -> PromptSaveResult:
        """原子写回单层提示词（IFC-IB-344）。

        `layer="fallback"` 且 `content` 为空 → `saved=False`（兜底恒非空，ADR-29）；
        `expected_hash` 与当前不一致 → `saved=False`（乐观并发，**拒绝覆盖**）。
        """
        ...

    def list_refs(self) -> tuple[ExpertPromptDocumentRef, ...]:
        """列出目录内全部提示词文件引用（IFC-IB-345 的装载入口）。

        **目录不可读即报错**（fail-closed），**不返回空集合**（否则「读不到」与「本就为空」
        无法区分）。
        """
        ...

    def delete_layer(self, expert_name: str, layer: PromptLayer) -> None:
        """删除单层提示词文件。缺失即幂等返回（不抛异常）。"""
        ...

    def layout(self) -> PromptDirectoryLayout:
        """返回目录布局描述（IFC-IB-338 / [ARCH-ASSUMPTION-A10]）。

        **只描述布局（键名 / 文件模式 / 命名规则），不回显任何路径值。**
        """
        ...


# =========================================================================== #
# 配置审计（REV-16-4 / ADR-34）
# =========================================================================== #
#
# 配置审计端口（IFC-IB-357，**第 17 个端口**，**恰好 2 个方法**）。
# 生产实现为 `SqliteConfigAuditStore`（与账户台账同一 SQLite 账本，手写迁移
# `004_config_audit.sql`），离线替身为 `MemoryConfigAuditStore`。
#
# **追加型只读审计**（ADR-34）：
#   * 审计表是**只读审计**，**不是第二真源** —— 任何上层模块**不得**从审计表回读
#     配置来驱动行为；配置真源恒为定义文档 / 提示词目录。
#   * 端口**无 update / delete**：审计记录一旦写入即不可变（append-only）。
#   * 审计写入**不与配置写入事务耦合**：审计写失败**不得**改变保存结果，但**不得静默**
#     （须发结构化 WARN，字段白名单）。
#   * `changed_field_names` **只含字段名**，`detail_code` **只含字段名 / 错误码**，
#     **永不**含任何字段值或凭据。


@runtime_checkable
class ConfigAuditStore(Protocol):
    """配置审计存储端口（IFC-IB-357，**第 17 个端口**，**恰好 2 个方法**）。

    生产实现 `SqliteConfigAuditStore`（同一 SQLite 账本，追加型）；离线替身
    `MemoryConfigAuditStore`。

    **纪律：**
      * **恰好 2 个方法**（`record` / `list_by_project`）——**无 update / delete**；
      * 审计记录一经写入**不可变**（append-only 台账）；
      * **不是第二真源**：不得从审计表回读配置驱动行为；
      * 错误体 / 记录**只出**字段名与错误码，**永不**回显字段值或凭据（SC-3）。
    """

    def record(self, entry: ConfigAuditEntry) -> None:
        """追加一条配置审计记录（IFC-IB-360）。

        成功保存写 `result="saved"`；被拒保存写 `result="rejected"` 且 `detail_code`
        只含字段名 / 错误码。**add-only**：实现**不得**提供更新或删除路径。
        """
        ...

    def list_by_project(
        self,
        project_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[ConfigAuditEntry, ...]:
        """按项目列出审计记录（IFC-IB-359），稳定升序（`entry_id` 追加序）。

        审计表是套在**追加台账**上的读视图：分页必须稳定，故按写入序升序回放。
        """
        ...
