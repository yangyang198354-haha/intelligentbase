<file_header>
  <project>intelligentbase</project>
  <artifact>implementation_plan</artifact>
  <path>docs/implementation_plan.md</path>
  <doc_id>IMPL-INTELBASE-001</doc_id>
  <version>2.5.0</version>
  <status>DRAFT</status>
  <phase>GROUP_C / PHASE_05 实现计划（R7 定义外置增量 + R8 缺陷修复增量 + R10 前端构建阻断修复增量）</phase>
  <author>software-developer</author>
  <invocation_id>INV-GROUP_C-INTELBASE-002</invocation_id>
  <latest_invocation_id>INV-GROUP_C-INTELBASE-008</latest_invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-09-27</updated_at>
  <revision_note>R1（v1.0.0）为 GROUP_C 首轮交付（69 文件 / 16,396 行 / 25 模块）。
    R2（v2.0.0）为**增量**：只做两件事 ——（L-03）实现 MOD-IB-26 `ib-embed` 服务端 + 进程内第三种 Embedder 形态；
    （M-02）实现页面图关联的生产与读路径（related_images）。**R1 内容一律保留**，本轮只追加与最小改动（见 §12）。
    R3（v2.1.0）为**缺陷修复增量**（invocation INV-GROUP_C-INTELBASE-003；输入 = `docs/test_report.md` §5 登记的两个缺陷）：
    修 FND-GROUP-D-02（未绑定 collection 前删除 → 500 且产生幽灵文档，MAJOR）与 FND-GROUP-D-01（能力摘要恒空，MEDIUM），
    并订正 `deploy/checklists.txt` 中「ib-embed 无归属模块」的过期表述。**未新增模块 / 未改任何 IFC 签名 / 未改配置键名与默认值**，
    只追加（见 §13）。正文 §1~§12 为 R1/R2 的**历史记录，未改写**。
    R4（v2.2.0）为**缺陷修复 + 依赖补齐增量**（invocation INV-GROUP_C-INTELBASE-004；输入 = verifier 独立复现的 FND-GROUP-D-03 与
    部署侧登记的 B-05）：（A）修 FND-GROUP-D-03（删除文档后原文件字节成孤儿、`blob_deleted` 恒 False，MAJOR，触及 AC-IB-03-02/03）
    —— 将「可选 kb → 存储段」的推导收敛为**单一真源** `ib.blob.kb_segment`，并让 `delete_document` 由**台账记录**派生原文件删除 scope；
    （B）补 B-05 —— 新增 `src/requirements-embed.txt`（ib-embed 推理运行时：FlagEmbedding + torch(CPU) + transformers，含 bge-m3 权重双源说明）。
    **未新增模块 / 未改任何 IFC 签名（含 `delete_document`）/ 未改配置键名与默认值 / 未把重型依赖混入主 `requirements.txt`**，只追加（见 §14）。
    正文 §1~§13 为 R1~R3 的**历史记录，未改写**。
    R7（v2.3.0，invocation INV-GROUP_C-INTELBASE-005）为 **GROUP_B R7 定义外置增量**（内容与 `module_design.md` R7 / `architecture_design.md` R7 对齐；
    **本文件沿用自身版本线 v2.3.0**（R2=v2.0.0 → R3=v2.1.0 → R4=v2.2.0 → R7=v2.3.0），**与 GROUP_B 三份文档的 1.3.0 属各自独立版本线，不互相覆盖**）。**只追加、不改写**：落地 REQ-FUNC-IB-25 / IB-26 / IB-27 ——
    ①**施工前置**（REV-07-6 裁定 (a)）：先把「专家 / 路由 / 编排 / 工具授权」外置为**定义文档数据**并确立**单一真源**（REQ-FUNC-IB-01 / IB-02 的实现落差闭合），再回填界面真实内容；
    ②**定义文档数据层**（MOD-IB-02，IFC-IB-288~292）：装载 / 完备性校验 / 派生 / 原子写回 / 可编辑白名单，`validate` 与 `derive` 为**纯函数**（离线可测）；
    ③**定义文档端口**（MOD-IB-01，IFC-IB-287）：第 **14** 个端口 `DefinitionDocumentStore`（Protocol，5 方法）+ 10 个 frozen 数据结构（纯 stdlib、零第三方依赖）；
    ④**装配期 fail-fast 准入闸门 + 端点**（MOD-IB-23，IFC-IB-293~295）：校验不通过即**拒绝装配、服务不启动**，无强制继续开关；`GET`/`PUT /api/config/definition`，界面编辑与直接改文档**一视同仁**；
    ⑤**可视化配置页**（MOD-IB-24，IFC-IB-296）：Vue Flow **只读**图渲染 + 白名单表单（拓扑运行期**不可编辑**），**视图侧零持久化**（无第二真源），**本地打包、运行期禁 CDN**（数据不出本机）；
    ⑥**配置键**（IFC-IB-297）：`IB_DEFINITION_DOC_PATH`、`IB_VISUAL_CONFIG_ENABLED`——**仅登记键名，任何文件与响应体均不含键值**。
    **未新增模块（仍 26，MOD-IB-01~26）/ 端口 13 → 14（纯追加）/ 未改既有 IFC 签名 / 未改既有配置键名与默认值 / 未改依赖边**，只追加（见 §15）。正文 §1~§14 为 R1~R4 的**历史记录，未改写**（§1 概览表仅追加 R7 计数订正行，见 §15.1）。（R7 门控订正：INV-GROUP_C-INTELBASE-006，PM 门控 GR-C-005 复核修正版本线与计数口径。）
    R8（v2.4.0，invocation INV-GROUP_C-INTELBASE-007）为**缺陷修复增量**（输入 = GROUP_D `docs/test_report.md` §12.6 / §12.10 登记的 **FND-R7-01（MAJOR）**；协调者裁决 A / REV-08）：在 `src/ib/config/definition.py::validate` **纯追加**两项装配期校验 —— ①**跨专家路由关键词撞车**（归一化 = `strip().lower()`，对齐路由消费方 `ib/routing/intent.py::_keyword_hits`）、②**`cn_label` 唯一性**（去首尾空白后比较）；违反即产出可定位的 `ValidationErrorItem`（`expert_keyword_collision` / `expert_cn_label_duplicate`），由既有 `admit` 聚合闸门在装配期 fail-fast 拒绝。**本文件沿用自身版本线 2.3.0 → 2.4.0**（R2=2.0.0 → R3=2.1.0 → R4=2.2.0 → R7=2.3.0 → R8=2.4.0），**与 GROUP_B 三份文档的 1.3.0/R7 属各自独立版本线，不互相覆盖**。**未新增模块（仍 26）/ 未改端口数（仍 14）/ 未改任何 IFC-IB 号或签名 / 未改模块边界 / 未改 `EXPERT_SPECS` 默认数据 / 未改 validate() 既有 9 项校验的语义与顺序（仅在其后追加）**，只追加（见 §16）。正文 §1~§15 为 R1~R7 的**历史记录，未改写**。
    R10（v2.5.0，invocation INV-GROUP_C-INTELBASE-008）为**前端构建阻断修复增量**（输入 = PM 只读取证：CI 阶段9 在 `src/frontend` 执行 `npm ci` 因**锁文件与 `package.json` 失同步**而 EUSAGE 失败，`npm run build` 永不抵达）。修三处**交付管线阻断**：①**锁同步** —— `src/frontend/package-lock.json` 内**无** `@vue-flow/core` 任何条目（R7 引入该依赖时未随锁提交），重新 `npm install` 生成，纳入 `@vue-flow/core` **1.48.2** 及其 **14 个传递包**；②**未跟踪源文件** —— `src/frontend/src/views/ConfigPage.vue`（被已跟踪的 `App.vue` 导入）此前**未纳入 git**，CI checkout 后 `vue-tsc` 必因缺文件而失败，本轮 `git add` 纳入版本控制；③**类型错误** —— `ConfigPage.vue` 导入未使用的 `type ExpertSpecInput`，在 `noUnusedLocals: true` 下直接 `TS6133` 致 `vue-tsc --noEmit` 失败，删除该无用导入。另落地**前端冒烟测试最小入口**（`package.json` 新增 `test` = `node --test`，纯 Node 内建、**零新增依赖**；含「锁与 `package.json` 同步」回归闸）并据实登记传递依赖许可于 `tech_stack.md` §2.1。**本文件沿用自身版本线 2.4.0 → 2.5.0**，**与 GROUP_B 文档属各自独立版本线**。**未新增模块（仍 26）/ 未改端口数（仍 14）/ 未改任何 IFC-IB 号或签名 / 未改后端 `src/ib`·`src/ibweb`·`src/ib_embed` 任何行为 / 未改配置键名与默认值**，只追加（见 §17）。正文 §1~§16 为 R1~R8 的**历史记录，未改写**。</revision_note>
  <inputs>
    <input path="docs/architecture_design.md" version="1.2.0" revision="R2" status="APPROVED (GROUP_B gate_decision=PASS / GR-B-003；文件头 status 字段仍为 DRAFT_FOR_GATE_REVIEW，以 phase_status.md 为权威 —— 见 §8 偏差 D-01)"/>
    <input path="docs/module_design.md" version="1.2.0" revision="R2" status="APPROVED（同上；R2 增补 MOD-IB-26 与 IFC-IB-266~286）"/>
    <input path="docs/tech_stack.md" version="1.2.0" revision="R2" status="APPROVED（同上；§1.2 登记 11 个 IB_EMBED_* 键）"/>
    <input path="docs/ib_embed_service_contract.md" version="1.1.0" revision="R2" status="APPROVED"/>
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
  </inputs>
  <frozen_constraints>
    <constraint>Django + DRF + Waitress/Gunicorn（WSGI）；禁止 FastAPI/Uvicorn 作为 Web 载体</constraint>
    <constraint>Django StreamingHttpResponse 原生 SSE；禁止 Channels、禁止 Redis；SSE 鉴权仅 Authorization 头，禁止 ?token=</constraint>
    <constraint>Qdrant 经窄 VectorStore 端口（11 方法 IFC-IB-100~110）；scope 必填；filter 恒含 project_id</constraint>
    <constraint>embedding=bge-m3 经独立 ib-embed HTTP 服务；Embedder 冷/热双路径</constraint>
    <constraint>collection-per-project 硬隔离 + 知识库软隔离；CollectionResolver.resolve() 唯一入口</constraint>
    <constraint>原始文件持久化 ON；BlobStore sha256 内容寻址；重建 = 新版本→逐文档 delete-then-write→原子切换</constraint>
    <constraint>台账 = stdlib sqlite3（WAL + busy_timeout），LedgerRepository 端口 + 自管 SQL，不经 Django ORM；手写 scoped 迁移</constraint>
    <constraint>PDF = pypdf(主) + pdfminer.six(回退) + pdfplumber(可选) + pypdfium2(栅格化) + rapidocr-onnxruntime(OCR)；严禁 PyMuPDF</constraint>
    <constraint>LLM = DeepSeek 经 LlmProvider；langchain-openai pin &lt;0.3；EgressDescriptor 显式声明外发；路由 temperature=0</constraint>
    <constraint>MOD-IB-15 永不抛异常（fail-open → RetrievalResult.degraded）；台账/BlobStore fail-closed（503）</constraint>
    <constraint>LangGraph StateGraph；Annotated[..., operator.add]；MAX_EXPERT_STEPS=8；编排仅经已绑 scope 的工具</constraint>
    <constraint>MOD-IB-23 唯一装配点 build_application(deps)；AuthzPolicy 未注入即启动失败；配置键名不得新增/改名</constraint>
    <constraint>IC-IB-01 前端统一走封装 api 层显式 Authorization，禁止裸 axios 依赖隐式 session cookie</constraint>
  </frozen_constraints>
</file_header>

# 实现计划 — intelligentbase

**版本**: 1.0.0 | **日期**: 2026-09-25 | **阶段**: GROUP_C / PHASE_05
**范围**: 26 个模块（MOD-IB-01~26）/ 14 个端口 / 59 条端口级 IFC-IB 契约（R7 +1，IFC-IB-287；另 R7 新增 IFC-IB-287~297 共 11 条，其中端口级 1 条）/ 27 条 REQ-FUNC。
**本计划不含测试套件**（GROUP_D 职责）；`src/scripts/selfcheck.py` 仅为**自我验证**用途，非正式测试交付物。

---

## 1. 实现概览

| 项 | 值 |
|----|----|
| 交付文件数 | **69**（代码 + 部署交付物 + 文档模板） |
| 交付代码行数 | **16,396** |
| 模块总数 | 25（MOD-IB-01 ~ MOD-IB-25） |
| 端口数 | 13（定义于 MOD-IB-01 `ib/core/ports.py`） |
| 生产适配器 | 10 个（Qdrant / LocalHttpEmbedder / OpenAiCompatibleProvider / RapidOcr / Pdfium / SqliteLedger / FsBlob / MemorySession / DenyAllPolicy / FileConfigSource） |
| 替身适配器 | 10 个（InMemoryVectorStore / FakeEmbedder / FakeLlmProvider / NullOcr / NullRenderer / InMemoryLedger / InMemoryBlob / StubOcr + 同上两项复用） |
| 包结构 | `src/ib/`（基座库，MOD-IB-01~22）+ `src/ibweb/`（Django 项目 = MOD-IB-23）+ `src/frontend/`（MOD-IB-24）+ `src/deploy/`（MOD-IB-25） |
| 实现批次 | 6 批（严格按 MOD 编号升序 = 拓扑序） |
| 目标 Python | `>=3.11,<3.14`（部署锁定）；本地自测机为 3.14.6 —— 见 §9 偏差 D-03 |
| **R7 计数订正** | **端口数 13 → 14**（+`DefinitionDocumentStore`，IFC-IB-287，纯追加）；生产适配器 **10 → 11**（+`FileDefinitionDocumentStore`）；替身适配器 **10 → 11**（+`InMemoryDefinitionDocumentStore`）；**模块总数 25 → 26（R2 起；R7 未再增，MOD-IB-01~26）、实现批次仍 6 批**；REQ-FUNC 覆盖计数 **24 → 27**（R7 同步）。详见 §15 |

**核心不变式（贯穿实现）**：
1. `ib/core/`（MOD-IB-01）**零第三方依赖** —— 只允许 `dataclasses` / `typing` / `enum` / `abc` / `collections.abc` 等 stdlib。实现后以 `selfcheck.py::test_core_framework_free` 在**干净子进程**中断言 `sys.modules` 无任何非 stdlib 顶层包。
2. Django / DRF 类型**只出现在 `src/ibweb/` 内**，不得向 `src/ib/` 反向渗透（module_design §2.1.1 不变式）。
3. 所有第三方重依赖（qdrant_client / pypdf / pdfminer / pypdfium2 / rapidocr / python-docx / langgraph / langchain_openai）一律**函数内延迟导入**，缺失时抛 `DependencyUnavailableError`（含安装指引），不做模块级导入 —— 保证离线可导入、离线可装配替身。

---

## 2. 文件树（实际交付）

```
src/
  manage.py                                # Django 管理入口（收窄配置）
  requirements.txt                         # 版本约束（部署时锁定）
  ib/                                      # ── 可复用基座库（MOD-IB-01~22）──
    __init__.py
    core/__init__.py        # MOD-IB-01 契约层（enums/errors/types/ports 汇总导出）
    core/enums.py           # MOD-IB-01  IFC-IB-011
    core/errors.py          # MOD-IB-01  IFC-IB-012
    core/types.py           # MOD-IB-01  IFC-IB-001~010
    core/ports.py           # MOD-IB-01  13 个 Protocol（含 CollectionResolver/BlobStore）
    config/__init__.py      # MOD-IB-02  IFC-IB-021~024
    context/__init__.py     # MOD-IB-03  IFC-IB-031~034
    observability/__init__.py # MOD-IB-04 IFC-IB-041~045
    parsing/__init__.py     # MOD-IB-05  IFC-IB-051~053 + 魔数签名（sniff_magic）
    parsing/pdf_parser.py   # MOD-IB-05  PDF 三路径（pypdf 主 / pdfminer.six 备 / pdfplumber 可选）
    parsing/text_parsers.py # MOD-IB-05  txt / md / docx
    ocr/__init__.py         # MOD-IB-06  IFC-IB-061~064
    chunking/__init__.py    # MOD-IB-07  IFC-IB-071
    rendering/__init__.py   # MOD-IB-08  IFC-IB-081~082
    embedding/__init__.py   # MOD-IB-09  IFC-IB-090~096 + 098（CollectionResolver）
    vectorstore/__init__.py # MOD-IB-10  InMemoryVectorStore + QdrantVectorStore
    ledger/__init__.py      # MOD-IB-11  IFC-IB-120~131（InMemoryLedgerRepository）
    ledger/sqlite_repo.py   # MOD-IB-11  SqliteLedgerRepository（自管 SQL / WAL / 租约）
    ledger/schema.py        # MOD-IB-11  手写 scoped DDL（单一真源）
    blob/__init__.py        # MOD-IB-12  IFC-IB-131~134（InMemoryBlobStore + FsBlobStore）
    lifecycle/__init__.py   # MOD-IB-13  IFC-IB-141~145
    rebuild/__init__.py     # MOD-IB-14  IFC-IB-151~156
    retrieval/__init__.py   # MOD-IB-15  IFC-IB-161~162
    experts/__init__.py     # MOD-IB-16  IFC-IB-171~179
    tools/__init__.py       # MOD-IB-17  IFC-IB-181~183
    routing/semantic.py     # MOD-IB-18  IFC-IB-191~193
    routing/intent.py       # MOD-IB-19  IFC-IB-201~203
    llm/__init__.py         # MOD-IB-20  IFC-IB-211~215
    streaming/__init__.py   # MOD-IB-21  IFC-IB-221~225
    orchestration/__init__.py # MOD-IB-22 IFC-IB-231~233
  ibweb/                                   # ── Django 项目 = MOD-IB-23 ──
    __init__.py
    settings.py             # 收窄配置（不启用 auth/admin；不经 ORM 承接台账）
    apps.py                 # AppConfig.ready() = 启动期必填校验（IFC-IB-263）
    urls.py                 # URLconf（IFC-IB-242~250 路由）
    wsgi.py                 # WSGIApplication 入口
    composition.py          # IFC-IB-241 build_application / build_deps（唯一装配点）
    authz.py                # IFC-IB-250 AuthzPolicy 注入 + 401/403
    serializers.py          # DRF Serializer（HTTP 边界；领域契约仍在 ib/core）
    views.py                # IFC-IB-242~249
    sse.py                  # StreamingHttpResponse 承载 + SSE 头纪律
  frontend/                                # ── MOD-IB-24 ──
    package.json  vite.config.ts  index.html  tsconfig.json  .gitignore
    src/main.ts               # 引导：令牌只从 sessionStorage 取，并抹掉 URL 上的 ?token=
    src/env.d.ts              # *.vue 模块声明（缺它会让 vue-tsc 报 TS2307）
    src/App.vue               # 外壳 + 三页切换 + 令牌门（未认证即阻断，不白屏）
    src/api/client.ts         # IFC-IB-259（显式 Authorization，IC-IB-01；无 axios）
    src/views/UploadPage.vue   # IFC-IB-256（在途文档才轮询）
    src/views/ChatPage.vue     # IFC-IB-257（fetch 流式读 SSE，带 Authorization 头）
    src/views/RebuildPage.vue  # IFC-IB-258（单文档失败 → 不切换版本）
  deploy/                                  # ── MOD-IB-25 ──
    systemd/{qdrant,ib-embed,ib-web,ib-worker}.service   # IFC-IB-261
    env.example                                        # IFC-IB-262（纯占位符）
    config.example.json                                # 配置模板（纯占位符）
    migrations/001_ledger_init.sql                     # 手写 scoped 迁移（由 ddl_script 生成）
    checklists.txt                                     # IFC-IB-264/265（真机验证 + Qdrant 安装）
  requirements-offline.txt                 # 离线装配裁剪集（Django/DRF/langgraph/core/pypdf）
  ibweb/worker.py                          # 队列消费 + 租约回收 + 重建推进（D-07）
  ibweb/bootstrap.py                       # --ensure-schema 启动前置（D-07）
  scripts/selfcheck.py                     # 后端离线自检 15 例（非正式测试套件）
  scripts/sse_parser_selfcheck.mts         # 前端 SSE 分帧自检 9 例（Node 类型擦除直跑）
```

---

## 3. 模块 → 文件映射（按拓扑序）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置 | 复杂度 | 状态 |
|------|--------|--------|---------|----------|--------|------|
| 1 | MOD-IB-01 | 核心契约 | `ib/core/{enums,errors,types,ports}.py` | — | H | PLANNED |
| 2 | MOD-IB-02 | 配置 | `ib/config/__init__.py` | 01 | H | PLANNED |
| 3 | MOD-IB-03 | 请求上下文 | `ib/context/__init__.py` | 01 | L | PLANNED |
| 4 | MOD-IB-04 | 可观测性 | `ib/observability/__init__.py` | 01 | M | PLANNED |
| 5 | MOD-IB-05 | 解析器注册表与格式解析器 | `ib/parsing/{__init__,parsers}.py` | 01,02,04 | H | PLANNED |
| 6 | MOD-IB-06 | OCR 端口与适配 | `ib/ocr/__init__.py` | 01,02,04 | M | PLANNED |
| 7 | MOD-IB-07 | 切分器 | `ib/chunking/__init__.py` | 01,02 | M | PLANNED |
| 8 | MOD-IB-08 | 页面渲染端口与适配 | `ib/rendering/__init__.py` | 01,02,04 | M | PLANNED |
| 9 | MOD-IB-09 | Embedding 端口与适配 | `ib/embedding/__init__.py` | 01,02,04 | H | PLANNED |
| 10 | MOD-IB-10 | VectorStore 端口与适配 | `ib/vectorstore/__init__.py` | 01,02,04 | H | PLANNED |
| 11 | MOD-IB-11 | 台账 | `ib/ledger/{__init__,schema,sqlite_repo}.py` | 01,02,04 | H | PLANNED |
| 12 | MOD-IB-12 | 原文件 BlobStore | `ib/blob/__init__.py` | 01,02,04 | M | PLANNED |
| 13 | MOD-IB-13 | 文档生命周期 | `ib/lifecycle/__init__.py` | 01..05,07,09..12 | H | PLANNED |
| 14 | MOD-IB-14 | 索引重建 | `ib/rebuild/__init__.py` | 01..04,11,12,13 | H | PLANNED |
| 15 | MOD-IB-15 | 检索服务 | `ib/retrieval/__init__.py` | 01..04,09,10 | H | PLANNED |
| 16 | MOD-IB-16 | 专家注册表 | `ib/experts/__init__.py` | 01 | M | PLANNED |
| 17 | MOD-IB-17 | 工具注册与能力摘要 | `ib/tools/__init__.py` | 01,15,16 | M | PLANNED |
| 18 | MOD-IB-18 | 语义路由 | `ib/routing/semantic.py` | 01,09,16 | M | PLANNED |
| 19 | MOD-IB-19 | 意图路由内核 | `ib/routing/intent.py` | 01,16,17,18 | H | PLANNED |
| 20 | MOD-IB-20 | LLM 端点抽象 | `ib/llm/__init__.py` | 01,02,04 | H | PLANNED |
| 21 | MOD-IB-21 | 流式契约与会话 | `ib/streaming/__init__.py` | 01,02,04 | M | PLANNED |
| 22 | MOD-IB-22 | 编排图 | `ib/orchestration/__init__.py` | 01..04,16..21 | H | PLANNED |
| 23 | MOD-IB-23 | HTTP API 与组合根 | `ibweb/*.py` | 01..22 | H | PLANNED |
| 24 | MOD-IB-24 | Web 前端 | `frontend/**` | 23（HTTP/SSE 契约） | M | PLANNED |
| 25 | MOD-IB-25 | 部署运维 | `deploy/**` | 01,02,04 | M | PLANNED |

---

## 4. 实现顺序（6 批；严格等于 MOD 编号升序 = module_design §4.2 拓扑序）

| 批 | 层 | 模块 | 批内门禁（本批完成即自检，不通过不进下一批） |
|----|----|------|--------------------------------------------|
| B1 | L0 | 01, 02, 03, 04 | `selfcheck::core_framework_free` 通过；配置必填校验只报键名不回显值 |
| B2 | L1~L2 | 05, 06, 07, 08, 09, 10 | 纯逻辑单测（切分/注册表分派/魔数）；InMemoryVectorStore 与端口签名一致 |
| B3 | L3 | 11, 12, 13, 14, 15 | 台账状态机 + 租约；`search()` 无异常出口；重建原子切换 |
| B4 | L4-a | 16, 17, 18, 19, 20, 21 | 专家派生访问器一致；`parse_route_output` 脏输出容错；SSE 帧编码 |
| B5 | L4-b | 22 | `build_graph()` 可编译；State reducer 为 `operator.add`；步数上限 8 |
| B6 | L5 | 23, 24, 25 | `manage.py check` 通过；未注入 AuthzPolicy → 启动失败；SSE 头纪律 |

**批间不可跳步**：B1 的契约是 B2~B6 的类型前提；B3 的台账端口是 B6 组合根的装配前提。

---

## 5. IFC-IB 契约落点

| IFC 段 | 契约 | 落点文件 | 符号 |
|--------|------|---------|------|
| 001~012 | 数据结构 / 枚举 / 异常层次 | `ib/core/types.py` `enums.py` `errors.py` | 同名 frozen dataclass / Enum / Exception |
| 021~024 | ConfigurationSource / resolve_project_config / validate_required / GlobalConfig | `ib/config/__init__.py` | `FileConfigurationSource` `DictConfigurationSource` `resolve_project_config` `validate_required` `GlobalConfig` |
| 031~034 | RequestContext / can_manage / can_query / DenyAllPolicy | `ib/context/__init__.py` | `RequestContext` `AuthzPolicy` `DenyAllPolicy` |
| 041~045 | get_logger / log_event / Timer / emit_degrade / redact | `ib/observability/__init__.py` | 同名函数与类 |
| 051~053 | supports / parse / register | `ib/parsing/__init__.py` | `ParserRegistry` + `parsers.py` 四个 `DocumentParser` |
| 061~064 | available / recognize / descriptor / NullOcrEngine | `ib/ocr/__init__.py` | `RapidOcrEngine` `NullOcrEngine` `StubOcrEngine` |
| 071 | Chunker.split | `ib/chunking/__init__.py` | `SlidingWindowChunker` |
| 081~082 | available / render_page | `ib/rendering/__init__.py` | `PdfiumRenderer` `NullRenderer` |
| 090~096, 098 | Embedder 7 方法 + CollectionResolver.resolve | `ib/embedding/__init__.py` | `LocalHttpEmbedder` `FakeEmbedder` `CollectionResolver` |
| 100~110 | VectorStore 11 方法（含 flush） | `ib/vectorstore/__init__.py` | `InMemoryVectorStore` `QdrantVectorStore` |
| 120~131 | LedgerRepository 12 方法 | `ib/ledger/__init__.py` `ledger/sqlite_repo.py` | `InMemoryLedgerRepository` `SqliteLedgerRepository` |
| 131~134 | BlobStore 4 方法 | `ib/blob/__init__.py` | `InMemoryBlobStore` `FsBlobStore` |
| 141~145 | validate_upload / submit_upload / process_pending / delete_document / retry_document | `ib/lifecycle/__init__.py` | `DocumentLifecycleService` |
| 151~156 | plan/start/step/activate/rollback/fingerprint | `ib/rebuild/__init__.py` | `RebuildService` + `fingerprint()` |
| 161~162 | search / search_as_tool | `ib/retrieval/__init__.py` | `RetrievalService` |
| 171~179 | EXPERT_SPECS + 8 个派生访问器 | `ib/experts/__init__.py` | `EXPERT_SPECS` `names()` … `get()` |
| 181~183 | register_tool / build_capability_digest / bind_scope | `ib/tools/__init__.py` | `ToolRegistry` `build_capability_digest` `bind_scope` |
| 191~193 | score_experts / decide / route | `ib/routing/semantic.py` | `SemanticRouter` + 两个纯函数 |
| 201~203 | classify_experts / parse_route_output / guard_against_misroute | `ib/routing/intent.py` | `IntentRouter` + 两个纯函数 |
| 211~215 | build_router / build_expert / build_aggregator / health / describe_egress | `ib/llm/__init__.py` | `OpenAiCompatibleProvider` `FakeLlmProvider` |
| 221~225 | SessionStore 3 方法 + StreamEvent + to_sse | `ib/streaming/__init__.py` | `MemorySessionStore` `StreamEvent` `to_sse` |
| 231~233 | build_graph / run / resume | `ib/orchestration/__init__.py` | `Orchestrator` |
| 241~250 | build_application + 8 个 HTTP 端点 + 鉴权注入 | `ibweb/composition.py` `views.py` `urls.py` `authz.py` | `build_application` `build_deps` + 视图函数 |
| 256~259 | 前端 4 项 | `frontend/src/**` | `UploadPage.vue` `ChatPage.vue` `RebuildPage.vue` `api/client.ts` |
| 261~265 | systemd ×4 / env.example / 启动校验 / 真机清单 / Qdrant 清单 | `deploy/**` + `ibweb/apps.py` | 同名交付物 |

> **编号冲突留痕（MINOR，见 code_review_report FND-xxx）**：`IFC-IB-131` 被 module_design.md §3 MOD-IB-11（`list_chunks`/`list_orphan_doc_ids`）与 §3 MOD-IB-12（`BlobStore.put`）**重复使用**（Ledger 计 120~131 共 12 条 + Blob 计 131~134 共 4 条 = 16 条占用 120~134 的 15 个号）。实现按文档字面编号落点，并在代码注释中以模块前缀消歧。

---

## 6. 依赖与第三方库清单（版本策略：约束 + 部署时锁定）

| 类别 | 库 | 版本策略 | 落点 | 本地可用性（自测机） |
|------|----|---------|------|--------------------|
| Web | `django` | `>=4.2 LTS`，部署锁定 | `ibweb/*` | 6.0.6（可用） |
| Web | `djangorestframework` | 随 Django 主版本 | `ibweb/serializers.py` | 3.17.1（可用） |
| WSGI | `waitress`（主）/ `gunicorn`（备） | 部署锁定 | `deploy/systemd/ib-web.service` | 缺失（部署期装；本地以 `manage.py runserver` 验证） |
| 向量库客户端 | `qdrant-client` | 与服务端大版本匹配 | `vectorstore/__init__.py`（延迟导入） | **缺失** → 走 InMemory 替身 |
| Embedding 运行时 | `FlagEmbedding`（首选）/ `sentence-transformers`（备） | 部署锁定；**由 [TBD-T1] 实测择一** | 不在 `src/`（`ib-embed` 服务侧） | 缺失 |
| PDF 文本（主） | `pypdf` | 部署锁定 | `parsing/parsers.py`（延迟导入） | 缺失 |
| PDF 文本（回退） | `pdfminer.six` | 部署锁定 | 同上 | 缺失 |
| PDF 表格（可选） | `pdfplumber` | 可选，缺失即降级 | 同上 | 缺失 |
| PDF 渲染 | `pypdfium2` | 部署锁定 | `rendering/__init__.py`（延迟导入） | 缺失 |
| DOCX | `python-docx` | 部署锁定 | `parsing/parsers.py`（延迟导入） | 缺失 |
| OCR | `rapidocr-onnxruntime` + `onnxruntime` | 部署锁定 | `ocr/__init__.py`（延迟导入） | onnxruntime 1.27.0 可用；rapidocr 缺失 |
| 编排 | `langgraph` | 主版本随实现锁定 | `orchestration/__init__.py`（延迟导入） | 1.2.8（可用） |
| LLM 客户端 | `langchain` + `langchain-openai` | **pin `<0.3`** | `llm/__init__.py`（延迟导入 + 版本断言告警） | 1.3.3（**违反 pin** → 代码内显式检测并 WARN，见偏差 D-04） |
| 配置解析 | `PyYAML` | 部署锁定 | `config/__init__.py`（延迟导入；缺失时仅支持 JSON） | 可用 |
| 台账 | stdlib `sqlite3` | 随 Python | `ledger/sqlite_repo.py` | 可用 |

**凭据纪律（强制）**：任何 key / token / password **只经环境变量注入**；仓库内只有 `deploy/env.example`（纯占位符）；日志不记正文 / 片段原文 / 凭据。

---

## 7. 测试替身清单落点（REQ-NFR-IB-14 / module_design §8）

| 端口 | 生产实现（落点） | 替身（落点） | 装配开关 |
|------|-----------------|-------------|---------|
| VectorStore | `QdrantVectorStore`（`vectorstore/__init__.py`） | `InMemoryVectorStore`（同文件，暴力余弦） | `IB_VECTORSTORE_BACKEND=qdrant\|memory` |
| Embedder | `LocalHttpEmbedder`（`embedding/__init__.py`） | `FakeEmbedder`（同文件，确定性伪向量） | `IB_EMBED_BACKEND=http\|fake` |
| LlmProvider | `OpenAiCompatibleProvider`（`llm/__init__.py`） | `FakeLlmProvider`（同文件，可编排脏输出/超时） | `IB_LLM_BACKEND=openai_compatible\|fake` |
| OcrEngine | `RapidOcrEngine`（`ocr/__init__.py`） | `NullOcrEngine` / `StubOcrEngine`（同文件） | `IB_OCR_ENABLED=true\|false` |
| PageRenderer | `PdfiumRenderer`（`rendering/__init__.py`） | `NullRenderer`（同文件） | `IB_RENDER_ENABLED=true\|false` |
| LedgerRepository | `SqliteLedgerRepository`（`ledger/sqlite_repo.py`） | `InMemoryLedgerRepository`（`ledger/__init__.py`） | `IB_LEDGER_BACKEND=sqlite\|memory` |
| BlobStore | `FsBlobStore`（`blob/__init__.py`） | `InMemoryBlobStore`（同文件） | `IB_BLOB_STORE_ENABLED=true\|false` |
| SessionStore | `MemorySessionStore`（`streaming/__init__.py`） | 同（自身即内存实现） | `IB_SESSION_BACKEND=memory` |
| AuthzPolicy | 接入方注入（`ibweb/authz.py`） | `DenyAllPolicy`（`context/__init__.py`） | **未注入即启动失败** |
| ConfigurationSource | `FileConfigurationSource`（`config/__init__.py`） | `DictConfigurationSource`（同文件） | `IB_CONFIG_SOURCE=file\|dict` |

**一键离线**：`IB_OFFLINE_MODE=1` → 组合根把上表全部置为替身列（`IB_CONFIG_SOURCE=dict` 除外，仍读文件/环境变量）。

**离线可测纯逻辑单元**（无外部 IO）：`ib/core`（契约）、`ib/config`（合并与校验）、`ib/chunking`（切分）、`ib/parsing`（注册表分派 + 魔数）、`ib/routing/semantic.py`（打分与判定）、`ib/routing/intent.py::parse_route_output`、`ib/rebuild::fingerprint`。

---

## 8. P1 开放问题（OQ-IB-02~08）默认取值与理由

> 政策：**不阻塞**。以下为已确认的合理默认，实现按此落点；均以「可配置 + 单一开关」形态保留后续裁决空间。

| OQ | 采用的默认 | 理由 | 影响面（代码落点） |
|----|-----------|------|------------------|
| **OQ-IB-02** 格式边界 | **v1 落 4 种：`.pdf` / `.docx` / `.md` / `.txt`**；HTML / Excel / PPT **不实现**，按扩展点预留（注册表 `register(ext, parser)`） | requirements_spec §7.2 已给默认；UB-3 仅要求 Word/PDF/Markdown「等」，其余无用户诉求；扩展点已由 AC-IB-04-05 明确要求「新增格式不改主动线」 | `ib/parsing/__init__.py::ParserRegistry`（白名单常量 `SUPPORTED_EXTS`）、`lifecycle::validate_upload` 扩展名校验 |
| **OQ-IB-04** 问答侧终端界面 | **基座自带最小可验证问答入口**（`ChatPage.vue` + `GET /api/chat/stream`），**不做产品化界面**（无登录页、无多会话管理 UI、无 Markdown 富渲染） | requirements_spec §7.2：基座提供最小可验证入口用于验收，完整产品化由接入项目自建；OOS-06 明确「完整问答产品化界面」不在本期 | `src/frontend/src/views/ChatPage.vue`、`ibweb/views.py::chat_stream` |
| **OQ-IB-05** rerank / 混合检索 | **v1 不纳入**；仅稠密向量检索；端口留扩展位 `VectorStore.supports_hybrid_search() -> bool` **显式返回 False**（不静默失败） | requirements_spec §7.2 + architecture ADR-01 Consequences（「未来混合检索须扩展端口，属已知且被接受的演进成本」）；OOS-08 明确不纳入 | `ib/vectorstore/__init__.py::supports_hybrid_search`（两个适配器都实现）、`retrieval`（不做 rerank 阶段） |
| **OQ-IB-06** 中文检索效果评测方法 | **待接入项目提供真实语料构造留出集**；指标**暂用 Recall@5**；基线**不在代码中硬编码阈值** —— 阈值/`top_k` 全部经 `RetrievalConfig` 配置注入，`candidate_count` + 分数量级作为校准证据出口 | requirements_spec §7.2 已给默认；REQ-NFR-IB-05 的验收锚点属目标机实测项（TBD-T12），代码侧只能保证「可配置 + 可观测」 | `ib/config/__init__.py::RetrievalConfig`、`ib/retrieval/__init__.py`（回显 `candidate_count` / `elapsed_ms`） |
| **OQ-IB-07** 写操作确认门（人工确认中间态） | **机制保留、默认关闭**：`GraphConfig.confirmation_gate_enabled: bool = False`；`gate` 节点恒存在（步数上限始终生效），确认分支仅在该开关为真且存在写操作类工具时启用 | requirements_spec §7.2 + architecture §6（「基座不应默认带业务副作用」）+ module_design §7.1（gate 默认关闭） | `ib/orchestration/__init__.py::GraphConfig` / `gate` 节点 |
| **OQ-IB-08** 会话历史范围与隔离 | **会话内隔离、不跨会话注入**；`session_key = f"{project_id}:{actor_id}:{session_id}"` 且读取时**断言前缀 = 当前 project_id，不符即拒（fail-closed）**；历史注入长度上限**可配置**（`SessionConfig.max_history_messages`，默认 20）；路由判据**只取当前提问**（剥离历史前缀） | requirements_spec §7.2 已给默认；FM-7 要求键构造断言；architecture §6 要求「路由只看当前提问」 | `ib/streaming/__init__.py::session_key` / `MemorySessionStore`、`ib/routing/intent.py::classify_experts`（只用 `query`） |

---

## 9. 架构偏差记录

| 偏差ID | 偏差描述 | 原 ADR / 约束 | 偏差原因 | 处置 |
|--------|---------|--------------|---------|------|
| D-01 | 三份 GROUP_B 文档的 `<file_header><status>` 仍为 `DRAFT_FOR_GATE_REVIEW`，而 `phase_status.md` 已记 `GROUP_B status=APPROVED / GR-B-002=PASS` 且三个 phase 均 `status=APPROVED` | 硬约束「status ≠ APPROVED 即 BLOCKED」 | 冲突源为**文件头状态字段未随门控回写**（纯文档一致性问题，非设计未批）。PM 的权威项目状态文件与门控记录（GR-B-002，reviewer=pm-orchestrator，decision=PASS）均为 APPROVED，且调用块显式声明「R1，已通过 GR-B-002」 | **不阻塞**，按 APPROVED 执行；本项作为 MINOR finding 记入 code_review_report，建议 GROUP_B 回写文件头 status |
| D-02 | `IFC-IB-131` 编号在 LedgerRepository（`list_chunks`）与 BlobStore（`put`）**重复** | module_design §2.2 / §3（自称 12+4 条共占 120~134） | 上游文档编号算术缺陷（12+4=16 条需 120~135） | 按字面编号实现，代码注释以 `MOD-IB-11:` / `MOD-IB-12:` 前缀消歧；记 MINOR finding |
| D-03 | 自测机 Python 为 **3.14.6**，超出 tech_stack 的 `>=3.11,<3.14` | tech_stack §1 编程语言行 | 开发机既有环境，不擅自改动（且不属本代理职责） | 自测证据标注「开发机 3.14.6」；部署目标机须以 `venv` 满足版本约束后才作为验收证据 |
| D-04 | 自测机 `langchain-openai` 为 **1.3.3**，违反 `pin <0.3` | tech_stack §3 / 冻结约束 9 | 开发机既有全局环境，本代理不改动全局依赖 | **实际实现与本节初稿不同**：不是「WARN 不抛错」，而是 `ib/llm/__init__.py::assert_langchain_openai_version()` 在**构造 provider 时直接抛 `StartupError`**。理由：0.3.x 移除 `_convert_chunk_to_generation_chunk` 会让**流式**输出静默退化为一次性返回 —— 只 WARN 等于把 FreeArk 已发生过的生产漂移原样复刻。已实证该断言会拒绝本机的 1.3.3（见 code_review_report §2.5）；离线装配走 `fake` 后端，不受影响。记 MAJOR finding（部署前必须满足） |
| D-05 | 台账 DDL 的手写 scoped 迁移以 **`.sql` + 运行时 `ensure_schema()`** 双形态交付，未走 Django migration 机制 | ADR-07-R1「手写 scoped 迁移，禁 makemigrations 全产物」 | 台账不经 Django ORM，故 Django migration framework 不适用；但 DDL 仍须「手写、scoped、可审计」 | DDL 单一真源于 `ib/ledger/schema.py`，同内容导出为 `deploy/migrations/001_ledger_init.sql`（供 DBA 审阅与手工回放）；**仓库内不出现任何 Django 自动迁移产物**。注意：`WAL` / `busy_timeout` 是**连接级** PRAGMA，不在该 .sql 内，已在文件头写明（否则会误以为「有了迁移就有 WAL」） |
| D-06 | `src/` 下未实现 MOD-IB-25 的 systemd 单元**安装**动作，只交付单元文件与清单文本 | scope_boundary（GROUP_E 冻结） | 本轮明确不做部署动作 | 单元文件与 `.env.example` 作为**交付物**落盘 `src/deploy/`，不写目标机 |
| D-07 | 新增 `src/ibweb/worker.py`（队列消费 / 租约回收 / 重建推进）与 `src/ibweb/bootstrap.py`（`--ensure-schema` 启动前置） | §2 文件树初稿未列 | 依据 MOD-IB-11「台账表兼作队列与 worker 租约」必须有执行体；`ib-web` 的 `ExecStartPre` 需要一个可独立执行的 schema 保证命令 | 两者均属 MOD-IB-23（组合根/HTTP 层）职责内，未新增模块；worker **不**调用 `activate_version`（切换只由重建流程在全部成功后执行） |
| D-08 | 新增 `deploy/config.example.json`、`requirements-offline.txt`、`deploy/migrations/` | §2 文件树初稿未列 | 前者为配置模板（纯占位符）；后者支撑「离线装配不装 Qdrant/pypdf/langgraph 也能跑自检」 | 均为 MOD-IB-25 交付物范畴；`requirements-offline.txt` 只含 Django/DRF/langgraph/core/pypdf 级别的裁剪集 |
| D-09 | 文件与符号命名同义不同名：计划 `ib/parsing/parsers.py` → 实际 `pdf_parser.py` + `text_parsers.py`；计划符号 `DocumentLifecycleService` → 实际类名 `DocumentLifecycle`；module_design 写 `.env.example` → 实际 `deploy/env.example`；module_design 写 `apiClient.ts` → 实际 `frontend/src/api/client.ts` | module_design §3 内的路径/符号写法 | 拆分 pdf/text 解析器是为了让「三路径 PDF」与「文本系」两类实现各自独立可测；其余为路径风格统一 | **IFC 编号与契约均未变**，仅实现位置/符号名不同；已在此列明以便复核（同一 IFC-IB-259 落在 `src/api/client.ts`） |
| D-10 | `related_images` 事件种类保留在枚举/契约中，但本基座**无生产端**（无任何模块负责图片引用提取） | module_design §7.3 事件 kind 列表；requirements_spec 标为「可选的附带产物」 | 前端**不猜负载结构**（不发明未定义的接口），只做保守展示 | 记 MAJOR finding M-02，上报 PM 决定「指派提取器」或「从契约移除该 kind」 |
| D-11 | 会话历史为**内存**实现（`session.backend: memory`），进程重启即丢 | module_design 默认值 | 遵循默认；GR 阶段未要求持久化 | 记 MINOR finding M-01；若接入项目要求审计连续性，需上游决定新增持久化会话存储 |

**无架构级偏差**：25 模块划分 / 13 端口 / 58 条 IFC 编号 / DAG 依赖边 / 配置键名 / fail-open 与 fail-closed 语义划分，全部与 module_design.md R1 一致，未新增模块、未新增依赖边、未改名任何配置键。

**本轮修复的 4 个 CRITICAL 与 6 个 MAJOR**（细节见 `docs/code_review_report.md` §1.4 / §3）：
`FND-IB-21-001`（`StreamEvent` 同名双定义）、`FND-IB-23-001`（读路径闭包 `NameError`，被 fail-open 掩盖）、
`FND-IB-23-002`（往 `build_ledger`/`build_blob_store` 传段配置而非 GlobalConfig，开关静默失效）、
`FND-IB-24-001`（前端 SSE 分帧 `-1` 哨兵 × `>= 0` 判断，导致正文全丢且不报错）；
以及 `LOG_FIELDS` 白名单缺 `egress_*`/`backend`、`ib/tools` 的 `setdefault` 可被覆盖（跨项目读路径）、
`stream_mode="updates"` / `gate` 回写 `{}` / reducer 只加并行键、清单初稿三条错命令。

---

## 10. 配置键清单（不得新增/改名，module_design §5 / §3 MOD-IB-23）

| 键 | 取值 | 默认 | 读者 |
|----|------|------|------|
| `IB_VECTORSTORE_BACKEND` | `qdrant` \| `memory` | `qdrant` | `ibweb/composition.py` |
| `IB_EMBED_BACKEND` | `http` \| `fake` | `http` | 同上 |
| `IB_LLM_BACKEND` | `openai_compatible` \| `fake` | `openai_compatible` | 同上 |
| `IB_OCR_ENABLED` | `true` \| `false` | `true` | 同上 |
| `IB_RENDER_ENABLED` | `true` \| `false` | `true` | 同上 |
| `IB_LEDGER_BACKEND` | `sqlite` \| `memory` | `sqlite` | 同上 |
| `IB_BLOB_STORE_ENABLED` | `true` \| `false` | `true` | 同上 |
| `IB_SESSION_BACKEND` | `memory` | `memory` | 同上 |
| `IB_CONFIG_SOURCE` | `file` \| `dict` | `file` | 同上 |
| `IB_OFFLINE_MODE` | `0` \| `1` | `0` | 同上（置 1 = 全替身） |

**业务/凭据类环境变量**（仅登记键名，无值）：`IB_LEDGER_PATH`、`IB_BLOB_ROOT`、`IB_QDRANT_URL`、`IB_EMBED_URL`、`IB_LLM_MODEL`、`IB_LLM_BASE_URL`、`IB_LLM_API_KEY`、`IB_LOG_LEVEL`、`IB_CONFIG_FILE`、`IB_WORKER_LEASE_SECONDS`、`IB_MAX_UPLOAD_MB`、`IB_CHUNK_SIZE`、`IB_CHUNK_OVERLAP`。

---

## 11. 本地自测计划与实际执行（无外网；不连生产库 / 不连真实 Qdrant / DeepSeek / ib-embed）

> 纪律：**无实跑证据不声称「通过」**。以下各行均为本轮真实执行过的命令，
> 原始输出见 `docs/code_review_report.md` §2。

| 命令 | 结果 | 证据位置 |
|------|------|---------|
| `python -X utf8 scripts/selfcheck.py` | **15/15 PASS**（含 framework-free、无 FastAPI/uvicorn/channels/redis、无 fitz/PyMuPDF、端口一致性、AuthzPolicy 未注入即启动失败、配置只报键名、魔数拒改名、台账状态机+租约（WAL）、隔离 scope 必填、检索正常路径不降级、fail-open 降级、SSE 帧与 done 终止、编排事件顺序、HTTP 契约、部署模板无凭据） | code_review_report §2.1 |
| `IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=file IB_CONFIG_FILE=deploy/config.example.json IB_OFFLINE_TOKEN=offline-test-token python -X utf8 manage.py check --settings=ibweb.settings` | `System check identified no issues (0 silenced).` + 启动日志含外发声明三键与 `backend=` 汇总 | §2.2 |
| `node --experimental-strip-types scripts/sse_parser_selfcheck.mts` | **9/9 PASS**（修复 FND-IB-24-001 前为 3 FAILED —— 修复前后输出均已归档） | §2.4 |
| `grep -rniE "^[^#]*(import\|from)\s+(fitz\|pymupdf\|fastapi\|uvicorn\|channels\|redis\|aioredis)" src` | 无匹配 | §2.5 |
| `python -c "from ib.llm import assert_langchain_openai_version as a; a()"` | 在本机（1.3.3）**抛 `StartupError`** —— 钉版约束真的在生效 | §2.5 |
| 检查清单 B4/B6/B7 命令形状核验（fake/离线装配） | 形状正确；核验中**纠正了清单初稿的 3 处错误**（`embed()` 不存在、`provider.complete()` 不存在、ib-embed 端口 18080→8100） | §2.6 |

**不在本轮范围 / 未执行（已在报告中登记为遗留项）**：
正式测试套件与测试报告（GROUP_D）；部署与真机验证（GROUP_E）；
`npm install` / `vue-tsc --noEmit` / `vite build`（安装依赖会访问外部包源，与「严禁连接外部服务」冲突 → 遗留 L-02）；
Qdrant / OCR / bge-m3 真装验证与 PDF 三路径真跑（本机缺包 → 遗留 L-01；目标机按 `deploy/checklists.txt` B4/B5 执行，AC-IB-12-04）。

---

## 12. R2 增量实现（L-03 + M-02；追加，不改写 §1~§11）

> **性质**：R2 是**追加式增量**，只做两件事。R1 的 69 个文件**一个都没有重写**；
> 下表「改动」一律为**追加段落 / 追加方法 / 追加常量 / 追加行**（唯一例外是
> `ChatPage.vue` 中 R1 遗留的 `extras` 占位结构，因 M-02 把它**落成真功能**而移除 —— 见 §12.7 D-R2-05）。
> 依据：`module_design.md` R2 §2.2.1 / §3 MOD-IB-01/09/13/21/23/24/25/26、
> `architecture_design.md` R2 §2.0.1（ADR-02-R2 附注）、`docs/ib_embed_service_contract.md`。

### 12.1 两个任务与落点总览

| 任务 | 内容 | 新增模块 | 新增文件 | 新增 IFC |
|------|------|---------|---------|---------|
| **L-03** | `ib-embed` 服务端（bge-m3 常驻 HTTP 服务）+ 第三种 Embedder 形态 | **MOD-IB-26**（顶层独立包 `ib_embed/`） | 4（`ib_embed/{__init__,config,runtime,server}.py`）+ 1（`ib/embedding/inproc.py`）+ 2（部署交付物） | 266~275、286 |
| **M-02** | 页面图关联的生产（绑定→落库）与读路径（流事件 + 取图端点 + 前端渲染） | 无（落在既有 MOD-IB-01/11/13/21/23/24） | 0 | 276~284 |

### 12.2 文件树增量

**新增文件（7 个）**：

```
src/ib_embed/__init__.py           # 包门面（显式声明「本包不被任何 ib.* 模块 import」）
src/ib_embed/config.py             # IFC-IB-273/274：11 个 IB_EMBED_* 键的**封闭集合** + 启动期校验（只报键名）
src/ib_embed/runtime.py            # IFC-IB-270~272：可替换推理运行时（Runtime 端口 + 三候选 + FakeRuntime + UnavailableRuntime）
src/ib_embed/server.py             # IFC-IB-266~269：线协议（/embed /healthz /warmup /descriptor）+ 有界并发 + 有界队列
src/ib/embedding/inproc.py         # IFC-IB-275：InProcessBgeM3Embedder（第三适配器，**不 import MOD-IB-26**）
src/deploy/ib-embed.env.example    # IFC-IB-286：第二份 EnvironmentFile 模板（仅 11 键名，无凭据）
src/deploy/migrations/002_chunk_image.sql  # IFC-IB-278/281：chunk_image 表手写 scoped DDL（+ ON DELETE CASCADE）
```

**改动文件（18 个，全部为追加/最小修改）**：

| 文件 | 模块 | 改动内容 |
|------|------|---------|
| `src/ib/core/types.py` | 01 | 追加 `PageImageRef` / `PageImageBinding` / `PageImageSourceKindLiteral` / `RelatedImageItem` / `RelatedImagesPayload` / `ChunkImageRecord`；**既有 `ParsedChunk` / `RetrievedChunk` 字段集合一字未改** |
| `src/ib/core/ports.py` | 01 | `LedgerRepository` 追加 `upsert_chunk_images` / `list_chunk_images` / `get_chunk_image`（R2 段注释说明「类型定义在 01 是为避免 11→13 反向边」） |
| `src/ib/core/__init__.py` | 01 | `__all__` 追加 5 个新类型名；已登记重复号 `IFC-IB-131` **不动** |
| `src/ib/config/__init__.py` | 23 | `IB_RUNTIME_ENV_KEYS` 追加 `IB_EMBED_MODEL_PATH`（**键名早已在服务端登记**，此处只登记进客户端集合）；`IB_EMBED_BACKEND` 取值域 `{http,fake}` → `{http,inproc,fake}`；`inproc` 的必填键校验 |
| `src/ib/lifecycle/__init__.py` | 13 | 追加 IFC-IB-277 `bind_page_images`（纯函数）/ IFC-IB-278 `persist_page_images` / IFC-IB-280 `_process_one` 九步写序 / IFC-IB-281 `delete_document` 仅追加**不变式 docstring**（代码零改动） |
| `src/ib/ledger/schema.py` | 11 | 追加 `chunk_image` 表 DDL（含 `(project_id,kb_id,doc_id,page_or_section,image_id)` 唯一键 + FK `ON DELETE CASCADE`） |
| `src/ib/ledger/sqlite_repo.py` | 11 | 实现三条 R2 端口方法（复用 `_scope_clause` 单点下推；`upsert` = 同 doc_id 先删后写，单事务） |
| `src/ib/ledger/__init__.py` | 11 | 内存替身 `InMemoryLedgerRepository` 同步实现三条方法（级联删除由 `mark_deleted` 显式对齐） |
| `src/ib/streaming/__init__.py` | 21 | 追加 `IMAGE_ENDPOINT_TEMPLATE` / `related_image_url` / `related_images_event` / `related_images_json` / `related_images_of`；**`StreamEventKind` 取值集合不变**（`related_images` R1 已在枚举内） |
| `src/ib/orchestration/__init__.py` | 22 | 追加可选关键字 `related_images_provider`（`build_graph` 同）；`run()`/`arun()` 在 `content` 之后、`done` 之前产出 `related_images`（**失败静默不发事件**，不打断流） |
| `src/ib/embedding/__init__.py` | 09 | `build_embedder` 值域扩展（`inproc` 分支）；导出 `InProcessBgeM3Embedder`；**`http` 仍为默认落点** |
| `src/ibweb/views.py` | 23 | 追加 `file_image_endpoint`（IFC-IB-283）+ 固定 ext→MIME 表 + `_blob_ref_of_rel_path`；`/healthz/deps` 字段集**不变** |
| `src/ibweb/urls.py` | 23 | 追加路由 `api/files/<doc_id>/images/<image_id>`（`APPEND_SLASH=False`，避免 301 丢掉 `Authorization`） |
| `src/ibweb/composition.py` | 23 | 追加 `_make_related_images_provider` 并注入 `orchestrator_for`（组装接缝；R2 命中为空 → 不发事件） |
| `src/deploy/systemd/ib-embed.service` | 25 | **确认** `ExecStart=… -m ib_embed.server`；`MemoryMax=2560M` 与 `IB_EMBED_MEMORY_LIMIT_MB=2560` 数值一致（注释写明「改一处必须改另一处」） |
| `src/frontend/src/api/client.ts` | 24 | 追加 `RelatedImageItem` / `RelatedImagesPayload` / `fileImageUrl` / `ApiClient.fetchFileImage`（取字节转 `blob:` URL） |
| `src/frontend/src/views/ChatPage.vue` | 24 | 追加 `related_images` 分支 + 缩略图行（正文**下方**、可点击取原图、失败静默隐藏、卸载释放 blob URL） |
| `src/scripts/selfcheck.py` | 23 | 追加 9 个 R2 用例 + `main()` 注册 + `port_conformance` 补两形态（见 §12.6） |

### 12.3 实现顺序（R2 追加批次，仍严格按 MOD 编号升序 = 拓扑序）

| 批次 | MOD | 依据 |
|------|-----|------|
| B7 | **MOD-IB-26**（`ib_embed/`） | 只有出边到 {01,02,04}、**无入边**（C8 硬约束），故先做可独立验证 |
| B8 | MOD-IB-01（R2 类型/端口）+ MOD-IB-11（表与端口实现） | 编号小者先；11 依赖 01 的类型 |
| B9 | MOD-IB-13（绑定/落库/九步写序）+ MOD-IB-09（`inproc` 形态） | 13 依赖 11；09 依赖 01 |
| B10 | MOD-IB-21（事件载荷）+ MOD-IB-22（生产接缝）+ MOD-IB-23（端点/装配） | 21 依赖 01；22 依赖 21；23 依赖 13/22 |
| B11 | MOD-IB-24（前端）+ MOD-IB-25（部署模板） | 24 依赖 23 的契约；25 依赖 26 的键清单 |

**无环性**：新增模块 MOD-IB-26 的编号 26 大于其全部依赖 {01,02,04}，且**不被任何模块 import**，
故「编号即拓扑序」不变式仍成立（`module_design.md` R2 §4.2）。

### 12.4 IFC-IB 编号落点（266~286；285 预留未用）

| IFC | 模块 | 落点（文件） | 离线验证用例 |
|-----|------|-------------|-------------|
| 266 | MOD-IB-26 | `ib_embed/server.py` `POST /embed` | `ib_embed_wire_protocol` |
| 267 | MOD-IB-26 | 同上（维度三方一致性） | 同上（`dim`/`len(vec)`/`count`） |
| 268 | MOD-IB-26 | 同上（错误码表 + 4xx/5xx 分类） | 同上（400/404/409/503/500 + `retry_after_s`） |
| 269 | MOD-IB-26 | 同上 `GET /healthz`（**永不 5xx**） | 同上（含 `UnavailableRuntime` → 200 + `ok=false`） |
| 270 | MOD-IB-26 | 同上 `POST /warmup`（幂等） | 同上（连发两次均 200） |
| 271 | MOD-IB-26 | 同上 `POST /descriptor`（**恰五字段**） | 同上（字段集合断言） |
| 272 | MOD-IB-26 | `config.py` 批上限 + `server.py` 400 回显 `max_batch` | 同上 |
| 273 | MOD-IB-26 | 服务端**不区分冷热**（无超时/重试键） | `ib_embed_config_keys`（11 键闭集） |
| 274 | MOD-IB-26 / 09 | `ib_embed/config.py` + `ib/embedding/__init__.py::build_embedder` | `ib_embed_config_keys` + `embed_three_form_conformance` |
| 275 | MOD-IB-09 | `ib/embedding/inproc.py` | `embed_three_form_conformance` + `port_conformance` |
| 276 | MOD-IB-01 | `ib/core/types.py` | `page_image_binding_and_ledger` |
| 277 | MOD-IB-13 | `ib/lifecycle/__init__.py::bind_page_images` | `page_image_binding_and_ledger` |
| 278 | MOD-IB-13 / 11 | `persist_page_images` + `upsert_chunk_images` | 同上 + `lifecycle_nine_step_order` |
| 279 | MOD-IB-01 | `ChunkImageRecord`（幂等键） | `page_image_binding_and_ledger` |
| 280 | MOD-IB-13 | `_process_one` 九步写序 | `lifecycle_nine_step_order` |
| 281 | MOD-IB-13 / 11 | 级联删除不变式（DDL `ON DELETE CASCADE`） | `page_image_binding_and_ledger`（**SQLite 真库**） |
| 282 | MOD-IB-21 | `ib/streaming/__init__.py::related_images_event` | `related_images_events` |
| 283 | MOD-IB-23 | `ibweb/views.py::file_image_endpoint` | `file_image_endpoint` |
| 284 | MOD-IB-24 | `ChatPage.vue` 渲染约束 | `frontend_image_discipline` |
| 286 | MOD-IB-25 | `deploy/ib-embed.env.example` | `deploy_templates_have_no_secrets` |
| 285 | — | **预留未分配**（未使用，不得回收改义） | — |

**容量／纪律项**：`IB_EMBED_MAX_BATCH(服务端) ≥ cold_batch_size(客户端默认 16)`；
`IB_EMBED_MEMORY_LIMIT_MB == MemoryMax`；服务端**不得**出现 `IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*`。

### 12.5 配置键增量

| 键 | 变化 | 读者 |
|----|------|------|
| `IB_EMBED_BACKEND` | 取值域 `{http, fake}` → **`{http, inproc, fake}`**（键名与默认 `http` 不变） | `ibweb/composition.py`（经 `build_embedder`） |
| `IB_EMBED_MODEL_PATH` | **登记进客户端集合**（键名早已在服务端登记，**非新增键**）；`inproc` 形态下为必填 | `ib/config/__init__.py` + `ib_embed/config.py` |
| 其余 10 个 `IB_EMBED_*` | **键名清单（封闭集合）唯一落点**在 `ib_embed/config.py`；模板见 `deploy/ib-embed.env.example` | `ib_embed/config.py` |

**凭据纪律**：`ib-embed` 服务**不需要任何令牌**，`ib-embed.env.example` 内**不含任何凭据**
（自检用例 `deploy_templates_have_no_secrets` 扫描真实凭据形态正则）。

### 12.6 R2 本地自测（真实执行；命令与原始输出见 `docs/code_review_report.md` §9）

| 命令 | 结果 |
|------|------|
| `python -X utf8 -m compileall -q .` | 退出码 **0**（无语法错误） |
| `PYTHONUTF8=1 python -X utf8 scripts/selfcheck.py` | **24/24 PASS**（R1 的 15 例全绿 + R2 新增 9 例全绿） |

R2 新增 9 例：`ib_embed_config_keys` / `ib_embed_isolation` / `embed_three_form_conformance` /
`ib_embed_wire_protocol`（**真监听回环端口的真 HTTP**）/ `page_image_binding_and_ledger`（InMemory + **真实 SQLite**）/
`lifecycle_nine_step_order`（记录型代理观测写序）/ `related_images_events` / `file_image_endpoint`（200/404/403/503/400/405）/
`frontend_image_discipline`。

**C5 合规声明**：以上用例**全程不联网**、**不连任何生产库或外部服务**（ib-embed 服务端用回环随机端口 + 进程内 `FakeRuntime` 伪向量），
**未下载任何 bge-m3 权重**。

### 12.7 架构偏差记录（R2）

| 偏差ID | 偏差描述 | 原 ADR / 约束 | 原因与处置 |
|--------|---------|--------------|-----------|
| D-R2-01 | `PageImageRef.blob_ref` 恒为 `None`（页面图**字节未落盘**）：`ib/parsing/pdf_parser.py` 的 OCR 路径在内存中消费页面图后即弃，未产出可持久化字节 | ADR-05（原文件内容寻址 ON）只约束**原始文件**，未规定页面图字节的留存 | **不伪造路径**：`bind_page_images` 诚实登记 `blob_ref=None`；因此 IFC-IB-283 对**真实 R2 数据**将返回 **404**（契约 §7.4 明文允许）。记 **P1 开放问题**，不阻塞（见 code_review_report §9.3） |
| D-R2-02 | `related_images` 生产接缝已装配但**当前恒为空**：R1 编排器只把工具**名称/描述字符串**交给 LLM，从不执行工具、也拿不到检索命中，故 provider 被调用时命中列表为空 → **不发事件**（正确行为） | IFC-IB-282 要求「有图才发」 | **接缝正确但未点亮**。不发明未定义接口、不伪造命中；记 **P1 开放问题**（读路径改为检索依据化后自动点亮，代码无需改）。见 code_review_report §9.3 |
| D-R2-03 | Content-Type 由 `ibweb/views.py` 内的**固定 ext→MIME 表**决定，不用 `mimetypes.guess_type` | ADR-11（响应头纪律） | `mimetypes` 在 Windows 上读注册表，同一份代码在不同机器上会给出不同 `Content-Type`，破坏 IFC-IB-283 的 `image/*` 契约；未知扩展名诚实回落 `application/octet-stream`（页面图为栅格，正常路径必命中表） |
| D-R2-04 | 图片端点的**跨项目**请求返回 **404**（不是 403），而上传端点跨项目 kb_id 为 **403** | module_design §1.4 第 2 条（反存在性探测） | 两处**刻意不同**：上传时 `kb_id` 是**请求方声明**的（属主体性质 → 403）；取图时 `(doc_id, image_id)` 是**被寻址的资源**，403 会变成「该图存在但不属于你」的存在性预言机。与契约「不区分不存在与不属于你」一致 |
| D-R2-05 | `ChatPage.vue` 移除了 R1 的 `extras` 占位结构与 `FND-IB-24-001` 注释 | R1 §2 文件树 | 该占位结构正是 M-02 要落成的真功能（`related_images`）的宿主；R1 遗留注释描述的是已在 R1 修复的缺陷，留着会误导复核。**唯一一处 R1 行的删除**，逐行理由见 code_review_report §9.4 |
| D-R2-06 | `IB_EMBED_MEMORY_LIMIT_MB=2560` / `MemoryMax=2560M` 的目标机内存前提（4GB vs 实为 11GiB）沿用架构侧 **[TBD-T4]/[TBD-T16]**，未在本轮实测重定 | 架构 §9 TBD | 本轮无目标机访问（GROUP_E 不触碰）；数值一致性已由自检与注释锁定，重定只需改两处数值（非结构改动） |

**无架构级偏差**：R2 **未新增端口**（仍 13）、**未改动** `IFC-IB-001~265` 一字、
未改任何既有配置键的键名或默认值、未新增依赖边（MOD-IB-26 只有出边且无入边）、DAG 仍无环。

---

## 13. R3 增量实现（缺陷修复；追加，不改写 §1~§12）

> **性质**：**只修缺陷、不新增能力**。输入 = `docs/test_report.md` §5 登记的两个缺陷
> （FND-GROUP-D-02 MAJOR / FND-GROUP-D-01 MEDIUM）。**未新增模块**（仍 26）、**未新增端口**（仍 13）、
> **未改任何 IFC 签名或编号**、**未改任何配置键的键名或默认值**、**未新增依赖边**。

### 13.1 结论摘要

| 缺陷 | 根因 | 修法 | 证据 |
|------|------|------|------|
| FND-GROUP-D-02（MAJOR） | `delete_document` 依赖「向量库恰好已被别处绑定」；但组合根启动期只 `ensure_collection`（建库）而**不** `bind_collection` → 「上传后立刻删除」窗口内 `delete_by_doc` 抛 `StartupError` → 500 + 台账行残留 → worker 照常索引 → **用户以为删了、内容仍在作答** | ① `delete_document` 先经 `CollectionResolver` **自绑**写路径 collection 再删（`_bind_write_collection`）；② 台账行删除后追加一次「竞态清扫」；③ `_process_one` 开头与 `process_pending` 的分类分支让「行已删」**安全跳过**（`skipped`）并清掉本次写入的向量 | `docs/evidence/groupc_r3_after_symptoms.log`、(a)(b)(c) 三段 |
| FND-GROUP-D-01（MEDIUM） | 摘要走**进程级 `default_registry`**（空），而自带工具只登记进 `bind_tools()` 内的**局部**注册表 → 摘要恒空、L2 路由提示恒为「（无可用工具）」 | ②（**采纳**）把「自带工具清单」收敛为**唯一登记点** `register_builtin_tools(registry)`，并在装配期用同一函数登记进 `default_registry`；`bind_tools` 也改走该函数 | `docs/evidence/groupc_r3_after_symptoms.log` 第一段 |

### 13.2 FND-GROUP-D-02 —— 修法选择与理由

**采纳：删除路径自绑 collection（现取现绑），而不是「把未绑定当作 0 条」或「启动期预绑」。**

| 候选修法 | 评估 | 结论 |
|---------|------|------|
| A. `except StartupError: vectors_deleted = 0` | 具**特定**异常类型，看似最小；但它把「未绑定」当成「无派生物」——对 **Qdrant 这类持久化后端**，「未绑定」只表示**本进程还没绑**，磁盘上完全可能有既有向量。于是删除会留下「台账行已删、向量仍在」的**幽灵向量**（正是本次要消除的那一类残留），且被静默吞掉 | **否决** |
| B. 启动期给每个项目预绑 collection | 只能绑**一个**（`bind_collection` 是单值），而进程要服务多项目；预绑无法覆盖多项目场景 | **否决** |
| C. **删除路径自绑**（`_bind_write_collection`：`project_provider` → `CollectionResolver.resolve` → `assert_prefix` → `bind_collection`），与 `_process_one` 第 6 步、`RetrievalService` 第 1 步**同源同形** | 唯一真源仍是 `CollectionResolver`（FM-5），**绝无** `ib_<project>_v1` 之类的静默回退；「尚无事发生」时表现为 collection 已建但为空 → `delete_by_doc` 自然返回 **0**（诚实语义，不是被吞掉的异常）；真故障照旧上抛（Qdrant 不可达 → `DependencyUnavailableError` → 503 fail-closed） | **采纳** |

**附加硬化（同属本缺陷的「不得产生幽灵文档」要求）**：

1. **台账行删除后的竞态清扫**（`delete_document` 第 4 步再做一次 `delete_by_doc`）。
   覆盖的窗口：删除路径的第一次向量清扫与台账行删除**之间**，worker 正好完成了 upsert ——
   此时 `mark_indexed` 会成功（行还在），仅靠「先删派生物后删台账」拦不住。
   这是把既有的顺序不变式**补强**，不是改向：两次清扫都发生在权威侧之前/之后的**派生物**上。
   `vectors_deleted` 计数把两次结果相加（正常路径第二次恒为 0，语义与 IFC-IB-281 一致）。
2. **处理侧安全跳过**：`_process_one` 开头若台账行已不在 → 抛既有的 `_DeletedConcurrently`（该异常类
   R1 就定义了，但**从未被抛出**——本次把它接上）；`process_pending` 新增 `NotFoundError` 分类分支：
   仅当**行确实不在**时判为并发删除 → `skipped` + `_discard_written_vectors`，
   否则（行还在 → 真故障）仍走原来的 `failed` 路径。**日志枚举与 `ProcessReport` 字段不变**。

**为什么不用宽泛 `except Exception`**：真故障必须继续可见。唯一一处宽捕获在
`_discard_written_vectors`（清掉「台账行已不存在」的文档的残留向量），其失败只记 WARNING ——
因为该文档对读路径**已经不可见**，且删除侧的第 4 步是兜底；把 `skipped` 翻成 `failed`
等于把用户的主动删除报成系统故障。

**保留不变的既有语义**（逐条对照 gate 判据）：文档确实不存在 → `NotFoundError` → 404；
签名 / 返回类型 / `DeleteReport` 三计数语义不变（IFC-IB-281）；「先删派生物、后删权威台账」顺序不变。

### 13.3 FND-GROUP-D-01 —— 修法选择与理由

**采纳：方案②（让 `default_registry` 承载基座自带工具），并以「唯一登记点」实现；未采纳方案①。**

- **为什么方案①单独不够**：`Deps.capability_digest` 只被装配结果**导出**，而真正进提示的是
  `ib/routing/intent.py::IntentRouter._capability_digest()` → **无参** `build_capability_digest()`
  → `default_registry`。只把绑定期的局部注册表接进 `Deps` 字段，**路由提示仍会是「（无可用工具）」**，
  gate 判据的第三条不成立。① 与 ② 对 `Deps` 字段的效果相同，但只有 ② 同时修好提示。
- **为什么不改路由层**：`intent.py` 的 `or "（无可用工具）"` 是**合法兜底**（摘要函数异常/为空时的可读占位），
  在路由层塞一个假摘要会让「提示与真实工具集漂移」重新出现（IFC-IB-182 明令摘要必须**由注册表纯派生**）。
- **单一登记点（防漂移）**：新增 `register_builtin_tools(registry)`，`bind_tools` 与装配期登记
  **共用同一函数** → 「实际被绑定的工具」与「摘要里声称的工具」不可能再分叉。
- **不构成跨项目泄漏**：注册表里只有 `ToolSpec`（纯声明）+ **未绑定**的实现函数；
  `scope` 是实现的**关键字参数**，只在 `bind_scope(...)` 构造期由闭包注入（ADR-09）。
  因此进程级注册表中**不存在任何项目作用域**，`bind_tools` 仍**每项目新建注册表**（纪律不变）。
- **登记时机**：放在 `_assemble()` 内（而非 import 期）——保持「`default_registry` 由组合根在**装配期**填充」
  的既有文档语义，且不给模块导入附加副作用。
- **顺带订正**：`SEARCH_TOOL_SPEC.description` 原先把「（需要范围绑定）」手写进描述，而
  `build_capability_digest` 在 `needs_scope=True` 时**也会**追加同一后缀 —— 摘要此前恒空，
  这个重复一直不可见；点亮后会出现「…（需要范围绑定）（需要范围绑定）」。故从描述里移除，
  由摘要统一附加（**描述文本变更，工具名/契约键不变**）。

### 13.4 附带订正（低优先级）

| 项 | 变更 | 理由 |
|---|------|------|
| `src/deploy/checklists.txt` B6 段 | 删除「`ib-embed` 服务端不在 MOD-IB-01~25 任一模组范围内 / 需由其归属方提供」的待办，改为「已有模块归属 = **MOD-IB-26**；线协议契约唯一落点 = `docs/ib_embed_service_contract.md`（IFC-IB-266~274）」 | 该表述是 **R2 前的状态**（L-03），R2 引入 MOD-IB-26 后已过期。属**文档陈旧**订正，无代码影响 |

### 13.5 P1 开放问题（OQ-IB-02~08）—— 本轮逐条核对结论

**本轮**未触碰 §8 中任何默认值。逐条：OQ-IB-02（格式边界）无改动；OQ-IB-04（终端界面）无改动；
OQ-IB-05（混合检索）无改动；OQ-IB-06（评测方法）无改动；OQ-IB-07（写操作确认门）无改动 ——
本轮只让**已有**自带工具（`search_knowledge`，只读）出现在路由提示里，未新增任何工具、未启用 gate 分支；
OQ-IB-08（会话历史）无改动。
**前向说明（不改变任何默认值）**：若将来按 OQ-IB-07 引入写操作类工具，其登记应同样经
`register_builtin_tools` 一并登记（否则摘要会再次与实绑工具漂移，即本缺陷的复发形态）。

### 13.6 架构偏差记录（R3）

| 偏差ID | 偏差描述 | 原 ADR / 约束 | 偏差原因与处置 |
|--------|---------|--------------|-------------|
| D-R3-01 | `SEARCH_TOOL_SPEC.description` 文案变更（去掉手写的「（需要范围绑定）」后缀） | module_design §3 MOD-IB-17 / IFC-IB-182 | 文案级订正：后缀由 `build_capability_digest` 依 `needs_scope` 统一附加；不改工具名、不改摘要函数签名与语义 |

**无架构级偏差**：未新增/删除模块（仍 26）、端口（仍 13）、IFC 编号、依赖边；
`IFC-IB-141~145` / `IFC-IB-181~183` / `IFC-IB-280/281` 的**签名与返回类型一字未改**；
冻结约束（Django + 原生 SSE、Qdrant 双适配器、collection-per-project、PDF 四件套禁 PyMuPDF、
`langchain-openai` pin、IC-IB-01 前端封装）**全部未触碰**。

### 13.7 R3 变更文件清单与验证证据

| 文件 | 变更性质 | 对应缺陷 |
|------|---------|---------|
| `src/ib/lifecycle/__init__.py` | `delete_document` 自绑 collection + 竞态清扫；新增 `_bind_write_collection` / `_discard_written_vectors` / `_fail_document`；`_process_one` 开头加「行已删即跳过」；`process_pending` 加 `NotFoundError` 分类分支 | FND-GROUP-D-02 |
| `src/ibweb/composition.py` | 新增 `register_builtin_tools`（唯一登记点）；`bind_tools` 改走它；`_assemble` 登记进 `default_registry`；`SEARCH_TOOL_SPEC.description` 订正 | FND-GROUP-D-01 |
| `src/deploy/checklists.txt` | B6 段归属表述订正 | §1.3（可选） |

| 证据文件（`docs/evidence/`） | 内容 |
|---|---|
| `groupc_r3_before_fixated_defects.log` | **修复前**：三个固化用例 PASS（缺陷在场），EXIT=0 |
| `groupc_r3_before_regression.log` | **修复前**全量回归转录：`138 passed`（EXIT=0） |
| `groupc_r3_after_fixated_defects.log` | **修复后**：三个固化用例如期 FAIL（守卫串 `偏差已消除`），EXIT=1 |
| `groupc_r3_after_symptoms.log` | **修复后**症状探针（`docs/evidence/groupc_r3_probe.py`）：FND-01 摘要非空；FND-02 (a)(b)(c) 三种窗口均无幽灵；不存在 → `NotFoundError` |
| `groupc_r3_after_regression.log` | **修复后**全量回归：`3 failed, 135 passed`（失败者恰为三个固化用例，无 ERROR/collect error） |
| `groupc_r3_after_selfcheck.log` | 开发者离线自检 `24/24 PASS`（EXIT=0） |

---

# §14 R4 增量实现（FND-GROUP-D-03 修复 + B-05 依赖补齐；追加，不改写 §1~§13）

> 输入：verifier 以**真实 Django HTTP 路径**独立复现的 **FND-GROUP-D-03**（MAJOR；
> 含 kb 级对照组以排除探针误差，证据 `docs/evidence/verify_r3_probe_blob_http.log`），
> 与部署侧登记的 **B-05**（`src/requirements.txt` 不含 ib-embed 推理运行时）。
> 本轮**只做这两件事**，不触碰 `tests/`、不改其他代理产出、不部署（不触目标机）。

## 14.1 结论摘要

| 项 | 结果 |
|---|------|
| FND-GROUP-D-03（MAJOR） | **已修复**：删除文档后原文件**不再成孤儿**；`blob_deleted` **正确置位**（确有且已删 → True；本无 → False） |
| B-05（依赖缺口） | **已补齐**：新增 `src/requirements-embed.txt`（FlagEmbedding + torch(CPU) + transformers；bge-m3 权重双源与离线加载约定写在文件头） |
| 新增模块 / 端口 / IFC / 配置键 / 依赖边 | **均无**；`delete_document` 签名与 `DeleteReport` 三计数语义**一字未改**（IFC-IB-144 / IFC-IB-281 仍成立） |
| 回归 | 全量 `142 passed`（EXIT=0）；离线自检 `24/24 PASS`（EXIT=0） |
| 未回归 FND-GROUP-D-02 | 是（探针第 6 组：项目级 scope 删除「尚无事发生」的文档仍成功，无 500 / 无幽灵） |

## 14.2 FND-GROUP-D-03 —— 修法选择与理由

### 14.2.1 根因（三处**互不一致**的 kb 段推导）

存储布局是 `<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`（ADR-05），
而「可选 kb → 存储段名」这条规则此前被**手写三份**：

1. `ib/blob/__init__.py`（**写/删路径**）：`scope.kb_ids[0] if scope.kb_ids else "default"`（4 处）；
2. `ib/lifecycle/__init__.py::blob_ref_for`（**读路径**）：`record.kb_id or "default"`；
3. `ibweb/composition.py::resolve_scope`（**调用方 scope**）：返回项目级 `Scope(project_id)`，即 `kb_ids=None`。

上传经 `submit_upload(ctx, kb_id)` → 写入用 **kb 级** scope（落盘到真实 kb 段）；
而 **HTTP 删除**经 `resolve_scope` → 传入 **项目级** scope（`kb_ids=None`）→ BlobStore 归为
`"default"` 段 → 在 `default` 段找不到目录 → `delete` 返回 0 → **原文件成孤儿且
`blob_deleted` 恒 False**（违反 AC-IB-03-02「不留下孤儿数据」与 AC-IB-03-03）。

### 14.2.2 所选方案（两条判据并做，构成**单一真源**）

**（a）收敛推导为单一真源**：在 `ib/blob/__init__.py` 新增模块内纯函数
`kb_segment(kb_id) -> str`（规则仅一条：**空 / None → `"default"`**），
写路径 4 处与 `blob_ref_for` **全部改用它**。三处推导在结构上不可能再分叉。

**（b）删除**由**台账记录**派生原文件 scope：`delete_document` 中把
`self._blobs.delete(scope, doc_id)` 改为 `self._blobs.delete(_blob_scope_of(record), doc_id)`，
其中 `_blob_scope_of(record) = Scope(project_id=record.project_id, kb_ids=(record.kb_id,) if record.kb_id else None)`。
`record` 是 `get_document(scope, doc_id)` 的返回值，其 `kb_id` 与写入时 `BlobStore.put`
的 kb 段**同源**（`create_document` 存的就是它），故删除 scope 的 kb 段必然与落盘段一致。

### 14.2.3 为什么**不**走「以 `blob_ref_for(record).rel_path` 精确定位 + 新增 `delete_ref`」那条路

调用单**首选**推荐的是「以 `blob_ref_for(record)` 推导出的**实际 `rel_path`** 定位并删除」。
实现它需要在 `BlobStore` 端口上**新增一个方法**（如 `delete_ref(blob_ref)`）。但
`module_design.md §3 MOD-IB-12` 把该端口**冻结为 4 个方法**（IFC-IB-131~134），而硬约束
明令「**禁止**实现 module_design.md 中未定义的模块或**接口**」。新增端口方法会**越界**。

因此改走任务**显式许可的另一分支**（「或把三处推导收敛为单一真源并保证写入 scope 与删除
scope 的 kb 段一致」），并**叠加**了共享 `kb_segment`（防止未来再漂移）。
效果等价且**不新增任何接口**：删除仍调用既有 `delete(scope, doc_id)`（IFC-IB-133 签名不变），
只是喂给它的 scope 由**权威来源**（台账记录）派生，而非调用方那个项目级 scope。

### 14.2.4 为什么**不会**误删其他 doc / 其他 project（安全论证）

- `record` 来自 `get_document(scope, doc_id)`，**已通过 scope 过滤**：`record.project_id`
  必等于 `scope.project_id`，故 `_blob_scope_of` 的 `project_id` 与调用方授权范围**同一项目**，
  不存在跨项目删除。
- `record.kb_id` 是该 doc 在**同一项目内**的归属，经 `safe_segment` 白名单校验（`_doc_dir`）
  后才拼路径；路径穿越由 `safe_segment`（拒绝 `..` / 分隔符）与 `_abs`（断言结果仍在 root 内）
  **两道**防护保留，**未削弱**。
- 删除的目录仍是 `<root>/<project>/<kb>/<doc_id>`（`FsBlobStore.delete` 的 `rmtree` 目标），
  只覆盖**该 doc 自己的目录**；探针第 5 组实测：删 `p_alpha` 的 doc 后 `p_beta` 的 blob **仍在**。
- `blob_deleted` 语义：`delete(...) > 0`。确有文件且被删 → True；本无（`data=None` 的 D-08
  路径，`content_sha256` 为空 → 无文件）→ 目录不存在 → 返回 0 → **False**（不虚报）。第 3 组实测。

### 14.2.5 为什么不回归 FND-GROUP-D-02

本轮**只改了 blob 删除那一步的 scope 来源**；R3 的两处修正（删除前自绑 collection、
台账删行后的竞态清扫）**一行未动**，`vectors_deleted` 计数不变。探针第 6 组在**fresh 装配**
（启动期只 `ensure_collection` 不 `bind_collection`）下用**项目级** scope 删除刚上传的文档：
不抛 `StartupError`、`vectors_deleted == 0`、台账行为 None、`process_pending` 不认领、无孤儿。

## 14.3 B-05 —— ib-embed 推理运行时依赖清单与权重来源（新增文件）

**新增 `src/requirements-embed.txt`**，写清三件事：

1. **运行时依赖（PRIMARY = FlagEmbedding）**：`FlagEmbedding>=1.2,<1.4`、`torch>=2.2,<2.6`
   （**CPU-only**，须经 `--index-url https://download.pytorch.org/whl/cpu` 安装，**严禁 CUDA**）、
   `transformers>=4.44,<4.50`。**备选** = `sentence-transformers`（默认注释，切换方式写在文件内：
   注释 FlagEmbedding 行、放开 sentence-transformers 行，**无需改代码** —— 运行时候选顺序
   `("flagembedding", "sentence_transformers", "onnxruntime")` 自动回落）。**候选③**
   （onnxruntime 直载 ONNX）仅登记、不启用。
2. **权重来源（双源，国内可达优先）**：HuggingFace `BAAI/bge-m3` 与 ModelScope `BAAI/bge-m3`；
   给出两条下载命令。**离线加载约定**：`IB_EMBED_MODEL_PATH` 指向本地权重目录，启动**不联网下载**；
   权重约 2.3GB **不入 git**（并新增根 `.gitignore` 规则 `models/bge-m3/` / `*.bge-m3/` / `**/bge-m3/`）。
3. **与 `src/requirements.txt` 的关系**：基座 venv 装 `requirements.txt`（**不含** torch 系）；
   ib-embed 专属 venv 装 `requirements-embed.txt`。**刻意不合并**，三条理由（C8 进程隔离 /
   内存·磁盘面 / SIGILL 爆炸半径收敛）已写入文件头。若改用**进程内**形态
   （`IB_EMBED_BACKEND=inproc`，默认 `http`），则须**往基座 venv**装本文件 ——
   结论仍是「torch/FlagEmbedding 任何时候都不进 `src/requirements.txt`」。

**版本 pin 的诚实性**：本项目离线执行，**无法**在此确证任何依赖的确切可用版本；
文件内所有区间均标注「**待目标机实测锁定**」，部署时以 `pip freeze` 回填，**不把区间当锁定值**。

## 14.4 架构偏差记录（R4）

| 偏差ID | 偏差描述 | 原 ADR / 契约 | 偏差原因与处置 |
|--------|---------|--------------|-------------|
| D-R4-01 | `ib/blob/__init__.py` 新增模块内纯函数 `kb_segment`（导出到 `ib.blob.__all__`） | module_design §3 MOD-IB-12 冻结 BlobStore 端口为 4 方法（IFC-IB-131~134） | **非端口方法**、**不登记 IFC**、纯函数无 IO；仅作为「可选 kb → 存储段」的**单一真源**，不改变任何冻结签名。属**加法**，向后兼容 |
| — | 新增 `src/requirements-embed.txt` + 根 `.gitignore` 权重规则 | 无（部署/依赖面） | 新增文件，不属模块/接口/配置键；回应 B-05 |

**无架构级偏差**：未新增/删除**模块**（仍 26）或**端口**（仍 13）或 **IFC 编号**或**依赖边**；
`IFC-IB-141~145`（含 `delete_document`）与 `DeleteReport` 结构**一字未改**；配置键名与默认值未动；
冻结约束（Django + 原生 SSE / 禁 Channels·Redis、Qdrant、bge-m3 dim=1024 CPU-only、**禁 PyMuPDF**、
`langchain-openai>=0.2,<0.3`、**禁 Docker**）**全部未触碰**。

## 14.5 R4 变更文件清单与验证证据

| 文件 | 变更性质 | 对应项 |
|------|---------|-------|
| `src/ib/blob/__init__.py` | 新增 `kb_segment`；`InMemoryBlobStore.put/delete`、`FsBlobStore._doc_dir/put` 的 kb 段推导改用它（4 处） | FND-GROUP-D-03(a) |
| `src/ib/lifecycle/__init__.py` | `blob_ref_for` 改用 `kb_segment`；删除路径新增 `_blob_scope_of(record)` 并由记录派生删除 scope；`delete_document` 文档串补 R4 说明 | FND-GROUP-D-03(b) |
| `src/requirements-embed.txt` | **新增**：ib-embed 推理运行时依赖 + bge-m3 权重双源/离线加载约定 | B-05 |
| `.gitignore` | 新增 bge-m3 权重忽略规则 | B-05（权重不入 git） |

| 证据文件（`docs/evidence/`） | 内容 |
|---|---|
| `groupc_r4_probe_fnd_d03.py` / `groupc_r4_after_probe.log` | R4 自验探针（HTTP + 文件系统 + 隔离 + 不回归），**22/22 PASS，EXIT=0** |
| `groupc_r4_after_existing_probe.log` | 复跑 **verifier 原有缺陷探针**（`groupd_r3_blob_probe.py`）：修复前 `blob_deleted=False 且对象数=1`（缺陷在场，见同名 before 日志），修复后 `blob_deleted=True 且对象数=0` |
| `groupc_r4_after_regression.log` | 全量回归 `142 passed`（EXIT=0） |
| `groupc_r4_after_selfcheck.log` | 离线自检 `24/24 PASS`（EXIT=0） |
| `groupc_r4_compileall.log` | `python -m compileall -q src` EXIT=0 |
| `groupc_r4_credscan.log` | 凭据形态扫描 **零命中**（EXIT=1），覆盖 4 个改动文件 |

---

## 15. R7 增量实现（定义外置为单一真源 + REQ-FUNC-IB-25/26/27 落地；追加，不改写 §1~§14）

> 依据：`module_design.md` R7 §2.1 / §3 MOD-IB-01 / MOD-IB-02 / MOD-IB-23 / MOD-IB-24 / §5 / §9；`architecture_design.md` R7 ADR-14 / ADR-15 / ADR-16。
> **性质**：**只追加、不改写**。未新增模块（仍 26）、未改既有 IFC 签名、未改既有配置键名与默认值、未改依赖边；端口 13 → 14（纯追加）。§1~§14 为 R1~R4 历史记录。

### 15.1 施工前置（REV-07-6 裁定 (a)）与落地顺序

本轮**先闭合「定义外置为数据、单一真源」的实现落差（REQ-FUNC-IB-01 / IB-02 的施工前置），再回填界面真实内容**。落地顺序（= 构造顺序，与 ADR-16 的装配期闸门一致）：

1. **数据层**：`definition.py` 的 `validate`（IFC-IB-290）/ `derive`（IFC-IB-291）**纯函数**先成立（离线可测，无 IO）。
2. **端口层**：`DefinitionDocumentStore`（IFC-IB-287）Protocol + 10 个 frozen 数据结构先稳定。
3. **装配层**：`admit`（IFC-IB-293）在装配期**第一步**闸门化，`_assemble` 按「装载 → 准入 → 派生 → 注入」注入 MOD-IB-16/19。
4. **界面层**：仅在此之后，配置页（IFC-IB-296）以**只读图 + 白名单表单**回填真实内容。

**关键不变式（R7）**：派生注册表 == 现有默认注册表 → **无行为变化**（默认定义文档由既有默认值精确派生：`EXPERT_SPECS` / `DEFAULT_TAU` / `DEFAULT_MARGIN` / `max_expert_steps=8` / `search_knowledge` 授权），故 R1~R4 的既有回归**不受影响**（见 §15.5）。

### 15.2 REQ-FUNC-IB-25 / 26 / 27 → 实现落点映射

| REQ-ID | 需求要点 | MOD | IFC | 实现落点（文件 :: 符号） |
|--------|---------|-----|-----|------------------------|
| REQ-FUNC-IB-25 | UI 可视化配置（只读编排图 + 白名单表单） | MOD-IB-24 | IFC-IB-296 | `src/frontend/src/views/ConfigPage.vue`（`VueFlow` 只读渲染 + 白名单表单 + 未提交草稿标注）；`src/frontend/src/App.vue`（`ViewKey='config'` + 导航）；`src/frontend/package.json`（`@vue-flow/core` 本地打包） |
| REQ-FUNC-IB-26 | 拓扑运行期**不可编辑**、单一真源、本地打包禁 CDN、编辑后 round-trip 写回 | MOD-IB-24 / MOD-IB-02 | IFC-IB-296 / IFC-IB-289 / IFC-IB-292 | `ConfigPage.vue`（`nodes-draggable` / `connectable` 只读；无 add/remove node/edge；零持久化）；`src/ib/config/definition.py::editable_field_whitelist`（拓扑不在白名单）、`::non_editable_changes`（拓扑变更即 400）、`::FileDefinitionDocumentStore.save`（原子写回 + 乐观并发）、`::InMemoryDefinitionDocumentStore` |
| REQ-FUNC-IB-27 | 装配期 fail-fast 准入闸门；**不提供**强制继续 / 忽略错误开关 | MOD-IB-23 / MOD-IB-02 | IFC-IB-290 / IFC-IB-293 | `src/ibweb/composition.py::admit`（聚合全部 `ValidationErrorItem` 的 `ConfigError`；拒绝装配）；`src/ib/core/types.py::ValidationReport`（字段集**不含** force/ignore/warn_only）；`definition.py::validate`（≥7 类校验项） |
| 前置（IB-01/IB-02 落差闭合） | 定义外置为数据、单一真源 | MOD-IB-01 / MOD-IB-02 | IFC-IB-287 ~ 292 | `src/ib/core/ports.py::DefinitionDocumentStore`；`src/ib/config/definition.py`；`src/ibweb/composition.py::{build_definition_store, _default_definition_document, _inject_derived_experts}` |

### 15.3 R7 变更文件清单

| 文件 | 变更性质 | 对应 IFC / 项 |
|------|---------|-------------|
| `src/ib/core/types.py` | **追加** 10 个 frozen `slots=True` 数据结构：`ExpertSpecInput` / `RouteSpecInput` / `ConditionalEdgeSpec` / `OrchestrationSpecInput` / `ToolGrantSpec` / `DefinitionDocument` / `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult`（+`__all__`） | IFC-IB-287 |
| `src/ib/core/ports.py` | **追加** 第 14 个端口 `DefinitionDocumentStore`（Protocol，5 方法）；头注释 13 → 14 端口；`__all__` | IFC-IB-287 |
| `src/ib/core/__init__.py` | 追加导出（10 结构 + 端口） | IFC-IB-287 |
| `src/ib/config/definition.py` | **新增**：`semantic_hash` / `validate` / `derive` / `editable_field_whitelist` / `non_editable_changes` / `build_definition_document` / `document_to_json` / `document_from_json` / `InMemoryDefinitionDocumentStore` / `FileDefinitionDocumentStore`（原子写 + 乐观并发） | IFC-IB-288~292 |
| `src/ib/config/__init__.py` | `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED` 登记入 `IB_RUNTIME_ENV_KEYS`（**仅键名**）+ 导出定义层符号 | IFC-IB-297 |
| `src/ib/experts/__init__.py` | **追加** `install_derived(specs)`（幂等、可重复装配） | IFC-IB-291 |
| `src/ibweb/composition.py` | **追加** `admit`（fail-fast 闸门）、`_known_tool_names`、`_default_definition_document`、`build_definition_store`、`_inject_derived_experts`；`_assemble` 新增 4c 步「装载→准入→派生→注入」；`Deps` 增 `definition_store` / `definitions` / `derived_views`；`_graph_config` / `_build_semantic_router` 接受文档派生 `route` | IFC-IB-293 |
| `src/ibweb/serializers.py` | **追加** 定义文档读写序列化器（`DefinitionConfigInputSerializer` 含 `expected_content_hash`）+ `definition_derived_summary` | IFC-IB-294/295 |
| `src/ibweb/views.py` | **追加** `definition_config_endpoint`（GET/PUT；405/404/401/403/503/400/409）+ `_visual_config_enabled` / `_read_failure_response` / `_validation_failure_response` / `_get_definition_config` / `_put_definition_config` | IFC-IB-294/295 |
| `src/ibweb/urls.py` | **追加** `path("api/config/definition", …, name="ib-config-definition")` | IFC-IB-294/295 |
| `src/frontend/package.json` | **追加** 依赖 `@vue-flow/core`（MIT，本地打包） | IFC-IB-296 |
| `src/frontend/src/api/client.ts` | **追加** `definitionConfig()` / `saveDefinition()` + 类型；`ApiClientError.details` | IFC-IB-294/295/296 |
| `src/frontend/src/views/ConfigPage.vue` | **新增**：只读编排图（Vue Flow）+ 白名单表单 + 冲突处理；**零持久化** | IFC-IB-296 |
| `src/frontend/src/App.vue` | **追加** 配置页导航与宿主 | IFC-IB-296 |
| `src/scripts/selfcheck.py` | **追加** 6 个 R7 离线用例（见 §15.5） | 自验 |
| `docs/implementation_plan.md` | 本 §15 + 头部版本 2.3.0/R7 + §1 R7 计数订正 + 范围行 REQ 计数 24 → 27（现 L63） | Task 1 |
| `docs/code_review_report.md` | §6 / 计数订正 + R7 增量评审小节 | Task 1/3 |

### 15.4 架构偏差记录（R7）

| 偏差ID | 偏差描述 | 原 ADR / 契约 | 偏差原因与处置 |
|--------|---------|--------------|-------------|
| — | **无架构偏差** | — | 未新增/删除模块（仍 26）；端口 13 → 14 为 module_design R7 §3 明示的**纯追加**（IFC-IB-287）；未改既有 IFC 签名与配置键名/默认值；未改依赖边（新端口的适配器由既有边 `23 → 01/02` 构造）；ADR-14/15/16 全部遵循 |

**冻结约束复核**：Django + 原生 SSE / 禁 Channels·Redis、Qdrant、bge-m3 dim=1024 CPU-only、**禁 PyMuPDF**、`langchain-openai>=0.2,<0.3`、**禁 Docker**、**禁 AGPL/copyleft**（`@vue-flow/core` = MIT）—— **全部未触碰**。

### 15.5 R7 自验证据

| 证据 | 内容 |
|---|---|
| `PYTHONUTF8=1 python -X utf8 scripts/selfcheck.py`（cwd=`src/`） | **30/30 PASS，EXIT=0**（R1~R4 的 24 例全绿 + R7 新增 6 例全绿） |
| R7 新增用例 | `definition_pure_functions`（validate/derive 纯函数 + 白名单）、`definition_store`（原子写 + 乐观并发 + 缺失不静默回退）、`definition_gate`（fail-fast 聚合）、`definition_config 端点`（GET/PUT 200/400/401/403/405/409）、`definition_assembly`（装载→校验→派生→注入）、`frontend_config_discipline`（无 CDN / 零持久化 / 拓扑只读 / 只有键名） |
| 未变的保护值 | `src/scripts/selfcheck.py` 例数由 24 → 30；**R2 / R3 / R4 增量小节内记载的「24/24 PASS」为 R1~R4 时点的历史自检记录**，对应本文件受保护的四行（**调用时行号 L471 / L603 / L621 / L732**；因本轮在文件头追加 R7 修订说明而整体下移至 **L481 / L613 / L631 / L742**）为**自检例数口径（≠ REQ 计数）**，本轮**逐字未改** —— 以 `git diff -U0 docs/implementation_plan.md \| grep '24/24 PASS'` 取证：四处**零出现在 diff**（仅新增的 §15.5 本行为本轮新增） |
| 残留（诚实标注） | `@vue-flow/core` **未在本机安装** → 前端 `vue-tsc` 类型检查与 `vite build` **无法离线验证**；Python 侧 `frontend_config_discipline` 仅做**源码级**纪律断言（依赖声明 / import / 无 CDN / 零持久化 / 拓扑只读入口不存在）。与既有 L-02（前端构建依赖联网）同类残留 |

---

## 16. R8 增量实现（FND-R7-01 修复：`validate` 补齐两项装配期校验；追加，不改写 §1~§15）

> 依据：`architecture_design.md` R7 ADR-16（校验项枚举含「路由关键词撞车」「面向用户标签唯一性」）；`user_stories.md` AC-IB-18-02；`module_design.md` §3 MOD-IB-02（IFC-IB-290）；登记处：`docs/test_report.md` §12.6 / §12.10。
> **性质**：**只追加、不改写**。未新增模块（仍 26）、未改端口数（仍 14）、未改任何 IFC-IB 号或签名、未改模块边界、未改 `EXPERT_SPECS` 默认数据、未改 `validate()` 既有 9 项校验的语义与顺序（仅在末尾追加第 10 / 11 项）。§1~§15 为 R1~R7 历史记录，**逐字未改**。

### 16.1 修复范围（协调者裁决 A / REV-08）

| 项 | 内容 |
|----|------|
| 缺陷 | **FND-R7-01（MAJOR）** —— `validate` 未覆盖 ADR-16 / REQ-FUNC-IB-27 ① 列举的两类装配期校验（`test_report.md` §12.6） |
| 补齐项 | ① 跨专家「路由关键词撞车」；② `cn_label`（中文标签）唯一性 |
| 边界 | `EXPERT_SPECS` 默认数据、既有 9 项校验语义与顺序、全部 IFC 号 / 签名、模块边界 —— **均未改** |

> 口径说明（**如实登记，不扩围**）：`test_report.md` §12.6 另举「专家内关键词为空/重复未由 `validate` 覆盖」一项。该子项**不在本轮授权范围**（协调者明确限定为「两项校验」），且已由 `ib/experts.validate_specs` 在**派生安装期**以 `ValueError` 兜底（既有行为，非本轮缺陷面）。本轮**未**改动该项。

### 16.2 校验口径与实现落点

| 新增校验 | 归一化口径 | 错误码 | 落点 | 理由 |
|---------|-----------|--------|------|------|
| 跨专家关键词撞车 | `kw.strip().lower()` | `expert_keyword_collision` | `src/ib/config/definition.py::validate` §10（L362~L389） | `lower()` **对齐路由消费方** `ib/routing/intent.py::_keyword_hits`（`keyword.lower() in text.lower()`）—— 大小写不同、小写后相同的两词在运行期**同样**并列命中、结果不可复现；`strip()` 去首尾空白（带空白的关键词几乎必然是录入错误，其去空白形态仍会重叠命中）。**只在跨专家之间**判定（专家内重复由 `validate_specs` 兜底） |
| `cn_label` 唯一性 | `label.strip()` | `expert_cn_label_duplicate` | `src/ib/config/definition.py::validate` §11（L391~L411） | 标签是**展示串**，空白填充在界面不可见 → 必须视为重复；大小写差异界面可见 → 不归一。空标签由既有第 5 项 `expert_text_missing` 单独报出，本项跳过空值以免重复告警 |

错误信息**定位到具体条目键**并回显冲突值（关键词 / 标签）与涉及的**两个专家名**，无任何凭据值（AC-IB-18-02 / AC-IB-18-04）。

### 16.3 R8 变更文件清单

| 文件 | 变更性质 | 对应 IFC / 项 |
|------|---------|-------------|
| `src/ib/config/definition.py` | `validate()` **末尾纯追加**第 10 / 11 项校验（+docstring 登记第 10 / 11 类；既有 9 项一字未改） | IFC-IB-290（签名 / 返回类型不变） |
| `src/scripts/selfcheck.py` | **修正 2 个既有用例的夹具**（`definition_pure_functions` 的 `b` 关键词 `k → j`；`definition_gate` 的 `e{i}` 关键词 `k → k{i}`）—— 原夹具「两专家共用关键词 `k`」仅在旧（不完整）校验下「合法」，修后即为**应拒**；**并在 `cases` 列表登记 1 个新用例** | 自验 |
| `src/scripts/selfcheck.py` | **新增** `definition_uniqueness` 用例（通过 + 拒绝两分支；ADR-16 / AC-IB-18-02） | 自验 |
| `tests/unit/test_definition_uniqueness_r8.py` | **新增**（TC-UNIT-062 / 063 / 064，纯函数离线） | GROUP_D 套件新增 |
| `docs/implementation_plan.md` | 本 §16 + 头部版本 2.3.0 → **2.4.0** / R8 修订行 / `latest_invocation_id` | Task 3 |
| `docs/code_review_report.md` | 头部版本行 + 新增 **§13 R8 增量评审** | Task 4 |

**未改**：`src/` 下与本次修复无关的文件；`tests/` 下**任何既有用例**（只新增 1 个文件）。

### 16.4 架构偏差记录（R8）

| 偏差ID | 偏差描述 | 原 ADR / 契约 | 偏差原因与处置 |
|--------|---------|--------------|-------------|
| — | **无架构偏差** | — | ADR-16 的校验项枚举**本已含**这两类；本轮是**补齐实现落差**，非新增架构决策。未改模块 / 端口 / IFC / 配置键 / 依赖边 / 默认数据 |

### 16.5 R8 自验证据

| 证据 | 内容 |
|---|---|
| `PYTHONUTF8=1 python -X utf8 src/scripts/selfcheck.py`（**cwd = 仓库根目录**） | **31/31 PASS，EXIT=0**（R1~R7 的 30 例全绿 + R8 新增 1 例全绿） |
| R8 新增用例 | `definition_uniqueness`（跨专家关键词撞车 / `cn_label` 重复 → fail-fast；通过 + 拒绝两分支） |
| 新增单元测试 | `tests/unit/test_definition_uniqueness_r8.py` → **3 passed**（TC-UNIT-062 / 063 / 064） |
| 默认装配不回归 | `selfcheck.py::definition_assembly` / `definition_config 端点` **PASS** —— 默认定义文档（由 `EXPERT_SPECS` 精确派生：三专家无跨专家关键词撞车、`cn_label` 唯一）**修后仍通过**（`TC-UNIT-064` 亦独立佐证） |
| `python -m compileall -q src` | **EXIT=0**（含改动文件） |

### 16.6 下游影响（诚实登记，需 GROUP_D 处置）

新增校验使**部分既有测试夹具**（两专家共用关键词 `k` 或共用 `cn_label` `"标签"`）由「旧校验下合法」变为「修后应拒」。经**实跑**，`tests/unit` + `tests/integration` 中恰好 **4 个既有用例**因此失败：

| 用例 | 文件 | 根因 |
|------|------|------|
| TC-UNIT-056 / 057 / 061 | `tests/unit/test_definition_data_layer_r7.py` | 夹具 `_expert` 默认 `keywords=("k",)` / `cn_label="标签"`，两专家撞车 |
| TC-INT-082 | `tests/integration/test_definition_config_r7.py` | 同上 |

**处置建议（不改 tests/，交 GROUP_D）**：将上述两文件的 `_expert` 夹具改为「每专家关键词互异、标签互异」的合法数据（如 `keywords=(f"k{name}",)`）。此与 `test_report.md` §12.10 第 4 项「FND-R7-01 修复后补验回归用例」及 NV-R7-05 一致 —— 属 GROUP_D 的修复后测试侧工作。**本轮未改 `tests/` 任何既有用例**。

### 16.7 冻结约束复核（R8）

- **未改**：`IFC-IB-001~297`（无新增编号、无签名/返回类型变更）；端口数 14；模块数 26；`EXPERT_SPECS` 默认数据；配置键名与默认值；依赖边。
- **未触碰**：Django + 原生 SSE / 禁 Channels·Redis；Qdrant；bge-m3 dim=1024 CPU-only；**禁 PyMuPDF**；`langchain-openai` pin `<0.3`；**禁 Docker**；**禁 AGPL/copyleft**。
- **未触网 / 未引新依赖**：本轮自测离线（纯函数 + 临时目录），未真连 Qdrant / DeepSeek / ib-embed，未安装任何新依赖。
- **凭据纪律**：改动代码与文档**不含任何真实凭据**；错误信息只回显关键词 / 标签值（业务数据，非凭据），且不回显任何环境变量值。

---

## 17. R10 增量实现（前端构建阻断修复 + 冒烟入口 + 许可登记；追加，不改写 §1~§16）

> 依据：PM 只读取证（`.github/workflows/ci.yml` 阶段9 `npm ci` → `npm run build`；`src/frontend/package.json` L16 声明 `@vue-flow/core@^1.41.0`）；`docs/test_plan.md`（AC-IB-17-06 / REQ-NFR-IB-08 离线与零外发）；`docs/tech_stack.md` §1.3 / §2（传递依赖许可 `[待核实]`）。
> **性质**：**只追加、不改写**。未新增模块（仍 26）、未改端口数（仍 14）、未改任何 IFC-IB 号或签名、未改后端 `src/ib` / `src/ibweb` / `src/ib_embed` 任何行为、未改配置键名与默认值。§1~§16 为 R1~R8 历史记录，**逐字未改**。

### 17.1 缺陷根因（三处叠加，任一处均令交付管线走不通）

| 编号 | 缺陷 | 证据（R10 前） | 后果 |
|------|------|---------------|------|
| **FND-R10-01（CRITICAL）** | **锁文件与 `package.json` 失同步**：`package-lock.json` 内**无任何** `vue-flow` 条目（`grep -c vue-flow package-lock.json` = **0**），其根节点 `packages[""].dependencies` 只含 `vue` | `src/frontend/package-lock.json`（R10 前 1459 行） | CI 阶段9 `npm ci` 比对 package.json ↔ lock 不一致 → **EUSAGE 失败**，`npm run build` **永不抵达** |
| **FND-R10-02（CRITICAL）** | **源文件未被跟踪**：`src/frontend/src/views/ConfigPage.vue` 未入 git（`git ls-files` 无、`git status` 显示 `??`），而**已跟踪**的 `src/frontend/src/App.vue:23` 已 `import ConfigPage from './views/ConfigPage.vue'` | `git ls-files src/frontend/src/views` 仅 3 个文件 | CI checkout 后**缺该文件** → `vue-tsc --noEmit` 报模块不存在 → 阶段9 仍失败；且 R7 的 IFC-IB-296 页面**不会进产物** |
| **FND-R10-03（CRITICAL）** | **类型错误**：`ConfigPage.vue` L41 导入 `type ExpertSpecInput` 但全文未使用；`tsconfig.json` 开启 `noUnusedLocals: true` | R10 首跑 `npm run build` 原始输出：`src/views/ConfigPage.vue(41,8): error TS6133: 'ExpertSpecInput' is declared but its value is never read.` `EXIT=2` | 即便锁与跟踪均修好，`vue-tsc --noEmit` 仍非零退出 → 阶段9 失败 |

> 二者（01 / 02）互为**独立**阻断：只修锁不改跟踪，或只改跟踪不修锁，`npm run build` 均不可达 / 不通过。故本轮必须**三处同修**方能使 CI 阶段9 绿。

### 17.2 R10 变更文件清单

| 文件 | 变更性质 | 对应 IFC / 项 |
|------|---------|-------------|
| `src/frontend/package-lock.json` | **重新生成**：新增 `@vue-flow/core@1.48.2` 及 14 个传递包（+216 行；`npm ci` 可精确复现） | FND-R10-01 |
| `src/frontend/package.json` | 新增 `"test": "node --test"` 脚本；`_comment` 追加 R10 说明（**dependencies 未增删**，`@vue-flow/core@^1.41.0` 保持原样） | 前端冒烟入口 |
| `src/frontend/src/views/ConfigPage.vue` | 删除未使用的 `type ExpertSpecInput` 导入（**-1 行**，其余逐字未改）；**并入 git 跟踪** | FND-R10-02 / 03（IFC-IB-296 不变） |
| `src/frontend/tests/frontend.smoke.test.js` | **新增**：零新增依赖的冒烟骨架（6 用例，含「锁 ↔ package.json 同步」回归闸） | 前端冒烟入口 |
| `docs/tech_stack.md` | 新增 **§2.1** 前端依赖许可登记（14 传递包版本 + 许可）；§1 / §2 / §5.3 三处 `[待核实]` 收敛为**已核实（R10）**；头部 1.3.0 → **1.3.1** | NFR-12 许可合规落点 |
| `docs/implementation_plan.md` | 本 §17 + 头部版本 2.4.0 → **2.5.0** / R10 修订行 / `latest_invocation_id` | Task 3 |
| `docs/code_review_report.md` | 头部版本行 + 新增 **§14 R10 增量评审** | Task 4 |

**未改**：`src/` 下**后端**任何文件（`ib` / `ibweb` / `ib_embed`）；`tests/` 下任何既有用例；`src/frontend/src/` 下除 `ConfigPage.vue` 一行删除外的任何文件；`vite.config.ts` / `tsconfig.json` / `index.html`。**未改** `.github/workflows/ci.yml`（阶段9 命令保持 `npm ci` + `npm run build` 原样 —— 本轮修的是被它检验的产物，不是检验本身）。

### 17.3 构建证明（严格按 CI 顺序复现；可被第三方重跑）

| # | 命令（cwd = `src/frontend`） | 结果 | 证据文件 |
|---|---------------------------|------|---------|
| 1 | `npm install --no-fund --no-audit` | **EXIT=0**；`added 16 packages` | `docs/evidence/groupc_r10_npm_install.log` |
| 2 | `npm ci`（先 `rm -rf node_modules`，依 lock 重装） | **EXIT=0**；`added 65 packages`；`node_modules/@vue-flow/core` 就位 | `docs/evidence/groupc_r10_npm_ci.log` |
| 3 | `npm run build`（= `vue-tsc --noEmit && vite build`） | **EXIT=0**；`28 modules transformed`；`dist/assets/index-*.js` **252.35 kB（gzip 89.20 kB）**、`index-*.css` **12.62 kB（gzip 2.74 kB）** | `docs/evidence/groupc_r10_npm_build.log` |
| 4 | `npm test`（= `node --test`） | **EXIT=0**；`tests 6 / pass 6 / fail 0` | `docs/evidence/groupc_r10_npm_test.log` |
| 5 | 回归闸负向对照：以 **R10 前的旧锁**（`git show HEAD:src/frontend/package-lock.json`）跑用例 2 | **按预期失败**：`AssertionError: package-lock.json 未解析 @vue-flow/core`（`pass 5 / fail 1`） | `docs/evidence/groupc_r10_guard_negative_control.log` |
| 6 | 传递依赖许可核实（逐包读 `node_modules/<pkg>/package.json`） | 14 包全部 **MIT / ISC / BSD-3-Clause**，无 copyleft | `docs/evidence/groupc_r10_license.log` |

> 第 2 步 `npm ci` 会**先清空 `node_modules` 再依 lock 重装**，是「锁完整、可离线复现」的最强证明；其 EXIT=0 即证 FND-R10-01 已闭合。第 3 步 EXIT=0 即证 FND-R10-03 已闭合。

### 17.4 架构偏差记录（R10）

| 偏差ID | 偏差描述 | 原 ADR / 契约 | 偏差原因与处置 |
|--------|---------|--------------|-------------|
| D-R10-01 | **`git add src/frontend/src/views/ConfigPage.vue`**（将既有未跟踪文件纳入版本控制） | 无对应 ADR；属交付完整性问题 | FND-R10-02：文件由 R7 交付（`implementation_plan.md` §15 已登记 `ConfigPage.vue`），但从未 `git add`。**未改其内容语义**（仅删 1 行无用导入），仅补登记。**已 staging，待 PM 纳入提交** |
| — | 其余**无架构偏差** | — | 未改 ADR/模块/端口/IFC/配置键/依赖边/后端行为 |

### 17.5 冻结约束复核（R10）

- **未改**：`IFC-IB-001~297`（无新增编号、无签名/返回类型变更）；端口数 14；模块数 26；配置键名与默认值；依赖边；后端 `src/ib` / `src/ibweb` / `src/ib_embed` 任何行为。
- **未触碰**：Django + 原生 SSE / 禁 Channels·Redis；Qdrant；bge-m3 dim=1024 CPU-only；**禁 PyMuPDF**；`langchain-openai` pin `<0.3`；**禁 Docker**。
- **许可（NFR-12）**：新纳入的 14 个传递包**全部宽松**（MIT / ISC / BSD-3-Clause），**无 AGPL / copyleft**；已登记于 `tech_stack.md` §2.1。
- **离线纪律（AC-IB-17-06 / REQ-NFR-IB-08）**：**未引入运行期 CDN**；依赖经构建本地打包；冒烟用例 5 对外发 CDN 主机名做**源码 + `dist/index.html`** 双向扫描；`npm test` **零新增依赖**（仅 Node 20 内建 `node:test`）。
- **体积纪律**：未引入 UI 组件库；`dist` JS 252.35 kB（gzip 89.20 kB），对 4GB 目标机可接受。
- **凭据纪律**：改动文件与证据日志**不含任何真实凭据**（证据仅为 npm 输出与包元数据）。
- **FreeArk 仓库全程只读**；`docs/phase_status.md` **未触碰**（PM 专属）。
- **受保护行复核（R10）**：本文件四处「24/24 PASS」保护行**逐字未改**。因 R8 / R10 各在文件头 `revision_note` 追加一段（各 +1 行），四行的**当前行号**为 **L483 / L615 / L633 / L744**（R7 时点记录为 L481 / L613 / L631 / L742）。R10 的改动仅落在文件头（L6 / L8 / L11 / L36）与本 §17，**与保护行无交集**。取证：`grep -n "24/24 PASS" docs/implementation_plan.md`。`src/scripts/selfcheck.py` 及其相关行**本轮未触碰**。
