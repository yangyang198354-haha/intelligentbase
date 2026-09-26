-- ---------------------------------------------------------------------------
-- @module MOD-IB-25 / MOD-IB-11
-- @implements 手写 scoped 迁移（002）：页面图 ↔ 文块关联表（R2 / M-02 / IFC-IB-278~279）
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::ddl_script()` 中 **R2 新增的那三条 DDL 语句** 原样摘录
-- （单一真源不变；本文件只是「可人工审阅的增量快照」）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import DDL_STATEMENTS;print(';\n'.join(s.strip() for s in DDL_STATEMENTS if 'chunk_image' in s)+';')"
--
-- 为什么不改 001 而是新增 002：
--   001 是 **R1 的 DDL 快照**，其契约是「与当时的 ddl_script() 逐字一致」；R2 增量另立
--   文件，使**升级路径显式可审计**（schema.py docstring 的既定纪律：「新增列通过显式
--   ALTER 迁移脚本落地 —— 表结构变更应当显式且可审计」，而**不是**回头改历史快照）。
--
-- 应用方式（两种，正常部署**无需手工执行**）：
--   1) 自动：systemd 单元 `ib-web.service` 的 ExecStartPre 调用 `ensure_schema()`，
--      其中的 `CREATE TABLE IF NOT EXISTS` 会幂等建好本表（对既有 R1 库同样生效）。
--   2) 手工（核对时）：sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 002_chunk_image.sql
--
-- 语义要点：
--   * **独立表，不动 `chunks` 任何列** —— 既有 `IFC-IB-009`（ParsedChunk）与
--     `IFC-IB-007`（RetrievedChunk）字段集一字不改（编号只增不改）。
--   * 幂等键物化为主键 `image_row_id` = `(project_id, kb_id, doc_id, page_or_section, image_id)`
--     的定长拼接（与 `chunks.chunk_id` 的做法同构）→ 重跑（重建 / 重试）覆盖同一行。
--   * `ON DELETE CASCADE` → **IFC-IB-281 的「删除零改动不变式」**：`mark_deleted` 只删
--     `documents` 行，关联行由 SQLite 在同一事务内级联清除；`DeleteReport` 的
--     `vectors_deleted` / `blob_deleted` / `ledger_deleted` 三个计数**语义不变**。
--   * `blob_ref` 可空：OCR 后即弃的历史文档其图字节不可得 —— 此时仍登记关联（可审计），
--     但取图端点返回 404、流事件不为其发 `related_images`（§7.4 降级行，fail-open）。
-- ---------------------------------------------------------------------------

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
);
CREATE INDEX IF NOT EXISTS idx_chunk_image_doc ON chunk_image(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunk_image_scope ON chunk_image(project_id, kb_id);
