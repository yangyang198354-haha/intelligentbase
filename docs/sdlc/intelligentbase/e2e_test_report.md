<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-27T16:13:50+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>test_plan.md</file>
    <file>unit_test_report.md</file>
    <file>integration_test_report.md</file>
    <file>user_stories.md</file>
    <file>phase_status.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（REV-26）

## 摘要

critical path 口径：替代（后端多步 API 旅程：Django 测试客户端 + 真实账户体系 + 真实发布/运行时/检索管线，离线替身；本机无可用无头浏览器，浏览器内交互不在其内）

- 0.2.0（GR-D-001 缺陷回流复测，2026-10-27T16:12+08:00）：DEF-R26-001/002 FIXED 复测通过，DEF-R26-003 PM 裁决关闭；critical path **如实仍为 0.96**，缺口 US-003 待用户裁决，测试工程师推荐方案：**上线后人工浏览器验收**（清单见文末），不自行改判。
- 命令：`python -m pytest tests/e2e -q`；环境：`/root/.venvs/intelligentbase/bin/python`，`PYTHONPATH=src`，仓库根，离线。
- **新写 E2E 用例**：total = pass + fail + skip + blocked + not_testable = 6 = 6 + 0 + 0 + 0 + 0；**整层**：total = 51 = 51 + 0 + 0 + 0 + 0（基线 45 + 新写 6）。
- critical path 覆盖率 = 有 E2E 旅程用例的 Must Have 故事 / Must Have 故事总数 = **23 / 24 = 0.96**。缺口：US-003（编排图随编辑实时更新）——其 AC 全部是浏览器内交互，无法以后端旅程表达；已以前端模型/结构用例（TC-FE-R26-010/024，执行通过）覆盖其模型层，真实交互列入“未验证”。其余 23 个 Must 故事均有 ≥1 条 E2E 旅程（见下表）。
- critical path 通过率 = pass/(pass+fail+blocked) = 6/6 = **1.00**（旅程用例）。
- 判定模式：INCREMENTAL / baseline：整层相对基线（45）**新增失败 0**，新写 6/6 通过。
- **本层门控：PASSED**（测试工程师口径）。须 PM 注意：invocation 要求“critical path 覆盖 1.00”，实测 0.96，缺口仅 US-003（浏览器交互，无法验证、**不记 PASS**）；是否接受由 PM 门控裁决。上一层（integration）门控 PASSED，故执行本层。
- 另：前端层（独立于 Python 三层）：`npm run build` 成功，`npm test` 77/77（基线 57 + 新写 20），见下。

Must Have 故事 → E2E 旅程覆盖表：

| 旅程 | 覆盖的 Must 故事 |
|---|---|
| TC-E2E-R26-001 Builder→预览→保存热生效→回滚→审计 | US-014、016、017、023、024、027 |
| TC-E2E-R26-002 并发编辑冲突（409→草稿副本→合并）+ 进行中回答 | US-014、015、018 |
| TC-E2E-R26-003 旧项目升级：基线 v1/用户 v2/回滚后行为等价 | US-017、020 |
| TC-E2E-R26-004 三档权限升级 + 跨项目隔离 | US-010、019 |
| TC-E2E-R26-005 编排编辑：含环/重名被拒→合法图（路由+汇聚+新 agent）→路由/兜底→运行时范围与参数 | US-001、002、004、006、007、009、011、013、021 |
| TC-E2E-R26-006 Builder 安全：越权需求被适配→10 次同分→出站零 canary→云端不可用手工可用 | US-024、025、026、030 |

## 全量回归

- 命令：按层串行 `python -m pytest tests/unit|integration|e2e|agents -q`（未加覆盖率参数；0.2.0 未再单独跑 `pytest tests` 合并命令，合计为四层之和）；合计：**908 passed**；公式：908 = unit 509 + integration 333 + e2e 51 + agents 15。
- 相对基线新增失败数：**0**（基线 unit 314 / integration 232 / e2e 45 / agents 15 全部仍通过；新写 195 + 101 + 6）。
- 分层命令的原文计数行（均为最后一次执行）：
  - `509 passed in 23.31s`（unit）
  - `333 passed in 449.62s (0:07:29)`（integration）
  - `51 passed in 40.56s`（e2e）
  - `15 passed in 0.08s`（tests/agents）
- 前端：`cd src/frontend && npm run build`（0.2.0 未重跑，前端未改；0.1.0 结果）→ `✓ built in 31.43s`（vue-tsc + vite，仅既有 chunk 超 500 kB 警告）；`npm test` → `# tests 77 / # pass 77 / # fail 0 / # cancelled 0 / # skipped 0`（基线 57；新写 20：`src/frontend/tests/config_studio_r26.test.js`）。
- 离线自检（0.1.0 结果，0.2.0 未重跑）：`python src/scripts/selfcheck.py` → `自检结果：57/58 通过`，唯一失败 `core_framework_free`（`sitecustomize`，解释器环境所致；GR-C-001 已核 HEAD 干净导出同样失败，**既有，非本轮引入**）。

## 用户旅程

### TC-E2E-R26-001: Builder 生成 → 差异预览 → 保存热生效 → 回滚 → 审计
- 关联：US-024 / 027 / 016 / 014 / 017 / 023；环境：accounts_app（内存台账）、FakeLlm 云端替身
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 编辑档 `POST /api/builder/draft` | 200，草案 name=billing-agent；版本仍 0 | 一致 | PASS |
| 2 | `POST /api/config/publish/preview` | 差异含 agent_added billing-agent | 一致 | PASS |
| 3 | `POST /api/config/publish`（用户修改后的提示词） | 200，version=2，applied=true | 一致 | PASS |
| 4 | 终端提问“我的发票怎么报销” | 版本 2，由 billing-agent 以用户修改后的提示词作答 | 一致 | PASS |
| 5 | 管理档 `POST /api/config/rollback` → v1 | 200，version=3 | 一致 | PASS |
| 6 | 再次提问 | 版本 3，回到 kb-agent | 一致 | PASS |
| 7 | 审计 | 含 builder.egress / config.publish / config.rollback / access.grant；历史 [3,2,1] | 一致 | PASS |
- 结论：PASS

### TC-E2E-R26-002: 并发编辑冲突
- 关联：US-018 / 015 / 014
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 甲、乙基于 v0；甲保存 | 200 | 一致 | PASS |
| 2 | 乙保存（陈旧基线） | 409，回执含冲突对象 | 一致 | PASS |
| 3 | 乙另存草稿副本 | 201 | 一致 | PASS |
| 4 | 乙重新载入，甲的改动在位；基于新版本合并保存 | 200，version+1 | 一致 | PASS |
| 5 | 持旧租约的进行中回答 | 仍版本 0、旧专家作答 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R26-003: 旧项目升级与回到基线
- 关联：US-020 / 017
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 未保存提问 | 版本 0 正常作答 | 一致 | PASS |
| 2 | 首次保存 | 历史 [(2,publish),(1,baseline)] | 一致 | PASS |
| 3 | 回滚到 1 | 200 | 一致 | PASS |
| 4 | 同 3 个问题再问 | 与升级前作答专家逐一相同 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R26-004: 权限与跨项目隔离
- 关联：US-010 / 019
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 查看档保存 | 403，required_level=edit | 一致 | PASS |
| 2 | 管理档改其档位为编辑 | 200，审计 1 条 | 一致 | PASS |
| 3 | 该账号保存 | 200 | 一致 | PASS |
| 4 | p_beta 管理档读 p_alpha（头声明） | 403，不含 billing-agent | 一致 | PASS |
| 5 | p_beta 自己的配置 | 版本 0，仍只有 kb-agent | 一致 | PASS |
- 结论：PASS

### TC-E2E-R26-005: 编排编辑旅程
- 关联：US-001 / 002 / 004 / 006 / 007 / 009 / 011 / 013 / 021
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 查看档读 catalog / 提示词全文 | 卡片摘要与全文一致 | 一致 | PASS |
| 2 | 提交含环图；提交重名 agent | 400 graph_cycle；400 expert_name_duplicate；版本 0 | 一致 | PASS |
| 3 | 提交合法图（route + join + 新 agent + 目录范围 + top_k=1 + 步数 2） | 200，version=2 | 一致 | PASS |
| 4 | 提问“发票”/“天气” | billing-agent；kb-agent（兜底） | 一致 | PASS |
| 5 | 新 agent 检索 | 只见“产品手册”，仅 1 条；kb-agent 可见 2 条以上 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R26-006: Builder 安全旅程
- 关联：US-024 / 025 / 026 / 030
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 敌意需求 + 越权模型输出 | 草案仅含既有工具/目录，步数回默认 4，适配说明 2+2+1 | 一致 | PASS |
| 2 | 同草案评审 10 次 | 总分与各维度一致，扣分均有证据 | 一致 | PASS |
| 3 | 扫描全部出站载荷 | 无资料 canary、无 project_id、无凭据模式 | 一致 | PASS |
| 4 | 未配置 Key | 503，含“尚未配置 LLM Key”，版本不变；手工发布成功 | 一致 | PASS |
- 结论：PASS

## 缺陷与观察

| DEF | 级别 | 状态（0.2.0） | 现象与处置 | 复测用例 | 位置 |
|---|---|---|---|---|---|
| DEF-R26-001（= CR-001） | MINOR | **FIXED，复测通过** | 并行超步内执行数可超全图步数上限（上限 2、1+3 并行曾执行 4 个）。修复后执行数严格 ≤ 上限，被截分支记 skipped_step_cap，仍有应答 | TC-INT-R26-024（已改 AC 断言）、150~153 | src/ib/orchestration/dag.py |
| DEF-R26-002 | MINOR | **FIXED，复测通过** | temperature 曾被静默忽略（200）。修复后保存路径对请求体 temperature 返回 400（顶层 error.code=validation_error，items[].code=field_not_editable，PM 裁决视为满足 AC-021-03），不落盘不产生版本，写 rejected 审计 | TC-INT-R26-059（已改 AC 断言）、154~156 | src/ib/config/definition.py、src/ibweb/views.py、src/ibweb/config_views.py |
| DEF-R26-003 | MINOR | **PM 裁决关闭**，AC-030-02 待下次 GROUP_A 改措辞 | 1 次生成产生 2 条外发审计（generate + judge）；PM 裁决保留实现（每次外发各 1 条审计），TC-INT-R26-098 即规格 | TC-INT-R26-098 | src/ib/builder/service.py、egress.py |

当前待开发修复缺陷：0。

观察项（不计缺陷，供 PM/开发参考）：
- OBS-R26-01：`build_agent_tools` 文档串（src/ib/tools/__init__.py:416-429）称参数越界“编译期 fail-fast”，实测不抛（TC-UNIT-R26-153）；越界值由保存/发布路径的 `validate_tool_params` 拦截（TC-UNIT-R26-069、TC-INT-R26-045），不会入库，影响仅限文档串与纵深防御。
- OBS-R26-02：AC-025-03 示例中 top_k “范围 1–20、默认 5”与真实工具声明（1–50、无声明默认值）不同；实测越界值被**移除**并列入适配说明（而非调整为 5）。建议 PM 在下次需求修订时校准 AC 示例。
- OBS-R26-03：v1 旧项目首次保存在写文件阶段失败时，升级前基线 v1 已与 pending 同事务落点，故 head 停在基线 v1（内容等价于升级前文件态，可回滚/可继续保存）。version 号由 0 变 1，不影响行为（TC-UNIT-R26-141、TC-UNIT-R26-126）。
- OBS-R26-04：把令牌放在查询串访问配置端点返回 400（非 401），仍被拒且不泄露内容（TC-INT-R26-079）。
- OBS-R26-05：`NodeHoverCard` 无延迟逻辑（即时显示），“300 ms 内出现”无可度量对象（AC-001-01/022-01 的时限不可测）。

## 未验证清单（不记 PASS）

浏览器内真实交互因本机无可用无头浏览器且不得新增依赖，下列 AC 只有模型层/源码结构层覆盖，**真实点击/渲染/时限未验证**：

| AC | 未验证部分 | 已有的替代覆盖 |
|---|---|---|
| AC-001-01 / 022-01 | 悬停卡片 300 ms 内出现、30 节点悬停流畅 | TC-FE-R26-001（卡片数据）；TC-UNIT-R26-015（校验耗时下界） |
| AC-003-01~03 | 页面内 1 秒联动、“未保存”标记、放弃/重新载入的真实点击 | TC-FE-R26-010/024（模型 + 源码结构） |
| AC-004-01/05 | 画布出现节点；克隆流程的界面操作 | 手工路径经 API 发布（TC-INT-R26-099/109） |
| AC-011-01/02/04 | 真实拖拽、连线、删除键、只读档实际不可拖拽/无句柄 | TC-FE-R26-006/009/021（预校验、位置回写、源码 `:nodes-draggable="!readonly"`） |
| AC-018-02/03 | 冲突对话框两个按钮的真实点击 | TC-INT-R26-053、TC-E2E-R26-002（接口层）；TC-FE-R26-025（源码） |
| AC-019-02 / 030-05 | 页面无弹窗（`<script>` 纯文本渲染） | TC-FE-R26-020（无 v-html/innerHTML）；TC-INT-R26-107（响应为 JSON 字面量） |
| AC-024-02 / 028-01/02 | “加入画布”“逐项采纳差异”的界面操作 | TC-INT-R26-106/109（接口层） |
| AC-022-02 | 拖拽 10 节点后保存、画布无重叠 | — |

## 目标机上线验证项（离线不可测，建议并入 E1 部署计划）

1. **热生效 5 秒**（AC-014-01/017-02）：用 `src/scripts/hot_effect_probe.py` 在目标机两进程（ib-web 多线程 + ib-worker 若涉及）上实测 head 探测间隔 `IB_CONFIG_HEAD_CHECK_INTERVAL_S` 下的收敛时间；100 次提问版本一致（AC-014-04）。
2. **30 节点 / 60 边**画布悬停 ≤300 ms、保存校验 ≤2 s（AC-022）。
3. **真实 DeepSeek 路径**（TBD-T32/T36）：Builder 生成/评审/优化、`run_tool_loop(on_unauthorized=)` 的真实 langchain 分支、60 s 超时（AC-030-04）。
4. **SQLite 版本**：目标机 `sqlite3 --version` ≥ 3.35 方可使用 008 回滚注释中的 `DROP COLUMN`；`ALTER TABLE ADD COLUMN … CHECK` 在目标机行为（开发机 3.45.1 已验）。
5. **ci.yml 迁移检查加 008**（E1 待办，本组不改 ci.yml）；上线需 ib-web / ib-worker 各重启一次（nginx 无改动）。
6. 上线后核对：`users.config_level` 补列后存量 ops 账号为 manage（TC-INT-R26-123 已在老库形态上验证逻辑）。

## 上线后人工浏览器验收清单（供 E1 部署计划引用）

背景：本机无无头浏览器且不得新增依赖，下列项目离线无法执行，**不记 PASS**；建议在目标机上线后由有「管理」档的验收人员用真实浏览器逐条执行（critical path 缺口 US-003 的推荐处置方案，须用户裁决后生效）。验收用独立测试项目与测试账号，不动生产业务配置；测完用“回滚”回到验收前版本。

### A. US-003（编排图随编辑实时更新，Must）

| # | 对应 AC | 操作步骤 | 期望结果 |
|---|---|---|---|
| A1 | AC-003-01 | 编辑档打开配置页，在表单中新增一个 agent 并填写名称 | 1 秒内画布出现对应节点；默认专家带“默认”标记 |
| A2 | AC-003-01 | 修改某 agent 的显示名/参数（不保存） | 画布节点标签同步更新，页面出现“未保存”标记 |
| A3 | AC-003-02 | 在画布上拖动节点并连线后，点击“放弃” | 画布与表单恢复到最近一次已保存状态，“未保存”标记消失 |
| A4 | AC-003-03 | 有未保存修改时点击“重新载入”或切换项目 | 弹出确认；取消则修改保留，确认则载入最新已保存版本 |

### B. 其余未验证清单项

| # | 对应 AC | 操作步骤 | 期望结果 |
|---|---|---|---|
| B1 | AC-001-01 / 022-01 | 鼠标悬停任一节点；再对 30 节点图重复 | 卡片在约 300 ms 内出现（占位阈值，开发者工具计时），内容含中文标签、name、工具、提示词前 120 字符；30 节点悬停不卡顿 |
| B2 | AC-004-01 / 004-05 | 手工新建 agent 并保存；再对已有 agent 点“克隆” | 保存后画布出现节点且提问可路由到它；克隆生成同配置草稿，重名时被提示且不能保存 |
| B3 | AC-011-01 / 011-02 | 拖拽节点、从节点连线到另一节点、选中边按删除键 | 位置保存后刷新一致；非法连线（如造成环）被预校验拦截并提示；删除键删除所选边 |
| B4 | AC-011-04 | 用查看档账号打开配置页 | 节点不可拖拽、无连线手柄、所有输入框禁用；保存按钮不可用 |
| B5 | AC-018-02 / 018-03 | 两个浏览器（甲、乙）基于同一版本编辑；甲先保存，乙再保存 | 乙看到冲突对话框；点“重新载入”看到甲的改动；点“另存为草稿副本”生成副本且乙的编辑不丢 |
| B6 | AC-019-02 / 030-05 | 在 agent 名称/提示词/Builder 需求中输入 `<script>alert(1)</script>` 并保存、查看卡片与审计页 | 页面无弹窗，内容以纯文本原样显示 |
| B7 | AC-024-02 / 028-01 / 028-02 | Builder 生成草案后点“加入画布”；对已有 agent 点评审，逐项采纳修订差异 | 草案节点加入画布但未发布；采纳逐项生效；确认发布前线上版本不变 |
| B8 | AC-022-02 | 拖拽 10 个节点后保存 | 保存成功；画布无节点重叠；服务端校验在 2 s 内返回 |
| B9 | AC-014-01 / 014-04 / 017-02（目标机） | 发布后立即连续提问 100 次 | 5 秒内新版本生效，100 次提问绑定版本一致；响应与页面不出现“重启”字样 |
| B10 | AC-030-04（目标机） | 配置真实 Key 触发一次 Builder 生成；再在不可达条件下重试 | 正常时返回草案；不可达时 60 s 内给出可读错误，手工创建仍可用 |

记录方式：验收人填写 通过/不通过 + 截图（不含凭据）；不通过项按缺陷回流。
