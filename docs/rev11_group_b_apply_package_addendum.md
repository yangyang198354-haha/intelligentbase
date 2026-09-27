# REV-11-2 增量修订包 · 补遗（APPLY PACKAGE ADDENDUM · F 部）

**文档编号**: APPLY-REV-11-2-INTELBASE-001F
**版本**: 0.1.0
**状态**: DRAFT（**待 PM 门控**；仅含落盘指令，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: 收口 `docs/architecture_design.md` 与 `docs/module_design.md` 上**已被独立只读验证方**认定的 **3 处「包级缺漏」**（即：既有 50 条指令 `A-01 ~ A-17` / `M-01 ~ M-33` 未覆盖到的落盘编辑）。指令数 **3 条**：`M-34`、`A-18`、`M-35`。

**前置事实（由 PM 转述，本代理未复核门控结论）**:
- 既有 REV-11-2 包（A 部 `docs/rev11_group_b_apply_package.md`、B 部 `..._arch_b.md`、C 部 `..._module_a.md`、D 部 `..._module_b.md`）**已由 PM 落盘**至两份目标文件；二者现为 **`1.4.0 / R8`，status = `DRAFT_FOR_GATE_REVIEW`**。
- 独立只读验证方对落盘结果**重新从文件推导**，结论为 **PASS_WITH_CONDITIONS**，其缺陷项**全部为包级**（指令集自身遗漏了所需编辑，而非落盘错误）。

> **交付形态说明**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对任何目标文件发起任何写入**，而是产出 APPLY-READY 补遗，由 PM 以 Edit **机械落盘**（先例：`docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md`）。
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。本包每条均已核验（逐条计数见 §2；对存在同形行的锚点使用**行首行尾锚定**的正则以排除同形行）。
> **落盘后不得改版**：三份指令均为**原位补漏**，落盘后两份目标文件的 **version 仍为 `1.4.0`、revision 仍为 `R8`、status 仍为 `DRAFT_FOR_GATE_REVIEW`**，**不得**因本补遗而升版 / 升修订号 / 改状态。

---

## 1. 权威内容正文（F 部 · M-34 / A-18 / M-35）

> **通用约定**：`REPLACE` 条为「以 `new_string` 逐字替换 `old_string`」；`INSERT_AFTER` 条的插入点为该锚点**所在行的行尾之后**，凡 `new_string` **以空行开头**者已显式标注 —— 该空行用于与其上方段落分隔，**不得省略**。
> **表格内竖线**：`new_string` 位于 Markdown 表格行内，值域枚举中的 `|` 必须写成转义形式 `\|`（与 §5 既有 R2 行 `IB_EMBED_BACKEND=http\|inproc\|fake` 的写法一致），否则会破坏表格列结构。

### M-34 · `docs/module_design.md` · REPLACE（**MUST**）
- **落点**: §5「组合根装配表（MOD-IB-23）」的 `SessionStore` 行（L779）
- **anchor / old_string**（核验次数 **1**；正则 `^\| \`SessionStore\` \| \`MemorySessionStore\` \| 同（内存实现即替身） \| \`IB_SESSION_BACKEND=memory\` \|$`）:
```text
| `SessionStore` | `MemorySessionStore` | 同（内存实现即替身） | `IB_SESSION_BACKEND=memory` |
```
- **new_string**（逐字）:
```text
| `SessionStore` | `MemorySessionStore` | 同（内存实现即替身） | `IB_SESSION_BACKEND=memory\|external`（**R8 仅扩展值域（`memory` 或 `external`）；键名与默认值 `memory` 不变**） |
```
- **为何必须**：§5 是**值域声明的规范落点**（R2 先例即在**同一张表** L773 的 `IB_EMBED_BACKEND` 行声明「仅扩展值域」）。本代理在 §2.2 R8 增记（L178）/ IFC-IB-304（L224）/ §3 MOD-IB-02（L282）/ §11（L1097）与 `architecture_design.md` L93 均**已声明** `IB_SESSION_BACKEND` 值域为 `memory 或 external`，但 §5 装配行**未同步**，构成同一文档内的**声明不一致**。本指令**仅**修正该行，**键名与默认值（`memory`）不变**，**其余任何 §5 行一律不动**。
- **不变约束**: 不新增端口 / 不新增依赖边 / 不改 IFC 签名 / 不改任何既有键名或默认值；「离线/测试装配」列与「配置开关」列之外的单元格**一字不改**。

### A-18 · `docs/architecture_design.md` · REPLACE（**MUST**）
- **落点**: §10.3 自检声明 · 最后一条 R8 项目符号（L848）内的一个从句
- **anchor / old_string**（核验次数 **1**）:
```text
（R8 无新第三方依赖，理由见 A 部 §1.4）
```
- **new_string**（逐字）:
```text
（R8 无新第三方依赖：本轮新增均为**类型定义**与**配置值域扩展**（`IB_SESSION_BACKEND` 增列 `external` 取值），**不新增任何外部库 / 二进制 / 服务**，故 §10.2 许可合规结论无新增条目）
```
- **为何必须**：原文的「A 部 §1.4」是**验收用暂存包文件**（`docs/rev11_group_b_apply_package.md`）的章节，**不是**本交付文档自身的章节（本文件 §1.4 为「请求上下文传播」），属交付物内的**悬空外部引用**。替换后**理由自含**（R8 仅新增类型定义与配置值域，不引入外部依赖），并以**文内可解析**的 §10.2「许可合规结论（REQ-NFR-IB-12）」作为落点。
- **不变约束**: 该项目符号**其余措辞逐字保留**（`FreeArk` 未改 / 需求侧只读 / `implementation_plan.md` 未改 / `tech_stack.md` 未改 / 只登记键名）；未新增 REQ / ADR / 端口 / 依赖边。

### M-35 · `docs/module_design.md` · INSERT_AFTER（**可选采纳**）
- **落点**: §4.2.3 标题行之后（L738），使其与 §4.2.1 / §4.2.2 的**并行结构**一致
- **anchor**（核验次数 **1**；正则 `^### 4\.2\.3 R8 无环性再声明（零新增依赖边）$`）:
```text
### 4.2.3 R8 无环性再声明（零新增依赖边）
```
- **new_string**（**首行为空行**；逐字，共 2 行 —— 空行 + 结论行）:
```text

**结论：DAG 拓扑在 R8 下不变，无环证明（§4.2）继续成立。**
```
- **为何采用**：§4.2.2 在标题与正文之间有一条加粗 `**结论：…**` 起句（L730），§4.2.3 缺失（本代理在 M-29 编写时遗漏），破坏同一小节族的三段并行结构。本指令**只补起句**，措辞逐字镜像 §4.2.2（R7 → R8），**不改动 §4.2.3 任何既有条目**。
- **落盘后形态**（应与 §4.2.2 同形；原 L739 空行保留，作为与下方条目的分隔）:
```text
### 4.2.3 R8 无环性再声明（零新增依赖边）

**结论：DAG 拓扑在 R8 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：R8 的全部新增落在 …
```
- **可选性说明**：若 PM 判定此项属**格式润色**而非缺陷，可**不落盘**；不落盘**不影响** M-34 / A-18 两条 MUST 项的独立性，也不构成任何门控条件。

---

## 2. 锚点核验计数表（落盘前强制）

| 指令 | 目标文件 | 行 | 锚点（摘要） | 核验方式 | 出现次数 |
|------|---------|----|-------------|---------|---------|
| **M-34** | `docs/module_design.md` | L779 | §5 装配表 `SessionStore` 行（含「同（内存实现即替身）」） | 正则 `^...$` 行首行尾锚定（以排除 **L922** 同形行「同（自身即内存实现）」） | **1** |
| **A-18** | `docs/architecture_design.md` | L848 | `（R8 无新第三方依赖，理由见 A 部 §1.4）` | 字面串匹配 | **1** |
| **M-35** | `docs/module_design.md` | L738 | `### 4.2.3 R8 无环性再声明（零新增依赖边）` | 正则 `^...$` 行首行尾锚定 | **1** |

> **同形行规避提示（M-34）**：`| \`SessionStore\` | \`MemorySessionStore\` | … | \`IB_SESSION_BACKEND=memory\` |` 在 `module_design.md` 内**另有 L922 一处**（§7.2 替身一致性表，第 3 列为「同（自身即内存实现）」、第 4 列为「会话隔离键断言」）。故 M-34 的 `old_string` **必须整行含「同（内存实现即替身）」**，**不得**只截取前半段，否则会误匹配 L922。
> **悬空引用唯一性（A-18）**：`[A-D] 部` 形式的**暂存包章节引用**在两份目标文件内**仅 L848 一处**（`module_design.md` 经检索**无**此类引用），故本补遗**不遗漏同类项**。

---

## 3. 不变约束声明（硬约束，逐条自检）

1. **不升版**：两份目标文件落盘后仍为 **version `1.4.0` / revision `R8` / status `DRAFT_FOR_GATE_REVIEW`**。
2. **不新增结构**：**无**新 REQ / 新模块 / 新端口 / 新 IFC / 新 ADR / **新依赖边**；模块数仍 **26**、端口数仍 **14**、依赖图**仍为 DAG**。
3. **无实现代码**：三条指令均为文档文本编辑（表格单元格 / 从句 / 起句），**不含任何代码或伪代码**。
4. **不越界**：三条指令**仅**改动 `docs/architecture_design.md` 与 `docs/module_design.md` 各一至两处，**未**涉 `tech_stack.md` / `requirements_spec.md` / `user_stories.md` / `implementation_plan.md`。
5. **凭据纪律**：新增文本**只出现键名**（`IB_SESSION_BACKEND`），**无**任何凭据值、URL 查询串或敏感数据。
6. **不主张门控结论**：本补遗**不声明**任何 PASS / FAIL；门控由 PM 依据独立验证方结论裁决。

---

## 4. 已评估未采纳项（留痕）

- **`docs/architecture_design.md` L555（ADR-17 Context）的 `REQ-FUNC-IB-20（§2.5）`**：经检索，`architecture_design.md` 自身**不存在 §2.5 标题**（该 §2.5 仅存在于 `requirements_spec.md` L324「RAG 检索与多智能体编排」）。**判定：接受现状，不落盘**。理由：① 该引用在**同一从句**内紧随需求 ID（`REQ-FUNC-IB-20`）出现，「§」显然指**需求文档**的章节，专业读者无实质歧义；② 本补遗的指令预算（≤3）已用于**两处声明不一致 / 悬空引用**（真实缺陷）与**一处结构缺句**（内部一致性），此项属**风格可读性**，优先级最低；③ 若 PM 仍希望显化，建议留待下一轮（须另行核验锚点唯一性）。
- **`docs/architecture_design.md` §1.4 与他处命名冲突**：本补遗**不**改动文档自有 §1.4「请求上下文传播」的标题或编号（A-18 采取「消解引用」而非「改编号」的更低风险路径）。

---

## 5. 落盘后自检清单（交 PM 机械执行）

1. Grep 三条 `anchor`，确认计数各为 **1**（M-34 须用行首行尾锚定，规避 L922 同形行）。
2. 执行 3 次 Edit：`M-34`（REPLACE，行级）→ `A-18`（REPLACE，串级）→ `M-35`（INSERT_AFTER，**首行为空行**）。
3. 复核 `module_design.md` §5 表格**列数仍为 4**（转义 `\|` 未破坏表格）；`SessionStore` 行**键名与默认值**仍为 `IB_SESSION_BACKEND` / `memory`。
4. 复核 `architecture_design.md` L848 项目符号**其余措辞逐字未变**，且**全文不再出现 `A 部` 形式的暂存包引用**。
5. 复核两份文件 **version / revision / status 未变**（`1.4.0` / `R8` / `DRAFT_FOR_GATE_REVIEW`）；**未**新增 REQ / 模块 / 端口 / IFC / ADR / 依赖边。
6. 本补遗**不**产生任何门控结论；门控由 PM 裁定。
