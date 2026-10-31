<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-10-31T09:41:01+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/archive/rev26/user_stories.md</file>
    <file>src/frontend/src/views/ConfigStudio.vue</file>
    <file>src/frontend/src/components/config/FlowCanvas.vue</file>
    <file>src/frontend/src/components/config/AgentDetailPanel.vue</file>
  </input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事（REV-27 增量）— 可视化配置：删除画布节点

**范围**：只写 REV-27 增量，承接 `requirements_spec.md`（同目录）的 REQ-FUNC-001~013 与 REQ-NFUNC-001~003。REV-26 的故事（US-001~030）归档于 `archive/rev26/user_stories.md`，只读；本文件的 US-001~011 编号空间独立，引用 R26 故事时写"R26 US-NNN"。
**角色**：沿用基线角色（集成开发者、运维账户用户、系统管理员、终端提问用户）；"查看 / 编辑 / 管理"是项目内权限档位，不是新角色。故事中"有编辑权限的账号"指被授予编辑档及以上者。本轮不新增角色。
**AC 书写口径**：Given / When / Then；界面文案用引号给出的示例即为期望文案。开放问题按推荐项书写（OQ-R27-01~10 均为非阻塞），用户改选时只需定向修订对应 AC。1 秒响应的目标机实测校准沿用 R26 INF-5，校准前该项标"未验收"。
**故事点**：输入中没有估算，均为相对估算 `[ESTIMATE]`（Fibonacci），供开发评估，不作为承诺。
**现状基线（用于 AC 的"变更前"对照）**：除 agent 外的节点没有删除入口；Delete 键只删边；"放弃改动"丢弃全部未保存内容（`FlowCanvas.vue:97,102`、`AgentDetailPanel.vue:189-193`、`ConfigStudio.vue:89-92`）。

## 角色 × 功能矩阵

| 角色 | 删除未完成节点 | 键盘删除 | 连带边与校验 | agent 两种移除 | 结构节点保护 | 撤销 | 差异确认 |
|---|---|---|---|---|---|---|---|
| 集成开发者 / 运维账户用户 / 系统管理员（编辑档及以上） | US-001 | US-002 | US-003、US-008 | US-005 | US-006 | US-009 | US-011 |
| 同上（查看档） | — （只读，US-007） | — （US-007） | — | — | — | — | — |
| 终端提问用户 | —（无感知，US-010：删除不影响线上） | — | — | — | — | — | — |

## 用户故事

### US-001: 直接删除一个尚未编辑完成的节点
- 故事：As a 集成开发者, I want to 在画布上删除我刚新增、还没编辑完整或没通过校验的节点（路由、agent、条件分支、汇聚、人工确认）, so that 我不必为了去掉一个节点而放弃本次编辑的所有其他改动。
- 关联需求：REQ-FUNC-001、REQ-FUNC-002、REQ-NFUNC-002；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-001-01：Given 编辑档账号，画布上已有 3 个本次新增、未保存的节点：条件分支 `condition-1`（分支键 a，关键词为默认占位值）、汇聚 `join-1`（无任何连线）、人工确认 `confirm-1`；以及 1 个已完成的改动（把 `kb-agent` 的最大步数改为 3） / When 选中 `condition-1`，在右侧详情面板点击"删除节点" / Then `condition-1` 从画布消失；`join-1`、`confirm-1` 仍在；`kb-agent` 的最大步数仍为 3；"未保存"标记仍显示；点击"保存并生效"弹出的差异清单中不含 `condition-1`
- AC-001-02：Given 同上 / When 对 `join-1`、`confirm-1`、再对一个新增的路由节点 `route-1` 依次执行"删除节点" / Then 三者均被删除，每次删除前后都不要求先修正其参数或先通过校验，页面不出现"请先修正校验错误"类拦截提示
- AC-001-03：Given 画布上新增了一个未选择工具、未填写提示词的 agent 节点（来自节点面板的 agent 按钮，对应一个已存在但此前未上图的 agent `faq-agent`） / When 选中它并点击"删除节点" / Then 节点从画布消失，不弹出任何校验错误（行为详见 US-005 对 agent 的语义）
- AC-001-04：Given 编辑档账号，画布上有节点但当前没有选中任何节点 / When 查看右侧详情面板 / Then 面板显示"点击画布上的节点查看或编辑其配置"，没有可点击的"删除节点"按钮

### US-002: 用 Delete 键删除选中的节点，且不会误删
- 故事：As a 集成开发者, I want to 选中节点后按 Delete 键删除它, so that 清理画布像删除连线一样快；同时在输入框里编辑文字时不会把节点误删。
- 关联需求：REQ-FUNC-003；优先级：Should Have；故事点：3 [ESTIMATE]（OQ-R27-05 推荐 A：仅 Delete 键）
- AC-002-01：Given 编辑档账号，画布上新增了无相连边的 `route-1` 且仅选中它，键盘焦点在画布上 / When 按 Delete 键 / Then `route-1` 被删除（按 US-004 规则无需确认），图在 1 秒内更新（`[INFERRED]` 阈值沿用 R26，校准前未验收）
- AC-002-02：Given 仅选中一条边（R26 AC-011-02 场景） / When 按 Delete 键 / Then 只删除该边，两端节点保留（继承行为不变）
- AC-002-03：Given 画布上选中了节点 `condition-1`，同时键盘焦点位于右侧面板的"关键词"文本框内，框中有文字 / When 按 Delete 键 / Then 仅删除文本框内光标后的字符；`condition-1` 仍在画布上，"未保存"状态不因节点被删而变化
- AC-002-04：Given 同时选中 2 个节点（如 `route-1` 与 `join-1`） / When 按 Delete 键 / Then 两个节点都不被删除，出现提示"请选中单个节点后再删除"
- AC-002-05：Given 编辑档账号，选中开始节点 / When 按 Delete 键 / Then 节点保留，提示"开始 / 结束节点不可删除"
- AC-002-06：Given 按下 Backspace 键（而非 Delete）且画布上有选中的节点 / When 按键 / Then 节点不被删除（Backspace 不是触发键）

### US-003: 删除节点时相连的边一并清理，校验问题留给保存时指出
- 故事：As a 集成开发者, I want to 删除节点时它的连线自动一起清掉、并且保存前仍会被告知图哪里不完整, so that 画布上不会留下指向空节点的悬空线，也不会因为删了一个节点就悄悄保存出一张跑不通的图。
- 关联需求：REQ-FUNC-004、REQ-FUNC-011；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-003-01：Given 画布上 `condition-1` 有 1 条入边（来自 `route-1`）和 2 条出边（分支键 a → `kb-agent`、"否则" → `end`） / When 删除 `condition-1`（按 US-004 确认） / Then 这 3 条边都从画布消失；画布上没有任何一端缺失节点的边；`route-1`、`kb-agent`、`end` 节点及其各自配置不变
- AC-003-02：Given 路由节点 `route-1` 有一条分支键为 `billing-agent` 的出边指向 agent `billing-agent` / When 将 `billing-agent` 节点按"仅从画布移除"移除 / Then 该出边（含分支键）随之消失，`route-1` 的其余出边与全局路由参数（tau、margin、max_expert_steps、default_expert）不变
- AC-003-03：Given 条件分支节点 `condition-1` 的分支 a 原本指向 `faq-agent`，删除 `faq-agent` 节点后 / When 点击"保存并生效" / Then 保存预检返回校验错误，错误项指出节点 `condition-1` 的分支键 a 没有目标，弹窗中列出该错误；不弹出"忽略并继续"选项；在用版本号不变
- AC-003-04：Given 删除了路由节点 `route-1`，使默认专家 `kb-agent` 从开始节点不可达 / When 点击"保存并生效" / Then 保存被拒绝，错误项指出"默认专家从开始节点不可达"，与 R26 AC-013-04 同口径
- AC-003-05：Given 图中原有一条错误"节点 `join-2` 从开始节点不可达" / When 删除 `join-2` 后再点击"保存并生效" / Then 返回的错误清单（或差异清单）中不再出现与 `join-2` 相关的任何一项

### US-004: 删除前的确认规则
- 故事：As a 集成开发者, I want to 删除有连线的、或线上已生效的节点时被确认一次，而刚加的空节点能直接删掉, so that 我既不会误删重要内容，也不会被无谓的弹窗打断。
- 关联需求：REQ-FUNC-005；优先级：Must Have；故事点：3 [ESTIMATE]（免确认例外为 `[INFERRED]`，OQ-R27-03 推荐 A）
- AC-004-01：Given 画布上有节点 `condition-1`，连有 2 条边 / When 点击"删除节点" / Then 出现确认框，文案含"将同时删除 2 条边"；此时节点与边仍在画布上
- AC-004-02：Given 确认框已出现 / When 点击"取消" / Then 节点与 2 条边仍在，"未保存"状态不变，草稿内容逐字段与确认前一致
- AC-004-03：Given 确认框已出现 / When 点击"确认" / Then 节点与 2 条边被删除，确认框关闭
- AC-004-04：Given 本次编辑中新增、尚未保存且没有任何连线的节点 `route-1` / When 点击"删除节点" / Then 不出现确认框，节点直接被删除
- AC-004-05：Given 一个已存在于当前生效版本、且没有任何连线的汇聚节点 `join-9` / When 点击"删除节点" / Then 出现确认框（文案不含边数，或标明"将删除 0 条边"），确认后才删除
- AC-004-06：Given 本次编辑中新增、尚未保存，但已连有 1 条边的节点 `confirm-1` / When 点击"删除节点" / Then 出现确认框，文案含"将同时删除 1 条边"

### US-005: agent 节点的两种移除：仅从画布移除 vs 删除 agent
- 故事：As a 集成开发者, I want to 清楚地选择"只把 agent 从图上拿掉"还是"连它的定义一起删除", so that 我可以放弃一个放错位置的 agent 节点而不丢掉它辛苦写的提示词，也能在确实不要时彻底删除它。
- 关联需求：REQ-FUNC-006、REQ-FUNC-010、REQ-FUNC-005；优先级：Must Have；故事点：5 [ESTIMATE]（OQ-R27-02 推荐 A；OQ-R27-07 推荐 A）
- AC-005-01：Given 项目有非默认 agent `billing-agent`（关键词"发票"、工具 `search_knowledge`、已编辑主提示词草稿"仅回答账单问题"），其节点在画布上并连有 2 条边 / When 选中该节点，点击通用"删除节点" / Then 节点与 2 条边从画布消失；`billing-agent` 的关键词、工具授权、主提示词草稿保留；"尚未上图的 agent"列表（点击节点面板的 agent 按钮时可选）中出现 `billing-agent`
- AC-005-02：Given AC-005-01 之后 / When 点击节点面板的 agent 按钮 / Then `billing-agent` 作为未连线的 agent 节点重新上图，其关键词、工具授权、主提示词仍是之前的值
- AC-005-03：Given AC-005-01 之后直接点击"保存并生效" / When 预检 / Then 差异清单显示节点与边的移除，不显示"删除 agent `billing-agent`"，`billing-agent` 的主提示词保存后仍存在于项目提示词目录
- AC-005-04：Given `billing-agent` 的节点被选中 / When 在 agent 详情面板点击"删除 agent" / Then 出现确认框，文案明确写出将移除该 agent 的定义与工具授权，并写出将同时删除的边数；文案中不出现与 R26 软删口径（历史会话仍可显示该 agent）相矛盾的承诺（OQ-R27-07 推荐 A，提示词文件处置的最终措辞待架构阶段核对后定稿）
- AC-005-05：Given AC-005-04 的确认框 / When 点击"确认" / Then `billing-agent` 的节点、相连边、专家条目、工具授权均消失；节点面板的"尚未上图的 agent"中不再出现它；历史会话中该 agent 的名称与标签仍可显示（R26 AC-005-01）
- AC-005-06：Given 通过 Agent Builder 加入画布、尚未保存的 agent `faq-agent`（草案含主提示词与兜底提示词，已写入提示词草稿） / When 在 agent 详情面板"删除 agent"并确认 / Then 节点、专家条目、工具授权消失；点击"保存并生效"的预检载荷与差异清单中不含 `faq-agent` 的任何字段，也不含其提示词；若除此之外无其他改动，"未保存"标记消失、"保存并生效"按钮禁用
- AC-005-07：Given 默认专家 `kb-agent` 的节点被选中 / When 查看面板 / Then "删除节点"与"删除 agent"均不可用（禁用），旁边提示"默认专家不能删除，请先指定其他默认专家"；通过 Delete 键触发同样被拒绝并给出同一提示

### US-006: 开始 / 结束节点不可删
- 故事：As a 集成开发者, I want to 画布上固定的开始和结束节点不会被我误删, so that 图始终有入口和出口。
- 关联需求：REQ-FUNC-007；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-006-01：Given 编辑档账号，选中开始节点 / When 查看右侧详情面板 / Then 面板中没有"删除节点"按钮（或按钮为禁用并说明"开始 / 结束节点不可删除"）
- AC-006-02：Given 选中结束节点 / When 按 Delete 键 / Then 节点保留，提示"开始 / 结束节点不可删除"；图与"未保存"状态不变
- AC-006-03：Given 画布上有路由节点 `route-1`（OQ-R27-06 推荐 A） / When 选中并"删除节点" / Then 路由节点可被删除（遵循 US-004 的确认规则）；删除后若默认专家不可达，在保存时才被拒绝（见 AC-003-04）

### US-007: 查看档账号不能删除节点
- 故事：As a 系统管理员, I want to 只读账号在配置页上完全无法删除节点, so that 只有被授权的人能改动编排。
- 关联需求：REQ-FUNC-008；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-007-01：Given 查看档账号，打开配置页 / When 点击任一节点 / Then 详情面板中没有"删除节点"与"删除 agent"按钮（不渲染或禁用），其他内容只读可见（沿用 R26 AC-010-01 口径）
- AC-007-02：Given 查看档账号，选中某节点 / When 按 Delete 键 / Then 节点保留，图与"未保存"状态不变（页面无未保存改动）
- AC-007-03：Given 查看档账号绕过界面直接向保存接口提交一份删除了某节点的配置 / When 请求到达服务端 / Then 返回 403，响应含所需权限名；在用版本号不变（继承 R26 AC-002-03 / AC-009-04 口径）

### US-008: 删除后画布、面板与"未保存"标记保持一致
- 故事：As a 集成开发者, I want to 删完节点后画布、右侧面板和"未保存"标记都立即反映真实状态, so that 我清楚当前草稿是什么、能不能保存。
- 关联需求：REQ-FUNC-009、REQ-NFUNC-001；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-008-01：Given 选中节点 `condition-1` 并且其悬停卡片正在显示 / When 删除该节点 / Then 1 秒内（`[INFERRED]` 阈值，沿用 R26 INF-5，校准前未验收）节点消失；悬停卡片消失；右侧详情面板显示"点击画布上的节点查看或编辑其配置"
- AC-008-02：Given 页面刚载入，无任何未保存改动，随后新增一个路由节点 `route-1`（"未保存"标记出现，保存按钮可用） / When 删除 `route-1` / Then "未保存"标记消失，"保存并生效"按钮禁用，"放弃改动"按钮禁用
- AC-008-03：Given 存在两处改动：新增 `route-1`、修改 `kb-agent` 的最大步数 / When 删除 `route-1` / Then "未保存"标记仍显示（因第二处改动仍在）；`kb-agent` 的最大步数改动保留
- AC-008-04：Given 删除后 / When 点击"放弃改动" / Then 图、面板、提示词回到服务端当前版本的样子，被删的已生效节点重新出现（放弃改动仍为整体回滚，行为不变）

### US-009: 误删后撤销最近一次删除
- 故事：As a 集成开发者, I want to 删错节点后一键撤销, so that 我不必因一次误删去放弃全部改动。
- 关联需求：REQ-FUNC-013；优先级：Should Have；故事点：3 [ESTIMATE]（`[INFERRED]`，OQ-R27-04 推荐 A）
- AC-009-01：Given 删除了含 2 条边的 `condition-1`（原位置 x=300、y=120，分支键 a） / When 点击撤销 / Then `condition-1` 回到画布，位置、类型、分支定义与删除前一致；2 条边回到原端点与原分支键；"未保存"标记按与基线的比较重新判定
- AC-009-02：Given 删除了 agent 定义 `billing-agent`（含工具授权与提示词草稿） / When 点击撤销 / Then 节点、相连边、专家条目、工具授权、提示词草稿全部恢复，点击"保存并生效"的预检载荷中包含它们
- AC-009-03：Given 删除后又做了任意一次其他编辑（如拖动另一个节点），或执行了保存、重新载入、放弃改动 / When 查看撤销入口 / Then 撤销入口不再可用（仅最近一次删除、且在下一次编辑前有效）
- AC-009-04：Given 连续删除了 `route-1`、再删 `join-1`，未做其他操作 / When 点击撤销 / Then 只恢复 `join-1`（最近一次）；`route-1` 保持已删除（不提供多步撤销）
- AC-009-05：Given 查看档账号 / When 查看页面 / Then 没有撤销入口

### US-010: 删除只改草稿，不影响线上，也不破坏既有功能
- 故事：As a 终端提问用户, I want to 配置人员在页面上删节点时我的提问不受影响, so that 只有他们确认保存后线上才变化；As a 集成开发者, I want to 其他画布功能不因这次改动而失效, so that 我的日常编辑照常工作。
- 关联需求：REQ-NFUNC-002、REQ-NFUNC-003；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-010-01：Given 当前版本号 N，线上有 agent `billing-agent` 的节点 / When 编辑者在页面删除该节点（未点击保存） / Then 在用版本号仍为 N；审计无新记录；项目提示词目录与定义文档文件哈希与删除前一致；此时终端用户提问含"发票"仍路由到 `billing-agent`
- AC-010-02：Given 同上，删除后点击"保存并生效"并在差异清单点击"取消" / When 查看状态 / Then 在用版本号仍为 N，草稿（含已删除状态）保留在页面上
- AC-010-03：Given 本轮改动完成 / When 在 `src/frontend` 运行 `npm run build && npm test` / Then 相对改动前基线零新增失败；既有用例（删边 R26 AC-011-02、Builder 加入画布 R26 AC-004-01、拖拽与悬停卡片）仍通过
- AC-010-04：Given 删除节点的草稿，点击"保存并生效"并确认成功 / When 保存返回 / Then 版本号变为 N+1，页面提示"已生效（版本 N+1）"，重新载入后该节点不再出现（保存流程与 R26 一致，不因本轮改变）

### US-011: 保存前的差异清单能看到被删的节点
- 故事：As a 集成开发者, I want to 保存前的差异清单明确列出我删掉的节点（不只是 agent）, so that 最后一道确认处我能看清到底删了什么。
- 关联需求：REQ-FUNC-012；优先级：Should Have；故事点：3 [ESTIMATE]（`[INFERRED]`）
- AC-011-01：Given 已生效版本含条件分支节点 `condition-9`（连有 2 条边）和 agent `kb-agent`；用户删除了 `condition-9` / When 点击"保存并生效" / Then 差异清单含 1 项"删除 条件分支节点：`condition-9`"以及其 2 条相连边的删除项（或"含 2 条边"的合并表述），可逐项核对；点击"确认"才提交
- AC-011-02：Given 用户新增了路由节点 `route-1` 又将其删除，无其他改动 / When 查看保存按钮 / Then 保存按钮禁用（无变更），不产生差异清单
- AC-011-03：Given 用户删除了已生效的汇聚节点 `join-9`，并新增了 1 个汇聚节点 `join-10` / When 点击"保存并生效" / Then 差异清单同时含"删除 汇聚节点：`join-9`"与"新增 汇聚节点：`join-10`"，两项互不混淆

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 8（US-001/003/004/005/006/007/008/010） | 26 [ESTIMATE] |
| Should Have | 3（US-002/009/011） | 9 [ESTIMATE] |
| **合计** | **11** | **35 [ESTIMATE]** |

- AC 总数：50 组 Given / When / Then（US-001 4、US-002 6、US-003 5、US-004 6、US-005 7、US-006 3、US-007 3、US-008 4、US-009 5、US-010 4、US-011 3；每个故事 ≥ 2 组，含正常路径与异常 / 权限 / 边界路径）。
- 需求覆盖：REQ-FUNC-001→US-001；002→US-001；003→US-002；004→US-003；005→US-004、US-005；006→US-005；007→US-006、US-005（默认专家）；008→US-007；009→US-008；010→US-005（AC-005-06）；011→US-003；012→US-011；013→US-009。REQ-NFUNC-001→US-008；002→US-010；003→US-010。
- 与 R26 的关系：未取代任何 R26 故事；R26 US-005（Should）的 AC-005-01/02/03 继续有效，本轮 US-004、US-005 在其基础上扩展确认规则和移除语义。
