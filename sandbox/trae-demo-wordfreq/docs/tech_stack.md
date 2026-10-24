<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-23T23:16:18+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈 — trae-demo-wordfreq

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | 目标 3.11+（画像 P1）；本机实测 3.14.6（`python --version`） | 沿用 | 画像 P1 指定；标准库足以完成全部需求 | REQ-NFUNC-001 | Low：需避免使用 3.12+ 独有语法，否则 3.11 不可运行 |
| 运行时依赖 | 仅标准库：`argparse`、`re`、`collections`、`pathlib` | 随 Python 发行版（本机 3.14.6） | 沿用 | 零第三方依赖（REQ-NFUNC-001、ADR-005） | REQ-NFUNC-001 | Low：标准库 API 稳定 |
| 参数解析 | `argparse` | Python 标准库（3.11+ 稳定） | 沿用 | ADR-001；自带 `--help` 与非法整数校验 | REQ-FUNC-001…004 | Low：默认错误文案为英文 |
| 分词 | `re`（Unicode `[^\W_]+`） | Python 标准库 | 沿用 | ADR-002；同时覆盖 ASCII 与中文 | REQ-FUNC-005 | Medium：不做 Unicode 规范化（见 A-01） |
| 计数/排序 | `collections.Counter` + `sorted` | Python 标准库 | 沿用 | ADR-003；排序键 `(-count, word)` 保证确定性 | REQ-FUNC-006、REQ-NFUNC-002 | Low |
| 文件读取 | `pathlib.Path.read_text(encoding="utf-8")` | Python 标准库 | 沿用 | 显式 UTF-8，跨平台一致；异常类型清晰 | REQ-FUNC-007/008 | Low：Windows 上目录路径抛 `PermissionError`，已在 AC-006-02 覆盖 |
| 测试框架 | pytest | 9.1.1（`python -m pytest --version`，本机已装，画像 P4） | 沿用 | 画像 P4 指定；不进入运行时依赖 | 全部 | Low：版本差异可能影响断言输出格式，测试只断言自身 stdout |
| 数据存储 | 无 | — | — | 需求无持久化 | — | — |
| 消息/缓存 | 无 | — | — | 单进程 CLI | — | — |
| 前端 | 无 | — | — | 需求无界面 | — | — |
| 进程管理/容器化 | 无 | — | — | 画像 P8 禁用 Docker；画像 P7 无服务 | — | — |
| CI/CD | GitHub Actions（仅文档示例） | 未知：不使用仓库配置，未联网核实 runner 版本 | 新增（文档） | E1 产出示例流水线，不落地配置文件（画像 P7"CI 系统与配置文件：无"） | — | Low：示例不执行 |
| 部署方式 | 无（画像 P7"部署方式：无"） | — | — | 本轮不部署；E1 仅计划 | — | — |
| 新增第三方依赖 | **无** | — | — | 明确禁止（REQ-NFUNC-001、画像 P8） | REQ-NFUNC-001 | — |

## 技术风险

### High

- 无。

### Medium

1. **Unicode 规范化缺失**（ADR-002 / A-01）：同一视觉词的不同编码形式（NFC vs NFD）会被计为两个词。缓解：需求未要求规范化，保持最小实现；在文档中明示；若后续有真实多语言语料再新增需求。
2. **"字典序"按码位而非本地化排序**（ADR-003）：`APPLE`、`Apple`、`apple` 的顺序由 Unicode 码位决定，与某些用户的直觉排序不同。缓解：该行为已固化为 AC-003-02，测试锁定预期；如需本地化排序需引入 `locale`（进程级全局状态），不在本轮范围。

### Low

1. **Python 版本下界**：使用 `from __future__ import annotations` 与 `X | Y` 类型写法（3.10+），3.11 可用；避免 3.12 的 `type` 语句。缓解：代码评审时核对语法。
2. **Windows 目录读取差异**：对目录调用 `read_text` 在 Windows 抛 `PermissionError`，在部分平台可能抛 `IsADirectoryError`，两者均为 `OSError` 子类，统一映射为退出码 2。缓解：集成测试用目录路径覆盖（AC-006-02）。
3. **argparse 错误路径**：缺参/非法整数的退出码是 argparse 内建的 2，不是我们显式返回的 2；语义一致但来源不同。缓解：测试只断言退出码与 stderr 非空，不断言文案全文。
