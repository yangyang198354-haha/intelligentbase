<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-23T23:27:24+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/test_plan.md</file><file>sandbox/trae-demo-wordfreq/docs/user_stories.md</file><file>sandbox/trae-demo-wordfreq/src/wordfreq/core.py</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — trae-demo-wordfreq

## 摘要

- 执行时间：2026-10-23T23:27:24+08:00（最后一次执行）
- 环境：Windows / Python 3.14.6 / pytest 9.1.1
- 命令：`python -m pytest sandbox/trae-demo-wordfreq/tests/unit -q`
- 用例：10 个，全部新写（greenfield）
- `total = pass + fail + skip + blocked + not_testable = 10 + 0 + 0 + 0 + 0 = 10`
- 通过率 = `pass / (pass + fail + blocked) = 10 / 10 = **100%**`
- 判定模式：threshold（阈值 0.80）；**本层门控：PASSED**

## 执行输出

```text
> python -m pytest sandbox/trae-demo-wordfreq/tests/unit -q
..........                                                               [100%]
10 passed in 0.02s
UNIT_EXIT=0
```

## 分项结果

按模块 MOD-001 core（全部 unit 用例的目标模块）：

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-001 | AC-001-01 | 基础分词与计数、Top-N | PASS | — | — |
| TC-UNIT-002 | AC-001-02 | 空文本得到空 Counter 与空报告 | PASS | — | — |
| TC-UNIT-003 | AC-002-01/02 | `top` 截断、不足 N、非正数 | PASS | — | — |
| TC-UNIT-004 | AC-003-01/02 | 大小写折叠与未折叠的码位顺序 | PASS | — | — |
| TC-UNIT-005 | AC-004-01/02 | `min_length` 过滤与 0/1 边界 | PASS | — | — |
| TC-UNIT-006 | AC-005-01 | 同次数按字典序升序 | PASS | — | — |
| TC-UNIT-007 | AC-005-02 | 标点/分号作为分隔符 | PASS | — | — |
| TC-UNIT-008 | AC-007-02 | Unicode 中文分词 + IFC-004 格式契约 | PASS | — | — |
| TC-UNIT-009 | AC-006-01 | `read_text` 显式 UTF-8、缺失文件抛 `FileNotFoundError` | PASS | — | — |
| TC-UNIT-010 | AC-001-01/AC-002-02 | `run()` 组合管线 | PASS | — | — |

## 与基线对比

greenfield，无既有测试与既有失败；本次全部用例新写，新增失败 0。

## 失败汇总（需路由给开发）

无。
