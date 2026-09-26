<file_header>
  <project>intelligentbase</project>
  <artifact>architecture_design</artifact>
  <path>docs/architecture_design.md</path>
  <doc_id>ARCH-INTELBASE-001</doc_id>
  <version>1.2.0</version>
  <revision>R2</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_03 系统架构设计</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-09-25</updated_at>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.1.0" status="APPROVED"/>
    <readonly_reference path="FreeArk 仓库" note="只读参考；本阶段未修改 FreeArk 任何文件"/>
  </inputs>
  <locked_decisions source="requirements_spec.md §6.0">DR-01 Qdrant 单实例非容器 | DR-02 bge-m3 稠密本地 | DR-03 禁 Docker 全裸装 | DR-04 云端 DeepSeek 可配置 | DR-05 千级文档量级 CPU-only 假设 | DR-06 单实例多项目 | DR-07 须支持索引重建 | DR-08 v1 纳入 OCR</locked_decisions>
  <revision_history>
    <rev version="1.0.0" date="2026-09-25" note="初稿（GROUP_B 首次提交，PM 门控前）"/>
    <rev version="1.1.0" revision="R1" date="2026-09-25" note="按 PM 架构复核反馈 REV-01 修订：① 后端 Web 框架 FastAPI → Django（+DRF）（用户明确指定，非建议），前端 Vue 3 + Vite 不变；② 流式载体改为 Django 同步视图 + StreamingHttpResponse 原生 SSE（text/event-stream），不引 Channels、不引 Redis；③ 新增 §2.0「框架切换影响复核表」，对 ADR-01~13 共 13 条逐条复核（受影响 5 条：ADR-03/07/08/11/13；不受影响 8 条）；④ ADR-11 全文重写为 ADR-11-R1（评估 A/B/C 三方案，量化升级触发条件，Option C 拒绝），两个 FreeArk 真实坑（?token= 入访问日志、channels_redis × redis-py 不兼容）写成强制实施约束；⑤ ADR-01 端口方法数更正为 11（IFC-IB-100~110，以 module_design.md 为权威）；ADR-03/07/08/13 各追加 -R1 修订节，ADR-02/04/05/06/09/10/12 逐条写入「经检查，不受框架切换影响」；⑥ ARCH-ASSUMPTION-A2 关闭（已确认=软隔离）、OQ-IB-01 关闭（原文件保留 ON）、A4 保持 TBD；⑦ 新增 [TBD-T15]（SSE 并发上限）；§10.2 许可台账补登 Django/DRF/Waitress/Gunicorn。不变约束：模块数 25、端口 13、IFC-IB 编号 58 个使用中全部不变（仅改载体说明）、DAG 无环、覆盖 24/24 REQ-FUNC + 14 NFR。需求侧文档与 FreeArk 仓库未改动。"/>
    <rev version="1.2.0" revision="R2" date="2026-09-26" invocation_id="INV-GROUP_B-INTELBASE-004" note="R2 补交（L-03：ib-embed 服务端无模块归属与契约）：① 追加 ADR-02-R2 附注——ib-embed 的服务端归属成立（MOD-IB-26，补齐既有 Option B 决策的落点，Decision/Options/Consequences 未改）、冷/热双路径单一落点在客户端、形态可逆值域显式化为 http|inproc|fake；并随附登记「错误码语义映射不变式」（4xx/409=重试无用，5xx=重试可能有用）；② 新增 §2.0.1 R2 影响复核表（ADR-01~13 逐条：ADR-02 受影响（仅补附注）、其余 12 条 R2 不受影响），并为 ADR-04/06/11/13 追加 inline R2 复核句；③ §9 TBD 清单补 [TBD-T16]（ib-embed 并发与线程校准）与 [TBD-T18]（目标机 CPU 指令集 AVX2 基线实测），并声明 [TBD-T17] 为预留未分配；④ §10.3 自检追加 R2 行。不变约束：模块数 25→26（仅追加）、端口 13、IFC-IB 001~265 一字不动（新增 266~284/286）、DAG 无环、覆盖 24/24 REQ-FUNC + 14 NFR。需求侧文档与 FreeArk 仓库未改动。"/>
  </revision_history>
  <scope_boundary>只做架构与模块设计；不含实现代码、测试用例、部署脚本。允许接口签名、类型注解、数据结构定义。</scope_boundary>
</file_header>

# 系统架构设计 — intelligentbase 通用 RAG + 多智能体可复用基础架构

**版本**: 1.2.0（R2 补交）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26
**R2 修订摘要（L-03：`ib-embed` 服务端无模块归属与完整契约）**: 追加 **ADR-02-R2 附注**（服务端归属成立 = 新增 MOD-IB-26；冷/热单一落点在客户端；形态可逆值域 `http|inproc|fake`），新增 **§2.0.1 R2 影响复核表**（**受影响 1 条：ADR-02（仅补附注）**；**R2 不受影响 12 条**：ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13），并为 ADR-04 / 06 / 11 / 13 追写 inline R2 复核句；§9 补 **[TBD-T16] / [TBD-T18]** 并声明 **[TBD-T17] 预留未分配**。**不变**：§1 / §3~§7 的结论、模块数与端口数、`IFC-IB-001~265`、REQ→MOD 覆盖矩阵、DAG 无环（R2 只追加）。
**R1 修订摘要**: 后端 Web 框架 **FastAPI → Django（+ DRF）**（用户明确指定，非建议）；流式载体改为 **Django 同步视图 + `StreamingHttpResponse` 原生 SSE**（**不引 Channels、不引 Redis**）；受影响 ADR **5 条**（ADR-03 / 07 / 08 / 11 / 13），其中 **ADR-11 全文重写（ADR-11-R1）**，逐条复核见 §2.0；模块数 / 端口数 / IFC-IB 编号 / 覆盖矩阵**均未变**（改动仅载体说明）。
**输入**: `requirements_spec.md` v1.1.0（APPROVED）、`user_stories.md` v1.1.0（APPROVED）
**文档分工**: 本文 = 架构决策（ADR）+ 架构级设计。模块清单、类型化接口契约、依赖图 DAG 证明、REQ→MOD 覆盖率矩阵、状态机与降级矩阵详表见 `module_design.md`；技术选型与许可合规表见 `tech_stack.md`。

**标记约定**: `[ARCH-ASSUMPTION-An]` 架构假设（需 PM 确认）；`[ESTIMATE]` 估计（非实测）；`[TBD-Tn]` 必须部署阶段在目标机实测校准；`[需 PM 确认]` 需 PM/用户裁决。**本文件不含任何编造的实测数值。**

---

## 1. 架构概览

### 1.1 架构风格与关键性质

**选定：分层 + 端口适配器（Ports & Adapters）的模块化单体；单实例多项目；全物理机直部署（禁 Docker）。**

| 维度 | 结论 | 依据 |
|------|------|------|
| 部署拓扑 | 单实例多项目（同机多进程 / 多 systemd 单元） | DR-03、DR-06 |
| 代码组织 | 一个仓库、三个可独立启动的进程入口（web / worker / embed） | REQ-NFR-IB-11；[ARCH-ASSUMPTION-A5] |
| 依赖方向 | 单向由外向内：应用层 → 管线层 → 适配器层 → 契约层；**契约层零依赖** | REQ-NFR-IB-01、IB-11 |
| 可替换性 | 解析 / 切分 / embedding / 向量库 / 台账 / 原文件 / OCR / 渲染 / LLM 各为「端口 + 适配器」 | REQ-NFR-IB-11 |
| 编排骨架 | **业务零依赖**（依赖反转）：业务语义由调用方构造后透传 | REQ-NFR-IB-01；AC-IB-11-06 |
| 框架依赖 | 仅编排层（langgraph/langchain）与 Web 层（**Django + DRF**；R1 由 FastAPI 变更），且均被端口隔离 | REQ-NFR-IB-11 |

**为何不是微服务**：DR-05（千级文档量级）+ DR-03（禁 Docker）+ C-IB-08（最小权限/最小组成面）共同否定了微服务的收益。可复用性由**配置化 + 端口化 + 专家/工具可插拔**达成。但**三处进程边界是刻意保留的**（`ib-web` / `ib-worker` / `ib-embed`），因三者有独立故障域与资源特征（ADR-02 / ADR-10）。

### 1.2 分层

| 层 | 模块 | 说明 |
|----|------|------|
| **L5 应用与运维** | MOD-IB-23 HTTP API、MOD-IB-24 Web 前端、MOD-IB-25 部署运维 | 组合根（唯一装配点）在此层 |
| **L4 多智能体编排**（业务零依赖） | MOD-IB-16 专家注册表、MOD-IB-17 工具注册、MOD-IB-18 语义路由、MOD-IB-19 意图路由内核、MOD-IB-20 LLM 端点、MOD-IB-21 流式与会话、MOD-IB-22 编排图 | 唯一允许依赖 langgraph 的层 |
| **L3 数据管线与检索** | MOD-IB-11 台账、MOD-IB-12 原文件、MOD-IB-13 文档生命周期、MOD-IB-14 索引重建、MOD-IB-15 检索服务 | 跨存储一致性的唯一归属地 |
| **L2 外部依赖适配器** | MOD-IB-06 OCR、MOD-IB-08 页面渲染、MOD-IB-09 Embedding、MOD-IB-10 VectorStore | 端口实现在此；故障降级语义在此固化 |
| **L1 解析与切分**（纯 CPU、无外部 IO） | MOD-IB-05 解析器注册表与格式解析器、MOD-IB-07 切分器 | 可离线单测 |
| **L0 契约与横切** | MOD-IB-01 核心契约（零依赖）、MOD-IB-02 配置、MOD-IB-03 请求上下文、MOD-IB-04 可观测性 | MOD-IB-01 不 import 任何第三方框架 |

**依赖铁律**：编译期依赖只允许由编号大的模块指向编号小的模块 → 严格 DAG，证明见 `module_design.md` §4。**运行期装配与编译期依赖分离**：装配集中在 MOD-IB-23 组合根，见 `module_design.md` §5。

### 1.3 可替换点（对应 REQ-NFR-IB-11）

| 可替换点 | 端口（定义于 MOD-IB-01） | v1 适配器 | 替换成本 | 验收 |
|----------|--------------------------|-----------|----------|------|
| 向量库 | `VectorStore` | `QdrantVectorStore` + `InMemoryVectorStore`（替身） | 新增适配器 + 改配置 | AC-IB-06-05 |
| 向量模型/维度 | `CollectionSpec.dim` + `Embedder.descriptor()` | bge-m3 / dim=1024 | 改配置 + 触发重建 | REQ-FUNC-IB-24 |
| Embedding | `Embedder` | `LocalHttpEmbedder` + `FakeEmbedder` | 新增适配器 | AC-IB-07-02 |
| LLM | `LlmProvider` | `OpenAiCompatibleProvider`（DeepSeek）+ `FakeLlmProvider` | 新增适配器（端点可配） | DR-04、AC-IB-12-05 |
| 文档格式 | `DocumentParser`（按扩展名注册） | docx / pdf / md / txt | 注册新解析器 | AC-IB-04-05 |
| OCR | `OcrEngine` | `RapidOcrEngine` + `NullOcrEngine` | 新增适配器 | AC-IB-04-07 |
| 页面渲染 | `PageRenderer` | `PdfiumRenderer` | 新增适配器 | AC-IB-04-06 |
| 台账 | `LedgerRepository` | `SqliteLedgerRepository` + `InMemoryLedgerRepository` | 新增适配器（如接 PG/MySQL） | REQ-NFR-IB-11 |
| 原始文件 | `BlobStore` | `FsBlobStore` | 新增适配器 | ADR-05 |
| 会话状态 | `SessionStore` | `MemorySessionStore`（可选持久化实现） | 新增适配器 | REQ-FUNC-IB-20 |
| 鉴权 | `AuthzPolicy` | `DenyAllPolicy`（安全默认）+ 接入方注入；**R1：Django 侧落点 = 中间件（解析已认证主体 → 构造 `RequestContext` / `AuthzContext`）+ 视图装饰器（调用 `can_manage` / `can_query`）** | 注入一个实现（**未注入即启动失败**，默认拒绝） | AC-IB-11-05 |
| 配置来源 | `ConfigurationSource` | 文件 + 环境变量 | 新增适配器（如接配置中心） | REQ-FUNC-IB-01 |

### 1.4 请求上下文传播（隔离贯穿全链路）

三处刻意设计，使「项目 / 知识库」范围**在类型层面无法被漏传**：

1. **`Scope` 为必填参数**：`VectorStore.upsert/query/delete_by_doc/delete_by_scope`、`RetrievalService.search`、`LedgerRepository.list_by_scope` 的 `scope` **无默认值**——不传即类型检查期报错，而非运行期静默全库检索。这是对「漏 filter 即泄漏」的**结构性防御**（§3.3 FM-1/FM-3）。
2. **范围不可由客户端自证**：HTTP 层从已认证主体解析 `project_id`，**不信任**请求体中的 project 字段；知识库标识若由请求体给出，须经 `LedgerRepository.assert_kb_in_project(project_id, kb_id)` 归属断言，失败返回 **403**（非 404，避免存在性探测）。
3. **上下文两段式传递**（对齐 ADR-09）：
   - **机械传播段**（骨架可见但不解释语义）：`request_id`、`session_key`、`scope_token`（不透明字符串，仅用于日志与线程 id 拼装）；
   - **语义段**（骨架完全不可见）：知识库范围封装进**工具闭包与检索客户端构造期**——`knowledge_search` 工具在装配时已绑定 scope，路由/聚合节点看到的只是无参工具。

   故 REQ-FUNC-IB-23 的「隔离贯穿上传 → 存储 → 检索 → 路由上下文」成立，而骨架无需理解隔离模型——这正是 REQ-NFR-IB-01（新项目核心代码改动 0 行）与 REQ-FUNC-IB-23 同时成立的关键。

---

## 2. 架构决策记录（ADR）

> 每条 ADR 含 Context（REQ 引用）/ Options（≥2，含已评估未采纳项留痕）/ Decision / Status / Consequences。`[锁定]` = 用户已拍板（DR-*），ADR 只决策其落地方式。

### 2.0 框架切换影响复核表（R1 新增：FastAPI → Django）

> **背景**：用户于 R1 **明确指定后端框架为 Django（非建议）**，1.0.0 的「FastAPI + Uvicorn」载体随之撤销（详见 **ADR-11-R1**）。本节对 1.0.0 的 **13 条 ADR（ADR-01 ~ ADR-13）逐条复核**框架切换的影响，作为「设计未因载体替换而漂移」的可审计证据。
> **复核口径**：凡 ADR 的决策客体位于 **L0 契约层 / L1 解析层 / L2 适配器层 / L3 管线层 / L4 编排层**，或位于 **L5 但与 Web 框架的请求-响应机制无关**，即判「**经检查，不受框架切换影响**」；凡决策客体**直接落在 Web 层（HTTP 请求-响应、长连接流式、依赖注入载体、迁移/schema 机制）**者，判「**受影响**」并给出对应 `-R1` 修订节。

| ADR | 决策客体 | 所在层 | R1 复核结论 | 处置 | 说明 |
|-----|----------|--------|-------------|------|------|
| ADR-01 | 向量库抽象层与 Qdrant 集成方式 | L2（MOD-IB-10） | **经检查，不受框架切换影响** | 仅**契约编号一致性更正**：端口方法数 **10 → 11**（含 `flush()`），IFC-IB-100~**110**，**以 `module_design.md` 为权威** | 端口位于适配器层，与 HTTP 载体无关；`qdrant-client` 为独立库 |
| ADR-02 | embedding 服务部署形态与 CPU 推理策略 | L2（MOD-IB-09） | **经检查，不受框架切换影响** | 无需修订（仅追写复核行） | `ib-embed` 为独立 systemd 单元；端口、冷/热双路径纪律与「形态可逆」均不变 |
| ADR-03 | 部署形态（systemd 裸装编排） | L5（MOD-IB-25）+ 进程载体 | **受影响** | **ADR-03-R1**：`ib-web` 载体由 ASGI（Uvicorn）改 **Waitress / Gunicorn（WSGI）**；写明 SSE 下 worker/线程占用与并发上限，新增 **[TBD-T15]** | `ib-web` 的应用服务器是 Web 框架的直接后果；四单元清单与部署检查项不变 |
| ADR-04 | 多项目隔离实现 | L0 / L2 / L3（MOD-IB-01/10/15） | **经检查，不受框架切换影响** | **ADR-04-R1**：ARCH-ASSUMPTION-A2 由「待确认」改为「**已确认 = 软隔离**（项目级硬隔离 collection + KB 级软隔离 filter）」；`CollectionResolver.resolve()` 单入口收敛设计不变 | 隔离是数据层设计（collection + payload filter），与 Web 框架无关 |
| ADR-05 | 原始文件持久化与索引重建 | L3（MOD-IB-12/14） | **经检查，不受框架切换影响** | **ADR-05-R1**：Status 追加「**OQ-IB-01 已确认 = 原文件保留（ON）**」；DR-07 的 sha256 内容寻址 + 原子重建**不变** | blob 落本地文件系统；版本切换是台账上的一次原子写 |
| ADR-06 | PDF 解析库许可合规选型 | L1（MOD-IB-05/08） | **经检查，不受框架切换影响** | 无需修订（仅追写复核行） | 纯库选型（`pypdf` / `pdfminer.six` / `pdfplumber` / `pypdfium2`），与 Web 框架无关 |
| ADR-07 | 元数据 / 台账存储 | L3（MOD-IB-11） | **受影响**（须显式排除 Django ORM） | **ADR-07-R1**：台账**不经 Django ORM**；保留 `LedgerRepository` 端口 + **自管 SQL**（WAL / `busy_timeout` / 条件 UPDATE 认领 / 租约回收）+ **手写 scoped 迁移**；PG 升级路径保留 | 若由 ORM 承接会连带引入 Django 迁移机制（`makemigrations` 全量产物），与「禁全量自动产物」纪律冲突，且把 schema 演进绑死 Web 框架发布节奏 |
| ADR-08 | LLM 端点抽象与数据外发边界 | L4（MOD-IB-20） | **受影响**（复核结论 = **无冲突**） | **ADR-08-R1**：`LlmProvider` 位于 L4 且被端口隔离；langchain **同步**流式语义与 WSGI-SSE **同构**；配置一律环境变量注入；**沿用 `langchain-openai` pin `<0.3`** | 唯一与 Web 层相邻的是「同步 / 异步流式模型」，复核后同构，故设计不变 |
| ADR-09 | 编排骨架业务零依赖（依赖反转） | L4（MOD-IB-22） | **经检查，不受框架切换影响** | 无需修订（仅追写复核行） | 骨架只认端口与纯数据；两段式上下文与装配期闭包绑定与 Web 框架无关 |
| ADR-10 | 异步入库执行形态与队列载体 | L3 + `ib-worker` 进程 | **经检查，不受框架切换影响** | 无需修订（仅追写复核行） | 以台账表本身为队列 + 独立 systemd 单元；条件 UPDATE 认领保证多 worker 不重复处理，与 `ib-web` 的 worker 模型无关 |
| ADR-11 | Web 层技术栈与流式通道 | L5（MOD-IB-21 / 23） | **受影响（核心，全文重写）** | **ADR-11-R1**：Option A（选定）= Django + DRF **同步视图 + `StreamingHttpResponse` 原生 SSE**（**不引 Channels、不引 Redis**）；Option B = Django 异步视图 + `uvicorn.workers.UvicornWorker`（**升级路径，默认不启用，含量化触发条件**）；Option C = Channels + Redis（**拒绝**）；两个 FreeArk 真实坑写成**强制实施约束** | 1.0.0 的「FastAPI + Uvicorn」与「Channels」两处结论均须改写；「SSE 而非 WebSocket 以防凭据进 URL」的反泄漏初衷保留 |
| ADR-12 | OCR 与页面渲染端口 | L2（MOD-IB-06/08） | **经检查，不受框架切换影响** | 无需修订（仅追写复核行） | 两个端口与降级语义均在适配器层；`NullOcrEngine` 的显式装配与 Web 框架无关 |
| ADR-13 | 检索结果契约与降级语义 | L0（MOD-IB-01）+ HTTP 边界 | **受影响**（仅载体表达形式） | **ADR-13-R1**：`RetrievalResult` 载体 = **frozen dataclass（端口层）+ DRF Serializer（HTTP 边界）**；**类型完整度不得降级**（门控标准 4） | 端口契约仍**零第三方依赖**；字段名 / 类型 / 可空性逐字段保留，降级语义不变 |

**复核小结**：受影响 **5 条**（ADR-03 / 07 / 08 / 11 / 13，其中 **ADR-11 为核心重写**）；不受影响 **8 条**（ADR-01 / 02 / 04 / 05 / 06 / 09 / 10 / 12，ADR-01 另有契约编号更正）。**无一条 ADR 未复核**。所有改动**不触及**模块数（25）、端口数（13）、IFC-IB 编号体系与 REQ→MOD 覆盖矩阵。

### 2.0.1 R2 影响复核表（R2 补交：`ib-embed` 服务端归属 + M-02 页面图绑定）

> **口径**：R2 是**追加式增量**（新增模块 1 个、新增 IFC 段、新增读路径端点与关联表），**不改既有契约**。凡决策客体未被 R2 增量触及者，一律**显式声明「R2 不受影响」**，以便门控区分「已检查」与「漏检查」。以下逐条覆盖 ADR-01 ~ ADR-13（**无一条跳过**）。

| ADR | R2 复核结论 | 一句话理由 |
|-----|-------------|-----------|
| ADR-01 | **R2 不受影响** | Qdrant 端口与 collection 维度声明未动；M-02 的图片关联落在**台账（SQLite）**而非向量库 payload，不触碰 `PointPayload` / `CollectionSpec`（IFC-IB-001~012、100~110 不变） |
| **ADR-02** | **受影响（仅补附注；Decision / Options / Consequences 不变）** | 见上方 **ADR-02-R2 附注**：补齐 `ib-embed` 的服务端模块归属（MOD-IB-26）与契约单一落点；形态可逆**值域**显式化 |
| ADR-03 | **R2 不受影响** | systemd 单元清单仍为四个（`ib-embed` 单元**早已存在**）；R2 未新增单元、未改 `ib-web` 载体；第二份 `EnvironmentFile`（IFC-IB-286）是 ADR-03 既定做法「每单元一个 EnvironmentFile」的**补齐**，非新决策 |
| ADR-04 | **R2 不受影响** | 隔离机制未动：`Scope` 仍**必填**、`CollectionResolver` 仍为**唯一**解析入口；M-02 的图片端点与关联表**一律带 `scope` 并复用归属断言**（IFC-IB-283 的 403/404 口径与 §1.4 第 2 条一致）——是 ADR-04 的**应用**而非修改 |
| ADR-05 | **R2 不受影响** | 原文件内容寻址与重建流程未动；`ChunkImageRecord` 是**派生关联元数据**（可由原文件重建），**不成为新的真源**；重建时随文档重跑再生，**不改 `fingerprint` 因子** |
| ADR-06 | **R2 不受影响** | PDF 库选型与三路径未动；M-02 消费的是解析**已产出**的页面图信息，**不引入任何新 PDF 库**（尤其**未引入 PyMuPDF / AGPL-3.0**） |
| ADR-07 | **R2 不受影响** | 台账仍为 SQLite + `LedgerRepository` 端口 + 自管 SQL + **手写 scoped 迁移**；新增关联**表**经同一端口与同一迁移纪律落地，**不经 Django ORM**；写序仍为「向量成功后才置 `indexed`」 |
| ADR-08 | **R2 不受影响** | LLM 端点抽象与外发边界未动；M-02 **不外发图片字节**（`related_images` 只传**站内** `url_path`），`describe_egress()` 的 `data_categories` **无需扩项** |
| ADR-09 | **R2 不受影响** | 骨架业务零依赖未动；`related_images` 是流事件的**既有 `kind`**（IFC-IB-224 早已枚举），R2 只定义其**载荷类型**，不向骨架注入业务语义 |
| ADR-10 | **R2 不受影响** | 异步入库仍以台账表为队列；`bind_page_images` 为**纯函数**、`persist_page_images` 在同事务内，**不新增任务类型、不改租约语义** |
| ADR-11 | **R2 不受影响** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；新端点 IFC-IB-283 是**普通 HTTP 响应（非流式）**，不占用 worker 长连接预算，与 [TBD-T15] 的容量纪律相容；「禁止 `?token=`」纪律在 R2 **扩展到全部端点**（含图片端点） |
| ADR-12 | **R2 不受影响** | OCR 与渲染**两个端口**及降级语义未动；M-02 把 OCR 产出的页面图**关联**到同页文字块，是**消费**既有的 `ParsedChunk.page_or_section` / `locator` / `source_kind`，不改端口签名 |
| ADR-13 | **R2 不受影响** | `RetrievalResult` 字段与降级语义未动；`related_images` 走**独立的流事件**而非并入 `RetrievalResult`，故「故障 vs 空结果可区分」的不变式不受影响；R2 另为 §7.4 增补一格降级行 |

**R2 复核小结**：**受影响 1 条**（ADR-02，且**仅补附注**）；**R2 不受影响 12 条**（ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13）。**无一条 ADR 未复核**。R2 的所有改动**不触及**：端口数（13）、`IFC-IB-001~265` 编号体系、REQ→MOD 覆盖矩阵（仍 24/24 + 14）与 DAG 无环性（模块数 25 → 26，纯追加）。

### ADR-01 向量库抽象层与 Qdrant 集成方式

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-13（存储）/14（检索）/16（一致性）/23（隔离）；REQ-NFR-IB-11（可替换）/14（替身可测）。AC-IB-06-05 明确要求「替换向量库实现只需改配置与客户端适配，上层无需改动，含替身的既有测试全部通过」。选型已由 DR-01 锁定为 Qdrant（单实例、非容器裸装）；本 ADR 决策的是**集成方式与抽象层边界**，非选型本身。
- **Options**:
  - **A 无抽象层，上层直依赖 `qdrant-client`**：优—代码最少、无映射层损耗、Qdrant 全部能力直用。缺—**直接违反 AC-06-05**；无端口则无法构造「向量库不可达」替身，AC-14-05（降级路径须有替身测试覆盖）不可达；离线 CI 需真 Qdrant（与附录 D「测试不得依赖网络/生产服务」冲突）。
  - **B 窄接口 `VectorStore` 端口 + `QdrantVectorStore` / `InMemoryVectorStore` 双适配器** ← **选定**：优—AC-06-05 与 REQ-NFR-IB-14 直接满足；可对两适配器跑同一套**端口一致性测试**，把「替换后行为等价」变成可执行断言；类型化契约满足门控标准 4；内存替身兼作度量对齐的对照实现。缺—引入 payload ↔ 领域契约映射层（需维护）；Qdrant 高级能力（混合检索/量化）须经扩展方法透出；多一层间接（相对网络 RTT 可忽略）。
  - **C 复用 langchain `VectorStore` 抽象（langchain-qdrant）**：优—与 langgraph 同族、社区维护。缺—抽象面过宽；版本耦合风险（同栈曾因 `langchain-openai` 破坏性变更致生产漂移）；`Document.metadata: dict` **非类型化**，与门控标准 4 冲突；替身须模拟 langchain 语义。
- **Decision**: **Option B**。AC-06-05 / AC-14-05 / REQ-NFR-IB-14 三项硬约束共性指向「必须有可替换、可替身的存储端口」。端口保持窄（**11 方法**（R1 更正：含 `flush()`），见 `module_design.md` **IFC-IB-100~110**，**以 `module_design.md` 为权威**），`scope` **必填**；高级能力经**显式扩展方法**渐进暴露（扩展方法须声明「不支持」语义而非静默失败）。集成：官方 `qdrant-client`，默认 gRPC `:6334`，REST `:6333` 作回退与健康检查；连接参数全走配置与环境变量；**维度不硬编码**，由 `CollectionSpec.dim` 声明。
- **Consequences**: 正向—AC-06-05 可自动化验证；AC-14-05 离线可测；类型化满足门控标准 4；内存替身可与 Qdrant 结果互校。负向—映射层字段新增需两处同步（以端口一致性测试 + `PointPayload.schema_version` 约束）；未来混合检索（OQ-IB-05）须扩展端口，属**已知且被接受**的演进成本；HNSW 调优参数收敛进 `CollectionSpec`，牺牲直连 SDK 的灵活性。

**ADR-01-R1 更正（框架切换复核：经检查，不受框架切换影响）**

- **更正项（契约编号一致性）**：`VectorStore` 端口方法数统一为 **11**（含 `flush()`：IFC-IB-100 ~ **IFC-IB-110**）。1.0.0 的 `architecture_design.md` 曾记为「10 方法 / IFC-IB-100~109」，与 `module_design.md` §2.2 不一致；**R1 以 `module_design.md` 为权威**统一，本文件同步更正。
- **不变项**：端口窄接口策略、`scope` **必填无默认值**、`QdrantVectorStore` / `InMemoryVectorStore` 双适配器与**端口一致性测试**、`CollectionSpec.dim` 不硬编码维度、高级能力经**显式扩展方法**渐进暴露（声明「不支持」而非静默失败）—— 全部不变。
- **框架切换复核**：该端口位于 **L2 适配器层（MOD-IB-10）**，仅依赖 MOD-IB-01/02/04，**不接触任何 Web 框架** → **经检查，不受框架切换影响**。

### ADR-02 embedding 服务部署形态与 CPU 推理策略

- **Status**: Accepted（**形态可逆**，见 Decision）
- **Context**: REQ-FUNC-IB-15 要求以开源本地 embedding（DR-02：bge-m3、稠密、余弦）替代云端，且**须同时支持批量（入库冷路径）与单条（查询热路径），二者可配置不同超时与重试**；AC-IB-07-03 对该点直接设验收。REQ-NFR-IB-03（检索性能）/IB-10（CPU-only 可运行、依赖须目标机真机验证）/IB-14（替身可替换）。算力假设 CPU-only + bge-m3 CPU 模式（DR-05），硬件规格 [TBD-T13]。
- **Options**:
  - **A 进程内加载**：优—零网络跳数、无额外服务与端口、离线测试直接注入 `FakeEmbedder`、组件最少。缺—模型内存被**每个 worker 复制**；加载耗时拖慢启动；推理与 Web 请求争抢 CPU（无资源隔离）；模型升级须重启 Web；与 onnxruntime（OCR）同进程内存叠加 [TBD-T4']。
  - **B 独立常驻服务（本基座自带轻量 HTTP 服务，systemd 管）** ← **选定**：优—Web 可多 worker（降低 CPU 争用，REQ-NFR-IB-03）；模型加载/预热与 Web 启动解耦；**双路径纪律有单一落点**（同一 HTTP 契约、两个客户端实例：冷路径长超时+多重试，热路径短超时+少重试，与 AC-IB-07-03 一一对应）；可独立限流、健康检查、观测（AC-IB-13-02）。缺—多一个服务与端口；每请求一次本地回环往返；不可达路径须完整实现（由 REQ-FUNC-IB-21 覆盖，非净增）；CPU 延迟未实测 [TBD-T1~T4]。
  - **C 第三方推理服务器（Ollama / TEI / vLLM）**：优—成熟、批处理与并发调度现成、可选 GPU。缺—重量级额外依赖与运维面；DR-03 禁 Docker 下安装摩擦显著；对 bge-m3 的支持须逐版本核实；本基座只需**一个模型一条稠密路径**，收益与成本不匹配。**已评估未采纳**。
- **Decision**: **Option B**，实现为本基座**自带**的轻量 HTTP 服务（同仓库、独立 systemd 单元 `ib-embed`），不引入 Option C。理由：① AC-IB-07-03 的双路径超时纪律，落在「同一 HTTP 契约的两个客户端实例」上最直接、最可测；Option A 下两路径仅是同对象两方法，超时语义需自建且与 Web 请求超时混在一起。② DR-04 已确认 v1 不承载本地 LLM，故目标机 CPU 预算只需承载 embedding + OCR，独立服务可精确设 CPU/内存边界而不与 Web 争抢。③ Web 多 worker 是降低 CPU 争用的直接手段。
  - **形态可逆（关键性质）**：端口 `Embedder` 使 Option A 仍是合法实现（`InProcessBgeM3Embedder`）。**若 [TBD-T1/T3] 显示服务开销不可接受，可切回进程内而不改任何上层模块**——切换成本 = 换一个适配器类 + 改一行装配配置。这是为对冲「CPU 延迟未实测」而刻意保留的可逆性。
  - **CPU 推理策略**（适配器内部，全部可配置）：模型**单例常驻** + 启动期 `warmup()`（是否后台预热由 [TBD-T3] 决定）；冷路径**批处理**（默认批量值须由 [TBD-T2] 校准，量级参考 FreeArk `BATCH_SIZE=20` 的思路）；热路径**单条 + 短超时 + 不重试**（超时即降级，AC-IB-14-01）；**并发上限 + 有界队列**，超限请求**快速降级而非无限排队**（排队会把「慢」放大成「全链路超时」，违反有界延迟原则）；**推理线程数受控**，避免与 Qdrant/worker/OCR 抢核（上限 [TBD-T7]）。
  - **GPU 可选**：端口不暴露设备概念；「是否用 GPU」是适配器内部运行参数，上层无感，满足 REQ-NFR-IB-10 的「有 GPU 时须可借助加速」。
- **Consequences**: 正向—双路径纪律可测；Web 多 worker 可行；模型升级不影响 Web；embedding 故障可仅凭日志定位；换模型（含换尺寸，AC-IB-07-05）只改配置与适配器。负向—多一个服务与端口；一次本地回环往返（[ESTIMATE] 亚毫秒量级，**不作数值承诺**，由 [TBD-T1] 一并实测）；降级路径须完整实现与测试；**若 [TBD-T1/T2] 实测不可接受，按 AC-IB-07-05 需重选模型尺寸，该变更回溯 DR-02（用户已拍板）→ 必须由 PM/用户裁决，架构层不自行改选型。**

**ADR-02-R1 复核（框架切换）**：**经检查，不受框架切换影响**。

- 决策客体（embedding 服务形态）位于 **L2 适配器层（MOD-IB-09）**，经 `Embedder` 端口隔离；`ib-embed` 为**独立 systemd 单元**，不随 Web 框架变化。
- 不变项：冷路径（批量 / 长超时 / 多重试）与热路径（单条 / 短超时 / 不重试）**双路径纪律**、模型单例常驻 + `warmup()`、并发上限 + 有界队列（超限**快速降级**）、推理线程数受控、**形态可逆**（可切回进程内 `InProcessBgeM3Embedder`）、可选 GPU 对上层无感 —— 全部不变。
- 与 Web 层的唯一关联是「Web 多 worker」这一**前提**（R1 下由 Waitress/Gunicorn 的 worker/线程配置承载，见 ADR-03-R1 与 [TBD-T15]），不改变本 ADR 的任何决策。

**ADR-02-R2 附注（L-03 补交：`ib-embed` 的模块归属与契约单一落点）**

- **归属成立，且不改变本 ADR 的任何决策**：ADR-02 Option B 选定「本基座**自带**的轻量 HTTP 服务 + 独立 systemd 单元」。L-03 指出该服务此前**只有 systemd 单元与客户端、缺服务端模块归属与完整契约** —— R2 补上 **MOD-IB-26**（`module_design.md` §1 / §3）与**单列契约** `docs/ib_embed_service_contract.md`（IFC-IB-266~274）。**Options / Decision / Consequences 一字未改**，本条只是把既定决策的**落点补齐并写实**：从「有一个单元文件」升级为「有一个有归属、有契约、可被测试与门控的模块」。
- **冷/热双路径的单一落点仍成立，且落点在客户端（写成可测试口径）**：服务端**无状态、不区分冷热**；「冷路径（批量 / 长超时 / 多重试）vs 热路径（单条 / 短超时 / 少重试）」由**同一 HTTP 契约的两个客户端实例**承载（IFC-IB-273）。**服务端不得**为「让冷路径更成功」引入无界队列（那会把热路径一起拖死，违反有界延迟原则）；**服务端必须**显式配置并发与队列，并在超限时快速失败、回显 `retry_after_s`，同时以 `/healthz` 暴露 `queue_depth` / `inflight` 使降级可观测（AC-IB-13-02）。
- **形态可逆仍成立，且值域显式化**：`IB_EMBED_BACKEND ∈ {http, inproc, fake}`（**键名与默认值 `http` 不变**，仅**扩展值域**）。`inproc` 实现 `InProcessBgeM3Embedder` **位于 MOD-IB-09 之内**（**不 import MOD-IB-26**），故「切回进程内不改任何上层模块」这句话在 R2 之后仍是**类型可验证**的（见 `module_design.md` §4.1 / §4.2）。默认保持 `http` 的理由不变：进程内形态的模型内存 × worker 数风险（Option A 的缺点原样成立）与「与 onnxruntime（OCR）同进程」的叠加峰值 [TBD-T4']。
- **错误码语义映射不变式（R2 新增，随附注登记）**：`4xx / 409 = 「重试无用」`（配置或请求问题），`5xx = 「重试可能有用」`（暂时故障）。**这是客户端「4xx 不重试」实现（`if exc.code < 500: break`）能够成立的前提**：不得把暂时性故障放进 4xx；服务端也不得引入该分类之外的失败表达（例如用 `200` + 部分向量表示失败 —— 客户端在长度不符时会直接判为依赖不可用）。
- **单一落点纪律**：MOD-IB-26 的契约正文只在 `docs/ib_embed_service_contract.md`；`module_design.md` §3 是**摘要视图**，冲突时以契约文件为准并须回写摘要。

### ADR-03 部署形态（systemd 裸装编排；Qdrant 裸装安装方式）

- **Status**: Accepted（部署形态 **[锁定]** DR-03；Qdrant 安装方式为本 ADR 的实质决策）
- **Context**: REQ-FUNC-IB-22 要求以操作系统级服务单元定义常驻进程、支持开机自启与失败重启、配置与凭据经环境变量注入、提供配置模板、关键事件写结构化日志。**部署形态由 DR-03 锁定：禁 Docker、全物理机直部署、各组件（含 Qdrant 与 embedding）一律裸装、不做容器/非容器双路径。** 目标机 Ubuntu（C-IB-03；CPU 架构 [ARCH-ASSUMPTION-A4]）；凭据纪律 REQ-NFR-IB-07 / C-IB-02；最小权限 C-IB-08；依赖须目标机真机验证 AC-IB-12-04。
- **Options**:
  - **形态-A 全裸装（systemd 直管全部组件）** ← **[锁定] 用户选定**：优—与既有无容器运维心智一致（服务重启 + 配置变更即可）；无容器运行时开销；依赖直接可见、排障路径短；无镜像仓库/网络依赖。缺—依赖版本隔离靠 venv 手工保证；跨项目复用有环境污染风险，需纪律约束；「可复现交付物」弱于容器。
  - **形态-B Docker Compose 全容器化** — **已评估未采纳**（与 DR-03 冲突）。
  - **形态-C 折中（基座裸装 + 向量库可选容器）** — **已评估未采纳**（用户明确选择不维护双路径）。
  - **Qdrant 安装方式（本 ADR 实质决策）**：
    - **Q1 官方 `.deb` + 自建 systemd 单元** ← **选定**：优—官方每 release 提供 `.deb`（同时布好二进制与 `/etc/qdrant/config.yaml` 示例）；`apt install ./x.deb` 即完成，无需编译；与 Ubuntu 包管理一致。缺—**官方 `.deb` 不安装 systemd 单元，也不创建 snapshots 目录**，两者须部署方自建，否则首次启动因 snapshots 临时目录创建失败而 panic（必列检查项）。
    - **Q2 官方预编译二进制 tarball + 自建单元**：优—不经包管理器，可精确指定版本与安装路径；无 `.deb` 的 Ubuntu codename 依赖 [TBD-T14]。缺—手工步骤多于 Q1；升级须手工替换二进制。
    - **Q3 源码 `cargo build --release`**：优—精确控版、可针对特定架构编译。缺—需 Rust 与 clang/cmake/protoc 构建依赖；构建耗时不可控；产出物一致性自负。**保留为 aarch64 且无官方产物时的回退路径**。
    - **Q4 第三方 apt 源** — **已评估未采纳**（第三方仓库信任依赖 + 版本滞后，与 AC-IB-12-04「真装真验证」的可控性诉求不符）。
- **Decision**: **形态-A（锁定）+ Q1**。Qdrant 以官方 `.deb` 安装，并**必须补齐三项官方产物不含的内容**（部署检查清单强制项）：① 专用**非特权**系统用户（`--system --shell /usr/sbin/nologin`）以满足 C-IB-08；② `/var/lib/qdrant/{storage,snapshots}` 并 `chown` 给该用户（snapshots 缺失会 panic）；③ `/etc/systemd/system/qdrant.service`：`User=qdrant`、`WorkingDirectory=/var/lib/qdrant`、`ExecStart=/usr/bin/qdrant --config-path /etc/qdrant/config.yaml`、`Restart=on-failure`、`LimitNOFILE=65536`，且 `config.yaml` 一律绝对路径。

- **服务清单（v1 四个 systemd 单元）**

  | 单元 | 职责 | 依赖 | 备注 |
  |------|------|------|------|
  | `qdrant` | 向量存储与相似度检索 | 无 | 独立失败域 |
  | `ib-embed` | bge-m3 推理服务（`/embed`、`/healthz`） | 无 | 模型常驻；显式 CPU/内存边界 |
  | `ib-web` | HTTP API + SSE 流式问答 + 静态前端 | qdrant、ib-embed | **R1：以 Waitress（主选）/ Gunicorn（备选）WSGI 启动 Django 应用**；可多 worker / 多线程（ADR-02 前提）；**SSE 长连接占用 worker/线程槽位**，容量见 [TBD-T15]，池满**快速失败 503** |
  | `ib-worker` | 异步入库 / 删除重放 / 索引重建（ADR-10） | qdrant、ib-embed | 并发度与租约可配 |

- **配置与凭据**：每单元一个 `EnvironmentFile`（`.env`，不入 git）；仓库仅含 `.env.example`（无真实值）。**启动期校验必填项**，缺失即给出「指明配置项名、不回显其值」的可读错误并以非零码退出（AC-IB-12-03）。日志级别经环境变量配置（AC-IB-13-03）。
- **健康检查**：`ib-web` 暴露 `/healthz`（自身）与 `/healthz/deps`（逐依赖探测 qdrant / ib-embed / LLM 端点可达性，并输出**数据外发边界声明**），供 systemd 与运维使用（REQ-NFR-IB-06；AC-IB-13-02；AC-IB-12-05）。
- **Consequences**: 正向—部署路径与既有运维心智一致；零容器开销；四单元清单可被 AC-IB-12-01 逐条核对；非特权用户满足 C-IB-08。负向—`.deb` 与 unit 的手工拼装带来三类「静默陷阱」（无 unit / 无 snapshots 目录 / `LimitNOFILE` 过低），已列为强制检查项；Python 依赖隔离完全依赖 venv 纪律（v1 采取**每进程一个 venv**）；跨项目复用同机时共用同一组进程（单实例多项目，DR-06），故**隔离完全落在数据层**（§3）。

**ADR-03-R1 修订（框架切换复核：受影响）**

- **载体变更**：`ib-web` 由「FastAPI + Uvicorn（ASGI）」改为 **Django + Waitress（主选）/ Gunicorn（备选）**，即**同步 WSGI** 承载。理由：全链路为同步调用（同步台账 SQL、同步 `ib-embed` HTTP 客户端、同步 Qdrant 客户端、langgraph **同步**流），WSGI 与之同构，且组成面更小（无需 ASGI 运行时与 `sync_to_async` 桥接纪律）。
- **SSE 下的 worker/线程占用（关键代价，须显式声明）**：WSGI 为「一请求一 worker（进程或线程）」模型，**每个 SSE 长连接会独占一个 worker/线程直到流结束**；因此**同时在线 SSE 连接数受 worker/线程池总容量硬约束**。此为选定 ADR-11-R1 Option A 的**已知代价**，须以「有界 + 可观测」方式管理，不得默认无限容量。
- **容量规划与 fail-closed**：worker 数 / 线程数**显式配置**（不依赖默认值）；并发容量按 **[TBD-T15]** 在目标机实测后设定；池满时**不排队**，一律**快速失败 `503` + 可读文案**（fail-closed；排队会把「慢」放大为「全链路超时」，与 §7.3 一致）。SSE 响应头须含 `X-Accel-Buffering: no` / `Cache-Control: no-cache`（前置反向代理须禁用响应缓冲）。
- **升级路径（默认不启用）**：若 [TBD-T15] 实测显示同步 worker 池容量不足以满足并发需求，启用 **ADR-11-R1 的 Option B**（Django 异步视图 + Gunicorn `uvicorn.workers.UvicornWorker`，**仍不含 Channels / Redis**）。
- **不变项（逐条重申）**：四个 systemd 单元清单（`qdrant` / `ib-embed` / `ib-web` / `ib-worker`）、每单元一个 `EnvironmentFile`（凭据**经环境变量注入**）、启动期必填校验（指明键名、不回显值、非零码退出）、`/healthz` 与 `/healthz/deps`（含**数据外发边界声明**）、专用非特权用户、Qdrant 安装三项强制补齐（用户 / `snapshots` 目录 / unit 文件）—— **全部不受框架切换影响**。
- **[TBD-T15]**：**SSE 并发上限**（单实例可同时承载的 SSE 连接数 + 对应 worker/线程配置）—— **未实测，部署前必须在目标机测定**；条目见 §9，触发判据见 ADR-11-R1。

### ADR-04 多项目隔离实现（collection-per-project vs 单 collection + payload filter）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-23 要求同实例承载多项目/多知识库且彼此隔离，**隔离须贯穿「上传 → 存储 → 检索 → 路由上下文」全链路**，删除须限定在所属项目内；**拓扑由 DR-06 锁定：单实例多项目，以 Qdrant collection + 项目级配置实现隔离**。验收锚点：AC-IB-06-02（针对知识库 A 检索仅返回 A）、AC-IB-11-02（项目 A 用户检索仅含 A 数据；B 的台账/切分块/向量均不可见）、AC-IB-06-04（按文档删除不误删）、AC-IB-03-03（删除后不再命中）。另受 REQ-FUNC-IB-24 隐含约束：**若不同项目使用不同 embedding 模型/维度，存储须支持维度异构**。
- **Options**:
  - **A collection-per-project（每项目一 collection；知识库维度用 payload filter）** ← **选定**：优—**跨项目泄漏在存储层不可达**（硬隔离，不依赖「每处查询都写对 filter」）；删除项目 = `delete_by_collection`（O(1)，无跨项目误删面）；每 collection 可独立声明 `dim` 与距离度量 → **支持项目间异构模型/维度并存**，是 REQ-FUNC-IB-24 的前提；collection 数与项目数同阶（项目数 ≪ 知识库数）。缺—项目内**知识库间隔离退化为软隔离**（依赖 filter 正确性，见 FM-1）；项目数多时每 collection 的段与索引开销叠加（千级量级可忽略，须核验 [TBD-T5]）；跨项目联邦检索不可行（非本期需求）。
  - **B 单 collection + payload filter**：优—collection 数恒为 1，资源最省；跨项目检索天然可行。缺—**隔离仅在查询语句正确性上成立（软隔离）**，一处漏 filter 即静默泄漏；按项目删除有误删面；**单一 collection 固定矢量维度**，与 REQ-FUNC-IB-24 及多项目异构模型诉求**直接冲突**；AC-IB-11-02 的「B 的向量不可见」只能靠断言而非结构。
  - **C 实例-per-project**：优—物理隔离最强、配置完全独立。缺—与 DR-06 **直接冲突**；资源重复占用；运维对象随项目数线性增长。**已评估未采纳**。
  - **D collection-per-(project, kb)**：优—知识库级也成硬隔离，AC-IB-06-02 在存储层直接成立。缺—collection 数 = 项目数 × 知识库数，Qdrant 每 collection 固定开销随知识库数放大；跨知识库联合检索须多次查询归并；语料被切碎到大量小 collection 削弱 HNSW 效率。**保留为可升级路径**，v1 不采纳。
- **Decision**: **Option A**。理由：① DR-06 明确「以 Qdrant collection + 项目级配置实现隔离」，A 是其直接实现；② A 使 AC-IB-11-02 的「跨项目不可见」成为**结构性事实**而非断言式事实；B 把安全性寄托在「每处查询都写对 filter」上——在「不得泄漏」被反复强调的语境下，A 的失效模式更可控；③ A 允许**每 collection 独立声明维度与模型**，这是 REQ-FUNC-IB-24 与 IB-23 同时成立的必要条件（B 无法满足）。
  - **defense-in-depth（选定 A 后仍施加）**：`PointPayload` **冗余写入** `project_id` 与 `kb_id`，且 `query` / `delete_by_doc` 的 filter **始终**包含 `project_id`。目的：使「collection 名解析错误」这类**配置级错误**不演变为泄漏，而变成「查不到」（fail-closed 而非 fail-open）。
  - **知识库维度用 payload filter —— 显式取舍**：`Scope = {project_id: str, kb_ids: tuple[str,...] | None}`，`kb_ids=None` 表示项目内全部知识库。该取舍**已识别为软隔离面**，防护见 §3.3 FM-1。
  - **可升级性（对冲 [ARCH-ASSUMPTION-A2]）**：collection 名由**单一入口** `CollectionResolver.resolve(scope) -> str` 解析（`module_design.md` IFC-IB-098）。若 PM 判定「知识库之间也须硬隔离」，改 A→D 的成本仅限**改解析规则 + 改配置结构**，上层模块（管线/检索/编排）**零改动**。这是把可能变化的「隔离粒度」收敛到单一函数的设计。
  - **命名**：`ib_<project_id>_v<collection_version>`。`project_id` 启动期校验 `^[a-z0-9][a-z0-9_-]{0,39}$`（防注入与路径穿越）；`collection_version` 语义见 ADR-05。
- **Consequences**: 正向—AC-IB-11-02 / AC-IB-06-02（跨项目部分）在存储层结构性成立；项目级删除 O(1) 且无误删面；支持项目间异构模型/维度；单实例多项目资源开销可接受（[TBD-T5] 核验）。负向—**项目内知识库级隔离为软隔离**（已识别并列入 §3.3 FM-1）；项目数增长带来 collection 数增长，须在 [TBD-T5] 核验内存与查询延迟；跨知识库联合检索需按 kb 多次查询后归并（由检索服务统一处理，对上层透明）。

**ADR-04-R1 修订（ARCH-ASSUMPTION-A2 已关闭；框架切换复核：经检查，不受框架切换影响）**

- **A2 状态变更（R1）**：~~需 PM 确认~~ → **已确认**。PM 裁定 **隔离粒度 = 项目级硬隔离（collection-per-project）+ 知识库级软隔离（payload filter）**，即**维持 1.0.0 选定的 Option A，不升级为 Option D**（`CollectionResolver` 的升级能力仍保留为可选路径，但**不启用**）。
- **设计不变项**：`CollectionResolver.resolve(scope, project) -> str`（`module_design.md` IFC-IB-098）仍是**唯一** collection 名解析入口；`Scope` **必填无默认值**；`query` / `delete_by_doc` 的 filter **恒含** `project_id`；`PointPayload` 冗余写入 `project_id` / `kb_id` 的 defense-in-depth 保留；命名 `ib_<project_id>_v<collection_version>` 与启动期前缀断言保留。软隔离面的防护见 §3.3 FM-1。
- **框架切换复核**：隔离机制全部位于**契约层（MOD-IB-01，`Scope` 必填）**、**适配器层（MOD-IB-10，filter 组装）**与**检索服务（MOD-IB-15）**，与 Web 框架无关 → **经检查，不受框架切换影响**。
- **残留风险（不变）**：知识库级漏 filter 即泄漏（FM-1）；防护为「类型系统 + 归属断言 + 单入口解析 + 启动期断言」四重。若未来判定须硬隔离，成本仍被收敛在「改解析规则 + 改配置结构」，上层零改动。

**ADR-04-R2 复核**：**R2 不受影响** —— M-02 的图片端点（IFC-IB-283）与关联表（IFC-IB-279）**一律带 `scope`** 并复用归属断言；隔离粒度、`Scope` 必填与 `CollectionResolver` 单入口**均未动**（R2 是 ADR-04 的应用，不是修改）。

### ADR-05 原始文件持久化与索引重建机制

- **Status**: Accepted（**R1：OQ-IB-01 已确认 = 原文件保留（ON）**；原「开关默认值待 OQ-IB-01 一行确认」已关闭）
- **Context**: REQ-FUNC-IB-24 要求 embedding 模型/维度变更后一键重建且**不必重新上传**；AC-IB-16-01（无需重传）/16-02（中断后可重跑且幂等）/16-03（重建期间行为明确）/16-04（单文档失败隔离）。重建的**前置**是原始文件仍可得 → OQ-IB-01。REQ-NFR-IB-13（可靠性/降级）。DR-07 锁定「须支持索引重建」。
- **Options**:
  - **A 不持久化原文件，重建时要求重新上传**：优—零存储、无隐私面。缺—**AC-IB-16-01 直接不成立**；用户被迫重传；与 DR-07 的实用价值冲突。**已评估未采纳**。
  - **B 持久化原始文件（内容寻址 sha256，落本地文件系统）** ← **选定**：优—AC-16-01 成立；重试/重建可用；sha256 内容寻址天然去重且可校验完整性；删除可与台账联动。缺—磁盘占用随语料增长；需访问控制（C-IB-08）与删除联动（AC-IB-02-04 删除须连同原文件）。
  - **C 对象存储（MinIO / S3）**：优—可扩展、可跨机。缺—新增组件与凭据面，违反 DR-03 / C-IB-08 的最小组成面；DR-05 量级下收益为负。**已评估未采纳**。
- **Decision**: **Option B**。布局 `<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`（项目/知识库/文档三级目录使删除与隔离都可按前缀处理）。开关 `IB_BLOB_STORE_ENABLED`（**默认开启**，因 DR-07 是用户已拍板需求）；关闭时**启动期给出可读告警**并明确降级语义（重试需重传、重建不可用、相关 API 返回明确错误而非半可用），**不是运行期崩溃**。
  - **幂等与重建设计**：
    - `collection_version = fingerprint(embedding_model_id, dim, chunk_size, chunk_overlap, parser_version, normalizer_version, schema_version)` 取前 8 位十六进制（**纯函数**，跨进程稳定）。
    - 重建流程：建新 collection `ib_<pid>_v<newver>` → **逐文档 delete-then-write（以 doc_id 为幂等键）** → 全部成功后台账 `active_collection_version` 切到新值 → 旧 collection 由运维确认后删除（保留回滚窗口）。
    - **不做双写、不做混合读**：读路径只读 `active_collection_version` 指向的**单一** collection，避免同一次检索混到两个版本。
    - **断点续跑**：台账记录 `target_collection_version` 与每文档 `indexed_collection_version`，重跑跳过已是目标版本的文档；`pending_rebuild` 标记使重建可中断可恢复（AC-16-02）。
    - **重建期间行为**（AC-16-03）：**读继续读旧 collection（服务可用，只是内容非最新）**；新写入库的目标 collection 由配置明确选择并在响应中回显，不出现「写一半读一半」。
    - **单文档失败隔离**（AC-16-04）：失败仅置该文档 `failed` 并记原因，不阻塞其余文档，**不切换 active 版本**（保证「切换即完整」）。
- **Consequences**: 正向—AC-16-01~04 均可满足；重建可中断可续跑；版本切换原子。负向—磁盘占用与访问控制面增加；旧 collection 需人工确认删除意味着短期内双份存储；`fingerprint` 因子一旦漏项会造成「该重建却没重建」的静默错误（以 `PointPayload.schema_version` + 启动期一致性断言缓解）。

**ADR-05-R1 修订（框架切换复核：经检查，不受框架切换影响）**

- **OQ-IB-01 已确认（R1）**：原始文件**保留（ON）** —— `IB_BLOB_STORE_ENABLED` **默认开启**，因 DR-07 索引重建以其为前置（关闭则 AC-IB-16-01 不成立）。开关的降级语义**不变**：关闭时**启动期给出可读告警**并明确降级（重试需重传、重建不可用、相关 API 返回明确错误），**不是运行期崩溃**。
- **设计不变项**：sha256 **内容寻址**布局 `<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`；`collection_version = fingerprint(...)`（**纯函数**，跨进程稳定）；重建流程 = 建新 collection → **逐文档 delete-then-write（以 doc_id 为幂等键）** → 全部成功后台账**原子切换** `active_collection_version` → 旧 collection 保留回滚窗口；**不做双写、不做混合读**；断点续跑 / 重建期间行为 / 单文档失败隔离（AC-IB-16-01~04）均不变。
- **框架切换复核**：blob 落**本地文件系统（MOD-IB-12）**，版本切换是**台账（MOD-IB-11）上的一次原子写**，二者均不经 Web 框架、不经 Django ORM（见 ADR-07-R1） → **经检查，不受框架切换影响**。

### ADR-06 PDF 解析库的许可合规选型

- **Status**: Accepted（**推翻 FreeArk 现状实现**）
- **Context**: REQ-FUNC-IB-10（格式解析）/IB-11（扫描件 OCR，需**渲染**能力，AC-IB-04-06 要求扫描页整页栅格化后 OCR）；**REQ-NFR-IB-12 要求开源协议友好，并明确禁止沿用「内部平台合规」豁免**。FreeArk 现状使用 PyMuPDF，其代码注释自述「AGPL v3，内部平台合规」。AGPL v3 具传染性：对外提供服务即触发源码提供义务，与「可复用基础架构」目标直接冲突。
- **Options**:
  - **A 保留 PyMuPDF**：优—能力最全（文本 + 渲染 + 图像提取）、CPU 最快、FreeArk 三路径逻辑与 XObject 处理可直接移植。缺—**AGPL v3**。三条合规前置条件：① 购买 Artifex 商业授权；② 整个基座以 AGPL 开源（与内部多项目复用目标冲突）；③ 严格内部使用且不与外部网络交互（与 REQ-FUNC-IB-23 多项目/多使用方目标冲突）。**前置①成本不可接受，②与项目目标冲突，③与需求冲突 → 全部不满足。**
  - **B `pypdf`（文本主）+ `pdfminer.six`（回退）+ `pdfplumber`（可选表格）+ `pypdfium2`（渲染）** ← **选定**：许可分别 BSD-3 / MIT / MIT / BSD-3 OR Apache-2.0，全部宽松，满足 REQ-NFR-IB-12。
  - **C Poppler CLI（`pdftotext` / `pdftoppm`）**：优—成熟、CJK 表现好。缺—**GPL-2.0**，仍属 copyleft；「子进程隔离是否构成衍生作品」法律上存在争议，**不能作为合规确定性来源**。**已评估未采纳**。
  - **D `pypdfium2` 同时承担文本与渲染**：优—单库双能力、PDFium 内核与 Chrome 同源、文本质量好。缺—CJK 复杂版面（分栏/表格）的提取控制不如 pdfminer.six 精细。**保留为渲染的唯一实现 + 文本提取的备选**。
- **Decision**: **Option B**。① 文本提取主用 `pypdf`；② 空结果/异常/CJK 版面疑难时回退 `pdfminer.six`；③ 表格密集文档可选用 `pdfplumber`（可选依赖，缺失则自动降级为 pdfminer.six）；④ 扫描页栅格化由 `pypdfium2` 承担——**前述三个纯 Python 库均不具备渲染能力**，故渲染必须另选，`pypdfium2` 是在许可友好前提下唯一成熟的选择。**明确声明：本决策改变 FreeArk 既有实现，其三路径解析逻辑须按新库重写（架构结论；实现属 GROUP_C）。**
- **Consequences**: 正向—许可全部宽松，可对外复用；每类问题都有明确替代路径。[ESTIMATE] 纯 Python 文本提取较 C 内核实现慢一个数量级、抽取准确率亦有差异（社区基准差异明显，**本文件不作数值承诺**）→ 入库为异步冷路径可接受；须以 [TBD-T8] 在目标机对中文语料实测后再定主/回退顺序。
  - 负向—复杂版面（多栏、表格）抽取质量可能下降，须以 [TBD-T8] 验证；XObject 滤镜覆盖（JPXDecode / CCITTFaxDecode）须核验 [TBD-T9]；**若 [TBD-T8] 判定 pypdf 中文质量不可接受，可将回退顺序改为 pdfminer.six 优先——端口不变，架构无需变更。**
  - **合规留痕**：不采纳「内部平台合规」口径（REQ-NFR-IB-12 明令禁止）；三条 AGPL 前置条件已逐条列明且均不满足或与需求冲突，故 Option A 不可取。完整许可台账见 `tech_stack.md`。

**ADR-06-R1 复核（框架切换）**：**经检查，不受框架切换影响**。

- 决策客体为**纯库选型**（`pypdf` / `pdfminer.six` / `pdfplumber` / `pypdfium2`），位于 **L1 解析层（MOD-IB-05）与 L2 适配器层（MOD-IB-08）**，经 `DocumentParser` / `PageRenderer` 端口隔离，与 HTTP 载体无关。
- 不变项：文本三路径（文本层 / 内嵌图像 OCR / 扫描页栅格化 + OCR）、主 / 回退顺序可配置（由 [TBD-T8] 决定）、**三纯 Python 库均不能渲染故渲染必须另选 `pypdfium2`**、许可合规留痕（**不采纳 PyMuPDF / AGPL-3.0，且明确撤除「内部平台合规」口径**）—— 全部不变。

**ADR-06-R2 复核**：**R2 不受影响** —— R2 **未引入任何新 PDF 库**；M-02 只**消费**解析已产出的页面图关联信息（`ParsedChunk.page_or_section` / `locator` / `source_kind` 均为既有字段）。**注（R2 新发现，见 [TBD-T18]）**：OCR 链路的 `onnxruntime` 与 R2 的 embedding 推理运行时**同受「目标机 CPU 指令集基线」风险**约束，但该风险**不改变**本 ADR 的库选型结论（缓解与判定见 `tech_stack.md` §5.2）。

### ADR-07 元数据 / 台账存储

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-04（上传后异步状态可见）/IB-08（删除）/IB-16（**须与向量库保持一致**）/IB-24（重建）；REQ-NFR-IB-11（可替换）/IB-13（可靠性）。台账须承载：项目/知识库/文档/切分块元数据、入库状态机、重建标记、任务租约（ADR-10）。
- **Options**:
  - **A 关系库（SQLite，WAL 模式）+ `LedgerRepository` 端口** ← **选定**：状态机、列表分页、聚合计数、按 scope 过滤都是关系模型的强项；单机零组件。
  - **B 全部元数据放 Qdrant payload**：优—单一存储、无一致性跨库问题。缺—**状态机 / 文档列表 / 分页 / 聚合是向量库反模式**；台账可用性被耦合到向量库（向量库故障即无法查文档列表）；删除文档须先全量扫描点。**已评估未采纳**。
  - **C PostgreSQL / MySQL**：优—并发写强、生态成熟。缺—新增组件与凭据面（违反 DR-03 / C-IB-08）；DR-05 量级下 SQLite 足够。**保留为升级路径**（端口使其可换）。
  - **D 文档数据库（MongoDB）**：**SSPL 许可**与 REQ-NFR-IB-12 冲突。**已评估未采纳**。
- **Decision**: **Option A**。SQLite WAL（单写多读，匹配「单 worker 写 + 多 web 读」的并发形态），端口抽象使未来换 PG 只改适配器。
  - **一致性设计（REQ-FUNC-IB-16）**：
    - **写序**：删旧向量（按 doc_id）→ 写新向量 → 全部成功后才把台账置 `indexed`。因此「台账 `indexed`」是「向量已写入」的**充分条件**。
    - **反向不一致**（向量在而台账已删）：由 `ib-worker` 的**删除重放**任务按「台账无此 doc_id 但 collection 中存在」对账清理；删除接口先写台账删除标记再删向量，重放保证最终一致。
    - **查询路径只信任台账**判定可见性，向量库只负责相似度排序。
- **Consequences**: 正向—无需新组件；单机单文件即备份；状态机与分页是关系库强项。负向—SQLite 写并发受单写者约束（v1 单 worker 写路径 + 短事务可接受）；**须显式开启 WAL 与 `busy_timeout`**（否则出现 `database is locked`）；schema 迁移须**手写 scoped 迁移**（沿用 FreeArk 纪律，禁止全量自动产物）。

**ADR-07-R1 修订（框架切换复核：受影响 —— 显式排除 Django ORM）**

- **结论**：台账**不经 Django ORM**。**保留 `LedgerRepository` 端口 + 自管 SQL（stdlib `sqlite3`）** 的 1.0.0 设计**不变**。
- **为何必须显式排除**：① 若改由 Django ORM 承接，将连带引入 **Django 迁移机制（`makemigrations` 全量自动产物）**，与本项目「**手写 scoped 迁移、禁止全量自动产物**」纪律**直接冲突**（FreeArk 有迁移漂移前科）；② 会把台账 schema 的演进**绑死到 Web 框架的发布节奏**上，破坏 MOD-IB-11 作为 L3 独立模块的可复用性与可替换性（REQ-NFR-IB-11）。
- **不变项（逐条重申）**：① **WAL 模式 + `busy_timeout` 必开**（否则 `database is locked`）；② 认领用**条件 UPDATE**（`WHERE status='pending' AND lease_expires_at < now`）保证多 worker 不重复处理；③ **租约超时自动回收**（`reap_expired_leases`）；④ 写入 **delete-then-write** 幂等（ADR-05）；⑤ schema 走**手写 scoped 迁移**；⑥ 查询路径**只信任台账**判定可见性。
- **PG 升级路径保留**：端口语义不变，未来升级（如接 PostgreSQL）**仅替换适配器**（`SqliteLedgerRepository` → PG 实现），上层模块零改动。
- **配置与日志不接管**：配置仍由 `ConfigurationSource` 端口（MOD-IB-02）装载，不依赖 Django `settings`；日志仍以 MOD-IB-04 为单一落点，不依赖 Django `LOGGING` 作为唯一配置源（保持离线单测与跨项目复用能力）。

### ADR-08 LLM 端点抽象与数据外发边界

- **Status**: Accepted（DR-04 锁定：v1 保留云端 DeepSeek，端点可配置，**不做本地/云端双路径**）
- **Context**: REQ-FUNC-IB-18（多智能体问答）/IB-19（意图路由）/IB-21（流式输出）；REQ-NFR-IB-08（数据不出本地的**例外须显式声明**：提问文本 + 检索片段外发云端）/IB-07（凭据走环境变量）。AC-IB-12-05 要求外发行为在**配置层可追溯**。
- **Options**:
  - **A `LlmProvider` 端口 + `OpenAiCompatibleProvider`（DeepSeek）+ `FakeLlmProvider`** ← **选定**。
  - **B 在编排层直接调用 langchain `ChatOpenAI` 并硬编码参数**：缺—端点/密钥/温度散落各处；无法离线替身（AC-IB-15-04 不可达）；**外发边界无处声明**（AC-IB-12-05 不成立）。**已评估未采纳**。
  - **C v1 即同时支持本地 LLM（vLLM / Ollama）与云端**：与 DR-04 直接冲突（v1 不承载本地 LLM）；且显著增加目标机 CPU/内存压力（DR-05）。**已评估未采纳，保留为 v2 经同一端口接入的路径**——这正是端口的价值。
- **Decision**: **Option A**。v1 **仅装配一个 provider 实例**（拒绝隐式多端点）；路由分类（**temperature=0，确定性**，AC-IB-09-07）、专家作答、结果聚合三个角色在端口**内部**构造，provider 细节不外泄到编排层。
  - **数据外发边界（AC-IB-12-05）**：`describe_egress() -> {remote: bool, endpoint_host: str, data_categories: ["user_query", "retrieved_chunks"]}`；启动日志输出一次，`/healthz/deps` 可查。**显式声明：本系统会将用户提问文本与命中的检索片段发送至所配置的云端 LLM 端点（DR-04）。不外发：原始文件、未命中片段、台账、其他项目数据。**
  - **已知坑（FreeArk 经验，须在适配器内解决）**：`langchain-openai` 0.3.x 曾**丢弃 `reasoning_content`**（推理流被吞）且移除 `_convert_chunk_to_generation_chunk` 致**生产漂移** → 依赖须 pin `<0.3`；若 v1 需展示推理过程，须在 provider 内直读 SDK delta 字段而非依赖 langchain 透传 [TBD-T10]。
- **Consequences**: 正向—端点可配（可切自建 OpenAI 兼容端点）；离线替身可测；外发边界可追溯（合规留痕）。负向—云端为外部依赖，不可达时须降级（§7 / module_design §7 降级矩阵）；成本与限流不受本基座控制（属运维项）；`langchain-openai<0.3` 的 pin 是**显式技术债**（已记入 `tech_stack.md` 风险表）。

**ADR-08-R1 修订（框架切换复核：受影响，结论 = 无冲突）**

- **复核结论**：`LlmProvider` 端口与 **`langchain-openai`** 在 **Django（同步 WSGI 栈）** 下**无冲突**，1.0.0 设计**不变**。
- **理由**：① `LlmProvider` 实现位于 **L4 编排层（MOD-IB-20）** 且**被端口隔离**——不 import 任何 Web 框架，Web 框架切换无法触及；② langgraph / langchain 提供**同步**流式 API，与 ADR-11-R1 选定的**同步 WSGI + `StreamingHttpResponse`** 在并发模型上**同构**，**无需 `sync_to_async` 桥接**（这是相对「异步视图」的关键优势，也是 Option A 优于 Option B 的理由之一）；③ 端点 / 密钥 / 温度一律**环境变量注入**（MOD-IB-02），不经 Django `settings`；④ **沿用 `langchain-openai` pin `<0.3`**（0.3.x 移除 `_convert_chunk_to_generation_chunk` 致生产漂移，且丢弃 DeepSeek `reasoning_content`；见 `tech_stack.md` §3）。
- **不变项**：v1 **仅装配一个 provider 实例**（拒绝隐式多端点）；`build_router()`（`temperature=0`，确定性，AC-IB-09-07）/ `build_expert()` / `build_aggregator()` 三角色在端口**内部**构造；`describe_egress()` 外发边界声明（AC-IB-12-05）与「不外发：原始文件、未命中片段、台账、其他项目数据」的边界**不变**；是否需要直读 SDK delta 取 `reasoning_content` 仍以 [TBD-T10] 决定。

### ADR-09 编排骨架业务零依赖（依赖反转）

- **Status**: Accepted
- **Context**: REQ-NFR-IB-01（通用性/可复用：新项目核心代码改动 0 行）、AC-IB-11-06（**编排骨架不得包含业务依赖**）。FreeArk 已验证该性质可行：`langgraph_chat` 对 `api.*` 的依赖为零（`adapter.py` 除外），业务语义（人格文本、用户范围）由调用方构造后透传。同时 REQ-FUNC-IB-23 又要求「隔离贯穿路由上下文」——两条要求存在张力，本 ADR 即是其解法。
- **Options**:
  - **A 骨架内直接引用业务模块**：缺—新项目必须改骨架，与 REQ-NFR-IB-01 / AC-11-06 直接冲突。**已评估未采纳**（FreeArk 早期形态）。
  - **B 依赖反转（骨架只认端口与纯数据；业务语义由调用方注入）** ← **选定**。
  - **C 骨架不含任何上下文，隔离完全在仓储层**：优—最简单。缺—REQ-FUNC-IB-23「隔离贯穿路由上下文」在架构上无处落脚；工具与检索客户端的 scope 绑定被推迟到调用点，**漏传风险升高**。**已评估未采纳**。
- **Decision**: **Option B**，并采用**两段式上下文**（详见 §1.4）：机械段（`request_id` / `session_key` / `scope_token`）骨架透传但**不解释语义**；语义段（知识库范围）在**装配期**绑定进工具闭包与检索客户端，**骨架完全不可见**。**知识库范围刻意不作为骨架字段**——这样骨架无需理解隔离模型，而 REQ-FUNC-IB-23 仍成立。
- **Consequences**: 正向—新项目零改动（骨架可作模板直接复用）；骨架可独立单测（纯逻辑 + 替身）；隔离模型演进（A→D 升级）不触及骨架。负向—装配期闭包绑定使「scope 从哪来」位于骨架之外，需在组合根（MOD-IB-23）集中说明与断言；调试时上下文不如显式字段直观（以结构化日志的 `request_id` 关联缓解）。

**ADR-09-R1 复核（框架切换）**：**经检查，不受框架切换影响**。

- 决策客体（编排骨架业务零依赖 / 依赖反转）位于 **L4（MOD-IB-22）**，其反转载荷为「只认端口与纯数据；业务语义由调用方构造后透传」，与 HTTP 框架无关。
- 不变项：**两段式上下文**（机械段 `request_id` / `session_key` / `scope_token` 骨架透传但不解释语义；语义段知识库范围在**装配期**绑定进工具闭包与检索客户端，骨架完全不可见）、「知识库范围刻意不作为骨架字段」、scope 绑定发生在**组合根（MOD-IB-23）** —— 全部不变。
- 说明：流式**载体**（SSE / `StreamingHttpResponse`）属**外层传输**决策（ADR-11-R1），不改变骨架的事件契约；`StreamEvent` 的 `kind ∈ {reasoning, content, degraded, related_images, error, done}` 不变。

### ADR-10 异步入库执行形态与队列载体

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-04（上传后异步入库、状态可查）/IB-07（入库顺序与批量）/IB-24（重建属长任务）；AC-IB-02-04（删除与入库并发时**安全退出**）；REQ-NFR-IB-13（可靠性）/IB-14（可测）。FreeArk 现状用 `transaction.on_commit` 起 daemon 线程——**进程重启即在途文档永久停留 `parsing`**。
- **Options**:
  - **A 进程内 daemon 线程**：优—零组件。缺—**无持久性**（重启丢任务，文档永久卡住）；与 Web 生命周期耦合；无法限并发；失败可观测性差（AC-IB-13 不达标）。**已评估未采纳**（即 FreeArk 现状，本基座的明确改进点）。
  - **B 以台账表本身为队列**（`status` + `lease_owner` + `lease_expires_at`），独立 `ib-worker` systemd 单元轮询认领 ← **选定**：优—零新增组件；任务**持久**（重启不丢）；认领/心跳/超时可观测；可用台账同一事务保证状态与任务一致。
  - **C Redis / RabbitMQ 队列**：优—成熟的可见性超时与重试语义。缺—新增组件与凭据面（DR-03 / C-IB-08）；FreeArk 有 `channels_redis` 4.3.0 与 `redis-py` 8.0.0 不兼容、WS 收包超时的**前车之鉴**；DR-05 量级下收益为负。**已评估未采纳**。
- **Decision**: **Option B**。① 认领用**条件 UPDATE**（`WHERE status='pending' AND lease_expires_at < now`）保证多 worker 不重复处理；② **租约超时自动回收**（崩溃任务回到 `pending`）；③ 处理前**预检并发删除**（AC-IB-02-04：文档已被删除则直接结束并清理向量）；④ 写入 **delete-then-write** 幂等（ADR-05）。
- **Consequences**: 正向—无需新组件；任务持久；认领/心跳/超时可观测（AC-IB-13）。负向—轮询有空转（以可配间隔 + 退避缓解）；**租约时长与任务时长须匹配**——重建属长任务，须独立心跳续租，否则被误回收；**同一文档的入库与重建须互斥**（以租约 + 状态机约束，避免版本互踩）。

**ADR-10-R1 复核（框架切换）**：**经检查，不受框架切换影响**。

- 决策客体（以台账表本身为队列 + 独立 `ib-worker` systemd 单元轮询认领）**不经 Web 层**；任务的持久性、认领、心跳、超时可观测性均落在 L3 与独立进程。
- 不变项：**条件 UPDATE 认领**（多 worker 不重复处理）、**租约超时自动回收**、处理前**预检并发删除**（AC-IB-02-04 安全退出）、**delete-then-write 幂等**（ADR-05）、长任务独立心跳续租、入库与重建对同一文档**互斥** —— 全部不变。
- 与 R1 的关联仅为「`ib-web` 变为多 worker/多线程 WSGI」这一事实；但**队列正确性由台账的条件 UPDATE 保证**，与 `ib-web` 的 worker 模型无关，故本 ADR 不受影响。

### ADR-11 Web 层技术栈与流式通道（SSE vs WebSocket）

- **Status**: Accepted（**R1 全文重写**：结论由「FastAPI + Uvicorn」改为「Django（同步 WSGI）+ `StreamingHttpResponse` 原生 SSE」；本节末 **ADR-11-R1 修订节**给出 A/B/C 三方案重评估并**取代下方 1.0.0 的 Option / Decision 结论**）
- **Context**: REQ-FUNC-IB-09（Web 导入界面）/IB-17（问答入口）/IB-21（流式输出与会话生命周期）；REQ-NFR-IB-09（权限与访问控制，AC-IB-11-05：未授权返回 **401/403 而非静默**）；C-IB-03 目标机资源有限。
- **Options（1.0.0 原评估 —— 留痕；R1 结论见本节末修订节）**:
  - **A′ 1.0.0 选项 A：FastAPI + Uvicorn（ASGI）+ 独立 Vue 3 + Vite 前端，流式用 SSE（`text/event-stream`）** —— **R1 已撤销**（用户明确指定后端框架为 Django，非建议）。**留痕**：「SSE 而非 WebSocket」的反泄漏初衷由 R1 继承。
  - **B′ 1.0.0 选项 B：Django + DRF + Channels（WebSocket）** —— **R1 部分采纳 / 部分拒绝**：**Django + DRF 已采纳**（见修订节 Option A）；**Channels 及其 Redis channel layer 仍拒绝**（组成面 + 两个已知真实缺陷，见修订节 Option C）。
  - **C′ 1.0.0 选项 C：服务端渲染（Flask / FastAPI + 模板）** —— **仍已评估未采纳**（REQ-FUNC-IB-09/17 的交互与流式问答更适合 SPA + 事件流）。
- **Decision（1.0.0）**: ~~Option A（FastAPI + Uvicorn）~~ **已由 R1 取代**，见下方 **ADR-11-R1 修订节**。
- **Consequences（1.0.0；除「载体」表述外仍成立）**: 正向—凭据不出现在 URL（消除已记录事故类别）；流式为单向服务端推送，SSE 语义天然匹配；**无 Redis 依赖（R1 沿用并强化）**；前端可独立构建与部署。负向—SSE 为单向（用户中断/确认须另发 POST，属可接受）；须处理反向代理缓冲（须禁用响应缓冲）；断线重连的 `Last-Event-ID` 语义 v1 取最简实现（「重连即重问」）并在文档显式声明；**（R1 新增）WSGI 下每个 SSE 长连接独占一个 worker/线程，故并发容量有界，须有界 + 可观测**，见修订节。

---

#### ADR-11-R1 修订节（R1；**取代上方 1.0.0 的 Option / Decision 结论**）

- **Context（R1 增补）**: 用户**明确指定后端框架为 Django（非建议）** → 1.0.0 的 Option A（FastAPI + Uvicorn）不可用。须在**保留 1.0.0「弃 WebSocket 以防凭据进 URL」反泄漏初衷**的前提下重新选定流式载体。触发需求不变：REQ-FUNC-IB-09 / IB-17 / IB-21；REQ-NFR-IB-09（AC-IB-11-05：401/403 而非静默）；C-IB-03（目标机资源有限）。**新增容量约束 [TBD-T15]**（SSE 并发上限，未实测）。
- **Options（R1 三方案）**:
  - **Option A（**选定**）：Django + DRF **同步视图 + `StreamingHttpResponse` 直接输出原生 SSE（`text/event-stream`）**，**不引 Channels、不引 Redis**。**
    - 优 — ① 与用户指定框架一致；② **Django 原生能力即可完成 SSE，零新增组件**（对比 1.0.0 Option B 需 Channels + Redis channel layer）；③ **保留并强化 1.0.0 的反泄漏初衷**：SSE 走标准 HTTP，可带 `Authorization` 头，**凭据不进 URL**；④ 同步栈与全链路（同步台账 SQL / 同步 `ib-embed` HTTP 客户端 / 同步 Qdrant 客户端 / langgraph 同步流）**同构**，无需 `sync_to_async` 桥接，从而**不存在**「未桥接的阻塞调用拖慢全部并发连接」这一失效模式；⑤ 与 FreeArk 后端同栈，运维与排障认知成本最低。
    - 缺 — **代价明确**：WSGI 为「一请求一 worker/线程」，**每个 SSE 长连接独占一个 worker/线程至流结束** → 并发问答数受 worker/线程池容量**硬约束**。故必须**有界 + 可观测**：容量显式配置（不依赖默认值）、连接空闲 / 总时长上限、**占满即快速失败 `503`（fail-closed）而非无界排队**（排队会把「慢」放大为「全链路超时」，与 §7.3 一致）；容量按 **[TBD-T15]** 在目标机实测后设定；前置反向代理须**禁用响应缓冲**（`X-Accel-Buffering: no` / `Cache-Control: no-cache`）。
  - **Option B（**升级路径保留，默认不启用**）：Django 异步视图 + Gunicorn `uvicorn.workers.UvicornWorker`（ASGI 服务器，**仍不含 Channels**）。**
    - 优 — 异步视图下 SSE 长连接**不占用 worker 槽位**，并发由事件循环承载，从而解除 Option A 的容量上限；且**仍不引入 Channels / Redis**，反泄漏初衷与最小组成面纪律同时保持。
    - 缺 / 前提 — 全链路同步调用（Django 侧 DB 读、`ib-embed` HTTP、Qdrant 同步客户端、langgraph 同步流）**须经 `sync_to_async` 正确桥接**；**任一未桥接的阻塞调用会拖慢全部并发连接**——该失效模式比「占用一个 worker」**更危险**，故列为升级路径而非默认，且**默认不安装 Uvicorn**。
    - **量化触发条件**：**仅当 [TBD-T15] 实测显示 Option A 的 SSE 并发上限不足以满足目标并发需求时**才启用；判据（目标并发数 vs 实测上限）与结论一并记入 [TBD-T15] 的实测记录。
  - **Option C（**拒绝**）：Channels + Redis channel layer。**
    - 理由 — ① 引入 **Redis 组件与凭据面**，违反 DR-03 / C-IB-08 最小组成面；② 需额外处理**两个已知真实缺陷**（见下方强制约束 (a)(b)）；③ Django 原生 `StreamingHttpResponse` 已满足 SSE 诉求，**收益不足以抵消成本**。**已评估未采纳**。
- **Decision（R1）**: **Option A**。前端静态产物由 `ib-web` 直接提供（或系统 nginx），前端仅通过类型化 HTTP / SSE 契约与后端交互（[ARCH-ASSUMPTION-A5]；Vue 3 + Vite **不受框架切换影响**）。**Option B 作为「有量化触发条件的升级路径」保留**（默认不启用、不安装）；**Option C 拒绝**。
- **Consequences（R1）**:
  - 正向 — 框架与用户指定一致；**零新增组件**（无 Redis、无 Channels）；「凭据不进 URL」的反泄漏初衷保留且被强化；同步栈同构、无 async 桥接风险；前端零改动；HTTP / SSE 契约（`StreamEvent` / `to_sse` / 端点）逐条不变。
  - 负向 — **并发容量被 worker/线程池钉死**（「有界」即须承认上限并显式声明）；池满时部分用户被**明确拒绝（`503`）**而非排队等待——这是刻意的 fail-closed，用以避免「慢」放大为「全链路超时」；容量须在目标机实测校准（[TBD-T15]）后方可承诺；若实测不足须启用 Option B，届时须完成全链路 `sync_to_async` 桥接与回归。
- **两个 FreeArk 真实坑（**强制实施约束；无论最终是否选 C 都必须遵守**）**:
  - **(a) 禁止 `?token=`（任何通道）**：WebSocket 的 token 置于 query string 会被**访问日志完整记录**（FreeArk 真实事故：ChatConsumer 从 `?token=` 读 token，访问日志打印整条 URL）→ **一律改走 `Authorization` 头**（或请求体注入，或**中间件鉴权并把已认证主体写入请求上下文**）；**文档与 URL 一律不得出现凭据型查询串**（对应 AC-IB-12-02 与 `tech_stack.md` §4.5 检查项 8）。
  - **(b) `channels_redis` 4.3.0 与 `redis-py` 8.0.0 不兼容**（WS 收包 RESP3 超时）→ **若未来引入 Channels + Redis，必须 pin `redis-py` 5.x** 并锁定与 `channels_redis` 的兼容组合，且**必须用本地真实 Redis 验证 WS 收发**（**InMemory 测试测不出**该缺陷）。

**ADR-11-R1 复核（框架切换：**已被 ADR-11-R1 全文重写取代**）**

- 本节内容已由上方 **ADR-11-R1 修订节**取代：1.0.0 的「FastAPI + Uvicorn + SSE」结论**撤销**；1.0.0 的「Django + DRF + Channels」结论**部分采纳**（Django + DRF 采纳、Channels 拒绝）。
- **SSE 而非 WebSocket** 的安全取舍**被 R1 继承并强化**（凭据不进 URL；见修订节强制约束 (a)）。载体为实现形式：**Django 同步视图 + `StreamingHttpResponse`**。
- 与其他 ADR 的衔接：容量与进程载体的落点在 **ADR-03-R1**；容量参数在 **[TBD-T15]**；模块侧的映射见 `module_design.md` §2.1.1。

**ADR-11-R2 复核**：**R2 不受影响** —— 流式仍为 Django 同步视图 + `StreamingHttpResponse` 原生 SSE（Option A），Option B 的量化触发条件与 Option C 的拒绝结论**均未动**；R2 新增的图片端点（IFC-IB-283）是**普通 HTTP 响应（非流式）**，**不占用 SSE 长连接预算**，与 [TBD-T15] 的容量纪律相容；强制约束 (a)「禁止 `?token=`」在 R2 中**扩展到全部端点**（含图片端点）。

### ADR-12 OCR 与页面渲染端口（含 OCR 不可用的显式降级）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-11（扫描件 OCR）；AC-IB-04-06（扫描页整页栅格化后 OCR）、AC-IB-04-07（**OCR 引擎不可用须跳过并告警**而非整篇失败）；DR-08（v1 纳入 OCR，移植 FreeArk 既有 RapidOCR 链路）；REQ-NFR-IB-12（`rapidocr-onnxruntime` 为 Apache-2.0，可）。
- **Options**:
  - **A 不设端口，在解析器内 try-import + try/except**：缺—降级语义散落各处；无法替身测试（AC-IB-15-04 不达标）；「跳过并告警」的一致性无法保证。**已评估未采纳**（FreeArk 现状形态）。
  - **B `OcrEngine` 端口（`RapidOcrEngine` / `NullOcrEngine`）+ 独立 `PageRenderer` 端口（`PdfiumRenderer`）** ← **选定**。
  - **C OCR 作为独立常驻服务**：优—与 Web 进程内存隔离、可独立限流。缺—多一个服务与端口；收益在本量级不显。**保留为同一端口下的可切换部署形态**（与 ADR-02 同款可逆性）。
- **Decision**: **Option B**。**OCR 与渲染分为两个端口**，因为二者由不同库提供（OCR 来自 `rapidocr-onnxruntime`，渲染来自 `pypdfium2`），合并会把许可与依赖强绑。`NullOcrEngine` 使 AC-IB-04-07 的「跳过 + WARNING」成为**显式装配选择**而非散落的异常捕获：引擎不可用时装配 `NullOcrEngine`，其返回「无文本」并记录 WARNING，管线继续（该页按无文本处理）。启动期探测依赖可达性并给出可读告警（AC-IB-12-03 / 12-04）。
- **Consequences**: 正向—降级显式可测；替换 OCR 或渲染器只改适配器；OCR 权重与渲染库的许可可**分别**评估。负向—两个端口意味两套替身；扫描页处理为双跳（渲染 → OCR），内存峰值须关注（[TBD-T4']）；OCR 模型首次加载耗时须纳入启动/首次请求预算（[TBD-T3]）。

**ADR-12-R1 复核（框架切换）**：**经检查，不受框架切换影响**。

- 决策客体（`OcrEngine` 端口 + 独立 `PageRenderer` 端口，以及 OCR 不可用的显式降级）位于 **L2 适配器层（MOD-IB-06 / MOD-IB-08）**，仅依赖 MOD-IB-01/02/04，与 HTTP 载体无关。
- 不变项：**OCR 与渲染分为两个端口**（不同库、许可分别评估）、`NullOcrEngine` 使「跳过 + WARNING」（AC-IB-04-07）成为**显式装配选择**而非散落的异常捕获、启动期依赖可达性探测与可读告警（AC-IB-12-03/04）、Option C（OCR 独立服务）作为**同端口可切换部署形态**保留 —— 全部不变。

### ADR-13 检索结果契约与降级语义

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-14（相似度检索）/IB-17（检索供专家使用）；AC-IB-13-01/02（降级须可观测、**可仅凭日志定位失败依赖**）、AC-IB-14-01（embedding 不可用 → 降级标记 + 空命中 + 明确提示「当前未接入知识资料库」）、**AC-IB-14-02（知识库为空不得标记降级，二者须可区分）**、AC-IB-08-04（P95 目标在目标机校准）。
- **Options**:
  - **A 沿用 FreeArk 的 `{"chunks": [...], "degraded": bool}`**：优—语义兼容、调用方改动小。缺—`degraded` **无法区分「哪个依赖坏了」**（AC-IB-13-02 不达标）；无耗时与候选数，阈值校准与观测缺证据；字典**非类型化**（与门控标准 4 冲突）。
  - **B 类型化 `RetrievalResult`（`hits` / `degraded` / `degrade_reason` / `scope` / `elapsed_ms` / `candidate_count`）** ← **选定**。
- **Decision**: **Option B**，且**检索服务永不抛异常**：任何依赖故障一律转为 `degraded=True` 的结果。`degrade_reason ∈ {embedding_unavailable, vectorstore_unavailable, timeout}` 使 AC-IB-13-02「仅凭日志定位失败依赖」成立。**「空知识库」与「依赖故障」在契约上是两个不同取值**（前者 `degraded=False, hits=[]`；后者 `degraded=True, degrade_reason≠None`），直接满足 AC-14-01 / 14-02。`candidate_count` 与分数量级作为 [TBD-T12] 阈值校准的证据出口。
- **Consequences**: 正向—降级可区分、可观测、可测；阈值校准有数据出口；上层按契约分支而非异常处理（无漏捕异常风险）。负向—契约比 FreeArk 宽（调用方须适配）；`degrade_reason` 取值集合须随依赖增加而维护（以枚举约束避免自由字符串）。

---

**ADR-13-R1 修订（框架切换复核：受影响，结论 = 载体更换、类型完整度不降级）**

- **载体变更**：`RetrievalResult` 的载体**明确为 frozen dataclass（端口层，定义于 MOD-IB-01）+ DRF Serializer（HTTP 边界）**（1.0.0 的 FastAPI / Pydantic 载体已随框架切换**撤销**，见 ADR-11-R1）。
- **分层理由**：端口契约位于 **L0 契约层（MOD-IB-01）**，该层**零第三方依赖**（REQ-NFR-IB-01），**不得引入 Pydantic**；DRF Serializer 仅承担 **HTTP 边界**的请求校验、响应序列化与错误聚合（Web 层关注点）。
- **类型完整度不得降级（门控标准 4）**：`RetrievalResult` 的全部字段名 + 类型 + 可空性**逐字段保留**（`module_design.md` §2.1 / IFC-IB-007）：`hits: list[RetrievedChunk]`、`degraded: bool`、`degrade_reason: Literal["embedding_unavailable","vectorstore_unavailable","timeout"] | None`、`scope: Scope`、`elapsed_ms: int`、`candidate_count: int`。**「空知识库」与「依赖故障」的可区分性（AC-IB-14-02）不因载体变更而改变。**
- **不变项**：检索服务**永不抛异常**（任何依赖故障一律转 `degraded=True` 的结果）；`degrade_reason` 以**枚举约束**（非自由字符串）；`candidate_count` 与分数量级仍作为 [TBD-T12] 阈值校准的证据出口。
- **复核结论**：仅**载体表达形式**变化，契约为**等价升级**；对上层（MOD-IB-15 调用方、MOD-IB-17 工具、MOD-IB-21 流事件）**零语义改动**。

**ADR-13-R2 复核**：**R2 不受影响** —— `RetrievalResult` 的字段与降级语义未动；`related_images` 走**独立的流事件**而**不并入** `RetrievalResult`，故「依赖故障 vs 空知识库可区分」（AC-IB-14-02）的不变式保持；R2 另在 `module_design.md` §7.4 为「`ib-embed` 服务不可达」与「页面图不可得」各补一格降级行（前者映射到既有 `degrade_reason`，**不新增枚举值**）。

## 3. 多项目隔离：链路落点与跨项目泄漏失败模式

### 3.1 隔离在链路上的落点（REQ-FUNC-IB-23）

| 链路 | 落点 | 实现要点 | 反例（不做会怎样） |
|------|------|----------|--------------------|
| 上传 | HTTP 层 | `project_id` **只从已认证主体解析**；请求体中的 project 字段被忽略；`kb_id` 须过归属断言 | 请求体伪造 project → 写入他人 collection |
| 存储 | 管线层 + 适配器 | 台账写 `(project_id, kb_id, doc_id)`；原文件落 `/<project_id>/<kb_id>/<doc_id>/`；向量写 `CollectionResolver.resolve(scope)` 得到的 collection，且 payload 冗余 `project_id`/`kb_id` | 单 collection 单命名空间 → 检索跨项目命中 |
| 检索 | 检索服务 | `Scope` **必填**；filter **恒含** `project_id`（defense-in-depth）；返回 `RetrievalResult.scope` 回显供审计 | 漏 filter → 静默跨项目命中 |
| 路由上下文 | 装配期 | 知识库 scope 绑定进 `knowledge_search` 工具闭包与检索客户端；骨架只见无参工具 | scope 作为骨架字段被中途丢失 → 工具退化为项目外检索 |

### 3.2 隔离的三个层面

1. **结构性隔离**（不依赖正确性）：collection-per-project；项目级删除 O(1)；每项目独立 `dim`/模型。
2. **契约性隔离**（依赖类型系统）：`Scope` 必填、无默认值；`ReturnType` 中回显 scope；`degrade_reason` 与 scope 一并落日志。
3. **运行期隔离**（依赖断言与对账）：启动期 `project_id` ↔ collection 前缀一致性断言；归属断言返回 403；删除重放对账；跨 scope 混读检测。

### 3.3 跨项目泄漏失败模式与防护（FM-1 ~ FM-8）

| 编号 | 失败模式 | 后果 | 防护（架构层强制） | 可验证锚点 |
|------|----------|------|--------------------|-----------|
| FM-1 | 检索/删除**漏写 scope filter**（项目内知识库为软隔离，最可能的一处） | 返回他知识库甚至他项目内容 | ① `Scope` 必填无默认值（编译期拦）；② filter **恒含** `project_id`，`kb_ids` 为空时视为「全部知识库」而非「不过滤」；③ `kb_ids` 与 `project_id` 不一致时**先断言后查询** | AC-IB-06-02、AC-IB-11-02 |
| FM-2 | **写入侧错绑 scope**（客户端自证 project） | 数据写到他人 collection，长期潜伏 | `project_id` 只出自认证主体；请求体 project 字段忽略；`kb_id` 过 `assert_kb_in_project` | AC-IB-11-05 |
| FM-3 | **删除越界**（按 doc_name 或按向量 id 删除，未限 scope） | 误删他项目数据 | 删除接口一律收 `Scope`；`delete_by_doc(scope, doc_id)` 内部 filter 含 `project_id`；禁止按「名称」删除 | AC-IB-06-04、AC-IB-03-03 |
| FM-4 | **重建期维度混用**（新旧版本向量混入同一 collection） | 检索报错或静默返回垃圾 | 版本化 collection + `active_collection_version` 单值解析；**不做双写、不做混合读**；切换是台账上的原子写 | AC-IB-16-03 |
| FM-5 | **配置覆盖指向他人 collection**（项目级配置填错） | 隔离被配置错误击穿 | 启动期断言：每项目配置的 collection 前缀必须等于 `ib_<project_id>_v`；`CollectionResolver` 为唯一解析入口，不接受外部传入的 collection 名 | 启动期校验（AC-IB-12-03） |
| FM-6 | **语义路由样例缓存跨项目共享** | 用 A 项目样例为 B 项目路由 → 路由偏差 + 样例文本泄漏 | 路由样例按 `project_id` 分区缓存；缓存键必含 `project_id`；缺样例时回退到关键词/LLM 路径（fail-open 到安全路径） | REQ-FUNC-IB-19 |
| FM-7 | **会话/线程 id 碰撞**（两项目同 `session_id`） | 跨项目读到同一会话历史 | `session_key = f"{project_id}:{actor_id}:{session_id}"`；读取时断言 key 前缀 = 当前 `project_id`，不符即拒（fail-closed） | REQ-FUNC-IB-20 |
| FM-8 | **日志/可观测层泄漏**（把文档正文写进日志） | 敏感内容落盘 | 结构化日志**只记** `doc_id` / `kb_id` / `project_id` / 长度 / 分数 / 耗时，**禁止记正文与片段原文**；异常堆栈中的 payload 亦须脱敏 | AC-IB-12-02、REQ-NFR-IB-06 |

**总结断言**：FM-1/2/3 由**类型系统 + 契约**防（结构性）；FM-4/5 由**命名与断言**防（配置级）；FM-6/7/8 由**键构造与日志纪律**防（运行期）。三类防护层次不同，缺任一层都会留下一条真实可走的泄漏路径。

---

## 4. CPU-only 可行性与必测清单（DR-05）

> **本节是评估，不是实测结论。** 目标机硬件规格未实测（[TBD-T13]），故**本文件不给出任何延迟/吞吐数值**，只给出量级判断、可行性与缓解手段、以及必须实测的指标清单。

**量级判断**：[ESTIMATE] bge-m3 属 XLM-RoBERTa-large 量级编码器，CPU 单条短文本推理的量级通常落在**数十至数百毫秒**区间——**这正是必须实测的原因**：该量级能否满足 REQ-NFR-IB-03 的检索 P95 目标（AC-IB-08-04 要求在目标机校准），**取决于目标机核数与是否支持向量指令（如 AVX 系列）**，无法在开发机外推（AC-IB-07-05 已明令不得以开发机数据充数）。

**可行性结论（DR-05：千级文档）**：① **入库**为异步冷路径，吞吐压力可由时间摊平，CPU-only 可行；② **查询**为同步热路径，是唯一真正的风险点，必须靠下述缓解手段 + 实测校准；③ 千级文档的向量规模对 Qdrant 内存压力温和，风险主要在 embedding 侧而非存储侧。

**缓解手段（架构层已内置，见 ADR-02）**：
1. **批处理**（冷路径）：批量编码摊薄固定开销，批量值由 [TBD-T2] 校准。
2. **模型常驻**（`ib-embed` 独立服务）：避免每次请求加载权重，把冷启动一次性成本移出热路径。
3. **并发上限 + 有界队列**：超出即**快速降级**而非排队，保证「最坏延迟有界」。
4. **推理线程数受控**：避免与 Qdrant / worker / OCR 争核（向量指令并行已用满核时，超订会整体劣化）。
5. **热路径短超时**：超时即降级（返回「当前未接入知识资料库」），把「慢」隔离为「降级」而非「卡死」。
6. **Web 多 worker**（ADR-02 前提）：embedding 独立后 Web 可横向扩 worker。**（R1）** 注意载体已由 ASGI 改为 **WSGI（Waitress / Gunicorn）**：worker 数 / 线程数是**显式配置项**（不依赖默认值），且 **SSE 长连接会占用 worker/线程槽位**，故**并发问答容量 ≈ worker/线程池容量**；容量须按 **[TBD-T15]** 实测设定，池满即**快速失败 `503`**（见 ADR-11-R1 / ADR-03-R1）。
8. **（R1 新增）SSE 容量与「有界」纪律**：流式问答的并发上限**由 worker/线程池显式决定**，不得依赖无限排队；「最坏延迟有界」在本项目同时适用于 embedding 降级路径与 SSE 连接准入路径。
7. **可选 GPU**：`ib-embed` 侧开关，上层无感（REQ-NFR-IB-10）。

**必须实测的指标（TBD，部署前完成，不得以估计代替）**：[TBD-T1] 单条查询 embedding 延迟 P50/P95；[TBD-T2] 批量入库吞吐；[TBD-T2'] PDF 抽取吞吐；[TBD-T3] 模型冷启动加载耗时；[TBD-T4] embedding 进程内存；[TBD-T4'] embedding + OCR 同机内存叠加；[TBD-T5] Qdrant 在目标规模的查询延迟/内存/磁盘；[TBD-T6] 端到端检索 P95（喂给 AC-IB-08-04）；[TBD-T7] 并发上限下的降级曲线；[TBD-T13] 目标机硬件规格。完整清单与判定口径见 §9。

**触发条件（重要）**：若 [TBD-T1/T2] 实测显示 CPU-only 不满足 REQ-NFR-IB-03，可选手段依次为：调模型尺寸（AC-IB-07-05）→ 启用 GPU（REQ-NFR-IB-10）→ 调低并发与批量目标。**调模型尺寸将回溯 DR-02（用户已拍板），须由 PM/用户裁决**；架构层不自行改选型。

---

## 5. 数据处理管线（架构级约定）

> 状态机详表、失败粒度与重试策略、幂等键定义、任务租约字段见 `module_design.md` §6（MOD-IB-13 / MOD-IB-14）。

**七步主流程**：`上传 → 校验 → 解析 → 切分 → 向量化 → 写入 → 台账置位`。

| 步骤 | 归属模块 | 架构级约定 |
|------|----------|-----------|
| 校验 | MOD-IB-13 / MOD-IB-23 | 三重校验：扩展名白名单 → 大小上限 → **文件头魔数签名**（防改扩展名伪装）。校验在**落盘之前**完成 |
| 原文件 | MOD-IB-12 | 内容寻址 sha256 落盘（ADR-05）；写入成功才继续 |
| 解析 | MOD-IB-05 + MOD-IB-06 + MOD-IB-08 | 按扩展名查注册表；PDF 走「文本层 / 内嵌图像 OCR / 扫描页栅格化 + OCR」三路径；**单页 OCR 失败只跳过该页 + WARNING**（AC-IB-04-07） |
| 切分 | MOD-IB-07 | 滑窗切分（`chunk_size` / `chunk_overlap` 可配）；切分参数变更**不自动作用于既有文档**（AC-IB-05-03），须触发重建 |
| 向量化 | MOD-IB-09 | 冷路径批量；维度由 `Embedder.descriptor()` 声明，写入前与 `CollectionSpec.dim` 断言一致 |
| 写入 | MOD-IB-10 | `delete_by_doc(scope, doc_id)` → `upsert(points)`，**以 doc_id 为幂等键**；`wait` 语义可配 |
| 台账置位 | MOD-IB-11 | 向量落库成功**之后**才置 `indexed`（ADR-07 写序）；同事务更新文档状态与计数 |

**状态机（文档级）**：`pending → parsing → indexed`；任一步失败 → `failed`（记 `error_code` + 摘要）。重建为**文档级标记**（`target_collection_version` / `indexed_collection_version`），与入库状态正交。

**失败粒度**：文档级失败**不阻塞**其他文档（AC-IB-16-04 的推广）；页级（OCR）失败只降级该页；**无块级失败概念**（块是派生物，重建即可再生）。

**重试**：① 手动重试（重置为 `pending` 并清租约）；② 租约超时自动回收（ADR-10）；③ 重试次数上限可配，超限进 `failed` 并需人工介入，**不允许无限自动重试**（避免坏文档反复占用 worker）。

---

## 6. 多智能体编排（架构级约定）

> 图节点/边、State 键与 reducer、路由各级判据、事件类型枚举、会话存储接口见 `module_design.md` §7（MOD-IB-16 ~ MOD-IB-22）。

**图结构**：`route → (条件边，fan-out) → expert × N（并行） / general → gate → aggregate → END`。并行扇出用条件边返回多个 `Send`，聚合节点收齐后合并（AC-IB-09-02）。有步数上限（参考 FreeArk `MAX_EXPERT_STEPS = 8`）防失控。

**多级意图路由（REQ-FUNC-IB-19，逐级降级，永不无解）**：
1. **L0 关键词唯一命中** → 短路；
2. **L1 语义高置信**（阈值 τ + 与次优的分差 margin，纯函数判定；**故障即 fail-open 返回 None**，进入下一级）；
3. **L2 LLM 分类器**（`temperature=0` 保证确定性，AC-IB-09-07；**输出须容错解析**，脏输出不得致崩）；
4. **L3 关键词兜底** → 5. **粘性**（沿用上一轮专家，AC-IB-09-05） → 6. **OOD**（明确表态且无任何信号，AC-IB-09-04 的反面保证） → 7. **默认专家**（保证「永远有人回答」，AC-IB-09-04）。
   另设**误路由守卫**：仅在「单专家且低置信且与原路由矛盾」时介入纠正（对齐 FreeArk `_guard_against_misroute`）。
   **路由只看当前提问**（历史前缀剥离），避免多轮上下文污染判据。

**聚合**：合并多专家结果时**禁止暴露内部分工**（不得出现「专家」「转交」「咨询」「路由」类措辞，AC-IB-09-03）——该约束落在聚合提示与结果后处理两处。

**流式输出契约**：事件为类型化元组/对象序列，至少含 `reasoning`（若可得）/ `content` / `degraded` / `related_images` / `error` / `done`；**降级事件必须在流内可见**（用户能看到「当前未接入知识资料库」，AC-IB-14-01 的界面落点）。单专家时流式透传该专家 token；多专家时流式输出聚合结果。

**会话生命周期**：`session_key = f"{project_id}:{actor_id}:{session_id}"`；状态存于 `SessionStore` 端口（默认内存实现，语义 fail-closed）；会话隔离属 FM-7。

**与 FreeArk 的解耦差异（REQ-NFR-IB-01 的落地证明）**：

| FreeArk 现状 | intelligentbase 架构 | 差异理由 |
|--------------|----------------------|----------|
| 人格/身份文本来自业务模块 | 骨架**仅在提供时包裹**，不感知来源 | 骨架业务零依赖 |
| `UserScope` / `ScopeEnforcer` 硬编码 | 泛化为 `context_enricher` 注入点 + 工具闭包 scope 绑定 | REQ-FUNC-IB-23 与 REQ-NFR-IB-01 同时成立 |
| `fa_tools` 业务工具集 | 注册表驱动；内置仅 `knowledge_search` | 可插拔 |
| 三个业务专家 | 通用基线专家集 + 可注册扩展 | 可复用 |
| 写操作确认门（`interrupt()`） | **机制保留、默认关闭**（OQ-IB-07） | 基座不应默认带业务副作用 |
| 流式走 Channels WebSocket（`?token=`） | **Django 原生 SSE（`StreamingHttpResponse`，`text/event-stream`）+ `Authorization` 头；无 Channels、无 Redis** | 消除凭据入 URL 的泄漏类别；且不引入 Redis 组成面（ADR-11-R1） |
| Web 层为 Django + DRF（流式靠 Channels WebSocket，WSGI/ASGI 混合） | **Django + DRF + Waitress/Gunicorn（纯 WSGI）**；流式用原生 `StreamingHttpResponse`，**不引 Channels、不引 Redis** | 与用户指定框架同栈；组成面更小；凭据不进 URL（ADR-11-R1 / ADR-03-R1） |
| 会话态 `MemorySaver` 直接使用 | `SessionStore` 端口（默认内存实现） | 可替换、可替身 |
| `RagVectorCache` 进程内 numpy 全量暴力检索 | Qdrant 原生 HNSW | DR-01 + REQ-NFR-IB-03 |

---

## 7. 应用层、可观测性、降级矩阵与可测试性

> 降级矩阵详表（依赖 × 故障 × 行为 × 用户可见文案 × 日志级别 × fail 语义）与替身清单见 `module_design.md` §7.4 / §8。

### 7.1 应用层定位与责任边界

| 组件 | 架构位置 | 责任 | **明确不负责** |
|------|----------|------|----------------|
| Web 数据导入前端 | L5（MOD-IB-24） | 上传交互、格式与大小**前置**提示、入库状态轮询、删除确认、错误显示 | **不实现校验规则**（以后端为准，前端提示仅为体验）；不直连数据库/向量库 |
| 最小可验证问答入口 | L5（MOD-IB-23 暴露的 SSE 端点 + MOD-IB-24 的问答页） | 提问输入、流式渲染、降级提示展示、引用来源展示 | 不做路由/检索决策；不缓存检索结果（会话历史除外） |

**边界原则**：应用层是**唯一装配点**（组合根）与**唯一的协议转换层**（HTTP/SSE ↔ 领域契约）；它**不含任何业务规则**——校验、切分、路由、聚合的判据全部在下层模块，应用层只做参数解析、鉴权、调用与协议映射。

### 7.2 可观测性（REQ-NFR-IB-06）

结构化日志统一字段：`request_id`、`project_id`、`kb_id`、`doc_id`、`stage`、`outcome`、`elapsed_ms`、`error_code`、`degrade_reason`。**纪律（FM-8）：绝不记录文档正文、检索片段原文、凭据或密钥。** 级别经环境变量可调（AC-IB-13-03）；关键路径（上传/解析/向量化/检索/路由/聚合/降级）**必打点**，使 AC-IB-13-02「仅凭日志定位失败依赖」成立。

### 7.3 降级语义总原则（架构级）

**核心区分：fail-open（降级可用）与 fail-closed（拒绝服务）。**

| 类别 | 依赖 | 语义 | 理由 |
|------|------|------|------|
| **fail-closed（写路径核心）** | 台账、原文件存储 | 不可用即**拒绝**（上传返回 5xx，不产生半成品状态） | 写路径的可靠性是数据一致性的前提（REQ-NFR-IB-16）；半成品状态比拒绝更危险 |
| **fail-open（读路径依赖）** | embedding、向量库、LLM、路由分类器、OCR | 不可用即**降级**：返回明确标记 + 空命中 + 用户可读提示，**不抛异常** | REQ-NFR-IB-13/21；AC-IB-14-01 |
| **可区分语义** | 空知识库 vs 依赖故障 | 二者在契约上取值不同（ADR-13） | AC-IB-14-02 明确要求可区分 |

**降级必须留痕**：每次降级写一条含 `degrade_reason` 的结构化日志，并在流式响应中发 `degraded` 事件。

### 7.4 可测试性（REQ-NFR-IB-14）

| 能力 | 架构支撑 | 验收锚点 |
|------|----------|----------|
| 离线运行 | 全部外部依赖经端口：`FakeEmbedder` / `InMemoryVectorStore` / `FakeLlmProvider` / `NullOcrEngine` / `InMemoryLedgerRepository` | AC-IB-15-01、附录 D |
| 纯逻辑单测 | L0/L1 模块（契约、配置、切分器、解析器注册表、语义路由判分、路由档位、聚合后处理）**无外部 IO** | AC-IB-15-02 |
| 脏输出健壮性 | 路由分类器输出解析为**独立纯函数**，以畸形样本直测 | AC-IB-15-03 |
| 端到端替身 | vectorstore + embedding + LLM 三替身可装配出完整问答链路 | AC-IB-15-04 |
| 替换等价性 | 对 `VectorStore` 的两个适配器跑**同一套端口一致性测试** | AC-IB-06-05 |
| 可观测性可测 | 日志字段与降级事件为契约的一部分，可断言 | AC-IB-13 |
| 离线开关 | 单一环境变量（如 `IB_OFFLINE_MODE`）一键切换全部替身装配 | 附录 D |

---

## 8. 架构假设（需 PM 确认）

| 编号 | 假设内容 | 为何需要假设（需求侧缺口） | 若不成立的影响与代价 | 状态 |
|------|----------|---------------------------|---------------------|------|
| **ARCH-ASSUMPTION-A1** | 项目配置以**配置文件（YAML/JSON）+ 环境变量覆盖凭据**的方式提供，并由 `ConfigurationSource` 端口抽象 | REQ-FUNC-IB-01/IB-02 要求可配置，但未规定配置载体与优先级 | 若要求接入配置中心，只需新增一个 `ConfigurationSource` 适配器，上层零改动 | 需 PM 确认优先级规则（文件 vs 环境变量 vs 默认值） |
| **ARCH-ASSUMPTION-A2** | **隔离边界 = 项目（硬隔离 collection）+ 知识库为项目内软隔离维度（payload filter）** | DR-06 只写「Qdrant collection + 项目级配置隔离」，**未说明知识库是否也为硬隔离边界**；而 AC-IB-06-02 的测试用例字面是「知识库 A vs 知识库 B」 | 若 PM 判定知识库也须硬隔离，须改 A→D（collection-per-(project,kb)）。代价已被收敛：**只改 `CollectionResolver` 解析规则 + 配置结构，上层零改动** | **已确认（R1）：软隔离**（项目级硬隔离 collection + KB 级软隔离 filter）；**维持 Option A，不升级 D**；见 ADR-04-R1 |
| **ARCH-ASSUMPTION-A3** | 向量数 = 文档数 × 平均块数（不假设具体数值） | 需求给量级（千级文档）未给块数分布 | 若块数远超预期，[TBD-T5] 会暴露 Qdrant 内存/延迟问题，可用 HNSW 参数与磁盘化向量缓解 | 需 PM 知悉；由 [TBD-T5] 校准 |
| **ARCH-ASSUMPTION-A4** | 目标机为 **x86_64** Ubuntu（`192.168.31.133`）；**亦可能为 aarch64 —— R1 保持 TBD** | C-IB-03 只写「Ubuntu」，未写架构；而 Qdrant `.deb` 可用性、`pypdfium2` wheel 与 `onnxruntime` 均与架构相关 | 若为 aarch64，Qdrant 可能须走源码编译（ADR-03 Q3），`onnxruntime` 与 `pypdfium2` 须确认对应 wheel。**（R1）该项不影响架构设计与模块设计，仅影响安装路径选择（Q1 vs Q3）；部署前补测即可。** | **TBD（R1：保持未闭合）** —— 部署前补测，标 [TBD-T14]；x86_64 / aarch64 两种结果**均有既定路径** |
| **ARCH-ASSUMPTION-A5** | 前端静态产物由 `ib-web` 直接提供（或系统 nginx） | 需求未规定前端托管方式 | 若改用 nginx，仅部署配置变化，无代码影响 | 需 PM 知悉 |

---

## 9. TBD 清单（部署阶段必须在**目标机**实测校准）

> **纪律**：本节所有项在实测前一律为 TBD。**不得以开发机数据外推**（AC-IB-07-05 明令）。实测记录须可复查（AC-IB-12-04）。

| 编号 | 待测指标 | 关联需求 / AC | 判定用途 |
|------|----------|---------------|----------|
| TBD-T1 | 单条查询 embedding 延迟 P50 / P95（含 / 不含服务往返） | REQ-NFR-IB-03；AC-IB-07-05 | 决定热路径超时值；ADR-02 形态是否可逆切回 |
| TBD-T2 | 批量入库吞吐（块/秒）与最优批量值 | REQ-NFR-IB-04 | 冷路径批量默认值、worker 并发度 |
| TBD-T2' | PDF 抽取吞吐（页/秒，分文本型 / 扫描型） | REQ-FUNC-IB-10/IB-11 | 入库时长上限、worker 并发 |
| TBD-T3 | 模型冷启动加载耗时 + OCR 模型加载耗时 | REQ-FUNC-IB-22 | 是否后台预热、启动超时设置 |
| TBD-T4 | `ib-embed` 常驻内存占用 | REQ-NFR-IB-10 | 目标机内存预算 |
| TBD-T4' | embedding + OCR 同机内存叠加峰值 | REQ-NFR-IB-10 | 进程边界是否需要进一步隔离 |
| TBD-T5 | Qdrant 在目标规模的查询延迟 / 内存 / 磁盘；**多 collection 的伸缩性** | REQ-NFR-IB-03；ARCH-ASSUMPTION-A3 | 验证 collection-per-project 的资源代价 |
| TBD-T6 | **端到端检索 P95** | REQ-NFR-IB-03；AC-IB-08-04 | **该 AC 的校准基准** |
| TBD-T7 | 并发上限下的降级曲线（何时开始降级、劣化是否平滑） | REQ-NFR-IB-13 | 并发上限参数 |
| TBD-T8 | 中文语料上 `pypdf` / `pdfminer.six` / `pdfplumber` 抽取质量与速度对比 | REQ-FUNC-IB-10；ADR-06 | **决定 ADR-06 的主 / 回退顺序** |
| TBD-T9 | XObject 滤镜覆盖（JPXDecode / CCITTFaxDecode 等） | REQ-FUNC-IB-11 | 扫描件路径的覆盖率缺口 |
| TBD-T10 | 云端 DeepSeek 是否原生流式返回 `reasoning_content`，以及当前 `langchain-openai` 是否丢弃 | REQ-FUNC-IB-21 | 是否需在 provider 内直读 SDK delta |
| TBD-T11 | 单文档入库时长上界（含 OCR） | REQ-FUNC-IB-04 | 租约时长（ADR-10，过短会误回收） |
| TBD-T12 | bge-m3 在中文语料上的余弦分数分布 → 合理阈值区间 | REQ-FUNC-IB-14；AC-IB-08-03 | 检索阈值默认值 |
| TBD-T13 | **目标机硬件规格**（核数 / 内存 / 磁盘 / 指令集 / 是否 GPU） | C-IB-03 | 上述全部指标的分母 |
| TBD-T14 | Qdrant 官方 `.deb` 在目标 Ubuntu 版本的可用性（含架构） | REQ-FUNC-IB-22；ARCH-ASSUMPTION-A4 | 决定 ADR-03 走 Q1 / Q2 / Q3 |
| **TBD-T15（R1 新增）** | **SSE 并发上限**：单实例可同时承载的 **SSE 长连接数** + 对应 **worker/线程配置**（Waitress `--threads`；Gunicorn `--workers` × `gthread` 线程数），以及达到上限时的实际行为 | REQ-FUNC-IB-21；REQ-NFR-IB-13；**ADR-11-R1 / ADR-03-R1** | 决定 **Option A 的容量参数**；判定**是否触发 Option B 升级路径**（Django 异步视图 + `uvicorn.workers.UvicornWorker`，**仍不含 Channels / Redis**）；实测须同时确认池满时**快速失败 `503`**（fail-closed）**而非排队**，且未拖垮非流式端点 |
| **TBD-T16（R2 新增）** | `ib-embed` 服务端的**并发与线程校准**：`IB_EMBED_MAX_CONCURRENCY` / `IB_EMBED_THREADS` / `IB_EMBED_QUEUE_DEPTH` 在目标机的最优值，以及它与 Qdrant / `ib-web` / OCR **同为 CPU 竞争者**时的叠加影响 | REQ-NFR-IB-03；ADR-02；`ib_embed_service_contract.md` §9 | 定服务端并发 / 队列 / 线程参数，并**据实重定** `IB_EMBED_MEMORY_LIMIT_MB`（目标机 11GiB，须与单元文件 `MemoryMax` 一并重定，见契约 §13 第 4 项） |
| **TBD-T17（R2 预留，未分配）** | ——（R2 保留号；目的：防止下游为**同一指标**另起一个号） | — | 供 GROUP_C 追加实测项时**按序取用**；**R2 未使用** |
| **TBD-T18（R2 新增）** | **目标机 CPU 指令集基线实测**：目标机 CPU（Intel i7-3770S / Ivy Bridge）具备 **AVX 但无 AVX2**；须实测候选预编译 wheel（**① 既有 OCR 链路的 `onnxruntime` 系；② R2 的 embedding 推理运行时**）在该机上是否会触发 **SIGILL（非法指令，进程级崩溃，不可捕获）** | REQ-NFR-IB-10；AC-IB-07-05；ADR-02 / ADR-06 / ADR-12 | 决定 wheel 选型 / 是否**自源码编译并关闭 AVX2** / 是否改用纯 Python 后备路径；**不得以「开发机可用」代替目标机实测**（AC-IB-07-05 同精神）。**两条链路同源，须一次性合并评估**，否则排障会归因错误 | |

---

## 10. 开放问题、合规结论与自检

### 10.1 开放问题（不阻塞架构，须用户/PM 裁决）

| 编号 | 问题 | 架构默认取值 | 影响面 |
|------|------|--------------|--------|
| OQ-IB-01 | 原始文件是否持久化 | **持久化（默认开）**，因 DR-07 索引重建以其为前置 | **已确认（R1）：保留（ON）** —— ADR-05-R1；关闭则 AC-IB-16-01 不成立 |
| ARCH-ASSUMPTION-A2 | 知识库是否须硬隔离 | 软隔离（payload filter） | **已确认（R1）：软隔离**（项目级硬隔离 collection + KB 级软隔离 filter）；ADR-04-R1；升级路径成本仍收敛到 `CollectionResolver`（不启用） |
| ARCH-ASSUMPTION-A4 | 目标机 CPU 架构 | x86_64（**R1：保持 TBD**，亦可能为 aarch64） | ADR-03 安装路径；依赖 wheel 可用性。**不影响架构实现**，仅影响安装路径（Q1 vs Q3）；部署前实测 [TBD-T14] |
| OQ-IB-05 | 是否需要混合检索（稀疏 + 稠密） | v1 仅稠密（DR-02） | 端口已预留扩展方法位 |
| OQ-IB-07 | 写操作确认门是否默认启用 | **默认关闭** | 编排机制保留，装配期开关 |
| OQ-IB-02 / 04 / 06 / 08 | 次级开放问题（措辞未变，P1） | 不阻塞 | 待用户裁决 |

### 10.2 许可合规结论（REQ-NFR-IB-12）

| 组件 | 许可 | 结论 |
|------|------|------|
| **PyMuPDF** | **AGPL-3.0** | **不采纳**。三条合规前置条件均不满足或与需求冲突（ADR-06 已逐条列明）。**未沿用「内部平台合规」口径（REQ-NFR-IB-12 明令禁止）。** |
| Qdrant | Apache-2.0 | 采纳（DR-01） |
| bge-m3 模型权重 | MIT | 采纳（DR-02） |
| rapidocr-onnxruntime | Apache-2.0 | 采纳（DR-08） |
| onnxruntime | MIT | 采纳 |
| pypdf | BSD-3-Clause | 采纳（文本主） |
| pdfminer.six | MIT | 采纳（回退） |
| pdfplumber | MIT | 可选采纳 |
| pypdfium2 | BSD-3-Clause OR Apache-2.0 | 采纳（渲染） |
| **Django（R1 新增）** | **BSD-3-Clause** | **采纳**（Web 框架；用户指定；R1 经外部核实后登记） |
| **Django REST Framework（R1 新增）** | **BSD-3-Clause** | **采纳**（HTTP 边界校验与序列化；R1 经外部核实后登记） |
| **Waitress（R1 新增）** | **ZPL-2.1**（OSI 认可、FSF 判定 GPL 兼容） | **采纳**（生产 WSGI 服务器主选，与 FreeArk 一致；R1 经外部核实后登记） |
| **Gunicorn（R1 新增）** | **MIT** | **采纳**（WSGI 服务器备选，多 worker / 多线程；R1 经外部核实后登记） |
| **Uvicorn（R1 新增；仅并发升级路径）** | **BSD-3-Clause** | **条件性采纳**：仅当 ADR-11-R1 的 Option B 被 [TBD-T15] 触发时引入，**默认不安装** |
| Poppler CLI | GPL-2.0 | 不采纳（仍属 copyleft，子进程隔离的法律定性有争议） |

**（R1）新增登记**：Django / DRF（BSD-3-Clause）、Waitress（ZPL-2.1）、Gunicorn（MIT）—— 均经外部核实后登记，未凭印象；锁定版本后仍须按发行包内 `LICENSE` 复核。**（R1）撤销**：FastAPI / Uvicorn 退出 Web 层选型（用户指定 Django，见 ADR-11-R1）；Pydantic 退出 Web / 校验层，仅可作**可选**独立校验库，且**不得**作为任何端口契约的载体（ADR-13-R1）。

完整选型与风险表见 `tech_stack.md`。

### 10.3 自检声明

- 本文所有 ADR 均含 Context（**REQ-* 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences 五节。
- 本文**不含任何实现代码**：所有片段均为接口签名、类型注解、数据结构与架构级约定。
- 本文**未给出任何编造的实测数值**：性能相关内容一律标注 `[ESTIMATE]` 或 `[TBD-Tn]`。
- 隔离设计**贯穿上传 → 存储 → 检索 → 路由上下文**（§3.1），并给出 8 类跨项目泄漏失败模式与逐条防护（§3.3）。
- REQ → MOD 覆盖率矩阵（24 条 REQ-FUNC 全覆盖）、模块依赖图 DAG 无环证明、类型化接口契约、组合根装配表见 `module_design.md`。
- 本阶段**止于 GROUP_B**：未进入 GROUP_C，未调用任何实现类子代理，**未修改 FreeArk 仓库任何文件**，**未在任何输出中写入凭据/密钥/令牌**。
- **（R1）框架切换复核已逐条留痕**：§2.0 给出 ADR-01 ~ ADR-13 共 **13 行**影响复核表（**受影响 5 条**：ADR-03 / 07 / 08 / 11 / 13；**不受影响 8 条**：ADR-01 / 02 / 04 / 05 / 06 / 09 / 10 / 12），受影响者均有对应的 `-R1` 修订节或更正说明，**无一条 ADR 未复核**。
- **（R1）不变约束未被破坏**：模块数仍 **25**（MOD-IB-01 ~ MOD-IB-25）、端口仍 **13**、IFC-IB 契约编号（**58 个使用中**）**全部未变**（仅改**载体说明**；ADR-01 的方法数 11 / IFC-IB-100~110 为**与 `module_design.md` 对齐的一致性更正**）；REQ→MOD 覆盖仍为 **24/24 REQ-FUNC + 14 条 NFR**；模块依赖图 **DAG 无环**（证明未受改动影响，见 `module_design.md` §4.2.1）。
- **（R1）凭据纪律**：本文所有凭据相关表述一律为「**环境变量注入**」；**未写入任何凭据 / 密钥 / 令牌**；**URL 与文档中不得出现凭据型查询串**（`?token=` 类），该纪律已写入 ADR-11-R1（强制约束 (a)）与 `tech_stack.md` §3 / §4.5 检查项 8。
- **（R1）需求侧与 FreeArk 未受影响**：`requirements_spec.md` / `user_stories.md` **未作任何修改**；`FreeArk` 仓库**任何文件未作任何修改**。
- **（R2）L-03 补交已闭合**：`ib-embed` 具**模块归属**（MOD-IB-26）与**契约单一落点**（`docs/ib_embed_service_contract.md`，IFC-IB-266~274）；ADR-02 追加 **R2 附注**（Decision 未改）；新增 **§2.0.1 R2 影响复核表**（**受影响 1 条**（ADR-02，仅补附注）／**R2 不受影响 12 条**，无一条跳过），并为 ADR-04 / 06 / 11 / 13 追写 inline 复核句。
- **（R2）不变约束未被破坏**：`IFC-IB-001~265` 一字不动（新增 266~284 / 286；285 预留未分配）；端口数仍 **13**；REQ→MOD 覆盖仍 **24/24 REQ-FUNC + 14 NFR**；依赖图**仍为 DAG**（模块数 25 → 26，新增单边 `26 → {01,02,04}` 且 26 无入边）；**错误码语义映射不变式**（4xx/409 = 重试无用，5xx = 重试可能有用）已随 ADR-02-R2 附注登记。
- **（R2）凭据纪律**：全文仍只登记**键名**；`ib-embed` **不需要任何令牌**；**URL 与文档一律不得出现凭据型查询串**（该纪律在 R2 扩展至**全部**端点，含新增的图片端点）。
