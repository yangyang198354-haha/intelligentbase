<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-31T15:51:00+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/integration_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（REV-27 节点删除）

REV-26 APPROVED 版本已归档于 `archive/rev26/e2e_test_report.md`。上一层（integration）门控 PASSED，故执行本层。

## 摘要

critical path 口径：替代（前端模型层多步旅程：真实 `nodeRemoval` / `publishDiff` / `graphModel` 产品函数 + 真实 `configDraft` store（vue 最小替身）；本机无可用无头浏览器、不得新增依赖，浏览器内交互不在其内，已列入人工验收清单）

- 命令：`(cd src/frontend && npm run build && npm test)`；`python -m pytest tests -q`（全量回归，后端未改动）。环境：Node v22.23.3；`/root/.venvs/intelligentbase/bin/python`，`PYTHONPATH=src`，离线。
- **本层用例**：total = pass + fail + skip + blocked + not_testable = 13 = 5 + 0 + 0 + 0 + 8（5 条旅程 TC-FE-R27-E01~E05 全部实跑通过；8 条浏览器 / 线上验证项为 NOT_TESTABLE，见"人工验收清单"，不计入分母）。
- critical path 覆盖率 = 有 E2E 级旅程用例的 Must Have 故事 / Must Have 故事总数 = **8 / 8 = 1.00**（US-001/003/004/005/006/007/008/010；对照见下表）。
- critical path 通过率 = pass/(pass+fail+blocked) = 5/5 = **1.00**。
- 判定模式：INCREMENTAL / baseline：全量回归相对基线**新增失败 0**，新写全部通过。**本层门控：PASSED**（测试工程师口径）。
- 须 PM 知悉：覆盖率 1.00 建立在"替代口径"之上——Must Have 故事中的浏览器内真实交互（真实 Delete 键、vue-flow 选中态、悬停卡片、1 秒响应）与线上"零影响"验证**没有被执行**，均在人工清单中；AC-008-01 的"1 秒内"、REQ-NFUNC-001 沿用 R26 INF-5，目标机校准前"未验收"。

### Must Have 故事 → 旅程用例

| 故事 | 旅程用例 | 另有支撑 |
|---|---|---|
| US-001 直接删未完成节点 | TC-FE-R27-E03 | TC-FE-R27-011、031 |
| US-003 删节点清边、校验留给保存 | TC-FE-R27-E01 | TC-FE-R27-015、030；校验由 TC-UNIT-R26-003/005/011（既有）|
| US-004 确认规则 | TC-FE-R27-E01、E03 | TC-FE-R27-012、013、037 |
| US-005 两种移除 | TC-FE-R27-E02 | TC-FE-R27-016、017、032、033、036 |
| US-006 开始 / 结束不可删 | TC-FE-R27-E04 | TC-FE-R27-009、055 |
| US-007 查看档不能删 | TC-FE-R27-E04 | TC-FE-R27-004、054；服务端 TC-INT-R26-070（既有）|
| US-008 画布 / 面板 / 未保存一致 | TC-FE-R27-E03 | TC-FE-R27-031、038、053 |
| US-010 只改草稿、不破坏既有 | TC-FE-R27-E05 | TC-FE-R27-051、057、058；既有 77 个前端用例 |

## 全量回归

```
$ cd src/frontend && npm run build
✓ built in 26.71s     (BUILD_RC=0)
$ cd src/frontend && npm test
# tests 129
# suites 19
# pass 129
# fail 0
# cancelled 0
# skipped 0
# todo 0
$ python -m pytest tests -q          （仓库根，后端未改动；无关回归）
910 passed in 28.99s
  其中 tests/unit 511、tests/integration 333、tests/e2e 51、tests/agents 15；910 = 908 既有 + 2 新写（TC-UNIT-R27-001/002）
$ python -m pytest tests/agents -q
15 passed
```

- 前端：基线 77/77 → 现 129/129（+52 新写），相对基线新增失败 **0**。
- 后端：908 个既有用例全部通过，新增失败 **0**；`selfcheck` 与 compileall 未执行（后端未改动，不在本任务范围）。
- 新增失败逐条列表：无。

## 用户旅程

> 说明：旅程在模型层执行——输入事件用 `decideDeleteKey` 的参数对象表达（桩对象代替 DOM 事件目标），`window.confirm` 以回调代替，store 为真实代码。表中"实际响应"为断言实测值（用例全部通过）。

### TC-FE-R27-E01: 删除带边的条件分支节点（取消 → 确认 → 载荷 → 差异行 → 撤销）
- 关联：US-002 AC-002-01、US-003 AC-003-01、US-004 AC-004-01/02/03、US-009 AC-009-01、US-011 AC-011-01；环境：Node 22 离线。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 选中 condition-1，按 Delete（焦点在画布） | `{action:'request', nodeId:'condition-1'}` | 同期望 | PASS |
| 2 | 请求删除，确认框点"取消" | 文案含「将同时删除 3 条边」；快照与基线逐字相同 | 同期望 | PASS |
| 3 | 再次请求，点"确认" | 节点与 3 条边消失；无悬空边；route-1 / kb-agent / end 仍在；dirty=true | 同期望 | PASS |
| 4 | 取保存载荷与差异行 | 载荷图不含 condition-1；`formatDiffLine(node_removed, condition)` =「删除 条件分支节点：condition-1」 | 同期望 | PASS |
| 5 | 撤销 | 快照 = 基线；dirty=false | 同期望 | PASS |
- 结论：PASS

### TC-FE-R27-E02: agent 的两种移除与撤销
- 关联：US-005 AC-005-01~05、US-009 AC-009-02；环境同上。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | billing-agent（含主提示词草稿）"仅从画布移除" | 文案「从画布移除」；出现在"尚未上图" | 同期望 | PASS |
| 2 | 重新上图 | 提示词草稿不变 | 同期望 | PASS |
| 3 | "删除 agent" | 文案含「移除其定义与工具授权」；重新上图的节点无边（edgeCount=0）；补丁清空；不在"尚未上图" | 同期望 | PASS |
| 4 | 撤销 | 补丁与专家定义恢复 | 同期望 | PASS |
- 结论：PASS

### TC-FE-R27-E03: 未完成节点逐个直接删除，其它改动保留
- 关联：US-001 AC-001-01/02、US-004 AC-004-04、US-008 AC-008-03；环境同上。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 新增 condition / join / confirm，并改 kb-agent 最大步数为 3 | dirty=true | 同期望 | PASS |
| 2 | 删除 condition-2、confirm-1 | 均成功，确认回调从未被调用；不出现校验拦截 | 同期望 | PASS |
| 3 | 删除 join-1 | 成功；dirty 仍为 true；最大步数仍为 3 | 同期望 | PASS |
- 结论：PASS

### TC-FE-R27-E04: 全部拒绝路径下草稿与"未保存"不变
- 关联：US-002 AC-002-04/05、US-005 AC-005-07、US-006 AC-006-02/03、US-007 AC-007-02；环境同上。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 多选 route-1 + join-9 按 Delete | hint「请选中单个节点后再删除」 | 同期望 | PASS |
| 2 | 查看档按 Delete | ignore | 同期望 | PASS |
| 3 | 对 start / end / kb-agent 按 Delete 并请求删除 | 均被拒，原因为「开始 / 结束节点不可删除」或「默认专家不能删除，请先指定其他默认专家」；快照不变、dirty=false | 同期望 | PASS |
| 4 | 查看档请求删除 route-1 | 不执行；无撤销位 | 同期望 | PASS |
| 5 | 编辑档删除 route-1 | 允许；无悬空边；`route.default_expert` 仍为 kb-agent | 同期望 | PASS |
- 结论：PASS

### TC-FE-R27-E05: 删除后保存成功，基线更新、撤销失效
- 关联：US-010 AC-010-04、US-009 AC-009-03；环境同上。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 删除 condition-1 | dirty=true；载荷图不含该节点 | 同期望 | PASS |
| 2 | `markSaved(8)`（模拟保存成功） | baseVersion=8；dirty=false；canUndo=false；该节点不再属基线；补丁清空 | 同期望 | PASS |
- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| — | — | 本轮未发现产品缺陷 | — | — |

观察项（非缺陷）：
- `decideDeleteKey` 的 `_graph` 与 `removalVerdict` 的 `_mode` 为按契约保留的未使用参数（implementation_plan 已声明）。
- ASM-R27-02：1 节点 + 1 边混选时，节点不删并提示，被选中的边仍由 vue-flow 既有行为删除，属设计内行为，需人工确认体验可接受（M-05）。

## 人工验证清单（上线后人工浏览器验收清单）

以下 8 项在本环境无法执行，计数为 NOT_TESTABLE（不计入通过率分母）；对应 Must Have 的项已标 critical path。所需环境：已部署新前端的真实浏览器（Chrome / Edge），编辑档账号 + 查看档账号各一个，一个含 ≥ 3 个 agent 的测试项目。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-002-01、风险 R-1（GR-B-001 a） | 编辑档打开配置页；新增 route 节点；点击选中它；将焦点留在画布；按 Delete。再对"已存在、拖动过一次的节点"重复；再在**删除另一个节点后**立刻选中第三个节点按 Delete | 每次均只删除被选中的那个节点；删除后下一个选中节点再按 Delete 仍生效（选中态未因图更新丢失）；不出现脚本报错 | 真实浏览器 + 编辑档账号 | 是（US-002 Should，US-004 Must 的触发入口） |
| M-02 | AC-002-03、AC-002-06 | 选中 condition 节点；点击右侧"关键词"文本框，在有文字时按 Delete 与 Backspace；再点击空白画布后按 Backspace | 文本框内仅删除字符，节点仍在、"未保存"不因节点被删而变化；画布上按 Backspace 不删除节点 | 同上 | 否（Should） |
| M-03 | AC-008-01、REQ-NFUNC-001（INF-5，目标机校准） | 鼠标悬停某节点使卡片显示；保持悬停并点击右侧"删除节点"（确认）；在 30 节点图上用秒表或录屏测删除到画布更新的耗时 | 节点消失、悬停卡片消失、右侧面板回到"点击画布上的节点查看或编辑其配置"；耗时 ≤ 1 秒。校准前该项仍记"未验收" | 目标机浏览器 + 屏幕录制 | 是（US-008 Must） |
| M-04 | AC-002-04 | 按住 Shift 或 Ctrl 多选 2 个节点，按 Delete | 两个节点都不删，出现提示「请选中单个节点后再删除」 | 同 M-01 | 否（Should） |
| M-05 | ASM-R27-02（GR-B-001 b） | 选中 1 个节点 + 1 条边（多选），按 Delete | 节点不删并出现多选提示；被选中的那条边是否被 vue-flow 删除——按设计应删除；记录实际现象，由 PM / 用户判断体验是否可接受 | 同 M-01 | 否 |
| M-06 | AC-007-01/02、AC-009-05 | 用查看档账号打开配置页，逐个点击节点；选中节点按 Delete | 详情面板无"删除节点""删除 agent"；节点保留；无撤销条；"未保存"不出现 | 查看档账号 | 是（US-007 Must） |
| M-07 | AC-010-01、AC-010-02 | 记录当前版本号 N 与审计列表条数；编辑档删除线上 billing-agent 的节点（不点保存）；另开无痕窗口以终端用户身份提问含"发票"；回到编辑页点"保存并生效"再点"取消" | 版本号仍为 N、审计无新记录；提问仍路由到 billing-agent；取消后草稿（已删除状态）保留在页面上 | 目标机 + 终端用户账号 | 是（US-010 Must） |
| M-08 | AC-005-03、AC-005-04、AC-005-05、AC-004-01~06（真实弹窗） | 对 billing-agent：先"删除节点"（确认框应为"从画布移除"文案）并保存，检查项目提示词目录中其主提示词文件仍在；再放回画布后"删除 agent"（确认框应写明移除定义与工具授权、边数、提示词文件保存后移除、版本历史可回滚）并保存，检查提示词文件被移除、历史会话仍显示其名称；各场景目视确认真实 `window.confirm` 的取消 / 确认行为 | 文案与 AC 一致；两次保存后的目录与历史会话表现与 AC-005-03 / 005-05 一致；"版本历史"回滚可找回 | 目标机 + 服务器文件检查权限 | 是（US-005 Must） |

## 本层局限（如实）

1. 旅程为模型层串联，不含 DOM、vue-flow 与 Vue 响应式；"通过"证明产品函数与 store 状态机的语义与 AC 一致，不证明浏览器中的交互。
2. `configDraft` 离线执行借助测试内 `vue` 最小替身；`requestRemove` 无导出，由测试内 `drive()` 按 IFC-R27-011 复刻并由 TC-FE-R27-057 以顺序断言绑定到源码。
3. 服务端行为（校验错误、403、差异）依赖既有 R26 用例与 2 个新写后端纯函数用例，未做端到端 HTTP 联调（后端本轮未改动）。
