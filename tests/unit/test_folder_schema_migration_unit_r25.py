"""[R25 / GROUP_D] 单元 —— 007 迁移：单源一致、幂等、老库补列 / 回填、唯一约束（MOD-001 / MOD-015）。

溯源：US-017（AC-017-01 的数据层）、US-011（AC-011-05 同名不区分大小写的数据库兜底）、
画像 P6（手写 scoped 迁移、与 schema.py 逐字一致、幂等、已有迁移不改）。
只用标准库 sqlite3 + 临时文件 / 内存库，不连任何外部服务。
"""

from __future__ import annotations

import pathlib
import sqlite3
import subprocess

import pytest

from ib.ledger import schema

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATION = _ROOT / "src" / "deploy" / "migrations" / "007_folder_tree.sql"


def _norm(text: str) -> str:
    return "".join(text.split())


def _insert_project(con: sqlite3.Connection, project_id: str = "p1") -> None:
    con.execute(
        "INSERT OR IGNORE INTO projects(project_id, name, active_collection_version, embedding_model_id, dim, created_at)"
        " VALUES(?,?,?,?,?,?)",
        (project_id, project_id, "1", "bge-m3", 1024, "2026-01-01T00:00:00Z"),
    )


def _old_shape_db(path) -> sqlite3.Connection:
    """001 形态的老库（只有 DDL_STATEMENTS，documents 没有 6 个新列）。"""
    con = sqlite3.connect(str(path))
    for statement in schema.PRAGMA_DB_LEVEL + schema.PRAGMA_ON_CONNECT:
        con.execute(statement)
    for statement in schema.DDL_STATEMENTS:
        con.execute(statement)
    con.commit()
    return con


def _seed_old(con: sqlite3.Connection) -> list[tuple]:
    """插入 5 个文件：3 个 indexed、1 个 failed、1 个 pending；其中 `A.pdf` / `a.pdf` 为大小写历史重名。"""
    _insert_project(con)
    rows = [
        ("d1", "A.pdf", "indexed", "2026-01-01T01:00:00Z", "2026-01-01T01:05:00Z"),
        ("d2", "a.pdf", "indexed", "2026-01-01T02:00:00Z", "2026-01-01T02:05:00Z"),
        ("d3", "手册.txt", "indexed", "2026-01-01T03:00:00Z", "2026-01-01T03:05:00Z"),
        ("d4", "坏文件.txt", "failed", "2026-01-01T04:00:00Z", "2026-01-01T04:05:00Z"),
        ("d5", "新来的.md", "pending", "2026-01-01T05:00:00Z", "2026-01-01T05:00:00Z"),
    ]
    for doc_id, name, status, created, updated in rows:
        con.execute(
            "INSERT INTO documents(doc_id, project_id, kb_id, doc_name, ext, size_bytes, content_sha256, blob_ref,"
            " status, error_code, chunk_count, indexed_collection_version, target_collection_version, lease_owner,"
            " lease_expires_at, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (doc_id, "p1", "p1", name, name.rsplit(".", 1)[-1], 100, "sha-" + doc_id, None, status, None,
             3 if status == "indexed" else 0, "1" if status == "indexed" else None, None, None, None, created, updated),
        )
    con.commit()
    return rows


def _snapshot(con: sqlite3.Connection):
    docs = con.execute(
        "SELECT doc_id, doc_name, folder_id, name_key, uploaded_at, content_updated_at, indexed_at, revision_of, status"
        " FROM documents ORDER BY doc_id"
    ).fetchall()
    objs = con.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
    return docs, objs


def test_TC_UNIT_R25_040_migration_007_is_single_source_with_generator():
    """[TC-UNIT-R25-040] 画像 P6 单源：007_folder_tree.sql 去空白后包含 `folder_tree_ddl_script()`（与 CI 003 检查同口径）；001~006 在 HEAD 上未被改动。"""
    text = _MIGRATION.read_text(encoding="utf-8")
    assert _norm(schema.folder_tree_ddl_script()) in _norm(text), "007 快照与 schema.py 生成器不一致"
    # 已有迁移不改：工作区相对 HEAD 无差异（git 不可用时跳过比较会掩盖问题，因此要求 git 可用）
    diff = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *[str(p.relative_to(_ROOT)) for p in sorted((_ROOT / "src/deploy/migrations").glob("00[1-6]*.sql"))]],
        cwd=_ROOT,
    )
    assert diff.returncode == 0, "001~006 迁移被改动（画像 P6：已存在的迁移不改）"
    # 回滚说明与 MANUAL_ROLLBACK_REQUIRED 标注（P6：每个迁移写回滚说明）
    assert "回滚说明" in text and "MANUAL_ROLLBACK_REQUIRED" in text


def test_TC_UNIT_R25_041_fresh_db_ensure_schema_idempotent_and_replay_007():
    """[TC-UNIT-R25-041] 新库：ensure_schema 连续两遍快照一致；007 快照在其后重放两遍无副作用；四张新表与 6 个新列、3 个唯一索引齐备。"""
    con = sqlite3.connect(":memory:")
    schema.ensure_schema(con)
    first = _snapshot(con)
    schema.ensure_schema(con)
    assert _snapshot(con) == first
    sql = _MIGRATION.read_text(encoding="utf-8")
    con.executescript(sql)
    con.executescript(sql)
    assert _snapshot(con) == first
    tables = {n for t, n in first[1] if t == "table"}
    assert {"folders", "upload_batches", "upload_batch_items", "doc_purge_queue"} <= tables
    indexes = {n for t, n in first[1] if t == "index"}
    assert {"uq_folders_name", "uq_documents_name", "uq_documents_revision", "idx_documents_folder"} <= indexes
    cols = {r[1] for r in con.execute("PRAGMA table_info(documents)")}
    assert {c for c, _ in schema.FOLDER_TREE_ADDED_COLUMNS} <= cols
    assert schema.missing_columns(con) == {} and schema.missing_folder_tree_columns(con) == {}


def test_TC_UNIT_R25_042_old_db_upgrade_backfills_without_losing_or_renaming_rows(tmp_path):
    """[TC-UNIT-R25-042] AC-017-01（数据层）：001 形态老库升级后 —— 全部 N=5 行在根目录（folder_id=''）、名称 / 状态 / 大小不变；
    uploaded_at=created_at；仅 indexed 行 indexed_at=updated_at；历史大小写重名（A.pdf / a.pdf）显示名不变、name_key 去重。"""
    con = _old_shape_db(tmp_path / "old.sqlite3")
    rows = _seed_old(con)
    assert schema.missing_columns(con) != {}, "前置：老库应缺新列（否则本用例不是升级场景）"
    schema.ensure_schema(con)
    assert schema.missing_columns(con) == {}
    got = {r[0]: r for r in con.execute(
        "SELECT doc_id, doc_name, folder_id, name_key, uploaded_at, content_updated_at, indexed_at, revision_of, status, size_bytes FROM documents"
    )}
    assert len(got) == 5, "升级不得丢行"
    for doc_id, name, status, created, updated in rows:
        r = got[doc_id]
        assert r[1] == name, "显示名必须与升级前一致"
        assert r[2] == "" and r[7] is None and r[5] is None
        assert r[8] == status and r[9] == 100
        assert r[4] == created, "uploaded_at 回填为 created_at"
        assert r[6] == (updated if status == "indexed" else None), "indexed_at 仅对 indexed 行回填为 updated_at"
        assert r[3] != "", "name_key 已回填"
    keys = [got[d][3] for d in ("d1", "d2")]
    assert len(set(keys)) == 2 and keys[0] == "a.pdf" and keys[1].startswith("a.pdf\x1f"), keys
    con.close()


def test_TC_UNIT_R25_043_old_db_upgrade_is_idempotent_across_restarts(tmp_path):
    """[TC-UNIT-R25-043] M-TE-006：老库连续 ensure_schema 两遍（模拟 ib-web 与 ib-worker 各启动一次），快照逐行一致；回填不重复追加后缀。"""
    con = _old_shape_db(tmp_path / "old2.sqlite3")
    _seed_old(con)
    schema.ensure_schema(con)
    first = _snapshot(con)
    schema.ensure_schema(con)
    assert _snapshot(con) == first
    con.executescript(_MIGRATION.read_text(encoding="utf-8"))
    assert _snapshot(con) == first
    con.close()


def test_TC_UNIT_R25_044_add_columns_tolerates_concurrent_duplicate_column(tmp_path):
    """[TC-UNIT-R25-044] 并发补列容错：列已被他人补上时 `_ensure_document_tree_columns` 不抛、不重复（duplicate column name 被容忍）。"""
    con = _old_shape_db(tmp_path / "old3.sqlite3")
    schema._ensure_document_tree_columns(con)
    schema._ensure_document_tree_columns(con)
    cols = [r[1] for r in con.execute("PRAGMA table_info(documents)")]
    assert len(cols) == len(set(cols)) and "revision_of" in cols
    con.close()


def test_TC_UNIT_R25_045_unique_indexes_enforce_case_insensitive_names_and_single_revision():
    """[TC-UNIT-R25-045] AC-011-05 / AC-016-03 的数据库兜底：同目录 name_key 重复被拒；修订行（name_key=''）不占名；同一存活行至多一个修订行。"""
    con = sqlite3.connect(":memory:")
    schema.ensure_schema(con)
    _insert_project(con)
    # folders 唯一
    now = "2026-01-01T00:00:00Z"
    con.execute("INSERT INTO folders VALUES('f1','p1','','Design','design',1,?,?)", (now, now))
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO folders VALUES('f2','p1','','design','design',1,?,?)", (now, now))
    con.execute("INSERT INTO folders VALUES('f3','p1','f1','design','design',2,?,?)", (now, now))  # 不同父目录可同名

    def doc(doc_id, name_key, revision_of=None):
        con.execute(
            "INSERT INTO documents(doc_id, project_id, kb_id, doc_name, ext, size_bytes, content_sha256, status, chunk_count,"
            " created_at, updated_at, folder_id, name_key, uploaded_at, revision_of) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (doc_id, "p1", "p1", doc_id, "txt", 1, "s", "pending", 0, now, now, "f1", name_key, now, revision_of),
        )

    doc("x1", "a.txt")
    with pytest.raises(sqlite3.IntegrityError):
        doc("x2", "a.txt")
    doc("rev1", "", revision_of="x1")  # 修订行 name_key='' 不占名
    doc("rev2", "", revision_of=None)  # 兼容：name_key='' 的待回填行不受 uq_documents_name 约束
    with pytest.raises(sqlite3.IntegrityError):
        doc("rev3", "", revision_of="x1")  # 同一存活行第二个修订行
    con.close()
