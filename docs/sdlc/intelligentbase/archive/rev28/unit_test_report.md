<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-04T14:37:52+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（REV-28 顾问 agent）

> 修订记录：2.1.0（2026-11-04T14:37:52+08:00）——GROUP_D-005（DEF-003 裁决后重跑）：本层无用例改动，805 passed，计数与 1.2.0 一致；DEF-003 CLOSED（设计行为，CL-006 Q1=A）；1.2.0（2026-11-03T18:44:10+08:00）——GROUP_D-004（缺陷回流 2/2 复测）：本层无用例改动，按 §K 复跑；805 passed，计数与 1.1.0 一致；1.1.0（2026-11-03T18:27:49+08:00）——GROUP_D-003（REWORK_AUTHORIZED，CP-003 Q7 纳入 DeepSeek 搜索 / Q3=A 替身生产禁用 / Q4=A 固定中文致歉等）：新增 `tests/unit/test_deepseek_search_unit_r28.py`（35 个用例组 TC-UNIT-R28-200~234，82 项）；整层 unit 723→805；1.0.0 的 208 项用例与结论未改动；0.2.0（2026-11-02T23:35:17+08:00）——DEF-001 回流复测：TC-UNIT-R28-085 由缺陷冻结翻转为正向断言（移除 DEF-001-GUARD），新增正例 TC-UNIT-R28-088；整层 unit 722→723，全量 1231→1232；DEF-001 状态 FIXED/VERIFIED；0.1.0——初稿。

REV-27 APPROVED 版本已归档于 `archive/rev27/unit_test_report.md`（只读）。

## 摘要

### 2.1.0（GROUP_D-005，DEF-003 裁决后重跑；最后一次整层执行 2026-11-04T14:37:52+08:00 之后）

- 命令：`python -m pytest tests/unit -q -p no:cacheprovider`（离线，零真实网络）→ `805 passed in 9.31s`；`--collect-only | grep -cE '::'` = 805。
- 本轮**单元层无新写 / 改写用例**（改动仅在集成层 TC-INT-R28-418 / 425 / 426）。
- total = pass + fail + skip + blocked + not_testable = **805 = 805 + 0 + 0 + 0 + 0**；新写本轮 0 = 0 + 0 + 0 + 0 + 0。通过率 = 805/805 = **1.00**；相对前值（1.2.0：805 passed）新增失败 **0**。判定模式：INCREMENTAL / baseline。**本层门控：PASSED**。
- 前端层（独立计数）：`npm test` 160/160（前端无改动）。

### 1.2.0（GROUP_D-004，缺陷回流 2/2 复测；最后一次整层执行 2026-11-03T18:40:37~18:40:55+08:00）

- 环境、命令同 1.1.0：`python -m pytest tests/unit -q -p no:cacheprovider`（离线，零真实网络）。
- 本轮**单元层无新写 / 改写用例**（测试改动仅在集成层 TC-INT-R28-344 / 418 与 E2E 层新文件）。DEF-002/004/005/006 的产品修复（`orchestration/__init__.py`、`builder/egress.py`、`webtools/tools.py`、`webtools/fetch.py`）使单元层复跑结果不变。
- total = pass + fail + skip + blocked + not_testable = **805 = 805 + 0 + 0 + 0 + 0**（整层，含既有 515 + R28 全部 290：1.0.0 的 208 + 1.1.0 的 82）；新写本轮 0 = 0 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 805/805 = **1.00**；相对前值（PM 复跑 1.1.0 时点 805 passed）新增失败 **0**。判定模式：INCREMENTAL / baseline。**本层门控：PASSED**。
- 前端层（独立计数，不并入上式）：`npm test` 160/160（本轮前端无改动）。

### 1.1.0 增量（GROUP_D-003；最后一次整层执行 2026-11-03T18:23~18:26+08:00）

- 环境：`/root/.venvs/intelligentbase/bin/python`，仓库根，`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`，离线；本文件所有 DeepSeek 用例只经 `FakeDeepSeekTransport` / 打桩 opener，autouse 夹具把 `socket.connect` / `create_connection` / `getaddrinfo` 置为“一旦调用即失败”，**真实网络连接尝试数 = 0**（AC-014-06）。
- 命令：`python -m pytest tests/unit -q -p no:cacheprovider`。
- **本轮新写用例**（pytest 项）：total = pass + fail + skip + blocked + not_testable = **82 = 82 + 0 + 0 + 0 + 0**（`test_deepseek_search_unit_r28.py`：35 个用例组 TC-UNIT-R28-200~234）。
- 通过率 = pass/(pass+fail+blocked) = 82/82 = **1.00**。
- **整层**（含既有）：`tests/unit` **805 passed** = 前值 723（PM 复跑口径，GROUP_C-003 后；含 1.0.0 的 208 项 R28 用例）+ 本轮新写 82；fail 0。
- 判定模式：INCREMENTAL / baseline：相对前值新增失败 **0**，新写用例全部通过。**本层门控：PASSED**。
- 前端层（独立计数，不并入上式；本轮前端无改动，未新增用例）：`npm test` 160/160（沿用，本轮复跑 pass 160 / fail 0）。
- 说明：1.0.0 的 TC-UNIT-R28-075 / 091 / 092 已由 GROUP_C-003 随 2.1.0 设计调整过口径（max_results 钳制 1..50、`build_search_provider` 的 `offline` 关键字、search.py 无网络导入 / 无厂商端点），这三项在本轮整层执行中均 PASS；本人复核其断言强度未被放宽（092 仍守卫 search.py 无网络导入；DeepSeek 网络代码只在 `deepseek.py`）。

### 1.0.0 范围（保留，未改动；数字仅描述 1.0.0 时点）

- 执行时间：2026-11-02T23:31:32+08:00（最后一次整层执行；DEF-001 回流复测）；环境：`/root/.venvs/intelligentbase/bin/python`，仓库根，`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`，离线。
- 命令：`python -m pytest tests/unit -q -p no:cacheprovider`；前端层（独立计数）`(cd src/frontend && npm run build && npm test)`。
- **本层新写用例**（pytest 项）：total = pass + fail + skip + blocked + not_testable = **208 = 208 + 0 + 0 + 0 + 0**（netguard 84 + fetch/gate 41 + tools 31 + advisor core 52；共 102 个用例组 TC-UNIT-R28-*）。
- 通过率 = pass/(pass+fail+blocked) = 208/208 = **1.00**。
- **整层**（含基线）：`tests/unit` 723 passed = 基线 515（本人 `--collect-only --ignore-glob='*_r28.py'` 实测）+ 新写 208；fail 0。
- 前端层（独立计数，不并入上式）：`npm test` 160 pass = 基线 141 + 新写 19（TC-FE-R28-*，其中 unit 级 TC-FE-R28-001~007 / 010~012 共 10 个、结构契约 7 个、替代口径旅程 2 个）；`npm run build` rc=0（含 `vue-tsc --noEmit`）。
- 判定模式：INCREMENTAL / baseline：相对基线新增失败 **0**，新写用例全部通过。**本层门控：PASSED**。
- DEF-001（MINOR）**FIXED / VERIFIED**：GROUP_C-002 修复（`budget.charge_bytes` 无条件入账）。`TC-UNIT-R28-085` 已由“缺陷冻结 + 守卫串”翻转为正向断言（守卫串已移除），强度不低于原缺陷描述：(a) 超限失败的抓取字节已入账（bytes_used 第 1 次 6000 → 第 2 次后 ≥ 10000 > 第 1 次）；(b) 预算耗尽后同回合第 3 次 `tr.count == 2`（未出站）且 bytes_used 不再增长；(c) 第 3 次返回 `PHRASE_BUDGET`（“已达本轮联网上限”）并记录事件 `(web_fetch, budget_exceeded)`；(d) 实际下载总量（计数迭代器实测 12000）≤ max_fetch_bytes_per_turn(10000) + 单次已读上限(6000)，口径依 CR-014：超限读取全额计入，bytes_used 可略大于上限，语义为“耗尽即拒”。新增正例 `TC-UNIT-R28-088`（未超限抓取如实计数 2000/4000 并放行，2 次出站，事件均 ok）。

## 执行输出

### 1.2.0（最后一次执行）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/unit -q -p no:cacheprovider
805 passed in 8.16s
$ python -m pytest tests/unit --collect-only -q -p no:cacheprovider | grep -cE '::'
805
$ (cd src/frontend && npm test)
# tests 160 / # pass 160 / # fail 0 / # skipped 0
```

### 1.1.0（上一次执行，保留）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/unit -q -p no:cacheprovider
........................................................................ [ 98%]
.............                                                            [100%]
805 passed in 8.03s

$ python -m pytest tests/unit --collect-only -q -p no:cacheprovider | grep -cE '::'
805
$ python -m pytest tests/unit/test_deepseek_search_unit_r28.py --collect-only -q -p no:cacheprovider | grep -cE '::'
82

$ (cd src/frontend && npm test)
# tests 160  # suites 26  # pass 160  # fail 0  # cancelled 0  # skipped 0
```

### 1.0.0 时点输出（保留）

```
$ cd /root/myproject/intelligentbase && python -m pytest tests/unit -q -p no:cacheprovider
........................................................................ [ 80%]
........................................................................ [ 91%]
................................................................         [100%]
723 passed in 8.22s

$ python -m pytest tests/unit --collect-only -q -p no:cacheprovider --ignore-glob='*_r28.py' | grep -cE '::'
515
$ python -m pytest tests/unit --collect-only -q -p no:cacheprovider | grep -cE '::'
723

$ (cd src/frontend && npm run build && npm test)
✓ built in 33.85s            # build_rc=0
# tests 160  # suites 26  # pass 160  # fail 0  # cancelled 0  # skipped 0
```

## 分项结果

全部 **PASS**（根因分类栏仅在 FAIL 时填写，此处无）。“项数”= pytest 参数化项数。

### 边界 MOD-R28-03：DeepSeek 搜索适配器 / 替身 / 提供方工厂 / Key 解析（`tests/unit/test_deepseek_search_unit_r28.py`，82 项，1.1.0 新增）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-UNIT-R28-200 | AC-018-06 / AC-014-06 / AC-014-07 | 请求契约（happy path）：POST 资料所载端点；头恰为 Authorization Bearer + Content-Type JSON；体键集恰为 {query,count,need_content}，need_content=false；200 非空计费 +1 | 1 | PASS |
| TC-UNIT-R28-201 | AC-018-06 / AQ6=A | 体不含 localization / ori_question，也不含 region 值；有无 region 请求一致（region 被忽略） | 1 | PASS |
| TC-UNIT-R28-202 | AC-014-09 | query 1/63/127/128 字符（CJK 以字符计）原样发送；SearchQuery 拒绝 129 字符与空串 | 4 | PASS |
| TC-UNIT-R28-203 | AC-014-09 | 合法 lang ⇒ 末尾追加 ` lang:zh,en` 且总长 ≤128；非法 lang（注入 site:）忽略且日志不含该值 | 1 | PASS |
| TC-UNIT-R28-204 | AC-014-09 | count 1/5/50 作为整数原样发送；0/51/-1/True 被 SearchQuery 拒绝 | 3 | PASS |
| TC-UNIT-R28-205 | AC-014-09 | 全空白检索词（空格 / 制表换行 / 全角空格）⇒ rejected、请求数 0；非空词成对出站 | 1 | PASS |
| TC-UNIT-R28-206 | AC-014-07 | 每条命中含非空标题 / 网址 / 摘要（summary 优先，缺则 snippet）；顺序保持；未知字段忽略；超 limit 截断 | 1 | PASS |
| TC-UNIT-R28-207 | AC-014-10 | 200 + 空数组 ⇒ error=None、hits=()、不计费；成对非空正例计费 +1 | 1 | PASS |
| TC-UNIT-R28-208 | NFUNC-011 | 10 种非常形态（非 JSON / 顶层数组 / 缺 results / 非法或非 http(s) 网址 / 204 / 302）⇒ bad_response，永不抛 | 10 | PASS |
| TC-UNIT-R28-209 | NFUNC-011 | 响应体超上限 ⇒ bad_response；上限内正常响应成对通过 | 1 | PASS |
| TC-UNIT-R28-210 | AC-014-08 | 资料 §错误 列出的 10 个状态码逐一映射到设计类别（400/413/403/404⇒rejected、401⇒auth_failed、402⇒quota_exceeded、408/504⇒timeout、429⇒rate_limited、500⇒unreachable）；单次尝试；结果中无状态码 / 错误体 message·type·code / Key | 10 | PASS |
| TC-UNIT-R28-211 | AC-014-08 / AC-018-05 | 错误体换成任意文本（像 Key 的串 / HTML / 空）映射与输出完全不变，不读取错误体 | 6 | PASS |
| TC-UNIT-R28-212 | AC-014-08 | 资料未列的 409/422 ⇒ rejected、502/503 ⇒ unreachable（设计兜底） | 1 | PASS |
| TC-UNIT-R28-213 | AC-014-08 | 超时 / 不可达 / 延迟 > 超时 ⇒ timeout·unreachable·timeout；意外异常 ⇒ bad_response 且异常内容（含 Key）不外泄 | 1 | PASS |
| TC-UNIT-R28-214 | AC-016-09（AQ8=A） | 不重试：429、500、成功三次 search 恰 3 次请求 | 1 | PASS |
| TC-UNIT-R28-215 | NFUNC-007 | query.timeout_s 原样传给传输缝（2.5 / 7.0） | 1 | PASS |
| TC-UNIT-R28-216 | AC-018-05 / CR-016 | 哨兵 Key 只出现在传输缝收到的 Authorization 头；repr / str / health / 外发声明 / 12 种结果 / 日志 / 构造异常消息中 0 次 | 1 | PASS |
| TC-UNIT-R28-217 | AC-018-03 | health() 不外呼；外发声明 remote=True、主机 api.deepseek.com、类别仅 web_search_query | 1 | PASS |
| TC-UNIT-R28-218 | AC-014-06（替身可信度） | 替身按资料校验：Key 不符 ⇒ 401；缺 Content-Type / count=51 ⇒ 400；只构造资料列出的错误码 | 1 | PASS |
| TC-UNIT-R28-219 | AC-014-05 / 014-07 | Fake 与 DeepSeek 适配器返回同一组 3 条 ⇒ 工具输出逐字相同 | 1 | PASS |
| TC-UNIT-R28-220 | AC-014-09 | 工具层：200 字符检索词截为前 128；max_results 100⇒50、0⇒1；全空白⇒“检索词为空”且请求数不增 | 1 | PASS |
| TC-UNIT-R28-221 | AC-014-08 | 工具层：10 个错误状态各得固定短语（408/504 超时，其余检索失败），无状态码 / 错误原文 / Key；审计仍写一条 | 10 | PASS |
| TC-UNIT-R28-222 | AC-016-09 | 每轮上限 5 次、连续 8 次 ⇒ 请求 5 次、第 6~8 次“已达本轮联网上限”；全 429 同样 5 次 | 1 | PASS |
| TC-UNIT-R28-223 | AC-014-06 / AC-018-05 | UrllibPostTransport（打桩 opener，不触网）：POST、端点、Bearer + JSON 头、超时、响应拼接 | 1 | PASS |
| TC-UNIT-R28-224 | AC-014-08 | HTTPError 11 个状态码（含 302）只取状态码、错误体 fp 未被读取 | 11 | PASS |
| TC-UNIT-R28-225 | AC-014-08 | TimeoutError / URLError(TimeoutError)⇒timeout；URLError·ConnectionReset·SSLError·RemoteDisconnected⇒unreachable；http:// ⇒ unreachable 且不调用 opener | 1 | PASS |
| TC-UNIT-R28-226 | A-14 / A-18 | 响应超限 ⇒ oversize 并丢弃；opener 不含 HTTPRedirectHandler（不转发 Authorization） | 1 | PASS |
| TC-UNIT-R28-227 | AC-020-01 / 020-03 | 非离线 + fake ⇒ ConfigError(key=IB_WEB_SEARCH_PROVIDER)，消息不含 “fake” 与 Key；FakeSearchProvider 构造 0 次；离线 + fake 正例 | 1 | PASS |
| TC-UNIT-R28-228 | AC-020-03 / AC-018-05 | 工厂矩阵：none⇒Null（与上一轮一致）；deepseek+离线⇒Fake 且不构造真实传输；deepseek+在线+Key⇒适配器（Key 裁剪）；无 Key（None/空/空白）⇒Null+WARNING 无 Key；未登记⇒ConfigError；内置标识不可登记 | 1 | PASS |
| TC-UNIT-R28-229 | AC-020-01 / 020-03 | 校验：非离线 fake ⇒ 仅键名、值 0 次；任意非法取值同；离线 fake / none / deepseek+DeepSeek 主机通过 | 1 | PASS |
| TC-UNIT-R28-230 | AC-018-05 | deepseek + 非 DeepSeek LLM 主机（子域·前缀·userinfo 伪装·空·非法 URL 共 7 种）⇒ 仅报键名、不含主机；正确主机（大小写 / 端口）通过 | 1 | PASS |
| TC-UNIT-R28-231 | AC-018-05 | resolve_llm_api_key：台账优先、环境回退、皆空 ⇒ None、裁剪空白 | 1 | PASS |
| TC-UNIT-R28-232 | AC-018-05 | build_web_runtime（非离线）：台账 Key / 环境回退进 Authorization 头；删除 Key ⇒ Null + “联网服务未配置”；离线 ⇒ Fake 且不构造真实传输 | 1 | PASS |
| TC-UNIT-R28-233 | NFUNC-005 / 006 | 源码纪律：适配器无 ori_question / localization 字面量；Bearer 只在 deepseek.py；端点 / 128 / 50 常量等于资料；替身无网络导入 | 1 | PASS |
| TC-UNIT-R28-234 | AC-001-04 | 致歉文本为单一固定中文常量：含中文，英文字母 0、数字 0、内部名 0 | 1 | PASS |

项数合计 = 1 + 1 + 4 + 1 + 3 + 1 + 1 + 1 + 10 + 1 + 10 + 6 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 10 + 1 + 1 + 11 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 = 82。

### 边界 MOD-R28-02：地址防护 / 域名名单 / 策略（`tests/unit/test_webtools_netguard_unit_r28.py`，84 项）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-UNIT-R28-001 | AC-015-02 / REQ-NFUNC-004 | SSRF 拒绝集：56 条每条被拒（环回 / 10/8 / 172.16/12 / 192.168/16 / 169.254.169.254 / 100.64/10 / 0.0.0.0 / 组播 / 保留 / IPv6 环回·ULA·链路本地·组播 / IPv4-mapped / NAT64 / AWS-IPv6 元数据 / 十进制·十六进制写法 / DNS→私有·元数据·回环·CGNAT·多记录含私有（rebinding）·IPv6 ULA·mapped / file·ftp·gopher·javascript·data / userinfo / 非标端口 / zone id / CRLF / 空白 / 空串 / DNS 失败） | 56 | PASS |
| TC-UNIT-R28-002 | REQ-NFUNC-004 | 口径守卫：拒绝集 ≥30 且覆盖 DNS 私有 / IPv6 / mapped / 169.254.169.254 / 100.64 | 1 | PASS |
| TC-UNIT-R28-003 | AC-015-02 | 拒绝原因仅短码，不回显解析结果与内网拓扑 | 1 | PASS |
| TC-UNIT-R28-004 | AC-015-03 | file:// ftp:// ⇒ scheme_not_allowed | 1 | PASS |
| TC-UNIT-R28-005 | AC-015-02（正例） | 公网目标放行，钉住已校验 IP、保留原主机名（与 001 成对） | 7 | PASS |
| TC-UNIT-R28-006 | AC-015-02 | 18 个拒绝网段 ∩ is_global 代表地址判定 | 1 | PASS |
| TC-UNIT-R28-007 | AC-016-06 | 期限已过 ⇒ resolve_failed（fail-closed） | 1 | PASS |
| TC-UNIT-R28-008 | AC-015-02 | **真实默认解析器**（getaddrinfo + 线程池）：localhost 各写法 / 十进制·十六进制·八进制·省略段数字写法 / [::1] 全部被拒（无外网 DNS） | 10 | PASS |
| TC-UNIT-R28-010 | AC-016-01 | 白名单放行本域与子域，其它域被拒 | 1 | PASS |
| TC-UNIT-R28-011 | AC-016-02 | 黑名单优先（含子域继承） | 1 | PASS |
| TC-UNIT-R28-012 | AC-016-04 | 域名清单解析：非法项指出第几项，合法项小写去重 | 1 | PASS |
| TC-UNIT-R28-020 | AC-016-07 / 016-03 | 有效上限 = min(工具参数, 全局, 硬上限) | 1 | PASS |
| TC-UNIT-R28-021 | AC-016-07 | 3 次 / 500KB 通过；8 次被拒“超出全局上限（5 次）” | 1 | PASS |
| TC-UNIT-R28-022 | AC-016-04 | 保存期域名清单非法项逐条错误 | 1 | PASS |

### 边界 MOD-R28-02 / 04：安全抓取 / 出站闸 / 预算 / 净化（`…test_webtools_fetch_gate_unit_r28.py`，41 项）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-UNIT-R28-030 | AC-015-01 | HTML 抓取：标题 + 最终网址 + 正文 ≤ 上限，剔除 script/style/nav | 1 | PASS |
| TC-UNIT-R28-031 | REQ-NFUNC-004 | 请求头：无 Cookie / Authorization / Referer；Accept-Encoding: identity | 1 | PASS |
| TC-UNIT-R28-032 | AC-015-02 | 首跳公网、重定向到内网·元数据·localhost·DNS 私有·mapped·CGNAT·file·非标端口 ⇒ 被拒；出站仅首跳 1 次 | 9 | PASS |
| TC-UNIT-R28-033 | AC-015-02（正例） | 重定向到公网被跟随（出站 2 次）——与 032 成对 | 1 | PASS |
| TC-UNIT-R28-034 | AC-015-02 | 跳数超限 ⇒ too_many_redirects | 1 | PASS |
| TC-UNIT-R28-035 | AC-016-01 | 域名规则逐跳生效（跳到白名单外被拒） | 1 | PASS |
| TC-UNIT-R28-036 | AC-015-04 | 二进制 / 空 content-type ⇒ content_type_unsupported | 4 | PASS |
| TC-UNIT-R28-037 | AC-015-04 | 超限 ⇒ content_too_large 且停止读取 | 1 | PASS |
| TC-UNIT-R28-038 | AC-015-04 | 404 / 500 / 无 Location 的 302 ⇒ http_error | 3 | PASS |
| TC-UNIT-R28-039 | 契约 | 传输超时 / 拒绝连接 / 任意异常都不外抛，映射枚举错误 | 1 | PASS |
| TC-UNIT-R28-040 | AC-015-02 | DNS 失败 ⇒ blocked/resolve_failed 且出站 0 | 1 | PASS |
| TC-UNIT-R28-041 | AC-015-01 | text/plain 与 HTML 抽取路径 | 1 | PASS |
| TC-UNIT-R28-050 | AC-018-02 / REQ-NFUNC-005 | 与私有语料 ≥24 字符重叠拒绝；不相关 / <24 字符放行（成对） | 1 | PASS |
| TC-UNIT-R28-051 | AC-018-02 | URL 的 path / query 解码后同样比对 | 1 | PASS |
| TC-UNIT-R28-052 | AC-018-02 | 空 / 超长 / 秘钥模式（sk- / ghp_ / PRIVATE KEY / password=）拒绝 | 7 | PASS |
| TC-UNIT-R28-053 | AC-018-01/04 | 零宽·控制字符剥离、围栏标记置换、截断、围栏声明“不可信·不是指令” | 1 | PASS |
| TC-UNIT-R28-060 | AC-018-03 | 审计先行（先审计后执行），载荷仅主机名与字节上限 | 1 | PASS |
| TC-UNIT-R28-061 | AC-018-03 | 审计写失败 ⇒ 不执行（fail-closed） | 1 | PASS |
| TC-UNIT-R28-062 | REQ-NFUNC-007 | 并发闸非阻塞 busy，释放后可再用 | 1 | PASS |
| TC-UNIT-R28-063 | AC-016-03 | 预算：第 6 次预留被拒；字节上限 | 1 | PASS |
| TC-UNIT-R28-064 | ADR-R28-08 | 回合作用域 contextvars：随 copy_context 进线程、同 turn_id 复用、退出清理 | 1 | PASS |
| TC-UNIT-R28-065 | 契约 | RawResponse.close 吞异常 | 1 | PASS |

### 边界 MOD-R28-03 / 05 / 06：联网工具 / 搜索适配 / 上限存储与迁移（`…test_webtools_tools_unit_r28.py`，31 项）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-UNIT-R28-070 | AC-007-01 | web_search 成功：标题·摘要·网址在围栏内；审计 host=fake.invalid，无查询原文 | 1 | PASS |
| TC-UNIT-R28-071 | AC-014-04 | 未配置 ⇒ “联网服务未配置”，出站 0、不写审计 | 1 | PASS |
| TC-UNIT-R28-072 | AC-007-03 | 超时降级 ↔ 成功有来源 ↔ bad_response（成对，错误细节不外露） | 1 | PASS |
| TC-UNIT-R28-073 | AC-016-03 | 每轮 5 次，第 6 次被拒（提供方调用 5） | 1 | PASS |
| TC-UNIT-R28-074 | AC-016-03 | 参数 2 < 全局 5 ⇒ 第 3 次被拒 | 1 | PASS |
| TC-UNIT-R28-075 | AC-014-03 | max_results 钳制到 [1,10] | 1 | PASS |
| TC-UNIT-R28-076 | AC-018-02 | 查询含私有片段 ⇒ “请求内容不被允许”，提供方调用 0；正常查询放行 | 1 | PASS |
| TC-UNIT-R28-077 | 契约 | 提供方抛异常 / 缺回合上下文 / 空实参 ⇒ 永不抛，固定短语 | 1 | PASS |
| TC-UNIT-R28-078 | AC-018-01 | 结果净化：零宽·控制字符剥离，伪造围栏结束标记被置换 | 1 | PASS |
| TC-UNIT-R28-080 | AC-015-05/06、016-08 | **总开关关闭**：出站 0、如实告知、不写审计、不占预算 | 1 | PASS |
| TC-UNIT-R28-081 | AC-015-01/06（正例） | 开关打开 ⇒ 返回标题·网址·正文，计入字节预算（与 080 成对） | 1 | PASS |
| TC-UNIT-R28-082 | AC-015-02/03 | 经工具入口：127.0.0.1 / 10.0.0.5 / 169.254.169.254 / file / ftp 被拒，出站 0 | 5 | PASS |
| TC-UNIT-R28-083 | AC-016-01/02 | 工具参数白 / 黑名单 | 1 | PASS |
| TC-UNIT-R28-084 | AC-015-04 | 二进制 ⇒ “内容类型不支持”；超限 ⇒ “内容超限” | 1 | PASS |
| TC-UNIT-R28-085 | AC-016-07 / **DEF-001** | 回合抓取字节总量预算（**已由冻结翻转为正向**）：超限失败的抓取入账、耗尽后第 3 次不出站（count==2）、固定短语 + 事件、总下载量 ≤ 上限 + 单次已读上限（CR-014 口径） | 1 | PASS |
| TC-UNIT-R28-088 | AC-016-07（正例） | 未超限的正常抓取如实计数（2000 / 4000）并放行，2 次出站 | 1 | PASS |
| TC-UNIT-R28-086 | AC-018-02 | 抓取 URL 含私有片段 ⇒ 拒绝，出站 0 | 1 | PASS |
| TC-UNIT-R28-087 | ADR-R28-06 | 工具规格：LLM 只可见 query / url；限制类参数为 config_parameters；external=True | 1 | PASS |
| TC-UNIT-R28-090 | AC-014-05 | 两个提供方替身（原始格式不同）⇒ 工具输出结构一致（标题·摘要·网址） | 1 | PASS |
| TC-UNIT-R28-091 | AC-014-04/06 | build_search_provider：none / fake / 未登记 ConfigError 不含密钥 / 重复登记 / 缺 https·密钥降级 Null | 1 | PASS |
| TC-UNIT-R28-092 | AC-014-06 | 守卫：search.py 无网络导入、无厂商端点 | 1 | PASS |
| TC-UNIT-R28-093 | 契约 | FakeSearchProvider 永不抛；error 时丢弃 hits | 1 | PASS |
| TC-UNIT-R28-100 | AC-016-07 | 上限存储（内存）：默认值 / 范围校验 / 拒 bool·非整数·越界 / 失败不改已存值 | 1 | PASS |
| TC-UNIT-R28-101 | AC-016-07 | 上限存储（SQLite）：往返、CHECK(id=1) | 1 | PASS |
| TC-UNIT-R28-102 | P6 | 迁移 009：与 schema.py 生成器单源、幂等两遍快照一致、回滚说明 MANUAL_ROLLBACK_REQUIRED、无可执行 DROP | 1 | PASS |
| TC-UNIT-R28-103 | A-2 | ledger_backend=memory 用内存替身（不落盘）；老库 ensure_schema 两遍补齐 | 1 | PASS |
| TC-UNIT-R28-104 | REQ-NFUNC-007 | 回合累计耗时用尽 ⇒ 后续联网被拒，出站 0 | 1 | PASS |

### 边界 MOD-R28-07 / 08 / 09 / 10 / 11 / 13：顾问核心 / 配置域 / Builder / 工具 / 看门狗 / 日志（`…test_advisor_core_unit_r28.py`，52 项）

| TC | AC | 描述 | 项数 | 结果 |
|---|---|---|---|---|
| TC-UNIT-R28-110 | AC-008-01、CR-008（正例） | 理解成功且未降级：source=llm，字段按枚举 / 长度约束解析 | 1 | PASS |
| TC-UNIT-R28-111 | CR-008（降级） | 输出不合规（空 / 非 JSON / 数组 / 缺键 / 非法枚举 / 非 bool / 围栏）10 种 ⇒ fail-open 透传，路由照常（与 110 成对） | 10 | PASS |
| TC-UNIT-R28-112 | CR-008 | LLM 抛异常 ⇒ 永不抛，透传 | 1 | PASS |
| TC-UNIT-R28-113 | AC-008-04 | 空白 / 纯符号 5 种 ⇒ 澄清且不调用 LLM | 5 | PASS |
| TC-UNIT-R28-114 | AC-008-01 | route_skip 语义（寒暄·通用·拒答旁路；知识·委托·unknown 不旁路） | 1 | PASS |
| TC-UNIT-R28-115 | AC-018-01 | 理解提示词把历史与问句当数据；历史块受预算约束 | 1 | PASS |
| TC-UNIT-R28-116 | AC-012-02/04 | 澄清话术与字段长度上限 | 1 | PASS |
| TC-UNIT-R28-117 | AC-013-01~04 | 话题关系四种取值 | 1 | PASS |
| TC-UNIT-R28-120 | AC-011-05 | ≤20 条且未超预算 ⇒ 原样，裁剪 0 | 1 | PASS |
| TC-UNIT-R28-121 | AC-011-05 | 窗口 20：窗口外消息不出现 | 1 | PASS |
| TC-UNIT-R28-122 | AC-011-05 | 超预算最旧优先整条丢弃、总长 ≤ 预算、最近一条保留、保留的是连续最新 | 1 | PASS |
| TC-UNIT-R28-123 | AC-011-05 | 最近一条单条超预算 ⇒ 截断保留不丢 | 1 | PASS |
| TC-UNIT-R28-124 | AC-011-05 | 空历史、默认预算常量 8000 | 1 | PASS |
| TC-UNIT-R28-130 | AC-006-06 | 保护片段抽取：数字·书名号·第N条·网址，去重 | 1 | PASS |
| TC-UNIT-R28-131 | AC-006-06 / 010-03 | 措辞格式变化但事实保留 ⇒ 缺失 0（全半角 / 空白归一） | 1 | PASS |
| TC-UNIT-R28-132 | AC-006-06 / 010-03 | 数字被改 / 引用丢 / 网址丢 ⇒ 逐项缺失 | 1 | PASS |
| TC-UNIT-R28-133 | AC-006-06 | 千分位归一 | 1 | PASS |
| TC-UNIT-R28-134 | AC-010-07 | 重试提示要求“必须原样保留”缺失片段 | 1 | PASS |
| TC-UNIT-R28-135 | AC-018-04 | 引用长度：≥200 字符逐字重叠超限；190 不超；概括不超 | 1 | PASS |
| TC-UNIT-R28-140 | AC-006-07 / 010-06 | 致歉文案：含“抱歉”+ 下一步建议；不含 agent·工具·路由名·异常字样·状态码·阿拉伯数字 | 1 | PASS |
| TC-UNIT-R28-141 | AC-005-01 | 顾问输入块渲染与省略规则 | 1 | PASS |
| TC-UNIT-R28-142 | 检查点安全 | AdvisorTurn 状态往返、全原语 | 1 | PASS |
| TC-UNIT-R28-150 | REQ-NFUNC-008 | 指标手算值一致（top-1·混淆矩阵·话题 F1=2/3·消解·误判率） | 1 | PASS |
| TC-UNIT-R28-151 | AC-019-03 | 评测 `evaluate()` 以替身：统计与判定（阈值 0.90/0.85/0.85/0.02），未达标分支 | 1 | PASS |
| TC-UNIT-R28-152 | AC-019-03/04 | 评测集读取（坏行报错）；脚本不内置合成集 | 1 | PASS |
| TC-UNIT-R28-160 | AQ5=A | 顾问判据 = 保留名 ∧ is_delegating ∧ active | 1 | PASS |
| TC-UNIT-R28-161 | AC-002-01 | 规范图形状且通过校验 | 1 | PASS |
| TC-UNIT-R28-162 | AC-009-03 | advisor_self_delegation / advisor_branch_target_invalid；非顾问项目不触发 | 1 | PASS |
| TC-UNIT-R28-163 | AC-005-04 / 009-03 | 回边成环 ⇒ graph_cycle；无顾问项目同类环结果一致 | 1 | PASS |
| TC-UNIT-R28-164 | AC-005-02 | 顾问不可达 ⇒ graph_unreachable_from_start（无特例） | 1 | PASS |
| TC-UNIT-R28-165 | AC-001-02 | 种子声明与 BLOCKED_TERMS 0 命中 | 1 | PASS |
| TC-UNIT-R28-166 | AC-001-01/03 | 内置顾问规格；不在默认注册表 | 1 | PASS |
| TC-UNIT-R28-170 | AC-004-02 | 顾问口径“工具与委托契约”通过（无 search_knowledge 字样） | 1 | PASS |
| TC-UNIT-R28-171 | AC-004-02 | 同文本 kb-agent 口径与基线一致；顾问三项无条件适用 | 1 | PASS |
| TC-UNIT-R28-172 | AC-004-03 | 禁用词判未通过且不泄露 | 1 | PASS |
| TC-UNIT-R28-180 | AC-014-03 | “配置胜出”：LLM 传 99 被丢弃；timeout_s = 配置 + 1.0 | 1 | PASS |
| TC-UNIT-R28-181 | AC-014-02 | route_visible=False 的联网工具不进路由能力摘要 | 1 | PASS |
| TC-UNIT-R28-182 | AC-016-06 | 看门狗：超时终止 + 上报 timeout；None 路径不变；contextvars 随任务；异常占位 | 1 | PASS |
| TC-UNIT-R28-183 | REQ-NFUNC-010 | 日志白名单含顾问回合键；未登记字段不入日志 | 1 | PASS |

### 前端层（独立计数，19 项，全部 PASS）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-FE-R28-001~007 | AC-003-01/02、AC-005-01 | advisorPlan 真实执行：判据、规范形态自动接线、纯函数性与幂等、非规范形态 wired=false、加入→移除往返恢复、边界、多 agent | PASS ×7 |
| TC-FE-R28-010~012 | AC-002-01/02、AC-016-07 | client 真实实例化：createProject 缺省 / false / 非 true 值 ⇒ 请求体与升级前逐字相同；仅 true 带 enable_advisor；Web 上限接口路径·方法·体·头 | PASS ×3 |
| TC-FE-R28-020~026 | AC-002-02、AC-003-03、AC-005-03、AC-016-07 | 源码结构契约（integration 级）：复选框默认不勾选；加入 / 移除按钮仅编辑档且不发请求；面板；路由 / 导航；页面只经 client、无外链；类型导出 | PASS ×7 |
| TC-FE-R28-E01~E02 | AC-002-01、AC-016-07 | 旅程（替代口径） | PASS ×2 |

## 与基线对比

| 项 | 基线（PM 实跑 HEAD 8d6fd4b） | 本次（最后一次执行） | 新增失败 |
|---|---|---|---|
| `tests/unit` 整层 | 515 passed（`--ignore-glob='*_r28.py'` 实测） | 723 passed | **0** |
| 前端 `npm test` | 141/141 | 160/160 | **0** |
| `tests/unit` 整层（1.1.0） | 723 passed（PM 复跑，GROUP_C-003 后） | 805 passed（= 723 + 82） | **0** |
| 既有失败 | pytest 无；selfcheck `core_framework_free`（sitecustomize，环境性）——本层不涉及 | 同 | 不算新增 |

## 失败汇总（需路由给开发）

本层无失败。DEF-001 已修复并复测通过（FIXED / VERIFIED），无遗留缺陷：

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-UNIT-R28-085（原冻结，已翻转） | 原现象：超限失败的抓取不计入回合预算。现：已入账、耗尽后拒绝 | `src/ib/webtools/tools.py:300`（`budget.charge_bytes`） | DEF-001（MINOR）FIXED / VERIFIED |

1.1.0：本层无失败（805 passed，fail 0）。
