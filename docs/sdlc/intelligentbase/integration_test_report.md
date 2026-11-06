<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-06T21:29:21+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（REV-29：agent 工具调用的 MCP 适配）

## 摘要

- 执行时间：2026-11-06 缺陷回流第 3 轮复测（GROUP_D-005），单元层门控 PASSED 之后的最后一次执行，耗时 64.02 s；此后未再修改任何测试文件。本轮新写 `test_mcp_supervisor_process_r29.py`（DEF-R29-008 成对用例，6 例）与 `test_mcp_access_levels_r29c.py`（AC-016-05 / 026-03 口径，2 例）；历史轮次（第 1、2 轮：1010、720 / 721 翻转）说明保留
- 环境：同单元层（Python 3.12.3；离线；SQLite 内存 / 文件；回环 `127.0.0.1` 随机端口 HTTP 服务仅在 `test_mcp_http_transport_r29.py` / `test_mcp_listen_realsocket_r29.py` 内启停，**不出网**；本轮新用例对套接字 connect / getaddrinfo / create_connection 打桩，尝试数 0）
- 命令：`$P -m pytest tests/integration -q -p no:cacheprovider`
- **本层总计**：total = pass + fail + skip + blocked + not_testable = 578 + 0 + 0 + 0 + 0 = **578**（独立实测收集数 = 578，一致）
- 其中 **新写 106**（既往 98 + 本轮 8）= 106 pass + 0 fail + 0 skip + 0 blocked；既有 472 全部 pass（578 − 106）
- **通过率** = pass / (pass + fail + blocked) = 578 / (578 + 0 + 0) = **1.00**；新写 106 / 106 = 1.00；本轮新写 8 / 8 = 1.00
- 判定模式：baseline（零新增失败 + 新写用例全部通过）；基线（PM 实跑）集成收集 570；**本层门控：PASSED**（单元层门控已 PASSED，才执行本层）
- 缺陷冻结用例：**0 条**。仅回环明文验证传输；HTTPS 路径（A13）未验证，见 e2e 报告 MV-09

## 执行输出

```
$ $P -m pytest tests/integration -q -p no:cacheprovider
..................................................................       [100%]
578 passed in 64.02s

$ $P -m pytest tests/integration --collect-only -q -p no:cacheprovider | grep -cE '::'
578

$ $P -m pytest tests/integration/test_mcp_supervisor_process_r29.py -q -p no:cacheprovider   # 本轮新写，连续 3 次稳定
6 passed in 2.71s / 6 passed in 2.60s / 6 passed in 2.64s

$ $P -m pytest tests/integration/test_mcp_access_levels_r29c.py -q -p no:cacheprovider
2 passed in 1.39s

$ $P -m pytest tests/integration/test_mcp_listen_realsocket_r29.py -q -p no:cacheprovider   # 翻转后连续 3 次，稳定
4 passed in 2.65s / 4 passed in 2.78s / 4 passed in 2.69s

$ $P -m pytest tests/integration/test_mcp_listen_realsocket_r29.py tests/integration/test_mcp_http_transport_r29.py -q -p no:cacheprovider   # 与既有传输契约同批，连续 3 次
24 passed in 4.69s / 24 passed in 4.67s / 24 passed in 4.72s
```

## 分项结果

按集成边界（MOD-A ↔ MOD-B）。全部新写；结果均为 PASS（含翻转后的 720 / 721 共 4 个实例）。

### 边界 1：HTTP 视图 MOD-R29-19 ↔ 管理服务 MOD-15 ↔ 目录服务 MOD-14 ↔ 存储 MOD-07 ↔ 传输替身 MOD-09（`test_mcp_admin_api_r29.py`，50 例）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| I-800 | AC-001-03、004-04、015-05、025-04 | 20 个 admin 端点 × 匿名 / view / edit / manage（共 80 次请求）→ 401 / 403；列表、工具详情、审计条数、治理参数、内网名单快照零变化 | PASS |
| I-801 | AC-003-03、011-03 | 读端点匿名 401；`?token=` 出现在查询串 → 400 `token_in_query_forbidden` | PASS |
| I-802 | AC-026-03 | 审计：admin 全量；manage 档强制只见本项目（传他项目 project_id 也被覆盖）；edit / view 403；非法过滤 400 | PASS |
| I-810~811 | AC-001-01/02/04 | 登记成功不回显令牌 / 重名 / 7 种非法字段 / 未知键 / 缺必填，不落库 | PASS |
| I-812 | AC-001-06 | 6 种非远程 HTTP 传输 → 400，`subprocess.Popen` 计数 0，列表为空 | PASS |
| I-813~815 | AC-008-02/04/05、027-03 | oauth 等被拒；userinfo / file / ftp 等零请求；公网明文 http 拒 / https 通过；名单精确放行与不放大；回环 / CGNAT 经名单可登记 | PASS |
| I-816 | AC-027-07 | 元数据 / 链路本地入名单 ⇒ effective=false，登记与测试连接均拒，请求 0；脏数据直写库也在传输前被拒 | PASS |
| I-817 | AC-006-06 | 无主密钥：带凭证登记 409；不带凭证 Server 登记成功；设置凭证被拒且无明文 | PASS |
| I-820~822 | AC-002-01/02/03、010-01 | 验证成功含协商结果；5 类失败类别（无泄露）；启用 409；地址被拒零请求 | PASS |
| I-823~825 | AC-004-01/02/03/05、006-03 | 变更说明不影响工具；改连接目标 → 待验证 + 4 工具待复审 + 调用 0；轮换使用新凭证 | PASS |
| I-826~828 | AC-006-02/04、005-01/02 | 凭证输入校验 / 范围规则 / 清除；项目专属凭证隔离；停用 / 启用循环 | PASS |
| I-829~830 | AC-005-03~06、026-02 | 删除：缺 confirm 400；被引用 409 列引用；强制级联 204 + 授权清理 + 定义文档 +1 版 + 审计保留；清理失败 409 且已停用未删除，重试成功 | PASS |
| I-831 | REQ-NFUNC-001 | `mcp_enabled=false`：读端点空列表、写端点 503、外部授权保存被拒 | PASS |
| I-840~845 | AC-012、015-04/05、021 | 审核流（风险不预设为只读、指纹 CAS、审计）；未审核 / 禁用不可授权不可调用；筛选与项目可见性（N=3 未开放 Server 泄露 0）；固定入参仅 admin 且回显键名；租户参数须确认；有副作用工具按项目放行 / 撤销 | PASS |
| I-850~853 | AC-020-04、013-02、024-03、007 | 治理读写范围；刷新差异与 409；开放范围校验与撤销；项目专属 Server 仅属主可见 | PASS |
| I-860~862 | AC-001-05、003-01、016-05、026-02 | 停用 Server 的工具不再可选；view 档保存 403；审计时间范围过滤，删除后历史可查 | PASS |

### 边界 2：传输 MOD-R29-08 `HttpMcpTransport` ↔ 客户端 MOD-10（`test_mcp_http_transport_r29.py`，20 例；GR-C-003 条件 2）

仅 127.0.0.1 临时 HTTP 服务（`ThreadingHTTPServer`，服务端行为复用产品 `FakeMcpServer.handle`），测试内启动、测试后关闭。

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| I-700 | AC-002-01、008-01、019-01 | modern：探测 + 分页 + 调用；Bearer 头、令牌不在 URL、无 Cookie、`Accept-Encoding: identity` | PASS |
| I-701 | AC-002-01 | legacy：回退 `initialize`，会话头；`tools/list` 带 `MCP-Session-Id` | PASS |
| I-702 | AC-010-01 | 真实 HTTP 分页（3 工具 / 页大小 2 → 2 次 list） | PASS |
| I-703 | AC-008-03 | 302 → 另一回环端口：不跟随、不读 Location，私有侧 0 命中（即使在名单内） | PASS |
| I-704 | AC-008-05 | 公网明文 http：解析器调用 0 次（字符串判定先于 DNS）；https 进入解析阶段（解析为回环 ⇒ 地址被拒，仍无连接） | PASS |
| I-705 | AC-008-02、027-02 | 8 种危险 URL（userinfo / file / 元数据 / 十六进制与十进制 IP / 未授权端口 …）零命中 | PASS |
| I-706 | AC-027-02 | 钉 IP：主机名仅由假解析器解析仍连通，Host 头保留原主机名；第二次请求重新解析为元数据地址 ⇒ 地址被拒 | PASS |
| I-707 | AC-002-02 | 401 / 缺凭证 / 自定义头鉴权（值在指定头，不在 Authorization，内部槽位头不外泄） | PASS |
| I-708 | AC-019-06 | 读取上限：300 KB 响应在 max_bytes=1000 ⇒ `response_too_large`；放宽后完整读取 | PASS |
| I-709 | AC-020-01 | 真实时钟超时：服务方 5 s、截止 1 s ⇒ `timeout`，耗时 0.5~2.0 s（30 s 口径按比例缩放） | PASS |
| I-710~712 | AC-019-04 | 503 → unreachable、畸形体 → protocol_error、SSE 形态正例；连接被拒 → unreachable，环境代理变量被忽略；头注入 / 超长 URL 拒 | PASS |

### 边界 3：授权校验 MOD-16 ↔ 编译 / 编排钩子 MOD-18 ↔ 注册器 MOD-13 ↔ 调用器 MOD-12（`test_mcp_compile_hotpath_r29.py`，16 例，真实 langgraph 运行时）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| I-1000~1001 | AC-016-01/04、019-01 | 授权只给 kb-agent；顾问越权调用被拒（出站 0）；发布后热生效、取消授权即撤 | PASS |
| I-1002 | AC-016-02、001-05 | 6 种不可用授权（不存在 / 待复审 / 已下线 / 停用 / 未开放 / 禁用）逐条报错，整份不保存，错误不泄露描述 | PASS |
| I-1003~1004 | AC-016-03、007-02/03/05 | 跨项目授权被拒；**运行期新建项目**（M-PM-010）开放前被拒、开放后可授权可调用 | PASS |
| I-1005 | AC-017-01~04、013-04 | 失效授权：配置页标注原因；旧装配调用被拒；无关保存成功；复审通过后新装配恢复 | PASS |
| I-1006~1007 | AC-005-05 | 悬空授权编译容忍；台账不可读 ⇒ 编译失败但保留旧快照，恢复后自动编译成功 | PASS |
| I-1008~1009 | AC-020-04、015-01 | 外部参数白名单与上限；LLM 可见 schema 不含固定 / 屏蔽参数；函数名字符集假设 | PASS |
| I-1010 | AC-016（故事口径“授权给顾问”）、AC-016-04、AC-020-02 | **已翻转（DEF-R29-005 已修复已验证）**：顾问被授权后调用成功（围栏结果含 `ok:search`），同一回合 7 次调用前 5 次成功、第 6 / 7 次 `turn_limit`、替身只收到 5 次（预算按回合计数，与非顾问一致），且不再出现 `no_turn_scope`；**成对**：顾问未授权时同样调用仍被拒（“未授权”，工具不在顾问工具列表，替身 0 次） | PASS |

### 边界 3b：传输 `HttpMcpTransport` ↔ `McpClient.listen` 监听流（真实 socket，`test_mcp_listen_realsocket_r29.py`，2 函数 / 4 实例；GR-C-004 条件 A12）

仅 127.0.0.1 随机端口（测试内启停，不出网）。服务端对 `subscriptions/listen` 回 200 + `text/event-stream` 后保持连接**安静阻塞**，分 close-delimited 与 chunked 两种形态参数化；客户端为真实 `HttpMcpTransport` + 真实 `McpClient.listen`。A12 第 1 轮结论：真实 socket 上 `stop` 不能打断阻塞读取、通知事件滞留（DEF-R29-006 / 007）；第 2 轮修复（`read1` + 关闭前 `shutdown(SHUT_RDWR)`）后，翻转用例全部通过。

| TC | AC / DEF | 描述 | 结果 |
|---|---|---|---|
| I-720[close-delimited / chunked] | CR-008、DEF-R29-006 | **已翻转（已修复已验证）**。正例：stop 之前监听线程阻塞在安静流上且客户端仍连着；`stop` 置位后 3 s 内 `is_alive()==False`，服务端 `client_gone` 在 3 s 内被置位（观察到客户端断开），监听线程 `errors == []`，`changed == []` | PASS ×2 |
| I-721[close-delimited / chunked] | AC-013-01、DEF-R29-007 | **已翻转（已修复已验证）**。流保持打开：服务端推送一条约 70 字节 list_changed 后不关闭，`on_changed` 在 2 s 内回调恰好一次（`changed == [1]`），回调时线程仍在监听、流未释放；再等 0.5 s 不重复；服务端关闭后线程退出且 `errors == []`，`changed` 仍为 `[1]` | PASS ×2 |

覆盖边界：仅回环明文 `http`；`SSLSocket` 上的 `read1` / `shutdown`（A13 / HTTPS）未验证，列入 e2e 报告人工验证清单 MV-09。

### 边界 4：未登记 Server 回归（`test_mcp_regression_r29.py`，8 例）

黄金 `integration/mcp_r29_baseline_golden.json` 由**基线 commit b4fa3a3 的 src 树**（`git archive b4fa3a3 src` 解出，`IB_SRC` 指向，运行 `tests/advisor_r28_probe_support.py`）生成，不取自被测代码；当前 src 重跑同一探针，逐键比对，**无任何白名单差异**。

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| I-900~901 | AC-025-01/02 | N=33 问句答复 / 事件 / 路由提示词哈希 / 外发载荷与基线逐项一致；探针全部其余键（healthz、可授权工具、参数规格、定义文档、默认图、授权、种子）逐项一致 | PASS |
| I-902~903 | AC-026-04、025-01 | `/healthz/deps` 在未登记 / 仅登记 / 停用后与基线逐字节相同，启用后追加 `egress_mcp`（主机 + 数据类别）；配置目录在无可见外部工具时逐字节相同，可见后仅追加 `external_tools`、`mcp` 两键 | PASS |
| I-904 | AC-018-01~03、007-05 | 升级 / 新建项目（含顾问）/ 新发现工具：无任何自动授权；新建项目未开放任何 Server | PASS |
| I-905~906 | AC-023-01/02 | 能力摘要无外部条目且内置条目与基线一致；描述含“总是路由到本工具”，N=30 问句路由序列无差异 | PASS |
| I-907 | AC-025-03 | 非离线真实装配（SQLite 持久台账 + 真实 `HttpMcpTransport` + supervisor）：3 个不可达 Server 重启——启动有界、套接字尝试 0、N=20 对话 20/20、关机无线程残留。**启动耗时增量待目标机校准（未验收）** | PASS |

### 边界 5（回流第 3 轮）：进程入口 `build_application` / `build_deps` / `ibweb.worker._setup_django` / `apps.ready` ↔ `Deps.mcp.supervisor`（`test_mcp_supervisor_process_r29.py`，6 例；DEF-R29-008）

夹具：非离线真实装配（持久化 SQLite 台账 + 真实 `HttpMcpTransport` + 真实 `McpSupervisor`），台账预置一个已启用的不可达 Server（`.invalid`），套接字三类入口打桩；线程按标识差集比较（OBS-06）；teardown 一律 `close()` 并断言无 `ib-mcp*` 线程残留。不 monkeypatch 被测函数。

| TC | AC / DEF | 描述 | 结果 |
|---|---|---|---|
| I-1100 | AC-025-03、DEF-R29-008 | **负例（ib-worker 路径）**：`build_deps` ⇒ 进程内无 `ib-mcp-supervisor` 线程且无任何新增 `ib-mcp*` 线程；再走 `worker._setup_django()` + `IbWebConfig.ready()` ⇒ 仍为 0，`supervisor._thread is None`；前置断言 supervisor 对象存在、传输为 `HttpMcpTransport`、台账含 `dead0`（排除假通过） | PASS |
| I-1101 | AC-025-03 | **正例（ib-web 路径）**：`build_application` ⇒ 恰好 1 个存活 daemon `ib-mcp-supervisor`；同 deps 再调一次仍为同一线程（幂等）；`close()` 后线程退出、无 `ib-mcp*` 残留；调用耗时 < 20 s | PASS |
| I-1102 | AC-024-01 | **同 deps 成对**：先 worker 路径 0 个线程，再 `build_application` 1 个——区分点在入口 | PASS |
| I-1103 | AC-024-01 | `start_mcp_supervisor`：启用 ⇒ True（可重复，线程恒为 1）；`None` / 无 mcp 属性对象 ⇒ False，不抛 | PASS |
| I-1104 | AC-025-01 | 边界（离线装配）：supervisor 缺失 ⇒ 返回 False；`build_application` 后无 `ib-mcp*` 线程 | PASS |
| I-1105 | AC-025-01 | 边界（IB_MCP_ENABLED=0，dict 配置源下为 raw 键 `mcp_enabled=False`）：`deps.mcp is None`、返回 False、无线程；**成对**：同样的非离线装配开关打开 ⇒ `build_application` 后恰好 1 个线程 | PASS |

局限（如实记录）：未起真实 ib-worker 子进程；`apps.ready()` 在“尚未装配、自行 `build_deps()`”分支需要外部配置源，离线测试环境无法构造非离线配置，故以“已装配后调用 `_setup_django` / `ready()`”等价路径验证；真机验证见 e2e 报告 MV-10。注：`IB_MCP_ENABLED` 环境变量在 `IB_CONFIG_SOURCE=dict` 下不被读取（首跑尝试用环境变量构造关闭场景失败属**测试假设写错**，已改用 dict 键）。

### 边界 6（回流第 3 轮）：HTTP 视图鉴权 ↔ authz 档位表 ↔ 配置发布 / 审计端点（`test_mcp_access_levels_r29c.py`，2 例；CP-002 Q3=A 口径）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| I-1110 | AC-016-05 | 匿名保存授权 ⇒ 401；view 档 ⇒ 403；两种情形配置版本不变、工具状态不变；edit 档保存成功（配置版本上升，正例成对） | PASS |
| I-1111 | AC-026-03 | **manage 档（read_audit）**查询审计 ⇒ 200，只得本项目记录（他项目 0 条）；edit 档 ⇒ 403、view 档 ⇒ 403；匿名 ⇒ 401。AC 原文“项目配置者”在此指 manage 档（`mcp_views.py:722` `require_level(request,"read_audit")`；`REQUIRED_LEVEL["read_audit"]=="manage"`，TC-UNIT-R26-050 锁定） | PASS |

AC-001-03 / 003-03 / 011-03 / 025-04 的 401 / 403 口径由既有 I-800（20 个 admin 端点 × 匿名 / view / edit / manage，共 80 次请求）与 I-801 / I-802 / I-842 覆盖，断言本就是“匿名 401、view / edit 越权 403”，与 3.0.0 措辞一致，未改。

## 与基线对比（baseline 模式）

基线（PM 实跑）：本层收集 570 例，既有 472 例；既有失败清单：**无**；新增失败：**0**；本轮新增 8 例（570 + 8 = 578）全部 PASS。

## 失败汇总（需路由给开发）

本层无 FAIL，无需要路由给开发的新增失败。DEF-R29-008 已修复已验证（I-1100~1105）。DEF-R29-005、DEF-R29-006、DEF-R29-007 已修复已验证（翻转用例 TC-INT-R29-1010、720、721）。HTTPS 路径未验证（MV-09）。

## 观察项

- OBS-02 `updated_at` 为秒级时间戳，乐观并发（`expected_updated_at`）在同一秒内的两次写无法区分（`TC-INT-R29-823` 需 `sleep(1.1)` 才能构造 409）；管理员并发写同一 Server 的窗口为 1 秒。
- OBS-03（**已裁决**，CP-002 Q3=A，user_stories 3.0.0）账户体系无独立“终端提问用户”主体；相关 AC 已改为“匿名 401；view / edit 档越权 403”，本观察项关闭。
- OBS-05 降级文案与 AC 字面不同（不影响“降级且出站 0”的行为断言）：AC-005-05 “该能力已下线” ⇒ 实际“外部工具不存在”；AC-012-04 “工具已禁用” ⇒ 实际“外部工具未启用”。
- OBS-06 全量回归时前序既有用例（非离线装配且不调用 `deps.close()`）在进程内遗留数十条 `ib-mcp-supervisor` daemon 线程（实测 25 条）；本轮新写的线程断言已按线程标识差集而非名称计数，不受影响。生产单进程只有一条。建议后续让这些既有用例在 teardown 调用 `deps.close()`。
