<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-31T15:32:00+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files><file>docs/sdlc/intelligentbase/module_design.md</file><file>docs/sdlc/intelligentbase/architecture_design.md</file><file>docs/sdlc/intelligentbase/requirements_spec.md</file><file>docs/sdlc/intelligentbase/user_stories.md</file><file>docs/sdlc/intelligentbase/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — REV-27 节点删除（纯前端）

## 实现概览
MOD-R27-01~06 共 6 个模块，7 个文件（2 新建、5 修改），均在 `src/frontend/src/`。MOD-R27-07（测试）归 GROUP_D，本轮未写。拓扑序：01（nodeRemoval.ts）→ 02（configDraft.ts）/ 03（publishDiff.ts + PublishDialog）→ 04（FlowCanvas）→ 05（AgentDetailPanel）→ 06（ConfigStudio）。无后端、依赖清单、package*.json、ci.yml 改动。

## 改动清单（按拓扑顺序）
| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-R27-01 | components/config/nodeRemoval.ts | 新建 | graphModel | M | IFC-001~006、009a 纯函数与常量 | DONE |
| 2 | MOD-R27-02 | stores/configDraft.ts | 修改 | 01 | L | applyRemoval/undoRemoval/canUndo/undoLabel/isBaselineNode；load/discard/markSaved 清撤销位 | DONE |
| 3 | MOD-R27-03 | components/config/publishDiff.ts | 新建 | graphModel | L | formatDiffLine（node_* 三类带中文类型，其余逐字不变） | DONE |
| 4 | MOD-R27-03 | components/config/PublishDialog.vue | 修改 | 3 | L | 删除本地 KIND_LABEL/line，改调 formatDiffLine | DONE |
| 5 | MOD-R27-04 | components/config/FlowCanvas.vue | 修改 | 01 | M | `id="config-canvas"`、document keydown 监听（挂载/卸载）、emits request-remove/hint、选中集合、悬停卡片清理 | DONE |
| 6 | MOD-R27-05 | components/config/AgentDetailPanel.vue | 修改 | 01 | M | 五类“删除节点”按钮；agent 另留“删除 agent”；join 新分支；start/end 说明；移除 window.confirm | DONE |
| 7 | MOD-R27-06 | views/ConfigStudio.vue | 修改 | 01~05 | M | requestRemove/onRemoveAgent/onUndo、撤销条、放回画布选择框（unplacedAgents/placeAgent） | DONE |

## GR-B-001 条件落实
- (a) 风险 R-1（图更新后选中态）：FlowCanvas 自维护选中集合 `selNodes/selEdges`，由 `@nodes-change` / `@edges-change` 的 `select` 变更事件更新，图变化时按存在性剪枝；Delete 判定只读该集合，不依赖 vue-flow 内部 `selected` 标志。另核实源码：`parseNode` 对已有节点 `Object.assign(existingNode, node)`，传入节点不含 `selected`，故 vue-flow 自身也保留选中（`vue-flow-core.mjs:3540-3574`），两者一致。未使用 `useVueFlow`（无必要）；浏览器内真实按键仍未验证。
- (b) ASM-R27-02（1 节点 + 1 边混选）：最终行为 = 提示“请选中单个节点后再删除”，节点不删除；vue-flow 既有 `delete-key-code` 仍会删除被选中的那条边（边变更走原 `@edges-change`）。与 module_design IFC-R27-002 第 6 条一致，交 GROUP_D 手工清单。
- (c) R26 字面量约束保留：`:delete-key-code="readonly ? null : 'Delete'"`、`:nodes-draggable/connectable`、`@node-mouse-enter` 等未动；AgentDetailPanel 只新增 `el-button`；无 v-html/localStorage/axios/CDN；PublishDialog 不含“忽略并继续”。
- CP-001：agent 通用删除 / Delete 键 = 仅从画布移除（`removeFromCanvas`）；“删除 agent”仅在详情面板，走 `mode='definition'`，文案按 ADR-R27-04。

## 迁移
无。

## 架构偏差
无。

## 开放问题
- `[ASSUMPTION]` `decideDeleteKey` 的 `graph` 参数按契约保留但未使用（命名 `_graph`），为与 IFC-R27-002 签名一致。
- `[ASSUMPTION]` `removalVerdict` 的 `mode` 参数按契约保留，两种模式口径相同（命名 `_mode`）。
- `[ASSUMPTION]` 删除后 `tab` 重置为 `'detail'`（IFC-R27-011 步骤 5）；放回画布选择框默认选中列表第一项。
- `[ASSUMPTION]` 面板内 route/condition/confirm/join 的“删除节点”按钮放在各分支末尾独立 `.actions` 容器；`start/end` 分支文案“开始 / 结束节点不可删除”。
- 未验证：浏览器内真实 Delete 键交互、悬停卡片视觉清理、1 秒响应（REQ-NFUNC-001，沿用 R26 INF-5）。
- 无 MOD-R27-07 测试（GROUP_D 编写）；本轮未新增任何测试文件，未改现有测试。
