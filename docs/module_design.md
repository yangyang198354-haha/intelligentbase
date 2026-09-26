<file_header>
  <project>intelligentbase</project>
  <artifact>module_design</artifact>
  <path>docs/module_design.md</path>
  <doc_id>MOD-INTELBASE-001</doc_id>
  <version>1.2.0</version>
  <revision>R2</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04 模块详细设计</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>
  <created_at>2026-09-25</created_at>
  <revision_history>
    <rev no="R1" date="2026-09-25" by="sub_agent_system_architect" basis="REV-01（框架切换 FastAPI→Django）">
      Web 层载体由 FastAPI/Uvicorn/ASGI 切换为 Django + DRF + WSGI（Waitress 主 / Gunicorn 备）。仅替换「载体」，不改变任何领域契约：25 模块、13 端口、58 条 IFC-IB 编号、DAG 拓扑序与 REQ 覆盖率均保持不变。新增 §2.1.1 载体等价映射表、§4.2.1 无环性再声明、§9.3 覆盖率再声明；MOD-IB-21 增补 SSE 承载与鉴权纪律；MOD-IB-23 组合根返回类型与外部依赖替换。
    </rev>
  <rev no="R2" date="2026-09-26" by="sub_agent_system_architect" invocation_id="INV-GROUP_B-INTELBASE-004" basis="PM 补交要求（L-03：ib-embed 服务端无模块归属与完整契约）">
    新增 MOD-IB-26「ib-embed 服务端」（26 大于其全部依赖 {01,02,04}，编号即拓扑序仍成立，且本模块不被任何模块 import）。新增 IFC 编号：266~274（MOD-IB-26 线协议，正文以 docs/ib_embed_service_contract.md 为准）、275（MOD-IB-09 的 InProcessBgeM3Embedder 第三适配器）、276~284（M-02 页面图绑定：MOD-IB-01 数据结构 / MOD-IB-13 五条 / MOD-IB-21 related_images 载荷 / MOD-IB-23 图片端点 / MOD-IB-24 渲染约束）、286（MOD-IB-25 第二份 EnvironmentFile 模板）；IFC-IB-285 预留未分配。既有 MOD-IB-01~25、IFC-IB-001~265、端口名、DAG 拓扑与 REQ 覆盖率矩阵一字不动（纯追加）。增补位置：§1 总览行与计数、§2.1 三行数据结构、§2.2.1 R2 IFC 段号索引、§3 的 MOD-IB-09/13/21/23/24/25 增补与 MOD-IB-26 新小节（摘要视图）、§4.1 一条新依赖边、§4.2 R2 无环补句、§4.3 分层一行、§5 装配表 IB_EMBED_BACKEND 值域扩展、§7.4 两行降级、§9.1/§9.2 覆盖更新与 §9.4 再声明、§11 R2 自检。
  </rev>
  </revision_history>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.1.0" status="DRAFT_FOR_GATE_REVIEW"/>
    <readonly_reference path="FreeArk 仓库" note="只读参考；未修改任何文件"/>
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW" note="MOD-IB-26 契约唯一落点；本文件 §3 MOD-IB-26 为摘要视图，冲突时以其为准"/>
  </inputs>
  <scope_boundary>模块划分、类型化接口契约、依赖图、装配表、覆盖率矩阵、状态机与降级矩阵。**不含实现代码**（无函数体、无伪代码级实现）。</scope_boundary>
</file_header>

# 模块详细设计 — intelligentbase

**版本**: 1.2.0 (R2) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26
**R2 性质**: 本修订为**补交式增量**（L-03：`ib-embed` 此前只有 systemd 单元与客户端、缺服务端模块归属与完整契约），**只追加、不改写**：新增 MOD-IB-26 与 IFC-IB-266~284 / 286（IFC-IB-285 预留）。既有 MOD-IB-01~25、IFC-IB-001~265、13 个端口名与 DAG 拓扑**一字不动**。MOD-IB-26 的契约**唯一落点**为 `docs/ib_embed_service_contract.md`，本文件 §3 为其**摘要视图**，二者冲突时以契约文件为准。
**配套**: 架构决策与背景见 `docs/architecture_design.md`；技术选型见 `docs/tech_stack.md`。
**R1 性质**: 本修订为**载体替换**（Web 框架 FastAPI→Django），**非契约变更**——模块划分、类型化接口、依赖图拓扑与需求覆盖率均不变，只在「谁承载这些契约」这一层做了等价映射（见 §2.1.1）。所有编号（MOD-IB-*、IFC-IB-*、端口名）保持稳定以便追溯。

**本文承担四项目门控标准的可验证证据**：① REQ→MOD 覆盖率矩阵（§9，24/24 REQ-FUNC 全覆盖）；② 依赖图 DAG 无环（§4，构造性证明）；③ 类型化接口契约（§2、§3）；④ 各 ADR 的候选方案已在架构文档中给出。

**契约记法**：`IFC-IB-NNN: name(param: Type, *, kw: Type) -> ReturnType | ErrorType`。`T | None` 表示可空；`scope` 无 `= 默认值` 即表示**必填**。

---

## 1. 模块总览

26 个模块（R2 新增 MOD-IB-26）。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4；R2 新增单边的权值校验见 §4.2）。

**R2 补充纪律**：MOD-IB-26 是**唯一**「不被任何模块 import」的服务端模块（上层只经 `Embedder` 端口与线协议访问，与 MOD-IB-10 对 Qdrant 服务的形态同构），因此它**不引入任何入边**，也不可能出现在任何依赖环上。若将来有人 `import` 本模块，会**同时**破坏 DAG 纪律与「形态可逆」（进程内形态不得依赖服务端）。

| MOD-ID | 模块名 | 层 | 职责（一句话） | 依赖于 |
|--------|--------|----|----------------|--------|
| MOD-IB-01 | 核心契约 | L0 | 定义全部端口 Protocol、枚举与不可变数据结构；零第三方依赖 | — |
| MOD-IB-02 | 配置 | L0 | 装载并校验 全局配置 / 项目级配置；注入凭据（仅环境变量） | 01 |
| MOD-IB-03 | 请求上下文 | L0 | 承载请求级机械上下文与鉴权主体；提供 `AuthzPolicy` 端口 | 01 |
| MOD-IB-04 | 可观测性 | L0 | 结构化日志、计时、降级事件发射；字段白名单与脱敏 | 01 |
| MOD-IB-05 | 解析器注册表与格式解析器 | L1 | 按扩展名分派；实现 docx / pdf / md / txt 解析（PDF 三路径） | 01,02,04 |
| MOD-IB-06 | OCR 端口与 RapidOCR 适配 | L2 | 图像 → 文本；不可用时以 `NullOcrEngine` 显式降级 | 01,02,04 |
| MOD-IB-07 | 切分器 | L1 | 将 `ParsedDocument` 按可配参数滑窗切分为块 | 01,02 |
| MOD-IB-08 | 页面渲染端口与 pypdfium2 适配 | L2 | PDF 页 → 栅格图像（供扫描页 OCR） | 01,02,04 |
| MOD-IB-09 | Embedding 端口与本地适配 | L2 | 文本 → 稠密向量；冷热双路径（超时/重试/批量策略不同） | 01,02,04 |
| MOD-IB-10 | VectorStore 端口与 Qdrant 适配 | L2 | collection 生命周期、upsert、query、按 doc/scope 删除、健康 | 01,02,04 |
| MOD-IB-11 | 台账 | L3 | 项目/知识库/文档/块元数据 + 状态机 + 任务租约 + 归属断言 | 01,02,04 |
| MOD-IB-12 | 原文件 BlobStore | L3 | 内容寻址（sha256）持久化原始文件；按 scope 删除 | 01,02,04 |
| MOD-IB-13 | 文档生命周期 | L3 | 校验 → 落盘 → 解析 → 切分 → 向量化 → 写库 → 置位；删除与重试 | 01,02,03,04,05,07,09,10,11,12 |
| MOD-IB-14 | 索引重建 | L3 | 指纹 → 新 collection 版本 → 逐文档 delete-then-write → 原子切换 | 01,02,03,04,11,12,13 |
| MOD-IB-15 | 检索服务 | L3 | 组装 filter、调用 embed+query、**永不抛异常**，返回 `RetrievalResult` | 01,02,03,04,09,10 |
| MOD-IB-16 | 专家注册表 | L4 | 专家规格的**唯一真源**（frozen dataclass，framework-free 纯数据） | 01 |
| MOD-IB-17 | 工具注册与能力摘要 | L4 | 工具注册表 + 由注册表**派生**的能力摘要；scope 闭包绑定 | 01,15,16 |
| MOD-IB-18 | 语义路由 | L4 | 向量化样例打分 + 阈值/分差判定（纯函数，fail-open） | 01,09,16 |
| MOD-IB-19 | 意图路由内核 | L4 | 四级降级路由（关键词 → 语义 → LLM → 兜底）+ 粘性 + OOD + 守卫 | 01,16,17,18 |
| MOD-IB-20 | LLM 端点抽象 | L4 | provider 端口；路由/专家/聚合三角色的构造；外发边界声明 | 01,02,04 |
| MOD-IB-21 | 流式契约与会话 | L4 | 类型化流事件与 SSE 编码；`SessionStore` 端口 | 01,02,04 |
| MOD-IB-22 | 编排图 | L4 | StateGraph：route → fan-out → expert/general → gate → aggregate | 01,02,03,04,16,17,18,19,20,21 |
| MOD-IB-23 | HTTP API 与组合根 | L5 | 唯一装配点；REST + SSE 端点；鉴权注入；健康检查 | 01,02,03,04 + 全部装配目标 |
| MOD-IB-24 | Web 前端 | L5 | 上传/列表/删除/重试/重建页 + 问答页 + 类型化 API 客户端 | 23（仅 HTTP/SSE 契约） |
| MOD-IB-25 | 部署运维 | L5 | 四个 systemd 单元、EnvironmentFile 模板、启动校验、检查清单 | 01,02,04 |
| MOD-IB-26 | ib-embed 服务端 | L2（服务端进程；不被任何模块 import） | bge-m3 常驻推理服务的**线协议实现与模块归属**；单模型、CPU-only、有界并发 + 有界队列 | 01,02,04 |

---

## 2. 类型化契约与端口（定义于 MOD-IB-01）

### 2.1 核心数据结构（不可变；全部字段名 + 类型 + 可空性）

| 结构 | 字段（名: 类型） |
|------|------------------|
| `Scope` | `project_id: str`；`kb_ids: tuple[str, ...] \| None`（`None` = 项目内全部知识库） |
| `HnswParams` | `m: int`；`ef_construct: int`；`ef_search: int` |
| `CollectionSpec` | `collection: str`；`dim: int`；`distance: Literal["cosine"]`；`on_disk_vectors: bool`；`hnsw: HnswParams` |
| `CollectionInfo` | `name: str`；`dim: int`；`distance: str`；`points_count: int` |
| `Vector` | `Sequence[float]`（别名；长度须等于 `dim`） |
| `PointPayload` | `project_id: str`；`kb_id: str`；`doc_id: str`；`doc_name: str`；`chunk_index: int`；`content: str`；`locator: str`；`source_kind: Literal["text","image_ocr","page_scan"]`；`page_or_section: str`；`content_hash: str`；`indexed_model: str`；`indexed_dim: int`；`created_at: str`；`blob_ref: str \| None`；`schema_version: int` |
| `VectorPoint` | `id: str`；`vector: Vector`；`payload: PointPayload` |
| `ScoredPoint` | `id: str`；`score: float`；`payload: PointPayload` |
| `PointFilter` | `project_id: str`（**必填**）；`kb_ids: tuple[str, ...] \| None`；`doc_ids: tuple[str, ...] \| None` |
| `UpsertResult` | `upserted: int`；`elapsed_ms: int` |
| `HealthStatus` | `ok: bool`；`detail: str`；`latency_ms: int \| None` |
| `EmbedderDescriptor` | `model_id: str`；`dim: int`；`normalized: bool`；`max_tokens: int`；`device: str` |
| `ChunkingSpec` | `chunk_size: int`；`chunk_overlap: int`；`normalizer_version: str` |
| `ParsedChunk` | `content: str`；`page_or_section: str`；`source_kind: Literal["text","image_ocr","page_scan"]`；`locator: str`；`image_ref: str \| None` |
| `ParsedDocument` | `chunks: list[ParsedChunk]`；`page_count: int`；`warnings: list[str]` |
| `RetrievedChunk` | `doc_id: str`；`doc_name: str`；`content: str`；`score: float`；`page_or_section: str`；`source_kind: str`；`locator: str` |
| `RetrievalResult` | `hits: list[RetrievedChunk]`；`degraded: bool`；`degrade_reason: Literal["embedding_unavailable","vectorstore_unavailable","timeout"] \| None`；`scope: Scope`；`elapsed_ms: int`；`candidate_count: int` |
| `DocumentRecord` | `doc_id: str`；`project_id: str`；`kb_id: str`；`doc_name: str`；`ext: str`；`size_bytes: int`；`content_sha256: str`；`blob_ref: str \| None`；`status: Literal["pending","parsing","indexed","failed"]`；`error_code: str \| None`；`chunk_count: int`；`indexed_collection_version: str \| None`；`target_collection_version: str \| None`；`lease_owner: str \| None`；`lease_expires_at: str \| None`；`created_at: str`；`updated_at: str` |
| `KbRecord` | `kb_id: str`；`project_id: str`；`name: str`；`created_at: str` |
| `ProjectRecord` | `project_id: str`；`name: str`；`active_collection_version: str`；`embedding_model_id: str`；`dim: int`；`created_at: str` |
| `AuthzContext` | `actor_id: str`；`project_id: str`；`roles: tuple[str, ...]` |
| `RequestContext` | `request_id: str`；`session_key: str`；`scope_token: str`；`authz: AuthzContext` |
| `PageImageRef`（R2 新增，定义于 MOD-IB-01） | `image_id: str`；`page_or_section: str`；`source_kind: Literal["embedded_image","page_scan"]`；`locator: str`；`blob_ref: str \| None`；`caption: str \| None` |
| `PageImageBinding`（R2 新增，定义于 MOD-IB-01） | `project_id: str`；`kb_id: str`；`doc_id: str`；`page_or_section: str`；`images: tuple[PageImageRef, ...]` |
| `RelatedImageItem` / `RelatedImagesPayload`（R2 新增，定义于 MOD-IB-01） | `RelatedImageItem`: `image_id: str`；`doc_id: str`；`doc_name: str`；`page_or_section: str`；`url_path: str`。`RelatedImagesPayload`: `images: tuple[RelatedImageItem, ...]` |

**R2 说明（字段集不变式）**：以上三行为**追加**，既有两个结构（`ParsedChunk` / `RetrievedChunk`）的字段集**不变**——页面图的图文关联经**独立结构 + 独立关联表**承载，不改 `IFC-IB-009` / `IFC-IB-007` 的既有字段（编号只增不改）。

### 2.1.1 Web 层载体等价映射（R1 新增；FastAPI → Django）

框架切换仅替换**载体**，不改**领域契约**。领域不可变数据结构仍定义于 MOD-IB-01（纯 stdlib / frozen dataclass，**不引入任何 Web 框架类型**），因此本表只覆盖「HTTP / 流式 / 装配」这层薄层。

| FastAPI 载体（v1.0.0） | Django 载体（R1） | 语义等价声明 |
|------------------------|-------------------|--------------|
| Pydantic `BaseModel`（请求/响应模型） | DRF `Serializer`（输入校验 + 输出渲染）+ frozen dataclass（领域契约） | **端口契约不经 Pydantic 承载**：Pydantic 降级为可选工具库；IFC-IB-242~250 的字段与状态码语义不变（ADR-13-R1） |
| FastAPI 依赖注入（`Depends`） | Django 视图显式参数 + **组合根显式注入**（`deps`）+ 中间件 | MOD-IB-23 仍是**唯一装配点**；端口注入语义不变（§5） |
| 路由装饰器（`@app.get/post`） | Django `URLconf` + DRF 视图（`APIView` / 函数视图） | 端点路径、方法、状态码契约（IFC-IB-242~250）逐条不变 |
| `ASGIApp`（`create_app()` 返回） | `WSGIApplication`（`build_application()` 返回，见 IFC-IB-241） | 仅返回类型载体替换；装配语义不变 |
| Starlette `StreamingResponse`（SSE） | `StreamingHttpResponse`（`Content-Type: text/event-stream`） | 事件帧编码（IFC-IB-225）不变；**不引入 Channels/Redis**（ADR-11-R1） |
| FastAPI 异常处理器（`HTTPException`） | DRF 异常处理器 + Django 中间件 | `403`/`409`/`503` 与 fail-closed 语义不变（§7.4） |
| FastAPI `lifespan` / 启动事件 | Django `AppConfig.ready()` + systemd 启动前置校验 | 启动期必填校验（IFC-IB-263）与「未注入即启动失败」（AC-IB-11-05）不变 |

**不变式（R1 强制）**：本表右列的 Django 载体**不得**向 MOD-IB-01 反向渗透（核心契约模块保持 framework-free）；Django 类型只允许出现在 MOD-IB-23（组合根 / HTTP 层）之内，MOD-IB-24（前端）不依赖 Django。

### 2.2 端口清单（含方法数与本文件 IFC 段落）

| 端口 | 方法数 | IFC 段 | 定义处 |
|------|--------|--------|--------|
| `ConfigurationSource` | 2 | IFC-IB-021~022 | §3 MOD-IB-02 |
| `AuthzPolicy` | 2 | IFC-IB-032~033 | §3 MOD-IB-03 |
| `DocumentParser` | 3 | IFC-IB-051~053 | §3 MOD-IB-05 |
| `OcrEngine` | 3 | IFC-IB-061~063 | §3 MOD-IB-06 |
| `Chunker` | 1 | IFC-IB-071 | §3 MOD-IB-07 |
| `PageRenderer` | 2 | IFC-IB-081~082 | §3 MOD-IB-08 |
| `Embedder` | 7 | IFC-IB-090~096 | §3 MOD-IB-09 |
| `CollectionResolver` | 1 | IFC-IB-098 | §3 MOD-IB-09（同层，供 MOD-IB-10/13/14/15 使用） |
| `VectorStore` | 11 | IFC-IB-100~110 | §3 MOD-IB-10 |
| `LedgerRepository` | 12 | IFC-IB-120~131 | §3 MOD-IB-11 |
| `BlobStore` | 4 | IFC-IB-131~134 | §3 MOD-IB-12 |
| `LlmProvider` | 5 | IFC-IB-211~215 | §3 MOD-IB-20 |
| `SessionStore` | 3 | IFC-IB-221~223 | §3 MOD-IB-21 |

`CollectionResolver` 归入 MOD-IB-09 所在层（L2，无外部依赖，仅依赖 MOD-IB-01/02）：它是**唯一**把 `Scope` 映射为 collection 名的地方（ADR-04 可升级性设计），因此必须由所有需要 collection 名的上层模块共用，而非各自拼接字符串。

### 2.2.1 R2 新增 IFC 段号索引（追加式编号；IFC-IB-001~265 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-266 ~ 274 | MOD-IB-26 | `/embed`、`/healthz`、`/warmup`、`/descriptor` 线协议；维度三方一致性；批上限与截断；错误码表与 4xx/5xx 分类不变式；冷/热单一落点；形态可逆 | `docs/ib_embed_service_contract.md` §3~§9（唯一落点） |
| IFC-IB-275 | MOD-IB-09 | `InProcessBgeM3Embedder`（第三适配器）+ 客户端 ↔ 线协议对接表 | §3 MOD-IB-09（本文件） |
| IFC-IB-276 | MOD-IB-01 | `PageImageRef` / `PageImageBinding` / `RelatedImagesPayload` 字段级定义 | §2.1（本文件） |
| IFC-IB-277 ~ 281 | MOD-IB-13 | M-02 五条：`bind_page_images` / `persist_page_images` / 关联模型字段 / `process_pending` R2 步骤 / 删除零改动不变式 | §3 MOD-IB-13（本文件） |
| IFC-IB-282 | MOD-IB-21 | `related_images` 流事件的载荷类型化 | §3 MOD-IB-21（本文件） |
| IFC-IB-283 | MOD-IB-23 | 图片字节端点（鉴权 + scope 断言 + fail 语义） | §3 MOD-IB-23（本文件） |
| IFC-IB-284 | MOD-IB-24 | 前端 `related_images` 渲染约束 | §3 MOD-IB-24（本文件） |
| IFC-IB-285 | —（预留） | **预留未分配**：R2 显式占位，供 GROUP_C 追加时按序取用，不得回收再用或改义 | — |
| IFC-IB-286 | MOD-IB-25 | `ib-embed` 的第二份 EnvironmentFile 模板（只登记键名；见 `tech_stack.md` §1.2） | §3 MOD-IB-25（本文件） |

**R2 编号规范（强制）**：新增号只许**追加**；`IFC-IB-001 ~ 265` 的号、名、签名、字段集**一字不动**。既有重号现状（`IFC-IB-131` 同时出现在 MOD-IB-11 与 MOD-IB-12 的清单中）**登记但不修正**——任何重排都会打断下游引用（见 part7 残余项 R-9）。

---

## 3. 模块详情

> 每个模块含：职责 / 覆盖需求 / 公开接口契约（类型化）/ 依赖模块 / 外部依赖。

### MOD-IB-01 核心契约 (L0)

- **职责**: 定义全部端口 Protocol、枚举与不可变数据结构；**不 import 任何第三方框架**（仅 stdlib）。
- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）
- **公开接口契约（数据结构定义，非行为）**:
  - IFC-IB-001: `Scope(project_id: str, kb_ids: tuple[str, ...] | None)`
  - IFC-IB-002: `CollectionSpec(collection: str, dim: int, distance: Literal["cosine"], on_disk_vectors: bool, hnsw: HnswParams)`
  - IFC-IB-003: `PointPayload(...)`（§2.1 全字段）
  - IFC-IB-004: `VectorPoint(id: str, vector: Vector, payload: PointPayload)`
  - IFC-IB-005: `ScoredPoint(id: str, score: float, payload: PointPayload)`
  - IFC-IB-006: `PointFilter(project_id: str, kb_ids: tuple[str, ...] | None, doc_ids: tuple[str, ...] | None)`
  - IFC-IB-007: `RetrievalResult(hits: list[RetrievedChunk], degraded: bool, degrade_reason: DegradeReason | None, scope: Scope, elapsed_ms: int, candidate_count: int)`
  - IFC-IB-008: `DocumentRecord(...)`（§2.1 全字段）
  - IFC-IB-009: `ParsedDocument` / `ParsedChunk` / `ChunkingSpec`
  - IFC-IB-010: `EmbedderDescriptor` / `RetrievalResult` / `HealthStatus` / `UpsertResult` / `CollectionInfo`
  - IFC-IB-011: 枚举 `DocStatus` / `SourceKind` / `DegradeReason` / `RouteTier` / `StreamEventKind`
  - IFC-IB-012: 异常类型层次 `IbError` → `ConfigError` / `ScopeViolationError` / `DependencyUnavailableError` / `ValidationError`
- **依赖模块**: 无
- **外部依赖**: 无

### MOD-IB-02 配置 (L0)

- **职责**: 装载全局配置与**项目级**配置；凭据仅从环境变量读取；启动期校验必填项并给出可读错误。
- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）；REQ-NFR-IB-02、IB-07
- **公开接口契约**:
  - IFC-IB-021: `ConfigurationSource.load() -> RawConfig`（文件 + 环境变量合并）
  - IFC-IB-022: `resolve_project_config(project_id: str) -> ProjectConfig | ConfigError`
  - IFC-IB-023: `validate_required(cfg) -> list[ConfigError]`（**只报键名，不回显值**）
  - IFC-IB-024: `GlobalConfig`（含 `EmbeddingConfig` / `VectorStoreConfig` / `RetrievalConfig` / `ChunkingConfig` / `LlmConfig` / `AuthzConfig` / `LoggingConfig` / `BlobConfig` / `WorkerConfig`）
- **依赖模块**: MOD-IB-01
- **外部依赖**: 配置文件解析库（YAML/JSON）；**凭据仅走环境变量**（C-IB-02 / REQ-NFR-IB-07）

### MOD-IB-03 请求上下文 (L0)

- **职责**: 承载请求级机械上下文与鉴权主体；提供鉴权端口（默认拒绝）。
- **覆盖需求**: REQ-FUNC-IB-23（上下文传播）；REQ-NFR-IB-09（AC-IB-11-05）
- **公开接口契约**:
  - IFC-IB-031: `RequestContext(request_id: str, session_key: str, scope_token: str, authz: AuthzContext)`
  - IFC-IB-032: `AuthzPolicy.can_manage(ctx: AuthzContext) -> bool`
  - IFC-IB-033: `AuthzPolicy.can_query(ctx: AuthzContext) -> bool`
  - IFC-IB-034: `DenyAllPolicy`（默认实现，两者恒返回 `False`；未注入即启动报错，AC-IB-11-05）
- **依赖模块**: MOD-IB-01
- **外部依赖**: 无

### MOD-IB-04 可观测性 (L0)

- **职责**: 结构化日志、计时、降级事件发射；**字段白名单 + 脱敏**（FM-8）。
- **覆盖需求**: REQ-NFR-IB-06；REQ-FUNC-IB-21（降级可见）
- **公开接口契约**:
  - IFC-IB-041: `get_logger(stage: str) -> StructuredLogger`
  - IFC-IB-042: `log_event(stage: str, outcome: str, *, project_id: str, kb_id: str | None, doc_id: str | None, elapsed_ms: int | None, error_code: str | None, degrade_reason: DegradeReason | None) -> None`
  - IFC-IB-043: `Timer`（上下文管理式计时，产出 `elapsed_ms`）
  - IFC-IB-044: `emit_degrade(reason: DegradeReason, *, stage: str) -> None`
  - IFC-IB-045: `redact(fields: dict) -> dict`（**禁止正文/片段原文/凭据进入日志**）
- **依赖模块**: MOD-IB-01
- **外部依赖**: 无

### MOD-IB-05 解析器注册表与格式解析器 (L1)

- **职责**: 按扩展名分派解析器；实现 docx / pdf / md / txt 解析，PDF 走三路径（文本层 / 内嵌图像 OCR / 扫描页栅格化 + OCR）。
- **覆盖需求**: REQ-FUNC-IB-10、IB-11（与 MOD-IB-06/08 协作）；AC-IB-04-05、AC-IB-04-06、AC-IB-04-07
- **公开接口契约**:
  - IFC-IB-051: `DocumentParser.supports(ext: str) -> bool`
  - IFC-IB-052: `DocumentParser.parse(source: BinaryIO, *, ocr: OcrEngine, renderer: PageRenderer, spec: ChunkingSpec) -> ParsedDocument`
  - IFC-IB-053: `registry.register(ext: str, parser: DocumentParser) -> None`（**新增格式不改主动线**，AC-IB-04-05）
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04（OCR/渲染以**参数注入**，不静态依赖 MOD-IB-06/08）
- **外部依赖**: `pypdf`（文本主）、`pdfminer.six`（回退）、`pdfplumber`（可选）、`python-docx`

### MOD-IB-06 OCR 端口与 RapidOCR 适配 (L2)

- **职责**: 图像字节 → 文本；引擎不可用时以 `NullOcrEngine` 显式降级为「无文本 + WARNING」。
- **覆盖需求**: REQ-FUNC-IB-11（DR-08）；AC-IB-04-07
- **公开接口契约**:
  - IFC-IB-061: `OcrEngine.available() -> bool`
  - IFC-IB-062: `OcrEngine.recognize(image: bytes, fmt: Literal["png","jpeg"]) -> str`（不可用返回 `""`）
  - IFC-IB-063: `OcrEngine.descriptor() -> OcrDescriptor(engine_id: str, available: bool)`
  - IFC-IB-064: `NullOcrEngine`（`available()->False`，`recognize()->""`，记录 WARNING）
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: `rapidocr-onnxruntime`、`onnxruntime`

### MOD-IB-07 切分器 (L1)

- **职责**: 将 `ParsedDocument` 按可配参数滑窗切分为块（空块过滤）。
- **覆盖需求**: REQ-FUNC-IB-12；AC-IB-05-03
- **公开接口契约**:
  - IFC-IB-071: `Chunker.split(doc: ParsedDocument, spec: ChunkingSpec) -> list[ParsedChunk]`
- **依赖模块**: MOD-IB-01、MOD-IB-02
- **外部依赖**: 无（纯 CPU、纯逻辑，可离线单测）

### MOD-IB-08 页面渲染端口与 pypdfium2 适配 (L2)

- **职责**: PDF 指定页 → 栅格图像字节（供扫描页 OCR）。
- **覆盖需求**: REQ-FUNC-IB-11；AC-IB-04-06
- **公开接口契约**:
  - IFC-IB-081: `PageRenderer.available() -> bool`
  - IFC-IB-082: `PageRenderer.render_page(source: BinaryIO, page_index: int, dpi: int) -> bytes | None`（不可用/超限返回 `None`）
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: `pypdfium2`

### MOD-IB-09 Embedding 端口与本地适配 (L2)

- **职责**: 文本 ↔ 稠密向量；**冷路径（批量、长超时、多重试）与热路径（单条、短超时、少重试）分离**；声明维度与模型标识。
- **覆盖需求**: REQ-FUNC-IB-15（DR-02）；AC-IB-07-01~05
- **公开接口契约**:
  - IFC-IB-090: `Embedder.dim() -> int`
  - IFC-IB-091: `Embedder.model_id() -> str`
  - IFC-IB-092: `Embedder.embed_documents(texts: Sequence[str], *, timeout_s: float, max_retries: int, batch_size: int) -> list[Vector]`（**冷路径**）
  - IFC-IB-093: `Embedder.embed_query(text: str, *, timeout_s: float) -> Vector`（**热路径**，超时即抛 `DependencyUnavailableError` 由 MOD-IB-15 转降级）
  - IFC-IB-094: `Embedder.health() -> HealthStatus`
  - IFC-IB-095: `Embedder.warmup() -> None`
  - IFC-IB-096: `Embedder.descriptor() -> EmbedderDescriptor`
  - IFC-IB-098: `CollectionResolver.resolve(scope: Scope, project: ProjectRecord) -> str`（**唯一** collection 名解析入口；命名 `ib_<project_id>_v<collection_version>`）
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: 本基座 `ib-embed` HTTP 服务；HTTP 客户端（stdlib）
- **R2 增补（L-03 服务端对接）**:
  - IFC-IB-275: `InProcessBgeM3Embedder`（**第三种适配器形态**，本模块**之内**实现）。**不 import MOD-IB-26**——否则产生 `09 → 26` 的非法反向依赖边。装配由 `IB_EMBED_BACKEND=inproc` 选择。
  - **客户端 ↔ 线协议对接表（服务端必须逐条遵守；此表是「已落盘客户端事实」的登记，不是新设计）**：
    | 项 | 客户端已落盘事实（`src/ib/embedding/__init__.py`） | 服务端义务 |
    |----|-----------------------------------------------|------------|
    | 路径 / 请求体 | `POST /embed`，体 `{"texts": [...], "model": ..., "mode": "document"\|"query"}` | 沿用 `/embed`；**不改 `/v1/embeddings`**（改即制造服务端与客户端不同步的 v1 断点） |
    | 响应键 | 读 `vectors` | 返回 `vectors` |
    | 长度 | `len(vectors) != len(texts)` 即抛 `DependencyUnavailableError` | **必须等长**，绝不返回部分向量 |
    | 维度 | `len(vec) != dim` 即抛 | 必须 `== dim == 1024` |
    | 健康 | `GET /healthz` 读 `ok` / `detail`，**永不抛** | 永不 5xx、永不异常 |
    | 预热 | `POST /warmup` 超时 `max(cold_timeout, 300s)`、重试 1、失败仅 WARN | **幂等**；快速失败而非挂死到超时 |
    | 自描述 | `POST /descriptor` 读五字段；失败回落配置值 | 字段名与 MOD-IB-01 `EmbedderDescriptor` **逐字段一致** |
    | 重试分类 | `if exc.code < 500: break`（4xx 不重试） | 错误码分类必须与「4xx=配置/请求错、5xx=暂时故障」严格对齐 |
- **R2 形态一致性强约束**：`http` / `inproc` / `fake` 三形态必须通过**同一套端口一致性测试**（沿用 AC-IB-06-05 的做法）——`descriptor()` 五字段逐字段一致、`dim` / `normalized` 一致、同文本余弦 ≈ 1；否则形态切换会**静默改变写入语义**。

### MOD-IB-10 VectorStore 端口与 Qdrant 适配 (L2)

- **职责**: collection 生命周期、向量 upsert、相似度 query、按 doc/scope 删除、计数、健康检查、flush。
- **覆盖需求**: REQ-FUNC-IB-13、IB-14、IB-16（与 MOD-IB-11 协作）；AC-IB-06-05
- **公开接口契约**:
  - IFC-IB-100: `VectorStore.ensure_collection(spec: CollectionSpec) -> CollectionInfo`
  - IFC-IB-101: `VectorStore.collection_info(spec: CollectionSpec) -> CollectionInfo | None`
  - IFC-IB-102: `VectorStore.list_collections() -> list[str]`
  - IFC-IB-103: `VectorStore.delete_by_collection(collection: str) -> bool`
  - IFC-IB-104: `VectorStore.upsert(points: Sequence[VectorPoint], *, wait: bool) -> UpsertResult`
  - IFC-IB-105: `VectorStore.query(vector: Vector, *, scope: Scope, top_k: int, score_threshold: float, filter: PointFilter | None) -> list[ScoredPoint]`（**`scope` 必填**）
  - IFC-IB-106: `VectorStore.delete_by_doc(scope: Scope, doc_id: str) -> int`（**`scope` 必填**，filter 恒含 `project_id`）
  - IFC-IB-107: `VectorStore.delete_by_scope(scope: Scope) -> int`
  - IFC-IB-108: `VectorStore.count(scope: Scope) -> int`
  - IFC-IB-109: `VectorStore.health() -> HealthStatus`
  - IFC-IB-110: `VectorStore.flush() -> None`
  - 扩展位（v1 不实现，须显式声明「不支持」而非静默失败）：`supports_hybrid_search() -> bool`
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: `qdrant-client`（gRPC :6334 主，REST :6333 回退与健康）

### MOD-IB-11 台账 (L3)

- **职责**: 项目/知识库/文档/块元数据、入库状态机、任务租约、归属断言；**可见性的唯一权威**。
- **覆盖需求**: REQ-FUNC-IB-04、IB-06、IB-08、IB-16、IB-23；REQ-NFR-IB-13
- **公开接口契约**:
  - IFC-IB-120: `LedgerRepository.create_document(scope: Scope, doc_name: str, ext: str, size_bytes: int, content_sha256: str, blob_ref: str | None) -> DocumentRecord`
  - IFC-IB-121: `LedgerRepository.get_document(scope: Scope, doc_id: str) -> DocumentRecord | None`
  - IFC-IB-122: `LedgerRepository.list_documents(scope: Scope, *, page: int, page_size: int, status: DocStatus | None) -> tuple[list[DocumentRecord], int]`
  - IFC-IB-123: `LedgerRepository.set_status(scope: Scope, doc_id: str, status: DocStatus, *, error_code: str | None) -> None`
  - IFC-IB-124: `LedgerRepository.claim_pending(lease_owner: str, lease_seconds: int, limit: int) -> list[DocumentRecord]`（条件 UPDATE 认领）
  - IFC-IB-125: `LedgerRepository.renew_lease(doc_id: str, lease_owner: str, lease_seconds: int) -> bool`
  - IFC-IB-126: `LedgerRepository.reap_expired_leases(now: str) -> int`（崩溃任务回收）
  - IFC-IB-127: `LedgerRepository.mark_indexed(scope: Scope, doc_id: str, collection_version: str, chunk_count: int) -> None`
  - IFC-IB-128: `LedgerRepository.mark_deleted(scope: Scope, doc_id: str) -> None`
  - IFC-IB-129: `LedgerRepository.active_collection_version(project_id: str) -> str` / `activate_collection_version(project_id: str, version: str) -> None`
  - IFC-IB-130: `LedgerRepository.assert_kb_in_project(project_id: str, kb_id: str) -> None`（失败抛 `ScopeViolationError` → HTTP 403）
  - IFC-IB-131: `LedgerRepository.list_chunks(scope: Scope, doc_id: str) -> list[ChunkRecord]` / `list_orphan_doc_ids(project_id: str, existing: Sequence[str]) -> list[str]`（删除重放对账）
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: SQLite（stdlib `sqlite3`；**WAL + busy_timeout 必开**）

### MOD-IB-12 原文件 BlobStore (L3)

- **职责**: 内容寻址持久化原始文件；按 scope 删除。
- **覆盖需求**: REQ-FUNC-IB-08（删除联动）；ADR-05（重建前置 OQ-IB-01）
- **公开接口契约**:
  - IFC-IB-131: `BlobStore.put(scope: Scope, doc_id: str, data: BinaryIO, ext: str) -> BlobRef(sha256: str, rel_path: str, size_bytes: int)`
  - IFC-IB-132: `BlobStore.get(blob_ref: BlobRef) -> bytes | None`
  - IFC-IB-133: `BlobStore.delete(scope: Scope, doc_id: str) -> int`
  - IFC-IB-134: `BlobStore.exists(blob_ref: BlobRef) -> bool`
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: 本地文件系统

### MOD-IB-13 文档生命周期 (L3)

- **职责**: 上传校验 → 落盘 → 解析 → 切分 → 向量化 → 写库 → 置位的全流程编排；删除、重试、并发删除安全退出。
- **覆盖需求**: REQ-FUNC-IB-04、IB-05、IB-06、IB-07、IB-08；AC-IB-01-02/03/04、AC-IB-02-04、AC-IB-04-05/06/07、AC-IB-05-03
- **公开接口契约**:
  - IFC-IB-141: `validate_upload(filename: str, size_bytes: int, head: bytes) -> ValidatedUpload | ValidationError`（扩展名 → 大小 → **魔数签名**，三重校验）
  - IFC-IB-142: `submit_upload(ctx: RequestContext, validated: ValidatedUpload, kb_id: str) -> DocumentRecord`（返回 `pending`；不在请求内做重活）
  - IFC-IB-143: `process_pending(lease_owner: str, limit: int) -> ProcessReport(processed: int, succeeded: int, failed: int, skipped: int)`
  - IFC-IB-144: `delete_document(scope: Scope, doc_id: str) -> DeleteReport(vectors_deleted: int, blob_deleted: bool, ledger_deleted: bool)`
  - IFC-IB-145: `retry_document(scope: Scope, doc_id: str) -> DocumentRecord`
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-05、IB-07、IB-09、IB-10、IB-11、IB-12
- **外部依赖**: 无（第三方库经 MOD-IB-05/06/08/09/10 隔离）
- **R2 增补（M-02：页面图 ↔ 文块绑定）**:
  - **根因（留痕）**：页面文字块与水印/插图 OCR 块此前出自**两次解析产出**，检索命中文字块时**无任何指向同页图片的引用**，导致问答链路「图明明在库里却取不到」。R2 把该关联**在入库期固化**，而不是在检索期做启发式猜测。
  - IFC-IB-277: `bind_page_images(parsed: ParsedDocument, *, doc_id: str) -> list[PageImageBinding]`（**纯函数、无 IO**）：按 `page_or_section` 把该页的 `PageImageRef` 聚合为一条 `PageImageBinding`。同一页的图文块共享同一 `page_or_section` 键即完成绑定；**不向 `ParsedChunk` 追加字段**（避免改动 IFC-IB-009 契约）。
  - IFC-IB-278: `persist_page_images(scope: Scope, doc_id: str, bindings: Sequence[PageImageBinding]) -> int`：按幂等键写入关联表；时机为**向量写入成功之后、台账置 `indexed` 之前**（与 ADR-07 写序一致，保证「`indexed` ⇒ 关联已就绪」）。
  - IFC-IB-279: 关联持久化模型 `ChunkImageRecord`（字段级）：`project_id: str`；`kb_id: str`；`doc_id: str`；`page_or_section: str`；`image_id: str`；`source_kind: str`；`locator: str`；`blob_ref: str | None`；`doc_name: str`；`created_at: str`。**幂等键** = `(project_id, kb_id, doc_id, page_or_section, image_id)`（重跑覆盖同一行，不产生重复）。
  - IFC-IB-280: `process_pending`（IFC-IB-143，**签名与返回类型不变**）的 R2 步骤扩展——七步 → 九步：在**切分**之后、**向量化**之前插入 ① `bind_page_images`；在**写入**之后、**台账置位**之前插入 ② `persist_page_images`。两步**不得**改变既有失败粒度（文档级仍整体 `failed`，页级仍只跳过该页 —— §6.4 不变）。
  - IFC-IB-281（**删除零改动不变式声明**）：`delete_document(scope, doc_id)`（IFC-IB-144）**签名、返回类型与语义一字不改**；关联行随 `(project_id, kb_id, doc_id)` **级联删除**（同一事务内按 scope 删除），故 `DeleteReport` 三个计数（`vectors_deleted` / `blob_deleted` / `ledger_deleted`）语义不变；删除重放对账（IFC-IB-131 `list_orphan_doc_ids`）**不新增用例**。**本项不需要新代码路径，故不引入新 IFC 签名 —— 仅登记为不变式。**

### MOD-IB-14 索引重建 (L3)

- **职责**: 指纹 → 新 collection 版本 → 逐文档 delete-then-write → 全部成功后原子切换 active 版本；断点续跑；单文档失败隔离。
- **覆盖需求**: REQ-FUNC-IB-24（DR-07）；AC-IB-16-01~04
- **公开接口契约**:
  - IFC-IB-151: `plan_rebuild(project_id: str) -> RebuildPlan(from_version: str, to_version: str, target_collection: str, doc_count: int, changed_factors: list[str])`
  - IFC-IB-152: `start_rebuild(project_id: str, plan: RebuildPlan) -> RebuildJob(job_id: str, state: str)`
  - IFC-IB-153: `step_rebuild(job: RebuildJob, lease_owner: str, limit: int) -> RebuildProgress(indexed: int, failed: int, pending: int, done: bool)`
  - IFC-IB-154: `activate_version(project_id: str, version: str) -> None`（**仅在所有目标文档成功后调用**，保证「切换即完整」）
  - IFC-IB-155: `rollback(project_id: str, version: str) -> None`
  - IFC-IB-156: `fingerprint(model_id: str, dim: int, chunk_size: int, chunk_overlap: int, parser_version: str, normalizer_version: str, schema_version: int) -> str`（**纯函数**，取前 8 位十六进制）
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-11、IB-12、IB-13
- **外部依赖**: 无

### MOD-IB-15 检索服务 (L3)

- **职责**: 组装 filter → 热路径向量化 → 向量查询 → 映射为 `RetrievedChunk`；**永不抛异常**，故障转 `degraded` 结果。
- **覆盖需求**: REQ-FUNC-IB-14、IB-16、IB-17、IB-23；AC-IB-06-02、AC-IB-08-03/04、AC-IB-13-01/02、AC-IB-14-01/02
- **公开接口契约**:
  - IFC-IB-161: `RetrievalService.search(query: str, *, scope: Scope, top_k: int, score_threshold: float) -> RetrievalResult`（**无异常出口**）
  - IFC-IB-162: `RetrievalService.search_as_tool(query: str, *, scope: Scope) -> ToolResult`（供 MOD-IB-17 绑定的工具形态）
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-09、IB-10
- **外部依赖**: 无

### MOD-IB-16 专家注册表 (L4)

- **职责**: 专家规格的**唯一真源**（frozen dataclass + 纯 stdlib）；其余模块的专家相关数据一律由此派生。
- **覆盖需求**: REQ-FUNC-IB-02（专家可配置）；REQ-NFR-IB-01（可复用）
- **公开接口契约**:
  - IFC-IB-171: `EXPERT_SPECS: list[ExpertSpec]`（`ExpertSpec(name: str, cn_label: str, keywords: tuple[str, ...], is_data_expert: bool, fallback_prompt: str, is_delegating: bool, is_default: bool)`）
  - IFC-IB-172: `names() -> tuple[str, ...]`；IFC-IB-173: `keywords_map() -> dict[str, tuple[str, ...]]`；IFC-IB-174: `cn_map() -> dict[str, str]`；IFC-IB-175: `fallback_prompts() -> dict[str, str]`；IFC-IB-176: `data_experts() -> tuple[str, ...]`；IFC-IB-177: `delegating_experts() -> tuple[str, ...]`；IFC-IB-178: `default_expert() -> str`；IFC-IB-179: `get(name: str) -> ExpertSpec | None`
- **依赖模块**: MOD-IB-01
- **外部依赖**: **无**（framework-free；不 import langchain/langgraph）

### MOD-IB-17 工具注册与能力摘要 (L4)

- **职责**: 工具注册表；由注册表**纯函数派生**能力摘要；在**构造期**把 scope 绑定进工具闭包（ADR-09 语义段）。
- **覆盖需求**: REQ-FUNC-IB-03、IB-17、IB-23（隔离贯穿路由上下文）
- **公开接口契约**:
  - IFC-IB-181: `register_tool(spec: ToolSpec, fn: Callable[..., ToolResult]) -> None`
  - IFC-IB-182: `build_capability_digest() -> str`（**纯函数**；异常时返回 `""` 而非抛出）
  - IFC-IB-183: `bind_scope(tools: list[RegisteredTool], scope: Scope, retrieval: RetrievalService) -> list[BoundTool]`（**构造期闭包绑定**；骨架只见无参工具）
- **依赖模块**: MOD-IB-01、MOD-IB-15、MOD-IB-16
- **外部依赖**: 无

### MOD-IB-18 语义路由 (L4)

- **职责**: 用向量样例打分 + 阈值/分差判定给出高置信路由；任何异常一律 fail-open 返回 `None`。
- **覆盖需求**: REQ-FUNC-IB-19
- **公开接口契约**:
  - IFC-IB-191: `score_experts(query_vec: Vector, exemplars: dict[str, list[Vector]]) -> dict[str, float]`（**纯函数**）
  - IFC-IB-192: `decide(scores: dict[str, float], tau: float, margin: float) -> str | None`（**纯函数**）
  - IFC-IB-193: `SemanticRouter.route(query: str, *, scope: Scope) -> str | None`（fail-open；样例按 `project_id` 分区，FM-6）
- **依赖模块**: MOD-IB-01、MOD-IB-09、MOD-IB-16
- **外部依赖**: 无

### MOD-IB-19 意图路由内核 (L4)

- **职责**: 四级降级路由 + 粘性 + OOD + 默认专家 + 误路由守卫；**只看当前提问**（剥离历史前缀）。
- **覆盖需求**: REQ-FUNC-IB-19；AC-IB-09-04/05/06/07、AC-IB-15-03
- **公开接口契约**:
  - IFC-IB-201: `classify_experts(query: str, *, history: Sequence[Message], scope: Scope) -> RouteDecision(experts: list[str], tier: RouteTier, confidence: float)`
  - IFC-IB-202: `parse_route_output(raw: str) -> list[str]`（**脏输出容错纯函数**，畸形输入返回空列表）
  - IFC-IB-203: `guard_against_misroute(decision: RouteDecision, scores: dict[str, float]) -> RouteDecision`
- **依赖模块**: MOD-IB-01、MOD-IB-16、MOD-IB-17、MOD-IB-18
- **外部依赖**: 无（LLM 经 `LlmProvider` 注入）

### MOD-IB-20 LLM 端点抽象 (L4)

- **职责**: provider 端口；路由（temperature=0）/ 专家 / 聚合三角色的**内部**构造；外发边界声明。
- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-21；DR-04；AC-IB-12-05、AC-IB-09-07
- **公开接口契约**:
  - IFC-IB-211: `LlmProvider.build_router() -> LlmRole`（`temperature=0`，确定性）
  - IFC-IB-212: `LlmProvider.build_expert(spec: ExpertSpec) -> LlmRole`
  - IFC-IB-213: `LlmProvider.build_aggregator() -> LlmRole`
  - IFC-IB-214: `LlmProvider.health() -> HealthStatus`
  - IFC-IB-215: `LlmProvider.describe_egress() -> EgressDescriptor(remote: bool, endpoint_host: str, data_categories: list[str])`
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: `langchain` / `langchain-openai`（**pin `<0.3`**，见 tech_stack 风险）；HTTP

### MOD-IB-21 流式契约与会话 (L4)

- **职责**: 类型化流事件与 SSE 编码；会话状态端口（默认内存实现，fail-closed）。
- **覆盖需求**: REQ-FUNC-IB-20、IB-21；AC-IB-14-01（降级事件可见）
- **R1 承载声明（ADR-11-R1）**: 事件流由 **Django `StreamingHttpResponse`** 以原生 SSE（`Content-Type: text/event-stream`）承载，运行于同步 WSGI（Waitress 主 / Gunicorn 备）；**不引入 Channels、不引入 Redis**。本模块只负责「事件 → 帧」编码（IFC-IB-224/225），与具体 Web 载体解耦，故框架切换对其**零改动**。
- **R1 鉴权纪律（强制）**: SSE 端点的身份令牌**只允许**经 `Authorization` 请求头（或请求体）注入，**禁止** `?token=` 查询串承载（FreeArk 教训：access log 会完整打印含 token 的 URL，导致令牌泄露）。该纪律落到 §3 MOD-IB-23 IFC-IB-247 与部署检查清单（IFC-IB-264）。
- **公开接口契约**:
  - IFC-IB-221: `SessionStore.load(session_key: str) -> SessionState | None`
  - IFC-IB-222: `SessionStore.save(session_key: str, state: SessionState) -> None`
  - IFC-IB-223: `SessionStore.delete(session_key: str) -> None`
  - IFC-IB-224: `StreamEvent(kind: StreamEventKind, data: str)`（`kind ∈ {reasoning, content, degraded, related_images, error, done}`）
  - IFC-IB-225: `to_sse(event: StreamEvent) -> str`（`event:` / `data:` 帧编码）
  - IFC-IB-282（R2）: `related_images` 事件的**载荷类型化** = `RelatedImagesPayload`（§2.1）。`data` 为该结构的 JSON 编码；**只传 `image_id` 与 `url_path`（站内相对路径），绝不内联图片字节或 base64** —— 帧体积有界，不阻塞流。事件在 `content` 之后、`done` 之前发出；**无图时不发该事件**（而非发空载荷）。`StreamEventKind` 的取值集合**不变**（`related_images` 早已在 IFC-IB-224 中枚举，R2 只定义其 data）。
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: 无

### MOD-IB-22 编排图 (L4)

- **职责**: StateGraph（route → 条件边 fan-out → expert×N / general → gate → aggregate → END）；并行扇出、聚合、流式透传。
- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06
- **公开接口契约**:
  - IFC-IB-231: `build_graph(*, llm: LlmProvider, experts: ExpertRegistry, tools: list[BoundTool], sessions: SessionStore, config: GraphConfig) -> CompiledGraph`（**业务零依赖**：人格/身份文本、scope 一律由调用方已在参数中构造完成）
  - IFC-IB-232: `run(query: str, *, ctx: RequestContext, session_key: str) -> AsyncIterator[StreamEvent]`
  - IFC-IB-233: `resume(session_key: str, payload: dict) -> AsyncIterator[StreamEvent]`
  - State 键（含 reducer）: `messages: Annotated[list[Message], operator.add]`；`expert_results: Annotated[list[ExpertResult], operator.add]`；`plan: list[tuple[str, str]]`；`route_tier: RouteTier`；`query: str`；`degraded: bool`；`step_count: int`（上限 `MAX_EXPERT_STEPS = 8`）
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-16、IB-17、IB-18、IB-19、IB-20、IB-21
- **外部依赖**: `langgraph`

### MOD-IB-23 HTTP API 与组合根 (L5)

- **职责**: **唯一装配点**；REST + SSE 端点；鉴权注入与 `project_id` 解析（不信请求体）；健康检查。
- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23；REQ-NFR-IB-09
- **公开接口契约（HTTP 契约）**:
  - IFC-IB-241: `build_application(deps: CompositionRoot) -> WSGIApplication`（**组合根**：装配全部适配器与替身，见 §5；**R1**：返回类型由 v1.0.0 的 `ASGIApp` 改为 `WSGIApplication`，装配语义不变）
  - IFC-IB-242: `POST /api/files`（multipart）→ `201 DocumentRecord`；`400` 校验失败；`403` 归属断言失败；`5xx` **fail-closed**（台账/Blob 不可用）
  - IFC-IB-243: `GET /api/files?page=&page_size=&status=` → `200 {items: list[DocumentRecord], total: int}`
  - IFC-IB-244: `DELETE /api/files/{doc_id}` → `200 DeleteReport | 404 | 403`
  - IFC-IB-245: `POST /api/files/{doc_id}/retry` → `200 DocumentRecord | 409`（非 `failed` 态）
  - IFC-IB-246: `POST /api/rebuild` → `202 RebuildJob`；`GET /api/rebuild/{job_id}` → `RebuildProgress`
  - IFC-IB-247: `GET /api/chat/stream?session_id=`（**SSE**，`Authorization` 头鉴权）→ `text/event-stream`，逐条 `StreamEvent`（**R1**：由 Django `StreamingHttpResponse` 承载；令牌**禁止**经 `?token=` 查询串传递，仅允许 `Authorization` 头 / 请求体，见 MOD-IB-21 鉴权纪律）
  - IFC-IB-248: `GET /healthz` → `200 {ok: bool}`
  - IFC-IB-249: `GET /healthz/deps` → `200 {qdrant: HealthStatus, embed: HealthStatus, llm: HealthStatus, egress: EgressDescriptor}`
  - IFC-IB-250: 鉴权注入点 `AuthzPolicy`（未注入 → 启动失败；AC-IB-11-05 返回 `401/403` 而非静默）
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04，并装配 L1~L4 全部实现（§5）
- **外部依赖**: `django`、`djangorestframework`、`waitress`（主 WSGI）、`gunicorn`（备 WSGI）；并发升级路径见 tech_stack §1（Gunicorn + `uvicorn.workers.UvicornWorker`，默认关闭）
- **R2 新增端点（M-02 读路径）**:
  - IFC-IB-283: `GET /api/files/{doc_id}/images/{image_id}` → `200`（`Content-Type: image/*`，字节流，可缓存）| `403`（归属断言失败）| `404`（文档或图片不存在；**不区分「不存在」与「不属于你」**，避免存在性探测 —— 沿用 §1.4 第 2 条口径）| `503`（BlobStore 不可用；**fail-closed**：直接报错，不返回占位图）。
  - **鉴权纪律（强制）**：沿用 IFC-IB-247 的口径，**仅允许 `Authorization` 头** / 中间件鉴权；本端点**不接受** `?token=`（MOD-IB-21 的鉴权纪律对**全部**端点生效，R2 显式扩展到图片端点）。
  - **单一取图入口**：前端与 SSE 载荷一律只引 `url_path`，字节一律经本端点按需获取。
  - `GET /healthz/deps`（IFC-IB-249）的字段集合**不变**：取图依赖 BlobStore，其健康语义已由既有字段与 §7.4 覆盖，**不新增字段**。
- **R1 装配语义不变声明**: §5 组合根装配表的全部 `IB_*_BACKEND` 开关与环境变量名**保持不变**（`IB_VECTORSTORE_BACKEND` / `IB_EMBED_BACKEND` / `IB_LLM_BACKEND` / `IB_OCR_ENABLED` / `IB_RENDER_ENABLED` / `IB_LEDGER_BACKEND` / `IB_BLOB_STORE_ENABLED` / `IB_SESSION_BACKEND` / `IB_CONFIG_SOURCE` / `IB_OFFLINE_MODE`）；框架切换只改变 HTTP 承载实现，**不新增/不改名任何配置键**，避免与 FreeArk 现有 `RAG_*` 环境变量约定冲突。

### MOD-IB-24 Web 前端 (L5)

- **职责**: 上传/列表/删除/重试/重建页 + 问答页；仅通过类型化 HTTP/SSE 契约与后端交互。
- **覆盖需求**: REQ-FUNC-IB-09、IB-17
- **公开接口契约（TS 类型与后端契约一一对应）**:
  - IFC-IB-256: `UploadPage`（消费 242/243/244/245）
  - IFC-IB-257: `ChatPage`（消费 247；渲染 `content`/`degraded`；`degraded` 时展示「当前未接入知识资料库」）
  - IFC-IB-258: `RebuildPage`（消费 246）
  - IFC-IB-259: `apiClient.ts`：`type DocumentRecord`、`type RetrievalResult`、`type StreamEvent` 等与后端字段**逐字段对齐**
- **依赖模块**: MOD-IB-23（**仅** HTTP/SSE 契约；不 import 任何后端模块）
- **外部依赖**: Vue 3、Vite、构建产物由 `ib-web` 静态托管
- **R2 渲染约束（IFC-IB-284）**:
  - `related_images` 事件到达时，在**该轮回答下方**以缩略图行渲染（点击经 IFC-IB-283 取原图）；**不得**插入正文中间，**不得**改写 `content` 文本。
  - 渲染顺序 = 载荷顺序（服务端按 `page_or_section` 升序给出，**前端不重排**）。
  - 图片加载失败 / 端点 `403` / `404` / `503` → **静默隐藏该缩略图**（不弹错误、不中断流、**不追加降级文案**）。降级文案**只对 `degraded` 事件负责** —— 避免同一观察点出现两种降级语义，对齐 ADR-13「故障与空结果可区分」。

### MOD-IB-25 部署运维 (L5)

- **职责**: 四个 systemd 单元、EnvironmentFile 模板、启动期必填校验、依赖真机验证清单、Qdrant 安装检查清单。
- **覆盖需求**: REQ-FUNC-IB-22（DR-03）；REQ-NFR-IB-07、IB-10
- **公开接口契约（交付物清单，非代码）**:
  - IFC-IB-261: 四个 systemd 单元定义（`qdrant` / `ib-embed` / `ib-web` / `ib-worker`）
  - IFC-IB-262: `.env.example` 模板（**无真实值**）
  - IFC-IB-263: 启动期校验：缺失必填项 → 非零码退出 + 指明**键名** + 不回显值（AC-IB-12-03）
  - IFC-IB-264: 依赖真机验证清单（Qdrant / bge-m3 / OCR **真装、真导入、真跑通**，产出可复查证据；AC-IB-12-04）
  - IFC-IB-265: Qdrant 安装检查清单（专用用户 / `storage`+`snapshots` 目录 / unit 文件 / `LimitNOFILE`）
  - IFC-IB-286（R2）: `ib-embed` 的 `EnvironmentFile` 模板（**第二份 `.env.example`**，与 `ib-web` 的键集合**分离**）。**只登记键名、不含任何值**；键名清单见 `tech_stack.md` §1.2，语义与默认值见 `docs/ib_embed_service_contract.md` §9。**凭据纪律**：该服务**不需要任何令牌**，不得向该文件写入任何凭据（加进去就是净增凭据面）。
  - R2 重申：IFC-IB-261 的**单元清单不变**（`ib-embed` 单元**早已存在**；L-03 缺的是**模块归属与契约**，不是单元文件）；IFC-IB-263 的「只报键名、不回显值、非零码退出」纪律对第二份模板同样生效。
- **依赖模块**: MOD-IB-01、IB-02、IB-04
- **外部依赖**: `systemd`

### MOD-IB-26 ib-embed 服务端 (L2；服务端进程)

> **R2 新增（L-03 补齐）**。**本节为摘要视图**；唯一权威为 `docs/ib_embed_service_contract.md`，二者冲突时**以契约文件为准**。本模块**不含部署配置**（部署配置属 MOD-IB-25）。

- **职责**: bge-m3 常驻推理服务的**线协议实现与模块归属**；单模型常驻、CPU-only、有界并发 + 有界队列、超限快速失败（绝不无界排队）。
- **覆盖需求**: REQ-FUNC-IB-15（本地 embedding，服务端侧）；REQ-FUNC-IB-22（`ib-embed` 单元交付物）；REQ-NFR-IB-03（检索性能的服务端侧）；REQ-NFR-IB-10（CPU-only 可运行）
- **公开接口契约（HTTP 线协议）**:
  - IFC-IB-266: `POST /embed`（请求 `texts`/`model`/`mode`；响应 `vectors`/`dim`/`model_id`/`normalized`/`count`/`elapsed_ms`；**保序**；**绝不返回部分向量**）
  - IFC-IB-267: 维度权威性与**三方一致性**（服务端真实维度 → 客户端 `IB_EMBED_DIM` → `CollectionSpec.dim`；三者任一不符须在最早可发现处失败）
  - IFC-IB-268: 错误码表与统一错误体 `{code, detail, max_batch?, retry_after_s?}`，含**分类不变式：`4xx/409 = 重试无用`，`5xx = 重试可能有用`**
  - IFC-IB-269: `GET /healthz`（**永不 5xx、永不抛**；客户端只读 `ok` / `detail`，其余字段为附加且向后兼容）
  - IFC-IB-270: `POST /warmup`（**幂等**；须在 300s 量级内完成或快速失败，**不得挂死到超时**）
  - IFC-IB-271: `POST /descriptor` → `EmbedderDescriptor`（五字段与 MOD-IB-01 **逐字段一致**，不得新增/改名）
  - IFC-IB-272: 批上限 / 单条截断保前缀 / **服务端 `MAX_BATCH` ≥ 客户端 `cold_batch_size`** 硬约束（错误体回显 `max_batch`，使配置错配一眼可定位）
  - IFC-IB-273: 冷/热双路径超时纪律的**单一落点** —— **服务端不区分冷热**（无状态 HTTP），冷热差异全部由**客户端的两个实例**承载
  - IFC-IB-274: 形态可逆（`http`/`inproc`/`fake`）+ 服务端配置**键名**清单 + 端口一致性测试
- **依赖模块**: MOD-IB-01（契约 / 枚举）、MOD-IB-02（配置）、MOD-IB-04（可观测性）
- **外部依赖**: 服务端推理运行时（候选与许可见 `tech_stack.md` §1「Embedding 推理运行时」行）；bge-m3 本地权重（**离线加载**）
- **不被 import 声明（R2 强制）**: 本模块**不被任何模块 import** —— 上层只经 `Embedder` 端口（MOD-IB-09）与线协议访问（与 MOD-IB-10 对 Qdrant 服务同构）。这是 §4.2 无环论证在本模块上的**唯一依据**，也是「形态可逆」成立的前提（进程内形态不得依赖服务端）。

---

## 4. 依赖关系图与 DAG 无环证明

### 4.1 依赖边清单（`A → B` 表示 A 依赖 B）

```
MOD-IB-01 → （无）
MOD-IB-02 → 01
MOD-IB-03 → 01
MOD-IB-04 → 01
MOD-IB-05 → 01, 02, 04
MOD-IB-06 → 01, 02, 04
MOD-IB-07 → 01, 02
MOD-IB-08 → 01, 02, 04
MOD-IB-09 → 01, 02, 04
MOD-IB-10 → 01, 02, 04
MOD-IB-11 → 01, 02, 04
MOD-IB-12 → 01, 02, 04
MOD-IB-13 → 01, 02, 03, 04, 05, 07, 09, 10, 11, 12
MOD-IB-14 → 01, 02, 03, 04, 11, 12, 13
MOD-IB-15 → 01, 02, 03, 04, 09, 10
MOD-IB-16 → 01
MOD-IB-17 → 01, 15, 16
MOD-IB-18 → 01, 09, 16
MOD-IB-19 → 01, 16, 17, 18
MOD-IB-20 → 01, 02, 04
MOD-IB-21 → 01, 02, 04
MOD-IB-22 → 01, 02, 03, 04, 16, 17, 18, 19, 20, 21
MOD-IB-23 → 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
MOD-IB-24 → 23（仅 HTTP/SSE 契约，非编译期模块依赖）
MOD-IB-25 → 01, 02, 04（交付物形态，非编译期依赖）
MOD-IB-26 → 01, 02, 04（**本模块不被任何模块 import**；只走线协议，非编译期依赖）
```

### 4.2 无环证明（构造性）

**命题**：上述依赖图是 DAG。

**证明**：为每个模块赋权 `w(MOD-IB-n) = n`。逐条检查 §4.1 的每一条依赖边 `A → B`，均有 `w(A) > w(B)`（即被依赖者编号恒小于依赖者编号）。因此**每条边的权值严格递减**。若图中存在环 `M1 → M2 → … → Mk → M1`，则沿环有 `w(M1) > w(M2) > … > w(Mk) > w(M1)`，矛盾。故无环。∎

**该性质是设计约束而非巧合**：模块编号按**拓扑序**分配，新增模块须选取「大于其全部依赖编号」的编号；若出现「新需求使某模块需要依赖编号更大的模块」，则说明**分层被破坏**，必须先重构分层（例如下沉契约或引入端口），不得直接加边。这条纪律写在此处，作为后续 GROUP_C 的架构约束。

**R2 补句（新增模块的权值校验）**：R2 新增的 `MOD-IB-26` 只有三条出边 `→ 01, 02, 04`，且 `w(26) = 26 > max{w(01), w(02), w(04)} = 4` —— 权值严格递减的性质**保持不变**；同时 26 号模块**没有任何入边**（不被任何模块 import），因此**不可能出现在任何环上**。**结论：R2 后依赖图仍为 DAG。**

**关键的「看似会成环」的三处，及其化解方式**：
1. `MOD-IB-13（入库）` 需要解析器（05/07）与存储（09/10/11/12）——但 05/07 只依赖 01/02/04，**不反向依赖 13**，故无环。
2. `MOD-IB-14（重建）} 需要 `MOD-IB-13`（复用入库管线）——13 不依赖 14，无环。
3. `MOD-IB-22（编排）` 需要 `MOD-IB-15`？**不需要**：编排只依赖 `MOD-IB-17`（已绑 scope 的工具），而 **scope 绑定发生在 23（组合根）**，故编排对检索是**间接的、构造期注入的**，编译期无依赖边。这正是 ADR-09 依赖反转的具体体现（否则 22 → 15 与 17 → 15 会与 15 → …→ 22 形成闭环风险）。

### 4.2.1 R1 无环性再声明（框架切换后）

**结论：DAG 拓扑在 R1 下不变，无环证明（§4.2）继续成立。**

- §4.1 依赖边清单**零改动**：框架切换只替换 MOD-IB-23（组合根 / HTTP 层）的**外部依赖载体**（`fastapi`/`uvicorn` → `django`/`djangorestframework`/`waitress`/`gunicorn`），MOD-IB-23 的**内部依赖边**（→ 01~22）与其余 24 个模块的依赖边完全不变，故权值 `w(MOD-IB-n)=n` 严格递减的构造性证明不受影响。
- 新增的 §2.1.1 载体映射**不引入任何新模块、不引入任何新依赖边**；Django 类型仅允许出现在 MOD-IB-23 内（见 §2.1.1 不变式），不构成对核心契约 MOD-IB-01 的反向渗透。
- 因此「编号即拓扑序」的纪律继续适用于 GROUP_C：新增模块须选取大于其全部依赖的编号，Django 适配不得绕开端口直接跨层调用。

### 4.3 分层视图

```
L5  MOD-IB-23 ── MOD-IB-24   MOD-IB-25
     ▲
L4  MOD-IB-16  17  18  19  20  21  →  MOD-IB-22
     ▲
L3  MOD-IB-11  12  13  14  15
     ▲
L2  MOD-IB-06  08  09(含 CollectionResolver)  10   26(独立服务端进程；不被任何模块 import)
     ▲
L1  MOD-IB-05  07
     ▲
L0  MOD-IB-01  02  03  04
```

**单向铁律**：箭头只向上（依赖只向下层）。**跨层反向依赖一律通过端口注入解决**（如 MOD-IB-13 → MOD-IB-05/07 是向下依赖，合规；MOD-IB-05 需要 OCR 但以**参数注入**而非静态依赖 MOD-IB-06，避免横向耦合）。

---

## 5. 组合根装配表（MOD-IB-23）

运行期装配与编译期依赖分离：**所有适配器选择集中在此处**，上层模块只见端口。

| 端口 | 生产装配 | 离线/测试装配 | 配置开关 |
|------|----------|---------------|----------|
| `VectorStore` | `QdrantVectorStore` | `InMemoryVectorStore` | `IB_VECTORSTORE_BACKEND=qdrant\|memory` |
| `Embedder` | `LocalHttpEmbedder`（→ `ib-embed`，MOD-IB-26 服务端） | `FakeEmbedder` / `InProcessBgeM3Embedder` | `IB_EMBED_BACKEND=http\|inproc\|fake`（**R2 仅扩展值域；键名与默认值 `http` 不变**） |
| `LlmProvider` | `OpenAiCompatibleProvider`（DeepSeek） | `FakeLlmProvider` | `IB_LLM_BACKEND=openai_compatible\|fake` |
| `OcrEngine` | `RapidOcrEngine` | `NullOcrEngine` | `IB_OCR_ENABLED=true\|false` |
| `PageRenderer` | `PdfiumRenderer` | `NullRenderer`（返回 `None`） | `IB_RENDER_ENABLED=true\|false` |
| `LedgerRepository` | `SqliteLedgerRepository` | `InMemoryLedgerRepository` | `IB_LEDGER_BACKEND=sqlite\|memory` |
| `BlobStore` | `FsBlobStore` | `InMemoryBlobStore` | `IB_BLOB_STORE_ENABLED=true\|false` |
| `SessionStore` | `MemorySessionStore` | 同（内存实现即替身） | `IB_SESSION_BACKEND=memory` |
| `AuthzPolicy` | 接入方注入 | `DenyAllPolicy` | **未注入即启动失败** |
| `ConfigurationSource` | 文件 + 环境变量 | 测试用固定字典 | `IB_CONFIG_SOURCE=file\|dict` |

> **R2 形态可逆开关说明**：`inproc` = 进程内 `InProcessBgeM3Embedder`（位于 **MOD-IB-09 之内**，**不 import MOD-IB-26**）；切换代价 = 改一个配置值 +（可选）停用 `ib-embed` 单元，**不改任何上层模块、不改 IFC 签名、不改任何既有键名**。三形态须通过**同一套端口一致性测试**（见 §3 MOD-IB-09）。默认保持 `http`：进程内形态的模型内存 × worker 数风险与「与 onnxruntime 同进程」的内存叠加峰值（[TBD-T4']）仍未实测。
> （R2 附：`IB_EMBED_BACKEND` 的**值域**扩展与 `IB_OFFLINE_MODE=1` 的一键离线语义**相容**——离线时仍取该表的「离线/测试」列。）

**一键离线**：`IB_OFFLINE_MODE=1` 等价于把上表全部置为「离线/测试」列（AC-IB-15-01、附录 D）。

---

## 6. 数据处理管线：状态机、幂等与租约（MOD-IB-13 / MOD-IB-14）

### 6.1 文档状态机

| 状态 | 含义 | 允许的下一状态 | 触发 |
|------|------|----------------|------|
| `pending` | 已登记，等待 worker | `parsing` / `failed` / （被删除） | `submit_upload` |
| `parsing` | 已被认领，处理中（有租约） | `indexed` / `failed` / `pending`（租约超时回收） | `claim_pending` |
| `indexed` | 向量已写入且台账已置位 | （仅重建时重入） | `mark_indexed` |
| `failed` | 终态（需人工重试） | `pending`（手动重试） | 任一阶段异常 |

**不变量**：`status == indexed` ⇒ 该文档的向量已存在于 `indexed_collection_version` 指向的 collection 中（ADR-07 写序保证）。

### 6.2 幂等键

| 对象 | 幂等键 | 语义 |
|------|--------|------|
| 向量点 | `doc_id` + `chunk_index`（→ `point.id`） | 重跑覆盖同一批点，不产生重复 |
| 文档向量集合 | `(scope, doc_id)` | 写入前先 `delete_by_doc`，delete-then-write |
| 原文件 | `sha256` | 内容寻址；同内容不重复占空间 |
| collection 版本 | `fingerprint(...)`（IFC-IB-156） | 同一组参数恒得同一版本号 |
| 重建任务 | `(project_id, target_collection_version)` | 重跑跳过已达目标版本的文档 |

### 6.3 任务租约字段与语义（ADR-10）

`DocumentRecord` 中 `lease_owner: str | None`、`lease_expires_at: str | None`。认领 = 条件 UPDATE（`status='pending' AND (lease_expires_at IS NULL OR lease_expires_at < now)`）并写入 `lease_owner`/`lease_expires_at`；处理中定期 `renew_lease`；`reap_expired_leases` 把过期任务重置为 `pending`。**入库任务与重建任务共用租约机制但状态标记不同**，二者对同一文档互斥。

### 6.4 失败粒度与重试

| 粒度 | 失败处理 | 依据 |
|------|----------|------|
| 文档 | 置 `failed` + `error_code`；**不阻塞其他文档** | AC-IB-16-04 的推广 |
| 页面（OCR 单页） | 跳过该页 + `WARNING`，文档仍可 `indexed` | AC-IB-04-07 |
| 块 | 无此粒度（块是派生物，重建即可再生） | 设计取舍 |

重试：手动重试（IFC-IB-145）/ 租约超时自动回收 / 次数上限（超限即终态 `failed`，**不允许无限自动重试**）。

### 6.5 重建流程与时序（MOD-IB-14）

```
plan_rebuild → [建新 collection ib_<pid>_v<new>] → step_rebuild（循环：逐文档 delete-then-write，续租）
                                                     ↓ 全部成功
                              activate_version（台账原子写 active_collection_version = new）
                                                     ↓
                              读路径切到新 collection（旧 collection 保留待人工确认删除 → 回滚窗口）
```

| 阶段 | 读行为 | 写行为 | 依据 |
|------|--------|--------|------|
| 重建进行中 | **读旧 collection（服务可用，内容非最新）** | 按配置写入目标 collection 并在响应回显 | AC-IB-16-03 |
| 切换瞬间 | 台账单值切换，**无混合读窗口** | 同左 | ADR-05 |
| 切换后 | 读新 collection | 写新 collection | — |
| 单文档失败 | 旧 collection 仍可读该文档 | 该文档 `failed`，**不切换版本** | AC-IB-16-04 |

---

## 7. 编排详设（MOD-IB-16 ~ MOD-IB-22）

### 7.1 图结构

| 节点 | 职责 | 出边 |
|------|------|------|
| `route` | 调 MOD-IB-19 得 `RouteDecision` | 条件边：`_fan_out` 返回 `Send("expert", …)` 列表或 `"general"` |
| `expert` | 以绑定的专家 prompt + 已绑 scope 的工具作答；支持**并行多实例** | → `gate` |
| `general` | 通用回答（无需知识库） | → `aggregate` |
| `gate` | 步数上限（`MAX_EXPERT_STEPS = 8`）与写操作确认门（**默认关闭**，OQ-IB-07） | → `aggregate` |
| `aggregate` | 合并多专家结果；**禁止暴露内部分工**（AC-IB-09-03） | → `END` |

`State` 用 `Annotated[..., operator.add]` 收集并行结果（`messages`、`expert_results`）；`step_count` 单调递增用于限步。

### 7.2 路由四级降级与兜底

| 级 | 判据 | 失败/未命中 |
|----|------|-------------|
| L0 | 关键词**唯一**命中 | 进入 L1 |
| L1 | 语义高置信（`τ` + `margin`，IFC-IB-192） | **fail-open → None**，进入 L2 |
| L2 | LLM 分类器（`temperature=0`），输出经 IFC-IB-202 容错解析 | 解析为空 → L3 |
| L3 | 关键词命中（多重） | → 粘性 → OOD → 默认专家 |
| 粘性 | 沿用上一轮专家（AC-IB-09-05） | — |
| OOD | 明确表态且无任何信号（AC-IB-09-04 反面） | — |
| 默认 | 保证「永远有人回答」（AC-IB-09-04） | — |
| 守卫 | 单专家 + 低置信 + 与原路由矛盾 → 纠正（IFC-IB-203） | — |

### 7.3 流式契约与会话

事件 `kind`：`reasoning`（若可得）/ `content` / `degraded` / `related_images` / `error` / `done`。**降级必须在流内可见**（AC-IB-14-01 的界面落点）。单专家时透传该专家 token；多专家时输出聚合结果。会话键 `session_key = f"{project_id}:{actor_id}:{session_id}"`，读取时断言前缀（FM-7）。

### 7.4 降级矩阵（依赖 × 故障 × 行为 × 用户可见 × 日志级别 × fail 语义）

| 依赖 | 故障情形 | 系统行为 | 用户可见 | 日志级别 | fail 语义 |
|------|----------|----------|----------|----------|-----------|
| **台账** | 不可用 | 上传/删除/列表返回 `503`，**不产生半成品状态** | 「服务暂时不可用，请稍后重试」 | ERROR | **fail-closed** |
| **BlobStore** | 不可用（或功能关闭） | 上传返回 `503`（功能关闭时启动期告警 + 相关 API 明确报错） | 「原文件存储不可用」 | ERROR / WARN | **fail-closed** |
| **Embedding** | 超时 / 不可达 | 检索返回 `degraded=True, degrade_reason=embedding_unavailable, hits=[]`；**问答继续** | 「当前未接入知识资料库」 | WARN | fail-open |
| **Embedding** | 热路径超时（短超时触发） | 同上，`degrade_reason=timeout` | 同上 | WARN | fail-open |
| **ib-embed 服务（MOD-IB-26）** | 不可达 / 未预热（`model_not_ready`）/ 队列满（`overloaded`）/ 服务端推理超时（`inference_timeout`） | 检索侧 `degraded=True`：不可达 → `degrade_reason=embedding_unavailable`；热路径超时 → `timeout`；**问答继续**。冷路径（入库）**不在此列**：由客户端重试预算承载，耗尽则**文档级** `failed` + `error_code`（**不阻塞其他文档**） | 「当前未接入知识资料库」 | WARN | fail-open（读路径）；冷路径为文档级失败隔离 |
| **页面图（M-02）** | 关联行缺失 / 图片字节不可得（Blob `503`、原文件已删、`blob_ref` 为空） | `related_images` **不发事件**（有图才发）；图片端点返回 `404` / `503`；**检索与回答不受影响**（图是增强项，不是前提） | 无感（缩略图静默隐藏） | WARN | fail-open（增强项） |
| **VectorStore** | 不可达 / 查询报错 | `degraded=True, degrade_reason=vectorstore_unavailable` | 「当前未接入知识资料库」 | ERROR | fail-open |
| **知识库为空** | 正常但无数据 | `degraded=False, hits=[]`（**与上两行可区分**，AC-IB-14-02） | 「未找到相关资料」 | INFO | 非降级 |
| **LLM 端点** | 不可达 / 限流 | 问答返回 `error` 事件 + 可读文案；路由降级到关键词档位 | 「模型服务暂时不可用」 | ERROR | fail-open（问答层） |
| **路由分类器** | LLM 分类失败 | 逐级降级 → 关键词 → 粘性 → 默认专家 | 无感（不暴露内部分工） | WARN | fail-open |
| **OCR 引擎** | 未安装 / 加载失败 | `NullOcrEngine`：扫描页按「无文本」处理，文档仍可 `indexed` | 无感（文档列表可标注「未识别到文本」） | WARN | fail-open（AC-IB-04-07） |
| **页面渲染** | 不可用 | 扫描页路径不可用；文本层路径正常 | 无感 | WARN | fail-open |
| **语义路由样例缓存** | 无本项目样例 | 跳过 L1，进入 L2（**不误用他项目样例**，FM-6） | 无感 | INFO | fail-open |
| **WSGI 工作进程**（R1 新增） | SSE 长连接占满同步 worker（Waitress / Gunicorn sync worker 被长连接占据，新请求排队） | 排队超时或返回 `503`；**fail-closed 明确报错，不静默空转**（并发上限 `[TBD-T15]` 复核前按保守 worker 数与 SSE 超时配置） | 「服务繁忙，请稍后重试」 | WARN | **fail-closed（容量）** |

---

## 8. 测试替身清单（REQ-NFR-IB-14）

| 端口 | 生产实现 | 替身（离线/测试） | 覆盖的行为差异 |
|------|----------|-------------------|----------------|
| `VectorStore` | `QdrantVectorStore` | `InMemoryVectorStore`（暴力余弦，与本基座同度量） | 需通过**同一套端口一致性测试**（AC-IB-06-05） |
| `Embedder` | `LocalHttpEmbedder` | `FakeEmbedder`（确定性伪向量） | 冷/热路径、超时、不可达三态 |
| `LlmProvider` | `OpenAiCompatibleProvider` | `FakeLlmProvider`（可编排脏输出、超时、限流） | 路由解析健壮性（AC-IB-15-03） |
| `OcrEngine` | `RapidOcrEngine` | `NullOcrEngine` / `StubOcrEngine`（固定文本） | 引擎缺失降级（AC-IB-04-07） |
| `PageRenderer` | `PdfiumRenderer` | `NullRenderer` | 渲染不可用降级 |
| `LedgerRepository` | `SqliteLedgerRepository` | `InMemoryLedgerRepository` | 状态机、租约、并发认领 |
| `BlobStore` | `FsBlobStore` | `InMemoryBlobStore` | 内容寻址、删除联动 |
| `SessionStore` | `MemorySessionStore` | 同（自身即内存实现） | 会话隔离键断言 |
| `AuthzPolicy` | 接入方注入 | `DenyAllPolicy` | 401/403 而非静默（AC-IB-11-05） |
| `ConfigurationSource` | 文件 + 环境变量 | 固定字典 | 必填校验与可读错误 |

**离线可测的纯逻辑单元**（无外部 IO，AC-IB-15-02）：MOD-IB-01（契约校验）、MOD-IB-02（配置合并与校验）、MOD-IB-07（切分）、MOD-IB-05（注册表分派）、MOD-IB-18（打分与判定）、MOD-IB-19（`parse_route_output` 脏输出）、MOD-IB-14（`fingerprint`）。

---

## 9. REQ → MOD 覆盖率矩阵

### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-24，**24/24 全覆盖**）

| REQ | 需求要点（摘要） | 覆盖模块（主 / 辅） |
|-----|------------------|---------------------|
| IB-01 | 通用化：新项目零改动核心代码 | **MOD-IB-02** / 01, 22 |
| IB-02 | 可配置：项目级配置与专家可配置 | **MOD-IB-16** / 02 |
| IB-03 | 工具注册与能力摘要 | **MOD-IB-17** / 16 |
| IB-04 | 上传后异步入库、状态可查 | **MOD-IB-13** / 11, 23 |
| IB-05 | 上传校验（格式/大小/上限可配） | **MOD-IB-23** / 02, 13 |
| IB-06 | 文档列表与状态展示 | **MOD-IB-23** / 11 |
| IB-07 | 入库顺序与批量 | **MOD-IB-13** / 10, 11 |
| IB-08 | 文档删除（含原文件与向量） | **MOD-IB-13** / 12, 11, 23 |
| IB-09 | Web 数据导入界面 | **MOD-IB-24** / 23 |
| IB-10 | 多格式解析（docx/pdf/md/txt） | **MOD-IB-05** / 07 |
| IB-11 | 扫描件 OCR（+ 渲染） | **MOD-IB-06, MOD-IB-08** / 05 |
| IB-12 | 文本切分 | **MOD-IB-07** / 05 |
| IB-13 | 向量写入（含 collection 管理） | **MOD-IB-10** / 13 |
| IB-14 | 相似度检索 | **MOD-IB-15** / 10 |
| IB-15 | 本地 embedding（bge-m3） | **MOD-IB-09, MOD-IB-26** / 10（09 = 客户端端口与冷热双路径；26 = 服务端线协议） |
| IB-16 | 台账与向量库一致性 | **MOD-IB-11** / 13, 10, 15 |
| IB-17 | 检索结果供专家使用（工具化） | **MOD-IB-17** / 15 |
| IB-18 | 多智能体问答 | **MOD-IB-22** / 16, 19, 20 |
| IB-19 | 多级意图路由 | **MOD-IB-19** / 18 |
| IB-20 | 会话生命周期 | **MOD-IB-21** / 22 |
| IB-21 | 流式输出 | **MOD-IB-21** / 22, 23 |
| IB-22 | 部署（systemd 单元、配置模板） | **MOD-IB-25** / 02 |
| IB-23 | 多项目隔离（贯穿全链路） | **MOD-IB-03** / 02, 09(Resolver), 10, 11, 12, 15, 17, 23 |
| IB-24 | 索引重建 | **MOD-IB-14** / 12, 13 |

**无缺口**：24 条 REQ-FUNC 每条至少一个「主」模块，且每条均可被至少一个 AC 验证。

### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-14）

| REQ | 需求要点 | 覆盖模块（主 / 辅） |
|-----|----------|---------------------|
| NFR-01 | 通用性与可复用性 | **MOD-IB-01** / 16, 17, 22 |
| NFR-02 | 可配置性 | **MOD-IB-02** |
| NFR-03 | 检索性能（P95） | **MOD-IB-09** / 10, 15（指标 TBD-T1/T6） |
| NFR-04 | 入库吞吐与请求响应性 | **MOD-IB-13** / 09, 10 |
| NFR-05 | 中文检索效果 | **MOD-IB-09** / 07（阈值 TBD-T12） |
| NFR-06 | 可观测性 | **MOD-IB-04** |
| NFR-07 | 安全性-凭据管理 | **MOD-IB-02** / 25 |
| NFR-08 | 安全性-数据不出本地（含外发声明） | **MOD-IB-20** / 09, 10, 25 |
| NFR-09 | 权限与访问控制 | **MOD-IB-03** / 23 |
| NFR-10 | 可移植性与算力适配 | **MOD-IB-09** / 25, 26 |
| NFR-11 | 可维护性与模块边界 | **MOD-IB-01**（全模块的端口化基础） |
| NFR-12 | 许可合规 | **MOD-IB-05, MOD-IB-06, MOD-IB-08**（选型见 tech_stack.md） |
| NFR-13 | 可靠性与降级 | **MOD-IB-04** / 15, 21 + §7.4 降级矩阵 |
| NFR-14 | 可测试性 | **MOD-IB-01** / §8 替身清单 |

### 9.3 R1 覆盖率再声明（框架切换后）

**结论：24/24 REQ-FUNC + 14 REQ-NFR 覆盖情况在 R1 下不变，无新增缺口。**

- 框架切换只替换 MOD-IB-23 的 HTTP 载体，**不改变任何 REQ 的覆盖模块**：REQ-FUNC-IB-05/06/09/21/23 的主覆盖模块（MOD-IB-23 / MOD-IB-24）未变，仅其内部实现载体由 FastAPI 改为 Django（DRF 视图 + `StreamingHttpResponse`）。
- NFR 侧：NFR-08（数据不出本地 + 外发声明，主覆盖 MOD-IB-20）与 NFR-09（权限与访问控制，主覆盖 MOD-IB-03 / 23）语义不变——鉴权端口 `AuthzPolicy` 仍默认拒绝（`DenyAllPolicy`），Django 中间件/视图装饰器只是其 HTTP 层注入点（见 §2.1.1）。
- 因此 §9.1 / §9.2 矩阵逐行有效，无需改动；本文档仍满足门控「REQ → MOD 全覆盖」标准。

### 9.4 R2 覆盖率再声明（L-03 增量）

**结论：24/24 REQ-FUNC + 14 REQ-NFR 覆盖不变，无新增缺口；R2 的新增只**加固**既有覆盖，不改任何既有主/辅归属。**

- **REQ-FUNC-IB-15**（本地 embedding）：R2 前只有 `MOD-IB-09`（端口 + 客户端）承载，**服务端无模块归属**——这正是 L-03；R2 由 `MOD-IB-26` 补上服务端侧（主覆盖并列：09 = 端口/客户端，26 = 服务端线协议）。
- **M-02（页面图绑定）不新增 REQ**：它落在 REQ-FUNC-IB-10 / IB-11（解析并产出页面图）与 IB-14 / IB-17（检索、供专家使用）的**既有语义**之内，故只**增辅覆盖**（MOD-IB-01 / 13 / 21 / 23 / 24），**不新增需求条目、不改变 24/24 的判定**。
- 若 PM 认为「图片回溯」应升格为**独立 REQ**，须回**需求侧**立项 —— 架构层**不自行新增 REQ**（见残余项 R-5）。

---

## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）

| FreeArk 现有资产 | 本基座对应 | 复用方式 |
|------------------|-----------|----------|
| `langgraph_chat/experts.py`（`ExpertSpec` frozen dataclass + 派生访问器） | MOD-IB-16 | **模式直接沿用**（framework-free 单一真源） |
| `langgraph_chat/orchestrator.py`（StateGraph / `_fan_out` / `_aggregate` / 步数上限） | MOD-IB-22 | **模式沿用**；聚合的「禁止暴露内部分工」提示与后处理一并保留 |
| `langgraph_chat/router.py`（`build_capability_digest` 纯函数、`classify_experts()` 降级优先级、`_guard_against_misroute`） | MOD-IB-17 / MOD-IB-19 | **模式沿用**；业务专家替换为通用基线专家 |
| `langgraph_chat/semantic_router.py`（`score_experts`/`decide` 纯函数 + τ/margin） | MOD-IB-18 | **模式沿用** |
| `langgraph_chat/adapter.py`（`_drive` 流式策略、`resume_chat`） | MOD-IB-21 / MOD-IB-22 | 语义沿用；通道由 WebSocket 改为 **Django 原生 SSE（`StreamingHttpResponse`，ADR-11-R1，不引入 Channels/Redis）**；`reasoning_content` 丢失问题须在 MOD-IB-20 内解决。**吸取 FreeArk 两处教训**：① WS token 曾以 `?token=` 承载并被 access log 完整打印 → 本基座 SSE **只允许 `Authorization` 头鉴权**；② `channels_redis` 4.3.0 × `redis-py` 8.0.0 不兼容 → 本基座不经 Redis，若未来升级路径引入 Redis，须 pin `redis-py` 5.x 并以真 Redis 验证 |
| `rag_service.py` 的 `ParsedChunk` / `RagParser` 三路径 / `_split_text` 滑窗 | MOD-IB-05 / MOD-IB-07 | **语义沿用，实现须重写**（PDF 库由 PyMuPDF 换为宽松许可组合，ADR-06） |
| `rag_service.py` 的 `_get_ocr_engine` 懒加载单例 / `_detect_image_format` 魔数探测 | MOD-IB-06 / MOD-IB-13 | **模式沿用**（探测逻辑升级为端口 + 显式降级） |
| `rag_service.py` 的 `RagIngestor.ingest()` / `BATCH_SIZE` / 并发删除检查 | MOD-IB-13 | **语义沿用**；执行载体由 daemon 线程改为 `ib-worker` + 租约（ADR-10） |
| `views_rag.py` 的 `_validate_upload_file`（扩展名 → 大小 → 头部魔数） | MOD-IB-13（IFC-IB-141） | **模式直接沿用** |
| `rag_service.py` 的 `search_rag()`（`{"chunks": ..., "degraded": ...}` 永不抛出） | MOD-IB-15 | **语义沿用**，契约升级为类型化 `RetrievalResult`（ADR-13） |
| `RagVectorCache`（进程内 numpy 全量暴力余弦） | MOD-IB-10 | **替换**（Qdrant 原生 HNSW，DR-01） |
| `settings.py` 的 `RAG_*` 环境变量配置模式 | MOD-IB-02 | **模式沿用**（升级为全局 + 项目级两层） |
| PyMuPDF 依赖及其「内部平台合规」注释 | MOD-IB-05 | **替换并撤除该口径**（ADR-06，REQ-NFR-IB-12 禁止） |

---

## 11. 自检声明

- **门控标准 1（REQ → MOD 全覆盖）**：§9.1 逐条列出 24 条 REQ-FUNC，**每条均有主模块**，无缺口；§9.2 覆盖 14 条 REQ-NFR。
- **门控标准 2（无循环依赖）**：§4.2 给出**构造性无环证明**（依赖边权值严格递减 ⇒ 无环），并列出三处「看似会成环」的化解方式。
- **门控标准 3（ADR ≥2 方案）**：13 条 ADR 见 `architecture_design.md` §2，每条含 ≥2 候选方案（含已评估未采纳项）、选择理由与负向后果。
- **门控标准 4（接口全部类型化）**：§2.1 给出全部数据结构的**字段名 + 类型 + 可空性**；§3 给出全部公开接口的类型化签名（含参数类型与返回类型）；§2.2 汇总端口与 IFC 段。
- **边界合规**：本文**不含实现代码**（无函数体、无伪代码实现）；**未修改 FreeArk 任何文件**；**未写入任何凭据/密钥/令牌**；本阶段**止于 GROUP_B**。
- **R1 自检（框架切换）**：
  - **载体替换、契约未变**：§2.1.1 逐条给出 FastAPI→Django 载体等价映射（7 行）；25 模块 / 13 端口 / 58 条 IFC-IB 编号 / DAG 拓扑序 / 需求覆盖率**全部保持不变**（§4.2.1、§9.3 再声明）。
  - **类型化未降级**：领域契约仍由 MOD-IB-01 的 frozen dataclass 承载（framework-free）；DRF `Serializer` 仅承担 HTTP 层输入校验/输出渲染，Pydantic 不再承载端口契约（ADR-13-R1）。
  - **流式结论**：MOD-IB-21 采用 Django 原生 SSE（`StreamingHttpResponse`），**不引入 Channels / Redis**；Option B（Django 异步视图 + Gunicorn UvicornWorker，不含 Channels）为保留升级路径，触发条件 `[TBD-T15]`。
  - **两处 FreeArk 教训已内化**：① 禁止 `?token=`（access log 泄露）→ 仅 `Authorization` 头；② `channels_redis` × `redis-py` 版本不兼容 → 本基座不经 Redis，升级路径引入时 pin `redis-py` 5.x 并真 Redis 验证。
  - **凭据纪律**：仍只记「凭据走环境变量」（IFC-IB-262/263），无任何真实值。
  - **R2 自检（L-03 补交）**：
    - **补交完整**：MOD-IB-26 具备模块归属（§1 / §3）、依赖边与无环论证（§4.1 / §4.2）、类型化契约（IFC-IB-266~274，正文单列文件）、装配与可逆开关（§5）、降级行（§7.4）、覆盖行（§9）。**「有单元文件与客户端、无模块归属」的状态已消除。**
    - **编号只增不改**：`IFC-IB-001~265` 的号/名/签名/字段集一字不动；新增 266~284 与 286，285 预留未分配；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。
    - **DAG 无环**：新增单边仅 `26 → {01,02,04}`，且 26 号无入边（不被 import）→ 权值严格递减性质保持（§4.2 R2 补句）。
    - **契约单一落点**：MOD-IB-26 正文以 `docs/ib_embed_service_contract.md` 为准，§3 为摘要视图，**全文无第二份口径**。
    - **边界合规**：R2 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；**未写入任何凭据或配置值**（只登记键名）；本阶段**止于 GROUP_B**。
