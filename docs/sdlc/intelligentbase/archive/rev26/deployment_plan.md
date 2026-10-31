<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-27T16:32:41+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>tech_stack.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>test_plan.md</file>
    <file>unit_test_report.md</file>
    <file>integration_test_report.md</file>
    <file>e2e_test_report.md</file>
    <file>phase_status.md</file>
    <file>cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：项目 agent 编排可视化配置（INCREMENTAL，REV-26，仅计划）

> **本文件不执行任何步骤；本轮不部署。** 用户 CL-008（2026-10-27）：「接受。等部署的时候验证。现在暂时不部署」。phase_status 中 GROUP_E2 = NOT_AUTHORIZED。本轮未连接目标机、未 ssh、未 commit / push（画像 P9）。下列命令是将来 E2 获得 `PRODUCTION_DEPLOY_CONFIRM=true`（环境名 `production`）后才可执行的**计划内容**。
> 基线 `docs/deployment_plan.md`（REV-21）只读；上一轮 `archive/rev25/deployment_plan.md` 只读参考，本文沿用其执行约定与回滚结构，另立 R26 独立计划（画像 P2）。
> 依据：`.claude/skills/ib-prod-deploy/SKILL.md`（§1–§9）、`module_design.md`「数据迁移」「受影响的运行单元 / 构建」、`e2e_test_report.md`「目标机上线验证项」与「上线后人工浏览器验收清单」、`src/deploy/checklists.txt` [B29]、GR-C-001 / GR-D-002 的 condition。
> 测试门控：phase_status 中 GROUP_D = APPROVED（GR-D-002 OVERRIDDEN：critical path 23/24 = 0.96，用户 CL-008 接受，浏览器交互在部署时人工验收）。PM 复跑：tests/unit 509 / integration 333 / e2e 51 / agents 15 passed；npm test 77/77/0；npm run build 成功；selfcheck 57/58（`core_framework_free` 为本机 venv 既有失败，HEAD 干净导出同样失败）。三份测试报告均已 APPROVED，门控满足。

## 给 PM 的部署计划摘要（供将来向用户请求 E2 授权）

| 项 | 内容 |
|---|---|
| 目标环境 | `production`（单台物理机 192.168.31.133，SSH 密钥；画像 P7"部署需用户确认=是"）。无 staging。**当前未授权。** |
| 策略 | **recreate**（单机 systemd 重启；画像唯一允许）。ib-web 不可用约 10–30 秒 `[INFERRED]`；ib-worker 重启最长等 300 秒（`TimeoutStopSec=300`，用户无感）；**内存态聊天会话与"人工确认挂起态"会丢失**（A06：挂起态仅进程内、重启后 fail-closed）；前端发布无停机。此后配置变更不再需要重启（热生效）。 |
| 步骤数 | 预检 11（PRE-00~10；PRE-00 为主会话，PRE-06~10 为用户执行）；部署 **4**（DEPLOY-001 git pull → 002 重启 ib-web〔自动应用 008〕→ 003 重启 ib-worker → 004 前端构建发布）；部署后验证 14（V-01~14，其中 V-05/07/09/10/11/12/13/14 含用户执行）；回滚 ROLLBACK-000/001a/001b/001-E/002a/002b/003/004（正式 7 + 紧急止血 1） |
| 不变面 | ib-embed、qdrant、nginx（**不 reload**）、全部 systemd unit（**无 daemon-reload**）、`src/requirements*.txt`、`package.json` / `package-lock.json`、`/etc/intelligentbase/*.env`（4 个可选键缺省值即可运行，**不要求改 env**）；不新增依赖 / systemd 单元 / Docker / nginx 改动；单 ib-worker。 |
| 不可逆 / 需人工 | **4 项** `[MANUAL_ROLLBACK_REQUIRED]`：① 008 新表 / 新列 DROP（ROLLBACK-002b，默认不执行）；② v2 配置文件态在旧代码下不可读，回退代码前须还原为 v1（ROLLBACK-000 路径 B 为人工分支）；③ 已发生的 DeepSeek 云端外发无法撤回（验收 B7/B10）；④ 上线后验收/使用产生的版本历史、草稿、评审缓存在 DROP 后丢失。详见「不可逆步骤汇总」。 |
| 回滚方式 | 源头 `git revert` → 用户确认后 push（主会话）→ 目标机 `git pull --ff-only` → 重启 ib-web / ib-worker、重建前端。回退代码前**必须先通过 ROLLBACK-000**。不使用 `reset --hard` / `clean` / `stash`。**配置版本回滚（产品功能）≠ 代码回滚**，见「回滚步骤」开头。 |
| 需要用户（非代理）执行 | 提交并 push 待部署提交（PRE-00，主会话经用户确认）；台账与配置文件备份（PRE-06，`sudo`）；台账只读基线查询（PRE-07）；env 键存在性计数（PRE-08，可选）；部署后结构核对 V-07；热生效探针 V-09；**上线后人工浏览器验收 V-12（A1~A4、B1~B10 全部必做）**；`daemon-reload` / unit 安装 / env 修改 / `nginx reload`：**本次均不需要**。 |
| 前提（E2 授权时由 PM 填入 `special_instructions`） | `PRODUCTION_DEPLOY_CONFIRM=true`；环境名 `production`；`DEPLOY_COMMIT=<40 位哈希>`（用户确认并 push 的待部署提交；**当前工作区改动尚未提交，含大量 untracked 新文件**，见 PRE-00）；计划版本 = phase_status 登记的 APPROVED 版本。 |

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启 / 发布的运行单元 |
|---|---|---|---|---|
| 台账结构 | `src/ib/ledger/schema.py`、`config_versions.py`（新）、`accounts.py`、`config_audit.py`、`tree.py`、`src/deploy/migrations/008_config_versions.sql`（新） | **008**：4 张新表 + 2 个索引（`config_versions` / `config_head` / `config_drafts` / `builder_eval_cache`）+ `users.config_level`（`ALTER ADD COLUMN … NOT NULL DEFAULT 'manage' CHECK`）+ `config_audit` 3 个可空列；`IF NOT EXISTS` + `PRAGMA table_info` 探测，幂等；由 `ib-web.service` 的 `ExecStartPre … --ensure-schema` 自动应用 | — | `ib-web`（重启即应用） |
| 配置层 / 版本化 / 图 | `src/ib/config/{__init__,definition,prompts}.py`、`graph.py`、`access.py`、`versioning.py`（新）、`src/ib/core/{__init__,ports,types}.py`、`graph.py`（新）、`src/ib/confsvc/`（新） | 无（文件态数据不迁移；v1 文档保持 v1，首次保存才升 v2） | — | `ib-web` + `ib-worker` |
| 运行时 / 编排 / 检索 / LLM | `src/ib/runtime/`（新）、`src/ib/orchestration/{__init__,dag}.py`、`src/ib/{retrieval,routing/intent,streaming,tools,llm,observability}/`、`src/ibweb/{composition,worker}.py` | 无 | — | `ib-web` + `ib-worker` |
| Agent Builder | `src/ib/builder/`（新，含 `assets/*.md` 提示词模板） | 无 | — | `ib-web` |
| Web 接口层 | `src/ibweb/{config_views,builder_views}.py`（新）、`views.py`、`urls.py`、`serializers.py`、`accounts/__init__.py` | 无 | — | `ib-web` |
| 前端 | `src/frontend/src/{api/client.ts,api/builderTypes.ts,router/index.ts,stores/configDraft.ts,views/{ConfigHub,ConfigStudio,ConfigPage,AccountsPage}.vue,components/**}` | 无 | 目标机 `npm run build`（`package-lock.json` 未变，不 `npm ci`） | 不重启，拷贝 web root |
| 自检 / 清单 / 探针 / CI | `src/scripts/{selfcheck.py,hot_effect_probe.py(新)}`、`src/deploy/checklists.txt`（[B29]）、`src/deploy/env.example`（4 个可选键名）、`.github/workflows/ci.yml` | 无 | — | 不影响运行（非运行时交付物） |
| **不变** | ib-embed、qdrant、nginx、全部 systemd unit、`src/requirements*.txt`、`package*.json`、`/etc/intelligentbase/*.env` | — | — | 无（PRE-02 用 `git diff` 机械核对） |

**"改什么重启什么"核对（SKILL.md §6）**：`ibweb/**` → ib-web ✓（DEPLOY-002）；`ibweb/worker.py` 与共享的 `ib.ledger` / `ib.core` / 入库链路 → ib-worker ✓（DEPLOY-003）；`ib_embed` 无改动 → 不重启 ✓；前端 → 不重启、拷贝 web root ✓（DEPLOY-004）；env 无必改项 ✓；unit / nginx 零变更 → 无 `daemon-reload`、无 `nginx reload` ✓；迁移 008 → 随 ib-web 重启自动应用 ✓（手工 `sqlite3 < 008` 不补 `users` / `config_audit` 的列，**部署路径只能是 ib-web 重启**，见 008 头注释）。

**新增 4 个可选 env 键（只写键名，缺省值即可运行；`/etc/intelligentbase/*.env` 由用户按需自行添加，本计划不要求添加）**：`IB_CONFIG_HEAD_CHECK_INTERVAL_S`、`IB_GRAPH_RUNTIME`、`IB_LLM_CLIENT_CACHE_MAX`、`IB_DOC_SCOPE_MAX_IDS`。它们在 `src/deploy/env.example` 中已注释登记；该模板为 ib-web / ib-worker 共用示例，写入哪个 env 文件按 SKILL.md §6 末段"只加在对应服务"由用户决定（键写错文件不报错、静默无效）。**不得回显或读取** `/etc/intelligentbase/*.env` 的值。

## 目标环境与策略

- **环境**：`production`（画像 P7）；SSH 密钥 `~/.ssh/ib_prod_ed25519`，主机 / 用户见 SKILL.md §1–§2。不设计 staging。
- **策略：recreate**。理由：单机、单实例（ib-web ×1、ib-worker ×1，**禁多实例**〔画像 P8〕）、无负载均衡与第二套环境，rolling / blue-green / canary 均无基础设施。
- **步骤顺序理由**：`git pull` → 先 ib-web（`ExecStartPre` 先应用 008 补列与建表；`ib-worker.service` 本就 `After=ib-web.service`）→ 再 ib-worker → **最后**发布前端（新配置 UI 只在后端就绪后才对用户可见；旧前端在整个窗口内仍可用）。
- **兼容窗口**：ib-web 新、ib-worker 旧的短窗口内，旧 worker 不认识新表 / 新列，但按命名列查询，不受影响（见回滚章节对旧代码兼容性的核对）；窗口约数十秒。
- **热生效的跨进程语义**：保存在 ib-web 内立即换版；ib-worker 不服务配置请求，其对配置版本的感知由 `IB_CONFIG_HEAD_CHECK_INTERVAL_S`（缺省 1.0 s，节流探测 head）决定。本次上线后两进程均已是新代码，无需再重启。
- **预计停机**：见摘要；建议在无人使用的时段部署，请用户确认当前无进行中的聊天。

## 执行约定（引号与变量）

执行端为 bash（Git Bash / Linux），**不要**把复杂命令作为参数从 PowerShell 传入（SKILL.md §4.2 的 5.1 引号改写坑）。

```bash
# 连接函数（密钥 / 主机 / 用户见 SKILL.md §1-2；BatchMode 保证绝不回落到口令交互）
ibssh() { ssh -i ~/.ssh/ib_prod_ed25519 -o UserKnownHostsFile=/tmp/ib_kh -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@192.168.31.133 "$@"; }
```

| 规则 | 说明 |
|---|---|
| Q1 | 不含本地值的远端命令：整条放进**单引号**，`$VAR` 在**远端**展开。 |
| Q2 | 需要本地值（`ANCHOR`、`DEPLOY_COMMIT`、`REVERT_COMMIT`）：一律用 `ibssh bash -s -- "$A" "$B" <<'EOF' … $1 $2 … EOF`——本地双引号只负责把值作为**位置参数**传过去，heredoc 用单引号定界使本地不展开，远端用 `$1 $2`。**禁止**写 `ibssh 'git checkout $ANCHOR -- …'`（`$ANCHOR` 在远端为空）。markdown 里 heredoc 代码块须顶格粘贴（缩进会破坏 `EOF` / python 缩进）。 |
| Q3 | 单引号内有意在远端定义并使用的变量（如 `TS=$(date …)`）是远端变量，属预期。 |
| Q4 | 变量取值与核验：`ANCHOR` = PRE-01 输出的 40 位 `git rev-parse HEAD`；`DEPLOY_COMMIT` = PM 在 `special_instructions` 下发；`REVERT_COMMIT` = ROLLBACK-001a 产生。使用前先本地核验 `[[ "$X" =~ ^[0-9a-f]{40}$ ]]`，并在远端 `git cat-file -t "$X"` 必须输出 `commit`；PRE-02 / ROLLBACK-001b 内置该核验。 |
| Q5 | 台账只读查询 / 备份一律在目标机上以 **`sudo -u ib-web`** 身份执行并用 `mode=ro` 打开（root 打开台账会把 `-wal` / `-shm` 建成 root 属主，见 checklists B22）；这些命令需口令，**由用户在交互式会话中粘贴执行**，输出只含名称、版本号与计数。**迁移前的基线查询不得引用 008 新增的列 / 表**（P-DE-002）。 |
| Q6 | 凭据：令牌只经执行者 shell 的环境变量（如 `IB_PROBE_TOKEN`，用 `read -rs` 读入）注入，不回显、不入日志、不入库、不入命令行参数；不读取、不回显 `/etc/intelligentbase/*.env` 的值（仅 `grep -c` 计数）；**禁止** `printf '<口令>' | sudo -S`；**禁止** scp / pscp / rsync 向生产传代码。本仓库 PUBLIC，本文不含任何凭据或内网口令。 |

## 预检清单

执行者：`A` = devops 代理经 ssh（E2 授权后）；`U` = 用户（需 sudo 口令）；`M` = 主会话（经用户确认，画像 P9）。任一项不通过：**停止，不进入 DEPLOY-001**（目标环境尚无变更，报告 `DEPLOYMENT_FAILED`，无需回滚）。

| ID | 检查项 | 执行者 | 通过标准 |
|---|---|---|---|
| PRE-00 | 待部署提交已在远端；新文件已入库；待部署提交的 CI 全绿（含 008 迁移门，PIPE-02） | M | 见下 |
| PRE-01 | 目标机 HEAD 记录为**回滚锚点**；跟踪文件无本地修改 | A | HEAD 为 40 位哈希且记入报告；无 ` M` 的已跟踪文件 |
| PRE-02 | 变更集与目标机本地状态不冲突；"不变"面确无改动 | A | 交集为空；systemd / nginx / ib_embed / requirements / package*.json 零改动；`src/deploy` 仅 `migrations/008_config_versions.sql`、`checklists.txt`、`env.example` |
| PRE-03 | 磁盘 / 内存 / 工具链余量 | A | `/var/lib/intelligentbase` 所在盘可用空间 ≥ 台账大小（PRE-06 备份）的 2 倍 + 2 GiB `[INFERRED]`；内存可用 ≥ 2 GiB `[INFERRED]`；node / npm 可用 |
| PRE-04 | **目标机 SQLite 版本与 008 补列行为探针**（`ALTER ADD COLUMN … NOT NULL DEFAULT … CHECK`、`IF NOT EXISTS`、`DROP COLUMN` 能力） | A | 探针输出 `config_level= manage`、`CHECK_ENFORCED`；版本记入报告；`DROP_COLUMN_OK` 仅为 ROLLBACK-002b 所需（不足不阻塞部署，改"重建表"人工路径） |
| PRE-05 | 服务与时钟基线 | A | 5 个单元 active；记录 ib-web / ib-worker / ib-embed 的 `ActiveEnterTimestamp` 与 `NRestarts` |
| PRE-06 | **备份（迁移 008 前）**：台账 SQLite + 定义文档 / 提示词文件态 | U | 备份文件 660 `ib-web:ib`，完整性 ok，行数一致；只拷贝、不回显内容 |
| PRE-07 | 迁移前只读基线（不引用 008 新列）：账号 / 项目计数、定义文档 `schema_version` | U | 数值记入报告（V-07 / ROLLBACK-000 对照） |
| PRE-08 | （可选）4 个可选键名是否已存在（仅计数） | U | 计数记录；不回显值；不要求添加 |
| PRE-09 | 无进行中的重建 / 入库高峰；告知用户重启会丢内存态会话 | U | `rebuild_open` 无 `planned`/`running`（沿用 R25 口径）；用户确认当前无进行中的聊天 |
| PRE-10 | 验收前置：用户备好验收用**独立测试项目**与**管理档测试账号**、浏览器、`IB_PROBE_TOKEN` 的获取方式（不入库） | U | 用户书面确认；验收不动生产业务配置（e2e_test_report 清单背景） |

### PRE-00（主会话，开发机；push 由主会话在用户确认后执行，子代理不 push）

```bash
# DEPLOY_COMMIT 由主会话在用户确认后 commit+push 得到
git status --porcelain                          # 不得遗漏 src/ tests/ 下的 '??' 新文件
git ls-files --others --exclude-standard src tests | wc -l     # 期望 0（提交后无遗漏的未跟踪文件）
git ls-remote origin refs/heads/main            # 首列必须 == DEPLOY_COMMIT
git ls-tree -r --name-only "$DEPLOY_COMMIT" | grep -cE '^(src/deploy/migrations/008_config_versions\.sql|src/ib/builder/service\.py|src/ib/builder/assets/generate\.md|src/ib/confsvc/publish\.py|src/ib/runtime/compile\.py|src/ib/orchestration/dag\.py|src/ib/config/graph\.py|src/ib/ledger/config_versions\.py|src/ibweb/config_views\.py|src/ibweb/builder_views\.py|src/scripts/hot_effect_probe\.py|src/frontend/src/views/ConfigStudio\.vue)$'     # 期望 12
```

- **为什么查新文件**：当前 `git status` 显示 008 迁移、`src/ib/{builder,confsvc,runtime}/`、`config_views.py`、`builder_views.py`、`components/` 等均为 **untracked**（共 43 个未跟踪的 src 文件，不含 tests / docs）；漏 `git add` 则目标机 `git pull` 后缺文件，ib-web 起不来。`src/ib/builder/assets/*.md` 是运行时读取的提示词模板，不能漏。
- **CI**：在 GitHub Actions 确认 `DEPLOY_COMMIT` 的 CI 运行全部成功（含 PIPE-02 新增的 008 门）。红灯不得部署。**本组无法运行 GitHub Actions，008 门仅在本机等价脚本验证过**（见 cicd_pipeline.md），首次 push 后的真实结果为准。`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`，仅为可选便利，网页查看等价。
- 仓库为 PUBLIC：`deploy_templates_have_no_secrets` 自检在 selfcheck 中（PM 复跑 57/58，失败项为环境项）。

### PRE-01（A）

```bash
ibssh 'cd /opt/intelligentbase && git rev-parse HEAD && git log --oneline -1 && git status --porcelain'
```

输出的 40 位哈希即 `ANCHOR`，写入 deployment_report 首节并在后续命令作为本地变量使用。已跟踪文件修改（` M`）必须为空；`??` / 被忽略项（venv、node_modules 等）属本地状态，只记录、不触碰。

### PRE-02（A）

```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git cat-file -t "$1")" = commit ]
git fetch origin main
[ "$(git cat-file -t "$2")" = commit ]                   # 待部署提交已在远端对象库
[ "$(git rev-parse origin/main)" = "$2" ]                # origin/main 恰为待部署提交（防 pull 拉到更新的提交）
git merge-base --is-ancestor "$1" "$2"                   # 锚点是其祖先 => ff-only 可行
echo "--- 变更文件数:"; git diff --name-only "$1" "$2" | wc -l
echo "--- 与目标机本地修改的交集(期望为空):"
comm -12 <(git diff --name-only "$1" "$2" | sort) <(git status --porcelain | awk '{print $2}' | sort)
echo "--- 不应变化的部署面(期望为空):"
git diff --name-only "$1" "$2" -- src/deploy/systemd src/deploy/nginx src/ib_embed src/requirements.txt src/requirements-embed.txt src/requirements-offline.txt src/frontend/package.json src/frontend/package-lock.json
echo "--- src/deploy 变更(期望仅 008、checklists、env.example):"
git diff --name-only "$1" "$2" -- src/deploy
EOF
```

`git fetch` 只更新远端跟踪引用，不改工作树。"不应变化的部署面"非空 → 依赖或 unit 有变，超出本计划范围，停止上报。

### PRE-03（A）

```bash
ibssh 'df -B1 --output=target,size,used,avail,pcent /var/lib/intelligentbase /var/lib/qdrant /opt/intelligentbase /var/www/intelligentbase; free -m | sed -n 1,2p; node -v; npm -v'
```

`yangyang198354` 不在 `ib` 组，台账大小由 PRE-06 的用户命令回报（`sudo du -sb`）。`snapshot_json` 存提示词全文，保留 50 版，最坏约 2–6 MB / 版（module_design 数据风险 ①，TBD-T33），磁盘余量判定宽松即可。

### PRE-04（A）：目标机 SQLite 行为探针（纯内存，不触台账，不依赖尚未拉取的代码）

```bash
ibssh /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
print("sqlite_version=", sqlite3.sqlite_version)
c = sqlite3.connect(":memory:", isolation_level=None)
c.execute("CREATE TABLE users (user_id TEXT PRIMARY KEY, role TEXT NOT NULL)")
c.execute("INSERT INTO users VALUES ('u','ops')")
c.execute("ALTER TABLE users ADD COLUMN config_level TEXT NOT NULL DEFAULT 'manage' CHECK (config_level IN ('view','edit','manage'))")
print("config_level=", c.execute("SELECT config_level FROM users").fetchone()[0])
try:
    c.execute("UPDATE users SET config_level='bogus'")
    print("CHECK_NOT_ENFORCED")
except sqlite3.IntegrityError:
    print("CHECK_ENFORCED")
c.execute("CREATE TABLE IF NOT EXISTS t (a INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS t (a INTEGER)")
c.execute("ALTER TABLE t ADD COLUMN b INTEGER")
try:
    c.execute("ALTER TABLE t DROP COLUMN b")
    print("DROP_COLUMN_OK")
except sqlite3.OperationalError as e:
    print("DROP_COLUMN_UNSUPPORTED", e)
PY
```

- 用服务解释器（`/opt/intelligentbase/venv`）而非系统 `sqlite3` CLI，因为 ib-web / ib-worker 链接的是该解释器的 SQLite。
- 判定：`config_level= manage` 且 `CHECK_ENFORCED` 为部署硬门（`NOT NULL DEFAULT` + `CHECK` 的 `ADD COLUMN` 在目标机行为与开发机 3.45.1 一致）；任一不符 → **停止并上报**，不进入 DEPLOY-001。`DROP_COLUMN_OK` 仅关系 ROLLBACK-002b（需 SQLite ≥ 3.35，开发机 3.45.1 已实测 008 的 DROP 序列可执行；目标机以本探针为准）。
- 设计依据：目标机为 Ubuntu 26.04，预计远高于门槛 `[INFERRED]`，以实测为准。

### PRE-05（A）

```bash
ibssh 'date "+%F %T %Z"; systemctl is-active ib-web ib-worker ib-embed qdrant nginx; systemctl show -p ActiveEnterTimestamp,NRestarts ib-web; systemctl show -p ActiveEnterTimestamp,NRestarts ib-worker; systemctl show -p ActiveEnterTimestamp ib-embed'
```

全部 `active` 才继续。`ib-embed` 的 `ActiveEnterTimestamp` 作为 V-10 的"未被重启"对照。

### PRE-06 备份（U；在交互式远端会话中粘贴，**不要**经 PowerShell 参数传入）

(a) 台账（SQLite backup API，在线一致性拷贝，含 WAL 中已提交页）：

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)                                   # 备份文件 660 ib-web:ib（与台账同口径）
src = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
dst = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r26.bak")
src.backup(dst); dst.close(); src.close(); print("backup done")
PY
sudo ls -l /var/lib/intelligentbase/ledger/ | grep -E 'ledger\.sqlite3'
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r26.bak?mode=ro", uri=True)
print("backup_integrity=", c.execute("PRAGMA integrity_check").fetchone()[0], "documents=", c.execute("SELECT COUNT(*) FROM documents").fetchone()[0], "users=", c.execute("SELECT COUNT(*) FROM users").fetchone()[0])
PY
sudo du -sb /var/lib/intelligentbase /var/lib/qdrant
```

(b) **定义文档与提示词文件态**（v1→v2 升级不可被旧代码读取，这是回滚路径 B 的唯一依据，必须备份；只拷贝与记哈希，不回显内容）：

```bash
sudo -u ib-web bash -c 'umask 007; mkdir -p /var/lib/intelligentbase/backup-pre-r26 && cp -a /var/lib/intelligentbase/definition.json /var/lib/intelligentbase/backup-pre-r26/ && cp -a /var/lib/intelligentbase/prompts /var/lib/intelligentbase/backup-pre-r26/ && ls -lR /var/lib/intelligentbase/backup-pre-r26 | head -n 40; sha256sum /var/lib/intelligentbase/definition.json'
```

- 文件 / 目录名取自 SKILL.md §7.4（`IB_DEFINITION_DOC_PATH`、`IB_EXPERT_PROMPT_DIR`）；若目标机实际路径不同或使用内存默认，以实际为准并记录 `[INFERRED]`——**不要为核对而读取 env 值**，用 `sudo ls` 看文件是否存在即可。
- 通过标准：备份存在、非空、660 `ib-web:ib`；`backup_integrity=ok`；`documents` / `users` 计数记入报告（V-07 对照）；`definition.json` 的 sha256 记入报告。
- 还原提示（回滚时用）：从台账备份还原后**必须** `sudo chmod 0660` 主库并核对属主 `ib-web:ib`（B22 陷阱）。验收通过后是否归档 / 删除这些备份由用户决定。

### PRE-07 迁移前只读基线（U；此刻 `users` / `config_audit` 尚无 008 新列，脚本不得引用）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import json, sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
print("users_by_role=", c.execute("SELECT role, COUNT(*) FROM users GROUP BY role ORDER BY role").fetchall())
print("config_audit_rows=", c.execute("SELECT COUNT(*) FROM config_audit").fetchone()[0])
print("rebuild_open=", c.execute("SELECT project_id, from_version, to_version, state FROM rebuild_jobs WHERE state IN ('planned','running','succeeded')").fetchall())
print("documents_total=", c.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
try:
    d = json.load(open("/var/lib/intelligentbase/definition.json", encoding="utf-8"))
    print("definition_schema_version=", d.get("schema_version"))     # 只打印版本号，不打印内容
except FileNotFoundError:
    print("definition_schema_version= N/A (file absent)")
PY
```

用途：① 上线后 V-07 对照"存量账号数不变、存量 ops 全为 manage"；② ROLLBACK-000 判断文件态是否仍为 v1。若目标机采用多文件 / 分项目布局，则按文件逐个回报 `schema_version`（布局以目标机实际为准 `[INFERRED]`）。

### PRE-08（U，可选，只计数不回显）

```bash
sudo grep -c -E '^(IB_CONFIG_HEAD_CHECK_INTERVAL_S|IB_GRAPH_RUNTIME|IB_LLM_CLIENT_CACHE_MAX|IB_DOC_SCOPE_MAX_IDS)=' /etc/intelligentbase/ib-web.env
```

仅回报计数，不要求添加任何键。未知键被配置层忽略，故提前写入对旧代码无害。

## 部署步骤

所有 DEPLOY 位置均为**目标机**（经 ssh），预检全部通过后按序执行；任一步失败按"失败处理矩阵"处置。

### DEPLOY-001: 目标机拉取代码（`git pull`，禁 scp / pscp / rsync）
- 组件: 全部后端 + 前端源码 + 迁移文件（architecture_design 部署视图：基础设施无变更 → 数据层 → 服务层 → 前端）
- 位置: 目标机 `/opt/intelligentbase`（属主 `yangyang198354`，免 sudo）
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git rev-parse HEAD)" = "$1" ]                      # 前置：仍在锚点，未被中途改动
git fetch origin main
[ "$(git rev-parse origin/main)" = "$2" ]               # 前置：远端恰为待部署提交；否则中止（此时尚无变更）
git pull --ff-only origin main                          # 等价于画像 P7 的 git pull origin main，加 --ff-only 禁止产生合并提交
[ "$(git rev-parse HEAD)" = "$2" ]                      # 后置：精确等于待部署提交
git log --oneline -1
git status --porcelain
EOF
```
- 预期: fast-forward 到 `DEPLOY_COMMIT`；`git status --porcelain` 无已跟踪文件修改；退出码 0。
- 回滚: ROLLBACK-001（001a + 001b）

### DEPLOY-002: 重启 ib-web（`ExecStartPre --ensure-schema` 自动应用 008：补列 + 建表）
- 组件: ib-web（Waitress，127.0.0.1:18080）、台账 schema（数据层）
- 位置: 目标机；`sudo -n systemctl restart ib-web`（三条免密 restart 之一，SKILL.md §4）
- 命令:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-web; for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/healthz)" = 200 ] && break; sleep 2; done; systemctl is-active ib-web; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-web; journalctl -u ib-web --since "$TS" --no-pager | grep -E "startup succeeded|ConfigError|OperationalError|Traceback|unable to open|runtime_compile_failed|config_drift" | tail -n 20'
```
  （`$TS` 在**远端**定义并展开，属 Q3；`RESTART_TS` 记入报告，供 V-02 / V-03 / V-06 复用。）
- 预期: `/healthz` 200；`is-active`=active、`SubState=running`、`NRestarts=0`；日志出现 `startup succeeded`，`ConfigError` / `OperationalError` / `Traceback` / `runtime_compile_failed` / `config_drift` 零命中。`restart` 时的 `daemon-reload` pending 警告是长期存在的，不是本次引入（SKILL.md §7.2），不处理。
- 失败特征: `ExecStartPre` 失败时 `Restart=on-failure` 每 3 秒重试，日志刷屏——立即进入回滚，不要反复重启。`ensure_schema` 分阶段提交（先补列、再建表），失败时可能已补列 / 建表；这些结构纯追加，旧代码按命名列查询并忽略，不构成回滚障碍。
- 回滚: ROLLBACK-002（002a 常规；002b 为人工 DROP，默认不执行）

### DEPLOY-003: 重启 ib-worker（单实例）
- 组件: ib-worker（入库队列 + 重建推进 + 本次新增的维护步骤；共享 `ib.ledger.schema` / `ib.core` 变更）
- 位置: 目标机；`sudo -n systemctl restart ib-worker`
- 命令（`TimeoutStopSec=300`，执行端命令超时需 ≥360 秒 `[INFERRED]`）:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-worker; for i in $(seq 1 20); do [ "$(systemctl is-active ib-worker)" = active ] && break; sleep 3; done; sleep 15; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-worker; echo "errors_in_log=$(journalctl -u ib-worker --since "$TS" --no-pager | grep -cE "unable to open database file|Traceback|OperationalError")"; pgrep -c -f "[i]bweb\.worker"'
```
- 预期: `ActiveState=active`、`SubState=running`、`NRestarts=0`；`errors_in_log=0`（含 B22 的"unable to open database file"无限重启特征）；`pgrep -c` 为 **1**（`[i]` 写法避免匹配到执行命令自身；单实例，画像 P8 禁多实例）。等待 15 秒 ≥ 两轮 `--interval 5`。
- 回滚: ROLLBACK-003

### DEPLOY-004: 前端构建并发布到 web root（不重启任何服务）
- 组件: 前端静态产物（nginx 直读 `/var/www/intelligentbase/`，属主 `yangyang198354`，无需 sudo；nginx 不改、不 reload）
- 位置: 目标机 `/opt/intelligentbase/src/frontend`（`node_modules` 已就位；`package-lock.json` 未变故不执行 `npm ci`）
- 命令（先留旧产物副本，再构建，构建成功才替换）:
```bash
ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r26 ]; mkdir ~/ib-webroot-pre-r26; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r26/; ls ~/ib-webroot-pre-r26'
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u'
```
- 预期: `vue-tsc --noEmit && vite build` 退出码 0；打印新的 `assets/index-<hash>.js`；`systemctl show -p ActiveEnterTimestamp ib-web` 与 DEPLOY-002 后相同（发布未触发重启）。构建失败时 `&&` 链在 `rm` 之前中断，web root 仍是旧产物（无停机）。
- 回滚: ROLLBACK-004
- 说明: 旧副本放在部署用户家目录（仓库外、不入 git），验收后由用户决定删除；`index.html` 为 `no-store`，`assets/*` 带新 hash，硬刷新即生效（SKILL.md §5.2）。前端构建环境（目标机 node 22）与 CI（Node 20）不同，属已知风险（见 cicd_pipeline「制品管理」）。

## 回滚步骤（逆序）

**先区分两种"回滚"，不要混用：**

| | 配置版本回滚（产品功能） | 代码回滚（本节 ROLLBACK-xxx） |
|---|---|---|
| 作用对象 | 某项目的**配置内容**（agent、路由图、提示词、权限）回到历史版本 | **程序代码 / 迁移 / 前端**回到部署前的提交 |
| 执行方式 | 在已上线的新代码上，用配置页"版本 → 回滚"（`POST /api/config/rollback`，需管理档），**热生效、无需重启**；产生一个新版本（kind=rollback） | `git revert` → push → 目标机 pull → 重启 ib-web / ib-worker、重建前端 |
| 能否撤销 | 可再次回滚到任一保留版本（保留 50 个） | 回退后旧代码**不认识**版本表与 v2 文档 |
| 何时用 | 线上配置改坏了、代码本身没问题 | 新代码有缺陷、需整体退回 |

执行总序：**ROLLBACK-000（前置门）→ 001a（源头 revert + push）→ 001b（目标机 pull）→ 004 → 003 → 002a →（002b 默认不执行）**。ROLLBACK-001 是把"目标机代码状态"还原的载体，必须先于各单元重启落地；其余按 DEPLOY 的逆序（前端 → worker → web）。目标机 pull 到 ib-web 重启之间，ib-web 进程仍在内存中运行新代码，窗口应尽量短。

**不得破坏的本地状态**（全部回滚路径均不触碰）：`/etc/intelligentbase/*.env`、`/var/lib/intelligentbase/`（台账、blob、definition.json、prompts；ROLLBACK-000 路径 B 是唯一例外且由用户执行）、bge-m3 权重、Qdrant 数据、`/opt/intelligentbase/venv`、前端 `node_modules`。**本计划所有回滚均不使用** `git reset --hard`、`git clean`、`git stash`、覆盖式同步。

**旧代码对 008 的兼容性（已核对，回滚可行性的依据）**：
- `users`：旧代码 `accounts.py` 的 `INSERT INTO users (<命名列清单>)`、查询用 `_U_COLUMNS` 命名列，无 `SELECT *`（`git show HEAD:src/ib/ledger/accounts.py` 实测 0 处；`git grep` 无 `SELECT * FROM users`）；新列 `config_level` 为 `NOT NULL DEFAULT 'manage'`，旧代码插入时由默认值填充且满足 CHECK，**旧代码可正常建号 / 读号**。
- `config_audit`：旧代码按 `_A_COLUMNS` 命名列插入 / 查询（`HEAD:src/ib/ledger/config_audit.py:165,193`，文中 `SELECT *` 仅出现在注释）；新增 3 列可空，**被忽略**。
- 新增 4 张表：旧代码不引用，**被忽略**；旧版 `ensure_schema` 全是 `IF NOT EXISTS` / 探测式，对多出的表 / 列无动作。
- **唯一不兼容**：v2 定义文档（`schema_version == 2`）旧代码**不可读**（旧 `SUPPORTED_SCHEMA_VERSION == 1`），启动即报错——这是 ROLLBACK-000 存在的原因。
- 结论：**回滚时无需 DROP 新表 / 新列**；DROP 由用户另行决定（ROLLBACK-002b）。

### ROLLBACK-000: 回滚前置门（任何"回退代码"之前必须通过；checklists [B29](3)）
- 类型: 正式回滚的前置检查与清理（U）
- 原因: ① 旧代码只认 `schema_version == 1`，文件态若已被新代码保存为 v2，回退后 ib-web 无法启动；② 存在 `pending` 版本表示发布中途（崩溃遗留），应先让新代码回收。
- 命令 A（只读核对；`config_*` 表不存在时按"尚未迁移"处理）:
```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import json, sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if "config_head" in tabs:
    print("config_head=", c.execute("SELECT project_id, published_version, pending_version FROM config_head ORDER BY project_id").fetchall())
    print("pending_projects=", c.execute("SELECT project_id FROM config_head WHERE pending_version IS NOT NULL").fetchall())
    print("baselines=", c.execute("SELECT project_id, version FROM config_versions WHERE kind='baseline' ORDER BY project_id").fetchall())
else:
    print("config_head= (table absent)")
try:
    d = json.load(open("/var/lib/intelligentbase/definition.json", encoding="utf-8"))
    print("definition_schema_version=", d.get("schema_version"))
except FileNotFoundError:
    print("definition_schema_version= N/A")
PY
```
- 处置:
  - `pending_projects` 非空：保持新代码运行，等待陈旧 pending 被回收（`recover`，装配期 / 下一次保存触发），复查；不为清 pending 而手工改库。
  - `definition_schema_version == 1`（或 N/A）：文件态仍是 v1，**直接通过**。
  - `definition_schema_version == 2`：**路径 A（优先，用户在新代码仍运行时操作）**——对每个已升级项目，用 `baselines` 查到的"升级前基线"版本号，在配置页"版本 → 回滚到该版本"（或 `POST /api/config/rollback`，需管理档），使文件态写回 v1 内容；随后重跑本命令，须得到 `definition_schema_version= 1`。回滚是热生效的配置发布，会新增一条 kind=rollback 版本与审计，不改代码。
  - 路径 A 不成立（基线已被 50 版保留策略修剪 / `baselines` 缺项 / 回滚后仍为 2）→ **路径 B** `[MANUAL_ROLLBACK_REQUIRED: 以 PRE-06(b) 备份还原 definition.json 与 prompts，使文件态回到部署前内容；上线后所有配置改动（新增 agent、路由图、提示词编辑）在文件态中丢失，仅版本表 snapshot_json 中保留可供人工取回；还原需 sudo 且须在无人保存配置时进行，命令由用户逐项确认后执行，代理不自行处理]`。路径 B 的参考命令（用户执行，核对 sha256 与 PRE-06 记录一致后再动手）：`sudo -u ib-web bash -c 'cp -a /var/lib/intelligentbase/backup-pre-r26/definition.json /var/lib/intelligentbase/definition.json && cp -a /var/lib/intelligentbase/backup-pre-r26/prompts/. /var/lib/intelligentbase/prompts/'`，然后重跑命令 A。
- 通过标准: `pending_projects` 为空，`definition_schema_version` 为 1 或 N/A。
- 例外: 若失败发生在 DEPLOY-002 且 ib-web 从未成功启动（无人能保存 v2），文件态必然仍是 v1，命令 A 自然通过，仍需执行该只读核对。

### ROLLBACK-001a: 源头 revert 并 push（主会话，用户确认；回滚 DEPLOY-001 的源头部分）
- 类型: 正式回滚
- 命令（开发机）:
```bash
git fetch origin main && git switch main && git pull --ff-only origin main
git log --merges --oneline "$ANCHOR..$DEPLOY_COMMIT"                 # 期望为空；非空则 revert 需加 -m 1，先上报
git revert --no-commit "$ANCHOR..$DEPLOY_COMMIT"                      # 反向还原整段范围，合并为一个回退提交
git diff --quiet "$ANCHOR" -- src && echo SRC_EQUALS_ANCHOR           # 暂存区 src 须与锚点逐字一致
git commit -m "revert(r26): roll back orchestration-config release to ${ANCHOR}"
git push origin main
git rev-parse HEAD                                                    # = REVERT_COMMIT，记入报告
```
- 变量取值与核验: `ANCHOR` 取 PRE-01 的输出（deployment_report 首节）；执行前 `git cat-file -t "$ANCHOR"` 必须输出 `commit`，且 `git merge-base --is-ancestor "$ANCHOR" "$DEPLOY_COMMIT"` 成立。回滚用的是**新提交 + 普通 push**，不 force-push、不 reset。
- 预期: `SRC_EQUALS_ANCHOR` 打印；push 成功；CI 对回退提交自动运行（不要求等待结果才继续回滚，但须记录）。注意：`git revert` 会同时撤销 `src/deploy/migrations/008_config_versions.sql` 文件，**这不会删除目标机台账里已建的表 / 列**（文件只是快照）。

### ROLLBACK-001b: 目标机拉取回退提交（回滚 DEPLOY-001）
- 类型: 正式回滚
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$REVERT_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git cat-file -t "$1")" = commit ]                 # 锚点必须是完整哈希且为 commit
git fetch origin main
[ "$(git cat-file -t "$2")" = commit ]                 # 回退提交已在远端
[ "$(git rev-parse origin/main)" = "$2" ]
git pull --ff-only origin main
[ "$(git rev-parse HEAD)" = "$2" ]
git diff --quiet "$1" HEAD -- src && echo SRC_EQUALS_ANCHOR   # 目标机 src 与部署前逐字一致
git status --porcelain                                  # 无已跟踪文件修改
EOF
```
- 变量取值与核验: 同上；`$1`=`ANCHOR`、`$2`=`REVERT_COMMIT` 均作为位置参数传入，**不是**在单引号里直接写 `$ANCHOR`（Q2）。
- 预期: HEAD = `REVERT_COMMIT`；`SRC_EQUALS_ANCHOR`。

### ROLLBACK-001-E: 紧急止血（仅当 ib-web 因 DEPLOY-002 无法启动、且 001a 的 push 通道暂不可用时，经用户批准；偏好序最低）
- 类型: 紧急止血，**必须带收尾**
- 命令（只就地恢复"被本次修改过的已跟踪文件"，新增文件不列入——旧版本不存在会报错，且旧代码不引用它们，保留无害）:
```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git cat-file -t "$1")" = commit ]
git diff --name-only --diff-filter=M "$1" "$2" > /tmp/ib_r26_modified.txt
wc -l < /tmp/ib_r26_modified.txt                        # 先核对文件数与清单，再执行
xargs -a /tmp/ib_r26_modified.txt git checkout "$1" --  # 把这些文件还原为锚点版本
git status --porcelain | head -n 50
EOF
```
  随后 `sudo -n systemctl restart ib-web`（及按需 ib-worker）。
- 变量核验: `ANCHOR` 同上；执行后抽查一个文件，`git diff --stat "$ANCHOR" -- <该文件>` 必须为空（防止"回滚静默失效"）。新增的 `src/ib/{builder,confsvc,runtime}/` 等目录留在工作树中无害（旧代码不 import）。
- **收尾（必做）**: 回退提交 push 后（001a）、在目标机 `pull` 之前，先把上述文件恢复到索引版本再 pull——`xargs -a /tmp/ib_r26_modified.txt git checkout HEAD --`，然后执行 001b，最后确认 `git status --porcelain` 无已跟踪修改，目标机回到与远端一致的干净状态。该步只作用于清单中的已跟踪文件，不触碰 env / 数据 / venv / node_modules。

### ROLLBACK-004: 回滚 DEPLOY-004（前端）
- 类型: 正式回滚 = 001b 之后在目标机用回退后的源码重新构建并发布（命令同 DEPLOY-004 的第二条）；紧急止血 = 还原部署前的 web root 副本。
- 正式回滚命令:
```bash
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/'
```
- 紧急止血（不依赖构建）:
```bash
ibssh 'set -e; test -s ~/ib-webroot-pre-r26/index.html; test -d ~/ib-webroot-pre-r26/assets; rm -rf /var/www/intelligentbase/assets; cp -r ~/ib-webroot-pre-r26/assets /var/www/intelligentbase/; cp ~/ib-webroot-pre-r26/index.html /var/www/intelligentbase/; ls -l /var/www/intelligentbase'
```
  收尾: 之后仍应执行正式回滚命令一次，使 web root 与远端 HEAD 的构建结果一致。
- 变量取值与核验: 无本地变量；执行前 `ls ~/ib-webroot-pre-r26` 确认副本存在且含 `index.html` 与 `assets/`（`test -s` / `test -d` 已内置）。
- 预期: 浏览器硬刷新后恢复旧配置页；`ActiveEnterTimestamp` 不变（无重启）。

### ROLLBACK-003: 回滚 DEPLOY-003（ib-worker 运行回退后的代码）
- 类型: 正式回滚（前提：001b 已完成、ROLLBACK-000 已通过）
- 命令: 同 DEPLOY-003 的 `restart ib-worker` 命令块。
- 预期: `active`/`running`/`NRestarts=0`，`errors_in_log=0`，`pgrep -c` 为 1。

### ROLLBACK-002a: 回滚 DEPLOY-002（ib-web 运行回退后的代码）
- 类型: 正式回滚（前提：001b 已完成、ROLLBACK-000 已通过）
- 命令: 同 DEPLOY-002 的 `restart ib-web` 命令块（`runtime_compile_failed` / `config_drift` 关键字在旧代码下不会出现，零命中即可）。
- 预期: `/healthz` 200；`startup succeeded`；无 `ConfigError`（若出现"不支持的 schema_version"类错误，说明 ROLLBACK-000 未真正通过，立即回到 ROLLBACK-000，不要反复重启）。回退后行为：配置回到"重启后生效"的旧语义，画布 / 版本 / Builder 入口消失；008 的新表与新列保留在台账中被旧代码忽略。

### ROLLBACK-002b: 撤销新结构（DROP 表 / 列）——`[MANUAL_ROLLBACK_REQUIRED: 丢失全部配置版本历史、草稿副本与 Builder 评审缓存，以及 config_audit 的 version_before / version_after / object_summary 与 users.config_level 数据（账号档位设置）；不可由代码恢复，只能从 PRE-06 台账备份还原。默认不执行；仅在确需回到 001–007 的纯净 schema（例如下次重新部署前）时，由用户在 ROLLBACK-000/001b/002a/003 之后执行]`
- 前提: ① PRE-06 备份存在且 `integrity=ok`；② PRE-04 输出 `DROP_COLUMN_OK`（SQLite ≥3.35；否则需"重建表"，属更高风险的人工操作，另议）；③ 已回退代码（旧代码运行中不需要这些结构）。
- 命令（用户执行；停服需口令，免密仅覆盖 restart）:
```bash
sudo systemctl stop ib-web ib-worker
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3", isolation_level=None)
c.execute("BEGIN IMMEDIATE")
for s in ("DROP TABLE IF EXISTS builder_eval_cache", "DROP TABLE IF EXISTS config_drafts",
          "DROP TABLE IF EXISTS config_head", "DROP TABLE IF EXISTS config_versions"):
    c.execute(s)                                  # 索引随表一并删除
c.execute("ALTER TABLE users DROP COLUMN config_level")
for col in ("version_before", "version_after", "object_summary"):
    c.execute(f"ALTER TABLE config_audit DROP COLUMN {col}")
c.execute("COMMIT")
PY
sudo -n systemctl restart ib-web && sudo -n systemctl restart ib-worker
```
- 变量取值与核验: 无本地变量；本序列已在开发机 SQLite 3.45.1 上对 `ensure_schema` 建出的库实测可执行（`config_level` 的 CHECK 是列级约束，不阻止 DROP COLUMN）。执行后以 checklists [B29](2) 的只读核对反向确认"4 表、4 列均已不存在"，`integrity_check=ok`，再按 V-01 / V-03 / V-04 验证服务。
- 失败处理: 任一步报错 → 事务内的 DDL 随 `ROLLBACK` 撤销；仍失败则用 PRE-06 备份还原主库（先停服，`sudo cp -a` 到位后 `sudo chmod 0660` 并核对属主 `ib-web:ib`，B22）。

### 回滚失败处理

| 失败位置 | 处置 |
|---|---|
| ROLLBACK-000 路径 A 回滚到基线失败（`version_not_found` / `conflict` / `config_busy` / `apply_failed`） | 不进入 001a；按回执处理（`conflict` 重新载入后重试；`version_not_found` 说明基线被修剪 → 转路径 B）。 |
| ROLLBACK-000 路径 B | `[MANUAL_ROLLBACK_REQUIRED]`：立即暂停，返回 BLOCKED，等待用户决定，代理不自行处理。 |
| ROLLBACK-001a / 001b 失败（push 被拒、pull 非 fast-forward、HEAD 不等于回退提交） | 停止回滚，`ROLLBACK_FAILED`；写清目标机 HEAD、各服务状态；不使用 reset / clean / stash；改走 ROLLBACK-001-E（经用户批准）或人工介入。 |
| 重启回退后的 ib-web 失败（002a） | 先查日志首个错误；若为 schema_version 不支持 → 回 ROLLBACK-000；若为其他 → `ROLLBACK_FAILED`，保留现场（不反复重启），人工介入。ib-web 停止期间前端旧版仍可访问但 API 不可用。 |
| 任何回滚步骤自身失败 | 停止回滚，`ROLLBACK_FAILED`，在 deployment_report 写清各步骤已部署 / 已回滚 / 状态未知，并给出人工干预建议。 |

### 失败处理矩阵（E2 使用）

| 失败位置 | 目标环境是否已变更 | 处置 |
|---|---|---|
| 任一 PRE | 否 | 停止，`DEPLOYMENT_FAILED`，无需回滚 |
| DEPLOY-001（前置核对失败） | 否 | 同上 |
| DEPLOY-001（pull 后 HEAD ≠ 待部署提交 / 工作树不干净） | 是 | ROLLBACK-000 → 001a → 001b |
| DEPLOY-002 | 是（代码已拉；schema 可能已部分应用） | ROLLBACK-000 → 001a → 001b → 002a |
| DEPLOY-003 | 是 | ROLLBACK-000 → 001a → 001b → 003 → 002a |
| DEPLOY-004 | 是（可能已部分替换 web root） | 先 004 紧急止血以恢复可用；再 ROLLBACK-000 → 001a → 001b → 004 → 003 → 002a |
| 部署后验证失败（V-xx，机器可验项） | 是 | `DEPLOYED_WITH_ISSUES`，列出失败项，由 PM 请用户决定是否回滚；**如问题仅在配置内容层面，优先用配置版本回滚而非代码回滚** |
| 回滚步骤自身失败 | — | 停止回滚，`ROLLBACK_FAILED`，写清各步骤已部署 / 已回滚 / 未知，由用户人工介入 |
| 遇到 `[MANUAL_ROLLBACK_REQUIRED]` 分支 | — | 立即暂停，返回 BLOCKED 等待人工决定 |

## 不可逆步骤汇总

| # | 步骤 | 性质 | 数据风险 | 处置 |
|---|---|---|---|---|
| I-1 | ROLLBACK-002b DROP 新表 / 新列 | `[MANUAL_ROLLBACK_REQUIRED]` | 丢失版本历史、草稿、评审缓存、审计新增列与账号档位 | 默认不执行；须备份（PRE-06）、SQLite ≥3.35、用户执行 |
| I-2 | ROLLBACK-000 路径 B：以备份还原 definition.json / prompts | `[MANUAL_ROLLBACK_REQUIRED]` | 上线后的配置改动在文件态丢失（仅版本表 `snapshot_json` 留有副本） | 由用户逐项确认；优先走路径 A |
| I-3 | 验收 B7 / B10 触发的 Builder 生成 / 评审 / 优化：向云端 DeepSeek 外发（含自评的第二次调用，DEF-R26-003 裁决：每次外发 1 条审计） | `[MANUAL_ROLLBACK_REQUIRED: 外发内容无法撤回；载荷为白名单字段，不含资料正文与凭据，已写 config 审计]` | 数据已离开本机，仅可通过审计核对 | 验收用测试项目与无敏感内容的需求描述；用户知情（CL-005 已确认外发） |
| I-4 | 上线时 ib-web / ib-worker 重启 | 不可撤销的副作用 | 内存态聊天会话与"人工确认挂起态"丢失（A06 fail-closed） | 选无人时段，PRE-09 用户确认 |

另（可逆但需知晓，非 MANUAL）：v1 项目首次保存会先存"升级前基线"再存用户版本（A07），之后配置版本回滚可回到基线；`users.config_level` 对存量 ops 账号补为 `manage`（等价于上线前"能写配置"，不回退能力，admin 行忽略该列）；迁移 / 补列无外部系统调用，不发送通知。

## 部署后验证

「真实启动时刻」= DEPLOY-002 / DEPLOY-003 输出的 `RESTART_TS`（远端时区 CST，已由命令在远端实取，不使用估算时间）。执行者 `A` = 代理经 ssh；`U` = 用户；`U*` = **用户人工验收必做项**。

| ID | 检查项 | 执行者 | 命令 / URL | 成功标准 |
|---|---|---|---|---|
| V-01 | 服务存活 | A | `ibssh 'systemctl is-active ib-web ib-worker ib-embed qdrant nginx'` | 5 行 `active` |
| V-02 | ib-web 启动日志无 schema / 装配错误 | A | `ibssh 'journalctl -u ib-web --since "<RESTART_TS>" --no-pager \| grep -E "startup succeeded\|ConfigError\|OperationalError\|Traceback\|runtime_compile_failed\|config_drift"'`；另 `… -p warning` 人工浏览 | 出现 `startup succeeded`；其余关键字零命中；`NRestarts=0`；warning 仅限已知项 |
| V-03 | ib-worker 日志与单实例 | A | `ibssh 'journalctl -u ib-worker --since "<RESTART_TS>" --no-pager \| grep -cE "unable to open database file\|Traceback\|OperationalError"; pgrep -c -f "[i]bweb\.worker"'` | 前者 0；后者 1；`NRestarts=0` |
| V-04 | 健康检查 | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz/deps'` | 均 200 |
| V-05 | 台账文件权限（B22） | U | `sudo ls -la /var/lib/intelligentbase/ledger`（先 `is-active` 再隔几秒查） | 除 `*.pre-*.bak*` 冷备外，凡存在的 `ledger.sqlite3*` 均为 `660 ib-web:ib`；`ib-worker` 非 failed |
| V-06 | **线上代码版本判据**（目标机 HEAD + 源文件 mtime 早于 ActiveEnterTimestamp；**不得用 .pyc**，SKILL.md §7.1） | A | 见下方脚本 | `HEAD_MATCH`、`MTIME_OK`（ib-web 与 ib-worker 均成立） |
| V-07 | **只读结构校验**（checklists [B29](2)，`sudo -u ib-web`，`mode=ro`） | U | 见下方脚本 | 4 张新表存在；`users.config_level` 与 `config_audit` 3 列存在；`users` 总数 = PRE-06 值；存量 ops 账号 `config_level` 全为 `manage`；`pending_version IS NOT NULL` 无结果；`integrity_check=ok`；`documents` 总数 = PRE-06 值 |
| V-08 | **selfcheck 在目标机离线跑**（对应 CI 阶段 7；不连生产服务、不读 env 文件）。在 `git archive` 的**临时干净导出**里跑，不在部署树内跑：selfcheck 配置了 `src/.selfcheck_blobs` 作 blob 根（selfcheck.py:82），避免在 `/opt/intelligentbase` 留下未跟踪文件 | A（无需 sudo） | 见下方 V-08 脚本 | 无新增 FAIL；`config_versions_schema_single_source` 与 `graph_validate_offline` 为 PASS。**已知**：开发机 `core_framework_free` 失败是该 venv 的 `sitecustomize` 所致；目标机若出现须核对原因（记录，非 008 回归即不阻塞）。若目标机 venv 缺 selfcheck 所需依赖则标"未验证"并如实记录，不安装。 |
| V-09 | **热生效 ≤ 5 s + 多次提问版本一致**（TBD-T32；AC-014-01/-04/-017-02） | U* | 见下方"热生效探针" | 保存 / 发布后 5 秒内 `applied_version` 追上 head；探针退出码 0（`apply_state == ok` 且样本所见版本唯一）；响应与页面不出现"重启"字样 |
| V-10 | 未变更组件确实未被触碰 | A | `ibssh 'systemctl show -p ActiveEnterTimestamp ib-embed; ss -lntp \| grep -E ":18080\|:8100\|:6333"'`；`git diff --name-only "$ANCHOR" HEAD -- src/deploy/nginx`（空） | `ib-embed` 的时间戳 = PRE-05 记录值（未重启）；三个端口仍只监听 127.0.0.1；ib-web 的 `ActiveEnterTimestamp` 在 DEPLOY-004 前后不变；nginx 未 reload |
| V-11 | **chat SSE 冒烟**（现有问答链路在新装配 / 新运行时下不退化） | U | 在目标机会话内（令牌用 `read -rs IB_PROBE_TOKEN; export IB_PROBE_TOKEN` 读入，不回显）：`curl -sN --max-time 120 -H "Authorization: Bearer $IB_PROBE_TOKEN" -H "X-IB-Project: <验收项目ID>" "http://127.0.0.1:18080/api/chat/stream?q=%E4%BD%A0%E5%A5%BD&session_id=smoke-$(date +%s)" \| head -c 2000`；并在浏览器经 nginx 对既有业务项目提一个问题 | 回环口立即开始返回 SSE 帧、连接正常结束、无 5xx；浏览器经 nginx 逐步出现回答（非"问了很久才一次性出结果"，SKILL.md §8.7）；问题用 `smoke-<epoch>` 唯一化，不写业务数据 |
| V-12 | **上线后人工浏览器验收（必做）**：`e2e_test_report.md` 文末「上线后人工浏览器验收清单」**A1~A4 与 B1~B10 全部执行**。本计划**不改写**其操作步骤与期望结果，以该文件为准：A1~A4 对应 US-003（图随编辑实时更新，Must）；B1~B10 对应其余未验证项（悬停卡片、手工新建 / 克隆、拖拽连线删除、查看档只读、冲突对话框、XSS 纯文本、Builder 加入画布 / 逐项采纳、10 节点保存、发布后 100 次提问版本一致、真实 Key 的 Builder 与不可达时 60 s 内可读错误） | U* | 浏览器 `https://192.168.31.133/` → 配置页；用 PRE-10 的独立测试项目与管理档测试账号；先 Ctrl+F5 硬刷新 | 验收人逐条填 通过 / 不通过 + 截图（不含凭据）；**全部 14 项通过**才算 critical path 缺口（US-003，23/24）闭合；不通过项按缺陷回流（画像 / 协议 §C）。测完用"回滚"回到验收前版本。 |
| V-13 | **30 节点 / 60 边性能**（AC-022；TBD-T32）与 **Builder 60 s 超时**（AC-030-04；TBD-T36）与**真实 DeepSeek 路径** | U* | 同 V-12 的 B1（30 节点悬停 ≤ 300 ms）、B8（保存校验 ≤ 2 s）、B10（真实 Key 生成；不可达时 60 s 内可读错误）；30 节点图由验收人在测试项目中构造 | 开发者工具计时：悬停 ≤ 300 ms、保存校验 ≤ 2 s；Builder 正常返回草案、不可达时 ≤ 60 s 给出可读错误且手工创建仍可用。阈值为设计占位值，实测值回填 TBD-T32/T36（不以开发机数据代替）。让 DeepSeek"不可达"的方式由用户决定，**不得为此在生产改 `/etc/intelligentbase/*.env` 而不另行授权**。 |
| V-14 | 外部可达性与前端已发布 | A（+开发机 curl） | 目标机：`ibssh 'grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html \| sort -u'`；外部：`curl -sk https://192.168.31.133/ \| grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \| sort -u`；`curl -sS -o /dev/null -w '%{http_code}\n' https://192.168.31.133/healthz` | 两处 hash 一致且等于 DEPLOY-004 输出；`/healthz` 200（本命令不携带凭据，`-k` 仅用于取公开首页） |

**V-06 脚本**（`$1`=`DEPLOY_COMMIT`、`$2`=`ANCHOR`，经位置参数传入）：

```bash
ibssh bash -s -- "$DEPLOY_COMMIT" "$ANCHOR" <<'EOF'
set -u
cd /opt/intelligentbase
echo "HEAD=$(git rev-parse HEAD)"
[ "$(git rev-parse HEAD)" = "$1" ] && echo HEAD_MATCH || echo HEAD_MISMATCH
bad=0
for unit in ib-web ib-worker; do
  ts=$(systemctl show -p ActiveEnterTimestamp --value "$unit")
  ep=$(date -d "$ts" +%s)
  echo "$unit ActiveEnterTimestamp=$ts"
  while read -r f; do
    [ -f "$f" ] || continue
    [ "$(stat -c %Y "$f")" -le "$ep" ] || { echo "NEWER_THAN_START: $unit $f"; bad=1; }
  done < <(git diff --name-only --diff-filter=AM "$2" "$1" -- src/ib src/ibweb)
done
[ "$bad" = 0 ] && echo MTIME_OK
EOF
```

**V-08 脚本**（`$1`=`DEPLOY_COMMIT`；临时目录在远端 `mktemp -d`，用后删除，不触碰 `/opt/intelligentbase` 工作树；普通 ssh 会话不加载 `/etc/intelligentbase/*.env`）：

```bash
ibssh bash -s -- "$DEPLOY_COMMIT" <<'EOF'
set -u
D=$(mktemp -d)
git -C /opt/intelligentbase archive "$1" src | tar -x -C "$D"
cd "$D"
env IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR PYTHONUTF8=1 PYTHONPATH=src /opt/intelligentbase/venv/bin/python src/scripts/selfcheck.py 2>&1 | tail -n 15
rm -rf "$D"
EOF
```

**V-07 脚本**（U；`mode=ro`，只输出名称与计数）：

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
need = {"config_versions", "config_head", "config_drafts", "builder_eval_cache"}
print("missing_tables=", sorted(need - tabs))
ucols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
acols = {r[1] for r in c.execute("PRAGMA table_info(config_audit)")}
print("missing_users_cols=", sorted({"config_level"} - ucols))
print("missing_audit_cols=", sorted({"version_before", "version_after", "object_summary"} - acols))
print("users_by_role_level=", c.execute("SELECT role, config_level, COUNT(*) FROM users GROUP BY role, config_level ORDER BY role").fetchall())
print("ops_not_manage=", c.execute("SELECT COUNT(*) FROM users WHERE role='ops' AND config_level<>'manage'").fetchone()[0], "(验收前应为 0；验收期间若试过其它档位则以实际为准)")
print("pending_versions=", c.execute("SELECT COUNT(*) FROM config_head WHERE pending_version IS NOT NULL").fetchone()[0])
print("integrity=", c.execute("PRAGMA integrity_check").fetchone()[0], "journal_mode=", c.execute("PRAGMA journal_mode").fetchone()[0])
print("users_total=", c.execute("SELECT COUNT(*) FROM users").fetchone()[0], "documents_total=", c.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
PY
```

**热生效探针（V-09，U 在目标机交互式会话中执行；探针只读，不写任何配置）**：

```bash
read -rs IB_PROBE_TOKEN; export IB_PROBE_TOKEN          # 令牌只经环境变量，不回显、不入命令行、不入库
cd /opt/intelligentbase
/opt/intelligentbase/venv/bin/python src/scripts/hot_effect_probe.py --base-url http://127.0.0.1:18080 --project <验收项目ID> --samples 100
echo "exit=$?"
```

- 先在验收项目里完成一次发布（V-12 的 B9 步骤）再立即跑探针；`--samples` 取 100 对应 AC-014-04 的"100 次提问版本一致"。退出码 0 = `apply_state == ok` 且样本所见 `applied_version` 唯一；1 = 状态异常 / 版本不一致 / 样本失败；2 = 参数非法。
- **探针的能力边界（如实）**：它核对"版本一致"与提问耗时分布，**不测量"发布到生效"的 ≤ 5 s 收敛时间**。收敛时间由验收人在 B9 中以"发布后 5 秒内提问即得到新行为"判定，并可用下述补充轮询计时（只读、`[INFERRED]` 字段名取自探针所读的 `/api/config/status`：`version`、`applied_version`）：`t0=$(date +%s.%N); until [ "$(curl -s -H "Authorization: Bearer $IB_PROBE_TOKEN" -H "X-IB-Project: <验收项目ID>" http://127.0.0.1:18080/api/config/status | /opt/intelligentbase/venv/bin/python -c 'import sys,json; d=json.load(sys.stdin); print(int(d.get("applied_version")==d.get("version")))')" = 1 ]; do sleep 0.5; done; echo "converged_s=$(echo "$(date +%s.%N) - $t0" | bc)"`（在点"发布"之后立即启动）。该补充命令尚未在目标机验证，属 `[INFERRED]`，失败时以 B9 的人工判定为准。
- ib-worker 侧的收敛仅由 `IB_CONFIG_HEAD_CHECK_INTERVAL_S` 决定，缺省 1.0 s，本计划不单独测。

回滚后的验证：用 V-01 / V-02 / V-03 / V-04 / V-14 / V-10，并把 V-06 中的 `DEPLOY_COMMIT` 换成 `REVERT_COMMIT`；V-07 改为 ROLLBACK-000 的只读脚本核对；V-12 不再适用。

## 下游产物同步核对（计划修订后 grep / 比对，M-DE-001 / 003 / 004 / 008）

| 产物 | 核对方法与结论 | 处置 |
|---|---|---|
| `.github/workflows/ci.yml` | 008 未被旧 Schema 门覆盖（旧门覆盖 003、007） | **已修改**（PM 要求）：Schema 门追加 008；diff 与本地等价校验见 `cicd_pipeline.md`；待首次 push 后的真实 CI 验证 |
| `src/deploy/checklists.txt` | 已含 [B29]（REV-26）与签署行 `B29` 一行；`B1–B27` 旧签署行保留（`selfcheck.py:3538` 断言 `"B1–B27" in checklists`，P-DE-001） | 本组**未改动**该文件（不在本角色写权限内，且已由 GROUP_C 追加）。V-07 / ROLLBACK-000 / ROLLBACK-002b 与 [B29](1)(2)(3) 逐项对应 |
| `src/deploy/systemd/*.service` | `git status` 无改动；`ib-web` 的 `ExecStartPre=… --ensure-schema`（`ib-web.service:47`）、`TimeoutStopSec=30`；`ib-worker` `After=ib-web.service`、`TimeoutStopSec=300`（`ib-worker.service:54`）已被步骤引用 | 无需修改；PRE-02 机械复核 |
| `src/deploy/env.example` | 新增 4 个**注释掉的**可选键示例（仅键名与缺省说明，无值）：`IB_CONFIG_HEAD_CHECK_INTERVAL_S`、`IB_GRAPH_RUNTIME`、`IB_LLM_CLIENT_CACHE_MAX`、`IB_DOC_SCOPE_MAX_IDS`；与 `env.example` 既有键集未改名 | 无需修改；注意 M-DE-004：这 4 个键对 ib-web 有意义（`IB_CONFIG_HEAD_CHECK_INTERVAL_S` 亦涉及 worker 的感知），写入哪个 env 文件由用户按 SKILL.md §6 决定；`src/deploy/ib-worker.env.example` 存在但本次 `git diff` 未改动它（只改了 `env.example`），该 4 键是否也需在 worker 示例中登记 → **未核对，建议 software-developer / PM 确认**（不影响运行：缺省值即可） |
| `src/deploy/nginx/*` | 无改动；`/api/` 已满足 SSE 与体积（module_design F-14）；SSE 反代三条件、http2 禁用均未触碰 | 无需 `nginx reload` |
| `src/deploy/migrations/008_config_versions.sql` | 与 `config_versions_ddl_script()` 去空白包含（CI 新门 + selfcheck 双重核对）；头注释含回滚说明与 `MANUAL_ROLLBACK_REQUIRED`；无可执行 DROP | 无需修改 |
| `docs/deployment_plan.md`（基线） | 只读 | 未改 |

## `[INFERRED]` 汇总（画像与设计均未给出的取值）

ib-web 不可用 10–30 秒；ib-worker 观察等待 15 秒；ib-web 就绪轮询 30×2 秒、ib-worker 就绪轮询 20×3 秒；ssh 命令超时 ≥360 秒；web root 副本目录名 `~/ib-webroot-pre-r26`；备份目录 `/var/lib/intelligentbase/backup-pre-r26`；台账备份文件名 `ledger.sqlite3.pre-r26.bak`；PRE-03 的磁盘 / 内存余量阈值（2 倍台账 + 2 GiB、2 GiB）；目标机 SQLite ≥3.35 与 `definition.json` / `prompts` 的实际路径与布局；V-08 selfcheck 在目标机 venv 离线可跑的前提（依赖是否齐全）；V-09 收敛计时的字段名与轮询命令；热生效与性能阈值（5 s、300 ms、2 s、60 s）为设计占位值，实测回填 TBD-T32/T36。
`[TOOL_UNREGISTERED]`：`gh`（仅 PRE-00 可选便利，可用网页替代）；`bc`（仅 V-09 补充计时，可手动用秒表替代）。
