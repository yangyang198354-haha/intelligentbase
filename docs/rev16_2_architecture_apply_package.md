# REV-16-2 架构侧落盘包（GROUP_B 增量）

> **2026-10-06 凭据洁净核验通过（口径如上）**：本包全文只登记键名 / 头名 / 标签名，不含任何口令 / 令牌 / 密钥字面量；全模式扫描（sk- / ghp_ / -----BEGIN / Bearer / 口令 / 密钥）零命中。

> **性质**：GROUP_B（系统架构 / 模块详细设计）**落盘指令包**。PM / 编排器按本包逐条机械应用 Edit 即可；本包**不含实现代码**，**不改动 `src/`**，**不整文件重写**三份受保护设计文档。
> **上游**：`docs/rev16_2_ruling_apply_package.md`（GROUP_A 需求侧 REV-16-2 落盘包）+ `docs/requirements_spec.md` 1.6.0 / `docs/user_stories.md` 1.6.0（均 `APPROVED`）。
> **只读参考**：`C:/Users/胖子熊/MyProject/FreeArk`（**严格只读**；本增量**未修改**其任何文件）。
> **凭据纪律**：本包**只登记键名 / 头名 / 标签名**，**不含任何口令 / 令牌 / 密钥字面量**。

---

## §0 元数据与编号账本

### 0.1 文档版本

| 文件 | 落盘前 | 落盘后 | 说明 |
|------|--------|--------|------|
| `docs/architecture_design.md` | 1.6.0 / REV-14 / `INV-GROUP_B-INTELBASE-008` | **1.7.0 / REV-16-2 / `INV-GROUP_B-INTELBASE-009`** | 提示词分层 + 工具可配置 + FreeArk 严格对齐 + **ADR-15 正式修订** |
| `docs/module_design.md` | 1.6.0 / REV-14 / `INV-GROUP_B-INTELBASE-008` | **1.7.0 / REV-16-2 / `INV-GROUP_B-INTELBASE-009`** | 同上 |
| `docs/tech_stack.md` | 1.4.0 / REV-13 / `INV-GROUP_B-INTELBASE-007` | **NO_CHANGE（不改）** | 本增量**零新增第三方依赖**（全部为类型定义 / 纯 stdlib / 现有库用法） |

### 0.2 编号账本（一律**追加**，既有编号一字不动）

| 类别 | 落盘前最大号 | 本增量新增 | 规则 |
|------|--------------|------------|------|
| ADR | ADR-28 | **ADR-29 / ADR-30 / ADR-31 / ADR-32**（4 条）+ 修订子节 **`ADR-15-R1`** | 新增号只许追加；ADR-15 正文 / Status **不改**，修订以 `-R1` 子节承载（沿用 ADR-11-R1 / ADR-13-R1 先例） |
| 端口 | 15（`AccountStore`，IFC-IB-310） | **16**（`ExpertPromptStore`，IFC-IB-339） | 纯追加 |
| IFC | IFC-IB-336 | **IFC-IB-337 ~ IFC-IB-354**（18 条） | 新增号从 **337** 起；`IFC-IB-001~336` 的号 / 名 / 签名 / 字段集**一字不动**；`IFC-IB-285` 仍**预留未分配**；既有重号 `IFC-IB-131` 登记不修 |
| 模块 | MOD-IB-26（共 26） | **0（不新增；共仍 26）** | 全部落点**并入既有模块**；理由见 §0.4 |
| REQ 覆盖 | REQ-FUNC 36/36、NFR 18 | **REQ-FUNC 42/42、NFR 19** | 新增 IB-37~42（6 条）+ NFR-19 |
| 依赖边 | §4.1 逐行 | **零新增边** | 全部复用既有边（`23 → 01/02/…`、`24 → 23`） |

### 0.3 约束溯源

- 触发需求：**REQ-FUNC-IB-37**（提示词分层语义：主 + 兜底）、**IB-38**（提示词可视化编辑与保存）、**IB-39**（工具授权可视化配置与保存）、**IB-40**（保存并经服务重启后生效）、**IB-41**（可经文件保存 / 落盘形态）、**IB-42**（示例项目与 FreeArk 专家 100% 对齐）、**REQ-NFR-IB-19**（一致性 / 可观测 / fail-safe）。
- 触发约束 / 开放项：**C-IB-39**（ADR-15 触发修订）、**C-IB-40**（时效纪律）、**OQ-IB-24**（承接 ADR-15 正式修订）、**OOS-16**（移除「无需重启即生效」验收范围）、**DR-19**（OQ-IB-16~23 一揽子裁决）。

### 0.4 为何**零新增模块**

新增工件（提示词目录载体 / 工具参数 / 对齐比对）**必然被组合根 `MOD-IB-23` 依赖**；若新开模块只能取 **>=27** 的编号 → 产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**，破坏 §4.2 构造性无环证明。故按既有纪律（`module_design.md` §1 R7 补充纪律 / §4.2.2 末句）**并入既有模块**。落点分配：契约与端口 → **MOD-IB-01**；装载 / 校验 / 保存 / 派生 / 键名 → **MOD-IB-02**；派生注册表扩展 → **MOD-IB-16**；工具授权与参数绑定 → **MOD-IB-17**；聚合禁止标签派生 → **MOD-IB-22**；端点与装配序列 → **MOD-IB-23**；前端编辑器 → **MOD-IB-24**。

---

## §1 落盘指令 · `docs/architecture_design.md`（A-01 ~ A-17，共 17 条）

> 记法：**锚点**为**原文唯一子串**（Edit 的 `old_string`）；**动作**为「替换为」或「其后追加」；**新文本**见 §4 对应块（逐字）。

| # | 锚点（原文，唯一） | 动作 / 新文本 |
|---|--------------------|----------------|
| A-01 | `  <version>1.6.0</version>` | 替换为 `  <version>1.7.0</version>` |
| A-02 | `  <revision>REV-14</revision>` | 替换为 `  <revision>REV-16-2</revision>` |
| A-03 | `  <invocation_id>INV-GROUP_B-INTELBASE-008</invocation_id>` | 替换为 `  <invocation_id>INV-GROUP_B-INTELBASE-009</invocation_id>` |
| A-04 | 连续两行：`    <input path="docs/requirements_spec.md" version="1.4.0" status="APPROVED"/>` + `    <input path="docs/user_stories.md" version="1.4.0" status="APPROVED"/>` | 两行 `version="1.4.0"` 均替换为 `version="1.6.0"` |
| A-05 | `  </revision_history>` | 在其**之前**插入 §4.A 的 `<rev version="1.7.0" revision="REV-16-2" …/>` |
| A-06 | `**版本**: 1.5.0（REV-13 增量）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06` | 替换为 `**版本**: 1.7.0（REV-16-2 增量）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06` |
| A-07 | 行尾子串 `（**14 → 15，纯追加**）、\`IFC-IB-001~308\` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环。` | 在其**之后**追加 §4.B 的「REV-16-2 修订摘要」整段 |
| A-08 | 行尾子串 `**R14 复核小结**：既有 **27 条 ADR 全部不受影响**…新增 IFC 为 **IFC-IB-333 ~ 336**（见 \`module_design.md\` §2.2.5）。` | 在其**之后**追加 §4.C 的 `### 2.0.6 R16-2 影响复核表` |
| A-09 | `### ADR-16 装配期完备性校验与 fail-fast 准入闸门` | 在其**之前**插入 §4.D 的 `### ADR-15-R1 …` 整节 |
| A-10 | `## 3. 多项目隔离：链路落点与跨项目泄漏失败模式` | 在其**之前**插入 §4.E 的 `ADR-29` / `ADR-30` / `ADR-31` / `ADR-32` 四节 |
| A-11 | `| 定义文档来源（**R7 新增**） | \`DefinitionDocumentStore\`（IFC-IB-287） | \`FileDefinitionDocumentStore\`（本地文件；原子写 + 语义哈希乐观并发） | 新增适配器（如接 DB / 配置中心，上层零改动） | AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |` | 在其**之后**追加 §4.F 的表行「独立提示词目录来源（**REV-16-2 新增**）」 |
| A-12 | `### 1.4 请求上下文传播（隔离贯穿全链路）` | 在其**之前**插入 §4.G 的「（REV-16-2）提示词载体与工具参数可替换点」段 |
| A-13 | 行首子串 `| **ARCH-ASSUMPTION-A9**（R13 新增） |` 所在整行（§8 表末行） | 在其**之后**追加 §4.H 的 `[ARCH-ASSUMPTION-A10]` 行 |
| A-14 | 行首子串 `| **TBD-T23（R13 新增）** |` 所在整行（§9 表末行） | 在其**之后**追加 §4.I 的 `[TBD-T24]` 行 |
| A-15 | 行首子串 `| **（R13）OQ-IB-09 ~ OQ-IB-15 的架构默认取值落地** |` 所在整行（§10.1 表末行） | 在其**之后**追加 §4.J 的 R16-2 行 |
| A-16 | `完整选型与风险表见 \`tech_stack.md\`。` | 在其**之前**插入 §4.K 的「（REV-16-2）许可合规」段 |
| A-17 | 行首子串 `- **（R14）未改动他处**：` 所在整行（§10.3 末行） | 在其**之后**追加 §4.L 的 R16-2 自检行 |

---

## §2 落盘指令 · `docs/module_design.md`（M-01 ~ M-31，共 31 条）

| # | 锚点（原文，唯一） | 动作 / 新文本 |
|---|--------------------|----------------|
| M-01 | `  <version>1.6.0</version>` | 替换为 `  <version>1.7.0</version>` |
| M-02 | `  <revision>REV-14</revision>` | 替换为 `  <revision>REV-16-2</revision>` |
| M-03 | `  <invocation_id>INV-GROUP_B-INTELBASE-008</invocation_id>` | 替换为 `  <invocation_id>INV-GROUP_B-INTELBASE-009</invocation_id>` |
| M-04 | 连续三行 `<input path="docs/requirements_spec.md" version="1.4.0" …/>` / `<input path="docs/user_stories.md" version="1.4.0" …/>` / `<input path="docs/architecture_design.md" version="1.5.0" revision="REV-13" …/>` | 前两行 `version="1.4.0"` → `version="1.6.0"`；第三行 `version="1.5.0" revision="REV-13"` → `version="1.7.0" revision="REV-16-2"` |
| M-05 | `  </revision_history>` | 在其**之前**插入 §4.M 的 `<rev no="REV-16-2" …/>` |
| M-06 | `**版本**: 1.5.0 (REV-13) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06` | 替换为 `**版本**: 1.7.0 (REV-16-2) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06` |
| M-07 | `**R2 性质**: …二者冲突时以契约文件为准。` | 在其**之后**追加 §4.N 的「**REV-16-2 性质**」段 |
| M-08 | 行首子串 `26 个模块（R2 新增 MOD-IB-26；**R7 未新增模块**` 所在整行 | 在该行「**R7 未新增模块**」后插入 `；**R8 / R13 / R14 / REV-16-2 均未新增模块**`（**仅改此一处措辞**） |
| M-09 | `**R7 补充纪律（编号即拓扑序的边界情形）**：` | 在该段**之后**追加 §4.O 的「**REV-16-2 补充纪律**」段 |
| M-10 | 行首子串 `| \`StreamEventKind\` **值域追加成员**（R8，定义于 MOD-IB-01） |` 所在整行（§2.1 末行） | 在其**之后**追加 §4.P 的 4 行结构定义 |
| M-11 | 行首子串 `| \`AccountStore\`（**R13 新增**） |` 所在整行（§2.2 端口表末行） | 在其**之后**追加 §4.Q 的端口表行「\`ExpertPromptStore\`（**REV-16-2 新增**）」 |
| M-12 | `> **方法数订正说明**：来源修订包` | 在其**之前**插入 §4.R 的「**REV-16-2 增记（第 16 个端口）**」段 |
| M-13 | `## 3. 模块详情` | 在其**之前**插入 §4.S 的 `### 2.2.6 REV-16-2 新增 IFC 段号索引` 整节 |
| M-14 | `- **依赖模块**: 无` （MOD-IB-01 段内） | 在其**之前**插入 §4.T 的 MOD-IB-01 增补条目（IFC-IB-337 ~ 342） |
| M-15 | `### MOD-IB-03 请求上下文 (L0)` | 在其**之前**插入 §4.U 的 MOD-IB-02 增补条目（IFC-IB-343 ~ 348） |
| M-16 | `  - IFC-IB-179: \`get(name: str) -> ExpertSpec | None\`` | 在其**之后**追加 §4.V 的 MOD-IB-16 增补条目（IFC-IB-349） |
| M-17 | `  - IFC-IB-183: \`bind_scope(tools: list[RegisteredTool], scope: Scope, retrieval: RetrievalService) -> list[BoundTool]\`` 所在行 | 在其**之后**追加 §4.W 的 MOD-IB-17 增补条目（IFC-IB-350） |
| M-18 | `- **依赖模块**: MOD-IB-01、IB-02、IB-03、IB-04、MOD-IB-16、IB-17、IB-18、IB-19、IB-20、IB-21` | 在其**之前**插入 §4.X 的 MOD-IB-22 增补条目（IFC-IB-351） |
| M-19 | `### MOD-IB-24 Web 前端 (L5)` | 在其**之前**插入 §4.Y 的 MOD-IB-23 增补条目（IFC-IB-352 / 353） |
| M-20 | `  - **恢复失败可读回执**：` | 在该行**之后**追加 §4.Z 的 MOD-IB-24 增补条目（IFC-IB-354） |
| M-21 | `### 4.3 分层视图` | 在其**之前**插入 §4.AA 的 `### 4.2.6 REV-16-2 无环性再声明` 整节 |
| M-22 | 行首子串 `| \`AccountStore\`（**R13 新增**） |` 所在整行（§5 装配表末行） | 在其**之后**追加 §4.AB 的装配表行「\`ExpertPromptStore\`（**REV-16-2 新增**）」 |
| M-23 | `> **R13 装配说明（账户 / 会话）**：` | 在该段**之后**追加 §4.AC 的「**R16-2 装配说明（提示词 / 工具参数）**」段 |
| M-24 | `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-36，**36/36 全覆盖**；R13 同步计数）` | 替换为 `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-42，**42/42 全覆盖**；REV-16-2 同步计数）` |
| M-25 | 行首子串 `| IB-36 | **HTTPS 落点**（TLS 终止与证书策略） |` 所在整行（§9.1 末行） | 在其**之后**追加 §4.AD 的 IB-37 ~ IB-42 六行 |
| M-26 | `### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-18）` | 替换为 `### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-19）` |
| M-27 | 行首子串 `| NFR-18 | 可测试性（账户 / 会话离线替身齐备） |` 所在整行（§9.2 末行） | 在其**之后**追加 §4.AE 的 NFR-19 行 |
| M-28 | `## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）` | 在其**之前**插入 §4.AF 的 `### 9.9 REV-16-2 覆盖率再声明` 整节 |
| M-29 | `## 9. REQ → MOD 覆盖率矩阵` | 在其**之前**插入 §4.AG 的 §8 替身行（`InMemoryExpertPromptStore`） |
| M-30 | `| PyMuPDF 依赖及其「内部平台合规」注释 | MOD-IB-05 | **替换并撤除该口径**（ADR-06，REQ-NFR-IB-12 禁止） |`（§10 映射表末行） | 在其**之后**追加 §4.AH 的 FreeArk 严格对齐映射行与说明 |
| M-31 | 行首子串 `- **（R14）未改动他处**：` 所在整行（§11 末行） | 在其**之后**追加 §4.AI 的 R16-2 自检段 |

---

## §3 落盘指令 · `docs/tech_stack.md`

**NO_CHANGE — 不做任何落盘。**

理由：本增量新增物全部为 (a) 类型化契约 / 枚举 / frozen dataclass（纯 stdlib，零第三方依赖），(b) 纯函数（stdlib），(c) 现有库（Vue 3 / Element Plus / DRF）的既有用法扩展，(d) 新增配置键名（不含值）。**未引入任何新第三方库 / 二进制 / 服务**，故 §1 选型表、§2 许可台账、§4.5 验证清单、§5 风险表**均无新增条目**；`tech_stack.md` 保持 1.4.0 / REV-13 不变。该「无新依赖」事实在 `architecture_design.md` §10.3 的 R16-2 自检行（§4.L）中体现，**不必改动 tech_stack.md**。

---

## §4 新文本块（逐字，供 §1 / §2 引用）

> 阅读顺序：§4.A ~ §4.E 为 architecture_design.md 的大块（ADR 与复核表）；§4.F ~ §4.L 为 architecture_design.md 的行级追加；§4.M ~ §4.AI 为 module_design.md 的块与行。

### §4.A — architecture_design.md `revision_history` 新增条目

```xml
    <rev version="1.7.0" revision="REV-16-2" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-009" note="REV-16-2 提示词与工具可视化配置增强（GROUP_A REV-16-2 下游贯通：REQ-FUNC-IB-37~42 / REQ-NFR-IB-19 / C-IB-39 / C-IB-40 / OQ-IB-24）：① 对既有 ADR-15 作**正式修订**（新增修订子节 **ADR-15-R1**，ADR-15 正文与 Status **一字不动**；supersede vs amend 裁定见包 §5.1）；② 新增 **ADR-29**（提示词主 / 兜底分层与回退）、**ADR-30**（工具授权勾选 + 工具参数可配，不新增工具本体）、**ADR-31**（FreeArk 严格对齐含专家名 + 改名与聚合禁止标签处置）、**ADR-32**（配置生效口径 = 保存 + 服务重启重装配，不引运行期热重载 / 不重编译图）；ADR 数 28 → 32；③ 新增 §2.0.6 R16-2 影响复核表（既有 28 条 ADR 逐条复核，无一条跳过；ADR-15 判『经 ADR-15-R1 修订』、ADR-14 / ADR-16 判『复用其机制』；新增 4 条）；④ 新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339，定义于 MOD-IB-01 零依赖 Protocol 层）；⑤ 新增 **IFC-IB-337 ~ IFC-IB-354**（18 条类型化契约；IFC-IB-001~336 一字不动，IFC-IB-285 仍预留）；⑥ §1.3 追加 R16-2 注、§8 新增 [ARCH-ASSUMPTION-A10]、§9 新增 [TBD-T24]、§10.1 / §10.2 / §10.3 追加 R16-2 行；⑦ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑧ 计数同步：REQ-FUNC 36/36 → **42/42**（新增 IB-37~42）、NFR 18 → **19**（新增 NFR-19）。不变约束：模块数 26、端口数 15 → 16（纯追加）、IFC-IB-001~336 一字不动、§4.1 依赖边逐行不变、DAG 无环、fail-closed 纪律不削弱、**不重编译编排图**（C-IB-40）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
```

### §4.B — REV-16-2 修订摘要（置于 A-07 锚点之后）

```markdown
**（REV-16-2）提示词与工具可视化配置增强增量**（GROUP_A REV-16-2 下游贯通）：承接 GROUP_A REV-16-2（REQ-FUNC-IB-37~42 / REQ-NFR-IB-19 / C-IB-39 / C-IB-40 / OQ-IB-24）：① 对 **ADR-15** 作**正式修订**（子节 **ADR-15-R1**；定为「**amend（追加修订子节）**」而非 supersede，理由见 ADR-15-R1 与包 §5.1）：真源由「定义文档为**全部**持久化态唯一真源」修订为「**分域真源 + 装配期合并**」——定义文档仍为**结构 / 配置域**持久化态唯一真源，专家**主 / 兜底提示词**改由**独立 markdown 目录**承载（**提示词域**持久化态唯一真源）；派生视图**仍只读**。② 新增 **ADR-29 / ADR-30 / ADR-31 / ADR-32**，每条 >=2 方案含已评估未采纳项；**ADR 数 28 → 32**。③ 新增 **§2.0.6 R16-2 影响复核表**（既有 28 条 ADR 逐条复核，**无一条跳过**；**新增 4 条**）。④ 新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）与 **IFC-IB-337 ~ 354**（18 条类型化契约）。⑤ 落点并入既有模块（**零新增模块、零新增依赖边**）；§1.3 / §8 / §9 / §10.1 / §10.2 / §10.3 同步追加 R16-2 行。⑥ **计数同步**：REQ-FUNC 36/36 → **42/42**（新增 IB-37~42）、NFR 18 → **19**（新增 NFR-19）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**15 → 16，纯追加**）、`IFC-IB-001~336` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、`tech_stack.md` **未改**（无新第三方依赖）。
```

### §4.C — `### 2.0.6 R16-2 影响复核表`（置于 A-08 锚点之后）

```markdown
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
```

### §4.D — `ADR-15-R1`（置于 A-09 锚点之前）

```markdown
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
```

### §4.E — `ADR-29` / `ADR-30` / `ADR-31` / `ADR-32`（置于 A-10 锚点之前）

```markdown
### ADR-29 专家提示词的**主 / 兜底分层**与回退语义

- **Status**: Accepted（REV-16-2 新增）
- **Context**: REQ-FUNC-IB-37（提示词**不仅限于兜底提示词**；主 / 兜底**分层并存**，主提示词缺失时回退兜底 —— 用户裁决 2026-10-06，OQ-IB-17 / DR-19）；REQ-FUNC-IB-38（提示词可视化编辑与保存）；REQ-FUNC-IB-41（可经文件保存）；REQ-NFR-IB-19（一致性 / fail-safe）。既有落点：MOD-IB-16（专家派生注册表，IFC-IB-171~179）、MOD-IB-20（LLM 端点抽象）、MOD-IB-23（装配序列）。**约束**：不得使「主提示词缺失」导致**空白系统提示词**（须回退兜底）；兜底提示词**恒非空**（AC-IB-30-03 / 30-06 定性口径）。
- **Options**:
  - **Option A 单一提示词字段**（沿用既有 `fallback_prompt` 一个字段）：优—零改动。缺—**直接违反 REQ-FUNC-IB-37**（不得把「提示词」等同于「兜底提示词」）。**已评估未采纳**。
  - **Option B 主 / 兜底**两字段**分层并存 + 主缺失回退兜底** ← **选定**：`ExpertPromptBundle.main_prompt: str | None` 与 `fallback_prompt: str`（**非空**）；装配期合并时 `effective_prompt = main_prompt if main_prompt else fallback_prompt`，**永不空白**；`resolved_from` 记录取值来源（`main_file` / `fallback_file` / `definition_doc_fallback`）以支持可观测。优—完全满足 IB-37；分层语义清晰；回退为**纯函数**可离线单测。缺—须新增两字段与回退逻辑（成本已收敛为纯追加）。
  - **Option C 主提示词**替换**兜底**（二选一，不并存）**：优—语义最简。缺—**违反用户裁决「分层并存」**（OQ-IB-17）。**已评估未采纳**。
- **Decision**: **Option B**。`PromptLayer = Literal["main","fallback"]`（IFC-IB-337）；`ExpertPromptBundle`（IFC-IB-338）；回退纯函数 `load_prompt_bundle`（IFC-IB-343）；派生注册表扩展 `prompt_bundles()` / `main_prompts()`（IFC-IB-349）。**兜底恒非空**由装配期校验（IFC-IB-290 扩展）保证。
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
    | 5 | `fallback_prompt` | 三段兜底文本 | 三段兜底文本 | 逐字对齐 |
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
```

### §4.F — §1.3 可替换点表新增行（A-11 锚点之后）

```markdown
| 独立提示词目录来源（**REV-16-2 新增**） | `ExpertPromptStore`（IFC-IB-339） | `FsExpertPromptStore`（本地 markdown 目录；原子写 + 语义哈希乐观并发，同 IFC-IB-289 精神） | 新增适配器（如接 DB / 配置中心，上层零改动） | REQ-FUNC-IB-37 / IB-41；ADR-15-R1；REQ-NFR-IB-11 |
```

### §4.G — §1.3 追加注（A-12 锚点之前）

```markdown
**（REV-16-2）提示词载体与工具参数的可替换点显式化**：① **提示词载体**由「仅定义文档」**扩展**为「定义文档（结构 / 配置域）+ 独立 markdown 目录（提示词域）」，经**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）抽象 —— 载体从文件换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11）；真源边界与合并规则见 **ADR-15-R1**。② **工具参数**的可配化**不改变**工具本体登记入口（`register_tool`，IFC-IB-181 不变）；参数 schema 由 `ToolParamSpec`（IFC-IB-340）声明并在**装配期**校验。③ **两个持久化载体并存**（定义文档 + 提示词目录）**不构成重叠第二真源**（真源按域唯一）；**禁止**将任一域的内容重复写入另一域。
```

### §4.H — §8 新增假设行（A-13 锚点之后）

```markdown
| **ARCH-ASSUMPTION-A10**（REV-16-2 新增） | **独立提示词目录的物理布局与命名规则**：根路径经 `IB_EXPERT_PROMPT_DIR` 注入；每专家一子目录（目录名 = 专家 `name`），内含 `main.md`（主提示词，可缺）与 `fallback.md`（兜底提示词，**不得缺**）；**一项目一目录树** | REQ-FUNC-IB-41 只规定「可经文件保存 / 独立 markdown 目录」，**未规定**目录布局与文件命名；OQ-IB-18 只给出「独立 markdown 目录、不在定义文档内」 | 若改为 DB / 配置中心，**只替换 `ExpertPromptStore` 适配器**（IFC-IB-339），合并 / 校验 / 派生逻辑零改动（ADR-15-R1）；「一项目多目录树」若成立，须改的是**聚合根**定义，属需求侧变更 | **需 PM 确认**（目录布局与命名规则；未确认前以本假设为准，且**不影响架构与模块设计成立**） |
```

### §4.I — §9 新增 TBD 行（A-14 锚点之后）

```markdown
| **TBD-T24（REV-16-2 新增）** | **提示词目录装载 + 跨域合并 + 工具参数校验**对**装配期冷启动耗时**的增量，以及随专家数 / 提示词正文总字节数的增长曲线 | REQ-FUNC-IB-37 ~ IB-41；REQ-NFR-IB-19；ADR-15-R1 / ADR-29 / ADR-30 / ADR-32；[TBD-T19] 同源 | 与 [TBD-T19] **合并观测**；决定是否需对「提示词正文读取 + 语义哈希」做**合规缓存**（ADR-15-R1 Option B 之下，缓存**不得**成为读源，失效键 = 两域语义哈希）。**未经实测前不得给出耗时结论** |
```

### §4.J — §10.1 新增行（A-15 锚点之后）

```markdown
| **（REV-16-2）OQ-IB-24 的架构承接 + C-IB-39 / C-IB-40 落地** | ① **ADR-15 正式修订**（真源边界 / 优先级合并规则 / 派生视图是否仍只读）；② 配置**生效口径**与是否重编译图 | ① 真源修订为「**分域真源 + 装配期合并**」，**派生视图仍只读**（见 **ADR-15-R1**；**amend** 而非 supersede，理由见包 §5.1）；② 生效口径 = **保存 + 服务重启重装配**，**不重编译图**（见 **ADR-32**；C-IB-40 / OOS-16） | **OQ-IB-24 由本包正式承接并关闭**（架构侧已给出方案）；**不裁决**「主提示词 / 兜底提示词的具体文案」「工具参数的具体取值」等业务内容（由接入方 / 施工期确定，架构层不发明） |
```

### §4.K — §10.2 追加段（A-16 锚点之前）

```markdown
**（REV-16-2）许可合规**：本增量**未引入任何新第三方依赖** —— 新增物为类型化契约 / 枚举 / frozen dataclass（纯 stdlib）、纯函数（stdlib）、现有库（Vue 3 / Element Plus / DRF / 既有前端图库）的既有用法扩展，以及新增配置键名（不含值）。故 §10.2 台账**无新增条目**，`tech_stack.md` **保持 1.4.0 / REV-13 不变**（REQ-NFR-IB-12 结论不变）。
```

### §4.L — §10.3 新增自检行（A-17 锚点之后）

```markdown
- **（REV-16-2）提示词与工具可视化配置增强已贯通**：新增 **ADR-15-R1**（对 ADR-15 的正式修订，**amend**）、**ADR-29 / ADR-30 / ADR-31 / ADR-32**（每条含 Context（**REQ 引用**）/ Options（**>=2**）/ Decision / Status / Consequences）；新增 **§2.0.6 R16-2 影响复核表**（**既有 28 条 ADR 全部已复核**、新增 4 条、**无一条跳过**）；新增**第 16 个端口** `ExpertPromptStore`（IFC-IB-339）与 **IFC-IB-337 ~ 354**（18 条，见 `module_design.md` §2.2.6）；§1.3 追加 R16-2 注、§8 新增 [ARCH-ASSUMPTION-A10]、§9 新增 [TBD-T24]、§10.1 / §10.2 追加行。
- **（REV-16-2）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 15 → **16**（**纯追加**）、`IFC-IB-001 ~ 336` 一字不动（新增 **337 ~ 354**；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.6）；REQ→MOD 覆盖 **42/42 REQ-FUNC（由 36 同步）+ 19 NFR（由 18 同步）**。
- **（REV-16-2）时效与图纪律未削弱**：生效口径为「**保存 + 服务重启重装配**」（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载，**不重编译编排图**（REQ-FUNC-IB-26 ②）；「无需重启即生效」类断言**全部不在**验收范围。
- **（REV-16-2）真源与 fail-safe 为契约事实**：真源按域唯一（定义文档 = 结构 / 配置域；提示词目录 = 提示词域），**重叠第二真源被结构性排除**（ADR-15-R1）；`effective_prompt` **恒非空**（ADR-29）；保存失败 / 校验拒绝时**在用配置保持原状**（fail-safe，REQ-NFR-IB-19）；`ValidationReport` **不含** `force` / `ignore` / `warn_only`（类型层事实不变）。
- **（REV-16-2）凭据纪律**：全文**只登记键名**（`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED`）；提示词正文与定义文档**不回显任何凭据值**；令牌仅经 `Authorization` 头；`?token=` 纪律**扩展至全部新端点**（`/api/config/prompts*`）；**未写入任何口令 / 令牌 / 密钥字面量**。
- **（REV-16-2）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
```

### §4.M — module_design.md `revision_history` 新增条目（M-05 锚点之前）

```xml
    <rev no="REV-16-2" date="2026-10-06" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-009" basis="GROUP_A REV-16-2 下游贯通（提示词与工具可视化配置增强：REQ-FUNC-IB-37~42 / REQ-NFR-IB-19 / C-IB-39 / C-IB-40 / OQ-IB-24）">
      **不新增模块、不新增依赖边**：提示词分层 / 提示词目录 / 工具参数 / FreeArk 对齐的**类型化契约与第 16 个端口** `ExpertPromptStore`（IFC-IB-339）并入 **MOD-IB-01**（IFC-IB-337~342）；装载 / 跨域合并 / 保存 / 校验 / 派生 / 键名（IFC-IB-343~348）并入 **MOD-IB-02**；派生注册表扩展（IFC-IB-349）并入 **MOD-IB-16**；工具授权与参数绑定（IFC-IB-350）并入 **MOD-IB-17**；聚合禁止标签派生视图（IFC-IB-351）并入 **MOD-IB-22**；提示词端点族与装配序列（IFC-IB-352~353）并入 **MOD-IB-23**；前端提示词分层编辑器与工具参数表单（IFC-IB-354）并入 **MOD-IB-24**。新增 IFC 编号 **337~354**（18 条，全部类型化、frozen dataclass / Protocol / 纯 stdlib、零第三方依赖）；**IFC-IB-285 仍预留未分配**；既有重号 `IFC-IB-131` 登记不修。**端口 15 → 16**（纯追加）。既有 MOD-IB-01~26、`IFC-IB-001~336`、§4.1 依赖边清单与 DAG 拓扑**一字不动**（纯追加；零新增边的再声明见 §4.2.6）。**真源边界经 ADR-15-R1 修订**（定义文档 = 结构 / 配置域；独立 markdown 目录 = 提示词域；派生视图仍只读；合并键 = 专家 name）。**计数同步**：REQ-FUNC 36/36 → **42/42**（新增 IB-37~42，§9.1）、NFR 18 → **19**（新增 NFR-19，§9.2）。**生效口径 = 保存 + 服务重启重装配**（ADR-32；**不重编译图**）。增补位置：§1 REV-16-2 性质段与补充纪律段、§2.1 四行结构、§2.2 端口行与增记、§2.2.6 IFC 段号索引、§3 的 MOD-IB-01/02/16/17/22/23/24 增补、§4.2.6 无环性再声明、§5 装配表行与说明、§8 替身行、§9.1 六行 + §9.2 一行 + §9.9 覆盖率再声明、§10 FreeArk 映射行、§11 自检。**OQ-IB-24 由架构侧正式承接并关闭**（ADR-15-R1）。需求侧文档只读；未修改 FreeArk 任何文件；未写入任何口令 / 令牌 / 密钥字面量（只登记键名）。
    </rev>
```

### §4.N — module_design.md §1「REV-16-2 性质」段（M-07 锚点之后）

```markdown
**REV-16-2 性质**: 本修订为**追加式增量**（GROUP_A REV-16-2 下游贯通：提示词与工具可视化配置增强），**只追加、不改写**：**不新增模块、不新增依赖边**。提示词分层 / 提示词目录 / 工具参数 / FreeArk 对齐的契约与**第 16 个端口** `ExpertPromptStore`（`IFC-IB-337~342`）并入 **MOD-IB-01**；装载 / 跨域合并 / 保存 / 校验 / 派生 / 键名（`IFC-IB-343~348`）并入 **MOD-IB-02**；派生注册表扩展并入 **MOD-IB-16**（`IFC-IB-349`）；工具授权与参数绑定并入 **MOD-IB-17**（`IFC-IB-350`）；聚合禁止标签派生视图并入 **MOD-IB-22**（`IFC-IB-351`）；提示词端点族与装配序列并入 **MOD-IB-23**（`IFC-IB-352~353`）；前端提示词编辑器与工具参数表单并入 **MOD-IB-24**（`IFC-IB-354`）。新增 `IFC-IB-337 ~ 354`（**IFC-IB-285 仍预留未分配**）。既有 MOD-IB-01~26、`IFC-IB-001~336`、15 个既有端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（零新增边的再声明见 §4.2.6）。**真源边界经 ADR-15-R1 修订**：定义文档 = **结构 / 配置域**唯一真源；独立 markdown 目录 = **提示词域**唯一真源；**派生视图仍只读**；合并键 = 专家 `name`。**生效口径** = 保存 + 服务重启重装配（ADR-32）。
```

### §4.O — module_design.md §1「REV-16-2 补充纪律」段（M-09 锚点之后）

```markdown
**REV-16-2 补充纪律（两个持久化载体 ≠ 第二真源）**：本增量引入**第二个持久化载体**（独立提示词 markdown 目录），但**不构成第二真源** —— 真源**按域唯一**（结构 / 配置域 = 定义文档；提示词域 = 提示词目录），两域**内容不得重叠**（定义文档不得承载主提示词正文，提示词目录不得承载专家元数据）。**越域写入即视为违规**，由装配期校验拒绝（IFC-IB-345）。**编号即拓扑序的边界情形**在本轮再次适用：提示词 / 工具参数的装载与派生**必然被组合根 MOD-IB-23 依赖**，故**不得新开** `MOD-IB-27`（否则产生 `23 → 27` 边，破坏 `w(A) > w(B)`），只能并入既有模块（同 §1 R7 补充纪律）。
```

### §4.P — §2.1 结构定义追加 4 行（M-10 锚点之后）

```markdown
| `PromptLayer` / `ExpertPromptDocumentRef`（REV-16-2 新增，定义于 MOD-IB-01） | `PromptLayer` = `Literal["main","fallback"]`。`ExpertPromptDocumentRef`: `expert_name: str`；`layer: PromptLayer`；`rel_path: str`；`content_hash: str`；`exists: bool` |
| `ExpertPromptBundle` / `PromptDirectoryLayout`（REV-16-2 新增，定义于 MOD-IB-01） | `ExpertPromptBundle`: `expert_name: str`；`main_prompt: str \| None`（**可缺**）；`fallback_prompt: str`（**非空**）；`effective_prompt: str`（**恒非空**）；`resolved_from: Literal["main_file","fallback_file","definition_doc_fallback"]`。`PromptDirectoryLayout`: `root_key: str`；`file_pattern: str`；`naming_rule: str`（子目录名 = 专家 `name`，见 [ARCH-ASSUMPTION-A10]） |
| `ToolParamSpec` / `ToolParamValue`（REV-16-2 新增，定义于 MOD-IB-01；**加成式扩展** `ToolGrantSpec`（IFC-IB-287），其文本不改） | `ToolParamSpec`: `name: str`；`type: Literal["int","float","bool","str"]`；`default: str`；`minimum: float \| None`；`maximum: float \| None`；`choices: tuple[str, ...] \| None`。`ToolParamValue`: `name: str`；`value: str`。`ToolGrantSpec` **增列** `param_values: tuple[ToolParamValue, ...] = ()` |
| `FreeArkAlignedExpertSpec` / `AlignmentChecklist` / `DimensionCheck`（REV-16-2 新增，定义于 MOD-IB-01） | `FreeArkAlignedExpertSpec`: = `ExpertSpec` 的 7 字段 + `main_prompt: str \| None` + `exemplars: tuple[str, ...]`（共 **9 维**）+ `tool_names: tuple[str, ...]`（第 **10** 维，**工具名对齐**）。`DimensionCheck`: `dimension: str`；`base_value: str`；`freeark_value: str`；`aligned: bool`；`unalignable: bool`；`note: str`。`AlignmentChecklist`: `items: tuple[DimensionCheck, ...]`（**10 维**，其中工具参数为 `unalignable=True` 的显式排除项） |
| `PromptSaveResult` / `PromptNotFoundError` / `ToolParamValidationError`（REV-16-2 新增，定义于 MOD-IB-01） | `PromptSaveResult`: `saved: bool`；`ref: ExpertPromptDocumentRef`；`content_hash: str`；`errors: tuple[ValidationErrorItem, ...]`。`PromptNotFoundError` / `ToolParamValidationError` 继承 `IbError`（IFC-IB-012 层次） |
```

### §4.Q — §2.2 端口表新增行（M-11 锚点之后）

```markdown
| `ExpertPromptStore`（**REV-16-2 新增**） | 5 | IFC-IB-339（端口）+ IFC-IB-337~338（结构） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-02（装载·合并·保存·校验·派生） |
```

### §4.R — §2.2「REV-16-2 增记」段（M-12 锚点之前）

```markdown
**REV-16-2 增记（第 16 个端口）**：`ExpertPromptStore`（IFC-IB-339）为**第 16 个端口**（15 → 16，**纯追加**，5 方法：`load_bundle` / `save_layer` / `list_refs` / `delete_layer` / `layout`）。它与 `DefinitionDocumentStore`（IFC-IB-287）的区别是**工件不同**：后者管**结构 / 配置域**（专家元数据 / 路由 / 编排 / 工具授权）；前者管**提示词域**（主 / 兜底提示词 markdown）。**两域真源按域唯一、内容不得重叠**（ADR-15-R1）；所有需要「按专家取提示词 / 合并派生」的上层模块（MOD-IB-16 / 20 / 22）**不得**各自读目录或各自解析，一律由组合根在**装配期**经该端口取得并合并注入（同 `CollectionResolver` / `DefinitionDocumentStore` 的「唯一入口」精神）。**离线替身** `InMemoryExpertPromptStore`（IFC-IB-339 的测试实现，见 §8）。**提示词目录根路径经 `IB_EXPERT_PROMPT_DIR` 注入（只登记键名，不含值）。**
```

### §4.S — `### 2.2.6 REV-16-2 新增 IFC 段号索引`（M-13 锚点之前）

```markdown
### 2.2.6 REV-16-2 新增 IFC 段号索引（追加式编号；IFC-IB-001~336 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-337 ~ 338 | MOD-IB-01 | `PromptLayer` / `ExpertPromptDocumentRef`；`ExpertPromptBundle` / `PromptDirectoryLayout` | §3 MOD-IB-01（本件） |
| IFC-IB-339 | MOD-IB-01 | 端口 `ExpertPromptStore`（**第 16 个端口**，5 方法：`load_bundle` / `save_layer` / `list_refs` / `delete_layer` / `layout`） | §3 MOD-IB-01（本件） |
| IFC-IB-340 ~ 342 | MOD-IB-01 | `ToolParamSpec` / `ToolParamValue`（**加成式扩展** `ToolGrantSpec`，其文本不改）；`PromptSaveResult` / `PromptNotFoundError` / `ToolParamValidationError`；`FreeArkAlignedExpertSpec` / `AlignmentChecklist` / `DimensionCheck` | §3 MOD-IB-01（本件） |
| IFC-IB-343 ~ 348 | MOD-IB-02 | `load_prompt_bundle`（主缺失回退兜底）/ `save_prompt_layer`（原子写 + 乐观并发）/ `load_prompt_directory` + `validate_prompt_directory`（孤儿文件 / 命名不符 / 缺兜底）/ `validate_tool_params`（越界 / 类型 / 未知 / 未授权带参）/ `derive_prompt_layers`（跨域合并派生，只读）/ 键名登记 `IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED` | §3 MOD-IB-02（本件） |
| IFC-IB-349 | MOD-IB-16 | `prompt_bundles()` / `main_prompts()`（**加成式**；`IFC-IB-171~179` 一字不动） | §3 MOD-IB-16（本件） |
| IFC-IB-350 | MOD-IB-17 | `build_authorized_tools` / `validate_grants`（勾选 → 最小授权；工具参数绑定；**不新增工具本体**） | §3 MOD-IB-17（本件） |
| IFC-IB-351 | MOD-IB-22 | `forbidden_labels(cn_map) -> tuple[str, ...]`（**派生视图**；AC-IB-09-03；对齐 ADR-09） | §3 MOD-IB-22（本件） |
| IFC-IB-352 ~ 353 | MOD-IB-23 | `/api/config/prompts` 端点族（GET 列表 / GET 单层 / PUT 单层）；装配序列扩展与生效口径（重启后重装配） | §3 MOD-IB-23（本件） |
| IFC-IB-354 | MOD-IB-24 | 前端提示词分层编辑器 + 工具授权勾选 + 工具参数表单 + 「保存后重启生效」提示 + 未提交草稿标注 | §3 MOD-IB-24（本件） |

**REV-16-2 编号规范（强制，延续 R2 / R7 / R8 / R13 / R14）**：新增号只许**追加**（本轮取 **337 ~ 354**）；`IFC-IB-001 ~ 336` 的号 / 名 / 签名 / 字段集**一字不动**（其中 `IFC-IB-287` 的 `ToolGrantSpec` 仅被**加成式扩展**，其文本不改）；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。以上 18 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**；**不含任何口令 / 令牌 / 密钥字面量**（只登记键名 / 标签名）。
```

### §4.T — MOD-IB-01 增补条目（M-14 锚点之前）

```markdown
  - **IFC-IB-337（REV-16-2 新增）**: `PromptLayer` = `Literal["main","fallback"]`；`ExpertPromptDocumentRef`（`expert_name` / `layer` / `rel_path` / `content_hash` / `exists`）。**frozen dataclass / Literal，纯 stdlib，无实现体**。
  - **IFC-IB-338（REV-16-2 新增）**: `ExpertPromptBundle`（`expert_name` / `main_prompt: str | None` / `fallback_prompt: str`（**非空**）/ `effective_prompt: str`（**恒非空**）/ `resolved_from`）；`PromptDirectoryLayout`（`root_key` / `file_pattern` / `naming_rule`）。**分层并存、主缺失回退兜底**（ADR-29）。
  - **IFC-IB-339（REV-16-2 新增）**: 端口 `ExpertPromptStore`（`Protocol`，**5 方法**，定义于 MOD-IB-01 零依赖层；**第 16 个端口**）：`load_bundle(expert_name: str, *, doc_fallback: str) -> ExpertPromptBundle`；`save_layer(expert_name: str, layer: PromptLayer, content: str, *, expected_hash: str | None) -> PromptSaveResult`；`list_refs() -> tuple[ExpertPromptDocumentRef, ...]`；`delete_layer(expert_name: str, layer: PromptLayer) -> None`；`layout() -> PromptDirectoryLayout`。**不实现于本模块**（实现落在 MOD-IB-02 的生产 / 离线适配器）。
  - **IFC-IB-340（REV-16-2 新增）**: `ToolParamSpec`（`name` / `type: Literal["int","float","bool","str"]` / `default` / `minimum: float | None` / `maximum: float | None` / `choices: tuple[str, ...] | None`）与 `ToolParamValue`（`name` / `value: str`）。**加成式扩展** `ToolGrantSpec`（IFC-IB-287）：**增列** `param_values: tuple[ToolParamValue, ...] = ()`，**其既有文本一字不动**（沿用 IFC-IB-282 / 324 先例）。**不提供**新增工具本体的入口（ADR-30）。
  - **IFC-IB-341（REV-16-2 新增）**: `PromptSaveResult`（`saved: bool` / `ref` / `content_hash` / `errors: tuple[ValidationErrorItem, ...]`）；异常 `PromptNotFoundError` / `ToolParamValidationError`（继承 `IbError`，IFC-IB-012 层次）。**错误体只出 `path` / `code` / `message`，不回显任何凭据值**。
  - **IFC-IB-342（REV-16-2 新增）**: `FreeArkAlignedExpertSpec`（`ExpertSpec` 7 字段 + `main_prompt` + `exemplars` + `tool_names`，共 **10 维**）；`DimensionCheck`（`dimension` / `base_value` / `freeark_value` / `aligned` / `unalignable` / `note`）；`AlignmentChecklist`（`items: tuple[DimensionCheck, ...]`）。**工具参数为显式排除项**（`unalignable=True`，ADR-31）。**frozen dataclass，纯 stdlib，无实现体**。
```

### §4.U — MOD-IB-02 增补条目（M-15 锚点之前）

```markdown
  - **IFC-IB-343（REV-16-2 新增）**: `load_prompt_bundle(expert_name: str, *, refs: tuple[ExpertPromptDocumentRef, ...], doc_fallback: str) -> ExpertPromptBundle`（**纯函数 + 端口协作**；**主存在→用主；主缺失→回退兜底**；**兜底为空即非法**；`resolved_from` 记录来源）。**永不返回空白系统提示词**（ADR-29 / REQ-FUNC-IB-37）。
  - **IFC-IB-344（REV-16-2 新增）**: `save_prompt_layer(expert_name: str, layer: PromptLayer, content: str, *, expected_hash: str | None) -> PromptSaveResult`（**先写临时文件、再原子替换**；`expected_hash` 不匹配 → `conflict`，**拒绝覆盖**；沿用 IFC-IB-289 的乐观并发纪律）。**保存失败不破坏在用配置**（fail-safe，REQ-NFR-IB-19）。
  - **IFC-IB-345（REV-16-2 新增）**: `load_prompt_directory() -> tuple[ExpertPromptDocumentRef, ...]` + `validate_prompt_directory(refs, *, doc) -> tuple[ValidationErrorItem, ...]`（**纯函数**：**孤儿提示词文件**（目录有、文档未登记）/ **命名不符**（子目录名 != 专家 name）/ **缺兜底**（`fallback.md` 缺失且文档 `fallback_prompt` 为空）逐条检出）。错误体只出 `path` / `code` / `message`。
  - **IFC-IB-346（REV-16-2 新增）**: `validate_tool_params(grants: tuple[ToolGrantSpec, ...], *, specs: tuple[ToolParamSpec, ...]) -> tuple[ValidationErrorItem, ...]`（**纯函数**：参数**越界**（< minimum / > maximum）/ **类型不符**（不满足 `type`）/ **未知参数**（spec 未声明）/ **choices 不匹配** / **未授权工具带参**（工具不在该专家 `tool_names` 内却给出参数）→ 一律检出）。**不提供**新增工具本体的校验路径。
  - **IFC-IB-347（REV-16-2 新增）**: `derive_prompt_layers(doc: DefinitionDocument, prompt_refs: tuple[ExpertPromptDocumentRef, ...]) -> DerivedView`（**纯函数**；**跨域合并**：定义文档专家 `name` ↔ 提示词目录子目录**按 name join**；产出 prompt bundle 并并入派生注册表）。**不落盘、不可反写任一真源**（ADR-15-R1）。**新增合并维，不新增参数到既有 IFC-IB-291**（IFC-IB-291 签名文本不变，本函数为其合并扩展的**独立**入口）。
  - **IFC-IB-348（REV-16-2 新增）**: 配置**键名登记**（**仅登记键名，不含值**）：`IB_EXPERT_PROMPT_DIR`（独立提示词目录根路径）、`IB_EXPERT_PROMPT_ENABLED`（提示词域开关）。
```

### §4.V — MOD-IB-16 增补条目（M-16 锚点之后）

```markdown
  - **IFC-IB-349（REV-16-2 新增）**: `prompt_bundles() -> dict[str, ExpertPromptBundle]`（按专家 `name` 取**主 / 兜底 / 生效提示词**）；`main_prompts() -> dict[str, str | None]`（仅主提示词，可缺）。**加成式扩展**：`IFC-IB-171~179` 的号 / 名 / 签名**一字不动**；其中 `IFC-IB-175 \`fallback_prompts()\`` 的语义**不变** —— 其仍返回**兜底层**（`dict[str, str]`，**非空**）。本模块持有的是**由两域在装配期合并派生并注入**的只读注册表（ADR-15-R1）。
```

### §4.W — MOD-IB-17 增补条目（M-17 锚点之后）

```markdown
  - **IFC-IB-350（REV-16-2 新增）**: `build_authorized_tools(grants: tuple[ToolGrantSpec, ...], *, registry, specs: tuple[ToolParamSpec, ...]) -> list[BoundTool]`（按**授权勾选** `tool_names` 绑定；工具参数经 `param_values` 注入闭包；**最小授权不变**）；`validate_grants(grants, *, registry) -> tuple[ValidationErrorItem, ...]`（引用不存在的工具 / 未登记工具带参 → 检出）。**工具本体仍只经 `register_tool`（IFC-IB-181，签名不变）登记**；本契约**不提供**新增 / 自定义工具本体的路径（ADR-30 / OQ-IB-19）。
```

### §4.X — MOD-IB-22 增补条目（M-18 锚点之前）

```markdown
  - **IFC-IB-351（REV-16-2 新增）**: `forbidden_labels(cn_map: dict[str, str]) -> tuple[str, ...]`（**纯函数 / 派生视图**：由**活体专家注册表**的 `cn_map()`（IFC-IB-174）派生「聚合阶段禁止出现的专家中文标签」全集；替代硬编码清单，使骨架**不承载业务中文名**，对齐 ADR-09）。用途：AC-IB-09-03「不得暴露内部分工」。**目标形态**；重构完成前，`AGGREGATION_FORBIDDEN_LABELS` 的硬编码值须为「旧 ∪ 新」并集（过渡态，GROUP_C 施工要点；ADR-31 Decision 第 4 条）。
```

### §4.Y — MOD-IB-23 增补条目（M-19 锚点之前）

```markdown
- **REV-16-2 新增端点与契约（提示词；全程仅 `Authorization` 头，**不接受 `?token=`**）**:
  - IFC-IB-352: `GET /api/config/prompts` → `200 {experts: [{name, cn_label, layers: {main: {exists, content_hash}, fallback: {exists, content_hash}}}]}`（**元数据与哈希，不含正文**；`403` 归属断言失败；`503` **fail-closed**：目录不可读即明确报错，**不返回空集合**）；`GET /api/config/prompts/{expert}/{layer}` → `200 {content, content_hash}` | `404`（不存在）| `403` | `503`；`PUT /api/config/prompts/{expert}/{layer}`（`{content, expected_hash?}`）→ `200 PromptSaveResult` | `400`（校验不通过：逐条 `path` / `code` / `message`）| `403` | `409`（乐观并发冲突，含可读回执，**不静默覆盖**）| `503`（**fail-closed**）。**挂载于既有 `MOD-IB-23`，不新增模块**；**保存仅原子落盘，不触发运行期重建**（ADR-32）。
  - IFC-IB-353: **装配序列扩展（显式化，任一步失败即启动失败）**：`装载定义文档（IFC-IB-288）→ 装载独立提示词目录（IFC-IB-345）→ 跨域合并 + 完备性校验（IFC-IB-290 扩展 + 345 + 346）→ 准入闸门（IFC-IB-293）→ 派生注册表 / 图配置（IFC-IB-291 扩展，含 347 + 349）→ 构造并注入 → 图编译一次常驻`。**生效口径 = 服务重启后重新装配**（ADR-32 / C-IB-40）；**不提供**任何运行期热重载 / 热重编译入口；**不重编译编排图**（REQ-FUNC-IB-26 ②）。工具参数装配经 `build_authorized_tools`（IFC-IB-350）。**鉴权与凭据纪律（强制）**：沿用 IFC-IB-247 口径，**仅允许 `Authorization` 头 / 中间件鉴权**；三个新端点**不接受** `?token=`；错误体**不回显任何凭据值**（REQ-NFR-IB-19）。
```

### §4.Z — MOD-IB-24 增补条目（M-20 锚点之后）

```markdown
- **REV-16-2 提示词与工具配置页约束（IFC-IB-354）**:
  - **提示词分层编辑器**：为每个专家提供**主提示词**与**兜底提示词**两个独立文本域（`PromptLayer`）；**主缺失时的「回退兜底」须可见**（显示 `resolved_from`，如「主提示词缺失，当前生效 = 兜底」），**不得**呈现为空白。
  - **工具授权勾选 + 参数表单**：工具列表为**勾选**形态（映射 `tool_names`）；每个已勾工具按其 `ToolParamSpec` 生成参数控件（int / float 用数值输入并按 `minimum` / `maximum` 约束，bool 用开关，str / 枚举用下拉）；**前端预校验仅为体验优化**，**服务端校验器为唯一裁决者**（同 ADR-16 精神）。
  - **视图侧零持久化**（沿用 ADR-14）：**不得**以 `localStorage` / `IndexedDB` / 独立后端表作为真源；未提交草稿须**显式标注「未提交（可丢弃）」**且**不得**作为下次载入源。
  - **生效口径显式提示（强制）**：保存成功后**必须**提示「**保存成功；重启 `ib-web` / `ib-worker` 后生效**」，**不得**呈现为「已即时生效」（ADR-32 / C-IB-40）；重启由**用户手工执行**（C-IB-38）。
  - **以文档 / 目录为准刷新**：服务端返回的提示词 / 参数更新后，界面**必须以服务端为准**刷新，**不得**用陈旧视图反向覆盖；`409` 冲突须给出可读回执。
  - **凭据不回显**：配置项只显示**键名**，不显示任何值 / 掩码 / 前缀（沿用 AC-IB-17-05 口径）。
  - **离线与数据本地化**：不引入任何运行期 CDN 依赖或外发请求（REQ-NFR-IB-08 同精神）。
```

### §4.AA — `### 4.2.6 REV-16-2 无环性再声明`（M-21 锚点之前）

```markdown
### 4.2.6 REV-16-2 无环性再声明（零新增依赖边）

**结论：DAG 拓扑在 REV-16-2 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：REV-16-2 新增全部落在 **MOD-IB-01 / 02 / 16 / 17 / 22 / 23 / 24** 内部（提示词 / 工具参数的类型化契约与第 16 个端口 / 装载·合并·保存·校验·派生 / 派生注册表扩展 / 工具参数绑定 / 聚合禁止标签派生 / 端点与装配序列 / 前端编辑器），**§4.1 依赖边清单逐行未改**；`w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **不新增模块**：提示词与工具参数的装载 / 派生**必然被组合根 `MOD-IB-23` 依赖**，若新开模块只能取 **>=27** 编号 → 产生 `23 → 27` 边，**违反 `w(A) > w(B)`**；故并入既有模块（§4.2.2 边界纪律继续适用；ADR-15-R1 Option D 同源论证）。
- **既有边被复用而非新增**：`ExpertPromptStore` 端口在 **MOD-IB-01**（L0）；其适配器在 **MOD-IB-02**（既有边 `02 → 01`）；合并派生在 **MOD-IB-16**（既有边 `16 → 01`）；工具参数绑定在 **MOD-IB-17**（既有边 `17 → {01,15,16}`）；聚合禁止标签派生在 **MOD-IB-22**（既有边 `22 → 01`）；端点在 **MOD-IB-23**（既有边 `23 → 01/02/…/22`）；前端 **MOD-IB-24 → 23**（既有）。
- **单一入口纪律未被绕开**：提示词 / 派生的唯一入口是组合根经 `ExpertPromptStore`（IFC-IB-339）取得并合并注入；工具本体仍只经 `register_tool`（IFC-IB-181）；前端仍只经 HTTP 契约（MOD-IB-24 → MOD-IB-23）取数，**不新增绕过路径**。
- 「编号即拓扑序」继续适用于 GROUP_C；REV-16-2 的**边界纪律同 §4.2.2 末句**。
```

### §4.AB — §5 装配表新增行（M-22 锚点之后）

```markdown
| `ExpertPromptStore`（**REV-16-2 新增**） | `FsExpertPromptStore`（独立 markdown 目录；原子写 + 语义哈希乐观并发，与 `DefinitionDocumentStore` 同纪律） | `InMemoryExpertPromptStore`（内存字典 + 同一合并 / 校验器） | `IB_EXPERT_PROMPT_DIR`（路径）；`IB_EXPERT_PROMPT_ENABLED=true\|false` |
```

### §4.AC — §5「R16-2 装配说明」段（M-23 锚点之后）

```markdown
> **R16-2 装配说明（提示词 / 工具参数）**：① 独立提示词目录的**装载 → 跨域合并 → 完备性校验 → 派生 → 注入**序列见 §3 MOD-IB-23（IFC-IB-353）；② 一键离线下 `ExpertPromptStore` 取「离线/测试」列（`InMemoryExpertPromptStore`），**合并与校验器照常执行**（离线亦可验证 REQ-NFR-IB-19）；③ 新增键 `IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED` **只登记键名**，其取值（含路径中任何敏感信息）一律不进文档、不进日志；④ **生效口径**：保存仅落盘，**重启后重新装配方生效**（ADR-32 / C-IB-40）；**不提供**运行期热重载 / 热重编译入口；⑤ **两个持久化载体并存不等于第二真源**（真源按域唯一，ADR-15-R1）；**禁止**把提示词正文写入定义文档，或把专家元数据写入提示词目录。
```

### §4.AD — §9.1 新增六行（M-25 锚点之后）

```markdown
| IB-37 | 提示词分层语义（主 + 兜底；**不仅限于兜底**） | **MOD-IB-01, MOD-IB-16** / 02, 24（主缺失回退兜底；兜底恒非空） |
| IB-38 | 提示词可视化编辑与保存（落盘为独立 markdown 目录） | **MOD-IB-24, MOD-IB-23** / 02, 01 |
| IB-39 | 工具授权可视化配置与保存（**勾选 + 参数可配**；不新增工具本体） | **MOD-IB-17, MOD-IB-24** / 02, 01, 23 |
| IB-40 | 配置**保存并经服务重启后生效**（不热重载 / 不重编译图） | **MOD-IB-23** / 02, 22（ADR-32；C-IB-40） |
| IB-41 | 专家定义 / 提示词**可经文件保存**（独立 markdown 目录） | **MOD-IB-02, MOD-IB-01** / 23, 16 |
| IB-42 | 示例项目专家定义与 FreeArk **100% 对齐**（含专家名；工具参数排除） | **MOD-IB-01, MOD-IB-16** / 02, 24（ADR-31） |
```

### §4.AE — §9.2 新增行（M-27 锚点之后）

```markdown
| NFR-19 | 可视化配置的一致性 / 可观测 / **fail-safe**（提示词与工具授权） | **MOD-IB-02, MOD-IB-23** / 01, 16, 24 |
```

### §4.AF — `### 9.9 REV-16-2 覆盖率再声明`（M-28 锚点之前）

```markdown
### 9.9 REV-16-2 覆盖率再声明（提示词与工具可视化配置增强增量）

**结论：新增 REQ-FUNC 42/42 + REQ-NFR 19 全覆盖，无缺口。**

- **覆盖同步**：§9.1 由 36/36 同步为 **42/42 REQ-FUNC**（新增 IB-37 ~ IB-42，各有主模块），§9.2 NFR 由 18 同步为 **19**（新增 NFR-19）；§9.3 / §9.4 / §9.5 / §9.6 / §9.7 / §9.8 结论句以括注保留历史基线。
- **追踪落点**：IFC-IB-337 ~ 342 / 349（提示词分层与对齐）→ REQ-FUNC-IB-37 / IB-42、REQ-NFR-IB-19；IFC-IB-343 ~ 347（装载 / 合并 / 保存 / 校验 / 派生）→ REQ-FUNC-IB-38 / IB-41、REQ-NFR-IB-19；IFC-IB-340 / 346 / 350（工具参数）→ REQ-FUNC-IB-39；IFC-IB-352 / 353（端点与生效）→ REQ-FUNC-IB-40、C-IB-40；IFC-IB-354（前端）→ REQ-FUNC-IB-37 / IB-38 / IB-39 / IB-40。
- **架构侧对应**：`architecture_design.md` 1.7.0（REV-16-2）的 **ADR-15-R1**、**ADR-29 ~ ADR-32**、**§2.0.6 R16-2 影响复核表**、§1.3 R16-2 注、[ARCH-ASSUMPTION-A10]、[TBD-T24]、§10.1 / §10.2 / §10.3 R16-2 行；`tech_stack.md` **NO_CHANGE**（无新第三方依赖）。
- **OQ 处置**：**OQ-IB-24**（ADR-15 正式修订）由本包**正式承接并关闭**（ADR-15-R1）；**不裁决**主 / 兜底提示词文案、工具参数具体取值等业务内容（架构层不发明）。
- **模块与依赖不变**：模块数仍 **26**、端口数 15 → **16**（纯追加）、**§4.1 依赖边逐行未改**（§4.2.6）。
```

### §4.AG — §8 替身清单新增行（M-29 锚点之前）

```markdown
| `ExpertPromptStore`（REV-16-2 新增） | `FsExpertPromptStore`（独立 markdown 目录，生产 / 离线同一合并·校验器） | `InMemoryExpertPromptStore`（内存字典） | REQ-NFR-IB-19；离线可验证：主缺失回退兜底、孤儿文件拒绝、缺兜底拒绝、参数越界拒绝 |
```

### §4.AH — §10 FreeArk 映射表新增行与说明（M-30 锚点之后）

```markdown
| `langgraph_chat/experts.py` 的 `EXPERT_SPECS`（**专家名与 `cn_label`**） | MOD-IB-16 / MOD-IB-01 | **REV-16-2 严格对齐（含专家名）**：`demo` 示例项目专家集按 **10 维**逐字段对齐（ADR-31 / REQ-FUNC-IB-42）；**FreeArk 全程只读**（C-IB-01）。**工具参数为唯一不可对齐维**（FreeArk 无 per-expert 参数真源），显式排除。 |
| `agents/<name>/SYSTEM_PROMPT.langgraph.md`（**主提示词**） | MOD-IB-01 / MOD-IB-02（`ExpertPromptStore`） | **REV-16-2 新增能力**：主提示词落于**独立 markdown 目录**（ADR-29 / ADR-15-R1）；**全文不复制进本仓设计文档**，仅施工期自只读源导入。 |

**REV-16-2 说明（FreeArk 参照的可复用边界）**：REV-16-2 对 FreeArk 的利用方式仅为「**示例项目的专家定义逐字段对齐 + 主提示词形态参考**」，**不引入**其业务逻辑 / 业务工具本体 / 业务话术（OOS-04 / OOS-11）。**改名会把 FreeArk 业务中文名与业务工具名带入示例项目**，与「业务不入通用基座」存在张力（已登记为需 PM / 用户注意项，见 `rev16_2_architecture_apply_package.md` §7）。**FreeArk 仓库任何文件未被修改。**
```

### §4.AI — §11 自检声明新增段（M-31 锚点之后）

```markdown
    - **REV-16-2 自检（提示词与工具可视化配置增强增量，GROUP_A REV-16-2 下游贯通）**：
      - **覆盖同步**：§9.1 由 36/36 同步为 **42/42 REQ-FUNC**（新增 IB-37 ~ IB-42，各有主模块），§9.2 NFR 由 18 同步为 **19**（新增 NFR-19）；**§9.9 给出 R16-2 再声明**。
      - **真源修订已承接**：新增 **ADR-15-R1**（**amend**，对 ADR-15 的正式修订；ADR-15 正文 / Status 一字不动）；真源边界修订为「**分域真源 + 装配期合并**」（定义文档 = 结构 / 配置域；独立 markdown 目录 = 提示词域；**派生视图仍只读**；合并键 = 专家 `name`）。**OQ-IB-24 关闭。**
      - **零新增模块 / 零新增依赖边**：模块数仍 **26**；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 16 / 17 / 22 / 23 / 24（§1 REV-16-2 补充纪律段给出「为何不新增 MOD-IB-27」的编号论证；§4.2.6 给出无环性再声明）。
      - **类型化未降级 / 编号纪律未破**：新增 `IFC-IB-337 ~ 354`（18 条）全部为 `name: type` + 可空性的**类型化契约**，均为 **frozen dataclass / Protocol / 纯 stdlib，零第三方依赖**；`IFC-IB-001 ~ 336` 的号 / 名 / 签名 / 字段集**一字不动**（其中 `IFC-IB-287` 的 `ToolGrantSpec` 仅被**加成式扩展**，其文本不改）；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。**端口 15 → 16**（纯追加）。
      - **时效 / 图纪律为契约事实**：生效口径 = **保存 + 服务重启重装配**（ADR-32 / C-IB-40；`IFC-IB-353`）；**不提供**运行期热重载 / 热重编译入口；**不重编译编排图**（REQ-FUNC-IB-26 ②）；`effective_prompt` **恒非空**（ADR-29）；保存失败 / 校验拒绝时**在用配置保持原状**（fail-safe，REQ-NFR-IB-19）。
      - **OQ 未越权**：**OQ-IB-24 关闭**（架构侧已给方案）；**不裁决**主 / 兜底提示词文案与工具参数具体取值等业务内容；**不新增 REQ**。
      - **凭据纪律**：全文只登记**键名**（`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED`）与**标签名**；令牌仅经 `Authorization` 头；`?token=` 纪律扩展至全部新端点；**未写入任何口令 / 令牌 / 密钥字面量**。
      - **边界合规**：REV-16-2 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**（全程只读）；需求侧文档只读未改；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
```

---

## §5 强制证据与裁定

### 5.1 ADR-15 修订：**supersede 还是 amend**

**裁定：采用 `amend`（追加修订子节 `ADR-15-R1`），不采用 `supersede`（新立单独取代性 ADR）。**

| 判据 | supersede（新 ADR-x 取代 ADR-15） | amend（追加 ADR-15-R1 子节） |
|------|-----------------------------------|------------------------------|
| 与本仓 append-only 纪律 | 需把 ADR-15 的 Status 改为 Superseded（**改动既有正文**） | **不改** ADR-15 任何字段，仅**追加**子节 |
| 先例 | 无先例 | **有先例**：`ADR-11-R1`、`ADR-13-R1`（对既有 ADR 结论的修订均以 `-RN` 子节承载） |
| 变更范围 | 真源边界**部分**修订（结构域不变，提示词域新增载体） | 同上；`-R1` 精确表达「同一条决策的口径修订」 |
| 下游追溯 | 需维护「ADR-15 作废 / ADR-x 生效」的映射 | 追溯链连续（ADR-15 → ADR-15-R1），编号账本最简 |

**理由**：本修订**不是**推翻「定义文档为真源」这一决策整体（结构 / 配置域**不变**），而是**收窄其适用范围**并**新增一个按域划分的载体**。这是「同一决策的口径修订」，与 ADR-11-R1 / ADR-13-R1 同性质。**用户裁决（OQ-IB-18）「不保持『定义文档是唯一真源』」在语义上等于对 ADR-15 的收窄**，而非对「定义文档作为真源」的否定；故 `amend` 精确刻画之。**`ADR-15-R1` 文本见 §4.D。** §2.0.5 / §2.0.6 复核表中 ADR-15 的结论由「不受影响」改为「**经 ADR-15-R1 修订**」。

### 5.2 对 5 条 APPROVED REQ 的处置结论

**总原则：不重写任何需求正文。** 架构侧只**收窄 ADR-15 的口径**并**登记受影响条目**；需求侧正文（含「定义文档为单一真源」措辞）**保持一字不动**（其口径修订已由需求侧自身的 **C-IB-39 / OQ-IB-24** 声明「已触发修订」，与架构侧 **ADR-15-R1** 一一对应）。

| REQ | 正文断言 | 架构侧处置 | 是否需回 GROUP_A |
|-----|----------|------------|------------------|
| **REQ-FUNC-IB-01**（通用化，主 MOD-IB-02） | 配置可外置、新项目零改动 | 覆盖归属**不变**；配置来源由「定义文档」**扩展**为「定义文档 + 独立提示词目录」，仍经端口抽象（REQ-NFR-IB-11 不破） | **否**（口径由 ADR-15-R1 承接） |
| **REQ-FUNC-IB-02**（专家可配置及其派生视图，主 MOD-IB-16） | 专家定义可配置 | 专家**元数据**仍源自定义文档（结构域）；提示词分层为**追加派生维**（MOD-IB-16 增 `prompt_bundles()`） | **否** |
| **REQ-FUNC-IB-25**（可视化配置界面；**无第二真源**，主 MOD-IB-24） | 「无第二真源」 | 架构侧口径 = 「第二真源」指**同域重叠**真源；**分域真源（结构域 vs 提示词域）不构成第二真源**（ADR-15-R1）。**该条正文措辞最接近冲突** | **条件性**：若 PM / 用户认为 REQ-FUNC-IB-25 正文必须**字面改写**为「无重叠的第二真源 / 分域真源」，则**须回 GROUP_A 立项**（架构层**不得**改写需求正文）。在获得 GROUP_A 裁决前，本包**不阻塞**、登记为注意项（见 §7） |
| **REQ-FUNC-IB-26**（可编辑范围白名单；不含运行期改图，主 MOD-IB-22/24） | 白名单制 | 可编辑白名单**扩展**为「定义文档白名单字段 + 提示词域文件」；**不含运行期改图**（不变） | **否** |
| **REQ-FUNC-IB-27**（装配期完备性校验 fail-fast，主 MOD-IB-23/02） | 校验 + 无强制继续开关 | 校验器**扩展**为跨两域合并后校验（孤儿文件 / 缺兜底 / 参数越界）；`ValidationReport` 仍不含 `force` / `ignore` / `warn_only`（**类型层事实不变**） | **否** |

**结论**：**5 条中 4 条（IB-01 / IB-02 / IB-26 / IB-27）无需回 GROUP_A**，仅 IB-25 为**条件性**（取决于 PM / 用户是否要求字面改写其「无第二真源」措辞）。**架构侧不自行改写任何 REQ 正文。**

### 5.3 `AGGREGATION_FORBIDDEN_LABELS` 的语义影响与处置

**现状**（只读核对）：`src/ib/orchestration/__init__.py` 的 `AGGREGATION_FORBIDDEN_LABELS` = `("路由到","专家","expert","router","聚合","agent","系统管家","巡检诊断","知识库问答")`。**语义作用** = AC-IB-09-03「聚合阶段**不得暴露内部分工**」（禁止把专家中文名等内部标签泄漏到最终答复）。

**改名带来的语义影响**：
1. `知识库问答` 改名后**变为陈旧**（不再是任何专家的 `cn_label`）→ 旧名单**漏**新名 `三恒知识`。
2. `系统管家` 当前已在名单内，但改名后**将成为** `freeark-expert`（原 `data-expert`）的**合法 `cn_label`** → 该条目**从「禁止」变为「必须保留」（仍须禁止其出现在聚合答复中）**，语义需重新确认。
3. 名单**缺失** `数据管家`（现 `data-expert` 的 `cn_label`）→ 既有名单本就不完整。

**处置（ADR-31 Decision 第 3 / 4 条）**：
- **目标形态**：名单改为**由活体专家注册表的 `cn_map()`（IFC-IB-174）派生的只读视图** `forbidden_labels(cn_map)`（**IFC-IB-351**，落点 MOD-IB-22）。这使「骨架不见业务语义」（ADR-09）真正成立 —— 当前把业务中文名硬编码在骨架里，**本身即是 ADR-09 的既有债**。
- **过渡措施（GROUP_C 施工要点，本包只登记；本阶段不改 `src/`）**：重构完成前，硬编码值**改为「旧 ∪ 新」并集** = `系统管家` / `巡检诊断` / `知识库问答` / `数据管家` / `三恒知识`（外加既有通用词），确保 AC-IB-09-03 **不回退**。**禁止只换名**（只删旧名或只加新名都会造成漏网或误伤）。
- **本阶段边界**：因任务约束「**禁止改动 `src/`**」，上述 `src/` 改动**不在本包内执行**，仅作为**设计裁定 + 施工待办**落盘于 **ADR-31**。

### 5.4 FreeArk 严格对齐证据（10 维）

见 **ADR-31 Option B 的 10 维比对表**（§4.E）。**权威真源（只读）**：`experts.py`（`EXPERT_SPECS`）、`agents/<name>/SYSTEM_PROMPT.langgraph.md`、`semantic_router.py`（exemplars）、`fa_tools.py` `TOOLS_BY_EXPERT`、`orchestrator.py` `DELEGATION_TOOLS_BY_EXPERT`。**改名映射**：`data-expert → freeark-expert`（`数据管家 → 系统管家`）、`inspection-expert`（不变）、`knowledge-expert → sanheng-knowledge`（`知识库问答 → 三恒知识`）。**唯一不可对齐维 = 工具参数**（FreeArk 无 per-expert 参数真源）。**renames 命中清单（约 41 处）以 `docs/rev16_2_ruling_apply_package.md` §3 为准**；落盘前 PM 应重新 Grep 复核（只读），确认无遗漏。

---

## §6 落盘后自检（PM 应用本包后逐项核对）

- [ ] `architecture_design.md`：header 版本 / 修订 / invocation 已改（A-01~A-03），inputs 已同步（A-04），revision_history 新增 REV-16-2（A-05），版本行（A-06）、修订摘要（A-07）、§2.0.6（A-08）、ADR-15-R1（A-09）、ADR-29~32（A-10）、§1.3 行与注（A-11 / A-12）、§8 A10（A-13）、§9 T24（A-14）、§10.1 / §10.2 / §10.3（A-15 / A-16 / A-17）均已落。
- [ ] `module_design.md`：header（M-01~M-04）、revision_history（M-05）、版本行（M-06）、§1 性质段与补充纪律（M-07~M-09）、§2.1 结构（M-10）、§2.2 端口行与增记（M-11 / M-12）、§2.2.6（M-13）、§3 七模块增补（M-14~M-20）、§4.2.6（M-21）、§5（M-22 / M-23）、§9.1 / §9.2 头与行（M-24~M-27）、§9.9（M-28）、§8（M-29）、§10（M-30）、§11（M-31）均已落。
- [ ] `tech_stack.md`：**未改动**（NO_CHANGE）。
- [ ] **编号纪律**：新增 ADR 从 29 起；新增 IFC 从 337 起（至 354，共 18）；端口 15 → 16；**模块仍 26**；`IFC-IB-001~336` 一字未动；`IFC-IB-285` 仍预留；`IFC-IB-131` 登记不修。
- [ ] **无循环依赖**：§4.1 依赖边逐行未改（零新增边）；§4.2.6 已再声明。
- [ ] **每条 ADR 五节齐全**（Context 含 REQ 引用 / Options >=2 / Decision / Status / Consequences）；**ADR-15 正文未改**。
- [ ] **无代码 / 无凭据**：三份文档**不含实现代码**；**未写入任何口令 / 令牌 / 密钥字面量**。
- [ ] **未越界**：未改 `src/`；未改 FreeArk；未改需求侧文档；未整文件重写三份设计文档。
- [ ] **落盘前 Grep 复核**：改名命中清单（约 41 处）与 `AGGREGATION_FORBIDDEN_LABELS`（`src/ib/orchestration/__init__.py`）现状以只读 Grep 复核（本包 §5.3 / §5.4）。

---

## §7 开放项 / 需 PM 与用户注意

| # | 事项 | 类型 | 建议处置 |
|---|------|------|----------|
| P-1 | **REQ-FUNC-IB-25 正文含「无第二真源」** —— 架构侧按「同域重叠」解释为不冲突（分域真源）。若 PM / 用户认为须**字面改写**其正文，则须**回 GROUP_A 立项**（架构层不改需求正文） | 需求侧口径 | 请 PM 裁决：按架构解释（**不阻塞，推荐**）或回 GROUP_A 立项 |
| P-2 | **改名把 FreeArk 业务中文名（`系统管家` / `三恒知识`）与业务工具名（ENERGY / PERSONA / INSPECTION / SANHENG）带入 `demo` 示例项目**，与 **OOS-04 / OOS-11**（FreeArk 业务不入通用基座）**存在张力** | 需求 / 基座边界 | 请 PM / 用户确认：示例项目对齐是否**仅限定义元数据**而不含业务工具本体语义（承接 `rev16_2_ruling_apply_package.md` §4 冲突项） |
| P-3 | **`AGGREGATION_FORBIDDEN_LABELS` 过渡态须双名并存**，重构前若**只换名**会导致 AC-IB-09-03 回退 | 施工纪律 | 登记为 GROUP_C 施工要点（本包 ADR-31 / §5.3）；**本阶段不改 `src/`** |
| P-4 | **独立提示词目录的物理布局与命名规则**（子目录名 = 专家 `name`；`main.md` / `fallback.md`）**无需求条文直接规定**，本包以 **[ARCH-ASSUMPTION-A10]** 默认 | 架构假设 | 请 PM 确认（载体与命名口径）；**不影响架构与模块设计成立** |
| P-5 | **本包引用的 `rev13` / `rev14` 架构侧落盘包在磁盘上不存在**（`module_design.md` §2.2 R13 注释引用了 `docs/rev13_auth_ui_architecture_apply_package.md`，该文件缺失） | 追溯 | 请 PM 知悉；不影响本包落盘（本包以磁盘现存文档 + `rev16_2_ruling_apply_package.md` 为锚点来源） |
| P-6 | **[TBD-T24]** 与 **[TBD-T19]** 同源（装配期耗时），须**合并观测** | 部署实测 | 目标机实测时合并记录（AC-IB-07-05 纪律） |

---

**交付声明**：本包为**纯设计落盘包**，不含实现代码 / 测试 / 部署脚本；**未修改 `src/`**、**未修改 FreeArk**、**未修改需求侧文档**、**未整文件重写三份受保护设计文档**；**未写入任何凭据**。落盘后 `architecture_design.md` / `module_design.md` → **1.7.0 / REV-16-2**；`tech_stack.md` → **NO_CHANGE**。
