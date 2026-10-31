<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-31T16:10:41+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>module_design.md</file>
    <file>architecture_design.md</file>
    <file>implementation_plan.md</file>
    <file>test_plan.md</file>
    <file>unit_test_report.md</file>
    <file>integration_test_report.md</file>
    <file>e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：REV-27 画布支持删除单个节点（INCREMENTAL）

> REV-26 已批准版本归档于 `archive/rev26/cicd_pipeline.md`（只读）；本文按 REV-27 整体重写，沿用其阶段结构。
> 本组**未连接任何环境、未 ssh、未部署、未 commit / push**（画像 P9）；**`.github/workflows/ci.yml` 未修改**。

## 现状与影响

### 现有 CI

| 项 | 内容 |
|---|---|
| 文件 | `.github/workflows/ci.yml`，触发：push / PR 到 `main`、`workflow_dispatch` |
| 运行环境 | `ubuntu-24.04`，Python 3.12，**Node 22**（`ci.yml:240`，R26 由 20 升版），`timeout-minutes: 30` |
| 阶段 | 10 阶段、单 job、fail-fast：Source → Config(compileall)+Schema 门(003/007/008) → Unit → Integration → E2E → Full+coverage → selfcheck → Version gate → Frontend build+test → Package artifact |
| 部署 | **CI 不含 CD**：生产部署由 E2 按 `.claude/skills/ib-prod-deploy/SKILL.md` 授权执行（画像 P7） |

### 本增量对 CI 的影响（逐项核对）

REV-27 提交 `1dde3d45e6e58df2c410593a9ba1d8d3d5e7ed6d`（= `origin/main`，本组核对 `git status -sb` 为 `main...origin/main` 无领先落后）。该提交在 `src tests .github` 下的改动共 9 个文件（`git show --stat`）：`src/frontend/src` 下 7 个产品文件（6 改 1 新：`AgentDetailPanel.vue`、`FlowCanvas.vue`、`PublishDialog.vue`、`publishDiff.ts`、`configDraft.ts`、`ConfigStudio.vue`；新文件 `nodeRemoval.ts`；与 invocation 所述"5 改 2 新"的计数口径不同，以 `git show --stat` 为准），以及 2 个新测试文件（`config_studio_r27.test.js`、`test_diff_node_removal_r27.py`）。

| 影响维度 | 结论 | 依据 |
|---|---|---|
| 新增依赖（Python / npm） | **无** | `git diff bb3ac4b 1dde3d4` 中 `src/requirements*.txt`、`package.json`、`package-lock.json` 无改动 |
| 新测试层 | **无**。新测试落在既有层，被既有 step 自动纳入（见下表） | — |
| 新服务 / 新环境 / 新环境变量 / Docker | **无**；不新增 staging，不引入 Docker（画像 P8） | module_design「受影响的运行单元」 |
| 新迁移 | **无**（Schema 门不变） | module_design「数据迁移」：无 |
| Node 版本 | 无需调整：`nodeRemoval.ts` 被测试直接 `import`，需 Node ≥ 22.6 原生剥离类型，CI 已是 22 | `ci.yml:234-240`；e2e 报告环境 Node v22.23.3 |
| **结论** | **`ci.yml` 无需修改**（本组已核对，未改动任何 CI 文件）。module_design 与 PM 均未要求改 CI | — |

### 新测试在 CI 的落点

| 新测试 | 发现机制 | 运行阶段 | 基线（PM 复跑，2026-10-31） |
|---|---|---|---|
| `src/frontend/tests/config_studio_r27.test.js`（+52 例） | `npm test` = `node --test`，默认发现 `**/*.test.js`（同目录 `config_studio_r26.test.js` 已同样被发现） | PIPE-09（先 `npm run build` 后 `npm test`） | 129 tests / 19 suites / pass 129 / fail 0（R26 基线 77） |
| `tests/unit/test_diff_node_removal_r27.py`（+2 例，TC-UNIT-R27-001/002） | `pytest tests/unit` 目录收集；基名全局唯一（`find tests -name` 仅 1 个，画像 P3 约束满足） | PIPE-03（并被 PIPE-06 重复覆盖） | tests/unit 511（R26 为 509）；全量 `pytest tests` 910 passed（unit 511 / integration 333 / e2e 51 / agents 15） |

**无新阶段。** `vue-tsc --noEmit`（含新文件 `nodeRemoval.ts` 类型检查）已在 PIPE-09 的 `npm run build` 内。

### 部署提交的 CI 状态（E1 取证，非 E2 门）

本机 `gh` 可用（`[TOOL_UNREGISTERED]`：`gh` 未在画像 P4 登记，仅作便利，网页查看等价）。E1 时刻（2026-10-31T16:09+08:00）`gh run list`：REV-27 提交的 CI run `41183387985` 状态 **in_progress**（已运行 1m5s）；前两个提交（`c1b491f`、`fcf5496`）的 CI 均 success。**不得据此视为绿**：deployment_plan 的 PRE-00 要求在 E2 时重新核对为 `completed / success`。

## 流水线概览

```
[Source] → [Config: compileall + Schema/迁移门(003/007/008)] → [Unit(含 R27 +2)] → [Integration] → [E2E]
        → [Full+coverage(含 tests/agents)] → [Selfcheck] → [Version gate] → [Frontend build+test(含 R27 +52)] → [Package artifact]
        ⇢（CI 之外，E2 授权后）[Deploy production: recreate，仅前端发布] → [部署后验证] → [用户人工浏览器验收 M-01~M-08]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 `main`；`workflow_dispatch` | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | Config + Schema 迁移门 | PIPE-01 成功 | `python -m compileall -q src`；内联迁移检查（003 / 007 / 008，REV-27 无变化） | 退出码 0；三行 `PASS:` | abort-and-notify |
| PIPE-03 | Unit | PIPE-02 成功 | `python -m pytest tests/unit -q` | 退出码 0；基线 511 passed（含 R27 +2） | abort-and-notify |
| PIPE-04 | Integration | PIPE-03 成功 | `python -m pytest tests/integration -q` | 退出码 0；基线 333 passed | abort-and-notify |
| PIPE-05 | E2E | PIPE-04 成功 | `python -m pytest tests/e2e -q` | 退出码 0；基线 51 passed | abort-and-notify |
| PIPE-06 | Full suite + coverage | PIPE-05 成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 退出码 0；基线 910 passed（含 `tests/agents` 15）；覆盖率仅记录不设门（画像 P5） | abort-and-notify |
| PIPE-07 | Offline selfcheck | PIPE-06 成功 | `python src/scripts/selfcheck.py` | 退出码 0（任一 FAIL 非零）。REV-27 后端零改动，selfcheck 范围未变；本组与 PM 均未重跑 | abort-and-notify；不得跳过 |
| PIPE-08 | Version gate | PIPE-07 成功 | ci.yml 阶段 8 内联命令 | bcrypt、langchain-core、langchain-openai pin、无 PyMuPDF、无 Dockerfile、Python 范围全 PASS | abort-and-notify |
| PIPE-09 | Frontend build + test | PIPE-08 成功 | `npm ci && npm run build && npm test`（`src/frontend`，Node 22） | vue-tsc 零错、vite build 成功、node:test 129/129/0 | abort-and-notify |
| PIPE-10 | Package artifact | PIPE-09 成功 | `git rev-parse HEAD > HEAD`；`actions/upload-artifact@v4` | artifact `ib-<sha>-<run_id>` 上传，保留 30 天 | abort-and-notify |

失败处理仅 abort-and-notify（fail-fast，无 `continue-on-error`），**禁止"跳过失败继续部署"**。CD 不在 CI 内：部署经 E2 ssh 到 production（`git pull --ff-only` + 前端目标机构建发布），部署前置 = 待部署提交的 CI 全绿。

## 环境矩阵

| 配置项 | dev/local | CI | production |
|---|---|---|---|
| 存在 | 是 | 是 | 是（单台物理机；**无 staging**，画像 P7） |
| 实例数 | 离线测试进程 | 1 个 runner | ib-web ×1、ib-worker ×1（禁多实例，画像 P8）、ib-embed ×1、qdrant ×1；**REV-27 不重启其中任何一个**（见 deployment_plan 的条件分支说明） |
| 资源 | 开发机 | ubuntu-24.04，30 min 超时 | i7-3770S 4C/8T、11 GiB、CPU-only（SKILL.md §1） |
| 外部依赖 | 无（离线） | 无（离线替身） | Qdrant、ib-embed、云端 DeepSeek（REV-27 不涉及） |
| 配置来源 | `tests/conftest.py` setdefault | ci.yml job 级 `env` | `/etc/intelligentbase/*.env`（0600，只由用户读写，不回显；REV-27 不触碰） |
| 部署需用户确认 | 否 | 否 | **是**（`PRODUCTION_DEPLOY_CONFIRM=true` + 环境名 `production`） |

## 制品管理

- **CI 制品**：frontend `dist/` + `HEAD` 作为 Actions artifact，命名 `ib-${{ github.sha }}-${{ github.run_id }}`（含提交号），保留 30 天；仅供追溯。
- **生产不使用该制品**：目标机 `git pull --ff-only` 后**本地构建**前端（`npm run build`）并拷贝到 web root。风险：目标机（node 22 / npm 9）与 CI 的 npm 版本不同，产物 hash 可能与 CI dist 不一致；缓解：`&&` 链使构建失败发生在替换 web root 之前（旧前端继续可用），并保留部署前 web root 副本（deployment_plan DEPLOY-002、ROLLBACK-002）。
- **晋升条件**：待部署提交已在 `origin/main` 且其 CI 运行 `completed / success`；无 staging，无环境间晋升。

## `[INFERRED]` 与待确认

- 本文无新增取值；CI 基线数字全部来自 PM 复跑（invocation `quality_thresholds`）与 e2e 报告，非本组实测。
- `[TOOL_UNREGISTERED]`：`gh`（仅取证便利）。
