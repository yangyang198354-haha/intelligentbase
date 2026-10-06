-- ---------------------------------------------------------------------------
-- @module MOD-IB-25 / MOD-IB-11
-- @implements 手写 scoped 迁移（003 / IFC-IB-330）：账户与会话表（R13 / REQ-FUNC-IB-30）
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::account_ddl_script()` **原样摘录**（单源不变；本文件是
-- 「可人工审阅的增量快照」）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import account_ddl_script;print(account_ddl_script())"
--
-- 为什么不改 001 / 002 而是新增 003：
--   001（R1 DDL 快照）与 002（chunk_image 增量）的契约都是「与生成时逐字一致」；
--   R13 增量另立 003，使**升级路径显式可审计**（延续 schema.py docstring 的既定纪律）。
--   `002` 已被 `chunk_image` 占用，故本轮取 `003`。
--
-- 应用方式（正常部署**无需手工执行**）：
--   1) 自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--      其中 `ensure_schema()` 会幂等建好本表（对既有 R1/R2 库同样生效）。
--   2) 手工（核对时）：sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 003_accounts.sql
--
-- 语义要点：
--   * **纯追加**：只新增 `users` / `sessions` 两张表 + 索引，**不动任何既有表 / 列**。
--   * **回滚策略 = 代码回滚**：旧代码不引用新表，可直接启动（无需破坏性 DDL）。
--     仅在**未投产**且确需清空时方可 `DROP TABLE users; DROP TABLE sessions;`（注明**丢数据**）。
--   * **幂等**：全部 `CREATE ... IF NOT EXISTS`，重复重放无副作用（B20）。
--   * **凭据摘要**：`users.password_hash` 只承载 bcrypt 摘要；`sessions.token_digest`
--     只承载 sha256 摘要 —— **绝不落任何口令 / 令牌原文**（C-IB-09 / ADR-19）。
--   * `users.role='admin'` 时 `project_id IS NULL`（全局账户，ADR-21）；该约束在存储层
--     以 CHECK 表达，杜绝「没有项目的 ops 账户」这一越权温床。
-- ---------------------------------------------------------------------------

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
);
CREATE INDEX IF NOT EXISTS idx_users_project ON users(project_id);

CREATE TABLE IF NOT EXISTS sessions (
    token_digest  TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    project_id    TEXT,
    issued_at     TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    last_seen_at  TEXT NOT NULL,
    revoked_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
