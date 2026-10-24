<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-10-23T23:13:22+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>.trae/sdlc/project_profile.md</file><file>sandbox/trae-demo-wordfreq/docs/phase_status.md</file></input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格说明书 — trae-demo-wordfreq

## 执行摘要

业务背景：操作者给定需求原文（见 phase_status `<request>`）："CLI `python -m wordfreq PATH` 读取 UTF-8 文本并输出词频 Top-N"，并附参数、分词与排序规则、退出码与零依赖约束。本文件只描述"系统应当做什么"，不含技术选型与代码设计。

- 功能需求：8 条（REQ-FUNC-001…008）；非功能需求：3 条（REQ-NFUNC-001…003）。
- `[INFERRED]`：2 条（REQ-FUNC-008、REQ-NFUNC-003）；占比 2 ÷ (8 + 3) = **18.2%**，未超过画像 P5 `inferred_max = 0.20`。
- 优先级默认规则：需求中明确列出的能力为 Must Have；为保证"同输入同输出"与运行时限而补充的条目为 Should Have。按此规则：Must Have 8 条，Should Have 3 条。
- 角色：命令行使用者（运维/分析师）、项目维护者；无多用户权限模型。

## 现有系统基线

greenfield 全新项目，仓库内无既有实现可参照（`sandbox/trae-demo-wordfreq/` 在本次流程前不存在）。画像 P1/P3 声明为 Python 标准库 CLI，测试用 pytest。

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-001 | 以 `python -m wordfreq PATH` 形式运行，读取 PATH 指向的 UTF-8 文本文件，统计词频并按规则输出 Top-N 结果 | 用户原文 1："CLI `python -m wordfreq PATH` 读取 UTF-8 文本并输出词频 Top-N" | Must Have | 新增 | 输出格式见"开放问题 Q1" |
| REQ-FUNC-002 | 支持 `--top N` 选项控制输出条数，缺省为 10；文件内不同词数少于 N 时输出全部词 | 用户原文 2："支持 `--top N`（默认 10）…" | Must Have | 新增 | |
| REQ-FUNC-003 | 支持 `--ignore-case` 选项，将大小写不同的词视为同一个词后统计 | 用户原文 2："…`--ignore-case`…" | Must Have | 新增 | |
| REQ-FUNC-004 | 支持 `--min-length L` 选项，只统计长度不小于 L 的词，缺省 L=1 | 用户原文 2："…`--min-length L`（默认 1）" | Must Have | 新增 | |
| REQ-FUNC-005 | 把"连续的字母或数字序列"识别为词；非字母/数字字符（标点、空白、下划线等）作为分隔符，不进入词内 | 用户原文 3："词 = 连续的字母/数字序列（`re` 提取）" | Must Have | 新增 | |
| REQ-FUNC-006 | 输出按出现次数降序排列；次数相同按词的字典序升序排列 | 用户原文 3："按出现次数降序，次数相同按词字典序升序" | Must Have | 新增 | |
| REQ-FUNC-007 | 正常结束时退出码为 0；目标文件不存在或不可读时退出码为 2，并在 stderr 给出可读的错误说明，stdout 不输出词频结果 | 用户原文 4："文件不存在或不可读 → 退出码 2 并在 stderr 给出错误；正常 → 退出码 0" | Must Have | 新增 | |
| REQ-FUNC-008 | 文件内容不是合法 UTF-8 时，按"不可读"处理：退出码 2、stderr 给出错误、stdout 无词频结果 | [INFERRED]（基于用户原文 1"读取 UTF-8 文本"+"不可读 → 退出码 2"的组合推断） | Should Have | 新增 | 见"待确认推断项" |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-001 | 运行时不依赖任何第三方包，仅使用 Python 标准库；在仅安装 Python 3.11+ 与本机 pytest 的环境中可直接运行 | 用户原文 5："零第三方依赖，仅标准库"；画像 P8 禁用第三方运行时依赖 | Must Have | 新增 | |
| REQ-NFUNC-002 | 对同一输入文件与同一组选项，多次运行输出内容与顺序完全一致（确定性） | 用户原文 3 的排序规则隐含确定性 | Should Have | 新增 | |
| REQ-NFUNC-003 | 在开发机上处理 1 MiB 左右的 ASCII 文本时，单次运行墙钟时间不超过 5 秒 | [INFERRED]（画像 P4"全量回归应 < 10s"反映的本地性能预期） | Should Have | 新增 | 见"待确认推断项" |

## 约束

- **C-01** 运行时语言与版本：Python 3.11+；仅标准库（画像 P1、P6、P8）。
- **C-02** 产物位置：文档平铺于 `sandbox/trae-demo-wordfreq/docs/`（画像 P2，flat 布局）。
- **C-03** 测试框架：pytest，测试位于 `sandbox/trae-demo-wordfreq/tests/{unit,integration,e2e}/`（画像 P3、P4）。
- **C-04** 离线纪律：不访问网络、不连接生产数据、不安装依赖（画像 P6、P8）。
- **C-05** 本轮不执行部署，只产出 CI/CD 与部署计划（操作者指令）。
- **C-06** 编码统一 UTF-8、行尾 LF（画像 P6）。

## 超出范围

- 图形界面、Web 服务与 API 接口。
- 结果持久化（数据库/文件缓存）、增量统计、跨文件汇总。
- 停用词（stopword）过滤：画像 P1 的一句话描述提到"过滤停用词"，但操作者给定的 5 条需求未包含该能力，按需求优先级视为 **Won't Have（本轮）**，见开放问题 Q2。
- 自定义分词正则、词形还原、多语言分词。
- 打包发布（PyPI）、安装脚本、生产部署。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| REQ-FUNC-008 | 非法 UTF-8 内容视同"不可读"，退出码 2 且 stderr 报错 | 用户原文 1 要求读取 UTF-8，原文 4 规定不可读的退出行为 | 操作者 |
| REQ-NFUNC-003 | 1 MiB 文本处理时间 ≤ 5 秒 | 画像 P4 全量回归 < 10s 的本地性能预期 | 操作者 |

## 开放问题

- **Q1（非阻断）** 输出格式未指定。为保证可验收，暂定每行 `词<TAB>次数`，最后一行无多余空行；该格式将在架构接口契约（GROUP_B）中固化为接口约定，若需 JSON/CSV 请在架构评审前提出。
- **Q2（非阻断）** 画像 P1 提到"过滤停用词"，与操作者给定需求不一致；本轮按需求原文不实现停用词，若需实现应新增需求并重新走 GROUP_A。
- **Q3（非阻断）** `--top` 为负数或非整数、`--min-length` 为负数时的行为未指定。暂定：负数按 0/1 处理（不报错），非整数由命令行参数解析报错并返回退出码 2（argparse 缺省行为）。
- **Q4（非阻断）** "字母/数字"是否指 Unicode 字母（如中文、带重音字符）。暂定按 Unicode 字母数字识别，ASCII 场景行为不变。
