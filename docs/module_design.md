<file_header>
  <project>intelligentbase</project>
  <artifact>module_design</artifact>
  <path>docs/module_design.md</path>
  <doc_id>MOD-INTELBASE-001</doc_id>
  <version>1.4.0</version>
  <revision>R8</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04 模块详细设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-006</invocation_id>
  <created_at>2026-09-25</created_at>
  <revision_history>
    <rev no="R1" date="2026-09-25" by="system-architect" basis="REV-01（框架切换 FastAPI→Django）">
      Web 层载体由 FastAPI/Uvicorn/ASGI 切换为 Django + DRF + WSGI（Waitress 主 / Gunicorn 备）。仅替换「载体」，不改变任何领域契约：25 模块、13 端口、58 条 IFC-IB 编号、DAG 拓扑序与 REQ 覆盖率均保持不变。新增 §2.1.1 载体等价映射表、§4.2.1 无环性再声明、§9.3 覆盖率再声明；MOD-IB-21 增补 SSE 承载与鉴权纪律；MOD-IB-23 组合根返回类型与外部依赖替换。
    </rev>
  <rev no="R2" date="2026-09-26" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-004" basis="PM 补交要求（L-03：ib-embed 服务端无模块归属与完整契约）">
    新增 MOD-IB-26「ib-embed 服务端」（26 大于其全部依赖 {01,02,04}，编号即拓扑序仍成立，且本模块不被任何模块 import）。新增 IFC 编号：266~274（MOD-IB-26 线协议，正文以 docs/ib_embed_service_contract.md 为准）、275（MOD-IB-09 的 InProcessBgeM3Embedder 第三适配器）、276~284（M-02 页面图绑定：MOD-IB-01 数据结构 / MOD-IB-13 五条 / MOD-IB-21 related_images 载荷 / MOD-IB-23 图片端点 / MOD-IB-24 渲染约束）、286（MOD-IB-25 第二份 EnvironmentFile 模板）；IFC-IB-285 预留未分配。既有 MOD-IB-01~25、IFC-IB-001~265、端口名、DAG 拓扑与 REQ 覆盖率矩阵一字不动（纯追加）。增补位置：§1 总览行与计数、§2.1 三行数据结构、§2.2.1 R2 IFC 段号索引、§3 的 MOD-IB-09/13/21/23/24/25 增补与 MOD-IB-26 新小节（摘要视图）、§4.1 一条新依赖边、§4.2 R2 无环补句、§4.3 分层一行、§5 装配表 IB_EMBED_BACKEND 值域扩展、§7.4 两行降级、§9.1/§9.2 覆盖更新与 §9.4 再声明、§11 R2 自检。
  </rev>
    <rev no="R7" date="2026-09-27" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-005" basis="GROUP_A REV-06 下游贯通（诉求③「UI 可视化配置」纳入 v1：REQ-FUNC-IB-25 / IB-26 / IB-27）">
      **不新增模块、不新增依赖边**（REV-07-1）：定义文档数据层（装载 / 完备性校验 / 原子写回 / 装配期派生）并入 MOD-IB-02；契约与**第 14 个端口** `DefinitionDocumentStore` 并入 MOD-IB-01；可视化端点与装配期 fail-fast 准入闸门并入 MOD-IB-23；可视化视图（白名单表单 + 编排图只读渲染）并入 MOD-IB-24。新增 IFC 编号 287~297（11 条，全部类型化、frozen dataclass / Protocol、零第三方依赖）；IFC-IB-285 仍预留未分配。既有 MOD-IB-01~26、IFC-IB-001~286、13 个既有端口名、§4.1 依赖边清单、DAG 拓扑与既有 REQ 覆盖归属**一字不动**（纯追加；零新增边的再声明见 §4.2.2）。增补位置：§0 门控证据行与 §1 总览行（计数 24/24 → 27/27）、R7 性质段与 R7 补充纪律段、§2.1 四行数据结构与 R7 字段集说明、§2.2 端口行与 R7 增记、§2.2.2 R7 IFC 段号索引、§3 的 MOD-IB-01/02/16/22/23/24 增补、§4.2.2 R7 无环性再声明、§5 装配表行与 R7 说明、§7.4 两行降级、§8 替身行与离线可测单元、§9.1 三行覆盖与计数同步、§9.2 R7 说明、§9.5 R7 覆盖率再声明、§11 R7 自检。**REV-07-6 施工前置判定 = (a) 可登记前置条件 / 风险，本轮继续**（见 §9.5）。未修改 FreeArk 任何文件；需求侧文档只读；未写入任何凭据或配置值（只登记键名）。
    </rev>
    <rev no="R8" date="2026-09-27" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-006" basis="GROUP_A REV-11-1 下游贯通（REQ-FUNC-IB-20 补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）">
      **不新增模块、不新增端口、不新增依赖边**：会话状态 / 持久化策略 / 完成产物 / 确认中间态的类型化契约并入 **MOD-IB-01**；键名登记与值域显式化并入 **MOD-IB-02**；流式终态与可见性判据并入 **MOD-IB-21**；恢复判定与确认门装配语义并入 **MOD-IB-22**；会话恢复端点与 fail-closed 准入并入 **MOD-IB-23**；确认中间态的呈递与决策回传渲染约束并入 **MOD-IB-24**。新增 IFC 编号 **298~308**（11 条，全部类型化、frozen dataclass / Protocol、零第三方依赖）；**IFC-IB-285 仍预留未分配**。`IFC-IB-221/222` 的**签名文本不改**（仅补齐其悬置引用的 `SessionState` 定义）、`IFC-IB-233` 的 `payload: dict` **签名文本不改**（仅新增其载荷类型 `ResumePayload`）；`IB_SESSION_BACKEND` 键名与默认值不变（**仅扩展值域**，沿用 R2 先例）。既有 MOD-IB-01~26、`IFC-IB-001~297`、14 个端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（纯追加；零新增边的再声明见 §4.2.3）。增补位置：R8 性质段、§2.1 五组数据结构与 R8 说明、§2.2 R8 增记与 §2.2.3 R8 IFC 段号索引、§3 的 MOD-IB-01/02/21/22/23/24 增补、§4.2.3 R8 无环性再声明、§7.3 四条规范化补充、§7.4 两行降级、§8 R8 离线可测单元、§9.1 IB-20 行与 R8 覆盖闭环段、§9.6 R8 覆盖率再声明、§11 R8 自检。需求侧文档（v1.3.0）只读；未修改 FreeArk 任何文件；未写入任何凭据或配置值（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）。
    </rev>
  </revision_history>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.3.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.3.0" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.4.0" revision="R8" status="DRAFT_FOR_GATE_REVIEW"/>
    <readonly_reference path="FreeArk 仓库" note="只读参考；未修改任何文件"/>
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW" note="MOD-IB-26 契约唯一落点；本文件 §3 MOD-IB-26 为摘要视图，冲突时以其为准"/>
  </inputs>
  <scope_boundary>模块划分、类型化接口契约、依赖图、装配表、覆盖率矩阵、状态机与降级矩阵。**不含实现代码**（无函数体、无伪代码级实现）。</scope_boundary>
</file_header>

# 模块详细设计 — intelligentbase

**版本**: 1.4.0 (R8) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-27
**R7 性质**: 本修订为**追加式增量**（GROUP_A REV-06 裁决：诉求③「UI 可视化配置」纳入 v1，新增 REQ-FUNC-IB-25 / IB-26 / IB-27），**只追加、不改写**：**不新增模块、不新增依赖边**。定义文档的**数据层**（装载 `IFC-IB-288` / 完备性校验 `IFC-IB-290` / 原子写回 `IFC-IB-289` / 装配期派生 `IFC-IB-291` / 白名单 `IFC-IB-292` / 新增键名 `IFC-IB-297`）并入 **MOD-IB-02**；契约（端口 + 数据结构）并入 **MOD-IB-01**；可视化端点与**装配期准入闸门**（`IFC-IB-293~295`）并入 **MOD-IB-23**；可视化视图约束（`IFC-IB-296`）并入 **MOD-IB-24**。新增 `IFC-IB-287 ~ 297`（**IFC-IB-285 仍预留未分配**）。既有 MOD-IB-01~26、`IFC-IB-001~286`、13 个既有端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（零新增边的再声明见 §4.2.2）。**REV-07-6 施工前置判定 = (a) 可登记的前置条件 / 风险，本轮继续**（见 §9.5；另见 `architecture_design.md` [ARCH-ASSUMPTION-A7]）。

**R8 性质**: 本修订为**追加式增量**（GROUP_A REV-11-1：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的**设计覆盖闭环**），**只追加、不改写**：**不新增模块、不新增端口、不新增依赖边**。会话状态（`SessionState` / `SessionTurn`）、持久化策略枚举、完成产物（`CompletionPayload` / `CitationItem`）与确认中间态（`ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`）的类型化契约并入 **MOD-IB-01**（`IFC-IB-298~301`，其中 **IFC-IB-298 补齐 `IFC-IB-221/222` 的既有悬置引用，不改其签名文本**）；键名登记与值域显式化并入 **MOD-IB-02**（`IFC-IB-304`）；流式终态单发与可见性判据并入 **MOD-IB-21**（`IFC-IB-302/303`）；恢复判定与确认门装配语义并入 **MOD-IB-22**（`IFC-IB-305/306`，其中 **IFC-IB-305 类型化 `IFC-IB-233` 的 `payload: dict`，不改其签名文本**）；会话恢复端点与 fail-closed 准入并入 **MOD-IB-23**（`IFC-IB-307`）；确认中间态的呈递与决策回传渲染约束并入 **MOD-IB-24**（`IFC-IB-308`）。新增 `IFC-IB-298 ~ 308`（**IFC-IB-285 仍预留未分配**）。既有 MOD-IB-01~26、`IFC-IB-001~297`、14 个端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（零新增边的再声明见 §4.2.3）。**OQ-IB-07 / OQ-IB-08 保持开放**（架构默认取值见 `architecture_design.md` §10.1 R8 行与 ADR-17）。

**R2 性质**: 本修订为**补交式增量**（L-03：`ib-embed` 此前只有 systemd 单元与客户端、缺服务端模块归属与完整契约），**只追加、不改写**：新增 MOD-IB-26 与 IFC-IB-266~284 / 286（IFC-IB-285 预留）。既有 MOD-IB-01~25、IFC-IB-001~265、13 个端口名与 DAG 拓扑**一字不动**。MOD-IB-26 的契约**唯一落点**为 `docs/ib_embed_service_contract.md`，本文件 §3 为其**摘要视图**，二者冲突时以契约文件为准。
**配套**: 架构决策与背景见 `docs/architecture_design.md`；技术选型见 `docs/tech_stack.md`。
**R1 性质**: 本修订为**载体替换**（Web 框架 FastAPI→Django），**非契约变更**——模块划分、类型化接口、依赖图拓扑与需求覆盖率均不变，只在「谁承载这些契约」这一层做了等价映射（见 §2.1.1）。所有编号（MOD-IB-*、IFC-IB-*、端口名）保持稳定以便追溯。

**本文承担四项目门控标准的可验证证据**：① REQ→MOD 覆盖率矩阵（§9，**27/27 REQ-FUNC 全覆盖**；R7 同步计数，v1.2.0 需求总数）；② 依赖图 DAG 无环（§4，构造性证明）；③ 类型化接口契约（§2、§3）；④ 各 ADR 的候选方案已在架构文档中给出。

**契约记法**：`IFC-IB-NNN: name(param: Type, *, kw: Type) -> ReturnType | ErrorType`。`T | None` 表示可空；`scope` 无 `= 默认值` 即表示**必填**。

---

## 1. 模块总览

26 个模块（R2 新增 MOD-IB-26；**R7 未新增模块**——REV-07-1：可视化配置的落点并入既有模块，理由见下方 R7 补充纪律）。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4；R2 新增单边的权值校验见 §4.2；**R7 零新增依赖边的再声明见 §4.2.2**）。

**R2 补充纪律**：MOD-IB-26 是**唯一**「不被任何模块 import」的服务端模块（上层只经 `Embedder` 端口与线协议访问，与 MOD-IB-10 对 Qdrant 服务的形态同构），因此它**不引入任何入边**，也不可能出现在任何依赖环上。若将来有人 `import` 本模块，会**同时**破坏 DAG 纪律与「形态可逆」（进程内形态不得依赖服务端）。

**R7 补充纪律（编号即拓扑序的边界情形）**：REV-07 曾评估「新增 `MOD-IB-27` 承载定义文档数据层」，**予以否决**：定义文档数据层是 **L0 纯数据工件**，**必然被组合根 `MOD-IB-23` 依赖**；而新模块只能取 **≥27** 的编号，于是产生 `23 → 27` 的边，违反 `w(A) > w(B)`，**构造性无环证明失效**（§4.2）。替代方案（独立服务进程 + 线协议，形态对齐 MOD-IB-26）则**净增第 5 个 systemd 单元**与新故障域，与 C-IB-08（最小组成面）与 ADR-03（四单元结论）冲突。故按 REV-07-1 将落点**并入既有模块**。**该边界情形固化为纪律**：当新工件被**低编号模块（尤其组合根）依赖**时，**不得新开编号更高的模块**——只能并入既有模块，或先把契约下沉（与 §4.2「分层被破坏须先重构分层」同源）。

| MOD-ID | 模块名 | 层 | 职责（一句话） | 依赖于 |
|--------|--------|----|----------------|--------|
| MOD-IB-01 | 核心契约 | L0 | 定义全部端口 Protocol、枚举与不可变数据结构；零第三方依赖 | — |
| MOD-IB-02 | 配置 | L0 | 装载并校验 全局配置 / 项目级配置；注入凭据（仅环境变量）；**R7**：定义文档的装载 / 完备性校验 / 原子写回 / 装配期派生（IFC-IB-288~292、297） | 01 |
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
| MOD-IB-16 | 专家注册表 | L4 | **装配期派生注册表**（由定义文档在装配期构造并注入；R7 前表述为「唯一真源」——真源已上移至定义文档，见 ADR-15；仍为 frozen dataclass，framework-free 纯数据） | 01 |
| MOD-IB-17 | 工具注册与能力摘要 | L4 | 工具注册表 + 由注册表**派生**的能力摘要；scope 闭包绑定 | 01,15,16 |
| MOD-IB-18 | 语义路由 | L4 | 向量化样例打分 + 阈值/分差判定（纯函数，fail-open） | 01,09,16 |
| MOD-IB-19 | 意图路由内核 | L4 | 四级降级路由（关键词 → 语义 → LLM → 兜底）+ 粘性 + OOD + 守卫 | 01,16,17,18 |
| MOD-IB-20 | LLM 端点抽象 | L4 | provider 端口；路由/专家/聚合三角色的构造；外发边界声明 | 01,02,04 |
| MOD-IB-21 | 流式契约与会话 | L4 | 类型化流事件与 SSE 编码；`SessionStore` 端口 | 01,02,04 |
| MOD-IB-22 | 编排图 | L4 | StateGraph：route → fan-out → expert/general → gate → aggregate；**R7**：图编译输入 = 经准入闸门校验通过的定义文档，**拓扑不可编辑**（运行期不得由图外输入改变节点/边） | 01,02,03,04,16,17,18,19,20,21 |
| MOD-IB-23 | HTTP API 与组合根 | L5 | 唯一装配点；REST + SSE 端点；鉴权注入；健康检查；**R7**：装配期 **fail-fast 准入闸门**（拒绝装配而非带病运行）+ 定义文档的 GET / PUT 端点 | 01,02,03,04 + 全部装配目标 |
| MOD-IB-24 | Web 前端 | L5 | 上传/列表/删除/重试/重建页 + 问答页 + 类型化 API 客户端；**R7**：可视化配置页（编排图只读渲染 + 白名单表单；**视图侧零持久化**） | 23（仅 HTTP/SSE 契约） |
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
| `RelatedImageItem` / `RelatedImagesPayload`（R2 新增，定义于 MOD-IB-01） | `RelatedImageItem`: `image_id: str`；`doc_id: str`；`doc_name: str`；`page_or_section: str`；`url_path: str`。`RelatedImagesPayload`: `images: tuple[RelatedImageItem, ...]`
| `DefinitionDocument`（R7 新增，定义于 MOD-IB-01） | `schema_version: int`；`project_id: str`；`content_hash: str`；`experts: tuple[ExpertSpecInput, ...]`；`route: RouteSpecInput`；`orchestration: OrchestrationSpecInput`；`tool_grants: tuple[ToolGrantSpec, ...]`；`updated_at: str` |
| `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec`（R7 新增，定义于 MOD-IB-01） | `ExpertSpecInput`: `name: str`；`cn_label: str`；`keywords: tuple[str, ...]`；`exemplars: tuple[str, ...]`；`is_data_expert: bool`；`fallback_prompt: str`；`is_delegating: bool`；`is_default: bool`。`RouteSpecInput`: `tau: float`；`margin: float`；`max_expert_steps: int`；`default_expert: str`。`ToolGrantSpec`: `expert_name: str`；`tool_names: tuple[str, ...]` |
| `OrchestrationSpecInput` / `ConditionalEdgeSpec`（R7 新增，定义于 MOD-IB-01） | `OrchestrationSpecInput`: `nodes: tuple[str, ...]`；`conditional_edges: tuple[ConditionalEdgeSpec, ...]`。`ConditionalEdgeSpec`: `from_node: str`；`branch_map: tuple[tuple[str, str], ...]`（元素为 `(branch_key: str, target_node: str)` 的有序对；**缺失或为空即非法** —— 界面无法判定可达性，由 IFC-IB-290 拒绝） |
| `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult`（R7 新增，定义于 MOD-IB-01） | `DerivedView`: `experts: tuple[ExpertSpecInput, ...]`；`capability_digest: str`；`graph_config: OrchestrationSpecInput`。`ValidationErrorItem`: `path: str`；`code: str`；`message: str`（**不回显任何凭据值**）。`ValidationReport`: `ok: bool`；`errors: tuple[ValidationErrorItem, ...]`（**无 `force` / `ignore` / `warn_only` 字段**）。`SaveResult`: `ok: bool`；`content_hash: str`；`conflict: bool`；`errors: tuple[ValidationErrorItem, ...]` | |
| `SessionState` / `SessionTurn`（R8 新增，定义于 MOD-IB-01；**补齐** `IFC-IB-221/222` 的既有悬置引用） | `SessionState`: `session_key: str`；`project_id: str`；`actor_id: str`；`turns: tuple[SessionTurn, ...]`；`gate: ConfirmationGateState 或 None`；`updated_at: str`。`SessionTurn`: `role: Literal["user","assistant"]`；`text: str`；`citations: tuple[CitationItem, ...]`；`created_at: str` |
| `SessionPersistencePolicy` / `SessionStateLossOutcome`（R8 新增，定义于 MOD-IB-01） | `SessionPersistencePolicy` = `Literal["in_process","external"]`（默认 `in_process`，**须显式声明**）。`SessionStateLossOutcome` = `Literal["fail_closed_restart_required"]`（**唯一取值**：状态丢失时只允许安全失败） |
| `CompletionPayload` / `CitationItem`（R8 新增，定义于 MOD-IB-01） | `CompletionPayload`: `citations: tuple[CitationItem, ...]`（**可为空元组**，无引用即空、不臆造）；`had_content: bool`（空内容边界）。`CitationItem`: `doc_id: str`；`doc_name: str`；`page_or_section: str`；`locator: str`；`score: float`（**均为定位信息；不内联字节、不含正文全文**） |
| `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`（R8 新增，定义于 MOD-IB-01） | `ConfirmationPrompt`: `gate_id: str`；`expert_name: str`；`summary: str`（**由接入方构造**，骨架不生成业务话术）。`ConfirmationDecision`: `gate_id: str`；`approved: bool`。`ConfirmationGateState`: `gate_id: str`；`prompt: ConfirmationPrompt`；`decision: ConfirmationDecision 或 None`（`None` = 待决策） |
| `StreamEventKind` **值域追加成员**（R8，定义于 MOD-IB-01） | 既有 6 个成员（`reasoning` / `content` / `degraded` / `related_images` / `error` / `done`）**一字不动**；**追加** `confirmation_required`（确认中间态的呈递事件；**仅在 `IB_CONFIRMATION_GATE_ENABLED=true` 时出现**） |

**R2 说明（字段集不变式）**：以上三行为**追加**，既有两个结构（`ParsedChunk` / `RetrievedChunk`）的字段集**不变**——页面图的图文关联经**独立结构 + 独立关联表**承载，不改 `IFC-IB-009` / `IFC-IB-007` 的既有字段（编号只增不改）。
**R7 说明（字段集不变式续）**：以上四行为**追加**，R1 / R2 既有结构（`ParsedChunk` / `RetrievedChunk` 与 R2 三行）的字段集**均不变**。`ValidationReport` 的字段集是**刻意**的：除 `ok` / `errors` 外**不存在** `force` / `ignore` / `warn_only`，使 REQ-FUNC-IB-27「**不提供**强制继续 / 忽略错误开关」成为**类型层事实**而非纪律约定（ADR-16）。`DerivedView` 为**只读派生结果**：不落盘、不可反写文档；`ValidationErrorItem` 只出 `path` / `code` / `message`，**不回显任何凭据值**（AC-IB-18-04）。全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5）。

**R8 说明（字段集不变式续）**：以上**五组为追加**，R1 / R2 / R7 既有结构（`ParsedChunk` / `RetrievedChunk` 与 R2 三行、R7 四行）的字段**均不变**。`SessionState` 是**既有悬置引用的补齐**：`IFC-IB-221/222` 早已引用该类型但 §2.1 **从未定义**，本轮补齐其字段级定义，**`IFC-IB-221/222` 的签名文本一字不改**。`SessionStateLossOutcome` 的**唯一取值** `fail_closed_restart_required` 使「重启丢弃待确认状态 = **安全失败**」成为**类型层事实**而非纪律约定（AC-IB-20-05）；`CompletionPayload.citations` **可为空元组**使「无引用即空、不臆造」成为结构事实（AC-IB-19-05）。全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5 延续）。

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
| `DefinitionDocumentStore`（**R7 新增**） | 5 | IFC-IB-287（端口）+ IFC-IB-288~292（方法） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-02（装载·校验·写回·派生·白名单） |

`CollectionResolver` 归入 MOD-IB-09 所在层（L2，无外部依赖，仅依赖 MOD-IB-01/02）：它是**唯一**把 `Scope` 映射为 collection 名的地方（ADR-04 可升级性设计），因此必须由所有需要 collection 名的上层模块共用，而非各自拼接字符串。

**R7 增记（第 14 个端口）**：`DefinitionDocumentStore`（IFC-IB-287）为**第 14 个端口**（13 → 14，**纯追加**）。它与 `ConfigurationSource` 的区别是**工件不同**：后者装载进程级配置（凭据只登记键名），前者装载**项目级定义文档**（专家 / 路由 / 编排 / 工具授权）并保证 round-trip 一致性（乐观并发 + 原子写）。所有需要「按项目取定义文档 / 派生结果」的上层模块（MOD-IB-16 / 17 / 19 / 22）**不得**各自读文件或各自解析，一律由组合根在**装配期**经该端口取得派生物后构造注入（同 `CollectionResolver` 的「唯一入口」精神；ADR-15）。

**R8 增记（不新增端口；类型化既有载荷）**：端口数仍为 **14**（`SessionStore` 仍为 **3 方法** `IFC-IB-221~223`，**方法数与签名一字不改**）。R8 的两处「类型化既有载荷」遵循 **IFC-IB-282 先例**（只定义载荷类型、不改父签名）：① **IFC-IB-298** 补齐 `IFC-IB-221/222` 悬置引用的 `SessionState` 定义；② **IFC-IB-305** 类型化 `IFC-IB-233` 的 `payload: dict`（改为语义等价的类型化载荷），**`IFC-IB-233` 的签名文本与参数个数不变**。另：装配表键 `IB_SESSION_BACKEND` 的**值域**由 `memory` 扩展为 `memory 或 external`，**键名与默认值（`memory`）不变** —— 沿用 R2 对 `IB_EMBED_BACKEND` 的「**仅扩展值域；键名与默认值不变**」先例（§5）。

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

### 2.2.2 R7 新增 IFC 段号索引（追加式编号；IFC-IB-001~286 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-287 | MOD-IB-01 | 端口 `DefinitionDocumentStore`（Protocol，5 方法）+ `DefinitionDocument` / `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec` / `OrchestrationSpecInput` / `ConditionalEdgeSpec` / `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult` 的字段级定义 | §2.1、§3 MOD-IB-01（本文件） |
| IFC-IB-288 | MOD-IB-02 | `load(project_id: str) -> DefinitionDocument \| ConfigError`（文档缺失或不可解析均为可读错误，**不静默回退为空文档**） | §3 MOD-IB-02 |
| IFC-IB-289 | MOD-IB-02 | `save(project_id: str, doc: DefinitionDocument, *, expected_content_hash: str \| None) -> SaveResult`（**先写临时文件、再原子替换**；`expected_content_hash` 不匹配即返回 `conflict=True` 并**拒绝覆盖**） | §3 MOD-IB-02 |
| IFC-IB-290 | MOD-IB-02 | `validate(doc: DefinitionDocument) -> ValidationReport`（**纯函数**，framework-free；≥7 类校验项；**不含强制继续开关**） | §3 MOD-IB-02 |
| IFC-IB-291 | MOD-IB-02 | `derive(doc: DefinitionDocument) -> DerivedView`（**纯函数**；注册表 / 阈值 / 图配置的装配期派生；**不落盘、不可反写**） | §3 MOD-IB-02 |
| IFC-IB-292 | MOD-IB-02 | `editable_field_whitelist() -> frozenset[str]`（可视化可编辑字段白名单；须与 IFC-IB-290 的校验项**成对维护**） | §3 MOD-IB-02 |
| IFC-IB-293 | MOD-IB-23 | 装配期**准入闸门**：`admit(doc: DefinitionDocument) -> DerivedView`（内部调用 IFC-IB-290；不通过即**拒绝装配**，抛出聚合全部 `ValidationErrorItem` 的 `ConfigError`） | §3 MOD-IB-23 |
| IFC-IB-294 | MOD-IB-23 | `GET /api/config/definition` → `200 DefinitionDocument`（+ 派生视图摘要）\| `403`（归属断言失败）\| `503`（**fail-closed**：读不到文档即明确报错，**不返回空文档**） | §3 MOD-IB-23 |
| IFC-IB-295 | MOD-IB-23 | `PUT /api/config/definition` → `200 SaveResult` \| `400`（校验不通过：逐条 `path` / `code` / `message`）\| `403` \| `409`（乐观并发冲突，**含可读冲突回执**）\| `503`（**fail-closed**） | §3 MOD-IB-23 |
| IFC-IB-296 | MOD-IB-24 | 可视化配置页的**渲染与编辑约束**（编排图只读渲染 + 白名单表单 + 未提交草稿显式标注 + 凭据不回显） | §3 MOD-IB-24 |
| IFC-IB-297 | MOD-IB-02 | 新增环境变量**键名**（**仅登记键名，不含任何值**）：`IB_DEFINITION_DOC_PATH`、`IB_VISUAL_CONFIG_ENABLED`（见 `tech_stack.md` §1.2） | §3 MOD-IB-02 |

**R7 编号规范（强制，延续 R2）**：新增号只许**追加**；`IFC-IB-001 ~ 286` 的号、名、签名、字段集**一字不动**；**`IFC-IB-285` 仍预留未分配**（不得被本轮占用或改义）；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。

### 2.2.3 R8 新增 IFC 段号索引（追加式编号；IFC-IB-001~297 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-298 | MOD-IB-01 | `SessionState` / `SessionTurn` 字段级定义（**补齐** `IFC-IB-221/222` 的悬置引用；不改其签名） | §3 MOD-IB-01 |
| IFC-IB-299 | MOD-IB-01 | 枚举 `SessionPersistencePolicy`（`in_process` / `external`）与 `SessionStateLossOutcome`（唯一取值 `fail_closed_restart_required`） | §3 MOD-IB-01 |
| IFC-IB-300 | MOD-IB-01 | `CompletionPayload` / `CitationItem`（完成事件结构化产物；`citations` 可空、`had_content` 标空内容边界） | §3 MOD-IB-01 |
| IFC-IB-301 | MOD-IB-01 | `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`；`StreamEventKind` **追加**成员 `confirmation_required` | §3 MOD-IB-01 |
| IFC-IB-302 | MOD-IB-21 | `completion_event(payload: CompletionPayload 或 None) -> StreamEvent`（终态恰一次单发；其后无 `content`；不臆造） | §3 MOD-IB-21 |
| IFC-IB-303 | MOD-IB-21 | `is_user_visible(kind: StreamEventKind) -> bool`（纯函数；`reasoning` 默认不可见；内部产物永不映射为可见 `kind`） | §3 MOD-IB-21 |
| IFC-IB-304 | MOD-IB-02 | 配置**键名登记与值域显式化**（**仅键名，不含值**）：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`；`IB_SESSION_BACKEND` 值域扩展 | §3 MOD-IB-02 |
| IFC-IB-305 | MOD-IB-22 | `ResumePayload`（`session_key: str`；`decision: ConfirmationDecision 或 None`）—— **类型化** `IFC-IB-233` 的 `payload: dict`，**不改其签名文本** | §3 MOD-IB-22 |
| IFC-IB-306 | MOD-IB-22 | `can_resume(state: SessionState 或 None, gate_id: str, payload: ResumePayload) -> bool`（纯函数；状态丢失 / 未携决策 / 归属不符 → `False` = fail-closed） | §3 MOD-IB-22 |
| IFC-IB-307 | MOD-IB-23 | `POST /api/chat/resume`（SSE，`Authorization` 头）→ 续跑流 或 `403` 或 `404`/`409`（fail-closed）或 `503` | §3 MOD-IB-23 |
| IFC-IB-308 | MOD-IB-24 | 前端对 `confirmation_required` 的**呈递与决策回传**约束（与答复片段可区分；未决策不继续） | §3 MOD-IB-24 |

**R8 编号规范（强制，延续 R2 / R7）**：新增号只许**追加**（本轮取 **298 ~ 308**）；`IFC-IB-001 ~ 297` 的号、名、签名、字段集**一字不动**；**`IFC-IB-285` 仍预留未分配**（不得被本轮占用或改义）；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。

---

## 3. 模块详情

> 每个模块含：职责 / 覆盖需求 / 公开接口契约（类型化）/ 依赖模块 / 外部依赖。

### MOD-IB-01 核心契约 (L0)

- **职责**: 定义全部端口 Protocol、枚举与不可变数据结构；**不 import 任何第三方框架**（仅 stdlib）。
- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）；**REQ-FUNC-IB-25 / IB-26 / IB-27（R7，辅：只承载新增契约与第 14 个端口，见 IFC-IB-287）**；**REQ-FUNC-IB-20（R8，辅：会话状态 / 持久化策略 / 完成产物 / 确认中间态的类型化契约落点，见 IFC-IB-298~301）**
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
  - **IFC-IB-287（R7 新增）**: 端口 `DefinitionDocumentStore`（`Protocol`，5 方法：`load` / `save` / `validate` / `derive` / `editable_field_whitelist`）+ 数据结构 `DefinitionDocument` / `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec` / `OrchestrationSpecInput` / `ConditionalEdgeSpec` / `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult`（字段级定义见 §2.1 末四行）。**类型化**（`name: type` + 可空性）；**frozen dataclass / Protocol，纯 stdlib、零第三方依赖**；**无实现体**。
  - **IFC-IB-298（R8 新增）**: 数据结构 `SessionState` / `SessionTurn`（字段级定义见 §2.1 R8 行）。**用途**：补齐 `IFC-IB-221/222` 的既有悬置引用（`SessionStore.load/save` 的 `SessionState`），**不改 `IFC-IB-221/222` 的签名文本**；**frozen dataclass、纯 stdlib、无实现体**。
  - **IFC-IB-299（R8 新增）**: 枚举 `SessionPersistencePolicy` = `Literal["in_process","external"]`（默认 `in_process`，**须显式声明**）；`SessionStateLossOutcome` = `Literal["fail_closed_restart_required"]`（**唯一取值**，使「状态丢失 = 安全失败」成为类型层事实，AC-IB-20-05）。
  - **IFC-IB-300（R8 新增）**: 数据结构 `CompletionPayload`（`citations: tuple[CitationItem, ...]` **可为空元组**；`had_content: bool`）与 `CitationItem`（`doc_id` / `doc_name` / `page_or_section` / `locator` / `score`，**均为定位信息，不内联字节、不含正文全文**）。供 `IFC-IB-302` 的单发完成事件使用（AC-IB-19-02 / 19-05）。
  - **IFC-IB-301（R8 新增）**: 数据结构 `ConfirmationPrompt`（`gate_id` / `expert_name` / `summary: str` **由接入方构造**）/ `ConfirmationDecision`（`gate_id` / `approved: bool`）/ `ConfirmationGateState`（`gate_id` / `prompt` / `decision: ConfirmationDecision 或 None`）；`StreamEventKind` **值域追加**成员 `confirmation_required`（**既有 6 个成员一字不动**）。**骨架只承载通道，不判定业务语义、不生成确认话术**（ADR-09 / ADR-17）。
- **依赖模块**: 无
- **外部依赖**: 无

### MOD-IB-02 配置 (L0)

- **职责**: 装载全局配置与**项目级**配置；凭据仅从环境变量读取；启动期校验必填项并给出可读错误；**R7 追加**：装载**定义文档**（项目级）、完备性校验、原子写回与**装配期派生**（framework-free 纯数据层，见 IFC-IB-288~292、IFC-IB-297）。
- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）、**IB-25 / IB-26 / IB-27（R7 新增：定义文档的装载 / 白名单 / 完备性校验与派生）**、**IB-20（R8 辅：会话持久化策略与确认门开关的键名登记与值域显式化，见 IFC-IB-304）**；REQ-NFR-IB-02、IB-07
- **公开接口契约**:
  - IFC-IB-021: `ConfigurationSource.load() -> RawConfig`（文件 + 环境变量合并）
  - IFC-IB-022: `resolve_project_config(project_id: str) -> ProjectConfig | ConfigError`
  - IFC-IB-023: `validate_required(cfg) -> list[ConfigError]`（**只报键名，不回显值**）
  - IFC-IB-024: `GlobalConfig`（含 `EmbeddingConfig` / `VectorStoreConfig` / `RetrievalConfig` / `ChunkingConfig` / `LlmConfig` / `AuthzConfig` / `LoggingConfig` / `BlobConfig` / `WorkerConfig`）
  - **IFC-IB-288（R7 新增）**: `load(project_id: str) -> DefinitionDocument | ConfigError`（文档缺失 / 不可解析均为可读错误；**不静默回退为空文档**）
  - **IFC-IB-289（R7 新增）**: `save(project_id: str, doc: DefinitionDocument, *, expected_content_hash: str | None) -> SaveResult`（**先写临时文件、再原子替换**；`expected_content_hash` 不匹配 → `conflict=True`，**拒绝覆盖**）
  - **IFC-IB-290（R7 新增）**: `validate(doc: DefinitionDocument) -> ValidationReport`（**纯函数**，framework-free；**≥7 类**校验项；`ValidationReport` **不含** `force` / `ignore` / `warn_only`）
  - **IFC-IB-291（R7 新增）**: `derive(doc: DefinitionDocument) -> DerivedView`（**纯函数**；注册表 / 路由阈值 / 图配置的装配期派生；**不落盘、不可反写文档**）
  - **IFC-IB-292（R7 新增）**: `editable_field_whitelist() -> frozenset[str]`（可视化可编辑字段白名单；须与 IFC-IB-290 的校验项**成对维护**）
  - **IFC-IB-297（R7 新增）**: 新增配置**键名**（**仅登记键名，不含值**）：`IB_DEFINITION_DOC_PATH`（定义文档路径）、`IB_VISUAL_CONFIG_ENABLED`（可视化配置页开关）
  - **IFC-IB-304（R8 新增）**: 配置**键名登记与值域显式化**（**仅登记键名，不含任何值**）：
    - `IB_CONFIRMATION_GATE_ENABLED`：确认中间态开关，**默认 `false`**（默认不启用即零行为差异；**OQ-IB-07 保持开放**）。
    - `IB_SESSION_PERSISTENCE_POLICY`：会话持久化策略，取值 `in_process`（默认）或 `external`；**须显式声明**（未声明即启动期报错，AC-IB-20-02）；v1 不提供 `external` 适配器（[ARCH-ASSUMPTION-A8]）。
    - `IB_REASONING_STREAM_ENABLED`：思考分区流式开关，**默认 `false`**（AC-IB-19-03）。
    - `IB_SESSION_BACKEND`：**值域扩展**为 `memory`（默认）或 `external`；**键名与默认值不变**（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域」先例）。
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

- **职责**: 专家规格的**装配期派生注册表**（frozen dataclass + 纯 stdlib）；**R7 措辞修正**：真源已上移至**定义文档**（ADR-15），本模块持有的是**由定义文档在装配期派生并注入**的只读注册表（同 MOD-IB-17 的「纯函数派生」模式）；其余模块的专家相关数据一律由此派生。
- **覆盖需求**: REQ-FUNC-IB-02（专家可配置）、**IB-25 / IB-26 / IB-27（R7：定义文档为该注册表的构造输入与唯一真源，见 ADR-15）**；REQ-NFR-IB-01（可复用）
- **R7 依赖不变声明**: 本模块的**依赖模块仍为 MOD-IB-01**（**零新增边**），对外契约 `IFC-IB-171~179` 的号 / 名 / 签名**一字不动**；R7 只改变**数据来源**（定义文档 → 装配期派生 → 构造注入），不改变模块边界与接口。派生的具体构造由 MOD-IB-02 的 `derive`（IFC-IB-291）完成、由组合根 MOD-IB-23 在装配期注入（见 §5 R7 说明）。
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
- **覆盖需求**: REQ-FUNC-IB-20、IB-21；AC-IB-14-01（降级事件可见）；**US-IB-19（流式交付最终答复；AC-IB-19-01 ~ 05）、US-IB-20（会话生命周期；AC-IB-20-01 ~ 03）（R8 补登记）**
- **R1 承载声明（ADR-11-R1）**: 事件流由 **Django `StreamingHttpResponse`** 以原生 SSE（`Content-Type: text/event-stream`）承载，运行于同步 WSGI（Waitress 主 / Gunicorn 备）；**不引入 Channels、不引入 Redis**。本模块只负责「事件 → 帧」编码（IFC-IB-224/225），与具体 Web 载体解耦，故框架切换对其**零改动**。
- **R1 鉴权纪律（强制）**: SSE 端点的身份令牌**只允许**经 `Authorization` 请求头（或请求体）注入，**禁止** `?token=` 查询串承载（FreeArk 教训：access log 会完整打印含 token 的 URL，导致令牌泄露）。该纪律落到 §3 MOD-IB-23 IFC-IB-247 与部署检查清单（IFC-IB-264）。
- **公开接口契约**:
  - IFC-IB-221: `SessionStore.load(session_key: str) -> SessionState | None`
  - IFC-IB-222: `SessionStore.save(session_key: str, state: SessionState) -> None`
  - IFC-IB-223: `SessionStore.delete(session_key: str) -> None`
  - IFC-IB-224: `StreamEvent(kind: StreamEventKind, data: str)`（`kind ∈ {reasoning, content, degraded, related_images, error, done}`）
  - IFC-IB-225: `to_sse(event: StreamEvent) -> str`（`event:` / `data:` 帧编码）
  - IFC-IB-282（R2）: `related_images` 事件的**载荷类型化** = `RelatedImagesPayload`（§2.1）。`data` 为该结构的 JSON 编码；**只传 `image_id` 与 `url_path`（站内相对路径），绝不内联图片字节或 base64** —— 帧体积有界，不阻塞流。事件在 `content` 之后、`done` 之前发出；**无图时不发该事件**（而非发空载荷）。`StreamEventKind` 的取值集合**不变**（`related_images` 早已在 IFC-IB-224 中枚举，R2 只定义其 data）。
  - **IFC-IB-302（R8 新增）**: `completion_event(payload: CompletionPayload 或 None) -> StreamEvent`（**纯函数**：构造**唯一**的终态事件；`kind=done`；**恰一次单发**，其后**不再有**该次交互的任何 `content` 片段，AC-IB-19-01；`payload` 缺省时**不臆造**引用，AC-IB-19-05；**不发空的 `content` 帧**；`payload` 定义见 IFC-IB-300）。
  - **IFC-IB-303（R8 新增）**: `is_user_visible(kind: StreamEventKind) -> bool`（**纯函数**：`content` / `degraded` / `related_images` / `error` / `done` → `True`；`reasoning` **默认不可见**（受 `IB_REASONING_STREAM_ENABLED` 门控）；**内部子任务产物永不属于任何 `StreamEventKind` 可见取值**，故**永不外流**，AC-IB-19-04；**默认不混帧** —— 同一事件不承载两个分区的语义）。
- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04
- **外部依赖**: 无

### MOD-IB-22 编排图 (L4)

- **职责**: StateGraph（route → 条件边 fan-out → expert×N / general → gate → aggregate → END）；并行扇出、聚合、流式透传。
- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06；**US-IB-20（会话生命周期；AC-IB-20-03 / 20-04 / 20-05）、US-IB-19（AC-IB-19-04）（R8 补登记）**
- **R7 图编译约束（新增）**: 图的编译输入 = **经准入闸门校验通过的定义文档**派生的 `OrchestrationSpecInput`（IFC-IB-291 → IFC-IB-293）；图**编译一次、进程常驻**，**运行期不得由任何图外输入改变拓扑** —— 节点 / 边集合与条件边**存在性**不是可编辑对象（REQ-FUNC-IB-26 ②）。拓扑变更的唯一路径 = 改定义文档 → 装配期校验 → 重新编译（AC-IB-18-01）。条件边**必须**带 `branch_map`，否则由 IFC-IB-290 拒绝（界面无法判定可达性）。`IFC-IB-231` 的签名**不变**（新增的图配置仍经 `GraphConfig` 参数注入，**不新增参数**）；`IFC-IB-232/233` 与 State 键（含 `MAX_EXPERT_STEPS = 8`）**不变**。
- **公开接口契约**:
  - IFC-IB-231: `build_graph(*, llm: LlmProvider, experts: ExpertRegistry, tools: list[BoundTool], sessions: SessionStore, config: GraphConfig) -> CompiledGraph`（**业务零依赖**：人格/身份文本、scope 一律由调用方已在参数中构造完成）
  - IFC-IB-232: `run(query: str, *, ctx: RequestContext, session_key: str) -> AsyncIterator[StreamEvent]`
  - IFC-IB-233: `resume(session_key: str, payload: dict) -> AsyncIterator[StreamEvent]`
  - State 键（含 reducer）: `messages: Annotated[list[Message], operator.add]`；`expert_results: Annotated[list[ExpertResult], operator.add]`；`plan: list[tuple[str, str]]`；`route_tier: RouteTier`；`query: str`；`degraded: bool`；`step_count: int`（上限 `MAX_EXPERT_STEPS = 8`）
  - **IFC-IB-305（R8 新增）**: `ResumePayload`（`session_key: str`；`decision: ConfirmationDecision 或 None`）—— **类型化** `IFC-IB-233` 的既有 `payload: dict`（**不改 `IFC-IB-233` 的签名文本与参数个数**；沿用 IFC-IB-282 先例）。`decision is None` = 未携带决策。
  - **IFC-IB-306（R8 新增）**: `can_resume(state: SessionState 或 None, gate_id: str, payload: ResumePayload) -> bool`（**纯函数**，无 IO：`state is None`（状态丢失）/ `state.gate` 为 `None` 或 `gate_id` 不符 / `payload.decision is None`（未携决策）→ **一律 `False`** = **fail-closed**；**仅当三门全过才 `True`**。AC-IB-20-04 / 20-05；配合 `SessionStateLossOutcome` 的唯一取值，使「安全失败」成为类型层事实）。
  - **确认门装配语义（R8，ADR-17）**: `IB_CONFIRMATION_GATE_ENABLED` **默认 `false`**；为 `false` 时 `gate` 节点**直接通过**（零行为差异：不写 `gate` 状态、不发 `confirmation_required`、`resume` 不可用）。为 `true` 时：`gate` 节点构造 `ConfirmationGateState`（`prompt.summary` **由接入方提供的业务构造器产出**，**骨架不生成业务话术**）并发出**一个** `confirmation_required` 事件后**挂起该会话**（保持中间态）；决策经 `POST /api/chat/resume`（IFC-IB-307）回传后经 `can_resume` 判定并续跑。**骨架不判定「哪些动作需要确认」**（ADR-09 / ADR-17 约束 2）。
- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-16、IB-17、IB-18、IB-19、IB-20、IB-21
- **外部依赖**: `langgraph`

### MOD-IB-23 HTTP API 与组合根 (L5)

- **职责**: **唯一装配点**；REST + SSE 端点；鉴权注入与 `project_id` 解析（不信请求体）；健康检查。
- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23、**IB-25 / IB-27（R7 新增：定义文档的读写端点与装配期准入闸门）**、**IB-20（R8 新增：会话恢复端点与 fail-closed 准入；US-IB-20 / AC-IB-20-04 ~ 20-06）**；REQ-NFR-IB-09
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
- **R7 新增契约与装配序列（可视化配置增量）**:
  - **IFC-IB-293**: 装配期**准入闸门** `admit(doc: DefinitionDocument) -> DerivedView`（内部调用 IFC-IB-290；不通过即**拒绝装配**，抛出聚合**全部** `ValidationErrorItem` 的 `ConfigError`）。
  - **IFC-IB-294**: `GET /api/config/definition` → `200 DefinitionDocument`（+ 派生视图摘要）| `403`（归属断言失败）| `503`（**fail-closed**：读不到文档即明确报错，**不返回空文档**）。
  - **IFC-IB-295**: `PUT /api/config/definition` → `200 SaveResult` | `400`（校验不通过：逐条 `path` / `code` / `message`）| `403` | `409`（乐观并发冲突，含可读冲突回执，**不静默覆盖**）| `503`（**fail-closed**）。
  - **R7 装配序列（显式化，任一步失败即启动失败）**: `装载定义文档（IFC-IB-288）→ 准入闸门（IFC-IB-293，内含 IFC-IB-290）→ 派生注册表 / 图配置（IFC-IB-291）→ 构造并注入（MOD-IB-16 / 17 / 19 / 22）→ 图编译一次常驻`。闸门位于**序列第一步**（ADR-16）。
  - **鉴权与凭据纪律（强制，扩展到全部新端点）**: 沿用 IFC-IB-247 口径，**仅允许 `Authorization` 头 / 中间件鉴权**；两个新端点**不接受** `?token=`；错误体**不回显任何凭据值**（AC-IB-18-04）；归属断言失败一律 `403`（**不因「是不是你的配置」而区分 `404`** —— 定义文档按 `project_id` 归属，同 §1.4 第 2 条精神）。
  - **R7 配置键不变声明**: 除 IFC-IB-297 新增的两个键名（`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）外，§5 装配表的**既有开关名与默认值一字不动**；**新增键名不含任何值**。
  - **R8 新增端点（会话恢复；IFC-IB-307）**: `POST /api/chat/resume`（**SSE**，`Content-Type: text/event-stream`；**仅允许 `Authorization` 头**鉴权，**不接受 `?token=`**）→ 续跑流（`text/event-stream`）| `403`（归属断言失败，AC-IB-20-06）| `404` / `409`（会话或待确认状态**不存在 / 已丢失** → **fail-closed，不新建会话**，AC-IB-20-05）| `503`（容量，与 `IFC-IB-247` 同源，池满**快速失败**，[TBD-T15] / [TBD-T21]）。
  - **准入顺序（强制，R8）**: `鉴权（Authorization 头）→ 归属断言（session_key 前缀，FM-7）→ SessionStore.load（IFC-IB-221）→ can_resume（IFC-IB-306）→ 续跑（IFC-IB-233）`。**任一前置不满足即 fail-closed**，**不得**退化为「新建会话后重跑」。
  - **R8 配置声明（强制）**: `IB_SESSION_PERSISTENCE_POLICY` 须在 `ib-web` 单元的 `EnvironmentFile` 模板（`IFC-IB-262`）中**显式声明**（AC-IB-20-02）；**只登记键名，不写入任何值**。

### MOD-IB-24 Web 前端 (L5)

- **职责**: 上传/列表/删除/重试/重建页 + 问答页 + **可视化配置页（R7）**；仅通过类型化 HTTP/SSE 契约与后端交互。
- **覆盖需求**: REQ-FUNC-IB-09、IB-17、**IB-25（主）、IB-26（并列主，与 MOD-IB-22）、IB-27（辅）**；**IB-20（R8 新增：问答页对确认中间态与恢复的呈递、流式交付渲染；US-IB-20 / AC-IB-20-04、US-IB-19 / AC-IB-19-01、AC-IB-19-03）**
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
- **R7 可视化配置页约束（IFC-IB-296）**:
  - **视图侧零持久化**：**不得**以 `localStorage` / `IndexedDB` / 独立后端表作为真源（ADR-14）；未提交草稿若存在，须在界面**显式标注「未提交（可丢弃）」**且**不得**作为下次载入源。
  - **白名单制**：只渲染 / 只提交 IFC-IB-292 白名单内的字段；**不得**提供运行期增删图节点、改变拓扑或编辑条件边存在性的入口（REQ-FUNC-IB-26；ADR-14 强制约束③）。
  - **编排图只读渲染**：用图可视化库渲染 `OrchestrationSpecInput` 产生的图（节点参数可编辑、**拓扑不可编辑**）；条件边须能按 `branch_map` 表达分支可达性。
  - **以文档为准刷新**：服务端返回的文档更新后，界面**必须以文档为准**刷新，**不得**用陈旧视图反向覆盖（AC-IB-17-03）；`409` 冲突须给出可读回执而非静默丢弃。
  - **凭据不回显**：配置项只显示**键名**，不显示任何值 / 掩码 / 前缀（AC-IB-17-05）。
  - **离线与数据本地化**：图可视化库及其传递依赖须**随构建产物本地打包**；**禁止运行期 CDN 加载**与任何外发请求（AC-IB-17-06、REQ-NFR-IB-08）。
  - **前端不做校验的最终裁决者**：前端预校验仅为体验优化；**服务端校验器（IFC-IB-290）为唯一裁决者**（界面编辑与直接改文档**一视同仁**）。
- **R8 问答页流式与确认约束（IFC-IB-308）**（R8 新增）:
  - **增量渲染**：`content` 片段到达即渲染，**不得等待 `done`**（AC-IB-19-01）；`done` 到达后**不再追加**该次交互的正文。
  - **完成与产物一次性呈现**：完成事件携带的结构化引用清单（`CompletionPayload`）在**该轮回答下方**一次性呈现；**无引用时不显示引用区**（不显示空占位、不臆造引用，AC-IB-19-05）。
  - **思考分区默认不渲染**：`reasoning` 分区**仅在服务端启用且明确标记为可见时**以可折叠区域呈现；**默认不渲染**（AC-IB-19-03）。
  - **确认中间态独立区呈现 + 决策回传**：收到 `confirmation_required` 时以**独立区域**呈现（**与答复片段视觉可区分**，不并入正文），经 `POST /api/chat/resume`（IFC-IB-307）回传 `ConfirmationDecision`；**未决策则界面不显示为「已完成」**、不自动继续（AC-IB-20-04）。
  - **恢复失败可读回执**：`404` / `409` / `403` 时给出可读提示（如「会话已失效，请重新发起或重新确认」），**不静默丢弃、不自动重跑**（AC-IB-20-05 / 20-06）。
  - **凭据不回显**：只显示**键名**，不显示任何值 / 掩码 / 前缀（延续 IFC-IB-296 口径）。

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

### 4.2.2 R7 无环性再声明（可视化配置增量后）

**结论：DAG 拓扑在 R7 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：R7 的全部新增落在 **MOD-IB-01 / 02 / 23 / 24** 内部（契约与第 14 个端口 / 定义文档数据层 / 装配期闸门与端点 / 可视化视图约束），**§4.1 依赖边清单逐行未改**；因此 `w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **为何不新增模块（编号即拓扑序的边界情形）**：见 §1「R7 补充纪律」。要点：定义文档数据层**必然被组合根 MOD-IB-23 依赖**，而新模块只能取 **≥27** 的编号 → 会产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**；替代的独立服务进程方案则净增第 5 个 systemd 单元（与 C-IB-08 / ADR-03 冲突）。故并入既有模块。
- **新端口不引入新边**：`DefinitionDocumentStore`（IFC-IB-287）定义于 **MOD-IB-01（L0）**；其生产适配器 `FileDefinitionDocumentStore` 由 **MOD-IB-23 在装配期构造**（复用既有边 `23 → 01 / 02`），MOD-IB-02 的实现只依赖 MOD-IB-01（既有边），**二者均不产生新边**。
- **既有单一入口纪律未被绕开**：定义文档是**项目级**工件，`Scope` 仍为必填（ADR-04）；「取定义文档 / 派生结果的唯一入口」与 `CollectionResolver` 的单一入口纪律同构（§2.2 R7 增记）。
- 因此「编号即拓扑序」继续适用于 GROUP_C，并**追加一条边界纪律**：**新增工件若被低编号模块（尤其组合根）依赖，不得新开编号更高的模块**。

### 4.2.3 R8 无环性再声明（零新增依赖边）

**结论：DAG 拓扑在 R8 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：R8 的全部新增落在 **MOD-IB-01 / 02 / 21 / 22 / 23 / 24** 内部（会话与确认的类型化契约 / 键名登记与值域显式化 / 终态与可见性判据 / 恢复判定与装配语义 / 恢复端点与准入 / 呈递与回传约束），**§4.1 依赖边清单逐行未改**；因此 `w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **不新增模块**：与 R7 同理 —— 会话状态与确认中间态**必然被 MOD-IB-21 / 22（低编号）持有并被 MOD-IB-23（组合根）装配**，若新开模块只能取 **≥27** 的编号，会产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**；故并入既有模块（§4.2.2 边界纪律继续适用）。
- **既有边被复用而非新增**：`IFC-IB-307` 的端点在 **MOD-IB-23**（既有边 `23 → 21 / 22` 已存在，无需新边）；`can_resume`（IFC-IB-306）与 `ResumePayload`（IFC-IB-305）定义在 **MOD-IB-22**（依赖 MOD-IB-01 为既有边）；`is_user_visible` / `completion_event` 在 **MOD-IB-21**（依赖 MOD-IB-01 为既有边）。
- **单一入口纪律未被绕开**：会话状态仍**只**经 `SessionStore`（MOD-IB-21 端口）读写，`session_key` 前缀断言（FM-7）沿用；前端仍**只**经 HTTP/SSE 契约（MOD-IB-24 → MOD-IB-23）取数，**不新增任何绕过路径**。
- 因此「编号即拓扑序」继续适用于 GROUP_C；R8 的**边界纪律同 §4.2.2 末句**：新增工件若被低编号模块（尤其组合根）依赖，**不得新开编号更高的模块**。

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
| `SessionStore` | `MemorySessionStore` | 同（内存实现即替身） | `IB_SESSION_BACKEND=memory\|external`（**R8 仅扩展值域（`memory` 或 `external`）；键名与默认值 `memory` 不变**） |
| `AuthzPolicy` | 接入方注入 | `DenyAllPolicy` | **未注入即启动失败** |
| `ConfigurationSource` | 文件 + 环境变量 | 测试用固定字典 | `IB_CONFIG_SOURCE=file\|dict` |
| `DefinitionDocumentStore`（**R7 新增**） | `FileDefinitionDocumentStore`（本地文件；原子写 + 语义哈希乐观并发） | `InMemoryDefinitionDocumentStore`（内存字典 + 同一校验器） | `IB_DEFINITION_DOC_PATH`（路径）；`IB_VISUAL_CONFIG_ENABLED=true\|false` |

> **R2 形态可逆开关说明**：`inproc` = 进程内 `InProcessBgeM3Embedder`（位于 **MOD-IB-09 之内**，**不 import MOD-IB-26**）；切换代价 = 改一个配置值 +（可选）停用 `ib-embed` 单元，**不改任何上层模块、不改 IFC 签名、不改任何既有键名**。三形态须通过**同一套端口一致性测试**（见 §3 MOD-IB-09）。默认保持 `http`：进程内形态的模型内存 × worker 数风险与「与 onnxruntime 同进程」的内存叠加峰值（[TBD-T4']）仍未实测。
> （R2 附：`IB_EMBED_BACKEND` 的**值域**扩展与 `IB_OFFLINE_MODE=1` 的一键离线语义**相容**——离线时仍取该表的「离线/测试」列。）

**一键离线**：`IB_OFFLINE_MODE=1` 等价于把上表全部置为「离线/测试」列（AC-IB-15-01、附录 D）。
> **R7 装配说明（定义文档）**：① 定义文档的**装配期装载 → 准入闸门 → 派生 → 注入**序列见 §3 MOD-IB-23；② 一键离线下 `DefinitionDocumentStore` 取「离线/测试」列（`InMemoryDefinitionDocumentStore`），**装配期闸门与校验器照常执行**（离线亦可验证 AC-IB-18-01/02/05）；③ 新增键 `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED` **只登记键名**，其取值（含路径中的任何敏感信息）一律不进文档、不进日志（凭据纪律）。

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

**（R8）流式与会话的四条规范化补充（REQ-FUNC-IB-20；US-IB-19 / US-IB-20）**：

1. **增量推送与终态单发**（AC-IB-19-01）：`content` 为增量片段，客户端不得等 `done`；完成事件**恰一次**，其后不再有该次交互的内容片段；终态构造经 `completion_event`（IFC-IB-302）。空内容时**不发空的 `content` 帧**（AC-IB-19-05）。
2. **完成事件附结构化产物**（AC-IB-19-02 / 19-05）：终态携带 `CompletionPayload`（IFC-IB-300）；`citations` **可为空元组**，**不编造引用**；引用项为定位信息，不内联字节、不含正文全文。
3. **思考分区与内部产物**（AC-IB-19-03 / 19-04）：`reasoning` **可选且默认不启用**（`IB_REASONING_STREAM_ENABLED` 默认 `false`）；**内部子任务产物永不映射为可见 `kind`**（`is_user_visible`，IFC-IB-303）；**不混帧**。
4. **会话状态与确认中间态**（AC-IB-20-02 / 20-03 / 20-04 / 20-05）：状态经 `SessionStore` 承载（默认内存实现）；**持久化策略须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`），**重启丢弃待确认状态 = fail-closed**（`SessionStateLossOutcome` 唯一取值）；确认门**机制保留、默认关闭、不绑定业务语义**，呈递与回传见 ADR-17；**OQ-IB-07 / OQ-IB-08 保持开放**。

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
| **定义文档（装配期）**（R7 新增） | 文档缺失 / 不可解析 / 完备性校验不通过 | **拒绝装配，服务不启动**（fail-fast）；错误逐条定位到 `path` / `code` / `message`（**不回显凭据值**） | 部署者见启动失败日志（界面尚不可用） | ERROR | **fail-closed（装配期）** |
| **定义文档（运行期读）**（R7 新增） | 运行期文档不可读（被移走 / 权限变化） | `GET /api/config/definition` 返回 `503`（**不返回空文档**）；**问答主链路不受影响**（派生结果已于装配期常驻内存，不重新读文档） | 「配置暂时不可读，请稍后重试」 | ERROR | **fail-closed（配置读）**；对问答链路无影响 |
| **会话状态（待确认中间态）**（R8 新增） | 状态丢失 / 未携决策 / 归属不符 / 会话不存在 | `POST /api/chat/resume`（IFC-IB-307）返回 `404` / `409` / `403`；**不新建会话、不重跑、不静默续跑**（`can_resume` = `False`） | 「会话已失效，请重新发起或重新确认」 | WARN | **fail-closed（会话状态）** |
| **完成事件的结构化产物**（R8 新增） | 本轮无可交付引用（`citations` 为空）或无可交付正文 | **不臆造引用**（`citations=()`）、**不发空的 `content` 帧**；仅以完成事件收束（`had_content=false`），**不追加降级文案**（无引用 ≠ 降级） | 无感（无引用时不显示引用区） | INFO | **fail-open（增强项）**；对问答主链路无影响 |

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
| `DefinitionDocumentStore`（**R7 新增**） | `FileDefinitionDocumentStore` | `InMemoryDefinitionDocumentStore` | 装载失败 / 原子写回 / 乐观并发冲突（`conflict=True`）/ 完备性校验拒绝 / 白名单边界 |

**离线可测的纯逻辑单元**（无外部 IO，AC-IB-15-02）：MOD-IB-01（契约校验）、MOD-IB-02（配置合并与校验）、MOD-IB-07（切分）、MOD-IB-05（注册表分派）、MOD-IB-18（打分与判定）、MOD-IB-19（`parse_route_output` 脏输出）、MOD-IB-14（`fingerprint`）。
**R7 追加的离线可测单元**（纯函数、无外部 IO）：**MOD-IB-02** 的 `validate`（IFC-IB-290）与 `derive`（IFC-IB-291）—— 前者对 **≥7 类**校验项逐条可测（AC-IB-18-01/02/05），后者对派生结果做结构等价断言；配合 `InMemoryDefinitionDocumentStore` 即可在**无任何外部服务**下完成装配期全链路离线验证（AC-IB-18-05）。

**R8 追加的离线可测单元**（**纯函数、无外部 IO、无第三方依赖**）：**MOD-IB-21** 的 `is_user_visible`（IFC-IB-303，含「内部产物永不外流」与「默认不混帧」的判据）与 `completion_event`（IFC-IB-302，含「恰一次」「其后无 `content`」「不臆造」「不发空帧」）；**MOD-IB-22** 的 `can_resume`（IFC-IB-306，含「状态丢失 / 未携决策 / 归属不符 → `False`」的 fail-closed 三例）。配合 **`MemorySessionStore`**（§8 替身表既有行，**未改动**）即可在**无任何外部服务**下完成「会话 → 确认中间态 → 恢复」的**全链路离线验证**（AC-IB-19-01 ~ 05、AC-IB-20-02 ~ 06）。

---

## 9. REQ → MOD 覆盖率矩阵

### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-27，**27/27 全覆盖**；R7 同步计数，v1.2.0 需求总数）

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
| IB-20 | 会话生命周期（流式输出契约 + 会话生命周期；**R8 补设计覆盖**） | **MOD-IB-21** / 22, 23, 24, 01, 02（**US-IB-19 / AC-IB-19-01 ~ 05；US-IB-20 / AC-IB-20-01 ~ 06**） |
| IB-21 | 流式输出 | **MOD-IB-21** / 22, 23 |
| IB-22 | 部署（systemd 单元、配置模板） | **MOD-IB-25** / 02 |
| IB-23 | 多项目隔离（贯穿全链路） | **MOD-IB-03** / 02, 09(Resolver), 10, 11, 12, 15, 17, 23 |
| IB-24 | 索引重建 | **MOD-IB-14** / 12, 13 |
| IB-25 | 可视化配置界面（定义文档的图形视图；round-trip 回写；**无第二真源**；数据不出本地） | **MOD-IB-24** / 02, 01, 23 |
| IB-26 | 可编辑范围（节点参数与专家集合；**不含**运行期改图；白名单制；条件边须显式分支映射） | **MOD-IB-24, MOD-IB-22** / 02, 01 |
| IB-27 | 装配期完备性校验与 fail-fast 准入闸门（可读定位；**无**强制继续开关；界面与直改文档一视同仁；默认专家恰好一个） | **MOD-IB-23, MOD-IB-02** / 01, 24 |

**无缺口**：**27 条 REQ-FUNC**（R7 同步计数；R1 / R2 时点基线 24 条）每条至少一个「主」模块，且每条均可被至少一个 AC 验证（R7 新增 3 条见上三行，AC 落点分别为 AC-IB-17-01~06、AC-IB-17-04 / AC-IB-18-01、AC-IB-18-01~06）。

**（R8）REQ-FUNC-IB-20 的设计覆盖闭环**：需求侧补入 **US-IB-19**（流式交付最终答复；AC-IB-19-01 ~ 05）与 **US-IB-20**（会话生命周期；AC-IB-20-01 ~ 06）后，本需求的设计覆盖由「仅登记 REQ 与模块归属」升级为「**US / AC → ADR / IFC 逐条可追溯**」（见 §9.6 的逐 AC 映射表）：`ADR-17`（承载方式与状态丢失语义）+ `IFC-IB-298 ~ 308`（11 条类型化契约）+ §7.3 / §7.4 / §8 的相应补充。**本轮不重写既有设计**（`IFC-IB-221 ~ 225` / `IFC-IB-231 ~ 233` / `IFC-IB-247` 一字不动）。

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

**R7 说明（NFR 覆盖不变）**：R7 **不新增 NFR 条目**，14 条 NFR 的主 / 辅归属**一行未改**。新增结构对 NFR 的作用为**既有条目的加固**：`DefinitionDocumentStore`（IFC-IB-287）服务 **NFR-11（可维护性 / 模块边界）**；`validate` / `derive`（IFC-IB-290 / 291）为纯函数 + 替身齐备，服务 **NFR-14（可测试性）**；装配期闸门服务 **NFR-02（可配置性）**；「数据不出本地 + 前端禁止 CDN」服务 **NFR-08**。

### 9.3 R1 覆盖率再声明（框架切换后）

**结论：27/27 REQ-FUNC（R7 同步计数；R1 时点基线为 24/24）+ 14 REQ-NFR 覆盖情况在 R1 下不变，无新增缺口。**

- 框架切换只替换 MOD-IB-23 的 HTTP 载体，**不改变任何 REQ 的覆盖模块**：REQ-FUNC-IB-05/06/09/21/23 的主覆盖模块（MOD-IB-23 / MOD-IB-24）未变，仅其内部实现载体由 FastAPI 改为 Django（DRF 视图 + `StreamingHttpResponse`）。
- NFR 侧：NFR-08（数据不出本地 + 外发声明，主覆盖 MOD-IB-20）与 NFR-09（权限与访问控制，主覆盖 MOD-IB-03 / 23）语义不变——鉴权端口 `AuthzPolicy` 仍默认拒绝（`DenyAllPolicy`），Django 中间件/视图装饰器只是其 HTTP 层注入点（见 §2.1.1）。
- 因此 §9.1 / §9.2 矩阵逐行有效，无需改动；本文档仍满足门控「REQ → MOD 全覆盖」标准。

### 9.4 R2 覆盖率再声明（L-03 增量）

**结论：27/27 REQ-FUNC（R7 同步计数；R2 时点基线为 24/24）+ 14 REQ-NFR 覆盖不变，无新增缺口；R2 的新增只**加固**既有覆盖，不改任何既有主/辅归属。**

- **REQ-FUNC-IB-15**（本地 embedding）：R2 前只有 `MOD-IB-09`（端口 + 客户端）承载，**服务端无模块归属**——这正是 L-03；R2 由 `MOD-IB-26` 补上服务端侧（主覆盖并列：09 = 端口/客户端，26 = 服务端线协议）。
- **M-02（页面图绑定）不新增 REQ**：它落在 REQ-FUNC-IB-10 / IB-11（解析并产出页面图）与 IB-14 / IB-17（检索、供专家使用）的**既有语义**之内，故只**增辅覆盖**（MOD-IB-01 / 13 / 21 / 23 / 24），**不新增需求条目、不改变 24/24 的判定**。
- 若 PM 认为「图片回溯」应升格为**独立 REQ**，须回**需求侧**立项 —— 架构层**不自行新增 REQ**（见残余项 R-5）。

---

### 9.5 R7 覆盖率再声明（可视化配置增量）

**结论：27/27 REQ-FUNC（R7 同步计数；R1 / R2 时点基线 24/24）+ 14 REQ-NFR 覆盖达成，无新增缺口。**

- **三条新增需求均有主模块**：IB-25 → **MOD-IB-24** / 02, 01, 23；IB-26 → **MOD-IB-24, MOD-IB-22** / 02, 01；IB-27 → **MOD-IB-23, MOD-IB-02** / 01, 24（见 §9.1 末三行）。
- **施工前置条件 ≠ 覆盖缺口**：REQ-FUNC-IB-25 / 26 / 27 的落地**有施工顺序前置** ——「专家 / 路由 / 编排 / 工具授权的定义须先外置为数据、且为单一真源」（即 REQ-FUNC-IB-01 / IB-02 的**实现落差**）；`requirements_spec.md` §2.7 前言已明示该前提「**不在本节新增需求**」。本文件**不把该前置计为覆盖缺口**：三条需求均已有**主模块 + 类型化接口落点**，受影响的只是**施工先后**（定义外置先于界面填充真实内容）。
- **REV-07-6 判定 = (a) 可登记的前置条件 / 风险，本轮继续**（另见 `architecture_design.md` §8 [ARCH-ASSUMPTION-A7] 与 §10.1）。若 PM / 用户改判 (b)，本修订整体回退并回 GROUP_A 立项 —— **该裁定权不在本代理**。
- **模块与依赖不变**：R7 **未新增模块、未新增依赖边**（§1 R7 补充纪律、§4.2.2）；`IFC-IB-001~286` 与 13 个既有端口名一字不动（新增 287~297 为纯追加，`IFC-IB-285` 仍预留）。
- **无在库悬置项**：`implementation_plan.md`（GROUP_C）内的「24/24 PASS」为**离线自检用例数**，与本文件的 REQ 计数 **27** 属**不同口径**，本文件**不得**据此改写该文件。

### 9.6 R8 覆盖率再声明（REQ-FUNC-IB-20 的设计覆盖闭环）

**结论：27/27 REQ-FUNC + 14 REQ-NFR 覆盖达成，无新增缺口；REQ-FUNC-IB-20 由「模块归属已登记」升级为「US / AC 逐条可追溯」。**

| AC | 需求要点 | 设计落点（R8） | 状态 |
|----|----------|----------------|------|
| AC-IB-19-01 | 增量交付、终态恰一次单发 | `IFC-IB-302`（`completion_event`）；§7.3 补充 1 | **新增** |
| AC-IB-19-02 | 完成事件附结构化产物 | `IFC-IB-300`（`CompletionPayload` / `CitationItem`）+ `IFC-IB-302`；§7.3 补充 2 | **新增** |
| AC-IB-19-03 | 思考分区可选且默认不启用 | `IFC-IB-304`（`IB_REASONING_STREAM_ENABLED`，默认 `false`）+ `IFC-IB-303`；§7.3 补充 3 | **新增** |
| AC-IB-19-04 | 内部子任务产物不外流 | `IFC-IB-303`（`is_user_visible`：内部产物永不映射为可见 `kind`）；§7.3 补充 3 | **新增（ADR-09 的具体化）** |
| AC-IB-19-05 | 空内容边界、不臆造 | `IFC-IB-300`（`citations` 可空 + `had_content`）+ `IFC-IB-302`；§7.4 第二新增行 | **新增** |
| AC-IB-20-01 | 会话键与状态承载 | `IFC-IB-298`（`SessionState`，补齐悬置引用）+ 既有 `IFC-IB-221/222` + FM-7（§7.3） | **补齐既有缺口** |
| AC-IB-20-02 | 持久化策略须显式声明 | `IFC-IB-299`（枚举）+ `IFC-IB-304`（键名）+ `IFC-IB-307`；部署落点 `IFC-IB-262`（MOD-IB-25） | **新增** |
| AC-IB-20-03 | 机制存在、默认不启用、不绑定业务语义 | `IFC-IB-301`（结构 + `confirmation_required` 值域追加）+ `IFC-IB-304`（默认 `false`）+ `IFC-IB-306`；ADR-17 约束 1 / 2 | **新增** |
| AC-IB-20-04 | 呈递与决策回传 | `IFC-IB-301`（呈递）+ `IFC-IB-307`（回传端点）+ `IFC-IB-308`（界面约束）；ADR-17 约束 3 | **新增** |
| AC-IB-20-05 | 携决策则续跑 / 未携或丢失则 fail-closed | `IFC-IB-299`（唯一取值）+ `IFC-IB-305` + `IFC-IB-306`（`can_resume`）+ `IFC-IB-307`；§7.4 第一新增行 | **新增** |
| AC-IB-20-06 | 归属断言与不新建会话 | `IFC-IB-307`（`403` / `404` / `409`，准入顺序显式化）+ FM-7（§7.3） | **新增** |

**边界声明（R8）**：

- **既有设计一字未改**：`IFC-IB-221 ~ 225`（`SessionStore` 3 方法 + `StreamEvent` / `to_sse`）、`IFC-IB-231 ~ 233`（`build_graph` / `run` / `resume`）、`IFC-IB-247`（既有 SSE 端点）的**号 / 名 / 签名 / 字段集一字不动**；R8 只**追加** `IFC-IB-298 ~ 308`。
- **模块与依赖不变**：模块数仍 **26**、端口数仍 **14**、**§4.1 依赖边逐行未改**（§4.2.3）；REQ→MOD 覆盖仍 **27/27 + 14 NFR**（**无新 REQ**）。
- **OQ 处置**：**OQ-IB-07 / OQ-IB-08 均保持开放**；R8 只落地「默认关闭 / 会话内隔离」的**安全默认**，**不裁决业务语义**（ADR-17；`architecture_design.md` §10.1 R8 行）。
- **架构侧对应**：`architecture_design.md` 1.4.0（R8）的 **ADR-17**、**§2.0.3 R8 影响复核表**、§1.3 R8 注、§6 四条规范化补充、[ARCH-ASSUMPTION-A8]、[TBD-T21]。

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

- **门控标准 1（REQ → MOD 全覆盖）**：§9.1 逐条列出 **27 条 REQ-FUNC**（R7 同步计数：新增 IB-25 / IB-26 / IB-27 三行，各有主模块），**每条均有主模块**，无缺口；§9.2 覆盖 14 条 REQ-NFR（R7 未变）。
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
    - **R7 自检（可视化配置增量，GROUP_A REV-06 下游贯通）**：
      - **覆盖同步**：§9.1 由 24/24 同步为 **27/27 REQ-FUNC**（新增 IB-25 / IB-26 / IB-27，各有主模块），§9.2 NFR 覆盖未变（14 条，另见该节 R7 说明）；§9.3 / §9.4 结论句以括注保留历史基线；**§9.5 给出 R7 再声明**（含「施工前置条件 ≠ 覆盖缺口」）。
      - **零新增模块 / 零新增依赖边**：模块数仍 **26**；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 23 / 24（§1 R7 补充纪律给出「为何不新增 MOD-IB-27」的编号论证；§4.2.2 给出无环性再声明）。
      - **类型化未降级**：新增 `IFC-IB-287~297`（11 条）全部为 `name: type` + 可空性的**类型化契约**（IFC-IB-287 为端口 Protocol + 结构定义），均为 **frozen dataclass / 纯 stdlib、零第三方依赖**；`ValidationReport` 结构上**不含** `force` / `ignore` / `warn_only`（「无强制继续开关」= **类型层事实**）。
      - **编号纪律未破**：`IFC-IB-001~286` 一字不动；新增 287~297 为**纯追加**；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。
      - **施工前置已登记且不阻断**：§9.5 显式声明前置与其非缺口性质；**REV-07-6 判定 = (a)**；本轮**未**设计 REQ-FUNC-IB-01 / IB-02 的实现方案（超 GROUP_B 边界，需求侧亦未立项）。
      - **边界合规**：R7 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为**离线自检用例数**，与本文件 REQ 计数 27 **不同口径**）；**未写入任何凭据或配置值**（只登记键名：`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；本阶段**止于 GROUP_B**。
    - **R8 自检（REQ-FUNC-IB-20 设计覆盖闭环，GROUP_A REV-11-1 下游贯通）**：
      - **覆盖闭环已贯通**：§9.1 的 `| IB-20 |` 行登记 **US-IB-19 / US-IB-20** 与 11 组 AC；§9.1 追加 R8 覆盖闭环段；**§9.6 给出逐 AC 映射表**（`AC-IB-19-01 ~ 05`、`AC-IB-20-01 ~ 06` 共 11 条**全部有落点**）；MOD-IB-21 / 22 / 23 / 24 / 01 / 02 的「覆盖需求」均补登记其 R8 归属。
      - **零新增模块 / 端口 / 依赖边**：模块数仍 **26**、端口数仍 **14**（`SessionStore` 仍 3 方法）；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 21 / 22 / 23 / 24（§4.2.3 给出无环性再声明与「为何不新增模块」的编号论证）。
      - **类型化未降级**：新增 `IFC-IB-298 ~ 308`（11 条）全部为 `name: type` + 可空性的**类型化契约**，均为 **frozen dataclass / 纯 stdlib、零第三方依赖**；`SessionStateLossOutcome` 的**唯一取值**使「状态丢失 = 安全失败」成为类型层事实；`CompletionPayload.citations` 可为空元组使「不臆造引用」成为结构事实。
      - **编号纪律未破**：`IFC-IB-001 ~ 297` 的号 / 名 / 签名 / 字段集**一字不动**（含 `IFC-IB-221/222` / `IFC-IB-233` 的签名文本）；新增 298 ~ 308 为**纯追加**；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。
      - **既有设计未被改写**：`IFC-IB-221 ~ 225`、`IFC-IB-231 ~ 233`、`IFC-IB-247`、§5 装配表既有行、§6 状态机、§7.1 / §7.2 表、§10 FreeArk 映射表**均未改动**；`IB_SESSION_BACKEND` **键名与默认值不变**（仅扩展值域，沿用 R2 先例）。
      - **OQ 未越权**：**OQ-IB-07 / OQ-IB-08 保持开放**；R8 只落地「默认关闭 / 会话内隔离」的安全默认，**不裁决**「是否应默认启用确认门」「历史是否跨会话」；架构层不自行扩围或缩围。
      - **边界合规**：R8 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；需求侧文档（`requirements_spec.md` v1.3.0 / `user_stories.md` v1.3.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **未改**（无新第三方依赖）；**未写入任何凭据或配置值**（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）；本阶段**止于 GROUP_B**。
