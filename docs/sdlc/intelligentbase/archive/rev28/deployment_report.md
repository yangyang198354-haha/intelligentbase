<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-04T22:10:19+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/deployment_plan.md</file>
    <file>docs/sdlc/intelligentbase/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：REV-28 平台级顾问 agent + DeepSeek 联网（首发，联网全关）

## 摘要

| 项 | 内容 |
|---|---|
| 目标环境 | production（192.168.31.133；本次经外网入口 ai-freeark.xin:9999 登录，`~/.ssh/id_ed25519`，`StrictHostKeyChecking=yes`） |
| 策略 | recreate（仅重启 ib-web；前端静态发布无停机） |
| 开始 / 结束 | 2026-11-04T22:06 / 22:10（CST，本次 E2-003；预检 E2-001/002 见后） |
| 回滚锚点 ANCHOR | `8d6fd4b3458e5aae72d006ac13751072ca09dd5f` |
| 待部署提交 DEPLOY_COMMIT | `b4fa3a3df7fd39745363a52452779711b5979bec`（目标机 HEAD 已等于它） |
| PULL_TS / RESTART_TS | `2026-11-04 22:07:11` / `2026-11-04 22:07:47`（ib-web ActiveEnterTimestamp `Wed 2026-11-04 22:07:48 CST`） |
| 步骤统计 | DEPLOY 本轮 4 步（001~004）：完成 4 / 失败 0 / 跳过 0；按授权不执行：005、006、007、008（4 步，未执行，不计 SUCCESS）；回滚 0 |
| 最终状态 | **DEPLOYED_SUCCESSFULLY**（V-01~V-03、V-05~V-09 代理可执行项全部通过）。V-04、V-10、V-11（Stage 1 人工验证）标「待用户」，不计 PASS；按计划口径整体交付至多 DELIVERED_WITH_ISSUES，直至人工项完成 |

## 授权核对

- 授权来源：invocation `special_instructions` 含 `PRODUCTION_DEPLOY_CONFIRM=true`（PM 依据用户本轮消息原话「1.确认。 2  部署rev-28」写入），只对本次调用有效。
- 授权环境名 `production` = 计划环境名 `production` = 画像 P7 环境名 `production`。
- 计划 deployment_plan.md 2.0.0（文件头 APPROVED）= PM 下发的 APPROVED 版本；DEPLOY_COMMIT 为 40 位哈希，与本机 HEAD、origin/main 一致（PM 复核 PRE-00；本代理另见 `git ls-remote` 首列 = b4fa3a3…）。
- 主机指纹核验：执行前 `ssh-keygen -lF '[ai-freeark.xin]:9999'` 的 ED25519 = `SHA256:BwIe6k9QhLUWCPPyrOykjSDtrWn+EgtesTllQjUd2eY`，与 SKILL.md §1 一致（解决 0.2.0 遗留 1）。
- 约束遵守：未用 scp/rsync；sudo 仅 `sudo -n systemctl restart ib-web`；未 `sudo -S`、未输入口令；未读取/回显 `/etc/intelligentbase/*.env` 值（V-09 仅 `stat`）；未改 env、未 daemon-reload、未 nginx reload；未重启 ib-worker / ib-embed；未执行 DEPLOY-005~008；未 commit / push；未使用 reset --hard / clean / checkout。

## 分步执行

连接函数：`ibssh() { ssh -p 9999 -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 yangyang198354@ai-freeark.xin "$@"; }`

### 预检重跑（`export LC_ALL=C`，E2-003）

| ID | 命令 | 开始 | 结果 | 输出摘要 |
|---|---|---|---|---|
| PRE-01 | `ibssh 'export LC_ALL=C; cd /opt/intelligentbase && git rev-parse HEAD && git log --oneline -1 && echo "porcelain:[$(git status --porcelain)]"'` | 22:06 | PASS | HEAD=`8d6fd4b3458e5aae72d006ac13751072ca09dd5f` = ANCHOR；`porcelain:[]` 工作树干净 |
| PRE-02 | 计划 PRE-02 脚本原样，前置 `export LC_ALL=C`（`ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'`） | 22:06 | PASS，**CLASS=A** | `changed_files=112`；CLASS-X 依据空；CLASS-E 依据空；依赖变动行仅两行 `+lxml>=5.0,<7.0`；`ib/ibweb=39 mig009=1 frontend=8`；与目标机本地修改交集为空；末行 `CLASS=A`。LC_ALL=C 后脚本一次通过，无 comm 告警 |

### DEPLOY 步骤

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 git pull --ff-only | 计划 DEPLOY-001 脚本原样（`ibssh bash -s -- "$ANCHOR" "$DEPLOY_COMMIT" <<'EOF'`，含前置 HEAD==ANCHOR、origin/main==DEPLOY_COMMIT、`date "+PULL_TS=%F %T"`、`git pull --ff-only origin main`、后置 HEAD==DEPLOY_COMMIT、`test -s …/009_web_governance.sql`） | 22:07:01 | 16 s | DEPLOYED_SUCCESSFULLY（步骤成功） | `PULL_TS=2026-11-04 22:07:11`；fast-forward，尾部 `create mode 100644 tests/unit/test_webtools_tools_unit_r28.py`；`b4fa3a3 feat(advisor): REV-28 平台级顾问 agent + DeepSeek 联网检索`；`porcelain:[]`；rc=0 |
| DEPLOY-002 依赖/导入只读闸 | 计划 DEPLOY-002 脚本原样（`PYTHONDONTWRITEBYTECODE=1`，`cd src`，`$PY -B -c …` 三条） | 22:07:27 | 6 s | 步骤成功 | `lxml ok (6, 1, 3, 0)`；`import ok`；`009 ddl in-memory replay ok`；rc=0 |
| DEPLOY-003 重启 ib-web | 计划 DEPLOY-003 命令原样（`sudo -n systemctl restart ib-web`，轮询 `/healthz`，`systemctl show`，journal 关键字过滤） | 22:07:42 | 8 s | 步骤成功 | `RESTART_TS=2026-11-04 22:07:47`；`active`；`ActiveState=active SubState=running NRestarts=0 ActiveEnterTimestamp=Wed 2026-11-04 22:07:48 CST MemoryCurrent=100311040`；日志 `{"outcome": "succeeded", "stage": "startup"}`（含 egress_host=api.deepseek.com，backend=…ledger=sqlite…）；错误关键字与 `path_not_configured_using_in_memory_default` 零命中；ExecStartPre 迁移 009 随之自动应用（表落库由 V-04 用户核对） |
| DEPLOY-004 前端构建并发布 | ① `ibssh 'set -e; [ ! -e ~/ib-webroot-pre-r28 ]; mkdir …; cp -a /var/www/intelligentbase/. ~/ib-webroot-pre-r28/; test -s …/index.html; test -d …/assets; ls …'`；② `ibssh 'cd /opt/intelligentbase/src/frontend && npm run build 2>&1 \| tail -n 8 && test -s dist/index.html && test -d dist/assets && rm -rf /var/www/intelligentbase/assets && cp -r dist/assets … && cp dist/index.html … && sha256sum … && grep -oE "assets/index-…js" …'` | 22:07:57 | ①6 s ②25 s | 步骤成功 | ① 旧副本 `assets index.html`，旧 index.html sha256 `c9cad5aa…6f97306` = PRE-04 基线。② `✓ built in 10.91s`（仅 chunk >500 kB 的常规告警）；新 `index.html` sha256 `930868f62f9a5a7afe1b7da4beae96423c39dbb233c68e75cb5fbd55edfa6a7d`；`assets/index-UKe_bFLW.js`（旧为 `index-CwQd2QJ4.js`）。注：②为便于取输出尾部，`npm run build` 后接 `\| tail`，管道使 npm 退出码被掩盖；以 `test -s dist/index.html && test -d dist/assets` 与产出新 hash、`✓ built` 作成功依据（与计划命令的唯一差异，已如实记录） |
| DEPLOY-005 | 不执行（用户裁决 Q1 / 授权范围） | — | — | **跳过**（非 SUCCESS） | ib-worker ActiveEnterTimestamp 保持 15:09:38（V-01 佐证） |
| DEPLOY-006 | 不执行（CLASS=A，不适用） | — | — | **跳过** | ib-embed 时间戳不变 |
| DEPLOY-007 / 008 | 不执行（OPT-A 需另行授权；OPT-B 本轮不启用） | — | — | **跳过** | env 零改动，联网保持全关 |

## 验证结果

| ID | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 服务存活与重启范围 | `systemctl is-active ib-web ib-worker ib-embed qdrant nginx` 五行 `active`；ib-web `ActiveEnterTimestamp=Wed 2026-11-04 22:07:48 CST`（晚于 RESTART_TS 22:07:47）、`NRestarts=0`；ib-worker 与 ib-embed 均 `Wed 2026-11-04 15:09:38 CST`、`NRestarts=0`，与 PRE-04 相同 | PASS |
| V-02 | 线上代码版本（HEAD + mtime，不用 .pyc） | `HEAD_OK`（== b4fa3a3…）；`porcelain:[]`；`AT=Wed 2026-11-04 22:07:48 CST`；`files_checked=40 mtime_check_bad=0`（`git diff --name-only --diff-filter=AMR ANCHOR DEPLOY_COMMIT -- src/ib src/ibweb src/deploy/migrations` 共 40 个文件，mtime 均早于启动）；`MIG009_PRESENT` | PASS |
| V-03 | 启动日志与文件态 | `--since "2026-11-04 22:07:47"`：有 `{"outcome": "succeeded", "stage": "startup"}`；`bad_keyword_count=0`（含 path_not_configured_using_in_memory_default / ConfigError / Traceback / ModuleNotFoundError / ImportError / web_governance_unavailable / runtime_compile_failed / config_drift）。注：首次调用因含空格的参数经 ssh 拆词，`$1` 只拿到日期，窗口被放大到当日 00:00（多出 15:09 的旧启动行，同样无错误关键字）；加引号后重跑得上述结果（计划 Q2 对含空格值的补充，见遗留 3） | PASS |
| V-04 | 迁移 009 已应用（只读，ib-web 身份） | 代理未执行（计划指定 U）。间接佐证：ExecStartPre 成功、ib-web 起来且 `web_governance_unavailable` 零命中 | **待用户** |
| V-05 | 健康检查与外发声明基线一致 | 目标机本地 `/healthz` = 200；目标机本地 nginx `https://127.0.0.1/healthz` = 200（开发机到 192.168.31.133 为内网，不可达，`ext_healthz=000`，改在目标机本机经 nginx 验证外部入口）；`/healthz/deps` 顶层键 `['egress', 'embed', 'llm', 'qdrant']` = PRE-04 基线，`"egress_web" in d` = `False` | PASS |
| V-06 | 新接口已挂载且受鉴权 | 不带令牌 `GET /api/web-governance` → **401**（非 404/500） | PASS |
| V-07 | 日志无新增错误（自 PULL_TS `2026-11-04 22:07:11`） | `journalctl -u ib-web --since … -p warning` → `-- No entries --`；`-u ib-worker` → `-- No entries --`；Traceback/OperationalError 计数 ib-web 0、ib-worker 0 | PASS |
| V-08 | 前端已发布为新构建 | 目标机 index.html sha256 `930868f6…6a7d`，引用 `assets/index-UKe_bFLW.js`；目标机本机经 nginx（https）取首页同为 `assets/index-UKe_bFLW.js`；不同于旧值 `index-CwQd2QJ4.js`。开发机直连 192.168.31.133 不可达（同 V-05 说明） | PASS |
| V-09 | 本地状态未触碰；资源 | `git status --porcelain` 空；`src/frontend/node_modules`、`venv` 仍在；env 文件仅 `stat`：`600 ib-embed:ib-embed`、`600 ib-web:ib-web`、`600 ib-worker:ib-worker`；ib-web `MemoryCurrent=134537216`（≈128 MiB）/ `MemoryMax=1073741824`；`~/ib-webroot-pre-r28` 含 `assets index.html` | PASS |
| V-10 | 既有功能冒烟（浏览器：问答 + 配置页打开） | 浏览器操作，代理不可执行 | **待用户** |
| V-11 | Stage 1 人工验证 MV | 见下清单 | **待用户** |

## Stage 1 人工验证待用户

测试须用独立测试项目（PRE-08）；步骤与期望以 `e2e_test_report.md` 2.0.0「人工验证清单」原文为准；旧页面须硬刷新（Ctrl+F5）。

| 项 | 内容 | 状态 |
|---|---|---|
| V-04 | 迁移 009 只读核对（计划 V-04 的 `sudo -u ib-web … mode=ro` 脚本）：列 `id, max_calls_per_turn, max_fetch_bytes_per_turn, max_seconds_per_turn, updated_at, updated_by`；`rows: 0`；`documents: 2`（= PRE-05 备份时值）；`ls -l ledger.sqlite3*` 仍属 ib-web:ib | 待用户 |
| V-10 | 浏览器登录 → 现有项目问答一次（流式正常）、配置页可打开；无白屏 / 控制台报错 | 待用户 |
| MV-01 | 新建项目「启用顾问」 | 待用户 |
| MV-02 | 加入 / 移除顾问 | 待用户 |
| MV-03 | 顾问面板勾选 web_search / web_fetch、参数、非法域名（仅测试项目；产生含联网授权的配置版本，见 I-2） | 待用户 |
| MV-04 | admin 联网上限页与权限（需非 admin 账号） | 待用户 |
| MV-06 | 意图 / 指代评测集（真实 LLM；`[DATA_REQUIRED]` 评测集由用户提供，不得以合成集宣告验收） | 待用户 |
| MV-07 | 评测集确认（同上） | 待用户 |
| MV-12 | 全旅程：创建启用顾问项目 → 上传文档 → 提问（联网关闭，回答来自知识库与来源标注） | 待用户 |

Stage 2（OPT-A，需用户另行单独授权）与 Stage 3（OPT-B，本轮不启用）未执行；MV-15/16 破坏性分支推迟（维护窗口）。

## 回滚记录

无。无步骤失败，未执行任何 ROLLBACK。回滚入口（如 Stage 1 判定需回退）：ROLLBACK-000（用户先清除含 web_search/web_fetch 授权的项目配置）→ 001a（主会话 revert `b4fa3a3`，仅 src/tests/.github，保留 docs/.claude）→ 001b → 004 → 003；web root 紧急止血副本在目标机 `~/ib-webroot-pre-r28`（index.html sha256 `c9cad5aa…6f97306`）。迁移 009 留表无害，ROLLBACK-009 仅在需完全还原 schema 时由用户执行（备份：`ledger.sqlite3.pre-r28.bak`）。

## 当前系统状态

- 目标机 HEAD = `b4fa3a3df7fd39745363a52452779711b5979bec`，工作树干净；ib-web 22:07:48 重启，其余服务未重启；web root 为新构建；联网三键未设置（全关）；env 文件、unit、nginx、`/var/lib/intelligentbase`（除 009 新表与 PRE-05 备份）均未触碰。
- 目标机新增文件：`~/ib-webroot-pre-r28/`（旧 web root 副本，验收通过后由用户决定删除）；`/var/lib/intelligentbase/ledger/ledger.sqlite3.pre-r28.bak`（PRE-05）。

## 遗留问题

1. 最终状态 DEPLOYED_SUCCESSFULLY 仅覆盖代理可验项；V-04、V-10 与 Stage 1 MV（01/02/03/04/06/07/12）待用户。按计划口径，只要仍有未完成人工验证，整体交付至多 DELIVERED_WITH_ISSUES；若 Stage 1 任一项不通过，应改判 DEPLOYED_WITH_ISSUES 并由用户决定回滚或缺陷回流。
2. 开发机无 `~/.ssh/ib_prod_ed25519` 且内网不可达，全程经外网入口；因此计划 V-05 / V-08 的"开发机 curl 192.168.31.133"无法执行，改在目标机本机经 nginx（127.0.0.1:443）验证；nginx 的 `http://127.0.0.1/healthz`（80 端口）返回 404，疑为 80 端口仅做跳转/静态而非回环 healthz 路径，未影响判定（`https` 为 200），未深查。
3. 计划建议修订：(a) PRE-02 脚本前置 `export LC_ALL=C`；(b) Q2 的 `ibssh bash -s -- "$VAR"` 对含空格的值（RESTART_TS、PULL_TS）会被 ssh 拆词，须写成 `"'$VAR'"` 或改用无空格格式；(c) DEPLOY-004 的 `npm run build` 如需取输出尾部，应使用 `set -o pipefail`；(d) PRE-05 备份权限为 640。
4. `sudo -n -u ib-web …` 免口令范围宽于 SKILL.md §1/§4 记载（沿 0.2.0 遗留 5，本次部署未使用，仍建议用户核对 `/etc/sudoers.d/` 并更新 SKILL.md）。
5. PRE-00（CI 全绿 run 41787772135）由 PM 核验，本报告未独立复核。

## 附：预检记录（E2-001 / E2-002，沿用 0.2.0，摘要）

- PRE-03/04（E2-001）：磁盘可用约 66.7 GiB；内存 available 9338 MiB；node v22.22.1 / npm 9.2.0；venv lxml 6.1.3；五个单元 active；ib-web/ib-worker/ib-embed ActiveEnterTimestamp 均 `Wed 2026-11-04 15:09:38 CST`、NRestarts=0；ib-web MemoryCurrent=192880640；`/healthz/deps` 键集 `['egress','embed','llm','qdrant']`；web root index.html sha256 `c9cad5aabd869129b011bbd0171f23fe9872d9973fb9ac9bda2f7bdac6f97306`，引用 `assets/index-CwQd2QJ4.js`；`~/ib-webroot-pre-r28` 原不存在。
- PRE-05（E2-002，以 ib-web 身份经 `sudo -n -u ib-web`）：备份 `ledger.sqlite3.pre-r28.bak`（299008 字节，640 ib-web:ib），documents=2，`integrity: ok`。PRE-06：`definition_docs_scanned: 3 advisor_hits: 0`，find 无输出。PRE-07：`llm_key_rows=1`、`IB_LLM_API_KEY` 行 1、`IB_WEB_` 行 0、非 DeepSeek `IB_LLM_BASE_URL` 行 0。PRE-08：用户本轮确认（PM 陈述）。
