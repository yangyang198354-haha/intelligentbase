"""
@module MOD-IB-11（schema）
@implements IFC-IB-120~131 的持久化基座（表结构 / 索引 / PRAGMA）
            IFC-IB-358（REV-16-4 配置审计表 DDL：`config_audit`）
@depends (none)
@author software-developer

台账 DDL 的**单一真源**（module_design.md §6；ADR-10；tech_stack §3）。

**为什么手写 SQL 而不走 Django ORM / makemigrations**（tech_stack §3「坑」、CLAUDE.md 开发约定 1）：
  * 本项目是 Django 收窄配置（无 auth/admin/ORM 用法），台账是**基座自有存储**，
    与 Django app 的迁移体系无关；
  * 若引入 Django 模型，会因「迁移漂移」在跨版本升级时产生不可预期的表结构变更；
  * 手写 DDL + 幂等 `CREATE TABLE IF NOT EXISTS` 使**升级路径显式可审计**。

**PRAGMA 三条是硬性要求**（tech_stack §3 / CLAUDE.md 生产教训）：
  * `journal_mode=WAL` —— 允许「一写多读」并发（worker 写入时 HTTP 读不被阻塞）；
  * `busy_timeout=5000` —— 写锁竞争时**等待重试而非立即 `SQLITE_BUSY`**（默认 0 会让
    并发认领随机失败，表现为「任务凭空消失」）；
  * `foreign_keys=ON` —— 父子表一致性由 SQLite 强制（避免 chunk 悬挂）。

**时间戳一律为 `YYYY-MM-DDTHH:MM:SSZ` 定长 UTC 字符串**：租约过期判定用字符串比较，
定长是「字典序 == 时间序」的前提（见 `ib.context.utc_now_iso`）。
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# PRAGMA
# --------------------------------------------------------------------------- #

#: 数据库级 PRAGMA（持久化在 DB 文件头、全库共享 —— 只需在库初始化时执行一次）。
#: `journal_mode=WAL` 是**数据库级**而非连接级：一旦 DB 已切到 WAL，每条新连接自动继承，
#: 重跑只会冗余地去抢排它锁（这正是「worker 首请求 30~90s 阻塞」的根因，见部署报告）。
PRAGMA_DB_LEVEL = (
    "PRAGMA journal_mode=WAL",
)

#: 连接级 PRAGMA（每条新连接都必须执行 —— `synchronous` / `busy_timeout` / `foreign_keys`
#: 都是**连接级**的，新连接不继承）。
PRAGMA_ON_CONNECT = (
    "PRAGMA synchronous=NORMAL",
    "PRAGMA busy_timeout=5000",
    "PRAGMA foreign_keys=ON",
)

#: `ensure_schema` 建表时执行的语句：数据库级 PRAGMA（一次）+ 连接级 PRAGMA + DDL。
#: `ensure_schema` 由 ibweb 在启动期调用一次，故 `journal_mode` 只在这里落地一次，
#: 不再每条新连接重跑。
PRAGMA_STATEMENTS = PRAGMA_DB_LEVEL + PRAGMA_ON_CONNECT

# --------------------------------------------------------------------------- #
# DDL（幂等）
# --------------------------------------------------------------------------- #

DDL_STATEMENTS: tuple[str, ...] = (
    # 项目：`active_collection_version` 是 ADR-05 的**单值切换点**（原子切换的载体）。
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_id                TEXT PRIMARY KEY,
        name                      TEXT NOT NULL,
        active_collection_version TEXT NOT NULL,
        embedding_model_id        TEXT NOT NULL,
        dim                       INTEGER NOT NULL,
        created_at                TEXT NOT NULL
    )
    """,
    # 知识库：`assert_kb_in_project` 的判定依据（→ HTTP 403）。
    """
    CREATE TABLE IF NOT EXISTS kbs (
        kb_id      TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
        name       TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_kbs_project ON kbs(project_id)
    """,
    # 文档：状态机 + 租约 + 索引版本三元信息都在这一张表。
    """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id                      TEXT PRIMARY KEY,
        project_id                  TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
        kb_id                       TEXT NOT NULL,
        doc_name                    TEXT NOT NULL,
        ext                         TEXT NOT NULL,
        size_bytes                  INTEGER NOT NULL,
        content_sha256              TEXT NOT NULL,
        blob_ref                    TEXT,
        status                      TEXT NOT NULL,
        error_code                  TEXT,
        chunk_count                 INTEGER NOT NULL DEFAULT 0,
        indexed_collection_version  TEXT,
        target_collection_version   TEXT,
        lease_owner                 TEXT,
        lease_expires_at            TEXT,
        created_at                  TEXT NOT NULL,
        updated_at                  TEXT NOT NULL,
        CHECK (status IN ('pending', 'parsing', 'indexed', 'failed'))
    )
    """,
    # 认领扫描的支撑索引（status + 租约到期）—— 按 created_at 先进先出。
    """
    CREATE INDEX IF NOT EXISTS idx_documents_claim
        ON documents(status, lease_expires_at, created_at)
    """,
    # 列表/计数按 (project_id, kb_id, status) 过滤。
    """
    CREATE INDEX IF NOT EXISTS idx_documents_scope
        ON documents(project_id, kb_id, status)
    """,
    # 块：`chunk_id` = `doc_id#chunk_index`（§6.2 幂等键），重跑覆盖而非重复。
    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id         TEXT PRIMARY KEY,
        doc_id           TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
        project_id       TEXT NOT NULL,
        kb_id            TEXT NOT NULL,
        chunk_index      INTEGER NOT NULL,
        content_hash     TEXT NOT NULL,
        locator          TEXT NOT NULL,
        source_kind      TEXT NOT NULL,
        page_or_section  TEXT NOT NULL,
        indexed_model    TEXT NOT NULL,
        indexed_dim      INTEGER NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project_id, kb_id)
    """,
    # 页面图关联（R2 / M-02 / IFC-IB-278~279）：**一张独立关联表**，不改 `chunks` 任何列。
    #
    # 幂等键 = `image_row_id` = `(project_id, kb_id, doc_id, page_or_section, image_id)`
    # 的定长拼接（与 `chunks.chunk_id` 的做法同构：把复合键物化成主键，重跑即覆盖）。
    # `ON DELETE CASCADE` 使 IFC-IB-281 的「删除零改动」成立 —— `mark_deleted` 只删
    # `documents` 行，关联行由 SQLite 在同一事务内级联清除，故 `DeleteReport` 三个计数
    # 的语义**一字不改**。
    # `blob_ref` 可空：OCR 后即弃的历史文档其图字节不可得，此时仍登记关联（供审计），
    # 但取图端点会返回 404（§7.4 降级行）。
    """
    CREATE TABLE IF NOT EXISTS chunk_image (
        image_row_id     TEXT PRIMARY KEY,
        project_id       TEXT NOT NULL,
        kb_id            TEXT NOT NULL,
        doc_id           TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
        page_or_section  TEXT NOT NULL,
        image_id         TEXT NOT NULL,
        source_kind      TEXT NOT NULL,
        locator          TEXT NOT NULL,
        blob_ref         TEXT,
        doc_name         TEXT NOT NULL,
        created_at       TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunk_image_doc ON chunk_image(doc_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunk_image_scope ON chunk_image(project_id, kb_id)
    """,
    # 重建任务：`(project_id, to_version)` 唯一 —— 同一目标版本不重复建任务（§6.2）。
    """
    CREATE TABLE IF NOT EXISTS rebuild_jobs (
        job_id           TEXT PRIMARY KEY,
        project_id       TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
        from_version     TEXT NOT NULL,
        to_version       TEXT NOT NULL,
        target_collection TEXT NOT NULL,
        doc_count        INTEGER NOT NULL,
        state            TEXT NOT NULL,
        lease_owner      TEXT,
        lease_expires_at TEXT,
        created_at       TEXT NOT NULL,
        updated_at       TEXT NOT NULL,
        UNIQUE (project_id, to_version)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_rebuild_jobs_state
        ON rebuild_jobs(state, lease_expires_at)
    """,
)

# --------------------------------------------------------------------------- #
# R13 账户 / 会话 DDL（IFC-IB-313；单源 = 迁移 003_accounts.sql）
# --------------------------------------------------------------------------- #
#
# 为什么**不**加外键到 `projects`：`admin` 是**全局账户**（`project_id IS NULL`），
# 不对应任何项目；`ops` 的 `project_id` 只作**归属标签**（隔离由中间件 + 策略保证），
# 且本表不参与「删除项目即级联清账户」的语义（项目登记在配置层）。
# `sessions.user_id` 亦**不加外键**：停用 / 改密时的批量撤销由应用层显式调用
# （IFC-IB-321 / IFC-IB-319），保留「先撤销会话、再改账户状态」的可审计顺序。
#
# 少量 CHECK 是**新增表自带**的完整性约束（不改任何既有表）：
#   * `role` / `status` 取值域在**存储层**再兜一道 —— 与 `documents.status` 的既有做法一致；
#   * `must_change_password` 限定 0/1，避免「真值被写成任意整数」；
#   * `role='admin' OR project_id IS NOT NULL` 使 ADR-21「只有 admin 是全局」成为
#     表结构层面的事实，杜绝「一个没有项目的 ops 账户」这种越权温床。

ACCOUNT_DDL_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id              TEXT PRIMARY KEY,
        username             TEXT NOT NULL UNIQUE,
        password_hash        TEXT NOT NULL,
        role                 TEXT NOT NULL,
        project_id           TEXT,
        status               TEXT NOT NULL,
        must_change_password INTEGER NOT NULL,
        failed_login_count   INTEGER NOT NULL DEFAULT 0,
        locked_until         TEXT,
        created_at           TEXT NOT NULL,
        updated_at           TEXT NOT NULL,
        CHECK (role IN ('admin', 'ops')),
        CHECK (status IN ('active', 'disabled')),
        CHECK (must_change_password IN (0, 1)),
        CHECK (role = 'admin' OR project_id IS NOT NULL)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_users_project ON users(project_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        token_digest  TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        project_id    TEXT,
        issued_at     TEXT NOT NULL,
        expires_at    TEXT NOT NULL,
        last_seen_at  TEXT NOT NULL,
        revoked_at    TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)
    """,
)

#: 账户 / 会话表的期望列（与 `missing_account_columns` 配套）。
ACCOUNT_EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "users": (
        "user_id",
        "username",
        "password_hash",
        "role",
        "project_id",
        "status",
        "must_change_password",
        "failed_login_count",
        "locked_until",
        "created_at",
        "updated_at",
    ),
    "sessions": (
        "token_digest",
        "user_id",
        "project_id",
        "issued_at",
        "expires_at",
        "last_seen_at",
        "revoked_at",
    ),
}

# --------------------------------------------------------------------------- #
# REV-16-4 配置审计 DDL（IFC-IB-358；ADR-34；单源 = 迁移 004_config_audit.sql）
# --------------------------------------------------------------------------- #
#
# **只读审计，不是第二真源**（ADR-34）：本表只承载「谁在何时对哪个项目的配置做了
# 何种动作、结果如何」的追加式记录，**任何**上层模块**不得**从这里回读配置来驱动行为
# —— 配置真源恒为定义文档（`IB_DEFINITION_DOC_PATH` 指向的文件 / 内存种子）与提示词目录。
#
# 与账户台账「逻辑分区」：本表**独立成块、独立迁移文件**（module_design §3 MOD-IB-11
# 明确建议「审计表与文档/账户台账逻辑分区（表名前缀/仓库内分文件）」），与
# `users` / `sessions` 一样**不加外键到 `projects`**（审计记录须在项目被删后仍可考）。
#
# 三条列设计的纪律（SC-3 / ADR-34）：
#   * `changed_field_names` 存 **JSON 数组**，且**只含字段名**（如
#     `["route.tau", "tool_grants[search].param_values"]`），**永不**含字段值；
#   * `detail_code` **只含** 字段名 / 错误码（如 `tool_param_unknown`），**永不**含值；
#   * `result` 用 CHECK 限定取值域 —— 在**存储层**再兜一道（与 `documents.status` /
#     `users.role` 的既有做法一致），杜绝「带病继续」之类非法结果被写进去。

CONFIG_AUDIT_DDL_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS config_audit (
        entry_id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp           TEXT NOT NULL,
        project             TEXT NOT NULL,
        actor               TEXT NOT NULL,
        action              TEXT NOT NULL,
        changed_field_names TEXT NOT NULL,
        result              TEXT NOT NULL,
        detail_code         TEXT,
        CHECK (result IN ('saved', 'rejected'))
    )
    """,
    # 按项目回放的支撑索引：`list_by_project` 恒按 `(project, entry_id)` 升序稳定分页。
    """
    CREATE INDEX IF NOT EXISTS idx_config_audit_project
        ON config_audit(project, entry_id)
    """,
)

#: 配置审计表的期望列（与 `missing_config_audit_columns` 配套）。
CONFIG_AUDIT_EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "config_audit": (
        "entry_id",
        "timestamp",
        "project",
        "actor",
        "action",
        "changed_field_names",
        "result",
        "detail_code",
    ),
}


# --------------------------------------------------------------------------- #
# REV-18 项目注册表 / LLM Key DDL（IFC-IB-370 / 371 / 377；ADR-37 / ADR-38）
# --------------------------------------------------------------------------- #
#
# **同一 SQLite 台账、同一手写 scoped 迁移机制**（ADR-18 / ADR-26 复用）。
#
# `projects` 表**复用**既有物理表（ADR-37 Option B：「同一 SQLite 台账的 projects 表
# 适配器」）。既有 6 列（`project_id` / `name` / `active_collection_version` /
# `embedding_model_id` / `dim` / `created_at`）承载**台账侧**信息；REV-18 **前向追加**
# 两列 `status` / `updated_at` 承载**注册表侧**软删 / 停用语义（用户裁决 2026-10-07：
# 删项目 = 软删 / 停用，数据保留、可恢复）。因此注册表适配器读的是**同一行的子集投影**
# （IFC-IB-367 的 5 字段），而 `005_projects.sql` 是这一前向扩展的**可审阅快照**。
#
# **为什么用 `ALTER TABLE ... ADD COLUMN` 而非改 `CREATE`**：`CREATE TABLE IF NOT
# EXISTS` 对既有库是 no-op，改其列清单不会给老库补列。SQLite **不支持**
# `ADD COLUMN IF NOT EXISTS`，故由 `ensure_schema()` 以 `PRAGMA table_info` 探测后
# 幂等补列（`_ensure_project_registry_columns`）—— 这是「显式且可审计」的既有纪律
# 的延续（schema.py docstring）。

#: `projects` 表 REV-18 **前向追加**的两列（注册表侧）：`status`（软删 / 停用语义）
#: 与 `updated_at`（编辑时间戳）。`DEFAULT` 使既有行与 `upsert_project` 的旧 INSERT
#: 在补列后仍满足 `NOT NULL`。
_PROJECT_REGISTRY_ADDED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("status", "TEXT NOT NULL DEFAULT 'active'"),
    ("updated_at", "TEXT NOT NULL DEFAULT ''"),
)

PROJECT_REGISTRY_DDL_STATEMENTS: tuple[str, ...] = (
    # `projects` 表**最终形态**（对新库一步到位；对老库由幂等补列对齐）。
    # 既有 6 列在前（与 001 快照逐字一致），REV-18 两列在后 —— 列序变化对既有
    # 命名式 SELECT 无影响（无 `SELECT *`）。
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_id                TEXT PRIMARY KEY,
        name                      TEXT NOT NULL,
        active_collection_version TEXT NOT NULL,
        embedding_model_id        TEXT NOT NULL,
        dim                       INTEGER NOT NULL,
        created_at                TEXT NOT NULL,
        status                    TEXT NOT NULL DEFAULT 'active',
        updated_at                TEXT NOT NULL DEFAULT ''
    )
    """,
    # 注册表枚举（活动项目）的支撑索引。
    """
    CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)
    """,
)

#: REV-18（IFC-IB-375 / ADR-41）：项目域资料上传以 `kb_id ≡ project_id` 推导 kb，故
#: **一次性、幂等、前向**地把「(a) 为每个项目登记 `kb_id == project_id` 的知识库行」与
#: 「(b) 既有落在 `kb_default` 的文档 / 块 / 页面图关联**改隶到归属项目 KB**」落地。
#: 全部语句重放无副作用（`WHERE NOT EXISTS` / `WHERE kb_id='kb_default'` 收敛）。
PROJECT_KB_REBIND_STATEMENTS: tuple[str, ...] = (
    """
    INSERT INTO kbs (kb_id, project_id, name, created_at)
    SELECT p.project_id, p.project_id, p.name, p.created_at
    FROM projects p
    WHERE NOT EXISTS (SELECT 1 FROM kbs k WHERE k.kb_id = p.project_id)
    """,
    """
    UPDATE documents SET kb_id = project_id WHERE kb_id = 'kb_default'
    """,
    """
    UPDATE chunks SET kb_id = project_id WHERE kb_id = 'kb_default'
    """,
    """
    UPDATE chunk_image SET kb_id = project_id WHERE kb_id = 'kb_default'
    """,
)

#: `llm_key` 单行表（以结构保证全局唯一；OOS-18 为扩展点预留）。
#: **单行**由 `CHECK (id = 1)` 表达 —— 全局唯一 Key 是**表结构层面的事实**。
LLM_KEY_DDL_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS llm_key (
        id         INTEGER PRIMARY KEY CHECK (id = 1),
        secret     TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
)

#: 项目注册表侧期望列（与 `missing_project_registry_columns` 配套）。
PROJECT_REGISTRY_EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "projects": (
        "project_id",
        "name",
        "active_collection_version",
        "embedding_model_id",
        "dim",
        "created_at",
        "status",
        "updated_at",
    ),
}

#: LLM Key 表期望列（与 `missing_llm_key_columns` 配套）。
LLM_KEY_EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "llm_key": ("id", "secret", "updated_at"),
}


#: 期望存在的列（用于启动期/自测期的一致性校验，防止「老库缺列」导致的运行期 TypeError）。
EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "projects": (
        "project_id",
        "name",
        "active_collection_version",
        "embedding_model_id",
        "dim",
        "created_at",
        "status",
        "updated_at",
    ),
    "kbs": ("kb_id", "project_id", "name", "created_at"),
    "documents": (
        "doc_id",
        "project_id",
        "kb_id",
        "doc_name",
        "ext",
        "size_bytes",
        "content_sha256",
        "blob_ref",
        "status",
        "error_code",
        "chunk_count",
        "indexed_collection_version",
        "target_collection_version",
        "lease_owner",
        "lease_expires_at",
        "created_at",
        "updated_at",
    ),
    "chunks": (
        "chunk_id",
        "doc_id",
        "project_id",
        "kb_id",
        "chunk_index",
        "content_hash",
        "locator",
        "source_kind",
        "page_or_section",
        "indexed_model",
        "indexed_dim",
    ),
    # R2（M-02）：页面图关联表。
    "chunk_image": (
        "image_row_id",
        "project_id",
        "kb_id",
        "doc_id",
        "page_or_section",
        "image_id",
        "source_kind",
        "locator",
        "blob_ref",
        "doc_name",
        "created_at",
    ),
    "rebuild_jobs": (
        "job_id",
        "project_id",
        "from_version",
        "to_version",
        "target_collection",
        "doc_count",
        "state",
        "lease_owner",
        "lease_expires_at",
        "created_at",
        "updated_at",
    ),
}


def ddl_script() -> str:
    """把 DDL 拼为单条脚本（供 `001_ledger_init.sql` 交付物与手工建库使用）。"""
    return ";\n".join(statement.strip() for statement in DDL_STATEMENTS) + ";\n"


def account_ddl_script() -> str:
    """把账户 / 会话 DDL 拼为单条脚本（供 `003_accounts.sql` 交付物与手工建库使用）。"""
    return ";\n".join(statement.strip() for statement in ACCOUNT_DDL_STATEMENTS) + ";\n"


def config_audit_ddl_script() -> str:
    """把配置审计 DDL 拼为单条脚本（供 `004_config_audit.sql` 交付物与手工建库使用）。"""
    return ";\n".join(statement.strip() for statement in CONFIG_AUDIT_DDL_STATEMENTS) + ";\n"


def project_registry_ddl_script() -> str:
    """把项目注册表 DDL + `kb_default` 数据迁移拼为单条脚本（供 `005_projects.sql` 交付物）。"""
    statements = PROJECT_REGISTRY_DDL_STATEMENTS + PROJECT_KB_REBIND_STATEMENTS
    return ";\n".join(statement.strip() for statement in statements) + ";\n"


def llm_key_ddl_script() -> str:
    """把 LLM Key DDL 拼为单条脚本（供 `006_llm_key.sql` 交付物与手工建库使用）。"""
    return ";\n".join(statement.strip() for statement in LLM_KEY_DDL_STATEMENTS) + ";\n"


def _ensure_project_registry_columns(connection) -> None:
    """**幂等**为既有 `projects` 表补 REV-18 两列（`status` / `updated_at`）。

    SQLite 不支持 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，故先以 `PRAGMA table_info`
    探测缺列，再逐列 `ALTER TABLE`。对**新库**（`CREATE` 已含两列）本函数为 no-op；
    对**老库**（仅 6 列）补列且既有行取 `DEFAULT`，满足 `NOT NULL`。

    `IFC-IB-377` 的「前向、幂等」即由此落实：重复重放无副作用（B21）。
    """
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA table_info(projects)")
        actual = {row[1] for row in cursor.fetchall()}
        if not actual:
            # 表尚不存在：`CREATE TABLE IF NOT EXISTS` 会以含两列的最终形态建表，无需补列。
            return
        for column, column_ddl in _PROJECT_REGISTRY_ADDED_COLUMNS:
            if column not in actual:
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {column} {column_ddl}")
    finally:
        cursor.close()


def ensure_schema(connection) -> None:
    """幂等建表 + 开 PRAGMA（运行期自愈）。

    刻意**不**引入版本号表：DDL 全部为 `IF NOT EXISTS`，且新增列通过显式 ALTER 迁移脚本
    （`src/deploy/migrations/`）落地 —— 基座的表结构变更应当**显式且可审计**，
    而不是靠框架自动 diff。启动期由 `ibweb` 调用一次即可。

    **R13**：同时幂等创建账户 / 会话表（`users` / `sessions`）—— 账户体系内建，
    不新增 systemd 单元（DR-09 / ADR-18），故与台账共用同一次 `--ensure-schema`。

    **REV-16-4**：再幂等创建配置审计表（`config_audit`）—— 审计与台账同一 SQLite
    账本（ADR-34 未引入第二个存储后端），同样复用这一次 `--ensure-schema`。

    **REV-18**：幂等创建 / 对齐项目注册表（`projects` 表前向追加 `status` / `updated_at`
    两列；ADR-37）与 LLM Key 单行表（`llm_key`；ADR-38）—— 与台账**同一** SQLite
    账本、同一手写 scoped 迁移机制（ADR-18 / ADR-26 复用）。
    """
    cursor = connection.cursor()
    try:
        for statement in PRAGMA_STATEMENTS:
            cursor.execute(statement)
        for statement in DDL_STATEMENTS:
            cursor.execute(statement)
        # REV-18：老库补列须在 `CREATE TABLE IF NOT EXISTS` 之后（新库由 CREATE 一步到位）。
        _ensure_project_registry_columns(connection)
        for statement in PROJECT_REGISTRY_DDL_STATEMENTS:
            cursor.execute(statement)
        for statement in PROJECT_KB_REBIND_STATEMENTS:
            cursor.execute(statement)
        for statement in LLM_KEY_DDL_STATEMENTS:
            cursor.execute(statement)
        for statement in ACCOUNT_DDL_STATEMENTS:
            cursor.execute(statement)
        for statement in CONFIG_AUDIT_DDL_STATEMENTS:
            cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()


def missing_columns(connection) -> dict[str, list[str]]:
    """返回缺失列（表 -> 列名列表）。空字典表示结构完整。"""
    return _missing(connection, EXPECTED_COLUMNS)


def missing_account_columns(connection) -> dict[str, list[str]]:
    """账户 / 会话表的缺失列（R13，IFC-IB-313）。空字典表示结构完整。"""
    return _missing(connection, ACCOUNT_EXPECTED_COLUMNS)


def missing_config_audit_columns(connection) -> dict[str, list[str]]:
    """配置审计表的缺失列（REV-16-4，IFC-IB-358）。空字典表示结构完整。"""
    return _missing(connection, CONFIG_AUDIT_EXPECTED_COLUMNS)


def missing_project_registry_columns(connection) -> dict[str, list[str]]:
    """项目注册表侧期望列的缺失检查（REV-18，IFC-IB-370）。空字典表示结构完整。"""
    return _missing(connection, PROJECT_REGISTRY_EXPECTED_COLUMNS)


def missing_llm_key_columns(connection) -> dict[str, list[str]]:
    """LLM Key 表期望列的缺失检查（REV-18，IFC-IB-371）。空字典表示结构完整。"""
    return _missing(connection, LLM_KEY_EXPECTED_COLUMNS)


def _missing(connection, expected_tables: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cursor = connection.cursor()
    try:
        for table, expected in expected_tables.items():
            cursor.execute(f"PRAGMA table_info({table})")
            actual = {row[1] for row in cursor.fetchall()}
            if not actual:
                out[table] = list(expected)
                continue
            missing = [column for column in expected if column not in actual]
            if missing:
                out[table] = missing
    finally:
        cursor.close()
    return out
