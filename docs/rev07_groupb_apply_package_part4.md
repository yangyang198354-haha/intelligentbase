<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package_part4</artifact>
  <path>docs/rev07_groupb_apply_package_part4.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_03 架构设计）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/architecture_design.md</targets>
</file_header>

# REV-07 APPLY-READY 修订包 · 第 4 册 — 架构文档指令（§6 / §8 / §9 / §10 与计数同步）

### R7-A-12
- target_file: `docs/architecture_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `**多级意图路由（REQ-FUNC-IB-19，逐级降级，永不无解）**：`
- old_string: `（空：纯插入）`
- new_string:
```text
**（R7）图编译输入与拓扑不可编辑**：编排图的编译输入是**经准入闸门校验通过的定义文档**（ADR-16；校验器 IFC-IB-290，闸门 IFC-IB-293）；图**编译一次、进程常驻**，**运行期不得由任何图外输入改变拓扑** —— 节点 / 边集合与条件边存在性**不是**可视化界面的可编辑对象（REQ-FUNC-IB-26 ②）。拓扑变更的**唯一路径**：改定义文档 → 装配期校验 → 重新编译（AC-IB-18-01）。可编辑的是**节点参数与专家集合**（模型与系统提示、工具授权、路由关键词与语义范例、路由阈值与边界参数、并行扇出专家集合、默认专家标记），且受白名单约束（IFC-IB-291）。

```
- rationale: REV-07-2 —— 「装配期完备性校验 + fail-fast 准入闸门」的架构级落点：明确编译输入、唯一变更路径与不可编辑边界，避免「可视化 = 运行期改图」的误读。

### R7-A-13
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| **ARCH-ASSUMPTION-A5** | 前端静态产物由 `ib-web` 直接提供（或系统 nginx） | 需求未规定前端托管方式 | 若改用 nginx，仅部署配置变化，无代码影响 | 需 PM 知悉 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **ARCH-ASSUMPTION-A6**（R7 新增） | **定义文档的物理载体 = 本地文件**（路径经 `IB_DEFINITION_DOC_PATH` 注入），**一项目一文档**，内容为结构化、机器可读文本 | REQ-FUNC-IB-25 只规定「项目级、结构化、机器可读」，**未规定存储载体**；也未规定「一项目是否可有多个文档」 | 若改为 DB / 配置中心承载，**只替换 `DefinitionDocumentStore` 适配器**（IFC-IB-292），装载 / 校验 / 写入 / 派生逻辑**零改动**（ADR-15）；「一项目多文档」若成立，须改的是文档**聚合根**定义，属需求侧变更 | 需 PM 确认（载体与「一项目一文档」口径） |
| **ARCH-ASSUMPTION-A7**（R7 新增） | **可视化的落地前置条件**：专家 / 路由 / 编排 / 工具授权的定义**已外置为数据、且为单一真源**（即 REQ-FUNC-IB-01 / IB-02 的**实现落差**先被闭合）——**该前提已被登记为「施工顺序前置 + 风险」，不构成施工阻断** | 需求侧已明示该前提并声明「**不在本节新增需求**」（`requirements_spec.md` §2.7 前言）；US-IB-17 / US-IB-18 为**施工顺序前置**而非阻塞（`user_stories.md` 决策前置状态行） | 若前提未闭合：定义文档无数据源，可视化的**装配期闸门与派生**仍可先落地与单测（AC-IB-18-05 离线可测），但界面**无真实内容可编辑**；**不影响架构与模块设计成立**。**REV-07-6 判定 = (a) 可登记前置条件 / 风险，本轮继续**；若 PM / 用户改判 (b)（IB-01/02 未闭合前不得开展可视化设计），须回 GROUP_A 立项并整体回退本修订 | **已登记（R7）：判定 (a)**；须 PM 知悉并在 GROUP_C 施工顺序中体现 |
```
- rationale: REV-07-6 —— 前置条件必须**显式声明**且落在架构假设表中（可被门控逐条核验）；A6 覆盖「需求未规定的载体问题」，A7 覆盖「施工前置判定」，二者均有「若不成立」的代价分析。

### R7-A-14
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `否则排障会归因错误 | |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **TBD-T19（R7 新增）** | **装配期装载 + 完备性校验 + 派生视图**的耗时（冷启动预算）与随定义文档**规模**（专家数 / 关键词数 / 条件边数）的增长曲线 | REQ-FUNC-IB-27；REQ-NFR-IB-02；AC-IB-18-06；ADR-15 / ADR-16 | 决定是否需要对派生结果做**合规缓存**（ADR-15 Option C 的两个前置条件：失效键 = 文档语义哈希、可随时删除且不得成为读源）；也用于校准装配期超时与启动预算 |
| **TBD-T20（R7 新增）** | **前端可视化的规模上界**：定义文档在目标机浏览器上的**图渲染**规模（节点数 / 条件边数 / 分支映射条目数）与前端产物体积增量（含图可视化库及其传递依赖） | REQ-FUNC-IB-25；AC-IB-17-02 / AC-IB-17-06 | 决定是否需要**虚拟化渲染 / 路由级按需加载**；并作为 `tech_stack.md` §5.3「图库许可与体积」风险行的实测依据 |
```
- rationale: 纪律要求「凡未能确证的事实须标 TBD / 待核实」；T19 / T20 是本增量新引入的**可实测**未知量，避免以估计值冒充实测。

### R7-A-15
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| OQ-IB-02 / 04 / 06 / 08 | 次级开放问题（措辞未变，P1） | 不阻塞 | 待用户裁决 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **（R7）REV-07-6 施工前置**（IB-01 / IB-02 定义外置） | 可视化落地的**施工顺序前置**是否须先闭合（「先定义外置、后可视化」） | **登记为前置条件 / 风险，不阻断**（[ARCH-ASSUMPTION-A7]；判定 **(a)**） | 若 PM / 用户改判 **(b)**，本修订整体回退并回 GROUP_A 立项；架构层不自行扩围或缩围 |
```
- rationale: REV-07-6 —— 判定必须**显式落纸**在开放问题表中，便于门控以「是否显式声明」而非「是否自述」核验。

### R7-A-16
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| Poppler CLI | GPL-2.0 | 不采纳（仍属 copyleft，子进程隔离的法律定性有争议） |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **Vue Flow（`@vue-flow/core`，R7 新增）** | **MIT** | **采纳**（可视化配置页的编排图渲染；R7 **经外部核实**：包内 `LICENSE` 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024）；**传递依赖**（D3 系 / `@vueuse/core` 等）须在锁定版本后**逐包核实并登记**，未核实者标 `[待核实]` |
```
- rationale: REV-07-4 —— 许可台账与 `tech_stack.md` §2 保持**单一口径**（两处同步登记，避免出现第二份口径）。

### R7-A-17
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `- REQ → MOD 覆盖率矩阵（24 条 REQ-FUNC 全覆盖）、模块依赖图 DAG 无环证明、类型化接口契约、组合根装配表见 `module_design.md`。`
- new_string: `- REQ → MOD 覆盖率矩阵（**27 条 REQ-FUNC 全覆盖**；R7 同步计数，v1.2.0 需求总数）、模块依赖图 DAG 无环证明、类型化接口契约、组合根装配表见 `module_design.md`。`
- rationale: REV-07-3 —— 计数同步（需求计数语境；24 → 27）。

### R7-A-18
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `REQ→MOD 覆盖仍为 **24/24 REQ-FUNC + 14 条 NFR**；模块依赖图 **DAG 无环**（证明未受改动影响，见 `module_design.md` §4.2.1）。`
- new_string: `REQ→MOD 覆盖仍为 **27/27 REQ-FUNC（R7 同步计数；R1 时点基线为 24/24）+ 14 条 NFR**；模块依赖图 **DAG 无环**（证明未受改动影响，见 `module_design.md` §4.2.1）。`
- rationale: REV-07-3 —— 同步计数并**保留基线时点**括注（历史事实不篡改，同时不给读者留下陈旧数字）。

### R7-A-19
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `端口数仍 **13**；REQ→MOD 覆盖仍 **24/24 REQ-FUNC + 14 NFR**；依赖图**仍为 DAG**`
- new_string: `端口数仍 **13**（**R7 同步：13 → 14，新增 `DefinitionDocumentStore`，纯追加**）；REQ→MOD 覆盖仍 **27/27 REQ-FUNC（R7 同步计数；R2 时点基线为 24/24）+ 14 NFR**；依赖图**仍为 DAG**`
- rationale: REV-07-3 —— 同上；并顺带把「端口 13」的陈旧感消除（端口数的**权威落点**为 `module_design.md` §2.2，本处只作同步说明）。

### R7-A-20
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `含新增的图片端点）。`
- old_string: `（空：纯插入）`
- new_string:
```text
- **（R7）可视化配置增量已贯通**：新增 **ADR-14 / ADR-15 / ADR-16**（编辑模型 / 单一真源（双向同源）/ 装配期 fail-fast 准入闸门），每条含 **≥2** 方案且含「已评估未采纳」留痕；新增 **§2.0.2 R7 影响复核表**（**既有 13 条 ADR 全部不受影响**、新增 3 条、**无一条跳过**）；新增**第 14 个端口** `DefinitionDocumentStore`（IFC-IB-287）；§6 明确「图编译输入 = 校验通过的定义文档；拓扑不可编辑」。
- **（R7）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、`IFC-IB-001~286` 一字不动（新增 287~297；`IFC-IB-285` 仍预留未分配）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（论证见 `module_design.md` §4.2.2）；REQ→MOD 覆盖 **27/27 REQ-FUNC + 14 NFR**（由 24/24 同步）。
- **（R7）前置条件已登记且不阻断**：`[ARCH-ASSUMPTION-A7]`（可视化落地前提 = IB-01 / IB-02 的定义外置）+ §10.1 对应行；**REV-07-6 判定 = (a) 可登记前置条件 / 风险，本轮继续**；**未**在本轮自行设计 IB-01 / IB-02 的实现方案（超 GROUP_B 边界）。
- **（R7）凭据纪律**：全文仍只登记**键名**（`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；定义文档**只出现键名、不出现凭据值**；界面与校验错误信息均**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；**URL 与文档一律不得出现凭据型查询串**（该纪律在 R7 扩展至全部新端点，含定义的 GET / PUT）。
- **（R7）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`implementation_plan.md`（GROUP_C）**未作修改**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为离线自检**用例数**，与本文件的 REQ 计数 27 属不同口径，**不得混淆、不得改动**）。
```
- rationale: 与 R1 / R2 自检节句式一致，给出可逐条核验的 R7 自检声明（含 REV-07-6 判定的落纸与「不得混淆两种 24」的显式提醒）。
