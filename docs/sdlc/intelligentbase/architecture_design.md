<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-31T15:24:47+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计（REV-27 增量）— 可视化配置：删除画布节点

**范围与基线**：只写 REV-27 增量。REV-26 设计（`docs/sdlc/intelligentbase/archive/rev26/architecture_design.md`，ADR-53~69）与项目基线 `docs/architecture_design.md` 继续有效，凡未在"继承 / 变更登记"中改动的决策一律沿用。需求依据 = 同目录 `requirements_spec.md`、`user_stories.md`（1.0.0 APPROVED）。ADR 编号 `ADR-R27-NN`；模块 / 接口见 `module_design.md`（`MOD-R27-NN` / `IFC-R27-NNN`）。
**用户裁决（CP-001）**：US-001~011 确认；OQ-R27-01~10、INF-1~3 全部按推荐项；OQ-R27-02=A、OQ-R27-07=A。

## 架构概览

**本次改动在现有系统中的位置**：仅前端"编排画布"页（`ConfigStudio.vue` 及 `components/config/*`、`stores/configDraft.ts`），属 R26 ADR-69 确定的"页面壳 + 画布 / 面板 / 发布对话框 + 手写草稿 store"结构内的补齐。**不新增服务端接口、不改数据模型、不新增依赖、不新增运行单元。**

```
ConfigStudio.vue (MOD-R27-06 页面壳：请求删除 → 可行性 → 确认 → 变换草稿 → 登记撤销)
 ├─ FlowCanvas.vue (04)      document 级 Delete 键监听 → request-remove / hint；删后清悬停卡片
 ├─ AgentDetailPanel.vue (05) “删除节点”(五类统一) + agent 另有“删除 agent”
 ├─ PublishDialog.vue (03)    差异行经 formatDiffLine 显示中文节点类型
 ├─ configDraft.ts (02)       applyRemoval / undoRemoval / canUndo / isBaselineNode
 └─ nodeRemoval.ts (01)       无框架纯函数：判定 / 确认规则 / 两种移除变换 / 撤销状态机
        ↓ 复用既有 graphModel.ts（edgesTouching / removeNode / KIND_LABEL）
服务端（不改）：publishPreview → diff_snapshots + validate_graph；publish → _sync_files（删被移除专家的提示词层文件）
```

**关键质量属性**
- REQ-NFUNC-002（删除只改草稿）：全部变换是内存纯函数，store 不引用 `ApiClient`；服务端写入仍只发生在"保存并生效"确认之后。
- REQ-NFUNC-001（1 秒内联动）：同步内存变换 + Vue 响应式；无网络往返。30 节点 / 60 边下的目标机实测沿用 R26 INF-5，校准前"未验收"。
- REQ-NFUNC-003（无回归）：所有 R26 锁定断言（`config_studio_r26.test.js` TC-FE-R26-021/022/023/026、`frontend.smoke.test.js:1020`）保持成立；边的 Delete 删除、拖拽、连线预检、悬停卡片、保存预检 / 差异 / 冲突流程不改。
- 可测性：新逻辑集中在两个无 Vue 依赖的模块（`nodeRemoval.ts`、`publishDiff.ts`），可由 node:test 离线真实执行。

## 部署视图

| 组件 | 运行单元 | 环境（画像 P7） | 变更 |
|---|---|---|---|
| 前端静态资源（`src/frontend` 构建产物） | 目标机本地 `npm run build` → 拷贝到 web root；nginx 静态托管 | dev/local、CI、production | **需重新构建并发布**；不重启任何服务 |
| ib-web / ib-worker / ib-embed / qdrant | systemd 单元 | production | **无改动、不重启** |
| CI 前端阶段 | GitHub Actions（Node 22，`ci.yml:240`）`npm ci && npm run build && npm test` | CI | 新增 `config_studio_r27.test.js` 被 `node --test` 自动发现 |

staging 不存在（P7），本设计不涉及。

## R26 继承 / 变更登记

| R26 决策 | 本轮处理 | 说明 |
|---|---|---|
| ADR-69 前端组件拆分与零新增依赖 | **Accepted（继承）** | 本轮同样零新依赖；新增两个纯函数模块与一个测试文件 |
| ADR-59 乐观并发 / 草稿副本 | Accepted（继承） | 保存、冲突回执流程不改 |
| ADR-68 专家停用 = `status='disabled'`（软删语义） | Accepted（继承），**不扩展** | 本仓库前端无"停用"入口；本轮不新增（见 OQ-ARCH-R27-01） |
| ADR-56 图结构与受限节点集 | Accepted（继承） | 节点类型集合不变（C-R27-05） |
| R26 REQ-FUNC-011 "新增 / 删除节点" | 补齐实现缺口 | 见 ADR-R27-01/03/05 |

## ADR

### ADR-R27-01: 节点删除键的检测与分派方式

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-003（Delete 键删节点，与删边并存；多选只提示；输入控件内不得误删）、REQ-FUNC-007/008、REQ-NFUNC-003。现状：节点被强制 `deletable: false`（`FlowCanvas.vue:97`），Delete 键仅对边生效（`:102`）；vue-flow 的删除键监听挂在 `document`，对 INPUT/SELECT/TEXTAREA / `contenteditable` / `.nokey` 目标不响应（`node_modules/@vue-flow/core/dist/vue-flow-core.mjs:3361-3367, 3402-3433`），按下后对选中节点调用 `removeNodes`、对选中边调用 `removeEdges`（`:8237-8245`），`removeNodes` 跳过 `deletable:false` 的节点（`:6562-6564`）。本项目要求删除前可能需要确认（REQ-FUNC-005），默认专家 / 结构节点要拒绝（REQ-FUNC-007）。
- Options:
  - A. 让节点 `deletable: true`，交给 vue-flow 原生删除，监听 `nodes-change`/`edges-change` 的 remove 变更回写图。优：零自定义按键代码；缺：vue-flow 会先改内部 store 并连带触发连接边的 remove 变更，确认框"取消"时需把已被移除的元素还原（与受控 `:nodes` 反复同步，易闪烁 / 丢选中）；start / end / 默认专家需靠 `deletable` 逐个标记或事后回滚；多选时 vue-flow 会批量删，与 REQ-FUNC-003 "多选不删"冲突。
  - B. 节点保持 `deletable: false`，在 FlowCanvas 注册 `document` 级 `keydown`，用 `useVueFlow(id)` 读选中集合，经纯函数 `decideDeleteKey` 判定后 emit `request-remove`，由页面壳统一做"可行性 → 确认 → 变换"。边的删除仍由 vue-flow 既有 `delete-key-code` 负责。 ← **选定**
  - C. 只在节点元素上监听 `keydown`（依赖节点获得焦点）。优：事件范围小；缺：点击节点是否稳定聚焦不可保证，用户点击后按键无反应时无法排查；与"选中单个节点"语义（vue-flow 的 `selected`）脱节。
- Decision: 选 B。节点 `deletable:false` 保持不变，因此 vue-flow 原生路径永不删节点（避免 A 的还原问题）；自有监听与 vue-flow 同目标（`document`）、同口径地跳过输入控件，并追加对弹窗 / 抽屉内按键的忽略（REQ-FUNC-003、AC-002-03）。所有判定（Backspace 不触发、修饰键、只读档、多选提示、无选中节点则让位给既有删边）集中在可离线测试的纯函数 IFC-R27-002。
- Consequences:
  - 正向：确认 / 拒绝逻辑与面板按钮共用一条路径（IFC-R27-011），口径一致；纯函数可 node:test 全分支覆盖；不触碰 vue-flow 内部状态。
  - 负向：(1) 依赖 vue-flow 的"选中"状态——`FlowCanvas` 把 `nodes` 映射为新对象传入（`FlowCanvas.vue:97`），图更新后选中标志是否保留需浏览器实测，列为风险 R-1（降级：面板按钮始终可用）；(2) "1 个节点 + 1 条边同时选中"时按 Delete：节点不删并提示，但边会被 vue-flow 既有逻辑删除（部分生效），属可接受的边界，写入 GROUP_D 手工清单；(3) 两个 `document` 级监听并存，须在 `onBeforeUnmount` 移除自有监听。

### ADR-R27-02: 撤销最近一次删除的实现方式

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-013（单步撤销，下一次任何编辑 / 保存 / 重新载入 / 放弃改动后失效；agent 定义删除时同时恢复专家条目、工具授权、提示词草稿）、OOS-R27-02（不做通用多步撤销）、REQ-NFUNC-002。草稿状态由 `document`（含图、专家、工具授权）与 `promptPatch` 组成，且页面多处直接赋值 `store.document.value = …`（`ConfigStudio.vue:122,140,286`），难以逐处拦截"下一次编辑"。
- Options:
  - A. 存删除前 / 后两份**整份草稿快照**（`JSON.stringify({d,p})`，口径同 `configDraft.ts:22`），撤销位有效当且仅当"当前快照 === 删除后快照"；撤销 = 恢复删除前快照。 ← **选定**
  - B. 记录每种删除的逆操作（还原节点、边、专家条目、工具授权、补丁）。优：占内存小；缺：每新增一种删除变换都要写逆操作，易漏（尤其 agent 定义 + 提示词补丁 + 位置 + 分支键），且"下一次编辑后失效"需在所有编辑入口手工清除。
  - C. 通用编辑历史栈（Ctrl+Z 多步）。缺：超出范围（OOS-R27-02），需拦截全部编辑入口。
- Decision: 选 A。快照比较天然覆盖任意后续编辑（面板修改、拖拽、连线、Builder 加入、直接赋值）使撤销失效，无需逐入口清除；`load` / `discard` / `markSaved` 另行显式清空。恢复的是整份删除前状态，所以位置、类型配置、分支键、专家条目、工具授权、提示词补丁一次性精确还原（AC-009-01/02）。连续删除只保留最近一次（AC-009-04）。
- Consequences:
  - 正向：实现面小（IFC-R27-009a 三个纯函数 + store 四个成员）；不会遗漏新字段；与 `dirty` 同一快照口径，状态一致。
  - 负向：每次判定对 30 节点规模的文档做 `JSON.stringify`（与 `dirty` 同量级，可忽略）；编辑后恰好手工还原到删除后状态时撤销会"复活"（恢复的仍是删除前状态，无数据风险，接受）；整份快照占用两份文档大小的内存 `[ESTIMATE]`（KB 级）。

### ADR-R27-03: 删除逻辑的放置位置与确认交互方式

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001/004/005/006/010/011、REQ-NFUNC-003；画像 P3（前端测试为 node:test，无组件挂载环境，见 `config_studio_r26.test.js` 文件头局限说明）。现状删除逻辑写在 `ConfigStudio.vue:116-129` 与 `AgentDetailPanel.vue:108-111`，确认用 `window.confirm`（两处，且 agent 有边时连弹两次），无法离线测试。
- Options:
  - A. 沿用现状，把新逻辑继续写进 `.vue` 组件。优：改动文件最少；缺：无法 node:test 真实执行（只能读源码断言），确认规则 / 提示词清理等关键决策缺少行为级回归。
  - B. 抽成无 Vue 依赖的纯函数模块 `nodeRemoval.ts`（判定、确认计划与文案、两种移除变换、撤销状态机），`.vue` 只做接线；确认仍用 `window.confirm`（与 `ConfigStudio.vue:86,120` 既有交互一致）；撤销状态存于手写 store。 ← **选定**
  - C. 在 B 基础上改用 `ElMessageBox` 异步确认。优：样式统一；缺：引入异步分支与测试替身成本，且与同页现有确认不一致，本轮无需求驱动。
- Decision: 选 B。统一单次确认（取代 agent 的两连弹，AC-005-04），文案由 `planConfirm` 生成并可断言；删除 agent 定义时在同一纯函数里同时清 `promptPatch`（REQ-FUNC-010）；"仅从画布移除"保留 experts / tool_grants / 补丁。
- Consequences:
  - 正向：确认规则（OQ-R27-03=A）、免确认例外、边数文案、提示词残留清理均可离线真实测试；面板与按键共享一条路径。
  - 负向：`window.confirm` 阻塞式、不可样式化（与现状一致，接受）；`nodeRemoval.ts` 运行期依赖 `./graphModel`，测试需做一次转译后的说明符替换（module_design MOD-R27-07 已写明）；`AgentDetailPanel` 的 emit 签名变更（`remove-agent` 参数由专家名改为节点 id）需同步页面壳。

### ADR-R27-04: X1 冲突点——"删除 agent"对提示词文件 / 历史的处置与确认文案（constraint-driven）

- Status: Proposed
- Type: constraint-driven
- Context: OQ-R27-07=A（以 R26 软删 / 历史保留口径为准，文案不得矛盾，处置由架构核对）、GR-A-001(a)、C-R27-01（不推翻 R26 已确认决策）、REQ-FUNC-006(b)。实测服务端行为（`module_design.md` §GR-A-001(a)）：保存删除了某专家的文档时，`_merge` 不带入其补丁（`publish.py:133-150`），`_sync_files` 删除其 main / fallback 提示词文件（`publish.py:333-335`），历史版本快照仍保留且回滚可写回（`publish.py:205-216`），发布路径不触碰会话（`git grep -n "session" -- src/ib/confsvc` 无结果）。
- 约束来源与被排除方案：
  - 被排除——改服务端为"删除专家时保留提示词文件 / 标 disabled"：会改变 `_sync_files` 的孤儿文件保护（"否则装配期判孤儿文件"，`publish.py:333` 注释）与发布 / 回滚语义，超出本轮"补齐前端删除入口"的范围，并有跨进程（ADR-53/55）回归风险，违背 C-R27-01 的最小改动原则。
  - 被排除——保持原文案"提示词文件将一并移除"不变：对保存后目录是真话，但未告知历史会话不受影响与可回滚，而 OQ-R27-07=A 要求文案与 R26 口径一致。
  - 被排除——把"删除 agent"改为 `status='disabled'` 的真软删：需新增"停用"入口并处理 `tool_grant_expert_disabled`、`expert_default_disabled` 等校验（`definition.py:644-668`），属新功能，另立项。
- Decision: 不改服务端；确认文案改为如实口径——"将移除其定义与工具授权（含相连 N 条边）；保存并生效后其提示词文件将从项目目录移除；历史会话不受影响，也可在‘版本历史’中回滚找回；若只想把它从画布拿掉并保留定义，请取消后改用‘删除节点’"（IFC-R27-004）。
- Consequences:
  - 正向：零服务端改动、零迁移；文案与可核实的行为一致，不再单方面承诺"提示词文件被移除"以外的内容。
  - 负向：R26 "软删"在提示词文件层面并非字面成立（保存后文件确实被移除，仅靠版本快照兜底，且版本保留上限 50）；该差异记入 OQ-ARCH-R27-01，交用户知悉，如需真软删另立项。

### ADR-R27-05: agent 节点的默认移除语义与"放回画布"的选择方式

- Status: Proposed
- Type: decision
- Context: OQ-R27-02=A（通用"删除节点" / Delete 键对 agent = 仅从画布移除；"删除 agent"留在 agent 详情面板）、REQ-FUNC-006、AC-005-01/02（"尚未上图的 agent 列表（点击节点面板的 agent 按钮时可选）"）、OQ-R27-10=A（默认专家不可移除）。现状 `ConfigStudio.vue:98-109`：点 agent 按钮时自动取**第一个**尚未上图的 active 专家，没有选择；用户被移除的 agent 若不是第一个未上图者，无法确定性放回。
- Options:
  - A. 通用删除对 agent = 仅从画布移除；"放回画布"在未上图 agent ≥2 个时弹出选择框（单选），0 个沿用现提示，1 个直接上图。 ← **选定**
  - B. 同 A，但"放回画布"保持"取第一个"，不加选择框。优：改动最小；缺：AC-005-01 的"列表可选"不满足，用户多次"仅移除"后无法控制放回哪一个。
  - C. 通用删除对 agent 弹窗二选一（OQ-R27-02 选项 C）。已被用户裁决为 A，排除。
- Decision: 选 A。选择框用已有 Element Plus `el-dialog` + `el-radio-group`（不增依赖），数据来自纯函数 `unplacedAgents`（IFC-R27-006，与现判据一致）。
- Consequences:
  - 正向：满足 AC-005-01/02 与可逆性；"仅移除"不丢定义与提示词，保存时补丁仍随专家落盘（`_merge` 对仍在 `experts` 中的专家保留补丁，`publish.py:133-150`）；"专家在 `experts[]` 但无图节点"是已有合法状态（`graph.py:63-224` 不要求每位专家有节点）。
  - 负向：页面壳多一个对话框与两个状态变量；被"仅移除"后保存的配置里，该 agent 在运行期不可路由（无节点）——属预期，需在面板说明文字中提示（"仅从画布移除，agent 的定义与提示词保留"）。

### ADR-R27-06: 差异清单对各节点类型删除的覆盖（constraint-driven）

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-012、INF-2、GR-A-001(b)、US-011。核对结果：服务端 `diff_snapshots` 对所有节点类型同样产出 `node_added` / `node_removed` / `node_changed`，对每条边产出 `edge_*`（`versioning.py:214-250`），且基线为文件态（`publish.py:184`），"新增后又删"净零无条目。缺口只在展示：`PublishDialog.vue:18-22` 对节点项显示英文类型代码。
- 约束来源与被排除方案：被排除——修改服务端 `DiffItem` 增加中文 / 展示字段：`DiffItem` 与 `_SUMMARY_LABELS`（`versioning.py:256-276`）同时用于版本历史、审计摘要（`summarize_diff`），改动面大且影响已存审计文本；约束 C-R27-01 / REQ-NFUNC-003 要求不回归。
- Decision: 服务端零改动；前端抽出纯函数 `formatDiffLine`（IFC-R27-008），对 `node_*` 三类把类型代码映射为 `graphModel.KIND_LABEL` 中文名，其余 kind 输出与现状逐字相同。
- Consequences:
  - 正向：AC-011-01/03 的"删除 条件分支节点：condition-9""新增 汇聚节点：join-10"可离线断言；INF-2 得到证实，不改变服务端。
  - 负向：版本历史对比（`config_views.py:568-586` 的 `_version_diff`）若也展示差异项，仍是旧格式——本轮不处理（不在需求内）。

### ADR-R27-07: 前端依赖与库能力使用边界（constraint-driven）

- Status: Accepted（沿用 R26 ADR-69，本轮重申）
- Type: constraint-driven
- Context: 画像 P8（禁 axios、运行期 CDN / 外链）、P6（前端 HTTP 只经 `client.ts`；hash 路由；Node 20/22 内置 node:test）、REQ-NFUNC-003。
- 约束来源与被排除方案：被排除——引入快捷键库（如 hotkeys / VueUse 直接依赖）：`@vue-flow/core` 1.48.2（`node_modules/@vue-flow/core/package.json`）已自带删除键机制，且 VueUse 仅为其传递依赖、未列入 `package.json`；原生 `document.addEventListener('keydown')` 足够。被排除——撤销 / 对话框用新库：Element Plus 已提供对话框与按钮。
- Decision: 零新增依赖；只用 `@vue-flow/core` 现有 `useVueFlow(id)`、`getSelectedNodes/Edges` 与原生 DOM 事件；`package.json` / `package-lock.json` 不改。
- Consequences: 正向——无供应链 / 体积 / 离线性新风险；负向——自有按键监听需自行保证卸载与输入焦点保护（由 IFC-R27-001/002 与结构断言覆盖）。

## 风险

| ID | 风险 | 缓解 |
|---|---|---|
| R-1 | `FlowCanvas` 把 `nodes` 映射为新对象（`FlowCanvas.vue:97`），图更新（如在面板里编辑后）可能使 vue-flow 选中标志丢失，Delete 键对节点暂无反应 | 面板"删除节点"按钮始终可用；GROUP_D 把"点击节点 → 编辑字段 → 按 Delete"列为手工验证项；若实测丢选中，GROUP_C 可在 FlowCanvas 以 `selectedId` 回填 `selected`（不改接口） |
| R-2 | 浏览器内真实按键 / 选中 / 悬停清理无法在 node:test 验证（无挂载环境、无无头浏览器，见 R26 测试局限） | 纯函数全覆盖 + 源码结构断言 + 手工清单；E2 前由用户在浏览器抽测 |
| R-3 | 文案承诺"可在版本历史回滚找回"依赖版本保留（上限 50）与回滚权限（manage 档） | 文案不承诺永久；OQ-ARCH-R27-01 记录 |

## 开放问题 / ASSUMPTION

| ID | 内容 | 类型 | 处理 |
|---|---|---|---|
| OQ-ARCH-R27-01 | "删除 agent"在提示词文件层面是硬移除（保存后从项目目录删除，仅靠版本快照 + 回滚兜底），与 R26 OQ-R26-11=A "软删 / 停用，历史保留"在文件层不完全同构；本轮按"只改文案、不改服务端"处置（ADR-R27-04）。是否另立项提供真软删（停用）入口？ | 非阻塞，交用户知悉 | 不影响本轮验收 |
| ASM-R27-01 | `[ASSUMPTION]` 节点 id 与专家名在 agent 节点上恒相等是项目约定（`graphModel.ts:108-121`、`graph.py:349`）；设计不依赖其恒成立（IFC-R27-005 分别取 `node.id` 与 `node.expert ?? node.id`） | 假设 | GROUP_C/D 用例覆盖 id≠expert 的桩数据 |
| ASM-R27-02 | `[ASSUMPTION]` "1 节点 + 1 边同时选中"视为多选并提示（节点不删），边仍由 vue-flow 既有逻辑删除；需求 REQ-FUNC-003 未逐字覆盖此组合 | 假设 | 交 GROUP_D 手工清单；如用户希望该组合"完全不动"，需关闭 vue-flow 自带删边并自管，另议 |
| ASM-R27-03 | `[ASSUMPTION]` 差异清单"含 N 条边"取"逐边列出"表述（AC-011-01 允许二选一），不做合并展示 | 假设 | 若要合并，前端 `formatDiffLine` 之上加分组，不涉服务端 |
| ASM-R27-04 | AC-009-05 查看档无撤销入口、AC-007-03 的 403 属 R26 既有服务端行为，本轮未改 | 说明 | 沿用 R26 测试 |

无需求冲突，无 CLARIFICATION_NEEDED。需求覆盖缺口：无（覆盖表见 `module_design.md`）。
