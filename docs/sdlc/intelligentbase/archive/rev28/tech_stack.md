<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-03T17:48:02+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/external_api/deepseek_search_fetch.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（REV-28 增量）— 平台级内置「顾问 agent」

## 修订记录

| 版本 | 时间 | 说明 |
|---|---|---|
| 1.0.0 | 2026-11-02T21:28:55+08:00 | 初版（APPROVED） |
| 2.1.0 | 2026-11-03T17:48:02+08:00 | 定向修订（invocation intelligentbase-R28-GROUP_B-003，REWORK_AUTHORIZED；落点 CP-003「Q7 纳入」，依据画像 1.1.0 P11-3 与 `docs/external_api/deepseek_search_fetch.md`）：(1) 搜索提供方由"端口 + Null / Fake，厂商未知"改为 **DeepSeek 官方 Search API**（外部服务，非新增依赖；stdlib `urllib` 适配器，**无新增 HTTP 库**）；(2) 密钥管理由"新增键 `IB_WEB_SEARCH_API_KEY`"改为"**复用现有 DeepSeek Key（台账 `llm_key` / 兼容 `IB_LLM_API_KEY`），不新增任何凭据键**"，并删除 `IB_WEB_SEARCH_BASE_URL`；(3) 网页抓取方案论证（architecture_design ADR-R28-12）：**保留本地 `SafeFetcher`，`lxml` 保留显式声明**，`requirements*.txt` 无改动；(4) 测试行增 DeepSeek 离线替身；(5) 风险表按 DeepSeek 接入更新（R-5 降级，新增 R-11~R-13）。**新增依赖汇总仍只有 `lxml>=5.0,<7.0`（2.0.0 已声明）** |
| 1.1.0 | 2026-11-02T21:50:53+08:00 | 最小订正（M-SA-017）：用户裁决 CP-002 使两处既有表述失真——风险 R-8 的"失败回退被委托 agent 原答（AQ1）"改为"统一致歉"（AQ1=B）；"全局工具目录新增两个工具名"的"AQ3 待用户确认"改为已裁决（AQ3=A）；搜索提供方行补注 Q7=C（本轮无厂商适配器、无网络代码）。**选型表、新增依赖（仅 `lxml`）、许可证登记均无变化** |

**结论**：本轮**新增依赖声明仍仅一项：`lxml`**（已是 `python-docx` 的间接依赖，现改为显式声明并加上下界 / 上界）；**无新增运行单元、无容器、无新 Python 框架、无新前端依赖**。完整技术栈基线见 REV-26 `archive/rev26/tech_stack.md`、REV-27 `archive/rev27/tech_stack.md` 与画像 P1。
**P11 说明（2.1.0 改写）**：画像 1.1.0 P11-3 登记了 DeepSeek Search / Fetch API，资料 `docs/external_api/deepseek_search_fetch.md`（主会话据官方页面整理，摘录 2026-11-02，PM 未核对原页面）。DeepSeek 是**外部服务而非软件包**：无版本号可登记（资料未给 API 版本，写"未知"）；端点、鉴权、限流、计费以资料为准并标 `[P11: docs/external_api/deepseek_search_fetch.md:§节名]`；**不联网查证**（§N-3）。

## 技术选型表

| 类别 | 选型 | 版本（出处；查不到写"未知"） | 新增 / 沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | `>=3.11,<3.14`；CI 用 3.12（画像 P1；`.github/workflows/ci.yml:58`） | 沿用 | 无变化；`ipaddress.is_global` 在 3.11~3.13 间有边界修订（[WEB: https://docs.python.org/3/library/ipaddress.html，2026-11-02]），故 SSRF 拒绝网段由项目显式列出，不单靠该属性 | REQ-NFUNC-004 | 低 |
| Web 框架 | Django + DRF + waitress（`--threads=8`） | `Django>=5.0,<6.1`（`src/requirements.txt:14`）；`waitress>=3.0,<4.0`（`:16`）；threads（`src/deploy/systemd/ib-web.service:52`） | 沿用 | 新端点 `/api/web-governance` 沿用现有手写视图风格与 `_require_admin`；联网调用占用请求线程，用并发闸限制 | REQ-FUNC-018 | 中：见技术风险 R-1 |
| 编排 | LangGraph + langchain-core | `langgraph>=0.2,<2.0`（`:23`）；`langchain-core>=0.3,<2.0`（`:24`） | 沿用 | 顾问是普通 agent 节点，沿用 ADR-57 层归一化与中继节点；不依赖 `defer` 等未核实特性 | REQ-FUNC-006/011 | 低：引擎改动经真实 langgraph 契约测试（`tests/integration/test_advisor_dag_rev28.py`） |
| LLM 客户端 | langchain-openai（DeepSeek） | `langchain-openai>=0.2,<0.3`（`:25`；画像 P8：`>=0.3` 禁用） | 沿用 | 工具循环继续用 `bind_tools` / `tool_calls`（`src/ib/llm/__init__.py:530-567`）；理解步骤用路由角色（温度 0） | REQ-FUNC-010/014 | 低 |
| 数据存储 | SQLite WAL 台账 | 画像 P1 | 沿用 + **新增单行表** `web_governance` | 全局用量上限需可被 admin 写入并审计，沿用 LLM Key 单行表先例（ADR-R28-07）；迁移 `009_web_governance.sql` 与 `schema.py` 单源 | REQ-FUNC-018 (d) | 低：可逆（DROP，标 `[MANUAL_ROLLBACK_REQUIRED]`） |
| 会话 / 预算存储 | 进程内（`MemorySessionStore`；`TurnBudget` 进程内） | 会话 2000 个 / 24h（`src/ib/streaming/__init__.py:207-225`） | 沿用 | OQ-R28-06=A；P8 禁 Redis 用于实时推送，且无外部会话存储的新故障面 | REQ-NFUNC-009 | 低：重启丢失会话（已知现状） |
| 向量库 / Embedding | Qdrant、bge-m3（ib-embed） | 画像 P1 | 沿用，**不改** | 顾问经路由委托 kb-agent 复用既有检索；不新增检索路径 | REQ-NFUNC-002 | 无 |
| HTTP 出站客户端 | Python 标准库 `urllib` / `http.client` / `ssl` / `socket` | 随 Python（无独立版本） | 沿用风格 | 与 `src/ib/embedding/__init__.py:259-312` 一致。**抓取**需自控连接层（钉已校验 IP + 逐跳重校验），现成第三方库均不提供；**搜索**（2.1.0）为向固定主机的单次 HTTPS POST，同样用 `urllib`，不为一两个 REST 调用引入 `requests` / `httpx`（用户指令：不引入新 HTTP 依赖）；网络导入仅限 `fetch.py` 与 `deepseek.py`，由 selfcheck 守住 | REQ-NFUNC-004、C-R28-09、D-07 | 中：抓取连接层为自写薄封装，需充分单测（≥30 条拒绝用例）；搜索适配器需自写状态码映射与读取上限，由离线替身覆盖 |
| 网页正文抽取 | `lxml`（`lxml.html`） | **声明 `lxml>=5.0,<7.0`**（下界 `[ASSUMPTION]` 保守值；当前稳定版 6.1.3、BSD-3-Clause：[WEB: https://pypi.org/pypi/lxml/json，2026-11-02]）；现状为 python-docx 1.2.0 的间接依赖 `lxml>=3.1.0`（[WEB: https://pypi.org/pypi/python-docx/json，2026-11-02]）。**2.1.0 去留论证**：架构 ADR-R28-12 选**保留本地抓取**，`SafeFetcher` 仍用 `lxml.html` 抽取正文，故**保留显式声明，`requirements.txt` / `requirements-offline.txt` 不改**；若将来改用 DeepSeek Fetch（响应已是 Markdown），可删除 `extract_text` 与显式行，但 `python-docx` 仍间接需要 `lxml`，**不得从 venv 卸载**，且 `requirements-offline.txt` 的 python-docx 行不动 | **新增（显式声明既有间接依赖，2.0.0 起；本次无变化）** | 用户"尽量复用"：库已在生产 venv，无新增体积 / 许可证；容错 HTML 解析 + xpath 比自写 `html.parser` 更省代码；显式声明避免 python-docx 将来换实现导致 `web_fetch` 静默失效 | REQ-FUNC-017、C-R28-09 | 中：C 扩展解析不可信 HTML；缓解 = 解析前按 `max_bytes` 截断、限制 `max_chars`、惰性 import（缺失时 `extract_unavailable` 降级）、不用已拆出的 `lxml.html.clean` |
| 搜索提供方 | **DeepSeek 官方 Search API**（外部服务，POST `https://api.deepseek.com/v1/tools/search` [P11: docs/external_api/deepseek_search_fetch.md:§端点与鉴权]）经项目自有端口 `SearchProvider` 接入；`NullSearchProvider` / `FakeSearchProvider` / 注册表保留 | API 版本：**未知**（资料未给）；资料摘录日期 2026-11-02 | 新增（外部服务 + 项目内适配器 `deepseek.py`，无第三方包） | D-07 / CP-003「Q7 纳入」；复用 Key、单次尝试、平台强制超时（ADR-R28-11）；可替换、缺省关闭、复用优先（C-R28-09）。限流 / 计费：Search QPS 100（账户级）；每 1000 次成功请求 0.75 美元，仅 200 且有结果计费 [P11: docs/external_api/deepseek_search_fetch.md:§限流与计费] | REQ-FUNC-016/019、REQ-NFUNC-005/006/007/011 | 中：资料未核对原页面（OQ-ARCH-R28-06）；资料未给超时 / 重试口径（A-14 / A-15）；真实端点效果列目标机人工验证（AC-014-06） |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + vue-router（hash） | `vue ^3.4.0`、`element-plus ^2.8.0`、`typescript ^5.4.0`（`src/frontend/package.json:18,19,25`） | 沿用 | 新增页面 / 纯函数模块沿用现有结构；HTTP 只经 `client.ts`（无 axios，P6/P8） | REQ-FUNC-003/004/018 | 低 |
| 测试 | pytest（后端）、Node 内置 `node:test`（前端） | `"test": "node --test"`（`package.json:14`）；CI Node 22（`ci.yml:240`） | 沿用 | 离线替身：`FakeSearchProvider`（端口级）、**`FakeDeepSeekTransport`（传输级，按资料字段与错误码构造 200 / 空结果 / 400 / 401 / 402 / 403 / 404 / 408 / 413 / 429 / 500 / 504，资料"测试替身"节：无官方沙箱）**、`FetchTransport` / `Resolver` 注入、LLM 替身；**自动化测试禁止触达真实 DeepSeek 端点**（构造器强制注入传输 + 单测 monkeypatch `socket.create_connection` 零外联）；真实联网与真实 LLM 精准度为目标机人工项（C-R28-02） | REQ-NFUNC-008、AC-014-06 | 中：评测集由用户提供，提供前验收"待评测集确认"；替身的错误体取值为占位，适配器不依赖 |
| 进程管理 / 容器化 | systemd；**无容器**（P8） | 画像 P7 | 沿用 | 不新增运行单元 | C-R28-03 | 无 |
| CI/CD | GitHub Actions `ci.yml`（10 阶段） | 画像 P7 | 沿用 + 追加检查 | 迁移检查追加 009；selfcheck 新用例（含 2.1.0 的替身生产禁用 / DeepSeek 契约 / 凭据复用自检）；依赖安装多一行 `lxml`（已被 python-docx 满足） | REQ-NFUNC-001 | 低 |
| 部署方式 | 目标机 `git pull` + `sudo -n systemctl restart ib-web`；前端本地构建 | 画像 P7 | 沿用 | 仅 ib-web 与前端受影响；env 文件 / unit / nginx 变更由用户执行 | — | 需用户编辑 `/etc/intelligentbase/ib-web.env`（仅键名，不写值） |
| 密钥管理 | **复用现有 DeepSeek API Key**：台账 `llm_key` 单行表（管理页 `PUT /api/llm-key` 写入；兼容回退环境变量 `IB_LLM_API_KEY`），经 `resolve_llm_api_key` 在装配期解析一次，同时供 LLM 与联网搜索 | 位置：[CODE: src/ibweb/composition.py:817-822]、[CODE: src/ib/llm/__init__.py:461-466]；值不入库 / 不入文档 | **沿用（2.1.0 撤销新增键）** | REQ-NFUNC-006：不新增任何凭据项、不新增存放位置；`IB_WEB_SEARCH_API_KEY` 与 `IB_WEB_SEARCH_BASE_URL` 删除；Key 只发往常量主机 `api.deepseek.com`；轮换（保存 + 重启 ib-web）对 LLM 与搜索同时生效（AQ7）；`env.example` 无新增占位，`deploy_templates_have_no_secrets` 自检继续覆盖 | REQ-NFUNC-006 | 低：LLM 服务方须为 DeepSeek（A-17，否则启动失败）；Key 未配置时联网按"未配置"降级 |
| 新增依赖汇总 | **`lxml>=5.0,<7.0`（显式声明）**；无其他。DeepSeek Search API 是外部服务，不是软件依赖；不新增 Python 包、不新增凭据、不新增运行单元 | 见上 | — | — | — | — |

## 许可证与维护登记（新增 / 变更依赖）

| 依赖 | 许可证 | 维护状态 | 备注 |
|---|---|---|---|
| lxml 6.1.3（当前稳定版） | BSD-3-Clause（[WEB: https://pypi.org/pypi/lxml/json，2026-11-02]；`license_expression` 字段为空，以 `info.license` 为准） | 活跃：changelog 记 6.1.3 日期 2026-09-02（同一来源） | 非 copyleft，与项目许可策略兼容；wheel 为 manylinux 预编译，不需要 AVX2 以外的特殊指令集（`[ASSUMPTION]`：未在目标老 CPU 上单独验证；因其本已随 python-docx 安装在生产 venv 并在运行，风险低） |
| python-docx 1.2.0（既有） | MIT（[WEB: https://pypi.org/pypi/python-docx/json，2026-11-02]） | 既有依赖，本轮不改 | 其 `lxml>=3.1.0` 约束宽于本轮声明，不冲突 |
| DeepSeek Search / Fetch API（外部服务，非软件包） | **未知**（资料未载服务条款 / 许可；使用受 DeepSeek 官方条款约束，需用户确认） | 官方文档页 https://api-docs.deepseek.com/guides/search（经主会话整理，未联网复核） | 计费：每 1000 次成功请求 0.75 美元 [P11: docs/external_api/deepseek_search_fetch.md:§限流与计费]；QPS 与用哪个 Key 无关 |

画像 P8 核对：`lxml` 不在禁用项；未引入 torch / transformers / FlagEmbedding / onnx / PyMuPDF / langchain-openai ≥0.3 / axios / CDN；无 Docker。画像 P6：Python 依赖下界 + 上界都写（`lxml>=5.0,<7.0`）；三份清单分工不变（`requirements-embed.txt` 不动）。

## 技术风险

### High
- **R-1 联网占用请求线程**（`waitress --threads=8`）：单次联网最坏占用一个线程至超时；缓解 = 并发闸（同时联网 ≤3）、协作式期限 + `_execute_tool` 看门狗、单轮累计耗时上限（全局，默认 30 秒）、池满快速失败降级（M-SA-006）；`[TBD-R28-2]` 目标机压测校准闸大小与上限。
- **R-2 理解步骤 LLM 准确率**（意图 / 指代 / 话题）：误判会导致错误旁路 `route` 或把专业问题联网外发。缓解 = `unknown` 一律走路由；评测集阈值（0.90 / 0.85 / 0.85 / ≤0.02）；评测集待用户提供前验收"待评测集确认"；真实 LLM 实测为人工项。
- **R-3 SSRF**：缓解 = `getaddrinfo` 统一解析 + 显式拒绝网段 + `is_global` 取交、钉 IP 连接、逐跳重校验、仅 80/443、禁代理、≥30 条拒绝用例；运维出站 ACL 作第二道防线（用户执行）。
- **R-4 引擎改动回归未启用项目**：缓解 = 全部新行为以 `view.advisor_id` 等显式条件门控；"同输入逐字相同"回归集 + 既有全量回归零新增失败（画像 P5 baseline）+ 真实 langgraph 契约测试。

### Medium
- **R-5 搜索厂商接入延期 / 资料缺口**（2.1.0 降级为 Low，已由 R-11~R-13 取代其具体内容）：厂商已定为 DeepSeek，P11-3 已补；端口 + 替身保留，顾问其余能力不受阻（联网降级）。
- **R-6 语义泄露**（知识库内容被改写后写入检索词）：逐字重叠闸只拦原样复制；缓解 = 提示词约束 + 域名白名单 + 出站 ACL；写入残余风险，不宣称根除。
- **R-7 `is_delegating` 语义复用**：旧配置页复选框可误关顾问模式；缓解 = 面板提示 + 注释 + 发布前核查存量定义无同名专家。
- **R-8 保真守卫误报**（语义等价改写被判缺失）：规则可调；**失败时返回统一致歉文本、不展示被委托 agent 原答**（AQ1=B，用户裁决；误报直接变成用户可见致歉，故实际影响高于初版评估，见 architecture_design R-7 与 `[TBD-R28-4]`）；`advisor_apology` 事件按原因计数入日志。
- **R-9 lxml 解析面**：缓解见选型表。
- **R-10 延迟**：每个顾问回合 LLM 调用 ≥3 次（理解 + 被委托 agent + 顾问），端到端时延未测 `[TBD-R28-1]`，目标机校准前标"未验收"（OQ-R28-11=A）。

- **R-11 DeepSeek 外部依赖**（2.1.0 新增）：账户级 QPS（Search 100）、余额不足（402）、服务端 / 下游错误（500 / 504）、按次计费。缓解 = 并发闸 3 + 每轮调用上限（缺省 5；按资料单价最坏每轮约 0.00375 美元，`5 × 0.75 / 1000`，且仅成功且有结果才计费）、状态码分类降级且不暴露细节、不重试、离线替身覆盖资料列出的全部错误码 `[P11: docs/external_api/deepseek_search_fetch.md:§限流与计费、§错误]`。
- **R-12 资料未经原页面核对**（2.1.0 新增）：`deepseek_search_fetch.md` 由主会话整理，PM 与本架构均未核对原页面；字段名或错误码若有出入，自动化测试（用替身）发现不了。缓解 = 目标机验证前由人工核对原页面（OQ-ARCH-R28-06），AC-014-06 的人工清单；适配器只依赖资料明确列出的状态码、不读错误体，减少对资料细节的耦合。
- **R-13 保留本地抓取的出站面**（2.1.0 新增，ADR-R28-12 的代价）：ib-web 在抓取总开关开启后需出站公网 80/443。缓解 = 缺省关闭；`UrlGuard` 钉 IP + 逐跳重校验 + ≥30 条拒绝用例；运维出站 ACL 作第二道防线；重新评估触发条件见 ADR-R28-12。

### Low
- **全局工具目录新增两个工具名**（所有项目配置页可见，无 agent 被授权则行为不变）：AQ3=A 已裁决（用户 CP-002）：列表恰多 2 项属展示变化，行为零变化（AC-017-05）。
- **LLM 服务方非 DeepSeek 时搜索不可用**（2.1.0）：`IB_WEB_SEARCH_PROVIDER=deepseek` 要求 `IB_LLM_BASE_URL` 主机为 `api.deepseek.com`，否则启动失败（A-17）；缺省配置满足。
- **Key 轮换需重启才对搜索生效**（2.1.0）：与 LLM 同语义（AQ7）。
- **`lxml` 在开发机未安装**：本地 pytest 本就不可用（画像 P4）；CI 经 offline 清单安装；缺失时 `web_fetch` 降级而非崩溃。
- **会话重启丢失**：OQ-R28-06=A 已知现状。
- **目标机 lxml 版本**：`[TBD-R28-3]` 部署前只读核对 venv 内版本是否满足 `>=5.0,<7.0`，不满足才升级（由用户 / devops 在 E1 / E2 处理）。
