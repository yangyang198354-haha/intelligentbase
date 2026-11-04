<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-31T16:10:41+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>implementation_plan.md</file>
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

# 部署计划：REV-27 画布支持删除单个节点（INCREMENTAL，仅计划）

> **本文件不执行任何步骤。** 本组未 ssh、未部署、未 commit / push；GROUP_E2 未授权。下列命令是将来 E2 获得 `PRODUCTION_DEPLOY_CONFIRM=true`（环境名 `production`）后才可执行的**计划内容**。
> REV-26 版本归档于 `archive/rev26/deployment_plan.md`（只读）；本文按 REV-27 整体重写，沿用其执行约定（引号规则 Q1~Q6）、回滚结构与验证脚本风格。`docs/deployment_plan.md`（REV-21 基线）与 `deployment_report.md` 不改。
> 依据：画像 P7/P8/P9、`.claude/skills/ib-prod-deploy/SKILL.md`（§1–§9）、`module_design.md`「数据迁移」「受影响的运行单元 / 构建」、`e2e_test_report.md`「人工验证清单」M-01~M-08。
> 测试门控：invocation 载明 GROUP_D 已通过（PM 2026-10-31 核实：前端 `npm test` 129/129/0，后端 `pytest tests` 910 passed）；三份测试报告均 APPROVED。

## 给 PM 的部署计划摘要（供将来向用户请求 E2 授权）

| 项 | 内容 |
|---|---|
| 目标环境 | `production`（单台物理机 192.168.31.133，SSH 密钥；画像 P7"部署需用户确认=是"）。无 staging。**当前未授权。** |
| 待部署提交 | `DEPLOY_COMMIT` = `1dde3d45e6e58df2c410593a9ba1d8d3d5e7ed6d`（= `origin/main`，已 push；E2 授权时由 PM 写入并与此核对） |
| 策略 | **recreate**（画像唯一允许）。REV-27 为纯前端静态发布：**不重启任何 systemd 服务**（SKILL.md §6 "前端不重启"），ib-web / ib-worker / ib-embed / qdrant / nginx 无停机；已打开旧页面的浏览器需硬刷新 |
| 步骤数 | 预检 7（PRE-00~06；PRE-00 为主会话，PRE-06 为用户）；**部署 2**（DEPLOY-001 git pull → DEPLOY-002 前端构建并发布）+ **条件步骤 2**（DEPLOY-003/004 重启 ib-web / ib-worker，仅 PRE-02 判为 CLASS-B 且 PM 另行授权时才执行，默认不执行）；部署后验证 9（V-01~09，其中 V-06 含用户执行的 M-01~M-08，critical path 5 条必做）；回滚 ROLLBACK-001a/001b/002/003/004（正式 4 + 紧急止血 1） |
| **重要发现（须 PM / 用户知悉）** | 自 REV-26 提交 `bb3ac4b` 至 `1dde3d4` 之间，除 REV-27 外还有提交 `6bfdef4`（"热生效版本快照"）改了**后端运行时文件 `src/ib/runtime/cache.py`**（`git diff bb3ac4b 1dde3d4 -- src` 实测：除前端外仅此一个 src 后端文件；另有 `ci.yml`、`tests/conftest.py`、`frontend.smoke.test.js` 的非运行时改动）。REV-27 自己的提交确为零后端改动，但**若目标机当前 HEAD 早于 `6bfdef4`**，`git pull` 到 `1dde3d4` 会把该后端文件一并落盘，而本次计划按 module_design **不重启**——磁盘代码将领先于运行中的进程，且 V-06 式 mtime 判据不再成立。若目标机 HEAD 早于 `bb3ac4b`（即 REV-26 实际并未按 1dde3d4 之前的版本部署），差异将包含迁移 008 与大量后端文件，**本计划不适用**。这两种情形由 PRE-02 的 CLASS 门机械判定（见下），不靠假定 |
| 生产当前版本 | **未知，不得假定。** 用户口头确认 REV-26 已部署（phase_status CL-001，无时间 / 版本细节，PM 未核验）；而 `deployment_report.md`（REV-26）记录的是"未执行，阻塞于连通性"。因此 PRE-01 必须在目标机实测 `git rev-parse HEAD` 作为**回滚锚点 `ANCHOR`**，PRE-02 据此分类 |
| 不变面 | 台账与全部状态目录（无迁移）、`/etc/intelligentbase/*.env`、systemd unit（无 `daemon-reload`）、nginx（不 reload）、`src/requirements*.txt`、`package.json` / `package-lock.json`（故不执行 `npm ci`）、ib-embed、qdrant |
| 不可逆 / 需人工 | 部署本身无不可逆步骤；验收 M-08 在**测试项目**写入配置版本 / 审计（只增不删），见「不可逆步骤汇总」。CLASS-B 条件分支的重启会丢内存态会话 |
| 回滚方式 | 源头 revert（仅还原 REV-27 的前端与测试改动，保留文档与 agent 记忆）→ 用户确认后 push（主会话）→ 目标机 `git pull --ff-only` → 目标机重建前端并发布；紧急止血 = 还原部署前 web root 副本。不使用 `reset --hard` / `clean` / `stash` / 覆盖式同步 |
| 需要用户（非代理）执行 | 待部署提交已 push（已满足，PRE-00 复核）；PRE-06 验收前置；**V-06 上线后人工浏览器验收（M-01、M-03、M-06、M-07、M-08 必做）**；M-08 中检查服务器提示词目录文件需 sudo。`daemon-reload` / unit 安装 / env 修改 / `nginx reload`：本次均不需要 |
| 前提（E2 授权时由 PM 填入 `special_instructions`） | `PRODUCTION_DEPLOY_CONFIRM=true`；环境名 `production`；`DEPLOY_COMMIT=1dde3d45e6e58df2c410593a9ba1d8d3d5e7ed6d`；计划版本 = phase_status 登记的 APPROVED 版本；如 PRE-02 判为 CLASS-B 且用户同意连带重启：另加 `INCLUDE_BACKEND_RESTART=true`（否则停止，见 PRE-02） |

## 变更摘要

| 组件 | 文件（`1dde3d4` 在 `src tests` 下共 9 个） | 迁移 | 构建 | 需重启 / 发布的运行单元 |
|---|---|---|---|---|
| 前端（Config Studio 画布删除节点） | `src/frontend/src/components/config/{AgentDetailPanel.vue,FlowCanvas.vue,PublishDialog.vue,publishDiff.ts,nodeRemoval.ts〔新〕}`、`src/frontend/src/stores/configDraft.ts`、`src/frontend/src/views/ConfigStudio.vue` | 无 | 目标机 `npm run build`（`vue-tsc --noEmit && vite build`）；`package-lock.json` 未变，不 `npm ci` | **不重启**；拷贝到 web root `/var/www/intelligentbase/` |
| 测试 | `src/frontend/tests/config_studio_r27.test.js〔新〕`、`tests/unit/test_diff_node_removal_r27.py〔新〕` | 无 | — | 非运行时交付物，部署无动作 |
| 后端 / 迁移 / 依赖 / systemd / nginx / env | **REV-27 无改动**（module_design「数据迁移」「受影响的运行单元」） | 无 | — | 无。**例外见"重要发现"：区间内可能带入 `src/ib/runtime/cache.py`（`6bfdef4`）**，由 PRE-02 判定 |

**"改什么重启什么"核对（SKILL.md §6）**：前端 `src/frontend/**` → 不重启、重新 build + 拷 web root ✓（DEPLOY-002）；`ibweb/**`、`ib_embed`、`src/deploy/**`、`/etc/intelligentbase/*.env` 均无 REV-27 改动 ✓；共享运行时 `src/ib/runtime/cache.py` 仅在 CLASS-B 出现，默认停止询问而不是静默重启。

## 目标环境与策略

- **环境**：`production`（画像 P7）；SSH 密钥 `~/.ssh/ib_prod_ed25519`，主机 / 用户见 SKILL.md §1–§2。不设计 staging。
- **策略：recreate**。理由：单机、单实例，无负载均衡与第二套环境（画像 P7 唯一允许）。REV-27 实质是静态资源原地替换：先备份旧 web root，构建成功才替换，无服务停机；`index.html` 为 `no-store`，`assets/*` 带新 hash（SKILL.md §5.2）。
- **替换窗口风险**：`rm -rf assets` 与 `cp -r dist/assets` 之间（秒级）以及此后，已加载旧 `index.html` 的浏览器标签页若再懒加载旧 hash 的分包会 404；正在编辑画布且有**未保存草稿**的用户须先保存或放弃再硬刷新 `[INFERRED]`（PRE-06 要求用户确认无人正在编辑）。
- **预计停机**：后端 0；前端无停机，切换窗口 ≤ 数秒 `[INFERRED]`。
- **兼容性**：REV-27 不改接口与载荷格式，仅前端本地删除逻辑；新前端调用的仍是既有保存 / 发布接口（module_design），后端无需配合。

## 执行约定（引号与变量）

执行端为 bash（Git Bash / Linux），**不要**把复杂命令作为参数从 PowerShell 传入（SKILL.md §4.2）。

```bash
# 连接函数（密钥 / 主机 / 用户见 SKILL.md §1-2；BatchMode 保证绝不回落到口令交互）
ibssh() { ssh -i ~/.ssh/ib_prod_ed25519 -o UserKnownHostsFile=/tmp/ib_kh -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@192.168.31.133 "$@"; }
```

| 规则 | 说明 |
|---|---|
| Q1 | 不含本地值的远端命令：整条放进**单引号**，`$VAR` 在**远端**展开。 |
| Q2 | 需要本地值（`ANCHOR`、`DEPLOY_COMMIT`、`REVERT_COMMIT`）：一律 `ibssh bash -s -- "$A" "$B" <<'EOF' … $1 $2 … EOF`——本地双引号只把值作为**位置参数**传过去，heredoc 用单引号定界使本地不展开，远端用 `$1 $2`。**禁止** `ibssh 'git checkout $ANCHOR -- …'`（远端为空）。markdown 里 heredoc 代码块须顶格粘贴。 |
| Q3 | 单引号内有意在远端定义并使用的变量（如 `TS=$(date …)`）是远端变量，属预期。 |
| Q4 | 变量取值与核验：`ANCHOR` = PRE-01 输出的 40 位 `git rev-parse HEAD`；`DEPLOY_COMMIT` = PM 在 `special_instructions` 下发；`REVERT_COMMIT` = ROLLBACK-001a 产生。使用前本地核验 `[[ "$X" =~ ^[0-9a-f]{40}$ ]]`，远端 `git cat-file -t "$X"` 必须输出 `commit`（PRE-02 / ROLLBACK-001b 内置）。 |
| Q5 | 凡需 sudo 口令的动作（M-08 检查提示词目录等）由用户在交互式会话中执行；**禁止** `printf '<口令>' \| sudo -S`；不读取、不回显 `/etc/intelligentbase/*.env` 的值；**禁止** scp / pscp / rsync 向生产传代码。 |
| Q6 | 凭据、令牌只写存放位置，不写值；本仓库 PUBLIC，本文不含任何凭据。 |

## 预检清单

执行者：`A` = devops 代理经 ssh（E2 授权后）；`U` = 用户；`M` = 主会话。任一项不通过：**停止，不进入 DEPLOY-001**（目标环境尚无变更，报告 `DEPLOYMENT_FAILED`，无需回滚）。

| ID | 检查项 | 执行者 | 通过标准 |
|---|---|---|---|
| PRE-00 | 待部署提交已在远端；无遗漏的未跟踪文件；该提交 CI 全绿 | M（CI 查询亦可由 A 在开发机执行 `gh`） | 见下 |
| PRE-01 | 目标机 HEAD 记录为**回滚锚点**；已跟踪文件无本地修改 | A | HEAD 为 40 位哈希且记入报告；无 ` M` 的已跟踪文件 |
| PRE-02 | **变更集分类门（CLASS）**：区间 `ANCHOR..DEPLOY_COMMIT` 只含前端 / 测试 / 文档类文件；与目标机本地修改无交集 | A | `CLASS=A` 方可继续；`CLASS=B` / `C` 见下 |
| PRE-03 | 磁盘 / 内存 / 工具链余量 | A | web root 与家目录所在盘可用 ≥ 1 GiB `[INFERRED]`；内存可用 ≥ 1 GiB `[INFERRED]`；node / npm 可用且 node 主版本 22 |
| PRE-04 | 服务基线（证明本次未重启任何服务的对照） | A | 5 个单元 active；记录 ib-web / ib-worker / ib-embed 的 `ActiveEnterTimestamp` 与 `NRestarts` |
| PRE-05 | web root 基线与副本路径可用 | A | 记录 `index.html` 的 sha256 与引用的 `assets/index-*.js` 文件名；`~/ib-webroot-pre-r27` 不存在 |
| PRE-06 | 验收前置（见下） | U | 用户书面确认 |

### PRE-00（开发机）

```bash
git status -sb | head -n 3                                           # 期望 main...origin/main，无领先落后
git ls-remote origin refs/heads/main                                  # 首列必须 == DEPLOY_COMMIT
git ls-files --others --exclude-standard src tests | wc -l            # 期望 0
git ls-tree -r --name-only "$DEPLOY_COMMIT" | grep -cE '^(src/frontend/src/components/config/nodeRemoval\.ts|src/frontend/tests/config_studio_r27\.test\.js|tests/unit/test_diff_node_removal_r27\.py)$'   # 期望 3
gh run list --commit "$DEPLOY_COMMIT" --workflow CI --json databaseId,status,conclusion --limit 5   # 须有 status=completed 且 conclusion=success
```

- **CI 门**：本组 E1 取证时（2026-10-31T16:09+08:00）该提交的 CI run `41183387985` 仍 **in_progress**，**不得视为绿**。E2 时必须为 `completed / success`；红灯或仍在运行不得部署。`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`，无 `gh` 时在 GitHub Actions 网页核对，等价。
- 本机 `gh` 不可用或未登录 → 该项标"未验证"并请用户确认，不得默认通过。

### PRE-01（A）

```bash
ibssh 'cd /opt/intelligentbase && git rev-parse HEAD && git log --oneline -1 && git status --porcelain'
```

输出的 40 位哈希即 `ANCHOR`，写入 deployment_report 首节。已跟踪文件修改（` M`）必须为空；`??` / 被忽略项（venv、node_modules 等）是本地状态，只记录、不触碰。**不得假定 HEAD 等于 REV-26 的任何提交**（CL-001）。

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
[ "$1" != "$2" ] || { echo "ANCHOR==DEPLOY_COMMIT: 无代码变化，停止并核对 web root 是否已是新构建"; exit 3; }
CH=$(git diff --name-only "$1" "$2")
echo "changed_files=$(printf '%s\n' "$CH" | grep -c .)"
REST=$(printf '%s\n' "$CH" | grep -vE '^(src/frontend/src/|src/frontend/tests/|tests/|docs/|\.claude/|\.github/)' | grep -v '^$' || true)
BONLY=$(printf '%s\n' "$REST" | grep -E '^src/ib/runtime/cache\.py$' || true)
C=$(printf '%s\n' "$REST" | grep -vE '^src/ib/runtime/cache\.py$' | grep -v '^$' || true)
echo "--- 非前端/测试/文档类文件(CLASS-C 依据):"; printf '%s\n' "$C"
echo "--- 后端运行时文件(CLASS-B 依据):"; printf '%s\n' "$BONLY"
echo "--- 与目标机本地修改的交集(期望为空):"
comm -12 <(printf '%s\n' "$CH" | sort) <(git status --porcelain | awk '{print $2}' | sort)
echo "--- 依赖/锁文件(期望为空):"
git diff --name-only "$1" "$2" -- src/frontend/package.json src/frontend/package-lock.json src/requirements.txt src/requirements-embed.txt src/requirements-offline.txt
if [ -n "$C" ]; then echo CLASS=C; elif [ -n "$BONLY" ]; then echo CLASS=B; else echo CLASS=A; fi
EOF
```

| CLASS | 含义 | 处置 |
|---|---|---|
| **A** | 区间只含 `src/frontend/{src,tests}`、`tests/`、`docs/`、`.claude/`、`.github/`（无后端运行时文件） | 继续 DEPLOY-001 / 002 |
| **B** | 在 A 之外仅多 `src/ib/runtime/cache.py`（`6bfdef4` 的热生效版本快照修复，ib-web 与 ib-worker 均加载 `ib.runtime`） | **默认停止，不进入 DEPLOY-001**，报告 PM / 用户择一：① 先单独完成其所属后端发布（连带重启）；② 授权 `INCLUDE_BACKEND_RESTART=true`，执行条件步骤 DEPLOY-003 / 004（会丢内存态聊天会话，选无人时段）；③ 用户明确接受"磁盘领先于进程"（下次重启才生效）——此时 V-06 的 mtime 判据对该文件豁免并在报告中如实记录。**代理不得自行选择** |
| **C** | 出现迁移、`src/deploy/**`、依赖、`src/ib_embed`、`src/scripts` 或其他后端文件（说明目标机落后 REV-26 一个或多个发布） | **停止**，`DEPLOYMENT_FAILED`（无变更）；本计划不适用，须先按 `archive/rev26/deployment_plan.md` 的流程（含迁移 008 备份与重启）补齐，由 PM 重新规划 |

- "依赖 / 锁文件"一行非空同样按 CLASS-C 停止（`package-lock.json` 变化意味着需 `npm ci`，超出本计划）。
- 交集非空（目标机对要覆盖的文件有本地修改）→ 停止上报，不 pull。
- `git fetch` 只更新远端跟踪引用，不改工作树。

### PRE-03 / PRE-04 / PRE-05（A）

```bash
ibssh 'df -B1 --output=target,size,used,avail,pcent /var/www/intelligentbase /opt/intelligentbase "$HOME"; free -m | sed -n 1,2p; node -v; npm -v'
ibssh 'date "+%F %T %Z"; systemctl is-active ib-web ib-worker ib-embed qdrant nginx; systemctl show -p ActiveEnterTimestamp,NRestarts ib-web; systemctl show -p ActiveEnterTimestamp,NRestarts ib-worker; systemctl show -p ActiveEnterTimestamp,NRestarts ib-embed'
ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u; ls ~/ib-webroot-pre-r27 2>&1 | head -n 1'
```

PRE-03 中 `"$HOME"` 位于单引号内，属远端展开（Q1，预期）。PRE-04 的时间戳是 V-01 "未被重启"的对照；PRE-05 末行应输出 `No such file or directory`（副本目录尚不存在）。

### PRE-06 验收前置（U）

用户书面确认：
1. 已有**独立测试项目**，含 ≥ 3 个 agent（含 `billing-agent` 或等价、可含主提示词草稿的 agent）；**验收不动生产业务配置**（M-07、M-08 的保存只发生在该项目；M-03 的 30 节点图亦在该项目构造）。
2. 编辑档账号、查看档账号各 1 个；M-07 所需的**终端用户**账号 1 个（可无痕窗口登录）。
3. M-08 需检查"项目提示词目录"的文件存在性：用户有 sudo 权限，并知道该目录实际路径（画像未登记；SKILL.md §7.4 为 `/var/lib/intelligentbase/prompts` 下，具体项目子路径以目标机为准 `[INFERRED]`）。
4. 无人正在编辑画布且持有未保存草稿；已知旧页面需硬刷新（Ctrl+F5）。
5. 约定时段（前端发布无停机，但验收需用户在场）。

**无需备份台账 / 状态目录**：REV-27 无迁移、不触碰 `/var/lib/intelligentbase`、不写 env；删除只改浏览器内存草稿，保存沿用既有发布路径（module_design）。

## 部署步骤

所有 DEPLOY 位置均为**目标机**（经 ssh）。预检全部通过（CLASS=A，或 CLASS=B 且已获 PM 对应授权）后按序执行；任一步失败按「失败处理矩阵」处置。

### DEPLOY-001: 目标机拉取代码（`git pull`，禁 scp / pscp / rsync）
- 组件: 前端源码与测试文件（架构部署视图：基础设施无变更 → 数据层无变更 → 服务层无变更 → 前端）
- 位置: 目标机 `/opt/intelligentbase`（属主 `yangyang198354`，免 sudo）
- 命令:
```bash
ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'
set -euo pipefail
cd /opt/intelligentbase
[ "$(git rev-parse HEAD)" = "$1" ]                      # 前置：仍在锚点
git fetch origin main
[ "$(git rev-parse origin/main)" = "$2" ]               # 前置：远端恰为待部署提交；否则中止（尚无变更）
date "+PULL_TS=%F %T"                                    # 记入报告，供 V-04 日志 --since
git pull --ff-only origin main                          # 等价画像 P7 的 git pull origin main，加 --ff-only 禁止合并提交
[ "$(git rev-parse HEAD)" = "$2" ]                      # 后置：精确等于待部署提交
git log --oneline -1
git status --porcelain
EOF
```
- 预期: fast-forward 到 `DEPLOY_COMMIT`；已跟踪文件无修改；退出码 0。
- 回滚: ROLLBACK-001（001a + 001b）

### DEPLOY-002: 前端构建并发布到 web root（不重启任何服务）
- 组件: 前端静态产物（nginx 直读 `/var/www/intelligentbase/`，属主 `yangyang198354`，无需 sudo；nginx 不改、不 reload）
- 位置: 目标机 `/opt/intelligentbase/src/frontend`（`node_modules` 已就位；`package-lock.json` 未变，不执行 `npm ci`）
- 命令（先留旧产物副本，再构建，构建成功才替换；构建命令超时需 ≥ 300 秒 `[INFERRED]`，本机构建约 27 秒）:
```bash
ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r27 ]; mkdir ~/ib-webroot-pre-r27; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r27/; test -s ~/ib-webroot-pre-r27/index.html; test -d ~/ib-webroot-pre-r27/assets; ls ~/ib-webroot-pre-r27'
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html && grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u'
```
- 预期: `vue-tsc --noEmit && vite build` 退出码 0；打印新的 `assets/index-<hash>.js`，其 hash **不同于** PRE-05 记录的旧 hash；`ib-web` / `ib-worker` 的 `ActiveEnterTimestamp` 仍等于 PRE-04 值（发布未触发重启）。构建失败时 `&&` 链在 `rm` 之前中断，web root 仍是旧产物。
- 说明: 旧副本放在部署用户家目录（仓库外、不入 git），验收通过后由用户决定删除；不使用 `rsync` / `scp`。
- 回滚: ROLLBACK-002

### DEPLOY-003: （条件）重启 ib-web —— 仅 CLASS-B 且 `INCLUDE_BACKEND_RESTART=true`
- 组件: ib-web（Waitress，127.0.0.1:18080），加载 `src/ib/runtime/cache.py`
- 位置: 目标机；`sudo -n systemctl restart ib-web`（三条免密 restart 之一，SKILL.md §4）
- 命令:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-web; for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/healthz)" = 200 ] && break; sleep 2; done; systemctl is-active ib-web; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-web; journalctl -u ib-web --since "$TS" --no-pager | grep -E "startup succeeded|ConfigError|OperationalError|Traceback|runtime_compile_failed|config_drift" | tail -n 20'
```
- 预期: `/healthz` 200；`active` / `running` / `NRestarts=0`；出现 `startup succeeded`，错误关键字零命中（`daemon-reload` pending 警告是长期存在的，SKILL.md §7.2，不处理）。ib-web 不可用约 10–30 秒 `[INFERRED]`；内存态聊天会话丢失。
- 回滚: ROLLBACK-003
- **默认（CLASS-A）不执行本步骤。**

### DEPLOY-004: （条件）重启 ib-worker（单实例）—— 仅 CLASS-B 且 `INCLUDE_BACKEND_RESTART=true`
- 组件: ib-worker（`TimeoutStopSec=300`，执行端命令超时需 ≥ 360 秒 `[INFERRED]`）
- 命令:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-worker; for i in $(seq 1 20); do [ "$(systemctl is-active ib-worker)" = active ] && break; sleep 3; done; sleep 15; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-worker; echo "errors_in_log=$(journalctl -u ib-worker --since "$TS" --no-pager | grep -cE "unable to open database file|Traceback|OperationalError")"; pgrep -c -f "[i]bweb\.worker"'
```
- 预期: `active` / `running` / `NRestarts=0`；`errors_in_log=0`；`pgrep -c` 为 **1**（`[i]` 写法避免匹配命令自身；单实例，画像 P8）。
- 回滚: ROLLBACK-004
- **默认（CLASS-A）不执行本步骤。**

## 回滚步骤（逆序）

执行总序：**ROLLBACK-001a（源头 revert + push）→ 001b（目标机 pull）→ 002（前端重建发布）→（仅条件步骤已执行时）003 → 004**。ROLLBACK-001 是把"目标机代码状态"还原的载体，必须先于各单元动作落地；其余按 DEPLOY 的逆序。因 DEPLOY-003/004 默认不存在，通常只有 001 与 002。

**不得破坏的本地状态**（全部回滚路径均不触碰）：`/etc/intelligentbase/*.env`、`/var/lib/intelligentbase/`（台账、blob、definition.json、prompts）、bge-m3 权重、Qdrant 数据、`/opt/intelligentbase/venv`、前端 `node_modules`。**所有回滚均不使用** `git reset --hard`、`git clean`、`git stash`、覆盖式同步。

**配置版本回滚（产品功能）≠ 代码回滚**：若问题只出在验收期间在测试项目中产生的配置内容，用配置页"版本 → 回滚"（热生效、无需代码回滚）；本节 ROLLBACK 仅用于前端代码本身有缺陷时。

### ROLLBACK-001a: 源头 revert 并 push（主会话，用户确认；回滚 DEPLOY-001 的源头部分）
- 类型: 正式回滚
- 命令（开发机；要求工作树对 `src tests` 干净，其他未提交改动需先由主会话处理）:
```bash
R27=1dde3d45e6e58df2c410593a9ba1d8d3d5e7ed6d               # REV-27 提交（本地常量，不含凭据）
git fetch origin main && git switch main && git pull --ff-only origin main
[ "$(git cat-file -t "$R27")" = commit ] && git merge-base --is-ancestor "$R27" HEAD
[ -z "$(git rev-list --merges -n 1 "$R27^..$R27")" ]        # 该提交不是合并提交，否则 revert 需 -m 1，先上报
git revert --no-commit "$R27"                                # 反向还原整个 REV-27 提交
git restore --source=HEAD --staged --worktree -- docs .claude   # 保留文档与 agent 记忆，只还原前端与测试改动
git diff --cached --name-only | grep -vE '^(src/frontend/|tests/)' && echo "UNEXPECTED_PATHS" || echo ONLY_FRONTEND_AND_TESTS
git diff --quiet "$ANCHOR" -- src/frontend/src && echo FRONTEND_SRC_EQUALS_ANCHOR || echo FRONTEND_SRC_DIFFERS_FROM_ANCHOR
```
  核验两行输出：必须是 `ONLY_FRONTEND_AND_TESTS` 与 `FRONTEND_SRC_EQUALS_ANCHOR`；否则先向用户上报，不 commit；若需放弃本次 revert 用 `git revert --abort`（该命令只撤销本次 revert 的暂存，不影响其他改动；若 revert 已完成暂存而非冲突态，则 `git restore --staged --worktree -- src/frontend tests` 且须先经用户确认）并停止。`FRONTEND_SRC_DIFFERS_FROM_ANCHOR` 说明锚点的前端不等于 `1dde3d4~1`，需人工判断。通过后:
```bash
git commit -m "revert(r27): roll back canvas node-removal frontend to pre-REV-27"
git push origin main
git rev-parse HEAD                                           # = REVERT_COMMIT，记入报告
```
- 变量取值与核验: `ANCHOR` 取 PRE-01 输出（deployment_report 首节），执行前 `git cat-file -t "$ANCHOR"` 必须输出 `commit`。回滚用的是**新提交 + 普通 push**，不 force-push、不 reset。`R27` 固定为 REV-27 提交哈希（与 `DEPLOY_COMMIT` 相同时二者一致；`DEPLOY_COMMIT` 更晚时仍只回退 REV-27 本身）。
- **CLASS-B 且已执行 DEPLOY-003/004 时追加**（同一回退提交内，commit 前执行）: `git checkout "$ANCHOR" -- src/ib/runtime/cache.py`，并核对 `git diff --cached --quiet "$ANCHOR" -- src/ib/runtime/cache.py && echo CACHE_EQUALS_ANCHOR`。
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
git diff --quiet "$1" HEAD -- src/frontend/src && echo FRONTEND_SRC_EQUALS_ANCHOR   # 目标机前端源码与部署前逐字一致
git status --porcelain
EOF
```
- 变量取值与核验: `$1`=`ANCHOR`、`$2`=`REVERT_COMMIT` 均作为位置参数传入（Q2），不在单引号里直接写 `$ANCHOR`。
- 预期: HEAD = `REVERT_COMMIT`；打印 `FRONTEND_SRC_EQUALS_ANCHOR`；无已跟踪文件修改。

### ROLLBACK-002: 回滚 DEPLOY-002（前端）
- 类型: 正式回滚 = 001b 之后在目标机用回退后的源码重新构建并发布（命令同 DEPLOY-002 的第二条）；紧急止血 = 还原部署前 web root 副本。
- 正式回滚命令:
```bash
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && sha256sum /var/www/intelligentbase/index.html'
```
- 紧急止血（不依赖构建；前端新版有严重缺陷且 push / pull 通道暂不可用时）:
```bash
ibssh 'set -e; test -s ~/ib-webroot-pre-r27/index.html; test -d ~/ib-webroot-pre-r27/assets; rm -rf /var/www/intelligentbase/assets; cp -r ~/ib-webroot-pre-r27/assets /var/www/intelligentbase/; cp ~/ib-webroot-pre-r27/index.html /var/www/intelligentbase/; sha256sum /var/www/intelligentbase/index.html; ls -l /var/www/intelligentbase'
```
  **收尾（必做）**: 止血后仍须走 001a → 001b 并执行一次正式回滚命令，使 web root 与远端 HEAD 的构建结果一致，目标机仓库回到与远端一致的干净状态（止血本身不改仓库，故无需 git 清理）。
- 变量取值与核验: 无本地变量；`test -s` / `test -d` 已内置。止血后 `sha256sum` 必须等于 PRE-05 记录值（证明还原为部署前内容）；正式回滚后须不同于 DEPLOY-002 的新 hash。
- 预期: 浏览器硬刷新后恢复旧画布（无"删除节点"入口）；`ActiveEnterTimestamp` 不变（无重启）。

### ROLLBACK-004 / ROLLBACK-003: （条件）回滚 DEPLOY-004 / DEPLOY-003
- 类型: 正式回滚（前提：001a 已含 `cache.py` 还原、001b 已完成）；仅在条件步骤执行过时适用。先 004 后 003（逆序）。
- 命令: 同 DEPLOY-004、DEPLOY-003 的重启命令块（此时磁盘代码为锚点版本）；验证标准同其「预期」。
- 失败处理: 重启失败 → 先查日志首个错误，不反复重启；`ROLLBACK_FAILED`，保留现场，人工介入。

### 失败处理矩阵（E2 使用）

| 失败位置 | 目标环境是否已变更 | 处置 |
|---|---|---|
| 任一 PRE（含 CLASS=B 未获授权、CLASS=C） | 否 | 停止，`DEPLOYMENT_FAILED`，无需回滚 |
| DEPLOY-001（前置核对失败） | 否 | 同上 |
| DEPLOY-001（pull 后 HEAD ≠ 待部署提交 / 工作树不干净） | 是 | ROLLBACK-001a → 001b |
| DEPLOY-002（构建失败，web root 未替换） | 否（仅代码已拉取） | 视为已变更：ROLLBACK-001a → 001b；web root 无需动作 |
| DEPLOY-002（替换中途失败，web root 可能不完整） | 是 | 先 ROLLBACK-002 紧急止血恢复可用，再 001a → 001b → 002 正式回滚 |
| DEPLOY-003 / 004（条件步骤失败） | 是 | 停止后续；按 ROLLBACK-001a（含 cache.py）→ 001b → 002 → 004 → 003 |
| 部署后验证机器可验项失败（V-01~V-05） | 是 | `DEPLOYED_WITH_ISSUES`，列出失败项，由 PM 请用户决定是否回滚 |
| 人工验收（V-06）critical path 项不通过 | 是 | `DEPLOYED_WITH_ISSUES`；按缺陷回流（协议 §C）或由用户决定回滚；仅测试项目内容问题优先用配置版本回滚 |
| 回滚步骤自身失败 | — | 停止回滚，`ROLLBACK_FAILED`，写清各步骤已部署 / 已回滚 / 状态未知，由用户人工介入 |
| 遇到 `[MANUAL_ROLLBACK_REQUIRED]` 步骤失败 | — | 立即暂停，返回 BLOCKED 等待人工决定 |

## 不可逆步骤汇总

| # | 步骤 | 性质 | 数据风险 | 处置 |
|---|---|---|---|---|
| I-1 | V-06 / M-08 在测试项目中"保存并生效"（先删节点再"删除 agent"） | `[MANUAL_ROLLBACK_REQUIRED: 配置版本与审计记录只增不删，代码回滚不会清除；"删除 agent"保存后其主提示词文件被移除，只能经配置页"版本 → 回滚"找回]` | 仅限 PRE-06 指定的独立测试项目；不影响生产业务配置 | 验收后用"版本 → 回滚"回到验收前版本（产生新版本而非删除历史）；由用户确认测试项目可保留或另行处置 |
| I-2 | （仅 CLASS-B 条件分支）DEPLOY-003/004 重启 | 不可撤销的副作用 | 内存态聊天会话与"人工确认挂起态"丢失（fail-closed） | 默认不执行；需 `INCLUDE_BACKEND_RESTART=true`；选无人时段 |

REV-27 本身无迁移、无外部系统调用、无通知发送；web root 替换可通过备份副本还原（ROLLBACK-002 止血），不属不可逆。

## 部署后验证

「真实启动时刻」仅在条件步骤执行时存在；CLASS-A 下**无重启**，对照基线为 PRE-04。执行者 `A` = 代理经 ssh；`U` = 用户；`U*` = **用户人工验收必做项**。

| ID | 检查项 | 执行者 | 命令 / URL | 成功标准 |
|---|---|---|---|---|
| V-01 | 服务存活且**未被重启**（CLASS-A） | A | `ibssh 'systemctl is-active ib-web ib-worker ib-embed qdrant nginx; systemctl show -p ActiveEnterTimestamp,NRestarts ib-web; systemctl show -p ActiveEnterTimestamp,NRestarts ib-worker; systemctl show -p ActiveEnterTimestamp ib-embed'` | 5 行 `active`；三个 `ActiveEnterTimestamp` 与 PRE-04 完全相同、`NRestarts` 未增（条件步骤已执行时 ib-web / ib-worker 的时间戳应晚于 `RESTART_TS` 且 `NRestarts=0`） |
| V-02 | 线上代码版本（仓库侧） | A | `ibssh 'cd /opt/intelligentbase && git rev-parse HEAD && git status --porcelain'` | HEAD = `DEPLOY_COMMIT`；已跟踪文件无修改。**前端是静态产物，不适用 `.pyc` / ActiveEnterTimestamp 判据**；web root 与源码一致性由 V-03 证明 |
| V-03 | 前端已发布为新构建 | A + 开发机 curl | 目标机：`ibssh 'sha256sum /var/www/intelligentbase/index.html; grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html \| sort -u'`；外部：`curl -sk https://192.168.31.133/ \| grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \| sort -u` | 两处 hash 一致，等于 DEPLOY-002 输出，且不同于 PRE-05 旧值；二次佐证（`[INFERRED]`，minify 可能把中文转义为 `\uXXXX`，仅作辅助，不单独判失败）：`ibssh 'grep -l "请选中单个节点后再删除" /var/www/intelligentbase/assets/*.js'` 命中新 bundle |
| V-04 | 日志无新增错误 | A | `PULL_TS` 取 DEPLOY-001 输出（形如 `2026-10-31 16:30:00`），作为本地值以位置参数传入（Q2）：`ibssh bash -s -- "$PULL_TS" <<'EOF'`，heredoc 体为 `journalctl -u ib-web --since "$1" -p warning --no-pager \| tail -n 30; journalctl -u ib-worker --since "$1" -p warning --no-pager \| tail -n 30`（粘贴时 heredoc 顶格，去掉表格中的转义反斜杠） | 区间内无 Traceback / OperationalError 等新错误；已知长期 warning（如 daemon-reload pending）除外，需如实记录 |
| V-05 | 健康检查与外部可达 | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz'`；`curl -sS -o /dev/null -w '%{http_code}\n' https://192.168.31.133/healthz`（不携带凭据；`-k` 仅用于公开首页） | 均 200 |
| V-06 | **上线后人工浏览器验收（必做）**：`e2e_test_report.md`「人工验证清单」M-01~M-08；**不改写其步骤与期望**，以该文件为准。所用环境 = PRE-06 的独立测试项目；先 Ctrl+F5 硬刷新 | U* | 浏览器 `https://192.168.31.133/` → 配置页 | 逐条填 通过 / 不通过 + 截图（不含凭据）；见下表 |
| V-07 | REQ-NFUNC-001 "1 秒"目标机校准（M-03 的一部分） | U* | 在 30 节点图（测试项目中构造）上，开发者工具 Performance 面板或录屏逐帧计时：点击"删除节点"（确认）→ 画布更新 | 实测值记入报告；≤ 1 秒为达标；**校准前该项保持"未验收"**（e2e 报告 INF-5）；超限不阻断部署，作为遗留问题回填 |
| V-08 | 本地状态未被触碰 | A | `ibssh 'cd /opt/intelligentbase && git status --porcelain; ls -d src/frontend/node_modules venv 2>&1 \| head -n 3'` | 已跟踪文件干净；`node_modules` 与 `venv` 仍在；（不读 env、不进状态目录） |
| V-09 | 部署后前端冒烟（写入数据唯一化） | U | 登录后打开配置页、选择测试项目、仅读取：不新增写入；若需保存见 M-08，节点 / agent 名称带 `r27-<epoch>` 后缀以唯一化 | 页面加载无白屏、无控制台错误；既有"保存并生效"流程可用（M-07 / M-08 覆盖） |

### V-06 逐项（引用 e2e_test_report.md「人工验证清单」，critical path 5 条必做）

| 编号 | 对应 AC | critical path | 要求 | 备注 |
|---|---|---|---|---|
| M-01 | AC-002-01、风险 R-1 | **是（必做）** | 编辑档，画布 Delete 键只删被选中节点，删除后再选下一节点 Delete 仍生效，无脚本报错 | 验证 vue-flow 选中态不因图更新丢失 |
| M-02 | AC-002-03、AC-002-06 | 否（建议做） | 文本框内 Delete / Backspace 只删字符；空白画布按 Backspace 不删节点 | Should |
| M-03 | AC-008-01、REQ-NFUNC-001 | **是（必做）** | 悬停卡片消失、右侧面板复位；耗时 ≤ 1 秒 | 在目标机浏览器计时；结果同 V-07 |
| M-04 | AC-002-04 | 否（建议做） | Shift / Ctrl 多选两个节点按 Delete，均不删并提示 | Should |
| M-05 | ASM-R27-02 | 否（建议做） | 1 节点 + 1 边混选按 Delete，记录实际现象供 PM / 用户判断 | 非阻断 |
| M-06 | AC-007-01/02、AC-009-05 | **是（必做）** | 查看档账号无"删除节点 / 删除 agent"，Delete 键无效，无撤销条、"未保存"不出现 | 需查看档账号 |
| M-07 | AC-010-01/02 | **是（必做）** | 删节点不保存时版本号与审计条数不变、终端用户提问仍路由到 billing-agent；"保存并生效"后点"取消"，草稿保留 | 在测试项目的等价 agent 上做；需终端用户账号 |
| M-08 | AC-005-03/04/05、AC-004-01~06 | **是（必做）** | 先"删除节点"（"从画布移除"文案）并保存，提示词文件仍在；再"删除 agent"并保存，提示词文件被移除、历史会话仍显示名称；"版本历史"可回滚找回 | 写测试项目；检查文件需用户 sudo（Q5）；结束后用"版本 → 回滚"复原（I-1） |

- **通过标准**：critical path 5 条（M-01、M-03、M-06、M-07、M-08）全部通过，且 V-01~V-05、V-08 全部通过 → `DEPLOYED_SUCCESSFULLY`；机器可验项通过但 critical path 有未完成 / 不通过 → `DEPLOYED_WITH_ISSUES`（`e2e_test_report.md` 已声明这些项为 NOT_TESTABLE 的"待人工验证"，协议 §K：未完成前最终状态至多 `DELIVERED_WITH_ISSUES`）。M-02、M-04、M-05 结果记录但不阻断。
- 回滚后的验证：V-01、V-03（hash 应等于 PRE-05 旧值或新重建值）、V-05、V-08；V-06 不再适用。

## 下游产物同步核对（M-DE-001 / 003 / 004 / 008）

| 产物 | 核对方法与结论 | 处置 |
|---|---|---|
| `.github/workflows/ci.yml` | REV-27 无新阶段 / 依赖 / env；Node 22 已满足；新测试被 `node --test` 与 `pytest tests/unit` 自动发现（见 cicd_pipeline.md） | **无需修改**，未改动 |
| `src/deploy/checklists.txt` | REV-27 无新增 `[Bn]` 项；`git diff bb3ac4b 1dde3d4 --stat` 未涉及 `src/deploy`、`src/scripts/selfcheck.py`（P-DE-001 的签署行断言无影响） | 无需修改 |
| `src/deploy/systemd/*.service`、`env*.example`、`nginx/*`、`migrations/` | 无改动 | 无需修改；PRE-02 机械复核（CLASS-C 依据） |
| `package.json` / `package-lock.json` | 无改动 → 不执行 `npm ci`；PRE-02 "依赖 / 锁文件"一行为空才继续 | 无需修改 |
| `docs/deployment_plan.md`（REV-21 基线）、`deployment_report.md` | 只读 | 未改 |

## `[INFERRED]` 汇总（画像与设计均未给出的取值）

前端发布无停机、切换窗口 ≤ 数秒；PRE-03 磁盘 / 内存余量阈值（1 GiB / 1 GiB）；构建命令超时 ≥ 300 秒（本机实测构建约 27 秒）；条件步骤 ib-web 不可用 10–30 秒、就绪轮询 30×2 秒、ib-worker 轮询 20×3 秒与观察 15 秒、命令超时 ≥ 360 秒；web root 副本目录 `~/ib-webroot-pre-r27`；M-08 提示词目录的具体项目子路径；旧页面未保存草稿的 chunk 404 风险；V-03 中文字符串在 minify 后的可 grep 性；分类门中"仅 `cache.py`"归 CLASS-B 的划分（依据 `git diff bb3ac4b 1dde3d4 -- src` 实测，目标机若落后更多则归 CLASS-C）。
`[TOOL_UNREGISTERED]`：`gh`（仅 PRE-00 取证便利，网页可替代）。
