# Project Profile — trae-demo-wordfreq

> **沙箱测试专用画像**：用于验证 TRAE 版 SDLC 套件能否端到端跑通。
> 由操作者在沙箱测试中预先批准（status=APPROVED），不代表任何真实业务项目的确认结论。
> 不含任何凭据。

<file_header>
  <author_agent>pm-orchestrator(draft)</author_agent>
  <timestamp>2026-10-23T00:00:00+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <status>APPROVED</status>
</file_header>

## P1. 项目概况
- 一句话描述：一个零依赖的命令行文本词频统计器，支持忽略大小写、过滤停用词、输出 Top-N。
- 技术栈：Python 3.11+ 标准库（`argparse` / `collections` / `re` / `pathlib`）；测试用 pytest。
- 运行形态：CLI。
- 权威说明文档：本画像；产物在 `sandbox/trae-demo-wordfreq/docs/`。

## P2. 文档工作区
- `docs_root`: `sandbox/trae-demo-wordfreq/docs/`
- `docs_layout`: **flat**（全部产物平铺在 docs_root 下）
- 是否入库: 是（沙箱验证产物，随仓库保留作为证据）

## P3. 代码布局
- `code_mode`: **greenfield**
- 代码目录：

  | 组件 | 目录 | 语言 |
  |---|---|---|
  | CLI 入口 | `sandbox/trae-demo-wordfreq/src/wordfreq/` | Python |
  | 测试 | `sandbox/trae-demo-wordfreq/tests/` | Python |

- 测试位置约定：`tests/unit/`、`tests/integration/`、`tests/e2e/`，命名 `test_*.py`，框架 pytest。
- 不可修改目录：无（不引第三方依赖）。

## P4. 命令（开发机本地，严禁连生产）
| 用途 | 工作目录 | 命令 | 备注
|---|---|---|---|
| 环境准备 | 仓库根 | 无（仅标准库 + 已装 pytest） | 不安装任何依赖
| 编译检查 | 仓库根 | `python -m compileall -q sandbox/trae-demo-wordfreq/src` | |
| 单元测试 | 仓库根 | `python -m pytest sandbox/trae-demo-wordfreq/tests/unit -q` | |
| 集成测试 | 仓库根 | `python -m pytest sandbox/trae-demo-wordfreq/tests/integration -q` | |
| E2E 测试 | 仓库根 | `python -m pytest sandbox/trae-demo-wordfreq/tests/e2e -q` | |
| 全量回归 | 仓库根 | `python -m pytest sandbox/trae-demo-wordfreq/tests -q` | 应 < 10s
- 已知既有失败 / 基线来源：greenfield，无既有基线（以本次实跑为准）。
- 缺依赖时的处理：如实标 BLOCKED，**不安装**。

## P5. 质量判定
- FULL_FLOW `gate_mode`: **threshold** — unit_pass 0.80 / integration_pass 0.90 / critical_path 1.00 / coverage_min 无
- INCREMENTAL `gate_mode`: baseline — 零新增失败
- `inferred_max`: 0.20

## P6. 开发约定
- 数据迁移方式：无（不持久化）。
- 鉴权与权限模型：无（本地 CLI）。
- 代码风格 / lint：PEP 8 基本风格；不引 lint 工具。
- 依赖管理：仅标准库；**禁止**新增第三方依赖。
- 其他约定：
  - 编码统一 UTF-8；行尾 LF。
  - 不读取网络、不访问生产数据。
  - 提交信息 Conventional Commits（本沙箱不提交）。

## P7. 环境、CI 与部署
- 环境：

  | 环境 | 存在 | 访问方式（不含口令） | 部署需用户确认 | 备注 |
  |---|---|---|---|---|
  | dev/local | 是 | 本机命令行 | 否 | |
  | staging | 否 | — | — | |
  | production | 否 | — | — | 沙箱不部署 |

- 部署方式：无（本轮仅验证流程，E1 只产出计划）。
- 允许的部署策略：recreate（仅文档示例）。
- 构建产物管理：无。
- 运行单元：单进程 CLI，无服务。
- 目标机本地状态：无。
- 回滚方式偏好：git revert（仅文档示例）。
- 部署后验证：`python -m wordfreq --help` 退出码 0。
- CI 系统与配置文件：无（文档描述 GitHub Actions 示例即可）。
- 部署相关配置文件：无。

## P8. 禁用项（门控时任一出现即 FAIL）
| 禁用的技术 / 操作 | 原因 |
|---|---|
| 任何第三方运行时依赖 | 沙箱要求零依赖、离线可跑 |
| 网络请求 / 访问生产数据 | 离线测试纪律 |
| Docker / 容器化 | 本项目无部署 |
| 修改 `.claude/**` | 源套件只读 |

## P9. 版本控制与远程操作权限
- 分支策略：不涉及（沙箱产物不提交）。
- 谁执行 commit / push：**不执行**。
- 子代理是否可 ssh / 部署：否。
- 提交前必须通过的检查：不涉及。

## P10. 额外必读（PM 填入 required_reading）
| Agent | 额外文件 |
|---|---|
| test-engineer | 无 |
| devops-engineer | 无 |
