-- ---------------------------------------------------------------------------
-- MOD-R26-22 / 手写 scoped 迁移（008）：配置版本化（config_versions / config_head /
-- config_drafts / builder_eval_cache 四张新表 + 索引）。REV-26：保存即热生效、版本历史与回滚、
-- 草稿副本、Agent Builder 评审缓存。
--
-- 由 `ib/ledger/schema.py::config_versions_ddl_script()` **原样摘录**（单源；本文件是可审阅快照）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import config_versions_ddl_script;print(config_versions_ddl_script())"
-- 001~007 一字不改；本迁移幂等（IF NOT EXISTS），可重放。
--
-- 应用方式（正常部署无需手工执行）：
--   自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--   `ensure_schema()` 依次：① users 补列 config_level、config_audit 补列 version_before /
--   version_after / object_summary（SQLite 无 ADD COLUMN IF NOT EXISTS，PRAGMA table_info 探测后逐列 ALTER）
--   → ② 本文件的新表与索引。
--
-- 重要：本快照**不含** users / config_audit 的 ALTER TABLE ADD COLUMN（见上）。
--   手工 `sqlite3 ledger.sqlite3 < 008_config_versions.sql` 仅创建四张新表与索引；
--   users.config_level（NOT NULL DEFAULT 'manage' CHECK IN ('view','edit','manage')）与
--   config_audit 三个可空列须由 ensure_schema（重启 ib-web）补上。存量 ops 账号上线后为 manage 档
--   （与今天“能写配置”等价，不回退能力；admin 行忽略该列）。
--
-- 回滚说明：
--   * 代码回退（git revert → 目标机 pull + 重启）：旧代码对 users / config_audit 按命名列清单查询
--     （accounts.py 的 _U_COLUMNS、config_audit.py 的 _A_COLUMNS，无 SELECT *），忽略新列，可运行；新表被忽略。
--     回退前须确认没有 pending 版本：SELECT 1 FROM config_head WHERE pending_version IS NOT NULL;
--     v2 定义文档在旧代码下不可读（旧代码只认 schema_version == 1）——回退前须从版本快照 1（基线）还原
--     定义文档与提示词文件为 v1。MANUAL_ROLLBACK_REQUIRED（步骤见 checklists.txt B29）。
--   * MANUAL_ROLLBACK_REQUIRED（仅在确需撤销新结构时，须先备份台账文件，由用户执行）：
--       DROP TABLE builder_eval_cache; DROP TABLE config_drafts; DROP TABLE config_head; DROP TABLE config_versions;
--       ALTER TABLE users DROP COLUMN config_level;
--       ALTER TABLE config_audit DROP COLUMN version_before; ... DROP COLUMN version_after; ... DROP COLUMN object_summary;
--     DROP COLUMN 需 SQLite >= 3.35（目标机版本未知，部署前核对；低版本需重建表）。
--     回滚会丢失版本历史、草稿副本与评审缓存。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS config_versions (
        project_id       TEXT NOT NULL,
        version          INTEGER NOT NULL,
        parent_version   INTEGER NOT NULL,
        status           TEXT NOT NULL,
        kind             TEXT NOT NULL,
        rolled_back_to   INTEGER,
        actor            TEXT NOT NULL,
        created_at       TEXT NOT NULL,
        summary          TEXT NOT NULL,
        manifest_hash    TEXT NOT NULL,
        snapshot_json    TEXT NOT NULL,
        snapshot_bytes   INTEGER NOT NULL,
        PRIMARY KEY (project_id, version),
        CHECK (status IN ('pending', 'published', 'aborted')),
        CHECK (kind IN ('publish', 'rollback', 'baseline', 'adopt'))
    );
CREATE INDEX IF NOT EXISTS idx_config_versions_status
        ON config_versions(project_id, status, version);
CREATE TABLE IF NOT EXISTS config_head (
        project_id         TEXT PRIMARY KEY,
        published_version  INTEGER NOT NULL,
        pending_version    INTEGER,
        updated_at         TEXT NOT NULL
    );
CREATE TABLE IF NOT EXISTS config_drafts (
        draft_id       TEXT PRIMARY KEY,
        project_id     TEXT NOT NULL,
        owner          TEXT NOT NULL,
        label          TEXT NOT NULL,
        base_version   INTEGER NOT NULL,
        payload_json   TEXT NOT NULL,
        payload_bytes  INTEGER NOT NULL,
        created_at     TEXT NOT NULL
    );
CREATE INDEX IF NOT EXISTS idx_config_drafts_owner
        ON config_drafts(project_id, owner, created_at);
CREATE TABLE IF NOT EXISTS builder_eval_cache (
        cache_key       TEXT PRIMARY KEY,
        rubric_version  TEXT NOT NULL,
        result_json     TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );
CREATE INDEX IF NOT EXISTS idx_builder_eval_created
        ON builder_eval_cache(created_at);
