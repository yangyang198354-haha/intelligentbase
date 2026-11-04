-- ---------------------------------------------------------------------------
-- MOD-R28-06 / 手写 scoped 迁移（009）：联网全局用量上限单行表（web_governance）。
-- REV-28：平台级内置顾问 agent 的联网治理——admin 设定每回合联网调用数 / 抓取字节 / 累计耗时上限
-- （IFC-R28-008 / ADR-R28-07）。
--
-- 由 `ib/ledger/schema.py::web_governance_ddl_script()` **原样摘录**（单源；本文件是可审阅快照）。生成命令：
--   python -X utf8 -c "import sys;sys.path.insert(0,'src');from ib.ledger.schema import web_governance_ddl_script;print(web_governance_ddl_script())"
-- 001~008 一字不改；本迁移幂等（IF NOT EXISTS），可重放。
--
-- 应用方式（正常部署无需手工执行）：
--   自动：`ib-web.service` 的 ExecStartPre 调 `python -m ibweb.bootstrap --ensure-schema`，
--   `ensure_schema()` 会幂等建好本表。
--
-- 语义要点：
--   * 单行表：`CHECK (id = 1)`；行缺失 ⇒ 读取返回保守默认值（5 次 / 1048576 字节 / 30 秒），
--     故升级后未设置即为默认上限。
--   * 三个整数列带 CHECK 范围（与代码硬上限一致：次数 1..20、字节 10000..5242880、秒 1..120）。
--
-- 回滚说明（MANUAL_ROLLBACK_REQUIRED）：本表为新增表，不触碰任何既有数据；确需撤销时，
--   由用户在备份台账文件后执行（本文件刻意不含可执行的删除语句）：
--       DROP TABLE web_governance;
--   回滚后存储不可读 ⇒ 含联网授权的配置保存 fail-closed（web_governance_unavailable），
--   不含联网授权的项目不受影响。代码回退走 git revert → 目标机 pull + 重启 ib-web。
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS web_governance (
        id                       INTEGER PRIMARY KEY CHECK (id = 1),
        max_calls_per_turn       INTEGER NOT NULL CHECK (max_calls_per_turn BETWEEN 1 AND 20),
        max_fetch_bytes_per_turn INTEGER NOT NULL CHECK (max_fetch_bytes_per_turn BETWEEN 10000 AND 5242880),
        max_seconds_per_turn     INTEGER NOT NULL CHECK (max_seconds_per_turn BETWEEN 1 AND 120),
        updated_at               TEXT NOT NULL,
        updated_by               TEXT NOT NULL
    );
