# REV-11-2 增量修订包（APPLY PACKAGE · 架构侧）

**文档编号**: APPLY-REV-11-2-INTELBASE-001A
**版本**: 0.1.0
**状态**: DRAFT（**待 PM 门控**；本包仅含落盘指令，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: `docs/architecture_design.md` 1.3.0（R7）→ **1.4.0（R8）**，指令 **A-01 ~ A-17**
**配套包**: `docs/rev11_group_b_apply_package_module.md`（`docs/module_design.md` 1.3.0（R7）→ **1.4.0（R8）**，指令 M-01 ~ M-33）
**本阶段边界**: 仅架构与模块设计（GROUP_B）。不含实现代码、测试用例、部署脚本；允许接口签名、类型注解与数据结构定义。FreeArk 仓库全程只读。

> **交付形态说明（务必先读一）**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对两份目标文件发起任何写入**，而是产出 APPLY-READY 修订包，由 PM 以 Edit **机械落盘**。此形态与既有先例 `docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md` 一致。
> **为何拆成两个包（务必先读二）**：REV-11-2 共 50 条指令（A-01 ~ A-17 + M-01 ~ M-33），其**完整权威文本**超出本代理单次写入的载荷上限（受输出网关截断）。为保证「权威文本可被逐字落盘」，按**目标文件**切分为两个 APPLY 包：本包（架构侧）+ 配套包（模块侧）。**两包合计才是 REV-11-2 的完整修订包**；两包共用同一个 `invocation_id` 与同一套编号纪律。**不因此新增任何 REQ / 模块 / 端口 / 依赖边。**
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。本包每条均已核验（计数见 §4）。

---

## 1. 修订总览

### 1.1 版本与状态变更

| 文件 | 旧版本 | 新版本 | 旧状态 | 新状态（本包建议值） | mode |
|------|--------|--------|--------|----------------------|------|
| `docs/architecture_design.md` | 1.3.0（R7） | **1.4.0（R8）** | DRAFT_FOR_GATE_REVIEW | **DRAFT_FOR_GATE_REVIEW** | REVISED_PENDING_GATE |
| `docs/module_design.md` | 1.3.0（R7） | **1.4.0（R8）** | DRAFT_FOR_GATE_REVIEW | **DRAFT_FOR_GATE_REVIEW** | REVISED_PENDING_GATE |
| `docs/tech_stack.md` | 1.0.0 | **不改**（理由见 §1.4） | — | — | NO_CHANGE |

> **状态门控纪律**：本包**不**把状态写为 APPROVED / ACCEPTED。两份文档保持既有 `DRAFT_FOR_GATE_REVIEW`（待 PM 门控签署）。文件头**保留**既有 `<revision_history>` 的 R1 / R2 / R7 元素（**一行不删**），仅**追加** R8 元素。
> **落盘后**：两文档 `<revision>` 由 `R7` → `R8`，`<version>` 由 `1.3.0` → `1.4.0`，`<invocation_id>` 由 `INV-GROUP_B-INTELBASE-002` → `INV-GROUP_B-INTELBASE-006`；`<inputs>` 中两份需求侧文档由 `1.2.0` → `1.3.0`（模块侧另有 `architecture_design.md` → `1.4.0 / R8`）。

### 1.2 新增编号一览（全部为**追加**，不重排、不删除）

**新增 IFC（11 条）：IFC-IB-298 ~ IFC-IB-308**

| 新增编号 | 内容 | 归属模块 | 关联 AC | 落盘指令 |
|----------|------|----------|---------|---------|
| **IFC-IB-298** | `SessionState` / `SessionTurn` 字段级定义（**补齐** IFC-IB-221/222 的既有悬置引用；**不改其签名**） | MOD-IB-01 | AC-IB-20-01 | M-10 / M-14 |
| **IFC-IB-299** | 枚举 `SessionPersistencePolicy`（`in_process` 或 `external`）/ `SessionStateLossOutcome`（唯一取值 `fail_closed_restart_required`） | MOD-IB-01 | AC-IB-20-02 / 20-05 | M-10 / M-14 |
| **IFC-IB-300** | `CompletionPayload` / `CitationItem`（完成事件结构化产物；`citations` 可空、`had_content` 标空内容边界） | MOD-IB-01 | AC-IB-19-02 / 19-05 | M-10 / M-14 |
| **IFC-IB-301** | `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`；**追加** `StreamEventKind` 成员 `confirmation_required` | MOD-IB-01 | AC-IB-20-03 / 20-04 | M-10 / M-14 |
| **IFC-IB-302** | `completion_event(payload) -> StreamEvent`（终态**恰一次**单发；其后无 `content`；不臆造） | MOD-IB-21 | AC-IB-19-01 / 19-02 / 19-05 | M-19 |
| **IFC-IB-303** | `is_user_visible(kind) -> bool`（**纯函数**：`reasoning` 默认不可见；内部产物永不映射为可见 `kind`） | MOD-IB-21 | AC-IB-19-03 / 19-04 | M-19 |
| **IFC-IB-304** | 配置**键名登记与值域显式化**（**仅键名、不含值**）：新增 `IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`；`IB_SESSION_BACKEND` 值域扩展 | MOD-IB-02 | AC-IB-20-02 / 20-03 / 19-03 | M-17 |
| **IFC-IB-305** | `ResumePayload`（`session_key: str`；`decision: ConfirmationDecision 或 None`）—— **类型化** IFC-IB-233 既有 `payload: dict`，**不改其签名文本** | MOD-IB-22 | AC-IB-20-05 | M-21 |
| **IFC-IB-306** | `can_resume(state, gate_id, payload) -> bool`（**纯函数**：状态丢失 / 未携决策 / 归属不符 → `False` = fail-closed） | MOD-IB-22 | AC-IB-20-04 / 20-05 | M-21 |
| **IFC-IB-307** | `POST /api/chat/resume`（SSE，`Authorization` 头）→ 续跑流 或 `403` 或 `404`/`409`（fail-closed）或 `503` | MOD-IB-23 | AC-IB-20-04 / 20-05 / 20-06 | M-23 |
| **IFC-IB-308** | 前端对 `confirmation_required` 的**呈递与决策回传**约束（与答复片段可区分；未决策不继续） | MOD-IB-24 | AC-IB-20-04 | M-25 |

**新增 ADR（1 条）：ADR-17** —— 「可选手动确认中间态」的承载方式与状态丢失语义；**3 候选方案**（A 骨架内置业务确认语义 / **B 装配期开关 + 类型化会话状态 + 恢复端点 + fail-closed** / C 完全下放接入方），**Option B 选定**；关联 AC-IB-20-02 / 20-03 / 20-04 / 20-05。落盘指令 **A-12**。

**未新增**：无新 REQ（REQ-FUNC 仍 **27**）、无新模块（仍 **26**）、无新端口（仍 **14**）、无新依赖边（§4.1 逐行不变）、无新 NFR。

### 1.3 本轮要补的「设计缺口」（为何不是重复设计）

REQ-FUNC-IB-20 的**设计与模块归属已存在**（`module_design.md` §9.1 的 `| IB-20 |` 行、§3 MOD-IB-21 / 22、§7.3；`architecture_design.md` §1.3 的 `SessionStore` 可替换点、§6 会话生命周期段）。**R8 不重写这些**。R8 只补**此前真正缺席**者：

| # | 缺口 | 证据 | R8 落点 |
|---|------|------|---------|
| G1 | **设计可追溯性缺席** | §9.1 `| IB-20 |` 行只有 `IB-20` 三字，未登记 **US-IB-19 / US-IB-20** 与其 11 组 AC；MOD-IB-21 / 22 的「覆盖需求」只有 REQ 无 AC | M-18 / M-20 / M-22 / M-24 / M-30 / M-32 |
| G2 | **`SessionState` 是悬置引用** | IFC-IB-221 / 222 的签名引用 `SessionState`，但 §2.1 **全文未定义**该结构 | M-10 / M-14（**IFC-IB-298**） |
| G3 | **持久化策略与丢失语义无类型化落点** | AC-IB-20-02 要求策略**显式声明**；AC-IB-20-05 要求重启丢弃待确认状态 = fail-closed；现无枚举、无键名 | M-10 / M-12 / M-14 / M-17（**IFC-IB-299 / 304**）+ §5 值域扩展 |
| G4 | **完成事件的结构化产物无载荷类型** | AC-IB-19-02 / 19-05 要求 `done` 一次性附引用清单、空内容不臆造；现仅 IFC-IB-224 的 `done` 字面 | M-10 / M-14 / M-19（**IFC-IB-300 / 302**） |
| G5 | **思考分区「可选且默认不启用」无规范化点** | AC-IB-19-03；现 §7.3 只列 `reasoning`（若可得），未写默认不启用、不混帧 | M-10 / M-14 / M-19（**IFC-IB-301 / 303 / 304**） |
| G6 | **内部子任务产物不外流无帧级判据** | AC-IB-19-04；ADR-09 只说「骨架不见业务语义」，未落「内部产物永不映射为可见 kind」 | M-19 / M-26（**IFC-IB-303**） |
| G7 | **确认中间态无类型化契约、无装配开关、无恢复端点** | AC-IB-20-03 / 20-04 / 20-05；`gate` 节点写着「机制保留、默认关闭」但**无键名、无结构、无端点** | M-10 / M-14 / M-17 / M-19 / M-21 / M-23 / M-25 / M-26 / **A-12**（**IFC-IB-301 / 304 / 305 / 306 / 307 / 308 + ADR-17**） |
| G8 | **`resume` 的载荷未类型化** | AC-IB-20-05；IFC-IB-233 的 `payload: dict` 无字段 | M-21（**IFC-IB-305**，沿用 IFC-IB-282 先例：类型化载荷而不改父签名） |
| G9 | **§4.1 无新增边须显式再声明** | 门控「无循环依赖」；R2 / R7 均有 §4.2.x 再声明，R8 缺 | M-29（新增 §4.2.3） |

### 1.4 `docs/tech_stack.md` 不改的理由（默认 = 不改，此处给出论证）

R8 **未引入任何新的第三方依赖、未改任何选型、未改任何版本 pin**：

1. **新增结构全部是纯 stdlib**：`SessionState` / `SessionTurn` / `CompletionPayload` / `CitationItem` / `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState` / `ResumePayload` 均为 **frozen dataclass**（定义于 L0 的 MOD-IB-01，该层**零第三方依赖**，REQ-NFR-IB-01）；两个枚举为 `Literal` 类型别名；`can_resume` / `is_user_visible` / `completion_event` 为**纯函数**。
2. **载体未变**：`POST /api/chat/resume`（IFC-IB-307）复用**同一个** Django `StreamingHttpResponse` + `text/event-stream` SSE 载体（ADR-11-R1），**不引 Channels、不引 Redis、不引任何新库**。
3. **无新端口、无新适配器**：`external` 持久化只是**已声明值域**，v1 **不提供适配器**（[ARCH-ASSUMPTION-A8]），故**不新增**任何驱动 / 客户端依赖。
4. **键名登记不构成选型变更**：三个新键名登记在 `module_design.md`（IFC-IB-304）；`tech_stack.md` §1.2 的键名清单**不在本包落盘范围**（若 PM 要求两处同步，**属另行立项**，本代理不擅自扩围 —— 见 §5 的 PM 决策项 ②）。

### 1.5 不变约束（门控硬线，逐条声明）

| 不变项 | 现状 | R8 是否改动 |
|--------|------|-------------|
| 模块总数 | **26**（MOD-IB-01 ~ 26） | **不改**（无新模块） |
| 端口总数 | **14** | **不改**（`SessionStore` 仍是 3 方法，其表行**不动**） |
| `IFC-IB-001 ~ 297` 的号 / 名 / 签名 / 字段集 | 一字不动 | **不改**（新增 298~308 为纯追加） |
| `IFC-IB-285` | 预留未分配 | **仍预留未分配** |
| `IFC-IB-131` 既有重号 | 登记不修（残余项 R-9） | **登记不修** |
| §4.1 依赖边清单 | 26 行 | **逐行不改**（零新增边） |
| DAG 无环性 | 构造性证明成立 | **不改**（M-29 再声明） |
| REQ→MOD 覆盖 | 27/27 REQ-FUNC + 14 NFR | **不改**（无新 REQ） |
| ADR 总数 | 16 | **16 → 17**（新增 ADR-17，含 3 方案） |
| `tech_stack.md` | 无改动需要 | **不改** |

### 1.6 编号纪律声明（哪些编号族「未改动」）

- `docs/architecture_design.md`：**ADR-01 ~ ADR-16 的 ID、Status、Context、Options、Decision、Consequences 一字不动**（R8 只**新增** ADR-17，并在新增的 §2.0.3 复核表中**声明**既有 16 条 R8 下不受影响）；`[ARCH-ASSUMPTION-A1 ~ A7]`、`[TBD-T1 ~ T20]`、`OQ-IB-01 ~ 08`、DR-01 ~ 08、§1.3 既有 14 行、§3.3 FM-1 ~ FM-8 **均不改**。
- `docs/module_design.md`：**MOD-IB-01 ~ 26 的 ID 与职责句、`IFC-IB-001 ~ 297`、14 个端口名、§4.1 依赖边 26 行、§5 装配表行、§6 状态机、§7.1 / §7.2 表、§10 FreeArk 映射表**均不改动。
- **编号族辨析（防误判）**：`AC-IB-19-*` / `AC-IB-20-*` 中的 `19` / `20` 是**用户故事序号**（沿用 `AC-IB-<US序号>-<两位序号>` 既有约定），与需求编号 `REQ-FUNC-IB-19` / `REQ-FUNC-IB-20` **不属同一编号族**；`US-IB-19/20` 亦与 `MOD-IB-19/20`、`IFC-IB-19x/20x` **不属同一编号族**。三者不构成冲突、不产生引用歧义。

---

## 2. 权威内容正文（架构侧 A-01 ~ A-17）

> 本节给出每条的**完整落盘文本**，PM 可**逐字**落盘。`REPLACE` 条的 `old_string` 与 `anchor` 相同（除特别注明）；`INSERT_AFTER` 条只需 `anchor` 定位，插入点为该锚点**所在行的行尾之后**。凡 `new_string` **以空行开头**者，已在条目中显式标注「**首行为空行**」——其作用是与其上方段落 / 表格分隔，**不得省略**。

### A-01 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `<version>1.3.0</version>`
- new_string:

```
<version>1.4.0</version>
```

- rationale: 版本号 1.3.0（R7）→ 1.4.0（R8）。

### A-02 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `<revision>R7</revision>`
- new_string:

```
<revision>R8</revision>
```

- rationale: 修订号 R7 → R8。

### A-03 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `<invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>`
- new_string:

```
<invocation_id>INV-GROUP_B-INTELBASE-006</invocation_id>
```

- rationale: 调用 ID 同步为本轮 `INV-GROUP_B-INTELBASE-006`。

### A-04 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `<input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>`
- new_string:

```
    <input path="docs/requirements_spec.md" version="1.3.0" status="APPROVED"/>
```

- rationale: 需求侧已升至 v1.3.0（GROUP_A REV-11-1）；输入版本同步。

### A-05 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `<input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>`
- new_string:

```
    <input path="docs/user_stories.md" version="1.3.0" status="APPROVED"/>
```

- rationale: 用户故事已升至 v1.3.0（含 US-IB-19 / US-IB-20）；输入版本同步。

### A-06 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `未写入任何凭据值。"/>`
- new_string:

```
    <rev version="1.4.0" revision="R8" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-006" note="R8 增量贯通（GROUP_A REV-11-1：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）：① 新增 ADR-17（「可选手动确认中间态」的承载方式与状态丢失语义；3 候选方案，Option B 选定），ADR 数 16 → 17；② 新增 §2.0.3 R8 影响复核表（ADR-01~17 逐条：既有 16 条在 R8 下均不受影响——其中 ADR-09 判『不受影响，且 R8 是其应用』、ADR-11 判『不受影响，R8 复用其载体』；新增 1 条；无一条跳过）；③ §1.3 可替换点表追加 R8 注（SessionStore 值域扩展 memory 或 external、恢复准入路径、状态丢失 fail-closed）；④ §6 增补『（R8）流式与会话的四条规范化补充』（增量推送与终态单发 / 完成附结构化产物 / 思考分区默认不启用且内部产物永不外流 / 会话状态与确认中间态）；⑤ §8 新增 [ARCH-ASSUMPTION-A8]（v1 默认持久化策略 = 进程内）；⑥ §9 新增 [TBD-T21]（会话状态容量与恢复并发）；⑦ §10.1 新增 OQ-IB-07 / OQ-IB-08 架构默认取值落地行、§10.3 追加 R8 自检。不变约束：模块数 26、端口数 14、IFC-IB-001~297 一字不动（新增 298~308）、§4.1 依赖边逐行不变（零新增边）、DAG 无环、覆盖 27/27 REQ-FUNC + 14 NFR、tech_stack.md 未改（无新第三方依赖）。需求侧文档与 FreeArk 仓库未改动；未写入任何凭据值。"/>
```

- rationale: 追加 R8 修订元素，**不改** R1 / R2 / R7 三行既有元素。

### A-07 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `**版本**: 1.3.0（R7 增量）`
- new_string:

```
**版本**: 1.4.0（R8 增量）
```

- rationale: 正文版本行同步（其余 `| **状态**: ... | **日期**: ...` 部分不变）。

### A-08 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `R1 / R2 时点基线 24/24 以括注保留）。`（即 R7 修订摘要段的段末子串）
- new_string（**首行为空行**）:

```

**R8 修订摘要（GROUP_A REV-11-1 下游贯通：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）**: 需求侧已补入 **US-IB-19「流式交付最终答复」（AC-IB-19-01 ~ 05）** 与 **US-IB-20「会话生命周期」（AC-IB-20-01 ~ 06）**。本轮**不重写**既有设计（ADR-11-R1 的流式载体、ADR-09、§1.3 的 `SessionStore` 可替换点、§6 会话生命周期段、`module_design.md` §3 MOD-IB-21 / 22、§7.3 均保留），只补此前**真正缺席**者：新增 **ADR-17**（「可选手动确认中间态」的承载方式与状态丢失语义；**3 候选方案**，Option B 选定），**ADR 数 16 → 17**；新增 **§2.0.3 R8 影响复核表**（**既有 16 条 ADR 在 R8 下全部不受影响**——ADR-09 判「不受影响，且 R8 是其应用」、ADR-11 判「不受影响，R8 复用其载体」；**新增 1 条**；**无一条跳过**）；§1.3 追加 R8 注；§6 增补流式与会话四条规范化补充；§8 新增 A8；§9 新增 [TBD-T21]；§10.1 / §10.3 追加 R8 行。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、端口数（**14**）、`IFC-IB-001~297` 编号体系、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、**`tech_stack.md` 未改**（无新第三方依赖）。
```

- rationale: 在 R7 摘要之后、R1 摘要之前插入 R8 摘要（保持「新在前、旧在后」的既有排列）。

### A-09 · `docs/architecture_design.md` · REPLACE
- anchor / old_string: `**输入**: `requirements_spec.md` v1.2.0（APPROVED）、`user_stories.md` v1.2.0（APPROVED）`
- new_string:

```
**输入**: `requirements_spec.md` v1.3.0（APPROVED）、`user_stories.md` v1.3.0（APPROVED）
```

- rationale: 与 A-04 / A-05 同步，正文「输入」行亦须为 v1.3.0。

### A-10 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `| AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |`（§1.3 可替换点表末行）
- new_string（**首行为空行**）:

```

**（R8）会话状态可替换点的值域扩展与恢复准入路径**：`SessionStore` 端口与「默认内存实现、语义 fail-closed」的表述**不变**。R8 仅做两件事：① **值域显式化** —— 装配表键 `IB_SESSION_BACKEND` 的取值域由 `memory` **扩展**为 `memory 或 external`，**键名与默认值（`memory`）不变**（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域；键名与默认值不变」先例）；`external` 在 v1 **无适配器**（[ARCH-ASSUMPTION-A8]），属**已声明未实现**，不改既有装配语义。② **恢复准入路径显式化** —— 会话恢复的准入顺序固定为「**鉴权（`Authorization` 头）→ 归属断言（`session_key` 前缀）→ `SessionStore.load` → `can_resume` → 续跑**」；**任一前置不满足或状态不存在即 fail-closed**（`403` / `404` / `409`，**不新建会话**）。**「重启丢弃待确认状态」= 安全失败（fail-closed），非静默续跑** —— 该语义由 MOD-IB-22 的纯函数 `can_resume`（IFC-IB-306）与枚举 `SessionStateLossOutcome`（唯一取值 `fail_closed_restart_required`，IFC-IB-299）在**类型层**保证（AC-IB-20-02 / AC-IB-20-05）。
```

- rationale: §1.3 表内不适合塞入长段；以独立段落紧随其后，声明值域扩展与恢复准入路径。
