<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-24T18:01:47+08:00</timestamp>
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

# 资料管理：文件夹上传与云盘式目录管理 — 模块设计（INCREMENTAL）

> 基线：`docs/module_design.md`（legacy_baseline，只读）。本文 MOD/IFC 用新序列（`MOD-001…`、`IFC-001…`），基线为 `MOD-IB-NN` / `IFC-IB-NNN`，互不冲突。
> **编号即拓扑序**：每条依赖边都从较大 MOD 编号指向较小编号（无环证明见"依赖关系"）。
> 设计到接口签名为止：不含函数体。Python 类型注解 / TypeScript 类型 / HTTP 契约均为实现必须满足的契约。
> ADR 引用指 `architecture_design.md` 的新序列 ADR-001…012。

## 模块总览

模块 = 本次新增/修改的代码单元。"新建"/"修改现有"均注明路径。

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-001 | 台账结构、核心类型与迁移 | 修改 `src/ib/ledger/schema.py`；**新建** `src/deploy/migrations/007_folder_tree.sql`；**新建** `src/ib/core/library.py`；修改 `src/ib/core/types.py`、`src/ib/core/__init__.py` | 新表/新列 DDL、老库补列与回填、`name_key`/名称校验纯函数、目录相关类型与错误码 | REQ-FUNC-009/016/017、REQ-NFUNC-001/007 | 无 |
| MOD-002 | 目录树与条目台账存储 | **新建** `src/ib/ledger/tree.py`；修改 `src/ib/ledger/sqlite_repo.py`、`src/ib/ledger/__init__.py`（内存替身） | 目录/文件 CRUD、移动、同名约束、修订行晋升、存活解析、清理队列（SQLite + 内存两实现） | REQ-FUNC-003/004/005/006/008/009/011/012/013/015/016/017、REQ-NFUNC-001/002/004/007 | MOD-001 |
| MOD-003 | 上传批次存储 | **新建** `src/ib/ledger/upload_batches.py` | 批次与逐项状态的持久化、过期清理 | REQ-FUNC-002/015、REQ-NFUNC-007 | MOD-001 |
| MOD-004 | 文档生命周期扩展 | 修改 `src/ib/lifecycle/__init__.py` | 目录内落库、修订提交/丢弃/晋升、删除级联修订、清理队列排空、非抛出式上传分类 | REQ-FUNC-001/002/006/007/008/009/010、REQ-NFUNC-001/002/003/004/007 | MOD-001、MOD-002 |
| MOD-005 | 检索命中解析与引用路径 | 修改 `src/ib/retrieval/__init__.py`、`src/ib/streaming/__init__.py`、`src/ib/core/types.py`（与 MOD-001 同文件不同符号） | 检索期台账存活过滤 + 当前名称/目录路径；引用/关联图携带 `doc_path` | REQ-FUNC-005/012/013/014、REQ-NFUNC-001/002 | MOD-001 |
| MOD-006 | 目录管理服务 | **新建** `src/ib/library/__init__.py` | 浏览、建/改名/移动/分步删除文件夹，文件改名；业务编排与权限无关 | REQ-FUNC-003/004/005/006/012/013/015/016、REQ-NFUNC-001/006/007 | MOD-002、MOD-004 |
| MOD-007 | 批量上传编排服务 | **新建** `src/ib/library/uploads.py` | 清单校验（限额/分类/冲突）、批次创建、逐文件受理（新建或更新） | REQ-FUNC-001/002/007/008/011/015、REQ-NFUNC-007 | MOD-002、MOD-003、MOD-004 |
| MOD-008 | 重建联动 | 修改 `src/ib/rebuild/__init__.py` | 激活后补晋升钩子；失败计数排除修订行 | REQ-NFUNC-004、REQ-FUNC-009 | MOD-002、MOD-004 |
| MOD-009 | 配置项 | 修改 `src/ib/config/__init__.py` | 四个新配置键 + 传输约束告警 | REQ-FUNC-015 | 无 |
| MOD-010 | 组合根装配 | 修改 `src/ibweb/composition.py` | 装配新存储/服务/解析端口；`related_images` 带 `doc_path` | 全部后端需求（装配） | MOD-002/003/004/005/006/007/008/009 |
| MOD-011 | ib-worker 周期动作 | 修改 `src/ibweb/worker.py` | `run_once` 追加"补晋升"与"清理队列排空" | REQ-NFUNC-002/004、REQ-NFUNC-001 | MOD-004、MOD-010 |
| MOD-012 | HTTP 接口层 | **新建** `src/ibweb/library_views.py`；修改 `src/ibweb/urls.py`、`src/ibweb/views.py`、`src/ibweb/serializers.py` | 目录/移动/修订/批次/文件改名端点，参数校验、鉴权、错误映射 | 全部 REQ-FUNC（接口面）、REQ-NFUNC-005 | MOD-004、MOD-006、MOD-007、MOD-010 |
| MOD-013 | 前端 API 客户端 | 修改 `src/frontend/src/api/client.ts` | 新增类型与方法（HTTP 唯一出口） | 全部前端需求（接口面） | MOD-012（HTTP 契约） |
| MOD-014 | 前端资料管理界面 | 修改 `src/frontend/src/views/UploadPage.vue`、`src/frontend/src/views/ChatPage.vue`；**新建** `src/frontend/src/views/library/LibraryBrowser.vue`、`UploadBatchPanel.vue`、`ConflictDialog.vue`、`FolderDeleteDialog.vue`、`src/frontend/src/stores/uploadBatch.ts`；修改 `src/frontend/tests/frontend.smoke.test.js` | 云盘式浏览/面包屑/新建/改名/移动/删除、文件夹上传进度与汇总、冲突弹窗、更新、三时间显示、引用路径显示 | REQ-FUNC-001~015（界面面）、REQ-NFUNC-006 | MOD-013 |
| MOD-015 | 自检与测试 | 修改 `src/scripts/selfcheck.py`；**新建**下列测试文件（见各节"测试落点"） | 007 单源一致性、目录完整性对账、成对正/反例 | REQ-FUNC-017、REQ-NFUNC-001/004/007 | MOD-001~MOD-012 |

## 模块详情

### MOD-001 台账结构、核心类型与迁移

**职责**：定义 007 迁移涉及的全部 DDL（单源），提供老库幂等补列与回填，提供名称规则/`name_key`/改名顺延的纯函数，定义目录相关类型。

**文件**：
- 修改 `src/ib/ledger/schema.py`：新增 `FOLDER_TREE_ADDED_COLUMNS`、`FOLDER_TREE_DDL_STATEMENTS`、`FOLDER_TREE_BACKFILL_STATEMENTS`、`FOLDER_TREE_UNIQUE_INDEX_STATEMENTS`、`folder_tree_ddl_script()`、`_ensure_document_tree_columns(connection)`、`backfill_name_keys(connection)`、`missing_folder_tree_columns(connection)`；`EXPECTED_COLUMNS["documents"]` 追加新列；`ensure_schema()` 追加调用（顺序见"数据迁移"）。**不改** `DDL_STATEMENTS`（001 逐字一致，已有迁移不改）。
- 新建 `src/deploy/migrations/007_folder_tree.sql`：由 `folder_tree_ddl_script()` 原样摘录（头注释含单源声明、应用方式、回滚说明，格式参照 `006_llm_key.sql`）。
- 新建 `src/ib/core/library.py`：见 IFC-014。
- 修改 `src/ib/core/types.py`：`DocumentRecord`（`types.py:409-428`）**尾部追加**带默认值字段。

**IFC-014 `src/ib/core/library.py`（纯函数 + 类型，无 IO）**

```python
ROOT_FOLDER_ID: Final[str] = ""
NAME_MAX_LEN: Final[int] = 255

EntryKind = Literal["folder", "file"]
ConflictAction = Literal["overwrite", "skip", "rename"]

class EntryNameError(ValidationError):
    # code ∈ {"name_empty","name_illegal_char","name_too_long"}
    ...

def validate_entry_name(name: str) -> str:
    """strip 后返回规范展示名；空/仅空白 → code=name_empty；含 '/' 或 '\\' → name_illegal_char；
    len>255 → name_too_long。另拒绝名称恰为 '.' 或 '..'（name_illegal_char）。"""

def name_key_of(name: str) -> str:
    """unicodedata.normalize('NFC', name.strip()).casefold()；同目录唯一性的比较键（ADR-002）。"""

def next_free_name(name: str, taken_keys: Collection[str], *, is_file: bool) -> str:
    """文件 'a.pdf' → 'a (2).pdf'，文件夹 'A' → 'A (2)'；序号顺延至 name_key 不在 taken_keys 中；
    结果长度超 255 时截断主名保留扩展名。"""

@dataclass(frozen=True, slots=True)
class EntryRef:
    kind: EntryKind
    entry_id: str

@dataclass(frozen=True, slots=True)
class FolderRecord:
    folder_id: str
    project_id: str
    parent_id: str          # '' = 根
    name: str
    name_key: str
    depth: int              # 根下一级 = 1
    created_at: str
    updated_at: str

@dataclass(frozen=True, slots=True)
class NameClash:
    """被冲突方（库中已存在的条目）。"""
    kind: EntryKind
    entry_id: str
    name: str

@dataclass(frozen=True, slots=True)
class EntryLocation:
    doc_id: str
    name: str
    folder_id: str
    folder_path: tuple[str, ...]      # 目录名链，根起，不含文件名

    @property
    def path(self) -> str: ...        # '/'.join((*folder_path, name))；根目录文件仅 name

class LibraryConflictError(ConflictError):
    code = "name_conflict"
    clashes: tuple[NameClash, ...]
    # 另有 code 取值 "update_in_progress"、"doc_busy"（同为 ConflictError 子类，同一类携带 code 参数）

class LibraryValidationError(ValidationError):
    # code ∈ {"depth_exceeded","move_into_self","ext_change_not_allowed","limit_files",
    #         "limit_total_bytes","confirm_required","bad_request"}
    details: Mapping[str, object] | None
```

**`DocumentRecord` 追加字段**（全部尾部、带默认值，保持按位置构造的既有代码/测试兼容）：

```python
folder_id: str = ""                    # '' = 根
name_key: str = ""                     # '' = 修订行（隐藏）或尚未回填
uploaded_at: str = ""                  # 首次上传登记时间（UTC 定长）
content_updated_at: str | None = None  # None = 从未更新
indexed_at: str | None = None          # 最近一次索引成功时间
revision_of: str | None = None         # 非空 = 修订行，值为旧（存活）doc_id
```

**输入校验 / 鉴权**：本模块无对外接口（纯库）。
**依赖**：无。**外部依赖**：标准库 `unicodedata`、`sqlite3`。
**测试落点**：`tests/unit/test_library_names.py`、`tests/unit/test_library_schema_migration_007.py`。

---

### MOD-002 目录树与条目台账存储

**职责**：在**同一 SQLite 台账、同一写事务机制**（`SqliteLedgerRepository._write()`，`BEGIN IMMEDIATE`，`sqlite_repo.py:239-253`）内实现目录树、同名约束、移动、修订晋升、存活解析与清理队列。

**文件**：
- 新建 `src/ib/ledger/tree.py`：`EntryTreeStore`（Protocol）、`SqliteEntryTree`、`MemoryEntryTree`。`SqliteEntryTree(ledger: SqliteLedgerRepository)` 复用其连接与 `_write()`（包内协作，文档注明）；`MemoryEntryTree(ledger: InMemoryLedgerRepository)` 作离线替身，两实现过**同一套端口一致性测试**（M-SA-001）。
- 修改 `src/ib/ledger/sqlite_repo.py`：`_DOC_COLUMNS`（`sqlite_repo.py:54-72`）与 `_row_to_document` 追加新列；`create_document` 保持签名不变并写 `uploaded_at=created_at`、`folder_id=''`、`name_key=name_key_of(doc_name)`（旧入口 `POST /api/files` 即根目录创建，且在同一事务内做同名检查）；`mark_indexed` 的同一 UPDATE 追加 `indexed_at=now`；`list_documents` 追加关键字参数 `include_revisions: bool = True`（默认 True，保持 `RebuildService._count` 行为：`rebuild/__init__.py:345-354`）。
- 修改 `src/ib/ledger/__init__.py`：`InMemoryLedgerRepository` 同步上述语义。

**IFC-015 `EntryTreeStore`**

```python
@dataclass(frozen=True, slots=True)
class ChildrenPage:
    items: tuple[FolderRecord | DocumentRecord, ...]   # 文件夹在前；(类别, name_key, id) 稳定升序；不含修订行
    total: int

@dataclass(frozen=True, slots=True)
class SubtreeCount:
    folders: int            # 不含自身
    files: int              # 存活文件（不含修订行）

@dataclass(frozen=True, slots=True)
class MoveOutcome:
    moved: tuple[EntryRef, ...]
    skipped: tuple[EntryRef, ...]
    renamed: tuple[tuple[EntryRef, str], ...]          # (条目, 新名称)
    overwritten_doc_ids: tuple[str, ...]               # 已在本事务内移出台账，已入清理队列

@dataclass(frozen=True, slots=True)
class CreatedDocument:
    record: DocumentRecord
    created_folders: tuple[FolderRecord, ...]          # 本次事务新建的目录链（供补偿用）

@dataclass(frozen=True, slots=True)
class PromoteOutcome:
    kind: Literal["promoted", "ready"]   # ready = 已索引但推迟晋升（ADR-007）
    record: DocumentRecord               # promoted: 晋升后的存活行；ready: 修订行本身
    retired_doc_id: str | None           # promoted 时的旧 doc_id（已入清理队列）
    renamed_to: str | None               # 晋升时因重名自动改名后的显示名

class EntryTreeStore(Protocol):
    # ---- 浏览 ----
    def list_children(self, scope: Scope, folder_id: str, *, page: int, page_size: int) -> ChildrenPage: ...
    def get_folder(self, scope: Scope, folder_id: str) -> FolderRecord | None: ...
    def folder_chain(self, scope: Scope, folder_id: str) -> tuple[FolderRecord, ...]:
        """根起（不含根）到 folder_id 的目录链；folder_id=='' 返回空元组；不存在 → NotFoundError。"""
    def count_subtree(self, scope: Scope, folder_id: str) -> SubtreeCount: ...
    def list_subtree_documents(self, scope: Scope, folder_id: str, *, limit: int) -> list[DocumentRecord]:
        """含修订行；按 (depth 降序, doc_id) 稳定；limit 上限由调用方控制。"""

    # ---- 目录变更（每个方法 = 一个写事务）----
    def create_folder(self, scope: Scope, parent_id: str, name: str, *, max_depth: int) -> FolderRecord: ...
    def rename_folder(self, scope: Scope, folder_id: str, new_name: str) -> FolderRecord: ...
    def rename_document(self, scope: Scope, doc_id: str, new_name: str) -> DocumentRecord:
        """扩展名必须与 DocumentRecord.ext 一致（否则 LibraryValidationError ext_change_not_allowed）；
        同事务内更新 chunk_image.doc_name；不改 uploaded_at/content_updated_at/indexed_at/updated_at 之外的时间语义。"""
    def move_entries(
        self, scope: Scope, entries: Sequence[EntryRef], target_folder_id: str,
        resolutions: Mapping[str, ConflictAction], *, max_depth: int,
    ) -> MoveOutcome:
        """全有全无：任一冲突缺少 resolution → LibraryConflictError(clashes=…)，台账不变；
        目标在被移动文件夹自身或子孙内 → LibraryValidationError move_into_self；
        移动后最深层 > max_depth → depth_exceeded；子树 depth 在同一事务内重算。"""
    def delete_empty_folders(self, scope: Scope, folder_ids: Sequence[str]) -> int:
        """仅删除"已无文档且已无子目录"的目录；自底向上；返回实际删除数。"""

    # ---- 文档落库（带目录）----
    def create_document_in(
        self, scope: Scope, *, folder_id: str, rel_dirs: Sequence[str], name: str, ext: str,
        size_bytes: int, content_sha256: str, on_conflict: Literal["fail", "rename"], max_depth: int,
    ) -> CreatedDocument:
        """单事务：校验 folder_id 存在 → 逐级确保 rel_dirs（缺失则建，受 max_depth 限制）→
        同名检查（文件/文件夹跨类，不区分大小写）→ 插入 pending 行。
        on_conflict='fail' → LibraryConflictError；'rename' → next_free_name 顺延。"""
    def find_name_clashes(
        self, scope: Scope, folder_id: str, names: Sequence[str],
    ) -> dict[str, NameClash]:
        """key = name_key_of(name) 命中的现有条目；用于批次计划与冲突弹窗（只读）。"""

    # ---- 修订（更新）----
    def create_revision(
        self, scope: Scope, live_doc_id: str, *, new_name: str, ext: str, size_bytes: int,
        content_sha256: str, on_conflict: Literal["fail", "rename"],
    ) -> tuple[DocumentRecord, tuple[DocumentRecord, ...]]:
        """返回 (新修订行, 被替换掉的旧修订行们——调用方负责物理清理)。
        前置：live 行存在且 status ∈ {indexed, failed}，否则 LibraryConflictError(code='doc_busy')；
        已有修订行 parsing → LibraryConflictError(code='update_in_progress')；
        修订行：name_key=''、revision_of=live_doc_id、folder_id 同旧行、uploaded_at 同旧行；
        新名称与同目录其他条目（不含 live 自身）冲突：fail → LibraryConflictError；rename → 自动顺延。"""
    def get_revision_of(self, scope: Scope, live_doc_id: str) -> DocumentRecord | None: ...
    def promote_revision(
        self, scope: Scope, revision_doc_id: str, *, collection_version: str, chunk_count: int,
        active_version: str,
    ) -> PromoteOutcome:
        """worker 在修订行索引成功后调用（代替 mark_indexed）。
        同一写事务：断言 parsing→indexed（复用 _assert_transition）→ 写 indexed 字段与 indexed_at；
        若 collection_version == active_version：旧行存在则删除旧行（级联 chunks/chunk_image）、
        修订行晋升为存活行（revision_of=NULL；name_key 重算；folder_id 取旧行当前值；
        uploaded_at/created_at 取旧行值；content_updated_at=now；名称被占用则 next_free_name）、
        旧 doc_id 入 doc_purge_queue；旧行已不存在 → NotFoundError（修订行随后由生命周期丢弃）；
        否则 kind='ready'（旧行保持存活）。"""
    def list_ready_revisions(self, project_id: str, *, active_version: str, limit: int) -> list[DocumentRecord]:
        """status='indexed' ∧ revision_of 非空 ∧ indexed_collection_version == active_version。"""
    def promote_ready(self, scope: Scope, revision_doc_id: str, *, active_version: str) -> PromoteOutcome | None:
        """对"就绪待晋升"的修订行重做晋升事务；条件不再满足返回 None。"""

    # ---- 存活解析（检索与引用）----
    def resolve_live(self, project_id: str, doc_ids: Sequence[str]) -> dict[str, EntryLocation]:
        """只返回台账中存活（存在且 revision_of 为空）的文档；目录路径由父链推导。"""

    # ---- 清理队列 ----
    def enqueue_purge(self, project_id: str, kb_id: str, doc_id: str, reason: str) -> None: ...
    def list_purge(self, limit: int) -> list[PurgeItem]: ...
    def ack_purge(self, doc_id: str) -> None: ...

@dataclass(frozen=True, slots=True)
class PurgeItem:
    doc_id: str
    project_id: str
    kb_id: str
    reason: str
    attempts: int
```

**并发保证（ADR-002）**：所有变更方法在 `_write()`（`BEGIN IMMEDIATE`）内"先检查后写"，因此 ib-web 多线程与 ib-worker 之间同名检查与写入原子；部分唯一索引 `uq_documents_name`、`uq_folders_name` 作为第二道保险，`sqlite3.IntegrityError` 映射为 `LibraryConflictError`。`depth` 校验与子树 `depth` 重算（递归 CTE）也在同一事务内。

**鉴权 / 输入校验**：存储层不做鉴权；所有方法均要求 `Scope`（项目作用域），所有 SQL 经 `_scope_clause`/显式 `project_id =` 下推；`folder_id`/`doc_id` 不存在或不属于该项目 → `NotFoundError`（不区分，M-SA-007）。名称经 `validate_entry_name` 后进入。
**依赖**：MOD-001。**外部依赖**：标准库 `sqlite3`；用到递归 CTE（SQLite ≥3.8.3）与部分索引（≥3.8.0）。开发机实测 `sqlite3.sqlite_version` = 3.45.1；目标机版本未实测，`[ASSUMPTION]` 其为 Ubuntu 系统库版本（远高于上述门槛），部署前以 `python3 -c "import sqlite3;print(sqlite3.sqlite_version)"` 核实。
**测试落点**：`tests/unit/test_library_tree_store.py`（Sqlite 与 Memory 参数化，同一套断言）、`tests/unit/test_library_revision_promote.py`。

---

### MOD-003 上传批次存储

**职责**：持久化"批次 + 逐项计划/结果"，服务端权威地核对每个到达文件，并按 TTL 清理。

**文件**：新建 `src/ib/ledger/upload_batches.py`：`UploadBatchStore`（Protocol）、`SqliteUploadBatchStore`、`MemoryUploadBatchStore`（共用同一 SQLite 台账路径，线程局部连接，与 `SqliteProjectRegistryStore` 同构，`projects.py:76`）。

**IFC-016**

```python
ItemAction = Literal["create", "update", "skip"]
ItemState = Literal["planned", "accepted", "skipped", "failed"]

@dataclass(frozen=True, slots=True)
class BatchItemPlan:
    client_idx: int
    rel_path: str                    # 客户端提交的相对路径（含文件名）
    final_rel_path: str | None       # 服务端定稿（含自动改名）；skip 为 None
    action: ItemAction
    declared_size: int
    target_doc_id: str | None        # action='update' 时的旧 doc_id
    reason_code: str | None          # action='skip' 时的跳过原因

@dataclass(frozen=True, slots=True)
class BatchItem:
    batch_id: str
    client_idx: int
    rel_path: str
    final_rel_path: str | None
    action: ItemAction
    declared_size: int
    target_doc_id: str | None
    state: ItemState
    reason_code: str | None
    doc_id: str | None

@dataclass(frozen=True, slots=True)
class BatchRecord:
    batch_id: str
    project_id: str
    target_folder_id: str
    planned_files: int
    planned_bytes: int
    created_at: str
    expires_at: str

@dataclass(frozen=True, slots=True)
class BatchSummary:
    batch: BatchRecord
    total: int
    accepted: int
    skipped: int
    failed: int
    pending: int                     # state='planned'
    items: tuple[BatchItem, ...]

class UploadBatchStore(Protocol):
    def create_batch(self, scope: Scope, *, target_folder_id: str, items: Sequence[BatchItemPlan], ttl_hours: int) -> BatchRecord:
        """同事务写批次与全部项；action='skip' 的项初始 state='skipped'，其余 'planned'；顺带清理已过期批次。"""
    def get_batch(self, scope: Scope, batch_id: str) -> BatchRecord | None: ...
    def get_item(self, scope: Scope, batch_id: str, client_idx: int) -> BatchItem | None: ...
    def mark_item(self, scope: Scope, batch_id: str, client_idx: int, *, state: ItemState,
                  reason_code: str | None, doc_id: str | None, final_rel_path: str | None) -> BatchItem:
        """仅允许 planned/failed → accepted|skipped|failed；accepted/skipped 为终态，重复调用幂等返回现状。"""
    def summarize(self, scope: Scope, batch_id: str) -> BatchSummary: ...
    def purge_expired(self, now_iso: str) -> int: ...
```

**输入校验 / 鉴权**：存储层无鉴权；所有方法限定 `scope.project_id`，批次不属于该项目 → `None`/`NotFoundError`。`client_idx` 在 `[0, planned_files)`，主键 `(batch_id, client_idx)`。
**依赖**：MOD-001。**外部依赖**：标准库。
**测试落点**：`tests/unit/test_library_upload_batch_store.py`。

---

### MOD-004 文档生命周期扩展

**职责**：在既有 `DocumentLifecycle`（`src/ib/lifecycle/__init__.py:222-247`）上增量扩展；**不改**既有方法签名与语义（`validate_upload`/`submit_upload`/`process_pending`/`delete_document`/`retry_document`）。构造参数新增 `tree: EntryTreeStore | None = None`、`active_version_provider: Callable[[str], str] | None = None`（取项目**当前 active**版本，来自台账 `active_collection_version`，`sqlite_repo.py:553`；而不是被重建重定向后的写路径 provider）；两者缺省时修订相关方法抛 `DependencyUnavailableError`（旧装配兼容）。

**IFC-017 新增方法与类型**

```python
class UploadRejection(str, Enum):
    UNSUPPORTED_TYPE = "UNSUPPORTED_TYPE"
    EMPTY_FILE = "EMPTY_FILE"
    TOO_LARGE = "TOO_LARGE"
    MAGIC_MISMATCH = "MAGIC_MISMATCH"

@dataclass(frozen=True, slots=True)
class RejectedUpload:
    reason: UploadRejection
    message: str                         # 与 validate_upload 现有中文提示一致

@dataclass(frozen=True, slots=True)
class DocumentPlacement:
    folder_id: str                       # '' = 根
    rel_dirs: tuple[str, ...]            # 需在 folder_id 之下确保存在的目录（展示名，已校验）
    name: str                            # 文件展示名（含扩展名）
    on_conflict: Literal["fail", "rename"] = "fail"

@dataclass(frozen=True, slots=True)
class RevisionResult:
    changed: bool                        # False = 内容与现有完全相同（不建修订行）
    live: DocumentRecord                 # 存活行（changed=False 时即现有行）
    revision: DocumentRecord | None      # 新修订行
    final_name: str

class DocumentLifecycle:
    def classify_upload(self, filename: str, size_bytes: int, head: bytes) -> ValidatedUpload | RejectedUpload:
        """非抛出式分类，顺序与 validate_upload 完全一致；validate_upload 改为基于它实现（行为、消息不变）。"""

    def submit_library_document(
        self, ctx: RequestContext, validated: ValidatedUpload, kb_id: str, *,
        placement: DocumentPlacement, data: BinaryIO,
    ) -> DocumentRecord:
        """目录内落库：assert_kb_in_project → 读流算 sha256（≤max_upload_bytes）→
        tree.create_document_in（单事务建目录链 + pending 行）→ blob put；
        blob 失败 → _compensate_upload（删台账行）并调用 tree.delete_empty_folders(created_folders)；
        返回 pending 记录。与 submit_upload 一致的 fail-closed（DependencyUnavailableError → 503）。"""

    def submit_revision(
        self, ctx: RequestContext, doc_id: str, validated: ValidatedUpload, *,
        data: BinaryIO, new_name: str, on_conflict: Literal["fail", "rename"] = "fail",
    ) -> RevisionResult:
        """更新：读存活行 → 若 sha256 相同且存活行 indexed → RevisionResult(changed=False)；
        否则 tree.create_revision → blob put（用修订行 doc_id）；被替换的旧修订行逐个
        delete_document 式清理（向量→blob→台账）；blob 失败补偿删除修订行。"""

    def discard_revision(self, scope: Scope, live_doc_id: str) -> bool:
        """丢弃 pending/failed 的修订行（parsing → ConflictError update_in_progress）；返回是否有修订被丢弃。"""

    def retry_revision(self, scope: Scope, live_doc_id: str) -> DocumentRecord:
        """修订行 failed → pending（沿用 retry_document 的状态校验）；无失败修订 → ConflictError。"""

    def promote_ready_revisions(self, project_id: str, limit: int = 50) -> int:
        """补晋升：list_ready_revisions(active_version) → promote_ready → 晋升后调用 drain_purge_queue。"""

    def drain_purge_queue(self, limit: int = 50) -> int:
        """逐项：vectors.delete_doc_everywhere(project, Scope(project,(kb,)), doc_id) → blobs.delete → ack；
        任一步异常保留队列项并 attempts+1，不外抛（记 WARNING，只记码不记内容）。返回已出队数。"""
```

**对既有方法的修改（行为说明）**：
1. `_process_one` 第 9 步（`lifecycle/__init__.py:614-617`）：若 `record.revision_of` 非空 → 调 `tree.promote_revision(scope, doc_id, collection_version=project.active_collection_version, chunk_count=len(chunks), active_version=active_version_provider(project_id))` 代替 `mark_indexed`；`kind=="promoted"` 后立即对 `retired_doc_id` 调 `drain_purge_queue`（best-effort）；`NotFoundError`（旧行已被删）→ 走既有"并发删除"分支，丢弃已写向量并删除修订行。普通行路径不变。
2. `delete_document`（`lifecycle/__init__.py:654-717`）：函数开头若 `tree` 存在且 `get_revision_of(scope, doc_id)` 非空 → 先对修订行递归调用 `delete_document`（顺序"向量→blob→台账"不变），再按原顺序删除存活行；`DeleteReport` 三字段语义不变。
3. 失败原因码：`ERROR_CODES` 不新增；修订失败沿用 `_fail_document`，`error_code` 对外经 `update_error_code` 暴露。

**鉴权 / 校验**：不在本层（由 MOD-012 的 `_require_manage` 前置）；本层断言 `kb_id` 属项目（`assert_kb_in_project`）、大小 ≤ `max_upload_bytes`（读流后再校验一次，沿用 `lifecycle/__init__.py:339-342`）。
**降级 / 失败语义**：写路径 fail-closed（台账或 blob 不可用 → `DependencyUnavailableError` → 503，M-SA-005）；`drain_purge_queue`/`promote_ready_revisions` 为后台动作，失败不外抛、可重试。
**依赖**：MOD-001、MOD-002。**外部依赖**：既有向量库/blob/台账端口（不新增方法）。
**测试落点**：`tests/unit/test_library_lifecycle_revision.py`、`tests/integration/test_library_rebuild_coexist.py`。

---

### MOD-005 检索命中解析与引用路径

**职责**：检索结果以台账为存活与展示名/路径的权威（ADR-005）。

**文件**：
- 修改 `src/ib/retrieval/__init__.py`：`RetrievalService.__init__`（`retrieval/__init__.py:67-91`）新增可选参数 `entry_resolver: EntryResolver | None = None`；`search`（步骤 3 之后、步骤 4 映射之前，`retrieval/__init__.py:~154-186`）增加"存活过滤 + 名称/路径回填"；`search_as_tool` 文本行（`:244-246`）改用 `hit.doc_path or hit.doc_name`。
- 修改 `src/ib/core/types.py`：`RetrievedChunk`（`types.py:268-277`）、`CitationItem`（`types.py:752-765`）、`RelatedImageItem`（`types.py:345-357`）尾部追加 `doc_path: str = ""`。
- 修改 `src/ib/streaming/__init__.py`：`citations` 编码（`:482-490`）与 `related_images_json`（`:103-121`）追加 `"doc_path"` 键（键追加，既有键不变）。

**IFC-018**

```python
class EntryResolver(Protocol):
    def resolve_live(self, project_id: str, doc_ids: Sequence[str]) -> Mapping[str, EntryLocation]:
        """返回存活文档的当前位置；缺失的 doc_id 视为已删除/被替换/修订行。"""

class RetrievalService:
    def __init__(self, *, embedder: Any, vectors: Any, resolver: Any,
                 project_provider: Callable[[str], Any], top_k: int = 5, score_threshold: float = 0.35,
                 candidate_multiplier: int = 4, hot_timeout_s: float = 5.0,
                 entry_resolver: EntryResolver | None = None) -> None: ...
    # search(...) -> RetrievalResult   签名不变
```

**行为契约**：
- `entry_resolver` 为 `None`：与基线完全一致（不过滤、不回填）。
- 非 `None`：对候选 `doc_id` 去重后**一次**调用 `resolve_live`；不在返回映射内的命中被丢弃；其余命中 `doc_name=location.name`、`doc_path=location.path`；之后再截取 `top_k`（候选数 = `top_k × candidate_multiplier`，已有，足以吸收过滤损失）。
- `resolve_live` 抛异常 → `_degrade(..., DegradeReason.LEDGER_UNAVAILABLE, ...)`，`hits=[]`（fail-closed，M-SA-005；**不新增枚举值**）。
- **正例判据（供成对测试）**：台账可用、命中均存活 → `degraded is False`，每个 `hit.doc_name/doc_path` 等于台账当前值；全部命中不存活 → `degraded is False` 且 `hits == []`（与"依赖故障"取值不同）；`resolve_live` 故障 → `degraded is True ∧ degrade_reason == LEDGER_UNAVAILABLE`。

**鉴权 / 校验**：沿用问答链路既有鉴权；`project_id` 取自 `scope.project_id`（服务端结论）。
**依赖**：MOD-001（`EntryLocation` 类型）。**外部依赖**：无。
**测试落点**：`tests/unit/test_library_retrieval_resolver.py`。

---

### MOD-006 目录管理服务

**职责**：目录/文件管理的业务编排（浏览、新建、改名、移动、分步删除）。纯 Python，不依赖 Django；权限由调用方（MOD-012）前置。

**文件**：新建 `src/ib/library/__init__.py`。

**IFC-019**

```python
@dataclass(frozen=True, slots=True)
class FolderCrumb:
    folder_id: str
    name: str

@dataclass(frozen=True, slots=True)
class FileEntryView:
    record: DocumentRecord
    searchable: bool                       # status=='indexed' ∧ indexed_collection_version == 项目 active 版本
    update_state: Literal["updating", "update_failed"] | None
    update_error_code: str | None

@dataclass(frozen=True, slots=True)
class BrowsePage:
    folder: FolderRecord | None            # None = 根
    breadcrumb: tuple[FolderCrumb, ...]
    folders: tuple[FolderRecord, ...]
    files: tuple[FileEntryView, ...]
    total: int
    page: int
    page_size: int

@dataclass(frozen=True, slots=True)
class FolderDetail:
    folder: FolderRecord
    subtree_folders: int
    subtree_files: int

@dataclass(frozen=True, slots=True)
class FolderDeleteStep:
    done: bool
    deleted_files: int
    deleted_folders: int
    failed: tuple[FailedDelete, ...]
    remaining_files: int

@dataclass(frozen=True, slots=True)
class FailedDelete:
    doc_id: str
    name: str
    path: str
    error_code: str                        # 异常类名对应的稳定码，不含异常文本

class LibraryService:
    def __init__(self, *, tree: EntryTreeStore, lifecycle: DocumentLifecycle,
                 ledger: Any, max_depth: int, delete_step_max_files: int = 100,
                 delete_step_budget_s: float = 20.0) -> None: ...

    def browse(self, scope: Scope, folder_id: str, *, page: int, page_size: int) -> BrowsePage: ...
    def folder_detail(self, scope: Scope, folder_id: str) -> FolderDetail: ...
    def create_folder(self, scope: Scope, parent_id: str, name: str) -> FolderRecord: ...
    def rename_folder(self, scope: Scope, folder_id: str, name: str) -> FolderRecord: ...
    def rename_file(self, scope: Scope, doc_id: str, name: str) -> DocumentRecord: ...
    def move(self, scope: Scope, entries: Sequence[EntryRef], target_folder_id: str,
             resolutions: Mapping[str, ConflictAction]) -> MoveOutcome: ...
    def delete_folder_step(self, scope: Scope, folder_id: str, *, max_files: int | None = None) -> FolderDeleteStep:
        """取子树至多 N 个文档（含修订行，修订行先于存活行）逐个 lifecycle.delete_document；
        单文件异常 → 记入 failed 并继续；本步结束后对"已空"目录自底向上 delete_empty_folders；
        done = 子树内已无文档且目录已删。失败文件及其目录链保留可见。"""
```

**行为约束**：
- `move` 的 `overwritten_doc_ids` 由存储层事务内入清理队列（物理清理由 worker 周期完成，存活过滤保证期间不可检索）。
- `browse` 的 `searchable` 用台账 `active_collection_version(project_id)`（`sqlite_repo.py:553`）一次取值，不逐文件查。
- 不访问 `cfg.projects`（M-SA-018）。

**输入校验**：名称经 `validate_entry_name`；`page ≥ 1`、`page_size` 截断到 `[1, 100]`；`folder_id` 不存在 → `NotFoundError`。
**鉴权**：服务层不鉴权（调用方保证）。
**依赖**：MOD-002（IFC-015）、MOD-004（`delete_document`、`DocumentLifecycle`）。**外部依赖**：无。
**测试落点**：`tests/unit/test_library_service.py`、`tests/integration/test_library_api_flow.py`。

---

### MOD-007 批量上传编排服务

**职责**：把"清单 → 计划 → 批次 → 逐文件受理"串成服务端权威的流程（ADR-003）。

**文件**：新建 `src/ib/library/uploads.py`。

**IFC-020**

```python
@dataclass(frozen=True, slots=True)
class ManifestEntry:
    client_idx: int
    rel_path: str                      # '/' 分隔；末段为文件名
    size: int

@dataclass(frozen=True, slots=True)
class UploadLimits:
    max_files: int
    max_total_bytes: int
    max_depth: int
    max_file_bytes: int

@dataclass(frozen=True, slots=True)
class PlannedItem:
    client_idx: int
    rel_path: str
    final_rel_path: str | None
    action: Literal["create", "update", "skip"]
    reason_code: str | None            # skip 原因：UNSUPPORTED_TYPE|EMPTY_FILE|TOO_LARGE|NAME_INVALID|USER_SKIPPED
    target_doc_id: str | None

@dataclass(frozen=True, slots=True)
class PlanConflict:
    rel_path: str                      # 文件：完整相对路径；文件夹：冲突的目录前缀
    kind: EntryKind
    existing_id: str
    existing_name: str

@dataclass(frozen=True, slots=True)
class UploadPlan:
    batch_id: str | None               # dry_run 为 None
    total: int
    limits: UploadLimits
    items: tuple[PlannedItem, ...]
    conflicts: tuple[PlanConflict, ...]
    accepted_count: int
    skipped_count: int

@dataclass(frozen=True, slots=True)
class UploadItemResult:
    client_idx: int
    state: Literal["accepted", "skipped", "failed"]
    reason_code: str | None            # skip 原因 + MAGIC_MISMATCH | SIZE_MISMATCH | NAME_CONFLICT | CONTENT_UNCHANGED | DOC_BUSY
    doc_id: str | None
    final_rel_path: str | None

class UploadBatchService:
    def __init__(self, *, tree: EntryTreeStore, batches: UploadBatchStore, lifecycle: DocumentLifecycle,
                 limits: UploadLimits, batch_ttl_hours: int) -> None: ...

    def plan(self, ctx: RequestContext, scope: Scope, *, target_folder_id: str,
             entries: Sequence[ManifestEntry], resolutions: Mapping[str, ConflictAction],
             commit: bool) -> UploadPlan:
        """校验顺序：条数 → 总大小 → 目录深度（仅统计含至少一个未跳过文件的目录）→ 逐项分类
        （扩展名/空/超大/名称非法）→ 同名冲突检测。任一限额违反 → LibraryValidationError，不落任何东西。
        commit=True 且存在未提供 resolution 的冲突 → LibraryConflictError(code='unresolved_conflict'-> 409)；
        commit=True 且无阻断 → 创建批次（不创建任何目录/文件，目录延迟到首个文件受理时建立）。"""

    def accept_item(self, ctx: RequestContext, scope: Scope, batch_id: str, client_idx: int,
                    *, filename: str, size_bytes: int, head: bytes, data: BinaryIO) -> UploadItemResult:
        """幂等：已 accepted/skipped 直接返回既有结果。流程：核对批次/项 → 实际大小 > declared_size →
        skipped SIZE_MISMATCH → lifecycle.classify_upload（魔数）→ RejectedUpload → skipped（原因码）→
        action='create' → lifecycle.submit_library_document（on_conflict='fail'；冲突 → skipped NAME_CONFLICT）→
        action='update' → lifecycle.submit_revision（changed=False → skipped CONTENT_UNCHANGED；
        doc_busy/update_in_progress → skipped DOC_BUSY）→ batches.mark_item。
        DependencyUnavailableError 不吞：item 记 failed(SERVER_ERROR) 后上抛（→503），可对同 idx 重试。"""

    def summary(self, scope: Scope, batch_id: str) -> BatchSummary: ...
```

**规则**：
- 限额来自 `UploadLimits`（配置，MOD-009）；服务端不信任客户端声明：`accept_item` 以实际字节数核对。声明大小之和 ≤ 总上限，且实际 ≤ 声明，因此累计实际字节数 ≤ 总上限（无需额外计数器）。
- 冲突动作：文件 `overwrite`→`update`（对应存活行 id）；`rename`→`next_free_name`；`skip`→`USER_SKIPPED`；文件夹 `overwrite`=合并；`rename`=整棵子树改用 `名称 (n)`；`skip`=整棵子树 `USER_SKIPPED`。
- 目录延迟创建：只在首个文件被受理时通过 `create_document_in` 与文件同事务创建（满足 AC-001-04：空/全跳过子文件夹不创建；魔数失败不会留下空目录）。
- 总汇总恒等：`accepted + skipped + failed + pending == total`，其中 `pending` 为尚未到达的项。

**输入校验（`plan`）**：`entries` 长度 `1..max_files`（超出 → `limit_files`，details `{limit, actual}`）；`Σsize ≤ max_total_bytes`（否则 `limit_total_bytes`，details `{limit, actual}`）；`client_idx` 唯一且 ∈ `[0, len)`；`rel_path` 长度 ≤4096、每段经 `validate_entry_name`（非法段 → 该项 skip `NAME_INVALID`）；`size` 为 `0 ≤ int ≤ 2**40`；深度超限 → `depth_exceeded`。
**鉴权**：调用方（MOD-012）前置 `_require_manage`；批次不属于 `scope.project_id` → `NotFoundError`。
**依赖**：MOD-002、MOD-003、MOD-004。**外部依赖**：无。
**测试落点**：`tests/unit/test_library_upload_plan.py`、`tests/integration/test_library_upload_batch_flow.py`。

---

### MOD-008 重建联动

**职责**：使修订晋升与重建激活正确共存（ADR-007）。

**文件**：修改 `src/ib/rebuild/__init__.py`。

**IFC-021（行为修改，签名不变）**
- `RebuildService.__init__` 新增可选参数 `revision_promoter: Callable[[str], int] | None = None`（`project_id → 晋升数`，装配为 `lifecycle.promote_ready_revisions`）。
- `activate_version(project_id, version)`（`rebuild/__init__.py:356-391`）：
  - `failed` 计数改为排除修订行（`list_documents(..., include_revisions=False)`）；`pending`/`parsing` 计数保持含修订行。
  - 台账 `activate_collection_version` 成功后，best-effort 调 `revision_promoter(project_id)`，异常只记日志（worker 每轮仍会补晋升，MOD-011）。
- `_count`（`rebuild/__init__.py:345-354`）增加可选 `include_revisions` 透传；`step_rebuild` 的计数口径不变（含修订行）。

**鉴权 / 校验**：沿用既有重建端点（`can_manage`）。
**依赖**：MOD-002（`list_documents` 新参数）、MOD-004（晋升函数）。
**测试落点**：`tests/integration/test_library_rebuild_coexist.py`（与 MOD-004 共用）。

---

### MOD-009 配置项

**职责**：新增可配置上限（REQ-FUNC-015、AC-015-03）。

**文件**：修改 `src/ib/config/__init__.py`（紧邻 `max_upload_mb`，`config/__init__.py:368`）。

**IFC-023**

```python
upload_batch_max_files: int = 1000          # IB_UPLOAD_BATCH_MAX_FILES；校验 1 ≤ v ≤ 10000
upload_batch_max_total_mb: int = 1024       # IB_UPLOAD_BATCH_MAX_TOTAL_MB；校验 1 ≤ v ≤ 102400 [ESTIMATE 默认值]
library_max_depth: int = 10                 # IB_LIBRARY_MAX_DEPTH；校验 1 ≤ v ≤ 64
upload_batch_ttl_hours: int = 24            # IB_UPLOAD_BATCH_TTL_HOURS；校验 1 ≤ v ≤ 720
```

非法取值（非整数/越界）→ `StartupError`（沿用既有配置校验风格，启动期 fail-fast，进程不起）。`max_upload_mb > 60` → 日志 WARNING（nginx 64m 限制，ADR-003），不改变基线行为。env 键写入 `/etc/intelligentbase/ib-web.env`（用户执行，重启 `ib-web`）；`ib-worker` 不使用这四键（worker 无上传入口），**不需要**写入 `ib-worker.env`。
**依赖**：无。**测试落点**：`tests/unit/test_library_config.py`。

---

### MOD-010 组合根装配

**职责**：在 `Deps`（`composition.py`）中装配新存储/服务；把 `SqliteEntryTree` 同时注入 `DocumentLifecycle`、`RetrievalService(entry_resolver=…)`、`RebuildService(revision_promoter=…)`；`related_images` 提供者（`composition.py:~420-500`）按 `hit.doc_path` 填 `RelatedImageItem.doc_path`、`doc_name` 取台账当前名（hits 已回填，不再读 `record.doc_name`）。

**IFC-024（`Deps` 新增字段）**

```python
tree: EntryTreeStore
upload_batches: UploadBatchStore
library: LibraryService
uploads: UploadBatchService
```

装配规则：`ledger_backend=sqlite` → `SqliteEntryTree`/`SqliteUploadBatchStore`；`memory` → 内存替身。`active_version_provider = ledger.active_collection_version`。**运行期新建项目不在 `cfg.projects`**：以上新对象均不读 `cfg.projects`（M-SA-018）。
**依赖**：MOD-002~009。**测试落点**：`tests/integration/test_library_api_flow.py`（装配冒烟）。

---

### MOD-011 ib-worker 周期动作

**职责**：在 `run_once`（`src/ibweb/worker.py:53-102`）末尾（重建推进之后、`cycle` 日志之前）追加：

```python
def run_once(*, lease_owner: str, limit: int, reap: bool = True) -> dict[str, Any]: ...
# 摘要新增键： "promoted": int, "purged": int, "batches_expired": int
```

步骤（均 `try/except Exception` + `log_event`，异常不外抛，与 `reap` 同口径）：对每个已知项目 `lifecycle.promote_ready_revisions(project_id)`；`lifecycle.drain_purge_queue()`；`upload_batches.purge_expired(now)`（低频，每轮廉价 DELETE）。项目集合取"注册表活动项目 ∪ `deps.projects`"（既有重建推进循环取 `deps.projects.keys()`，`worker.py:75`；运行期新建项目不在 `cfg.projects`，故新增循环以台账/注册表为准、config 仅回退，M-SA-018）。
**鉴权**：无（后台进程）。**依赖**：MOD-004、MOD-010。
**测试落点**：`tests/unit/test_library_worker_cycle.py`。

---

### MOD-012 HTTP 接口层

**职责**：新端点的路由、参数校验、鉴权、错误映射。统一约定：
- 鉴权：`Authorization: Bearer`（沿用中间件）；`?token=` 等一律由既有中间件 400，不新增传凭据路径。
- 写端点前置 `_require_manage(request)`（无权限 → 403，`views.py:285-290`）；浏览端点用 `_ctx_of(request)`。作用域 `composition.resolve_scope(ctx)`；`kb_id = scope.project_id`。
- 错误体沿用 `{"error": {"code": str, "message": str}}`，需要携带冲突列表时追加同级键 `"conflicts"`（由 `library_views` 本地构造，`error_response` 不变）。状态码：校验 400 / 无权限 403 / 不存在或不属于本项目 404 / 冲突 409 / 依赖不可用 503。
- ID 参数格式：`^[0-9a-f]{32}$` 或空串（根）；其余 → 400 `bad_request`。
- 路由顺序：字面量路由先于参数路由（`urls.py` 既有纪律）。

**文件**：新建 `src/ibweb/library_views.py`（视图函数）；修改 `src/ibweb/urls.py`（新增 `path` 条目）；修改 `src/ibweb/views.py`（`file_detail_endpoint` 增加 `PATCH` 分支委托给 `library_views.rename_file_endpoint`；`_list_files` 改传 `include_revisions=False`；`_upload_file`/`POST /api/files` 保持"根目录单文件"语义，遇同名返回 409 `name_conflict`——旧入口不再产生重名）；修改 `src/ibweb/serializers.py`（`LibraryFileSerializer`、`LibraryFolderSerializer`）。

**TypeScript 响应类型（同时是后端序列化契约）**

```ts
type DocStatus = 'pending' | 'parsing' | 'indexed' | 'failed';

interface FolderItem {
  kind: 'folder'; folder_id: string; name: string; depth: number;
  created_at: string; updated_at: string;
}
interface FileItem {
  kind: 'file'; doc_id: string; name: string; ext: string; size_bytes: number;
  status: DocStatus; error_code: string | null; chunk_count: number;
  uploaded_at: string;                       // ISO UTC，浏览器本地化显示
  content_updated_at: string | null;         // null = 从未更新
  indexed_at: string | null;                 // 仅 status==='indexed' 时非 null
  searchable: boolean;                       // 重建在途期间新增/更新的文件为 false
  update_state: 'updating' | 'update_failed' | null;
  update_error_code: string | null;
}
type LibraryItem = FolderItem | FileItem;
interface Crumb { folder_id: string; name: string }
type ConflictActionTs = 'overwrite' | 'skip' | 'rename';
interface ConflictInfo {
  rel_path?: string;                          // 上传场景
  entry?: { kind: 'file' | 'folder'; id: string; name: string };   // 移动/更新场景：发起方
  existing: { kind: 'file' | 'folder'; id: string; name: string };
}
interface ApiErrorBody {
  error: { code: string; message: string; details?: Record<string, unknown> };
  conflicts?: ConflictInfo[];
}
```

**HTTP 接口**

**IFC-001 `GET /api/library`** — 浏览。
- 鉴权：已认证本项目成员（**不要求**管理权限，CL-008/OQ-07）。
- Query：`folder_id`（可选，缺省/空 = 根；格式见上）、`page`（整数 ≥1，缺省 1）、`page_size`（整数，缺省 50，**截断到 ≤100**；非整数 → 400 `bad_request`）。
- 200：`{ folder: FolderItem | null; breadcrumb: Crumb[]; items: LibraryItem[]; total: number; page: number; page_size: number; permissions: { can_manage: boolean } }`。排序：文件夹在前，其后按 `name_key` 升序、`id` 升序（稳定，AC-003-02）。
- 错误：400；404（目录不存在或不属于本项目，A-10）。

**IFC-002 `GET /api/library/folders/{folder_id}`** — 目录详情（删除二次确认用）。鉴权：已认证成员。200：`{ folder: FolderItem; subtree_folders: number; subtree_files: number }`。404。

**IFC-003 `POST /api/library/folders`** — 新建文件夹。鉴权：`_require_manage`。
- Body：`{ parent_id: string; name: string }`（`name` 经 `validate_entry_name`，≤255）。
- 201：`FolderItem`。400：`name_empty`/`name_illegal_char`/`name_too_long`/`depth_exceeded`；404 父目录；409 `name_conflict`（`conflicts` 含现有条目）；403。

**IFC-004 `PATCH /api/library/folders/{folder_id}`** — 重命名。鉴权：`_require_manage`。Body：`{ name: string }`。200：`FolderItem`。400/403/404/409 同上。

**IFC-005 `DELETE /api/library/folders/{folder_id}`** — 分步递归删除（ADR-008）。鉴权：`_require_manage`。
- Body：`{ confirm: true; max_files?: number }`（`confirm` 缺失或非 `true` → 400 `confirm_required`；`max_files` 整数 `1..500`，缺省取配置 100）。
- 200：`{ done: boolean; deleted_files: number; deleted_folders: number; failed: { doc_id: string; name: string; path: string; error_code: string }[]; remaining_files: number }`。客户端在 `done=false` 时重复调用。404 / 403 / 503（台账不可用）。

**IFC-006 `POST /api/library/move`** — 移动文件/文件夹。鉴权：`_require_manage`。
- Body：`{ entries: { kind: 'file'|'folder'; id: string }[]; target_folder_id: string; resolutions?: Record<string, ConflictActionTs> }`（`entries` 长度 `1..200`；`resolutions` 键 = 发起条目 id）。
- 200：`{ moved: EntryRef[]; skipped: EntryRef[]; renamed: { id: string; kind: string; new_name: string }[]; overwritten: { id: string }[] }`。
- 409 `name_conflict` + `conflicts[]`（未提供 resolution 的冲突；**台账不变**）；400 `move_into_self`/`depth_exceeded`/`bad_request`；404（条目或目标不存在/不属于本项目——含"跨项目"，A-10）；403。

**IFC-007 `PATCH /api/files/{doc_id}`**（修改现有路由 `urls.py:42`）— 文件重命名。鉴权：`_require_manage`。Body：`{ name: string }`。200：`FileItem`。400：名称码、`ext_change_not_allowed`（A-04）；404；409 `name_conflict`；403。不改变三时间与状态（AC-012-01）。

**IFC-008 `POST /api/files/{doc_id}/revision`** — 更新文件内容。鉴权：`_require_manage`。
- Body：`multipart/form-data`：`file`（必填，≤ `IB_MAX_UPLOAD_MB`，经 `classify_upload` 三重校验）；`on_conflict`（可选，`fail`|`rename`，缺省 `fail`）。新显示名 = 上传文件名。
- 202：`{ changed: true; item: FileItem; final_name: string }`（`item` 为存活行，`update_state='updating'`）。
- 200：`{ changed: false; reason: 'CONTENT_UNCHANGED' }`（AC-008-06）。
- 400：`unsupported_type`|`empty_file`|`too_large`|`magic_mismatch`|名称码（响应 `error.code` 取 `UploadRejection` 小写）；403；404；409：`name_conflict`（`conflicts` 给出同目录冲突条目，供弹窗；`overwrite` 由客户端改以冲突条目为更新目标，A-02）、`doc_busy`（存活行 pending/parsing）、`update_in_progress`；503（台账/blob 不可用，fail-closed）。

**IFC-009 `DELETE /api/files/{doc_id}/revision`** — 丢弃未完成/失败的更新。鉴权：`_require_manage`。200：`{ discarded: boolean }`；409 `update_in_progress`（修订行 parsing）；404；403。

**IFC-010 `POST /api/uploads`** — 批次计划/提交。鉴权：`_require_manage`。
- Body：

```ts
interface UploadPlanRequest {
  target_folder_id: string;                 // '' = 根
  dry_run: boolean;                         // true: 只计划不落批次
  entries: { client_idx: number; rel_path: string; size: number }[];   // 1..max_files
  resolutions?: Record<string, ConflictActionTs>;  // 键 = 冲突的 rel_path（文件）或目录前缀（文件夹）
}
interface PlannedItemTs {
  client_idx: number; rel_path: string; final_rel_path: string | null;
  action: 'create' | 'update' | 'skip'; reason_code: string | null; target_doc_id: string | null;
}
interface UploadPlanResponse {
  batch_id: string | null; total: number;
  limits: { max_files: number; max_total_bytes: number; max_depth: number; max_file_bytes: number };
  items: PlannedItemTs[];
  conflicts: { rel_path: string; kind: 'file' | 'folder'; existing_id: string; existing_name: string }[];
  accepted_count: number; skipped_count: number;
}
```

- 200（`dry_run=true`，含 `conflicts` 供弹窗）；201（`dry_run=false`，`batch_id` 非空）。
- 400：`limit_files`（`details {limit, actual}`，AC-015-01）、`limit_total_bytes`（AC-015-04）、`depth_exceeded`（AC-015-02）、`bad_request`；404 目标目录；403；409 `unresolved_conflict`（提交时仍有未决冲突，`conflicts[]`）。**任何 4xx 均不产生批次、目录或文件**（"整体拒绝，不产生半成品"）。
- 请求体上限：JSON ≤ 1000 项约 0.2–4MB，远小于 64MB 限制，不触及 nginx/Django 上限。

**IFC-011 `PUT /api/uploads/{batch_id}/items/{client_idx}`** — 逐文件上传。鉴权：`_require_manage`。
- Body：`multipart/form-data`：`file`（必填）。`client_idx` 整数 ≥0。
- 200：`{ client_idx: number; state: 'accepted' | 'skipped'; reason_code: string | null; doc_id: string | null; final_rel_path: string | null }`（幂等：重复 PUT 返回既有终态）。
- 4xx/5xx：批次/项不存在或不属于本项目 404；文件缺失 400 `bad_request`；台账/blob 不可用 503（项记 `failed`，可对同 idx 重试）。
- 请求体上限：单文件 ≤ `IB_MAX_UPLOAD_MB`(50MB) + multipart 开销 < 64MB，现有 nginx `client_max_body_size 64m` 与 Django `DATA_UPLOAD_MAX_MEMORY_SIZE` 不变。

**IFC-012 `GET /api/uploads/{batch_id}`** — 批次汇总（页面刷新后恢复）。鉴权：`_require_manage`（与批次发起同口径）。200：`{ batch_id; target_folder_id; total; accepted; skipped; failed; pending; items: { client_idx; rel_path; final_rel_path: string|null; state: 'planned'|'accepted'|'skipped'|'failed'; reason_code: string|null; doc_id: string|null }[] }`。404。

**IFC-013（既有端点的受控修改）**：
- `GET /api/files`：不再返回修订行；其余不变（扁平兼容端点，保留）。
- `POST /api/files`：落根目录；同名 → 409 `name_conflict`。
- `POST /api/files/{doc_id}/retry`：若存活行 `indexed|failed` 且其修订行 `failed` → 重试修订行（`lifecycle.retry_revision`），否则沿用 `retry_document`。
- `DELETE /api/files/{doc_id}`：语义不变（级联修订行，MOD-004）。

**依赖**：MOD-004、MOD-006、MOD-007、MOD-010。
**测试落点**：`tests/integration/test_library_api_flow.py`、`tests/e2e/test_library_e2e_flow.py`。

---

### MOD-013 前端 API 客户端

**职责**：`src/frontend/src/api/client.ts` 是前端 HTTP 唯一出口（禁 axios、CDN）。在 `ApiClient`（`client.ts:~607-640` 邻近）新增类型与方法，请求头与错误处理沿用 `this.request`。

**IFC-025（方法签名）**

```ts
browse(params: { folder_id?: string; page?: number; page_size?: number }): Promise<LibraryPage>;
getFolder(folderId: string): Promise<FolderDetail>;
createFolder(parentId: string, name: string): Promise<FolderItem>;
renameFolder(folderId: string, name: string): Promise<FolderItem>;
deleteFolderStep(folderId: string, opts?: { max_files?: number }): Promise<FolderDeleteStep>;
moveEntries(req: MoveRequest): Promise<MoveResult>;          // 409 抛 ApiError，携带 conflicts
renameFile(docId: string, name: string): Promise<FileItem>;
updateFile(docId: string, file: File, onConflict?: 'fail' | 'rename'): Promise<UpdateResult>;
discardRevision(docId: string): Promise<{ discarded: boolean }>;
planUpload(req: UploadPlanRequest): Promise<UploadPlanResponse>;
uploadBatchItem(batchId: string, clientIdx: number, file: File): Promise<UploadItemResultTs>;
getUploadBatch(batchId: string): Promise<UploadBatchSummaryTs>;
```

新增 `ApiError` 扩展字段 `conflicts?: ConflictInfo[]`（解析响应体同级 `conflicts`）。既有 `uploadFile/listFiles/deleteFile/retryFile` 保持。
**依赖**：MOD-012（HTTP 契约）。**测试落点**：`src/frontend/tests/frontend.smoke.test.js`（契约字符串/导出存在性断言，沿用既有冒烟风格）。

---

### MOD-014 前端资料管理界面

**职责**：在**唯一导航入口**"资料管理"（路由 `files`，`router/index.ts:73-79`，组件 `UploadPage.vue`）内实现云盘式界面；`props: { client }` 契约不变。

| 组件 | 职责 |
|---|---|
| `UploadPage.vue`（改） | 页面骨架；挂载 `LibraryBrowser`；保留页面标题与项目域提示文案 |
| `views/library/LibraryBrowser.vue`（新） | 当前目录列表（文件夹在前）、面包屑与"返回上级"、分页（≤100/页）、新建文件夹、重命名、移动（目标目录选择）、更新、删除入口；显示 `uploaded_at / content_updated_at / indexed_at`（`fmtDate` 本地时区到秒，`—` 表示 null）、状态与失败原因、`update_state`、`searchable=false` 提示"已索引，重建切换后可检索"；无管理权限时隐藏写操作（`permissions.can_manage`） |
| `views/library/UploadBatchPanel.vue`（新） | 选择文件夹（`<input type="file" webkitdirectory multiple>`，读 `webkitRelativePath`）/多文件；先 `planUpload(dry_run)`，展示限额错误或冲突；确认后提交批次；**并发 2** 逐个 `uploadBatchItem`；整体进度"已处理 N / 总数"（单调不减，含计划期跳过项）；结束汇总：成功/跳过/失败三数 + 每个跳过/失败项的相对路径与原因 |
| `views/library/ConflictDialog.vue`（新） | 同名冲突三选项（覆盖 / 跳过 / 两者保留并自动改名）；文件夹合并覆盖时给出"同名文件将被覆盖"警示（A-03）；关闭未选择 = 取消整次操作（AC-011-04） |
| `views/library/FolderDeleteDialog.vue`（新） | 二次确认（`getFolder` 显示子文件夹/文件数）；循环 `deleteFolderStep` 至 `done`；展示 `failed` 列表（AC-006-03） |
| `stores/uploadBatch.ts`（新） | 批次状态机（计划→上传→汇总）、并发控制（固定 2）、重试单项、页面刷新后用 `getUploadBatch` 恢复 |
| `ChatPage.vue`（改） | `related_images` 项读取 `doc_path`，标题/`aria-label` 优先显示 `docPath`（`ChatPage.vue:66,217,382-386`） |

**交互约束**：文件夹入口在浏览器不支持 `webkitdirectory` 时隐藏（A-09）；HTTP 只经 `client.ts`；无 CDN/外链字体；路由保持 hash 模式；更新成功（202）后整表重新 `browse`（`doc_id` 会变，A-06）。
**依赖**：MOD-013。**测试落点**：`src/frontend/tests/frontend.smoke.test.js`（`npm run build` 后构建产物冒烟 + 组件导出存在性）。

---

### MOD-015 自检与测试

**文件**：修改 `src/scripts/selfcheck.py`（新增检查：① `007_folder_tree.sql` 与 `folder_tree_ddl_script()` 去空白后包含关系一致（参照 `selfcheck.py:3503-3513` 的 006 检查）；② 目录完整性对账——`documents.folder_id` 均指向存在的 `folders` 或 `''`、无循环父链、`depth` 与父链一致、无存活文档 `revision_of` 悬空）；CI 的 "Schema / migration check" 内联脚本（`.github/workflows/ci.yml:77-92`，画像 P4 所述）如需覆盖 007 由 devops 阶段决定（CI 属 devops 写权限）。

**测试文件（路径遵守画像 P3；基名必须全局唯一，开发前用 `ls tests/*/` 复核）**：
- `tests/unit/test_library_names.py`、`test_library_schema_migration_007.py`、`test_library_tree_store.py`、`test_library_revision_promote.py`、`test_library_upload_batch_store.py`、`test_library_upload_plan.py`、`test_library_lifecycle_revision.py`、`test_library_retrieval_resolver.py`、`test_library_service.py`、`test_library_config.py`、`test_library_worker_cycle.py`
- `tests/integration/test_library_api_flow.py`、`test_library_upload_batch_flow.py`、`test_library_rebuild_coexist.py`
- `tests/e2e/test_library_e2e_flow.py`
- 离线纪律不变：SQLite/内存/替身，不连 Qdrant/DeepSeek/ib-embed（`tests/conftest.py`）。

**必须成对覆盖的失败路径与正例判据**（供测试阶段）：

| 路径 | 失败/降级判据 | 同时必须有的正例判据 |
|---|---|---|
| 检索存活解析故障 | `degraded=True ∧ degrade_reason=LEDGER_UNAVAILABLE ∧ hits==[]` | 台账可用：`degraded=False`，名称/路径=台账当前值；全部命中被过滤：`degraded=False ∧ hits==[]` |
| 修订索引失败 | 存活行仍 `indexed`、旧关键词仍命中、`update_state='update_failed'` | 修订索引成功：旧关键词命中 0、新关键词命中、`content_updated_at` 非空、仅一条记录 |
| 重建在途更新 | 修订行 `ready` 未晋升、旧版仍可检索、`searchable=false` | 激活后 `promote_ready_revisions` → 旧版命中 0、新版命中 |
| 批次逐文件失败 | 该项 `failed`(503)，其余项不受影响，汇总三数之和=总数 | 重试同 `client_idx` 成功 → `accepted` |
| 分步删除部分失败 | `failed[]` 列出该文件，文件与目录链仍可见，`done=false` | 向量库恢复后再调 → `done=true`，目录删除，检索命中 0 |
| 同名并发 | 并发上传同名（含大小写变体）仅一个成功，其余 `name_conflict`/`NAME_CONFLICT` | 不同名并发全部成功 |
| 清理队列故障 | 队列项保留 `attempts+1`，孤儿向量对检索不可见 | 恢复后出队、向量/blob 物理消失 |

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-001 | US-001 | MOD-007（计划/受理/延迟建目录）、MOD-004、MOD-002、MOD-012、MOD-014 |
| REQ-FUNC-002 | US-002 | MOD-007、MOD-003、MOD-004（`classify_upload`）、MOD-012、MOD-014 |
| REQ-FUNC-003 | US-003 | MOD-006、MOD-002、MOD-012、MOD-014 |
| REQ-FUNC-004 | US-004 | MOD-006、MOD-002、MOD-012、MOD-014 |
| REQ-FUNC-005 | US-005 | MOD-006、MOD-002、MOD-005（路径随台账）、MOD-012 |
| REQ-FUNC-006 | US-006 | MOD-006（分步删除）、MOD-004（`delete_document` 级联修订）、MOD-012、MOD-014 |
| REQ-FUNC-007 | US-007 | MOD-007、MOD-004、MOD-012、MOD-014 |
| REQ-FUNC-008 | US-008 | MOD-004（`submit_revision`/晋升）、MOD-002（`create_revision`/`promote_revision`）、MOD-008、MOD-011、MOD-012、MOD-014 |
| REQ-FUNC-009 | US-009 | MOD-001（新列/回填）、MOD-002（`mark_indexed`/晋升写时间）、MOD-006（`FileEntryView`）、MOD-012、MOD-014 |
| REQ-FUNC-010 | US-010 | MOD-004（复用入库流水线）、MOD-005（检索过滤保持隔离）、MOD-010 |
| REQ-FUNC-011 | US-011 | MOD-007（冲突计划）、MOD-002（`find_name_clashes`/`create_document_in`）、MOD-006（移动冲突）、MOD-014（`ConflictDialog`） |
| REQ-FUNC-012 | US-012 | MOD-006、MOD-002（`rename_document`）、MOD-012 |
| REQ-FUNC-013 | US-013 | MOD-006、MOD-002（`move_entries`）、MOD-012、MOD-014 |
| REQ-FUNC-014 | US-014 | MOD-005（`doc_path`）、MOD-010（`related_images`）、MOD-014（`ChatPage.vue`） |
| REQ-FUNC-015 | US-015、US-004、US-013 | MOD-007（限额校验）、MOD-009（配置）、MOD-002（`max_depth`）、MOD-006 |
| REQ-FUNC-016 | US-016 | MOD-001（`validate_entry_name`/`name_key_of`）、MOD-002（唯一约束）、MOD-012 |
| REQ-FUNC-017 | US-017 | MOD-001（007 迁移 + 回填）、MOD-002（根目录语义）、MOD-015（对账自检） |
| REQ-NFUNC-001 | US-005/006/008/012/013 | MOD-005（存活过滤）、MOD-004、MOD-002、MOD-011（清理） |
| REQ-NFUNC-002 | US-008 | MOD-002（单事务晋升）、MOD-004、MOD-005 |
| REQ-NFUNC-003 | US-009 | MOD-004（失败码）、MOD-006（`update_state`/`indexed_at` 仅 indexed 返回）、MOD-012 |
| REQ-NFUNC-004 | US-008、US-009 | MOD-008、MOD-004、MOD-011、MOD-002 |
| REQ-NFUNC-005 | US-001/003/005/008 | MOD-012（`_require_manage`/`_ctx_of`/404 口径）、MOD-002（scope 下推） |
| REQ-NFUNC-006 | （专项测试） | MOD-002（覆盖索引）、MOD-006（分页上限）、MOD-014（并发 2、进度） |
| REQ-NFUNC-007 | US-002/006 | MOD-007（逐项独立）、MOD-006（分步删除）、MOD-002（移动全有全无） |

REQ-FUNC-001~017 无空行。

## 依赖关系

边的方向：调用方 → 被调用方（经由括号内 IFC）。**每条边均从较大编号指向较小编号**，故图无环。

- MOD-002 → MOD-001（IFC-014 类型/纯函数）
- MOD-003 → MOD-001（IFC-014）
- MOD-004 → MOD-001（IFC-014）、MOD-002（IFC-015）
- MOD-005 → MOD-001（`EntryLocation`、IFC-014；运行期由 MOD-002 实现的端口经 MOD-010 注入，非编译期依赖）
- MOD-006 → MOD-002（IFC-015）、MOD-004（IFC-017 `delete_document`）
- MOD-007 → MOD-002（IFC-015）、MOD-003（IFC-016）、MOD-004（IFC-017）
- MOD-008 → MOD-002（`list_documents` 参数）、MOD-004（IFC-017 `promote_ready_revisions`，经注入的 `Callable`）
- MOD-009 → （无）
- MOD-010 → MOD-002、MOD-003、MOD-004、MOD-005、MOD-006、MOD-007、MOD-008、MOD-009（装配）
- MOD-011 → MOD-004（IFC-017）、MOD-010（`composition.get_deps()`，IFC-024）
- MOD-012 → MOD-004、MOD-006（IFC-019）、MOD-007（IFC-020）、MOD-010（IFC-024）
- MOD-013 → MOD-012（HTTP：IFC-001~013）
- MOD-014 → MOD-013（IFC-025）
- MOD-015 → MOD-001~MOD-012（测试/自检）

**已检查：无循环依赖**（拓扑序即编号序 001→015；`ib.*` 不 import `ibweb.*`、`ib_embed`，符合画像 P8 与 C8 进程隔离；`ib.library` 仅依赖 `ib.core`/`ib.ledger`/`ib.lifecycle`）。

## 数据迁移

**有迁移**：新迁移号 **`src/deploy/migrations/007_folder_tree.sql`**（`006_llm_key.sql` 之后首个空号；已有 001~006 一字不改）。内容与 `src/ib/ledger/schema.py::folder_tree_ddl_script()` 逐字一致（单源，CI/自检以"去空白后包含"比对，参照 `.github/workflows/ci.yml:77-92` 与 `selfcheck.py:3503-3513`）。

**1) 新增表**

```sql
CREATE TABLE IF NOT EXISTS folders (
    folder_id   TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    parent_id   TEXT NOT NULL DEFAULT '',     -- '' = 根
    name        TEXT NOT NULL,
    name_key    TEXT NOT NULL,                 -- NFC + casefold
    depth       INTEGER NOT NULL,              -- 根下一级 = 1；CHECK (depth >= 1)
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    CHECK (depth >= 1)
);
CREATE TABLE IF NOT EXISTS upload_batches (
    batch_id         TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL,
    target_folder_id TEXT NOT NULL DEFAULT '',
    planned_files    INTEGER NOT NULL,
    planned_bytes    INTEGER NOT NULL,
    created_at       TEXT NOT NULL,
    expires_at       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS upload_batch_items (
    batch_id        TEXT NOT NULL REFERENCES upload_batches(batch_id) ON DELETE CASCADE,
    client_idx      INTEGER NOT NULL,
    rel_path        TEXT NOT NULL,
    final_rel_path  TEXT,
    action          TEXT NOT NULL,
    declared_size   INTEGER NOT NULL,
    target_doc_id   TEXT,
    state           TEXT NOT NULL,
    reason_code     TEXT,
    doc_id          TEXT,
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (batch_id, client_idx),
    CHECK (action IN ('create', 'update', 'skip')),
    CHECK (state IN ('planned', 'accepted', 'skipped', 'failed'))
);
CREATE TABLE IF NOT EXISTS doc_purge_queue (
    doc_id      TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    kb_id       TEXT NOT NULL,
    reason      TEXT NOT NULL,
    attempts    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);
```

**2) 既有表 `documents` 新增 6 列**（老库补列沿用 REV-18 做法：`schema.py:340-352,531-551`——`PRAGMA table_info` 探测 + 逐列 `ALTER TABLE … ADD COLUMN`；SQLite 无 `ADD COLUMN IF NOT EXISTS`）：

| 列 | 定义 | 说明 |
|---|---|---|
| `folder_id` | `TEXT NOT NULL DEFAULT ''` | `''` = 根（REQ-FUNC-017：既有行自动归根） |
| `name_key` | `TEXT NOT NULL DEFAULT ''` | 比较键；`''` = 修订行或待回填 |
| `uploaded_at` | `TEXT NOT NULL DEFAULT ''` | 回填 `= created_at` |
| `content_updated_at` | `TEXT`（可空） | NULL = 从未更新 |
| `indexed_at` | `TEXT`（可空） | 回填 `= updated_at WHERE status='indexed'` |
| `revision_of` | `TEXT`（可空） | 修订行指向存活行 |

`ensure_schema()` 中**不修改** `DDL_STATEMENTS`（001 逐字一致）；`EXPECTED_COLUMNS["documents"]` 追加这 6 列，使缺列在启动期被 `missing_columns` 拦截（`sqlite_repo.py:228-235` 既有逻辑）。

**3) 索引**

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_folders_name ON folders(project_id, parent_id, name_key);
CREATE INDEX        IF NOT EXISTS idx_folders_parent ON folders(project_id, parent_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_name
    ON documents(project_id, folder_id, name_key) WHERE name_key <> '' AND revision_of IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_revision ON documents(revision_of) WHERE revision_of IS NOT NULL;
CREATE INDEX        IF NOT EXISTS idx_documents_folder ON documents(project_id, folder_id);
CREATE INDEX        IF NOT EXISTS idx_batch_items_state ON upload_batch_items(batch_id, state);
CREATE INDEX        IF NOT EXISTS idx_upload_batches_expiry ON upload_batches(expires_at);
```

**4) `ensure_schema()` 执行顺序（必须按此序，否则唯一索引创建会失败）**
1. 既有：PRAGMA → `DDL_STATEMENTS` → REV-18 补列/DDL/`PROJECT_KB_REBIND_STATEMENTS` → LLM Key → 账户 → 审计。
2. `_ensure_document_tree_columns(connection)`：包在 `BEGIN IMMEDIATE`；缺列逐个 `ALTER TABLE documents ADD COLUMN …`；捕获 `OperationalError: duplicate column name`（`ib-web` 的 `ExecStartPre` 与 `ib-worker` 启动都会调 `ensure_schema`，防并发补列竞态）。
3. `FOLDER_TREE_DDL_STATEMENTS`（新表 + 非唯一索引）。
4. `FOLDER_TREE_BACKFILL_STATEMENTS`（幂等 SQL：`UPDATE documents SET uploaded_at = created_at WHERE uploaded_at = ''`；`UPDATE documents SET indexed_at = updated_at WHERE status = 'indexed' AND indexed_at IS NULL`）。
5. `backfill_name_keys(connection)`（Python，幂等：只处理 `name_key = '' AND revision_of IS NULL` 的行）：按 `(project_id, folder_id)` 分组、`created_at, doc_id` 升序，计算 `name_key_of(doc_name)`；组内重复者追加 `\x1f<doc_id>`，使历史重名行**显示名不变**（AC-017-01）。单事务提交。
6. `FOLDER_TREE_UNIQUE_INDEX_STATEMENTS`（唯一索引，必须在第 5 步之后）。

**可逆性与回滚说明**（写入 007 头注释）：
- 迁移幂等，可重放；对既有数据**只补列与回填标量，不改不删**。
- 代码回退（`git revert` → 目标机 pull + 重启）：旧代码按命名列 `SELECT`/显式列 `INSERT`，忽略新列，可运行。**回退前**须先清空在途修订行（否则旧代码会把它们当普通文档展示并重复索引）：运维先对每个有 `update_state` 的文件调用 `DELETE /api/files/{doc_id}/revision`，或在回退后手工 `DELETE FROM documents WHERE revision_of IS NOT NULL`（先删向量/blob，见 `delete_document`）。回退后子目录内的文件会在旧的扁平列表中全部可见，同名文件会并存（旧代码无同名约束）。
- 表/列/索引回滚（**`MANUAL_ROLLBACK_REQUIRED`**，仅在确需撤销新结构时）：`DROP TABLE doc_purge_queue; DROP TABLE upload_batch_items; DROP TABLE upload_batches; DROP TABLE folders;`；先 `DROP INDEX` 掉 `uq_documents_name/uq_documents_revision/idx_documents_folder`，再 `ALTER TABLE documents DROP COLUMN …`（需 SQLite ≥3.35；低版本需重建表）。回滚会丢失目录结构与时间语义列，须先备份台账文件 `/var/lib/intelligentbase/…`。
- **数据风险**：① `indexed_at` 回填为近似值（A-07）；② 历史重名行仅 `name_key` 去重，不改名；③ 迁移期间 `ib-web` 重启的 `ExecStartPre` 持有写锁时间极短（仅补列与标量回填，行数 = 现有文档数，量级 ≤ 万）`[ESTIMATE]`；④ 若 `ensure_schema` 在两进程并发启动时竞争，`BEGIN IMMEDIATE` + 忽略重复列保证幂等。
- **注意**：`007_folder_tree.sql` 作为"可审阅快照"含 DDL、SQL 回填与唯一索引，**不含** Python 的 `name_key` 回填；因此部署路径是 `ensure_schema`（自动），手工 `sqlite3 < 007` 仅在新库或已无历史数据时等价（头注释写明）。

## 受影响的运行单元 / 构建

按画像 P7 与 `.claude/skills/ib-prod-deploy/SKILL.md` §6"什么改动重启什么"：

| 改动 | 受影响单元 | 动作 | 执行人 |
|---|---|---|---|
| `src/frontend/**`（MOD-013/014） | 前端静态产物 | 目标机 `npm run build` + 拷贝 web root；**不重启任何服务** | devops（E2 授权后） |
| `src/ibweb/**`（MOD-010/012）、`src/ib/library/**`、`src/ib/ledger/**`、`src/ib/retrieval/**`、`src/ib/streaming/**`、`src/ib/core/**`、`src/ib/lifecycle/**`、`src/ib/rebuild/**`、`src/ib/config/**`（Web 路径与检索） | **`ib-web`** | `git pull` + `sudo -n systemctl restart ib-web`；迁移 007 由 `ExecStartPre … --ensure-schema` **随重启自动幂等应用** | devops |
| `src/ibweb/worker.py`（MOD-011）、入库/晋升/清理链路（`ib/lifecycle`、`ib/ledger`、`ib/rebuild`） | **`ib-worker`** | `sudo -n systemctl restart ib-worker`（**先于或紧随 ib-web**：ib-worker 启动也会调 `ensure_schema`；`ib-worker.service` 已 `After=ib-web.service`） | devops |
| `src/deploy/migrations/007_folder_tree.sql`（新文件） | 台账 schema | 随 `ib-web` 重启自动应用，无需单独动作 | — |
| 新配置键（MOD-009，可选） | `ib-web.env` | 如需调整默认值（尤其总大小上限，A-01）：**用户**编辑 `/etc/intelligentbase/ib-web.env`（0600，不得回显）并重启 `ib-web`；默认值无需任何 env 改动 | 用户 |
| `ib-embed`、`qdrant` | — | **不受影响** | — |
| nginx（`src/deploy/nginx/*`） | — | **不变更**：`client_max_body_size 64m` 保持，逐文件上传 ≤50MB 满足；因此**无需用户 reload nginx** | — |
| systemd unit | — | **不变更**（不新增单元、不改多实例），无需 `daemon-reload` | — |

**发布顺序建议**（供 devops）：① 前端可任意时刻先后发布，但旧前端调用旧端点仍兼容（`/api/files*` 受控修改见 IFC-013）；② 后端先重启 `ib-web`（迁移生效）再重启 `ib-worker`；③ 部署后验证：`systemctl is-active ib-web ib-worker ib-embed`；`journalctl -u ib-web --since <真实启动时刻>` 无 `ensure_schema` 错误；`sqlite3` 查询 `PRAGMA table_info(documents)` 含 6 个新列、`folders` 表存在；线上代码版本判据按 SKILL.md §7.1（目标机 HEAD + 源文件 mtime 早于 ActiveEnterTimestamp，不得用 `.pyc`）。
