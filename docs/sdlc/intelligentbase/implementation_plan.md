<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-24T23:10:48+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
    <file>docs/sdlc/intelligentbase/tech_stack.md</file>
    <file>docs/sdlc/intelligentbase/phase_status.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，重试 intelligentbase-GROUP_C-002）

## 实现概览

- 模块数：MOD-001 ~ MOD-015 全部实现（15/15）；按 module_design 的编号即拓扑序（依赖边均从大号指向小号）依次落地。
- 文件数：修改 20 个现有文件（含 3 个遗留改动文件 `core/__init__.py`、`core/types.py`、`ledger/schema.py`；`git status` 另显示的 2 个 `agent-memory/*/MEMORY.md` 是其他 agent 在本次调用前的改动，与本次无关）；新建 12 个文件：后端 6（`ib/core/library.py`〔遗留〕、`ib/ledger/tree.py`、`ib/ledger/upload_batches.py`、`ib/library/__init__.py`、`ib/library/uploads.py`、`ibweb/library_views.py`）、迁移 1、前端 5（`views/library/` 4 个 + `stores/uploadBatch.ts`）。另有本角色记忆文件追加 3 条待验证条目。
- 约束遵守：未用 Django ORM / contrib.auth；未新增依赖；未新增 systemd 单元、未改 nginx；`ib.*` 未 import `ib_embed` / `ibweb`；项目维度一律取台账 / 注册表（新增对象均不读 `cfg.projects`）；未 commit、未 push；未新建或修改任何测试文件。
- 上游条件 GR-B-001（A-01）：总大小默认 1024MB 仅出现在 `GlobalConfig.upload_batch_max_total_mb` 一处，作为可配置默认值（`IB_UPLOAD_BATCH_MAX_TOTAL_MB`，范围 1~102400），代码中无其他硬编码；部署阶段再确认。
- 需求 4.0.0 的用户答复 CL-010 已落实：按资源 id（folder_id / doc_id / batch_id）访问非本项目资源统一 `NotFoundError` → 404；`assert_kb_in_project` 归属断言失败仍 403；文件重命名禁止改扩展名（`ext_change_not_allowed`）；更新与同目录 Y 同名时选“覆盖”= 用新文件更新 Y（X 不变）、“两者保留”= X 更新并自动改名。

### 遗留改动处理（上一次调用中断留下的 +55/-1 与 library.py）

| 遗留文件 | 审阅结论 | 处理 |
|---|---|---|
| `src/ib/core/library.py`（新，178 行） | 与 IFC-014 一致：常量、`validate_entry_name`（另拒控制字符）、`name_key_of`、`next_free_name`、值类型、`LibraryConflictError` / `LibraryValidationError` | 保留；仅在 `LibraryConflictError` 增加可选 `initiators`（发起方条目，移动冲突弹窗用，`NameClash` 元组，与 `clashes` 按下标对应） |
| `src/ib/core/__init__.py` | 导出正确 | 保留不动 |
| `src/ib/core/types.py` | `DocumentRecord` 尾部 6 字段 + `RetrievedChunk` / `RelatedImageItem` / `CitationItem` 的 `doc_path` 均符合 IFC-014 / MOD-005 | 保留不动 |
| `src/ib/ledger/schema.py`（仅 `EXPECTED_COLUMNS` 追加 6 列） | 方向正确但半成品：缺 DDL、补列、回填、`ensure_schema` 接线 | 在其上继续补全 MOD-001 其余部分 |

未使用 `git checkout` / `reset` 丢弃任何文件。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-001 | `src/ib/ledger/schema.py` | 修改 | 无 | M | `FOLDER_TREE_ADDED_COLUMNS` / `_DDL_` / `_BACKFILL_` / `_UNIQUE_INDEX_STATEMENTS`、`FOLDER_TREE_EXPECTED_COLUMNS`、`folder_tree_ddl_script()`、`_ensure_document_tree_columns`、`backfill_name_keys`、`missing_folder_tree_columns`；`ensure_schema` 按“补列 → 新表/索引 → 标量回填 → name_key 回填 → 唯一索引”接线；`DDL_STATEMENTS`（001）未动 | DONE |
| 2 | MOD-001 | `src/deploy/migrations/007_folder_tree.sql` | 新建 | 1 | L | 由 `folder_tree_ddl_script()` 原样摘录；头注释含单源声明、应用方式、回滚说明（DROP 类标 `MANUAL_ROLLBACK_REQUIRED`）、“Python name_key 回填只在 ensure_schema 中”；001~006 未动 | DONE |
| 3 | MOD-001 | `src/ib/core/library.py`、`core/types.py`、`core/__init__.py` | 遗留+修改 | 无 | L | 见上表 | DONE |
| 4 | MOD-002 | `src/ib/ledger/tree.py` | 新建 | 1-3 | H | `EntryTreeStore` Protocol + `SqliteEntryTree` / `MemoryEntryTree`；业务逻辑只写一份（`_TreeLogic`），两后端只实现薄原语，语义一致由构造保证；变更均在 `_write()`（`BEGIN IMMEDIATE`）内“先检查后写”，`IntegrityError` → `LibraryConflictError`；内存后端异常时整体回滚快照 | DONE |
| 5 | MOD-002 | `src/ib/ledger/sqlite_repo.py` | 修改 | 1 | M | `_DOC_COLUMNS` / `_row_to_document` 追加 6 列；`create_document` 写 `uploaded_at` / `name_key` 并在同事务检查根目录同名（409）；`mark_indexed` 写 `indexed_at`；`list_documents(include_revisions=True)`；`find_name_clashes_sql`；启动期缺列检查含新表 | DONE |
| 6 | MOD-002 | `src/ib/ledger/__init__.py` | 修改 | 1 | M | 内存台账对齐上述语义（含 `_folders` / `_purge` 存储）；惰性导出 `SqliteEntryTree` 等 | DONE |
| 7 | MOD-002 | `src/ib/core/ports.py` | 修改 | 5 | L | `LedgerRepository.list_documents` 增加可选 `include_revisions=True`（见偏差 D-03） | DONE |
| 8 | MOD-003 | `src/ib/ledger/upload_batches.py` | 新建 | 1 | M | `UploadBatchStore` + SQLite / 内存实现；终态幂等；创建时顺带清理过期批次 | DONE |
| 9 | MOD-004 | `src/ib/lifecycle/__init__.py` | 修改 | 4-6 | H | `classify_upload`（`validate_upload` 改为基于它，行为与消息不变）；`submit_library_document` / `submit_revision` / `discard_revision` / `retry_revision` / `promote_ready_revisions` / `drain_purge_queue`；`_process_one` 第 9 步对修订行改走 `promote_revision`（`NotFoundError` → 丢弃修订行并安全跳过）；`delete_document` 先级联删修订行；构造参数 `tree` / `active_version_provider` / `library_max_depth` 均有缺省 | DONE |
| 10 | MOD-005 | `src/ib/retrieval/__init__.py` | 修改 | 3 | M | 可选 `entry_resolver`；候选 doc_id 去重后一次 `resolve_live`，不存活命中丢弃，名称/路径取台账；解析故障 → `LEDGER_UNAVAILABLE`（fail-closed）；工具文本用 `doc_path or doc_name` | DONE |
| 11 | MOD-005 | `src/ib/streaming/__init__.py` | 修改 | 3 | L | `related_images_json` / `completion_payload_json` 追加 `"doc_path"` 键，既有键不变 | DONE |
| 12 | MOD-006 | `src/ib/library/__init__.py` | 新建 | 4,9 | M | `LibraryService`：`browse` / `folder_detail` / `create_folder` / `rename_folder` / `rename_file` / `move` / `delete_folder_step`；另 `file_view`（改名/更新响应复用同一口径） | DONE |
| 13 | MOD-007 | `src/ib/library/uploads.py` | 新建 | 4,8,9 | H | `UploadBatchService.plan` / `accept_item` / `summary`；条数 → 总大小 → 深度 → 分类 → 冲突；目录延迟创建；幂等；`DependencyUnavailableError` 记 failed 后上抛 | DONE |
| 14 | MOD-008 | `src/ib/rebuild/__init__.py` | 修改 | 5,9 | L | `revision_promoter` 注入；`activate_version` 的 failed 计数排除修订行、切换后 best-effort 补晋升；`_count(include_revisions)` | DONE |
| 15 | MOD-009 | `src/ib/config/__init__.py` | 修改 | 无 | L | 四个新键（登记 `IB_RUNTIME_ENV_KEYS`、`GlobalConfig` 字段、范围校验）；`max_upload_mb > 60` 记 WARNING | DONE |
| 16 | MOD-010 | `src/ibweb/composition.py` | 修改 | 4-15 | M | 装配 `tree` / `upload_batches` / `library` / `uploads`（`Deps` 新增 4 个带默认值字段）；`DocumentLifecycle` / `RetrievalService(entry_resolver=tree)` / `RebuildService(revision_promoter)` 注入；`related_images` 带 `doc_path`、名称取命中回填值 | DONE |
| 17 | MOD-011 | `src/ibweb/worker.py` | 修改 | 9,16 | L | `run_once` 追加补晋升 / 清理队列排空 / 过期批次清理（均 try/except + log_event）；项目集合 = 注册表活动项目 ∪ `deps.projects` | DONE |
| 18 | MOD-012 | `src/ibweb/library_views.py` | 新建 | 9,12,13,16 | H | IFC-001~006、008~012 端点；ID 格式校验；错误体附 `conflicts` / `details` | DONE |
| 19 | MOD-012 | `src/ibweb/urls.py`、`views.py`、`serializers.py` | 修改 | 18 | M | 新路由（字面量先于参数）；`file_detail_endpoint` 增 `PATCH` 委托与“修订行失败时重试修订行”；`_list_files(include_revisions=False)`；`LibraryFileSerializer` / `LibraryFolderSerializer` | DONE |
| 20 | MOD-013 | `src/frontend/src/api/client.ts` | 修改 | 18-19 | M | IFC-025 全部 12 个方法与类型；`ApiClientError.conflicts`；`RelatedImageItem.doc_path?` | DONE |
| 21 | MOD-014 | `src/frontend/src/views/UploadPage.vue` | 修改 | 20 | M | 缩成页面骨架（标题 + 项目域提示 + `LibraryBrowser`）；旧“扁平表 + 单文件上传”区块已退役（无残留，见下） | DONE |
| 22 | MOD-014 | `src/frontend/src/views/library/{LibraryBrowser,UploadBatchPanel,ConflictDialog,FolderDeleteDialog}.vue`、`src/stores/uploadBatch.ts` | 新建 | 20 | H | 云盘式浏览 / 面包屑 / 新建 / 改名 / 移动 / 更新 / 删除；文件夹上传（`webkitdirectory`，不支持则隐藏）、并发 2、进度单调不减、汇总三数；冲突三选项；分步删除 | DONE |
| 23 | MOD-014 | `src/frontend/src/views/ChatPage.vue` | 修改 | 20 | L | `related_images` 读取 `doc_path`，标题 / `aria-label` 优先显示 | DONE |
| 24 | MOD-015 | `src/scripts/selfcheck.py` | 修改 | 1-19 | M | 新增 `folder_tree_migration_007`（007 单源比对 + 老库补列/回填 + 幂等 + 唯一约束）与 `folder_tree_integrity`（目录完整性对账，含人为损坏的反例）；同步 `retrieval_happy_path`（补存活台账行并成对断言）与 `related_images_events`（键集含 `doc_path`） | DONE |

MOD-015 的测试文件（`tests/**`）不由本角色新建，交 test-engineer（见“需同步的现有测试”）。

### 退役 UI 的僵尸检查

旧 `UploadPage.vue` 的“状态筛选下拉 + 扁平表格 + 单文件上传表单 + 2s 轮询”整体被 `LibraryBrowser` 取代（轮询逻辑迁入并仍只在有处理中条目时运行）。`grep -rn "statusFilter\|picked\b\|humanSize" src/frontend/src/views/UploadPage.vue` 无结果；`ApiClient.listFiles / uploadFile` 作为兼容端点的客户端方法保留（后端 `/api/files` 兼容端点仍在），但已无页面调用。资料管理仍是路由 `files`、导航顶级项，可从导航到达（`router/index.ts` 未改）。

## 迁移

- 文件：`src/deploy/migrations/007_folder_tree.sql`（新）；与 `ib.ledger.schema.folder_tree_ddl_script()` 逐字一致（去空白后包含，selfcheck `folder_tree_migration_007` 以与 CI 003 检查同口径比对）。001~006 一字未动。
- 内容摘要：4 张新表（`folders`、`upload_batches`、`upload_batch_items`、`doc_purge_queue`）、非唯一索引、`documents.uploaded_at` / `indexed_at` 标量回填、3 个唯一索引（`uq_folders_name`、`uq_documents_name`、`uq_documents_revision`）。`documents` 的 6 个新列由 `ensure_schema` 经 `PRAGMA table_info` 探测后逐列 `ALTER TABLE`（SQLite 无 `ADD COLUMN IF NOT EXISTS`），容忍并发补列的 `duplicate column name`。
- 幂等：全部 `IF NOT EXISTS` / 条件 UPDATE；已在老库形态（001 DDL + 含大小写重名历史数据）上 `ensure_schema` 两遍 + 007 快照重放两遍验证通过。
- 回滚：可逆为“代码回退即可运行”（旧代码忽略新列；回退前须先清掉在途修订行）；表 / 列 / 索引回滚为 DROP 类，已在迁移头注释标 `MANUAL_ROLLBACK_REQUIRED`，且回滚前须备份台账文件。
- 注意：007 快照不含 `ALTER TABLE ADD COLUMN` 与 Python 的 `name_key` 回填；部署路径是 `ib-web` 的 ExecStartPre `--ensure-schema`（自动），手工 `sqlite3 < 007` 仅在新库或 `ensure_schema` 已跑过时等价（头注释已写明）。
- 数据风险（沿用设计）：`indexed_at` 回填为近似值；历史重名行仅 `name_key` 追加 `U+001F + doc_id`，显示名不变。
- 与 CI：`.github/workflows/ci.yml` 的 “Schema / migration check” 内联脚本只检查 003，未改动（CI 属 devops 写权限）；本次未动 CI。若 devops 决定把 007 纳入，可复用 selfcheck 中的比对口径。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| D-01 `SqliteUploadBatchStore(ledger)` 构造参数为台账对象，而非“台账路径 + 线程局部连接” | MOD-003 | 复用 `SqliteLedgerRepository` 已有的线程局部连接与 `_write()`，少一套连接管理；表与迁移不变 | 无外部可见影响；测试需用台账对象构造 |
| D-02 `EntryTreeStore` / `LibraryConflictError` 增量：`bump_purge`、`list_subtree_folders`、`LibraryConflictError.initiators` | IFC-015 / IFC-014 | `drain_purge_queue` 需要“失败 attempts+1”而 Protocol 无对应方法；分步删除需要列出子树目录；移动冲突弹窗需要发起方名称 | 纯增量，不改既有方法签名；test-engineer 的端口一致性测试需覆盖这两个方法 |
| D-03 `ports.py::LedgerRepository.list_documents` 增加可选 `include_revisions=True` | 端口 IFC-IB-122 | 设计只在 sqlite / 内存实现里加参数，但 selfcheck `port_conformance` 按参数名集合比对端口与实现，不同步端口会失败 | 默认值保持基线行为；旧调用方不受影响 |
| D-04 配置越界 / 非整数抛 `ConfigError`（带键名）而非设计所写 `StartupError` | IFC-023 | 既有 `ib.config` 全部校验沿用 `ConfigError`；启动期 `build_deps` 同样 fail-fast | 进程仍起不来；异常类型不同于设计字面 |
| D-05 `submit_revision` 对被替换的旧修订行改走“清理队列 + 立即尽力排空”，而非同步逐个 `delete_document` | IFC-017 | 旧修订行已在 `create_revision` 事务内移出台账，只能经清理队列物理清理（可重试、不外抛） | 向量 / blob 清理可能延后到 worker 下一轮；存活过滤保证期间不可检索 |
| D-06 移动时“覆盖”的文件夹语义 = 合并（同名文件覆盖、同名子文件夹递归合并、跨类同名自动改名）；文件与文件夹互相“覆盖”→ 400 `bad_request` | IFC-006 | 设计未写明移动场景下文件夹“覆盖”的细则（上传场景 = 合并），采用与上传一致的语义 | 见开放问题 [ASSUMPTION] |

## 开放问题

- [ASSUMPTION] 移动冲突中的 `overwrite`：文件覆盖文件 = 被覆盖文件及其修订行移出台账并入清理队列；文件夹覆盖文件夹 = 合并（D-06）；文件夹与文件互相覆盖不支持（400）。需求只明确了上传 / 更新场景。
- [ASSUMPTION] 上传计划中，文件名与同目录**文件夹**同名、或目录段与同目录**文件**同名时，只接受“跳过 / 两者保留（自动改名）”，选“覆盖”按改名处理。
- [ASSUMPTION] 清单内部重复（同一目录下两条目大小写变体同名）自动按 `名称 (2)` 改名，不弹冲突。
- [ASSUMPTION] `submit_revision` 判定“内容未变化”仅比较 sha256 且存活行为 `indexed`；新文件名不同但内容相同时仍视为未变化（AC-008-06 的“完全相同”）。
- [ASSUMPTION] 单次上传总大小默认 1024MB（A-01 `[ESTIMATE]`，部署阶段确认）；目标机 SQLite 版本未实测（设计同），部署前以 `python3 -c "import sqlite3;print(sqlite3.sqlite_version)"` 核实（递归 CTE ≥3.8.3、部分索引 ≥3.8.0）。
- 新环境键 `IB_UPLOAD_BATCH_MAX_FILES` / `IB_UPLOAD_BATCH_MAX_TOTAL_MB` / `IB_LIBRARY_MAX_DEPTH` / `IB_UPLOAD_BATCH_TTL_HOURS` 未写入 `src/deploy/*.env.example`（部署配置属 devops；默认值无需任何 env 改动）。
- 无 `TODO(IFC-NNN)` stub；无 `[DEVIATION]` 之外的未实现项。

## 需同步的现有测试（交 test-engineer；本角色未改任何测试文件）

| 测试 | 位置 | 原因 | 建议改法 |
|---|---|---|---|
| 前端冒烟用例 32 | `src/frontend/tests/frontend.smoke.test.js:658-673` | 断言 `UploadPage.vue` 含 `uploadFile(picked.value)`；UploadPage 已缩为骨架，单文件上传由 `UploadBatchPanel` 的批次流程取代。**实测 `npm test` 39 通过 / 1 失败（仅此一条）** | 改为：UploadPage 仍含“项目域”文案且无 `kbId` / `kb_id` 赋值；`views/library/*` 经 `planUpload` / `uploadBatchItem` 上传；`client.ts` 的 `uploadFile(file: File)` 与 `body.append('file', file)`、无 kb 字段断言保持不变 |
| 精确键集断言 | `tests/unit/test_core_config_chunk_parse_stream.py:300`、`tests/integration/test_orchestration_related_images.py:123` | `related_images` 载荷按设计追加 `doc_path` 键 | 键集加入 `"doc_path"`；并补“值取自台账当前路径”的成对用例 |
| 引用字典全等 | `tests/unit/test_stream_session_lifecycle_unit_r12.py:~86` | `completion_payload_json` 的每条 citation 追加 `"doc_path"` | 字典加 `"doc_path": ""` |
| 旧入口同名 | 所有对同一项目重复 `POST /api/files` 同名文件 / 重复 `create_document` 同名的用例（本次静态检索未发现，需实跑确认） | 旧入口按设计遇同名返回 409 `name_conflict` | 如有命中，改用不同文件名或断言 409 |
| 直接 upsert 向量点的夹具 | 已改 selfcheck；`tests/` 内未发现同类夹具 | 带 `entry_resolver` 的检索只返回台账存活的命中 | 如新增此类夹具，须补存活台账行 |

新增测试落点（MOD-015，交 test-engineer）按 module_design 列出的 15 个文件基名；开发前以 `ls tests/*/` 复核基名全局唯一。

## 缺陷修复轮（1.1.0，invocation intelligentbase-GROUP_C-003，来源 GR-D-001）

| DEF | 文件 | 改动 | 状态 |
|---|---|---|---|
| DEF-R25-001 | `src/ib/rebuild/__init__.py` | 新增 `REDIRECT_REBUILD_STATES = IN_FLIGHT_REBUILD_STATES + ("succeeded",)`；`RebuildAwareProjectProvider.target_version` 与 `RebuildService._target_of` 改用它（写路径重定向与 `_base_project` 还原同口径）。`IN_FLIGHT_REBUILD_STATES` 不变（`step_rebuild` done 判据、worker 推进仍只认 planned/running） | DONE |
| DEF-R25-002 | `src/frontend/src/stores/uploadBatch.ts` | `describeLimit` 三条提示按 AC-015-01/-02/-04 字面：`单次最多上传 {limit} 个文件（当前 {actual}）`、`目录层级最多 {limit} 层`、`单次上传总大小超过上限（当前 {actual MB}，上限 {limit MB}）` | DONE |

**根因（DEF-R25-001）**：重建任务到 `succeeded` 后，`target_version` 返回 None，写路径回落到台账 active 版本 v1；修订行以 v1 索引，`tree.promote_revision` 的 `collection_version == active_version` 成立而被立即晋升，旧文档 v1/v2 向量被清理，激活 v2 后新旧内容皆命中 0。**修法（ADR-007 框架内）**：“succeeded 但未激活”按重建在途处理写路径——修订行落 v2，`collection_version != active_version` → 推迟晋升，激活后补晋升。`tree.py` 无需改动。激活 / 回滚会把任务置 `activated` / `rolled_back`，重定向随之自动失效。

**窗口内普通新上传评估**：会丢失，但**不是本增量引入**——基线 HEAD 的 `IN_FLIGHT_REBUILD_STATES` 同为 planned/running，窗口内新上传同样落旧版本 v1，激活 v2 后命中 0（基线遗留缺陷，REQ-FUNC-IB-24 重建链路）。本次修复使用同一重定向判定，因此该场景**被同一处改动一并覆盖**，未扩大改动范围（无额外文件 / 逻辑）。验证见 code_review_report“缺陷修复”。残余注意：窗口内新上传在激活前是 pending，会触发 `activate_version` 的“未完成索引”守卫，需 worker 处理完再激活（既有且合理的行为）。

**TC-INT-R25-050（任务在飞）**：重定向集合是原集合的超集，在飞窗口行为不变，050 仍通过。

[ASSUMPTION] `depth_exceeded` 的 `details.limit` 即最大层数（沿用原文案已有用法）；“目录层级最多 N 层”中 N 取该值。

## PM 复跑命令清单

本机 python3 无 pip / pytest / django，以下后端命令**本次均未能运行（BLOCKED）**，需 PM 在有依赖的环境复跑：

```bash
# 仓库根；环境变量见画像 P4（tests/conftest.py 会 setdefault）
python -m compileall -q src                       # 本次已运行：通过
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest tests/e2e -q
python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q     # 基线 434 passed / 2 skipped；预期因上表“需同步的现有测试”出现约 3 处失败（精确键集 2 处 + 引用字典全等 1 处；前端用例 32 在 npm test 中）
python src/scripts/selfcheck.py                   # 基线 52/52；本次新增 2 个用例，预期 54/54
python -m pytest tests/agents -q
# CI “Schema / migration check”内联脚本（ci.yml:77-92，只检查 003）应保持通过
(cd src/frontend && npm ci && npm run build && npm test)           # 本次已运行：build 通过；npm test 39/40（用例 32 待同步）
```

已在无 Django 环境下用纯 Python 脚本做过冒烟（脚本在 scratchpad，未入库，不算测试）：目录树两个后端（内存 / SQLite）、修订晋升与重建在途“就绪待晋升”、批次计划与逐文件上传、检索存活过滤的成对判据、`library_views` 的 12 个端点函数（stub 的 `rest_framework` / `django.http` + 假 request）。详见 code_review_report“自验证结果”。
