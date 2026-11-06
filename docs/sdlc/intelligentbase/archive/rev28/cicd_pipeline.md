<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-04T14:40:50+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/tech_stack.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

> 修订 1.1.0（2026-11-04，REWORK_AUTHORIZED，仅更新测试基线）：pytest 基线 1355 → 1358 passed；流水线阶段与命令未变，ci.yml 未改。


# CI/CD 流水线：REV-28 平台级内置「顾问 agent」+ 联网（INCREMENTAL）

> REV-27 已批准版本归档于 `archive/rev27/cicd_pipeline.md`（只读）；本文按 REV-28 整体重写，沿用其阶段结构。
> 本组**未连接任何环境、未 ssh、未部署、未 commit / push**（画像 P9）。**唯一改动的 CI 文件：`.github/workflows/ci.yml`**（PM 明确要求，module_design MOD-R28-16 / CR-006；改动摘要见下）。

## 现状与影响

### 现有 CI

| 项 | 内容 |
|---|---|
| 文件 | `.github/workflows/ci.yml`，触发：push / PR 到 `main`、`workflow_dispatch` |
| 运行环境 | `ubuntu-24.04`，Python 3.12，Node 22，`timeout-minutes: 30` |
| 阶段 | 10 阶段、单 job、fail-fast：Source → Config(compileall)+Schema 门(003/007/008，**本轮 +009**) → Unit → Integration → E2E → Full+coverage → selfcheck → Version gate → Frontend build+test → Package artifact |
| 部署 | **CI 不含 CD**：生产部署由 E2 按 `.claude/skills/ib-prod-deploy/SKILL.md` 授权执行（画像 P7） |

### 本增量对 CI 的影响（逐项核对）

当前工作区**未提交**（HEAD `8d6fd4b`；`git diff --name-only` 下 `src/` 已修改 33 个文件、`src tests` 未跟踪新文件 38 个），**CI 尚未跑过本轮代码**。

| 影响维度 | 结论 | 依据 |
|---|---|---|
| 新迁移 | **有**：`009_web_governance.sql`（新增单表 `web_governance`）→ Schema 门追加 009 检查（**已改 ci.yml**） | module_design「数据迁移」、MOD-R28-16 |
| 新依赖 | Python：`lxml>=5.0,<7.0` 已显式写入 `src/requirements.txt` 与 `src/requirements-offline.txt`（原为 python-docx 的间接依赖）；CI 的 `pip install -r src/requirements-offline.txt` 自动覆盖，**安装步骤无需改**。npm：无（`package.json` / `package-lock.json` 未改） | `git diff src/requirements*.txt`（各 +1 行） |
| 新测试层 | **无**。新测试落在既有层：`tests/unit/*r28*`、`tests/integration/*r28*`（含 3 个 golden JSON）、`tests/e2e/test_advisor_*_r28.py`、`src/frontend/tests/advisor_r28.test.js`；`tests/*_r28_*support.py` 为共用辅助模块（非测试文件，不被收集）；被既有 step 自动纳入 | pytest 目录收集 / `node --test` 默认 `**/*.test.js` |
| selfcheck | 新增用例（本地 68/69，唯一失败 `core_framework_free` 为开发机 `sitecustomize` 环境性既有；GitHub runner 上应为 69/69，**首次 push 后以 CI 为准**）。PIPE-07 范围扩大但 step 不改 | implementation_plan 自验证 |
| 新服务 / 新环境 / 新环境变量 | CI 侧**无**：联网三键（`IB_WEB_SEARCH_PROVIDER`、`IB_WEB_FETCH_ENABLED`、`IB_WEB_GOVERNANCE_BACKEND`）缺省 = 关闭，CI 保持离线（`IB_OFFLINE_MODE=1`，job 级 env 不加键）；测试只用替身（画像 P11-3：**自动化禁止调用真实 DeepSeek 端点**）。不新增 staging，不引入 Docker（画像 P8） | module_design「受影响的运行单元」 |
| Node / Python 版本 | 无需调整 | — |
| 版本门 / 硬门 | 不改（`lxml` 不在任何版本门内；新增依赖不含 fitz / 容器文件） | module_design「对 selfcheck / CI 门的影响」 |
| **结论** | **`ci.yml` 仅在「Schema / migration check」步骤追加 009 检查**（下节 diff 摘要）；其他阶段零改动 | PM 要求 |

### `ci.yml` 改动摘要（diff stat：`+42 / -1`，单文件）

位置：`jobs.ci.steps[name="Schema / migration check …"]`（阶段 2）的内联 `python - <<'PY'` 脚本；风格与 006 / 008 检查一致（只用标准库 + `ib.ledger.schema`，runner 无需 sqlite3 CLI）。

| # | 改动 | 内容 |
|---|---|---|
| 1 | 文件头注释 | 追加「REV-28 增量」说明块（PM 要求来源；lxml 声明不改安装步骤；基线数字） |
| 2 | 步骤 `name` | `… (阶段2 R13 + R25 + R26)` → `… (阶段2 R13 + R25 + R26 + R28)`（无其他文件引用此名） |
| 3 | 步骤注释 | 追加 R28 说明 3 行 |
| 4 | 脚本末尾（008 检查之后、`PY` 之前）追加 009 检查块 | (a) `norm(S.web_governance_ddl_script()) in norm(sql9)` —— 与 schema 生成器单源一致；(b) 001~008 迁移文件仍在；(c) 头注释（首个 `CREATE TABLE` 之前）含 `MANUAL_ROLLBACK_REQUIRED` 且无可执行 `DROP`；(d) 新库 `ensure_schema` 后重放 009 两遍幂等，`missing_web_governance_columns == {}`；(e) 单行 `CHECK (id=1)` 与范围 CHECK 生效（`id=2`、`max_calls=0` 被拒）；(f) 老库形态（仅 001 DDL）`ensure_schema` 两遍补齐；成功打印 `PASS: 009_web_governance.sql …` |
| — | **未改** | 依赖安装步骤、阶段 3~10、版本门（bcrypt / langchain-core / langchain-openai pin / 禁 PyMuPDF / 禁 Docker / Python 范围）、触发条件、权限、artifact |

**本组自验证（开发机、未提交工作区、未联网）**：用 `yaml.safe_load` 抽出该 step 的 `run`，在仓库根原样执行 → 4 行 `PASS:`（003 / 007 / 008 / 009）、退出码 0。对仓库副本做反例变异，均使该步骤失败：① 删 009 中全部 `IF NOT EXISTS` → `009 snapshot != web_governance_ddl_script()`；② 改 `CHECK … BETWEEN 1 AND 20` 为 `1 AND 21` → 同上（快照与生成器漂移）；③ 末尾追加 `DROP TABLE web_governance;` → `009 contains an executable DROP`。（`pytest` / 前端 build 未由本组运行：开发机缺依赖，数字取 PM 复跑。）

### 新测试在 CI 的落点

| 范围 | 发现机制 | 运行阶段 | 基线（PM 复跑，GROUP_D 门控后，未提交工作区） |
|---|---|---|---|
| 后端 unit / integration / e2e 的 `*r28*` 文件（含 `FakeDeepSeekTransport` 替身用例、SSRF / 地址防护拒绝用例） | pytest 目录收集；基名全局唯一（画像 P3：无 `__init__.py`，基名不得冲突——由 PM 门控核对） | PIPE-03 / 04 / 05，并被 PIPE-06 重复覆盖 | `pytest tests` **1358 passed** |
| `src/frontend/tests/advisor_r28.test.js` 及既有前端用例 | `npm test` = `node --test` | PIPE-09（先 `npm run build` 后 `npm test`） | 前端 build rc=0、**160/160** |
| selfcheck 新用例（`web_egress_single_exit`、`web_ssrf_rejects`、`web_governance_schema_single_source`、`advisor_*`、`search_*`、`deepseek_*`、`web_key_reuse_no_new_credential` 等） | `python src/scripts/selfcheck.py` | PIPE-07 | 68/69（`core_framework_free` 环境性既有） |

### 部署提交的 CI 状态（E2 前置条件）

本轮代码**未提交 / 未 push，CI 尚未运行**。把「**push 后 CI 在待部署提交上全绿**（`completed / success`，10 阶段含 009 迁移门与 selfcheck）」列为 **E2 的前置条件**（deployment_plan PRE-00）；红灯或仍在运行不得部署。`gh` 未在画像 P4 登记 `[TOOL_UNREGISTERED]`，仅取证便利，GitHub Actions 网页核对等价（本机 `gh` 路径存在，登录态本组未验证）。

## 流水线概览

```
[Source] → [Config: compileall + Schema/迁移门(003/007/008/009)] → [Unit] → [Integration] → [E2E]
        → [Full+coverage(含 tests/agents)] → [Selfcheck] → [Version gate] → [Frontend build+test] → [Package artifact]
        ⇢（CI 之外，E2 授权后）[Deploy production: recreate — pull → 依赖/导入核对 → 重启 ib-web(迁移 009) → 前端发布] → [部署后验证] → [人工验证 MV-01~16 分阶段]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 `main`；`workflow_dispatch` | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | Config + Schema 迁移门 | PIPE-01 成功 | `python -m compileall -q src`；内联迁移检查（003 / 007 / 008 / **009**） | 退出码 0；**四**行 `PASS:` | abort-and-notify |
| PIPE-03 | Unit | PIPE-02 成功 | `python -m pytest tests/unit -q` | 退出码 0（零新增失败；新用例全过） | abort-and-notify |
| PIPE-04 | Integration | PIPE-03 成功 | `python -m pytest tests/integration -q` | 退出码 0 | abort-and-notify |
| PIPE-05 | E2E | PIPE-04 成功 | `python -m pytest tests/e2e -q` | 退出码 0 | abort-and-notify |
| PIPE-06 | Full suite + coverage | PIPE-05 成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 退出码 0；PM 复跑基线 1358 passed；覆盖率仅记录不设门（画像 P5） | abort-and-notify |
| PIPE-07 | Offline selfcheck | PIPE-06 成功 | `python src/scripts/selfcheck.py` | 退出码 0（任一 FAIL 非零）；预期 runner 上 69/69 | abort-and-notify；不得跳过 |
| PIPE-08 | Version gate | PIPE-07 成功 | ci.yml 阶段 8 内联命令（本轮未改） | bcrypt、langchain-core、langchain-openai pin、无 PyMuPDF、无 Dockerfile、Python 范围全 PASS | abort-and-notify |
| PIPE-09 | Frontend build + test | PIPE-08 成功 | `npm ci && npm run build && npm test`（`src/frontend`，Node 22） | vue-tsc 零错、vite build 成功、node:test 全过（基线 160/160） | abort-and-notify |
| PIPE-10 | Package artifact | PIPE-09 成功 | `git rev-parse HEAD > HEAD`；`actions/upload-artifact@v4` | artifact `ib-<sha>-<run_id>` 上传，保留 30 天 | abort-and-notify |

失败处理仅 abort-and-notify（fail-fast，无 `continue-on-error`），**禁止"跳过失败继续部署"**。CD 不在 CI 内：部署经 E2 ssh 到 production（`git pull --ff-only` + 目标机依赖核对 + 重启 ib-web + 前端目标机构建发布），部署前置 = 待部署提交的 CI 全绿。

## 环境矩阵

| 配置项 | dev/local | CI | production |
|---|---|---|---|
| 存在 | 是 | 是 | 是（单台物理机；**无 staging**，画像 P7） |
| 实例数 | 离线测试进程 | 1 个 runner | ib-web ×1、ib-worker ×1（禁多实例，画像 P8）、ib-embed ×1、qdrant ×1。**REV-28 默认只重启 ib-web**（module_design「受影响的运行单元」）；ib-worker / ib-embed 为条件步骤 |
| 资源 | 开发机 | ubuntu-24.04，30 min 超时 | i7-3770S 4C/8T、11 GiB、CPU-only；ib-web `MemoryMax=1024M`（联网模块与 `lxml` 为进程内库，部署后记录 `MemoryCurrent` 观察） |
| 外部依赖 | 无（离线） | 无（离线替身；**禁止真实 DeepSeek 调用**） | Qdrant、ib-embed、云端 DeepSeek（LLM，既有）；**新增**：DeepSeek Search（`api.deepseek.com`，与 LLM 同主机，仅 `IB_WEB_SEARCH_PROVIDER=deepseek` 时出网）；本地网页抓取（仅 `IB_WEB_FETCH_ENABLED=1` 时出网，目标为任意公网主机，出站 ACL 由用户配置） |
| 配置来源 | `tests/conftest.py` setdefault | ci.yml job 级 `env`（本轮不加键） | `/etc/intelligentbase/*.env`（0600，只由用户读写，不回显）；联网三键**缺省即关闭**，首发不改 env；凭据**不新增**（搜索复用 LLM 的 DeepSeek Key：台账 `llm_key` / 兼容回退 `IB_LLM_API_KEY`） |
| 部署需用户确认 | 否 | 否 | **是**（`PRODUCTION_DEPLOY_CONFIRM=true` + 环境名 `production`） |

## 制品管理

- **CI 制品**：frontend `dist/` + `HEAD` 作为 Actions artifact，命名 `ib-${{ github.sha }}-${{ github.run_id }}`（含提交号），保留 30 天；仅供追溯。
- **生产不使用该制品**：目标机 `git pull --ff-only` 后**本地构建**前端（`npm run build`）并拷贝到 web root；Python 无构建产物（源码直跑 venv）。风险：目标机（node 22 / npm 9）与 CI 的 npm 版本不同，产物 hash 可能与 CI dist 不一致；缓解：`&&` 链使构建失败发生在替换 web root 之前，部署前保留 web root 副本（deployment_plan DEPLOY-004、ROLLBACK-004）。
- **晋升条件**：待部署提交已在 `origin/main` 且其 CI 运行 `completed / success`；无 staging，无环境间晋升。

## `[INFERRED]` 与待确认

- 无新增取值；CI 基线数字全部来自 PM 复跑（invocation `quality_thresholds`），非本组实测（本组仅实测 Schema 门脚本及其反例变异）。
- 「GitHub runner 上 selfcheck 预期 69/69」为推断（`core_framework_free` 失败源自开发机 `sitecustomize`，REV-27 的 CI 绿灯可佐证 runner 无此问题）；首次 push 后以 CI 实际为准。
- `[TOOL_UNREGISTERED]`：`gh`（仅取证便利）。
