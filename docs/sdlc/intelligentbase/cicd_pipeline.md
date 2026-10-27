<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-27T16:30:27+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>tech_stack.md</file>
    <file>implementation_plan.md</file>
    <file>e2e_test_report.md</file>
    <file>phase_status.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：项目 agent 编排可视化配置（INCREMENTAL，REV-26）

> 基线：`.github/workflows/ci.yml`（GitHub Actions，单 job、10 阶段、fail-fast，画像 P7）。本文只描述本增量对 CI 的影响与实际修改。
> 本次**未连接任何环境、未执行任何部署命令、未 commit / push**（画像 P9；用户 CL-008：现在暂时不部署，E2 NOT_AUTHORIZED）。唯一被修改的 CI 文件是 `.github/workflows/ci.yml`（PM 在 invocation 中明确要求：仅迁移检查段加 008）。
> 上一轮参考：`archive/rev25/cicd_pipeline.md`（只读）。

## 现状与影响

### 现有 CI

| 项 | 内容 |
|---|---|
| 文件 | `.github/workflows/ci.yml`，触发：push / PR 到 `main`、`workflow_dispatch` |
| 运行环境 | `ubuntu-24.04`，Python 3.12，Node 20，`timeout-minutes: 30` |
| 阶段 | 10 阶段：Source → Config(compileall) + Schema/迁移门 → Unit → Integration → E2E → Full+coverage → selfcheck → Version gate → Frontend build+test → Package(dist + HEAD artifact，保留 30 天) |
| 纪律 | 任一 step 失败即 abort（无 `continue-on-error`） |
| 部署 | **CI 不含 CD**：生产部署由 E2 按 `.claude/skills/ib-prod-deploy/SKILL.md` 授权执行（画像 P7） |

### 本增量对 CI 的影响（逐项）

| 影响维度 | 结论 | 依据 |
|---|---|---|
| 新增依赖（Python / npm） | **无**。`langgraph>=0.2,<2.0` 已在 `src/requirements-offline.txt`（CI 已装），`test_langgraph_contract_r26.py` 的 `langgraph` 导入可满足 | `git status` 中 `src/requirements*.txt`、`package.json`、`package-lock.json` 无改动；tech_stack.md 无新依赖 |
| 新测试层 | **无**。新用例 `tests/unit/*_r26.py`（12 个）、`tests/integration/*_r26.py`（10 个）、`tests/e2e/test_config_journeys{,2}_r26.py`（2 个）落在既有目录，由阶段 3/4/5/6 自动纳入；前端追加断言在 `frontend.smoke.test.js`，由阶段 9 的 `npm test` 纳入 | `ls tests/*/*_r26.py` |
| 新测试支撑模块 | `tests/config_r26_support.py`（位于 `tests/` 根，与既有 `folder_r25_support.py` 同做法）以 `from config_r26_support import …` 导入；`tests/conftest.py` 在 `tests/` 根，pytest rootdir-conftest 机制把 `tests/` 插入 `sys.path`，**无论单跑 `tests/unit` 还是 `tests`** 均可导入。本机实证见下「本地等价校验」③ | 同上 |
| tests/agents 是否在 CI 运行 | **仅阶段 6「Full suite + coverage」（`pytest tests`）会运行**（15 例，SDLC 套件契约）；阶段 3/4/5 只跑 unit / integration / e2e，不含 agents。本次不改，如实记录 | ci.yml 阶段 3~6 的命令 |
| 新服务 / 新环境 / Docker | **无**；不新增 staging，不引入 Docker（画像 P8） | architecture_design 部署视图 |
| 新环境变量（CI 内） | **无需**。`env.example` 新增 4 个**可选**键名（`IB_CONFIG_HEAD_CHECK_INTERVAL_S`、`IB_GRAPH_RUNTIME`、`IB_LLM_CLIENT_CACHE_MAX`、`IB_DOC_SCOPE_MAX_IDS`），缺省值即可运行；离线测试不依赖 | `src/deploy/env.example` diff |
| 新迁移 | **有**：`src/deploy/migrations/008_config_versions.sql`。现有 Schema 门只覆盖 003 与 007 → **需要修改**（见下）；selfcheck 已含 `config_versions_schema_single_source`（selfcheck.py:4372），CI 阶段 7 自动执行 | module_design「数据迁移」 |
| selfcheck | 阶段 7 自动执行；PM 复跑 57/58，唯一失败 `core_framework_free` 为本机 venv `sitecustomize` 既有失败（HEAD 干净导出同样失败），**不是 008 引入**；GitHub 干净 runner 上预期不受该本机因素影响 `[INFERRED]`，首次真实 CI 的结果为准 | phase_status GR-C-001 / quality_thresholds |
| 版本门 / 硬门 | 不变（langchain-openai<0.3、禁 PyMuPDF、禁 Docker、Python 范围、bcrypt） | — |
| 前端 | 阶段 9 命令不变（`npm ci && npm run build && npm test`）；PM 复跑 build 成功、npm test 77/77/0 | — |
| `hot_effect_probe.py` | **不进 CI**：它是目标机上线后由用户执行的只读 CLI（IFC-R26-190，需令牌与运行中的 ib-web），离线 CI 无对象可探；其模块可被 `compileall -q src`（阶段 2）语法检查，已覆盖 | 脚本文件头注释 |

### 实际修改（已落盘到 `.github/workflows/ci.yml`）

修改范围严格限于「Schema / migration check」这一个 step（同 step 内追加 008 检查；step 名补注 `+ R26`；注释补 3 行）。其余 step、job、触发器、env、第 1~19 行基线注释**一字未动**（`git diff` 仅此 step 变化）。

追加的 008 检查内容（与 001~007 同口径）：

1. **单源**：`ib.ledger.schema.config_versions_ddl_script()` 去空白后包含于 `008_config_versions.sql`。
2. **001~007 不被删改**：补查 `007_folder_tree.sql` 存在（001~006 由既有循环查；内容不变由 git 历史与评审保证）。
3. **回滚说明在位且无可执行 DROP**：头注释（第一个 `CREATE TABLE` 之前）含 `MANUAL_ROLLBACK_REQUIRED`；逐行剥离 `--` 注释后不得出现 `DROP`（与 selfcheck 同口径，保证回滚 DROP 只在注释里、由用户执行）。
4. **语法 + 两次重放幂等（新库形态）**：008 快照不含 `users.config_level` 与 `config_audit` 三列的 `ALTER TABLE ADD COLUMN`（008 头注释已声明，由 `ensure_schema()` 探测后补列），故先经 `ensure_schema()` 再 `executescript(008)` 两遍；`missing_config_version_columns()` 须为空，四张新表齐备。
5. **老库升级形态**：以 001 + 003 + 004 的 DDL 建库并插入一个 `ops` 账号 → `ensure_schema()` 两遍 → 重放 008 → 补列齐备，**存量 ops 账号 `config_level == 'manage'`**（A01：与上线前"能写配置"等价）。
6. 仅用标准库 + 仓库自带 `ib.ledger.schema`（runner 无需 sqlite3 CLI）；成功输出 `PASS: 008_config_versions.sql …`。

### 本地等价校验（不能运行 GitHub Actions，如实说明；用 `/root/.venvs/intelligentbase/bin/python`，Python 3.12、SQLite 3.45.1，与 CI 同一离线依赖集）

| # | 校验 | 命令 / 做法 | 结果 |
|---|---|---|---|
| ① | 抽取 ci.yml 中该 step 的 `run:` 脚本（`yaml.safe_load` 取出，原样不改写）并执行 | `PYTHONUTF8=1 IB_OFFLINE_MODE=1 /root/.venvs/intelligentbase/bin/python <抽取出的脚本>`（工作目录 = 仓库根，与 Actions 一致） | 退出码 0；依次输出 `PASS: 003_accounts.sql …` / `PASS: 007_folder_tree.sql …` / `PASS: 008_config_versions.sql syntax-ok / replay x2 idempotent / single-source / old-db upgrade` |
| ② | 反例（门是否真能拦） | 复制 `src/` 到 scratchpad，把副本 008 中 `IF NOT EXISTS config_head` 改成 `config_head`，在副本根执行同一脚本 | `AssertionError: 008 snapshot != config_versions_ddl_script()`，非零退出 |
| ③ | pytest 能收集新增 `_r26` 文件及支撑模块 | `PYTHONPATH=src /root/.venvs/intelligentbase/bin/python -m pytest tests --collect-only -q` | 908 tests collected，无导入错误；其中 `*_r26.py` 用例 309 条（unit 195 / integration 108 / e2e 6；tests/agents 无 `_r26` 文件）；`from config_r26_support import …` 在三层均可解析 |
| ④ | YAML 语法 | `yaml.safe_load('.github/workflows/ci.yml')` | 解析成功，step 名称为 `Schema / migration check (阶段2 R13 + R25 + R26)` |
| ⑤ | 全量测试 / selfcheck | **本组未重跑**（E1 不要求）；引用 PM 复跑结果（quality_thresholds）：tests/unit 509 / integration 333 / e2e 51 / agents 15 passed；npm test 77/77/0；npm run build 成功；selfcheck 57/58（`core_framework_free` 本机既有失败） | 引用，非本组实测 |

**未能验证的部分**：GitHub Actions 的 `ubuntu-24.04` runner、`actions/setup-python@v5` 缓存、`run: |` 对 heredoc 缩进的剥离只能在首次 push 后由真实 CI 验证（YAML 块标量会统一去除缩进，本机等价脚本是按解析后的 `run` 文本执行的，因此缩进风险已被 ①④ 覆盖）。

## 流水线概览

```
[Source] → [Config: compileall + Schema/迁移门(003/007/008)] → [Unit] → [Integration] → [E2E]
        → [Full+coverage(含 tests/agents)] → [Selfcheck] → [Version gate] → [Frontend build+test] → [Package artifact]
        ⇢（CI 之外，E2 授权后）[Deploy production: recreate] → [部署后验证] → [用户人工浏览器验收]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 `main`；`workflow_dispatch`（供部署前复跑） | `actions/checkout@v4` | 检出成功 | abort-and-notify（Actions 失败通知） |
| PIPE-02 | Config + Schema 迁移门 | PIPE-01 成功 | `python -m compileall -q src`；内联迁移检查脚本（003 / 007 / **008**） | 退出码 0；三行 `PASS:` | abort-and-notify；不得继续后续阶段 |
| PIPE-03 | Unit | PIPE-02 成功 | `python -m pytest tests/unit -q` | 退出码 0；基线 509 passed（PM 复跑，REV-26） | abort-and-notify |
| PIPE-04 | Integration | PIPE-03 成功 | `python -m pytest tests/integration -q` | 退出码 0；基线 333 passed | abort-and-notify |
| PIPE-05 | E2E | PIPE-04 成功 | `python -m pytest tests/e2e -q` | 退出码 0；基线 51 passed | abort-and-notify |
| PIPE-06 | Full suite + coverage | PIPE-05 成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 退出码 0；含 `tests/agents` 15 例；覆盖率仅记录不设门（画像 P5） | abort-and-notify |
| PIPE-07 | Offline selfcheck | PIPE-06 成功 | `python src/scripts/selfcheck.py` | 退出码 0（任一 FAIL 非零） | abort-and-notify。**注**：本机 `core_framework_free` 既有失败（57/58）若在 CI 复现，需 PM 判定是否环境项；不得靠跳过绕过 |
| PIPE-08 | Version gate | PIPE-07 成功 | ci.yml 阶段 8 内联命令 | bcrypt、langchain-core、langchain-openai pin、无 PyMuPDF、无 Dockerfile、Python 范围 全 PASS | abort-and-notify |
| PIPE-09 | Frontend build + test | PIPE-08 成功 | `npm ci && npm run build && npm test`（`src/frontend`） | vue-tsc 零错、vite build 成功、node:test 全绿（基线 77/77/0） | abort-and-notify |
| PIPE-10 | Package artifact | PIPE-09 成功 | `git rev-parse HEAD > HEAD`；`actions/upload-artifact@v4` | artifact `ib-<sha>-<run_id>` 上传，保留 30 天 | abort-and-notify |

CD（不在 CI 内，沿用画像 P7）：部署由 E2 经 ssh 到 production 执行（`git pull --ff-only` + `sudo -n systemctl restart`），**失败处理只有回滚（见 deployment_plan.md）或停止，禁止"跳过失败继续部署"**。部署前置：待部署提交的 CI 全绿。

## 环境矩阵

| 配置项 | dev/local | CI | production |
|---|---|---|---|
| 存在 | 是 | 是 | 是（单台物理机；无 staging，画像 P7） |
| 实例数 | 离线测试进程 | 1 个 runner | ib-web ×1、ib-worker ×1（禁多实例，画像 P8）、ib-embed ×1、qdrant ×1 |
| 资源 | 开发机 | ubuntu-24.04，30 min 超时 | i7-3770S 4C/8T、11 GiB、CPU-only（SKILL.md §1） |
| 外部依赖 | 无（离线，`IB_OFFLINE_MODE=1`） | 无（离线替身，不连 DeepSeek / Qdrant / ib-embed） | Qdrant、ib-embed、云端 DeepSeek（Builder 与 LLM 路径） |
| 配置来源 | `tests/conftest.py` setdefault | ci.yml job 级 `env` | `/etc/intelligentbase/*.env`（0600，只由用户读写，不回显） |
| 部署需用户确认 | 否 | 否 | **是**（`PRODUCTION_DEPLOY_CONFIRM=true` + 环境名） |

## 制品管理

- **CI 制品**：frontend `dist/` + `HEAD` 作为 Actions artifact，命名 `ib-${{ github.sha }}-${{ github.run_id }}`（含提交号），保留 30 天；仅供追溯。
- **生产不使用该制品**：目标机 `git pull` 后**本地构建**前端（`npm run build`）并拷贝到 web root。风险：目标机与 CI 的构建环境（node 22 / npm 9 vs Node 20）不同，构建结果可能与 CI 的 dist 不逐字一致；缓解：构建失败时 `&&` 链在替换 web root 之前中断（旧前端仍可用），并保留部署前 web root 副本供紧急止血（见 deployment_plan DEPLOY-004）。
- **晋升条件**：待部署提交（`DEPLOY_COMMIT`）已在 `origin/main`，其 CI 运行全部成功；无 staging，无环境间晋升。
