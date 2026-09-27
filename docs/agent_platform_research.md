<file_header>
  <project>intelligentbase</project>
  <artifact>agent_platform_research</artifact>
  <path>docs/agent_platform_research.md</path>
  <doc_id>RESEARCH-INTELBASE-001</doc_id>
  <version>0.1.0</version>
  <status>APPROVED</status>
  <phase>GROUP_A / PHASE_01 — 需求规格增量：业界对标调研补充</phase>
  <author_agent>requirement-analyst</author_agent>
  <invocation_id>INV-GROUP_A-INTELBASE-002</invocation_id>
  <mode>RESEARCH_SUPPLEMENT</mode>
  <created_at>2026-09-27</created_at>
  <updated_at>2026-09-27</updated_at>
  <inputs>
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED" note="只读；本文件未修改"/>
    <input path="docs/user_stories.md" version="1.1.0" status="APPROVED" note="只读；本文件未修改"/>
  </inputs>
  <readonly_note>本文件**不修改**上述两份 APPROVED 输入。对其提出的任何增量一律以「候选 / 待确认」形式列出，由 PM / 用户裁决后再另行落盘。</readonly_note>
  <evidence_policy>
    每条「能力断言」尽量附官方 URL；无法确证处标注「待官方证实」或「官方文档未查到」。
    **执行环境限制（如实披露）**：本次执行中 WebFetch 对**所有**目标域（docs.dify.ai / microsoft.github.io / openai.github.io / docs.crewai.com / learn.microsoft.com / github.com / raw.githubusercontent.com 等）均返回
    「Unable to verify if domain ... is safe to fetch」，即**原始页面抓取全线不可用**。故本文件全部证据经 **WebSearch** 检索获得 —— 即「搜索引擎对官方页面的检索摘要 + 官方 URL 定位」，
    **不是**原始 HTML 抓取。凡仅见于第三方站点（社区仓库 / DeepWiki / 教程 / 博客）的结论，一律显式标注「待官方证实」，不作为官方证据使用。
  </evidence_policy>
  <scope_boundary>
    对外部开源项目**官方文档的事实归纳** + 与本项目现状的**差距对照** + **候选建议**。
    **不含**本项目的架构决策、模块设计、接口签名（IFC-*）、ADR、代码或配置实现。凡涉本项目者一律写为「候选需求点 / 待确认建议」并标注 `[候选 — 待 PM/用户确认]`。
  </scope_boundary>
  <credential_policy>本文档不记录任何密钥、令牌、口令或证书；外部项目的密钥处理做法仅以「机制」形式引用，不含任何真实值。</credential_policy>
  <revision_history>
    <rev version="0.1.0" date="2026-09-27" note="初稿（GROUP_A 增量）：9 个开源项目的官方文档调研、缺口映射（G1~G8）、对三条用户诉求的证据化差距分析与 P0~P3 候选路线、风险与反模式。待 PM 门控。"/>
    <rev version="0.1.0" date="2026-09-27" note="PM 门控 GR-A-002 = PASS_WITH_CONDITIONS：status 置 APPROVED。遗留（WebFetch 不可用 → 证据经 WebSearch 检索摘要；用户诉求③『UI 可视化配置』无 REQ 承接，须用户裁决）见 docs/phase_status.md。"/>
  </revision_history>
</file_header>

# 业界 Agent 平台对标调研 — 面向「可配置专家 / 路由 / 编排 + UI 可视化」的通用化

**文档编号**: RESEARCH-INTELBASE-001
**项目名称**: intelligentbase（通用 RAG + 多智能体可复用基础架构）
**版本**: 0.1.0 ｜ **状态**: APPROVED（PM 门控 GR-A-002 = PASS_WITH_CONDITIONS，2026-09-27；遗留条件见 `docs/phase_status.md`）
**作者**: requirement-analyst (via pm-orchestrator)
**调用**: `INV-GROUP_A-INTELBASE-002`（`RESEARCH_SUPPLEMENT`，非重写需求规格、非架构设计）
**上游基线**: `docs/requirements_spec.md` v1.1.0（APPROVED）、`docs/user_stories.md` v1.1.0（APPROVED）

> **边界声明（先读）**：本文件是**需求分析阶段的证据化补充调研**。文中一切「借鉴机制 / DSL 形态 / 数据模型 / 演进建议 / 接缝」只有两种性质：
> ① 对**外部项目已有事实**的引用（附官方 URL）；② **候选建议（待 PM / 用户确认）**。
> 本文件**不产出**本项目的模块设计、接口签名（IFC-*）、ADR 决策、代码或配置实现。凡涉本项目者一律标注 `[候选 — 待 PM/用户确认]`。

---

## 1. 调研结论摘要

### 1.1 总览：项目 → 可借鉴机制 → 缺口 → 成本

| # | 项目 | 值得借鉴的机制（官方文档证实） | 对齐本项目缺口 | 借鉴成本 |
|---|------|--------------------------------|----------------|----------|
| 1 | **Dify** | ①**一份 DSL 文档承载整个应用**：`kind: app` + `version` + app 配置 + workflow 图 + 节点设置 + 模型参数与提示模板 + 知识库连接（不含知识库数据本身）；②**画布编排器**：拖拽节点、连线成 DAG；③**导出/导入 round-trip**（CLI 与 Studio 两路）；④**按类型区分导出语义**（Workflow/Chatflow 导出**草稿**、需 publish 才对运行生效；Chatbot/Agent 导出**已发布版**）；⑤**secrets / 依赖显式排除**：导出默认剔除第三方工具 API key 与知识库内容，`--include-secret` 才纳入 | **G1**（配置入口）、**G2**（编排定义）、**G5**（多项目并存）、**G8**（可追溯） | 高 |
| 2 | **Microsoft Agent Framework（MAF）** | ①**声明式 YAML/JSON 定义 agent 与 workflow**（跨 .NET / Python 同一份 YAML）；②**五种内置编排模式**：Sequential / Concurrent / Handoff / Group Chat / Magentic，且**全部支持 streaming、checkpointing、HITL 审批、暂停恢复**；③**Handoff 构建器**带 `turn_limits`（限制往返次数）与 `approval_mode="always_require"`（敏感工具强制人工批准）；④**checkpoint 回灌依赖稳定的 agent `Id`**；⑤**声明式 → 代码是单向的**：官方明确**无反向转换**（运行期 workflow → YAML），且**自定义 executor 尚不支持**；⑥（前身 AutoGen）**component config 是「蓝图」而非「状态」**：`dump_component()` / `load_component()`，`provider` + `component_type` + `version` + `config` 四元组，`SecretStr` 字段不进 config，默认仅信任第一方 provider 命名空间 | **G1**（配置入口）、**G2**（编排定义）、**G3**（提示外置）、**G7**（质量闭环） | 中 |
| 3 | **OpenAI Agents SDK** | ①**handoff 是一等公民**：`handoffs=[...]` / `handoff(agent, ...)`，对 LLM 表现为「一次特殊工具调用」（`transfer_to_<agent>`）；②**handoff 与 agents-as-tools 是两种正交语义**（前者移交控制权、后者保留控制权，即 manager 模式）；③**`input_filter`** 可在移交时裁剪历史，`nest_handoff_history` 把前序对话折叠为摘要；④**guardrail 与执行并行跑，tripwire 触发即 fail-fast**；⑤**Sessions 提供跨轮持久记忆**；⑥**Tracing 默认开启**，逐步 span | **G2**（handoff 死字段）、**G4**（语义路由）、**G7**（质量闭环）、**G8**（可追溯） | 低-中 |
| 4 | **CrewAI** | ①**YAML 声明 agent 与 task**：`config/agents.yaml`（role / goal / backstory / tools）+ `config/tasks.yaml`（description / expected_output / 指派 agent），经 `@agent` / `@task` 装饰器注入；②**Flow 是「管理者」**：`@start` / `@listen` / `@router` 显式定义执行顺序、分支与失败处理；③共享 **State**（Pydantic 模型）+ `@persist` 状态持久化；④`plot()` 输出静态流程图 | **G1**（配置入口）、**G2**（编排定义）、**G3**（提示外置）、**G5**（多项目并存） | 低 |
| 5 | **LangGraph / LangGraph Platform** | ①**`StateGraph` 是主 API**，`compile()` 产出可执行图；②**持久化/checkpointer**（`InMemorySaver` / `SqliteSaver` / `PostgresSaver`），`thread_id` 为主键，支持 `get_state` / `get_state_history` / `update_state` / 时间旅行重放；③**HITL = 动态 `interrupt()` + `Command(resume=...)`**（官方明确**不推荐**用静态 breakpoint 做 HITL）；④**让图「可配置」的正规做法**：v0.6 起以 `context_schema` + `Runtime.context` 取代 `config_schema` + `config['configurable']`（`config_schema` 已弃用，v2.0 移除）；⑤**Studio**：节点/边可视化 IDE，**Assistants 允许在不改图代码的前提下改行为**（模型、提示、工具可用性）；⑥条件边需**显式 path map 或 `Literal` 类型注解**，否则 Studio 无法判定可达性，会把条件边画到所有节点 | **G5**（多项目并存）、**G7**（质量闭环）、**G8**（可追溯）、**G1**（配置入口） | 中 |
| 6 | **n8n** | ①**子工作流复用**：父侧 `Execute Sub-workflow` 节点，**来源四选一**：Database（按 ID 或列表）、Local File（本地 JSON）、Parameter（**直接内联 Workflow JSON**）、URL；②子侧 `Execute Sub-workflow Trigger`（"When Executed by Another Workflow"）定义**输入契约**（字段清单 / JSON 样例 / 接受全部数据）；③**模式**：`Run once with all items` vs `Run once for each item`，并有 `Wait for Sub-Workflow Completion`；④数据回流由子工作流**最后一个节点**送回父侧 | **G2**（编排定义）、**G5**（多项目并存） | 低-中 |
| 7 | **aurelio-labs semantic-router** | ①**Route = 名字 + 范例语句（utterances）**，官方建议每 Route 给足多样范例；②**静态路由 vs 动态路由**（动态路由额外用 LLM 抽取参数，落到 `function_call`）；③**阈值是可训练的**：`evaluate(X, y)` 看效果、`get_thresholds()` 看现状、`fit(X, y)` 训练阈值（官方 notebook 展示同一数据集上默认阈值准确率远低于拟合后）；④**`RouteLayer` / `SemanticRouter` 是决策层**，可配本地 encoder，未命中返回 `None`；⑤层可 save/load | **G4**（语义路由哑火）、**G6**（关键词匹配粗糙）、**G7**（阈值无校准） | 低 |
| 8 | **DSPy** | ①**声明式签名（Signature）**：把任务写成有类型的输入/输出契约（`"question -> answer"` 或 `InputField`/`OutputField` 类），不手写提示；②**Module 同接口不同策略**（`Predict` / `ChainOfThought` / `ReAct`），可嵌套组合；③**Optimizer 以 metric 编译程序**：给样例 + 打分函数，自动调提示（甚至微调权重）直至收敛 | **G7**（路由质量无 eval 闭环） | 高 |
| 9 | **LiteLLM** | ①**统一 provider 抽象**：把各 provider 异常映射为 OpenAI 异常类型，跨 100+ provider 暴露统一 `completion()`；②**`model_list` + `routing_strategy`**：同 `model_name` 的多个条目组成一个负载组；③**Fallbacks 是分桶的**：通用 `fallbacks` / `content_policy_fallbacks` / `context_window_fallbacks`，组内还有 `order` 分层回退；④**cooldown + 健康检查**：失败超阈值即冷却并从选池剔除，后台健康检查**主动**摘除不健康部署；⑤**Proxy 形态**：`config.yaml` 里 `model_list` 用 `os.environ/VAR` 间接引用密钥（**不内联**），另有虚拟 key / 预算 / 限流 / guardrails | **G8**（决策可追溯）、对齐 **REQ-NFR-IB-13**（降级矩阵）与 **DR-04**（LLM 端点可配置） | 低-中 |

### 1.2 本轮调研的证据完备度（如实总述）

| 项目 | 官方证据完备度 | 说明 |
|------|----------------|------|
| Dify | **中** | **官方**：DSL 概念、`kind: app` + `version` + CLI 导出/导入、Studio UI 导出、app 类型（Workflow/Chatflow/Chatbot/Agent/Text Generator）、可视化画布与节点体系、Agent 节点与 ReAct / Function Calling 策略、导出排除 secrets 与知识库内容。**未获官方**：**字段级 DSL 规范**——langgenius/dify 官方仓库 Discussion #31561 称官方**尚无**完整 DSL YAML 字段级规范，建议从导出样例反推；社区流传的 `agent_packages` / `soul` / `CURRENT_APP_DSL_VERSION` / 0.6.0↔0.7.0 版本映射**均来自第三方社区仓库 → 待官方证实**。 |
| MAF | **中-高** | **官方**：五种编排模式与「streaming/checkpointing/HITL/暂停恢复」、Handoff 构建器与 `turn_limits` / `approval_mode` / 稳定 `Id`、声明式 YAML agent（`CreateFromYamlAsync`）、声明式 workflow 1.0、VS Code 低代码（左 YAML / 右可视化图 + YAML→代码）。**官方仓库讨论 #4450** 证实：无反向转换、无自定义 executor。**前身 AutoGen 的 component config**（`dump_component` / `load_component` / `ComponentBase` / `_to_config` / `_from_config` / `SecretStr` / 可信命名空间白名单）为**官方文档**，但与 MAF 的声明式 YAML 是**两代不同机制**，未在本文件中混为一谈。**待官方证实**：`WorkflowInput`、`AgentWorkflowBuilder.BuildConcurrent` 等具体 API 名（源自官方仓库提交/样例，非文档正文）。 |
| OpenAI Agents SDK | **中-高** | **官方**：五大原语（Agents / Handoffs / Guardrails / Sessions / Tracing）、handoff 即工具调用、`input_filter` 与 `nest_handoff_history` 的限制条件（**服务端托管会话与 RealtimeAgent 不支持 input_filter**）、guardrail 与 tripwire、Sessions 与 SQLiteSession、Tracing 默认开启。**待官方证实**：agent loop 的源码级细节（如核心循环约 800 行、`Runner._run_impl` 内部结构）—— 源自第三方源码解读。 |
| CrewAI | **中** | **官方**：`agents.yaml` / `tasks.yaml` 与 crew 目录结构、Flow 的 `@start` / `@listen` / `@router`、State 与 `@persist`、`plot()`。**待官方证实**：「独立 crew 采用 JSON-first（`crew.jsonc` + `agents/*.jsonc`）与 `load_crew`」—— 仅见于第三方教程，官方 agents/flows 页未见直接确认。 |
| LangGraph | **中-高** | **官方**：`StateGraph` 与 `compile()` 选项、checkpointer 家族与 `thread_id`、`get_state`/`get_state_history`/`update_state`/重放、动态 `interrupt()` + `Command(resume)` 且**官方不推荐**静态 breakpoint 做 HITL、`context_schema` 取代 `config_schema`（弃用→v2.0 移除）、Studio 的 Assistants 机制与条件边可视化限制。**注意**：调用块给出的 `langchain-ai.github.io/langgraph` 未直接返回结果，检索命中的是 **`docs.langchain.com`**（现行官方文档域）与若干第三方镜像（mintlify / DeepWiki）。 |
| n8n | **中** | **官方**：父/子两个节点、四种来源、输入契约三种定义方式、两种 Mode、`Wait for Sub-Workflow Completion`、数据回流路径。**官方文档未查到**：完整的独立 workflow JSON **schema**（官方仅给节点级用法，未发布字段级 schema）。 |
| semantic-router | **中** | **官方**：Quickstart（`RouteLayer` / `SemanticRouter`）、`Route` = name + utterances、静态/动态路由、阈值 `evaluate` / `get_thresholds` / `fit` 与优化前后对比、本地执行（`semantic-router[local]`）。**待官方证实**：`Route` 完整属性表（`function_schemas` / `llm` / `metadata` 等）与「每 Route 5~10 条范例」的最佳实践建议 —— 主要来自第三方 DeepWiki。 |
| DSPy | **中** | **官方**：signature（类式与 `"question -> answer"` 简写）、Module（`Predict` / `ChainOfThought` / `ReAct`）、Optimizer 以 metric 编译、`dspy.GEPA` 示例语法、「Program, don't prompt」。**待官方证实**：优化器家族清单（`LabeledFewShot` / `BootstrapFewShot*` / `KNNFewShot` / `COPRO` / `MIPROv2`）—— 来自第三方整理。 |
| LiteLLM | **中-高** | **官方**：统一异常映射与 100+ provider、`model_list` 负载组、六种 `routing_strategy`、三类 fallback 桶 + `order` 分层、cooldown 与 `allowed_fails`、健康检查驱动路由、Proxy `config.yaml` 的 `os.environ` 间接引用与虚拟 key/预算。**待官方证实**：`complexity_router` / Auto Router 与 `routing groups`（较新特性，描述源含第三方）；某版本供应链告警亦来自第三方，**不作为官方结论**。 |

**查阅不到的官方入口（如实登记）**：
1. **Dify 的字段级 App DSL 规范** —— 官方未发布（官方仓库 Discussion #31561 即为「求规范」的讨论）。
2. **n8n 的完整 workflow JSON schema** —— 官方文档未提供。
3. **`docs.dify.ai` 的直接抓取** —— WebFetch 被域安全校验拒绝；Dify 证据均为 WebSearch 命中的官方页摘要。

---

## 2. 分项目官方文档分析

> 每节统一回答三件事：(a) 它**怎么建模** agent / 路由 / 编排 / 工具 / UI 可视化；(b) **可直接借鉴的设计**（机制、数据模型、DSL 形态 —— 不是照抄代码）；(c) 哪些属**过度设计 / 本项目不该学**。

### 2.1 Dify（最贴近本需求）

**(a) 建模方式（官方）**
- **DSL 承载整个应用**：DSL 是 YAML 格式，捕获「应用配置与元数据 + 工作流编排与节点设置 + 模型参数与提示模板 + 知识库连接（**不含知识库数据本身**）」；用于在实例/工作区/团队间搬运应用。导出物带 `kind: app` 头与 `version` 字段。
  - 证据：<https://docs.dify.ai/en/learn/key-concepts>、<https://docs.dify.ai/en/cli/reference/apps>、<https://github.com/langgenius/dify-docs/blob/6e1454eccc44ee5ae6a48ff4257bb0fe20635b86/en/guides/workflow/export_import.mdx>
- **两条导出/导入通路**：Studio UI 的 Export / Import（上传 `.yml` 或 `.zip`）；CLI `difyctl export studio-app` / `import studio-app`。**导出语义按 app 类型不同**：Workflow / Chatflow 导出的是**当前草稿**（`run app` 执行的是已发布版 → 导入后须在 Dify 内 publish 才生效）；Chatbot / Agent / Text Generator 导出的是**已发布版**。导入时做**版本兼容校验**并对 DSL 版本过旧给出警告。证据：同上 + <https://docs.dify.ai/en/cli/reference/apps>
- **导出不包含什么**（对隐私与可移植性极关键）：第三方工具的 API key、知识库实际内容、使用日志/分析、LLM 生成物；若应用引用了 Secret 类型环境变量，会**询问是否纳入**并给出敏感信息警告。证据：Dify 官方 Apps/Manage Apps 文档（`docs.dify.ai`）。插件打包侧亦有同源纪律：**绝不把 `.env` / access token / 私钥 / 云凭据打进包**。证据：<https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/submit-plugin-to-marketplace>
- **可视化编排器**：Studio 的画布为**拖拽式有向图编辑器**，DAG 中节点是处理单元、边是数据流；Workflow 与 Chatflow **共用同一画布与节点体系**；节点按类别分组（Trigger / Processing / Logic & Control / Data / Advanced(Agent, Tools) / Output）；变量以上游节点输出引用下游（`{{node_name.output_variable}}`）。
  - 证据：<https://docs.dify.ai/en/self-host/use-dify/build/workflow-chatflow>（官方页，标题 "Workflow & Chatflow"）
- **Agent 节点**：LLM 自主控工具、迭代「想→选→调」。**策略（Agent Strategy）是可插拔插件**：官方内置 **Function Calling**（用模型原生 function calling 传 `tools`）与 **ReAct**（结构化提示走 Think→Act→Observe 循环）；更多策略可从 Marketplace 安装。节点可选 **Allowed tools** 白名单；执行控制含 **Max Iterations** 与 Memory(TokenBufferMemory)。证据：<https://docs.dify.ai/zh/cloud/use-dify/nodes/agent>、<https://enterprise-docs.dify.ai/en/3.12.x/use/nodes/agent>、<https://marketplace.dify.ai/plugin/langgenius/agent>
- **⚠ 待官方证实（DSL 字段级）**：`workflow.graph{nodes, edges, viewport}` 的完整字段、`app.mode` 取值集合（`workflow` / `advanced-chat` / `chat` / `completion` / `agent-chat` / `agent`）、DSL 版本映射（1.15.x↔0.6.0、1.16.x↔0.7.0）、以及 `agent_packages` / `soul` / `package_ref` 形态 —— 均来自第三方社区仓库，官方未发布字段级规范。**本项目不得据此臆造字段名。**

**(b) 该学什么**
1. **「一份文档 = 一个完整可搬运定义」**：DSL 把 app 配置、图、节点设置、提示模板、知识库**连接**打包为单一自包含文档 —— 这正是「按项目定义智能体 + 定义工作流」的载体形态。
2. **UI 画布与 DSL 是同一真源的两个视图**（画布编辑 ↔ YAML 导出/导入），而非两套数据。这是「UI 可视化配置」不沦为第二真源的关键设计。
3. **导出/导入的「显式排除清单」**：secrets 与知识库内容**默认不导出**，需显式开关才纳入。与本项目 C-IB-02「凭据绝不入库/入产物」同源。
4. **应用类型决定导出语义**（草稿 vs 已发布版）与**导入期版本兼容校验 + 警告**：说明「定义文档需要版本化与兼容策略」是这一层的固有需求。
5. **Agent 策略可插拔**（ReAct / Function Calling 作为可替换模块）+ **工具白名单** + **迭代上限**：与本项目「按专家最小授权」和 `MAX_EXPERT_STEPS` 同构。

**(c) 过度设计 / 不该学**
- **全功能节点库**（Iteration / Loop / 变量聚合器 / 列表算子 / 代码节点 / 定时与 Webhook 触发器）：这是通用工作流引擎的范畴，远超本项目「RAG + 多专家问答」的需要。
- **插件市场 + `.difypkg` 打包 + 插件远程安装**：引入包管理与供应链面。且官方明确**导出会拒绝远程插件**，说明这条路本身有可移植性代价。
- **DSL 版本迁移矩阵**：本项目若引入声明式定义，v1 只需**一个版本 + 明确的兼容拒绝策略**（读到不认识的版本就报错），不需要历史版本迁移能力。

---

### 2.2 Microsoft Agent Framework（MAF，AutoGen 后继）

**(a) 建模方式（官方）**
- **编排模式内置五种**：**Sequential**（顺序传递）、**Concurrent**（并行广播聚合）、**Handoff**（按上下文互转，网状拓扑、无中心管理员）、**Group Chat**（共享会话 + 管理器星型）、**Magentic**（manager/planner 动态协调专家）。**五种模式均支持 streaming、checkpointing、human-in-the-loop 审批、暂停/恢复**。证据：<https://learn.microsoft.com/en-sg/agent-framework/workflows/orchestrations/>
- **工作流三要素**：**Executors**（收消息/干活/发消息，可为 AI agent 或自定义逻辑）、**Edges**（直连边、条件边、switch-case 边、fan-out 一对多、fan-in 多对一）、**Events**（`WorkflowStartedEvent` / `WorkflowOutputEvent` / `WorkflowErrorEvent` / `ExecutorInvokeEvent` / `ExecutorCompleteEvent` / `RequestInfoEvent`）。证据：同上。
- **Handoff 构建器**：`CreateHandoffBuilderWith(triageAgent).WithHandoffs(triageAgent, [mathTutor, historyTutor]).WithHandoffs([...], triageAgent)`；因为是**经工具调用**完成转交，agent 若不调 handoff 工具就正常回答并把控制权交回用户 —— 官方指出**不能强制所有 agent 永远转交**，否则它无法产出有用回答；**`with_autonomous_mode()`** 让 agent 在无人介入下自动续跑，可按 agent 子集启用、并配 **`turn_limits={agent: N}`** 限制往返；敏感工具可设 **`approval_mode="always_require"`** 强制人工批准；**checkpoint 回灌时须复用同一 agent `Id`/`Name`**，否则 handoff 路由与 checkpoint 兼容性会被破坏。证据：<https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff>（各语言镜像页同源）
- **声明式 Agent（YAML/JSON）**：`kind: Prompt` + `name` / `description` / `instructions` / `temperature` / `topP` / `outputSchema`；C# 侧 `ChatClientPromptAgentFactory` + `PromptAgentFactory.CreateFromYamlAsync`；Python 侧 `agent-framework-declarative` 提供 `AgentFactory` 与 `create_agent_from_yaml(_path)`。**YAML 定义跨 .NET / Python 通用**，目的是「定义、修改、分享」与「行为与实现代码分离」。证据：<https://learn.microsoft.com/en-us/agent-framework/agents/declarative?pivots=programming-language-csharp>、<https://github.com/MicrosoftDocs/semantic-kernel-docs/blob/main/agent-framework/agents/declarative.md>
- **声明式 Workflow 1.0**：把多智能体编排搬进 YAML，支持 **state、分支、工具调用、人工交接、Power Fx 表达式、MCP 工具**；经 `DeclarativeWorkflowFactory` **编译为 pro-code workflow 执行**。**官方明确：无反向转换**（运行期 workflow → JSON/YAML），且**当前不支持自定义 executor**。证据：<https://learn.microsoft.com/en-us/agent-framework/workflows/declarative?pivots=programming-language-csharp>、<https://github.com/microsoft/agent-framework/discussions/4450>、<https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/declarative/README.md>
- **VS Code 低代码**：Foundry Toolkit 扩展里**左侧 YAML、右侧可视化工作流图**，并可把 YAML workflow **转成 Agent Framework 代码**。证据：<https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/foundry/agents/how-to/vs-code-agents-workflow-low-code.md>
- **（前身 AutoGen，官方文档）component config**：`ComponentBase[Config]` + `Component[Config]`，声明 `component_type` 与 `component_config_schema`，实现 `_to_config()` / `_from_config()`；实例侧 `dump_component()`，接口侧 `load_component(config)`。**官方强调「组件配置 ≠ 状态序列化」**：配置是**蓝图**，可反复「盖」出多个同配置实例；状态序列化则必须精确复现同一对象（含消息历史）。`SecretStr` 字段**不进 config**。**安全**：只从可信来源加载组件（反序列化可能执行代码），第一方命名空间默认可信，其余需经环境变量白名单。**限制**：`selector_func` 不可序列化会被忽略；**工具序列化尚不支持**。证据：<https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/component-config.html>、<https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/serialize-components.html>

**(b) 该学什么**
1. **「蓝图 ≠ 状态」这一区分**（AutoGen 官方原话）—— 本项目若做声明式专家/编排定义，**定义文档是蓝图**，会话状态（checkpointer）另走一路。这条区分能直接回答「配置里要不要放运行期数据」这类边界问题。
2. **声明式定义与运行期执行是编译关系**（`DeclarativeWorkflowFactory` 把 YAML 编译成 workflow）：与本项目 `install(specs)` + 编译一次常驻图的形态同构。
3. **Handoff 的三个护栏**（`turn_limits` 往返上限、`approval_mode` 敏感工具强制批准、稳定 `Id` 保证 checkpoint 可回灌）—— 这三点是「子委托/handoff 一旦真的实现，会立刻踩到的坑」，本项目 G2 尤其该记。
4. **`SecretStr` 不进 config + 可信命名空间白名单**：声明式配置的密钥与「可加载来源」必须有显式边界。
5. **YAML 定义跨语言通用 + 左右分栏（YAML ↔ 可视化图）**：UI 可视化的低成本形态是「定义文档的图形视图」，而不是独立编辑器。
6. **「不能强制所有 agent 永远 handoff」**：转交是**模型决策**而非纯配置可保证的行为 —— 对我方「绝不无人应答」的兜底设计是重要提示（handoff 不可作为唯一出口）。

**(c) 过度设计 / 不该学**
- **Power Fx 表达式**、**Magentic / Group Chat 编排模式**：远超本项目「路由 → 并行专家 → 聚合」的需要。
- **A2A 与 MCP 协议面**：跨信任边界的 agent 互调，本项目 v1 无此诉求（且会显著扩大攻击面）。
- **.NET / Python 双语言同构**：本项目单语言（Python），追求跨语言 YAML 一致性无收益。
- **「无反向转换」若照搬到 UI 侧会出问题**：MAF 的 YAML→code 单向足够，但本项目若要做 UI 编辑，**必须双向**（UI 改完要能写回定义文档）—— 这一点上应学 **Dify（画布与 DSL 双视图 round-trip）**，而不是 MAF。

---

### 2.3 OpenAI Agents SDK（Swarm 后继）

**(a) 建模方式（官方）**
- **五原语**：Agents、Handoffs、Guardrails、Sessions、Tracing；provider 无关（Responses / Chat Completions / 100+ LLM）。
- **Handoff**：表现为**一次特殊工具调用**（对 agent 名为 `Refund Agent` 的转交即工具 `transfer_to_refund_agent`）。`handoffs=[agent]` 或 `handoff(agent, ...)`；`handoff()` 支持 `tool_name_override` / `tool_description_override`、`on_handoff`（副作用回调，**不用于动态选目标**）、`input_type`（**描述的是转交工具的调用载荷，不是下一个 agent 的主输入**）、`input_filter`（改写下一位 agent 收到的历史）、`is_enabled`（可动态开关，关闭即对 LLM 隐藏）、`nest_handoff_history`（把前序对话折叠为摘要）。**限制**：`input_filter` 在**服务端托管会话**与 **`RealtimeAgent` 转交**上不支持。**生命周期**：LLM 产出转交工具调用 → SDK 识别并执行 `on_invoke_handoff` → 可选 `on_handoff` → `input_filter` → 控制权切换 → 生成 `HandoffOutputItem` → 新 agent 在下一轮循环以过滤后的历史运行。
- **Handoff vs agents-as-tools**：前者**对等移交控制权**（目标 agent 接管会话）；后者 `agent.as_tool()` 是 **manager 模式**（调用方保留控制权并解释被调 agent 的输出）。HITL 审批是 **run 级**的，覆盖直连工具、handoff 与嵌套 `as_tool`。
- **Guardrail**：**与 agent 执行并行跑**、校验输入输出，违规经 **tripwire** 抛异常即 **fail-fast** 中止。
- **Session**：跨运行的**自动对话历史管理**（如 `SQLiteSession`），`Runner.run(agent, input, session=session)`。
- **Tracing**：**默认开启**，为每一步产出 span，可自定义 `trace(...)` / `t.span(...)`，可对接第三方 processor。
- `Agent` 是**不可变配置**（name/instructions/tools/handoffs/model，自身不「运行」），`Runner` 是**无状态执行器** —— 因此同一 Agent 实例可被并发请求安全复用。
- 证据：<https://openai.github.io/openai-agents-python/>、<https://openai.github.io/openai-agents-python/ref/handoffs/>、<https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md>，以及官方 guardrails/sessions/tracing 页（`openai.github.io/openai-agents-python/guardrails/`、`/sessions/`、`/tracing/`）。**待官方证实**：核心循环行数与 `Runner._run_impl` 内部结构（第三方源码解读）。

**(b) 该学什么**
1. **handoff 的「一等公民化」+ 历史过滤**：把「移交」建模为一种工具调用，可复用既有工具机制，且**移交时能裁剪/折叠历史**（`input_filter` / `nest_handoff_history`）—— 直接对应本项目 G2（`is_delegating` / `delegating_experts()` 目前是死字段）。
2. **两种语义的正交划分**（handoff = 移交控制权 vs as_tool = 保留控制权）：本项目现状是「专家内部调另一个专家（深度限 1）」，语义上**更接近 as_tool（manager 模式）而非 handoff**。这个区分有助于把 G2 的「想做什么」说清楚。
3. **guardrail 与执行并行 + tripwire fail-fast**：对应本项目 `guard_against_misroute`（无证据不行动）。「并行校验、违规即止」是可借鉴的**形态**（不是照抄实现）。
4. **不可变 agent 配置 + 无状态 runner**：这是「同一个专家定义可被多项目/多请求共享」的安全前提 —— 对本项目 G5（全局单例 vs 多项目共存）有直接参考价值。
5. **Tracing 默认开启**：与本项目 G8（`RouteDecision.tier/confidence` 未见结构化落盘）形成对照 —— 路由决策**应当**是可追踪的一等产物。

**(c) 过度设计 / 不该学**
- **多 provider 100+ LLM 抽象**：本项目已由 DR-04 定为云端 DeepSeek（端点可配置即可），不需要 provider 矩阵。
- **Realtime（语音实时）与 `RealtimeAgent`**：范围外。
- **托管会话 / 服务端会话 API**：本项目会话策略应为「进程内 + 安全失败」（REQ-FUNC-IB-20 约束），引入远端托管会话会与 REQ-NFR-IB-08（数据不出本地）冲突。
- **自带 tracing 上报到第三方 SaaS**：与「数据不出本地」冲突；可学的是「span 化的可观测**形态**」，落点必须是本地日志/本地存储。

---

### 2.4 CrewAI

**(a) 建模方式（官方）**
- **Crews + Flows 两个层次**：Crew 是「干活的角色团队」（自主协作），Flow 是「知道顺序、处理失败的管理者」（事件驱动编排，精确控制执行顺序、分支、状态与持久化）；官方建议**生产应用从 Flow 起步**，把 Crew 作为子步骤嵌入。
- **四原语**：Agent（role + goal + backstory + tools）、Task（description + expected_output + 指派的 agent）、Crew（容器，持有 Process）、Process（Sequential / Hierarchical）。
- **YAML 声明**：crew 目录含 `config/agents.yaml`（逐个 agent 的 role / goal / backstory / tools）与 `config/tasks.yaml`（任务描述、期望输出、指派）；运行时读 YAML、注入到带 `@agent` / `@task` 装饰的方法；**改角色或任务顺序只需改 YAML**。
- **Flow**：`Flow[State]` + `@start` / `@listen` / `@router`；共享 `State`（Pydantic 模型）；`@persist` 状态持久化；`flow.plot("...")` 输出流程图；`kickoff()` 运行。
- 证据：<https://docs.crewai.com/en/concepts/flows>（含版本化路径如 `/v1.15.6/`、`/v1.15.17/`）、<https://docs.crewai.com/en/concepts/agents>。**待官方证实**：JSON-first 的 `crew.jsonc` + `agents/*.jsonc` 与 `load_crew`。

**(b) 该学什么**
1. **「YAML 声明 + 装饰器绑定」的低成本声明式**：不引入 DSL 引擎，只要「YAML 描述 + 启动期注入」，就能让「改专家元数据不必改代码」。这是本项目 G1 的**最低成本形态**。
2. **Agent 的元数据字段划分**（role / goal / backstory / tools）比本项目 `ExpertSpec` 更细 —— 但注意本项目 `ExpertSpec` **是单一真源**且被多模块派生，**不应为对齐而拆散**（见 §4）。
3. **Flow 与 Crew 分层**（编排 vs 角色团队）：与本项目「编排层 vs 注册层」分层同构，CrewAI 的分层经验可为「工作流定义」提供命名与边界参考。

**(c) 过度设计 / 不该学**
- **Flow 的 `@persist` 全量状态持久化**：本项目会话状态的语义已由 REQ-FUNC-IB-20 定为「安全失败」；引入全量状态持久化会改变该语义。
- **Crew 自主协作（Hierarchical / Consensual）**：与本项目「路由显式决定专家集合」的确定性诉求相悖（本项目的路由 temperature=0 是硬约束）。
- **`plot()` 静态图**：只是静态渲染，不构成「可编辑的 UI 可视化配置」。

---

### 2.5 LangGraph / LangGraph Platform（本项目已在用，重点关注「图能否配置化」）

**(a) 建模方式（官方）**
- **`StateGraph` 是主 API**；`compile()` 产出可执行图，编译选项含 `checkpointer`、`interrupt_before` / `interrupt_after`、`cache`、`store`、`debug`、`name`。
- **持久化**：`InMemorySaver`（仅开发）、`SqliteSaver`（本地单文件）、`PostgresSaver` / `AsyncPostgresSaver`（生产）；`thread_id` 是存储/检索 checkpoint 的主键。`get_state(config)` 返回 `StateSnapshot`（`values` / `next` / `config` / `metadata` / `created_at` / `parent_config` / `tasks`）；`get_state_history` 可取全量历史（支持 `filter` / `limit`）；**重放** = 用早先的 `checkpoint_id` 调用；`update_state` 可编辑状态（可带 `as_node`）。**durability 模式**：`exit` / `async` / `sync`。
- **HITL**：**动态 `interrupt(...)`** 在节点中暂停并把 JSON 可序列化载荷交给人，`Command(resume=...)` 恢复；**官方明确不推荐**把静态 breakpoint（`interrupt_before` / `interrupt_after`）用于 HITL，后者定位是调试/测试。
- **让图「可配置」的正规做法（关键）**：v0.6 起以 **`context_schema` + `Runtime.context`** 取代 `config_schema` + `config['configurable']`；`config_schema` 已弃用、**将在 v2.0 移除**。`Runtime` 统一暴露 `context`（run 起始传入的静态数据）、`store`（长期记忆）、`stream_writer`。**`config` 仍然是** `thread_id` / `checkpoint_id` / `checkpoint_ns` / `tags` / `recursion_limit` 这类运行期管道的载体。
- **Studio**：可交互、可视化的 agent IDE，展示节点/边/路由逻辑；**Assistants 允许通过配置（模型选择、提示、工具可用性）改行为而**不改图代码**；代码侧先定义 context schema，建 Assistant 时提供 context 值。**条件边可视化限制**：不显式给 path map（`add_conditional_edges(..., {True: "b", False: "c"})`）或 `Literal` 类型注解时，Studio **无法判定可达性，会把条件边画到所有节点**。
- 证据：<https://docs.langchain.com/oss/python/langgraph/checkpointers>、<https://docs.langchain.com/oss/python/langgraph/studio>、<https://docs.langchain.com/langsmith/add-human-in-the-loop>、<https://reference.langchain.com/python/langgraph/graph/state/StateGraph>、<https://github.com/langchain-ai/langgraph/pull/5243>、<https://docs.langchain.com/langsmith/graph-rebuild>

**(b) 该学什么**
1. **`context_schema` + `Runtime.context` 是「同一张图按项目/按运行配置行为」的**官方正规路径**（取代已弃用的 `config_schema`）。本项目 G5（多项目不同专家表）应优先考虑这条**框架自带**的路，而不是自造。
2. **Assistants 机制**：官方已支持「**不改图代码**改行为（模型/提示/工具可用性）」—— 这是「UI 可视化配置」在 LangGraph 生态里的**既有落点**，比自造编辑器成本低得多。
3. **条件边必须显式 path map / `Literal`**：否则 Studio 画不对。若本项目未来上可视化，这是**必须遵守的形状约束**（可借鉴的硬性工程经验）。
4. **HITL 用动态 `interrupt()` 而非静态 breakpoint**：本项目 REQ-FUNC-IB-20 已用 `interrupt()`，与官方推荐一致 —— **保持**。
5. **durability 三档 + `thread_id` 主键**：为「会话状态丢失语义 = 安全失败」提供了官方档位语言。

**(c) 过度设计 / 不该学**
- **Postgres / Cosmos 级生产 checkpointer**：与 DR-03（禁 Docker、物理机直部署）及「单实例」拓扑相比过重；`SqliteSaver` 量级足够（且本项目台账已用 sqlite3 + WAL 的既有先例）。
- **LangGraph Platform / LangSmith Cloud**：托管服务，与「数据不出本地」张力大。
- **把「图结构」本身做成运行期可改**：LangGraph 的图是**编译期**结构；「配置化」的正解是 context + assistant，而**不是**运行期改图。这一点直接约束本项目「UI 配置工作流」的可行边界（见 §3.4）。

---

### 2.6 n8n

**(a) 建模方式（官方）**
- **子工作流复用**：父工作流用 `Execute Sub-workflow` 节点调用子工作流；子工作流以 `Execute Sub-workflow Trigger`（"When Executed by Another Workflow"）为第一个节点。
- **父侧 Source 四选一**：**Database**（按 workflow **ID** 或从**列表**选）、**Local File**（本地 JSON 文件路径）、**Parameter**（**直接内联 Workflow JSON**）、**URL**。
- **输入契约**（子侧 trigger）：`Define using fields below`（逐字段名 + 类型）/ `Define using JSON example`（给样例 JSON）/ `Accept all data`。
- **Mode**：`Run once with all items` vs `Run once for each item`（后者可与 `Wait for Sub-Workflow Completion` 组合出并行）。
- **数据回流**：子工作流**最后一个节点**把数据送回父侧 `Execute Sub-workflow` 节点。
- **前置条件**：子工作流自身不能含错误，否则父侧无法触发。
- 证据：<https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow>、<https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflowtrigger>、<https://docs.n8n.io/build/flow-logic/break-workflows-into-smaller-parts>
- **官方文档未查到**：完整的独立 workflow JSON schema（官方只给节点级用法）。

**(b) 该学什么**
1. **「子工作流可作为 JSON 被内联 / 被引用 / 被 URL 拉取」**：同一份定义支持**引用式**（按 ID）与**内联式**（JSON）两种携带方式 —— 这是「定义可复用 + 可搬运」的实用折中，本项目若做「项目级编排定义」可参考「引用 vs 内联」的取舍维度。
2. **输入契约由被调方声明**（字段清单 / JSON 样例 / 接受全部）：清晰的**调用契约**思想，对应本项目「专家能力声明由工具表派生」（REQ-FUNC-IB-03）的同构思路。
3. **「Run once with all items」vs「Run once for each item」**：对应本项目 fan-out 语义的一个明确对照（本项目是**一次问题并发给多个专家**，属 "once with all items" 的并行变体）。

**(c) 过度设计 / 不该学**
- **整条可视化节点工作流引擎**（数百个集成节点、Webhook/定时触发器、凭据管理器、执行历史）：这是通用自动化平台，与本项目目标不同量级。
- **"本地文件路径" 作为工作流来源**：在服务端引入「按路径加载可执行定义」是**安全反模式**（路径即攻击面），与本项目 C-IB-02 纪律相悖。
- **执行次数计费/套餐语义**：商业平台约束，无借鉴价值。

---

### 2.7 aurelio-labs semantic-router

**(a) 建模方式（官方）**
- **定位**：LLM 与 agent 的「**超快决策层**」，用向量语义而非等待 LLM 生成来做路由决策。
- **Route = `name` + 范例语句（utterances）**；构造 `RouteLayer(encoder=..., routes=[...])`（新版亦见 `SemanticRouter(encoder=..., routes=..., auto_sync="local")`）；调用返回命中的 route 名，**未命中返回 `None`**。
- **Encoder 可换**（`CohereEncoder` / `OpenAIEncoder` / `HuggingFaceEncoder` / `FastEmbedEncoder` / `AzureOpenAIEncoder` 等），并支持**完全本地执行**（`semantic-router[local]`）。
- **静态路由 vs 动态路由**：静态只返回 route 名；动态额外用 LLM 抽取参数填入 `function_call`。
- **阈值可训练（关键）**：`evaluate(X, y)` 评估、`get_thresholds()` 查看、`fit(X, y)` **训练**阈值。官方 threshold-optimization notebook 展示：同一数据集默认阈值下准确率很低，**`fit` 之后显著提升**。
- **层可 save/load**。
- 证据：<https://docs.aurelio.ai/semantic-router/get-started/quickstart>、<https://semantic-router.readthedocs.io/en/latest/quickstart.html>、<https://github.com/aurelio-labs/semantic-router>（README + `docs/06-threshold-optimization.ipynb`）。**待官方证实**：`Route` 完整属性表与「每 Route 5~10 条范例」建议（主要来自第三方 DeepWiki）。

**(b) 该学什么**
1. **「Route 以范例语句为定义」**：与本项目 L1 语义路由的范例目录机制**同构**，但本项目 G4 的问题是**范例目录为空、生产哑火** —— semantic-router 证明「范例 + 阈值」这一路是**可行且被广泛使用**的，问题在**数据缺失**而非机制错误。
2. **`fit(X, y)` —— 阈值是有监督可训练的**：直接回应本项目 G7（`tau=0.65` / `margin=0.05` 来自 PoC、无金标集）。**形态**可借鉴：构造金标集 → 评估 → 拟合阈值。
3. **未命中返回 `None`**：与本项目「语义层 fail-open 返回 None，交下一级」的降级链一致 —— 可保持。
4. **encoder 可替换 + 可完全本地**：与本项目 DR-02（本地 bge-m3）不冲突，且提示「语义路由的 encoder 与检索的 embedding 可以是不同的实例/配置」。

**(c) 过度设计 / 不该学**
- **动态路由的 LLM 参数抽取**：本项目专家路由只需「选专家集合」，不需要抽参数成函数调用。
- **多模态路由 / 行业预置路由（如医疗行政）**：范围外。
- **自增长 route（自动生成新 route）**：会让「专家集合」这一**受控真源**失控，与本项目「注册表是单一真源、装配期校验」冲突，**明确不学**。

---

### 2.8 DSPy

**(a) 建模方式（官方）**
- **口号「Program, don't prompt」**：不手写提示，而是声明任务的有类型输入/输出。
- **Signature**：类式（`class X(dspy.Signature)` + `InputField` / `OutputField`）或简写 `"question -> answer"`。
- **Module**：「同接口、不同策略」—— `Predict`（直出）、`ChainOfThought`（加推理步骤）、`ReAct`（加工具与推理循环）；可嵌套组合为自定义 `dspy.Module`（实现 `forward`）。
- **Optimizer**：「以 metric 编译程序」—— 给样例与打分函数，自动调提示直至质量收敛（示例 `dspy.GEPA(metric=..., auto="medium").compile(program, trainset)`）。官方定位是可移植、可维护、跨模型/跨策略。
- 证据：<https://dspy.ai/>、<https://dspy.ai/current/getting-started/program-dont-prompt/>。**待官方证实**：优化器家族清单（`LabeledFewShot` / `BootstrapFewShot*` / `KNNFewShot` / `COPRO` / `MIPROv2`）。

**(b) 该学什么**
1. **「声明契约（signature）+ 策略可换（module）」**：把「做什么」与「怎么做」分开。与本项目 `ExpertSpec`（声明元数据）+ 专家实现（策略）的分层同构，**印证本项目方向正确**。
2. **以 metric 驱动的优化闭环**：回应 G7。但**本项目 v1 不该直接引入 DSPy**（见下）。

**(c) 过度设计 / 不该学**
- **优化器（Optimizer）体系**：其前提是**有金标集与可重复的 metric**—— 本项目当前**连金标集都没有（G7）**。**在缺金标时引入优化器是纯粹的成本**。正确顺序是「先建金标集 → 再谈优化」，届时也可用轻量手段（阈值拟合）而非引入完整框架。
- **DSPy 对提示的完全接管**：本项目有 `ROUTER_PROMPT` 固定模板与 temperature=0 的**确定性**诉求（REQ-FUNC-IB-19）；让优化器改写提示会引入非确定性，与既有约束冲突。

---

### 2.9 LiteLLM

**(a) 建模方式（官方）**
- **统一 provider 抽象**：把各 provider 异常**映射为 OpenAI 异常类型**（既有 OpenAI 错误处理可直接复用）；跨 100+ provider 暴露统一 `completion()`；有各 provider 的 endpoint 兼容矩阵。**两种形态**：Python SDK Router / Proxy（LLM Gateway）。
- **负载均衡**：`model_list` 中同 `model_name` 的多条目构成一个组；每条目一个部署，`model_id` 由 `litellm_params` 哈希确定性生成（用于健康、冷却、溯源）。`routing_strategy` 六档：`simple-shuffle`（默认，按 rpm/tpm/weight 加权随机，**官方推荐生产**）、`least-busy`、`latency-based-routing`、`usage-based-routing(-v2)`（v2 需 Redis 跨 worker，**官方警告生产慎用**）、`cost-based-routing`；另有自定义策略接口。
- **Fallbacks（分桶 + 分层）**：通用 `fallbacks`、`content_policy_fallbacks`（内容策略违规）、`context_window_fallbacks`（超上下文）；**组内还有 `order` 层级**：`order=1` 失败自动降到 `order=2`，每层各自跑完 `num_retries` 才升级；跨组 fallback 在 `num_retries` 耗尽后触发。重试为指数退避 + 抖动。
- **cooldown + 健康检查**：某分钟内失败数超过 `allowed_fails` 即进入冷却、被排除出选池；`cooldown_time` / `disable_cooldowns` / 按异常类型的 `AllowedFailsPolicy` 可配；多 worker 下需 Redis 共享冷却状态；**后台健康检查主动摘除不健康部署**。
- **Proxy（网关）**：`config.yaml` 的 `model_list` **用 `os.environ/VAR` 间接引用密钥（绝不内联）**，另有 `router_settings`（`num_retries` / `timeout` / `fallbacks` / `context_window_fallbacks`）与 `litellm_settings`；以 OpenAI 兼容端点对外；提供**虚拟 key、按 key/team 的预算与限流、多租户成本跟踪、guardrails、管理面板**。
- 证据：<https://docs.litellm.ai/docs/routing>、<https://docs.litellm.ai/docs/routing-load-balancing>、<https://docs.litellm.ai/docs/proxy/reliability>、<https://docs.litellm.ai/>。**待官方证实**：`complexity_router` / Auto Router / routing groups（较新特性）；某版本供应链告警（第三方来源，**不作为官方结论**）。

**(b) 该学什么**
1. **「分桶降级」的降级矩阵形态**：`fallbacks` / `content_policy_fallbacks` / `context_window_fallbacks` 是**按失败原因分桶**的，而非一锅端。本项目 REQ-NFR-IB-13 要求「明确各依赖故障时的降级行为矩阵」—— LiteLLM 的**分桶**是这一要求的最佳形态参考。
2. **组内 `order` 分层 + 每层独立重试预算**：与「依赖故障不得打挂会话」配合时的实用结构（先试同组备选，再跨组）。
3. **`cooldown` + 主动健康检查**：把「已知不健康的依赖」**提前摘除**，而不是每次请求都撞一次超时 —— 对本项目 fail-open（REQ-FUNC-IB-21）是「降级得更快」的补充。
4. **密钥只经 `os.environ` 间接引用**：与 C-IB-02 / REQ-NFR-IB-07 完全同源。
5. **统一异常映射**：本项目「fail-open 须可区分『依赖故障』与『知识库为空』」（REQ-FUNC-IB-21）需要**异常类型归一**做前提，LiteLLM 的做法印证了这一点。

**(c) 过度设计 / 不该学**
- **虚拟 key / 预算 / 多租户成本跟踪 / 管理面板**：本项目是内部基座，无计费与多租户诉求。
- **`cost-based-routing` / `usage-based-routing`**：需要完备成本表与 Redis 跨 worker 状态；单实例 + 单 LLM 端点（DR-04）下无收益。
- **Proxy 作为独立网关进程**：会新增一个部署组件（与 DR-03「全物理机直部署、组件裸装、不做双路径」的取向相悖，除非确有必要）。**可只借鉴「配置形态」而不引入 Proxy 组件。**

---

## 3. 对本项目需求分析的补充

> 本节把 §2 的业界结论映射回**用户三条诉求**，给出**证据化**的差距分析。所有针对本项目的建议一律标注 **`[候选 — 待 PM/用户确认]`**，不构成需求变更；如需落盘，应由 PM/用户裁决后另行修订 `requirements_spec.md` / `user_stories.md`。

### 3.1 用户诉求 → 现状 → 业界对照 → 差距结论

| 用户诉求 | 本项目现状（需求侧 + 已知缺口） | 业界对照（官方证据） | 差距结论 |
|----------|-------------------------------|----------------------|----------|
| **① 智能体可按具体项目定义** | REQ-FUNC-IB-01（项目级配置驱动，核心代码零改动）、REQ-FUNC-IB-02（专家注册表单真源 + 可插拔）、REQ-FUNC-IB-23（单实例多项目隔离）。**缺口**：G1（`install()` 无配置入口，专家写死在 `.py` 字面量）、G3（无提示文件加载，人格与代码耦合）、G5（注册表是全局单例，多项目无法共存不同专家表） | Dify：DSL 承载应用定义、可跨实例搬运；CrewAI：`agents.yaml` 声明 agent 并注入；MAF：YAML 定义 agent（`kind: Prompt` + instructions）；AutoGen：component config 作为**蓝图** | **需求已覆盖「专家可插拔」，但缺「配置载体」这一环**。REQ-FUNC-IB-01 的文字（「仅需提供一组配置…专家集合」）已隐含该要求，但**现有实现（G1）未落地**。这是**实现与需求的落差**，而非需求缺失 → 优先补**实现**，不必新增 REQ。 |
| **② 可定义工作流程（分工/路由/汇聚）** | REQ-FUNC-IB-18（LangGraph 路由→fan-out→聚合）、REQ-FUNC-IB-19（四级兜底 + 粘性 + OOD + 默认专家）。**缺口**：G2（子委托 handoff 未实现，`is_delegating` 是死字段）、G4（L1 语义路由范例为空、生产哑火）、G6（关键词纯 `substring in`）、G7（无 eval/回归闭环） | MAF：五种内置编排 + handoff 构建器（`turn_limits` / `approval_mode` / 稳定 `Id`）；OpenAI Agents SDK：handoff 一等公民 + `input_filter` + guardrail/tripwire；semantic-router：Route=范例集 + **阈值可 `fit`**；DSPy：metric 驱动的优化 | **编排「骨架」已定义清楚，缺的是「可声明」与「可校准」**：(a) 编排本身仍是**代码**（LangGraph 编译期图），业界通用做法是「声明式定义 → 编译执行」（MAF 的 `DeclarativeWorkflowFactory`）；(b) 路由质量**无闭环**（G4/G7）。**其中 (b) 是需求已隐含（REQ-FUNC-IB-19 要求「健壮」、REQ-NFR-IB-14 要求可离线单测）但未量化的缺口。** |
| **③ UI 可视化配置** | **需求中无对应 REQ。** OQ-IB-04 明确：基座只需「最小可验证的问答入口」，**完整产品化界面由接入项目自建**；OOS-06 亦把「完整问答产品化界面」列为范围外。 | Dify：拖拽画布 = DSL 的图形视图（**双视图同源**）；LangGraph Studio：节点/边可视化 + **Assistants 不改图代码改行为**（且条件边需显式 path map 否则画错）；MAF：VS Code 左侧 YAML / 右侧图；n8n：整条可视化节点工作流；CrewAI：`plot()` 仅静态图 | **这是本轮调研暴露的最大需求级缺口**：用户诉求 ③ 在 v1.1.0 需求中**没有任何 REQ 承接**（反而被 OQ-IB-04 / OOS-06 推给接入方）。**须由 PM/用户裁决是否纳入**；若纳入，则需新增 REQ（**候选，见 §3.4**）。 |

### 3.2 缺口 → 业界可借鉴机制（G1~G8 全量对照）

| 缺口 | 描述（来自 PM 调用块） | 业界可借鉴机制（官方证据） | 借鉴成本 |
|------|------------------------|---------------------------|----------|
| **G1** | `install()` 无配置入口，专家写死在 `.py` | CrewAI 的 YAML + 装饰器注入（最轻）；Dify DSL（重量级）；MAF 声明式 YAML；AutoGen `load_component(config)` | 低（YAML 形态）/ 高（DSL 形态） |
| **G2** | `is_delegating` / `delegating_experts()` 是死字段，handoff 未实现，但提示里已写「可委托数据管家」 | MAF handoff 构建器（`turn_limits` / `approval_mode` / 稳定 `Id`）；OpenAI Agents SDK（handoff = 工具调用 + `input_filter`；**且 as_tool 才是 manager 语义**） | 中 |
| **G3** | `build_expert` 只用 `fallback_prompt`，**无提示文件加载**；注释声称的「按 name 加载主提示」机制不存在 | Dify：提示模板与模型参数**随 DSL 一起搬运**；CrewAI：`backstory` 在 YAML；MAF：`instructions` 在 YAML | 低 |
| **G4** | L1 语义路由生产哑火（范例目录为空） | semantic-router：Route = name + utterances（范例即定义）；未命中返回 `None` | 低（**数据工作 > 代码工作**） |
| **G5** | 专家注册表全局单例，多项目无法共存不同专家表 | LangGraph：`context_schema` + `Runtime.context`（官方正规路径，取代已弃用的 `config_schema`）；Assistants 不改图改行为；Dify：一个实例多应用；CrewAI：一个项目一份 YAML | 中 |
| **G6** | 关键词路由是纯 `substring in`，无词边界/同义词 | semantic-router：以**语义范例**取代字面子串（从根上绕开词边界问题） | 低 |
| **G7** | 路由质量无 eval/回归闭环（`tau` / `margin` 来自 PoC） | semantic-router：`evaluate` / `get_thresholds` / **`fit`**；DSPy：metric 驱动编译；LiteLLM：健康检查驱动的**运行期**反馈 | 低（阈值拟合）/ 高（DSPy 全量） |
| **G8** | `RouteDecision.tier/confidence` 未见结构化落盘/追踪 | OpenAI Agents SDK：Tracing **默认开启**且逐步 span；LiteLLM：`model_id` 确定性生成用于**溯源**；MAF：内置 `Workflow*Event` / `Executor*Event` 事件族 | 低-中 |

### 3.3 建议演进路线（P0 → P3）— 全部为 `[候选 — 待 PM/用户确认]`

> **顺序原则（来自本轮调研的核心结论）**：
> **① 先把「定义」变成数据，② 再谈「可视化」；先有单一真源的声明式定义，UI 才有可编辑的对象。**
> Dify（画布与 DSL 同源双视图）、MAF（YAML 是源、图是视图）、LangGraph Studio（assistants 是配置层）三者**一致证明**：可视化**不是**独立系统，而是**定义文档的一个视图**。若先做画布，必然产生第二真源 —— 这与本项目「单一真源」优势直接冲突（见 §4）。
>
> 此外：**「图结构」在 LangGraph 中是编译期的**（`StateGraph.compile()`）；可配置化的正规路径是 `context_schema` / Assistants（改**行为参数**），**不是**运行期改图。故「UI 配置工作流」在本项目上的现实边界是「**配置节点参数与专家集合**」而非「运行期增删节点」。

| 优先级 | 候选动作 | 复用本项目**已有接缝** | 证据来源 |
|--------|----------|------------------------|----------|
| **P0** | **让「可配置专家」真正可配置**：把专家注册表从 `.py` 字面量外置为项目级可加载数据（形态建议从**最轻**的「YAML/JSON 声明 + 启动期注入」起步，参考 CrewAI 的 `agents.yaml` 形态；**不引入 DSL 引擎**）。 | `install(specs)`（装配期整体替换，已存在！）、`validate_specs`（非空/名唯一/默认专家恰好一个/关键词无重复，已存在！） | CrewAI YAML 注入；AutoGen `load_component`；Dify DSL |
| **P0** | **在装配期做「定义合法性」fail-fast**：把 `validate_specs` 的既有校验作为外部定义的**准入闸门**，非法定义启动即报错（不得静默降级）。 | `validate_specs`、`install(specs)` | Dify 导入期版本兼容校验 + 警告；AutoGen「只从可信来源加载」；MAF 声明式→执行前编译 |
| **P1** | **把提示从代码里拿出来**：`build_expert` 支持按专家加载提示文件（对外部定义以「相对路径 → 文件」解析，**并且必须规定根目录边界，禁止任意路径加载**）。 | `build_expert`、`ExpertSpec`（提示字段） | Dify（提示模板随 DSL 搬运）；CrewAI `backstory`；n8n 的**反例**（"本地文件路径"作来源 = 安全反模式） |
| **P1** | **修掉 G2 的「两难」**：`is_delegating` / `delegating_experts()` **要么实现、要么删除**，不得留在「字段宣称支持、实现没有、提示还写着可委托」的不一致状态。若实现，须同时补齐三件护栏：**往返次数上限**（对齐 MAF `turn_limits`）、**敏感写操作强制人工确认**（对齐 MAF `approval_mode` / 本项目既有 `interrupt()` 确认门）、**模型可能不转交的兜底**（对齐 OpenAI「不能强制所有 agent 永远 handoff」→ 必须有非 handoff 的正常回答路径，呼应本项目「绝不无人应答」）。 | `ExpertSpec.is_delegating`、`delegating_experts()`、既有 `_gate` / `interrupt()` | MAF handoff；OpenAI Agents SDK handoff vs `as_tool` |
| **P1** | **专家表按项目生效（G5）**：把全局单例改为「按项目解析专家表」。**优先评估 LangGraph 官方路径**（`context_schema` + `Runtime.context`，取代已弃用的 `config_schema`），而非自造配置注入。 | `orchestrator_for(project_id)`（**已按项目缓存**，是天然的挂载点）、`install(specs)` | LangGraph `context_schema` / Studio Assistants；Dify 单实例多应用 |
| **P2** | **语义路由从「哑火」到「可用」（G4 + G6）**：补范例数据（**这是数据工作**）；以语义命中缓解纯子串匹配的粗糙（G6）。 | L1 语义路由既有装配点 | semantic-router：Route = 范例集、未命中返回 `None` |
| **P2** | **路由质量闭环（G7）**：先建**金标集**，再做阈值/边界的**有监督评估与校准**（参考 `evaluate` → `fit` 的形态）。**明确不引入 DSPy 全量优化器**（前提是有金标与稳定 metric；缺金标时引入是纯成本）。 | 路由阈值配置项（`tau` / `margin`）；REQ-NFR-IB-14 的可离线单测要求 | semantic-router `fit` / `evaluate`；DSPy（**作为反例**） |
| **P2** | **路由决策可追溯（G8）**：把 `RouteDecision` 的层级（L0~L3）与置信度、以及降级事件结构化落盘。**落点必须是本地**（与 REQ-NFR-IB-08 一致），**不得**上报第三方 SaaS。 | REQ-NFR-IB-06 既有日志纪律；`RouteDecision` | OpenAI Tracing（**形态**）；LiteLLM `model_id` 溯源；MAF 事件族 |
| **P3** | **UI 可视化配置（用户诉求 ③）**：**前置条件是 P0/P1 已完成**（定义已是数据、已有单一真源）。现实形态为「**定义文档的图形视图**」（对齐 Dify 双视图同源 / MAF 左 YAML 右图），**不是**独立画布。**必备工程约束**：条件边必须显式 path map / `Literal`，否则可视化必然画错（LangGraph Studio 官方明示）。**须先由 PM/用户裁决是否纳入 v1（OQ-IB-04 现为「由接入方自建」）**。 | 待 P0/P1 建立的定义层 | Dify 画布=DSL 视图；LangGraph Studio；MAF VS Code 双栏 |
| **P3** | **可选：LLM 侧健壮性**：如未来多端点/多 key，可借鉴 LiteLLM 的**分桶降级 + 组内 `order` 分层 + cooldown + 主动健康检查**形态（**只借配置形态，不引入 Proxy 组件**）。 | DR-04（LLM 端点可配置）、REQ-NFR-IB-13（降级矩阵）、REQ-FUNC-IB-21（fail-open） | LiteLLM `fallbacks` / `order` / cooldown / health check |

### 3.4 若用户决定纳入「UI 可视化配置」：候选需求点 `[候选 — 待 PM/用户确认]`

> **这些不是需求，是供 PM/用户裁决的候选**。若裁决纳入，应作为**新 REQ-FUNC 提案**提交 `requirements_spec.md` 的**定向修订**（不改既有编号），并由 PM 决定其优先级与是否阻塞。
> **注意**：其形态受三条既有硬约束的**刚性限缩**——(1) 数据不出本地（REQ-NFR-IB-08）；(2) 单一真源（REQ-FUNC-IB-02 / REQ-NFR-IB-11）；(3) 禁 Docker 全物理机直部署（DR-03）。

- **候选点 A**：**可视化只作为「定义文档的视图」，定义文档本身是唯一真源**（编辑 UI ↔ 定义文档双向 round-trip；对齐 Dify 画布↔DSL）。`[候选 — 待 PM/用户确认]`
- **候选点 B**：**可视化的编辑对象限定为「节点参数与专家集合」**（模型、提示、工具授权、关键词/范例、路由阈值、并行集合），**不包含运行期增删图节点** —— 因 LangGraph 图结构是**编译期**的。`[候选 — 待 PM/用户确认]`
- **候选点 C**：**配置的完备性校验必须在装配期 fail-fast**（复用 `validate_specs` 语义），非法配置不得静默生效。`[候选 — 待 PM/用户确认]`
- **候选点 D**：**OQ-IB-04（问答侧界面）与本诉求的关系须澄清**：现文档把「完整产品化界面」列为范围外并由接入方自建；若纳入 UI 配置，须先解决「配置界面在基座内还是由接入方提供」的边界。`[候选 — 待 PM/用户确认]`
- **候选点 E**：**若纳入，须显式排除**：插件市场/包管理、远程定义拉取（URL/任意文件路径）、多语言同构、Power Fx 式表达式、A2A/MCP 协议面、成本/配额/多租户。`[候选 — 待 PM/用户确认]`

---

## 4. 风险与反模式：通用化会破坏本项目哪些既有优势，以及如何守住

> 本节逐一对照本项目的**五项既有优势**（来自 `requirements_spec.md`）。每项给出「业界会怎么把你带偏」与「守住的具体做法」。

### 4.1 风险 R-1：**单一真源**被「定义文档 + 代码」双写破坏

- **业界诱导**：Dify/MAF/CrewAI 都引入了「外部定义 → 运行期」。若实现时**既保留 `.py` 字面量、又新增 YAML**，就会出现两个真源；UI 再引入第三份，必然漂移。
- **本项目既有优势**：`ExpertSpec` 单一真源 + 派生视图（`names` / `keywords_map` / `cn_map` / `data_experts` / `delegating_experts` / `default_expert`）；REQ-FUNC-IB-02 明确「改一个专家只需改这一处」。
- **如何守住**：
  1. **定义文档是唯一真源，代码只做派生**（对齐 AutoGen 的「component config 是蓝图」语义）；**禁止**「YAML 声明 + `.py` 再写一份」并存。
  2. **派生视图必须继续存在且由定义文档派生**（`names` / `keywords_map` / … 不得变成第二份手写数据）。
  3. **UI（若有）只能是定义文档的视图**，不得有自己的持久化存储（对齐 Dify 画布↔DSL）。
  4. **`install(specs)` 是唯一装配入口**：外部定义最终必须**收敛为 `ExpertSpec` 列表**再进入 `install`，不让外部格式渗透到派生层。

### 4.2 风险 R-2：**「绝不无人应答」**被通用化削弱

- **业界诱导**：MAF/OpenAI 的 handoff 是**模型决策**（官方明说"不能强制所有 agent 永远 handoff"）；Dify 的 Agent 节点也有 Max Iterations 上限后失败的可能；把「转交/路由」完全交给模型，就可能出现「无人应答」。
- **本项目既有优势**：REQ-FUNC-IB-19「任何一级失败都不得导致无人应答」、四级降级 + 默认专家兜底；REQ-FUNC-IB-21 fail-open。
- **如何守住**：
  1. **默认专家兜底是不可配置删除的**：`validate_specs` 已校验「默认专家恰好一个」——**配置化后这条校验必须保留且更严**（对齐 Dify 导入期校验、MAF 声明式编译期校验）。
  2. **handoff（G2）若实现，必须保留非 handoff 出路**：不得让「转交」成为唯一出口。
  3. **降级链的每一级都必须有下一级**：语义路由返回 `None` → LLM 分类 → …→ 默认专家，**不允许出现"死路"**（对齐 semantic-router 未命中返回 `None` 而非报错）。

### 4.3 风险 R-3：**framework-free** 被声明式配置层侵蚀

- **业界诱导**：Dify DSL、MAF YAML、CrewAI YAML 都是「配置里携带行为」；若解析器直接 `import langgraph` 或在配置里嵌入可执行表达式（MAF 的 **Power Fx**、Dify 的 Code 节点、n8n 的 Workflow JSON），可测试性与安全边界同时受损。
- **本项目既有优势**：注册表**不依赖编排框架**、可离线单测（REQ-FUNC-IB-02 约束）；`router.py` 顶层不 import langchain（REQ-NFR-IB-14）；`build_capability_digest` 是纯函数。
- **如何守住**：
  1. **定义文档的解析层必须是纯数据层**：只做「读 → 校验 → 产出 `ExpertSpec`」，**不得 import 编排框架**（对齐 AutoGen：`config` 与 runtime 分离）。
  2. **配置里不得出现可执行代码/表达式**（明确**不学** Power Fx / Code 节点 / 内联 Workflow JSON）。
  3. **沿用既有可离线单测要求**（REQ-NFR-IB-14）：解析与校验必须能在无网络、无框架环境下单测。

### 4.4 风险 R-4：**fail-fast** 被「宽容导入」替代

- **业界诱导**：为了「用户友好」，导入配置时给出警告后**强行继续**（Dify 明确会警告「DSL 版本差异显著」并允许强制导入，同时提示可能导致故障）。若照搬到本项目，会把「启动期可检出」退化为「运行期出怪事」。
- **本项目既有优势**：REQ-FUNC-IB-01「配置项缺失/非法须在启动期可检出」；REQ-NFR-IB-02「启动期或首次使用给出可读错误」。
- **如何守住**：
  1. **配置非法 = 拒绝启动**（fail-fast），**不提供「强制继续」开关**。
  2. **校验错误信息须可读且定位到具体键**（Dify 的「导入警告」形态可借鉴其**信息呈现**，但**结论必须是拒绝**）。
  3. **校验发生在装配期**（`install(specs)` / `validate_specs`），不推迟到首次请求。

### 4.5 风险 R-5：**secret 不进配置** 被「定义可搬运」反噬

- **业界诱导**：定义要能导出/搬运（Dify DSL、MAF YAML、n8n Workflow JSON），很容易顺手把「端点 + 凭据」一起塞进去；n8n 甚至支持从**URL / 本地文件路径**加载工作流定义。
- **本项目既有优势**：C-IB-02 / REQ-NFR-IB-07「凭据一律走环境变量，绝不硬编码、绝不提交入库、绝不出现在日志或 HTTP 响应」；REQ-FUNC-IB-01「凭据不得硬编码」。
- **如何守住**（业界三家做法一致，证据强）：
  1. **定义文档中只允许出现「配置键名」，不出现值**（Dify 官方：导出**默认排除**第三方工具 API key，需 `--include-secret` 才纳入并给出敏感警告）。
  2. **若定义里有 secret 字段，必须标记为「不导出」**（AutoGen 官方：`SecretStr` 字段不进 config）。
  3. **引用外部密钥一律经环境变量间接引用**（LiteLLM 官方：`model_list` 用 `os.environ/VAR`，**绝不内联**）。
  4. **禁止从任意 URL / 任意本地路径加载定义**（n8n 的 URL / Local File 来源是**安全反模式**，明确不学）—— 加载来源必须收敛到受控的、有根目录边界的配置源。

### 4.6 明确的「过度设计黑名单」（照抄即亏）

| 来源 | 明确不学的部分 | 理由 |
|------|----------------|------|
| Dify | 全功能节点库（Iteration/Loop/变量聚合/Code/触发器）、插件市场与 `.difypkg`、DSL 历史版本迁移矩阵 | 远超「RAG + 多专家问答」需要；引入包管理与供应链面 |
| MAF | Power Fx、Magentic/Group Chat 模式、A2A/MCP 协议面、.NET/Python 双语言同构、**「无反向转换」**（若做 UI 必须双向） | 与本项目规模、单语言、无跨信任边界诉求不符 |
| OpenAI Agents SDK | 100+ provider 抽象、Realtime、托管/服务端会话、第三方 SaaS tracing | 与 DR-04（单 LLM 端点）及 REQ-NFR-IB-08（数据不出本地）冲突 |
| CrewAI | Flow 全量状态持久化（改变「安全失败」语义）、自主 Hierarchical/Consensual 协作、`plot()` 静态图 | 与「路由确定性（temperature=0）」及既有会话语义冲突 |
| LangGraph | Postgres/Cosmos 级 checkpointer、LangGraph Platform/LangSmith Cloud、**运行期改图** | 与 DR-03（单实例、禁 Docker）及「图是编译期结构」的事实不符 |
| n8n | 整条可视化自动化引擎、本地文件路径 / URL 作为定义来源、计费语义 | 量级不符；路径/URL 加载是安全反模式 |
| semantic-router | 动态路由的参数抽取、多模态/行业预置路由、**自增长 route** | 「专家集合」必须是受控真源，自增长会让真源失控 |
| DSPy | 优化器体系（在**无金标集**时） | 前提不成立时引入是纯成本；且会破坏路由提示的确定性 |
| LiteLLM | 虚拟 key/预算/多租户成本跟踪/管理面板、cost-based & usage-based routing、Proxy 独立进程 | 无计费与多租户诉求；单 LLM 端点下无收益；新增组件与 DR-03 取向相悖 |

---

## 5. 与既有需求的对照索引（便于逐条核验，不改动既有文档）

| 既有 REQ | 本调研中相关的业界证据 | 是否有增量建议 |
|----------|------------------------|----------------|
| REQ-FUNC-IB-01（项目级配置驱动） | Dify DSL；CrewAI YAML；MAF YAML；AutoGen `load_component` | **无需求变更**；§3.3 P0 为实现侧建议（补 G1 落差） |
| REQ-FUNC-IB-02（专家注册表单真源） | CrewAI `agents.yaml`；Dify 应用定义 | **无需求变更**；§4.1 给出「守真源」的边界 |
| REQ-FUNC-IB-03（工具注册与能力声明） | n8n 子工作流输入契约；OpenAI Agents SDK `as_tool` | 无 |
| REQ-FUNC-IB-18（LangGraph 编排图） | MAF 五种编排；LangGraph `compile()` | **无需求变更**；§3.3 P1 给出「按项目生效」的官方路径（G5） |
| REQ-FUNC-IB-19（意图路由多级兜底） | semantic-router（范例 + 可训练阈值）；OpenAI guardrail/tripwire | **无需求变更**；§3.3 P2 为质量闭环建议（G4/G6/G7） |
| REQ-FUNC-IB-20（流式与会话生命周期） | LangGraph `interrupt()` + `Command(resume)`（官方推荐用法）；OpenAI Sessions/HITL | 无（现状与官方推荐一致） |
| REQ-NFR-IB-06（可观测性） | OpenAI Tracing；LiteLLM `model_id` 溯源；MAF 事件族 | §3.3 P2（G8）为落点建议（**必须本地**） |
| REQ-NFR-IB-11（模块边界） | AutoGen「config 是蓝图 ≠ 状态」；LangGraph 编译期图 | §4.3 给出「framework-free 不被侵蚀」的边界 |
| REQ-NFR-IB-13（可靠性与降级矩阵） | LiteLLM 分桶 fallback + `order` 分层 + cooldown + 健康检查 | §3.3 P3 为可选借鉴（**只借形态**） |
| REQ-NFR-IB-14（可测试性） | semantic-router 纯决策层可离线评测；DSPy metric | §4.3 强调解析/校验层须可离线单测 |
| OQ-IB-04（问答侧界面） | Dify 画布；LangGraph Studio；MAF VS Code 双栏 | **§3.1 / §3.4：用户诉求 ③ 在需求中无承接，须 PM/用户裁决** |
| OQ-IB-07（人工确认中间态） | MAF `approval_mode="always_require"`；LangGraph 动态 `interrupt()` | 无（机制已保留，默认不启用） |
| DR-04（云端 DeepSeek，端点可配置） | LiteLLM 统一抽象与降级 | §3.3 P3（可选） |

---

## 附录 A：本文件的自检声明

- [x] 本文件**未修改** `docs/requirements_spec.md`（v1.1.0 / APPROVED）与 `docs/user_stories.md`（v1.1.0 / APPROVED）；本文件为**新建**，未覆盖既有任何文件。
- [x] 本文件**未产出**本项目的架构决策、模块设计、接口签名（IFC-*）、ADR、代码或配置实现；凡涉本项目者均标注 `[候选 — 待 PM/用户确认]`。
- [x] 每条「能力断言」均尽量附**官方 URL**；仅见于第三方的结论**逐条标注「待官方证实」**；查不到的如实标注「官方文档未查到」。
- [x] **如实披露执行限制**：WebFetch 在本环境**全线不可用**（域安全校验失败），全部证据经 **WebSearch** 获得（对官方页面的检索摘要 + 官方 URL 定位），**未做原始页面抓取**。
- [x] 未臆造 API / 字段名：Dify 字段级 DSL（`agent_packages` / `soul` / 版本映射）与 n8n 完整 JSON schema **均明确标注非官方/未查到**。
- [x] 本文件**无任何凭据、令牌、口令或证书**；外部项目的密钥做法仅以「机制」形式引用（不含任何真实值）。
- [x] 本文件**未引入**架构阶段产物（无 IFC-*、无 ADR、无模块图）。
- [x] **status 已于 2026-09-27 由 PM 门控置为 APPROVED**（GR-A-002 = PASS_WITH_CONDITIONS）；两条遗留条件（WebFetch 不可用 → 证据经 WebSearch；诉求③ 需求级缺口须用户裁决）见 `docs/phase_status.md`。

## 附录 B：证据来源清单（按项目）

> 均为检索命中的**官方域名**（另标注例外）。

1. **Dify** — <https://docs.dify.ai/en/learn/key-concepts>；<https://docs.dify.ai/en/cli/reference/apps>；<https://docs.dify.ai/en/self-host/use-dify/build/workflow-chatflow>；<https://docs.dify.ai/zh/cloud/use-dify/nodes/agent>；<https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/submit-plugin-to-marketplace>；<https://enterprise-docs.dify.ai/en/3.12.x/use/nodes/agent>；<https://marketplace.dify.ai/plugin/langgenius/agent>；官方仓库文档源 <https://github.com/langgenius/dify-docs>（`en/guides/workflow/export_import.mdx`、`en/use-dify/getting-started/key-concepts.mdx`）。**官方仓库讨论（非文档）**：`langgenius/dify` Discussion #31561（「无字段级 DSL 规范」）。**第三方（待官方证实）**：`yzmw123/dify-workflow-dsl-skill`。
2. **MAF / AutoGen** — <https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/>；<https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff>；<https://learn.microsoft.com/en-us/agent-framework/workflows/declarative>；<https://learn.microsoft.com/en-us/agent-framework/agents/declarative>；<https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/component-config.html>；<https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/serialize-components.html>；官方文档仓库 <https://github.com/MicrosoftDocs/semantic-kernel-docs>、<https://github.com/MicrosoftDocs/azure-ai-docs>；官方仓库讨论 <https://github.com/microsoft/agent-framework/discussions/4450>。
3. **OpenAI Agents SDK** — <https://openai.github.io/openai-agents-python/>；<https://openai.github.io/openai-agents-python/ref/handoffs/>；`/guardrails/`、`/sessions/`、`/tracing/`；官方仓库 <https://github.com/openai/openai-agents-python>（`docs/handoffs.md`）。
4. **CrewAI** — <https://docs.crewai.com/en/concepts/agents>；<https://docs.crewai.com/en/concepts/flows>（版本化路径 `/v1.15.6/`、`/v1.15.17/`）。
5. **LangGraph** — <https://docs.langchain.com/oss/python/langgraph/checkpointers>；<https://docs.langchain.com/oss/python/langgraph/studio>；<https://docs.langchain.com/langsmith/add-human-in-the-loop>；<https://docs.langchain.com/langsmith/graph-rebuild>；<https://reference.langchain.com/python/langgraph/graph/state/StateGraph>；官方仓库 <https://github.com/langchain-ai/langgraph>（PR #5243 上下文 API）。**注**：调用块所列 `langchain-ai.github.io/langgraph` 未直接返回结果，现行文档域为 `docs.langchain.com`。
6. **n8n** — <https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow>；<https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflowtrigger>；<https://docs.n8n.io/build/flow-logic/break-workflows-into-smaller-parts>。
7. **semantic-router** — <https://docs.aurelio.ai/semantic-router/get-started/quickstart>；<https://semantic-router.readthedocs.io/en/latest/quickstart.html>；官方仓库 <https://github.com/aurelio-labs/semantic-router>（README / `docs/06-threshold-optimization.ipynb`）。
8. **DSPy** — <https://dspy.ai/>；<https://dspy.ai/current/getting-started/program-dont-prompt/>。
9. **LiteLLM** — <https://docs.litellm.ai/>；<https://docs.litellm.ai/docs/routing>；<https://docs.litellm.ai/docs/routing-load-balancing>；<https://docs.litellm.ai/docs/proxy/reliability>。

---
