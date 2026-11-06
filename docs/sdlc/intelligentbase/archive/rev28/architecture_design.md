<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-03T17:38:46+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计（REV-28 增量）— 平台级内置「顾问 agent」

## 修订记录

| 版本 | 时间 | 说明 |
|---|---|---|
| 1.0.0 | 2026-11-02T21:19:03+08:00 | 初版（APPROVED） |
| 2.1.0 | 2026-11-03T17:38:46+08:00 | 定向修订（invocation intelligentbase-R28-GROUP_B-003，REWORK_AUTHORIZED；落点用户裁决 CP-003「Q7 纳入。 Q6：A 其他推荐」，经主会话转述；依据 requirements_spec 4.0.0 / user_stories 4.0.0、画像 1.1.0 P11-3、`docs/external_api/deepseek_search_fetch.md`）：(1) **Q7 纳入**：搜索提供方 = DeepSeek 官方 Search API——新增 **ADR-R28-11**（适配器、凭据复用、错误 / 重试 / 超时）；ADR-R28-04 追加 **R1 修订**（"本轮不实现厂商适配器"被取代，结论以 R1 为准）；(2) 新增 **ADR-R28-12** 网页抓取方案（比较 DeepSeek Fetch / 保留本地 SafeFetcher / 混合；**选保留本地抓取**，总开关缺省关闭、netguard、名单与上限均保留，`lxml` 保留）；(3) 新增 **ADR-R28-13** 搜索提供方替身的生产禁用（REQ-FUNC-019；**选启动失败**，只报键名）；(4) Q1=A：核对 ADR-R28-09 与"联网结果不纳入保真"**不一致**（原文从被委托产出与联网结果中抽取保护片段），以 **ADR-R28-09-R1** 订正；Q4=A：A-12 / A-12b 转为已裁决；Q2=A：Builder 摘要多两个工具名为明示例外（无设计变更，见复核表）；Q5=A、Q6=A：无架构影响；(5) 新增 ADR-R28-03 / 08 / 10 的 R1 订正与"ADR 影响复核表"；(6) 删除两个键：`IB_WEB_SEARCH_API_KEY`、`IB_WEB_SEARCH_BASE_URL`（不再有第二份搜索密钥，端点固定为资料所载）；(7) 开放问题增 OQ-ARCH-R28-06~09 与 A-13~A-20，待裁决题 AQ6~AQ9（均 NORMAL，给出推荐，不阻塞）。**其余 ADR 不变** |
| 1.1.0 | 2026-11-02T21:50:53+08:00 | 定向修订（invocation R28-GROUP_B-002）：(1) 落点用户裁决 CP-002（经主会话转述）：**AQ1=B**（用户否决推荐 A）——ADR-R28-09 改写：顾问汇总失败或保真守卫两次不通过 ⇒ 统一致歉文本、不展示被委托 agent 原答，原"回退原答"保留为已否决方案；同步 ADR-R28-01 后果 (4) 与叶子论述、风险 R-7；AQ2=A、AQ3=A、AQ4=A、AQ5=A 记为已裁决并回写 ADR-R28-02 / 03 / 05；Q7=C：ADR-R28-04 明确本轮只交付端口 + Null / Fake + 注册表，不含任何厂商适配器，OQ-ARCH-R28-01 维持开放；(2) GR-B-001 F02：更正"用户已明示不引入 langchain-community"的归属（实为主会话建议，用户原则为「尽量复用，不要重复造轮子」）；(3) 输入基线更新为 requirements_spec 3.0.0 / user_stories 3.0.0。其余 ADR 不变 |

**范围与基线**：只写 REV-28 增量。REV-27 已批准设计归档于 `docs/sdlc/intelligentbase/archive/rev27/`，REV-26 设计（ADR-53~69）与项目基线 `docs/architecture_design.md` 继续有效，凡未在"继承 / 变更登记"中改动的决策一律沿用。需求依据 = 同目录 `requirements_spec.md`、`user_stories.md`（均 4.0.0，含 3.1.0 修订 CP-003 / D-07 与 2.1.0 修订 CL-003 / D-06）。ADR 编号 `ADR-R28-NN`；模块 / 接口见 `module_design.md`（`MOD-R28-NN` / `IFC-R28-NNN`）。
**用户裁决（经主会话转述）**：Q3「顾问 通过路由去把问题委托给kb-agent， kb-agent 处理后把结果给顾问agent汇总、整理措辞、格式。」→ 编排式委托；Q4 生产可出网、搜索提供方为可替换外部服务且默认关闭、「尽量复用，不要重复造轮子」；OQ-R28-05=A、06=A、09=C、10=A+C、11=A、12=A。
**用户裁决（2.1.0 增补，CP-003，经主会话转述，原话「Q7 纳入。 Q6：A 其他推荐」，"其他推荐" = Q1~Q5 取推荐项 A）**：Q7 本轮纳入 DeepSeek 官方 Search API；Q3=A 搜索提供方替身只允许离线 / 测试；Q4=A 致歉文本固定中文；Q2=A Builder 摘要多两个工具名；Q1=A 联网结果不纳入保真；Q5=A OBS-1 不在本轮；Q6=A 进入部署计划。
**设计边界声明（协议 §N，2.1.0 改写）**：画像 1.1.0 已补 P11-3，DeepSeek Search / Fetch 的端点、鉴权、字段、错误码、限流与计费**只以** `docs/external_api/deepseek_search_fetch.md` 为出处（本文标 `[P11: docs/external_api/deepseek_search_fetch.md:§节名]`）；**不联网查证**（闭源 API，§N-3），也不凭记忆补全。资料**没有写**的事项（超时数值、Fetch 单域名 QPS、429 / 5xx 是否重试与是否计入上限、DeepSeek 对内网地址 / 重定向的处置、Search 的 403 / 404 语义）一律作为设计参数给出保守缺省，登记 `[ASSUMPTION]` 与开放问题（OQ-R28-15(b)(c)），**不写成已知事实**。资料由主会话整理、PM 未核对原页面（画像 P11-3 备注），故契约字段在目标机人工核对原页面前视为"以资料为准、待人工核实"（OQ-R28-15(a)）。

## 架构概览

**本次改动在现有系统中的位置**：落在四处——(1) 编排运行期（`ib/orchestration/dag.py` + `Orchestrator._run_dag_turn`）：回合前置"理解"步骤、`route` 旁路、顾问汇总节点的输入与保真校验；(2) 工具层（`ib/tools`、`ib/llm._execute_tool`）：新增两个内置工具与"平台限制类参数"机制、工具执行超时；(3) 配置域（`ib/config/graph.py` 校验、种子资产、`seed_project`、目录与创建项目接口、Agent Builder 评审口径）；(4) 前端（新建项目勾选、配置页"加入 / 移除顾问"、admin 的联网上限页）。**不新增运行单元、不新增节点类型、不新增 Python 依赖**（`lxml` 为显式声明既有间接依赖，ADR-R28-12 论证保留；DeepSeek 适配器用 stdlib `urllib`，不引入 HTTP 库）。2.1.0 增量：(5) 搜索端新增 `DeepSeekSearchProvider`（`src/ib/webtools/deepseek.py`）与其离线替身，凭据复用 LLM 密钥的同一解析点，提供方替身在非离线配置下被拒绝。

```
                       ┌──────────────── ib-web 进程（同一进程，无新单元）────────────────┐
 用户提问 ──► Orchestrator._run_dag_turn
                │  (仅 view.advisor_id 非空时)
                ├─► TurnUnderstander (MOD-R28-10)   意图 + 消解后问句 + 话题 + 澄清   [ADR-R28-02]
                │        └─ needs_clarification ─► 直接答复澄清话术（不进图）
                ▼
              run_dag(state: query=delegate_query, advisor_turn{…})                    [ADR-R28-01]
                START → route-1 ──[kb-agent / 其他已启用 agent]──► agent ──┐
                           └─[__else__ = 不委托 / 旁路]───────────────────┼─► advisor(with_upstream) → END
                                                                         │      │
                                       （无环；advisor 是唯一叶子）◄──────┘      │ 工具循环
                                                                                   ▼
                                                  web_search / web_fetch (MOD-R28-05) [ADR-R28-03/04/08]
                                                     └─ WebEgressGate(审计先行·预算·并发闸) → SafeFetcher（直连目标站，ADR-R28-12）
                                                                                          └→ DeepSeekSearchProvider（HTTPS POST → api.deepseek.com，ADR-R28-11）
                _collect(leaf=advisor) → _aggregate(单叶子直通) → 单条 content            [ADR-R28-09 保真守卫在 advisor 节点后]
```

**关键质量属性（引 REQ-NFUNC）**
- REQ-NFUNC-001 / 002（未启用项目逐位不变）：所有新行为由 `view.advisor_id` / 授权 / 配置**显式门控**；默认专家集合 `builtin_default_registry()` 不动；`validate_graph` 的新规则只在"顾问模式"下产生错误；路由算法、`_aggregate` 单叶子直通、kb-agent 种子与授权不动。唯一非"项目级"的可见变化是全局工具目录多出两个工具名（见 ADR-R28-05 后果与架构裁决 AQ3）。
- REQ-NFUNC-003 / 005（注入与外发）：**结构性**隔离——委托发生在任何网页内容出现**之前**（回合前置步骤 + 图），读取网页的节点没有"委托"能力；外发载荷类型只含检索词 / 网址；出站文本经"与私有语料逐字重叠"闸门（ADR-R28-08）。
- REQ-NFUNC-004（SSRF）：解析一次、逐址校验、**钉住已校验 IP 连接**、每跳重定向重校验、仅 80/443、禁代理（ADR-R28-03）。
- REQ-NFUNC-007（超时）：工具层协作式期限 + `_execute_tool` 通用看门狗；无实测前端到端时延标"未验收"（OQ-R28-11=A）`[TBD-R28-1]`。
- REQ-NFUNC-006（凭据，2.1.0 改写）：**复用现有 DeepSeek API Key，不新增任何凭据**——与 LLM 调用同一解析点（`LlmKeyStore.get()` → 兼容回退 `IB_LLM_API_KEY`，`composition.py:817-822`、`ib/llm/__init__.py:461-466`），装配期读取一次传入适配器；不进 `GlobalConfig` 的可打印字段、日志、审计、定义文档、前端（ADR-R28-11）。
- REQ-NFUNC-005 / 004（2.1.0）：发往 DeepSeek 的载荷类型只含 `query`、`count`（`need_content=false`），**不含** `ori_question`、`localization`；抓取由本机直连目标站，**待抓取网址不发往 DeepSeek**，被拒网址不发往任何外部服务（ADR-R28-11 / 12）。
- REQ-FUNC-019（2.1.0）：搜索提供方替身只在 `IB_OFFLINE_MODE` 下可用，生产配置为替身 ⇒ **启动失败，只报键名**（ADR-R28-13）。
- 可测性（C-R28-02）：端口 `SearchProvider` + 内存替身 `FakeSearchProvider`、`SafeFetcher` 的 `FetchTransport` 注入点、`TurnUnderstander` 的 LLM 替身——全部离线。

## 部署视图

| 组件 | 运行单元 | 环境（画像 P7） | 变更 |
|---|---|---|---|
| `ib.advisor` / `ib.webtools` / `ib.orchestration` / `ib.config` / `ib.tools` / `ib.llm` / `ib.runtime` / `ibweb.*` | `ib-web`（waitress `--threads=8`，`src/deploy/systemd/ib-web.service:49-52`） | dev/local、CI、production | **需重启 ib-web**；迁移 009 随 `ExecStartPre=… --ensure-schema` 自动应用 |
| 搜索提供方开关 / 抓取开关 | `/etc/intelligentbase/ib-web.env`（0600，**由用户编辑**；仅写键名） | production | 新增 `IB_WEB_SEARCH_PROVIDER`（`none`\|`deepseek`；`fake` 仅离线）、`IB_WEB_FETCH_ENABLED`、`IB_WEB_GOVERNANCE_BACKEND`（可选）；**2.1.0 删除** `IB_WEB_SEARCH_BASE_URL`、`IB_WEB_SEARCH_API_KEY`（端点固定、密钥复用 LLM Key，**不新增任何凭据项**）；`src/deploy/env.example` 删去这两个占位并更新注释；**env 变更后的 restart / unit 改动由用户执行**（画像 P7） |
| DeepSeek API Key（搜索与 LLM 共用） | 台账库 `llm_key` 单行表（管理页 `PUT /api/llm-key` 轮换）；兼容回退 `IB_LLM_API_KEY` | production | **无新增位置**；轮换后 **重启 ib-web 同时对 LLM 与搜索生效**（现有 ADR-32 语义，`views.py` `llm_key_endpoint` 文档串；见 ADR-R28-11 与 AQ7） |
| 前端静态资源 | 目标机本地 `npm run build` → web root | production | 需重新构建发布；不重启服务 |
| ib-worker / ib-embed / qdrant | systemd | production | **无改动、不重启** |
| CI | GitHub Actions `ci.yml` | CI | 迁移检查步骤追加 009（语法 / 重放 / 单源）；`selfcheck.py` 追加用例；依赖安装增加 `lxml`（经 requirements*.txt） |
| 出站网络 | 运维侧（用户执行）出站 ACL / 防火墙 | production | 搜索：`api.deepseek.com:443`（与 LLM 同一服务方，已需放行）；抓取（总开关开启时）：公网 80/443（ADR-R28-12 选保留本地抓取的代价）；作为 SSRF 的第二道防线（OQ-ARCH-R28-04），非本设计的唯一防线 |

无 staging（P7）；无新增 systemd 单元（C-R28-03）；无容器（P8）。

## R26 / R27 继承 / 变更登记

| 既有决策 | 本轮处理 | 说明 |
|---|---|---|
| R26 ADR-56 图结构与受限节点集（7 种节点） | **Accepted（继承）** | 不新增节点类型（C-R28-01）；顾问是一个普通 agent 节点 |
| R26 ADR-57 层归一化 + 中继节点 | **Accepted（继承）** | 顾问汇聚点跨层边由既有中继处理（`ib/config/graph.py::layerize_graph`）；零改动 |
| R26 ADR-61 每 agent 自己的授权 / 工具闭包 | **Accepted（继承）并扩展** | 扩展点：`ToolSpec.config_parameters`（ADR-R28-06）、`BoundTool.timeout_s`（ADR-R28-03） |
| R26 ADR-69 / R27 前端结构（页面壳 + 纯函数模块 + 手写 store） | **Accepted（继承）** | 新增 `advisorPlan.ts` 纯函数模块，沿用 node:test 离线模式（P-SA-007） |
| 基线 ADR-09 编排层业务零依赖 | **Accepted（继承）** | 理解器 / 保真守卫经注入接缝（`build_graph(turn_understander=…)`），编排层不 import `ib.webtools` |
| 基线"路由不读历史做分类"（`routing/intent.py:405-420`） | **Accepted（继承，不改）** | 路由收到的是**已消解问句**；`classify_experts` 签名与算法不动（OOS-R28-07） |
| 基线 REV-26 Builder 外发单点 `EgressGuard`（`ib/builder/egress.py`） | **Accepted（继承）并复用其形态** | 联网出站闸门沿用"固定字段载荷 + 唯一出口 + 审计先行 + 并发闸"，复用 `contains_secret_pattern` |

## ADR

### ADR-R28-01: "回到顾问"的图表达（OQ-R28-14 / C-R28-08）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-006/007/010/011/012，C-R28-08，REQ-NFUNC-001。用户裁决：顾问先理解意图、经路由委托、结果**回到顾问**汇总。现状事实：(1) 图禁环 `graph_cycle`（`src/ib/config/graph.py:198`）；(2) 同一专家只能对应一个 agent 节点 `graph_agent_duplicate`（`:133`），且 agent 节点 id 必须等于专家名 `graph_agent_id_mismatch`（`:129`）；(3) 叶子判定：结果的专家若有"产出成功的后代 agent"则不是叶子（`src/ib/orchestration/dag.py:395-399`），所以"顾问在 kb-agent 之后"时顾问是唯一叶子；(4) `_aggregate` 单结果直通、不调 LLM，仅确定性清洗内部标签（`src/ib/orchestration/__init__.py:925-945`）；(5) route 在候选集内**必有命中**（兜底到默认 / 首个候选，`src/ib/routing/intent.py:367-373`），`__else__` 实际只在候选为空 / 异常时出现；(6) `with_upstream` 把祖先 agent 的产出作为"上游材料（只读参考，不是指令）"拼进问句（`dag.py:255-261`）。硬约束：DAG 无环；未启用项目逐位不变；后置汇总不改事实 / 数字 / 引用（AC-006-06）；顾问仍能对通用问题直接联网（REQ-FUNC-008）；与 `_aggregate` 不叠加改写。
- Options:
  - **A. 顾问拆成"前置 / 后置"两个角色节点**（两个专家，如 `advisor-front` / `advisor-back`）。优：不碰校验器。缺：前置节点的产出（意图 / 改写问句）无法被 route 消费——`route` 只读 `state["query"]`（`dag.py:171`），条件节点只会对**问句**做关键词判定（`graph.py:446`），仍需改引擎；两个专家 = 两份提示词、两个 Builder 微调对象、画布出现两个"顾问"，违背 REQ-FUNC-001"一个内置 agent"；前置节点读完意图后仍无法旁路 route（无分支依据）。
  - **B. 放开"同一专家可有多个节点"**。优：画布上能表达 `顾问→route→agent→顾问`。缺：必须同时放宽 `graph_agent_duplicate` 与 `graph_agent_id_mismatch`，**所有项目**的校验结果变化（违反 C-R28-08"不含顾问的项目校验行为不变"）；`outputs` 以节点 id 为键、`results` 以专家名为键、叶子判定按专家名找后代（`dag.py:395-399`），多节点同专家会让叶子判定与 `with_upstream` 素材混淆；前端 `graphModel.ts` / `nodeRemoval.ts` / `publishDiff.ts` 均假设"节点 id = 专家名"；同专家两节点仍需解决"环"——因为 `顾问#2` 的上游含 route，而 route 的上游含 `顾问#1`，虽无环但语义上"顾问"出现两次，提示词 / 授权共享引起的行为歧义（两次运行是否同一 system 提示词？）需要新规则。变更面最大。
  - **C. 顾问为单个 agent 节点，置于委托链路之后作汇聚点（`with_upstream`），"理解"下沉为回合前置步骤（非图节点）**。优：零新增节点类型、零校验放宽；顾问 = 一个专家，提示词 / 授权 / Builder 都只有一份；`顾问`是**唯一叶子**，`_aggregate` 单叶子直通，天然不叠加改写；通用问题经 route 旁路（`__else__` → 顾问）直接由顾问联网作答；画布上"顾问 ← 各 agent、顾问 ← route.__else__"可见、可编排。缺：引擎需要小改（`route` 旁路、顾问输入块、顾问不计步数上限）；意图识别不在画布上可见（但在顾问的详情面板说明）。
  - **D. 新增 `aggregator` 节点类型（或新增 `input_mode`）**。优：语义直白。缺：违反 C-R28-01"不新增节点类型"；前端 `ADDABLE_KINDS`、校验器、差异清单、`graphModel.ts` 全线扩展；对未启用项目的保存校验输入域也变宽。否决。
- Decision: 选 **C**。图形态（"顾问模式"默认图，`canonical_graph_with_advisor`）：`START → route-1`；`route-1 --[agent 名]→ 各已启用非顾问 agent`；`route-1 --[__else__]→ advisor`；每个被委托 agent `→ advisor`；`advisor(with_upstream) → END`。无环证明：层序 `start < route < 被委托 agent < advisor < end`，每条边严格升层（既有 `layerize_graph` 的前置条件）；`route→advisor` 的 `__else__` 边跨两层，由既有中继节点承接。三项底线逐条满足：(1) 无环 —— 回边不存在，"回到顾问"是**汇聚而非回路**；(2) 未启用项目逐位一致 —— 新校验规则、`route` 旁路、顾问输入块、理解步骤全部以 `view.advisor_id`（专家 `advisor` 存在且 `is_delegating=True` 且启用，见 ADR-R28-05）为前提；(3) 不改事实 —— ADR-R28-09 的保真守卫。**与 `_aggregate` 的关系**：顾问产出成功时，所有被委托 agent 因"有成功产出的后代（顾问）"而不是叶子，`DagOutcome.results` 只含顾问一条，`_aggregate` 走 `len(texts)==1` 直通分支，仅做确定性标签清洗——**不再调用 LLM 融合，不叠加改写**；顾问自身失败（或保真守卫两次不通过）时**不再让被委托 agent 成为叶子**：顾问节点以统一致歉文本作为自己的产出（仍是唯一叶子，见 ADR-R28-09、AQ1=B），`_aggregate` 同样走单叶子直通，被委托 agent 原答不进入最终答复。确定性清洗的标签集在顾问模式下**剔除顾问自己的中文标签**（否则正常语句"财务顾问""我是您的顾问"会被删字；`_strip` 用 `forbidden_labels(cn_labels)` 对全文做子串删除，`orchestration/__init__.py:917-923, 1325-1340`），其他 agent 标签（如"知识库助手"）仍被清除。顾问**不计入** `route.max_expert_steps` 的已执行数（出口节点不得被步数上限跳过，否则答复缺失）。`route` 旁路：回合状态带 `route_skip` 时 `make_route` 直接选 `__else__`、不调用路由器（意图为寒暄 / 通用 / 拒答时）；顾问模式下路由器抛异常的兜底改为"默认专家（若在候选内）"，不再空命中（保证专业问题不因路由故障丢失知识库）。校验新增两条仅顾问模式生效的规则：`advisor_self_delegation`（route 出边分支键 = `advisor`，AC-009-03 "路由候选含顾问自身"）、`advisor_branch_target_invalid`（顾问节点为 route 出边目标但分支键 ≠ `__else__`）；环 / 同专家重复 / 停用专家引用沿用既有错误码（AC-005-04、AC-009-03/05）。
- Consequences: 正向——不含顾问的项目校验输入域、运行路径、前端节点集合均不变；顾问只有一份提示词 / 授权，Builder 与画布体验与其他 agent 一致；单叶子使"提问者看到的答复只来自顾问"成为结构事实（AC-010-04）。负向——(1) 引擎多三处受控改动（`make_route` 旁路、`make_agent` 顾问输入块、`_collect`/步数豁免），回归面集中在 `dag.py`，由"未启用项目同输入逐字相同"回归集守住；(2) "意图识别"不是画布节点，不可被用户在画布上替换（只能改顾问提示词与整张图）；(3) 用户手工搭出非标准图（如 AC-005-01 的 `顾问→A→END`）时，顾问不是叶子，"答复只来自顾问"不再成立——这是用户显式编排的结果，校验不拦（REQ-FUNC-006 要求规则对顾问无特例），在顾问详情面板给出提示文案；(4) 顾问汇总失败或保真两次不通过时返回统一致歉文本、不展示被委托 agent 原答（AQ1=B，用户裁决）——此时已检索到的有用信息对提问者不可见，换来"答复只来自顾问、内部分工不外露"在失败路径也成立。

### ADR-R28-02: 会话上下文进入 DAG 路径（REQ-FUNC-013~015；OQ-R28-09=C；OQ-R28-06=A）
- Status: Proposed
- Type: decision
- Context: DAG 路径下只有 `route` 节点接收 `history`（`src/ib/orchestration/dag.py:170-174`），agent 节点只拿到当前问句（`:246-262`、`:333-345`）；路由刻意不把历史喂给分类器（`src/ib/routing/intent.py:405-420`，`current_query` 剥离历史前缀 `:83-107`）。会话历史由 `Orchestrator._load_history` 取最近 `max_history_messages` 条（20，`src/ib/orchestration/__init__.py:986-996`）；存储为进程内 `MemorySessionStore`（2000 会话 / 24h，重启丢失，`src/ib/streaming/__init__.py:207-225`）。用户裁决：改写独立问句 + 给顾问少量最近轮次（C）；会话沿用进程内（OQ-R28-06=A）。
- Options:
  - **A. 只做"追问改写为独立问句"**。优：路由 / kb-agent 看到的就是完整问句；缺：顾问作答时缺语境（语气承接、"回到刚才说的"需历史），不满足 OQ-R28-09=C。
  - **B. 把历史直接塞给顾问与各 agent，不改写**。缺：route 与 kb-agent 仍看到残缺追问（`search_knowledge` 的 query 由 kb-agent 的 LLM 自行生成，质量不可控），违背 REQ-FUNC-014"交给路由的问题以消解后的完整问题为准"；且要给每个 agent 改输入形态，扩大对未启用项目的影响面。
  - **C. A + 顾问输入块（用户裁决）：回合前置"理解"步骤一次产出 {意图集合, 消解后完整问句, 委托子问句, 话题关系, 是否需澄清}；顾问节点另得"最近对话"块**。优：满足 014 / 015 与 OQ-R28-09=C；改动局限于顾问模式。缺：每轮多一次 LLM 调用（延迟 `[TBD-R28-1]`）。
  - **D. 让路由分类器读历史**。违反 OOS-R28-07 与基线"不喂历史"设计，否决。
- Decision: 选 **C**。(1) **理解步骤**（`TurnUnderstander`，MOD-R28-10）在 `Orchestrator._run_dag_turn` 内、`run_dag` 之前执行，**仅当** `build_graph(turn_understander=…)` 被注入（编译期由 `view.advisor_id` 决定，见 `ib/runtime/compile.py`）。它读取**整个保留窗口**（≤ `max_history_messages`），用路由角色（温度 0）的 LLM 单次调用输出受约束 JSON，解析容错、失败 fail-open 为"原样透传"（`resolved=原问句，delegate=原问句，intent=unknown`，路由照常运行）。(2) **回合状态**：`run_dag(..., advisor_turn=AdvisorTurn)` 把 `query` 置为 `delegate_query`（路由与被委托 agent 看到的就是消解后的子问句，REQ-FUNC-014），`route_skip` 在无可委托意图时为真；`AdvisorTurn.history_digest`（窗口内消息，按字符预算从最旧处裁剪，固定 8000 字符 `[ASSUMPTION A-3]`，AQ2=A 已裁决；**最近一条消息始终保留**，被裁掉的消息全部早于保留下来的消息，窗口之外的消息不进入，见 IFC-R28-014）、`resolved_query`、`original_query`、`intents`、`topic` 只供顾问节点渲染输入块（`render_advisor_input`），不进入路由器与其他 agent。(3) **话题切换 / 回归**：由理解步骤依据完整窗口判定 `topic ∈ {continue, switch, return, new_session}`；`switch` 时 `resolved_query` 必须是独立问句、不得带入前一话题实体（AC-013-01）；`return` 由模型从窗口内重新关联（AC-013-02），不依赖用户声明（AC-013-03）。(4) **澄清短路**：`needs_clarification`（指代对象不唯一 AC-012-02、无历史的残缺追问 AC-012-04、空白 / 纯符号 AC-008-04）时不进图、不调用任何工具，直接以澄清话术作为唯一 `content`（仍写入会话历史）。(5) **对"历史不进分类器"设计的影响**：路由器**仍然不读历史做分类**——它收到的是已消解问句，`classify_experts` 签名 / 算法不变；`run_dag` 仍把 `history` 传给 `route`（现状如此，供粘性回落），顾问模式下粘性只在零信号时介入，行为同现状。(6) **零变化保证**：理解步骤 / `AdvisorTurn` / `route_skip` / 输入块均不存在于未启用项目的执行路径（`_understander is None`），`run_dag` 的新增关键字参数缺省 `None` ⇒ 与现状逐位一致；`_save_history` 仍存**原始问句**与最终答复，会话键 / 隔离 / 20 条窗口 / 24h 过期 / 重启丢失全部沿用（REQ-NFUNC-009，OQ-R28-06=A）。(7) **评测**：意图 / 上下文评测流程做成离线可断言的指标计算库 + 目标机用真实 LLM 运行的脚本（`src/scripts/advisor_eval.py`），评测集数据待用户提供（OQ-R28-12），之前验收为"待评测集确认"。
- Consequences: 正向——历史对 route / kb-agent 的影响通过"消解后的问句"这一**单一窄通道**传递，路由与 kb-agent 的代码、提示词、检索一律不改（REQ-NFUNC-002）；窗口内第 11 轮仍可消解第 1 轮指代（AC-011-01）。负向——(1) 每个顾问回合多 1 次 LLM 调用，加上顾问自身与 kb-agent，共 ≥3 次，延迟未测 `[TBD-R28-1]`；(2) 理解步骤的准确率完全取决于 LLM，需评测集（REQ-NFUNC-008）；(3) 窗口按"消息条数"计（20 条 ≈ 10 轮），超出窗口的内容无法回溯（AC-011-04，顾问请用户补充）；(4) 历史中的助手答复若含网页派生内容，会二次进入理解步骤的提示词——理解步骤把历史当数据并且输出字段受枚举 / 长度约束（`delegate_query` ≤ 300 字符），这是缓解而非根除，写入风险。

### ADR-R28-03: 联网工具 `web_search` / `web_fetch` 的接入、执行安全与治理（REQ-FUNC-016/017/018，REQ-NFUNC-004/005/007/010）
- Status: Proposed
- Type: decision
- Context: 唯一登记点 `register_builtin_tools`（`src/ibweb/composition.py:476-494`，调用点 `:418, :887, :1120, :1203, :1758, :1778`）；工具授权与参数闭包由 `build_agent_tools`（`src/ib/tools/__init__.py:416-450`）按 agent 构造；`_execute_tool` 同步直调、无超时（`src/ib/llm/__init__.py:624-635`）；`run_tool_loop` 的未授权工具回调形态 `on_unauthorized`（`:530-567`）；`waitress --threads=8`（`ib-web.service:52`）使阻塞型联网调用直接占用请求线程（容量约束，M-SA-006）；`Builder` 已有"唯一出口 + 审计先行 + 并发闸"先例（`src/ib/builder/egress.py`）。
- Options:
  - **A. 进程内工具：新增 `ib.webtools`（`SafeFetcher` + `WebEgressGate` + 工具实现），注册进同一登记点；超时 / 预算 / 域名 / SSRF / 审计全部在工具层与 `_execute_tool` 看门狗内落实**。优：零新增运行单元（C-R28-03）；授权、参数、差异清单、Builder 目录全部沿用既有机制；离线可测。缺：占用 ib-web 线程（用并发闸限制）；DNS 解析不可中断（用带超时的小线程池隔离）。
  - **B. 独立"抓取代理"进程 / systemd 单元**。优：隔离最强。缺：新增运行单元须回架构评审（画像 P7、C-R28-03）；新增部署、监控、IPC 面；对一个单次 GET 过重。
  - **C. 复用 `langchain-community` 的网页 / 搜索工具**。缺：为少量 REST 调用引入庞大依赖树；其 `requests` 栈不提供"钉住已校验 IP + 逐跳重校验"，SSRF 要求（REQ-NFUNC-004）仍需自写；与用户原则「尽量复用，不要重复造轮子」的取舍见 ADR-R28-04：此处"复用"以不新增重依赖、不削弱 SSRF 约束为界（"不引入 langchain-community"是主会话建议，非用户原话）。
  - **D. 仅靠运维层出站防火墙**。缺：不可离线测试，且不覆盖域名白 / 黑名单、预算、注入隔离；只作第二道防线。
- Decision: 选 **A**，要点如下。
  1. **注册与授权**：`register_builtin_tools(registry, *, web: WebRuntime | None = None)`（`web=None` ⇒ 装配 `NullWebRuntime`，工具以"联网服务未配置"降级）。工具对未授权 agent 不可见——沿用 `build_agent_tools` 只绑定该 agent 授权的工具；顾问种子默认**不授权**任何工具（AC-001-01）。工具 `needs_scope=False`，且在能力摘要（`build_capability_digest`，`src/ib/tools/__init__.py:124-145`）中隐藏，**不改变路由 L2 提示词**（REQ-NFUNC-001）。
  2. **LLM 可见参数最小化**：`web_search(query)`、`web_fetch(url)`；其余（条数、超时、语言 / 地域、域名名单、正文长度、类型白名单、每轮次数 / 字节上限）全部是"平台限制类参数"，由配置闭包注入且**不可被 LLM 覆盖**（ADR-R28-06）。
  3. **执行超时（两层）**：(i) 协作式期限——`SafeFetcher` / 提供方适配器使用 `deadline = 开始时刻 + timeout_s`，每次 socket 操作取 `min(剩余, 单次上限)`，分块读取时检查；DNS 解析在隔离小线程池内 `future.result(timeout=剩余)`；(ii) 通用看门狗——`BoundTool.timeout_s`（= 配置超时 + 1 秒宽限）非空时，`_execute_tool` 把调用交给模块级 `ThreadPoolExecutor`（`ib-tool`，8 线程），超时返回"（工具执行超时）"并上报事件；`timeout_s is None`（现有 `search_knowledge`）走原同步路径，**零变化**。默认 `web_search` 10 秒 / `web_fetch` 15 秒（INF-4 已确认），30 秒替身在 ±1 秒内被终止（AC-016-06）。
  4. **SSRF（`UrlGuard` + 钉 IP 连接）**：只允许 `http` / `https`；拒绝带 userinfo 的网址；端口只允许 80 / 443 `[ASSUMPTION A-5]`；**一律经 `getaddrinfo` 解析**（天然覆盖十进制 / 十六进制 / 八进制 IP 写法与 IDN），对返回的**全部**地址要求 `ipaddress.ip_address(...).is_global` **且**不在项目自有的显式补充拒绝网段内（回环、私有、链路本地 169.254.0.0/16、CGNAT 100.64.0.0/10、`192.0.0.0/24`、`198.18.0.0/15`、云元数据 169.254.169.254 / fd00:ec2::254、IPv4 映射与 NAT64 的内嵌私有地址、组播 / 保留）；显式网段不依赖 `is_global`，因为官方文档记载 `is_global` 在 3.13 修订过边界范围、`100.64.0.0/10` 在其中既非 private 也非 global（[WEB: https://docs.python.org/3/library/ipaddress.html，2026-11-02]），而项目允许 Python `>=3.11,<3.14`（画像 P1）；任一地址不合格即整体拒绝；连接使用**已校验的字面 IP**（HTTP 直接连；HTTPS 用 `ssl` 默认上下文校验证书并以原主机名做 SNI / 主机名校验），消除 DNS 重绑定 TOCTOU；重定向手动处理，最多 3 跳，**每一跳重新走完整校验**（含域名名单）；`ProxyHandler({})` 禁用环境代理；不转发凭据 / Cookie；`Accept-Encoding: identity`；按块读取并在 `max_bytes` 处停止。拒绝原因只返回枚举短码（`private_address`、`scheme_not_allowed`…），不回显解析结果与内部拓扑。
  5. **域名名单**：`allow_domains` / `deny_domains`（逗号 / 换行分隔的 ASCII 域名后缀，小写，禁止协议头 / 空格 / 通配符以外字符），**黑名单优先**；每个 agent 的授权参数里各一份；保存期逐项校验并指出"第几项非法"（AC-016-04）。`web_search` 返回的结果网址不过滤（只展示），但顾问若要 `web_fetch` 其中的网址则走同一名单。
  6. **用量上限**：`TurnBudget`（线程安全）按 `turn_id` 记录**本轮联网调用总数 / 抓取总字节 / 联网累计耗时**；每个工具以"自己的 `max_calls_per_turn` 与全局上限取小"比较**本轮总调用数**（AC-016-03）；抓取字节同理；累计耗时受全局 `max_seconds_per_turn` 约束（保护 8 个请求线程）。超限的调用**不发生**，工具返回"已达本轮联网上限"文本，顾问据此降级说明。
  7. **全局上限 admin 设定、项目只能调低**：ADR-R28-07。
  8. **并发闸**：`WebEgressGate` 持 `BoundedSemaphore(3)`（≤ 请求线程数 8 的 3/8 `[ASSUMPTION A-6]`），拿不到立即返回 `busy`（M-SA-006：快速失败、禁止无界排队）。
  9. **审计与可观测**：每次出站前**先写审计**（沿用 `ConfigAuditEntry` / `config_audit_store`，`action="web.search"|"web.fetch"`，`object_summary` 仅含工具、主机名、字节上限，**不含完整查询与网址路径**），审计失败则**不发送**（fail-closed，与 Builder 一致）；运行日志追加结构化 `advisor_turn` 事件（意图类别、委托的 agent、联网主机、各步耗时 / 状态、降级原因、是否引用外部来源，REQ-NFUNC-010），字段加入 `ib/observability` 白名单；凭据值绝不进入任何一处。
  10. **外发声明**：`EgressDescriptor` 不改字段；新增 `Deps.egress_web: tuple[EgressDescriptor, ...]`，仅当搜索提供方已配置或抓取已启用时非空，元素为 `(remote=True, endpoint_host=<搜索主机>, data_categories=["web_search_query"])` 与 `(remote=True, endpoint_host="*", data_categories=["web_fetch_url"])`（`"*"` = 任意公网主机，受名单约束 `[ASSUMPTION A-7]`）；`GET /healthz/deps` 在非空时追加键 `egress_web`，**为空时响应与基线逐字节相同**（AC-017-02）；启动日志 `startup.succeeded` 之外追加一条 `startup.web_egress`（`src/ibweb/composition.py:955-966` 同风格）。
  11. **默认关闭**：`IB_WEB_SEARCH_PROVIDER` 缺省 `none`；`IB_WEB_FETCH_ENABLED` 缺省 `0`（AQ4=A 已裁决，AC-015-05/06、AC-016-08）；搜索关闭时工具返回 `not_configured`，其余功能不受影响（AC-014-04）。**总开关与授权相互独立**：`web_fetch` 工具恒登记，保存期授权不受总开关限制（AC-016-08 "保存成功"）；总开关关闭时 `fetcher is None`，`web_fetch` 调用在**预算预留、出站文本闸、审计、出站之前**直接返回固定短语「当前未开启网页抓取」（出站 0、不写 `web.fetch` 审计、不占并发闸），顾问据此如实告知（不声称已读取网页）；开关打开但 agent 未授权仍由 `build_agent_tools` 不绑定该工具。`GET /api/config/catalog.web.fetch_enabled` 暴露开关状态（AC-015-06）。
- Consequences: 正向——全部能力在同一进程内、可离线测试；SSRF 防护由代码结构（钉 IP + 逐跳校验）而非运维约定保证；未授权 agent 的工具列表中联网工具出现次数 = 0。负向——(1) 联网调用占用请求线程，最坏情形单轮 `max_seconds_per_turn`（默认 30 秒）× 并发闸 3 个同时联网的回合；其余回合联网时快速失败降级，需目标机实测校准 `[TBD-R28-2]`；(2) `getaddrinfo` 无法取消，超时后线程在后台继续至 OS 解析超时，用小线程池（4）+ 池满即拒绝兜底；(3) 全局工具目录新增两个工具名，非顾问项目的配置页"可授权工具"列表可见（但无任何 agent 被授权，行为不变；见 AQ3）；(4) 端口白名单 80 / 443 会拒绝少数非标准端口站点，可接受。

### ADR-R28-04: 搜索提供方适配器与网页正文抽取（C-R28-09 / C-R28-10；OQ-R28-08 / 13）
- Status: Proposed（2.1.0：Decision (1)(2) 与 Consequences 负向 (1) 被 **ADR-R28-04-R1 / ADR-R28-11** 取代，结论以 R1 为准）
- Type: decision
- Context: 用户原话「尽量复用，不要重复造轮子」；搜索服务是可替换外部服务、默认关闭；厂商未定、仓库无其 API 文档，画像无 P11（协议 §N，禁止联网查询闭源 API）；项目 HTTP 客户端风格 = stdlib `urllib`（`src/ib/embedding/__init__.py:36-37, 259, 294-312`）；依赖清单 `src/requirements.txt` 不含 `lxml`，`python-docx>=1.1,<2.0`（`:32`）经 PyPI 元数据 `requires_dist: lxml>=3.1.0`（[WEB: https://pypi.org/pypi/python-docx/json，2026-11-02]）间接引入；`requirements-offline.txt:25` 也含 `python-docx`；本地 `python3 -c "import lxml"` 实测 `ModuleNotFoundError`（开发机未装，CI 经 offline 清单安装）。
- Options（搜索适配）:
  - **A. 项目自有端口 `SearchProvider`（输入 `SearchQuery`、输出 `SearchOutcome`、永不抛）+ `NullSearchProvider` + `FakeSearchProvider` + 提供方注册表；生产适配器（stdlib `urllib` 风格）留给下一轮**。优：与 `Embedder` 的"窄端口 + 生产适配器 + 内存替身"同构（M-SA-001）；更换厂商只新增一个映射类；零新依赖；离线可测。缺：每个厂商仍需一个小映射类（用户裁决 Q7=C：厂商延至下一轮，本轮不实现任何厂商适配器，也不含任何网络代码）。
  - **B. `langchain-community` 的厂商封装**。缺：重依赖、厂商绑定、仍受 `[UNSOURCED]` 约束；主会话建议不引入，用户原则为「尽量复用，不要重复造轮子」（据此仅在"不新增重依赖且不削弱安全约束"时才算复用，B 不满足）。
  - **C. LLM 厂商自带联网搜索**。OQ-R28-08 已裁决不采纳（C-R28-09 取 A 方向）。
  - **D. 自建 / 自托管元搜索（如 SearXNG）**。新增运行单元，违反 C-R28-03 与 OOS-R28-09，否决。
- Options（正文抽取）:
  - **E. `lxml.html`（显式声明依赖）**。优：复用已在生产 venv 中的库；容错解析、`xpath` 去除 `script/style/nav/footer`、`itertext` 取正文；BSD-3-Clause，当前稳定 6.1.3（[WEB: https://pypi.org/pypi/lxml/json，2026-11-02]）。缺：依赖当前是**间接**的，不显式声明则 python-docx 将来换实现即失效；C 扩展解析不可信 HTML 的攻击面（libxml2）。
  - **F. stdlib `html.parser`**。优：零依赖、攻击面小。缺：正文块划分 / 编码探测要自写更多代码（更像"造轮子"）。
  - **G. `trafilatura` / `readability-lxml`**。优：正文质量高。缺：新增多个传递依赖与许可证登记，超出"尽量复用"；本轮无质量证据要求。
- Decision: 搜索选 **A**；抽取选 **E**。(1) 适配契约见 module_design IFC-R28-004：错误分类仅用项目自有枚举 `SearchErrorKind`（`not_configured / timeout / unreachable / rate_limited / auth_failed / quota_exceeded / bad_response / rejected`），**厂商状态码到枚举的映射、端点、请求 / 响应字段、鉴权头、限流一律 `[UNSOURCED]`，本轮不实现任何厂商适配器**（用户裁决 Q7=C：只实现端口 + Null + Fake + 注册表 + 配置读取；厂商选择与适配器延至下一轮，OQ-ARCH-R28-01 维持开放；用户另询 DeepSeek 是否有搜索服务，由主会话调研，结论不在本文设计），待用户补画像 P11-3 后另立增量；厂商端点主机由运维经 `IB_WEB_SEARCH_BASE_URL` 提供并要求 `https://`，主机名进 `describe_egress`。(2) 密钥只经 `/etc/intelligentbase/ib-web.env` 的 `IB_WEB_SEARCH_API_KEY` 注入，组合根读取一次传入适配器构造函数，**不进入** `GlobalConfig` 的可打印字段、日志、审计、定义文档、前端（REQ-NFUNC-006）；`env.example` 仅占位，`deploy_templates_have_no_secrets` 自检继续有效。(3) 抽取用 `lxml.html`，**在 `requirements.txt` 与 `requirements-offline.txt` 显式声明 `lxml>=5.0,<7.0`**（上界取当前主版本之上；下界 `[ASSUMPTION A-9]` 为保守值，未在目标机验证）；仅使用 `lxml.html.fromstring` 与 `xpath`，**不使用已拆出的 `lxml.html.clean`**；`import lxml` 惰性执行，缺失时 `web_fetch` 以 `extract_unavailable` 降级而非使整个 `ib.webtools` 导入失败。(4) 与禁用项核对：lxml 不在画像 P8 禁用列表；`ci.yml` 版本门（Python / bcrypt / langchain-openai / PyMuPDF / Docker）不受影响；不引入 torch / transformers / onnx 相关依赖。
- Consequences: 正向——零新增第三方库（lxml 本已在 venv），更换搜索厂商不影响顾问与工具形态（AC-014-05）；离线测试靠 Fake。负向——(1) 真实联网效果无法在本轮验收，真实适配器与目标机联网验证作为后续增量与人工项；(2) 显式声明 lxml 会让两份 requirements 清单多一行，需同步 `tech_stack.md` 许可台账；(3) lxml 是 C 扩展，解析前先按 `max_bytes` 截断并限制 `max_chars`，降低恶意超大 / 深嵌套文档风险。

### ADR-R28-05: 顾问作为"平台级可选内置 agent"的落地（REQ-FUNC-001~005）
- Status: Proposed
- Type: decision
- Context: 新项目播种 = 内置默认单例（仅 kb-agent，`src/ib/experts/__init__.py:439-448`），`seed_project`（`src/ibweb/composition.py:1869-1960`）对**每个**专家写同一份 kb 种子提示词（`:1937-1951`）；创建项目仅 admin（`src/ibweb/views.py:1513-1530` 区段，`_seed_created_project` 在 `:1754`）；专家字段 `is_delegating` 在运行期**无任何消费者**（`git grep is_delegating -- src/ib` 仅配置 / Builder / 定义序列化命中）；Builder 评审的三项条款仅当 agent 持有 `is_retrieval` 工具（`needs_scope=True`）时才适用（`src/ib/builder/rubric.py:125-129`，`adapt.py:206-209`，`composition.py:1222`），联网工具 `needs_scope=False`，不处理则顾问**逃过条款评审**；`GROUNDING_CLAUSES` 的 `tool_contract` 关键词为"工具 / 检索 / search_knowledge / 调用"（`builder/types.py:114-118`），不含"联网 / 委托"。
- Options:
  - **(1) 身份标记**——a. 保留名 `advisor` + `is_delegating=True`（零 schema 变更）；b. 新增专家字段 `role`（改定义序列化 / 哈希 / 前端 DTO / 白名单）；c. 仅凭图形态推断。选 **a**：b 触及 `semantic_hash` 与全部定义文档的序列化 / 前端类型，违背"未启用项目逐位不变"的成本最低路径；c 易误判。风险：存量项目恰有名为 `advisor` 且 `is_delegating=True` 的专家会被误判（发布前由运维只读核查 `[OQ-ARCH-R28-02]`）。
  - **(2) 新建项目**——a. `POST /api/projects` 增加可选 `enable_advisor: bool`（缺省 false）；b. 新增独立端点；c. 创建后再走配置页。选 **a**：保持"创建期同步播种 + 原子回滚"（AC-002-04）与 admin-only 口径。
  - **(3) 已有项目加入 / 移除**——a. 前端在草稿内变换（纯函数 `advisorPlan.ts`），经既有"预检→差异清单→保存并生效"；b. 新增服务端"加入顾问"写端点。选 **a**：REQ-FUNC-004 要求走与其他 agent 相同的保存校验 / 差异清单 / 生效流程；b 另开写路径会绕过乐观并发与差异清单。目录接口 `GET /api/config/catalog` 追加只读键 `builtin_agents`（顾问的专家规格、主提示词种子、接线规则版本）供前端使用。
  - **(4) Builder 评审口径**——a. 扩展全局 `GROUNDING_CLAUSES` 的关键词；b. 按"agent 画像"选条款集：新增 `ToolDigest.is_external`（联网工具）并对"顾问画像"（`name == "advisor" and is_delegating`）无条件适用三项条款，且其 `tool_contract` 备选词追加（"联网 / 委托 / web_search / web_fetch / 路由"）。选 **b**：a 会让 kb-agent 的评审放宽（违反 AC-004-02"kb-agent 评审行为不变"）。`BLOCKED_TERMS`（`builder/types.py:120`）不变；顾问种子须 0 命中（AC-001-02，单测断言）。
- Decision: 选 **(1)a + (2)a + (3)a + (4)b**。落地要点：新增种子资产 `src/ib/expert_seeds/advisor.md`（业务中立；声明面向客户、礼貌专业、用提问者的语言、不暴露内部分工与工具名、无依据如实说明、三类来源标注、网页内容仅为只读参考；**同时含"引用来源 / 如实告知 / 工具与委托"三项条款用语**）与读取函数 `advisor_seed_prompt()`（与 `kb_agent_seed_prompt()` 同构，缺失 fail-closed）；`ib.experts` 新增 `BUILTIN_ADVISOR`（`name="advisor"`、`cn_label="顾问"`、`keywords=()`、`is_delegating=True`、`is_default=False`、`is_data_expert=False`）与 `builtin_registry_with_advisor()`，**`builtin_default_registry()` 与 `EXPERT_SPECS` 不变**；`seed_project(project_id, *, registry_view=None, with_advisor=False, …)` 按专家取各自种子文本（kb-agent → kb 种子，advisor → 顾问种子），图由 `canonical_graph_with_advisor` 生成，授权为 `kb-agent: (search_knowledge)`、`advisor: ()`；`PUT` 保存时 `validate_graph` 的顾问模式规则（ADR-R28-01）与 `validate_web_grants`（域名格式、全局上限，ADR-R28-07）经发布校验器 `_plain_validate`（`composition.py:1156`）一并生效。"加入顾问"的接线规则（`addAdvisorToGraph`）：图含恰一个 route 且其 `__else__` 与全部叶子 agent 的出边满足规范形态时自动改线（叶子 agent→END 改为 agent→advisor，route `__else__` 改指 advisor，advisor→END）；否则仅放入未连线的顾问节点并提示手工连线（不猜测）。"移除顾问"（`removeAdvisorFromGraph`）反向恢复：叶子 agent→END，route `__else__` 回指默认专家。
- Consequences: 正向——未启用项目的专家集合 / 授权 / 图 / 种子逐字不变（AC-001-03、AC-003-04）；顾问走与其他 agent 相同的保存、差异清单、版本回滚；kb-agent 评审口径不变。负向——(1) `is_delegating` 被赋予"顾问模式开关"的隐含语义，旧配置页的该复选框（`ConfigPage.vue:852`）对 `advisor` 专家改动会改变运行行为，需在顾问详情面板与代码注释中标明；(2) 全局工具目录新增 `web_search` / `web_fetch`（`known_tool_names()`，`composition.py:1761`），所有项目的配置页可见这两个可授权项（AQ3）；(3) 自动接线只覆盖规范形态，其余需手工连线。

### ADR-R28-06: "平台限制类参数"的表达——LLM 不可见、不可覆盖（REQ-FUNC-016/017/018，AC-014-03）
- Status: Proposed
- Type: decision
- Context: 现有工具参数机制：`derive_tool_param_specs` 由工具 JSON Schema 的 `properties` 派生可配参数（`src/ib/tools/__init__.py:284-317`），配置值以 `functools.partial` 注入为**默认值**，"调用方显式实参优先"（`_wrap_with_params`，`:463-480`）；同一份 `properties` 又被 `_tool_schema` 原样交给 LLM（`src/ib/llm/__init__.py:596-606`）。若超时 / 域名名单 / 上限也这样声明，LLM 既看得见也改得了。
- Options: **A.** `ToolSpec` 追加 `config_parameters`（JSON Schema `properties` 形态）：参与 `derive_tool_param_specs`，**不进入** LLM 可见的 `parameters`；`_wrap_with_params` 对这类参数用"配置胜出"包装（丢弃调用方同名实参、再注入配置值），并据 `timeout_param` 计算 `BoundTool.timeout_s`。**B.** 约定特殊前缀（如 `_cfg_`）隐藏——靠命名约定、易漂移。**C.** 仅在工具内部对 LLM 传入值做钳制——名单类 / 布尔类无法钳制，模型可传空名单绕过。**D.** 把治理放到定义文档的项目级新段——改定义 schema / 哈希，波及所有项目。
- Decision: 选 **A**。对现有工具（`config_parameters=None`）逐位不变；`derive_tool_param_specs` 对 `config_parameters` 额外产出 `ToolParamSpec`（类型 / 默认 / 上下界 / 枚举，限于 `str|int|float|bool`，故域名名单以逗号分隔字符串表示）；配置页的 `AgentDetailPanel.vue` 工具参数区本就按 `tool_param_specs` 自动渲染，无需前端新控件。
- Consequences: 正向——限制类参数结构上不可被模型改动；沿用保存期 `validate_tool_params` 的类型 / 范围校验与现有存储（`tool_grants[].param_values`）。负向——`ToolSpec` / `BoundTool` 两个 dataclass 追加字段（均带默认值，向后兼容）；`str` 型名单需要额外的格式校验器（`validate_web_grants`）。

### ADR-R28-07: 全局联网用量上限的存储与权限（REQ-FUNC-018 (d)，OQ-R28-10=A+C，AC-016-07）
- Status: Proposed
- Type: decision
- Context: 全局上限由 admin 设定，项目管理员只能在其内调低；AC-016-07 要求"非 admin 修改全局上限的请求被服务端拒绝（403）"，即必须存在可被请求的写入口。既有先例：LLM Key 单行表 + `PUT /api/llm-key`（`src/deploy/migrations/006_llm_key.sql`，`CHECK (id = 1)`），迁移须与 `src/ib/ledger/schema.py` 生成器逐字一致（画像 P6）；最新迁移号 008。
- Options: **A.** 新表 `web_governance`（单行，`CHECK (id = 1)`）+ 端口 `WebGovernanceStore` + `GET|PUT /api/web-governance`（`_require_admin`）+ 迁移 `009_web_governance.sql`。**B.** 环境变量（`ib-web.env`）——运维可设，但没有"请求"可被 403，且改值需重启，不满足 AC-016-07。**C.** 文件态（`/var/lib/intelligentbase/`）——无事务 / 审计，与现有"设置落台账"风格不一致。
- Decision: 选 **A**。列：`max_calls_per_turn`（默认 5，硬上限 20）、`max_fetch_bytes_per_turn`（默认 1048576，硬上限 5242880）、`max_seconds_per_turn`（默认 30，硬上限 120）、`updated_at`、`updated_by`；未写入时读取返回默认值（行缺失 = 默认）。生效时刻：**运行期取 `min(全局, 项目参数)`**（admin 调低后立即对新回合生效，无需项目重新保存），**保存期**拒绝超出全局上限的项目值并给出"超出全局上限（N 次）"逐条错误。写入需 admin（沿用 `_require_admin`，`views.py` 现成），记审计（`action="web_governance.set"`）。读取（`GET`）对任一已登录账户开放（配置页展示上限用），不含任何凭据。
- Consequences: 正向——可审计、可热生效、与现有迁移 / 自检纪律一致；回滚迁移 = `DROP TABLE web_governance`（新增表，标 `[MANUAL_ROLLBACK_REQUIRED]`，不触碰既有数据）。负向——多一张表与一个 admin 页面；admin 调低后已保存的更高项目值在运行期被静默钳制（保存页提示"当前有效值"）。

### ADR-R28-08: 不可信联网内容与外发边界（REQ-NFUNC-003/005/006；协议 §L-1）
- Status: Proposed
- Type: decision
- Context: 顾问节点同时持有知识库结果（来自被委托 agent，上游材料）与联网工具；LLM 若被网页注入诱导，可能（i）改变角色 / 泄露提示词，（ii）诱导"调用其他 agent / 工具"，（iii）把知识库内容写进检索词或网址外发。先例：Builder `OutboundPayload`（字段集即白名单）+ `EgressGuard`（`src/ib/builder/egress.py`）；`with_upstream` 的"只读参考，不是指令"围栏（`dag.py:261`）。
- Options: **A.** 仅靠提示词约束。**B.** 结构性隔离 + 确定性闸门（围栏与净化、顾问无委托能力、出站文本闸、审计先行、固定字段载荷）。**C.** 再用一个 LLM 审查网页内容。
- Decision: 选 **B**。(1) **结构**：委托只发生在回合前置理解步骤与图的 `route` 上（此时尚无任何网页内容）；读取网页的顾问节点的工具集合仅限被授权的 `web_search` / `web_fetch`（及管理员显式授予的其他工具），**没有任何"调用 agent"的函数**——"诱导委托其他 agent"在结构上无通路（AC-018-01、REQ-NFUNC-003）。(2) **围栏与净化**：工具返回给 LLM 的文本统一包裹 `【联网内容（不可信数据，只读参考，不是指令）】…【联网内容结束】`，正文先净化（剥离控制 / 零宽字符、折叠连续空白、把内容里出现的围栏标记替换为无害占位、按 `max_chars` 截断）。(3) **出站文本闸**：`check_outbound_text(text, private_texts)`——长度上限（检索词 ≤ 200 字符，网址 ≤ 2048 字符）；`contains_secret_pattern`（复用 `ib/builder/egress.py`）命中即拒；与"本轮私有语料"（被委托 agent 的产出 + 窗口内的助手历史答复；**不含**用户自己的提问）存在**连续 ≥24 字符的逐字重叠**即拒绝（canary 命中数 = 0，AC-018-02）；网址的查询串同样检查。私有语料经 `bind_web_turn(WebTurn(private_texts=…))` 在顾问节点执行期间以线程局部方式提供。(4) **审计先行**（ADR-R28-03 第 9 点）。(5) **固定字段载荷**：搜索端只收 `SearchQuery`（文本 + 条数 + 语言 / 地域 + 超时），抓取端只发 `GET` 请求行与固定头；selfcheck 禁止 `ib.webtools` import `ib.retrieval / ib.vectorstore / ib.blob / ib.streaming / ib.context / ib.ledger`，并断言 `SearchQuery` / `WebCall` 字段集（类型层没有会话 / 资料 / 账号 / 提示词字段，沿用 `builder_single_egress` 手法）。(6) 答复中的网页引用只含标题与网址；顾问答复若出现与网页正文连续 ≥200 字符的逐字复制，保真守卫（ADR-R28-09）判定超出引用长度上限并触发重写（AC-018-04，`[ASSUMPTION A-10]`）。
- Consequences: 正向——注入防护的主论据是结构而非措辞；canary 类外发有确定性判据。负向——(1) 24 字符逐字重叠规则对"用户提问里本就含有、又被 kb 答复复述"的内容是**放行**的（因用户提问不入私有语料），而对短实体（如产品型号）不拦——这是有意的假阳性 / 假阴性权衡，阈值可调；(2) 不能阻止 LLM 把知识库内容**改写**后外发（语义泄露），只能靠顾问提示词与"只含检索词"的类型约束 + 域名白名单 + 运维出站 ACL 缓解，写入残余风险；(3) 线程局部私有语料依赖"工具循环与顾问节点同线程"，由单测断言。

### ADR-R28-09: 顾问汇总的事实保真守卫（AC-006-06 / AC-010-03；REQ-FUNC-012）
- Status: Proposed（1.1.0 改写 Decision / Consequences：用户裁决 AQ1=B；2.1.0 见 **ADR-R28-09-R1**：保真核对范围订正，以 R1 为准）
- Type: decision
- Context: 顾问是 LLM 节点，需统一措辞与格式但"不得增删或改变事实、数字、引用"；仅靠提示词无法保证。ADR-R28-01 使顾问成为唯一叶子，故其输出即最终答复。
- Options: **A.** 仅提示词约束。**B.（已否决，用户裁决 AQ1=B；原推荐项）** 确定性后验 → 最多重试 1 次 → 仍不合格或汇总失败则回退为被委托 agent 的原答（经标签清洗）：优——不丢已检索信息；缺——失败路径暴露 agent 原答，"答复只来自顾问"在该路径不成立，内部分工可能外露。**C.** 单来源时跳过顾问（直通）——违背 REQ-FUNC-012"单一来源也统一措辞"。**D.** 非 LLM 的模板化格式化——无法"整理措辞"。**E.** 确定性后验 → 最多重试 1 次 → 仍不合格或汇总步骤自身失败，则由顾问节点返回**统一致歉文本**，不展示被委托 agent 原答。优——失败路径同样只有顾问一个出口，不泄露内部分工；文案确定性可测。缺——失败时有用信息对提问者不可见。
- Decision: 选 **E**（REQ-FUNC-012 (e)、REQ-NFUNC-011；AC-006-07、AC-010-06/07）。
  1. **保真判据不变**：`check_fidelity(upstream_texts, final_text) -> tuple[str, ...]`（纯函数）从被委托产出与联网结果中抽取"保护片段"：数字串（含小数 / 千分位 / 百分号）、书名号 `《…》` 内的文件名、形如 `第N条/页/节` 的位置、`https?://` 网址；逐一在最终文本（做空白 / 全半角归一）中查找，返回缺失项。有缺失（或 `exceeds_quote_limit(web_texts, final_text, 200)`）⇒ 以"以下信息必须原样保留：…"为追加指令重试顾问**一次**；**首次不通过、第二次通过 ⇒ 返回顾问汇总后的正常答复，不出现致歉文案**（AC-010-07 后半）。
  2. **触发致歉的两条路径**：(i) 顾问节点自身失败——LLM 不可用 / 超时 / 异常导致 `_run_agent` 结果降级（AC-006-07、AC-010-06）；(ii) 保真或引用上限核对第二次仍不通过（AC-010-07 前半）。两条路径产出**同一**文本，不区分对用户可见的措辞。
  3. **致歉文案常量与位置**：`ADVISOR_APOLOGY_TEXT: Final[str]`，定义于 `src/ib/advisor/compose.py`（MOD-R28-10，IFC-R28-015），经 `advisor_apology_text()` 读取。文案要求：礼貌专业、含"抱歉"、含下一步建议（"稍后再试"或"换个问法"之一）、**不含**任何 agent 名 / 专家中文标签 / 工具名 / 路由相关词 / 异常信息 / 状态码 / 数字。示例（定稿由实现按此约束落笔）："非常抱歉，这个问题我暂时没能为您整理出可靠的答复。请您稍后再试，或换个问法再告诉我，也可以补充更多细节，我会尽力帮您。"
  4. **是否可配置——决定：不可配置（平台常量）**。理由：(a) 配置内容无法在运行期证明不含内部名称（专家名、工具名、路由词随项目变化，且配置会进入定义文档 / 差异清单 / 审计，形成新的泄露面）；(b) 可配置须新增定义 schema 字段或设置表，违背 REQ-NFUNC-001 "未启用项目逐位不变"与 AQ5 "零 schema 变更"；(c) 备选"可配置 + 黑名单校验"的校验对象（项目内专家 / 工具名）本身随编辑变化，校验不完备。代价：改文案需发版（可接受）。
  5. **失败路径的结构实现**：顾问节点在上述两条路径下**不返回降级结果**，而返回 `ExpertResult(expert="advisor", content=ADVISOR_APOLOGY_TEXT, degraded=False, degrade_reason=None)` 并把同文写入 `outputs["advisor"]`。因此：被委托 agent 因"有成功产出的后代（顾问）"而不是叶子（`_collect` 叶子判定不改，`dag.py:394-398`）；叶子集合 = {顾问}，`_collect` 的"默认专家直答"安全网（`dag.py:399-407`，会暴露 kb 原答）在顾问模式下不会被触发；`_aggregate` 单叶子直通，仅做确定性标签清洗（顾问标签已从清洗集剔除，致歉常量另被单测断言不含任何内置专家标签）。顾问模式下 `run_dag` 之外的未预期异常（`Orchestrator._run_dag_turn`）同样落到该文本，异常信息只写日志、不进响应 `[ASSUMPTION A-12]`。
  6. **对用户可见的形状**：HTTP 状态非 5xx（沿用正常答复的状态码与流式事件序列，仅 `content` 为致歉文案）；**不新增 `degrade_reason` 取值**（M-SA-005）；致歉文本照常作为本回合助手答复写入会话历史。
  7. **可观测**：回合日志 `advisor_turn` 追加 `apology: Literal["summary_failed","fidelity_failed",""]`（原 `advisor_fidelity_fallback` 事件改名为 `advisor_apology`，计数用于评估误报率，见 R-7）；异常类型名只入日志，不含查询原文、答复片段与凭据。
  同函数族提供 `exceeds_quote_limit`、`retry_instruction`。
- Consequences: 正向——(1) 失败路径与成功路径一样"提问者看到的答复只来自顾问"，内部分工（agent / 工具 / 路由名）与错误细节结构性不外露（AC-006-07、AC-010-06 的出现次数 = 0 可确定性断言）；(2) "数字与引用不被改写"成为可测的确定性判据（AC-006-06）；(3) 失败不静默、不 5xx，并给出下一步建议。负向——(1) **用户否决了推荐项 A 的代价**：失败时已检索到的有用信息（含引用来源）对提问者不可见，提问者须重试；(2) 抽取为正则启发式，会把"7 天 → 一周"这类语义等价改写判为缺失（按需求本意视为违规），**误报现在直接变成用户可见的致歉**，R-7 因此升级；(3) 重试增加一次 LLM 调用；(4) 文案为平台常量、不可配置，改文案需发版；致歉文案为中文单一文本，不随提问者语言变化 `[ASSUMPTION A-12b]`。

### ADR-R28-10: 部署形态与依赖约束（C-R28-03 / C-R28-09；画像 P6 / P7 / P8）
- Status: Accepted（沿用既有约束，无新选择）
- Type: constraint-driven
- Context / 约束来源: 画像 P7（v1 固定四个 systemd 单元，新增须回架构评审；物理机直部署；改什么重启什么）、P8（禁 Docker、禁 langchain-openai ≥0.3、torch 类不进基座清单、`ib.*` 不得 import `ib_embed`、禁用 Channels / Redis 实时推送、nginx SSE 条件不可破坏）、P6（依赖上下界都写、手写 scoped SQL 迁移与 `schema.py` 单源、离线测试纪律、仓库 PUBLIC）、C-R28-03/04/09。
- 被排除的替代方案及原因: 独立抓取代理 / 元搜索服务单元（新单元，P7）；`langchain-community`（重依赖 + 无 SSRF 钉 IP 能力；主会话建议不引入，用户原则为「尽量复用，不要重复造轮子」）；`trafilatura` / `readability-lxml`（新增传递依赖，超出"尽量复用"）；Redis 做会话 / 预算存储（P8 禁用）——会话与预算均进程内；Docker 化搜索网关（P8）。
- Decision: `ib.webtools` 与 `ib.advisor` 作为 `ib-web` 进程内的库包实现；预算 / 会话沿用进程内；新增依赖仅 `lxml`（显式声明既有间接依赖）；`ib.advisor` / `ib.webtools` 不得 import `ib_embed`；nginx 配置不改（现有 `proxy_read_timeout 300s` 覆盖更长的顾问回合；顾问回合延迟 `[TBD-R28-1]` 目标机实测）。
- Consequences: 正向——运维面不变（仍四单元），回滚 = `git revert` 后重新部署；负向——联网占用 ib-web 线程，容量靠并发闸与单轮时长上限控制（ADR-R28-03）。

### ADR-R28-11: DeepSeek 搜索适配器、凭据复用与错误 / 重试 / 超时策略（REQ-FUNC-016 / 018 / 019，REQ-NFUNC-005 / 006 / 007 / 011；OQ-R28-15）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-016 (a)~(d)（结果含标题 / 网址 / 摘要；检索词 1–128 字符、条数 1–50；空结果如实；401 / 402 / 429 / 408 / 500 / 504 降级且不暴露状态码）、REQ-FUNC-018 备注（按次计费 + 账户级 QPS）、REQ-NFUNC-005（外发仅检索词）、REQ-NFUNC-006（复用现有密钥，不新增凭据）、REQ-NFUNC-007（超时由平台强制）、REQ-NFUNC-011、C-R28-02（自动化只用替身）、C-R28-10、D-07。**P11 事实**：POST `https://api.deepseek.com/v1/tools/search`，头 `Authorization: Bearer <Key>`、`Content-Type: application/json` `[P11: docs/external_api/deepseek_search_fetch.md:§端点与鉴权]`；请求字段 `query`（1–128 Unicode 字符、不能全空白）、`count`（1–50，缺省 10）、`ori_question`、`localization`（**IP 地址**）、`need_content`（缺省 false，false 时 `content` 恒空）`[P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]`；响应 200 `{"results":[…]}`，空结果 = 空数组，条目含 `title`、`url`、`snippet`（约 100–200 字）、`summary`（约 600–800 字，供模型使用）、`content`、`site_name`、`date`、`rerank_score`、`authority` 等 `[P11: docs/external_api/deepseek_search_fetch.md:§Search 响应]`；错误码 400 / 401 / 402 / 403 / 404 / 408 / 413 / 429 / 500 / 504 及是否重试 `[P11: docs/external_api/deepseek_search_fetch.md:§错误]`；Search QPS 100（账户级）、仅"200 且有结果"计费、失败 / 空结果 / 超时不计费、**未给超时数值** `[P11: docs/external_api/deepseek_search_fetch.md:§限流与计费]`。**现有代码事实**：LLM Key 的装配期读取为唯一读点——`LlmKeyStore.get()` 取 DB 单行（`src/ibweb/composition.py:817-822`），`build_llm_provider` 在其为空时回退读 `cfg.llm.api_key_env`（`IB_LLM_API_KEY`，`src/ib/llm/__init__.py:461-466`）；管理页 `PUT /api/llm-key` 的生效语义 = 保存 + 重启重装配（`src/ibweb/views.py` `llm_key_endpoint` 文档串）；LLM 缺省 `base_url = https://api.deepseek.com/v1`（`src/ib/config/__init__.py:341`）；HTTP 出站风格 = stdlib `urllib`（`src/ib/embedding/__init__.py:259-312`）；`ConfigError(key=…)` 只报键名（`src/ib/config/__init__.py:879-935`）。
- Options:
  - **D1 HTTP 客户端**：**A. stdlib `urllib.request` 适配器 + 可注入的 `HttpPostTransport` 缝（选）**——优：与 `LocalHttpEmbedder` 同风格、零新依赖（用户裁决）、离线可测（替身实现同一缝）；缺：自写状态码映射与读取上限。B. `requests` / `httpx`——缺：新增依赖或依赖传递依赖的内部细节（违背用户"不引入新 HTTP 依赖"）。C. `langchain-community` 搜索工具——已被 ADR-R28-03 / 04 排除（重依赖、无法对接本项目的预算 / 审计 / 替身缝）。
  - **D2 凭据来源**：**A. 与 LLM 同一解析点（选）**——抽出 `resolve_llm_api_key(cfg, db_key)`（DB 优先 → 兼容回退 `IB_LLM_API_KEY`），`build_llm_provider` 与联网运行时共用，装配期解析一次、构造器注入。B. 每次调用读 `LlmKeyStore.get()`——能让搜索在轮换后立即换新，但破坏"装配期唯一读点"纪律（C-IB-42，`ports.py` LlmKeyStore 文档串），且与 LLM 轮换生效时刻不一致。C. 保留独立 `IB_WEB_SEARCH_API_KEY`——两份密钥，违反 REQ-NFUNC-006 与用户"复用现有 Key"。
  - **D3 失败重试**（OQ-R28-15(b)）：**A. 不重试，每次尝试都计入本轮上限（选）**。B. 对 408 / 429 / 500 / 504 各重试一次（带退避，计入上限）。C. 无界重试。
  - **D4 端点**：**A. 常量（选）**——`https://api.deepseek.com/v1/tools/search` 写入适配器常量。B. 保留 `IB_WEB_SEARCH_BASE_URL`。
- Decision: 选 **D1=A、D2=A、D3=A、D4=A**，要点如下（接口见 module_design IFC-R28-029 ~ 031）。
  1. **请求载荷最小化**：只发 `query`、`count`（= `SearchQuery.max_results`，上限 50）与显式 `need_content=false`；**绝不发送** `ori_question`（会把提问者原话外发，超出 REQ-NFUNC-005"仅检索词"）、`localization`（资料定义为 IP 地址，等于外发终端地址；也无法由本项目的 `region` 配置映射）。`SearchQuery` 字段集不变（`text`、`max_results`、`lang`、`region`、`timeout_s`），selfcheck 断言继续有效。
  2. **检索词边界**：`SearchQuery.text` 上限由 200 收紧为 **128 个 Unicode 字符**（`len(str)` 口径）；工具层先去首尾空白——空 / 全空白 ⇒ 不出站、返回明确原因；超过 128 ⇒ **截断到 128**（不拒绝，AC-014-09），再过出站文本闸。`count` 范围 1–50；配置页"返回条数上限"保存期拒绝超出 1–50（AC-014-09）。`lang` 以资料所载的 `lang:` 操作符追加到检索词（`lang:zh,en` 形态）`[P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]`，追加后总长仍 ≤128（先截基础检索词）；格式严格校验（保存期 + 运行期），避免经 `lang` 注入 `site:` 等操作符 `[ASSUMPTION A-16]`。**`region` 不被 DeepSeek 使用**（资料只有 IP 型 `localization`），保留配置字段但适配器忽略，见 AQ6。
  3. **结果映射**：`SearchHit.title ← title`、`url ← url`、`snippet ← summary`（非空时，面向模型的长摘要）否则 `snippet`；缺 `url`、非 http(s) 的条目丢弃；条目全被丢弃而原数组非空 ⇒ `bad_response`；空数组 ⇒ `SearchOutcome(hits=(), error=None)`（**空结果不是故障**，M-SA-005；工具文案"联网检索未找到相关结果"，AC-014-10）。保持提供方返回顺序，不用 `rerank_score` / `authority` 过滤（资料只给了"≥1.5 高质量""≥3 高权威"的解读，未规定丢弃阈值）。工具层摘要截断由 400 提到 800 字符以容纳 `summary` `[ASSUMPTION A-13]`。
  4. **错误映射（只按 HTTP 状态码，不读错误体）**：401 → `auth_failed`；402 → `quota_exceeded`；429 → `rate_limited`；408 / 504 → `timeout`；500 及其他 5xx → `unreachable`；400 / 413 / 其他 4xx（含 Search 资料未列的 403 / 404）→ `rejected`；3xx（**不跟随重定向**，避免把 `Authorization` 带给第三方）/ 200 但 JSON 非法或缺 `results` 数组 → `bad_response`；套接字超时 → `timeout`；DNS / 连接 / TLS 失败 → `unreachable`。适配器**永不读取、记录或回显错误体**（`error.message` 等字段取值资料只给了格式，未给穷举；映射只依赖资料明确列出的状态码）`[P11: docs/external_api/deepseek_search_fetch.md:§错误]`。对用户：工具只返回固定短语（"联网服务未配置"/"联网检索超时"/"联网检索失败"…），状态码数字、错误原文、密钥片段不出现（REQ-NFUNC-011，AC-014-08）；内部日志 / `TurnBudget.events` 只记枚举类别 + 耗时。
  5. **超时**：资料未给超时数值，**由平台强制**——`SearchQuery.timeout_s`（配置，缺省 10 秒，REQ-NFUNC-007）作为总期限，传输层每次套接字操作取 `min(剩余, 总期限)` 并在分块读取时检查期限；外层仍有 `_execute_tool` 看门狗（`timeout_s + 1`，ADR-R28-03 第 3 点）。响应体读取上限 2 MiB（超限 ⇒ `bad_response`；50 条 × 约 1 KB 级摘要远低于此 `[ASSUMPTION A-14]`）。
  6. **重试（D3=A）**：资料写明 408 / 429 / 500 / 504 "等待后重试"，但**未给间隔与次数**，也无超时数值。保守缺省：**适配器内不重试**；任何一次尝试（含 429）已在发出前 `reserve_call`，**计入本轮调用上限**（AC-016-09 下限）；是否由模型在同一轮再次调用由顾问提示词与上限共同约束。理由：(i) 搜索占用 ib-web 请求线程（8 线程，ADR-R28-03），重试会放大最坏占用；(ii) 429 即时重试加重限流；(iii) 失败 / 空结果 / 超时不计费，不重试不增加费用。402 按资料"充值后再重试"，本就不重试。`[ASSUMPTION A-15]`，OQ-R28-15(b) 作为"本轮采用保守缺省、目标机观察后再定"回写。
  7. **凭据（D2=A）**：Key 在装配期经 `resolve_llm_api_key` 解析**一次**，只传入 `DeepSeekSearchProvider` 构造器；该对象的 `__repr__` / 异常 / 日志 / `health().detail` / `describe_egress()` 均不含 Key；`Authorization` 头只在传输层请求构造处出现。Key 为空（含"LLM 未配置"首启态，ADR-39）⇒ 工厂返回 `NullSearchProvider` 并记 WARNING，联网按"未配置"降级，其余功能不受影响（AC-018-05 后半）。**目的地绑定**：端点是常量，不可由环境键改写，Key 因此只会发往 `api.deepseek.com`；并要求 `cfg.llm.base_url` 的主机为 `api.deepseek.com`，否则启动失败（只报键名 `IB_WEB_SEARCH_PROVIDER`）——防止"LLM 用的是另一家 OpenAI 兼容服务，却把那家的 Key 发给 DeepSeek"`[ASSUMPTION A-17]`。
  8. **Key 轮换（"同步生效"的解释）**：LLM 与搜索都在装配期取 Key，管理页轮换后**重启 ib-web** 两者同时换新——这是现有 LLM 的生效语义（不是本设计新增的限制）；不为搜索单独做热读（D2=B 的不一致与读点膨胀）。若需不重启生效，应对 LLM 与搜索一起改（超出本轮），见 AQ7。
  9. **废弃键**：`IB_WEB_SEARCH_API_KEY`、`IB_WEB_SEARCH_BASE_URL` 删除（`GlobalConfig.web_search_base_url`、`composition.py` 读取点、`env.example` 占位、`config/__init__.py` 键登记同步删除）；`IB_WEB_SEARCH_PROVIDER` 取值域 `none`（缺省）\|`deepseek`，`fake` 仅离线（ADR-R28-13）。
  10. **外发声明**：`DeepSeekSearchProvider.describe_egress()` = `EgressDescriptor(remote=True, endpoint_host="api.deepseek.com", data_categories=["web_search_query"])`，与 LLM 的外发条目**同一服务方、独立条目**（AC-018-03）；`/healthz/deps` 的 `egress_web` 与启动日志 `startup.web_egress` 沿用，形状不变。**仍禁止外发**：知识库片段、台账内容、其他项目数据、其他用户会话、提示词原文、凭据——由固定字段载荷（`SearchQuery`）+ 出站文本闸 + 审计先行保证（ADR-R28-08）。
  11. **健康探测**：`health()` 不主动调用 DeepSeek（资料无免费探测接口，且每次成功调用计费 `[P11: docs/external_api/deepseek_search_fetch.md:§限流与计费]`），仅报告"已配置"。
  12. **离线替身**：见 module_design IFC-R28-030（`FakeDeepSeekTransport`，按资料字段与错误码构造响应）。`DeepSeekSearchProvider` 构造器**必须显式传入** `transport`，无默认真实传输——测试若忘记注入会立即报错而不是触网；真实传输 `UrllibPostTransport` 仅由 `build_search_provider` 在非离线分支构造。
- Consequences: 正向——(1) 复用密钥，新增凭据数 = 0，Key 只会发往固定主机；(2) 请求载荷与资料字段一一对应、可由替身逐项断言，自动化测试不触真实端点；(3) 失败映射只依赖资料明确列出的状态码；(4) 外发类别收敛为"检索词"。负向——(1) 不重试意味着 429 / 5xx 时当轮直接降级（可接受：降级是产品内既有路径）；(2) 搜索在非 DeepSeek 的 LLM 配置下不可用（启动失败，需运维改键）；(3) `region` 偏好无法兑现，需 AQ6 裁决；(4) 资料由主会话整理、未核对原页面，字段若与实际有出入，在目标机人工验证时才会暴露（AC-014-06 的人工清单）；(5) 轮换 Key 需重启才对搜索生效。

### ADR-R28-12: 网页抓取方案——DeepSeek Fetch API / 保留本地 SafeFetcher / 混合（REQ-FUNC-017 / 018，REQ-NFUNC-004 / 005 / 007，OQ-R28-15(c)）
- Status: Proposed
- Type: decision
- Context: 用户裁决要求本 ADR 在方案一（改用 DeepSeek Fetch）与方案二（保留本地抓取）之间选择，可选混合。硬约束：总开关 `IB_WEB_FETCH_ENABLED` 缺省关闭；本机内网地址防护 netguard 保留；若用 DeepSeek Fetch，发出前仍须拒绝内网 / 私有 / 本机 / 元数据地址、非 http(s)、含用户名口令的网址，并保留域名名单与用量上限（REQ-NFUNC-004"被拒网址不得发往任何外部服务"）。**P11 事实**：Fetch = POST `https://api.deepseek.com/v1/tools/fetch`，请求仅 `url`（≤8192 字符、带主机名的 http / https、不含用户名密码）；响应仅 `title`（取不到为空串）与 `content`（Markdown）；**响应不含最终网址**；403 = 被安全策略拒绝，404 = 没拿到可用内容（URL 不可用、被站点策略屏蔽、目标站出错、内容类型不支持、提取不出 Markdown 五类合一）；429 含账户 QPS（25）与**单域名限制（数值未给）**；每 1000 次成功请求 0.75 美元；**未给超时数值**；**未写明重定向、内网地址的处置**，也**没有响应大小上限参数** `[P11: docs/external_api/deepseek_search_fetch.md:§Fetch 请求与响应、§错误、§限流与计费]`。现状：本地抓取已有 `SafeFetcher`（钉 IP + 逐跳重校验 + 限时限量 + `lxml` 抽取，`src/ib/webtools/fetch.py`）与 `UrlGuard`（`netguard.py`）。
- Options:
  - **方案一：改用 DeepSeek Fetch（服务端抓取，输出 Markdown）**。优：本机不再连接任意公网主机，出站 ACL 可收窄为仅 `api.deepseek.com:443`；本机 SSRF 的"连接面"消失；`lxml` 抽取代码与 `fetch.py` 的传输层可删。缺：(a) **响应无最终网址**，与 REQ-FUNC-017"返回正文（含标题与最终网址）"、AC-015-01 冲突，要么改需求、要么谎称"最终网址 = 请求网址"；(b) 重定向 / 内网处置 `[UNSOURCED]`，REQ-NFUNC-004 的"302 重定向到私有地址被拒"类用例（N≥30）无法由本项目验证，只能验证"发出前预检"；(c) 域名名单只能检查**初始网址**，服务端跟随的重定向跳不受控，REQ-FUNC-018 (a) 弱化；(d) 404 把五类失败合一，AC-015-04"内容类型不支持 / 内容超限"无法区分（AC-015-07 的"被拒 / 无内容"可区分）；(e) **待抓取网址发往 DeepSeek**（新增外发类别，网址可能带查询串中的令牌、或为用户私有链接）；(f) 按次计费 + 账户 QPS 25 + 单域名限流（数值未知）使 429 概率上升；(g) 没有响应大小参数，"抓取总字节上限"只能在已收到后截断；(h) 新增一套适配器、替身与 AC 重写；Markdown 质量无样本。
  - **方案二：保留本地抓取（`SafeFetcher` + `UrlGuard` + `lxml`）**。优：REQ-FUNC-017 / 018 / NFUNC-004 / 007 逐条已有实现与可测性（钉 IP、每跳重校验域名名单与地址、期限与字节上限、细分失败原因、最终网址）；待抓取网址只发往目标站，**不发往 DeepSeek**，发往 DeepSeek 的外发类别只有"检索词"；零计费、无单域名限流；不新增代码。缺：ib-web 需出站公网 80/443（第二道防线依赖运维 ACL，OQ-ARCH-R28-04）；SSRF 防护是自写连接层，需持续维护（已有 ≥30 条拒绝用例）；`lxml` 保留为显式依赖（C 扩展解析不可信 HTML，已有缓解）。
  - **方案三：混合（`IB_WEB_FETCH_BACKEND = local\|deepseek` 可配置）**。优：运维可按环境取舍。缺：两条代码路径与两套替身、AC 矩阵翻倍；deepseek 分支仍带有方案一的 (a)(b)(c)(d)(g) 缺陷；新增配置键与 `PageFetcher` 端口，范围超出本轮。
- Decision: 选 **方案二：保留本地抓取**。理由（引 REQ）：(1) REQ-FUNC-017 要求返回"最终网址"，Fetch 响应没有该字段 `[P11: docs/external_api/deepseek_search_fetch.md:§Fetch 请求与响应]`——选方案一等于改需求；(2) REQ-NFUNC-004 的验收要求"重定向到私有地址被放行次数 = 0"，该行为在方案一中发生在 DeepSeek 一侧且资料未写 `[UNSOURCED]`，无法验证；(3) REQ-FUNC-018 (a) 名单需逐跳生效；(4) REQ-NFUNC-005 把外发收敛到最小，方案二使待抓取网址不离开"本机 → 目标站"这一条边；(5) 资料的三处空白（超时、单域名 QPS、重定向 / 内网处置）都落在抓取安全结论上，不能以"保守缺省"代替证据；(6) 方案二已实现并有拒绝用例，成本最低。**硬约束全部保留**：`IB_WEB_FETCH_ENABLED` 缺省 0、关闭时出站 0 且不审计（ADR-R28-03 第 11 点）、`UrlGuard` 地址拒绝网段与钉 IP 连接、域名黑白名单、每轮次数 / 字节 / 时长上限均不变。**改变点**：无（本 ADR 不改 `fetch.py` / `netguard.py` 的契约）。**`lxml`**：保留显式声明 `lxml>=5.0,<7.0`（`requirements.txt`、`requirements-offline.txt` 不变）；若将来改用方案一，`python-docx` 仍间接需要 `lxml`，届时应只删除显式行及 `extract_text`，不应从 venv 卸载。**重新评估触发条件**（登记为 ADR-R28-12-R1 的前置）：(i) 目标机人工验证后运维明确不接受"ib-web 出站任意公网 80/443"；或 (ii) 资料补全重定向 / 内网处置、超时与单域名 QPS，且需求接受 Fetch 响应不含最终网址。届时优先走方案三的"端口 + 第二实现"形态，而非整体替换。
- Consequences: 正向——需求与验收口径无变化；发往 DeepSeek 的外发类别仍只有"检索词"；抓取细分失败原因保留；无新依赖、无新计费。负向——(1) 出站 ACL 需放行公网 80/443（仅在总开关开启时需要，缺省关闭）；(2) 自写连接层的维护成本与攻击面留在本项目（R-3 继续有效）；(3) `lxml` 的 C 扩展解析面继续存在（R-9 继续有效）；(4) 放弃 Fetch 的服务端 Markdown 抽取质量（无样本，不能比较）。

### ADR-R28-13: 搜索提供方替身的生产禁用——启动失败还是提供方不可用（REQ-FUNC-019 / US-020，Q3=A）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-019：替身（fake）只允许在离线 / 测试模式使用；非离线配置为替身必须被拒绝——"启动失败，或该提供方不可用，二者由架构择一"；错误只报配置键名；不得静默回退为假数据；被拒期间联网按"未配置"处理。现有先例：离线模式用 `_offline_view` 整体切到替身列（`src/ibweb/composition.py:1378` `_offline_view`）；`build_llm_provider` 在离线模式下后端非 fake 即 `StartupError`（`src/ib/llm/__init__.py:449-454`）；非法枚举值在 `validate_required` 中以 `ConfigError(key=…)` 启动失败（`src/ib/config/__init__.py:908-935`，离线模式在 `:879` 处提前返回）；`ConfigError` 只带键名（`config_error_reports_key_only`）。现状代码里 `build_search_provider` 对 `fake` 一律返回替身（`src/ib/webtools/search.py:127-142`），即**非离线也会加载**。
- Options:
  - **A. 启动失败**：`validate_required` 在非离线分支把 `IB_WEB_SEARCH_PROVIDER` 的值域定为 `{none, deepseek}`（`fake` 不在其中）⇒ `ConfigError(key="IB_WEB_SEARCH_PROVIDER")`；`build_search_provider(…, offline=…)` 在 `offline=False` 且 `fake` 时同样抛 `ConfigError`（纵深防御）。优：与既有"非法枚举值 fail-fast"一致；运维在重启时立即看到、不会出现"看似联网实为假数据"；错误信息只含键名与允许值，不含所配值；无需新增降级状态。缺：一个可选功能的误配会让 ib-web 起不来（影响面大于该功能）。
  - **B. 提供方不可用**：校验放行，工厂把 `fake` 在非离线时换成 `NullSearchProvider` 并记 WARNING，联网按"未配置"。优：其余功能不受影响。缺：误配只体现在日志 WARNING 与用户侧"联网服务未配置"，运维易忽略；要另设状态（catalog / healthz）才可见。
  - **C. 首次调用时拒绝**：缺：延迟暴露、测试面更大，否决。
- Decision: 选 **A（启动失败）**。理由：(1) REQ-FUNC-019 的目的是杜绝线上事故，最响亮的信号最安全；(2) 本项目对"非法枚举值"已是 fail-fast（同一函数、同一错误类型），B 会为一个键开出第二种失败语义；(3) 这是**可选**键，缺省 `none`，误配只可能发生在运维显式编辑 `ib-web.env` 之后，爆炸半径由"编辑者本人在重启时看到错误"限定；(4) M-SA-011：把"不允许的开关"做成装配期的类型 / 校验事实，而不是运行期约定。实现要点：① `validate_required` 非离线分支校验值域；同一处校验"`deepseek` ⇒ `cfg.llm.base_url` 主机为 `api.deepseek.com`"（ADR-R28-11 第 7 点），均 `key="IB_WEB_SEARCH_PROVIDER"`；② `build_search_provider(settings, api_key, *, offline: bool, transport=None)`：`fake` 且 `not offline` ⇒ `ConfigError`；`offline` 且 `deepseek` ⇒ 返回 `FakeSearchProvider`（离线永不触网，对齐 `build_llm_provider` 的离线纪律）；③ `_offline_view` 把 `web_search_provider` 在离线时由非 `none` 统一置 `fake`（与 embedding / llm 的整体替身列一致），`none` 保持 `none`；④ `selfcheck` 增用例 `search_fake_rejected_in_production`（非离线 + fake ⇒ `ConfigError` 且 `str(exc)` 不含所配值；离线 + fake 可用；`FakeSearchProvider` 被调用次数 = 0）。
- Consequences: 正向——生产不可能加载替身（AC-020-01 / 03），错误不含配置值；离线测试路径零改动。负向——误配导致 ib-web 启动失败（可由运维当场修正；若要降为"不可用"需改本 ADR）；`_offline_view` 多一个字段切换；AC-020-02（"提供方不可用"形态）因选 A 不适用，在 AC 承接表中标"不适用（选 A）"。

## ADR 修订（2.1.0；R1 订正）

### ADR-R28-04-R1（2.1.0 修订；取代 ADR-R28-04 Decision (1)(2) 与 Consequences 负向 (1)，**结论以 R1 为准**）
- Status: Proposed（修订）
- Type: decision（沿用 ADR-R28-04 的选择，仅更新"厂商"事实）
- Context: 用户裁决 CP-003「Q7 纳入」（D-07）：本轮搜索提供方 = DeepSeek 官方 Search API；画像 1.1.0 已补 P11-3。原 ADR-R28-04 因厂商未定、无 P11 而决定"只做端口 + Null + Fake + 注册表，不实现厂商适配器、`search.py` 不含网络代码、密钥经 `IB_WEB_SEARCH_API_KEY`、地址经 `IB_WEB_SEARCH_BASE_URL`"。
- Options: 搜索适配方式 A（项目自有端口 + 生产适配器 + 内存替身）仍是选中项，B/C/D 的排除理由不变（见 ADR-R28-04）；本修订不重新论证。
- Decision: (1) **端口、`NullSearchProvider`、`FakeSearchProvider`、注册表保持**（`SearchProvider` 方法集不变，M-SA-001）；(2) 生产适配器 = `DeepSeekSearchProvider`，决策与细节见 **ADR-R28-11**；(3) 原 (1) 中"本轮不实现任何厂商适配器、`search.py` 无网络代码"作废；网络代码落在新文件 `deepseek.py`（`search.py` 仍不含网络导入）；(4) 原 (2) 的 `IB_WEB_SEARCH_API_KEY` 与 `IB_WEB_SEARCH_BASE_URL` **废弃并删除**（ADR-R28-11 D2 / D4）；(5) 原 (3) 的抽取方案 E（`lxml.html`）由 **ADR-R28-12** 再次确认保留；(6) 原 Q7=C 行（"移到下一轮"）作废，见"开放问题"表。
- Consequences: 正向——更换提供方仍只新增"映射类 + 一次登记"，顾问与工具形态不变（AC-014-05）；负向——原负向 (1)"真实联网效果无法本轮验收"改为：**自动化验收只用离线替身（AC-014-06），真实端点效果为目标机人工验证项**；`selfcheck` 用例 `web_egress_single_exit` 的"search.py 不得含网络导入"断言需改为"网络导入仅限 `fetch.py` / `deepseek.py`"。

### ADR-R28-03-R1（订正 ADR-R28-03 第 3、6、10、11 点；**结论以 R1 为准**）
- Status: Proposed（修订）　Type: decision（沿用）
- Context: DeepSeek 接入（D-07）使以下条款的事实改变；其余条款（SSRF、名单、并发闸、审计先行、默认关闭）不变。
- Decision: (1) 第 3 点"执行超时"：搜索的期限由平台强制（资料无超时数值），见 ADR-R28-11 第 5 点；(2) 第 6 点"用量上限"：**每一次发出前的尝试（含后来返回 429 / 5xx 的）都计入本轮调用数**，不做适配器内重试（AC-016-09）；(3) 第 10 点"外发声明"：搜索条目 = `(remote=True, endpoint_host="api.deepseek.com", data_categories=["web_search_query"])`；抓取条目仍为 `("*", ["web_fetch_url"])`，其含义是"目标站"，**不是** DeepSeek（ADR-R28-12）；`EgressDescriptor` 字段不变；(4) 第 11 点"默认关闭"：`IB_WEB_SEARCH_PROVIDER` 缺省 `none`，取值域 `none\|deepseek`（`fake` 仅离线，ADR-R28-13）；`IB_WEB_FETCH_ENABLED` 缺省 `0` 不变。
- Consequences: 与 ADR-R28-03 相同，另增：搜索相关故障统一落到 `SearchErrorKind` 枚举，不新增 `WebBlockKind`。

### ADR-R28-08-R1（订正 ADR-R28-08 第 3、5 点）
- Status: Proposed（修订）　Type: decision（沿用）
- Decision: (1) 出站文本闸的检索词长度上限由 200 收紧为 **128**（与提供方上限一致，`check_outbound_text(kind="query")`）；工具层先截断到 128 再过闸，故超长检索词不再触发 `outbound_rejected`；(2) 固定字段载荷再收紧：`SearchQuery` 之外，适配器的请求体字段集合固定为 `{query, count, need_content}`，由替身逐请求断言（AC-018-06）；`ori_question` 与 `localization` 在类型层没有来源字段；(3) canary 判据不变：出站内容类别仅"检索词"（发往 DeepSeek）与"待抓取网址"（发往目标站），其他目的地数 = 0。
- Consequences: 128 字符限制使较长的检索词被截断，可能降低检索精度（可接受；截断发生在基础检索词，`lang:` 操作符保留）。

### ADR-R28-09-R1（订正 ADR-R28-09 Decision 1；Q1=A、Q4=A）
- Status: Proposed（修订）　Type: decision（沿用选项 E）
- Context: 用户 CP-003 Q1=A（REQ-FUNC-012 (e2)）：保真核对范围**仅限被委托 agent 产出**，联网结果中的数字 / 网址**不纳入**核对；Q4=A（(e1)）：顾问模式下其他未预期异常也返回同一致歉文本，致歉文本固定中文。**核对结果**：ADR-R28-09 第 1 点原文"从被委托产出**与联网结果**中抽取'保护片段'"与 module_design IFC-R28-019 的"`check_fidelity(祖先产出 + 联网工具返回文本, …)`"**与 Q1=A 不一致**（实现 `src/ib/orchestration/dag.py:348-360` 已按 Q1=A：`check_fidelity(upstream_texts, content)`，联网文本只进 `exceeds_quote_limit`）。
- Decision: (1) 保护片段只从**被委托 agent（祖先 agent 节点）的产出**抽取；联网工具返回文本**只**用于 `exceeds_quote_limit`（AC-018-04：不得逐字复制 ≥200 字符），不进入 `check_fidelity`；(2) 联网结果中数字 / 网址的忠实度仅由顾问提示词承担，目标机人工观察后再定（OQ-R28-16；若改选 B，则变更本条与 AC-010-09）；(3) A-12（其他未预期异常同一致歉）与 A-12b（固定中文）**转为已裁决**（D-07），不再是 ASSUMPTION；(4) 其余（统一致歉常量、不可配置、非 5xx、不新增 `degrade_reason`）不变。
- Consequences: 正向——联网来源的改写（如"37 元"→"约 40 元"）不再造成用户可见致歉，降低 R-7 误报面；负向——联网结果中的数字 / 网址可能被顾问改写而无确定性核对，残余风险记入 R-11。

### ADR-R28-10-R1（订正 ADR-R28-10 的约束清单）
- Status: Accepted（沿用）　Type: constraint-driven
- 约束来源增补：画像 1.1.0 P11-3（闭源 API 只以资料为出处、不联网、测试只用离线替身、凭据复用现有 Key）。被排除的替代方案增补：`requests` / `httpx`（新增 HTTP 依赖，违反 D-07 指令）；`openai` SDK 的非公开工具接口（资料未载）；DeepSeek Fetch 作为抓取后端（ADR-R28-12）。Decision 增补：依赖清单**无新增**（`lxml` 为显式声明既有间接依赖，沿用）；`ib.webtools` 内网络导入仅限 `fetch.py`（抓取）与 `deepseek.py`（搜索）；出站目的地 = `api.deepseek.com:443`（搜索，与 LLM 同一服务方）＋公网 80/443（抓取，缺省关闭）。

### ADR 影响复核表（2.1.0，M-SA-002）

| ADR | 结论 | 说明 |
|---|---|---|
| ADR-R28-01 图表达 | 不受影响 | 联网工具实现不改图结构 |
| ADR-R28-02 会话上下文 | 不受影响 | — |
| ADR-R28-03 联网工具接入 | **受影响 → R1** | 第 3 / 6 / 10 / 11 点订正（见 ADR-R28-03-R1） |
| ADR-R28-04 搜索适配 + 抽取 | **受影响 → R1** | 厂商适配器由 ADR-R28-11 取代；抽取方案经 ADR-R28-12 再确认 |
| ADR-R28-05 顾问落地 | 不受影响 | Q2=A（Builder 摘要多 `web_search` / `web_fetch` 两个工具名）：摘要的工具名来自 `known_tool_names()`（`composition.py:1244`），已自动包含，**无设计变更**；新增回归断言（AC-017-06）见 module_design 回归点 #6 |
| ADR-R28-06 平台限制类参数 | 不受影响 | 机制不变；仅 `web_search` 的 `max_results` 取值域 1–10 → 1–50（module_design IFC-R28-007） |
| ADR-R28-07 全局上限 | 不受影响 | 上限含义增加"成本 / QPS 控制"备注（REQ-FUNC-018），数值与迁移不变 |
| ADR-R28-08 不可信内容与外发边界 | **受影响 → R1** | 检索词 ≤128、请求体字段集合固定 |
| ADR-R28-09 保真守卫 | **受影响 → R1** | 与 Q1=A 不一致处已订正；A-12 / A-12b 转已裁决 |
| ADR-R28-10 部署与依赖约束 | **受影响 → R1** | 增补 P11-3 约束与出站目的地 |
| ADR-R28-11 / 12 / 13 | 新增 | 本次修订 |
| R26 / R27 继承项 | 不受影响 | — |

## 风险（架构级）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-1 | 理解步骤 LLM 误判（意图 / 指代 / 话题），导致错误旁路 route 或联网外发"专业问题" | High | 评测集门槛（REQ-NFUNC-008）；`route_skip` 仅在意图明确为通用 / 寒暄 / 拒答时置位，`unknown` 一律走路由；"专业问题被误判为通用并联网外发 ≤0.02"作为验收阈值；评测集待用户提供前验收为"待评测集确认" |
| R-2 | 联网占用请求线程拖垮 ib-web | High | 并发闸 3、单轮累计耗时上限、协作式期限 + 看门狗、快速失败降级；`[TBD-R28-2]` 目标机压测 |
| R-3 | SSRF 绕过 | High | `getaddrinfo` 统一解析 + `is_global` + 钉 IP + 逐跳重校验 + 端口白名单 + 禁代理；≥30 条拒绝用例（REQ-NFUNC-004）；运维出站 ACL 第二道防线 |
| R-4 | 语义泄露（知识库内容被改写后外发） | Medium | 逐字重叠闸只能挡原样复制；提示词 + 域名白名单 + 出站 ACL；写入残余风险，不宣称根除 |
| R-5 | 搜索厂商接入延期 | Low（2.1.0 降级：厂商已定为 DeepSeek，P11-3 已补） | 端口 + 离线替身保留，顾问其余能力不受阻（联网降级）；残余见 R-9 |
| R-6 | `is_delegating` 语义复用被误操作 | Medium | 面板提示 + 代码注释 + 发布前核查存量 `advisor` 专家（OQ-ARCH-R28-02） |
| R-7 | 保真守卫误报，或顾问汇总步骤故障，直接变成用户可见的统一致歉（AQ1=B，不再回退展示原答） | High `[ESTIMATE]` | 抽取规则保守（仅数字 / 书名号 / 位置 / 网址）并可调；重试带明确"原样保留"指令；`advisor_apology` 事件按原因计数入日志，目标机观测触发率 `[TBD-R28-4]`；评测脚本含保真误报统计；规则调优只能放宽抽取，不得恢复展示原答；文案不可配置，避免配置泄露内部名称 |
| R-9 | DeepSeek 搜索的外部依赖风险：账户级 QPS（Search 100）、余额不足（402）、服务端错误、按次计费；资料由主会话整理、未核对原页面，字段若与实际不符只能在目标机暴露 | Medium `[ESTIMATE]` | 并发闸 3 + 每轮调用上限（缺省 5 次；按资料单价最坏每轮约 0.00375 美元，`5 × 0.75 / 1000`，仅成功且有结果才计费）；错误分类降级、不重试、不暴露细节；离线替身覆盖全部资料列出的错误码；目标机人工核对原页面与端到端验证（OQ-ARCH-R28-06 / 08） |
| R-10 | 保留本地抓取使 ib-web 需出站公网 80/443（ADR-R28-12 的代价） | Medium | 抓取总开关缺省关闭；开启前由运维配置出站 ACL；`UrlGuard` 钉 IP + 逐跳重校验 + ≥30 条拒绝用例；重新评估触发条件见 ADR-R28-12 |
| R-11 | 联网结果中的数字 / 网址被顾问改写而无确定性核对（Q1=A 的代价） | Medium | 仅提示词约束；`exceeds_quote_limit` 仍拦整段复制；目标机人工观察后再定是否纳入（OQ-R28-16） |
| R-8 | 引擎改动回归未启用项目 | High | "同输入逐字相同"回归集（N≥30 问句，离线替身）+ 既有全量回归零新增失败 + 新增 `dag` 契约测试（真实 langgraph） |

## 开放问题 / ASSUMPTION

**架构待裁决题 AQ1~AQ5：已裁决（用户 CP-002，经主会话转述，2026-11-02；requirements_spec D-06 / CL-003）**

| ID | 问题 | 裁决 | 落点 |
|---|---|---|---|
| AQ1 | 顾问汇总步骤自身失败（或保真守卫两次不通过）时怎么办？ | **已裁决：B**（统一致歉文案，不展示被委托 agent 原答）——**用户否决了推荐项 A**（回退原答）。文案礼貌专业、不泄露内部分工与错误细节、给出下一步建议；HTTP 非 5xx | ADR-R28-09（改写）、ADR-R28-01 后果 (4)、R-7；module_design IFC-R28-015/016/019；AC-006-07、AC-010-06/07 |
| AQ2 | 顾问节点能看到多长的会话历史？ | **已裁决：A**（与保留窗口一致 ≤20 条消息；超 8000 字符预算从最旧整条裁剪，最近一条始终保留） | ADR-R28-02 (2)；module_design IFC-R28-014/015；AC-011-05 |
| AQ3 | 是否接受"联网工具名出现在所有项目的可授权工具列表"？ | **已裁决：A**（全局登记；配置页列表多 `web_search` / `web_fetch` 2 项属展示变化，行为零变化） | ADR-R28-03 后果 (3)、ADR-R28-05 后果 (2)；module_design 回归点 #6；AC-017-05 |
| AQ4 | 是否增设 `IB_WEB_FETCH_ENABLED` 总开关？ | **已裁决：A**（增设，缺省关闭；关闭时已授权也不抓取、出站 0、如实告知；授权保存不受总开关限制） | ADR-R28-03 第 11 点；module_design IFC-R28-007/011/025；AC-015-05/06、AC-016-08 |
| AQ5 | 顾问模式身份标记 | **已裁决：A**（保留名 `advisor` + `is_delegating=True`，零 schema 变更）；前提不变：发布前核查存量定义中无同名专家（OQ-ARCH-R28-02） | ADR-R28-05 (1)a |
| Q7 | 搜索厂商 | **2.1.0 改判：本轮纳入**（CP-003「Q7 纳入」，取代 1.1.0 的"已裁决：C"）——提供方 = DeepSeek 官方 Search API；抓取方案见 ADR-R28-12 | ADR-R28-04-R1、ADR-R28-11、ADR-R28-12；module_design MOD-R28-03；AC-014-06~10 |

**待补资料 / `[UNSOURCED]`（不阻塞本轮；协议 §N，未联网查询）**
- OQ-ARCH-R28-01（**2.1.0 已关闭**）：搜索厂商 = DeepSeek（D-07），端点、鉴权、字段、错误码、限流以 P11-3 资料为出处，见 ADR-R28-11 与 module_design 出处表；原博查 / 阿里云候选作废。
- OQ-ARCH-R28-02：发布前请运维（只读）核查生产定义文档中是否存在名为 `advisor` 的专家。
- OQ-ARCH-R28-03：评测集数据（OQ-R28-12）待用户 / 业务方提供；真实 LLM 精准度与端到端时延 `[TBD-R28-1]` 目标机实测。
- OQ-ARCH-R28-04：出站 ACL / 防火墙（仅放行搜索主机与 80/443）由运维配置——属第二道防线，非本设计依赖；env 文件与 unit 变更由用户执行（画像 P7）。
- OQ-ARCH-R28-05：生产目标机的实际出网能力与白名单域名（C-R28-03）由运维确认。
- OQ-ARCH-R28-06（OQ-R28-15(a)）：`docs/external_api/deepseek_search_fetch.md` 由主会话据官方页面整理，PM 与本架构均未核对原页面；契约字段（请求 / 响应字段名、错误码表）在**目标机人工核对原页面**之前视为"以资料为准、待人工核实"。需用户在部署计划阶段安排核对（交 GROUP_E1 人工清单）。
- OQ-ARCH-R28-07（OQ-R28-15(b)(c)）：资料**未写明**：超时数值；Fetch 单域名 QPS；429 / 5xx / 408 / 504 的重试间隔与次数；Search 对 403 / 404 的语义（资料只在 Fetch 下列出）；DeepSeek 对重定向与内网地址的处置。本设计的处理：超时由平台强制（缺省 10 秒）；不重试（A-15）；Search 的未列状态码按 `rejected` 处理；抓取不使用 Fetch（ADR-R28-12）故后两项不影响本轮契约。
- OQ-ARCH-R28-08（AC-014-06 目标机人工验证清单，由用户 / 运维执行，子代理不连生产）：① 在 `/etc/intelligentbase/ib-web.env` 设 `IB_WEB_SEARCH_PROVIDER=deepseek`（不写 Key；Key 沿用 LLM 管理页写入的那一份）并重启 `ib-web`；② `GET /healthz/deps` 的 `egress_web` 出现 `api.deepseek.com` 与 `web_search_query`；③ 对已授权 `web_search` 的顾问提一个需要时效信息的通用问题，核对答复列出标题与网址、网址均来自检索结果；④ 查审计 `web.search` 条目只含主机名、不含检索词原文；⑤ 观察 DeepSeek 控制台用量与计费是否与调用次数一致（仅成功且有结果计费）。期望结果与步骤写入 E1 的人工验证清单。
- OQ-ARCH-R28-09：目标机出网：`api.deepseek.com:443` 已为 LLM 所需；抓取总开关开启前另需放行公网 80/443（R-10）；目标机是否经代理出网未知（A-19）。

**ASSUMPTION**
- A-1 `[ASSUMPTION]` 理解步骤用路由角色（温度 0）LLM，单次调用输出 JSON；无新增 LLM 角色类型。
- A-2 `[ASSUMPTION]` 顾问的 `max_steps` 种子值取 4（沿用默认，`DEFAULT_AGENT_MAX_STEPS`，`src/ib/runtime/compile.py:37`），即顾问节点内工具循环至多 4 轮。
- A-3 `[ASSUMPTION]` 顾问输入块的历史字符预算 8000（AQ2=A 已裁决为"预算内从最旧裁剪"，具体数值 8000 仍为假设，可调常量）。
- A-4 `[ESTIMATE]` 顾问回合 LLM 调用 ≥3 次（理解 + 被委托 agent + 顾问），端到端时延未测 `[TBD-R28-1]`。
- A-5 `[ASSUMPTION]` 抓取端口仅 80 / 443。
- A-6 `[ASSUMPTION]` 并发闸 3、DNS 小线程池 4、`ib-tool` 看门狗池 8（`waitress --threads=8`）；目标机压测校准 `[TBD-R28-2]`。
- A-7 `[ASSUMPTION]` 抓取外发声明的 `endpoint_host` 用 `"*"` 表示任意公网主机。
- A-8 （已转为用户裁决 AQ4=A，不再是假设）增设 `IB_WEB_FETCH_ENABLED`，缺省关闭。
- A-9 `[ASSUMPTION]` `lxml>=5.0,<7.0` 的下界为保守值；当前稳定版 6.1.3 与许可证 BSD-3-Clause 见 [WEB: https://pypi.org/pypi/lxml/json，2026-11-02]。
- A-10 `[ASSUMPTION]` 网页引用逐字复制上限 200 字符为平台常量（AC-018-04 的"配置的引用长度上限"本轮不开放配置）。
- A-11 `[ASSUMPTION]` 联网硬上限常量：每轮调用 20、抓取 5 MiB、单轮累计 120 秒（admin 只能在硬上限内设定）。
- A-12 / A-12b（**2.1.0 已裁决**，不再是 ASSUMPTION）：用户 CP-003 Q4=A（D-07）——顾问模式下 `run_dag` 之外的未预期异常也返回同一致歉文本；致歉文案为中文单一文本、不随提问者语言变化。
- A-13 `[ASSUMPTION]` `SearchHit.snippet` 取 `summary`（长摘要，约 600–800 字，资料标明"供模型使用"），为空时取 `snippet`；工具层摘要截断由 400 提到 800 字符。资料未规定应用哪个字段喂给模型，此为设计取舍。`[P11: docs/external_api/deepseek_search_fetch.md:§Search 响应]`
- A-14 `[ASSUMPTION]` 搜索响应体读取上限 2 MiB（资料无响应大小数值；`count` ≤ 50 且 `need_content=false` 时 `content` 恒空，量级远低于此）。
- A-15 `[ASSUMPTION]` 不重试、每次尝试计入本轮上限（OQ-R28-15(b) 的保守缺省；资料未给重试间隔与次数）。
- A-16 `[ASSUMPTION]` `lang` 格式严格限定为 `^[A-Za-z]{2,3}(,[A-Za-z]{2,3}){0,4}$`（资料仅有 `lang:zh,en` 一个示例，未给语言代码全集），防止经配置注入其他查询操作符。
- A-17 `[ASSUMPTION]` 复用 LLM Key 的前提是 LLM 服务方即 DeepSeek：`cfg.llm.base_url` 的主机须为 `api.deepseek.com`，否则 `IB_WEB_SEARCH_PROVIDER=deepseek` 启动失败（只报键名）。
- A-18 `[ASSUMPTION]` 搜索请求不跟随 HTTP 重定向（3xx ⇒ `bad_response`），避免 `Authorization` 头被转发。
- A-19 `[ASSUMPTION]` 搜索传输沿用与 LLM 客户端相同的代理环境变量行为（`urllib` 默认），目标机是否经代理出网未知（OQ-ARCH-R28-09）。
- A-20 `[ASSUMPTION]` 以提供方返回顺序作为相关性顺序，不依据 `rerank_score` / `authority` 过滤或重排（资料只给解读阈值，未规定丢弃规则）。
- `[TBD-R28-4]` 致歉触发率（保真误报 + 汇总故障）目标机观测值与可接受阈值，待真实 LLM 评测后确定（编号只增不改，沿用 TBD-R28-1~3）。

**待用户裁决题 AQ6~AQ9（2.1.0；priority=NORMAL，均不阻塞；每题给选项与推荐）**

| ID | 问题 | 选项 | 推荐 |
|---|---|---|---|
| AQ6 | `web_search` 的"地域偏好"（REQ-FUNC-016 的结果语言 / 地域偏好）：DeepSeek 只支持 `lang:` 语言操作符，其 `localization` 是 **IP 地址**（外发终端地址，不符合 REQ-NFUNC-005），无法兑现"地域" | A) 保留 `region` 配置字段但适配器忽略，配置页对该参数加静态提示"当前提供方不支持"（零 schema 变更，已保存的配置仍有效）；B) 删除 `region` 参数（改动已有 `ToolSpec` 与已保存的 `param_values` 兼容性）；C) 允许发送 IP 形态的 `localization` | **A** |
| AQ7 | Key 轮换后"搜索同步生效"：现有 LLM Key 的生效语义是"保存 + 重启 ib-web"，搜索与之同一解析点，故**两者同在重启后生效** | A) 接受（推荐，零新增读点）；B) 对 LLM 与搜索一起做运行期热重载（需要重建 LLM provider 与搜索 provider，超出本轮，须回需求） | **A** |
| AQ8 | OQ-R28-15(b) 的重试：429 / 5xx / 408 / 504 是否重试 | A) 本轮不重试，每次尝试计入上限（推荐）；B) 对 408 / 429 / 500 / 504 各重试一次（需先由用户给出退避与是否计入上限的口径，且延长占用请求线程） | **A** |
| AQ9 | 抓取方案确认（ADR-R28-12）：保留本地 SafeFetcher | A) 保留本地抓取（推荐）；B) 改用 DeepSeek Fetch（须先接受"响应无最终网址"并修改 REQ-FUNC-017 / AC-015-01，且重写 REQ-NFUNC-004 的验收口径）；C) 混合（后续增量） | **A** |
