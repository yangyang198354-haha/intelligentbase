<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-31T15:24:47+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（REV-27 增量）— 可视化配置：删除画布节点

**结论**：本轮**无新增依赖**，全部沿用现有前端栈；`package.json` / `package-lock.json` / `requirements*.txt` 均不改。完整技术栈基线见 REV-26 `archive/rev26/tech_stack.md` 与画像 P1。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增 / 沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | TypeScript（前端）；Python（服务端，不改） | `typescript ^5.4.0`、`vue-tsc ^2.0.0`（`src/frontend/package.json:25,27`）；Python 画像 P1 | 沿用 | 新增模块用 TS 纯函数，`vue-tsc --noEmit` 构建期校验类型 | 全部 | 无 |
| 前端框架 | Vue 3 + Element Plus + vue-router（hash） | `vue ^3.4.0`、`element-plus ^2.8.0`（`package.json:18-19`） | 沿用 | 确认用 `window.confirm`（同页既有）；选择框用 `el-dialog` + `el-radio-group` | REQ-FUNC-005/006 | 无 |
| 画布库 | `@vue-flow/core` | 声明 `^1.41.0`（`package.json:17`）；实装 1.48.2（`src/frontend/node_modules/@vue-flow/core/package.json`） | 沿用 | 使用 `useVueFlow(id)`、`getSelectedNodes/getSelectedEdges`、`<VueFlow id>`；依据见 module_design §领域与外部依赖出处 | REQ-FUNC-003 | `^1.41.0` 允许 minor 升级，选中状态 API 变化会影响 ADR-R27-01；`package-lock.json` 锁定缓解 |
| 状态管理 | 手写 `createConfigDraft()` store（无 Pinia） | `src/frontend/src/stores/configDraft.ts` | 沿用并扩展 | 撤销位以快照比较实现（ADR-R27-02） | REQ-FUNC-009/013 | 低 |
| 数据存储 | 无变更（SQLite 台账 / 文件态 / blob） | 画像 P1 | 沿用 | 删除只改内存草稿，无新表 | REQ-NFUNC-002 | 无 |
| 消息 / 缓存 | 无 | — | — | — | — | — |
| 测试 | Node 内置 `node:test`；用工程已有 `typescript` 做内存转译 | Node 22（CI，`.github/workflows/ci.yml:240`）；`"test": "node --test"`（`package.json:14`） | 沿用 | 新增 `src/frontend/tests/config_studio_r27.test.js`（画像 P3 位置约定）；纯函数真实执行 + 源码结构断言 | REQ-NFUNC-003 | 无组件挂载 / 无头浏览器环境：浏览器内交互无法离线验证（R-2） |
| 进程管理 / 容器化 | systemd；**无容器**（P8） | 画像 P7 | 沿用 | 无新增运行单元 | — | — |
| CI/CD | GitHub Actions 前端阶段 `npm ci && npm run build && npm test` | `ci.yml:240` 起 | 沿用 | 新测试文件自动被发现，无需改工作流 | REQ-NFUNC-003 | 无 |
| 部署方式 | 目标机本地 `npm run build` + 拷贝 web root；前端不重启服务 | 画像 P7 | 沿用 | 纯前端改动 | — | 需重新构建发布静态资源 |
| 新增依赖 | **无** | — | — | 画像 P8 禁 axios / CDN；快捷键 / 对话框均不需要新库 | — | — |

## 技术风险

### High
- 无。

### Medium
- **R-1 选中状态与 Delete 键**：`FlowCanvas` 每次渲染把节点映射为新对象，vue-flow 选中标志在图更新后是否保留未经浏览器实测。缓解：面板"删除节点"按钮始终可用；GROUP_D 列手工验证项；必要时 GROUP_C 以 `selectedId` 回填 `selected`（接口不变）。
- **R-2 离线测试局限**：无组件挂载环境，浏览器内按键 / 悬停清理 / 1 秒响应只能手工或在目标浏览器验证。缓解：把决策集中到纯函数并全分支覆盖，其余用源码结构断言 + 手工清单；1 秒目标沿用 R26 INF-5，校准前"未验收"。

### Low
- **`@vue-flow/core` minor 升级**：缓解为 `package-lock.json` 入库、`npm ci` 复现。
- **`window.confirm` 阻塞式**：与现有交互一致，接受。
- **R-3 回滚找回的时效**：文案依赖版本保留上限 50 与 manage 档回滚权限；文案不承诺永久（见 architecture_design OQ-ARCH-R27-01）。
- **许可证 / 维护风险**：无新增第三方依赖，故无新增许可证登记项（`@vue-flow/core` MIT，沿用 R26 登记）。
