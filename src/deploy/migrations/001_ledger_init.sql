-- ---------------------------------------------------------------------------
-- @module MOD-IB-25 / MOD-IB-11
-- @implements 手写 scoped 迁移（001）：台账 SQLite schema 初始化
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::ddl_script()` **原样生成**（单一真源）。
-- 生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import ddl_script;print(ddl_script())"
--
-- 【R2 范围声明】本文件是 **R1 的 DDL 快照**；R2 新增的页面图关联表落在
-- `002_chunk_image.sql`（增量文件，不回头改历史快照 —— 结构变更须显式且可审计）。
-- 故「本文件与 `ddl_script()` 逐字一致」这一契约**仅在 R1 时点成立**；
-- 运行期结构以 `ddl_script()`（= 001 + 002）为唯一真源。
--
-- 为什么不走 Django migrations：
--   台账是**自管 SQL** 的 SQLite（ADR-07-R1），不经 Django ORM。用 `makemigrations`
--   生成的是 ORM 模型的迁移产物，与真实的 DDL 必然漂移（本项目 FreeArk 已踩过
--   「迁移漂移」的坑：makemigrations 全产物里混入了与模型状态不一致的历史迁移）。
--   本文件与 `ddl_script()` 一起评审，二者必须逐字一致。
--
-- 应用方式（systemd 单元 `ib-web.service` 的 ExecStartPre 会调用 `ensure_schema()`，
-- 故正常部署**无需手工执行**本文件；它存在的意义是「可人工审阅的 DDL 快照」）：
--   sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 001_ledger_init.sql
--
-- 注意：`ensure_schema()` 在连接时还会执行 WAL / busy_timeout 等 PRAGMA
-- （见 `ib/ledger/sqlite_repo.py::_connect`）—— PRAGMA 是**连接级**设置，
-- 与 schema 无关，因此不出现在本 DDL 中。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS projects (
        project_id                TEXT PRIMARY KEY,
        name                      TEXT NOT NULL,
        active_collection_version TEXT NOT NULL,
        embedding_model_id        TEXT NOT NULL,
        dim                       INTEGER NOT NULL,
        created_at                TEXT NOT NULL
    );
CREATE TABLE IF NOT EXISTS kbs (
        kb_id      TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
        name       TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
CREATE INDEX IF NOT EXISTS idx_kbs_project ON kbs(project_id);
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
    );
CREATE INDEX IF NOT EXISTS idx_documents_claim
        ON documents(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_documents_scope
        ON documents(project_id, kb_id, status);
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
    );
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project_id, kb_id);
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
    );
CREATE INDEX IF NOT EXISTS idx_rebuild_jobs_state
        ON rebuild_jobs(state, lease_expires_at);
