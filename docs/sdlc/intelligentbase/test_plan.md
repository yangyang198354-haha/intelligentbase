<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-06T21:28:39+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划（REV-29：agent 工具调用的 MCP 适配）

> 本文件 1.1.0 DRAFT（缺陷回流第 3 轮复测，用户经 CP-002 额外授权；见文末“回流第 3 轮”）。历史说明：0.3.0 DRAFT（缺陷回流第 2 轮复测，最后一轮）：GROUP_C 已修 DEF-R29-006 / 007（仅 `src/ib/mcp/transport.py`），TC-INT-R29-720 / 721 已翻转为 AC 原口径（close-delimited 与 chunked 两种参数均保留），当前**冻结用例 0 条**；A13（HTTPS 路径）列入人工验证清单 MV-09。上一版 0.2.0（缺陷回流第 1 轮复测）：7 条缺陷冻结用例中的 6 条翻转为 AC 原口径的正向断言（DEF-R29-002/003/004/005 已修复已验证），新增真实 socket 监听流用例 TC-INT-R29-720 / 721（A12），其验证结果登记新缺陷 DEF-R29-006 / 007。基础版本为 REV-29 的 0.1.0。REV-28 的 APPROVED 版本已归档于 `docs/sdlc/intelligentbase/archive/rev28/`（只读）。
> 用例 ID 沿用 `TC-UNIT|INT|E2E-R29-NNN`（修订号中缀，同既往轮次惯例）；前端用例 `TC-FE-R29-NNN`。

## 测试策略

**被测改动**：REV-29 新增 `src/ib/mcp/`（规则 / 线协议 / 客户端 / 传输 / 运行时 / 目录 / 管理 / 授权 / 绑定 / supervisor / 替身）、`src/ib/ledger/mcp_store.py` + 迁移 010、`src/ibweb/mcp_views.py` 及对 `composition.py` / `config_views.py` / `views.py` / `orchestration/dag.py` / `runtime/compile.py` / `webtools/netguard.py` 的加成式改动；前端 `McpServersPage.vue` / `utils/mcpLabels.ts` / `utils/externalGrants.ts` / `client.ts` / 路由与导航 / `AgentDetailPanel.vue` 外部工具区。

**范围（in scope）**：user_stories 3.0.0 的 25 个有效故事、113 条有效 AC（Must 23 个故事；3.0.0 仅按 CP-002 Q2/Q3 改写 AC-027-01 与 6 条访问控制 AC 的措辞，AC 数不变）；REQ-NFUNC-001（无 Server 时与基线一致）的“同输入逐字相同”回归；GR-C-003 的 5 条门控条件。
**范围外（out of scope）**：stdio / HITL（OOS-R29-11 / 12，已移出）；真实 MCP Server 互通；真实 `cryptography` 的 Fernet 执行（本机未安装，见下）；浏览器内交互；真实 LLM 的抗注入能力；目标机启动耗时校准。

**环境**：项目 venv `/root/.venvs/intelligentbase/bin/python`（Python 3.12.3，pytest 9.1.1）；环境变量 `PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`；Node v22.23.3（`npm run build && npm test`，未执行 `npm install` / `pip install`）。**venv 未安装 `cryptography`**：Fernet 契约用例本机 SKIP（逐条原因见 unit_test_report），不计 PASS；凭证主密钥在离线装配下由产品的 `make_secret_cipher(offline=True)` 回落 `ReversibleTestCipher`（报告记账 `cipher=test`）。测试数据库：SQLite 内存 / `tmp_path` 文件；不连 Qdrant / DeepSeek / ib-embed / 真实 MCP Server / 互联网。

**判定模式**：INCREMENTAL / `gate_mode=baseline`——每层相对基线零新增失败且新写用例全部通过才进入下一层；critical path（Must Have 故事的 E2E 用例）通过率 ≥ 1.00。
**基线来源**（PM 实跑，改动前 HEAD b4fa3a3）：`pytest tests` 1358 passed；selfcheck 68/69（`core_framework_free` 既有 FAIL）；前端 160/160（其中 `advisor_r28.test.js:260-261` 为本轮契约变更，GR-C-001 已授权，本轮核对其严格性：断言为 `const SYSTEM_ORDER = [...五项含 'mcp'];` 的整行精确匹配，无可选组 / 宽松正则，且单独断言前三项相对顺序不变——合格，未再改动）。改动后 PM 复跑口径：1358 passed、selfcheck 76/77、前端 160/160。
**分层机制**（画像 P4）：按目录分层（`tests/unit` / `tests/integration` / `tests/e2e`），前端为独立的 `node:test` 层，selfcheck 为独立层，二者不并入 Python 三层的算术（M-TE-001）。分层用例数用 `pytest tests/<层> --collect-only -q | grep -cE '::'` 独立实测。

**critical path 口径**：替代——项目无浏览器 E2E 框架，用最高层可执行的端到端级用例（真实账户鉴权 + 真实管理端点 + 真实发布协议 + 真实运行时 + 真实 SSE 流式问答的多步 HTTP/SSE 旅程；MCP Server / DNS / LLM 为替身）。

**测试替身与边界**（均为替身，不改产品代码，不 monkeypatch 被测模块自身判定）：产品自带 `FakeMcpServer` / `FakeMcpTransport` / `FakeResolver` / `ReversibleTestCipher`；脚本化 LLM（`ScriptedLlm`，仅替换 `deps.llm` 实例上的 `build_expert` / `build_router`）；`ListenTransport`（`FakeMcpTransport` 子类，补 `subscriptions/listen` 的阻塞 SSE 流）；回环 `ThreadingHTTPServer`（仅 127.0.0.1 随机端口，测试内启停，不出网）。

**GR-C-003 条件落实**（编号与 invocation special_instructions 第 5 条一致）：

| 条件 | 落实 |
|---|---|
| (1) Fernet 契约 + `IB_REQUIRE_CRYPTO` | `tests/unit/test_mcp_crypto_fernet_r29.py`（TC-UNIT-R29-220~225）：契约用例经 fixture 探测 `cryptography.fernet`，缺包且 `IB_REQUIRE_CRYPTO=1` ⇒ `pytest.fail`（守卫 + 5 条契约 ERROR），否则 SKIP（6 条如实计 SKIP，不冒充 PASS）。核对 CR-001：`ci.yml:54` 作业级 `env.IB_REQUIRE_CRYPTO: "1"`，所有 pytest 步骤继承；`requirements-offline.txt:35` 含 `cryptography>=42,<51`（CI 安装步骤自动覆盖）。本机演示（缺包 + `IB_REQUIRE_CRYPTO=1`）：`1 failed, 5 errors`，见 unit_test_report |
| (2) `HttpMcpTransport` 回环契约 | `tests/integration/test_mcp_http_transport_r29.py`（20 例，仅 127.0.0.1 临时端口）：modern / legacy 两形态、302 不跟随、公网明文 http 先于 DNS 拒绝、钉 IP + 每次重解析、读取上限、真实时钟超时、鉴权头仅传输层展开 |
| (3) supervisor 监听线程（CR-008） | `tests/unit/test_mcp_supervisor_r29.py`（11 例，真实线程 + 阻塞 SSE 流替身）：listen 流 → 去抖 → 复审态、健康探测、周期复核、start/stop 生命周期；DEF-R29-003 已修复，609 / 610 已翻转为正向断言；真实 socket 口径见 DEF-R29-006 / 007（TC-INT-R29-720 / 721） |
| (4) 前端管理页冒烟（CR-009） | `src/frontend/tests/mcp_r29.test.js`（20 例，TC-FE-R29-001~033）：词表 / 外部授权纯函数 / client 方法 / 页面源码结构（password 输入、二次确认、无 stdio、无 HITL）/ 路由与导航；真实浏览器交互 NOT_TESTABLE，列入 e2e_test_report「人工验证清单」 |
| (5) 接管 `advisor_r28.test.js:260-261` | 见下「现有测试调整」：登记为 test-engineer 接管，不放宽 |
| (6) fail-closed / fail-open 与正例成对 | 每个拒绝分支断言“替身 `tools/call` 数 = 0”并有放行正例（例：TC-UNIT-R29-300 正例 ↔ 301~309 各拒绝分支；TC-UNIT-R29-341 恢复 ↔ 340 熔断；TC-INT-R29-1000 授权后可调用 ↔ 越权被拒；TC-INT-R29-817 无主密钥拒绝 ↔ `auth_kind=none` 登记成功；TC-INT-R29-815 公网明文拒绝 ↔ https / 名单内 http 通过；TC-INT-R29-1005 失效 ↔ 复审后恢复）；永不抛 / 降级契约（TC-UNIT-R29-321、361）有失败分支用例，且 TC-E2E-R29-001 / 004 / 005 / 009 配“未降级且确有结果”的正例 |

**兼容性零变化（REQ-NFUNC-001）与黄金数据来源**：`tests/integration/mcp_r29_baseline_golden.json` 由基线 commit b4fa3a3 的 src 树生成（`git archive b4fa3a3 src` 解出，`IB_SRC` 指向，运行 `tests/advisor_r28_probe_support.py`），**不是**被测改动后代码自生成。本次 GROUP_D-002 在 scratchpad 独立重新生成（不 stash / checkout / reset），与入库黄金 `a == b` 为 True，逐键一致；回归用例以当前 src 重跑同一探针逐键比对，无白名单。module_design 兼容性回归点 #1~#12 的落点：#1/#2/#3/#4 → TC-INT-R29-900/901（答复、事件、路由哈希、LLM 载荷、定义文档逐项一致）+ 既有 `test_langgraph_contract_r26.py`；#5/#6/#10 → TC-INT-R29-901（可授权工具 / 参数规格 / 定义文档）+ selfcheck `mcp_namespace_guard`；#7 → 既有 R28 SSRF 用例 + TC-UNIT-R29（默认 80/443 回归）；#8/#9 → TC-INT-R29-902/903；#11 → TC-UNIT-R29（迁移 010 单源 / 幂等 / 无 DROP）；#12 → TC-INT-R29-907（关机无线程残留）。

**缺陷冻结纪律**（M-TE-007）：已发现但本轮不修的产品缺陷，用例断言“当前行为 + 守卫串”（修复后会响亮失败），同时登记 DEF；不 skip、不放宽断言。0.1.0 的 7 条冻结用例（`TC-UNIT-R29-324/325/370/609/610`、`TC-INT-R29-1010`、`TC-E2E-R29-008` 第③段）已在本轮翻转为正向断言（用例名去掉 `current_behavior_frozen`，守卫串删除，TC 编号不变，翻转强度不低于缺陷原描述，详见 unit / e2e 报告“翻转用例”）。当前冻结用例：**0 条**。`TC-INT-R29-720 / 721`（真实 socket，DEF-R29-006 / 007，各 2 个参数化实例）已在第 2 轮翻转：720 = stop 后 3 s 内监听线程 `is_alive()==False`、服务端观察到客户端断开、errors 为空（并含 stop 之前仍阻塞/仍连着的正例）；721 = 流保持打开时 list_changed 在 2 s 内回调恰好一次（流开着期间不重复）、服务端关闭后线程退出且 errors 为空。用例名去掉 `frozen` 字样，守卫串删除，TC 编号不变。

## AC 映射

说明：硬件类“运行方式”列不适用（画像 P11-1 / P11-2 为“无”，P11-3 的 DeepSeek 与本轮 MCP 无关），统一记 `—`；“前置 → 动作 → 预期”为 G/W/T 摘要，断言均有明确期望值。全部为**新写**（本轮 MCP 为全新子系统，无既有用例可复用；回归用既有用例单列于“回归”小节）。位置路径省略 `tests/` 前缀；ID 省略 `R29-` 中缀（如 `U-410` = `TC-UNIT-R29-410`，`I-810` = `TC-INT-R29-810`，`E-001` = `TC-E2E-R29-001`，`F-021` = `TC-FE-R29-021`）。

| AC | 用例 ID | 级别 | 位置（文件） | 前置 → 动作 → 预期 | 测试数据 |
|---|---|---|---|---|---|
| AC-001-01 | I-810, E-001 | INT, E2E | integration/test_mcp_admin_api_r29.py; e2e/test_mcp_e2e_r29.py | admin 登记 → 201、状态 registered、工具数 0、令牌只显示“已设置”、审计一条且不含令牌 | CANARY_TOKEN |
| AC-001-02 | I-811 | INT | integration/test_mcp_admin_api_r29.py | 已有 crm → 再登记 crm → 400 server_id_exists，原 Server 不变 | — |
| AC-001-03 | I-800, E-011 | INT, E2E | 同上; e2e | 20 个 admin 端点 × 匿名 / view / edit / manage → 匿名 401、view / edit 档越权 403（3.0.0 口径），快照零变化 | — |
| AC-001-04 | I-811, U-005, U-006 | INT, UNIT | 同上; unit/test_mcp_rules_r29.py | 标识名含空格 / 空 URL 等 → 400 并指出字段码，不落库（逐条列全部字段错误见 OBS-01） | — |
| AC-001-05 | I-860, I-1002 | INT | integration/test_mcp_admin_api_r29.py; test_mcp_compile_hotpath_r29.py | Server 停用 / 未启用 → 配置目录不列其工具；提交授权 → 400 mcp_server_unavailable | — |
| AC-001-06 | I-812, U-521, F-003, F-020 | INT, UNIT, FE | 同上; unit/test_mcp_store_r29.py; frontend | stdio / sse / http / 空等 6 种传输 → 400 transport_not_supported，Popen 计数 0，库层 CHECK 兜底，下拉仅 streamable_http | — |
| AC-002-01 | I-820, U-400, I-700, I-701, E-001 | INT, UNIT, E2E | 同上 | 测试连接 → ok + 协议版本 / 时代 / listChanged / 工具能力，记录验证时间；modern 与 legacy 均通过 | — |
| AC-002-02 | I-821, U-401, U-402, U-403, I-707 | INT, UNIT | 同上 | 不可达 / 超时 / 401 / 协议不兼容 / 无工具能力 → 对应类别；响应无凭证 / 主机 / 堆栈；启用 409 | — |
| AC-002-03 | I-822, U-404, E-010 | INT, UNIT, E2E | 同上 | 目标 169.254.169.254 → address_blocked，替身请求 0 | — |
| AC-003-01 | I-860, I-810 | INT | integration/test_mcp_admin_api_r29.py | 列表 / 详情字段齐全（状态、验证、分状态工具数、引用项目 / agent 数 = 1 / 1），无凭证明文 | — |
| AC-003-02 | I-842, E-009 | INT, E2E | 同上 | 仅开放 crm 的项目只见 crm；他 Server 详情 404 | — |
| AC-003-03 | I-801, I-800, I-842 | INT | 同上 | 匿名读 Server 列表 401；view / edit 档管理动作 403（I-800，Server 数据零变化）；view / edit 档读取仅见开放给本项目的 Server（I-842）。**已裁决**（CP-002 Q3=A，3.0.0）：原 OBS-03 待裁决说明作废 | — |
| AC-004-01 | I-823 | INT | 同上 | 只改说明与超时 → 工具仍 enabled，审计有 server.update；旧 expected_updated_at ⇒ 409 | — |
| AC-004-02 | I-824, E-003 | INT, E2E | 同上 | 改连接目标 → registered、4 工具全 needs_rereview、调用 0 次出站 | — |
| AC-004-03 | I-824, E-010 | INT, E2E | 同上 | 改为 10.0.0.5 → 400，原目标与工具状态不变 | — |
| AC-004-04 | I-800 | INT | 同上 | 配置者 PATCH → 403 | — |
| AC-004-05 | I-825 | INT | 同上 | 轮换凭证 → 详情只显示 configured 与新时间；审计与响应无旧 / 新值 | 两个测试令牌 |
| AC-005-01 | U-301, I-828 | UNIT, INT | unit/test_mcp_runtime_r29.py; integration | 停用 → 下一次调用被拒，出站 0；授权记录仍在 | — |
| AC-005-02 | I-828 | INT | 同上 | 启用先验证；验证失败保持不可用 | — |
| AC-005-03 | I-829 | INT | 同上 | 被引用时默认删除 → 409 server_in_use 列引用；一切不变 | — |
| AC-005-04 | I-829, I-830, E-003 | INT, E2E | 同上 | 强制删除 → 凭证清除、授权清理、定义文档 +1 版、仍可保存；清理失败 → 409 且已停用未删除 | — |
| AC-005-05 | I-829, U-302 | INT, UNIT | 同上 | 删除后调用 → 降级（短语为“外部工具不存在”，见 OBS-05），出站 0 | — |
| AC-005-06 | I-829 | INT | 同上 | 缺 confirm / 不一致 → 400 confirm_mismatch，不删除 | — |
| AC-006-01 | E-001, U-503, U-523, U-201, I-810 | E2E, UNIT | e2e; unit/test_mcp_store_r29.py; test_mcp_crypto_r29.py | canary 令牌全流程（响应 / 日志 / 审计 / 定义文档 / LLM 载荷 / 台账文件字节）命中 0；密文不含明文；主密钥不在台账字节中。真实 Fernet 见 U-221~225（本机 SKIP） | CANARY_TOKEN, SECRET_KEY |
| AC-006-02 | I-827, U-308, E-009 | INT, UNIT, E2E | 同上 | 项目专属凭证：A 设置、B 未设置 → B 得“凭证缺失”，出站 0 | — |
| AC-006-03 | I-825, U-203 | INT, UNIT | 同上 | 轮换后服务方收到新凭证；旧凭证被拒 | — |
| AC-006-04 | I-826, F-021, F-033 | INT, FE | 同上; frontend | 任何读取接口不含值；凭证输入校验；输入框 password、提交即清空。selfcheck `deploy_templates_have_no_secrets` 零命中见 e2e 报告 | — |
| AC-006-05 | E-007, U-321 | E2E, UNIT | 同上 | 401 → 降级文案不含状态码 / 服务方原文 / 凭证片段；审计类别 failed | — |
| AC-006-06 | I-817, U-204, U-212 | INT, UNIT | 同上 | 主密钥缺失登记带凭证 Server → 409 secret_key_missing，无明文落盘；不带凭证 Server 不受影响 | — |
| AC-007-01 | I-852, I-842 | INT | 同上 | 新登记未开放 → 项目看不到 | — |
| AC-007-02 | I-852, E-009, U-303 | INT, E2E, UNIT | 同上 | 开放给 A → A 可见 B 不可见；B 直接调用成功 0（含运行期新建项目 N=1） | — |
| AC-007-03 | I-853, E-009 | INT, E2E | 同上 | 项目专属 erp：B 查询 404、授权被拒、调用被拒，无信息泄露 | — |
| AC-007-04 | I-852, E-003, U-303 | INT, E2E, UNIT | 同上 | 取消开放 → 调用立即不生效，配置页标注“未对本项目开放”，保存不失败 | — |
| AC-007-05 | I-904 | INT | integration/test_mcp_regression_r29.py | 运行期新建项目（含顾问）→ 未开放任何 Server、外部授权数 0 | — |
| AC-008-01 | I-700, U-300 | INT, UNIT | integration/test_mcp_http_transport_r29.py | 真实 socket：Authorization: Bearer，令牌不在 URL | CANARY_TOKEN |
| AC-008-02 | I-814, I-705 | INT | 同上 | userinfo / file / ftp / javascript / 十六进制 IP 等 → 拒绝，回环服务端命中 0 | — |
| AC-008-03 | I-703 | INT | 同上 | 302 → 私有侧：不跟随、不读 Location，私有侧请求 0 | — |
| AC-008-04 | I-813 | INT | integration/test_mcp_admin_api_r29.py | oauth / basic 等 → 400 auth_kind_invalid | — |
| AC-008-05 | I-815, I-704, U-114 | INT, UNIT | 同上 | 公网明文 http → 400 且 DNS 解析 0 次；https 通过；名单内精确主机 + 端口的 http 通过 | — |
| AC-010-01 | I-820, U-410, I-702, U-001 | INT, UNIT | 同上 | 分页 3 工具 → 注册名 mcp__crm__*、展示名 mcp.crm.*、pending_review、含指纹 / schema | — |
| AC-010-02 | U-413, U-002 | UNIT | unit | 两 Server 同名 search 并存；search_knowledge 外部工具带前缀 | — |
| AC-010-03 | U-003 | UNIT | unit/test_mcp_rules_r29.py | 服务方自报内置名 → 注册名仍带登记标识名前缀 | — |
| AC-010-04 | U-411, U-010 | UNIT | unit | 非法名被排除（带原因），9 个合规保留 | — |
| AC-011-01 | I-842 | INT | integration | 按 state 筛选；详情含并列 observed / approved、注解标“服务方自报，未经核实” | — |
| AC-011-02 | I-842 | INT | 同上 | N=3 未开放 Server：项目侧泄露条数 0 | — |
| AC-011-03 | I-801, I-800, I-842 | INT | 同上 | 匿名读工具目录 401；view / edit 档审核 / 启用 / 风险裁定等管理动作 403、工具状态零变化；读取仅见开放项。**已裁决**（CP-002 Q3=A） | — |
| AC-012-01 | I-840 | INT | 同上 | 自称只读不预设只读（unknown）；审核审计含裁定人 / 级别 / 指纹 | — |
| AC-012-02 | I-840 | INT | 同上 | destructiveHint → side_effect | — |
| AC-012-03 | I-841, E-005 | INT, E2E | 同上 | 待审核工具：配置者启用 403；授权 400 mcp_tool_not_enabled | — |
| AC-012-04 | I-841 | INT | 同上 | 禁用后调用被拒，出站 0 | — |
| AC-013-01 | U-420, E-002, U-603, U-610, I-721 | UNIT, E2E, INT | unit; e2e; integration/test_mcp_listen_realsocket_r29.py | 描述变更（含新指令）→ needs_rereview；调用出站 0；差异可查；listen 通知 → 去抖 → 复审态；启用后保持协商值并启动监听（610，已翻转）；真实 socket 上 2 s 内恰好回调一次（721，已翻转，DEF-R29-007 已修复已验证） | — |
| AC-013-02 | U-422, U-601, I-851 | UNIT, INT | 同上 | 不支持通知：手动刷新 / 周期复核同样检出 | — |
| AC-013-03 | U-421 | UNIT | unit/test_mcp_catalog_r29.py | 仅注解变化也失效 | — |
| AC-013-04 | U-426, E-002 | UNIT, E2E | 同上 | 复审通过 → 自动恢复（新装配绑定新指纹）；驳回 → 保持失效 | — |
| AC-013-05 | E-002, U-305 | E2E, UNIT | e2e | 检测后 N=20 并发尝试放行 0；旧指纹绑定被拒 | — |
| AC-013-06 | U-424 | UNIT | unit | 新增工具 pending_review，无授权 | — |
| AC-013-07 | U-412, U-011 | UNIT | unit | 1000 工具 + 10 万字符描述 + 深嵌套：无崩溃，超限项排除，合规项保留 | — |
| AC-014-01 | U-425, E-002 | UNIT, E2E | unit; e2e | 撤下 → offline（含时间与原因），调用被拒；记录可查 | — |
| AC-014-02 | U-425, E-002 | UNIT, E2E | 同上 | 重现且指纹相同 → needs_rereview，不自动恢复 | — |
| AC-015-01 | U-311, U-313, I-1009, E-001 | UNIT, INT, E2E | unit/test_mcp_runtime_r29.py; integration | 固定 / 屏蔽参数不在 LLM 可见 schema；发出值 = 固定值 | — |
| AC-015-02 | U-311 | UNIT | unit | 30 个诱导值：生效次数 0 | — |
| AC-015-03 | U-312, E-009 | UNIT, E2E | 同上 | 两项目各自固定值互不串用 | — |
| AC-015-04 | I-844, E-005, U-427 | INT, E2E, UNIT | integration | 疑似租户参数未确认 → 400；确认后启用并审计 tenant_ack=1 | — |
| AC-015-05 | I-843, E-005 | INT, E2E | 同上 | 配置者改固定值 403；响应只回显键名 | — |
| AC-016-01 | I-1000, I-1001 | INT | integration/test_mcp_compile_hotpath_r29.py | 勾选授权 → 仅 kb-agent 的工具列表含外部工具；热生效 | — |
| AC-016-02 | I-1002 | INT | 同上 | 不存在 / 待复审 / 已下线 / 停用 / 未开放 / 禁用 → 逐条错误，整份不保存 | — |
| AC-016-03 | I-1003, E-009 | INT, E2E | 同上 | 跨项目授权被拒，错误不泄露描述 / schema | — |
| AC-016-04 | I-1000, I-1010 | INT | 同上 | 顾问未授权：越权调用被拒，出站 0；顾问被授权：调用成功且按回合计 5 次上限（I-1010，DEF-R29-005 已修复，已翻转，含未授权成对） | — |
| AC-016-05 | I-861, I-1110 | INT | integration/test_mcp_admin_api_r29.py; integration/test_mcp_access_levels_r29c.py | 匿名保存授权 401（I-1110，本轮新写）；view 档 403（I-861 / I-1110），两种情形配置版本与工具授权状态零变化；edit 档保存成功（正例） | — |
| AC-017-01 | I-1005, E-003 | INT, E2E | integration; e2e | 配置页标注失效原因；旧装配调用被拒 | — |
| AC-017-02 | I-1005 | INT | 同上 | 存在失效授权时保存无关配置成功，授权记录保留 | — |
| AC-017-03 | I-1005, E-002 | INT, E2E | 同上 | 复审通过后授权自动恢复；Server 删除则不恢复 | — |
| AC-017-04 | I-1005, U-305 | INT, UNIT | 同上 | 旧装配在失效后调用同样被拒（不依赖重启） | — |
| AC-018-01 | I-901, I-904 | INT | integration/test_mcp_regression_r29.py | 既有项目定义文档逐字不变 | — |
| AC-018-02 | I-904 | INT | 同上 | 新建项目（含顾问）：kb-agent 仅 search_knowledge，顾问空 | — |
| AC-018-03 | I-904, E-001 | INT, E2E | 同上 | 新发现 5 工具 + 已启用只读工具，无人操作 → 授权数不变 | — |
| AC-019-01 | U-300, E-001, I-1000 | UNIT, E2E | unit; e2e | 服务方收到原始工具名 + 校验后入参；答复引用结果；审计一条 | — |
| AC-019-02 | U-310 | UNIT | unit | 缺必填 / 类型错 → 不出站，可重试 | — |
| AC-019-03 | U-320, E-007 | UNIT, E2E | 同上 | isError → 围栏失败结果，整轮 200 | — |
| AC-019-04 | U-321, E-007 | UNIT, E2E | 同上 | 4 类故障各 5 次：降级短语固定，无状态码 / 原文 / 凭证，整轮 200 | — |
| AC-019-05 | U-323, U-050, E-007 | UNIT, E2E | 同上 | 文本 + 图片 + 资源链接 → 只采纳文本并标“已忽略 2 项” | — |
| AC-019-06 | U-051, U-323, U-324, U-325, I-708 | UNIT, INT | 同上 | 多字节正例；100 KB 与 60 KB ASCII：ok、正文+标注 ≤ 32768 字节、含“已截断”、围栏内；恰好等于上限不截断不标注（DEF-R29-002 已修复，已翻转） | — |
| AC-019-07 | U-322, E-007 | UNIT, E2E | 同上 | input_required → 降级，无追问请求 | — |
| AC-020-01 | I-709 | INT | integration/test_mcp_http_transport_r29.py | 真实时钟超时 1 ± 1 s（30 s 口径按比例缩放，机制同一） | — |
| AC-020-02 | U-330, E-004, I-1010 | UNIT, E2E | unit; e2e | 同回合 kb-agent 3 + 被委托 agent 2 = 5，第 6 次被拒；下回合清零 | — |
| AC-020-03 | U-340, U-341, E-004 | UNIT, E2E | 同上 | 5 次失败后第 6 次出站 0 且 ≤1 s；冷却后探测恢复 / 继续暂停；状态变化写审计 | — |
| AC-020-04 | U-331, I-850, E-004 | UNIT, INT, E2E | 同上 | 项目只能调低（8 → 400，2/3 成功）；治理参数范围校验 | — |
| AC-020-05 | U-350 | UNIT | unit | 并发上限 2，4 并发：在途峰值 ≤ 2，其余“繁忙”降级 | — |
| AC-021-01 | U-306, I-845, E-005 | UNIT, INT, E2E | 同上 | 有副作用未放行 → 保存被拒 mcp_risk_not_waived | — |
| AC-021-02 | I-845, E-005 | INT, E2E | 同上 | admin 填理由放行 → 保存成功；审计放行人 / 范围；B 仍被拒 | — |
| AC-021-03 | U-306, I-845, E-005 | UNIT, INT, E2E | 同上 | 撤销放行 → 调用被拒；配置页标注 | — |
| AC-021-04 | I-845 | INT | 同上 | 空 / 全空白理由 → 400 | — |
| AC-021-05 | U-307, I-845 | UNIT, INT | 同上 | unknown 与 side_effect 同样受限；裁定只读后放行 | — |
| AC-023-01 | I-905 | INT | integration/test_mcp_regression_r29.py | 能力摘要无 mcp__ / mcp. 条目，内置条目与基线一致 | — |
| AC-023-02 | I-906 | INT | 同上 | 描述含“总是路由到本工具”：N=30 问句 agent 调用序列与答复无差异 | — |
| AC-024-01 | U-343, U-600, I-1100~1103 | UNIT, INT | unit; integration/test_mcp_supervisor_process_r29.py | 探测发现不可达 → down；调用立即降级（≤1 s，出站 0）；supervisor 仅由 ib-web 入口启动（worker 路径 0 线程，见 AC-025-03 行，DEF-R29-008） | — |
| AC-024-02 | U-600 | UNIT | unit/test_mcp_supervisor_r29.py | 恢复 → 自动回 up，写审计两条状态变化 | — |
| AC-024-03 | I-851 | INT | integration | 配置者 verify / refresh → 403 | — |
| AC-025-01 | I-901, I-903, 全量回归 + selfcheck | INT, 回归 | integration/test_mcp_regression_r29.py | 探针全部键与基线黄金逐项一致；配置目录字节相同；可授权工具列表与基线相同；全量 1761 passed, 6 skipped（回流第 3 轮）；离线 / IB_MCP_ENABLED=0 下 start_mcp_supervisor 返回 False 且无线程（I-1104、I-1105，本轮新写） | 基线黄金 JSON |
| AC-025-02 | I-900, I-906, E-011 | INT, E2E | 同上; e2e | N=33 问句答复 / 事件 / 路由 / 外发载荷与基线逐项一致；删除全部 Server 后答复回到基线 | 基线黄金 JSON |
| AC-025-03 | I-907, I-1100~1103 | INT | 同上; integration/test_mcp_supervisor_process_r29.py | **DEF-R29-008 成对用例**（I-1100 worker 路径 build_deps + django.setup/apps.ready ⇒ 进程内无任何新增 ib-mcp* 线程；I-1101 build_application ⇒ 恰好 1 个 ib-mcp-supervisor，幂等，close 后退出；I-1102 同一 deps 先 0 后 1；I-1103 start_mcp_supervisor 返回 True/False 契约）。非离线装配 + 3 个不可达 Server 重启：启动有界、网络尝试 0、N=20 对话 20/20、关机无线程残留。**启动耗时增量待目标机校准（标“未验收”）** | — |
| AC-025-04 | I-800, E-011 | INT, E2E | 同上 | 管理动作全集 × 4 类身份：未授权成功 0，匿名 401、view / edit 档越权 403（3.0.0 口径） | — |
| AC-026-01 | U-362, E-001 | UNIT, E2E | unit; e2e | N≥30 次调用：审计字段齐全率 100%，凭证与入参原文 0 命中 | — |
| AC-026-02 | I-862, E-003 | INT, E2E | integration; e2e | 按 Server + 时间范围过滤；Server 删除后历史可查 | — |
| AC-026-03 | I-802, I-1111, U-506 | INT, UNIT | 同上; integration/test_mcp_access_levels_r29c.py | **正例按项目 manage 档（read_audit）口径**：manage 档账户查询只得本项目记录（强制覆盖 project_id，他项目 0 条）；**edit 档 → 403、view 档 → 403**（I-802、I-1111 均有）；匿名 401。注：AC 原文“项目配置者”在此指 manage 档——`src/ibweb/mcp_views.py:722` `require_level(request, "read_audit")`，档位表 `REQUIRED_LEVEL["read_audit"]=="manage"`（`tests/unit/test_config_access_r26.py` TC-UNIT-R26-050 锁定，改动即失败）；edit 档项目配置者**没有**审计读取权。已裁决（CP-002 Q3=A；GR-A-003 条件） | — |
| AC-026-04 | I-902, I-901 | INT | integration/test_mcp_regression_r29.py | 已启用 Server → /healthz/deps 列主机与数据类别；未登记 / 仅登记 / 停用后与基线逐字节相同 | — |
| AC-027-01 | U-053, U-052, U-042, U-700~706, E-006 | UNIT, E2E | unit/test_mcp_rules_r29.py; unit/test_mcp_desc_channels_r29c.py; e2e | **3.0.0 分通道口径（ADR-R29-11）**。返回内容通道：注入集 N=23 的返回 / 错误文本围栏，围栏被提前闭合次数 0（含用零宽 / 方向字符拆分标记、多 text 项伪造闭合、超限截断边界，U-052/053/704/705/706）。描述通道：工具描述 ≤ 1000、参数描述 ≤ 300（边界对 299/300/301、999/1000/1001，含嵌套属性，U-701/702）；注入集 N=23 的描述无控制 / 零宽字符、不超上限、产品不追加围栏（U-703）；合规短描述原样不被围栏包裹（U-700 正例）；提示词 / 工具集 / 委托序列不变（E-006） | 23 条注入样例 |
| AC-027-02 | U-120, U-121, U-122, E-010, I-705 | UNIT, INT, E2E | unit/test_mcp_netguard_r29.py; e2e | 单元 38 条 + E2E 33 条地址拒绝集；先公后私重绑；放行 0；名单空时内网放行 0 | — |
| AC-027-03 | U-123, U-124, I-815, E-010 | UNIT, INT, E2E | 同上 | 10.0.0.8:9000 精确放行；别端口 / 别主机仍拒；回环 / CGNAT / ULA 经名单可登记 | — |
| AC-027-04 | E-008, U-370 | E2E, UNIT | e2e; unit | N=30 会话 canary 外发命中 0（仅声明参数）；LLM 添加的未声明键外发 0 次，fixed_args 覆盖、hidden 不外发，schema 无 properties 时 LLM 入参全丢（DEF-R29-004 已修复，已翻转） | 4 个 canary 串 |
| AC-027-05 | E-009 | E2E | e2e | 双项目 + 运行期新建项目：B 指向 A 的 Server / 凭证 / 固定入参成功 0；A 数据在 B 响应 0 | — |
| AC-027-06 | E-002, U-305 | E2E, UNIT | 同上 | 待复审 / 禁用 / 删除后 N=20 并发放行 0；指纹不符被拒 | — |
| AC-027-07 | U-125, I-816, E-010 | UNIT, INT, E2E | 同上 | 元数据 / 链路本地即使在名单内：effective=false，登记 / 测试连接 / 传输均拒，请求 0 | — |

**覆盖统计**：113/113 条有效 AC 均有至少一条用例映射；其中 AC-006-01（真实 Fernet 部分，本机 SKIP）、AC-020-01（按比例缩放）、AC-025-03（启动耗时待目标机校准）、AC-027-01（3.0.0 已按 ADR-R29-11 修订，描述通道与返回通道均有可测项覆盖，不再有“部分满足”）、AC-013-01（真实 socket 通知通道已由 TC-INT-R29-721 翻转验证，回环明文；HTTPS 未验证，见 MV-09）存在“部分满足”说明，已在各层报告逐条列出。

**A12（GR-C-004 条件）真实 socket 阻塞 SSE 流**：可行，已落实为 `tests/integration/test_mcp_listen_realsocket_r29.py`（TC-INT-R29-720 / 721，close-delimited 与 chunked 两种形态参数化，仅 127.0.0.1）。第 1 轮结论：A12 假设被证伪，登记 DEF-R29-006 / 007。第 2 轮：GROUP_C 修复（`read1` + 关闭前 `shutdown(SHUT_RDWR)`），720 / 721 翻转后 4 实例全部 PASS（连跑 3 次稳定）。仍未覆盖：A13 的 HTTPS 路径（`SSLSocket` 上的 `read1` / `shutdown`；离线、仅回环明文）——GR-C-005 条件，列入 e2e 报告人工验证清单 MV-09；目标机真实长连接复验见 MV-08。

## 测试数据需求

| 数据 | 来源 | 说明 |
|---|---|---|
| 主密钥 `SECRET_KEY` | 测试内生成的 Fernet 形态常量（32 个 `k` 的 urlsafe-base64） | 非真实密钥；`mcp_r29_support.py` |
| 凭证 canary `CANARY_TOKEN` 等 | 测试内常量 | 非真实凭证；用于“命中数 = 0”断言 |
| 基线黄金 `integration/mcp_r29_baseline_golden.json` | 由基线 commit b4fa3a3 的 src 树（`git archive b4fa3a3 src`）运行 `tests/advisor_r28_probe_support.py` 生成（P-TE-011 手法） | 期望值不取自被测代码；24 669 字节 |
| 注入集 23 条 / SSRF 目标 38 + 33 条 | 测试内常量 | 见 unit_test_report / e2e_test_report |
| [DATA_REQUIRED] 真实 `cryptography` 环境 | 目标机 / CI | 真实 Fernet 契约（U-221~225）需 `cryptography>=42,<51`；本机无，见人工验证清单 |

## 不可测项

| AC / 项 | 原因 |
|---|---|
| AC-025-03 启动耗时增量 | `[NOT_TESTABLE: 需目标机实测校准]`——自动化只验证“不触网 + 有界 + 对话 100%”，耗时数字标“未验收” |
| 真实 MCP Server 互通 / 真实 TLS CA 链 | `[NOT_TESTABLE: 无真实 Server，禁止出网]`——人工验证清单 |
| 真实 Fernet 执行（本机） | 本机 SKIP（`cryptography` 未安装，且不得 pip install）；CI 以 `IB_REQUIRE_CRYPTO=1` 强制运行 |
| DeepSeek 函数名字符集（A-R29-2） | `[NOT_TESTABLE: 禁止调用真实 DeepSeek]`——仅断言注册名匹配 `[A-Za-z0-9_-]{1,64}` 假设；目标机探针见人工验证清单 |
| 浏览器内交互 | `[NOT_TESTABLE: 无浏览器 E2E 框架]`——人工验证清单 |
| 真实模型抗注入能力 | `[NOT_TESTABLE: LLM 为脚本化替身]`——本轮验证管线隔离与围栏，不评估模型本身 |
| ~~AC-003-03 / 011-03 / 026-03 的“终端提问用户”~~ | **已裁决，移出不可测项**（CP-002 Q3=A，user_stories 3.0.0）：AC 措辞已改为“匿名 401；view / edit 档越权 403”，计入通过率分母 |

## 现有测试调整

| 文件:行 | 原断言 → 调整 | 责任与结论 |
|---|---|---|
| `src/frontend/tests/advisor_r28.test.js:260-261`（TC-FE-R28-023） | `SYSTEM_ORDER = [... 'web-governance']`（四项）→ `/const SYSTEM_ORDER = \['accounts', 'projects', 'llm-key', 'web-governance', 'mcp'\];/`（五项整行精确匹配） | GR-C-001 授权的契约变更（MOD-R29-22 要求 `SYSTEM_ORDER` 末尾追加 `'mcp'`），**由 test-engineer 接管**。本次核对：无可选组、无宽松正则；其后 `order.slice(0,3)` 既有三项相对顺序断言原样未动；`ConsoleLayout.vue` 为五项字面；新增 TC-FE-R29-031 另行断言“严格五项且 mcp 在末尾”。未放宽 |
| `tests/integration/test_mcp_http_transport_r29.py`（本轮新写文件内） | 回环服务增加 `handle_error` 静默 | 仅测试辅助，消除客户端提前断开（读取上限 / 超时用例）时 socketserver 线程向 stderr 打印的回溯；断言未改 |

其余既有测试零改动。

## 缺陷登记（产品缺陷，不改产品代码）

| DEF | 级别 | 位置 | 状态 / 对应用例 |
|---|---|---|---|
| DEF-R29-001 | MINOR | `src/ib/mcp/schema_lite.py:253-262`、`src/ib/mcp/binding.py:53-54`（工具 / 参数描述仅净化 + 截断；原 AC-027-01 字面要求围栏形式） | **CLOSED（依据：需求修订，非代码修复）**——用户 CP-002 Q2=A，AC-027-01 已按 ADR-R29-11 修订（user_stories 3.0.0）；TC-UNIT-R29-042 及本轮 TC-UNIT-R29-700~706 与新 AC 措辞一致 |
| DEF-R29-002 | MAJOR | `src/ib/mcp/result.py`、`src/ib/mcp/client.py` | **已修复已验证**：翻转用例 TC-UNIT-R29-324 / 325 |
| DEF-R29-003 | MAJOR | `src/ib/mcp/client.py`、`src/ib/mcp/supervisor.py`、`catalog.py` | **已修复已验证**：翻转用例 TC-UNIT-R29-609 / 610（离线替身口径；真实 socket 残留见 DEF-R29-006） |
| DEF-R29-004 | MAJOR | `src/ib/mcp/runtime.py` | **已修复已验证**：翻转用例 TC-UNIT-R29-370、TC-E2E-R29-008 |
| DEF-R29-005 | MINOR | `src/ib/orchestration/dag.py` | **已修复已验证**：翻转用例 TC-INT-R29-1010 |
| DEF-R29-006（新增） | MAJOR | `src/ib/mcp/transport.py:139`、`:121-135`；`src/ib/mcp/client.py:436-445`（真实 socket：`resp.close()` 不能唤醒阻塞读取，stop 后监听线程残留） | **已修复已验证**（回环明文，close-delimited 与 chunked）：翻转用例 TC-INT-R29-720；HTTPS 路径未验证，见 MV-09 |
| DEF-R29-007（新增） | MAJOR | `src/ib/mcp/transport.py:129`（`resp.read(8192)` 阻塞到凑满块或连接关闭，list_changed 事件滞留） | **已修复已验证**（回环明文，close-delimited 与 chunked）：翻转用例 TC-INT-R29-721；HTTPS 路径未验证，见 MV-09 |

| DEF-R29-008（回流第 3 轮） | MAJOR | `src/ibweb/composition.py` `_assemble`（ib-web 与 ib-worker 共用装配体）曾启动 MCP supervisor；ib-worker 进程出现 `ib-mcp-supervisor` 线程，违反 module_design.md:866 | **已修复已验证**（GROUP_C-006：启动点移到 `build_application`:893-895，新函数 `start_mcp_supervisor` :1640）；成对用例 TC-INT-R29-1100~1105（`tests/integration/test_mcp_supervisor_process_r29.py`） |

## 回流第 3 轮（缺陷回流第 3 轮复测；用户经 CP-002 额外授权，原话“全部按推荐”，经主会话转述）

1. **DEF-R29-008 成对用例**（M-PM-001 / M-PM-002）：新文件 `tests/integration/test_mcp_supervisor_process_r29.py`（基名全局唯一），夹具 = 非离线真实装配（持久化 SQLite 台账 + 真实 `HttpMcpTransport` + 真实 supervisor，台账内预置一个不可达已启用 Server 使 supervisor “有活可干”），套接字 connect / getaddrinfo / create_connection 打桩（尝试数 0），不 monkeypatch 被测函数。负例强度 ≥ 缺陷原描述：断言整个进程内新增 `ib-mcp*` 线程数 = 0（不仅是名为 `ib-mcp-supervisor` 的线程），且 `supervisor._thread is None`；worker 路径 = `build_deps` + `ibweb.worker._setup_django()` + `IbWebConfig.ready()`。正例 = `build_application` 恰好 1 个存活 daemon 线程，二次调用仍 1，`close()` 后无残留。边界 = 离线、`mcp_enabled=False`（dict 配置源下的 IB_MCP_ENABLED=0）返回 False 且无线程；`mcp_enabled` 打开的同夹具才有线程（防假通过）。限制：未起真实 ib-worker 子进程；`apps.ready()` 在“未装配”分支（自行 `build_deps()`）依赖外部配置源，离线测试环境无法覆盖非离线配置，故以“已装配后调用 ready / _setup_django”等价路径代替（目标机验证见 e2e 报告 MV-10）。
2. **DEF-R29-001 关闭**（需求修订）：见缺陷表。TC-UNIT-R29-042 原断言（参数描述 ≤ 300、无控制 / 零宽字符）与新 AC 措辞一致，无需改；原 AC 未覆盖的可测项由 `tests/unit/test_mcp_desc_channels_r29c.py`（U-700~706，35 个收集项）补齐：工具描述 ≤ 1000（含边界对）、参数描述 ≤ 300（含嵌套）、注入集 N=23 描述净化与“不加围栏”、返回围栏不可被零宽 / 方向字符拆分的标记提前闭合。期望值来自 ADR-R29-11 常量与围栏常量，不取自被测输出。说明：描述通道不要求置换描述里的围栏标记（AC 未要求；该通道不是围栏内容），本轮测试据此不作该断言（首跑曾多断言，属测试写错，已按 AC 文本修正）。
3. **AC 口径同步**（CP-002 Q3=A）：AC-001-03 / 003-03 / 011-03 / 016-05 / 025-04 / 026-03 映射已更新（见上表）；原 OBS-03 待裁决说明改为已裁决。新增 `tests/integration/test_mcp_access_levels_r29c.py`：I-1110（AC-016-05 匿名保存授权 401 / view 403 / edit 200，零变化）、I-1111（AC-026-03 manage 档 200 只见本项目、edit / view 档 403、匿名 401）。AC-026-03 的 edit 档 403 另有既有 I-802。
4. 新写用例：单元 +35（U-700~706，含参数化实例）、集成 +8（I-1100~1105 其中 1105 为单实例，共 6 + I-1110~1111 共 2）、E2E +0。

## 回归（既有用例，单列）

全量 `pytest tests` 中 1358 条既有用例作为回归，见 e2e_test_report“全量回归”（回流第 3 轮：1761 passed, 6 skipped，收集 1767，相对基线（1718 passed / 6 skipped / 收集 1724）新增失败 0；新增 43 例全部 PASS）；selfcheck 76/77（既有 FAIL `core_framework_free`）与前端 180/180。
