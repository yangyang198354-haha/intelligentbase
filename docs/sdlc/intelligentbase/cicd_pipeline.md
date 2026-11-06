<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-06T21:38:01+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/e2e_test_report.md</file>
    <file>docs/sdlc/intelligentbase/integration_test_report.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：REV-29 agent 工具调用的 MCP 适配（INCREMENTAL）

> REV-28 已批准版本归档于 `archive/rev28/cicd_pipeline.md`（只读）；本文按 REV-29 整体重写（`REWORK_AUTHORIZED`），沿用其阶段结构。
> **修订记录 1.1.0（2026-11-06，缺陷回流第 3 轮后；`REWORK_AUTHORIZED`，用户经 CP-002 授权"全部按推荐"，经主会话转述）**：① 关闭 OI-5（DEF-R29-008 已修复并验证：GR-C-006、GR-D-004；supervisor 只由 `build_application` 启动）；② 关闭 OI-1 / OI-2（`checklists.txt [B30]` 已由 software-developer 修复，本组逐行核对）；OI-3 保留；新增 OI-7（GR-C-006-F03：`[B30](2)` 的 `pip install -r` 口径）；③ CI 预期数字按回流后实测更新（本机 `1761 passed, 6 skipped`，收集 1767；CI 带 `IB_REQUIRE_CRYPTO=1` 预期 `1767 passed, 0 skipped` `[INFERRED]`）；④ 部署后验证新增 MV-10（见 deployment_plan V-13）。**历史陈述保留**：1.0.0 的 OI-1 / OI-2 / OI-5 原文以"已关闭"条目形式留在末节表中，数字 1718 / 1724 仅出现在"历史基线"行。
> 本组**未连接任何环境、未 ssh、未部署、未 commit / push**（画像 P9）。**本组不修改任何 CI / 部署交付物**：`ci.yml`、`checklists.txt`、`env.example`、requirements、systemd 均由 GROUP_C 在本轮改好，本组只核对（核对结论见末节「待修正项 / 开放问题」）。

## 现状与影响

### 现有 CI

| 项 | 内容 |
|---|---|
| 文件 | `.github/workflows/ci.yml`，触发：push / PR 到 `main`、`workflow_dispatch` |
| 运行环境 | `ubuntu-24.04`，Python 3.12，Node 22，`timeout-minutes: 30`，job 级 `permissions: contents: read` |
| 阶段 | 10 阶段、单 job、fail-fast：Source → Config(compileall)+Schema 门(003/007/008/009，**本轮 +010**) → Unit → Integration → E2E → Full+coverage → selfcheck → Version gate → Frontend build+test → Package artifact |
| 部署 | **CI 不含 CD**：生产部署由 E2 按 `.claude/skills/ib-prod-deploy/SKILL.md` 授权执行（画像 P7） |

### 本增量对 CI 的影响（逐项核对，来源 `git diff HEAD -- .github/workflows/ci.yml src/requirements*.txt` 与 module_design「对 selfcheck / CI 门的影响」）

当前工作区**未提交**（HEAD `b4fa3a3`；`git diff HEAD` 涉及 `src` / `.github` 26 个已修改文件，`src tests .github` 未跟踪新文件 40 个），**CI 尚未跑过本轮代码**。

| 影响维度 | 结论 | 依据 |
|---|---|---|
| 新迁移 | **有**：`010_mcp.sql`（9 张新表 + 4 索引）→ Schema 门追加 010 检查（**GROUP_C 已改 ci.yml**，`git diff --stat`：+33/-0） | ci.yml 迁移检查 R29 块 |
| **新依赖** | Python：`cryptography>=42,<51` 写入 `src/requirements.txt` 与 `src/requirements-offline.txt`（各 +1 行）。CI 的 `pip install -r src/requirements-offline.txt pytest pytest-cov`（ci.yml:76）自动覆盖，**安装步骤无需改**。npm：`package.json` / `package-lock.json` 无改动（`git diff --stat` 为空） | git diff |
| **新环境变量（CI job 级）** | `IB_REQUIRE_CRYPTO: "1"`（ci.yml:54，GROUP_C 已加，ADR-R29-17 方案 C）：`tests/unit/test_mcp_crypto_fernet_r29.py` 内守卫用例在该变量为 1 且 `cryptography` 不可导入时**失败而非 skip** | architecture_design 测试分层 3；ci.yml 头注释 |
| 新测试层 | **无**。新测试落在既有层：`tests/unit/*mcp*_r29.py`、`tests/integration/*mcp*_r29.py`（含真实回环 socket 用例与 `mcp_r29_baseline_golden.json`）、`tests/e2e/test_mcp_e2e_r29.py`、`src/frontend/tests/mcp_r29.test.js`；`tests/mcp_r29_support.py` 为共用辅助（非测试文件）；被既有 step 自动纳入 | 目录收集 / `node --test` |
| selfcheck | 新增 8 个 MCP 守卫（`mcp_schema_single_source`、`mcp_egress_single_exit`、`mcp_namespace_guard`、`mcp_no_plaintext_secret`、`mcp_fake_rejected_in_production` 等）；PIPE-07 step 不改 | implementation_plan |
| 新服务 / 新环境 | CI 侧**无**：离线（`IB_OFFLINE_MODE=1`），MCP 用 `FakeMcpServer`/`FakeMcpTransport`/`ReversibleTestCipher` 替身，不连真实 MCP Server / 互联网；不新增 staging，不引入 Docker（画像 P8） | module_design 兼容性论证；C-R29-04 |
| 版本门 / 硬门 | 不改（`cryptography` 不在任何版本门内；无 fitz / 容器文件） | module_design |
| **结论** | **`ci.yml` 已含全部需要的改动**（作业级 `IB_REQUIRE_CRYPTO` + 010 迁移门）；本组无新增改动请求 | PM 要求本组不改 |

### 合并 / 部署前置门：IB_REQUIRE_CRYPTO=1 的 Fernet 契约（GR-D-003 条件 4）

- **为何是门**：开发机 venv 未装 `cryptography`，本机 `tests/unit/test_mcp_crypto_fernet_r29.py` 的 **6 个用例 SKIP**（unit_test_report / e2e_test_report：回流第 3 轮后全量 `1761 passed, 6 skipped`；回流前为 1718 / 6）。**本机 6 SKIP 不代表通过**；真实 `FernetSecretCipher` / `MultiFernet` 路径（往返、旧钥解密、坏令牌、密文不含明文）只有 CI 才会真跑。
- **CI 上的判定标准（缺一不可，PRE-00 逐项核对）**：
  1. 待部署提交的 CI 运行 `completed / success`（10 阶段全绿）；
  2. PIPE-03（Unit）日志中 `test_mcp_crypto_fernet_r29.py` 的用例**为 passed、无 skipped**：全量汇总行期望 **`1767 passed`、`0 skipped`**（本机 1761 passed + 6 skipped；两者之和 1767 = 全量收集数 = 单元 1097 + 集成 578 + E2E 77 + tests/agents 15，6 条 SKIP 在 CI 上应转为 PASS；此为 `[INFERRED]`，首次 push 后以 CI 实际为准）；出现任何 `skipped` 且指向该文件 → **不得合并 / 部署**，视同红灯；
  3. `IB_REQUIRE_CRYPTO: "1"` 确在该运行的 job env 中生效（ci.yml:54；查看运行日志的 env 段或 ci.yml 在待部署提交上的内容）。
- **首次运行**即带该变量，无"先宽后紧"过渡期：缺包即失败。若首次运行因 `cryptography` 缺失 / Fernet 契约失败而红灯 → 回 GROUP_C 修复，不得改 ci.yml 去掉变量或标 skip 绕过。

### 新测试在 CI 的落点与基线

基线 = 回流第 3 轮后本机实测（GROUP_D-005，未提交工作区，开发机；E2E 层 77 passed 无变化）。

| 范围 | 阶段 | 基线（PM 复跑 / GROUP_D，未提交工作区，开发机） | CI 预期 |
|---|---|---|---|
| 单元 | PIPE-03 | `1091 passed, 6 skipped`（收集 1097） | `1097 passed, 0 skipped` `[INFERRED]` |
| 集成 | PIPE-04 | `578 passed`（含 TC-INT-R29-720/721 真实回环 socket、TC-INT-R29-1100~1105 进程入口成对用例） | 同 |
| E2E | PIPE-05 | `77 passed` | 同 |
| 全量 + tests/agents | PIPE-06 | `1761 passed, 6 skipped`（收集 1767 = 1097 + 578 + 77 + 15；历史基线：回流前 1718 / 6 / 收集 1724，REV-28 为 1358 passed） | `1767 passed, 0 skipped` `[INFERRED]` |
| selfcheck | PIPE-07 | `76/77`，唯一 FAIL `core_framework_free`（开发机 `sitecustomize` 环境性既有） | `77/77` `[INFERRED]`（runner 无该 sitecustomize；REV-28 起同理，以 CI 为准） |
| 前端 | PIPE-09 | `# tests 180 / pass 180 / fail 0`（`npm run build` 本轮未由 GROUP_D 重跑；以 CI 为准） | build rc=0 且 180/180 |

### 部署提交的 CI 状态（E2 前置条件）

本轮代码**未提交 / 未 push**。把「**提交并推送到 `main`，CI 在待部署提交上全绿且满足上节 3 条判定**」列为 **E2 的前置条件**（deployment_plan PRE-00）；红灯、仍在运行或未触发均不得部署。`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`，仅取证便利，GitHub Actions 网页核对等价；无法核对 → 标"未验证"并请用户确认，不得默认通过。

## 流水线概览

```
[Source] → [Config: compileall + Schema/迁移门(003/007/008/009/010)] → [Unit(含 Fernet 契约, IB_REQUIRE_CRYPTO=1)] → [Integration] → [E2E]
        → [Full+coverage(含 tests/agents)] → [Selfcheck] → [Version gate] → [Frontend build+test] → [Package artifact]
        ⇢（CI 之外，E2 授权后）[Deploy production: recreate — 用户置主密钥 → pull → 依赖/导入/Fernet 探针 → 重启 ib-web(迁移 010) → 前端发布] → [部署后验证 V-01~V-13] → [人工验证 MV-01~10 分阶段]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 `main`；`workflow_dispatch` | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | Config + Schema 迁移门 | PIPE-01 成功 | `python -m compileall -q src`；内联迁移检查（003 / 007 / 008 / 009 / **010**） | 退出码 0；**五**行 `PASS:`（含 `PASS: 010_mcp.sql …`） | abort-and-notify |
| PIPE-03 | Unit（**Fernet 契约门**） | PIPE-02 成功；job env `IB_REQUIRE_CRYPTO=1` | `python -m pytest tests/unit -q` | 退出码 0；零新增失败；`test_mcp_crypto_fernet_r29.py` 全部 passed、**无 skipped**（缺 `cryptography` 则守卫用例失败） | abort-and-notify；**不得**以 skip / 去变量绕过 |
| PIPE-04 | Integration | PIPE-03 成功 | `python -m pytest tests/integration -q` | 退出码 0 | abort-and-notify |
| PIPE-05 | E2E | PIPE-04 成功 | `python -m pytest tests/e2e -q` | 退出码 0 | abort-and-notify |
| PIPE-06 | Full suite + coverage | PIPE-05 成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 退出码 0；预期 `1767 passed, 0 skipped` `[INFERRED]`；覆盖率仅记录不设门（画像 P5） | abort-and-notify |
| PIPE-07 | Offline selfcheck | PIPE-06 成功 | `python src/scripts/selfcheck.py` | 退出码 0（任一 FAIL 非零）；预期 runner 上 77/77（含 8 个 MCP 守卫） | abort-and-notify；不得跳过 |
| PIPE-08 | Version gate | PIPE-07 成功 | ci.yml 阶段 8 内联命令（本轮未改） | bcrypt、langchain-core、langchain-openai pin、无 PyMuPDF、无 Dockerfile、Python 范围全 PASS | abort-and-notify |
| PIPE-09 | Frontend build + test | PIPE-08 成功 | `npm ci && npm run build && npm test`（`src/frontend`，Node 22；CI runner 为全新检出，`npm ci` 适用——**仅目标机禁用**，见制品管理） | vue-tsc 零错、vite build 成功、node:test 全过（基线 180/180） | abort-and-notify |
| PIPE-10 | Package artifact | PIPE-09 成功 | `git rev-parse HEAD > HEAD`；`actions/upload-artifact@v4` | artifact `ib-<sha>-<run_id>` 上传，保留 30 天 | abort-and-notify |

失败处理仅 abort-and-notify（fail-fast，无 `continue-on-error`），**禁止"跳过失败继续部署"**。CD 不在 CI 内：部署经 E2 ssh 到 production（`git pull --ff-only` + 目标机依赖核对 + 重启 ib-web + 前端目标机构建发布），部署前置 = 待部署提交的 CI 全绿且 Fernet 契约真实执行（上节）。

## 环境矩阵

| 配置项 | dev/local | CI | production |
|---|---|---|---|
| 存在 | 是 | 是 | 是（单台物理机；**无 staging**，画像 P7） |
| 实例数 | 离线测试进程 | 1 个 runner | ib-web ×1、ib-worker ×1（禁多实例，画像 P8）、ib-embed ×1、qdrant ×1。**REV-29 只重启 ib-web**（module_design「受影响的运行单元」；SKILL.md §6）；ib-worker 不重启，ib-embed / qdrant / nginx 不动 |
| 资源 | 开发机；`cryptography` **未装**（用户安装，子代理不得 pip install） | ubuntu-24.04，30 min 超时；`cryptography` 由 requirements-offline 安装 | i7-3770S 4C/8T、11 GiB、CPU-only；ib-web `MemoryMax=1024M`；supervisor 为 **仅 ib-web** 进程内 daemon 线程（含 2 线程探测池 + ≤`listener_max` 监听线程；DEF-R29-008 已修复：由 `build_application` 启动，ib-worker 路径不启动），部署后记录 `MemoryCurrent` 与线程数观察 |
| 外部依赖 | 无（离线） | 无（离线替身；**不连真实 MCP Server**） | Qdrant、ib-embed、DeepSeek（LLM，既有）；**新增**：每个已登记 MCP Server 的 `host:port`（出站 ACL 由用户配置；缺省**无任何 Server**，不出网） |
| 配置来源 | `tests/conftest.py` setdefault | ci.yml job 级 `env`（**新增 `IB_REQUIRE_CRYPTO=1`**） | `/etc/intelligentbase/ib-web.env`（0600，只由用户读写，不回显）；**新增键** `IB_MCP_SECRET_KEY`（**必须由用户生成并写入**，否则登记 bearer/header 型 Server 被拒）、可选 `IB_MCP_ENABLED`（缺省 1）/ `IB_MCP_SECRET_KEY_PREVIOUS` / `IB_MCP_CA_BUNDLE` / `IB_MCP_TRANSPORT`（缺省 http） |
| 部署需用户确认 | 否 | 否 | **是**（`PRODUCTION_DEPLOY_CONFIRM=true` + 环境名 `production`） |

## 制品管理

- **CI 制品**：frontend `dist/` + `HEAD` 作为 Actions artifact，命名 `ib-${{ github.sha }}-${{ github.run_id }}`（含提交号），保留 30 天；仅供追溯。
- **生产不使用该制品**：目标机 `git pull --ff-only` 后**本地构建**前端（`npm run build`，不 `npm ci`；`checklists.txt [B30](3)` 已同口径）并拷贝到 web root；Python 无构建产物（源码直跑 venv）。风险：目标机（node 22 / npm 9）与 CI 的 npm 版本不同，产物 hash 可能与 CI dist 不一致；缓解：`&&` 链使构建失败发生在替换 web root 之前，部署前保留 web root 副本（deployment_plan DEPLOY-004 / ROLLBACK-004）。
- **晋升条件**：待部署提交已在 `origin/main` 且其 CI 运行 `completed / success` 并满足 Fernet 契约判定；无 staging，无环境间晋升。

## 待修正项 / 开放问题（本组只记录，不改交付物）

| # | 项 | 说明 | 建议责任方 |
|---|---|---|---|
| OI-1 | **已关闭（1.1.0）**。1.0.0 记录：`checklists.txt` B30(3) 写"前端目标机本地 `npm ci && npm run build`"，与 SKILL.md §5.2 / 画像 P7 不一致 | 复核：`checklists.txt:639` 现为"前端 lock 未变时目标机本地只 `npm run build` 后拷贝，不 `npm ci`——node_modules 属目标机本地状态，SKILL.md §5.2"，与 deployment_plan DEPLOY-005 一致 | 已由 software-developer 修复（GR-C-006） |
| OI-2 | **已关闭（1.1.0）**。1.0.0 记录：B30(2) 的 `grep -c` / `awk` 读 env 未写 `sudo`；`pip show` / `python -c` 未写 venv 路径 | 复核：`checklists.txt:632-635` 现为 `/opt/intelligentbase/venv/bin/pip show`、`/opt/intelligentbase/venv/bin/python -c`、`sudo grep -c` / `sudo awk`，与 PRE-03 / PRE-07 / DEPLOY-001 一致 | 同上 |
| OI-3 | `checklists.txt` B30(5) 回滚核对写"先在新版本中'强制清理授权'或手工移除 `mcp__` 授权"（**仍成立，保留**） | deployment_plan 的 ROLLBACK-000 采用，并给出只读核验脚本；两者方向一致，无冲突，仅措辞粒度不同 | — |
| OI-4 | CI 无显式"打印 skipped 数"的步骤 | Fernet 契约被 skip 只会在缺包且 `IB_REQUIRE_CRYPTO` 未生效时发生；ci.yml 已设该变量，缺包即失败。PRE-00 仍要求人工核对 CI 日志无 skipped（上节判定 2） | 可选：后续在 pytest 命令加 `-rs` 便于核对 |
| OI-5 | **已关闭（1.1.0）**。1.0.0 记录：ib-worker 经 `django.setup()` → `apps.ready()` → `build_deps()` 可能同样启动 supervisor | 已修复并验证：`src/ibweb/composition.py:881-895` `build_application`（仅 `wsgi.py:33` 的模块级 `application = build_application(build_deps())` 调用）在 :895 显式 `start_mcp_supervisor(get_deps(required=False))`（定义 :1640）；`composition.py:1636-1637` 注释说明 `_assemble` / `_install_config_runtime` **不再**启动 supervisor；ib-worker 路径（`worker._setup_django()` → `apps.ready()` → `build_deps`）0 个 `ib-mcp*` 线程（TC-INT-R29-1100 / 1102 PASS），ib-web 路径恰好 1 个（TC-INT-R29-1101 PASS；1103~1105 覆盖幂等、离线、`IB_MCP_ENABLED=0`）。证据：GR-C-006、GR-D-004、integration_test_report「边界 5」。`src/ibweb/worker.py`、`apps.py`、`wsgi.py` 相对 HEAD 无 diff（`git diff HEAD --stat` 为空）。**残留**：自动化未起真实进程 → 部署后以 MV-10 / V-13 在目标机补验（deployment_plan） | 无需处置 |
| OI-6 | 关于 `docs/deployment_plan.md`（REV-21 基线）与 `deployment_report.md` | 本组均未改（`deployment_report.md` 含用户 REV-28 未提交改动，保持原样） | — |
| OI-7 | **新增（GR-C-006-F03）**：`checklists.txt [B30](2)`（:632）仍写"先 `/opt/intelligentbase/venv/bin/pip install -r src/requirements.txt`" | **口径以 deployment_plan PRE-03 为准**：requirements 仅 `cryptography` 一行变更，生产 venv 已有（pdfminer.six 传递依赖）→ **先核对**（`pip show` / 探针），不满足区间时才由**用户**在 sudo 会话中安装，代理不安装依赖。`pip install -r` 会按区间升级 venv，触碰画像 P7 的本地状态（`/opt/intelligentbase/venv`），不宜作为默认第一步 | 交付物待下轮同步：software-developer 将 `[B30](2)` 改为"先核对，不满足时由用户升级"。**本组不改 checklists**（PM 指令） |

## `[INFERRED]` 与待确认

- CI 预期数字（`1767 passed, 0 skipped`、单元 `1097 passed`、selfcheck `77/77`）为由本机实测推算（本机 `1761 passed, 6 skipped`、收集 1767、selfcheck `76/77`、前端 `180/180`），**非 CI 实测**；首次 push 后以 CI 实际为准。
- 本组仅做只读核对（git diff / grep），未运行 pytest / 前端 build；所有测试数字取自 e2e_test_report、unit_test_report、integration_test_report（回流第 3 轮，GROUP_D-005 / PM 复跑）。
- `[TOOL_UNREGISTERED]`：`gh`（仅取证便利，网页核对等价）。
