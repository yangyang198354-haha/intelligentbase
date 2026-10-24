<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-23T23:27:24+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/test_plan.md</file><file>sandbox/trae-demo-wordfreq/tests/integration/test_cli.py</file><file>sandbox/trae-demo-wordfreq/src/wordfreq/__main__.py</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — trae-demo-wordfreq

## 摘要

- 执行时间：2026-10-23T23:27:24+08:00（最后一次执行）
- 环境：Windows / Python 3.14.6 / pytest 9.1.1；集成边界 = **MOD-002 CLI ↔ MOD-001 core**（真实 `python -m wordfreq` 子进程，非 mock）
- 命令：`python -m pytest sandbox/trae-demo-wordfreq/tests/integration -q`
- 用例：4 个，全部新写
- `total = pass + fail + skip + blocked + not_testable = 4 + 0 + 0 + 0 + 0 = 4`
- 通过率 = `pass / (pass + fail + blocked) = 4 / 4 = **100%**`
- 判定模式：threshold（阈值 0.90）；**本层门控：PASSED**

## 执行输出

```text
> python -m pytest sandbox/trae-demo-wordfreq/tests/integration -q
....                                                                     [100%]
4 passed in 0.35s
INT_EXIT=0
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-001 | AC-001-01/AC-002-01 | CLI 解析 `path` 与 `--top`，输出恰好 2 行、退出码 0、stderr 空 | PASS | — | — |
| TC-INT-002 | AC-003-01/AC-004-01 | `--ignore-case` 与 `--min-length 5` 组合生效 | PASS | — | — |
| TC-INT-003 | AC-006-01 | 缺失文件 → 退出码 2、stdout 空、stderr 含 `wordfreq` | PASS | — | — |
| TC-INT-004 | AC-006-02/AC-007-01 | 目录路径与非法 UTF-8 均 → 退出码 2、stdout 空 | PASS | — | — |

集成边界覆盖：

- `MOD-002 → MOD-001`：4 个用例全部经 `IFC-006 run()` 调用链，覆盖成功与失败路径。
- 模块内部纯函数由 UNIT 层覆盖，不在本层重复。

## 与基线对比

greenfield，无既有集成测试；本次 4 个用例全部新写，新增失败 0。

## 失败汇总（需路由给开发）

无。
