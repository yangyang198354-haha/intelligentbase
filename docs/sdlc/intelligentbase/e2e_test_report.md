<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-24T23:25:21+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>user_stories.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>test_plan.md</file>
    <file>unit_test_report.md</file>
    <file>integration_test_report.md</file>
    <file>phase_status.md</file>
    <file>implementation_plan.md（2.0.0）</file>
    <file>code_review_report.md（2.0.0）</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，intelligentbase-GROUP_D-001）

## 摘要

critical path 口径：替代（Django 测试客户端 + 真实认证头 + 真实上传 / worker 处理 / 检索管线的多步 API 旅程；项目无浏览器 E2E 框架）

- 执行时间：2026-10-24T23:22 起（缺陷回流复测，本层最后一次执行；0.1.0 初测为 22:41）；环境同单元报告。
- 命令：`python -m pytest tests/e2e -q`；计数行（原文）：`45 passed in 10.41s`
- **total = pass + fail + skip + blocked + not_testable = 45 = 45 + 0 + 0 + 0 + 0**（既有 29 + 新写 16：TC-E2E-R25-001~016）
- 通过率 = 45/(45+0+0) = **1.00**；判定模式 baseline（相对基线零新增失败且新写用例全部通过）。
- **critical path 覆盖率** = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = **13 / 13 = 1.00**（US-001~011、US-015、US-017）。
- **critical path 通过率** = critical path 用例 PASS / 总数 = 15 / 15 = **1.00**（TC-E2E-R25-001~013、015、016；TC-E2E-R25-014 对应 Should Have 的 US-013，不计入 critical path）。
- **本层门控：PASSED**。

### 缺陷回流复测摘要（defect_loops=1）

- E2E 层测试文件未改动，复测 45 passed（`45 = 45 + 0 + 0 + 0 + 0`）；critical path 覆盖率 13/13 = 1.00、通过率 15/15 = 1.00，重新计算无变化（回流新增用例位于集成层与前端冒烟层，不属 Must Have 故事的 E2E 用例）。
- DEF-R25-001 涉及的 Must Have 故事 US-008 / US-010：succeeded 窗口的服务端语义由集成层 TC-INT-R25-055~059 复测（见集成报告），E2E 旅程 009/013 保持通过。
- **DEF-R25-001：FIXED-VERIFIED；DEF-R25-002：FIXED-VERIFIED**（前端冒烟 TC-FE-46，见下）。

### Must Have 故事 → E2E 用例

| 故事 | E2E 用例 | 重点 AC |
|---|---|---|
| US-001 | 001 | AC-001-01/02/04 |
| US-002 | 001、002 | AC-002-01/02 |
| US-003 | 003、004 | AC-003-01/02/03（跨项目 404、归属断言 403） |
| US-004 | 005 | AC-004-01/02 |
| US-005 | 005 | AC-005-01/02 |
| US-006 | 006、007 | AC-006-01~04（含删除后检索命中 0） |
| US-007 | 008 | AC-007-01/02 |
| US-008 | 009、013 | AC-008-01/02/03/07（旧版可检索 → 成功切换 → 失败保留旧版） |
| US-009 | 010 | AC-009-01~04（三个时间） |
| US-010 | 001、004、011 | AC-010-01/02/03 |
| US-011 | 012、013 | AC-011-01~05（含大小写） |
| US-015 | 015 | AC-015-01/02/04（整体拒绝、无半成品）、AC-015-03（配置可调） |
| US-017 | 016 | AC-017-01/02（老库升级后在根目录且可检索） |

## 全量回归

```
$ python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q
...
TOTAL                              11731   2373    80%
605 passed in 129.40s (0:02:09)
```

- 分层构成：unit 314 + integration 225 + e2e 45 + agents 21 = 605（= 基线 436 + 新写 169）。
- **相对基线新增失败数：0**。0.1.0 时 PM 复跑的 3 个失败（TC-INT-044、TC-UNIT-019、TC-UNIT-070）已按 GR-C-001 条件 1 同步并通过；回流复测中冻结用例已翻转，不再有预期失败；无既有失败。覆盖率仅记录不设门。
- 辅助：`python -m pytest tests/agents -q` → `21 passed in 0.09s`。

```
$ python src/scripts/selfcheck.py
...
自检结果：53/54 通过
失败项：
  - core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）: AssertionError: ib/core 引入了第三方顶层包：sitecustomize
```

selfcheck：53/54，唯一失败 `core_framework_free`（`sitecustomize`，Ubuntu 系统 site 在解释器启动时加载所致）= **基线既有环境项**（PM 基线 51/52 同一项）。selfcheck 为独立层，不并入 pytest 算术。

### 前端冒烟（独立层，不并入 Python 三层算术）

```
$ (cd src/frontend && npm run build && npm test)
✓ built in 29.24s
# tests 46
# pass 46
# fail 0
# skipped 0
```

46 = 既有 40 + 新写 6（TC-FE-41~46：冲突弹窗三选项与取消语义、批次 store 并发 2 / 进度 / 原因文案 / 限额提示、浏览器三时间与权限隐藏、删除对话框、客户端方法与冲突体；回流新增 TC-FE-46 限额文案字面断言）。0.1.0 已同步的过时断言（REV-18 子用例 #32，`uploadFile(picked.value)` 退役上传器断言 → 目录式上传入口 / `webkitdirectory` / `planUpload` / `uploadBatchItem` 断言）保持通过。

### TC-FE-46：DEF-R25-002 限额提示文案断言（回流新增）

- 关联：US-015 / AC-015-01、AC-015-02、AC-015-04；位置：`src/frontend/tests/frontend.smoke.test.js` 用例 46（去注释后的 `uploadBatch.ts` 源码断言）。

| 断言 | 期望（与 AC 字面一致） | 结果 |
|---|---|---|
| `limit_files` | 模板串 `单次最多上传 ${raw.limit} 个文件（当前 ${raw.actual ?? '?'}）` → 1000/1001 时为"单次最多上传 1000 个文件（当前 1001）"（AC-015-01） | PASS |
| `limit_total_bytes` | `单次上传总大小超过上限（当前 ${mb(raw.actual ?? 0)}，上限 ${mb(raw.limit)}）`（AC-015-04，含实际值与上限 L） | PASS |
| `depth_exceeded` | `目录层级最多 ${raw.limit} 层` → "目录层级最多 10 层"（AC-015-02） | PASS |
| 旧文案 | 不得残留 | PASS |

边界说明：项目无组件挂载框架，本断言为源码模板串字面断言；后端 `error.details` 的 limit/actual 由 TC-INT-R25-030、TC-E2E-R25-015 真实执行断言。

## 用户旅程

用户旅程 TC-E2E-R25-001~016 本轮未改动，复测全部 PASS（`45 passed`）；步骤表沿用 0.1.0 记录。

### TC-E2E-R25-001: 整个文件夹上传 → 汇总 → 浏览 → 索引 → 问答可检索（含引用路径）
- 关联：US-001 / US-002 / US-010；AC-001-01/02/04、AC-002-02、AC-010-01、AC-014-01；环境：Django 测试客户端 + 离线令牌（管理者，p_alpha）
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | dry-run 计划 4 个文件（A/x.txt、A/B/y.md、A/bad.exe、A/fake/q.pdf） | 200，batch_id=null，conflicts=[]；资料库未变化 | 200 / null / [] / total=0 | PASS |
| 2 | 提交批次并逐文件 PUT | x、y accepted；bad.exe 跳过 UNSUPPORTED_TYPE；q.pdf 跳过 MAGIC_MISMATCH | (accepted, accepted, skipped, skipped)，原因码一致 | PASS |
| 3 | GET 批次汇总 | 成功 2 / 跳过 2 / 失败 0 / pending 0（和 4） | (2,2,0,0,4) | PASS |
| 4 | 逐级浏览 | A 下 x.txt + 子文件夹 B；B 下 y.md；面包屑 [A,B]；fake / bad 所在目录与文件均未创建；y.md 初始 pending | 一致 | PASS |
| 5 | worker 处理后检索 y 独有内容 | y.md indexed、chunk_count>0、indexed_at 非空；命中引用路径 `A/B/y.md` | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-002: 100 文件汇总 95/5/0 与单调进度
- 关联：US-002；AC-002-01/02；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 提交含 95 合规 + 3 不支持 + 1 空 + 1 超 50MB 的清单 | 201；total=100，accepted_count=95，skipped_count=5 | (100,95,5) | PASS |
| 2 | 逐个 PUT 95 个文件，每次读汇总 | 已处理数单调不减，最终 =100 | 序列单调不减，末值 100 | PASS |
| 3 | 终态汇总 | (95,5,0,0)；5 个跳过项带相对路径与原因（3×UNSUPPORTED_TYPE、EMPTY_FILE、TOO_LARGE） | 一致；目录内 95 个文件 | PASS |
- 结论：PASS

### TC-E2E-R25-003: 云盘式浏览：逐级进入、面包屑、返回、150 条分页
- 关联：US-003；AC-003-01/02；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 进入 A → B | 各目录仅含直接子项；面包屑 [A]、[A,B] | 一致 | PASS |
| 2 | 点击面包屑 A | 回到与进入 A 时完全相同的内容 | 完全相等 | PASS |
| 3 | 150 条目分页（page_size=100） | 每页 ≤100；无重复无遗漏；文件夹在前、名称升序；刷新一致 | 100+50，150 个唯一名称，顺序一致 | PASS |
- 结论：PASS

### TC-E2E-R25-004: 跨项目访问：404 不可区分 / 归属断言 403 / 问答隔离
- 关联：US-003 / US-010；AC-003-03、AC-010-02；环境：真实账户体系令牌（全局管理员 + 绑定 p_alpha 的运维账户）
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理者在 p_beta 建目录 `乙项目机密目录` 并入库文件 | — | 已建 | PASS |
| 2 | p_alpha 运维账户按该目录 id 浏览 / 取详情 | 404，响应体与访问一个不存在 id 逐字相同，不含目录名 | 两者 404 且 content 相等 | PASS |
| 3 | 运维账户声明 X-IB-Project=p_beta | 403 project_mismatch | 403 / project_mismatch | PASS |
| 4 | p_alpha 检索 p_beta 独有内容；p_beta 自检（成对） | p_alpha 无命中；p_beta 命中 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-005: 新建 / 重命名文件夹，文件仍已索引、引用路径随之改变
- 关联：US-004 / US-005 / US-016；AC-004-01/02、AC-005-01/02；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 建 D → 建 `设计`；重复建（含首尾空白） | 201 立即可见且为空；重复 409 | 一致 | PASS |
| 2 | 入库 3 个文件；把 `其它` 重命名为 `设计` | 409，原名保持 | 一致 | PASS |
| 3 | 把 `设计` 重命名为 `新名` | 200；3 个文件仍 indexed；面包屑 [D,新名] | 一致 | PASS |
| 4 | 检索其内文件 | 引用路径均以 `D/新名/` 开头，不含 `设计` | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-006: 递归删除文件夹（确认 → 分步 → 检索 0 命中）
- 关联：US-006；AC-006-01/02；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 取详情；缺 confirm 的 DELETE | 详情 (2,10)；缺 confirm → 400；取消后内容原样 | (2,10)；400；仍 10 个文件 | PASS |
| 2 | 确认后分步删除（max_files=4） | 每步 4/4/2 个，最后一步 done=true、failed=[] | [4,4,2]，done | PASS |
| 3 | 删除后 | 根目录仅剩 keep.txt；10 个文件向量数 0；各独有关键词命中该文件 0 条；keep.txt 仍可检索；目录详情 404 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-007: 删除部分失败可见 → 恢复；处理中文件被删后 worker 安全退出
- 关联：US-006；AC-006-03/04；环境：同上，向量清理注入故障
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 1 个文件向量清理失败（另有 1 个 parsing 文件）时 DELETE | done=false；failed 列出该文件（路径 `部分失败/内层/p3.txt`，无内部细节）；remaining_files=1；已删 6 个 | 一致 | PASS |
| 2 | 浏览 | 失败文件及其目录链仍可见；parsing 文件已被删 | 一致 | PASS |
| 3 | worker 带旧认领记录继续 | 受控 `_DeletedConcurrently`，不写回；检索无命中 | 一致 | PASS |
| 4 | 向量库恢复后再删 | done=true、failed=[]、目录消失、命中 0 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-008: 向指定目录一次上传多个文件
- 关联：US-007；AC-007-01/02；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 在目录 D 上传 f1.txt、f2.md、bad.exe、f3.txt | 3 个 accepted；bad.exe 跳过 UNSUPPORTED_TYPE | 一致 | PASS |
| 2 | 浏览 D 与根 | D 下 3 个文件且 pending；根目录只有 D；worker 后全部 indexed | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-009: 更新文件：旧版可检索 → 成功切换；再次更新失败保留旧版 → 重试成功
- 关联：US-008；AC-008-01/02/03；环境：同上，嵌入器故障注入
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 更新规范.txt（K1→K2），索引前 | 202；update_state=updating；K1 仍命中、K2 未命中 | 一致 | PASS |
| 2 | worker 处理后 | indexed、update_state=null、content_updated_at 非空；K2 命中、K1 为 0；列表仅一条 | 一致 | PASS |
| 3 | 再次更新（K3）并令索引失败 | 状态 indexed + update_state=update_failed + 原因码；当前版（K2）仍可检索、K3 不可检索 | 一致 | PASS |
| 4 | 恢复后 `POST /retry` | 200；晋升后 K3 命中、K2 为 0；列表仍一条 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-010: 三个时间与状态：上传 / 更新 / 重命名移动 / 失败 / 重建
- 关联：US-009；AC-009-01~04；环境：受控时钟
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 上传 T1，索引成功 T2 | uploaded_at=T1；indexed_at=T2≥T1；content_updated_at=null | 一致 | PASS |
| 2 | 更新并处理 | 上传时间不变；最近更新 = 索引成功 = 替换时刻（OBS-1） | 一致 | PASS |
| 3 | 重命名 + 移动 | 三个时间不变 | 一致 | PASS |
| 4 | 失败文件 | status=failed、有原因码、indexed_at=null | 一致 | PASS |
| 5 | 重建并激活（T5） | indexed_at=T5≠T2；uploaded_at、content_updated_at 不变；状态 indexed | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-011: 所有上传途径均可检索，失败文件不可检索
- 关联：US-010；AC-010-01/03；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 文件夹上传 / 目录内上传 / 旧入口上传 / 更新后的新内容 | 各自检索：未降级且有命中；引用路径 `X/Y/folder.txt`、`legacy.txt`；status=indexed 且 chunk_count>0 | 一致 | PASS |
| 2 | 嵌入器故障下再传 1 个文件 | 状态 failed + 原因码；检索无命中 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-012: 同名冲突：对话框三选项 / 取消 / 大小写变体
- 关联：US-011；AC-011-01/02/04/05；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | dry-run 上传 a.txt（D 已有） | 200，列出冲突；选择前资料库不变；未决提交 409；原文件内容 / 状态 / 向量不变 | 一致 | PASS |
| 2 | 两次选“两者保留” | `a (2).txt`、`a (3).txt`；原 a.txt 不变 | 一致 | PASS |
| 3 | 选“跳过” | skipped USER_SKIPPED，条目数不变 | 一致 | PASS |
| 4 | 选“覆盖” | action=update，处理后仍只有一个 a.txt；新标记命中、旧标记为 0 | 一致 | PASS |
| 5 | 上传 a2.txt（库中为 A2.txt） | 同样冲突；保留 → `a2 (2).txt`，A2.txt 不变 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-013: 文件夹冲突合并 + 更新重名冲突
- 关联：US-011 / US-008；AC-011-03、AC-008-07；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 上传 A（A/x.txt、A/new.txt），目标已有 A；文件夹选覆盖 | 409，仅剩 `A/x.txt` 冲突需单独确认 | 一致 | PASS |
| 2 | x.txt 也选覆盖并上传 | 合并为同一个 A（同 folder_id）；x.txt 按更新，旧 x 被替换，other.txt 不变 | 一致 | PASS |
| 3 | 用 规范V2.MD 更新 规范.txt（库中有 规范v2.md） | 409 + 冲突条目；双方不变 | 一致 | PASS |
| 4 | 选 rename / 以 Y 为目标覆盖 | `规范V2 (2).MD`；覆盖时 X 不变、条目数不变 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-014: 移动文件与文件夹（Should，随旅程覆盖）
- 关联：US-013；AC-013-01/02/04、US-014；环境：同上
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | x.txt 从 A 移到 B | A 空、B 有；命中集合不变；路径 `B/x.txt` | 一致 | PASS |
| 2 | 文件夹 B 整体移到 C | 路径 `C/B/x.txt` | 一致 | PASS |
| 3 | 把 C 移到其子孙 B | 400 move_into_self，结构不变 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-015: 上限整体拒绝，不产生半成品
- 关联：US-015；AC-015-01/02/03/04；环境：同上，总大小上限配置为 1MB
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 1001 个文件 | 400 limit_files {limit:1000, actual:1001}；资料库为空 | 一致 | PASS |
| 2 | 目标第 8 层上传 3 层嵌套 / 第 7 层上传同一文件夹 | 前者 400 depth_exceeded（actual 11）且无任何新目录；后者 201 | 一致 | PASS |
| 3 | 总大小 L+1 / 恰为 L | 前者 400 limit_total_bytes {limit, actual}，无任何产物；后者 201 | 一致 | PASS |
- 结论：PASS

### TC-E2E-R25-016: 老库升级后既有平铺文件归入根目录且仍可检索
- 关联：US-017；AC-017-01/02；环境：真实 SQLite 临时库 + 真实账户令牌；老库 = 去掉新列 / 新表 / 新索引的 001 形态
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 上线前 5 个文件（3 个 indexed、1 failed、1 pending，含仅大小写不同的历史重名） | — | 已构造并还原为老库形态 | PASS |
| 2 | `ensure_schema` 升级并重复一次（重启） | 不报错，结果不变 | 一致 | PASS |
| 3 | 浏览根目录 | 5 个文件全在根，3 个 indexed；名称 / 大小 / 上传时间与升级前一致；无文件夹 | 一致 | PASS |
| 4 | 检索 / 移动 / 改名 / 更新 / 删除 | 独有内容可检索，路径 `手册.txt`→`整理后/手册.txt`；改名更新删除与新文件一致；历史重名显示名不变 | 一致 | PASS |
- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-R25-001 | MAJOR | 重建 succeeded 未激活窗口内更新文件，激活后新旧内容均检索不到（0.1.0 登记） | TC-INT-R25-055（已翻转为正向断言，内存 / SQLite）、056~059 | `src/ib/rebuild/__init__.py`（`REDIRECT_REBUILD_STATES`） | **FIXED-VERIFIED** |
| DEF-R25-002 | MINOR | 前端限额提示文案与 AC-015-01/02/04 字面不一致（0.1.0 登记） | TC-FE-46 | `src/frontend/src/stores/uploadBatch.ts`（`describeLimit`） | **FIXED-VERIFIED** |

本轮复测未发现新的产品缺陷。

### 观察项（非缺陷，供 PM / 用户知悉）

- **OBS-1（规格口径）**：`content_updated_at`（"最近更新时间"）在"内容被替换"的晋升事务中写入（ADR-006、REQ-FUNC-009"最近一次内容被替换的时间"），因此与 `indexed_at` 同刻；AC-008-01 / AC-009-02 字面"最近更新时间为本次更新时间 T3、索引成功于 T4"可被读作 T3=提交更新的时刻。实现与已批准设计一致，测试按设计断言（`content_updated_at ≥ 提交时刻` 且 `== indexed_at`，TC-UNIT-R25-070/076，TC-E2E-R25-010）；索引排队较久时用户会看到"最近更新时间"晚于其点击更新的时刻。如需改为提交时刻需回 GROUP_B 变更 ADR-006。
- **OBS-2（口径差异）**：AC-013-04 写"目标属于其他项目 → 提示'不支持跨项目移动'"，实现按 CL-010 / A-10 对他项目资源 id 一律 404（与不存在不可区分，TC-UNIT-R25-021b、TC-INT-R25-041 验证拒绝且结构不变）；提示文案不同，安全语义更强。
- **OBS-3（测试边界）**：AC-006-04 的"worker 安全退出"用内部受控信号 `_DeletedConcurrently` 断言（`process_pending` 内部捕获处理），未起真实 worker 进程。
- 浏览器内真实渲染 / 交互不可测（见 test_plan"不可测项"），仅有源码结构断言。
