"""
@module MOD-IB-01
@implements IFC-IB-001 .. IFC-IB-010 （全部不可变数据结构；逐字段名 + 类型 + 可空性）
@depends (none)
@author sub_agent_software_developer

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
    """工具声明（IFC-IB-181）。`description` 进入能力摘要（IFC-IB-182）。"""

    name: str
    description: str
    needs_scope: bool = False


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    """注册表中的工具条目（IFC-IB-181）。"""

    spec: ToolSpec
    fn: Any  # Callable[..., ToolResult]


@dataclass(frozen=True, slots=True)
class BoundTool:
    """已绑定 scope 的工具（IFC-IB-183）。

    **构造期闭包绑定**的结果形态：`callable` 是**无参**的（骨架只见无参工具），
    scope 已被封闭在闭包内（ADR-09 / §1.4）。
    """

    name: str
    description: str
    callable: Any  # Callable[[], ToolResult] 或 Callable[[str], ToolResult]


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
# 会话与流（IFC-IB-221 / 224）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class SessionState:
    """会话状态（IFC-IB-221）。

    `last_expert` 支撑粘性路由（AC-IB-09-05）；`messages` 供多轮上下文，
    但**路由判据只取当前提问**（历史前缀须剥离）。
    """

    messages: list[Message] = field(default_factory=list)
    last_expert: str | None = None
    sticky_turns_left: int = 0


@dataclass(frozen=True, slots=True)
class StreamEvent:
    """类型化流事件（IFC-IB-224）。**本类是唯一实现**（`ib.streaming` 直接复用，不另立同名类）。

    `kind ∈ {reasoning, content, degraded, related_images, error, done}`。

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
    max_history_messages: int = 20
    aggregation_forbids_internal_labels: bool = True


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
]
