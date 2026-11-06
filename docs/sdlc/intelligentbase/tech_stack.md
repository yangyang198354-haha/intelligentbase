<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-05T15:16:29+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/archive/rev28/tech_stack.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（REV-29 增量）— agent 工具调用的 MCP 适配

## 修订记录

| 版本 | 时间 | 说明 |
|---|---|---|
| 0.1.0 | 2026-11-05T11:15:36+08:00 | REV-29 设计草案（基线 HEAD b4fa3a3；REV-28 版本归档于 `archive/rev28/tech_stack.md`，完整基线栈见画像 P1 与该归档）。依赖 OQ-R29-01=B 的确认；未确认前不得进入开发 |
| 1.1.0 | 2026-11-05T15:16:29+08:00 | 定向修订（invocation intelligentbase-R29-GROUP_B-002，`REWORK_AUTHORIZED`，其余逐字保留，不改代码）：落地 CP-001（原话「全部按照推荐」，经主会话转述）——OQ-R29-01 已确认（Q1=B，"未确认前不得进入开发"限制解除）；Q5=A：A-R29-1 已确认（画像 P8"凭据入库"= 不得提交进 git）；**A-R29-3 核实闭合并订正表述**：pdfminer.six 区间两端（`20231228` 与区间内最新 `20251230`）均硬依赖 `cryptography>=36.0.0`，"已是传递依赖"**仅对生产 venv 成立**，开发 venv 与离线清单均无（PM 核验 2026-11-05），故对它们 `cryptography` 是真正新增；补 `cryptography` 的 wheel 可用性（42.0.0 / 50.0.2 均有 `cp39-abi3` manylinux x86_64，覆盖 Python 3.11–3.13）；新增「离线测试覆盖凭证加解密」选型（ADR-R29-17）与「开发机安装指引（用户执行）」；风险表：HITL / stdio 条目改为"已移出"，新增 R-11；新增信息项 OBS-R29-1（pdfminer.six advisory） |

**结论**：本轮**唯一新增的显式依赖声明是 `cryptography>=42,<51`**（用于凭证加密落盘；它对**生产 venv** 已是**传递依赖**——`pdfminer.six` 的硬依赖，区间两端已核实；对**开发 venv 与 `requirements-offline.txt`** 则是真正新增，开发 venv 现状未装，PM 核验 2026-11-05）。**不引入官方 MCP SDK**（ADR-R29-03），**不新增 HTTP 客户端库**（沿用 stdlib `http.client` + 既有钉 IP 连接），**不新增运行单元、不新增容器、不新增前端依赖**。MCP 协议客户端自写（同步、约 600~800 行 `[ESTIMATE]`），入参 schema 校验自写有界子集。
**出处纪律**：MCP 为公开协议，规范事实标 `[WEB: URL，2026-11-05]`；`mcp` / `cryptography` / `pdfminer.six` 的版本与依赖来自 PyPI JSON（`cryptography` 与 `pdfminer.six` 在 1.1.0 按具体版本重取）；`ToolAnnotations` 字段名与默认值来自官方规范 schema 页；仓库内事实以依赖清单 `文件:行` 为准，不用网页覆盖。

## 技术选型表

| 类别 | 选型 | 版本（出处；查不到写"未知"） | 新增 / 沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | `>=3.11,<3.14`；CI 用 3.12（画像 P1；`.github/workflows/ci.yml:63`） | 沿用 | 无变化；`ipaddress.is_global` 在 3.11~3.13 间有边界修订，拒绝网段继续由项目显式列出（`netguard.py:124-144`） | REQ-NFUNC-004 | 低 |
| Web 框架 | Django + DRF + waitress（`--threads=8`） | `Django>=5.0,<6.1`（`src/requirements.txt:14`）；`djangorestframework>=3.15,<4.0`（`:15`）；`waitress>=3.0,<4.0`（`:16`）；threads（`src/deploy/systemd/ib-web.service:52`） | 沿用 | 新端点族 `/api/mcp/*` 沿用手写视图风格与 `_require_admin`（`views.py:1740`）；外部调用占用请求线程，用并发闸限制 | REQ-FUNC-001~007/011/012 | 中：见 R-1 |
| 编排 | LangGraph + langchain-core | `langgraph>=0.2,<2.0`（`:23`）；`langchain-core>=0.3,<2.0`（`:24`） | 沿用 | 外部工具只是普通 agent 工具；`run_dag` 对所有运行生成 `turn_id`（一行语义变化）；沿用 ADR-57 层归一化，不依赖未核实特性 | REQ-FUNC-016/020 | 低：改动经真实 langgraph 契约测试 `tests/integration/test_mcp_compile_hotpath_r29.py` |
| LLM 客户端 | langchain-openai（DeepSeek） | `langchain-openai>=0.2,<0.3`（`:25`；画像 P8：`>=0.3` 禁用） | 沿用 | 工具循环 `bind_tools` / `tool_calls` 不变（`llm/__init__.py:545-609`）；外部工具名须落在函数名字符集内（ADR-R29-02，A-R29-2 待探针） | REQ-FUNC-010/019 | 中：函数名字符集资料未载明 |
| 数据存储 | SQLite WAL 台账 | 画像 P1 | 沿用 + **新增 9 张表**（迁移 `010_mcp.sql`） | 平台级 admin-only 数据放台账（ADR-R29-07）；与 `llm_key` / `web_governance` 同机制；迁移与 `schema.py` 单源 | REQ-FUNC-001/003~007/011~015/021，REQ-NFUNC-008 | 低：可逆（DROP，标 `[MANUAL_ROLLBACK_REQUIRED]`）；审计表增长见 R-8 |
| 会话 / 预算 / 断路器存储 | 进程内（contextvars + TTL 登记簿 + 内存断路器） | 同 R28 `TurnBudget` 手法（`gate.py:53-141`） | 沿用风格 | P8 禁 Redis 用于实时推送；无外部状态的新故障面 | REQ-NFUNC-006/007 | 低：重启丢失断路器状态（默认可接受）；Gunicorn 多 worker 不共享 |
| MCP 客户端 | **自写最小同步客户端** `ib.mcp.client` + 传输 `ib.mcp.transport`（stdlib `http.client` / `ssl` / `socket`） | 随 Python（无独立版本）；支持的协议修订 `2026-07-28`（modern）、`2025-11-25`（legacy）`[WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning.md，2026-11-05]` | **新增（项目内代码，无第三方包）** | 同步 WSGI 友好；可复用钉已校验 IP 的连接层（`fetch.py:127-145`），官方 SDK 经 `httpx2` 发请求无法注入该防护；零新增传递依赖（ADR-R29-03） | REQ-FUNC-002/008/010/019，REQ-NFUNC-004/011/012 | 高：随规范演进需自跟（R-2） |
| 备选（未采纳）：官方 Python SDK | `mcp` | 最新 2.3.0，MIT，`requires_python>=3.10`，`requires_dist` 含 `httpx2>=2.10.0`、`mcp-types==2.3.0`、`pydantic>=2.12.0`、`starlette`、`sse-starlette>=3.0.0`、`uvicorn>=0.31.1`、`pyjwt[crypto]>=2.10.1`、`jsonschema>=4.20.0`、`opentelemetry-api>=1.28.0`、`python-multipart`、`anyio>=4.9`；1.x 最新 1.30.0（2026-09-07）`[WEB: https://pypi.org/pypi/mcp/json，2026-11-05]`；是否同时支持两个协议时代：**未知** | 不采纳 | asyncio 为主；HTTP 层不可注入钉 IP；传递依赖体量大且 pydantic 下界较高（与现有 venv 的解析冲突未做试验 `[ESTIMATE]`） | — | — |
| JSON Schema 校验 | **自写有界子集** `ib.mcp.schema_lite` | 无 | 新增（项目内代码） | 规范要求 MUST NOT 自动解引用网络 `$ref`、组合关键字须有资源上限 `[WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/index.md，2026-11-05]`；自有遍历器最易审计；只作预检，权威校验在 Server 侧 | REQ-FUNC-019，REQ-NFUNC-011 | 中：方言差异（备选 `jsonschema>=4.20,<5`，其下界取自上述 SDK 元数据） |
| 凭证加密 | **`cryptography`（Fernet / MultiFernet）**，**延迟导入** | **声明 `cryptography>=42,<51`**。出处（1.1.0 按版本重取）：`42.0.0` 有 `cp39-abi3` manylinux x86_64 wheel（`manylinux_2_17` / `manylinux_2_28`），`requires_python>=3.7`，`requires_dist` 含 `cffi>=1.12`（非 PyPy）`[WEB: https://pypi.org/pypi/cryptography/42.0.0/json，2026-11-05]`；当前最新 `50.0.2` 有 `cp39-abi3` 与 `cp311-abi3` manylinux x86_64 wheel，`requires_python !=3.9.0,!=3.9.1,>=3.9`，`requires_dist` 含 `cffi>=2.0.0`（非 PyPy）、`typing-extensions>=4.13.2`（Python<3.11），许可 `Apache-2.0 OR BSD-3-Clause` `[WEB: https://pypi.org/pypi/cryptography/50.0.2/json，2026-11-05]`。结论：区间两端在 Python 3.11–3.13（x86_64 manylinux）均有预编译 abi3 wheel，无需本机编译。下界 42 是项目的保守选择（Fernet 为长期稳定 API），**未做逐版 CVE 核查（未知）**。现状：`pdfminer.six>=20231228,<20260101`（`src/requirements.txt:30`）区间两端均硬依赖 `cryptography>=36.0.0` `[WEB: https://pypi.org/pypi/pdfminer.six/20231228/json；https://pypi.org/pypi/pdfminer.six/20251230/json，2026-11-05]`（区间内其余版本未逐个取数）；开发 venv 未装（PM 核验 2026-11-05） | **新增显式声明**（对生产 venv 已是传递依赖；对开发 venv / 离线清单是真正新增） | 标准库无对称加密原语，自实现密码学被排除；认证加密（Fernet）满足"不明文落盘"（REQ-NFUNC-005）；主密钥与库分离；延迟导入使无该包的环境仍可 `import ib.mcp`（ADR-R29-17） | REQ-FUNC-006，REQ-NFUNC-005 | 中：目标老 CPU 上 import + 加解密探针 `[TBD-R29-1]`（M-SA-009）；上界 `<51` 须随主版本复核；生产 venv 已装版本是否 ≥42 未知（`pip install -r` 会按区间升级，部署前 `pip show cryptography`） |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + vue-router（hash） | `vue ^3.4.0`（`package.json:19`）、`element-plus ^2.8.0`（`:18`）、`typescript ^5.4.0`（`:25`） | 沿用 | 新页面 / 纯 TS 模块沿用现有结构；HTTP 只经 `client.ts`（无 axios，P6/P8）；凭证输入框 `type="password"` 提交即清空 | REQ-FUNC-001~007/011/012/016 | 低 |
| 测试 | pytest（后端）、Node 内置 `node:test`（前端） | `"test": "node --test"`（`package.json:14`）；CI 见 `ci.yml` | 沿用 | 离线替身：`FakeMcpServer` / `FakeMcpTransport` / `FakeResolver`（`ib.mcp.double`，可编排畸形、恶意、变更、慢响应、不可达、modern / legacy 两个时代）；传输契约测试对 `HttpMcpTransport`（回环线程服务）与 Fake 同跑；**自动化测试不连真实 MCP Server / 互联网**（C-R29-04），`monkeypatch socket.create_connection` 零外联断言；真实 Server 兼容性为目标机人工项。**凭证加解密的离线覆盖（ADR-R29-17，a+b 兼顾）**：端口层用例对 `ReversibleTestCipher` / `UnconfiguredSecretCipher` 在开发机必跑；真实 Fernet 契约测试 `tests/unit/test_mcp_crypto_fernet_r29.py` 用 `pytest.importorskip("cryptography")`，开发机未装则 skip 并记账，CI（装有真实依赖）在 `IB_REQUIRE_CRYPTO=1` 下**不得 skip**（缺包即失败） | REQ-NFUNC-001，REQ-NFUNC-005，C-R29-04 | 中：替身的行为取自规范示例，真实 Server 的方言差异只能人工发现；开发机默认不跑 Fernet 契约（R-11） |
| 进程管理 / 容器化 | systemd；**无容器**（P8） | 画像 P7 | 沿用 | 不新增运行单元；supervisor 为 ib-web 进程内 daemon 线程 | C-R29-03，REQ-NFUNC-012 | 无 |
| CI/CD | GitHub Actions `ci.yml`（10 阶段） | 画像 P7 | 沿用 + 追加检查 | 迁移检查追加 010；selfcheck 新增 8 个用例；offline 清单追加 `cryptography`（安装步骤 `ci.yml:73-74` 自动覆盖）；作业级 `env`（`ci.yml:46-52`）追加 `IB_REQUIRE_CRYPTO: "1"` | REQ-NFUNC-001，REQ-NFUNC-005 | 低 |
| 部署方式 | 目标机 `git pull` + `sudo -n systemctl restart ib-web`；前端本地构建 | 画像 P7 | 沿用 | 仅 ib-web 与前端受影响；env / unit / nginx 变更由用户执行 | — | 需用户编辑 `/etc/intelligentbase/ib-web.env`（仅键名） |
| 密钥管理 | 主密钥 `IB_MCP_SECRET_KEY`（`ib-web.env`，0600，用户编辑）；凭证密文在台账 `mcp_credentials` | 位置：`/etc/intelligentbase/ib-web.env`；值不入库 / 不入文档 / 不回显 | 新增（键名） | REQ-NFUNC-005；与 LLM Key（台账明文，`006_llm_key.sql`）不同——后者不满足本需求，不沿用；"加密存台账 + 主密钥在 `ib-web.env`"已获用户确认（CP-001 Q5=A，A-R29-1 关闭） | REQ-FUNC-006 | 中：丢失即凭证不可恢复（R-5） |
| 新增依赖汇总 | **`cryptography>=42,<51`（显式声明，写入 `src/requirements.txt` 与 `src/requirements-offline.txt` 各一行）**；无其他 Python 包、无新前端包；`requirements-embed.txt` 不动；`requirements.txt:30` 的 `pdfminer.six` 行不动 | 见上 | — | — | — | — |

## 许可证与维护登记（新增 / 变更依赖）

| 依赖 | 许可证 | 维护状态 | 备注 |
|---|---|---|---|
| cryptography 50.0.2（当前最新；声明区间 `>=42,<51`） | Apache-2.0 OR BSD-3-Clause（[WEB: https://pypi.org/pypi/cryptography/json，2026-11-05]；`license_expression` 字段） | 活跃（主版本快速迭代，故上界取当前主版本 +1，每轮发布前复核） | 非 copyleft，与项目许可策略兼容；wheel 为 manylinux 预编译（abi3；含 Rust / `cffi`；Python 3.11–3.13 x86_64 均有，见上），**未在目标老 CPU 上验证**（`[TBD-R29-1]`；因 `pdfminer.six` 已将其带入生产 venv 且 `pypdf` / `pdfminer` 路径在运行，风险低但不等于已验证）；传递依赖 `cffi`（42.0.0：`>=1.12`；50.0.2：`>=2.0.0`），`typing-extensions`（仅 Python<3.11，不适用） |
| pdfminer.six（既有，仅用于说明传递关系） | MIT（[WEB: https://pypi.org/pypi/pdfminer.six/json，2026-11-05]；`20231228` 的 license 字段为 `MIT/X`） | 既有依赖，本轮不改；`20231228` 的 `requires_python>=3.6`、`20251230` 的 `requires_python>=3.10`；PyPI 元数据对 `20231228` 列出两条 advisory（见 OBS-R29-1） | 区间两端 `requires_dist` 均含 `cryptography>=36.0.0`（硬依赖，非 extra）`[WEB: https://pypi.org/pypi/pdfminer.six/20231228/json；https://pypi.org/pypi/pdfminer.six/20251230/json，2026-11-05]`；其约束宽于本轮声明（`>=42`），不冲突；`20260107` 在 pin 区间外 |
| mcp（官方 SDK，**未采纳**，仅作比较） | MIT（[WEB: https://pypi.org/pypi/mcp/json，2026-11-05]） | 活跃（2.x 与 1.x 并行发布） | 若将来改用，须新增 `McpClient` 实现并逐项重验 SSRF 钉 IP；不影响本稿的端口划分 |
| MCP 协议规范（非软件包） | 规范站点开放文档（许可未核对） | 规范在演进：2026-07-28 修订为无状态模型，2025-11-25 及更早为会话式（[WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning.md，2026-11-05]） | 本稿支持 `{2026-07-28, 2025-11-25}`，其余版本 ⇒ "协议不兼容" |

画像 P8 核对：`cryptography` 不在禁用项；未引入 torch / transformers / FlagEmbedding / onnx / PyMuPDF / `langchain-openai>=0.3` / axios / CDN；无 Docker；`ib.*` 未 import `ib_embed`；无多实例 ib-worker；nginx 与 SSE 条件未触及；未使用 Channels / Redis。画像 P6：Python 依赖下界 + 上界都写（`cryptography>=42,<51`）；三份清单分工不变（`requirements-embed.txt` 不动；`requirements.txt` 与 `requirements-offline.txt` 各加一行）。
关于画像 P8 条目"凭据入库"：按"不得把凭据提交进 git 仓库"理解，台账内**加密**凭证不在此列——**用户已确认**（CP-001 Q5=A，2026-11-05，经主会话转述；A-R29-1 关闭）。

## 开发机安装指引（由用户执行；子代理不得自行安装，画像 P4）

| 项 | 内容 |
|---|---|
| 现状（PM 核验 2026-11-05） | 开发 venv `/root/.venvs/intelligentbase`（Python 3.12.3，pytest 9.1.1）**未安装** `cryptography`，也未安装 `pdfminer.six`；`requirements-offline.txt` 不含二者。系统 python3 带 Debian 版 cryptography 41.0.7，**不属项目环境**且低于 `>=42` 下界，不得依赖。基线：pytest 1358 passed，selfcheck 68/69（`core_framework_free` 既有失败） |
| 安装命令（二选一） | ① `/root/.venvs/intelligentbase/bin/python -m pip install "cryptography>=42,<51"`；② 待开发把 `cryptography>=42,<51` 写入 `src/requirements-offline.txt` 后，在仓库根执行 `python -m pip install -r src/requirements-offline.txt pytest pytest-cov`（即画像 P4 环境准备命令）。Windows / PowerShell 用户：在已激活的项目虚拟环境中执行同一条 `python -m pip …`。**无需**安装 `pdfminer.six`（生产备路径解析器，离线清单刻意不含） |
| 确认命令 | `python -c "import cryptography; print(cryptography.__version__)"`，版本应落在 `>=42,<51`（不涉及任何密钥） |
| 未安装时的行为 | `import ib.mcp.*` 仍成功（延迟导入）；端口层测试（`ReversibleTestCipher` / `UnconfiguredSecretCipher`）照跑；`tests/unit/test_mcp_crypto_fernet_r29.py` skip，报告须写明"cryptography 未安装"，**不得标 PASS**；selfcheck `mcp_no_plaintext_secret` 输出 `cipher=test` 记账 |
| CI | `requirements-offline.txt` 含该依赖，runner 自动安装；`IB_REQUIRE_CRYPTO=1` 使 Fernet 契约测试不得 skip |
| 目标机（生产） | 不在本指引内：部署前由用户 / devops 核对 `pip show cryptography`（版本区间）与 import + 一次加解密探针（`[TBD-R29-1]`），写入 `src/deploy/checklists.txt` |

## 技术风险

### High
- **R-1 外部调用占用请求线程**（`waitress --threads=8`，`ib-web.service:52`）：单次外部调用最坏占用一个线程至超时（默认 30 秒）。缓解 = 全局在途并发闸（默认 3 ≈ 请求线程 3/8，沿用 R28 A-6）+ Server 级并发闸（非阻塞，拿不到即 `busy` 降级，M-SA-006）+ 断路器 open 期间零网络等待 + 每用户回合调用上限 + `BoundTool.timeout_s` 看门狗 + 传输层 deadline；`[TBD-R29-4]` 目标机压测校准各默认值。
- **R-2 自写协议客户端随规范演进**：规范刚由会话式切到无状态（2026-07-28），后续修订可能再变。缓解 = 方法集只含 4 类消息；支持集合显式常量；`McpClient` 经端口隔离，可替换为 SDK 实现；契约测试夹具逐字取自规范示例；规范修订时先加探测测试再扩支持集合（ADR-R29-04）。
- **R-3 rug-pull 检测窗口**：Server 在两次检测之间更换工具内容，调用路径无法逐次比对指纹（协议无调用时携带清单版本的机制）。缓解 = 监听（modern，可选）+ 低频复核（默认 300 秒）+ 手动刷新 + 重连；调用前用**已审核** schema 预检；`side_effect` / `unknown` 工具默认拒绝；`needs_rereview` 即刻不可调用。残余风险写入验收：窗口 ≤ 复核周期。
- **R-4 SSRF 与内网允许名单**：允许名单内主机被入侵可成为内网跳板；DNS 重绑可把允许名单域名指向元数据地址。缓解 = "绝不放行集"（链路本地 / 元数据 / 保留段永不放行）+ 精确 `host:port` + 每次请求重解析并钉 IP + 重定向一律不跟随 + ≥30 条拒绝用例 + 运维出站 ACL 作第二道防线（用户执行）。

### Medium
- **R-5 凭证主密钥运维**：主密钥丢失 ⇒ 已存凭证不可恢复（需重录）；主密钥与库文件同机存放，同机被攻破则两者皆失（威胁模型：防止库文件 / 备份单独泄露，不防 root）。SQLite 删除行后页内残留属已知局限（`VACUUM` 可选，由运维决定）。缓解 = 主密钥只在 `ib-web.env`（0600）；`IB_MCP_SECRET_KEY_PREVIOUS` 支持轮换；检查清单明确"备份主密钥与库文件分开保管"。
- **R-6 回合预算需引擎小改**：`run_dag` 对所有运行生成 `turn_id`、`make_agent` 注入回合作用域。缓解 = 默认 `nullcontext`、仅含外部工具的节点进入；既有 `test_langgraph_contract_r26` 与 R28 顾问用例零新增失败；OQ-ARCH-R29-04 可退为"每 agent 运行"粒度（零引擎改动）。
- **R-7 compile 路径新增台账依赖**：registrar 读台账失败会使含外部授权的项目编译失败。缓解 = fail-closed 且可见（`apply_failed`，旧快照保留并退避）；不含外部授权的项目不调用 registrar。
- **R-8 `mcp_audit` 无限增长**：无清理任务（OQ-ARCH-R29-10）。缓解 = 索引覆盖查询维度；每次调用一行（开始写 + 结束回填各一次写事务，`[ESTIMATE]` 亚毫秒，目标机待测）；后续按增长评估归档策略。
- **R-9 函数名字符集假设**：LLM 端点是否接受 `mcp__<server>__<tool>`（A-R29-2）未载明。缓解 = 名称规则落在 OpenAI 兼容通例内且不含点；目标机契约探针 `[TBD-R29-2]`；探针失败时仅需调整 `local_tool_name`（单点函数）。
- **R-11 开发机缺 `cryptography`，真实 Fernet 契约测试只在 CI 真跑**（1.1.0 新增）：开发 venv 未装（PM 核验 2026-11-05），开发期间本地看不到 Fernet 实现的回归。缓解 = 延迟导入保证其余测试不受影响；端口层覆盖业务语义；`IB_REQUIRE_CRYPTO=1` 使 CI 缺包即失败；用户安装后本地亦可跑（见「开发机安装指引」）；替身与真实实现共享端口契约用例的公共部分以防漂移。
- **R-10 间接提示注入的残余**：外部工具返回内容可诱导同一 agent 调用其**已被授权**的其他工具。缓解 = 结构隔离（无委托通路）+ 围栏净化 + 回合调用上限 + 默认拒绝有副作用 / 未知风险工具 + 固定入参；不宣称根除。

### Low
- **目标机性能未实测**：延迟增量、并发闸与探测池大小均标 `[TBD-R29-3/4]`，校准前验收标"未验收"（记忆 M-SA-008）。
- **监听线程占用**：最多 4 个 daemon 线程 + 长连接；可由 `listener_max=0` 关闭，退化为轮询 + 手动刷新。
- **HITL 已移出**：本轮不做（CP-001 Q2=A，OQ-R29-05=A，OOS-R29-12），以默认拒绝 + 显式放行兜底（REQ-FUNC-021）；未来增量工作量 L（ADR-R29-12 第 5 点）。
- **stdio 已移出**：本轮不做（CP-001 Q2=A，OQ-R29-02=A，OOS-R29-11；ADR-R29-13 Rejected / Deferred）；若日后要做，隔离需新增专用 systemd 单元（须回架构评审）且 `mcp_servers.transport` 的 `CHECK` 需新迁移重建表。
- **OBS-R29-1（信息项，非本轮范围）**：PyPI 元数据对 `pdfminer.six 20231228` 列出两条 advisory（GHSA-wf5f-4jwr-ppcp / CVE-2025-64512 修复于 20251107；GHSA-f83h-ghpp-7wcc / CVE-2025-70559 修复于 20251230；均为加载 CMap 的不安全 pickle 反序列化）`[WEB: https://pypi.org/pypi/pdfminer.six/20231228/json，2026-11-05]`；现 pin `>=20231228,<20260101`（`src/requirements.txt:30`）允许装到受影响版本，实际装到哪版未知。建议另案评估把下界提到 `20251230`；本轮不改。
