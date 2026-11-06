<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-04T14:37:52+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（REV-28 顾问 agent）

> 修订记录：2.1.0（2026-11-04T14:37:52+08:00）——GROUP_D-005（用户裁决 CL-006 Q1=A：DEF-003 不是缺陷，理解步骤 fail-open 为设计行为，user_stories 5.0.0 AC-010-10）：TC-INT-R28-418[intent] 的缺陷冻结断言（含全部 DEF-003-GUARD 守卫串）移除，改为对 AC-010-10 的正向断言（拆为 TC-INT-R28-425）；418 只保留 [prepare] / [orchestrate]（AC-010-08）；新增 TC-INT-R28-425[intent|resolve]、426[intent|resolve]（AC-010-10）；只改测试与文档，未改产品代码；整层 integration 472 passed；1.2.0（2026-11-03T18:44:10+08:00）——GROUP_D-004（缺陷回流 2/2 复测）：DEF-002/004/005/006 FIXED/VERIFIED（418[prepare]/421/423/424 转绿）；TC-INT-R28-344 由 `["is_external"]` 下标改为 `.get("is_external")`（CR-022，见下）；TC-INT-R28-418[intent] 改为缺陷冻结（DEF-003-GUARD，DEF-003 OPEN 待用户裁决）；整层 integration 469 passed；本层门控 PASSED；1.1.0（2026-11-03T18:27:49+08:00）——GROUP_D-003：新增 `tests/integration/test_deepseek_search_int_r28.py`（TC-INT-R28-400~424，38 项）与基线对比探针 `tests/advisor_r28_builder_probe_support.py` + 黄金 `tests/integration/advisor_r28_builder_golden.json`；整层 integration 431→469；**本层门控 FAILED**（新写 38 项中 5 项因产品缺陷失败，DEF-002~006）；1.0.0 的 98 项与既有 333 项全部仍 PASS；0.2.0（2026-11-02T23:35:17+08:00）——DEF-001 回流复测：本层无用例改动，按 §K 在 DEF-001 修复后复跑，计数不变（431 passed）；单元层 085 翻转、新增 088 见单元报告；0.1.0——初稿。

REV-27 APPROVED 版本已归档于 `archive/rev27/integration_test_report.md`（只读）。

## 摘要

### 2.1.0（GROUP_D-005，DEF-003 裁决后重跑；最后一次整层执行 2026-11-04T14:37:52+08:00 之后，472 passed in 39.91s）

- 命令：`python -m pytest tests/integration -q -p no:cacheprovider`；环境同 1.1.0（离线；autouse 夹具使真实网络连接尝试数 = 0）。
- **用例改动**（`tests/integration/test_deepseek_search_int_r28.py`；只改测试，未改产品代码）：
  | 用例 | 改前 | 改后 |
  |---|---|---|
  | TC-INT-R28-418（原 3 项 `orchestrate|intent|prepare`） | `intent` 项为缺陷冻结：断言当前 fail-open 行为 + 守卫串 `DEF-003-GUARD` | `intent` 项移出；仅保留 `prepare|orchestrate` 两项，均断言 `cs == [ADVISOR_APOLOGY_TEXT]`、HTTP 200、无 error 事件、答复不含异常信息 / 堆栈 / 状态码 / agent 名 / 工具名（AC-010-08 订正后范围，断言强度不变） |
  | TC-INT-R28-425[intent\|resolve]（新写，AC-010-10） | — | 意图识别（替换 `TurnUnderstander.understand` 抛错）/ 问题消解（替换 `understand._parse` 抛错）注入一次未预期异常，原问句“退货期限是多久”：HTTP 200、无 error 事件；恰一条答复，含 kb 结论“7 天”与引用《退换货政策》第 3 条；与 ADVISOR_APOLOGY_TEXT 相同文字出现次数 = 0；异常信息 / 堆栈 / 状态码 / agent 名 / 工具名出现次数 = 0；成对正例：未注入时同一问题同样正常答复 |
  | TC-INT-R28-426[intent\|resolve]（新写，AC-010-10 后半） | — | 同一环节异常且问句含指代“那它呢”（会话无历史，不可消解）：HTTP 200、无 error 事件；答复非空；不含致歉文本；不含异常信息 / 堆栈 / 状态码 / agent 名 / 工具名 |
- **本轮新写**用例（pytest 项）：total = pass + fail + skip + blocked + not_testable = **4 = 4 + 0 + 0 + 0 + 0**（425×2 + 426×2）；改写的 418：3 项 → 2 项（`intent` 项转入 425，守卫串移除）。通过率 = 4/4 = **1.00**。
- **整层**：`tests/integration` **472 passed**（收集 472）= 前值 469 - 1（418[intent] 移出）+ 4（新写）；fail 0；相对前值（1.2.0：469 passed）新增失败 **0**。
- 判定模式：INCREMENTAL / baseline：新增失败 0 且新写用例全部通过。**本层门控：PASSED**。**不再含任何缺陷冻结用例**；`grep -rn DEF-003-GUARD tests` = 0 处。
- **缺陷状态**：DEF-003 → **CLOSED — 按用户裁决为设计行为（CL-006 Q1=A），非缺陷**。DEF-002/004/005/006 沿用 FIXED / VERIFIED；无 OPEN 缺陷。

#### 2.1.0 执行输出

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/integration -q -p no:cacheprovider
472 passed in 39.91s
$ python -m pytest tests/integration --collect-only -q -p no:cacheprovider | grep -cE '::'
472
$ python -m pytest tests/integration/test_deepseek_search_int_r28.py -q -p no:cacheprovider -k "418 or 425 or 426"
6 passed, 35 deselected in 2.55s     # 418[prepare|orchestrate] + 425[intent|resolve] + 426[intent|resolve]
$ grep -rn "DEF-003-GUARD" tests
（无输出）
```

#### 2.1.0 分项结果（AC-010-08 / AC-010-10 拆分）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-INT-R28-418[orchestrate] | AC-010-08 | 委托编排未预期异常 ⇒ 统一致歉，200，无内部信息；成对正例 | 1 | PASS |
| TC-INT-R28-418[prepare] | AC-010-08 | 回合准备未预期异常 ⇒ 统一致歉，200，无内部信息；成对正例 | 1 | PASS |
| TC-INT-R28-425[intent] | AC-010-10 | 意图识别异常 ⇒ fail-open 正常答复（含“7 天”与引用），无致歉、无错误细节、非 5xx | 1 | PASS |
| TC-INT-R28-425[resolve] | AC-010-10 | 问题消解异常 ⇒ 同上 | 1 | PASS |
| TC-INT-R28-426[intent] | AC-010-10 | 指代问句“那它呢”+ 意图识别异常 ⇒ 200，答复非空，无致歉 | 1 | PASS |
| TC-INT-R28-426[resolve] | AC-010-10 | 指代问句“那它呢”+ 问题消解异常 ⇒ 同上 | 1 | PASS |

下文 1.2.0 / 1.1.0 小节为历史记录（其中 418[intent] 与 DEF-003 OPEN / 缺陷冻结的描述已被本小节取代）。

### 1.2.0（GROUP_D-004，缺陷回流 2/2 复测；最后一次整层执行 2026-11-03T18:40:59+08:00 起，469 passed in 39.08s）

- 命令：`python -m pytest tests/integration -q -p no:cacheprovider`；环境同 1.1.0（离线；autouse 夹具使真实网络连接尝试数 = 0）。
- **本轮新写**用例：0；**改动的既有用例 2 个**（见下“本轮用例改动”）。1.1.0 的 38 项（TC-INT-R28-400~424）复跑：total = pass + fail + skip + blocked + not_testable = **38 = 38 + 0 + 0 + 0 + 0**（其中 1 项为**缺陷冻结**：TC-INT-R28-418[intent]，断言当前实际 fail-open 行为并带守卫串 `DEF-003-GUARD`，缺陷 DEF-003 状态 OPEN 待用户裁决）。
- 通过率 = pass/(pass+fail+blocked) = 38/38 = **1.00**（含 1 项冻结用例；去掉冻结用例为 37/37 = 1.00）。
- **整层**：`tests/integration` **469 passed**（收集 469） = 既有 431 + 38；fail 0；相对前值（1.1.0 时点 464 passed + 5 failed）新增失败 **0**，原 5 项失败：418[prepare] / 421 / 423 / 424 转绿（产品已修），418[intent] 改为冻结后绿。
- 判定模式：INCREMENTAL / baseline：新增失败 0 且新写用例全部通过（缺陷冻结用例按 invocation 规定除外，带守卫串并登记缺陷）。**本层门控：PASSED**（带 1 项未裁决缺陷 DEF-003，见“缺陷状态”）。

#### 本轮用例改动（不得放宽其他断言；其余断言逐字未动）

| 用例 | 改前 | 改后 | 原因 |
|---|---|---|---|
| TC-INT-R28-344（`tests/integration/test_advisor_http_int_r28.py`） | `... and not tools["search_knowledge"]["is_external"]`（下标读取） | `... and not tools["search_knowledge"].get("is_external")`（其余三项断言——工具名集合恰为 {search_knowledge, web_search, web_fetch}、`web_search`/`web_fetch` 的 `is_external` 为真、摘要不含凭据哨兵——逐字不变） | DEF-004 修复（`builder/egress.py` 外发序列化时 `is_external` 仅为真保留）后，`search_knowledge` 条目不再输出 `is_external: false`，这正是 AC-017-06（与基线逐字一致）所要求；原下标读取对缺键 `KeyError`，与 TC-INT-R28-421 互相矛盾（CR-022）。“search_knowledge 非外部、web_search/web_fetch 为外部”的语义保持不变（缺键 ⇒ falsy ⇒ 非外部）。 |
| TC-INT-R28-418[intent]（`tests/integration/test_deepseek_search_int_r28.py`，参数化项 `intent`） | 期望 `cs == [ADVISOR_APOLOGY_TEXT]`（意图识别 / 理解步骤异常也返回统一致歉，REQ-FUNC-012 (e1) 字面） | **缺陷冻结**：仅 `intent` 分支断言当前实际行为——HTTP 200、无 error 事件、恰一条答复、**不是**致歉文本、含 kb 原答“7 天”（fail-open 透传、正常答复）、答复不含异常信息 / 堆栈 / agent 名 / 工具名 / “500”；断言消息带守卫串 `DEF-003-GUARD`；`prepare` / `orchestrate` 两项仍断言致歉（原期望不变） | DEF-003 待用户裁决（CR-008 已接受“理解步骤永不阻断问答”设计 vs. AC-010-08 / REQ-FUNC-012 (e1) 字面）。**原期望保留在用例注释与本报告中**，便于裁决后翻转：裁决“致歉” ⇒ 产品改为致歉后此冻结分支会响亮失败，翻转为通用断言 `cs == [ADVISOR_APOLOGY_TEXT]` 并关闭 DEF-003；裁决“fail-open 为正确设计” ⇒ 保留冻结断言、改 AC-010-08 措辞并关闭为 WONTFIX。 |

#### 缺陷状态（集成层相关）

| DEF | 级别 | 复现用例 | 状态 |
|---|---|---|---|
| DEF-002 | MAJOR | TC-INT-R28-418[prepare] | **FIXED / VERIFIED**（回合准备段异常 ⇒ 统一致歉，HTTP 200，无 error 事件、无内部信息；复测 PASS） |
| DEF-003 | MINOR | TC-INT-R28-418[intent]（1.2.0 冻结，守卫串 DEF-003-GUARD） | **2.1.0：CLOSED — 按用户裁决为设计行为（CL-006 Q1=A），非缺陷**（用例已改为正向断言 TC-INT-R28-425 / 426，守卫串已移除） |
| DEF-004 | MINOR | TC-INT-R28-421（+ 344 同源 CR-022） | **FIXED / VERIFIED**（去掉两项联网条目后与基线黄金逐字相同；`search_knowledge` 条目不再带 `is_external`） |
| DEF-005 | MAJOR | TC-INT-R28-423 / 422 | **FIXED / VERIFIED**（403 ⇒ “目标网站拒绝了访问”，404 / 不支持类型 ⇒ “该网页无可用内容”，可区分，均不含状态码 / 错误原文） |
| DEF-006 | MAJOR | TC-INT-R28-424 | **FIXED / VERIFIED**（200 空白页 ⇒ 失败短语“该网页无可用内容”，不再返回空正文围栏） |
| CR-022 | MINOR | TC-INT-R28-344 | 测试侧已改（`.get`）并复测 PASS，由测试工程师关闭 |

### 1.1.0 增量（GROUP_D-003；最后一次整层执行 2026-11-03T18:24~18:26+08:00）

- 环境：同单元层（离线；真实 Django 装配 + 发布协议 + 运行时编译 + LangGraph DAG + 工具循环看门狗 + 出站闸 + 审计 + HTTP 视图；搜索提供方 = **真实的 `DeepSeekSearchProvider` 适配器 + `FakeDeepSeekTransport` 替身**，LLM 为脚本化替身）。autouse 夹具使任何真实网络连接尝试即失败，**尝试数 = 0**（AC-014-06）。
- 命令：`python -m pytest tests/integration -q -p no:cacheprovider`。
- **本轮新写用例**（pytest 项）：total = pass + fail + skip + blocked + not_testable = **38 = 33 + 5 + 0 + 0 + 0**（TC-INT-R28-400~424，25 个用例组，其中 401 参数化 10 项、405 参数化 3 项、418 参数化 3 项）。
- 通过率 = pass/(pass+fail+blocked) = 33/(33+5+0) = 33/38 = **0.8684**。
- **整层**（含既有）：`tests/integration` 469 项 = 前值 431（PM 复跑口径；含 1.0.0 的 98 项）+ 本轮新写 38；**464 passed / 5 failed**；既有 431 项全部 PASS，**失败全部在本轮新写用例内**。
- 判定模式：INCREMENTAL / baseline：要求“新写用例全部通过”——**未满足**（5 项失败，均判为产品缺陷：DEF-002~006，见“失败汇总”）。**本层门控：FAILED**；按 §K 停在本层，E2E 层未执行（见 `e2e_test_report.md`）。
- 成对原则（M-PM-001）：每个降级用例有 happy path 正例——400（成功）↔ 401（10 个错误状态）/ 402；403（空结果）↔ 非空；404（截断 / 空白）↔ 正常检索；408（429 全失败）↔ 成功轮；413（非离线 fake 拒绝）↔ none 可启动；414 ↔ 正确主机；417（致歉）↔ 无失败的中英文正常答复；418（三环节异常）↔ 同一问题未注入的正常答复；422 ↔ 正常页。
- 回归（provider=none 缺省 / 未启用顾问项目逐字一致）：1.0.0 的 TC-INT-R28-100~107、311、323（基线黄金）在本轮整层执行中全部 PASS，未改动。

### 1.0.0 范围（保留，未改动；数字仅描述 1.0.0 时点）

- 执行时间：2026-11-02T23:31:40+08:00（最后一次整层执行；DEF-001 回流复测，本层无用例改动，复跑结果不变）；环境同单元层（`/root/.venvs/intelligentbase/bin/python`，离线；LLM / 搜索 / 抓取传输 / DNS 均为替身；真实 Django 装配 + 发布协议 + 运行时编译 + LangGraph DAG + 工具循环看门狗 + 出站闸 + 审计 + HTTP 视图）。
- 命令：`python -m pytest tests/integration -q -p no:cacheprovider`。
- **本层新写用例**（pytest 项）：total = pass + fail + skip + blocked + not_testable = **98 = 98 + 0 + 0 + 0 + 0**（orchestration 32 + regression 8 + web 38 + http 20；共 77 个用例组 TC-INT-R28-*，其中 TC-INT-R28-220 参数化 22 项）。
- 通过率 = pass/(pass+fail+blocked) = 98/98 = **1.00**。
- **整层**（含基线）：`tests/integration` 431 passed（复跑输出 `431 passed in 37.70s`，收集数 431） = 基线 333（`--ignore-glob='*_r28.py'` 实测）+ 新写 98；fail 0。
- 层间门控输入：上一层（单元）门控 PASSED。判定模式：INCREMENTAL / baseline：相对基线新增失败 **0**，新写用例全部通过。**本层门控：PASSED**。
- 基线对照机制：未启用顾问项目的“同输入逐字相同”用基线黄金文件（`git archive 8d6fd4b src` 解出的基线 src 树运行探针生成，非被测代码自产）比对，见 TC-INT-R28-100~106、311、323。

## 执行输出

### 1.2.0（最后一次执行）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/integration -q -p no:cacheprovider
469 passed in 39.08s
$ python -m pytest tests/integration --collect-only -q -p no:cacheprovider | grep -cE '::'
469
$ python -m pytest tests/integration/test_deepseek_search_int_r28.py tests/integration/test_advisor_http_int_r28.py -q -p no:cacheprovider -k "418 or 344 or 421 or 423 or 424"
7 passed, 51 deselected in 1.42s     # 418[orchestrate/intent/prepare] + 344 + 421 + 423 + 424
```

### 1.1.0（上一次执行，保留；其失败已在 1.2.0 复测中消除或冻结）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/integration -q -p no:cacheprovider
FAILED tests/integration/test_deepseek_search_int_r28.py::test_TC_INT_R28_418_unexpected_exception_in_each_advisor_stage_returns_the_same_apology_over_http_not_5xx[intent]
FAILED tests/integration/test_deepseek_search_int_r28.py::test_TC_INT_R28_418_unexpected_exception_in_each_advisor_stage_returns_the_same_apology_over_http_not_5xx[prepare]
FAILED tests/integration/test_deepseek_search_int_r28.py::test_TC_INT_R28_421_builder_summary_for_unadvised_project_differs_from_baseline_only_by_the_two_web_tool_entries
FAILED tests/integration/test_deepseek_search_int_r28.py::test_TC_INT_R28_423_fetch_refused_by_site_and_no_usable_content_have_distinguishable_reasons
FAILED tests/integration/test_deepseek_search_int_r28.py::test_TC_INT_R28_424_fetch_of_page_with_no_extractable_text_does_not_return_success_with_empty_body
5 failed, 464 passed in 40.48s

$ python -m pytest tests/integration --collect-only -q -p no:cacheprovider | grep -cE '::'
469
$ python -m pytest tests/integration/test_deepseek_search_int_r28.py --collect-only -q -p no:cacheprovider | grep -cE '::'
38
```

AC-017-06 黄金生成命令（一次性，产物已入库 `tests/integration/advisor_r28_builder_golden.json`）：
`git archive 8d6fd4b src | tar -x -C <临时目录> && IB_SRC=<临时目录>/src python tests/advisor_r28_builder_probe_support.py > advisor_r28_builder_golden.json`（基线 src 树生成，非被测代码自产；探针记录 Agent Builder 在 `POST /api/builder/draft` 时发给云端 LLM 的完整载荷）。

### 1.0.0 时点输出（保留）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/integration -q -p no:cacheprovider
........................................................................ [ 66%]
........................................................................ [ 83%]
.......................................................................  [100%]
431 passed in 39.11s

$ python -m pytest tests/integration --collect-only -q -p no:cacheprovider --ignore-glob='*_r28.py' | grep -cE '::'
333
$ python -m pytest tests/integration --collect-only -q -p no:cacheprovider | grep -cE '::'
431
```

基线黄金生成命令（一次性，已入库产物 `tests/integration/advisor_r28_baseline_golden.json`）：
`cd <git archive 8d6fd4b src 解出目录> && IB_SRC=<该目录>/src python tests/advisor_r28_probe_support.py > advisor_r28_baseline_golden.json`；同一探针在当前 src 下重复执行两次输出字节一致（稳定）。

## 分项结果

### 集成边界 E：DeepSeek 联网搜索全链路（适配器 ↔ 出站闸 ↔ 审计 ↔ 工具循环 ↔ 顾问节点 ↔ HTTP；`tests/integration/test_deepseek_search_int_r28.py`，38 项，1.1.0 新增）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-INT-R28-400 | AC-014-07 / AC-018-06 | 成功路径（happy）：3 条结果 ⇒ 工具输出每条含标题·网址·摘要；答复列出标题与网址；请求为资料端点 / POST / Bearer + JSON 头 / 体键集 {query,count,need_content}；审计 host=api.deepseek.com 且无查询原文 | 1 | PASS |
| TC-INT-R28-401 | AC-014-08 | 资料 §错误 的 10 个状态码逐个：整轮正常答复 + “未能联网检索到最新信息”，无 error 事件、无致歉；最坏顾问回显工具输出，答复中状态码 / 错误体 / API Key / Key / Bearer 0 次；仅 1 次出站 | 10 | PASS |
| TC-INT-R28-402 | AC-014-08 | 401、402、429、500、504 依次，用户各提一次：五次降级；期间寒暄与 kb 委托不受影响；之后恢复 ⇒ 成功有来源 | 1 | PASS |
| TC-INT-R28-403 | AC-014-10 | 200 空数组 ⇒ 工具返回“联网检索未找到相关结果”，答复“未检索到相关结果”，答复网址集合为空；非空成对：答复网址 ⊆ 替身返回 | 1 | PASS |
| TC-INT-R28-404 | AC-014-09 | 200 字符检索词 ⇒ 请求 query 恰为前 128 字符；全空白 ⇒ 请求数不增、返回“检索词为空”；整轮正常 | 1 | PASS |
| TC-INT-R28-405 | AC-014-09 / 014-03 | 配置条数 1/5/50 ⇒ 请求体 count 原样；模型传 100 时配置胜出 | 3 | PASS |
| TC-INT-R28-406 | AC-014-09 | 配置保存 max_results=0 / 51 被拒（tool_param_out_of_range，分别指出下界 1 / 上界 50）；50 保存成功并回显 | 1 | PASS |
| TC-INT-R28-407 | AQ6=A / AC-018-06 | region 可配置保存，请求体无 localization 与 region 值；lang 作为资料操作符追加 | 1 | PASS |
| TC-INT-R28-408 | AC-016-09 | 一轮 8 次 web_search、上限 5 ⇒ 请求 5 次，第 6~8 次“已达本轮联网上限”；全 429 同样 5 次且每个检索词恰 1 次（无重试） | 1 | PASS |
| TC-INT-R28-409 | AC-018-06 | canary ×30 段会话（专业问题 + 联网问题）：DeepSeek 替身全部出站请求命中 0；目的地仅资料端点；键集恰三键；正常检索仍出站 30 次；外发声明仅 api.deepseek.com / web_search_query | 1 | PASS |
| TC-INT-R28-410 | AC-018-05 / 018-03 / CR-016 | 哨兵 Key 经 DeepSeek 路径跑 1 成功 + 10 失败：只在传输缝 Authorization 头；日志·审计·答复·healthz·配置目录·定义文档·repr·外发声明 0 次 | 1 | PASS |
| TC-INT-R28-411 | AC-018-05 | 非离线真实装配：仅环境变量 ⇒ 适配器用该 Key；llm_key 存储有值 ⇒ 存储优先；存储清除且环境为空 ⇒ not_configured、外发声明为空；外发声明主机 api.deepseek.com | 1 | PASS |
| TC-INT-R28-412 | AC-018-05 | 非离线装配 + 顾问项目经真实 SSE：有 Key ⇒ 联网成功有来源；删除 Key ⇒ “联网服务未配置”降级，kb 问题正常，HTTP 200 | 1 | PASS |
| TC-INT-R28-413 | AC-020-01 | 非离线 + provider=fake（含大小写 / 空白变体）⇒ StartupError，信息含键名 IB_WEB_SEARCH_PROVIDER、不含 “fake”；Fake 构造 0 次、被调用 0 次；成对：none 可启动且为 Null | 1 | PASS |
| TC-INT-R28-414 | AC-018-05 | deepseek + 非 DeepSeek LLM 主机 ⇒ 启动失败只报键名、不含主机；正确主机可启动 | 1 | PASS |
| TC-INT-R28-415 | AC-020-03 | 离线 + fake / deepseek ⇒ 装配为 Fake 且可用；真实传输构造 0 次 | 1 | PASS |
| TC-INT-R28-416 | AC-014-05 | 端口级 Fake 与 DeepSeek 适配器返回同一组 3 条 ⇒ 顾问收到的工具输出逐字相同（重新发布触发重编译后换提供方） | 1 | PASS |
| TC-INT-R28-417 | AC-001-04 | 汇总失败：中文 / 英文提问的致歉答复逐字相同、中文、英文字母占比 0、无 error 事件；无失败时英文提问得英文答复、中文得中文（成对） | 1 | PASS |
| TC-INT-R28-418[orchestrate] | AC-010-08 | 委托编排（run_dag）未预期异常 ⇒ 经 HTTP SSE 返回统一致歉，200，无内部信息；成对：未注入时正常答复 | 1 | PASS |
| TC-INT-R28-418[intent] | AC-010-08 | 意图识别（理解步骤）未预期异常 ⇒ 期望统一致歉；实际：fail-open 透传，返回**正常答复**（含 kb 原答），无致歉 | 1 | 1.1.0 FAIL → **1.2.0 PASS（缺陷冻结，DEF-003-GUARD；DEF-003 OPEN 待裁决）** |
| TC-INT-R28-418[prepare] | AC-010-08 | 理解之后、进入图之前的回合准备（历史摘要 / 回合对象）未预期异常 ⇒ 期望统一致歉；实际：SSE 返回 `error` 事件（“生成回答时发生错误，请稍后重试”），无致歉 | 1 | 1.1.0 FAIL → **1.2.0 PASS（DEF-002 FIXED / VERIFIED）** |
| TC-INT-R28-419 | AC-010-08 后半 | 联网 503 / 超时、kb-agent 异常 ⇒ 各自降级说明，不使用统一致歉（两类口径不混用） | 1 | PASS |
| TC-INT-R28-420 | AC-010-09 / AC-006-06 | 联网结果数字“37 元”被改写为“约 40 元” ⇒ 不重试、无致歉（顾问被调用 1 次）；反例：kb-agent 数字被改 ⇒ 重试，两次不过致歉 | 1 | PASS |
| TC-INT-R28-421 | AC-017-06 | 未启用顾问项目的 Builder 载荷 vs 基线黄金：去掉 web_search / web_fetch 两条后应与基线逐字相同；实际 `search_knowledge` 条目多出键 `is_external: false` | 1 | 1.1.0 FAIL → **1.2.0 PASS（DEF-004 FIXED / VERIFIED）** |
| TC-INT-R28-422 | AC-015-07（共性） | 403 / 404 / 不支持类型 ⇒ 均为非空失败原因，不含状态码数字 / 错误原文；整轮非 5xx；正常页返回正文（成对） | 1 | PASS |
| TC-INT-R28-423 | AC-015-07（核心） | “目标站拒绝抓取”(403) 与“无可用内容”(404 / 不支持类型) 应返回可区分的失败原因；实际 403 与 404 同为“网页抓取失败” | 1 | 1.1.0 FAIL → **1.2.0 PASS（DEF-005 FIXED / VERIFIED）** |
| TC-INT-R28-424 | AC-015-07 | 提取不出正文的 200 空白页 ⇒ 应返回失败原因、不返回空正文；实际返回“成功 + 空正文”围栏 | 1 | 1.1.0 FAIL → **1.2.0 PASS（DEF-006 FIXED / VERIFIED）** |

（1.1.0 时点）项数合计 38 = PASS 33 + FAIL 5；1.2.0 复测 38 = PASS 38（其中 1 项缺陷冻结）。当时 FAIL 的根因分类全部为**产品缺陷**（测试保持原样作为证据；断言期望值取自 user_stories / 资料 / 基线黄金，不取自被测代码输出）。

全部 **PASS**。

### 集成边界 A：编排器 ↔ 顾问核心 ↔ 被委托 agent ↔ 顾问汇总（MOD-R28-12 ↔ 10；`test_advisor_orchestration_int_r28.py`，32 项）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-R28-001 | AC-006-01/06、010-03 | 专业问题委托 kb-agent（调用 1 次，入参含“退货期限”），顾问汇总为唯一答复，保留“7 天”与《退换货政策》第 3 条，无内部名称，保真一次通过（happy-path） | PASS |
| TC-INT-R28-002 | AC-006-02 | 无资料 ⇒ “知识库中未找到相关资料” + 联系人工 | PASS |
| TC-INT-R28-003 | AC-006-03 / 017-04 | 真实入库 + 真实检索：直达与经顾问委托检索片段逐项相同 | PASS |
| TC-INT-R28-004 | AC-006-05 / 009-04 | kb-agent 超时 ⇒ 正常答复 + “暂时无法查询”，无 error 事件，不泄露内网地址 / 异常类名（与 001 成对） | PASS |
| TC-INT-R28-010 | **AC-006-07** | 汇总步骤失败 ⇒ 统一致歉；不含 ORIG-KB-7DAY / 异常信息 | PASS |
| TC-INT-R28-011 | AC-010-06 | 顾问返回空 ⇒ 同样统一致歉 | PASS |
| TC-INT-R28-012 | **AC-010-06** | contract-agent 作答含 ORIG-AGENT-1，汇总失败 ⇒ 致歉；agent 名 / 工具名 / 路由词 / 异常 0 | PASS |
| TC-INT-R28-013 | **AC-010-07** | 保真两次不过 ⇒ 致歉（顾问被调 2 次，重试提示含“必须原样保留”）；首次不过、第二次通过 ⇒ 正常答复且无致歉（**反例 ↔ 正例成对**） | PASS |
| TC-INT-R28-014 | AC-010-06 | run_dag 未预期异常 ⇒ 响应只含致歉文案 | PASS |
| TC-INT-R28-015 | AC-006-06 | 措辞 / 格式（全角数字）大改但事实保留 ⇒ 不重试 | PASS |
| TC-INT-R28-020 | AC-008-01 | 五类问句：无工具无委托 / 委托 kb / 自身联网不委托 / 委托合同 agent / 礼貌拒答且不含提示词原文；寒暄·通用·拒答不调用路由 L2 | PASS |
| TC-INT-R28-021 | AC-008-02 / 007-04 | 双意图同一答复含知识库与互联网两部分各自标注来源 | PASS |
| TC-INT-R28-022 | AC-008-04 | 空白 / 纯符号 ⇒ 澄清，顾问与工具均未被调用 | PASS |
| TC-INT-R28-023 | AC-008-03 | 路由收到消解后的 delegate 问句；同一问句路由结果与基线（未加入顾问）一致；路由提示词不含历史 | PASS |
| TC-INT-R28-030 | AC-009-01 | 委托 contract-agent 1 次，结果回顾问，唯一答复，无 agent 名 | PASS |
| TC-INT-R28-031 | AC-009-02 | 专家存在但不在路由候选（图中无节点）⇒ ops-agent 调用 0，顾问说明“暂不在我的处理范围” | PASS |
| TC-INT-R28-032 | AC-009-04 | 被委托 agent 超时 ⇒ 如实说明未完成，无致歉文案 | PASS |
| TC-INT-R28-033 | AC-009-03 | 运行期被委托 agent 不再委托；保存时连回顾问之前节点 ⇒ graph_cycle 被拒 | PASS |
| TC-INT-R28-034 | AC-009-05 | 停用 agent：保存被拒（逐条错误，含该 agent 路径）；直接编译已停用快照 ⇒ 运行期委托 0 | PASS |
| TC-INT-R28-040 | AC-010-01 | kb + 联网 + 合同 agent 三路结果合并为一条，保留结论与来源，无“根据 xx agent” | PASS |
| TC-INT-R28-041 | AC-010-04 | 并行两路 ⇒ 1 条答复，两路原始答复（RAW-KB / RAW-CT）独立出现 0 次 | PASS |
| TC-INT-R28-042 | AC-010-02 | 知识库与联网矛盾 ⇒ 指出分歧并分别标注 | PASS |
| TC-INT-R28-043 | AC-010-05 | 未启用顾问项目多专家并行汇总沿用基线（无理解步骤 / 无顾问 / 无致歉） | PASS |
| TC-INT-R28-050 | AC-011-01 / 012-01 | 10 轮后第 11 轮“X 有保修吗”：第 1 轮产品在窗口内，委托问题含“产品X” | PASS |
| TC-INT-R28-051 | AC-011-04 / 011-05 | 第 13 轮：窗口外（第 1 轮）消息不进入顾问 / 理解步骤，最近一轮保留 | PASS |
| TC-INT-R28-052 | **AC-011-05** | 20 条消息超字符预算 ⇒ 顾问收到历史 ≤8000，保留连续最新若干轮，最旧轮整条被裁，最近一条保留；对照：短历史原样 | PASS |
| TC-INT-R28-053 | AC-011-02 | 另一会话 / 另一操作者看不到会话 A 的特征串；同会话下一轮可见 | PASS |
| TC-INT-R28-054 | AC-011-03 | 空闲 25h ⇒ 新会话（历史“（无）”），不报错；对照未超时可见 | PASS |
| TC-INT-R28-055 | AC-012-02/04 | 指代不明 / 首轮残缺追问 ⇒ 澄清，kb-agent·顾问均未调用 | PASS |
| TC-INT-R28-056 | AC-012-01/03 | 追问“它的价格呢”：委托问题与联网查询词均含“产品 X” | PASS |
| TC-INT-R28-057 | AC-013-01~04 | 话题切换不带旧实体、不检索 kb；回归接回；延续沿用实体 | PASS |
| TC-INT-R28-058 | **CR-008** | 理解输出数组 / LLM 抛错 ⇒ fail-open 透传仍委托 kb-agent 并正常作答；答复与“理解成功”完全一致（**降级 ↔ 成功成对**） | PASS |

### 集成边界 B：未启用顾问项目回归集（`test_advisor_regression_int_r28.py`，8 项）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-R28-100 | AC-017-01 | **33(≥30) 条问句**：答复文本、事件序列、路由提示词哈希、外发给 LLM 的载荷（专家系统提示词哈希 + 用户提示词原文）与基线黄金逐项一致；非平凡性守卫 | PASS |
| TC-INT-R28-101 | AC-017-02 | /healthz/deps 与基线一致，无搜索主机 | PASS |
| TC-INT-R28-102 | AC-017-03 / 001-03 / 003-04 | 定义文档、默认图、校验结果、授权、kb 种子、专家表、各 agent 提示词哈希 / 工具与基线一致；无 advisor_id | PASS |
| TC-INT-R28-103 | **AC-017-05** | 可授权工具列表恰多 `web_fetch` / `web_search` 2 项，其余项与顺序不变；参数规格只新增 web_* 前缀项 | PASS |
| TC-INT-R28-104 | 目录 | 配置目录仅追加 `builtin_agents`、`web` 两键 | PASS |
| TC-INT-R28-105 | AC-017-05 | 联网替身已装配，30 条问句：提供方调用 0、出站 0、理解步骤 0、各 agent 工具列表恒为 (search_knowledge)；无致歉 | PASS |
| TC-INT-R28-106 | AC-017-04 | 启用顾问前后，kb-agent 的系统提示词 / 工具 / 步数 / 收到的问题完全一致 | PASS |
| TC-INT-R28-107 | AC-001-03 / 003-01 | 加入前专家集合仅 kb-agent；加入后含顾问；其它项目不受影响 | PASS |

### 集成边界 C：联网链路——授权 / 配置胜出 / 出站闸 / 总开关 / 预算 / 超时 / 安全（`test_advisor_web_int_r28.py`，38 项）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-R28-200 | AC-007-01 / REQ-NFUNC-010 | 授权后联网成功：来源标题 + 网址 + “来自互联网”；审计 web.search（host=fake.invalid，无查询原文） | PASS |
| TC-INT-R28-201 | AC-007-02 / 014-02 / 016-05 | 未授权 ⇒ 不联网（提供方·传输 0）；越权调用被拒；kb-agent 工具列表不含联网工具；取消授权后新会话联网 0 | PASS |
| TC-INT-R28-202 | AC-007-03 | 联网超时降级（“未能联网检索到最新信息”，<5s，无致歉）↔ 同运行时下一次成功有来源（成对） | PASS |
| TC-INT-R28-203 | AC-014-01/03 | 配置 5 条 / 10 秒；LLM 传 100 / 99 ⇒ 提供方实收 5 / 10.0（配置胜出） | PASS |
| TC-INT-R28-204 | AC-014-04 | 未配置提供方 ⇒ “联网服务未配置”，顾问降级；专业问题不受影响；无联网审计（与 200 成对） | PASS |
| TC-INT-R28-210 | **AC-015-05/06、016-08** | ① 总开关缺省关闭 + 已授权：出站 0、如实告知、其余能力（web_search）照常、不写抓取审计；② 重新编译后（运行时绑定装配期开关）打开 ⇒ 抓取正文；③ 开关打开但未授权 ⇒ 不可调用 | PASS |
| TC-INT-R28-211 | AC-015-06 | 配置层 `web_fetch_enabled` 缺省 ⇒ fetcher=None 且外发声明为空；打开 ⇒ fetcher 存在且声明含 web_fetch_url | PASS |
| TC-INT-R28-212 | AC-016-01/02 | 经完整管线：白名单内放行、外部被拒（出站仅 1 次）；黑白名单并存 ⇒ 黑名单优先 | PASS |
| TC-INT-R28-213 | AC-016-03 | 第 6 次联网不发生（提供方调用 5）；新一轮重新计数 | PASS |
| TC-INT-R28-214 | **AC-016-06** | 提供方遵从超时：配置 10 秒 ⇒ 9.0~11.0 秒内返回“联网检索超时”（真实时长） | PASS |
| TC-INT-R28-215 | AC-016-06 | 提供方忽略超时：看门狗在“配置 + 1 秒”处终止，返回“（工具执行超时）”（缩放：1 秒 / 阻塞 4 秒） | PASS |
| TC-INT-R28-220 | **AC-018-01** | 注入集 **22 条**（中英文、零宽字符、伪造围栏、外泄抓取、内网、file://、base64 等）：围栏内数据身份保持；合同 agent 调用 0；越权工具被拒；危险抓取出站 0；顾问输入块不含注入原文（行为改变 0） | PASS ×22 |
| TC-INT-R28-221 | GR-C-001-5 | 注入集规模与多样性守卫（≥20 且覆盖关键类型） | PASS |
| TC-INT-R28-222 | **AC-018-02** | canary：**30 段会话（60 轮，含助手历史含 canary）**——完整 / 24 字符片段 / URL 参数 / URL 编码外发全部被拒，出站载荷与审计中 canary 命中 0；60 次正常检索照常出站（防“全拦”假阳性） | PASS |
| TC-INT-R28-223 | AC-018-03 | 启用联网：启动日志 web_egress 与 /healthz/deps 列出搜索主机与数据类别；密钥哨兵在 healthz·审计·答复·定义文档·目录·日志中出现 0 次 | PASS |
| TC-INT-R28-224 | AC-018-04 | ≥200 字符整段复制 ⇒ 重试要求概括 ⇒ 第二次合格则正常；两次都复制 ⇒ 统一致歉 | PASS |
| TC-INT-R28-225 | REQ-NFUNC-010 | advisor_turn 日志含联网主机与事件摘要，不含查询原文 / 网页正文 | PASS |

### 集成边界 D：HTTP ↔ composition ↔ confsvc / ledger / builder（`test_advisor_http_int_r28.py`，20 项）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-R28-300 | AC-001-01/02/03 | 目录含内置顾问（标签“顾问”、职责、默认授权空）；种子条款与 BLOCKED_TERMS 0 命中；agents 仅 kb-agent；web 概况 | PASS |
| TC-INT-R28-310 | AC-002-01 | admin 勾选启用顾问 ⇒ 201；定义含两专家、规范图（通过校验）、授权（顾问空）、种子逐字落盘 | PASS |
| TC-INT-R28-311 | AC-002-02 | 不勾选 ⇒ 与基线创建结果（黄金 seed_plain：文档 + 提示词文件哈希）逐项相同；不含顾问 / 联网授权 | PASS |
| TC-INT-R28-312 | AC-002-03 | 非 admin 403；enable_advisor 非 bool（5 种）400 且先于创建 | PASS |
| TC-INT-R28-313 | AC-002-04 | 种子失败 ⇒ 整体回滚（无定义文件、注册表项停用），明确错误 project_seed_failed | PASS |
| TC-INT-R28-320 | AC-003-01 | 预检差异含 agent_added 顾问；发布生效；审计记录 | PASS |
| TC-INT-R28-321 | AC-003-02 | 移除顾问后回到未启用行为；审计保留 | PASS |
| TC-INT-R28-322 | AC-003-03 | 查看档 403，版本不变 | PASS |
| TC-INT-R28-323 | AC-003-04 | 未操作项目定义文档与基线黄金逐字节相同 | PASS |
| TC-INT-R28-330 | AC-016-07 | /api/web-governance：admin 读写、逐字段 400（9 种坏体）、非 admin 403、PATCH 405 | PASS |
| TC-INT-R28-331 | **AC-016-07** | 全局 5 次 / 1MB：项目保存 3 次 / 500KB 成功；8 次被拒“超出全局上限（5 次）”；admin 调到 2 次后同值再被拒 | PASS |
| TC-INT-R28-332 | AC-016-04 | 非法域名清单保存被拒（第 2、3 项）；/validate 口径一致；合法清单可保存 | PASS |
| TC-INT-R28-333 | AC-014-01/02 | 未授权却带参数 ⇒ 既有规则拒绝；授权 + 参数保存并回显；kb-agent 无联网授权 | PASS |
| TC-INT-R28-334 | REQ-NFUNC-007 | 上限存储不可读 ⇒ 含联网授权的文档 fail-closed；不含联网授权的文档不受影响 | PASS |
| TC-INT-R28-340 | AC-004-01 | Builder 微调顾问：返回草稿 + 评审三项条款通过；版本与服务端提示词不变 | PASS |
| TC-INT-R28-341 | AC-004-02 | 同文本：顾问口径通过；kb-agent 口径与基线一致（clause_tool_contract 未通过） | PASS |
| TC-INT-R28-342 | AC-004-03 | 禁用词判未通过且不回显 | PASS |
| TC-INT-R28-343 | AC-004-04 | 查看档 Builder 403，云端出站 0 | PASS |
| TC-INT-R28-344 | CR-010 / AC-017-06 | Builder 外发摘要工具名恰为 {search_knowledge, web_search, web_fetch}，web_search / web_fetch 为 is_external，search_knowledge 缺键或假（1.2.0 改 `.get`，见本轮用例改动） | PASS |
| TC-INT-R28-350 | AC-017-02 / 018-03 | 未配置联网 ⇒ healthz 与基线一致；配置搜索提供方后才追加搜索主机与类别 | PASS |

## 与基线对比

| 项 | 基线（PM 实跑 HEAD 8d6fd4b） | 本次（最后一次执行） | 新增失败 |
|---|---|---|---|
| `tests/integration` 整层 | 333 passed（`--ignore-glob='*_r28.py'` 实测） | 431 passed | **0** |
| AQ3=A 调整过的既有断言（3 文件 4 处） | 绿 | 绿（并由 TC-INT-R28-103 以基线黄金独立背书“恰多 2 项”） | 0 |
| `tests/integration` 整层（1.2.0） | 464 passed / 5 failed（1.1.0 时点） | 469 passed | **0** |
| `tests/integration` 整层（1.1.0） | 431 passed（PM 复跑，GROUP_C-003 后） | 464 passed / 5 failed（= 431 既有 PASS + 33 新写 PASS；5 失败均为新写用例） | **既有用例新增失败 0；新写用例失败 5（产品缺陷，非回归）** |
| 既有失败 | 无 | 无 | — |

## 失败汇总（需路由给开发）

### 1.2.0

无新增失败。（2.1.0 更新：DEF-003 已按用户裁决 CLOSED，非缺陷；本节无待路由项。）

### 1.1.0（历史，5 项失败 → 5 个缺陷，均由本轮新写的 AC 验收用例发现）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-INT-R28-418[prepare] | 顾问回合中，理解步骤之后、`run_dag` 之前的回合准备（`build_history_digest` / `AdvisorTurn(...)` / `private_texts_of_history`）出现未预期异常：异常逃出 `_run_dag_turn`，SSE 只有 `error` 事件（“生成回答时发生错误，请稍后重试”），提问者拿不到统一致歉。AC-010-08 / REQ-FUNC-012 (e1) 要求同一致歉。HTTP 状态仍为 200（非 5xx），但答复口径不符 | `src/ib/orchestration/__init__.py:475-483`（try 只包住 `understand` 与 `run_dag`，中间三处调用在 try 之外） | DEF-002（MAJOR） |
| TC-INT-R28-418[intent] | 理解步骤（意图识别 / 问题消解）被注入未预期异常：编排器 fail-open 透传，返回**正常答复**，不是致歉。与 REQ-FUNC-012 (e1) 原文“意图识别、问题消解、委托编排等环节的未预期失败也返回同一致歉文本”不符；但与 CR-008 已接受的“理解步骤永不阻断问答”设计一致（TC-INT-R28-058 即验证该 fail-open）。**需 PM / 用户裁决**：保留 fail-open 并修订 AC-010-08 措辞，或改为致歉 | `src/ib/orchestration/__init__.py:461-466`、`src/ib/advisor/understand.py:166-171` | DEF-003（MINOR，待裁决） |
| TC-INT-R28-421 | 未启用顾问项目的 Agent Builder 发给云端 LLM 的项目摘要，除多出 `web_search` / `web_fetch` 两个工具条目外，`search_knowledge` 条目也多了新键 `is_external: false`（基线无此键）。AC-017-06 要求其余差异字符数 = 0。无业务数据泄露，影响仅为摘要逐字不等 | `src/ib/builder/types.py:107`（`ToolDigest.is_external`）、`src/ibweb/composition.py:1333` | DEF-004（MINOR） |
| TC-INT-R28-423 | 抓取“目标站拒绝”(HTTP 403) 与“无可用内容”(HTTP 404) 都返回同一短语“网页抓取失败”，不可区分；AC-015-07 要求可区分“被拒绝”与“无可用内容”。（原因文本不含状态码与错误原文，该点合格） | `src/ib/webtools/tools.py:_web_fetch`（`result.error == "http_error"` 一律映射“网页抓取失败”）、`src/ib/webtools/fetch.py:299-310` | DEF-005（MAJOR） |
| TC-INT-R28-424 | 目标页 200 但提取不出正文（空白页 / 仅 script）时，`web_fetch` 返回“成功”围栏，标题与正文均为空（`正文：\n\n`）；AC-015-07 要求不返回空正文、给出明确失败原因。顾问可能据此臆测网页内容 | `src/ib/webtools/fetch.py:328-336`（成功分支未检查 `text` 非空）、`src/ib/webtools/tools.py:_web_fetch` | DEF-006（MAJOR） |

1.0.0 观察项（保留）：
1.0.0 时点：本层无失败。

观察项（不是失败，供 PM 决策；详见 `e2e_test_report.md`“缺陷 / 观察”）：
- **TC-INT-R28-034**：基线发布协议对含**停用专家**的文档一律报 `prompt_orphan_expert`（`src/ib/config/versioning.py:375`，REV-26 既有行为，REV-28 未改动）。AC-009-05 的“保存时给出逐条校验错误”因此成立，但“把专家停用后再发布”在基线本就走不通；本用例的运行期部分改为直接编译快照验证。
- **TC-INT-R28-210**：联网运行时在**编译期**绑定装配期的抓取总开关（AC-015-06“重启后生效”的实际机制）——已编译租约内热替换开关不生效，符合设计。
