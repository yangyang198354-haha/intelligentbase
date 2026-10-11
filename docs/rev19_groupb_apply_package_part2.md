# REV-19 GROUP_B 架构增量 — Apply-Ready 修订包 · Part 2（新 ADR 全文 / §2.0.10 全 ADR 复核表 / 新 IFC 契约）

<file_header>
  <project>intelligentbase</project>
  <artifact>rev19_groupb_apply_package_part2</artifact>
  <path>docs/rev19_groupb_apply_package_part2.md</path>
  <doc_id>ARCH-PKG-INTELBASE-REV19-B-P2</doc_id>
  <version>1.0.0</version>
  <revision>REV-19</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-19 增量（apply-ready package）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-014</invocation_id>
  <created_at>2026-10-11</created_at>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
    <readonly_reference path="docs/architecture_design.md" version="1.10.2" revision="REV-18-R2" note="目标文件；本包为其 REV-19 增量，编号只增不改"/>
    <readonly_reference path="docs/module_design.md" version="1.10.2" revision="REV-18-R2" note="目标文件；本包为其 REV-19 增量，编号只增不改"/>
  </inputs>
  <scope_boundary>只做架构与模块设计；不含实现代码、测试用例、部署脚本。允许接口签名、类型注解、数据结构定义。</scope_boundary>
</file_header>

> **性质**：本文件是 `docs/rev19_groupb_apply_package.md` 的 **Part 2**，承载「新 ADR 全文（ADR-43 ~ ADR-47）」、`architecture_design.md` 的 **§2.0.10 REV-19 影响复核表（全 42 条 ADR 逐条）**、以及**新 IFC 契约全文**。编辑条目（落点/锚点）在 Part 1 / Part 3。
> **纪律**：本包**不覆盖**任何 APPROVED 文件；由 PM 机械 Edit 落盘。**编号只增不改**：新 ADR 自 **43** 起，新 IFC 自 **378** 起；既有 ADR / IFC / 模块 / 端口编号与正文**一字不动**。模块数 **26**、端口数 **19**、§4.1 依赖边**逐行不变（零新增边）**、DAG 无环、**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）。**无实现代码 / 伪代码**；**不含任何口令 / Key / token / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）。

---

# Part E — 新 ADR 全文（ADR-43 ~ ADR-47）

> 落点：`docs/architecture_design.md`，插入于 **ADR-42 正文末（第 1160 行）之后、`## 3. 多项目隔离…`（第 1162 行）之前**。
> 每条含 Context（**REQ 引用**）/ Options（**≥2，含已评估未采纳项**）/ Decision / Status / Consequences 五节。

---

### ADR-43 每项目专家注册表的解析与 C-IB-45 不变量的结构保证

- **Status**: Accepted
- **Context**: **REQ-FUNC-IB-49**（每项目专家集隔离；配置页可切换 / 加载自己的专家 agent）、**REQ-NFR-IB-21**（专家域 fail-closed 与可观测）、**C-IB-44**（每项目专家集隔离）、**C-IB-45**（两条不变量：① **默认专家恰好一个**；② **永不无应答**）、**OQ-IB-34(a)**（硬隔离）、**OOS-20**（专家集硬隔离）。**一手事实锚点**：**F4** —— `EXPERT_SPECS` 为**进程级单例**（`src/ib/experts/__init__.py:215`），`install()` / `install_derived()` 以 **rebind 模块级全局**的方式注入；**F8** —— `orchestrator_for(project_id)` 消费**全局** `EXPERT_SPECS`（`src/ibweb/composition.py:189-225`，取全局处 `200` / `213`）；**S-4** —— `_default_definition_document(project_id, cfg)` 取**全局** `EXPERT_SPECS`（`composition.py:1190 / 1207 / 1221 / 1251`）；**装配期「首项目 → 全局 rebind」点** —— `composition.py:633-634`（`_inject_derived_experts` / `_inject_prompt_bundles`）；**路由侧** —— `src/ib/routing/intent.py`（`names` / `default_expert` / `keywords_map` / `data_experts` / `EXPERT_SPECS` 在**调用期**读进程级全局）。与 **ADR-15 / ADR-15-R1**（真源分域：定义文档 = 结构 / 配置域；独立 markdown 目录 = 提示词域）一致。
- **Options**:
  - **Option A 进程级「按 `project_id` 键的注册表字典」**：把 `EXPERT_SPECS` 由单例改为 `dict[project_id, tuple[ExpertSpec, ...]]`，全部访问器加 `project_id`**位置形参**。优—改动局部，调用点统一；缺—**仍是可变进程级全局**，装配顺序耦合（后装配项目可覆盖先装配项目），类型层**无法**保证「默认专家恰一个 / 永不无应答」（仍是运行期字典查找 + 兜底）。
  - **Option B（选定）装配期每项目解析为不可变 `ExpertRegistryView`，随装配产物 `Deps` 携带并显式注入消费点**：进程级 `EXPERT_SPECS` 降级为「**内置默认单例 + 代码兜底安全网**」（离线 / 未配置路径 / 提示词文本缺失兜底），**退出生产装配主路径**。优—真源单一（项目定义文档 + 项目提示词目录）；**无跨项目泄漏**；视图为 **frozen 值对象**（可测）；与 **ADR-32** 生效口径一致（装配期解析、重启重装配）；**C-IB-45 两条不变量由结构保证**（`ExpertRegistryView.default_expert` 为**必填非空字段** → 「默认专家恰一个 / 永不无应答」**不可表达为非法态**）。缺—须把专家集穿过 `orchestrator_for` / `IntentRouter` / `_default_definition_document` 等消费点（改签名须 **append-only 可选形参**）。
  - **Option C 请求期按 `project_id` 解析**：每次请求查定义文档解析专家集。优—无装配期状态；缺—**引入运行期热生效**（违反 ADR-32 / C-IB-40 / OOS-16）、每请求 IO / 解析开销、fail-closed 面扩大。**（已评估未采纳）**
- **Decision**: **Option B**。① **真源** = 项目定义文档（结构 / 配置域）+ 项目提示词目录（提示词域），装配期合并派生为该项目 `ExpertRegistryView`；② **载体** = 既有装配产物 `Deps.derived_views[project_id]`（`composition.py:620-632`），新增 `resolve_expert_registry(project_id)`（IFC-IB-380）构造视图；③ 进程级 `EXPERT_SPECS`（含 `install_derived` 全局 rebind）**退出生产装配主路径**，仅作**内置默认单例**（IFC-IB-381）与**代码兜底安全网**；④ **消费点显式注入**：`orchestrator_for`（`composition.py:200 / 213`）取**本项目视图**；`IntentRouter` 增 **keyword-only 可选** `experts`（IFC-IB-382；`None` → 内置默认单例，行为与既有**逐位一致**）；⑤ `_default_definition_document`（`composition.py:1190 / 1207 / 1221 / 1251`）改用「**该项目自身**的专家集」；⑥ `_inject_derived_experts` / `_inject_prompt_bundles` 的「**取首个项目 → 全局 rebind**」（`composition.py:633-634`）**退化为兼容保留**（仅离线 / 未配置路径），标注「REV-19 起不再作为生产真源」；⑦ **零新增模块、零新增端口、零新增依赖边**（落点并入 MOD-IB-16 / MOD-IB-19 / MOD-IB-23）。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-49 / C-IB-44 / OOS-20（硬隔离）；满足 REQ-NFR-IB-21（fail-closed + 结构化）；**C-IB-45 两条不变量成为类型层事实**（`ExpertRegistryView.default_expert` 必填非空 + 内置不可删默认专家种子），**不依赖「校验放行」**；跨项目专家集泄漏面**结构性消除**（复用 §3.3 FM-6 纪律）。
  - 负向：若干调用点签名需 append-only 扩展；`Deps` 携带**每项目视图**的装配期内存增量（以 **[TBD-T28]** 校准）；`install_derived` 路径的既有单测须按「**内置默认单例**」语义重述（**不改变**既有 IFC 号 / 名 / 签名）。

---

### ADR-44 定义文档物理载体目录化（`IB_DEFINITION_DOC_PATH` 文件 → 目录）与 C-IB-46 部署迁移

- **Status**: Accepted
- **Context**: **REQ-FUNC-IB-50**（可视化配置可切换 / 加载自己项目的专家 agent）、**OQ-IB-32(b)**（**每项目一份文件**）、**OQ-IB-39**（接受语义变更及其部署面影响）、**C-IB-46**（部署约束与迁移要求）、**C-IB-38**（须用户手工执行的步骤须显式列出）。**一手事实锚点**：**F5** —— `FileDefinitionDocumentStore.load(project_id)` **忽略 `project_id`**、只读 `self._path`（`src/ib/config/definition.py:874-884`），与 `[ARCH-ASSUMPTION-A6]`（一项目一文档）不符；生产现值为**单文件** `/var/lib/intelligentbase/definition.json`。内存版 `InMemoryDefinitionDocumentStore` **已按项目**（`definition.py:803-831`，见 S-2）。
- **Options**:
  - **Option A（选定）`IB_DEFINITION_DOC_PATH` 语义由「文件路径」改为「目录根」**，每项目一文件 `<dir>/<project_id>.json`；旧单文件一次性迁移为 `<dir>/demo.json`（**用户手工 + 先备份 + 失败回滚**）。优—与内存版（S-2）逐位一致；把 A6 / S-3 从纸面**落到实现**；缺—**破坏性口径变更**（旧值「指向文件」不再合法），部署面须一次性迁移。
  - **Option B 新增独立键 `IB_DEFINITION_DOC_DIR`，保留旧键「文件」语义双键并存**：优—兼容窗口；缺—**双键并存引入「哪个是真源」歧义**（违反 ADR-15 真源唯一）、配置面扩大；OQ-IB-32(b) **未**要求并存。**（已评估未采纳）**
  - **Option C 载体改为 DB 表**（复用同一 SQLite，同 ADR-37 / ADR-38 载体）：优—与注册表 / Key 同载体；缺—**超出 REV-19 范围**（需求未要求、OOS 未列）；`[ARCH-ASSUMPTION-A6]` 已定「本地文件」；迁移面更大。**（已评估未采纳；作为可替换点保留）**
- **Decision**: **Option A**。① **目录布局** = `<dir>/<project_id>.json`（**一项目一文件**；与内存版一致，落地 A6 / S-3 / OQ-IB-32(b)）；② `FileDefinitionDocumentStore` 构造形参语义改为**目录根**，内部按 `_path_for(project_id)` 解析（**IFC-IB-383**）；`load` / `save` 按 `project_id` 解析（**消除 F5 偏差**）；**端口 `DefinitionDocumentStore`（IFC-IB-287）签名不变**（`load` / `save` 本就带 `project_id`；仅文字口径修订）；③ **兼容 / 迁移路径（C-IB-46）**：`migrate_legacy_definition_file(dir_root, target_project_id="demo", backup=True)`（**IFC-IB-384**）—— 目录不存在则创建；旧单文件存在且 `<dir_root>/demo.json` **不存在** → **备份后移动**；目标**已存在** → **fail-closed，不覆盖**；④ **失败回滚**：语义变更后目录未配置 / 不可用 → **装配期 fail-closed**（可读错误 + **指明迁移目标**），**不回退到「单文件」旧语义、不静默当空文档**；⑤ 迁移**由用户手工执行**（C-IB-38），**先备份、失败回滚**；⑥ 落点并入 **MOD-IB-02**（数据层）/ **MOD-IB-25**（检查清单 B24）；**零新增模块 / 端口 / 依赖边**。
- **Consequences**:
  - 正向：**F5 偏差闭合**；A6 从纸面落地；配置页「切换 / 加载自己项目的专家 agent」成立（REQ-FUNC-IB-50）；与内存版逐位一致。
  - 负向：**部署面一次性迁移**（生产 `definition.json` → `<dir>/demo.json`；**用户手工 + 备份 + 回滚**）；`IB_DEFINITION_DOC_PATH` 语义变更属**破坏性口径变更**，须在部署检查清单 **B24** 显式（IFC-IB-388）。

---

### ADR-45 新项目默认种子与「三专家属 `demo`」

- **Status**: Accepted
- **Context**: **REQ-FUNC-IB-52**（新项目默认种子：**1 个 KB 问答 agent + 1 个默认编排流**）、**REQ-FUNC-IB-53**（**三专家属 `demo`**，非 demo 隐藏）、**C-IB-44**、**OQ-IB-33(a)**（内置**不可删**默认专家）、**OQ-IB-35(a)**（三专家在非 demo **隐藏**）、**OQ-IB-36(a)**（**单一默认编排流**、不自定义 DAG）、**OOS-21**、**US-IB-44 / US-IB-45**。**一手事实锚点**：**F7** —— `POST /api/projects` **不 seed**（`src/ibweb/views.py:1467-1490`，仅注册表写 + `reload_projects()`）；**F6** —— 三内置专家 `freeark-expert` / `inspection-expert` / `sanheng-knowledge`（`src/ib/experts/__init__.py:96-177`）；**F4** —— 全局单例（同上 ADR-43）。
- **Options**:
  - **Option A（选定）创建期播种**：`POST /api/projects` 注册表写入成功后，由组合根**同步** `seed_project(project_id)`（**IFC-IB-385**）—— 写 `<dir>/<project_id>.json`（该项目专家集 + **单一默认编排流**）+ 提示词目录骨架 `<root>/<project_id>/<expert>/`；**新建项目种子 = 内置默认单例（1 个 KB 问答 agent）+ 1 默认编排流**；**`demo` 项目种子 = 三对齐专家**。**种子真源 = 项目自身专家集**。
  - **Option B 懒播种**（首访该项目时播种）：优—创建端点不变；缺—在「未登记项目 **fail-closed**」路径上**引入写操作**；首请求路径副作用；可测性差（无独立创建事件）。**（已评估未采纳）**
  - **Option C 装配期对全部已知项目统一播种**（复用 `_seed_projects` / 既有 `seeds = {pid: … for pid in projects}`）：优—与既有装配一致；缺—项目为**运行期可变**（ADR-37），装配期枚举**覆盖不了装配后新建项目**，会把「新建项目」耦合成「**须重启才可见**」，与 REQ-FUNC-IB-44 运行期 CRUD 张力。**（已评估未采纳；仅保留为装配期兜底）**
- **Decision**: **Option A（创建期播种）**，**装配期兜底保留 Option C 语义**（启动时对未落盘项目构造内置默认种子，等价既有 `_default_definition_document` 的逐项目种子）。① **真源** = 项目自身专家集；新建项目 = **内置默认单例**（KB 问答 agent，`is_default=True`；**内置不可删**，OQ-IB-33(a)）；`demo` = 其三专家；② **落点**：**MOD-IB-23**（`seed_project`，IFC-IB-385）+ **MOD-IB-02**（`_default_definition_document` 改用该项目专家集）+ **MOD-IB-01**（内置默认单例契约，IFC-IB-381）；③ **三专家仅属 `demo`**：`demo` 项目种子含之、**非 demo 项目种子不含** → 非 demo 的专家集在**装配期**即不含三专家，**不是** UI 隐藏；UI 隐藏仅为**体验优化**，**可解析性的裁决者为服务端**（同 ADR-42「UI 分组非权限机制」纪律）；④ **单一默认编排流**（OOS-21；**不提供**自定 DAG 入口）；⑤ **零新增模块 / 端口 / 依赖边**。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-52 / IB-53 / OQ-IB-33(a) / 35(a) / 36(a) / OOS-21；新项目「**开箱即有 1 个 KB 问答 agent + 1 默认编排流**」；**F7 偏差闭合**；「三专家属 `demo`」由**种子差异**结构性保证（**非 UI 约定**）。
  - 负向：`POST /api/projects` 由「**纯注册表写**」变为「**注册表写 + 定义文档 / 提示词目录播种**」，播种失败须**原子回滚**（删除半成品 + 明确错误，**不静默**）；创建耗时增量以 **[TBD-T29]** 校准。

---

### ADR-46 三专家既有会话 / 历史 / 引用的归属数据迁移（C-IB-47 / DR-23）

- **Status**: Accepted
- **Context**: **C-IB-47**（数据迁移要求）、**DR-23**（OQ-IB-40 = **(b)**：迁到 `demo`）、**OQ-IB-40(b)**、**US-IB-45 / AC-IB-45-04**（记录归属改写为 `demo`、**记录保留**、**非 demo 失去该历史**、**手工 + 备份 + 回滚**）、**DR-21**（**误删优先软删**）、**REQ-FUNC-IB-53**。
- **Options**:
  - **Option A（选定）归属改写**：把「归属非 `demo` 且引用三专家」的会话 / 历史 / 引用记录的**所有权字段 `project_id` 改写为 `demo`**；**记录保留**（**不删除任何行**）；幂等；备份 + 可回滚；显式登记「**非 demo 项目失去该历史**」。
  - **Option B 删除这些记录**：缺—**违反 DR-21**（软删优先）；不可逆。**（已评估未采纳）**
  - **Option C 复制到 `demo` 且保留原归属**（双份）：缺—同一历史**两份**、引用**真源歧义**、存储膨胀。**（已评估未采纳）**
- **Decision**: **Option A**。**架构范围声明（不含实现代码）**：① **载体** = 会话状态（**MOD-IB-21** 的 `SessionStore` / `SessionState` / `SessionTurn`）+ 台账 `sessions` 表的 `SessionRecord.project_id`（**MOD-IB-11**）+ 引用 / 引文记录（citations）；② **所有权字段** = `project_id`；③ **改写规则** = 「`project_id != 'demo'` 且该会话 / 记录引用了 `freeark-expert` / `inspection-expert` / `sanheng-knowledge` 之一」→ 置 `project_id = 'demo'`；④ **幂等** = 已属 `demo` 的记录**跳过**（重复执行无副作用）；⑤ **与 DR-21 的关系** = 迁移是**归属改写**而非删除、**不删除任何行**，故与「误删优先软删」**无冲突**、**可回滚**；⑥ **显式登记**：「**非 demo 项目因此失去这些历史**」（C-IB-47 / AC-IB-45-04 明文）；⑦ **手工 + 先备份 + 失败回滚**（C-IB-38）；⑧ **落点**：**MOD-IB-21**（会话状态，IFC-IB-386）/ **MOD-IB-11**（`sessions` 表）/ **MOD-IB-25**（迁移交付物与检查清单 B25）；⑨ **零新增模块 / 端口 / 依赖边**。
- **Consequences**:
  - 正向：满足 C-IB-47 / DR-23 / US-IB-45；历史**不丢失**（保留 + 改归属）；**幂等可重复**；与 DR-21 **不冲突**。
  - 负向：**非 demo 项目失去这些历史的可见性**（已登记、可回滚）；迁移脚本须**手工执行**；跨载体（会话态 + SQLite `sessions` 表）一致性以 **[TBD-T29]** 校准。

---

### ADR-47 专家域解析的 fail-closed 与可观测（REQ-NFR-IB-21）

- **Status**: Accepted
- **Context**: **REQ-NFR-IB-21**（专家域 **fail-closed** 与**可观测**）、**AC-IB-41-04**（fail-closed + **结构化日志**）、**US-IB-41**、**C-IB-44**、**C-IB-45**。既有事实：`orchestrator_for` 对**未登记项目**已 **fail-closed**（`StartupError`，**无回退**，`composition.py:195-196`）；装配期闸门为 **ADR-16**（fail-fast，`admit_two_domains`，IFC-IB-353 / 364）。
- **Options**:
  - **Option A（选定）解析失败一律 fail-closed**（未登记项目 / 无定义文档 / **默认专家缺失或非唯一** / 专家集为空）：**装配期** `StartupError`（复用 ADR-16 闸门），**运行期**明确错误（**无隐式回退到其他项目或全局默认**）；并发**结构化日志**（`project_id` / 失败类别 / 关联 REQ）。优—与硬隔离一致、错误可定位；缺—专家域配置错误**阻断启动**（fail-fast 面扩大）。
  - **Option B 解析失败回退内置默认单例**（fail-open）：缺—**跨项目泄漏面**、掩盖配置错误、与「硬隔离」冲突。**（已评估未采纳）** —— 保留一条**受限**的代码内置兜底，**仅**用于**提示词文本缺失**，**不用于专家集解析**（**ADR-36** 不变）。
  - **Option C 仅告警继续**（warn-only）：缺—**静默降级**。**（已评估未采纳）**
- **Decision**: **Option A**。① **fail-closed 触发点**：**装配期**（构造 `ExpertRegistryView` 时默认专家缺失 / 非唯一 / 空专家集 → `StartupError`，IFC-IB-380）；**运行期**（`orchestrator_for` 未登记项目 → `StartupError`，**既有语义一字不动**）；② **结构化日志**：`log_event("expert_domain", <code>, project_id=…, reason=…)`（**不含任何凭据 / 提示词正文**）；③ **不引入**运行期热重载 / 热重编译（ADR-32）；④ **落点**：**MOD-IB-16**（`resolve_expert_registry` fail-closed，IFC-IB-380）/ **MOD-IB-23**（装配期闸门与 `orchestrator_for`）/ **MOD-IB-04**（可观测）；⑤ **零新增模块 / 端口 / 依赖边**。
- **Consequences**:
  - 正向：满足 REQ-NFR-IB-21 / AC-IB-41-04；「**永不无应答**」与「**未登记项目不回退**」成为**可测事实**；错误可定位（结构化字段）。
  - 负向：专家域配置错误**阻断启动**（与 ADR-16 一致，须在部署检查清单显式）；运行期新增一条 fail-closed 分支。

---

# Part F — `architecture_design.md` §2.0.10 REV-19 影响复核表（全 42 条 ADR 逐条，无一条跳过）

> 落点：`docs/architecture_design.md`，插入于 **§2.0.9 末段（第 386 行「R18 被修订 IFC 逐条登记」之后）与第 388 行 `---` 之前**。

```markdown
### 2.0.10 REV-19 影响复核表（每项目专家集隔离 + 定义文档目录化 + 新项目种子 + 三专家属 demo + 专家域 fail-closed 增量）

> **背景**：`requirements_spec.md` v1.11.0 / **REV-19**（APPROVED）新增 REQ-FUNC-IB-49 ~ IB-53、REQ-NFR-IB-21、C-IB-44 ~ C-IB-47、OOS-20 / OOS-21、DR-22 / DR-23，并就 OQ-IB-32 ~ OQ-IB-40 一次拍板。本节对 v1.10.2 的 **42 条 ADR（ADR-01 ~ ADR-42）逐条复核**并登记新增 5 条，作为「设计未因需求增量而漂移」的可审计证据。**无一条跳过**。

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01（向量库抽象 / Qdrant） | **不受影响** | 向量库与 collection 解析未动；REV-19 不触检索载面 |
| ADR-02（embedding 服务形态） | **不受影响** | 冷 / 热双路径与 `ib-embed` 归属未动 |
| ADR-03（部署形态 systemd 裸装） | **不受影响** | REV-19 不新增 systemd 单元（目录化 / 迁移为**文件级**，非新服务） |
| ADR-04（多项目隔离：collection-per-project + KB 软隔离） | **不受影响，且 REV-19 是其应用** | 专家集硬隔离 = **项目级**（不引入 KB 级专家）；隔离边界不变 |
| ADR-05（原始文件持久化 / 索引重建） | **不受影响** | REV-19 不触原文件与重建 |
| ADR-06（PDF 解析库许可） | **不受影响** | **禁 PyMuPDF** 维持；REV-19 无新解析依赖 |
| ADR-07（台账存储） | **不受影响，且 REV-19 复用其载体** | C-IB-47 的历史迁移落在**同一 `sessions` 表**，**无新表** |
| ADR-08（LLM 端点抽象 / 数据外发边界） | **不受影响** | REV-19 不触 LLM 端点与外发声明 |
| ADR-09（编排骨架业务零依赖 / 依赖反转） | **不受影响，且 REV-19 是其应用** | 专家集经**构造期注入**、路由不反向依赖检索；「按项目注入」= 依赖反转的具体化 |
| ADR-10（异步入库执行形态）/ ADR-11（Web 层技术栈 / SSE） | **不受影响** | REV-19 不触入库与流式载体 |
| ADR-12（OCR / 渲染端口） | **不受影响** | REV-19 不触 OCR / 渲染 |
| ADR-13（检索契约与降级） | **不受影响** | REV-19 不触检索契约 |
| ADR-14（可视化编辑模型） | **不受影响，且 REV-19 是其应用** | 「配置页切换 / 加载自己项目的专家 agent」仍为**显式 round-trip + 视图零持久化 + 白名单制**；无第二真源 |
| ADR-15（定义文档单一真源 / 双向同源） | **不受影响** | 真源分域未动；REV-19 把「**一项目一文档**」从纸面**落到实现**，**强化** ADR-15 的项目级真源，**不改结论** |
| ADR-15-R1（分域真源 + 装配期合并） | **不受影响，且 REV-19 是其应用** | 每项目专家集 = 定义文档（结构域）+ 提示词目录（提示词域）**装配期合并** → `ExpertRegistryView`（ADR-43） |
| ADR-15-R2（兜底层收窄） | **不受影响** | 提示词文本唯一可写载体 = 目录两层文件；REV-19 不改 |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 REV-19 是其应用** | 专家域 fail-closed = **复用闸门**（ADR-47）；`ValidationReport` 不含 `force` / `ignore` / `warn_only` 未动 |
| ADR-17（确认中间态） | **不受影响** | 承载与状态丢失语义未动 |
| ADR-18（账户 / 会话落点与载体） | **不受影响** | REV-19 不触账户 / 会话载体 |
| ADR-19（不透明会话令牌） | **不受影响** | 无 Cookie / 只存摘要 / 仅 `Authorization` 头未动 |
| ADR-20（bcrypt 口令与首登强制改密） | **不受影响** | REV-19 不触口令链路 |
| ADR-21（账户↔项目绑定） | **不受影响** | REV-19 不触；口径已由 **ADR-21-R1** 订正为 **N:1** |
| ADR-21-R1（N:1 修订子节） | **不受影响** | 关系式与零迁移未动 |
| ADR-22（单一授权真源） | **不受影响，且 REV-19 是其应用** | 「三专家在非 demo 隐藏」若涉可见性，**UI 隐藏仅为体验优化**；**授权 / 可解析性的唯一裁决者为服务端**（复用 ADR-42 纪律） |
| ADR-23（前端路由与守卫） | **不受影响，且 REV-19 是其应用** | 配置页 / 问答页的项目域切换**复用**既有 `projectContext` store（IFC-IB-335）与 `client.ts` 注入点（IFC-IB-334）；**路由树不新增父级** |
| ADR-24（粘贴令牌入口废除） | **不受影响** | 无旁路未动 |
| ADR-25（HTTPS 落点） | **不受影响** | TLS 终止与证书策略未动 |
| ADR-26（迁移 / 种子 / 回滚） | **不受影响，且 REV-19 是其应用** | C-IB-46 定义文档目录迁移 + C-IB-47 历史归属迁移走「**用户手工 + 先备份 + 失败回滚**」纪律（同 ADR-26 精神） |
| ADR-27（登录限速与审计，条件性） | **不受影响** | 条件性未动 |
| ADR-28（项目上下文选择与传播） | **不受影响，且 REV-19 是其应用** | 配置页 / 问答页项目域切换 = **显式选择 + 显式传播**（`X-IB-Project`）；**未选项目仍 fail-closed**（同 ADR-28） |
| ADR-29（提示词主 / 兜底分层） | **不受影响** | 分层与回退方向未动 |
| ADR-30（工具授权与参数） | **不受影响** | 勾选 + 参数可配、不新增工具本体未动 |
| ADR-31（FreeArk 严格对齐） | **不受影响** | REV-19 明确「**三专家属 `demo`**」（REQ-FUNC-IB-53），与 ADR-31 的 **demo 示例项目**对齐**一致**；FreeArk 全程只读 |
| ADR-32（配置生效口径） | **不受影响，且 REV-19 沿用** | 专家集 / 种子 / 迁移一律按「**保存 + 服务重启重装配**」生效；**不引运行期热重载**（OOS-16 维持） |
| ADR-33（保存期单校验入口） | **不受影响** | REV-19 不触定义域 / 工具域 / 提示词域校验 |
| ADR-34（配置审计） | **不受影响** | 只读审计 / 非第二真源未动；REV-19 不把专家集 / 种子 / 迁移写入 `config_audit` |
| ADR-35（内存态提示暴露） | **不受影响** | `GET /api/config/storage-state` 与 `StorageState` 未动 |
| ADR-36（提示词兜底层重定位） | **不受影响** | 代码内置安全网未动；`ExpertRegistryView` **不取代**提示词兜底 |
| ADR-37（项目注册表承载与软删） | **不受影响，且 REV-19 是其应用** | REQ-FUNC-IB-52 的**创建期播种**挂在 `POST /api/projects`；注册表仍为项目可变状态的唯一载体；**REV-19 不新增列 / 不新增表** |
| ADR-38（LLM Key 载体 = DB） | **不受影响** | REV-19 不触 Key 载体与凭据纪律 |
| ADR-39（LLM 未配置态语义） | **不受影响** | 缺 Key 非致命 / 调用期 fail-closed 未动 |
| ADR-40（运维账号 CRUD 扩展） | **不受影响** | REV-19 不触账号链路 |
| ADR-41（项目域 `kb_id` 推导） | **不受影响** | `kb_id ≡ project_id` 与归属断言未动 |
| ADR-42（系统管理三分 IA + 授权解耦） | **不受影响** | 「三专家在非 demo 隐藏」若表现为 IA 可见性，则同 ADR-42 纪律：**UI 可见性非权限机制**、服务端为唯一裁决者 |
| **ADR-43 ~ ADR-47** | **新增** | 每项目专家注册表解析 + C-IB-45 不变量结构保证（ADR-43）/ 定义文档目录化 + C-IB-46 迁移（ADR-44）/ 新项目默认种子 + 三专家属 demo（ADR-45）/ 三专家历史归属迁移 + C-IB-47（ADR-46）/ 专家域 fail-closed 与可观测（ADR-47）；每条含 Context（REQ 引用）/ Options（≥2，含已评估未采纳）/ Decision / Status / Consequences |

**REV-19 复核小结**：既有 **42 条 ADR 全部已复核**（**不受影响 42 条**；其中 **11 条**判「**不受影响且 REV-19 是其应用**」：ADR-04 / 09 / 14 / 15-R1 / 16 / 22 / 23 / 26 / 28 / 32 / 37；**待裁决 0 条**）；**新增 5 条** → ADR 总数 **42 → 47**。**无一条跳过**。REV-19 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、**端口数（19，未新增）**、既有 `IFC-IB-001 ~ 377` 编号 / 名 / 签名（文字性修订见下方清单）；新增 IFC 为 **IFC-IB-378 ~ 388**（见 `module_design.md` §2.2.10）。

**REV-19 被修订 IFC 逐条登记**（**只改文字与取值口径，不改号 / 名 / 签名**）：`IFC-IB-287`（`DefinitionDocumentStore` 端口：`IB_DEFINITION_DOC_PATH` 由「文件路径」语义改为「**目录根**」；端口签名不变）、`IFC-IB-289`（`FileDefinitionDocumentStore.save` 路径语义目录化；签名不变）、`IFC-IB-297`（`IB_DEFINITION_DOC_PATH` **键名语义口径修订**：文件 → 目录）、`IFC-IB-172 ~ IFC-IB-179`（派生访问器**语义澄清**为「**内置默认专家集**（代码内置安全网，非项目真源）」；号 / 名 / 签名不变）、`IFC-IB-201`（`IntentRouter` 路由入口：**增 keyword-only 可选 `experts` 形参**并改为消费注入视图；`classify_experts` 签名不变）。

**REV-19 新增 IFC 清单**：`IFC-IB-378`（迁移 / 播种结果值对象）/ `IFC-IB-379`（`ExpertRegistryView`）/ `IFC-IB-380`（`resolve_expert_registry` fail-closed）/ `IFC-IB-381`（内置默认单例语义澄清 + `builtin_default_registry`）/ `IFC-IB-382`（`IntentRouter` 可选 `experts`）/ `IFC-IB-383`（`FileDefinitionDocumentStore` 目录化）/ `IFC-IB-384`（`migrate_legacy_definition_file`，C-IB-46）/ `IFC-IB-385`（`seed_project`，REQ-FUNC-IB-52）/ `IFC-IB-386`（`migrate_expert_history`，C-IB-47）/ `IFC-IB-387`（前端项目域切换 + 知识问答项目闭环，REQ-FUNC-IB-50 / IB-51）/ `IFC-IB-388`（部署检查清单 B24 / B25）。
```

---

# Part G — 新 IFC 契约全文（IFC-IB-378 ~ IFC-IB-388）

> 落点：`docs/module_design.md` §2.2.10（新增索引小节）与 §3 各模块增补。**全部为类型化契约（`name: type` + 可空性），不含任何实现体**；**不含任何口令 / Key / token / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）。

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| **IFC-IB-378** | MOD-IB-01 | **迁移 / 播种结果值对象**（frozen dataclass，纯 stdlib，**无实现体**）：`MigrationResult(applied: bool, backup_path: str \| None, affected: int, notes: tuple[str, ...])`；`MigrationReport(applied: bool, backup_path: str \| None, affected_sessions: int, affected_references: int, target_project_id: str, notes: tuple[str, ...])`。**不含任何凭据**；`backup_path` 仅登记**路径字符串**（由用户环境决定，**不入日志 / 不回显**）。 | §3 MOD-IB-01（本件） |
| **IFC-IB-379** | MOD-IB-16 | `ExpertRegistryView`（frozen dataclass）：`project_id: str`；`experts: tuple[ExpertSpec, ...]`；`default_expert: ExpertSpec`（**必填、非空、不可为 `None`** —— 「**默认专家恰好一个**」**不可表达为非法态**）；`by_name: Mapping[str, ExpertSpec]`。派生方法（**纯函数**）：`names() -> tuple[str, ...]`（顺序 = 注册表顺序）；`default_name() -> str`；`keywords_map() -> dict[str, tuple[str, ...]]`；`cn_map() -> dict[str, str]`；`data_experts() -> tuple[str, ...]`；`delegating_experts() -> tuple[str, ...]`；`get(name: str) -> ExpertSpec \| None`。**不变量（结构保证）**：`experts` **非空**；`default_expert.name ∈ {e.name for e in experts}`。 | §3 MOD-IB-16（本件） |
| **IFC-IB-380** | MOD-IB-16 | `resolve_expert_registry(project_id: str, *, view: DerivedView) -> ExpertRegistryView`（**纯函数**，装配期由组合根调用）：从 `view`（IFC-IB-291 / 347 的派生产物）构造该项目 `ExpertRegistryView`。**fail-closed（REQ-NFR-IB-21 / ADR-47）**：默认专家缺失 / 非唯一 / 专家集为空 → 抛 `ExpertRegistryError(project_id, reason)`（**不回退**全局默认、**不回退**其他项目）。 | §3 MOD-IB-16（本件） |
| **IFC-IB-381** | MOD-IB-16 | **内置默认单例语义澄清 + 访问器（回归安全网）**：既有零参访问器 `names()` / `keywords_map()` / `cn_map()` / `default_expert()` / `data_experts()` / `delegating_experts()` / `get()` / `fallback_prompts()`（IFC-IB-172 ~ 179）**号 / 名 / 签名一字不动**，语义澄清为「**内置默认专家集**（代码内置安全网；**非项目真源**）」（对齐 REV-17 对 `fallback_prompts` 的同款澄清）；新增 `builtin_default_registry() -> ExpertRegistryView`（**新建项目**的种子真源 = **1 个 KB 问答 agent**，`is_default=True`，内置**不可删**；OQ-IB-33(a) / REQ-FUNC-IB-52）。 | §3 MOD-IB-16（本件） |
| **IFC-IB-382** | MOD-IB-19 | `IntentRouter.__init__(*, llm_provider: Any = None, semantic: Any = None, max_experts: int = MAX_ROUTE_EXPERTS, experts: ExpertRegistryView \| None = None)`（**append-only 新增 keyword-only 可选形参**；`experts=None` → 退化为**内置默认单例**（IFC-IB-381），行为与既有**逐位一致**）。`classify_experts` 的合法集 / `_expert_lines` / `_first_expert` 改为消费 `self._experts`（**不再读进程级 `ib.experts` 全局**）。`IFC-IB-201 / 202 / 203` 的号 / 名 / 签名不变。 | §3 MOD-IB-19（本件） |
| **IFC-IB-383** | MOD-IB-02 | `FileDefinitionDocumentStore`（实现 IFC-IB-287）**目录化**：构造形参语义由「文件路径」改为「**目录根**」；内部 `_path_for(project_id: str) -> str`（`<dir>/<project_id>.json`）；`load(project_id)` / `save(project_id)` 按 `project_id` 解析文件（**消除 F5 偏差**）；**原子写 + 语义哈希乐观并发**纪律不变。`InMemoryDefinitionDocumentStore` 不变（本就按项目）。**端口 `DefinitionDocumentStore`（IFC-IB-287）签名不变**。 | §3 MOD-IB-02（本件） |
| **IFC-IB-384** | MOD-IB-02 | `migrate_legacy_definition_file(dir_root: str, *, target_project_id: str = "demo", backup: bool = True) -> MigrationResult`（**C-IB-46 部署迁移**；**步骤说明，无实现体**）：① `<dir_root>` 不存在 → 创建；② 旧单文件（生产为 `/var/lib/intelligentbase/definition.json`）存在且 `<dir_root>/<target_project_id>.json` **不存在** → **备份后移动**；③ 目标文件**已存在** → **fail-closed**（不覆盖，返回 `applied=False` + 可读 `notes`）；④ `backup=True` 时先备份。**迁移由用户手工执行**（C-IB-38）；失败即回滚。 | §3 MOD-IB-02（本件） |
| **IFC-IB-385** | MOD-IB-23 | **项目创建播种（REQ-FUNC-IB-52 / IB-53）**：`POST /api/projects` 注册表写入成功后，由组合根**同步**调用 `seed_project(project_id: str, *, registry_view: ExpertRegistryView) -> SeedResult`：写 `<dir>/<project_id>.json`（该项目专家集 + **单一默认编排流**，OOS-21）+ 提示词目录骨架 `<root>/<project_id>/<expert>/`；**新建项目种子 = 内置默认单例（1 个 KB 问答 agent）**（IFC-IB-381）；**`demo` 项目种子 = 三对齐专家**（`freeark-expert` / `inspection-expert` / `sanheng-knowledge`）。**幂等**（已存在不覆盖）；**原子回滚**（任一子步失败 → 删除半成品 + 明确错误，**不静默**）。**装配期兜底**：启动时对未落盘项目构造内置默认种子（等价既有逐项目种子）。 | §3 MOD-IB-23（本件） |
| **IFC-IB-386** | MOD-IB-21 / MOD-IB-11 | **三专家历史数据迁移（C-IB-47 / DR-23；架构范围声明，无实现代码）**：`migrate_expert_history(target_project_id: str = "demo", *, experts: tuple[str, ...] = ("freeark-expert", "inspection-expert", "sanheng-knowledge"), backup: bool = True) -> MigrationReport`。**载体**：MOD-IB-21 会话状态（`SessionStore` / `SessionState` / `SessionTurn`）+ MOD-IB-11 台账 `sessions` 表（`SessionRecord.project_id`）+ 引用 / 引文记录（citations）。**所有权字段** = `project_id`。**改写规则**：`project_id != target_project_id` 且记录引用了 `experts` 之一 → 置 `project_id = target_project_id`。**记录保留**（**不删除任何行**；与 DR-21「误删优先软删」**不冲突**）。**幂等**（已属目标项目的记录跳过）。**显式登记**：**非 demo 项目因此失去这些历史**（AC-IB-45-04 明文）。**手工 + 先备份 + 失败回滚**。 | §3 MOD-IB-21（会话状态）/ §3 MOD-IB-11（`sessions` 表） |
| **IFC-IB-387** | MOD-IB-24 | **前端项目域切换 / 加载 + 知识问答项目闭环（REQ-FUNC-IB-50 / IB-51）**：配置页与知识问答页**复用**既有 `projectContext` store（IFC-IB-335）与 `client.ts` 单一注入点（IFC-IB-334）的项目域切换；切换后配置页 `GET /api/config/definition`（IFC-IB-295 系列）**按当前项目域加载**、编辑**只写当前项目**；知识问答页提问**绑定当前项目域**（`X-IB-Project`），答案引用 / 检索范围限于该项目（**非 demo 项目不出现三专家的知识 / 历史**）。**授权与失败语义为服务端裁决**：未选项目 → 前端**不发送** `X-IB-Project` → 服务端 **fail-closed**（同 ADR-28）；知识问答的项目闭环**不是**前端过滤，而是服务端 `Scope(project_id=…)` + `orchestrator_for` **fail-closed** 的既有事实（IFC-IB-201 的 `scope` 必填）。 | §3 MOD-IB-24（本件） |
| **IFC-IB-388** | MOD-IB-25 | **交付物（部署检查清单新增 B24 / B25）**：**B24** 定义文档目录化迁移 —— `IB_DEFINITION_DOC_PATH` 语义 = **目录**；生产单文件 `/var/lib/intelligentbase/definition.json` → `<dir>/demo.json`，**用户手工执行 + 先备份 + 失败回滚**（C-IB-46）；旧值「指向文件」**不再合法**（可读错误 + 迁移目标提示）。**B25** 三专家历史迁移 —— `migrate_expert_history` **幂等 / 备份 / 回滚**；**非 demo 项目失去该历史已登记**（C-IB-47）。 | §3 MOD-IB-25（本件） |

**REV-19 编号规范（强制，延续 R2 / R7 / R8 / R13 / R14 / REV-16-2 / REV-16-4 / REV-17 / REV-18）**：新增号只许**追加**（本轮取 **378 ~ 388**）；`IFC-IB-001 ~ 377` 的**号 / 名 / 签名一字不动**（**仅上 §2.2.10 文字修订索引登记的 5 组文字与取值口径修订**）；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。**端口数不变（19，未新增）**；**模块数不变（26）**；**零新增依赖边**。以上 11 条 IFC 全部为**类型化契约**，**不含任何实现体**；**不含任何口令 / 令牌 / Key / 证书字面量，也不含任何配置取值**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）。

---

（Part 2 结束。编辑条目与 6 问答复见 `docs/rev19_groupb_apply_package.md`（Part 1）；`module_design.md` 编辑条目见 `docs/rev19_groupb_apply_package_part3.md`（Part 3）。）
