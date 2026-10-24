<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-23T23:22:51+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/implementation_plan.md</file><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — trae-demo-wordfreq

## 摘要

greenfield 新建 3 个文件、合计 118 行（无 `git diff`，文件清单如下）：

| 文件 | 行数 | 对应 MOD |
|---|---|---|
| `sandbox/trae-demo-wordfreq/src/wordfreq/core.py` | 62 | MOD-001 |
| `sandbox/trae-demo-wordfreq/src/wordfreq/__main__.py` | 51 | MOD-002 |
| `sandbox/trae-demo-wordfreq/src/wordfreq/__init__.py` | 5 | MOD-003 |

- 五维平均分：**9.4 / 10**（Correctness 9.7、Security 9.3、Performance 9.7、Maintainability 9.3、Testability 9.3）。
- 问题统计：CRITICAL **0（已修复 0）** / MAJOR **0** / MINOR **3**（均 OPEN，不阻断）。
- CRITICAL 遗留：无。

## 文件 → MOD/IFC 映射

| 文件 | MOD | 实现 IFC |
|---|---|---|
| `core.py` | MOD-001 | IFC-001 `tokenize`、IFC-002 `count_words`、IFC-003 `top_words`、IFC-004 `format_report`、IFC-005 `read_text`、IFC-006 `run` |
| `__main__.py` | MOD-002 | IFC-007 `build_parser`、IFC-008 `main`、IFC-009 模块入口 |
| `__init__.py` | MOD-003 | IFC-010 公开导出 |

## 自验证结果

### 1) 编译检查

```text
> python -m compileall -q sandbox/trae-demo-wordfreq/src
COMPILE_EXIT=0
```

### 2) 命令行实跑（`PYTHONPATH=sandbox/trae-demo-wordfreq/src`）

```text
> python -m wordfreq %TEMP%\wf_demo.txt            # 内容: Apple apple APPLE banana
APPLE   1
Apple   1
apple   1
banana  1
EXIT=0

> python -m wordfreq %TEMP%\wf_demo.txt --ignore-case
apple   3
banana  1
EXIT=0

> python -m wordfreq %TEMP%\no_such_file_xyz.txt
wordfreq: error: [Errno 2] No such file or directory: '...\no_such_file_xyz.txt'
EXIT=2

> python -m wordfreq %TEMP%\wf_empty.txt
EXIT=0                      # stdout 为空

> python -m wordfreq %TEMP%\wf_bad.txt              # 字节 61 FF FE 62
wordfreq: error: 'utf-8' codec can't decode byte 0xff in position 1: invalid start byte
EXIT=2

> python -m wordfreq %TEMP%                          # 目录路径
wordfreq: error: [Errno 13] Permission denied: '...\Temp'
EXIT=2

> python -m wordfreq %TEMP%\wf_sort.txt --top 2     # 内容: b a b a c
a       2
b       2
EXIT=0

> python -m wordfreq %TEMP%\wf_min.txt --min-length 3   # 内容: a bb ccc dd eee
ccc     1
eee     1
EXIT=0
```

结论：默认路径、三个选项、空文件、缺失文件、目录、非法 UTF-8 全部与 IFC/AC 预期一致。

### 3) 未验证项

- 单元/集成/E2E 的 pytest 用例尚未存在（由 test-engineer 负责），故本次没有 pytest 计数行；已如实标注，不声称"测试通过"。

## 按模块评审

### MOD-001

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 10/10 | 9/10 | 10/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `core.py:45` | `format_report` 标注为 `Sequence[tuple[str, int]]`，但不校验元素形状；外部误用时会在 f-string 处抛 `TypeError` | OPEN |
| CR-003 | MINOR | `core.py:26` | 词条契约写作 `word<TAB>count` 字面量，读起来略生硬（功能无误） | OPEN |

### MOD-002

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 10/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MINOR | `__main__.py:47` | stderr 文本直接包含异常中的本地绝对路径；本地 CLI 可接受，未脱敏 | OPEN |

说明：`main()` 只捕获 `OSError` 与 `UnicodeDecodeError`；argparse 的 `SystemExit(2)` 按 ADR-001 保留，与 REQ-FUNC-007 的退出码一致。

### MOD-003

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无问题 | — |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无（0 条，未超过 3 条阈值）。

## 缺陷修复

无（首轮实现，未收到 test-engineer 的 `<defects>`）。

## 现有测试调整

无。greenfield，改动前不存在任何测试文件（`sandbox/trae-demo-wordfreq/tests/` 为空目录），未新建测试文件。
