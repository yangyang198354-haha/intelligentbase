<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-06T21:29:42+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/integration_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（REV-29：agent 工具调用的 MCP 适配）

> 覆盖重写 REV-28 的 3.0.0 APPROVED 版本（REWORK_AUTHORIZED；原版已归档于 `docs/sdlc/intelligentbase/archive/rev28/`）。

## 摘要

critical path 口径：替代（项目无浏览器 E2E 框架；用最高层可执行的端到端级用例——真实账户鉴权 + 真实管理端点 + 真实发布协议 + 真实运行时 + 真实 SSE 流式问答的多步 HTTP/SSE 旅程；MCP Server / DNS / LLM 为替身）

- 执行时间：2026-11-06 缺陷回流第 3 轮复测（GROUP_D-005），单元、集成层门控均 PASSED 之后的最后一次执行（`77 passed in 9.55s`）；环境同单元层；命令 `$P -m pytest tests/e2e -q -p no:cacheprovider`；此后未再修改任何测试文件。本轮 E2E 层无新写用例（回流第 3 轮的新增用例在单元 / 集成层，见 3 份报告）
- **本层总计**：total = pass + fail + skip + blocked + not_testable = 77 + 0 + 0 + 0 + 0 = **77**（独立实测收集数 77，一致）；其中新写 11 = 11 pass；既有 66 全部 pass（77 − 11）
- 通过率 = pass / (pass + fail + blocked) = 77 / (77 + 0 + 0) = **1.00**
- **critical path 覆盖率** = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = **23 / 23 = 1.00**（Must：US-001~008、010~021、025、026、027；各故事所在旅程见下表）；**critical path 通过率** = 11 / 11 = **1.00**（11 条新写旅程，均真实执行）
- 判定模式 baseline：本层相对基线零新增失败且新写全部通过；**本层门控：PASSED**；全量回归新增失败 = 0
- 缺陷冻结：全套件 **0 条**。DEF-R29-001 已 **CLOSED**（需求修订，CP-002 Q2=A）；DEF-R29-008 已修复已验证（成对用例 TC-INT-R29-1100~1105）；当前无待决产品缺陷
- 待人工验证项（critical path 内）：0 条自动化不可替代的 Must 旅程；浏览器内交互 6 项列入「人工验证清单」（非 critical path 口径，均为 UI 层）

| Must Have 故事 | 所在 E2E 旅程 |
|---|---|
| US-001/002/003/006/007/008/010/011/012/015/016/018/019/026 | TC-E2E-R29-001 |
| US-013/014/017/027 | TC-E2E-R29-002 |
| US-004/005/007/017/026 | TC-E2E-R29-003 |
| US-020 | TC-E2E-R29-004 |
| US-012/015/021 | TC-E2E-R29-005 |
| US-027/019 | TC-E2E-R29-006 |
| US-019/006 | TC-E2E-R29-007 |
| US-027/006/026 | TC-E2E-R29-008 |
| US-007/011/015/016/027 | TC-E2E-R29-009 |
| US-027/008/002/004 | TC-E2E-R29-010 |
| US-025 | TC-E2E-R29-011 |

Should Have 故事 US-023、US-024 不入 critical path（由集成 / 单元层覆盖，另在 TC-E2E-R29-004 触及 US-024）。

## 全量回归

| 命令（`$P` = `/root/.venvs/intelligentbase/bin/python`） | 结果（计数行 / 结论行原样） | 相对基线新增失败 |
|---|---|---|
| `$P -m pytest tests -q -p no:cacheprovider` | `1761 passed, 6 skipped in 91.97s (0:01:31)`；独立收集数 1767 | **0**（基线 1718 passed / 6 skipped / 收集 1724；1724 + 新写 43 = 1767 = 1761 + 6；新写 43 = 单元 35 + 集成 8，全部 PASS） |
| `$P -m pytest tests/unit -q` | `1091 passed, 6 skipped in 16.32s` | 0 |
| `$P -m pytest tests/integration -q` | `578 passed in 64.02s` | 0 |
| `$P -m pytest tests/e2e -q` | `77 passed in 9.55s` | 0 |
| `$P -m pytest tests/agents -q`（套件契约） | `15 passed in 0.08s` | 0 |
| `$P -m compileall -q src` | rc=0 | 0 |
| `$P src/scripts/selfcheck.py` | `自检结果：76/77 通过`；`失败项：- core_framework_free … 引入了第三方顶层包：sitecustomize` | 0（基线 76/77，唯一 FAIL `core_framework_free` 为基线既有——环境注入的 sitecustomize，非本轮引入） |
| `(cd src/frontend && npm test)` | `# tests 180` / `# suites 31` / `# pass 180` / `# fail 0` / `# skipped 0` | 0（本轮未改前端；`npm run build` 本轮未重跑，前端源码未改） |

分层用例数（M-TE-001，独立实测，不与前端 / selfcheck 并算）：单元 1097（既有 805 + 新写 292）、集成 578（既有 472 + 新写 106）、E2E 77（既有 66 + 新写 11）；合计 1752 + tests/agents 15 例 = 1767（`--collect-only` 全量 1767）。算术：1097 + 578 + 77 = 1752，1767 − 1752 = 15 = tests/agents 套件契约；全量 1761 pass + 6 skip + 0 fail + 0 blocked + 0 not_testable = 1767。SKIP 6 条（全部为 `test_mcp_crypto_fernet_r29.py`，原因见 unit_test_report：cryptography 未安装且不得 pip install；CI 以 `IB_REQUIRE_CRYPTO=1` 必跑），无 xfail；不计入通过率分母。

## 用户旅程

通用环境（以下 11 条同）：Django 测试客户端 + 真实账户鉴权（`ibweb.accounts.policy`，admin / 项目 manage / edit / view 档）+ 真实管理端点 + 真实发布协议与热编译 + 真实 langgraph 运行时 + SSE 问答；MCP Server 为产品自带 `FakeMcpServer` 替身，DNS 为 `FakeResolver`，LLM 为脚本化替身；凭证全部为测试假值；不连任何外部网络（TC-INT-R29-907 另以 socket 打桩证明零网络尝试）。下表“期望 / 实际”列的实际值即该用例断言（均已执行通过）。

### TC-E2E-R29-001: 管理员接入 MCP Server → 配置者授权 → 客户提问得到引用外部结果的答复
- 关联：US-001/002/003/006/007/008/010/011/012/015/016/018/019/026；AC-001-01、002-01、006-01、010-01、012-01、015-01、016-01、018-03、019-01、026-01
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | admin 登记 `crm`（Bearer 令牌） | 201；状态“未启用”；令牌只显示已设置 | 与期望一致 | PASS |
| 2 | 测试连接 / 启用 | 协商结果展示；发现 3 工具，注册名 `mcp__crm__*`，状态待审核 | 与期望一致 | PASS |
| 3 | 项目配置者在未开放前查询 | 看不到 `crm` 及其工具 | 与期望一致 | PASS |
| 4 | admin 审核 + 裁定风险 + 固定 tenant 入参，开放给项目 | 工具 enabled；LLM 可见 schema 不含 tenant | 与期望一致 | PASS |
| 5 | 配置者保存授权并发布 | 差异清单仅 kb-agent 新增 `mcp__crm__get` | 与期望一致 | PASS |
| 6 | 客户 SSE 提问 | 200；答复引用外部结果；替身收到原始工具名 + 固定 tenant + Bearer 头 | 与期望一致 | PASS |
| 7 | 查审计 / 扫 canary | 审计字段齐全；canary 令牌在响应 / 日志 / 审计 / 定义文档 / LLM 载荷命中 0 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-002: rug-pull 旅程（变更检测、复审、下线、重现）
- 关联：US-013/014/017/027；AC-013-01~05、014-01/02、017-01/03、027-06
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 工具在用并已授权；服务方改描述（含新指令）；admin 刷新 | 工具转待复审；差异清单可查 | 与期望一致 | PASS |
| 2 | 客户提问 | 调用被拒，替身 `tools/call` 数 0；答复含降级说明；HTTP 非 5xx | 与期望一致 | PASS |
| 3 | 检测后 N=20 并发尝试 | 放行次数 0 | 0 | PASS |
| 4 | 无关配置保存 | 成功，失效授权记录保留 | 与期望一致 | PASS |
| 5 | 复审通过 | 授权自动恢复，下一次调用成功（正例） | 与期望一致 | PASS |
| 6 | 工具被撤下 / 重现且指纹相同 | 已下线（含原因）；重现 → 待复审，不自动恢复 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-003: 变更连接目标 → 取消开放 → 删除（被引用拒绝 / 强制清理）
- 关联：US-004/005/007/017/026；AC-004-02、005-03/04/05、007-04、017-01、026-02
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 改连接目标 | Server 待验证；工具全部待复审；调用被拒 | 与期望一致 | PASS |
| 2 | 取消对项目的开放 | 调用立即不生效，配置页标注，保存不失败 | 与期望一致 | PASS |
| 3 | 删除被引用 Server | 409 列出引用，一切不变 | 与期望一致 | PASS |
| 4 | 强制删除 + 二次确认 | 授权清理、定义文档 +1 版、配置仍可保存 | 与期望一致 | PASS |
| 5 | 客户提问 / 查审计 | 降级、非 5xx；历史审计仍可查 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-004: 回合预算跨 agent、熔断、项目只能调低
- 关联：US-020/024；AC-020-02/03/04、024-01
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 同一用户回合 kb-agent 3 次 + 被委托 agent 2 次，再发第 6 次 | 第 6 次被拒、替身不增加；下一回合清零后首次可发（正例） | 与期望一致 | PASS |
| 2 | 连续 5 次失败后第 6 次 | 出站 0，≤1 s 降级；冷却后恢复 | 与期望一致 | PASS |
| 3 | 项目把上限调到 2 / 调高于全局 | 第 3 次被拒 / 保存 400 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-005: 有副作用工具受限 → admin 按项目放行 → 撤销；租户参数确认
- 关联：US-012/015/021；AC-012-03、015-04/05、021-01~04
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 待审核工具授权 | 403 / 逐条报错 | 与期望一致 | PASS |
| 2 | 疑似租户参数未确认就启用 | 400；确认后启用 | 与期望一致 | PASS |
| 3 | 配置者保存有副作用工具 | 被拒 | 与期望一致 | PASS |
| 4 | admin 填理由放行项目 A → 保存并调用 | 成功（正例）；项目 B 仍被拒 | 与期望一致 | PASS |
| 5 | 撤销放行 | 调用被拒，替身不增加 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-006: 提示注入集 N=23
- 关联：US-027/019；AC-027-01、019-03
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 23 条注入（描述藏指令 / 返回与错误诱导调用、外发、忘记规则、委托）逐条提问 | 注入文本只在围栏内；系统提示词、工具集、被调用 agent 序列与对照组逐项相同；答复无提示词原文；HTTP 200 | 与期望一致（LLM 为脚本化替身，仅验证管线隔离） | PASS |
- 结论：PASS

### TC-E2E-R29-007: 降级矩阵（不可达 / 超时 / 鉴权失败 / 协议错误各 5 次，isError，追问，非文本）
- 关联：US-019/006；AC-019-03/04/05/07、006-05
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 4 类故障 × 5 次 | 整轮 200、无 5xx；答复含降级说明；无状态码数字 / 服务方原文 / 凭证片段 | 与期望一致 | PASS |
| 2 | isError / 追问 / 非文本 | 失败结果经围栏；追问按降级；“已忽略 N 项非文本内容” | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-008: 外发载荷 canary N=30
- 关联：US-027/006/026；AC-027-04、026-01
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 知识库 / 历史 / 他项目 / 提示词植入 canary，30 条会话 | 发往替身的载荷 canary 命中 0（仅已声明参数 q）；审计无入参原文 | 0 命中 | PASS |
| 2 | ③ LLM 自行添加 schema 未声明的键 `leak`（值为 canary） | 不外发：替身收到的载荷恰为 `{"q":"x"}`，全部外发载荷 canary 命中 0；声明键 q 照常外发（正例） | 与期望一致（**已翻转**，DEF-R29-004 已修复已验证） | PASS |
- 结论：PASS

### TC-E2E-R29-009: 双项目隔离（含运行期新建项目）
- 关联：US-007/011/015/016/027；AC-007-02/03、011-02、015-03、016-03、027-05
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | B / 运行期新建项目 N 查询、授权、直接调用 A 的专属 Server 与仅开放给 A 的 `crm` | 不可见（404 / 空）、授权被拒、调用成功 0；A 的数据在 B 响应 0 | 与期望一致 | PASS |
| 2 | A、B 各自固定不同 tenant | 各自替身记录各自的值（正例）；B 读不到 A 的凭证 / 固定入参 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-010: SSRF 拒绝集 N=33 与允许名单
- 关联：US-027/008/002/004；AC-027-02/03/07、008-02/03/05、002-03、004-03
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 33 个危险目标登记 / 变更 / 测试连接 | 放行 0；替身请求 0 | 0 / 0 | PASS |
| 2 | 名单放行 `10.0.0.8:9000`；别端口 / 别主机；元数据入名单 | 精确放行（正例）；别端口 / 别主机仍拒；元数据仍拒 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-R29-011: 权限矩阵旅程与回到基线
- 关联：US-025；AC-025-04、025-02
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理动作全集 × 匿名 / view / edit / manage / admin | 未授权成功 0；匿名 401、越权 403；admin 成功（正例） | 与期望一致 | PASS |
| 2 | admin 删除全部 Server 后问答 | 答复与从未登记的对照逐字相同；`/healthz/deps` 回到基线字节 | 与期望一致 | PASS |
- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-R29-001 | MINOR | 工具 / 参数描述仅净化 + 截断，未以围栏形式进入 LLM 输入（原 AC-027-01 字面要求围栏；设计 ADR 取净化方案） | TC-UNIT-R29-042、700~706 | `src/ib/mcp/schema_lite.py:253-262`、`src/ib/mcp/binding.py:53-54` | **CLOSED（依据：需求修订，非代码修复）**：用户 CP-002 Q2=A，AC-027-01 已按 ADR-R29-11 修订（user_stories 3.0.0：返回内容围栏；描述净化截断 ≤1000 / ≤300、不加围栏）；用例断言与新 AC 一致 |
| DEF-R29-002 | MAJOR | 100 KB 文本被降级 / ASCII 超限静默截短无标注（AC-019-06） | TC-UNIT-R29-324 / 325 | `src/ib/mcp/result.py`、`src/ib/mcp/client.py` | **已修复已验证**（翻转用例 TC-UNIT-R29-324、325） |
| DEF-R29-003 | MAJOR | refresh 覆盖协商值致监听线程永不启动；`stop()` 后监听线程残留（离线替身口径） | TC-UNIT-R29-609 / 610 | `src/ib/mcp/client.py`、`src/ib/mcp/supervisor.py` | **已修复已验证**（翻转用例 TC-UNIT-R29-609、610；真实 socket 口径见 DEF-R29-006） |
| DEF-R29-004 | MAJOR | LLM 添加的未声明键被外发（AC-027-04 / REQ-NFUNC-009） | TC-UNIT-R29-370、TC-E2E-R29-008 ③ | `src/ib/mcp/runtime.py` | **已修复已验证**（翻转用例 TC-UNIT-R29-370、TC-E2E-R29-008） |
| DEF-R29-005 | MINOR | 顾问被授权外部工具后调用恒被拒（`no_turn_scope`） | TC-INT-R29-1010 | `src/ib/orchestration/dag.py` | **已修复已验证**（翻转用例 TC-INT-R29-1010） |
| DEF-R29-006 | MAJOR | 真实 socket 上 `stop` 不能结束监听线程（`close=conn.close` 无法唤醒另一线程里阻塞的 `resp.read()`） | TC-INT-R29-720（已翻转） | `src/ib/mcp/transport.py` | **已修复已验证**（GROUP_C 第 2 轮：关闭前 `shutdown(SHUT_RDWR)`；回环明文，close-delimited 与 chunked；HTTPS 未验证，见 MV-09） |
| DEF-R29-007 | MAJOR | 真实 socket 上 `list_changed` 通知滞留（`resp.read(8192)` 阻塞到凑满块） | TC-INT-R29-721（已翻转） | `src/ib/mcp/transport.py` | **已修复已验证**（GROUP_C 第 2 轮：`read1`；回环明文，close-delimited 与 chunked；HTTPS 未验证，见 MV-09） |

| DEF-R29-008 | MAJOR | `_assemble`（ib-web / ib-worker 共用）启动 MCP supervisor，ib-worker 进程出现 `ib-mcp-supervisor` 线程（违反 module_design.md:866） | TC-INT-R29-1100（负例）/ 1101~1103（正例与契约）/ 1104~1105（边界） | `src/ibweb/composition.py`（原 `_assemble` 末尾；现 `build_application`:893-895、`start_mcp_supervisor` :1640） | **已修复已验证**（GROUP_C-006；成对用例见集成报告边界 5） |

当前待决缺陷：**0**（DEF-R29-001 CLOSED 需求修订；DEF-R29-008 已修复已验证）。本轮未发现新增产品缺陷。缺陷冻结用例 0 条。

## 人工验证清单

本轮 MCP 为公开协议（非画像 P11-3 闭源 API）；自动化一律使用替身。以下为无法自动化的验证项：

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | CR-009、US-001/003/010~012 | 浏览器打开 #/system/mcp：登记 → 测试连接 → 启用 → 发现 → 审核 → 开放 | 页面可操作；凭证输入框为 password、提交后清空、列表只显示“已设置”；传输下拉只有 streamable_http | 浏览器 + 目标机前端构建 | 否（UI 层） |
| MV-02 | US-016/017/021 | 配置页勾选外部工具、查看失效徽标、风险置灰 | 外部工具按 Server 分组；有副作用 / 未知置灰；失效授权显示原因 | 浏览器 | 否 |
| MV-03 | US-005 | 删除对话框输入标识名二次确认并勾选“强制删除” | 未输入标识名按钮不可用；强制删除后授权清理 | 浏览器 | 否 |
| MV-04 | A-R29-2 / TBD-R29-2 | 目标机契约探针：LLM 端点对函数名 `mcp__<server>__<tool>` 的字符 / 长度约束 | 端点接受注册名（≤64、`[A-Za-z0-9_-]`） | 目标机 + 真实 DeepSeek Key（由用户执行） | 否 |
| MV-05 | AC-006-01、checklists B30 | 目标机 `pip show cryptography` 版本在 >=42,<51；import + 加解密探针；`IB_MCP_SECRET_KEY` 存在性（不回显） | 探针通过 | 目标机（用户 / devops 执行） | 否 |
| MV-06 | 真实 MCP Server 互通 | 在目标机登记一个真实（内网允许名单内或公网 https）Server，走 modern / legacy 协商 | 协商、发现、调用成功；出站 ACL 已放行 | 目标机 + 真实 Server | 否 |
| MV-08 | A12 / DEF-R29-006、007（回环明文已自动化验证） | 在目标机对真实长连接 MCP Server 验证：服务方推送 `list_changed` 后秒级进入“待复审”；`systemctl restart ib-web` 时无监听线程残留 | 通知到达；重启在超时内完成 | 目标机 + 真实 Server（公网 https 或内网允许名单内） | 否 |
| MV-09 | A13 / GR-C-005 条件；DEF-R29-006、007 的 HTTPS 路径（`SSLSocket` 上的 `read1` / `shutdown(SHUT_RDWR)`，自动化仅覆盖回环明文） | ① 在目标机或带自签/内部 CA 的测试环境，对一个 `https://` 的 streamable-http MCP Server（保持长连接的 `subscriptions/listen` 流）登记并启用（modern 形态）；② 让服务方推送一条小的 `list_changed` 事件但不关闭连接，计时；③ 触发 stop（`systemctl restart ib-web`，或在配置页停用该 Server），观察进程日志与线程；④ 另测服务方先静默再断开的情形 | ② 事件在约 2 s 内使工具进入“待复审”（不是等到流关闭 / 周期复核）且只触发一次；③ 停止后监听线程在超时预算内退出，服务端观察到连接断开，日志无未处理的 `ssl.SSLError` / `AttributeError` / `ValueError` 泄漏，重启在超时内完成；④ 线程正常结束，无残留 | 目标机 + 真实 https MCP Server（或可信 CA 的本机 TLS 测试服务）；由用户 / devops 执行 | 否 |
| MV-10 | DEF-R29-008（自动化已覆盖 build_deps / `_setup_django` / `ready()` 等价路径，未起真实进程） | 目标机部署后：`systemctl restart ib-web ib-worker`，各自对进程做线程转储（如 `py-spy dump --pid` 或 `ls /proc/<pid>/task/*/comm`） | ib-web 进程存在 `ib-mcp-supervisor` 线程（MCP 启用时）；ib-worker 进程**不存在** `ib-mcp*` 线程 | 目标机（用户 / devops 执行；不得读取 env 文件值） | 否 |
| MV-07 | AC-025-03 | 全部已登记 Server 不可达时重启 ib-web 并测启动耗时 | 启动成功；耗时增量记入校准（校准前标“未验收”） | 目标机 | 否 |

## 回流第 3 轮摘要（GROUP_D-005）

- 用户经 CP-002 额外授权（原话“全部按推荐”，经主会话转述）；REWORK_AUTHORIZED 四份测试文档（1.0.0 APPROVED → 1.1.0 DRAFT，历史轮次段落保留）。
- DEF-R29-008：成对用例 TC-INT-R29-1100~1105 全部 PASS（worker 路径 0 线程 / web 路径恰好 1 线程 / 幂等 / close 后无残留 / 离线与总开关关闭返回 False），详见集成报告边界 5。
- DEF-R29-001：关闭（需求修订）；AC-027-01 新增可测项由 TC-UNIT-R29-700~706 覆盖，详见单元报告。
- AC 口径同步：6 条访问控制 AC 映射更新；AC-026-03 正例按 manage 档（read_audit）验证，edit 档 → 403 有用例（TC-INT-R29-802 / 1111）；匿名保存授权 401 新增 TC-INT-R29-1110。
- critical path：口径不变（替代），覆盖率 23 / 23 = 1.00、通过率 11 / 11 = 1.00；E2E 层本轮 77 / 77 PASS，无新增失败。
- 新产品缺陷：无。
