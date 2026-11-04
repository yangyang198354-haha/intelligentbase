<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-31T15:24:47+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计（REV-27 增量）— 可视化配置：删除画布节点

**范围**：只写 REV-27 增量；REV-26 设计基线归档于 `docs/sdlc/intelligentbase/archive/rev26/module_design.md`（只读，MOD-R26-18/19/20/21 是本轮的修改对象）。编号 `MOD-R27-NN` / `IFC-R27-NNN`；引用 R26 的条目写 `MOD-R26-NN`。需求引用均指本轮 `requirements_spec.md`（REQ-FUNC-001~013、REQ-NFUNC-001~003）。
**结论先行**：**纯前端改动，零服务端改动、零迁移、零新依赖**。服务端既有行为已满足 REQ-FUNC-011/012 与冲突点 X1 的口径（证据见 §GR-A-001 处置），因此只改前端文案与格式化。
**用户裁决（CP-001）**：US-001~011 确认；OQ-R27-01~10 与 INF-1~3 全部按推荐项；OQ-R27-02=A、OQ-R27-07=A。

## GR-A-001 处置（条件 (a)(b) 的核对结果）

### (a) 冲突点 X1：保存一份删除了某 agent 的配置时，服务端对其提示词文件 / 历史的实际处置

| # | 事实 | 证据 |
|---|---|---|
| 1 | 提交的文档里不再含某专家 → 合并后的快照只含 `doc.experts` 中的专家；请求里该专家的提示词补丁被忽略（不落盘、不报错） | `src/ib/confsvc/publish.py:133-150`（`_merge` 只遍历 `req.document.experts`）；`src/ib/config/versioning.py:63-69`（`build_snapshot` 只含 `doc.experts`） |
| 2 | 保存落盘时，对"当前文件态有、目标快照没有"的专家，**删除其 main / fallback 两层提示词文件**（注释：否则装配期判孤儿文件） | `src/ib/confsvc/publish.py:333-335` |
| 3 | 发布前的版本快照（含提示词正文）保留在版本台账中；回滚 = 以目标版本快照为目标重新 `_sync_files`，会把被删专家的提示词层写回 | `src/ib/confsvc/publish.py:205-216`（`rollback` → `_apply(found[1], …)`）；`:317-331`（`_sync_files` 写层）；版本保留上限 `keep_versions: int = 50`（`publish.py:110`） |
| 4 | 发布路径不触碰会话 / 历史记录 | `git grep -n "session" -- src/ib/confsvc` 无结果 |
| 5 | R26 的"软删"口径：R26 ADR-68 把"停用"定义为 `status='disabled'`（保留在 `experts[]`）；本仓库前端**没有**"停用"入口（`git grep -n "停用" -- src/frontend/src` 只命中账号/项目面板与注释） | `archive/rev26/architecture_design.md` ADR-68；`src/ib/config/definition.py:644-646`（`disabled` 校验） |

**结论**：现有"删除 agent"文案"其连线与提示词文件将一并移除（保存后生效）"（`AgentDetailPanel.vue:110`）对**保存后的项目提示词目录**是准确的（事实 2）；所谓"历史保留"在版本快照（事实 3）与会话（事实 4）两处成立，与 R26 OQ-R26-11=A 不构成字面矛盾，但"提示词文件"并非软删：保存后确实从项目目录移除，只能经版本回滚找回。
**处置**：**不改服务端**（改动会动到发布/回滚语义与 `_sync_files` 的孤儿文件保护，超出本轮范围且违背 C-R27-01）。只改前端确认文案，写出真实口径并指明两条出路（见 IFC-R27-004 的文案模板）。**残留差异**（"删除 agent 在提示词文件层面是硬移除、仅靠版本回滚兜底"）写入 architecture_design 开放问题 OQ-ARCH-R27-01，交用户知悉；是否另立项做"停用"入口（真正的软删）不属于本轮。

### (b) 保存预检差异清单对 route / condition / join / confirm 节点新增 / 删除的覆盖（REQ-FUNC-012）

| # | 事实 | 证据 |
|---|---|---|
| 1 | 差异计算对**所有节点类型**一视同仁：按节点 id 做集合差，新增 → `node_added`（after=kind），删除 → `node_removed`（before=kind），内容变化 → `node_changed`；边同理 `edge_added/removed/changed`（每条边一项） | `src/ib/config/versioning.py:214-232`（节点）、`:233-250`（边）；`_node_core` `:142-146` |
| 2 | 差异基线 = 文件态（`cur`），"新增后又删除"净变化为零时无条目 | `src/ib/confsvc/publish.py:184`（`diff_snapshots(cur, new)`） |
| 3 | 预检返回 `items` 与逐条 `errors`，校验错误以 `validation_error` 抛出；保存时同一校验再跑一次 | `publish.py:175-192`、`:253-258` |
| 4 | 展示层缺口：`PublishDialog.vue:18-22` 对节点类项显示为"删除节点：join-9 · node：join → ∅"——类型是英文代码，不是"汇聚"等中文名；AC-011-01 期望"删除 条件分支节点：condition-9" | `src/frontend/src/components/config/PublishDialog.vue:7-22`；`src/frontend/src/components/config/graphModel.ts:30-38`（`KIND_LABEL`） |

**结论**：服务端覆盖已足（无需改动）；不足只在前端展示层，最小改动 = 抽出纯函数 `formatDiffLine`（IFC-R27-008），把节点类型代码映射为中文名。**INF-2 已验证**（差异清单对非 agent 节点原本就有条目）。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改） | 职责（一句话） | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-R27-01 | 节点删除纯逻辑 | `src/frontend/src/components/config/nodeRemoval.ts`（**新建**） | 无框架纯函数：Delete 键判定与输入焦点保护、删除可行性、确认规则与文案、两种移除的草稿变换、未上图 agent 列表、撤销状态机 | REQ-FUNC-001/003/004/005/006/007/010/011/013；US-001~006、009 | `graphModel.ts`（既有：`edgesTouching`、`removeNode`、`ADDABLE_KINDS`、`KIND_LABEL`） |
| MOD-R27-02 | 草稿 store 扩展 | `src/frontend/src/stores/configDraft.ts`（**修改** MOD-R26-18） | 在 store 上提供 `applyRemoval` / `undoRemoval` / `canUndo` / `isBaselineNode`，并在 load / discard / markSaved 时清空撤销位 | REQ-FUNC-009/010/013、REQ-NFUNC-002；US-008、009 | MOD-R27-01（仅类型与撤销状态机函数） |
| MOD-R27-03 | 差异清单格式化 | `src/frontend/src/components/config/publishDiff.ts`（**新建**）+ `PublishDialog.vue`（**修改** MOD-R26-20） | 把差异项渲染为含中文节点类型的一行文本 | REQ-FUNC-012；US-011 | `graphModel.ts`（`KIND_LABEL`） |
| MOD-R27-04 | 画布组件修改 | `src/frontend/src/components/config/FlowCanvas.vue`（**修改** MOD-R26-19） | 注册 Delete 键监听并上报"请求删除节点 / 提示"；删除后清理悬停卡片 | REQ-FUNC-003/007/008/009；US-002、006、007、008 | MOD-R27-01 |
| MOD-R27-05 | 详情面板修改 | `src/frontend/src/components/config/AgentDetailPanel.vue`（**修改** MOD-R26-19） | 五类可删节点统一"删除节点"入口；agent 另保留"删除 agent"；开始 / 结束给出说明；移除面板内的 `window.confirm` | REQ-FUNC-002/006/007/008；US-001、005、006、007 | MOD-R27-01 |
| MOD-R27-06 | 页面壳编排 | `src/frontend/src/views/ConfigStudio.vue`（**修改** MOD-R26-21） | 统一处理"请求删除"：可行性 → 确认 → 变换草稿 → 清选中 → 登记撤销；撤销条；未上图 agent 选择；Builder 加入 / 删除 agent 的提示词补丁一致性 | REQ-FUNC-001~013（编排）；US-001~011 | MOD-R27-01、02、03、04、05；既有 MOD-R26-20 其余组件 |
| MOD-R27-07 | 前端测试 | `src/frontend/tests/config_studio_r27.test.js`（**新建**） | node:test 离线覆盖 MOD-R27-01/03 纯函数与 02/04/05/06 的源码结构事实 | 全部 AC 的可离线部分 | MOD-R27-01、03 |

编号即拓扑序（M-SA-003）：每条依赖边从高编号指向低编号；既有模块 `graphModel.ts`、`client.ts` 视为更低层，不被本轮任何新模块反向依赖。

## 模块详情

> 以下类型均为 TypeScript。`DefinitionDocumentV2`、`GraphDto`、`GraphNodeDto`、`NodeKind`、`PromptPatch`、`DiffItemDto` 取自 `src/frontend/src/api/client.ts`（`NodeKind` 在 `client.ts:565` 一带，`GraphNodeDto` / `GraphDto` / `DiffItemDto` 在其后；`PromptPatch` 已被 `configDraft.ts:10` 引用）。**本轮无新增 HTTP / 消息 / CLI 接口**：所有 IFC 均为进程内函数或组件契约；不涉及鉴权（权限闸门仍是 R26 的服务端保存档位校验，`config_views.py` 保存端点，REQ-NFUNC-002 / C-R27-03）与服务端输入校验（保存时由 `validate_graph` 等裁决，未改动）。前端侧的"输入校验"见各 IFC 的非法输入行为。

### MOD-R27-01 节点删除纯逻辑（`src/frontend/src/components/config/nodeRemoval.ts`，新建）

**职责**：把本轮全部可测决策收敛为无 DOM、无 Vue 依赖的纯函数。运行期 import 仅限 `./graphModel`（其余均为 `import type`），使 node:test 能用 `ts.transpileModule` 加载（做法见 MOD-R27-07）。

```ts
import type { DefinitionDocumentV2, GraphDto, GraphNodeDto, NodeKind, PromptPatch } from '../../api/client';

/** 可删类型 = ADDABLE_KINDS（route / agent / condition / join / confirm）；start / end 为结构节点。 */
export const REMOVABLE_KINDS: readonly NodeKind[];            // 取值与 graphModel.ADDABLE_KINDS 相同
export const STRUCTURAL_REMOVE_HINT = '开始 / 结束节点不可删除';
export const DEFAULT_EXPERT_HINT = '默认专家不能删除，请先指定其他默认专家';   // 沿用 AgentDetailPanel.vue:192 原文
export const MULTI_SELECT_HINT = '请选中单个节点后再删除';

/** 草稿的"可被删除操作改变的部分"：文档 + 提示词补丁（与 configDraft 快照口径一致，configDraft.ts:22）。 */
export interface DraftState { document: DefinitionDocumentV2; promptPatch: PromptPatch }
export type RemovalMode = 'canvas' | 'definition';
```

**IFC-R27-001** `isEditableTarget(target: KeyTargetLike | null): boolean`
- `KeyTargetLike = { nodeName?: string; hasAttribute?: (n: string) => boolean; closest?: (sel: string) => unknown }`（结构类型，便于 node:test 传桩对象，不依赖 DOM）。
- 返回 true 当：`nodeName ∈ {INPUT, SELECT, TEXTAREA}`，或带 `contenteditable` 属性，或 `closest('.nokey, .el-overlay, .el-drawer, [role="dialog"]')` 命中（弹窗 / 抽屉打开时不响应画布按键）。前三条与 `@vue-flow/core` 自带 `isInputDOMNode` 同口径（`node_modules/@vue-flow/core/dist/vue-flow-core.mjs:3361-3367`，`inputTags = INPUT/SELECT/TEXTAREA`、`contenteditable`、`.nokey`），后两类（`.el-overlay` 等）为本项目追加。`target` 为 null → false。
- 输入校验：无异常抛出；缺方法的桩对象按"未命中"处理。

**IFC-R27-002** `decideDeleteKey(input: DeleteKeyInput, graph: GraphDto): DeleteKeyDecision`
```ts
export interface DeleteKeyInput {
  key: string;                       // KeyboardEvent.key
  ctrlKey: boolean; metaKey: boolean; altKey: boolean; shiftKey: boolean;
  readonly: boolean;
  target: KeyTargetLike | null;
  selectedNodeIds: readonly string[];   // 画布当前选中的节点
  selectedEdgeIds: readonly string[];   // 画布当前选中的边
}
export type DeleteKeyDecision =
  | { action: 'ignore' }
  | { action: 'hint'; text: string }
  | { action: 'request'; nodeId: string };
```
判定顺序（短路）：
1. `key !== 'Delete'` → ignore（Backspace 不是触发键，AC-002-06 / OQ-R27-05=A）；
2. `readonly` → ignore（AC-007-02）；
3. 任一修饰键为真 → ignore（与 `useKeyPress(..., { actInsideInputWithModifier: false })` 的保守口径一致，`vue-flow-core.mjs:8237`）；
4. `isEditableTarget(target)` → ignore（AC-002-03：文本框内按 Delete 只作用于输入内容）；
5. `selectedNodeIds.length === 0` → ignore（只选了边：由 vue-flow 既有 `delete-key-code` 删边，AC-002-02 不变）；
6. `selectedNodeIds.length + selectedEdgeIds.length > 1` → `{hint, MULTI_SELECT_HINT}`（AC-002-04；"1 节点 + 1 边"同样提示，节点不删，边由 vue-flow 既有行为删除，见 architecture_design ADR-R27-01 后果）；
7. 否则 → `{request, nodeId: selectedNodeIds[0]}`（start / end / 默认专家的拒绝由 IFC-R27-003 统一给出，保证按键与面板按钮口径一致）。

**IFC-R27-003** `removalVerdict(doc: DefinitionDocumentV2, graph: GraphDto, nodeId: string, mode: RemovalMode): RemovalVerdict`
```ts
export interface RemovalVerdict { ok: boolean; reason?: string }
```
- 节点不存在 → `{ok:false, reason:'节点不存在'}`；
- `kind ∈ {start,end}` → `{ok:false, reason: STRUCTURAL_REMOVE_HINT}`（REQ-FUNC-007）；
- `kind === 'agent'` 且该节点对应专家（`node.expert ?? node.id`）`is_default === true` → `{ok:false, reason: DEFAULT_EXPERT_HINT}`，`mode` 为 `canvas` 与 `definition` 均适用（OQ-R27-10=A，AC-005-07）；
- 其余（含 route）→ `{ok:true}`（OQ-R27-06=A；REQ-FUNC-001：**不检查节点是否填写完整 / 能否通过校验**）。
- 只读档拒绝不在本函数（由调用方 `readonly` 先行短路，见 IFC-R27-011）。

**IFC-R27-004** `planConfirm(graph: GraphDto, nodeId: string, isBaselineNode: boolean, mode: RemovalMode, label: string): ConfirmPlan`
```ts
export interface ConfirmPlan { needConfirm: boolean; edgeCount: number; text: string }
```
- `edgeCount = edgesTouching(graph, nodeId)`（`graphModel.ts:251-253`）。
- `mode='canvas'`：`needConfirm = edgeCount > 0 || isBaselineNode`（OQ-R27-03=A；AC-004-04 / 05 / 06）。文本模板：
  - 非 agent：`确认删除${label}节点「${nodeId}」？${edgeCount>0 ? `将同时删除 ${edgeCount} 条边。` : ''}`
  - agent（仅从画布移除）：`确认将 agent「${label}」从画布移除？${edgeCount>0 ? `将同时删除 ${edgeCount} 条边。` : ''}其定义、工具授权与提示词草稿保留，之后可点击节点面板的“agent”按钮重新放回画布。`
  - 含边数时文本必含 `将同时删除 N 条边`（AC-004-01 / 06）。
- `mode='definition'`（仅 agent）：`needConfirm = true`（沿用现状：删除 agent 恒确认，AC-005-04）。文本（OQ-R27-07=A，X1 口径，事实依据见 §GR-A-001(a)）：
  `确认删除 agent「${label}」（${nodeId}）？将移除其定义与工具授权${edgeCount>0 ? `，并同时删除 ${edgeCount} 条边` : ''}。保存并生效后，其提示词文件将从项目目录移除；历史会话不受影响，也可在“版本历史”中回滚找回。若只想把它从画布拿掉并保留定义，请取消后改用“删除节点”。`
  - 单次确认：取代现状"面板确认 + `ConfigStudio.vue:120` 边数二次确认"的两连弹（`AgentDetailPanel.vue:110` + `ConfigStudio.vue:120`）。
  - 文案不得出现"提示词文件将一并移除"以外对 R26 软删口径的矛盾承诺；不得写"不可恢复"。
- 输入校验：`label` 仅做文本插值，不进入 HTML（沿用 R26 REQ-NFUNC-008 的"一律文本插值"）。

**IFC-R27-005** 两种移除的草稿变换（纯函数，不修改入参）
```ts
/** 仅从画布移除：只去掉节点与相连边；experts / tool_grants / promptPatch 原样保留（REQ-FUNC-006(a)、010 后半）。 */
export function removeFromCanvas(state: DraftState, nodeId: string): DraftState;

/** 删除 agent 定义：去掉节点 + 相连边 + experts 条目 + tool_grants 条目 + promptPatch[expert]（REQ-FUNC-006(b)、010 前半）。
 *  expert 名 = node.expert ?? node.id；非 agent 节点按 removeFromCanvas 处理。 */
export function deleteAgentDefinition(state: DraftState, nodeId: string): DraftState;

export function dropPromptPatch(patch: PromptPatch, expert: string): PromptPatch;   // 去掉某专家的补丁键；其余键引用不变
```
- 节点与边的移除复用 `graphModel.removeNode`（`graphModel.ts:255-260`）：同时去掉以该节点为端点的所有边（含条件边及其 `branch_key`），其他节点（含条件分支节点自身 `predicate`）**不改**（REQ-FUNC-004）。
- 变换保持 `document` 顶层键顺序（对象展开 `{...doc, graph}`），确保"删掉刚新增的节点"后 `JSON.stringify` 与基线逐字相同，`dirty` 自然回到 false（REQ-FUNC-009(d)、AC-008-02）。该性质由 MOD-R27-07 的用例锁定。
- 节点 id 与专家名：现有代码以 `node.id === expert` 为约定（`graphModel.ts:108-121` 新增 agent 时 `id = expert`；`src/ib/config/graph.py:349` 规范图亦然）；本函数仍按 `node.expert ?? node.id` 取专家名，按 `node.id` 删节点，不依赖该约定恒成立。

**IFC-R27-006** `unplacedAgents(doc: DefinitionDocumentV2, graph: GraphDto): { name: string; cn_label: string }[]`
- 返回 `status ?? 'active' === 'active'` 且不在图上（以 `n.expert ?? n.id` 集合判定）的专家，保持 `doc.experts` 顺序。与 `ConfigStudio.vue:101-103` 现判据一致，抽出供选择框使用（AC-005-01/02 "尚未上图的 agent 列表"）。

**IFC-R27-009a** 撤销状态机（供 MOD-R27-02 包装，纯函数以便离线测试）
```ts
export interface RemovalUndoSlot { label: string; before: string; after: string }   // before/after = 草稿快照字符串
export function recordRemoval(label: string, before: string, after: string): RemovalUndoSlot;
export function undoAvailable(slot: RemovalUndoSlot | null, currentSnapshot: string): boolean;   // slot !== null && slot.after === currentSnapshot
export function restoreFrom(slot: RemovalUndoSlot): DraftState;                                   // JSON.parse(before) → {d,p}
```
- 快照字符串口径 = `configDraft.ts:22` 的 `JSON.stringify({ d: document, p: promptPatch })`。

### MOD-R27-02 草稿 store 扩展（`src/frontend/src/stores/configDraft.ts`，修改）

**职责**：持有撤销位，并以"当前快照 === 删除后快照"作为撤销有效性的唯一判据（任何后续编辑——无论经 `setGraph`、`setPrompt` 还是 `store.document.value = …` 直接赋值——都会改变快照，撤销自动失效，不必逐处清除）。

**IFC-R27-007** `createConfigDraft()` 返回值新增（既有成员 `baseVersion/document/promptPatch/dirty/load/discard/markSaved/setGraph/setPrompt/toPublishPayload` 签名不变）：
```ts
applyRemoval(label: string, next: DraftState): void;   // 先取 before 快照 → 写入 document/promptPatch → 取 after 快照 → recordRemoval 存入撤销位（覆盖上一次，AC-009-04）
undoRemoval(): boolean;                                 // canUndo 为真时恢复 before 并清空撤销位，返回 true；否则不动返回 false
canUndo: ComputedRef<boolean>;                          // undoAvailable(slot, snapshotOf())
undoLabel: ComputedRef<string>;                         // 撤销位的 label；无则 ''
isBaselineNode(nodeId: string): boolean;                // 基线（最近一次 load / markSaved）图中是否含该节点 id；基线未载入 → false
```
- `load` / `discard` / `markSaved` 末尾清空撤销位（AC-009-03：保存、重新载入、放弃改动后失效）。
- 不使用任何浏览器本地存储；不调用 `ApiClient`（C-R27-02、REQ-NFUNC-002；MOD-R27-07 以源码断言锁定）。
- 依赖：MOD-R27-01 的 `RemovalUndoSlot` / `recordRemoval` / `undoAvailable` / `restoreFrom` / `DraftState`。
- `isBaselineNode` 的数据来源为已有 `baseline` 快照字符串（`configDraft.ts:19,29`）：`JSON.parse(baseline).d.graph.nodes` 取 id 集合；30 节点规模下代价可忽略。

### MOD-R27-03 差异清单格式化（`publishDiff.ts` 新建 + `PublishDialog.vue` 修改）

**IFC-R27-008** `formatDiffLine(i: DiffItemDto): string`（`src/frontend/src/components/config/publishDiff.ts`，仅 `import type` 与 `./graphModel` 的 `KIND_LABEL`）
- 把 `PublishDialog.vue:7-22` 内的 `KIND_LABEL`（diff kind → 中文）与 `line()` 原样迁出（行为不回归：其余 kind 的输出与现状逐字相同）。
- 仅对 `node_added` / `node_removed` / `node_changed` 改写为 `${动作} ${类型中文}节点：${object_id}`，类型中文取自 `graphModel.KIND_LABEL`（`before ?? after` 的节点类型代码；未知代码回落为原代码）。示例：`{kind:'node_removed', object_id:'condition-9', before:'condition', after:null}` → `删除 条件分支节点：condition-9`；`node_added` + `join` → `新增 汇聚节点：join-10`（AC-011-01 / 03）。
- 边类项保持现状（`删除边：e3 · edge：a->b → ∅`）：服务端每条边一项（`versioning.py:233-250`），满足 AC-011-01 "其 2 条相连边的删除项"。
- `PublishDialog.vue` 修改点仅：删除本地 `KIND_LABEL` / `line`，改为 `import { formatDiffLine } from './publishDiff'` 并在模板中调用；保留"校验错误无忽略选项"（`PublishDialog.vue:30-31` 与 smoke 断言 `frontend.smoke.test.js:1020`）。
- 输入校验：不抛异常；`before/after` 为 null 的处理与现状一致（`∅`）。

### MOD-R27-04 画布组件（`FlowCanvas.vue`，修改）

**契约变化**（props 不变；emits 追加两个）：
```ts
// 新增 emits
(e: 'request-remove', nodeId: string): void;   // Delete 键判定为"请求删除单个节点"
(e: 'hint', text: string): void;               // 多选等需要提示但不动草稿的情形
```
行为：
1. `<VueFlow id="config-canvas" …>` 增加固定 `id`，组件内用 `useVueFlow('config-canvas')` 取 `getSelectedNodes` / `getSelectedEdges`（`@vue-flow/core` 1.48.2：`useVueFlow(id?: string)` 见 `dist/composables/useVueFlow.d.ts:14`；`id` 属性见 `dist/types/flow.d.ts:130`；两个 getter 定义在 `dist/vue-flow-core.mjs:7861-7878`，按 `selected` 标志过滤）。
2. `onMounted` 在 `document` 上注册 `keydown`，`onBeforeUnmount` 移除（与 vue-flow 自带删除键监听同一目标，`vue-flow-core.mjs:3403` `defaultDoc`）。处理函数把事件字段 + 选中集合交给 IFC-R27-002：`request` → `emit('request-remove', nodeId)`；`hint` → `emit('hint', text)`；`ignore` → 不动。
3. **保持不变**（既有测试锁定）：`:delete-key-code="readonly ? null : 'Delete'"`（`config_studio_r26.test.js` TC-FE-R26-021）、`deletable: false` 的节点映射（`FlowCanvas.vue:97`：vue-flow 自带删除仍对节点无效，节点删除只走本模块的受控路径；见 vue-flow `removeNodes` 对 `deletable:false` 的跳过 `vue-flow-core.mjs:6562-6564`）；边的 Delete 删除沿用 `@edges-change`（`FlowCanvas.vue:86-91`）。
4. 悬停卡片清理（REQ-FUNC-009(c)）：记录 `cardTarget: { kind: 'node' | 'edge'; id: string } | null`；`watch(() => props.graph, …)` 中若 `cardTarget` 指向的节点 / 边已不在图中则 `card = null`（节点被移除时不会触发 mouseleave，故需主动清）。图仍含该目标（如拖拽结束）时不清除，保持既有悬停行为（REQ-NFUNC-003）。
5. 只读档：监听函数在 `readonly` 时由 IFC-R27-002 返回 ignore；不渲染任何删除控件。
- 鉴权 / 输入校验：无外部接口；按键事件仅取 `key` 与修饰键，不读取输入框内容。

### MOD-R27-05 详情面板（`AgentDetailPanel.vue`，修改）

**契约变化**：
```ts
// emits 变更
(e: 'request-remove', nodeId: string): void;        // 新增：点击“删除节点”（五类可删节点一致；agent 的语义 = 仅从画布移除）
(e: 'remove-agent', nodeId: string): void;          // 修改：参数由专家名改为节点 id；不再在面板内 window.confirm（确认统一在 ConfigStudio，IFC-R27-004）
```
- 新增通用操作区（`v-if="!readonly"`）：当 `node && REMOVABLE_KINDS.includes(node.kind)` 时在各类型详情末尾渲染 `<el-button size="small" type="danger" plain @click="emit('request-remove', node.id)">删除节点</el-button>`。route / condition / confirm 分支追加该按钮；**join 节点现落入"点击画布上的节点…"兜底分支（`AgentDetailPanel.vue:214`）**，需新增 `v-else-if="node?.kind === 'join'"` 分支（标题"汇聚"+ 说明 + 删除按钮）；`start` / `end` 分支显示说明"开始 / 结束节点不可删除"且不渲染按钮（AC-006-01）。
- agent 分支：在既有 `.actions`（`:189-193`）中保留"设为默认专家"与"删除 agent"，并追加"删除节点"按钮 + 说明 `仅从画布移除，agent 的定义与提示词保留`；默认专家时"删除节点"与"删除 agent"均 `:disabled="expert()?.is_default"`，旁注沿用 `DEFAULT_EXPERT_HINT`（AC-005-07）。
- 只读档：整个操作区 `v-if="!readonly"`（AC-007-01）。既有断言"所有 `el-input/el-input-number/el-checkbox/el-select/el-switch` 须带 `:disabled="readonly"` 或 `readonly`"（TC-FE-R26-022）继续成立：本模块**只新增 `el-button`**，不新增上述表单控件。
- 移除 `confirmRemove()`（`:108-111`）及其 `window.confirm`。
- 鉴权 / 输入校验：无新增外部接口；按钮点击只携带节点 id（来自当前选中的 `props.node`）。

### MOD-R27-06 页面壳编排（`ConfigStudio.vue`，修改）

**IFC-R27-011**（组件内部处理函数，无导出）
```ts
function requestRemove(nodeId: string, mode: RemovalMode = 'canvas'): void;
//  1) readonly → return（不提示）
//  2) removalVerdict(doc, graph, nodeId, mode)；!ok → ElMessage.info(reason)，return
//  3) planConfirm(graph, nodeId, store.isBaselineNode(nodeId), mode, label)；needConfirm 且 !window.confirm(text) → return（取消：草稿逐字段不变，AC-004-02）
//  4) next = mode==='definition' ? deleteAgentDefinition(state, nodeId) : removeFromCanvas(state, nodeId)
//  5) store.applyRemoval(`${label}「${nodeId}」`, next)；selectedId = null；tab 保持 'detail'
function onRemoveAgent(nodeId: string): void;          // = requestRemove(nodeId, 'definition')，由面板 remove-agent 触发
function onUndo(): void;                               // store.undoRemoval()；selectedId = null；成功时 ElMessage.success('已撤销删除')
function onAddNode(kind: NodeKind): void;              // 修改 agent 分支：unplacedAgents 为 0 → 现提示；为 1 → 直接上图；≥2 → 打开选择框 pickerOpen
function placeAgent(name: string): void;               // 选择框确认后 setGraph(addNodeOfKind(..,'agent',name))
function onBuilderAdd(d: AgentDraftDto): void;         // 保持（写入 experts / tool_grants / graph / 提示词补丁）
```
- 接线：`<FlowCanvas @request-remove="(id) => requestRemove(id)" @hint="(t) => ElMessage.info(t)" …/>`；`<AgentDetailPanel @request-remove="(id) => requestRemove(id)" @remove-agent="onRemoveAgent" …/>`；`@notice` 保持（连线预检提示，沿用 `banner`）。
- 撤销条：画布下方 `<div v-if="!readonly && store.canUndo.value" class="undo-bar">已删除 {{ store.undoLabel.value }} <el-button link type="primary" size="small" @click="onUndo">撤销</el-button></div>`（REQ-FUNC-013；查看档不渲染，AC-009-05）。
- 选择框：`<el-dialog v-model="pickerOpen" title="选择要放回画布的 agent">` + `el-radio-group` 列出 `unplacedAgents(...)`，确认调用 `placeAgent`；`label` 仅文本插值。
- 保存 / 放弃 / 重新载入流程（`startSave` / `confirmSave` / `discard` / `reloadWithConfirm`）**不改**；`discard` 经 store.discard 自动清撤销位。`onRemoveAgent` 旧实现（`ConfigStudio.vue:116-129`，未清提示词补丁）被替换。
- `import { addNodeOfKind, edgesTouching, removeNode, type AgentInfo }` 中 `edgesTouching` / `removeNode` 不再直接使用，改由 MOD-R27-01 引用；`ConfigStudio.vue` 模块注释更新为 `@implements` 追加 REQ-FUNC-001~013（R27）。
- 鉴权：无新增请求；所有删除只写内存；保存仍走 `publishPreview` / `publish`（服务端 edit 档校验，R26 `config_views.py`）。

### MOD-R27-07 前端测试（`src/frontend/tests/config_studio_r27.test.js`，新建）

位置与命名遵守画像 P3（前端测试在 `src/frontend/tests/`，框架 Node 内置 node:test；`package.json` 的 `"test": "node --test"` 会自动发现 `tests/*.test.js`，无需改配置；CI 为 Node 22，`ci.yml:240`）。**离线可测面（供 GROUP_D 编写 `TC-FE-R27-NNN`）**：

| 目标 | 加载方式 | 可断言内容 |
|---|---|---|
| `nodeRemoval.ts`、`publishDiff.ts` | 沿用 `config_studio_r26.test.js:26-30` 的 `ts.transpileModule` + `data:` URL。二者均 `import … from './graphModel'`：测试先转译 `graphModel.ts` 得到 data URL，再把转译结果中的 `'./graphModel'` 字符串替换为该 URL 后导入（模块内其余 import 全是 `import type`，转译后消失） | IFC-R27-001~006、008、009a 全部分支：Delete 判定 7 条规则（含 Backspace、修饰键、输入焦点桩对象、多选、只读）；`removalVerdict` 对 start/end/默认专家/route；`planConfirm` 的 AC-004-01~06 与两套文案（含 `将同时删除 2 条边`、定义删除文案含"版本历史"且不含"不可恢复"）；`removeFromCanvas` 保留 experts / tool_grants / 补丁；`deleteAgentDefinition` 清补丁（AC-005-06）；"新增后删除"变换前后 `JSON.stringify` 相同；`unplacedAgents`；`formatDiffLine` 节点三类与其余 kind 不回归；撤销状态机（AC-009-03/04） |
| `configDraft.ts` | 因 `import { computed, ref } from 'vue'` 为运行期裸导入，data: URL 无法解析；**不在离线单测里实例化**。以读源码断言覆盖：含 `applyRemoval/undoRemoval/canUndo/isBaselineNode`；`load/discard/markSaved` 内清撤销位；无 `localStorage`、不引用 `client`/`fetch`（REQ-NFUNC-002 的结构侧证据） | 结构事实 |
| `FlowCanvas.vue` / `AgentDetailPanel.vue` / `ConfigStudio.vue` | 沿用 `stripComments(read(...))` 读源码断言（`config_studio_r26.test.js:143-150`） | FlowCanvas 保留 `:delete-key-code="readonly ? null : 'Delete'"`、注册并卸载 `keydown` 监听、含 `id="config-canvas"`；Panel 无 `window.confirm`、含"删除节点"与"删除 agent"、join / start / end 分支、新增控件无 `el-input` 类；ConfigStudio 含撤销条与选择框、`request-remove` 接线、不再含 `将同时删除 ${n} 条边，继续？` 二次确认；全部无 `v-html/localStorage/axios/CDN` |

**无法离线验证**（如实，列入 GROUP_D 的"未验证"）：浏览器内真实按键（vue-flow 选中集合与 Delete 键在 `deletable:false` 节点上的交互）、悬停卡片的视觉清理、1 秒响应（REQ-NFUNC-001 沿用 R26 INF-5，目标机校准前"未验收"）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-001 | US-001 | MOD-R27-01（IFC-003 不检查完整性）、05（五类入口）、06 |
| REQ-FUNC-002 | US-001 | MOD-R27-05、06 |
| REQ-FUNC-003 | US-002 | MOD-R27-01（IFC-001/002）、04、06 |
| REQ-FUNC-004 | US-003 | MOD-R27-01（IFC-005，复用 `removeNode`）、06 |
| REQ-FUNC-005 | US-004、005 | MOD-R27-01（IFC-004）、02（`isBaselineNode`）、06 |
| REQ-FUNC-006 | US-005 | MOD-R27-01（IFC-005/006）、05、06 |
| REQ-FUNC-007 | US-006、005 | MOD-R27-01（IFC-003）、05 |
| REQ-FUNC-008 | US-007 | MOD-R27-01（IFC-002 readonly）、04、05、06（`readonly` 短路、无撤销条）；服务端闸门沿用 R26，未改 |
| REQ-FUNC-009 | US-008 | MOD-R27-02（快照比较）、04（悬停卡片清理）、06（清选中） |
| REQ-FUNC-010 | US-005 | MOD-R27-01（`dropPromptPatch`/`deleteAgentDefinition`）、06；Builder 加入 → 删除路径见 AC-005-06 用例 |
| REQ-FUNC-011 | US-003 | 无新代码：删除不触发前置校验（MOD-R27-01 IFC-003 不校验图合法性），保存预检沿用 R26（`publish.py:175-192`）；MOD-R27-06 不改 `startSave` |
| REQ-FUNC-012 | US-011 | MOD-R27-03（服务端覆盖已足，见 §GR-A-001(b)） |
| REQ-FUNC-013 | US-009 | MOD-R27-01（IFC-009a）、02、06 |
| REQ-NFUNC-001 | US-008 | MOD-R27-06（同步内存变换，无网络；30 节点规模下的目标机校准沿用 R26 INF-5，未验收） |
| REQ-NFUNC-002 | US-010 | MOD-R27-02、06（零服务端写入；MOD-R27-07 结构断言） |
| REQ-NFUNC-003 | US-010 | 全部修改点保留既有锁定断言（TC-FE-R26-021/022/023/026、smoke 1020）；MOD-R27-07 回归 |

## 依赖关系

- MOD-R27-06 → MOD-R27-01（IFC-001~006）、MOD-R27-02（IFC-007）、MOD-R27-03（`PublishDialog` 经 IFC-008）、MOD-R27-04（组件 `FlowCanvas`，emits `request-remove`/`hint`）、MOD-R27-05（组件 `AgentDetailPanel`，emits `request-remove`/`remove-agent`）
- MOD-R27-05 → MOD-R27-01（`REMOVABLE_KINDS`、`DEFAULT_EXPERT_HINT`）
- MOD-R27-04 → MOD-R27-01（IFC-001/002）
- MOD-R27-03 → `graphModel.ts`（`KIND_LABEL`，既有）
- MOD-R27-02 → MOD-R27-01（IFC-009a、`DraftState`）
- MOD-R27-01 → `graphModel.ts`（`edgesTouching`、`removeNode`、`ADDABLE_KINDS`、`KIND_LABEL`，既有）
- MOD-R27-07 → MOD-R27-01、03（运行期加载）；其余以源码读取
- 已检查：无循环（依赖边均从高编号指向低编号 / 既有底层文件；`graphModel.ts` 不引用任何 R27 模块）。

## 数据迁移

**无**。不新增表 / 字段 / 索引，不新增 `src/deploy/migrations/NNN_*.sql`；`src/ib/ledger/schema.py` 不动。定义文档 schema（v2）与 `content_hash` 口径不变——"仅从画布移除"产生的"专家在 `experts[]` 中但无图节点"状态是系统已有的合法状态（`ConfigStudio.vue:98-109` 的上图路径；`src/ib/config/graph.py:63-224` 的 `validate_graph` 只校验"节点引用的专家存在"，不要求每个专家都有节点）。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 说明（画像 P7） |
|---|---|---|
| 前端构建 `src/frontend`（`npm run build`，`vue-tsc --noEmit && vite build`） | **需重新构建并发布静态资源** | 在目标机本地构建后拷贝到 web root（P7 部署方式）；构建含类型检查，`nodeRemoval.ts` 等新文件须通过 `vue-tsc` |
| ib-web / ib-worker / ib-embed / qdrant | **不重启** | 零后端代码改动（SKILL.md §6 "前端不重启"） |
| systemd unit / env 文件 / nginx | 无变更 | 无新增运行单元（P7 ADR-03 限制不受影响） |
| 目标机本地状态（`/var/lib/intelligentbase/` 等） | 不触碰 | 删除只改内存草稿；保存沿用既有发布路径 |
| CI | 前端阶段 `npm ci && npm run build && npm test`（Node 22，`ci.yml:240`） | 新增 `config_studio_r27.test.js` 被 `node --test` 自动发现 |

## 领域与外部依赖出处

画像无 P11 小节 → 本节"不适用"（无硬件 / 算法 / 闭源 API）。为满足门控"引用真实"，下表登记本设计依赖的**库能力与服务端事实**出处（均已打开原文核对，2026-10-31；`@vue-flow/core` 版本 1.48.2 取自 `src/frontend/node_modules/@vue-flow/core/package.json`）。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-R27-001 / MOD-R27-04 | vue-flow 删除键监听挂在 `document`，对 INPUT/SELECT/TEXTAREA、`contenteditable`、`.nokey` 目标不响应 | [CODE: node_modules/@vue-flow/core/dist/vue-flow-core.mjs:3361-3367, 3402-3433] |
| MOD-R27-04 | 画布按 Delete 时对选中节点调用 `removeNodes`、对选中边调用 `removeEdges`；`deletable:false` 的节点被 `removeNodes` 跳过 | [CODE: vue-flow-core.mjs:8237-8245, 6562-6564] |
| MOD-R27-04 | `useVueFlow(id)` 与 `<VueFlow id>` 共享 store；`getSelectedNodes` / `getSelectedEdges` 按 `selected` 过滤 | [CODE: dist/composables/useVueFlow.d.ts:14, dist/types/flow.d.ts:130, vue-flow-core.mjs:7861-7878] |
| MOD-R27-06 | 现有"删除 agent"、"未上图 agent 上图"、Builder 加入的实现与未清理提示词补丁的缺口 | [CODE: src/frontend/src/views/ConfigStudio.vue:98-129, 130-151] |
| MOD-R27-02 | 草稿快照 = 文档 + 提示词补丁；`dirty` 为快照与基线比较 | [CODE: src/frontend/src/stores/configDraft.ts:19-22] |
| §GR-A-001(a) | 保存时删除被移除专家的提示词层文件；回滚用版本快照写回 | [CODE: src/ib/confsvc/publish.py:133-150, 205-216, 317-336] |
| §GR-A-001(b) / MOD-R27-03 | 差异覆盖全部节点类型与每条边 | [CODE: src/ib/config/versioning.py:214-250] |
| MOD-R27-05 | 现面板删除按钮与 join / start / end 兜底分支 | [CODE: src/frontend/src/components/config/AgentDetailPanel.vue:108-111, 189-193, 214] |
