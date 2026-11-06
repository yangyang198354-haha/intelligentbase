<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-06T21:13:39+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>4.0.0</version>
  <input_files><file>docs/sdlc/intelligentbase/implementation_plan.md</file><file>docs/sdlc/intelligentbase/module_design.md</file><file>docs/sdlc/intelligentbase/architecture_design.md</file><file>docs/sdlc/intelligentbase/requirements_spec.md</file><file>docs/sdlc/intelligentbase/user_stories.md</file><file>docs/sdlc/intelligentbase/tech_stack.md</file></input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — REV-29 agent 工具调用的 MCP 适配

REV-28 版本已归档于 `docs/sdlc/intelligentbase/archive/rev28/code_review_report.md`。本报告为 REV-29 全新版本（0.1.0 DRAFT，`REWORK_AUTHORIZED`）。

## 修订记录

| 版本 | 时间 | 说明 |
|---|---|---|
| 0.1.0 | 2026-11-05T16:06:04+08:00 | 初稿 |
| 0.2.0 | 2026-11-05T16:16:46+08:00 | GR-C-001 返工：测试断言严格化（见“现有测试调整”）；其余正文保留 |
| 1.1.0 | 2026-11-05T22:46:38+08:00 | 缺陷回流第 1 轮（GR-D-001）：追加文末“缺陷修复轮”，既有内容未删 |
| 2.1.0 | 2026-11-05T23:13:57+08:00 | 缺陷回流第 2 轮（GR-D-002）：追加文末“缺陷修复轮 2”，既有内容未删 |
| 3.1.0 | 2026-11-06T21:13:39+08:00 | 缺陷回流第 3 轮（DEF-R29-008、B30）：追加文末“缺陷回流第 3 轮”，既有内容未删 |

## 摘要

- **产品代码改动范围**（`git diff --stat -- src .github`，仅修改既有文件）：`26 files changed, 2070 insertions(+), 27 deletions(-)`；另有**新建**文件：`src/deploy/migrations/010_mcp.sql`、`src/ib/mcp/`（16 个 .py）、`src/ib/ledger/mcp_store.py`、`src/ibweb/mcp_views.py`、`src/frontend/src/views/McpServersPage.vue`、`src/frontend/src/utils/`（`mcpLabels.ts`、`externalGrants.ts`）。工作区 `git diff --stat` 全量另含 `docs/`（其他 agent 的文档改动，非本次产物）。无无关文件。
- **五维平均分**（24 个 MOD 自评，见“按模块评审”；算术：正确性 203/24=8.46，安全 215/24=8.96，性能 203/24=8.46，可维护性 191/24=7.96，可测试性 203/24=8.46；总和 1015 ÷ 120 = **8.46**）。
- **问题统计**：CRITICAL 0（已修复 0）/ MAJOR 5（已修复 1，遗留 4）/ MINOR 6（遗留 6）。共 11 条 CR（MAJOR：CR-001、003、005、008、009；其中 CR-005 已 FIXED）。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `src/ib/core/types.py`、`ports.py`、`__init__.py` | MOD-R29-01 / IFC-R29-001、002 |
| `src/ib/mcp/rules.py`、`schema_lite.py`、`__init__.py` | MOD-R29-02 / IFC-R29-010~016 |
| `src/ib/mcp/wire.py` | MOD-R29-03 / IFC-R29-020~024 |
| `src/ib/webtools/netguard.py`、`fetch.py` | MOD-R29-04 / IFC-R29-030、031 |
| `src/ib/tools/__init__.py` | MOD-R29-05 / IFC-R29-040、041 |
| `src/ib/mcp/crypto.py` | MOD-R29-06 / IFC-R29-050~052 |
| `src/ib/ledger/mcp_store.py`、`schema.py`、`src/deploy/migrations/010_mcp.sql` | MOD-R29-07 / IFC-R29-060~065 |
| `src/ib/mcp/transport.py` | MOD-R29-08 / IFC-R29-070 |
| `src/ib/mcp/double.py` | MOD-R29-09 / IFC-R29-080~083 |
| `src/ib/mcp/client.py` | MOD-R29-10 / IFC-R29-090~093 |
| `src/ib/mcp/result.py` | MOD-R29-11 / IFC-R29-100~102 |
| `src/ib/mcp/runtime.py` | MOD-R29-12 / IFC-R29-110~114 |
| `src/ib/mcp/binding.py` | MOD-R29-13 / IFC-R29-120~122 |
| `src/ib/mcp/catalog.py`、`auditing.py` | MOD-R29-14 / IFC-R29-130~133 |
| `src/ib/mcp/admin.py` | MOD-R29-15 / IFC-R29-140~144 |
| `src/ib/mcp/grants.py` | MOD-R29-16 / IFC-R29-160~164 |
| `src/ib/mcp/supervisor.py` | MOD-R29-17 / IFC-R29-170 |
| `src/ib/runtime/compile.py`、`orchestration/dag.py`、`config/definition.py` | MOD-R29-18 / IFC-R29-180~183 |
| `src/ibweb/mcp_views.py`、`urls.py` | MOD-R29-19 / IFC-R29-200~218 |
| `src/ibweb/composition.py`、`views.py`、`config_views.py`、`src/ib/config/__init__.py` | MOD-R29-20 / IFC-R29-219~223 |
| `src/frontend/src/api/client.ts`、`src/utils/mcpLabels.ts` | MOD-R29-21 |
| `src/frontend/src/views/McpServersPage.vue`、`router/index.ts`、`layouts/ConsoleLayout.vue` | MOD-R29-22 |
| `src/frontend/src/components/config/AgentDetailPanel.vue`、`src/utils/externalGrants.ts` | MOD-R29-23 |
| `src/scripts/selfcheck.py`、`.github/workflows/ci.yml`、`src/deploy/env.example`、`checklists.txt`、`src/requirements.txt`、`requirements-offline.txt` | MOD-R29-24 |

外部协议事实一律取自 module_design“领域与外部依赖出处”表（代码文件头/函数文档串中以 `[WEB: …]` / `[CODE: …]` 标注）；表外内容（函数名字符集）保持 `[UNSOURCED]`，见 implementation_plan U1。画像 P11 的 DeepSeek Search/Fetch 与本轮无关，未触及；未调用任何真实端点。

## 自验证结果

环境：项目 venv `/root/.venvs/intelligentbase/bin/python`；`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`。未安装任何依赖。最终一轮（2026-11-05 16:06~16:12，修复 CR-005 之后）结果：

| 命令 | 输出尾部（计数行 / 结论行） | 结论 |
|---|---|---|
| `python -m compileall -q src` | rc=0 | 通过 |
| `python -m pytest tests -q -p no:cacheprovider` | `1358 passed in 60.68s (0:01:00)` | 与基线 1358 一致，**零新增失败** |
| `python src/scripts/selfcheck.py` | `自检结果：76/77 通过` ／ `失败项：- core_framework_free … 引入了第三方顶层包：sitecustomize` | 基线 68/69 + 新增 8 个 MCP 守卫全部 PASS；唯一失败为基线既有 `core_framework_free`（本轮未引入新的第三方包到 `ib.core`） |
| `(cd src/frontend && npm run build)` | `vue-tsc --noEmit && vite build` → `✓ built in 28.54s` | 通过 |
| `(cd src/frontend && npm test)` | `# tests 160 / # pass 160 / # fail 0` | 通过（首轮 159/160，见“现有测试调整”） |
| scratchpad 冒烟 `test_smoke_mcp.py`（Django 测试客户端；**不入库、不算测试**） | `2 passed` | 覆盖登记（stdio/明文 http/元数据地址被拒）、凭证（响应与库内无明文）、启用、发现、租户参数确认、审核、固定入参覆盖 LLM 同名实参、未开放时保存被拒、发布热编译、调用、无作用域拒绝、回合预算 5 次后拒绝且替身请求数不增加、rug-pull 后立即拒绝、审计无凭证、被引用时删除 409、强制删除清理授权、治理/允许名单、viewer 403；禁用路径（`mcp_enabled=False`：写端点 503、catalog 键集与基线相同、healthz 无 `egress_mcp`） |
| scratchpad 回环 HTTP 服务冒烟（`HttpMcpTransport` + `McpClient`，modern 与 legacy） | probe/list/call 成功；3xx ⇒ `address_blocked`；未命中允许名单的明文 http ⇒ `address_blocked` | 通过（真实套接字路径已执行一次） |
| scratchpad 内联驱动 `McpSupervisor.tick()` + `start()/stop()` | 健康探测落库、去抖刷新触发 `needs_rereview` 并通知、start/stop 干净退出 | 通过（监听线程路径除外，见 CR-008） |

**未验证项（如实）**：① 真实 `FernetSecretCipher`/`MultiFernet`（venv 无 `cryptography`；本机 `test_mcp_crypto_fernet_r29.py` 将 SKIP，不得记 PASS；CI 以 `IB_REQUIRE_CRYPTO=1` 强制）；② `subscriptions/listen` 监听线程的真实流（CR-008）；③ 前端真实浏览器交互（仅 `vue-tsc` 严格类型检查 + 构建 + 源码级冒烟）；④ 目标机 CPU 上的 `cryptography` 探针（部署项 `[B30]`）；⑤ 与真实 MCP Server 互通（超出离线范围）。

## 按模块评审

评分口径：正确性 / 安全 / 性能 / 可维护性 / 可测试性，各 0~10；无任何维度 < 6，故无强制 finding。CR 编号见文末问题表。

### MOD-R29-01 核心类型与端口
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

仅追加；`ib.core` 零第三方依赖（selfcheck `core_framework_free` 的失败为基线既有，与本模块无关）。CR：无。

### MOD-R29-02 命名、指纹与 schema 规则
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 10/10 |

纯函数；无异常外泄；schema 校验有深度/节点数/体积上限，忽略 `pattern`。CR：无。

### MOD-R29-03 线协议
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 10/10 |

头值禁 CR/LF；未知 `resultType` 视为无效。`subscriptions/listen` 参数形状与 `MCP-Session-Id` 拼写取自出处表字面（见 implementation_plan A7）。CR：无。

### MOD-R29-04 出网防护扩展
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 9/10 |

默认值 = 现行为（R28 全部用例零新增失败；selfcheck `mcp_ssrf_rejects` 含默认端口白名单回归）；允许名单永不放行“绝不放行集”，含映射内嵌地址与“名单域名重绑”场景。CR：无。

### MOD-R29-05 工具注册表扩展
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

遮蔽防护三道之二（`register` 拒保留前缀、`register_external` 禁覆盖）。CR：无。

### MOD-R29-06 凭证加解密
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 9/10 | 8/10 |

`Secret` repr/str 恒 `***` 且不可 pickle；无 `cryptography` 时 import 成功。真实 Fernet 路径未执行。CR：CR-001。

### MOD-R29-07 台账存储与迁移 010
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 7/10 | 8/10 |

SQL 全参数化；写入 `BEGIN IMMEDIATE`；`read_admission` 单次联结查询无缓存；凭证表无明文列。单文件约 970 行（两后端共用实现）。CR：CR-004、CR-006。

### MOD-R29-08 HTTP 传输
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

每次新建 `UrlGuard` + 钉 IP；3xx 不跟随；日志/异常/repr 无头值。已用回环服务执行一次；无自动化回环用例（留 GROUP_D 的传输契约测试）。CR：无。

### MOD-R29-09 离线替身
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 9/10 | 8/10 | 9/10 |

无网络导入（selfcheck 断言）；`ReversibleTestCipher` 令牌不含明文子串，非离线永不被组合根返回。安全 8：替身可逆，仅靠组合根工厂与 selfcheck 守卫保证不进生产。CR：无。

### MOD-R29-10 MCP 客户端
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 7/10 | 8/10 |

时代探测/回退、legacy 会话 404 重初始化一次、分页与工具数上限；`listen` 仅 modern。CR：CR-008（监听流）。

### MOD-R29-11 结果转换与不可信内容
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

只采纳文本；净化 + 字节截断 + 专用围栏并置换围栏标记；失败短语无状态码/原文/凭证。CR：无。

### MOD-R29-12 运行时
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 7/10 | 8/10 |

11 步固定顺序；永不抛；审计先行失败不发送；回合预算按 `turn_id` 跨 agent 合计（冒烟：5 次后拒绝、替身请求数不增加）。CR：CR-002。

### MOD-R29-13 外部工具注册器
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

闭包签名不含 `scope/retrieval/knowledge`（selfcheck `mcp_callable_signature_guard`）；悬空授权容忍。CR：无。

### MOD-R29-14 目录服务
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

状态迁移集中在存储层事务内（selfcheck `mcp_state_machine` 穷举）；审核对租户参数嫌疑强制确认。CR：CR-007。

### MOD-R29-15 管理服务
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 7/10 | 7/10 | 8/10 |

公网明文 http 纯字符串先判；传输类型/主密钥缺失校验；强制删除“先停用 → 逐项目清理 → 全成功才删除”。`GrantIndex` 每次遍历全部活动项目。CR：CR-003、CR-004、CR-007。

### MOD-R29-16 授权校验与项目视图
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 9/10 |

与调用期共用 `admission_reason`；台账不可读 ⇒ 单条 `mcp_store_unavailable`（fail-closed，仅当存在新增外部授权/参数变更）。CR：无。

### MOD-R29-17 supervisor
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

任何异常只写 WARN/审计；`inline=True` 便于离线驱动；监听线程路径未被自动化覆盖。CR：CR-008。

### MOD-R29-18 编译 / 编排 / 定义校验钩子
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

加成式，默认 `None`；无外部授权时与现行路径逐位相同（全量回归零新增失败）；`IB_MCP_ENABLED=0` 时外部授权视为悬空而不使编译失败。CR：无。

### MOD-R29-19 HTTP 视图与路由
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 7/10 | 7/10 | 7/10 |

写端点先鉴权后解析请求体；`?token=` 由中间件统一 400；错误体不回显凭证；admin 判定与 `_require_admin` 同口径。自评审发现并修复项目侧可枚举他项目凭证行（CR-005）。CR：CR-003、CR-005（FIXED）、CR-010。

### MOD-R29-20 组合根装配
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 7/10 | 8/10 |

主密钥只从 `os.environ` 读取，不进 `GlobalConfig`；`make_secret_cipher` 四分支；发布服务/运行时缓存按调用时解析。`composition.py` 继续增长（+264 行）。CR：CR-010。

### MOD-R29-21 前端 API 客户端与词表
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

HTTP 只经 `client.ts`；无 axios/CDN；词表为纯 TS。CR：无。

### MOD-R29-22 前端管理页与导航
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8/10 | 8/10 | 7/10 | 7/10 |

导航入口（`SYSTEM_ORDER` + 路由 `requiresAdmin`）已接；凭证 `type="password"`、提交即清空、永不回填；传输下拉仅 `streamable_http`。单文件约 690 行；未在真实浏览器中运行。CR：CR-009。

### MOD-R29-23 前端配置页外部工具区
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

纯函数 `externalGrants.ts` 不 import 其他模块（可被 `node:test` 单文件转译加载）；无外部工具且无失效授权时不渲染。CR：无。

### MOD-R29-24 部署 / CI / 自检
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

`selfcheck.py:3924/:3962` 既有断言未改；`checklists.txt` 新增 `[B30]` 并同步签署行（既有 `B28/B29` 签署行断言不受影响）；`env.example` 仅 `<REPLACE_ME_…>` 占位。CR：无。

## CR 问题表

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `src/ib/mcp/crypto.py`（`FernetSecretCipher`） | 真实 Fernet/MultiFernet 路径在本机从未执行（venv 无 `cryptography`，按 ADR-R29-17 方案 C 只验证了端口层与替身）；密钥格式校验、轮换解密、坏令牌异常不含值等行为仅靠代码审阅 | OPEN |
| CR-002 | MINOR | `src/ib/mcp/runtime.py` 步骤② | 回合预算在步骤②先 `reserve`，之后被准入/断路器等拒绝的调用也消耗计数（保守方向，不放宽上限）；Server 级每回合分计在③之后复核 | OPEN |
| CR-003 | MAJOR | `src/ibweb/mcp_views.py`（`_tool_dto`、`tools_endpoint`/`server_endpoint`）；`src/ib/mcp/admin.py`（`GrantIndex.references`） | 列表接口对每个工具各发一次审计查询（N+1，每次 ≤200 行）；引用索引每次遍历全部活动项目（O(P)，设计已估算为十~百量级）。目录规模大时列表接口变慢 | OPEN |
| CR-004 | MINOR | `src/ib/ledger/mcp_store.py`（`update`，CAS 基于 `updated_at`） | 乐观并发用秒级 ISO 时间戳，同一秒内两次更新无法区分（沿用 `utc_now_iso` 精度） | OPEN |
| CR-005 | MAJOR | `src/ibweb/mcp_views.py`（`_server_dto`） | 自评审发现：项目绑定主体读 Server 时，`credential.projects` 会列出其他项目的专属凭证行（泄露他项目标识）。**已修复**：非 admin 仅见本项目条目；冒烟与全量回归复跑通过 | FIXED |
| CR-006 | MINOR | `src/ib/ledger/mcp_store.py`（`Memory*`） | 单独实例化的 `Memory*` 各自独立内存库（只有 `build_mcp_stores(None, backend="memory")` 共享连接）；偏差 D1 已登记，测试需用工厂 | OPEN |
| CR-007 | MINOR | `src/ib/mcp/admin.py`、`catalog.py`、`client.py` | 少量未使用的导入（仓库无 lint 配置，未被工具发现） | OPEN |
| CR-008 | MAJOR | `src/ib/mcp/supervisor.py`（`_sync_listeners`/`_listen_loop`）、`client.py::listen` | 监听线程与 `subscriptions/listen` 流的真实路径无自动化覆盖：`FakeMcpServer` 对该方法返回 `-32601`，且 `tick()` 的 inline 模式不启动监听线程；仅健康探测/复核/去抖/启停被执行验证 | OPEN |
| CR-009 | MAJOR | `src/frontend/src/views/McpServersPage.vue` | 管理页仅通过 `vue-tsc` 严格类型检查与构建，未在真实浏览器中运行，也没有页面逻辑的单元测试（本轮不写测试） | OPEN |
| CR-010 | MINOR | `src/ibweb/config_views.py::_mcp_catalog_keys`、`composition.py::_external_param_specs` | 台账读取失败时静默省略追加键/参数规格（只读路径的降级；保存路径另有 fail-closed 的 `mcp_store_unavailable`），管理员在该窗口看不到失效标注 | OPEN |
| CR-011 | MINOR | `src/ib/mcp/double.py`（`FakeMcpServer.handle`） | 替身对 `x-mcp-header` 镜像只校验“头存在”，不比对值；契约测试需另行断言镜像值 | OPEN |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

遗留 4 条（CR-001、003、008、009），逐条原因与建议处理时机：

| CR | 遗留原因 | 建议处理时机 |
|---|---|---|
| CR-001 | 项目约束不允许子代理安装依赖；设计已选方案 C（端口 + 替身 + CI 必跑真实依赖） | GROUP_D 写入 `test_mcp_crypto_fernet_r29.py`；**CI 首次运行**以 `IB_REQUIRE_CRYPTO=1` 强制执行；用户在开发机执行 tech_stack 的安装命令后本机可复核 |
| CR-003 | 设计已接受 O(P) 遍历（项目数十~百量级）；缓存会引入新的一致性窗口，违背“管理动作后下一次读取即可见” | 若目录/项目规模增长到数百以上，GROUP_B/E 评估按请求缓存或聚合审计查询；本轮不改 |
| CR-008 | 替身不支持流式订阅，补替身属测试夹具工作（GROUP_D 职责）；监听只是变更感知的四途径之一，其故障不影响调用路径（ADR-R29-04 第 6 点） | GROUP_D 在回环线程服务上补监听用例；部署后以 `[B30]` 与日志核对 |
| CR-009 | 无浏览器环境；本轮范围不含前端单元测试 | GROUP_D 前端冒烟追加（导航入口/词表/外部授权纯函数）；上线后用户在 UI 复核（登记→验证→启用→审核→开放→授权） |

## 缺陷修复

非缺陷修复模式（无 `<defects>`）。不适用。

## 现有测试调整

仅 1 处。v0.2.0 按 GR-C-001（retry 1/2）修正：上一轮的可选组 `(, 'mcp')?` 属弱化，已撤销并改为严格匹配新契约；授权来源 `REWORK_AUTHORIZED: src/frontend/tests/advisor_r28.test.js`（仅 :260 附近这一条断言）。

| 文件:行 | 原断言 | 调整 | 原因 |
|---|---|---|---|
| `src/frontend/tests/advisor_r28.test.js:260-261`（TC-FE-R28-023） | `/const SYSTEM_ORDER = \['accounts', 'projects', 'llm-key', 'web-governance'\];/` | 严格改为 `/const SYSTEM_ORDER = \['accounts', 'projects', 'llm-key', 'web-governance', 'mcp'\];/`（无可选组、无宽松正则），注释为“REV-29 MOD-R29-22 契约变更；授权 GR-C-001 REWORK_AUTHORIZED”；其后 `order.slice(0,3)` 的既有三项相对顺序断言原样未动 | module_design MOD-R29-22 明确要求 `SYSTEM_ORDER` 末尾追加 `'mcp'`（新管理页必须有导航入口，画像 P6），契约由四项变为五项。ConsoleLayout.vue:59 实际为五项字面，严格断言通过；去掉 'mcp' 则会失败 |

返工后复跑 `(cd src/frontend && npm run build && npm test)`：`# tests 160 / # suites 26 / # pass 160 / # fail 0`。产品代码与 .py 未改动，故未重跑 pytest / selfcheck（沿用 1358 passed；selfcheck 基线不变）。

其余既有测试（pytest 1358、selfcheck `:3924` / `:3962`）**零改动**。

## 缺陷修复轮（GR-D-001，缺陷回流第 1 轮；文档 1.1.0 DRAFT）

### 缺陷修复（DEF-ID → 修改位置 → 根因）

| DEF | 修改位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-R29-004 | `src/ib/mcp/runtime.py` `_call` ⑥ | 构造入参只做“剔除 hidden/fixed 键”的黑名单，未做白名单；LLM 自加的未声明键原样外发（AC-027-04 / REQ-NFUNC-009） | 白名单 = 已审核 `input_schema.properties` 键，且不属于 `hidden ∪ fixed`；之后 `update(fixed_args)`；其后的 `max_arg_bytes` 与 `validate_args` 仍照常执行 |
| DEF-R29-003 | `src/ib/mcp/client.py` `McpTarget` / `list_tools` / `listen`；`src/ib/mcp/catalog.py` `_target`；`src/ib/mcp/supervisor.py` `stop` | ① 已知时代分支把 `list_changed` 写死 False，refresh 的 `record_probe(negotiated=...)` 覆盖验证期协商值 ⇒ 监听从不启动；② `stop()` 只置 Event，阻塞在安静 SSE 流上的读取不检查 Event，流也未被关闭 ⇒ 线程残留 | ① `McpTarget` 增可选字段（默认 False，位置在末尾，全部既有调用点不变）并由 `catalog._target` 带入台账值；② `listen()` 的关闭小线程在 stop 置位时 `resp.close()`，`supervisor.stop()` 带超时 join 监听线程 |
| DEF-R29-002 | `src/ib/mcp/result.py` `render_result`；`src/ib/mcp/client.py` `call_tool` | ① `sanitize(max_chars=limit)` 先按字符截断，ASCII 下已压到上限，随后字节截断判定“未超限”⇒ 静默截短、无标注；② 读取上限仅 `max_bytes+64KB`，100 KB 文本被判 `response_too_large` | ① 净化不截断，统一字节截断 + 标注，并为标注预留字节；② 读取上限放宽到 `max(4×max_bytes, max_bytes+64KB)` |
| DEF-R29-005 | `src/ib/orchestration/dag.py` `_advisor_node` | 顾问节点走独立分支，未进入 `mcp_turn_scope`，调用恒 `no_turn_scope` | 与非顾问分支同判定进入外部回合作用域；`ExitStack` 叠加在既有 `turn_scope` 之内，预算语义不变 |

### 共享判定函数 / 调用方副作用评估（P-PM-001）

| 被改符号 | 全部调用方 | 评估 |
|---|---|---|
| `McpTarget`（新增末位默认字段） | `catalog.py`（2 处，其中 `_target` 已改）、`supervisor.py`（2 处，位置参数 6 项）、`runtime.py:456`（关键字）、测试夹具 | 默认值 False，旧调用点语义不变；仅 `_target` 路径（verify 之后的 refresh）获得协商值。supervisor 的监听 target 不用该字段 |
| `render_result` | 仅 `runtime.py` ⑪；单测 `test_mcp_rules_r29.py`（256/264/284 等）全部仍通过 | 不再字符截断：中文超限由字节截断承担，`test_mcp_rules` 的 120000 字节用例仍通过；标注预留字节只在 `truncated` 时触发 |
| `call_tool` 读取上限 | 仅 `runtime._call` 经 `max_bytes` 传入 | 内存仍有界（≤ 4×结果上限，默认 128 KB）；`response_too_large` 仍对更大响应生效 |
| `McpSupervisor.stop` | `Deps.close()`、测试 | 最坏多等 `timeout_s`（默认 2 s）；`_inline` 模式无监听线程，无影响 |
| `_advisor_node` | 仅 `make_agent` 顾问分支 | 无 `mcp__` 工具或 `mcp_turn_scope is None` ⇒ `nullcontext`，与现状逐位相同（REV-28 顾问全量回归通过） |

### 新问题自评审

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-012 | MINOR | `client.py` `listen()` | 每次监听多一个轮询小线程（0.2 s 间隔，流结束即退出）；与 supervisor 既有 watcher 功能重叠，后续可合并 | OPEN |
| CR-013 | MINOR | `runtime.py` ⑥ | 被白名单丢弃的键名未写审计（指令“可记入”）；如需可观测，后续追加审计字段 | OPEN |
| CR-008 | MAJOR | `supervisor.stop` / `client.listen` | 线程残留问题已修复；真实传输下 `resp.close()` 打断阻塞读取未在真实 socket 上验证（见 A12） | FIXED（离线）；真实路径未验证 |

五维（本轮改动范围）：正确性 9 / 安全 9 / 性能 8 / 可维护性 8 / 可测试性 8。

### 自验证结果（本轮）

- `$P -m compileall -q src` → 无输出，通过。
- `$P -m pytest tests -q -p no:cacheprovider` → `7 failed, 1707 passed, 6 skipped in 85.61s`；7 个失败**恰为**上述预期翻转的缺陷冻结用例（列表见 implementation_plan“预期翻转的缺陷冻结用例”），基线 1714 passed = 1707 + 7；无其他新增失败。
- `$P src/scripts/selfcheck.py` → `自检结果：76/77 通过`；唯一失败 `core_framework_free`（既有，`sitecustomize`），8 个 mcp_* 守卫均 PASS。
- `(cd src/frontend && npm test)` → `# tests 180 / # pass 180 / # fail 0`（前端未改，仅确认）。
- 未验证：真实 socket 上监听流被关闭后的读取行为；真实 MCP Server 互通。

### 现有测试调整

无（本轮未改任何测试文件；7 个冻结用例交 test-engineer 翻转）。

## 缺陷修复轮 2（GR-D-002，缺陷回流第 2 轮；文档 2.1.0 DRAFT）

### 缺陷修复（DEF-ID → 修改位置 → 根因）

| DEF | 修改位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-R29-007 | `src/ib/mcp/transport.py` `_chunks`（原 :129） | `HTTPResponse.read(N)` 在真实 socket 上循环读到凑满 N 字节或 EOF，约 70 字节的 list_changed 事件滞留；离线替身整块投递掩盖了问题 | 改为 `read1(_BLOCK)`（一次底层读取，有多少返回多少；chunked 返回当前块内已到达的部分）；`settimeout` 改用留底的 `sock`，期限语义不变，`socket.timeout`→`timeout`、其余→`unreachable` 的映射保留 |
| DEF-R29-006 | `src/ib/mcp/transport.py` `post`（原 :139 `close=conn.close`） | close-delimited 响应时 `getresponse()` 已把 `conn.sock` 置 None 并把 fd 交给响应的 makefile，`conn.close()` 无事可做；chunked 时 fd 仍被 makefile 引用，close 不真正关 fd；二者都无法唤醒另一线程阻塞的 recv | 新 `_close()`：先对 `endheaders` 后留底的 `sock` 执行 `shutdown(SHUT_RDWR)`（忽略 OSError）唤醒读取，再 `resp.close()`、`conn.close()`（各自吞异常，幂等）。`_chunks` 的异常映射追加 `ValueError/AttributeError`：首次实现后实测关闭与读取线程存在竞态（`'NoneType' object has no attribute 'close'` 泄漏到 `listen` 的 errors），现统一映射为 `unreachable`，`listen` 在 stop 已置位时吞掉 |

### 共享符号 / 调用方副作用评估（P-PM-001）

`HttpMcpTransport.post` 的返回对象 `McpHttpResponse.chunks` / `.close` 被所有调用方共用。grep 结果（`src/ib/mcp`）：`client.py` 仅 5 处消费 `resp.chunks`（:140 错误体读取、:148 排空、:167 SSE 读取、:177 JSON 读取、:449 listen）与 2 处 `resp.close()`（`_exchange` 的 finally、`listen` 的 `_closer` 与 finally）；`supervisor.py` / `catalog.py` / `runtime.py` 不直接接触 chunks/close（均经 `McpClient`）；`double.py` 的替身自带 `chunks=iter(...)`、`close=lambda: None`，不经本文件。

| 调用方 | read1 的影响 | shutdown/_close 的影响 |
|---|---|---|
| `_exchange` 错误体（:140）、排空（:148） | 块变小但累计到 `_ERR_BODY_MAX` 的逻辑按累计长度，无影响；排空仅取首块即 break，read1 更快返回 | 读取已完成后才 close；此时 fd 多已关闭，`shutdown` 抛 OSError 被忽略；`resp.close`/`conn.close` 幂等 |
| `_read_outcome` JSON（:177）、SSE（:167） | 按块累计 `len(buf) > max_bytes`、`iter_sse_events` 逐块拼接，不依赖块大小；块更碎只多几次循环，内存上限不变 | 同上；SSE 读到匹配 id 即返回后 finally 关闭：shutdown 对仍存活的流会主动 RST/FIN 对端（此前依赖 conn.close，行为等价于提前断开，符合“读完即弃”） |
| `listen`（:449） | 事件即时投递（修复目标） | stop 后 `_closer` 线程调用 `_close()`，监听线程在约 0.1 s 内因 EOF 正常结束或因竞态异常被映射为 `unreachable` 且被吞 |
| `initialize / list_tools / call_tool / probe` | 均经 `_exchange`，同上 | 同上 |

HTTPS：`ssl.SSLSocket.shutdown` 同样可用，OSError/SSLError 均被忽略；本轮仅回环明文验证，HTTPS 路径**未验证**。

自验证期间既有传输契约测试 `tests/integration/test_mcp_http_transport_r29.py` 全部通过（与 realsocket 文件同批连跑 3 次：`4 failed, 20 passed`，4 个失败恰为冻结用例）。

### 新问题自评审

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-014 | MINOR | `transport.py` `_chunks` | 关闭/读取竞态靠捕获 `AttributeError`/`ValueError` 兜底，而非加锁；语义安全（stop 已置位时被吞，否则映射 `unreachable`）但略显粗；后续可在 `_close` 与读取间加显式状态位 | OPEN |
| CR-008 | MAJOR | `supervisor.stop` / `client.listen` | 真实 socket（回环明文）上 stop 后线程约 0.1 s 退出，客户端断开已由服务端观察到；HTTPS 路径未验证 | FIXED（回环明文）；HTTPS 未验证 |

五维（本轮改动范围）：正确性 9 / 安全 9 / 性能 9 / 可维护性 8 / 可测试性 8。

### 自验证结果（本轮）

- `$P -m compileall -q src` → 无输出（exit 0）。
- scratchpad 复现脚本（不入库）：stop 后线程 alive=False、服务端 client_gone=True、errors=[]（close-delimited 与 chunked，重复 5 轮）；list_changed 在流仍开着 1 s 内 `changed == [1]`。
- `$P -m pytest tests -q -p no:cacheprovider` → `4 failed, 1714 passed, 6 skipped in 92.01s`；4 个失败恰为 `test_mcp_listen_realsocket_r29.py` 的 720/721 × (close-delimited, chunked) 冻结守卫串（预期翻转）；基线 1718 passed = 1714 + 4；无其他新增失败。
- `$P -m pytest tests/integration/test_mcp_listen_realsocket_r29.py tests/integration/test_mcp_http_transport_r29.py -q` 连跑 3 次 → 每次 `4 failed, 20 passed`（稳定，失败项同上）。
- `$P src/scripts/selfcheck.py` → `自检结果：76/77 通过`；唯一失败 `core_framework_free`（既有，`sitecustomize`）。
- 前端未改，未重跑（沿用 180/180）。
- 未验证：HTTPS 路径的 shutdown/read1；真实 MCP Server 互通。

### 现有测试调整

无（本轮未改任何测试文件；720/721 的 4 个收集项交 test-engineer 翻转为期望口径）。

## 缺陷回流第 3 轮（DEF-R29-008、B30；文档 3.1.0 DRAFT）

### 缺陷修复（DEF-ID → 修改位置 → 根因）

| DEF | 修改位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-R29-008 | `src/ibweb/composition.py` `_assemble` 末尾（原 :1631-1633）；`build_application`；新增 `start_mcp_supervisor` | `_assemble` 是 ib-web 与 ib-worker 共用的装配体（worker.py `_setup_django` → `django.setup` → `apps.ready` → `build_deps`），把“启动后台线程”这一进程级副作用放在共用装配体内，违反“supervisor 仅在 ib-web 进程内”（module_design.md:866） | 启动点移到仅 ib-web 经过的 `build_application`（wsgi.py 调用）；`_assemble` 不再启动；`close()` 的停止逻辑不变 |
| （交付物，CP-002 Q5=A / GR-E1-001-F02） | `src/deploy/checklists.txt` `[B30]` | 清单与 SKILL.md §5.2 / deployment_plan 不一致：前端写 `npm ci && npm run build`；env 读取缺 `sudo`；venv 命令未写绝对路径 | 见 implementation_plan 第 3 轮 G4；[B30] 以外未动；无凭据 |

### 本轮五维与问题

| 维度 | Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|---|
| 评分 | 9/10 | 9/10 | 10/10 | 9/10 | 8/10 |

五维平均 = (9+9+10+9+8)/5 = 9.0。

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-015 | MINOR | `composition.py` `build_application` | `manage.py runserver` 不再（亦不应）启动 supervisor，开发联调需经 wsgi 路径；已在计划 A14 登记取舍 | OPEN |
| CR-016 | MINOR | tests（未改） | worker 不启动 / web 启动的成对用例尚缺，交 test-engineer；当前仅有一次性命令演示 | OPEN |

统计（本轮新增）：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 2。DEF-R29-008（MAJOR）本身 FIXED。全文累计 MAJOR 遗留数不因本轮增加（CR-001/003/009 等沿用既有逐条原因，见“遗留 MAJOR”）。

### 自验证结果（本轮，gate_mode=baseline）

- `/root/.venvs/intelligentbase/bin/python -m compileall -q src` → 无输出（exit 0）。
- 一次性演示（scratchpad 脚本，不入库；非离线真实装配 + 持久化 SQLite 台账）：
  ```
  supervisor object present: True
  [worker path] threads after build_deps: []
  [web path] threads after build_application: ['ib-mcp-supervisor']
  [idempotent] threads: ['ib-mcp-supervisor']
  [after close] threads: []
  ```
- `$P -m pytest tests -q -p no:cacheprovider` → `1718 passed, 6 skipped in 91.03s`（与基线一致，零新增失败；6 skip = Fernet 契约，cryptography 未装）。
- `$P src/scripts/selfcheck.py` → `自检结果：76/77 通过`；唯一失败 `core_framework_free`（既有，`sitecustomize`）。
- 前端未改，未重跑（沿用 180/180）。
- 未验证：目标机真实进程（ib-web / ib-worker）线程情况；`checklists.txt` 仅文本改动，已由全量 pytest/selfcheck（含 `deploy_templates_have_no_secrets`）通过。

### 现有测试调整

无（本轮未改任何测试文件）。
