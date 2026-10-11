# REV-19 GROUP_B 架构增量 — Apply-Ready 修订包 · Part 1（封面 / 编辑条目 / 6 问答复）

<file_header>
  <project>intelligentbase</project>
  <artifact>rev19_groupb_apply_package</artifact>
  <path>docs/rev19_groupb_apply_package.md</path>
  <doc_id>ARCH-PKG-INTELBASE-REV19-B</doc_id>
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
    <readonly_reference path="docs/tech_stack.md" version="1.4.1" revision="REV-18" note="目标文件；REV-19 = NO_CHANGE"/>
  </inputs>
  <scope_boundary>只做架构与模块设计；不含实现代码、测试用例、部署脚本。允许接口签名、类型注解、数据结构定义。</scope_boundary>
</file_header>

> **本包性质**：GROUP_B **文档阶段** 的 REV-19 架构增量，**apply-ready**（供 PM 机械 Edit 落盘，**本包不覆盖任何 APPROVED 文件**）。
> **文件构成**：
> - **Part 1（本文件）**：封面 + 应用指导 + 编辑条目总索引 + **Part A**（`architecture_design.md` 编辑条目）+ **Part C**（`tech_stack.md` 决策）+ **Part D**（**6 问答复**）。
> - **Part 2**（`docs/rev19_groupb_apply_package_part2.md`）：**Part E** = 新 ADR-43 ~ ADR-47 全文；**Part F** = `architecture_design.md` §2.0.10 REV-19 影响复核表（全 42 条 ADR 逐条）；**Part G** = 新 IFC 契约全文（IFC-IB-378 ~ IFC-IB-388）。
> - **Part 3**（`docs/rev19_groupb_apply_package_part3.md`）：**Part B** = `module_design.md` 编辑条目。
>
> **纪律（逐条复核后成立）**：**编号只增不改**（ADR 自 **43** 起；IFC 自 **378** 起；既有 ADR / IFC / 模块 / 端口编号与正文**一字不动**，仅 5 组文字 / 取值口径修订按 §2.0.10 登记）；**模块数 26**；**端口数 19**；**§4.1 依赖边逐行不变（零新增边）**；DAG 无环；**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）；**无实现代码 / 伪代码**；**不含任何口令 / Key / token / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）；**凭据纪律**：迁移 / 播种仅登记路径字符串，不入日志、不回显。
> **版本目标**：`architecture_design.md` / `module_design.md` → **1.11.0 / REV-19**；`tech_stack.md` → **NO_CHANGE**（维持 **1.4.1 / REV-18**，无新第三方组件）。
> **阶段边界**：本包**止于 GROUP_B**；**未进入 GROUP_C**；**未改动 `src/` 下任何文件**；**未对生产目标机做任何写操作**；**未 commit / push**。

---

## 01. 应用指导（PM 落盘顺序，建议）

1. **先改文件头**（A-1 / M-1）：`architecture_design.md` 与 `module_design.md` 的 `<version>` / `<revision>` / `<invocation_id>` / `<updated_at>` / `<inputs>`。
2. **再追加 revision_history 行**（A-2 / M-3）：各**一行** `<rev>`；`</revision_history>` 之前插入。
3. **再插入正文块**（A-3 ~ A-10 / M-4 ~ M-22）：全部为**插入类**锚点（除 A-6 / A-3 内含 2 处**替换类**），按锚点逐条 Edit。
4. **§2.0.10 复核表 + ADR-43~47 + 新 IFC**：正文取自 **Part 2**（Part E / Part F / Part G）。PM **直接复制 Part 2 对应代码块**粘贴至指定锚点，无需重排。
5. **最后 `tech_stack.md`**：按 **Part C**，**NO_CHANGE**（不落盘）。
6. **不动 `phase_status.md`**（由 PM 负责）。

> **替换 vs 插入**：每条标注「**替换**」或「**插入**」。替换类给出**逐字现有原文**；插入类给出**前置锚点**（在该锚点**之后**插入）。

---

## 02. 编辑条目总索引

| 条目 | 文件 | 章节 / 锚点 | 性质 | 正文来源 |
|------|------|-------------|------|----------|
| **A-1** | architecture_design.md | `<file_header>` 第 6 / 7 / 11 / 13 行 + `<inputs>` 15 / 16 行 | 替换 | 本件 §Part A |
| **A-2** | architecture_design.md | `</revision_history>` 之前（第 34 行 `</rev>` 之后） | 插入 | 本件 §Part A |
| **A-3** | architecture_design.md | §1.3 表第 108 行（替换）+ §1.3 第 122 行后（插入） | 替换 + 插入 | 本件 §Part A |
| **A-4** | architecture_design.md | §2.0.9 末段（第 386 行）之后、第 388 行 `---` 之前 | 插入 | **Part 2 §Part F** |
| **A-5** | architecture_design.md | ADR-42 正文末（第 1160 行）之后、`## 3.`（第 1162 行）之前 | 插入 | **Part 2 §Part E** |
| **A-6** | architecture_design.md | §8 [ARCH-ASSUMPTION-A6] 行末列（替换）+ A10 行末尾（追加）+ §8 末尾新增行 | 替换 / 追加 | 本件 §Part A |
| **A-7** | architecture_design.md | §9 TBD 表末（第 1385 行 TBD-T27 之后、第 1387 行 `---` 之前） | 插入 | 本件 §Part A |
| **A-8** | architecture_design.md | §10.1 表格末（第 1409 行 OI-3 之后、第 1411 行前） | 插入 | 本件 §Part A |
| **A-9** | architecture_design.md | §10.2 第 1449 行（REV-18 许可面未变）之后 | 插入 | 本件 §Part A |
| **A-10** | architecture_design.md | §10.3 第 1511 行（REV-18 末行）之后 | 插入 | 本件 §Part A |
| **M-1 ~ M-22** | module_design.md | 见 Part 3 | 见 Part 3 | **Part 3** |

---

# Part A — `docs/architecture_design.md` 编辑条目（REV-19）

## 条目 A-1（文件头 + 输入指针）— **替换**

- **章节 / 锚点**: `<file_header>` 第 6 / 7 / 11 / 13 行；`<inputs>` 第 15 / 16 行
- **现有原文**（第 6 / 7 行）:
  ```
    <version>1.10.2</version>
    <revision>REV-18-R2</revision>
  ```
- **拟替换**（第 6 / 7 行）:
  ```
    <version>1.11.0</version>
    <revision>REV-19</revision>
  ```
- **现有原文**（第 11 行）: `  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>`
- **拟替换**（第 11 行）: `  <invocation_id>INV-GROUP_B-INTELBASE-014</invocation_id>`
- **现有原文**（第 13 行）: `  <updated_at>2026-10-07</updated_at>`
- **拟替换**（第 13 行）: `  <updated_at>2026-10-11</updated_at>`
- **现有原文**（第 15 / 16 行）:
  ```
      <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
      <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
  ```
- **拟替换**（第 15 / 16 行）:
  ```
      <input path="docs/requirements_spec.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
      <input path="docs/user_stories.md" version="1.11.0" revision="REV-19" status="APPROVED"/>
  ```
- **性质**: 替换（6 处）

---

## 条目 A-2（revision_history 新增行）— **插入**

- **章节 / 锚点**: `</revision_history>`（第 35 行）**之前**；前置锚点为第 34 行 `REV-18-R2` 的 `</rev>`
- **拟插入文本**（紧接第 34 行 `</rev>` 之后、第 35 行 `</revision_history>` 之前插入一行）:
  ```xml
      <rev version="1.11.0" revision="REV-19" date="2026-10-11" invocation_id="INV-GROUP_B-INTELBASE-014" basis="GROUP_A REV-19 下游贯通（每项目专家集隔离 / 可视化配置项目域切换-加载 / 知识问答项目闭环 / 新项目默认种子 / 三专家属 demo：REQ-FUNC-IB-49~53 / REQ-NFR-IB-21 / C-IB-44~C-IB-47 / OOS-20 / OOS-21 / DR-22 / DR-23）；上游 requirements_spec.md 1.11.0（REV-19）/ user_stories.md 1.11.0（REV-19）（均 APPROVED）；用户裁决 2026-10-11：OQ-IB-32~40 一次拍板" note="REV-19 每项目专家集 / 定义文档目录化 / 新项目种子 / 三专家属 demo（下游贯通）：① 新增 **ADR-43**（每项目专家注册表的解析与 C-IB-45 不变量的结构保证）、**ADR-44**（定义文档物理载体目录化 `IB_DEFINITION_DOC_PATH` 文件 → 目录 + C-IB-46 部署迁移）、**ADR-45**（新项目默认种子与「三专家属 demo」）、**ADR-46**（三专家既有会话 / 历史 / 引用的归属数据迁移 C-IB-47 / DR-23）、**ADR-47**（专家域解析的 fail-closed 与可观测 REQ-NFR-IB-21）；每条含 Context（REQ 引用）/ Options（≥2，含已评估未采纳）/ Decision / Status / Consequences；**ADR 数 42 → 47**；② 新增 **§2.0.10 REV-19 影响复核表**（**既有 42 条 ADR 逐条复核，无一条跳过**：42 条不受影响、其中 **11 条**判「不受影响且 REV-19 是其应用」；**新增 5 条**）；③ §1.3 追加 R19 增补段与定义文档来源行口径修订（**不新增端口**）；④ §8 修订 **[ARCH-ASSUMPTION-A6]**（由「需 PM 确认」订正为「**已确认，落地于 ADR-44**」；一项目一文档 = `<dir>/<project_id>.json`）、[ARCH-ASSUMPTION-A10] 追加「**REV-19 不受影响**」句；⑤ §9 新增 **[TBD-T28]** / **[TBD-T29]**；⑥ §10.1 新增 REV-19 OPEN ITEM（OQ-IB-32~40 承接并关闭 + 新建项目 KB 问答 agent 命名与文案为代码内置且待定，**架构层不发明**）；⑦ §10.2 追加「许可面未变」句；⑧ §10.3 追加 REV-19 自检；⑨ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑩ **计数同步**：REQ-FUNC 48/48 → **53/53**（新增 IB-49~53）、NFR 20 → **21**（新增 NFR-21）。**不变约束**：模块数 26、端口数 19（**未新增**）、既有 `IFC-IB-001 ~ 377` 号 / 名 / 签名一字不动（**仅 5 组文字与取值口径修订**，登记于 §2.0.10 / `module_design.md` §2.2.10）、**§4.1 依赖边逐行不变（零新增边）**、DAG 无环、**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）；新增 IFC 为 **IFC-IB-378 ~ 388**（11 条，见 `module_design.md` §2.2.10）。**红线未破（强制）**：专家集**硬隔离 = 项目级**（**无跨项目回退**）；三专家「属 demo」由**种子差异**结构性保证（**非 UI 约定**）；**UI 分组 / 可见性非权限机制**（ADR-42 纪律）；`kb_id` 仍由已认证主体 `project_id` 推导、**保留** `assert_kb_in_project`（IFC-IB-130）归属断言（失败仍 403）。**C-IB-45 两条不变量为类型层事实**（`ExpertRegistryView.default_expert` 必填非空 + 内置不可删默认专家种子），**不依赖校验放行**。**登记：C-IB-46 / C-IB-47 迁移由用户手工执行 + 先备份 + 失败回滚**（C-IB-38）。需求侧文档与 FreeArk 仓库未改动；**未写入任何口令 / 令牌 / Key / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名 / 头名）。"/>
  ```
- **性质**: 插入

---

## 条目 A-3（§1.3 定义文档来源行口径修订 + R19 增补段）— **替换 + 插入**

### A-3a 行口径修订（**替换**）

- **章节 / 锚点**: §1.3 表第 108 行（「定义文档来源（**R7 新增**）」行）
- **现有原文**（第 108 行，逐字）:
  ```
  | 定义文档来源（**R7 新增**） | `DefinitionDocumentStore`（IFC-IB-287） | `FileDefinitionDocumentStore`（本地文件；原子写 + 语义哈希乐观并发） | 新增适配器（如接 DB / 配置中心，上层零改动） | AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |
  ```
- **拟替换**（第 108 行）:
  ```
  | 定义文档来源（**R7 新增**；**REV-19 口径修订**） | `DefinitionDocumentStore`（IFC-IB-287） | `FileDefinitionDocumentStore`（**本地目录** `<dir>/<project_id>.json`，一项目一文件；原子写 + 语义哈希乐观并发） | 新增适配器（如接 DB / 配置中心，上层零改动） | AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11；**REV-19：REQ-FUNC-IB-50 / C-IB-46** |
  ```
- **性质**: 替换（登记型口径修订：`IB_DEFINITION_DOC_PATH` 由「文件路径」改为「**目录根**」；**端口签名 / 表结构一字不动**）

### A-3b R19 增补段（**插入**）

- **章节 / 锚点**: §1.3 第 122 行（REV-18 增补段）**之后**、`### 1.4 请求上下文传播`（第 124 行）**之前**
- **拟插入文本**:
  ```markdown
  **（REV-19）每项目专家集与定义文档目录化的可替换点显式化**：① **定义文档物理载体**的语义由「文件路径」改为「**目录根**」—— 每项目一文件 `<dir>/<project_id>.json`（`IB_DEFINITION_DOC_PATH` **键名不变**、**端口 `DefinitionDocumentStore`（IFC-IB-287）签名不变**；仅**适配器与文件布局**口径修订，把 `[ARCH-ASSUMPTION-A6]`「一项目一文档」从纸面**落到实现**；换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11；**ADR-44**）。② **每项目专家集**经**装配期派生的只读视图** `ExpertRegistryView`（IFC-IB-379，落在 **MOD-IB-16**，**不是端口**）表达 —— 真源 = 项目定义文档（结构 / 配置域）+ 项目提示词目录（提示词域），装配期合并派生（**ADR-43**）；进程级 `EXPERT_SPECS` **退出生产装配主路径**，降级为「**内置默认单例 + 代码兜底安全网**」（IFC-IB-381）。③ **两个持久化载体的域边界不变**（真源按域唯一）；**禁止**把任一域内容重复写入另一域（ADR-15-R1）。④ **不新增任何端口 / 模块 / 依赖边**；新键名 / 开关 **零新增**。
  ```
- **性质**: 插入

---

## 条目 A-4（§2.0.10 REV-19 影响复核表）— **插入**

- **章节 / 锚点**: §2.0.9 末段（第 386 行「R18 被修订 IFC 逐条登记」）**之后**、第 388 行 `---` **之前**
- **拟插入文本**: **直接复制 Part 2 §Part F 的 ` ```markdown ` 代码块内容**（即 `### 2.0.10 REV-19 影响复核表 …` 至「**REV-19 新增 IFC 清单**」行末），**逐字粘贴**，不重排。
- **性质**: 插入

---

## 条目 A-5（ADR-43 ~ ADR-47 全文）— **插入**

- **章节 / 锚点**: ADR-42 正文末（第 1160 行）、`## 3. …`（§3 标题，第 1162 行）**之前**
- **拟插入文本**: **直接复制 Part 2 §Part E 的「### ADR-43 …」至 ADR-47 正文末**（含每条 Context / Options / Decision / Consequences；**Status** 行随正文），逐字粘贴。
- **性质**: 插入

---

## 条目 A-6（§8 假设项）— **替换 + 追加**

### A-6a [ARCH-ASSUMPTION-A6] 末列修订（**替换**）

- **章节 / 锚点**: §8 假设表第 1341 行（`[ARCH-ASSUMPTION-A6]`（R7 新增）行）的**最后一列**
- **现有原文（该行末列，逐字）**: `| 需 PM 确认（载体与「一项目一文档」口径） |`
- **拟替换（该行末列）**: `| **已确认（REV-19，2026-10-11）**：一项目一文档 = \`<dir>/<project_id>.json\`（\`IB_DEFINITION_DOC_PATH\` 语义 = **目录根**）；**落地于 ADR-44**（含 C-IB-46 迁移）；**不再为待确认项** |`
- **性质**: 替换（登记型：A6 由「需 PM 确认」→「**已确认**」，见 Part D 第 6 问）

### A-6b [ARCH-ASSUMPTION-A10] 追加「REV-19 不受影响」（**追加**）

- **章节 / 锚点**: §8 第 1345 行（`[ARCH-ASSUMPTION-A10]` 行）**行尾**（末列之后追加，**不删既有文字**）
- **拟追加文本**（追加到该行末列结尾）:
  ```
  **（REV-19 复核）不受影响** —— REV-19 的「三专家属 demo」由**种子差异**保证（ADR-45），**不改**本假设的目录布局规则（`<root>/<project_id>/<expert_name>/`）；**提示词目录仍为提示词域唯一真源**（ADR-15-R2 不变）。
  ```
- **性质**: 追加

### A-6c §8 末尾追加 A13（**插入**，可选）

- **章节 / 锚点**: §8 假设表**末行**（第 1347 行 `A12`）**之后**
- **拟插入文本**:
  ```markdown
  | **ARCH-ASSUMPTION-A13**（REV-19 新增） | **新建项目的默认 KB 问答 agent 的名称与文案为代码内置且待定**：ADR-45 落地的**创建期种子**使用「内置默认单例」专家（`is_default=True`，**内置不可删**）；其 `name` / `cn_name` / 默认编排流显示名在 v1 采用**代码内置默认值**，**具体字面由施工期 / 用户指定** | REQ-FUNC-IB-52 只规定「**1 个 KB 问答 agent + 1 个默认编排流**」，**未规定**其命名与文案 | 若用户要求特定命名，只需改**内置默认单例**的常量（**上层零改动**）；**不**新增 REQ / AC 亦可落地（属实现常量，非架构决策） | **登记 OPEN ITEM**（见 §10.1 REV-19 行）；**架构层不发明需求 / 不写死字面** |
  ```
- **性质**: 插入（登记型）

---

## 条目 A-7（§9 TBD 新增 T28 / T29）— **插入**

- **章节 / 锚点**: §9 TBD 表末（第 1385 行 `TBD-T27` 行）**之后**、第 1387 行 `---` **之前**
- **拟插入文本**:
  ```markdown
  | **TBD-T28（REV-19 新增）** | **每项目专家注册表的装配期成本**：`ExpertRegistryView`（IFC-IB-379）随 `Deps.derived_views[project_id]` 携带的**内存增量**（项目数 × 专家数），`resolve_expert_registry`（IFC-IB-380）的**解析耗时**，以及「按项目注入专家集」对装配期冷启动耗时的增量（与 [TBD-T24] / [TBD-T19] 同源） | REQ-FUNC-IB-49 / IB-53；REQ-NFR-IB-21；ADR-43 / ADR-47 | 定是否需要缓存 / 惰性派生（**缓存不得成为读源**）。**未经实测前不得给出容量 / 耗时结论** |
  | **TBD-T29（REV-19 新增）** | **创建期播种与历史迁移的成本与一致性**：① `POST /api/projects` → `seed_project`（IFC-IB-385）的**写盘耗时**与失败回滚的实际发生率；② `migrate_expert_history`（IFC-IB-386）**跨载体**（会话状态 + SQLite `sessions` 表 + citations）的**一致性窗口**与耗时；③ 目录化迁移 `migrate_legacy_definition_file`（IFC-IB-384）在目标机的实测 | REQ-FUNC-IB-52 / IB-53；C-IB-46 / C-IB-47；ADR-44 / ADR-45 / ADR-46 | 定播种 / 迁移的**真机验证口径**（部署检查清单 B24 / B25）。**未经实测前不得给出耗时 / 一致性结论** |
  ```
- **性质**: 插入

---

## 条目 A-8（§10.1 REV-19 OPEN ITEM）— **插入**

- **章节 / 锚点**: §10.1 表（第 1393 ~ 1409 行）**末行**（第 1409 行 `OI-3` 行）**之后**、第 1411 行（`**（REV-17）OPEN ITEM …`）**之前**
- **拟插入文本**:
  ```markdown
  | **（REV-19）OQ-IB-32 ~ OQ-IB-40 的架构承接与关闭** | ① 定义文档载体「一项目一文件」（OQ-IB-32）；② 新项目默认专家（OQ-IB-33）；③ 专家集硬隔离（OQ-IB-34）；④ 三专家在非 demo 的可见性（OQ-IB-35）；⑤ 新项目默认编排流（OQ-IB-36）；⑥-⑨ 其余边界（OQ-IB-37 ~ IB-39）；⑩ 三专家历史去向（OQ-IB-40） | ① 目录化 `<dir>/<project_id>.json`（**ADR-44**）；② 内置**不可删**默认单例（**ADR-45 / IFC-IB-381**）；③ 项目级**硬隔离**、**无跨项目回退**（**ADR-43**）；④ **种子差异**保证「三专家属 demo」（**ADR-45**）；⑤ **单一默认编排流**、**不自定 DAG**（**ADR-45 / OOS-21**）；⑥-⑨ 由 **fail-closed** 与 **C-IB-45 结构不变量**承接（**ADR-47**）；⑩ 归属改写为 demo、**记录保留**（**ADR-46**） | **由 REV-19 正式承接并关闭**（用户裁决 2026-10-11；DR-22 / DR-23）；架构侧只落地「**项目级硬隔离 / 目录化真源 / 创建期种子 / 种子差异归属 / fail-closed / 归属改写非删除**」的安全默认，**不发明**业务内容 |
  | **（REV-19）新建项目默认 KB 问答 agent 的名称 / 文案与默认编排流显示名** | REQ-FUNC-IB-52 只规定「**1 个 KB 问答 agent + 1 个默认编排流**」，**未规定**其 `name` / `cn_name` / 显示名 | 架构侧取**代码内置默认值**（`is_default=True`，**内置不可删**；见 **ADR-45** / **IFC-IB-381**）；**具体字面由施工期 / 用户指定**，**本包不写死** | **保持 OPEN（施工期定，不阻塞）**：口径已收敛到「**恰 1 个**默认 KB 问答 agent + 1 默认编排流」；命名 / 文案属实现常量，**架构层不发明需求、不新增 AC**（登记 `[ARCH-ASSUMPTION-A13]`） |
  ```
- **性质**: 插入

---

## 条目 A-9（§10.2 许可面未变）— **插入**

- **章节 / 锚点**: §10.2 第 1449 行（`**（REV-18）许可面未变**…`）**之后**、第 1451 行（`### 10.3 自检声明`）**之前**
- **拟插入文本**:
  ```markdown
  **（REV-19）许可面未变**：本增量**未引入任何第三方组件** —— 定义文档目录化复用**同一** `FileDefinitionDocumentStore`（本地文件系统，stdlib `os` / `json`）；专家注册表视图 `ExpertRegistryView`（IFC-IB-379）/ 解析 `resolve_expert_registry`（IFC-IB-380）/ 迁移 `migrate_*`（IFC-IB-384 / 386）/ 播种 `seed_project`（IFC-IB-385）/ 结果值对象（IFC-IB-378）**均为 frozen dataclass / Protocol / 纯 stdlib**；前端项目域切换**复用既有** `projectContext` store（IFC-IB-335）与 `client.ts`（IFC-IB-334），**无新前端库**。故本节许可台账**不变**（`tech_stack.md` 记 **NO_CHANGE**，维持 **1.4.1 / REV-18**）。
  ```
- **性质**: 插入

---

## 条目 A-10（§10.3 自检 REV-19 追加）— **插入**

- **章节 / 锚点**: §10.3 第 1511 行（REV-18 末行）**之后**（文末追加）
- **拟插入文本**:
  ```markdown
  - **（REV-19）每项目专家集 / 定义文档目录化 / 新项目种子 / 三专家属 demo 增量已贯通**：新增 **ADR-43 / ADR-44 / ADR-45 / ADR-46 / ADR-47**（每条含 Context（**REQ 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.10 REV-19 影响复核表**（**既有 42 条 ADR 全部已复核**：不受影响 **42**、其中 **11 条**判「不受影响且 REV-19 是其应用」、待裁决 **0**、**新增 5**、**无一条跳过**）；新增 IFC **IFC-IB-378 ~ 388**（11 条，见 `module_design.md` §2.2.10）；§1.3 追加 R19 增补段与定义文档来源行口径修订（**不新增端口**）、§8 修订 [ARCH-ASSUMPTION-A6] / 追加 A10 复核句 / 新增 [ARCH-ASSUMPTION-A13]、§9 新增 [TBD-T28] / [TBD-T29]、§10.1 新增 REV-19 OPEN ITEM（OQ-IB-32~40 承接并关闭 + 默认 KB 问答 agent 命名待定）、§10.2 追加「许可面未变」句。
  - **（REV-19）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口数仍 **19**（**未新增端口**）、`IFC-IB-001 ~ 377` **号 / 名 / 签名一字不动**（**仅 5 组文字与取值口径修订**，逐条登记于 §2.0.10：`IFC-IB-287` / `289` / `297` / `172 ~ 179` / `201`）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.9）；REQ→MOD 覆盖 **53/53 REQ-FUNC（由 48 同步）+ 21 NFR（由 20 同步）**。
  - **（REV-19）C-IB-45 两条不变量为类型层事实**：`ExpertRegistryView.default_expert`（IFC-IB-379）为**必填非空**字段 → 「**默认专家恰好一个**」**不可表达为非法态**；`builtin_default_registry`（IFC-IB-381）恒含**恰 1 个** `is_default` 专家（**内置不可删**）→ 「**永不无应答**」。**不依赖「校验放行」**。
  - **（REV-19）红线未被破坏（强制）**：专家集**硬隔离 = 项目级**（`ExpertRegistryView` 按 `project_id` 装配期解析，**无跨项目回退**）；`kb_id` 仍由已认证主体的 `project_id` 推导，**保留** `LedgerRepository.assert_kb_in_project`（IFC-IB-130）归属断言（失败仍 **403**）；「**三专家属 demo**」由**种子差异**在装配期结构性保证（**非 UI 约定**）；**「UI 分组 / 可见性非权限机制」**（ADR-42 纪律）。
  - **（REV-19）生效口径与运维动作（登记，不自动执行）**：专家集 / 种子 / 迁移**一律经「保存 + 服务重启重装配」生效**（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载、**不重编译编排图**；**登记：C-IB-46 定义文档目录化迁移与 C-IB-47 三专家历史迁移由用户手工执行 + 先备份 + 失败回滚**（C-IB-38）—— 架构 / 部署文档只写「由用户执行」的动作。
  - **（REV-19）凭据纪律**：全文**只登记键名 / 头名 / 表名 / 字段名 / 文件名**（`IB_DEFINITION_DOC_PATH` / `IB_EXPERT_PROMPT_DIR` / `sessions` / `project_id`）；迁移 / 播种**仅登记路径字符串**，`backup_path` **不入日志、不回显**；**未写入任何口令 / 令牌 / Key / 证书字面量**；令牌仅经 `Authorization` 头，`?token=` 纪律对**全部新端点**有效。
  - **（REV-19）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` v1.11.0 / `user_stories.md` v1.11.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **NO_CHANGE**（无新第三方依赖，见本包 Part C）；本阶段**止于 GROUP_B**。
  ```
- **性质**: 插入

---

# Part C — `docs/tech_stack.md` 决策：**NO_CHANGE**

- **文件**: `docs/tech_stack.md`
- **决策**: **NO_CHANGE** —— 维持 **1.4.1 / REV-18**；**不落盘、不改任何行**。
- **理由（逐条复核）**：REV-19 的**全部新增均为类型化契约 / frozen dataclass / Protocol / 纯 stdlib**（`ExpertRegistryView`、`resolve_expert_registry`、`migrate_*`、`seed_project`、结果值对象），以及**既有库的既有用法扩展**（`FileDefinitionDocumentStore` 本地目录化 = stdlib `os` / `json`；前端项目域切换**复用**既有 `projectContext` / `client.ts`）；**未引入任何新的第三方库 / 二进制 / 服务**，**未新增前端依赖**，**未新增数据库 / 中间件**。
- **与 §10.2 一致**：`architecture_design.md` §10.2 追加「**（REV-19）许可面未变**」句（条目 A-9），与 `tech_stack.md` **NO_CHANGE** 相互印证。
- **许可与红线**：**禁 Docker / 禁 PyMuPDF(fitz) / 禁运行时 CDN** 均未触及（REV-19 无部署拓扑变化、无新前端产物来源、无 PDF 解析变化）；FreeArk **全程只读**。
- **若 PM 需要**：可在 `tech_stack.md` 的修订日志追加一行「REV-19：NO_CHANGE（无新第三方依赖；见 `docs/rev19_groupb_apply_package.md` Part C）」—— **可选，非必需**（默认不落盘以严守「不改 APPROVED 文件」）。

---

# Part D — 6 问答复（每问标注落点：ADR / 模块 / IFC）

> 答复与 **Part 2 / Part 3** 一致；每条给出「**结论 + 落点**」。

## 问 1：`EXPERT_SPECS` 进程级单例 → 每项目解析

**(a) 真源与解析时机**：真源**不是**全局单例，而是「**每项目定义文档（结构 / 配置域）+ 每项目提示词目录（提示词域）**」在**装配期合并派生**；**解析时机 = 装配期（服务启动 / 重启重装配）**，**非请求期**（**不引运行期热生效**，ADR-32 / C-IB-40 / OOS-16）。
**落点**：**ADR-43**（Decision Option B）；**IFC-IB-379**（`ExpertRegistryView`，frozen 值对象）/ **IFC-IB-380**（`resolve_expert_registry`，装配期纯函数，fail-closed）；**模块 MOD-IB-16**（视图定义与解析）/ **MOD-IB-23**（组合根在装配序列调用并注入）。

**(b) 装配链改动面**：进程级 `EXPERT_SPECS` **退出生产装配主路径**，降级为「**内置默认单例 + 代码兜底安全网**」；消费点改为**构造注入**（append-only）。
**落点**：**IFC-IB-381**（内置默认单例语义澄清 + `builtin_default_registry`）；**IFC-IB-382**（`IntentRouter.__init__` **增 keyword-only 可选 `experts`**，`None` → 内置默认单例，行为**逐位一致**）；`orchestrator_for`（`composition.py:200 / 213`）与 `_default_definition_document`（`1207 / 1221 / 1251`）改取**本项目视图**；`_inject_derived_experts` / `_inject_prompt_bundles` 的「取首项目 → 全局 rebind」（`633-634`）**退化为兼容保留**；**模块 MOD-IB-19 / MOD-IB-16 / MOD-IB-23**。**零新增模块 / 端口 / 依赖边**。

**(c) C-IB-45 两条不变量如何由结构（而非校验放行）保证**：
- 「**默认专家恰好一个**」→ `ExpertRegistryView.default_expert` 为**必填、非空、不可为 `None`** 字段（**IFC-IB-379**）；`experts` **非空**且 `default_expert.name ∈ experts` —— **0 或 ≥2 个默认专家在类型层不可表达**（构造即非法）。
- 「**永不无应答**」→ 内置默认单例 `builtin_default_registry`（**IFC-IB-381**）恒含**恰 1 个** `is_default=True` 的专家（**内置不可删**，OQ-IB-33(a)）；`resolve_expert_registry`（**IFC-IB-380**）在默认专家缺失 / 非唯一 / 专家集为空时 **fail-closed**（`ExpertRegistryError`，**无回退**）——**不会退化为「无专家可路由」**。
**落点**：**ADR-43**（Decision ③ + Consequences「成为类型层事实」）；**ADR-47**（fail-closed）；**模块 MOD-IB-16**；**IFC-IB-379 / 380 / 381**。

---

## 问 2：C-IB-46 部署迁移（`IB_DEFINITION_DOC_PATH` 文件 → 目录）

**结论**：`IB_DEFINITION_DOC_PATH` 语义由「**文件路径**」改为「**目录根**」；目录布局 = **`<dir>/<project_id>.json`（一项目一文件）**。
**落点**：**ADR-44**（Option A，含 Option B「双键并存」/ Option C「DB 表」**已评估未采纳**）；**IFC-IB-383**（`FileDefinitionDocumentStore` 目录化 + `_path_for(project_id)`，「**消除 F5 偏差**」——旧 `load()` 忽略 `project_id`）；**IFC-IB-384**（`migrate_legacy_definition_file`）；**模块 MOD-IB-02**（数据层）/ **MOD-IB-25**（检查清单 **B24**，**IFC-IB-388**）。
**兼容 / 迁移路径**：旧单文件（生产 `/var/lib/intelligentbase/definition.json`）若存在且 `<dir>/demo.json` **不存在** → **备份后移动**；目标**已存在** → **fail-closed（不覆盖）**；迁移**由用户手工执行 + 先备份 + 失败回滚**（C-IB-38 / C-IB-46）。
**失败回滚**：语义变更后目录未配置 / 不可用 → **装配期 fail-closed**（可读错误 + **指明迁移目标**），**不回退到「单文件」旧语义、不静默当空文档**。**端口 `DefinitionDocumentStore`（IFC-IB-287）签名不变**（仅文字口径修订，登记于 §2.0.10）。**零新增端口 / 模块 / 依赖边**。

---

## 问 3：C-IB-47 数据迁移（三专家会话 / 历史 / 引用改属 `demo`）

**结论**：**归属改写**（**不删除任何行**），**架构范围**如下（**无实现代码**）。
**落点**：**ADR-46**（Option A，Option B「删除」/ Option C「双份」**已评估未采纳**）；**IFC-IB-386**（`migrate_expert_history`）；**模块 MOD-IB-21**（会话状态）/ **MOD-IB-11**（`sessions` 表）/ **MOD-IB-25**（检查清单 **B25**，**IFC-IB-388**）。
**涉及的表 / 载体**：① 会话状态（`SessionStore` / `SessionState` / `SessionTurn`，**MOD-IB-21**）；② 台账 `sessions` 表中的 `SessionRecord.project_id`（**MOD-IB-11**）；③ 引用 / 引文记录（citations）。
**所有权字段** = `project_id`；**改写规则** = 「`project_id != 'demo'` 且记录引用了 `freeark-expert` / `inspection-expert` / `sanheng-knowledge` 之一」→ 置 `project_id = 'demo'`。
**幂等** = 已属 `demo` 的记录**跳过**（重复执行无副作用）；**手工 + 先备份 + 失败回滚**（C-IB-38）。
**与 DR-21「误删优先软删」的关系** = 本迁移是**归属改写而非删除**、**不删除任何行**，故**无冲突、可回滚**。
**显式登记**：「**非 demo 项目因此失去这些历史**」（C-IB-47 / AC-IB-45-04 明文）。**零新增表 / 列 / 模块 / 端口 / 依赖边**。

---

## 问 4：新项目默认种子（REQ-FUNC-IB-52）

**结论**：**创建期播种**（`POST /api/projects` 注册表写入成功后，由组合根**同步**播种）。
**真源** = **项目自身专家集**；**新建项目种子 = 内置默认单例（1 个 KB 问答 agent，`is_default=True`，内置不可删）+ 1 个默认编排流（单一 DAG，不自定）**；**`demo` 项目种子 = 三对齐专家**。
**落点**：**ADR-45**（Option A「创建期播种」选定；Option B「懒播种」/ Option C「装配期统一播种」**已评估未采纳**，Option C 仅保留为**装配期兜底**）；**IFC-IB-385**（`seed_project`）；**模块 MOD-IB-23**（创建端点 / 组合根播种）+ **MOD-IB-02**（`_default_definition_document` 改用该项目专家集）+ **MOD-IB-01**（内置默认单例契约，**IFC-IB-381**）。
**幂等**（已存在不覆盖）；**原子回滚**（任一子步失败 → 删除半成品 + 明确错误，**不静默**）；**装配期兜底**：启动时对未落盘项目构造内置默认种子。**零新增模块 / 端口 / 依赖边**。

---

## 问 5：可视化配置项目域切换 / 加载（REQ-FUNC-IB-50）+ 知识问答项目闭环（REQ-FUNC-IB-51）

**结论**：**复用**既有前端项目域机制（`projectContext` store = IFC-IB-335；`client.ts` 单一注入点 = IFC-IB-334），**服务端为唯一裁决者**。
**落点**：**ADR-43 / ADR-44**（专家集与定义文档按项目解析）；**IFC-IB-387**（前端项目域切换 + 知识问答项目闭环）；**模块 MOD-IB-24**（前端）/ **MOD-IB-23**（HTTP / 组合根）/ **MOD-IB-19**（路由 `experts` 注入）/ **MOD-IB-16**（项目视图）。
**不变量如何保持**：
- **`orchestrator_for` 对未登记项目 fail-closed（`StartupError`，无回退）**：**既有语义一字不动**（**ADR-47** 明确「运行期 `orchestrator_for` 未登记项目 → `StartupError`，既有语义一字不动」；组合根仍不回落全局或其他项目）。
- **已 `bind_tools(Scope(project_id=…))`**：**保持**——知识问答提问**绑定当前项目域**（`X-IB-Project`），`Scope` 仍为**必填参数**（IFC-IB-201 的 `scope` 无默认值，类型层防漏传）；答案引用 / 检索范围限于该项目（**非 demo 项目不出现三专家的知识 / 历史**）。**未选项目** → 前端**不发送** `X-IB-Project` → 服务端 **fail-closed**（同 ADR-28）；**禁止**把全局哨兵解析为「全项目并集」。
- **「项目闭环」非前端过滤**：是服务端 `Scope(project_id=…)` + `orchestrator_for` **fail-closed** 的既有事实；前端切换仅为**体验面**，**可解析性 / 授权唯一裁决者为服务端**（**ADR-42 纪律复用**）。
**生效口径**：配置页编辑**只写当前项目**；生效仍为「**保存 + 服务重启重装配**」（ADR-32 / C-IB-40 / OOS-16），**不引即时跨项目生效**。**零新增模块 / 端口 / 依赖边**。

---

## 问 6：`[ARCH-ASSUMPTION-A6]` 与 `[ARCH-ASSUMPTION-A10]` —— 修订还是升格 ADR？

**结论**：**A6 → 本轮修订（登记型：由「需 PM 确认」订正为「已确认」），并将其实质内容升格为正式 ADR-44**；**A10 → 本轮登记「不受影响」**（保持既有的「已确认并转为决策」状态，**不新增 ADR**）。
**A6**：「一项目一文档」口径**已确认**，落地为 **ADR-44**（**IFC-IB-383 / 384**；`IB_DEFINITION_DOC_PATH` = **目录根**，`<dir>/<project_id>.json`，含 **C-IB-46** 迁移）；§8 A6 行末列按 **A-6a** 替换（登记型）。**理由**：A6 原先的「载体（本地文件）」与「一项目一文档」在 REV-19 被**同时确定**，载体细节（目录化 + 迁移）已构成**架构决策**（有 ≥2 方案、有权衡、有部署后果），**宜以 ADR-44 承载**，A6 记账为「已确认」。
**A10**：提示词目录物理布局（`<root>/<project_id>/<expert_name>/`）**未被 REV-19 改动** —— REV-19 只把「**三专家属 demo**」改为由**种子差异**保证（ADR-45），**不触及** A10 的目录规则；故 **A10 登记「不受影响」**（§8 A10 行末追加，**A-6b**），**不升格为新 ADR**。**理由**：A10 早在 REV-16-3 已「确认并转为决策」，修改它需要**新的目录布局事实**，而 REV-19 无此事实。
**新增登记**：REV-19 新增 **`[ARCH-ASSUMPTION-A13]`**（新建项目默认 KB 问答 agent 的名称 / 文案待定；**A-6c**）—— 属**实现常量**，**不升格 ADR**。

---

（Part 1 结束。新 ADR 全文 / §2.0.10 复核表 / 新 IFC 全文见 `docs/rev19_groupb_apply_package_part2.md`（Part 2）；`module_design.md` 编辑条目见 `docs/rev19_groupb_apply_package_part3.md`（Part 3）。）
