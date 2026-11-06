<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-06T21:29:00+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（REV-29：agent 工具调用的 MCP 适配）

## 摘要

- 执行时间：2026-11-06 缺陷回流第 3 轮复测（GROUP_D-005）的最后一次执行（本层耗时 16.32 s；此后未再修改任何测试文件）。本轮新写 `tests/unit/test_mcp_desc_channels_r29c.py`（TC-UNIT-R29-700~706，35 个收集项）；历史轮次（第 1、2 轮）的翻转说明保留在下方；报告数字仅来自本次执行
- 环境：`/root/.venvs/intelligentbase/bin/python`（Python 3.12.3，pytest 9.1.1）；`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`；SQLite 内存 / `tmp_path`；**未安装 `cryptography`**
- 命令：`$P -m pytest tests/unit -q -p no:cacheprovider`
- **本层总计**：total = pass + fail + skip + blocked + not_testable = 1091 + 0 + 6 + 0 + 0 = **1097**（独立实测收集数 `--collect-only -q | grep -cE '::'` = 1097，一致）
- 其中 **新写 292** = 286 pass + 0 fail + 6 skip + 0 blocked + 0 not_testable（257 既往 + 本轮 35）；既有 805 全部 pass（1091 − 286 = 805）
- **通过率** = pass / (pass + fail + blocked) = 1091 / (1091 + 0 + 0) = **1.00**；新写用例通过率 = 286 / 286 = 1.00（6 SKIP 不计入分母，原因见下）；本轮新写 35 / 35 = 1.00
- 判定模式：baseline（零新增失败 + 新写用例全部通过）；基线（PM 实跑）单元收集 1062；**本层门控：PASSED**
- 缺陷冻结用例：**0 条**

## 执行输出

```
$ $P -m pytest tests/unit -q -p no:cacheprovider
......................................................                   [100%]
1091 passed, 6 skipped in 16.32s

$ $P -m pytest tests/unit --collect-only -q -p no:cacheprovider | grep -cE '::'
1097

$ $P -m pytest tests/unit/test_mcp_desc_channels_r29c.py -q -p no:cacheprovider   # 本轮新写
35 passed in 0.47s

```

SKIP 的 6 条与上一轮相同（`test_mcp_crypto_fernet_r29.py`，`cryptography` 未安装且不得 pip install）。

### GR-C-003 条件 1：`IB_REQUIRE_CRYPTO=1` 本机演示（CI 不会静默跳过）

不带该变量（上面的正常套件）：Fernet 契约 SKIP，**不计 PASS**。带该变量（本机 venv 无 `cryptography`）：

```
$ IB_REQUIRE_CRYPTO=1 $P -m pytest tests/unit/test_mcp_crypto_fernet_r29.py -q -p no:cacheprovider
E       AssertionError: IB_REQUIRE_CRYPTO=1 ⇒ cryptography 必须已安装（CI 不得静默跳过 Fernet 契约）
E       assert False
E        +  where False = _crypto_available()
tests/unit/test_mcp_crypto_fernet_r29.py:51: AssertionError
FAILED tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_220_require_crypto_guard_fails_instead_of_skipping_in_ci
ERROR  tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_221_fernet_round_trip_and_ciphertext_has_no_plaintext
ERROR  tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_222_multifernet_old_key_decrypts_new_key_encrypts
ERROR  tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_223_bad_token_error_does_not_leak_value
ERROR  tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_224_invalid_key_format_raises_config_error_without_value
ERROR  tests/unit/test_mcp_crypto_fernet_r29.py::test_TC_UNIT_R29_225_composition_picks_real_fernet_when_available
1 failed, 5 errors in 0.31s
```

结论：缺包 + `IB_REQUIRE_CRYPTO=1` ⇒ 守卫 1 失败 + 5 契约 ERROR（fixture `pytest.fail`），CI（`ci.yml` 作业级 `env.IB_REQUIRE_CRYPTO: "1"`）不会因缺包而静默变绿。该演示未改动任何文件，正常套件已在其后以不带该变量的方式运行并通过。

### SKIP 逐条原因（6 条，不计入通过率分母，**不得标 PASS**）

| TC | AC | 原因 |
|---|---|---|
| TC-UNIT-R29-220 | AC-006-01（CI 门禁） | `IB_REQUIRE_CRYPTO` 未设置（开发机）：守卫仅在 CI 口径下有意义；以上“本机演示”已验证其失败行为 |
| TC-UNIT-R29-221 | AC-006-01 | `cryptography` 未安装（开发机现状，禁止 pip install）：真实 Fernet 往返 / 密文不含明文，CI 必跑 |
| TC-UNIT-R29-222 | AC-006-03 | 同上：MultiFernet 旧钥解密 / 新钥加密 |
| TC-UNIT-R29-223 | AC-006-01 | 同上：坏令牌异常不含值 |
| TC-UNIT-R29-224 | AC-006-04 | 同上：非法密钥格式 ⇒ ConfigError 且不含值 |
| TC-UNIT-R29-225 | AC-006-01 | 同上：组合根在可导入 `cryptography` 时选真实 Fernet（offline 与否皆然） |

端口层语义（`ReversibleTestCipher` / `UnconfiguredSecretCipher` 同一套契约、`Secret` 脱敏、`make_secret_cipher` 四分支）由 `test_mcp_crypto_r29.py` 27 例在本机真实执行（其中 `make_secret_cipher` 的期望由 `importlib.util.find_spec` 独立判定，不取自被测代码；本机落到 `ReversibleTestCipher`，记账 `cipher=test`）。

## 分项结果

按模块（第 1、2 轮既往新写 257 例，本轮 +35 见下方“回流第 3 轮”；全部在本层 PASS 除上述 6 SKIP；根因分类栏仅在 FAIL / 冻结时填写）：

| 模块 / 文件 | 新写数 | 覆盖 AC | 要点 | 结果 |
|---|---|---|---|---|
| MOD-R29-02 `test_mcp_rules_r29.py` | 52 | AC-001-04、010-01~04、012-01/02、013-01/03/07、015-04、019-05/06、021、027-01 | 命名 / 指纹 / 发现合规 / 风险推断永不推定只读 / 准入全分支（11 个拒绝原因 + 放行正例）/ schema 子集 / 投影 / 结果围栏 / 注入集 N=23 / 降级短语无状态码 | 52 PASS |
| MOD-R29-03 `test_mcp_wire_r29.py` | 28 | AC-002、008-05、019-04/07 | 报文构造 / 头注入拒绝 / SSE 切片与上限 / JSON-RPC 解析 / HTTP 失败分类 / `plain_http_allowed` 13 组 | 28 PASS |
| MOD-R29-04 `test_mcp_netguard_r29.py` | 53 | AC-027-02/03/07、008-05 | 地址拒绝集 38 条（≥30）/ 重绑 / 名单精确放行 / 绝不放行集 / 默认 80,443 回归 | 53 PASS |
| MOD-R29-06 `test_mcp_crypto_r29.py` | 27 | AC-006-01/03/04/06 | `Secret` 脱敏、两种密码器契约、旋转、输入校验、`make_secret_cipher` 四分支、非离线 `fake` 传输被拒 | 27 PASS |
| MOD-R29-06 `test_mcp_crypto_fernet_r29.py` | 6 | AC-006-01/03/04 | 真实 Fernet 契约 + `IB_REQUIRE_CRYPTO` 守卫 | 0 PASS / 6 SKIP |
| MOD-R29-07 `test_mcp_store_r29.py` | 26 | AC-001-02/06、004-01、005-04、006-01、007、020-04、026、027-03 | 内存与文件型 SQLite 同套用例（端口一致性）/ 乐观并发 / 级联删除 / 治理范围 / 审计过滤 / 迁移 010 单源 + 幂等 + 无 DROP / 台账文件字节扫描无明文无主密钥 | 26 PASS |
| MOD-R29-12 `test_mcp_runtime_r29.py` | 34 | AC-005、006-02/05、007-04、012、013、014、015、017-04、019、020、021、024-01、026-01、027-04/06 | 准入全分支“出站 0”+ 放行正例 / 固定入参 N=30 / 回合预算跨 agent / 熔断 / 并发闸 / 审计先行 / 永不抛 | 34 PASS（含翻转的 324 / 325 / 370） |
| MOD-R29-14 `test_mcp_catalog_r29.py` | 20 | AC-002、010、012、013、014、015-04 | 验证类别 / 分页 / 排除 / 1000 工具畸形 / 状态机 / 差异 / CAS / legacy 会话重建 | 20 PASS |
| MOD-R29-17 `test_mcp_supervisor_r29.py` | 11 | AC-013-01/02、024-01/02、017-01 | 健康探测 / 周期复核 / 去抖 / **listen 流 → 刷新 → 复审态**（真实线程）/ start·stop 线程生命周期 / 永不抛 | 11 PASS（含翻转的 609 / 610） |

### 翻转用例（缺陷回流第 1 轮：DEF-R29-002/003/004 已修复已验证）

| TC（编号不变） | AC | 翻转后的正向断言（强度不低于缺陷原描述） | 结果 | DEF |
|---|---|---|---|---|
| TC-UNIT-R29-324 `…_100kb_text_truncated_not_degraded_AC_019_06` | AC-019-06 | 100 KB 文本：`ok=True` 且不是“返回内容过大”；围栏内（正文 + 标注）≤ 32768 字节、含“已截断”、前 1000 字节正文保留；**边界正例**：恰好 32768 字节 ⇒ 内容逐字相等、无“已截断”；32769 字节反例 ⇒ 截断 + 标注且 ≤ 上限 | PASS | DEF-R29-002 已修复已验证 |
| TC-UNIT-R29-325 `…_ascii_over_32kb_truncated_with_marker_within_limit_AC_019_06` | AC-019-06 | 60 KB 纯 ASCII：`ok=True`，围栏内 ≤ 32768 字节，含“已截断”且以其结尾，正文被保留 | PASS | DEF-R29-002 已修复已验证 |
| TC-UNIT-R29-370 `…_undeclared_args_never_forwarded_declared_pass_fixed_override_AC_027_04` | AC-027-04 | ① 未声明键（`history` / `other_project`，含 canary）外发 0 次，声明键 `q` 照常外发；② `fixed_args` 覆盖 LLM 给的 `tenant`，`hidden` 键 `debug` 不外发，未声明键仍丢弃（发出载荷恰为 `{"q":"x","tenant":"a-001"}`）；③ 已审核 schema 无 `properties`（仅 `additionalProperties`）⇒ LLM 入参全部丢弃，发出载荷恰为 `{}`（实现假设 A11，已核对与 AC-027-04“载荷仅含已审核入参 schema 内的参数”不冲突） | PASS | DEF-R29-004 已修复已验证 |
| TC-UNIT-R29-609 `…_listener_thread_exits_within_timeout_after_stop_with_quiet_stream_DEF_R29_003` | CR-008 | 安静 listen 流上：`stop(timeout_s=2.0)` 总等待 < 3 s；监听线程 `is_alive()==False`（2 s 内）；监听响应流已被关闭；无 `ib-mcp-listen*` 线程残留 | PASS | DEF-R29-003 已修复已验证 |
| TC-UNIT-R29-610 `…_enable_flow_keeps_negotiated_list_changed_so_listener_starts_DEF_R29_003` | AC-013-01 | verify 协商 True ⇒ `go_live`（enable + refresh）后 `supports_list_changed` 仍为 True，监听线程 `ib-mcp-listen-crm` 启动并发出 `subscriptions/listen`；stop 后线程退出；**成对**：服务方不支持 listChanged ⇒ 协商为 False、`listens==0`、不启动 | PASS | DEF-R29-003 已修复已验证 |

说明：A12（真实 socket 上 `resp.close()` 能否打断阻塞读取）由集成层 `TC-INT-R29-720 / 721` 验证；第 1 轮结论为不能（DEF-R29-006 / 007），第 2 轮修复后翻转通过（见集成报告）。本层的 609 针对离线替身流，不代表真实传输。

另：`TC-UNIT-R29-042` 记录的设计取舍（LLM 可见的工具 / 参数描述是“净化 + 截断”而非围栏）已于 3.0.0 成为 AC-027-01 的正式口径，DEF-R29-001 已关闭（需求修订）。

### 回流第 3 轮：AC-027-01（3.0.0，ADR-R29-11 分通道口径）补强

新文件 `tests/unit/test_mcp_desc_channels_r29c.py`（分层 unit；被测 `ib.mcp.binding.external_tool_spec` / `ib.mcp.schema_lite.project_llm_schema` / `ib.mcp.result.render_result`）。期望值来自 ADR-R29-11 常量（1000 / 300）与围栏常量，不取自被测输出。

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-R29-700 | AC-027-01 | 正例：合规短描述 `查询客户资料` 原样出现，不被围栏包裹、不被改写 | PASS | — |
| TC-UNIT-R29-701 ×4 | AC-027-01 | 工具描述长度上限 1000：999→999、1000→1000（恰好不截断）、1001→1000、5000→1000 | PASS ×4 | — |
| TC-UNIT-R29-702 ×4 | AC-027-01 | 参数描述上限 300（顶层与嵌套属性）：299/300/301/4000；同时直接测 `project_llm_schema(desc_max=300)` | PASS ×4 | — |
| TC-UNIT-R29-703 ×23 | AC-027-01 | 注入集 N=23（≥20）：描述（含 700 个“填充”超长尾）净化后无控制 / 零宽 / 方向字符、长度 ≤ 1000 / ≤ 300、产品不追加围栏标记 | PASS ×23 | 首跑 2 例失败为**测试写错**（多断言“描述里已有的围栏标记被置换”，AC 3.0.0 未要求；描述通道不是围栏内容）；已按 AC 文本修正为“输出标记数 ≤ 输入标记数”，未放宽长度 / 字符类断言 |
| TC-UNIT-R29-704 | AC-027-01 | 返回内容里用 6 种零宽 / 方向字符把围栏开 / 闭标记拆开（剥离后会拼回）：围栏开 / 闭各恰好 1 次 | PASS | — |
| TC-UNIT-R29-705 | AC-027-01 | isError 错误文本：5 个 text 项各夹带伪造闭合标记，整体围栏仍闭合 1 次，5 处标记均被置换为方括号形式 | PASS | — |
| TC-UNIT-R29-706 | AC-027-01 | 超限（40000 字符 + 伪造闭合标记）截断后：围栏开 / 闭各 1 次，“已截断”标注在围栏内 | PASS | — |

合计 1 + 4 + 4 + 23 + 1 + 1 + 1 = 35 个收集项。既有 TC-UNIT-R29-042（参数描述 ≤ 300、无控制 / 零宽字符）、052（返回围栏不可伪造闭合）、053（注入集 N=23 返回内容围栏）与 3.0.0 措辞一致，原断言未改、仍 PASS。

## 与基线对比（baseline 模式）

基线（PM 实跑，GR-D-003 / GR-C-006）：全量 1718 passed / 6 skipped；本层收集 1062（1056 pass + 6 skip）。本层既有失败清单：**无**（既有 805 例全部仍 PASS）。新增失败：**0**；本轮新增 35 例全部 PASS。上一轮（0.1.0）PM 复跑的 7 条失败（324 / 325 / 370 / 609 / 610 / E2E-008 / INT-1010）为缺陷冻结用例在产品修复后按设计失败，现已全部翻转并 PASS。selfcheck 既有 FAIL `core_framework_free` 不属于 pytest 层（见 e2e 报告“全量回归”）。

## 失败汇总（需路由给开发）

本层无 FAIL。仍需开发处理的单元层关联项：

无。DEF-R29-001 已 **CLOSED**（依据：需求修订，非代码修复——用户 CP-002 Q2=A，AC-027-01 已按 ADR-R29-11 修订，user_stories 3.0.0；TC-UNIT-R29-042 / 052 / 053 与 700~706 与新 AC 一致）。

DEF-R29-002 / 003 / 004：已修复已验证（翻转用例 TC-UNIT-R29-324 / 325；609 / 610；370）。DEF-R29-006 / 007（传输层）：已修复已验证，验证用例在集成层（TC-INT-R29-720 / 721）。

## 观察项（非缺陷，供 PM 裁决 AC 措辞）

- OBS-01 AC-001-04 要求“逐条指出字段名与原因”：登记接口一次只返回首个校验错误码（如 server_id 与 endpoint 同时非法只得 `server_id_invalid`）；每个字段单独非法时均有明确码（`TC-INT-R29-811`）。
- OBS-04 `FakeResolver`（产品自带替身）只查表、不放行 IP 字面量，需测试预置字面量→自身映射才能登记 `http://10.0.0.8:9000/`；生产 `default_resolver` 无此限制，仅替身便利性问题。
