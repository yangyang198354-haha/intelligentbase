<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-04T14:37:52+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划（REV-28：平台级内置「顾问 agent」）

> 修订记录：2.1.0（2026-11-04T14:37:52+08:00）——GROUP_D-005（用户裁决 CL-006 Q1=A：DEF-003 不是缺陷，理解步骤 fail-open 为设计行为，user_stories 5.0.0 AC-010-10）：TC-INT-R28-418[intent] 的缺陷冻结断言（含全部 DEF-003-GUARD 守卫串）移除，改为对 AC-010-10 的正向断言（拆为 TC-INT-R28-425）；418 只保留 [prepare] / [orchestrate]（AC-010-08）；新增 TC-INT-R28-425[intent|resolve]、426[intent|resolve]（AC-010-10）；只改测试与文档，未改产品代码；AC 映射把 AC-010-08 拆分并新增 AC-010-10；全量 1358 passed（805 + 472 + 66 + 15）；1.2.0（2026-11-03T18:44:32+08:00）——GROUP_D-004（缺陷回流 2/2 复测）：DEF-002/004/005/006 FIXED/VERIFIED；DEF-003 OPEN（待用户裁决），TC-INT-R28-418[intent] 改为缺陷冻结（守卫串 DEF-003-GUARD）；TC-INT-R28-344 改 `.get`（CR-022）；新增 E2E 旅程 TC-E2E-R28-013~015（新文件 `tests/e2e/test_advisor_deepseek_journeys_r28.py`，3 项）补齐 US-020 / DeepSeek 搜索 / 抓取三种失败短语；critical path 覆盖 18/19 → 19/19；新写总数 318+120=438 → 441；1.1.0（2026-11-03T18:27:49+08:00）——GROUP_D-003（requirements_spec / user_stories 4.0.0、module_design 3.0.0、implementation_plan 3.0.0、画像 1.1.0 P11-3）：新增“1.1.0 增量”——3.1.0 新增 / 改写 AC 的映射、DeepSeek 适配器经 `FakeDeepSeekTransport` 的测试策略、Key / 替身生产禁用 / Builder 摘要 / 致歉 / 抓取失败的用例；AC-014-06 由“延至下一轮”改为“自动化只用替身 + 真实效果人工验证”；新增 AC-020-02 N/A；不可测项与 MV 清单更新；0.2.0（2026-11-02T23:35:17+08:00）——DEF-001 回流复测：AC-016-07 映射追加 TC-UNIT-R28-085（翻转）/ 088（新写正例）；新写总数 317→318（unit 208）；DEF-001 FIXED/VERIFIED；0.1.0——初稿。

REV-27 APPROVED 版本已归档于 `archive/rev27/test_plan.md`（只读）；本文件按 REV-28 整体重写。

## 测试策略

- **被测改动**：MOD-R28-01~18（`implementation_plan.md` 改动清单）——核心类型 / 端口、`ib/webtools/`（地址防护、安全抓取、搜索端口适配、出站闸与预算、联网工具）、`ib/advisor/`（理解 / 历史裁剪 / 保真守卫 / 致歉 / 评测指标）、`ib/ledger/web_governance.py` + 迁移 009、配置域（顾问规范图与规则、种子）、工具参数“配置胜出”与看门狗、编排运行期（`dag.py` 顾问节点、`Orchestrator` 理解步骤）、运行时编译、组合根、HTTP 视图（`enable_advisor`、`/api/web-governance`、目录追加键）、selfcheck、`advisor_eval.py`、前端 `advisorPlan.ts` / `client.ts` / 页面。
- **范围（in）**：REQ-FUNC-001~018、REQ-NFUNC-001~011 中可离线验证的部分；US-001~019 的全部 AC（Must 18 个故事、Should 1 个）。
- **范围（out / 不可离线验证）**：真实 DeepSeek 端点效果 / 真实 TLS·超时·代理 / 真实计费（AC-014-06，1.1.0 起改为目标机人工验证）；真实 LLM 的意图 / 上下文精准度与评测集确认（AC-019-01 / 02 / 04）；真实 LLM 对注入指令的“顺从度”（只能验证平台侧强制手段）；真实 TLS 钉 IP 连接 / 真实外网 DNS；目标机时延；浏览器内真实交互（复选框点击、画布拖拽连线、弹窗、联网上限表单）。这些 **不记 PASS**，列入 `e2e_test_report.md` 的人工验证清单。
- **环境**：`/root/.venvs/intelligentbase/bin/python`（仓库根；`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`）；Node v22 + `src/frontend`（`npm run build && npm test`）。全部离线：LLM = 脚本化替身、搜索 = `FakeSearchProvider`、抓取传输 = 假传输（`FakeTransport`）、DNS = 假解析器（另有一组用真实 `getaddrinfo` 只解析本机 / 数字地址）。不连生产、不装依赖、不引入容器。
- **判定模式**：INCREMENTAL / `gate_mode=baseline`——每层相对基线零新增失败且新写用例全部通过才进入下一层；critical path（Must 故事的 E2E 级用例）通过率 1.00。
- **基线（PM 实跑，HEAD 8d6fd4b 改动前）**：`pytest tests` 914 passed；selfcheck 57 PASS / 1 FAIL（`core_framework_free`：sitecustomize，环境性既有失败）；前端 141/141。GROUP_C 后 PM 复跑：pytest 914 passed；selfcheck 64/65（同一既有失败）；前端 build rc=0、141/141。各层基线条数由本人用 `--collect-only --ignore-glob='*_r28.py'` 独立实测：unit 515 / integration 333 / e2e 51（其余 15 例在 `tests/agents`）。
- **用例口径**：“用例”= pytest 项（参数化每个参数一例）；`TC-…` 是用例组（一个测试函数），报告里逐组列出并注明项数。前端用例 ID 为 `TC-FE-R28-*`，在 Python 三层之外独立计数（沿用 R26 / R27 口径）。

### 测试替身与测试数据来源（均为替身，不改产品代码）

| 替身 | 位置 | 说明 |
|---|---|---|
| `ScriptedLlm` | `tests/advisor_r28_support.py` | 在已装配的 `deps.llm` 实例上替换 `build_expert` / `build_router`（同 R26 `ExpertRecorder` 手法）：按 agent 名脚本化作答；工具调用走产品真实 `ib.llm._execute_tool`（真实看门狗线程池 + contextvars）；理解步骤 / 路由 L2 输出可脚本化；“被注入后顺从的 LLM”也由脚本模拟——被测对象是平台侧的强制手段 |
| `FakeSearchProvider` | 产品内置 | 离线搜索提供方（脚本化结果 / 延迟 / 错误） |
| `FakeTransport` + `resolver_map` | `tests/advisor_r28_support.py` | 假抓取传输（记录每次出站 = “出站请求次数”）+ 假 DNS 解析器 |
| 基线黄金文件 | `tests/integration/advisor_r28_baseline_golden.json` | 由**基线 commit 8d6fd4b 的 src 树**（`git archive 8d6fd4b src`）运行 `tests/advisor_r28_probe_support.py` 生成；期望值**不是**用被测代码生成；回归用例用当前 src 重跑探针并逐项比对 |

### 层间口径（各处一致）

| 层 | 内容 | 位置 |
|---|---|---|
| unit | 单模块纯函数 / 注入式替身：地址防护、域名名单、策略、安全抓取、出站闸、联网工具、搜索适配、上限存储与迁移、理解 / 历史裁剪 / 保真 / 致歉 / 指标 / 评测脚本、配置域规则与种子、Builder 评审口径、配置胜出与看门狗 | `tests/unit/test_webtools_netguard_unit_r28.py`、`test_webtools_fetch_gate_unit_r28.py`、`test_webtools_tools_unit_r28.py`、`test_advisor_core_unit_r28.py`（DEF-001 复测：085 由冻结翻转为正向，新增 088 正例） |
| integration | 跨模块：真实装配 + 发布协议 + 运行时编译 + LangGraph DAG + 编排器 + 工具循环 + 出站闸 + HTTP 视图（边界：HTTP ↔ composition ↔ confsvc / ledger / builder；编排器 ↔ 顾问核心 ↔ 联网闸） | `tests/integration/test_advisor_orchestration_int_r28.py`、`test_advisor_regression_int_r28.py`、`test_advisor_web_int_r28.py`、`test_advisor_http_int_r28.py` |
| e2e（替代口径） | 多步 HTTP / SSE 用户旅程（真实账户鉴权 + 发布 + 运行时 + SSE 流）；**非真实浏览器** | `tests/e2e/test_advisor_journeys_r28.py` |
| 前端（独立计数） | unit：`advisorPlan.ts` / `client.ts` 真实执行；integration：源码结构契约；e2e（替代）：纯函数 + 请求形状串联 | `src/frontend/tests/advisor_r28.test.js` |

> 分层标记：Python 以目录为层（pytest 目录分层，无 marker 机制，画像 P3/P4）；前端以 `describe` 分组 + ID 前缀。新文件基名全局唯一并带 `r28` 标记；未新增 `conftest.py`、未新增 `__init__.py`。

### GR-C-001 条件 → 覆盖落点

| 条件 | 覆盖 |
|---|---|
| 1 全部 Must 故事各 ≥1 个真实执行用例；AC→TC 追溯矩阵 | 下方“AC 映射”+ “Must 故事追溯汇总” |
| 2 未启用顾问项目“同输入逐字相同”回归集 | TC-INT-R28-100~107（33 条问句 × {答复、事件序列、路由、外发载荷}、healthz/deps、种子/授权/定义文档/默认图/校验、可授权工具列表恰多 2 项、30 条问句联网工具调用 0）；TC-INT-R28-311（建项目种子）；TC-E2E-R28-010（SSE 旅程对黄金逐项比对） |
| 3 AQ1=B 致歉路径 + 正例 | TC-INT-R28-010~014、015（反例）与 013 / E2E-008（首次不过、第二次通过 ⇒ 正常答复无致歉）；TC-UNIT-R28-140 |
| 4 抓取总开关缺省关闭 | TC-UNIT-R28-080/081、TC-INT-R28-210/211、TC-E2E-R28-006（关闭 ⇒ 出站 0 + 如实告知；开启 ⇒ 可抓取；开启未授权 ⇒ 不可调用） |
| 5 安全集：SSRF ≥30 放行 0 / 注入 ≥20 / canary ≥30 | SSRF 拒绝集 **56 条**（TC-UNIT-R28-001，含 DNS→私有、重定向→私有、IPv6、IPv4-mapped、169.254.169.254、100.64/10）+ 重定向 9 条（TC-UNIT-R28-032）+ 真实解析器本机写法 10 条（TC-UNIT-R28-008）；注入集 **22 条**（TC-INT-R28-220）；canary **30 段会话（60 轮）**（TC-INT-R28-222） |
| 6 fail-open / 降级与 happy-path 成对 | CR-008：TC-UNIT-R28-110（成功）↔ 111/112（降级）、TC-INT-R28-058（三种理解失败 ↔ 成功答复一致）；联网：TC-INT-R28-202（超时降级 ↔ 成功有来源）、204 ↔ 200（未配置 ↔ 已配置）；kb 失败 TC-INT-R28-004 ↔ 001；致歉 010~014 ↔ 013 正例；抓取 080 ↔ 081；重定向拦截 032 ↔ 033 |
| 7 历史裁剪 | TC-UNIT-R28-120~124、TC-INT-R28-051/052 |
| 8 不可测项 → NOT_TESTABLE + 人工验证清单 | 见下“不可测项”与 `e2e_test_report.md` |

## AC 映射

图例：U = 单元，I = 集成，E = E2E 级（替代口径），F = 前端；全部“新写”（既有回归另列）；运行方式均为离线真实执行（P11 为“无”，不适用 sim/hil/manual 分类）。位置缩写：`NG`=`tests/unit/test_webtools_netguard_unit_r28.py`，`FG`=`…test_webtools_fetch_gate_unit_r28.py`，`TL`=`…test_webtools_tools_unit_r28.py`，`CO`=`…test_advisor_core_unit_r28.py`，`OR`=`tests/integration/test_advisor_orchestration_int_r28.py`，`RG`=`…test_advisor_regression_int_r28.py`，`WB`=`…test_advisor_web_int_r28.py`，`HT`=`…test_advisor_http_int_r28.py`，`EJ`=`tests/e2e/test_advisor_journeys_r28.py`，`FE`=`src/frontend/tests/advisor_r28.test.js`。

| AC | 用例 ID（级别） | 位置 | 预期要点 |
|---|---|---|---|
| AC-001-01 | TC-INT-R28-300 (I)、TC-E2E-R28-001 (E) | HT、EJ | 目录同时含 kb-agent 与“顾问”；标签 / 职责 / 默认授权为空 / 默认未加入 |
| AC-001-02 | TC-UNIT-R28-165 (U)、TC-INT-R28-300 (I) | CO、HT | 种子声明面向客户 / 礼貌专业 / 同语言 / 不暴露内部分工 / 如实；BLOCKED_TERMS 0 命中 |
| AC-001-03 | TC-INT-R28-107、TC-INT-R28-300 (I) | RG、HT | 未启用项目专家集合 / 授权不变，顾问不出现在专家列表 |
| AC-002-01 | TC-INT-R28-310 (I)、TC-E2E-R28-003 (E)、TC-FE-R28-011/020 (F) | HT、EJ、FE | 创建成功；两专家 + 规范图（通过校验）+ 种子逐字落盘；请求带 enable_advisor |
| AC-002-02 | TC-INT-R28-311 (I)、TC-FE-R28-010/020 (F) | HT、FE | 不勾选 ⇒ 与基线（黄金）种子逐项相同；默认不勾选；请求体不带键 |
| AC-002-03 | TC-INT-R28-312 (I)、TC-E2E-R28-003 (E) | HT、EJ | 非 admin 403 不创建；非 bool 400 先于创建 |
| AC-002-04 | TC-INT-R28-313 (I) | HT | 种子失败整体回滚，无半成品，明确错误 |
| AC-003-01 | TC-INT-R28-320 (I)、TC-E2E-R28-001 (E) | HT、EJ | 预检差异含“新增 agent：顾问”；生效后专家集合含顾问 |
| AC-003-02 | TC-INT-R28-321 (I)、TC-FE-R28-005 (F) | HT、FE | 移除后回到未启用行为；审计保留 |
| AC-003-03 | TC-INT-R28-322 (I)、TC-E2E-R28-001 (E) | HT、EJ | 查看档 403，版本不变 |
| AC-003-04 | TC-INT-R28-323、TC-INT-R28-102 (I) | HT、RG | 升级后未操作项目定义文档与基线逐字节相同 |
| AC-004-01 | TC-INT-R28-340 (I)、TC-E2E-R28-001 (E) | HT、EJ | 返回草稿 + 三项条款逐项通过；服务端不写 |
| AC-004-02 | TC-UNIT-R28-170/171 (U)、TC-INT-R28-341 (I) | CO、HT | 顾问口径通过；同文本 kb-agent 口径与基线一致（未通过） |
| AC-004-03 | TC-UNIT-R28-172 (U)、TC-INT-R28-342 (I) | CO、HT | 禁用词判未通过且不回显 |
| AC-004-04 | TC-INT-R28-343 (I) | HT | 查看档 Builder 写入 403，云端出站 0 |
| AC-005-01 | TC-E2E-R28-002 (E) | EJ | START→顾问(query_only)→A(with_upstream)→END 通过；A 的输入含顾问产出的上游材料段 |
| AC-005-02 | TC-UNIT-R28-164 (U)、TC-E2E-R28-001 (E) | CO、EJ | 顾问不可达 ⇒ graph_unreachable_from_start，无特例 |
| AC-005-03 | TC-E2E-R28-001 (E)、TC-FE-R28-022 (F) | EJ、FE | 顾问提示词 / 授权 / 参数可读（数据面）；面板结构契约；浏览器点击为人工项 MV-02 |
| AC-005-04 | TC-UNIT-R28-163 (U)、TC-E2E-R28-001 (E) | CO、EJ | 回边成环 ⇒ graph_cycle，无“忽略并继续”；无顾问项目同类校验与基线一致 |
| AC-006-01 | TC-INT-R28-001 (I) | OR | kb-agent 被调用 1 次且入参含“退货期限”；唯一答复含“7 天”与引用，无内部名称 |
| AC-006-02 | TC-INT-R28-002 (I) | OR | 无资料 ⇒ “知识库中未找到相关资料”+ 下一步建议 |
| AC-006-03 | TC-INT-R28-003 (I) | OR | 直达与经顾问委托检索片段逐项相同 |
| AC-006-05 | TC-INT-R28-004 (I) | OR | kb-agent 失败 ⇒ 正常答复 + “暂时无法查询”，无 error 事件 |
| AC-006-06 | TC-INT-R28-001/015 (I)、TC-UNIT-R28-131/132 (U) | OR、CO | 数字与引用位置原样保留，措辞可变；缺失 0 |
| AC-006-07 | TC-INT-R28-010/011/012/014 (I)、TC-E2E-R28-008 (E) | OR、EJ | 汇总失败 ⇒ 统一致歉；答复不含原答特征串 / 内部名 / 异常；HTTP 200 |
| AC-007-01 | TC-INT-R28-200 (I) | WB | 联网成功：来源标题 + 网址 + “来自互联网”；审计先行（无查询原文） |
| AC-007-02 | TC-INT-R28-201 (I) | WB | 未授权 ⇒ 不联网（出站 0），如实说明；越权调用被拒 |
| AC-007-03 | TC-INT-R28-202 (I)、TC-UNIT-R28-072 (U) | WB、TL | 超时降级 ↔ 成功有来源（成对） |
| AC-007-04 | TC-INT-R28-021 (I) | OR | 同一答复分别标明知识库 / 互联网来源 |
| AC-008-01 | TC-INT-R28-020 (I) | OR | 五类问句依次：无工具无委托 / 委托 kb / 自身联网 / 委托合同 agent / 拒答 |
| AC-008-02 | TC-INT-R28-021 (I) | OR | 双意图同一答复含两部分各自标注来源 |
| AC-008-03 | TC-INT-R28-023 (I) | OR | 路由收到消解后问句；结果与基线相同；路由提示词不含历史 |
| AC-008-04 | TC-UNIT-R28-113 (U)、TC-INT-R28-022 (I) | CO、OR | 空白 / 纯符号 ⇒ 澄清，不调用工具 |
| AC-009-01 | TC-INT-R28-030 (I)、TC-E2E-R28-007 (E) | OR、EJ | 委托 contract-agent 1 次，结果回顾问，唯一答复 |
| AC-009-02 | TC-INT-R28-031 (I)、TC-E2E-R28-007 (E) | OR、EJ | 候选外 agent 调用 0 |
| AC-009-03 | TC-INT-R28-033 (I)、TC-UNIT-R28-162/163 (U) | OR、CO | 成环 / 路由候选含顾问 ⇒ 保存被拒；运行期被委托 agent 不再委托 |
| AC-009-04 | TC-INT-R28-032 (I)、TC-E2E-R28-007 (E) | OR、EJ | 被委托 agent 超时 ⇒ 如实说明，整轮正常 |
| AC-009-05 | TC-INT-R28-034 (I) | OR | 停用 agent：保存给出逐条错误；运行期不被委托 |
| AC-010-01 | TC-INT-R28-040 (I) | OR | 三路结果合并为一条，保留结论与来源，无“根据 xx agent” |
| AC-010-02 | TC-INT-R28-042 (I) | OR | 矛盾 ⇒ 指出分歧并分别标注 |
| AC-010-03 | TC-INT-R28-001/015 (I)、TC-UNIT-R28-131 (U) | OR、CO | 单路结果仍统一措辞，事实不增删 |
| AC-010-04 | TC-INT-R28-041 (I)、TC-E2E-R28-007 (E) | OR、EJ | 并行两路 ⇒ 1 条答复，原始答复独立出现 0 次 |
| AC-010-05 | TC-INT-R28-043 (I) | OR | 未启用项目多专家并行汇总沿用基线 |
| AC-010-06 | TC-INT-R28-010/011/012 (I)、TC-UNIT-R28-140 (U)、TC-E2E-R28-008 (E) | OR、CO、EJ | 统一致歉：含“抱歉”+ 下一步建议；原答 / agent 名 / 工具名 / 路由词 / 异常 / 状态码 0；答复数 1 |
| AC-010-07 | TC-INT-R28-013 (I)、TC-E2E-R28-008 (E) | OR、EJ | 保真两次不过 ⇒ 致歉；第二次通过 ⇒ 正常答复无致歉（成对） |
| AC-011-01 | TC-INT-R28-050 (I)、TC-E2E-R28-004 (E) | OR、EJ | 第 11 轮能解析第 1 轮的产品 |
| AC-011-02 | TC-INT-R28-053 (I)、TC-E2E-R28-004 (E) | OR、EJ | 另一会话 / 操作者看不到特征串 |
| AC-011-03 | TC-INT-R28-054 (I) | OR | 空闲 >24h ⇒ 新会话不报错 |
| AC-011-04 | TC-INT-R28-051 (I) | OR | 窗口外消息不进入顾问 / 理解步骤 |
| AC-011-05 | TC-UNIT-R28-120~124 (U)、TC-INT-R28-052 (I) | CO、OR | 超预算最旧优先裁剪、最近一条始终保留、≤20 条原样、窗口外不提供 |
| AC-012-01 | TC-INT-R28-056 (I)、TC-INT-R28-050 (I) | OR | 委托问题 / 联网查询词含消解后的“产品 X” |
| AC-012-02 | TC-INT-R28-055 (I) | OR | 指代不明 ⇒ 澄清，不检索 |
| AC-012-03 | TC-INT-R28-056 (I)、TC-E2E-R28-004 (E) | OR、EJ | 委托含完整问题 |
| AC-012-04 | TC-INT-R28-055 (I) | OR | 首轮残缺追问 ⇒ 澄清，不检索 |
| AC-013-01~04 | TC-INT-R28-057 (I)、TC-UNIT-R28-117 (U)、TC-E2E-R28-004 (E) | OR、CO、EJ | 切换不带旧实体、不检索 kb；回归接回；延续沿用实体；无需显式声明 |
| AC-014-01 | TC-INT-R28-203 (I)、TC-INT-R28-333 (I) | WB、HT | 勾选 + 条数 5 / 超时 10 保存并回显 |
| AC-014-02 | TC-INT-R28-201 (I)、TC-INT-R28-333 (I)、TC-UNIT-R28-181 (U) | WB、HT、CO | 未授权 agent 工具列表不含联网工具，调用 0 |
| AC-014-03 | TC-UNIT-R28-075/180 (U)、TC-INT-R28-203 (I) | TL、CO、WB | LLM 传 100 / 99 ⇒ 配置胜出（5 / 10 秒） |
| AC-014-04 | TC-UNIT-R28-071 (U)、TC-INT-R28-204 (I) | TL、WB | 未配置 ⇒ “联网服务未配置”，其余意图不受影响 |
| AC-014-05 | TC-UNIT-R28-090 (U) | TL | 两个提供方替身返回结构一致 |
| AC-014-06 | **NOT_TESTABLE**（TC-UNIT-R28-092 仅守卫“本轮无厂商端点 / 网络导入”） | TL | 真实厂商结果下一轮 / 人工 |
| AC-015-01 | TC-UNIT-R28-030/081 (U) | FG、TL | 标题 + 最终网址 + 正文 ≤ 上限，剔除 script/style/nav |
| AC-015-02 | TC-UNIT-R28-001/008/032/082 (U) | NG、FG、TL | 内网 / 元数据 / DNS 私有 / 重定向私有全部被拒；出站仅首跳 |
| AC-015-03 | TC-UNIT-R28-004/082 (U) | NG、TL | file:// ftp:// ⇒ scheme_not_allowed |
| AC-015-04 | TC-UNIT-R28-036/037/084 (U) | FG、TL | 二进制 / 超限 ⇒ 明确原因 |
| AC-015-05 | TC-UNIT-R28-080 (U)、TC-INT-R28-210 (I)、TC-E2E-R28-006 (E) | TL、WB、EJ | 总开关关闭 ⇒ 出站 0 + “当前未开启网页抓取”，其余能力照常 |
| AC-015-06 | TC-INT-R28-210/211 (I)、TC-E2E-R28-006 (E)、TC-UNIT-R28-081 (U) | WB、EJ、TL | 缺省关闭；打开后可抓取；打开未授权仍不可调用 |
| AC-016-01 | TC-UNIT-R28-010/083 (U)、TC-INT-R28-212 (I)、TC-E2E-R28-005 (E) | NG、TL、WB、EJ | 白名单放行 / 外部被拒 |
| AC-016-02 | TC-UNIT-R28-011/083 (U)、TC-INT-R28-212 (I) | NG、TL、WB | 黑名单优先 |
| AC-016-03 | TC-UNIT-R28-063/073/074 (U)、TC-INT-R28-213 (I) | FG、TL、WB | 第 6 次不发生（提供方调用 5） |
| AC-016-04 | TC-UNIT-R28-012/022 (U)、TC-INT-R28-332 (I) | NG、HT | 非法域名保存被拒，指出第几项 |
| AC-016-05 | TC-INT-R28-201 (I)、TC-E2E-R28-005 (E) | WB、EJ | 取消授权 ⇒ 新会话联网 0 + 降级 |
| AC-016-06 | TC-INT-R28-214/215 (I)、TC-UNIT-R28-182 (U) | WB、CO | 提供方遵从超时：10 ±1 秒（真实时长）；看门狗终止忽略超时者 |
| AC-016-07 | TC-UNIT-R28-020/021/085/088/100 (U)、TC-INT-R28-330/331 (I)、TC-E2E-R28-012 (E)、TC-FE-R28-012/E02 (F) | NG、TL、HT、EJ、FE | 3 次 / 500KB 成功；8 次被拒“超出全局上限（5 次）”；非 admin 403；运行期 min(参数, 全局) |
| AC-016-08 | TC-INT-R28-210 (I)、TC-E2E-R28-006 (E) | WB、EJ | 授权保存成功，但总开关关闭 ⇒ 出站 0 + 如实告知；开关与授权各自独立 |
| AC-017-01 | TC-INT-R28-100 (I)、TC-E2E-R28-010 (E)、全量回归 | RG、EJ | 33 条问句答复 / 事件 / 路由 / 外发载荷与基线逐项一致；全量零新增失败 |
| AC-017-02 | TC-INT-R28-101/350 (I) | RG、HT | healthz/deps 与基线一致，无搜索主机；配置后才追加 |
| AC-017-03 | TC-INT-R28-102 (I) | RG | kb 种子 / 授权 / 参数 / 定义文档 / 默认图 / 校验与基线一致 |
| AC-017-04 | TC-INT-R28-106 (I) | RG | 启用顾问不影响 kb-agent 路径（提示词 / 工具 / 步数 / 收到的问题） |
| AC-017-05 | TC-INT-R28-103/104/105 (I) | RG | 可授权工具列表恰多 2 项；30 条问句联网调用 0、未授权 agent 工具列表不含 |
| AC-018-01 | TC-INT-R28-220/221 (I)、TC-E2E-R28-009 (E)、TC-UNIT-R28-053/078 (U) | WB、EJ、FG、TL | 注入集 22 条：围栏 / 越权被拒 / 危险抓取不出站 / 合同 agent 调用 0 |
| AC-018-02 | TC-INT-R28-222 (I)、TC-E2E-R28-009 (E)、TC-UNIT-R28-050/051/076/086 (U) | WB、EJ、FG、TL | canary 30 段会话出站命中 0，正常检索仍出站 |
| AC-018-03 | TC-INT-R28-223/225/350 (I) | WB、HT | 启动日志 / healthz 列出搜索主机与类别；密钥哨兵 0 次出现 |
| AC-018-04 | TC-INT-R28-224 (I)、TC-UNIT-R28-135 (U) | WB、CO | ≥200 字符整段复制 ⇒ 重试要求概括；两次都复制 ⇒ 致歉 |
| AC-019-01 | **NOT_TESTABLE**（真实 LLM + 用户评测集，目标机） | — | 人工验证清单 MV-06 |
| AC-019-02 | **NOT_TESTABLE**（同上） | — | 人工验证清单 MV-06 |
| AC-019-03 | TC-UNIT-R28-150/151/152 (U)、TC-E2E-R28-011 (E) | CO、EJ | 指标手算值一致；评测 CLI 判定逻辑（替身）；标注真实精准度需人工 |
| AC-019-04 | **NOT_TESTABLE**（流程性：评测集来源确认） | — | 人工验证清单 MV-07 |

**非功能需求落点**：REQ-NFUNC-001 → TC-INT-R28-100~107；003 → TC-INT-R28-220/221；004 → TC-UNIT-R28-001~008/032；005 → TC-INT-R28-222；006 → TC-INT-R28-223；007 → TC-UNIT-R28-072、TC-INT-R28-202/214/215；008 → TC-UNIT-R28-150~152、TC-E2E-R28-011（真实精准度人工）；009 → TC-UNIT-R28-120~124、TC-INT-R28-051/052；010（审计 / 日志）→ TC-INT-R28-200/225、TC-UNIT-R28-060/183。

**既有测试（回归用）**：AQ3=A 调整过的 3 个文件 4 处断言——`tests/integration/test_prompt_config_r16.py::test_TC_INT_R16_prompt_list_contract`、`tests/integration/test_prompt_tool_config_int_r16d.py::test_TC_INT_136_single_registration_point_tools_and_params`、`tests/unit/test_prompt_tool_config_unit_r16d.py::test_TC_UNIT_123_search_tool_spec_exposes_optional_retrieval_param_specs`。本人复核：仅放行“其余项恰为 web_search / web_fetch”，`search_knowledge` 的精确断言保留，未放宽无关断言；其“恰多 2 项”口径另由 TC-INT-R28-103 以基线黄金独立背书。

### Must 故事追溯汇总（每个 Must 故事至少 1 个真实执行用例）

| 故事 | 用例组 |
|---|---|
| US-001 | INT-300、INT-107、UNIT-165、E2E-001 |
| US-002 | INT-310/311/312/313、E2E-003、FE-010/011/020 |
| US-004 | INT-340~343、UNIT-170~172、E2E-001 |
| US-005 | E2E-002、E2E-001、UNIT-161~164、FE-022 |
| US-006 | INT-001~004、010~015、UNIT-130~135、E2E-004/008 |
| US-007 | INT-200~202、021、UNIT-070~078 |
| US-008 | INT-020~023、UNIT-110~117 |
| US-009 | INT-030~034、E2E-007 |
| US-010 | INT-040~043、010~015、E2E-007/008 |
| US-011 | INT-050~054、UNIT-120~124 |
| US-012 | INT-050/055/056 |
| US-013 | INT-057、E2E-004 |
| US-014 | UNIT-070~075/090、INT-203/204/333 |
| US-015 | UNIT-030~041/080~084、INT-210/211、E2E-006 |
| US-016 | UNIT-010~022/063/073~074/100、INT-212~215/330~332、E2E-005/012 |
| US-017 | INT-100~107、350、E2E-010 |
| US-018 | UNIT-050~053/060~065、INT-220~225、E2E-009 |
| US-019 | UNIT-150~152、E2E-011（AC-019-03；AC-019-01/02/04 为 NOT_TESTABLE） |
| US-020（1.1.0 新增 Must） | UNIT-227~229、INT-413/415、**E2E-014**（1.2.0）；AC-020-02 为 N/A |
| US-003（Should） | INT-320~323 |

## 1.1.0 增量：DeepSeek 联网搜索（CP-003 Q7 纳入）与 3.1.0 新增 / 改写 AC

### 增量测试策略

- **被测改动**：MOD-R28-03（`deepseek.py` 适配器与 `HttpPostTransport` 缝、`deepseek_double.py` 替身、`search.py` 工厂的离线 / 生产闸）、IFC-R28-031（`resolve_llm_api_key`）、IFC-R28-032（`validate_required` 值域与 LLM 主机校验）、`tools.py` 的 128 / 50 边界、顾问致歉 / 其他未预期异常（Q4=A）、保真范围（Q1=A）、Builder 摘要（Q2=A）。
- **闭源 API 纪律（画像 P11-3）**：无官方沙箱，**只用项目离线替身** `FakeDeepSeekTransport`（按资料字段与错误码构造）；每个 DeepSeek 用例文件带 autouse 夹具，把 `socket.socket.connect` / `socket.create_connection` / `socket.getaddrinfo` 置为“调用即失败”并在 teardown 断言尝试数为 0 ⇒ **发往真实端点 / 任何外网的请求数 = 0**（AC-014-06）。真实 `UrllibPostTransport` 只经打桩 opener 验证（方法 / 头 / 错误映射 / 超时 / 不跟随重定向），真实 TLS、超时与代理行为列入人工清单（MV-14）。
- **期望值出处**：端点 / 头 / 字段 / 范围 / 状态码来自 `docs/external_api/deepseek_search_fetch.md`（用例内以字面量复述，不引用被测常量作期望）；降级类别来自 module_design IFC-R28-029 状态码映射表；AC-017-06 的期望值来自**基线 commit 8d6fd4b 的 src 树**运行探针所得黄金文件（`tests/advisor_r28_builder_probe_support.py` → `tests/integration/advisor_r28_builder_golden.json`）；不取自被测代码输出。资料未给的超时数值不断言具体秒数（只断言 `query.timeout_s` 原样传给传输缝）。
- **哨兵 Key**：测试占位串（非真实凭据）；断言口径 = 只出现在替身记录的 Authorization 请求头，在日志·异常·repr·健康检查·外发声明·答复·审计·定义文档·配置目录中出现 0 次（补回 CR-016 缩小的覆盖）。
- **配对原则**：每个降级用例配 happy path 正例（见各用例描述）。
- **最坏 LLM**：脚本化顾问把工具输出原样回显进答复，以证明状态码 / 错误原文 / Key 不在工具输出里（被测对象是平台侧映射与围栏，不是 LLM 自觉）。
- **新文件**：`tests/unit/test_deepseek_search_unit_r28.py`（82 项）、`tests/integration/test_deepseek_search_int_r28.py`（38 项）、`tests/advisor_r28_builder_probe_support.py` + `tests/integration/advisor_r28_builder_golden.json`；未新增 `conftest.py` / `__init__.py`；基名全局唯一并带 `r28`。
- **基线（PM 复跑，GROUP_C-003 后）**：pytest 1232 passed（unit 723 / integration 431 / e2e 63 / agents 15，本人 `--collect-only` 实测同）；selfcheck 68/69（`core_framework_free` 既有环境性）；前端 160/160。原始基线（8d6fd4b）914 / 57+1 / 141。
- **门控结论（1.1.0 时点，历史）**：unit PASSED（82/82）→ integration FAILED（33/38，5 项产品缺陷 DEF-002~006）⇒ E2E 层未执行。
- **门控结论（1.2.0，GROUP_D-004）**：unit PASSED（805/805）→ integration PASSED（469 passed；新写 38/38，含 1 项缺陷冻结）→ e2e PASSED（66 passed；critical path 15/15，覆盖 19/19）；全量 1355 passed；selfcheck 68/69（既有 `core_framework_free`）；前端 160/160。

### 3.1.0 新增 / 改写 AC → 用例映射（全部“新写”；位置缩写：`DU`=`tests/unit/test_deepseek_search_unit_r28.py`，`DI`=`tests/integration/test_deepseek_search_int_r28.py`，`EN`=`tests/e2e/test_advisor_deepseek_journeys_r28.py`）

| AC | 用例 ID（级别） | 位置 | 预期要点 | 本轮结果 |
|---|---|---|---|---|
| AC-001-04 | TC-INT-R28-417 (I)、TC-UNIT-R28-234 (U) | DI、DU | 汇总失败：中文 / 英文提问的致歉文本逐字相同、中文、英文字母占比 0、非 5xx；无失败时英文提问英文答复（成对） | PASS |
| AC-010-08 | TC-INT-R28-418[orchestrate\|prepare] (I)、TC-INT-R28-419 (I) | DI | （5.0.0 订正范围）委托编排 / 回合准备两环节异常 ⇒ 同一致歉（HTTP 200、无内部信息）；已有降级情形不混用致歉 | 418[orchestrate] PASS；418[prepare] PASS（DEF-002 FIXED / VERIFIED）；419 PASS |
| AC-010-10 | TC-INT-R28-425[intent\|resolve] (I)、TC-INT-R28-426[intent\|resolve] (I) | DI | 意图识别 / 问题消解异常 ⇒ fail-open 按原问句正常答复（含 kb 结论与引用；无致歉文字、无异常信息 / 堆栈 / 状态码 / agent 名 / 工具名；200 非 5xx）；指代问句“那它呢”同环节异常 ⇒ 仍 200、无致歉 | 全部 PASS（2.1.0；取代 1.2.0 的 418[intent] 缺陷冻结） |
| AC-010-09 | TC-INT-R28-420 (I) | DI | 联网数字改写不触发致歉（顾问仅调用 1 次）；反例：被委托 agent 数字被改 ⇒ 重试 + 致歉 | PASS |
| AC-014-05（改写） | TC-UNIT-R28-219 (U)、TC-INT-R28-416 (I) | DU、DI | 端口级 Fake 与 DeepSeek 适配器同一组结果 ⇒ 工具输出逐字相同 | PASS |
| AC-014-06（改写） | TC-UNIT-R28-200 / 218 / 223 / 225 / 226 (U)、TC-INT-R28-400 (I)、两文件 autouse 零网络夹具 | DU、DI | 自动化只用替身，真实端点 / 外网连接尝试 = 0；替身按资料校验请求；真实效果列人工清单（MV-05 / MV-14） | PASS（真实效果为人工项） |
| AC-014-07 | TC-UNIT-R28-206 / 219 (U)、TC-INT-R28-400 (I) | DU、DI | 每条结果含非空标题 / 网址 / 摘要；答复列出标题与网址 | PASS |
| AC-014-08 | TC-UNIT-R28-208~213 / 221 / 224 / 225 (U)、TC-INT-R28-401 / 402 (I) | DU、DI | 资料 10 个状态码 + 超时 / 不可达 ⇒ 降级说明、非 5xx、答复中状态码·错误原文·Key 0 次；五状态依次；其余意图不受影响 | PASS |
| AC-014-09 | TC-UNIT-R28-202~205 / 220 (U)、TC-INT-R28-404 / 405 / 406 (I) | DU、DI | 保存 0 / 51 被拒（指出 1–50）、50 通过；200 字符检索词 ⇒ ≤128；全空白不出站 | PASS |
| AC-014-10 | TC-UNIT-R28-207 (U)、TC-INT-R28-403 (I) | DU、DI | 200 空数组 ⇒ 如实说明、不虚构来源（答复网址 ⊆ 替身返回） | PASS |
| AC-015-02（改写） | 沿用 1.0.0 的 TC-UNIT-R28-001 / 008 / 032 / 082；本轮补：TC-INT-R28-409 目的地仅 api.deepseek.com | NG、FG、TL、DI | 内网·元数据·重定向被拒；DeepSeek 出站目的地仅搜索端点 | PASS |
| AC-015-07 | TC-INT-R28-422 / 423 / 424 (I) | DI | 403 / 404 / 无正文 ⇒ 明确失败原因、可区分、不返回空正文、答复无状态码与错误原文；ADR-R28-12 保留本地抓取，故用 `SafeFetcher` + 假传输模拟 | 422 / 423 / 424 PASS（DEF-005 / DEF-006 FIXED / VERIFIED）；E2E 旅程 TC-E2E-R28-015 复验 |
| AC-016-09 | TC-UNIT-R28-214 / 222 (U)、TC-INT-R28-408 (I) | DU、DI | 一轮 8 次、上限 5 ⇒ 请求 ≤5；429 也计入；不重试 | PASS |
| AC-017-06 | TC-INT-R28-421 (I) | DI | Builder 摘要与基线黄金逐字比对：差异仅两个联网工具条目 | PASS（DEF-004 FIXED / VERIFIED；同源 TC-INT-R28-344 改 `.get`，CR-022） |
| AC-018-03（改写） | TC-UNIT-R28-217 (U)、TC-INT-R28-409 / 410 (I) | DU、DI | 外发声明含 api.deepseek.com（独立条目，类别 web_search_query）；凭据 0 次 | PASS |
| AC-018-05 | TC-UNIT-R28-216 / 228 / 230 / 231 / 232 (U)、TC-INT-R28-410 / 411 / 412 / 414 (I) | DU、DI | Key 与 LLM 同源（存储优先、环境回退）；新增凭据配置项 0；Key 只在请求头；删除 Key ⇒ 明确降级；LLM 主机非 DeepSeek ⇒ 启动失败只报键名 | PASS |
| AC-018-06 | TC-UNIT-R28-200 / 201 / 233 (U)、TC-INT-R28-407 / 409 (I) | DU、DI | 请求体键集恰三键；canary ×30 命中 0；目的地仅 DeepSeek 端点；region 被忽略（AQ6） | PASS |
| AC-020-01 | TC-UNIT-R28-227 / 229 (U)、TC-INT-R28-413 (I) | DU、DI | 非离线 + fake ⇒ 启动失败，错误含键名、不含值；Fake 构造 / 调用 0；不静默回退 | PASS |
| AC-020-02 | **N/A（NOT_TESTABLE：设计未选该形态）** | — | 架构 ADR-R28-13 选择“启动失败”形态，不存在“提供方不可用”的运行形态；其用户可见语义（联网按未配置降级、非 5xx、其余能力正常）由 AC-014-04（TC-UNIT-R28-071、TC-INT-R28-204）与 AC-018-05 删除 Key 用例（TC-INT-R28-412）等价覆盖 | 不计入分母 |
| AC-020-03 | TC-UNIT-R28-227 / 228 / 229 (U)、TC-INT-R28-415 (I) | DU、DI | 离线 + 替身可用（AC-014-05~10 用例即在此下执行）；非离线替身被调用 0 次 | PASS |
| **1.2.0 补充（E2E 级）** AC-014-07~10、016-09、018-05 / 06 | TC-E2E-R28-013 (E) | EN | 编辑者发布授权 ⇒ SSE 提问：成功有来源 → 401/402/429/500/504 依次降级（kb 不受影响）→ 空结果 → 一轮 5 次检索上限 3 → canary 检索词被拒 → 审计无查询原文 → 恢复成功 | PASS |
| **1.2.0 补充（E2E 级）** AC-020-01 / 020-03、AC-018-05 | TC-E2E-R28-014 (E) | EN | 离线 + 替身提供方 SSE 联网可用；非离线 + fake ⇒ StartupError（含键名不含值，Fake 构造 0）；非离线 deepseek：环境 Key → 存储优先 → 删除 ⇒ 降级，kb 正常 | PASS |
| **1.2.0 补充（E2E 级）** AC-015-07 | TC-E2E-R28-015 (E) | EN | 经 SSE：403 ⇒ “目标网站拒绝了访问”、404 / 不支持类型 ⇒ “该网页无可用内容”、200 空白页 ⇒ 失败短语（非空正文围栏）；三者可区分、不含状态码 / 错误原文；正常页返回正文 | PASS |
| AC-006-06（措辞）/ AC-014-04 / AC-017-01（provider=none 缺省行为不变） | 沿用 1.0.0 回归集 TC-INT-R28-100~107、204、311、323；本轮 TC-UNIT-R28-228（none ⇒ Null）、TC-INT-R28-413（none 可启动且为 Null） | RG、WB、DU、DI | 缺省行为与上一轮一致；未启用顾问项目回归黄金集逐字一致 | PASS |

**非功能落点（1.1.0）**：REQ-NFUNC-005 → TC-UNIT-R28-200 / 201 / 233、TC-INT-R28-407 / 409；006 → TC-UNIT-R28-216 / 231 / 232、TC-INT-R28-410 / 411；011 → TC-UNIT-R28-208~213 / 221、TC-INT-R28-401 / 402。

### 1.1.0 测试数据需求

- 全部脚本内合成；哨兵 Key 为占位串；AC-017-06 黄金文件为唯一新增持久夹具（来源：基线 src 树探针，生成命令见 `integration_test_report.md`）。
- `[DATA_REQUIRED]`：无新增（真实 DeepSeek 响应样本需目标机人工验证，见 MV-05 / MV-14 / MV-15 / MV-16）。

## 1.2.0 增量（GROUP_D-004，缺陷回流 2/2 复测）

- **范围**：复测 DEF-002/004/005/006（已修）；冻结 DEF-003（待用户裁决）；修 CR-022（测试 344）；补 E2E 层 TC-E2E-R28-013~015，使 Must Have 故事 19/19 有 E2E 级用例。**不改产品代码**。
- **E2E 旅程编号调整**：1.1.0 计划的 TC-E2E-R28-015（致歉三环节）改由集成层 TC-INT-R28-417 / 418 / 419 / 420 覆盖（含 HTTP SSE，且 418[intent] 待 DEF-003 裁决），E2E 层 015 改为 US-015 抓取三种失败短语（invocation 指定）；TC-E2E-R28-008 仍覆盖致歉旅程。
- **新文件**：`tests/e2e/test_advisor_deepseek_journeys_r28.py`（3 项；基名全局唯一，带 `r28`；未新增 `conftest.py` / `__init__.py`）；autouse 零真实网络夹具（`socket.connect` / `create_connection` / `getaddrinfo` 调用即失败，teardown 断言尝试数 = 0）。
- **缺陷冻结用例**：TC-INT-R28-418[intent]，守卫串 `DEF-003-GUARD`；原期望（致歉）保留在用例注释与集成报告，裁决后翻转。
- **基线（PM 复跑，C-004 后）**：pytest 2 failed / 1350 passed（418[intent]、344）；selfcheck 68/69；前端 160/160。本人最后一次全量：1355 passed（805 unit + 469 integration + 66 e2e + 15 agents）。
- **不可测项（1.2.0）**：沿用 1.1.0；MV 清单仍 16 项（US-020 的真实装配 / 目标机 Key 来源验证已含于 MV-16；真实 TLS 等含于 MV-14）。

## 2.1.0 增量（GROUP_D-005，DEF-003 裁决）

- **依据**：用户裁决 CL-006 Q1=A（经主会话转述）：DEF-003 不是缺陷，理解步骤（意图识别、问题消解）未预期异常 fail-open 照常作答；user_stories 5.0.0 修订 AC-010-08（只覆盖委托编排与回合准备）并新增 AC-010-10。
- **范围**：仅改测试与测试文档，**未改产品代码**，不联网。418[intent] 的缺陷冻结（守卫串 `DEF-003-GUARD`）移除；新增 TC-INT-R28-425 / 426（各 `intent|resolve` 两项，共 4 项）；AC 映射表已把 AC-010-08 与 AC-010-10 分行。其余 1.2.0 增量节中关于 DEF-003 “冻结 / 待裁决”的描述为历史记录。
- **注入点**：intent = 替换 `TurnUnderstander.understand` 抛错；resolve = 替换 `ib.advisor.understand._parse` 抛错（消解结果解析 / 校验环节）；prepare = `build_history_digest`；orchestrate = `run_dag`。
- **门控结论（2.1.0）**：unit PASSED（805/805）→ integration PASSED（472 passed；新写 4/4）→ e2e PASSED（66 passed；critical path 15/15，覆盖 19/19）；全量 1358 passed（805 + 472 + 66 + 15）；selfcheck 68/69（既有 `core_framework_free`）；前端 160/160。DEF-003 CLOSED（设计行为）；无 OPEN 缺陷。
- **不可测项 / 测试数据**：无变化。

## 测试数据需求

- 全部为脚本内合成数据，无外部数据文件依赖；唯一持久化夹具为基线黄金 `tests/integration/advisor_r28_baseline_golden.json`（来源：基线 src 树运行探针，见上）。
- 会写入持久存储的数据：HTTP 旅程中创建的项目 / 用户均走每用例独立的内存装配（`build_deps(force=True)`）或 `tmp_path`；不写仓库目录；无需唯一化。
- 凭据：无真实凭据；`TC-INT-R28-223` 用哨兵串（非真实密钥）验证“密钥 0 次出现”。
- `[DATA_REQUIRED]`：真实评测集（意图 ≥150 条、上下文 ≥40 段）由用户提供，**标 `[DATA_REQUIRED: 用户提供的评测集，OQ-R28-12]`**，对应 AC-019-01 / 02 / 04（见不可测项）。

## 不可测项

| AC / 项 | 原因 | 去向 |
|---|---|---|
| AC-014-06（1.1.0 改写） | 自动化部分已测（只用离线替身，外网请求 0）；**真实 DeepSeek 端点效果 / 真实 TLS·超时·代理 / 真实计费不可离线验证**（画像 P11-3：无官方沙箱；禁止调用真实端点） | 人工验证 MV-05、MV-14、MV-15 |
| AC-020-02 | N/A：设计选择“启动失败”形态，“提供方不可用”形态不存在；等价语义由 AC-014-04 / AC-018-05 用例覆盖 | 不计入分母；无人工项 |
| AC-019-01 | 真实 LLM 的意图 top-1 ≥ 0.90 需目标机 + 用户评测集 `[DATA_REQUIRED]` | MV-06 |
| AC-019-02 | 指代消解 ≥ 0.85、话题 F1 ≥ 0.85、误判 ≤ 0.02 需真实 LLM + 评测集 `[DATA_REQUIRED]` | MV-06 |
| AC-019-04 | 评测集来源确认属流程项，非离线可执行 | MV-07 |
| AC-005-03 的浏览器交互部分、AC-001-01 / 002-02 的“复选框默认不勾选的渲染” | 无组件挂载环境 / 无头浏览器（数据面与源码结构契约已测） | MV-01 ~ MV-04 |
| 真实 LLM 对注入指令的顺从度（AC-018-01 的“角色与语气不变”真实表现）、真实 TLS 钉 IP 连接、真实外网 DNS、目标机时延 | 不得联网 / 真实 LLM；平台侧强制手段已测 | MV-08 ~ MV-11 |
| 浏览器端到端旅程（US-006 全旅程）；联网事实不在保真守卫保护片段内（CR-007 / Q-2）的真实影响 | 无浏览器；需用户裁决 + 真实 LLM | MV-12、MV-13 |

> 以上不可测项不计入通过率分母，在 `e2e_test_report.md` 中单独计数为“待人工验证”（1.1.0：MV-01~MV-16，共 16 项）。
