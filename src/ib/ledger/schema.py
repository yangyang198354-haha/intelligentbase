"""
@module MOD-IB-11（schema）
@implements IFC-IB-120~131 的持久化基座（表结构 / 索引 / PRAGMA）
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

#: 连接级 PRAGMA（每次开连接都必须执行 —— `busy_timeout` 与 `foreign_keys` 是**连接级**的）。
PRAGMA_ON_CONNECT = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA busy_timeout=5000",
    "PRAGMA foreign_keys=ON",
)

#: 每个新连接都会执行的初始化语句（含连接级 PRAGMA）。
PRAGMA_STATEMENTS = PRAGMA_ON_CONNECT

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

#: 期望存在的列（用于启动期/自测期的一致性校验，防止「老库缺列」导致的运行期 TypeError）。
EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "projects": (
        "project_id",
        "name",
        "active_collection_version",
        "embedding_model_id",
        "dim",
        "created_at",
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


def ensure_schema(connection) -> None:
    """幂等建表 + 开 PRAGMA（运行期自愈）。

    刻意**不**引入版本号表：DDL 全部为 `IF NOT EXISTS`，且新增列通过显式 ALTER 迁移脚本
    （`src/deploy/migrations/`）落地 —— 基座的表结构变更应当**显式且可审计**，
    而不是靠框架自动 diff。启动期由 `ibweb` 调用一次即可。

    **R13**：同时幂等创建账户 / 会话表（`users` / `sessions`）—— 账户体系内建，
    不新增 systemd 单元（DR-09 / ADR-18），故与台账共用同一次 `--ensure-schema`。
    """
    cursor = connection.cursor()
    try:
        for statement in PRAGMA_STATEMENTS:
            cursor.execute(statement)
        for statement in DDL_STATEMENTS:
            cursor.execute(statement)
        for statement in ACCOUNT_DDL_STATEMENTS:
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
