-- ---------------------------------------------------------------------------
-- MOD-R29-07 / 手写 scoped 迁移（010）：MCP 外部工具 9 张新表。
-- REV-29：agent 工具调用的 MCP 适配——Server 登记、工具快照与审核、项目开放与固定入参、风险放行、
-- 加密凭证（只存密文）、全局治理参数、内网允许名单、调用与管理审计（IFC-R29-060 / ADR-R29-07）。
--
-- 由 `ib/ledger/schema.py::mcp_ddl_script()` **原样摘录**（单源；本文件是可审阅快照）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import mcp_ddl_script;print(mcp_ddl_script())"
-- 001~009 一字不改；本迁移幂等（IF NOT EXISTS），可重放。
--
-- 应用方式（正常部署无需手工执行）：
--   自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--   `ensure_schema()` 会幂等建好这些表（纯新表，无补列、无回填）。
--
-- 语义要点：
--   * `mcp_servers.transport` 的 CHECK 只含 'streamable_http'（stdio 已移出本轮，OOS-R29-11）；
--     SQLite 无法原地修改 CHECK，将来若支持其他传输需新迁移并重建该表。
--   * `mcp_credentials` 只有密文列（ciphertext BLOB + key_id），无任何明文列。
--   * `mcp_governance` 单行表（CHECK (id = 1)）；行缺失 ⇒ 读取返回保守默认值；16 个整数列带范围 CHECK。
--   * 升级后无任何 Server ⇒ 全部新路径不触发（行为 = REV-28）。
--
-- 回滚说明（MANUAL_ROLLBACK_REQUIRED）：以上均为新增表，不触碰任何既有数据；确需撤销时，
--   由用户在备份台账文件后执行（本文件刻意不含可执行的删除语句），按依赖逆序删除 9 张表
--   （mcp_audit、mcp_internal_allow、mcp_governance、mcp_credentials、mcp_risk_waivers、
--   mcp_tool_bindings、mcp_tools、mcp_server_projects、mcp_servers）。
--   回退前应先通过"强制清理授权"或手工移除各项目定义文档中的 mcp__ 授权，否则旧代码下保存会被拒绝。
--   代码回退走 git revert → 目标机 pull + 重启 ib-web。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mcp_servers (
        server_id            TEXT PRIMARY KEY,
        description          TEXT NOT NULL,
        transport            TEXT NOT NULL CHECK (transport IN ('streamable_http')),
        endpoint_url         TEXT NOT NULL,
        auth_kind            TEXT NOT NULL CHECK (auth_kind IN ('none', 'bearer', 'header')),
        auth_header_name     TEXT,
        credential_scope     TEXT NOT NULL CHECK (credential_scope IN ('shared', 'project')),
        scope_kind           TEXT NOT NULL CHECK (scope_kind IN ('platform', 'project')),
        owner_project        TEXT,
        open_all             INTEGER NOT NULL CHECK (open_all IN (0, 1)),
        data_categories      TEXT NOT NULL,
        admin_state          TEXT NOT NULL CHECK (admin_state IN ('registered', 'enabled', 'disabled')),
        health               TEXT NOT NULL CHECK (health IN ('unknown', 'up', 'down')),
        health_checked_at    TEXT,
        protocol_era         TEXT CHECK (protocol_era IS NULL OR protocol_era IN ('modern', 'legacy')),
        protocol_version     TEXT,
        supports_list_changed INTEGER NOT NULL CHECK (supports_list_changed IN (0, 1)),
        last_verify_at       TEXT,
        last_verify_result   TEXT,
        identity_epoch       INTEGER NOT NULL CHECK (identity_epoch >= 0),
        limit_call_timeout_s     INTEGER,
        limit_max_calls_per_turn INTEGER,
        limit_max_result_bytes   INTEGER,
        limit_max_concurrency    INTEGER,
        limit_breaker_threshold  INTEGER,
        limit_breaker_cooldown_s INTEGER,
        limit_discover_timeout_s INTEGER,
        created_at           TEXT NOT NULL,
        created_by           TEXT NOT NULL,
        updated_at           TEXT NOT NULL,
        updated_by           TEXT NOT NULL
    );
CREATE TABLE IF NOT EXISTS mcp_server_projects (
        server_id   TEXT NOT NULL,
        project_id  TEXT NOT NULL,
        created_at  TEXT NOT NULL,
        created_by  TEXT NOT NULL,
        PRIMARY KEY (server_id, project_id)
    );
CREATE INDEX IF NOT EXISTS ix_mcp_server_projects_project ON mcp_server_projects (project_id);
CREATE TABLE IF NOT EXISTS mcp_tools (
        tool_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id               TEXT NOT NULL,
        remote_name             TEXT NOT NULL,
        local_name              TEXT NOT NULL,
        display_name            TEXT NOT NULL,
        state                   TEXT NOT NULL CHECK (state IN ('pending_review', 'enabled', 'disabled', 'needs_rereview', 'offline', 'excluded')),
        risk                    TEXT NOT NULL CHECK (risk IN ('read_only', 'side_effect', 'unknown')),
        exclusion_reason        TEXT,
        observed_title          TEXT,
        observed_description    TEXT,
        observed_input_schema   TEXT,
        observed_output_schema  TEXT,
        observed_annotations    TEXT,
        observed_fingerprint    TEXT,
        observed_at             TEXT,
        approved_title          TEXT,
        approved_description    TEXT,
        approved_input_schema   TEXT,
        approved_output_schema  TEXT,
        approved_annotations    TEXT,
        approved_fingerprint    TEXT,
        approved_at             TEXT,
        approved_by             TEXT,
        approved_epoch          INTEGER,
        llm_description         TEXT,
        hidden_params           TEXT NOT NULL,
        offline_at              TEXT,
        offline_reason          TEXT,
        UNIQUE (server_id, remote_name),
        UNIQUE (local_name)
    );
CREATE INDEX IF NOT EXISTS ix_mcp_tools_server_state ON mcp_tools (server_id, state);
CREATE TABLE IF NOT EXISTS mcp_tool_bindings (
        tool_id     INTEGER NOT NULL,
        project_id  TEXT NOT NULL,
        fixed_args  TEXT NOT NULL,
        updated_at  TEXT NOT NULL,
        updated_by  TEXT NOT NULL,
        PRIMARY KEY (tool_id, project_id)
    );
CREATE TABLE IF NOT EXISTS mcp_risk_waivers (
        tool_id     INTEGER NOT NULL,
        project_id  TEXT NOT NULL,
        reason      TEXT NOT NULL,
        granted_by  TEXT NOT NULL,
        granted_at  TEXT NOT NULL,
        revoked_at  TEXT,
        PRIMARY KEY (tool_id, project_id)
    );
CREATE TABLE IF NOT EXISTS mcp_credentials (
        server_id   TEXT NOT NULL,
        scope_key   TEXT NOT NULL,
        ciphertext  BLOB NOT NULL,
        key_id      TEXT NOT NULL,
        updated_at  TEXT NOT NULL,
        updated_by  TEXT NOT NULL,
        PRIMARY KEY (server_id, scope_key)
    );
CREATE TABLE IF NOT EXISTS mcp_governance (
        id                         INTEGER PRIMARY KEY CHECK (id = 1),
        discover_timeout_s         INTEGER NOT NULL CHECK (discover_timeout_s BETWEEN 1 AND 60),
        call_timeout_s             INTEGER NOT NULL CHECK (call_timeout_s BETWEEN 1 AND 120),
        max_calls_per_turn         INTEGER NOT NULL CHECK (max_calls_per_turn BETWEEN 1 AND 20),
        max_result_bytes           INTEGER NOT NULL CHECK (max_result_bytes BETWEEN 1024 AND 262144),
        breaker_threshold          INTEGER NOT NULL CHECK (breaker_threshold BETWEEN 1 AND 50),
        breaker_cooldown_s         INTEGER NOT NULL CHECK (breaker_cooldown_s BETWEEN 1 AND 3600),
        max_concurrency_per_server INTEGER NOT NULL CHECK (max_concurrency_per_server BETWEEN 1 AND 16),
        max_inflight_global        INTEGER NOT NULL CHECK (max_inflight_global BETWEEN 1 AND 8),
        max_tools_per_server       INTEGER NOT NULL CHECK (max_tools_per_server BETWEEN 1 AND 500),
        max_description_chars      INTEGER NOT NULL CHECK (max_description_chars BETWEEN 100 AND 20000),
        max_schema_bytes           INTEGER NOT NULL CHECK (max_schema_bytes BETWEEN 1024 AND 131072),
        max_schema_depth           INTEGER NOT NULL CHECK (max_schema_depth BETWEEN 2 AND 16),
        max_arg_bytes              INTEGER NOT NULL CHECK (max_arg_bytes BETWEEN 256 AND 65536),
        health_interval_s          INTEGER NOT NULL CHECK (health_interval_s BETWEEN 0 AND 3600),
        revalidate_interval_s      INTEGER NOT NULL CHECK (revalidate_interval_s BETWEEN 0 AND 86400),
        listener_max               INTEGER NOT NULL CHECK (listener_max BETWEEN 0 AND 8),
        updated_at                 TEXT NOT NULL,
        updated_by                 TEXT NOT NULL
    );
CREATE TABLE IF NOT EXISTS mcp_internal_allow (
        host        TEXT NOT NULL,
        port        INTEGER NOT NULL CHECK (port BETWEEN 1 AND 65535),
        created_at  TEXT NOT NULL,
        created_by  TEXT NOT NULL,
        PRIMARY KEY (host, port)
    );
CREATE TABLE IF NOT EXISTS mcp_audit (
        call_id      TEXT PRIMARY KEY,
        ts           TEXT NOT NULL,
        kind         TEXT NOT NULL CHECK (kind IN ('admin', 'call', 'system')),
        action       TEXT NOT NULL,
        actor        TEXT NOT NULL,
        project_id   TEXT NOT NULL,
        server_id    TEXT NOT NULL,
        tool_name    TEXT NOT NULL,
        display_name TEXT NOT NULL,
        outcome      TEXT NOT NULL,
        reason       TEXT NOT NULL,
        duration_ms  INTEGER,
        args_digest  TEXT NOT NULL,
        args_summary TEXT NOT NULL,
        fingerprint  TEXT NOT NULL,
        confirm      INTEGER NOT NULL CHECK (confirm IN (0, 1)),
        trial        INTEGER NOT NULL CHECK (trial IN (0, 1))
    );
CREATE INDEX IF NOT EXISTS ix_mcp_audit_server_ts ON mcp_audit (server_id, ts);
CREATE INDEX IF NOT EXISTS ix_mcp_audit_project_ts ON mcp_audit (project_id, ts);
CREATE INDEX IF NOT EXISTS ix_mcp_audit_tool_ts ON mcp_audit (tool_name, ts);
