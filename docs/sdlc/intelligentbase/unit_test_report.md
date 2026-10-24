<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-24T23:25:21+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>user_stories.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>module_design.md</file>
    <file>test_plan.md</file>
    <file>phase_status.md</file>
    <file>implementation_plan.md（2.0.0）</file>
    <file>code_review_report.md（2.0.0）</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，intelligentbase-GROUP_D-001）

## 摘要

- 执行时间：2026-10-24T23:22 起（缺陷回流复测，本层最后一次执行；0.1.0 初测为 22:41）；环境：`/root/.venvs/intelligentbase/bin/python`（Python 3.12.3、pytest 9.1.1、Django 6.0.9），`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`，仓库根运行。
- 命令：`python -m pytest tests/unit -q`
- 计数行（原文）：`314 passed in 19.68s`
- **total = pass + fail + skip + blocked + not_testable = 314 = 314 + 0 + 0 + 0 + 0**
- 其中 既有 194（基线 `tests/unit`，含已同步断言的 TC-UNIT-019、TC-UNIT-070）+ 新写 120（pytest 收集项；对应 81 个 TC-UNIT-R25 编号，参数化展开：名称 +7、目录树 内存/SQLite 与参数 +25、计划 +2、配置 +5）。
- 通过率 = pass/(pass+fail+blocked) = 314/(314+0+0) = **1.00**；判定模式 baseline（相对基线零新增失败且新写用例全部通过）。
- **本层门控：PASSED**（既有失败 0；新增失败 0；新写 120/120 通过；GR-C-001 条件 1 中的 2 处单元断言已同步）。

## 缺陷回流复测（defect_loops=1，GR-D-001 / GR-C-002）

- 本层测试文件在回流中**未改动**（DEF-R25-001/002 的复测用例在集成层与前端冒烟层）；仅在产品修复后重跑，结果 314 passed，与初测数字一致（`314 = 314 + 0 + 0 + 0 + 0`）。
- 基线对比：相对基线零新增失败；新写 120/120 仍通过。
- 命令与计数行见下方"执行输出"（已更新为复测的最后一次执行）。

## 执行输出

```
$ python -m pytest tests/unit --collect-only -q | grep -cE '::'
314
$ python -m pytest tests/unit -q
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 68%]
........................................................................ [ 91%]
..........................                                               [100%]
314 passed in 19.68s
```

辅助检查（不并入本层算术）：`python -m compileall -q src` → 退出码 0；`python -m pytest tests/agents -q` → `21 passed in 0.08s`。

## 过时断言同步（GR-C-001 条件 1，单元部分）

只把旧契约改为新契约（`doc_path` 为已批准设计 REQ-FUNC-014 / MOD-005 新增键）；强度均高于原断言，未删用例、未放宽。

| 位置 | 改前断言 | 改后断言 |
|---|---|---|
| `tests/unit/test_core_config_chunk_parse_stream.py:300`（TC-UNIT-019） | `set(decoded["images"][0]) == {"image_id","doc_id","doc_name","page_or_section","url_path"}`（精确键集 5 键） | `set(decoded["images"][0]) == {…同 5 键…, "doc_path"}`（精确键集 6 键），并新增 `decoded["images"][0]["doc_path"] == ""`（未提供目录路径时为空串） |
| `tests/unit/test_stream_session_lifecycle_unit_r12.py:86`（TC-UNIT-070） | `cite == {"doc_id","doc_name","page_or_section","locator","score"}`（字典全等 5 键） | `cite == {…同 5 键…, "doc_path": ""}`（字典全等 6 键），并新增成对用例：携带 `doc_path="技术文档/设计/方案.pdf"` 的引用经 `completion_event` 输出后 `citations[0]["doc_path"]` 原样等于该路径 |

（集成层的第 3 处 `TC-INT-044` 见集成报告；前端第 4 处见 E2E 报告"前端冒烟"。）

## 分项结果

按模块分组；全部新写用例（含参数化展开项）均 PASS，无失败、无跳过、无 BLOCKED。docstring 中"[TC-…]"即用例编号，"AC-…"即溯源。

#### 名称规则 / 比对键 / 自动改名（MOD-001，`test_folder_names_unit_r25.py`，13 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-001 | AC-016-01 | AC-016-01：空白 / 含 / 或 \\ / 超过 255 字符 → 拒绝并给出稳定错误码。 | PASS | — | — |
| TC-UNIT-R25-002 | AC-016-02 | AC-016-02：合法名称（含空格、中文、恰 255 字符）通过，且 strip 后返回展示名。 | PASS | — | — |
| TC-UNIT-R25-003 | AC-011-05、AC-016-03 | AC-016-03 / AC-011-05：`Design`/`design`/`DESIGN`、`A.pdf`/`a.pdf` 同键；NFC 等价同键；不同名不同键。 | PASS | — | — |
| TC-UNIT-R25-004 | AC-011-02 | AC-011-02：文件 `a.pdf` → `a (2).pdf`，被占用则 `a (3).pdf`；文件夹 `A` → `A (2)`；原名未占用原样返回。 | PASS | — | — |
| TC-UNIT-R25-005 | （专项/偏差） | 边界：改名后超 255 字符时截断主名、保留扩展名与序号（结果仍 ≤255）。 | PASS | — | — |
| TC-UNIT-R25-006 | AC-014-01 | AC-014-01/02：目录路径 `a/b/文件`；根目录文件仅文件名，无空前缀或多余 `/`。 | PASS | — | — |

#### 007 迁移（MOD-001 / MOD-015，`test_folder_schema_migration_unit_r25.py`，6 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-040 | （专项/偏差） | 画像 P6 单源：007_folder_tree.sql 去空白后包含 `folder_tree_ddl_script()`（与 CI 003 检查同口径）；001~006 在 H | PASS | — | — |
| TC-UNIT-R25-041 | （专项/偏差） | 新库：ensure_schema 连续两遍快照一致；007 快照在其后重放两遍无副作用；四张新表与 6 个新列、3 个唯一索引齐备。 | PASS | — | — |
| TC-UNIT-R25-042 | AC-017-01 | AC-017-01（数据层）：001 形态老库升级后 —— 全部 N=5 行在根目录（folder_id=''）、名称 / 状态 / 大小不变； | PASS | — | — |
| TC-UNIT-R25-043 | （专项/偏差） | M-TE-006：老库连续 ensure_schema 两遍（模拟 ib-web 与 ib-worker 各启动一次），快照逐行一致；回填不重复追加后缀。 | PASS | — | — |
| TC-UNIT-R25-044 | （专项/偏差） | 并发补列容错：列已被他人补上时 `_ensure_document_tree_columns` 不抛、不重复（duplicate column name 被容忍）。 | PASS | — | — |
| TC-UNIT-R25-045 | AC-011-05、AC-016-03 | AC-011-05 / AC-016-03 的数据库兜底：同目录 name_key 重复被拒；修订行（name_key=''）不占名；同一存活行至多一个修订行。 | PASS | — | — |

#### 目录树存储与目录服务（MOD-002 / MOD-006，`test_folder_tree_store_unit_r25.py`，45 项 = 内存 / SQLite 参数化）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-010 | AC-004-01 | AC-004-01：在目录 D 新建 `设计` → D 下立即出现且为空；重新读取仍存在。 | PASS | — | — |
| TC-UNIT-R25-011 | AC-004-02、AC-016-03 | AC-004-02 / AC-016-03：同名（含仅大小写不同）新建与重命名均 409，目录下仍只有原条目、原名不变。 | PASS | — | — |
| TC-UNIT-R25-012 | AC-004-03 | AC-004-03：根下一级 = 第 1 层，第 10 层目录内再建 → 拒绝（depth_exceeded）；第 10 层本身可建。 | PASS | — | — |
| TC-UNIT-R25-013 | AC-016-01、AC-016-02 | AC-016-01 / AC-016-02：非法名称新建与重命名都被拒绝，且不创建 / 不修改任何条目。 | PASS | — | — |
| TC-UNIT-R25-014 | AC-003-02 | AC-003-02：150 个条目分页（≤100/页）无重复无遗漏，文件夹在前再按名称升序；多次读取顺序一致；page_size 截断到 100。 | PASS | — | — |
| TC-UNIT-R25-015 | AC-003-01 | AC-003-01：A/B 的面包屑依次为 [A]、[A,B]；不存在的目录 id → NotFoundError。 | PASS | — | — |
| TC-UNIT-R25-016 | AC-003-03 | AC-003-03：P1 以 P2 的目录 id 访问 → NotFoundError，与不存在的 id 不可区分（异常类与消息均相同）。 | PASS | — | — |
| TC-UNIT-R25-017 | AC-005-01 | AC-005-01：重命名文件夹后其内 3 个已索引文件仍在其中、仍为 indexed；检索引用路径为 `新名/…`，不再出现旧名。 | PASS | — | — |
| TC-UNIT-R25-018 | AC-012-01、AC-012-02 | AC-012-01 / AC-012-02：文件重命名后状态与三时间不变、引用显示新名；同目录重名 409；任何扩展名变化（含改为另一受支持类型）400 且名称不变。 | PASS | — | — |
| TC-UNIT-R25-020 | AC-013-01、AC-013-02 | AC-013-01 / AC-013-02：移动文件与整个文件夹后原位置无、新位置有，状态仍 indexed，检索命中数不变且路径同步为新位置。 | PASS | — | — |
| TC-UNIT-R25-021 | AC-013-04 | AC-013-04：移动到自身 / 子孙、超 10 层均拒绝（move_into_self / depth_exceeded），原结构不变。 | PASS | — | — |
| TC-UNIT-R25-021b | AC-013-04 | AC-013-04（跨项目）：目标目录属于其他项目 → 拒绝（NotFoundError，与不存在不可区分，A-10 / CL-010），原结构不变；他项目的目录也不被改动。 | PASS | — | — |
| TC-UNIT-R25-022 | AC-013-03 | AC-013-03：目标有同名条目且未给处理方式 → 409 并带冲突列表，台账完全不变（含同批无冲突条目也不移动）。 | PASS | — | — |
| TC-UNIT-R25-023 | AC-011-02、AC-013-03 | AC-013-03 / AC-011-02：移动冲突选 skip → 不动；选 rename → `x (2).txt`；移到当前所在目录视为 skipped。 | PASS | — | — |
| TC-UNIT-R25-024 | （专项/偏差） | 偏差 D-06（文件）：移动冲突选“覆盖” → 目标侧同名文件被替换（移出台账并清理向量），来源文件原样落到目标，检索旧内容命中 0。 | PASS | — | — |
| TC-UNIT-R25-025 | （专项/偏差） | 偏差 D-06（文件夹）：移动冲突选“覆盖” → 两个同名文件夹合并为一个；同名文件被替换，目标侧独有文件、来源独有文件、子文件夹（递归合并）全部保留，来源文件夹消失。 | PASS | — | — |
| TC-UNIT-R25-026 | （专项/偏差） | 偏差 D-06 边界：文件与文件夹之间不能互相覆盖 → bad_request，台账不变。 | PASS | — | — |
| TC-UNIT-R25-030 | AC-006-01 | AC-006-01：子树计数 = 2 个子文件夹、10 个文件（不含修订行）；resolve_live 返回当前目录路径，不存活 id 不在结果中。 | PASS | — | — |
| TC-UNIT-R25-031 | （专项/偏差） | 偏差 D-03：`list_documents(include_revisions)` —— 默认（True）含修订行（重建口径）；False 不含；存活行两种口径都在。 | PASS | — | — |
| TC-UNIT-R25-032 | （专项/偏差） | 偏差 D-03（端口一致性）：`LedgerRepository.list_documents` 端口、SQLite 实现与内存实现的参数名集合一致且含 include_revis | PASS | — | — |

#### 批量上传计划与受理（MOD-007，`test_folder_upload_plan_unit_r25.py`，21 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-050 | AC-015-01 | AC-015-01：默认配置 1001 个文件 → limit_files（limit=1000, actual=1001），不产生批次 / 目录 / 文件；恰 1000 个通过。 | PASS | — | — |
| TC-UNIT-R25-051 | AC-015-02 | AC-015-02：目标在第 8 层、所选文件夹嵌套 3 层 → 最深第 11 层，整体拒绝；同一文件夹从第 7 层上传（最深第 10 层）通过。 | PASS | — | — |
| TC-UNIT-R25-052 | AC-015-03 | AC-015-03：上限配置为 20 层 / 2000 个文件时，1500 个文件、15 层的文件夹通过校验；单文件 50MB 上限仍适用（超限者被跳过）。 | PASS | — | — |
| TC-UNIT-R25-053 | AC-015-04 | AC-015-04：总大小上限 L（配置 1MB）—— 超过 L 整体拒绝（details 含上限与实际），不产生批次 / 目录 / 文件；总大小恰为 L 通过。 | PASS | — | — |
| TC-UNIT-R25-054 | AC-002-02 | AC-002-02：95 合规 + 3 个不支持类型 + 1 个空文件 + 1 个超 50MB → 接受 95、跳过 5、三数之和 100；跳过原因分别为 UNSUPPORTED_ | PASS | — | — |
| TC-UNIT-R25-055 | AC-002-02 | AC-002-02（魔数）：扩展名 .pdf 但内容不是 PDF → 逐文件受理时记“跳过”（MAGIC_MISMATCH），汇总 failed=0 且三数之和 = 总数；不入库。 | PASS | — | — |
| TC-UNIT-R25-056 | AC-001-01 | AC-001-01：上传 A/x.txt 与 A/B/y.txt → 目标目录下出现 A（含 x.txt 与子文件夹 B），B 内含 y.txt；层级与本地一致。 | PASS | — | — |
| TC-UNIT-R25-057 | AC-001-04 | AC-001-04：A 含合规 x.txt、全部被跳过的子文件夹 A/onlybad（z.exe）与魔数失败的 A/fake（q.pdf）→ 只创建 A（内含 x.txt），A 下 | PASS | — | — |
| TC-UNIT-R25-058 | AC-002-03 | AC-002-03：服务端临时错误（blob 不可用）→ 该项记 failed 并上抛，其余项不受影响；对同 idx 重试成功后 failed 变 accepted；汇总三数之和  | PASS | — | — |
| TC-UNIT-R25-059 | （专项/偏差） | 服务端权威：重复 PUT 返回既有终态不重复入库；实际字节数 > 声明 → 跳过 SIZE_MISMATCH（累计实际 ≤ 声明和 ≤ 总上限）。 | PASS | — | — |
| TC-UNIT-R25-060 | （专项/偏差） | REQ-NFUNC-005：他项目 / 不存在的批次与批次项 → NotFoundError（不可区分）。 | PASS | — | — |
| TC-UNIT-R25-061 | AC-011-01、AC-011-04 | AC-011-01 / AC-011-04：D 已有 a.txt，再传 a.txt → dry-run 列出冲突，原文件内容 / 状态 / 向量不变；commit 但未选择 → 4 | PASS | — | — |
| TC-UNIT-R25-062 | AC-011-02 | AC-011-02：覆盖 → 按“更新”处理（target=原 doc）；跳过 → 不入库并计入跳过；两者保留 → 新文件改名 `a (2).txt`。 | PASS | — | — |
| TC-UNIT-R25-063 | AC-011-02 | AC-011-02：`a (2).txt` 已存在时，自动改名顺延为 `a (3).txt`；原 a.txt 不变。 | PASS | — | — |
| TC-UNIT-R25-064 | AC-011-05 | AC-011-05：D 已有 A.txt，上传 a.txt（仅大小写不同）→ 同样列出冲突，选择前不出现 a.txt；选“两者保留”→ `a (2).txt`，A.txt 不变。 | PASS | — | — |
| TC-UNIT-R25-065 | AC-011-03 | AC-011-03：上传文件夹 A，目标已有同名文件夹 A（含 x.txt、other.txt）——选“覆盖”合并为一个 A；x.txt 冲突仍需单独确认并按更新处理；other. | PASS | — | — |
| TC-UNIT-R25-066 | AC-011-03 | AC-011-03 的其余分支：文件夹选“两者保留”→ 整棵子树改用 `A (2)`；选“跳过”→ 整棵子树 USER_SKIPPED。 | PASS | — | — |
| TC-UNIT-R25-067 | AC-007-01 | AC-007-01：一次选择 3 个合规文件上传到目录 D → D 下出现这 3 个文件，初始“待处理”，根目录下不出现。 | PASS | — | — |
| TC-UNIT-R25-068 | AC-007-02 | AC-007-02：混选中 1 个不支持类型 → 其余正常入库，不支持者给出原因并不入库。 | PASS | — | — |

#### 更新 / 三个时间 / 检索存活过滤 / 分步删除 / 清理队列（MOD-004/005/006，`test_folder_lifecycle_revision_unit_r25.py`，20 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-070 | AC-008-01、AC-008-02 | AC-008-01 / AC-008-02：更新提交后、新版索引完成前，旧版 K1 仍可检索（新版 K2 尚不可检索）；索引成功后 K2 命中、K1 命中 0、列表仅一条记录、目录 | PASS | — | — |
| TC-UNIT-R25-071 | AC-008-03 | AC-008-03（反例）：新版索引失败 → 状态“更新失败”+ 原因码，旧版仍 indexed 且 K1 仍可检索、K2 不可检索； | PASS | — | — |
| TC-UNIT-R25-072 | AC-008-03 | AC-008-03 / ADR-004：失败的更新可丢弃（旧版不受影响）；parsing 中的更新不可丢弃（update_in_progress）；存活行 pending 时不可更 | PASS | — | — |
| TC-UNIT-R25-073 | AC-008-05 | AC-008-05：用不同格式 / 不同名的新文件更新 —— 被接受；条目显示新文件名（含新扩展名），目录与上传时间不变，K2 命中、K1 为 0。 | PASS | — | — |
| TC-UNIT-R25-074 | AC-008-06 | AC-008-06：内容与现有完全相同 → changed=False，不建修订行；状态、索引成功时间、最近更新时间、向量数均不变。 | PASS | — | — |
| TC-UNIT-R25-075 | AC-008-07 | AC-008-07：用 `规范V2.MD`（与同目录另一条目 `规范v2.md` 仅大小写不同）更新 `规范.txt` —— | PASS | — | — |
| TC-UNIT-R25-076 | AC-009-01、AC-009-02 | AC-009-01 / AC-009-02：上传 T1、索引成功 T2（T2≥T1）、从未更新 → 最近更新为 null；更新于 T3、索引成功 T4 → 上传仍 T1、更新 T3 | PASS | — | — |
| TC-UNIT-R25-077 | AC-009-03 | AC-009-03：失败的文件状态为 failed、带原因码、索引成功时间为 null；处理中 / 待处理同样为 null。 | PASS | — | — |
| TC-UNIT-R25-078 | AC-009-04 | AC-009-04：embedding 变更后重建重新索引完成于 T5 → 索引成功时间 = T5（不再是 T2），上传时间仍 T1，最近更新仍为 null，状态 indexed， | PASS | — | — |
| TC-UNIT-R25-080 | （专项/偏差） | 正例：依赖齐备 → degraded=False 且有命中；命中的名称 / 路径 = 台账当前值（目录路径含目录链）。 | PASS | — | — |
| TC-UNIT-R25-081 | （专项/偏差） | 正例（空结果 ≠ 故障）：命中全部不存活（台账行已删、向量成孤儿）→ degraded=False 且 hits==[]。 | PASS | — | — |
| TC-UNIT-R25-082 | （专项/偏差） | 反例：存活解析故障 → degraded=True，原因 LEDGER_UNAVAILABLE，hits==[]（fail-closed，不返回未核验命中）；与 080 正例成对（ | PASS | — | — |
| TC-UNIT-R25-083 | （专项/偏差） | 兼容：未注入 entry_resolver 时与基线一致（不过滤、不回填路径）——孤儿向量仍被返回，doc_path 为空串。 | PASS | — | — |
| TC-UNIT-R25-084 | AC-010-03 | AC-010-03：索引失败的文件检索无命中，列表中状态为“失败”（不是已索引）；成对：同批次的正常文件可检索。 | PASS | — | — |
| TC-UNIT-R25-090 | AC-006-01、AC-006-02 | AC-006-01 / AC-006-02：删除前 detail 给出“2 个子文件夹、10 个文件”且不改任何数据；确认删除后目录与文件全部消失， | PASS | — | — |
| TC-UNIT-R25-091 | AC-006-03 | AC-006-03（反例）：1 个文件向量清理失败 → failed 列出该文件（稳定错误码，不含异常文本），其余删除；该文件及其目录链仍可见（可再次删除）， | PASS | — | — |
| TC-UNIT-R25-092 | （专项/偏差） | ADR-008：每步最多 max_files 个文件，done=False 时重复调用可续；最终 done=True（无状态、可恢复）。 | PASS | — | — |
| TC-UNIT-R25-093 | AC-006-04 | AC-006-04：文件正处于“处理中”时确认删除 → 删除成功，该文件不在列表也不在向量库；随后 worker 对该（已被删除的）行的处理安全退出，不崩溃、不重新写入向量。 | PASS | — | — |
| TC-UNIT-R25-094 | （专项/偏差） | MOD-004：删除带在途修订行的存活文件 → 修订行与存活行一并删除（向量→blob→台账），检索 K1/K2 均为 0。 | PASS | — | — |
| TC-UNIT-R25-095 | （专项/偏差） | 清理队列故障：向量清理失败 → 队列项保留且 attempts+1，不外抛；期间孤儿向量对检索不可见；恢复后出队、向量物理消失（成对）。 | PASS | — | — |

#### 配置 D-04 / 批次存储 / worker 周期动作（MOD-003/009/011，`test_folder_config_batch_worker_unit_r25.py`，15 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-R25-100 | AC-015-01 | MOD-009 / AC-015-01：默认 单次 1000 个文件、总大小 1024MB、10 层、批次 TTL 24 小时（总大小默认值只在配置一处）。 | PASS | — | — |
| TC-UNIT-R25-101 | （专项/偏差） | 偏差 D-04：越界（低于下界 / 高于上界）或非整数 → `ConfigError`（异常类型即 D-04 的实际口径，非设计字面 StartupError），携带键名，消息不回 | PASS | — | — |
| TC-UNIT-R25-102 | （专项/偏差） | 偏差 D-04（启动期 fail-fast）：`build_deps` 遇到越界配置同样抛 ConfigError（进程起不来），不是静默回落默认值。 | PASS | — | — |
| TC-UNIT-R25-103 | （专项/偏差） | 环境变量映射：四个新键登记在 `IB_RUNTIME_ENV_KEYS`，可由环境变量覆盖。 | PASS | — | — |
| TC-UNIT-R25-104 | （专项/偏差） | ADR-003：`max_upload_mb > 60` 记 WARNING（error_code=max_upload_mb_exceeds_proxy_limit）但取值不变； | PASS | — | — |
| TC-UNIT-R25-105 | （专项/偏差） | 批次汇总恒等：accepted+skipped+failed+pending == total；skip 项初始即 skipped；终态幂等（重复 mark 不改变）；failed | PASS | — | — |
| TC-UNIT-R25-106 | （专项/偏差） | 批次按项目隔离（他项目 get → None、summarize → NotFoundError）；TTL 到期后 purge_expired 清理批次及其项（未到期不清理）。 | PASS | — | — |
| TC-UNIT-R25-110 | （专项/偏差） | 正例：run_once 摘要含 promoted / purged / batches_expired；清理队列中的项被排空；到期批次被清理（batches_expired==1） | PASS | — | — |
| TC-UNIT-R25-111 | （专项/偏差） | 反例：补晋升 / 清理排空 / 批次清理任一抛异常，run_once 都不外抛，其余动作照常执行（隔离）；对应计数保持 0。与 110 正例成对。 | PASS | — | — |
| TC-UNIT-R25-112 | （专项/偏差） | M-SA-018：已知项目集合 = 注册表活动项目 ∪ deps.projects（运行期新建项目只在注册表）；注册表读失败时只用回退集合，不抛。 | PASS | — | — |


### 偏差 D-03 / D-04 / D-06 专项（GR-C-001 条件 3）结果

| 偏差 | 用例 | 结果 |
|---|---|---|
| D-03 `list_documents(include_revisions)`：默认 True 含修订行、False 排除、存活行两口径都在；端口 / SQLite / 内存签名与默认值一致 | TC-UNIT-R25-031（内存 + SQLite）、TC-UNIT-R25-032 | PASS |
| D-04 越界 / 非整数配置抛 `ConfigError`（键名、不回显值）；边界值合法；`build_deps` 启动期 fail-fast | TC-UNIT-R25-101（4 键参数化）、TC-UNIT-R25-102 | PASS |
| D-06 移动冲突选"覆盖"：文件 = 目标文件被替换（移出台账、向量清理、检索 0 命中）；文件夹 = 递归合并（同名文件替换、独有文件保留、同名子文件夹合并）；跨类互相覆盖 400 | TC-UNIT-R25-024/025/026（内存 + SQLite） | PASS |

## 与基线对比（baseline 模式）

| 项 | 基线（HEAD 65490cf，PM 实测） | 本次 | 说明 |
|---|---|---|---|
| tests/unit 通过数 | 194（推算：当前分层收集数减新写数；与 PM 实测全量 436 = unit 194 + integration 192 + e2e 29 + agents 21 吻合） | 314 | = 194 + 120 新写 |
| 失败 | 0 | 0 | PM 在改动后工作区复跑的 2 处单元失败（TC-UNIT-019、TC-UNIT-070）已按 GR-C-001 条件 1 同步并通过 |

既有失败：无。新增失败：0。

## 失败汇总（需路由给开发）

无（本层 0 失败）。本轮发现的产品缺陷在集成层登记（DEF-R25-001、DEF-R25-002），见集成报告。
