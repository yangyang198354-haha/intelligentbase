<file_header>
  <project>intelligentbase</project>
  <artifact>architecture_design</artifact>
  <path>docs/architecture_design.md</path>
  <doc_id>ARCH-INTELBASE-001</doc_id>
  <version>1.10.2</version>
  <revision>REV-18-R2</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_03 系统架构设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-10-07</updated_at>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <readonly_reference path="FreeArk 仓库" note="只读参考；本阶段未修改 FreeArk 任何文件"/>
  </inputs>
  <locked_decisions source="requirements_spec.md §6.0">DR-01 Qdrant 单实例非容器 | DR-02 bge-m3 稠密本地 | DR-03 禁 Docker 全裸装 | DR-04 云端 DeepSeek 可配置 | DR-05 千级文档量级 CPU-only 假设 | DR-06 单实例多项目 | DR-07 须支持索引重建 | DR-08 v1 纳入 OCR</locked_decisions>
  <revision_history>
    <rev version="1.0.0" date="2026-09-25" note="初稿（GROUP_B 首次提交，PM 门控前）"/>
    <rev version="1.1.0" revision="R1" date="2026-09-25" note="按 PM 架构复核反馈 REV-01 修订：① 后端 Web 框架 FastAPI → Django（+DRF）（用户明确指定，非建议），前端 Vue 3 + Vite 不变；② 流式载体改为 Django 同步视图 + StreamingHttpResponse 原生 SSE（text/event-stream），不引 Channels、不引 Redis；③ 新增 §2.0「框架切换影响复核表」，对 ADR-01~13 共 13 条逐条复核（受影响 5 条：ADR-03/07/08/11/13；不受影响 8 条）；④ ADR-11 全文重写为 ADR-11-R1（评估 A/B/C 三方案，量化升级触发条件，Option C 拒绝），两个 FreeArk 真实坑（?token= 入访问日志、channels_redis × redis-py 不兼容）写成强制实施约束；⑤ ADR-01 端口方法数更正为 11（IFC-IB-100~110，以 module_design.md 为权威）；ADR-03/07/08/13 各追加 -R1 修订节，ADR-02/04/05/06/09/10/12 逐条写入「经检查，不受框架切换影响」；⑥ ARCH-ASSUMPTION-A2 关闭（已确认=软隔离）、OQ-IB-01 关闭（原文件保留 ON）、A4 保持 TBD；⑦ 新增 [TBD-T15]（SSE 并发上限）；§10.2 许可台账补登 Django/DRF/Waitress/Gunicorn。不变约束：模块数 25、端口 13、IFC-IB 编号 58 个使用中全部不变（仅改载体说明）、DAG 无环、覆盖 24/24 REQ-FUNC + 14 NFR。需求侧文档与 FreeArk 仓库未改动。"/>
    <rev version="1.2.0" revision="R2" date="2026-09-26" invocation_id="INV-GROUP_B-INTELBASE-004" note="R2 补交（L-03：ib-embed 服务端无模块归属与契约）：① 追加 ADR-02-R2 附注——ib-embed 的服务端归属成立（MOD-IB-26，补齐既有 Option B 决策的落点，Decision/Options/Consequences 未改）、冷/热双路径单一落点在客户端、形态可逆值域显式化为 http|inproc|fake；并随附登记「错误码语义映射不变式」（4xx/409=重试无用，5xx=重试可能有用）；② 新增 §2.0.1 R2 影响复核表（ADR-01~13 逐条：ADR-02 受影响（仅补附注）、其余 12 条 R2 不受影响），并为 ADR-04/06/11/13 追加 inline R2 复核句；③ §9 TBD 清单补 [TBD-T16]（ib-embed 并发与线程校准）与 [TBD-T18]（目标机 CPU 指令集 AVX2 基线实测），并声明 [TBD-T17] 为预留未分配；④ §10.3 自检追加 R2 行。不变约束：模块数 25→26（仅追加）、端口 13、IFC-IB 001~265 一字不动（新增 266~284/286）、DAG 无环、覆盖 24/24 REQ-FUNC + 14 NFR。需求侧文档与 FreeArk 仓库未改动。"/>
    <rev version="1.3.0" revision="R7" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-005" note="R7 增量贯通（GROUP_A REV-06 裁决：诉求③ UI 可视化配置纳入 v1，新增 REQ-FUNC-IB-25/26/27）：① 新增 ADR-14（可视化配置的编辑模型 = 定义文档唯一真源 + 显式 round-trip，视图零持久化）、ADR-15（定义文档单一真源（双向同源）与只读派生视图）、ADR-16（装配期完备性校验 + fail-fast 准入闸门，无强制继续开关），每条含 ≥2 方案与已评估未采纳留痕；ADR 数 13 → 16；② 新增 §2.0.2 R7 影响复核表（ADR-01~16 逐条：既有 13 条在 R7 下均不受影响、新增 3 条），§2.0 / §2.0.1 保留为 R1 / R2 历史复核；③ 新增第 14 个端口 DefinitionDocumentStore（IFC-IB-287，定义于 MOD-IB-01 的零依赖 frozen dataclass / Protocol 层），§1.3 可替换点增一行；④ §6 增补「图编译输入 = 经准入闸门校验通过的定义文档；拓扑不可编辑」；⑤ §8 新增 [ARCH-ASSUMPTION-A6]（定义文档物理载体 = 本地文件，一项目一文档）与 [ARCH-ASSUMPTION-A7]（可视化落地的前置条件 = IB-01/IB-02 定义外置；REV-07-6 判定 (a) 可登记前置/风险，不阻断）；⑥ §9 新增 [TBD-T19]（装配期装载/校验/派生耗时）与 [TBD-T20]（前端图渲染规模上界）；⑦ 计数同步：REQ-FUNC 24/24 → 27/27（REV-07-3，仅需求计数语境；端口 13 → 14）；⑧ 需求侧文档与 FreeArk 仓库未改动；未写入任何凭据值。"/>
    <rev version="1.4.0" revision="R8" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-006" note="R8 增量贯通（GROUP_A REV-11-1：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）：① 新增 ADR-17（「可选手动确认中间态」的承载方式与状态丢失语义；3 候选方案，Option B 选定），ADR 数 16 → 17；② 新增 §2.0.3 R8 影响复核表（ADR-01~17 逐条：既有 16 条在 R8 下均不受影响——其中 ADR-09 判『不受影响，且 R8 是其应用』、ADR-11 判『不受影响，R8 复用其载体』；新增 1 条；无一条跳过）；③ §1.3 可替换点表追加 R8 注（SessionStore 值域扩展 memory 或 external、恢复准入路径、状态丢失 fail-closed）；④ §6 增补『（R8）流式与会话的四条规范化补充』（增量推送与终态单发 / 完成附结构化产物 / 思考分区默认不启用且内部产物永不外流 / 会话状态与确认中间态）；⑤ §8 新增 [ARCH-ASSUMPTION-A8]（v1 默认持久化策略 = 进程内）；⑥ §9 新增 [TBD-T21]（会话状态容量与恢复并发）；⑦ §10.1 新增 OQ-IB-07 / OQ-IB-08 架构默认取值落地行、§10.3 追加 R8 自检。不变约束：模块数 26、端口数 14、IFC-IB-001~297 一字不动（新增 298~308）、§4.1 依赖边逐行不变（零新增边）、DAG 无环、覆盖 27/27 REQ-FUNC + 14 NFR、tech_stack.md 未改（无新第三方依赖）。需求侧文档与 FreeArk 仓库未改动；未写入任何凭据值。"/>
    <rev version="1.5.0" revision="REV-13" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-007" note="REV-13 认证与商用界面增量贯通（GROUP_A REV-13 下游）：① 新增 ADR-18 ~ ADR-27（账户/会话落点与载体、不透明服务端会话令牌（无 Cookie）、bcrypt 口令存储与首登强制改密、账户↔项目 1:1 绑定、与既有 AuthzPolicy 端口协作（单一授权真源 / 生产 fail-closed）、前端重构与路由（Element Plus + vue-router hash）、粘贴令牌入口废除、HTTPS 落点、迁移/种子/回滚、登录失败限速与审计（条件性）），每条 ≥2 方案；ADR 数 17 → 27；② 新增 §2.0.4 R13 影响复核表（既有 17 条 ADR 逐条：全部不受影响——其中 ADR-07 / ADR-11 / ADR-16 判『不受影响且 R13 复用其纪律/机制』；新增 10 条；无一条跳过）；③ 新增第 15 个端口 AccountStore（IFC-IB-310，定义于 MOD-IB-01 零依赖 Protocol 层；14 → 15，纯追加）；④ 新增 IFC-IB-309 ~ IFC-IB-332（24 条类型化契约；IFC-IB-001~308 一字不动，IFC-IB-285 仍预留）；⑤ §1.3 追加 R13 注、§8 新增 [ARCH-ASSUMPTION-A9]、§9 新增 [TBD-T22] / [TBD-T23]、§10.1/§10.2/§10.3 追加 R13 行；⑥ 落点并入既有模块（零新增模块、零新增依赖边）；⑦ 计数同步：REQ-FUNC 27/27 → 36/36（新增 IB-28~36）、NFR 14 → 18（新增 NFR-15~18）。不变约束：模块数 26、IFC-IB-001~308 一字不动、§4.1 依赖边逐行不变（零新增边）、DAG 无环。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.6.0" revision="REV-14" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-008" note="REV-14 回归缺陷修复（R13 引入：全局管理员因前端从不下发 X-IB-Project 且无项目枚举端点，无法使用任一项目级页面）：① 新增 ADR-28「项目上下文的选择与传播」（4 候选方案：服务端隐式默认 / 显式选择+显式传播 / 全局哨兵解析为并集(拒) / 部署期绑定 admin(拒)；Option B 选定并吸收 Option A 的『单项目预选』便利），ADR 数 27 → 28；② 新增 §2.0.5 R14 影响复核表（既有 27 条 ADR 逐条复核，无一条跳过；ADR-04 判『不受影响且 R14 是其应用』、ADR-11 判『不受影响，R14 复用其纪律』；新增 1 条）；③ 新增 IFC-IB-333 ~ 336（项目枚举端点 / X-IB-Project 头契约（加成式扩展 IFC-IB-324，其文本不动）/ 前端 projectContext store / client.ts 单一注入点）；④ §10.1 新增 R14 OPEN ITEM（项目选择 UX 与项目枚举端点无独立 REQ/AC，登记不发明）、§10.3 追加 R14 自检；⑤ 落点并入既有模块 MOD-IB-23 / MOD-IB-24（零新增模块、零新增依赖边）。不变约束：模块数 26、端口数 15、既有 IFC-IB-001~332 一字不动（新增 333~336）、§4.1 依赖边逐行不变、DAG 无环、fail-closed 纪律不削弱（未选项目即不泄露）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.7.0" revision="REV-16-2" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-009" note="REV-16-2 提示词与工具可视化配置增强（GROUP_A REV-16-2 下游贯通：REQ-FUNC-IB-37~42 / REQ-NFR-IB-19 / C-IB-39 / C-IB-40 / OQ-IB-24）：① 对既有 ADR-15 作**正式修订**（新增修订子节 **ADR-15-R1**，ADR-15 正文与 Status **一字不动**；supersede vs amend 裁定见包 §5.1）；② 新增 **ADR-29**（提示词主 / 兜底分层与回退）、**ADR-30**（工具授权勾选 + 工具参数可配，不新增工具本体）、**ADR-31**（FreeArk 严格对齐含专家名 + 改名与聚合禁止标签处置）、**ADR-32**（配置生效口径 = 保存 + 服务重启重装配，不引运行期热重载 / 不重编译图）；ADR 数 28 → 32；③ 新增 §2.0.6 R16-2 影响复核表（既有 28 条 ADR 逐条复核，无一条跳过；ADR-15 判『经 ADR-15-R1 修订』、ADR-14 / ADR-16 判『复用其机制』；新增 4 条）；④ 新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339，定义于 MOD-IB-01 零依赖 Protocol 层）；⑤ 新增 **IFC-IB-337 ~ IFC-IB-354**（18 条类型化契约；IFC-IB-001~336 一字不动，IFC-IB-285 仍预留）；⑥ §1.3 追加 R16-2 注、§8 新增 [ARCH-ASSUMPTION-A10]、§9 新增 [TBD-T24]、§10.1 / §10.2 / §10.3 追加 R16-2 行；⑦ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑧ 计数同步：REQ-FUNC 36/36 → **42/42**（新增 IB-37~42）、NFR 18 → **19**（新增 NFR-19）。不变约束：模块数 26、端口数 15 → 16（纯追加）、IFC-IB-001~336 一字不动、§4.1 依赖边逐行不变、DAG 无环、fail-closed 纪律不削弱、**不重编译编排图**（C-IB-40）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.7.1" revision="REV-16-3" date="2026-10-06" basis="用户 / 协调者裁决：REV-16-3 措辞收敛（真源分域口径）+ [ARCH-ASSUMPTION-A10] 确认；由 PM 机械落盘（无新 producer 调用）" note="REV-16-3 措辞收敛 + A10 确认（append-only，不改既有结论）：① **措辞收敛（真源分域口径）** —— 将 §8 [ARCH-ASSUMPTION-A7] 中「已外置为数据、且为单一真源」按**分域**口径收敛为「真源按域唯一」（结构与配置域 = 定义文档；提示词域 = 独立 markdown 目录）；ADR-15 正文（§2 内 L607-628）**一字不动**，修订只落在 ADR-15-R1 与下游措辞（回链 requirements_spec.md C-IB-41 / C-IB-39）。② **[ARCH-ASSUMPTION-A10] 转为已确认决策** —— 独立提示词目录物理布局定为 `&lt;root&gt;/&lt;project_id&gt;/` 一项目一目录树、每专家一子目录（目录名 = 专家 name，即 ADR-15-R1 合并键的物理实现）、`main.md` 可缺 / `fallback.md` 不得缺；并登记 P-2 边界约束（FreeArk 业务名称仅存在于 demo，通用种子不得携带业务名；对齐限于定义元数据 + 工具名映射）与 P-3 发布说明（硬改名、无并存窗口；升级后基于文件的定义文档须用新专家名；AGGREGATION_FORBIDDEN_LABELS 迁移态取旧 ∪ 新）。**铁律**：模块数 26、端口 16、§4.1 依赖边逐行不变、DAG 无环、IFC-IB-001~354 编号 / 签名一字不改、不新增 REQ、不改 AC、ADR-15 正文一字不动。`&lt;inputs&gt;` 指针同步指向 requirements_spec.md 1.7.0/REV-16-3。需求侧与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.8.0" revision="REV-16-4" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-010" note="REV-16-4 设计增量（回归缺陷修复轮 GROUP_B；DEFECT-R16-02 / GAP-R16-03 / GAP-R16-04）：① 新增 ADR-33（保存期工具参数 / 跨域完备性校验的落点 = MOD-IB-02 合成纯函数 validate_definition_full，IFC-IB-355；保存路径与装配路径共用的单校验入口，结构性消除两路径发散根因；不改任何既有 IFC 签名）；② 新增 ADR-34（配置保存 / 生效的可查询记录载体 = 同一 SQLite 新表 config_audit + 手写迁移 004_config_audit.sql + 只读审计端口 ConfigAuditStore（IFC-IB-357，第 17 个端口）+ 查询端点 GET /api/config/audit（IFC-IB-359）；成功与失败均记录；审计写失败与保存结果解耦且不静默；端口方法集在类型层排除写回配置，坐实只读审计非第二真源）；③ 新增 ADR-35（内存态生效提示的暴露 = 只读端点 GET /api/config/storage-state（IFC-IB-362）+ 类型化 StorageState（IFC-IB-361）；不改变 REV-FUNC-IB-40 生效口径，沿用 OOS-16 / C-IB-40）；ADR 数 32 → 35；④ 新增 §2.0.7 R16-4 影响复核表（既有 32 条 ADR 逐条复核，无一条跳过；ADR-16 判 不受影响且 R16-4 是其应用，ADR-32 判 不受影响且 R16-4 是其提示面补足；新增 3 条）；⑤ 新增第 17 个端口 ConfigAuditStore（IFC-IB-357；端口 16 → 17，纯追加）；⑥ 新增 IFC-IB-355 ~ IFC-IB-363（9 条类型化契约；IFC-IB-001 ~ 354 一字不动，IFC-IB-285 仍预留未分配，既有重号 IFC-IB-131 登记不修）；⑦ §1.3 追加 R16-4 注、§8 新增 ARCH-ASSUMPTION-A11、§9 新增 TBD-T25、§10.1 新增 OPEN ITEM、§10.2 追加 R16-4 说明、§10.3 追加 R16-4 自检；⑧ 落点并入既有模块（零新增模块、零新增依赖边）。不变约束：模块数 26、端口 16 → 17（纯追加）、IFC-IB-001 ~ 354 一字不动、§4.1 依赖边逐行不变、DAG 无环、fail-closed 纪律不削弱、不重编译编排图（C-IB-40）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.9.0" revision="REV-17" date="2026-10-07" invocation_id="INV-GROUP_B-INTELBASE-011" basis="用户裁决（2026-10-07）：「取消定义文档（承载提示词），仅仅使用 markdown 文件和兜底提示词。可视化配置可以对 markdown 进行 CRUD、加载、保存、生效」+ 协调者裁决 REV-17 按**正式修订**交付（本仓纪律「编号只增不改」）" note="REV-17 提示词兜底层重定位（把提示词文本彻底移出定义文档）：① 新增 **ADR-36**（提示词兜底层重定位：提示词文本唯一可写载体 = 目录 `main.md` / `fallback.md` 两层文件；代码内置兜底 = 不可界面编辑的安全网；定义文档交出提示词文本、回归纯结构配置；4 候选方案，3 项已评估未采纳）；② 新增 **ADR-15-R2**（对 ADR-15 的**第二次**正式修订子节，**收窄** ADR-15-R1 规则 ⑤ 的**兜底层载体**：由「定义文档 `fallback_prompt` 字段」改为「代码内置兜底」；**ADR-15 与 ADR-15-R1 正文一字不动**，其余六条规则结论不变）；③ 修订 **ADR-29**（`resolved_from` 第三值 `definition_doc_fallback` → `builtin_fallback`；「兜底恒非空」由**结构**保证而非校验放行）与 **ADR-33**（单一校验入口上提为 `validate_two_domains`，范围**含提示词域**，保存路径 ≡ 装配路径逐条同序同码）；④ 新增 **§2.0.8 R17 影响复核表**（**既有 35 条 ADR 逐条复核，无一条跳过**；ADR-15 判「经 ADR-15-R2 修订」、ADR-29 / ADR-33 各判「经 R17 修订」、ADR-31 判「不受影响，第 5 行口径澄清」；**新增 1 条**；ADR 数 **35 → 36**）；⑤ 新增 **IFC-IB-364**（`validate_two_domains`）与 **IFC-IB-365**（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `builtin_fallback_for` / `builtin_fallbacks_for`）；**被修订的既有 IFC 逐条登记**（IFC-IB-212 / 287 / 290 / 292 / 338 / 339 / 343 / 345 / 347 / 355，**只改文字与取值口径，号 / 名 / 签名一字不动**）；⑥ §8 修订 **[ARCH-ASSUMPTION-A10]**（`fallback.md` **不得缺 → 亦可缺**）；§10.1 新增 **OPEN ITEM**（`general` / 无专家路径的人格串为代码内置且不可配置 —— **既有不对称事实，只登记不修复**）；§10.3 追加 R17 自检 11 行；⑦ **两条待写入交付说明的运维事实**：**一次性 `content_hash` 变更**（所有既有定义文档哈希变一次；开着配置页未刷新的会话首次保存可能收 `409`，前端已按 AC-IB-17-03 处理）、**legacy 键两级处置与迁移步骤**（与内置逐字相同 → 静默丢弃；不同 → fail-closed 抛 `ConfigError` 并指明迁移目标 `&lt;root&gt;/&lt;project_id&gt;/&lt;name&gt;/fallback.md`，只报长度不回显正文）。⑧ **同批矫正一处运行期缺陷**：配置页编辑的提示词**从未进入 system 消息**（被拼进 human 前缀），`build_expert` 声称存在 `system_prompt` 覆盖形参而实际不存在的**假陈述 docstring** 随之消解（IFC-IB-212 真实落地；`_run_expert` 传 `prompt or None` —— 空串会致裸客户端、**同时静默失去** system 消息与 function-calling）。不变约束：模块数 26、**端口数 17（未新增）**、§4.1 依赖边逐行不变（零新增边）、DAG 无环、`IFC-IB-001 ~ 363` 号 / 名 / 签名一字不动、REQ→MOD 覆盖不变（42/42 REQ-FUNC + 19 NFR）、**不 bump schema_version**、不新增 REQ / 不改 AC、**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）。`&lt;inputs&gt;` 指针不变（requirements_spec.md 1.7.0 / REV-16-3；需求侧落盘载体措辞的同步**另立交付项**）。FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.10.0" revision="REV-18" date="2026-10-07" invocation_id="INV-GROUP_B-INTELBASE-012" basis="用户裁决（2026-10-07，REV-18-2）：OQ-IB-25 ~ OQ-IB-31 七条一次性拍板并登记 DR-21（Key 存 DB + 重启生效 / Key 全局唯一 / 删项目=软删停用 / 账号沿用现状 / 禁删 admin 与最后管理员 + 二次确认 / kb 由项目推导 / 父级「系统管理」+三子项）；上游 requirements_spec.md 1.10.0（REV-18-2）/ user_stories.md 1.10.0（REV-18-2）" note="REV-18 下游贯通（系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）：① 新增 **ADR-37**（项目注册表承载与软删语义）、**ADR-38**（LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析）、**ADR-39**（LLM 未配置态启动 / 运行期语义，破除首启死锁）、**ADR-40**（运维账号 CRUD 扩展 / 顺序依赖 / 删除保护）、**ADR-41**（项目域 `kb_id` 推导 + 保留归属断言 + kb_default 迁移）、**ADR-42**（系统管理三分 IA + 服务端授权与导航解耦）；每条含 Context（REQ 引用）/ Options（≥2，含已评估未采纳）/ Decision / Status / Consequences；**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：32 条不受影响、3 条口径补注（ADR-08 / 18 / 28）、1 条待裁决口径张力（ADR-21，登记 OPEN ITEM）、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 追加 R18 增补段与 2 行；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**、§9 新增 **[TBD-T26] / [TBD-T27]**、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）、§10.2 追加「许可面未变」句、§10.3 追加 R18 自检；⑥ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。不变约束：模块数 26、端口 17 → 19（纯追加）、`IFC-IB-001 ~ 365` 号 / 名 / 签名一字不动（仅 4 条文字口径修订，登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增边）**、DAG 无环、**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）。**登记：生产后端重启与首次环境变量配置须由用户执行**（架构 / 部署文档只写「由用户执行」的动作）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
    <rev version="1.10.1" revision="REV-18-R1" date="2026-10-07" basis="用户裁决（2026-10-07）：GR-B 三项待决收口 —— OI-1 出 ADR-21-R1（N:1，amend）；OI-2 采纳 ADR-39 Option C；OI-3 保持 OPEN" note="REV-18-R1 裁决收口（状态登记 + amend 子节，无结构变更）：① 新增 **ADR-21-R1**（对 ADR-21 的正式修订子节，**amend**；**ADR-21 正文一字不动**）—— 把「账户↔项目绑定」关系式**收窄 / 订正为 N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），承接 **OI-1**（依据 OQ-IB-28 / DR-15 / ADR-21）；**零迁移**（不加 `users.project_id` 唯一约束），授权落点与端口结论不变。② §2.0.9 影响复核表 ADR-21 行由「待裁决（口径张力）」改为「口径补注（已由 ADR-21-R1 承接）」；**结论计数 32 / 3 / 1 / 6 → 32 / 4 / 0 / 6**。③ §10.1：**OI-1 CLOSED**（经 ADR-21-R1）、**OI-2 CLOSED**（采纳 **ADR-39 Option C**，缺 Key 非致命、fail-closed 于调用期，其余必填仍 fail-fast；备选 Option B 已评估未采纳）、**OI-3 保持 OPEN**（施工期定，不阻塞）。④ ADR-39 Consequences 补记「Option B 已评估未采纳 / 采纳 Option C」；§10.3 自检同步。**不变约束**：ADR 数 42、模块数 26、端口 19、`IFC-IB-001 ~ 377` 号 / 名 / 签名一字不动、§4.1 依赖边逐行不变、DAG 无环、**不新增 REQ / 不改 AC**、**不新增 / 不删 ADR 编号**。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / Key / 证书字面量（只登记键名 / 表名 / 文件名 / 字段名）。"/>
    <rev version="1.10.2" revision="REV-18-R2" date="2026-10-07" basis="协调者复核（2026-10-07）：GR-B 落档复核后三处「现在时未决」措辞收尾；由 PM 机械落盘（无新 producer 调用）" note="REV-18-R2 一致性措辞收尾（无结构变更；只把与已关闭 OI 冲突的现时态陈述改为已决，供 software-developer 照已决实现）：① **ADR-40 ③** 注句由「与 ADR-21 的 1:1 表述存在口径张力，登记为 OPEN ITEM OI-1，本 ADR 不自行改写 ADR-21」改为「口径张力已由 **ADR-21-R1**（amend 子节）承接、关系式订正为 **N:1**、**OI-1 已由用户裁决于 2026-10-07 关闭**；**ADR-21 正文一字未动**」；② **[ARCH-ASSUMPTION-A12]** 末两列由「若 PM / 用户不采纳『未配置态』，须以部署期由用户手工预置 Key 替代（ADR-39 Option B）…／需 PM 知悉（OI-2 / OI-3）」改为「**用户裁决 2026-10-07 已采纳『未配置态』（ADR-39 Option C）**、Option B **已评估未采纳** …／**已决**：**OI-2 已关闭**、**OI-3 保持 OPEN**（施工期定，不阻塞）」—— **架构侧取值列（①…③）的既有取值一字未动**，**未新增假设项**。**不变约束**：ADR 数 42、模块数 26、端口 19、`IFC-IB-001 ~ 377` 号 / 名 / 签名一字不动、§4.1 依赖边逐行不变、DAG 无环、**不新增 REQ / 不改 AC**、**ADR-21 正文一字不动**。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / Key / 证书字面量（只登记键名 / 表名 / 文件名 / 字段名）。"/>
  </revision_history>
  <scope_boundary>只做架构与模块设计；不含实现代码、测试用例、部署脚本。允许接口签名、类型注解、数据结构定义。</scope_boundary>
</file_header>

# 系统架构设计 — intelligentbase 通用 RAG + 多智能体可复用基础架构

**版本**: 1.10.2（REV-18-R2 修订）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-07
**R2 修订摘要（L-03：`ib-embed` 服务端无模块归属与完整契约）**: 追加 **ADR-02-R2 附注**（服务端归属成立 = 新增 MOD-IB-26；冷/热单一落点在客户端；形态可逆值域 `http|inproc|fake`），新增 **§2.0.1 R2 影响复核表**（**受影响 1 条：ADR-02（仅补附注）**；**R2 不受影响 12 条**：ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13），并为 ADR-04 / 06 / 11 / 13 追写 inline R2 复核句；§9 补 **[TBD-T16] / [TBD-T18]** 并声明 **[TBD-T17] 预留未分配**。**不变**：§1 / §3~§7 的结论、模块数与端口数、`IFC-IB-001~265`、REQ→MOD 覆盖矩阵、DAG 无环（R2 只追加）。
**R7 修订摘要（GROUP_A REV-06 贯通：诉求③「UI 可视化配置」纳入 v1）**: 新增 **ADR-14 / ADR-15 / ADR-16**（编辑模型 / 单一真源（双向同源）/ 装配期 fail-fast 准入闸门），**ADR 数 13 → 16**；新增 **§2.0.2 R7 影响复核表**（**既有 13 条 ADR 在 R7 下全部不受影响**——其中 ADR-09 判「不受影响且 R7 是其应用」；**新增 3 条**；**无一条 ADR 未复核**）；新增**第 14 个端口** `DefinitionDocumentStore`（IFC-IB-287，纯追加；§1.3 增一行）；§6 增补图编译输入约束；§8 新增 A6 / A7；§9 新增 [TBD-T19] / [TBD-T20]。**不变**：§1 / §3~§7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001~286` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环。**计数同步**：REQ→MOD 覆盖由 24/24 同步为 **27/27**（v1.2.0 需求总数；R1 / R2 时点基线 24/24 以括注保留）。

**R8 修订摘要（GROUP_A REV-11-1 下游贯通：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）**: 需求侧已补入 **US-IB-19「流式交付最终答复」（AC-IB-19-01 ~ 05）** 与 **US-IB-20「会话生命周期」（AC-IB-20-01 ~ 06）**。本轮**不重写**既有设计（ADR-11-R1 的流式载体、ADR-09、§1.3 的 `SessionStore` 可替换点、§6 会话生命周期段、`module_design.md` §3 MOD-IB-21 / 22、§7.3 均保留），只补此前**真正缺席**者：新增 **ADR-17**（「可选手动确认中间态」的承载方式与状态丢失语义；**3 候选方案**，Option B 选定），**ADR 数 16 → 17**；新增 **§2.0.3 R8 影响复核表**（**既有 16 条 ADR 在 R8 下全部不受影响**——ADR-09 判「不受影响，且 R8 是其应用」、ADR-11 判「不受影响，R8 复用其载体」；**新增 1 条**；**无一条跳过**）；§1.3 追加 R8 注；§6 增补流式与会话四条规范化补充；§8 新增 A8；§9 新增 [TBD-T21]；§10.1 / §10.3 追加 R8 行。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**14**）、`IFC-IB-001~297` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、**`tech_stack.md` 未改**（无新第三方依赖）。
**（REV-13）认证与商用界面重构增量**（GROUP_A REV-13 下游贯通）：承接 GROUP_A REV-13（REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）：① 新增 **ADR-18 ~ ADR-27**（账户/会话落点与载体、令牌机制、口令与首登改密、账户↔项目绑定、与 `AuthzPolicy` 端口协作、前端重构与路由、粘贴令牌入口废除、HTTPS 落点、迁移/回滚、限速与审计（条件性）），每条 ≥2 方案；**ADR 数 17 → 27**；② 新增 **§2.0.4 R13 影响复核表**（既有 17 条 ADR 逐条复核，无一条跳过）；③ 新增**第 15 个端口** `AccountStore`（IFC-IB-310，定义于 MOD-IB-01 零依赖 Protocol 层）；④ 新增 **IFC-IB-309 ~ IFC-IB-332**（24 条类型化契约）；⑤ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑥ 增量**不含实现代码**；**未写入任何口令 / 令牌 / 密钥字面量**（只登记键名）。**计数同步**：REQ-FUNC 27/27 → **36/36**（新增 IB-28~36）、NFR 14 → **18**（新增 NFR-15~18）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**14 → 15，纯追加**）、`IFC-IB-001~308` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环。

**（REV-16-2）提示词与工具可视化配置增强增量**（GROUP_A REV-16-2 下游贯通）：承接 GROUP_A REV-16-2（REQ-FUNC-IB-37~42 / REQ-NFR-IB-19 / C-IB-39 / C-IB-40 / OQ-IB-24）：① 对 **ADR-15** 作**正式修订**（子节 **ADR-15-R1**；定为「**amend（追加修订子节）**」而非 supersede，理由见 ADR-15-R1 与包 §5.1）：真源由「定义文档为**全部**持久化态唯一真源」修订为「**分域真源 + 装配期合并**」——定义文档仍为**结构 / 配置域**持久化态唯一真源，专家**主 / 兜底提示词**改由**独立 markdown 目录**承载（**提示词域**持久化态唯一真源）；派生视图**仍只读**。② 新增 **ADR-29 / ADR-30 / ADR-31 / ADR-32**，每条 >=2 方案含已评估未采纳项；**ADR 数 28 → 32**。③ 新增 **§2.0.6 R16-2 影响复核表**（既有 28 条 ADR 逐条复核，**无一条跳过**；**新增 4 条**）。④ 新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）与 **IFC-IB-337 ~ 354**（18 条类型化契约）。⑤ 落点并入既有模块（**零新增模块、零新增依赖边**）；§1.3 / §8 / §9 / §10.1 / §10.2 / §10.3 同步追加 R16-2 行。⑥ **计数同步**：REQ-FUNC 36/36 → **42/42**（新增 IB-37~42）、NFR 18 → **19**（新增 NFR-19）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**15 → 16，纯追加**）、`IFC-IB-001~336` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、`tech_stack.md` **未改**（无新第三方依赖）。

**（REV-17）提示词兜底层重定位增量**（用户裁决 2026-10-07：「取消定义文档（承载提示词），仅仅使用 markdown 文件和兜底提示词」）：① 新增 **ADR-36**（提示词兜底层重定位：**提示词文本的唯一可写载体 = 目录 `main.md` / `fallback.md` 两层文件**；**代码内置兜底**为不可界面编辑的安全网；**定义文档交出提示词文本**，回归纯结构配置），并新增 **ADR-15-R2**（对 ADR-15 的**第二次**正式修订子节，**收窄** ADR-15-R1 规则 ⑤ 的兜底层载体）；**ADR-15 与 ADR-15-R1 正文一字不动**。② 修订 **ADR-29**（`resolved_from` 第三值 `definition_doc_fallback` → **`builtin_fallback`**；「兜底恒非空」由**结构**保证）与 **ADR-33**（单入口上提为 **`validate_two_domains`**，范围**含提示词域**）。③ 新增 **§2.0.8 R17 影响复核表**（**既有 35 条 ADR 逐条复核，无一条跳过**；**新增 1 条**；**ADR-15 判「经 ADR-15-R2 修订」**）。④ 新增 **IFC-IB-364 / 365**（**端口数不变，仍 17**）。⑤ §8 修订 **[ARCH-ASSUMPTION-A10]**（`fallback.md` **不得缺 → 亦可缺**，两层皆缺时回落代码内置兜底）；§10.1 新增 OPEN ITEM（`general` / 无专家路径人格串不可配置，**只登记不修复**）。⑥ **两条待写入交付说明的运维事实**：**一次性 `content_hash` 变更**（所有既有定义文档哈希变一次 → 开着配置页未刷新的会话首次保存可能收 `409`，前端已处理）、**legacy 键的两级处置与迁移步骤**（同内置静默丢弃 / 异内置 fail-closed 并指明迁移目标）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**17，未新增**）、`IFC-IB-001 ~ 363` **号 / 名 / 签名一字不动**（仅 10 条文字口径修订，逐条登记于 §2.0.8）、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、`tech_stack.md` **未改**（无新第三方依赖）、生效口径（ADR-32 / C-IB-40 / OOS-16）**未改**。

**（REV-18）系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量**（用户裁决 2026-10-07，REV-18-2；上游 `requirements_spec.md` v1.10.0 / REV-18-2）：① 新增 **ADR-37 ~ ADR-42**（项目注册表承载与软删 / LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析 / LLM 未配置态启动与运行期语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 服务端授权与导航解耦），**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：**不受影响 32 条**、**口径补注 4 条**（ADR-08 Key 取值来源 / ADR-18 复用载体与迁移机制 / ADR-28 项目列表数据源 / **ADR-21 由新增修订子节 ADR-21-R1 承接**）、**待裁决 0 条**、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 增 2 行 + R18 增补段；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**；§9 新增 **[TBD-T26] / [TBD-T27]**；§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3；**OI-1 / OI-2 经用户裁决 2026-10-07 关闭，OI-3 保持 OPEN**）；§10.2 追加「许可面未变」句；§10.3 追加 R18 自检；⑥ **落点并入既有模块**（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、生效口径（ADR-32 / C-IB-40 / OOS-16）**未改**、`tech_stack.md`（见 Part C：登记型口径修订，无新第三方依赖）。**登记**：**生产后端重启与首次环境变量配置须由用户执行**；`IB_DEFAULT_ADMIN_PASSWORD` 等既有凭据键纪律不变，**LLM Key 不入 `.env`**（载体内 DB，库文件 0600 且属主对齐服务账号）。

**R1 修订摘要**: 后端 Web 框架 **FastAPI → Django（+ DRF）**（用户明确指定，非建议）；流式载体改为 **Django 同步视图 + `StreamingHttpResponse` 原生 SSE**（**不引 Channels、不引 Redis**）；受影响 ADR **5 条**（ADR-03 / 07 / 08 / 11 / 13），其中 **ADR-11 全文重写（ADR-11-R1）**，逐条复核见 §2.0；模块数 / 端口数 / IFC-IB 编号 / 覆盖矩阵**均未变**（改动仅载体说明）。
**输入**: `requirements_spec.md` v1.7.0 / REV-16-3（APPROVED）、`user_stories.md` v1.6.0（APPROVED）
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
| 定义文档来源（**R7 新增**） | `DefinitionDocumentStore`（IFC-IB-287） | `FileDefinitionDocumentStore`（本地文件；原子写 + 语义哈希乐观并发） | 新增适配器（如接 DB / 配置中心，上层零改动） | AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |
| 独立提示词目录来源（**REV-16-2 新增**） | `ExpertPromptStore`（IFC-IB-339） | `FsExpertPromptStore`（本地 markdown 目录；原子写 + 语义哈希乐观并发，同 IFC-IB-289 精神） | 新增适配器（如接 DB / 配置中心，上层零改动） | REQ-FUNC-IB-37 / IB-41；ADR-15-R1；REQ-NFR-IB-11 |
| 配置审计（**REV-16-4 新增**） | `ConfigAuditStore`（IFC-IB-357） | `SqliteConfigAuditStore`（同一 SQLite 台账；**只读审计，append-only**） | 新增适配器（如接 DB / 日志中心，上层零改动） | REQ-NFR-IB-19 / IB-06；AC-IB-32-02 |
| 项目注册表（**REV-18 新增**） | `ProjectRegistryStore`（IFC-IB-367） | `SqliteProjectRegistryStore`（**同一 SQLite 台账**；手写迁移 `005_projects.sql`；**软删 = 状态列**） | 新增适配器（如接 DB / 配置中心，上层零改动） | REQ-FUNC-IB-44 / IB-45；ADR-37；REQ-NFR-IB-11 |
| LLM Key 载体（**REV-18 新增**） | `LlmKeyStore`（IFC-IB-368） | `SqliteLlmKeyStore`（**同一 SQLite 台账**；手写迁移 `006_llm_key.sql`；**单行表，全局唯一**） | 新增适配器（如接密钥管理服务，上层零改动） | REQ-FUNC-IB-47；REQ-NFR-IB-20；C-IB-42；ADR-38；REQ-NFR-IB-11 |

**（REV-16-4）保存期校验、审计与内存态暴露的可替换点显式化**：① **保存期校验落点**收敛为 MOD-IB-02 的合成纯函数 `validate_definition_full`（IFC-IB-355）= `validate`（IFC-IB-290）∪ `validate_tool_params`（IFC-IB-346），**保存路径与装配路径共用**（ADR-33）；**（本项不新增端口）**、**不改任何既有 IFC 签名**。② **审计载体**经**第 17 个端口** `ConfigAuditStore`（IFC-IB-357）抽象 —— 换为 DB / 日志中心时**上层零改动**（REQ-NFR-IB-11）；端口方法集**在类型层**排除写回配置（`record` / `list_by_project`，无 update / delete），坐实**只读审计、非第二真源**（ADR-34）。③ **内存态提示**经只读端点 `GET /api/config/storage-state`（IFC-IB-362）暴露 `StorageState`（IFC-IB-361）；**不改变** REV-FUNC-IB-40 生效口径（ADR-32 / C-IB-40 / OOS-16 不变，ADR-35）。

**（R8）会话状态可替换点的值域扩展与恢复准入路径**：`SessionStore` 端口与「默认内存实现、语义 fail-closed」的表述**不变**。R8 仅做两件事：① **值域显式化** —— 装配表键 `IB_SESSION_BACKEND` 的取值域由 `memory` **扩展**为 `memory 或 external`，**键名与默认值（`memory`）不变**（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域；键名与默认值不变」先例）；`external` 在 v1 **无适配器**（[ARCH-ASSUMPTION-A8]），属**已声明未实现**，不改既有装配语义。② **恢复准入路径显式化** —— 会话恢复的准入顺序固定为「**鉴权（`Authorization` 头）→ 归属断言（`session_key` 前缀）→ `SessionStore.load` → `can_resume` → 续跑**」；**任一前置不满足或状态不存在即 fail-closed**（`403` / `404` / `409`，**不新建会话**）。**「重启丢弃待确认状态」= 安全失败（fail-closed），非静默续跑** —— 该语义由 MOD-IB-22 的纯函数 `can_resume`（IFC-IB-306）与枚举 `SessionStateLossOutcome`（唯一取值 `fail_closed_restart_required`，IFC-IB-299）在**类型层**保证（AC-IB-20-02 / AC-IB-20-05）。

**（REV-13）鉴权主体来源的可替换点显式化**：§1.3「鉴权」行的形态**不变**（`AuthzPolicy` 注入 + 默认 `DenyAllPolicy` + 未注入即启动失败）。R13 只做两件事：① **主体解析来源**由「接入方 `resolve_principal`」**扩展**为「接入方可注入，或使用**基座内置**的 `SessionTokenResolver`（IFC-IB-322）」—— `IB_AUTHZ_POLICY_MODULE` 的**键名与语义不变**，仅其**可取值**新增内置模块路径 `ibweb.accounts.policy`（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域；键名与默认值不变」先例）；② **生产 fail-closed 语义不变**（未配置即 `StartupError`）。**不得**因此产生第二授权真源（ADR-22；REQ-FUNC-IB-33）。

**（REV-16-2）提示词载体与工具参数的可替换点显式化**：① **提示词载体**由「仅定义文档」**扩展**为「定义文档（结构 / 配置域）+ 独立 markdown 目录（提示词域）」，经**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）抽象 —— 载体从文件换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11）；真源边界与合并规则见 **ADR-15-R1**。② **工具参数**的可配化**不改变**工具本体登记入口（`register_tool`，IFC-IB-181 不变）；参数 schema 由 `ToolParamSpec`（IFC-IB-340）声明并在**装配期**校验。③ **两个持久化载体并存**（定义文档 + 提示词目录）**不构成重叠第二真源**（真源按域唯一）；**禁止**将任一域的内容重复写入另一域。

**（REV-18）项目注册表与 LLM Key 载体的可替换点显式化**：① **项目注册表**经**第 18 个端口** `ProjectRegistryStore`（IFC-IB-367）抽象 —— 项目管理（CRUD + 软删 / 停用）从「配置枚举（`IB_CONFIG_FILE` 的 `projects.<id>`，装配期 `_seed_projects` 只读快照）」升格为「**运行期可变状态的唯一载体**」；`GET /api/projects`（IFC-IB-333）**数据源切换**为注册表（**端点号 / 名 / 签名与 fail-closed 语义一字不动**，登记型口径修订）；换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11；ADR-37）。② **LLM Key 载体**经**第 19 个端口** `LlmKeyStore`（IFC-IB-368）抽象 —— **单一全局 Key**（单行表，以**结构**保证唯一，OOS-18 为扩展点预留）；装配期由组合根经 `resolve_secret()` 读取（**唯一读点**）；HTTP 层只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`）—— **不回显明文为类型层事实**（响应类型无明文字段；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**，避免长度 / 前缀侧信道）；承载**库文件 0600 且属主对齐服务账号**（ADR-38 / REQ-NFR-IB-20）。③ **`.env` 仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**（登记型口径修订；见 ADR-38 Consequences 与 `tech_stack.md` Part C）。④ **生效口径不变**：Key / 项目 / 账号的**保存与变更一律经「保存 + 服务重启重装配」生效**（ADR-32 / C-IB-40 / OOS-16），**不引运行期热重载**；**重启由用户手工执行**。

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

**R2 复核小结**：**受影响 1 条**（ADR-02，且**仅补附注**）；**R2 不受影响 12 条**（ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13）。**无一条 ADR 未复核**。R2 的所有改动**不触及**：端口数（13；**R7 同步：13 → 14，新增 `DefinitionDocumentStore`，纯追加**）、`IFC-IB-001~265` 编号体系、REQ→MOD 覆盖矩阵（**R7 同步计数：27/27 + 14；R2 时点基线为 24/24**）与 DAG 无环性（模块数 25 → 26，纯追加）。

### 2.0.2 R7 影响复核表（R7 增量：可视化配置 = REQ-FUNC-IB-25 / IB-26 / IB-27）

> **口径**：R7 是**追加式增量**（新增 ADR 3 条、端口 1 个、IFC 段 11 条；**不新增模块、不新增依赖边**）。凡决策客体未被 R7 触及者，一律**显式声明「R7 不受影响」**，以便门控区分「已检查」与「漏检查」。以下逐条覆盖 **ADR-01 ~ ADR-16**（**无一条跳过**）。

| ADR | R7 复核结论 | 一句话理由 |
|-----|-------------|-----------|
| ADR-01 | **R7 不受影响** | 向量库端口与 collection 维度声明未动；定义文档属**配置侧**工件，不触碰 `PointPayload` / `CollectionSpec`（IFC-IB-001~012、100~110 不变） |
| ADR-02 | **R7 不受影响** | embedding 服务端形态与冷 / 热双路径未动；可视化不改变 `ib-embed` 线协议，也不改动其配置**键集**（`tech_stack.md` §1.2 不变） |
| ADR-03 | **R7 不受影响** | systemd 单元仍为**四个**；可视化是 `ib-web` 内的页面与端点（**非新进程**），未新增单元、未改 `ib-web` 载体 |
| ADR-04 | **R7 不受影响** | 隔离机制未动：定义文档是**项目级**工件（一项目一文档，`Scope` 必填），其端点一律复用归属断言（`403` 口径与 §1.4 第 2 条一致）；`CollectionResolver` 仍为唯一 collection 解析入口 |
| ADR-05 | **R7 不受影响** | 原文件内容寻址与重建机制未动；定义文档**不是**内容寻址对象（属配置，不参与 blob 寻址），也**不进入** `fingerprint` 因子 |
| ADR-06 | **R7 不受影响** | PDF 解析库选型与三路径未动；可视化**未引入任何新 PDF 库** |
| ADR-07 | **R7 不受影响** | 台账仍为 SQLite + `LedgerRepository` + 自管 SQL + **手写 scoped 迁移**；定义文档**不经台账**（无新表、无新迁移），**不经 Django ORM** |
| ADR-08 | **R7 不受影响** | 外发边界未动：可视化**不外发定义文档或其内容**（AC-IB-17-06）；图可视化库须**随构建产物本地打包、禁止运行期 CDN 加载**；`describe_egress()` 的 `data_categories` **无需扩项** |
| ADR-09 | **R7 不受影响（且 R7 是其应用）** | 定义文档在**装配期**被派生为构造参数后透传；编排骨架仍只认端口与纯数据、**仍不见业务语义** —— 与「两段式上下文 + 装配期注入」同一模式 |
| ADR-10 | **R7 不受影响** | 异步入库的队列载体与租约语义未动；定义文档的装载与校验发生在**启动 / 装配期**，不进入入库任务路径 |
| ADR-11 | **R7 不受影响** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；可视化端点为**普通 HTTP（非流式）**，不占 worker 长连接预算，与 [TBD-T15] 容量纪律相容；「禁止 `?token=`」纪律**扩展至全部新端点**（含定义文档的 GET / PUT） |
| ADR-12 | **R7 不受影响** | OCR 与页面渲染两个端口及降级语义未动；可视化不消费也不改变其签名 |
| ADR-13 | **R7 不受影响** | `RetrievalResult` 字段与降级语义未动；R7 的新失败面是**装配期 fail-closed（拒绝装配）**，与运行期读路径 fail-open **在时间轴与契约上分离**（§7.3 / §7.4），二者不冲突 |
| **ADR-14（R7 新增）** | **新增** | 可视化配置的**编辑模型**：定义文档唯一真源 + 显式 round-trip，视图侧零持久化 |
| **ADR-15（R7 新增）** | **新增** | 定义文档**单一真源（双向同源）**与只读派生视图（派生不落盘、不可反写） |
| **ADR-16（R7 新增）** | **新增** | **装配期完备性校验 + fail-fast 准入闸门**（无「强制继续 / 忽略错误」开关） |

**R7 复核小结**：**既有 13 条 ADR 在 R7 下全部不受影响**（其中 ADR-09 判「不受影响，且 R7 是其应用」）；**新增 3 条**（ADR-14 / 15 / 16）→ **ADR 总数 13 → 16**。**无一条 ADR 未复核**。R7 的所有改动**不触及**：模块数（**26，未新增**）、`IFC-IB-001~286` 编号体系、**§4.1 依赖边（零新增边）**与 DAG 无环性；**端口数 13 → 14**（纯追加）；REQ→MOD 覆盖矩阵**由 24/24 同步为 27/27**（v1.2.0 需求总数，见 §10.3）。

### 2.0.3 R8 影响复核表（GROUP_A REV-11-1 下游贯通；追加式复核，不改写既有结论）

> 本节**只新增**，§2.0（R1）/ §2.0.1（R2）/ §2.0.2（R7）三次复核**原样保留**。**逐条复核，无一条跳过。**

| ADR | R8 判定 | 复核理由 |
|-----|---------|---------|
| ADR-01 | **R8 不受影响** | 向量库抽象层与 Qdrant 集成方式未动；会话状态不经向量库承载 |
| ADR-02 | **R8 不受影响** | `ib-embed` 的形态值域（`http` / `inproc` / `fake`）与服务端归属未动；会话状态不涉 embedding |
| ADR-03 | **R8 不受影响** | 部署形态（禁 Docker / 系统级安装）未动；v1 的持久化策略只取进程内取值，不引入新部署单元 |
| ADR-04 | **R8 不受影响** | `Scope` 仍为必填、`session_key` 前缀断言沿用同一隔离精神（FM-7）；**未新增隔离维度、未改 `CollectionResolver`** |
| ADR-05 | **R8 不受影响** | `BlobStore` 与图片字节口径未动；完成事件的结构化产物只携带引用定位（`CitationItem`），**不内联字节、不涉 BlobStore** |
| ADR-06 | **R8 不受影响** | LLM 提供方与调用语义未动；确认门与恢复不改变 LLM 调用契约 |
| ADR-07 | **R8 不受影响** | 切分与嵌入的本地化口径未动 |
| ADR-08 | **R8 不受影响** | 入库流水线与台账语义未动；会话状态**不入台账**（v1 为内存实现，不持久化到台账） |
| ADR-09 | **R8 不受影响，且 R8 是其应用** | 「骨架不见业务语义」在 R8 被**具体化**为「内部子任务产物永不映射为可见 `kind`」（IFC-IB-303，AC-IB-19-04）——仍不引入业务语义，只是把既有边界落到**帧级判据** |
| ADR-10 | **R8 不受影响** | 异步入库的队列载体与租约语义未动 |
| ADR-11 | **R8 不受影响，R8 复用其载体** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；新增的 `POST /api/chat/resume`（IFC-IB-307）**复用同一载体**，不引 Channels、不引 Redis；「禁止 `?token=`」纪律**扩展至该新端点** |
| ADR-12 | **R8 不受影响** | OCR 与页面渲染两个端口及降级语义未动 |
| ADR-13 | **R8 不受影响** | 「故障与空结果可区分」在 R8 被沿用：完成事件**不臆造**引用（`citations` 可为空元组 + `had_content: bool`，IFC-IB-300）；会话状态丢失走 **fail-closed**，与运行期读路径 fail-open 在时间轴与契约上分离 |
| ADR-14 | **R8 不受影响** | 可视化配置的编辑模型未动；R8 不涉定义文档 |
| ADR-15 | **R8 不受影响** | 定义文档单一真源（双向同源）未动；R8 不涉派生视图 |
| ADR-16 | **R8 不受影响** | 装配期 fail-fast 准入闸门未动；R8 的「会话状态丢失 = fail-closed」发生在**运行期**，与装配期闸门分属不同时点，二者不冲突 |
| **ADR-17（R8 新增）** | **新增** | 「可选手动确认中间态」的承载方式与状态丢失语义（3 候选方案，Option B 选定） |

**R8 复核小结**：**既有 16 条 ADR 在 R8 下全部不受影响**（其中 ADR-09 判「不受影响，且 R8 是其应用」、ADR-11 判「不受影响，R8 复用其载体」）；**新增 1 条**（ADR-17）→ **ADR 总数 16 → 17**。**无一条 ADR 未复核**。R8 的所有改动**不触及**：模块数（**26，未新增**）、端口数（**14**）、`IFC-IB-001~297` 编号体系、**§4.1 依赖边（零新增边）**与 DAG 无环性、REQ→MOD 覆盖矩阵（**27/27 REQ-FUNC + 14 NFR**）、`tech_stack.md`（**未改**）。

### 2.0.4 R13 影响复核表（REV-13 追加式复核，不改写既有结论）

> 只新增；§2.0（R1）/ §2.0.1（R2）/ §2.0.2（R7）/ §2.0.3（R8）**原样保留**。逐条复核，无一条跳过。

| ADR | R13 判定 | 复核理由 |
|-----|---------|---------|
| ADR-01 | **不受影响** | 向量库抽象层未动；账户/会话不经向量库 |
| ADR-02 | **不受影响** | `ib-embed` 形态值域与服务端归属未动 |
| ADR-03 | **不受影响** | 部署形态（禁 Docker / 系统级）未动；**未净增 systemd 单元**（账户内建于 `ib-web`） |
| ADR-04 | **不受影响** | `Scope` 必填、归属断言沿用；账户绑定项目不新增隔离维度 |
| ADR-05 | **不受影响** | BlobStore 未动；账户不落 Blob |
| ADR-06 | **不受影响** | LLM 提供方未动；认证不改变 LLM 调用契约 |
| ADR-07 | **不受影响** | 台账 SQLite + 手写 scoped 迁移（ADR-07-R1）**正是 R13 复用的机制**：`003_accounts.sql` 沿用 |
| ADR-08 | **不受影响** | 入库流水线未动；**账户与会话表入台账但不在既有状态机语义内**（独立表，见 ADR-18/26） |
| ADR-09 | **不受影响** | 骨架不见业务语义未动；认证发生在 HTTP 边界之外层（中间件） |
| ADR-10 | **不受影响** | 异步入库队列与租约未动 |
| ADR-11 | **不受影响，R13 复用其纪律** | 流式仍 Django 原生 SSE；**「凭据不进 URL」纪律在 R13 扩展至 `/api/auth/*` 与 `/api/accounts*` 全部新端点**（`?token=` 一律 4xx） |
| ADR-12 | **不受影响** | OCR / 页面渲染端口未动 |
| ADR-13 | **不受影响** | 「故障与空结果可区分」沿用：认证失败统一 401（**不区分用户是否存在**，避免探测预言机） |
| ADR-14 | **不受影响** | 可视化编辑模型未动 |
| ADR-15 | **不受影响** | 定义文档单一真源未动 |
| ADR-16 | **不受影响** | 装配期 fail-fast 闸门未动；**R13 的账户装配（种子 + 策略模块）沿用同一「装配期失败即不启动」纪律**（B9） |
| ADR-17 | **不受影响** | 确认中间态未动；会话令牌（ADR-19）与确认门会话状态（`SessionStore`）**是两个不同概念，不得混淆** |
| **ADR-18 ~ ADR-27（R13 新增）** | **新增 10 条** | 见本节之后新增的 ADR-18 ~ ADR-27 全文（§2 末尾） |

**R13 复核小结**：既有 **17 条 ADR 全部不受影响**（其中 ADR-07、ADR-11、ADR-16 判「不受影响，且 R13 复用其纪律/机制」）；**新增 10 条** → ADR 总数 **17 → 27**。**无一条跳过**。R13 **不触及**：模块数（26，未新增）、`IFC-IB-001~308` 编号体系、§4.1 依赖边与 DAG 无环性、既有 REQ→MOD 覆盖（新增 REQ 单列）。

### 2.0.5 R14 影响复核表（REV-14 回归缺陷修复：全局管理员项目上下文）

> 只新增；§2.0（R1）/ §2.0.1（R2）/ §2.0.2（R7）/ §2.0.3（R8）/ §2.0.4（R13）**原样保留**。逐条复核，**无一条跳过**。本表覆盖既有 **ADR-01 ~ ADR-27** 并登记新增 **ADR-28**。

| ADR | R14 判定 | 复核理由 |
|-----|---------|---------|
| ADR-01 | **不受影响** | 向量库抽象层与 collection 维度未动；项目枚举不改 `PointPayload` / `CollectionSpec` |
| ADR-02 | **不受影响** | `ib-embed` 形态值域与服务端归属未动；项目上下文不涉 embedding 线协议 |
| ADR-03 | **不受影响** | 部署形态与四单元未动；`GET /api/projects` 是 `ib-web` 内的普通端点，不净增进程 |
| ADR-04 | **不受影响，且 R14 是其应用** | `Scope` 仍必填、隔离仍 fail-closed；R14 **不得**削弱「未选项目即不泄露」（ADR-28 约束③）；项目枚举只回「可见集合」，不改隔离粒度 |
| ADR-05 | **不受影响** | BlobStore 与重建机制未动 |
| ADR-06 | **不受影响** | 解析库选型未动 |
| ADR-07 | **不受影响** | 台账仍 SQLite + 手写迁移；项目列表取自装配（`Deps.projects` / `_seed_projects`），**不新增表、不经 ORM** |
| ADR-08 | **不受影响** | LLM 端点与数据外发边界未动；项目枚举不外发 |
| ADR-09 | **不受影响** | 骨架不见业务语义未动；项目上下文发生在 HTTP 边界（`AuthMiddleware`），不入骨架 |
| ADR-10 | **不受影响** | 异步入库队列与租约未动 |
| ADR-11 | **不受影响，R14 复用其纪律** | SSE 载体未动；`X-IB-Project` 经 `headers()` 进入 `chatStream` / `chatResume` 的 `fetch` 请求头（`EventSource` 不能设自定义头，本项目已用 `fetch` 读流）——仍**不含 `?token=`** |
| ADR-12 | **不受影响** | OCR / 页面渲染端口未动 |
| ADR-13 | **不受影响** | 「故障与空结果可区分」沿用：未选项目 → 项目级端点 fail-closed（可区分于空结果） |
| ADR-14 | **不受影响** | 可视化编辑模型（定义文档唯一真源 + 显式 round-trip）未动 |
| ADR-15 | **不受影响** | 定义文档单一真源与只读派生视图未动 |
| ADR-16 | **不受影响** | 装配期 fail-fast 准入闸门未动；R14 使可视化配置页能取得当前项目，`503` 消失的原因是**项目上下文就位**而非放宽闸门 |
| ADR-17 | **不受影响** | 确认中间态承载与状态丢失语义未动 |
| ADR-18 | **不受影响** | 账户 / 会话模块落点与数据载体未动 |
| ADR-19 | **不受影响** | 令牌机制（不透明、服务端存储、无 Cookie）未动；`X-IB-Project` **不是**凭据 |
| ADR-20 | **不受影响** | 口令与首登强制改密未动；改密态放行清单不变 |
| ADR-21 | **不受影响** | 账户↔项目绑定与角色模型未动；R14 是其在「项目选择」上的应用 |
| ADR-22 | **不受影响** | 单一授权真源未动；`X-IB-Project` **不**替换授权判定（仍唯一经 `AuthzPolicy`） |
| ADR-23 | **不受影响** | 前端重构与路由（Element Plus + vue-router hash）未动；`projectContext` 为既有 store 模式（模块级 `reactive`，不引 Pinia） |
| ADR-24 | **不受影响** | 粘贴令牌入口废除未动；`X-IB-Project` 不引入任何旁路 |
| ADR-25 | **不受影响** | HTTPS 落点未动 |
| ADR-26 | **不受影响** | 迁移 / 种子 / 回滚未动；项目列表不新增迁移 |
| ADR-27 | **不受影响** | 登录限速与审计（条件性）未动 |
| **ADR-28（R14 新增）** | **新增** | 项目上下文的选择与传播；**4 候选方案**，Option B 选定并吸收 Option A 的「单项目预选」便利 |

**R14 复核小结**：既有 **27 条 ADR 全部不受影响**（其中 ADR-04 判「不受影响，且 R14 是其应用」、ADR-11 判「不受影响，R14 复用其纪律」）；**新增 1 条** → ADR 总数 **27 → 28**。**无一条跳过**。R14 **不触及**：模块数（26，未新增）、端口数（15）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001~332` 编号体系；新增 IFC 为 **IFC-IB-333 ~ 336**（见 `module_design.md` §2.2.5）。

### 2.0.6 R16-2 影响复核表（提示词与工具可视化配置增强增量）

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01 ~ ADR-13 | **不受影响** | 向量库 / embedding / LLM / 解析 / OCR / 渲染 / 台账 / Blob / 会话 / 鉴权 / 配置 / 检索契约均未动 |
| ADR-14（可视化编辑模型） | **不受影响，且 R16-2 是其应用** | 「定义文档唯一真源 + 显式 round-trip、视图零持久化」纪律**扩展**到提示词域（提示词亦经显式 round-trip 回写独立目录，视图侧仍零持久化） |
| **ADR-15**（定义文档单一真源） | **经 ADR-15-R1 修订** | 真源边界由「全量唯一真源」修订为「**分域真源 + 装配期合并**」；ADR-15 正文 / Status 一字不动，修订见 **ADR-15-R1**（§4.D） |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 R16-2 复用其机制** | 校验器**扩展**为跨两域合并后的校验（孤儿提示词文件 / 缺兜底 / 工具参数越界），`ValidationReport` 仍不含 `force` / `ignore` / `warn_only`（类型层事实不变） |
| ADR-17 ~ ADR-28 | **不受影响** | 确认中间态 / 账户 / 会话 / 令牌 / 口令 / 项目绑定 / 授权 / 前端 / HTTPS / 迁移 / 限速 / 项目上下文均未动 |
| **ADR-29 / ADR-30 / ADR-31 / ADR-32** | **新增** | 提示词分层 / 工具授权与参数 / FreeArk 严格对齐 / 生效口径；每条 >=2 方案 |

**R16-2 复核小结**：既有 **28 条 ADR 全部已复核**（其中 ADR-14 / ADR-16 判「不受影响且 R16-2 复用其机制」，**ADR-15 判「经 ADR-15-R1 修订」**）；**新增 4 条** → ADR 总数 **28 → 32**。**无一条跳过**。R16-2 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001~336` 编号体系；新增 IFC 为 **IFC-IB-337 ~ 354**（见 `module_design.md` §2.2.6）。

### 2.0.7 R16-4 影响复核表（回归缺陷修复轮：DEFECT-R16-02 / GAP-R16-03 / GAP-R16-04）

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01 ~ ADR-13 | **不受影响** | 向量库 / embedding / LLM / 解析 / OCR / 渲染 / 台账 / Blob / 会话 / 鉴权 / 配置 / 检索契约均未动 |
| ADR-14（可视化编辑模型） | **不受影响** | 「定义文档唯一真源 + 显式 round-trip、视图零持久化」纪律未动；R16-4 只在校验入口与审计面增量 |
| ADR-15 / ADR-15-R1（真源边界） | **不受影响** | 真源分域（定义文档 = 结构 / 配置域；提示词目录 = 提示词域）一字未动 |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 R16-4 是其应用** | 保存期前移的完备性校验（合成入口 IFC-IB-355）是 ADR-16 fail-fast 闸门在**保存路径**的对称实现；`ValidationReport` **仍不含** `force` / `ignore` / `warn_only`（类型层事实不变） |
| ADR-17 ~ ADR-28 | **不受影响** | 确认中间态 / 账户 / 会话 / 令牌 / 口令 / 项目绑定 / 授权 / 前端 / HTTPS / 迁移 / 限速 / 项目上下文均未动 |
| ADR-29 / ADR-30 / ADR-31 | **不受影响** | 提示词分层 / 工具授权与参数 / FreeArk 严格对齐未动；R16-4 **复用** ADR-30 的工具参数契约（IFC-IB-346）做保存期校验 |
| **ADR-32**（配置生效口径） | **不受影响，且 R16-4 是其提示面补足** | ADR-35 仅**暴露**存储态（内存 / 文件），**不改变**「保存 + 服务重启重装配」语义；OOS-16 / C-IB-40 不变 |
| **ADR-33 / ADR-34 / ADR-35** | **新增** | 保存期校验落点 / 可查询审计记录载体 / 内存态提示暴露；每条含已评估未采纳项 |

**R16-4 复核小结**：既有 **32 条 ADR 全部已复核**（其中 ADR-16 判「不受影响，且 R16-4 是其应用」、ADR-32 判「不受影响，且 R16-4 是其提示面补足」）；**新增 3 条** → ADR 总数 **32 → 35**。**无一条跳过**。R16-4 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 354` 编号体系；新增 IFC 为 **IFC-IB-355 ~ 363**；**端口 16 → 17（纯追加）**（见 `module_design.md` §2.2.7）。

### 2.0.8 R17 影响复核表（提示词兜底层重定位：ADR-15-R2 + ADR-36）

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01 ~ ADR-13 | **不受影响** | 向量库 / embedding / LLM / 解析 / OCR / 渲染 / 台账 / Blob / 会话 / 鉴权 / 配置 / 检索契约均未动。**注**：ADR-04（LLM 端点抽象）**载体未动** —— 本轮的 `build_expert` 加 keyword-only 形参与 system 位矫正属**既有端口的方法签名补全**，端口号 / 名不变，见 ADR-36 Decision 第 3 条 |
| ADR-14（可视化编辑模型） | **不受影响，且 R17 是其应用** | 「显式 round-trip + 视图零持久化 + 白名单制」纪律**原样复用**：R17 只是把 `experts[].fallback_prompt` **移出白名单**，使「可编辑对象 ⊂ 已校验对象」的成对维护约束更紧（可编辑集**变小**，无新增死角） |
| **ADR-15**（定义文档单一真源） | **经 ADR-15-R2 修订** | 第二次正式修订：**收窄** ADR-15-R1 规则 ⑤ 的**兜底层载体**（定义文档字段 → 代码内置安全网）；ADR-15 **与 ADR-15-R1 正文一字不动**，修订落在 **ADR-15-R2**。ADR-15-R1 的其余六条规则（域不重叠 / 合并键 = 专家 `name` / 主缺失回退 / 孤儿拒装 / 派生视图只读 / 生效口径）**结论不变** |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 R17 复用其机制** | R17 **不新增**闸门、**不放松**闸门：`ValidationReport` 仍不含 `force` / `ignore` / `warn_only`。**唯一的判据变更**：`prompt_fallback_missing` 的触发条件由「目录无 `fallback.md`」收窄为「**无 `fallback.md` 且无内置兜底**」—— 因内置兜底为**全函数**，该错误降级为**防御性断言**（ADR-36 Decision 第 2 条）；孤儿文件（`prompt_orphan_file`）**仍被拒**，反越域不变 |
| ADR-17 ~ ADR-28 | **不受影响** | 确认中间态 / 账户 / 会话 / 令牌 / 口令 / 项目绑定 / 授权 / 前端 / HTTPS / 迁移 / 限速 / 项目上下文均未动；R17 的界面改动限于配置页（MOD-IB-24）内的**字段级**调整，不触及路由 / 鉴权 / 会话 |
| **ADR-29**（提示词主 / 兜底分层） | **经 R17 修订两处** | ① Option B 的 `resolved_from` 第三值由 `definition_doc_fallback` **更名为 `builtin_fallback`**（取值域仍为**三值**，语义一一对应）；② Decision 的「**兜底恒非空**由装配期校验（IFC-IB-290 扩展）保证」修订为「**由结构保证**」（全函数内置兜底 → 合并结果不可能为空；原校验保留为冗余第二道防线）。**分层语义、回退方向、IFC-IB-337/338/343/349 全部不变** |
| ADR-30（工具授权与参数） | **不受影响** | 工具授权 / 参数可配 / 不新增工具本体均未动；R17 不触及 `ToolGrantSpec` / `ToolParamSpec` / `validate_tool_params` |
| **ADR-31**（FreeArk 严格对齐） | **不受影响，10 维表第 5 行口径澄清** | 第 5 行维度仍是 `fallback_prompt`，**对齐取值文本不变**；澄清其基座落点 = `_DEFAULT_SPECS[].fallback_prompt`（**代码内置安全网**），而非定义文档字段（该字段已移出 schema）。其余 9 维与工具参数排除项均不变；FreeArk **全程只读**不变 |
| ADR-32（生效口径） | **不受影响** | 「保存 + 服务重启重装配」**一字未动**；R17 **明确不引**热重载（本 ADR Options 已否 A / C）；`fallback.md` 可缺**不改变**生效时机，只改变合并结果的取值来源 |
| **ADR-33**（单校验入口） | **经 R17 扩展范围** | 单入口**上提一级**为 `validate_two_domains`（IFC-IB-364）= `validate_definition_full` ∪ `validate_prompt_directory`，覆盖定义域 → 工具域 → **提示词域**（顺序固定）。**不改** `validate_definition_full`（IFC-IB-355）的号 / 名 / 签名；收敛目标（保存路径 ≡ 装配路径）不变，R17 只是让提示词域也进入该等价 |
| ADR-34（配置审计） | **不受影响** | 审计载体 / 只读端口 / 端点均未动；R17 **未**把「本次丢弃了 N 处 legacy 键」这类提示加到 definition 的 GET / PUT 响应上（**红线**：顶层键集不变），若将来需提示，**只能**走既有 `/api/config/storage-state`（ADR-35 的提示面） |
| ADR-35（内存态提示暴露） | **不受影响** | storage-state 端点 / `StorageState` 类型 / 提示语义均未动；R17 的「代码内置兜底**只读回显**」落在 `/api/config/prompts` 的 **per-expert 键**上（顶层 5 键集不变），与 ADR-35 的提示面**互不重叠** |
| **ADR-36** | **新增** | 提示词兜底层重定位：文件两层 + 代码内置安全网（无第二可写入口）；含 4 候选方案与 3 项已评估未采纳留痕 |

**R17 复核小结**：既有 **35 条 ADR 全部已复核**（其中 ADR-14 判「不受影响，且 R17 是其应用」、ADR-16 判「不受影响，且 R17 复用其机制」；**ADR-15 判「经 ADR-15-R2 修订」**、**ADR-29 / ADR-33 各判「经 R17 修订」**、**ADR-31 判「不受影响，第 5 行口径澄清」**）；**新增 1 条** → ADR 总数 **35 → 36**。**无一条跳过**。R17 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、**端口数（17，未新增）**、既有 `IFC-IB-001 ~ 363` 编号 / 名 / 签名（**文字性修订**见下方清单）；新增 IFC 为 **IFC-IB-364 / 365**（见 `module_design.md` §2.2.8）。

**R17 被修订 IFC 逐条登记**（**只改文字 / 取值口径，不改号 / 名 / 签名**）：`IFC-IB-212`（`build_expert` 补 keyword-only `system_prompt`；消解假陈述 docstring）、`IFC-IB-287`（`ExpertSpecInput` 去 `fallback_prompt` 字段）、`IFC-IB-290`（定义域校验项 5 只留 `cn_label`；白名单去该键）、`IFC-IB-292`（`_semantic_payload` 去该键 → 一次性内容哈希变更）、`IFC-IB-338`（`resolved_from` 第三值更名）、`IFC-IB-339`（`load_bundle` 形参改名）、`IFC-IB-343`（`merge_prompt_layers` 第三分支 + 形参改名）、`IFC-IB-345`（`validate_prompt_directory` 缺兜底判据收窄）、`IFC-IB-347`（`derive_prompt_layers` 形参改名）、`IFC-IB-355`（`validate_definition_full` 被更上层合成入口包含，**自身不变**）。**新增**：`IFC-IB-364`（`validate_two_domains`）、`IFC-IB-365`（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `builtin_fallback_for` / `builtin_fallbacks_for`）。

### 2.0.9 REV-18 影响复核表（系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量）

> **背景**：`requirements_spec.md` v1.10.0 / **REV-18-2**（APPROVED）新增 REQ-FUNC-IB-43 ~ IB-48、REQ-NFR-IB-20、C-IB-42 / C-IB-43、OOS-17 ~ OOS-19、DR-20 / DR-21，并就 OQ-IB-25 ~ OQ-IB-31 七条一次拍板。本节对 v1.9.0 的 **36 条 ADR（ADR-01 ~ ADR-36）逐条复核**并登记新增 6 条，作为「设计未因需求增量而漂移」的可审计证据。**无一条跳过**。

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01 ~ ADR-13 | **不受影响** | 向量库 / embedding / 解析 / OCR / 渲染 / 台账 / Blob / 会话 / 鉴权 / 配置 / 检索契约均未动（含 ADR-03 部署拓扑、ADR-04 项目 / 知识库隔离与 collection 解析、ADR-05 原始文件、ADR-06 解析、ADR-07 台账、ADR-09 依赖反转、ADR-10 租约、ADR-11 流式、ADR-12 CPU 适配、ADR-13 边界校验）。**注**：**ADR-08（LLM 端点抽象与数据外发边界）决策未动** —— Key 的**取值来源**改由 **DB 装配期解析**（ADR-38），属**口径补注**；ADR-08 的端口边界 / 供应商可配 / 外发声明结论**一字未动** |
| ADR-14（可视化编辑模型） | **不受影响** | 「显式 round-trip + 视图零持久化 + 白名单制」纪律未动 |
| ADR-15 / ADR-15-R1 / ADR-15-R2（真源边界） | **不受影响** | 真源分域（定义文档 = 结构 / 配置域；提示词目录 = 提示词域）一字未动；REV-18 **不触**提示词文本载体 |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 REV-18 复用其机制** | 闸门与 `ValidationReport`（不含 `force` / `ignore` / `warn_only`）未动；REV-18 的新增装配（注册表装载与幂等播种 / Key 解析 / 账号存在性前置）沿用「任一步失败即拒绝装配」纪律 |
| ADR-17（确认中间态） | **不受影响** | 承载方式与状态丢失语义未动 |
| ADR-18（账户 / 会话落点与载体） | **不受影响，且 REV-18 复用其载体与迁移机制** | 「**同一 SQLite 台账 + 手写 scoped 迁移 + WAL + `busy_timeout`**」未动；项目注册表（`005_projects.sql`）与 LLM Key 表（`006_llm_key.sql`）**复用**该载体与迁移机制（ADR-37 / ADR-38） |
| ADR-19（不透明服务端会话令牌） | **不受影响** | 无 Cookie、只存摘要、仅 `Authorization` 头、`?token=` 一律 4xx 未动；REV-18 的新端点沿用该纪律 |
| ADR-20（bcrypt 口令存储与首登强制改密） | **不受影响** | 口令哈希与受限会话未动；REV-18 的账号编辑 / 删除**不新增口令回显路径** |
| **ADR-21（账户↔项目绑定）** | **口径补注（已由 ADR-21-R1 承接）** | R13 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。**用户裁决（2026-10-07）已关口径张力**：关系式**收窄 / 订正为 N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），由新增修订子节 **ADR-21-R1** 承接（**ADR-21 正文一字不动**，amend）。ADR-21 的**授权结论 / 端口边界不变**；**零迁移**（不加唯一约束）。**本包未改动任何既有 REQ 文本** |
| ADR-22（单一授权真源） | **不受影响，且 REV-18 是其应用** | 授权判定仍只经注入的 `AuthzPolicy`；**ADR-42 明令**「**UI 分组不作为权限机制**、非 admin 一律**服务端 403**」——即 REV-18 复用 ADR-22 纪律 |
| ADR-23（前端路由与守卫） | **不受影响** | `vue-router`（hash）与鉴权守卫未动；REV-18 的「系统管理父级导航」为**路由树内新增节点**，不引入 nginx `try_files` 回退 |
| ADR-24（粘贴令牌入口废除） | **不受影响** | 无旁路未动 |
| ADR-25（HTTPS 落点） | **不受影响** | TLS 终止与证书策略未动 |
| ADR-26（迁移 / 种子 / 回滚） | **不受影响，且 REV-18 是其应用** | 手写 scoped 迁移纪律未动；REV-18 新增迁移 `005` / `006` 走**同一机制**（前向、幂等；新表为**纯追加**，回滚 = 代码回滚） |
| ADR-27（登录限速与审计，条件性） | **不受影响** | 条件性未动；REV-18 不把项目 / Key 变更纳入限速面 |
| **ADR-28（项目上下文选择与传播）** | **不受影响；口径补注** | 显式选择 + 显式传播（`X-IB-Project`）+ fail-closed 语义**一字不动**；**仅** `GET /api/projects`（IFC-IB-333）的**数据源**由「配置枚举 `Deps.projects`」改为「**项目注册表**」（ADR-37）—— 登记型口径修订，**端点号 / 名 / 签名不变** |
| ADR-29（提示词主 / 兜底分层） | **不受影响** | 分层与回退方向未动 |
| ADR-30（工具授权与参数） | **不受影响** | 勾选 + 参数可配、不新增工具本体未动 |
| ADR-31（FreeArk 严格对齐） | **不受影响** | 10 维对齐与工具参数排除项未动；FreeArk 全程只读 |
| ADR-32（配置生效口径） | **不受影响，且 REV-18 沿用其生效口径** | 「**保存 + 服务重启重装配**」**一字未动**；REV-18 的 Key / 项目 / 账号变更**一律按 ADR-32 生效**（**不引热重载**，OOS-16 维持）；**重启由用户手工执行** |
| ADR-33（保存期单校验入口） | **不受影响** | `validate_two_domains`（IFC-IB-364）与其等价性未动；REV-18 不触定义域 / 工具域 / 提示词域校验 |
| ADR-34（配置审计） | **不受影响** | 只读审计 / 非第二真源未动；REV-18 **不**把项目 / Key / 账号变更写入 `config_audit`（顶层键集与审计面均不变） |
| ADR-35（内存态提示暴露） | **不受影响** | `GET /api/config/storage-state` 与 `StorageState` 未动 |
| ADR-36（提示词兜底层重定位） | **不受影响** | 文件两层 + 代码内置安全网未动 |
| **ADR-37 ~ ADR-42** | **新增** | 项目注册表承载与软删 / LLM Key 凭据载体 = DB + 装配期解析 / LLM 未配置态语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 授权与导航解耦；每条含 Context（REQ 引用）/ Options（≥2）/ Decision / Status / Consequences |

**R18 复核小结**：既有 **36 条 ADR 全部已复核**（**不受影响 32 条**；**口径补注 4 条**：ADR-08 / ADR-18 / ADR-28 / **ADR-21**（由新增修订子节 **ADR-21-R1** 承接，其口径张力经**用户裁决 2026-10-07 关闭**）；**待裁决 0 条**）；**新增 6 条** → ADR 总数 **36 → 42**。**无一条跳过**。R18 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 365` 编号 / 名 / 签名（文字性修订见下方清单）；**端口 17 → 19（纯追加）**；新增 IFC 为 **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）。

**R18 被修订 IFC 逐条登记**（**只改文字与取值口径，不改号 / 名 / 签名**）：`IFC-IB-024`（`LlmConfig.api_key_env` **语义降级**为「历史 / 兼容登记」——LLM Key 来源改由 DB 装配期解析，ADR-38 / ADR-39）、`IFC-IB-262` / `IFC-IB-263`（凭据纪律由「**一律经环境变量注入**」收窄为「**除外 LLM Key**：LLM Key 经 DB；其余密钥仍经环境变量」；启动校验口径改为「**LLM Key 未配置非致命**（fail-closed 于调用期）」，其余必填项仍 fail-fast）、`IFC-IB-321`（账户端点族**补齐** `PATCH /api/accounts/{user_id}` / `DELETE /api/accounts/{user_id}`（软删 + 二次确认 + 禁删 admin 与最后管理员）；`POST /api/accounts` **增前置**：目标 `project_id` 须在注册表存在且 `active`；**号 / 名 / 既有方法签名不变**）、`IFC-IB-333`（`GET /api/projects` **数据源**由配置枚举改为项目注册表；**号 / 名 / 签名不变**）。**新增**：`IFC-IB-366`（`update_user`，**加成式扩展** `AccountStore`，其既有 13 方法文本不改）、`IFC-IB-367`（端口 `ProjectRegistryStore` + 结构）、`IFC-IB-368`（端口 `LlmKeyStore` + `LlmKeyStatus`）、`IFC-IB-369`（REV-18 键名登记与启动校验口径）、`IFC-IB-370` / `IFC-IB-371`（SQL 适配器与 DDL 单源 `005` / `006`）、`IFC-IB-372 ~ IFC-IB-375`（项目 CRUD / 账号扩展 / LLM Key 端点 / 项目域上传与装配期解析）、`IFC-IB-376`（前端系统管理 IA）、`IFC-IB-377`（部署检查清单 B21 ~ B23）。

---



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

### ADR-14 可视化配置的编辑模型（定义文档唯一真源 + 显式 round-trip 编辑事务）

- **Status**: Accepted（R7 新增）
- **Context**: REQ-FUNC-IB-25（可视化配置界面 = **定义文档的图形视图**；编辑结果须**双向 round-trip** 回写；**不得**拥有独立于定义文档的持久化、**不得**形成第二真源）；REQ-FUNC-IB-26（可编辑对象 = **节点参数与专家集合**；**不含**运行期增删图节点 / 改变拓扑；**白名单制**；条件边须**显式声明分支映射**，否则界面无法判定可达性）；US-IB-17 / AC-IB-17-01（写回唯一真源 + 系统中不存在第二份持久化副本）、AC-IB-17-02（round-trip 语义等价）、AC-IB-17-03（以文档为准刷新、**不得**用陈旧视图反向覆盖、不静默丢弃）、AC-IB-17-04（白名单；**不提供**运行期改图）、AC-IB-17-05（文档只出现键名、界面不回显凭据）、AC-IB-17-06（数据不出本地 + 禁 Docker 直部署）。承载模块：MOD-IB-24（视图）/ MOD-IB-02（定义文档读写与派生）/ MOD-IB-23（端点与装配）。
- **Options**:
  - **A 界面独立持久化 + 与定义文档双写**（界面自有存储 / 表）：优—实现最直接、界面可自由演进。缺—**直接违反 REQ-FUNC-IB-25 约束②**（形成第二真源），双写必然产生分叉，AC-IB-17-01「不存在第二份持久化副本」**不可能成立**。**已评估未采纳**。
  - **B 定义文档为唯一真源 + 显式三阶段编辑事务**（载入并派生视图 → 白名单内编辑（含前端预校验）→ 服务端校验通过后**整体写回**文档），写回以**语义哈希**做乐观并发判定；视图侧**零持久化** ← **选定**。
  - **C 文件系统监听 + 内存模型双向隐式同步**（watch → 视图变即回写）：优—用户无「保存」心智。缺—隐式写回使冲突**不可判定**（AC-IB-17-03 要求「以文档为准刷新、**不得**反向覆盖」），且难以保证 round-trip 语义等价（AC-IB-17-02），失败时留下半成品文档。**已评估未采纳**。
- **Decision**: **Option B**。编辑模型 = 「**文档 → 派生视图 → （白名单内编辑 + 前端预校验）→ 服务端完备性校验（ADR-16）→ 整体写回文档（乐观并发，冲突即拒绝）**」。三点强制约束：① **视图侧零持久化** —— 不得以 localStorage / IndexedDB / 独立后端表作为真源；未提交草稿若存在，须在界面显式标注「未提交（可丢弃）」且**不得**作为载入源；② **白名单制** —— 清单外字段界面不得写入（AC-IB-17-04），白名单由 `EditableFieldWhitelist`（IFC-IB-291）定义；③ **拓扑不可编辑** —— 节点 / 边集合与条件边**存在性**不是可编辑对象（拓扑是编译期结构，见 ADR-15 与 §6）；条件边**必须**显式声明 `branch_map`，缺失即非法（由 ADR-16 校验拒绝）。写回形态为「先写临时文件、再原子替换」，**不产生半成品文档**。
- **Consequences**: 正向—从结构上消除第二真源（对齐 `agent_platform_research.md` §4.1 风险 R-1）；round-trip 可测（AC-IB-17-02 有明确判据 = 语义哈希比对）；「以文档为准」的刷新语义天然成立（AC-IB-17-03）；同时守住 REQ-FUNC-IB-26 的边界，不把可视化做成运行期改图（对齐 §4.6 过度设计黑名单）。负向—界面须承担「不可识别内容不静默丢弃 + 可读报告」的实现责任（未知字段须保留并报告）；并发编辑须给出可读冲突回执（`409` + 定位）；前端**不得**依赖任何 CDN 运行时资源（离线 + 数据不出本地，AC-IB-17-06），图可视化库须随构建产物本地打包。

### ADR-15 定义文档的单一真源（双向同源）与只读派生视图

- **Status**: Accepted（R7 新增）
- **Context**: REQ-FUNC-IB-25（描述 / 输出：**定义文档本身是唯一真源**；既有派生视图（专家集合、关键词表、默认专家、可委托集合等，见 REQ-FUNC-IB-02）**全部由更新后的定义文档重新派生**）；REQ-FUNC-IB-02（专家可配置及其派生视图）；REQ-NFR-IB-01（通用性）、IB-11（可替换性）、IB-14（可测试性）。既有落点：MOD-IB-16（专家注册表）、MOD-IB-17（能力摘要纯函数派生）、MOD-IB-19（路由内核）、MOD-IB-22（图编译）。
- **Options**:
  - **A 维持双真源**（定义文档 + 各模块内存注册表各自为准、按需同步）：优—不触碰既有 MOD-IB-16 结论。缺—与「定义文档是唯一真源」**直接冲突**；两处真源在分歧时无法判定谁对（如同一专家的关键词在文档与注册表不一致）。**已评估未采纳**。
  - **B 定义文档为持久化态唯一真源；一切派生视图为只读、可丢弃的**内存视图，在**装配期**由组合根构造并注入；派生视图**不落盘、不得反写文档** ← **选定**。
  - **C 派生视图落盘缓存**（以缓存提升界面 / 启动性能）：优—启动与界面刷新更快。缺—缓存与真源可分叉，一旦被当作**读源**即等价于第二真源（违反 REQ-FUNC-IB-25）。**已评估未采纳**；若将来确需缓存，前置条件为：失效键**必须是文档语义哈希**，且**显式声明「可随时删除、删除即回落到重新派生」**，且**不得**成为任何读路径的权威来源。
  - **D 把定义文档做成独立服务进程**（新模块 + 线协议，形态对齐 MOD-IB-26 之于 Qdrant）：优—定义文档读写与 `ib-web` 故障域隔离。缺—**净增第 5 个 systemd 单元、新端口面与新故障域**，与 C-IB-08（最小组成面）、ADR-03（四单元结论）以及「可视化**只是定义文档的视图**」的定位冲突；且新模块只能取 ≥ 27 的编号，被组合根（MOD-IB-23）依赖会产生 `23 → 27` 的边，**破坏 `w(A) > w(B)` 的构造性无环证明**（见 `module_design.md` §4.2.2）。**已评估未采纳**。
- **Decision**: **Option B**。**真源层级显式化（三层）**：① **持久化态唯一真源** = 定义文档（落点为 `IB_DEFINITION_DOC_PATH` 指向的本地文件，见 [ARCH-ASSUMPTION-A6]）；② **装配期派生注册表 / 视图**（MOD-IB-16 / 17 / 19 / 22 的构造输入）为**内存只读派生物** —— 不落盘、不可反写文档、进程重启即由文档重建；③ **派生入口可替换** —— 新增端口 `DefinitionDocumentStore`（IFC-IB-287），使文档载体从文件换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11）。**「双向同源」的准确含义** = 同一份文档**既生成编辑视图、又生成运行期配置**，两个方向同源于一份文档；而**不是**两份数据互相同步。数据层落位：契约与端口 → MOD-IB-01（L0，零依赖）；装载 / 校验 / 写回 / 派生 → MOD-IB-02（L0，framework-free）；**不新增模块、不新增依赖边**。
- **Consequences**: 正向—MOD-IB-16 既有的「纯函数派生」模式被**复用而非推翻**（`build_capability_digest` 同类模式），模块边界与 DAG 不变；派生逻辑可离线单测（AC-IB-18-05）；通用性增强（换载体只换适配器）。负向—MOD-IB-16 的「唯一真源」措辞须降级为「装配期派生注册表」（`module_design.md` §1 / §3 已同步），否则留下口径冲突；每次装配与每次界面载入均须重新派生，其耗时与规模上界须实测（[TBD-T19] / [TBD-T20]）。

### ADR-15-R1 真源边界的修订：分域真源 + 装配期合并（REV-16-2 修订子节）

- **Status**: Accepted（REV-16-2 修订；**本子节为对 ADR-15 的正式修订**，ADR-15 的 ID / Status / Context / Options / Decision / Consequences **一字不动**）
- **修订触发**: **C-IB-39**（GROUP_A REV-16-2 登记 ADR-15 触发修订）+ **OQ-IB-24**（转架构阶段承接）+ 用户裁决（2026-10-06，DR-19 / OQ-IB-18）：「专家提示词 / 定义落盘于**独立 markdown 目录**，不在定义文档内 / **不保持『定义文档是唯一真源』**」。相关需求：**REQ-FUNC-IB-37 / IB-38 / IB-41**、**REQ-NFR-IB-19**；受影响既有需求：REQ-FUNC-IB-01 / IB-02 / IB-25 / IB-26 / IB-27。
- **修订问题**: 用户裁决引入「独立提示词 markdown 目录」后，ADR-15 原 Decision 中「**定义文档为持久化态唯一真源**」的断言是否仍成立；若不成立，新的真源边界、定义文档与提示词目录的**优先级 / 合并规则**、以及**派生视图是否仍只读**应如何定义。
- **Options**:
  - **Option A（更简方案：维持「定义文档唯一真源」并把提示词内嵌为文档字段 `main_prompt` / `fallback_prompt`）**：优—不引入第二载体；ADR-14 / ADR-15 / ADR-16 的编辑模型 / 校验 / round-trip 全部**原样复用**，改动最小。缺—**与用户裁决（OQ-IB-18 / DR-19）直接冲突**（裁决明确要求独立 markdown 目录、不在定义文档内）；且提示词为**大段 markdown 文本**，内嵌会使定义文档体积膨胀、diff 噪声大、编辑体验差，与 REQ-FUNC-IB-41「可经文件保存」的落盘形态诉求不符。**已评估未采纳**（保留为**降级形态**：若用户改判，仅需把提示词字段并入定义文档 schema，不动其它纪律）。
  - **Option B（分域真源 + 装配期合并）** ← **选定**：**定义文档** = **结构 / 配置域**持久化态唯一真源（专家元数据 / 路由 / 编排 / 工具授权）；**独立 markdown 目录** = **提示词域**持久化态唯一真源（每专家主提示词 + 兜底提示词）。两域按专家 **`name`** 在**装配期**合并为**内存派生视图**（只读、不落盘、不反写任一真源）。优—**同时满足**用户裁决与「**除按域划分外不存在重叠真源**」的不变量；提示词与结构配置各自拥有合适的落盘形态与编辑体验；ADR-14 / ADR-16 的编辑与校验纪律**被复用而非推翻**。缺—须新增**合并规则**与**跨域校验**（孤儿文件 / 缺兜底 / 命名不符），成本已收敛为**纯追加**（新增 IFC 与校验项，不改既有边）。
  - **Option C（目录为「覆盖层」，定义文档仍为唯一真源并保留 `fallback_prompt` 字段）**：优—可渐进迁移。缺—同一「兜底提示词」将**同时存在于**定义文档与目录 → 形成**真实的重叠第二真源**，分歧时无法判定谁对（与 ADR-15 Option A 被拒的理由同源）。**已评估未采纳**。
- **Decision**: **Option B**。**修订后的真源边界（三域显式化）**：
  1. **结构 / 配置域**（持久化态唯一真源）= 定义文档（`IB_DEFINITION_DOC_PATH`）；承载专家**元数据**、路由、编排、工具授权（**不含**主提示词正文）。
  2. **提示词域**（持久化态唯一真源）= 独立 markdown 目录（`IB_EXPERT_PROMPT_DIR`）；承载每专家的**主提示词**与**兜底提示词**正文。
  3. **装配期派生视图**（内存只读、不落盘、不可反写）= 由**两域合并**得出（MOD-IB-16 的派生注册表 + prompt bundle）；进程重启即由两域重建。
  **优先级 / 合并规则（强制）**：① **域不重叠** —— 定义文档**不得**承载主提示词正文，提示词目录**不得**承载专家元数据；真源**按域唯一**，故「第二真源」不成立（原 ADR-15 的「唯一真源」断言**据修订收窄为「按域唯一」**）。② **合并键 = 专家 `name`**（跨域唯一）。③ **主提示词缺失 → 回退兜底提示词**（**兜底恒非空**；见 ADR-29）。④ **孤儿提示词文件**（目录内有、定义文档未登记）→ 装配期**校验拒绝**（`validate_prompt_directory`，IFC-IB-345）。⑤ **有登记但无任何提示词文件** → 允许（用定义文档既有 `fallback_prompt` 字段作为兜底层），记为「**回退生效**」并可观测。⑥ **派生视图仍只读**（ADR-15 Option B 的结论**不变**：不落盘、不得反写文档 / 目录）。⑦ **生效口径** = 保存 + 服务重启重装配（**ADR-32** / C-IB-40）。
- **Consequences**:
  - 正向: 用户裁决（OQ-IB-18 / DR-19）被准确定位为「**新增一个按域划分的持久化载体**」，而非「引入重叠的第二真源」；ADR-14（视图零持久化 + 显式 round-trip）与 ADR-16（装配期 fail-fast）**被复用**；两域均可离线单测（REQ-NFR-IB-19 / AC-IB-18-05 同精神）。
  - 负向: MOD-IB-16 的「唯一真源」措辞须进一步降级为「**装配期派生注册表（由两域合并）**」（`module_design.md` §3 MOD-IB-16 已同步）；须新增跨域合并与校验逻辑（IFC-IB-343 ~ 347）；每次装配须重新合并派生，其耗时上界并入 [TBD-T19] 观测。**overlapping 第二真源被结构性排除**，但**两个持久化载体**并存，故「定义文档即全部配置」的旧心智须更新（写入 §4.R / §4.AC 与 §5.3 说明）。

### ADR-15-R2 兜底层真源的收窄：定义文档交出提示词文本（REV-17 修订子节）

- **Status**: Accepted（REV-17 修订；**本子节为对 ADR-15 的第二次正式修订**，ADR-15 与 **ADR-15-R1** 的既有文本（含 ID / Status / Context / Options / Decision / Consequences 与本子节的 ①~⑦ 规则）**一字不动**；本子节**收窄** ADR-15-R1 规则 ⑤ 中关于兜底层**载体**的那一句，其余六条规则与全部结论**不变**）
- **修订触发**: ADR-15-R1 **Option C 被否决的理由原话**（本文件 §ADR-15-R1 Options，REV-16-2 留痕）——「同一『兜底提示词』将**同时存在于**定义文档与目录 → 形成**真实的重叠第二真源**，分歧时无法判定谁对」。ADR-15-R1 选定 Option B 后，规则 ⑤ 仍以「定义文档既有 `fallback_prompt` 字段」作兜底层，使**同一语义的兜底文本保留了两个可写入口**：定义文档字段（在可编辑白名单内、且被校验强制非空）与目录 `fallback.md`（经 `PUT /api/config/prompts/{expert}/fallback`）。二者分歧时**文件静默胜出** —— 用户在定义文档一侧改完保存成功、却不生效，正是 Option C 被拒的同一病灶以**弱化形态**残留。REV-17 用户裁决：「取消定义文档（承载提示词）——仅仅使用 markdown 文件和兜底提示词。」
- **修订问题**: 在**不取消**定义文档（它继续承载专家元数据 / 路由 / 编排 / 工具授权）、**不引入**运行期热重载（ADR-32 / C-IB-40 / OOS-16）的前提下，兜底层应如何取值，才能使「同一语义只有一个可写载体」成为**结构事实**而非优先级约定；以及「有登记但无任何提示词文件」时兜底从何而来（ADR-15-R1 规则 ⑤ 原以定义文档字段作答）。
- **Options**:
  - **Option A（维持 ADR-15-R1 规则 ⑤ 原状：定义文档字段继续作为兜底层，仅靠优先级规则消歧）**：优—**零改动**，既有 IFC、既有校验、既有配置页字段全部原样复用。缺—**Option C 的病灶未被消除**：兜底文本仍有**两个可写入口**，分歧时靠「文件优先」这一条**约定**判定，而用户在文档一侧看到的输入框是**可编辑且保存成功**的 —— 失败是**静默**的（保存 200、生效无变化）。ADR-15-R1 否决 Option C 的理由「无法判定谁对」在此**并未真正解除**，只是被降级为「谁都不会报错」。**已评估未采纳**。
  - **Option B（兜底层重定位：`fallback.md` 为主 + 代码内置为安全网；定义文档交出提示词文本）** ← **选定**：提示词域（`main.md` / `fallback.md`，`IB_EXPERT_PROMPT_DIR`）成为**唯一的提示词文本可写载体**；代码内置兜底（`ib.experts` 的 `BUILTIN_FALLBACKS` / `BUILTIN_FALLBACK_DEFAULT`）为**不可经界面编辑的安全网**，仅在两层文件皆缺时生效。优—**结构性**消除第二写入口（定义文档 schema 中**不再存在**承载提示词文本的字段，不是「不推荐用它」而是**无处可写**）；ADR-15-R1 的合并键（专家 `name`）、优先级精神（主 > 兜底）与派生视图只读结论**全部保留**；ADR-14（视图零持久化 + round-trip）与 ADR-16（装配期 fail-fast）**原样复用**。缺—**一次性内容哈希变更**（`_semantic_payload` 去掉该字段，所有既有定义文档的 `content_hash` 变化一次，见 Consequences）；旧文档若残留该键须有迁移处置（见 Decision 第 4 条）。
  - **Option C（定义文档保留 `fallback_prompt` 字段但改为只读展示 / 不可写）**：优—用户仍能在文档一侧「看见」兜底文本，观感连续。缺—**同一段文本仍同时存在于两处**，只是其中一处不可改；一旦两者不一致（目录文件被手改、代码内置被升级），**只读展示的就是假信息**，而 `resolved_from` 的可判定性依赖「文本来源唯一」。且 schema 层留字段即为**将来重新开放写入口**埋下位置，纪律靠约定维持。**已评估未采纳**（保留其**可见性**诉求：以「**只读回显**当前生效的代码内置兜底」满足，见 Decision 第 5 条）。
- **Decision**: **Option B**。**收窄后的兜底层真源边界（ADR-15-R1 规则 ⑤ 的修订）**：
  1. **提示词文本的唯一可写载体** = 独立 markdown 目录（`IB_EXPERT_PROMPT_DIR`）的**两层文件**：`main.md`（主提示词，**可缺**）与 `fallback.md`（兜底提示词，**自 REV-17 起亦可缺**）。写入口恰为这两个（`PUT /api/config/prompts/{expert}/main|fallback`）；**不存在**第三个写入口。
  2. **定义文档交出提示词文本** —— `ExpertSpecInput.fallback_prompt` 字段**自 REV-17 起不存在**（移出 schema、移出可编辑白名单 IFC-IB-291、移出定义域校验项）。定义文档回归**纯结构配置**：专家元数据 / 路由 / 编排 / 工具授权。**`ExpertSpec.fallback_prompt`（运行期类型）原样保留** —— 它是**安全网本体**（代码内置，非文档字段），`_prompt_of` / `build_expert` / `fallback_prompts()`（IFC-IB-175）均锚在它上面。
  3. **合并优先序（强制，扩展 ADR-15-R1 规则 ③）**：`main.md` > `fallback.md` > **代码内置兜底**；`resolved_from` 的取值域**第三值由 `definition_doc_fallback` 改为 `builtin_fallback`**（见 ADR-29 修订）。**「兜底恒非空」（ADR-29）自 REV-17 起由结构保证** —— 代码内置兜底是对**任意**专家名都非空的**全函数**（`builtin_fallback_for(name)`：`_DEFAULT_SPECS` 内取该专家专属文本，其外回落 `BUILTIN_FALLBACK_DEFAULT`），故合并结果**不可能**为空，**不再依赖**任何校验放行。
  4. **通用安全网（破「界面新增专家」死锁）**：未登记进 `_DEFAULT_SPECS` 的专家**恒**有非空内置兜底。**死锁原形**：`PUT definition` 新增专家 c 曾要求非空兜底 → `PUT prompts/c/fallback` 又因「专家未登记」返回 404 → 该专家**永远加不进来**。设通用安全网后此路贯通；代价是 `prompt_fallback_missing`（IFC-IB-345 第三类）在正常配置下**不再触发**，语义收窄为「注入的内置兜底映射残缺」的**防御性断言**（见 ADR-36 与 ADR-15-R1 Consequences 的口径同步）。
  5. **可见性不牺牲**：代码内置兜底在配置界面**只读回显**（`GET /api/config/prompts` 的每位专家带 `builtin_fallback`），界面为它**不提供**任何写控件 —— 这是 Feature「用户看得见当前生效的兜底」的满足方式，而非第二写入口。
  6. **旧文档残留键的分级处置**（`document_from_json` 读到 `experts[].fallback_prompt` 时）：与 `builtin_fallback_for(name)` **逐字相同** → **静默丢弃**（零信息损失；生产种子文档正是这一支）；**不同** → **抛 `ConfigError` 并指明迁移目标**（`<root>/<project_id>/<name>/fallback.md`，只报长度不回显正文）。**这是真正的信息损失，必须 fail-closed**，绝不静默丢弃用户手写的提示词。**不 bump `schema_version`**（无迁移机制，bump 会使全部 v1 文档在 `load()` 阶段硬失败 → 服务起不来），改由本条分级处置兜底。
  7. **其余 ADR-15-R1 规则（① 域不重叠 / ② 合并键 = 专家 `name` / ⑥ 派生视图仍只读 / ⑦ 生效口径 = 保存 + 服务重启重装配）与 ADR-15 / ADR-15-R1 的全部结论一字不变。**
- **Consequences**:
  - 正向: **第二写入口被结构性排除**（不是「约定不许写」，而是 schema 里没有该字段）—— ADR-15-R1 否决 Option C 的理由**自此真正成立**；「保存成功却不生效」这一**静默**失败形态从根上消失；兜底层的关系收敛为 `main.md` > `fallback.md` > 代码内置兜底 的**单链**，`resolved_from` 三值（`main_file` / `fallback_file` / `builtin_fallback`）互斥且穷尽。**行为等价性**：生产种子文档的 `fallback_prompt` 本就是 `spec.fallback_prompt` 的直抄（`composition.py` 的 `_default_definition_document`），故删字段后**生效提示词文本零变化**，仅 `resolved_from` 的第三值名称变化（配置页标签文案随之更新）。
  - 负向: ① **一次性内容哈希变更** —— `_semantic_payload` 去掉该键后，所有既有定义文档的 `content_hash` 变化一次；持有旧哈希的会话（如**开着配置页未刷新**）首次保存可能收到 `409` 冲突，须刷新重载（前端已按 AC-IB-17-03 处理，属**已知且可控**的一次性代价，须写入交付说明）。② `prompt_fallback_missing` 从「常见校验失败」降级为「防御性断言」，其触发条件变窄，须在需求侧落盘载体措辞（REQ-FUNC-IB-37 / 38 / 41）与 `module_design.md` 同步，否则留下口径冲突。③ 定义文档的**可编辑字段进一步收窄**，配置界面须提供**指向提示词页**的引导（用户不再能在文档一侧改提示词），此为 UX 事实的变化，须在 §4 说明中登记。④ 代码内置兜底成为**唯一**的「无人配置时的兜底」，其文本质量直接影响开箱体验（安全性优于便利性：宁可回落到通用安全网，不可静默沿用一份用户看不见来源的文本）。

### ADR-16 装配期完备性校验与 fail-fast 准入闸门

- **Status**: Accepted（R7 新增）
- **Context**: REQ-FUNC-IB-27（经可视化配置产生或修改的定义文档须在**装配期**经过**完备性校验**；不通过即**拒绝装配**并给出**可读且定位到具体条目 / 键**的错误；**非法配置不得静默生效**；**不提供**「强制继续 / 忽略错误」开关；**经界面编辑**与**直接编辑文档**两条来源**一视同仁**；校验项至少覆盖 7 类；**不得削弱「默认专家恰好一个」**的兜底前提；错误信息**不回显任何凭据值**；**可离线单测**）；REQ-FUNC-IB-01（配置项缺失 / 非法须在**启动期**可检出）；REQ-NFR-IB-02；US-IB-18 / AC-IB-18-01~06（其中 AC-IB-18-06 明令**不得**「启动成功、直到首次提问才失败」）。外部约束：`agent_platform_research.md` §3.3 P0（在装配期做定义合法性 fail-fast，复用 `validate_specs` 语义）、§4.4 风险 R-4（**不得**以「宽容导入 + 警告后继续」替代）、§4.2 风险 R-2（守住默认专家兜底）。
- **Options**:
  - **A 宽容导入 + 警告后继续**（warn-and-continue）：优—升级 / 试错体验好。缺—**直接违反 REQ-FUNC-IB-27**（不提供忽略开关；非法配置不得静默生效），且与 §4.4 风险 R-4 明确冲突。**已评估未采纳**。
  - **B 首次提问期惰性校验**（首轮问答时才校验并报错）：优—启动更快。缺—违反「时机为**装配期**」与 AC-IB-18-06（不得「启动成功、直到首次提问才失败」）。**已评估未采纳**。
  - **C 装配期单点准入闸门**：定义文档 →（**纯函数**校验器，零编排框架依赖）→ `ValidationReport`；**通过才**进入派生与图编译，**不通过即拒绝装配**；错误逐条定位到 `path` ← **选定**。
- **Decision**: **Option C**。闸门位置 = **组合根装配序列的第一步**（MOD-IB-23，IFC-IB-293），装配序列显式化为：`装载定义文档（IFC-IB-288）→ 准入闸门（IFC-IB-293，内含 IFC-IB-290）→ 派生注册表与图配置（IFC-IB-291）→ 构造并注入（MOD-IB-16/17/19/22）→ 图编译一次常驻`；**任一步失败即启动失败**。校验器为**纯数据层纯函数**（MOD-IB-02，IFC-IB-290；framework-free → 可离线单测，AC-IB-18-05）。校验项枚举（**至少**）：必填项缺失；专家标识 / 面向用户标签唯一性；**默认专家缺失或不止一个**；路由关键词撞车；工具授权引用不存在的工具；路由阈值 / 边界参数越界；条件边分支映射缺失或不可判定。`ValidationReport`（IFC-IB-287）**结构上不存在** `force` / `ignore` / `warn_only` 字段 —— 使「无强制继续开关」成为**类型层事实**而非纪律约定；错误体只出 `path` / `code` / `message`，**不回显任何凭据值**（AC-IB-18-04）。
- **Consequences**: 正向—承接并**具体化** REQ-FUNC-IB-01 / REQ-NFR-IB-02（不构成重复需求）；AC-IB-18-01~06 全部有落点；「界面不豁免」由**同一闸门 + 同一校验器**保证；「绝不无人应答」的兜底前提（默认专家恰好一个）被提升为不可绕过的硬校验（对齐 §4.2 风险 R-2）。负向—校验项枚举须与可编辑对象白名单（IFC-IB-291）**成对维护**，否则出现「可编辑但未校验」死角（列为 GROUP_C 维护约束）；装配期失败会使服务**不可用**（这是**设计意图**：宁可拒绝装配，不可带病运行），其错误可读性由 AC-IB-18-02 把关。

### ADR-17 「可选手动确认中间态」的承载方式与状态丢失语义（R8 新增）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-20（§2.5）末句明确「**可选手动确认中间态**」与「**会话恢复**」两条子条款；用户故事侧已补 **US-IB-20**（AC-IB-20-02 持久化策略须**显式声明**、AC-IB-20-03 机制**存在但默认不启用且不绑定业务语义**、AC-IB-20-04 呈递与决策回传、AC-IB-20-05 **携决策则续跑 / 未携带或状态丢失则 fail-closed**、AC-IB-20-06 归属断言）与 **US-IB-19**（AC-IB-19-01 ~ 05 流式交付契约）。需求原文用「**可选**」与「**机制保留、默认关闭**」表述，并把该点登记为 **OQ-IB-07（仍开放）**。既有架构只给出「机制保留、默认关闭」（§6 会话生命周期段、§10.1）与「状态存于 `SessionStore` 端口、语义 fail-closed」，**未规定**：开关的承载位置、中间态的结构、决策回传的路径、以及「状态丢失」的判定与取值。相关既有决策：**ADR-09**（骨架不见业务语义）、**ADR-11-R1**（SSE 载体与「禁止 `?token=`」纪律）、**ADR-13**（故障与空结果可区分）。**约束**：本 ADR **不得**为满足「确认」而把业务语义引入骨架，**不得**绕过 OQ-IB-07 的开放性（默认必须关闭）。
- **Options**:
  - **A 骨架内置业务确认语义**（参照 FreeArk 的 `interrupt()` 强制确认门）：优—接入方零配置即得确认能力。缺—**违反「不绑定业务语义」与「默认不启用」**（AC-IB-20-03）；把「哪些动作需要确认」这类**业务判定**写进骨架，与 ADR-09 冲突；且 FreeArk 的 `interrupt()` 是**无开关**的强确认门，与 OQ-IB-07 的默认关闭口径相反。**已评估未采纳**。
  - **B 装配期开关（默认关闭）+ 类型化会话状态 + 专用恢复端点 + 状态丢失 fail-closed**：优—开关默认关闭（**不启用即零行为差异**）；中间态以**类型化结构**承载（`ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`），`summary` 文案**由接入方构造**（骨架不生成业务话术，守住 ADR-09）；呈递与回传经**既有 SSE 载体 + 一个专用端点**（复用 ADR-11-R1，不引新依赖）；「状态丢失即 fail-closed」由**纯函数 + 单一取值枚举**在类型层保证（AC-IB-20-02 / 05）。缺—须新增若干契约与一个端点（成本已收敛为**纯追加**）。**选定**。
  - **C 完全下放接入方**（骨架只留一个回调位，其余自建）：优—骨架最薄。缺—**无法满足 AC-IB-20-04 的「呈递与决策回传」**（需求要求该机制在基座内成立），且会诱导接入方**各自实现会话状态**，破坏「唯一入口」与 FM-7 的隔离纪律。**已评估未采纳**。
- **Decision**: **Option B**，并绑定 4 条强制约束：
  1. **默认不启用**：装配期开关 `IB_CONFIRMATION_GATE_ENABLED`（**仅键名**，IFC-IB-304）**默认 `false`**；为 `false` 时**零行为差异**（不发 `confirmation_required`、不写 `gate` 状态、`resume` 不可用）。**OQ-IB-07 保持开放**，本 ADR **不裁决**「是否应默认启用」。
  2. **不绑定业务语义**：骨架**不判定**「哪些动作需要确认」，也不生成确认文案；`ConfirmationPrompt.summary` 为 `str`，**由接入方构造**；`expert_name` 只作定位用。骨架只做「**呈递 + 等待 + 回传**」的通道。该边界与 ADR-09 同构。
  3. **呈递与续跑**：呈递 = 在流内发**一个** `confirmation_required` 事件（`StreamEventKind` **追加**该成员，既有 6 个成员不动，IFC-IB-301）；决策回传 = 新端点 `POST /api/chat/resume`（IFC-IB-307，SSE，`Authorization` 头），**从不新建会话**，只从**已存在的中间态**继续；续跑后仍以 `done` 收束（`done` 之后不再有该次交互的内容片段，AC-IB-19-01）。
  4. **状态丢失 = fail-closed**：持久化策略**必须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`，取值 `in_process` 或 `external`，**v1 默认 `in_process`**；未显式声明即启动期报错）；重启后待确认状态丢弃时，`can_resume`（IFC-IB-306，**纯函数**）必返回 `False`，端点返回 `404` / `409`（**不静默新建、不静默续跑**）；**「安全失败」语义由枚举 `SessionStateLossOutcome` 的唯一取值 `fail_closed_restart_required`（IFC-IB-299）在类型层固定**（与 ADR-13、§7.4 的 fail-closed 口径同精神：宁可明确失败，不可带病继续）。
- **Consequences**: 正向—AC-IB-20-02 / 03 / 04 / 05 与 AC-IB-20-06（归属断言）全部有落点；承接并**具体化** REQ-FUNC-IB-20 的两条子条款，**不新增需求**；「不绑定业务语义」与「默认不启用」成为**契约级事实**而非纪律约定；`external` 持久化只**声明值域**，v1 不引适配器（**零新依赖**），留出可升级路径。负向—新增失败面 `404` / `409`（会话或待确认状态不存在 / 已丢失）与 `403`（归属断言），须在客户端给出可读回执（IFC-IB-308）；会话状态容量与恢复并发**未经实测**，登记为 **[TBD-T21]**；`in_process` 是**刻意保守**的 v1 默认（跨重启不保状态），若接入方要求跨重启续跑，须回到 `external` 值域并另行立项适配器（[ARCH-ASSUMPTION-A8]）。
- **R8 新增说明**: 本 ADR 为**纯追加**；`ADR-01 ~ ADR-16` 的 ID / Status / Context / Options / Decision / Consequences **一字不动**（R8 复核见 §2.0.3）。

### 2.1 ADR-18 ~ ADR-27（REV-13 新增，全文五节齐备）

> 追加式：既有 ADR-01 ~ ADR-17 号 / 名 / 结论一字不动；新增 10 条，每条含 Context（**含 REQ-* 引用**）/ Options（**≥2**，含「已评估未采纳」）/ Decision / Status / Consequences；**无单方案决策**。

---
**ADR-18: 账户/会话子系统的模块落点与数据载体**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-28 / IB-30 / IB-31 / IB-32（账户与会话）[INFERRED 配对以 GROUP_A 包为准]；用户登记 **DR-09**（账户内建于 `ibweb`，不新增服务）、**DR-11**（用户/会话表落在**既有 SQLite 台账**，手写迁移，不引 Django ORM / 新组件）。须遵守「编号即拓扑序」边界纪律（`module_design.md` §1 / §4.2.2）：被组合根 MOD-IB-23 依赖的新工件**不得新开更高编号模块**。
- **Options**:
  - Option A：新增独立鉴权服务进程（对齐 MOD-IB-26 形态）+ 线协议 — 优点: 故障域隔离 — 缺点: 净增第 5 个 systemd 单元与新凭据面，与 C-IB-08 / ADR-03 冲突；凭据跨进程传输净增泄漏面。
  - Option B：新建模块 MOD-IB-27 承载账户数据层 — 优点: 边界清晰 — 缺点: 账户必然被 MOD-IB-23（组合根）依赖，新模块只能取 ≥27 → 产生 `23 → 27` 边，违反 `w(A) > w(B)`，无环证明失效（§4.2.2 已就 MOD-IB-27 先例否决）。
  - Option C：**并入既有模块** —— 契约入 **MOD-IB-01**、键名入 **MOD-IB-02**、SQL 适配器与 bcrypt 入 **MOD-IB-11**（同一 SQLite 文件与同一迁移机制）、端点/解析器/策略模块/装配入 **MOD-IB-23**、前端入 **MOD-IB-24**、迁移/nginx/检查清单入 **MOD-IB-25** — 优点: 零新增模块/边/进程，复用既有边与迁移机制 — 缺点: MOD-IB-11 职责扩展，新增外部依赖 bcrypt。
- **Decision**: 选 **Option C**。理由：同时满足 DR-09（不新增服务）与 DR-11（同一 SQLite + 手写迁移），并保持 DAG 无环（零新增边）；符合 REQ-NFR-IB-11（模块边界）与 C-IB-08（最小组成面）。
- **Consequences**:
  - 正向: 无新进程/单元/组件；复用 ADR-07-R1 的手写 scoped 迁移与 WAL 纪律；组合根仍为唯一装配点。
  - 负向: 账户数据层与文档台账同处 MOD-IB-11，须以表名前缀与仓库内分区隔离；MOD-IB-11 外部依赖新增 bcrypt（宽松许可，须登记）。
---

---
**ADR-19: 会话令牌机制（不透明、服务端存储、过期与续期、无 Cookie）**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-29（会话令牌）[INFERRED]；REQ-NFR-IB-16（会话安全）；**DR-10**（不透明令牌，**仅 `Authorization: Bearer`**，**无 Cookie**）；C-IB-09（`?token=` 一律 4xx）。
- **Options**:
  - Option A：JWT / 自包含签名令牌 — 优点: 无状态、无服务端表 — 缺点: 撤销需黑名单（等价于又一张服务端表）；载荷可读；引入签名库与新密钥面；与「可撤销 + 过期/续期」要求相比无净收益。
  - Option B：**不透明随机令牌 + 服务端会话表（只存摘要）** —— 令牌 = `secrets.token_urlsafe(32)`（stdlib，256-bit 熵）；服务端**只存 `token_digest = sha256(token)`**；校验 `hmac.compare_digest`（常量时间）；过期 `expires_at`；续期 = 显式端点在阈值内滑动；撤销 = 置 `revoked_at` — 优点: 可撤销/可枚举/零额外库；摘要存储使「读到库 ≠ 拿到可用令牌」 — 缺点: 每请求一次索引查询（同库同进程，可控）；过期会话需清理。
  - Option C：Cookie 会话（Django session） — 优点: 浏览器原生 — 缺点: **DR-10 明令禁止**，且重开 CSRF 面。
- **Decision**: 选 **Option B**。理由：可撤销 + 过期/续期 + 零第三方库 + 无 Cookie，直接满足 DR-10 与 REQ-NFR-IB-16；`?token=` 在中间件层一律 4xx（沿用 `forbidden_token_in_query`）。
- **Consequences**:
  - 正向: 撤销/停用/改密可即时失效会话（批量置 `revoked_at`）；令牌原文只在响应体一次性出现，不落库不落日志。
  - 负向: TTL / 续期窗口取值未实测（[TBD-T22]）；过期会话需惰性 + 定期 purge（IFC-IB-315 的 `purge_expired_sessions`）。
---

---
**ADR-20: 口令存储与首登强制改密 / 默认管理员种子**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-30、IB-28 [INFERRED]；REQ-NFR-IB-15；C-IB-09（默认管理员、首登强制改密、**初始口令不得以明文出现在日志/响应/文档**）；**DR-11**（bcrypt）。
- **Options（哈希算法）**:
  - Option A：**bcrypt**（`bcrypt` 库，Apache-2.0） — 优点: 用户登记默认（DR-11）；自带 salt 与 cost；成熟 — 缺点: 单次耗时随 cost 线性增长，CPU-only 目标机须实测。
  - Option B：argon2-cffi — 优点: 现代内存硬参数 — 缺点: 非用户登记，新增库面。
  - Option C：stdlib `hashlib.pbkdf2_hmac` — 优点: 零依赖 — 缺点: 非用户登记；需自管 salt/编码/参数升级，易错。
- **Options（首登强制改密机制）**:
  - Option A：**服务端「改密态」**—— `must_change_password=True` 时签发**受限会话**（服务端标记），中间件对受限会话只放行 `me` / `change-password` / `logout`，其余端点一律 `403 password_change_required` — 优点: **结构上不可绕过**。
  - Option B：仅响应回 `must_change_password: true`，由前端自觉跳转 — 优点: 实现最小 — 缺点: **可绕过**（客户端可忽略标志调用业务端点），违反 C-IB-09「无旁路」。
- **Decision**: 算法选 **Option A（bcrypt，DR-11 用户确认项，本文只登记落点与纪律，不重新裁决）**；机制选 **Option A（服务端强制改密态）**。
- **Consequences**:
  - 正向: 默认管理员种子幂等（`INSERT … ON CONFLICT(username) DO NOTHING`）；初始口令仅经 **0600 EnvironmentFile** 注入（键名 `IB_DEFAULT_ADMIN_PASSWORD`），**代码/文档/日志/响应均无字面量**。
  - 负向: bcrypt cost 未实测（[TBD-T22]）；改密态需在中间件新增**一处**判定（与既有 401/403 口径合并，**不新增授权真源**）。
---

---
**ADR-21: 账户↔项目绑定与角色模型**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-31、IB-32 [INFERRED]；**DR-15**（一运维账户绑定一个项目，**1:1**）、**DR-16**（运维账户全功能 = 等价 `manager`，项目边界内隔离）；用户确认「admin 为全局」。
- **Options**:
  - Option A：在**既有** `AuthzContext(actor_id, project_id, roles)` 上表达 —— admin 账户 `project_id=None`（全局）、`roles=("admin",)`；运维账户 `project_id=<绑定的唯一项目>`、`roles=("manager",)`；登录解析时由会话反查用户得到绑定 — 优点: 零新增授权维度，复用既有 `can_manage` / `can_query`。
  - Option B：新建 ACL 表（账户 × 资源 × 动作） — 优点: 表达力最强 — 缺点: 超 REQ-FUNC-IB-32（1:1）所需，净增表与第二套判定逻辑，违反「单一授权真源」（REQ-FUNC-IB-33）。
- **Decision**: 选 **Option A**。
- **Consequences**:
  - 正向: 权限判定仍**只**经 `can_manage` / `can_query`（IFC-IB-032/033）；运维账户复用 `manager` 语义，边界由 `project_id` 强制（与 FM-7 归属断言同源）。
  - 负向: 1:1 为硬约束 → 一个运维账户无法跨项目；若用户改判为 1:N 须回 GROUP_A（超本轮范围）。

### ADR-21-R1 账户↔项目绑定关系式的收窄：N:1（REV-18 修订子节）

- **Status**: Accepted（REV-18 修订；**本子节为对 ADR-21 的正式修订子节（amend）**，ADR-21 的 ID / Status / Context / Options / Decision / Consequences **一字不动**；本子节**收窄并订正** ADR-21 中「账户↔项目 1:1 绑定」的**关系式歧义**为 **N:1**，ADR-21 的**授权落点与端口结论全部不变**）
- **Context**: 用户裁决（2026-10-07）就 **OI-1**（本文件 §10.1）作出裁定：ADR-21 的「账户↔项目绑定」关系式明确为 **N:1**。关系方既有依据：**DR-15**（一运维账户绑定一个项目）、**OQ-IB-28**（REV-18 裁决：**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**）、**ADR-21**（R13，账户↔项目绑定与角色模型）。**语义裁定**：ADR-21 的「1:1」**以「每账号恰绑一项目」为唯一合法读法** —— 它与 OQ-IB-28 的「1:N」为**同一关系的两侧读法**（账号侧 N → 项目侧 1；反向 1 → N），据此排除「每项目至多一账号」（与 OQ-IB-28 冲突）的歧义读法。既有落点：ADR-40（R18 已按 1:N、零迁移落地，**不**加唯一约束）、`AccountStore`（IFC-IB-310，13 方法一字不动）、`UserRecord.project_id`（单值、可空）。
- **Options**:
  - **Option A（不改 ADR-21，仅在口头 / 单测注释里说明「1:1」读作「每账号恰绑一项目」）**：优—零改动、零迁移。缺—**歧义仍在**：「1:1」在对称语境下可被合法读为「每项目至多一账号」，与 OQ-IB-28 的 1:N 直接冲突；下游（测试门控 / 施工 / 检查清单）须各自解释，口径**不可审计 / 不可回溯**。**已评估未采纳**。
  - **Option B（出 ADR-21-R1 amend 子节，把关系式显式收窄 / 订正为 N:1）** ← **选定**：**ADR-21 正文一字不动**（沿用 ADR-15-R1 / ADR-15-R2 的 amend 先例，**不 supersede**），修订落在本子节；关系式固化为「**每个运维账号恰绑一个项目（N 账号 → 1 项目）；一个项目可有多个运维账号**」。优—歧义被**结构性消除**且**有唯一落点**（可回溯 OQ-IB-28 / DR-15 / ADR-21）；**与既有无 `users.project_id` 唯一约束一致**，**零迁移**；ADR-21 的授权结论（Option A：`AuthzContext(actor_id, project_id, roles)`；admin `project_id=None` 全局）与端口边界**不变**。缺—ADR-21 正文的字面「1:1」仍在，引用该处者须一并标注 **ADR-21-R1**。
  - **Option C（改写 ADR-21 正文，把「1:1」字面直接替换为「N:1」）**：优—字面一致、无二次引用。缺—**违反「编号只增不改」纪律**（ADR-21 为已 Accepted 正文；改写会使 REV-13 的历史留痕失真），且 ADR-15-R1 / ADR-15-R2 已确立「正文一字不动 + amend 子节」先例。**已评估未采纳**。
- **Decision**: **Option B**。**固化后的关系式（N:1）**：**每个运维账号恰绑定一个项目（N 个账号 → 1 个项目）；一个项目可有多个运维账号**。① **数据落点不变**：`UserRecord.project_id`（单值、可空；admin 为 `None`）；**不新增**任何唯一约束（OQ-IB-28「零迁移」）。② **授权落点不变**：仍**只**经 `AuthzContext(actor_id, project_id, roles)` 表达（ADR-21 Option A）；运维账号 `roles=("manager",)`、边界由 `project_id` 强制；admin `project_id=None` 全局。③ **端口不变**：`AccountStore`（IFC-IB-310）方法集一字不动；账号创建的顺序依赖前置校验（目标 `project_id` 须在注册表存在且 `active`，ADR-40 / REQ-FUNC-IB-45）不变。④ **零迁移**：无 DDL 变更、无数据回填。
- **Consequences**:
  - 正向: 「账户↔项目」口径**唯一且可回溯**（本子节 → OQ-IB-28 / DR-15 / ADR-21）；**ADR-21 正文一字不动**（amend 而非 supersede，REV-13 历史留痕完整）；**与既有无 `users.project_id` 唯一约束一致、零迁移**；下游「1:1」引用可统一回链本子节，消除测试门控 / 施工各自解释的风险。
  - 负向: **ADR-21 正文仍保留「1:1」字面**，凡引用该处者**须一并标注 ADR-21-R1**（否则仍可能被误读为「每项目至多一账号」）；本子节为**收窄 / 订正**而非推翻，故**不新增**任何 IFC / 端点 / 迁移足迹。
---

---
**ADR-22: 与既有 `AuthzPolicy` 端口的协作（单一授权真源 / 生产 fail-closed）**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-33 [INFERRED]；C-IB-09（生产未配置 `IB_AUTHZ_POLICY_MODULE` 即 `StartupError`，fail-closed）；既有 `build_authz` 语义（未注入即启动失败，默认 `DenyAllPolicy`）；`src/deploy/checklists.txt` [B9]。
- **Options**:
  - Option A：把内置账户模块**发布为可注入的策略模块** `ibweb.accounts.policy`（暴露 `POLICY` + `resolve_principal(token)`），生产经 `IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy` 指向它；未配置即 `StartupError` — 优点: 授权真源唯一，账户体系是**一个可注入实现**而非特权旁路。
  - Option B：在 `build_authz` 内硬编码内置账户策略并自动启用 — 优点: 开箱即用 — 缺点: **绕开注入 → 第二授权真源**，破坏 fail-closed（REQ-FUNC-IB-33 明令禁止）。
  - Option C：中间件内并行加一套账户判定 — 缺点: 第二真源 + 双判定路径。
- **Decision**: 选 **Option A**。
- **Consequences**:
  - 正向: 判定仍唯一（注入模块）；生产未配置即**拒绝启动**（安全失败）——且是既有 B9 纪律的自然延伸。
  - 负向: 部署**必须**显式设置 `IB_AUTHZ_POLICY_MODULE`，否则服务不启动（写入部署检查清单与 tech_stack §4.5）。
---

---
**ADR-23: 前端重构与路由（Element Plus + Claude 主题；vue-router vs ref 切换）**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-34、IB-35 [INFERRED]；REQ-NFR-IB-17；**DR-13**（Element Plus + 自定义主题，**本地 npm 打包，禁 CDN**）、**DR-17**（中文优先）。既有前端为 `App.vue` 的 ref 式视图切换（`VIEWS`），`package.json` 注释显式声明「刻意不加 UI 组件库」—— **R13 由 DR-13 反转该约定**。
- **Options（路由）**:
  - Option A：保留 ref 式切换 — 优点: 零新依赖、构建最小 — 缺点: 新增登录/首登改密/运维控制台/账户管理/主题后，视图与守卫耦合集中于单组件；无深链接；鉴权守卫无处安放。
  - Option B：引入 `vue-router`（**hash 模式**） — 优点: 路由与 `beforeEach` 守卫（登录态 + 改密态）成为一等结构；hash 模式**不需** nginx `try_files` 回退，部署面更小 — 缺点: 新依赖（MIT）。
  - Option C：`vue-router`（history 模式） — 优点: URL 美观 — 缺点: 需 nginx `try_files` 回退，增部署面。
- **Options（组件库）**: Option A: **Element Plus**（DR-13）+ 自定义 Claude 主题（设计令牌覆写）+ 本地打包 — 优点: 用户拍板、组件齐备。Option B: 自研组件 — 缺点: 成本高，且 DR-13 已拍板。
- **Decision**: 路由选 **Option B（vue-router, hash）**；组件库选 **Option A（Element Plus）**。
- **Consequences**:
  - 正向: 路由守卫使「未登录→登录页」「须改密→改密页」成为结构性约束；主题可切（暗/亮）、中文优先。
  - 负向: 产物体积增长（须实测 [TBD-T23]）；Element Plus 与传递依赖许可须逐包登记（tech_stack §2.2）；既有 `package.json` 的「不加 UI 库」注释须在施工期同步改写。
---

---
**ADR-24: 「粘贴令牌」入口的废除、无旁路，与离线自测令牌的边界**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-28 [INFERRED]；C-IB-09（无旁路）；OQ-IB-15。既有实现：`App.vue` 的 token-paste 门（`v-if="!tokenSet"` / `saveToken()`）与 `main.ts` 的 `?token=` 迁移逻辑。
- **Options**:
  - Option A：**彻底移除**前端令牌粘贴 UI 与 `?token=` 迁移逻辑；登录成为唯一入口；`IB_OFFLINE_MODE=1` 下的既有 `EnvTokenResolver` **仅作离线自测替身**，不进生产装配、不出现在界面 — 优点: 消除「凭据入 URL/日志」同类事故入口。
  - Option B：保留粘贴入口但默认隐藏 — 缺点: 仍存在旁路与凭据面（用户明确要求移除）。
  - Option C：移除 UI 但保留 `?token=` 查询参数兼容 — 缺点: 违反「`?token=` 一律 4xx」硬约束。
- **Decision**: 选 **Option A**。
- **Consequences**:
  - 正向: 登录成为唯一鉴权入口；与 ADR-11 的「凭据不进 URL」纪律合流。
  - 负向: 离线开发须显式 `IB_OFFLINE_MODE=1`，并以离线令牌经**请求头**调用（不经界面）。
---

---
**ADR-25: HTTPS 落点与证书策略**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-36 [INFERRED]；REQ-NFR-IB-16（会话安全）；用户确认「HTTPS 作为部署项」；既有 `ib-web` 绑 `127.0.0.1:18080`（Waitress），systemd 注释已说明「nginx 在前终止 TLS」。
- **Options**:
  - Option A：**nginx TLS 终止**（`ib-web` 仍绑回环，明文仅在回环） — 证书策略：内网自签或内网 CA 签发 — 优点: 与既有 SSE 禁缓冲纪律（`X-Accel-Buffering: no`）合并落地；后端零改动。
  - Option B：Waitress 直挂 TLS — 缺点: Waitress 非为 TLS 终止设计；证书热更与多站点弱。
  - Option C：不启用 TLS（依赖内网） — 缺点: 令牌与口令明文过网，违反 REQ-NFR-IB-16。
- **Decision**: 选 **Option A**。
- **Consequences**:
  - 正向: 后端零改动；SSE 与 TLS 同点收敛于 nginx。
  - 负向: 自签证书需客户端信任导入；证书续期须运维流程（登记为部署检查项）。
---

---
**ADR-26: 迁移 / 种子 / 回滚策略**
- **Status**: Accepted
- **Context**: REQ-FUNC-IB-30 [INFERRED]；C-IB-09；**ADR-07-R1**（手写 scoped 迁移，无 Django ORM / `makemigrations`）；既有 `src/deploy/migrations/`（`001_ledger_init.sql`、`002_chunk_image.sql`）与 `ibweb.bootstrap --ensure-schema`。
- **Options**:
  - Option A：新增**手写前向迁移** `003_accounts.sql`（幂等 `CREATE TABLE IF NOT EXISTS`）+ 幂等种子；回滚 = **代码回滚**（新表纯追加，旧代码忽略之，**无需破坏性 DDL**）。
  - Option B：破坏性重建（drop & recreate） — 缺点: 丢数据，风险高。
  - Option C：改用 Django 迁移 — 缺点: 违反 ADR-07-R1（不经 ORM）。
- **Decision**: 选 **Option A**。编号 **003**（`002` 已被 `chunk_image` 占用）。
- **Consequences**:
  - 正向: 与既有 `ensure-schema` 路径一致；可前向、可安全回滚（回滚不动数据）。
  - 负向: 表结构变更须继续手写 SQL；须以检查清单保证 `ensure-schema` 覆盖新表。
---

---
**ADR-27: 登录失败限速与账户认证审计留痕（条件性 / 可选，待用户确认）**
- **Status**: **Proposed（条件性；OQ-IB-12 / OQ-IB-13 未裁决前不进入施工）**
- **Context**: OQ-IB-12（登录限速阈值）、OQ-IB-13（账户认证审计留痕）；REQ-NFR-IB-16。
- **Options**:
  - Option A：进程内滑动窗口计数器（按 `username` + 来源 IP）达阈值即 `429`；审计以**结构化日志行**（`event=login_failed|login_success|account_disabled`，字段白名单，**不含口令/令牌**）落 MOD-IB-04 — 优点: 零新增表，沿用既有可观测性单一落点。
  - Option B：持久化到台账（`login_attempts` / `auth_audit` 两表） — 优点: 跨重启生效、可查询 — 缺点: 净增两张表。
  - Option C：v1 不做（仅审计日志，不限速）。
- **Decision**: **倾向 Option A，但标记为条件性**：因 OQ-IB-12 / OQ-IB-13 保持开放，本轮**只提供设计**（接口 IFC-IB-326 与键名），**未纳入默认施工范围**；须待 PM / 用户确认后启用。
- **Consequences**:
  - 正向: 为「暴力破解防护」与「认证留痕」预留低摩擦落点（沿用 MOD-IB-04 + 键名登记）。
  - 负向: v1 若不启用，则在 REQ-NFR-IB-16 威胁模型上留下「无速率限制」缺口，须由用户显式接受；阈值取值 [TBD-T22]。
---

---
**ADR-28: 项目上下文的选择与传播（全局管理员「当前项目」与 `X-IB-Project` 契约）**
- **Status**: Accepted
- **Context**: REV-14 回归缺陷修复（R13 引入：全局管理员无法使用任一项目级页面）。REQ-FUNC-IB-31（账户 : 项目 = 1 : 1；**admin 全局**）、REQ-FUNC-IB-32（角色与权限模型：管理员全局 / 运维账户全功能 + 项目边界隔离；AC-IB-24-02 跨项目 403、AC-IB-24-03 admin 不受项目绑定限制）、REQ-FUNC-IB-23（多项目隔离须贯穿全链路）；US-IB-24 / AC-IB-24-03。**已实现的服务端语义**（`src/ibweb/authz.py` `AuthMiddleware.__call__`）：全局主体（`authz.project_id == GLOBAL_PROJECT`，`GLOBAL_PROJECT` 取常量 `"*"`）经 `X-IB-Project` 选定「当前项目」，未选定时沿用全局哨兵，项目级端点因「无匹配项目」而 **fail-closed**（不泄露）——该 fail-closed 是**刻意设计**，本 ADR 不得削弱。**缺口**：前端 `client.ts` 的 `headers()` 从不发送 `X-IB-Project`，且不存在「列出项目」的端点，故 admin 无法选定项目 → 任一项目级页面（问答 / 文件 / 重建 / 可视化配置）不可用（可视化配置返回 `503 定义文档当前不可读（fail-closed）`）。相关既有决策：**ADR-04**（`Scope` 必填、隔离 fail-closed）、**ADR-19**（令牌仅 `Authorization` 头）、**ADR-22**（单一授权真源）、**ADR-24**（无粘贴令牌旁路）。
- **Options**:
  - Option A（**较小改动 / 服务端隐式默认**）：服务端在「全局主体且恰有一个项目」时**隐式**选择该项目，前端不改 — 优点: 单项目部署零前端改动即恢复可用；不改 `client.ts` — 缺点: **多项目部署下语义不成立**（无法判定「当前项目」：任选其一即错、拒绝即失败）；**未满足「admin 必须能显式选择当前项目」的诉求**；前端仍无「当前项目」概念，切换项目时可视化配置等页面无落点。**保留为前端「单项目预选」便利**（见 Decision），**不单独采用**。
  - Option B（**显式选择 + 显式传播**）：新增 `GET /api/projects` 供前端枚举**可见**项目；前端 `projectContext` store 持有「当前项目」；`client.ts` 在**唯一**注入点 `headers()` 向**全部**项目级请求（含 SSE `chatStream` / `chatResume`）附加 `X-IB-Project`；`ops` 锁定为其绑定项目 ← **选定**。
  - Option C（**全局哨兵解析为「全部项目并集」/ 全库检索** — fail-open）：优—前端零改动。缺—**破坏项目隔离**（违反 REQ-FUNC-IB-23 与 §3.3 FM-1），与「未选项目即不泄露」的 fail-closed 纪律**直接冲突**；admin 的每次检索都跨全部项目，泄漏面最大。**已评估未采纳**。
  - Option D（**部署期把 admin 绑定到单一项目**，当作 ops）：优—复用既有 ops 语义。缺—与 **DR-15**（admin 全局）与 **AC-IB-24-03**（admin 不受项目绑定限制）**直接冲突**；多项目部署不可用。**已评估未采纳**。
- **Decision**: 选 **Option B**，并吸收 **Option A 作为纯前端「单项目预选」便利**（**服务端不隐式默认**）。四条强制约束：① **单一注入点** —— `X-IB-Project` 只在 `ApiClient.headers()`（IFC-IB-336）注入，取值只来自 `projectContext` store（IFC-IB-335），**SSE 调用点（`chatStream` / `chatResume`）不重复拼头**（二者已同经 `headers()`）；② **ops 结构上不可切换** —— 项目列表端点对 ops 只返回其自身项目（列表长度恒为 1，IFC-IB-333），叠加后端 `403 project_mismatch`（IFC-IB-334）与前端 `select` 仅 admin 可调用（IFC-IB-335），共三重；③ **fail-closed 纪律不削弱** —— 前端未选择项目时**不发送** `X-IB-Project`，服务端 `effective_project` 取全局哨兵，项目级端点继续 fail-closed（**未选项目 ⇒ 不泄露**）；禁止把哨兵解析为并集（Option C 被拒）；④ **不破坏既有认证契约** —— 令牌仍只经 `Authorization` 头、`?token=` 仍 4xx、零 Set-Cookie、改密态与角色划分不变；`X-IB-Project` **不是**鉴权凭据、**不**替换授权判定（仍唯一经 `AuthzPolicy`，ADR-22）。
- **Consequences**:
  - 正向: 多项目语义正确（admin 可显式选择并切换，ops 不可切换）；**新增端点 `GET /api/projects`** 使「可见项目集合」由服务端裁定（admin 全部 / ops 仅自身），跨项目枚举在 ops 侧结构性不可能；SSE 与普通请求同源注入，覆盖问答 / 文件 / 重建 / 可视化配置**全部**项目级页面；**零新增模块、零新增依赖边**（沿既有 `MOD-IB-24 → MOD-IB-23` HTTP 边）；「未选项目即不泄露」的 fail-closed 保持为架构事实。
  - 负向: 前端净增一个 store（IFC-IB-335）与一处注入点扩展（IFC-IB-336）；**切换当前项目后必须重置项目内视图态**（会话历史 / 文件列表 / 可视化草稿），否则可能出现「旧项目数据显示在新项目下」的**串项显示**风险——登记为施工要点（GROUP_C）；`GET /api/projects` 引入「项目枚举」这一新的读面，须以「ops 仅见自身」避免横向枚举（IFC-IB-333）。**需求侧无独立 REQ / AC 覆盖「项目选择 UX 与项目枚举端点」**，已登记为 **OPEN ITEM**（见 §10.1 R14 行；按纪律**不发明需求**，downstream 需 GROUP_A 澄清）。
- **R14 新增说明**: 本 ADR 为**纯追加**；`ADR-01 ~ ADR-27` 的 ID / Status / Context / Options / Decision / Consequences **一字不动**（R14 复核见 §2.0.5）。
---

### ADR-29 专家提示词的**主 / 兜底分层**与回退语义

- **Status**: Accepted（REV-16-2 新增）
- **Context**: REQ-FUNC-IB-37（提示词**不仅限于兜底提示词**；主 / 兜底**分层并存**，主提示词缺失时回退兜底 —— 用户裁决 2026-10-06，OQ-IB-17 / DR-19）；REQ-FUNC-IB-38（提示词可视化编辑与保存）；REQ-FUNC-IB-41（可经文件保存）；REQ-NFR-IB-19（一致性 / fail-safe）。既有落点：MOD-IB-16（专家派生注册表，IFC-IB-171~179）、MOD-IB-20（LLM 端点抽象）、MOD-IB-23（装配序列）。**约束**：不得使「主提示词缺失」导致**空白系统提示词**（须回退兜底）；兜底提示词**恒非空**（AC-IB-30-03 / 30-06 定性口径）。
- **Options**:
  - **Option A 单一提示词字段**（沿用既有 `fallback_prompt` 一个字段）：优—零改动。缺—**直接违反 REQ-FUNC-IB-37**（不得把「提示词」等同于「兜底提示词」）。**已评估未采纳**。
  - **Option B 主 / 兜底**两字段**分层并存 + 主缺失回退兜底** ← **选定**：`ExpertPromptBundle.main_prompt: str | None` 与 `fallback_prompt: str`（**非空**）；装配期合并时 `effective_prompt = main_prompt if main_prompt else fallback_prompt`，**永不空白**；`resolved_from` 记录取值来源（`main_file` / `fallback_file` / `definition_doc_fallback`；**REV-17 修订**：第三值更名为 **`builtin_fallback`** —— 兜底层载体由定义文档字段移出，见 **ADR-15-R2**）以支持可观测。优—完全满足 IB-37；分层语义清晰；回退为**纯函数**可离线单测。缺—须新增两字段与回退逻辑（成本已收敛为纯追加）。
  - **Option C 主提示词**替换**兜底**（二选一，不并存）**：优—语义最简。缺—**违反用户裁决「分层并存」**（OQ-IB-17）。**已评估未采纳**。
- **Decision**: **Option B**。`PromptLayer = Literal["main","fallback"]`（IFC-IB-337）；`ExpertPromptBundle`（IFC-IB-338）；回退纯函数 `load_prompt_bundle`（IFC-IB-343）；派生注册表扩展 `prompt_bundles()` / `main_prompts()`（IFC-IB-349）。**兜底恒非空**由装配期校验（IFC-IB-290 扩展）保证。**（REV-17 修订）** 自 REV-17 起「兜底恒非空」改由**结构**保证 —— 代码内置兜底是对**任意**专家名都非空的**全函数**（`builtin_fallback_for` / `builtin_fallbacks_for`，**IFC-IB-365**），故 `merge_prompt_layers` 的合并结果**不可能**为空，**不再依赖**任何校验放行（见 **ADR-15-R2** 规则 ③ 与 **ADR-36**）。原「由校验保证」的措辞在 REV-17 后仅为**冗余的第二道防线**（`prompt_fallback_missing` 降级为防御性断言）。
- **Consequences**: 正向—IB-37 的定性口径全部有落点；「绝不空白系统提示词」成为**结构事实**（`effective_prompt` 恒非空）。负向—须维护「主 / 兜底 / 回退来源」三态语义，并在前端呈现（IFC-IB-354）；派生注册表增加一个键（不影响既有 `fallback_prompts()` 语义 —— 其仍返回兜底层）。

### ADR-30 工具授权的**勾选式配置**与**工具参数可配**（不新增工具本体）

- **Status**: Accepted（REV-16-2 新增）
- **Context**: REQ-FUNC-IB-39（对**既有工具集**的**授权勾选** + **工具参数可配**，如 top_k / 阈值；**不含新增 / 自定义工具本体** —— 用户裁决 2026-10-06，OQ-IB-19 / DR-19 / OOS-14）；REQ-FUNC-IB-03（工具注册与能力声明自动派生）；REQ-NFR-IB-19。既有落点：MOD-IB-17（工具注册与能力摘要，IFC-IB-181~183）、MOD-IB-15（`RetrievalService.search` 的 `top_k` / `score_threshold` 参数）、`ToolGrantSpec`（IFC-IB-287 内，字段 `expert_name` / `tool_names`）。**约束**：工具本体由代码登记，**运行期不得新增**；参数须**校验**（越界 / 类型不符 / 未知参数 / 未授权工具带参 → 拒绝）；须与「专家 - 工具最小授权」口径一致。
- **Options**:
  - **Option A 仅授权勾选**（沿用 `tool_names`，不支持参数）：优—零改动。缺—**不满足**「工具参数可配」（OQ-IB-19）。**已评估未采纳**。
  - **Option B 授权勾选 + 类型化工具参数（带 spec 与校验）** ← **选定**：授权以 `tool_names` 勾选承载（既有字段语义不变）；参数以**加成式扩展**承载 —— `ToolGrantSpec` 增列 `param_values: tuple[ToolParamValue, ...]`（**其既有文本一字不动**，沿用 IFC-IB-282 / 324 的「加成式扩展」先例）；每个工具的**可配参数**由 `ToolParamSpec`（类型 / 默认 / 上下界 / 枚举）声明；装配期由 `validate_tool_params`（IFC-IB-346）校验，越界 / 未知即**拒绝装配**（复用 ADR-16 闸门）。**不新增工具本体**：`register_tool`（IFC-IB-181）仍为唯一登记入口，运行期无新工具面。优—满足 IB-39；参数可配且**受类型约束**；不破坏最小授权。缺—须维护工具参数 spec 与校验（纯追加）。
  - **Option C 允许新增 / 自定义工具本体**：优—扩展性最强。缺—**明确排除**（OQ-IB-19 / OOS-14）；会引入运行期新工具面与安全面。**已评估未采纳**。
- **Decision**: **Option B**。`ToolParamSpec` / `ToolParamValue`（IFC-IB-340）；`validate_tool_params`（IFC-IB-346）；装配 `build_authorized_tools` / `validate_grants`（IFC-IB-350）。**工具本体仍由代码登记**，本 ADR **不提供**任何新增工具本体的路径。
- **Consequences**: 正向—IB-39 全部有落点；「无新增工具本体」由**不提供该接口**成为结构事实；参数越界在**装配期**被拒（fail-fast）。负向—`ToolParamSpec` 的枚举须与各工具实现**成对维护**（列为 GROUP_C 约束）；前端须为参数生成表单（IFC-IB-354）。

### ADR-31 FreeArk **严格对齐（含专家名）**、改名处置与**聚合禁止标签**派生

- **Status**: Accepted（REV-16-2 新增）
- **Context**: REQ-FUNC-IB-42（示例项目专家定义与 FreeArk 专家 **100% 对齐**；用户裁决「**严格对齐，含专家名**」—— OQ-IB-20 / DR-19）；OQ-IB-23（示例项目 = `demo`）；C-IB-01（FreeArk **只读**）。FreeArk 权威真源（只读）：`FreeArk:FreeArkWeb/backend/freearkweb/api/langgraph_chat/experts.py`（`ExpertSpec` 与 `EXPERT_SPECS`）、`…/agents/<name>/SYSTEM_PROMPT.langgraph.md`（主提示词）、`semantic_router.py` 的 exemplars、`fa_tools.py` `TOOLS_BY_EXPERT`、`orchestrator.py` `DELEGATION_TOOLS_BY_EXPERT`。基座现状：`src/ib/experts/__init__.py` 的 `_DEFAULT_SPECS`（专家名 `data-expert` / `inspection-expert` / `knowledge-expert`）；`src/ib/orchestration/__init__.py` 的 `AGGREGATION_FORBIDDEN_LABELS`。**约束**：对齐落实为**可核验的逐字段比对清单**；FreeArk **全程只读**（不改其任何文件）。
- **Options**:
  - **Option A 弱对齐**（仅对齐字段**结构**，不强制取值，保留基座自造专家名）：优—与「业务不入基座」零张力。缺—**违反「严格对齐，含专家名」**（OQ-IB-20）。**已评估未采纳**。
  - **Option B 严格对齐 = 逐字段取值对齐（含 `name` / `cn_label`），工具集合按「工具名」对齐，工具参数排除** ← **选定**。**10 维比对表**（9 维专家定义 + 1 维工具映射）：

    | # | 维度 | FreeArk（只读真源） | 基座现状 | 对齐动作 |
    |---|------|---------------------|----------|----------|
    | 1 | `name` | `freeark-expert` / `inspection-expert` / `sanheng-knowledge` | `data-expert` / `inspection-expert` / `knowledge-expert` | **改名**（含专家名） |
    | 2 | `cn_label` | `系统管家` / `巡检诊断` / `三恒知识` | `数据管家` / `巡检诊断` / `知识库问答` | **改名** |
    | 3 | `keywords` | 三组关键词 | 三组关键词 | 逐项对齐 |
    | 4 | `is_data_expert` | true / true / false | true / true / false（同） | 逐位对齐 |
    | 5 | `fallback_prompt` | 三段兜底文本 | 三段兜底文本（`_DEFAULT_SPECS[].fallback_prompt` = **代码内置安全网**，`BUILTIN_FALLBACKS`） | 逐字对齐（**REV-17 口径澄清**：对齐**不再**经定义文档字段 —— 该字段已移出 schema；对齐落在 `ib.experts` 内置兜底常量上，即 ADR-15-R2 的 `main.md > fallback.md > 代码内置兜底` 中**最末一层**。取值文本不变） |
    | 6 | `is_delegating` | true / true / true | true / true / true（同） | 逐位对齐 |
    | 7 | `is_default` | true / false / false | true / false / false（同） | 逐位对齐 |
    | 8 | `exemplars` | `semantic_router.py` 自 `routing_eval/dataset.jsonl` | 定义文档 `exemplars` 字段 | 逐项对齐 |
    | 9 | 主提示词 | `agents/<name>/SYSTEM_PROMPT.langgraph.md` | 基座**无主提示词** | **新建能力**（= ADR-29；以 FreeArk 提示词全文作为示例项目主提示词；**全文不复制进本仓设计文档**，仅施工期自只读源导入） |
    | 10 | 工具集合（**按工具名**） | `TOOLS_BY_EXPERT` / `DELEGATION_TOOLS_BY_EXPERT`：freeark-expert→能耗+人格(+委托知识)；inspection-expert→巡检(+全委托)；sanheng-knowledge→三恒检索(+委托读) | `tool_grants[].tool_names` | **按工具名对齐** |
    | 10' | 工具**参数** | **FreeArk 无 per-expert 工具参数真源** | `ToolParamSpec` / `param_values` | **不参与对齐（显式排除项）** —— 工具参数是**唯一无法对齐的维度** |

  - **Option C 严格对齐 + 为消除改名影响而**同时强化**聚合禁止标签的静态清单**（只把新名加入硬编码）：优—改动局部。缺—仍是**静态硬编码业务中文名**，与 ADR-09「骨架不见业务语义」冲突，且每次改名都要重复改；`AGGREGATION_FORBIDDEN_LABELS` 现状已含 `系统管家`（改名后将成为**合法专家标签**）并**缺** `数据管家`。**已评估未采纳**（作为**过渡措施**保留，见 Decision）。
- **Decision**: **Option B**，并**一并裁定 `AGGREGATION_FORBIDDEN_LABELS` 的处置**（见包 §5.3）：
  1. **示例项目（`demo`）专家集按 10 维逐字段对齐**（工具参数为显式排除项）；对齐产物为 `demo` 的默认专家集（OQ-IB-23）。
  2. **改名落点**（约 41 处命中：专家名 ~36 + `cn_label` ~5）：`name` 与 `cn_label` 依 10 维表改名；**FreeArk 只读，不改其任何文件**。
  3. **`AGGREGATION_FORBIDDEN_LABELS` 目标形态 = 由活体专家注册表派生的只读视图**（`forbidden_labels(cn_map)`，IFC-IB-351，落点 MOD-IB-22）；符合 ADR-09（骨架不硬编码业务语义）。
  4. **过渡措施（本增量落盘后、重构前，属 GROUP_C 施工要点，本包只登记，不改 `src/`）**：硬编码清单**暂时**改为「**旧 ∪ 新**」label 的并集（`系统管家` / `巡检诊断` / `知识库问答` / `数据管家` / `三恒知识`），确保 AC-IB-09-03「不得暴露内部分工」**不回退**。**禁止只换名**（只删旧名或只加新名都会造成漏网或误伤）。
- **Consequences**: 正向—IB-42 有可核验清单；「工具参数为唯一不可对齐维」被显式排除，避免伪造对齐；`AGGREGATION_FORBIDDEN_LABELS` 的债务被显式登记并有目标形态。负向—**改名会在示例项目引入 FreeArk 业务中文名（`系统管家` / `三恒知识`）与业务工具名（ENERGY / PERSONA / INSPECTION / SANHENG）**，与 **OOS-04 / OOS-11（FreeArk 业务不入通用基座）存在张力**（**已登记为需 PM / 用户注意项，见包 §7**）；在重构完成前，禁止标签须**双名并存**（过渡态）。

### ADR-32 配置**生效口径**：保存 + 服务重启重装配（不引运行期热重载 / 不重编译图）

- **Status**: Accepted（REV-16-2 新增）
- **Context**: REQ-FUNC-IB-40（提示词与工具授权**保存并经服务重启后生效**；用户裁决 2026-10-06，OQ-IB-16 / OQ-IB-21 / DR-19 / **C-IB-40** 时效纪律）；OOS-16（**显式移出**「无需重启即生效 / 运行期热重载 / 跨进程无重启热传播」类验收）；**C-IB-38**（生产重启须**用户手工执行**）；REQ-FUNC-IB-26 ②（运行期**不得**改变图拓扑）。既有落点：MOD-IB-23 装配序列（IFC-IB-293）、MOD-IB-22（图编译一次常驻）。
- **Options**:
  - **Option A 运行期热重载 + 热重编译图**（保存即重建派生注册表与图）：优—即时生效。缺—**直接违反 C-IB-40 / OOS-16**（无重启热重载被移出验收范围）；运行期重编译图违反 REQ-FUNC-IB-26 ②；且引入并发装配 / 半更新态风险。**已评估未采纳**。
  - **Option B 保存落盘 + 服务重启（用户手工）重装配** ← **选定**：保存仅**原子落盘**（定义文档 / 提示词目录），**不**运行期重建；新配置在**下次装配**（`ib-web` / `ib-worker` 重启，用户手工执行）时生效；图**编译一次常驻**，重启方能换拓扑。优—与 C-IB-40 / OOS-16 / REQ-FUNC-IB-26 ②**全部一致**；装配语义与既有单点闸门（ADR-16）同源；无并发装配风险。缺—生效有延迟（须重启）；须在界面**显式提示**「保存后重启生效」且**不静默**（IFC-IB-354）。
  - **Option C 保存即生效但不重编译图**（只重载提示词 / 参数，不换拓扑）：优—部分即时。缺—仍属「运行期热重载」，与 C-IB-40 字面冲突；且 `ib-web` / `ib-worker` 双进程一致性无保证（OOS-16 ②③）。**已评估未采纳**。
- **Decision**: **Option B**。保存端点仅原子落盘；**装配序列**显式扩展为：`装载定义文档（IFC-IB-288）→ 装载独立提示词目录（IFC-IB-345）→ 跨域合并 + 完备性校验（IFC-IB-290 扩展 + 345 + 346）→ 准入闸门（IFC-IB-293）→ 派生注册表 / 图配置（IFC-IB-291 扩展，含 347 + 349）→ 构造并注入 → 图编译一次常驻`（IFC-IB-353）。**任一步失败即启动失败**。**不提供**任何运行期热重载 / 热重编译入口。
- **Consequences**: 正向—C-IB-40 时效纪律被架构层承接；「不重编译图」与既有 ADR-16 / REQ-FUNC-IB-26 ② 一致；生效语义可测（离线验证保存后重建装配即得新配置）。负向—生效须用户手工重启（C-IB-38）；界面须显式提示以免「以为已生效」（IFC-IB-354 强制）。

### ADR-33 保存期「工具参数 / 跨域完备性」校验的落点（保存路径 = 装配路径的单校验入口）

- **Status**: Accepted（REV-16-4 新增）
- **Context**: **DEFECT-R16-02**；**AC-IB-30-04 / AC-IB-31-03**（保存被完备性 / 授权校验拒绝 + **既有在用配置保持不变**）；REQ-FUNC-IB-39（工具参数可配）；REQ-NFR-IB-19（fail-safe）。既有落点：IFC-IB-290（`validate`，纯函数）、**IFC-IB-346**（`validate_tool_params`，纯函数）、IFC-IB-295（`PUT /api/config/definition`）。**事实（一手核实）**：保存路径仅调 `store.validate()`（IFC-IB-290，`views.py:891`），**未**调 IFC-IB-346；装配路径 `admit_two_domains`（`composition.py:823 / 826`）**两者皆调** → 两路径**校验集发散**，非法工具参数保存返回 `200` 并**覆盖在用配置**，违反 fail-safe。
- **Options**:
  - **A 改 `validate()` / `store.validate()`（IFC-IB-290）签名加可选 `tool_param_specs`**：优—单入口。缺—**改动既有 IFC-IB-290 签名文本（违反本轮「既有 IFC 一字不动」铁律）**；须同步枚举全部调用点（生产 4 处 + 离线自检 10+ 处），**漏一处即静默放行**（缺陷原地复发）。**已评估未采纳**。
  - **B 视图层补调一次 `validate_tool_params`**：优—零改既有 IFC、改动最小。缺—领域校验散进 HTTP 层；校验集仍由「视图是否记得调」维系数，**未结构性消除发散根因**。**已评估未采纳**。
  - **C（选定）MOD-IB-02 新增合成纯函数 `validate_definition_full`（IFC-IB-355）= IFC-IB-290 ∪ IFC-IB-346；保存路径（IFC-IB-295）与装配路径（`admit_two_domains`）共用**：优—**单校验入口**，结构性消除两路径发散；**不改任何既有 IFC 号 / 名 / 签名 / 字段集**；校验仍在 framework-free 纯函数层（= 需求源锚点 `definition.py`）。缺—视图与装配各改 1 处调用（GROUP_C 施工）。
- **Decision**: **Option C**。`validate_definition_full` 为**唯一**校验入口；`PUT /api/config/definition` 落盘前调用之；装配期同调之。`ValidationReport` **仍不含** `force` / `ignore` / `warn_only`。**（REV-17 修订 · 单入口范围扩及提示词域）**：该单入口**上提一级**为 **`validate_two_domains`（IFC-IB-364）= `validate_definition_full`（IFC-IB-355）∪ `validate_prompt_directory`（IFC-IB-345）**，覆盖**三个域且顺序固定**（定义域 → 工具域 → 提示词域）；保存路径（IFC-IB-295）与装配路径（`admit_two_domains`）**共用同一合成入口**，回执的校验项**逐条同序、同码、同路径**。理由：REV-17 之前**提示词域只在装配期查**，故「页面上存得下、重启装配才炸」是可能的 —— 这正是本 ADR 要消除的发散根因在**提示词域上的残留**（ADR-15-R2 的失败形态）。**不改** `validate_definition_full` 的号 / 名 / 签名（其被既有测试以 `getsource` 扫描）。
- **Consequences**: 正向—AC-IB-30-04 / AC-IB-31-03 的 fail-safe 可验证；**根因（两路径校验集发散）被结构性消除**（REV-17 后**含提示词域**）；编号纪律未破。负向—新增 1 个合成入口（REV-17 再增 1 个更上层的合成入口，纯追加），须在文档纪律上维持「保存 = 装配」等价（由单函数保证）；GROUP_C 须同步改 `views.py` 与 `composition.py` 两处调用点。

### ADR-34 配置「保存 / 生效」的**可查询记录**载体（只读审计；非第二真源）

- **Status**: Accepted（REV-16-4 新增）
- **Context**: **GAP-R16-04**；**REQ-NFR-IB-19**（保存与生效应可观测：**谁 / 何时 / 改了哪些字段 / 结果**）；**AC-IB-32-02**；REQ-NFR-IB-06（可观测，含字段白名单与脱敏）。既有落点：MOD-IB-04 `log_event`（**现缺 actor 与 changed_fields**）；MOD-IB-11 同一 SQLite + 手写迁移（`001` / `002` / `003`）；R13 先例（账户并入同一 SQLite）。**硬约束**：本记录**不得成为第二真源**（只读审计，**不得写回配置**）。
- **Options**:
  - **A 仅复用 MOD-IB-04 结构化日志**：优—零新表 / 端口。缺—`log_event` 无 actor / changed_fields；日志面向文件，**不易经端点查询**，轮转后不可查 → 不满足「可查询的记录」。**已评估未采纳**。
  - **B 追加式 JSONL 审计文件**：优—append-only，无迁移。缺—多进程并发追加须额外锁；查询须自建索引；与既有 SQLite 台账风格不一致。**已评估未采纳**。
  - **C（选定）同一 SQLite 新表 `config_audit`（手写迁移 `004_config_audit.sql`）+ 只读端口 `ConfigAuditStore`（IFC-IB-357，**2 方法，无 update / delete**）+ 只读端点 `GET /api/config/audit`（IFC-IB-359）**：优—真 SQL 查询 + 索引；跨重启持久；沿用 R13「同一 SQLite + 手写迁移」先例与 WAL / busy_timeout 纪律；**方法集在类型层排除写回配置**。缺—新增 1 表 + 1 迁移 + 1 端口（纯追加面）。
- **Decision**: **Option C**。**写入时机**：成功与失败**均记录**（`result ∈ {"saved","rejected"}`；`rejected` 附 `detail_code`，**只出字段名 / 码，不出现取值**）；顺序 = **校验 → 原子落盘 → 审计写**。**与 fail-safe 的关系（决策 + 理由）**：审计写与配置写**非事务耦合**、**审计写失败不改变保存结果**（保存成功仍 `200`），但**不静默** —— 发结构化 `WARN config_audit_write_failed`（字段白名单）；理由：REQ-NFR-IB-19 的 fail-safe 旨趣是「保存失败不得破坏在用配置」，而非「可观测性故障须回滚已成功的保存」；若令审计写失败使保存失败（fail-closed），日志 / DB 抖动将**阻断合法配置变更**，且原子文件已写，事后回滚反增损坏面。**残余风险（登记）**：存在「保存成功但记录缺失」的有界窗口。
- **Consequences**: 正向—AC-IB-32-02 可验证；「谁 / 何时 / 改了哪些字段 / 结果」四要素齐备；**「非第二真源」为类型层事实**（端口无 update / delete；无配置读取路径消费审计；`ConfigAuditEntry` 不含配置取值）。负向—新表增长与**保留策略未由需求规定**（登记 [ARCH-ASSUMPTION-A11] / [TBD-T25]）；审计写失败时可查询性存在有界缺口（见 Decision）。**「生效」口径**：按 **ADR-32**，「生效」= 下次装配（用户手工重启），**非运行期事件** —— 本记录是**保存事件**的记录，**不发明**运行期「生效事件」。

### ADR-35 「内存态生效」提示的暴露（只读 storage-state 端点；不改变生效口径）

- **Status**: Accepted（REV-16-4 新增）
- **Context**: **GAP-R16-03**；**AC-IB-33-02**（定义文档存储**未启用**时须**明确提示**「配置仅内存生效、不跨重启保留」，**不静默丢失**）；AC-IB-33-01 / 33-03。**事实（一手核实）**：`build_definition_store`（`composition.py`）在非离线且**未配置 `IB_DEFINITION_DOC_PATH`** 时返回 `InMemoryDefinitionDocumentStore`（**重启重播种、配置页改动丢失**），仅 `log_event(...path_not_configured_using_in_memory_default...)`，**未向界面暴露**；**生产目标机当前正处该态**。**硬约束**：**不改变** REV-FUNC-IB-40「重启后生效」语义（**OOS-16 / C-IB-40 不变**）。
- **Options**:
  - **A 合并进既有配置读取响应**（IFC-IB-294 / IFC-IB-352 各追加 `storage_mode`）：优—零新端点，加载即显示。缺—须在**两处**既有响应上加成式扩展；两编辑器都要显示 → 字段重复。**已评估未采纳**。
  - **B（选定）新增只读端点 `GET /api/config/storage-state`（IFC-IB-362）→ `200 StorageState`（IFC-IB-361：`definition_store` / `prompt_store ∈ {memory,file}` + 两处是否已配置的布尔）**：优—**单一类型化真源**，definition / prompt 编辑器共用；**不扰动** IFC-IB-294 / IFC-IB-352 字段集；字段名与值域显式登记。缺—多一次轻量读请求。
- **Decision**: **Option B**。前端（MOD-IB-24，**IFC-IB-363**）在任一 `mode == "memory"` 时渲染**非静默**提示「**配置仅内存生效、不跨重启保留**」。**语义声明（强制）**：本决策**仅增加可观测提示**，**不改变** REV-FUNC-IB-40 生效口径（保存 + 服务重启重装配；ADR-32 / C-IB-40 / OOS-16）；**不引入**运行期热重载；**不改变**「未配置 `IB_DEFINITION_DOC_PATH` → 内存态」的既有装配语义（**仅暴露**）。
- **Consequences**: 正向—AC-IB-33-02 可验证；**GAP-R16-03 闭合**；提示与生效口径解耦（纯可观测）。负向—storage-state 端点须与装配期实际选用的存储实现**单一来源**（由 IFC-IB-362 直读装配结果保证）；该提示**不修复**内存态本身（是否配置 `IB_DEFINITION_DOC_PATH` 仍由用户手工决定，AC-IB-33-02 明文）。

### ADR-36 提示词兜底层的重定位：文件两层 + 代码内置安全网（无第二可写入口）

- **Status**: Accepted（REV-17 新增）；**修订关系**：本 ADR 是 **ADR-15-R2**（amend 子节）的**决策本体**，与 ADR-15-R1（分域真源 + 装配期合并）**承接而非推翻** —— 合并键、合并方向、派生视图只读结论全部保留，只把**兜底层的载体**由「定义文档字段」换为「代码内置常量」。
- **Context**: **REQ-FUNC-IB-37**（提示词主 / 兜底分层并存，主缺失回退兜底）、**REQ-FUNC-IB-38**（提示词可视化编辑与保存）、**REQ-FUNC-IB-41**（可经文件保存）、**REQ-NFR-IB-19**（一致性 / fail-safe）；**C-IB-39**（触发 ADR-15 修订的约束）；用户裁决（2026-10-07，REV-17）：「取消定义文档（承载提示词），仅仅使用 markdown 文件和兜底提示词。可视化配置可以对 markdown 进行 CRUD、加载、保存、生效。」**两条一手核实的事实**（构成本 ADR 的缺陷前提）：
  1. **同一兜底语义存在两个可写入口** —— 定义文档 `experts[].fallback_prompt`（在可编辑白名单 IFC-IB-291 内，且被定义域校验强制非空）与目录 `fallback.md`（`PUT /api/config/prompts/{expert}/fallback`）；装配期合并时**文件静默胜出**，用户在文档一侧保存成功（`200`）而**生效无变化**。这正是 ADR-15-R1 否决 Option C 的理由原话所指的病灶（「形成真实的重叠第二真源，分歧时无法判定谁对」）以**弱化形态**残留。
  2. **配置页编辑的提示词从未进入 system 消息** —— 合并结果经 `_prompt_of` → `_expand_plan` → `_fan_out` → `_run_expert` 被拼成 `f"{prompt}\n\n用户问题：{query}"` 走 **human** 前缀；system 位恒为 `spec.fallback_prompt`（代码内置）。`build_expert` 的 docstring 声称存在「主提示词经 `system_prompt` 覆盖」的形参，**该形参不存在、全仓无调用方** —— 是**假陈述**，使「主 / 兜底分层」在运行期**名不副实**。
  既有落点：ADR-29（主 / 兜底分层）、ADR-15-R1（分域真源 + 合并）、MOD-IB-16（专家派生注册表，IFC-IB-171~179）、MOD-IB-20（LLM 端点抽象）、MOD-IB-23（装配序列）。
  **本 ADR 的约束**：① 不取消定义文档（它继续承载专家元数据 / 路由 / 编排 / 工具授权）；② 不引运行期热重载（**ADR-32** / C-IB-40 / OOS-16）；③ **不 bump `schema_version`**（无迁移机制，bump 会使全部 v1 文档在 `load()` 阶段硬失败 → 服务起不来）；④ 既有 IFC 编号 / 名 / 签名一字不改。
- **Options**:
  - **Option A 维持现状（规则 ⑤ 原状），仅补「保存成功却不生效」的提示**：优—零结构改动。缺—**只治症状**：第二写入口照旧存在，用户仍可在定义文档一侧改一段**永远不会生效**的文本；界面需要额外维护「这个框其实没用」的说明，与 ADR-14「视图是文档的忠实视图」直接冲突。**已评估未采纳**。
  - **Option B（选定）兜底层 = 文件两层 + 代码内置安全网；定义文档交出提示词文本**：提示词文本的**唯一可写载体** = 目录 `main.md` / `fallback.md`；**不可编辑的安全网** = `ib.experts` 的 `BUILTIN_FALLBACKS`（由 `_DEFAULT_SPECS` 派生的模块级常量，import 时求值）/ `BUILTIN_FALLBACK_DEFAULT`（通用兜底），经 `builtin_fallback_for(name)` / `builtin_fallbacks_for(names)`（**IFC-IB-365**）取值。优—**结构性**排除第二写入口（schema 中不存在承载提示词文本的字段）；「保存成功却不生效」的**静默**失败形态消失；兜底层关系收敛为**单链**；`resolved_from` 三值互斥且穷尽。缺—一次性内容哈希变更；须新增 legacy 键分级处置。
  - **Option C 定义文档保留字段但标记为只读 / 不可写**：优—界面观感连续。缺—**同一段文本仍两处存在**，一旦分歧，只读展示的即**假信息**；schema 留位等于为**将来重开写入口**预留位置，纪律退化为约定。**已评估未采纳**。
  - **Option D 把提示词文本整体迁入数据库（与账户 / 审计同库）**：优—与既有 SQLite 台账统一。缺—**用户明确要求 markdown 文件**（REQ-FUNC-IB-41「可经文件保存」+ 本 ADR Context 的用户裁决原话）；DB 化会使提示词的 diff / 版本管理等文件态优势全部丧失；且违背 ADR-15-R1 已选定的「独立 markdown 目录 = 提示词域真源」。**已评估未采纳**。
- **Decision**: **Option B**。四条落地决定：
  1. **合并（`merge_prompt_layers`，IFC-IB-343）**：`effective_prompt = main 或 fallback 或 builtin`，优先序 `main.md` > `fallback.md` > **代码内置兜底**；`resolved_from ∈ {main_file, fallback_file, builtin_fallback}`（**第三值由 `definition_doc_fallback` 更名而来**，见 ADR-29 修订）。因内置兜底为**全函数**，「兜底恒非空」（ADR-29）自本 ADR 起由**结构**保证。
  2. **通用安全网（破「界面新增专家」死锁）**：**`BUILTIN_FALLBACK_DEFAULT` 是每个未登记专家的兜底**。**死锁原形**：`PUT definition`（新增专家 c）要求非空兜底 → `PUT prompts/c/fallback` 因「专家未登记」返回 `404`（端点落点 `views.py:1274-1279`）→ 专家**永远加不进来**。故**必须**是通用兜底而非「每专家各自登记一份」。代价：`prompt_fallback_missing`（IFC-IB-345 第三类错误）在正常配置下**不再触发**，语义收窄为「注入的内置兜底映射残缺」的**防御性断言** —— 此收窄**须在需求侧与 module_design 同步**。**反越域不受影响**：孤儿文件（目录有、文档未登记）仍被拒（`prompt_orphan_file`），通用兜底**不是**把校验整体关掉。
  3. **通道矫正（system 位）**：合并结果**必须**经 `build_expert(spec, *, system_prompt=...)` 进 **system 消息**；human 位**只**留用户问题。硬性守卫：`_run_expert` 传 `system_prompt=prompt or None` —— 因 `_make_langchain_client` 在 `system_prompt` **falsy 时返回裸客户端**，裸客户端**没有 `run_tool_loop`**，会**同时静默失去 system 消息与 function-calling**；空串必须传 `None`，使实现侧明确回落到 `spec.fallback_prompt`（安全网）。`build_expert` 的**假陈述 docstring 随之消解**。
  4. **`_clients` 缓存的硬规则**：`system_prompt` **只允许是装配期常量**（人格文本），**不得**把请求期变量（用户问题 / 会话历史）拼进来 —— 否则缓存项随请求数增长，既是内存泄漏，也破坏「同人格共用实例」的前提。该规则以「缓存上界 = 专家数 + 3（路由 / 专家 / 聚合三类固定角色）」为**可测断言**。
  落点：类型 / 端口 → MOD-IB-01（零依赖层）；合并 / 校验 / 派生 → MOD-IB-02（framework-free 纯函数）；内置兜底常量 → MOD-IB-16（`ib.experts`，**分层纪律：`ib.config` 只允许 stdlib + `ib.core`，不得 import `ib.experts`，内置兜底经参数注入**）；装配 → MOD-IB-23；HTTP / 前端 → MOD-IB-23 / MOD-IB-24。**零新增模块、零新增依赖边。**
- **Consequences**:
  - 正向: 第二写入口被**结构性**排除（schema 无字段，非「约定不许写」）—— ADR-15-R1 否决 Option C 的理由**自此真正成立**；「配置页编辑的提示词从未生效」这一**假陈述与真缺陷同时闭合**（主 / 兜底分层在运行期**名副其实**）；`resolved_from` 成为**单一可判定**的取值来源；**行为等价性**：生产种子文档的 `fallback_prompt` 本就是 `spec.fallback_prompt` 直抄，删字段后**生效提示词文本零变化**（仅 `resolved_from` 第三值名称与界面标签文案变化）。
  - 负向: ① **一次性内容哈希变更** —— `_semantic_payload` 去掉该键后所有既有文档 `content_hash` 变一次；**开着配置页未刷新**的会话首次保存可能收 `409`（前端已按 AC-IB-17-03 处理；须写入**交付说明**）。② **legacy 键分级处置**（旧文档残留 `experts[].fallback_prompt`）：与内置**逐字相同** → 静默丢弃（零信息损失，生产种子即此支）；**不同** → **fail-closed** 抛 `ConfigError` 并指明迁移目标 `<root>/<project_id>/<name>/fallback.md`（只报长度、**不回显正文**；对齐 IFC-IB-348 纪律）—— 真正的信息损失**绝不静默丢弃**；运维迁移步骤须写入**交付说明**。③ `prompt_fallback_missing` 降级为防御性断言（口径收窄须同步需求侧 REQ-FUNC-IB-37 / 38 / 41 与 `module_design.md`）。④ 定义文档可编辑字段进一步收窄，配置界面须**只读回显**内置兜底并**引导至提示词页**（满足可见性而不开第二写入口）。⑤ **`general` / 无专家路径不受影响**（它不走 `_run_expert`，而走 `build_aggregator()`，system 为硬编码串）—— 该**既有不对称事实**登记为 **OPEN ITEM**，本 ADR **不顺手扩围**。

### ADR-37 项目注册表的承载、落点与软删语义

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-44（项目管理：项目 CRUD + 项目注册表）、REQ-FUNC-IB-45（**先建项目、后建账号**的顺序依赖 → 「项目存在」成为可校验事实）；OQ-IB-27（用户裁决 2026-10-07：**引入项目注册表承载运行期可变状态**，**删项目 = 软删 / 停用**，物理级联删除移出 = OOS-19）、OQ-IB-29（删除须二次确认）、DR-21。**现状**：`GET /api/projects`（IFC-IB-333）的数据源是组合根 `Deps.projects`（由 `IB_CONFIG_FILE` 的 `projects.<project_id>` 经 `_seed_projects` 装配的**只读快照**）——**无法承载运行期 CRUD**。
- **Options**:
  - **Option A 仅回写配置文件（`IB_CONFIG_FILE`）**：优—零新表，复用 `DefinitionDocumentStore` 式「先写临时文件、再原子替换」纪律。缺—（1）把**运行期可变状态**与「**配置 = 装配期只读输入**」混淆；（2）写文件与装配期读存在并发竞争与半写风险；（3）**与 OQ-IB-27 裁决不符**（用户明确要求「引入注册表承载运行期可变状态」）。**（已评估未采纳）**
  - **Option B 引入项目注册表（SQLite 新表 + 手写迁移 + 独立端口）** ← **选定**：优—与既有 `LedgerRepository` / `AccountStore` / `ConfigAuditStore` **同库同机制**（ADR-07 / ADR-18 / ADR-26 复用）；软删 = 状态列；与裁决一致；上层（检索 / 台账 / 定义文档）**零改动**（项目标识仍是字符串）。缺—新增第 18 个端口与一张表；`Deps.projects` 语义由「配置快照」变为「注册表读出的活动项目」。
  - **Option C 独立轻量文件注册表（JSON 状态文件）**：优—不触库。缺—与既有「**同一 SQLite 台账 + 手写 scoped 迁移**」纪律**分叉**，净增**第二持久化机制**；并发 / 事务语义弱于 SQLite。**（已评估未采纳）**
- **Decision**: **Option B**。① 引入**第 18 个端口** `ProjectRegistryStore`（IFC-IB-367，定义于 **MOD-IB-01** 零依赖层：`ProjectRegistryEntry` / `ProjectStatus` 结构 + 端口方法集）+ **SQLite 适配器** `SqliteProjectRegistryStore`（**MOD-IB-11**，**DDL 单源 = 手写迁移 `005_projects.sql`**）+ `MemoryProjectRegistryStore` 替身。② `GET /api/projects`（IFC-IB-333）**数据源切换**为注册表（**登记型口径修订**：端点号 / 名 / 签名与 fail-closed 语义**一字不动**）。③ **装配期幂等首次播种**：以 `IB_CONFIG_FILE.projects.<id>` 为**初始数据**（沿用 `_seed_projects` 语义；离线取 memory 替身；`INSERT … ON CONFLICT DO NOTHING` 语义，**不覆盖既有注册表行**）。④ **软删 / 停用**：`DELETE /api/projects/{project_id}` = `status="disabled"`（**数据保留、可恢复**），**不做物理级联删除**（OOS-19）；删除须**二次确认**（确认值 = 目标 `project_id`，不一致即 `400`）。⑤ **零新增模块、零新增依赖边**（复用既有边 `23 → 01 / 11`）。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-44 / IB-45；复用同库迁移纪律（ADR-18 / ADR-26）；软删使误删可恢复（OQ-IB-29）；上层零改动（项目标识仍为字符串，`Scope` 契约不动）。
  - 负向：新增第 18 个端口与一张表 + **一处 `GET /api/projects` 数据源口径修订**（登记于 §2.0.9）；`Deps.projects` 由「配置快照」变为「注册表读出的活动项目」，**既有基于配置快照的离线用例须相应调整**（属施工期影响，非契约变更）；注册表规模 / 查询开销待实测（**[TBD-T26]**）。

### ADR-38 LLM Key 的持久化载体（DB）、凭据纪律与装配期解析

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-47（LLM Key 管理：增 / 改 / 删）、REQ-NFR-IB-20（Key 存储与呈现纪律：载体 = 数据库；库文件 0600 且属主对齐服务账号；`.env` 仅保留非 LLM Key 的其他密钥；5 判据）、C-IB-42（LLM Key 凭据纪律，载体 = DB）；OQ-IB-25（用户裁决 2026-10-07：Key 存 **DB**；生效 = 保存 + 服务重启重装配；**非 `.env`**）、OQ-IB-26（**Key 全局唯一一个**；项目级 / 每项目 / 多供应商 = 移出 = OOS-18）、DR-21。**现状**：`LlmConfig.api_key_env`（默认 `IB_LLM_API_KEY`）+ 启动校验要求存在，否则 `StartupError`。
- **Options**:
  - **Option A 界面写回 0600 `.env`**（原草拟推荐路径）：优—零新表，复用环境变量纪律。缺—**与用户裁决不符**（OQ-IB-25 明确否决）；运行期写凭据文件 + 与 systemd `EnvironmentFile` 语义冲突；写回后**仍须重启**（与 Option B 同等）。**（已评估未采纳）**
  - **Option B 界面写 DB 表（装配期读取）** ← **选定**：优—裁决选定；**不落 `.env`**；权限可 0600 + 属主对齐；与既有 SQLite 同库同迁移机制；明文**不回显**可做成类型层事实。缺—新增第 19 个端口与一张表；凭据载体由「环境变量」改为「DB」→ 须登记修订 `tech_stack.md` 凭据纪律与「配置载体」行（Part C）。
  - **Option C 保持仅环境变量（现状）**：优—零改动。缺—与「**界面管理 Key**」的 REQ-FUNC-IB-47 直接冲突。**（已评估未采纳）**
- **Decision**: **Option B**。① 引入**第 19 个端口** `LlmKeyStore`（IFC-IB-368，定义于 **MOD-IB-01**：`LlmKeyStatus` 结构 + 端口方法集）+ **SQLite 适配器** `SqliteLlmKeyStore`（**MOD-IB-11**，**DDL 单源 = 手写迁移 `006_llm_key.sql`**，**单行表** `llm_key(id=1, secret, updated_at)`）+ `MemoryLlmKeyStore` 替身。② **全局唯一一个 Key** —— 以**单行表结构**保证（OOS-18 为扩展点预留，**不**做项目级 / 多供应商）。③ **装配期由组合根经 `resolve_secret()` 读取（唯一读点）**；HTTP 层只暴露 `LlmKeyStatus`（`configured: bool` / `masked: str` / `updated_at: str | None`）—— **不回显明文为类型层事实**（响应类型无明文字段）；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道；口径见 §10.1 OI-3）。④ **唯一写入口** = `PUT /api/llm-key`；删除 = `DELETE /api/llm-key`（清空单行）。⑤ **承载库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；部署检查清单 B22）；`.env` 仅保留非 LLM Key 的其他密钥。⑥ **生效口径 = 保存 + 服务重启重装配**（**ADR-32 不变**；**不引热重载**，OOS-16 维持）；重启**由用户手工执行**。⑦ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-47 / REQ-NFR-IB-20 / C-IB-42；Key **不入 `.env` / 不进 git / 不进命令行或 shell history**（唯一写入口为管理端点）；同库同迁移；明文不回显为结构事实。
  - 负向：新增第 19 个端口与一张表；**凭据载体由环境变量改为 DB** → 须修订 `tech_stack.md` 的 `<credential_policy>` 与 §1「配置载体」行（**登记型口径修订，无新第三方依赖**，见 Part C）；库文件权限与属主须真机实测（**[TBD-T27]**）；`api_key_env` 字段语义降级须登记（IFC-IB-024，见 §2.0.9）。

### ADR-39 LLM 未配置态的启动与运行期语义（破除首启死锁）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-47（Key 经**管理界面**增 / 改 / 删）、REQ-NFR-IB-20、ADR-38（Key 载体 = DB）。**派生事实**：若沿用既有「装配期缺 `IB_LLM_API_KEY` 即 `StartupError`」，则**首启 DB 无 Key → 服务不启动 → 管理界面不可达 → 无法写入首个 Key**，构成**死锁**（Key 的唯一写入口是管理端点）。**本 ADR 决策的是「未配置态」的语义**，非任何业务数值。
- **Options**:
  - **Option A 保持 fail-fast（缺 Key 即 `StartupError`）**：优—fail-fast 一致。缺—**首启死锁**（见 Context）；对「先部署、后配 Key」的常见序不友好。**（已评估未采纳）**
  - **Option B 保持 fail-fast + 部署期预置种子 Key（手工写库 / CLI）**：优—保留 fail-fast。缺—预置步骤须「**由用户执行**」（C-IB-38 口径）；引入**第二条写 Key 通道**（与「唯一写入口 = 管理端点」张力）；且对纯界面管理诉求不友好。**（已评估未采纳）**
  - **Option C 放宽为「未配置态」（fail-closed 于调用期）** ← **选定**：装配期 Key 解析结果三态 `configured` / `unconfigured`；`unconfigured` 时**服务正常启动**，LLM 依赖路径 **fail-closed**（调用期以可读、**不含任何 Key 信息**的错误拒绝），管理端点与健康端点**始终可达**。
- **Decision**: **Option C**。① 装配期 Key 解析结果 `configured` / `unconfigured`；**缺 Key 不再致命**（**仅** LLM Key 放宽，**其余必填项仍 fail-fast**）。② `unconfigured` 时：`GET /api/llm-key` → `configured=false`；**LLM 依赖路径**（问答 / 路由 LLM 档 / 聚合）以 `DependencyUnavailableError`-类可读错误 **fail-closed** —— **不得**回落到「无 Key 静默出空答案」。③ 启动日志与 `/healthz/deps` 的 `llm` 字段**显式声明 LLM 未配置**（**不含任何 Key 值**）。④ 配置成功后**仍须服务重启重装配方生效**（ADR-32）。⑤ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：破除首启死锁；满足 REQ-FUNC-IB-47 的界面可达性；fail-closed 不静默（对齐 ADR-13「故障与空结果可区分」精神）。
  - 负向：**局部放宽**了既有「缺 Key 即启动失败」的 fail-fast（**注**：其余必填配置的 fail-fast **不变**）；须登记 OPEN ITEM **OI-2**（首启序：部署 → 登录 → 设 Key → **由用户手工重启**）；若 PM / 用户不采纳 Option C，则须以 Option B 的**用户手工预置**替代（二选一，架构层不自行拍板）。**REV-18 裁决补记（用户裁决 2026-10-07）**：备选 **Option B（部署期由用户手工预置 Key）已评估未采纳**；**用户已裁决采纳 Option C**（缺 Key 非致命、fail-closed 于调用期，其余必填仍 fail-fast）—— OI-2 据此**关闭**（见 §10.1）。

### ADR-40 运维账号 CRUD 扩展、顺序依赖与删除保护

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-45（**先建项目、后建账号**→创建账号须校验项目存在；OQ-IB-28 裁决 1:N、**零迁移**）、REQ-FUNC-IB-46（账号**查看 / 编辑 / 删除**）、REQ-FUNC-IB-31（既有创建 / 查看 / 停用，**正文不改**）；OQ-IB-28（**零迁移**：**不**加 `users.project_id` 唯一约束）、OQ-IB-29（**禁删 `admin` 与最后一个有效 `admin`**；删除须**二次确认**；**优先软删**）、OOS-19（物理级联删除移出）。
- **Options**:
  - **Option A 硬删除账号（`DELETE` 真删行）**：优—语义直白。缺—不可恢复，**与 OQ-IB-29「软删优先」不符**；且会随账号消失丢失审计线索。**（已评估未采纳）**
  - **Option B 软删 / 停用（复用既有 `AccountStatus="disabled"`）+ 删除保护 + 二次确认** ← **选定**：优—**复用既有 `set_status`**（IFC-IB-310，方法集**不变**）、**零迁移**（无新列，符合 OQ-IB-28）；`disabled` 已表达「不可登录」。缺—「最后管理员」判定须读 `list_users`（规模小，可接受）。
  - **Option C 新增独立 `deleted_at` 列（真软删时间戳）**：优—可区分「停用」与「删除」。缺—需迁移，**触碰 OQ-IB-28 的「零迁移」裁决**；`disabled` 已足够表达「不可登录」。**（已评估未采纳）**
- **Decision**: **Option B**。① **新增端点**（并入 **MOD-IB-23**）：`PATCH /api/accounts/{user_id}`（编辑：`project_id` 重绑 / `username` / `status`；**不回显任何凭据**）、`DELETE /api/accounts/{user_id}`（软删 = 置 `disabled`；**二次确认** `confirm_username` 与目标 `username` 一致否则 `400`；**禁止删除 `admin` 或最后一个有效 `admin`** → `409`）。② **创建账号的顺序依赖**：`POST /api/accounts` **增前置校验** —— 目标 `project_id` 须在**项目注册表**（ADR-37）存在且为 `active`，否则 `422` / `400` 可读错误（**不静默创建无主账号**）。③ **1:N 零迁移**：**不**加 `users.project_id` 唯一约束；REQ-FUNC-IB-31 正文不改（**注**：与 ADR-21 的 1:1 表述的口径张力已由 **ADR-21-R1**（amend 子节）承接，关系式订正为 **N:1** —— **OI-1 已由用户裁决于 2026-10-07 关闭**；**ADR-21 正文一字未动**）。④ **删除账号不随项目级联**（软删项目亦不删除其账号，保留可恢复）。⑤ `AccountStore` 端口**方法集不变**（软删复用 `set_status`；编辑经 IFC-IB-366 `update_user` —— **加成式扩展**，其既有 13 方法文本不改）；**「最后管理员」判定在服务层**（非端口层）。⑥ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-45 / IB-46；**零迁移**（OQ-IB-28）；复用既有 `status` 与 `AccountStore`；删除保护与二次确认降低误操作风险。
  - 负向：新增 2 个端点与 1 个端口方法（`update_user`，**加成式扩展**）；「最后管理员」判定引入一次 `list_users` 读（规模小）；`PATCH` 编辑须**严格不回显口令 / 令牌**（沿用 IFC-IB-321 / IFC-IB-324 纪律）。

### ADR-41 项目域资料的 `kb_id` 推导、归属断言保留与 `kb_default` 迁移

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-48（**项目域文件上传取代「知识库标识」输入**）；C-IB-43（「取代知识库标识」**必须不破坏架构红线 `docs/architecture_design.md:120`**；REV-18-2：**`kb_id ≡ project_id`**，**请求体不再接收 kb 字段**，**保留** `assert_kb_in_project`）；OQ-IB-30（用户裁决 2026-10-07：**项目级单 DB**；`kb_id` **由已认证主体的 `project_id` 推导**；请求体不再接收 kb 字段；既有 `kb_default` 数据**迁移到归属项目 KB**；**保留** `assert_kb_in_project`，失败 `403`）；DR-21。
- **Options**:
  - **Option A 由客户端继续提交 `kb` 字段，服务端仅断言归属（现状 + 断言）**：优—改动最小。缺—**违反 C-IB-43 / OQ-IB-30**（请求体**不应**再接收 kb 字段）；客户端仍可自证范围，与 §1.4 第 2 条「**范围不可由客户端自证**」精神存在张力；「知识库标识」输入框须**移除**（REQ-FUNC-IB-48）。
  - **Option B `kb_id` 由已认证主体的 `project_id` 推导（`kb_id ≡ project_id`），请求体不再接收 kb 字段，且**保留** `assert_kb_in_project`** ← **选定**：优—**范围只能来自服务端结论**（对齐 §1.4 第 2 条与 ADR-04 / ADR-28 约束③）；请求体**收缩**；**红线 120 的归属断言仍生效**（防回归）。缺—既有 `kb_default` 数据须**一次性迁移**到归属项目 KB；上传 / 列表端点的请求体形状变化（属施工期影响）。
  - **Option C 由客户端提交并**直接**作为 `kb_id`（不做推导、不做断言）**：优—零改动。缺—**直接违反红线 `architecture_design.md:120`**（「范围不可由客户端自证」）与 C-IB-43。**（已评估未采纳）**
- **Decision**: **Option B**。① HTTP 层**由已认证主体解析 `project_id`**，**据此推导** `kb_id`（`kb_id ≡ project_id`）；**请求体不再接收 `kb` 字段**（既有字段**移除**）。② **保留** `LedgerRepository.assert_kb_in_project(project_id, kb_id)`（IFC-IB-130）**归属断言**；失败仍 `403`（**非 404**，避免存在性探测）—— **红线 `architecture_design.md:120` 不被破坏**（这是 C-IB-43 的硬要求）。③ **`kb_default` 数据迁移**：既有落在 `kb_default` 的行**迁移到归属项目 KB**（一次性迁移，随迁移家族交付；幂等、前向）。④ 上传 / 列表 / 删除端点（IFC-IB-242 / 243 / 244）**请求体形状收缩**（去掉 kb 字段）—— **登记型口径修订**（号 / 名 / 签名不变），见 §2.0.9 与 `module_design.md` §2.2.9。⑤ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-48 / C-IB-43 / OQ-IB-30；**范围只认服务端结论**（红线 120 加固而非削弱）；请求体收缩、界面简化（移除「知识库标识」输入）。
  - 负向：`kb_default` 一次性**数据迁移**（须幂等、可前向；回滚 = 代码回滚 + 数据保留）；上传 / 列表端点的**既有请求体契约形状变化**（须在 `requirements_spec.md` 侧同步口径 —— **本包不改需求文档**，登记为交付说明）；**保留** `assert_kb_in_project` 使「客户端自证」在结构上不可绕过。

### ADR-42 系统管理三分的信息架构与服务端授权解耦

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-43（**系统管理**三分：账户管理 / 项目管理 / LLM Key 管理）；OQ-IB-31（用户裁决 2026-10-07：父级「**系统管理**」含**三子项**；既有账户管理**移入**；**资料管理**仍为独立顶级，视图改为**项目域**；**UI 分组不得视为权限机制** —— 非 admin 一律**服务端 403**）；REQ-NFR-IB-09 / IB-16；ADR-22（单一授权真源）。
- **Options**:
  - **Option A 三分项各自为顶级导航项（不设父级）**：优—改动最小。缺—**与 OQ-IB-31 裁决不符**（裁决要求父级「系统管理」+ 三子项）。**（已评估未采纳）**
  - **Option B 父级「系统管理」下挂三子项（账户管理 / 项目管理 / LLM Key 管理），资料管理独立顶级且视图改为项目域** ← **选定**：优—符合裁决；导航分组清晰；**授权仍只经服务端 `AuthzPolicy`**（UI 分组**不作为**权限机制）。缺—路由树新增父级节点；既有账户管理页**迁移**到子项（须处理既有路由 / 深链）。
  - **Option C 以 UI 分组**兼任**权限边界（仅 admin 可见 / 可操作）**：优—体验直观。缺—**违反 ADR-22 单一授权真源**与「**UI 分组不得视为权限机制**」裁决；前端可见性可被绕过，**服务端必须**仍 `403`。**（已评估未采纳）**
- **Decision**: **Option B**。① **信息架构**：父级「**系统管理**」含三子项（**账户管理** / **项目管理** / **LLM Key 管理**）；**资料管理**保持**独立顶级**，其视图由「知识库」改为「**项目域**」（对齐 ADR-41）。② **授权与导航解耦（强制）**：UI 分组的可见性 / 可点性**仅为体验优化**；**授权判定唯一经服务端**（注入的 `AuthzPolicy`，ADR-22）；**非 admin 一律服务端 `403`** —— 「UI 分组不是权限机制」为**架构层事实**，不得以导航隐藏替代服务端拒绝。③ 前端路由：`vue-router`（hash）**新增父级节点**，既有账户管理路由**迁移**（保留 hash，不引入 `try_files`）。④ 落点并入 **MOD-IB-24**（前端 IA）；**零新增模块、零新增依赖边**。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-43 / OQ-IB-31；导航分组与授权解耦，**不产生第二授权真源**（ADR-22 复用）；资料管理视图与 ADR-41 的项目域口径一致。
  - 负向：既有账户管理页的**路由 / 深链迁移**（施工期影响）；**前端改密态与权限可见性仅为体验优化**的口径须在 UI 文案与测试中显式（服务端为唯一裁决者）。

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

**（R7）图编译输入与拓扑不可编辑**：编排图的编译输入是**经准入闸门校验通过的定义文档**（ADR-16；校验器 IFC-IB-290，闸门 IFC-IB-293）；图**编译一次、进程常驻**，**运行期不得由任何图外输入改变拓扑** —— 节点 / 边集合与条件边存在性**不是**可视化界面的可编辑对象（REQ-FUNC-IB-26 ②）。拓扑变更的**唯一路径**：改定义文档 → 装配期校验 → 重新编译（AC-IB-18-01）。可编辑的是**节点参数与专家集合**（模型与系统提示、工具授权、路由关键词与语义范例、路由阈值与边界参数、并行扇出专家集合、默认专家标记），且受白名单约束（IFC-IB-291）。

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

**（R8）流式与会话的四条规范化补充（REQ-FUNC-IB-20；US-IB-19 / US-IB-20）**：

1. **增量推送与终态单发**（AC-IB-19-01）：`content` 为**增量**片段，客户端**不得**等待 `done` 才渲染；**完成事件恰一次单发**，其后**不再有**该次交互的任何内容片段；终态构造经 `completion_event`（IFC-IB-302）。空内容边界：无可交付正文时，**不发空的 `content` 帧**，只发完成事件且 `had_content=false`（AC-IB-19-05）。
2. **完成事件附结构化产物**（AC-IB-19-02 / 19-05）：终态事件携带 `CompletionPayload`（`citations: tuple[CitationItem, ...]` + `had_content: bool`，IFC-IB-300）；`citations` **可为空元组**（无引用即空，**不编造引用**）；引用项为**定位信息**（`doc_id` / `doc_name` / `page_or_section` / `locator` / `score`），**不内联字节、不含正文全文**。
3. **思考分区与内部产物**（AC-IB-19-03 / 19-04）：`reasoning` 分区为**可选增强且默认不启用**（`IB_REASONING_STREAM_ENABLED` 默认 `false`，仅键名，IFC-IB-304）；**内部子任务产物（专家内部步骤、路由判定、转交与咨询痕迹）永不映射为可见 `kind`**，该判据落在纯函数 `is_user_visible(kind)`（IFC-IB-303）—— 对齐 ADR-09「骨架不见业务语义」与 FreeArk 的 `INTERNAL_NOSTREAM_TAG` / `_run_subexpert` 不外流口径；**默认不混帧**（同一事件不承载两个分区的语义）。
4. **会话状态与确认中间态**（AC-IB-20-02 / 20-03 / 20-04 / 20-05）：会话状态经 `SessionStore` 端口承载（**默认内存实现**，键 `session_key = f"{project_id}:{actor_id}:{session_id}"`）；**持久化策略须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`，`in_process` 或 `external`，v1 默认 `in_process`），**重启丢弃待确认状态 = fail-closed**（`SessionStateLossOutcome` 唯一取值 `fail_closed_restart_required`，IFC-IB-299）；「可选手动确认中间态」**机制保留、默认关闭**（`IB_CONFIRMATION_GATE_ENABLED` 默认 `false`），**不绑定业务语义**，呈递与回传见 ADR-17。**OQ-IB-07 / OQ-IB-08 均保持开放**。

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
| **ARCH-ASSUMPTION-A6**（R7 新增） | **定义文档的物理载体 = 本地文件**（路径经 `IB_DEFINITION_DOC_PATH` 注入），**一项目一文档**，内容为结构化、机器可读文本 | REQ-FUNC-IB-25 只规定「项目级、结构化、机器可读」，**未规定存储载体**；也未规定「一项目是否可有多个文档」 | 若改为 DB / 配置中心承载，**只替换 `DefinitionDocumentStore` 适配器**（IFC-IB-292），装载 / 校验 / 写入 / 派生逻辑**零改动**（ADR-15）；「一项目多文档」若成立，须改的是文档**聚合根**定义，属需求侧变更 | 需 PM 确认（载体与「一项目一文档」口径） |
| **ARCH-ASSUMPTION-A7**（R7 新增） | **可视化的落地前置条件**：专家 / 路由 / 编排 / 工具授权的定义**已外置为数据、且真源按域唯一**（REV-16-3：结构与配置域 = 定义文档；提示词域 = 独立 markdown 目录，见 ADR-15-R1）（即 REQ-FUNC-IB-01 / IB-02 的**实现落差**先被闭合）——**该前提已被登记为「施工顺序前置 + 风险」，不构成施工阻断** | 需求侧已明示该前提并声明「**不在本节新增需求**」（`requirements_spec.md` §2.7 前言）；US-IB-17 / US-IB-18 为**施工顺序前置**而非阻塞（`user_stories.md` 决策前置状态行） | 若前提未闭合：定义文档无数据源，可视化的**装配期闸门与派生**仍可先落地与单测（AC-IB-18-05 离线可测），但界面**无真实内容可编辑**；**不影响架构与模块设计成立**。**REV-07-6 判定 = (a) 可登记前置条件 / 风险，本轮继续**；若 PM / 用户改判 (b)（IB-01/02 未闭合前不得开展可视化设计），须回 GROUP_A 立项并整体回退本修订 | **已登记（R7）：判定 (a)**；须 PM 知悉并在 GROUP_C 施工顺序中体现 |
| **ARCH-ASSUMPTION-A8**（R8 新增） | **v1 的会话持久化策略默认 = 进程内（`in_process`）**：`IB_SESSION_PERSISTENCE_POLICY` 取值 `in_process`（默认）或 `external`；`external` 为**已声明值域**，**v1 不提供适配器**（`IB_SESSION_BACKEND` 的值域扩展为 `memory` 或 `external`，默认 `memory`） | REQ-FUNC-IB-20 要求「会话恢复」与「持久化策略显式声明」，**未规定** v1 采哪种策略；AC-IB-20-02 只要求策略**显式**、AC-IB-20-05 只要求状态丢失时 **fail-closed** | 若接入方要求**跨重启续跑**，只需在 `external` 值域内新增一个 `SessionStore` 适配器（**上层零改动**，ADR-04 同精神），并据 [TBD-T21] 校准容量；**不影响 ADR-17 与既有 DAG** | **需 PM 确认**（v1 默认持久化策略；若判「v1 必须跨重启持久化」，须回 GROUP_A / 立项，架构层不自行扩围） |
| **ARCH-ASSUMPTION-A9**（R13 新增） | **会话 TTL / 续期窗口 / bcrypt cost / 限速阈值在 v1 采用可配置默认值**（键名 `IB_SESSION_TTL_SECONDS` / `IB_SESSION_RENEW_WINDOW_SECONDS` / `IB_LOGIN_MAX_FAILURES` / `IB_LOGIN_LOCK_SECONDS`），**具体取值由部署阶段在目标机标定** | REQ-FUNC-IB-29 / REQ-NFR-IB-16 **未规定具体数值**；AC 只要求「过期」「续期」「阈值可配置」**显式存在** | 若目标机实测显示 bcrypt cost 过高拖慢登录，只需调键值（**上层零改动**）；若用户要求「会话永久有效」，与 REQ-NFR-IB-16 冲突，须回 GROUP_A | **需 PM 确认**（默认值与 OQ-IB-09 / OQ-IB-12 同源；架构层不自行拍板数值） |
| **ARCH-ASSUMPTION-A10**（REV-16-2 新增；**REV-16-3 已确认并转为决策**） | **独立提示词目录的物理布局与命名规则（已确认）**：根路径经 `IB_EXPERT_PROMPT_DIR` 注入；目录树为 **`<root>/<project_id>/`**（**一项目一目录树**）；其下**每专家一子目录**，**目录名 = 专家 `name`**（即 ADR-15-R1 的**合并键**在物理层的落地），内含 `main.md`（主提示词，**可缺**）与 `fallback.md`（兜底提示词，**REV-17 起亦可缺** —— 两层文件皆缺时回落**代码内置兜底**，见 ADR-15-R2 / ADR-36；故该层的**存在性不再是装配前置条件**） | REQ-FUNC-IB-41 只规定「可经文件保存 / 独立 markdown 目录」，**未规定**目录布局与文件命名；OQ-IB-18 只给出「独立 markdown 目录、不在定义文档内」 | 若改为 DB / 配置中心，**只替换 `ExpertPromptStore` 适配器**（IFC-IB-339），合并 / 校验 / 派生逻辑零改动（ADR-15-R1）；「一项目多目录树」若成立，须改的是**聚合根**定义，属需求侧变更 | **已确认（PM / 用户裁决，2026-10-06，REV-16-3）**：目录布局与命名规则如上；**目录名 = `name` 即 ADR-15-R1 合并键的物理实现**。**边界约束（P-2；2026-10-07 据实订正）**：FreeArk 业务 `cn_name`（系统管家 / 三恒知识）与业务专家名经**全局硬改名**生效于**通用默认种子**（`src/ib/experts/__init__.py::_DEFAULT_SPECS`，即所有项目无差别继承）；全仓**无 `demo` 特判**，故**不存在**「业务名仅存在于 `demo` 项目」的边界实现 —— 本句此前写作「通用默认种子（`p_alpha` 等）**不得携带任何 FreeArk 业务名称**」，**与实现不符、系假陈述**，现据实订正。与 FreeArk 的对齐**限于定义元数据 + 工具名映射**，不改通用基座语义；由此引入的 **OOS-04 / OOS-11 张力按「已登记」接受**（用户裁决 2026-10-07：**保留 FreeArk 名 + 补回兜底提示词护栏**）。**发布说明（P-3）**：专家改名为**硬改名、无并存窗口**（如 `data-expert`→`freeark-expert`、`knowledge-expert`→`sanheng-knowledge`）；升级后**基于文件的定义文档须使用新专家名**；`AGGREGATION_FORBIDDEN_LABELS` 迁移态取 **旧 ∪ 新 并集** |
| **ARCH-ASSUMPTION-A11**（REV-16-4 新增） | **配置审计记录的保留策略（容量上界 / 轮转 / 清理）在 v1 未定**：`config_audit` 表**只增不删**（append-only），具体保留时长 / 条数上界 / 归档方式**由部署阶段标定** | REQ-NFR-IB-19 / AC-IB-32-02 只要求「存在可查询的记录」，**未规定保留策略**；需求侧无对应 REQ | 若需限额：新增一个清理任务即可（**上层零改动**）；若需长期留存：换/接外部存储只替换 `ConfigAuditStore` 适配器（IFC-IB-357） | **需 PM 知悉**（保留策略；架构层不自行拍板数值；与 [TBD-T25] 同源） |
| **ARCH-ASSUMPTION-A12**（REV-18 新增） | **LLM Key「未配置态」的启动语义 + 承载库文件权限口径**（架构侧取值）：① 装配期 Key 解析结果 `configured` / `unconfigured`；**`unconfigured` 非致命**（服务正常启动；LLM 依赖路径 **fail-closed** 于调用期；`GET /api/llm-key` 返 `configured=false`）—— 见 **ADR-39**；② Key **承载库文件权限 0600 且属主对齐服务账号**（REQ-NFR-IB-20；部署检查清单 B22）；③ **掩码口径** = **不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道）。**唯一写入口** = `PUT /api/llm-key`；**生效 = 保存 + 服务重启重装配**（ADR-32），**重启由用户手工执行** | REQ-FUNC-IB-47 / REQ-NFR-IB-20 规定「界面管理 Key」「载体 = DB」「库文件 0600」与「只回掩码 / 存在性 / 更新时间」，但**未规定首启缺 Key 的启动语义**（否则构成首启死锁，见 OI-2），亦未逐字规定掩码字面 | **用户裁决 2026-10-07 已采纳「未配置态」（ADR-39 Option C）**：缺 Key **非致命**、服务正常启动、LLM 依赖路径**调用期 fail-closed**，其余必填项**仍 fail-fast**；备选 Option B（部署期由用户手工预置 Key）**已评估未采纳**；掩码字面与库文件属主由施工期 / 部署期定 | **已决**（用户裁决 2026-10-07；与 [TBD-T27] 同源）—— **OI-2 已关闭**；**OI-3 保持 OPEN**（施工期定，不阻塞） |

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
| **TBD-T19（R7 新增）** | **装配期装载 + 完备性校验 + 派生视图**的耗时（冷启动预算）与随定义文档**规模**（专家数 / 关键词数 / 条件边数）的增长曲线 | REQ-FUNC-IB-27；REQ-NFR-IB-02；AC-IB-18-06；ADR-15 / ADR-16 | 决定是否需要对派生结果做**合规缓存**（ADR-15 Option C 的两个前置条件：失效键 = 文档语义哈希、可随时删除且不得成为读源）；也用于校准装配期超时与启动预算 |
| **TBD-T20（R7 新增）** | **前端可视化的规模上界**：定义文档在目标机浏览器上的**图渲染**规模（节点数 / 条件边数 / 分支映射条目数）与前端产物体积增量（含图可视化库及其传递依赖） | REQ-FUNC-IB-25；AC-IB-17-02 / AC-IB-17-06 | 决定是否需要**虚拟化渲染 / 路由级按需加载**；并作为 `tech_stack.md` §5.3「图库许可与体积」风险行的实测依据 |
| **TBD-T21（R8 新增）** | **会话状态的容量与恢复并发**：并发会话数 × `SessionTurn` 上界下的**内存占用**；`POST /api/chat/resume`（IFC-IB-307）的**并发容量**（与 [TBD-T15] 同源，SSE 长连接占同步 worker）；待确认中间态的**丢失率**；需据此定 `MemorySessionStore` 的**保留时长 / 淘汰上界** | REQ-FUNC-IB-20；AC-IB-20-02 / AC-IB-20-05；ADR-17 | 决定是否需引入 `external` 适配器（[ARCH-ASSUMPTION-A8]）；并校准「会话失效」的可观测性与可读回执口径（IFC-IB-308）。**未经实测前不得给出容量结论** | |
| **TBD-T22（R13 新增）** | **账户/会话链路的运行时标定**：① bcrypt cost 在目标机（CPU-only）的单次耗时；② `IB_SESSION_TTL_SECONDS` / 续期窗口的并发索引查询开销；③ 限速阈值（OQ-IB-12）；④ 种子与 `ensure-schema` 的耗时 | REQ-NFR-IB-15 / IB-16；ADR-19 / ADR-20 / ADR-26 / ADR-27；[ARCH-ASSUMPTION-A9] | 决定默认键值；决定是否需为 `sessions(token_digest)` 建索引以外的优化。**未经实测前不得给出容量/时延结论** | |
| **TBD-T23（R13 新增）** | **前端产物增量体积与首屏**：Element Plus + vue-router 引入后 `dist` 体积与目标机（4GB 内存）首屏；与 [TBD-T20] 同源（R10 基线 JS 252.35 kB / gzip 89.20 kB） | REQ-NFR-IB-17；ADR-23 | 决定是否需按需引入（`unplugin-vue-components`）与代码分割。**未实测前不得宣称体积可接受** | |
| **TBD-T24（REV-16-2 新增）** | **提示词目录装载 + 跨域合并 + 工具参数校验**对**装配期冷启动耗时**的增量，以及随专家数 / 提示词正文总字节数的增长曲线 | REQ-FUNC-IB-37 ~ IB-41；REQ-NFR-IB-19；ADR-15-R1 / ADR-29 / ADR-30 / ADR-32；[TBD-T19] 同源 | 与 [TBD-T19] **合并观测**；决定是否需对「提示词正文读取 + 语义哈希」做**合规缓存**（ADR-15-R1 Option B 之下，缓存**不得**成为读源，失效键 = 两域语义哈希）。**未经实测前不得给出耗时结论** | |
| **TBD-T25（REV-16-4 新增）** | **配置审计表增长与查询开销**：`config_audit` 在目标规模的**行数增长曲线 / 单文件体积**，`GET /api/config/audit`（IFC-IB-359）与 `GET /api/config/storage-state`（IFC-IB-362）的响应耗时，及「审计写失败」实际发生率 | REQ-NFR-IB-19；REQ-NFR-IB-06；AC-IB-32-02；ADR-34 / ADR-35；[ARCH-ASSUMPTION-A11] | 定保留 / 轮转策略与是否需要归档；量化「保存成功但记录缺失」窗口。**未经实测前不得给出容量 / 时延结论** |
| **TBD-T26（REV-18 新增）** | **项目注册表的规模与查询开销**：`projects` 表在目标规模的**行数上界 / 单文件体积增量**，`GET /api/projects`（IFC-IB-333）与项目 CRUD 端点的响应耗时，及**装配期幂等首次播种**（以 `IB_CONFIG_FILE.projects.<id>` 为初始数据）的耗时 | REQ-FUNC-IB-44 / IB-45；REQ-NFR-IB-11；ADR-37 | 定注册表是否需要索引 / 分页；量化 `Deps.projects` 由「配置快照」变为「注册表读出」后的装配期增量。**未经实测前不得给出容量 / 时延结论** |
| **TBD-T27（REV-18 新增）** | **LLM Key 承载库文件的实际权限与属主**：库文件（含 `llm_key` 表的 SQLite 文件）在目标机的**实际 mode（须 0600）与 owner（须对齐服务账号）**、`busy_timeout` 下的写入耗时，以及 `SqliteLlmKeyStore` 的读写争用；另含 **AVX2 / SIGILL 与本轮无涉的确认**（本轮**未**引入任何新 wheel） | REQ-NFR-IB-20；REQ-FUNC-IB-47；C-IB-42；ADR-38 / ADR-39；[ARCH-ASSUMPTION-A12] | 定库文件权限 / 属主的**真机验证**口径（部署检查清单 B22）；确认「Key 不入 `.env` / 不进 git / 不进命令行」的端到端可复查证据。**未经实测前不得给出权限 / 时延结论** |

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
| **（R7）REV-07-6 施工前置**（IB-01 / IB-02 定义外置） | 可视化落地的**施工顺序前置**是否须先闭合（「先定义外置、后可视化」） | **登记为前置条件 / 风险，不阻断**（[ARCH-ASSUMPTION-A7]；判定 **(a)**） | 若 PM / 用户改判 **(b)**，本修订整体回退并回 GROUP_A 立项；架构层不自行扩围或缩围 |
| **（R8）OQ-IB-07 / OQ-IB-08 的架构默认取值落地** | ① 写操作确认门（OQ-IB-07）在架构上如何承载；② 会话历史的作用范围（OQ-IB-08） | ① **机制保留、默认关闭**（`IB_CONFIRMATION_GATE_ENABLED` 默认 `false`，且**不绑定业务语义**；见 ADR-17）；② **会话内隔离**（`session_key` 前缀断言，FM-7），**不跨会话注入**历史 | **两项 OQ 均保持开放**，本修订**不裁决**「是否应默认启用确认门」或「历史是否跨会话」；架构层只落地「默认关闭 / 会话内隔离」的安全默认，**不裁决业务语义、不自行扩围** |
| **（R13）OQ-IB-09 ~ OQ-IB-15 的架构默认取值落地** | ① TTL/续期（OQ-IB-09）；② 首登强制改密（OQ-IB-10）；③ 口令强度策略（OQ-IB-11）；④ 登录限速（OQ-IB-12）；⑤ 认证审计留痕（OQ-IB-13）；⑥ 管理员重置口令路径（OQ-IB-14）；⑦ 粘贴令牌入口处置（OQ-IB-15） | ① 可配置默认值 + [TBD-T22]（[ARCH-ASSUMPTION-A9]）；② **服务端强制改密态**（ADR-20）；③ 键名 `IB_PASSWORD_MIN_LENGTH`，**策略细节 TBD**（OQ-IB-11 开放）；④⑤ **设计提供但条件性**（ADR-27，**未纳入默认施工**）；⑥ 端点设计提供（IFC-IB-321 的 `reset-password`），是否纳入 v1 待确认；⑦ **彻底移除、无旁路**（ADR-24） | **OQ-IB-11 / 12 / 13 / 14 保持开放**，本修订**不裁决**业务策略值；架构层只落地「服务端强制 / 可配置 / 可注入」的安全默认，**不自行扩围或缩围** |
| **（REV-16-2）OQ-IB-24 的架构承接 + C-IB-39 / C-IB-40 落地** | ① **ADR-15 正式修订**（真源边界 / 优先级合并规则 / 派生视图是否仍只读）；② 配置**生效口径**与是否重编译图 | ① 真源修订为「**分域真源 + 装配期合并**」，**派生视图仍只读**（见 **ADR-15-R1**；**amend** 而非 supersede，理由见包 §5.1）；② 生效口径 = **保存 + 服务重启重装配**，**不重编译图**（见 **ADR-32**；C-IB-40 / OOS-16） | **OQ-IB-24 由本包正式承接并关闭**（架构侧已给出方案）；**不裁决**「主提示词 / 兜底提示词的具体文案」「工具参数的具体取值」等业务内容（由接入方 / 施工期确定，架构层不发明） |
| **（REV-16-4）配置审计保留策略 + 「保存成功但记录缺失」窗口** | ① `config_audit` 的**保留时长 / 容量上界 / 轮转**；② 审计写失败时是否须**提升为保存失败**（fail-closed） | ① **只增不删**（append-only），保留策略**待定**（[ARCH-ASSUMPTION-A11] / [TBD-T25]）；② **审计写失败非致命**（保存结果不变 + 结构化 WARN），**不因可观测性故障回滚已成功的保存**（ADR-34） | 两项均**待用户 / PM 裁决**；架构层只落地「只读审计 / 非第二真源 / 非致命」的安全默认，**不自行拍板保留数值、不自行扩围为 fail-closed** |
| **（REV-17）`general` / 无专家路径的人格串不可配置** | 落定 ADR-36 的 system 位通道时暴露的**既有不对称事实**：专家路径的 system 提示词由**两域合并**派生（可配置，ADR-29 / ADR-36），而 **`general`（无专家 / 聚合）路径**的 system 是 `build_aggregator()` 内的**硬编码串**，**不经**提示词目录、**不可配置** | 保持现状：**本 ADR 不顺手扩围** —— `general` 路径压根不走 `_run_expert`（走 `build_aggregator()`），其可配置化属**新能力**（须新增 REQ / AC 与提示词层级定义），不在 REV-17 的收窄范围内 | **登记为 OPEN ITEM，待用户 / PM 裁决**；若要求 `general` 人格可配，须回 GROUP_A 立项（**架构层不发明需求、不新增 AC、不自行扩围**） |
| **（REV-18）OI-1：ADR-21「账户↔项目 1:1」与 OQ-IB-28「1:N」的口径张力** | R13 ADR-21 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」 | **用户裁决（2026-10-07）**：关系式明确为 **N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），**由新增修订子节 ADR-21-R1 承接**（**ADR-21 正文一字不动**，amend）；沿用既有 `UserRecord.project_id`（单值）与 `AccountStore` 方法集（**13 方法一字不动**）；ADR-40 已按「**1:N、零迁移**」落地（**不**加唯一约束） | **CLOSED（用户裁决 2026-10-07）** —— 经 **ADR-21-R1** 承接并关闭；**本包未改动任何既有 REQ 文本** |
| **（REV-18）OI-2：LLM Key 首启的供给序（派生后果）** | 用户裁决 Key 存 **DB**、`.env` 仅保留非 LLM Key 的其他密钥（OQ-IB-25 / REQ-NFR-IB-20）；既有装配在「缺 `IB_LLM_API_KEY`」时 `StartupError` → **首启死锁**（DB 无 Key ⇒ 服务不启动 ⇒ 管理界面不可达 ⇒ 无法写入首个 Key） | **用户裁决（2026-10-07）采纳 ADR-39 Option C**：**缺 Key 非致命**，服务正常启动、LLM 依赖路径 **fail-closed 于调用期**（可读错误、不含任何 Key 信息），管理端点与健康端点始终可达；**其余必填项仍 fail-fast**；**备选 Option B（部署期用户手工预置 Key）不采纳**（见 ADR-39 Consequences 补记） | **CLOSED（用户裁决 2026-10-07）** —— 采纳 **ADR-39 Option C**；Option B **已评估未采纳** |
| **（REV-18）OI-3：LLM Key 掩码口径** | REQ-FUNC-IB-47 约束①要求「只回掩码 / 存在性与更新时间」 | 架构侧将 `LlmKeyStatus.masked` 定为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道），并**以类型层排除明文**（响应类型无明文字段）；具体掩码字面由施工期定，**本包不写死** | **保持 OPEN（施工期定，不阻塞）**：口径已收敛到「无明文可分」；具体掩码字面由用户在施工期指定（**架构层不发明**） |

**（REV-17）OPEN ITEM — 需求侧缺口（登记，不发明）**：REV-17 的收窄使「**提示词域**成为提示词文本的唯一可写载体」，但**聚合 / 无专家路径（`general`）的人格串**仍为代码内置且不可配置（见上表末行）。该不对称在 REV-17 **之前即已存在**，本包**只登记、不修复**：修复它须先有需求侧条目（新 REQ / AC）与「聚合人格是否属于提示词域」的定性，**架构层不发明需求**。

**（R14）OPEN ITEM — 需求侧缺口（登记，不发明）**：R14 引入的「**全局管理员的当前项目选择 UX**」与「**`GET /api/projects` 项目枚举端点**」在 `requirements_spec.md` / `user_stories.md` 中**无独立 REQ / AC** 直接覆盖（REQ-FUNC-IB-32 只规定角色与项目边界，未规定前端如何取得「当前项目」）。按纪律**不发明需求、不新增 AC**，登记为 OPEN ITEM，待 **downstream: requirement clarification / GROUP_A** 裁决。**在获得新 AC 之前**，测试门控可将本设计映射到**既有 AC**：AC-IB-24-03（admin 全局可访问任一项目）、AC-IB-24-02（ops 跨项目 403）、REQ-FUNC-IB-31（1:1 绑定）、REQ-FUNC-IB-23（项目隔离 fail-closed）。

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
| **Vue Flow（`@vue-flow/core`，R7 新增）** | **MIT** | **采纳**（可视化配置页的编排图渲染；R7 **经外部核实**：包内 `LICENSE` 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024）；**传递依赖**（D3 系 / `@vueuse/core` 等）须在锁定版本后**逐包核实并登记**，未核实者标 `[待核实]` |
| **Element Plus（R13 新增）** | **MIT** | **采纳**（DR-13；本地 npm 打包，禁 CDN）。**R13 经外部核实后登记**（MIT）；传递依赖须按 `package-lock.json` 锁定后**逐包核实**（tech_stack §2.2） |
| **vue-router（R13 新增）** | **MIT** | **采纳**（前端路由与守卫，ADR-23） |
| **`bcrypt`（Python，R13 新增）** | **Apache-2.0** | **采纳**（口令哈希，DR-11；详见 tech_stack §2） |

**（R1）新增登记**：Django / DRF（BSD-3-Clause）、Waitress（ZPL-2.1）、Gunicorn（MIT）—— 均经外部核实后登记，未凭印象；锁定版本后仍须按发行包内 `LICENSE` 复核。**（R1）撤销**：FastAPI / Uvicorn 退出 Web 层选型（用户指定 Django，见 ADR-11-R1）；Pydantic 退出 Web / 校验层，仅可作**可选**独立校验库，且**不得**作为任何端口契约的载体（ADR-13-R1）。

**（R13）登记规则重申**：Element Plus / vue-router 的**传递依赖**（如 `@element-plus/icons-vue`、`@floating-ui/dom`、`async-validator`、`lodash-es` 等——**具体清单以锁定后的 `package-lock.json` 为准**）须逐包登记；**任一传递依赖出现 copyleft / AGPL 面即须回 tech_stack §1 重新选型**，**不得**沿用「内部平台合规」豁免。**未逐包核实前标 `[待核实]`**。

**（REV-16-2）许可合规**：本增量**未引入任何新第三方依赖** —— 新增物为类型化契约 / 枚举 / frozen dataclass（纯 stdlib）、纯函数（stdlib）、现有库（Vue 3 / Element Plus / DRF / 既有前端图库）的既有用法扩展，以及新增配置键名（不含值）。故 §10.2 台账**无新增条目**，`tech_stack.md` **保持 1.4.0 / REV-13 不变**（REQ-NFR-IB-12 结论不变）。

完整选型与风险表见 `tech_stack.md`。

**（REV-16-4）许可面未变**：本增量**未引入任何第三方组件** —— 配置审计落点复用**同一 SQLite**（stdlib `sqlite3`）与既有手写迁移机制（`003_accounts.sql` → `004_config_audit.sql`）；其余新增均为 frozen dataclass / Protocol / 纯 stdlib。故本节许可台账**不变**（`tech_stack.md` 记 **NO_CHANGE**）。

**（REV-18）许可面未变**：本增量**未引入任何第三方组件** —— 项目注册表与 LLM Key 载体均复用**同一 SQLite**（stdlib `sqlite3`）与既有手写 scoped 迁移机制（新增迁移 `005_projects.sql` / `006_llm_key.sql`）；其余新增均为 frozen dataclass / Protocol / 纯 stdlib。故本节许可台账**不变**（`tech_stack.md` 为**登记型口径修订**——凭据载体说明由「一律经环境变量」收窄为「**除外 LLM Key**」，**无新第三方依赖**，见 Part C）。

### 10.3 自检声明

- 本文所有 ADR 均含 Context（**REQ-* 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences 五节。
- 本文**不含任何实现代码**：所有片段均为接口签名、类型注解、数据结构与架构级约定。
- 本文**未给出任何编造的实测数值**：性能相关内容一律标注 `[ESTIMATE]` 或 `[TBD-Tn]`。
- 隔离设计**贯穿上传 → 存储 → 检索 → 路由上下文**（§3.1），并给出 8 类跨项目泄漏失败模式与逐条防护（§3.3）。
- REQ → MOD 覆盖率矩阵（**36 条 REQ-FUNC 全覆盖**；R13 同步计数）、模块依赖图 DAG 无环证明、类型化接口契约、组合根装配表见 `module_design.md`。
- 本阶段**止于 GROUP_B**：未进入 GROUP_C，未调用任何实现类子代理，**未修改 FreeArk 仓库任何文件**，**未在任何输出中写入凭据/密钥/令牌**。
- **（R1）框架切换复核已逐条留痕**：§2.0 给出 ADR-01 ~ ADR-13 共 **13 行**影响复核表（**受影响 5 条**：ADR-03 / 07 / 08 / 11 / 13；**不受影响 8 条**：ADR-01 / 02 / 04 / 05 / 06 / 09 / 10 / 12），受影响者均有对应的 `-R1` 修订节或更正说明，**无一条 ADR 未复核**。
- **（R1）不变约束未被破坏**：模块数仍 **25**（MOD-IB-01 ~ MOD-IB-25）、端口仍 **13**、IFC-IB 契约编号（**58 个使用中**）**全部未变**（仅改**载体说明**；ADR-01 的方法数 11 / IFC-IB-100~110 为**与 `module_design.md` 对齐的一致性更正**）；REQ→MOD 覆盖仍为 **27/27 REQ-FUNC（R7 同步计数；R1 时点基线为 24/24）+ 14 条 NFR**；模块依赖图 **DAG 无环**（证明未受改动影响，见 `module_design.md` §4.2.1）。
- **（R1）凭据纪律**：本文所有凭据相关表述一律为「**环境变量注入**」；**未写入任何凭据 / 密钥 / 令牌**；**URL 与文档中不得出现凭据型查询串**（`?token=` 类），该纪律已写入 ADR-11-R1（强制约束 (a)）与 `tech_stack.md` §3 / §4.5 检查项 8。
- **（R1）需求侧与 FreeArk 未受影响**：`requirements_spec.md` / `user_stories.md` **未作任何修改**；`FreeArk` 仓库**任何文件未作任何修改**。
- **（R2）L-03 补交已闭合**：`ib-embed` 具**模块归属**（MOD-IB-26）与**契约单一落点**（`docs/ib_embed_service_contract.md`，IFC-IB-266~274）；ADR-02 追加 **R2 附注**（Decision 未改）；新增 **§2.0.1 R2 影响复核表**（**受影响 1 条**（ADR-02，仅补附注）／**R2 不受影响 12 条**，无一条跳过），并为 ADR-04 / 06 / 11 / 13 追写 inline 复核句。
- **（R2）不变约束未被破坏**：`IFC-IB-001~265` 一字不动（新增 266~284 / 286；285 预留未分配）；端口数仍 **13**（**R7 同步：13 → 14，新增 `DefinitionDocumentStore`，纯追加**）；REQ→MOD 覆盖仍 **27/27 REQ-FUNC（R7 同步计数；R2 时点基线为 24/24）+ 14 NFR**；依赖图**仍为 DAG**（模块数 25 → 26，新增单边 `26 → {01,02,04}` 且 26 无入边）；**错误码语义映射不变式**（4xx/409 = 重试无用，5xx = 重试可能有用）已随 ADR-02-R2 附注登记。
- **（R2）凭据纪律**：全文仍只登记**键名**；`ib-embed` **不需要任何令牌**；**URL 与文档一律不得出现凭据型查询串**（该纪律在 R2 扩展至**全部**端点，含新增的图片端点）。
- **（R7）可视化配置增量已贯通**：新增 **ADR-14 / ADR-15 / ADR-16**（编辑模型 / 单一真源（双向同源）/ 装配期 fail-fast 准入闸门），每条含 **≥2** 方案且含「已评估未采纳」留痕；新增 **§2.0.2 R7 影响复核表**（**既有 13 条 ADR 全部不受影响**、新增 3 条、**无一条跳过**）；新增**第 14 个端口** `DefinitionDocumentStore`（IFC-IB-287）；§6 明确「图编译输入 = 校验通过的定义文档；拓扑不可编辑」。
- **（R7）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、`IFC-IB-001~286` 一字不动（新增 287~297；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（论证见 `module_design.md` §4.2.2）；REQ→MOD 覆盖 **27/27 REQ-FUNC + 14 NFR**（由 24/24 同步）。
- **（R7）前置条件已登记且不阻断**：`[ARCH-ASSUMPTION-A7]`（可视化落地前提 = IB-01 / IB-02 的定义外置）+ §10.1 对应行；**REV-07-6 判定 = (a) 可登记前置条件 / 风险，本轮继续**；**未**在本轮自行设计 IB-01 / IB-02 的实现方案（超 GROUP_B 边界）。
- **（R7）凭据纪律**：全文仍只登记**键名**（`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；定义文档**只出现键名、不出现凭据值**；界面与校验错误信息均**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；**URL 与文档一律不得出现凭据型查询串**（该纪律在 R7 扩展至全部新端点，含定义的 GET / PUT）。
- **（R7）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`implementation_plan.md`（GROUP_C）**未作修改**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为离线自检**用例数**，与本文件的 REQ 计数 27 属不同口径，**不得混淆、不得改动**）。
- **（R8）REQ-FUNC-IB-20 的设计覆盖闭环已贯通**：需求侧补入 **US-IB-19 / US-IB-20**（11 组 AC）后，本轮新增 **ADR-17**（3 方案，Option B）与 **§2.0.3 R8 影响复核表**（**既有 16 条 ADR 全部不受影响**、新增 1 条、**无一条跳过**）；§1.3 追加 R8 注、§6 追加四条规范化补充、§8 新增 [ARCH-ASSUMPTION-A8]、§9 新增 [TBD-T21]、§10.1 追加 OQ 默认取值落地行；设计侧落点模块与 IFC 见 `module_design.md` §9.6。
- **（R8）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口数仍 **14**、`IFC-IB-001~297` 一字不动（新增 298~308）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.3）；REQ→MOD 覆盖 **27/27 REQ-FUNC + 14 NFR**（**无新 REQ**）。
- **（R8）「安全失败」为类型层事实**：会话状态丢失的 fail-closed 由 `SessionStateLossOutcome` 的**唯一取值** `fail_closed_restart_required`（IFC-IB-299）与纯函数 `can_resume`（IFC-IB-306）固定，**不依赖纪律约定**；`CompletionPayload.citations` 可为空元组使「不臆造引用」成为结构事实（IFC-IB-300）。
- **（R8）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` v1.3.0 / `user_stories.md` v1.3.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未作修改**；`tech_stack.md` **未改**（R8 无新第三方依赖：本轮新增均为**类型定义**与**配置值域扩展**（`IB_SESSION_BACKEND` 增列 `external` 取值），**不新增任何外部库 / 二进制 / 服务**，故 §10.2 许可合规结论无新增条目）；**未写入任何凭据值**（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）。
- **（R13）认证与商用界面增量已贯通**：新增 **ADR-18 ~ ADR-27**（10 条，每条含 Context（**REQ 引用**）/ Options（**≥2**）/ Decision / Status / Consequences）；新增 **§2.0.4 R13 影响复核表**（**既有 17 条 ADR 全部不受影响**、新增 10 条、**无一条跳过**）；新增**第 15 个端口** `AccountStore`（IFC-IB-310）；§1.3 追加 R13 注、§8 新增 [ARCH-ASSUMPTION-A9]、§9 新增 [TBD-T22] / [TBD-T23]、§10.1 / §10.2 追加行。
- **（R13）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 14 → **15**（**纯追加**）、`IFC-IB-001 ~ 308` 一字不动（新增 **309 ~ 332**；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.4）；REQ→MOD 覆盖 **36/36 REQ-FUNC（由 27 同步）+ 18 NFR（由 14 同步）**。
- **（R13）「单一授权真源 / 安全失败」为架构层事实**：授权判定仍**只**经注入的 `AuthzPolicy`（ADR-22）；生产未配置 `IB_AUTHZ_POLICY_MODULE` 即 `StartupError`（fail-closed，B9）；**首登强制改密由服务端受限会话在结构上保证**（ADR-20，不可由客户端绕过）。
- **（R13）凭据纪律**：全文**只登记键名**（`IB_ACCOUNT_BACKEND` / `IB_SESSION_TTL_SECONDS` / `IB_SESSION_RENEW_WINDOW_SECONDS` / `IB_DEFAULT_ADMIN_USERNAME` / `IB_DEFAULT_ADMIN_PASSWORD` / `IB_PASSWORD_MIN_LENGTH` / `IB_LOGIN_MAX_FAILURES` / `IB_LOGIN_LOCK_SECONDS` / `IB_AUTHZ_POLICY_MODULE`）；**默认初始口令的字面量不在本文出现**（C-IB-09）；令牌**仅**经 `Authorization` 头；`?token=` 纪律**扩展至全部新端点**（`/api/auth/*`、`/api/accounts*`）。
- **（R13）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；**未写入任何口令 / 令牌 / 密钥字面量**；本阶段**止于 GROUP_B**。
- **（R14）回归缺陷修复增量已贯通**：新增 **ADR-28**（项目上下文的选择与传播；**4 候选方案**，Option B 选定，Option A 作为前端单项目预选便利）与 **§2.0.5 R14 影响复核表**（**既有 27 条 ADR 全部不受影响**、新增 1 条、**无一条跳过**）；新增 IFC **IFC-IB-333 ~ 336**（`GET /api/projects` / `X-IB-Project` 头契约 / 前端 `projectContext` store / `client.ts` 单一注入点，见 `module_design.md` §2.2.5）。
- **（R14）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口数仍 **15**、既有 `IFC-IB-001 ~ 332` 一字不动（新增 **333 ~ 336**）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**；ADR 数 27 → **28**。
- **（R14）fail-closed 纪律未削弱**：前端未选择项目时**不发送** `X-IB-Project`，服务端 `effective_project` 取全局哨兵，项目级端点继续 **fail-closed**（**未选项目 ⇒ 不泄露**）；**禁止**把全局哨兵解析为「全部项目并集」（ADR-28 Option C 被拒）。
- **（R14）凭据纪律**：`X-IB-Project` **不是**鉴权凭据、**不**携带任何敏感值；令牌**仅**经 `Authorization` 头；`?token=` 纪律**对其余端点同样有效**；全文**未写入任何口令 / 令牌 / 密钥字面量**（只登记头名与键名）。
- **（R14）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md` 与 `tech_stack.md` **未改**；本阶段**止于 GROUP_B**。
- **（REV-16-2）提示词与工具可视化配置增强已贯通**：新增 **ADR-15-R1**（对 ADR-15 的正式修订，**amend**）、**ADR-29 / ADR-30 / ADR-31 / ADR-32**（每条含 Context（**REQ 引用**）/ Options（**>=2**）/ Decision / Status / Consequences）；新增 **§2.0.6 R16-2 影响复核表**（**既有 28 条 ADR 全部已复核**、新增 4 条、**无一条跳过**）；新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）与 **IFC-IB-337 ~ 354**（18 条，见 `module_design.md` §2.2.6）；§1.3 追加 R16-2 注、§8 新增 [ARCH-ASSUMPTION-A10]、§9 新增 [TBD-T24]、§10.1 / §10.2 追加行。
- **（REV-16-2）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 15 → **16**（**纯追加**）、`IFC-IB-001 ~ 336` 一字不动（新增 **337 ~ 354**；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.6）；REQ→MOD 覆盖 **42/42 REQ-FUNC（由 36 同步）+ 19 NFR（由 18 同步）**。
- **（REV-16-2）时效与图纪律未削弱**：生效口径为「**保存 + 服务重启重装配**」（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载，**不重编译编排图**（REQ-FUNC-IB-26 ②）；「无需重启即生效」类断言**全部不在**验收范围。
- **（REV-16-2）真源与 fail-safe 为契约事实**：真源按域唯一（定义文档 = 结构 / 配置域；提示词目录 = 提示词域），**重叠第二真源被结构性排除**（ADR-15-R1）；`effective_prompt` **恒非空**（ADR-29）；保存失败 / 校验拒绝时**在用配置保持原状**（fail-safe，REQ-NFR-IB-19）；`ValidationReport` **不含** `force` / `ignore` / `warn_only`（类型层事实不变）。
- **（REV-16-2）凭据纪律**：全文**只登记键名**（`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED`）；提示词正文与定义文档**不回显任何凭据值**；令牌仅经 `Authorization` 头；`?token=` 纪律**扩展至全部新端点**（`/api/config/prompts*`）；**未写入任何口令 / 令牌 / 密钥字面量**。
- **（REV-16-2）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
- **（REV-16-4）回归缺陷修复增量已贯通**：新增 **ADR-33 / ADR-34 / ADR-35**（保存期校验落点 / 可查询审计记录载体 / 内存态提示暴露；每条含 Context（**REQ 引用**）/ Options（**>=2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.7 R16-4 影响复核表**（**既有 32 条 ADR 全部已复核**、新增 3 条、**无一条跳过**）；新增 **IFC-IB-355 ~ 363**（9 条，见 `module_design.md` §2.2.7）；§1.3 追加 R16-4 注、§8 新增 [ARCH-ASSUMPTION-A11]、§9 新增 [TBD-T25]、§10.1 新增 OPEN ITEM、§10.2 追加 R16-4 说明。
- **（REV-16-4）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 16 → **17**（**纯追加**）、`IFC-IB-001 ~ 354` 一字不动（新增 **355 ~ 363**；`IFC-IB-285` 仍预留未分配；既有重号 `IFC-IB-131` 登记不修）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.7）；REQ→MOD 覆盖**不变**（42/42 REQ-FUNC + 19 NFR；本增量**不新增 REQ、不改 AC**）。
- **（REV-16-4）fail-safe 与时效纪律未削弱**：保存期校验拒绝 / 审计写失败均**不得破坏在用配置**（REQ-NFR-IB-19；ADR-33 / ADR-34）；生效口径仍为「**保存 + 服务重启重装配**」（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载，**不重编译编排图**。
- **（REV-16-4）非第二真源为契约事实**：`ConfigAuditStore` 端口**无 update / delete**（只读审计）；**无配置读取路径消费审计**；`ConfigAuditEntry` **只含字段名与结果码**，不含任何配置取值（ADR-34）。
- **（REV-16-4）凭据纪律**：全文**只登记键名 / 头名 / 表名**（`IB_DEFINITION_DOC_PATH` / `IB_EXPERT_PROMPT_DIR` / `config_audit`）；审计与响应**不回显任何取值 / 凭据**；令牌仅经 `Authorization` 头；`?token=` 纪律**扩展至全部新端点**（`/api/config/audit`、`/api/config/storage-state`）；**未写入任何口令 / 令牌 / 密钥字面量**。
- **（REV-16-4）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
- **（REV-17）提示词兜底层重定位已贯通**：新增 **ADR-36**（提示词兜底层重定位：文件两层 + 代码内置安全网；含 **4** 候选方案与 **3** 项已评估未采纳留痕）与 **ADR-15-R2**（对 ADR-15 的**第二次**正式修订子节，**收窄** ADR-15-R1 规则 ⑤ 的兜底层载体）；**ADR-15 与 ADR-15-R1 正文一字不动**；修订 **ADR-29**（`resolved_from` 第三值更名 + 「兜底恒非空」改由结构保证）与 **ADR-33**（单入口上提为 `validate_two_domains`，范围**含提示词域**）；新增 **§2.0.8 R17 影响复核表**（**既有 35 条 ADR 全部已复核**、新增 1 条、**无一条跳过**）；新增 **IFC-IB-364 / 365**（2 条，见 `module_design.md` §2.2.8）；§8 修订 [ARCH-ASSUMPTION-A10]（`fallback.md` **不得缺 → 亦可缺**）、§10.1 新增 OPEN ITEM（`general` / 无专家路径的人格串不可配置）、§10.3 追加 R17 自检。
- **（REV-17）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口数仍 **17**（**未新增端口**）、`IFC-IB-001 ~ 363` **号 / 名 / 签名一字不动**（**仅 10 条文字的取值口径修订**，逐条登记于 §2.0.8；新增 **364 / 365**；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**；REQ→MOD 覆盖**不变**（42/42 REQ-FUNC + 19 NFR；本增量**不新增 REQ、不改 AC**）；**不 bump `schema_version`**（无迁移机制；改由 legacy 键分级处置兜底）。
- **（REV-17）第二写入口被结构性排除**：`ExpertSpecInput` **不再有** `fallback_prompt` 字段（移出 schema / 白名单 IFC-IB-291 / 定义域校验项），提示词文本的**唯一可写载体** = 目录 `main.md` / `fallback.md` 两层文件；代码内置兜底（`BUILTIN_FALLBACKS` / `BUILTIN_FALLBACK_DEFAULT`，IFC-IB-365）**不可经界面编辑**，**只读回显**（`/api/config/prompts` 的 per-expert `builtin_fallback`；**顶层 5 键集不变**）；写入口纪律由**不存在第三个端点**成为结构事实（`builtin` / `default` 等层名一律 `404`）。
- **（REV-17）兜底恒非空由结构保证 + 死锁已破**：`merge_prompt_layers` 的 `effective_prompt` **不可能为空**（`builtin_fallback_for` 对**任意**专家名非空，全函数）；「界面新增专家」死锁（`PUT definition` 要兜底 × `PUT prompts/<新专家>/fallback` 因未登记 `404`）**由通用安全网打破**；**反越域不受影响** —— 孤儿提示词文件**仍被拒**（`prompt_orphan_file`），通用兜底**不是**把校验整体关掉。
- **（REV-17）legacy 键 fail-closed 而非静默丢弃**：旧文档残留 `experts[].fallback_prompt` 与内置**逐字相同** → 静默丢弃（零信息损失）；**不同** → **抛 `ConfigError`** 并指明迁移目标 `<root>/<project_id>/<name>/fallback.md`，错误消息**只报长度、不回显提示词正文**（对齐 IFC-IB-348 纪律）——**绝不静默丢弃用户手写的提示词**。
- **（REV-17）系统位通道矫正 + 假陈述消解**：合并后的生效提示词**必须**经 `build_expert(spec, *, system_prompt=...)` 进 **system 消息**，human 位**只**留用户问题；`_run_expert` 传 `system_prompt=prompt or None`（空串会致 `_make_langchain_client` 返回**裸客户端** → **同时静默失去** system 消息与 function-calling）；`build_expert` 声称存在 `system_prompt` 覆盖形参而实际不存在的**假陈述 docstring 随之消解**（形参真实落地，IFC-IB-212）。`_clients` 缓存硬规则：`system_prompt` **只允许是装配期常量**。
- **（REV-17）时效纪律未削弱**：生效口径仍为「**保存 + 服务重启重装配**」（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载，**不重编译编排图**（REQ-FUNC-IB-26 ②）；`fallback.md` 可缺**只改变合并结果取值来源，不改变生效时机**。
- **（REV-17）凭据与仓库纪律**：全文**只登记键名 / 头名 / 表名 / 文件层名**；提示词正文与定义文档**不回显任何凭据值**；令牌仅经 `Authorization` 头，`?token=` 纪律对全部既有端点有效；**未写入任何口令 / 令牌 / 密钥字面量**；`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档**只读未改**（落盘载体措辞的同步**另立交付项**）；本阶段**止于 GROUP_B**。
- **（REV-18）系统管理 / 项目 / LLM Key / 项目域资料增量已贯通**：新增 **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42**（每条含 Context（**REQ 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 全部已复核**：不受影响 **32**、口径补注 **4**（ADR-08 / 18 / 28 / **21**，其中 ADR-21 由新增修订子节 **ADR-21-R1** 承接）、待裁决 **0**、**新增 6**、**无一条跳过**）；新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368）；新增 IFC **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）；§1.3 追加 R18 增补段与 2 行、§8 新增 [ARCH-ASSUMPTION-A12]、§9 新增 [TBD-T26] / [TBD-T27]、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3；**OI-1 / OI-2 经用户裁决 2026-10-07 关闭，OI-3 保持 OPEN**）、§10.2 追加「许可面未变」句。
- **（REV-18）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 17 → **19**（**纯追加**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9：`IFC-IB-024` / `262` / `263` / `321` / `333`）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.8）；REQ→MOD 覆盖 **48/48 REQ-FUNC（由 42 同步）+ 20 NFR（由 19 同步）**。
- **（REV-18）红线未被破坏（强制）**：REQ-FUNC-IB-48 / C-IB-43 的「**取代知识库标识**」**未**削弱 `architecture_design.md:120`（「**范围不可由客户端自证**」）—— `kb_id` **由已认证主体的 `project_id` 推导**，**请求体不再接收 kb 字段**，且**保留** `LedgerRepository.assert_kb_in_project`（IFC-IB-130）归属断言，失败仍 **403**（非 404）。**「UI 分组不是权限机制」**：ADR-42 明令非 admin 一律**服务端 403**（授权唯一经注入的 `AuthzPolicy`，ADR-22 复用）。
- **（REV-18）凭据纪律（新增口径）**：① LLM Key **载体 = DB**（**不入 `.env`**、**不进 git**、**不进命令行 / shell history**）；**唯一写入口** = `PUT /api/llm-key`；HTTP 只回 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），**不回显明文为类型层事实**；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**；承载**库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；[ARCH-ASSUMPTION-A12]；检查清单 B22）。② `.env` **仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**（登记型口径修订，`IFC-IB-024` / `262` / `263`）。③ 全文**只登记键名 / 头名 / 表名 / 字段名 / 文件名**；**未写入任何口令 / 令牌 / Key / 证书字面量**；令牌仅经 `Authorization` 头，`?token=` 纪律对**全部新端点**有效（`/api/projects*`、`/api/accounts*`、`/api/llm-key`）。
- **（REV-18）生效口径与运维动作（登记，不自动执行）**：Key / 项目 / 账号的保存与变更**一律经「保存 + 服务重启重装配」生效**（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载、**不重编译编排图**；**登记：生产后端重启与首次环境变量配置须由用户执行** —— 架构 / 部署文档只写「由用户执行」的动作，**不设计为代理自动执行**。
- **（REV-18）OQ / OPEN ITEM 处置（用户裁决 2026-10-07 后）**：**OI-1**（ADR-21 的 1:1 口径张力）**已由 ADR-21-R1 承接并关闭**（ADR-21 正文一字不动）；**OI-2**（LLM Key 首启供给序）**已关闭**（采纳 **ADR-39 Option C**，缺 Key 非致命；备选 Option B 已评估未采纳）；**OI-3**（掩码字面）**保持 OPEN**（施工期定，不阻塞）。架构层**未自行改写 ADR-21 正文、未自行拍板业务数值、未新增 REQ、未改 AC**。
- **（REV-18）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` v1.10.0 / `user_stories.md` v1.10.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **仅登记型口径修订**（凭据载体说明收窄，**无新第三方依赖**，见 Part C）；本阶段**止于 GROUP_B**。
