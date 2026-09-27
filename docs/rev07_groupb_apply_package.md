<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package</artifact>
  <path>docs/rev07_groupb_apply_package.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_03 架构设计 / PHASE_04 模块详细设计 / PHASE_04b 技术选型 贯通）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/architecture_design.md; docs/module_design.md; docs/tech_stack.md</targets>
  <package_parts>本包共 4 册：本册（§0 总览 + §1 架构文档指令 R7-A-01~R7-A-19）、docs/rev07_groupb_apply_package_part2.md（§2 模块文档指令 R7-M-01~R7-M-26）、part3（§3 技术栈指令 R7-T-01~R7-T-13）、part4（§4 落盘后核验清单 + 不变量核对表）</package_parts>
  <scope_boundary>本文件是**编辑指令包（APPLY-READY）**，不重写任何目标文档：只产出「目标文件 + 唯一锚点 + 新内容 + 理由」的可机械落盘指令。领域内容由 system-architect 撰写；PM 用 Edit 逐条落盘，**不使用 Write 整文件覆盖**（历史事故 KE-REQ-011 / KE-REQ-019）。</scope_boundary>
  <credential_policy>本包**不含任何口令 / 密钥 / token 值**；仅登记**配置键名**。凭据一律「环境变量注入」（REQ-NFR-IB-07 / C-IB-02）。</credential_policy>
</file_header>

# REV-07 APPLY-READY 修订包 — GROUP_B 增量贯通（REQ-FUNC-IB-25 / IB-26 / IB-27）

**依据**: `AGENT_INVOCATION` `INV-GROUP_B-INTELBASE-005`（flow_mode = PARTIAL_FLOW 增量修订；revision = REV-07「REV-06 下游贯通」）。
**上游基线**: `requirements_spec.md` v1.2.0（APPROVED，REV-06）+ `user_stories.md` v1.2.0（APPROVED，REV-06）；既有 GROUP_B 结论（GR-B-002 / GR-B-003）**继续有效**；本修订为**增量**，不推翻整篇文档。

---

## 0. 落盘方式与总览

### 0.1 PM 落盘规程（逐条机械执行）

1. 本包共 **58 条**编辑指令：架构文档 `R7-A-01 ~ R7-A-19`；模块文档 `R7-M-01 ~ R7-M-26`；技术栈 `R7-T-01 ~ R7-T-13`。**按序执行**（同一文件内按编号顺序；锚点互不重叠）。
2. 每条指令的 `anchor` 即该条的 `old_string`（文件中**全局唯一**原文，生成前已逐条 grep 核验）；`action` 取值：
   - `REPLACE`：用 `new_string` 替换 `anchor`（逐字符替换）。
   - `INSERT_AFTER`：在 `anchor` **所在行之下**插入 `new_string`（**不删除** anchor 原文）。
   - `INSERT_BEFORE`：在 `anchor` **所在行之上**插入 `new_string`（**不删除** anchor 原文）。
   - 纯插入类指令的 `old_string` 记为 `（空：纯插入）`。
3. **本包之外的行一律不动**（见 §0.5 禁止清单）。凡报「未找到匹配」，**不得**退化为整文件 Write：停下来核对 anchor 原文（全角/半角、行尾空格）后手工定位。

### 0.2 REV-07-6 施工前置判定（**必须显式声明**）

**判定 = (a) 可登记的前置条件 / 风险，本轮继续；不构成施工阻断（不报 BLOCKED）。**

依据（逐条可核）：
1. `requirements_spec.md` v1.2.0 §2.7 前言原文：「**施工顺序前置（不改变优先级，仅说明顺序）**：可视化只能作为**定义文档的视图**存在，故其落地前提是「专家 / 路由 / 编排 / 工具授权的定义已外置为数据、且为单一真源」；该前提属既有 REQ-FUNC-IB-01 / REQ-FUNC-IB-02 的**实现落差**（见 `agent_platform_research.md` §3.3 P0），**不在本节新增需求**。」→ 需求侧已把该前提定性为**顺序说明 / 实现落差**，未定性为阻断。
2. `user_stories.md` v1.2.0（US-IB-17 / US-IB-18 决策前置状态行）：两故事**不受 OD-1 ~ OD-5 影响**（无选型依赖），其落地有**施工顺序前置**——属「前置」而非「阻塞」。
3. GROUP_A 门控结论 = **PASS_WITH_CONDITIONS**（附 open_item_1）→ 属「条件」，非「否决」。
4. 三条新需求优先级均为 **Must Have** 且已被用户裁决纳入 v1；若架构层判 (b)，等于**自行否决已批准的需求**，属擅自动用扩/缩围权力（PM 明令禁止）。

**处置**：本轮**登记为前置条件 + 风险**（架构侧 `[ARCH-ASSUMPTION-A7]` + §10.1 开放问题行；模块侧 §9.5 声明「施工前置条件 ≠ 覆盖缺口」），并**继续产出**。**不在本轮自行设计 REQ-FUNC-IB-01 / IB-02 的实现方案**（超出 GROUP_B 边界，且需求侧未立项）。
**若 (b) 的复核触发条件（供 PM 判断，本代理不采用）**：若 PM / 用户裁定「IB-01 / IB-02 未闭合前不得开展可视化设计」，则本包整体作废并回 GROUP_A 立项；该裁定权在 PM / 用户，不在本代理。

### 0.3 版本与状态变更表

| 文件 | 现版本 | 修订后 | status | 落盘位置 |
|------|--------|--------|--------|----------|
| `docs/architecture_design.md` | 1.2.0 / R2 | **1.3.0 / R7** | DRAFT_FOR_GATE_REVIEW（不变） | §1（本册） |
| `docs/module_design.md` | 1.2.0 / R2 | **1.3.0 / R7** | DRAFT_FOR_GATE_REVIEW（不变） | part2 |
| `docs/tech_stack.md` | 1.2.0 / R2 | **1.3.0 / R7** | DRAFT_FOR_GATE_REVIEW（不变） | part3 |

三份文档 `<file_header><input>` 中 `requirements_spec.md` / `user_stories.md` 版本 **1.1.0 → 1.2.0**，并**新增 R7 修订历史行**（REV-07-7）。

### 0.4 关键设计结论摘要（REV-07-2 / -1 / -5 / -6）

1. **编辑模型** = 定义文档为**唯一真源** + **显式三阶段 round-trip 编辑事务**，视图侧**零持久化** → **新增 ADR-14**（评估 3 方案，含 2 项已评估未采纳）。
2. **单一真源（双向同源）** = 文档是**持久化态**唯一真源；一切派生视图（专家集合 / 关键词表 / 默认专家 / 可委托集合 / 能力摘要 / 图）为**只读、不落盘、不可反写**的派生物，派生在**装配期**由组合根完成 → **新增 ADR-15**（评估 4 方案，含 3 项已评估未采纳）。
3. **装配期完备性校验 + fail-fast 准入闸门** = 闸门置于装配序列第一步；校验器为纯函数；`ValidationReport` **结构上不含** force / ignore / warn-only 字段（「无强制继续开关」成为类型事实）→ **新增 ADR-16**（评估 3 方案，含 2 项已评估未采纳）。**ADR 总数 13 → 16**。
4. **模块归属（REV-07-1）：不新增模块**（26 个模块不变）。定义文档数据层 → 落 **MOD-IB-02**（L0，纯数据、framework-free）；契约与**新增第 14 个端口** `DefinitionDocumentStore` → 落 **MOD-IB-01**；可视化端点与装配期闸门 → 落 **MOD-IB-23**；可视化视图 → 落 **MOD-IB-24**。**零新增依赖边**（§4.1 逐行不变）。
5. **接口**：新增 `IFC-IB-287 ~ 297`（11 条），全部**类型化**（`name: type` + 可空性），全部为 **frozen dataclass / Protocol，纯 stdlib、零第三方依赖**（REV-07-5）。
6. **技术选型**：新增「前端图可视化库」= **Vue Flow（`@vue-flow/core`，MIT，R7 经外部核实）**；§1.1 留痕 4 项已评估未采纳（AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3）；传递依赖须逐包核实（未核实者标 `[待核实]`）（REV-07-4）。

### 0.5 禁止清单（本包**不**要求改动，PM 亦请勿顺手改动）

| 项 | 原因 |
|----|------|
| `implementation_plan.md` L471 / L603 / L621 / L732 的「24/24 PASS」 | 离线自检**用例数**，非 REQ 计数；该文件属 GROUP_C，本轮 PM 未令改（REV-07-3 明令禁止改动） |
| `docs/ib_embed_service_contract.md` | MOD-IB-26 契约唯一落点；本轮参考勿改 |
| `IFC-IB-285` | R2 显式预留未分配；本轮**不占用**、不改义 |
| 既有重号 `IFC-IB-131`（MOD-IB-11 / MOD-IB-12 同号） | 登记不修（残余项 R-9）；任何重排会打断下游引用 |
| 三份文档 `revision_history` 中 R1 / R2 历史行 | 历史事实，**不回改**；计数同步只在正文结论句与自检节内以括注方式落笔 |
| `requirements_spec.md` / `user_stories.md` | 需求侧 APPROVED 文档，本轮**只读** |

---

## 1. `docs/architecture_design.md` 指令（R7-A-01 ~ R7-A-19）

### R7-A-01
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
  <version>1.2.0</version>
  <revision>R2</revision>
```
- new_string:
```text
  <version>1.3.0</version>
  <revision>R7</revision>
```
- rationale: REV-07 版本号规则（1.2.0 → 1.3.0（R7））。

### R7-A-02
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `<updated_at>2026-09-25</updated_at>`
- new_string: `<updated_at>2026-09-27</updated_at>`
- rationale: 修订日期同步为 REV-07 日期。

### R7-A-03
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.1.0" status="APPROVED"/>
```
- new_string:
```text
    <input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>
```
- rationale: REV-07-7 — `<input>` 引用版本 1.1.0 → 1.2.0（REV-06 后的 APPROVED 基线）。

### R7-A-04
- target_file: `docs/architecture_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `  </revision_history>`
- old_string: `（空：纯插入）`
- new_string:
```text
    <rev version="1.3.0" revision="R7" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-005" note="R7 增量贯通（GROUP_A REV-06 裁决：诉求③ UI 可视化配置纳入 v1，新增 REQ-FUNC-IB-25/26/27）：① 新增 ADR-14（可视化配置的编辑模型 = 定义文档唯一真源 + 显式 round-trip，视图零持久化）、ADR-15（定义文档单一真源（双向同源）与只读派生视图）、ADR-16（装配期完备性校验 + fail-fast 准入闸门，无强制继续开关），每条含 ≥2 方案与已评估未采纳留痕；ADR 数 13 → 16；② 新增 §2.0.2 R7 影响复核表（ADR-01~16 逐条：既有 13 条在 R7 下均不受影响、新增 3 条），§2.0 / §2.0.1 保留为 R1 / R2 历史复核；③ 新增第 14 个端口 DefinitionDocumentStore（IFC-IB-287，定义于 MOD-IB-01 的零依赖 frozen dataclass / Protocol 层），§1.3 可替换点增一行；④ §6 增补「图编译输入 = 经准入闸门校验通过的定义文档；拓扑不可编辑」；⑤ §8 新增 [ARCH-ASSUMPTION-A6]（定义文档物理载体 = 本地文件，一项目一文档）与 [ARCH-ASSUMPTION-A7]（可视化落地的前置条件 = IB-01/IB-02 定义外置；REV-07-6 判定 (a) 可登记前置/风险，不阻断）；⑥ §9 新增 [TBD-T19]（装配期装载/校验/派生耗时）与 [TBD-T20]（前端图渲染规模上界）；⑦ 计数同步：REQ-FUNC 24/24 → 27/27（REV-07-3，仅需求计数语境；端口 13 → 14）；⑧ 需求侧文档与 FreeArk 仓库未改动；未写入任何凭据值。"/>
```
- rationale: REV-07-7 — 新增 R7 修订历史行；历史行（R1 / R2）不回改。

### R7-A-05
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**版本**: 1.2.0（R2 补交）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26`
- new_string: `**版本**: 1.3.0（R7 增量）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-27`
- rationale: 文档头版本行同步（版本号 + 状态 + 日期）。

### R7-A-06
- target_file: `docs/architecture_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `**R1 修订摘要**:`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 修订摘要（GROUP_A REV-06 贯通：诉求③「UI 可视化配置」纳入 v1）**: 新增 **ADR-14 / ADR-15 / ADR-16**（编辑模型 / 单一真源（双向同源）/ 装配期 fail-fast 准入闸门），**ADR 数 13 → 16**；新增 **§2.0.2 R7 影响复核表**（**既有 13 条 ADR 在 R7 下全部不受影响**——其中 ADR-09 判「不受影响且 R7 是其应用」；**新增 3 条**；**无一条 ADR 未复核**）；新增**第 14 个端口** `DefinitionDocumentStore`（IFC-IB-287，纯追加；§1.3 增一行）；§6 增补图编译输入约束；§8 新增 A6 / A7；§9 新增 [TBD-T19] / [TBD-T20]。**不变**：§1 / §3~§7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001~286` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环。**计数同步**：REQ→MOD 覆盖由 24/24 同步为 **27/27**（v1.2.0 需求总数；R1 / R2 时点基线 24/24 以括注保留）。
```
- rationale: REV-07-2 / -7 — 与既有 R1 / R2 摘要句式对齐，给出本轮改动的可审计摘要。

### R7-A-07
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**输入**: `requirements_spec.md` v1.1.0（APPROVED）、`user_stories.md` v1.1.0（APPROVED）`
- new_string: `**输入**: `requirements_spec.md` v1.2.0（APPROVED）、`user_stories.md` v1.2.0（APPROVED）`
- rationale: REV-07-7 — 正文输入行与 `<file_header>` 同步。
