<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-26T22:18:00+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment_plan.md</file>
    <file>cicd_pipeline.md</file>
    <file>phase_status.md</file>
    <file>module_design.md</file>
    <file>architecture_design.md</file>
    <file>e2e_test_report.md</file>
    <file>implementation_plan.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：R25 资料管理文件夹树（生产）

## 摘要

| 项 | 值 |
|---|---|
| 目标环境 | `production`（192.168.31.133，单台物理机） |
| 策略 | recreate（单机 systemd 重启；前端静态发布） |
| 部署提交 | `80f2962cafe5d17d40aebcb8e9aa31d4e38f54a1` |
| 回滚锚点 | `f49a39582b741e86eaf6bbbf5cb1cd5d71bbd9e4` |
| 开始 | 2026-10-25T01:23:32+08:00（预检启动） |
| 主体完成 | 2026-10-25T01:52:00+08:00 |
| 验收完成 | 2026-10-26T22:15:00+08:00（跨日，用户分两次完成 API/UI 复核） |
| 步骤 | DEPLOY 4 / 完成 4 / 失败 0（DEPLOY-001 首轮 pull 失败，修复属主后就地重试成功）/ 跳过 0 |
| 验证 | V-01~13 全部有实际结果，全部通过 |
| 回滚 | 未触发正式回滚；未执行 ROLLBACK-000/001/002/003/004 |
| 最终状态 | **DEPLOYED_SUCCESSFULLY** |

## 授权核对

| 核对项 | 结果 |
|---|---|
| 授权来源 | PM 在本次 invocation `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true`；源自用户当轮消息「将最新的代码部署到生产环境」 |
| 环境名一致 | 授权环境 `production` = 计划目标环境 = 画像 P7 `production`（部署需用户确认=是） |
| 计划版本 | `deployment_plan.md` v1.0.0 = phase_status 登记 APPROVED |
| CI 前置 | `80f2962` 的 CI run 40112554749 completed/success（20 steps 全 success） |
| 附加安全授权 | 用户 2026-10-26 明确选择「全量 NOPASSWD ALL」，安装 `/etc/sudoers.d/90-ib-deploy-full`（0440 root:root，`visudo -cf` 先校验）；已作为安全例外登记，见「遗留问题」 |

## 分步执行

| DEPLOY | 命令（摘要） | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| PRE-00 | 开发机：确认 `origin/main`、新文件入库、CI 绿灯 | 2026-10-25T01:23 | — | PASS | `origin/main=80f2962`；CI run 40112554749 success |
| PRE-01 | `git rev-parse HEAD` / `git status --porcelain` | 2026-10-25T01:23 | <1s | PASS | `ANCHOR=f49a39582b741e86eaf6bbbf5cb1cd5d71bbd9e4`；工作树干净 |
| PRE-02 | `git fetch` + 变更面机械核对 | 2026-10-25T01:24 | ~2s | PASS | 变更 171 文件；本地修改交集空；systemd/nginx/ib_embed/requirements/package* 零改动；`src/deploy` 仅 `checklists.txt`、`migrations/007_folder_tree.sql` |
| PRE-03 | `df`/`free`/`node -v` | 2026-10-25T01:26 | <1s | PASS | 可用 71508713472 B；available 9250 MB；node v22.22.1；npm 9.2.0 |
| PRE-04 | venv python 读 sqlite 版本 | 2026-10-25T01:26 | <1s | PASS | SQLite 3.46.1（≥3.5，DROP COLUMN 路径可用） |
| PRE-05 | 5 单元状态与时间戳 | 2026-10-25T01:26 | <1s | PASS | 全 active；ib-web/ib-worker/ib-embed 均 `2026-10-24 16:19:08 CST`、NRestarts=0 |
| PRE-06 | `sudo -u ib-web` SQLite online backup | 2026-10-25T01:38 | ~1s | PASS | `backup_integrity=ok`、`documents=2`；备份文件 151552 B；初建 640，验收时补为 660 `ib-web:ib` |
| PRE-07 | 只读查询重建任务/文档状态 | 2026-10-25T01:38 | <1s | PASS | `rebuild_open=[]`；`documents_by_status=[('indexed',2)]`；`documents_total=2`；New=1、demo=1 |
| PRE-08 | `sudo grep -c` 新 env 键 | 2026-10-25T01:38 | <1s | PASS | 计数 0（全部使用默认值） |
| PRE-09 | A-01 判定 | 2026-10-25T01:40 | — | SKIP | `F−B−R=54042799584 ≥ 3·1GiB` ⇒ `C*=1024`，保持默认，不改 env |
| DEPLOY-001 | 目标机 `git pull --ff-only` | 首轮 2026-10-25T01:41；重试 2026-10-25T01:46 | 首轮失败；重试 ~1s | PASS | 首轮因 `.trae/` 等路径 root 所有失败（HEAD 未前进，工作树已就地恢复）；用户 chown 后重试 `f49a395→80f2962` fast-forward，171 文件，`git status` 空 |
| DEPLOY-002 | `sudo -n systemctl restart ib-web` | 2026-10-25T01:47:53 | ~2s | PASS | `/healthz=200`；active/running/NRestarts=0；日志 `台账 schema 就绪`、`stage=startup outcome=succeeded`、`prompt_source main_file`；错误关键字 0；`/healthz/deps=200` |
| DEPLOY-003 | `sudo -n systemctl restart ib-worker` | 2026-10-25T01:48:44 | ~16s（含等 15s） | PASS | active/running/NRestarts=0；`errors_in_log=0`；`worker_procs=1`；有 `ledger_chmod_failed` WARN×3 |
| DEPLOY-004 | 备份 web root；`npm run build`；发布 | 2026-10-25T01:49~01:51 | ~12s 构建 | PASS | 旧产物 `~/ib-webroot-pre-r25`；新入口 `assets/index-DE-71Zgt.js`；ib-web `ActiveEnterTimestamp` 保持 01:47:54（未重启） |

## 验证结果

| ID | 实际结果 | 通过 |
|---|---|---|
| V-01 服务存活 | ib-web / ib-worker / ib-embed / qdrant / nginx 全 `active` | PASS |
| V-02 ib-web 启动日志 | `stage=startup outcome=succeeded`；`ConfigError/OperationalError/Traceback/unable to open` 计数 0；NRestarts=0 | PASS（计划期望字面 `startup succeeded`，实际为结构化等价事件，见遗留 MINOR） |
| V-03 worker 日志与单实例 | 错误关键字 0；`pgrep -c` = 1；NRestarts=0 | PASS |
| V-04 健康检查 | `/healthz=200`、`/healthz/deps=200` | PASS |
| V-05 台账权限 | 部署后 `ledger.sqlite3`/`-wal`/`-shm` 均 `660 ib-web:ib`；`pre-r25.bak` 已补 660 | PASS |
| V-06 代码版本判据 | `HEAD=80f2962...` → `HEAD_MATCH`；`src/ib`、`src/ibweb` 变更文件 mtime 均早于两单元 `ActiveEnterTimestamp` → `MTIME_OK` | PASS |
| V-07 只读结构校验 | `missing_cols=[]`、`missing_tables=[]`、`missing_indexes=[]`；`unfilled_name_key=0`；`documents_total=2`（New=1/demo=1，与 PRE-07 一致）；`revision_rows=0`；`integrity=ok`、`journal_mode=wal` | PASS |
| V-08 关键功能冒烟 | 项目 New：`POST /api/library/folders=201`；`PATCH=200`；`DELETE=200`（`done=true`、`deleted_folders=1`、`remaining_files=0`、`failed=[]`）；`GET /api/library=200`（`root_total=1`、`root_folders=0`、`root_files=1`，既有文件 `indexed/searchable=true`） | PASS（首次 401 为无有效令牌，重取令牌后通过） |
| V-09 外部可达与前端发布 | 目标机与开发机 `curl -sk https://192.168.31.133/` 均为 `assets/index-DE-71Zgt.js`；外部 `/healthz=200` | PASS |
| V-10 未变更组件 | `ib-embed ActiveEnterTimestamp` 保持 `2026-10-24 16:19:08 CST`；18080/8100/6333 仍仅监听 127.0.0.1 | PASS |
| V-11 重建与队列 | `rebuild_open=[]`；`purge_queue=0` | PASS |
| V-12 浏览器 UI 复核 | 用户 2026-10-26 复核：文件夹上传汇总、新建/重命名/删除、更新、同名冲突三选项、上传/更新/索引时间列、引用目录路径、既有文件根目录状态 —— **确认无误** | PASS |
| V-13 磁盘与资源 | `/var/lib/intelligentbase` 可用 71504650240 B（较 PRE-03 略降，符合迁移/备份预期）；内存 available 9181 MB | PASS |

## 回滚记录

未触发正式回滚。DEPLOY-001 首轮失败时 HEAD 未前进、服务未重启，按证据采取「就地恢复工作树到锚点 + 修复属主后重试」而非 `git revert`；未使用 `reset --hard` / `clean` / `stash`。

## 当前系统状态与人工建议

- 生产 HEAD = `80f2962cafe5d17d40aebcb8e9aa31d4e38f54a1`，`git status --porcelain` 为空。
- 服务：ib-web、ib-worker、ib-embed、qdrant、nginx 全部 active；ib-embed 全程未重启。
- 可保留项：`/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r25.bak`（660 `ib-web:ib`）与部署账号家目录 `~/ib-webroot-pre-r25`（旧前端产物）。是否清理由用户决定；建议验收稳定后保留至少一个发布周期。
- 属主修复：`.trae/`、`tests/agents/`、`src/ib/core/__init__.py` 已改为 `yangyang198354:yangyang198354`（历史 root 遗留），后续 pull 不再阻塞。
- sudo：`/etc/sudoers.d/90-ib-deploy-full`（`yangyang198354 ALL=(ALL) NOPASSWD: ALL`）已生效，`sudo -n true` 通过；一次性安装脚本与 V-08 临时脚本已从目标机删除。

## 遗留问题

| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| 生产 `.trae/`、`tests/agents/`、`src/ib/core/__init__.py` 曾为 root 所有，导致 pull 首轮失败 | DEPLOY-001 | MAJOR（已消除） | 已 chown；deployment_plan PRE-02 应增加「部署面路径属主/可写性」核对 |
| V-02 计划期望日志字面 `startup succeeded`，实际为 `stage=startup outcome=succeeded` | DEPLOY-002 | MINOR | 更新 deployment_plan V-02 的 grep 口径 |
| ib-worker 启动有 `ledger_chmod_failed:PermissionError` WARN×3（db/wal/shm） | DEPLOY-003 | MINOR（观察） | 不影响运行；worker 非属主无法 chmod，建议后续评估是否降级为 DEBUG 或由 ib-web 统一权限 |
| PRE-06 备份初建 640，计划期望 660 | PRE-06 | MINOR（已消除） | 验收时已 chmod 660；后续脚本显式 `os.chmod` |
| V-08 首次 401（令牌为空/过期） | V-08 | MINOR（流程） | 冒烟脚本应在执行前校验令牌非空并提示 |
| 全量 NOPASSWD ALL 安全例外 | 用户 2026-10-26 授权 | 安全 | 部署账号已等价 root；SSH 私钥 `ib_prod_ed25519` 需按 root 级密钥保管，禁止复制到其他设备 |
| V-12 为浏览器目检，无法在 CI/离线测试中自动化 | 计划 | 已知 | 每次发布保留用户目检项，或后续引入浏览器自动化并解决登录凭据托管 |
