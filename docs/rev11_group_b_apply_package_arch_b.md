# REV-11-2 增量修订包（APPLY PACKAGE · 架构侧 B 部）

**文档编号**: APPLY-REV-11-2-INTELBASE-001B
**版本**: 0.1.0
**状态**: DRAFT（**待 PM 门控**；仅含落盘指令，不含对既有文件的任何改动）
**mode**: APPLY_PACKAGE
**invocation_id**: INV-GROUP_B-INTELBASE-006
**revision**: R8（GROUP_B 增量，REV-11-2）
**作者**: system-architect (via pm-orchestrator)
**创建日期**: 2026-09-27
**本包范围**: `docs/architecture_design.md` 1.3.0（R7）→ **1.4.0（R8）**，指令 **A-11 ~ A-17**（A-01 ~ A-10 见 A 部）

**REV-11-2 完整修订包的四个分部（同一 `invocation_id`，同一套编号纪律）**:

| 分部 | 文件 | 内容 |
|------|------|------|
| **A 部** | `docs/rev11_group_b_apply_package.md` | 修订总览 + 架构侧指令 **A-01 ~ A-10** |
| **B 部（本文件）** | `docs/rev11_group_b_apply_package_arch_b.md` | 架构侧指令 **A-11 ~ A-17** + 架构侧一致性自检 + §verify 锚点清单 |
| **C 部** | `docs/rev11_group_b_apply_package_module_a.md` | 模块侧指令 **M-01 ~ M-17** |
| **D 部** | `docs/rev11_group_b_apply_package_module_b.md` | 模块侧指令 **M-18 ~ M-33** + 模块侧一致性自检 + §verify 锚点清单 |

> **为何分四个分部**：REV-11-2 共 50 条指令，其**完整权威文本**超出本代理单次写入的载荷上限（输出网关截断）。为保证「权威文本可被逐字落盘」，按**目标文件 + 段落序号**切分为四个分部。**四部合计才是 REV-11-2 的完整修订包**；**不因此新增任何 REQ / 模块 / 端口 / 依赖边**。
> **交付形态说明**：本代理**不具备 Edit 工具**。依据本项目既定纪律（对既有产出文件的修订**一律**使用定向编辑，`Write` 仅用于新建文件），**本代理未对两份目标文件发起任何写入**，而是产出 APPLY-READY 修订包，由 PM 以 Edit **机械落盘**（先例：`docs/rev06_ui_config_apply_package.md`、`docs/rev11_stream_session_apply_package.md`）。
> **落盘前锚点核验（强制）**：`Grep` 每条 `anchor`，确认在目标文件内**出现次数 == 1**，再执行 Edit。本包每条均已核验（计数见 §2）。

---

## 1. 权威内容正文（架构侧 A-11 ~ A-17）

> `INSERT_AFTER` 条的插入点为该锚点**所在行的行尾之后**。凡 `new_string` **以空行开头**者已显式标注 —— 该空行用于与其上方段落 / 表格分隔，**不得省略**。

### A-11 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `REQ→MOD 覆盖矩阵**由 24/24 同步为 27/27**（v1.2.0 需求总数，见 §10.3）。`（即 §2.0.2 的 R7 复核小结段末）
- new_string（**首行为空行**）:

```

### 2.0.3 R8 影响复核表（GROUP_A REV-11-1 下游贯通；追加式复核，不改写既有结论）

> 本节**只新增**，§2.0（R1）/ §2.0.1（R2）/ §2.0.2（R7）三次复核**原样保留**。**逐条复核，无一条跳过。**

| ADR | R8 判定 | 复核理由 |
|-----|---------|---------|
| ADR-01 | **R8 不受影响** | 向量库抽象层与 Qdrant 集成方式未动；会话状态不经向量库承载 |
| ADR-02 | **R8 不受影响** | `ib-embed` 的形态值域（`http` / `inproc` / `fake`）与服务端归属未动；会话状态不涉 embedding |
| ADR-03 | **R8 不受影响** | 部署形态（禁 Docker / 系统级安装）未动；v1 的持久化策略只取进程内取值，不引入新部署单元 |
| ADR-04 | **R8 不受影响** | `Scope` 仍为必填、`session_key` 前缀断言沿用同一隔离精神（FM-7）；**未新增隔离维度、未改 `CollectionResolver`** |
| ADR-05 | **R8 不受影响** | `BlobStore` 与图片字节口径未动；完成事件的结构化产物只携带引用定位（`CitationItem`），**不内联字节、不涉 BlobStore** |
| ADR-06 | **R8 不受影响** | LLM 提供方与调用语义未动；确认门与恢复不改变 LLM 调用契约 |
| ADR-07 | **R8 不受影响** | 切分与嵌入的本地化口径未动 |
| ADR-08 | **R8 不受影响** | 入库流水线与台账语义未动；会话状态**不入台账**（v1 为内存实现，不持久化到台账） |
| ADR-09 | **R8 不受影响，且 R8 是其应用** | 「骨架不见业务语义」在 R8 被**具体化**为「内部子任务产物永不映射为可见 `kind`」（IFC-IB-303，AC-IB-19-04）——仍不引入业务语义，只是把既有边界落到**帧级判据** |
| ADR-10 | **R8 不受影响** | 异步入库的队列载体与租约语义未动 |
| ADR-11 | **R8 不受影响，R8 复用其载体** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；新增的 `POST /api/chat/resume`（IFC-IB-307）**复用同一载体**，不引 Channels、不引 Redis；「禁止 `?token=`」纪律**扩展至该新端点** |
| ADR-12 | **R8 不受影响** | OCR 与页面渲染两个端口及降级语义未动 |
| ADR-13 | **R8 不受影响** | 「故障与空结果可区分」在 R8 被沿用：完成事件**不臆造**引用（`citations` 可为空元组 + `had_content: bool`，IFC-IB-300）；会话状态丢失走 **fail-closed**，与运行期读路径 fail-open 在时间轴与契约上分离 |
| ADR-14 | **R8 不受影响** | 可视化配置的编辑模型未动；R8 不涉定义文档 |
| ADR-15 | **R8 不受影响** | 定义文档单一真源（双向同源）未动；R8 不涉派生视图 |
| ADR-16 | **R8 不受影响** | 装配期 fail-fast 准入闸门未动；R8 的「会话状态丢失 = fail-closed」发生在**运行期**，与装配期闸门分属不同时点，二者不冲突 |
| **ADR-17（R8 新增）** | **新增** | 「可选手动确认中间态」的承载方式与状态丢失语义（3 候选方案，Option B 选定） |

**R8 复核小结**：**既有 16 条 ADR 在 R8 下全部不受影响**（其中 ADR-09 判「不受影响，且 R8 是其应用」、ADR-11 判「不受影响，R8 复用其载体」）；**新增 1 条**（ADR-17）→ **ADR 总数 16 → 17**。**无一条 ADR 未复核**。R8 的所有改动**不触及**：模块数（**26，未新增**）、端口数（**14**）、`IFC-IB-001~297` 编号体系、**§4.1 依赖边（零新增边）**与 DAG 无环性、REQ→MOD 覆盖矩阵（**27/27 REQ-FUNC + 14 NFR**）、`tech_stack.md`（**未改**）。
```

- rationale: 门控要求「每条 ADR 显式复核、不跳过」；R8 新增本表覆盖 ADR-01 ~ ADR-17 共 17 行。

### A-12 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `其错误可读性由 AC-IB-18-02 把关。`（即 ADR-16 的 Consequences 段末）
- new_string（**首行为空行**）:

```

### ADR-17 「可选手动确认中间态」的承载方式与状态丢失语义（R8 新增）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-20（§2.5）末句明确「**可选手动确认中间态**」与「**会话恢复**」两条子条款；用户故事侧已补 **US-IB-20**（AC-IB-20-02 持久化策略须**显式声明**、AC-IB-20-03 机制**存在但默认不启用且不绑定业务语义**、AC-IB-20-04 呈递与决策回传、AC-IB-20-05 **携决策则续跑 / 未携带或状态丢失则 fail-closed**、AC-IB-20-06 归属断言）与 **US-IB-19**（AC-IB-19-01 ~ 05 流式交付契约）。需求原文用「**可选**」与「**机制保留、默认关闭**」表述，并把该点登记为 **OQ-IB-07（仍开放）**。既有架构只给出「机制保留、默认关闭」（§6 会话生命周期段、§10.1）与「状态存于 `SessionStore` 端口、语义 fail-closed」，**未规定**：开关的承载位置、中间态的结构、决策回传的路径、以及「状态丢失」的判定与取值。相关既有决策：**ADR-09**（骨架不见业务语义）、**ADR-11-R1**（SSE 载体与「禁止 `?token=`」纪律）、**ADR-13**（故障与空结果可区分）。**约束**：本 ADR **不得**为满足「确认」而把业务语义引入骨架，**不得**绕过 OQ-IB-07 的开放性（默认必须关闭）。
- **Options**:
  - **A 骨架内置业务确认语义**（参照 FreeArk 的 `interrupt()` 强制确认门）：优—接入方零配置即得确认能力。缺—**违反「不绑定业务语义」与「默认不启用」**（AC-IB-20-03）；把「哪些动作需要确认」这类**业务判定**写进骨架，与 ADR-09 冲突；且 FreeArk 的 `interrupt()` 是**无开关**的强确认门，与 OQ-IB-07 的默认关闭口径相反。**已评估未采纳**。
  - **B 装配期开关（默认关闭）+ 类型化会话状态 + 专用恢复端点 + 状态丢失 fail-closed**：优—开关默认关闭（**不启用即零行为差异**）；中间态以**类型化结构**承载（`ConfirmationPrompt` / `ConfirmationDecision` / `ConfirmationGateState`），`summary` 文案**由接入方构造**（骨架不生成业务话术，守住 ADR-09）；呈递与回传经**既有 SSE 载体 + 一个专用端点**（复用 ADR-11-R1，不引新依赖）；「状态丢失即 fail-closed」由**纯函数 + 单一取值枚举**在类型层保证（AC-IB-20-02 / 05）。缺—须新增若干契约与一个端点（成本已收敛为**纯追加**）。**选定**。
  - **C 完全下放接入方**（骨架只留一个回调位，其余自建）：优—骨架最薄。缺—**无法满足 AC-IB-20-04 的「呈递与决策回传」**（需求要求该机制在基座内成立），且会诱导接入方**各自实现会话状态**，破坏「唯一入口」与 FM-7 的隔离纪律。**已评估未采纳**。
- **Decision**: **Option B**，并绑定 4 条强制约束：
  1. **默认不启用**：装配期开关 `IB_CONFIRMATION_GATE_ENABLED`（**仅键名**，IFC-IB-304）**默认 `false`**；为 `false` 时**零行为差异**（不发 `confirmation_required`、不写 `gate` 状态、`resume` 不可用）。**OQ-IB-07 保持开放**，本 ADR **不裁决**「是否应默认启用」。
  2. **不绑定业务语义**：骨架**不判定**「哪些动作需要确认」，也不生成确认文案；`ConfirmationPrompt.summary` 为 `str`，**由接入方构造**；`expert_name` 只作定位用。骨架只做「**呈递 + 等待 + 回传**」的通道。该边界与 ADR-09 同构。
  3. **呈递与续跑**：呈递 = 在流内发**一个** `confirmation_required` 事件（`StreamEventKind` **追加**该成员，既有 6 个成员不动，IFC-IB-301）；决策回传 = 新端点 `POST /api/chat/resume`（IFC-IB-307，SSE，`Authorization` 头），**从不新建会话**，只从**已存在的中间态**继续；续跑后仍以 `done` 收束（`done` 之后不再有该次交互的内容片段，AC-IB-19-01）。
  4. **状态丢失 = fail-closed**：持久化策略**必须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`，取值 `in_process` 或 `external`，**v1 默认 `in_process`**；未显式声明即启动期报错）；重启后待确认状态丢弃时，`can_resume`（IFC-IB-306，**纯函数**）必返回 `False`，端点返回 `404` / `409`（**不静默新建、不静默续跑**）；**「安全失败」语义由枚举 `SessionStateLossOutcome` 的唯一取值 `fail_closed_restart_required`（IFC-IB-299）在类型层固定**（与 ADR-13、§7.4 的 fail-closed 口径同精神：宁可明确失败，不可带病继续）。
- **Consequences**: 正向—AC-IB-20-02 / 03 / 04 / 05 与 AC-IB-20-06（归属断言）全部有落点；承接并**具体化** REQ-FUNC-IB-20 的两条子条款，**不新增需求**；「不绑定业务语义」与「默认不启用」成为**契约级事实**而非纪律约定；`external` 持久化只**声明值域**，v1 不引适配器（**零新依赖**），留出可升级路径。负向—新增失败面 `404` / `409`（会话或待确认状态不存在 / 已丢失）与 `403`（归属断言），须在客户端给出可读回执（IFC-IB-308）；会话状态容量与恢复并发**未经实测**，登记为 **[TBD-T21]**；`in_process` 是**刻意保守**的 v1 默认（跨重启不保状态），若接入方要求跨重启续跑，须回到 `external` 值域并另行立项适配器（[ARCH-ASSUMPTION-A8]）。
- **R8 新增说明**: 本 ADR 为**纯追加**；`ADR-01 ~ ADR-16` 的 ID / Status / Context / Options / Decision / Consequences **一字不动**（R8 复核见 §2.0.3）。
```

- rationale: 补「确认中间态」承载方式的架构决策；**含 3 个候选方案**（满足「每决策点 ≥2 方案」硬线），其中 A / C 留「已评估未采纳」痕迹。

### A-13 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `**会话生命周期**：`（即 §6 的会话生命周期整段，锚点为其段首，插入点在该**段末**）
- **注意**：本条的插入点务必在该**整段结束**之后（该段末子串为 `会话隔离属 FM-7。`），而非段首之后。
- new_string（**首行为空行**）:

```

**（R8）流式与会话的四条规范化补充（REQ-FUNC-IB-20；US-IB-19 / US-IB-20）**：

1. **增量推送与终态单发**（AC-IB-19-01）：`content` 为**增量**片段，客户端**不得**等待 `done` 才渲染；**完成事件恰一次单发**，其后**不再有**该次交互的任何内容片段；终态构造经 `completion_event`（IFC-IB-302）。空内容边界：无可交付正文时，**不发空的 `content` 帧**，只发完成事件且 `had_content=false`（AC-IB-19-05）。
2. **完成事件附结构化产物**（AC-IB-19-02 / 19-05）：终态事件携带 `CompletionPayload`（`citations: tuple[CitationItem, ...]` + `had_content: bool`，IFC-IB-300）；`citations` **可为空元组**（无引用即空，**不编造引用**）；引用项为**定位信息**（`doc_id` / `doc_name` / `page_or_section` / `locator` / `score`），**不内联字节、不含正文全文**。
3. **思考分区与内部产物**（AC-IB-19-03 / 19-04）：`reasoning` 分区为**可选增强且默认不启用**（`IB_REASONING_STREAM_ENABLED` 默认 `false`，仅键名，IFC-IB-304）；**内部子任务产物（专家内部步骤、路由判定、转交与咨询痕迹）永不映射为可见 `kind`**，该判据落在纯函数 `is_user_visible(kind)`（IFC-IB-303）—— 对齐 ADR-09「骨架不见业务语义」与 FreeArk 的 `INTERNAL_NOSTREAM_TAG` / `_run_subexpert` 不外流口径；**默认不混帧**（同一事件不承载两个分区的语义）。
4. **会话状态与确认中间态**（AC-IB-20-02 / 20-03 / 20-04 / 20-05）：会话状态经 `SessionStore` 端口承载（**默认内存实现**，键 `session_key = f"{project_id}:{actor_id}:{session_id}"`）；**持久化策略须显式声明**（`IB_SESSION_PERSISTENCE_POLICY`，`in_process` 或 `external`，v1 默认 `in_process`），**重启丢弃待确认状态 = fail-closed**（`SessionStateLossOutcome` 唯一取值 `fail_closed_restart_required`，IFC-IB-299）；「可选手动确认中间态」**机制保留、默认关闭**（`IB_CONFIRMATION_GATE_ENABLED` 默认 `false`），**不绑定业务语义**，呈递与回传见 ADR-17。**OQ-IB-07 / OQ-IB-08 均保持开放**。
```

- rationale: 把 REQ-FUNC-IB-20 / US-IB-19 / US-IB-20 的规范点在架构侧一次落清（四条对应 11 组 AC）。

### A-14 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `须 PM 知悉并在 GROUP_C 施工顺序中体现 |`（即 §8 表 `[ARCH-ASSUMPTION-A7]` 行末）
- new_string:

```
| **ARCH-ASSUMPTION-A8**（R8 新增） | **v1 的会话持久化策略默认 = 进程内（`in_process`）**：`IB_SESSION_PERSISTENCE_POLICY` 取值 `in_process`（默认）或 `external`；`external` 为**已声明值域**，**v1 不提供适配器**（`IB_SESSION_BACKEND` 的值域扩展为 `memory` 或 `external`，默认 `memory`） | REQ-FUNC-IB-20 要求「会话恢复」与「持久化策略显式声明」，**未规定** v1 采哪种策略；AC-IB-20-02 只要求策略**显式**、AC-IB-20-05 只要求状态丢失时 **fail-closed** | 若接入方要求**跨重启续跑**，只需在 `external` 值域内新增一个 `SessionStore` 适配器（**上层零改动**，ADR-04 同精神），并据 [TBD-T21] 校准容量；**不影响 ADR-17 与既有 DAG** | **需 PM 确认**（v1 默认持久化策略；若判「v1 必须跨重启持久化」，须回 GROUP_A / 立项，架构层不自行扩围） |
```

- rationale: 把「v1 不跨重启持久化」这一**刻意默认**显式登记为假设，交 PM 确认（不自行扩围）。

### A-15 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `并作为 `tech_stack.md` §5.3「图库许可与体积」风险行的实测依据 |`（即 §9 表 `[TBD-T20]` 行末）
- new_string:

```
| **TBD-T21（R8 新增）** | **会话状态的容量与恢复并发**：并发会话数 × `SessionTurn` 上界下的**内存占用**；`POST /api/chat/resume`（IFC-IB-307）的**并发容量**（与 [TBD-T15] 同源，SSE 长连接占同步 worker）；待确认中间态的**丢失率**；需据此定 `MemorySessionStore` 的**保留时长 / 淘汰上界** | REQ-FUNC-IB-20；AC-IB-20-02 / AC-IB-20-05；ADR-17 | 决定是否需引入 `external` 适配器（[ARCH-ASSUMPTION-A8]）；并校准「会话失效」的可观测性与可读回执口径（IFC-IB-308）。**未经实测前不得给出容量结论** | |
```

- rationale: 会话容量与恢复并发属「必须目标机实测校准」项，按既有 TBD 纪律登记（不写入编造数值）。

### A-16 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `架构层不自行扩围或缩围 |`（即 §10.1 表末行末）
- new_string:

```
| **（R8）OQ-IB-07 / OQ-IB-08 的架构默认取值落地** | ① 写操作确认门（OQ-IB-07）在架构上如何承载；② 会话历史的作用范围（OQ-IB-08） | ① **机制保留、默认关闭**（`IB_CONFIRMATION_GATE_ENABLED` 默认 `false`，且**不绑定业务语义**；见 ADR-17）；② **会话内隔离**（`session_key` 前缀断言，FM-7），**不跨会话注入**历史 | **两项 OQ 均保持开放**，本修订**不裁决**「是否应默认启用确认门」或「历史是否跨会话」；架构层只落地「默认关闭 / 会话内隔离」的安全默认，**不裁决业务语义、不自行扩围** |
```

- rationale: 把两项仍开放的 OQ 的「架构默认取值」写清，同时显式声明**未越权裁决**。

### A-17 · `docs/architecture_design.md` · INSERT_AFTER
- anchor（核验次数 1）: `**不得混淆、不得改动**）。`（即 §10.3 自检末行末，文末最后一行）
- new_string:

```
- **（R8）REQ-FUNC-IB-20 的设计覆盖闭环已贯通**：需求侧补入 **US-IB-19 / US-IB-20**（11 组 AC）后，本轮新增 **ADR-17**（3 方案，Option B）与 **§2.0.3 R8 影响复核表**（**既有 16 条 ADR 全部不受影响**、新增 1 条、**无一条跳过**）；§1.3 追加 R8 注、§6 追加四条规范化补充、§8 新增 [ARCH-ASSUMPTION-A8]、§9 新增 [TBD-T21]、§10.1 追加 OQ 默认取值落地行；设计侧落点模块与 IFC 见 `module_design.md` §9.6。
- **（R8）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口数仍 **14**、`IFC-IB-001~297` 一字不动（新增 298~308）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.3）；REQ→MOD 覆盖 **27/27 REQ-FUNC + 14 NFR**（**无新 REQ**）。
- **（R8）「安全失败」为类型层事实**：会话状态丢失的 fail-closed 由 `SessionStateLossOutcome` 的**唯一取值** `fail_closed_restart_required`（IFC-IB-299）与纯函数 `can_resume`（IFC-IB-306）固定，**不依赖纪律约定**；`CompletionPayload.citations` 可为空元组使「不臆造引用」成为结构事实（IFC-IB-300）。
- **（R8）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` v1.3.0 / `user_stories.md` v1.3.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未作修改**；`tech_stack.md` **未改**（R8 无新第三方依赖，理由见 A 部 §1.4）；**未写入任何凭据值**（只登记键名：`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）。
```

- rationale: 按既有惯例在 §10.3 追加 R8 自检 bullet，供门控直接比对。

---

## 2. §verify 锚点核验清单（架构侧 A-01 ~ A-17）

| 指令 | 动作 | anchor（`Grep` 目标） | 核验次数 | 唯一性 |
|------|------|----------------------|----------|--------|
| A-01 | REPLACE | `<version>1.3.0</version>` | 1 | 通过 |
| A-02 | REPLACE | `<revision>R7</revision>` | 1 | 通过 |
| A-03 | REPLACE | `<invocation_id>INV-GROUP_B-INTELBASE-002</invocation_id>` | 1 | 通过 |
| A-04 | REPLACE | `<input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>` | 1 | 通过 |
| A-05 | REPLACE | `<input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>` | 1 | 通过 |
| A-06 | INSERT_AFTER | `未写入任何凭据值。"/>` | 1 | 通过 |
| A-07 | REPLACE | `**版本**: 1.3.0（R7 增量）` | 1 | 通过 |
| A-08 | INSERT_AFTER | `R1 / R2 时点基线 24/24 以括注保留）。` | 1 | 通过 |
| A-09 | REPLACE | `**输入**: `requirements_spec.md` v1.2.0（APPROVED）、`user_stories.md` v1.2.0（APPROVED）` | 1 | 通过 |
| A-10 | INSERT_AFTER | `| AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |` | 1 | 通过 |
| A-11 | INSERT_AFTER | `REQ→MOD 覆盖矩阵**由 24/24 同步为 27/27**（v1.2.0 需求总数，见 §10.3）。` | 1 | 通过 |
| A-12 | INSERT_AFTER | `其错误可读性由 AC-IB-18-02 把关。` | 1 | 通过 |
| A-13 | INSERT_AFTER | `**会话生命周期**：` 所在**整段段末** | 1（段首）/ 段末子串 `会话隔离属 FM-7。` 亦为 1 | 通过 |
| A-14 | INSERT_AFTER | `须 PM 知悉并在 GROUP_C 施工顺序中体现 |` | 1 | 通过 |
| A-15 | INSERT_AFTER | `并作为 `tech_stack.md` §5.3「图库许可与体积」风险行的实测依据 |` | 1 | 通过 |
| A-16 | INSERT_AFTER | `架构层不自行扩围或缩围 |` | 1 | 通过 |
| A-17 | INSERT_AFTER | `**不得混淆、不得改动**）。` | 1 | 通过 |

---

## 3. 一致性自检（架构侧）

1. **编号稳定性**：`ADR-01 ~ ADR-16` 的 ID / Status / Context / Options / Decision / Consequences **一字未改**（A-11 表仅**新增**行、A-12 仅**新增** ADR-17）；`[ARCH-ASSUMPTION-A1 ~ A7]`、`[TBD-T1 ~ T20]`、`OQ-IB-01 ~ 08`、DR-01 ~ 08、§1.3 既有 14 行、§3.3 FM-1 ~ FM-8 **均未改**。
2. **计数更新**：ADR 数 **16 → 17**（A-06 / A-08 / A-11 / A-12 / A-17 五处一致陈述）；模块数 **26**、端口数 **14**、REQ-FUNC **27/27**、NFR **14** 各处**未变**。
3. **两文件交叉引用一致**：A-11 引 `module_design.md` §4.2.3；A-12 引 IFC-IB-299 / 301 / 304 / 305 / 306 / 307 / 308；A-17 引 `module_design.md` §9.6 —— 与 C / D 部落盘后的编号**逐一对应**（IFC-IB-298 ~ 308 无跳号、无占位）。
4. **无残留旧版本号**：落盘后全文**不得**再出现 `1.3.0（R7 增量）`（A-07）、`INV-GROUP_B-INTELBASE-002`（A-03）与 `v1.2.0（APPROVED）`（A-04 / A-05 / A-09）；历史 `<rev>` 元素内**允许**保留旧版本号（属历史记录，**不得**改动）。
5. **无代码**：A-01 ~ A-17 全部为设计文本 / 表格行 / XML 元数据，**不含函数体、不含伪代码**。
6. **ADR 方案数**：ADR-17 含 **3 个候选方案**（A / B / C），其中 A / C 标注「已评估未采纳」，满足「每决策点 ≥2 方案」硬线。

---

## 4. 本包（B 部）自检声明

- 本包**只含落盘指令**，**未对** `docs/architecture_design.md` **发起任何写入**。
- 本包 **17 条**锚点（A-01 ~ A-17）全部经 `Grep` 核验，**出现次数均为 1**（A-13 以「段首锚点 + 段末子串」双重定位，二者均为 1）。
- 本包**未新增** REQ / 模块 / 端口 / 依赖边；**未新增** `IFC-IB-*`（IFC 新增全部在 C / D 部）；**新增 1 条 ADR**（ADR-17，含 3 方案）。
- 本包**未写入任何凭据值 / 配置值**（只登记键名）。
- **不声称任何门控结果**：门控裁决权在 PM。

### 需 PM 决策 / 知悉项（架构侧）

| # | 事项 | 本包立场 | 需 PM 的动作 |
|---|------|----------|--------------|
| ① | **ADR-17 是否必要** | R8 为「确认中间态 + 会话恢复」新增架构决策（3 方案）；若不新增，则 AC-IB-20-03 / 04 / 05 在架构侧**无决策留痕**，仅剩模块契约 | 若 PM 判「ADR-11-R1 + ADR-09 已足够、不需新 ADR」，则**跳过 A-12**，并把 A-06 / A-08 / A-11 / A-17 中「ADR 数 16 → 17」的表述**相应回退**（本代理不擅自改口径，等 PM 裁决） |
| ② | **`tech_stack.md` §1.2 键名清单是否同步** | 三个新键名（`IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）登记在 `module_design.md`（IFC-IB-304）；`tech_stack.md` **不在本包范围**（避免反复扩围） | 若 PM 要求两处同步，**请另行指派一轮**（本代理不擅自扩围） |
| ③ | **[ARCH-ASSUMPTION-A8]** | v1 默认持久化策略 = `in_process`（跨重启不保待确认状态，语义 fail-closed）；`external` 只声明值域、不配适配器 | 需 PM **确认**该默认；若判「v1 必须跨重启持久化」，**须回 GROUP_A / 立项**（属需求侧扩围） |
| ④ | **OQ-IB-07 / OQ-IB-08** | **保持开放**；R8 只落地「默认关闭 / 会话内隔离」的安全默认 | 知悉即可；架构层**不裁决**业务语义 |
