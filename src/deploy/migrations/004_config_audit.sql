-- ---------------------------------------------------------------------------
-- @module MOD-IB-11
-- @implements 手写 scoped 迁移（004）：配置审计表（REV-16-4 / ADR-34 / IFC-IB-358）
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::config_audit_ddl_script()` **原样摘录**（单源不变；本文件是
-- 「可人工审阅的增量快照」）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import config_audit_ddl_script;print(config_audit_ddl_script())"
--
-- 为什么不改 001 / 002 / 003 而是新增 004：
--   001（R1 DDL 快照）/ 002（chunk_image 增量）/ 003（accounts 增量）的契约都是
--   「与生成时逐字一致」；REV-16-4 增量另立 004，使**升级路径显式可审计**
--   （延续 schema.py docstring 的既定纪律）。`004` 位号本轮首次占用。
--
-- 应用方式（正常部署**无需手工执行**）：
--   1) 自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--      其中 `ensure_schema()` 会幂等建好本表（对既有 R1~R13 库同样生效）。
--   2) 手工（核对时）：sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 004_config_audit.sql
--
-- 语义要点（ADR-34）：
--   * **只读审计，不是第二真源** —— 本表只承载「谁在何时对哪个项目的配置做了何种动作、
--     结果如何」的追加式记录；任何上层模块**不得**从这里回读配置来驱动行为；
--   * 与 `users` / `sessions` 一样**不加外键**到 `projects`（审计记录须在项目被删后仍可考）；
--   * `changed_field_names` 存 **JSON 数组**且**只含字段名**；`detail_code` **只含**
--     字段名 / 错误码 —— 二者**永不**含任何字段值或凭据（SC-3）；
--   * `CHECK (result IN ('saved', 'rejected'))` 在**存储层**兜一道取值域。
--
-- 回滚说明：本表为**新增只读审计表**，回滚即 `DROP TABLE config_audit;`
-- （不影响任何既有表；审计历史随之丢弃，符合「审计是旁路」的定位）。
-- ---------------------------------------------------------------------------

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
    );
CREATE INDEX IF NOT EXISTS idx_config_audit_project
        ON config_audit(project, entry_id);
