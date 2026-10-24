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
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：资料管理文件夹树增量（INCREMENTAL，R25）

> 基线：`.github/workflows/ci.yml`（GitHub Actions，单 job、10 阶段、fail-fast，画像 P7）。本文只描述本增量对 CI 的影响与实际修改。
> 本次**未连接任何环境、未执行任何部署命令、未 commit / push**（画像 P9）。唯一被修改的 CI 文件是 `.github/workflows/ci.yml`（PM 明确授权，只改"Schema / migration check"步骤与第 15 行基线注释）。

## 现状与影响

### 现有 CI

| 项 | 内容 |
|---|---|
| 文件 | `.github/workflows/ci.yml`，触发：push / PR 到 `main`、`workflow_dispatch` |
| 运行环境 | `ubuntu-24.04`，Python 3.12，Node 20，`timeout-minutes: 30` |
| 阶段 | 10 阶段：Source → Config(compileall) + Schema/迁移门 → Unit → Integration → E2E → Full+coverage → selfcheck → Version gate → Frontend build+test → Package(dist + HEAD artifact，保留 30 天) |
| 纪律 | 任一 step 失败即 abort（无 `continue-on-error`） |
| 部署 | **CI 不含 CD**：生产部署由 E2 按 `.claude/skills/ib-prod-deploy/SKILL.md` 手工/授权执行（画像 P7） |

### 本增量对 CI 的影响（逐项）

| 影响维度 | 结论 | 依据 |
|---|---|---|
| 新增依赖（Python / npm） | **无** | `git status` 中 `src/requirements*.txt`、`src/frontend/package.json`、`package-lock.json` 均未改动；tech_stack 无新依赖 |
| 新测试层 | **无**；新用例落在既有 `tests/unit`、`tests/integration`、`tests/e2e`（10 个 `*_r25.py` 文件）与 `frontend.smoke.test.js`，由既有 step 自动纳入 | implementation_plan / unit/integration/e2e 报告 |
| 新服务 / 新环境 / Docker | **无**；不新增 staging，不引入 Docker（画像 P8） | architecture_design 部署视图 |
| 新环境变量（CI 内） | **无需**；4 个新业务键（`IB_UPLOAD_BATCH_*`、`IB_LIBRARY_MAX_DEPTH`）有默认值，离线测试不依赖 | implementation_plan 开放问题 |
| 新迁移 | **有**：`src/deploy/migrations/007_folder_tree.sql`。现有 Schema 门只检查 003 → **需要修改**（见下） | module_design「数据迁移」；ci.yml 原 :74-92 |
| selfcheck | 已含 `folder_tree_migration_007`、`folder_tree_integrity`（共 54 项）；CI 阶段 7 自动执行，无需改 | selfcheck.py:4231、:4436-4437 |
| 版本门 / 硬门 | 不变（langchain-openai<0.3、禁 PyMuPDF、禁 Docker、Python 范围、bcrypt） | — |

### 实际修改（已落盘到 `.github/workflows/ci.yml`）

修改范围严格限于：① "Schema / migration check" 这一个 step（同 step 内追加 007 检查，step 名补注 `R25`）；② 第 15 行测试基线注释。其余行一字未动。

追加的 007 检查内容：

1. **单源**：`folder_tree_ddl_script()` 去空白后包含于 `007_folder_tree.sql`（与 003 同口径）。
2. **001~006 不被删改**：六个既有迁移文件必须存在（文件存在性；内容不变由 git 历史与评审保证）。
3. **语法 + 两次重放幂等**：因 007 快照不含 `documents` 的 `ALTER TABLE ADD COLUMN` 与 Python `name_key` 回填（007 头注释已声明），先经 `ensure_schema()` 建立前置形态，再 `executescript(007)` 两遍；断言 4 张新表、3 个唯一索引、`documents` 6 个新列齐备。
4. **老库升级形态**：仅 001 DDL 起步 → `ensure_schema()` 两遍 → 007 重放两遍，其表/索引/列集合须与新库形态一致。
5. 仅用标准库 + 仓库自带 `ib.ledger.schema`（不需要 runner 安装 `sqlite3` CLI）。

本地实测（venv `/root/.venvs/intelligentbase`，与 CI 同一离线依赖集，画像 P4 环境变量）：

| 场景 | 结果 |
|---|---|
| 将 step 的 `run` 抽出执行 | 退出码 0；输出 `PASS: 003_accounts.sql …` 与 `PASS: 007_folder_tree.sql syntax-ok / replay x2 idempotent / single-source / old-db upgrade` |
| 反例：把 007 副本中 `idx_folders_parent` 改名后指向该副本 | 退出码 1，`AssertionError: 007 snapshot != folder_tree_ddl_script()`（门有效） |
| `yaml.safe_load(ci.yml)` | 解析通过 |
| `python src/scripts/selfcheck.py`（checklists.txt 修改后） | 53/54，唯一失败 `core_framework_free: sitecustomize`（本机环境项，与基线一致） |

> 尚未在真实 GitHub Actions 上运行（子代理不 push）。**首次 push 后的 CI 运行是该 step 的最终验证**；若失败，按 abort-and-notify 处理，不得带着红灯部署（见 deployment_plan PRE-02）。

#### diff（`git diff .github/workflows/ci.yml`，节选全部改动）

```diff
@@ -12,7 +12,8 @@
 #   **不新增、不删除、不修改任何 step**，仅同步下方注释基线标签：
-#   * 测试基线：unit 95 / integration 129 / e2e 21 / full 245（0 skip/xfail）；前端冒烟 21。
+#   * 测试基线（R25 实测更新，PM 复跑 2026-10-24）：unit 314 / integration 225 / e2e 45 / full 605（0 skip/xfail）；前端冒烟 46。
+#     （REV-14 原数 95/129/21/245/21 已过时；下方各阶段注释中的旧基线数字未改，以此行为准。）
@@ -73,8 +74,9 @@
       # 与代码生成器（ib/ledger/schema.py::account_ddl_script()）单源一致。
-      # 对齐 checklists B20；只用标准库（runner 无需 sqlite3 CLI）。
-      - name: Schema / migration check (阶段2 R13)
+      # R25：同一步骤追加 007_folder_tree.sql（语法 / 两次重放 / 与 folder_tree_ddl_script() 单源 / 老库升级形态）。
+      # 对齐 checklists B20 / B28；只用标准库（runner 无需 sqlite3 CLI）。
+      - name: Schema / migration check (阶段2 R13 + R25)
@@ -89,6 +91,42 @@
           print("PASS: 003_accounts.sql syntax-ok / idempotent / single-source")
+
+          # R25（阶段2）：追加 007_folder_tree.sql —— 语法 + 两次重放幂等 + 与
+          # ib.ledger.schema.folder_tree_ddl_script() 去空白包含的单源比对。
+          # 007 快照不含 documents 的 ALTER ADD COLUMN 与 Python name_key 回填（头注释已声明），
+          # 故先经 ensure_schema() 得到「007 的前置形态」，再重放 007 两次。
+          from ib.ledger.schema import DDL_STATEMENTS, ensure_schema, folder_tree_ddl_script  # noqa: E402
+          sql7 = pathlib.Path("src/deploy/migrations/007_folder_tree.sql").read_text(encoding="utf-8")
+          assert norm(folder_tree_ddl_script()) in norm(sql7), "007 snapshot != folder_tree_ddl_script()"
+          for old in ("001_ledger_init", "002_chunk_image", "003_accounts", "004_config_audit",
+                      "005_projects", "006_llm_key"):
+              assert pathlib.Path(f"src/deploy/migrations/{old}.sql").is_file(), f"{old}.sql missing (001-006 must stay)"
+          new_tables = {"folders", "upload_batches", "upload_batch_items", "doc_purge_queue"}
+          new_cols = {"folder_id", "name_key", "uploaded_at", "content_updated_at", "indexed_at", "revision_of"}
+          new_idx = {"uq_folders_name", "uq_documents_name", "uq_documents_revision"}
+          def shape(c):
+              t = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
+              i = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index'")}
+              k = {r[1] for r in c.execute("PRAGMA table_info(documents)")}
+              return t, i, k
+          # (a) 新库形态：ensure_schema 一遍 -> 007 重放两遍
+          c7 = sqlite3.connect(":memory:", isolation_level=None)
+          ensure_schema(c7)
+          c7.executescript(sql7)   # replay 1
+          c7.executescript(sql7)   # replay 2 (idempotent)
+          t, i, k = shape(c7)
+          assert new_tables <= t and new_idx <= i and new_cols <= k, (new_tables - t, new_idx - i, new_cols - k)
+          # (b) 老库形态（仅 001 DDL）：ensure_schema 两遍 -> 007 重放两遍，形态与 (a) 一致
+          c0 = sqlite3.connect(":memory:", isolation_level=None)
+          for st in DDL_STATEMENTS:
+              c0.execute(st)
+          ensure_schema(c0)
+          ensure_schema(c0)
+          c0.executescript(sql7)
+          c0.executescript(sql7)
+          assert shape(c0) == shape(c7), "old-db upgrade shape != fresh shape"
+          print("PASS: 007_folder_tree.sql syntax-ok / replay x2 idempotent / single-source / old-db upgrade")
           PY
```

### 未改动项与遗留（MINOR，不阻塞）

- 阶段 3~6 的注释里仍有 REV-13/14 旧基线数字（94/98/102/106 行），本次按授权只更新第 15 行；以第 15 行与 PM 复跑数为准（605 passed / 前端 46/46 / selfcheck 53/54）。
- 无 `paths-ignore`：仅改文档/agent 配置的提交也会跑全流水线（通用经验建议排除）。本增量不改触发策略，列为后续可选优化。
- `src/deploy/env.example` / `ib-worker.env.example` 未登记 4 个新键（implementation_plan 已声明交 devops）。本次授权范围不含这两个文件，且默认值无需 env 改动，**不改**；如 PM 希望登记，需另行授权（见 deployment_plan「下游产物同步核对」）。

## 流水线概览

```
[Source] → [Config: compileall + Schema/迁移门(003+007)] → [Unit] → [Integration] → [E2E] → [Full+cov]
        → [selfcheck] → [Version gate] → [Frontend build+test] → [Package: dist+HEAD artifact]
   ── CI 到此为止（无 CD）──
   → [Deploy: production, recreate, 授权后手工/E2] → [部署后冒烟 V-xx] → [UI 人工复核]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR→main；`workflow_dispatch` | `actions/checkout@v4` | checkout 成功 | abort-and-notify（Actions 通知） |
| PIPE-02 | Config + Schema 门 | 同上 | `python -m compileall -q src`；内联脚本（003 + **007 新增**） | 退出码 0；输出两行 `PASS:` | abort-and-notify；禁止带红灯部署 |
| PIPE-03 | Unit | 同上 | `python -m pytest tests/unit -q` | 0 failed（当前 314 passed） | abort-and-notify |
| PIPE-04 | Integration | 同上 | `python -m pytest tests/integration -q` | 0 failed（当前 225 passed） | abort-and-notify |
| PIPE-05 | E2E（离线 Django 客户端旅程） | 同上 | `python -m pytest tests/e2e -q` | 0 failed（当前 45 passed） | abort-and-notify |
| PIPE-06 | Full + coverage | 同上 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 0 failed（当前 605 passed）；覆盖率仅记录不设门 | abort-and-notify |
| PIPE-07 | selfcheck | 同上 | `python src/scripts/selfcheck.py` | 退出码 0。**CI runner 上期望 54/54**；本机因 `sitecustomize` 为 53/54（`core_framework_free`，环境项） | abort-and-notify |
| PIPE-08 | Version gate | 同上 | 见 ci.yml 阶段 8（bcrypt、langchain-*、禁 fitz、禁 Docker、Python 范围） | 全部 `PASS` | abort-and-notify |
| PIPE-09 | Frontend build + test | 同上 | `npm ci && npm run build && npm test`（`src/frontend`） | vue-tsc 零错、vite build 成功、46/46 | abort-and-notify |
| PIPE-10 | Package | 前序全部成功 | 记录 `HEAD`；`upload-artifact`（dist + HEAD，30 天） | artifact 上传成功 | abort-and-notify |
| —（CD） | Deploy / 部署后冒烟 / E2E | **不在 CI 内**；仅在用户授权 E2（`PRODUCTION_DEPLOY_CONFIRM=true`）后由 devops 按 deployment_plan 执行 | 见 deployment_plan | 见其 V-xx | 失败：从失败步骤按逆序执行 ROLLBACK；回滚本身失败则停止并报告 |

失败处理只使用 abort-and-notify；无"跳过失败继续部署"。

## 环境矩阵

只列画像 P7 中存在的环境；staging 不存在，不设计晋升。

| 配置项 | dev/local | CI | production |
|---|---|---|---|
| 实例数 | 本机进程 | 单 job runner | 单机：ib-web ×1、ib-worker ×1（**禁多实例**，画像 P8）、ib-embed ×1、qdrant ×1、nginx |
| 资源 | 开发机 | ubuntu-24.04，30 分钟超时 | i7-3770S 4C/8T、11 GiB；各单元 MemoryMax 见 systemd unit（ib-web 1024M / ib-worker 2048M / ib-embed 2560M） |
| 外部依赖 | 无（`IB_OFFLINE_MODE=1`） | 无（离线替身，不连 Qdrant/DeepSeek/ib-embed） | Qdrant 127.0.0.1:6333、ib-embed 127.0.0.1:8100、DeepSeek（外发，已声明） |
| 配置来源 | `IB_CONFIG_SOURCE=dict`（conftest setdefault） | job 级 `env:`（ci.yml:40-46） | `/etc/intelligentbase/*.env`（0600，用户维护，不读取回显） |
| 部署需用户确认 | 否 | 否 | **是**（`PRODUCTION_DEPLOY_CONFIRM=true` 由 PM 依据用户本轮消息写入） |
| 部署策略 | — | — | recreate（单机 systemd 重启；画像 P7 唯一允许） |

## 制品管理

- **存储位置**：CI 将 `src/frontend/dist/` 与 `HEAD` 作为 Actions artifact 上传，保留 30 天（`ib-${{ github.sha }}-${{ github.run_id }}`）。
- **命名**：含提交号与 run id，可追溯到待部署提交。
- **晋升条件**：生产**不消费该制品**——前端在目标机 `npm run build` 本地构建后拷贝 web root，后端 `git pull origin main`。因此"晋升条件"落在部署前置检查：待部署提交的 CI 运行全绿（deployment_plan PRE-02），目标机 HEAD 精确等于该提交（V-06）。
- **目标机本地构建的风险**（画像 P7 既定，写明并接受）：① 目标机构建结果与 CI 的 dist 不是同一份产物，需靠同一提交 + `package-lock.json`（未变）保证复现；② 构建耗内存/CPU，部署窗口内与 ib-web 竞争资源（11 GiB 内存，影响有限）；③ 构建失败即无新前端（旧前端仍服务，无停机），因此 DEPLOY-004 的发布 `rm` 必须在构建成功后才执行（`&&` 串联）。
