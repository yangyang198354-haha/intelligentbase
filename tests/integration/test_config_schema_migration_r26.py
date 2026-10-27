"""[REV-26 / GROUP_D] 迁移 008（config_versions）：与 schema.py 单源逐字一致、幂等、老库形态补列、存量 ops 账号为 manage 档；
worker 维护（版本修剪 / 草稿过期 / 审计 1 年保留 / 评审缓存）。

溯源：US-020（AC-020-02 升级零改写）、US-017（AC-017-04 保留 50）、US-023（AC-023-05 审计 1 年）、OQ-R26-A01、MOD-R26-17/22、画像 P6。
层级：集成（真实 sqlite3 临时库 + 真实 ensure_schema + 真实 worker.run_maintenance）。
"""

from __future__ import annotations

import pathlib
import re
import sqlite3

from config_r26_support import expert, make_v2_document

from ib.config.versioning import build_snapshot, manifest_hash
from ib.core import ConfigAuditEntry, NewVersion, PromptLayers
from ib.ledger.config_audit import SqliteConfigAuditStore
from ib.ledger.config_versions import SqliteConfigDraftStore, SqliteConfigVersionStore
from ib.ledger.schema import config_versions_ddl_script, ensure_schema, missing_config_version_columns

SQL = pathlib.Path(__file__).resolve().parents[2] / "src" / "deploy" / "migrations" / "008_config_versions.sql"
NEW_TABLES = {"config_versions", "config_head", "config_drafts", "builder_eval_cache"}


def _strip(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    return re.sub(r"\s+", " ", sql).strip()


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _schema(conn):
    return sorted((r[0], r[1]) for r in conn.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"))


def test_TC_INT_R26_120_migration_008_is_verbatim_single_source_of_schema():
    """画像 P6：008 迁移内容（去注释、去空白后）与 schema.py 生成器逐字一致（单源）。"""
    assert _strip(SQL.read_text(encoding="utf-8")) == _strip(config_versions_ddl_script())
    assert "IF NOT EXISTS" in SQL.read_text(encoding="utf-8") and "MANUAL_ROLLBACK_REQUIRED" in SQL.read_text(encoding="utf-8")


def test_TC_INT_R26_121_migration_creates_four_tables_and_replays_idempotently(tmp_path):
    """画像 P6：手工执行 008 两遍 → 四张新表存在，结构快照一致（幂等 IF NOT EXISTS）。"""
    conn = sqlite3.connect(str(tmp_path / "m.db"))
    conn.executescript(SQL.read_text(encoding="utf-8"))
    first = _schema(conn)
    conn.executescript(SQL.read_text(encoding="utf-8"))
    assert _schema(conn) == first and NEW_TABLES <= _tables(conn)


def test_TC_INT_R26_122_ensure_schema_on_fresh_db_twice_is_stable_and_complete(tmp_path):
    """新库 ensure_schema 两遍 → 结构一致；users.config_level 与 config_audit 三个新列齐全（missing = {}）。"""
    conn = sqlite3.connect(str(tmp_path / "f.db"), isolation_level=None)
    ensure_schema(conn)
    one = _schema(conn)
    ensure_schema(conn)
    assert _schema(conn) == one and missing_config_version_columns(conn) == {}
    cols = {r[1] for r in conn.execute("PRAGMA table_info(config_audit)")}
    assert {"version_before", "version_after", "object_summary"} <= cols


def test_TC_INT_R26_123_old_db_shape_gets_columns_and_existing_ops_become_manage(tmp_path):
    """OQ-R26-A01、US-020：老库形态（001+003+004 已应用、无新列）→ ensure_schema 补列；老库里已存在的 ops 账号补列后为 manage 档；
    重复执行结构一致；既有审计行保留且新列为空。"""
    mig = SQL.parent
    conn = sqlite3.connect(str(tmp_path / "old.db"), isolation_level=None)
    for name in ("001_ledger_init.sql", "003_accounts.sql", "004_config_audit.sql"):
        conn.executescript((mig / name).read_text(encoding="utf-8"))
    assert "config_level" not in {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    conn.execute("INSERT INTO users (user_id, username, password_hash, role, project_id, status, must_change_password, "
                 "failed_login_count, locked_until, created_at, updated_at) VALUES ('u1','ops_old','h','ops','p_alpha','active',0,0,NULL,'t','t')")
    conn.execute("INSERT INTO config_audit (timestamp, project, actor, action, changed_field_names, result, detail_code) "
                 "VALUES ('2026-01-01T00:00:00Z','p_alpha','a','definition.save','[\"x\"]','saved',NULL)")
    ensure_schema(conn)
    snap = _schema(conn)
    ensure_schema(conn)
    assert _schema(conn) == snap and missing_config_version_columns(conn) == {} and NEW_TABLES <= _tables(conn)
    assert conn.execute("SELECT config_level FROM users WHERE user_id='u1'").fetchone()[0] == "manage"
    row = conn.execute("SELECT version_before, version_after, object_summary FROM config_audit").fetchone()
    assert row[0] is None and row[1] is None
    try:
        conn.execute("UPDATE users SET config_level='root' WHERE user_id='u1'")
        raised = False
    except sqlite3.IntegrityError:
        raised = True
    assert raised, "config_level 有 CHECK 约束"


# ------------------------------ worker 维护 ------------------------------ #


def _deps_with_sqlite(tmp_path):
    from types import SimpleNamespace

    path = str(tmp_path / "w.db")
    vs, ds, audit = SqliteConfigVersionStore(path), SqliteConfigDraftStore(path), SqliteConfigAuditStore(path)
    return SimpleNamespace(version_store=vs, draft_store=ds, config_audit_store=audit, eval_cache=None), vs, ds, audit


def _snap(i):
    ex = (expert("a", default=True, max_steps=1 + (i % 8)),)
    return build_snapshot(make_v2_document("p", ex), {"a": PromptLayers("t", None)})


def test_TC_INT_R26_124_run_maintenance_prunes_versions_purges_old_drafts_and_audit(tmp_path):
    """US-017 / AC-017-04、US-023 / AC-023-05：维护保留 head + 最近 50 个版本；过期草稿被清；审计保留 1 年：
    364 天前的记录保留、366 天前的记录被清。"""
    from ibweb.worker import run_maintenance

    deps, vs, ds, audit = _deps_with_sqlite(tmp_path)
    base = 0
    for i in range(60):
        s = _snap(i)
        r = vs.begin_publish("p", base_version=base, new=NewVersion("publish", "u", f"v{i}", None, manifest_hash(s)), snapshot=s,
                             extra_baseline=None, now="2026-10-27T00:00:00Z", stale_after_s=30.0)
        vs.commit_publish("p", r.version, now="2026-10-27T00:00:00Z", keep=1000)   # 不在提交时修剪，交给维护
        base = r.version
    assert len(vs.list_versions("p", limit=500, before_version=None)) == 60
    ds.save("p", "u", label="old", base_version=0, payload_json="{}", now="2026-08-01T00:00:00Z", max_per_owner=5)
    ds.save("p", "u", label="new", base_version=0, payload_json="{}", now="2026-10-20T00:00:00Z", max_per_owner=5)
    def entry(ts, who):
        return ConfigAuditEntry(timestamp=ts, project="p", actor=who, action="config.publish", changed_field_names=(),
                                result="saved", detail_code=None)
    audit.record(entry("2025-10-28T00:00:00Z", "d364"))     # 距 now 364 天
    audit.record(entry("2025-10-26T00:00:00Z", "d366"))     # 距 now 366 天
    m = run_maintenance(deps=deps, now="2026-10-27T00:00:00Z")
    assert m.versions_pruned == 10 and len(vs.list_versions("p", limit=500, before_version=None)) == 50
    assert vs.head("p").published_version == 60 and vs.get_version("p", 60) is not None and vs.get_version("p", 10) is None
    assert m.drafts_purged == 1 and [d.label for d in ds.list("p", "u")] == ["new"]
    left = {e.actor for e in audit.list_by_project("p", limit=100)}
    assert "d364" in left and "d366" not in left and m.audit_purged == 1


def test_TC_INT_R26_125_maintenance_step_failure_does_not_block_other_steps(tmp_path):
    """MOD-R26-17：每一类维护各自 try，一类失败不影响其余。"""
    from ibweb.worker import run_maintenance

    deps, vs, ds, audit = _deps_with_sqlite(tmp_path)

    class Boom:
        def prune_all(self, *, keep):
            raise RuntimeError("down")

    deps.version_store = Boom()
    ds.save("p", "u", label="old", base_version=0, payload_json="{}", now="2026-01-01T00:00:00Z", max_per_owner=5)
    m = run_maintenance(deps=deps, now="2026-10-27T00:00:00Z")
    assert m.versions_pruned == 0 and m.drafts_purged == 1


def test_TC_INT_R26_126_web_layer_exposes_no_audit_delete_path():
    """US-023 / AC-023-03：Web 层 Deps 不持有审计删除句柄；config_audit 端口只有 record / list_by_project 两个方法（purge_before 仅 worker 经具体类用）。"""
    from ib.core import ConfigAuditStore

    methods = {m for m in dir(ConfigAuditStore) if not m.startswith("_")}
    assert methods == {"record", "list_by_project"}
    import dataclasses

    from ibweb.composition import Deps

    assert "audit_retention" not in {f.name for f in dataclasses.fields(Deps)}
