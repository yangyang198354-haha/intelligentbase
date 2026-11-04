<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-04T14:40:50+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/tech_stack.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/e2e_test_report.md</file>
    <file>docs/sdlc/intelligentbase/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：REV-28 平台级内置「顾问 agent」+ DeepSeek 联网（INCREMENTAL，仅计划）

## 修订记录

| 版本 | 时间 | 内容 |
|---|---|---|
| 1.0.0 | 2026-11-04T11:12:54+08:00 | 初版（APPROVED）。 |
| 1.1.0 | 2026-11-04T14:40:50+08:00 | 定向修订（`REWORK_AUTHORIZED`），落实用户裁决 CP-004（「Q1: A，其他按照推荐」，经主会话转述）：Q1~Q6 全部改为「已裁决」并落到步骤。(1) DEPLOY-005 固定为不执行（`INCLUDE_WORKER_RESTART` 缺省 false，不再作为授权选项）；(2) PRE-02 判 CLASS-E 时固定为：先单独发布前序 ib-embed 提交，再重跑本轮预检；DEPLOY-006 不与本轮同批（原选项 ②③ 作废）；(3) 首发联网全关，OPT-A（DEPLOY-007）需用户在主会话另行单独授权，OPT-B（DEPLOY-008）本轮不启用；(4) MV-15 与 MV-16 的破坏性分支在 MV 排期中标「推迟（维护窗口）」，只做无破坏部分；(5) PRE-03 lxml 不满足时由用户在 sudo 会话升级，写入失败处置；(6) 009 的 checklists `B30` 由 software-developer 下一轮补，本轮签署以 selfcheck `web_governance_schema_single_source` + CI 009 门为准；(7) DEF-003 已按用户裁决关闭（理解步骤异常 fail-open 为设计行为），无计划影响；(8) 测试基线 1355 → 1358 passed。DEPLOY/ROLLBACK 编号与命令未变。 |

> **本文件不执行任何步骤。** 本组未 ssh、未部署、未 commit / push、未读取生产；GROUP_E2 未授权。下列命令是将来 E2 获得 `PRODUCTION_DEPLOY_CONFIRM=true`（环境名 `production`）后才可执行的**计划内容**。
> REV-27 版本归档于 `archive/rev27/deployment_plan.md`（只读）；本文按 REV-28 整体重写，沿用其执行约定（引号规则 Q1~Q6）、CLASS 门、回滚结构与验证脚本风格。`docs/deployment_plan.md`（REV-21 基线）与 `deployment_report.md` 不改。
> 依据：画像 P7/P8/P9/P11-3、`.claude/skills/ib-prod-deploy/SKILL.md`（§1–§9）、`module_design.md` 3.0.0「数据迁移」「受影响的运行单元」「对 selfcheck / CI 门的影响」、`implementation_plan.md` 4.0.0、`e2e_test_report.md` 2.0.0「人工验证清单」MV-01~MV-16、`src/deploy/migrations/009_web_governance.sql`、`src/deploy/env.example`。
> 测试门控：invocation 载明 GROUP_D 已通过（PM 复跑，未提交工作区：`pytest tests` 1358 passed；selfcheck 68/69，失败项 `core_framework_free` 环境性既有；前端 build rc=0、160/160）。

## 给 PM 的部署计划摘要（供将来向用户请求 E2 授权）

| 项 | 内容 |
|---|---|
| 目标环境 | `production`（单台物理机 192.168.31.133，SSH 密钥；画像 P7"部署需用户确认=是"）。无 staging。**当前未授权。** |
| 待部署提交 | `DEPLOY_COMMIT` = **待定**：本轮代码仍在未提交工作区（HEAD `8d6fd4b`；33 个已修改 + 38 个未跟踪的 `src`/`tests` 文件）。须先由主会话在用户确认后 commit + push（含新文件，尤其 `009_web_governance.sql`、`src/ib/advisor/`、`src/ib/webtools/`、`src/ib/ledger/web_governance.py`、`src/ib/expert_seeds/advisor.md`），E2 授权时由 PM 写入 40 位哈希 |
| 策略 | **recreate**（画像唯一允许）：重启 ib-web（约 10–30 秒不可用 `[INFERRED]`，丢内存态聊天会话）；前端静态发布无停机。**首发 `IB_WEB_SEARCH_PROVIDER=none`（缺省）、`IB_WEB_FETCH_ENABLED=0`（缺省）**：不改 env 文件即联网全关，行为同现状（用户裁决 Q3）；Stage 1 人工验证通过后，OPT-A（DEPLOY-007）须用户在主会话**另行单独授权**；OPT-B（DEPLOY-008）本轮不启用 |
| 步骤数 | 预检 PRE-00~08（含用户执行项 U）；**部署 4**：DEPLOY-001 git pull → 002 依赖/导入核对（只读闸）→ 003 重启 ib-web（迁移 009 自动应用）→ 004 前端构建发布；**本轮不执行的步骤**：DEPLOY-005 重启 ib-worker（Q1 已裁决：不执行）、DEPLOY-006 重启 ib-embed（Q2 已裁决：若需要则先单独发布，不与本轮同批）、OPT-B（DEPLOY-008，本轮不启用）；**后续需另行授权**：OPT-A（DEPLOY-007，启用 DeepSeek 搜索）；回滚 ROLLBACK-000（用户前置）/001a/001b/004/003/005/006/007/008 + 迁移撤销 ROLLBACK-009 |
| 重启范围 | ib-web：**重启**（`ib.*` / `ibweb.*` 代码、迁移 009、依赖声明，module_design）。ib-worker：**不重启**（Q1 已裁决；共享包 `ib.ledger` 仅追加建表，无行为变化——module_design 结论）；ib-embed / qdrant / nginx：不动 |
| 迁移 | 009 `web_governance`（新增单行表，`IF NOT EXISTS` 幂等），随 `ib-web` 重启的 `ExecStartPre … --ensure-schema` 自动应用；**回滚 = `DROP TABLE web_governance;`，`[MANUAL_ROLLBACK_REQUIRED]`**（用户在备份后执行；代码回退后留表无害，通常不需要 DROP） |
| 生产当前版本 | **未知，不得假定。** 仓库近期提交含 ib-embed 预热与路由重试（`ae07f44`、`47f19a3`，触及 `src/ib_embed/server.py`、`src/ib/routing/semantic.py`、`src/deploy/ib-embed.env.example`）及配置页条件分支（`8d6fd4b`，前端）；它们是否已上线未在计划输入中核实。PRE-01 必须在目标机实测 `git rev-parse HEAD` 作为**回滚锚点 `ANCHOR`**，PRE-02 的 CLASS 门据 `ANCHOR..DEPLOY_COMMIT` 机械分类 |
| 不变面 | `/etc/intelligentbase/*.env`（首发零改动，不读取不回显）、systemd unit（无 `daemon-reload`）、nginx（不 reload）、`/var/lib/intelligentbase/` 现有数据（除 009 新增表外只读）、`package.json` / `package-lock.json`（故不 `npm ci`）、qdrant、bge-m3 权重 |
| 不可逆 / 需人工 | 迁移 009 撤销（见上）；验收中在测试项目产生的配置版本 / 审计只增不删；启用 deepseek 后的搜索按次计费；`ROLLBACK-000`（回滚代码前须先清除含 `web_search` / `web_fetch` 授权的项目配置，否则旧代码启动校验 `tool_grant_tool_unknown`，见「不可逆步骤汇总」） |
| 需要用户（非代理）执行 | ① 待部署提交 commit + push（主会话经用户确认）；② PRE-05 台账迁移前备份；③ PRE-06 只读核查生产定义中无名为 `advisor` 的专家（OQ-ARCH-R28-02）；④ PRE-07 DeepSeek Key / 环境键「存在性计数」（只出数字）；⑤ 首发之后 **OPT-A 的 `ib-web.env` 编辑**（OPT-B 本轮不做）（只写键名与建议值，不写凭据）与出站 ACL；⑥ 浏览器人工验证 MV-01~16；⑦ 需要 sudo 口令的一切动作（Q5）。`daemon-reload` / unit 安装 / `nginx reload`：本轮均不需要 |
| 前提（E2 授权时由 PM 填入 `special_instructions`） | `PRODUCTION_DEPLOY_CONFIRM=true`；环境名 `production`；`DEPLOY_COMMIT=<40 位>`；计划版本 = phase_status 登记的 APPROVED 版本；`INCLUDE_WORKER_RESTART` 缺省 false 且本轮不授权（Q1）；`INCLUDE_EMBED_RESTART` 本轮不使用（Q2：CLASS-E 时先单独发布前序提交）；OPT-A 需用户在主会话**另行单独授权** `ENABLE_WEB_SEARCH=true`，且其 env 编辑已由用户完成并口头确认；OPT-B 本轮不授权 |

## 变更摘要

| 组件 | 文件（以 `git diff --name-only` / 未跟踪清单为准） | 迁移 | 构建 | 需重启 / 发布的运行单元 |
|---|---|---|---|---|
| 核心类型 / 端口 / 配置域 / 编排 / 运行时 | `src/ib/{core,config,experts,orchestration,runtime,tools,llm,builder,observability}/…` | 无 | 无 | ib-web 重启 |
| 联网工具 / 顾问核心（新） | `src/ib/webtools/`（含 `deepseek.py`、`fetch.py`、`netguard.py`、`gate.py`…）、`src/ib/advisor/`、`src/ib/expert_seeds/advisor.md`、`src/ib/ledger/web_governance.py`、`src/scripts/advisor_eval.py`（目标机手工运行，非服务） | 无 | 无 | ib-web 重启 |
| 台账 | `src/ib/ledger/{schema.py,__init__.py}`、`src/deploy/migrations/009_web_governance.sql`〔新〕 | **009**（新增表 `web_governance`） | — | ib-web 重启时 `ExecStartPre` 自动应用 |
| Web | `src/ibweb/{composition,config_views,urls,views}.py`（新增 `GET/PUT /api/web-governance`，仅 admin） | 无 | 无 | ib-web 重启 |
| 依赖 | `src/requirements.txt`、`src/requirements-offline.txt`（各 +`lxml>=5.0,<7.0`） | — | 目标机 venv 仅**核对** lxml 版本（DEPLOY-002），不安装 | 同上 |
| 前端 | `ProjectsPage.vue`（新建项目「启用顾问」）、`ConfigStudio.vue`、`AgentDetailPanel.vue`、`ConsoleLayout.vue`、`router/index.ts`、`api/client.ts`、`advisorPlan.ts`〔新〕、`WebGovernancePage.vue`〔新〕 | 无 | 目标机 `npm run build`；lock 未变，不 `npm ci` | 不重启；拷贝到 `/var/www/intelligentbase/` |
| 部署模板 | `src/deploy/env.example`（+联网三键注释，无凭据） | — | — | 仓库文件，不被服务读取；**目标机 env 首发不改** |
| 自检 / CI / 测试 | `src/scripts/selfcheck.py`、`.github/workflows/ci.yml`、`tests/**`、`src/frontend/tests/advisor_r28.test.js` | — | — | 非运行时交付物 |
| systemd / nginx / ib-embed / qdrant | **无改动**（module_design） | — | — | 无（例外见 PRE-02 CLASS-E：区间可能带入前序提交的 ib-embed 改动） |

**"改什么重启什么"核对（SKILL.md §6）**：`ibweb/**` → ib-web ✓（DEPLOY-003）；前端 → 不重启、build + 拷 web root ✓（DEPLOY-004）；迁移 → 随 ib-web 重启 ✓；`ibweb/worker.py` / 入库链路 → 本轮**无改动**，故 ib-worker 不重启（`ib.ledger` 追加建表无行为变化，见条件步骤 DEPLOY-005 的取舍）；`/etc/intelligentbase/ib-web.env` → 首发无改动，OPT-A / OPT-B 才需（用户编辑 + 重启 ib-web）；`src/deploy/systemd/*`、`nginx/*` 无改动 ✓。

## 目标环境与策略

- **环境**：`production`（画像 P7）；SSH 密钥 `~/.ssh/ib_prod_ed25519`，主机 / 用户见 SKILL.md §1–§2（外网备用入口 §8.1）。不设计 staging。
- **策略：recreate**。理由：单机、单实例，无负载均衡与第二套环境。顺序按依赖：数据层（迁移 009，随 ib-web 启动）→ 服务层（ib-web 重启）→ 前端（避免新前端先于新接口上线，`/api/web-governance` 与 `enable_advisor` 参数在旧后端不存在）。
- **预计停机**：ib-web 约 10–30 秒 `[INFERRED]`（`TimeoutStopSec=30` + 启动 + `ExecStartPre` 建表）；内存态聊天会话丢失（选无人时段）；前端发布窗口 ≤ 数秒；旧页面需硬刷新（Ctrl+F5）。
- **首发上线形态**：联网全关。依据 module_design：未设置联网三键 = `none` / `0` / `sqlite`，`/healthz/deps` 与基线逐字节相同（`egress_web` 为空），`GET /api/config/catalog` 仅多出 `web_search`、`web_fetch` 两个工具项（预期变化）。**既有项目不迁移**（定义文档与提示词文件逐字节不变，AC-003-04），顾问仅在新建项目勾选或配置页保存后才进入某项目。
- **兼容性**：未启用顾问的项目走原路径（module_design 兼容性论证 #1~#14）；唯一需用户知悉的可见差异是目录接口多两个工具名。

## 执行约定（引号与变量）

执行端为 bash（Git Bash / Linux），**不要**把复杂命令作为参数从 PowerShell 传入（SKILL.md §4.2）。

```bash
# 连接函数（密钥 / 主机 / 用户见 SKILL.md §1-2；BatchMode 保证绝不回落到口令交互）
ibssh() { ssh -i ~/.ssh/ib_prod_ed25519 -o UserKnownHostsFile=/tmp/ib_kh -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@192.168.31.133 "$@"; }
```

| 规则 | 说明 |
|---|---|
| Q1 | 不含本地值的远端命令：整条放进**单引号**，`$VAR` 在**远端**展开。 |
| Q2 | 需要本地值（`ANCHOR`、`DEPLOY_COMMIT`、`REVERT_COMMIT`、`PULL_TS`）：一律 `ibssh bash -s -- "$A" "$B" <<'EOF' … $1 $2 … EOF`——本地双引号只把值作为**位置参数**传过去，heredoc 用单引号定界使本地不展开，远端用 `$1 $2`。**禁止** `ibssh 'git checkout $ANCHOR -- …'`（远端为空）。markdown 里 heredoc 代码块须顶格粘贴。 |
| Q3 | 单引号内有意在远端定义并使用的变量（如 `TS=$(date …)`）是远端变量，属预期。 |
| Q4 | 变量取值与核验：`ANCHOR` = PRE-01 输出的 40 位 `git rev-parse HEAD`；`DEPLOY_COMMIT` = PM 在 `special_instructions` 下发；`REVERT_COMMIT` = ROLLBACK-001a 产生。使用前本地核验 `[[ "$X" =~ ^[0-9a-f]{40}$ ]]`，远端 `git cat-file -t "$X"` 必须输出 `commit`（PRE-02 / ROLLBACK-001b 内置）。 |
| Q5 | 凡需 sudo 口令的动作（台账备份 / 只读核查、编辑 env、`DROP`）由用户在交互式会话中执行；**禁止** `printf '<口令>' \| sudo -S`；**不读取、不回显** `/etc/intelligentbase/*.env` 的值（只允许 `grep -c` 之类的"计数"，且由用户执行）；**禁止** scp / pscp / rsync 向生产传代码。 |
| Q6 | 凭据、令牌（含 DeepSeek Key）只写存放位置，不写值；本仓库 PUBLIC，本文不含任何凭据。 |
| Q7 | 参与"线上代码版本"判据的 Python 命令一律 `python -B` / `PYTHONDONTWRITEBYTECODE=1`，避免在部署树写 `.pyc` 污染判断（SKILL.md §7.1）。 |

## 预检清单

执行者：`A` = devops 代理经 ssh（E2 授权后）；`U` = 用户；`M` = 主会话。任一项不通过：**停止，不进入 DEPLOY-001**（目标环境尚无变更，报告 `DEPLOYMENT_FAILED`，无需回滚）。

| ID | 检查项 | 执行者 | 通过标准 |
|---|---|---|---|
| PRE-00 | 待部署提交已在远端；无遗漏的未跟踪文件；**该提交 CI 全绿**（含 009 迁移门） | M | 见下 |
| PRE-01 | 目标机 HEAD 记录为**回滚锚点**；已跟踪文件无本地修改 | A | HEAD 为 40 位哈希且记入报告；无 ` M` 的已跟踪文件 |
| PRE-02 | **变更集分类门（CLASS）**：区间 `ANCHOR..DEPLOY_COMMIT` 的文件类别符合预期；与目标机本地修改无交集 | A | `CLASS=A` 方可继续；`E` / `X` 见下 |
| PRE-03 | 磁盘 / 内存 / 工具链 / **venv lxml 版本**（TBD-R28-3） | A | 盘余量 ≥ 1 GiB、可用内存 ≥ 1 GiB `[INFERRED]`；node / npm 可用且 node 主版本 22；lxml 版本满足 `>=5.0,<7.0` |
| PRE-04 | 服务与页面基线（对照用） | A | 5 个单元 active；记录 ib-web / ib-worker / ib-embed 的 `ActiveEnterTimestamp`、`NRestarts`、ib-web `MemoryCurrent`；记录 `/healthz/deps` 的顶层键集；记录 web root `index.html` 的 sha256 与引用的 `assets/index-*.js`；`~/ib-webroot-pre-r28` 不存在 |
| PRE-05 | **台账迁移前备份**（用户执行） | U | 备份文件存在、非空、`integrity_check` 为 ok、`documents` 行数与主库一致 |
| PRE-06 | **只读核查**：生产定义文档与提示词目录中**没有**名为 `advisor` 的专家（OQ-ARCH-R28-02 / R-6） | U | 输出"命中 0"；命中 >0 → **停止**，报 PM（保留名冲突会让存量专家被当作"顾问模式"） |
| PRE-07 | DeepSeek Key 存在性与 env 键现状（**只出数字**，不读值） | U | Key 来源 ≥ 1（台账 `llm_key` 行数 或 `IB_LLM_API_KEY` 行数）；`IB_WEB_*` 键行数 = 0（首发不应已存在）；显式设置了非 `api.deepseek.com` 的 `IB_LLM_BASE_URL` 行数 = 0 |
| PRE-08 | 验收前置（见下） | U | 用户书面确认 |

### PRE-00（开发机 / 主会话）

```bash
git status -sb | head -n 3                                            # 期望 main...origin/main，无领先落后
git ls-remote origin refs/heads/main                                   # 首列必须 == DEPLOY_COMMIT
git ls-files --others --exclude-standard src tests .github | wc -l     # 期望 0（新文件均已入库）
git ls-tree -r --name-only "$DEPLOY_COMMIT" | grep -cE '^(src/deploy/migrations/009_web_governance\.sql|src/ib/webtools/fetch\.py|src/ib/webtools/deepseek\.py|src/ib/advisor/compose\.py|src/ib/ledger/web_governance\.py|src/ib/expert_seeds/advisor\.md|src/frontend/src/views/WebGovernancePage\.vue|src/frontend/src/components/config/advisorPlan\.ts)$'   # 期望 8
gh run list --commit "$DEPLOY_COMMIT" --workflow CI --json databaseId,status,conclusion --limit 5   # 须有 status=completed 且 conclusion=success
```

- **CI 门（E2 前置条件）**：本轮代码尚未 push，CI 未跑过。push 后必须在 `DEPLOY_COMMIT` 上看到 `completed / success`；红灯、仍在运行、或未触发均**不得部署**。特别关注 PIPE-02（009 迁移门）与 PIPE-07（runner 上 selfcheck 预期 69/69）。`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`；本机无 `gh` 或未登录 → 在 GitHub Actions 网页核对，等价；无法核对 → 标"未验证"并请用户确认，不得默认通过。
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
[ "$(git cat-file -t "$1")" = commit ]
git fetch origin main
[ "$(git cat-file -t "$2")" = commit ]
[ "$(git rev-parse origin/main)" = "$2" ]                # 远端恰为待部署提交
git merge-base --is-ancestor "$1" "$2"                   # 锚点是祖先 => ff-only 可行
[ "$1" != "$2" ] || { echo "ANCHOR==DEPLOY_COMMIT: 无代码变化，停止并核对是否已部署"; exit 3; }
CH=$(git diff --name-only "$1" "$2")
echo "changed_files=$(printf '%s\n' "$CH" | grep -c .)"
# 类别（互斥，按优先级）
X=$(printf '%s\n' "$CH" | grep -E '^(src/deploy/systemd/|src/deploy/nginx/|src/deploy/config\.example\.json|src/requirements-embed\.txt|src/frontend/package(-lock)?\.json)' || true)
MIGX=$(printf '%s\n' "$CH" | grep -E '^src/deploy/migrations/' | grep -vE '^src/deploy/migrations/009_web_governance\.sql$' || true)
E=$(printf '%s\n' "$CH" | grep -E '^(src/ib_embed/|src/deploy/ib-embed\.env\.example$)' || true)
DEPS=$(git diff -U0 "$1" "$2" -- src/requirements.txt src/requirements-offline.txt | grep -E '^[+-][^+-]' || true)
echo "--- CLASS-X 依据(unit/nginx/embed 依赖/前端依赖/009 以外的迁移):"; printf '%s\n%s\n' "$X" "$MIGX" | grep -v '^$' || true
echo "--- CLASS-E 依据(ib_embed 前序提交):"; printf '%s\n' "$E"
echo "--- 依赖清单变动行(期望仅 lxml 两行):"; printf '%s\n' "$DEPS"
echo "--- 本轮预期类别计数: ib/ibweb 后端=$(printf '%s\n' "$CH" | grep -cE '^src/(ib|ibweb)/') migration009=$(printf '%s\n' "$CH" | grep -cE '^src/deploy/migrations/009_') frontend=$(printf '%s\n' "$CH" | grep -cE '^src/frontend/src/')"
echo "--- 与目标机本地修改的交集(期望为空):"
comm -12 <(printf '%s\n' "$CH" | sort) <(git status --porcelain | awk '{print $2}' | sort)
DEPX=$(printf '%s\n' "$DEPS" | grep -vE '^[+-]lxml>=5\.0,<7\.0' | grep -v '^$' || true)
if [ -n "$X" ] || [ -n "$MIGX" ] || [ -n "$DEPX" ]; then echo CLASS=X; elif [ -n "$E" ]; then echo CLASS=E; else echo CLASS=A; fi
EOF
```

| CLASS | 含义 | 处置 |
|---|---|---|
| **A** | 区间含本轮预期类别：后端 `src/ib`、`src/ibweb`、迁移 **仅 009**、`src/requirements*.txt` **仅 lxml 行**、前端 `src/frontend/{src,tests}`、`tests/`、`docs/`、`.claude/`、`.github/`、`src/scripts/`、`src/deploy/env.example`；无其他 | 继续 |
| **E** | 在 A 之外还含 `src/ib_embed/**` 或 `src/deploy/ib-embed.env.example`（目标机落后于前序 ib-embed 预热提交 `ae07f44` / `47f19a3`，它们与本轮同区间落盘） | **停止，不进入 DEPLOY-001**（用户裁决 Q2 已定处置）：先**单独发布**该前序提交——按其既有发布方式（目标机 `git pull --ff-only` 到该前序提交后 `sudo -n systemctl restart ib-embed`，并按 DEPLOY-006 的验证标准确认 `model_loaded=true`、`warm=true`、维度正确、无 `ILL`；`/etc/intelligentbase/ib-embed.env` 须含 `MKL_ENABLE_INSTRUCTIONS=AVX`，SKILL.md §8.11，由用户确认键存在）；该单独发布需 PM 另行下发授权与 `DEPLOY_COMMIT`；完成后以新的 `ANCHOR` **重跑 PRE-01 / PRE-02**，应判 CLASS=A 再进入本轮。**本轮 DEPLOY-006 不与本轮同批执行**；代理不得自选其他处置（原选项「同批 `INCLUDE_EMBED_RESTART`」「接受磁盘领先」已作废） |
| **X** | 出现 unit / nginx / ib-embed 依赖 / 前端依赖锁 / 009 以外的迁移 / 除 lxml 以外的 Python 依赖变化 | **停止**，`DEPLOYMENT_FAILED`（无变更）；本计划不适用（需 `daemon-reload` / `npm ci` / `pip install` / 额外迁移备份），PM 重新规划 |

- 交集非空（目标机对要覆盖的文件有本地修改）→ 停止上报，不 pull。`git fetch` 只更新远端跟踪引用，不改工作树。
- CLASS 门的变动行过滤依赖 `lxml>=5.0,<7.0` 的写法与两份清单一致（实际 diff：各 +1 行，行尾注释不同；`grep -vE '^[+-]lxml>=5\.0,<7\.0'` 以前缀匹配）。

### PRE-03 / PRE-04（A）

```bash
ibssh 'df -B1 --output=target,size,used,avail,pcent /var/www/intelligentbase /opt/intelligentbase "$HOME"; free -m | sed -n 1,2p; node -v; npm -v'
ibssh 'PYTHONDONTWRITEBYTECODE=1 /opt/intelligentbase/venv/bin/python -B -c "import lxml.etree as E; v=E.LXML_VERSION; print(\"lxml\", v); assert (5,0) <= tuple(v[:2]) < (7,0), v"'
ibssh 'date "+%F %T %Z"; systemctl is-active ib-web ib-worker ib-embed qdrant nginx; for u in ib-web ib-worker ib-embed; do systemctl show -p ActiveEnterTimestamp,NRestarts "$u"; done; systemctl show -p MemoryCurrent,MemoryMax ib-web'
ibssh 'curl -s http://127.0.0.1:18080/healthz/deps | python3 -c "import sys,json; print(sorted(json.load(sys.stdin)))"'
ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u; ls ~/ib-webroot-pre-r28 2>&1 | head -n 1'
```

- `"$HOME"`、`"$u"` 位于单引号内，属远端展开（Q1，预期）。lxml 命令内的 `\"` 是本地单引号内的字面双引号，远端 python 看到的是 `"lxml"`。
- lxml 不满足 `>=5.0,<7.0`（或 import 失败）→ **停止**（TBD-R28-3），目标环境无变更，报告 `DEPLOYMENT_FAILED`：按用户裁决 Q5，由用户在交互式 sudo 会话中升级 venv 内 lxml（升级需 venv 属主权限，`[INFERRED]` 需 sudo），完成后口头确认并由 PM 重新发起，从 PRE-03 重跑；代理不安装依赖。
- PRE-04 的 `/healthz/deps` 键集用作 V-05 对照；末行应输出 `No such file or directory`（副本目录尚不存在）。

### PRE-05（U）：台账迁移前备份（同 checklists B28(1) / B29(1) 口径，只拷贝不回显）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)
src = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
dst = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r28.bak")
src.backup(dst)
print("documents:", dst.execute("select count(*) from documents").fetchone()[0],
      "integrity:", dst.execute("pragma integrity_check").fetchone()[0])
dst.close(); src.close(); print("backup done")
PY
sudo ls -l /var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r28.bak
```

- 以 `ib-web` 身份而非 root，避免 `-wal/-shm` 被建为 root 属主（checklists B22）。备份文件应为 `660 ib-web:ib`、非空。`documents:` 计数与主库一致即可（只输出计数）。**回滚迁移 009 之前必须有此备份**。

### PRE-06（U）：只读核查无名为 `advisor` 的专家（OQ-ARCH-R28-02）

定义文档为"每项目一文件 `<dir>/<project_id>.json`"，状态目录 `drwxrws--- ib-web:ib`，部署用户读不了，故由用户 sudo 只读执行。脚本**不打印文件内容**，只打印"含 advisor 专家的文件路径与计数"：

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import json, os
hits = scanned = 0
for root, _dirs, files in os.walk("/var/lib/intelligentbase"):
    for f in files:
        if not f.endswith(".json"):
            continue
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 5_000_000:
                continue
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        ex = d.get("experts") if isinstance(d, dict) else None
        if not isinstance(ex, list):
            continue
        scanned += 1
        if any(isinstance(e, dict) and e.get("name") == "advisor" for e in ex):
            hits += 1
            print("HIT:", p)
print("definition_docs_scanned:", scanned, "advisor_hits:", hits)
PY
sudo find /var/lib/intelligentbase -iname 'advisor*' -not -path '*/blobs/*' 2>/dev/null | head
```

- 通过标准：`advisor_hits: 0` 且 `find` 无输出；`definition_docs_scanned` ≥ 1（为 0 说明路径/格式假设失败，须人工确认定义文档位置，不得当作通过）。

### PRE-07（U）：DeepSeek Key 与 env 键存在性（只出数字）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
print("llm_key_rows:", c.execute("select count(*) from llm_key").fetchone()[0])   # 只数行，不 select secret
PY
sudo grep -c '^IB_LLM_API_KEY=.' /etc/intelligentbase/ib-web.env || true
sudo grep -c '^IB_WEB_' /etc/intelligentbase/ib-web.env || true
sudo grep -E '^IB_LLM_BASE_URL=' /etc/intelligentbase/ib-web.env | grep -vc 'api\.deepseek\.com' || true
```

- 只关心"已配置 / 未配置"：`llm_key_rows` + `IB_LLM_API_KEY` 行数 ≥ 1 即有 Key（DeepSeek LLM 本就依赖它）。**不得读取或回显 Key 值**；这四条命令只输出数字。
- `IB_WEB_*` 行数应为 0（首发即缺省关闭）。非 0 → 停止，由用户说明其含义（可能意外启用联网）。第四条（显式 `IB_LLM_BASE_URL` 但主机非 DeepSeek 的行数）应为 0；缺省未设置时 LLM 主机即 `api.deepseek.com`（env.example:57），OPT-A 才要求它。
- 无 Key（两项皆 0）不阻断首发（联网关闭），但会让 OPT-A 的 `deepseek` 提供方降级——记入报告。

### PRE-08 验收前置（U）

用户书面确认：
1. 已有**独立测试项目**（或同意用新建项目「启用顾问」创建的测试项目）；人工验证**不动生产业务配置**；不在业务项目上授权 `web_search` / `web_fetch`（原因见 ROLLBACK-000）。
2. admin 账号、编辑档账号、查看档账号、终端用户账号各 1 个；MV-04 需非 admin 账号。
3. 无人正在编辑配置页且持有未保存草稿；已知旧页面需硬刷新（Ctrl+F5）。
4. 约定无人时段（ib-web 重启丢内存态会话）；用户在场执行人工验证。
5. 已看到下文「用户需要执行的动作」与「用户裁决」两节（已裁决）。

## 部署步骤

所有 DEPLOY 位置均为**目标机**（经 ssh）。预检全部通过（CLASS=A，或 CLASS=E 且已获 PM 对应授权）后按序执行；任一步失败按「失败处理矩阵」处置。

### DEPLOY-001: 目标机拉取代码（`git pull`，禁 scp / pscp / rsync）
- 组件: 全部源码（架构部署视图：基础设施无变更 → 数据层（迁移文件落盘，尚未应用）→ 服务层 → 前端）
- 位置: 目标机 `/opt/intelligentbase`（属主 `yangyang198354`，免 sudo）
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git rev-parse HEAD)" = "$1" ]                      # 前置：仍在锚点
git fetch origin main
[ "$(git rev-parse origin/main)" = "$2" ]               # 前置：远端恰为待部署提交；否则中止（尚无变更）
date "+PULL_TS=%F %T"                                    # 记入报告，供 V-07 日志 --since
git pull --ff-only origin main                          # 等价画像 P7 的 git pull origin main，加 --ff-only 禁止合并提交
[ "$(git rev-parse HEAD)" = "$2" ]                      # 后置：精确等于待部署提交
test -s src/deploy/migrations/009_web_governance.sql
git log --oneline -1
git status --porcelain
EOF
```
- 预期: fast-forward 到 `DEPLOY_COMMIT`；已跟踪文件无修改；009 文件在位；退出码 0。**注意：此刻磁盘代码已领先于运行中的 ib-web / ib-worker 进程**（pull 与 DEPLOY-003 之间应尽量缩短，且期间不做验证性访问以外的操作）。
- 回滚: ROLLBACK-001（001a + 001b）

### DEPLOY-002: 依赖与导入核对（只读闸，不改任何文件、不重启）
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
$PY -B -c 'import lxml.etree as E; v=E.LXML_VERSION; assert (5,0) <= tuple(v[:2]) < (7,0), v; print("lxml ok", v)'
$PY -B -c 'import ib.webtools, ib.advisor, ib.ledger.web_governance, ibweb.composition, ibweb.views; print("import ok")'
$PY -B -c 'import sqlite3; from ib.ledger.schema import web_governance_ddl_script as g; c=sqlite3.connect(":memory:"); c.executescript(g()); c.executescript(g()); print("009 ddl in-memory replay ok")'
EOF
```
- 预期: 打印 `lxml ok …`、`import ok`、`009 ddl in-memory replay ok`（迁移文件与生成器的单源一致性由 CI Schema 门 + selfcheck 判定，此处不重复）。三行任一失败 → 停止（磁盘已 pull，进入失败矩阵：视为已变更，ROLLBACK-001a → 001b；服务尚未重启，无需其他回滚）。
- 说明: `python -B` + 目标机 `cd src` 使 `ib` / `ibweb` 可导入（`PYTHONPATH` 机制 `[INFERRED]`：服务单元 `WorkingDirectory=/opt/intelligentbase` 下 `-m ibweb.bootstrap` 可用，其路径设置方式本组未核实）。导入 `ibweb.views` 若因缺 `DJANGO_SETTINGS_MODULE` 报错，视为核对方法问题而非产品缺陷，改用只导入 `ib.*` 的前两条并在报告注明。
- 回滚: 无（只读）；失败按上。

### DEPLOY-003: 重启 ib-web（迁移 009 随 `ExecStartPre` 自动应用）
- 组件: ib-web（Waitress，127.0.0.1:18080）；`ExecStartPre=…/python -m ibweb.bootstrap --ensure-schema` 先建 `web_governance`（幂等）
- 位置: 目标机；`sudo -n systemctl restart ib-web`（三条免密 restart 之一，SKILL.md §4）
- 命令（重启严格断言，不得只用 `is-active`）:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-web; for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/healthz)" = 200 ] && break; sleep 2; done; systemctl is-active ib-web; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp,MemoryCurrent ib-web; journalctl -u ib-web --since "$TS" --no-pager | grep -E "startup|ConfigError|OperationalError|Traceback|ModuleNotFoundError|ImportError|runtime_compile_failed|config_drift|web_governance_unavailable|path_not_configured_using_in_memory_default" | tail -n 30'
```
- 预期: `/healthz` 200；`active` / `running` / `NRestarts=0`；日志含 `"outcome": "succeeded", "stage": "startup"`；错误关键字零命中；**不出现** `path_not_configured_using_in_memory_default`（文件态仍生效，SKILL.md §7.4）；`daemon-reload` pending 警告是长期存在的（SKILL.md §7.2），不处理。`RESTART_TS` 记入报告。
- 若 `ExecStartPre` 失败（迁移 009 应用失败）→ ib-web 不会起来（`Restart=on-failure` 会反复重试）：**立即停止轮询**，查 `journalctl -u ib-web --since "$TS"` 的首个错误，不反复重启；进入回滚（ROLLBACK-003 的先决：001a→001b）。
- 回滚: ROLLBACK-003（先 ROLLBACK-001）

### DEPLOY-004: 前端构建并发布到 web root（不重启任何服务）
- 组件: 前端静态产物（nginx 直读 `/var/www/intelligentbase/`，属主 `yangyang198354`，无需 sudo；nginx 不改、不 reload）
- 位置: 目标机 `/opt/intelligentbase/src/frontend`（`node_modules` 已就位；`package-lock.json` 未变，不执行 `npm ci`）
- 命令（先留旧产物副本，再构建，构建成功才替换；构建命令超时需 ≥ 300 秒 `[INFERRED]`）:
```bash
ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r28 ]; mkdir ~/ib-webroot-pre-r28; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r28/; test -s ~/ib-webroot-pre-r28/index.html; test -d ~/ib-webroot-pre-r28/assets; ls ~/ib-webroot-pre-r28'
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html && grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u'
```
- 预期: `vue-tsc --noEmit && vite build` 退出码 0；打印新的 `assets/index-<hash>.js`，hash **不同于** PRE-04 记录的旧值；ib-worker / ib-embed 的 `ActiveEnterTimestamp` 不变。构建失败时 `&&` 链在 `rm` 之前中断，web root 仍是旧产物。旧副本放在部署用户家目录（仓库外、不入 git），验收通过后由用户决定删除；不使用 `rsync` / `scp`。
- 替换窗口风险: `rm -rf assets` 与 `cp -r dist/assets` 之间（秒级）及此后，已加载旧 `index.html` 的浏览器若再懒加载旧 hash 分包会 404；有未保存草稿的用户须先保存或放弃再硬刷新 `[INFERRED]`（PRE-08 已确认无人编辑）。
- 回滚: ROLLBACK-004

### DEPLOY-005: （不执行，已裁决）重启 ib-worker —— 用户裁决 Q1：本次发布不重启 ib-worker
- 裁决: 固定为**不执行**。`INCLUDE_WORKER_RESTART` 缺省 false，本轮 PM 不得授权为 true；E2 遇到该步骤一律记「跳过（用户裁决 Q1）」，不得标 SUCCESS。V-01 中 ib-worker 的 `ActiveEnterTimestamp` 必须与 PRE-04 相同。
- 取舍留档: module_design 结论为 ib-worker 不需重启（共享包 `ib.ledger` 仅追加建表，无行为变化）；DEPLOY-001 后磁盘领先于 worker 进程、惰性 import 混用的小概率风险 `[INFERRED]` 由用户接受。若日后需要，须新开计划修订，不在本轮。
- 命令（仅留档，本轮不执行）:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-worker; for i in $(seq 1 20); do [ "$(systemctl is-active ib-worker)" = active ] && break; sleep 3; done; sleep 15; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-worker; echo "errors_in_log=$(journalctl -u ib-worker --since "$TS" --no-pager | grep -cE "unable to open database file|Traceback|OperationalError")"; pgrep -c -f "[i]bweb\.worker"'
```
- 预期: `active` / `running` / `NRestarts=0`；`errors_in_log=0`；`pgrep -c` 为 **1**（`[i]` 写法避免匹配命令自身；单实例，画像 P8）。`TimeoutStopSec=300`，执行端命令超时需 ≥ 360 秒 `[INFERRED]`。
- 回滚: ROLLBACK-005

### DEPLOY-006: （不与本轮同批；仅用于「前序 ib-embed 提交的单独发布」）重启 ib-embed —— 用户裁决 Q2
- 裁决: PRE-02 判 CLASS-E 时先单独发布前序提交（`ae07f44` / `47f19a3`），本命令块是该单独发布使用的重启与验证标准；**不在本轮 DEPLOY-001~004 同一批次中执行**，`INCLUDE_EMBED_RESTART` 在本轮不使用。CLASS=A 时本步骤不适用（跳过，不标 SUCCESS）。
- 前提: 用户已确认 `/etc/intelligentbase/ib-embed.env` 含 `MKL_ENABLE_INSTRUCTIONS=AVX`（SKILL.md §8.11；**只核对键存在，不读值**：`sudo grep -c '^MKL_ENABLE_INSTRUCTIONS=' …`）。
- 命令:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-embed; for i in $(seq 1 40); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8100/healthz)" = 200 ] && break; sleep 3; done; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-embed; curl -s http://127.0.0.1:8100/healthz; echo; journalctl -u ib-embed --since "$TS" --no-pager | grep -E "启动预热|Traceback|status=4/ILL|invalid opcode" | tail -n 10'
```
- 预期: `/healthz` 200 且 `model_loaded=true`、`warm=true`（对应 `47f19a3`）、维度正确（M-DE-002）；出现"启动预热完成"；无 `ILL`。启动加载 bge-m3 可能需 1–2 分钟 `[INFERRED]`。
- 回滚: ROLLBACK-006

### DEPLOY-007: （后续，OPT-A）启用 DeepSeek 搜索 —— 仅在首发人工验证（Stage 1）通过**且用户在主会话本轮单独授权** `ENABLE_WEB_SEARCH=true`（Q3 已裁决；首发批次不含本步骤）
- 组件: ib-web 进程配置（`IB_WEB_SEARCH_PROVIDER=deepseek`）；**无新凭据**：搜索复用 LLM 的 DeepSeek Key（台账 `llm_key` / 回退 `IB_LLM_API_KEY`）
- **步骤 7a（用户执行，代理不碰 env）**: 编辑 `/etc/intelligentbase/ib-web.env`（0600，属主 ib-web，需 sudo），**追加一行键值**：`IB_WEB_SEARCH_PROVIDER=deepseek`（建议值；`IB_WEB_FETCH_ENABLED` 与 `IB_WEB_GOVERNANCE_BACKEND` 保持不设置）。前提：`IB_LLM_BASE_URL` 主机为 `api.deepseek.com`（缺省即是，PRE-07 已核）；`fake` 在生产非法（启动失败）。完成后口头确认"已改"，**不要贴出文件内容**。
- **步骤 7b（A）**: 与 DEPLOY-003 相同的重启严格断言命令（`RESTART_TS` 重新取值）。预期额外：启动不因 `IB_WEB_SEARCH_PROVIDER` 值域 / LLM 主机校验失败（失败只报键名）；`/healthz/deps` 新增 `egress_web`，列出主机 `api.deepseek.com` 与数据类别 `web_search_query`（外发声明）。
- 出站: ib-web 出站 `api.deepseek.com:443`（与 LLM 同主机，LLM 已需放行，无新增放行项）。
- 回滚: ROLLBACK-007（用户删除该行 + 重启 ib-web；零数据影响）。
- 计费提示: 按次计费、有 QPS 限制（P11-3 资料）；MV-15 的 429 / 402 触发已裁决推迟到维护窗口（Q4），Stage 2 不做。

### DEPLOY-008: （本轮不启用，OPT-B）启用本地网页抓取 —— 用户裁决 Q3：本轮暂不启用；以下仅留档，E2 不得执行，后续启用须新授权并修订计划
- 步骤 8a（用户执行）: 在 `ib-web.env` 追加 `IB_WEB_FETCH_ENABLED=1`（缺省 `0`）；完成后口头确认。
- 步骤 8b（A）: 同 DEPLOY-003 的重启严格断言。预期 `/healthz/deps` 的 `egress_web` 增加抓取项（目标主机为通配）。
- **出站 ACL 建议（由用户配置，非代码依赖，`[INFERRED]` 建议）**: 抓取开启后 ib-web 可对**任意公网主机**发起 80/443 请求。代码侧已有 SSRF 防护（地址防护、钉 IP、重定向复核、禁内网），防火墙为第二道防线：对 `ib-web` 用户（按 uid 匹配）的出站**拒绝** RFC1918（含目标机所在的 192.168.31.0/24 局域网）、链路本地 / 云元数据地址 `169.254.0.0/16`、回环以外的内部段；**放行** loopback（Qdrant 6333、ib-embed 8100）、DNS 解析器（若解析器在局域网，如 192.168.31.1，须单独放行 53，否则 LLM 与搜索的 `api.deepseek.com` 解析也会失败）、`api.deepseek.com:443`。规则落地前后各跑一次 LLM 问答与 MV-09/10 验证。该配置由用户在防火墙层执行，本组不提供可直接粘贴的 ACL 命令以免误伤。
- 回滚: ROLLBACK-008（用户把该键改回 `0` 或删除 + 重启 ib-web）。

## 回滚步骤（逆序）

执行总序：**ROLLBACK-000（用户前置，仅当已有项目授权过联网/启用过顾问）→ 001a（源头 revert + push）→ 001b（目标机 pull）→ 004（前端重建发布）→ 003（重启 ib-web）→（若 OPT-A 已执行）007；006 / 005 / 008 本轮不执行，无需回滚（env 键须在代码回退前后均无害，见各条）**。ROLLBACK-001 是把"目标机代码状态"还原的载体，必须先于各单元动作落地；其余按 DEPLOY 逆序（前端先于 ib-web，避免旧后端配新前端）。

**不得破坏的本地状态**（全部回滚路径均不触碰）：`/etc/intelligentbase/*.env`（由用户编辑）、`/var/lib/intelligentbase/`（台账、blob、definition、prompts）、bge-m3 权重、Qdrant 数据、`/opt/intelligentbase/venv`、前端 `node_modules`。**所有回滚均不使用** `git reset --hard`、`git clean`、`git stash`、覆盖式同步。

**配置版本回滚（产品功能）≠ 代码回滚**：若问题只出在验收期间在测试项目里产生的配置内容，用配置页"版本 → 回滚"（热生效，无需代码回滚）；本节 ROLLBACK 用于代码 / 迁移 / 前端本身有缺陷时。

### ROLLBACK-000: 回滚前置——清除联网授权（用户，经配置页，**新代码仍在运行时**执行） `[MANUAL_ROLLBACK_REQUIRED]`
- 为何必须: 旧代码（REV-27）的定义文档校验不认识 `web_search` / `web_fetch`（`ib/config/definition.py` 的 `tool_grant_tool_unknown`），若任一项目的已保存配置含这两个工具授权，回退代码后该项目定义加载失败（可能影响 ib-web 启动）。
- 操作: 对验收期间保存过联网授权的项目，在配置页用"版本 → 回滚"回到授权之前的版本（或在配置页取消 `web_search` / `web_fetch` 并保存生效）。含 `advisor` 专家的新建测试项目无联网授权即可被旧代码当作普通专家加载（`advisor` 只是个名字，旧代码无顾问专属规则）`[INFERRED]`，但**更稳妥**是回滚前同样清理。
- 核验（用户）: 复用 PRE-06 脚本，把判据改成"任一定义文档含 `web_search` / `web_fetch` 字样"，输出命中 0 才可继续 001a。

### ROLLBACK-001a: 源头 revert 并 push（主会话，用户确认；回滚 DEPLOY-001 的源头部分）
- 类型: 正式回滚
- 变量: `R28_COMMITS` = 本轮发布的提交哈希（可能多个；由 PM 在授权时与 `DEPLOY_COMMIT` 一并给出，**须全部是 `ANCHOR` 之后、`DEPLOY_COMMIT` 及之前的提交**），按**从新到旧**依次 revert。
- 命令（开发机；要求工作树对 `src tests .github` 干净）:
```bash
set -- <R28_COMMITS 从新到旧，空格分隔的 40 位哈希>            # 由 PM 提供；下面全部用 "$@"
git fetch origin main && git switch main && git pull --ff-only origin main
for c in "$@"; do [ "$(git cat-file -t "$c")" = commit ] && git merge-base --is-ancestor "$c" HEAD || { echo "BAD_COMMIT $c"; exit 1; }; [ -z "$(git rev-list --merges -n 1 "$c^..$c")" ] || { echo "MERGE_COMMIT $c"; exit 1; }; done
git revert --no-commit "$@"                                    # 参数 = R28_COMMITS（从新到旧）
git restore --source=HEAD --staged --worktree -- docs .claude   # 保留文档与 agent 记忆，只还原代码与测试
git diff --cached --name-only | grep -vE '^(src/|tests/|\.github/)' && echo UNEXPECTED_PATHS || echo ONLY_SRC_TESTS_CI
```
  核验两点：① 输出必须是 `ONLY_SRC_TESTS_CI`；② 对**最早的 R28 提交的父提交**（记作 `BASE`，须等于 `ANCHOR` 或其祖先且二者之间无其他运行时变更）：`git diff --quiet "$BASE" -- src tests .github && echo SRC_EQUALS_BASE || echo SRC_DIFFERS_FROM_BASE`，必须是 `SRC_EQUALS_BASE`；否则上报，不 commit，放弃本次 revert 用 `git revert --abort`（仅在 revert 处于进行中状态时可用；已完成暂存而无冲突态时先经用户确认再 `git restore --staged --worktree -- src tests .github`）。通过后:
```bash
git commit -m "revert(r28): roll back advisor agent and web search (REV-28)"
git push origin main
git rev-parse HEAD                                             # = REVERT_COMMIT，记入报告
```
- 变量取值与核验: `R28_COMMITS` 以脚本位置参数传入并逐个 `git cat-file -t` / `merge-base --is-ancestor` / 非合并核验（上方循环）；`ANCHOR` 取 PRE-01 输出（deployment_report 首节），执行前 `git cat-file -t "$ANCHOR"` 必须输出 `commit`。回滚用的是**新提交 + 普通 push**，不 force-push、不 reset。revert 同时删除 `009_web_governance.sql` 与对应生成器（**数据库中已建的 `web_governance` 表保留，旧代码不读它，无害**，见 ROLLBACK-009）。
- 预期: push 成功；CI 对回退提交自动运行（记录结果，不必等待完成才继续回滚）。

### ROLLBACK-001b: 目标机拉取回退提交（回滚 DEPLOY-001）
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
test ! -e src/deploy/migrations/009_web_governance.sql && echo MIG009_REMOVED
git diff --stat "$1" HEAD -- src/ib src/ibweb src/deploy src/frontend/src src/requirements.txt src/requirements-offline.txt   # 期望：仅 ANCHOR 之后的非 REV-28 差异（通常为空）
git status --porcelain
EOF
```
- 变量取值与核验: `$1`=`ANCHOR`、`$2`=`REVERT_COMMIT` 均作为位置参数传入（Q2）。
- 预期: HEAD = `REVERT_COMMIT`；打印 `MIG009_REMOVED`；`git diff --stat` 为空或仅含非 REV-28 差异（人工判断）；无已跟踪文件修改。

### ROLLBACK-004: 回滚 DEPLOY-004（前端）
- 类型: 正式回滚 = 001b 之后用回退后的源码重新构建并发布；紧急止血 = 还原部署前 web root 副本。
- 正式回滚命令:
```bash
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html'
```
- 紧急止血（不依赖构建；新前端有严重缺陷且 push / pull 通道暂不可用时）:
```bash
ibssh 'set -e; test -s ~/ib-webroot-pre-r28/index.html; test -d ~/ib-webroot-pre-r28/assets; rm -rf /var/www/intelligentbase/assets; cp -r ~/ib-webroot-pre-r28/assets /var/www/intelligentbase/; cp ~/ib-webroot-pre-r28/index.html /var/www/intelligentbase/; sha256sum /var/www/intelligentbase/index.html; ls -l /var/www/intelligentbase'
```
  **收尾（必做）**: 止血后仍须走 001a → 001b 并执行一次正式回滚命令，使 web root 与远端 HEAD 的构建结果一致、目标机仓库回到与远端一致的干净状态（止血本身不改仓库，无需 git 清理）。
- 变量取值与核验: 无本地变量；`test -s` / `test -d` 已内置。止血后 `sha256sum` 必须等于 PRE-04 记录值；正式回滚后须不同于 DEPLOY-004 的新 hash。
- 预期: 硬刷新后恢复旧界面（新建项目无"启用顾问"、无"联网上限"页）。

### ROLLBACK-003: 回滚 DEPLOY-003（ib-web 以回退后的代码重启）
- 类型: 正式回滚（前提：ROLLBACK-000 已满足、001a / 001b 已完成）
- 命令: 同 DEPLOY-003 的重启严格断言命令块（此时磁盘代码为回退版本）。
- 预期: 同 DEPLOY-003 的「预期」，另 `ExecStartPre` 在**含 `web_governance` 表的库**上正常通过（旧 `ensure_schema` 只补自己认识的表 / 列，不报多余表）`[INFERRED]`。
- 失败处理: 重启失败 → 先查日志首个错误（重点 `tool_grant_tool_unknown` → 返回 ROLLBACK-000），不反复重启；`ROLLBACK_FAILED`，保留现场，人工介入。

### ROLLBACK-006 / ROLLBACK-005: （本轮不适用）回滚 DEPLOY-006 / DEPLOY-005
- 类型: 正式回滚（前提：001b 已完成）；DEPLOY-005 / 006 本轮不执行（Q1 / Q2），故本轮无需执行；仅当将来修订计划后执行过才适用。先 006 后 005（逆序）。
- 命令: 同 DEPLOY-006、DEPLOY-005 的重启命令块（此时磁盘代码为回退版本）；验证标准同其「预期」。重启失败 → 不反复重启，`ROLLBACK_FAILED`。
- 注意: ib-embed 的前序提交（`ae07f44`、`47f19a3`）不属于 REV-28，**不随 REV-28 回滚而回退**；ROLLBACK-001a 只 revert `R28_COMMITS`。

### ROLLBACK-008 / ROLLBACK-007: （可选）回滚 OPT-B / OPT-A
- 类型: 正式回滚。**用户**编辑 `/etc/intelligentbase/ib-web.env`：OPT-B → 删除 `IB_WEB_FETCH_ENABLED` 行（或设 `0`）；OPT-A → 删除 `IB_WEB_SEARCH_PROVIDER` 行（或设 `none`）。随后 A 执行与 DEPLOY-003 相同的重启严格断言。
- 预期: `/healthz/deps` 回到基线键集（无 `egress_web`）；顾问若已授权 `web_search`，调用降级为"联网未开启"类文案（module_design：总开关关闭短路）。
- 说明: 仅需关闭联网（不回滚代码）时，只做本条即可，零数据影响。**若同时回滚代码，env 键残留无害**（旧代码不读 `IB_WEB_*`）；但仍建议清理。

### ROLLBACK-009: 撤销迁移 009（用户，**可选**） `[MANUAL_ROLLBACK_REQUIRED: 删除 web_governance 表及 admin 设定的联网上限；仅在需要完全还原 schema 时执行]`
- 通常**不需要**：代码回退后旧代码不读该表，留表无害，且再次部署 009 为幂等 `IF NOT EXISTS`。
- 需要时（**必须先有 PRE-05 备份**，且代码已回退并已重启 ib-web，避免新代码仍在使用该表）由用户执行（命令来自 009 头注释，不在迁移文件内以可执行形式出现）:
```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)
c = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3")
print("before:", c.execute("select count(*) from sqlite_master where name='web_governance'").fetchone()[0])
c.execute("DROP TABLE web_governance")
c.commit()
print("after:", c.execute("select count(*) from sqlite_master where name='web_governance'").fetchone()[0])
c.close()
PY
sudo ls -l /var/lib/intelligentbase/ledger/ledger.sqlite3*     # 核对仍为 660 ib-web:ib（-wal/-shm 属主不得变 root）
```
- 数据风险: 丢失 admin 设置的三项联网上限（行缺失 ⇒ 默认 5 次 / 1 MiB / 30 秒，影响仅限已回退的功能）；无其他表受影响。回滚后若重新部署 REV-28，上限回到默认值。

### 失败处理矩阵（E2 使用）

| 失败位置 | 目标环境是否已变更 | 处置 |
|---|---|---|
| 任一 PRE（含 CLASS=E 未获授权、CLASS=X、PRE-06 命中、PRE-07 异常） | 否 | 停止，`DEPLOYMENT_FAILED`，无需回滚 |
| DEPLOY-001（前置核对失败） | 否 | 同上 |
| DEPLOY-001（pull 后 HEAD ≠ 待部署提交 / 工作树不干净） | 是 | ROLLBACK-001a → 001b |
| DEPLOY-002（lxml / 导入 / DDL 核对失败） | 是（仅代码已落盘，服务未重启） | ROLLBACK-001a → 001b；服务无需动作 |
| DEPLOY-003（重启失败 / `ExecStartPre` 迁移失败 / 日志有错误） | 是 | 停止后续；ROLLBACK-001a → 001b → 003（ROLLBACK-000 若涉及） |
| DEPLOY-004（构建失败，web root 未替换） | 是（后端已变更） | 视为已变更：保持后端新版本是否可接受由 PM 请用户裁决；若回滚按 001a → 001b → 004 → 003 |
| DEPLOY-004（替换中途失败，web root 可能不完整） | 是 | 先 ROLLBACK-004 紧急止血恢复可用，再 001a → 001b → 004 → 003 |
| DEPLOY-005 / 006 | — | 本轮不执行（Q1 / Q2）；前序 ib-embed 单独发布若失败，按其自身计划处置，不进入本轮 DEPLOY-001 |
| 部署后验证机器可验项失败（V-01~V-10） | 是 | `DEPLOYED_WITH_ISSUES`，列出失败项，由 PM 请用户决定是否回滚 |
| 人工验证 Stage 1 critical path 不通过 | 是 | `DEPLOYED_WITH_ISSUES`；缺陷回流（协议 §C）或用户决定回滚；仅测试项目内容问题优先用配置版本回滚 |
| OPT-A 步骤失败（OPT-B 本轮不执行） | 是（仅限 env 与 ib-web） | ROLLBACK-007（不影响首发已上线部分） |
| 回滚步骤自身失败 | — | 停止回滚，`ROLLBACK_FAILED`，写清各步骤已部署 / 已回滚 / 状态未知，由用户人工介入 |
| 遇到 `[MANUAL_ROLLBACK_REQUIRED]` 步骤失败（ROLLBACK-000 / 009） | — | 立即暂停，返回 BLOCKED 等待人工决定 |

## 不可逆步骤汇总

| # | 步骤 | 性质 | 数据风险 | 处置 |
|---|---|---|---|---|
| I-1 | DEPLOY-003 应用迁移 009（新增表 `web_governance`） | `[MANUAL_ROLLBACK_REQUIRED: 撤销 = ROLLBACK-009 的 DROP TABLE，由用户在 PRE-05 备份之后执行]` | 低：新表无存量；DROP 只丢三项上限设置（回默认值）；代码回退后留表无害 | 默认不 DROP；需要时按 ROLLBACK-009 |
| I-2 | 验收中在测试项目"保存并生效"（含启用顾问 / 授权联网 / 加入顾问） | `[MANUAL_ROLLBACK_REQUIRED: 配置版本与审计记录只增不删，代码回滚不会清除；含 web_search / web_fetch 授权的版本在旧代码下无法加载，回滚代码前须先 ROLLBACK-000]` | 仅限测试项目；旧代码加载失败的风险见 ROLLBACK-000 | 验收后用"版本 → 回滚"回到授权前版本（产生新版本而非删除历史）；新建的测试项目是否保留由用户决定 |
| I-3 | DEPLOY-003 重启 ib-web（DEPLOY-005 / 006 本轮不执行） | 不可撤销的副作用 | 内存态聊天会话与"人工确认挂起态"丢失（fail-closed）；ib-worker 重启会中断在途入库作业（可恢复） | 选无人时段 |
| I-4 | OPT-A 启用搜索后的真实调用 | 外部系统调用 | 向 DeepSeek 发送搜索查询并**按次计费**；不可撤回 | 仅在 Stage 2 人工验证时使用；MV-15 的限流 / 欠费触发需用户另行同意（Q4）；关闭见 ROLLBACK-007 |
| I-5 | OPT-B 启用抓取后的真实调用 | 外部系统调用 | 向任意公网主机发出 HTTP 请求；按设计受域名名单与 SSRF 防护约束；MV-09 / 10 只用自有受控服务器 | 出站 ACL 就位后才开启；关闭见 ROLLBACK-008 |

web root 替换可通过备份副本还原（ROLLBACK-004 止血），不属不可逆。

## 部署后验证

「真实启动时刻」= DEPLOY-003 输出的 `RESTART_TS`。执行者 `A` = 代理经 ssh；`U` = 用户；`U*` = 用户人工验证（见 MV 排期）。

| ID | 检查项 | 执行者 | 命令 / URL | 成功标准 |
|---|---|---|---|---|
| V-01 | 服务存活且重启符合预期 | A | `ibssh 'systemctl is-active ib-web ib-worker ib-embed qdrant nginx; for u in ib-web ib-worker ib-embed; do systemctl show -p ActiveEnterTimestamp,NRestarts "$u"; done'` | 5 行 `active`；ib-web `ActiveEnterTimestamp` 晚于 `RESTART_TS` 且 `NRestarts=0`；ib-worker / ib-embed 的时间戳与 PRE-04 相同（本轮 005 / 006 不执行，必须相同） |
| V-02 | **线上代码版本**（HEAD + 源文件 mtime 早于启动时刻，**不用 .pyc**） | A | `ibssh bash -s -- "$DEPLOY_COMMIT" "$ANCHOR" <<'EOF'`；体：`cd /opt/intelligentbase; [ "$(git rev-parse HEAD)" = "$1" ]; git status --porcelain; AT=$(systemctl show -p ActiveEnterTimestamp --value ib-web); AT_EPOCH=$(date -d "$AT" +%s); bad=0; for f in $(git diff --name-only --diff-filter=AMR "$2" "$1" -- src/ib src/ibweb src/deploy/migrations); do m=$(stat -c %Y "$f"); [ "$m" -lt "$AT_EPOCH" ] \|\| { echo "NEWER_THAN_START $f"; bad=1; }; done; echo "mtime_check_bad=$bad"; test -s src/deploy/migrations/009_web_governance.sql && echo MIG009_PRESENT`；`EOF`（粘贴时 heredoc 顶格，去掉表格中的转义反斜杠） | HEAD = `DEPLOY_COMMIT`；已跟踪文件无修改；`mtime_check_bad=0`；`MIG009_PRESENT`。`$2`=`ANCHOR` 作为位置参数传入（Q2） |
| V-03 | 启动日志与文件态 | A | `ibssh 'journalctl -u ib-web --since "<RESTART_TS>" --no-pager \| grep -E "\"stage\": \"startup\"\|path_not_configured_using_in_memory_default\|ConfigError\|Traceback\|ModuleNotFoundError\|ImportError\|web_governance_unavailable\|runtime_compile_failed\|config_drift" \| tail -n 30'`（`<RESTART_TS>` 为本地已知值，须按 Q2 以位置参数传入，示意） | 有 `"outcome": "succeeded", "stage": "startup"`；**无** `path_not_configured_using_in_memory_default`；错误关键字零命中 |
| V-04 | 迁移 009 已应用（只读，ib-web 身份） | U | `sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'`；体：`import sqlite3; c=sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro",uri=True); print([r[1] for r in c.execute("pragma table_info(web_governance)")]); print("rows:", c.execute("select count(*) from web_governance").fetchone()[0]); print("documents:", c.execute("select count(*) from documents").fetchone()[0])`；`PY` | 列为 `id, max_calls_per_turn, max_fetch_bytes_per_turn, max_seconds_per_turn, updated_at, updated_by`；`rows: 0`（未设置 = 默认上限）；`documents` 计数等于 PRE-05 备份时的值；`ls -l ledger.sqlite3*` 仍 660 ib-web:ib |
| V-05 | 健康检查、外发声明与基线一致（联网关闭） | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz'`；`curl -sS -o /dev/null -w '%{http_code}\n' https://192.168.31.133/healthz`（不携带凭据；`-k` 仅用于公开首页）；`ibssh 'curl -s http://127.0.0.1:18080/healthz/deps \| python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d)); print(\"egress_web\" in d)"'` | 两处 `/healthz` 均 200；`/healthz/deps` 顶层键集与 PRE-04 完全相同，且 `egress_web` 为 `False`（联网关闭 ⇒ 外发声明与基线逐字节相同，module_design 兼容性 #6） |
| V-06 | 新接口已挂载且受鉴权保护 | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/api/web-governance'`（不带令牌） | 返回 401 或 403（**不是** 404 / 500；404 = 新代码未生效，500 = 装配异常）`[INFERRED]` 具体码以 `authz` 现状为准，记录实际值 |
| V-07 | 日志无新增错误 | A | `PULL_TS` 取 DEPLOY-001 输出，经 Q2 位置参数传入：`journalctl -u ib-web --since "$1" -p warning --no-pager \| tail -n 30; journalctl -u ib-worker --since "$1" -p warning --no-pager \| tail -n 30`（`ibssh bash -s -- "$PULL_TS" <<'EOF'`，heredoc 顶格） | 无 Traceback / OperationalError 等新错误；已知长期 warning（`daemon-reload` pending）除外，需如实记录 |
| V-08 | 前端已发布为新构建 | A + 开发机 curl | 目标机：`ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html \| sort -u'`；外部：`curl -sk https://192.168.31.133/ \| grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \| sort -u` | 两处 hash 一致，等于 DEPLOY-004 输出，且不同于 PRE-04 旧值 |
| V-09 | 本地状态未被触碰；资源基线 | A | `ibssh 'cd /opt/intelligentbase && git status --porcelain; ls -d src/frontend/node_modules venv 2>&1 \| head -n 3; stat -c "%a %U:%G %n" /etc/intelligentbase/*.env; systemctl show -p MemoryCurrent,MemoryMax ib-web'` | 已跟踪文件干净；`node_modules` 与 `venv` 仍在；env 文件权限属主与上线前一致（只 `stat`，不读内容）；`MemoryCurrent` 记录在案（接近 1024M 上限需上报，非失败项） |
| V-10 | 既有功能冒烟（联网关闭，不新增写入；写入数据唯一化） | U | 浏览器登录 → 现有项目问答一次（现有 kb-agent 路径）、配置页可打开（只读） | 问答有答复且流式正常；页面无白屏 / 控制台报错；既有项目行为不变（兼容性 #1~#5）。若需保存，名称带 `r28-<epoch>` 后缀 |
| V-11 | 人工验证（见下 MV 排期 Stage 1） | U* | `e2e_test_report.md`「人工验证清单」 | 见下 |

### 人工验证 MV-01~MV-16 排期（引用 `e2e_test_report.md` 2.0.0 原文，**不改写其步骤与期望**）

分三阶段，避免首发即联网。"联网状态"指 `ib-web` 当时的配置：

| 阶段 | 联网状态（ib-web） | 谁/何时 | 包含的 MV | 说明 |
|---|---|---|---|---|
| **Stage 1**（首发后立即） | `none` / 抓取 `0`（缺省，无 env 改动） | U；DEPLOY-004 完成后 | **MV-01**（新建项目启用顾问）、**MV-02**（加入/移除顾问）、**MV-03**（顾问面板勾选 web_search / web_fetch、参数、非法域名；保存授权只在**测试项目**）、**MV-04**（admin 联网上限页与权限）、**MV-12**（全旅程：创建启用顾问项目 → 上传文档 → 提问，**联网关闭时**回答来自知识库与来源标注）、**MV-06 / MV-07**（意图 / 指代评测集与"评测集确认"：只用真实 LLM，不依赖联网；评测集由用户提供，`src/scripts/advisor_eval.py` 目标机手工运行，密钥只读环境变量）| 联网关闭即可验；MV-03 的保存会产生含联网授权的配置版本（I-2，仅测试项目） |
| **Stage 2**（用户确认 Stage 1 并在主会话单独授权 OPT-A 后） | `deepseek` / 抓取 `0` | U 编辑 env + A 重启（DEPLOY-007）；用户在场 | **MV-05**（真实 DeepSeek 搜索效果、`/healthz/deps` 外发声明、日志无 Key）、**MV-08**（≥20 条注入样例，仅搜索类）、**MV-11**（联网超时 10±1 秒降级，以搜索为例）、**MV-13**（联网事实被改写 / 致歉频次，需用户裁决）、**MV-14**（真实 TLS、慢速 / 断网 / 代理）、**MV-15**（只做无破坏部分：核对错误分类 / 降级文案与日志；**制造 429 / 402 的真实计费调用 = 推迟（维护窗口）**）、**MV-16**（只做无破坏部分：存储有值时优先、日志 Key 出现 0 次、`git diff` 的 env.example 无新增密钥键；**"删除生产 LLM Key 回退环境变量"分支 = 推迟（维护窗口）**） | 依赖 provider=deepseek；Q4 已裁决，推迟项不属本轮通过标准，在报告中标「推迟（维护窗口）」，不得标 PASS |
| **Stage 3**（本轮不启用，OPT-B；Q3 已裁决） | `deepseek` / 抓取 `1`，出站 ACL 已就位 | U；用户明确需要网页抓取 | **MV-09**（受控测试服务器：公网页、证书错配、重定向到内网）、**MV-10**（受控 DNS：私有地址、IPv6）、MV-08 的网页正文型样例、MV-11 的抓取慢速场景 | **不得探测生产内网**；仅用自有可控服务器 / 域名 |

- **通过标准**（E2 状态映射）：V-01~V-10 机器可验项全部通过 **且** Stage 1 的 MV（MV-01/02/03/04/06/07/12）完成并通过 → `DEPLOYED_SUCCESSFULLY`；机器可验项通过但 Stage 1 人工项未完成 / 不通过 → `DEPLOYED_WITH_ISSUES`。Stage 2 / 3 属可选后续步骤，其 MV 结果单独记录，不影响首发的最终状态；MV-06 / MV-07（评测集 / 验收口径）为 `[DATA_REQUIRED]`，用户未提供评测集时按 e2e 报告口径标"待评测集确认"，**不得以合成集通过率宣告验收**（AC-019-04）。协议 §K：只要仍有未完成的人工验证，整体交付状态至多 `DELIVERED_WITH_ISSUES`（e2e 报告已声明这 16 项为 NOT_TESTABLE 的"待人工验证"）。
- 回滚后的验证：V-01、V-05（`/healthz/deps` 键集 = PRE-04）、V-06（应为 404，证明新接口已移除）、V-08（hash 等于 PRE-04 旧值或新重建值）、V-09；V-11 不再适用。
- 验收中的写入全部在测试项目；验收后用"版本 → 回滚"复原（I-2）。

## 用户需要执行的动作（汇总，代理不代做）

| # | 动作 | 时机 | 要点 |
|---|---|---|---|
| U-1 | commit + push 本轮代码（经主会话） | E2 授权前 | 含全部未跟踪新文件；确认 CI 全绿后再给 `DEPLOY_COMMIT` |
| U-2 | PRE-05 台账备份（ib-web 身份、只拷贝） | DEPLOY-001 之前 | 备份后核对大小 / 属主 / `integrity_check` |
| U-3 | PRE-06 只读核查无名为 `advisor` 的专家 | DEPLOY-001 之前 | 命中 >0 则停止 |
| U-4 | PRE-07 Key / env 键存在性计数 | DEPLOY-001 之前 | 只出数字，不回显 |
| U-5 | 首发后 Stage 1 浏览器人工验证（MV-01/02/03/04/06/07/12） + V-04、V-10 | DEPLOY-004 之后 | 用测试项目；准备评测集 |
| U-6 | （后续，需另行单独授权）OPT-A 编辑 `ib-web.env` 追加 `IB_WEB_SEARCH_PROVIDER=deepseek` | Stage 1 通过后 | 只改键值，不贴内容；无新增凭据键 |
| U-7 | OPT-B（抓取 + 出站 ACL）：**本轮不做**（Q3） | — | 留档见 DEPLOY-008 |
| U-9 | PRE-03 lxml 不满足时升级（Q5） | 仅失败时，PRE-03 之后 | 用户 sudo 会话；代理不安装依赖 |
| U-8 | 所有需 sudo 口令的动作；`daemon-reload` / `nginx reload`：本轮不需要 | — | Q5 |

## 用户裁决（CP-004，2026-11-04，用户原话「Q1: A，其他按照推荐」，经主会话转述）

| ID | 问题 | 裁决（已落入步骤） |
|---|---|---|
| Q1 | DEPLOY-005：是否随本次重启 ib-worker | **A：不重启。** DEPLOY-005 固定为不执行，`INCLUDE_WORKER_RESTART` 缺省 false |
| Q2 | PRE-02 判 CLASS-E 时的处置 | **推荐 ①：** 先单独发布前序 ib-embed 提交（重启 ib-embed 并验证），再进行本轮；DEPLOY-006 不与本轮同批（见 PRE-02、DEPLOY-006） |
| Q3 | 首发策略与 OPT-A / OPT-B | **推荐：** 首发联网全关（`IB_WEB_SEARCH_PROVIDER=none`、`IB_WEB_FETCH_ENABLED=0`）；Stage 1 通过后 OPT-A（DEPLOY-007）需用户在主会话本轮单独授权；OPT-B（DEPLOY-008）本轮暂不启用 |
| Q4 | MV-15 / MV-16 破坏性分支 | **推荐：** 只做无破坏部分；制造 429 / 402 的真实计费调用与删除生产 LLM Key 回退环境变量分支推迟到维护窗口（MV 排期标「推迟（维护窗口）」） |
| Q5 | PRE-03 lxml 不满足谁升级 | **推荐：** 用户在 sudo 会话中升级，代理不安装依赖（见 PRE-03 失败处置） |
| Q6 | checklists.txt 009 项 `B30` | **推荐：** 下一轮由 software-developer 补（遵守 P-DE-001：保留 `B1–B27` 签署行，另起一行写 B30）；本轮签署以 selfcheck `web_governance_schema_single_source` + CI 009 门为准 |

另：DEF-003 已按用户裁决关闭（理解步骤异常 fail-open 为设计行为），对部署无影响。提交由主会话在用户确认后执行（PRE-00 不变）。

## 下游产物同步核对（M-DE-001 / 003 / 004 / 008）

| 产物 | 核对方法与结论 | 处置 |
|---|---|---|
| `.github/workflows/ci.yml` | 仅「Schema / migration check」追加 009 检查（+42/-1）；已在开发机原样执行该 step 的脚本并做 3 个反例变异（见 cicd_pipeline.md） | **已改**（PM 明确要求） |
| `src/deploy/checklists.txt` | 无 009 对应项；`B1–B27` 签署行与 selfcheck 断言未改 | 本组不改；Q6 已裁决：下一轮由 software-developer 补 B30 |
| `src/deploy/env.example` | 与 module_design 一致：三键均为注释行、无凭据键、无 `IB_WEB_SEARCH_API_KEY` / `IB_WEB_SEARCH_BASE_URL`；`git diff` 仅 +10 行注释（本组已核对） | 无需修改；不被服务读取，目标机 env 由用户维护 |
| `src/deploy/systemd/*.service`、`nginx/*` | `git status` 无改动；PRE-02 CLASS-X 机械复核 | 无需修改 |
| `src/requirements*.txt` | 各 +1 行 `lxml>=5.0,<7.0`，两份一致；不触碰 `requirements-embed.txt`（torch 永不进基座） | 无需修改；目标机仅核对 |
| `package.json` / `package-lock.json` | 无改动 → 不执行 `npm ci` | 无需修改；PRE-02 复核 |
| 009 迁移文件 | 头注释含回滚说明且无可执行 `DROP`；与 `web_governance_ddl_script()` 去空白单源一致（CI 门 + selfcheck 双重断言） | 不改 |
| `docs/deployment_plan.md`（REV-21 基线）、`deployment_report.md` | 只读 | 未改 |

## `[INFERRED]` 汇总（画像与设计均未给出的取值）

ib-web 不可用 10–30 秒、就绪轮询 30×2 秒；ib-worker 轮询 20×3 秒与观察 15 秒、命令超时 ≥ 360 秒；ib-embed 就绪轮询 40×3 秒、启动 1–2 分钟；PRE-03 磁盘 / 内存余量（1 GiB / 1 GiB）；构建命令超时 ≥ 300 秒；web root 副本目录 `~/ib-webroot-pre-r28`；定义文档位于 `/var/lib/intelligentbase` 下 `*.json` 且含顶层 `experts` 列表（PRE-06 扫描假设）；目标机 `cd src` 后 `ib` / `ibweb` 可导入（DEPLOY-002）；`/api/web-governance` 未鉴权访问返回 401 / 403；旧代码对含 `advisor` 专家但无联网授权的定义可正常加载；旧 `ensure_schema` 不因多余表 `web_governance` 失败；ib-worker 惰性 import 混用风险；出站 ACL 建议（拒内网网段并保留 loopback / DNS / DeepSeek）；venv 升级权限（需 sudo）。
`[TOOL_UNREGISTERED]`：`gh`（仅 PRE-00 取证便利，网页可替代）。
