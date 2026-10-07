-- ---------------------------------------------------------------------------
-- @module MOD-IB-11
-- @implements 手写 scoped 迁移（006）：LLM Key 单行表（REV-18 / ADR-38 / IFC-IB-371 / IFC-IB-377）
-- @author software-developer
--
-- 由 `ib/ledger/schema.py::llm_key_ddl_script()` **原样摘录**（单源不变；本文件是
-- 「可人工审阅的增量快照」）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import llm_key_ddl_script;print(llm_key_ddl_script())"
--
-- 为什么新增 006 而不改 001~005：
--   001~005 的契约都是「与生成时逐字一致」；REV-18 的 LLM Key 增量另立 006，使
--   **升级路径显式可审计**（延续 schema.py docstring 的既定纪律）。`006` 位号本轮首次占用。
--
-- 应用方式（正常部署**无需手工执行**）：
--   1) 自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--      其中 `ensure_schema()` 会幂等建好本表（对既有 R1~REV-16-4 库同样生效）。
--   2) 手工（核对时）：sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 006_llm_key.sql
--
-- 语义要点（ADR-38 / REQ-NFR-IB-20 / C-IB-42）：
--   * **单行表**：`CHECK (id = 1)` —— 「全局唯一一个 Key」是**表结构层面的事实**（OQ-IB-26）；
--     项目级 / 多供应商 = OOS-18，为扩展点预留，本轮不做。
--   * **承载库文件 0600 且属主对齐服务账号**（部署检查清单 B22）：本表落在**同一 SQLite
--     台账文件**（`IB_LEDGER_PATH`）；文件权限由 `SqliteLlmKeyStore` 在 POSIX 上 best-effort
--     收紧至 0600，**属主对齐服务账号须由用户在部署期执行**（代理不执行生产变更）。
--   * **凭据纪律（硬约束）**：`secret` **明文**只可经 `LlmKeyStore.get()` 供组合根**装配期**
--     解析（唯一读点，ADR-38）；**唯一写入口** = HTTP `PUT /api/llm-key`；HTTP 响应只承载
--     `LlmKeyStatus`（`configured` / `masked` / `updated_at`，**类型层不含明文**）。
--   * Key **不入 `.env` / 不进 git / 不进命令行与 shell history**（部署检查清单 B23）。
--
-- 回滚说明：本表为**新增凭据表**，回滚即 `DROP TABLE llm_key;`（不影响任何既有表）。
--   生产回滚前请先确认已由**用户**完成 Key 的移交 / 下线（本迁移不触碰既有数据）。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS llm_key (
        id         INTEGER PRIMARY KEY CHECK (id = 1),
        secret     TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
