<phase_status project="intelligentbase" mode="INCREMENTAL" created="2026-11-02T20:45:55+08:00" updated="2026-11-04T14:42:25+08:00">
  <request><![CDATA[除了 kb-agent 以外，现在还需要一个可以给所有项目使用的顾问 agent，顾问 agent 默认是一个客户，能够专业有礼貌地回答客户的问题。对于专业的知识，他可以调用 kb-agent 查询 RAG，对于通用的信息，它可以使用 WebSearch 或者 WebFetch 这样的工具在互联网检索。后回答。并且它在一个会话中能保留上下文记忆，能够正确理解上下文的意思，包括话题的变化。能够精准识别意图，也能派发给其他 agent。并且把结果收拢总结答复。这个 agent 要加到这个编排系统中，以后新建项目也能决定用不用这个 agent，或者使用 agent-builder 对他进行微调。或者对多个 agent 进行编排。
（调用方转述用户原话：「先整理我的需求，写成用户故事。确认后再开始开发。」）]]></request>
  <revision>REV-28</revision>
  <scope>本轮（调用方指定）只执行 GROUP_A（PHASE_01、PHASE_02），以现有代码（HEAD 8d6fd4b）为基线；GROUP_A 门控后写检查点停止，用户确认用户故事后再进入 GROUP_B。不改产品代码。</scope>
  <profile version="1.1.0 (APPROVED, 2026-11-03 补入 P11：P11-3 DeepSeek Search/Fetch；此前 1.0.0 无 P11)"/>
  <groups>
    <group id="GROUP_A" agent="requirement-analyst" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_01" status="APPROVED"/><phase id="PHASE_02" status="APPROVED"/>
    </group>
    <group id="GROUP_B" agent="system-architect" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_03" status="APPROVED"/><phase id="PHASE_04" status="APPROVED"/>
    </group>
    <group id="GROUP_C" agent="software-developer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_05" status="APPROVED"/><phase id="PHASE_06" status="APPROVED"/>
    </group>
    <group id="GROUP_D" agent="test-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0" defect_loops="2">
      <phase id="PHASE_07" status="APPROVED"/><phase id="PHASE_08" status="APPROVED"/><phase id="PHASE_09" status="APPROVED"/>
    </group>
    <group id="GROUP_E1" agent="devops-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_10" status="APPROVED"/><phase id="PHASE_11a" status="APPROVED"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="NOT_AUTHORIZED" environment=""/>
  </groups>
  <artifacts>
    <artifact path="docs/sdlc/intelligentbase/archive/rev27/" version="REV-27 全套（16 个文档，含 phase_status.md）" status="SUPERSEDED" group="ARCHIVE"/>
    <artifact path="docs/sdlc/intelligentbase/requirements_spec.md" version="1.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/user_stories.md" version="1.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/requirements_spec.md" version="2.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/requirements_spec.md" version="3.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/requirements_spec.md" version="4.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/requirements_spec.md" version="5.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/user_stories.md" version="2.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/user_stories.md" version="3.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/user_stories.md" version="4.0.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/user_stories.md" version="5.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="docs/sdlc/intelligentbase/architecture_design.md" version="1.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/architecture_design.md" version="2.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/architecture_design.md" version="3.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/module_design.md" version="1.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/module_design.md" version="2.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/module_design.md" version="3.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/tech_stack.md" version="1.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/tech_stack.md" version="2.0.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/tech_stack.md" version="3.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="docs/sdlc/intelligentbase/implementation_plan.md" version="1.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/implementation_plan.md" version="2.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/implementation_plan.md" version="3.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/implementation_plan.md" version="4.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/code_review_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/code_review_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/code_review_report.md" version="3.0.0" status="SUPERSEDED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/code_review_report.md" version="4.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="docs/sdlc/intelligentbase/test_plan.md" version="1.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/unit_test_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/integration_test_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/e2e_test_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/test_plan.md" version="2.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/unit_test_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/integration_test_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/e2e_test_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/test_plan.md" version="3.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/unit_test_report.md" version="3.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/integration_test_report.md" version="3.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/e2e_test_report.md" version="3.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="docs/sdlc/intelligentbase/cicd_pipeline.md" version="1.0.0" status="SUPERSEDED" group="GROUP_E1"/>
    <artifact path="docs/sdlc/intelligentbase/deployment_plan.md" version="1.0.0" status="SUPERSEDED" group="GROUP_E1"/>
    <artifact path="docs/sdlc/intelligentbase/cicd_pipeline.md" version="2.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="docs/sdlc/intelligentbase/deployment_plan.md" version="2.0.0" status="APPROVED" group="GROUP_E1"/>
  </artifacts>
  <legacy_baseline>REV-27 已批准产物（archive/rev27/ 副本；原位 architecture_design.md / module_design.md 等在 GROUP_B 重写前作为基线只读）；本轮需求基线以现有代码（HEAD 8d6fd4b）为准。</legacy_baseline>
  <invocations>
    <invocation id="intelligentbase-R28-GROUP_A-001" agent="requirement-analyst" start="2026-11-02T20:46:11+08:00" end="2026-11-02T20:53:02+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_A-002" agent="requirement-analyst" start="2026-11-02T21:01:24+08:00" end="2026-11-02T21:08:20+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_B-001" agent="system-architect" start="2026-11-02T21:08:20+08:00" end="2026-11-02T21:31:27+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_A-003" agent="requirement-analyst" start="2026-11-02T21:47:51+08:00" end="2026-11-02T21:50:28+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_B-002" agent="system-architect" start="2026-11-02T21:50:28+08:00" end="2026-11-02T21:56:01+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_C-001" agent="software-developer" start="2026-11-02T21:56:01+08:00" end="2026-11-02T22:31:13+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_D-001" agent="test-engineer" start="2026-11-02T22:31:13+08:00" end="2026-11-02T23:26:01+08:00" result="PARTIAL_SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_C-002" agent="software-developer" start="2026-11-02T23:26:01+08:00" end="2026-11-02T23:30:04+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_D-002" agent="test-engineer" start="2026-11-02T23:30:04+08:00" end="2026-11-02T23:38:48+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_A-004" agent="requirement-analyst" start="2026-11-03T17:26:48+08:00" end="2026-11-03T17:32:38+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_B-003" agent="system-architect" start="2026-11-03T17:32:38+08:00" end="2026-11-03T17:49:46+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_C-003" agent="software-developer" start="2026-11-03T17:49:46+08:00" end="2026-11-03T18:07:44+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_D-003" agent="test-engineer" start="2026-11-03T18:07:44+08:00" end="2026-11-03T18:33:02+08:00" result="PARTIAL_SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_C-004" agent="software-developer" start="2026-11-03T18:33:02+08:00" end="2026-11-03T18:38:47+08:00" result="PARTIAL_SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_D-004" agent="test-engineer" start="2026-11-03T18:38:47+08:00" end="2026-11-03T18:45:08+08:00" result="UNKNOWN（会话中断，agent_response 未送达；产出已核实完整）"/>
    <invocation id="intelligentbase-R28-GROUP_E1-001" agent="devops-engineer" start="2026-11-04T11:08:25+08:00" end="2026-11-04T11:18:49+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_A-005" agent="requirement-analyst" start="2026-11-04T14:31:25+08:00" end="2026-11-04T14:33:09+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_D-005" agent="test-engineer" start="2026-11-04T14:33:09+08:00" end="2026-11-04T14:40:43+08:00" result="SUCCESS"/>
    <invocation id="intelligentbase-R28-GROUP_E1-002" agent="devops-engineer" start="2026-11-04T14:40:43+08:00" end="2026-11-04T14:42:25+08:00" result="SUCCESS"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="intelligentbase-R28-GROUP_A-001" decision="PASS_WITH_CONDITIONS" time="2026-11-02T20:53:02+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/requirements_spec.md" version="0.1.0"/><file path="docs/sdlc/intelligentbase/user_stories.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A 文件存在与文件头" result="SATISFIED">两文件存在（20:50:38 / 20:51:59），文件头齐全，0.1.0 DRAFT，timestamp 2026-11-02T20:47:23+08:00 为真实时间；git status 仅两文档 + phase_status + archive/rev27 变动，无产品代码改动</criterion>
      <criterion id="J-A 来源" result="SATISFIED">29 条需求（18 FUNC + 11 NFUNC）均有来源列。PM 抽查 3 条：src/ibweb/composition.py:103 确为 SEARCH_TOOL_SPEC(name="search_knowledge")；src/ib/routing/intent.py:405 确为 _sticky_expert（历史仅用于粘性）；src/ib/streaming/__init__.py:222 MemorySessionStore max_sessions=2000、idle_ttl_s=24*3600。引号内用户原话逐条比对均出自用户原文（P-PM-003）</criterion>
      <criterion id="J-A AC 格式" result="SATISFIED">user_stories.md 中 AC-NNN-NN 行 78 条，不含 Given 的仅 1 行且为说明性引用（非 AC 定义）</criterion>
      <criterion id="J-A INFERRED 占比" result="SATISFIED">5/29=17.2% ≤ 0.20（requirements_spec.md:33），INF-1~5 已汇总于"待确认推断项"</criterion>
      <criterion id="J-A 无技术实现" result="SATISFIED">正文为可观察行为；工具名 web_search/web_fetch 源自用户原话 WebSearch/WebFetch；condense question 等选型只出现在 OQ-R28-09（明示不进需求正文）</criterion>
      <criterion id="J-A 必读" result="SATISFIED">notes 已读清单含协议、画像、通用经验、R27 基线两份与基线代码行号</criterion>
      <finding id="GR-A-001-F01" severity="MINOR">notes 自述未读 ConfigStudio 工具授权前端内部细节（required_reading 已点名），仅引用文件名；需求层面未见因此出错。GROUP_B 调用时点名要求先读。</finding>
      <finding id="GR-A-001-F02" severity="MINOR">REQ-FUNC-018（requirements_spec.md:83）把用户原文「后回答」列为"联网治理"的来源，属牵强引用；真实来源是调用方转述（域名白名单/黑名单），用户确认时一并核对。</finding>
      <condition>用户确认 US-001~019、OQ-R28-01~12 与 INF-1~5 后才进入 GROUP_B；改选项时由 requirement-analyst 定向修订。OQ-R28-07/08（出网能力、搜索服务）未定时 GROUP_B 须把联网工具设计为提供方可替换、默认停用。</condition>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="intelligentbase-R28-GROUP_A-002" decision="PASS" time="2026-11-02T21:08:20+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/requirements_spec.md" version="1.1.0"/><file path="docs/sdlc/intelligentbase/user_stories.md" version="1.1.0"/></reviewed_files>
      <criterion id="J-A 文件头与版本" result="SATISFIED">两文件 1.1.0 DRAFT（§B 回流 MINOR+1），timestamp 2026-11-02T21:03:27+08:00 真实；各含"修订记录"（requirements_spec.md:30）；git status 无产品代码改动</criterion>
      <criterion id="J-A 来源" result="SATISFIED">D-03（requirements_spec.md:39）引号内文本与用户 Q3 原话逐字一致；「尽量复用，不要重复造轮子」与用户原话一致；博查/IQS 仅在 D-04 标"主会话推荐"，未写端点/字段/价格（§N 合规）；C-R28-08 引 graph.py:133/:198，PM 已 git grep 核实</criterion>
      <criterion id="J-A AC 格式" result="SATISFIED">AC 行 83 条，非 G/W/T 的仅 AC-006-04"已删除"占位行</criterion>
      <criterion id="J-A INFERRED 占比" result="SATISFIED">REQ 行带 [INFERRED] 0 条；0/29=0%（INF-2~5 经 CL-001 Q1=A 确认，INF-1 作废并入取代登记 requirements_spec.md:49）</criterion>
      <criterion id="J-A 无技术实现" result="SATISFIED">"回到顾问"的图表达方式未在需求中选定，交 OQ-R28-14 / ADR</criterion>
      <criterion id="GR-A-001 条件与 finding" result="SATISFIED">F02 已修（REQ-FUNC-018 来源删去「后回答」，requirements_spec.md:113）；条件一（用户确认）经 CL-001 闭合；F01 转为 GROUP_B 必读要求</criterion>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="intelligentbase-R28-GROUP_B-001" decision="PASS_WITH_CONDITIONS" time="2026-11-02T21:31:27+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/architecture_design.md" version="0.1.0"/><file path="docs/sdlc/intelligentbase/module_design.md" version="0.1.0"/><file path="docs/sdlc/intelligentbase/tech_stack.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-B 文件与文件头" result="SATISFIED">三文件存在（21:28:59~21:29:47），0.1.0 DRAFT，timestamp 真实（21:19:03 / 21:25:04 / 21:28:55）；git status 无产品代码改动（另有 system-architect MEMORY.md 待验证区追加，属 §A 允许）</criterion>
      <criterion id="J-B REQ 覆盖" result="SATISFIED">module_design.md:619 需求覆盖表 REQ-FUNC-001~018 与 REQ-NFUNC-001~011 均映射到 MOD-R28-01~18，无空行</criterion>
      <criterion id="J-B 无循环依赖" result="SATISFIED">module_design.md:655 依赖边均为高号→低号（编号即拓扑序），无反向边</criterion>
      <criterion id="J-B ADR" result="SATISFIED">ADR-R28-01~10 均有 Status（9 Proposed decision、1 Accepted constraint-driven 并写约束来源 P6/P7/P8）；ADR-R28-01 比较 A/B/C/D 四方案（architecture_design.md:77-88），选 C：顾问为单 agent 节点置于委托链之后作唯一叶子（with_upstream），"理解"为回合前置步骤，route __else__→顾问供通用问题直接联网</criterion>
      <criterion id="J-B 类型签名 / 迁移 / 运行单元" result="SATISFIED">IFC-R28-001~028 有类型签名；"数据迁移"（module_design.md:671，009_web_governance.sql，现有迁移止于 008，单源 schema.py，DROP 回滚标 MANUAL_ROLLBACK_REQUIRED）；"受影响的运行单元"（:682，仅 ib-web 重启 + 前端构建，无新增 systemd 单元）</criterion>
      <criterion id="J-B 引用现有代码真实存在" result="SATISFIED">PM 抽查 11 处：graph.py:129 graph_agent_id_mismatch；dag.py:395-399 叶子判定；orchestration/__init__.py:925 _aggregate、:1325 _strip_internal_labels；intent.py:367-373 默认专家兜底；llm/__init__.py:170 build_router；ib-web.service:52 --threads=8；schema.py:398 llm_key 单行表；tools/__init__.py:284 derive_tool_param_specs；rubric.py:125-129 条款仅对检索工具；embedding/__init__.py:259 stdlib urllib。git grep 核实 canonical_graph_from_experts、evaluate_condition、known_tool_names、seed_project、_require_admin、build_capability_digest 存在</criterion>
      <criterion id="J-B 禁用技术（P8）" result="SATISFIED">无 Docker/Redis/Channels/PyMuPDF/langchain-openai≥0.3/新增单元；新增依赖仅 lxml&gt;=5.0,&lt;7.0（BSD-3，经 python-docx 已间接引入，现改显式），tech_stack.md:50 已核对 P8</criterion>
      <criterion id="J-B §N 出处" result="SATISFIED">出处表（module_design.md:728）共 21 行，[CODE:] 行已在上述抽查中核对；厂商端点/鉴权/字段/错误码/限流全部标 [UNSOURCED] 且不进入接口契约（IFC-R28-005 仅项目自有 SearchErrorKind）；未联网查询厂商 API；[WEB:] 仅 PyPI 与 Python 官方文档（公开）</criterion>
      <finding id="GR-B-001-F01" severity="MINOR">画像 P10 基线 docs/architecture_design.md、docs/module_design.md 仅 grep 定位未通读，FlowCanvas.vue 未读正文（notes 自述）；本次产出未见因此出错。GROUP_C 调用时点名要求开发前读 FlowCanvas.vue 及 P10 设计中 dag/route 相关章节。</finding>
      <finding id="GR-B-001-F02" severity="MINOR">architecture_design.md:130 称 langchain-community"用户已明示不引入"——该项是主会话推荐（CL-001 Q4 转述），用户原话只有「尽量复用，不要重复造轮子」。归属不准确，下一次修订 architecture_design 时更正为"主会话推荐，用户复用原则"。</finding>
      <finding id="GR-B-001-F03" severity="MINOR">出处表 IFC-R28-022~025 引 views.py:2165-2199 作 _require_admin 出处，实际 :2165 为 llm_key_endpoint（使用方），_require_admin 定义在 views.py:1724；行号精度问题，不影响契约。</finding>
      <condition>进入 GROUP_C 前：用户裁决 AQ1~AQ5（架构待裁决题，architecture_design 末尾）；搜索厂商确认并补画像 P11-3 前，GROUP_C 只实现提供方无关端口 + Null/Fake 提供方，不实现任何厂商适配器（OQ-ARCH-R28-01）。</condition>
      <condition>发布前（E1/E2）：运维只读核查生产定义无名为 advisor 的专家（OQ-ARCH-R28-02）；目标机 venv lxml 版本核对（TBD-R28-3）；ib-web.env 新增键由用户编辑。</condition>
    </gate_review>
    <gate_review id="GR-A-003" invocation_id="intelligentbase-R28-GROUP_A-003" decision="PASS" time="2026-11-02T21:50:28+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/requirements_spec.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/user_stories.md" version="2.1.0"/></reviewed_files>
      <criterion id="J-A 文件头" result="SATISFIED">2.1.0 DRAFT，timestamp 2026-11-02T21:48:15+08:00；修订记录追加 2.1.0</criterion>
      <criterion id="J-A 来源与裁决落点" result="SATISFIED">REQ-FUNC-012 (e) 统一致歉、不展示原答、不泄露内部分工与错误细节，来源"用户裁决 CL-003 Q2=B（经主会话转述）"；AQ2/AQ3/AQ4 分别落 REQ-FUNC-013、REQ-NFUNC-001、REQ-FUNC-017/018；Q7=C 落 AC-014-06 与 OQ-R28-08/13</criterion>
      <criterion id="J-A AC 格式" result="SATISFIED">新增 9 条 AC（006-07、010-06/07、011-05、014-06、015-05/06、016-08、017-05）PM 逐条 grep 均含 Given；AC 总计 92</criterion>
      <criterion id="J-A INFERRED 占比" result="SATISFIED">0/29=0%</criterion>
    </gate_review>
    <gate_review id="GR-B-002" invocation_id="intelligentbase-R28-GROUP_B-002" decision="PASS_WITH_CONDITIONS" time="2026-11-02T21:56:01+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/architecture_design.md" version="1.1.0"/><file path="docs/sdlc/intelligentbase/module_design.md" version="1.1.0"/><file path="docs/sdlc/intelligentbase/tech_stack.md" version="1.1.0"/></reviewed_files>
      <criterion id="J-B 文件头" result="SATISFIED">三文件 1.1.0 DRAFT，timestamp 2026-11-02T21:50:53+08:00，各有修订记录</criterion>
      <criterion id="裁决落点" result="SATISFIED">ADR-R28-09 改选统一致歉（原回退原答保留为已否决选项）；致歉文案为不可配置常量 ADVISOR_APOLOGY_TEXT（module_design.md:487）+ selfcheck advisor_apology_text_safe；IB_WEB_FETCH_ENABLED 缺省关闭短路（module_design.md:309、:382）；历史裁剪 HistoryDigest；MOD-R28-03 仅端口/注册表/Null/Fake，无厂商适配器</criterion>
      <criterion id="GR-B-001 F02/F03" result="SATISFIED">grep"用户已明示/用户指示"仅剩修订记录行；_require_admin 出处改 [CODE: src/ibweb/views.py:1724]（module_design.md:791）</criterion>
      <criterion id="覆盖 / 无环 / 迁移 / 运行单元" result="SATISFIED">新增"新增 AC 承接表"覆盖 9 条新 AC；MOD 18、迁移仅 009、运行单元不变</criterion>
      <finding id="GR-B-002-F01" severity="MAJOR">ASSUMPTION A-12b"致歉文案为中文单一文本，不随提问者语言变化"与 REQ-FUNC-002"使用提问者的语言作答"存在冲突；需用户确认是否接受该例外（仅致歉这一兜底文案）。不阻塞开发：GROUP_C 按设计实现，用户若否决再定向修订。</finding>
      <finding id="GR-B-002-F02" severity="MINOR">架构师自行延伸的两点需用户确认：A-12（顾问模式下 run_dag 之外的未预期异常也返回同一致歉文本）；本轮 search.py 不含任何网络代码（Q7=C 的延伸）。均为更保守的方向，PM 判定可先按此实现。</finding>
      <condition>GROUP_C：按 2.0.0 设计实现；不实现任何搜索厂商适配器；开发前先读 FlowCanvas.vue 与 P10 基线设计中 dag/route 相关章节（GR-B-001-F01）。</condition>
      <condition>交付汇报中请用户确认 A-12、A-12b。</condition>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="intelligentbase-R28-GROUP_C-001" decision="PASS_WITH_CONDITIONS" time="2026-11-02T22:31:13+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/implementation_plan.md" version="0.1.0"/><file path="docs/sdlc/intelligentbase/code_review_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-C MOD 全部实现" result="SATISFIED">MOD-R28-01~18 DONE；两子项按角色移交（ci.yml→E1，新测试→GROUP_D），implementation_plan 已登记</criterion>
      <criterion id="J-C 无未解决 CRITICAL / MAJOR 遗留" result="SATISFIED">CR-001 CRITICAL 已修；MAJOR 遗留 3（CR-006/007/008）≤3 且逐条有原因；评分与统计（1/7/5）算术一致</criterion>
      <criterion id="J-C PM 复跑零新增失败" result="SATISFIED">见 verification：pytest 914 passed（基线 914）；selfcheck 64/65，唯一 FAIL 为基线既有环境性 core_framework_free，新增 7 用例全 PASS；前端 build rc=0、npm test 141/141（基线 141）</criterion>
      <criterion id="J-C 改动范围" result="SATISFIED">git status：src 下 32 个修改 + 新增 webtools/、advisor/、web_governance.py、advisor.md、009 迁移、advisor_eval.py、advisorPlan.ts、WebGovernancePage.vue，与 implementation_plan 清单一致；无无关改动；3 个既有测试改动仅为 AQ3 全局多 2 项，断言为精确集合（非放宽），search_knowledge 精确断言保留</criterion>
      <criterion id="J-C 迁移（P6）" result="SATISFIED">009_web_governance.sql 新号、单源（selfcheck web_governance_schema_single_source PASS）、头注释 MANUAL_ROLLBACK_REQUIRED</criterion>
      <criterion id="J-C P8 / 凭据 / §N-2" result="SATISFIED">diff 中无 Docker/PyMuPDF/axios/CDN/langchain_community/ib_embed 导入；lxml&gt;=5.0,&lt;7.0 上下界齐全；env.example 仅占位 &lt;REPLACE_ME_web_search_api_key&gt;；search.py 无网络导入、无厂商名/端点（grep bocha/aliyun/iqs/http 无命中）</criterion>
      <finding id="GR-C-001-F01" severity="MAJOR">CR-007：联网结果未纳入保真守卫保护片段，偏离 ADR-R28-09 文字；需用户裁决（见检查点）。</finding>
      <finding id="GR-C-001-F02" severity="MAJOR">CR-010：Builder 的项目摘要对所有项目（含未启用顾问的项目）新增 web_search/web_fetch 工具名，属外发给 LLM 的内容变化；REQ-NFUNC-001 例外只覆盖"可授权工具列表展示"。仅工具名、无业务数据，但需用户确认是否接受或改为仅顾问项目。</finding>
      <finding id="GR-C-001-F03" severity="MAJOR">CR-008：理解器复用 router 角色，system 提示要求 JSON 数组与理解器 JSON 对象冲突，已 fail-open；GROUP_D 须有成对用例（fail-open 降级 + happy path 正例断言"理解成功且未降级"，M-PM-001）。</finding>
      <finding id="GR-C-001-F04" severity="MINOR">必读漏读第二次出现：FlowCanvas.vue 与 P10 基线设计仍未读（GR-B-001-F01 已点名），本次未见因此出错；requirements/user_stories 未逐字通读。</finding>
      <finding id="GR-C-001-F05" severity="MINOR">CR-009：IB_WEB_SEARCH_PROVIDER=fake 在生产可被接受，会向客户返回替身结果；建议限制为仅离线模式（待用户确认）。</finding>
      <condition>GROUP_D：覆盖全部 Must AC；未启用顾问项目"同输入逐字相同"回归集；致歉路径（AC-006-07、010-06/07）断言不含原答特征串与内部名；抓取总开关缺省关闭（AC-015-05/06）；SSRF ≥30、注入 ≥20、canary ≥30（REQ-NFUNC-003~005）；fail-open 用例与 happy-path 正例成对。</condition>
      <condition>GROUP_E1：ci.yml 迁移检查追加 009（CR-006）。</condition>
      <verification><![CDATA[env PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings; P=/root/.venvs/intelligentbase/bin/python
$P -m compileall -q src -> rc=0
$P -m pytest tests -q -p no:cacheprovider -> 914 passed in 29.75s
$P src/scripts/selfcheck.py -> 自检结果：64/65 通过；FAIL core_framework_free（sitecustomize，基线既有）
(cd src/frontend && npm run build) -> ✓ built in 31.94s rc=0 ; npm test -> # tests 141 # pass 141 # fail 0 # skipped 0
git diff --stat -- src tests -> 35 files changed, 1624 insertions(+), 85 deletions(-)]]></verification>
    </gate_review>
    <gate_review id="GR-C-002" invocation_id="intelligentbase-R28-GROUP_C-002" decision="PASS" time="2026-11-02T23:30:04+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/implementation_plan.md" version="1.1.0"/><file path="docs/sdlc/intelligentbase/code_review_report.md" version="1.1.0"/></reviewed_files>
      <criterion id="DEF-001 已修" result="SATISFIED">src/ib/webtools/tools.py:300 改为 budget.charge_bytes(result.bytes_read)（无条件入账），gate.py:78 新增 charge_bytes；add_bytes 保留（生产无其他调用方，开发者已 grep）</criterion>
      <criterion id="只改实现不改测试（M-PM-005）" result="SATISFIED">tests/unit/test_webtools_tools_unit_r28.py mtime 23:04:59，早于修复 23:26:39；git status 无其他测试变动</criterion>
      <criterion id="PM 复跑" result="SATISFIED">见 verification：仅冻结用例 TC-UNIT-R28-085 失败（预期信号），其余 1230 passed；selfcheck 64/65 仅基线既有失败</criterion>
      <criterion id="文档" result="SATISFIED">两文档 1.1.0 DRAFT，修订记录 + DEF-001 说明；CR-014 MINOR（超限读取全额入账，bytes_used 可略超上限，语义"耗尽即拒后续"）</criterion>
      <verification><![CDATA[$P -m compileall -q src -> ok
$P -m pytest tests -q -p no:cacheprovider -> 1 failed, 1230 passed in 46.56s (FAILED test_TC_UNIT_R28_085_fetch_tool_total_bytes_budget_and_call_limit)
$P src/scripts/selfcheck.py -> 自检结果：64/65 通过]]></verification>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="intelligentbase-R28-GROUP_D-002" decision="PASS_WITH_CONDITIONS" time="2026-11-02T23:38:48+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/test_plan.md" version="0.2.0"/><file path="docs/sdlc/intelligentbase/unit_test_report.md" version="0.2.0"/><file path="docs/sdlc/intelligentbase/integration_test_report.md" version="0.2.0"/><file path="docs/sdlc/intelligentbase/e2e_test_report.md" version="0.2.0"/></reviewed_files>
      <criterion id="J-D 三层报告齐全" result="SATISFIED">四份文档 0.2.0 DRAFT（23:35:17），含修订记录（D-001 0.1.0 → D-002 0.2.0）</criterion>
      <criterion id="J-D PM 复跑一致" result="SATISFIED">见 verification：unit 723 / integration 431 / e2e 63 / 全量 1232 passed，collect-only 1232，与报告逐项一致；selfcheck 64/65 仅基线既有失败；前端 160/160</criterion>
      <criterion id="J-D 基线判定（§K baseline）" result="SATISFIED">基线 914 → 1232 = 914 + 新写 318（208/98/12），新增失败 0；前端 141 → 160（+19）</criterion>
      <criterion id="J-D Must 覆盖与 critical path" result="SATISFIED">Must 18/18 有真实执行用例（test_plan AC→TC 矩阵）；critical path 12/12=1.00；NOT_TESTABLE 4 项（AC-014-06、AC-019-01/02/04）不计分母且入人工清单；待人工验证 13 项（MV-01~13）</criterion>
      <criterion id="GR-C-001 条件" result="SATISFIED">未启用顾问回归集 33 问逐字对照黄金文件（黄金由基线 8d6fd4b git archive 生成，独立于被测代码）；致歉路径与正例成对；抓取总开关缺省出站 0；SSRF 56+9+10 放行 0、注入 22、canary 30 会话 0 命中；fail-open 与 happy path 成对</criterion>
      <criterion id="防注水 / 冻结点" result="SATISFIED">新测试文件无 skip/xfail/deselect；测试文件 mtime 23:31:23 早于报告 23:35:17；DEF-001 翻转强度不低于原描述（M-PM-002）：bytes 入账、第 3 次出站 0（tr.count == 2）、PHRASE_BUDGET + budget_exceeded 事件、总下载量口径；另补正例 TC-UNIT-R28-088；DEF-001-GUARD 守卫串已移除（grep 0）</criterion>
      <criterion id="产品代码未被测试改动" result="SATISFIED">find src -newer src/ib/webtools/tools.py 无产品文件（仅测试文件）</criterion>
      <finding id="GR-D-001-F01" severity="MINOR">必读漏读：D-001 未通读 requirements_spec / architecture_design / module_design / ci.yml，D-002 点名补读仍未读（自述）；本次产出未见因此出错。同类漏读本轮在 B/C/D 均出现，记 PM 待验证经验。</finding>
      <finding id="GR-D-001-F02" severity="MINOR">13 项待人工验证（真实 LLM 精准度、真实 DNS/TLS、浏览器交互、真实搜索厂商等），最终状态至多 DELIVERED_WITH_ISSUES。</finding>
      <condition>E1 前：用户裁决 CP-003（CR-007、CR-009、CR-010、A-12/A-12b、OBS-1、下一步）。</condition>
      <condition>E1：ci.yml 迁移检查追加 009（CR-006）；部署计划含 ib-web.env 新键（用户编辑）、目标机 lxml 核对、发布前只读核查无同名 advisor 专家、MV-01~13 人工验收清单。</condition>
      <verification><![CDATA[P=/root/.venvs/intelligentbase/bin/python（离线环境变量同画像 P4）
$P -m pytest tests/unit -q -p no:cacheprovider -> 723 passed in 7.93s
$P -m pytest tests/integration -q -p no:cacheprovider -> 431 passed in 36.76s
$P -m pytest tests/e2e -q -p no:cacheprovider -> 63 passed in 4.37s
$P -m pytest tests -q -p no:cacheprovider -> 1232 passed in 47.20s ; --collect-only -> 1232 tests collected
$P src/scripts/selfcheck.py -> 自检结果：64/65 通过（core_framework_free，基线既有环境性）
(cd src/frontend && npm test) -> # tests 160 # pass 160 # fail 0（D-001 后 PM 已复跑 npm run build rc=0）
grep -c DEF-001-GUARD tests/unit/test_webtools_tools_unit_r28.py -> 0]]></verification>
    </gate_review>
    <gate_review id="GR-A-004" invocation_id="intelligentbase-R28-GROUP_A-004" decision="PASS" time="2026-11-03T17:32:38+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/requirements_spec.md" version="3.1.0"/><file path="docs/sdlc/intelligentbase/user_stories.md" version="3.1.0"/></reviewed_files>
      <criterion id="J-A 文件头" result="SATISFIED">3.1.0 DRAFT，timestamp 2026-11-03T17:28:10+08:00，修订记录追加</criterion>
      <criterion id="J-A 来源 / §N" result="SATISFIED">外部事实均标 [P11: docs/external_api/deepseek_search_fetch.md:§…]（§Search 请求/响应、§错误、§限流与计费、§测试替身、§Fetch 请求与响应），PM 对照资料：检索词 1–128 字符、条数 1–50、错误码 400/401/402/403/404/408/413/429/500/504 与资料一致；端点/字段名未抄入需求（分析师 grep 无命中）；用户原话「Q7 纳入。 Q6：A 其他推荐」与转述分开标注</criterion>
      <criterion id="J-A AC 格式" result="SATISFIED">新增/改写 AC（001-04、010-08/09、014-06~10、015-07、016-09、017-06、018-05/06、020-01~03）PM 逐条 grep 均含 Given；AC 总计 107；US 20（新增 US-020 替身仅离线）</criterion>
      <criterion id="J-A INFERRED 占比" result="SATISFIED">0/30=0%（REQ 行中"INFERRED"字样仅为历史取代说明）</criterion>
    </gate_review>
    <gate_review id="GR-B-003" invocation_id="intelligentbase-R28-GROUP_B-003" decision="PASS_WITH_CONDITIONS" time="2026-11-03T17:49:46+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/architecture_design.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/module_design.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/tech_stack.md" version="2.1.0"/></reviewed_files>
      <criterion id="J-B 文件头" result="SATISFIED">三文件 2.1.0 DRAFT，修订记录齐全</criterion>
      <criterion id="J-B ADR" result="SATISFIED">新增 ADR-R28-11（DeepSeek 搜索适配器 + Key 复用，Proposed）、ADR-R28-12（抓取方案：比较 DeepSeek Fetch / 本地 SafeFetcher / 混合，选本地——Fetch 响应无最终网址与 REQ-FUNC-017 冲突、重定向/内网处置资料未写）、ADR-R28-13（fake 非离线启动失败，只报键名）；ADR-03/04/08/09/10 以 R1 订正</criterion>
      <criterion id="J-B §N 出处核对（抽查 10 条，PM 逐条对照 docs/external_api/deepseek_search_fetch.md）" result="SATISFIED">module_design.md:258 端点 POST /v1/tools/search；:301 Bearer + Content-Type；:941 未知字段忽略；:259 query ≤128；:260 count ≤50；:310-315 错误码 400/413/401/402/408/504/429/500 语义与重试规则；:314 Search QPS 100；:340 rerank_score 0–3、authority -1..4、date RFC 3339；:351 计费仅 200 且非空；Fetch 无最终网址（资料"Fetch 请求与响应"只有 title/content）——均与资料一致。资料空白项（重定向/内网处置、单域名 QPS、超时数值）标 [UNSOURCED] 且不入契约</criterion>
      <criterion id="J-B 引用现有代码" result="SATISFIED">composition.py:817-822 llm_key 存储解析；llm/__init__.py:461-466 IB_LLM_API_KEY 兼容回退；views.py llm_key_endpoint 文档串"生效 = 保存 + 服务重启重装配"——均核实</criterion>
      <criterion id="J-B 覆盖 / 迁移 / 运行单元 / P8" result="SATISFIED">覆盖表补 REQ-FUNC-019、US-020；IFC 28→32；迁移仍只 009；无新增运行单元与依赖；删除 IB_WEB_SEARCH_API_KEY / IB_WEB_SEARCH_BASE_URL，不新增凭据键</criterion>
      <finding id="GR-B-003-F01" severity="MINOR">AQ6~AQ9 为 NORMAL 待裁决题；子代理模式下 PM 按"最保守、改动最小"代答（CL-005），待用户确认。</finding>
      <condition>GROUP_C 按 3.0.0 设计实现 DeepSeek 搜索适配器 + 离线替身 + fake 非离线启动失败；自动化测试禁止调用真实端点。</condition>
    </gate_review>
    <gate_review id="GR-C-003" invocation_id="intelligentbase-R28-GROUP_C-003" decision="PASS_WITH_CONDITIONS" time="2026-11-03T18:07:44+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/implementation_plan.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/code_review_report.md" version="2.1.0"/></reviewed_files>
      <criterion id="J-C 实现" result="SATISFIED">新增 src/ib/webtools/deepseek.py（适配器 + UrllibPostTransport，无重定向处理器）、deepseek_double.py（离线替身）；Key 复用、fake 非离线启动失败、配置键删除（git grep IB_WEB_SEARCH_API_KEY / IB_WEB_SEARCH_BASE_URL 于 src 无命中）</criterion>
      <criterion id="J-C PM 复跑零新增失败" result="SATISFIED">见 verification：pytest 1232 passed（前值 1232）；selfcheck 68/69（新增 4 例 PASS，唯一 FAIL 为既有环境性）；前端 build rc=0、160/160</criterion>
      <criterion id="J-C §N-2" result="SATISFIED">deepseek.py 端点/字段/状态码依据 P11-3 资料（已在 GR-B-003 核对的设计表）；无 module_design 出处表以外的 API 用法</criterion>
      <criterion id="J-C 凭据" result="SATISFIED">env.example 仅注释与键名，无值；deepseek.py 唯一日志为"lang ignored"警告，不含 Key；__repr__ 已覆盖</criterion>
      <criterion id="CR 统计" result="SATISFIED">新增 CR-015/016/017，CR-009 FIXED；MAJOR 遗留仍 3（CR-006/007/008）</criterion>
      <finding id="GR-C-003-F01" severity="MINOR">开发者修改了 test-engineer 编写的 2 个测试文件 3 个用例（075 钳制上限 10→50 随设计；091 删除随 base_url 消失的 2 条断言；223 改走 IB_LLM_API_KEY）并在一处用脚本批量替换；均登记于 implementation_plan 且与设计变更一致，但 223 覆盖面缩小（CR-016）——GROUP_D 须补 Key→请求头→不入日志的替身用例。</finding>
      <finding id="GR-C-003-F02" severity="MINOR">EgressDescriptor 无"禁止外发清单"字段，靠固定字段载荷 + 出站文本闸 + 审计先行约束（实现方 Q-4）；空检索词新增固定短语"检索词为空"（A-13b）。列入交付遗留，不阻塞。</finding>
      <condition>GROUP_D：覆盖 US-020 与 AC-001-04、010-08/09、014-06~10、015-07、016-09、017-06、018-05/06、020-01~03；DeepSeek 替身覆盖 200/空/400/401/402/403/404/408/413/429/500/504/超时/不可达，断言答复不暴露错误细节；Key→请求头且不入日志/异常/repr（CR-016）；fake 非离线启动失败只报键名；自动化测试禁止真实端点。</condition>
      <verification><![CDATA[$P -m compileall -q src -> ok
$P -m pytest tests -q -p no:cacheprovider -> 1232 passed in 54.54s
$P src/scripts/selfcheck.py -> 自检结果：68/69 通过（core_framework_free 既有）
(cd src/frontend && npm run build) -> rc=0 ; npm test -> # tests 160 # pass 160 # fail 0
git grep -n 'IB_WEB_SEARCH_API_KEY\|IB_WEB_SEARCH_BASE_URL' -- src -> 无输出]]></verification>
    </gate_review>
    <gate_review id="GR-C-004" invocation_id="intelligentbase-R28-GROUP_C-004" decision="PASS_WITH_CONDITIONS" time="2026-11-03T18:38:47+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/implementation_plan.md" version="3.1.0"/><file path="docs/sdlc/intelligentbase/code_review_report.md" version="3.1.0"/></reviewed_files>
      <criterion id="缺陷修复" result="SATISFIED">DEF-002（_run_dag_turn 顾问分支准备阶段异常 → ADVISOR_APOLOGY_TEXT）、DEF-004（egress.render_user_message 在 is_external 为 false 时不输出该键）、DEF-005（403/401/429 → "目标网站拒绝了访问"，其余 http_error → "该网页无可用内容"）、DEF-006（正文为空 → empty_content 失败）；DEF-003 按指令未修</criterion>
      <criterion id="只改实现" result="SATISFIED">tests/ 下无早于报告之后被修改的 .py（find -newer 无输出）</criterion>
      <criterion id="PM 复跑" result="SATISFIED">见 verification：2 failed / 1350 passed；418[intent] = DEF-003（预期）；344 = 测试与 DEF-004 目标冲突（以 [] 读 is_external，键已按 AC-017-06 移除），属测试需调整，非产品回归；418[prepare]/421/423/424 已转绿；selfcheck 68/69</criterion>
      <finding id="GR-C-004-F01" severity="MINOR">TC-INT-R28-344（tests/integration/test_advisor_http_int_r28.py:387）以下标读 search_knowledge.is_external，与 DEF-004 修复冲突；交 test-engineer 改为 .get（断言"非外部"语义不变，不构成放宽）。</finding>
      <finding id="GR-C-004-F02" severity="MINOR">[ASSUMPTION] 站点 429 归为"拒绝访问"短语（429 实为限流），设计未分类状态码；开发者用 sed 改文档头三行（已披露）。</finding>
      <verification><![CDATA[$P -m compileall -q src -> ok
$P -m pytest tests -q -p no:cacheprovider -> 2 failed, 1350 passed in 51.10s
  FAILED test_advisor_http_int_r28.py::test_TC_INT_R28_344_builder_digest_outbound_gains_only_tool_names_when_web_tools_registered
  FAILED test_deepseek_search_int_r28.py::test_TC_INT_R28_418_...[intent]
$P src/scripts/selfcheck.py -> 自检结果：68/69 通过]]></verification>
    </gate_review>
    <gate_review id="GR-D-002" invocation_id="intelligentbase-R28-GROUP_D-004" decision="PASS_WITH_CONDITIONS" time="2026-11-04T11:08:25+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/test_plan.md" version="1.2.0"/><file path="docs/sdlc/intelligentbase/unit_test_report.md" version="1.2.0"/><file path="docs/sdlc/intelligentbase/integration_test_report.md" version="1.2.0"/><file path="docs/sdlc/intelligentbase/e2e_test_report.md" version="1.2.0"/></reviewed_files>
      <criterion id="产出完整（会话中断后核实）" result="SATISFIED">D-004 的 agent_response 因会话中断未送达；PM 核实四份文档 1.2.0（2026-11-03T18:44:10~18:45:08），新/改测试文件 mtime 18:39:11~18:40:29 早于报告（冻结点成立）；新增 tests/e2e/test_advisor_deepseek_journeys_r28.py（TC-E2E-R28-013~015）；TC-INT-R28-344 改为 .get（tests/integration/test_advisor_http_int_r28.py:388，语义不变）；418[intent] 带 DEF-003-GUARD 冻结（test_deepseek_search_int_r28.py:713-718）</criterion>
      <criterion id="J-D PM 复跑一致" result="SATISFIED">见 verification：unit 805 / integration 469 / e2e 66 / agents 15 / 全量 1355 passed，collect-only 1355，与 e2e_test_report.md:68 一致；selfcheck 68/69；前端 build rc=0、160/160</criterion>
      <criterion id="J-D 基线判定" result="SATISFIED">原始基线 914 → 1355，零新增失败；DEF-001/002/004/005/006 FIXED/VERIFIED</criterion>
      <criterion id="J-D critical path" result="SATISFIED">Must 19/19 有 E2E 级用例（e2e_test_report.md:33），通过 15/15；待人工验证 16 项（MV-01~16）</criterion>
      <criterion id="防注水" result="SATISFIED">新测试文件无 skip/xfail/deselect；C-004 后无产品文件改动；零外网夹具 teardown 断言 socket 尝试 0</criterion>
      <finding id="GR-D-002-F01" severity="MAJOR">DEF-003 OPEN（理解步骤异常 fail-open 返回正常答复，与 REQ-FUNC-012(e1) 字面不符、与已接受设计 CR-008 一致），以缺陷冻结用例记录，待用户裁决；缺陷回流已用尽 2/2，若裁决为"改为致歉"需用户同意追加一轮回流。</finding>
      <finding id="GR-D-002-F02" severity="MINOR">16 项待人工验证（真实 DeepSeek 端点、真实 TLS/超时/代理、计费、真实 LLM 精准度、浏览器交互等），最终状态至多 DELIVERED_WITH_ISSUES。</finding>
      <condition>交付前：用户裁决 DEF-003；用户确认 PM 代答 CL-005（AQ6~AQ9）。</condition>
      <verification><![CDATA[P=/root/.venvs/intelligentbase/bin/python（离线环境变量同画像 P4）
pytest tests/unit -> 805 passed ; tests/integration -> 469 passed ; tests/e2e -> 66 passed ; tests/agents -> 15 passed
pytest tests -q -p no:cacheprovider -> 1355 passed in 51.58s ; --collect-only -> 1355 tests collected
selfcheck -> 自检结果：68/69 通过（core_framework_free 既有环境性）
(cd src/frontend && npm run build) -> rc=0 ; npm test -> # tests 160 # pass 160 # fail 0]]></verification>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="intelligentbase-R28-GROUP_E1-001" decision="PASS_WITH_CONDITIONS" time="2026-11-04T11:18:49+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/cicd_pipeline.md" version="0.1.0"/><file path="docs/sdlc/intelligentbase/deployment_plan.md" version="0.1.0"/><file path=".github/workflows/ci.yml" version="working tree"/></reviewed_files>
      <criterion id="J-E1 文档齐全" result="SATISFIED">两文档 0.1.0 DRAFT，timestamp 2026-11-04T11:12:54+08:00</criterion>
      <criterion id="J-E1 每个 DEPLOY 有 ROLLBACK" result="SATISFIED">DEPLOY-001~008 对应 ROLLBACK-000~009（DEPLOY-002 为只读闸，失败处置 ROLLBACK-001a→001b，deployment_plan.md:463）；009 撤销 ROLLBACK-009 标 [MANUAL_ROLLBACK_REQUIRED]；回滚不用 reset --hard / clean / 覆盖同步</criterion>
      <criterion id="J-E1 预检" result="SATISFIED">PRE-00~08：CI 全绿前置、目标机 HEAD 锚点、CLASS 门、venv lxml 版本、只读核查无 advisor 同名专家、Key 存在性只出计数</criterion>
      <criterion id="J-E1 环境与策略（P7）/ 禁用项（P8）" result="SATISFIED">仅 production、recreate、git pull；grep 无 scp/rsync/pscp/docker/staging/sudo -S/读取 env 值的可执行用法；env 变更由用户执行，只写键名</criterion>
      <criterion id="CI 改动（CR-006）" result="SATISFIED">git diff --stat ci.yml：+42/-1，仅"Schema / migration check"步骤与头注释；PM 抽出该步骤脚本原样执行：003/007/008/009 四行 PASS</criterion>
      <criterion id="部署后验证" result="SATISFIED">V-01~V-11 + MV-01~16 三阶段排期（联网全关 → OPT-A deepseek → OPT-B 抓取）</criterion>
      <finding id="GR-E1-001-F01" severity="MAJOR">回滚前置：旧代码对未知工具报 tool_grant_tool_unknown（PM 核实 src/ib/config/definition.py:528-533），含 web_search/web_fetch 授权的项目在回滚后无法加载——计划已设 ROLLBACK-000（先清除授权）并要求人工验证只在独立测试项目授权联网；用户须知悉。</finding>
      <finding id="GR-E1-001-F02" severity="MINOR">src/deploy/checklists.txt 无 009 对应的 [Bn] 项（devops 无写权，建议下一轮由 software-developer 追加 B30）；gh 标 [TOOL_UNREGISTERED]。</finding>
      <condition>E2 前：主会话 commit + push 本轮代码且 CI 全绿（PRE-00）；用户裁决 CP-004；部署须在主会话模式 claude --agent pm-orchestrator 中由用户本轮授权。</condition>
      <verification><![CDATA[git diff --stat -- .github/workflows/ci.yml -> 1 file changed, 42 insertions(+), 1 deletion(-)
抽出 ci.yml "Schema / migration check" run 脚本，PYTHONPATH=src 在 venv 下原样执行 ->
PASS: 003_accounts.sql ... / PASS: 007_folder_tree.sql ... / PASS: 008_config_versions.sql ... / PASS: 009_web_governance.sql syntax-ok / replay x2 idempotent / single-source / no executable DROP / old-db upgrade]]></verification>
    </gate_review>
    <gate_review id="GR-A-005" invocation_id="intelligentbase-R28-GROUP_A-005" decision="PASS" time="2026-11-04T14:33:09+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/requirements_spec.md" version="4.1.0"/><file path="docs/sdlc/intelligentbase/user_stories.md" version="4.1.0"/></reviewed_files>
      <criterion id="裁决落点" result="SATISFIED">REQ-FUNC-012 (e1) 收窄为委托编排与回合准备，理解步骤 fail-open 例外，来源 CL-006 Q1=A / D-08；AC-010-08 修订、AC-010-10 新增，均为 G/W/T；AC 总计 108；INFERRED 0</criterion>
    </gate_review>
    <gate_review id="GR-D-003" invocation_id="intelligentbase-R28-GROUP_D-005" decision="PASS_WITH_CONDITIONS" time="2026-11-04T14:40:43+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/test_plan.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/unit_test_report.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/integration_test_report.md" version="2.1.0"/><file path="docs/sdlc/intelligentbase/e2e_test_report.md" version="2.1.0"/></reviewed_files>
      <criterion id="DEF-003 翻转" result="SATISFIED">418 收窄为 prepare|orchestrate（AC-010-08 致歉断言保留）；新写 425[intent|resolve]（正常答复含"7 天"与《退换货政策》第 3 条，无致歉、无泄漏词，带成对正例）与 426（不可消解指代仍 200、不致歉）；grep -rn DEF-003-GUARD tests → 0；DEF-003 CLOSED（按用户裁决为设计行为）</criterion>
      <criterion id="PM 复跑一致" result="SATISFIED">见 verification；与报告 1358 一致，零新增失败；测试 mtime 14:33:56 早于文档 14:37:52</criterion>
      <criterion id="产品代码未改" result="SATISFIED">find src -newer code_review_report.md 无输出</criterion>
      <finding id="GR-D-003-F01" severity="MINOR">16 项待人工验证（MV-01~16），最终状态至多 DELIVERED_WITH_ISSUES。</finding>
      <verification><![CDATA[pytest tests/integration/test_deepseek_search_int_r28.py -k "418 or 425 or 426" -> 6 passed, 35 deselected
pytest tests -q -p no:cacheprovider -> 1358 passed in 50.87s ; --collect-only -> 1358 tests collected
selfcheck -> 自检结果：68/69 通过（core_framework_free 既有环境性）
(cd src/frontend && npm test) -> # tests 160 # pass 160 # fail 0
grep -rn DEF-003-GUARD tests | wc -l -> 0]]></verification>
    </gate_review>
    <gate_review id="GR-E1-002" invocation_id="intelligentbase-R28-GROUP_E1-002" decision="PASS_WITH_CONDITIONS" time="2026-11-04T14:42:25+08:00">
      <reviewed_files><file path="docs/sdlc/intelligentbase/deployment_plan.md" version="1.1.0"/><file path="docs/sdlc/intelligentbase/cicd_pipeline.md" version="1.1.0"/></reviewed_files>
      <criterion id="裁决落点（CL-006 Q3~Q7）" result="SATISFIED">DEPLOY-005 不执行（INCLUDE_WORKER_RESTART 缺省 false）；CLASS-E 先单独发布 ae07f44/47f19a3，DEPLOY-006 不同批；首发联网全关，DEPLOY-007 需主会话本轮单独授权，DEPLOY-008 本轮不启用；MV-15/16 破坏性分支推迟维护窗口（deployment_plan.md:354）；PRE-03 lxml 不符由用户 sudo 升级（U-9，:538）；B30 下一轮补</criterion>
      <criterion id="J-E1 其余标准" result="SATISFIED">沿用 GR-E1-001 已核对内容（回滚、预检、P7/P8）；ci.yml 未再改动（git diff --stat 仍 +42/-1）；测试基线 1358</criterion>
      <condition>E2 前：主会话 commit + push 且 CI 全绿（PRE-00）；部署须用户在主会话模式本轮授权；回滚前须先执行 ROLLBACK-000（清除联网工具授权）。</condition>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification id="CL-001" answered_by="用户（经主会话转述）" time="2026-11-02T21:01:12+08:00">CP-001 答复：Q1=A（确认 US-001~019，OQ/INF 按推荐，Q3 所涉 OQ-R28-02/03 除外）；Q2=A（笔误，默认面向客户的顾问角色）；Q5=A（REV-27 已收尾：主会话称 ae07f44/47f19a3 此前已在生产，8d6fd4b 今日已按用户要求部署到生产且仅前端改动；PM 未核验、未访问生产机，本流程未发出任何部署授权）。
Q3=自定义，用户原话「顾问 通过路由去把问题委托给kb-agent， kb-agent 处理后把结果给顾问agent汇总、整理措辞、格式。」→ 编排式委托（顾问 → 路由 → kb-agent 等 → 回到顾问汇总/润色/排版），替代推荐的 agent-as-tool；需修订 OQ-R28-02/03、US-006/009/010 及相关 AC。已知结构冲突（主会话转述）：图校验禁止环（graph_cycle）、同一专家只能对应一个 agent 节点（graph_agent_duplicate），"回到顾问"不能画成回边；交 GROUP_B 以 ADR 比较（前置/后置双角色节点 / 放开同专家多节点 / 顾问专属 aggregator 节点），保持 DAG 无环、现有项目逐位不变；顾问仍需能对通用问题直接联网作答。
Q4=A，用户不知选哪家，要求「尽量复用，不要重复造轮子」。主会话推荐（厂商待用户最终确认，架构不阻断）：首选博查 Bocha Web Search API，备选阿里云 IQS；不自建爬虫/搜索；提供方做成可替换适配器、默认关闭、密钥只经 /etc/intelligentbase/ib-web.env 注入；HTTP 客户端沿用 stdlib urllib 风格（参照 src/ib/embedding/__init__.py），不引入 langchain-community；web_fetch 正文抽取优先复用 lxml，新增依赖需在 tech_stack.md 论证。厂商价格等为主会话二手信息，PM 不作为已核实事实。</clarification>
    <clarification id="CL-002" answered_by="PM 记录（待用户补资料）" time="2026-11-02T21:01:12+08:00">画像 P11 待补项：P11-3 闭源 API——联网搜索服务（候选 Bocha Web Search API / 阿里云 IQS），需补：API 文档在仓库中的位置、端点/鉴权/字段/错误码/限流、测试替身（mock）。厂商未定、资料未入库前，GROUP_B 只定义项目自有的提供方无关适配器契约，任何厂商端点/字段映射不得设计（协议 §N），列为开放问题；画像本体暂不修改（须用户确认后 MINOR+1）。</clarification>
    <clarification id="CL-003" answered_by="用户（经主会话转述）" time="2026-11-02T21:47:27+08:00">CP-002 答复：Q1=A（认可架构，进入开发）；Q2=B（AQ1：顾问汇总失败或事实保真两次不过 → 统一致歉文本，不展示被委托 agent 原答；致歉文案须礼貌、不泄露内部分工与错误细节）——非推荐项，需修订需求 AC 与 ADR-R28-09；Q3=A（AQ2 历史与保留窗口一致 ≤20 条 / 约 8000 字符预算）；Q4=A（AQ3 联网工具全局登记）；Q5=A（AQ4 增设 IB_WEB_FETCH_ENABLED 缺省关闭）；Q6=A（AQ5 保留名 advisor + is_delegating）；Q7=C（本轮只做厂商无关搜索端口 + 离线替身，不对接真实厂商；P11-3 维持待补；用户另询 DeepSeek 是否有搜索服务，由主会话调研，厂商留到下一轮）。另：主会话要求修正 GR-B-001-F02（architecture_design.md:130 归属）与 F03（_require_admin 位于 views.py:1724）。范围：续跑 GROUP_C→GROUP_D，遇需用户裁决再停；不部署、不 commit。</clarification>
    <clarification id="CL-004" answered_by="用户（经主会话转述）" time="2026-11-03T17:26:22+08:00">CP-003 答复（用户原话「Q7 纳入。 Q6：A 其他推荐」）：Q1=A（联网结果不纳入保真守卫，先人工验证 MV-13）；Q2=A（接受 Builder 摘要多两个工具名）；Q3=A（fake 搜索提供方仅离线模式可用，本轮修复）；Q4=A（接受 A-12、A-12b：致歉固定中文）；Q5=A（OBS-1 登记下一轮）；Q6=A（进入 GROUP_E1，不部署）。另：CP-002 Q7 由 C 改为"本轮纳入"——接入 DeepSeek 官方 Search/Fetch API 作为搜索提供方；资料 docs/external_api/deepseek_search_fetch.md（主会话据官方页面整理，PM 未直接核对原页面），凭据复用现有 DeepSeek API Key（只写位置）。网页抓取方案（DeepSeek Fetch vs 本地抓取）由架构 ADR 评估决定；总开关缺省关闭与本地 netguard 均保留。新增范围回流 A→B→C→D，不占缺陷回流次数；随后 GROUP_E1（CI 含 009 检查 + 部署计划）；不部署、不 commit。</clarification>
    <clarification id="CL-005" answered_by="PM 代答，待用户确认" time="2026-11-03T17:49:46+08:00">架构待裁决题（NORMAL，子代理模式 PM 按最保守/改动最小代答）：AQ6=A（保留 region 字段但 DeepSeek 适配器忽略、不发送 IP 形态 localization，配置页加静态提示——避免外发终端地址）；AQ7=A（Key 轮换后与 LLM 一样需重启 ib-web 生效，不做热重载）；AQ8=A（本轮不重试，每次尝试计入每轮上限）；AQ9=A（保留本地 SafeFetcher 抓取，不用 DeepSeek Fetch）。交付状态因此至多 DELIVERED_WITH_ISSUES，最终汇报单列"待确认代答"。</clarification>
    <clarification id="CL-006" answered_by="用户（经主会话转述）" time="2026-11-04T14:31:25+08:00">CP-004 答复（用户原话「Q1: A, 其他按照推荐」）：Q1=A（DEF-003 保持 fail-open 照常作答，修订 AC-010-08 措辞只覆盖"委托编排和回合准备"，测试改正向断言并去掉 DEF-003-GUARD）；Q2=A（确认 CL-005：AQ6~AQ9 全部确认，CL-005 由"PM 代答待确认"转为用户确认）；Q3=A（不重启 ib-worker）；Q4=A（若目标机缺前序 ib-embed 提交，先单独发布）；Q5=A（首发联网全关，Stage 1 验证后开 DeepSeek 搜索，抓取暂不开）；Q6=A（只做无破坏部分，破坏性分支推迟维护窗口）；Q7=A（lxml 不符由用户 sudo 升级；B30 下一轮补）；Q8=A（主会话 commit + push，PM 不 commit）。另：主会话称 P11-3 资料已对照官方页面 https://api-docs.deepseek.com/guides/search 经 WebFetch 核对（2026-11-02/03），PM 记录此陈述、未独立核验。不部署。</clarification>
  </clarifications>
  <checkpoints>
    <checkpoint id="CP-001" time="2026-11-02T20:53:02+08:00" group="GROUP_A" reason="GROUP_A 已批准；按调用范围停在用户确认用户故事与开放问题之前" status="ANSWERED">
      <question id="Q1" blocking="true">是否确认 REV-28 用户故事 US-001~019（Must 18 / Should 1，104 点）并按推荐采纳 OQ-R28-01~12 与 INF-1~5？A) 全部按推荐确认，进入架构（推荐）；B) 按推荐确认，但改选部分 OQ（写明编号与选项）；C) 先调整故事范围（如把联网或运行期派发拆到下一轮）。</question>
      <question id="Q2" blocking="true">OQ-R28-01「默认是一个客户」：A) 笔误，意为默认面向客户的顾问/客服角色（推荐）；B) 顾问扮演客户，用于演练其他 agent；C) 使用者默认是客户，对内部员工另有口径。</question>
      <question id="Q3" blocking="true">OQ-R28-02 调用 kb-agent 的口径：A) agent-as-tool，顾问调用 kb-agent（推荐，贴合原话、KB 作答口径只一份）；B) 顾问直接用 search_knowledge；C) 仅在画布上串联顾问→kb-agent。</question>
      <question id="Q4" blocking="false">OQ-R28-07/08 生产出网与搜索服务：A) 可直接出网，用国内商业搜索 API，密钥放受控密钥文件（推荐，需告知厂商）；B) 经企业代理出网；C) 生产不能出网，联网部分暂不在生产启用。选定厂商后其 API 文档需补入画像 P11-3（闭源 API），再进入 GROUP_B。</question>
      <question id="Q5" blocking="false">REV-27 收尾：其 E2 部署未经本流程授权/记录，HEAD 另有 SDLC 外提交 ae07f44/47f19a3/8d6fd4b。A) 已在别处部署，按已收尾处理；B) 尚未部署，REV-28 完成后一起部署（推荐）；C) 先单独部署（须主会话 claude --agent pm-orchestrator 授权）。</question>
    </checkpoint>
    <checkpoint id="CP-002" time="2026-11-02T21:31:27+08:00" group="GROUP_B" reason="GROUP_B 已批准；按调用范围停在开发之前，架构待裁决题需用户决定" status="ANSWERED">
      <question id="Q1" blocking="true">是否认可架构方案并进入开发（GROUP_C）？要点：顾问为单个 agent 节点，放在被委托 agent 之后作汇聚点（唯一叶子），意图理解/问题改写为回合前置步骤；通用问题由 route 的"其他"分支直接交顾问联网作答；不新增节点类型、不放宽现有图校验，未启用项目零变化。A) 认可，进入开发（推荐）；B) 认可，但改选部分 AQ；C) 先调整方案（请说明）。</question>
      <question id="Q2" blocking="false">AQ1 顾问汇总失败或事实保真校验两次不通过时：A) 回退展示被委托 agent 原答（清洗内部标签），推荐；B) 统一道歉文案；C) 同 A 但前缀"以下为未经整理的资料"。</question>
      <question id="Q3" blocking="false">AQ2 顾问可见的会话历史：A) 与保留窗口一致（≤20 条，约 8000 字符预算从最旧处裁剪），推荐；B) 仅最近 6 条（与 REQ-FUNC-013 冲突）；C) 窗口可配置。</question>
      <question id="Q4" blocking="false">AQ3 web_search / web_fetch 出现在所有项目的"可授权工具"列表（不授权则无行为变化）：A) 接受，全局登记，推荐；B) 仅含顾问的项目列出；C) 仅已配置搜索提供方时登记。</question>
      <question id="Q5" blocking="false">AQ4 增设运维总开关 IB_WEB_FETCH_ENABLED（缺省关闭）：A) 增设，推荐（网页抓取面向任意公网主机，外发面大）；B) 不增设，随授权可用。</question>
      <question id="Q6" blocking="false">AQ5 顾问身份标记：A) 保留专家名 advisor + is_delegating=True，零 schema 变更（推荐；发布前运维核查生产无同名专家）；B) 新增专家字段 role（改序列化、语义哈希、前端 DTO）。</question>
      <question id="Q7" blocking="false">搜索厂商与画像 P11-3：A) 选博查 Bocha，并把其 API 文档（或官方文档链接存档）放入仓库，补画像 P11-3 后实现适配器（推荐）；B) 选阿里云 IQS，同上；C) 本轮只交付提供方无关端口 + 离线替身，厂商适配器下一轮再做。未补 P11-3 前 GROUP_C 一律按 C 执行。</question>
    </checkpoint>
    <checkpoint id="CP-003" time="2026-11-02T23:38:48+08:00" group="GROUP_D" reason="调用方范围 C→D 已完成；遗留设计取舍与下一步需用户决定" status="ANSWERED">
      <question id="Q1" blocking="false">CR-007 联网结果的数字/网址是否也纳入保真守卫：A) 维持现状，只靠提示词约束，先在目标机人工验证 MV-13 观察后再定（推荐：纳入后按 AQ1=B 会让大量联网回合误触发致歉）；B) 本轮纳入保护片段（需回流开发+测试）。</question>
      <question id="Q2" blocking="false">CR-010 Agent Builder 发给 LLM 的项目摘要对所有项目都多了 web_search/web_fetch 工具名（只有工具名，无业务数据）：A) 接受，视为 AQ3=A 的同类展示变化（推荐）；B) 改为仅启用顾问的项目才出现（需回流）。</question>
      <question id="Q3" blocking="false">CR-009 生产环境若把 IB_WEB_SEARCH_PROVIDER 设为 fake，会向客户返回替身结果：A) 本轮修复为仅离线模式可用 fake（推荐，改动小，需一次缺陷回流 2/2）；B) 不改，靠运维配置纪律，部署清单注明。</question>
      <question id="Q4" blocking="false">架构师两项延伸假设：A-12 顾问模式下其他未预期异常也返回同一致歉文本；A-12b 致歉文本固定中文、不随提问者语言变化（与 REQ-FUNC-002"用提问者语言作答"有出入）。A) 两项都接受（推荐，用户以中文为主）；B) 接受 A-12，A-12b 改为中英两版按提问语言选择（需回流）；C) 都不接受，请说明。</question>
      <question id="Q5" blocking="false">OBS-1（REV-26 既有问题，非本轮引入）：含停用专家的配置文档无法保存（versioning.py:375 报 prompt_orphan_expert）：A) 登记为下一轮缺陷单独处理（推荐）；B) 本轮一起修；C) 不处理。</question>
      <question id="Q6" blocking="true">下一步：A) 进入 GROUP_E1，产出 CI（追加 009 迁移检查）与部署计划，不执行部署（推荐）；B) 先按 e2e_test_report 人工验证清单 MV-01~13 在本地/目标机验收，再决定；C) 到此为止。另：提交由主会话在用户确认后执行（子代理不 commit）。</question>
    </checkpoint>
    <checkpoint id="CP-004" time="2026-11-04T11:18:49+08:00" group="GROUP_E1" reason="E1 已批准；存在 DEF-003 待裁决、PM 代答待确认与部署计划待裁决项" status="ANSWERED">
      <question id="Q1" blocking="true">DEF-003：顾问"理解步骤"（意图识别/问题改写）出现未预期异常时，目前是跳过理解、按原问句继续给出正常答复（fail-open，与已接受设计 CR-008 一致），而 REQ-FUNC-012(e1)/AC-010-08 字面要求返回致歉。A) 保留 fail-open，修订 AC-010-08 措辞为只覆盖"委托编排与回合准备"（推荐：用户仍能得到答复，改动最小）；B) 改为返回统一致歉（需用户同意追加第 3 轮缺陷回流，超过协议上限 2）；C) 其他。</question>
      <question id="Q2" blocking="false">确认 PM 代答 CL-005：AQ6=A 不向 DeepSeek 发送 IP 形态 localization，region 字段忽略并在配置页提示；AQ7=A Key 轮换后与 LLM 一样重启 ib-web 生效；AQ8=A 搜索失败不重试，每次尝试计入每轮上限；AQ9=A 保留本地网页抓取（DeepSeek Fetch 响应无最终网址，不满足 REQ-FUNC-017）。A) 全部确认；B) 改选（请写编号与选项）。</question>
      <question id="Q3" blocking="false">部署计划 Q1：本次发布是否重启 ib-worker？A) 不重启（推荐，设计结论无行为变化）；B) 一并重启。</question>
      <question id="Q4" blocking="false">部署计划 Q2：若预检发现目标机尚未部署前序 ib-embed 预热提交（CLASS-E）：A) 先单独发布该前序提交（推荐）；B) 同批授权重启 ib-embed；C) 接受磁盘代码领先进程。</question>
      <question id="Q5" blocking="false">部署计划 Q3：分阶段启用联网：A) 首发联网全关，Stage 1 人工验证后再启用 DeepSeek 搜索（OPT-A），网页抓取（OPT-B）暂不启用（推荐）；B) 首发即启用 DeepSeek 搜索；C) 搜索与抓取都启用（需先由用户配置出站 ACL）。</question>
      <question id="Q6" blocking="false">部署计划 Q4：MV-15（人为制造 429/402，会真实调用计费）与 MV-16 的"删除 Key 回退环境变量"分支（会临时移除生产 LLM Key）：A) 只做无破坏部分，破坏性分支推迟到维护窗口（推荐）；B) 全部执行；C) 不执行。</question>
      <question id="Q7" blocking="false">部署计划 Q5/Q6：A) venv 的 lxml 不满足 &gt;=5.0,&lt;7.0 时由用户在 sudo 会话中升级；checklists.txt 的 009 签署项 B30 下一轮由开发补（推荐）；B) 其他安排。</question>
      <question id="Q8" blocking="false">提交：A) 由主会话在用户确认后 commit + push（含 archive/rev27/、docs/external_api/、画像 1.1.0、REV-28 文档、产品代码、测试、ci.yml、agent 记忆），push 后看 CI（推荐，部署前置）；B) 仅 commit 不 push；C) 暂不提交。</question>
    </checkpoint>
  </checkpoints>
  <escalations></escalations>
  <audit_log>
    <event time="2026-11-02T20:45:55+08:00" type="RUN" actor="pm-orchestrator">运行模式=子代理模式。依据：第一条消息为调用方转述口吻（"用户原始需求（逐字）""我在本会话中已核实…""返回给我"），判定规则 2。已读 shared_protocol.md、project_profile.md、knowledge_base/generic/pm-orchestrator.md；项目记忆已注入。</event>
    <event time="2026-11-02T20:45:55+08:00" type="INVOCATION" actor="pm-orchestrator">REV-28 新建状态文件。REV-27 全部 16 个文档复制到 archive/rev27/（含原 phase_status.md）。注意：REV-27 的 E2 在原状态文件中为 NOT_AUTHORIZED、无 deployment_report 更新与 delivery_report；HEAD 另有 SDLC 外提交 ae07f44 / 47f19a3 / 8d6fd4b。归档不代表已部署。</event>
    <event time="2026-11-02T20:46:11+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（intelligentbase-R28-GROUP_A-001，PHASE_01,PHASE_02，REWORK_AUTHORIZED requirements_spec.md / user_stories.md，REV-27 版本已归档）。</event>
    <event time="2026-11-02T20:53:02+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS；requirements_spec / user_stories 0.1.0→1.0.0 APPROVED；收件箱已有 hook 记录（R28 前缀，1 条）。</event>
    <event time="2026-11-02T20:53:02+08:00" type="RUN" actor="pm-orchestrator">按调用范围写检查点 CP-001 并停止，不进入 GROUP_B；未改产品代码、未 commit。</event>
    <event time="2026-11-02T21:01:12+08:00" type="RUN" actor="pm-orchestrator">续跑（同一上下文，子代理模式；消息含 PM_MODE: subagent）：收到 CP-001 答复（经主会话转述），CP-001 改 ANSWERED，记 CL-001、CL-002。Q5 的部署陈述仅记录，不构成本流程部署授权（DEPLOY_AUTH 不适用）。Q3 改选 → GROUP_A 定向修订后再进 GROUP_B（PM §5 异常处理 6：需求变更影响最早 GROUP=A）。</event>
    <event time="2026-11-02T21:01:24+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（intelligentbase-R28-GROUP_A-002，定向修订 CL-001 Q3 / CL-002；REWORK_AUTHORIZED requirements_spec.md / user_stories.md，1.0.0→1.1.0 DRAFT；回流修订，不计 retries）。</event>
    <event time="2026-11-02T21:08:20+08:00" type="GATE" actor="pm-orchestrator">GR-A-002 PASS；requirements_spec / user_stories 1.1.0→2.0.0 APPROVED，1.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-02T21:08:20+08:00" type="INVOCATION" actor="pm-orchestrator">调用 system-architect（intelligentbase-R28-GROUP_B-001，PHASE_03,PHASE_04；REWORK_AUTHORIZED architecture_design / module_design / tech_stack，REV-27 版本在 archive/rev27/）。</event>
    <event time="2026-11-02T21:31:27+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS；architecture_design / module_design / tech_stack 0.1.0→1.0.0 APPROVED（REV-27 版本在 archive/rev27/）。收件箱已有 hook 记录（A-002 三条、B-001 三条）。</event>
    <event time="2026-11-02T21:31:27+08:00" type="RUN" actor="pm-orchestrator">按调用范围写检查点 CP-002 并停止，不进入 GROUP_C；未改产品代码、未 commit、未部署。</event>
    <event time="2026-11-02T21:47:27+08:00" type="RUN" actor="pm-orchestrator">续跑（子代理模式，消息含 PM_MODE: subagent）：CP-002 改 ANSWERED，记 CL-003。Q2=B 改选 → 先定向修订 GROUP_A（落 AC）与 GROUP_B（ADR-R28-09、AQ 裁决、F02/F03），再进 GROUP_C。测试环境：/root/.venvs/intelligentbase（pytest 9.1.1、lxml 6.1.3），Node v22.23.3。</event>
    <event time="2026-11-02T21:47:51+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（intelligentbase-R28-GROUP_A-003，定向修订 CL-003 Q2=B 等落点；REWORK_AUTHORIZED requirements_spec.md / user_stories.md，2.0.0→2.1.0 DRAFT）。</event>
    <event time="2026-11-02T21:49:07+08:00" type="BASELINE" actor="pm-orchestrator"><![CDATA[GROUP_C 前基线（HEAD 8d6fd4b，代码未改；venv /root/.venvs/intelligentbase，离线环境变量按画像 P4）：pytest tests -q -p no:cacheprovider -> 914 passed in 33.40s；selfcheck rc=1：57 PASS / 1 FAIL（core_framework_free：ib/core 引入 sitecustomize——来自系统 /usr/lib/python3.12/sitecustomize.py，环境性既有失败，非代码）；src/frontend npm test -> tests 141 pass 141 fail 0 skipped 0。]]></event>
    <event time="2026-11-02T21:50:28+08:00" type="GATE" actor="pm-orchestrator">GR-A-003 PASS；requirements_spec / user_stories 2.1.0→3.0.0 APPROVED，2.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-02T21:50:28+08:00" type="INVOCATION" actor="pm-orchestrator">调用 system-architect（intelligentbase-R28-GROUP_B-002，定向修订：AQ1~AQ5 裁决回写、ADR-R28-09 改统一致歉、GR-B-001-F02/F03、新增 AC 覆盖；REWORK_AUTHORIZED 三份架构文档 1.0.0→1.1.0）。</event>
    <event time="2026-11-02T21:56:01+08:00" type="GATE" actor="pm-orchestrator">GR-B-002 PASS_WITH_CONDITIONS；三份架构文档 1.1.0→2.0.0 APPROVED，1.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-02T21:56:01+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（intelligentbase-R28-GROUP_C-001，PHASE_05,PHASE_06；REWORK_AUTHORIZED implementation_plan / code_review_report，REV-27 版本在 archive/rev27/）。</event>
    <event time="2026-11-02T22:31:13+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS；implementation_plan / code_review_report 0.1.0→1.0.0 APPROVED（REV-27 版本在 archive/rev27/）。PM 复跑零新增失败。</event>
    <event time="2026-11-02T22:31:13+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（intelligentbase-R28-GROUP_D-001，PHASE_07,PHASE_08,PHASE_09；REWORK_AUTHORIZED 四份测试文档）。</event>
    <event time="2026-11-02T23:26:01+08:00" type="GATE" actor="pm-orchestrator"><![CDATA[GROUP_D-001 预核验（门控未结，待缺陷回流后定稿）：PM 复跑 unit 722 passed / integration 431 passed / e2e 63 passed / 全量 1231 passed（collect-only 1231），与报告一致；selfcheck 仅基线既有 core_framework_free 失败；新测试文件无 skip/xfail/deselect；git diff --stat -- src 32 files 1605+/79-，与 GROUP_C 后一致（产品代码未被测试工程师改动）。DEF-001（MINOR）PM 核实 src/ib/webtools/tools.py:300-302 `except WebBlocked: pass` 吞掉字节超限，属真实产品缺陷 → 缺陷回流 1/2（PM §5），调 GROUP_C 修复后再调 GROUP_D 翻转冻结用例 TC-UNIT-R28-085。]]></event>
    <event time="2026-11-02T23:26:01+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（intelligentbase-R28-GROUP_C-002，缺陷回流 1：DEF-001；REWORK_AUTHORIZED implementation_plan / code_review_report 1.0.0→1.1.0）。</event>
    <event time="2026-11-02T23:30:04+08:00" type="GATE" actor="pm-orchestrator">GR-C-002 PASS；implementation_plan / code_review_report 1.1.0→2.0.0 APPROVED，1.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-02T23:30:04+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（intelligentbase-R28-GROUP_D-002，缺陷回流 1：翻转 DEF-001 冻结用例并刷新四份测试文档 0.1.0→0.2.0）。</event>
    <event time="2026-11-02T23:38:48+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS_WITH_CONDITIONS；四份测试文档 0.2.0→1.0.0 APPROVED（REV-27 版本在 archive/rev27/）。DEF-001 FIXED/VERIFIED，缺陷回流 1/2。</event>
    <event time="2026-11-02T23:38:48+08:00" type="RUN" actor="pm-orchestrator">按调用方范围（C→D）停止，写检查点 CP-003；未调用 E1/E2，未部署、未 commit。</event>
    <event time="2026-11-03T17:26:22+08:00" type="RUN" actor="pm-orchestrator">续跑（子代理模式，消息含 PM_MODE: subagent；限流中断后恢复）：CP-003 改 ANSWERED，记 CL-004。</event>
    <event time="2026-11-03T17:26:22+08:00" type="INVOCATION" actor="pm-orchestrator">画像 1.0.0→1.1.0：按 PM §2（旧画像无 P11、本次需求出现闭源 API 信号）补入 P11（P11-1/P11-2 无；P11-3 DeepSeek Search/Fetch，资料 docs/external_api/deepseek_search_fetch.md，无沙箱、测试只用离线替身）。依据：用户「Q7 纳入」（经主会话转述）。资料中无凭据（PM 已通读，未发现注入类内容）。</event>
    <event time="2026-11-03T17:26:48+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（intelligentbase-R28-GROUP_A-004，新增范围：DeepSeek Search/Fetch 接入 + CL-004 落点；REWORK_AUTHORIZED requirements_spec / user_stories 3.0.0→3.1.0）。</event>
    <event time="2026-11-03T17:32:38+08:00" type="GATE" actor="pm-orchestrator">GR-A-004 PASS；requirements_spec / user_stories 3.1.0→4.0.0 APPROVED，3.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-03T17:32:38+08:00" type="INVOCATION" actor="pm-orchestrator">调用 system-architect（intelligentbase-R28-GROUP_B-003，新增范围：DeepSeek 搜索适配器 + 抓取方案 ADR + Q3 fake 仅离线；REWORK_AUTHORIZED 三份架构文档 2.0.0→2.1.0）。</event>
    <event time="2026-11-03T17:49:46+08:00" type="GATE" actor="pm-orchestrator">GR-B-003 PASS_WITH_CONDITIONS；三份架构文档 2.1.0→3.0.0 APPROVED，2.0.0 登记 SUPERSEDED。AQ6~AQ9 PM 代答（CL-005）。</event>
    <event time="2026-11-03T17:49:46+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（intelligentbase-R28-GROUP_C-003，新增范围：DeepSeek 搜索适配器、离线替身、Key 复用、fake 非离线启动失败、配置键调整；REWORK_AUTHORIZED implementation_plan / code_review_report 2.0.0→2.1.0；不计缺陷回流）。</event>
    <event time="2026-11-03T18:07:44+08:00" type="GATE" actor="pm-orchestrator">GR-C-003 PASS_WITH_CONDITIONS；implementation_plan / code_review_report 2.1.0→3.0.0 APPROVED，2.0.0 登记 SUPERSEDED；四份测试文档 1.0.0 因新增范围待重写，登记 SUPERSEDED。</event>
    <event time="2026-11-03T18:07:44+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（intelligentbase-R28-GROUP_D-003，新增范围测试；REWORK_AUTHORIZED 四份测试文档 1.0.0→1.1.0）。</event>
    <event time="2026-11-03T18:33:02+08:00" type="GATE" actor="pm-orchestrator"><![CDATA[GROUP_D-003 预核验：PM 复跑 unit 805 passed；integration 5 failed / 464 passed（失败仅 test_deepseek_search_int_r28.py 的 TC-INT-R28-418[intent]、418[prepare]、421、423、424），与报告一致；产品文件 mtime 均早于 D-003 开始（测试工程师未改产品代码）。E2E 按 §K 未执行。DEF-002/005/006（MAJOR）、DEF-004（MINOR）→ 缺陷回流 2/2；DEF-003（MINOR）与已接受设计 CR-008 及用户裁决 A-12 冲突，需用户裁决，本轮不修、用例改为缺陷冻结。]]></event>
    <event time="2026-11-03T18:33:02+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（intelligentbase-R28-GROUP_C-004，缺陷回流 2/2：DEF-002、DEF-004、DEF-005、DEF-006；REWORK_AUTHORIZED implementation_plan / code_review_report 3.0.0→3.1.0）。</event>
    <event time="2026-11-03T18:38:47+08:00" type="GATE" actor="pm-orchestrator">GR-C-004 PASS_WITH_CONDITIONS；implementation_plan / code_review_report 3.1.0→4.0.0 APPROVED，3.0.0 登记 SUPERSEDED。缺陷回流已用 2/2。</event>
    <event time="2026-11-03T18:38:47+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（intelligentbase-R28-GROUP_D-004：调整 TC-INT-R28-344、冻结 DEF-003 用例、补 E2E 并定稿四份测试文档 1.1.0→1.2.0）。</event>
    <event time="2026-11-04T11:08:25+08:00" type="RUN" actor="pm-orchestrator">续跑（新会话上下文，子代理模式，消息含 PM_MODE: subagent）：上次会话在 GROUP_D-004 运行中结束，agent_response 未送达；核实其产出已完整，不重做。</event>
    <event time="2026-11-04T11:08:25+08:00" type="GATE" actor="pm-orchestrator">GR-D-002 PASS_WITH_CONDITIONS；四份测试文档 1.2.0→2.0.0 APPROVED。DEF-003 OPEN 待用户裁决。</event>
    <event time="2026-11-04T11:08:25+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（intelligentbase-R28-GROUP_E1-001，PHASE_10,PHASE_11a；REWORK_AUTHORIZED cicd_pipeline / deployment_plan，并要求改 .github/workflows/ci.yml 追加 009 迁移检查（CR-006，module_design MOD-R28-16）；E2 NOT_AUTHORIZED）。</event>
    <event time="2026-11-04T11:18:49+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS_WITH_CONDITIONS；cicd_pipeline / deployment_plan 0.1.0→1.0.0 APPROVED（REV-27 版本在 archive/rev27/）；ci.yml 工作区改动已复核。</event>
    <event time="2026-11-04T11:18:49+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">子代理模式：流程止于 E1，不调用 E2；GROUP_E2 保持 NOT_AUTHORIZED。部署须用户在主会话模式（claude --agent pm-orchestrator）本轮授权。delivery_report 与 PHASE_12 蒸馏待 DEF-003 裁决、部署与人工验收后执行。</event>
    <event time="2026-11-04T11:18:49+08:00" type="RUN" actor="pm-orchestrator">写检查点 CP-004 并停止；未部署、未 commit。</event>
    <event time="2026-11-04T14:31:25+08:00" type="RUN" actor="pm-orchestrator">续跑（子代理模式，消息含 PM_MODE: subagent）：CP-004 改 ANSWERED，记 CL-006；CL-005 经用户确认。</event>
    <event time="2026-11-04T14:31:25+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（intelligentbase-R28-GROUP_A-005，定向修订 AC-010-08 / REQ-FUNC-012(e1)；REWORK_AUTHORIZED requirements_spec / user_stories 4.0.0→4.1.0）。</event>
    <event time="2026-11-04T14:33:09+08:00" type="GATE" actor="pm-orchestrator">GR-A-005 PASS；requirements_spec / user_stories 4.1.0→5.0.0 APPROVED，4.0.0 登记 SUPERSEDED；四份测试文档 2.0.0 因 DEF-003 翻转待改，登记 SUPERSEDED。</event>
    <event time="2026-11-04T14:33:09+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（intelligentbase-R28-GROUP_D-005：DEF-003 冻结用例翻转为正向断言（AC-010-10），去 DEF-003-GUARD；四份测试文档 2.0.0→2.1.0）。</event>
    <event time="2026-11-04T14:40:43+08:00" type="GATE" actor="pm-orchestrator">GR-D-003 PASS_WITH_CONDITIONS；四份测试文档 2.1.0→3.0.0 APPROVED；全部缺陷 FIXED/CLOSED，无 OPEN。</event>
    <event time="2026-11-04T14:40:43+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（intelligentbase-R28-GROUP_E1-002：把 CL-006 Q3~Q7 裁决落入 deployment_plan，1.0.0→1.1.0；cicd_pipeline 计数更新可选）。</event>
    <event time="2026-11-04T14:42:25+08:00" type="GATE" actor="pm-orchestrator">GR-E1-002 PASS_WITH_CONDITIONS；deployment_plan / cicd_pipeline 1.1.0→2.0.0 APPROVED，1.0.0 登记 SUPERSEDED。</event>
    <event time="2026-11-04T14:42:25+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">子代理模式：流程止于 E1，不调用 E2；GROUP_E2 保持 NOT_AUTHORIZED。commit/push 由主会话执行（Q8=A），PM 未 commit。delivery_report 与 PHASE_12 蒸馏待部署与人工验收（MV-01~16）后执行。</event>
    <event time="2026-11-04T14:42:25+08:00" type="RUN" actor="pm-orchestrator">本次运行结束：无 OPEN 检查点；已提供建议提交清单（112 个文件），凭据扫描未发现真实凭据（命中仅为检测正则与测试合成样本）。</event>
  </audit_log>
</phase_status>
