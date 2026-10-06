"""
@module MOD-IB-01
@implements IFC-IB-001 .. IFC-IB-010 （全部不可变数据结构；逐字段名 + 类型 + 可空性）
            IFC-IB-337 ~ 342（REV-16-2 提示词分层 / 工具参数 / FreeArk 对齐数据结构）
@depends (none)
@author software-developer

契约层数据结构。**framework-free**：仅使用 stdlib `dataclasses` / `typing`。

规则（module_design.md §2.1）：
  * 全部为 `frozen=True, slots=True` 的 dataclass —— 不可变、不可赋属性、内存紧凑。
  * 凡 `... | None` 即表示可空；无 `| None` 即表示必填且非空。
  * 凡 `tuple[...]` 即表示有序不可变集合；凡 `list[...]` 即表示有序可变集合（文档原文如此，
    例如 `ParsedDocument.chunks` / `RetrievalResult.hits`）。
  * 本文件**不得** import 任何第三方包，也不得 import 本包以外的模块 —— 它是全仓的叶子节点。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence, TypeAlias

# --------------------------------------------------------------------------- #
# 类型别名
# --------------------------------------------------------------------------- #

#: 稠密向量。长度必须等于 `CollectionSpec.dim` / `EmbedderDescriptor.dim`。
Vector: TypeAlias = Sequence[float]

DistanceLiteral: TypeAlias = Literal["cosine"]
SourceKindLiteral: TypeAlias = Literal["text", "image_ocr", "page_scan"]
DocStatusLiteral: TypeAlias = Literal["pending", "parsing", "indexed", "failed"]
DegradeReasonLiteral: TypeAlias = Literal[
    "embedding_unavailable", "vectorstore_unavailable", "timeout"
]

#: 提示词分层（IFC-IB-337，REV-16-2；ADR-29）：`main` 主提示词（**可缺**）/
#: `fallback` 兜底提示词（**不得缺**）。分层并存，主缺失时回退兜底。
PromptLayer: TypeAlias = Literal["main", "fallback"]

#: 工具参数类型（IFC-IB-340，REV-16-2；ADR-30）。纯标准库，零第三方依赖。
ToolParamTypeLiteral: TypeAlias = Literal["int", "float", "bool", "str"]


# --------------------------------------------------------------------------- #
# 作用域与 collection（IFC-IB-001 / IFC-IB-002）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Scope:
    """检索 / 存储 / 台账的作用域 —— **多项目隔离的类型层基石**（IFC-IB-001）。

    `kb_ids is None` 表示「项目内全部知识库」（**不是**「不过滤」，见 FM-1）：
    filter 仍恒含 `project_id`，只是不加 `kb_id` 约束。
    """

    project_id: str
    kb_ids: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("Scope.project_id 不得为空")
        if self.kb_ids is not None and len(self.kb_ids) == 0:
            # 空元组是「无知识库」这种自相矛盾的作用域 —— 显式拒绝，避免被误当成「全部」。
            raise ValueError("Scope.kb_ids 为空元组；请用 None 表示项目内全部知识库")


@dataclass(frozen=True, slots=True)
class HnswParams:
    """Qdrant HNSW 索引参数（收敛进 `CollectionSpec`，不暴露直连 SDK 的灵活性）。"""

    m: int = 16
    ef_construct: int = 128
    ef_search: int = 64


@dataclass(frozen=True, slots=True)
class CollectionSpec:
    """collection 声明（IFC-IB-002）。`collection` 名必须来自 `CollectionResolver.resolve()`。"""

    collection: str
    dim: int
    distance: DistanceLiteral = "cosine"
    on_disk_vectors: bool = False
    hnsw: HnswParams = field(default_factory=HnswParams)


@dataclass(frozen=True, slots=True)
class CollectionInfo:
    """collection 现状（IFC-IB-010）。"""

    name: str
    dim: int
    distance: str
    points_count: int


# --------------------------------------------------------------------------- #
# 向量点位（IFC-IB-003 / 004 / 005 / 006）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class PointPayload:
    """向量点 payload（IFC-IB-003）。**冗余携带 project_id / kb_id** 作为纵深防御（FM-1）。

    即使某一层漏了 collection 级隔离，payload filter 仍能拦住跨项目命中；
    反之亦然。两层冗余是刻意的。
    """

    project_id: str
    kb_id: str
    doc_id: str
    doc_name: str
    chunk_index: int
    content: str
    locator: str
    source_kind: SourceKindLiteral
    page_or_section: str
    content_hash: str
    indexed_model: str
    indexed_dim: int
    created_at: str
    blob_ref: str | None
    schema_version: int

    def to_dict(self) -> dict[str, Any]:
        """转成 JSON 安全的普通 dict（供 Qdrant payload 使用）。"""
        return {
            "project_id": self.project_id,
            "kb_id": self.kb_id,
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "locator": self.locator,
            "source_kind": self.source_kind,
            "page_or_section": self.page_or_section,
            "content_hash": self.content_hash,
            "indexed_model": self.indexed_model,
            "indexed_dim": self.indexed_dim,
            "created_at": self.created_at,
            "blob_ref": self.blob_ref,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PointPayload":
        """从 Qdrant payload 还原。缺字段即抛 KeyError（不静默补默认值）。"""
        return cls(
            project_id=raw["project_id"],
            kb_id=raw["kb_id"],
            doc_id=raw["doc_id"],
            doc_name=raw["doc_name"],
            chunk_index=int(raw["chunk_index"]),
            content=raw["content"],
            locator=raw["locator"],
            source_kind=raw["source_kind"],
            page_or_section=raw["page_or_section"],
            content_hash=raw["content_hash"],
            indexed_model=raw["indexed_model"],
            indexed_dim=int(raw["indexed_dim"]),
            created_at=raw["created_at"],
            blob_ref=raw.get("blob_ref"),
            schema_version=int(raw["schema_version"]),
        )


@dataclass(frozen=True, slots=True)
class VectorPoint:
    """待写入的向量点（IFC-IB-004）。`id` 的幂等键 = `doc_id` + `chunk_index`（§6.2）。"""

    id: str
    vector: Vector
    payload: PointPayload


@dataclass(frozen=True, slots=True)
class ScoredPoint:
    """带分数的命中点（IFC-IB-005）。"""

    id: str
    score: float
    payload: PointPayload


@dataclass(frozen=True, slots=True)
class PointFilter:
    """向量库 payload 过滤条件（IFC-IB-006）。

    `project_id` **必填且无默认值** —— 结构性防御 FM-1/FM-3。
    """

    project_id: str
    kb_ids: tuple[str, ...] | None = None
    doc_ids: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class UpsertResult:
    """写入结果（IFC-IB-010）。"""

    upserted: int
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """依赖健康状态（IFC-IB-010）。`detail` 不得包含凭据或正文。"""

    ok: bool
    detail: str = ""
    latency_ms: int | None = None


# --------------------------------------------------------------------------- #
# Embedding 与切分（IFC-IB-009 / IFC-IB-010）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class EmbedderDescriptor:
    """embedding 模型自述（IFC-IB-010）。写入前须与 `CollectionSpec.dim` 断言一致。"""

    model_id: str
    dim: int
    normalized: bool
    max_tokens: int
    device: str


@dataclass(frozen=True, slots=True)
class ChunkingSpec:
    """切分参数（IFC-IB-009）。参数变更**不自动**作用于既有文档（AC-IB-05-03）。"""

    chunk_size: int
    chunk_overlap: int
    normalizer_version: str = "v1"


@dataclass(frozen=True, slots=True)
class ParsedChunk:
    """解析产出的原始块（IFC-IB-009）。"""

    content: str
    page_or_section: str
    source_kind: SourceKindLiteral
    locator: str
    image_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """解析产出（IFC-IB-009）。`warnings` 承载页级降级说明（如「未识别到文本」）。"""

    chunks: list[ParsedChunk]
    page_count: int
    warnings: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# 检索结果（IFC-IB-007）—— ADR-13 的核心契约
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """单条检索命中（供专家使用）。"""

    doc_id: str
    doc_name: str
    content: str
    score: float
    page_or_section: str
    source_kind: str
    locator: str


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """检索结果（IFC-IB-007）。

    **两态可区分**（AC-IB-14-02）：
      * 知识库为空：`degraded=False, hits=[]`
      * 依赖故障：`degraded=True, degrade_reason != None, hits=[]`

    `scope` 回显供审计；`candidate_count` 与分数量级是阈值校准（[TBD-T12]）的证据出口。
    """

    hits: list[RetrievedChunk]
    degraded: bool
    degrade_reason: DegradeReasonLiteral | None
    scope: Scope
    elapsed_ms: int
    candidate_count: int


# --------------------------------------------------------------------------- #
# 页面图 ↔ 文块关联（R2 新增：IFC-IB-276 / IFC-IB-279）
#
# 根因（留痕，M-02）：页面文字块与水印/插图 OCR 块此前出自**两次解析产出**，
# 检索命中文字块时**无任何指向同页图片的引用** —— 图明明在库里却取不到。
# R2 把该关联**在入库期固化**（独立结构 + 独立关联表），而不是在检索期做启发式猜测。
#
# 字段集不变式（**硬约束**）：本节全部为**追加**结构；既有 `ParsedChunk`（IFC-IB-009）
# 与 `RetrievedChunk`（IFC-IB-007）的字段集**一字不动** —— 故不向二者追加任何字段。
# --------------------------------------------------------------------------- #

#: 页面图来源：`embedded_image`（页内嵌图，取出后 OCR/留存）；`page_scan`（整页栅格化）。
PageImageSourceKindLiteral: TypeAlias = Literal["embedded_image", "page_scan"]


@dataclass(frozen=True, slots=True)
class PageImageRef:
    """一条页面图引用（IFC-IB-276，定义于 MOD-IB-01）。

    `image_id` 在**同一文档内**唯一（幂等键的组成部分，见 `ChunkImageRecord`）；
    `page_or_section` 是该图与同页文字块**共享的绑定键** —— 二者相同即完成绑定，
    无需在检索期做任何猜测（M-02 的核心机制）。
    `blob_ref` 为空表示该图**字节不可得**（OCR 后即弃的历史文档）：此时关联行仍登记，
    但取图端点返回 404/503，且流事件不为其发 `related_images`（§7.4 降级行）。
    """

    image_id: str
    page_or_section: str
    source_kind: PageImageSourceKindLiteral
    locator: str
    blob_ref: str | None = None
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class PageImageBinding:
    """**一页**的全部页面图（IFC-IB-276）—— `bind_page_images` 的聚合产出单元。"""

    project_id: str
    kb_id: str
    doc_id: str
    page_or_section: str
    images: tuple[PageImageRef, ...]


@dataclass(frozen=True, slots=True)
class RelatedImageItem:
    """问答回显用的单张关联图（IFC-IB-276）。

    **只含 `image_id` + `url_path`（站内相对路径），绝不含图片字节/base64**——
    帧体积有界，不阻塞流（IFC-IB-282）。
    """

    image_id: str
    doc_id: str
    doc_name: str
    page_or_section: str
    url_path: str


@dataclass(frozen=True, slots=True)
class RelatedImagesPayload:
    """`related_images` 流事件的载荷（IFC-IB-282 / 类型定义于 IFC-IB-276）。

    顺序即**服务端给出的顺序**（按 `page_or_section` 升序）；前端**不得重排**（IFC-IB-284）。
    空元组是**合法**值，但此时**不发**该事件（IFC-IB-282：无图不发空事件）。
    """

    images: tuple[RelatedImageItem, ...]


@dataclass(frozen=True, slots=True)
class ChunkImageRecord:
    """页面图 ↔ 文块关联的**持久化模型**（IFC-IB-279）。

    > 归属说明：本条 IFC 由 **MOD-IB-13** 的持久化流程（`persist_page_images`）拥有，
    > 但**类型定义落在 MOD-IB-01** —— 因为台账端口（MOD-IB-11）与端口契约（MOD-IB-01）
    > 均需在其**签名**中引用该类型；若定义在 MOD-IB-13，会产生 `11 → 13` 与 `01 → 13`
    > 两条**非法反向边**（违反 §4「编号即拓扑序」）。故按 §2.1 的既有纪律
    > （「类型化契约与端口定义于 MOD-IB-01」）落在此处。

    **幂等键** = `(project_id, kb_id, doc_id, page_or_section, image_id)`：
    重跑（重建 / 重试）**覆盖同一行**，不产生重复（IFC-IB-278）。
    """

    project_id: str
    kb_id: str
    doc_id: str
    page_or_section: str
    image_id: str
    source_kind: str
    locator: str
    blob_ref: str | None
    doc_name: str
    created_at: str

    @staticmethod
    def idempotent_key(
        project_id: str, kb_id: str, doc_id: str, page_or_section: str, image_id: str
    ) -> tuple[str, str, str, str, str]:
        """幂等键的**唯一构造点**（避免各处手拼五元组顺序写错）。"""
        return (project_id, kb_id, doc_id, page_or_section, image_id)


# --------------------------------------------------------------------------- #
# 台账记录（IFC-IB-008）与项目 / 知识库
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """文档台账记录（IFC-IB-008）。租约字段见 §6.3。"""

    doc_id: str
    project_id: str
    kb_id: str
    doc_name: str
    ext: str
    size_bytes: int
    content_sha256: str
    blob_ref: str | None
    status: DocStatusLiteral
    error_code: str | None
    chunk_count: int
    indexed_collection_version: str | None
    target_collection_version: str | None
    lease_owner: str | None
    lease_expires_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    """块元数据（台账侧；`content` 不入台账，只存 hash 与定位信息 —— 减小台账体积与泄漏面）。"""

    chunk_id: str
    doc_id: str
    project_id: str
    kb_id: str
    chunk_index: int
    content_hash: str
    locator: str
    source_kind: str
    page_or_section: str
    indexed_model: str
    indexed_dim: int


@dataclass(frozen=True, slots=True)
class KbRecord:
    """知识库记录。"""

    kb_id: str
    project_id: str
    name: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    """项目记录（IFC-IB-008 邻近结构）。

    `active_collection_version` 是**读路径的唯一版本真源**（FM-4 防护）。
    """

    project_id: str
    name: str
    active_collection_version: str
    embedding_model_id: str
    dim: int
    created_at: str


# --------------------------------------------------------------------------- #
# 请求上下文（IFC-IB-031）—— 两段式上下文（ADR-09 / §1.4）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class AuthzContext:
    """鉴权主体。`roles` 由接入方注入的 `AuthzPolicy` 解释，基座不内置角色语义。"""

    actor_id: str
    project_id: str
    roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RequestContext:
    """请求级机械上下文（IFC-IB-031）。

    **机械段**（骨架可见但不解释语义）：`request_id` / `session_key` / `scope_token`。
    **语义段**（骨架完全不可见）：知识库范围经工具闭包与检索客户端构造期绑定 —— 刻意
    不作为字段出现在此处（ADR-09）。
    """

    request_id: str
    session_key: str
    scope_token: str
    authz: AuthzContext


# --------------------------------------------------------------------------- #
# 配置读取原始载体（供 IFC-IB-021 端口签名使用）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RawConfig:
    """配置文件 + 环境变量合并后的**原始**键值（未经 schema 校验）。

    值可能是任意 JSON/YAML 标量或嵌套映射；`source` 记录来源以便启动期诊断。
    """

    values: Mapping[str, Any]
    source: str = "unknown"


# --------------------------------------------------------------------------- #
# 上传 / 生命周期（IFC-IB-141 ~ IFC-IB-145）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class BlobRef:
    """内容寻址的原文件引用（IFC-IB-131 BlobStore.put 返回值）。

    `sha256` 同时是**幂等键**（同内容不重复占空间，§6.2）。
    """

    sha256: str
    rel_path: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    """通过三重校验的上传描述（IFC-IB-141）。"""

    filename: str
    ext: str
    size_bytes: int
    detected_mime: str


@dataclass(frozen=True, slots=True)
class ProcessReport:
    """一批 `process_pending` 的结果（IFC-IB-143）。"""

    processed: int
    succeeded: int
    failed: int
    skipped: int


@dataclass(frozen=True, slots=True)
class DeleteReport:
    """文档删除结果（IFC-IB-144）。"""

    vectors_deleted: int
    blob_deleted: bool
    ledger_deleted: bool


# --------------------------------------------------------------------------- #
# 索引重建（IFC-IB-151 ~ IFC-IB-153）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RebuildPlan:
    """重建计划（IFC-IB-151）。`to_version` = `fingerprint(...)` 前 8 位十六进制。"""

    from_version: str
    to_version: str
    target_collection: str
    doc_count: int
    changed_factors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RebuildJob:
    """重建任务（IFC-IB-152）。`state` 取值见 `RebuildState`。"""

    job_id: str
    state: str


@dataclass(frozen=True, slots=True)
class RebuildProgress:
    """重建推进结果（IFC-IB-153）。`done=True` 才允许 `activate_version`。"""

    indexed: int
    failed: int
    pending: int
    done: bool


# --------------------------------------------------------------------------- #
# 工具（IFC-IB-181 / 183）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ToolResult:
    """工具调用结果（IFC-IB-162 / 181）。

    `degraded` 使「工具层降级」可被编排层看见并转成 `degraded` 流事件。
    """

    ok: bool
    content: str
    degraded: bool = False
    degrade_reason: DegradeReasonLiteral | None = None


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """工具声明（IFC-IB-181）。`description` 进入能力摘要（IFC-IB-182）。

    `parameters` 是**业务参数**的 JSON Schema（不含 `scope`/`retrieval` 这类构造期注入项），
    供 function-calling 把工具交给 LLM 时描述「该传什么参数」。缺省 `None` 表示无业务参数
    （退化为无参工具，`parameters={"type":"object","properties":{}}`）。
    """

    name: str
    description: str
    needs_scope: bool = False
    parameters: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    """注册表中的工具条目（IFC-IB-181）。"""

    spec: ToolSpec
    fn: Any  # Callable[..., ToolResult]


@dataclass(frozen=True, slots=True)
class BoundTool:
    """已绑定 scope 的工具（IFC-IB-183）。

    **构造期闭包绑定**的结果形态：`callable` 是**无参**的（骨架只见无参工具），
    scope 已被封闭在闭包内（ADR-09 / §1.4）。`parameters` 从 `ToolSpec.parameters`
    原样透传（业务参数 JSON Schema，供 function-calling 使用）。
    """

    name: str
    description: str
    callable: Any  # Callable[[], ToolResult] 或 Callable[[str], ToolResult]
    parameters: dict[str, Any] | None = None


# --------------------------------------------------------------------------- #
# 专家与路由（IFC-IB-171 / 201）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ExpertSpec:
    """专家规格（IFC-IB-171）。framework-free 纯数据 —— 不 import langchain/langgraph。"""

    name: str
    cn_label: str
    keywords: tuple[str, ...]
    is_data_expert: bool
    fallback_prompt: str
    is_delegating: bool
    is_default: bool


@dataclass(frozen=True, slots=True)
class Message:
    """对话消息（路由历史 / 编排 State）。

    `role ∈ {system, user, assistant}`。
    """

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """路由判定结果（IFC-IB-201）。`experts` 有序，首个为主专家。"""

    experts: list[str]
    tier: str
    confidence: float


# --------------------------------------------------------------------------- #
# LLM（IFC-IB-211 / 215）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LlmRole:
    """已构造的 LLM 角色（路由 / 专家 / 聚合）。

    `impl` 承载 provider 私有对象（如 langchain 的 ChatOpenAI 实例），
    类型为 `Any` 以确保 MOD-IB-01 **不静态依赖** langchain（framework-free 不变式）。
    """

    role: str
    temperature: float
    impl: Any = None


@dataclass(frozen=True, slots=True)
class EgressDescriptor:
    """数据外发边界声明（IFC-IB-215 / REQ-NFR-IB-08 / AC-IB-12-05）。

    必须输出至启动日志与 `GET /healthz/deps`，使外发行为在**配置层可追溯**。
    """

    remote: bool
    endpoint_host: str
    data_categories: list[str]


@dataclass(frozen=True, slots=True)
class OcrDescriptor:
    """OCR 引擎自述（IFC-IB-063）。"""

    engine_id: str
    available: bool


# --------------------------------------------------------------------------- #
# 会话与流（IFC-IB-221 / 224；R8 追加 IFC-IB-298~301）
# --------------------------------------------------------------------------- #


#: 会话持久化策略（IFC-IB-299）。**默认 `in_process`**（进程内、重启即失忆，v1 刻意保守）。
#: 取值域 `{"in_process","external"}` —— `external` 只**声明值域**，v1 不提供适配器
#: （[ARCH-ASSUMPTION-A8] / ADR-17 约束 4）。
SessionPersistencePolicy: TypeAlias = Literal["in_process", "external"]

#: 「待确认状态丢失」的**唯一结局**（IFC-IB-299）。**唯一取值**使「重启丢弃待确认状态 =
#: 安全失败」成为**类型层事实**而非纪律约定（AC-IB-20-05）。
SessionStateLossOutcome: TypeAlias = Literal["fail_closed_restart_required"]

#: `SessionPersistencePolicy` 的默认值（与 IFC-IB-304 的 `IB_SESSION_PERSISTENCE_POLICY` 对齐）。
DEFAULT_SESSION_PERSISTENCE_POLICY: SessionPersistencePolicy = "in_process"

#: `SessionStateLossOutcome` 的唯一取值常量（便于调用方引用而不硬编码字符串）。
SESSION_STATE_LOSS_OUTCOME: SessionStateLossOutcome = "fail_closed_restart_required"


@dataclass(frozen=True, slots=True)
class CitationItem:
    """引用的**定位信息**（IFC-IB-300）。

    **只给定位，不给正文**：`locator` 指向原始文档中的位置（页码 / 章节 / 锚点），
    `score` 是检索得分供调用方按相关性呈现。**绝不内联字节、不含正文全文** ——
    内联正文会让完成事件的体积随命中数线性膨胀（几百 KB 级），并诱发「回答与引用
    各带一份同样的文本」的漂移。
    """

    doc_id: str
    doc_name: str
    page_or_section: str
    locator: str
    score: float


@dataclass(frozen=True, slots=True)
class CompletionPayload:
    """完成事件的结构化产物（IFC-IB-300；AC-IB-19-02 / 19-05）。

    `citations` **可为空元组**（无引用即空、**不臆造**引用 —— 结构事实而非纪律约定）；
    `had_content` 标记本次交互是否产出了可交付正文（空内容边界）。
    """

    citations: tuple[CitationItem, ...] = ()
    had_content: bool = True


@dataclass(frozen=True, slots=True)
class ConfirmationPrompt:
    """确认呈递的**业务话术载体**（IFC-IB-301）。

    `summary` **由接入方构造**，骨架**不生成**任何业务话术（ADR-09 / ADR-17 约束 2）；
    `expert_name` 只作定位用。骨架只做「**呈递 + 等待 + 回传**」的通道。
    """

    gate_id: str
    expert_name: str
    summary: str


@dataclass(frozen=True, slots=True)
class ConfirmationDecision:
    """确认决策（IFC-IB-301）。`approved=False` 表示明确拒绝（同样是一条决策）。"""

    gate_id: str
    approved: bool


@dataclass(frozen=True, slots=True)
class ConfirmationGateState:
    """待确认中间态（IFC-IB-301；AC-IB-20-04）。

    `decision is None` = **待决策**（尚未收到决策，该次执行保持在此中间态）。
    """

    gate_id: str
    prompt: ConfirmationPrompt
    decision: ConfirmationDecision | None = None


@dataclass(frozen=True, slots=True)
class SessionTurn:
    """单轮会话记录（IFC-IB-298；补齐 `IFC-IB-221/222` 的悬置引用）。

    `citations` 为**定位信息**（IFC-IB-300），默认空元组。
    """

    role: str
    text: str
    citations: tuple[CitationItem, ...] = ()
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class SessionState:
    """会话状态（IFC-IB-221；字段级定义由 IFC-IB-298 / R8 补齐）。

    ## 两类字段并存（R8 实现说明，登记为设计缺口）

    本类在实现中**先于** R8 设计而存在（承载 `messages` / `last_expert` / `sticky_turns_left`
    —— 支撑多轮上下文与粘性路由，AC-IB-09-05），R8 设计（§2.1，IFC-IB-298）按
    `session_key` / `project_id` / `actor_id` / `turns` / `gate` / `updated_at` **另立字段集**。

    设计文档明言「`IFC-IB-221/222` 早已引用该类型但 §2.1 从未定义」，即设计者在**看不到
    既有实现**的前提下给出字段集。两套字段子集对**既有调用方**（`orchestration` / `streaming`
    与 GROUP_D R11 用例，均构造 `SessionState(messages=..., last_expert=..., sticky_turns_left=...)`）
    是**既成事实**，删除即破坏既有断言（违反本轮硬约束）。

    故本轮按**最小一致原则**：保留既有三个字段**一字不动**，**追加** R8 的六个字段
    （全部带安全默认值）。`IFC-IB-221/222` 的**签名文本一字不改**（仍收 / 返 `SessionState`）；
    新增字段只被新契约（`can_resume` / 确认门）消费。**此为设计缺口**（两套字段集的归一
    应由 PM / 架构裁决），已登记于 `docs/code_review_report.md`。
    """

    # --- 既有字段（R1~R7；一字不动） --- #
    messages: list[Message] = field(default_factory=list)
    last_expert: str | None = None
    sticky_turns_left: int = 0
    # --- R8 追加字段（IFC-IB-298；全部带默认值，构造兼容） --- #
    session_key: str = ""
    project_id: str = ""
    actor_id: str = ""
    turns: tuple[SessionTurn, ...] = ()
    gate: "ConfirmationGateState | None" = None
    updated_at: str = ""


@dataclass(frozen=True, slots=True)
class StreamEvent:
    """类型化流事件（IFC-IB-224）。**本类是唯一实现**（`ib.streaming` 直接复用，不另立同名类）。

    `kind ∈ {reasoning, content, degraded, related_images, error, done, confirmation_required}`。

    `data` 给默认空串：除正文外的事件（`done` / `error` / 纯进度 `reasoning`）都没有载荷，
    若强制调用方每次写 `data=""`，只会诱导出「随手传个占位串」的坏习惯 ——
    而占位串会被前端当成真实内容渲染出来。
    """

    kind: str
    data: str = ""


@dataclass(frozen=True, slots=True)
class ExpertResult:
    """单个专家的作答结果（MOD-IB-22 State 的并行归集元素）。"""

    expert: str
    content: str
    degraded: bool = False
    degrade_reason: DegradeReasonLiteral | None = None


# --------------------------------------------------------------------------- #
# 编排配置（IFC-IB-231）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class GraphConfig:
    """编排图配置（IFC-IB-231）。

    `max_expert_steps` 默认 8（对齐 FreeArk `MAX_EXPERT_STEPS`）。
    `confirmation_gate_enabled` **默认关闭** —— OQ-IB-07：「机制保留、默认不启用」。
    """

    max_expert_steps: int = 8
    confirmation_gate_enabled: bool = False
    #: REV-12-2（G2）专家**单跳交接**开关。**默认关闭** —— 关闭时 `_expand_plan` 与既有
    #: 行为逐位一致（计划 == 路由命中的专家，`is_delegating` 不参与）；开启时允许可委托专家
    #: 把问题**单跳转交**给默认同侪，受 `max_expert_steps` 上限约束，且**保留**不通交时的
    #: 常规作答路径。**触发时机**（哪些轮次需要交接）属未决设计项，故此处只提供受控接缝并
    #: **默认关闭**（见 `docs/code_review_report.md` 设计缺口登记），不擅自决定业务语义。
    expert_handoff_enabled: bool = False
    max_history_messages: int = 20
    aggregation_forbids_internal_labels: bool = True


# --------------------------------------------------------------------------- #
# 定义文档（R7 增量，IFC-IB-287~292；module_design.md §2.1 / §3 MOD-IB-01）
#
# 这些是「定义文档为单一真源」的**类型层契约**（ADR-15）：定义文档在装配期被
# 装载 → 校验 → 派生为**只读**视图（DerivedView），运行期不得由任何图外输入改变拓扑。
# 全部 frozen dataclass / 纯 stdlib（REV-07-5），字段一律用不可变元组，杜绝共享可变状态。
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ExpertSpecInput:
    """定义文档中的**专家规格输入**（IFC-IB-287 / 288）。

    与运行期 `ExpertSpec` 的区别：本类额外携带 `exemplars`（供语义路由的样例句），
    且**不含**运行期注入项。`keywords` / `exemplars` 均为不可变元组。
    """

    name: str
    cn_label: str
    keywords: tuple[str, ...]
    exemplars: tuple[str, ...]
    is_data_expert: bool
    fallback_prompt: str
    is_delegating: bool
    is_default: bool


@dataclass(frozen=True, slots=True)
class RouteSpecInput:
    """定义文档中的**路由参数**（IFC-IB-287）。

    `tau` / `margin` 对应语义路由阈值；`default_expert` 必须**恰好**匹配一个专家 name。
    """

    tau: float
    margin: float
    max_expert_steps: int
    default_expert: str


@dataclass(frozen=True, slots=True)
class ConditionalEdgeSpec:
    """条件边规格（IFC-IB-287）。

    `branch_map` 为**有序** `(branch_key, target_node)` 序列。**显式声明**是硬要求：
    缺失 / 为空即非法（IFC-IB-290 拒绝）—— 否则界面无法判定可达性（REQ-FUNC-IB-26 ④）。
    """

    from_node: str
    branch_map: tuple[tuple[str, str], ...]


#: 保留的**合成端点**：只允许出现在 `OrchestrationSpecInput.edges` 的端点上，
#: **不得**出现在 `nodes` 里，也不得作为条件边的分支目标。它们表达的是一张图的入口与
#: 出口，本身不是可编排的节点 —— 混进 `nodes` 会让「节点集合」同时承载两种语义。
RESERVED_GRAPH_ENDPOINTS: frozenset[str] = frozenset({"START", "END"})


@dataclass(frozen=True, slots=True)
class EdgeSpec:
    """普通边（无条件转移）规格（IFC-IB-287 扩展）。

    与 `ConditionalEdgeSpec` 的分工：条件边表达「一个节点按分支键走到多个目标」，
    普通边表达「无条件从 A 到 B」。二者**都**要声明 —— 只画条件边的图会丢掉主干
    （典型症状：`gate` / `aggregate` 这类只靠普通边相连的节点在界面上成为孤立方块）。

    端点除真实节点外，还允许 `RESERVED_GRAPH_ENDPOINTS`（`START` / `END`）以表达入口
    与出口；它们**不**进 `nodes`。
    """

    from_node: str
    to_node: str


@dataclass(frozen=True, slots=True)
class OrchestrationSpecInput:
    """编排图规格输入（IFC-IB-287）。

    `nodes` 为节点名集合；`conditional_edges` 为条件边集合，`edges` 为普通边集合。
    **图拓扑不在运行期可编辑**（REQ-FUNC-IB-26 ②）：本结构一旦派生为 `DerivedView`，
    进程内不得再被改写。

    `edges` **带默认值 `()`**：既有文档与全仓既有的构造点（自检 / 测试 / 探针）都不声明
    它，不给默认值会因缺参全仓报错。空 `edges` 等价于「本图无普通边」，是合法状态。
    """

    nodes: tuple[str, ...]
    conditional_edges: tuple[ConditionalEdgeSpec, ...]
    edges: tuple[EdgeSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolGrantSpec:
    """工具授权规格（IFC-IB-287；**REV-16-2 加成式扩展** IFC-IB-340）。

    `expert_name` → 该专家**可绑定**的工具名集合。工具名须在已知工具注册表内，
    否则 IFC-IB-290 报错（不静默放行未定义工具）。

    **REV-16-2 加成式扩展**：增列 `param_values`（默认空元组）承载**工具参数值**
    （ADR-30 / REQ-FUNC-IB-39）。既有字段与语义**一字未动**（沿用 IFC-IB-282 / 324
    的「加成式扩展」先例）。本结构**不提供**新增工具本体的路径。
    """

    expert_name: str
    tool_names: tuple[str, ...]
    param_values: tuple["ToolParamValue", ...] = ()


@dataclass(frozen=True, slots=True)
class DefinitionDocument:
    """**定义文档**（单一真源；IFC-IB-287~288，module_design.md §2.1）。

    承载「专家 / 路由 / 编排 / 工具授权」的完整定义。`content_hash` 为语义哈希，
    用于写回的**乐观并发**判据（IFC-IB-289）；`schema_version` 供未来迁移。
    """

    schema_version: int
    project_id: str
    content_hash: str
    experts: tuple[ExpertSpecInput, ...]
    route: RouteSpecInput
    orchestration: OrchestrationSpecInput
    tool_grants: tuple[ToolGrantSpec, ...]
    updated_at: str


@dataclass(frozen=True, slots=True)
class DerivedView:
    """**只读派生视图**（IFC-IB-291，ADR-15 第二层）。

    由 `derive(doc)` **纯函数**产出：**不落盘、不可反写文档**。装配期据此注入运行期
    注册表 / 图配置。`capability_digest` 为工具授权的能力摘要。

    **REV-16-2 加成式扩展**：增列 `prompt_bundles`（默认空元组），承载跨域合并派生的
    提示词分层结果（IFC-IB-347）。既有字段与 `derive()` 签名文本**一字未动**。
    """

    experts: tuple[ExpertSpecInput, ...]
    capability_digest: str
    graph_config: OrchestrationSpecInput
    prompt_bundles: tuple["ExpertPromptBundle", ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationErrorItem:
    """单条校验错误（IFC-IB-290）。

    **只出** `path` / `code` / `message`：`message` 不得回显任何凭据值（AC-IB-18-04）。
    """

    path: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """校验报告（IFC-IB-290 / 293，ADR-16）。

    **字段集是刻意的**：除 `ok` / `errors` 外**不存在** `force` / `ignore` / `warn_only`
    —— 使「不提供强制继续 / 忽略错误开关」成为**类型层事实**而非纪律约定
    （REQ-FUNC-IB-27）。任何「带病继续」都无法由本结构表达。
    """

    ok: bool
    errors: tuple[ValidationErrorItem, ...] = ()


@dataclass(frozen=True, slots=True)
class SaveResult:
    """写回结果（IFC-IB-289，module_design.md §2.1）。

    `conflict=True` 表示乐观并发哈希不匹配 —— **拒绝覆盖**并回执可读冲突收据；
    此时 `ok=False` 且 `errors` 至少含一条 `code="content_hash_conflict"`。
    """

    ok: bool
    content_hash: str
    conflict: bool
    errors: tuple[ValidationErrorItem, ...] = ()


# --------------------------------------------------------------------------- #
# REV-16-2 提示词 / 工具参数（IFC-IB-337 ~ 342，module_design.md §2.1）
#
# 真源边界（ADR-15-R1）：定义文档 = 结构与配置域唯一真源；独立 markdown 提示词目录
# = 提示词域唯一真源；装配期**按域合并**（合并键 = 专家 `name`）。两域不重叠。
# 以下均为 **frozen dataclass / Literal，纯 stdlib，无实现体**（零第三方依赖）。
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ExpertPromptDocumentRef:
    """单层提示词文档引用（IFC-IB-337）。

    指向独立提示词目录中的**一个文件**（`main.md` 或 `fallback.md`）。
    `rel_path` 为相对目录根的路径；`content_hash` 为语义哈希（乐观并发判据）；
    `exists=False` 表示该层文件缺失（`main` 缺失合法，`fallback` 缺失非法）。
    """

    expert_name: str
    layer: PromptLayer
    rel_path: str
    content_hash: str
    exists: bool


@dataclass(frozen=True, slots=True)
class ExpertPromptBundle:
    """专家提示词分层合并结果（IFC-IB-338，ADR-29）。

    * `main_prompt`：主提示词，**可缺**（`None`）；
    * `fallback_prompt`：兜底提示词，**非空**（否则非法）；
    * `effective_prompt`：跨域合并后**恒非空**的生效系统提示词
      （主缺失 → 回退兜底；见 ADR-29「绝不空白系统提示词」）；
    * `resolved_from`：生效来源（`main_file` / `fallback_file` / `definition_doc_fallback`），
      供界面可观测（IFC-IB-354）。
    """

    expert_name: str
    main_prompt: str | None
    fallback_prompt: str
    effective_prompt: str
    resolved_from: Literal["main_file", "fallback_file", "definition_doc_fallback"]


@dataclass(frozen=True, slots=True)
class PromptDirectoryLayout:
    """独立提示词目录的物理布局（IFC-IB-338 / [ARCH-ASSUMPTION-A10]）。

    只描述布局事实（键名 / 文件模式 / 命名规则），**不含任何路径值**（路径值不进响应 / 日志）。
    """

    root_key: str
    file_pattern: str
    naming_rule: str


@dataclass(frozen=True, slots=True)
class ToolParamValue:
    """工具参数的**取值**（IFC-IB-340，ADR-30）。

    `name` 为参数标识：可使用 `<tool_name>.<param_name>` 的限定形式以声明归属工具
    （从而支持「未授权工具带参」判定）；不含 `.` 时视为全局参数。
    """

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class ToolParamSpec:
    """工具参数的**声明**（IFC-IB-340，ADR-30）。

    类型 / 默认值 / 上下界 / 枚举。参数 schema 须与各工具实现**成对维护**（ADR-30 负向）。
    """

    name: str
    type: ToolParamTypeLiteral
    default: str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class PromptSaveResult:
    """提示词单层保存结果（IFC-IB-341）。

    `saved=False` 时 `errors` 至少一条（校验不通过 / 乐观并发冲突）；
    **保存失败不破坏在用配置**（fail-safe，REQ-NFR-IB-19）。
    """

    saved: bool
    ref: ExpertPromptDocumentRef
    content_hash: str
    errors: tuple[ValidationErrorItem, ...] = ()


@dataclass(frozen=True, slots=True)
class DimensionCheck:
    """FreeArk 对齐比对表的**单维**结果（IFC-IB-342，ADR-31）。

    `unalignable=True` 表示该维**显式排除**（FreeArk 无真源，不得伪造对齐）。
    """

    dimension: str
    base_value: str
    freeark_value: str
    aligned: bool
    unalignable: bool
    note: str


@dataclass(frozen=True, slots=True)
class AlignmentChecklist:
    """FreeArk 严格对齐**可核验清单**（IFC-IB-342，ADR-31）。

    10 维（9 维专家定义 + 1 维工具名映射），其中**工具参数为显式排除项**（`unalignable=True`）。
    """

    items: tuple[DimensionCheck, ...]


@dataclass(frozen=True, slots=True)
class FreeArkAlignedExpertSpec:
    """FreeArk 严格对齐的专家规格（IFC-IB-342，ADR-31）。

    = `ExpertSpec` 的 7 字段 + `main_prompt` + `exemplars`（共 **9 维**）
    + `tool_names`（第 **10** 维，工具名对齐）。**纯数据，无实现体。**
    """

    name: str
    cn_label: str
    keywords: tuple[str, ...]
    exemplars: tuple[str, ...]
    is_data_expert: bool
    fallback_prompt: str
    is_delegating: bool
    is_default: bool
    main_prompt: str | None
    tool_names: tuple[str, ...]


# --------------------------------------------------------------------------- #
# R13（IFC-IB-309）：账户 / 会话 / 令牌的数据结构
# --------------------------------------------------------------------------- #
#
# 为什么把凭据相关结构放进 framework-free 的 `ib.core`：它们是**端口 AccountStore
# （IFC-IB-310）签名的一部分**，而端口必须与实现（SQLite / 内存）解耦。若把它们放进
# `ib.ledger`，`ibweb` 就会反向依赖具体存储模块，端口倒置随之失效。
#
# 凭据纪律（C-IB-09 / REQ-NFR-IB-15，硬约束）：
#   * `UserRecord.password_hash` **只承载 bcrypt 摘要**，绝不承载任何口令明文；
#   * `SessionRecord.token_digest` **只承载 sha256 摘要**，绝不承载令牌原文
#     （「读到库 ≠ 拿到可用令牌」，ADR-19）；
#   * 本层**不提供任何**把口令 / 令牌写成日志或响应的字段。

#: 账户角色（IFC-IB-309）。`admin` = 全局（`project_id is None`）；`ops` = 绑定单项目、
#: 语义等价既有 `manager`（ADR-21）。**新增取值只许追加**，既有取值不得改义。
UserRole: TypeAlias = Literal["admin", "ops"]

#: 账户状态（IFC-IB-309）。`disabled` 的账户即使携带有效会话也必须 fail-closed。
AccountStatus: TypeAlias = Literal["active", "disabled"]

#: 登录结果分词（IFC-IB-309）。**仅用于内部判定 / 审计字段**（IFC-IB-326）；
#: **对外一律折叠为 `401`、不区分** —— 区分等于给攻击者一个账号/状态探测预言机（ADR-13 精神）。
LoginOutcome: TypeAlias = Literal["ok", "bad_credentials", "disabled", "locked"]


@dataclass(frozen=True, slots=True)
class UserRecord:
    """账户记录（IFC-IB-309）。

    `password_hash` 只承载 **bcrypt 摘要**；`project_id is None` **仅对 `admin` 成立**
    （全局账户，ADR-21）。`staff`（管理动作）与 `viewer` 的区分由 `role` 承载，
    而「能不能管 / 能不能问」的最终判定**只**经注入的 `AuthzPolicy`（ADR-22）——
    本结构不含任何授权结论。
    """

    user_id: str
    username: str
    password_hash: str
    role: UserRole
    project_id: str | None
    status: AccountStatus
    must_change_password: bool
    failed_login_count: int
    locked_until: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """会话记录（IFC-IB-309）。

    **只承载 `token_digest`（sha256 摘要）**，绝不承载令牌原文（ADR-19）。
    `revoked_at` / `expires_at` 任一已过即视为无效（`resolve_session` 返回 `None`，fail-closed）。
    """

    token_digest: str
    user_id: str
    project_id: str | None
    issued_at: str
    expires_at: str
    last_seen_at: str
    revoked_at: str | None


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    """口令强度策略（IFC-IB-309；细节 OQ-IB-11 保持开放）。

    `require_classes` = 必须命中的字符类别数（小写 / 大写 / 数字 / 符号，≥2 类即 2）。
    策略**只在服务端生效**；前端预校验仅为体验优化（服务端为唯一裁决者）。
    """

    min_length: int
    require_classes: int


@dataclass(frozen=True, slots=True)
class AccountSummary:
    """账户的**对外**可序列化视图（IFC-IB-309）。

    **不含 `password_hash`**（也不含 `failed_login_count` / `locked_until` 等内部态）——
    供 `GET /api/accounts` 与 `GET /api/auth/me` 输出，避免任何摘要外泄。
    """

    user_id: str
    username: str
    role: UserRole
    project_id: str | None
    status: AccountStatus
    must_change_password: bool


# --------------------------------------------------------------------------- #
# REV-16-4 配置审计 / 存储态（IFC-IB-356 / 361，module_design.md §2.2.7 / §3 MOD-IB-01）
# --------------------------------------------------------------------------- #
#
# 两件事放在 framework-free 的 `ib.core`：
#   * `ConfigAuditEntry` 是端口 `ConfigAuditStore`（IFC-IB-357）签名的一部分，
#     必须与实现（SQLite / 内存）解耦，否则 `ibweb` 会反向依赖 `ib.ledger`（端口倒置失效）；
#   * `StorageState` 是 `GET /api/config/storage-state`（IFC-IB-362）的响应契约，
#     definition / prompt 两类编辑器**共用**同一类型化真源（ADR-35）。
#
# 凭据 / 取值纪律（ADR-34，硬约束）：
#   * `ConfigAuditEntry.changed_field_names` **只承载字段名**（如 `route.tau`），
#     **绝不承载任何配置取值**；
#   * `detail_code` **只承载结果码**，不回显取值；
#   * 本层**不提供任何**承载配置取值 / 凭据的字段。

#: 配置审计结果（IFC-IB-356）：成功与失败**均记录**（ADR-34）。取值只许追加，不得改义。
ConfigAuditResult: TypeAlias = Literal["saved", "rejected"]

#: 存储模式（IFC-IB-361，ADR-35）：`memory` = 「配置仅内存生效、不跨重启保留」。
StoreMode: TypeAlias = Literal["memory", "file"]


@dataclass(frozen=True, slots=True)
class ConfigAuditEntry:
    """配置「保存 / 生效」的**可查询记录**（IFC-IB-356，ADR-34）。

    **只读审计，非第二真源**：本结构不含任何配置取值，故**没有任何配置读取路径**
    能消费它（端口 `ConfigAuditStore`（IFC-IB-357）亦在类型层排除 `update` / `delete`）。

    字段：`timestamp`（UTC 定长串）/ `project` / `actor`（谁）/ `action`（做了什么）/
    `changed_field_names`（改了**哪些字段**，只出字段名）/ `result ∈ {saved,rejected}` /
    `detail_code`（拒绝原因 / 结果码，只出码）。
    """

    timestamp: str
    project: str
    actor: str
    action: str
    changed_field_names: tuple[str, ...]
    result: ConfigAuditResult
    detail_code: str | None


@dataclass(frozen=True, slots=True)
class StorageState:
    """配置存储态（IFC-IB-361，ADR-35）。

    `definition_store` / `prompt_store ∈ {memory,file}` 为**装配期实际选用**的存储实现
    的诚实投影（单一来源 = 装配结果，IFC-IB-362）；`*_configured` 表示对应存储
    **是否已配置**（键已设置）。任一 `memory` 即「**配置仅内存生效、不跨重启保留**」。

    **语义声明（强制）**：本结构**仅增加可观测提示**，**不改变**「保存 + 服务重启重装配」
    生效口径（ADR-32 / C-IB-40 / OOS-16），**不引入**运行期热重载。
    """

    definition_store: StoreMode
    prompt_store: StoreMode
    definition_store_configured: bool
    prompt_store_configured: bool


__all__ = [
    "Vector",
    "DistanceLiteral",
    "SourceKindLiteral",
    "DocStatusLiteral",
    "DegradeReasonLiteral",
    "PageImageSourceKindLiteral",
    "Scope",
    "HnswParams",
    "CollectionSpec",
    "CollectionInfo",
    "PointPayload",
    "VectorPoint",
    "ScoredPoint",
    "PointFilter",
    "UpsertResult",
    "HealthStatus",
    "EmbedderDescriptor",
    "ChunkingSpec",
    "ParsedChunk",
    "ParsedDocument",
    "RetrievedChunk",
    "RetrievalResult",
    "PageImageRef",
    "PageImageBinding",
    "RelatedImageItem",
    "RelatedImagesPayload",
    "ChunkImageRecord",
    "DocumentRecord",
    "ChunkRecord",
    "KbRecord",
    "ProjectRecord",
    "AuthzContext",
    "RequestContext",
    "RawConfig",
    "BlobRef",
    "ValidatedUpload",
    "ProcessReport",
    "DeleteReport",
    "RebuildPlan",
    "RebuildJob",
    "RebuildProgress",
    "ToolResult",
    "ToolSpec",
    "RegisteredTool",
    "BoundTool",
    "ExpertSpec",
    "Message",
    "RouteDecision",
    "LlmRole",
    "EgressDescriptor",
    "OcrDescriptor",
    "SessionState",
    "StreamEvent",
    "ExpertResult",
    "GraphConfig",
    # R7 定义文档（IFC-IB-287~292）
    "ExpertSpecInput",
    "RouteSpecInput",
    "ConditionalEdgeSpec",
    "OrchestrationSpecInput",
    "ToolGrantSpec",
    "DefinitionDocument",
    "DerivedView",
    "ValidationErrorItem",
    "ValidationReport",
    "SaveResult",
    # R13 账户 / 会话（IFC-IB-309）
    "UserRole",
    "AccountStatus",
    "LoginOutcome",
    "UserRecord",
    "SessionRecord",
    "PasswordPolicy",
    "AccountSummary",
    # REV-16-2 提示词 / 工具参数（IFC-IB-337 ~ 342）
    "PromptLayer",
    "ToolParamTypeLiteral",
    "ExpertPromptDocumentRef",
    "ExpertPromptBundle",
    "PromptDirectoryLayout",
    "ToolParamValue",
    "ToolParamSpec",
    "PromptSaveResult",
    "DimensionCheck",
    "AlignmentChecklist",
    "FreeArkAlignedExpertSpec",
    # REV-16-4 配置审计 / 存储态（IFC-IB-356 / 361）
    "ConfigAuditResult",
    "StoreMode",
    "ConfigAuditEntry",
    "StorageState",
]
