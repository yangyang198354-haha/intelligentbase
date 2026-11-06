<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-06T21:13:39+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>4.0.0</version>
  <input_files><file>docs/sdlc/intelligentbase/module_design.md</file><file>docs/sdlc/intelligentbase/architecture_design.md</file><file>docs/sdlc/intelligentbase/requirements_spec.md</file><file>docs/sdlc/intelligentbase/user_stories.md</file><file>docs/sdlc/intelligentbase/tech_stack.md</file><file>docs/sdlc/intelligentbase/e2e_test_report.md</file></input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — REV-29 agent 工具调用的 MCP 适配

REV-28 版本已归档于 `docs/sdlc/intelligentbase/archive/rev28/implementation_plan.md`（只读）。本文件为 REV-29 全新版本（0.1.0 DRAFT，`REWORK_AUTHORIZED`）。基线：HEAD b4fa3a3（PM 2026-11-05 实跑：pytest 1358 passed；selfcheck 68/69，`core_framework_free` 为既有失败）。

## 修订记录

| 版本 | 时间 | 说明 |
|---|---|---|
| 0.1.0 | 2026-11-05T16:06:04+08:00 | 初稿 |
| 0.2.0 | 2026-11-05T16:16:46+08:00 | GR-C-001 返工：仅将 `advisor_r28.test.js:260` 的 SYSTEM_ORDER 断言严格化为五项；产品代码未动 |
| 1.1.0 | 2026-11-05T22:46:38+08:00 | 缺陷回流第 1 轮（GR-D-001）：修 DEF-R29-002/003/004/005；见文末“缺陷修复轮”；既有内容未删 |
| 2.1.0 | 2026-11-05T23:13:57+08:00 | 缺陷回流第 2 轮（GR-D-002）：修 DEF-R29-006/007；见文末“缺陷修复轮 2”；既有内容未删 |
| 3.1.0 | 2026-11-06T21:13:39+08:00 | 缺陷回流第 3 轮（pm_escalation_GROUP_D_20261105T2341 / CP-002 Q1=A、Q5=A）：修 DEF-R29-008 与 checklists [B30]；见文末“缺陷回流第 3 轮”；既有内容未删 |

## 实现概览

- **MOD 完成数：24 / 24**（MOD-R29-01 ~ 24；统计口径见下表“状态”）。新建文件 24 个（`ib/mcp` 16 个、`ib/ledger/mcp_store.py`、`ibweb/mcp_views.py`、`010_mcp.sql`、前端 `McpServersPage.vue` + `utils/` 2 个），修改既有文件 26 个（含 `ci.yml`、两份 requirements、`env.example`、`checklists.txt`、selfcheck、前端 5 个文件）。
- **实现顺序**：按模块依赖图的拓扑（编号即拓扑序）：01 核心类型/端口 → 04 出网防护 → 05 注册表 → 02 规则/schema → 03 线协议 → 06 加解密 → 07 台账/迁移 → 08 传输 → 09 替身 → 10 客户端 → 11 结果 → 12 运行时 → 13 注册器 → 14 目录 → 15 管理 → 16 授权视图 → 17 supervisor → 18 编译/编排钩子 → 20 组合根 → 19 视图/路由 → 21~23 前端 → 24 CI/自检/部署文件。每组之后跑 compileall 与全量既有回归（均零新增失败）。
- **分工边界**：按协议 §A 与 invocation，本轮只写产品代码与迁移，**不在 `tests/` 下新建任何文件**，module_design MOD-R29-24 列出的 10 个新测试文件（`tests/unit|integration|e2e/*_r29.py`、前端冒烟追加）留给 GROUP_D。唯一的既有测试改动见“现有测试调整”（code_review_report）。
- **自验证方式**（均已执行，命令与输出尾部见 code_review_report“自验证结果”）：`compileall`；既有回归全量 pytest；离线 `selfcheck`（新增 8 个 MCP 守卫）；前端 `npm run build && npm test`；scratchpad 内的 Django 测试客户端冒烟（不入库，2 个用例，覆盖登记/凭证/启用/发现/审核/授权发布/热编译/调用/回合预算/rug-pull/审计/强制删除/禁用路径）；scratchpad 内的回环 HTTP 服务对 `HttpMcpTransport` 冒烟（modern + legacy、重定向不跟随、未命中允许名单的明文 http 被拒）。
- **ADR-R29-17 方案 C**：项目 venv 未装 `cryptography`——`ib.mcp.crypto` 延迟导入（无该包时 import 成功）；`make_secret_cipher`（组合根）四分支；离线落到 `ReversibleTestCipher`（`selfcheck mcp_no_plaintext_secret` 输出 `cipher=test`）；`ci.yml` 作业级 `IB_REQUIRE_CRYPTO: "1"`；两份 requirements 各加 `cryptography>=42,<51`。**真实 Fernet 路径本机未执行（未验证）**。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-R29-01 | `src/ib/core/types.py`、`ports.py`、`__init__.py` | 修改（追加） | — | M | 常量/枚举/21 个领域类型、`MCP_DEFAULTS`/`MCP_HARD_MAX`、5 个存储端口 + `SecretCipher` + `McpTransport` + `McpStores`；`ib.core` 仍零第三方依赖 | DONE |
| 2 | MOD-R29-04 | `src/ib/webtools/netguard.py`、`fetch.py` | 修改（加成式） | — | M | `NEVER_ALLOW_NETWORKS`；`is_address_allowed(internal_allowed=)`；`UrlGuard(allowed_ports=, internal_allow=)`（默认值 = 现行为）；`fetch.py` 追加 `PinnedHTTP(S)Connection` 公开别名 | DONE |
| 3 | MOD-R29-05 | `src/ib/tools/__init__.py` | 修改 | 01 | S | `ReservedToolNameError`/`ToolNameConflictError`；`register()` 拒保留前缀；`register_external()` 禁覆盖；`validate_grants` 放行保留前缀（含 param_values 归属） | DONE |
| 4 | MOD-R29-02 | `src/ib/mcp/__init__.py`、`rules.py`、`schema_lite.py` | 新建 | 01 | H | server_id/本地名/展示名/指纹；发现期合规检查（含 `over_limit`/`param_name_reserved`/`x_mcp_header_invalid`/`name_collision`）；租户嫌疑；风险推定；`admission_reason` 单一判定；有界 JSON Schema 子集（内联本地 `$ref`、`validate_args`、`project_llm_schema`、`x_mcp_header_violation`） | DONE |
| 5 | MOD-R29-03 | `src/ib/mcp/wire.py` | 新建 | 01 | M | modern/legacy 报文与头构造（含 `x-mcp-header` 镜像与 Base64 哨兵编码）、SSE 解析、JSON-RPC 解析（未知 resultType ⇒ ProtocolError）、HTTP 失败分类、`plain_http_allowed` | DONE |
| 6 | MOD-R29-06 | `src/ib/mcp/crypto.py` | 新建 | 01 | S | `Secret` 脱敏、`FernetSecretCipher`（延迟导入）、`UnconfiguredSecretCipher`、`validate_credential_input`/`validate_header_name` | DONE（Fernet 真实路径未验证） |
| 7 | MOD-R29-07 | `src/ib/ledger/mcp_store.py`、`schema.py`、`src/deploy/migrations/010_mcp.sql` | 新建/修改 | 01 | H | 9 张表 DDL 单源（`MCP_DDL_STATEMENTS`/`mcp_ddl_script`/`missing_mcp_tables`，`ensure_schema` 末尾追加）；5 个存储（Sqlite + Memory）；`read_admission` 单次联结查询；`build_mcp_stores` | DONE |
| 8 | MOD-R29-08 | `src/ib/mcp/transport.py` | 新建 | 01、03、04 | M | `HttpMcpTransport`：每次 `UrlGuard`+钉 IP；公网明文 http 先于 DNS 拒绝；3xx 不跟随；鉴权头仅此处展开；块迭代读取受期限约束；私有 CA | DONE |
| 9 | MOD-R29-09 | `src/ib/mcp/double.py` | 新建 | 01、03、06 | M | `FakeMcpServer`（modern/legacy、分页、脚本化、rug-pull、会话过期、SSE）、`FakeMcpTransport`、`FakeResolver`（含先公后私重绑）、`ReversibleTestCipher`；无网络导入 | DONE |
| 10 | MOD-R29-10 | `src/ib/mcp/client.py` | 新建 | 01、02、03 | H | 时代探测/回退、legacy 会话缓存与 404 重初始化一次、`tools/list` 分页（≤50 页、工具数上限）、`tools/call`、`listen` | DONE |
| 11 | MOD-R29-11 | `src/ib/mcp/result.py` | 新建 | 01、02 | S | 仅采纳文本、净化/截断/围栏、固定失败短语（无状态码/原文/凭证） | DONE |
| 12 | MOD-R29-12 | `src/ib/mcp/runtime.py` | 新建 | 01、02、06、10、11 | H | `McpBreaker`、`McpTurnBudget`（按 turn_id 跨 agent 合计）、`bind_mcp_turn`（contextvars + TTL 登记簿）、`McpInvoker.invoke` 固定 11 步 | DONE |
| 13 | MOD-R29-13 | `src/ib/mcp/binding.py` | 新建 | 01、02、05、12 | M | `make_registrar`（已审核快照 → `ToolSpec`+闭包；悬空授权容忍；失败抛 `ExternalRegistrationError`）、`external_tool_spec`、`external_param_specs_for` | DONE |
| 14 | MOD-R29-14 | `src/ib/mcp/catalog.py`、`auditing.py` | 新建 | 01、02、06、10 | M | verify/refresh/approve/reject/set_tool_enabled/tool_diff；发现凭证选择；审计辅助 | DONE |
| 15 | MOD-R29-15 | `src/ib/mcp/admin.py` | 新建 | 01、06、14 | H | Server CRUD、公网明文 http/传输类型/主密钥缺失校验、凭证、开放、固定入参、放行、治理、允许名单、`GrantIndex`、`GrantCleaner`、强制删除流程 | DONE |
| 16 | MOD-R29-16 | `src/ib/mcp/grants.py` | 新建 | 01、02 | M | `validate_external_grants`（仅相对 prior 新增者严格校验）、`grant_statuses`、`visible_servers/tools`、`catalog_external_tools` | DONE |
| 17 | MOD-R29-17 | `src/ib/mcp/supervisor.py` | 新建 | 01、12、14 | M | daemon 线程、2 线程探测池、复核、去抖刷新、≤`listener_max` 监听线程（退避重连） | DONE |
| 18 | MOD-R29-18 | `src/ib/runtime/compile.py`、`orchestration/dag.py`、`config/definition.py` | 修改（加成式） | 01、05 | M | `RuntimeDeps` 两字段；编译期注册器注入与悬空剔除；`run_dag` 对所有运行写 `turn_id`；`make_agent` 外部工具节点进入回合作用域；`definition.validate` 放行保留前缀 | DONE |
| 19 | MOD-R29-20 | `src/ibweb/composition.py`、`views.py`、`config_views.py`、`src/ib/config/__init__.py` | 修改 | 01~19 | H | `make_secret_cipher`/`build_mcp_runtime`/`mcp_egress_descriptors`/`McpRuntimeBundle`；`Deps.mcp`；`_plain_validate` 追加外部授权校验与项目级参数规格；`close()` 停 supervisor；healthz `egress_mcp`；catalog 追加键；5 个 env 键登记与 `IB_MCP_TRANSPORT` 取值域校验 | DONE |
| 20 | MOD-R29-19 | `src/ibweb/mcp_views.py`、`urls.py` | 新建/修改 | 01、12、14、15、16 | H | 14 个视图函数覆盖 IFC-R29-200~218（219 在 config_views）；admin 判定同 `_require_admin` 口径；错误体不回显凭证 | DONE |
| 21 | MOD-R29-21 | `src/frontend/src/api/client.ts`、`src/utils/mcpLabels.ts` | 修改/新建 | 19 | M | DTO 类型 + 25 个 `mcp*` 方法；统一词表（状态/风险/失效原因/失败类别/错误码） | DONE |
| 22 | MOD-R29-22 | `src/frontend/src/views/McpServersPage.vue`、`router/index.ts`、`layouts/ConsoleLayout.vue` | 新建/修改 | 21 | H | 4 个标签页（服务/工具目录/治理与允许名单/审计）+ 登记/详情/审核/固定入参放行/删除对话框；`SYSTEM_ORDER` 追加 `'mcp'`；传输下拉仅 `streamable_http`；凭证输入 `type="password"` 提交即清空 | DONE |
| 23 | MOD-R29-23 | `src/frontend/src/components/config/AgentDetailPanel.vue`、`src/utils/externalGrants.ts` | 修改/新建 | 21 | M | 外部工具分组（按 Server）、风险徽标、置灰、失效原因徽标、限制参数渲染；无可见外部工具/失效授权时不渲染。`ConfigPage.vue` 未改（见偏差 D8） | DONE |
| 24 | MOD-R29-24 | `src/scripts/selfcheck.py`、`.github/workflows/ci.yml`、`env.example`、`checklists.txt`、`requirements.txt`、`requirements-offline.txt` | 修改 | 07、19、20 | M | 8 个 selfcheck 用例；ci.yml 迁移检查纳入 010 + `IB_REQUIRE_CRYPTO`；env 占位；`[B30]` 核对项与签署行；依赖声明 | DONE（测试文件留 GROUP_D） |

## 迁移

- **`src/deploy/migrations/010_mcp.sql`**：9 张新表（`mcp_servers`、`mcp_server_projects`、`mcp_tools`、`mcp_tool_bindings`、`mcp_risk_waivers`、`mcp_credentials`、`mcp_governance`、`mcp_internal_allow`、`mcp_audit`）+ 4 个索引；内容 = 头注释（含 `[MANUAL_ROLLBACK_REQUIRED]` 回滚说明）+ `mcp_ddl_script()` 逐字输出（由生成器输出拼接，单源；selfcheck `mcp_schema_single_source` 与 ci.yml 迁移检查均核对）。
- `IF NOT EXISTS` 幂等，可重放；`ensure_schema` 末尾追加建表（纯新表，无补列/回填）；001~009 一字未改；文件中无可执行 `DROP`；`transport` 的 CHECK 只含 `'streamable_http'`。
- **可逆**：是（备份后由用户手工 DROP 9 张表，按依赖逆序，见头注释）；回退代码前须先清理项目授权（头注释与 `[B30]` 已写明）。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| D1 `Memory*` 存储 = 共享 `:memory:` SQLite 连接 + 全局锁，与 Sqlite 实现共用同一份 SQL | IFC-R29-061~065（“一个 Memory 替身 + 一个 Sqlite 实现”） | 用同一份 DDL/SQL 保证两种后端行为一致（端口一致性由构造保证），避免两套手写实现漂移；`build_mcp_stores(None, backend="memory")` 共享连接，单独实例化的 `Memory*` 各自独立库 | 端口一致性测试仍可对两者跑同一套用例；离线夹具行为 = 真实 SQL 约束（含 CHECK/UNIQUE） |
| D2 `McpStores` 定义在 `ib.core.ports`（而非 composition） | IFC-R29-220 | `ib.mcp.*` 与 `ib.ledger.mcp_store` 都需要该聚合类型，composition 属 `ibweb`，`ib.mcp` 不得反向依赖 | 组合根 import 使用，行为不变 |
| D3 `plain_http_allowed`、`McpTransportError`、`AUTH_SLOT_HEADER` 放在 `wire.py` | IFC-R29-070 / 003 | 使 `double.py` 与 `client.py` 不 import `transport.py`（后者是唯一网络导入文件，selfcheck 以源码判定） | `transport.py` 仍是唯一含网络导入的文件 |
| D4 `x-mcp-header` 合规判定实现在 `schema_lite.x_mcp_header_violation`，`wire.validate_x_mcp_header_annotations` 为包装 | MOD-02 依赖 01 | 避免 02 → 03 的依赖边（保持编号拓扑） | 签名与语义不变 |
| D5 新增可选关键字参数/字段：`GrantCleaner(head_of=)`、`McpAdminService(resolver=)`、`McpSupervisor(inline=)`、`McpAuditStore.count`、`SqliteMcpToolStore.waiver_projects/bindings_for`（非端口）、`McpRuntimeBundle.transport/resolver/gov_reader/registrar` | IFC-R29-144 / 140 / 170 / 002 / 221 | 分别用于：取 head 版本（避免访问发布服务私有属性）、离线 DNS 注入、离线驱动、审计分页总数、详情页展示、离线测试句柄 | 均为加成式；默认值保持设计语义 |
| D6 `McpGovernance` 各字段带默认值 | IFC-R29-001 | 方便“行缺失/读取失败回落 = 保守默认” | 与 `MCP_DEFAULTS` 同值 |
| D7 `McpInvoker` 在步骤②（回合预算）前独立读取一次治理参数，步骤③再随准入快照取 `governance` | IFC-R29-114 步骤顺序（② 先于 ③） | 步骤②需要全局上限而 Server 级上限要等③；Server 级每回合分计在③之后用 `server_count` 复核 | 多一次治理读取（读失败回落保守默认）；顺序与“此前步骤不出站”不变 |
| D8 `ConfigPage.vue` 未修改 | MOD-R29-23 文件清单 | 实际渲染配置面板的是 `ConfigStudio.vue` → `AgentDetailPanel.vue`，且整份 catalog 已整体传入，外部工具区只需改面板；`ConfigPage.vue` 为旧页，无需改动 | 无功能缺口 |
| D9 `run_dag` 对所有运行同时写入 `session_key`（原仅顾问路径） | IFC-R29-182 | 外部工具回合作用域的 `actor_id` 取自 `session_key`（与顾问节点同手法） | 状态多一个原语字段；`DagOutcome` 与 trace 不变（全量回归零新增失败） |

## 开放问题

- **[ASSUMPTION] A1** 注册器不区分试运行：`ExternalToolBinding.trial` 恒为 `False`（`RuntimeDeps.external_tool_registrar` 签名不含 trial 标志）；审计的 `trial` 列因此恒 0。如需区分，需扩展 registrar 签名（回流 GROUP_B）。
- **[ASSUMPTION] A2** 被排除（`excluded`）工具的占位 `local_name` = `mcp__<server>__!x<sha256 前 12 位>`（含 `!`，永不是合法函数名，满足 `UNIQUE(local_name)`，不会被授权/注册）；该工具后来变合规时 `local_name` 改写为正常名。
- **[ASSUMPTION] A3** 凭证 `scope_key`：`@shared` / `@discovery` / `<project_id>`；`credential_scope='shared'` 的 Server 只接受 `shared` 范围写入，`'project'` 的只接受 `discovery`/`project`。
- **[ASSUMPTION] A4** “计入熔断”的失败类 = `unreachable/timeout/protocol_error/auth_failed/protocol_incompatible`；`address_blocked/bad_arguments/input_required/response_too_large` 与 `isError` 不计入。
- **[ASSUMPTION] A5** 审计开始行 `outcome='pending'`，`finish_call` 只回填 `outcome='pending'` 的行一次；准入拒绝记 `action='call.denied'` 尽力而为（写失败不影响拒绝）。
- **[ASSUMPTION] A6** 保存期 `credential_missing` 映射为错误码 `mcp_server_unavailable`（设计的错误码清单无对应项）。
- **[ASSUMPTION] A7** `subscriptions/listen` 请求参数形状取 `params.notifications.toolsListChanged=true`（出处表只写“请求 `notifications.toolsListChanged`”）；legacy 会话头拼写取出处表的 `MCP-Session-Id`。监听流 300 秒窗口后由 supervisor 退避重连。
- **[ASSUMPTION] A8** 回合预算登记簿 TTL 900 秒；`ttlMs/cacheScope` 未使用（复核间隔取治理参数）。
- **[ASSUMPTION] A9** 乐观并发 `expected_updated_at` 基于秒级 ISO 时间戳，同一秒内的两次更新无法区分（见 code_review_report CR-006）。
- **[UNSOURCED] U1** 函数名字符集/长度（≤64、`[A-Za-z0-9_-]`）沿用设计的保守通例，目标机契约探针待验证（架构 A-R29-2、TBD-R29-2），未联网查证。
- **[TODO，非本轮范围]** stdio、调用前人工确认（HITL）、legacy GET 长流/旧 HTTP+SSE 均按 OOS-R29-11/12 未实现，无任何预留接口。
- **未验证项**：① `FernetSecretCipher` 真实路径（venv 无 `cryptography`，`test_mcp_crypto_fernet_r29.py` 将在本机 SKIP，CI 以 `IB_REQUIRE_CRYPTO=1` 强制）；② 目标机 CPU 上的 `cryptography` import/加解密探针（`[B30]`）；③ 真实浏览器交互（前端仅做类型检查与源码级冒烟）；④ 真实 MCP Server 互通（不在离线范围）。

## 缺陷修复轮（GR-D-001，缺陷回流第 1 轮）

范围：只修 DEF-R29-002 / 003 / 004 / 005，只改产品代码，未改任何测试文件；DEF-R29-001（工具描述未围栏，AC 与 ADR 冲突，待用户裁决）按指令未触碰。

| 序号 | DEF | 文件 | 改动要点 | 复杂度 | 状态 |
|---|---|---|---|---|---|
| F1 | DEF-R29-004 | `src/ib/mcp/runtime.py`（`_call` 步骤⑥） | 入参只保留已审核 `inputSchema.properties` 中声明、且不属于 `hidden ∪ fixed` 的键，再合入 `fixed_args`；schema 无 `properties` ⇒ 声明集为空 ⇒ 全部 LLM 实参被丢弃 | L | DONE |
| F2 | DEF-R29-003 | `src/ib/mcp/client.py`、`src/ib/mcp/catalog.py` | `McpTarget` 追加可选字段 `supports_list_changed: bool = False`；`catalog._target` 带入台账中验证期协商值；`list_tools` 已知时代分支改为 `bool(target.supports_list_changed)`，不再硬编码 False；`listen()` 起一个 `ib-mcp-listen-close` 小线程，`stop` 置位即关闭监听响应流（`done` 事件保证正常结束时线程退出） | M | DONE |
| F3 | DEF-R29-003 | `src/ib/mcp/supervisor.py`（`stop`） | 置位各监听 `ev` 后对监听线程带超时 join（总预算 = `timeout_s`） | L | DONE |
| F4 | DEF-R29-002 | `src/ib/mcp/result.py`、`src/ib/mcp/client.py`（`call_tool` 读取上限） | `render_result` 净化阶段不再按字符数截断（`max_chars=len(body)`），长度上限统一由字节截断承担，超限 `truncated=True` 并追加“已截断”；截断时为标注预留字节，正文 + 标注合计 ≤ `max_result_bytes`；读取上限由 `max_bytes+64KB` 改为 `max(4×max_bytes, max_bytes+64KB)`，100 KB 合法文本不再被降级为“返回内容过大” | M | DONE |
| F5 | DEF-R29-005 | `src/ib/orchestration/dag.py`（`_advisor_node`；import 增加 `ExitStack`） | 顾问节点持有 `mcp__` 工具且 `mcp_turn_scope` 非空 ⇒ 在顾问回合作用域内再进入外部工具回合作用域（同 `turn_id/project_id/actor_id`，与非顾问分支一致，IFC-R29-182），不放宽预算；用 `ExitStack` 避免整段重缩进 | M | DONE |

迁移：无。架构偏差：无新增（`McpTarget` 增加默认值字段属加成式，同 D5 手法；读取上限系数 4 为 `[ASSUMPTION] A10`）。

### 开放问题（本轮新增）
- **[ASSUMPTION] A10** `call_tool` 响应读取上限取 `max(4×max_result_bytes, max_result_bytes+64KB)`（默认 128 KB；上限 256 KB 时 1 MB）：设计只写“受 max_bytes 约束”，未给系数；超过该上限仍降级 `response_too_large`（内存仍有界）。
- **[ASSUMPTION] A11** DEF-004 声明集 = `approved.input_schema["properties"]` 的键；schema 若无 `properties`（仅 `additionalProperties`）则视为“未声明任何参数”，LLM 实参全部丢弃，仅 `fixed_args` 外发。被丢弃键名本轮**未**写审计（“可记入”为可选项，避免改审计契约）。
- **[ASSUMPTION] A12** 真实传输下 `resp.close()` 能否打断另一线程中阻塞的 socket 读取取决于 `http.client` 实现（`transport.py:139` 的 `close=conn.close`）；离线替身已验证，真实长连接路径**未验证**，监听线程为 daemon 且有 300 秒窗口兜底。

### 预期翻转的“缺陷冻结用例”（断言旧缺陷行为，修复后按设计失败；不计新增失败，由 test-engineer 翻转）
（第 1 轮清单；第 2 轮清单见文末“缺陷修复轮 2”）
| # | 用例 | 失败原因（断言旧缺陷行为） |
|---|---|---|
| 1 | `tests/unit/test_mcp_runtime_r29.py::test_TC_UNIT_R29_370_undeclared_args_are_forwarded_to_server_current_behavior_frozen_DEF_R29_004_AC_027_04` | 断言未声明键 `history/other_project` 被外发；现仅剩 `{'q': 'x'}` |
| 2 | `tests/e2e/test_mcp_e2e_r29.py::test_TC_E2E_R29_008_outbound_payload_canary_N30_sessions_declared_params_only_and_extra_key_gap_frozen` | 断言 `last.arguments == {"q":"x","leak":C_HIST}`；现为 `{"q":"x"}` |
| 3 | `tests/unit/test_mcp_runtime_r29.py::test_TC_UNIT_R29_324_exactly_100kb_text_current_behavior_frozen_DEF_R29_002_AC_019_06` | 断言 `r.ok is False` 且为“返回内容过大”；现 `ok=True`，文本已截断并带“已截断” |
| 4 | `tests/unit/test_mcp_runtime_r29.py::test_TC_UNIT_R29_325_ascii_over_32kb_marker_missing_current_behavior_frozen_DEF_R29_002_AC_019_06` | 守卫串 `"已截断" not in r.content`；现已带标注（正文 + 标注 ≤ 32768 字节仍成立） |
| 5 | `tests/unit/test_mcp_supervisor_r29.py::test_TC_UNIT_R29_609_listener_thread_exit_after_stop_with_quiet_stream_current_behavior_frozen_DEF_R29_003` | 断言 `stop()` 后监听线程残留；现 `lingering == []` |
| 6 | `tests/unit/test_mcp_supervisor_r29.py::test_TC_UNIT_R29_610_enable_flow_overwrites_list_changed_support_so_listener_never_starts_frozen_DEF_R29_003` | 断言启用后 `supports_list_changed is False` 且监听不启动；现保留为 True 并启动监听 |
| 7 | `tests/integration/test_mcp_compile_hotpath_r29.py::test_TC_INT_R29_1010_advisor_granted_external_tool_is_always_denied_no_turn_scope_current_behavior_frozen_DEF_R29_005` | 断言顾问调用得 `no_turn_scope` 短语；现调用成功（`ok:search`） |

## 缺陷修复轮 2（GR-D-002，缺陷回流第 2 轮，最后一轮）

范围：只修 DEF-R29-006 / 007，只改 `src/ib/mcp/transport.py`（`client.py`、`supervisor.py` 无需改动），未改任何测试文件。

| 序号 | DEF | 文件 | 改动要点 | 复杂度 | 状态 |
|---|---|---|---|---|---|
| F6 | DEF-R29-007 | `src/ib/mcp/transport.py` `_chunks` | `resp.read(_BLOCK)` → `resp.read1(_BLOCK)`（有多少读多少，一次底层读取即返回）；`settimeout` 改用 `post()` 中留底的 `sock`（close-delimited 时 `conn.sock` 已为 None，原先该分支不更新超时） | L | DONE |
| F7 | DEF-R29-006 | `src/ib/mcp/transport.py` `post` / `_close` | `endheaders` 后留底 `sock = conn.sock`；`close` 由 `conn.close` 改为 `_close()`：先 `sock.shutdown(SHUT_RDWR)`（忽略 OSError）唤醒另一线程阻塞的读取，再分别关闭 `resp` 与 `conn`（各自吞异常，幂等）；`_chunks` 异常映射追加 `ValueError`/`AttributeError`（关闭与读取竞态时 fp 已置 None），统一映射 `unreachable`，`listen` 在 stop 已置位时吞掉 | M | DONE |

迁移：无。架构偏差：无（MOD-R29-08 契约“响应以块迭代、期限内读取”未变）。

### 开放问题（本轮新增）
- A12 已在真实回环 socket 上验证：stop 置位后监听线程约 0.1 s 退出且服务端观察到客户端断开（close-delimited 与 chunked 均成立）。HTTPS（SSLSocket.shutdown）路径本轮**未验证**（离线、仅回环明文）。
- **[ASSUMPTION] A13** `resp.read1` 为 `http.client.HTTPResponse` 公开方法（Python ≥3.5，项目要求 ≥3.11）；返回块可能小于 `_BLOCK`，下游 `iter_sse_events` / 拼接逻辑按块累计，不依赖块大小。

### 预期翻转的“缺陷冻结用例”（不计新增失败，由 test-engineer 翻转）
`tests/integration/test_mcp_listen_realsocket_r29.py`：
1. `test_TC_INT_R29_720_...frozen_DEF_R29_006_A12[close-delimited]`（守卫串 `th.is_alive()` 在 :142 失败；现 stop 后线程已退出、客户端断开）
2. `test_TC_INT_R29_720_...frozen_DEF_R29_006_A12[chunked]`（同上）
3. `test_TC_INT_R29_721_...frozen_DEF_R29_007_AC_013_01[close-delimited]`（守卫串 `changed == []` 在 :163 失败；现 on_changed 在流仍开着时已回调一次）
4. `test_TC_INT_R29_721_...frozen_DEF_R29_007_AC_013_01[chunked]`（同上）

## 缺陷回流第 3 轮（DEF-R29-008、B30；文档 3.1.0 DRAFT）

来源：`pm_escalation_GROUP_D_20261105T2341.md`；用户经 CP-002 Q1=A、Q5=A 额外授权（原话“全部按推荐”，经主会话转述）。本轮只改产品代码与 `checklists.txt [B30]`，**未改任何测试文件**，未改 module_design（设计口径本就是“supervisor 仅在 ib-web 进程内”，`module_design.md:866`）。

### 改动清单

| # | DEF / 项 | 文件 | 新建/修改 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|
| G1 | DEF-R29-008 | `src/ibweb/composition.py` `_assemble` 末尾 | 修改 | L | 删除 `deps.mcp.supervisor.start()`（原 :1631-1633）；改注释说明 `_assemble` 也被 ib-worker 走到、supervisor 不在此启动 | DONE |
| G2 | DEF-R29-008 | `src/ibweb/composition.py` 新函数 `start_mcp_supervisor(deps)`（并入 `__all__`） | 修改 | L | 幂等入口：`deps.mcp`/`supervisor` 为 None（离线 / `IB_MCP_ENABLED=0`）⇒ 返回 False；否则 `supervisor.start()`（其自身对已存活线程为 no-op） | DONE |
| G3 | DEF-R29-008 | `src/ibweb/composition.py` `build_application()` | 修改 | L | 在 `get_deps` 就绪后调用 `start_mcp_supervisor(get_deps(required=False))`，再返回 `get_wsgi_application()` | DONE |
| G4 | CP-002 Q5=A | `src/deploy/checklists.txt` `[B30]` | 修改 | L | (3) 前端：改为“lock 未变时只 `npm run build`，不 `npm ci`”（SKILL.md §5.2、DEPLOY-005）；(2) env 核对命令加 `sudo` 并写全路径 `/etc/intelligentbase/ib-web.env`，仅输出计数/长度；目标机 venv 命令写 `/opt/intelligentbase/venv/bin/pip`、`/opt/intelligentbase/venv/bin/python`。[B30] 以外未动 | DONE |

### 设计取舍（为何由 `build_application` 启动）

- **进程入口事实**：ib-web 生产入口 `wsgi.py` 顶层 `application = build_application(build_deps())`；`apps.ready()` 在 `is_bootstrapped()` 为真时直接 return（`apps.py:43-46`），故 ib-web 生产路径上 supervisor 的启动点只能在 `build_application`（不依赖 ready）。ib-worker 路径为 `worker._setup_django → django.setup → apps.ready → build_deps`，**从不调用 `build_application`**，因此不再启动。
- 未采用“env 新键/显式标志”：用户本轮维护 env，不新增必填键；用进程入口自然区分，零配置。
- 未改 `wsgi.py`/`apps.py`/`worker.py`（最小改动）。`build_application` 本就是“WSGI 应用工厂”，在其中启动与 ib-web 语义一致。
- **各路径行为**：
  | 路径 | supervisor | 理由 |
  |---|---|---|
  | wsgi（Waitress/Gunicorn，ib-web） | 启动 | 经 `build_application` |
  | ib-worker（`python -m ibweb.worker`） | **不启动** | 不经 `build_application` |
  | `manage.py runserver` | 不启动 | Django 自建 WSGI handler，不经本工厂；开发期无需周期探测，且 runserver 会自动重载双进程，启动后台线程反而重复。需要联调时手动经 wsgi 路径 |
  | `manage.py check` / migrate / 其他管理命令 | 不启动 | 短命进程不应常驻线程（此前会启动，属附带改善） |
  | 测试/selfcheck 仅 `build_deps` | 不启动 | 避免无谓后台线程；需要时测试自行 `build_application(deps)`（现有 `test_TC_INT_R29_907` 即如此） |
- 停止路径：`Deps.close()` 的 supervisor.stop 逻辑（`composition.py` 原 :455-457）未改，仍对未启动为 no-op。
- 共享符号评估（P-PM-001）：`build_application` 调用方 grep —— 生产仅 `wsgi.py`；其余为 selfcheck / 测试（均离线，`deps.mcp` 为 None 或测试自管线程）。`start_mcp_supervisor` 为新增符号，无既有调用方。

### 迁移 / 架构偏差
迁移：无。架构偏差：无（实现与 module_design.md:866 对齐）。

### 开放问题（本轮新增）
- **[ASSUMPTION] A14** `manage.py runserver` 不启动 supervisor（见上表）。若开发联调需要，由使用者经 wsgi 路径；如需 runserver 也启动，须另行设计（RUN_MAIN 守卫），本轮不做。
- 成对用例（worker 装配 `build_deps` 后无 `ib-mcp-supervisor` 线程；`build_application` 后有）交 test-engineer 在 GROUP_D 补写。既有 `test_TC_INT_R29_907` 断言非离线 `build_application` 后线程存在，按本设计仍成立（已实跑）。
- 目标机行为（ib-web 重启后 supervisor 线程存在、ib-worker 重启后不存在）未在真机验证，留待部署后验证项。
