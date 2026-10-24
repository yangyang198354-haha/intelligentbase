<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-10-23T23:13:22+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/requirements_spec.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事 — trae-demo-wordfreq

## 角色 × 功能矩阵

| 角色 | 基础统计 | 条数控制 | 大小写 | 长度过滤 | 排序 | 错误处理 |
|---|---|---|---|---|---|---|
| 命令行使用者 | US-001 | US-002 | US-003 | US-004 | US-005 | US-006 |
| 项目维护者 | US-001 | — | — | — | US-005 | US-006、US-007 |

## 用户故事

### US-001: 统计文本词频并输出 Top-10
- 故事：As a 命令行使用者, I want to 用一条命令得到文件的词频排行, so that 我能快速看出文本的主题集中度。
- 关联需求：REQ-FUNC-001；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-001-01：Given 一个 UTF-8 文件内容为 `apple banana apple`，When 运行 `python -m wordfreq <PATH>` 且不传其他选项，Then stdout 恰好为两行 `apple\t2` 与 `banana\t1`（按此顺序），退出码为 0。
- AC-001-02：Given 一个 0 字节的 UTF-8 文件，When 运行 `python -m wordfreq <PATH>`，Then stdout 为空字符串，退出码为 0。

### US-002: 控制输出条数
- 故事：As a 命令行使用者, I want to 指定输出前 N 名, so that 我能把结果控制在一屏内。
- 关联需求：REQ-FUNC-002；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-002-01：Given 文件含 5 个互不相同的词各出现 1 次，When 运行 `python -m wordfreq <PATH> --top 2`，Then stdout 恰好 2 行，且为字典序最小的两个词（次数相同时按字典序升序），退出码为 0。
- AC-002-02：Given 文件含 2 个不同的词，When 运行 `python -m wordfreq <PATH> --top 5`，Then stdout 恰好 2 行（不足 N 时输出全部），退出码为 0。

### US-003: 忽略大小写统计
- 故事：As a 命令行使用者, I want to 把大小写变体合并统计, so that 我不会因为首字母大写而低估某个词。
- 关联需求：REQ-FUNC-003；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-003-01：Given 文件内容为 `Apple apple APPLE banana`，When 运行 `python -m wordfreq <PATH> --ignore-case`，Then stdout 第一行为 `apple\t3`，第二行为 `banana\t1`，退出码为 0。
- AC-003-02：Given 同样的文件，When 运行 `python -m wordfreq <PATH>`（不带 `--ignore-case`），Then stdout 为 4 行，分别为 `APPLE\t1`、`Apple\t1`、`apple\t1`、`banana\t1`（按字典序升序），退出码为 0。

### US-004: 过滤过短的词
- 故事：As a 命令行使用者, I want to 排除长度小于 L 的词, so that 冠词、单字母等噪声不占据结果。
- 关联需求：REQ-FUNC-004；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-004-01：Given 文件内容为 `a bb ccc dd eee`，When 运行 `python -m wordfreq <PATH> --min-length 3`，Then stdout 恰好 2 行 `ccc\t1`、`eee\t1`（字典序升序），退出码为 0。
- AC-004-02：Given 同样的文件，When 运行 `python -m wordfreq <PATH>`（L 缺省为 1），Then stdout 为 5 行，包含 `a\t1`，退出码为 0。

### US-005: 结果顺序稳定可预期
- 故事：As a 命令行使用者, I want to 顺序规则固定（次数降序、同次数按字典序）, so that 两次运行的差异只来自文件内容。
- 关联需求：REQ-FUNC-005、REQ-FUNC-006；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-005-01：Given 文件内容为 `b a b a c`，When 运行 `python -m wordfreq <PATH>`，Then stdout 依次为 `a\t2`、`b\t2`、`c\t1`（同次数时字典序升序），退出码为 0。
- AC-005-02：Given 文件内容为 `foo,bar.baz;foo`，When 运行 `python -m wordfreq <PATH>`，Then stdout 依次为 `foo\t2`、`bar\t1`、`baz\t1`，退出码为 0（标点不是词的一部分）。

### US-006: 文件不可用时明确失败
- 故事：As a 项目维护者, I want to 在输入文件不可读时得到明确错误与退出码, so that 我能在脚本里可靠地区分成功与失败。
- 关联需求：REQ-FUNC-007；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-006-01：Given 一个不存在的路径 `<PATH>`, When 运行 `python -m wordfreq <PATH>`, Then 退出码为 2，stderr 非空且包含字符串 `wordfreq`，stdout 为空。
- AC-006-02：Given 一个目录路径，When 运行 `python -m wordfreq <DIR>`, Then 退出码为 2，stderr 非空，stdout 为空。

### US-007: 非 UTF-8 内容按不可读处理
- 故事：As a 项目维护者, I want to 在文件不是合法 UTF-8 时失败而不是输出乱码, so that 结果可信。
- 关联需求：REQ-FUNC-008（[INFERRED]）；优先级：Should Have；故事点：2 [ESTIMATE]
- AC-007-01：Given 一个包含非法 UTF-8 字节（如 `0xFF 0xFE`）的文件，When 运行 `python -m wordfreq <PATH>`, Then 退出码为 2，stderr 非空，stdout 为空。
- AC-007-02：Given 一个合法的 UTF-8 中文文件内容 `中文 中文 测试`, When 运行 `python -m wordfreq <PATH>`, Then stdout 第一行为 `中文\t2`，退出码为 0。

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 6 | 15 |
| Should Have | 1 | 2 |
| **合计** | **7** | **17** |

AC 总数：14（每个故事 2 条，均含正常路径与异常/边界路径）。
