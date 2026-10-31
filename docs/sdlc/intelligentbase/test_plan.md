<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-31T15:46:11+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
    <file>docs/sdlc/intelligentbase/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划（REV-27 增量：配置画布节点删除，纯前端）

REV-26 APPROVED 版本已归档于 `archive/rev26/test_plan.md`（只读）；本文件按 REV-27 整体重写。

## 测试策略

- **被测改动**：MOD-R27-01 `nodeRemoval.ts`（新建）、02 `stores/configDraft.ts`、03 `publishDiff.ts` + `PublishDialog.vue`、04 `FlowCanvas.vue`、05 `AgentDetailPanel.vue`、06 `views/ConfigStudio.vue`。无后端、迁移、依赖清单、CI 改动。
- **范围（in）**：REQ-FUNC-001~013 与 REQ-NFUNC-002/003 中可离线验证的部分；US-001~011 的 50 组 AC。
- **范围（out）**：浏览器内真实按键与鼠标交互、vue-flow 选中态（风险 R-1）、悬停卡片视觉清理、1 秒响应（REQ-NFUNC-001，沿用 R26 INF-5，目标机校准前"未验收"）、线上生效后的终端提问路由。上述项**不记 PASS**，列入 `e2e_test_report.md` 的"上线后人工浏览器验收清单"。
- **环境**：Node v22.23.3（与 CI 一致，ci.yml:240 附近）；`src/frontend` 下 `npm run build && npm test`（node:test，`typescript` 为工程既有依赖，零新增依赖）；后端抽查用 `/root/.venvs/intelligentbase/bin/python`、`PYTHONPATH=src`、仓库根、离线（tests/conftest.py 设 `IB_OFFLINE_MODE=1`）。不连任何外部服务。
- **判定模式**：INCREMENTAL / baseline——每层相对基线零新增失败且新写用例全部通过；critical path（Must Have 故事的 E2E 级用例）覆盖 1.00。
- **基线（PM 实测，改动前 HEAD c1b491f，Node v22.23.3）**：前端 `npm test` 77 pass / 0 fail / 0 skip；后端未改动。本次另实跑后端全量作无关回归抽查（见各报告）。

### 测试加载方式（MOD-R27-07）

| 被测文件 | 方式 | 说明 |
|---|---|---|
| `nodeRemoval.ts`、`publishDiff.ts` | `ts.transpileModule` + `data:` URL；先转译 `graphModel.ts`，再把二者的 `'./graphModel'` 说明符替换为其 data URL | 真实执行产品代码 |
| `configDraft.ts` | 同上，并把唯一的运行期裸导入 `'vue'` 替换为 8 行最小替身（`ref`→`{value}`，`computed`→每次读取重算的 getter），`nodeRemoval` 说明符替换为其 data URL | **真实 store 代码**离线执行（dirty / applyRemoval / undoRemoval / load / discard / markSaved）；替身只提供存取，不改变被测语义。偏离 module_design MOD-R27-07 原计划（原计划仅做源码结构断言），属增强，已在测试文件头声明 |
| `FlowCanvas.vue`、`AgentDetailPanel.vue`、`ConfigStudio.vue`、`PublishDialog.vue` | 读源码 → `stripComments` → 正则 / 函数体抽取断言 | 无挂载环境，仅结构事实 |

### 分层口径（与 R26 一致）

R26 的前端用例（TC-FE-R26-*）在 Python 三层之外独立计数（"前端层"），其中纯函数执行与源码结构断言同属一个文件、不分层。**R27 沿用"前端独立于 Python 三层"，但为满足三份报告的逐层门控，本轮在前端内部按如下口径归层并保持各处一致**：

| 层 | 内容 | 用例 ID |
|---|---|---|
| unit | 单模块纯函数的真实执行（nodeRemoval / publishDiff）；后端 1 个纯函数文件 | TC-FE-R27-001~024、TC-UNIT-R27-001~002 |
| integration | 跨模块：真实 store ↔ nodeRemoval ↔ graphModel 的衔接；组件 / 页面壳与纯逻辑之间的源码结构契约 | TC-FE-R27-030~041、TC-FE-R27-050~060 |
| e2e（替代口径） | 真实产品函数 + 真实 store 的多步用户旅程（模型层）；**非真实浏览器** | TC-FE-R27-E01~E05 |

分层标记：前端用例以 ID 前缀 + `describe` 分组标识（node:test 无 tag 机制，与 R26 一致）；后端用例 `tests/unit/` 目录即层。

## AC 映射

图例：U = 单元，I = 集成，E = E2E 级（替代口径）；"现有"= 复用既有用例（回归）；"新写"= 本轮新增。运行方式均为离线真实执行（本项目 P11 为"无"，不适用 sim/hil/manual，浏览器项在人工清单）。位置：`F` = `src/frontend/tests/config_studio_r27.test.js`；`B` = `tests/unit/test_diff_node_removal_r27.py`。

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 前置 → 动作 → 预期（摘要） |
|---|---|---|---|---|---|
| AC-001-01 | TC-FE-R27-031、E03 | I、E | 新写 | F | 新增 3 节点 + 改最大步数 3 → 删 condition → 其余节点在、步数仍 3、dirty 仍真 |
| AC-001-02 | TC-FE-R27-011、E03 | U、E | 新写 | F | 空 predicate / 空话术节点 `removalVerdict.ok===true`；逐个删除不被拦截 |
| AC-001-03 | TC-FE-R27-016、020、E02 | U、E | 新写 | F | agent 仅从画布移除，无校验拦截，定义保留 |
| AC-001-04 | TC-FE-R27-055 | I | 新写 | F | 未选中节点分支为"点击画布上的节点…"且无按钮（源码） |
| AC-002-01 | TC-FE-R27-002、E01 | U、E | 新写 | F | Delete + 单选 + 画布焦点 → `request(nodeId)` |
| AC-002-02 | TC-FE-R27-007、052 | U、I | 新写 | F | 仅选边 → ignore；`:delete-key-code` 字面量保留（边仍由 vue-flow 删） |
| AC-002-03 | TC-FE-R27-001、006 | U | 新写 | F | 焦点在 INPUT/TEXTAREA/SELECT/contenteditable/弹窗内 → ignore |
| AC-002-04 | TC-FE-R27-008、E04 | U、E | 新写 | F | 2 节点（或 1 节点 + 1 边）→ hint「请选中单个节点后再删除」 |
| AC-002-05 | TC-FE-R27-009、E04 | U、E | 新写 | F | start 选中 Delete → `removalVerdict` 拒绝「开始 / 结束节点不可删除」，草稿不变 |
| AC-002-06 | TC-FE-R27-003 | U | 新写 | F | Backspace → ignore |
| AC-003-01 | TC-FE-R27-015、030、E01 | U、I、E | 新写 | F | condition-1（1 入 2 出，实际夹具 3 条）→ 3 条边全删、无悬空、相邻节点不变 |
| AC-003-02 | TC-FE-R27-016 | U | 新写 | F | 移除 billing-agent → 含分支键的出边消失；其余出边与 tau/margin/max_expert_steps/default_expert 不变 |
| AC-003-03 | TC-UNIT-R26-011（error_code_matrix）、TC-FE-R27-059 | U、I | 现有 + 新写 | `tests/unit/test_graph_validate_r26.py`；F | 服务端校验由既有用例锁定；前端弹窗逐条展示错误且无"忽略"、确认按钮禁用 |
| AC-003-04 | TC-UNIT-R26-005、E04（删 route 允许） | U、E | 现有 + 新写 | `tests/unit/test_graph_validate_r26.py`；F | 默认专家不可达由服务端裁决（既有）；前端允许删路由且不改 default_expert |
| AC-003-05 | TC-UNIT-R26-003（不连通判定）、TC-FE-R27-015 | U | 现有 + 新写 | 同上；F | 删除后相关节点与边从草稿消失，服务端不再对其报错（图中无此节点） |
| AC-004-01 | TC-FE-R27-012、E01 | U、E | 新写 | F | 2 条边 → 需确认，文案含「将同时删除 2 条边」 |
| AC-004-02 | TC-FE-R27-037、E01 | I、E | 新写 | F | 取消 → 快照逐字不变、dirty 不变、无撤销位 |
| AC-004-03 | TC-FE-R27-030、E01 | I、E | 新写 | F | 确认 → 节点与边删除 |
| AC-004-04 | TC-FE-R27-013、031 | U、I | 新写 | F | 本次新增 + 无边 → `needConfirm=false`，且 `confirm` 回调从未被调用 |
| AC-004-05 | TC-FE-R27-013、039 | U、I | 新写 | F | 基线节点无边 → 需确认，文案不含边数 |
| AC-004-06 | TC-FE-R27-013 | U | 新写 | F | 新增 + 1 条边 → 需确认，含「将同时删除 1 条边」 |
| AC-005-01 | TC-FE-R27-016、020、036、E02 | U、I、E | 新写 | F | 仅从画布移除：关键词、工具授权、主提示词草稿保留；出现在"尚未上图"列表 |
| AC-005-02 | TC-FE-R27-020、036、E02 | U、I、E | 新写 | F | 重新上图为未连线节点，值不变 |
| AC-005-03 | TC-FE-R27-036 | I | 新写 | F | 载荷中 experts 保留、prompts 保留、无 agent 删除（"保存后提示词仍在目录"的服务端半段见人工清单） |
| AC-005-04 | TC-FE-R27-014 | U | 新写 | F | definition 文案：定义与工具授权、边数、版本历史、历史会话不受影响、无"不可恢复" |
| AC-005-05 | TC-FE-R27-017、032 | U、I | 新写 | F | 节点、边、专家条目、工具授权消失；不在"尚未上图"列表 |
| AC-005-06 | TC-FE-R27-017、033 | U、I | 新写 | F | Builder 加入的 faq-agent 删除定义 → 载荷不含其任何字段与提示词；dirty=false |
| AC-005-07 | TC-FE-R27-010、041、054、E04 | U、I、E | 新写 | F | 默认专家两模式均拒绝；面板两按钮 `:disabled` + 提示文案 |
| AC-006-01 | TC-FE-R27-055 | I | 新写 | F | start/end 分支无按钮、有说明（源码） |
| AC-006-02 | TC-FE-R27-009、E04 | U、E | 新写 | F | end 选中 Delete → 拒绝，图与 dirty 不变 |
| AC-006-03 | TC-FE-R27-011、E04 | U、E | 新写 | F | route-1 可删；保存时才由服务端拒绝 |
| AC-007-01 | TC-FE-R27-054 | I | 新写 | F | 全部删除入口在 `v-if="!readonly"` 容器内 |
| AC-007-02 | TC-FE-R27-004、E04 | U、E | 新写 | F | readonly 下 Delete → ignore；`drive` 在 readonly 下不改草稿 |
| AC-007-03 | TC-INT-R26-070 | I | 现有 | `tests/integration/test_config_access_api_r26.py` | 查看档所有写接口 403，响应含所需档位 |
| AC-008-01 | TC-FE-R27-053、057 | I | 新写 | F | 图更新后清悬停卡片（源码）；删除后 `selectedId=null` → 面板回到占位。**视觉 / 1 秒 → 人工清单** |
| AC-008-02 | TC-FE-R27-021、031、058 | U、I | 新写 | F | 新增后删除 → `JSON.stringify` 与基线逐字相同 → dirty=false；按钮 `:disabled="!store.dirty.value"` |
| AC-008-03 | TC-FE-R27-031、E03 | I、E | 新写 | F | 另有改动时 dirty 仍真且改动保留 |
| AC-008-04 | TC-FE-R27-038 | I | 新写 | F | 放弃改动 → 快照回基线，已生效节点重现 |
| AC-009-01 | TC-FE-R27-030、E01 | I、E | 新写 | F | 撤销 → x=300/y=120、分支定义、3 条边端点与分支键恢复，快照 = 基线 |
| AC-009-02 | TC-FE-R27-032、E02 | I、E | 新写 | F | 撤销 agent 定义 → 全部恢复并进入保存载荷 |
| AC-009-03 | TC-FE-R27-022、034、051、E05 | U、I、E | 新写 | F | 其它编辑 / 保存 / 载入 / 放弃后撤销失效 |
| AC-009-04 | TC-FE-R27-035 | I | 新写 | F | 只恢复最近一次 |
| AC-009-05 | TC-FE-R27-056 | I | 新写 | F | 撤销条 `v-if="!readonly && store.canUndo.value"` |
| AC-010-01 | TC-FE-R27-051、057、060 | I | 新写 | F | 删除全程无 client / publish / 本地存储（结构侧）。**版本号 / 审计 / 文件哈希 / 线上路由 → 人工清单**（零写入由"未调用任何客户端"推出，不记为已验证线上） |
| AC-010-02 | TC-FE-R27-037、058 | I | 新写 | F | 预览与确认分离，取消不提交（结构），草稿保留 |
| AC-010-03 | 全量回归 | — | 现有 | `npm run build && npm test` | 77 个既有前端用例零新增失败 |
| AC-010-04 | TC-FE-R27-058、E05 | I、E | 新写 | F | 成功文案「已生效（版本 N）」后 `load()`；`markSaved` 更新基线 |
| AC-011-01 | TC-UNIT-R27-001、TC-FE-R27-023、E01 | U、E | 新写 | B；F | 服务端 `node_removed(before=类型)` + 每条相连边一个 `edge_removed`；前端渲染「删除 条件分支节点：condition-9」 |
| AC-011-02 | TC-UNIT-R27-002、TC-FE-R27-021 | U | 新写 | B；F | 净变化为零 → 服务端差异为空；前端快照与基线相同 → 保存按钮禁用 |
| AC-011-03 | TC-FE-R27-023 | U | 新写 | F | 「删除 汇聚节点：join-9」与「新增 汇聚节点：join-10」互不混淆 |
| REQ-FUNC-009(c) / ASM-R27-01 | TC-FE-R27-010、018、040 | U、I | 新写 | F | agent 节点 id ≠ 专家名：按专家名判默认 / 清定义 / 清补丁，按节点 id 删节点 |
| NFUNC-003 | TC-FE-R27-024、050、052、055、059、060；R26 全部既有 | U、I | 新写 + 现有 | F；R26 | 其余 diff kind 逐字不变；R26 锁定断言（delete-key-code、disabled、无忽略）不回归 |

## 测试数据需求

- 全部为测试内联夹具（`baseDoc()`：kb-agent 默认、billing-agent 关键词"发票"、faq-agent 未上图；condition-1 x=300/y=120；join-9 已生效无连线）；后端夹具复用 `tests/config_r26_support.py`。无持久化数据、无外部数据，不涉及 `[DATA_REQUIRED]`。
- 不写入任何持久存储，无需唯一化。

## 不可测项

| AC / 项 | 原因 |
|---|---|
| AC-008-01 的"1 秒内更新"与悬停卡片视觉消失；REQ-NFUNC-001 | `[INFERRED]` 阈值，需真实浏览器 + 目标机校准（沿用 R26 INF-5，校准前"未验收"）；本环境无无头浏览器且不得新增依赖。结构侧（图更新后清卡片的 watch）已由 TC-FE-R27-053 覆盖 |
| 风险 R-1：图更新后 vue-flow 选中态 + 真实 Delete 键（AC-002-01 的"画布焦点按键"端到端） | 需真实浏览器；本测试只验证判定函数与自维护选中集合的结构，不验证 vue-flow 事件真实触发 |
| ASM-R27-02：1 节点 + 1 边混选时 vue-flow 仍会删除被选中的边 | 需真实浏览器观察 |
| AC-010-01 的线上侧：版本号不变、审计无记录、文件哈希不变、终端提问仍路由 billing-agent | 需要真实环境；前端零写入由结构断言（TC-FE-R27-051/057）佐证，非线上验证 |
| AC-005-03 的"保存后提示词文件仍在项目目录"、AC-005-04 的"保存生效后提示词文件被移除" | 属保存后的服务端文件处置，后端本轮未改且无对应既有端到端用例；列入人工清单 |
| AC-007-03 之外的查看档真实点击 | 同上，浏览器项 |

以上项在 `e2e_test_report.md`"上线后人工浏览器验收清单"中给出步骤与期望结果，计数时标 NOT_TESTABLE（不计入通过率分母）。

## 用例位置索引

- 前端（52）：`src/frontend/tests/config_studio_r27.test.js`——unit 24（001~024）、integration 23（030~041 共 12、050~060 共 11）、e2e 级 5（E01~E05）。
- 后端（2，新写）：`tests/unit/test_diff_node_removal_r27.py`——TC-UNIT-R27-001、002（基名全局唯一）。
- 复用的既有后端用例：`tests/unit/test_graph_validate_r26.py`、`tests/unit/test_config_diff_conflict_r26.py`、`tests/integration/test_config_access_api_r26.py`。
