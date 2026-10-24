-- ---------------------------------------------------------------------------
-- MOD-001 / 手写 scoped 迁移（007）：资料库文件夹树（folders / upload_batches / upload_batch_items /
-- doc_purge_queue 四张新表 + documents 新列的索引与标量回填）
--
-- 由 `ib/ledger/schema.py::folder_tree_ddl_script()` **原样摘录**（单源；本文件是可审阅快照）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import folder_tree_ddl_script;print(folder_tree_ddl_script())"
-- 001~006 一字不改；本迁移幂等（IF NOT EXISTS / 条件 UPDATE），可重放。
--
-- 应用方式（正常部署无需手工执行）：
--   自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--   `ensure_schema()` 依次执行：① documents 补 6 列（folder_id / name_key / uploaded_at /
--   content_updated_at / indexed_at / revision_of；SQLite 无 ADD COLUMN IF NOT EXISTS，
--   PRAGMA table_info 探测后逐列 ALTER）→ ② 本文件的新表与非唯一索引 → ③ 标量回填 →
--   ④ Python 的 name_key 回填 → ⑤ 本文件末尾的唯一索引。
--
-- 重要：Python 的 name_key 回填（NFC + casefold；历史重名行的键追加 U+001F + doc_id，显示名不变）
--   只在 ensure_schema 中执行，**不在本快照里**；本快照也**不含** documents 的 ALTER TABLE ADD COLUMN。
--   因此手工 `sqlite3 ledger.sqlite3 < 007_folder_tree.sql` 仅在“新库，或 ensure_schema 已跑过一次”时等价；
--   对仍有历史数据且未补列的老库直接执行会因缺列失败，请改走 ensure_schema（重启 ib-web）。
--
-- 回滚说明：
--   * 迁移只补列与回填标量，不改不删既有数据。
--   * 代码回退（git revert → 目标机 pull + 重启）：旧代码按命名列 SELECT / 显式列 INSERT，忽略新列，可运行。
--     回退前须先清掉在途修订行（documents.revision_of 非空；对每个有更新中状态的文件调用
--     DELETE /api/files/{doc_id}/revision，或回退后先删向量/blob 再 DELETE 这些行），否则旧代码会把它们当普通文档。
--     回退后子目录内的文件会在旧扁平列表中全部可见，同名文件会并存。
--   * MANUAL_ROLLBACK_REQUIRED（仅在确需撤销新结构时，须先备份台账文件）：
--       DROP TABLE doc_purge_queue; DROP TABLE upload_batch_items; DROP TABLE upload_batches; DROP TABLE folders;
--       DROP INDEX uq_documents_name; DROP INDEX uq_documents_revision; DROP INDEX idx_documents_folder;
--       ALTER TABLE documents DROP COLUMN <新列>（需 SQLite >= 3.35；低版本需重建表）。
--     回滚会丢失目录结构与时间语义列。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS folders (
        folder_id   TEXT PRIMARY KEY,
        project_id  TEXT NOT NULL,
        parent_id   TEXT NOT NULL DEFAULT '',
        name        TEXT NOT NULL,
        name_key    TEXT NOT NULL,
        depth       INTEGER NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_folders_parent ON folders(project_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_documents_folder ON documents(project_id, folder_id);
CREATE INDEX IF NOT EXISTS idx_batch_items_state ON upload_batch_items(batch_id, state);
CREATE INDEX IF NOT EXISTS idx_upload_batches_expiry ON upload_batches(expires_at);
UPDATE documents SET uploaded_at = created_at WHERE uploaded_at = '';
UPDATE documents SET indexed_at = updated_at WHERE status = 'indexed' AND indexed_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_folders_name ON folders(project_id, parent_id, name_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_name
        ON documents(project_id, folder_id, name_key) WHERE name_key <> '' AND revision_of IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_revision ON documents(revision_of) WHERE revision_of IS NOT NULL;
