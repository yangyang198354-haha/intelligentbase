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
    <file>docs/sdlc/intelligentbase/cicd_pipeline.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：REV-29 agent 工具调用的 MCP 适配（INCREMENTAL，仅计划）

> **本文件不执行任何步骤。** 本组未 ssh、未部署、未 commit / push、未读取生产；GROUP_E2 未授权。下列命令是将来 E2 获得 `PRODUCTION_DEPLOY_CONFIRM=true`（环境名 `production`）后才可执行的**计划内容**；子代理模式下 PM 不发部署授权。
> REV-28 版本归档于 `archive/rev28/deployment_plan.md`（只读）；本文按 REV-29 整体重写，沿用其执行约定（引号规则 Q1~Q7）、CLASS 门、回滚结构。`docs/deployment_plan.md`（REV-21 基线）与 `deployment_report.md`（含用户 REV-28 未提交改动）**未改**。
> **修订记录 1.1.0（2026-11-06，缺陷回流第 3 轮后；`REWORK_AUTHORIZED`，用户经 CP-002 授权"全部按推荐"，经主会话转述）**：① **关闭 OI-5**（DEF-R29-008 已修复并验证，GR-C-006 / GR-D-004：supervisor 只由 `build_application`（仅 `wsgi.py` 调用）启动，ib-worker 路径不启动，TC-INT-R29-1100~1105 PASS）；DEPLOY-006 重新裁决，**仍不执行**（理由见 DEPLOY-006）；② 部署后验证**新增 V-13 = MV-10**（只读线程核对），并**更正一处不可行口径**：CPython ≤ 3.13 不把线程名写入 `/proc/<pid>/task/*/comm`（本机 Python 3.12.3 实测：命名线程的 comm 仍为 `python3`），故不能靠 comm 匹配 `ib-mcp-supervisor`，改用"线程数差分 + comm（仅 Python ≥ 3.14 有效）+ 可选 py-spy"；③ 关闭 OI-1 / OI-2（`checklists.txt [B30]` 已修，逐行核对），新增 OI-7（GR-C-006-F03，`[B30](2)` 的 `pip install -r` 口径以 PRE-03 为准，待下轮同步，**本组不改 checklists**）；OI-3 保留；④ CI / 测试数字按回流后实测更新（本机 `1761 passed, 6 skipped`，收集 1767；CI 预期 `1767 passed, 0 skipped` `[INFERRED]`）；⑤ MV 范围 MV-01~09 → MV-01~10。**历史陈述保留**：1.0.0 的 1718 / 1724 数字仅出现在"历史基线"括注中。
> 依据：画像 P7/P8/P9、`.claude/skills/ib-prod-deploy/SKILL.md`（§1–§9；主机、用户、密钥名只引用其 §1–§2，本文不重复）、`module_design.md`「数据迁移」「受影响的运行单元」「对 selfcheck / CI 门的影响」、`implementation_plan.md`、`e2e_test_report.md`「人工验证清单」MV-01~10、`src/deploy/migrations/010_mcp.sql`、`src/deploy/env.example`、`src/deploy/checklists.txt` `[B30]`、`src/deploy/systemd/ib-web.service`。
> 测试门控：GROUP_D 已通过（GR-D-003 / GR-D-004 均 PASS_WITH_CONDITIONS，条件已落入本计划）：未提交工作区 `pytest tests` `1761 passed, 6 skipped`，收集 1767 = 单元 1097 + 集成 578 + E2E 77 + tests/agents 15（6 SKIP = Fernet 契约，开发机缺 `cryptography`；历史基线：回流前 1718 / 6 / 1724）；selfcheck `76/77`（唯一 FAIL `core_framework_free` 环境性既有）；前端 `180/180`；critical path 23/23。

## 给 PM 的部署计划摘要（供将来向用户请求 E2 授权）

| 项 | 内容 |
|---|---|
| 目标环境 | `production`（单台物理机，SSH 密钥，见 SKILL.md §1–§2；画像 P7"部署需用户确认=是"）。无 staging。**当前未授权。** |
| 待部署提交 | `DEPLOY_COMMIT` = **待定**：本轮代码仍在未提交工作区（HEAD `b4fa3a3`；26 个已修改 + 40 个未跟踪的 `src`/`tests`/`.github` 文件）。须先由主会话在用户确认后 commit + push（含全部新文件，尤其 `010_mcp.sql`、`src/ib/mcp/`、`src/ib/ledger/mcp_store.py`、`src/ibweb/mcp_views.py`、`src/frontend/src/views/McpServersPage.vue`、`src/frontend/src/utils/`），**CI 全绿且 Fernet 契约真实执行（IB_REQUIRE_CRYPTO=1，无 skipped，见 cicd_pipeline）后**，由 PM 在授权时写入 40 位哈希 |
| 策略 | **recreate**（画像唯一允许）：重启 ib-web（约 10–30 秒不可用 `[INFERRED]`，丢内存态聊天会话）；前端静态发布无停机。**首发无任何已登记 MCP Server**：新路径全部不触发，行为 = REV-28（module_design 兼容性论证 #1~#12） |
| 步骤数 | 预检 PRE-00~08（含用户执行项 U）；**部署 5**：DEPLOY-001（用户写入 `IB_MCP_SECRET_KEY`）→ 002 git pull → 003 依赖/导入/Fernet 探针（只读闸）→ 004 重启 ib-web（迁移 010 自动应用）→ 005 前端构建发布；**不执行**：DEPLOY-006 重启 ib-worker（module_design 结论 + SKILL.md §6 逐项核对：不需重启；OI-5 已关闭，见 DEPLOY-006）；部署后验证 V-01~V-13（V-13 = MV-10）；**可选后续**：DEPLOY-007（私有 CA）；回滚 ROLLBACK-000（用户前置）/001/002a/002b/004/005/007/008 |
| 重启范围 | 按 SKILL.md §6：`src/ib/**`、`src/ibweb/**`、迁移 010、env 新键 → **ib-web 重启**；`src/frontend/**` → 不重启，目标机 `npm run build` 后拷 web root；`src/deploy/**` 本轮只有 `migrations/010`、`env.example`、`checklists.txt`（仓库文件，不被服务读取）→ 无 unit / nginx 变更，**无 `daemon-reload`、无 `nginx reload`**；requirements 变更仅 `cryptography` 一行 → 目标机核对而非安装（生产 venv 已有，pdfminer.six 传递依赖）。ib-worker / ib-embed / qdrant / nginx：**不重启** |
| 迁移 | 010 `mcp_*` 9 张新表 + 4 索引（纯新表，`IF NOT EXISTS` 幂等），随 `ib-web` 重启的 `ExecStartPre=… -m ibweb.bootstrap --ensure-schema` 自动应用；**回滚 = 备份后按依赖逆序 `DROP` 9 张表，`[MANUAL_ROLLBACK_REQUIRED]`**（ROLLBACK-007，含回滚前数据处置）；代码回退后留表无害，通常不需要 DROP |
| 生产当前版本 | **未知，不得假定**（REV-28 部署记录 DEPLOY_COMMIT 为 `b4fa3a3…`，仅作 PRE-02 祖先门的参照，不作为目标机状态假设）。PRE-01 必须在目标机实测 `git rev-parse HEAD` 作为**回滚锚点 `ANCHOR`** |
| 不变面 | `/etc/intelligentbase/ib-worker.env`、`ib-embed.env`（不动）；`ib-web.env` 仅**追加一键** `IB_MCP_SECRET_KEY`（用户执行，不读取不回显，其余键不动）；systemd unit、nginx；`/var/lib/intelligentbase/` 现有数据（除 010 新增表外只读）；`package.json` / `package-lock.json`（故不 `npm ci`；`checklists.txt [B30](3)` 已同口径，cicd_pipeline OI-1 已关闭）；qdrant；bge-m3 权重；`/opt/intelligentbase/venv`（只核对，不改）；目标机前端 `node_modules` |
| 不可逆 / 需人工 | 迁移 010 撤销（ROLLBACK-007）；**主密钥丢失 / 删除 ⇒ 已存凭证密文永久不可恢复**（需重录）；Stage 2 中向真实 MCP Server 的调用与登记数据（审计只增不删，外部系统效应不可撤回）；ROLLBACK-000（回滚代码前须先清除项目的 `mcp__` 授权，否则旧代码 `tool_grant_tool_unknown`） |
| 需要用户（非代理）执行 | ① 待部署提交 commit + push（主会话经用户确认）；② PRE-05 台账迁移前备份；③ PRE-06 只读核查；④ PRE-07 env 键存在性计数；⑤ **DEPLOY-001 生成并写入 `IB_MCP_SECRET_KEY`**（GR-D-003 条件 2）；⑥ PRE-03 `cryptography` 不满足时的升级；⑦ 为 Stage 2 的真实 MCP Server 配置出站 ACL；⑧ 浏览器人工验证 MV-01~03 与 Stage 2 的真实 Server 操作；⑨ 一切需 sudo 口令的动作（Q5）。`daemon-reload` / unit 安装 / `nginx reload`：本轮均不需要 |
| 前提（E2 授权时由 PM 填入 `special_instructions`） | `PRODUCTION_DEPLOY_CONFIRM=true`；环境名 `production`；`DEPLOY_COMMIT=<40 位>`；计划版本 = phase_status 登记的 APPROVED 版本；`INCLUDE_WORKER_RESTART` 缺省 false 且本轮不授权；用户已口头确认 DEPLOY-001 完成（主密钥已写入） |

## 变更摘要

| 组件 | 文件（以 `git diff --name-only HEAD` / 未跟踪清单为准） | 迁移 | 构建 | 需重启 / 发布的运行单元 |
|---|---|---|---|---|
| 核心类型 / 端口 / 出网防护 / 工具注册 | `src/ib/core/{types,ports,__init__}.py`、`src/ib/webtools/{netguard,fetch}.py`、`src/ib/tools/__init__.py` | 无 | 无 | ib-web 重启 |
| MCP 适配核心（新） | `src/ib/mcp/`（16 个文件：`transport`、`client`、`crypto`、`supervisor`、`admin`、`runtime` 等）、`src/ib/ledger/mcp_store.py` | 无 | 无 | ib-web 重启（supervisor 为 ib-web 进程内 daemon 线程） |
| 编排 / 配置 / 运行时 | `src/ib/runtime/compile.py`、`src/ib/orchestration/dag.py`、`src/ib/config/{definition,__init__}.py` | 无 | 无 | ib-web 重启 |
| 台账 | `src/ib/ledger/schema.py`、`src/deploy/migrations/010_mcp.sql`〔新〕 | **010**（9 张新表 + 4 索引） | — | ib-web 重启时 `ExecStartPre` 自动应用 |
| Web | `src/ibweb/{composition,views,config_views,urls}.py`、`src/ibweb/mcp_views.py`〔新〕（`/api/mcp/*` 14 个视图，仅 admin） | 无 | 无 | ib-web 重启 |
| 依赖 | `src/requirements.txt`、`src/requirements-offline.txt`（各 +`cryptography>=42,<51`） | — | 目标机 venv 仅**核对**（DEPLOY-003），不安装 | 同上 |
| 前端 | `McpServersPage.vue`〔新〕、`utils/{mcpLabels,externalGrants}.ts`〔新〕、`api/client.ts`、`router/index.ts`、`layouts/ConsoleLayout.vue`、`components/config/AgentDetailPanel.vue` | 无 | 目标机 `npm run build`；lock 未变，不 `npm ci` | 不重启；拷贝到 `/var/www/intelligentbase/` |
| 部署模板 | `src/deploy/env.example`（+5 个注释键，占位 `<REPLACE_ME_…>`，无凭据）、`src/deploy/checklists.txt`（+`[B30]` 与签署行） | — | — | 仓库文件，不被服务读取 |
| 自检 / CI / 测试 | `src/scripts/selfcheck.py`、`.github/workflows/ci.yml`、`tests/**`、`src/frontend/tests/mcp_r29.test.js` | — | — | 非运行时交付物 |
| systemd / nginx / ib-embed / qdrant | **无改动**（`git diff HEAD --stat -- src/deploy/systemd src/deploy/nginx src/ib_embed src/frontend/package*.json` 为空；module_design） | — | — | 无 |

**"改什么重启什么"核对（SKILL.md §6）**：`ibweb/**`、`ib/**` → ib-web ✓（DEPLOY-004）；前端 → 不重启，build + 拷 web root ✓（DEPLOY-005）；迁移 → 随 ib-web 重启 ✓；`/etc/intelligentbase/ib-web.env`（新键）→ 重启 ib-web，**与 DEPLOY-004 合并为同一次重启**（故主密钥须在重启前写入，DEPLOY-001）；`ibweb/worker.py` / 入库链路 → 本轮**无改动**，ib-worker 不重启（OI-5 已关闭：supervisor 只在 ib-web 进程启动，见 DEPLOY-006）；unit / nginx 无改动 ✓。

## 目标环境与策略

- **环境**：`production`（画像 P7）；SSH 见 SKILL.md §1–§2（外网备用入口 §8.1）。不设计 staging。
- **策略：recreate**。理由：单机单实例，无负载均衡与第二套环境。顺序按依赖：env 键（配置）→ 代码落盘 → 依赖核对 → 数据层（迁移 010，随 ib-web 启动）→ 服务层（ib-web 重启）→ 前端（避免新前端先于新接口上线：`/api/mcp/*` 在旧后端不存在）。
- **预计停机**：ib-web 约 10–30 秒 `[INFERRED]`（`TimeoutStopSec=30`，ib-web.service:68）；内存态聊天会话丢失（选无人时段）；前端发布窗口 ≤ 数秒；旧页面需硬刷新（Ctrl+F5）。
- **首发上线形态**：升级后**无任何 MCP Server**，`/healthz/deps` 无 `egress_mcp`，`/api/config/catalog` 键集与基线相同（module_design 兼容性 #8 / #9）；`IB_MCP_ENABLED` 缺省 1（功能开启但空载）。既有项目不迁移，定义文档 / 提示词逐字节不变。
- **未配置主密钥时的系统行为（GR-B-002-F02，架构 ADR-R29-06 第 1、7 点）**：`IB_MCP_SECRET_KEY` 缺失**不阻断启动**；`auth_kind=none` 的 Server 登记 / 使用照常；登记或改为 `bearer` / `header` 型 Server、写入凭证（`PUT …/credentials`）一律返回 `409 secret_key_missing`（文案"凭证主密钥未配置"），**不写任何凭证行，不降级为明文**；已有凭证的调用降级（fail-closed）。**设置了但格式非法（或 `cryptography` 不可导入）⇒ ib-web 启动失败**（`ConfigError`，key=`IB_MCP_SECRET_KEY`，只报键名、不含值；composition.py:574/588）。故主密钥必须用官方生成命令产出（DEPLOY-001），不得手写。

## 执行约定（引号与变量）

执行端为 bash（Git Bash / Linux），**不要**把复杂命令作为参数从 PowerShell 传入（SKILL.md §4.2）。

```bash
# 连接函数（密钥 / 主机 / 用户见 SKILL.md §1-2；BatchMode 保证绝不回落到口令交互）
ibssh() { ssh -i ~/.ssh/ib_prod_ed25519 -o UserKnownHostsFile=/tmp/ib_kh -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@192.168.31.133 "$@"; }
```

| 规则 | 说明 |
|---|---|
| Q1 | 不含本地值的远端命令：整条放进**单引号**，`$VAR` 在**远端**展开。 |
| Q2 | 需要本地值（`ANCHOR`、`DEPLOY_COMMIT`、`REVERT_COMMIT`、`PULL_TS`、`RESTART_TS`）：一律 `ibssh bash -s -- "$A" "$B" <<'EOF' … $1 $2 … EOF`——本地双引号只把值作为**位置参数**传过去，heredoc 用单引号定界使本地不展开，远端用 `$1 $2`。**禁止** `ibssh 'git checkout $ANCHOR -- …'`（远端为空）。markdown 里 heredoc 代码块须顶格粘贴。 |
| Q3 | 单引号内有意在远端定义并使用的变量（如 `TS=$(date …)`）是远端变量，属预期。 |
| Q4 | 变量取值与核验：`ANCHOR` = PRE-01 输出的 40 位 `git rev-parse HEAD`；`DEPLOY_COMMIT` = PM 在 `special_instructions` 下发；`REVERT_COMMIT` = ROLLBACK-002a 产生。使用前本地核验 `[[ "$X" =~ ^[0-9a-f]{40}$ ]]`，远端 `git cat-file -t "$X"` 必须输出 `commit`（PRE-02 / ROLLBACK-002b 内置）。 |
| Q5 | 凡需 sudo 口令的动作（台账备份 / 只读核查、编辑 env、`DROP`、venv 升级）由用户在交互式会话中执行；**禁止** `printf '<口令>' \| sudo -S`；**不读取、不回显** `/etc/intelligentbase/*.env` 的值（只允许 `grep -c` / 长度这类"计数"，且由用户执行）；**禁止** scp / pscp / rsync 向生产传代码。 |
| Q6 | 凭据、令牌、主密钥只写存放位置，不写值；本仓库 PUBLIC，本文不含任何凭据。 |
| Q7 | 参与"线上代码版本"判据的 Python 命令一律 `python -B` / `PYTHONDONTWRITEBYTECODE=1`，避免在部署树写 `.pyc` 污染判断（SKILL.md §7.1）。 |

## 预检清单

执行者：`A` = devops 代理经 ssh（E2 授权后）；`U` = 用户；`M` = 主会话。任一项不通过：**停止，不进入 DEPLOY-001**（目标环境尚无变更，报告 `DEPLOYMENT_FAILED`，无需回滚）。

| ID | 检查项 | 执行者 | 通过标准 |
|---|---|---|---|
| PRE-00 | 待部署提交已在远端；无遗漏的未跟踪文件；**该提交 CI 全绿且 Fernet 契约真实执行**（GR-D-003 条件 4） | M | 见下 |
| PRE-01 | 目标机 HEAD 记录为**回滚锚点**；已跟踪文件无本地修改 | A | HEAD 为 40 位哈希且记入报告；无 ` M` 的已跟踪文件 |
| PRE-02 | **变更集分类门（CLASS）**：REV-28 已在目标机；区间 `ANCHOR..DEPLOY_COMMIT` 文件类别符合预期；与目标机本地修改无交集 | A | `CLASS=A` 方可继续；`P` / `E` / `X` 见下 |
| PRE-03 | 磁盘 / 内存 / 工具链；**venv `cryptography` 版本区间与 Fernet 探针**（GR-D-003 条件 2） | A | 盘余量 ≥ 1 GiB、可用内存 ≥ 1 GiB `[INFERRED]`；node 主版本 22；`cryptography` ∈ `[42,51)`；探针输出 `fernet ok` |
| PRE-04 | 服务与页面基线（对照用） | A | 5 个单元 active；记录 ib-web / ib-worker / ib-embed 的 `ActiveEnterTimestamp`、`NRestarts`、ib-web `MemoryCurrent`；记录 `/healthz/deps` 顶层键集；记录 web root `index.html` 的 sha256 与 `assets/index-*.js`；`~/ib-webroot-pre-r29` 不存在；记录 **ib-web 与 ib-worker 的线程数**（MV-09 / **MV-10 = V-13** 的"旧代码"基线）与 venv Python 版本 |
| PRE-05 | **台账迁移前备份**（用户执行；`[B30](1)` 同 `[B28](1)` 口径） | U | 备份文件存在、非空、`integrity_check` 为 ok、`documents` 行数与主库一致 |
| PRE-06 | **只读核查**：定义文档中无 `mcp__` 授权；台账中尚无 `mcp_*` 表 | U | 输出"命中 0"；命中 >0 → **停止**报 PM（说明 010 已被应用或存在命名冲突） |
| PRE-07 | env 键现状（**只出数字**，不读值） | U | `IB_MCP_SECRET_KEY` 行数 = 0（避免 DEPLOY-001 追加出重复键）；`IB_MCP_` 前缀其余键行数记录在案（期望 0）；`ib-web.env` 仍为 `600 ib-web:ib-web` |
| PRE-08 | 验收前置（见下） | U | 用户书面确认 |

### PRE-00（开发机 / 主会话）

```bash
git status -sb | head -n 3                                            # 期望 main...origin/main，无领先落后
git ls-remote origin refs/heads/main                                   # 首列必须 == DEPLOY_COMMIT
git ls-files --others --exclude-standard src tests .github | wc -l     # 期望 0（新文件均已入库）
git ls-tree -r --name-only "$DEPLOY_COMMIT" | grep -cE '^(src/deploy/migrations/010_mcp\.sql|src/ib/mcp/transport\.py|src/ib/mcp/crypto\.py|src/ib/mcp/supervisor\.py|src/ib/ledger/mcp_store\.py|src/ibweb/mcp_views\.py|src/frontend/src/views/McpServersPage\.vue|src/frontend/src/utils/mcpLabels\.ts|src/frontend/src/utils/externalGrants\.ts|tests/unit/test_mcp_crypto_fernet_r29\.py)$'   # 期望 10
gh run list --commit "$DEPLOY_COMMIT" --workflow CI --json databaseId,status,conclusion --limit 5   # 须有 status=completed 且 conclusion=success
gh run view <databaseId> --log | grep -E "test_mcp_crypto_fernet|IB_REQUIRE_CRYPTO|[0-9]+ skipped|passed" | tail -n 20   # Fernet 契约门取证
```

- **CI 门（E2 前置条件，GR-D-003 条件 4）**：本轮代码尚未 push，CI 未跑过。push 后必须在 `DEPLOY_COMMIT` 上同时满足：① 10 阶段 `completed / success`（特别关注 PIPE-02 的 010 迁移门与 PIPE-07 selfcheck）；② job env 含 `IB_REQUIRE_CRYPTO=1`；③ 日志中 `test_mcp_crypto_fernet_r29.py` 为 passed、**无 skipped**（汇总行预期 `1767 passed`、`0 skipped` `[INFERRED]`，首次 push 后以 CI 实际为准）。**本机 6 SKIP 不代表通过**，不得以本机结果代替 CI。红灯、仍在运行、未触发、或有 skipped 指向该文件 → **不得部署**。
- `gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`；本机无 `gh` 或未登录 → 在 GitHub Actions 网页核对，等价；无法核对 → 标"未验证"并请用户确认，不得默认通过。
- 勿在 `src tests .github` 留下未入库文件（否则 `git pull` 到目标机时缺文件，运行时 ImportError）。

### PRE-01（A）

```bash
ibssh 'cd /opt/intelligentbase && git rev-parse HEAD && git log --oneline -1 && git status --porcelain'
```

输出的 40 位哈希即 `ANCHOR`，写入 deployment_report 首节。已跟踪文件修改（` M`）必须为空；`??` / 被忽略项（venv、node_modules 等）是本地状态，只记录、不触碰。**不得假定 HEAD 等于任何已知提交。**

### PRE-02（A）：变更集分类门

```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
R28=b4fa3a3df7fd39745363a52452779711b5979bec            # REV-28 提交（参照点，来自仓库历史，非目标机状态假设）
[ "$(git cat-file -t "$1")" = commit ]
git fetch origin main
[ "$(git cat-file -t "$2")" = commit ]
[ "$(git rev-parse origin/main)" = "$2" ]                # 远端恰为待部署提交
git merge-base --is-ancestor "$1" "$2"                   # 锚点是祖先 => ff-only 可行
[ "$1" != "$2" ] || { echo "ANCHOR==DEPLOY_COMMIT: 无代码变化，停止并核对是否已部署"; exit 3; }
if git merge-base --is-ancestor "$R28" "$1"; then P=""; else P="REV28_NOT_IN_ANCHOR"; fi
CH=$(git diff --name-only "$1" "$2")
echo "changed_files=$(printf '%s\n' "$CH" | grep -c .)"
X=$(printf '%s\n' "$CH" | grep -E '^(src/deploy/systemd/|src/deploy/nginx/|src/deploy/config\.example\.json|src/deploy/ib-(embed|worker)\.env\.example$|src/requirements-embed\.txt|src/frontend/package(-lock)?\.json)' || true)
MIGX=$(printf '%s\n' "$CH" | grep -E '^src/deploy/migrations/' | grep -vE '^src/deploy/migrations/010_mcp\.sql$' || true)
E=$(printf '%s\n' "$CH" | grep -E '^src/ib_embed/' || true)
DEPS=$(git diff -U0 "$1" "$2" -- src/requirements.txt src/requirements-offline.txt | grep -E '^[+-][^+-]' || true)
DEPX=$(printf '%s\n' "$DEPS" | grep -vE '^[+-](cryptography>=42,<51|#)' | grep -v '^$' || true)
echo "--- 依赖清单变动行(期望仅 cryptography 两行 + 注释行):"; printf '%s\n' "$DEPS"
echo "--- CLASS-X 依据:"; printf '%s\n%s\n%s\n' "$X" "$MIGX" "$DEPX" | grep -v '^$' || true
echo "--- CLASS-E 依据(ib_embed 变更):"; printf '%s\n' "$E"
echo "--- 预期类别计数: ib/ibweb 后端=$(printf '%s\n' "$CH" | grep -cE '^src/(ib|ibweb)/') migration010=$(printf '%s\n' "$CH" | grep -cE '^src/deploy/migrations/010_') frontend=$(printf '%s\n' "$CH" | grep -cE '^src/frontend/src/')"
echo "--- 与目标机本地修改的交集(期望为空):"
comm -12 <(printf '%s\n' "$CH" | sort) <(git status --porcelain | awk '{print $2}' | sort)
if [ -n "$P" ]; then echo "CLASS=P"; elif [ -n "$X" ] || [ -n "$MIGX" ] || [ -n "$DEPX" ]; then echo CLASS=X; elif [ -n "$E" ]; then echo CLASS=E; else echo CLASS=A; fi
EOF
```

| CLASS | 含义 | 处置 |
|---|---|---|
| **A** | REV-28 提交已在 `ANCHOR` 的历史中；区间只含本轮预期类别：后端 `src/ib`、`src/ibweb`、迁移 **仅 010**、`src/requirements*.txt` **仅 cryptography 行**、前端 `src/frontend/{src,tests}`、`tests/`、`docs/`、`.claude/`、`.github/`、`src/scripts/`、`src/deploy/env.example`、`src/deploy/checklists.txt` | 继续 |
| **P** | `ANCHOR` 不含 REV-28 提交（目标机落后于 REV-28，区间会同时带入 009 迁移、lxml 依赖、联网模块、可能还有 ib-embed 前序提交） | **停止**，`DEPLOYMENT_FAILED`（无变更）；本计划不适用（需先按 REV-28 计划发布，或由 PM 重新规划），代理不自选处置 |
| **E** | 区间含 `src/ib_embed/**`（目标机落后于 ib-embed 的前序提交） | **停止**；先**单独发布**前序 ib-embed 提交（按其既有方式 `git pull --ff-only` + `sudo -n systemctl restart ib-embed` 并验证 `model_loaded=true`、`warm=true`、无 `ILL`，SKILL.md §8.11），由 PM 另行授权；完成后以新 `ANCHOR` 重跑 PRE-01 / PRE-02，应判 CLASS=A |
| **X** | 出现 unit / nginx / ib-embed 或 ib-worker 的 env 模板 / ib-embed 依赖 / 前端依赖锁 / 010 以外的迁移 / 除 `cryptography` 以外的 Python 依赖变化 | **停止**，`DEPLOYMENT_FAILED`（无变更）；本计划不适用（需 `daemon-reload` / `npm ci` / `pip install` / 额外迁移备份），PM 重新规划 |

- 交集非空（目标机对要覆盖的文件有本地修改）→ 停止上报，不 pull。`git fetch` 只更新远端跟踪引用，不改工作树。
- 依赖 diff 的过滤依赖 `cryptography>=42,<51` 的写法与两份清单一致（实际 diff：各 +1 行依赖加若干注释行，行尾无注释）。

### PRE-03 / PRE-04（A）

```bash
ibssh 'df -B1 --output=target,size,used,avail,pcent /var/www/intelligentbase /opt/intelligentbase "$HOME"; free -m | sed -n 1,2p; node -v; npm -v'
ibssh 'PYTHONDONTWRITEBYTECODE=1 /opt/intelligentbase/venv/bin/python -B -c "
import importlib.metadata as m
v = m.version(\"cryptography\"); t = tuple(int(x) for x in v.split(\".\")[:2])
print(\"cryptography\", v); assert (42, 0) <= t < (51, 0), v
from cryptography.fernet import Fernet
k = Fernet.generate_key(); f = Fernet(k); assert f.decrypt(f.encrypt(b\"probe\")) == b\"probe\"; print(\"fernet ok\")"'
ibssh 'date "+%F %T %Z"; systemctl is-active ib-web ib-worker ib-embed qdrant nginx; for u in ib-web ib-worker ib-embed; do systemctl show -p ActiveEnterTimestamp,NRestarts "$u"; done; systemctl show -p MemoryCurrent,MemoryMax ib-web; for u in ib-web ib-worker; do echo "$u pid=$(systemctl show -p MainPID --value $u) threads=$(ls /proc/$(systemctl show -p MainPID --value $u)/task | wc -l)"; done; /opt/intelligentbase/venv/bin/python -V'
ibssh 'curl -s http://127.0.0.1:18080/healthz/deps | python3 -c "import sys,json; print(sorted(json.load(sys.stdin)))"'
ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u; ls ~/ib-webroot-pre-r29 2>&1 | head -n 1'
```

- `"$HOME"`、`"$u"` 位于单引号内，属远端展开（Q1，预期）。python 块内 `\"` 是本地单引号内的字面双引号，远端看到的是正常字符串。探针用**临时随机密钥**，与 `IB_MCP_SECRET_KEY` 无关，不读任何 env。
- `cryptography` 不在 `[42,51)`（或 import / 探针失败，较老 x86_64 CPU 上的 import + 一次真实加解密，TBD-R29-1）→ **停止**，目标环境无变更，报告 `DEPLOYMENT_FAILED`：由用户在交互式 sudo 会话中升级 venv 内 `cryptography`（建议 `/opt/intelligentbase/venv/bin/pip install 'cryptography>=42,<51'`，权限身份 `[INFERRED]`，venv 属主决定是否需 sudo），完成后口头确认并由 PM 重新发起，从 PRE-03 重跑；代理不安装依赖（Q5）。
- PRE-04 的两行 `threads=`（旧代码 REV-28 下的 ib-web / ib-worker 稳态线程数，记作 `W_OLD` / `K_OLD`）与 `Python 3.x.y` 用作 V-13 对照；`/healthz/deps` 键集用作 V-05 对照；web root 副本目录末行应输出 `No such file or directory`（本轮副本目录尚不存在；`~/ib-webroot-pre-r28` 为上轮遗留，不触碰）。

### PRE-05（U）：台账迁移前备份（同 checklists `[B30](1)` / `[B28](1)`，只拷贝不回显）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)
src = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
dst = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r29.bak")
src.backup(dst)
print("documents:", dst.execute("select count(*) from documents").fetchone()[0],
      "integrity:", dst.execute("pragma integrity_check").fetchone()[0])
dst.close(); src.close(); print("backup done")
PY
sudo ls -l /var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r29.bak
```

以 `ib-web` 身份而非 root，避免 `-wal/-shm` 被建为 root 属主（checklists B22）。备份文件应为 `660 ib-web:ib`、非空。**回滚迁移 010 之前必须有此备份**（ROLLBACK-007 另要求 DROP 前再做一次新备份）。

### PRE-06（U）：只读核查（无 `mcp__` 授权、无 `mcp_*` 表）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
hits = scanned = 0
for root, _dirs, files in os.walk("/var/lib/intelligentbase"):
    for f in files:
        if not f.endswith(".json"):
            continue
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 5_000_000:
                continue
            txt = open(p, encoding="utf-8").read()
        except Exception:
            continue
        scanned += 1
        if '"mcp__' in txt:
            hits += 1
            print("HIT:", p)
print("json_scanned:", scanned, "mcp_grant_hits:", hits)
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
print("mcp_tables:", c.execute("select count(*) from sqlite_master where name like 'mcp\\_%' escape '\\'").fetchone()[0])
PY
```

- 通过标准：`mcp_grant_hits: 0` 且 `mcp_tables: 0`；`json_scanned` ≥ 1（为 0 说明路径假设失败，须人工确认定义文档位置，不得当作通过）。脚本**不打印文件内容**。同一扫描脚本在 ROLLBACK-000 中复用为"授权已清零"的核验。

### PRE-07（U）：env 键存在性（只出数字）

```bash
sudo grep -c '^IB_MCP_SECRET_KEY=' /etc/intelligentbase/ib-web.env || true
sudo grep -c '^IB_MCP_' /etc/intelligentbase/ib-web.env || true
sudo grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' /etc/intelligentbase/ib-web.env || true      # 键总数，DEPLOY-001 前后对比（应恰好 +1）
sudo stat -c '%a %U:%G %n' /etc/intelligentbase/ib-web.env
```

只关心数字：`IB_MCP_SECRET_KEY` 行数应为 0；`IB_MCP_` 其余键应为 0；`stat` 应为 `600 ib-web:ib-web`。**不得读取或回显任何值**。`IB_MCP_SECRET_KEY` 已为 1 → 停止，由用户说明来源（可能是上次尝试遗留；若已有则 DEPLOY-001 跳过生成，改为只做长度核验）。

### PRE-08 验收前置（U）

用户书面确认：
1. 已有**独立测试项目**；人工验证**不动生产业务配置**；不在业务项目上授权 `mcp__` 外部工具（原因见 ROLLBACK-000）。
2. admin 账号、编辑档账号、终端用户账号各 1 个（MV 需 admin 页面；授权勾选需编辑档）。
3. 无人正在编辑配置页且持有未保存草稿；已知旧页面需硬刷新（Ctrl+F5）。
4. 约定无人时段（ib-web 重启丢内存态会话；Stage 2 的 MV-07 / MV-08 / MV-09 还会再重启 1~2 次）；用户在场执行人工验证。
5. **Stage 2 的真实 MCP Server**：用户已指定可用的真实 Server（公网 https，或内网并将加入"内网允许名单"）及其出站 ACL 已放行 `host:port`（由用户配置）；MV-08 / MV-09 要求该 Server 是保持长连接的 streamable-http 且能被触发推送 `list_changed`，MV-09 要求 `https://`。**未能提供真实 Server → Stage 2 全部项记 `NOT_TESTABLE`（待人工验证），不阻断首发**（见「部署后验证」通过标准）。
6. 已看到下文「用户需要执行的动作」。

## 部署步骤

位置：DEPLOY-001 在目标机由**用户**执行；其余在目标机经 ssh。预检全部通过（CLASS=A）后按序执行；任一步失败按「失败处理矩阵」处置。

### DEPLOY-001: 用户生成并写入 `IB_MCP_SECRET_KEY`（GR-D-003 条件 2；env 修改属用户操作，画像 P7/P9）
- 组件: `/etc/intelligentbase/ib-web.env`（0600，属主 ib-web；SKILL.md §5.3）。**仅追加一键**，其余键不动；代理不碰该文件，不读不回显。
- 位置: 目标机，**用户**在交互式 ssh 会话中执行（需 sudo 口令，Q5）。此刻运行中的旧代码忽略该键，无副作用；新代码在 DEPLOY-004 重启时读取。
- 命令（用户在远端 bash 粘贴；密钥在 shell 变量中生成并直接追加，**不 echo、不进命令行参数**；首行 `\n` 保证即使文件末尾无换行也另起一行，空行对 EnvironmentFile 无害）:
```bash
K=$(/opt/intelligentbase/venv/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
printf '\nIB_MCP_SECRET_KEY=%s\n' "$K" | sudo tee -a /etc/intelligentbase/ib-web.env >/dev/null
unset K
```
- 核验（用户执行；只出数字 / 属性，不回显值）:
```bash
sudo grep -c '^IB_MCP_SECRET_KEY=' /etc/intelligentbase/ib-web.env          # 期望 1
sudo awk -F= '/^IB_MCP_SECRET_KEY=/{print length($2)}' /etc/intelligentbase/ib-web.env   # 期望 44（Fernet 密钥 url-safe base64）
sudo grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' /etc/intelligentbase/ib-web.env     # 期望 = PRE-07 的键总数 + 1
sudo stat -c '%a %U:%G %n' /etc/intelligentbase/ib-web.env                   # 期望仍为 600 ib-web:ib-web
```
- 预期: 键行数 1、长度 44、键总数恰 +1、权限属主不变。长度 ≠ 44 或键总数不对 → **停止，不进入 DEPLOY-002**（env 已变更，进入 ROLLBACK-001 由用户删除该行；目标机代码尚未变更）。
- 用户须知: **主密钥丢失 ⇒ 已存凭证不可恢复**（需重录）。用户应自行决定在密钥管理处另存一份（计划不读取、不规定存放方式）；备份的台账文件内的凭证密文也依赖同一主密钥。
- 回滚: ROLLBACK-001（默认**保留**该键，见其说明）

### DEPLOY-002: 目标机拉取代码（`git pull`，禁 scp / pscp / rsync）
- 组件: 全部源码（架构部署视图：基础设施无变更 → 数据层（迁移文件落盘，尚未应用）→ 服务层 → 前端）
- 位置: 目标机 `/opt/intelligentbase`（属主 `yangyang198354`，免 sudo）
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git rev-parse HEAD)" = "$1" ]                      # 前置：仍在锚点
git fetch origin main
[ "$(git rev-parse origin/main)" = "$2" ]               # 前置：远端恰为待部署提交；否则中止（尚无代码变更）
date "+PULL_TS=%F %T"                                    # 记入报告，供 V-07 日志 --since
git pull --ff-only origin main                          # 等价画像 P7 的 git pull origin main，加 --ff-only 禁止合并提交
[ "$(git rev-parse HEAD)" = "$2" ]                      # 后置：精确等于待部署提交
test -s src/deploy/migrations/010_mcp.sql
test -d src/ib/mcp
git log --oneline -1
git status --porcelain
EOF
```
- 预期: fast-forward 到 `DEPLOY_COMMIT`；已跟踪文件无修改；010 与 `src/ib/mcp/` 在位；退出码 0。**注意：此刻磁盘代码已领先于运行中的 ib-web / ib-worker 进程**（pull 与 DEPLOY-004 之间应尽量缩短，期间只做验证性访问）。
- 回滚: ROLLBACK-002（002a + 002b）

### DEPLOY-003: 依赖、导入与 Fernet 探针核对（只读闸，不改任何文件、不重启）
- 组件: venv（`/opt/intelligentbase/venv`，本地状态，不触碰）
- 位置: 目标机；Q7 不写 `.pyc`
- 命令:
```bash
ibssh bash -s -- "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git rev-parse HEAD)" = "$1" ]
export PYTHONDONTWRITEBYTECODE=1
cd src
PY=/opt/intelligentbase/venv/bin/python
$PY -B -c 'import importlib.metadata as m; v=m.version("cryptography"); t=tuple(int(x) for x in v.split(".")[:2]); assert (42,0)<=t<(51,0), v; print("cryptography ok", v)'
$PY -B -c 'from cryptography.fernet import Fernet; k=Fernet.generate_key(); f=Fernet(k); assert f.decrypt(f.encrypt(b"probe"))==b"probe"; print("fernet ok")'
$PY -B -c 'import ib.mcp, ib.mcp.crypto, ib.mcp.supervisor, ib.ledger.mcp_store, ib.tools; print("import ok")'
$PY -B -c 'import sqlite3; from ib.ledger import schema as S; c=sqlite3.connect(":memory:", isolation_level=None); S.ensure_schema(c); S.ensure_schema(c); c.executescript(S.mcp_ddl_script()); assert S.missing_mcp_tables(c)==(), S.missing_mcp_tables(c); print("010 ddl in-memory replay ok")'
EOF
```
- 预期: 打印 `cryptography ok …`、`fernet ok`、`import ok`、`010 ddl in-memory replay ok`（迁移文件与生成器的单源一致性由 CI Schema 门 + selfcheck `mcp_schema_single_source` 判定，此处不重复）。任一失败 → 停止（磁盘已 pull，进入失败矩阵：视为已变更，ROLLBACK-002a → 002b；服务尚未重启）。
- 说明: `cd src` 使 `ib` / `ibweb` 可导入（`PYTHONPATH` 机制 `[INFERRED]`，与 REV-28 同）；失败原因若为导入路径而非产品缺陷，改用等价的 `-m` 形式并在报告注明。探针用临时密钥，不读 env。
- 回滚: 无（只读）；失败按上。

### DEPLOY-004: 重启 ib-web（迁移 010 随 `ExecStartPre` 自动应用；同时加载 `IB_MCP_SECRET_KEY`）
- 组件: ib-web（Waitress，127.0.0.1:18080）；`ExecStartPre=/opt/intelligentbase/venv/bin/python -m ibweb.bootstrap --ensure-schema`（ib-web.service:47）先建 9 张 `mcp_*` 表（幂等）；ib-web 启动后 supervisor 作为进程内 daemon 线程延迟首轮启动（无已启用 Server ⇒ 无探测、无监听）
- 位置: 目标机；`sudo -n systemctl restart ib-web`（三条免密 restart 之一，SKILL.md §4）
- 命令（重启严格断言，不得只用 `is-active`；同时记录启动就绪耗时作为 MV-07 的基线）:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; S=$(date +%s); sudo -n systemctl restart ib-web; for i in $(seq 1 60); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/healthz)" = 200 ] && break; sleep 1; done; E=$(date +%s); echo "ready_after_s=$((E-S))"; systemctl is-active ib-web; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp,MemoryCurrent ib-web; journalctl -u ib-web --since "$TS" --no-pager | grep -E "startup|ConfigError|IB_MCP|OperationalError|Traceback|ModuleNotFoundError|ImportError|runtime_compile_failed|config_drift|secret_key|mcp|path_not_configured_using_in_memory_default" | tail -n 40'
```
- 预期: `/healthz` 200；`active` / `running` / `NRestarts=0`；日志含 `"outcome": "succeeded", "stage": "startup"`；错误关键字零命中，**无 `ConfigError … IB_MCP_*`**（出现 ⇒ 主密钥格式非法或 `cryptography` 不可用，只报键名）；**不出现** `path_not_configured_using_in_memory_default`（文件态仍生效，SKILL.md §7.4）；`ready_after_s` 记入报告（MV-07 基线；`seq` 精度为 1 秒）；`daemon-reload` pending 警告是长期存在的（SKILL.md §7.2），不处理。`RESTART_TS` 记入报告。
- 若 `ExecStartPre` 失败（迁移 010 应用失败）→ ib-web 不会起来（`Restart=on-failure` 会反复重试）：**立即停止轮询**，查 `journalctl -u ib-web --since "$TS"` 的首个错误，不反复重启；进入回滚（ROLLBACK-004 的先决：002a→002b；若错误指向主密钥则先 ROLLBACK-001 删除该键再回滚代码或重试，由 PM 请用户决定）。
- 回滚: ROLLBACK-004（先 ROLLBACK-002）；迁移撤销见 ROLLBACK-007

### DEPLOY-005: 前端构建并发布到 web root（不重启任何服务）
- 组件: 前端静态产物（nginx 直读 `/var/www/intelligentbase/`，属主 `yangyang198354`，无需 sudo；nginx 不改、不 reload）。新页面 `#/system/mcp` 仅 admin 可见（`[B30](3)`）。
- 位置: 目标机 `/opt/intelligentbase/src/frontend`（`node_modules` 已就位；`package-lock.json` 未变，**不执行 `npm ci`**——`npm ci` 会先删除并重建 `node_modules`，触碰画像 P7 的本地状态；`checklists.txt [B30](3)` 已同口径，cicd_pipeline OI-1 已关闭）
- 命令（先留旧产物副本，再构建，构建成功才替换；构建命令超时需 ≥ 300 秒 `[INFERRED]`）:
```bash
ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r29 ]; mkdir ~/ib-webroot-pre-r29; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r29/; test -s ~/ib-webroot-pre-r29/index.html; test -d ~/ib-webroot-pre-r29/assets; ls ~/ib-webroot-pre-r29'
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html && grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u'
```
- 预期: `vue-tsc --noEmit && vite build` 退出码 0；打印新的 `assets/index-<hash>.js`，hash **不同于** PRE-04 记录的旧值；ib-worker / ib-embed 的 `ActiveEnterTimestamp` 不变。构建失败时 `&&` 链在 `rm` 之前中断，web root 仍是旧产物（**不要**在 `npm run build` 后接管道，以免掩盖退出码）。旧副本放在部署用户家目录（仓库外、不入 git），验收通过后由用户决定删除；不使用 `rsync` / `scp`。
- 替换窗口风险: `rm -rf assets` 与 `cp -r dist/assets` 之间（秒级），已加载旧 `index.html` 的浏览器若再懒加载旧 hash 分包会 404；有未保存草稿的用户须先保存或放弃再硬刷新 `[INFERRED]`（PRE-08 已确认无人编辑）。
- 回滚: ROLLBACK-005

### DEPLOY-006: （本轮不执行）重启 ib-worker
- **裁决（SKILL.md §6 逐项核对，1.1.0 重新评估）：仍不执行。**
  1. SKILL.md §6 触发 ib-worker 重启的只有 `ibweb/worker.py` / 入库链路 / `ib-worker.env` 的改动。核对（只读 git，2026-11-06）：`git diff HEAD --stat -- src/ibweb/worker.py src/ibweb/apps.py src/ibweb/wsgi.py src/ibweb/settings.py src/ib/{rebuild,parsing,chunking,ocr,blob,embedding,vectorstore,lifecycle,library}` **为空**；`src/deploy/ib-worker.env.example`、`src/deploy/systemd/` 无改动。回流第 3 轮只改了 `src/ibweb/composition.py`（组合根，被 ib-web 与 ib-worker 共用）等 MCP 相关文件，不触及 worker 入口与入库链路。
  2. **目标机上正在运行的 ib-worker 进程加载的是 REV-28 代码**（内存中的模块不随磁盘 `git pull` 改变；该进程从未载入 `ib.mcp`），因此它**不可能**存在 `ib-mcp-supervisor` 线程；OI-5 所担心的"重复 supervisor"仅会在 ib-worker **下次重启**（含主机重启）加载新 `composition.py` 后才有机会出现。
  3. **OI-5 已关闭**：DEF-R29-008 已修复并验证（`composition.py:881-895` `build_application` 在 :895 显式 `start_mcp_supervisor(...)`，`wsgi.py:33` 为唯一调用方；`composition.py:1636-1637` 注释声明 `_assemble` / `_install_config_runtime` 不再启动；TC-INT-R29-1100 / 1102：`worker._setup_django()` + `apps.ready()` 路径 0 个 `ib-mcp*` 线程；TC-INT-R29-1101：`build_application` 恰好 1 个；1103~1105 覆盖幂等 / 离线 / `IB_MCP_ENABLED=0`）。故 ib-worker 下次重启后：`build_deps` 会装配 `McpDeps`，但**不启线程、不探测、不监听**；`ib-worker.env` 没有 `IB_MCP_SECRET_KEY` 无影响（无 tick 即无凭证解密）。**不再需要**"代码层门控 / 在 `ib-worker.env` 设 `IB_MCP_ENABLED=0`"这类处置。
  4. 残留风险（如实留档）：上述结论来自**未起真实进程**的自动化（集成报告边界 5 明言），ib-worker **真实进程**路径在目标机尚未经验证。该验证只有"以新代码重启 ib-worker"才能做；因收益小于代价（重启会中断进行中的入库批次 `[INFERRED]`，且属于 §6 之外的额外变更），**默认不做**，改由：⓵ V-13 对 ib-web / ib-worker 做线程数核对（ib-worker 为未重启的旧进程，核对只证明"旧进程无 MCP 线程"，**不是** DEF-R29-008 的真实进程验证，报告中须如实标注）；⓶ 下次 ib-worker 因任何原因重启后，按下方"可选 DEPLOY-006b 的核对命令"补做一次。
- E2 遇到该步骤一律记「跳过」，不得标 SUCCESS；V-01 中 ib-worker 的 `ActiveEnterTimestamp` 必须与 PRE-04 相同。
- **可选 DEPLOY-006b（仅当 PM 在授权的 `special_instructions` 显式写 `INCLUDE_WORKER_RESTART=true`；缺省不授权）**：目的 = 在目标机真实进程上验证 DEF-R29-008 的 worker 半边。位置：目标机；前置 = DEPLOY-004 / V-13 已完成且无进行中的入库任务（用户确认）。命令（`K_OLD` 取 PRE-04 的 ib-worker 线程数，作位置参数传入，Q2）:
```bash
ibssh bash -s -- "$K_OLD" <<'EOF'
set -euo pipefail
TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "WORKER_RESTART_TS=$TS"
sudo -n systemctl restart ib-worker
sleep 45                                                   # 覆盖 supervisor 首轮 5~30 s 延迟（若它错误地存在）+ 余量 [INFERRED]
systemctl is-active ib-worker
systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-worker
pid=$(systemctl show -p MainPID --value ib-worker); [ "$pid" -gt 0 ]
n=$(ls "/proc/$pid/task" | wc -l); echo "ib-worker pid=$pid threads=$n (K_OLD=$1)"
echo "comm_ib_mcp=$(cat /proc/$pid/task/*/comm 2>/dev/null | grep -c '^ib-mcp' || true)"
journalctl -u ib-worker --since "$TS" --no-pager | grep -E "Traceback|ConfigError|IB_MCP|mcp|ModuleNotFoundError|ImportError" | tail -n 20 || true
EOF
```
  通过标准：`active`/`running`、`NRestarts=0`；`threads == K_OLD`（新进程无额外线程；`+1` 即疑似 supervisor 被错误启动 ⇒ DEF-R29-008 在真实进程上复发，**立即上报，不自行处置**）；`comm_ib_mcp=0`（Python ≥ 3.14 时有效，见 V-13 说明）；journal 无新错误。线程数基线依赖 worker 稳态线程数在重启前后一致 `[INFERRED]`，差 1 以内按"疑似"处理并附 py-spy 复核（V-13）。
- 回滚: ROLLBACK-006（同留档）

### DEPLOY-007: （可选，仅 Stage 2 的 `https://` 目标使用内网私有 CA 时）配置 `IB_MCP_CA_BUNDLE`
- 触发条件: 用户在 PRE-08 声明所用 https MCP Server 的证书由内网私有 CA 签发（公网可信 CA 无需此步）。
- 步骤 7a（用户执行）: 将 CA 的 PEM 放到目标机 `/etc/intelligentbase/mcp-ca.pem`（属主 / 权限使 ib-web 可读，如 `640 root:ib-web` `[INFERRED]`；公开证书，不含私钥），并在 `ib-web.env` 追加 `IB_MCP_CA_BUNDLE=/etc/intelligentbase/mcp-ca.pem`；完成后口头确认，不贴文件内容。
- 步骤 7b（A）: 与 DEPLOY-004 相同的重启严格断言命令（`RESTART_TS` 重新取值）。
- 回滚: ROLLBACK-008（用户删除该键行 + 重启 ib-web；零数据影响）

## 回滚步骤（逆序）

执行总序：**ROLLBACK-000（用户前置，仅当已有项目授权过外部工具 / 已登记 Server）→ 002a（源头 revert + push）→ 002b（目标机 pull）→ 005（前端重建发布）→ 004（重启 ib-web）→（若 DEPLOY-007 已执行）008 →（可选）007 迁移撤销 →（可选，通常不做）001 主密钥**。ROLLBACK-002 是把"目标机代码状态"还原的载体，必须先于各单元动作落地；其余按 DEPLOY 逆序（前端先于 ib-web，避免旧后端配新前端）。ROLLBACK-007 / 001 必须在旧代码已运行之后。

**不得破坏的本地状态**（全部回滚路径均不触碰）：`/etc/intelligentbase/*.env`（由用户编辑，除 ROLLBACK-001 / 008 的单行删除）、`/var/lib/intelligentbase/`（台账、blob、definition、prompts）、bge-m3 权重、Qdrant 数据、`/opt/intelligentbase/venv`、前端 `node_modules`。**所有回滚均不使用** `git reset --hard`、`git clean`、`git stash`、覆盖式同步。

**配置版本回滚（产品功能）≠ 代码回滚**：若问题只出在验收期间在测试项目里产生的配置内容，用配置页"版本 → 回滚"（热生效，无需代码回滚）；本节 ROLLBACK 用于代码 / 迁移 / 前端本身有缺陷时。**只想停用外部工具而不回滚代码**：设 `IB_MCP_ENABLED=0`（用户编辑 env + 重启 ib-web；功能整体关闭，调用 fail-closed、supervisor 不启动、管理写端点 503；含外部授权的配置编译时视为悬空授权）——零数据影响。

### ROLLBACK-000: 回滚前置——清除项目的 `mcp__` 授权，并处置已登记 Server / 凭证（用户，经新版本的页面，**新代码仍在运行时**执行） `[MANUAL_ROLLBACK_REQUIRED: 外部授权与 Server 数据]`
- 为何必须: 旧代码（REV-28）的定义文档校验不认识 `mcp__*` 工具名（`tool_grant_tool_unknown`），若任一项目已保存的配置含 `mcp__` 授权，回退代码后在旧代码下保存会被拒绝，运行期因 `build_agent_tools` 抛错而编译失败（保留旧快照）——可能让该项目配置无法更新 / 加载失败（module_design「是否可逆」；`checklists.txt [B30](5)`）。
- 操作: 对验收期间保存过外部工具授权的项目，在配置页取消外部工具勾选并保存生效，或用"版本 → 回滚"回到授权之前的版本（产生新版本而非删除历史）；或在 `#/system/mcp` 对相应 Server 使用"删除 + 强制删除"（输入标识名二次确认，**自动清理授权**；同时删除该 Server 的工具、绑定、放行、凭证）。
- 核验（用户，只读）: 复用 PRE-06 的扫描脚本，输出 `mcp_grant_hits: 0` 才可继续 002a。
- **回滚前数据处置说明**（已登记 Server 与加密凭证）: 
  - 默认处置 = **保留**：不 DROP 表、不删 `IB_MCP_SECRET_KEY`。旧代码不读 `mcp_*` 表，留表无害；日后重新部署 REV-29 时 `CREATE TABLE IF NOT EXISTS` 幂等，已登记的 Server / 工具审核结果 / 凭证密文原样恢复（前提：主密钥仍在 env 且未变）。
  - 如决定放弃这些数据：先在 `#/system/mcp` 逐个删除 Server（凭证随之删除，无需密文处置），再按 ROLLBACK-007 DROP 表。
  - **凭证密文只能被同一主密钥解密**：若在保留密文的同时删除了主密钥（ROLLBACK-001），这些凭证永久不可恢复，重新部署后须重录。
  - `mcp_audit` 是审计记录，DROP 即永久丢失（PRE-05 / ROLLBACK-007 的备份是唯一副本）。

### ROLLBACK-002a: 源头 revert 并 push（主会话，用户确认；回滚 DEPLOY-002 的源头部分）
- 类型: 正式回滚
- 变量: `R29_COMMITS` = 本轮发布的提交哈希（可能多个；由 PM 在授权时与 `DEPLOY_COMMIT` 一并给出，**须全部是 `ANCHOR` 之后、`DEPLOY_COMMIT` 及之前的提交**），按**从新到旧**依次 revert。
- 命令（开发机；要求工作树对 `src tests .github` 干净）:
```bash
set -- <R29_COMMITS 从新到旧，空格分隔的 40 位哈希>            # 由 PM 提供；下面全部用 "$@"
git fetch origin main && git switch main && git pull --ff-only origin main
for c in "$@"; do [ "$(git cat-file -t "$c")" = commit ] && git merge-base --is-ancestor "$c" HEAD || { echo "BAD_COMMIT $c"; exit 1; }; [ -z "$(git rev-list --merges -n 1 "$c^..$c")" ] || { echo "MERGE_COMMIT $c"; exit 1; }; done
git revert --no-commit "$@"                                    # 参数 = R29_COMMITS（从新到旧）
git restore --source=HEAD --staged --worktree -- docs .claude   # 保留文档与 agent 记忆，只还原代码与测试
git diff --cached --name-only | grep -vE '^(src/|tests/|\.github/)' && echo UNEXPECTED_PATHS || echo ONLY_SRC_TESTS_CI
```
  核验两点：① 输出必须是 `ONLY_SRC_TESTS_CI`；② 对**最早的 R29 提交的父提交**（记作 `BASE`，须等于 `ANCHOR` 或其祖先且二者之间无其他运行时变更）：`git diff --quiet "$BASE" -- src tests .github && echo SRC_EQUALS_BASE || echo SRC_DIFFERS_FROM_BASE`，必须是 `SRC_EQUALS_BASE`；否则上报，不 commit，放弃本次 revert 用 `git revert --abort`（仅在 revert 处于进行中状态时可用；已完成暂存而无冲突态时先经用户确认再 `git restore --staged --worktree -- src tests .github`）。通过后:
```bash
git commit -m "revert(r29): roll back MCP adapter for agent tool calls (REV-29)"
git push origin main
git rev-parse HEAD                                             # = REVERT_COMMIT，记入报告
```
- 变量取值与核验: `R29_COMMITS` 以脚本位置参数传入并逐个 `git cat-file -t` / `merge-base --is-ancestor` / 非合并核验（上方循环）；`ANCHOR` 取 PRE-01 输出（deployment_report 首节），执行前 `git cat-file -t "$ANCHOR"` 必须输出 `commit`。回滚用的是**新提交 + 普通 push**，不 force-push、不 reset。revert 同时删除 `010_mcp.sql`、`mcp_ddl_script()`、requirements 中的 `cryptography` 行（**数据库中已建的 `mcp_*` 表保留，旧代码不读它们；venv 中的 `cryptography` 保留——它本是 pdfminer.six 的传递依赖，旧代码仍需要**）。
- 预期: push 成功；CI 对回退提交自动运行（记录结果，不必等待完成才继续回滚）。

### ROLLBACK-002b: 目标机拉取回退提交（回滚 DEPLOY-002）
- 类型: 正式回滚
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$REVERT_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git cat-file -t "$1")" = commit ]
git fetch origin main
[ "$(git cat-file -t "$2")" = commit ]
[ "$(git rev-parse origin/main)" = "$2" ]
git pull --ff-only origin main
[ "$(git rev-parse HEAD)" = "$2" ]
test ! -e src/deploy/migrations/010_mcp.sql && echo MIG010_REMOVED
test ! -d src/ib/mcp && echo MCP_PKG_REMOVED
git diff --stat "$1" HEAD -- src/ib src/ibweb src/deploy src/frontend/src src/requirements.txt src/requirements-offline.txt   # 期望：仅 ANCHOR 之后的非 REV-29 差异（通常为空）
git status --porcelain
EOF
```
- 变量取值与核验: `$1`=`ANCHOR`、`$2`=`REVERT_COMMIT` 均作为位置参数传入（Q2）。
- 预期: HEAD = `REVERT_COMMIT`；打印 `MIG010_REMOVED` 与 `MCP_PKG_REMOVED`（`src/ib/mcp/` 内若遗留未跟踪的 `__pycache__` 目录，目录会存在——此时以 `git ls-files src/ib/mcp | wc -l` = 0 判定，不 `git clean`，也不手工删除）；`git diff --stat` 为空或仅含非 REV-29 差异（人工判断）；无已跟踪文件修改。

### ROLLBACK-005: 回滚 DEPLOY-005（前端）
- 类型: 正式回滚 = 002b 之后用回退后的源码重新构建并发布；紧急止血 = 还原部署前 web root 副本。
- 正式回滚命令:
```bash
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html'
```
- 紧急止血（不依赖构建；新前端有严重缺陷且 push / pull 通道暂不可用时）:
```bash
ibssh 'set -e; test -s ~/ib-webroot-pre-r29/index.html; test -d ~/ib-webroot-pre-r29/assets; rm -rf /var/www/intelligentbase/assets; cp -r ~/ib-webroot-pre-r29/assets /var/www/intelligentbase/; cp ~/ib-webroot-pre-r29/index.html /var/www/intelligentbase/; sha256sum /var/www/intelligentbase/index.html; ls -l /var/www/intelligentbase'
```
  **收尾（必做）**: 止血后仍须走 002a → 002b 并执行一次正式回滚命令，使 web root 与远端 HEAD 的构建结果一致、目标机仓库回到与远端一致的干净状态（止血本身不改仓库，无需 git 清理）。
- 变量取值与核验: 无本地变量；`test -s` / `test -d` 已内置。止血后 `sha256sum` 必须等于 PRE-04 记录值；正式回滚后须不同于 DEPLOY-005 的新 hash。
- 预期: 硬刷新后恢复旧界面（无"MCP 外部工具"系统页、配置页无外部工具区）。

### ROLLBACK-004: 回滚 DEPLOY-004（ib-web 以回退后的代码重启）
- 类型: 正式回滚（前提：ROLLBACK-000 已满足、002a / 002b 已完成）
- 命令: 同 DEPLOY-004 的重启严格断言命令块（此时磁盘代码为回退版本）。
- 预期: 同 DEPLOY-004 的「预期」，另 `ExecStartPre` 在**含 `mcp_*` 表的库**上正常通过（旧 `ensure_schema` 只补自己认识的表 / 列，不报多余表）`[INFERRED]`；`IB_MCP_SECRET_KEY` 残留在 env 中被旧代码忽略。
- 失败处理: 重启失败 → 先查日志首个错误（重点 `tool_grant_tool_unknown` → 返回 ROLLBACK-000），不反复重启；`ROLLBACK_FAILED`，保留现场，人工介入。

### ROLLBACK-006: 回滚 DEPLOY-006
- 本轮 DEPLOY-006 默认不执行，无需回滚；仅当可选 DEPLOY-006b 被授权并执行过才适用：回滚 = 在 ROLLBACK-002b 之后对 ib-worker 重复 006b 的 `sudo -n systemctl restart ib-worker` 与 `active`/`NRestarts=0` 断言（磁盘代码为回退版本），重启失败不反复重试，`ROLLBACK_FAILED`。

### ROLLBACK-008: 回滚 DEPLOY-007（可选）
- 类型: 正式回滚。**用户**编辑 `/etc/intelligentbase/ib-web.env`，删除 `IB_MCP_CA_BUNDLE` 行（仅该行）；随后 A 执行与 DEPLOY-004 相同的重启严格断言。使用该 CA 的 https Server 将因证书校验失败而 `unreachable`（预期，不影响其他功能）。
- 核验（用户）: `sudo grep -c '^IB_MCP_CA_BUNDLE=' /etc/intelligentbase/ib-web.env` 为 0；键总数比删除前少 1；`stat` 权限属主不变。

### ROLLBACK-007: 撤销迁移 010（用户，**可选**） `[MANUAL_ROLLBACK_REQUIRED: 删除 9 张 mcp_* 表——已登记 Server、工具审核结果、项目绑定与放行、加密凭证、治理参数、内网允许名单、调用与管理审计]`
- 通常**不需要**：代码回退后旧代码不读这些表，留表无害，且再次部署 010 为幂等 `IF NOT EXISTS`、数据原样恢复（见 ROLLBACK-000 默认处置）。
- 前提（缺一不执行）: ① 旧代码已运行（ROLLBACK-004 完成，避免新代码仍在使用这些表）；② ROLLBACK-000 的处置已决定为"放弃数据"；③ **在 DROP 之前再做一次新备份**（PRE-05 的备份早于 Stage 2 的登记 / 审计，不含之后的数据）。
- 命令（命令来自 010 头注释的逆依赖顺序，不在迁移文件内以可执行形式出现；用户执行）:
```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)
db = "/var/lib/intelligentbase/ledger/ledger.sqlite3"
order = ["mcp_audit", "mcp_internal_allow", "mcp_governance", "mcp_credentials", "mcp_risk_waivers",
         "mcp_tool_bindings", "mcp_tools", "mcp_server_projects", "mcp_servers"]
src = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
dst = sqlite3.connect(db + ".pre-r29-drop.bak")
src.backup(dst)
print("backup integrity:", dst.execute("pragma integrity_check").fetchone()[0])
for t in order:
    print("before", t, src.execute("select count(*) from " + t).fetchone()[0])      # 只数行，不 select 凭证列
dst.close(); src.close()
c = sqlite3.connect(db)
for t in order:
    c.execute("DROP TABLE IF EXISTS " + t)
c.commit()
print("after mcp_tables:", c.execute("select count(*) from sqlite_master where name like 'mcp\\_%' escape '\\'").fetchone()[0])
c.close()
PY
sudo ls -l /var/lib/intelligentbase/ledger/ledger.sqlite3*     # 核对主库与 -wal/-shm 仍为 660 ib-web:ib（属主不得变 root）；两份 .bak 保持 660
```
- 变量取值与核验: 表名固定常量（来自 010 头注释），无外部变量；脚本先备份、`integrity_check` 为 `ok`、打印每表行数，之后 DROP；`after mcp_tables` 必须为 0（索引随表删除）。
- 数据风险: 丢失全部 MCP 登记 / 审核 / 审计数据；**凭证密文随表删除**（备份文件中保留的密文只能被原主密钥解密——勿同时删除 `IB_MCP_SECRET_KEY`）；`mcp_audit` 备份是唯一副本。DROP 后若重新部署 REV-29，上述数据需重新登记 / 审核 / 重录凭证，治理参数回到默认值。备份文件内含凭证密文，须保持 `660 ib-web:ib`，不得拷出目标机。

### ROLLBACK-001: 回滚 DEPLOY-001（主密钥，用户，**默认不执行**） `[MANUAL_ROLLBACK_REQUIRED: 已存凭证密文将永久不可解密]`
- 默认**保留**该键：旧代码忽略它；保留才能使"留表 / 日后重新部署 / 备份恢复"场景下的凭证密文仍可解密。
- 仅当同时满足 ① 从未存过凭证（V-04 / `mcp_credentials` 行数 0），或已按 ROLLBACK-000 删除全部 Server，且 ② 用户明确要求移除，才执行（用户，需 sudo）:
```bash
sudo grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' /etc/intelligentbase/ib-web.env          # 删除前键总数 N
sudo sed -i '/^IB_MCP_SECRET_KEY=/d' /etc/intelligentbase/ib-web.env
sudo grep -c '^IB_MCP_SECRET_KEY=' /etc/intelligentbase/ib-web.env || true           # 期望 0
sudo grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' /etc/intelligentbase/ib-web.env             # 期望 N-1
sudo stat -c '%a %U:%G %n' /etc/intelligentbase/ib-web.env                           # 期望仍为 600 ib-web:ib-web（sed -i 以 root 执行会保持属主权限，仍须核对）
```
- 变量取值与核验: 无本地变量；以键总数 N → N-1 与 `stat` 核验；不回显任何值。删除后仍有 ib-web 以旧代码运行则无需重启（旧代码不读该键）；若新代码仍在运行则必须重启才生效，并会使凭证型 Server 降级。

### 失败处理矩阵（E2 使用）

| 失败位置 | 目标环境是否已变更 | 处置 |
|---|---|---|
| 任一 PRE（含 CLASS=P/E/X、PRE-03 `cryptography` 不满足、PRE-06 命中、PRE-07 异常） | 否 | 停止，`DEPLOYMENT_FAILED`，无需回滚 |
| DEPLOY-001（用户写入主密钥后核验不符：长度 ≠ 44 / 键总数不对 / 权限属主变化） | 是（仅 env） | 停止；ROLLBACK-001（用户删除该行，核验 N → N-1）；代码尚未变更 |
| DEPLOY-002（前置核对失败） | 否（env 若已写入则保留，无害） | 停止，`DEPLOYMENT_FAILED` |
| DEPLOY-002（pull 后 HEAD ≠ 待部署提交 / 工作树不干净） | 是 | ROLLBACK-002a → 002b |
| DEPLOY-003（`cryptography` / Fernet / 导入 / DDL 核对失败） | 是（仅代码已落盘，服务未重启） | ROLLBACK-002a → 002b；服务无需动作 |
| DEPLOY-004（重启失败 / `ExecStartPre` 迁移失败 / `ConfigError IB_MCP_*` / 日志有错误） | 是 | 停止后续；ROLLBACK-002a → 002b → 004；主密钥格式类错误由用户决定先 ROLLBACK-001（ROLLBACK-000 若涉及） |
| DEPLOY-005（构建失败，web root 未替换） | 是（后端已变更） | 视为已变更：保持后端新版本是否可接受由 PM 请用户裁决；若回滚按 002a → 002b → 005 → 004 |
| DEPLOY-005（替换中途失败，web root 可能不完整） | 是 | 先 ROLLBACK-005 紧急止血恢复可用，再 002a → 002b → 005 → 004 |
| DEPLOY-006 | — | 本轮不执行（OI-5 已关闭）；可选 006b 若执行后线程数多 1 → 视为 DEF-R29-008 复发，立即上报 PM，不自行处置 |
| 部署后验证机器可验项失败（V-01~V-11、V-13） | 是 | `DEPLOYED_WITH_ISSUES`，列出失败项，由 PM 请用户决定是否回滚 |
| 人工验证 Stage 1 不通过 | 是 | `DEPLOYED_WITH_ISSUES`；缺陷回流（协议 §C）或用户决定回滚；仅测试项目内容问题优先用配置版本回滚 / 删除测试 Server |
| Stage 2 项失败（MV-04/06/07/08/09 等） | 是 | 单独记录结果（不影响首发状态判定，见通过标准）；严重问题（如重启超时、线程残留）→ `IB_MCP_ENABLED=0` 止血或回滚 |
| 回滚步骤自身失败 | — | 停止回滚，`ROLLBACK_FAILED`，写清各步骤已部署 / 已回滚 / 状态未知，由用户人工介入 |
| 遇到 `[MANUAL_ROLLBACK_REQUIRED]` 步骤失败（ROLLBACK-000 / 007 / 001） | — | 立即暂停，返回 BLOCKED 等待人工决定 |

## 不可逆步骤汇总

| # | 步骤 | 性质 | 数据风险 | 处置 |
|---|---|---|---|---|
| I-1 | DEPLOY-004 应用迁移 010（新增 9 张 `mcp_*` 表） | `[MANUAL_ROLLBACK_REQUIRED: 撤销 = ROLLBACK-007 的 DROP，由用户在备份之后执行]` | 低（新表无存量）→ 登记 Server 后变为中：DROP 会丢失 Server / 审核 / 审计 / 凭证密文；代码回退后留表无害 | 默认不 DROP；需要时按 ROLLBACK-000 处置说明与 ROLLBACK-007 |
| I-2 | DEPLOY-001 写入主密钥；其移除 | `[MANUAL_ROLLBACK_REQUIRED: 移除或丢失主密钥 ⇒ 已存凭证密文永久不可恢复]` | 写入本身无风险；一旦存过凭证，密钥即成为这些数据的唯一解密条件 | 默认保留；移除须满足 ROLLBACK-001 的两个前提；用户自行保管副本 |
| I-3 | Stage 2 在测试项目中登记真实 Server、审核启用工具、授权调用 | 外部系统调用 + 数据只增不删 | 对真实 MCP Server 的调用不可撤回（工具默认只放行 `read_only`；`side_effect` / `unknown` 工具默认置灰，放行需显式 waiver，本轮验收**不得**放行有副作用的工具）；`mcp_audit` 与配置版本只增不删；含 `mcp__` 授权的版本在旧代码下无法保存（见 ROLLBACK-000） | 仅限测试项目与只读工具；验收后用"版本 → 回滚"回到授权前，并删除测试 Server |
| I-4 | DEPLOY-004 重启 ib-web（Stage 2 的 MV-07 / 08 / 09 还会再重启） | 不可撤销的副作用 | 内存态聊天会话与"人工确认挂起态"丢失（fail-closed）；supervisor 监听线程在重启时终止 | 选无人时段 |
| I-5 | ROLLBACK-007 之后重新部署 | 数据不可恢复 | 见 ROLLBACK-007 数据风险 | — |

web root 替换可通过备份副本还原（ROLLBACK-005 止血），不属不可逆。

## 部署后验证

「真实启动时刻」= DEPLOY-004 输出的 `RESTART_TS`。执行者 `A` = 代理经 ssh；`U` = 用户；`U*` = 用户人工验证（见 MV 排期）。

| ID | 检查项 | 执行者 | 命令 / URL | 成功标准 |
|---|---|---|---|---|
| V-01 | 服务存活且重启符合预期 | A | `ibssh 'systemctl is-active ib-web ib-worker ib-embed qdrant nginx; for u in ib-web ib-worker ib-embed; do systemctl show -p ActiveEnterTimestamp,NRestarts "$u"; done'` | 5 行 `active`；ib-web `ActiveEnterTimestamp` 晚于 `RESTART_TS` 且 `NRestarts=0`；ib-worker / ib-embed 的时间戳与 PRE-04 相同（本轮不重启，必须相同） |
| V-02 | **线上代码版本**（HEAD + 源文件 mtime 早于启动时刻，**不用 .pyc**） | A | `ibssh bash -s -- "$DEPLOY_COMMIT" "$ANCHOR" <<'EOF'`；体：`cd /opt/intelligentbase; [ "$(git rev-parse HEAD)" = "$1" ]; git status --porcelain; AT=$(systemctl show -p ActiveEnterTimestamp --value ib-web); AT_EPOCH=$(date -d "$AT" +%s); bad=0; for f in $(git diff --name-only --diff-filter=AMR "$2" "$1" -- src/ib src/ibweb src/deploy/migrations); do m=$(stat -c %Y "$f"); [ "$m" -lt "$AT_EPOCH" ] \|\| { echo "NEWER_THAN_START $f"; bad=1; }; done; echo "mtime_check_bad=$bad"; test -s src/deploy/migrations/010_mcp.sql && echo MIG010_PRESENT`；`EOF`（粘贴时 heredoc 顶格，去掉表格中的转义反斜杠） | HEAD = `DEPLOY_COMMIT`；已跟踪文件无修改；`mtime_check_bad=0`；`MIG010_PRESENT`。`$2`=`ANCHOR` 作为位置参数传入（Q2） |
| V-03 | 启动日志与文件态 | A | `ibssh 'journalctl -u ib-web --since "<RESTART_TS>" --no-pager \| grep -E "\"stage\": \"startup\"\|path_not_configured_using_in_memory_default\|ConfigError\|IB_MCP\|Traceback\|ModuleNotFoundError\|ImportError\|runtime_compile_failed\|config_drift" \| tail -n 30'`（`<RESTART_TS>` 为本地已知值，须按 Q2 以位置参数传入，示意） | 有 `"outcome": "succeeded", "stage": "startup"`；**无** `path_not_configured_using_in_memory_default`；错误关键字（含 `ConfigError … IB_MCP_*`）零命中 |
| V-04 | 迁移 010 已应用（只读，ib-web 身份）；空载 | U | `sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'`；体：`import sqlite3; c=sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro",uri=True); print(sorted(r[0] for r in c.execute("select name from sqlite_master where type='table' and name like 'mcp\\_%' escape '\\'"))); [print(t, c.execute("select count(*) from "+t).fetchone()[0]) for t in ("mcp_servers","mcp_tools","mcp_credentials","mcp_audit","mcp_governance")]; print("documents:", c.execute("select count(*) from documents").fetchone()[0])`；`PY`；`sudo ls -l /var/lib/intelligentbase/ledger/ledger.sqlite3*` | 9 张表齐全（`mcp_audit, mcp_credentials, mcp_governance, mcp_internal_allow, mcp_risk_waivers, mcp_server_projects, mcp_servers, mcp_tool_bindings, mcp_tools`，与 `[B30](3)` 一致）；`mcp_servers` / `mcp_tools` / `mcp_credentials` 为 0（首发空载；只数行不 select 凭证列）；`mcp_governance` 0 行（缺行 ⇒ 默认值）；`documents` 计数等于 PRE-05 备份值；`ledger.sqlite3*` 仍 660 ib-web:ib |
| V-05 | 健康检查、外发声明与基线一致（无已启用 Server） | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz'`；`curl -sk -o /dev/null -w '%{http_code}\n' https://192.168.31.133/healthz`（不携带凭据）；`ibssh 'curl -s http://127.0.0.1:18080/healthz/deps \| python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d)); print(\"egress_mcp\" in d)"'` | 两处 `/healthz` 均 200；`/healthz/deps` 顶层键集与 PRE-04 完全相同，且 `egress_mcp` 为 `False`（无已启用 Server ⇒ 与基线逐字节相同，module_design 兼容性 #9） |
| V-06 | 新接口已挂载且受鉴权保护 | A | `ibssh 'for p in servers tools governance audit; do printf "%s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:18080/api/mcp/$p"; done'`（不带令牌） | 均返回 401 或 403（**不是** 404 / 500；404 = 新代码未生效，500 = 装配异常）`[INFERRED]` 具体码以 `authz` 现状为准，记录实际值 |
| V-07 | 日志无新增错误 | A | `PULL_TS` 取 DEPLOY-002 输出，经 Q2 位置参数传入：`journalctl -u ib-web --since "$1" -p warning --no-pager \| tail -n 30; journalctl -u ib-worker --since "$1" -p warning --no-pager \| tail -n 30`（`ibssh bash -s -- "$PULL_TS" <<'EOF'`，heredoc 顶格） | 无 Traceback / OperationalError 等新错误；已知长期 warning（`daemon-reload` pending）除外，需如实记录 |
| V-08 | 前端已发布为新构建 | A + 开发机 curl | 目标机：`ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html \| sort -u'`；外部：`curl -sk https://192.168.31.133/ \| grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \| sort -u` | 两处 hash 一致，等于 DEPLOY-005 输出，且不同于 PRE-04 旧值 |
| V-09 | 本地状态未被触碰；资源基线 | A | `ibssh 'cd /opt/intelligentbase && git status --porcelain; ls -d src/frontend/node_modules venv 2>&1 \| head -n 3; stat -c "%a %U:%G %n" /etc/intelligentbase/*.env; systemctl show -p MemoryCurrent,MemoryMax ib-web; echo "ib-web threads=$(ls /proc/$(systemctl show -p MainPID --value ib-web)/task \| wc -l)"'` | 已跟踪文件干净；`node_modules` 与 `venv` 仍在；env 文件权限属主与上线前一致（`600 ib-web:ib-web` 等，只 `stat`，不读内容）；`MemoryCurrent` 与线程数记录在案（接近 1024M 上限需上报，非失败项；线程数供 MV-09 对照） |
| V-10 | 既有功能冒烟（空载，不新增写入；写入数据唯一化） | U | 浏览器登录 → 现有项目问答一次（现有 kb-agent 路径）、配置页可打开（只读）。若需保存，名称带 `r29-<epoch>` 后缀 | 问答有答复且流式正常；页面无白屏 / 控制台报错；既有项目行为不变（兼容性 #1~#5） |
| V-11 | **MV-05（GR-D-003 条件 1，gating）**：部署后目标机 `cryptography` 版本区间、加解密探针、主密钥存在性 | A（前两项）+ U（第三项） | A：重复 DEPLOY-003 的前两条 python 命令（`ibssh bash -s -- … <<'EOF'` 体内 `$PY -B -c '…cryptography ok…'` 与 `'…fernet ok…'`）；U：DEPLOY-001 的四条核验命令（`grep -c` 为 1、`awk` 长度 44、`stat` 权限属主不变） | `cryptography ok <42≤v<51>` 且 `fernet ok`；`IB_MCP_SECRET_KEY` 存在且长度 44、文件仍 `600 ib-web:ib-web`；全程不回显值。主密钥**已被服务加载**的间接证据在 MV-01（登记 bearer 型 Server 不返回 `409 secret_key_missing`） |
| V-12 | 人工验证（见下 MV 排期） | U* | `e2e_test_report.md`「人工验证清单」 | 见下 |
| V-13 | **MV-10（DEF-R29-008，GR-D-004 条件）：进程内 supervisor 线程只在 ib-web**（只读；见下「V-13 / MV-10 说明」） | A（无需 sudo；`/proc` 受限时改 U） | 在 V-03 通过且 `RESTART_TS` 之后 **≥ 45 秒**执行（见说明）：`ibssh bash -s -- "$RESTART_TS" <<'EOF'`；体：`set -euo pipefail; echo "py=$(/opt/intelligentbase/venv/bin/python -V)"; echo "elapsed_s=$(( $(date +%s) - $(date -d "$1" +%s) ))"; for u in ib-web ib-worker; do pid=$(systemctl show -p MainPID --value "$u"); [ "$pid" -gt 0 ]; echo "$u pid=$pid threads=$(ls /proc/$pid/task \| wc -l) comm_supervisor=$(cat /proc/$pid/task/*/comm 2>/dev/null \| grep -c '^ib-mcp-supervis$' \|\| true) comm_any_ib_mcp=$(cat /proc/$pid/task/*/comm 2>/dev/null \| grep -c '^ib-mcp' \|\| true)"; done`；`EOF`（heredoc 顶格，去掉表格中的转义反斜杠；`$1` = `RESTART_TS`，Q2） | ① `elapsed_s ≥ 45`；② **ib-web**：`threads == W_OLD + 1`（W_OLD = PRE-04 记录；多出的 1 个即 supervisor daemon 线程；无已启用 Server ⇒ 无探测池线程、无监听线程）；若 `py` ≥ 3.14，另须 `comm_supervisor=1`；③ **ib-worker（本轮未重启，仍为 REV-28 旧进程）**：`threads == K_OLD`（= PRE-04 记录）且 `comm_supervisor=0`、`comm_any_ib_mcp=0`；④ ib-worker 的 `ActiveEnterTimestamp` 同 V-01 未变。②③ 全部满足 ⇒ PASS（**仅证明"旧 worker 进程无 MCP 线程、ib-web 多 1 个线程"，不等于 ib-worker 新代码路径已在真实进程验证**，报告须如此措辞）。偏差 ⇒ 记实际数字，`DEPLOYED_WITH_ISSUES`，由 PM / 用户裁决，可用 py-spy（说明 ④）复核 |

### 人工验证 MV-01~MV-10 排期（引用 `e2e_test_report.md`「人工验证清单」原文，**不改写其步骤与期望**；MV-10 的执行方式因事实约束有调整，见「V-13 / MV-10 说明」）

MV-01~03 为浏览器项（用户 UI 复核）；MV-04~10 为目标机可执行项（GR-D-003 条件 1、GR-D-004 条件）。分两阶段，首发先空载：

| 阶段 | 状态 | 谁 / 何时 | 包含的 MV | 说明 |
|---|---|---|---|---|
| **Stage 1**（首发后立即，无已登记 Server） | `IB_MCP_SECRET_KEY` 已设；无 Server | A + U；DEPLOY-005 完成后 | **MV-05**（= V-11，目标机探针，gating）；**MV-10**（= V-13，线程核对，只读，ib-web 重启 ≥ 45 s 后）；**MV-01 的页面部分**（浏览器打开 `#/system/mcp`：页面可打开、仅 admin 可见；凭证输入框 `type=password`；传输下拉只有 `streamable_http`）；**MV-02 / MV-03 的页面部分**（配置页外部工具区在无可见外部工具时不渲染；非 admin 看不到 MCP 系统页） | 不登记任何 Server、不产生外部出站；V-01~V-11 与 V-13 全绿 + Stage 1 页面项通过 ⇒ 可判 `DEPLOYED_SUCCESSFULLY` |
| **Stage 2**（用户提供真实 MCP Server 并已放行出站 ACL；PRE-08 第 5 项） | 测试项目 + 真实 Server（只放行 `read_only` 工具） | U 操作页面、A 在目标机取证；用户在场 | **MV-01 完整流程**（登记 → 测试连接 → 启用 → 发现 → 审核 → 开放；登记 bearer / header 型 Server 不返回 `409 secret_key_missing` 即证明主密钥已加载）、**MV-02**（配置页勾选外部工具、失效徽标、风险置灰）、**MV-03**（删除对话框输入标识名二次确认并勾选"强制删除"，授权清理；对象为测试 Server）、**MV-06**（真实 Server 互通，modern / legacy 协商）、**MV-04**（函数名约束探针）、**MV-08 / MV-09**（长连接与 HTTPS 流式路径）、**MV-07**（最后做，会再重启 ib-web） | 依赖真实 Server；未能提供 ⇒ 全部标 `NOT_TESTABLE`（待人工验证），不得标 PASS |

**V-13 / MV-10 说明（只读；e2e 报告 MV-10 原文："目标机部署后 `systemctl restart ib-web ib-worker`，各自线程转储（`py-spy dump --pid` 或 `ls /proc/<pid>/task/*/comm`）；ib-web 存在 `ib-mcp-supervisor` 线程、ib-worker 不存在 `ib-mcp*`"）**

1. **`/proc/<pid>/task/*/comm` 匹配线程名在 CPython ≤ 3.13 上不可行**：解释器不把 `threading.Thread(name=…)` 写入内核线程名（本机 Python 3.12.3 实测：命名为 `ib-mcp-supervisor` 的线程，其 comm 仍是 `python3`）；线程原生命名自 Python 3.14 起才有 `[INFERRED]`，须以 PRE-04 的 `python -V` 为准。内核 `comm` 上限 15 字节，故即便在 ≥ 3.14，`ib-mcp-supervisor`（17 字节）也会被截为 `ib-mcp-supervis`——匹配口径用**精确行** `^ib-mcp-supervis$`（V-13 命令已采用），泛匹配 `^ib-mcp` 另含探测池 `ib-mcp-probe_N` 与监听线程 `ib-mcp-listen-*`（截断后形如 `ib-mcp-listen-s`）。**因此 `comm_* = 0` 在 Python ≤ 3.13 上是"无信息"，不得据此判 ib-worker 通过**；主判据是线程数差分。
2. **线程数差分**（主判据，`[INFERRED]`）：waitress 工作线程池大小固定，`Supervisor.start()` 立即创建 1 个 daemon 线程 `ib-mcp-supervisor`（`supervisor.py:78-88`，延迟 5–30 s 发生在该线程内部的首轮 tick 之前，**线程本身启动即存在**）；探测池 `ThreadPoolExecutor(max_workers=2)` 的工作线程按需创建，无已启用 Server 时不创建。所以新 ib-web 稳态线程数 = 旧 ib-web 线程数 `W_OLD` + 1。该差分对"同代码、同配置的稳态"成立；若 V-13 前有人登记并启用了 Server，则不适用（Stage 1 约束：无 Server）。
3. **等待时机**：监督线程启动即在；首轮 tick（5–30 s 随机延迟后）在无 Server 时不产生新线程。取 **`RESTART_TS` 之后 ≥ 45 秒**（30 s 上限 + 余量 `[INFERRED]`）执行，既覆盖首轮 tick，也避开 waitress 启动期线程数波动。Stage 2 的 MV-07/08/09 会再重启 ib-web，其后的线程数不再与 `W_OLD` 比较。
4. **可选复核（U，需 sudo；`py-spy` 未登记 `[TOOL_UNREGISTERED]`，仅当用户目标机已装有）**：`sudo py-spy dump --pid "$(systemctl show -p MainPID --value ib-web)" | grep -c 'ib-mcp-supervisor'`（期望 1）；同样对 ib-worker（期望 0）。py-spy 不由代理安装，装不装由用户决定；无 py-spy 时以线程数差分为准。**执行者划分**：V-13 命令不需 sudo，由 A（代理经 ssh）执行；若 `/proc/<pid>/task` 因 hidepid / 权限读不到（`Permission denied`），改由 U 加 `sudo` 执行同一脚本；py-spy 复核一律 U。
5. **诚实边界**：本轮 ib-worker 不重启，V-13 对 ib-worker 的核对只证明"未重启的旧进程没有 MCP 线程"（旧进程根本没有 `ib.mcp` 代码，近乎平凡成立），**不能**替代"新代码下 ib-worker 重启后无 supervisor"这一 DEF-R29-008 的真实进程验证；后者仅由可选 DEPLOY-006b 或下次 ib-worker 自然重启后补做，报告中该半边标 `NOT_TESTABLE`（待人工验证，计入遗留），不得标 PASS。

**Stage 2 目标机取证命令（A，随 U 的页面操作配合；全部只读 / 只用已有重启权限）**

- **MV-06**（真实 Server 互通）: U 在页面完成登记 / 测试连接 / 启用 / 发现 / 审核；A 取证：`ibssh bash -s -- "$T0" <<'EOF'` 体 `journalctl -u ib-web --since "$1" --no-pager | grep -iE "mcp|protocol|handshake|discover" | tail -n 40`（`$T0` = 操作开始时刻；日志事件名 `[INFERRED]`，按实际输出记录）；页面显示 `protocol_era`（modern / legacy）与发现的工具数；一次授权后的真实调用在 `#/system/mcp` 审计页有 `outcome` 成功行。通过标准同 e2e 报告：协商、发现、调用成功；出站 ACL 已放行。
- **MV-04**（函数名约束探针；U + 真实 DeepSeek Key，**由用户执行，计划不读取 Key**）: 通过产品路径完成——在测试项目的 agent 上授权上一步审核通过的只读工具（其注册名形如 `mcp__<server>__<tool>`），向该 agent 提一个会触发该工具的问题；成功标准 = LLM 端点接受该函数名（该回合无 LLM 4xx / 无 `invalid function name` 类错误，审计页该次调用有记录，journal 无 LLM 请求失败）。边界覆盖：选用 / 构造使注册名长度尽量接近 64 字符且含 `-` 与 `_` 的 `server_id`（`[A-Za-z0-9_-]`），页面工具目录会显示最终 `local_name` 与长度；**若所测最大长度 < 64，如实记录"已验证到 N 字符，64 字符边界未验"**。此项为架构 A-R29-2 / TBD-R29-2 的唯一实测，**不得用合成替身通过**。
- **MV-08**（长连接 `list_changed` + 重启无残留；真实 Server）: ① U 在页面启用该 Server（监听线程启动）；A 记录 `ib-web threads=<n1>`（V-09 同款命令）；② 服务方推送 `list_changed` → U 观察工具进入"待复审"，记录耗时（期望秒级）；A：`journalctl -u ib-web --since "<推送时刻>" --no-pager | tail -n 30` 取证；③ A 执行重启并计时：同 DEPLOY-004 命令（含 `ready_after_s`），另取 `journalctl -u ib-web --since "$TS" --no-pager | grep -E "timed out|SIGKILL|Failed|Main process exited|Traceback|SSLError" | tail`；期望：`ready_after_s` 在预算内（`TimeoutStopSec=30`，ib-web.service:68，停止不触发 `stop-sigterm timed out`）、无 `SIGKILL`、无未处理异常。
- **MV-09**（HTTPS 流式路径，DEF-R29-006 / 007 自动化仅覆盖回环明文）: 同 MV-08 但目标为 `https://` Server：① 登记并启用（modern 形态，保持 `subscriptions/listen` 长连接；私有 CA 时先做 DEPLOY-007）；② 服务方推送一条小的 `list_changed` 且**不关闭连接**，计时 ≤ 约 2 s 使工具进入"待复审"且只触发一次（不是等流关闭 / 周期复核）；③ U 在页面停用该 Server（或 A 重启 ib-web），A 对比线程数：`ib-web threads` 在停用后回到启用前 `n0` 附近（监听线程退出，`[INFERRED]` 以 `/proc/<pid>/task` 条数近似），服务端日志（用户在服务方观察）可见连接断开，`journalctl` 无未处理的 `ssl.SSLError` / `AttributeError` / `ValueError`（grep 同上）；④ 另测服务方先静默再断开：线程正常结束、无残留。通过标准同 e2e 报告 MV-09 ②③④。
- **MV-07**（最后做）: 前提 = 所有已登记 Server 均不可达（用户让其不可达：停服务或阻断出站 ACL；**计划不改防火墙**）。A 执行 DEPLOY-004 的重启命令（取新 `RESTART_TS`），记录 `ready_after_s` 并与 DEPLOY-004 空载基线比较；日志无 `Traceback`；supervisor 的首轮探测为延迟 / 非阻塞，启动应成功。通过标准同 e2e 报告：启动成功；耗时增量记入校准（校准前标"未验收"）。验证后用户恢复 Server 可达（或在页面停用 / 删除测试 Server）。

**通过标准（E2 状态映射）**：V-01~V-11 与 V-13 机器可验项全部通过 **且** Stage 1 页面项（MV-01/02/03 的页面部分）完成并通过 → `DEPLOYED_SUCCESSFULLY`；机器可验项通过但 Stage 1 页面项未完成 / 不通过 → `DEPLOYED_WITH_ISSUES`。Stage 2（MV-04/06/07/08/09 与 MV-01~03 的完整流程）属依赖真实 Server 的后续步骤，其结果单独记录，不影响首发的最终状态；未执行项在报告中标 `NOT_TESTABLE`（待人工验证）而非 PASS，并列入遗留问题。协议 §K：只要仍有未完成的人工验证，整体交付状态至多 `DELIVERED_WITH_ISSUES`（e2e 报告已声明 MV-01~09 为 NOT_TESTABLE 的"待人工验证"，MV-04 的 `[UNSOURCED]` 函数名字符集在 MV-04 完成前保持开放）。

- 回滚后的验证：V-01、V-05（`/healthz/deps` 键集 = PRE-04）、V-06（应为 404，证明新接口已移除）、V-08（hash 等于 PRE-04 旧值或新重建值）、V-09；V-12、V-13 不再适用（回退代码后 ib-web 线程数应回到 `W_OLD` 附近，可顺带记录）。
- 验收中的写入全部在测试项目；验收后用"版本 → 回滚"复原并删除测试 Server（I-3）。

## 用户需要执行的动作（汇总，代理不代做）

| # | 动作 | 时机 | 要点 |
|---|---|---|---|
| U-1 | commit + push 本轮代码（经主会话），确认 CI 全绿且 Fernet 契约无 skipped | E2 授权前 | 含全部未跟踪新文件；之后才给 `DEPLOY_COMMIT` |
| U-2 | PRE-05 台账备份（ib-web 身份、只拷贝） | DEPLOY-002 之前 | 备份后核对大小 / 属主 / `integrity_check` |
| U-3 | PRE-06 只读核查（无 `mcp__` 授权、无 `mcp_*` 表） | DEPLOY-002 之前 | 命中 >0 则停止 |
| U-4 | PRE-07 env 键存在性计数 | DEPLOY-001 之前 | 只出数字，不回显 |
| U-5 | **DEPLOY-001：生成并追加 `IB_MCP_SECRET_KEY`** | DEPLOY-004 重启之前（建议 PRE 全部通过后立即） | 用官方命令生成；不 echo；核验长度 44；自行保管副本 |
| U-6 | PRE-03 `cryptography` 不满足时升级 | 仅失败时，PRE-03 之后 | 用户 sudo 会话；代理不安装依赖 |
| U-7 | Stage 1 页面项（MV-01/02/03 页面部分）+ V-04、V-10、V-11 第三项 | DEPLOY-005 之后 | 用测试项目与 admin 账号 |
| U-8 | Stage 2：提供真实 MCP Server、放行出站 ACL、（私有 CA 时 DEPLOY-007）、页面登记 / 审核 / 开放、MV-04 / 06 / 07 / 08 / 09 的服务方侧操作 | Stage 1 通过后 | 只放行 `read_only` 工具；不动业务项目 |
| U-9 | 所有需 sudo 口令的动作；`daemon-reload` / `nginx reload`：本轮不需要 | — | Q5 |

## 下游产物同步核对（M-DE-001 / 003 / 004 / 008；本组只读核对，未改任何交付物）

| 产物 | 核对方法与结论 | 处置 |
|---|---|---|
| `.github/workflows/ci.yml` | `git diff HEAD` +33/-0：作业级 `IB_REQUIRE_CRYPTO: "1"`（:54）+ 010 迁移检查块（单源 / 001~009 仍在 / 头注释含 `MANUAL_ROLLBACK_REQUIRED` 且无可执行 `DROP` / 重放两遍幂等 / `missing_mcp_tables` / 两个 CHECK 反例 / 老库形态）。与 module_design「对 selfcheck / CI 门的影响」一致 | 无需修改 |
| `src/deploy/checklists.txt` | 1.1.0 重新逐行核对 `[B30]`（:629-644）与签署行（:653）：`B1–B27` 签署行保留（P-DE-001），表名 9 个与 010 一致，env 键 5 个与 `env.example` 一致。**OI-1 已关闭**：B30(3)（:639）现为 "只 `npm run build`，不 `npm ci`"；**OI-2 已关闭**：B30(2)（:632-635）现含 venv 绝对路径与 `sudo grep` / `sudo awk`；OI-3 保留（B30(5) 与 ROLLBACK-000 同向）。**仍有差异 OI-7**：B30(2)（:632）仍写"先 `…/pip install -r src/requirements.txt`"，与 PRE-03（先核对；不满足才由用户升级）不一致 | **以本计划 PRE-03 为准**；本组不改 checklists；记入 cicd_pipeline OI-7，建议下一轮 software-developer 将 B30(2) 改为"先核对，不满足时由用户升级"（同时维持 `B1–B27` 签署行断言，P-DE-001）。E2 执行时遇到 checklists 的 `pip install -r` 一律按 PRE-03 处理，不得由代理安装 |
| `src/deploy/env.example` | 5 个新键均为注释行，主密钥占位 `<REPLACE_ME_fernet_key_set_on_target_host_only>`，无真实值；与 module_design / checklists 一致；`ib-worker.env.example` / `ib-embed.env.example` 无改动 | 无需修改；不被服务读取，目标机 env 由用户维护 |
| `src/deploy/systemd/ib-web.service` | 未改；核对 `ExecStartPre`（:47）、`WorkingDirectory`、`EnvironmentFile`（:44）、`--port=18080`（:51）、`TimeoutStopSec=30`（:68）、`MemoryMax=1024M`（:70）与本计划一致 | 无需修改；PRE-02 CLASS-X 机械复核 |
| `src/deploy/nginx/*` | 未改；MCP 出站调用不新增入站流式端点，SSE 反代条件不涉及（module_design） | 无需修改 |
| `src/requirements*.txt` | 各 +`cryptography>=42,<51`（带注释），两份一致；`requirements-embed.txt` 未触碰（torch 永不进基座）；PRE-02 过滤 `cryptography` 行与注释行 | 无需修改；目标机仅核对 |
| `package.json` / `package-lock.json` | 无改动 → 不执行 `npm ci` | 无需修改；PRE-02 复核 |
| `010_mcp.sql` | 头注释含 `MANUAL_ROLLBACK_REQUIRED` 回滚说明、无可执行 `DROP`；9 张表与 4 索引同 module_design「数据迁移」；与 `mcp_ddl_script()` 单源一致（CI 门 + selfcheck 双重断言） | 不改 |
| `docs/deployment_plan.md`（REV-21 基线）、`deployment_report.md` | 只读 | 未改 |

## 待修正项 / 开放问题（汇总，需 PM / 后续 GROUP 处置）

1. **OI-5 — 已关闭（1.1.0）**：DEF-R29-008 已修复并验证（GR-C-006、GR-D-004；`composition.py:881-895` / `wsgi.py:33` / TC-INT-R29-1100~1105）。残留：自动化未起真实进程 → 部署后 V-13（MV-10）补验 ib-web 半边；ib-worker 新代码路径的真实进程验证 = `NOT_TESTABLE`，仅在可选 DEPLOY-006b 或下次 ib-worker 重启后补做（见 DEPLOY-006）。
2. **OI-1 / OI-2 — 已关闭（1.1.0）**：`checklists.txt [B30]` 已订正（`npm ci`、`sudo`、venv 路径），逐行核对见「下游产物同步核对」。**OI-3 保留**（B30(5) 措辞与 ROLLBACK-000 同向，无冲突）。**OI-7 新增（GR-C-006-F03，待下轮同步）**：`[B30](2)` 的 `pip install -r src/requirements.txt` 与 PRE-03"核对而非安装"不一致——**口径以 PRE-03 为准**（先核对；仅当 `cryptography` 不在 `[42,51)` 时由用户在 sudo 会话中升级），交付物待 software-developer 下轮同步，本组不改。另 GR-C-006-F02：`manage.py runserver` 不再启动 supervisor（仅开发期影响，不涉及生产部署）。
3. MV-04 无专用探针脚本（e2e 报告未指定方法）：本计划采用"经产品路径 + 真实 Key 由用户执行"的方式；若用户要求直连 LLM 端点的专用探针，需另行提供（涉及 Key 处理，不由代理读取）。
4. CI 数字（`1767 passed, 0 skipped`、单元 `1097`、selfcheck 77/77）为由本机实测（`1761 passed, 6 skipped`、76/77）推算，首次 push 后以 CI 实际为准（cicd_pipeline）。
5. **MV-10 执行口径变更**：e2e 报告 MV-10 原文的 `/proc/<pid>/task/*/comm` 方法在 CPython ≤ 3.13 不可行，已在 V-13 改为线程数差分 + 条件性 comm + 可选 py-spy；建议 test-engineer 下轮在人工验证清单同步该口径；其"重启 ib-worker"一步按 DEPLOY-006 裁决默认不做。

## `[INFERRED]` 汇总（画像与设计均未给出的取值）

ib-web 不可用 10–30 秒、就绪轮询 60×1 秒（`ready_after_s` 精度 1 秒）；PRE-03 磁盘 / 内存余量（1 GiB / 1 GiB）；构建命令超时 ≥ 300 秒；web root 副本目录 `~/ib-webroot-pre-r29`；定义文档位于 `/var/lib/intelligentbase` 下 `*.json`（PRE-06 扫描假设）；目标机 `cd src` 后 `ib` / `ibweb` 可导入（DEPLOY-003）；`/api/mcp/*` 未鉴权访问返回 401 / 403；旧 `ensure_schema` 不因多余 `mcp_*` 表失败；venv `cryptography` 升级所需权限；`/etc/intelligentbase/mcp-ca.pem` 的属主权限；MCP 相关日志事件名（MV-06 / 08 / 09 grep 关键字）；以 `/proc/<pid>/task` 条数近似监听线程数；CI 预期数字（`1767 passed, 0 skipped`）；V-13：`W_OLD + 1` 线程差分与 ≥ 45 s 等待、Python ≥ 3.14 才命名内核线程、`/proc` 可由部署用户读取；DEPLOY-006b 的 45 s 等待、重启会中断进行中入库批次、ib-worker 稳态线程数重启前后一致。
`[TOOL_UNREGISTERED]`：`gh`（仅 PRE-00 取证便利，网页可替代）。
