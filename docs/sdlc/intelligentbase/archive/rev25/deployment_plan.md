<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-24T23:44:16+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>implementation_plan.md</file>
    <file>e2e_test_report.md</file>
    <file>phase_status.md</file>
    <file>cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：资料管理文件夹树增量（INCREMENTAL，R25，仅计划）

> **本文件不执行任何步骤。** 本轮未连接目标机、未 ssh、未 commit / push（画像 P9）。所有命令是 E2 获得 `PRODUCTION_DEPLOY_CONFIRM=true`（目标环境名 `production`）后才可执行的**计划内容**。
> 基线 `docs/deployment_plan.md`（REV-21，1898 行）只读、不续写；本文是 R25 的独立计划（画像 P2）。
> 依据：`.claude/skills/ib-prod-deploy/SKILL.md`（§1–§9）、`module_design.md`「数据迁移」「受影响的运行单元 / 构建」、`architecture_design.md` ADR-003/009/010 与部署视图、GR-B-001 / GR-C-002 / GR-D-002 的 condition。
> 测试门控：phase_status 中 GROUP_D = APPROVED（GR-D-002 PASS_WITH_CONDITIONS，PM 复跑 unit 314 / integration 225 / e2e 45 / full 605 passed，前端 46/46，selfcheck 53/54〔`core_framework_free` 为本机环境项〕）。

## 给 PM 的部署计划摘要（供向用户请求 E2 授权）

| 项 | 内容 |
|---|---|
| 目标环境 | `production`（单台物理机 192.168.31.133，SSH 密钥；画像 P7"部署需用户确认=是"）。无 staging。 |
| 策略 | **recreate**（单机 systemd 重启；画像唯一允许）。预计 ib-web 不可用约 10–30 秒 `[INFERRED]`；ib-worker 重启最长等 300 秒（`TimeoutStopSec`，用户无感）；内存态聊天会话会丢失；前端发布无停机。 |
| 步骤数 | 预检 10（PRE-00~09：PRE-00 为主会话，PRE-06~09 为用户执行）；部署 **4**（DEPLOY-001 git pull → 002 重启 ib-web〔自动应用 007〕→ 003 重启 ib-worker → 004 前端构建发布）；部署后验证 13（V-01~13，其中 V-05/07/08/11/12 为用户执行）；回滚 7 + 1 条紧急止血（ROLLBACK-000/001a/001b/002a/002b/003/004，+ 001-E） |
| 不可逆 / 需人工 | **3 项** `[MANUAL_ROLLBACK_REQUIRED]`：① 新表/新列 DROP（ROLLBACK-002b，默认不执行，需备份与 SQLite ≥3.35）；② 上线后用户操作造成的数据变化（更新晋升后旧内容已物理清除、移动覆盖、删除）代码回滚无法还原；③ 已索引待晋升的修订行无法经 API 丢弃（ROLLBACK-000 的人工分支）。 |
| 回滚方式 | 源头 `git revert` → 用户确认后 push（主会话）→ 目标机 `git pull --ff-only` → 重启 ib-web / ib-worker、重建前端。回退代码前**必须先通过 ROLLBACK-000**（清空在途修订行、清理队列排空）。不使用 `reset --hard` / `clean` / `stash`。 |
| 需要用户（非代理）执行 | 提交并 push 待部署提交（PRE-00，主会话经用户确认）；台账备份（PRE-06，`sudo`）；台账只读基线查询（PRE-07）；env 键存在性计数与按需写入（PRE-08/09）；部署后结构核对 V-07；API 写冒烟 V-08；浏览器 UI 复核 V-12；`daemon-reload` / unit 安装 / env 修改 / `nginx reload`：**本次均不需要**（unit、nginx 零变更，env 默认值无需改动，除非 PRE-09 判定要调总大小上限）。 |
| 前提（E2 授权时由 PM 填入 `special_instructions`） | `PRODUCTION_DEPLOY_CONFIRM=true`；环境名 `production`；`DEPLOY_COMMIT=<40 位哈希>`（用户确认并 push 的待部署提交，当前工作区改动**尚未提交**，其中大量新文件为 untracked，见 PRE-00）。 |
| GR-B-001 条件 A-01 结论 | 总大小上限默认 1024 MB 的**判定规则与建议值**见 PRE-03 / PRE-09；以目标机实测磁盘余量代入规则，通过则保持默认、**不改 env**。 |
| GR-C-002-F01 对运维的影响 | 重建任务处于 `succeeded` 未激活时，部署后：启动不同目标版本的新重建返回 409；新增/更新的文件写入目标版本，激活前 `searchable=false`。PRE-07 先查并由用户决定（建议先激活或回滚该任务，再部署）。 |

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启 / 发布的运行单元 |
|---|---|---|---|---|
| 台账结构 | `src/ib/ledger/schema.py`、`src/deploy/migrations/007_folder_tree.sql`（新） | **007**：4 张新表 + `documents` 6 列 + 3 个唯一索引 + `name_key` 回填；幂等；由 `ib-web.service` 的 `ExecStartPre … --ensure-schema` 自动应用 | — | `ib-web`（重启即应用） |
| 目录树 / 批次 / 修订存储 | `src/ib/ledger/tree.py`（新）、`upload_batches.py`（新）、`sqlite_repo.py`、`src/ib/ledger/__init__.py`、`src/ib/core/{library.py(新),types.py,ports.py,__init__.py}` | 同上 | — | `ib-web` + `ib-worker` |
| 生命周期 / 重建 / 检索 / 流式 / 配置 | `src/ib/{lifecycle,rebuild,retrieval,streaming,config}/__init__.py`、`src/ib/library/`（新） | 无 | — | `ib-web` + `ib-worker` |
| Web 接口层 | `src/ibweb/{library_views.py(新),urls.py,views.py,serializers.py,composition.py}` | 无 | — | `ib-web` |
| worker 周期动作 | `src/ibweb/worker.py`（补晋升 / 清理队列排空 / 过期批次清理） | 无 | — | `ib-worker` |
| 前端 | `src/frontend/src/{api/client.ts,views/UploadPage.vue,views/ChatPage.vue,views/library/*,stores/uploadBatch.ts}` | 无 | 目标机 `npm run build` | 不重启，拷贝 web root |
| 自检 / 清单 / CI | `src/scripts/selfcheck.py`、`src/deploy/checklists.txt`（本次追加 B28）、`.github/workflows/ci.yml`（本次改） | 无 | — | 不影响运行（非运行时交付物） |
| **不变** | ib-embed、qdrant、nginx（`client_max_body_size 64m` 保持）、全部 systemd unit、`src/requirements*.txt`、`package.json` / `package-lock.json`、`/etc/intelligentbase/*.env`（默认值无需改） | — | — | 无（PRE-02 用 `git diff` 机械核对） |

**"改什么重启什么"核对（SKILL.md §6）**：`ibweb/**`→ib-web ✓（DEPLOY-002）；`ibweb/worker.py` 与入库链路（`ib/lifecycle`、`ib/ledger`、`ib/rebuild`）→ib-worker ✓（DEPLOY-003）；`ib_embed` 无改动→不重启 ib-embed ✓；前端→不重启、拷贝 web root ✓（DEPLOY-004）；env 无必改项（仅 PRE-09 条件分支，由用户执行并并入 DEPLOY-002 的同一次重启）；unit / nginx 零变更→无 `daemon-reload`、无 `nginx reload` ✓；迁移 007→随 ib-web 重启自动应用 ✓。

## 目标环境与策略

- **环境**：`production`（画像 P7）；SSH 密钥 `~/.ssh/ib_prod_ed25519`，主机 / 用户见 SKILL.md §1–§2。不设计 staging。
- **策略：recreate**。理由：单机、单实例（ib-web ×1、ib-worker ×1，**禁多实例**〔画像 P8〕）、无负载均衡与第二套环境，rolling / blue-green / canary 均无基础设施。
- **步骤顺序理由**：`git pull` → 先 ib-web（`ExecStartPre` 先应用 007 与 `name_key` 回填，`ib-worker.service` 本就 `After=ib-web.service`）→ 再 ib-worker → **最后**发布前端（新 UI 只在后端已就绪后才对用户可见；旧前端在整个窗口内仍可用，旧端点保持兼容）。
- **兼容窗口**：ib-web 新、ib-worker 旧的短窗口内，若有人经 API 创建修订行，旧 worker 会把它当普通行索引；新 worker 启动后 `promote_ready_revisions` 会自愈晋升（module_design MOD-011）。前端最后发布，此窗口内无 UI 入口，风险可忽略。
- **预计停机**：见摘要；建议在无人使用的时段部署，并请用户确认当前无进行中的聊天与上传。

## 执行约定（引号与变量）

执行端为 bash（Git Bash / Linux），**不要**把复杂命令作为参数从 PowerShell 传入（SKILL.md §4.2 的 5.1 引号改写坑）。

```bash
# 连接函数（密钥 / 主机 / 用户见 SKILL.md §1-2；BatchMode 保证绝不回落到口令交互）
ibssh() { ssh -i ~/.ssh/ib_prod_ed25519 -o UserKnownHostsFile=/tmp/ib_kh -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@192.168.31.133 "$@"; }
```

| 规则 | 说明 |
|---|---|
| Q1 | 不含本地值的远端命令：整条放进**单引号**，`$VAR` 在**远端**展开。 |
| Q2 | 需要本地值（`ANCHOR`、`DEPLOY_COMMIT`、`REVERT_COMMIT`）：一律用 `ibssh bash -s -- "$A" "$B" <<'EOF' … $1 $2 … EOF`——本地双引号只负责把值作为**位置参数**传过去，heredoc 用单引号定界使本地不展开，远端用 `$1 $2`。**禁止**写 `ibssh 'git checkout $ANCHOR -- …'`（`$ANCHOR` 在远端为空）。 |
| Q3 | 单引号内有意在远端定义并使用的变量（如 `TS=$(date …)`）是远端变量，属预期。 |
| Q4 | 变量取值与核验：`ANCHOR` = PRE-01 输出的 40 位 `git rev-parse HEAD`；`DEPLOY_COMMIT` = PM 在 `special_instructions` 下发；`REVERT_COMMIT` = ROLLBACK-001a 产生。使用前先本地核验 `[[ "$X" =~ ^[0-9a-f]{40}$ ]]`，并在远端 `git cat-file -t "$X"` 必须输出 `commit`；PRE-02 / ROLLBACK-001b 内置该核验。 |
| Q5 | 台账只读查询 / 备份一律在目标机上以 **`sudo -u ib-web`** 身份执行并用 `mode=ro` 打开（root 打开台账会把 `-wal` / `-shm` 建成 root 属主，复现 DEFECT-R18-01，见 checklists B22）；这些命令需口令，**由用户在交互式会话中粘贴执行**，输出只含名称与计数。 |
| Q6 | 凭据：令牌只经执行者 shell 的环境变量（如 `IB_ADMIN_TOKEN`）注入，不回显、不入日志、不入库；不读取、不回显 `/etc/intelligentbase/*.env` 的值（仅 `grep -c` 计数）。 |

## 预检清单

执行者：`A` = devops 代理经 ssh（E2 授权后）；`U` = 用户（需 sudo 口令或主会话权限）；`M` = 主会话（经用户确认，画像 P9）。任一项不通过：**停止，不进入 DEPLOY-001**（目标环境尚无变更，报告 `DEPLOYMENT_FAILED`，无需回滚）。

| ID | 检查项 | 执行者 | 命令（详见下方命令块） | 通过标准 |
|---|---|---|---|---|
| PRE-00 | 待部署提交已在远端；新文件已入库；CI 全绿 | M | `git ls-remote` / `git ls-tree` / Actions | 见下 |
| PRE-01 | 目标机 HEAD 记录为**回滚锚点**；跟踪文件无本地修改 | A | `git rev-parse HEAD`、`git status --porcelain` | HEAD 为 40 位哈希且记入报告；无 ` M` 的已跟踪文件 |
| PRE-02 | 变更集与目标机本地状态不冲突；"不变"面确无改动 | A | `git fetch` + `git diff --name-only` | 交集为空；systemd / nginx / ib_embed / requirements / package*.json 零改动；`src/deploy` 仅 `migrations/007_folder_tree.sql`、`checklists.txt` |
| PRE-03 | 磁盘 / 内存 / 工具链余量；**A-01 判定** | A（+U 取 du） | `df`、`free`、`node -v` | 满足下方判定规则 |
| PRE-04 | 目标机 SQLite 版本 | A | venv `python -c 'import sqlite3…'` | ≥3.8.3 为部署硬门；≥3.35 仅为 DROP COLUMN 回滚所需（不足则 ROLLBACK-002b 改"重建表"人工路径，不阻塞部署） |
| PRE-05 | 服务与时钟基线 | A | `systemctl is-active/show`、`date` | 5 个单元 active；记录 ib-web / ib-worker / ib-embed 的 `ActiveEnterTimestamp` 与 `NRestarts` |
| PRE-06 | 台账备份（迁移 007 前） | U | `sqlite3.backup` + `du` | 备份文件 660 `ib-web:ib`，完整性 ok，行数一致；只拷贝、不回显内容 |
| PRE-07 | 重建任务与文档状态基线（GR-C-002-F01） | U | 只读脚本 | 无 `planned`/`running` 重建；`succeeded` 未激活项已由用户决定；`pending`/`parsing` 文档记录在案 |
| PRE-08 | 新 env 键是否已存在（仅计数） | U | `sudo grep -c` | 计数结果记录；不回显值 |
| PRE-09 | 按 PRE-03 判定结果决定是否写 `IB_UPLOAD_BATCH_MAX_TOTAL_MB` | U（条件） | `tee -a` | 默认通过则**跳过**；写入后 env 仍为 600 |

### PRE-00（主会话，开发机；push 由主会话在用户确认后执行，子代理不 push）

```bash
# DEPLOY_COMMIT 由主会话在用户确认后 commit+push 得到
git status --porcelain                         # 不得遗漏 src/ tests/ 下的 '??' 新文件（见下）
git ls-remote origin refs/heads/main           # 首列必须 == DEPLOY_COMMIT
git ls-tree -r --name-only "$DEPLOY_COMMIT" | grep -cE '^(src/deploy/migrations/007_folder_tree\.sql|src/ib/library/uploads\.py|src/ib/core/library\.py|src/ib/ledger/tree\.py|src/ib/ledger/upload_batches\.py|src/ibweb/library_views\.py|src/frontend/src/stores/uploadBatch\.ts|src/frontend/src/views/library/LibraryBrowser\.vue)$'   # 期望 8
```

- **为什么查新文件**：当前 `git status` 显示 007 迁移、`src/ib/library/`、`library_views.py`、`views/library/` 等均为 **untracked**；漏 `git add` 则目标机 `git pull` 后缺文件，ib-web 起不来。
- **CI**：在 GitHub Actions 确认 `DEPLOY_COMMIT` 的 CI 运行全部成功（含本次扩展的 Schema 门，PIPE-02）。红灯不得部署。`gh run list`（`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`，仅为可选便利，页面查看等价）。
- 仓库为 PUBLIC：`deploy_templates_have_no_secrets` 自检已在 PM 复跑中通过（selfcheck 53/54）。

### PRE-01（A）

```bash
ibssh 'cd /opt/intelligentbase && git rev-parse HEAD && git log --oneline -1 && git status --porcelain'
```

输出的 40 位哈希即 `ANCHOR`，写入 deployment_report 首节并在后续命令作为本地变量使用。`git status --porcelain` 中的已跟踪文件修改（` M`）必须为空；`??` / 被忽略项（venv、node_modules 等）属本地状态，只记录、不触碰。

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
echo "--- src/deploy 变更(期望仅 007 与 checklists):"
git diff --name-only "$1" "$2" -- src/deploy
EOF
```

`git fetch` 只更新远端跟踪引用，不改工作树。若"不应变化的部署面"非空 → 依赖或 unit 有变，超出本计划范围，停止上报。

### PRE-03（A；`du` 部分 U）与 A-01 判定

```bash
ibssh 'df -B1 --output=target,size,used,avail,pcent /var/lib/intelligentbase /var/lib/qdrant /opt/intelligentbase /var/www/intelligentbase; free -m | sed -n 1,2p; node -v; npm -v'
```

`sudo du -sb /var/lib/intelligentbase /var/lib/qdrant` 由用户执行并随 PRE-06 一并回报（`yangyang198354` 不在 `ib` 组，无权读）。

**判定规则（GR-B-001 条件 A-01；系数与余量为 `[INFERRED]`）**：令 `C` = 拟定的 `IB_UPLOAD_BATCH_MAX_TOTAL_MB`（字节），`F` = `/var/lib/intelligentbase` 所在文件系统的可用字节（`df avail`），`B` = 台账文件大小（PRE-06 的备份将占同等空间），`R` = 保留余量 = max(10 GiB, 该文件系统总量的 15%)。
- 理由：blob 永久持久化（基线 ADR-05），一批最多新增 ≈`C`；更新期间修订行与旧版并存最坏再 ≈`C`；向量与重建开销另计入 `R`。故要求 **`F − B − R ≥ 3·C`**。
- 若 `/var/lib/qdrant` 与台账不在同一文件系统，需另行满足 checklists A8（重建期间 Qdrant 数据 ×2）；本规则只管 blob / 台账所在盘。
- **取值**：`C* = min(1024 MiB, floor((F − B − R) / 3) 向下取整到 128 MiB 倍数)`。
  - `C* = 1024`（默认）→ **保持默认，不改 env**（预期情形：SKILL.md 快照 2026-10-07 记录 78 GiB 可用，远超 `3·1 GiB + 10 GiB`，但**以 PRE-03 实测为准**，不以快照代替）。
  - `128 ≤ C* < 1024` → 进入 PRE-09，写入 `IB_UPLOAD_BATCH_MAX_TOTAL_MB=<C*>`（用户执行）。
  - `C* < 128` → **停止部署并上报**（磁盘余量不足以安全承载批量上传，需用户先清理或扩容）。
- 下限提醒：`C*` 不得小于单文件上限 `IB_MAX_UPLOAD_MB`（默认 50）；该键本身不改（须 +multipart 开销 <64 MB，nginx `client_max_body_size 64m` 不变）。
- 其余容量项 `[TBD]`：批量上传并发 2 与 SSE 共享 8 个 Waitress 线程、单 worker 对大批量的索引排队时长，沿用基线 TBD 机制，部署后凭实测记录，不用开发机数据代替。

### PRE-04（A）

```bash
ibssh '/opt/intelligentbase/venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"'
```

设计依据：递归 CTE ≥3.8.3、部分索引 ≥3.8.0（硬门）；开发机 3.45.1；目标机为 Ubuntu 26.04，预计远高于门槛 `[INFERRED]`，以实测为准。

### PRE-05（A）

```bash
ibssh 'date "+%F %T %Z"; systemctl is-active ib-web ib-worker ib-embed qdrant nginx; systemctl show -p ActiveEnterTimestamp,NRestarts ib-web; systemctl show -p ActiveEnterTimestamp,NRestarts ib-worker; systemctl show -p ActiveEnterTimestamp ib-embed'
```

全部 `active` 才继续。`ib-embed` 的 `ActiveEnterTimestamp` 作为 V-10 的"未被重启"对照。

### PRE-06 台账备份 + 容量回报（U；在交互式远端会话中粘贴，**不要**经 PowerShell 参数传入）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import os, sqlite3
os.umask(0o007)                                   # 备份文件 660 ib-web:ib（与台账同口径）
src = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
dst = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r25.bak")
src.backup(dst); dst.close(); src.close(); print("backup done")
PY
sudo ls -l /var/lib/intelligentbase/ledger/ | grep -E 'ledger\.sqlite3'
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r25.bak?mode=ro", uri=True)
print("backup_integrity=", c.execute("PRAGMA integrity_check").fetchone()[0], "documents=", c.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
PY
sudo du -sb /var/lib/intelligentbase /var/lib/qdrant
```

- 只做**在线一致性拷贝**（SQLite backup API，含 WAL 中已提交页），不回显任何文档内容；备份与主库同目录，沿用 `*.pre-rev18.bak` 先例（B22 判据已排除 `*.pre-*.bak*` 冷备）。
- 通过标准：备份存在、非空、660 `ib-web:ib`；`backup_integrity=ok`；`documents` 计数与 PRE-07 的 `documents_total` 一致；回报 `du` 数值供 PRE-03 代入。
- 还原提示（回滚时用）：从备份还原后**必须** `sudo chmod 0660` 主库并核对属主 `ib-web:ib`（B22 陷阱）。验收通过后是否归档/删除该备份由用户决定。

### PRE-07 重建与文档状态基线（U；此刻 `documents` 尚无 007 新列，脚本不得引用它们）

```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
print("rebuild_open=", c.execute("SELECT project_id, from_version, to_version, state FROM rebuild_jobs WHERE state IN ('planned','running','succeeded')").fetchall())
print("documents_by_status=", c.execute("SELECT status, COUNT(*) FROM documents GROUP BY status ORDER BY status").fetchall())
print("documents_total=", c.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
print("documents_by_project=", c.execute("SELECT project_id, COUNT(*) FROM documents GROUP BY project_id ORDER BY project_id").fetchall())
PY
```

判定与处置：
- `planned` / `running`：**推迟部署**直到重建完成（推荐）；若用户坚持，须明示接受（worker 重启靠租约续跑，但属于不必要的风险）。
- `succeeded`（已重建完、**未激活**）：GR-C-002-F01 行为变更会影响运维——部署后（a）`start_rebuild` 对不同目标版本返回 409（放弃该版本须先激活再回滚）；（b）新增 / 更新文件写入目标版本，`searchable=false` 直到激活。**建议部署前由用户先激活或回滚该任务**；若保留，须知晓上述行为并写入 deployment_report。
- `pending` / `parsing` 文档数 > 0：记录在案；worker 收到 SIGTERM 会让当前一轮跑完（`TimeoutStopSec=300`），重启后租约回收续跑，不阻塞。

### PRE-08（U，只计数不回显）

```bash
sudo grep -c -E '^(IB_UPLOAD_BATCH_MAX_FILES|IB_UPLOAD_BATCH_MAX_TOTAL_MB|IB_LIBRARY_MAX_DEPTH|IB_UPLOAD_BATCH_TTL_HOURS|IB_MAX_UPLOAD_MB)=' /etc/intelligentbase/ib-web.env
```

仅回报计数。新键均有默认值；`ib-web.env` 里未知键被配置层忽略，故提前写入对旧代码无害。`IB_MAX_UPLOAD_MB` 若存在且用户记得其值 >60，新代码会在启动时记 WARNING（V-02 会看到），这是预期告警，不改变行为。

### PRE-09（U，条件：仅当 PRE-03 得到 128 ≤ C* < 1024）

```bash
echo 'IB_UPLOAD_BATCH_MAX_TOTAL_MB=<C*的整数MB值>' | sudo tee -a /etc/intelligentbase/ib-web.env >/dev/null
sudo stat -c '%a %U:%G %n' /etc/intelligentbase/ib-web.env       # 期望仍为 600 且属主不变
```

随后**无需单独重启**：DEPLOY-002 的那一次 ib-web 重启即生效（ADR-32：生效 = 保存 + 服务重启重装配）。回滚时该行可保留（旧代码忽略）；如需删除，用 `sudo sed -i '/^IB_UPLOAD_BATCH_MAX_TOTAL_MB=/d' /etc/intelligentbase/ib-web.env`（B23 先例，不用 vim、不先 cp），并复核 `stat` 仍为 600。

## 部署步骤

所有 DEPLOY 位置均为**目标机**（经 ssh），预检全部通过后按序执行；任一步失败按"失败处理矩阵"处置。

### DEPLOY-001: 目标机拉取代码（`git pull`，禁 scp / pscp / rsync）
- 组件: 全部后端 + 前端源码 + 迁移文件（architecture_design 部署视图）
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

### DEPLOY-002: 重启 ib-web（`ExecStartPre --ensure-schema` 自动应用 007 与 `name_key` 回填）
- 组件: ib-web（Waitress，127.0.0.1:18080）、台账 schema
- 位置: 目标机；`sudo -n systemctl restart ib-web`（三条免密 restart 之一，SKILL.md §4）
- 命令:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-web; for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/healthz)" = 200 ] && break; sleep 2; done; systemctl is-active ib-web; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-web; journalctl -u ib-web --since "$TS" --no-pager | grep -E "startup succeeded|ConfigError|OperationalError|Traceback|unable to open" | tail -n 20'
```
  （此处 `$TS` 在**远端**定义并展开，属 Q3；`RESTART_TS` 记入报告，供 V-02 / V-03 / V-06 复用。）
- 预期: `/healthz` 200；`is-active`=active、`SubState=running`、`NRestarts=0`；日志出现 `startup succeeded`，`ConfigError` / `OperationalError` / `Traceback` 零命中。`restart` 时的 `daemon-reload` pending 警告是长期存在的，不是本次引入（SKILL.md §7.2），不处理。
- 失败特征: `ExecStartPre` 失败时 `Restart=on-failure` 每 3 秒重试，日志刷屏——立即进入回滚，不要反复重启。ensure_schema 分阶段提交，失败时可能已补列 / 建表；这些结构纯追加，旧代码忽略，不构成回滚障碍。
- 回滚: ROLLBACK-002（002a 常规；002b 为人工 DROP，默认不执行）

### DEPLOY-003: 重启 ib-worker（单实例）
- 组件: ib-worker（入库队列 + 重建推进 + 补晋升 + 清理队列排空，ADR-010）
- 位置: 目标机；`sudo -n systemctl restart ib-worker`
- 命令（`TimeoutStopSec=300`，执行端命令超时需 ≥360 秒 `[INFERRED]`）:
```bash
ibssh 'TS=$(date "+%Y-%m-%d %H:%M:%S"); echo "RESTART_TS=$TS"; sudo -n systemctl restart ib-worker; for i in $(seq 1 20); do [ "$(systemctl is-active ib-worker)" = active ] && break; sleep 3; done; sleep 15; systemctl show -p ActiveState,SubState,NRestarts,ActiveEnterTimestamp ib-worker; echo "errors_in_log=$(journalctl -u ib-worker --since "$TS" --no-pager | grep -cE "unable to open database file|Traceback|OperationalError")"; pgrep -c -f "[i]bweb\.worker"'
```
- 预期: `ActiveState=active`、`SubState=running`、`NRestarts=0`；`errors_in_log=0`（含 B22 的"unable to open database file"无限重启特征）；`pgrep -c` 为 **1**（`[i]` 写法避免匹配到执行命令自身；单实例，画像 P8 禁多实例）。等待 15 秒 ≥ 两轮 `--interval 5`，使 `run_once` 新增的补晋升 / 清理排空至少执行过。
- 回滚: ROLLBACK-003

### DEPLOY-004: 前端构建并发布到 web root（不重启任何服务）
- 组件: 前端静态产物（nginx 直读 `/var/www/intelligentbase/`，属主 `yangyang198354`，无需 sudo）
- 位置: 目标机 `/opt/intelligentbase/src/frontend`（`node_modules` 已就位；`package-lock.json` 未变故不执行 `npm ci`）
- 命令（先留旧产物副本，再构建，构建成功才替换）:
```bash
ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r25 ]; mkdir ~/ib-webroot-pre-r25; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r25/; ls ~/ib-webroot-pre-r25'
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/ && grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html | sort -u'
```
- 预期: `vue-tsc --noEmit && vite build` 退出码 0；打印新的 `assets/index-<hash>.js`；`systemctl show -p ActiveEnterTimestamp ib-web` 与 DEPLOY-002 后相同（发布未触发重启）。构建失败时 `&&` 链在 `rm` 之前中断，web root 仍是旧产物（无停机）。
- 回滚: ROLLBACK-004
- 说明: 旧副本放在部署用户家目录（仓库外、不入 git），验收后由用户决定删除；`index.html` 为 `no-store`，`assets/*` 带新 hash，硬刷新即生效（SKILL.md §5.2）。

## 回滚步骤（逆序）

执行总序：**ROLLBACK-000（前置门）→ 001a（源头 revert + push）→ 001b（目标机 pull）→ 004 → 003 → 002a →（002b 默认不执行）**。ROLLBACK-001 是把"目标机代码状态"还原的载体，必须先于各单元重启落地；其余按 DEPLOY 的逆序（前端 → worker → web）。目标机 pull 到 ib-web 重启之间，ib-web 进程仍在内存中运行新代码，窗口应尽量短。

**不得破坏的本地状态**（全部回滚路径均不触碰）：`/etc/intelligentbase/*.env`、`/var/lib/intelligentbase/`（台账、blob、definition.json、prompts）、bge-m3 权重、Qdrant 数据、`/opt/intelligentbase/venv`、前端 `node_modules`。**本计划所有回滚均不使用** `git reset --hard`、`git clean`、`git stash`、覆盖式同步。

### ROLLBACK-000: 回滚前置门（任何"回退代码"之前必须通过；module_design「数据迁移」可逆性说明）
- 类型: 正式回滚的前置检查与清理（U；API 调用可由持令牌者执行）
- 原因: 旧代码不认识 `revision_of`：在途修订行会被当普通文档展示并重复索引；清理队列里的旧向量 / 旧 blob 若未排空，回退后（旧代码无台账存活过滤）被"替换掉的旧内容"会重新出现在检索中。
- 命令（只读查询，`documents` 缺 `revision_of` 列时按 0 处理）:
```bash
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("file:/var/lib/intelligentbase/ledger/ledger.sqlite3?mode=ro", uri=True)
cols = {r[1] for r in c.execute("PRAGMA table_info(documents)")}
tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if "revision_of" in cols:
    print("revisions_by_status=", c.execute("SELECT status, COUNT(*) FROM documents WHERE revision_of IS NOT NULL GROUP BY status").fetchall())
    print("revision_doc_ids(pending/failed)=", [r[0] for r in c.execute("SELECT doc_id FROM documents WHERE revision_of IS NOT NULL AND status IN ('pending','failed')")])
else:
    print("revisions_by_status= [] (no revision_of column)")
print("purge_queue=", c.execute("SELECT COUNT(*) FROM doc_purge_queue").fetchone()[0] if "doc_purge_queue" in tabs else 0)
PY
```
- 处置:
  - `pending` / `failed` 修订行：逐个丢弃（新代码仍在跑时）：`curl -sS -X DELETE -H "Authorization: Bearer ${IB_ADMIN_TOKEN}" -H "X-IB-Project: <项目>" "https://192.168.31.133/api/files/<doc_id>/revision"`（令牌来自环境变量，不回显；若证书为自签，按 B15 使用已预置的根证书，不得为发送令牌而关闭校验）。`parsing` 返回 409 `update_in_progress`：等待其结束后重查。
  - `indexed` 且 `revision_of` 非空（已索引、因重建推迟晋升的"就绪修订行"）：API 不能丢弃 → `[MANUAL_ROLLBACK_REQUIRED: 需先激活对应重建使其晋升，或手工删除该修订行及其向量 / blob（delete_document 语义：先向量、再 blob、最后台账行）；操作不当会留下无主向量或误删存活文件，须由用户逐项确认后执行，代理不自行处理]`。
  - `purge_queue > 0`：保持 ib-worker（新代码）运行等待排空，复查；若计数不降（`attempts` 增长，向量库不可用等）则不得回退代码，转人工。
- 通过标准: `revision` 行数为 0 且 `purge_queue=0`。
- 例外: 若失败发生在 DEPLOY-002 且 ib-web 从未成功启动（无人能创建修订行），脚本输出自然为 0，仍需执行该只读核对。

### ROLLBACK-001a: 源头 revert 并 push（主会话，用户确认；回滚 DEPLOY-001 的源头部分）
- 类型: 正式回滚
- 命令（开发机）:
```bash
git fetch origin main && git switch main && git pull --ff-only origin main
git log --merges --oneline "$ANCHOR..$DEPLOY_COMMIT"                 # 期望为空；非空则 revert 需加 -m 1，先上报
git revert --no-commit "$ANCHOR..$DEPLOY_COMMIT"                      # 反向还原整段范围，合并为一个回退提交
git diff --quiet "$ANCHOR" -- src && echo SRC_EQUALS_ANCHOR           # 暂存区 src 须与锚点逐字一致
git commit -m "revert(r25): roll back folder-tree release to ${ANCHOR}"
git push origin main
git rev-parse HEAD                                                    # = REVERT_COMMIT，记入报告
```
- 变量取值与核验: `ANCHOR` 取 PRE-01 的输出（deployment_report 首节）；执行前 `git cat-file -t "$ANCHOR"` 必须输出 `commit`，且 `git merge-base --is-ancestor "$ANCHOR" "$DEPLOY_COMMIT"` 成立。回滚用的是**新提交 + 普通 push**，不 force-push、不 reset。
- 预期: `SRC_EQUALS_ANCHOR` 打印；push 成功；CI 对回退提交自动运行（不要求等待结果才继续回滚，但须记录）。

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
git diff --name-only --diff-filter=M "$1" "$2" > /tmp/ib_r25_modified.txt
wc -l < /tmp/ib_r25_modified.txt                        # 先核对文件数与清单，再执行
xargs -a /tmp/ib_r25_modified.txt git checkout "$1" --  # 把这些文件还原为锚点版本
git status --porcelain | head -n 50
EOF
```
  随后 `sudo -n systemctl restart ib-web`（及按需 ib-worker）。
- 变量核验: `ANCHOR` 同上；执行后抽查一个文件，`git diff --stat "$ANCHOR" -- <该文件>` 必须为空（防止"回滚静默失效"）。
- **收尾（必做）**: 回退提交 push 后（001a）、在目标机 `pull` 之前，先把上述文件恢复到索引版本再 pull——`xargs -a /tmp/ib_r25_modified.txt git checkout HEAD --`，然后执行 001b，最后确认 `git status --porcelain` 无已跟踪修改，目标机回到与远端一致的干净状态。该步只作用于清单中的已跟踪文件，不触碰 env / 数据 / venv / node_modules。

### ROLLBACK-004: 回滚 DEPLOY-004（前端）
- 类型: 正式回滚 = 001b 之后在目标机用回退后的源码重新构建并发布（命令同 DEPLOY-004 的第二条）；紧急止血 = 还原部署前的 web root 副本。
- 正式回滚命令:
```bash
ibssh 'cd /opt/intelligentbase/src/frontend && npm run build && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets /var/www/intelligentbase/ && cp dist/index.html /var/www/intelligentbase/'
```
- 紧急止血（不依赖构建）:
```bash
ibssh 'set -e; test -s ~/ib-webroot-pre-r25/index.html; test -d ~/ib-webroot-pre-r25/assets; rm -rf /var/www/intelligentbase/assets; cp -r ~/ib-webroot-pre-r25/assets /var/www/intelligentbase/; cp ~/ib-webroot-pre-r25/index.html /var/www/intelligentbase/; ls -l /var/www/intelligentbase'
```
  收尾: 之后仍应执行正式回滚命令一次，使 web root 与远端 HEAD 的构建结果一致。
- 变量取值与核验: 无本地变量；执行前 `ls ~/ib-webroot-pre-r25` 确认副本存在且含 `index.html` 与 `assets/`（`test -s` / `test -d` 已内置）。
- 预期: 浏览器硬刷新后恢复旧资料管理页；`ActiveEnterTimestamp` 不变（无重启）。

### ROLLBACK-003: 回滚 DEPLOY-003（ib-worker 运行回退后的代码）
- 类型: 正式回滚（前提：001b 已完成、ROLLBACK-000 已通过）
- 命令: 同 DEPLOY-003 的 `restart ib-worker` 命令块。
- 预期: `active`/`running`/`NRestarts=0`，`errors_in_log=0`，`pgrep -c` 为 1。

### ROLLBACK-002a: 回滚 DEPLOY-002（ib-web 运行回退后的代码）
- 类型: 正式回滚（前提：001b 已完成）
- 命令: 同 DEPLOY-002 的 `restart ib-web` 命令块（回退后的 `ensure_schema` 不认识新结构，对多出的表 / 列无动作）。
- 预期: `/healthz` 200；`startup succeeded`；无 `ConfigError`。回退后行为：旧扁平列表会显示所有子目录里的文件，同名文件可并存（旧代码无同名约束），这是已知且已声明的回退后果（ADR-009 负向 ③）。

### ROLLBACK-002b: 撤销新结构（DROP 表 / 索引 / 列）——`[MANUAL_ROLLBACK_REQUIRED: 丢失全部目录结构、批次记录、清理队列与 uploaded_at / content_updated_at / indexed_at / name_key 等时间与命名语义；不可由代码恢复，只能从 PRE-06 备份还原。默认不执行；仅在确需撤销新结构（例如下次重新部署前要求回到 001–006 的纯净 schema）时，由用户在 ROLLBACK-000/001b/002a/003 之后执行]`
- 前提: ① PRE-06 备份存在且 `integrity=ok`；② PRE-04 的 SQLite ≥3.35（否则 `DROP COLUMN` 不可用，需"重建表"，属更高风险的人工操作，另议）；③ 已回退代码（旧代码运行中不需要这些结构）。
- 命令（用户执行；停服需口令，免密仅覆盖 restart）:
```bash
sudo systemctl stop ib-web ib-worker
sudo -u ib-web /opt/intelligentbase/venv/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect("/var/lib/intelligentbase/ledger/ledger.sqlite3", isolation_level=None)
c.execute("BEGIN IMMEDIATE")
for s in ("DROP TABLE IF EXISTS doc_purge_queue", "DROP TABLE IF EXISTS upload_batch_items",
          "DROP TABLE IF EXISTS upload_batches", "DROP TABLE IF EXISTS folders",
          "DROP INDEX IF EXISTS uq_documents_name", "DROP INDEX IF EXISTS uq_documents_revision",
          "DROP INDEX IF EXISTS idx_documents_folder"):
    c.execute(s)
for col in ("folder_id", "name_key", "uploaded_at", "content_updated_at", "indexed_at", "revision_of"):
    c.execute(f"ALTER TABLE documents DROP COLUMN {col}")
c.execute("COMMIT")
PY
sudo -n systemctl restart ib-web && sudo -n systemctl restart ib-worker
```
- 变量取值与核验: 无本地变量；索引必须先于列删除（SQLite 拒绝删除仍被索引引用的列）。执行后以 B28(3) 的脚本核对"6 列、4 表、3 索引均已不存在"，`integrity_check=ok`，再按 V-01 / V-03 / V-04 验证服务。
- 失败处理: 任一步报错 → 事务内的 DDL 随 `ROLLBACK` 撤销；仍失败则用 PRE-06 备份还原主库（先停服，`sudo cp -a` 到位后 `sudo chmod 0660` 并核对属主 `ib-web:ib`，B22）。

### 失败处理矩阵（E2 使用）

| 失败位置 | 目标环境是否已变更 | 处置 |
|---|---|---|
| 任一 PRE | 否 | 停止，`DEPLOYMENT_FAILED`，无需回滚 |
| DEPLOY-001（前置核对失败） | 否 | 同上 |
| DEPLOY-001（pull 后 HEAD ≠ 待部署提交 / 工作树不干净） | 是 | ROLLBACK-000 → 001a → 001b |
| DEPLOY-002 | 是（代码已拉；schema 可能已部分应用） | ROLLBACK-000 → 001a → 001b → 002a |
| DEPLOY-003 | 是 | ROLLBACK-000 → 001a → 001b → 003 → 002a |
| DEPLOY-004 | 是（可能已部分替换 web root） | 先 004 紧急止血以恢复可用；再 ROLLBACK-000 → 001a → 001b → 004 → 003 → 002a |
| 回滚步骤自身失败 | — | 停止回滚，`ROLLBACK_FAILED`，写清各步骤已部署 / 已回滚 / 未知，由用户人工介入 |
| 遇到 `[MANUAL_ROLLBACK_REQUIRED]` 分支 | — | 立即暂停，返回 BLOCKED 等待人工决定 |

## 不可逆步骤汇总

| # | 步骤 | 性质 | 数据风险 | 处置 |
|---|---|---|---|---|
| I-1 | ROLLBACK-002b DROP 新表 / 索引 / 列 | `[MANUAL_ROLLBACK_REQUIRED]` | 丢失目录结构、批次记录、清理队列与三个时间 / name_key 列 | 默认不执行；须备份（PRE-06）、SQLite ≥3.35、用户执行 |
| I-2 | 上线后用户操作的数据后果：更新晋升后旧版内容 / blob 被物理清除（C-04 不保留历史）、移动"覆盖"删除被覆盖文件、文件夹递归删除 | `[MANUAL_ROLLBACK_REQUIRED]`（代码回滚**不会**恢复） | 数据不可恢复，只能从 PRE-06 备份（仅台账）与用户原始文件重建；向量需重新入库 | 在部署报告 / 交付说明中向用户明示；回滚决策前先评估期间新增的用户数据 |
| I-3 | ROLLBACK-000 的"就绪修订行"人工分支 | `[MANUAL_ROLLBACK_REQUIRED]` | 手工删行 / 向量 / blob 可能误删存活文件或留下孤儿向量 | 由用户逐项确认；代理不自行处理 |

另（可逆但需知晓，非 MANUAL）：007 回填 `indexed_at` 为近似值（`updated_at`，A-07）；历史同目录大小写重名行仅 `name_key` 追加 `U+001F+doc_id`，显示名不变；迁移 / 回填无外部系统调用，不发送通知。

## 部署后验证

「真实启动时刻」= DEPLOY-002 / DEPLOY-003 输出的 `RESTART_TS`（远端时区 CST，已由命令在远端实取，不使用估算时间）。

| ID | 检查项 | 执行者 | 命令 / URL | 成功标准 |
|---|---|---|---|---|
| V-01 | 服务存活 | A | `ibssh 'systemctl is-active ib-web ib-worker ib-embed qdrant nginx'` | 5 行 `active` |
| V-02 | ib-web 启动日志无 ensure_schema 错误 | A | `ibssh 'journalctl -u ib-web --since "<RESTART_TS>" --no-pager \| grep -E "startup succeeded\|ConfigError\|OperationalError\|Traceback"'`；另 `… -p warning` 人工浏览 | 出现 `startup succeeded`；其余关键字零命中；`NRestarts=0`；warning 仅限已知项（如 `max_upload_mb>60` 告警，若 PRE-08 判断适用） |
| V-03 | ib-worker 日志与单实例 | A | `ibssh 'journalctl -u ib-worker --since "<RESTART_TS>" --no-pager \| grep -cE "unable to open database file\|Traceback\|OperationalError"; pgrep -c -f "[i]bweb\.worker"'` | 前者 0；后者 1；`NRestarts=0` |
| V-04 | 健康检查 | A | `ibssh 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/healthz/deps'` | 均 200 |
| V-05 | 台账文件权限（B22） | U | `sudo ls -la /var/lib/intelligentbase/ledger`（先 `is-active` 再隔几秒查） | 除 `*.pre-*.bak*` 冷备外，凡存在的 `ledger.sqlite3*` 均为 `660 ib-web:ib`；`ib-worker` 非 failed |
| V-06 | **线上代码版本判据**（目标机 HEAD + 源文件 mtime 早于 ActiveEnterTimestamp；**不得用 .pyc**，SKILL.md §7.1） | A | 见下方脚本 | `HEAD_MATCH`、`MTIME_OK`（ib-web 与 ib-worker 均成立） |
| V-07 | **只读结构校验**：documents 6 个新列、4 张新表、3 个唯一索引存在；`name_key` 已回填；行数未变；`integrity=ok`、`journal_mode=wal` | U | checklists.txt B28(3) 脚本（`sudo -u ib-web`，`mode=ro`） | 三个 `missing_*` 均为 `[]`；`unfilled_name_key=0`；`documents` 总数与 `by_project` 均 = PRE-07 的值；`revision_rows=0`（刚部署、无人更新时） |
| V-08 | 关键功能冒烟（写入数据唯一化、零残留） | U（持令牌者） | 以环境变量令牌依次：`POST /api/library/folders` 新建 `zz-deploy-smoke-<epoch>`（名称含 `date +%s`）→ `PATCH` 改名为 `…-renamed` → `DELETE /api/library/folders/<id>` → `GET /api/library` | 四次调用分别 201 / 200 / 200(done) / 200；所选项目根目录列表（`GET /api/library`，`page_size≤100`，必要时翻页）的文件数 = PRE-07 中该项目的 `documents_by_project` 计数，且既有 `indexed` 文件仍为 indexed / searchable（REQ-FUNC-017：既有文件仍在根）；不上传文件、不触发索引、结束后无残留 |
| V-09 | 外部可达性与前端已发布 | A（+开发机 curl） | 目标机：`ibssh 'grep -oE "assets/index-[A-Za-z0-9_-]+\.js" /var/www/intelligentbase/index.html \| sort -u'`；外部：`curl -sk https://192.168.31.133/ \| grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \| sort -u`；`curl -sS -o /dev/null -w '%{http_code}\n' https://192.168.31.133/healthz` | 两处 hash 一致且等于 DEPLOY-004 输出；`/healthz` 200（本命令不携带凭据，`-k` 仅用于取公开首页） |
| V-10 | 未变更组件确实未被触碰 | A | `ibssh 'systemctl show -p ActiveEnterTimestamp ib-embed; ss -lntp \| grep -E ":18080\|:8100\|:6333"'` | `ib-embed` 的时间戳 = PRE-05 记录值（未重启）；三个端口仍只监听 127.0.0.1；ib-web 的 `ActiveEnterTimestamp` 在 DEPLOY-004 前后不变 |
| V-11 | 重建与队列一致性（GR-C-002-F01） | U | B28(3) 输出的 `purge_queue`；重建任务状态沿用 PRE-07 脚本 | `purge_queue` 在若干 worker 周期后趋近 0；`rebuild_open` 与 PRE-07 一致（未被部署改变）；若有 `succeeded` 未激活项，按 PRE-07 的决定核对行为 |
| V-12 | **资料管理页 UI 复核**（`[NOT_TESTABLE]` 于离线测试，由用户在浏览器确认；先 Ctrl+F5 硬刷新） | U | 浏览器访问 `https://192.168.31.133/` →「资料管理」 | 逐项确认：① 选择文件夹上传（`webkitdirectory`；浏览器不支持时入口应隐藏），汇总显示 成功 / 跳过 / 失败；② 新建文件夹、③ 文件夹重命名、④ 删除文件夹（多步进度）、⑤ 更新已有文件（旧版期间仍可检索、成功后切换、失败保留旧版并提示）、⑥ 同名冲突三选项弹窗、⑦ 文件列表显示上传时间 / 更新时间 / 索引成功时间、⑧ 问答引用显示目录路径、⑨ 既有文件均在根目录且状态不变 |
| V-13 | 磁盘与资源复核 | A | `ibssh 'df -B1 --output=target,avail,pcent /var/lib/intelligentbase; free -m \| sed -n 2p'` | 余量与 PRE-03 相比无异常下降；PRE-03 判定使用的 `C*` 仍成立 |

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

回滚后的验证：用 V-01 / V-02 / V-03 / V-04 / V-09 / V-10，并把 V-06 中的 `DEPLOY_COMMIT` 换成 `REVERT_COMMIT`；V-07 改为 ROLLBACK-000 的只读脚本核对。

## 下游产物同步核对（计划修订后 grep / 比对，M-DE-001 / 003 / 008）

| 产物 | 核对方法与结论 | 处置 |
|---|---|---|
| `.github/workflows/ci.yml` | 007 未被旧 Schema 门覆盖（旧 :74-92 只查 003）；基线注释过时 | **已修改**（PM 授权）：Schema 门追加 007；第 15 行基线更新；diff 见 `cicd_pipeline.md`；本地正反例通过；待首次 push 后的真实 CI 验证 |
| `src/deploy/checklists.txt` | 无 007 对应验收项（B27 为最后一项） | **已追加 [B28]**（仅追加条目；`C. 验收签署` 增一行 B28）。**未把签署行改为 `B1–B28`**：`src/scripts/selfcheck.py:3535` 断言字符串 `"B1–B27" in checklists`，改动会令 selfcheck 少一项（M-DE-008）；该文件不在本角色写权限内。已实测 selfcheck 仍为 53/54（仅环境项）。**建议**后续由 software-developer 将 selfcheck 的清单项断言扩到 `[B28]` / `B1–B28`，届时再把签署行同步 |
| `src/deploy/systemd/*.service` | `git diff` 无改动；`ib-web` 的 `ExecStartPre --ensure-schema`、`WorkingDirectory=/opt/intelligentbase`、`ReadWritePaths=/var/lib/intelligentbase` 与本计划一致；`ib-worker` `After=ib-web.service`、`TimeoutStopSec=300`、`--interval 5` 已被步骤引用 | 无需修改；PRE-02 机械复核 |
| `src/deploy/*.env.example` | 4 个新键（`IB_UPLOAD_BATCH_MAX_FILES` / `_MAX_TOTAL_MB` / `IB_LIBRARY_MAX_DEPTH` / `IB_UPLOAD_BATCH_TTL_HOURS`）未登记；默认值无需 env 改动；配置层忽略未知键 | **未修改**（超出本次授权）；如 PM 希望登记，另行授权后只加注释掉的示例键并保持 `ib-web.env` / `ib-worker.env` 键集对称（M-DE-004：这 4 个键只对 ib-web 有意义，写错文件静默无效） |
| `src/deploy/nginx/*` | 无改动；逐文件上传 ≤50 MB 小于 `client_max_body_size 64m` | 无需 `nginx reload`（SSE 反代条件、http2 禁用均未触碰） |
| `src/deploy/migrations/007_folder_tree.sql` | 与 `folder_tree_ddl_script()` 去空白包含（CI 新门 + selfcheck 双重核对）；头注释含回滚说明 | 无需修改 |
| `docs/deployment_plan.md`（基线） | 只读 | 未改 |

## `[INFERRED]` 汇总（画像与设计均未给出的取值）

保留余量 `R = max(10 GiB, 文件系统 15%)` 与系数 `3·C`、128 MiB 取整粒度；ib-web 不可用 10–30 秒；ib-worker 观察等待 15 秒；ib-web 就绪轮询 30×2 秒、ib-worker 就绪轮询 20×3 秒；ssh 命令超时 ≥360 秒；web root 副本目录名 `~/ib-webroot-pre-r25`；目标机 SQLite ≥3.35（Ubuntu 26.04 预计满足，PRE-04 实测）；`name_key` 回填耗时（行数量级 ≤ 万）。
`[TOOL_UNREGISTERED]`：`gh`（仅 PRE-00 可选便利，可用网页替代）。
