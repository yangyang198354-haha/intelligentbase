<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-23T23:16:18+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/requirements_spec.md</file><file>sandbox/trae-demo-wordfreq/docs/user_stories.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — trae-demo-wordfreq

## 架构概览

**架构风格**：分层单体 + 单进程 CLI。一次执行由三部分组成：

1. **入口层**：解析命令行参数，捕获错误并映射退出码（MOD-002）。
2. **核心层**：纯函数式的分词、计数、排序与格式化，不读写文件、不退出进程（MOD-001）。
3. **IO 层**：以显式 UTF-8 读取文件（MOD-001 内部 `read_text`）。

选择该风格的原因：需求规模极小（REQ-FUNC-001…008），唯一质量压力是零依赖（REQ-NFUNC-001）与确定性（REQ-NFUNC-002）。核心层保持纯函数可直接被单元测试覆盖，入口层薄到只做参数与错误映射，避免把退出逻辑散落到业务函数中（ADR-006）。

**关键质量属性**：

- 零第三方运行时依赖（REQ-NFUNC-001）：只用 `argparse`、`re`、`collections.Counter`、`pathlib`。
- 确定性（REQ-NFUNC-002）：排序键完全由 `(-次数, 词码位)` 决定，不依赖哈希顺序或输入顺序。
- 性能（REQ-NFUNC-003）：单次线性扫描 + 一次排序；1 MiB 文本在本地远低于 5 秒。
- 可观测的失败（REQ-FUNC-007/008）：只有入口层决定退出码，错误统一写 stderr。

## 部署视图

| 组件 | 运行单元 | 环境 | 说明 |
|---|---|---|---|
| `wordfreq` 包（MOD-001/002/003） | 单次 CLI 进程（`python -m wordfreq`） | dev/local（画像 P7 唯一存在的环境） | 无服务、无端口、无持久化、无定时任务 |
| 测试套件 | pytest 进程 | dev/local | 不作为部署单元 |

画像 P7 声明 staging / production 不存在，故部署视图**不设计**这两个环境；本轮也不执行 E2（操作者指令、画像 P7"部署方式：无"）。

## ADR

### ADR-001: 命令行参数解析方式

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001/002/003/004 要求 `PATH`、`--top N`、`--ignore-case`、`--min-length L`；REQ-NFUNC-001 禁止第三方依赖。
- Options:
  - **A. `argparse`（标准库）**：优——自动生成 `--help`、自动处理 `--opt=value`/`--opt value`、非法整型自动报错；缺——用法消息为英文默认文案，定制空间有限。
  - **B. 手写 `sys.argv` 解析**：优——完全可控；缺——需自行实现 `--help`、非法值、缺参处理，重复实现且易漏边界，测试面更大。
  - **C. `click` / `typer`（第三方）**：优——体验好；缺——违反 REQ-NFUNC-001 与画像 P8（第三方运行时依赖），直接排除。
- Decision: 选择 **A**。标准库即可满足全部选项契约，且非法整数由解释器框架统一返回退出码 2（与 REQ-FUNC-007 的错误码一致）。
- Consequences: 正向——参数错误与帮助文本零成本获得；负向——`--help` 文案为英文且不可本地化；参数错误路径由框架决定，测试需按框架实际行为断言（见 module_design IFC-007）。

### ADR-002: 分词规则

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-005 要求"连续的字母/数字序列（`re` 提取）"；REQ-FUNC-003 要求可忽略大小写；开放问题 Q4 询问 Unicode 字母范围。
- Options:
  - **A. `re.findall(r"[^\W_]+", text, re.UNICODE)`**：优——Unicode 感知，字母与数字归为词、下划线与标点作为分隔符，符合 Q4 的暂定口径；缺——对组合字符（如带变音符号的分解形式）不规范化，同形不同码位会被算作不同的词。
  - **B. `re.findall(r"[A-Za-z0-9]+", text)`**：优——行为最可预测、只覆盖 ASCII；缺——中文/带重音词会被丢弃，不满足 Q4 暂定口径。
  - **C. `text.split()` + 标点剥离**：优——简单；缺——标点与单词粘连时需二次处理，且无法自然排除下划线，违背 REQ-FUNC-005 的"仅字母/数字"定义。
- Decision: 选择 **A**。`[^\W_]` 等价于"Unicode 字母或数字"，与需求定义一致；大小写折叠在分词前用 `str.lower()` 完成（REQ-FUNC-003）。
- Consequences: 正向——一份正则同时覆盖 ASCII 与中文；负向——不处理 Unicode 规范化，同一视觉词的 NFC/NFD 两种编码可能分列（记录为开放问题 A-01，不扩范围）。

### ADR-003: 排序与并列规则

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-006 要求次数降序、同次数按词字典序升序；REQ-NFUNC-002 要求确定性。
- Options:
  - **A. `sorted(items, key=lambda kv: (-kv[1], kv[0]))`**：优——单次排序完成两个排序键，结果完全确定；缺——需对全部不同词排序（O(k log k)，k 为不同词数），不接受部分排序优化。
  - **B. `Counter.most_common(n)`**：优——实现短；缺——并列时顺序取决于插入顺序（`most_common` 对相等计数保留首次出现顺序），不满足 REQ-FUNC-006 的字典序要求，需要再补一次排序。
- Decision: 选择 **A**。`most_common` 的并列语义与需求冲突，A 用单一排序键同时满足两个条件。
- Consequences: 正向——输出与输入顺序、哈希种子无关；负向——"字典序"按 Unicode 码位比较（大写字母排在小写字母前），不是本地化排序；该行为已在 AC-003-02 中固化为可测预期。

### ADR-004: 错误处理与退出码映射

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-007 要求文件缺失/不可读时退出码 2 且 stderr 有错误；REQ-FUNC-008 要求非法 UTF-8 同样处理；正常退出码 0。
- Options:
  - **A. 核心层抛出异常，入口层统一捕获并返回整数退出码**：优——核心层可被单元测试直接调用，异常类型（`OSError`、`UnicodeDecodeError`）语义清晰；缺——入口层必须同时覆盖两类异常。
  - **B. 核心层内部 `sys.exit(2)` / 打印 stderr**：优——调用点少；缺——把进程控制埋进可复用函数，单测难以覆盖，且违反"核心层纯函数"的边界。
- Decision: 选择 **A**。`__main__.main()` 捕获 `OSError` 与 `UnicodeDecodeError`，写 stderr 并返回 2；`run()` 不捕获异常。
- Consequences: 正向——错误映射单点、可测；负向——若未来新增调用方直接调用 `run()`，需自行处理异常（记录于 module_design IFC-002 的错误契约）。

### ADR-005: 零第三方依赖

- Status: Accepted
- Type: constraint-driven
- Context: REQ-NFUNC-001；画像 P1/P6/P8。
- Options（被排除的方案）：
  - `click`/`typer`（更好的 CLI 体验）——被 REQ-NFUNC-001 与画像 P8 排除。
  - `wordfreq`/`nltk`（成品词频库）——被"仅标准库"与离线纪律排除。
- Decision: 运行时与测试断言均只用标准库 + 已装 pytest（测试工具，不进入运行时依赖）。
- Consequences: 正向——离线可跑、无供应链风险；负向——需要自行实现分词与排序（已由 ADR-002/003 覆盖）。

### ADR-006: 模块边界与文件划分

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001…008；画像 P3 指定代码根 `sandbox/trae-demo-wordfreq/src/wordfreq/`。
- Options:
  - **A. 三文件：`core.py`（纯逻辑）+ `__main__.py`（CLI 入口）+ `__init__.py`（公开 API）**：优——职责清晰，单测直接导入 core，CLI 通过 `python -m` 进入；缺——对如此小的项目略显分散。
  - **B. 单文件 `__main__.py` 包办一切**：优——文件最少；缺——参数解析与业务逻辑耦合，单元测试必须绕过 argparse，且公开 API 无处安放。
- Decision: 选择 **A**。核心逻辑与进程边界分离，是实现 ADR-004 与"每层可独立测试"的前提。
- Consequences: 正向——unit/integration/e2e 三层测试职责自然对应；负向——三个文件需保持导出同步（由 IFC-006 约束）。

## 开放问题 / ASSUMPTION

- **A-01（ASSUMPTION）** 不做 Unicode 规范化（NFC/NFD）；需求未要求，按最小实现处理。
- **A-02（ASSUMPTION）** `--top` 非正整数时按"输出 0 行、退出码 0"处理；`--min-length` < 1 时按 1 处理。需求未定义，取"不报错、不崩溃"的最小行为。
- **Q1 已落实**：输出契约为每行 `词<TAB>次数`，行间 `\n`，末尾无空行；0 个结果时 stdout 为空字符串。
- **Q4 已落实**：词按 Unicode 字母/数字识别（ADR-002）。
