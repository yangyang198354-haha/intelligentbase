<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-23T23:27:24+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/user_stories.md</file><file>sandbox/trae-demo-wordfreq/docs/requirements_spec.md</file><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>sandbox/trae-demo-wordfreq/docs/implementation_plan.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — trae-demo-wordfreq

## 测试策略

- **被测改动**：MOD-001 core、MOD-002 cli、MOD-003 package（greenfield，3 个源文件共 118 行）。
- **范围 in scope**：US-001…US-007 对应的 14 条 AC；三层（unit / integration / e2e）全部真实执行。
- **范围 out of scope**：性能压测（REQ-NFUNC-003 只在大文件场景下验证，本轮不构造 1 MiB 数据）、CLI `--help` 文案、非法参数（`--top abc`）由 argparse 负责的路径。
- **环境**：Windows，Python 3.14.6（画像 P1 目标 3.11+），pytest 9.1.1；测试仅用 `tmp_path` 下的临时文件，不访问网络、不写持久存储、不连任何服务。
- **分层机制**：目录分层（画像 P4）——`tests/unit`、`tests/integration`、`tests/e2e`；每个用例额外打 pytest marker（`unit` / `integration` / `e2e`），marker 在 `sandbox/trae-demo-wordfreq/pytest.ini` 注册。
- **判定模式**：threshold（FULL_FLOW）；`unit_pass ≥ 0.80`、`integration_pass ≥ 0.90`、`critical_path = 1.00`；`coverage_min = 无`。
- **基线来源**：greenfield，画像 P4 声明无既有测试与既有失败；本次为首次执行。
- **分层顺序**：unit → 判定 → integration → 判定 → e2e → 判定 → 全量回归。
- **critical path 口径**：E2E（真实 `python -m wordfreq` 子进程旅程）；Must Have 故事 6 个（US-001…US-006），E2E 用例需覆盖全部 6 个。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|
| AC-001-01 | TC-UNIT-001 | unit | 新写 | `tests/unit/test_core.py::test_tokenize_and_count_basic` | 文本 `apple banana apple` | `count_words` + `top_words` | `[("apple",2),("banana",1)]` | 内存字符串 |
| AC-001-01 | TC-UNIT-010 | unit | 新写 | `::test_run_composes_pipeline` | 临时文件 `one two two three three three` | `run(top=2)` | `"three\t3\ntwo\t2"` | tmp_path |
| AC-001-01 | TC-INT-001 | integration | 新写 | `tests/integration/test_cli.py::test_cli_top_n_and_default_sorting` | 临时文件 `e d c b a` | 子进程 `python -m wordfreq file --top 2` | 退出码 0，两行 `a\t1`、`b\t1` | tmp_path |
| AC-001-01 | TC-E2E-001 | e2e | 新写 | `tests/e2e/test_e2e_cli.py::test_e2e_basic_report_and_top_option` | 8 词故事文本 | 子进程默认运行两次 | 首行 `the\t3`、次行 `fox\t2`、共 8 行、两次输出一致 | tmp_path |
| AC-001-02 | TC-UNIT-002 | unit | 新写 | `::test_empty_text_yields_empty_report` | 空字符串 | `count_words` + `format_report([])` | 空 Counter、空串 | 内存字符串 |
| AC-002-01 | TC-UNIT-003 | unit | 新写 | `::test_top_words_respects_limit_and_short_input` | 5 个单次词 | `top_words(counter, 2)` | `[("a",1),("b",1)]` | 内存字符串 |
| AC-002-01 | TC-INT-001 | integration | 新写 | 同上 | 5 词文件 | `--top 2` | 恰好 2 行 | tmp_path |
| AC-002-01 | TC-E2E-001 | e2e | 新写 | 同上 | 8 词文件 | `--top 2` | 恰好 2 行 | tmp_path |
| AC-002-02 | TC-UNIT-003 | unit | 新写 | 同上 | 5 个不同词 | `top_words(counter, 5)` | 长度 5 | 内存字符串 |
| AC-002-02 | TC-UNIT-010 | unit | 新写 | 同上 | 3 种词 | `run(top=2)` | 2 行 | tmp_path |
| AC-003-01 | TC-UNIT-004 | unit | 新写 | `::test_ignore_case_folds_tokens` | `Apple apple APPLE banana` | `count_words(ignore_case=True)` | `apple` 3、`banana` 1 | 内存字符串 |
| AC-003-01 | TC-INT-002 | integration | 新写 | `::test_cli_case_and_length_options_combine` | `Alpha alpha ALPHA beta gamma` | `--ignore-case --min-length 5` | `alpha\t3`、`gamma\t1`，退出码 0 | tmp_path |
| AC-003-01 | TC-E2E-002 | e2e | 新写 | `::test_e2e_case_and_length_journey` | 同一文本 | `--ignore-case` | `alpha 3 / beta 1 / gamma 1` | tmp_path |
| AC-003-02 | TC-UNIT-004 | unit | 新写 | 同上 | 同一文本，不折叠 | `count_words` | `APPLE/Apple/apple` 各 1，顺序固定 | 内存字符串 |
| AC-003-02 | TC-E2E-002 | e2e | 新写 | 同上 | 同一文本 | 默认运行 | 5 行，`ALPHA`、`Alpha`、`alpha`、`beta`、`gamma` 各 1 | tmp_path |
| AC-004-01 | TC-UNIT-005 | unit | 新写 | `::test_min_length_filters` | `a bb ccc dd eee` | `min_length=3` | `ccc`、`eee` | 内存字符串 |
| AC-004-01 | TC-INT-002 | integration | 新写 | 同上 | 同 TC-INT-002 | `--min-length 5` | `beta` 被过滤 | tmp_path |
| AC-004-01 | TC-E2E-002 | e2e | 新写 | 同上 | 同 TC-E2E-002 | `--min-length 5` | 仅 `alpha`、`gamma` | tmp_path |
| AC-004-02 | TC-UNIT-005 | unit | 新写 | 同上 | 同一文本 | `min_length=0` | 5 个词全部保留 | 内存字符串 |
| AC-005-01 | TC-UNIT-006 | unit | 新写 | `::test_tie_break_is_lexicographic` | `b a b a c` | `top_words` | `a 2 / b 2 / c 1` | 内存字符串 |
| AC-005-01 | TC-E2E-003 | e2e | 新写 | `::test_e2e_ordering_and_failure_exit_codes` | 同一文本 | 子进程默认运行 | 三行顺序固定 | tmp_path |
| AC-005-02 | TC-UNIT-007 | unit | 新写 | `::test_punctuation_separates_words` | `foo,bar.baz;foo` | `top_words` | `foo 2 / bar 1 / baz 1` | 内存字符串 |
| AC-006-01 | TC-UNIT-009 | unit | 新写 | `::test_read_text_is_utf8_and_raises_on_missing` | 不存在路径 | `read_text` | 抛 `FileNotFoundError` | tmp_path |
| AC-006-01 | TC-INT-003 | integration | 新写 | `::test_cli_missing_file_exits_2` | 不存在路径 | 子进程运行 | 退出码 2、stdout 空、stderr 含 `wordfreq` | tmp_path |
| AC-006-01 | TC-E2E-003 | e2e | 新写 | 同上 | 不存在路径 | 子进程运行 | 退出码 2、stdout 空 | tmp_path |
| AC-006-02 | TC-INT-004 | integration | 新写 | `::test_cli_directory_and_bad_utf8_exit_2` | 目录路径 | 子进程运行 | 退出码 2、stderr 非空 | tmp_path |
| AC-007-01 | TC-INT-004 | integration | 新写 | 同上 | 字节 `61 FF FE 62` | 子进程运行 | 退出码 2、stdout 空 | tmp_path |
| AC-007-02 | TC-UNIT-008 | unit | 新写 | `::test_unicode_words_and_format_contract` | `中文 中文 测试` | `count_words` + `format_report` | `中文 2 / 测试 1`，`word\tcount` 契约 | 内存字符串 |

统计：14 条 AC 全部有至少 1 个真实执行用例；17 个测试函数（UNIT 10 / INT 4 / E2E 3），全部新写（greenfield 无既有测试）。

## 测试数据需求

无 `[DATA_REQUIRED]`。全部数据为测试内构造的临时文件或内存字符串，不依赖外部环境，不写持久存储（无需唯一化）。

## 不可测项

| AC | 原因 |
|---|---|
| REQ-NFUNC-003（1 MiB ≤ 5s） | 属于性能指标，非 AC 条目；本轮未构造大文件，改由 `test_plan` 说明 + 全量回归 < 1s 间接佐证。无 `[NOT_TESTABLE]` AC。 |
