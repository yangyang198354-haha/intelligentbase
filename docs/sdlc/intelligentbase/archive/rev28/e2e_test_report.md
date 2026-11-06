<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-04T14:37:52+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/integration_test_report.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（REV-28 顾问 agent）

> 修订记录：2.1.0（2026-11-04T14:37:52+08:00）——GROUP_D-005（DEF-003 裁决后重跑）：集成层门控 PASSED（472 passed）⇒ E2E 66 passed 不变；全量回归 1358 passed（805 unit + 472 integration + 66 e2e + 15 agents）；DEF-003 CLOSED（设计行为，CL-006 Q1=A）；critical path 口径与覆盖不变；1.2.0（2026-11-03T18:45:08+08:00）——GROUP_D-004（缺陷回流 2/2 复测）：集成层门控 PASSED ⇒ 执行本轮新增 E2E 旅程 TC-E2E-R28-013 / 014 / 015（新文件 `tests/e2e/test_advisor_deepseek_journeys_r28.py`）；critical path 覆盖 18/19 → 19/19、通过率 15/15；全量回归 1355 passed；DEF-002/004/005/006 FIXED/VERIFIED，DEF-003 OPEN（待用户裁决）；MV 仍 16 项；1.1.0（2026-11-03T18:27:49+08:00）——GROUP_D-003：上一层（集成）门控 FAILED（5 项新写用例因产品缺陷失败，DEF-002~006）⇒ 按 §K **本轮新增范围的 E2E 层未执行**；更新全量回归（1352 = 1347 passed + 5 failed）、缺陷清单与人工验证清单（MV-05 改写、新增 MV-14~16，待人工验证 13→16）；1.0.0 的 12 个旅程正文保留；0.2.0（2026-11-02T23:35:17+08:00）——DEF-001 回流复测：全量回归 1231→1232（DEF-001 复测）；DEF-001 状态 FIXED/VERIFIED；Q1/Q3/Q4 待裁决 / 观察项保持原样；0.1.0——初稿。

REV-27 APPROVED 版本已归档于 `archive/rev27/e2e_test_report.md`（只读）。

## 摘要

critical path 口径：替代（项目无浏览器 E2E 框架；用最高层可执行的端到端级用例——后端多步 HTTP / SSE 旅程，真实账户鉴权 + 发布协议 + 运行时 + SSE 流；前端为“纯函数 + 请求形状”模型层替代，非真实浏览器）。

### 2.1.0（GROUP_D-005；最后一次执行 2026-11-04T14:37:52+08:00 之后）

- 上一层（集成）门控 **PASSED**（472 passed；新写 4/4；无缺陷冻结用例）⇒ 执行 E2E 层。`python -m pytest tests/e2e -q -p no:cacheprovider` → `66 passed in 5.26s`（收集 66，不变）。
- 本层 R28 旅程：total = pass + fail + skip + blocked + not_testable = **20 = 15 + 0 + 0 + 0 + 5**（同 1.2.0；本轮无 E2E 用例改动，新增 0）；通过率 = 15/15 = **1.00**。
- **critical path 覆盖率** = 19 / 19 = **1.00**；**critical path 通过率** = 15 / 15 = **1.00**；待人工验证 16 项（MV-01~MV-16，不变）；最终状态至多 DELIVERED_WITH_ISSUES。
- 前端层（独立）：`npm test` → `# tests 160 / # pass 160 / # fail 0 / # skipped 0`。
- **全量回归（2.1.0）**：

| 命令 | 输出尾部 | 前值（1.2.0） | 新增失败 |
|---|---|---|---|
| `python -m pytest tests -q -p no:cacheprovider` | `1358 passed in 51.36s` | 1355 passed | **0** |
| `python src/scripts/selfcheck.py` | `自检结果：68/69 通过`；失败项仅 `core_framework_free：ib/core 引入了第三方顶层包：sitecustomize` | 68/69（同一既有环境性失败） | **0** |
| `(cd src/frontend && npm test)` | `# tests 160 / # pass 160 / # fail 0` | 160/160 | **0** |

  算术：1358 = 805 + 472 + 66 + 15；亦 = 1355（前值）- 1（418[intent] 移出）+ 4（425×2 + 426×2 新写）。逐条与前值比对：pytest 无失败；selfcheck 的 1 个 FAIL = 既有（依据：基线同项，`sitecustomize` 为开发机 Python 环境注入的第三方顶层包，与 REV-28 无关）。
- 判定模式：INCREMENTAL / baseline。**本层门控：PASSED**。
- **缺陷状态表（2.1.0）**：

| DEF | 级别 | 复现 / 验证用例 | 状态 |
|---|---|---|---|
| DEF-001 | MINOR | TC-UNIT-R28-085 / 088 | FIXED / VERIFIED |
| DEF-002 | MAJOR | TC-INT-R28-418[prepare] | FIXED / VERIFIED |
| DEF-003 | MINOR | TC-INT-R28-425 / 426（原 418[intent] 冻结用例已翻转为正向断言） | **CLOSED — 按用户裁决为设计行为（CL-006 Q1=A），非缺陷** |
| DEF-004 | MINOR | TC-INT-R28-421、344（CR-022） | FIXED / VERIFIED |
| DEF-005 | MAJOR | TC-INT-R28-423、TC-E2E-R28-015 | FIXED / VERIFIED |
| DEF-006 | MAJOR | TC-INT-R28-424、TC-E2E-R28-015 | FIXED / VERIFIED |

  无 OPEN 缺陷。下文 1.2.0 及更早小节中 DEF-003 “OPEN / 待用户裁决 / 缺陷冻结”的表述为历史记录，以本表为准。

### 1.2.0（GROUP_D-004；最后一次整层执行 2026-11-03T18:40:59~18:41:49+08:00）

- 上一层（集成）门控 **PASSED**（469 passed，新写 38/38，含 1 项缺陷冻结 TC-INT-R28-418[intent]）⇒ 执行 E2E 层。命令：`python -m pytest tests/e2e -q -p no:cacheprovider` → `66 passed in 4.61s`（收集 66 = 既有 51 + R28 旅程 TC-E2E-R28-001~012 的 12 + 本轮新增 3）。
- **本层 R28 旅程**：total = pass + fail + skip + blocked + not_testable = **20 = 15 + 0 + 0 + 0 + 5**（15 个旅程 TC-E2E-R28-001~015 全部 PASS；5 项 NOT_TESTABLE：AC-014-06 的真实端点效果部分、AC-019-01、AC-019-02、AC-019-04、AC-020-02〔N/A：设计未选该形态〕，无执行、不计分母，见“人工验证清单”与 test_plan“不可测项”）。其中本轮新增 total = **3 = 3 + 0 + 0 + 0 + 0**。
- 通过率 = pass/(pass+fail+blocked) = 15/15 = **1.00**。
- **critical path 覆盖率** = 有 E2E 级用例的 Must Have 故事 / Must Have 故事总数 = **19 / 19 = 1.00**（US-001/002/004/005/006/007/008/009/010/011/012/013/014/015/016/017/018/019 + **US-020**〔TC-E2E-R28-014〕）。
- **critical path 通过率** = 15 / 15 = **1.00**；**待人工验证（critical path 内单独计数）= 16 项**（MV-01~MV-16，较 1.1.0 不变）；只要仍有未完成的人工验证，最终状态至多 DELIVERED_WITH_ISSUES。
- 前端层（独立计数）：`npm test` 160/160（本轮前端无改动）。
- 全量回归：新增失败 **0**（见下）。判定模式：INCREMENTAL / baseline。**本层门控：PASSED**（critical path 1.00；待人工验证项如实保留；DEF-003 OPEN 待用户裁决，已按“缺陷冻结”处理）。
- 零外网：新文件 autouse 夹具把 `socket.connect` / `create_connection` / `getaddrinfo` 置为“调用即失败”，teardown 断言尝试数 = 0（画像 P11-3：自动化禁止调用真实端点）；搜索走真实 `DeepSeekSearchProvider` + `FakeDeepSeekTransport`，抓取走 `SafeFetcher` + 假传输 + 假 DNS。

### 1.1.0（GROUP_D-003，历史；其“未执行”结论已被 1.2.0 取代）

**未执行：上一层未达标**——集成层 33/38 通过（新写 5 项失败，均为产品缺陷 DEF-002~006，见 `integration_test_report.md`），按 §K（baseline 模式：新写用例须全部通过才进入下一层）停在集成层，**本轮新增范围的 E2E 层不执行、不写新增旅程用例**。本层门控：**FAILED（未执行）**。

- total（本轮新增 E2E 级用例）= pass + fail + skip + blocked + not_testable = **0 = 0 + 0 + 0 + 0 + 0**；通过率 n/a。
- 既有 12 个 R28 旅程（TC-E2E-R28-001~012）及其余 `tests/e2e` 共 63 项作为全量回归的一部分于 2026-11-03T18:26+08:00 再次随全量执行，全部 PASS（见“全量回归”，失败 5 项均在 integration 层新写用例内）；这**不**构成本轮新增范围的 E2E 验收。
- critical path 覆盖率（1.1.0 口径）= 有 E2E 级用例的 Must Have 故事 / Must Have 故事总数 = **18 / 19**（Must Have 由 18 增至 19：新增 US-020；US-020 目前仅有集成级用例 TC-INT-R28-413 / 415 / 227~229，尚无 E2E 级旅程 ⇒ 待门控放行后补）。
- critical path 通过率：既有 12 个旅程在全量回归中 12/12 = 1.00（1.0.0 口径沿用）；新增范围未执行。
- **待人工验证（critical path 内单独计数）= 16 项**（MV-01~MV-16；相对 1.0.0 的 13 项：MV-05 改写为真实 DeepSeek 搜索效果，新增 MV-14 / 15 / 16）；只要仍有未完成的人工验证，最终状态至多 DELIVERED_WITH_ISSUES。
- 前端层（独立计数）：`npm test` 160/160（本轮前端无改动，复跑 pass 160）。
- 缺陷：DEF-002 ~ DEF-006（见“缺陷 / 观察”）；DEF-001 保持 FIXED / VERIFIED。

### 1.0.0 范围（保留，未改动；数字仅描述 1.0.0 时点）

- 执行时间：2026-11-02T23:31:50+08:00（最后一次整层执行；DEF-001 回流复测，tests/e2e 复跑 `63 passed in 4.79s`）；环境同上，离线。
- 命令：`python -m pytest tests/e2e -q -p no:cacheprovider`（后端）；前端层 `(cd src/frontend && npm run build && npm test)`。
- **本层**（后端 E2E 级）：total = pass + fail + skip + blocked + not_testable = **16 = 12 + 0 + 0 + 0 + 4**（12 个旅程 TC-E2E-R28-001~012 全部 PASS；4 项 NOT_TESTABLE：AC-014-06、AC-019-01、AC-019-02、AC-019-04，无执行、不计分母，见“人工验证清单”）。
- 通过率 = pass/(pass+fail+blocked) = 12/12 = **1.00**。
- **critical path 覆盖率** = 有 E2E 级用例的 Must Have 故事 / Must Have 故事总数 = **18 / 18 = 1.00**（US-001/002/004/005/006/007/008/009/010/011/012/013/014/015/016/017/018/019；对应关系见各旅程“关联”）。
- **critical path 通过率** = 12 / 12 = **1.00**；**待人工验证（critical path 内单独计数）= 13 项**（MV-01~MV-13，其中 MV-05~MV-07 为 AC-014-06 / AC-019-01 / 02 / 04 的 NOT_TESTABLE 对应项）；只要仍有未完成的人工验证，最终状态至多 DELIVERED_WITH_ISSUES。
- 前端层（独立计数）：`npm test` 160/160（基线 141 + 新写 19），含 2 个替代口径旅程 TC-FE-R28-E01~E02。
- 全量回归：新增失败 **0**（见下）。判定模式：INCREMENTAL / baseline；上一层（集成）门控 PASSED。**本层门控：PASSED**（critical path 通过率 1.00；待人工验证项如实保留）。

## 全量回归

### 1.2.0（最后一次执行 2026-11-03T18:41:53~18:42:44+08:00）

| 命令 | 输出尾部 | 前值（PM 复跑，C-004 后） | 新增失败 |
|---|---|---|---|
| `python -m pytest tests -q -p no:cacheprovider` | `1355 passed in 48.62s`（= 805 unit + 469 integration + 66 e2e + 15 agents） | 2 failed / 1350 passed（418[intent]、344） | **0**（既有用例新增失败 0；新写用例失败 0） |
| `python src/scripts/selfcheck.py` | `自检结果：68/69 通过`；失败项仅 `core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）`（sitecustomize 环境性） | 68/69（同一既有失败） | **0** |
| `(cd src/frontend && npm test)` | `# tests 160 / # pass 160 / # fail 0 / # skipped 0`（本轮前端无改动，未重跑 build） | 160/160 | **0** |
| `python -m pytest tests/agents -q -p no:cacheprovider` | `15 passed in 0.07s` | 15 passed | **0** |

算术：1355 = 1350（前值 passed）+ 2（418[intent] 冻结后转绿、344 改 `.get` 后转绿）+ 3（本轮新增 E2E）；亦 = 1352（1.1.0 时点总数）+ 3。分层：805 + 469 + 66 + 15 = 1355。
逐条与前值比对：pytest 无任何失败；selfcheck 的 1 个 FAIL = 既有（依据：基线 57+1 与 PM 复跑同项，`sitecustomize` 为开发机 Python 环境注入的第三方顶层包，与 REV-28 无关）。

### 1.1.0（历史，保留）

| 命令 | 输出尾部 | 前值（PM 复跑，GROUP_C-003 后） | 新增失败 |
|---|---|---|---|
| `python -m pytest tests -q -p no:cacheprovider` | `5 failed, 1347 passed in 53.14s`（总 1352 = 805 unit + 469 integration + 63 e2e + 15 agents） | 1232 passed | 既有用例新增失败 **0**；新写用例失败 **5**（全部在 `tests/integration/test_deepseek_search_int_r28.py`：TC-INT-R28-418[intent]、418[prepare]、421、423、424 ⇒ DEF-003 / 002 / 004 / 005 / 006） |
| `python src/scripts/selfcheck.py` | `自检结果：68/69 通过`；失败项仅 `core_framework_free：ib/core 引入了第三方顶层包：sitecustomize` | 68/69（同一既有失败） | **0** |
| `(cd src/frontend && npm test)` | `# tests 160 / # pass 160 / # fail 0 / # skipped 0`（本轮前端无改动，未重跑 build） | 160/160 | **0** |

算术：1352 = 1232（前值）+ 82（unit 新写）+ 38（integration 新写）；1347 passed = 1232 + 82 + 33；5 failed = 5 项新写失败。
逐条与前值比对：失败清单逐条 = 新增（本轮新写用例，产品缺陷）；selfcheck 的 1 个 FAIL = 既有（依据：前值同项，`sitecustomize` 环境性）。

### 1.0.0 时点（保留）

| 命令 | 输出尾部 | 基线 | 新增失败 |
|---|---|---|---|
| `python -m pytest tests -q -p no:cacheprovider` | `1232 passed in 48.20s` | 914 passed | **0**（1232 = 914 + 新写 318 = 208 unit + 98 integration + 12 e2e；PM 所述“1 failed / 1230 passed”中的 1 failed 即冻结用例，翻转后转为 passed，另加正例 088 ⇒ 1232） |
| `python src/scripts/selfcheck.py` | `自检结果：64/65 通过`；失败项仅 `core_framework_free：ib/core 引入了第三方顶层包：sitecustomize` | 57 PASS / 1 FAIL（同一失败；本轮复跑 64/65，rc=1） | **0**（开发新增的 7 项 `web_egress_single_exit` / `web_ssrf_rejects` / `web_governance_schema_single_source` / `advisor_graph_rules` / `advisor_seed_clean` / `search_port_conformance` / `advisor_apology_text_safe` 全 PASS；唯一 FAIL 为环境性既有失败） |
| `(cd src/frontend && npm run build)` | `✓ built in 33.85s`（含 vue-tsc；rc=0；本轮前端无改动，build 沿用上一次执行，未重跑） | rc=0 | 0 |
| `(cd src/frontend && npm test)` | `# tests 160 / # pass 160 / # fail 0 / # skipped 0` | 141/141 | **0** |

逐条与基线比对：pytest 无任何失败；selfcheck 的 1 个 FAIL = 既有（依据：PM 基线 57 PASS / 1 FAIL 同项，`sitecustomize` 为开发机 Python 环境注入的第三方顶层包，与 REV-28 无关）。

## 用户旅程

通用：HTTP 全部经 Django 测试客户端；账户鉴权为生产同构（`ibweb.accounts.policy` + 令牌）；提问走真实 `GET /api/chat/stream`（SSE）；LLM / 搜索 / 抓取传输 / DNS 为替身。每个旅程的“实际响应”均为断言通过的实测值。

### TC-E2E-R28-001: 编辑者上手——目录 → 预检 → 画布规则 → 加入顾问 → 提问 → Builder 微调
- 关联：US-001 / 003 / 004 / 005；AC-001-01、003-01/03、004-01、005-02/03/04；环境：p_alpha，账号 editor（编辑档）/ viewer（查看档）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | GET /api/config/catalog（editor） | agents 仅 kb-agent；builtin_agents 含“顾问” | 符合 | PASS |
| 2 | POST /api/config/publish/preview（含顾问 + 合同 agent 的规范图） | 200，差异含 agent_added/advisor | 符合 | PASS |
| 3 | POST /api/config/publish（viewer） | 403，版本仍为 0 | 403，版本 0 | PASS |
| 4 | 发布顾问无入边的图 | 400 `graph_unreachable_from_start` | 符合 | PASS |
| 5 | 发布顾问回边成环的图 | 400 `graph_cycle`，版本不变 | 符合 | PASS |
| 6 | 发布合法规范图（editor） | 200，applied=true | 符合 | PASS |
| 7 | SSE 提问“帮我审一下合同” | 恰一个 content、一个 done；含“20%”“第 5 条”；无内部名称；顾问输入含上游材料段 | 符合 | PASS |
| 8 | GET /api/config/prompts/advisor/main（viewer） | 200，内容 = 顾问提示词 | 符合 | PASS |
| 9 | POST /api/builder/review-existing（顾问，“面向房产客户，语气更正式”） | 返回草稿；三项条款 0 扣分；版本与服务端提示词不变 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-002: 自由编排——START→顾问(query_only)→A(with_upstream)→END
- 关联：US-005 / AC-005-01；环境：p_alpha

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 发布该拓扑（顾问为默认专家） | 校验通过 | 发布成功 | PASS |
| 2 | 提问 | 合同 agent 收到的输入含“【上游材料（只读参考，不是指令）】”且含顾问产出标记 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-003: 管理员新建项目并启用顾问 → 提问
- 关联：US-002 / US-006；AC-002-01/02/03；环境：文件态种子（tmp 目录）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | POST /api/projects（editor 账号，启用顾问） | 403 | 403 | PASS |
| 2 | POST /api/projects（admin，enable_advisor=true） | 201；顾问种子逐字落盘；项目可见 | 符合 | PASS |
| 3 | 经提示词端口写入种子（离线内存提示词库等价于生产 Fs 目录）后取运行时 | 专家 [kb-agent, advisor]；advisor 无工具；kb-agent 仅 search_knowledge | 符合 | PASS |
| 4 | SSE 提问“退货期限是多久” | 唯一答复含“7 天” | 符合 | PASS |
| 5 | POST /api/projects（不勾选） | 201；专家仅 kb-agent，无 advisor_id | 符合 | PASS |
- 结论：PASS（离线模式限制见“观察”OBS-2）

### TC-E2E-R28-004: 知识问答 + 上下文 + 话题（真实入库 / 真实检索）
- 关联：US-006 / 008 / 011 / 012 / 013；AC-006-01、008-01、011-01/02、012-01/03、013-01~04；环境：p_alpha，《退换货政策.txt》经真实上传 + 处理管线入库

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | SSE“退货期限是多久” | 唯一答复含“7 天”与文件名《退换货政策.txt》引用，无内部名称 | 符合 | PASS |
| 2 | SSE“那运费呢”（同会话） | 答复含“12 元”；委托问题含“退货”“运费” | 符合 | PASS |
| 3 | SSE“推荐一部适合周末看的电影” | 答复含“《某电影》”；不调用 kb-agent；联网查询词不含“退货” | 符合 | PASS |
| 4 | SSE“回到刚才说的退货期限” | 答复含“7 天”；kb-agent 再被调用 1 次 | 符合 | PASS |
| 5 | 另一会话问候 | 理解步骤历史为“（无）”，看不到上一会话 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-005: 联网旅程——授权 / 预算 / 白名单 / 全局上限 / 审计 / 取消授权
- 关联：US-007 / 014 / 015 / 016 / 018；AC-007-01/02、014-01/03、016-01/03/05/07；环境：搜索 = Fake，抓取 = 假传输 + 假 DNS

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | editor 发布授权 web_search/web_fetch（返回条数 3、超时 10、白名单 example.com、每轮 3 次） | 200 | 200 | PASS |
| 2 | SSE 提问天气 | 答复含“来自互联网”与来源网址；提供方收到 max_results=3 | 符合 | PASS |
| 3 | 同轮第 4 次联网 | “已达本轮联网上限”，提供方只被调用 1 次 | 符合 | PASS |
| 4 | 白名单内 / 外抓取 | 内：放行含正文；外：“目标地址不被允许”，other.org 出站 0 | 符合 | PASS |
| 5 | admin 把全局上限调到 2 次后 editor 再保存每轮 3 次 | 400，“超出全局上限（2 次）” | 符合 | PASS |
| 6 | 审计 | web.* 记录只含 host:，不含查询原文 | 符合 | PASS |
| 7 | 取消授权后新会话提问 | 联网 0；顾问工具列表空；答复“当前未开启联网检索” | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-006: 抓取总开关旅程（AQ4=A）
- 关联：US-015 / 016；AC-015-05/06、016-08；环境：缺省装配，再以 `web_fetch_enabled=True` 重新装配（模拟运维打开并重启）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 全新装配：fetcher 为 None；已授权顾问读网页 | 出站请求 0；答复“当前未开启网页抓取” | 符合 | PASS |
| 2 | 重新装配（配置层打开）并换入假传输；同一调用 | 返回正文；出站 1 次 | 符合 | PASS |
| 3 | 开关打开但取消 web_fetch 授权 | 工具列表仅 web_search；调用被拒“未授权”；出站仍为 1 次 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-007: 委托旅程——单个 / 并行 / 范围外 / 超时
- 关联：US-009 / 010；AC-009-01/02/04、010-01/04；环境：p_alpha（kb-agent + advisor + contract-agent）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | SSE“审一下合同的违约条款” | 合同 agent 被调 1 次；唯一答复含“20%”；原答标记与内部名 0 | 符合 | PASS |
| 2 | SSE 同时涉及退货与合同的问题 | 两路结果都进入唯一答复；原始答复标记 0 | 符合 | PASS |
| 3 | SSE 范围外问题（服务器运维） | 合同 agent 调用数不变；仍有答复 | 符合 | PASS |
| 4 | 合同 agent 超时 | 答复说明“暂时未能完成”，无致歉文案 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-008: 致歉旅程（AQ1=B）
- 关联：US-006 / 010；AC-006-07、010-06/07；环境：p_alpha，kb-agent 原答含 `ORIG-KB-7DAY`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 顾问汇总异常（含内部错误细节） | HTTP 200；唯一 content = 统一致歉；无原答 / 内部名 / 异常细节 | 符合 | PASS |
| 2 | 顾问两次保真不过 | 同上 | 符合 | PASS |
| 3 | 首次不过、第二次通过（正例） | 正常答复，无“抱歉” | 符合 | PASS |
| 4 | 下一轮恢复正常 | 正常答复 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-009: 安全旅程——注入 / SSRF / canary / 越权
- 关联：US-018；AC-018-01/02；REQ-NFUNC-003~005；环境：搜索结果含注入指令；kb-agent 产出含 canary

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | SSE 提问（顾问脚本模拟被诱导：外发 canary、访问内网 / file / ::1、调用未授权的合同 agent） | 整轮 HTTP 200，答复正常，不致歉 | 符合 | PASS |
| 2 | 检查工具结果 | 注入文本只在围栏内，围栏结束标记恰 1 个 | 符合 | PASS |
| 3 | 外发检查 | canary 出站 0；内网 / file / ::1 抓取出站 0；合同 agent 调用 0；正常检索仍出站 1 次 | 符合 | PASS |
- 结论：PASS（真实 LLM 的顺从度见 MV-08）

### TC-E2E-R28-010: 未启用顾问项目的 SSE 旅程与基线一致
- 关联：US-017；AC-017-01；环境：p_alpha 未启用，p_beta 同期启用顾问并联网

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | p_alpha 经 SSE 提 6 问 | 每问事件序列与答复文本与基线黄金逐帧一致 | 6/6 一致 | PASS |
| 2 | 联网替身观察 | 提供方调用 0；p_alpha 无 advisor_id，p_beta 有 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-011: 评测流程（离线、替身）
- 关联：US-019；AC-019-03；环境：评测 CLI `advisor_eval.main`，评测集为临时文件（合成，仅验证流程）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 完美替身 + 评测集 | 退出码 0；pass=true；计数 intent 10 / context 6 / topic 16 | 符合 | PASS |
| 2 | 弱替身 | 退出码 1；verdict.intent_top1=false；误判率 1.0 | 符合 | PASS |
- 结论：PASS（**合成集通过率不得用于宣告验收**——AC-019-04；真实精准度见 MV-06 / MV-07）

### TC-E2E-R28-012: 全局上限调整的运行期效果
- 关联：US-016 / AC-016-07；环境：项目已保存每轮 5 次

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | editor 调全局上限 | 403 | 403 | PASS |
| 2 | admin 调到 2 次 | 200 | 200 | PASS |
| 3 | 下一轮联网 3 次 | 前 2 次成功，第 3 次“已达本轮联网上限”（运行期取 min(参数, 全局)） | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-013: DeepSeek 联网搜索旅程（1.2.0 新增）
- 关联：US-014 / 016 / 018；AC-014-07~10、016-09、018-05 / 06；环境：p_alpha，editor / viewer；搜索 = 真实 `DeepSeekSearchProvider` + `FakeDeepSeekTransport`（哨兵 Key），零外网夹具
- 新文件：`tests/e2e/test_advisor_deepseek_journeys_r28.py`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | POST /api/config/publish（viewer，含 web_search 授权、每轮上限 3） | 403 | 403 | PASS |
| 2 | 同一发布体（editor） | 200，applied=true | 符合 | PASS |
| 3 | SSE 提问“明天上海天气怎样？” | 200，唯一答复含“上海天气预报”与网址，非致歉；出站请求 = 资料端点 `https://api.deepseek.com/v1/tools/search`，Bearer 头，体键集恰为 {query,count,need_content} | 符合 | PASS |
| 4 | 提供方依次 401 / 402 / 429 / 500 / 504，每次提问后再提 kb 问题 | 每轮 200、单条答复含“未能联网检索到最新信息”，状态码 / Key / Bearer 0 次，非致歉；kb 答复含“7 天”；共 6 次出站 | 符合 | PASS |
| 5 | 提供方返回 200 空数组 | 答复“未检索到相关结果”，无网址；工具返回“联网检索未找到相关结果” | 符合 | PASS |
| 6 | 一轮连续 5 次检索，每轮上限 3 | 替身请求数恰增 3 | 增 3 | PASS |
| 7 | kb 输出含 canary 进入历史后，顾问以完整 canary 作检索词外发 + 一次正常检索 | 前者“请求内容不被允许”，后者成功；canary 出现在出站体 0 次 | 符合 | PASS |
| 8 | 审计 web.search | 仅 host:api.deepseek.com，无查询原文 / canary / Key | 符合 | PASS |
| 9 | 提供方恢复 | 成功有来源 | 符合 | PASS |
- 结论：PASS

### TC-E2E-R28-014: 替身仅限离线 / DeepSeek Key 来源切换（US-020，1.2.0 新增）
- 关联：US-020 / 018；AC-020-01 / 020-03、AC-018-05；环境：离线装配 + 非离线真实装配（`build_deps(force=True)`，LLM 主机 api.deepseek.com，传输类 `UrllibPostTransport` 被替身替换）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 离线 + `FakeSearchProvider`，editor 经 SSE 提问联网问题 | 200，答复含替身返回的标题与网址（AC-020-03：离线可用） | 符合 | PASS |
| 2 | 非离线 + `web_search_provider=fake` 装配 | `StartupError`，信息含 `IB_WEB_SEARCH_PROVIDER`，不含 “fake”；`FakeSearchProvider` 构造 0 次（AC-020-01） | 符合 | PASS |
| 3 | 非离线 + deepseek，仅环境变量 Key，SSE 联网提问 + kb 提问 | 联网成功有来源，请求头 Bearer 为该 Key；kb 答复含“7 天” | 符合 | PASS |
| 4 | 向 llm_key 存储写入另一 Key 后重新装配，再提问 | 存储优先于环境变量，请求头 Bearer 为存储 Key | 符合 | PASS |
| 5 | 清除存储并删除环境变量后重新装配，再提问 | 工具返回“联网服务未配置”，答复降级（HTTP 200、非致歉、无 Key 值），kb 正常 | 符合 | PASS |
- 结论：PASS（AC-020-02 为 N/A：设计选“启动失败”形态；其用户可见语义由步骤 5 与 TC-INT-R28-204 / 412 等价覆盖）

### TC-E2E-R28-015: 抓取失败三种短语（US-015，1.2.0 新增）
- 关联：US-015；AC-015-07；环境：p_alpha，已授权 web_fetch，抓取 = `SafeFetcher` + `FakeTransport` + 假 DNS（ADR-R28-12 保留本地抓取）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | SSE 提问“请读取这个网页”，顾问依次抓取 403 站点 / 404 站点 / 200 空白页 / 不支持类型 / 正常页 | HTTP 200，单条答复，无 error 事件 | 符合 | PASS |
| 2 | 正常页（正例） | 返回“【联网内容…”围栏且含正文“正文 ABC” | 符合 | PASS |
| 3 | 403 与 404 | 失败短语非空且**可区分**：403 ⇒ “目标网站拒绝了访问”，404 ⇒ “该网页无可用内容” | 符合（DEF-005 FIXED） | PASS |
| 4 | 200 空白页 | 失败短语，不是“成功 + 空正文”围栏，且不同于 403 短语 | 符合（DEF-006 FIXED） | PASS |
| 5 | 全部失败短语 | 不含状态码数字 403 / 404，不含错误页原文 ERRTEXT-R28 | 符合 | PASS |
- 结论：PASS

### 前端替代口径旅程（独立计数）
- TC-FE-R28-E01：创建项目（enable_advisor:true）→ 加入顾问 → 序列化发布体 → 移除，图与请求体符合约定；TC-FE-R28-E02：读 → 改 → 写联网上限，请求体仅三个整数键。均 PASS。

## 缺陷 / 观察

### 1.2.0 缺陷状态表（GROUP_D-004 复测）

| DEF | 级别 | 复现 / 验证用例 | 状态 |
|---|---|---|---|
| DEF-001 | MINOR | TC-UNIT-R28-085 / 088 | FIXED / VERIFIED（沿用 1.0.0） |
| DEF-002 | MAJOR | TC-INT-R28-418[prepare] | **FIXED / VERIFIED**（回合准备段异常 ⇒ 统一致歉，HTTP 200，无 error 事件） |
| DEF-003 | MINOR | TC-INT-R28-418[intent]（1.2.0 缺陷冻结，守卫串 `DEF-003-GUARD`；2.1.0 已关闭，见顶部缺陷状态表） | **（1.2.0 历史）OPEN — 待用户裁决**：理解步骤异常目前 fail-open 返回正常答复（HTTP 200、无错误细节）；原期望（致歉，REQ-FUNC-012 (e1) 字面）保留在用例注释与集成报告，裁决后翻转 |
| DEF-004 | MINOR | TC-INT-R28-421、344（CR-022） | **FIXED / VERIFIED** |
| DEF-005 | MAJOR | TC-INT-R28-423、TC-E2E-R28-015 | **FIXED / VERIFIED** |
| DEF-006 | MAJOR | TC-INT-R28-424、TC-E2E-R28-015 | **FIXED / VERIFIED** |

本轮未发现新的产品缺陷。

### 1.1.0 新增缺陷（历史记录；状态以上表为准；均由集成层新写用例发现）

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| DEF-002 | MAJOR | 顾问回合中理解步骤之后、`run_dag` 之前的回合准备（历史摘要 / 回合对象）出现未预期异常时，异常逃出编排器，SSE 只有 `error` 事件，提问者拿不到统一致歉（AC-010-08、REQ-FUNC-012 (e1)；HTTP 200 非 5xx） | TC-INT-R28-418[prepare] | `src/ib/orchestration/__init__.py:475-483` |
| DEF-003 | MINOR（待裁决） | 理解步骤（意图识别 / 问题消解）的未预期异常被 fail-open 吞掉，返回正常答复而不是致歉；与 REQ-FUNC-012 (e1) 字面不符，但与 CR-008 已接受设计一致。**需用户 / PM 裁决走哪一边** | TC-INT-R28-418[intent]（对照 TC-INT-R28-058） | `src/ib/orchestration/__init__.py:461-466`、`src/ib/advisor/understand.py:166-171` |
| DEF-004 | MINOR | Builder 项目摘要对未启用顾问项目的差异不止多两个联网工具条目：`search_knowledge` 条目多了键 `is_external: false`（AC-017-06 要求其余差异 = 0） | TC-INT-R28-421 | `src/ib/builder/types.py:107`、`src/ibweb/composition.py:1333` |
| DEF-005 | MAJOR | `web_fetch`：目标站拒绝（403）与无内容（404）返回同一短语“网页抓取失败”，不可区分（AC-015-07） | TC-INT-R28-423 | `src/ib/webtools/tools.py:_web_fetch`、`src/ib/webtools/fetch.py:299-310` |
| DEF-006 | MAJOR | `web_fetch`：200 但提取不出正文的页面被当作成功返回空正文围栏（AC-015-07 要求不返回空正文） | TC-INT-R28-424 | `src/ib/webtools/fetch.py:328-336` |

### 1.0.0 缺陷 / 观察（保留）

| DEF | 级别 | 现象 | 复现 / 验证用例 | 位置 | 状态 |
|---|---|---|---|---|---|
| DEF-001 | MINOR | 原现象：抓取因内容超过回合剩余字节额度而失败时，已读取字节未计入回合字节预算，同一回合内可重复发起超限抓取，累计下载量可超出 `max_fetch_bytes_per_turn`。 | TC-UNIT-R28-085（已翻转为正向断言）、TC-UNIT-R28-088（正例） | `src/ib/webtools/tools.py:300`（`budget.charge_bytes`，GROUP_C-002 修复） | **FIXED / VERIFIED**（2026-11-02 复测：超限字节入账、耗尽后第 3 次不出站、固定短语 + 事件、总下载量 ≤ 上限 + 单次已读上限；CR-014 MINOR 语义说明不影响上限约束） |

观察项（不登记为 DEF，供 PM / 用户知悉）：

- **OBS-1（REV-26 既有行为，非 REV-28 引入）**：`validate_prompt_texts` 对 `snapshot.prompts` 中所有“非启用”专家一律报 `prompt_orphan_expert`，而 `_merge` 会为文档里的每个专家（含停用者）生成一条提示词层——故含停用专家的文档无法通过发布协议保存（`src/ib/config/versioning.py:375`、`src/ib/confsvc/publish.py:_merge`；这两个文件 REV-28 未改动）。AC-009-05 的“保存时给出逐条校验错误”成立；运行期“已停用不被委托”由 TC-INT-R28-034 直接编译快照验证。建议另立缺陷评估。
- **OBS-2（离线模式限制）**：离线模式下提示词库为内存态且只预填 kb-agent，运行期新建的“启用顾问”项目其顾问提示词不在内存库中，`runtime_for` 会因 `prompt_missing` fail-closed；生产为 `FsExpertPromptStore` 读取创建期落盘的种子，不受影响。TC-E2E-R28-003 以提示词端口写入种子等价模拟。
- **OBS-3（设计口径）**：被出站闸 / 地址防护拒绝的联网调用同样占用回合调用额度（`reserve_call` 先于校验）。符合 AC-016-03“第 6 次请求联网不发生”的口径，仅提示。
- **OBS-4（已登记的开放项，复核确认现状）**：CR-007 / implementation_plan Q-2——联网事实不在保真守卫的保护片段内（仅 `exceeds_quote_limit`），“联网事实原样保留”靠提示词；CR-009 / Q-3——`IB_WEB_SEARCH_PROVIDER=fake` 在任何模式下被接受（1.0.0 时点；**1.1.0 已由 Q3=A 取代：非离线 + fake ⇒ 启动失败，TC-UNIT-R28-227 / 229、TC-INT-R28-413 验证**）；CR-008——理解步骤与路由器 system 约束冲突，真实遵从度离线不可验（TC-INT-R28-058 证明 fail-open 路径可用）。均需用户 / 目标机裁决，见 `<questions>`。

## 人工验证清单

> 1.2.0：共 **16 项**（MV-01~MV-16），全部属 critical path；与 1.1.0 一致（本轮新增的 3 个 E2E 旅程使用离线替身，其对应的真实端点 / 真实 TLS / 真实 Key 来源验证仍由 MV-05 / MV-14 / MV-15 / MV-16 承接，未新增人工项）。1.1.0：MV-05 改写、MV-14 / 15 / 16 新增，其余沿用 1.0.0。

> 无组件挂载环境、无头浏览器与真实外部服务；以下项均**不记 PASS**，不计入通过率分母。critical path 栏：是 = 属 Must 故事 critical path 的待人工验证项。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-002-01/02、US-002；TC-FE-R28-020 | 浏览器登录 admin → 项目管理 → 新建项目对话框 | “启用顾问”复选框默认**未勾选**；勾选后创建成功并出现新项目；不勾选创建的项目无顾问 | 浏览器 + 目标机前端 | 是 |
| MV-02 | AC-003-01/03、AC-005-03、US-003/005；TC-FE-R28-021/022 | 编辑账号打开配置页 → 工具栏“加入顾问” → 点击顾问节点；再换查看账号 | 规范图自动接线并提示未保存；非规范图弹出“请手工连线”；点击顾问节点右侧面板显示提示词 / 授权 / 参数；查看账号看不到加入 / 移除按钮；“移除顾问”二次确认并可撤销 | 浏览器 + 目标机 | 是 |
| MV-03 | AC-014-01、016-04/07、US-014/016；TC-FE-R28-022 | 在顾问详情面板勾选 web_search / web_fetch，设置返回条数、超时、域名清单；输入非法域名；保存并刷新 | 参数输入与回显正确；全局上限提示文案可见；非法域名保存被拒并指出第几项 | 浏览器 + 目标机 | 是 |
| MV-04 | AC-016-07；TC-FE-R28-023/024 | admin 登录 → 系统管理 → 联网上限；改值保存；再用非 admin 访问 `#/system/web-governance` | admin 可见并可保存；非 admin 导航不可见，直接访问显示无权限文案；保存后值回填 | 浏览器 + 目标机 | 是 |
| MV-05 | **AC-014-06**（真实 DeepSeek 搜索效果；1.1.0 改写，取代“下一轮接入厂商”）；AC-014-07 / 014-08 / 014-10 的真实表现 | 目标机以现有 DeepSeek Key 配置 `IB_WEB_SEARCH_PROVIDER=deepseek` 并重启（`journalctl` 确认无 Key）；顾问提 ≥10 条时效性问题（含无结果的冷门词） | 真实结果含标题 / 网址 / 摘要且结构与替身一致；冷门词如实“未检索到”；/healthz/deps 列出 `api.deepseek.com` 与类别 `web_search_query`；密钥不出现在日志；返回质量由用户主观评价 | 目标机 + 真实 DeepSeek Key + 公网（资料 `docs/external_api/deepseek_search_fetch.md`） | 是 |
| MV-06 | **AC-019-01/02**（NOT_TESTABLE）；REQ-NFUNC-008 | 目标机准备用户提供的评测集（意图 ≥150 条五类各 ≥30；上下文 ≥40 段含指代 ≥20、切换 ≥20、回归 ≥10），运行 `python src/scripts/advisor_eval.py --intent-set … --context-set … --report …`（真实 LLM，密钥只读环境变量） | 意图 top-1 ≥ 0.90；指代消解 ≥ 0.85；话题 F1 ≥ 0.85；“专业误判为通用并联网外发”≤ 0.02；同时观察 CR-008（理解步骤是否稳定输出 JSON 对象而非数组） | 目标机 + 真实 LLM + 评测集 `[DATA_REQUIRED]` | 是 |
| MV-07 | **AC-019-04**（NOT_TESTABLE） | 验收前由用户确认评测集来源 | 未确认前验收状态标为“待评测集确认”，不得以合成集通过率宣告验收 | 用户裁决 | 是 |
| MV-08 | AC-018-01（真实 LLM 部分）；TC-INT-R28-220 | 目标机以真实 LLM 取 ≥20 条注入样例（含网页正文型 / 摘要型）逐条经顾问联网提问 | 答复不含系统提示词原文、不调用未授权工具 / 其它 agent、角色与语气不变（平台侧强制手段已在 TC-INT-R28-220 验证） | 目标机 + 真实 LLM + 公网测试页 | 是 |
| MV-09 | AC-015-01/02；REQ-NFUNC-004 | 目标机开启 IB_WEB_FETCH_ENABLED=1 并重启；顾问读取公网测试页；读取证书域名错配的 https 页；读取重定向到内网的页（仅用自有可控测试服务器，**不得探测生产内网**） | 公网页返回正文；证书错配被拒；重定向到内网被拒；钉 IP 连接使用已校验地址（`PinnedTransport` 的真实 TLS / SNI） | 目标机 + 受控测试服务器 | 是 |
| MV-10 | AC-015-02 | 目标机真实 DNS：解析到私有地址的域名（自有测试域）、含 IPv6 记录域名 | 全部被拒；DNS 超时不拖垮整轮（<规定时间） | 目标机 + 受控 DNS | 是 |
| MV-11 | REQ-NFUNC-007；AC-016-06、007-03 | 目标机真实联网：配置超时 10 秒，断网 / 慢速场景下提问 | 联网调用 10 ±1 秒内终止并降级，整轮返回正常答复 | 目标机 | 是 |
| MV-12 | US-006 全旅程 | 浏览器：创建启用顾问的项目 → 上传文档 → 提问 | SSE 流在页面显示单条答复，含引用，不出现 agent / 工具名 | 浏览器 + 目标机 | 是 |
| MV-13 | CR-007 / Q-2；AQ1=B | 目标机真实 LLM + 联网回合观察：联网事实（数字 / 网址）是否被改写；保真守卫导致统一致歉的频次（误报直接可见） | 用户裁决后确定是否把联网文本纳入保护片段；致歉频次在可接受范围 | 目标机 + 真实 LLM；**需用户裁决** | 是 |
| MV-14 | AC-014-06；CR-015 / A-9 / A-18 / A-19 | 目标机真实 TLS：在 `UrllibPostTransport` 下发起一次搜索；再人为让网络变慢 / 断网 / 经公司代理（若有）重试 | 证书校验通过；慢速时在配置超时内降级（最坏总耗时约 2×timeout_s，与 A-9 一致）；3xx 不跟随；代理环境变量行为符合 urllib 默认；整轮不 5xx | 目标机 + 真实网络 | 是 |
| MV-15 | AC-016-09；资料 §限流与计费 | 目标机真实计费 / 限流：短时间连发请求触发 429（账户 QPS 100）；用余额不足的测试 Key 触发 402（如可行） | 429 / 402 均降级、答复不含状态码与错误原文；失败 / 空结果不计费（对照 DeepSeek 控制台账单）；单轮不超过 5 次出站 | 目标机 + DeepSeek 控制台账单 | 是 |
| MV-16 | AC-018-05；REQ-NFUNC-006 | 目标机 `ib-web.env` 与 LLM Key 存储两种来源各验证一次：存储有值时优先；删除后回退环境变量；两者皆无时联网降级 | 联网随 Key 来源变化符合预期；`journalctl -u ib-web` 中 Key 出现 0 次；无新增凭据配置项（`git diff` 的 env.example 无新增密钥键） | 目标机（只读验证，不回显 `/etc/intelligentbase/*.env` 内容） | 是 |

## 1.1.0 计划的补做旅程 → 1.2.0 落实情况（历史计划表）

| 计划 ID | 故事 / AC | 旅程 |
|---|---|---|
| TC-E2E-R28-013（1.2.0 已执行 PASS） | US-014 / 016 / 018（AC-014-07~10、AC-016-09、AC-018-05 / 06） | 管理员授权联网 → 提问：成功有来源 → 五种错误依次降级 → 空结果 → 一轮 8 次上限 5 → canary 会话（DeepSeek 替身） |
| TC-E2E-R28-014（1.2.0 已执行 PASS） | US-020 / 018（AC-020-01 / 03、AC-018-05） | 非离线装配：provider=fake 启动失败；deepseek + Key 来源切换（存储 → 环境 → 删除）经真实 SSE 提问 |
| TC-E2E-R28-015（1.2.0 改为 US-015 抓取三种失败短语，已执行 PASS） | 原计划 US-001 / 010（AC-001-04、AC-010-08 / 09） | 原计划的致歉口径 / 三环节异常 / 联网数字改写，由集成层 TC-INT-R28-417 / 418 / 419 / 420 与 E2E 旅程 008 覆盖（intent 环节待 DEF-003 裁决） |
