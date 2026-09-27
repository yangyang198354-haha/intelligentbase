# REV-11-2 增量修订包（APPLY PACKAGE · 模块侧 A 部）

**文档编号**: APPLY-REV-11-2-INTELBASE-001C
**版本**: 0.1.0
**状态**: DRAFT（**待 PM 门控**；仅含落盘指令，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: `docs/module_design.md` 1.3.0（R7）→ **1.4.0（R8）**，指令 **M-01 ~ M-17**（M-18 ~ M-33 + 自检见 D 部）

| 分部 | 文件 | 内容 |
|------|------|------|
| **A 部** | `docs/rev11_group_b_apply_package.md` | 修订总览 + 架构侧指令 **A-01 ~ A-10** |
| **B 部** | `docs/rev11_group_b_apply_package_arch_b.md` | 架构侧指令 **A-11 ~ A-17** + 架构侧自检 + §verify |
| **C 部（本文件）** | `docs/rev11_group_b_apply_package_module_a.md` | 模块侧指令 **M-01 ~ M-17** |
| **D 部** | `docs/rev11_group_b_apply_package_module_b.md` | 模块侧指令 **M-18 ~ M-33** + 模块侧自检 + §verify |

> **为何分四个分部**：REV-11-2 共 50 条指令，其**完整权威文本**超出本代理单次写入的载荷上限（输出网关截断）。为保证「权威文本可被逐字落盘」，按**目标文件 + 段落序号**切分为四个分部。**四部合计才是 REV-11-2 的完整修订包**；**不因此新增任何 REQ / 模块 / 端口 / 依赖边**。
> **交付形态说明**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对两份目标文件发起任何写入**，而是产出 APPLY-READY 修订包，由 PM 以 Edit **机械落盘**（先例：`docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md`）。
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。本包每条均已核验（计数见 D 部 §2）。

---

## 1. 权威内容正文（模块侧 M-01 ~ M-17）

> `INSERT_AFTER` 条的插入点为该锚点**所在行的行尾之后**。凡 `new_string` **以空行开头**者已显式标注 —— 该空行用于与其上方段落 / 表格分隔，**不得省略**。

### M-01 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<version>1.3.0</version>`
- new_string:

```
<version>1.4.0</version>
```

- rationale: 版本号 1.3.0（R7）→ 1.4.0（R8）。

### M-02 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<revision>R7</revision>`
- new_string:

```
<revision>R8</revision>
```

- rationale: 修订号 R7 → R8。

### M-03 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>`
- new_string:

```
<invocation_id>INV-GROUP_B-INTELBASE-006</invocation_id>
```

- rationale: 调用 ID 同步为本轮 `INV-GROUP_B-INTELBASE-006`。

### M-04 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>`
- new_string:

```
    <input path="docs/requirements_spec.md" version="1.3.0" status="APPROVED"/>
```

- rationale: 需求侧已升至 v1.3.0；输入版本同步。

### M-05 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>`
- new_string:

```
    <input path="docs/user_stories.md" version="1.3.0" status="APPROVED"/>
```

- rationale: 用户故事已升至 v1.3.0（含 US-IB-19 / US-IB-20）；输入版本同步。

### M-06 · `docs/module_design.md` · REPLACE
- anchor / old_string: `<input path="docs/architecture_design.md" version="1.3.0" revision="R7" status="DRAFT_FOR_GATE_REVIEW"/>`
- new_string:

```
    <input path="docs/architecture_design.md" version="1.4.0" revision="R8" status="DRAFT_FOR_GATE_REVIEW"/>
```

- rationale: 与 A 部落盘后的 `architecture_design.md` 1.4.0（R8）保持一致。

### M-07 · `docs/module_design.md` · INSERT_AFTER
- anchor（**两行块**；核验：第 1 行子串在文件内出现 1 次）:

```
未修改 FreeArk 任何文件；需求侧文档只读；未写入任何凭据或配置值（只登记键名）。
    </rev>
```

- **说明**：该锚点的第 1 行是 R7 `<rev>` 元素的**段末子串**（唯一），第 2 行是 R7 元素的**闭合行**。插入点为闭合行**行尾之后**（即 R7 元素之后）。
- new_string:

```
    <rev no="R8" date="2026-09-27" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-006" basis="GROUP_A REV-11-1 下游贯通（REQ-FUNC-IB-20 补入 US-IB-19 / US-IB-20 与 11 组 AC 后的设计覆盖闭环）">
      **不新增模块、不新增端口、不新增依赖边**：会话状态 / 持久化策略 / 完成产物 / 确认中间态的类型化契约并入 **MOD-IB-01**；键名登记与值域显式化并入 **MOD-IB-02**；流式终态与可见性判据并入 **MOD-IB-21**；恢复判定与确认门装配语义并入 **MOD-IB-22**；会话恢复端点与 fail-closed 准入并入 **MOD-IB-23**；确认中间态的呈递与决策回传渲染约束并入 **MOD-IB-24**。新增 IFC 编号 **298~308**（11 条，全部类型化、frozen dataclass / Protocol、零第三方依赖）；**IFC-IB-285 仍预留未分配**。`IFC-IB-221/222` 的**签名文本不改**（仅补齐其悬置引用的 `SessionState` 定义）、`IFC-IB-233` 的 `payload: dict` **签名文本不改**（仅新增其载荷类型 `ResumePayload`）；`IB_SESSION_BACKEND` 键名与默认值不变（**仅扩展值域**，沿用 R2 先例）。既有 MOD-IB-01~26、`IFC-IB-001~297`、14 个端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（纯追加；零新增边的再声明见 §4.2.3）。增补位置：R8 性质段、§2.1 五组数据结构与 R8 说明、§2.2 R8 增记与 §2.2.3 R8 IFC 段号索引、§3 的 MOD-IB-01/02/21/22/23/24 增补、§4.2.3 R8 无环性再声明、§7.3 四条规范化补充、§7.4 两行降级、§8 R8 离线可测单元、§9.1 IB-20 行与 R8 覆盖闭环段、§9.6 R8 覆盖率再声明、§11 R8 自检。需求侧文档（v1.3.0）只读；未修改 FreeArk 任何文件；未写入任何凭据或配置值（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）。
    </rev>
```

- rationale: 追加 R8 修订元素；R1 / R2 / R7 三行既有元素**一行不删**。

### M-08 · `docs/module_design.md` · REPLACE
- anchor / old_string: `**版本**: 1.3.0 (R7)`
- new_string:

```
**版本**: 1.4.0 (R8)
```

- rationale: 正文版本行同步（其余 `| **状态**: ... | **日期**: ...` 部分不变）。

### M-09 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `（见 §9.5；另见 `architecture_design.md` [ARCH-ASSUMPTION-A7]）。`（即 R7 性质段的段末）
- new_string（**首行为空行**）:

```

**R8 性质**: 本修订为**追加式增量**（GROUP_A REV-11-1：REQ-FUNC-IB-20「流式输出契约与会话生命周期」补入 US-IB-19 / US-IB-20 与 11 组 AC 后的**设计覆盖闭环**），**只追加、不改写**：**不新增模块、不新增端口、不新增依赖边**。会话状态（`SessionState` / `SessionTurn`）、持久化策略枚举、完成产物（`CompletionPayload` / `CitationItem`）与确认中间态（`ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`）的类型化契约并入 **MOD-IB-01**（`IFC-IB-298~301`，其中 **IFC-IB-298 补齐 `IFC-IB-221/222` 的既有悬置引用，不改其签名文本**）；键名登记与值域显式化并入 **MOD-IB-02**（`IFC-IB-304`）；流式终态单发与可见性判据并入 **MOD-IB-21**（`IFC-IB-302/303`）；恢复判定与确认门装配语义并入 **MOD-IB-22**（`IFC-IB-305/306`，其中 **IFC-IB-305 类型化 `IFC-IB-233` 的 `payload: dict`，不改其签名文本**）；会话恢复端点与 fail-closed 准入并入 **MOD-IB-23**（`IFC-IB-307`）；确认中间态的呈递与决策回传渲染约束并入 **MOD-IB-24**（`IFC-IB-308`）。新增 `IFC-IB-298 ~ 308`（**IFC-IB-285 仍预留未分配**）。既有 MOD-IB-01~26、`IFC-IB-001~297`、14 个端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（零新增边的再声明见 §4.2.3）。**OQ-IB-07 / OQ-IB-08 保持开放**（架构默认取值见 `architecture_design.md` §10.1 R8 行与 ADR-17）。
```

- rationale: 在 R7 性质段之后、R2 性质段之前插入 R8 性质段（保持「新在前、旧在后」既有排列）。

### M-10 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `conflict: bool`；`errors: tuple[ValidationErrorItem, ...]` | |`（即 §2.1 表末行末）
- new_string:

```
| `SessionState` / `SessionTurn`（R8 新增，定义于 MOD-IB-01；**补齐** `IFC-IB-221/222` 的既有悬置引用） | `SessionState`: `session_key: str`；`project_id: str`；`actor_id: str`；`turns: tuple[SessionTurn, ...]`；`gate: ConfirmationGateState 或 None`；`updated_at: str`。`SessionTurn`: `role: Literal["user","assistant"]`；`text: str`；`citations: tuple[CitationItem, ...]`；`created_at: str` |
| `SessionPersistencePolicy` / `SessionStateLossOutcome`（R8 新增，定义于 MOD-IB-01） | `SessionPersistencePolicy` = `Literal["in_process","external"]`（默认 `in_process`，**须显式声明**）。`SessionStateLossOutcome` = `Literal["fail_closed_restart_required"]`（**唯一取值**：状态丢失时只允许安全失败） |
| `CompletionPayload` / `CitationItem`（R8 新增，定义于 MOD-IB-01） | `CompletionPayload`: `citations: tuple[CitationItem, ...]`（**可为空元组**，无引用即空、不臆造）；`had_content: bool`（空内容边界）。`CitationItem`: `doc_id: str`；`doc_name: str`；`page_or_section: str`；`locator: str`；`score: float`（**均为定位信息；不内联字节、不含正文全文**） |
| `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`（R8 新增，定义于 MOD-IB-01） | `ConfirmationPrompt`: `gate_id: str`；`expert_name: str`；`summary: str`（**由接入方构造**，骨架不生成业务话术）。`ConfirmationDecision`: `gate_id: str`；`approved: bool`。`ConfirmationGateState`: `gate_id: str`；`prompt: ConfirmationPrompt`；`decision: ConfirmationDecision 或 None`（`None` = 待决策） |
| `StreamEventKind` **值域追加成员**（R8，定义于 MOD-IB-01） | 既有 6 个成员（`reasoning` / `content` / `degraded` / `related_images` / `error` / `done`）**一字不动**；**追加** `confirmation_required`（确认中间态的呈递事件；**仅在 `IB_CONFIRMATION_GATE_ENABLED=true` 时出现**） |
```

- rationale: 补 §2.1 的字段级定义；**全是追加行**，既有行的字段集不变。

### M-11 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5）。`（即 §2.1 R7 说明的段末）
- new_string（**首行为空行**）:

```

**R8 说明（字段集不变式续）**：以上**五组为追加**，R1 / R2 / R7 既有结构（`ParsedChunk` / `RetrievedChunk` 与 R2 三行、R7 四行）的字段**均不变**。`SessionState` 是**既有悬置引用的补齐**：`IFC-IB-221/222` 早已引用该类型但 §2.1 **从未定义**，本轮补齐其字段级定义，**`IFC-IB-221/222` 的签名文本一字不改**。`SessionStateLossOutcome` 的**唯一取值** `fail_closed_restart_required` 使「重启丢弃待确认状态 = **安全失败**」成为**类型层事实**而非纪律约定（AC-IB-20-05）；`CompletionPayload.citations` **可为空元组**使「无引用即空、不臆造」成为结构事实（AC-IB-19-05）。全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5 延续）。
```

- rationale: 声明「字段集不变式」在 R8 继续成立，并点明 `SessionState` 是补齐而非新增语义。

### M-12 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `（同 `CollectionResolver` 的「唯一入口」精神；ADR-15）。`（即 §2.2 R7 增记的段末）
- new_string（**首行为空行**）:

```

**R8 增记（不新增端口；类型化既有载荷）**：端口数仍为 **14**（`SessionStore` 仍为 **3 方法** `IFC-IB-221~223`，**方法数与签名一字不改**）。R8 的两处「类型化既有载荷」遵循 **IFC-IB-282 先例**（只定义载荷类型、不改父签名）：① **IFC-IB-298** 补齐 `IFC-IB-221/222` 悬置引用的 `SessionState` 定义；② **IFC-IB-305** 类型化 `IFC-IB-233` 的 `payload: dict`（改为语义等价的类型化载荷），**`IFC-IB-233` 的签名文本与参数个数不变**。另：装配表键 `IB_SESSION_BACKEND` 的**值域**由 `memory` 扩展为 `memory 或 external`，**键名与默认值（`memory`）不变** —— 沿用 R2 对 `IB_EMBED_BACKEND` 的「**仅扩展值域；键名与默认值不变**」先例（§5）。
```

- rationale: 明确 R8 不新增端口、不改既有签名；值域扩展沿用 R2 先例。

### M-13 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。`（即 §2.2.2 R7 编号规范的段末）
- new_string（**首行为空行**）:

```

### 2.2.3 R8 新增 IFC 段号索引（追加式编号；IFC-IB-001~297 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-298 | MOD-IB-01 | `SessionState` / `SessionTurn` 字段级定义（**补齐** `IFC-IB-221/222` 的悬置引用；不改其签名） | §3 MOD-IB-01 |
| IFC-IB-299 | MOD-IB-01 | 枚举 `SessionPersistencePolicy`（`in_process` / `external`）与 `SessionStateLossOutcome`（唯一取值 `fail_closed_restart_required`） | §3 MOD-IB-01 |
| IFC-IB-300 | MOD-IB-01 | `CompletionPayload` / `CitationItem`（完成事件结构化产物；`citations` 可空、`had_content` 标空内容边界） | §3 MOD-IB-01 |
| IFC-IB-301 | MOD-IB-01 | `ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`；`StreamEventKind` **追加**成员 `confirmation_required` | §3 MOD-IB-01 |
| IFC-IB-302 | MOD-IB-21 | `completion_event(payload: CompletionPayload 或 None) -> StreamEvent`（终态恰一次单发；其后无 `content`；不臆造） | §3 MOD-IB-21 |
| IFC-IB-303 | MOD-IB-21 | `is_user_visible(kind: StreamEventKind) -> bool`（纯函数；`reasoning` 默认不可见；内部产物永不映射为可见 `kind`） | §3 MOD-IB-21 |
| IFC-IB-304 | MOD-IB-02 | 配置**键名登记与值域显式化**（**仅键名，不含值**）：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`；`IB_SESSION_BACKEND` 值域扩展 | §3 MOD-IB-02 |
| IFC-IB-305 | MOD-IB-22 | `ResumePayload`（`session_key: str`；`decision: ConfirmationDecision 或 None`）—— **类型化** `IFC-IB-233` 的 `payload: dict`，**不改其签名文本** | §3 MOD-IB-22 |
| IFC-IB-306 | MOD-IB-22 | `can_resume(state: SessionState 或 None, gate_id: str, payload: ResumePayload) -> bool`（纯函数；状态丢失 / 未携决策 / 归属不符 → `False` = fail-closed） | §3 MOD-IB-22 |
| IFC-IB-307 | MOD-IB-23 | `POST /api/chat/resume`（SSE，`Authorization` 头）→ 续跑流 或 `403` 或 `404`/`409`（fail-closed）或 `503` | §3 MOD-IB-23 |
| IFC-IB-308 | MOD-IB-24 | 前端对 `confirmation_required` 的**呈递与决策回传**约束（与答复片段可区分；未决策不继续） | §3 MOD-IB-24 |

**R8 编号规范（强制，延续 R2 / R7）**：新增号只许**追加**（本轮取 **298 ~ 308**）；`IFC-IB-001 ~ 297` 的号、名、签名、字段集**一字不动**；**`IFC-IB-285` 仍预留未分配**（不得被本轮占用或改义）；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。
```

- rationale: 与 §2.2.1（R2）/ §2.2.2（R7）同构，给出 R8 的 IFC 段号索引。

### M-14 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `**frozen dataclass / Protocol，纯 stdlib、零第三方依赖**；**无实现体**。`（即 MOD-IB-01 的 `IFC-IB-287` 契约段末）
- new_string:

```
  - **IFC-IB-298（R8 新增）**: 数据结构 `SessionState` / `SessionTurn`（字段级定义见 §2.1 R8 行）。**用途**：补齐 `IFC-IB-221/222` 的既有悬置引用（`SessionStore.load/save` 的 `SessionState`），**不改 `IFC-IB-221/222` 的签名文本**；**frozen dataclass、纯 stdlib、无实现体**。
  - **IFC-IB-299（R8 新增）**: 枚举 `SessionPersistencePolicy` = `Literal["in_process","external"]`（默认 `in_process`，**须显式声明**）；`SessionStateLossOutcome` = `Literal["fail_closed_restart_required"]`（**唯一取值**，使「状态丢失 = 安全失败」成为类型层事实，AC-IB-20-05）。
  - **IFC-IB-300（R8 新增）**: 数据结构 `CompletionPayload`（`citations: tuple[CitationItem, ...]` **可为空元组**；`had_content: bool`）与 `CitationItem`（`doc_id` / `doc_name` / `page_or_section` / `locator` / `score`，**均为定位信息，不内联字节、不含正文全文**）。供 `IFC-IB-302` 的单发完成事件使用（AC-IB-19-02 / 19-05）。
  - **IFC-IB-301（R8 新增）**: 数据结构 `ConfirmationPrompt`（`gate_id` / `expert_name` / `summary: str` **由接入方构造**）/ `ConfirmationDecision`（`gate_id` / `approved: bool`）/ `ConfirmationGateState`（`gate_id` / `prompt` / `decision: ConfirmationDecision 或 None`）；`StreamEventKind` **值域追加**成员 `confirmation_required`（**既有 6 个成员一字不动**）。**骨架只承载通道，不判定业务语义、不生成确认话术**（ADR-09 / ADR-17）。
```

- rationale: 在 MOD-IB-01 的契约清单末尾追加 4 条（插入点在该模块 `- **依赖模块**:` 行之前，仍在列表内）。

### M-15 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）；**REQ-FUNC-IB-25 / IB-26 / IB-27（R7，辅：只承载新增契约与第 14 个端口，见 IFC-IB-287）**`
- new_string:

```
- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）；**REQ-FUNC-IB-25 / IB-26 / IB-27（R7，辅：只承载新增契约与第 14 个端口，见 IFC-IB-287）**；**REQ-FUNC-IB-20（R8，辅：会话状态 / 持久化策略 / 完成产物 / 确认中间态的类型化契约落点，见 IFC-IB-298~301）**
```

- rationale: 按 G1（设计可追溯性）补登记 R8 的覆盖归属。

### M-16 · `docs/module_design.md` · REPLACE
- anchor / old_string: `- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）、**IB-25 / IB-26 / IB-27（R7 新增：定义文档的装载 / 白名单 / 完备性校验与派生）**；REQ-NFR-IB-02、IB-07`
- new_string:

```
- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）、**IB-25 / IB-26 / IB-27（R7 新增：定义文档的装载 / 白名单 / 完备性校验与派生）**、**IB-20（R8 辅：会话持久化策略与确认门开关的键名登记与值域显式化，见 IFC-IB-304）**；REQ-NFR-IB-02、IB-07
```

- rationale: 补登记配置侧对 IB-20 的辅助归属（键名登记与值域显式化）。

### M-17 · `docs/module_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `**IFC-IB-297（R7 新增）**: 新增配置**键名**（**仅登记键名，不含值**）：`IB_DEFINITION_DOC_PATH`（定义文档路径）、`IB_VISUAL_CONFIG_ENABLED`（可视化配置页开关）`（即 MOD-IB-02 契约清单末条）
- new_string:

```
  - **IFC-IB-304（R8 新增）**: 配置**键名登记与值域显式化**（**仅登记键名，不含任何值**）：
    - `IB_CONFIRMATION_GATE_ENABLED`：确认中间态开关，**默认 `false`**（默认不启用即零行为差异；**OQ-IB-07 保持开放**）。
    - `IB_SESSION_PERSISTENCE_POLICY`：会话持久化策略，取值 `in_process`（默认）或 `external`；**须显式声明**（未声明即启动期报错，AC-IB-20-02）；v1 不提供 `external` 适配器（[ARCH-ASSUMPTION-A8]）。
    - `IB_REASONING_STREAM_ENABLED`：思考分区流式开关，**默认 `false`**（AC-IB-19-03）。
    - `IB_SESSION_BACKEND`：**值域扩展**为 `memory`（默认）或 `external`；**键名与默认值不变**（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域」先例）。
```

- rationale: 插入点在 MOD-IB-02 的 `- **依赖模块**: MOD-IB-01` 行之前，仍在契约列表内；**只登记键名、不含值**。
