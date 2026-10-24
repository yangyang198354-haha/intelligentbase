<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-24T23:10:48+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，intelligentbase-GROUP_C-002）

## 摘要

- 改动范围（`git diff --shortstat`）：22 files changed, 1458 insertions(+), 404 deletions(-)。其中 2 个 `.claude/agent-memory/*/MEMORY.md` 是其他 agent 在本次调用前的改动，与本次无关；本次实际修改 20 个现有文件，另有 12 个新建文件（约 4750 行，含 4 张表的迁移与 5 个前端文件）。`git status` 中不含无关文件。
- 五维平均分：正确性 8.47 / 安全 8.87 / 性能 8.53 / 可维护性 8.00 / 可测试性 8.00，总平均 **8.37**（15 个 MOD 各自评分见下；无低于 6 的维度）。
- 问题统计：**CRITICAL 0（已修复 0） / MAJOR 3 / MINOR 6**（合计 9 = 0 + 3 + 6）。MAJOR 遗留 3 条（未超过 3 条），仍逐条写明建议处理时机。

## 文件 → MOD/IFC 映射

| 文件 | MOD | IFC |
|---|---|---|
| `src/ib/ledger/schema.py`、`src/deploy/migrations/007_folder_tree.sql`、`src/ib/core/library.py`、`core/types.py`、`core/__init__.py` | MOD-001 | IFC-014 |
| `src/ib/ledger/tree.py`、`ledger/sqlite_repo.py`、`ledger/__init__.py`、`core/ports.py` | MOD-002 | IFC-015 |
| `src/ib/ledger/upload_batches.py` | MOD-003 | IFC-016 |
| `src/ib/lifecycle/__init__.py` | MOD-004 | IFC-017 |
| `src/ib/retrieval/__init__.py`、`streaming/__init__.py`、`core/types.py` | MOD-005 | IFC-018 |
| `src/ib/library/__init__.py` | MOD-006 | IFC-019 |
| `src/ib/library/uploads.py` | MOD-007 | IFC-020 |
| `src/ib/rebuild/__init__.py` | MOD-008 | IFC-021 |
| `src/ib/config/__init__.py` | MOD-009 | IFC-023 |
| `src/ibweb/composition.py` | MOD-010 | IFC-024 |
| `src/ibweb/worker.py` | MOD-011 | — |
| `src/ibweb/library_views.py`、`urls.py`、`views.py`、`serializers.py` | MOD-012 | IFC-001~013 |
| `src/frontend/src/api/client.ts` | MOD-013 | IFC-025 |
| `src/frontend/src/views/UploadPage.vue`、`views/library/*.vue`、`stores/uploadBatch.ts`、`ChatPage.vue` | MOD-014 | — |
| `src/scripts/selfcheck.py` | MOD-015 | — |

## 自验证结果

环境事实：本机 python3 无 pip / pytest / django / langgraph（PM 实测并经本次复核）；未安装任何依赖。

| 项 | 命令 | 输出尾部 / 结论 |
|---|---|---|
| 编译检查 | `python3 -m compileall -q src` | 无输出，退出 0（通过） |
| 前端构建 | `(cd src/frontend && npm run build)` | `vue-tsc --noEmit` 通过；`✓ 1661 modules transformed` … `✓ built in 25.35s`（通过） |
| 前端冒烟 | `(cd src/frontend && npm test)` | `# tests 40 / # pass 39 / # fail 1`；唯一失败为 REV-18 用例 32（断言 UploadPage 含 `uploadFile(picked.value)`，已由设计取代，见 implementation_plan“需同步的现有测试”），其余 39 条通过 |
| 新增 selfcheck 用例（无 django 可单独运行） | `python3 -I -c "import selfcheck as s; s.folder_tree_migration_007(); s.folder_tree_integrity()"`（`src/scripts`） | `PASS folder_tree_migration_007` / `PASS folder_tree_integrity`（含 007 单源比对、老库补列回填、007 重放两遍、唯一约束、对账正反例） |
| 既有 selfcheck 子集（无 django 可运行的 43 个用例） | 同上，逐个调用 | 43 run，40 通过，3 失败且均为环境原因：`core_framework_free`（系统 site 的 `apport_python_hook` / `sitecustomize` / `zope` 被子进程计入，与改动无关）、`orchestration_events_order`（缺 langgraph）、`r14_project_context`（缺 django）。改动前曾有 2 个失败由本次改动引起并已修复：`retrieval_happy_path`（夹具向量点无存活台账行）与 `related_images_events`（精确键集），修复后重跑通过 |
| 内存 / SQLite 端到端冒烟（脚本在 scratchpad，未入库，不是测试） | `python3 -I smoke_e2e.py` | `memory OK` / `sqlite OK`：计划 → 批次 → 逐文件上传 → 入库 → 浏览 → 检索（路径取台账）→ 改名后路径随之变化 → 更新（旧版本在更新期仍可检索、成功后旧关键词 0 命中、`content_updated_at` 非空、`uploaded_at` 不变）→ 解析故障 `LEDGER_UNAVAILABLE` → 分步删除 → 删除后命中 0 且不降级 → 跨项目 404 |
| 修订晋升 / 重建在途（两后端） | scratchpad 脚本 | `ok` / `ok`：集合版本 ≠ active 时 `ready` 不晋升且旧版仍存活；激活后 `promote_ready` 晋升、旧 doc 入清理队列、`bump_purge` / `ack_purge`；孤儿修订行抛 `NotFoundError` |
| HTTP 视图函数冒烟（stub 的 `rest_framework` / `django.http` + 假 request） | scratchpad 脚本 | 新建重名 409 带 `conflicts`；非法 ID 400；不存在 404；限额 400 带 `details`；逐文件 PUT 幂等；改扩展名 400 `ext_change_not_allowed`；内容相同 200 `CONTENT_UNCHANGED`；更新 202；丢弃 200；移动到自身 400；跨项目 404；缺确认 400 `confirm_required`；分步删除 `done=true` |
| pytest（unit / integration / e2e / agents / 全量）、完整 `selfcheck.py`、CI 迁移内联脚本 | — | **BLOCKED / 未验证**：无 pytest、无 django。复跑命令见 implementation_plan“PM 复跑命令清单” |

未验证项及原因：Django 特有路径（`PUT` multipart 的 `MultiPartParser` 手动解析、`request.POST` 取 `on_conflict`、URLconf 反解、中间件交互）因缺 django 无法运行；浏览器内的真实交互（`webkitdirectory`、并发 2 的上传、对话框）未运行，仅通过 `vue-tsc` + `vite build` 与源码结构检查。

## 按模块评审

### MOD-001 台账结构、核心类型与迁移

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

遗留改动经审阅符合设计后沿用；`ensure_schema` 顺序为补列 → 新表/索引 → 标量回填 → `name_key` 回填 → 唯一索引，已在含大小写重名历史数据的 001 形态老库上验证两遍幂等，也在 `isolation_level` 默认（非自动提交）的连接上验证。CR：无。

### MOD-002 目录树与条目台账存储

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 7/10 | 8/10 |

业务逻辑一份、两后端薄原语，端口语义一致由构造保证；变更均在写事务内先检后写；project 条件显式下推，不存在 / 不属于本项目一律 `NotFoundError`。CR：CR-005（私有成员协作）。

### MOD-003 上传批次存储

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

CR：无（偏差 D-01 已登记）。

### MOD-004 文档生命周期扩展

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 7/10 | 8/10 |

`validate_upload` 行为与消息不变（基于 `classify_upload`）；`drain_purge_queue` / `promote_ready_revisions` 为后台动作不外抛，所用日志器与枚举均为模块级导入（无局部 import 被吞成降级的风险）。CR：CR-007。

### MOD-005 检索命中解析与引用路径

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

一次 `resolve_live` 批量解析；故障 fail-closed 为 `LEDGER_UNAVAILABLE`，并已用 selfcheck 成对断言（happy 路径：`degraded is False` 且名称 / 路径 = 台账当前值；全部不存活：`degraded is False` 且 `hits == []`；解析故障：`degraded is True`）。CR：无。

### MOD-006 目录管理服务

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

分步删除逐文件失败隔离、失败文件及其目录链保留、错误码只用稳定码不带异常文本。CR：CR-006（逐文件查修订）。

### MOD-007 批量上传编排服务

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 7/10 | 8/10 |

限额校验在落任何东西之前；实际字节数核对声明大小；目录延迟创建。CR：CR-009（多轮逐层冲突确认）。

### MOD-008 重建联动

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

仅 `activate_version` 的 failed 计数排除修订行；`step_rebuild` 口径不变；补晋升失败不影响已完成的切换。CR：无。

### MOD-009 配置项

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

总大小默认 1024MB 仅此一处（GR-B-001 条件满足）。CR：无（偏差 D-04）。

### MOD-010 组合根装配

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 8/10 |

新对象均不读 `cfg.projects`；`Deps` 新字段带默认值，旧构造点不受影响。CR：无。

### MOD-011 ib-worker 周期动作

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

三个动作均 try/except + log_event；项目集合以注册表为准、`deps.projects` 仅回退。`run_once` 本身依赖 `composition.get_deps()`，未在无 django 环境单独运行。CR：CR-007。

### MOD-012 HTTP 接口层

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8/10 | 8/10 | 8/10 | 6/10 |

写端点前置 `_require_manage`，浏览端点只要求已认证；ID 格式校验；跨项目按 id 访问 → 404（CL-010）；错误体附 `conflicts` / `details`。可测试性 6 分因 Django 特有路径无法在本机运行，已对应 CR-001。CR：CR-001、CR-002。

### MOD-013 前端 API 客户端

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 7/10 |

HTTP 唯一出口；无 axios / CDN；`ApiClientError.conflicts`。CR：无。

### MOD-014 前端资料管理界面

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 7/10 | 8/10 | 8/10 | 7/10 | 6/10 |

入口仍为路由 `files`；旧区块无残留；无 `v-html`、无 `localStorage`（批次 id 仅 `sessionStorage`）。可测试性 6 分因无组件级测试与浏览器内实跑，对应 CR-008。CR：CR-008、CR-009。

### MOD-015 自检与测试

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

新增 2 个 selfcheck 用例并同步 2 个受影响的既有用例；测试文件由 test-engineer 负责。CR：CR-004。

## CR 问题清单

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `src/ibweb/library_views.py:_multipart_file`、`file_revision_endpoint` | `PUT /api/uploads/{batch}/items/{idx}` 依赖 `MultiPartParser` 手动解析 multipart（Django 不为 PUT 填充 `request.FILES`），更新端点依赖 `request.POST`；本机无 django，仅用 stub 验证过其余逻辑，这两条 Django 特有路径未实跑。建议：test-engineer 用 Django 测试客户端 `client.put(..., content_type=MULTIPART_CONTENT)` 写集成用例（含 >2.5MB 临时文件分支）；时机：GROUP_D 单元/集成阶段 | OPEN |
| CR-002 | MAJOR | `src/ib/ledger/sqlite_repo.py:create_document`、`ledger/__init__.py:create_document`、`ibweb/views.py:_upload_file` | 按设计，旧入口 `POST /api/files` 与 `create_document` 对根目录同名返回 409 `name_conflict`（此前允许重名）。行为变更可能令未被静态检索发现的既有测试 / 调用方失败。建议：PM 复跑全量 pytest 与 selfcheck 时重点看；时机：GROUP_C 门控复跑 | OPEN |
| CR-003 | MAJOR | 全仓 pytest、完整 `selfcheck.py` | 因缺 pytest / django / langgraph，后端回归未能实跑（BLOCKED），门控所需的“零新增失败”暂无法证明；已用可运行子集与 scratchpad 冒烟替代并如实标注。建议：PM 在具备依赖的环境复跑 implementation_plan 的命令清单；时机：GROUP_C 门控 | OPEN |
| CR-004 | MINOR | `src/ib/ledger/sqlite_repo.py`（`_DOC_COLUMNS` 与 `_row_to_document` 两处）、`views/library/UploadBatchPanel.vue`（删除两个未用 ref） | 这三处小改动用了一次性 Python 脚本而非 Edit 工具，违反“改文件只用 Edit / Write”的审计要求；改动内容可由 `git diff` 完整复核。建议：后续一律用 Edit；已无需代码修改 | OPEN |
| CR-005 | MINOR | `src/ib/ledger/tree.py:SqliteEntryTree` | 直接使用 `SqliteLedgerRepository` 的私有 `_conn` / `_write`（包内协作，模块文档已注明）；若台账重构该私有接口会同时影响树存储。建议：后续在台账上提供公开的事务上下文 | OPEN |
| CR-006 | MINOR | `src/ib/library/__init__.py:_file_view` | 浏览每个文件调用一次 `get_revision_of`（页内至多 100 次索引查询，命中 `uq_documents_revision`）；未提供批量接口。NFUNC-006 的专项性能用例若不达标再优化 | OPEN |
| CR-007 | MINOR | `src/ib/lifecycle/__init__.py:promote_ready_revisions` | 每个项目补晋升结尾都会 `drain_purge_queue`，与 worker 随后的 `drain_purge_queue` 重复（幂等、无害，仅多一次列队查询） | OPEN |
| CR-008 | MINOR | `src/frontend/src/views/library/*.vue` | 仅通过 `vue-tsc` / `vite build` 与源码结构检查，未在浏览器中实跑（`webkitdirectory`、并发 2 上传、对话框流程）；前端冒烟测试也只是源码断言。建议 test-engineer 补冒烟断言，E2E 阶段手工走查 | OPEN |
| CR-009 | MINOR | `src/ib/library/uploads.py:_Planner`、`stores/uploadBatch.ts:plan` | 嵌套目录的多层同名冲突按层暴露：每轮 dry-run 只确认当前可见的最外层冲突，用户可能需要多次弹窗（行为正确、体验次优）。建议后续把已知的各层冲突一并返回 | OPEN |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

共 3 条（CR-001、CR-002、CR-003），未超过 3 条；处理时机见上表：CR-001 在 GROUP_D 集成阶段补测；CR-002 / CR-003 由 PM 在 GROUP_C 门控复跑时确认。

## 缺陷修复

缺陷修复轮（invocation intelligentbase-GROUP_C-003，defect_loops=1，1.1.0 / DRAFT；1.0.0 请 PM 登记为 SUPERSEDED）。详情亦见 implementation_plan.md“缺陷修复轮”小节。

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-R25-001（MAJOR） | `src/ib/rebuild/__init__.py`：新增 `REDIRECT_REBUILD_STATES`（= `IN_FLIGHT_REBUILD_STATES` + `succeeded`），`RebuildAwareProjectProvider.target_version` 与 `RebuildService._target_of` 改用它 | 写路径重定向只认 planned/running；任务 `succeeded`（已重建完成、未激活）后写路径回落旧 active 版本 v1，修订行的 collection_version == active_version 使 `tree.promote_revision` 立即晋升并清理旧文档 v1/v2 向量，激活 v2 后新旧内容均命中 0 | 窗口内写入继续落目标版本 v2，`tree.py:815` 判据 `collection_version != active_version` 自然走“ready 推迟晋升”，激活后由 `_revision_promoter` / worker 补晋升。`tree.py` 未改。`IN_FLIGHT_REBUILD_STATES` 保持不变，`step_rebuild` 的 done 判据与 worker 推进不受影响，TC-INT-R25-050 行为不变 |
| DEF-R25-002（MINOR） | `src/frontend/src/stores/uploadBatch.ts` `describeLimit` | 限额提示文案自拟，与 AC 字面不符 | 三条提示改为 AC-015-01/-02/-04 字面（数值取实际上限与实际值）；grep 旧文案无残留 |

### 代码评审（缺陷修复轮增量）

| 维度 | Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|---|
| 本轮改动 | 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

CR-010（MINOR，`rebuild/__init__.py:RebuildAwareProjectProvider` 类文档串仍写“pending/running”，未含 succeeded）：OPEN，仅文档串，不影响行为。无新增 CRITICAL / MAJOR。

### 自验证（缺陷修复轮）

环境变量：`PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`；解释器 `/root/.venvs/intelligentbase/bin/python`。

```
$ python -m compileall -q src            -> 无输出（通过）
$ python -m pytest tests -q
FAILED tests/integration/test_folder_rebuild_coexist_int_r25.py::test_TC_INT_R25_055_DEF_R25_001_update_after_rebuild_succeeded_before_activation_loses_file_from_search
  AssertionError: GUARD:DEF-R25-001 修订行被写入 v1 并立即晋升
1 failed, 595 passed in 119.14s (0:01:59)
$ python src/scripts/selfcheck.py
自检结果：53/54 通过   （仅 core_framework_free：sitecustomize 既有环境项）
$ cd src/frontend && npm run build && npm test
✓ built in 25.69s ... # tests 45 / # pass 45 / # fail 0
```

唯一失败为预期：冻结用例 TC-INT-R25-055 的守卫串断言“响亮失败”（修订行现在未被立即晋升），由 test-engineer 翻转。未修改任何测试文件，未修改 selfcheck。

修复后行为的额外核验（scratchpad 临时用例，不入库、不算测试）：(a) 与 055 同流程，断言修订行 `revision_of` 保留、`indexed_collection_version == "2"`，激活后新内容命中、旧内容命中 0、旧行已晋升移除——通过；(b) 窗口内普通新上传，激活后可检索——通过；(c) 把 `REDIRECT_REBUILD_STATES` 临时置回旧值重放 (b)，新上传命中 0（复现修复前行为）。

### 现有测试调整（缺陷修复轮）

无（按规则不改测试）。待 test-engineer 翻转 TC-INT-R25-055：激活后 `new_hits` 非空、`old_hits == []`、`view.searchable is True`，并将“修订行写入 v1 并立即晋升”前置断言改为“修订行 `revision_of == live.doc_id`、`indexed_collection_version == "2"`、存活行仍在”。建议另补“succeeded 窗口内普通新上传，激活后可检索”成对用例。

## 现有测试调整

本角色未修改任何测试文件。受影响、需 test-engineer 同步的现有测试清单（原因与建议改法见 implementation_plan“需同步的现有测试”）：

1. `src/frontend/tests/frontend.smoke.test.js` 用例 32：断言 `UploadPage.vue` 含 `uploadFile(picked.value)`，已被批次上传流程取代（实测 `npm test` 唯一失败项）。
2. `tests/unit/test_core_config_chunk_parse_stream.py:300`、`tests/integration/test_orchestration_related_images.py:123`：`related_images` 载荷精确键集需加入 `doc_path`。
3. `tests/unit/test_stream_session_lifecycle_unit_r12.py:~86`：citation 字典全等需加入 `"doc_path": ""`。
4. 对同一项目重复同名上传 / `create_document` 的用例（若有）：旧入口现返回 409。

同时已由本角色同步的是开发自检脚本 `src/scripts/selfcheck.py`（它属于产品代码目录，不是 tests/）：`retrieval_happy_path`（补存活台账行并增加成对判据）与 `related_images_events`（键集含 `doc_path`），原因同上。
