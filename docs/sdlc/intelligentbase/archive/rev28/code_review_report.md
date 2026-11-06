<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-03T18:35:30+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>4.0.0</version>
  <input_files><file>docs/sdlc/intelligentbase/module_design.md</file><file>docs/sdlc/intelligentbase/implementation_plan.md</file><file>docs/external_api/deepseek_search_fetch.md</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — REV-28 平台级内置「顾问 agent」

REV-27 版本已归档于 `docs/sdlc/intelligentbase/archive/rev27/code_review_report.md`（只读）。本报告为 REV-28 自评审（0.1.0 DRAFT）；ET 解析不适用（Markdown 表格正文）。

## 摘要

`git diff --stat -- src tests`（仅追踪文件；2.1.0 后）：**35 files changed, 1878 insertions(+), 91 deletions(-)**（含工作区内与本 REV 无关的既有未提交改动，不代表本轮增量）；另有未追踪文件：2.0.0 的 18 个新增文件，加 2.1.0 新增 `src/ib/webtools/deepseek.py`、`deepseek_double.py`（`webtools/` 为未追踪目录，故不在 diff --stat 内）。2.1.0 本轮触及的文件见 implementation_plan "变更文件清单（2.1.0）"，无无关文件。

五维平均分（18 个 MOD 的算术平均；逐模块评分见下；2.1.0 仅 MOD-R28-03 重评：Correctness 9→8、Maintainability 9→8）：Correctness 8.17 / Security 9.00 / Performance 8.61 / Maintainability 8.28 / Testability 8.39；总平均 **8.49**（764/90）。无低于 6 的维度（MOD-R28-18 Testability = 6，为最低值，对应 CR-011）。

问题统计（累计，含 2.1.0）：**CRITICAL 1（已修复 1）/ MAJOR 7（已修复 4，遗留 3）/ MINOR 9（已修复 2：CR-009、CR-017；遗留 7：CR-010~016）**。2.1.0 新增 CR-015、016、017，CR-009 因 ADR-R28-13 落地转 FIXED。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `src/ib/core/types.py`、`ports.py`、`__init__.py` | MOD-R28-01 / IFC-R28-001、002 |
| `src/ib/webtools/netguard.py`、`policy.py`、`fetch.py`、`__init__.py` | MOD-R28-02 / IFC-R28-003、004 |
| `src/ib/webtools/search.py`、`deepseek.py`、`deepseek_double.py`（2.1.0） | MOD-R28-03 / IFC-R28-005、029、030 |
| `src/ib/llm/__init__.py` `resolve_llm_api_key`（2.1.0）；`src/ib/config/__init__.py` 校验与键删除（2.1.0） | MOD-R28-09 / IFC-R28-031；MOD-R28-07 / IFC-R28-011、032 |
| `src/ib/webtools/gate.py` | MOD-R28-04 / IFC-R28-006 |
| `src/ib/webtools/tools.py` | MOD-R28-05 / IFC-R28-007 |
| `src/ib/ledger/schema.py`、`web_governance.py`、`__init__.py`、`src/deploy/migrations/009_web_governance.sql` | MOD-R28-06 / IFC-R28-008 |
| `src/ib/config/graph.py`、`prompts.py`、`__init__.py`、`src/ib/experts/__init__.py`、`src/ib/expert_seeds/advisor.md` | MOD-R28-07 / IFC-R28-009、010、011 |
| `src/ib/tools/__init__.py` | MOD-R28-08 / IFC-R28-012 |
| `src/ib/llm/__init__.py` | MOD-R28-09 / IFC-R28-013 |
| `src/ib/advisor/*.py` | MOD-R28-10 / IFC-R28-014~017 |
| `src/ib/builder/types.py`、`rubric.py`、`adapt.py` | MOD-R28-11 / IFC-R28-018 |
| `src/ib/orchestration/dag.py`、`__init__.py` | MOD-R28-12 / IFC-R28-019 |
| `src/ib/runtime/compile.py`、`src/ib/observability/__init__.py` | MOD-R28-13 / IFC-R28-020 |
| `src/ibweb/composition.py`、`src/deploy/env.example` | MOD-R28-14 / IFC-R28-021 |
| `src/ibweb/views.py`、`config_views.py`、`urls.py` | MOD-R28-15 / IFC-R28-022~025 |
| `src/scripts/selfcheck.py`、`advisor_eval.py`、`src/requirements.txt`、`requirements-offline.txt` | MOD-R28-16 |
| `src/frontend/src/api/client.ts`、`components/config/advisorPlan.ts` | MOD-R28-17 / IFC-R28-026、027 |
| `ProjectsPage.vue`、`ConfigStudio.vue`、`AgentDetailPanel.vue`、`WebGovernancePage.vue`、`ConsoleLayout.vue`、`router/index.ts` | MOD-R28-18 / IFC-R28-028 |
| `tests/integration/test_prompt_config_r16.py`、`test_prompt_tool_config_int_r16d.py`、`tests/unit/test_prompt_tool_config_unit_r16d.py` | 既有测试（AQ3=A 预期更新点，见 implementation_plan） |

## 自验证结果

环境变量：`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`；venv `/root/.venvs/intelligentbase`，未安装任何依赖。

| 命令 | 输出尾部 | 与基线 |
|---|---|---|
| `python -m compileall -q src` | 无输出（退出码 0，`COMPILE_OK`） | — |
| `python -m pytest tests -q -p no:cacheprovider`（全量；含 3 个按 AQ3 调整的既有测试文件） | `914 passed in 27.66s` | 基线 914 passed → 新增失败 0 |
| `python src/scripts/selfcheck.py` | `自检结果：64/65 通过`；失败项仅 `core_framework_free：… 引入了第三方顶层包：sitecustomize`（环境性既有失败） | 基线 57 PASS / 1 FAIL → 新增失败 0；新增用例 7 个全 PASS（`web_egress_single_exit`、`web_ssrf_rejects`（≥30 条）、`web_governance_schema_single_source`、`advisor_graph_rules`、`advisor_seed_clean`、`search_port_conformance`、`advisor_apology_text_safe`） |
| `cd src/frontend && npm run build` | `✓ built in 33.20s`（含 `vue-tsc --noEmit`） | — |
| `cd src/frontend && npm test` | `# tests 141 / # pass 141 / # fail 0` | 基线 141/141 → 新增失败 0 |

**未验证项（如实）**：真实 `PinnedTransport`（钉 IP 的 HTTP / TLS 连接）、真实 DNS 解析（仅做了 `localhost` 级本机解析冒烟）、真实搜索厂商（Q7=C，本轮无适配器）、真实 LLM 的理解步骤输出遵从度（A-7）、浏览器内的前端交互（无挂载环境）、`advisor_eval.py` 对真实 LLM 的运行（`langchain-openai` 未安装，且评测集由用户提供）。

## 按模块评审

评分口径：0–10，本轮为自评审；"正确性"考虑未被真实环境验证的部分。

| MOD | Correctness | Security | Performance | Maintainability | Testability | 均分 |
|---|---|---|---|---|---|---|
| MOD-R28-01 | 9 | 9 | 9 | 9 | 9 | 9.00 |
| MOD-R28-02 | 8 | 9 | 8 | 8 | 9 | 8.40 |
| MOD-R28-03 | 8 | 9 | 9 | 8 | 9 | 8.60 |
| MOD-R28-04 | 8 | 9 | 8 | 8 | 9 | 8.40 |
| MOD-R28-05 | 8 | 9 | 8 | 8 | 8 | 8.20 |
| MOD-R28-06 | 9 | 9 | 9 | 9 | 9 | 9.00 |
| MOD-R28-07 | 9 | 9 | 9 | 9 | 9 | 9.00 |
| MOD-R28-08 | 8 | 9 | 9 | 8 | 9 | 8.60 |
| MOD-R28-09 | 8 | 9 | 8 | 8 | 8 | 8.20 |
| MOD-R28-10 | 8 | 9 | 8 | 9 | 9 | 8.60 |
| MOD-R28-11 | 9 | 9 | 9 | 9 | 9 | 9.00 |
| MOD-R28-12 | 7 | 9 | 8 | 7 | 7 | 7.60 |
| MOD-R28-13 | 9 | 9 | 9 | 9 | 9 | 9.00 |
| MOD-R28-14 | 8 | 9 | 8 | 7 | 7 | 7.80 |
| MOD-R28-15 | 8 | 9 | 9 | 8 | 8 | 8.40 |
| MOD-R28-16 | 8 | 9 | 9 | 8 | 8 | 8.40 |
| MOD-R28-17 | 8 | 9 | 9 | 9 | 9 | 8.80 |
| MOD-R28-18 | 7 | 9 | 9 | 8 | 6 | 7.80 |
| **维度平均** | **8.17** | **9.00** | **8.61** | **8.28** | **8.39** | **8.49** |

### MOD-R28-01 核心类型与端口扩展
追加字段均带默认值，既有构造调用与序列化不变（全量 914 passed 佐证）。`SearchQuery.__post_init__` 构造期校验 ~~1..200 / 1..10~~ → 2.1.0：1..128 / 1..50 / >0（资料收紧）；新增常量 `DEEPSEEK_API_HOST`。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

### MOD-R28-02 地址防护与安全抓取
SSRF：`getaddrinfo` 统一解析、全部地址须通过"18 个显式网段 ∩ `is_global`"、IPv4 映射按内嵌地址判、zone id 拒绝、端口仅 80/443、userinfo / 控制字符 / 超长拒绝、每跳重校验、`Accept-Encoding: identity`、无 Cookie / Authorization / Referer；selfcheck 53 条拒绝用例（含重定向到内网、跳数超限）全部通过。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MAJOR | `webtools/netguard.py`（初版） | 初版 `netguard.py` 持有 `socket` 导入（默认解析器），违反 `web_egress_single_exit`（仅 `fetch.py` / `search.py` 可持有网络导入）。已把 `default_resolver` 移到 `fetch.py`，`UrlGuard` 惰性引用 | FIXED |
| CR-012 | MINOR | `webtools/fetch.py` `default_resolver` | `getaddrinfo` 不可取消：超时后后台线程继续至 OS 解析超时；已用 ≤4 的隔离线程池 + 满则拒绝兜底（设计已知风险，ADR-R28-03 后果 (2)） | OPEN |

### MOD-R28-03 搜索提供方适配
2.1.0 重写：`search.py`（工厂 / 注册表 / Null / Fake，仍无网络导入）、`deepseek.py`（适配器 + `UrllibPostTransport`，搜索侧唯一网络代码）、`deepseek_double.py`（离线替身，无网络导入）。密钥不进日志 / 异常消息 / `repr` / `health()` / `describe_egress()`；适配器只按状态码映射、不读错误体；单次尝试不重试；不跟随重定向；构造器强制 `transport`。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MINOR | `webtools/search.py` `build_search_provider` | 2.0.0：`provider_id="fake"` 在生产环境也被接受。2.1.0：非离线 + `fake` ⇒ `ConfigError`（Fake 不被构造），`validate_required` 同步拒绝（ADR-R28-13） | FIXED（2.1.0） |
| CR-015 | MINOR | `webtools/deepseek.py` `UrllibPostTransport.post_json` | 真实传输未对真实端点验证（P11-3 禁止）；套接字超时取 `timeout_s`，总期限仅在分块读取处检查，单次阻塞读最长可达 `timeout_s`，最坏总耗时约 `2×timeout_s`（A-9），由外层看门狗（`timeout_s+1`）兜底。仅做回环不可达冒烟与 opener 处理器清单核对 | OPEN（目标机人工验证，OQ-ARCH-R28-08） |
| CR-017 | MINOR | `webtools/deepseek.py`（自评审初版） | 模块文档串与 `encode_search_request` 文档串含字面量 `ori_question` / `localization`，违反 selfcheck `deepseek_adapter_contract` 的源码纪律（适配器源码不得含未使用的外发字段名）。已改写为中文描述 | FIXED |

### MOD-R28-04 联网出站闸与预算
顺序固定：并发闸（非阻塞）→ 审计先行（失败不执行 `fn`）→ 执行；出站文本闸：长度 → 秘钥模式 → 与私有语料 ≥24 字符重叠（URL 含解码后的 path / query）。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | CRITICAL | `webtools/gate.py`、`llm/__init__.py`（初版） | 设计的"线程局部"回合绑定在 `_execute_tool` 看门狗线程池中不可见，联网工具会因"缺少回合上下文"整体失效（或在改动时绕过预算 / 出站闸）。改用 `contextvars.ContextVar`，`_execute_tool` 以 `copy_context().run` 提交；联网路径冒烟（看门狗线程内预算 / 审计 / 私有语料可见）通过 | FIXED |

### MOD-R28-05 联网工具
永不抛；失败文本固定短语；AQ4：`fetcher is None` 在预算 / 出站闸 / 审计 / 并发闸之前短路并只记 `fetch_disabled`；LLM 实参仅 `query` / `url`，其余同名实参被 MOD-R28-08 丢弃。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题（A-6 见 implementation_plan） | — |

### MOD-R28-06 联网治理存储与迁移
009 与生成器逐字一致（selfcheck 单源 / 幂等 / CHECK / 老库补齐）；SQL 全参数化；`set` 校验 int 非 bool 且在范围内。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MAJOR | `ledger/web_governance.py` `build_web_governance_store`（初版） | 初版在离线夹具（`ledger_backend=memory`、`ledger_path=./var/ledger/…`）下无条件打开 SQLite，目录不存在 → 装配失败（全量 pytest 首轮 `ERROR`）；且会在离线测试时落盘。改为 `web_governance_backend=memory` 或 `ledger_backend=memory` 时用内存替身，并为 sqlite 路径创建父目录 | FIXED |

### MOD-R28-07 配置域
顾问规则仅在存在启用的顾问专家时追加；`canonical_graph_from_experts` 输出不变；种子 0 命中 `BLOCKED_TERMS` 且含三项条款用语。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

### MOD-R28-08 工具注册与参数闭包
`config_parameters=None` 的工具走原路径；配置胜出包装不暴露 `scope` / `knowledge` 形参。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MAJOR | `tools/__init__.py` `bind_scope` / `build_agent_tools`（初版） | 这两处重建 `BoundTool` 时未携带 `timeout_s`，联网工具会失去看门狗。已补 `timeout_s=getattr(item, "timeout_s", None)` | FIXED |

### MOD-R28-09 工具执行看门狗
`timeout_s is None` 与现状完全一致（占位文本不变）；事件回调异常被吞。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题（线程池 8 线程为模块级共享；超时的任务线程无法强杀，由工具自身的协作式期限兜底） | — |

### MOD-R28-10 顾问核心库
`understand` 永不抛、fail-open；`build_history_digest` 满足"窗口 20 / 整条从最旧丢弃 / 最近一条始终保留 / len ≤ 预算"（含单条超预算截断）。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-008 | MAJOR | `advisor/understand.py` `_PROMPT` | 理解步骤复用 `build_router()` 角色，其 system 提示要求"只输出 JSON 数组"，与理解器要求的 JSON 对象冲突；真实 LLM 的遵从度离线不可验证。不合规输出已 fail-open 为透传（路由照常），不影响可用性，但会削弱意图旁路 / 消解的收益。需目标机用评测集验收 | OPEN |

### MOD-R28-11 Agent Builder 评审口径
kb-agent 画像（含 `is_retrieval` 工具）返回原 `grounding_clauses`；顾问画像三项条款无条件适用；消息文案对非顾问画像逐字不变。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-010 | MINOR | `ibweb/composition.py` `_context` | Builder 的项目摘要 `tools` 现在对所有项目含 `web_search` / `web_fetch`（`is_external=True`），Builder 外发的 `project_digest` 内容随之多两项；属设计允许的目录可见变化，但影响 Builder 提示输入 | OPEN |

### MOD-R28-12 编排运行期
全部新行为以 `view.advisor_id` 为前提；步数上限不计顾问、顾问不会被记 `skipped_step_cap`；失败路径（节点降级 / 保真两次不过 / 节点内异常 / `run_dag` 未预期异常）统一返回 `ADVISOR_APOLOGY_TEXT`，叶子集合 = {顾问}，`_collect` 与默认专家安全网未改且在顾问模式下不会触发。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-007 | MAJOR | `orchestration/dag.py` `_advisor_node` | ADR-R28-09 要点 1 写"从被委托产出与联网结果中抽取保护片段"，实现只对祖先 agent 产出做保真核对，联网文本仅参与 `exceeds_quote_limit`。理由：联网结果含大量数字 / 网址，要求答复全部复述会使几乎每个联网回合触发致歉（用户裁决 AQ1=B 下误报直接可见）。联网事实"原样保留"目前仅靠提示词。需用户确认（implementation_plan Q-2 / A-1） | OPEN |
| CR-013 | MINOR | `orchestration/dag.py` `_advisor_node` | 函数长（约 110 行）、分支多，致歉判定与重试内联；可读性一般，建议后续拆分为"作答→核对→重试"小函数（本轮保持最小改动、行为已由冒烟覆盖 6 条路径） | OPEN |

### MOD-R28-13 运行时编译
未启用项目：`advisor_id=None`、无理解器、无 `turn_scope`；日志白名单仅追加精确键名。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

### MOD-R28-14 组合根
API Key 仅在 `_assemble` 读环境一次传入 `build_web_runtime`，不进 `GlobalConfig` / 日志 / 审计 / 描述；`seed_project(with_advisor=False)` 路径逐位不变；`_plain_validate` 对含联网授权文档在上限不可读时 fail-closed。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MAJOR | `ibweb/composition.py` `Deps.bind_tools`（初版） | 防御性回落（项目无授权文档）会 `bind_scope(registry.registered())`，联网工具恒登记后将被绑定给所有此类项目的 agent，违反"未启用项目逐位一致"。已过滤 `external=True` 的工具 | FIXED |
| CR-006 | MAJOR | `.github/workflows/ci.yml`（MOD-R28-16 子项） | 迁移检查步骤未追加 009：画像 P7 把 CI 配置归 devops，开发角色不写 CI 配置。等价检查由 selfcheck `web_governance_schema_single_source`（CI 已运行 selfcheck）覆盖；已在 implementation_plan Q-1 移交 | OPEN |

### MOD-R28-15 HTTP 接口
`enable_advisor` 非 bool → 400 且先于创建（不留半成品）；`/api/web-governance` 仅 admin、逐字段 400、存储不可用 503；`/healthz/deps` 在 `egress_web` 为空时不追加键（基线逐字节一致）。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

### MOD-R28-16 自检 / CI / 评测脚本 / 依赖清单
`lxml>=5.0,<7.0` 上下界都写，仅 `requirements.txt` / `requirements-offline.txt`；`env.example` 仅注释形态占位。`advisor_eval.py` 不内置合成集，统计逻辑经替身验证。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MAJOR | （同 MOD-R28-14 表） | 同上，不重复计数 | OPEN（见上） |

### MOD-R28-17 前端 API 与顾问接线纯函数
`createProject` 仅当 `enableAdvisor === true` 才加键，其余请求体与既有逐字相同；`addAdvisor`/`removeAdvisor` 往返恢复规范图（冒烟验证）。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

### MOD-R28-18 前端页面
HTTP 只经 `client.ts`；无 axios / CDN；"启用顾问"默认不勾选；联网上限页经"系统管理"导航可达（`SYSTEM_ORDER` 追加 `web-governance`，导航项由路由表派生，仅 admin 可见）。
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-011 | MINOR | `src/frontend/tests/`、`tests/unit|integration|e2e/*rev28*` | 本轮未提交新测试文件（`advisor_r28.test.js` 及后端 `*_rev28.py`，属 GROUP_D 职责）；前端组件交互无挂载环境，仅 `advisorPlan.ts` 做了脚本冒烟。Testability 6 分对应本条 | OPEN |

## 未解决的 CRITICAL

无（CR-001 已修复）。

## 遗留 MAJOR

遗留 3 条（≤3，无强制逐条要求，仍逐条说明）：

| CR | 原因 | 建议处理时机 |
|---|---|---|
| CR-006 | 角色边界：CI 配置归 devops；selfcheck 已等价覆盖 | 下一轮 GROUP_E1 追加 `ci.yml` 迁移检查 009 |
| CR-007 | 与 ADR 文字有出入且涉及用户可见误报权衡，需用户裁决 | 本轮门控 / 用户确认（Q-2） |
| CR-008 | 离线无法验证真实 LLM 遵从度；已 fail-open | 目标机用评测集运行 `advisor_eval.py` 后；若遵从度低，改为专用理解角色（需设计变更） |

## 缺陷修复

非缺陷修复模式（无 `<defects>`）。

## 现有测试调整

3 个既有测试文件共 4 处断言（原因：AQ3=A，全局工具目录恰好多出 `web_search`、`web_fetch`），逐条改前改后见 implementation_plan "既有测试调整"：

1. `tests/integration/test_prompt_config_r16.py::test_TC_INT_R16_prompt_list_contract` — `available_tools` 与 `tool_param_specs` 两处；
2. `tests/integration/test_prompt_tool_config_int_r16d.py::test_TC_INT_136_single_registration_point_tools_and_params` — 工具名元组与规格列表；
3. `tests/unit/test_prompt_tool_config_unit_r16d.py::test_TC_UNIT_123_search_tool_spec_exposes_optional_retrieval_param_specs` — 规格集合。

均保留 `search_knowledge` 的精确断言（集合 / 顺序不变），仅放行"其余项恰为 `web_search` / `web_fetch`"；未放宽任何无关断言。

## 修订记录（1.1.0，DEF-001 修复）

### 缺陷修复补充

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-001 | `src/ib/webtools/tools.py`（`_web_fetch`，原 300-302 行）；`src/ib/webtools/gate.py`（`TurnBudget.charge_bytes`） | `add_bytes` 先判超限再累计，超限时抛 `WebBlocked` 且不累计，调用处 `except WebBlocked: pass` 吞掉，导致超限失败的抓取字节未入账，同回合可重复超限抓取 | 新增无条件累计的 `charge_bytes`，调用处改用之；`add_bytes` 不变；耗尽后由既有 `remaining_bytes <= 0` 在出站前拒绝 |

### 新增评审条目

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-014 | MINOR | `src/ib/webtools/gate.py` `charge_bytes` | 超限读取全额计入，`bytes_used` 可略大于上限；语义为"耗尽即拒"，不影响上限约束。`add_bytes` 现无生产调用方，保留供既有单测 | OPEN |

### 自验证（1.1.0，历史）

环境同上（venv `/root/.venvs/intelligentbase`，PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings）。

| 检查 | 命令 | 结果 |
|---|---|---|
| 编译 | `python -m compileall -q src` | `COMPILE_OK` |
| 全量后端 | `python -m pytest tests -q -p no:cacheprovider` | `1 failed, 1230 passed`；失败仅 `test_TC_UNIT_R28_085_fetch_tool_total_bytes_budget_and_call_limit`（`assert tr.count == 3`，实际 2；预期信号，冻结守卫 DEF-001-GUARD） |
| selfcheck | `python src/scripts/selfcheck.py` | `自检结果：64/65 通过`（失败仅 `core_framework_free`，环境性既有） |

改动范围：`src/ib/webtools/gate.py`（+5 行）、`src/ib/webtools/tools.py`（-4/+2 行）；`webtools/` 为未追踪新目录，故 `git diff --stat` 无输出。无测试文件改动；本轮五维评分不变，问题统计增 MINOR 1（共 MINOR 6）。

## 修订记录（2.1.0，Q7 纳入：DeepSeek 搜索适配器；新增范围，非缺陷回流）

依据：module_design 3.0.0 MOD-R28-03、IFC-R28-029~032，ADR-R28-11/12/13；唯一外部出处 `docs/external_api/deepseek_search_fetch.md`（画像 P11-3）。逐文件改动与 selfcheck / 既有测试口径变更见 implementation_plan "修订记录 2.1.0"。

### 文件 → MOD/IFC（2.1.0 增量）

| 文件 | MOD / IFC |
|---|---|
| `src/ib/webtools/deepseek.py`（新）、`deepseek_double.py`（新）、`search.py`（改） | MOD-R28-03 / IFC-R28-005、029、030、032（工厂闸） |
| `src/ib/core/types.py`、`core/__init__.py` | MOD-R28-01 / IFC-R28-001（`SearchQuery` 取值域、`DEEPSEEK_API_HOST`） |
| `src/ib/llm/__init__.py` | MOD-R28-09 / IFC-R28-031 |
| `src/ib/config/__init__.py` | MOD-R28-07 / IFC-R28-011、032 |
| `src/ib/webtools/gate.py`、`policy.py`、`tools.py` | MOD-R28-04 / 02 / 05（IFC-R28-006、003、007：128 字符、lang 校验、1..50、空检索词短语、摘要 800） |
| `src/ibweb/composition.py`、`src/deploy/env.example` | MOD-R28-14 / IFC-R28-021 |
| `src/scripts/selfcheck.py` | MOD-R28-16 |
| `AgentDetailPanel.vue` | MOD-R28-18（AQ6=A 静态提示） |
| `tests/unit/test_webtools_tools_unit_r28.py`、`tests/integration/test_advisor_web_int_r28.py` | 既有测试调整（见下） |

### 2.1.0 评审要点（按设计硬约束逐条核对）

| 约束 | 核对结论 | 证据 |
|---|---|---|
| 自动化 / 自验证不调用真实端点 | 满足：构造器强制 `transport`；`UrllibPostTransport` 仅在 `build_search_provider` 非离线 + `deepseek` + 有 Key 分支构造，全部测试与自检均离线（`offline_mode=1` ⇒ Fake）；回环冒烟仅连 `127.0.0.1:1` | selfcheck `search_fake_rejected_in_production`（离线路径真实传输构造数 = 0） |
| 请求只发 `query` / `count` / `need_content`；query ≤128；count 1..50 | 满足 | `deepseek_adapter_contract` |
| 不重试；不读错误体；不暴露错误细节 | 满足：`HTTPError` 仅取 `code` 后 `close()`；意外异常统一 `bad_response`，不记录细节 | `deepseek_adapter_contract`（请求数 = 1） |
| Key 不进日志 / 异常 / `repr` | 满足：`repr` 固定串；构造器异常文案不含 Key；`DoubleRequest` 只记 `authorization_ok` | `search_port_conformance`、`deepseek_double_covers_p11` |
| 非离线 + `fake` ⇒ 启动失败只报键名 | 满足：`validate_required` 与工厂双重拒绝，消息不含所配值 | `search_fake_rejected_in_production` |
| 复用 LLM Key 解析点，不新增凭据 | 满足：`resolve_llm_api_key` 单点；两个旧键与 `web_search_base_url` 删除 | `web_key_reuse_no_new_credential` |
| `env.example` 无真实值 | 满足（仅删除两行并改注释） | `deploy_templates_have_no_secrets` PASS |
| 未启用顾问 / `none` 缺省行为逐位一致 | 满足：`resolve_llm_api_key` 为原逻辑搬移；`_offline_view` 对 `none` 保持；全量 pytest 1232 passed | 全量回归 |
| 资料未写的数值标假设 | 满足：2 MiB（A-14）、lang 正则（A-16）、不重试（A-15）、不跟随重定向（A-18）、非 2xx/其他 4xx 映射（[ASSUMPTION]）在注释中标出 | `deepseek.py` 注释 |

### 新增评审条目（2.1.0）

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MINOR | `webtools/search.py` | 见 MOD-R28-03 表：因 ADR-R28-13 落地转 FIXED | FIXED |
| CR-015 | MINOR | `webtools/deepseek.py` `UrllibPostTransport` | 真实传输未对真实端点验证；最坏总耗时约 `2×timeout_s`（A-9） | OPEN |
| CR-016 | MINOR | `tests/integration/test_advisor_web_int_r28.py::test_TC_INT_R28_223` | 因旧键 / 自定义提供方路径取消，该用例对“非离线 Key 流向”的覆盖减弱（离线夹具下搜索提供方统一为 Fake，哨兵 Key 经 `IB_LLM_API_KEY` 仅验证不泄露面）；DeepSeek 路径的 Key → 请求头 → 不入日志需 GROUP_D 以 `FakeDeepSeekTransport.requests` 新增用例覆盖 | OPEN（移交 GROUP_D） |
| CR-017 | MINOR | `webtools/deepseek.py`（初版文档串） | 含未使用外发字段名字面量，违反源码纪律；已改写 | FIXED |

评分变化：仅 MOD-R28-03（Correctness 9→8：真实传输未验证；Maintainability 9→8：新增 3 个文件 + 惰性 import 分支，复杂度上升）。其余 MOD 的 2.0.0 评分不变（MOD-R28-01/05/07/09/14/16/18 的 2.1.0 改动均为小幅、被新增自检覆盖，未改变其评分依据）。总平均 8.51 → 8.49；无低于 6 的维度。

### 遗留 MAJOR（2.1.0 无变化）

仍为 CR-006、CR-007、CR-008 共 3 条（≤3），原因与建议时机见上文“遗留 MAJOR”。2.1.0 未新增 MAJOR。

### 现有测试调整（2.1.0，逐条）

1. `tests/unit/test_webtools_tools_unit_r28.py::test_TC_UNIT_R28_075_…`：期望 `[10, 1, 5]` → `[50, 1, 5]`（条数上限 10 → 50，IFC-R28-001 / 007）。
2. `…::test_TC_UNIT_R28_091_…`：工厂调用补 `offline=` 关键字、去 `base_url`；删除两条“`http://` 或缺 Key ⇒ Null”断言（该退化规则随 `base_url` 删除取消）；其余断言保留。
3. `tests/integration/test_advisor_web_int_r28.py::test_TC_INT_R28_223_…`：取消自定义提供方 `r28cred` 与两个已删除的键，哨兵 Key 改经 `IB_LLM_API_KEY`，期望主机 `search.r28.test` → `fake.invalid`（离线整体切替身）；全部“哨兵串出现 0 次”断言保留。

详细改前 / 改后与原因见 implementation_plan "既有测试调整（2.1.0）"。未放宽任何无关断言。selfcheck 口径变更（`web_egress_single_exit`、`search_port_conformance` 两条既有，另新增 4 条）逐条见 implementation_plan "selfcheck 口径变更"。

### 缺陷修复

非缺陷修复模式（无 `<defects>`）。

### 自验证（2.1.0）

| 命令 | 输出尾部 | 与当前基线（1232 / 64/65 / 160） |
|---|---|---|
| `python -m compileall -q src` | `COMPILE_OK` | — |
| `python -m pytest tests -q -p no:cacheprovider` | `1232 passed in 47.02s` | 新增失败 0 |
| `python src/scripts/selfcheck.py` | `自检结果：68/69 通过`；失败项仅 `core_framework_free`（`sitecustomize`，环境性既有） | 新增失败 0；新增 4 个用例全 PASS |
| `cd src/frontend && npm run build` | `✓ built in 33.66s` | — |
| `cd src/frontend && npm test` | `# tests 160 / # pass 160 / # fail 0` | 新增失败 0 |

**未验证项（如实）**：`UrllibPostTransport` 对真实 `api.deepseek.com` 的 TLS / 重定向 / 超时 / 代理行为（P11-3 禁止调用真实端点；列目标机人工验证）；资料本身由主会话整理、PM 未核对原页面。
ET 解析不适用（Markdown 表格正文）；文件头为 `&lt;`/`&gt;` 安全的纯文本。

## 修订记录（3.1.0，缺陷回流 2/2）

### 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-002 | `src/ib/orchestration/__init__.py` `_run_dag_turn`（摘要 / `AdvisorTurn` 构造） | A-12 兜底只覆盖 `run_dag` 调用，理解步骤之后的回合准备在 try 之外，异常逃出到视图层只剩 error 事件 | 准备段包进 try，异常 ⇒ 日志（仅异常类名）+ `ADVISOR_APOLOGY_TEXT` + 写历史 + 终态；仅顾问分支，未启用顾问项目不变 |
| DEF-004 | `src/ib/builder/egress.py` `render_user_message`（根源字段 `types.py:107`、`composition.py:1333`） | `ToolDigest.is_external` 经 `asdict` 对所有工具恒输出，基线条目多出键 | 外发序列化时 `is_external` 仅为真保留；dataclass 与装配不动 |
| DEF-005 | `src/ib/webtools/tools.py` `_web_fetch` | `http_error` 一律落到通用“网页抓取失败” | 401/403/429 ⇒ “目标网站拒绝了访问”，其余 `http_error` ⇒ “该网页无可用内容”，不含状态码 |
| DEF-006 | `src/ib/webtools/fetch.py` `_fetch` | 200 且抽取为空仍判 ok + 空正文 | 空正文 ⇒ 失败 `empty_content` ⇒ “该网页无可用内容” |

DEF-003 本轮不修（CR-008 已接受设计，待用户裁决）。

副作用评估：`FetchResult` / `SafeFetcher.fetch` 调用方仅 `tools.py::_web_fetch`（grep 核对）；`render_user_message` 的 `asdict` 仅作用于 `project_digest`，judge 载荷无 tools；全量回归无其他层新增失败。

### 新增评审条目（3.1.0）

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-018 | MAJOR | `orchestration/__init__.py` 顾问回合准备段 | DEF-002：准备段异常无致歉 | FIXED |
| CR-019 | MINOR | `builder/egress.py` | DEF-004：既有工具条目多出 `is_external` | FIXED |
| CR-020 | MAJOR | `webtools/tools.py` | DEF-005：拒绝与无内容不可区分 | FIXED |
| CR-021 | MAJOR | `webtools/fetch.py` | DEF-006：空正文判成功 | FIXED |
| CR-022 | MINOR | `tests/integration/test_advisor_http_int_r28.py:387`（344）与 `test_deepseek_search_int_r28.py`（421） | 两测试对 `search_knowledge.is_external` 键的要求互相矛盾；满足 421 后 344 KeyError；需 test-engineer 改 344 为 `.get` | OPEN |

### 统计（累计，含 3.1.0）

CRITICAL 1（已修复 1）/ MAJOR 10（已修复 7，遗留 3：原遗留不变）/ MINOR 11（已修复 3，遗留 8）。算术：MAJOR 7+3(CR-018/020/021)=10，已修复 4+3=7，遗留 10-7=3；MINOR 9+2(CR-019/022)=11，已修复 2+1(CR-019)=3，遗留 11-3=8。五维评分：受影响 MOD 评分不变。

### 自验证（3.1.0）

- `python -m compileall -q src`：通过。
- `pytest tests -q`（离线环境变量同 CI）：**2 failed, 1350 passed**；失败：TC-INT-R28-418[intent]（DEF-003，预期）、TC-INT-R28-344（CR-022，新增，测试间矛盾）。
- `python src/scripts/selfcheck.py`：68/69，仅 `core_framework_free`（既有，sitecustomize）失败。
- 前端：未改动，未运行。

### 现有测试调整

无（本轮未改任何测试）。
