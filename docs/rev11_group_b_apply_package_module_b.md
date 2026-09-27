# REV-11-2 增量修订包（APPLY PACKAGE · 模块侧 B 部 + 收口）

**文档编号**: APPLY-REV-11-2-INTELBASE-001D
**版本**: 0.1.0
**状态**: DRAFT（**待 PM 门控**；仅含落盘指令，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: `docs/module_design.md` 1.3.0（R7）→ **1.4.0（R8）**，指令 **M-18 ~ M-33** + 模块侧自检 + §verify 锚点清单 + REV-11-2 全局收口

| 分部 | 文件 | 内容 |
|------|------|------|
| **A 部** | `docs/rev11_group_b_apply_package.md` | 修订总览 + 架构侧指令 **A-01 ~ A-10** |
| **B 部** | `docs/rev11_group_b_apply_package_arch_b.md` | 架构侧指令 **A-11 ~ A-17** + 架构侧自检 + §verify |
| **C 部** | `docs/rev11_group_b_apply_package_module_a.md` | 模块侧指令 **M-01 ~ M-17** |
| **D 部（本文件）** | `docs/rev11_group_b_apply_package_module_b.md` | 模块侧指令 **M-18 ~ M-33** + 模块侧自检 + §verify + 全局收口 |

> **为何分四个分部**：REV-11-2 共 50 条指令，其**完整权威文本**超出本代理单次写入的载荷上限（输出网关截断）。为保证「权威文本可被逐字落盘」，按**目标文件 + 段落序号**切分为四个分部。**四部合计才是 REV-11-2 的完整修订包**；**不因此新增任何 REQ / 模块 / 端口 / 依赖边**。
> **交付形态说明**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对两份目标文件发起任何写入**，而是产出 APPLY-READY 修订包，由 PM 以 Edit **机械落盘**（先例：`docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md`）。
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。本包每条均已核验（计数见 §2）。

---

## 1. 权威内容正文（模块侧 M-18 ~ M-33）

> `INSERT_AFTER` 条的插入点为该锚点**所在行的行尾之后**。凡 `new_string` **以空行开头**者已显式标注 —— 该空行用于与其上方段落 / 表格分隔，**不得省略**。

### M-18 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-FUNC-IB-20、IB-21；AC-IB-14-01（降级事件可见）`（MOD-IB-21）
- new_string:

```
- **覆盖需求**: REQ-FUNC-IB-20、IB-21；AC-IB-14-01（降级事件可见）；**US-IB-19（流式交付最终答复；AC-IB-19-01 ~ 05）、US-IB-20（会话生命周期；AC-IB-20-01 ~ 03）（R8 补登记）**
```

- rationale: 按 G1 补登记 US / AC 追溯（MOD-IB-21 承载流式契约与会话状态端口）。

### M-19 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `R2 只定义其 data）。`（即 `IFC-IB-282（R2）` 契约段的段末）
- new_string:

```
  - **IFC-IB-302（R8 新增）**: `completion_event(payload: CompletionPayload 或 None) -> StreamEvent`（**纯函数**：构造**唯一**的终态事件；`kind=done`；**恰一次单发**，其后**不再有**该次交互的任何 `content` 片段，AC-IB-19-01；`payload` 缺省时**不臆造**引用，AC-IB-19-05；**不发空的 `content` 帧**；`payload` 定义见 IFC-IB-300）。
  - **IFC-IB-303（R8 新增）**: `is_user_visible(kind: StreamEventKind) -> bool`（**纯函数**：`content` / `degraded` / `related_images` / `error` / `done` → `True`；`reasoning` **默认不可见**（受 `IB_REASONING_STREAM_ENABLED` 门控）；**内部子任务产物永不属于任何 `StreamEventKind` 可见取值**，故**永不外流**，AC-IB-19-04；**默认不混帧** —— 同一事件不承载两个分区的语义）。
```

- rationale: 插入点在 `- **依赖模块**: MOD-IB-01、MOD-IB-02、MOD-IB-04` 行之前，仍在契约列表内；`IFC-IB-224` / `IFC-IB-282` 的文本**不动**。

### M-20 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06`（MOD-IB-22）
- new_string:

```
- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06；**US-IB-20（会话生命周期；AC-IB-20-03 / 20-04 / 20-05）、US-IB-19（AC-IB-19-04）（R8 补登记）**
```

- rationale: 补登记（MOD-IB-22 承载确认门装配语义与恢复判定）。

### M-21 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `` `step_count: int`（上限 `MAX_EXPERT_STEPS = 8`） ``（即 MOD-IB-22 的 State 键行末）
- new_string:

```
  - **IFC-IB-305（R8 新增）**: `ResumePayload`（`session_key: str`；`decision: ConfirmationDecision 或 None`）—— **类型化** `IFC-IB-233` 的既有 `payload: dict`（**不改 `IFC-IB-233` 的签名文本与参数个数**；沿用 IFC-IB-282 先例）。`decision is None` = 未携带决策。
  - **IFC-IB-306（R8 新增）**: `can_resume(state: SessionState 或 None, gate_id: str, payload: ResumePayload) -> bool`（**纯函数**，无 IO：`state is None`（状态丢失）/ `state.gate` 为 `None` 或 `gate_id` 不符 / `payload.decision is None`（未携决策）→ **一律 `False`** = **fail-closed**；**仅当三门全过才 `True`**。AC-IB-20-04 / 20-05；配合 `SessionStateLossOutcome` 的唯一取值，使「安全失败」成为类型层事实）。
  - **确认门装配语义（R8，ADR-17）**: `IB_CONFIRMATION_GATE_ENABLED` **默认 `false`**；为 `false` 时 `gate` 节点**直接通过**（零行为差异：不写 `gate` 状态、不发 `confirmation_required`、`resume` 不可用）。为 `true` 时：`gate` 节点构造 `ConfirmationGateState`（`prompt.summary` **由接入方提供的业务构造器产出**，**骨架不生成业务话术**）并发出**一个** `confirmation_required` 事件后**挂起该会话**（保持中间态）；决策经 `POST /api/chat/resume`（IFC-IB-307）回传后经 `can_resume` 判定并续跑。**骨架不判定「哪些动作需要确认」**（ADR-09 / ADR-17 约束 2）。
```

- rationale: 插入点在 `- **依赖模块**: ...` 行之前，仍在契约列表内；`IFC-IB-231/232/233` 与 State 键**一字不动**。

### M-22 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23、**IB-25 / IB-27（R7 新增：定义文档的读写端点与装配期准入闸门）**；REQ-NFR-IB-09`（MOD-IB-23）
- new_string:

```
- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23、**IB-25 / IB-27（R7 新增：定义文档的读写端点与装配期准入闸门）**、**IB-20（R8 新增：会话恢复端点与 fail-closed 准入；US-IB-20 / AC-IB-20-04 ~ 20-06）**；REQ-NFR-IB-09
```

- rationale: 补登记（MOD-IB-23 承载 IFC-IB-307 与新准入顺序）。

### M-23 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `**新增键名不含任何值**。`（即 MOD-IB-23 的 R7 配置键不变声明段末）
- new_string:

```
  - **R8 新增端点（会话恢复；IFC-IB-307）**: `POST /api/chat/resume`（**SSE**，`Content-Type: text/event-stream`；**仅允许 `Authorization` 头**鉴权，**不接受 `?token=`**）→ 续跑流（`text/event-stream`）| `403`（归属断言失败，AC-IB-20-06）| `404` / `409`（会话或待确认状态**不存在 / 已丢失** → **fail-closed，不新建会话**，AC-IB-20-05）| `503`（容量，与 `IFC-IB-247` 同源，池满**快速失败**，[TBD-T15] / [TBD-T21]）。
  - **准入顺序（强制，R8）**: `鉴权（Authorization 头）→ 归属断言（session_key 前缀，FM-7）→ SessionStore.load（IFC-IB-221）→ can_resume（IFC-IB-306）→ 续跑（IFC-IB-233）`。**任一前置不满足即 fail-closed**，**不得**退化为「新建会话后重跑」。
  - **R8 配置声明（强制）**: `IB_SESSION_PERSISTENCE_POLICY` 须在 `ib-web` 单元的 `EnvironmentFile` 模板（`IFC-IB-262`）中**显式声明**（AC-IB-20-02）；**只登记键名，不写入任何值**。
```

- rationale: 插入点在 MOD-IB-24 小节标题之前；`IFC-IB-241 ~ 250` / `283` / `293 ~ 295` **一字不动**。

### M-24 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-FUNC-IB-09、IB-17、**IB-25（主）、IB-26（并列主，与 MOD-IB-22）、IB-27（辅）**`（MOD-IB-24）
- new_string:

```
- **覆盖需求**: REQ-FUNC-IB-09、IB-17、**IB-25（主）、IB-26（并列主，与 MOD-IB-22）、IB-27（辅）**；**IB-20（R8 新增：问答页对确认中间态与恢复的呈递、流式交付渲染；US-IB-20 / AC-IB-20-04、US-IB-19 / AC-IB-19-01、AC-IB-19-03）**
```

- rationale: 补登记（MOD-IB-24 承载 IFC-IB-308）。

### M-25 · `docs/module_design.md` · REPLACE
- anchor / old_string: `  - **前端不做校验的最终裁决者**：前端预校验仅为体验优化；**服务端校验器（IFC-IB-290）为唯一裁决者**（界面编辑与直接改文档**一视同仁**）。`
- **注意**：本条以该行**自身**替换为「该行 + 一个新的顶层列表项」。新列表项**必须顶格（`- ` 不带缩进）**，否则会被并入上方的 R2 渲染约束项。
- new_string:

```
  - **前端不做校验的最终裁决者**：前端预校验仅为体验优化；**服务端校验器（IFC-IB-290）为唯一裁决者**（界面编辑与直接改文档**一视同仁**）。
- **R8 问答页流式与确认约束（IFC-IB-308）**（R8 新增）:
  - **增量渲染**：`content` 片段到达即渲染，**不得等待 `done`**（AC-IB-19-01）；`done` 到达后**不再追加**该次交互的正文。
  - **完成与产物一次性呈现**：完成事件携带的结构化引用清单（`CompletionPayload`）在**该轮回答下方**一次性呈现；**无引用时不显示引用区**（不显示空占位、不臆造引用，AC-IB-19-05）。
  - **思考分区默认不渲染**：`reasoning` 分区**仅在服务端启用且明确标记为可见时**以可折叠区域呈现；**默认不渲染**（AC-IB-19-03）。
  - **确认中间态独立区呈现 + 决策回传**：收到 `confirmation_required` 时以**独立区域**呈现（**与答复片段视觉可区分**，不并入正文），经 `POST /api/chat/resume`（IFC-IB-307）回传 `ConfirmationDecision`；**未决策则界面不显示为「已完成」**、不自动继续（AC-IB-20-04）。
  - **恢复失败可读回执**：`404` / `409` / `403` 时给出可读提示（如「会话已失效，请重新发起或重新确认」），**不静默丢弃、不自动重跑**（AC-IB-20-05 / 20-06）。
  - **凭据不回显**：只显示**键名**，不显示任何值 / 掩码 / 前缀（延续 IFC-IB-296 口径）。
```

- rationale: 补前端侧对确认中间态与流式交付的渲染约束；`IFC-IB-256 ~ 259` / `284` / `296` **一字不动**。

### M-26 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `` 读取时断言前缀（FM-7）。 ``（即 §7.3 流式契约与会话段的段末）
- new_string（**首行为空行**）:

```

**（R8）流式与会话的四条规范化补充（REQ-FUNC-IB-20；US-IB-19 / US-IB-20）**：

1. **增量推送与终态单发**（AC-IB-19-01）：`content` 为增量片段，客户端不得等 `done`；完成事件**恰一次**，其后不再有该次交互的内容片段；终态构造经 `completion_event`（IFC-IB-302）。空内容时**不发空的 `content` 帧**（AC-IB-19-05）。
2. **完成事件附结构化产物**（AC-IB-19-02 / 19-05）：终态携带 `CompletionPayload`（IFC-IB-300）；`citations` **可为空元组**，**不编造引用**；引用项为定位信息，不内联字节、不含正文全文。
3. **思考分区与内部产物**（AC-IB-19-03 / 19-04）：`reasoning` **可选且默认不启用**（`IB_REASONING_STREAM_ENABLED` 默认 `false`）；**内部子任务产物永不映射为可见 `kind`**（`is_user_visible`，IFC-IB-303）；**不混帧**。
4. **会话状态与确认中间态**（AC-IB-20-02 / 20-03 / 20-04 / 20-05）：状态经 `SessionStore` 承载（默认内存实现）；**持久化策略须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`），**重启丢弃待确认状态 = fail-closed**（`SessionStateLossOutcome` 唯一取值）；确认门**机制保留、默认关闭、不绑定业务语义**，呈递与回传见 ADR-17；**OQ-IB-07 / OQ-IB-08 保持开放**。
```

- rationale: 与 `architecture_design.md` §6 的四条规范化补充**同构**（两文件口径一致，便于门控对读）。

### M-27 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `| ERROR | **fail-closed（配置读）**；对问答链路无影响 |`（即 §7.4 表末行末）
- new_string:

```
| **会话状态（待确认中间态）**（R8 新增） | 状态丢失 / 未携决策 / 归属不符 / 会话不存在 | `POST /api/chat/resume`（IFC-IB-307）返回 `404` / `409` / `403`；**不新建会话、不重跑、不静默续跑**（`can_resume` = `False`） | 「会话已失效，请重新发起或重新确认」 | WARN | **fail-closed（会话状态）** |
| **完成事件的结构化产物**（R8 新增） | 本轮无可交付引用（`citations` 为空）或无可交付正文 | **不臆造引用**（`citations=()`）、**不发空的 `content` 帧**；仅以完成事件收束（`had_content=false`），**不追加降级文案**（无引用 ≠ 降级） | 无感（无引用时不显示引用区） | INFO | **fail-open（增强项）**；对问答主链路无影响 |
```

- rationale: 按 §7.4 既有六列格式追加两行；**既有行一字不动**。

### M-28 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `配合 `InMemoryDefinitionDocumentStore` 即可在**无任何外部服务**下完成装配期全链路离线验证（AC-IB-18-05）。`（即 §8 R7 追加的离线可测单元段段末）
- new_string（**首行为空行**）:

```

**R8 追加的离线可测单元**（**纯函数、无外部 IO、无第三方依赖**）：**MOD-IB-21** 的 `is_user_visible`（IFC-IB-303，含「内部产物永不外流」与「默认不混帧」的判据）与 `completion_event`（IFC-IB-302，含「恰一次」「其后无 `content`」「不臆造」「不发空帧」）；**MOD-IB-22** 的 `can_resume`（IFC-IB-306，含「状态丢失 / 未携决策 / 归属不符 → `False`」的 fail-closed 三例）。配合 **`MemorySessionStore`**（§8 替身表既有行，**未改动**）即可在**无任何外部服务**下完成「会话 → 确认中间态 → 恢复」的**全链路离线验证**（AC-IB-19-01 ~ 05、AC-IB-20-02 ~ 06）。
```

- rationale: 按既有 §8 纪律登记 R8 的离线可测单元（纯函数直测）。

### M-29 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `不得新开编号更高的模块**。`（即 §4.2.2 末行末）
- new_string（**首行为空行**）:

```

### 4.2.3 R8 无环性再声明（零新增依赖边）

- **零新增依赖边**：R8 的全部新增落在 **MOD-IB-01 / 02 / 21 / 22 / 23 / 24** 内部（会话与确认的类型化契约 / 键名登记与值域显式化 / 终态与可见性判据 / 恢复判定与装配语义 / 恢复端点与准入 / 呈递与回传约束），**§4.1 依赖边清单逐行未改**；因此 `w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **不新增模块**：与 R7 同理 —— 会话状态与确认中间态**必然被 MOD-IB-21 / 22（低编号）持有并被 MOD-IB-23（组合根）装配**，若新开模块只能取 **≥27** 的编号，会产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**；故并入既有模块（§4.2.2 边界纪律继续适用）。
- **既有边被复用而非新增**：`IFC-IB-307` 的端点在 **MOD-IB-23**（既有边 `23 → 21 / 22` 已存在，无需新边）；`can_resume`（IFC-IB-306）与 `ResumePayload`（IFC-IB-305）定义在 **MOD-IB-22**（依赖 MOD-IB-01 为既有边）；`is_user_visible` / `completion_event` 在 **MOD-IB-21**（依赖 MOD-IB-01 为既有边）。
- **单一入口纪律未被绕开**：会话状态仍**只**经 `SessionStore`（MOD-IB-21 端口）读写，`session_key` 前缀断言（FM-7）沿用；前端仍**只**经 HTTP/SSE 契约（MOD-IB-24 → MOD-IB-23）取数，**不新增任何绕过路径**。
- 因此「编号即拓扑序」继续适用于 GROUP_C；R8 的**边界纪律同 §4.2.2 末句**：新增工件若被低编号模块（尤其组合根）依赖，**不得新开编号更高的模块**。
```

- rationale: 门控「无循环依赖」硬线；按 R2 / R7 惯例给出 R8 的无环性再声明。

### M-30 · `docs/module_design.md` · REPLACE
- anchor / old_string: `| IB-20 | 会话生命周期 | **MOD-IB-21** / 22 |`（§9.1）
- new_string:

```
| IB-20 | 会话生命周期（流式输出契约 + 会话生命周期；**R8 补设计覆盖**） | **MOD-IB-21** / 22, 23, 24, 01, 02（**US-IB-19 / AC-IB-19-01 ~ 05；US-IB-20 / AC-IB-20-01 ~ 06**） |
```

- rationale: 按 G1 把 `IB-20` 行从「三字」升级为「US / AC 可追溯」。

### M-31 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `AC 落点分别为 AC-IB-17-01~06、AC-IB-17-04 / AC-IB-18-01、AC-IB-18-01~06）。`（即 §9.1 「无缺口」段的段末）
- new_string（**首行为空行**）:

```

**（R8）REQ-FUNC-IB-20 的设计覆盖闭环**：需求侧补入 **US-IB-19**（流式交付最终答复；AC-IB-19-01 ~ 05）与 **US-IB-20**（会话生命周期；AC-IB-20-01 ~ 06）后，本需求的设计覆盖由「仅登记 REQ 与模块归属」升级为「**US / AC → ADR / IFC 逐条可追溯**」（见 §9.6 的逐 AC 映射表）：`ADR-17`（承载方式与状态丢失语义）+ `IFC-IB-298 ~ 308`（11 条类型化契约）+ §7.3 / §7.4 / §8 的相应补充。**本轮不重写既有设计**（`IFC-IB-221 ~ 225` / `IFC-IB-231 ~ 233` / `IFC-IB-247` 一字不动）。
```

- rationale: 与 §9.3 / §9.4 / §9.5 同构的「再声明」段落。

### M-32 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `本文件**不得**据此改写该文件。`（即 §9.5 末行末）
- new_string（**首行为空行**）:

```

### 9.6 R8 覆盖率再声明（REQ-FUNC-IB-20 的设计覆盖闭环）

**结论：27/27 REQ-FUNC + 14 REQ-NFR 覆盖达成，无新增缺口；REQ-FUNC-IB-20 由「模块归属已登记」升级为「US / AC 逐条可追溯」。**

| AC | 需求要点 | 设计落点（R8） | 状态 |
|----|----------|----------------|------|
| AC-IB-19-01 | 增量交付、终态恰一次单发 | `IFC-IB-302`（`completion_event`）；§7.3 补充 1 | **新增** |
| AC-IB-19-02 | 完成事件附结构化产物 | `IFC-IB-300`（`CompletionPayload` / `CitationItem`）+ `IFC-IB-302`；§7.3 补充 2 | **新增** |
| AC-IB-19-03 | 思考分区可选且默认不启用 | `IFC-IB-304`（`IB_REASONING_STREAM_ENABLED`，默认 `false`）+ `IFC-IB-303`；§7.3 补充 3 | **新增** |
| AC-IB-19-04 | 内部子任务产物不外流 | `IFC-IB-303`（`is_user_visible`：内部产物永不映射为可见 `kind`）；§7.3 补充 3 | **新增（ADR-09 的具体化）** |
| AC-IB-19-05 | 空内容边界、不臆造 | `IFC-IB-300`（`citations` 可空 + `had_content`）+ `IFC-IB-302`；§7.4 第二新增行 | **新增** |
| AC-IB-20-01 | 会话键与状态承载 | `IFC-IB-298`（`SessionState`，补齐悬置引用）+ 既有 `IFC-IB-221/222` + FM-7（§7.3） | **补齐既有缺口** |
| AC-IB-20-02 | 持久化策略须显式声明 | `IFC-IB-299`（枚举）+ `IFC-IB-304`（键名）+ `IFC-IB-307`；部署落点 `IFC-IB-262`（MOD-IB-25） | **新增** |
| AC-IB-20-03 | 机制存在、默认不启用、不绑定业务语义 | `IFC-IB-301`（结构 + `confirmation_required` 值域追加）+ `IFC-IB-304`（默认 `false`）+ `IFC-IB-306`；ADR-17 约束 1 / 2 | **新增** |
| AC-IB-20-04 | 呈递与决策回传 | `IFC-IB-301`（呈递）+ `IFC-IB-307`（回传端点）+ `IFC-IB-308`（界面约束）；ADR-17 约束 3 | **新增** |
| AC-IB-20-05 | 携决策则续跑 / 未携或丢失则 fail-closed | `IFC-IB-299`（唯一取值）+ `IFC-IB-305` + `IFC-IB-306`（`can_resume`）+ `IFC-IB-307`；§7.4 第一新增行 | **新增** |
| AC-IB-20-06 | 归属断言与不新建会话 | `IFC-IB-307`（`403` / `404` / `409`，准入顺序显式化）+ FM-7（§7.3） | **新增** |

**边界声明（R8）**：

- **既有设计一字未改**：`IFC-IB-221 ~ 225`（`SessionStore` 3 方法 + `StreamEvent` / `to_sse`）、`IFC-IB-231 ~ 233`（`build_graph` / `run` / `resume`）、`IFC-IB-247`（既有 SSE 端点）的**号 / 名 / 签名 / 字段集一字不动**；R8 只**追加** `IFC-IB-298 ~ 308`。
- **模块与依赖不变**：模块数仍 **26**、端口数仍 **14**、**§4.1 依赖边逐行未改**（§4.2.3）；REQ→MOD 覆盖仍 **27/27 + 14 NFR**（**无新 REQ**）。
- **OQ 处置**：**OQ-IB-07 / OQ-IB-08 均保持开放**；R8 只落地「默认关闭 / 会话内隔离」的**安全默认**，**不裁决业务语义**（ADR-17；`architecture_design.md` §10.1 R8 行）。
- **架构侧对应**：`architecture_design.md` 1.4.0（R8）的 **ADR-17**、**§2.0.3 R8 影响复核表**、§1.3 R8 注、§6 四条规范化补充、[ARCH-ASSUMPTION-A8]、[TBD-T21]。
```

- rationale: 本轮的**核心可追溯性交付**；按 §9.3 ~ §9.5 惯例新增 §9.6 再声明。

### M-33 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `` 只登记键名：`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；本阶段**止于 GROUP_B**。 ``（即 §11 自检末行末，文末最后一行）
- new_string:

```
    - **R8 自检（REQ-FUNC-IB-20 设计覆盖闭环，GROUP_A REV-11-1 下游贯通）**：
      - **覆盖闭环已贯通**：§9.1 的 `| IB-20 |` 行登记 **US-IB-19 / US-IB-20** 与 11 组 AC；§9.1 追加 R8 覆盖闭环段；**§9.6 给出逐 AC 映射表**（`AC-IB-19-01 ~ 05`、`AC-IB-20-01 ~ 06` 共 11 条**全部有落点**）；MOD-IB-21 / 22 / 23 / 24 / 01 / 02 的「覆盖需求」均补登记其 R8 归属。
      - **零新增模块 / 端口 / 依赖边**：模块数仍 **26**、端口数仍 **14**（`SessionStore` 仍 3 方法）；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 21 / 22 / 23 / 24（§4.2.3 给出无环性再声明与「为何不新增模块」的编号论证）。
      - **类型化未降级**：新增 `IFC-IB-298 ~ 308`（11 条）全部为 `name: type` + 可空性的**类型化契约**，均为 **frozen dataclass / 纯 stdlib、零第三方依赖**；`SessionStateLossOutcome` 的**唯一取值**使「状态丢失 = 安全失败」成为类型层事实；`CompletionPayload.citations` 可为空元组使「不臆造引用」成为结构事实。
      - **编号纪律未破**：`IFC-IB-001 ~ 297` 的号 / 名 / 签名 / 字段集**一字不动**（含 `IFC-IB-221/222` / `IFC-IB-233` 的签名文本）；新增 298 ~ 308 为**纯追加**；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。
      - **既有设计未被改写**：`IFC-IB-221 ~ 225`、`IFC-IB-231 ~ 233`、`IFC-IB-247`、§5 装配表既有行、§6 状态机、§7.1 / §7.2 表、§10 FreeArk 映射表**均未改动**；`IB_SESSION_BACKEND` **键名与默认值不变**（仅扩展值域，沿用 R2 先例）。
      - **OQ 未越权**：**OQ-IB-07 / OQ-IB-08 保持开放**；R8 只落地「默认关闭 / 会话内隔离」的安全默认，**不裁决**「是否应默认启用确认门」「历史是否跨会话」；架构层不自行扩围或缩围。
      - **边界合规**：R8 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；需求侧文档（`requirements_spec.md` v1.3.0 / `user_stories.md` v1.3.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **未改**（无新第三方依赖）；**未写入任何凭据或配置值**（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）；本阶段**止于 GROUP_B**。
```

- rationale: 按既有惯例在 §11 追加 R8 自检；插入点为文末最后一行之后（追加于文件尾）。
