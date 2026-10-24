<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-23T23:31:44+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>sandbox/trae-demo-wordfreq/docs/tech_stack.md</file><file>sandbox/trae-demo-wordfreq/docs/e2e_test_report.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — trae-demo-wordfreq

## 现状与影响

- 画像 P7："CI 系统与配置文件：**无**"；仓库中不存在 `.github/workflows/` 之外的可用 CI 配置（`.github/` 存在但本项目的产物不依赖它）。
- 本轮**不创建/修改任何 CI 配置文件**，只产出流水线设计（操作者指令；画像 P7 部署相关配置文件：无）。
- 本次改动为 greenfield 新增 3 个源文件（MOD-001/002/003）、3 个测试文件、1 个 `conftest.py`、1 个 `pytest.ini`；无新依赖、无新服务、无新环境变量，因此对既有 CI 的影响为"无"。

## 流水线概览

```text
[Source] → [PIPE-02 Lint/静态检查] → [PIPE-03 Build] → [PIPE-04 Unit]
         → [PIPE-05 Integration] → [PIPE-06 Package/制品]
         → [PIPE-07 Deploy dev/local] → [PIPE-08 部署后冒烟] → [PIPE-09 E2E]
```

环境：**仅 dev/local**（画像 P7 中 staging 与 production 均为"否"，故流水线**不设计**环境晋升、审批或生产部署阶段）。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | `push` / `pull_request` 到任意分支 | 检出提交 | 检出成功，记录提交 SHA | abort-and-notify |
| PIPE-02 | Lint/静态检查 | 依赖 PIPE-01 | `python -m compileall -q sandbox/trae-demo-wordfreq/src sandbox/trae-demo-wordfreq/tests` | 退出码 0 | abort-and-notify（无自动重试） |
| PIPE-03 | Build | 依赖 PIPE-02 | `python -m compileall -q sandbox/trae-demo-wordfreq/src` | 退出码 0；无第三方依赖安装步骤 | abort-and-notify |
| PIPE-04 | Unit | 依赖 PIPE-03 | `python -m pytest sandbox/trae-demo-wordfreq/tests/unit -q` | 退出码 0 且通过率 ≥ 0.80（本次实测 10 passed） | abort-and-notify |
| PIPE-05 | Integration | 依赖 PIPE-04 | `python -m pytest sandbox/trae-demo-wordfreq/tests/integration -q` | 退出码 0 且通过率 ≥ 0.90（本次实测 4 passed） | abort-and-notify |
| PIPE-06 | Package/制品 | 依赖 PIPE-05；仅 `main` 分支 | 生成源码归档：`git archive --format=zip --output=wordfreq-${COMMIT_SHA}.zip HEAD -- sandbox/trae-demo-wordfreq/src sandbox/trae-demo-wordfreq/tests sandbox/trae-demo-wordfreq/pytest.ini` | 归档存在且非空；文件名含提交 SHA | abort-and-notify |
| PIPE-07 | Deploy dev/local | 依赖 PIPE-06；**仅手工触发**（`workflow_dispatch`） | 按 `deployment_plan.md` 的 DEPLOY-001…003 | DEPLOY 全部成功 | abort-and-notify（禁止跳过失败继续部署） |
| PIPE-08 | 部署后冒烟 | 依赖 PIPE-07 | `python -m wordfreq --help` + 临时样例文件运行 | `--help` 退出码 0；样例输出符合预期 | abort-and-notify |
| PIPE-09 | E2E | 依赖 PIPE-08 | `python -m pytest sandbox/trae-demo-wordfreq/tests/e2e -q` | 退出码 0；critical path 3 passed | abort-and-notify |

- 所有阶段均为"失败即中止并通知"，**不做** `continue-on-error`、`|| true` 或"跳过失败继续部署"。
- 无自动 retry；flake 由人工复核后重跑。
- 运行器未在画像中登记：本文件仅为文档示例，**不引用具体 runner 版本**（画像 P7 无 CI 系统）。

## 环境矩阵

| 配置项 | dev/local（画像 P7 唯一存在） |
|---|---|
| 存在 | 是 |
| 实例数 | 1（单进程 CLI，无服务实例） |
| 资源 | 开发机本地；无容器、无资源限额 [INFERRED] |
| 外部依赖 | 仅 Python 3.11+ 与 pytest 9.1.1（开发依赖，不进入运行时） |
| 配置来源 | 仓库内源码；无环境变量、无配置文件 |
| 部署需用户确认 | 否（画像 P7），但本轮操作者要求不执行 E2 |
| staging / production | 画像 P7 声明不存在，**不设计** |

## 制品管理

- 画像 P7"构建产物管理：无"、"CI 系统与配置文件：无"。
- 因此采用**源码归档制品**（`git archive` 产物），而非目标机本地构建：
  - 命名：`wordfreq-{COMMIT_SHA}.zip`（含 `src/`、`tests/`、`pytest.ini`）。
  - 存储位置：CI 运行产物（artifact），不落地到仓库，不进入制品库（画像无制品库）。
  - 晋升条件：PIPE-04、PIPE-05、PIPE-09 全部通过且提交位于 `main` 分支。
- 风险与缓解：
  - **风险**：无制品库导致版本不可长期追溯。缓解：文件名强制含完整提交 SHA；部署记录中登记 SHA。
  - **风险**：开发机 Python 版本漂移（3.11 vs 3.14）。缓解：部署前核验 `python --version`，并在部署记录中登记。
  - 本轮 P9 规定不执行 commit/push：上述 Source/制品阶段为文档设计，实际启用前需用户确认版本控制操作。
