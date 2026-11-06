<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-06T21:07:20+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/archive/rev28/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
  </input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事（REV-29 增量）— agent 工具调用的 MCP 适配

## 修订记录

| 版本 | 日期 | 变更摘要 | 依据 |
|---|---|---|---|
| 0.1.0 | 2026-11-05 | REV-29 初稿；REV-28 故事归档于 `archive/rev28/user_stories.md`（只读），本文件 US 编号空间独立 | requirements_spec 0.1.0 |
| 1.1.0 | 2026-11-05 | 定向修订（CP-001 用户裁决落地，其余逐字保留）：(1) **US-009（stdio）、US-022（HITL）移出本轮**，编号保留为"已移出（CP-001）"占位、不复用，其 AC 一并移出（AC-009-01~04、AC-022-01~03 作废）；(2) 工具名同步：授权 / 函数名处 `mcp.<server>.<tool>` → `mcp__<server>__<tool>`，展示处保留点号形式并注明是展示名（OQ-ARCH-R29-05=A）；(3) AC-020-02 计数口径改为"用户回合跨 agent 合计"（OQ-ARCH-R29-04=A）；(4) 新增 AC-001-06（stdio 等不支持的传输被拒）、AC-008-05（公网明文 http 被拒）、AC-027-07（链路本地 / 元数据地址即使在名单内也不放行），并补 AC-027-03 回环 / 私有 / CGNAT 正例；(5) AC-006-01 补主密钥不入库 / 未配置主密钥被拒；(6) 汇总与覆盖映射更新；故事 27 → 25 条有效 | requirements_spec 1.1.0；用户裁决（CP-001 Q1~Q5，经主会话转述）："全部按照推荐" |
| 2.1.0 | 2026-11-06 | 定向修订（REV-29 CP-002 用户裁决（经主会话转述，2026-11-06），其余逐字保留）：(1) CP-002 Q2=A：AC-027-01 "工具描述与返回内容均以围栏形式出现"改为与 ADR-R29-11 一致的分通道表述（返回内容围栏；工具 / 参数描述净化截断 ≤ 1000 / ≤ 300 字符、不加围栏）；(2) CP-002 Q3=A：AC-001-03 / 003-03 / 011-03 / 016-05 / 025-04 / 026-03 的"终端提问用户 / 终端用户"改为"匿名 → 401；view / edit 档越权 → 403"；(3) CP-002 Q4=A：仅记录，无对应 AC 变更。故事数、AC 数（113）、故事点不变；US-019 / US-023 中"终端用户提问"是对话提问者的业务角色，非登录主体，不属访问控制口径，保留 | requirements_spec 2.1.0；用户裁决（CP-002 Q2 / Q3 / Q4，经主会话转述）：「全部按推荐」 |

**范围**：承接同目录 `requirements_spec.md` 的有效 REQ-FUNC（001~024，其中 009、022 已移出本轮，共 22 条）与 REQ-NFUNC-001~013。
**角色**：沿用基线角色——系统管理员（admin）、项目配置者（项目内编辑档及以上账户）、终端提问用户（客户）；"评测与验收人"沿用 R28。**说明（2.1.0，CP-002 Q3=A）**："终端提问用户"仅指在对话中提问的业务角色（受益方），现有账户体系没有对应的独立登录主体（登录主体只有 admin 或项目绑定的 view / edit / manage 档），因此访问控制类 AC 一律按"匿名 → 401；view / edit 档越权 → 403"书写。"MCP Server"= 外部工具提供方；"外部工具"= 其发现的工具（带命名空间前缀）。
**AC 书写口径**：Given / When / Then；按需求文档的推荐项书写（OQ-R29-02=A、04=A、05=A、06=A、07=A、09=停用+C、10=A）；这些选项及 OQ-R29-01=B 已全部由用户裁决（CP-001，经主会话转述，原话"全部按照推荐"），不再待确认。"替身 Server"= 离线测试用的 MCP Server 替身（C-R29-04）。**工具名口径**（OQ-ARCH-R29-05=A）：授权、函数调用、定义文档、保存校验涉及的名称为注册名 `mcp__<server>__<tool>`；点号形式 `mcp.<server>.<tool>` 只是展示名（管理页、审计、查询结果中的展示字段），AC 中凡断言展示字段处明确写"展示名"。
**故事点**：输入中没有估算，均为相对估算 `[ESTIMATE]`（Fibonacci），供开发评估，不作为承诺。**来源**：用户原文 / 调用方转述 / 基线 B# 见各故事。安全类故事均含负例 AC（越权、跨项目、注入、凭证泄露、未复审即调用等）。

## 角色 × 功能矩阵

| 角色 | Server 生命周期 | 工具生命周期 | 授权 | 调用与治理 | 安全与审计验收 |
|---|---|---|---|---|---|
| 系统管理员 | US-001~US-008（US-009 已移出） | US-010~US-015 | US-018（放行）、US-021 | US-020（全局默认）、US-024 | US-025、US-026 |
| 项目配置者（编辑档及以上） | US-003（只读，限本项目可见） | US-011（只读，限本项目可见） | US-016、US-017、US-021（收到拒绝） | US-020（只能调低） | — |
| 终端提问用户（客户） | —（无感知） | — | — | US-019、US-023（受益 / 参与方；US-022 已移出） | US-027（受益方） |
| 评测与验收人 | — | — | — | — | US-025、US-026、US-027 |

## 用户故事

### US-001: 登记 MCP Server
- 故事：As a 系统管理员, I want to 登记一个 MCP Server（名称、说明、传输、连接目标、鉴权、外发数据类别、可用范围）, so that 平台能把它提供的工具纳入受控管理。
- 来源：用户原文「增加，变更，删除，查询新工具」；调用方转述（管理员登记 Server）
- 关联需求：REQ-FUNC-001；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-001-01：Given admin 打开 MCP 管理页 / When 提交唯一标识名、说明、传输类型"远程 HTTP"、合法的连接目标、鉴权方式"静态令牌"及令牌、数据类别声明 / Then 返回成功；Server 列表出现该条，状态为"未启用"；其工具数为 0；令牌显示为"已设置"而不显示明文；写入一条审计（操作者、时间、Server 标识名、动作"登记"，不含令牌）。
- AC-001-02：Given 已存在标识名为 `crm` 的 Server / When admin 再次登记标识名 `crm` / Then 返回 400 及错误"标识名已存在"，不创建；原 Server 不变。
- AC-001-03：Given 非 admin 主体（项目 view 档账户、项目 edit 档及以上的项目配置者、匿名） / When 请求登记 Server / Then view 档与 edit 档账户返回 403、匿名返回 401；Server 列表不变；审计中无"登记"记录。
- AC-001-04：Given admin 登记时缺少必填项（连接目标为空或标识名含空格 / 非法字符） / When 提交 / Then 返回 400，错误逐条指出字段名与原因；不落库。
- AC-001-05：Given 登记成功的 Server 处于"未启用" / When 项目配置者尝试在授权页勾选该 Server 的任意工具 / Then 该工具不可选（列表中不出现），直接以接口提交时被拒并返回逐条错误。
- AC-001-06：Given admin 登记时选择"本机子进程（stdio）"或其他非远程 HTTP 的传输类型（本轮不支持，OOS-R29-11） / When 提交 / Then 返回 400，错误"传输类型不受支持"；不落库；平台未启动任何子进程（进程数增量 = 0）；传输类型下拉中不出现 stdio 选项。

### US-002: 连接验证与能力协商
- 故事：As a 系统管理员, I want to 在登记、变更和"测试连接"时让平台与 Server 完成协议握手并看到协商结果, so that 只有可正常工作的 Server 才能被启用。
- 来源：用户原文「对标mcp 的业务流程」；调用方转述（initialize 能力协商）；`[WEB: https://modelcontextprotocol.io/specification/latest/server/tools，2026-11-05]`
- 关联需求：REQ-FUNC-002；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-002-01：Given 替身 Server 声明支持工具能力与变更通知 / When admin 点击"测试连接" / Then 页面显示"连接成功"，并展示协商出的协议版本、是否支持工具能力、是否支持变更通知；记录最近验证时间；该 Server 可被启用。
- AC-002-02：Given 替身 Server 分别模拟：不可达、握手超时、鉴权失败（401）、协议版本不兼容、未声明工具能力 / When 分别测试连接 / Then 每种情形返回的原因类别依次为"不可达""超时""鉴权失败""协议不兼容""无工具能力"；响应中凭证、内网主机名、堆栈出现次数 = 0；"启用"按钮不可用 / 启用请求被拒。
- AC-002-03：Given 连接目标指向 `http://169.254.169.254/` / When 测试连接 / Then 在发出任何出站请求之前被拒，原因类别"地址被拒"，替身记录的请求数 = 0（REQ-NFUNC-004）。

### US-003: 查询 MCP Server
- 故事：As a 系统管理员, I want to 查看 Server 列表与详情（状态、最近连接、工具数、被谁引用）, so that 我掌握所有外部连接的现状与影响面。
- 来源：用户原文「查询新工具」；调用方转述；基线 B14
- 关联需求：REQ-FUNC-003；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-003-01：Given 已有 3 个 Server（状态分别为可用、不可用、已停用） / When admin 打开列表 / Then 每行显示标识名、传输类型、鉴权方式、状态、最近连接结果与时间、按状态分计的工具数、授权引用的项目数与 agent 数；任何位置不出现凭证明文（只有"已设置 / 未设置"与最近轮换时间）。
- AC-003-02：Given 项目 P 仅被开放了 Server `crm` / When P 的项目配置者查询 Server 列表 / Then 只返回 `crm`，且不含连接目标之外的凭证信息；其他 Server 的标识名与存在性均不可见（直接按标识名请求其详情返回 404）。
- AC-003-03：Given 匿名请求 Server 列表，或项目 view / edit 档账户请求 Server 的登记 / 变更 / 停用 / 删除等管理动作 / When 请求 / Then 匿名返回 401、view / edit 档管理动作返回 403，Server 数据无任何变化；view / edit 档账户读取列表时仅返回开放给本项目的 Server（同 AC-003-02）。

### US-004: 变更 MCP Server
- 故事：As a 系统管理员, I want to 修改 Server 的说明、连接目标、鉴权和治理参数, so that 能随外部服务变化维护连接而不失控。
- 来源：用户原文「变更」；调用方转述（schema 变更后重新审核）
- 关联需求：REQ-FUNC-004；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-004-01：Given Server 下有 4 个"已启用"工具 / When admin 只修改说明与超时参数 / Then 保存成功；4 个工具仍为"已启用"；审计记录变更前 → 变更后。
- AC-004-02：Given 同上 / When admin 修改连接目标为另一个合法地址 / Then Server 状态变为"待验证"，4 个工具全部转"待复审"，复审通过前对它们的调用次数 = 0（替身收到请求数 = 0）；页面提示"连接目标变更，工具需重新审核"。
- AC-004-03：Given admin 把连接目标改为私有地址（如 `http://10.0.0.5/`，允许名单为空） / When 保存 / Then 返回 400，原因"地址被拒"；原连接目标不变；工具状态不变。
- AC-004-04：Given 项目配置者 / When 修改任一 Server / Then 返回 403，Server 不变。
- AC-004-05：Given admin 变更鉴权凭证 / When 保存后查询详情 / Then 详情只显示"已设置"与更新后的轮换时间；审计记录中凭证值出现次数 = 0。

### US-005: 停用、启用与删除 MCP Server
- 故事：As a 系统管理员, I want to 可逆地停用、启用，并在确认影响后删除 Server, so that 下线外部服务时不留悬空授权、不影响其他配置。
- 来源：用户原文「删除」；调用方转述（删除 Server 后已授权 agent 的处理）；基线 B3
- 关联需求：REQ-FUNC-005；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-005-01：Given Server `crm` 的 2 个工具已授权给项目 P 的 kb-agent / When admin 停用 `crm` / Then 两个工具的下一次调用立即降级（替身收到请求数 = 0）；P 的授权记录仍在，配置页标注"Server 已停用"；P 的配置保存不因此失败。
- AC-005-02：Given `crm` 已停用 / When admin 启用 / Then 状态先变"待验证"，连接验证通过后才恢复"可用"；验证失败则保持不可用且授权不恢复生效。
- AC-005-03：Given `crm` 仍被项目 P 的授权引用 / When admin 请求删除 / Then 默认被拒，响应列出引用的项目与 agent；`crm` 及其工具、授权不变。
- AC-005-04：Given 同上，admin 选择"强制删除并清理授权"并二次确认 / When 提交 / Then `crm`、其工具、其凭证被清除（凭证事后不可取回）；P 的定义文档新增一条变更记录，其中 `crm` 的授权已移除；P 的配置仍可正常保存；审计与历史调用记录保留可查。
- AC-005-05：Given 删除完成后 / When 任意 agent 尝试调用原 `mcp__crm__*` 工具 / Then 返回降级结果"该能力已下线"，替身收到请求数 = 0；非 admin 请求删除返回 403。
- AC-005-06：Given 删除未二次确认（请求缺少确认标志） / When 提交 / Then 返回 400，不删除。

### US-006: 托管 MCP Server 凭证
- 故事：As a 系统管理员, I want to 安全保管并轮换 Server 凭证（平台共享或项目专属）, so that 凭证不泄露且各项目互不借用。
- 来源：调用方转述（凭证按项目隔离或由平台注入；不明文存储）；画像 P6、P8
- 关联需求：REQ-FUNC-006、REQ-NFUNC-005；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-006-01：Given 植入 canary 凭证串 / When 依次完成登记、查询、调用、变更、删除 / Then 日志、审计、所有 API 响应、定义文档、发往 LLM 的载荷中 canary 命中数 = 0；落盘介质中以明文形式命中数 = 0；凭证为加密存放，主密钥在仓库与台账中的命中数 = 0（CP-001 Q5=A）。
- AC-006-02：Given Server 配置为"项目专属凭证"，项目 A 已设置、项目 B 未设置 / When B 的 agent 调用该 Server 的工具 / Then 返回降级结果"凭证缺失"；替身收到的请求数 = 0；A 的凭证、平台共享凭证被用于 B 的次数 = 0。
- AC-006-03：Given admin 轮换凭证 / When 轮换完成后发起调用 / Then 替身收到的请求使用新凭证，旧凭证不再被使用；详情显示新的轮换时间。
- AC-006-04：Given 任何调用方（含 admin） / When 通过任何查询接口读取凭证 / Then 响应中不含凭证值，只含"已设置 / 未设置"；仓库 `selfcheck` 凭证扫描零命中。
- AC-006-06：Given 部署环境未配置凭证主密钥 / When admin 登记带凭证的 Server 或轮换凭证 / Then 请求被拒并返回明确原因"凭证主密钥未配置"；凭证未以明文落盘（明文命中数 = 0）；不带凭证的 Server 登记不受影响。
- AC-006-05：Given 凭证配置错误导致 Server 返回 401 / When agent 调用 / Then 降级文案不包含状态码数字、服务方错误原文与凭证片段；审计记录降级原因类别为"鉴权失败"。

### US-007: 控制 Server 的项目可见范围
- 故事：As a 系统管理员, I want to 决定每个 Server 对哪些项目开放, so that 外部服务不会越过项目边界被使用。
- 来源：调用方转述（项目 / 租户隔离）；基线 B2、B5；记忆 M-PM-010（运行期新建项目以项目台账为准）
- 关联需求：REQ-FUNC-007、REQ-NFUNC-002；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-007-01：Given 平台级 Server `crm` 新登记 / When 未开放给任何项目 / Then 任一项目的配置页均看不到 `crm` 及其工具；各项目 agent 的函数调用工具列表中 `mcp__crm__*` 出现次数 = 0。
- AC-007-02：Given admin 将 `crm` 开放给项目 A / When A 的项目配置者打开授权页 / Then 看到 `crm` 下"已启用"的工具；项目 B 仍看不到；B 的 agent 直接调用 `mcp__crm__*` 的成功次数 = 0（含运行期新建的项目，N≥1 个）。
- AC-007-03：Given 项目专属 Server `erp` 属于 A / When B 的 admin 以外账号请求查询 / 授权 / 调用 `erp` / Then 查询返回 404 或空，授权保存被拒，调用被拒；`erp` 的任何信息不出现在 B 的页面与响应中。
- AC-007-04：Given `crm` 已授权给 A 的 agent / When admin 取消对 A 的开放 / Then A 对 `crm` 的授权在其后的调用上立即不生效（替身请求数 = 0），配置页标注"Server 未对本项目开放"，A 的配置保存不失败。
- AC-007-05：Given 新建项目（含启用顾问） / When 创建完成 / Then 该项目未开放任何 Server。

### US-008: 连接远程 MCP Server（HTTP 类）
- 故事：As a 系统管理员, I want to 连接用 HTTP 提供服务的远程 MCP Server 并使用静态令牌鉴权, so that 常见的远程工具服务可以接入。
- 来源：调用方转述（传输：Streamable HTTP）；`[WEB: https://modelcontextprotocol.io/specification/latest/basic/transports，2026-11-05]`
- 关联需求：REQ-FUNC-008；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-008-01：Given 替身远程 Server 要求 Bearer 令牌 / When 以正确令牌登记并连接验证 / Then 验证成功，替身记录的请求带有 Bearer 头；令牌不出现在 URL 查询串中（出现次数 = 0）。
- AC-008-02：Given 连接目标为 `http://user:pass@host/` 或 `file:///etc/passwd` 或非 http(s) 协议 / When 登记或变更 / Then 返回 400 原因"地址被拒"，替身请求数 = 0。
- AC-008-03：Given 替身 Server 在连接过程中返回 302 重定向到私有地址 / When 连接验证或调用 / Then 重定向不被跟随，结果为"地址被拒"；私有地址侧请求数 = 0。
- AC-008-04：Given 本轮仅支持静态令牌（OQ-R29-03=A） / When admin 选择 OAuth 授权码鉴权 / Then 该选项不可选；以接口提交时返回 400 "鉴权方式不受支持"。
- AC-008-05：Given 连接目标为公网主机的 `http://`（明文）地址，且不在内网允许名单内（OQ-ARCH-R29-07=A） / When 登记、变更、测试连接或调用 / Then 返回 400 原因"公网目标禁止明文 http"，替身请求数 = 0；When 改为同一主机的 `https://` 地址 / Then 可通过地址校验；When 目标为内网允许名单内的精确主机 + 端口且使用 `http://` / Then 可通过地址校验（明文仅限名单内目标）。

### US-009: 本机子进程（stdio）Server（已移出）
- **【已移出（CP-001）】** 本机子进程（stdio）本轮不做（用户裁决 CP-001 Q2=A，OQ-R29-02=A，经主会话转述），对应 REQ-FUNC-009 已移入超出范围 OOS-R29-11；US-009 编号保留为占位、不复用，原 AC-009-01~04 作废、不再验收；不计入故事数、AC 数与故事点。"stdio 请求被拒"的行为由 AC-001-06 承接。

### US-010: 发现外部工具并加命名空间前缀
- 故事：As a 系统管理员, I want to 让平台从已启用的 Server 获取工具清单，并以带前缀的唯一名称呈现, so that 新工具能被发现且不与内置工具冲突。
- 来源：用户原文「增加…新工具」；调用方转述（命名空间前缀防冲突）；基线 B1
- 关联需求：REQ-FUNC-010；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-010-01：Given 替身 Server `crm` 提供 3 个工具（`search`、`get`、`update`），清单分 2 页返回 / When Server 启用并首次发现 / Then 工具目录出现 3 条，注册名（= 授权名 = LLM 可见函数名）为 `mcp__crm__search`、`mcp__crm__get`、`mcp__crm__update`，展示名分别为 `mcp.crm.search`、`mcp.crm.get`、`mcp.crm.update`（仅管理页 / 审计 / 查询结果的展示字段），状态均为"待审核"；每条记录含描述原文、入参 schema、服务方注解、发现时间、指纹。
- AC-010-02：Given 另一 Server `kb` 也提供名为 `search` 的工具，且某 Server 提供名为 `search_knowledge` 的工具 / When 发现 / Then 注册名 `mcp__kb__search` 与 `mcp__crm__search` 并存互不覆盖；名为 `search_knowledge` 的外部工具注册名为 `mcp__<server>__search_knowledge`（展示名 `mcp.<server>.search_knowledge`），内置 `search_knowledge` 的行为、描述、授权不变（逐项一致）。
- AC-010-03：Given 某 Server 自报名称为 `search_knowledge` 或与已有标识名相同 / When 发现 / Then 命名空间仍只用平台登记的标识名（注册名仍以 `mcp__<登记标识名>__` 开头），内置工具未被遮蔽。
- AC-010-04：Given 清单中有 1 个名称含非法字符 / 超长的工具和 9 个合规工具 / When 发现 / Then 非法工具被排除，目录中出现"已排除"记录（含原因）；9 个合规工具正常入目录。

### US-011: 查询外部工具目录
- 故事：As a 项目配置者 / 系统管理员, I want to 按 Server、状态、风险筛选并查看外部工具详情与引用, so that 我知道有哪些工具、是否安全、被谁使用。
- 来源：用户原文「查询新工具」；基线 B14
- 关联需求：REQ-FUNC-011；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-011-01：Given 目录中有"待审核 / 已启用 / 待复审 / 已下线"各状态工具 / When admin 按状态"待复审"筛选 / Then 只返回待复审的工具；详情显示名称、描述原文、schema、注解（标"服务方自报，未经核实"）、风险级别、授权引用、近期调用次数 / 失败率 / 平均耗时。
- AC-011-02：Given 项目 A 的项目配置者 / When 查询工具目录 / Then 只返回开放给 A 的 Server 下的工具；其他 Server 的工具数量与名称均不出现（N≥3 个未开放 Server 的夹具中泄露条数 = 0）。
- AC-011-03：Given 匿名请求工具目录，或项目 view / edit 档账户请求工具的审核 / 启用 / 风险裁定等管理动作 / When 请求 / Then 匿名返回 401、view / edit 档管理动作返回 403，工具状态无任何变化；view / edit 档读取目录时仅返回开放给本项目的工具（同 AC-011-02）。

### US-012: 审核、启用并为外部工具定风险级别
- 故事：As a 系统管理员, I want to 逐个审核新工具的描述、schema 与注解，裁定风险级别并启用, so that 只有我认可的工具才可能被授权。
- 来源：用户原文「增加，变更，删除，查询新工具」；调用方转述（审核 / 启用；readOnly / destructive 注解）
- 关联需求：REQ-FUNC-012；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-012-01：Given 工具 `mcp__crm__search`（展示名 `mcp.crm.search`）注解自称只读 / When admin 打开审核 / Then 页面并列显示描述原文、入参 schema、服务方注解，初始风险级别为"未知"（不因注解自称只读而预设为只读）；admin 裁定为"只读"并启用后，状态为"已启用"，审计记录裁定人、级别、审核时的内容指纹。
- AC-012-02：Given 工具注解自称"破坏性" / When admin 查看 / Then 初始风险级别为"有副作用"或"未知"（不为"只读"）。
- AC-012-03：Given 工具处于"待审核" / When 项目配置者尝试启用该工具或把它授权给 agent / Then 启用请求返回 403；授权保存被拒并逐条报错"工具未启用"。
- AC-012-04：Given admin 禁用一个已启用工具 / When 随后 agent 调用它 / Then 调用被拒（替身请求数 = 0），结果为降级"工具已禁用"。

### US-013: 感知工具变更并复审
- 故事：As a 系统管理员, I want to 在 Server 的工具清单、描述或 schema 变化时被发现并复审后才放行, so that 不会被事后更换内容的工具（rug-pull）攻击。
- 来源：调用方转述（notifications/tools/list_changed、rug-pull、重新审核与授权失效）；`[WEB: https://modelcontextprotocol.io/specification/latest/server/tools，2026-11-05]`
- 关联需求：REQ-FUNC-013、REQ-NFUNC-010；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-013-01：Given 工具 `mcp__crm__get` 已启用并授权给项目 A 的 kb-agent / When 替身 Server 发出清单变更通知，且 `get` 的描述被改为含新指令的文本 / Then 系统重新获取清单并比对指纹，`mcp__crm__get` 转"待复审"；此后 kb-agent 对它的调用被拒（替身收到 `get` 调用数 = 0）；管理员可查看差异清单（变更前 → 变更后）。
- AC-013-02：Given Server 不支持变更通知 / When admin 手动"刷新"或 Server 重连 / Then 同样检出描述 / schema / 注解变化并转"待复审"；不依赖通知是唯一途径。
- AC-013-03：Given 变更仅为 `get` 的注解由"只读"改为"破坏性" / When 刷新 / Then 仍转"待复审"（任一指纹变化均失效）。
- AC-013-04：Given 复审中 admin 审核通过 / When 完成 / Then 状态回"已启用"，绑定新指纹；原授权按 OQ-R29-07=A 自动恢复，下一次调用成功；admin 选择不通过则保持待复审，授权保持失效。
- AC-013-05：Given 变更检测完成的同一时刻另一请求正在调用 `get` / When 检测完成之后发起新的调用 / Then 新调用被拒，不使用旧审核结果放行（检测后放行次数 = 0；N≥20 次并发尝试）。
- AC-013-06：Given Server 新增工具 `delete_all` / When 刷新 / Then 其状态为"待审核"，没有任何 agent 获得授权。
- AC-013-07：Given 替身返回畸形清单（工具数 1000、描述 10 万字符、深层嵌套 schema） / When 刷新 / Then ib-web 无崩溃与超时，超限项被排除并记录，合规项保留。

### US-014: 工具下线
- 故事：As a 系统管理员, I want to 当工具被 Server 撤下或 Server 被停用 / 删除时让工具立即不可调用并可追溯, so that 下线不留可用窗口。
- 来源：用户原文「删除…新工具」；调用方转述
- 关联需求：REQ-FUNC-014；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-014-01：Given 工具 `mcp__crm__update` 已启用且被授权 / When 刷新后 Server 清单不再含 `update` / Then 状态为"已下线"（含下线时间与原因），下线后的调用被拒（替身请求数 = 0）；目录中仍可查询到该记录。
- AC-014-02：Given 已下线的 `update` 被 Server 重新提供，指纹与曾审核版本相同 / When 刷新 / Then 状态为"待复审"，不自动恢复"已启用"，授权仍失效。

### US-015: 固定或屏蔽外部工具入参
- 故事：As a 系统管理员, I want to 为外部工具的入参设置固定值或屏蔽, so that 项目 / 租户等标识不由 LLM 填写，且无法被诱导篡改。
- 来源：调用方转述（外部 Server 不懂项目 scope，LLM 不得填租户参数）；基线 B5
- 关联需求：REQ-FUNC-015、REQ-NFUNC-002；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-015-01：Given 工具 `mcp__crm__search` 有参数 `tenant`，admin 为项目 A 把 `tenant` 固定为 `a-001` / When 查看提供给 LLM 的工具描述 / Then `tenant` 不出现在其中；agent 调用时替身收到的 `tenant` = `a-001`。
- AC-015-02：Given 同上，LLM（或注入内容）在调用中给出 `tenant = b-002` / When 调用 / Then 实际发出的值仍为 `a-001`（LLM 的实参被覆盖）；N≥30 条诱导样例中生效次数 = 0。
- AC-015-03：Given 项目 B 对同一工具固定 `tenant = b-002` / When 两个项目分别调用 / Then 各自替身记录的 `tenant` 分别为各自的固定值，互不串用。
- AC-015-04：Given 审核时工具有必填参数名为 `user_id` / `project_id` 且未被固定或屏蔽 / When admin 提交启用 / Then 页面给出风险提示"疑似承载租户 / 用户语义，请固定或屏蔽"；admin 仍须显式确认后才能启用（审计记录该确认）。
- AC-015-05：Given 项目配置者 / When 修改固定值 / Then 返回 403（固定值仅 admin 可设）。

### US-016: 把外部工具授权给 agent
- 故事：As a 项目配置者, I want to 把已启用的外部工具授权给 kb-agent、顾问等 agent, so that 这些 agent 能调用外部能力，且权限最小。
- 来源：用户原文「增加，变更，删除，查询新工具」；调用方转述（对 kb-agent、advisor 等 agent 授权）；基线 B3、B4
- 关联需求：REQ-FUNC-016；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-016-01：Given 项目 A 可见已启用的只读工具 `mcp__crm__get`（展示名 `mcp.crm.get`） / When 配置者勾选授权给 kb-agent 并保存、发布 / Then 差异清单显示新增授权（授权名为 `mcp__crm__get`）；发布后 kb-agent 的函数调用工具列表含 `mcp__crm__get`；同项目其他 agent 的工具列表不含它。
- AC-016-02：Given 授权引用了不存在 / 待复审 / 已下线 / Server 停用的外部工具 / When 保存 / Then 返回逐条错误，指出工具名与原因类别；整份配置不被保存。
- AC-016-03：Given 项目 A 的配置者提交含 B 项目专属 Server 工具的授权 / When 保存 / Then 被拒（跨项目越权），错误不泄露该工具的描述 / schema；B 的数据未被读取。
- AC-016-04：Given kb-agent 已授权 `mcp__crm__get`，顾问未授权 / When 顾问的 LLM 尝试调用 `mcp__crm__get` / Then 调用被拒（该工具不在顾问的工具列表中），替身请求数 = 0。
- AC-016-05：Given 匿名请求保存授权 / When 请求 / Then 返回 401；Given 项目 view 档账户（无配置写权限）请求保存授权 / When 请求 / Then 返回 403；两种情形下授权记录变化条数 = 0。

### US-017: 授权失效与恢复
- 故事：As a 项目配置者, I want to 在工具变更、下线、Server 停用或取消开放时看到授权失效及原因，且保存不被卡住, so that 我能清楚处置而不影响其他配置。
- 来源：调用方转述（schema 变更后授权失效；删除 Server 后已授权 agent 的处理）；基线 B3；C-R29-09（R28 OBS-1 教训）
- 关联需求：REQ-FUNC-017；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-017-01：Given 工具授权后转"待复审" / When 配置者打开授权页 / Then 该授权标注"失效：工具待复审"；agent 的调用被拒（替身请求数 = 0）。
- AC-017-02：Given 存在失效授权 / When 配置者修改其他无关配置并保存 / Then 保存成功（失效授权不触发 `工具不存在` 类整体拒绝）；失效授权记录保留。
- AC-017-03：Given 工具复审通过 / When 状态回"已启用" / Then 原授权自动恢复，agent 下一次调用成功；工具被 admin 删除（Server 删除）则授权不恢复。
- AC-017-04：Given 失效发生后 / When 某个已缓存的旧装配仍在运行 / Then 其后发起的调用同样被拒（不依赖重启或下次保存）；失效后放行次数 = 0。

### US-018: 默认不授权
- 故事：As a 系统管理员, I want to 确保升级、新建项目、新发现的工具都不自动授予任何 agent, so that 外部能力永远是显式决策的结果。
- 来源：调用方转述（kb-agent、advisor 授权；顾问默认可用性待确认）；基线 B9
- 关联需求：REQ-FUNC-018；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-018-01：Given 升级到含 MCP 适配的版本 / When 查看既有项目的定义文档与工具授权 / Then 与升级前逐项相同（差异字符数 = 0）。
- AC-018-02：Given admin 新建项目并启用顾问 / When 创建完成 / Then kb-agent 授权仅 `search_knowledge`，顾问授权为空；外部工具授权数 = 0。
- AC-018-03：Given Server 新发现 5 个工具并有一个"只读"已启用工具 / When 无人操作 / Then 没有任何 agent 的授权增加（含顾问）。

### US-019: 调用外部工具并处理结果
- 故事：As a 终端提问用户, I want to 让 agent 在需要时调用外部工具并得到可靠的答复, so that 我能获得外部系统的信息，且失败时得到如实说明。
- 来源：用户原文「能做好…调用」；调用方转述（结果 content + isError）；基线 B5、B6；`[WEB: https://modelcontextprotocol.io/specification/latest/server/tools，2026-11-05]`
- 关联需求：REQ-FUNC-019；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-019-01：Given kb-agent 已被授权可用的只读工具 `mcp__crm__get`，替身返回文本结果 / When 终端用户提问触发该工具 / Then 替身收到的调用名为原始工具名 `get` 且入参通过 schema 校验；agent 的答复引用该结果；审计留下该次调用记录。
- AC-019-02：Given LLM 生成的参数不符合入参 schema（缺必填项或类型错误） / When 调用 / Then 不发出外部请求（替身请求数 = 0），agent 收到明确的参数错误并可重试；整轮不失败。
- AC-019-03：Given 替身返回工具执行错误（isError = true，含错误文本） / When 调用 / Then agent 收到"失败结果"（含经围栏的错误文本）；整轮 HTTP 状态不是 5xx；答复不暴露内部错误细节原文之外的堆栈。
- AC-019-04：Given 替身分别模拟：协议级错误、不可达、超时、鉴权失败 / When 各调用 5 次 / Then 整轮 5xx 次数 = 0；agent 答复含"该能力暂不可用"的说明；答复中出现状态码数字、服务方错误原文、凭证片段的次数 = 0。
- AC-019-05：Given 替身返回含文本 + 1 张图片 + 1 个资源链接的结果 / When 调用 / Then agent 只收到文本，并附标注"已忽略 2 项非文本内容"。
- AC-019-06：Given 替身返回 100 KB 文本 / When 调用 / Then 交给 agent 的文本长度 ≤ 32 KB 并带"已截断"标注。
- AC-019-07：Given 替身要求补充输入（交互式追问） / When 调用 / Then 按失败降级处理，agent 收到"该工具需要交互输入，暂不支持"，不发起任何追问请求。

### US-020: 治理调用的超时、次数、并发与熔断
- 故事：As a 系统管理员, I want to 设置并强制外部工具调用的超时、次数上限、并发与熔断（项目只能调低）, so that 单个外部服务的故障或滥用不会拖垮平台。
- 来源：调用方转述（超时、调用次数、熔断）；基线 B6、B10
- 关联需求：REQ-FUNC-020、REQ-NFUNC-006、REQ-NFUNC-007；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-020-01：Given 全局调用超时 30 秒，替身 60 秒才返回 / When 调用 / Then 在 30 ± 1 秒内终止并返回"超时"；整轮仍有答复。
- AC-020-02：Given 每用户回合上限 5 次，计数跨该回合内全部 agent 合计（OQ-ARCH-R29-04=A），同一用户回合内 kb-agent 已调用 3 次、被委托的另一 agent 已调用 2 次 / When 该回合内任一 agent 发起第 6 次调用 / Then 不发出外部请求（替身请求数不增加），该 agent 收到"本轮调用次数已达上限"；When 用户发起下一个用户回合 / Then 计数清零，首次调用可发出。
- AC-020-03：Given 某 Server 连续 5 次失败 / When 第 6 次调用 / Then 立即降级（出站请求数 = 0，1 秒内返回）；60 秒后首次探测成功则恢复，失败则继续暂停；状态变化写审计。
- AC-020-04：Given 全局每轮上限 5 / When 项目配置者把本项目 agent 的上限设为 8 / Then 保存被拒，逐条报错"超出上层上限"；设为 3 则成功并按 3 生效。
- AC-020-05：Given Server 并发上限 2 / When 同时发起 4 个调用 / Then 同一时刻替身观测到的在途调用数 ≤ 2，其余排队或按超时降级，无 5xx。

### US-021: 有副作用的外部工具默认受限
- 故事：As a 系统管理员, I want to 默认禁止把有副作用或风险未知的外部工具授权给 agent，仅在我显式接受风险后放行, so that 在没有人工确认能力前不会发生未经许可的写操作。
- 来源：调用方转述（有副作用工具的人工确认，当前系统没有 HITL）；基线 B13
- 关联需求：REQ-FUNC-021；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-021-01：Given 工具 `mcp__crm__update` 风险级别为"有副作用" / When 项目配置者把它授权给 kb-agent 并保存 / Then 保存被拒，错误"风险级别为有副作用，未获管理员放行"；授权未生效。
- AC-021-02：Given admin 对项目 A 的 `mcp__crm__update` 填写理由并"接受风险放行" / When A 的配置者再次保存授权 / Then 保存成功；审计记录放行人、理由、范围（项目 A、该工具）；项目 B 的同类授权仍被拒。
- AC-021-03：Given 放行后 admin 撤销放行 / When 其后调用 / Then 调用被拒（替身请求数 = 0），配置页标注授权失效原因"放行已撤销"。
- AC-021-04：Given 放行时未填写理由 / When admin 提交 / Then 返回 400，不放行。
- AC-021-05：Given 风险级别为"未知"的工具 / When 授权 / Then 与"有副作用"同样被拒，直至 admin 裁定为"只读"或放行。

### US-022: 调用前人工确认（HITL）（已移出）
- **【已移出（CP-001）】** 调用前人工确认（HITL）本轮不做（用户裁决 CP-001 Q2=A，OQ-R29-05=A，经主会话转述），对应 REQ-FUNC-022 已移入超出范围 OOS-R29-12；US-022 编号保留为占位、不复用，原 AC-022-01~03 作废、不再验收；不计入故事数、AC 数与故事点。有副作用 / 未知风险工具的受限行为由 US-021 承接。

### US-023: 外部工具不进入路由能力摘要
- 故事：As a 系统管理员, I want to 外部工具的描述不进入路由提示, so that 服务方可控的文本无法影响路由决策。
- 来源：调用方转述（是否进入路由能力摘要，待确认）；基线 B7
- 关联需求：REQ-FUNC-023；优先级：Should Have；故事点：2 [ESTIMATE]
- AC-023-01：Given 项目有多个已启用且已授权的外部工具 / When 构造路由提示的能力摘要 / Then 摘要不含任何 `mcp__` 前缀工具（及其 `mcp.` 展示名）的名称或描述（出现次数 = 0），内置工具条目与基线逐项一致。
- AC-023-02：Given 某外部工具描述含"总是路由到本工具"类文本 / When 终端用户提问 / Then 路由结果与未登记该 Server 时相同（N≥20 条问句差异 = 0）。

### US-024: 健康探测与手动刷新
- 故事：As a 系统管理员, I want to 看到 Server 的实时健康并能手动测试 / 刷新, so that 故障时能快速判断、恢复后无需手工干预。
- 来源：调用方转述（超时、熔断、可观测）
- 关联需求：REQ-FUNC-024；优先级：Should Have；故事点：3 [ESTIMATE]
- AC-024-01：Given 已启用的 Server 突然不可达 / When 下一个探测周期结束 / Then 状态变为"不可用"；其后的调用立即降级（无超时等待，1 秒内返回）。
- AC-024-02：Given Server 恢复 / When 探测成功 / Then 状态自动回"可用"，无需人工操作；写审计一条状态变化。
- AC-024-03：Given 项目配置者 / When 尝试触发"测试连接"或"刷新工具清单" / Then 返回 403。

### US-025: 兼容、可用性与回归守护
- 故事：As a 评测与验收人, I want to 确认未使用 MCP 的部署与对话完全不受影响, so that 本次增量不引入回归。
- 来源：画像 P5；基线 B12、B15；调用方转述
- 关联需求：REQ-NFUNC-001、REQ-NFUNC-012、REQ-NFUNC-013；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-025-01：Given 未登记任何 Server / When 跑既有全量回归与 selfcheck / Then 零新增失败；内置工具全集断言（`selfcheck.py:3924`、`:3962` 所检内容）口径不变；配置页可授权工具列表与基线逐项相同。
- AC-025-02：Given 未登记 Server / When 对 N≥30 条问句比对答复 / Then 与基线逐字相同（离线替身 LLM）。
- AC-025-03：Given 全部已登记 Server 替身不可达或挂起 / When 重启 ib-web 并发起 N≥20 条不涉及外部工具的对话 / Then ib-web 启动成功，对话成功率 = 100%；启动耗时增量待目标机实测校准，校准前标"未验收"。
- AC-025-04：Given 管理动作全集（登记 / 变更 / 停用 / 删除 / 凭证 / 开放 / 审核 / 风险裁定 / 放行 / 全局治理参数） / When 分别以匿名、项目 view 档、项目 edit 档（项目配置者）、admin 调用 / Then 未授权动作成功次数 = 0；匿名得 401、view / edit 档越权得 403，与权限矩阵逐项一致。

### US-026: 审计与可观测
- 故事：As a 系统管理员 / 评测与验收人, I want to 查询所有管理操作与每次外部调用的留痕, so that 出现问题可追溯，外发可核查。
- 来源：调用方转述（审计与可观测性）；基线 B11、B14
- 关联需求：REQ-NFUNC-008、REQ-NFUNC-009；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-026-01：Given 完成 N≥30 次外部调用与全部管理操作类型 / When 抽检审计记录 / Then 每条含操作者或 agent、项目、Server、工具（含前缀）、入参摘要（脱敏限长）、结果状态、耗时、降级原因、是否经人工确认、内容指纹；字段齐全率 = 100%；凭证值与完整入参原文出现次数 = 0。
- AC-026-02：Given admin 按 Server + 时间范围查询 / When 提交 / Then 仅返回匹配记录；Server 已删除时历史记录仍可查询。
- AC-026-03：Given 项目配置者查询审计 / When 提交 / Then 只返回本项目的记录，他项目记录出现次数 = 0；Given 匿名查询审计 / Then 401，Given 项目 view / edit 档账户查询审计 / Then 403（审计读取权限口径同 REQ-NFUNC-013）。
- AC-026-04：Given 已启用 1 个 Server 且声明数据类别 / When 请求 `GET /healthz/deps` 与查看启动日志 / Then 列出该 Server 的主机与数据类别；未登记 Server 时输出与基线一致。

### US-027: 安全攻防验收（注入、跨项目、外发、SSRF）
- 故事：As a 评测与验收人, I want to 用攻击样例验证外部工具链路的隔离与防护, so that 上线前确认关键风险已被封堵。
- 来源：调用方转述（提示注入、项目隔离、SSRF、凭证、外发）；协议 §L-1
- 关联需求：REQ-NFUNC-002、REQ-NFUNC-003、REQ-NFUNC-004、REQ-NFUNC-005、REQ-NFUNC-009；优先级：Must Have；故事点：8 [ESTIMATE]
- AC-027-01：Given 注入集 N≥20 条（工具描述含隐藏指令、返回内容诱导"调用另一工具 / 外发数据 / 忘记规则"、错误信息中带指令） / When agent 处理 / Then agent 的提示词、角色、工具选择、委托对象、答复格式被改变的次数 = 0；答复中出现系统提示词原文的次数 = 0；返回内容（含 isError 错误文本）以外部工具专用围栏形式出现在 LLM 输入中，围栏被内容提前闭合的次数 = 0；工具描述长度 ≤ 1000 字符、参数描述长度 ≤ 300 字符（数值出处：`architecture_design.md` ADR-R29-11），经净化后不含控制 / 零宽字符，以净化截断形式经函数 schema 通道出现、不加围栏。
- AC-027-02：Given 地址拒绝集 N≥30 条（127/8、10/8、172.16/12、192.168/16、169.254/16、IPv6 回环与 ULA、解析到私有地址的域名、302 到私有地址、先公后私的 DNS 重绑、十进制 / 十六进制 IP 写法） / When 作为连接目标登记、变更、测试连接、调用 / Then 被放行次数 = 0；允许名单为空时对内网目标放行次数 = 0。
- AC-027-03：Given admin 把 `10.0.0.8:9000` 加入内网允许名单 / When 登记指向该精确主机 + 端口的 Server / Then 登记成功；指向 `10.0.0.8:9001` 或 `10.0.0.9:9000` 的登记仍被拒；When 允许名单另含回环 `127.0.0.1:9100` 与 CGNAT `100.64.0.5:9200` / Then 这两个精确主机 + 端口的 Server 同样可登记（回环 / 私有 / CGNAT 均可经名单放行，OQ-ARCH-R29-06=A）。
- AC-027-04：Given 在知识库、会话历史、其他项目数据、提示词中植入 canary / When 跑 N≥30 条含外部工具调用的会话 / Then 发往替身 Server 的载荷中 canary 命中数 = 0；载荷内容仅含已审核入参 schema 内的参数。
- AC-027-05：Given 双项目夹具（含运行期新建项目） / When B 项目的 agent 构造调用试图指向 A 的专属 Server、A 的凭证或 A 的固定入参 / Then 成功次数 = 0；A 的数据在 B 的响应中出现次数 = 0。
- AC-027-07：Given admin 把 `169.254.169.254:80` 与其他链路本地地址（如 `169.254.10.1:8080`）填入内网允许名单 / When 登记、变更、测试连接、调用指向它们的 Server / Then 全部被拒，原因"地址被拒"，放行次数 = 0，替身请求数 = 0（链路本地与云元数据永不放行，即使在名单内）。
- AC-027-06：Given 工具被置为待复审 / 禁用 / 删除后立即发起调用 N≥20 次 / When 并发执行 / Then 实际发出的外部请求数 = 0；指纹被篡改的替身清单下调用被放行次数 = 0。

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 23 | 122 |
| Should Have | 2 | 5 |
| Could Have | 0 | 0 |
| **合计** | **25** | **127** |

2.1.0 变更（CP-002，经主会话转述）：只改 AC 措辞，故事数 25、故事点 127、有效 AC 113 条均不变。

1.1.0 变更：有效故事 27 → 25（US-009 Could / 8 点、US-022 Should / 13 点已移出，编号保留为占位不计数）；故事点 148 → 127；有效 AC 共 113 条（移出 AC-009-01~04、AC-022-01~03 共 7 条，新增 AC-001-06、AC-006-06、AC-008-05、AC-027-07 共 4 条）。

REQ-FUNC 覆盖：REQ-FUNC-001→US-001；002→US-002；003→US-003；004→US-004；005→US-005；006→US-006；007→US-007；008→US-008；010→US-010；011→US-011；012→US-012；013→US-013；014→US-014；015→US-015；016→US-016；017→US-017；018→US-018；019→US-019；020→US-020；021→US-021；023→US-023；024→US-024（有效 22/22 均有故事）；REQ-FUNC-009、REQ-FUNC-022 已移出（OOS-R29-11 / OOS-R29-12），其占位故事 US-009 / US-022 无 AC、不计数，无悬空引用。REQ-NFUNC 由 US-006（005）、US-007 / 015 / 027（002）、US-013 / 027（010 / 003）、US-020（006 / 007）、US-025（001 / 012 / 013）、US-026（008 / 009）、US-027（002–005、009）承接；REQ-NFUNC-011（畸形输入）由 AC-013-07 与 AC-010-04 承接。
