<file_header>
  <project>intelligentbase</project>
  <artifact>implementation_plan</artifact>
  <path>docs/implementation_plan.md</path>
  <doc_id>IMPL-INTELBASE-001</doc_id>
  <version>2.12.0</version>
  <status>DRAFT</status>
  <phase>GROUP_C / PHASE_05 实现计划（R7 定义外置增量 + R8 缺陷修复增量 + R10 前端构建阻断修复增量 + R11 IB-20 流式/会话增量 + R13 账户/会话/商用界面增量 + R13.1 回修增量 DEFECT-R13-01 来源 IP 限速修复 + R14 回归缺陷修复增量 全局管理员「当前项目」选择与 X-IB-Project 传播 + REV-16-2 提示词分层与工具可视化配置增量 + REV-16-4 回归缺陷修复增量 DEFECT-R16-01/02 与 GAP-R16-03/04 配置审计与存储态 + REV-17 提示词兜底层重定位增量 提示词文本移出定义文档 / 合并结果进 system 位 / 通用内置安全网破新增专家死锁）</phase>
  <author>software-developer</author>
  <invocation_id>INV-GROUP_C-INTELBASE-018</invocation_id>
  <latest_invocation_id>INV-GROUP_C-INTELBASE-018</latest_invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-10-07</updated_at>
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
    R10（v2.5.0，invocation INV-GROUP_C-INTELBASE-008）为**前端构建阻断修复增量**（输入 = PM 只读取证：CI 阶段9 在 `src/frontend` 执行 `npm ci` 因**锁文件与 `package.json` 失同步**而 EUSAGE 失败，`npm run build` 永不抵达）。修三处**交付管线阻断**：①**锁同步** —— `src/frontend/package-lock.json` 内**无** `@vue-flow/core` 任何条目（R7 引入该依赖时未随锁提交），重新 `npm install` 生成，纳入 `@vue-flow/core` **1.48.2** 及其 **14 个传递包**；②**未跟踪源文件** —— `src/frontend/src/views/ConfigPage.vue`（被已跟踪的 `App.vue` 导入）此前**未纳入 git**，CI checkout 后 `vue-tsc` 必因缺文件而失败，本轮 `git add` 纳入版本控制；③**类型错误** —— `ConfigPage.vue` 导入未使用的 `type ExpertSpecInput`，在 `noUnusedLocals: true` 下直接 `TS6133` 致 `vue-tsc --noEmit` 失败，删除该无用导入。另落地**前端冒烟测试最小入口**（`package.json` 新增 `test` = `node --test`，纯 Node 内建、**零新增依赖**；含「锁与 `package.json` 同步」回归闸）并据实登记传递依赖许可于 `tech_stack.md` §2.1。**本文件沿用自身版本线 2.4.0 → 2.5.0**，**与 GROUP_B 文档属各自独立版本线**。**未新增模块（仍 26）/ 未改端口数（仍 14）/ 未改任何 IFC-IB 号或签名 / 未改后端 `src/ib`·`src/ibweb`·`src/ib_embed` 任何行为 / 未改配置键名与默认值**，只追加（见 §17）。正文 §1~§16 为 R1~R8 的**历史记录，未改写**。R11（v2.6.0，invocation INV-GROUP_C-INTELBASE-010；协调者轮次口径亦记作 **REV-12**）为 **IB-20 流式交付 / 会话生命周期的实现增量**（输入 = `docs/module_design.md` **1.4.0/R8** §2.1 / §2.2.3 / §3 + `docs/architecture_design.md` **1.4.0/R8** **ADR-17**；上一轮 REV-11 第 1 项的遗留「4 项部分覆盖 + 2 项未覆盖 AC」正是因 `IFC-IB-298~308` 尚未实现，本轮闭合）。**命名口径声明**：GROUP_B 把该设计增量记为 **R8**（`module_design.md` 1.4.0/R8），而 GROUP_C 自身的版本线在 **v2.4.0** 已用掉「R8」这一标签（FND-R7-01 修复轮）—— 故本文件按协调者本轮口径记为 **R11**，并在本节内同时标注设计侧编号 **R8/ADR-17/IFC-IB-298~308**，避免两套版本线互相覆盖。**四件事**：①**REV-12-1** 落地 `IFC-IB-298~308`（会话状态与轮次 / 持久化策略与状态丢失结局 / 完成产物与引用 / 确认中间态三件套 + `StreamEventKind` **追加** `confirmation_required` / 终态单发 `completion_event` / 可见性白名单 `is_user_visible` / 三个键名登记与 `IB_SESSION_BACKEND` 值域扩展 / 类型化恢复载荷 `ResumePayload` / 纯函数 `can_resume` / `POST /api/chat/resume` 端点 / 前端确认区呈递与决策回传约束）；②**REV-12-2** 使 `ExpertSpec.is_delegating` / `delegating_experts()` 不再是死字段（G2 专家单跳交接落地，默认关闭；**三护栏口径按 R11 补丁轮 MAJOR-2 精确改写**——护栏①③**已实现**、护栏② = 机制就绪但**组合根未接线 → 不可经配置触发**（**OPEN：GAP-R11-07**），详见 §18.3 / §18.8）；③**REV-12-3** 修 **FND-R11-01**（`chat_stream_endpoint` 缺会话标识**不得**静默回退字面量 `"default"` → 显式 4xx）；④**REV-12-4** 落地 **BLK-R8-02**（`validate()` 追加第 3 子项：**同专家内**关键词空 / 重复，**先归一化再比较**）。**本文件沿用自身版本线 2.5.0 → 2.6.0**（R2=2.0.0 → R3=2.1.0 → R4=2.2.0 → R7=2.3.0 → R8=2.4.0 → R10=2.5.0 → R11=2.6.0），**与 GROUP_B 文档的 1.4.0/R8 属各自独立版本线**。**未新增模块（仍 26）/ 未改端口数（仍 14）/ 未改任何既有 IFC-IB 号或签名文本（`IFC-IB-221~225` / `231~233` / `247` 一字未改）/ 未改模块边界 / 未改依赖边（DAG 不变）/ 未改既有配置键名与默认值（`IB_SESSION_BACKEND` **仅扩展值域**）/ 未新增第三方依赖**，只追加（见 §18）。正文 §1~§17 为 R1~R10 的**历史记录，未改写**（受保护行在 §18.7 复核）。
    R13（v2.7.0，invocation INV-GROUP_C-INTELBASE-012；设计侧口径 **REV-13**）为**账户 / 会话 / 商用界面重构增量**（输入 = `docs/module_design.md` **1.5.0/REV-13** §2.1 / §2.2 / §2.2.4 / §3 + `docs/architecture_design.md` **1.5.0/REV-13** ADR-18~ADR-27 + `docs/tech_stack.md` 1.4.0/REV-13 + `docs/requirements_spec.md` 1.4.0/REV-13（REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）；上游 GR-B-006 = PASS_WITH_CONDITIONS）。**五件事**：①**账户与会话契约 + 第 15 个端口** `AccountStore`（MOD-IB-01，IFC-IB-309~311：类型化数据结构 / 13 方法 `Protocol` / 令牌原语 `new_session_token`·`token_digest`·`token_digest_matches`）；②**键名登记**（MOD-IB-02，IFC-IB-312，**仅登记键名不含值**）；③**SQL 适配器 / bcrypt / 幂等种子 / 离线替身**（MOD-IB-11，IFC-IB-313~315：`SqliteAccountStore` 与 `MemoryAccountStore` 共用同一 SQLite 台账与同一手写 scoped 迁移机制）；④**端点 / 解析器 / 可注入策略 / 中间件扩展 / 组合根装配 / 条件性限速审计**（MOD-IB-23，IFC-IB-316~326：登录·登出·主体查询·改密·续期 + 账户 CRUD + 内置 `SessionTokenResolver` 与 `ibweb.accounts.policy` + 改密态受限会话 + `?token=` 全端点 4xx + `LoginThrottle`）；⑤**前端商用界面重构**（MOD-IB-24，IFC-IB-327~329：登录页 + 首登强制改密 + 运维控制台外壳 + `vue-router`(hash) 鉴权守卫 + 类型化 API 客户端扩展；Element Plus 与 vue-router 经 **npm 本地打包**，**禁运行期 CDN**）与**部署落点**（MOD-IB-25，IFC-IB-330~332：手写迁移 `003_accounts.sql` + nginx TLS 终止模板 + 清单 B15~B20）。**"粘贴服务令牌"入口前后端彻底移除、无旁路**；**零 Cookie**（不透明令牌仅经 `Authorization: Bearer`）；**既有可注入 `AuthzPolicy` 端口仍是唯一授权真源**（账户模块只提供 `PrincipalResolver`）；**首登强制改密为服务端受限会话（结构性不可绕过）**；**默认管理员初始口令只从 `IB_DEFAULT_ADMIN_PASSWORD` 读**（仓库 / 日志 / 响应零字面量）。**本文件沿用自身版本线 2.6.0 → 2.7.0**（R2=2.0.0 → … → R11=2.6.0 → R13=2.7.0），**与 GROUP_B 文档的 1.5.0/REV-13 属各自独立版本线**。**未新增模块（仍 26）/ 端口 14 → 15（纯追加）/ 未改任何既有 IFC-IB 号或签名文本（`IFC-IB-001~308` 一字未改）/ 未改模块边界 / 未改依赖边（DAG 不变；`module_design.md` §4.2.4 再声明）**；后端唯一新增第三方依赖 `bcrypt&gt;=4,&lt;5`（Apache-2.0，已登记），前端新增 Element Plus（MIT）与 vue-router（MIT）**按 DR-13 登记且本地打包**，只追加（见 §19）。**5 条架构偏差**（D-R13-01~05）在 §19.5 逐条登记。正文 §1~§18 为 R1~R11 的**历史记录，未改写**。
    R13.1（v2.8.0，invocation INV-GROUP_C-INTELBASE-013）为 **GROUP_C 回修增量**（缺陷由 GROUP_D 门控 `condition_1` 登记并路由：**DEFECT-R13-01**（MEDIUM），可执行证据 = `tests/integration/test_accounts_int_r13.py::TC-INT-119`）。**只修一个缺陷、零新增能力**：来源 IP 维度的登录限速未生效（429 分支不可达）—— 根因是 `src/ibweb/views.py::auth_login_endpoint` **每请求** `build_throttle()` 新建一个空 `LoginThrottle`，其滑动窗口 `_hits` 为**实例态**，计数永不跨请求累积。修复：把限速器提升为**应用级单例** —— 组合根 `_assemble()` 装配期构建一次并存入 `Deps.login_throttle`（= 每应用实例一份，测试 `build_deps(force=True)` 天然隔离），登录端点经 `_login_throttle()` 取用；同时把「取账户 + 判锁定」前置于 429 判定，使**已锁定账户仍返回统一 401**（AC-IB-29-01），避免 IP 维度的 429 遮蔽账户维度锁定（否则 TC-INT-118 契约破裂）。**本文件沿用自身版本线 2.7.0 → 2.8.0**（R2=2.0.0 → … → R13=2.7.0 → R13.1=2.8.0），**与 GROUP_B 文档的 1.5.0/REV-13 属各自独立版本线**。**未新增模块（仍 26）/ 未改端口数（仍 15）/ 未改任何 IFC-IB 号或签名文本 / 未改模块边界 / 未改依赖边（DAG 不变）/ 未改配置键名与默认值 / 未新增第三方依赖 / 未改任何测试用例（`tests/**` 未触碰）**，只追加（见 §20）。正文 §1~§19 为 R1~R13 的**历史记录，未改写**。
    R14（v2.9.0，invocation INV-GROUP_C-INTELBASE-014；设计侧口径 **REV-14**）为 **GROUP_C 回归缺陷修复增量**（输入 = `docs/architecture_design.md` **1.6.0/REV-14** **ADR-28** + §2.0.5 + §10.1；`docs/module_design.md` **1.6.0/REV-14** IFC-IB-333~336 + §2.2.5 + §3 MOD-IB-23/24 增补；`docs/tech_stack.md` 1.4.0/REV-13 **NO_CHANGE**；上游 GROUP_B 已 APPROVED = GR-B-007）。**修复 R13 引入的回归缺陷**：全局管理员（`users.project_id IS NULL`）因「前端从不下发 `X-IB-Project` + 后端无项目枚举端点」无法使用任一项目级页面（问答 / 资料 / 重建 / 可视化配置；后者 `503` fail-closed）。**四件事**：①**后端项目枚举端点** `GET /api/projects`（MOD-IB-23，IFC-IB-333）：数据源 = 组合根 `Deps.projects`（**不新增表 / 不经 ORM / 不新增端口**），全局主体见**全部** / 项目绑定主体（ops）**仅见自身**（长度恒为 1），**不是**项目级端点（未选定项目的全局主体同样 `200`）；②**`X-IB-Project` 头契约**（MOD-IB-23，IFC-IB-334；**加成式扩展**既有 `AuthMiddleware`，其文本不动）：已实现语义的契约化登记，ops 跨项目 → `403 project_mismatch`，缺省 → 全局哨兵 → 项目级端点 fail-closed；③**前端项目上下文 store**（MOD-IB-24，IFC-IB-335；新建 `stores/project.ts`，与 `session.ts` 同构、**不引 Pinia**）：`available` / `current`（null = 未选 ⇒ 不注入头）/ `load` / `select`（仅 admin）/ `clear` / `headerValue`（唯一取值出口）；④**`client.ts` 单一注入点**（MOD-IB-24，IFC-IB-336）：`headers()` 追加 `X-IB-Project`（值只来自 store），**自动覆盖 SSE 调用点**（`chatStream` / `chatResume` 已同经 `this.headers()`），并以「客户端暴露提供者 + `app/env.ts` 注入」断开 `client.ts ↔ project.ts` 的 ESM 循环依赖。前端控制台把静态项目文本替换为 **admin 可选 / ops 只读**的项目选择器，并对 `&lt;router-view :key="当前项目"&gt;` **切换即重置项目内视图态**（防串项显示）。**未新增模块（仍 26）/ 未改端口数（仍 15）/ 未改任何既有 IFC-IB 号或签名文本（`IFC-IB-001~332` 一字未改，新增 333~336）/ 未改模块边界 / 未改依赖边（DAG 不变）/ 未改配置键名与默认值 / 未新增第三方依赖**；**fail-closed 纪律未削弱**（未选项目 ⇒ 不注入头 ⇒ 项目级端点继续 fail-closed）。另**顺带修复一处既有潜伏缺陷**（MINOR）：`client.ts` 模块级 `import.meta.env` 在 Node 下为 `undefined` 致整模块无法导入，与其「可被离线自检脚本导入」的自身契约冲突，已防御性回退 `?? {}`（Vite 构建期行为逐位不变）。**本文件沿用自身版本线 2.8.0 → 2.9.0**（R2=2.0.0 → … → R13=2.7.0 → R13.1=2.8.0 → R14=2.9.0），**与 GROUP_B 文档的 1.6.0/REV-14 属各自独立版本线**。只追加（见 §21）。正文 §1~§20 为 R1~R13.1 的**历史记录，未改写**。
    REV-16-4（v2.11.0，invocation INV-GROUP_C-INTELBASE-016；设计侧口径 **REV-16-4**）为 **GROUP_C 回归缺陷修复增量**（输入 = `docs/module_design.md` **1.8.0/REV-16-4** §2.2.7（IFC-IB-355~363）+ §3 MOD-IB-01/02/11/23/24 增补 + `docs/architecture_design.md` **1.8.0/REV-16-4** ADR-33/34/35 + §2.0.7；上游 gate GR-A-009 = PASS / GR-B-009 = PASS）。**修两缺陷 + 补两缺口，共四件事**：①**DEFECT-R16-01**（`src/ibweb/serializers.py::_ToolGrantSpecSerializer` 只声明 `expert_name`/`tool_names`，漏 `param_values` ⇒ GET→PUT 原样读回**静默丢参**）：改为与该文件既有纪律同构的**手写 `to_representation`**（同 `_EdgeSpecSerializer`），保序输出 `param_values` 为 `[{"name","value"}, …]`，**不改任何其它字段的线形**；②**DEFECT-R16-02**（保存路径只跑 `validate`（290），漏掉工具参数校验（346），致「保存期接受、装配期拒绝」的漂移）：新增**合成纯函数** `validate_definition_full`（MOD-IB-02，IFC-IB-355）= 290 ∪ 346，**保存路径**（`_put_definition_config`）与**装配路径**（`admit_two_domains`）**共用同一入口**（ADR-33）；被拒保存返回文档化 4xx 且**在用配置逐字节不变**（fail-safe）；`ValidationReport` 仍不含 `force`/`ignore`/`warn_only`；**未改 `validate()` / `store.validate()` / 任何既有 IFC 的签名**；③**GAP-R16-03**（ADR-35）：落地 `StorageState`（MOD-IB-01，IFC-IB-361）与只读端点 `GET /api/config/storage-state` → `get_storage_state`（MOD-IB-23，IFC-IB-362，**单一来源 = 装配期实际选用的存储实现**，非从环境变量再推导）+ 配置页**内存态非静默提示**（MOD-IB-24，IFC-IB-363）；**不改变**「保存 + 服务重启重装配」生效口径、**不引入**运行期热重载；④**GAP-R16-04**（ADR-34）：落地只读审计 `ConfigAuditEntry`（IFC-IB-356）/ 第 **17** 个端口 `ConfigAuditStore`（IFC-IB-357，**恰好 2 方法** `record`/`list_by_project`，**无 update/delete**）/ `SqliteConfigAuditStore`（IFC-IB-358，同一 SQLite 台账，手写迁移 `004_config_audit.sql`）/ `record_config_audit` + 保存路径审计挂钩（IFC-IB-360，顺序 = 校验 → 落盘 → 审计写；**审计写与配置写非事务耦合**，失败不改变保存结果但发结构化 `WARN config_audit_write_failed`）/ `GET /api/config/audit` → `list_config_audit`（IFC-IB-359）；成功与失败**均**记录（`result ∈ {"saved","rejected"}`，失败带 `detail_code` 只含字段名/码）。**未新增模块（仍 26，MOD-IB-01~26）/ 端口 16 → 17（纯追加）/ 未改任何既有 IFC-IB 号或签名文本（`IFC-IB-001~354` 一字未改）/ 未改模块边界 / 未新增 §4.1 依赖边（DAG 不变）/ 未改既有配置键名与默认值 / 未新增第三方依赖（仅 stdlib `sqlite3`）**，只追加（见 §23）。正文 §1~§22 为 R1~REV-16-2 的**历史记录，未改写**。
    [元数据订正 — 无领域变更]（2026-10-07，PM 机械落盘；回链 phase_status.md 审计日志）：file_header 的 inputs 块此前仍声明 R2 期版本（architecture_design / module_design / tech_stack 1.2.0/R2、ib_embed_service_contract 1.1.0/R2、requirements_spec 1.1.0），早已不是事实；现按各文档头部实测版本订正为 architecture_design.md 1.8.0/REV-16-4、module_design.md 1.8.0/REV-16-4、tech_stack.md 1.4.0/REV-13、ib_embed_service_contract.md 1.0.0/R2（原声明 1.1.0 本身即笔误）、requirements_spec.md 1.7.0/REV-16-3，并新增 user_stories.md 1.8.0/REV-16-4 一条。**本文件版本号不递增**（无领域变更；依 file_header inputs 指针元数据订正的既有先例，避免向 test_report.md / test_plan.md 的『上游输入』as-of 记录级联引入新陈旧引用）。正文与 §1~§23 一字未改。
    REV-17（v2.12.0，invocation INV-GROUP_C-INTELBASE-018；设计侧口径 **REV-17**）为**提示词兜底层重定位增量**（输入 = `docs/architecture_design.md` **1.9.0/REV-17** 的 **ADR-36** + **ADR-15-R2** + 经修订的 ADR-29 / ADR-31 / ADR-33 与 §2.0.8 R17 影响复核表；`docs/module_design.md` **1.9.0/REV-17** 的 **IFC-IB-364 / IFC-IB-365** 与 §2.2.8 REV-17 文字修订索引；`docs/requirements_spec.md` **1.8.0/REV-17** 的 REQ-FUNC-IB-37/38/41 与 C-IB-41 补注）。**三件事**：①**提示词文本彻底移出定义文档** —— `ExpertSpecInput` 删 `fallback_prompt`（`ExpertSpec.fallback_prompt` **原样保留**为安全网本体）、可编辑白名单删 `experts[].fallback_prompt`、`_semantic_payload` 同步（既有文档 `content_hash` 因此**一次性全变**）、legacy 键**分级处置**（与内置逐字相同 → 静默丢弃；不同 → `ConfigError` 并指明迁移目标 `fallback.md`，**只报长度不回显正文**）；②**合并结果进 system 位** —— `LlmProvider.build_expert(spec, *, system_prompt: str | None = None)`（IFC-IB-212 补形参，**消解** llm/__init__.py 那条「可按 spec.name 加载后经 system_prompt 覆盖」的**假陈述 docstring**），编排层改传 `system_prompt=prompt or None` 且 human 位只留用户问题；③**通用内置安全网破死锁** —— 新增 IFC-IB-365（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `builtin_fallback_for` / `builtin_fallbacks_for`，快照**由 `_DEFAULT_SPECS` 派生**，**不取** `EXPERT_SPECS` —— `install_derived` 会 rebind 而 `build_deps(force=True)` 不回滚全局 `EXPERT_SPECS`）+ 新增 IFC-IB-364 `validate_two_domains`（= `validate_definition_full` ∪ `validate_prompt_directory`，域序固定：定义域 → 工具域 → 提示词域），使**保存期与装配期共用同一校验入口**。**本文件沿用自身版本线 2.11.0 → 2.12.0**（R2=2.0.0 → … → R14=2.9.0 → REV-16-2=2.10.0 → REV-16-4=2.11.0 → REV-17=2.12.0），**与 GROUP_B 文档的 1.9.0/REV-17 属各自独立版本线**。**未新增模块（仍 26）/ 未改端口数（仍 17）/ 未新增第三方依赖 / 未改模块边界 / 未改依赖边（DAG 不变）/ 未改配置键名与默认值 / 未 bump `schema_version`**（无迁移机制；bump 会让所有 v1 文档在 `load()` 阶段硬失败致服务起不来）；`IFC-IB-001~363` 中**被修订的 10 条**（IB-212 / 287 / 290 / 292 / 338 / 339 / 343 / 345 / 347 / 355）**编号与签名名一字不改**，只改口径并在两处索引逐条登记。只追加（见 §24）。正文 §1~§23 为 R1~R17 之前各轮的**历史记录，未改写**。</revision_note>
  <inputs>
    <input path="docs/architecture_design.md" version="1.9.0" revision="REV-17" status="APPROVED（以 phase_status.md 为权威；文件头 status 字段仍为 DRAFT_FOR_GATE_REVIEW；GROUP_B GR-B-009 = PASS / REV-16-4；REV-17 新增 ADR-36 与 ADR-15-R2、明文修订 ADR-29 / ADR-31 / ADR-33、新增 §2.0.8 R17 影响复核表）"/>
    <input path="docs/module_design.md" version="1.9.0" revision="REV-17" status="APPROVED（同上；REV-17 增补 IFC-IB-364 / IFC-IB-365 与 §2.2.8 REV-17 文字修订索引，端口数不变仍 17）"/>
    <input path="docs/tech_stack.md" version="1.4.0" revision="REV-13" status="APPROVED（同上；REV-13 / REV-16-2 / REV-16-4 / REV-17 均判 NO_CHANGE）"/>
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="APPROVED"/>
    <input path="docs/requirements_spec.md" version="1.8.0" revision="REV-17" status="APPROVED（REV-17 收窄 REQ-FUNC-IB-37/38/41 的落盘载体措辞并补 C-IB-41 补注）"/>
    <input path="docs/user_stories.md" version="1.8.0" revision="REV-16-4" status="APPROVED（2026-10-07 追溯链分域订正）"/>
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

---

## 18. R11 增量实现（IB-20 流式交付 / 会话生命周期：IFC-IB-298~308 + G2 交接 + FND-R11-01 + BLK-R8-02；追加，不改写 §1~§17）

> 依据：`docs/module_design.md` **1.4.0/R8** §2.1（数据结构行）/ §2.2.3（IFC-IB-298~308 索引）/ §3（MOD-IB-01 / 02 / 16 / 21 / 22 / 23 / 24 的 R8 增补）；`docs/architecture_design.md` **1.4.0/R8** **ADR-17**（可选手动确认中间态，4 条约束）；`docs/user_stories.md` 1.3.0/R7（US-IB-19 / US-IB-20，AC-IB-19-01~05 / AC-IB-20-01~06）；`docs/test_report.md` R11（184 基线 + 2 项未覆盖 / 4 项部分覆盖 AC 的归属缺口 + **FND-R11-01**）；`docs/rev11_group_b_apply_package*.md`（设计落盘包）。
> **性质**：**只追加、不改写**。未新增模块（仍 26）、未改端口数（仍 14）、未改任何既有 IFC-IB 号或签名文本、未改模块边界、未改依赖边（DAG 不变）、未改既有配置键名与默认值、未引入任何第三方依赖。§1~§17 为 R1~R10 历史记录，**逐字未改**。
>
> **命名口径**：设计侧记为 **R8**（`module_design.md` 1.4.0/R8、ADR-17、IFC-IB-298~308），协调者轮次口径记为 **REV-12**，本文件自身版本线记为 **R11/2.6.0**（因 v2.4.0 已占用「R8」标签）。三套口径指向**同一批**改动。

### 18.1 实现顺序（拓扑排序；被依赖模块先实现）

DAG 未变，本轮触及的模块按拓扑序执行（MOD-IB-01 → 02 → 16 → 21 → 22 → 23 → 24）：

```
MOD-IB-01（core：类型 / 枚举 / 常量，纯 stdlib·framework-free）
   ↓
MOD-IB-02（config：键名登记 + 值域 + validate 第 3 子项）
   ↓
MOD-IB-16（experts：is_delegating / delegating_experts 消费侧话术对齐）
   ↓
MOD-IB-21（streaming：终态单发 + 可见性白名单 + 确认事件 + MemorySessionStore 逐字段复制）
   ↓
MOD-IB-22（orchestration：确认门装配 + resume fail-closed + G2 单跳交接计划展开）
   ↓
MOD-IB-23（ibweb：chat_stream 显式 4xx + POST /api/chat/resume 准入顺序）
   ↓
MOD-IB-24（frontend：确认区独立呈递 + 决策回传 + 会话标识纪律）
```

> 每层只 import 其前置（`ib/core` **零 Django import**，自检 `core_framework_free` 持续守护）。**无环**：本轮**零新增依赖边**。

### 18.2 模块实现计划（按拓扑顺序）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-01 | core（类型 / 枚举） | `src/ib/core/types.py`、`src/ib/core/enums.py`、`src/ib/core/__init__.py` | — | H | DONE |
| 2 | MOD-IB-02 | config（键名 / 校验 / 定义文档） | `src/ib/config/__init__.py`、`src/ib/config/definition.py` | MOD-IB-01 | M | DONE |
| 3 | MOD-IB-16 | experts（注册表纯数据） | `src/ib/experts/__init__.py` | MOD-IB-01 | L | DONE |
| 4 | MOD-IB-21 | streaming（事件 / 会话存储） | `src/ib/streaming/__init__.py` | MOD-IB-01 | M | DONE |
| 5 | MOD-IB-22 | orchestration（图 / 门 / 恢复） | `src/ib/orchestration/__init__.py` | 01 / 16 / 21 | H | DONE |
| 6 | MOD-IB-23 | ibweb（视图 / 路由） | `src/ibweb/views.py`、`src/ibweb/urls.py` | 01 / 22 | M | DONE |
| 7 | MOD-IB-24 | frontend（视图 / 客户端） | `src/frontend/src/api/client.ts`、`src/frontend/src/views/ChatPage.vue` | 23 | M | DONE |

### 18.3 逐任务落点与设计依据

| 任务 | 落点（IFC / 文件） | 实现要点 |
|------|------------------|---------|
| **REV-12-1**（IFC-IB-298~308） | `ib/core/types.py`（298 / 299 / 300 / 301 / 305）、`ib/core/enums.py`（301 的 `StreamEventKind` 追加）、`ib/streaming/__init__.py`（302 / 303 / 301 呈递）、`ib/config/__init__.py`（304）、`ib/orchestration/__init__.py`（305 / 306 / 301 装配 / 307 语义）、`ibweb/views.py` + `ibweb/urls.py`（307）、`frontend/src/api/client.ts` + `views/ChatPage.vue`（308） | ①`SessionState` / `SessionTurn` 补齐 `IFC-IB-221/222` 的**悬置引用**（**签名文本一字未改**）；②`SessionPersistencePolicy`（`in_process`/`external`）与 `SessionStateLossOutcome`（**唯一取值** `fail_closed_restart_required`）；③`CompletionPayload` / `CitationItem`（`citations` 可空元组、`had_content`、**只含定位信息不含字节**）；④`ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState` + `StreamEventKind` **追加** `confirmation_required`（既有 6 成员**逐位未动**）；⑤`completion_event(payload)` 终态**恰一次**、其后无 content、不臆造引用、不发空帧；⑥`is_user_visible(kind)` **白名单 + 默认不可见**（reasoning 受 `IB_REASONING_STREAM_ENABLED` 门控；内部子任务产物永不映射为可见类别）；⑦键名登记（**只登记名不写值**）：`IB_CONFIRMATION_GATE_ENABLED`（默认 `false`）/ `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`，`IB_SESSION_BACKEND` **值域扩展**为 `{memory, external}`（键名 / 默认值不变）；⑧`ResumePayload`（**类型化** `IFC-IB-233` 的 `payload: dict`，**不改其签名文本**）；⑨`can_resume(state, gate_id, payload)` **纯函数·三判据·fail-closed**（状态丢失 / 无待确认中间态·归属不符 / 未携决策，任一不满足即 `False`）；⑩`POST /api/chat/resume` **准入顺序强制**：鉴权（**仅 Authorization 头**）→ 归属断言（session_key 前缀）→ `SessionStore.load` → `can_resume` → 续跑；任一前置失败 = fail-closed（`403`/`404`/`409`/`503`），**不新建会话、不重跑**；⑪前端确认区**独立呈现**（不与答案片段合并、未决前不显示「已完成」、**无自动续跑**），决策经**独立端点**回传 |
| **REV-12-2**（G2 专家交接） | `ib/experts/__init__.py`（`delegating_experts()` 文档 + 三处兜底话术按**实际能力**改写）、`ib/orchestration/__init__.py::_expand_plan` | `is_delegating` / `delegating_experts()` **不再是死字段**。交接与既有图结构一致（`route → 条件边扇出 → expert×N / general → gate → aggregate`）：**单跳**把命中且可交接的专家的**默认同侪**补入计划。**三护栏口径（R11 补丁轮按 MAJOR-2 精确改写，见 §18.8）**：护栏①（往返上限）**已实现** —— 对齐 `min(config.max_expert_steps, MAX_EXPERT_STEPS=8)`（纵深防线：`_fan_out` 另有 `step_count > max_expert_steps → general`）；护栏③（非 handoff 出路）**已实现** —— 保留**非交接的常规作答路径**（默认关闭时计划与既有行为**逐位零差异**，且 `general` 域作答路径仍在，交接**不是唯一出口**）；护栏②（敏感写操作强制人工确认）**= 机制就绪 + 必批无自动批准**，**触发规则按设计由接入方提供（骨架不判定「哪些动作需要确认」）**，当前**组合根未接线 → 不可经配置触发**（登记为 **OPEN：GAP-R11-07**） |
| **REV-12-3**（FND-R11-01） | `src/ibweb/views.py::chat_stream_endpoint`（+ 前端同源约束 `client.ts` / `ChatPage.vue`） | 原实现为 `request.GET.get("session_id") or "default"`（静默回退字面量默认会话，导致多标签页共用会话且无法区分「未填」与「显式用 default」）。现改为：取回并 `strip` 后**为空即显式 4xx**（`ValidationError` → `400`），**不得回退**（对齐 AC-IB-20-01）。前端 `chatStream/chatResume` 对空标识**提前拒绝**并给可读回执；会话标识输入框**不再预填** `'default'`（原 `ref('default')` 会使服务端纪律被前端兜底抹平） |
| **REV-12-4**（BLK-R8-02） | `src/ib/config/definition.py::validate`（第 12 项，位于既有 11 项之后**追加**） | 新增第 3 子项：**同专家内**关键词的**空**（`expert_keyword_empty`）与**重复**（`expert_keyword_duplicate`），**先归一化**（`strip().lower()`，口径与既有跨专家撞车校验及路由消费方 `ib/routing/intent.py::_keyword_hits` 一致）**再比较**；产出可定位 `ValidationErrorItem`（含专家名与原关键词），由既有 `admit` 聚合闸门在装配期 fail-fast。既有 `ib.experts.validate_specs` 的派生 / 安装期兜底**保留、未削弱**（自检第 5 例以行为断言守护） |

### 18.4 R11 变更文件清单（`git diff --stat` 口径：13 文件，+1596 / −59）

| 文件 | 变更性质 | 对应 IFC / 项 |
|------|---------|-------------|
| `src/ib/core/enums.py` | `StreamEventKind` **追加** `CONFIRMATION_REQUIRED = "confirmation_required"`（既有 6 成员逐位未动） | IFC-IB-301 |
| `src/ib/core/types.py` | 新增 `CitationItem` / `CompletionPayload` / `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState` / `SessionTurn` + 两个类型别名与两个常量；`SessionState` **追加** R8 字段（既有 3 字段逐字保留，新增字段全有默认值）；`GraphConfig` 新增 `max_expert_steps` / `confirmation_gate_enabled` / `expert_handoff_enabled` / `max_history_messages` / `aggregation_forbids_internal_labels` | IFC-IB-298~301、305 |
| `src/ib/core/__init__.py` | 导出上述新增类型 / 常量（纯追加） | IFC-IB-298~301、305 |
| `src/ib/config/__init__.py` | `IB_RUNTIME_ENV_KEYS` 追加 3 个 R8 键名；`SessionConfig.persistence_policy`、`GlobalConfig.confirmation_gate_enabled` / `reasoning_stream_enabled`（**键名登记，值取安全默认**）；`validate_required` 的值域表新增两项（`IB_SESSION_BACKEND` 值域扩展 / `IB_SESSION_PERSISTENCE_POLICY`） | IFC-IB-304 |
| `src/ib/config/definition.py` | `validate()` **追加**第 12 项（同专家内空 / 重复关键词，归一化后比较）；docstring 同步 | BLK-R8-02 |
| `src/ib/experts/__init__.py` | 三处兜底话术按**实际能力**改写（据实作答 / 可转交同侪 / 转交受步数上限约束）；`delegating_experts()` 文档标注 REV-12-2 落地 | REV-12-2（IFC-IB-171/177 消费侧） |
| `src/ib/streaming/__init__.py` | `USER_VISIBLE_KINDS` 白名单 + `is_user_visible` / `completion_payload_json` / `completion_event` / `confirmation_required_event`；`MemorySessionStore.load` **逐字段**复制 R8 字段（否则 `gate` 被静默丢弃） | IFC-IB-301~303 |
| `src/ib/orchestration/__init__.py` | `ResumePayload` / `can_resume`（纯函数）/ `_run_inner(gate=)` / `_maybe_gate` / `_persist_gate` / `_pending_query_of` / `_gate_suspend_events` / `_gate_error_events` / `_expand_plan`（G2）/ `resume()` 同步与异步同源；`build_graph` 新增**可选关键字** `confirmation_prompt_builder` | IFC-IB-301 / 305 / 306 / 302 / REV-12-2 |
| `src/ibweb/views.py` | `chat_stream_endpoint` 缺会话标识 → 显式 `400`（FND-R11-01）；新增 `chat_resume_endpoint`（IFC-IB-307，准入顺序 + `403`/`404`/`409`/`503` fail-closed） | FND-R11-01、IFC-IB-307 |
| `src/ibweb/urls.py` | 新增 `path("api/chat/resume", ...)`（纯追加，位于 `api/chat/stream` 之后） | IFC-IB-307 |
| `src/frontend/src/api/client.ts` | `StreamEventKind` 联合类型追加 `'confirmation_required'`；新增 `ConfirmationPrompt` / `ConfirmationDecision` 类型与 `chatResume()`（**仅 Authorization 头**）；`chatStream` 空会话标识**提前拒绝**（FND-R11-01 前端同源） | IFC-IB-308 |
| `src/frontend/src/views/ChatPage.vue` | 确认区**独立区域**（`role="alertdialog"`，视觉可辨、不并入正文）+ `decide()` 显式点击回传（**无自动续跑**）+ 「本轮已完成」仅在本轮真正收束时显示；会话标识不再预填 `'default'` | IFC-IB-308、FND-R11-01 |
| `src/scripts/selfcheck.py` | 新增 **8 个离线自检用例**（见 §18.6）+ 既有 `http_contract_offline` 用例追加「缺 session_id → 400」断言 | 本轮自验 |

**未改**：任何既有 IFC-IB 号与签名文本；`src/tests/`（GROUP_D 资产）；模块 / 端口 / 依赖边计数；既有配置键名与默认值；`requirements*.txt`（**零新增第三方依赖**）；`docs/phase_status.md`（PM 专属）。

### 18.5 架构偏差记录与**设计缺口登记**（R11）

| 编号 | 类别 | 描述 | 处置 |
|------|------|------|------|
| — | 架构偏差 | **无**（未偏离任何 ADR；ADR-17 四条约束逐条满足：默认关闭 / 无业务语义 / SSE + 独立端点 / 状态丢失 fail-closed） | — |
| **GAP-R11-01** | **设计缺口（须 PM 裁决）** | `module_design.md` R8 列出的 `SessionState` 字段集与**既有实现**（被 `orchestration` / `streaming` / GROUP_D 既有用例依赖）不一致：设计为「新字段集」，实现需同时被旧消费方读取 | 按**最小一致**原则 **扩展**（既有 3 字段逐字保留 + R8 字段全默认值），**未改任何调用方**。**未擅改设计文档** |
| **GAP-R11-02** | 设计缺口 | **挂起时的终态表示**未规定：`confirmation_required` 之后是否需要/如何收束流（不发 `done` 会让前端永远转圈） | 实现为「**恰一条** `confirmation_required` + `completion_event(None)`」，且**不发 content** |
| **GAP-R11-03** | 设计缺口 | **确认话术构造器接缝**未在 IFC 中命名：骨架**不得生成业务话术**（ADR-09），但未定义「话术由谁提供、以何签名注入」 | 实现为 `build_graph` 的**可选关键字** `confirmation_prompt_builder`（沿用 `related_images_provider` 的「兼容超集」先例）；**未启用即零行为差异** |
| **GAP-R11-04** | 设计缺口 | **G2 交接的业务触发条件未定义**（哪一轮需要交接、交接目标集合、上限落点） | 实现为**确定性**最小选择：开关控制 + 目标取 `default_expert()`（默认同侪）+ 上限取 `min(config.max_expert_steps, MAX_EXPERT_STEPS)`；**骨架不判定业务规则**（骨架其余部分亦不引入业务语义） |
| **GAP-R11-05** | 设计缺口 | **resume 续跑所需的「原提问」承载**未规定（`ResumePayload` 只有 `session_key` + `decision`） | 实现为挂起时把原提问写入 `SessionState.turns` 末条 user 轮，续跑经 `_pending_query_of` 取回；缺失即 fail-closed（**不臆造**） |
| **GAP-R11-06** | 口径提示 | `IFC-IB-307` 的 `403` / `404` / `409` / `503` 语义粒度（哪一前置对应哪一码）在设计中只给出「fail-closed，不新建会话」 | 按「鉴权 401/403 → 归属 403 → 门未启用/未携决策/不一致 409 → 会话不存在 404 → 存储不可用 503」实现，**均为 fail-closed 方向**，不放松任何判据 |

> 上述缺口**均未擅自扩充架构**：全部按**最小一致 + 保守（fail-closed）**方向实现，并在此登记待 PM 裁决；设计侧文档**一字未改**。

### 18.6 R11 自验证据（离线；命令可被第三方重跑）

| # | 命令 | 结果 | 证据文件 |
|---|------|------|---------|
| 1 | `python -m py_compile`（11 个改动文件）+ `python -m pytest tests -q` | `py_compile OK`；**184 passed**（= R11 基线，无回归） | `docs/evidence/groupc_r11_compile.log` |
| 2 | `python scripts/selfcheck.py`（离线自检） | **39/39 PASS，EXIT=0**（R1~R10 的 31 例 + 本轮新增 **8 例**） | `docs/evidence/groupc_r11_selfcheck.log` |
| 3 | `node --test`（cwd = `src/frontend`） | **tests 6 / pass 6 / fail 0，EXIT=0** | `docs/evidence/groupc_r11_frontend.log` |
| 4 | `vue-tsc --noEmit` + `vite build` | 各 **EXIT=0**（28 modules；`dist/assets/index-*.js` 254.44 kB / gzip 89.93 kB） | `docs/evidence/groupc_r11_frontend_build.log` |

新增 8 个自检用例（**全部离线：InMemory / Fake 替身 + 纯函数，零外部依赖**）：

| # | 用例 | 覆盖 |
|---|------|------|
| 1 | `r8_contracts` | `StreamEventKind` 追加而不改既有 6 成员；`SessionState` 构造兼容；持久化策略 / 状态丢失结局取值域；终态单发（`None` → `data=""`，空引用 → `[]`，无 base64）；可见性白名单（`reasoning` 默认不可见、未登记类别不可见） |
| 2 | `r8_can_resume` | 三判据 + 加固判据的**正反两向**；残缺载荷**不被补成默认批准**；显式拒绝不被反转 |
| 3 | `r8_gate_resume` | 门默认关闭**零行为差异** + 关闭时 `resume` 显式失败；开关开但无话术构造器仍不触发；挂起恰一条 `confirmation_required` 且**不发 content**；状态丢失 fail-closed；批准续跑且**不再次触发门**；拒绝**不执行** |
| 4 | `r8_config_keys` | 三键名登记；安全默认值；`IB_SESSION_BACKEND` 值域扩展后合法值通过、非法值**逐键**报错（只报键名） |
| 5 | `r8_within_expert_keywords` | 同专家内精确 / 归一化后重复 → `expert_keyword_duplicate`（不误报跨专家 `expert_keyword_collision`）；空 → `expert_keyword_empty`；合法基线不被误杀；`validate_specs` 兜底**未被削弱** |
| 6 | `r8_expert_handoff` | `is_delegating` 已激活；关闭时计划逐位一致；开启时单跳补入默认同侪且**原专家仍在首位**；上限生效；不自交接 |
| 7 | `r8_chat_resume_http` | 端点 `401` / `?token=` `400` / 非法 JSON `400` / 缺会话标识 `400` / 归属不符 `403` / 门未启用 `409` |
| 8 | `r8_frontend_confirmation` | 前端静态纪律：事件类别登记、独立端点、**令牌不进查询串**、**不预填 / 不回退默认会话**、确认区 `role=alertdialog`、**确认分支不写入正文**、**无自动续跑定时器** |

### 18.7 冻结约束复核（R11）

- **契约纪律**：`IFC-IB-221~225` / `231~233` / `247` 的**签名文本一字未改**（`IFC-IB-233` 仅新增其载荷类型 `ResumePayload`；`IFC-IB-221/222` 仅补齐其悬置引用的 `SessionState` 定义）；新增编号仅 `298~308`（11 条，设计已分配）；端口 14 / 模块 26 / 依赖边**零新增**（DAG 不变）。
- **离线纪律**：全部自检与回归**零外部网络**（InMemory / Fake / 纯函数；Django 测试客户端走**进程内**）；**未触达**真实 Qdrant / DeepSeek / bge-m3 / 任何外部端点；**未引入 Docker**；**未引入运行期 CDN**。
- **框架无关内核**：`src/ib/core` **零 Django import**（自检 `core_framework_free` 守护）；新增类型全部 frozen dataclass / `slots` / 纯 stdlib；**零新增第三方依赖**（`requirements*.txt` 未改）。
- **凭据纪律**：键名**只登记不写值**；改动文件与证据日志**不含任何真实凭据**；`?token=` / `?key=` 在**新端点同样被拒**（自检第 7 例直接断言）。
- **未削弱既有断言**：GROUP_D 基线 **184 passed** 原样通过；`validate_specs` 兜底、`validate()` 既有 11 项校验的语义与顺序**均未改动**（本轮仅在**其后追加**第 12 项）；**未使用 skip / xfail 掩盖任何失败**。
- **FreeArk 仓库全程只读**；`docs/phase_status.md` **未触碰**（PM 专属）；**未执行 `git add` / `git commit`**（提交属 PM 授权范围）。
- **受保护行复核（R11）**：本文件四处「24/24 PASS」保护行**逐字未改**。因本轮仅**在 `revision_note` 同一物理行（L37）末尾追写**、并在文件末尾**追加 §18**，头部**未新增任何行** → 四行当前行号仍为 **L483 / L615 / L633 / L744**（与 R10 记录**完全一致**）。取证：`grep -n "24/24 PASS" docs/implementation_plan.md`。

### 18.8 R11 补丁轮（REV-12 patch；invocation INV-GROUP_C-INTELBASE-011）

> 触发：独立只读核验 **INV-GROUP_C-VERIFY-R11** = **CONFIRMED_WITH_CAVEATS**（1 项**必须修 MAJOR** + 3 项 MINOR/口径）。本轮**只做 4 项有界修复**，不扩范围。

#### 18.8.1 修复落点

| 项 | 级别 | 落点（文件:行） | 要点 |
|----|------|----------------|------|
| **MAJOR-1** | MAJOR → **FIXED** | `src/ibweb/views.py`（`chat_resume_endpoint` 会话键派生段） | 缺 `session_key` 时改走**唯一入口** `ib.context.session_key(project_id, ctx.authz.actor_id, session_id)`，与流路径 `ctx.session_key` **逐字一致**；视图内**不再**自造 2 段键、**不再**出现独立分隔符拼接；`session_key` 直传分支保留。修复前自造 2 段键 → 真实 HTTP 续跑**恒 404** |
| **MINOR-2** | MINOR → **FIXED** | `src/ib/orchestration/__init__.py`（新增私有 `_requested_gate_id` + `resume`/`aresume` 调用点）、`src/ibweb/views.py`（`chat_resume_endpoint` 调用点） | `gate_id` 改取**请求指向的中间态**（`payload.decision.gate_id`，或请求体显式 `gate_id`），与 `state.gate.gate_id` **真实对账**，不一致即 fail-closed（→409）。**`IFC-IB-306` 签名文本 `can_resume(state, gate_id, payload)` 一字未改**（仅改调用点传值来源） |
| **MINOR-1** | MINOR → **FIXED** | `src/ib/orchestration/__init__.py::_expand_plan` | `expert_handoff_enabled=False` 时**直接**按 `decision.experts` 原序、原样展开（**不去重 / 不过滤**，与 G2 前**逐位零差异**）；开启分支**保留**去重 + 上限 |
| **MAJOR-2** | 文档/口径 | `docs/code_review_report.md` §15.2 / §15.6（新增 **GAP-R11-07** OPEN 行）/ §15.9 / §15.10 与本文件 §18.3 / §18.8 | 「三条护栏齐备」**精确改写**为：护栏①③**已实现**；护栏② = **机制就绪 + 必批无自动批准**，**触发规则按设计由接入方提供（骨架不判定）**，**组合根未接线 → 不可经配置触发**（**OPEN：GAP-R11-07**）。**未新增**「敏感动作清单」或任何默认策略代码 |

#### 18.8.2 补丁轮自验证据（离线；命令可被第三方重跑）

| # | 命令 | 结果 | EXIT | 证据文件 |
|---|------|------|------|---------|
| 1 | `python -m py_compile`（3 改动文件） | `py_compile OK` | **0** | `docs/evidence/groupc_r11_patch_compile.log` |
| 2 | `python -m pytest tests -q` | **184 passed**（= R11 基线，无回归） | **0** | `docs/evidence/groupc_r11_patch_pytest.log` |
| 3 | `python scripts/selfcheck.py`（离线） | **40/40 PASS**（新增 1 例 `r8_chat_resume_http_success`） | **0** | `docs/evidence/groupc_r11_patch_selfcheck.log` |
| 4 | `node --test`（cwd = `src/frontend`） | **tests 6 / pass 6 / fail 0** | **0** | `docs/evidence/groupc_r11_patch_frontend.log` |
| 5 | 负向对照（临时还原 2 段键） | `r8_chat_resume_http_success` **FAIL(404)**；`r8_chat_resume_http` **PASS** | **1** | `docs/evidence/groupc_r11_patch_negative_control.log` |
| 6 | MAJOR-1 成功续跑探针 | 键 byte-identical；`200` + `StreamingHttpResponse` + `text/event-stream`；事件 `reasoning, content, done` | **0** | `docs/evidence/groupc_r11_patch_major1_probe.log` |

> 新增用例 `r8_chat_resume_http_success`（MAJOR-1 正向）：以**流路径真实键**（`make_request_context("p_alpha","service-account","resume-ok").session_key`）预置带 `gate` 的 `SessionState` → `POST /api/chat/resume`（体 `{"session_id":"resume-ok","decision":{"gate_id":"gate-http-1","approved":true}}`）→ 断言 `200` / `StreamingHttpResponse` / `text/event-stream` / 流含 `event: done` 且**不含** `event: confirmation_required`；另断言 `gate_id` 不符 → `409`。全程**进程内** Django 测试客户端，**零外部网络**。

#### 18.8.3 补丁轮守约复核

- **契约纪律**：`IFC-IB-221~225` / `231~233` / `247` / `306` 签名文本**一字未改**；只新增 `298~308`；端口 14 / 模块 26 / 依赖边**零新增**。
- **未削弱既有断言**：GROUP_D 基线 **184 passed** 原样通过；selfcheck 既有 **39 例全部保留**（含 401/400/403/409 反向断言）；**未使用 skip / xfail**。
- **只读约束**：未改 `tests/**`（GROUP_D）、`docs/phase_status.md`（PM）、设计真源四文档；未执行 `git add` / `git commit`。
- **受保护行复核（补丁轮）**：本轮对 L37 `revision_note`、L997 §18.3 REV-12-2 行均为**同一物理行原地改写**（行数不变），并在文件末尾**追加 §18.8** → §18.7 四处「24/24 PASS」保护行当前行号**仍为 L483 / L615 / L633 / L744**（未位移）。取证：`grep -n "24/24 PASS" docs/implementation_plan.md`。

## 19. R13 增量实现（账户 / 会话 / 商用界面重构：IFC-IB-309~332 + REQ-FUNC-IB-28~36；追加，不改写 §1~§18）

> **依据**：`docs/module_design.md` **1.5.0/REV-13** §2.1（数据结构行）/ §2.2（端口行：第 15 个 `AccountStore`）/ §2.2.4（IFC-IB-309~332 段号索引）/ §3（MOD-IB-01 / 02 / 11 / 23 / 24 / 25 的 R13 增补）；`docs/architecture_design.md` **1.5.0/REV-13** **ADR-18~ADR-27**（账户体系归属 / 令牌摘要 / 零 Cookie / 策略单一真源 / 前端组件库 / TLS 终止 / 限速条件性）；`docs/tech_stack.md` **1.4.0/REV-13**（§1 三新行：Element Plus / vue-router / bcrypt；§1.4 客户端键登记；§4.5 第 13~18 项）；`docs/requirements_spec.md` **1.4.0/REV-13**（REQ-FUNC-IB-28~36、REQ-NFR-IB-15~18、C-IB-09、DR-09~DR-17）；`docs/user_stories.md` 1.4.0（US-IB-21~29）；上游门控 **GR-B-006 = PASS_WITH_CONDITIONS**。
> **性质**：**只追加、不改写**。**未新增模块**（仍 **MOD-IB-01~26**，26 个）、**端口 14 → 15**（`AccountStore`，纯追加）、**依赖边零新增**（DAG 不变）、**既有 `IFC-IB-001~308` 的号 / 名 / 签名 / 字段集一字未改**。§1~§18 为 R1~R11 的历史记录，**逐字未改**。
> **命名口径**：设计侧记为 **REV-13**（`module_design.md` 1.5.0/REV-13、`IFC-IB-309~332`），本文件自身版本线记为 **R13 / v2.7.0**（v2.6.0 已占用「R11」标签）。两套口径指向**同一批**改动。

### 19.1 实现顺序（拓扑排序；被依赖模块先实现）

DAG 未变（R13 **零新增依赖边**），本轮触及的模块按既有编号序执行（编号即拓扑序）：

```
MOD-IB-01（core：账户 / 会话 / 令牌类型 + 第 15 个端口 AccountStore，纯 stdlib·framework-free）
   ↓
MOD-IB-02（config：IFC-IB-312 键名登记，**只登记键名不含值**）
   ↓
MOD-IB-11（ledger：users / sessions 表 + bcrypt + SqliteAccountStore + MemoryAccountStore 替身 + 幂等种子）
   ↓
MOD-IB-23（ibweb：8 个端点 + SessionTokenResolver + 可注入策略模块 + AuthMiddleware 扩展 + 组合根装配）
   ↓
MOD-IB-24（frontend：登录页 / 首登改密 / 控制台外壳 / hash 路由守卫 / 类型化 API 客户端扩展）
   ↓
MOD-IB-25（deploy：手写迁移 003 + nginx TLS 模板 + 检查清单 B15~B20）
```

> 每层只 import 其前置（`ib/core` **零 Django import**，自检 `core_framework_free` 持续守护；MOD-IB-11 的 `bcrypt` 为**惰性导入**，见 `ib/ledger/__init__.py::__getattr__`，故未启用账户体系时零代价）。**无环**：本轮**零新增依赖边**（再声明见 `module_design.md` §4.2.4）。

### 19.2 模块实现计划（按拓扑顺序）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-01 | core（账户 / 会话 / 令牌契约 + 第 15 个端口） | `src/ib/core/accounts.py`（新）、`src/ib/core/ports.py`、`src/ib/core/types.py`、`src/ib/core/__init__.py` | — | H | DONE |
| 2 | MOD-IB-02 | config（键名登记） | `src/ib/config/__init__.py` | MOD-IB-01 | L | DONE |
| 3 | MOD-IB-11 | ledger（SQL 适配器 / bcrypt / 种子 / 离线替身） | `src/ib/ledger/accounts.py`（新）、`src/ib/ledger/schema.py`、`src/ib/ledger/__init__.py` | MOD-IB-01 | H | DONE |
| 4 | MOD-IB-23 | ibweb（端点 / 解析器 / 策略 / 中间件 / 装配） | `src/ibweb/accounts/__init__.py`（新）、`src/ibweb/accounts/policy.py`（新）、`src/ibweb/accounts/throttle.py`（新）、`src/ibweb/authz.py`、`src/ibweb/views.py`、`src/ibweb/urls.py`、`src/ibweb/composition.py` | 01 / 11 | H | DONE |
| 5 | MOD-IB-24 | frontend（登录 / 控制台 / 路由 / 客户端） | `src/frontend/src/{app/env.ts,router/index.ts,layouts/ConsoleLayout.vue,stores/session.ts,stores/theme.ts,styles/theme.css,views/LoginPage.vue,views/ChangePasswordPage.vue,views/AccountsPage.vue}`（新）、`api/client.ts`、`main.ts`、`App.vue`、`env.d.ts`、`vite.config.ts`、`package.json`、`package-lock.json` | 23 | H | DONE |
| 6 | MOD-IB-25 | deploy（迁移 / TLS 模板 / 检查清单 / 键模板） | `src/deploy/migrations/003_accounts.sql`（新）、`src/deploy/nginx/intelligentbase.conf.example`（新）、`src/deploy/env.example`、`src/deploy/checklists.txt`、`src/requirements.txt`、`src/requirements-offline.txt` | 24 | M | DONE |

> **非模块交付物**：`src/scripts/selfcheck.py`（新增 5 例 R13 自检，见 §19.6）。自检脚本不是 runtime 模块，登记于此以避免与 MOD 表混淆（沿用 R2/R10 先例）。

### 19.3 逐任务落点与设计依据（映射 REQ-FUNC-IB-28 ~ IB-36）

| REQ / 任务 | 落点（IFC / 文件） | 实现要点 |
|-----------|------------------|---------|
| **REQ-FUNC-IB-28 / IB-33**（用户名密码登录，替代并移除粘贴令牌入口，无旁路；与既有 AuthzPolicy 端口协作） | `ibweb/views.py::auth_login_endpoint`（IFC-IB-316）、`ibweb/accounts/__init__.py::SessionTokenResolver`（IFC-IB-322）、`ibweb/accounts/policy.py`（IFC-IB-323）、`ibweb/authz.py`、`frontend/src/views/LoginPage.vue`（IFC-IB-327） | 登录**唯一**入口：`get_user_by_username` → `verify_password`（bcrypt） → 状态 / 锁定校验 → `issue_session(user_id, token_digest(token), expires_at=…)`；**响应体与日志零口令 / 零令牌原文**。前端**彻底删除**粘贴令牌入口（`App.vue` 改为纯 `<router-view/>`；`main.ts` 删除 `?token=` URL 迁移；`client.ts` 不再从查询串取令牌）——**删除而非隐藏**。既有注入式 `AuthzPolicy`（IFC-IB-032/033）**仍是唯一授权真源**：账户模块只提供 `PrincipalResolver`（把请求解成 `AuthzContext(actor_id, project_id, roles)`），**不做**第二套鉴权判断 |
| **REQ-FUNC-IB-29**（不透明会话令牌 / 仅 Authorization 头 / 过期与续期 / 无 Cookie） | `ib/core/accounts.py::new_session_token / token_digest / token_digest_matches`（IFC-IB-311）、`ib/ledger/accounts.py`（sessions 表：只存 `token_digest`）、`ibweb/views.py::auth_session_renew_endpoint`（IFC-IB-320）、`ibweb/authz.py`（`?token=` 4xx） | 令牌 = `secrets.token_urlsafe(32)`（256-bit）；**库里只存 SHA-256 摘要**（读到库 ≠ 拿到可用令牌）；比较用 `hmac.compare_digest`（常量时间）。**零 Cookie**：全端点**不发** `Set-Cookie`（自检 `r13_account_http_contract` 断言全响应零 `Set-Cookie`）。续期**只补窗口不延长绝对寿命**：仅当剩余有效期 < `IB_SESSION_RENEW_WINDOW_SECONDS` 时才延长 |
| **REQ-FUNC-IB-30**（默认管理员 + 首登强制改密；初始口令经 `IB_DEFAULT_ADMIN_PASSWORD` 注入，不落盘 / 不回显） | `ib/ledger/accounts.py::seed_default_admin`（IFC-IB-314）、`ibweb/composition.py::_seed_accounts`（IFC-IB-325）、`ibweb/authz.py::_CHANGE_PASSWORD_ALLOWLIST`、`frontend/src/views/ChangePasswordPage.vue` | 种子**幂等**（重放不覆盖既有口令）；`role=admin` / `project_id=None` / **`must_change_password=True`**。首登强制改密为**服务端受限会话**（结构性不可绕过）：改密态下中间件只放行 `GET /api/auth/me`、`POST /api/auth/change-password`、`POST /api/auth/logout`，**其余一律 `403 password_change_required`**（自检断言 `/api/accounts`、`/api/files` 均 403）。初始口令**只**从环境变量读（仓库内零字面量，见 §19.6 凭据扫描） |
| **REQ-FUNC-IB-31 / IB-32**（管理员管理运维账户；账户:项目 = 1:1；admin 全局 / ops 全功能 + 项目边界隔离） | `ibweb/views.py::accounts_endpoint / account_disable_endpoint / account_reset_password_endpoint`（IFC-IB-321）、`ibweb/accounts/__init__.py::effective_roles / GLOBAL_PROJECT`、`ib/ledger/accounts.py`（DDL `CHECK (role='admin' OR project_id IS NOT NULL)`）、`frontend/src/views/AccountsPage.vue` | **账户 CRUD 仅管理员**：`_require_admin` 要求 `is_global(authz)` **且** `policy.can_manage(ctx)`，否则 `ScopeViolationError`（403）。`ops` 账户**必须**带 `project_id`（存储层 CHECK + 视图层 400 双保险）；**越权取消**：`disable` 清 status + **撤销该账户全部会话**；`reset-password` 置 `must_change=True` + 撤销全部会话。ops 的**功能不削减**（等同 manager 全功能），隔离**只**由项目边界实现（`X-IB-Project` 声明他项目 → 403） |
| **REQ-FUNC-IB-34 / IB-35**（Claude 风格商用界面：左导航 + 右内容 / 暗亮主题 / 中文为主；组件库本地打包禁 CDN） | `frontend/src/layouts/ConsoleLayout.vue`、`styles/theme.css`、`stores/theme.ts`、`router/index.ts`（IFC-IB-328）、`package.json` / `package-lock.json`（IFC-IB-329）、`vite.config.ts` | **Element Plus ^2.8**（MIT）+ **vue-router ^4.4**（MIT，`createWebHashHistory`）经 **npm 本地打包**（`manualChunks` 拆分 vendor），**构建产物零外网引用**（自检 `r13_frontend_auth_discipline` 断言 index.html / main.ts / router 无 http(s) 外链）。自定义主题：`:root` 亮色令牌 + `:root[data-theme='dark']` 暗色令牌 + Element Plus 变量覆盖；字体栈含 `PingFang SC` / `Microsoft YaHei`，**无 `@font-face`**（不引外部字体）。界面文案**中文为主**。路由守卫：未登录 → `/login`；改密态 → 强制 `/change-password`；非管理员进 `requiresAdmin` 路由被拦截 |
| **REQ-FUNC-IB-36**（登录失败限速，`[INFERRED]`） | `ibweb/accounts/throttle.py::LoginThrottle / build_throttle / audit`（IFC-IB-326） | **条件性**（ADR-27 / OQ-IB-12 未裁决）：**未设置 `IB_LOGIN_MAX_FAILURES` 即不启用**（`build_throttle()` 返回 `None`）。启用后按 `client_ip` 滑动窗口计数（防「挑用户名爆破」）；账户维度计数由 `AccountStore.record_login_failure` 承载。审计经 `ib.observability.log_event`，**只记枚举 / 状态 / 项目 id**，**函数签名本身不接受** username / user_id / 口令 / 令牌 |
| **REQ-NFR-IB-15**（凭据存储与呈现纪律） | `ib/ledger/accounts.py::hash_password / verify_password`（IFC-IB-313）、`deploy/env.example`、`deploy/checklists.txt` [B19] | bcrypt（`$2b$` 前缀，每次 `gensalt` 随机盐）；仓库 / 日志 / 响应**零口令字面量**；初始口令**仅**经 0600 EnvironmentFile |
| **REQ-NFR-IB-16**（传输安全 HTTPS） | `deploy/nginx/intelligentbase.conf.example`（IFC-IB-331）、`deploy/checklists.txt` [B15] | TLS 终止在 nginx；`ib-web` 仍绑 `127.0.0.1:18080`（**明文只存在于回环**）；证书 / 私钥**不进仓库**（路径为 `<REPLACE_ME…>` 占位符）；HSTS **仅以注释给出**（自签证书下启用会封死降级排障路径） |
| **REQ-NFR-IB-17**（前端自包含 / 数据不出本机） | `frontend/package.json`、`vite.config.ts`、`styles/theme.css` | 依赖全部本地打包；**禁运行期 CDN**；**无 `@font-face` 外部字体**；`vite build` 产物自包含 |
| **REQ-NFR-IB-18**（审计留痕，`[INFERRED]`） | `ibweb/accounts/throttle.py::audit`、`ib/ledger/accounts.py`（会话表 `revoked_at` / `last_seen_at`） | 认证事件**只记枚举与计数**（白名单字段）；会话签发 / 撤销 / 续期在台账留痕 |
| **迁移与清单**（支撑全部上述） | `deploy/migrations/003_accounts.sql`（IFC-IB-330）、`deploy/checklists.txt` [B15]~[B20]（IFC-IB-332） | 003 为**纯追加**（只建 `users` / `sessions` 两表 + 3 索引，`CREATE … IF NOT EXISTS` 幂等，不动任何既有表 / 列）；回滚策略 = **代码回滚**（旧代码不引用新表即可启动）。新增 B15（HTTPS 生效）/ B16（零 `Set-Cookie`）/ B17（`?token=` 全端点 4xx，含 `/api/auth/*`）/ B18（首登强制改密，403 `password_change_required`）/ B19（EnvironmentFile 0600 + `IB_DEFAULT_ADMIN_PASSWORD` 唯一落点 + bcrypt `$2b$` 核对）/ B20（迁移前向 / 回滚） |

### 19.4 R13 变更文件清单（`git status` 口径）

**新增（21 个，全部为 R13 产出）**

| 类别 | 文件 |
|------|------|
| core 契约 | `src/ib/core/accounts.py`（63 行） |
| ledger 适配器 | `src/ib/ledger/accounts.py`（815 行：`hash_password` / `verify_password` / `SqliteAccountStore` / `MemoryAccountStore` / `seed_default_admin` / `build_account_store`） |
| ibweb 账户 | `src/ibweb/accounts/__init__.py`（201 行）、`src/ibweb/accounts/policy.py`（74 行）、`src/ibweb/accounts/throttle.py`（133 行） |
| 前端 | `src/frontend/src/app/env.ts`、`router/index.ts`、`layouts/ConsoleLayout.vue`、`stores/session.ts`、`stores/theme.ts`、`styles/theme.css`、`views/LoginPage.vue`、`views/ChangePasswordPage.vue`、`views/AccountsPage.vue`（合计 1,539 行） |
| 部署 | `src/deploy/migrations/003_accounts.sql`（60 行）、`src/deploy/nginx/intelligentbase.conf.example`（144 行） |

**修改（21 个 tracked 文件；`git diff --stat -- src` = +2,090 / −204）**

`src/ib/core/{__init__,ports,types}.py`（+247）、`src/ib/config/__init__.py`（IFC-IB-312 键名登记）、`src/ib/ledger/{__init__,schema}.py`（+127）、`src/ibweb/{authz,composition,urls,views}.py`（+553）、`src/scripts/selfcheck.py`（+565，5 例 R13 自检）、`src/deploy/{env.example,checklists.txt}`（+113）、`src/requirements{,-offline}.txt`（+13，`bcrypt>=4,<5`）、`src/frontend/{package.json,package-lock.json,vite.config.ts,src/main.ts,src/App.vue,src/api/client.ts,src/env.d.ts}`。

> **未触碰**（只读约束）：`tests/**`（GROUP_D 领地）、`docs/phase_status.md`（PM 领地）、设计真源四文档（`architecture_design.md` / `module_design.md` / `requirements_spec.md` / `user_stories.md` —— 已由 GROUP_B 更新，本轮**只读**）。**未执行** `git add` / `git commit`（留给协调者）。

### 19.5 架构偏差记录（R13）

| 偏差 ID | 偏差描述 | 原设计决策 | 偏差原因与合规性 |
|---------|---------|-----------|----------------|
| **D-R13-01** | 全局主体的 `AuthzContext.project_id` 用哨兵值 `"*"`（`GLOBAL_PROJECT`）承载，而非 `None` / `""` | ADR-21：admin 的 `project_id=None`（全局） | `AuthzContext.project_id` 的类型（`str`）受「**IFC-IB-001~308 一字不动**」保护，不能改为可空。以 `"*"` 哨兵使全局语义在**不动机场字段**的前提下显式可读（`"*"` 在项目 id 值域中不可能出现，无碰撞风险）。`[DEVIATION — 为守「既有契约一字不动」的硬约束，以哨兵值显式化全局语义]`。已登记于 `ibweb/accounts/__init__.py` 模块头与 `policy.py` 判据处 |
| **D-R13-02** | `SqliteAccountStore` 增加 `revoke_sessions_for_user(user_id, *, keep_digest=None)` 方法（`AccountStore` 端口 13 方法之外） | `module_design.md` §3 MOD-IB-01：端口 `AccountStore` **恰好 13 方法** | 改密后**必须**撤销该用户其它会话（否则旧令牌在改密后仍可用 = 安全缺陷），而标准 13 方法中的 `revoke_session(token_digest)` 需**逐个**摘要才能撤销，调用方无从枚举。故按 **`upsert_chunks` 先例（D-07）**在**同组存储实现**内扩展方法：**端口协议 `AccountStore` 一字未改（仍 13 方法）**，扩展只存在于 `ib/ledger/accounts.py` 的具体实现（`MemoryAccountStore` 同签名提供，保证替身一致）。`[DEVIATION — 端口契约不变，仅在实现侧扩展内部能力，避免「改密后旧会话仍有效」]` |
| **D-R13-03** | 前端新增 **Element Plus** 与 **vue-router** 两项 npm 依赖 | R1~R12 的 `src/frontend/package.json` 旧约定：「**刻意不加 UI 组件库**」 | 该旧约定由用户在 **REV-13 明确变更**（`requirements_spec.md` REQ-FUNC-IB-35 约束② + 决策登记 **DR-13**：Element Plus + 自定义 Claude 主题）。`package.json` 的 `_comment` 已就地改写，**留痕该决策反转**（引 DR-13），并非静默引入。**许可合规**：Element Plus（MIT）/ vue-router（MIT），`tech_stack.md` §1 / §2 已登记（§2.2 传递依赖暂标 `[待核实]`，属 GROUP_B 的许可核实动作，非本代理主张）。`[DEVIATION — 用户于 REV-13 明确变更旧约定；已按 DR-13 留痕]` |
| **D-R13-04** | 前端构建期配置键经 `import.meta.env.VITE_IB_AUTH_LOGIN_PATH` / `VITE_IB_AUTH_SESSION_STORAGE_KEY` 读取，代码内默认值与 `tech_stack.md` §1.4 登记的键名一一对应 | `tech_stack.md` §1.4（R13 新增）：只登记键名 `IB_AUTH_LOGIN_PATH` / `IB_AUTH_SESSION_STORAGE_KEY` | Vite 的客户端注入前缀固定为 `VITE_`，故登记名需以 `VITE_IB_AUTH_*` 形式引用；**键名与语义与 §1.4 一一对应，未新增任何未登记键**（默认值 `/api/auth/login` 与 `ib_token` 与 §1.4 语义一致）。`[DEVIATION — 前缀由 Vite 机制决定，键名语义与 §1.4 登记一致]` |
| **D-R13-05** | 主题偏好（暗 / 亮）**不持久化**（会话内有效，每次加载回到 `prefers-color-scheme`） | REQ-FUNC-IB-34：**必须**支持暗 / 亮主题切换（未规定是否跨会话记忆） | 若持久化需新增客户端存储键 → 而 `tech_stack.md` §1.4 只登记了两个键名，新增键属「悄悄扩大对外契约」；且 `scripts/selfcheck.py::frontend_config_discipline` 对前端源码有「**视图侧零持久化**（ADR-14）」的全仓断言，为 UI 偏好放宽该断言会把「哪些持久化允许」变成需逐案判断的问题。**切换功能完整可用**，仅不跨会话记忆 —— 对「系统偏好即用户偏好」的多数场景正是期望行为。**已登记为遗留 MINOR**（见 `code_review_report.md` §16），建议路径：先回设计登记键名，再持久化。`[DEVIATION — 为守 ADR-14 与「不新增未登记键」，主动缩小实现范围，并登记补救路径]` |

> 除上述 5 条外，**无其他架构偏差**。特别地：**未引入** Cookie 会话 / JWT / 独立鉴权服务 / Django ORM / `contrib.auth` / 运行期 CDN / Docker / Redis / PyMuPDF（ADR-18~27 逐条遵守）。

### 19.6 R13 自验证据（离线；命令可被第三方重跑）

| # | 命令（cwd） | 结果 | EXIT |
|---|------------|------|------|
| 1 | `python -X utf8 -m compileall -q .`（`src/`） | 无语法错误（`ib/config` 与全部 R13 新文件一并纳入） | **0** |
| 2 | `python -X utf8 scripts/selfcheck.py`（`src/`） | **45/45 通过**（R13 新增 **5 例**，见下） | **0** |
| 3 | `python -X utf8 -m pytest tests -q`（仓库根） | **207 passed**（**无回归**） | **0** |
| 4 | `npx vue-tsc --noEmit`（`src/frontend`） | 类型检查通过（`strict` / `noUnusedLocals`） | **0** |
| 5 | `npx vite build`（`src/frontend`） | 构建成功（`index` 44.97 kB / gzip 17.96；`vendor-vue` 110.22；`vendor-flow` 157.24；`vendor-element` 938.89 / gzip 301.82；`css` 382.72 / gzip 52.81） | **0** |
| 6 | `node --test`（`src/frontend`） | `tests 6 / pass 6 / fail 0`（含「锁 ↔ `package.json` 同步」回归闸） | **0** |
| 7 | 凭据扫描（见下） | **零命中**（真凭据形态 / 口令字面量 / 部署模板内摘要或证书材料） | **0** |

**R13 新增自检用例（5 例，全部离线；InMemory / 临时 SQLite + Django 进程内测试客户端，零外部网络）**

| 用例 | 覆盖 | 断言要点 |
|------|------|---------|
| `r13_token_primitives` | IFC-IB-311 / 313 | 令牌熵与唯一性；`token_digest` 确定性；`token_digest_matches` 常量时间比较；bcrypt `gensalt` 每次不同、`checkpw` 正确；**明文不出现在摘要中** |
| `r13_account_store_parity` | IFC-IB-310 / 313 / 315 | **断言 `AccountStore` 恰好 13 方法**；同一段行为体分别跑 `MemoryAccountStore` 与 `SqliteAccountStore` **要求语义一致**：幂等种子 / ops 1:1 项目绑定与其冲突 / list 过滤 / 会话签发·解析·过期·撤销·续期 / `revoke_sessions_for_user(keep_digest=)` / 失败计数与重置 / `set_status` / purge / `set_password` 清 `must_change`；**扫 main/-wal/-shm 三件套确认零明文且 `$2` 摘要存在** |
| `r13_account_http_contract` | IFC-IB-316~321 | 走**完整生产鉴权路径**（`IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy`，`build_deps(force=True)`）：无令牌 401；`?token=` / `?access_token=` 400（**含 `/api/auth/login`**）；**全响应零 `Set-Cookie`**；错口令 / 未知账户**同一 401 文案**（防枚举）；登录 200 形状；改密态 403 `password_change_required`（`/api/accounts` 与 `/api/files`）；弱口令 / 与旧同口令被拒；改密成功后旧会话**被撤销**；账户列表**无 `password_hash`**；create 201 / 重名 409 / 缺 `project_id` 400 / 非 ops 角色 400；项目过滤；ops 登录 → 既有改密 200 → `/api/files` 200 → `/api/accounts` **403 scope_violation**；续期 200；登出 204 后再用 401；reset-password 200；disable 200 后登录 401（同文案）；未知账户 disable / reset 404 |
| `r13_frontend_auth_discipline` | IFC-IB-327~329 | Element Plus / vue-router 已声明；**无 axios**；index.html / main.ts / router **无外部 http(s)**；`App.vue` **结构性无**令牌输入（无 `<input` / `setToken(` / `type="password"`）；main.ts **无** `location.search` / URL 令牌迁移；router 用 hash history + `beforeEach` + `bootstrap` + `mustChangePassword`；`client.ts` 含全部端点 + `Authorization`/`Bearer` + **无** `?token=`（**先剥离注释**再断言）+ 无 localStorage 存令牌；`theme.css` 含暗色令牌 + **无 `@font-face`** + CJK 字体栈 |
| `r13_deploy_discipline` | IFC-IB-330~332 | 003 幂等 DDL + 必需列 + `002` 存在；nginx 模板含 `ssl_certificate`/`_key`、`127.0.0.1:18080`、`proxy_buffering off;`、Authorization 透传、`<REPLACE_ME`、**零证书 / 私钥材料**、**无生效的 HSTS 行**；env.example 含全部 R13 键名、`IB_DEFAULT_ADMIN_PASSWORD=<REPLACE_ME`、`ibweb.accounts.policy`；checklists 含 [B15]~[B20] 与签署行「B1–B20」；**新增**：R13 键名在**唯一真源** `ib.config.IB_RUNTIME_ENV_KEYS`（IFC-IB-312）内有登记，且**未**混入 `IB_ENV_KEYS` |

**凭据扫描（#7 展开；命令可被第三方重跑）**

| 扫描项 | 命令要点 | 结果 |
|--------|---------|------|
| 真凭据形态 | `grep -rInE 'sk-[A-Za-z0-9]{16,}\|ghp_[A-Za-z0-9]{20,}\|-----BEGIN [A-Z ]*PRIVATE KEY\|eyJ[A-Za-z0-9_-]{20,}\.' src` | **0 命中** |
| 初始口令字面量 | `grep -rIn 'IB_DEFAULT_ADMIN_PASSWORD' src docs` | 仅**键名引用**（注释 / 校验命令 / `env.example:113` = `<REPLACE_ME_generated_random_password>`），**无任何值** |
| 部署模板内摘要 / 证书材料 | `grep -rInE '\$2[aby]\$[0-9]{2}\$\|BEGIN CERTIFICATE\|PRIVATE KEY' src/deploy` | 唯一命中 = `checklists.txt` 中**校验命令自身的模式串**（元引用，非凭据） |

### 19.7 冻结约束复核（R13）

- **契约纪律**：**既有 `IFC-IB-001~308` 的号 / 名 / 签名 / 字段集一字未改**（含 R11 受保护的 `221~225` / `231~233` / `247` / `306`）；只**新增** `IFC-IB-309~332`；端口 **14 → 15**（纯追加）；模块 **26 不变**；**依赖边零新增**。
- **未新增第三方运行时依赖（后端）**：唯一新增是 `bcrypt>=4,<5`（Apache-2.0，非 copyleft），经 `tech_stack.md` §1 / §2 登记；**未引入** Docker / Redis / PyMuPDF / Cookie 会话 / JWT / Django ORM / `contrib.auth`。**前端**新增 Element Plus（MIT）+ vue-router（MIT），按 DR-13 登记，**本地打包、禁运行期 CDN**。
- **凭据纪律**：**代码 / 文档 / 日志 / 响应零口令字面量**；初始口令**只**从 `IB_DEFAULT_ADMIN_PASSWORD` 读（0600 EnvironmentFile）；令牌**仅**经 `Authorization: Bearer`；`?token=` / `?access_token=` 在**全部端点**（含 `/api/auth/*`）返回 4xx。
- **未削弱既有断言**：`pytest` **207 passed**（无回归）；selfcheck 既有 **40 例全部保留**（含 401/400/403/409 反向断言）；**未使用** skip / xfail。
- **fail-closed**：生产缺 `IB_AUTHZ_POLICY_MODULE` → `StartupError`（服务**不启动**）；改密态**服务端受限会话**（allowlist 之外一律 403），非前端遮挡。
- **只读约束**：未改 `tests/**`（GROUP_D）、`docs/phase_status.md`（PM）、设计真源四文档；未执行 `git add` / `git commit`；**未部署**、未触碰任何生产目标。
- **知识库/记忆**：本轮新增 5 条 R13 经验，写入 `.claude/agents/knowledge_base/software_developer/`（见 §19.8）。

### 19.8 本轮知识蒸馏（KB）

| 动作 | 条目 | 类型 | 置信度 | 来源 |
|------|------|------|--------|------|
| CREATE | KE-DEV-013「契约项有指定落点模块时，必须在**该模块**落地；只在消费点读取不算实现」 | heuristic | 0.8 | 本轮 §19 起草时发现 IFC-IB-312 未落到 MOD-IB-02，自查后补做 |
| CREATE | KE-DEV-014「端口协议禁改时，用**实现侧扩展方法**满足新需求（`upsert_chunks` / `revoke_sessions_for_user` 先例），并登记 `[DEVIATION]`」 | pattern | 0.8 | D-R13-02 |
| CREATE | KE-DEV-015「Windows 上自检用临时 SQLite 必须显式 close + `TemporaryDirectory(ignore_cleanup_errors=True)`，否则清理异常会**掩盖真实断言失败**」 | exception | 0.8 | `r13_account_store_parity` 修复过程 |
| CREATE | KE-DEV-016「结构化日志 `log_event(stage, outcome, **extra)`：`outcome` 是**位置参数**，不可再放入 `**extra`（否则 `TypeError` 静默吞掉审计事件）」 | exception | 0.8 | `throttle.py::audit` 修复过程 |
| CREATE | KE-DEV-017「源码纪律自检若断言『某字符串不得出现』，必须先**剥离注释**，否则解释性注释会造成假阳性」 | exception | 0.7 | `r13_frontend_auth_discipline` 修复过程 |

## 20. R13.1 回修增量（DEFECT-R13-01：来源 IP 维度登录限速未生效；追加，不改写 §1~§19）

> **依据**：GROUP_D 门控 `condition_1` 登记的 **DEFECT-R13-01**（MEDIUM；可执行证据 = `tests/integration/test_accounts_int_r13.py::TC-INT-119`，实测序列 `[401, 401, 401, 401]`）；缺陷路由 = software-developer（`src/ibweb/views.py` / 组合根接线）。关联 REQ-FUNC-IB-36（`[INFERRED]`，IP 维度登录限速）/ AC-IB-29-01。

### 20.1 缺陷与根因

| 项 | 内容 |
|----|------|
| 缺陷号 | DEFECT-R13-01（MEDIUM） |
| 现象 | 配置来源 IP 维度失败阈值（`IB_LOGIN_MAX_FAILURES=3`）后，同一 IP 连续 4 次错误登录仍全部 401，**429 分支不可达**（TC-INT-119 FAIL） |
| 根因 | `src/ibweb/views.py::auth_login_endpoint` 在**每个请求内**调用 `build_throttle()` 新建一个空 `LoginThrottle`；`LoginThrottle._hits`（`src/ibweb/accounts/throttle.py`）是**实例状态**，`record_failure()` 写入的对象随请求结束被 GC，故滑动窗口**永不跨请求累积**，`check()` 恒 `allow=True` |
| 对照（为何 118 原已 PASS） | 账户维度锁定经 `AccountStore.record_login_failure` **持久化**于用户记录（`views.py` 读 `user.locked_until`），与 IP 维度无关 |

### 20.2 修复方案（最小改动，零新增能力）

1. **限速器提升为应用级单例（装配期构建一次、按请求复用）**：
   - `src/ibweb/composition.py`：`Deps` 新增字段 `login_throttle: Any = None`；`_assemble()` 新增步骤 **4e**，装配期调用一次 `build_throttle()` 并存入该字段。
   - `src/ibweb/views.py`：新增 `_login_throttle()`，从 `composition.get_deps()` 取 `Deps.login_throttle`；`auth_login_endpoint` 改用之，**不再每请求 `build_throttle()`**。
   - **每应用实例一份**（非进程级全局）：生产装配幂等故等价单例；测试每次 `build_deps(force=True)` 得到全新空窗口 → **用例隔离**，无跨用例状态泄漏。
   - 未配置 `IB_LOGIN_MAX_FAILURES` → `build_throttle()` 返回 `None` → 不启用（ADR-27 语义不变）。
2. **账户锁定优先于 IP 限速（保持 TC-INT-118 契约）**：把「取账户 + 判锁定」前置于 429 判定，仅 `not locked` 才走 IP 滑动窗口。理由：账户维度锁定是**权威结论**，已锁定账户必须返回**统一 401**（AC-IB-29-01，不泄露「已锁定」）；若被 IP 维度的 429 遮蔽，会引入「账户是否已锁定」的侧信道，并使 TC-INT-118 回归失败。

> **未修改测试**：本节方案以「同时满足 TC-INT-118 与 TC-INT-119」为约束求解，`tests/**` 零改动。

### 20.3 影响文件与版本

| 文件 | 改动 | 版本 |
|------|------|------|
| `src/ibweb/composition.py` | `Deps.login_throttle` 字段 + `_assemble()` 步骤 4e + 头部 `@implements` 补记 IFC-IB-326 装配 | — |
| `src/ibweb/views.py` | 移除 `build_throttle` 导入；新增 `_login_throttle()`；登录端点改用应用级限速器 + 锁定优先的 429 判定 | — |
| `docs/implementation_plan.md` | 本 §20 + 头部 2.7.0 → **2.8.0** + `latest_invocation_id` | v2.8.0 |
| `docs/code_review_report.md` | 回修自查节（见该文件 §17） | — |
| `tests/**` | **零改动**（未迎合实现改测试、未 skip/xfail） | — |

### 20.4 架构偏差记录

无新增架构偏差（D-R13-01~05 保持不变）。本次「账户锁定优先于 IP 限速」的判定顺序属既有 **AC-IB-29-01** 契约的**兑现**，非偏离任何 ADR。

### 20.5 自验证据（离线；命令可被第三方重跑）

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -m pytest tests/integration/test_accounts_int_r13.py -q -k "TC_INT_118 or TC_INT_119"` | **2 passed**（118 与 119 同时绿） | 0 |
| `python -m pytest tests/unit -q` | **95 passed** | 0 |
| `python -m pytest tests/integration -q` | **123 passed** | 0 |
| `python -m pytest tests/e2e -q` | **21 passed** | 0 |
| `python -m pytest tests -q` | **239 passed**（基线 239/239 不回退） | 0 |
| `python -m compileall -q src` | 无输出 | 0 |
| `python src/scripts/selfcheck.py` | **45/45 通过** | 0 |
| `cd src/frontend && node --test` | **13/13 pass**（未触碰前端） | 0 |

### 20.6 冻结约束复核（R13.1）

- **未改测试用例**：`tests/**` 与 `src/frontend/tests/**` 一字未动；未使用 skip / xfail / 削弱既有断言。
- **未新增能力 / 未回退既有实现**：只把已有的 `LoginThrottle` 由「请求级临时对象」改为「应用级复用实例」+ 调整判定顺序；账户 CRUD / 会话 / 端点契约均未改。
- **凭据纪律**：未引入 Cookie / session；令牌仍仅经 `Authorization: Bearer`；本次改动不涉及任何口令 / 令牌 / 密钥的读写或落盘。
- **依赖纪律**：未新增任何第三方依赖；`langchain-openai<0.3` / `langchain-core>=0.3,<2.0` 未触碰；未引入 Docker / PyMuPDF。
- **只读约束**：未 `git add` / `commit` / `push`；未部署；未触碰任何生产目标；未改设计真源四文档与 `docs/phase_status.md`。

## 21. R14 增量实现（回归缺陷修复：全局管理员「当前项目」选择与 `X-IB-Project` 传播；追加，不改写 §1~§20）

> **依据**：`docs/architecture_design.md` **1.6.0/REV-14** **ADR-28**（项目上下文的选择与传播；4 候选方案，Option B 选定并吸收 Option A 的「单项目预选」便利）+ §2.0.5 R14 影响复核表 + §10.1 R14 OPEN ITEM；`docs/module_design.md` **1.6.0/REV-14** **IFC-IB-333 / 334 / 335 / 336**（§2.2.5 段号索引；§3 MOD-IB-23 的 R14 新增端点与契约；§3 MOD-IB-24 的 R14 项目上下文 store 与传播约束；§4.2.5 无环性再声明；§9.8 覆盖率再声明）；`docs/tech_stack.md` 1.4.0（REV-14 判 **NO_CHANGE**：无新第三方依赖）；需求侧映射 = REQ-FUNC-IB-31 / IB-32 / IB-23、US-IB-24 / AC-IB-24-03 / AC-IB-24-02；`docs/phase_status.md` 的 **IC-IB-02**（REV-14 实现约束）与 REV-14-2（实现范围）；上游 GROUP_B 已 APPROVED（GR-B-007）。

> **命名口径**：设计侧记为 **REV-14**（`architecture_design.md` 1.6.0/REV-14、`module_design.md` 1.6.0/REV-14、`IFC-IB-333~336`），本文件自身版本线记为 **R14 / v2.9.0**（v2.8.0 已被 R13.1 占用）。两套口径指向**同一批**改动。

### 21.1 实现顺序（拓扑排序；被依赖模块先实现）

模块依赖图与 §4.1 逐行不变（**零新增依赖边**）—— 本增量全部落在既有 **MOD-IB-23**（后端）与 **MOD-IB-24**（前端）内部。故实现顺序为：

1. **MOD-IB-23**（后端项目枚举端点 + 头契约）—— 被前端依赖，先实现；
2. **MOD-IB-24**（前端 store + 单点注入 + 控制台选择器）—— 经既有 `MOD-IB-24 → MOD-IB-23` HTTP/SSE 边消费 1 的端点。

模块编号仍即拓扑序（26 个模块，未新增），DAG 无环。

### 21.2 模块实现计划（按拓扑顺序）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-23 | HTTP API 与组合根 | `src/ibweb/views.py`（`projects_endpoint`）/ `src/ibweb/urls.py`（`api/projects`） | —（既有装配） | L | DONE |
| 2 | MOD-IB-24 | Web 前端 | `src/frontend/src/stores/project.ts`（新建）/ `src/frontend/src/api/client.ts` / `src/frontend/src/app/env.ts` / `src/frontend/src/layouts/ConsoleLayout.vue` / `src/frontend/src/main.ts` | MOD-IB-23（仅 HTTP/SSE 契约） | M | DONE |

### 21.3 逐任务落点与设计依据

| 任务 | 落点 | 依据 |
|------|------|------|
| `GET /api/projects`（admin 全部 / ops 仅自身；非项目级端点，未选定项目也 200） | `views.projects_endpoint` + `urls.py` 路由 | IFC-IB-333；ADR-28 Decision ①；数据源 `Deps.projects` |
| `X-IB-Project` 头契约（ops 跨项目 403 / 缺省全局哨兵 / 未知项目不校验存在性） | 既有 `AuthMiddleware`（**未改**，仅契约登记） | IFC-IB-334；加成式扩展 IFC-IB-324 |
| 前端项目上下文 store（`available` / `current` / `load` / `select` 仅 admin / `clear` / `headerValue`） | `stores/project.ts` | IFC-IB-335；ADR-28 Decision ② |
| `X-IB-Project` **单一注入点**（`headers()`；SSE 自动覆盖；提供者注入断开循环依赖） | `client.ts`（`setProjectHeaderProvider` / `projectHeader()` / `headers()` / `listProjects`）+ `app/env.ts` 接线 | IFC-IB-336；ADR-28 Decision ① |
| 控制台项目选择器（admin 可选 / ops 只读）+ 切换即重置视图态 | `ConsoleLayout.vue`（`el-select` + `<router-view :key>`） | IFC-IB-335；ADR-28 Consequences（负向）「切换后须重置项目内视图态」 |
| 登出 / `401` 清空项目上下文 | `ConsoleLayout.confirmLogout` + `main.ts` 的 401 回调 | IFC-IB-335（`clear`） |
| （顺带 MINOR 修复）`import.meta.env` 防御性取值 | `client.ts` `const ENV = import.meta.env ?? {}` | 使「可被离线自检脚本导入」的自身契约成立（否则 Node 下整模块导入即 `TypeError`） |

### 21.4 R14 变更文件清单（`git status` 口径）

**新增（3）**：
| 文件 | 说明 |
|------|------|
| `src/frontend/src/stores/project.ts` | 前端项目上下文 store（IFC-IB-335） |
| `tests/integration/test_project_context_int_r14.py` | R14 集成用例 TC-INT-120~122（离线；纯 pytest，无第三方新增） |
| （无其它新增源码文件） | — |

**修改（6）**：
| 文件 | 说明 | 一句话 |
|------|------|--------|
| `src/ibweb/views.py` | 新增 `projects_endpoint` + `__all__` + 文件头 `@implements` | 项目枚举端点（admin 全部 / ops 仅自身；非项目级端点） |
| `src/ibweb/urls.py` | 注册 `path("api/projects", ...)` + 文件头 | 路由登记 |
| `src/frontend/src/api/client.ts` | `ProjectSummary` / `ProjectListEnvelope` / `ProjectHeaderProvider` 类型 + `setProjectHeaderProvider` + `projectHeader()` + `headers()` 扩展 + `listProjects()` + `import.meta.env` 防御性取值 | 单一注入点 + 项目枚举客户端 |
| `src/frontend/src/app/env.ts` | 装配 `projectContext` 单例 + 接线 `setProjectHeaderProvider` | 唯一装配点（断循环依赖） |
| `src/frontend/src/layouts/ConsoleLayout.vue` | 项目选择器 + `router-view :key` + `load`/`clear` 触发 | 当前项目 UX + 视图态重置 |
| `src/frontend/src/main.ts` | 401 回调追加 `projectContext.clear()` | 防「当前项目」跨会话残留 |

**测试与自检（修改 2）**：`src/scripts/selfcheck.py`（新增 `r14_project_context` / `r14_frontend_project_discipline` 两用例并注册）、`src/frontend/tests/frontend.smoke.test.js`（新增 R14 用例 14~17）。

**文档（修改 2）**：`docs/implementation_plan.md`（本 §21 + 头部）、`docs/code_review_report.md`（§18 + 头部）。

### 21.5 架构偏差记录（R14）

**无新增架构偏差。** 本增量严格遵循 ADR-28（Option B），且**未削弱** fail-closed 纪律（ADR-28 约束③）。一处**实现写法选择**（非架构偏差）需登记：

| 偏差ID | 偏差描述 | 原 ADR 决策 | 偏差原因 |
|--------|---------|------------|---------|
| —（不构成偏差） | `client.ts` 以「暴露项目头提供者 + `env.ts` 注入」而非直接 `import stores/project.ts` 取值 | ADR-28 只说「单一注入点由 `headers()` 扩展、取值来自 `projectContext` store」，未规定接线写法 | 直接 import 会形成 `client.ts ↔ project.ts` 的 ESM 循环依赖。ADR-28 的 Decision 与 IFC-IB-336 均允许「等价注入」（「或等价注入」原文），故属**契约内的实现选择**，非偏离 |

**顺带 MINOR 修复**：`client.ts` 的 `import.meta.env` 防御性取值（见 §21.3 末行）—— 不影响 Vite 构建期行为，仅为兑现该文件「可被离线自检脚本导入」的既有自述契约。

### 21.6 R14 自验证据（离线；命令可被第三方重跑）

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -m compileall -q src/ibweb src/ib src/scripts tests` | 无输出 | 0 |
| `python src/scripts/selfcheck.py` | **47/47 通过**（基线 45 + R14 新增 2） | 0 |
| `python -m pytest tests -q` | **242 passed**（基线 239 + R14 新增 3；零回退） | 0 |
| ├ `python -m pytest tests/unit -q` | 95 passed | 0 |
| ├ `python -m pytest tests/integration -q` | **126 passed**（基线 123 + R14 新增 3） | 0 |
| └ `python -m pytest tests/e2e -q` | 21 passed | 0 |
| `cd src/frontend && npm run typecheck` | 无输出（`vue-tsc --noEmit` 通过） | 0 |
| `cd src/frontend && npm run build` | `✓ built`（1640 modules；产物正常） | 0 |
| `cd src/frontend && npm test`（`node --test`） | **17/17 pass**（基线 13 + R14 新增 4；用例 17 为**真跑**行为断言） | 0 |
| `node --experimental-strip-types src/scripts/sse_parser_selfcheck.mts` | **ALL PASS**（修复 `import.meta.env` 后恢复；此前因该值在 Node 下为 `undefined` 而整模块导入失败） | 0 |

### 21.7 冻结约束复核（R14）

- **未新增模块 / 端口 / 依赖边**：模块数仍 **26**、端口数仍 **15**、§4.1 依赖边逐行未改；`GET /api/projects` 是既有 `MOD-IB-24 → MOD-IB-23` HTTP 边上的新端点。
- **未改既有 IFC 编号 / 签名**：`IFC-IB-001~332` 一字未改；新增 **333~336**（纯追加）；`IFC-IB-324` 仅**加成式扩展**（`AuthMiddleware` 文本未改）。
- **授权真源不变**：`X-IB-Project` **不是**鉴权凭据、不新增授权维度；判定仍只经注入的 `AuthzPolicy`（ADR-22）；身份判定沿用 `_ctx_of` / `get_authz` / `is_global`，**未新增第二套授权逻辑**。
- **fail-closed 未削弱**：前端未选项目 ⇒ 不注入头 ⇒ 服务端取全局哨兵 ⇒ 项目级端点继续 fail-closed（**未选项目即不泄露**）；**禁止**把哨兵解析为并集（ADR-28 Option C 被拒）。
- **认证契约未破坏**：令牌仍仅经 `Authorization: Bearer`；`?token=` 仍 `4xx`（含 `/api/projects`）；零 `Set-Cookie`；改密态与 admin/ops 角色划分不变。
- **凭据纪律**：未写入任何口令 / 令牌 / 密钥字面量；新增测试口令为**测试替身占位值**（与既有 `R13_*_PASSWORD` 同性质）。
- **依赖纪律**：未新增任何第三方依赖；前端仍 **Element Plus / vue-router 本地打包、禁 CDN、hash 路由、不引 Pinia**；未引入 Docker / PyMuPDF。
- **只读约束**：未 `git add` / `commit` / `push`；未部署；未触碰目标机；未改 `requirements_spec.md` / `user_stories.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` / `phase_status.md`。

---

# §22 REV-16-2 增量实现（提示词分层 + 工具可视化配置：IFC-IB-339~354；追加，不改写 §1~§21）

> 调用：`INV-GROUP_C-INTELBASE-015`（GROUP_C = PHASE_05 实现 + PHASE_06 自评）。
> 上游（均 APPROVED）：`requirements_spec.md` **1.7.0 / REV-16-3**、`user_stories.md` **1.6.0 / REV-16-2**、
> `architecture_design.md` **1.7.1 / REV-16-3**（ADR-15-R1 / ADR-29 / ADR-30 / ADR-31 / ADR-32 / ARCH-ASSUMPTION-A10）、
> `module_design.md` **1.7.1 / REV-16-3**（IFC-IB-339~354）。
> 参考仓 `C:\Users\胖子熊\MyProject\FreeArk` 全程**只读**（未写入一个字节）。

## 22.1 结论摘要（本轮范围四项 + 一条纪律）

| # | 范围 | 落点 | 状态 |
|---|------|------|------|
| 1 | 提示词主 / 兜底分层 + **独立 markdown 提示词目录**（第 16 个端口 `ExpertPromptStore` / IFC-IB-339） | MOD-IB-01 / MOD-IB-02 / MOD-IB-16 / MOD-IB-22 / MOD-IB-23 / MOD-IB-24 | DONE |
| 2 | 工具**授权勾选** + **可配工具参数**（IFC-IB-350，作用于**既有**工具集，**不新增工具本体**） | MOD-IB-01（`ToolParamSpec` / `ToolParamValue`）/ MOD-IB-17 / MOD-IB-23 / MOD-IB-24 | DONE |
| 3 | **FreeArk 严格对齐**（ADR-31）：专家硬改名 + `AGGREGATION_FORBIDDEN_LABELS` 派生只读视图 + 过渡态**旧 ∪ 新**并集 | MOD-IB-16（专家登记）/ MOD-IB-22（`forbidden_labels(cn_map)`） | DONE |
| 4 | **装配期完备性校验**跨两域（ADR-16）：孤儿提示词文件 / 缺兜底 / 工具参数越界；两域按专家 `name` 合并 | MOD-IB-02 / MOD-IB-17 / MOD-IB-23 | DONE |
| — | **生效口径**（ADR-32 / C-IB-40）：保存 = 原子落盘 + **重启后**装配期重组；**无运行期热重载、不重编译编排图** | MOD-IB-23（端点）+ MOD-IB-24（强制提示文案） | DONE |

**未新增模块**（模块数仍 **26**）；**新增端口 15 → 16**（`ExpertPromptStore`，IFC-IB-339）；`ib.core` 仍**零三方依赖**。

## 22.2 模块实现计划（按拓扑顺序；REV-16-2 触及部分）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-01 | 核心契约层（零三方依赖） | `src/ib/core/types.py` / `ports.py` / `errors.py` / `__init__.py` | — | H | DONE |
| 2 | MOD-IB-02 | 配置与定义文档数据层 | `src/ib/config/__init__.py` / `definition.py` / `prompts.py`(新) | MOD-IB-01 | H | DONE |
| 3 | MOD-IB-16 | 派生注入层（专家登记） | `src/ib/experts/__init__.py` | MOD-IB-01/02 | M | DONE |
| 4 | MOD-IB-17 | 工具运行时（授权绑定 + 参数派生） | `src/ib/tools/__init__.py` | MOD-IB-01 | M | DONE |
| 5 | MOD-IB-22 | 编排层（禁止标签派生视图） | `src/ib/orchestration/__init__.py` | MOD-IB-01/16 | M | DONE |
| 6 | MOD-IB-23 | Web 装配与端点 | `src/ibweb/composition.py` / `views.py` / `urls.py` | MOD-IB-01/02/16/17/22 | H | DONE |
| 7 | MOD-IB-24 | 前端配置页（分层编辑器 + 勾选 + 参数） | `src/frontend/src/api/client.ts` / `src/views/ConfigPage.vue` / `tests/frontend.smoke.test.js` | MOD-IB-23（仅 HTTP 契约） | M | DONE |

**实现顺序说明**：`core`（契约）→ `config`（数据层）→ `tools` / `experts`（派生）→ `orchestration`（消费派生）→ `ibweb`（装配 + 端点）→ `frontend`（消费端点）。与 §4.1 既有依赖边**逐行一致**，无新增依赖边。

## 22.3 逐项落地要点

> **REV-17 后注（2026-10-07，协调者机械落盘）**：本节（§22.3）为 **REV-16-2 交付时的口径快照**，其中 **5 处表述已被 REV-17 取代**，原文按「只追加、不改写历史小节」纪律**保留不动**，以本条注记关档：① **§22.3.2** 的合并优先级第三层「定义文档兜底」→ 现为**代码内置兜底**，`resolved_from` 第三值 `definition_doc_fallback` → **`builtin_fallback`**；② **§22.3.3** 的 `validate_prompt_directory(refs, *, doc)` 形参 → 现为 `(refs, *, doc, builtin_fallbacks=None)`，且缺兜底判据改为「无 `fallback.md` **且** 无内置兜底」；③ **§22.3.4** 的 `derive_prompt_layers(doc, refs)` → 现增 `builtin_fallbacks=None`，`_prompt_of` 的回落分支由「文档兜底」改为「内置安全网」（`spec.fallback_prompt`）；④ **§22.3.6** 的 `admit_two_domains` 聚合口径 → 现改调 **`validate_two_domains`**（IFC-IB-364，范围**含提示词域**，保存期与装配期**同序同条**）；⑤ **§22.3.8** 的前端回退标签三值「主提示词 / 主缺失回退兜底 / 定义文档兜底」→ 第三值文案同步为**内置兜底**（`fallback_file` 一层文案一字未改）。**§22.3 其余小节与 §22.1 / §22.2 / §22.4~22.6 的结论不受影响**（模块数 26、端口数 16 等不变约束在 REV-17 仍成立）。**现行口径以 §24 为准**。

### 22.3.1 第 16 个端口 `ExpertPromptStore`（IFC-IB-339；MOD-IB-01）

`ib.core.ports` 新增 `ExpertPromptStore` Protocol（`list_refs` / `load_bundle` / `save_layer` / `delete_layer` / `layout`）。**零三方依赖**（Protocol + dataclass，stdlib only），与既有 15 个端口同层。
新增 dataclass / 错误：`ExpertPromptRef` / `PromptBundle` / `PromptDirectoryLayout` / `PromptSaveResult` / `ToolParamSpec` / `ToolParamValue` / `PromptNotFoundError` / `ToolParamValidationError`。
两个实现（MOD-IB-02 `src/ib/config/prompts.py`）：
- `InMemoryExpertPromptStore`（离线测试替身；与 Fs 语义**逐条一致**——同名参数化测试同时跑两者）；
- `FsExpertPromptStore`（`<root>/<project_id>/<expert_name>/{main.md|fallback.md}`；**原子写**（临时文件 + `os.replace`）；子目录名 = 专家 `name`（ADR-15-R1 合并键）；`..` 路径穿越**拒绝**）。

### 22.3.2 分层合并 `merge_prompt_layers`（IFC-IB-343；MOD-IB-02）

优先级：**主文件 > 兜底文件 > 定义文档兜底**；`resolved_from ∈ {main_file, fallback_file, definition_doc_fallback}`。
**`effective_prompt` 恒非空**（ADR-29）：三层皆空 → `PromptNotFoundError`（fail-closed，**不返回空提示词**）。
`prompt_content_hash` = `"sha256:" + hex`（语义哈希，乐观并发判据）。

### 22.3.3 目录装载 / 完备性校验（IFC-IB-345；MOD-IB-02）

`load_prompt_directory(root, project_id)`：目录**不存在 ⇒ 空元组**（不报错，未配置即未配置）。
`validate_prompt_directory(refs, *, doc)` → `{prompt_orphan_file, prompt_naming_mismatch, prompt_fallback_missing}`。
`validate_tool_params(grants, *, specs)` → `{tool_param_unknown, tool_param_unauthorized_tool, tool_param_type_mismatch, tool_param_out_of_range, tool_param_choice_invalid}`。
**`ValidationReport` 未新增 `force` / `ignore` / `warn_only`**（ADR-16 决议）。

### 22.3.4 跨域合并派生与注入（IFC-IB-347 / 349；MOD-IB-02 / MOD-IB-16）

`derive_prompt_layers(doc, refs)` 按专家 `name` **join** 两域，产出 `prompt_bundles`；`install_prompt_bundles` 注入 `ib.experts` 注册表。
`ib.orchestration._prompt_of(expert)` 优先取**已注入的分层有效提示词**，无则回落文档兜底 —— 于是「编辑提示词不重编译图」也能在**重启后**装配期生效。

### 22.3.5 工具授权勾选 + 参数（IFC-IB-350；MOD-IB-17）

`derive_tool_param_specs(registry)` 由**既有工具**的 JSON Schema **派生**限定名规格 `<tool>.<param>`（类型 / 默认 / 最小 / 最大 / 枚举）——派生而非手写，规格与工具声明**不可能漂移**。
`build_authorized_tools(grants, registry, specs)`：授权 = 最小集合；参数经 `functools.partial` 注入，**调用方显式实参优先**（配置作默认）。
`bind_scope` 增益：对 `BoundTool` 且其 callable 仍需 `scope` / `retrieval` 者**重包裹**，使「授权 + 参数 + 范围绑定」三种包装可叠加（补上 R7 之后出现的组合缺口）。
**未新增任何工具本体**（`register_builtin_tools` 名单一字未增）。

### 22.3.6 装配期两域闸门（IFC-IB-353；MOD-IB-23）

`composition.admit_two_domains(doc, *, store, prompt_refs, tool_specs)` = `store.validate` ∪ `validate_prompt_directory` ∪ `validate_tool_params`，任一非空即**拒绝装配**（错误计数不重复：工具名存在性仍由 `validate` 单点裁决）。
**`admit(doc, *, store=None)` 签名一字未改**（既有冻结断言 `set(signature) == {"doc","store"}` 仍绿）——两域聚合走**新函数**，属加成式扩展。
`build_prompt_stores(cfg, projects)`：非离线 + `IB_EXPERT_PROMPT_DIR` 已设 + 提示词域开关开 → `FsExpertPromptStore`，否则 `InMemoryExpertPromptStore`（离线可测）。
新增 `known_tool_names()`（既有工具名单，勾选 UI 与装配期校验**同源**）。

### 22.3.7 端点族（IFC-IB-352；MOD-IB-23）

- `GET /api/config/prompts` → `{experts, tool_param_specs, available_tools, layout, config_key_names}`（**列表只出元数据 + 哈希，不出正文**；`config_key_names` **只登记键名**）。
- `GET /api/config/prompts/<expert>/<layer>` → `{content, content_hash}`；不存在 / 不属于你 → **统一 404**（反存在性探测）。
- `PUT /api/config/prompts/<expert>/<layer>` → 200 / 400（校验）/ 403（无管理权）/ 404 / 409（`prompt_content_hash_conflict` 乐观并发）。
- 总开关关闭 → 整族 404；`?token=` 仍被中间件先行拒绝（不接受查询参数令牌）。
- **保存不触发运行期重建**：集成用例断言 `deps.orchestrator_for(p) is deps.orchestrator_for(p)`（同一实例）。

### 22.3.8 前端分层编辑器（IFC-IB-354；MOD-IB-24）

- **分层编辑器**：每个专家**主 / 兜底**两个独立文本域 + 逐层保存；两域**各自独立草稿与基线哈希**（提示词域与定义文档域不互串乐观并发判据）。
- **回退可见**（US-IB-30）：`resolvedFrom(expert)` 派生「当前生效 = 主提示词 / 主缺失回退兜底 / 定义文档兜底」并**常驻显示**。
- **工具授权勾选**：`available_tools` 渲染 checkbox（只作用于既有工具集）；**工具参数**按 `ToolParamSpec` 生成控件（int/float 数字带 min/max、bool 开关、枚举下拉、否则文本框；留空 = 用工具默认）。
- **生效口径显式提示（强制）**：保存成功文案 =「**保存成功；重启 `ib-web` / `ib-worker` 后生效**（保存仅原子落盘，不热重载）」；界面**无**任何热重载 / 运行期重建入口。
- **视图侧零持久化**仍未破坏：提示词草稿只在内存，无 `localStorage` / `IndexedDB`；**零新增前端依赖**（仍无 CDN、无 Docker）。

### 22.3.9 FreeArk 严格对齐（ADR-31；MOD-IB-16 / MOD-IB-22）

| 旧（业务名） | 新（FreeArk 对齐） | 中文标签变更 |
|---|---|---|
| `data-expert` | `freeark-expert` | `数据管家` → `系统管家` |
| `knowledge-expert` | `sanheng-knowledge` | `知识库问答` → `三恒知识` |
| `inspection-expert`（未变） | `inspection-expert` | `巡检诊断`（未变） |

**硬改名，无并存窗口**（无旧名兼容分支）。`AGGREGATION_FORBIDDEN_LABELS` 改为**派生只读视图** `forbidden_labels(cn_map)`（IFC-IB-351，MOD-IB-22）。
**过渡态例外（ADR-31 Decision 第 4 条）**：`_TRANSITION_EXPERT_LABELS` 保留**旧 ∪ 新**并集（`数据管家` / `知识库问答` / `巡检诊断` / `系统管家` / `三恒知识`），以保证过渡期旧标签**不会被聚合起来输出**。这是本轮**唯一**保留旧中文标签的位置，属 ADR 明令，非遗漏。

## 22.4 架构偏差记录（REV-16-2）

| 偏差 ID | 偏差描述 | 原 ADR 决策 | 偏差原因 |
|---------|---------|------------|---------|
| —（不构成偏差） | 两域聚合走**新函数** `admit_two_domains`，而 `admit` 签名保持不变 | ADR-16 要求装配期跨域完备性校验；IFC-IB-353 描述装配序列 | `admit` 的签名被 §18 的冻结断言（`{"doc","store"}`）钉住；把两域聚合放进新函数是**加成式扩展**（既有调用面零改动），语义与 IFC-IB-353 一致 |
| —（不构成偏差） | 工具参数注入用 `functools.partial`（而非在 `build_authorized_tools` 内再写一层包装） | ADR-30 / IFC-IB-350 只规定「参数注入 + 调用方优先」 | 未规定接线写法；`partial` 的「调用点显式实参覆盖已绑默认值」语义**天然**满足「调用方优先」，且不引入新包装层 |
| —（不构成偏差） | 提示词正文经**独立端点** `GET /api/config/prompts/...` 读取，不塞进定义文档响应 | ARCH-ASSUMPTION-A10 / ADR-15-R1 划两域 | 两域真源不同；把提示词正文混入文档响应会破坏「列表不出正文」与定义文档白名单边界 |

## 22.5 REV-16-2 自验证据（离线；命令可被第三方重跑）

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -m compileall -q src` | 无输出 | 0 |
| `python src/scripts/selfcheck.py` | **50/50 通过**（基线 47 + REV-16-2 新增 3） | 0 |
| `python -m pytest tests/ -q` | **273 passed**（基线 254 + REV-16-2 新增 19；零回退） | 0 |
| `cd src/frontend && npm run typecheck`（`vue-tsc --noEmit`） | 无输出 | 0 |
| `cd src/frontend && npm test`（`node --test`） | **26/26 pass**（基线 21 + REV-16-2 新增 5） | 0 |
| 旧专家 slug 全仓扫描 | `src/` `tests/` 中 **0 处**（唯一命中为本轮新增的**反向核验断言**自身） | — |
| 新专家 slug 出现次数 | `freeark-expert` 48 次 / `sanheng-knowledge` 15 次；新中文标签 `系统管家` 15 次 / `三恒知识` 7 次 | — |

**新增 / 修改文件清单（REV-16-2）**

- 新增：`src/ib/config/prompts.py`、`tests/unit/test_prompt_layers_r16.py`、`tests/integration/test_prompt_config_r16.py`
- 修改：`src/ib/core/{types,ports,errors,__init__}.py`、`src/ib/config/{__init__,definition}.py`、`src/ib/experts/__init__.py`、`src/ib/tools/__init__.py`、`src/ib/orchestration/__init__.py`、`src/ibweb/{composition,views,urls}.py`、`src/scripts/selfcheck.py`、`src/frontend/src/api/client.ts`、`src/frontend/src/views/ConfigPage.vue`、`src/frontend/tests/frontend.smoke.test.js`

## 22.6 冻结约束复核（REV-16-2）

- **未新增模块**（26 个不变）；**端口 15 → 16**（`ExpertPromptStore`，IFC-IB-339）；§4.1 依赖边**逐行未改**。
- **未改既有 IFC 编号 / 签名**：`IFC-IB-001~338` 一字未改（含 `admit`）；新增 **339~354**。
- **零新增第三方依赖**（后端与前端皆然）；无 Docker；无 PyMuPDF / `fitz`；`langchain-openai` 仍 `<0.3`。
- **无运行期 CDN / 无数据外发**；前端仍本地打包。
- **凭据纪律**：未写入任何口令 / 令牌 / 密钥字面量；`config_key_names` **只登记键名**（`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED`）；测试正文为占位中文，**不含**任何凭据。
- **fail-closed / fail-safe 未削弱**：三层皆空 → 拒绝（不返回空提示词）；兜底存空 → 拒绝；保存失败不影响在用配置；保存不重建编排图（ADR-32 / C-IB-40）。
- **只读约束**：未 `git add` / `commit` / `push` / `stage`；未部署；未触碰目标机；FreeArk 参考仓**只读**。

---

## 23. REV-16-4 增量实现（DEFECT-R16-01/02 + GAP-R16-03/04：配置审计与存储态；追加，不改写 §1~§22）

**设计侧口径**：`docs/module_design.md` **1.8.0/REV-16-4**（§2.2.7 IFC-IB-355~363）+ `docs/architecture_design.md` **1.8.0/REV-16-4**（ADR-33/34/35 + §2.0.7）。**上游** GR-A-009 = PASS / GR-B-009 = PASS。

> **REV-17 后注（2026-10-07，协调者机械落盘）**：本节为 **REV-16-4 交付时的口径快照**，原文按纪律保留不动，两处以本条关档：① **§23.3 的「签名零改动」中 `admit_two_domains` 一项已被 REV-17 取代** —— 现签名增 `builtin_fallbacks: Mapping | None = None`（缺省取 `ib.experts.builtin_fallbacks()`），即闸门由「三域拼接」上提为 **`validate_two_domains`（IFC-IB-364）是唯一入口**；当时的**冻结断言仍绿**，因其形如 `{"doc","store","prompt_refs","tool_specs"} <= params` 与「不得含 force/ignore/warn_only」的**子集 / 否定式**断言（`tests/e2e/test_config_restart_effect_r16.py:126-129`、`tests/unit/test_prompt_tool_config_unit_r16d.py:169-171`），加参数不触及；`admit` 的 `{doc, store}` **逐字冻结在 REV-17 仍成立**。② **`validate_definition_full`（IFC-IB-355）签名与行为均未被 REV-17 改动** —— REV-17 **新增** `validate_two_domains` 包在其外，正是为不改该函数（`tests/unit/test_config_audit_rev16_4_unit.py:93-95` 用 `getsource` 扫它）。**现行口径以 §24 为准**。

### 23.1 结论摘要（本轮范围四项 + 一条纪律）

| 项 | 类型 | 结论 | 关键落点 |
|----|------|------|----------|
| DEFECT-R16-01 | 回归缺陷 | **DONE** | `src/ibweb/serializers.py::_ToolGrantSpecSerializer`（手写 `to_representation`，补 `param_values`） |
| DEFECT-R16-02 | 回归缺陷 | **DONE** | `src/ib/config/definition.py::validate_definition_full`（IFC-IB-355）+ `src/ibweb/views.py::_put_definition_config` + `src/ibweb/composition.py::admit_two_domains` |
| GAP-R16-03 | 缺口（ADR-35） | **DONE** | IFC-IB-361 `StorageState` + IFC-IB-362 `GET /api/config/storage-state` + IFC-IB-363 前端非静默提示 |
| GAP-R16-04 | 缺口（ADR-34） | **DONE** | IFC-IB-356~360：`ConfigAuditEntry` / `ConfigAuditStore`（第 17 端口）/ `SqliteConfigAuditStore` + 迁移 `004_config_audit.sql` / `record_config_audit` + 保存路径挂钩 / `GET /api/config/audit` |

**一条纪律（全轮不变）**：**只读审计、非第二真源**（ADR-34）—— 审计表**无写回配置的路径**、`ConfigAuditEntry` **只含字段名与结果码**（绝不落取值 / 凭据）；审计写与配置写**非事务耦合**，失败**不改变**保存结果但**不静默**（发结构化 `WARN config_audit_write_failed`，字段白名单）。

### 23.2 模块实现计划（按拓扑顺序；REV-16-4 触及部分）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-01 | 核心契约（端口与结构） | `src/ib/core/types.py`（+`ConfigAuditEntry`/`ConfigAuditResult`/`StoreMode`/`StorageState`）、`src/ib/core/ports.py`（+`ConfigAuditStore` 第 17 端口）、`src/ib/core/__init__.py`（汇总导出） | — | L | DONE |
| 2 | MOD-IB-02 | 配置 / 定义文档数据层 | `src/ib/config/definition.py`（+`validate_definition_full` IFC-IB-355）、`src/ib/config/__init__.py`（导出） | MOD-IB-01 | M | DONE |
| 3 | MOD-IB-11 | 台账（含账户 / 审计） | `src/ib/ledger/schema.py`（+`config_audit` DDL）、`src/ib/ledger/config_audit.py`（新建）、`src/ib/ledger/__init__.py`（惰性导出） | MOD-IB-01 | M | DONE |
| 4 | MOD-IB-23 | Web / 组合根 / 端点 | `src/ibweb/composition.py`、`src/ibweb/views.py`、`src/ibweb/urls.py`、`src/ibweb/serializers.py`（装配审计存储 / 存储态快照 / 保存路径挂钩 / 两个只读端点 / 两个投影） | MOD-IB-01/02/11 | H | DONE |
| 5 | MOD-IB-24 | 前端（配置页 / 客户端） | `src/frontend/src/api/client.ts`（`storageState`/`configAudit`）、`src/frontend/src/views/ConfigPage.vue`（内存态非静默提示） | MOD-IB-23 | M | DONE |
| 6 | MOD-IB-25 | 部署交付物 | `src/deploy/migrations/004_config_audit.sql`（新建，与 `schema.py::config_audit_ddl_script()` 单源） | MOD-IB-11 | L | DONE |

### 23.3 逐项落地要点

**① DEFECT-R16-01（`param_values` 静默丢参）** —— `src/ibweb/serializers.py`：
`_ToolGrantSpecSerializer` 由自动 `_fields` 展开改为**手写 `to_representation`**（与该文件 `_EdgeSpecSerializer` 同纪律）：
保序输出 `{"expert_name", "tool_names", "param_values"}`，`param_values` 为 `[{"name","value"}, …]`。
线形与 `document_to_json`/`document_from_json` 的 `_semantic_payload` **逐字段一致**（`[{"name","value"}]`），
故「GET 读回 → PUT 原样写回」**逐字节等价**（DEFECT-R16-01 的根因消除）。**无其它字段线形变化**。

**② DEFECT-R16-02（保存 / 装配校验漂移）** ——
- **新增** `src/ib/config/definition.py::validate_definition_full`（IFC-IB-355）：**合成纯函数**（无 I/O、无副作用）
  = `validate(doc, known_tools=…)`（IFC-IB-290）∪ `validate_tool_params(doc.tool_grants, specs=tool_param_specs)`（IFC-IB-346）；
  两段错误**按固定顺序合并**（定义文档域在前、工具参数域在后）为**一份** `ValidationReport`。
  `validate_tool_params` 位于 `ib.config.prompts`（其在模块层导入本模块）⇒ **函数内惰性导入**避免循环依赖。
- **保存路径**（`src/ibweb/views.py::_put_definition_config`）：`deps.definition_store.validate(submitted)` → `validate_definition_full(submitted, known_tools=composition.known_tool_names(), tool_param_specs=deps.tool_param_specs())`。
- **装配路径**（`src/ibweb/composition.py::admit_two_domains`）：`store.validate(doc)` + `validate_tool_params(...)` → **一次** `validate_definition_full(doc, known_tools=_known_tool_names(), tool_param_specs=tuple(tool_specs))`；提示词目录域 `validate_prompt_directory` 保持（错误码集合不变，仅顺序为定义+工具参数在前）。
- **签名零改动**：`validate` / `validate_tool_params` / `store.validate` / `admit` / `admit_two_domains` 参数集**逐字不变**（见 §23.5）。
- **fail-safe**：校验不通过 ⇒ 返回 4xx / 弃装配，**在用配置逐字节不变**（未进入 `save()` 的写路径）。

**③ GAP-R16-03（存储态，ADR-35）** ——
- `src/ib/core/types.py`：`StoreMode: Literal["memory","file"]` + `StorageState(definition_store, prompt_store, definition_store_configured, prompt_store_configured)`（frozen dataclass）。
- `src/ibweb/composition.py`：装配期调用 `_derive_storage_state(definition_store, prompt_stores)`（**由实际存储实例的 `isinstance` 判定** —— `FileDefinitionDocumentStore` ⇒ file、`FsExpertPromptStore` ⇒ file，否则 memory；`configured` = 对应键名是否提供非空值，**只登记键名与否，不回显值**），存入 `Deps.storage_state`；`get_storage_state()` 直读该快照（**不经第二真源 / 不在请求期从环境变量再推导**）。
- `src/ibweb/views.py::storage_state_endpoint` + `src/ibweb/urls.py`：`GET /api/config/storage-state` → `200 StorageState` | `403` | `503`（fail-closed）。
- `src/frontend/src/views/ConfigPage.vue`：`loadStorageState()` 消费端点；`memoryNotice`（任一 mode == "memory"）**常驻显式渲染**提示「配置仅内存生效、不跨重启保留」；读不到存储态（fail-closed）**不静默当作文件态**。**未改变**生效口径、**未引入**热重载。

**④ GAP-R16-04（配置审计，ADR-34）** ——
- `src/ib/core/types.py`：`ConfigAuditResult: Literal["saved","rejected"]` + `ConfigAuditEntry(timestamp, project, actor, action, changed_field_names, result, detail_code)`（frozen dataclass）。
- `src/ib/core/ports.py`：第 **17** 个端口 `ConfigAuditStore`（`@runtime_checkable Protocol`）—— **恰好 2 方法** `record(entry)` / `list_by_project(project_id, *, limit, offset)`；**类型层无 update/delete**（「只读审计、非第二真源」为类型层事实）。
- `src/ib/ledger/schema.py`：`CONFIG_AUDIT_DDL_STATEMENTS`（`CREATE TABLE IF NOT EXISTS config_audit`，`CHECK (result IN ('saved','rejected'))`；`changed_field_names` 存**只含字段名**的 JSON 数组）+ 索引 `idx_config_audit_project(project, entry_id)` + `config_audit_ddl_script()` + `CONFIG_AUDIT_EXPECTED_COLUMNS` / `missing_config_audit_columns`，纳入 `ensure_schema`。
- `src/ib/ledger/config_audit.py`（新建）：`SqliteConfigAuditStore`（线程局部连接 + WAL + `busy_timeout`，同 `SqliteAccountStore` 纪律；`record` 只 INSERT，`list_by_project` 按 `entry_id` **升序**稳定回放）、`MemoryConfigAuditStore`（离线替身）、`build_config_audit_store(cfg, *, ledger_path)`（跟随 `cfg.ledger_backend`；sqlite 构造失败**不静默降级**）。
- `src/deploy/migrations/004_config_audit.sql`（新建）：与 `config_audit_ddl_script()` **单源摘录**（含幂等 + 回滚说明）。
- `src/ibweb/composition.py`：`Deps.config_audit_store` + `_assemble` 装配构建；`changed_field_names(previous, current)`（递归**结构路径**差分，排除 `content_hash`/`updated_at`，**只出字段名 / 下标，绝不落取值**）；`record_config_audit(entry, *, deps)`（**永不抛**；失败发 `WARN config_audit_write_failed`）。
- `src/ibweb/views.py`：`_put_definition_config` **顺序 = 校验 → 落盘 → 审计写**（`_audit_definition_save`；成功 `saved` / 被拒 `rejected` + `detail_code` 只含错误码）；`config_audit_endpoint` + `urls.py`：`GET /api/config/audit?limit=&offset=` → `200 {items, total}` | `403` | `503`（fail-closed，**不返回空集合冒充「无记录」**）；`project_id` **只认服务端结论** `ctx.authz.project_id`。

### 23.4 架构偏差记录（REV-16-4）

| 偏差 ID | 偏差描述 | 原 ADR 决策 | 偏差原因 |
|---------|---------|------------|---------|
| —（不构成偏差） | `validate_definition_full` 的 `known_tools` 注解取 `tuple[str, ...] | frozenset[str] | set[str] | None`（IFC-IB-355 文本作 `tuple[str, ...] | None`） | IFC-IB-355 只规定「工具名集合」语义，未冻结容器类型 | 与既有 `validate`（IFC-IB-290）的形参类型**同构**并取超集：既满足 IFC 文本，又使既有调用点（传 `frozenset`）零改动；运行期 `frozenset(known_tools)` 兼容任意可迭代 |
| —（不构成偏差） | `changed_field_names` 对列表用**下标路径**（如 `tool_grants[0].param_values[1]`） | IFC-IB-360 只规定「只出字段名 / 码，不含取值」 | 下标是**纯结构**表达，**不引入任何取值**；以专家名等作为路径段会构成「值进入审计」，与 ADR-34 更相冲突 |
| —（不构成偏差） | `GET /api/config/audit` 的 `total` 由一次**上限扫描**（`_AUDIT_TOTAL_SCAN_LIMIT = 1000`）内 `len()` 得出 | IFC-IB-359 规定响应含 `total`，端口只提供 `list_by_project`（2 方法，无 count） | 端口方法集被 IFC-IB-357 钉死为 2 个（不得加 `count`）；审计为**追加式且写入稀疏**，上限扫描足以给出稳定 `total`，不新增端口方法 |

**无偏离 ADR-32 / 33 / 34 / 35 的实质性偏差。**

### 23.5 自验证据（离线；命令可被第三方重跑）

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -m compileall -q src` | 无输出 | 0 |
| `python -m src.scripts.selfcheck` | **50/50 通过**（基线 50，零回退） | 0 |
| `python -m pytest tests/unit tests/integration -q` | **273 passed**（零回退；含 r16d 21 项） | 0 |
| `python -m pytest tests/e2e -q` | **24 passed** | 0 |
| `python -m pytest tests/unit/test_prompt_layers_r16.py tests/unit/test_prompt_tool_config_unit_r16d.py tests/integration/test_prompt_config_r16.py tests/integration/test_prompt_tool_config_int_r16d.py tests/e2e/test_config_restart_effect_r16.py tests/integration/test_definition_config_r7.py -q` | **52 passed**（含 TC_INT_139/140 两缺陷复现用例） | 0 |
| `cd src/frontend && npx vue-tsc --noEmit` | 无输出 | 0 |
| `cd src/frontend && node --test` | **27/27 pass**（基线 27，零回退） | 0 |
| 既有 IFC 签名比对（`inspect.signature`） | `validate` / `validate_tool_params` / `store.validate` / `admit` / `admit_two_domains` **逐字未变** | — |

**基线对照**：修改前 `test_prompt_tool_config_int_r16d.py` 为 **2 failed / 5 passed**（TC_INT_139 期望 400 实得 200；TC_INT_140 `param_values` 缺键）—— 即两缺陷的**复现用例**；本轮修复后 **7 passed**。

**新增 / 修改文件清单（REV-16-4）**

- 新增：`src/ib/ledger/config_audit.py`、`src/deploy/migrations/004_config_audit.sql`
- 修改：`src/ib/core/types.py`、`src/ib/core/ports.py`、`src/ib/core/__init__.py`、`src/ib/config/definition.py`、`src/ib/config/__init__.py`、`src/ib/ledger/schema.py`、`src/ib/ledger/__init__.py`、`src/ibweb/composition.py`、`src/ibweb/views.py`、`src/ibweb/urls.py`、`src/ibweb/serializers.py`、`src/frontend/src/api/client.ts`、`src/frontend/src/views/ConfigPage.vue`
- **未触碰**：`tests/**`（GROUP_D 输出目录）、`docs/user_stories.md`、`docs/requirements_spec.md`、`docs/architecture_design.md`、`docs/module_design.md`

### 23.6 冻结约束复核（REV-16-4）

- **未新增模块**（26 个不变，MOD-IB-01~26）；**端口 16 → 17**（`ConfigAuditStore`，IFC-IB-357，纯追加，2 方法无 update/delete）；§4.1 依赖边**逐行未改**。
- **未改任何既有 IFC 编号 / 签名 / 字段集**：`IFC-IB-001~354` 一字未改；新增 **355~363**（9 条）。
- **零新增第三方依赖**（仅 stdlib `sqlite3`）；无 Docker；无 PyMuPDF / `fitz`；`langchain-openai` 仍 `<0.3`；bge-m3 权重未入仓。
- **生效口径未变**：仍为「保存 + 服务重启重装配」（ADR-32 / C-IB-40 / OOS-16）；存储态端点**仅暴露**，**不引入**运行期热重载（ADR-35）。
- **只读审计 / 非第二真源**：审计表无写回配置路径；`ConfigAuditStore` 类型层无 update/delete；`ConfigAuditEntry` 只含字段名与结果码。
- **审计写非事务耦合**：失败**不改变**保存结果，但发结构化 `WARN config_audit_write_failed`（字段白名单）。
- **凭据纪律**：未在任何文件 / 命令行 / 日志写入任何口令 / 令牌 / 密钥字面量；只登记**键名**（`IB_DEFINITION_DOC_PATH` / `IB_EXPERT_PROMPT_DIR` / `config_audit`）。
- **fail-closed / fail-safe 未削弱**：校验不通过 ⇒ 4xx 且在用配置不变；审计 / 存储态不可读 ⇒ 503（不返回空集冒充无记录，不静默当作文件态）。
- **测试阈值未削弱**：未把任何失败改为 `skip` / `xfail`。
- **只读约束**：未 `git add` / `commit` / `push` / `stage`；未部署；未触碰目标机；FreeArk 参考仓**只读**（未读未改）。

### 23.7 REV-16-4 回修增量（DEFECT-R16-4-01：审计写失败旁路自身抛 `NameError`；追加，不改写 §23.1~§23.6）

**调用 ID**：INV-GROUP_C-INTELBASE-017（`flow_mode: PARTIAL_FLOW`）　**触发**：GR-D-013 = **FAIL**（单一 MAJOR 缺陷，PM 独立确认）。

| 项 | 类型 | 结论 | 关键落点 |
|----|------|------|----------|
| DEFECT-R16-4-01 | 回归缺陷（MAJOR） | **DONE（已修复）** | `src/ibweb/composition.py::_warn_audit_write_failed`（`log_event` 改函数内局部导入 + 整段 `try/except` 兜底） |

**根因（模块级符号未定义）**：`_warn_audit_write_failed(project_id)`（L968）在**模块作用域**调用 `log_event(...)`，而 `log_event` 在 `composition.py` 中**仅**以**函数内局部导入**引入（L449 `_assemble`、L1130 `build_definition_store`），**不存在模块级 `log_event`** ⇒ 调用即 `NameError: name 'log_event' is not defined`。该函数的两个调用点（`record_config_audit` L960「审计存储为 `None`」/ L965「`store.record(entry)` 抛错」）均落在这条**审计旁路**上，故 `record_config_audit`（IFC-IB-360）**不再返回而抛 `NameError`**，逸出至保存路径 `src/ibweb/views.py::_put_definition_config`（无捕获）⇒ **已成功落盘**的保存被报 **500**、被拒保存（非法工具参数，应 400）亦被报 500 —— 违反 ADR-34 / IFC-IB-360「审计写失败**不改变**保存结果，但**不静默**（结构化 `WARN config_audit_write_failed`）」。

**修复（最小改动，零新增能力）** —— `src/ibweb/composition.py::_warn_audit_write_failed`：
1. `log_event` 改为**函数内局部导入**（与本文件 L449 / L1130 既有 `ib.observability` 局部导入约定一致）—— 消除 `NameError`；
2. 导入 + 打点**整段 `try/except Exception` 兜底** —— 使本函数**自身不可能抛异常**，从而 `record_config_audit` 真正兑现「**永不**向调用方抛异常」契约（审计旁路**永不反噬**保存结果）。

**语义零改**：logger 名仍 `config_audit`、事件仍 `config_audit_write_failed`、字段白名单仍 `project_id` / `error_code` / `level`（**不落任何配置取值 / 凭据**）。**签名零改**：`record_config_audit(entry, *, deps=None) -> None` 逐字未变；未改任何既有 IFC 编号 / 签名。**行为不变式**：成功保存即便审计写失败仍返回其正常成功码；非法参数保存仍返回 400。

**§23.7 自验证据（离线；命令可被第三方重跑）**

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -X utf8 -m pytest tests/integration/test_config_rev16_4_int.py -q` | **7 passed**（`test_TC_INT_147_..._DEFECT_R16_4_01` 由 **FAIL（NameError）→ PASS**；强制负例 `test_TC_INT_141_failed_save_is_failsafe_via_subsequent_get` 仍 PASS） | 0 |
| `python -X utf8 -m pytest tests/unit tests/integration tests/e2e -q` | **308 passed**（零回退） | 0 |
| `python -X utf8 src/scripts/selfcheck.py` | **50/50 通过** | 0 |
| `python -X utf8 -m compileall -q src` | 无输出 | 0 |
| 抗性取证（脚本内即验，不落文件） | 即便 `log_event` 自身抛错 / `log_event` 属性缺失，`record_config_audit` **均不抛**；WARN payload 键集 == `{stage, outcome, project_id, error_code, level}` | — |

**§23.7 冻结约束复核（回修面）**：未新增模块 / 端口 / 依赖；未改 IFC 编号 / 签名 / 字段集；`tests/**` **未触碰**（仅运行）；未 `git add` / `commit` / `push` / 部署；FreeArk 参考仓**只读**；无任何口令 / 令牌 / 密钥字面量。

---

## 24. REV-17 增量实现（提示词兜底层重定位：提示词文本移出定义文档 + 合并结果进 system 位 + 通用内置安全网；追加，不改写 §1~§23）

**设计侧口径**：`docs/module_design.md` **1.9.0/REV-17**（新增 §2.2.8 IFC-IB-364 / IFC-IB-365 + REV-17 文字修订索引）+ `docs/architecture_design.md` **1.9.0/REV-17**（新增 ADR-36、ADR-15-R2；明文修订 ADR-29 / ADR-31 / ADR-33；§2.0.8 R17 影响复核表）。**用户裁决**（2026-10-07，经三轮澄清）：用户请求原文「取消定义文档，仅仅使用 markdown 文件和兜底提示词。可视化配置文件可以对 markdown 进行 CRUD，加载，保存，生效」；七项拍板见 §24.1。

### 24.1 结论摘要（本轮范围三件事 + 七项用户裁决）

| 项 | 类型 | 结论 | 关键落点 |
|----|------|------|----------|
| 提示词文本移出定义文档 | 真源收窄（ADR-15-R2） | **DONE** | `ExpertSpecInput` 删 `fallback_prompt`；`_semantic_payload` / 可编辑白名单 / 校验项 5 同步；legacy 键分级处置 |
| 合并结果进 system 位 | 通道矫正（ADR-36） | **DONE** | `LlmProvider.build_expert(spec, *, system_prompt)`（IFC-IB-212）+ `orchestration` 传 `prompt or None`；假陈述 docstring 消解 |
| 通用内置安全网破死锁 | 结构性保证（IFC-IB-365） | **DONE** | `BUILTIN_FALLBACK_DEFAULT` + `builtin_fallback_for`；`validate_two_domains`（IFC-IB-364）保存期与装配期共用 |

**七项用户裁决**：①**只收窄**，不取消定义文档（继续承载专家元数据 / 路由 / 编排 / 工具授权）；②兜底层 = `fallback.md`（界面可编辑）为主 + 代码内置（**不可界面编辑**）为安全网；③生效口径**维持**「保存 + 服务重启重装配」（ADR-32），**不引热重载**；④**矫正通道** = 合并结果进 system 位，两层文件都缺才用代码内置；⑤**保存期一并校验提示词文件**；⑥**加通用内置安全网**破「界面新增专家」死锁；⑦按**正式修订 REV-17** 交付。

**合并语义（本轮定稿）**：`main.md` > `fallback.md` > 代码内置兜底；`resolved_from` 取值域 `{main_file, fallback_file, builtin_fallback}`（第三值由 `definition_doc_fallback` **更名**）。

### 24.2 模块实现计划（按拓扑顺序；REV-17 触及部分）

| 序号 | MOD-ID | 模块名 | 文件路径 | 依赖前置模块 | 复杂度 | 状态 |
|------|--------|--------|---------|------------|--------|------|
| 1 | MOD-IB-01 | 核心契约（端口与结构） | `src/ib/core/types.py`（`ExpertSpecInput` 删字段；`ExpertPromptBundle.resolved_from` 第三值更名）、`src/ib/core/ports.py`（`build_expert` 加 keyword-only `system_prompt`；`load_bundle` 形参更名） | — | M | DONE |
| 2 | MOD-IB-02 | 配置 / 定义文档数据层 | `src/ib/config/definition.py`（`_semantic_payload` / 白名单 / 校验项 5 / `document_from_json` legacy 分级处置；新增 `validate_two_domains` = IFC-IB-364）、`src/ib/config/prompts.py`（`merge_prompt_layers` 第三分支改 `builtin_fallback`；`validate_prompt_directory` 判据改为「无 `fallback.md` **且** 无内置兜底」） | MOD-IB-01 | L | DONE |
| 3 | MOD-IB-16 | 专家注册表与提示词安全网 | `src/ib/experts/__init__.py`（`_BUILTIN_FALLBACK_PROMPTS` / `BUILTIN_FALLBACK_DEFAULT` / `builtin_fallback_for` / `builtin_fallbacks_for` / `BUILTIN_FALLBACKS` = IFC-IB-365；`__all__` 同步） | MOD-IB-01 | M | DONE |
| 4 | MOD-IB-20 | LLM 提供方 | `src/ib/llm/__init__.py`（`build_expert` 生效口径 = 非空 `system_prompt` 否则 `spec.fallback_prompt`；`FakeLlmProvider` 同步；`_client` docstring 补「`system_prompt` 只允许是装配期常量」硬规则） | MOD-IB-01 | M | DONE |
| 5 | MOD-IB-22 | 编排 | `src/ib/orchestration/__init__.py`（`_run_expert` 传 `system_prompt=prompt or None`、human 位只留用户问题；`_prompt_of` 注释改口径） | MOD-IB-20 | M | DONE |
| 6 | MOD-IB-23 | Web / 组合根 / 端点 | `src/ibweb/composition.py`（`_assemble` 取一次内置兜底映射传下游；`admit_two_domains` 改调 `validate_two_domains`；`_default_definition_document` 删直抄；`_inject_derived_experts` 改注入）、`src/ibweb/views.py`（`_put_definition_config` 改调 `validate_two_domains` 且校验 `submitted`；refs 取用失败映射 503；删 `_doc_fallback_of`）、`src/ibweb/serializers.py`（删字段） | MOD-IB-02 / 16 / 22 | L | DONE |
| 7 | MOD-IB-24 | 前端（配置页 / 客户端） | `src/frontend/src/api/client.ts`（`ExpertSpecInput` 删字段；新增只读 `builtin_fallback`）、`src/frontend/src/views/ConfigPage.vue`（`addExpert()` 删默认值；定义文档兜底 textarea 改**只读回显**；`resolvedFrom()` 第三值同步） | MOD-IB-23 | M | DONE |
| 8 | MOD-IB-25 | 部署交付物 | **NO_CHANGE**（零新增迁移、零新增依赖、`schema_version` **不 bump**） | — | S | NO_CHANGE |

### 24.3 逐项落地要点

1. **删字段的连锁落点（唯一会当场断掉的地方）**：`ExpertSpecInput.fallback_prompt` 删除后，`_inject_derived_experts` 的 `ExpertSpec(..., fallback_prompt=...)` 是**唯一**构造 `ExpertSpec` 时从输入取该值的落点 —— 改为 `builtin_fallback_for(e.name)`。`ExpertSpec.fallback_prompt` **必须原样保留**：`_prompt_of` / `build_expert` 的回落分支 / `IFC-IB-175 fallback_prompts()` 都锚在它上面，且 `tests/unit/test_prompt_tool_config_unit_r16d.py` 有一条「所有 `EXPERT_SPECS` 的兜底非空」的断言正是该字段必须存在的验证点。
2. **内置兜底映射必须由 `_DEFAULT_SPECS` 派生，绝不能取 `EXPERT_SPECS`**：`install_derived` 是 **rebind 全局名**，而 `build_deps(force=True)` 只重建 `_DEPS`、**不回滚** `ib.experts.EXPERT_SPECS`（进程级单例，在测试里是常态）。若在装配期取一次 `EXPERT_SPECS`，第二次装配即漂移。
3. **分层纪律**：`ib.config` 只允许 import stdlib + `ib.core` —— **不得** import `ib.experts`。内置兜底一律经**参数注入**（`builtin_fallback=` / `builtin_fallbacks=`），只有 `ibweb` 直接调用 `ib.experts`。
4. **`system_prompt` 必须传 `prompt or None`，不是可选优化**：`_make_langchain_client` 在 `system_prompt` 为 falsy 时返回**裸 client**；裸 client **没有 `run_tool_loop`**，`_run_expert` 的 `getattr` 取不到便掉进单次 `invoke` —— 结果是**同时失去 system 消息与 function-calling，且不报错**。
5. **`_clients` 是无界 dict**（键含 `system_prompt`），故 `system_prompt` **只允许是装配期常量**（ADR-36 硬规则）。本轮的生效提示词来自装配期合并视图，满足该不变式；缓存上界 = 专家数 + 3（新用例断言）。
6. **`resolved_from` 第三值更名**：`definition_doc_fallback` → `builtin_fallback`。契约面同步处 = `types.py` 的 `Literal` 与 docstring、`prompts.py` 的合并分支、`ConfigPage.vue` 的 `resolvedFrom()` / `RESOLVED_LABEL`、`selfcheck.py` 与 `tests/**` 的取值断言。
7. **legacy 键分级处置（真正的信息损失必须 fail-closed）**：`document_from_json` 读到旧文档的 `experts[].fallback_prompt` 时 —— 与 `builtin_fallback_for(name)` **逐字相同** → 静默丢弃（零信息损失；生产种子文档正是这一支，因其值本就是 `spec.fallback_prompt` 直抄）；**不同** → 抛 `ConfigError`，指明路径与迁移目标（`<root>/<project_id>/<name>/fallback.md`），**只报长度、不回显正文**。「本次丢弃了 N 处」这类提示**只能**走既有的 `/api/config/storage-state`（ADR-35 的提示面），**绝不**加到 definition 的 GET / PUT 响应上。
8. **`prompt_fallback_missing`（IFC-IB-345 第三类错误）语义收窄**：因「兜底恒非空」已由**结构**保证（`BUILTIN_FALLBACKS` 是**全函数**），该错误在正常配置下**不再触发**，降级为「注入的内置兜底映射残缺」的防御性断言。已在 `module_design.md` §2.2.6 / §2.2.8 登记。
9. **为保持两条红线，内置兜底走「下级只读字段」而非顶层键**：`/api/config/definition` 的 GET / PUT 响应顶层仍**恰 4 键**（`selfcheck.py` 断言）；`/api/config/prompts` 顶层仍**恰 5 键**（`tests/integration/test_prompt_config_r16.py` 断言）。可读性需求由 `experts[].builtin_fallback` 满足 —— **只读展示，不开第二写入口**（写入口只有 `main` / `fallback` 两层文件）。
10. **死锁为何被破**：旧口径下 `PUT definition` 要求非空兜底、而 `PUT prompts/<新专家>/fallback` 又因「专家未登记」404（`_put_prompt_layer` 前置查登记）⇒ 界面新增专家**无解**。`BUILTIN_FALLBACK_DEFAULT` 使新专家的兜底**必然有值**，两条路同时打开；而**越域防护未被顺手放开**（新增用例反证：孤儿提示词文件仍被 `prompt_orphan_file` 拒绝）。

### 24.4 架构偏差记录（REV-17）

| 编号 | 偏差 | 性质 | 处置 |
|------|------|------|------|
| D-R17-01 | `content_hash` 口径变化导致**既有定义文档的哈希一次性全变**（`_semantic_payload` 少一个键） | 预期内、已登记 | 不影响正确性（哈希是自洽的乐观锁）；运维面影响 = 开着配置页的旧会话首次保存可能得 **409**，前端已有处理（`ConfigPage.vue`）；已登记于交付注意 |
| D-R17-02 | `prompt_fallback_missing` 在正常配置下不可达（语义收窄为防御性断言） | 设计侧已声明 | 见 `module_design.md` §2.2.8；**不删该错误码**（保留为防御） |
| D-R17-03 | 代码内置兜底可被界面**看到**（只读字段）但**不可编辑** | 用户裁决 ② 的直接后果 | 设计侧 ADR-36 已写明「只读展示，非写入口」；新增用例断言写入口仍只有两层 |

**未采纳的备选（记录以免复评）**：不取消定义文档（用户裁决 ①）；不引运行期热重载（ADR-32 / OOS-16）；不让 `general` / 无专家路径的人格串可配置（既有不对称事实，登记为 `architecture_design.md` §10.1 OPEN ITEM，**不顺手扩围**）；**不 bump `schema_version`**（无迁移机制；bump 会让所有 v1 文档在 `load()` 阶段硬失败 → 服务起不来），改为靠 legacy 键分级处置兜底。

### 24.5 REV-17 自验证据（离线；命令可被第三方重跑）

| 命令 | 结果 | EXIT |
|------|------|------|
| `python -X utf8 -m pytest tests/unit tests/integration tests/e2e -q` | **327 passed**（unit **149** / integration **154** / e2e 24；零 skip 零 xfail）；相对 REV-16-4 基线 **308** 零回归（+19 = 新增 unit 13 + integration 6） | 0 |
| `python -X utf8 -m pytest tests/unit/test_prompt_system_slot_r17.py -q` | **13 passed**（system 位真的生效 / 空白与空串回落 / 内置兜底全覆盖 / legacy 键分级处置 / `_clients` 上界） | 0 |
| `python -X utf8 -m pytest tests/integration/test_prompt_config_r17_int.py -q` | **6 passed**（保存期与装配期**同序同条** / fail-safe 不半写 / 新专家死锁已破 / 孤儿仍拒 / 顶层键集不变 / 写入口仍只有两层） | 0 |
| `python -X utf8 src/scripts/selfcheck.py` | **51/51 通过**（REV-16-4 为 50/50；新增 `r17_build_expert_system_slot`） | 0 |
| `cd src/frontend && npm run typecheck` | 无输出 | 0 |
| `cd src/frontend && npm test` | **29 passed**（REV-16-4 为 28；新增 REV-17 用例） | 0 |
| `cd src/frontend && npm run build` | `✓ built`（`vue-tsc --noEmit` 已随 `typecheck` 单独跑过） | 0 |

**行为等价性论证（关键一条）**：生产种子文档的 `experts[].fallback_prompt` 本就是 `spec.fallback_prompt` **直抄**（旧 `composition.py::_default_definition_document`），故删字段后**生效提示词文本零变化**；变化的只有 `resolved_from` 的**取值名**（`definition_doc_fallback` → `builtin_fallback`）与随之同步的界面标签文案。

### 24.6 冻结约束复核（REV-17）

未新增模块（仍 26）/ 未改端口数（仍 17）/ 未新增第三方依赖 / 未改模块边界 / 未改依赖边（DAG 不变）/ 未改配置键名与默认值 / **未 bump `schema_version`** / 未改 `IFC-IB-001~363` 中除已登记 10 条口径外的任何编号与签名名 / 未改任何既有 ADR 正文（ADR-15 与 ADR-15-R1 **一字未动**，收窄全落 ADR-15-R2；ADR-29 / ADR-31 / ADR-33 的改动均带**明文 REV-17 修订标记**，非静默改写）/ 未 commit / 未 push / 未 deploy / FreeArk 参考仓**只读** / 无任何口令、令牌或密钥字面量。
