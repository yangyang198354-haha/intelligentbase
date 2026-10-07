-- ---------------------------------------------------------------------------
-- @module MOD-IB-11
-- @implements 手写 scoped 迁移（005）：项目注册表 + kb_default 归属迁移
--             （REV-18 / ADR-37 / ADR-41 / IFC-IB-370 / IFC-IB-377）
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::project_registry_ddl_script()` **原样摘录**（单源不变；
-- 本文件是「可人工审阅的增量快照」）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import project_registry_ddl_script;print(project_registry_ddl_script())"
--
-- 为什么新增 005 而不改 001~004：
--   001（R1 DDL 快照）/ 002（chunk_image 增量）/ 003（accounts 增量）/ 004（config_audit
--   增量）的契约都是「与生成时逐字一致」；REV-18 增量另立 005，使**升级路径显式可审计**
--   （延续 schema.py docstring 的既定纪律）。`005` 位号本轮首次占用。
--
-- 应用方式（正常部署**无需手工执行**）：
--   1) 自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--      其中 `ensure_schema()` 幂等建表 / 补列并执行本快照中的前向数据迁移（对既有 R1~REV-16-4
--      库同样生效）。
--   2) 手工（核对时）：sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 005_projects.sql
--
-- 语义要点（ADR-37 / ADR-41）：
--   * **同一 SQLite 台账的既有 `projects` 表**：本快照的 `CREATE TABLE IF NOT EXISTS`
--     在既有库上是**空操作**（表已由 001 建）；REV-18 新增的注册表侧列
--     `status` / `updated_at` 由 `ensure_schema()` 的幂等补列
--     （`ALTER TABLE ... ADD COLUMN`，SQLite 无 `ADD COLUMN IF NOT EXISTS`，故在 Python
--     侧先 `PRAGMA table_info` 再补）落实 —— 见 `schema.py::_ensure_project_registry_columns`。
--     两列**带默认值**（`'active'` / `''`），使既有 `upsert_project` 的 6 列 INSERT 继续有效。
--   * **软删 = 置 `status="disabled"`（不删行）**：数据保留、可恢复（OOS-19 已把物理级联删除
--     移出范围）；`idx_projects_status` 支撑 `GET /api/projects` 的活动项目过滤。
--   * **`kb_default` 归属迁移（前向、幂等）**：为每个项目登记 `kb_id == project_id` 的 KB 行，
--     并把既有落在 `kb_default` 的 `documents` / `chunks` / `chunk_image` 行改挂到其
--     `project_id`（ADR-41 ③）。`WHERE NOT EXISTS` / `WHERE kb_id='kb_default'` 使重复执行
--     收敛（迁移家族纪律：幂等、可前向）。
--   * 表内**只承载项目标识 / 名称 / 状态 / 时间戳与台账侧列**，**不承载任何凭据 / 配置取值**。
--
-- 回滚说明：本迁移**纯前向放大**（只新增列 / 索引 / 数据归属，不删除既有列）。
--   回滚 = **代码回滚**（数据保留；新列与 `kb_id` 归属不回退，属「向前兼容」的既定纪律）。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS projects (
        project_id                TEXT PRIMARY KEY,
        name                      TEXT NOT NULL,
        active_collection_version TEXT NOT NULL,
        embedding_model_id        TEXT NOT NULL,
        dim                       INTEGER NOT NULL,
        created_at                TEXT NOT NULL,
        status                    TEXT NOT NULL DEFAULT 'active',
        updated_at                TEXT NOT NULL DEFAULT ''
    );
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
INSERT INTO kbs (kb_id, project_id, name, created_at)
    SELECT p.project_id, p.project_id, p.name, p.created_at
    FROM projects p
    WHERE NOT EXISTS (SELECT 1 FROM kbs k WHERE k.kb_id = p.project_id);
UPDATE documents SET kb_id = project_id WHERE kb_id = 'kb_default';
UPDATE chunks SET kb_id = project_id WHERE kb_id = 'kb_default';
UPDATE chunk_image SET kb_id = project_id WHERE kb_id = 'kb_default';
