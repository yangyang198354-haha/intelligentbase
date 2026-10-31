<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-31T15:49:30+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/test_plan.md</file>
    <file>docs/sdlc/intelligentbase/unit_test_report.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（REV-27 节点删除）

REV-26 APPROVED 版本已归档于 `archive/rev26/integration_test_report.md`。上一层（unit）门控 PASSED，故执行本层。

## 摘要

- 执行时间：2026-10-31T15:41~15:48+08:00；环境同单元报告（Node v22.23.3；后端 `/root/.venvs/intelligentbase/bin/python`，离线）。
- 命令：`(cd src/frontend && npm run build && npm test)`；`python -m pytest tests/integration -q`。
- **本层新写用例**：total = pass + fail + skip + blocked + not_testable = 23 = 23 + 0 + 0 + 0 + 0（TC-FE-R27-030~041 共 12，TC-FE-R27-050~060 共 11）。
- 通过率 = pass/(pass+fail+blocked) = 23/23 = **1.00**。
- 另有 1 条被引用的既有集成用例（TC-INT-R26-070，AC-007-03）实跑通过，不计入新写。
- 判定模式：INCREMENTAL / baseline：新增失败 **0**，新写全部通过。**本层门控：PASSED**。

## 执行输出

```
$ cd src/frontend && npm test            （与单元报告同一次执行，23 个集成用例含在内）
# tests 129
# pass 129
# fail 0
# cancelled 0
# skipped 0
$ python -m pytest tests/integration -q
333 passed in 19.39s
$ python -m pytest tests/integration/test_config_access_api_r26.py -q
10 passed in 1.66s
```

## 分项结果

### 集成边界 A：真实 `configDraft` store ↔ `nodeRemoval` ↔ `graphModel`（store 代码真实执行，vue 为最小替身）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-FE-R27-030 | AC-009-01 | 删 condition-1（3 条边）→ 撤销：x=300/y=120、分支定义、3 条边端点与分支键恢复；快照 = 基线，dirty=false | PASS | — | — |
| TC-FE-R27-031 | AC-008-02/03、AC-004-04 | 新增 route 后删除 → dirty 回 false 且全程免确认；另有最大步数改动时 dirty 仍真且改动保留 | PASS | — | — |
| TC-FE-R27-032 | AC-009-02 | 删除 agent 定义 → 撤销：节点、相连边 e5/e8、专家、工具授权、补丁全部恢复并进入载荷 | PASS | — | — |
| TC-FE-R27-033 | AC-005-06 | Builder 加入的 faq-agent（含主/兜底草稿）删除定义 → 载荷不含任何字段，dirty=false | PASS | — | — |
| TC-FE-R27-034 | AC-009-03 | 拖动 / 改提示词 / 直接赋值文档 / 保存 / 重新载入 / 放弃改动 → 撤销失效且不改草稿 | PASS | — | — |
| TC-FE-R27-035 | AC-009-04 | 连删 route-1、join-9 → 撤销只恢复 join-9，无第二次撤销 | PASS | — | — |
| TC-FE-R27-036 | AC-005-01/02/03 | 仅从画布移除：载荷保留 experts 与提示词草稿，重新上图值不变 | PASS | — | — |
| TC-FE-R27-037 | AC-004-02、AC-010-02 | 取消确认 → 快照逐字不变、无撤销位 | PASS | — | — |
| TC-FE-R27-038 | AC-008-04 | 删除后"放弃改动"→ 快照回基线、已生效节点重现、补丁清空 | PASS | — | — |
| TC-FE-R27-039 | AC-004-04/05 | `isBaselineNode`：载入前 false；基线内 true；新增 false；`markSaved` 后新增节点转为基线 | PASS | — | — |
| TC-FE-R27-040 | ASM-R27-01 | 节点 id ≠ 专家名的 agent 经删除定义 → 撤销，快照还原 | PASS | — | — |
| TC-FE-R27-041 | AC-005-07、AC-006-02、AC-007-02 | 开始 / 结束 / 默认专家（两模式）/ 不存在 / 查看档的删除被拒：草稿不变、无撤销位、dirty=false | PASS | — | — |

### 集成边界 B：组件 / 页面壳 ↔ 纯逻辑与 store（源码结构契约）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-FE-R27-050 | 设计 MOD-R27-07 | `nodeRemoval.ts` / `publishDiff.ts` 运行期仅依赖 `./graphModel`，无 DOM / Vue / 存储 / 网络 | PASS | 首跑因正则误伤 `state.document.` 失败，已修测试 | 测试问题（已修） |
| TC-FE-R27-051 | REQ-NFUNC-002、AC-010-01 | `configDraft` 暴露撤销 API；load/discard/markSaved 均清撤销位；无存储 / 客户端引用；`canUndo` 以快照比较定义 | PASS | — | — |
| TC-FE-R27-052 | AC-002-02、AC-007-02 | FlowCanvas 保留 `:delete-key-code`、`deletable:false`、只读开关；`id="config-canvas"`；挂载注册 / 卸载移除 keydown；判定读自维护选中集合，不依赖 `getSelectedNodes` | PASS | — | — |
| TC-FE-R27-053 | AC-008-01（结构侧） | 图更新后清悬停卡片（目标不在新图才清）与失效选中；`@mouseleave` 保留 | PASS | — | — |
| TC-FE-R27-054 | AC-001-02、AC-005-07、AC-007-01 | 面板无 `window.confirm`；5 个"删除节点"+ 1 个"删除 agent"入口均在 `v-if="!readonly"` 容器内；默认专家两按钮禁用并提示 | PASS | — | — |
| TC-FE-R27-055 | AC-006-01、AC-001-04 | start/end 仅说明无按钮；占位文案分支无按钮；新增控件仅 `el-button`（与 TC-FE-R26-022 同口径） | PASS | — | — |
| TC-FE-R27-056 | AC-009-05、AC-005-02 | ConfigStudio 接线 `@request-remove`/`@hint`/`@remove-agent`；撤销条仅编辑档；放回画布选择框；旧二次确认已移除 | PASS | — | — |
| TC-FE-R27-057 | AC-010-01、REQ-NFUNC-002 | `requestRemove` 步骤顺序：只读短路 → 可行性 → 确认规则 → `window.confirm` → 变换 → `applyRemoval` → 清选中；函数体无 `client`/`publish`/`fetch`/`await` | PASS | — | — |
| TC-FE-R27-058 | AC-008-02、AC-010-02/04 | 保存按钮 / 放弃改动随 dirty 启停；`startSave` 先预览后弹窗；`confirmSave` 才 `publish`；成功文案「已生效（版本 N）」后重新载入 | PASS | — | — |
| TC-FE-R27-059 | AC-003-03、AC-011 | PublishDialog 经 `formatDiffLine` 渲染；无本地 `KIND_LABEL`；无"忽略"；错误逐条展示；有错误 / 无变更时确认禁用；取消不提交 | PASS | — | — |
| TC-FE-R27-060 | NFUNC-003 | 全部 R27 改动文件无 v-html / innerHTML / localStorage / axios / CDN；package.json 无浏览器 / 测试框架类新增依赖 | PASS | — | — |

### 引用的既有后端集成用例

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-R26-070 | AC-007-03 | 查看档所有写接口直接调用均 403，响应含所需档位 | PASS（在 `tests/integration` 整层 333 passed 与单文件 10 passed 中） |

## 与基线对比（baseline 模式）

- 前端基线 77 → 现 129，新增 52，失败 0。
- 后端 `tests/integration` 整层 333 passed、0 failed（后端未改动，等于基线）。
- 既有失败：无。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 无 | — | — |

## 局限

- 边界 B 全部为**源码结构断言**：证明"接线与约束字面量存在且顺序正确"，不证明组件在浏览器中的运行时行为（vue-flow 事件、响应式刷新）；这部分在 `e2e_test_report.md` 的人工验收清单中。
- `requestRemove` 在 ConfigStudio 内部（无导出），集成用例用测试内 `drive()` 复刻其步骤 1~5 来驱动真实产品函数；TC-FE-R27-057 以顺序断言锁定"复刻与源码一致"。若 ConfigStudio 以后改动步骤顺序，057 会先失败。
