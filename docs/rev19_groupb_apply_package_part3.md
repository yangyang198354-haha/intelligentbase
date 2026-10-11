# REV-19 GROUP_B 架构增量 — Apply-Ready 修订包 · Part 3（`docs/module_design.md` 编辑条目）

<file_header>
  <project>intelligentbase</project>
  <artifact>rev19_groupb_apply_package_part3</artifact>
  <path>docs/rev19_groupb_apply_package_part3.md</path>
  <doc_id>ARCH-PKG-INTELBASE-REV19-B-P3</doc_id>
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
    <readonly_reference path="docs/module_design.md" version="1.10.2" revision="REV-18-R2" note="目标文件；本包为其 REV-19 增量，编号只增不改"/>
  </inputs>
  <scope_boundary>只做架构与模块设计；不含实现代码、测试用例、部署脚本。</scope_boundary>
</file_header>

> **使用方式**：每条 = （文件，章节 / 锚点，现有原文 → 拟替换 / 插入文本）。**替换类**条目给出**逐字原文**；**插入类**条目给出**前置锚点**（在该锚点**之后**插入）。
> **不变式（复核后逐条核对）**：模块数 **26**（MOD-IB-01 ~ 26 未改）；端口数 **19**（未新增）；§4.1 依赖边**逐行不变（零新增边）**；DAG 无环；**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）；**无实现代码**；**不含任何口令 / Key / token / 证书字面量**。

---

## 条目 M-1（文件头版本）— `docs/module_design.md`

- **章节 / 锚点**: `<file_header>` 第 6 / 7 / 11 行
- **现有原文**:
  ```
    <version>1.10.2</version>
    <revision>REV-18-R2</revision>
  ```
  （第 11 行）`  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>`
- **拟替换文本**:
  ```
    <version>1.11.0</version>
    <revision>REV-19</revision>
  ```
  （第 11 行）`  <invocation_id>INV-GROUP_B-INTELBASE-014</invocation_id>`
- **性质**: 替换（3 处）

---

## 条目 M-2（`<inputs>` 指针同步）— `docs/module_design.md`

- **章节 / 锚点**: `<inputs>` 第 55 ~ 57 行
- **现有原文**:
  ```
      <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
      <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
      <input path="docs/architecture_design.md" version="1.10.2" revision="REV-18-R2" status="DRAFT_FOR_GATE_REVIEW"/>
  ```
- **拟替换文本**:
  ```
      <input path="docs/requirements_spec.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
      <input path="docs/user_stories.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
      <input path="docs/architecture_design.md" version="1.11.0" revision="REV-19" status="DRAFT_FOR_GATE_REVIEW"/>
  ```
- **性质**: 替换

---

## 条目 M-3（revision_history 新增行）— `docs/module_design.md`

- **章节 / 锚点**: `</revision_history>`（第 53 行）**之前**；即第 52 行 `REV-18-R2` `</rev>` 之后
- **前置锚点**: `    <rev no="REV-18-R2" …（第 50 ~ 52 行）… </rev>`
- **拟插入文本**:
  ```xml
      <rev no="REV-19" date="2026-10-11" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-014" basis="GROUP_A REV-19 下游贯通（每项目专家集隔离 + 可视化配置项目域切换/加载 + 知识问答项目闭环 + 新项目默认种子 + 三专家属 demo：REQ-FUNC-IB-49~53 / REQ-NFR-IB-21 / C-IB-44~C-IB-47 / OOS-20 / OOS-21 / DR-22 / DR-23；用户裁决 2026-10-11：OQ-IB-32~40 一次拍板）；上游 architecture_design.md 1.11.0（REV-19），对应 ADR-43~47 / §2.0.10">
        **不新增模块、不新增端口、不新增依赖边**（模块数仍 **26**，**端口数仍 19（未新增）**，**§4.1 依赖边清单逐行未改（零新增边）**，DAG 无环，§4.2.9 再声明）：**每项目专家注册表解析** —— `ExpertRegistryView`（IFC-IB-379，frozen 值对象）/ `resolve_expert_registry`（IFC-IB-380，fail-closed）/ 内置默认单例语义澄清与 `builtin_default_registry`（IFC-IB-381）并入 **MOD-IB-16**；`IntentRouter` 增 keyword-only 可选 `experts`（IFC-IB-382，**append-only**）并入 **MOD-IB-19**。**定义文档目录化** —— `FileDefinitionDocumentStore` 目录化与 `_path_for(project_id)`（IFC-IB-383）/ `migrate_legacy_definition_file`（IFC-IB-384，**C-IB-46**）并入 **MOD-IB-02**。**新项目默认种子** —— `seed_project`（IFC-IB-385，**REQ-FUNC-IB-52 / IB-53**）并入 **MOD-IB-23**。**三专家历史迁移** —— `migrate_expert_history`（IFC-IB-386，**C-IB-47 / DR-23**）并入 **MOD-IB-21**（会话状态）/ **MOD-IB-11**（`sessions` 表）。**前端项目域切换 / 知识问答项目闭环** —— IFC-IB-387（**REQ-FUNC-IB-50 / IB-51**）并入 **MOD-IB-24**。**迁移结果值对象** —— `MigrationResult` / `MigrationReport`（IFC-IB-378）并入 **MOD-IB-01**。**交付物** —— 部署检查清单 **B24 / B25**（IFC-IB-388）并入 **MOD-IB-25**。新增 IFC 编号 **378 ~ 388**（11 条，全部类型化、frozen dataclass / Protocol / 纯 stdlib、零第三方依赖；**IFC-IB-285 仍预留未分配**；既有重号 IFC-IB-131 **登记不修**）。**既有 `IFC-IB-001 ~ 377` 的号 / 名 / 签名一字不动** —— **仅 5 组文字与取值口径修订**（`IFC-IB-287` / 289 / 297；`IFC-IB-172 ~ 179`；`IFC-IB-201`，逐条登记于 **§2.2.10**）。**计数同步**：REQ-FUNC **48/48 → 53/53**（新增 IB-49~53，§9.1）、NFR **20 → 21**（新增 NFR-21，§9.2）。**红线未破（强制）**：专家集**硬隔离 = 项目级**（`ExpertRegistryView` 按项目解析，**无跨项目回退**）；`kb_id` 仍由已认证主体的 `project_id` 推导、**保留** `assert_kb_in_project`（IFC-IB-130）归属断言（失败仍 403）；「**UI 分组 / 可见性非权限机制**」（ADR-42 纪律），非 demo 的专家集差异由**种子差异**在**装配期**结构性保证。**生效口径未变**：**保存 + 服务重启重装配**（ADR-32 / C-IB-40 / OOS-16），**不引运行期热重载**、**不重编译编排图**。**凭据纪律**：全文**只登记键名 / 表名 / 文件名 / 字段名 / 头名**；`migrate_expert_history` / `migrate_legacy_definition_file` **不含任何凭据**（`backup_path` 仅登记路径字符串，**不入日志**）；**迁移由用户手工执行 + 先备份 + 失败回滚**（C-IB-38 / C-IB-46 / C-IB-47）。增补位置：§1 REV-19 补充纪律段、§2.2 R19 增记、§2.2.10 REV-19 IFC 段号索引与文字修订索引、§3 的 MOD-IB-01 / 02 / 16 / 19 / 21 / 23 / 24 / 25 增补、§4.2.9 无环性再声明、§5 R19 说明、§7.4 R19 说明、§8 替身 / 离线可测单元、§9.1 六行 + §9.2 一行 + §9.12 覆盖率再声明、§11 自检。需求侧文档只读；未修改 FreeArk 任何文件；未写入任何口令 / Key / token / 证书字面量。
      </rev>
  ```
- **性质**: 插入（在 `</revision_history>` 之前）

---

## 条目 M-4（§1 REV-19 补充纪律段）— `docs/module_design.md`

- **章节 / 锚点**: §1 末尾（**§2 标题 `## 2. …` 之前**；即 MOD-IB-01 ~ 26 总览表与既有增补段之后）
- **拟插入文本**:
  ```markdown
  **REV-19 性质段（每项目专家集隔离 + 定义文档目录化 + 新项目种子 + 三专家属 demo + 专家域 fail-closed）**：本增量**不新增模块、不新增端口、不新增依赖边**（模块数仍 **26**、端口数仍 **19**、**§4.1 依赖边清单逐行未改**）。新增类型化契约与落点**并入既有模块**：**MOD-IB-01**（迁移 / 播种结果值对象，IFC-IB-378）、**MOD-IB-02**（定义文档存储目录化与 C-IB-46 迁移，IFC-IB-383 / 384）、**MOD-IB-16**（`ExpertRegistryView` 与按项目解析 / 内置默认单例，IFC-IB-379 ~ 381）、**MOD-IB-19**（`IntentRouter` 可选 `experts`，IFC-IB-382）、**MOD-IB-21 / MOD-IB-11**（三专家历史迁移，IFC-IB-386）、**MOD-IB-23**（项目创建播种 `seed_project`，IFC-IB-385）、**MOD-IB-24**（前端项目域切换 + 知识问答项目闭环，IFC-IB-387）、**MOD-IB-25**（检查清单 B24 / B25，IFC-IB-388）。

  **REV-19 补充纪律段（强制）**：① **专家集硬隔离 = 项目级** —— `ExpertRegistryView` 按 `project_id` 在**装配期**解析，**无跨项目回退**、**无全局单例真源**（进程级 `EXPERT_SPECS` 降级为**内置默认单例 / 代码兜底安全网**）；② **C-IB-45 两条不变量由结构保证** —— 「**默认专家恰好一个**」由 `ExpertRegistryView.default_expert`（**必填非空字段**）保证、「**永不无应答**」由内置**不可删**默认专家种子保证，**不依赖校验放行**；③ **`IB_DEFINITION_DOC_PATH` 语义 = 目录**（其下 `<dir>/<project_id>.json`，**一项目一文件**，把 `[ARCH-ASSUMPTION-A6]` 从纸面**落到实现**）；旧「单文件」值**不再合法**，须按 **C-IB-46** 一次性迁移（**用户手工 + 先备份 + 失败回滚**）；④ **新项目默认种子在创建期落盘**（`POST /api/projects` → `seed_project`；**1 个 KB 问答 agent + 1 个默认编排流**）；⑤ **「三专家属 demo」由种子差异保证**（非 demo 项目种子**不含**三专家），**不是** UI 约定；⑥ **不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）。
  ```
- **性质**: 插入

---

## 条目 M-5（§2.2 R19 增记）— `docs/module_design.md`

- **章节 / 锚点**: §2.2 端口清单表后、既有「R7 增记」等说明段**之后**（§2.2 **末尾**，**§2.2.1 标题之前**）
- **前置锚点**: §2.2 末段（含 `CollectionResolver` 归层说明与 `R7 增记（第 14 个端口）` 等）
- **拟插入文本**:
  ```markdown
  **R19 增记（端口数不变）**：REV-19 **未新增任何端口** —— 端口数仍为 **19**（第 1 ~ 19 个端口清单逐行未改）。REV-19 的四类新增均为**既有模块内的类型化契约**：① **专家域派生视图** `ExpertRegistryView`（IFC-IB-379）与 `resolve_expert_registry`（IFC-IB-380）落在 **MOD-IB-16**（**不是端口**，是**装配期派生的只读值对象**，与既有派生访问器 IFC-IB-172 ~ 179 同处；其**真源**为每项目定义文档 + 提示词目录，见 **ADR-43**）；② **定义文档存储**的目录化改动落在 `DefinitionDocumentStore` 端口的**文件适配器**（IFC-IB-383，**端口签名不变**）；③ **项目创建播种** `seed_project`（IFC-IB-385）落在 **MOD-IB-23**（复用既有边 `23 → 01 / 02`）；④ **历史迁移** `migrate_expert_history`（IFC-IB-386）落在 **MOD-IB-21 / MOD-IB-11**（复用既有边）。**「按项目取专家集」的唯一入口**与 `CollectionResolver` 的单一入口纪律同构：上层（MOD-IB-17 / 19 / 22）**不得**各自解析专家集，一律由组合根在**装配期**经 `resolve_expert_registry` 取得视图后**构造注入**（ADR-43 / ADR-15）。
  ```
- **性质**: 插入

---

## 条目 M-6（§2.2.10 新增索引小节）— `docs/module_design.md`

- **章节 / 锚点**: §2.2.9 末段（第 409 行「REV-18 编号规范…」段）**之后**，`## 3. 模块详情`（第 411 行）**之前**
- **拟插入文本**: **直接采用 Part 2 §Part G 的两张表 + 「REV-19 编号规范」段**，小节标题为：
  ```markdown
  ### 2.2.10 REV-19 新增 IFC 索引（IFC-IB-378 ~ 388）与文字修订索引
  ```
  其后依次粘贴：①「IFC 段 / 归属模块 / 内容 / 权威落点」主表（IFC-IB-378 ~ 388，共 11 行）；②「**REV-19 文字修订索引（5 组；只改文字与取值口径，号 / 名 / 签名一字不动）**」子表：
  | IFC | 修订内容 |
  |-----|----------|
  | `IFC-IB-287` | 端口 `DefinitionDocumentStore` 的 `IB_DEFINITION_DOC_PATH` **语义口径**由「文件路径」改为「**目录根**」；**端口签名 / 方法数不变** |
  | `IFC-IB-289` | `save` 的**路径语义**目录化（`<dir>/<project_id>.json`）；**签名不变**（`project_id` 形参本已存在） |
  | `IFC-IB-297` | `IB_DEFINITION_DOC_PATH` **键名语义**由「定义文档路径（文件）」修订为「定义文档**目录**」；**键名本身不变** |
  | `IFC-IB-172 ~ 179` | 派生访问器**语义澄清**为「**内置默认专家集**（代码内置安全网；**非项目真源**）」；**号 / 名 / 签名一字不动**（对齐 REV-17 对 `fallback_prompts` 的同款澄清） |
  | `IFC-IB-201` | `IntentRouter` 路由入口**增 keyword-only 可选 `experts` 形参**并改为消费注入视图；`classify_experts` **签名不变** |

  ③ 末段（**REV-19 编号规范**，逐字采用 Part 2 Part G 末段）。
- **性质**: 插入

---

## 条目 M-7（§3 MOD-IB-01 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-01 核心契约 (L0)` 的**公开接口契约**清单**末尾**（既有 `IFC-IB-366` / `367` / `368` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-378（REV-19 新增）**: `MigrationResult(applied: bool, backup_path: str | None, affected: int, notes: tuple[str, ...])` 与 `MigrationReport(applied: bool, backup_path: str | None, affected_sessions: int, affected_references: int, target_project_id: str, notes: tuple[str, ...])`。**frozen dataclass，纯 stdlib，零第三方依赖，无实现体**。**不含任何凭据**；`backup_path` 仅登记**路径字符串**（**不入日志 / 不回显**）。
  ```
- **性质**: 插入
- **附注**: 同步在 MOD-IB-01 的「覆盖需求」行**末尾追加**（不删既有文字）：`；**REQ-FUNC-IB-49 / IB-52 / IB-53（REV-19，辅：专家注册表视图 / 播种结果 / 迁移结果的值对象落点，见 IFC-IB-378）**`

---

## 条目 M-8（§3 MOD-IB-02 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-02 配置 (L0)` 的**公开接口契约**清单**末尾**（既有 `IFC-IB-297` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-383（REV-19 新增）**: `FileDefinitionDocumentStore`（实现 IFC-IB-287）**目录化**：构造形参语义由「**文件路径**」改为「**目录根**」；内部 `_path_for(project_id: str) -> str`（`<dir>/<project_id>.json`）；`load(project_id: str) -> DefinitionDocument | ConfigError` / `save(project_id: str, doc: DefinitionDocument, *, expected_content_hash: str | None) -> SaveResult` 按 `project_id` 解析文件（**消除 F5 偏差**：旧实现 `load()` 忽略 `project_id`、只读单文件）。**原子写 + 语义哈希乐观并发**纪律不变。`InMemoryDefinitionDocumentStore` 不变（本就按项目）。**端口 `DefinitionDocumentStore`（IFC-IB-287）签名不变**。
    - **IFC-IB-384（REV-19 新增）**: `migrate_legacy_definition_file(dir_root: str, *, target_project_id: str = "demo", backup: bool = True) -> MigrationResult`（**C-IB-46**；**步骤说明，无实现体**）：① `<dir_root>` 不存在 → 创建；② 旧单文件存在且 `<dir_root>/<target_project_id>.json` **不存在** → **备份后移动**；③ 目标**已存在** → **fail-closed**（不覆盖，`applied=False` + 可读 `notes`）；④ `backup=True` 时先备份。**用户手工执行**（C-IB-38）；失败即回滚。
  ```
- **性质**: 插入
- **附注**: 同步在 MOD-IB-02 的「覆盖需求」行**末尾追加**（不删既有文字）：`；**REQ-FUNC-IB-49 / IB-50（REV-19，辅：按项目装载定义文档 + C-IB-46 目录迁移，见 IFC-IB-383 / 384）**`

---

## 条目 M-9（§3 MOD-IB-16 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-16 专家注册表与提示词装配`（或同名小节）的**公开接口契约**清单**末尾**（既有 `IFC-IB-365` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-379（REV-19 新增）**: `ExpertRegistryView`（frozen dataclass）：`project_id: str`；`experts: tuple[ExpertSpec, ...]`；`default_expert: ExpertSpec`（**必填、非空、不可为 `None`**）；`by_name: Mapping[str, ExpertSpec]`。派生方法（**纯函数**）：`names` / `default_name` / `keywords_map` / `cn_map` / `data_experts` / `delegating_experts` / `get`。**不变量（结构保证）**：`experts` **非空**；`default_expert.name ∈ {e.name for e in experts}` —— 「**默认专家恰好一个**」**不可表达为非法态**。**frozen dataclass，纯 stdlib，零第三方依赖，无实现体**。
    - **IFC-IB-380（REV-19 新增）**: `resolve_expert_registry(project_id: str, *, view: DerivedView) -> ExpertRegistryView`（**纯函数**，装配期由组合根调用）：从 `view`（IFC-IB-291 / 347）构造该项目视图。**fail-closed（REQ-NFR-IB-21 / ADR-47）**：默认专家缺失 / 非唯一 / 专家集为空 → 抛 `ExpertRegistryError(project_id, reason)`（**无跨项目 / 全局回退**）。
    - **IFC-IB-381（REV-19 新增）**: 既有零参访问器 `names` / `keywords_map` / `cn_map` / `default_expert` / `data_experts` / `delegating_experts` / `get` / `fallback_prompts`（IFC-IB-172 ~ 179）**号 / 名 / 签名一字不动**，**语义澄清**为「**内置默认专家集**（代码内置安全网；**非项目真源**）」；新增 `builtin_default_registry() -> ExpertRegistryView`（**新建项目种子真源** = **1 个 KB 问答 agent**，`is_default=True`，内置**不可删**；OQ-IB-33(a) / REQ-FUNC-IB-52）。
  ```
- **性质**: 插入
- **附注**: 同步在 MOD-IB-16 的「覆盖需求」行**末尾追加**（不删既有文字）：`；**REQ-FUNC-IB-49 / IB-53（REV-19，主：每项目专家注册表隔离 + 三专家属 demo，见 IFC-IB-379 ~ 381）**；**REQ-NFR-IB-21（REV-19，主：专家域 fail-closed）**`

---

## 条目 M-10（§3 MOD-IB-19 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-19 …（意图路由）` 的**公开接口契约**清单**末尾**（既有 `IFC-IB-201 ~ 203` 相关行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-382（REV-19 新增）**: `IntentRouter.__init__(*, llm_provider: Any = None, semantic: Any = None, max_experts: int = MAX_ROUTE_EXPERTS, experts: ExpertRegistryView | None = None)` —— **append-only 新增 keyword-only 可选形参** `experts`；`experts=None` → 退化为**内置默认单例**（IFC-IB-381），**行为与既有逐位一致**。`classify_experts` 的合法集 / `_expert_lines` / `_first_expert` 改为消费 `self._experts`（**不再读进程级 `ib.experts` 全局**）。**`IFC-IB-201 / 202 / 203` 的号 / 名 / 签名不变**。
  ```
- **性质**: 插入
- **附注**: 同步在 MOD-IB-19 的「覆盖需求」行**末尾追加**（不删既有文字）：`；**REQ-FUNC-IB-49 / IB-51（REV-19，辅：路由消费本项目专家集，见 IFC-IB-382）**`

---

## 条目 M-11（§3 MOD-IB-21 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-21 …（会话 / 流式）` 的**公开接口契约**清单**末尾**
- **拟插入文本**:
  ```markdown
    - **IFC-IB-386（REV-19 新增；载体 MOD-IB-21 会话状态 + MOD-IB-11 `sessions` 表）**: `migrate_expert_history(target_project_id: str = "demo", *, experts: tuple[str, ...] = ("freeark-expert", "inspection-expert", "sanheng-knowledge"), backup: bool = True) -> MigrationReport`（**C-IB-47 / DR-23；架构范围声明，无实现代码**）。**所有权字段** = `project_id`；**改写规则**：`project_id != target_project_id` 且记录引用了 `experts` 之一 → 置 `project_id = target_project_id`；**记录保留**（**不删除任何行**，与 DR-21「误删优先软删」**不冲突**）；**幂等**（已属目标项目的记录跳过）；**显式登记**：**非 demo 项目因此失去这些历史**（AC-IB-45-04）；**用户手工执行 + 先备份 + 失败回滚**（C-IB-38 / C-IB-47）。
  ```
- **性质**: 插入（MOD-IB-21）
- **附注**: 同一条 IFC-IB-386 的**载体说明**同步写入 **MOD-IB-11**「覆盖需求 / 契约」区（`sessions` 表 `SessionRecord.project_id` 为所有权字段）；两处**指向同一条 IFC**，**不新增表 / 不新增列**。

---

## 条目 M-12（§3 MOD-IB-23 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-23 组合根 / HTTP 层` 的**公开接口契约**清单**末尾**（既有 `IFC-IB-375` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-385（REV-19 新增；REQ-FUNC-IB-52 / IB-53）**: 项目创建播种 —— `POST /api/projects`（IFC-IB-372）注册表写入成功后，由组合根**同步**调用 `seed_project(project_id: str, *, registry_view: ExpertRegistryView) -> SeedResult`：写 `<dir>/<project_id>.json`（该项目专家集 + **单一默认编排流**，OOS-21）+ 提示词目录骨架 `<root>/<project_id>/<expert>/`；**新建项目种子 = 内置默认单例（1 个 KB 问答 agent）**（IFC-IB-381）；**`demo` 项目种子 = 三对齐专家**（`freeark-expert` / `inspection-expert` / `sanheng-knowledge`）。**幂等**（已存在不覆盖）；**原子回滚**（任一子步失败 → 删除半成品 + 明确错误，**不静默**）。**装配期兜底**：启动时对未落盘项目构造内置默认种子（等价既有逐项目种子）。**不新增端点 / 不新增依赖边**。
  ```
- **性质**: 插入
- **附注**: ① 同步在 MOD-IB-23 的「覆盖需求」行**末尾追加**：`；**REQ-FUNC-IB-51 / IB-52（REV-19，主：知识问答项目闭环 + 新项目默认种子，见 IFC-IB-385）**`；② 在 §3 MOD-IB-23 的**装配序列**说明**末尾追加**一句（不删既有文字）：`**（REV-19）** 装配序列新增一步：对每个已登记项目构造该项目 `ExpertRegistryView`（IFC-IB-380，fail-closed）；`orchestrator_for` 消费**本项目视图**（**不再消费进程级全局**）；**未登记项目仍 fail-closed**（既有语义一字不动）。`

---

## 条目 M-13（§3 MOD-IB-24 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-24 …（前端）` 的**公开接口契约**约束**末尾**（既有 `IFC-IB-376` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-387（REV-19 新增；REQ-FUNC-IB-50 / IB-51）**: **前端项目域切换 / 加载 + 知识问答项目闭环**：配置页与知识问答页**复用**既有 `projectContext` store（IFC-IB-335）与 `client.ts` 单一注入点（IFC-IB-334）的项目域切换；切换后配置页 `GET /api/config/definition`（IFC-IB-295 系列）**按当前项目域加载**、编辑**只写当前项目**；知识问答页提问**绑定当前项目域**（`X-IB-Project`），答案引用 / 检索范围限于该项目（**非 demo 项目不出现三专家的知识 / 历史**）。**授权与失败语义为服务端裁决**：未选项目 → 前端**不发送** `X-IB-Project` → 服务端 **fail-closed**（同 ADR-28）；项目闭环**不是**前端过滤，而是服务端 `Scope(project_id=…)` + `orchestrator_for` **fail-closed** 的既有事实。**不引入**任何“即时跨项目生效”暗示（生效口径 = 保存 + 服务重启重装配）。
  ```
- **性质**: 插入
- **附注**: 同步在 MOD-IB-24 的「覆盖需求」行**末尾追加**：`；**REQ-FUNC-IB-50 / IB-51（REV-19，主：配置页项目域切换 / 加载 + 知识问答项目闭环，见 IFC-IB-387）**`

---

## 条目 M-14（§3 MOD-IB-25 增补）— `docs/module_design.md`

- **章节 / 锚点**: §3 `### MOD-IB-25 …（部署 / 交付物）` 的交付物清单**末尾**（既有 `IFC-IB-377` 行**之后**）
- **拟插入文本**:
  ```markdown
    - **IFC-IB-388（REV-19 新增）**: 交付物 —— 部署检查清单新增 **B24 / B25**：**B24** 定义文档目录化迁移（`IB_DEFINITION_DOC_PATH` 语义 = **目录**；生产单文件 `/var/lib/intelligentbase/definition.json` → `<dir>/demo.json`；**用户手工执行 + 先备份 + 失败回滚**，C-IB-46；旧值「指向文件」**不再合法**，可读错误 + 迁移目标提示）；**B25** 三专家历史迁移（`migrate_expert_history` **幂等 / 备份 / 回滚**；**非 demo 项目失去该历史已登记**，C-IB-47）。
  ```
- **性质**: 插入

---

## 条目 M-15（§4.2.9 REV-19 无环性再声明）— `docs/module_design.md`

- **章节 / 锚点**: §4.2.8 末段**之后**，`## 5. 组合根装配表（MOD-IB-23）`（第 1168 行）**之前**
- **拟插入文本**:
  ```markdown
  ### 4.2.9 REV-19 无环性再声明（零新增依赖边）

  **结论：DAG 拓扑在 REV-19 下不变，无环证明（§4.2）继续成立。**

  - **零新增依赖边**：REV-19 的全部新增落在 **MOD-IB-01 / 02 / 11 / 16 / 19 / 21 / 23 / 24 / 25** 内部（迁移 / 播种结果值对象 / 定义文档存储目录化与迁移 / `sessions` 表归属字段说明 / `ExpertRegistryView` 与按项目解析 / `IntentRouter` 可选形参 / 会话状态迁移 / 创建播种 / 前端项目域切换 / 检查清单），**§4.1 依赖边清单逐行未改**；因此 `w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
  - **不新增模块**：与 R7 / R8 / R13 同理 —— 专家注册表视图**必然被 MOD-IB-16（低编号）持有并被 MOD-IB-23（组合根）装配**，项目创建播种**必然被组合根（MOD-IB-23）调用**，历史迁移落在**既有 MOD-IB-21 / MOD-IB-11**；若新开模块只能取 **≥27** 的编号，会产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**；故并入既有模块（§4.2.2 边界纪律继续适用）。
  - **既有边被复用而非新增**：`resolve_expert_registry`（IFC-IB-380）定义在 **MOD-IB-16**（依赖 MOD-IB-01 为既有边）、由组合根在装配期调用（既有边 `23 → 16`）；`seed_project`（IFC-IB-385）在 **MOD-IB-23**（复用既有边 `23 → 01 / 02`）；`migrate_expert_history`（IFC-IB-386）在 **MOD-IB-21 / MOD-IB-11**（复用既有边）；`FileDefinitionDocumentStore` 目录化在 **MOD-IB-02**（既有边 `02 → 01`）。**均零新增边**。
  - **单一入口纪律未被绕开**：专家集仍**只**经装配期 `resolve_expert_registry` 派生并**构造注入**（上层 MOD-IB-17 / 19 / 22 **不得**各自解析）；定义文档仍**只**经 `DefinitionDocumentStore` 端口读写；前端仍**只**经 HTTP/SSE 契约取数（**不新增任何绕过路径**）。
  - 因此「编号即拓扑序」继续适用于 GROUP_C；REV-19 的**边界纪律同 §4.2.2 末句**：新增工件若被低编号模块（尤其组合根）依赖，**不得新开编号更高的模块**。
  ```
- **性质**: 插入

---

## 条目 M-16（§5 装配表 R19 说明）— `docs/module_design.md`

- **章节 / 锚点**: §5 装配表后既有说明段**末尾**（`## 6. …` 之前）
- **拟插入文本**:
  ```markdown
  > **R19 装配说明（定义文档与专家注册表）**：① **`IB_DEFINITION_DOC_PATH` 语义 = 目录**（其下 `<dir>/<project_id>.json`）—— §5 中 `DefinitionDocumentStore` 行的**适配器与开关名不变**，仅**值语义**由「文件」改为「**目录**」（REV-19 登记型口径修订；IFC-IB-287 / 289 / 297）；旧「单文件」值**不再合法**，须按 **C-IB-46** 一次性迁移（**用户手工 + 先备份 + 失败回滚**）。② **专家集按项目装配**：组合根在装配期对每个已登记项目构造 `ExpertRegistryView`（IFC-IB-380，fail-closed）；`orchestrator_for` 消费**本项目视图**。③ **项目创建播种**：`POST /api/projects` 成功后调用 `seed_project`（IFC-IB-385）写 `<dir>/<project_id>.json` 与提示词目录骨架。④ **不新增任何装配键名 / 开关**（无新环境变量）；持久化载体（本地文件 / 目录）与键名一律**只登记键名、不含值**（凭据纪律）。
  ```
- **性质**: 插入

---

## 条目 M-17（§7.4 降级矩阵 R19 说明）— `docs/module_design.md`

- **章节 / 锚点**: §7.4 降级矩阵表**末尾**（`---` 与 `## 8. 测试替身清单` 之前）
- **拟插入文本**:
  ```markdown
  **（REV-19）专家域解析降级（新增）**：**未登记项目 / 无定义文档 / 默认专家缺失或非唯一 / 专家集为空** → **fail-closed**：**装配期** `StartupError`（复用 ADR-16 闸门，IFC-IB-380）、**运行期** `orchestrator_for` `StartupError`（既有语义一字不动）；**无隐式回退**（不回退全局默认、不回退其他项目）；并发**结构化日志** `log_event("expert_domain", <code>, project_id=…, reason=…)`（**不含任何凭据 / 提示词正文**）。**用户可见**：部署者见启动失败日志；**日志级别**：ERROR；**fail 语义**：**fail-closed**（ADR-47 / REQ-NFR-IB-21）。
  ```
- **性质**: 插入

---

## 条目 M-18（§8 测试替身 / 离线可测单元 R19 说明）— `docs/module_design.md`

- **章节 / 锚点**: §8 内既有「REV-18 追加的离线可测单元」段**之后**
- **拟插入文本**:
  ```markdown
  **REV-19 追加的离线可测单元**（**纯函数 / 内存替身，无外部 IO、无第三方依赖**）：① **MOD-IB-16** 的 `resolve_expert_registry`（IFC-IB-380）—— 对「默认专家缺失 / 非唯一 / 专家集为空」三例断言 `ExpertRegistryError`（fail-closed 可测），对合法派生产物断言 `ExpertRegistryView` 不变量（`experts` 非空 ∧ `default_expert.name ∈ experts`）；② **MOD-IB-16** 的 `builtin_default_registry`（IFC-IB-381）—— 断言新建项目种子**恰 1 个** `is_default` 专家（「默认专家恰好一个」= 类型层可测事实）；③ **MOD-IB-02** 的 `FileDefinitionDocumentStore._path_for` 与 `migrate_legacy_definition_file`（IFC-IB-383 / 384）—— 在临时目录下完成「旧单文件 → `<dir>/demo.json`」全链路（含目标已存在时 fail-closed）离线验证；④ **MOD-IB-21 / MOD-IB-11** 的 `migrate_expert_history`（IFC-IB-386）—— 在 `MemorySessionStore` + 内存台账上断言「归属改写 + 记录保留 + 幂等 + 非 demo 失去可见」四性质。配合上述替身即可在**无任何外部服务**下完成 REV-19 全链路离线验证（REQ-FUNC-IB-49 ~ 53 / REQ-NFR-IB-21）。
  ```
- **性质**: 插入
- **附注**: 可在 §8 替身表中**追加**一行（**不改既有一行**）：`| `DefinitionDocumentStore`（**REV-19 口径**） | `FileDefinitionDocumentStore`（**目录根** `<dir>/<project_id>.json`） | `InMemoryDefinitionDocumentStore`（本就按项目） | 目录化装载 / 按项目隔离 / C-IB-46 迁移幂等 + 目标已存在的 fail-closed |`。**注**：既有 `DefinitionDocumentStore`（R7 新增）行**一字不动**（其替身与行为列仍成立）；新增行只为补登 REV-19 的目录语义。

---

## 条目 M-19（§9.1 覆盖率新增行）— `docs/module_design.md`

- **章节 / 锚点**: §9.1 表格**末尾**（`| IB-48 |` 行**之后**）
- **拟插入文本**:
  ```markdown
  | IB-49 | **每项目专家集隔离**（配置页可切换 / 加载自己项目的专家 agent） | **MOD-IB-16** / 02, 19, 23, 24（ADR-43；IFC-IB-379 ~ 382） |
  | IB-50 | **可视化配置项目域切换 / 加载**（配置页按项目域加载与写回） | **MOD-IB-24** / 23, 02, 16（ADR-44；IFC-IB-383 / 387） |
  | IB-51 | **知识问答项目闭环**（提问 / 引用 / 检索范围限于当前项目域） | **MOD-IB-23** / 19, 16, 21, 24（ADR-43 / ADR-47） |
  | IB-52 | **新项目默认种子**（1 个 KB 问答 agent + 1 个默认编排流） | **MOD-IB-23** / 02, 16, 01（ADR-45；IFC-IB-385） |
  | IB-53 | **三专家属 `demo`**（非 demo 隐藏；由种子差异保证） | **MOD-IB-16** / 23, 02, 24（ADR-45；IFC-IB-379 / 381） |
  ```
- **性质**: 插入
- **附注**: §9.1 标题行由「**48/48**」**替换**为「**53/53**」（仅计数改动，其余文字一字不动）：
  - 现有原文: `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-48，**48/48 全覆盖**；REV-18 同步计数）`
  - 拟替换: `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-53，**53/53 全覆盖**；REV-19 同步计数）`

---

## 条目 M-20（§9.2 覆盖率新增行）— `docs/module_design.md`

- **章节 / 锚点**: §9.2 表格**末尾**（`| NFR-20 |` 行**之后**）
- **拟插入文本**:
  ```markdown
  | NFR-21 | **专家域 fail-closed 与可观测**（未登记项目 / 默认专家缺失或非唯一 → fail-closed + 结构化日志） | **MOD-IB-16** / 23, 04（ADR-47；IFC-IB-380） |
  ```
- **性质**: 插入
- **附注**: §9.2 标题行由「IB-20」**替换**为「IB-21」（仅计数改动）：
  - 现有原文: `### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-20）`
  - 拟替换: `### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-21）`

---

## 条目 M-21（§9.12 REV-19 覆盖率再声明）— `docs/module_design.md`

- **章节 / 锚点**: §9.11 末段**之后**，`## 10. FreeArk 参考模块映射`（第 1545 行）**之前**
- **拟插入文本**:
  ```markdown
  ### 9.12 REV-19 覆盖率再声明（每项目专家集隔离 + 定义文档目录化 + 新项目种子 + 三专家属 demo + 专家域 fail-closed 增量）

  **结论：REQ 覆盖 48/48 → 53/53（REQ-FUNC）+ 20 → 21（REQ-NFR），无新增缺口。覆盖归属见 §9.1 / §9.2 增行。**

  - **新增覆盖归属**：IB-49（每项目专家集隔离）→ MOD-IB-16（主）/ 02, 19, 23, 24；IB-50（配置页项目域切换 / 加载）→ MOD-IB-24（主）/ 23, 02, 16；IB-51（知识问答项目闭环）→ MOD-IB-23（主）/ 19, 16, 21, 24；IB-52（新项目默认种子）→ MOD-IB-23（主）/ 02, 16, 01；IB-53（三专家属 demo）→ MOD-IB-16（主）/ 23, 02, 24。**NFR-21**（专家域 fail-closed 与可观测）→ MOD-IB-16（主）/ 23, 04。
  - **追踪落点**：IFC-IB-379 ~ 381（专家注册表视图 / 按项目解析 / 内置默认单例）→ REQ-FUNC-IB-49 / IB-53、REQ-NFR-IB-21（ADR-43 / ADR-45 / ADR-47）；IFC-IB-382（路由可选 `experts`）→ REQ-FUNC-IB-49 / IB-51（ADR-43）；IFC-IB-383 / 384（定义文档目录化 + C-IB-46 迁移）→ REQ-FUNC-IB-50、C-IB-46（ADR-44）；IFC-IB-385（创建播种）→ REQ-FUNC-IB-52 / IB-53（ADR-45）；IFC-IB-386（历史迁移）→ C-IB-47 / DR-23（ADR-46）；IFC-IB-387（前端项目域切换 + 问答闭环）→ REQ-FUNC-IB-50 / IB-51（ADR-43 / ADR-44）；IFC-IB-388（检查清单 B24 / B25）→ C-IB-46 / C-IB-47（ADR-44 / ADR-46）。
  - **模块与依赖不变**：模块数仍 **26**、端口数仍 **19**（**未新增**）、**§4.1 依赖边逐行未改**（§4.2.9）。
  - **OQ 处置**：**OQ-IB-32 ~ OQ-IB-40 由 REV-19 正式承接并关闭**（用户裁决 2026-10-11；DR-22 / DR-23）；架构侧只落地「**项目级硬隔离 / 目录化真源 / 创建期种子 / 种子差异归属 / fail-closed / 归属改写非删除**」的安全默认，**不发明**「新建项目默认 KB 问答 agent 的具体命名与文案」（登记为 OPEN ITEM，见 `architecture_design.md` §10.1）。
  - **架构侧对应**：`architecture_design.md` 1.11.0（REV-19）的 **ADR-43 / ADR-44 / ADR-45 / ADR-46 / ADR-47**、**§2.0.10 REV-19 影响复核表**、[ARCH-ASSUMPTION-A6]（REV-19 修订）、[TBD-T28] / [TBD-T29]、§10.1 / §10.2 / §10.3 REV-19 行；`tech_stack.md` **NO_CHANGE**（无新第三方依赖，见主包 Part C）。
  ```
- **性质**: 插入

---

## 条目 M-22（§11 自检 REV-19 追加）— `docs/module_design.md`

- **章节 / 锚点**: §11 自检声明**末尾**（文末最后一行，即 REV-18 自检各项之后）
- **拟插入文本**:
  ```markdown
  - **REV-19 自检（每项目专家集隔离 / 定义文档目录化 / 新项目种子的增量）**：
    - **覆盖同步**：§9.1 由 48/48 同步为 **53/53 REQ-FUNC**（新增 IB-49 ~ IB-53，各有主模块），§9.2 NFR 由 20 同步为 **21**（NFR-21）；**§9.12 给出 REV-19 再声明**。
    - **零新增模块 / 端口 / 依赖边**：模块数仍 **26**、端口数仍 **19**（**未新增**）；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 11 / 16 / 19 / 21 / 23 / 24 / 25（§4.2.9 给出无环性再声明与「为何不新增模块」的编号论证）。
    - **C-IB-45 两条不变量为结构事实**：`ExpertRegistryView.default_expert`（IFC-IB-379）为**必填非空**字段 → 「**默认专家恰好一个**」**不可表达为非法态**；`builtin_default_registry`（IFC-IB-381）恒含**恰 1 个** `is_default` 专家 → 「**永不无应答**」。**不依赖校验放行**。
    - **真源单一未被破坏**：专家集真源 = 每项目定义文档（结构 / 配置域）+ 提示词目录（提示词域），装配期合并（ADR-15-R1 复用）；`IB_DEFINITION_DOC_PATH` 语义 = **目录**（`<dir>/<project_id>.json`，把 [ARCH-ASSUMPTION-A6] 落地），**未引入第二真源**。
    - **红线未破（强制）**：专家集**硬隔离 = 项目级**（**无跨项目回退**）；「**三专家属 demo**」由**种子差异**在**装配期**结构性保证（**非 UI 约定**）；**UI 分组 / 可见性非权限机制**（ADR-42 纪律）；非 admin / 未选项目仍 **fail-closed**。
    - **生效口径未变**：**保存 + 服务重启重装配**（ADR-32 / C-IB-40 / OOS-16）；**不引运行期热重载**、**不重编译编排图**；迁移（C-IB-46 / C-IB-47）**由用户手工执行 + 先备份 + 失败回滚**（C-IB-38）。
    - **编号纪律未破**：`IFC-IB-001 ~ 377` 的号 / 名 / 签名**一字不动**（**仅 5 组文字与取值口径修订**，登记于 §2.2.10）；新增 378 ~ 388 为**纯追加**；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。
    - **类型化未降级**：新增 `IFC-IB-378 ~ 388`（11 条）全部为 `name: type` + 可空性的**类型化契约**，均为 **frozen dataclass / Protocol / 纯 stdlib、零第三方依赖**；`backup_path` 仅登记路径字符串，**不含任何凭据**。
    - **边界合规**：REV-19 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**（全程只读）；需求侧文档（`requirements_spec.md` v1.11.0 / `user_stories.md` v1.11.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **NO_CHANGE**（无新第三方依赖）；**未写入任何口令 / 令牌 / Key / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）；本阶段**止于 GROUP_B**。
  ```
- **性质**: 插入

---

（Part 3 结束。）
