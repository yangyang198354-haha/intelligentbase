<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-23T23:22:51+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file><file>sandbox/trae-demo-wordfreq/docs/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — trae-demo-wordfreq

## 实现概览

- 模块数：3（MOD-001 core、MOD-002 cli、MOD-003 package）；文件数：3；总行数 **118**（core 62 + `__main__` 51 + `__init__` 5），满足 ≤120 行约束。
- 实现顺序（按依赖拓扑）：**MOD-001 → MOD-003 → MOD-002**。MOD-003 与 MOD-002 都只依赖 MOD-001，二者之间无依赖，故顺序可交换；先写 MOD-003 以便包导入路径尽早可用。
- 全部代码仅使用标准库（`argparse`、`re`、`collections`、`pathlib`），无第三方依赖。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 L/M/H | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-001 | `sandbox/trae-demo-wordfreq/src/wordfreq/core.py` | 新建 | 无 | M | 实现 IFC-001…006：Unicode 分词、计数、`(-count, word)` 排序、`word<TAB>count` 格式化、UTF-8 读取、`run` 组合；异常不捕获（ADR-004） | DONE |
| 2 | MOD-003 | `sandbox/trae-demo-wordfreq/src/wordfreq/__init__.py` | 新建 | MOD-001 | L | 实现 IFC-010：重导出 6 个公开函数、`__all__`、`__version__="1.0.0"` | DONE |
| 3 | MOD-002 | `sandbox/trae-demo-wordfreq/src/wordfreq/__main__.py` | 新建 | MOD-001 | M | 实现 IFC-007/008/009：argparse 定义 4 个参数；捕获 `OSError`/`UnicodeDecodeError` 返回 2；`raise SystemExit(main())` | DONE |

## 迁移

无。项目不持久化数据，无表结构或配置文件变更（画像 P6）。

## 架构偏差

无。代码严格按 module_design 的 10 个 IFC 实现，未偏离任何 ADR。

## 开放问题

- **[ASSUMPTION-01]** `--min-length` 小于 1 时按"不过滤"处理（`min_length > 1` 才过滤），与 architecture A-02 一致；未额外 `max(1, L)` 归一化，因为对结果等价。
- **[ASSUMPTION-02]** `format_report` 接受 `collections.abc.Sequence`；内部调用方只传 `list[tuple[str, int]]`，不做逐元素类型校验（成本高、收益低）。
- **[ASSUMPTION-03]** 错误消息直接复用异常文本（含系统路径），不额外脱敏；本地 CLI 场景不涉及凭据（协议 §L-2）。
- 无 stub / 无 `TODO(IFC-NNN)`。

## 自验证摘要

- `python -m compileall -q sandbox/trae-demo-wordfreq/src` → 退出码 0。
- 命令行实跑覆盖：默认统计、`--ignore-case`、`--top`、`--min-length`、空文件、缺失文件（退出码 2）、目录路径（退出码 2）、非法 UTF-8（退出码 2）。结果见 `code_review_report.md` 的"自验证结果"。
- 未新建测试文件（按分工，测试由 GROUP_D 编写）。
