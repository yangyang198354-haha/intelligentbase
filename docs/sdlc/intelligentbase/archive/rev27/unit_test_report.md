<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-31T15:48:30+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（REV-27 节点删除）

REV-26 APPROVED 版本已归档于 `archive/rev26/unit_test_report.md`。

## 摘要

- 执行时间：2026-10-31T15:41~15:48+08:00；环境：Node v22.23.3（前端）；`/root/.venvs/intelligentbase/bin/python` + `PYTHONPATH=src`（后端）；仓库根 / `src/frontend`；离线。
- 命令：`(cd src/frontend && npm run build && npm test)`；`python -m pytest tests/unit -q`。
- **本层新写用例**：total = pass + fail + skip + blocked + not_testable = 26 = 26 + 0 + 0 + 0 + 0（前端 TC-FE-R27-001~024 共 24 + 后端 TC-UNIT-R27-001~002 共 2）。
- 通过率 = pass/(pass+fail+blocked) = 26/26 = **1.00**。
- 相关既有回归：前端基线 77 个（R26 20 + 冒烟 57）全部通过，见下；后端 `tests/unit` 整层 511 passed（= 基线 509 + 新写 2）。
- 判定模式：INCREMENTAL / baseline：相对基线新增失败 **0**，新写用例全部通过。**本层门控：PASSED**。

## 执行输出

```
$ cd src/frontend && npm run build
✓ built in 26.71s           (BUILD_RC=0；仅既有 chunk > 500 kB 警告；含 vue-tsc 类型检查)
$ cd src/frontend && npm test
# tests 129
# suites 19
# pass 129
# fail 0
# cancelled 0
# skipped 0
# todo 0
$ node --test tests/config_studio_r27.test.js
# tests 52
# pass 52
# fail 0
# cancelled 0
# skipped 0
$ node --test tests/config_studio_r26.test.js tests/frontend.smoke.test.js     （基线文件）
# tests 77
# pass 77
# fail 0
# cancelled 0
# skipped 0
$ python -m pytest tests/unit -q
511 passed in 6.27s
$ python -m pytest tests/unit/test_diff_node_removal_r27.py tests/unit/test_graph_validate_r26.py tests/unit/test_config_diff_conflict_r26.py -q
47 passed in 0.32s
```

129 = 77（基线）+ 52（R27 新写：unit 24 + integration 23 + e2e 级 5）。其中 unit 层只统计 24 个，其余 28 个在后两份报告中计数，各层互不重复。

首次执行中的两处失败均为**测试写错**（非产品缺陷），已在报告冻结前修正并全量重跑：(1) TC-FE-R27-050 的"无 DOM 依赖"正则把 `state.document.` 属性访问误当 `document.` 全局，收窄为全局用法；(2) 把 `node_*` 差异项的 `field` 默认值改为服务端真实值 `'node'` 后，TC-FE-R27-024 末例期望文本同步为 `删除节点：n · node`。均 1 轮修复，未改产品代码、未弱化断言。

## 分项结果

### MOD-R27-01 `nodeRemoval.ts`（Delete 键判定 IFC-001/002）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-FE-R27-001 | AC-002-03 | `isEditableTarget` 命中 INPUT/SELECT/TEXTAREA、contenteditable、`.nokey/.el-overlay/.el-drawer/[role="dialog"]`；null 与缺方法桩不命中 | PASS | — |
| TC-FE-R27-002 | AC-002-01 | Delete + 单选 + 画布焦点 → `request` | PASS | — |
| TC-FE-R27-003 | AC-002-06 | Backspace / 其它键 → ignore | PASS | — |
| TC-FE-R27-004 | AC-007-02 | readonly → ignore（优先于多选提示） | PASS | — |
| TC-FE-R27-005 | IFC-002 规则 3 | Ctrl/Meta/Alt/Shift + Delete → ignore | PASS | — |
| TC-FE-R27-006 | AC-002-03 | 输入框 / 文本域 / 弹窗内 Delete → ignore（即便选中节点） | PASS | — |
| TC-FE-R27-007 | AC-002-02 | 无选中节点 / 仅选边 → ignore | PASS | — |
| TC-FE-R27-008 | AC-002-04 | 2 节点或 1 节点 + 1 边 → hint「请选中单个节点后再删除」 | PASS | — |

### MOD-R27-01 可行性与确认规则（IFC-003/004）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-FE-R27-009 | AC-002-05、AC-006-02 | start/end 两种模式均拒绝「开始 / 结束节点不可删除」 | PASS | — |
| TC-FE-R27-010 | AC-005-07、ASM-R27-01 | 默认专家两模式均拒绝；按专家名而非节点 id 判定 | PASS | — |
| TC-FE-R27-011 | AC-001-02、AC-006-03 | route/condition/join/confirm 可删，不检查完整性；不存在节点被拒；`REMOVABLE_KINDS` = `ADDABLE_KINDS` | PASS | — |
| TC-FE-R27-012 | AC-004-01 | 2 条边 → 需确认，文案「将同时删除 2 条边」 | PASS | — |
| TC-FE-R27-013 | AC-004-04/05/06 | 新增无边免确认；基线无边需确认且无边数；新增 + 1 边需确认 | PASS | — |
| TC-FE-R27-014 | AC-005-04 | agent canvas / definition 两套文案要素（含版本历史、无"不可恢复"） | PASS | — |

### MOD-R27-01 草稿变换（IFC-005/006/009a）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-FE-R27-015 | AC-003-01 | 删 condition-1：3 条边全删、无悬空、相邻节点逐字不变、不改入参 | PASS | — |
| TC-FE-R27-016 | AC-005-01、AC-003-02 | 仅从画布移除：experts/tool_grants/promptPatch 引用不变；路由参数与其余出边不变；顶层键顺序保持 | PASS | — |
| TC-FE-R27-017 | AC-005-05/06 | 删除定义：节点、边、experts、tool_grants、补丁全清；不改入参 | PASS | — |
| TC-FE-R27-018 | ASM-R27-01 | 节点 id ≠ 专家名：按专家名清定义，按节点 id 删节点；非 agent 走 canvas 变换 | PASS | — |
| TC-FE-R27-019 | REQ-FUNC-010 | `dropPromptPatch` 引用语义 | PASS | — |
| TC-FE-R27-020 | AC-005-01/02 | `unplacedAgents`：移除后出现、停用不出现、顺序、放回后消失 | PASS | — |
| TC-FE-R27-021 | AC-008-02、AC-011-02 | 新增后删除 → `JSON.stringify` 与基线逐字相同 | PASS | — |
| TC-FE-R27-022 | AC-009-03 | 撤销状态机三函数 | PASS | — |

### MOD-R27-03 `publishDiff.ts`

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-FE-R27-023 | AC-011-01/03 | node_added/removed/changed 带中文类型；删 join-9 与增 join-10 互不混淆；未知类型回落原代码 | PASS | — |
| TC-FE-R27-024 | NFUNC-003 | 其余 kind 与 R26 现状逐字相同；无类型代码回落旧格式 | PASS | 首跑期望文本需随 `field='node'` 同步（测试问题，已修） |

### 后端纯函数（服务端差异契约，后端未改动）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-R27-001 | AC-011-01 | 删节点 b → `node_removed(b, before='agent', after=None)`，且每条相连边各一个 `edge_removed` | PASS | — |
| TC-UNIT-R27-002 | AC-011-02 | 相同图 → 差异为空 | PASS | — |

## 与基线对比（baseline 模式）

- 前端基线 77/77/0（PM 实测，HEAD c1b491f）→ 现 129 = 77 + 52，**fail 0、新增失败 0**。
- 后端：`tests/unit` 现 511 passed（含新写 2），无失败；后端源码未改动。
- 既有失败：无。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 无 | — | — |

## 备注

- `configDraft.ts` 的离线执行使用测试内 8 行 `vue` 替身（`ref` / `computed` 仅存取语义），这意味着 Vue 响应式本身（依赖追踪、视图刷新）**未被验证**，仅验证 store 的状态机语义。
- 单元层没有产品缺陷发现；`decideDeleteKey` 的 `_graph`、`removalVerdict` 的 `_mode` 参数按契约保留但未使用（implementation_plan 已声明），不属缺陷。
