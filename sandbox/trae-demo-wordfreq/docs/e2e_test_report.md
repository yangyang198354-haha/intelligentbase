<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-23T23:27:24+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/test_plan.md</file><file>sandbox/trae-demo-wordfreq/tests/e2e/test_e2e_cli.py</file><file>sandbox/trae-demo-wordfreq/docs/user_stories.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — trae-demo-wordfreq

## 摘要

**critical path 口径：E2E**（真实 `python -m wordfreq` 子进程，多步用户旅程）

- 执行时间：2026-10-23T23:27:24+08:00（最后一次执行）
- 环境：Windows / Python 3.14.6 / pytest 9.1.1
- 命令：`python -m pytest sandbox/trae-demo-wordfreq/tests/e2e -q`
- `total = pass + fail + skip + blocked + not_testable = 3 + 0 + 0 + 0 + 0 = 3`
- 本层通过率 = `3 / (3 + 0 + 0) = **100%**`
- **critical path 覆盖率 = 6 / 6 = 100%**（Must Have 故事 US-001…US-006 全部有 E2E 用例）
- **critical path 通过率 = 3 / 3 = 100%**
- 判定模式：threshold（阈值 1.00）；**本层门控：PASSED**

## 执行输出

```text
> python -m pytest sandbox/trae-demo-wordfreq/tests/e2e -q
...                                                                      [100%]
3 passed in 0.55s
E2E_EXIT=0
```

## 全量回归

```text
> python -m pytest sandbox/trae-demo-wordfreq/tests -q
.................                                                        [100%]
17 passed in 0.89s
ALL_EXIT=0
```

- 计数：`17 = 17 pass + 0 fail + 0 skip + 0 blocked + 0 not_testable`
- 相对基线新增失败数：**0**（greenfield，无既有失败）

## 用户旅程

### TC-E2E-001: 统计文件并控制输出条数

- 关联：US-001、US-002 / AC-001-01、AC-002-01；环境：dev/local，临时文件
- 输入：`the quick brown fox jumps over the lazy dog the fox`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | `python -m wordfreq story.txt` | 退出码 0；首行 `the\t3`，次行 `fox\t2`，共 8 行 | 与期望一致 | PASS |
| 2 | 再次运行同一命令 | stdout 与步骤 1 完全一致（确定性） | 完全一致 | PASS |
| 3 | `python -m wordfreq story.txt --top 2` | 恰好两行 `the\t3`、`fox\t2` | 与期望一致 | PASS |

- 结论：PASS

### TC-E2E-002: 大小写折叠与长度过滤

- 关联：US-003、US-004 / AC-003-01、AC-003-02、AC-004-01；环境：dev/local
- 输入：`Alpha alpha ALPHA beta gamma`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 默认运行 | 5 行：`ALPHA\t1`、`Alpha\t1`、`alpha\t1`、`beta\t1`、`gamma\t1` | 与期望一致 | PASS |
| 2 | `--ignore-case` | `alpha\t3`、`beta\t1`、`gamma\t1` | 与期望一致 | PASS |
| 3 | `--ignore-case --min-length 5` | 仅 `alpha\t3`、`gamma\t1` | 与期望一致 | PASS |

- 结论：PASS

### TC-E2E-003: 排序稳定性与失败退出码

- 关联：US-005、US-006 / AC-005-01、AC-006-01；环境：dev/local
- 输入：`b a b a c`；另用不存在的路径

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | `python -m wordfreq ties.txt` | 退出码 0；`a\t2`、`b\t2`、`c\t1` | 与期望一致 | PASS |
| 2 | `python -m wordfreq absent.txt` | 退出码 2；stdout 为空；stderr 含 `wordfreq` | 与期望一致 | PASS |

- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| — | — | 无产品缺陷 | — | — |

### 测试自身修正记录（非产品缺陷）

首轮执行 `TC-E2E-002` 时，断言把 `beta` 的期望次数写成 2（实际文本中 `Alpha/alpha/ALPHA` 是三个不同词，`beta` 仅出现 1 次），属**测试编写错误**。已修正断言并重跑三层与全量回归；本报告所有数字均来自修正后的最后一次执行（3 passed / 17 passed）。
