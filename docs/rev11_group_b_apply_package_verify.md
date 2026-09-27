# REV-11-2 增量修订包（APPLY PACKAGE · E 部：核验与收口）

**文档编号**: APPLY-REV-11-2-INTELBASE-001E
**版本**: 0.1.1
**状态**: DRAFT（**待 PM 门控**；仅含落盘指令与核验记录，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: 模块侧 §verify 锚点核验清单 + 模块侧一致性自检 + **REV-11-2 全局收口**

> **本包承接**：D 部（`rev11_group_b_apply_package_module_b.md`）中提到的「见 §2 锚点核验」与「模块侧一致性自检」**均在本文件**给出（D 部因单次写入载荷上限未并入，内容不缺失）。
> **⚠ 分部文件名的更正（务必先读）**：**A 部**（`docs/rev11_group_b_apply_package.md`）文件头曾写「配套包 = `docs/rev11_group_b_apply_package_module.md`」——**该文件不存在**（因单次写入载荷上限，模块侧被进一步拆为 C 部 + D 部）。**正确的分部映射以本表为准**；PM 落盘时请**忽略 A 部文件头那一行**（或按本表把该行改为「配套包见 C / D 部」）。

**REV-11-2 完整修订包的五个分部（同一 `invocation_id`，同一套编号纪律）**:

| 分部 | 文件 | 内容 |
|------|------|------|
| **A 部** | `docs/rev11_group_b_apply_package.md` | 修订总览 + 架构侧指令 **A-01 ~ A-10** |
| **B 部** | `docs/rev11_group_b_apply_package_arch_b.md` | 架构侧指令 **A-11 ~ A-17** + 架构侧自检 + §verify |
| **C 部** | `docs/rev11_group_b_apply_package_module_a.md` | 模块侧指令 **M-01 ~ M-17** |
| **D 部** | `docs/rev11_group_b_apply_package_module_b.md` | 模块侧指令 **M-18 ~ M-33** |
| **E 部（本文件）** | `docs/rev11_group_b_apply_package_verify.md` | 模块侧 §verify + 模块侧自检 + **全局收口** |

> **交付形态说明**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对 `docs/architecture_design.md` 与 `docs/module_design.md` 发起任何写入**，而是产出 APPLY-READY 修订包，由 PM 以 Edit **机械落盘**（先例：`docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md`）。
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。下表为本轮**实际执行**的核验结果（每条均 == 1）。

---

## 1. 模块侧 §verify 锚点核验清单（`docs/module_design.md`，M-01 ~ M-33）

| 指令 | 动作 | anchor（`Grep` 目标，逐字） | 核验次数 | 唯一性 |
|------|------|---------------------------|----------|--------|
| M-01 | REPLACE | `<version>1.3.0</version>` | 1 | 通过 |
| M-02 | REPLACE | `<revision>R7</revision>` | 1 | 通过 |
| M-03 | REPLACE | `<invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>` | 1 | 通过 |
| M-04 | REPLACE | `<input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>` | 1 | 通过 |
| M-05 | REPLACE | `<input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>` | 1 | 通过 |
| M-06 | REPLACE | `<input path="docs/architecture_design.md" version="1.3.0" revision="R7" status="DRAFT_FOR_GATE_REVIEW"/>` | 1 | 通过 |
| M-07 | INSERT_AFTER | **两行块**：第 1 行 `未修改 FreeArk 任何文件；需求侧文档只读；未写入任何凭据或配置值（只登记键名）。` + 第 2 行 `    </rev>` | 1（第 1 行子串；R7 元素的唯一段末） | 通过（`^    </rev>$` 在文件内有 **2** 处，故**必须**用两行块定位） |
| M-08 | REPLACE | `**版本**: 1.3.0 (R7)` | 1 | 通过 |
| M-09 | INSERT_AFTER | `（见 §9.5；另见 `architecture_design.md` [ARCH-ASSUMPTION-A7]）。` | 1 | 通过 |
| M-10 | INSERT_AFTER | `` conflict: bool`；`errors: tuple[ValidationErrorItem, ...]` \| \| `` | 1 | 通过 |
| M-11 | INSERT_AFTER | `全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5）。` | 1 | 通过 |
| M-12 | INSERT_AFTER | `` （同 `CollectionResolver` 的「唯一入口」精神；ADR-15）。 `` | 1 | 通过 |
| M-13 | INSERT_AFTER | `` 以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。 `` | 1 | 通过 |
| M-14 | INSERT_AFTER | `**无实现体**。` | 1 | 通过 |
| M-15 | REPLACE | `REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）` | 1 | 通过 |
| M-16 | REPLACE | `**IB-25 / IB-26 / IB-27（R7 新增：定义文档的装载 / 白名单 / 完备性校验与派生）**；REQ-NFR-IB-02、IB-07` | 1 | 通过 |
| M-17 | INSERT_AFTER | `**IFC-IB-297（R7 新增）**: 新增配置**键名**（**仅登记键名，不含值**）` | 1 | 通过 |
| M-18 | REPLACE | `- **覆盖需求**: REQ-FUNC-IB-20、IB-21；AC-IB-14-01（降级事件可见）` | 1 | 通过 |
| M-19 | INSERT_AFTER | `R2 只定义其 data）。` | 1 | 通过 |
| M-20 | REPLACE | `- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06` | 1 | 通过 |
| M-21 | INSERT_AFTER | `` `step_count: int`（上限 `MAX_EXPERT_STEPS = 8`） `` | 1 | 通过 |
| M-22 | REPLACE | `IB-25 / IB-27（R7 新增：定义文档的读写端点与装配期准入闸门）**；REQ-NFR-IB-09` | 1 | 通过 |
| M-23 | INSERT_AFTER | `**新增键名不含任何值**。` | 1 | 通过 |
| M-24 | REPLACE | `**IB-25（主）、IB-26（并列主，与 MOD-IB-22）、IB-27（辅）**` | 1 | 通过 |
| M-25 | REPLACE | `前端预校验仅为体验优化；**服务端校验器（IFC-IB-290）为唯一裁决者**（界面编辑与直接改文档**一视同仁**）。` | 1 | 通过 |
| M-26 | INSERT_AFTER | `读取时断言前缀（FM-7）。` | 1 | 通过 |
| M-27 | INSERT_AFTER | `\| ERROR \| **fail-closed（配置读）**；对问答链路无影响 \|` | 1 | 通过 |
| M-28 | INSERT_AFTER | `` 配合 `InMemoryDefinitionDocumentStore` 即可在**无任何外部服务**下完成装配期全链路离线验证（AC-IB-18-05）。 `` | 1 | 通过 |
| M-29 | INSERT_AFTER | `不得新开编号更高的模块**。` | 1 | 通过 |
| M-30 | REPLACE | `\| IB-20 \| 会话生命周期 \| **MOD-IB-21** / 22 \|` | 1 | 通过 |
| M-31 | INSERT_AFTER | `AC 落点分别为 AC-IB-17-01~06、AC-IB-17-04 / AC-IB-18-01、AC-IB-18-01~06）。` | 1 | 通过 |
| M-32 | INSERT_AFTER | `本文件**不得**据此改写该文件。` | 1 | 通过 |
| M-33 | INSERT_AFTER | `` 只登记键名：`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；本阶段**止于 GROUP_B**。 `` | 1 | 通过 |

> **M-07 特别提示（防误落）**：`    </rev>` 在文件内出现 **2** 次（R1 元素与 R7 元素各一行），**单独以该行作锚点会定位歧义**。故 M-07 **强制**使用「R7 元素段末子串 + 闭合行」的**两行块**作锚点；该两行组合在文件内**唯一**。

---

## 2. 模块侧一致性自检

1. **编号稳定性**：`MOD-IB-01 ~ 26` 的 ID 与职责句、`IFC-IB-001 ~ 297` 的号 / 名 / 签名 / 字段集、**14 个端口名**、**§4.1 依赖边 26 行**、§5 装配表既有行、§6 状态机、§7.1 / §7.2 表、§10 FreeArk 映射表 **一字未改**；R8 只**追加** `IFC-IB-298 ~ 308`。
2. **签名文本零改动（两条关键防线）**：`IFC-IB-221 / 222`（`SessionStore.load` / `save`）的签名文本**不改**（M-10 / M-14 只补其悬置引用的 `SessionState` 定义）；`IFC-IB-233`（`resume(session_key, payload: dict)`）的签名文本与参数个数**不改**（M-21 只新增其载荷类型 `ResumePayload`，沿用 IFC-IB-282 先例）。
3. **端口数不变**：`SessionStore` 仍为 **3 方法**（`IFC-IB-221 ~ 223`），其端口表行**未改**；全文件端口数仍 **14**（M-12 显式声明）。
4. **计数更新一致**：模块数 **26**、端口数 **14**、`IFC-IB-285` **仍预留未分配**、`IFC-IB-131` **登记不修**、REQ→MOD 覆盖 **27/27 REQ-FUNC + 14 NFR**（**无新 REQ**）—— 上述计数在 M-07 / M-09 / M-12 / M-13 / M-29 / M-32 / M-33 **各处陈述一致**。
5. **值域扩展的键名/默认值不变**：`IB_SESSION_BACKEND` 仅**值域**由 `memory` 扩展为 `memory 或 external`，**键名与默认值（`memory`）不变**（M-12 / M-17，沿用 R2 对 `IB_EMBED_BACKEND` 的先例）；新增三个键名**只登记键名、不含任何值**。
6. **两文件交叉引用一致**：M-07 / M-09 / M-32 / M-33 引 `architecture_design.md` 的 **ADR-17** / **§2.0.3** / **[ARCH-ASSUMPTION-A8]** / **[TBD-T21]** —— 均已在 B 部落盘清单内，编号**逐一对应**，无悬空引用。
7. **无循环依赖再声明**：M-29 新增 §4.2.3，与 §4.2.1（R1）/ §4.2.2（R7）同构；**零新增依赖边**，`w(MOD-IB-n) = n` 严格递减的构造性证明不受影响。
8. **无代码**：M-01 ~ M-33 全部为设计文本 / 表格行 / XML 元数据 / 类型化契约（`name: type` + 可空性），**不含函数体、不含伪代码**。
9. **无残留旧版本号**：落盘后目标文件**不得**再出现 `1.3.0 (R7)`（M-08）、`INV-GROUP_B-INTELBASE-002`（M-03）、`version="1.2.0"`（M-04 / M-05）、`architecture_design.md ... version="1.3.0" revision="R7"`（M-06）；历史 `<rev>` 元素内**允许**保留旧版本号（属历史记录，**不得**改动）。
10. **OQ 未越权**：**OQ-IB-07 / OQ-IB-08 保持开放**（M-17 / M-26 / M-32 三处一致声明）；R8 只落地「默认关闭 / 会话内隔离」的安全默认。

---

## 3. REV-11-2 全局收口

### 3.1 待编辑文件（仅 2 份）与指令数

| 目标文件 | 旧版本 → 新版本 | 指令数 | 分部 |
|----------|----------------|--------|------|
| `docs/architecture_design.md` | 1.3.0（R7）→ **1.4.0（R8）** | **17**（A-01 ~ A-17） | A 部（A-01 ~ A-10）+ B 部（A-11 ~ A-17） |
| `docs/module_design.md` | 1.3.0（R7）→ **1.4.0（R8）** | **33**（M-01 ~ M-33） | C 部（M-01 ~ M-17）+ D 部（M-18 ~ M-33） |
| `docs/tech_stack.md` | **不改**（1.0.0 保持） | **0** | —（理由见 A 部 §1.4） |

**指令总数：50 条** = **REPLACE 22 条** + **INSERT_AFTER 28 条**。逐文件拆分：

| 文件 | REPLACE | INSERT_AFTER | 小计 |
|------|---------|--------------|------|
| `docs/architecture_design.md` | **7**（A-01 / 02 / 03 / 04 / 05 / 07 / 09） | **10**（A-06 / 08 / 10 / 11 / 12 / 13 / 14 / 15 / 16 / 17） | 17 |
| `docs/module_design.md` | **15**（M-01 / 02 / 03 / 04 / 05 / 06 / 08 / 15 / 16 / 18 / 20 / 22 / 24 / 25 / 30） | **18**（M-07 / 09 / 10 / 11 / 12 / 13 / 14 / 17 / 19 / 21 / 23 / 26 / 27 / 28 / 29 / 31 / 32 / 33） | 33 |
| **合计** | **22** | **28** | **50** |

两份文档的 `<status>` **均保持** `DRAFT_FOR_GATE_REVIEW`（本包**不**写 APPROVED / ACCEPTED）。

### 3.2 新增编号（全部为**追加**）

| 类别 | 新增 | 数量 | 备注 |
|------|------|------|------|
| **IFC** | **IFC-IB-298 ~ IFC-IB-308** | **11** | 无跳号；`IFC-IB-285` **仍预留未分配**；`IFC-IB-131` **登记不修** |
| **ADR** | **ADR-17** | **1** | **3 候选方案**（A / B / C），**Option B** 选定；含「已评估未采纳」留痕；ADR 总数 **16 → 17** |
| REQ-FUNC | — | **0** | 仍 **27** |
| REQ-NFR | — | **0** | 仍 **14** |
| 模块 | — | **0** | 仍 **26**（无 MOD-IB-27） |
| 端口 | — | **0** | 仍 **14**（`SessionStore` 仍 3 方法） |
| 依赖边 | — | **0** | §4.1 **逐行不变**；DAG 无环 |

### 3.3 需 PM 决策 / 知悉项

| # | 事项 | 本包立场 | 需 PM 的动作 |
|---|------|----------|--------------|
| ① | **ADR-17 是否必要** | R8 为「可选手动确认中间态 + 会话恢复」新增架构决策（**3 方案**），使 AC-IB-20-03 / 04 / 05 在**架构侧**有决策留痕 | 若 PM 判「ADR-11-R1 + ADR-09 已足够、不需新 ADR」，则**跳过 A-12**，并把 A-06 / A-08 / A-11 / A-17 中「ADR 数 16 → 17」的表述**相应回退**（本代理**不擅自改口径**，等 PM 裁决） |
| ② | **`tech_stack.md` §1.2 键名清单是否同步** | 三个新键名登记在 `module_design.md`（IFC-IB-304）；`tech_stack.md` **不在本包落盘范围**（避免反复扩围） | 若 PM 要求两处同步，**请另行指派一轮**（本代理不擅自扩围） |
| ③ | **[ARCH-ASSUMPTION-A8]（v1 默认持久化策略）** | v1 默认 = `in_process`（跨重启不保待确认状态，语义 fail-closed）；`external` **只声明值域、不配适配器** | 需 PM **确认**该默认；若判「v1 必须跨重启持久化」，**须回 GROUP_A / 立项**（属需求侧扩围） |
| ④ | **OQ-IB-07 / OQ-IB-08** | **保持开放**；R8 只落地「默认关闭 / 会话内隔离」的安全默认，**不裁决业务语义** | 知悉即可 |
| ⑤ | **本轮未触碰 `implementation_plan.md`（GROUP_C）** | 其 L471 / L603 / L621 / L732 的「24/24 PASS」为**离线自检用例数**，与本轮 REQ 计数 **27** 属**不同口径** | 知悉即可（**不得**据此改写该文件） |

### 3.4 本包（E 部）自检声明

- 本包**只含核验记录与收口说明**，**未对任何既有文件发起写入**。
- 模块侧 **33 条**锚点（M-01 ~ M-33）全部经 `Grep` 核验，**出现次数均为 1**（M-07 以**两行块**定位，见 §1 提示）。
- 本包**未新增** REQ / 模块 / 端口 / 依赖边；**未新增** `IFC-IB-*`；**未新增** ADR。
- 本包**未写入任何凭据值 / 配置值**（只登记键名）。
- **不声称任何门控结果**：门控裁决权在 PM。
- **未修改 FreeArk 仓库任何文件**（只读参考）；**未修改需求侧文档**（`requirements_spec.md` v1.3.0 / `user_stories.md` v1.3.0 只读）。
