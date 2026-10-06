<file_header>
  <project>intelligentbase</project>
  <artifact>tech_stack</artifact>
  <path>docs/tech_stack.md</path>
  <doc_id>TECH-INTELBASE-001</doc_id>
  <version>1.4.0</version>
  <revision>REV-13</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04b 技术选型</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-007</invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-10-06</updated_at>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.4.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.4.0" status="APPROVED" note="R7 新增登记：可视化配置的 AC 落点（AC-IB-17-01~06 / AC-IB-18-01~06）为 §4.5 新增项与 §1.3 凭据纪律的直接依据"/>
    <input path="docs/architecture_design.md" version="1.5.0" revision="REV-13" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/module_design.md" version="1.5.0" revision="REV-13" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW" note="MOD-IB-26 契约唯一落点；本文件 §1.2 的键名清单以其 §9 为准"/>
    <readonly_reference path="FreeArk 仓库" note="只读参考；未修改任何文件"/>
  </inputs>
  <scope_boundary>技术选型、许可合规台账、目标机依赖验证清单、风险汇总。**不含实现代码与部署脚本**。</scope_boundary>
  <credential_policy>本文档不记录任何密钥、令牌、口令或证书。目标机凭据**一律经环境变量注入**（REQ-NFR-IB-07 / C-IB-02）。所有条目仅登记「配置键名」，不登记值。</credential_policy>
  <revision_history>
    <rev version="1.0.0" date="2026-09-25" note="初稿（GROUP_B 首次提交，PM 门控前）"/>
    <rev version="1.1.0" revision="R1" date="2026-09-25" note="按 PM 架构复核反馈 REV-01 修订：① Web 框架 FastAPI→Django（用户明确指定，非建议），前端 Vue 3 + Vite 不变；② Uvicorn 作为 ASGI 应用服务器的条目改写为 Waitress/Gunicorn（WSGI），Pydantic 退出 Web/校验层选型（仅作可选独立校验库）；③ §2 许可台账补登 Django（BSD-3-Clause）/ DRF（BSD-3-Clause）/ Waitress（ZPL-2.1）/ Gunicorn（MIT），经外部核实后登记；④ 新增 §4.5 Web 层（Django）与服务承载验证清单、§5.2 SSE 并发风险项、[TBD-T15]；⑤ 编号稳定优先：类别与条目名尽量沿用 1.0.0，被替换者移入 §1.1 留痕；所有改动带 -R1 标记。需求侧文档未改动。"/>
    <rev version="1.2.0" revision="R2" date="2026-09-26" invocation_id="INV-GROUP_B-INTELBASE-004" note="R2 补交（L-03）：① 「Embedding 推理运行时」行改写为三候选（FlagEmbedding / sentence-transformers / 直接 onnxruntime 载 bge-m3 的 ONNX 导出），补记许可、CPU-only 可用性、传递依赖与指令集基线风险；② §2 许可台账补登传递依赖 torch（BSD-3-Clause）与 transformers（Apache-2.0），均标条件性采纳；③ 新增 §1.2「服务端配置键登记」（只登记键名与语义，不含任何值，覆盖 IFC-IB-286 的第二份 EnvironmentFile）；④ §5.2 新增一行中风险：目标机 CPU 缺 AVX2 致预编译 wheel 触发 SIGILL（同时命中既有 OCR 链路与 R2 的 embedding 推理运行时），缓解与判定指向 [TBD-T18]；⑤ 编号稳定：既有条目类别/行序尽量沿用，被改写者标「（R2 改写）」；未引入 PyMuPDF、未引入 Docker（DR-03）。需求侧文档与 FreeArk 仓库未改动。"/>
    <rev version="1.3.0" revision="R7" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-005" note="R7 增量贯通（GROUP_A REV-06 裁决：诉求③「UI 可视化配置」纳入 v1，新增 REQ-FUNC-IB-25/26/27）：① 新增「前端图可视化库」行 = Vue Flow（@vue-flow/core，MIT，R7 经外部核实：包内 LICENSE 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024），要求随构建产物本地打包、禁止运行期 CDN；② §1.1 留痕 5 项已评估未采纳（AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / 运行期 CDN 加载）；③ 新增 §1.3 客户端配置键登记（只登记键名 IB_DEFINITION_DOC_PATH / IB_VISUAL_CONFIG_ENABLED，不含任何值）；④ §2 台账登记 Vue Flow（MIT，采纳）与传递依赖（条件性采纳 + [待核实]，须锁定版本后逐包复核）；⑤ §4.5 新增第 10~12 项（前端产物零外发依赖、装配期 fail-fast 实测、定义文档凭据明文扫描）；⑥ §5.3 新增两行低风险（定义文档被写入凭据明文 / 图库传递依赖的许可与体积，以 [TBD-T20] 实测为准）；⑦ 硬约束未松动：未引入 Docker / Redis / PyMuPDF，端口契约仍 framework-free。需求侧文档与 FreeArk 仓库未改动；未写入任何凭据或配置值（只登记键名）。"/>
    <rev version="1.3.1" revision="R10" date="2026-09-27" invocation_id="INV-GROUP_C-INTELBASE-008" author="software-developer" note="R10 传递依赖许可登记（GROUP_C 前端构建阻断修复轮）：① 新增 §2.1「前端依赖许可登记」—— 在 src/frontend 执行 npm install 后逐包实测，登记 @vue-flow/core 1.48.2 与 14 个传递包（@vueuse/core·shared·metadata 10.11.1 / vue-demi 0.14.10 / @types/web-bluetooth 0.0.20 / d3-color·dispatch·drag·interpolate·selection·timer·transition·zoom + d3-ease）的精确版本与许可，全部 MIT / ISC / BSD-3-Clause，**无 copyleft / AGPL 面** → 不触发 §1 重选型（REQ-NFR-IB-12 合规）；② §2 台账「Vue Flow 的传递依赖」行由 [待核实] 改为**已核实（R10）**；③ §1「前端图可视化库」行与 §5.3 风险行同步收敛；④ 补记 R10 实测产物体积（JS 252.35 kB / gzip 89.20 kB）供 [TBD-T20] 引用。**仅登记事实，未改任何选型决策 / 未改键名 / 未写入任何凭据值**；证据 = docs/evidence/groupc_r10_license.log。**性质：登记型修订，选型未变**（GROUP_B 可复核）。"/>
    <rev version="1.4.0" revision="REV-13" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-007" author="system-architect" note="REV-13 认证与商用界面重构增量（GROUP_A REV-13 下游贯通：REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）：① §1 新增三行 —— 前端 UI 组件库 Element Plus（MIT，DR-13）、前端路由 vue-router（MIT，hash 模式）、口令哈希库 bcrypt（Apache-2.0，DR-11）；② §1.1 留痕 5 项已评估未采纳（Cookie 会话 / JWT 自包含令牌 / 独立鉴权服务 / Django contrib.auth+ORM 迁移 / 运行期 CDN 加载 Element Plus）；③ 新增 §1.4 客户端配置键登记（只登记键名 IB_AUTH_LOGIN_PATH / IB_AUTH_SESSION_STORAGE_KEY，不含任何值）；④ §2 台账新增三行（Element Plus / vue-router / bcrypt，均采纳）+ （R13）遗留合规动作追加；⑤ 新增 §2.2 前端依赖许可登记（方法同 R10，结论暂标 [待核实]）；⑥ §4.5 新增第 13~18 项（默认管理员种子与首登强制改密 / 零 Cookie / token-query 全端点 4xx / IB_AUTHZ_POLICY_MODULE 未配置即启动失败 / HTTPS 生效 / 前端自包含与凭据不回显）；⑦ §5.2 新增一行中风险（bcrypt cost 与阈值标定，以 [TBD-T22] 为准）、§5.3 新增一行低风险（Element Plus 传递依赖许可与体积 + 口令/令牌泄露缓解）；⑧ 硬约束未松动：未引入 Docker / Redis / PyMuPDF / Cookie 会话 / Django ORM / contrib.auth；禁止运行期 CDN。仅登记键名，未写入任何凭据值。"/>
  </revision_history>
</file_header>

# 技术选型 — intelligentbase

**版本**: 1.4.0（REV-13 增量） | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06

**R2 修订摘要（L-03：`ib-embed` 服务端无模块归属与契约）**：

| 序 | 改动 | 落点 |
|----|------|------|
| 1 | 「Embedding 推理运行时」行**改写为三候选**（含直接 `onnxruntime` 载 ONNX），补许可 / CPU-only 可用性 / 传递依赖 / 指令集基线风险 | §1 该行（标「R2 改写」） |
| 2 | 许可台账**补登传递依赖** `torch` / `transformers`（均条件性采纳） | §2 |
| 3 | 新增 **§1.2 服务端配置键登记**（**只登记键名与语义，不含任何值**） | §1.2（新增） |
| 4 | 新增一行中风险：**目标机缺 AVX2 → 预编译 wheel 触发 SIGILL**（同时命中既有 OCR 链路与 R2 的 embedding 运行时） | §5.2 |
| 5 | **编号与许可稳定**：既有条目的类别、行序、条目名尽量沿用；被改写者标「（R2 改写）」；未引入任何 AGPL / copyleft 新面，**未引入 PyMuPDF、未引入 Docker** | 全文 |

**R7 修订摘要（GROUP_A REV-06 下游贯通：诉求③「UI 可视化配置」纳入 v1）**：

| 序 | 改动 | 落点 |
|----|------|------|
| 1 | 新增「**前端图可视化库**」行 = **Vue Flow（`@vue-flow/core`，MIT）**（选型理由 / 许可 / 离线本地打包 / 传递依赖待核实） | §1（新行，标「R7 新增」） |
| 2 | §1.1 留痕 **5 项已评估未采纳**：AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / **运行期 CDN 加载** | §1.1 |
| 3 | 新增 **§1.3 客户端配置键登记**（只登记键名与语义，**不含任何值**） | §1.3（新增） |
| 4 | §2 台账登记 **Vue Flow（MIT，采纳）** 与**传递依赖（条件性采纳 + `[待核实]`）** | §2 |
| 5 | §4.5 新增第 **10~12** 项：前端产物**零外发依赖**、**装配期 fail-fast 实测**、**定义文档凭据明文扫描** | §4.5 |
| 6 | §5.3 新增两行低风险：定义文档被写入凭据明文 / 图库传递依赖的许可与体积（[TBD-T20]） | §5.3 |
| 7 | **禁项与硬约束未松动**：未引入 Docker / Redis / PyMuPDF；图库**禁 CDN**；端口契约仍 framework-free | 全文 |

**版本策略说明**：本表给出**版本约束/主版本策略**，并在 `精确版本` 列统一标注「部署时锁定」。原因是目标机硬件与系统版本未实测（[TBD-T13] / [TBD-T14]），且基座定位为可复用资产——**具体小版本须在部署阶段经实测后写入 `requirements` 锁文件**，此处不预先编造精确版本号。凡本文未能确证的版本事实，一律标 `[待核实]`。

**R1 修订摘要（对应 PM 复核反馈 REV-01）**：

| 序 | 改动 | 落点 |
|----|------|------|
| 1 | **后端 Web 框架由 FastAPI 改为 Django**（用户明确指定）；前端 Vue 3 + Vite **不变** | §1「Web 框架」「WSGI 服务器」「ASGI 服务器」三行；§1.1；§2 |
| 2 | 移除/改写 FastAPI、Uvicorn、Pydantic 作为 **Web/校验框架**的条目；Pydantic 仅作**可选**独立契约校验库保留（取舍已写明） | §1「数据校验（R1 改写）」行；§1.1 |
| 3 | 许可台账补登 **Django / DRF / Waitress / Gunicorn**（R1 经外部核实后登记，未臆造） | §2 |
| 4 | 新增 **Web 层（Django）与服务承载验证清单**；新增 SSE 并发上限 [TBD-T15] | §4.5；§5.2 |
| 5 | 两个 FreeArk 已知坑（`?token=` 入日志、`channels_redis`×`redis-py` 不兼容）明确写为**实现约束**，无论最终是否采用 Channels 均适用 | §3 |

---

## 1. 技术选型表

| 类别 | 选型 | 版本约束 / 精确版本 | Rationale | 关联 REQ-* | 风险 | 备注 |
|------|------|---------------------|-----------|-----------|------|------|
| 编程语言 | Python | `>=3.11,<3.14`；部署时锁定 | RAG/Embedding 生态（含 bge-m3 与 OCR）在 Python 侧最完整；团队既有栈同源（FreeArk 3.12） | REQ-NFR-IB-11 | 低 | `PYTHONUTF8=1` 需显式设置（沿用 FreeArk 纪律，中文路径/编码问题）；**（R1）目标版本线与 FreeArk / Django 保持同一较新小版本线** |
| 包管理 / 隔离 | `venv` + `pip` + `requirements*.txt` 锁文件 | 部署时锁定 | DR-03 禁容器 → 依赖隔离只能靠 venv；**每进程一个 venv**（ADR-03） | REQ-FUNC-IB-22 | 中 | 无容器即无镜像层缓存，跨项目复用同机时依赖冲突须靠 venv 纪律；**禁止 pscp 逐文件上传**，一律 `git pull`（沿用 FreeArk 纪律） |
| **Web 框架（R1 改写）** | **Django** + **Django REST Framework**（HTTP 边界校验与序列化） | Django `>=4.2 LTS` 或 5.x，部署时锁定；DRF 与 Django 主版本匹配 | **用户明确指定后端框架为 Django（非建议，R1）**；与 FreeArk 后端同栈，运维与排障认知成本最低；内置 URLconf 路由、中间件（请求上下文注入）、`JsonResponse`，并提供 **`StreamingHttpResponse`** 承载**原生 SSE**（无需 Channels / Redis）；DRF Serializer 提供类型化请求校验与响应序列化，等价承接 FastAPI 侧的 Pydantic 模型 + `Depends` 依赖注入职责（映射说明见 `module_design.md` §2.1.1） | REQ-FUNC-IB-21；REQ-NFR-IB-01、IB-09、IB-11 | 低 | **ADR-11-R1**；同步 WSGI 下 `StreamingHttpResponse` 的每个 SSE 长连接占用一个 worker（进程/线程）→ 见 §5.2 与 [TBD-T15]；**不使用 Django ORM 承接台账**（见下方「台账数据库」行与 ADR-07-R1）；前端 Vue 3 + Vite **不变** |
| **WSGI 服务器（R1 改写；1.0.0 此行为 Uvicorn/ASGI）** | **Waitress**（生产主选，与 FreeArk 一致）/ **Gunicorn**（多 worker/多线程备选） | 部署时锁定 | 同步 WSGI 是 Django 同步视图的默认部署形态；Waitress 已在 FreeArk 生产验证（systemd 直管、纯 Python、无额外运行时）；Gunicorn（`gthread` worker 类）在需以 worker/线程池承载并发 SSE 时提供显式容量旋钮 | REQ-FUNC-IB-21、IB-22 | 中 | **SSE 长连接占用 worker 槽位**：并发上限 ≈ worker 池容量；超限须**快速失败（503，可读文案）而非无限排队**（排队会把「慢」放大成「全链路超时」）；`--workers` / `--threads` 由 [TBD-T15] 实测校准；前置 nginx 须**禁用响应缓冲**（SSE 前提，响应头 `X-Accel-Buffering: no`） |
| **ASGI 服务器（R1 新增；仅并发升级路径）** | Gunicorn + `uvicorn.workers.UvicornWorker`（承载 **Django 异步视图**） | 部署时锁定 | **仅当 [TBD-T15] 显示同步 worker 池容量不足时启用**：异步视图下 SSE 长连接不占用 worker 槽位、并发由事件循环承载，而**仍不引入 Channels/Redis**，保留「SSE 而非 WebSocket」的防泄漏初衷 | REQ-FUNC-IB-21 | 中 | **默认不启用、不安装**（Uvicorn 不再作为独立 ASGI 应用服务器选型）；启用前提：全链路同步调用（Django DB 读、`ib-embed` HTTP、Qdrant 同步客户端、langgraph 同步流）须经 `sync_to_async` 正确桥接——**任一未桥接的阻塞调用会拖慢全部并发连接**，该失效模式比「占用一个 worker」更危险，故列为升级路径而非默认（ADR-11-R1） |
| **数据校验（R1 改写；1.0.0 此行为 Pydantic）** | **DRF Serializer**（HTTP 边界校验/序列化）+ **frozen dataclass**（端口契约，定义于 MOD-IB-01） | 随 Django / DRF 主版本 | 契约分层：**内部端口契约**用零依赖 frozen dataclass 承载类型化（满足「接口须类型化」门控标准，且不使 MOD-IB-01 依赖任何第三方）；**HTTP 边界**由 DRF Serializer 承担请求校验、响应序列化与错误聚合 | REQ-NFR-IB-01 | 低 | **Pydantic 取舍（显式说明）**：Pydantic **不再是 Web 层或校验层的选型**（FastAPI 已整体移除）；若后续需要**独立于 Web 框架**的配置/契约校验（如配置文件 schema 校验），可作为**可选依赖**引入，但**不得**成为任何端口契约的载体，也不得进入 MOD-IB-01 的依赖集（ADR-13-R1） |
| 前端框架 | Vue 3 + Vite | Vue 3.4+ / Vite 5+；部署时锁定 | 与既有前端栈同源，降低维护成本；构建产物静态托管 | REQ-FUNC-IB-09/17 | 低 | ADR-11；前端**仅通过 HTTP/SSE 契约**与后端交互；**（R1）前端不受后端框架切换影响：Vue 3 + Vite 不变** |
| **前端图可视化库（R7 新增；R10 传递依赖已核实）** | **Vue Flow**（`@vue-flow/core`） | 主版本随实现锁定（建议 `^1`）；部署时锁定 | 可视化配置页需渲染编排图（节点 / 条件边 / 分支可达性），Vue 3 生态内成熟首选：组件化节点与边、视口与缩放、**只读模式**（节点不可拖拽、不可连线）开箱可用；**MIT 许可**；可**随构建产物本地打包**（满足离线 + 数据不出本地，AC-IB-17-06） | REQ-FUNC-IB-25、IB-26；AC-IB-17-02、AC-IB-17-06；REQ-NFR-IB-08 | 中 | **MIT（R7 经外部核实：包内 `LICENSE` 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024）**；**传递依赖**（D3 系 / `@vueuse/core` 等）须在锁定版本后**逐包核实并登记**（**R10 已逐包核实并登记于 §2.1**：14 个传递包全部为 **MIT / ISC / BSD-3-Clause**，**无 copyleft / AGPL 面**），见 §2 / §2.1 与 [TBD-T20]；**禁止运行期 CDN 加载**；**只读渲染优先**（拓扑不可编辑，ADR-14 / ADR-15） |
| 编排框架 | LangGraph | 主版本随实现锁定 | 图编排 + 条件边并行扇出 + checkpointer，是 REQ-FUNC-IB-18/19 的直接支撑；FreeArk 已验证可行 | REQ-FUNC-IB-18/19/20 | 中 | **仅 L4 层使用**，且被端口隔离（REQ-NFR-IB-11）；版本升级须跑骨架回归；**（R1）为同步流式 API，与 ADR-11-R1 选定的同步 WSGI + SSE 在并发模型上同构**（不需 async 桥接） |
| LLM 客户端 | LangChain + `langchain-openai` | **`langchain-openai` pin `<0.3`** | 沿 FreeArk 既有集成路径 | REQ-FUNC-IB-18；DR-04 | **高** | **生产事故史**：0.3.x 移除 `_convert_chunk_to_generation_chunk` 致生产漂移，且会丢弃 `DeepSeek` 的 `reasoning_content`。ADR-08 已把该风险收敛到 MOD-IB-20 适配器内部（[TBD-T10]） |
| LLM 服务 | 云端 DeepSeek（OpenAI 兼容接口） | 端点经配置；不锁死 | DR-04 用户拍板；端点可配以便未来切自建兼容端点 | REQ-FUNC-IB-18；REQ-NFR-IB-08 | 中 | **须显式声明「提问文本 + 检索片段外发云端」**（AC-IB-12-05）；`describe_egress()` 输出至启动日志与 `/healthz/deps` |
| 向量数据库 | **Qdrant** | 最新稳定版；部署时锁定；`.deb` 可用性 [TBD-T14] | DR-01 用户拍板；原生 HNSW、payload filter 表达力强、per-collection 距离度量（支持项目间异构维度）、单机资源占用可控 | REQ-FUNC-IB-13/14/23/24；DR-01 | 中 | **Apache-2.0**；裸装（`.deb` + 自建 unit，见 §4）；**官方 `.deb` 不含 unit、不建 snapshots 目录**（启动会 panic） |
| 向量库客户端 | `qdrant-client` | 与 Qdrant 服务版本匹配 | 官方客户端；gRPC 主、REST 回退 | REQ-FUNC-IB-13 | 低 | 客户端与服务端**大版本须匹配**，纳入部署检查清单 |
| Embedding 模型 | **bge-m3**（稠密） | 权重版本部署时锁定 | DR-02 用户拍板；中文效果强、1024 维、多语种 | REQ-FUNC-IB-15；REQ-NFR-IB-05 | 中 | **MIT 许可**（满足 AC-IB-07-04）；[ESTIMATE] CPU 单条推理延迟量级见架构文档 §4，**须以 [TBD-T1] 实测** |
| **Embedding 推理运行时（R2 改写）** | **三候选**：① `FlagEmbedding`（BAAI 官方）；② `sentence-transformers`；③ **直接以 `onnxruntime` 载 bge-m3 的 ONNX 导出** | 部署时锁定（**三者择一，不得并行安装**） | **选择依据（R2 显式化）**：① 对 bge 系列适配最直接、抽象层最少，但**带入 `torch` + `transformers`** 两条传递依赖（磁盘与内存面最大）；② 生态最广、CPU 支持成熟，同样带入 `torch` / `transformers`，且对 bge-m3 的多向量能力支持弱于 ①；③ **唯一不引入 `torch` 的路径**（仅 `onnxruntime`），bge-m3 官方提供 ONNX 权重，**CPU-only 可用**、内存面最小 —— 目标机内存仅 11GiB 且 OCR 链路**已依赖 `onnxruntime`**，选 ③ 可与之共享同一运行时依赖，代价是**须自行承担 tokenizer 与池化后处理**（1024 维 + L2 归一化的契约责任仍落在本行，与 §1「Embedding 模型」行一致）。**许可**：① MIT / ② Apache-2.0 / ③ MIT（`onnxruntime`）——三者均为宽松许可，**无一触犯 REQ-NFR-IB-12**。**CPU-only 可用性**：三者均可纯 CPU 运行、**均不需 GPU/CUDA**（③ 须选 CPU 版 wheel，**不得**装 GPU 版） | REQ-FUNC-IB-15；REQ-NFR-IB-10；REQ-NFR-IB-12 | **高** | **最终择一须在 GROUP_C 以目标机实测为依据**（[TBD-T1] 延迟 / [TBD-T4] 内存 / **[TBD-T18] 指令集基线**），此处不预先拍板；→ **指令集风险（R2 新发现）**：目标机 CPU 缺 **AVX2**，① / ② 经 PyTorch、③ 经 `onnxruntime`，其**预编译 x86_64 wheel 均可能触发 SIGILL**（非法指令，进程级崩溃，**不可捕获**）→ 缓解与判定见 §5.2 与 [TBD-T18]；→ **硬约束提醒（R2 重申）**：本项**不得**以 `PyMuPDF` 或任何 AGPL / copyleft 组件替代（见 §1.1），**不得**引入 Docker / 容器化（DR-03）；→ 若选 ① / ②，须在 §2 台账以**条件性采纳**登记传递依赖 `torch`（BSD-3-Clause）与 `transformers`（Apache-2.0） |
| Embedding 服务形态 | 本基座自带轻量 HTTP 服务（`ib-embed`，systemd 单元） | — | ADR-02；使冷/热双路径超时纪律有单一落点 | REQ-FUNC-IB-15；REQ-FUNC-IB-22 | 中 | **形态可逆**：端口不变，可切回进程内（ADR-02） |
| OCR 引擎 | `rapidocr-onnxruntime` | 部署时锁定 | DR-08；FreeArk 既有链路，已验证可行；Apache-2.0 | REQ-FUNC-IB-11 | 中 | **Apache-2.0**。首次加载耗时与内存须实测（[TBD-T3]/[TBD-T4']） |
| OCR 运行时 | `onnxruntime` | CPU 版；部署时锁定 | 与 rapidocr 配套；CPU 可用 | REQ-FUNC-IB-11 | 中 | **MIT**；CPU 架构相关（[ARCH-ASSUMPTION-A4]） |
| PDF 文本提取（主） | **`pypdf`** | 部署时锁定 | **BSD-3-Clause**（宽松，满足 REQ-NFR-IB-12）；纯 Python 无二进制依赖 | REQ-FUNC-IB-10；REQ-NFR-IB-12 | 中 | [ESTIMATE] 纯 Python 较 C 内核慢一个量级（入库为异步冷路径可接受）；**主/回退顺序由 [TBD-T8] 决定** |
| PDF 文本提取（回退） | **`pdfminer.six`** | 部署时锁定 | **MIT**；CJK 字符级版面处理更精细，作为空结果/异常/疑难版面回退 | REQ-FUNC-IB-10；REQ-NFR-IB-12 | 低 | ADR-06 |
| PDF 表格提取（可选） | `pdfplumber` | 部署时锁定 | **MIT**；表格密集文档增强；**可选依赖，缺失即自动降级** | REQ-FUNC-IB-10 | 低 | 非必需项，缺失不影响主流程 |
| PDF 渲染（扫描页） | **`pypdfium2`** | 部署时锁定 | **BSD-3-Clause OR Apache-2.0**（双许可）；PDFium 内核；是「许可友好 + 可渲染」的唯一成熟选择 | REQ-FUNC-IB-11；AC-IB-04-06 | 中 | 纯 Python 三库**均不能渲染**；wheel 与架构相关（[ARCH-ASSUMPTION-A4]） |
| DOCX 解析 | `python-docx` | 部署时锁定 | 与 FreeArk 一致；docx 段落与内嵌图像提取 | REQ-FUNC-IB-10 | 低 | MIT |
| Markdown / 纯文本 | 标准库 + 轻量解析 | — | md/txt 无需重依赖 | REQ-FUNC-IB-10 | 低 | 保持最小组成面 |
| 台账数据库 | SQLite（WAL 模式） | 随 Python 标准库 | 零新增组件；状态机/分页/聚合为关系模型强项 | REQ-FUNC-IB-16；ADR-07 | 中 | **须显式开启 WAL + `busy_timeout`**，否则 `database is locked`；升级路径为 PG（端口已抽象）；**（R1）不经 Django ORM 承接**：保持 `LedgerRepository` 端口 + 自管 SQL（stdlib `sqlite3`），schema 走**手写 scoped 迁移**（ADR-07-R1） |
| 原文件存储 | 本地文件系统（内容寻址 sha256） | — | ADR-05；零组件、可校验完整性 | REQ-FUNC-IB-24；OQ-IB-01 | 低 | 布局 `<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`；**（R1）OQ-IB-01 已确认 = 保留（ON）**，ADR-05-R1 确认 sha256 内容寻址 + 原子重建方案 |
| 会话状态 | 进程内内存实现（`SessionStore` 端口默认实现） | — | ADR-11；无 Redis 依赖；语义 fail-closed | REQ-FUNC-IB-20 | 中 | **多 worker 下会话不共享**：若 v1 需多 worker + 共享会话，须替换实现（端口已备）。**默认按单 worker（或多 worker 但接受会话按 worker 归属）部署，须在部署配置中显式声明**；**（R1）与 SSE 的 worker/线程池容量须一并权衡（[TBD-T15]）** |
| 流式通道 | SSE（`text/event-stream`） | — | ADR-11；**凭据不进 URL**（消除 FreeArk `?token=` 泄漏类别） | REQ-FUNC-IB-21 | 低 | 须禁用反向代理缓冲；**（R1）由 Django `StreamingHttpResponse` 承载（原生 SSE，不引 Channels）** — ADR-11-R1 |
| 鉴权 | 可注入 `AuthzPolicy` 端口（默认 `DenyAllPolicy`） | — | 基座不带业务鉴权模型；接入方注入；**未注入即启动失败** | REQ-NFR-IB-09；AC-IB-11-05 | 低 | 未授权返回 401/403，不得静默；**（R1）Django 侧落点：中间件（解析已认证主体 + 构造 `RequestContext`/`AuthzContext`）+ 视图装饰器（调用 `can_manage` / `can_query`）**；默认拒绝且未注入即启动失败 |
| 服务编排 | systemd（4 个单元） | 系统自带 | DR-03 禁 Docker；与既有运维心智一致 | REQ-FUNC-IB-22；DR-03 | 中 | 单元清单见 `architecture_design.md` ADR-03；**（R1）`ib-web` 单元以 Waitress/Gunicorn 启动 Django 应用，凭据仍经 `EnvironmentFile` 注入** |
| 配置载体 | 配置文件（YAML/JSON）+ 环境变量覆盖（凭据仅环境变量） | — | REQ-FUNC-IB-01/02；[ARCH-ASSUMPTION-A1] | REQ-NFR-IB-02/07 | 低 | 仓库仅含 `.env.example`（无真实值）；启动期校验必填项；**（R1）配置装载不依赖 Django settings 机制**（保持 `ConfigurationSource` 端口的独立性，便于离线单测与跨项目复用） |
| 日志 | 标准库 `logging` + 结构化字段（JSON 行） | — | REQ-NFR-IB-06；级别经环境变量可调 | REQ-NFR-IB-06 | 低 | 字段白名单 + 脱敏（FM-8）；**禁止记录正文与凭据**；**（R1）不经 Django `LOGGING` 作为唯一配置源**（保持 `MOD-IB-04` 的单一落点） |
| 测试框架 | 标准库 `unittest` / `pytest`（二选一，GROUP_D 定） | — | 离线替身驱动的测试（REQ-NFR-IB-14） | REQ-NFR-IB-14 | 低 | 全部测试须离线可跑（附录 D）；性能项须目标机证据；**（R1）测试须使用 SQLite（测试库），严禁连接生产/外部数据库** |
| 版本控制 / 部署 | `git`（直接提交 `main`）+ `git pull` 部署 | — | 沿用 FreeArk 纪律；**禁止逐文件上传** | REQ-FUNC-IB-22 | 低 | 目标机凭据经环境变量，不入仓库 |
| **前端 UI 组件库（R13 新增）** | **Element Plus** | `^2`（部署时锁定） | **DR-13 用户拍板**：Claude 风格商用界面对表单 / 表格 / 消息 / 弹窗 / 抽屉 / 主题变量覆盖有硬需求；Element Plus 提供**设计令牌级主题定制**与暗/亮主题（`dark/css-vars`），可在 Vue 3 生态内**随构建产物本地打包**（满足「数据不出本地」，AC-IB-17-06 精神） | REQ-FUNC-IB-34、IB-35；REQ-NFR-IB-17 | 中 | **MIT**（R13 经外部核实后登记）；**传递依赖须逐包核实**（§2.2，锁定 `package-lock.json` 后）；**禁止运行期 CDN**；体积增量以 **[TBD-T23]** 实测为准（R10 基线 JS 252.35 kB / gzip 89.20 kB） |
| **前端路由（R13 新增）** | **`vue-router`** | `^4`（部署时锁定） | 登录页 / 首登改密 / 运维控制台 / 账户管理的**路由与鉴权守卫**（`beforeEach` 检查登录态与改密态）需一等结构；**hash 模式**不需 nginx `try_files` 回退，减部署面（ADR-23） | REQ-FUNC-IB-28、IB-34、IB-35 | 低 | **MIT**（R13 经外部核实后登记）；**hash 模式**（非 history）；**禁止运行期 CDN** |
| **口令哈希库（R13 新增）** | **`bcrypt`**（pyca/bcrypt） | 部署时锁定（建议 `>=4,<5`） | **DR-11 用户拍板**：口令哈希须用 bcrypt（自带 salt 与 cost 旋钮，无自研密码学）；纯 stdlib 的 PBKDF2 须自管 salt / 编码 / 参数升级，风险更高 | REQ-FUNC-IB-30；REQ-NFR-IB-15 | 中 | **Apache-2.0**（R13 经外部核实后登记）；**CPU-only 目标机单次耗时须实测**（[TBD-T22]）；**只存摘要，绝不存口令明文**；随 `ib-web` venv 安装（**非** Django ORM / 非 contrib.auth） |

### 1.1 明确**不采纳**的选型（留痕）

| 候选 | 不采纳理由 | 关联 |
|------|-----------|------|
| **PyMuPDF** | **AGPL-3.0**，传染性；三条合规前置条件均不满足或与需求冲突；且不得沿用「内部平台合规」口径 | ADR-06；REQ-NFR-IB-12 |
| Poppler CLI（`pdftotext`/`pdftoppm`） | **GPL-2.0** 仍属 copyleft；子进程隔离的法律定性有争议，不能作为合规确定性来源 | ADR-06 |
| Docker / 容器化（任意形态） | **DR-03 明令禁止**；且不维护容器/非容器双路径 | DR-03 |
| Redis（会话 / 缓存 / channel layer） | 新增组件与凭据面；FreeArk 有 `channels_redis` 与 `redis-py` 版本不兼容致 WS 收包超时的**事故史** | ADR-10 / ADR-11-R1 |
| RabbitMQ | 同上（新增组件与凭据面）；DR-05 量级下收益为负 | ADR-10 |
| PostgreSQL / MySQL | 新增组件与凭据面（违反 C-IB-08 最小组成面）；SQLite 在本量级足够。**保留为升级路径** | ADR-07 |
| MongoDB | **SSPL 许可**，与 REQ-NFR-IB-12 冲突 | ADR-07 |
| **Channels（WebSocket 流式 + Redis channel layer）（R1 改写）** | **1.0.0 此行为「Django + DRF + Channels」，已被 REV-01 修订** —— Django/DRF 已改为**采纳**（见 §1）；剩余不采纳部分仅为 **Channels 及其 Redis channel layer**：与 DR-03 / C-IB-08 最小组成面冲突，且牵出两个已知坑（`?token=` 入访问日志、`channels_redis` 4.3.0 × `redis-py` 8.0.0 不兼容致 WS 收包超时）。Django 原生 `StreamingHttpResponse` 已满足 SSE 流式诉求 | ADR-11-R1；§3 |
| **FastAPI + Uvicorn（作为 Web 应用框架 / ASGI 应用服务器）（R1 新增留痕）** | **R1 移除**：用户明确指定后端框架为 **Django**（非建议）；且 FastAPI 的 SSE 需 ASGI 部署形态，而本项目全链路为同步调用（同步 ORM/DB 读、同步 HTTP 客户端、langgraph 同步流），同步 WSGI 与之同构、组成面更小。**留痕：1.0.0 曾选定此项，本次按用户指定替换** | ADR-11-R1 |
| 第三方推理服务器（Ollama / TEI / vLLM） | 重量级依赖与运维面；DR-03 下安装摩擦大；本基座只需单模型单路径 | ADR-02 |
| langchain `VectorStore` 抽象（`langchain-qdrant`） | 抽象面过宽、版本耦合风险、`Document.metadata: dict` 非类型化（违反门控标准 4） | ADR-01 |
| 对象存储（MinIO / S3） | 新增组件与凭据面；本量级收益为负 | ADR-05 |
| 本地 LLM（v1） | 与 DR-04 冲突；显著加重目标机 CPU/内存压力。**保留 v2 经同一端口接入** | ADR-08 |
| **AntV X6（R7 新增）** | 图编辑能力更强（拖拽连线、布局算法齐备），但**框架无关的独立图引擎**在本项目「只读渲染 + 白名单表单」的前提下属**能力过剩**；引入自成一体的图形栈与主题体系，与既有 Vue 3 组件体系叠两套心智模型。**已评估未采纳** | REQ-FUNC-IB-26；ADR-14 |
| **LogicFlow（R7 新增）** | 国产流程编排图库，流程图语义贴合；但生态与社区规模小于 Vue Flow，且其**编辑导向**（锚点 / 连线）与「**拓扑不可编辑**」硬约束需要额外裁剪。**已评估未采纳** | REQ-FUNC-IB-26；ADR-14 |
| **React Flow（R7 新增）** | 与 Vue Flow 同源、成熟度最高；但**要求 React 运行时**，与既有前端栈（Vue 3 + Vite）冲突，为单一页面引入第二前端框架不可接受。**已评估未采纳** | REQ-FUNC-IB-25；ADR-11 |
| **自绘 SVG / 直接使用 D3（R7 新增）** | 零新依赖、产物体积最小；但需自实现节点布局、边路由、缩放平移与命中测试，**维护与回归成本显著高于引入成熟库**（D3 许可仍需登记）。**已评估未采纳**；**保留为回退路径**：若将来要求「零新增前端依赖」，可回退至此并在 §2 补登 D3 许可 | REQ-FUNC-IB-25；REQ-NFR-IB-11 |
| **运行期 CDN 加载图库（R7 新增）** | 免打包、可远程热更；但**违反「数据不出本地 / 离线可用」**（AC-IB-17-06），并引入外部可用性与供应链风险。**已评估未采纳（并明令禁止）** | REQ-NFR-IB-08；AC-IB-17-06 |
| **Cookie 会话（Django session / `contrib.sessions`）（R13 新增）** | **DR-10 明令禁止 Cookie 会话**；且会重开 CSRF 面并牵入第二凭据通道。令牌改为不透明服务端令牌 + **仅 `Authorization` 头**（ADR-19） | DR-10；REQ-FUNC-IB-29 |
| **JWT / 自包含签名令牌（R13 新增）** | 撤销需另建黑名单（等价于又一张服务端表）；载荷可读；引入签名库与新密钥面；与「可撤销 + 过期/续期」无净收益。**已评估未采纳** | ADR-19 |
| **独立鉴权服务 / 进程（R13 新增）** | 净增 systemd 单元与凭据面，与 C-IB-08（最小组成面）/ ADR-03（四单元）冲突；账户体系内建（DR-09）**更小更安全**。**已评估未采纳** | DR-09；ADR-18 |
| **Django `contrib.auth` / `contrib.admin` / ORM 迁移（R13 新增）** | 与既有收窄配置（`DATABASES={}`、不经 ORM、手写 scoped 迁移，ADR-07-R1）冲突；会牵入自动迁移产物与会话框架（含 Cookie）。**已评估未采纳** | ADR-07-R1；ADR-18/26 |
| **运行期 CDN 加载 Element Plus（R13 新增）** | **违反「数据不出本地 / 离线可用」**（REQ-NFR-IB-17），并引入外部可用性与供应链风险。**已评估未采纳（并明令禁止）** | REQ-NFR-IB-17；AC-IB-17-06 |

---

### 1.2 服务端配置键登记（**R2 新增**；只登记键名与语义，**不含任何值**）

> **用途**：`ib-embed`（MOD-IB-26）此前**无服务端配置契约**（L-03）。本表登记其配置**键名**，使 `IFC-IB-286`（第二份 `EnvironmentFile` 模板）有据可依。**语义与默认值以 `docs/ib_embed_service_contract.md` §9 为准**（唯一落点），本表为**键名清单视图**。
> **凭据纪律（强制）**：`ib-embed` **不需要任何令牌** —— 该文件**不得**出现任何凭据型键名或值。若有人为它加鉴权令牌，是**净增凭据面**，须先回架构层评审。

| 键名 | 语义（一句话） | 关联 IFC |
|------|---------------|----------|
| `IB_EMBED_HOST` | 监听地址（默认仅本机回环） | IFC-IB-274 |
| `IB_EMBED_PORT` | 监听端口（客户端 `LocalHttpEmbedder` 的目标端口） | IFC-IB-266 / IFC-IB-274 |
| `IB_EMBED_MODEL_ID` | 模型标识（须与 `/descriptor` 回报一致） | IFC-IB-271 |
| `IB_EMBED_DIM` | 向量维度（须 = 客户端 `IB_EMBED_DIM` = `CollectionSpec.dim` = 1024，三方一致性） | IFC-IB-267 |
| `IB_EMBED_MODEL_PATH` | 本地权重**目录**（离线加载，不联网下载） | IFC-IB-270 |
| `IB_EMBED_MAX_BATCH` | 单请求批上限（**硬约束：≥ 客户端 `cold_batch_size`**） | IFC-IB-272 |
| `IB_EMBED_MAX_TOKENS` | 单条截断上限（保前缀） | IFC-IB-272 |
| `IB_EMBED_MAX_CONCURRENCY` | 推理并发上限（**有界**，不设无界） | IFC-IB-268 |
| `IB_EMBED_QUEUE_DEPTH` | 排队深度上限（超限**快速失败**并回显 `retry_after_s`，**绝不无界排队**） | IFC-IB-268 |
| `IB_EMBED_THREADS` | 推理线程数（与 Qdrant / `ib-web` / OCR 同为 CPU 竞争者） | IFC-IB-274 |
| `IB_EMBED_MEMORY_LIMIT_MB` | 服务端内存上限（**须与单元文件 `MemoryMax` 一致**） | IFC-IB-274 |

**未列出的键**：`IB_EMBED_BACKEND` 属**客户端**（`ib-web`）配置，**不在本表**；`IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*` 亦属**客户端**冷/热双路径实例（IFC-IB-273：**服务端不区分冷热**）。**此处不得为服务端补一套超时/重试键**——那会把冷热纪律从客户端**双落点**化，破坏 ADR-02-R2 附注的单一落点。

### 1.3 客户端配置键登记（**R7 新增**；只登记键名与语义，**不含任何值**）

> **用途**：REV-07（可视化配置）为 `ib-web` 侧新增两个配置键（IFC-IB-297）。与 §1.2 的分工：**§1.2 = `ib-embed` 服务端键**（不得在此补服务端超时 / 重试键），**本节 = `ib-web` 客户端键**。语义与校验规则以 `module_design.md` §3 MOD-IB-02 / MOD-IB-23 为准；键名的唯一权威落点为 `module_design.md` §2.2.2（IFC-IB-297）。

| 键名 | 语义（一句话） | 关联 IFC |
|------|---------------|----------|
| `IB_DEFINITION_DOC_PATH` | 定义文档的本地文件路径（**一项目一文档**；[ARCH-ASSUMPTION-A6]）；装配期由准入闸门读取 | IFC-IB-288 / IFC-IB-293 / IFC-IB-297 |
| `IB_VISUAL_CONFIG_ENABLED` | 可视化配置页与定义文档端点（`GET` / `PUT`）的开关；关闭时端点不注册、界面不提供入口 | IFC-IB-294 / IFC-IB-295 / IFC-IB-297 |

**凭据纪律（强制）**：上述键**只登记键名**。定义文档内**只允许出现键名**（如凭据型配置项**的名称**），**不得出现任何值**；界面与校验错误信息**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；`?token=` / `?key=` 类凭据型查询串纪律（§3）**扩展至全部新端点**（含定义文档的 `GET` / `PUT`）。若 `IB_DEFINITION_DOC_PATH` 的路径本身含敏感信息，须经**环境变量**注入且**不得**写入文档、日志或响应。

---

### 1.4 客户端配置键登记（**R13 新增**；只登记键名与语义，**不含任何值**）

**前端（Vite / 运行时）仅登记以下键名，不登记任何值**：`IB_AUTH_LOGIN_PATH`（登录端点路径，默认 `/api/auth/login`）、`IB_AUTH_SESSION_STORAGE_KEY`（会话令牌的**客户端存储键名**，**只登记键名**）。**纪律**：**不得**在前端源码 / 构建产物 / 文档中出现任何**令牌值或口令值**；令牌**仅**经 `Authorization` 头；**不接受 `?token=`**（`src/deploy/checklists.txt` [B14]/[B17]）。

---

## 2. 许可合规台账（REQ-NFR-IB-12）

> **强制约束**：REQ-NFR-IB-12 明确**禁止默认以「内部平台合规」豁免**。下表逐项登记许可与结论，作为可追溯的合规证据。
> **（R1）** 新增登记的 Django 系依赖许可**已经外部核实**（Django 与 DRF 为 BSD-3-Clause；Waitress 为 ZPL-2.1，OSI 认可且 FSF 判定 GPL 兼容；Gunicorn 为 MIT），未凭印象登记；部署锁定版本后仍须按发行包内 `LICENSE` 复核。

| 组件 | 许可 | 兼容性 | 结论 |
|------|------|--------|------|
| Qdrant | Apache-2.0 | 宽松 | **采纳** |
| bge-m3 模型权重 | MIT | 宽松 | **采纳** |
| `FlagEmbedding` | MIT | 宽松 | 采纳（首选） |
| `sentence-transformers` | Apache-2.0 | 宽松 | 采纳（备选） |
| **`torch`（R2 新增；传递依赖，条件性）** | **BSD-3-Clause** | 宽松 | **条件性采纳**：仅当选 §1「Embedding 推理运行时」的 ① / ② 时才进入依赖集；选 ③（onnxruntime 直载）则**不引入**。许可本身合规，但**体积与内存面最大**，且是 [TBD-T18] 指令集风险的主要来源 |
| **`transformers`（R2 新增；传递依赖，条件性）** | **Apache-2.0** | 宽松 | **条件性采纳**：同 `torch`，仅 ① / ② 路径引入；③ 路径**不引入**（tokenizer 职责由本基座自行承担） |
| `rapidocr-onnxruntime` | Apache-2.0 | 宽松 | **采纳** |
| `onnxruntime` | MIT | 宽松 | **采纳** |
| `pypdf` | BSD-3-Clause | 宽松 | **采纳**（PDF 文本主） |
| `pdfminer.six` | MIT | 宽松 | **采纳**（回退） |
| `pdfplumber` | MIT | 宽松 | 可选采纳 |
| `pypdfium2` | BSD-3-Clause OR Apache-2.0 | 宽松（双许可） | **采纳**（渲染） |
| `python-docx` | MIT | 宽松 | **采纳** |
| **Django（R1 新增）** | **BSD-3-Clause** | 宽松 | **采纳**（Web 框架，用户指定） |
| **Django REST Framework（R1 新增）** | **BSD-3-Clause** | 宽松 | **采纳**（HTTP 边界校验与序列化） |
| **Waitress（R1 新增）** | **ZPL-2.1**（Zope Public License 2.1，OSI 认可、FSF 判定 GPL 兼容） | 宽松 | **采纳**（生产 WSGI 服务器；与 FreeArk 一致） |
| **Gunicorn（R1 新增）** | **MIT** | 宽松 | **采纳**（多 worker/多线程备选 WSGI 服务器） |
| **Uvicorn（R1 新增；仅并发升级路径）** | **BSD-3-Clause** | 宽松 | **采纳（条件性）**：仅当 ADR-11-R1 的 Option B（Django 异步视图 + ASGI）被 [TBD-T15] 触发时引入；默认不安装 |
| Vue 3 / Vite | MIT | 宽松 | 采纳 |
| **Vue Flow（`@vue-flow/core`）（R7 新增）** | **MIT** | 宽松 | **采纳**（可视化配置页的编排图渲染）。**R7 经外部核实**：包内 `LICENSE` 为标准 MIT 文本（© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024） |
| **Vue Flow 的传递依赖（R7 新增；R10 已逐包核实）** | **已核实（R10）**：`@vueuse/core` 10.11.1（MIT）、`@vueuse/shared` 10.11.1（MIT）、`@vueuse/metadata` 10.11.1（MIT）、`vue-demi` 0.14.10（MIT）、`@types/web-bluetooth` 0.0.20（MIT）、`d3-color` 3.1.0（ISC）、`d3-dispatch` 3.0.1（ISC）、`d3-drag` 3.0.0（ISC）、`d3-ease` 3.0.1（BSD-3-Clause）、`d3-interpolate` 3.0.1（ISC）、`d3-selection` 3.0.0（ISC）、`d3-timer` 3.0.1（ISC）、`d3-transition` 3.0.1（ISC）、`d3-zoom` 3.0.0（ISC）（版本随 `src/frontend/package-lock.json` 锁定） | **全部宽松（MIT / ISC / BSD-3-Clause）** | **采纳**（**R10 实地核实**：逐包读 `node_modules/<pkg>/package.json` 的 `version` / `license` 字段并确认包内 `LICENSE` 文件存在；**零 copyleft / AGPL 面**，满足 REQ-NFR-IB-12）。复核证据：`docs/evidence/groupc_r10_license.log`。**任一传递依赖出现 copyleft / AGPL 面即须回 §1 重新选型**（**不得**沿用「内部平台合规」豁免）；传递依赖的许可留痕规则见本节末段与 §2.1 |
| **Element Plus（R13 新增）** | **MIT** | 宽松 | **采纳**（DR-13；本地打包，禁 CDN）。**R13 经外部核实后登记**；**传递依赖须逐包核实并登记于 §2.2**（`@element-plus/icons-vue` / `@floating-ui/dom` / `async-validator` / `lodash-es` 等——**清单以锁定后的 `package-lock.json` 为准**），未核实前标 `[待核实]` |
| **vue-router（R13 新增）** | **MIT** | 宽松 | **采纳**（前端路由与守卫） |
| **`bcrypt`（Python，R13 新增）** | **Apache-2.0** | 宽松 | **采纳**（口令哈希，DR-11；随 `ib-web` venv 安装，非 Django 组件） |
| LangGraph / LangChain / `langchain-openai` | MIT | 宽松 | 采纳（**版本 pin 见风险表**） |
| **PyMuPDF** | **AGPL-3.0** | **传染性，不兼容** | **不采纳** |
| Poppler CLI | GPL-2.0 | 传染性 | **不采纳** |
| MongoDB | SSPL | 非 OSI 认可 | **不采纳** |
| ~~FastAPI / Uvicorn / Pydantic~~ | ~~MIT / BSD-3 / MIT~~ | — | **（R1）该行已撤销**：FastAPI 与 Uvicorn（应用服务器）已移出采纳清单，见 §1.1 留痕；Pydantic 退出 Web/校验层，仅可作**可选**独立校验库（若引入须单独登记许可） |

**AGPL 三条合规前置条件（逐条判定，用于留痕）**：① 购买 Artifex 商业授权 —— 成本不可接受；② 整个基座以 AGPL 开源 —— 与「内部多项目复用」目标冲突；③ 严格内部使用且不与外部网络交互 —— 与 REQ-FUNC-IB-23（多项目、多使用方）冲突。**三条均不成立，故不采纳 PyMuPDF。**

**遗留合规动作（部署阶段）**：`pypdf` / `pdfminer.six` / `pdfplumber` / `pypdfium2` 的实际许可文本须在锁定版本后**从发行包内 `LICENSE` 文件复核**（发行方可能随版本调整），复核结果记入部署记录。**（R1 追加）** 同规则适用于 **Django / DRF / Waitress / Gunicorn**（及条件性引入的 Uvicorn）。**（R2 追加）** 同规则适用于**实际选中的 Embedding 推理运行时**及其**传递依赖**（若选 ① / ② 则含 `torch` / `transformers`；若选 ③ 则含 `onnxruntime` 与 bge-m3 的 ONNX 权重再分发条款）—— **传递依赖的许可亦须逐条留痕**，不得只登记直接依赖。

**（R13）遗留合规动作追加**：Element Plus / vue-router 的**传递依赖**须在锁定版本后**逐包**读 `node_modules/<pkg>/package.json` 的 `version` / `license` 与包内 `LICENSE` 文件复核，结果记入 §2.2（沿用 R10 方法）。**任一传递依赖出现 copyleft / AGPL 面即须回 §1 重新选型**，**不得**沿用「内部平台合规」豁免（REQ-NFR-IB-12）。

### 2.1 前端依赖许可登记（**R10 新增**；NFR-12 可核验落点）

> **落点与依据**：R7 引入 `@vue-flow/core` 时，其**传递依赖**的许可与版本标为 `[待核实]`（见上表与 §1「前端图可视化库」行）。GROUP_C R10（前端构建阻断修复轮，invocation `INV-GROUP_C-INTELBASE-008`）在 `src/frontend` 执行 `npm install` 后，**逐包实测**解析结果并据实登记于下；`src/frontend/package-lock.json` 已重新生成，锁定以下精确版本。

**核实方法**：对每个包读取 `src/frontend/node_modules/<pkg>/package.json` 的 `version` / `license` 字段，并确认包内 `LICENSE` 文件存在。原始输出：`docs/evidence/groupc_r10_license.log`。

| 包 | 版本（锁定） | 许可 | 性质 |
|----|-------------|------|------|
| `@vue-flow/core`（直接依赖，R7） | **1.48.2** | MIT | 宽松 |
| `@vueuse/core` | 10.11.1 | MIT | 宽松 |
| `@vueuse/shared` | 10.11.1 | MIT | 宽松 |
| `@vueuse/metadata` | 10.11.1 | MIT | 宽松 |
| `vue-demi`（嵌套于 `@vueuse/{core,shared}`） | 0.14.10 | MIT | 宽松 |
| `@types/web-bluetooth` | 0.0.20 | MIT | 宽松 |
| `d3-color` | 3.1.0 | ISC | 宽松 |
| `d3-dispatch` | 3.0.1 | ISC | 宽松 |
| `d3-drag` | 3.0.0 | ISC | 宽松 |
| `d3-ease` | 3.0.1 | **BSD-3-Clause** | 宽松 |
| `d3-interpolate` | 3.0.1 | ISC | 宽松 |
| `d3-selection` | 3.0.0 | ISC | 宽松 |
| `d3-timer` | 3.0.1 | ISC | 宽松 |
| `d3-transition` | 3.0.1 | ISC | 宽松 |
| `d3-zoom` | 3.0.0 | ISC | 宽松 |

**结论（R10）**：14 个传递包（15 个 `node_modules` 条目，`vue-demi` 因嵌套去重计两处）**全部为宽松许可（MIT / ISC / BSD-3-Clause）**，**无 copyleft / AGPL 面** → **不触发 §1 重选型**，REQ-NFR-IB-12 合规。`@vue-flow/core` 由 `^1.41.0` 区间解析并锁定为 **1.48.2**；该版本仍处 `^1` 主版本内，与 §1「主版本随实现锁定（建议 `^1`）」一致。**仍禁止运行期 CDN 加载**（AC-IB-17-06 / REQ-NFR-IB-08）：上述依赖全部经构建本地打包。

**体积实测（R10，`npm run build` 产物）**：`dist/assets/index-*.js` **252.35 kB（gzip 89.20 kB）**、`index-*.css` **12.62 kB（gzip 2.74 kB）** —— 供 [TBD-T20] 引用；目标机（4GB 内存）首屏体积敏感，故仍**不引入** UI 组件库。

---

### 2.2 前端依赖许可登记（**R13 新增**；NFR-12 可核验落点）

**落点与依据**：R13 引入 Element Plus / vue-router 后，须在 `src/frontend` 执行 `npm install` 并**逐包实测**，按 §2.1（R10）同一方法登记**精确版本与许可**（读 `node_modules/<pkg>/package.json` 的 `version` / `license` 并确认包内 `LICENSE` 存在）。

| 包 | 版本（锁定后填） | 许可 | 性质 |
|----|------------------|------|------|
| `element-plus`（直接依赖，R13） | **待 `package-lock.json` 锁定** | **MIT**（R13 经外部核实） | 宽松 |
| `@element-plus/icons-vue`（传递） | 待锁定 | [待核实] | — |
| `@floating-ui/dom` / `@floating-ui/core`（传递） | 待锁定 | [待核实] | — |
| `async-validator`（传递） | 待锁定 | [待核实] | — |
| `lodash-es`（传递） | 待锁定 | [待核实] | — |
| `memoize-one` / `normalize-wheel-es` / `dayjs`（传递） | 待锁定 | [待核实] | — |
| `vue-router`（直接依赖，R13） | 待锁定 | **MIT**（R13 经外部核实） | 宽松 |

**结论（R13，`[待核实]`）**：上表**传递依赖清单为预列**（依据 Element Plus 的已知直接依赖），**具体集合与版本以锁定后的 `package-lock.json` 为准**；须逐包复核后方可判「无 copyleft / AGPL 面」。**在逐包核实完成前，本项结论标 `[待核实]`，不得据此宣称合规已完成**（REQ-NFR-IB-12）。**仍禁止运行期 CDN**：全部依赖经构建本地打包。

**体积实测（R13，`npm run build` 产物，待测）**：Element Plus + vue-router 引入后 `dist/assets/*.js` / `*.css` 体积与 gzip 值 —— 供 **[TBD-T23]** 引用；**建议按需引入**（`unplugin-vue-components` + `unplugin-auto-import`）以控体积；目标机（4GB 内存）首屏体积敏感。

---

## 3. 版本 pin 与已知坑（来自 FreeArk 生产事故经验）

> **（R1）本节为「实现约束」而非「选型建议」**：下列条目即使当前方案**不引入 Channels/Redis**，其前半部分（`?token=` 纪律）仍然适用，且是本项目选定 SSE 的直接动因；后半部分（`channels_redis` × `redis-py`）为**任何未来引入 Channels 时的强制前置**。

| 项 | 纪律 | 事故背景 | 违反后果 |
|----|------|----------|----------|
| `langchain-openai` | **pin `<0.3`** | 0.3.x 移除 `_convert_chunk_to_generation_chunk`，生产环境曾漂移；且会丢弃 DeepSeek `reasoning_content` | 流式静默降级为「无输出」/ 推理过程丢失 |
| **凭据传递（R1 强化为实现约束）** | **禁止把 token 放进 query string**（任何通道：WebSocket / SSE / 普通 HTTP；一律走 `Authorization` 头或正文/中间件注入） | FreeArk ChatConsumer 从 `?token=` 读 token，访问日志完整打印整条 URL | 凭据泄漏入日志；须轮换。**本项目即便全程不用 WebSocket，仍沿用该纪律**，SSE 走标准 HTTP 可带 `Authorization` 头，天然规避该类泄漏 |
| **Redis 生态（R1：若未来引入 Channels 则强制）** | 若引入 Channels + Redis，**须 pin `redis-py` 5.x** 并锁定与 `channels_redis` 的兼容组合 | `channels_redis` 4.3.0 与 `redis-py` 8.0.0 不兼容，WS receive 超时 | WS 收包超时；**且 InMemory 测试测不出**——须以**本地真 Redis** 验证 WS 收发 |
| 字符编码 | 设 `PYTHONUTF8=1` | 中文路径/编码问题在 Windows 与 Linux 表现不一 | 解析/写盘乱码或报错 |
| Python 依赖隔离 | **每进程一个 venv** | 无容器；同机多项目共用进程组 | 依赖冲突致启动失败 |
| 数据库并发 | SQLite **必须开 WAL + `busy_timeout`** | 单写者模型 | `database is locked` 随机失败 |
| 迁移 | **手写 scoped 迁移，禁止全量自动产物** | FreeArk 存在迁移漂移历史 | 部署期 schema 漂移。**（R1）台账不经 Django ORM，故不得使用 `makemigrations` 产物**（ADR-07-R1） |
| 部署 | **`git pull` + systemd 重启；禁止逐文件上传** | 逐文件上传致版本不一致 | 生产与仓库不一致，无法复现 |
| 前端构建 | 小程序侧 `marked` 曾因 `\p{}` 正则致安卓真机白屏 | 模拟器与 iOS 测不出 | 若引入 Markdown 渲染须真机验证 |
| **SSE 承载（R1 新增）** | 响应头须含 `X-Accel-Buffering: no` / `Cache-Control: no-cache`；worker/线程池容量须显式设定并在超限时**快速失败** | 反向代理缓冲会把流式退化为「一次性返回」；worker 被长连接占满会令全站不可用 | SSE 不流式（用户等到全部生成完才见内容）；或全站 503 |

---

## 4. 目标机依赖验证清单（AC-IB-12-04）

> **纪律**：Qdrant、bge-m3、OCR 三项依赖须在目标机**真安装、真导入、真运行**，并留下**可复查证据**。不得以「开发机通过」替代。

**目标机**：Ubuntu `192.168.31.133`（CPU 架构 [ARCH-ASSUMPTION-A4]，硬件规格 [TBD-T13]）；凭据**仅经环境变量**注入。

### 4.1 Qdrant 裸装检查清单（ADR-03 Q1）

| 序号 | 检查项 | 通过判据 |
|------|--------|----------|
| 1 | 官方 `.deb` 在目标 Ubuntu 版本与架构可用（[TBD-T14]） | `apt install ./qdrant_*.deb` 成功；不可用则降级到 tarball（Q2）或源码编译（Q3） |
| 2 | 专用**非特权**系统用户已创建（C-IB-08） | 用户存在且 shell 为 `nologin` |
| 3 | `/var/lib/qdrant/storage` 与 **`/var/lib/qdrant/snapshots`** 均已创建并 `chown` | 目录存在且属主正确（**snapshots 缺失会导致首次启动 panic**） |
| 4 | `/etc/systemd/system/qdrant.service` 已创建 | 含 `User=` / `WorkingDirectory=` / `ExecStart=/usr/bin/qdrant --config-path /etc/qdrant/config.yaml` / `Restart=on-failure` / `LimitNOFILE=65536` |
| 5 | 服务可启动且开机自启 | `systemctl is-enabled` / `is-active` 均为期望值 |
| 6 | REST 与 gRPC 端口可达 | `:6333` 与 `:6334` 在本机可连 |
| 7 | 客户端与服务端大版本匹配 | `qdrant-client` 连通性探测通过 |
| 8 | 建 collection / upsert / query 冒烟通过 | 返回结果符合预期；`Distance.COSINE` 生效 |
| 9 | 在目标规模的延迟/内存/磁盘与**多 collection 伸缩性**已实测 | 记录 [TBD-T5] 数据 |
| 10 | 重启后数据仍在 | 持久化路径正确 |

### 4.2 Embedding（bge-m3）验证清单

| 序号 | 检查项 | 通过判据 |
|------|--------|----------|
| 1 | 推理运行时已安装并可导入 | 导入无误（真跑，非 `pip list`） |
| 2 | 模型权重已就位且**离线可加载** | 断网状态下可完成加载 |
| 3 | `ib-embed` 服务可启动并响应 `/healthz` | HTTP 200 |
| 4 | 单条 embed 返回维度 = 1024，且**已 L2 归一化** | 向量模长 ≈ 1；维度与 `CollectionSpec.dim` 一致 |
| 5 | 冷/热双路径超时行为符合配置 | 超时确实触发降级路径 |
| 6 | 延迟 P50/P95 与内存已实测 | 记录 [TBD-T1]、[TBD-T4]（**不得用开发机数据**） |
| 7 | 冷启动加载耗时已实测 | 记录 [TBD-T3] |
| 8 | 批量最优值与吞吐已实测 | 记录 [TBD-T2] |
| 9 | 自相似度检查：同文本两条路径结果一致（余弦 ≈ 1） | AC-IB-07-02 |
| 10 | 与 Qdrant 距离度量对齐（余弦 vs 余弦） | 跨层检索分数量级合理 |
| **11** | **（R2）目标机指令集基线：推理运行时在目标机完成一次**真推理**（非仅 `pip list`）且**进程未崩溃** | `SIGILL` 零命中；记录目标机 CPU 指令集（是否含 AVX2）→ **[TBD-T18]**；**不得以开发机结果替代**（AC-IB-07-05 同精神） |

### 4.3 OCR 链路验证清单

| 序号 | 检查项 | 通过判据 |
|------|--------|----------|
| 1 | `rapidocr-onnxruntime` + `onnxruntime` 已安装并可导入 | 真导入无误 |
| 2 | OCR 模型首次加载成功且耗时已记录 | 记录 [TBD-T3] |
| 3 | 扫描件 PDF 整页栅格化 → OCR 全链路跑通 | AC-IB-04-06 |
| 4 | 引擎不可用时行为为「跳过 + WARNING」 | AC-IB-04-07 |
| 5 | OCR 与 embedding **同机内存叠加峰值**已实测 | 记录 [TBD-T4'] |
| 6 | 单文档入库时长上界已实测（含 OCR） | 记录 [TBD-T11]（用于校准租约时长） |
| **7** | **（R2）OCR 的 `onnxruntime` 在同一目标机上完成一次真推理且进程未崩溃** | 与 §4.2 第 11 项**同源风险**（[TBD-T18]），**须合并判定**：两者若均触发 `SIGILL`，须一并处置构建方式，不得分别归因 |

### 4.4 平台与合规验证清单

| 序号 | 检查项 | 通过判据 |
|------|--------|----------|
| 1 | Python 版本与 venv 隔离就绪 | 版本满足约束；各进程 venv 独立 |
| 2 | 必填环境变量缺失时给出**可读错误**且非零码退出，且**不回显其值** | AC-IB-12-03 |
| 3 | 凭据不出现在仓库、日志与响应中 | AC-IB-12-02（全模式扫描零命中） |
| 4 | 数据外发边界声明可在配置层追溯 | AC-IB-12-05（启动日志 + `/healthz/deps`） |
| 5 | 目标机硬件规格已记录（核数/内存/磁盘/指令集/GPU） | [TBD-T13] |
| 6 | 中文语料 PDF 提取库对比已实测 | [TBD-T8]（决定 ADR-06 主/回退顺序） |
| 7 | XObject 滤镜覆盖已实测 | [TBD-T9] |
| **8** | **（R1）文档与 URL 全量扫描：无任何 `?token=` / `?key=` / 凭据型 query string** | AC-IB-12-02；§3 纪律 |
| **9** | **（R1）备份与恢复路径已验证（SQLite 文件 + Blob 目录 + Qdrant 快照）** | 可复现恢复；台账与向量库一致性由恢复后对账验证 |

### 4.5 Web 层（Django）与服务承载验证清单（**R1 新增**）

| 序号 | 检查项 | 通过判据 |
|------|--------|----------|
| 1 | Django + DRF 在目标机**真装真导入**（非 `pip list`） | `django-admin --version` 与 `import rest_framework` 均无误 |
| 2 | Django 在**收窄配置**下可正常启动（不启用 `django.contrib.auth` / `admin`，且**不使用 Django ORM 与迁移机制**承载台账） | 服务启动成功并响应 `/healthz`；**仓库内不出现自动生成的迁移产物** |
| 3 | `ib-web` 以 **Waitress（或 Gunicorn）** 由 systemd 拉起、可开机自启、故障重启 | `systemctl is-enabled` / `is-active` 为期望值 |
| 4 | **SSE 真流式跑通**：`GET /api/chat/stream` 逐条推送事件 | 客户端可**逐条**收到事件（非一次性全量）；响应头含 `X-Accel-Buffering: no` / `Cache-Control: no-cache` |
| 5 | **`Authorization` 头鉴权生效**；未授权返回 **401/403**（非静默） | AC-IB-11-05；且凭据不出现在任何 URL 与访问日志中 |
| 6 | **`AuthzPolicy` 未注入即启动失败**（默认 `DenyAllPolicy`） | AC-IB-11-05；启动期报错可读 |
| 7 | **SSE 并发上限与 worker 池耗尽行为已实测** | 记录 [TBD-T15]：达到上限时新连接**快速失败（503 + 可读文案）**，不出现无限排队或全站挂死 |
| 8 | 反向代理（若前置 nginx）不缓冲 SSE | 实测流式未被缓冲；`proxy_buffering off` 类配置生效 |
| 9 | 前端（Vue 3 + Vite）构建产物可托管并完成一次端到端问答 | REQ-FUNC-IB-09/17；**前端不受后端框架切换影响（R1）** |
| **10** | **（R7）前端产物零外发依赖**：图可视化库及全部前端依赖**随构建产物本地打包**；产物体内**不得**出现指向公网 CDN / 字体 / 图床的引用 | 断网状态下可视化配置页可正常加载与渲染；构建产物内公网 URL 扫描**零命中**（AC-IB-17-06；REQ-NFR-IB-08） |
| **11** | **（R7）装配期 fail-fast 实测**：故意提交一份非法定义文档（如条件边缺分支映射 / 默认专家为 0 个或 2 个 / 工具授权引用不存在的工具），观察装配行为 | **拒绝装配、服务不启动**；错误**逐条定位**到 `path` / `code` / `message` 且**不回显凭据值**；**不存在**「启动成功、首次提问才失败」的路径（AC-IB-18-01 / 02 / 03 / 04 / 06） |
| **12** | **（R7）定义文档凭据明文扫描**：定义文档、`.env.example` 与全部响应体扫描 | **零命中**任何凭据型**值**（只允许出现**键名**）；`GET /api/config/definition` 的响应体内**无**任何凭据值或掩码残留（AC-IB-17-05 / AC-IB-18-04；§1.3 纪律） |
| **13** | **（R13）默认管理员种子与首登强制改密**：迁移 `003_accounts.sql` 应用后首登 | `ensure-schema` 幂等重放无副作用；默认管理员首登后被强制改密（未改密前业务端点 `403 password_change_required`）；**日志 / 响应中不含初始口令字面量**（AC-IB-30，[B18]） |
| **14** | **（R13）零 Cookie**：任意响应扫描 | **`Set-Cookie` 零命中**（DR-10，[B16]）；令牌**仅**经 `Authorization` 响应体一次性返回 |
| **15** | **（R13）`?token=` 全端点 4xx** | `/api/auth/*`、`/api/accounts*`、既有端点上 `?token=` / `?access_token=` **一律 4xx**（[B17]） |
| **16** | **（R13）`IB_AUTHZ_POLICY_MODULE` 未配置即启动失败** | 生产未设该键 → **服务拒绝启动**（fail-closed）；设为 `ibweb.accounts.policy` 后可正常启动与鉴权（[B9]） |
| **17** | **（R13）HTTPS 生效** | 外部经 `https://` 可达；`http://` 重定向或拒绝；`ib-web` 仍绑 `127.0.0.1:18080`；SSE 仍不被缓冲（`X-Accel-Buffering: no`）（[B15]） |
| **18** | **（R13）前端自包含 + 凭据不回显** | 断网状态登录页 / 运维控制台可加载；构建产物内公网 URL 扫描零命中；界面只显示**键名**，不显示口令 / 令牌 / 掩码；登录失败文案不区分「用户不存在 / 口令错误」 |

---

## 5. 风险汇总

### 5.1 高风险

| 风险 | 影响 | 缓解措施 | 关联 |
|------|------|----------|------|
| **`langchain-openai` 版本漂移** | 流式静默失效、推理过程丢失、生产与开发不一致 | **pin `<0.3`**；该风险已收敛到 MOD-IB-20 适配器内部（单点可控）；升级须跑骨架回归；必要时直读 SDK delta（[TBD-T10]） | REQ-FUNC-IB-21 |
| **PyMuPDF → 宽松许可库的解析质量回退** | 复杂版面/扫描件抽取质量下降 | 四库组合 + 主/回退顺序可配置；[TBD-T8] 目标机实测决定顺序；端口不变故切换零架构成本 | REQ-FUNC-IB-10；REQ-NFR-IB-12 |

### 5.2 中风险

| 风险 | 影响 | 缓解措施 | 关联 |
|------|------|----------|------|
| CPU-only 下 embedding 延迟不达标（未实测） | 检索 P95 超标 | ADR-02 已内置 7 项缓解（批处理/常驻/并发上限/有界队列/短超时/多 worker/可选 GPU）；**ADR-02 形态可逆**（可切进程内）；不达标则按 AC-IB-07-05 调模型尺寸并回溯 DR-02 由用户裁决 | REQ-NFR-IB-03；[TBD-T1/T6] |
| 目标机硬件规格未知 | 所有性能判断缺乏分母 | 部署前实测 [TBD-T13]；全部性能 AC 以目标机证据为准 | C-IB-03 |
| Qdrant `.deb` 与目标系统/架构不匹配 | 部署路径受阻 | ADR-03 已备 Q1→Q2→Q3 三级回退 | [TBD-T14] |
| 项目数增长致 collection 数增长 | 内存与查询延迟劣化 | collection-per-project 的代价已识别；[TBD-T5] 需覆盖**多 collection 伸缩性**；必要时可合并小项目（改配置） | ADR-04 |
| 知识库级为软隔离 | 漏 filter 即泄漏 | 五重防护：`Scope` 必填、filter 恒含 `project_id`、归属断言 403、启动期前缀断言、`CollectionResolver` 单入口；升级路径已收敛。**（R1）该隔离粒度已由 PM 确认为「软隔离」（ARCH-ASSUMPTION-A2 关闭）** | ADR-04；FM-1 |
| OCR 权重加载耗时与内存占用 | 启动慢、内存峰值高 | 懒加载 + 可用性探测 + `NullOcrEngine` 显式降级；[TBD-T3]/[TBD-T4'] | ADR-12 |
| SQLite 并发写 | `database is locked` | 显式 WAL + `busy_timeout`；单 worker 写路径；短事务 | ADR-07 |
| 多 worker 下会话不共享 | 会话历史漂移 | v1 部署显式声明为单 worker，或接受会话按 worker 归属；`SessionStore` 端口已备替换实现 | REQ-FUNC-IB-20 |
| **（R1 新增）SSE 长连接占满 WSGI worker/线程池** | **并发问答数被 worker 池容量钉死；池满后新连接排队或全站不可用** | ① worker/线程池容量**显式配置**（不依赖默认值）；② 超限**快速失败（503 + 可读文案）而非无限排队**（避免「慢」放大为「全链路超时」）；③ 连接空闲/总时长上限；④ 统一走 SSE 单端点，便于限流；⑤ 已内置升级路径：Django 异步视图 + ASGI（Gunicorn + uvicorn worker，**仍不引 Channels/Redis**）；⑥ 由 [TBD-T15] 在目标机实测并发曲线后定容量与是否触发升级 | REQ-FUNC-IB-21；REQ-NFR-IB-13；ADR-11-R1 |
| **（R1 新增）框架切换引入的集成面**（Django 收窄配置 / 不经 ORM 的台账 / 中间件鉴权） | 装配错误导致启动失败或鉴权静默放行 | 组合根为**唯一装配点**；`AuthzPolicy` 未注入即启动失败；§4.5 逐项目标机验证；台账端口一致性测试保证换载体不改语义 | REQ-NFR-IB-09/11 |
| 云端 LLM 不可达/限流 | 问答不可用 | §7.4 降级矩阵：`error` 事件 + 可读文案；路由降级到关键词档位 | REQ-NFR-IB-13 |
| **（R2 新增）目标机 CPU 缺 AVX2 → 预编译 wheel 触发 SIGILL** | **进程级崩溃（不可捕获），非降级**：`ib-embed` 与 OCR 链路**双双不可用**；且**开发机（新 CPU）可用掩盖问题**，只在目标机暴露 | ① **[TBD-T18] 目标机实测优先**：先跑「导入 + 一次真实推理」的最小探针，**不以 `pip list` 或开发机结果代替**；② 判定后三选一 —— **换用无 AVX2 依赖的构建**（如 CPU 版 wheel 的兼容包）/ **自源码编译并关闭 AVX2**（`-mno-avx2` 类开关）/ **降级到纯 Python 后备路径**；③ **两条链路须合并评估**（OCR 的 `onnxruntime` 与 R2 的推理运行时**同源**）：分别修会重复踩坑且排障归因错误；④ 若实测确有 SIGILL 且无可用构建，须**回 PM 裁决**是否放宽 DR-08 / 降级 OCR 能力（**不得**以引入 PyMuPDF 或 Docker 规避） | REQ-NFR-IB-10；AC-IB-07-05；ADR-02 / ADR-06 / ADR-12；[TBD-T18] |
| **（R13 新增）bcrypt cost 在 CPU-only 目标机拖慢登录**；会话索引查询与限速阈值未标定 | 登录 P95 超标；阈值错配致误锁或形同虚设 | ① cost 与 TTL / 窗口 / 阈值**全部可配置**（IFC-IB-312）→ 改键值即调，**上层零改动**；② **[TBD-T22] 目标机实测**后再定默认值；③ 限速与审计为**条件性**（ADR-27，OQ-IB-12/13 未裁决前不启用，不留「半开」旋钮）；④ `sessions` 建 `(expires_at)` 索引 + 定期 purge | REQ-NFR-IB-15/16；[ARCH-ASSUMPTION-A9] |

### 5.3 低风险

| 风险 | 缓解 |
|------|------|
| 前端 Markdown 渲染兼容性 | 若引入 Markdown 渲染，须**真机验证**（FreeArk 有 `marked` 正则致安卓白屏的前科） |
| venv 依赖隔离依赖纪律 | 每进程一 venv；锁文件入库；部署前 `pip install -r` 校验 |
| 反向代理缓冲破坏 SSE | 部署检查项：禁用响应缓冲（`X-Accel-Buffering: no`） |
| **（R7 新增）定义文档被写入凭据明文** | 缓解：定义文档**只允许出现键名**（§1.3）；界面与校验错误**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；§4.5 第 12 项加入「定义文档凭据明文扫描」；仓库内**不得**出现除 `.env.example` 之外的任何真实值 |
| **（R7 新增；R10 已收敛）图可视化库传递依赖的许可与体积** | 缓解：主体 `@vue-flow/core` 的 **MIT 已外部核实**；传递依赖（D3 系 / `@vueuse/core`）**已于 R10 锁定版本后逐包复核并登记**于 **§2.1**（14 包全部 MIT / ISC / BSD-3-Clause，**无 copyleft 面**，故**不**回 §1 重选）；体积与渲染规模上界以 **[TBD-T20]** 实测为准（R10 已测产物 JS 252.35 kB / gzip 89.20 kB）；**禁止 CDN**（AC-IB-17-06） |
| **（R13 新增）Element Plus 传递依赖的许可与体积** | 缓解：主体 `element-plus` 的 **MIT 已外部核实**；**传递依赖须在锁定版本后逐包复核并登记于 §2.2**（未核实前 `[待核实]`；出现 copyleft / AGPL 面即回 §1 重选）；体积以 **[TBD-T23]** 实测，**建议按需引入**；**禁止 CDN**（REQ-NFR-IB-17）。另：**口令 / 令牌泄露风险** —— 缓解：只存摘要（bcrypt / sha256，IFC-IB-311/313）、令牌仅经 `Authorization`、`?token=` 全端点 4xx、`.env` 0600（[B19]）、日志字段白名单（[B14]） |

---

## 6. 自检声明

- 本表每项均有 **Rationale**、**关联 REQ-*** 与**风险**列，无空缺（门控要求）。
- 版本列采用「约束 + 部署时锁定」策略，**未编造精确小版本号**；不确定事实标 `[待核实]`。
- 许可合规逐项登记（§2），**未沿用「内部平台合规」口径**，且**明确记录 PyMuPDF (AGPL-3.0) 不采纳及其三条合规前置条件的逐条判定**；**（R1）新增登记的 Django / DRF / Waitress / Gunicorn 许可已经外部核实**（BSD-3-Clause / BSD-3-Clause / ZPL-2.1 / MIT），未凭印象登记，且已纳入「锁定版本后按发行包 `LICENSE` 复核」的遗留动作。
- 目标机依赖验证清单（§4）对应 AC-IB-12-04，要求**真装、真导入、真跑通、可复查**；**（R1）新增 §4.5 Web 层验证清单**（Django 真装真导入、收窄配置可启动、SSE 真流式、`Authorization` 鉴权、并发上限实测）。
- **（R1）框架切换留痕**：FastAPI / Uvicorn / Pydantic 退出采纳清单的处置已写明（§1「（R1 改写）」行 + §1.1 留痕 + §2 撤销行），并给出 **Pydantic 的保留边界（可选独立校验库，不得作端口契约载体）**；前端 Vue 3 + Vite **未变**。
- **（R1）两个 FreeArk 已知坑已同时落入 ADR 与实现约束**：`?token=` 入访问日志（§3，适用于任何通道）、`channels_redis` × `redis-py` 不兼容（§3，未来引入 Channels 时强制 pin `redis-py` 5.x 且须真 Redis 验证）。
- 本文**不含实现代码与部署脚本**，**不含任何凭据/密钥/令牌**（仅登记配置键名），**未修改 FreeArk 任何文件**，**未修改需求侧文档**。
- 本阶段**止于 GROUP_B**：产出后停止，等待 PM 门控评审，不进入 GROUP_C。
- **（R13）认证 / 会话 / 商用界面的技术面结论**：① 新增 **前端 UI 组件库 = Element Plus（MIT，R13 经外部核实，DR-13）**、**前端路由 = `vue-router`（MIT，hash 模式）**、**口令哈希库 = `bcrypt`（Apache-2.0，DR-11）**（§1 三新行）；§1.1 留痕 **5 项**已评估未采纳（Cookie 会话 / JWT 自包含令牌 / 独立鉴权服务 / Django `contrib.auth`+ORM 迁移 / **运行期 CDN 加载 Element Plus**）；② §2 台账登记三新组件（**采纳**）+ **传递依赖（`[待核实]`）**，新增 **§2.2 前端依赖许可登记**（方法同 R10，**结论暂标 `[待核实]`**）；③ 新增 **§1.4 客户端配置键登记**（只登记键名，**不含任何值**）；④ §4.5 新增第 **13 ~ 18** 项（种子与首登改密 / 零 Cookie / `?token=` 全端点 4xx / `IB_AUTHZ_POLICY_MODULE` 未配即启动失败 / HTTPS 生效 / 前端自包含与凭据不回显）；⑤ §5.2 新增一行中风险（bcrypt cost 与阈值标定，以 [TBD-T22] 为准）、§5.3 新增一行低风险（Element Plus 传递依赖许可与体积 + 口令/令牌泄露缓解）。
- **（R13）禁项与硬约束未松动**：**未引入 Docker / 容器化**（DR-03）、**未引入 Redis / RabbitMQ**（C-IB-08）、**未引入 PyMuPDF 或任何 AGPL / copyleft 组件**（REQ-NFR-IB-12）、**未引入 Cookie 会话**（DR-10）、**未引入 Django ORM / `contrib.auth`**（ADR-07-R1）、**未引入独立鉴权服务**（DR-09）；UI 组件库与路由**随构建产物本地打包、禁止运行期 CDN**（REQ-NFR-IB-17）；**端口契约仍 framework-free**（新增契约全部落在 MOD-IB-01，纯 stdlib）。
- **（R13）凭据纪律**：§1.4 / IFC-IB-312 **只登记键名**；**默认初始口令的字面量不在本文件出现**；全文**不含任何键值**；`?token=` / `?key=` 纪律由 §3 **扩展至全部新端点**（`/api/auth/*`、`/api/accounts*`）；日志扫描须零命中（[B14]）。
- **（R13）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档**只读未改**；`architecture_design.md` / `module_design.md` 的 R1 / R2 / R7 / R8 结论**未改写**（R13 只追加）；`implementation_plan.md`（GROUP_C）**未改**；**未写入任何口令 / 令牌 / 密钥字面量**；本阶段**止于 GROUP_B**。
- **（R13）版本订正说明**：任务文本称本文件由 1.3.0 升 1.4.0；**实际起版为 1.3.1**（R7 + R10 传递依赖许可登记，`author=software-developer`）→ 本提案为 **1.3.1 → 1.4.0 / REV-13**。
- **（R2）L-03 补交已完成**：新增 **§1.2 服务端配置键登记**（`ib-embed` / MOD-IB-26 的配置**键名**清单，**只登记键名与语义、不含任何值**，对应 IFC-IB-286 的第二份 `EnvironmentFile`）；「Embedding 推理运行时」行改写为**三候选**并显式化**选择依据 / 许可 / CPU-only 可用性 / 传递依赖 / 指令集基线风险**；§2 台账补登传递依赖 `torch`（BSD-3-Clause）与 `transformers`（Apache-2.0）（**条件性采纳**）；§5.2 新增**目标机缺 AVX2 → SIGILL** 风险行（该风险**同时命中既有 OCR 链路**，须合并评估）。
- **（R2）技术面硬约束未松动**：**未引入 PyMuPDF**（仍为 AGPL-3.0，不采纳）、**未引入 Docker/容器化**（DR-03）、**未引入 Redis/RabbitMQ**；新候选 ③（`onnxruntime` 直载）与既有 OCR 运行时**同组件**，**未净增组件面**。
- **（R2）凭据纪律**：§1.2 **只登记键名**；`ib-embed` **不需要任何令牌**，其 `EnvironmentFile` **不得**写入任何凭据；全文**不含任何键值**。
- **（R7）可视化配置增量的技术面结论**：① 新增**前端图可视化库 = Vue Flow（`@vue-flow/core`，MIT，R7 经外部核实）**（§1 新行）；§1.1 留痕 **5 项**已评估未采纳（AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / **运行期 CDN 加载**）；② §2 台账登记 Vue Flow（**MIT，采纳**）与**传递依赖（条件性采纳 + `[待核实]`）**；③ 新增 **§1.3 客户端配置键登记**（只登记键名 `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`，**不含任何值**）；④ §4.5 新增第 **10~12** 项（前端产物**零外发依赖**、**装配期 fail-fast 实测**、**定义文档凭据明文扫描**）；⑤ §5.3 新增两行低风险（定义文档被写入凭据明文 / 图库传递依赖的许可与体积，后者以 [TBD-T20] 实测为准）。
- **（R7）禁项与硬约束未松动**：**未引入 Docker / 容器化**（DR-03）、**未引入 Redis / RabbitMQ**（C-IB-08）、**未引入 PyMuPDF 或任何 AGPL / copyleft 组件**（REQ-NFR-IB-12）；图库**随构建产物本地打包、禁止运行期 CDN**（数据不出本地，AC-IB-17-06）；**端口契约仍 framework-free**（新增契约落在 MOD-IB-01，纯 stdlib / frozen dataclass，零第三方依赖）。
- **（R7）凭据纪律**：§1.3 **只登记键名**；定义文档内**只允许出现键名**；全文**不含任何键值**；`?token=` / `?key=` 纪律由 §3 **扩展至全部新端点**（含定义文档的 `GET` / `PUT`）。
- **（R7）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`architecture_design.md` / `module_design.md` 的 R1 / R2 结论**未改写**（R7 只追加）；`implementation_plan.md`（GROUP_C）**未改动**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为**离线自检用例数**，与本表的 REQ 计数口径无关，**不得混淆**）。
- **（R2）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`architecture_design.md` / `module_design.md` 的 R1 结论**未改写**（R2 只追加）。
