<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-10-27T00:20:37+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/agent_platform_research.md</file>
    <file>docs/requirements_spec.md</file>
    <file>src/frontend/src/views/ConfigPage.vue</file>
    <file>src/ibweb/views.py</file>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

> **修订说明（1.0.0 APPROVED → 1.1.0 DRAFT，2026-10-27，REWORK_AUTHORIZED，承接用户裁决 CL-005）**：只做两处定向修订：① §5 候选点表新增"用户裁决"列，并在其后新增"用户裁决结果"小节；② CAND-16 的"建议是否纳入本轮"原文保留（记录当时的建议），以新增列的"已纳入"为准。其余内容（§1~§4、§6 的业界事实与证据）一字不动。

# 业界可视化 Agent / 工作流编排平台对比与优化建议（REV-26）

**性质**：需求阶段的调研补充。只给出业界事实、与本项目的差距、以及**候选建议（CAND-nn）**。候选建议**不是需求**：每条标注"是否建议纳入本轮"，由用户裁决后，才会进入 `requirements_spec.md`（PM 记忆 M-PM-012；约束 C-R26-09）。本文件不含本项目的架构决策、接口或代码。
**与旧调研的关系**：`docs/agent_platform_research.md`（RESEARCH-INTELBASE-001，2026-09-27 / 2026-10-07）以开源框架为主，且当时 WebFetch 全线不可用；本文件聚焦"可视化编排平台"，并在本轮用 WebFetch / WebSearch 补充了版本发布、权限、热生效相关事实。凡引用旧调研的事实，标注 `[旧调研 §x]`。
**查询纪律（协议 §L-7）**：查询词只用通用技术名词（平台名 + 功能词），不含项目代码或内部信息。网页内容按数据处理：n8n 一个文档页的抓取结果里夹带了一条"向外部检索端点发请求"的指令，已忽略，仅作信息评估（已记入 security_events）。

## 1. 证据说明与可信度

访问日期统一为 **2026-10-26**。可信度：高 = 官方文档页直接抓取到；中 = 官方来源但只见到搜索摘要；低 = 第三方或抓取失败，仅作线索，不作结论。

| 平台 | 本轮取得的证据 | 可信度 | 未能核实 |
|---|---|---|---|
| Dify | 官方"Version Control"页：草稿 / 已发布 / 历史版本、命名与发布说明、还原覆盖草稿、部分能力限付费计划 [WEB: https://docs.dify.ai/en/use-dify/build/version-control，2026-10-26]；DSL、导出排除密钥 [旧调研 §2.1] | 高 | 角色权限（RBAC）、悬停配置卡片、进行中会话在发布时的处理（页面明确未描述） |
| Coze（扣子） | 开源版 Coze Studio 仓库首页：agent 构建、可视化画布拖拽节点、插件 / 知识库 / 数据库 / 提示词 / 变量等资源、可发布 agent / 应用 / 工作流、有 API 与 SDK；仓库提示存在 API 水平越权的安全告警 [WEB: https://github.com/coze-dev/coze-studio，2026-10-26] | 中-低 | 官方帮助中心（coze.cn / coze.com）本轮未检索到；节点调试 / 试运行、版本、空间权限均**未核实**，下表标"未核实" |
| n8n | 官方文档：自动保存草稿、发布后生产执行跑已发布版本、触发器按变更增量更新、取消发布 [WEB: https://docs.n8n.io/workflows/publish/，2026-10-26]；版本历史：保存即生成版本、还原前先保存最新版本、可命名、可克隆 / 下载 JSON、24 小时之外的历史按套餐限制 [WEB: https://docs.n8n.io/workflows/history/，2026-10-26]；子工作流 [旧调研 §2.6] | 高 | AI Agent 节点与 MCP 客户端工具的细节（官方页未覆盖）；并发编辑保护；发布时进行中执行的处理（页面明确未描述） |
| Flowise | 官方 Agentflow V2 页：节点类型（Start / LLM / Agent / Tool / Retriever / HTTP / Condition / Condition Agent / Iteration / Loop / Human Input / Direct Reply / Custom Function / Execute Flow）、Condition 与 Condition Agent 的分支机制、Loop 最大次数默认 5、Agent 内每个工具可勾选"需要人工输入"、人工输入暂停时保存检查点、重启后可恢复 [WEB: https://docs.flowiseai.com/using-flowise/agentflowv2，2026-10-26] | 高 | 流程导出格式与 API 密钥机制（页面未覆盖）；版本管理 |
| Langflow | 官方"flows import"页：导出 JSON（含节点 / 边 / 元数据 / 视口 / 备注）、API Key 默认不导出，需勾选"Save with my API keys"，存于全局变量的只导出变量名；导入需目标实例有同名全局变量；每个 flow 可经项目级 MCP server 暴露为工具 [WEB: https://docs.langflow.org/concepts-flows-import，2026-10-26]；MCP 客户端组件、Playground [WEB: https://docs.langflow.org/mcp-client，2026-10-26，仅搜索摘要] | 高（导出）/ 中（MCP） | 草稿 / 发布与版本回滚、权限 |
| LangGraph / LangSmith Studio | Studio：图模式展示经过的节点与中间状态、助手与线程管理、提示词迭代、时间旅行、一键部署 [WEB: https://docs.langchain.com/langsmith/studio，2026-10-26]；助手（Assistants）把配置与图逻辑分离，每次编辑产生新版本且全部保留，可把任一版本设为活动版本，也是回滚方式；更新须提供完整配置、不与旧版本合并 [WEB: https://docs.langchain.com/langsmith/assistants，2026-10-26]；检查点与时间旅行 [旧调研 §2.5] | 高 | Studio 的悬停细节、热重载（官方页未描述；第三方称支持，不采信）；助手新版本是否保存即活动（页面未明确） |
| Microsoft Copilot Studio | 官方"发布"页：发布适用于所有关联渠道；**最新发布内容仅在新会话开始后才对用户可见**（多数渠道 30 分钟无活动结束会话；Teams 等持久会话渠道最长约 1 小时后生效，或用户输入"start over"）[WEB: https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels，2026-10-26]；官方"共享"页：聊天权限与协作编写权限分离；协作者可查看 / 编辑 / 配置 / 共享 / 发布但不能删除；另有仅看分析的"Analytics Viewer"、仅看与运行评估的"Agent Viewer"角色；会话记录权限单独设角色；多人编辑同一主题时显示"谁在编辑"，保存冲突时提供"放弃更改"或"另存副本" [WEB: https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-share-bots，2026-10-26]；方案（solution）与环境的 ALM [WEB: https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-overview，2026-10-26，仅搜索摘要] | 高 | 可视化画布悬停；无自由 DAG（主题式对话建模） |
| OpenAI Agent Builder / AgentKit | 官方发布文：可视化画布、拖拽节点、连接工具、自定义护栏；节点含 Agent / File search / Guardrails / MCP / User approval / If-else；顶部有 Evaluate / Code / Preview / Publish [WEB: https://openai.com/index/introducing-agentkit/，2026-10-26，仅搜索摘要]；官方指南页：编辑自动保存为草稿、发布生成新的主版本快照、API 调用可固定到旧版本、预览逐节点展示执行、可导出 Agents SDK 代码自托管；**页面写明 Agent Builder 已被弃用，计划于 2026-11-30 关闭，ChatKit 保留** [WEB: https://developers.openai.com/api/docs/guides/agent-builder，2026-10-26，单一来源，建议用户复核] | 中-高 | 节点完整清单与参数（页面指向另一参考页）；权限模型 |

**证据缺口的处理**：Coze 的试运行 / 版本 / 权限、Dify 与 Langflow 的权限模型、n8n 的 MCP 与并发编辑，本轮均**未能从官方来源核实**，下表一律标"未核实"，不用第三方博客补全。

## 2. 维度对比表

> 单元格只写已核实事实；"—"= 该平台无此概念；"未核实"= 本轮没取到官方证据。

| 维度 | Dify | Coze（Studio） | n8n | Flowise | Langflow | LangGraph / LangSmith Studio | Copilot Studio | OpenAI Agent Builder |
|---|---|---|---|---|---|---|---|---|
| 画布与节点模型 | 拖拽式 DAG；Workflow 与 Chatflow 共用画布；节点分类（触发 / 处理 / 逻辑 / 数据 / 高级 / 输出）[旧调研 §2.1] | 拖拽节点组装工作流 | 节点式工作流（本轮未取到画布细节） | Agentflow V2：14 类节点，含 Loop / Iteration / Execute Flow | 组件拖拽并连线（导出含节点与边） | 图模式展示已执行节点与中间状态；图本身由代码定义 | 主题（topic）式对话建模，非自由 DAG | 画布 + 类型化边，节点含 Agent / If-else / MCP / 人工批准 / 护栏 |
| agent 定义方式 | Agent 节点：选推理策略（Function Calling / ReAct）、工具白名单、最大迭代数 [旧调研 §2.1] | agent 构建器：挂接工作流 / 知识库等资源 | AI Agent 节点（本轮未核实） | Agent 节点：LLM 自主选工具 / 文档库；Tool 节点可确定性调用 | 组件组合 | 助手 = 同一图的不同配置（提示词 / 模型 / 工具） | 在门户内配置 agent、主题与工具 | Agent 节点内配置指令、工具、模型 |
| 路由与条件分支 | IF/ELSE 等逻辑节点（本轮仅确认存在逻辑类别） | 条件分支（未核实） | 条件 / 开关节点（未核实细节） | Condition（按值）与 Condition Agent（LLM 按场景分类，每场景一个出口） | 未核实 | 条件边须显式分支映射，否则 Studio 无法判定可达性 [旧调研 §2.5] | 主题触发（语义匹配）+ 多主题消歧 | If-else、分类类节点 |
| 工具与 MCP | 工具白名单；插件市场 [旧调研 §2.1] | 插件（官方商店插件需第三方授权密钥） | MCP 客户端工具等（未核实） | Tool 节点；Custom MCP；可在工作流中放 MCP 节点；每个工具可勾选"需要人工输入" | 作为 MCP 客户端调用外部工具；每个 flow 可暴露为 MCP 工具 | 工具在图代码中定义 | 工具 / 连接器；连接常绑定到用户身份，共享时需注意 | MCP 节点；File search |
| 权限与多租户 | 未核实 | 空间权限未核实；仓库提示 API 水平越权风险 | 未核实（本轮） | 未核实 | 导出时 API Key 默认排除 | 部署级权限（本轮未核实） | 聊天权限与编写权限分离；Analytics Viewer / Agent Viewer 等只读角色；会话记录单独角色；协作者不能删除 agent | 未核实 |
| 版本 / 草稿 / 发布 / 回滚 | 当前草稿 + 最新版本 + 历史版本；可命名并写发布说明；还原 = 整体覆盖草稿，且还原后仍需再发布；部分能力限付费计划 | 可发布 agent / 应用 / 工作流（版本细节未核实） | 编辑自动存草稿；发布后生产跑已发布版本；历史版本可还原 / 克隆 / 命名 / 下载 | 未核实 | 导出 JSON 含 `last_tested_version`；无发布概念（未核实） | 助手每次编辑生成新版本，全部保留，设为活动版本即回滚 | 发布适用于所有渠道；未发布的修改不影响用户 | 编辑自动存草稿；发布 = 新主版本快照；API 可固定旧版本 |
| 热生效机制 | 发布后"最新版本"对用户可见；**进行中会话如何处理文档未说明** | 未核实 | 发布后生产执行用已发布版本；触发器按变更增量更新；**进行中执行如何处理文档未说明** | 人工输入暂停时存检查点，重启后可恢复 | 未核实 | 图是编译期结构；配置通过助手版本切换 | **新内容只在新会话开始后生效**（空闲 30 分钟结束会话；持久渠道最长约 1 小时） | 发布生成新版本；调用方可固定版本 |
| 调试与运行轨迹 | 未核实（本轮） | 未核实 | 未核实 | 未核实 | Playground 试运行 | 图模式展示经过节点与中间状态；时间旅行（回放 / 分叉） | 测试对话面板；发布后用演示网站测试 | 预览逐节点展示执行；Evaluate 用 trace grader 评估；可导出代码 |
| 导入导出 | DSL（YAML），导出默认排除密钥，类型不同导出草稿或已发布版 [旧调研 §2.1] | 未核实 | 下载版本为 JSON | 未核实 | 导出 JSON；Key 默认不导出，全局变量只导出变量名；导入需目标有同名变量 | — | 方案（solution）导出导入，托管 / 非托管 | 导出 Agents SDK 代码 |
| 并发编辑 | 未核实 | 未核实 | 未核实 | 未核实 | 未核实 | 未核实 | 显示"谁在编辑"；保存冲突时二选一：放弃更改 / 另存副本 | 未核实 |

## 3. 业界共性模式（对本项目最有参考价值的 8 条）

1. **草稿与已发布分离**（Dify、n8n、OpenAI、Copilot Studio、LangSmith 助手）：编辑永远落在草稿，发布才影响线上；发布产生可回滚的版本快照。本项目今天是"保存 = 落盘，重启才生效"，用户新诉求"保存后生效"相当于把草稿与发布合并为一步——这是业界主流做法之外的取舍，风险需要靠"保存前校验 + 差异确认 + 回滚"补偿（CAND-01 / 02）。
2. **回滚 = 把旧版本变成新版本再发布**（Dify 还原到草稿再发布；LangSmith 把旧版本设为活动；n8n 还原前先保存当前）：不删历史，回滚自己也留痕。
3. **新版本对"新会话"生效**（Copilot Studio）：避免进行中的对话被中途换配置。这是本项目 OQ-R26-04 的直接证据；Dify / n8n 的文档对此**没有说明**，说明这是一个容易被忽略的设计点。
4. **类型化节点 + 受限节点集**（Flowise、OpenAI）：节点类型有限（Agent、Condition、Human Input、Loop 等），循环有最大次数（Flowise 默认 5）。本项目只做 DAG，无需循环；若未来支持循环必须带上限。
5. **人工批准是工具或节点的一等属性**（Flowise 的"需要人工输入"、OpenAI 的 User approval 节点；MAF 的 approval_mode [旧调研 §2.2]）：本项目已有人工确认（`interrupt()`），可考虑把"某工具需人工确认"暴露为权限配置项（CAND-07）。
6. **导出默认排除密钥**（Dify、Langflow）：与本项目 C-IB-02 同向；若做导入导出（CAND-08），必须沿用。
7. **权限分层：用 ≠ 改 ≠ 发布 ≠ 看分析**（Copilot Studio）：聊天权限、编写权限、只读评估、会话记录各有独立角色，协作者不能删除。对应本项目 CL-004(b)（OQ-R26-06）。
8. **MCP 作为工具扩展面**（Flowise、Langflow、OpenAI、n8n）：几乎所有平台都在接 MCP，但这扩大了供应链与数据外发面，且与本项目 OOS-14 / OOS-10 冲突，需单独立项（CAND-09）。

## 4. 本项目现状与差距（要点）

详见 `requirements_spec.md` §现有能力 vs 用户诉求对照表。与业界对照的要点：

| 能力 | 本项目现状（文件:行） | 业界做法 | 差距 |
|---|---|---|---|
| 画布可编辑 | 只读（`ConfigPage.vue:757-759`） | 全部可编辑（Copilot Studio 除外，非 DAG） | 大 |
| 悬停 / 点击看配置 | 无（`ConfigPage.vue:238` 仅标签） | 多数在节点上直接展开配置 | 大（本轮 REQ-FUNC-001 / 002） |
| 版本 / 回滚 | 无；审计仅记字段名（`views.py:1015-1041`） | 草稿 / 发布 / 历史版本普遍具备 | 大（REQ-FUNC-017） |
| 并发冲突 | 已有 409 乐观并发（`views.py:979-993`） | Copilot Studio 另有"谁在编辑"与"另存副本" | 小 |
| 权限分层 | 仅 admin / manager 可写（`policy.py:50-54`） | 多档角色 | 中（REQ-FUNC-010） |
| 热生效 | 无，需重启（`ConfigPage.vue:675-676`） | 发布即生效，对新会话 / 新执行生效 | 大（REQ-FUNC-014） |
| 试运行 / 预览 | 无 | OpenAI Preview、Langflow Playground、Copilot Studio 测试面板 | 中（CAND-02） |
| 运行轨迹 | 无 | LangGraph Studio、OpenAI 预览逐节点 | 中（CAND-03） |

## 5. 优化提示与建议（候选点，须用户裁决）

> "建议纳入本轮"的含义：我（需求分析师）认为若不做，会让本轮已确认的"热生效 + 自由画布"风险过高，或成本很低。"后续"= 价值明确但可拆出本轮。"不建议"= 与既有裁决或长期决定冲突。**所有候选点在用户裁决前都不是需求。**

| ID | 建议 | 业界依据 | 与本轮需求 / OQ 的关系 | 建议是否纳入本轮 | 成本 / 风险 | 用户裁决（2026-10-27） |
|---|---|---|---|---|---|---|
| CAND-01 | 保存后生效采用"单步保存并生效 + 版本快照 + 一键回滚"，而不是纯"保存即覆盖" | Dify / LangSmith / OpenAI 均有版本快照与回滚（§2） | 已转为 REQ-FUNC-017（Should）；建议用户在 OQ-R26-03 选 C 时把它升为 Must | **是** | 版本存储小（配置文本）；需定保留数量（OQ-R26-08） | **已纳入**：REQ-FUNC-017（升为 Must） |
| CAND-02 | 保存前"试运行 / 预览"：在不影响线上的前提下，用草稿配置对话测试一次 | OpenAI Preview、Langflow Playground、Copilot Studio 测试面板、Dify 草稿运行 | 目前只有差异确认（REQ-FUNC-016），没有真正的试运行；热生效 + 自由 DAG 下，试运行是最有效的风险缓冲 | **是（建议作为 Should 追加）** | 需要"草稿配置可独立运行"的能力，架构影响中等；试运行会调用云端 LLM（数据外发与现有问答同口径） | **已纳入**：新增 REQ-FUNC-023 / US-029（Should） |
| CAND-03 | 运行轨迹可视化：历史回答可回放"经过了哪些节点"；后续再做实时高亮 | LangGraph Studio 图模式；OpenAI 预览逐节点执行 | 对应 OQ-R26-01 的 B / C；与 REQ-NFUNC-004（回答记录含版本号）相衔接 | **后续**（OQ-R26-01 选 A 时不做） | 需要结构化的节点级运行记录；中 | 后续（本轮不做；OOS-R26-09） |
| CAND-04 | 新版本对新提问生效，进行中的回答用旧版跑完（或进一步：新会话才生效） | Copilot Studio：新内容仅在新会话生效 | 已转为 REQ-FUNC-015；OQ-R26-04 | **是** | 需要"每次提问绑定版本"的运行记录；中 | **已纳入**：REQ-FUNC-015 |
| CAND-05 | 图合法性校验规则集：无环、可达、有出口、默认专家可达、条件边必有"否则"；将来若支持循环，必须带最大次数上限（参考 Flowise 默认 5） | LangGraph Studio 对条件边的显式映射要求；Flowise Loop 上限 | 已转为 REQ-FUNC-013；循环列入 OOS-R26-08 | **是** | 低；纯函数、可离线单测 | **已纳入**：REQ-FUNC-013 |
| CAND-06 | 受限节点集：不提供代码 / 表达式节点，不提供 HTTP 任意调用节点 | Flowise 的 Custom Function / HTTP 节点会扩大攻击面；本项目 OOS-10 | 已体现在 OQ-R26-02 推荐项 A 与 OOS-R26-04 | **是（作为范围护栏）** | 无 | **已纳入**（范围护栏）：OQ-R26-02=A、OOS-R26-04 |
| CAND-07 | "某工具需人工确认"作为 agent 权限配置项（对应一次调用前要人工点确认） | Flowise 的"Require Human Input"、OpenAI 的 User approval、MAF approval_mode [旧调研 §2.2] | 属 REQ-FUNC-009 运行时权限的自然延伸；本项目已有人工确认机制 | **可选**（若用户希望对写类工具加护栏则纳入；当前工具集以只读检索为主，价值有限） | 低-中 | 可选（不入需求） |
| CAND-08 | 定义的导入 / 导出（JSON）：导出默认排除凭据，导入走同一套服务端校验；仅限同一实例内的项目间复用或备份 | Dify DSL、Langflow JSON、n8n 下载 JSON | 与 OOS-R26-03（跨项目共享）冲突部分需用户另行裁决；导入必须经 REQ-FUNC-013 的校验 | **后续** | 中；要守住不从任意路径 / URL 加载（旧调研 §4.5） | 后续（本轮不做；OOS-R26-09） |
| CAND-09 | 外部工具经 MCP 接入 | Flowise / Langflow / OpenAI / n8n 均支持 | 与 OOS-14（不新增工具本体）、OOS-10（A2A / MCP 协议面）冲突；涉及数据外发与供应链 | **不建议本轮**，需用户单独立项并重新评估安全面 | 高 | **不纳入**（OOS-R26-01） |
| CAND-10 | 路由质量评测（金标集 + 阈值校准）与"试运行 / 评测"结合 | OpenAI Evaluate（trace grader）；semantic-router 的阈值拟合 [旧调研 §2.7] | 与 G7（路由无评测闭环）同源；不属本轮用户诉求 | **后续** | 中；需先有金标集 | 后续（本轮不做；OOS-R26-09） |
| CAND-11 | 权限分层采用"看 / 改 / 管理（回滚与授权）"三档，并考虑为只读评审者提供独立的只读角色 | Copilot Studio 的 Analytics Viewer / Agent Viewer、协作者不可删除 | 已转为 REQ-FUNC-010 与 OQ-R26-06 | **是** | 低-中 | **已纳入**：REQ-FUNC-010（三档） |
| CAND-12 | 冲突时提供"另存为草稿副本"，并显示"谁正在编辑"的提示（后者仅作提示、不加锁） | Copilot Studio 的编辑者列与"放弃 / 另存副本" | 副本对应 OQ-R26-09 的 B；"谁在编辑"本轮不进需求 | 副本：**是**；编辑提示：**后续** | 低 | 副本：**已纳入**（REQ-NFUNC-005）；编辑提示：后续（OOS-R26-09） |
| CAND-13 | 每次回答的运行记录带配置版本号，并在版本历史中可反查 | OpenAI 固定版本；LangSmith 助手版本 | 已转为 REQ-NFUNC-004 | **是** | 低 | **已纳入**：REQ-NFUNC-004 |
| CAND-14 | 画布体验：悬停卡片 + 侧边详情、"自动整理布局"按钮、大图时分组折叠与小地图 | 通用画布产品共性（本轮无单一官方来源，视为经验性建议） | 与 REQ-FUNC-001 / 012、REQ-NFUNC-009 相关；"自动整理 / 折叠 / 小地图"未进需求 | 悬停 + 侧栏：**已纳入**；其余：**可选（Could）** | 低 | 悬停 + 侧栏：**已纳入**（REQ-FUNC-001 / 002）；其余：可选（不入需求） |
| CAND-15 | 版本命名与发布说明（一句话说明本次为何改） | Dify 命名版本 + 发布说明；n8n 命名版本 | 可附在 REQ-FUNC-016 / 017 上；目前变更摘要为系统生成 | **可选（Could）** | 低 | 可选（不入需求） |
| CAND-16 | AI 辅助生成 agent 提示词草稿（一句话描述 → 提示词） | 多个平台的 builder 具备（本轮无单一官方来源，视为经验性建议） | 即 OQ-R26-10 的 C；提示词内容会发往云端 DeepSeek | **不建议本轮**，需用户单独裁决数据外发 | 中；安全与成本需评估 | **已纳入**（用户裁决 OQ-R26-10，范围扩大为"按需求生成整个 agent 草案"）：REQ-FUNC-018~022、REQ-NFUNC-014 / 015、C-R26-11 / 12 |
| CAND-17 | agent 作为另一个 agent 的工具（"agents-as-tools"）与子流程复用 | OpenAI Agents SDK 的 as_tool [旧调研 §2.3]；Flowise Execute Flow；n8n 子工作流 [旧调研 §2.6] | 本项目 `is_delegating` 仍是遗留字段（旧调研 G2）；自由 DAG 之后，"调用另一个 agent"可以用边表达，是否另需子流程待议 | **后续** | 中 | 后续（本轮不做；OOS-R26-09） |
| CAND-18 | 对配置类接口做越权专项测试（跨项目读写、查看档调写接口、请求体伪造项目标识） | Coze Studio 仓库对 API 水平越权的提示 | 已转为 REQ-NFUNC-007 与 US-019 / US-010 的 AC | **是** | 低 | **已纳入**：REQ-NFUNC-007、US-010 / 019 |

### 对用户裁决的汇总建议（1.0.0 时的建议，保留原文）

- **建议本轮一并纳入**：CAND-01（回滚）、CAND-02（试运行，建议追加为 Should 的新需求）、CAND-04、CAND-05、CAND-06、CAND-11、CAND-12（副本）、CAND-13、CAND-18。其中 CAND-02 是目前需求里**尚未覆盖**的最大一块：热生效 + 自由 DAG 之后，没有"先试再发"，一次误操作就直接影响线上。
- **建议后续**：CAND-03、08、10、12（编辑提示）、17。
- **不建议本轮**：CAND-09（MCP）、CAND-16（AI 生成提示词，涉数据外发）。
- **可选**：CAND-07、CAND-14（其余部分）、CAND-15。
- 对 OQ 的联动：如果用户选 OQ-R26-03 = C（本文件推荐），则 CAND-01 与 CAND-02 应同时纳入，否则"保存即生效"缺少安全网。

### 用户裁决结果（2026-10-27，CL-005）

- **纳入**：CAND-01、02、04、05、06、11、12（副本）、13、18，以及 CAND-16。其中 **CAND-02**（保存前试运行：用草稿配置试对话、不影响线上）新增为 Should 需求 REQ-FUNC-023 与故事 US-029；**CAND-16** 的范围由"AI 生成提示词草稿"扩大为用户原话所述的"按需求生成可被画布编排、适配所在项目的 agent 草案"（REQ-FUNC-018~022），并由用户确认数据外发至现有云端 DeepSeek（C-R26-11、REQ-NFUNC-014 / 015）。
- **后续（本轮不做）**：CAND-03、08、10、12（编辑提示部分）、17。
- **不纳入**：CAND-09（MCP 接入）。
- **可选（不入需求）**：CAND-07、CAND-14 的其余部分（自动整理布局 / 分组折叠 / 小地图）、CAND-15。
- **Builder 的业界参照说明**：用户裁决指定产品内 Agent Builder 类似套件内 `.claude/agents/agent-builder.md`（按需求生成、固定维度百分制评审、按项目画像注入约束、优化存量）。该文件是需求参照而非产品内容；对应关系见 `requirements_spec.md` §现有系统基线"参照物"小节。业界平台中，OpenAI Agent Builder 等的"画布 + 预览 + 发布"形态与此相邻，但本轮没有取得其"按需求生成 agent"的官方证据，不作结论。

## 6. 局限与待复核

- Coze、Dify（权限）、Langflow（版本与权限）、n8n（MCP / 并发）、Flowise（导出）的相应维度本轮未取到官方证据，已在表中标"未核实"，**没有用第三方文章补全**。
- OpenAI Agent Builder 页面称其已被弃用并将于 2026-11-30 关闭：该信息仅来自一次页面抓取，**建议用户自行复核**；若属实，应避免将其作为长期对标对象，只作"画布 + 发布版本"形态的参考。
- 搜索摘要来源（标"仅搜索摘要"）的事实，可信度低于直接抓取的官方页。
- 本文件不比较各平台的价格、性能、生态，也不替用户选型。
