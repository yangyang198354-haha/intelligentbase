"""单元测试层 —— REV-18 增量（项目注册表 / LLM Key / kb 项目域迁移 / LLM 未配置态启动）。

覆盖 `architecture_design.md` ADR-37 ~ ADR-42 与 `module_design.md` IFC-IB-367 ~ IFC-IB-377 的
**纯函数 / 结构 / 语义**层（离线，无 HTTP）：

  * `LlmKeyStatus` **类型层不含明文字段**（AC-IB-39-01 / AC-IB-39-03；REQ-NFR-IB-20 / C-IB-42）；
  * `llm_key` **单行表**（`CHECK (id = 1)`）以**结构**保证「全局唯一一个 Key」（OQ-IB-26 / ADR-38）；
  * `LlmKeyStore` / `ProjectRegistryStore` 两实现的语义一致与端口形状（IFC-IB-367 / 368 / 370 / 371）；
  * 项目注册表**软删 = 置状态**（数据保留、可恢复；OOS-19）与 `seed` **幂等且不覆盖**（ADR-37）；
  * 手写迁移 `005` 的**单源一致**与 **`kb_default` 前向迁移幂等**（AC-IB-40-04 / ADR-41 / IFC-IB-377）；
  * **LLM 未配置态非致命**（ADR-39 **Option C**）：缺 Key 服务仍可启动，其余必填项仍 fail-fast；
  * `users.project_id` **无唯一约束**（OQ-IB-28「零迁移」；1:N）。

凭据纪律：本文件内的 secret 一律为**占位值**（非真实密钥），仅用于验证「写入后只回掩码」。
"""

from __future__ import annotations

import dataclasses
import os
import sqlite3
import stat
from pathlib import Path

import pytest

#: 测试用**占位** Key（**非真实密钥**；性质同 `conftest.R13_ADMIN_PASSWORD`）。
PLACEHOLDER_SECRET = "sk-rev18-unit-placeholder-not-a-real-key"
PLACEHOLDER_SECRET_LONG = "sk-rev18-unit-placeholder-" + "x" * 40


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalize_sql(text: str) -> str:
    """去掉 `--` 注释并把空白折叠为单空格（使快照与脚本可比对**语义同一**）。"""
    code = [line.split("--")[0] for line in text.splitlines()]
    return " ".join(" ".join(code).split())


def _kb_snapshot(conn: sqlite3.Connection) -> dict:
    """把 kb 归属相关的四张表按稳定顺序投影为可比较的静态快照。"""
    return {
        "documents": conn.execute("SELECT doc_id, kb_id FROM documents ORDER BY doc_id").fetchall(),
        "chunks": conn.execute("SELECT chunk_id, kb_id FROM chunks ORDER BY chunk_id").fetchall(),
        "chunk_image": conn.execute(
            "SELECT image_row_id, kb_id FROM chunk_image ORDER BY image_row_id"
        ).fetchall(),
        "kbs": conn.execute("SELECT kb_id, project_id FROM kbs ORDER BY kb_id").fetchall(),
    }


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-001 LLM Key 状态视图：类型层不含明文 + 掩码与明文长度无关
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_001_llm_key_status_excludes_plaintext() -> None:
    """US-IB-39 / AC-IB-39-01 / AC-IB-39-03；REQ-NFR-IB-20 / C-IB-42 / ADR-38。

    「不回显明文」是**类型层事实**：`LlmKeyStatus` 只有 `configured` / `masked` / `updated_at`
    三个字段，且 `masked` 为固定占位掩码（不含明文任何前 / 后缀字符、长度无关 ——
    消除长度 / 前缀侧信道，ADR-38 §10.1 OI-3）。
    """
    from ib.core import LLM_KEY_MASK, LlmKeyStatus
    from ib.ledger.llm_key import MemoryLlmKeyStore

    fields = {f.name for f in dataclasses.fields(LlmKeyStatus)}
    assert fields == {"configured", "masked", "updated_at"}, fields
    assert not (fields & {"secret", "key", "api_key", "value", "token", "plaintext"}), (
        f"LlmKeyStatus 承载了明文字段：{fields}"
    )

    assert LLM_KEY_MASK == "********"
    assert "sk-" not in LLM_KEY_MASK

    # 长度 / 前缀侧信道被消除：不同长度明文 → 同一掩码。
    store = MemoryLlmKeyStore()
    short = store.set(PLACEHOLDER_SECRET)
    long_ = store.set(PLACEHOLDER_SECRET_LONG)
    assert short.masked == long_.masked == LLM_KEY_MASK
    assert PLACEHOLDER_SECRET not in short.masked
    assert PLACEHOLDER_SECRET_LONG not in long_.masked
    # 未配置态：configured=False，**且 masked 为空**、updated_at 为空。
    store.clear()
    idle = store.status()
    assert idle.configured is False and idle.masked == "" and idle.updated_at is None


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-002 llm_key 单行表：快照单源一致 + CHECK(id=1) 以结构保证唯一
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_002_llm_key_single_row_structure() -> None:
    """US-IB-39 / AC-IB-39-02；OQ-IB-26 / ADR-38 / IFC-IB-371（+ 交付物 IFC-IB-377）。

    * `006_llm_key.sql` 快照与 `schema.llm_key_ddl_script()` **语义同一**（单源不变）；
    * `CHECK (id = 1)` 使「全局唯一一个 Key」成为**表结构层面的事实**：直插 `id=2` 被拒。
    """
    from ib.ledger.schema import llm_key_ddl_script

    snapshot = (_repo_root() / "src" / "deploy" / "migrations" / "006_llm_key.sql").read_text(
        encoding="utf-8"
    )
    script = llm_key_ddl_script()
    assert _normalize_sql(snapshot) == _normalize_sql(script), "006 快照与 DDL 单源不一致"
    assert "CHECK (id = 1)" in script or "CHECK(id = 1)" in script

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(script)
        conn.execute("INSERT INTO llm_key (id, secret, updated_at) VALUES (1, 'a', 't')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO llm_key (id, secret, updated_at) VALUES (2, 'b', 't')")
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-003 LlmKeyStore：端口形状 + SQLite/内存语义一致 + 覆盖写入单行
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_003_llm_key_store_port_and_parity(tmp_path) -> None:
    """US-IB-39 / AC-IB-39-02；IFC-IB-368 / IFC-IB-371 / ADR-38。

    端口恰 `get` / `set` / `clear` 三方法；SQLite 与内存两实现语义一致（未配置 → 写入 →
    覆盖 → 清空幂等），且 SQLite 侧 `set` 两次后**仍只有一行**（单行表）。
    """
    from ib.core.ports import LlmKeyStore
    from ib.ledger.llm_key import MemoryLlmKeyStore, SqliteLlmKeyStore

    for method in ("get", "set", "clear"):
        assert callable(getattr(LlmKeyStore, method, None)), f"端口缺方法 {method}"

    db_path = tmp_path / "ledger.sqlite3"
    sqlite_store = SqliteLlmKeyStore(str(db_path))
    mem_store = MemoryLlmKeyStore()

    for store in (sqlite_store, mem_store):
        assert store.get() is None
        first = store.set(PLACEHOLDER_SECRET)
        assert first.configured is True and first.masked == "********" and first.updated_at
        second = store.set(PLACEHOLDER_SECRET_LONG)
        assert second.configured is True
        record = store.get()
        assert record is not None and record.secret == PLACEHOLDER_SECRET_LONG
        store.clear()
        assert store.get() is None
        store.clear()  # 幂等：重复清空不报错

    sqlite_store.set(PLACEHOLDER_SECRET)
    sqlite_store.set(PLACEHOLDER_SECRET_LONG)
    sqlite_store.close()

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT COUNT(*), MIN(id), MAX(id) FROM llm_key").fetchone()
    finally:
        conn.close()
    assert rows == (1, 1, 1), f"llm_key 非单行（{rows}）"


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-004 项目注册表：端口形状 + 软删语义 + seed 幂等不覆盖
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_004_project_registry_soft_delete_and_seed() -> None:
    """US-IB-36 / AC-IB-36-03；ADR-37 / IFC-IB-367 / IFC-IB-370（OQ-IB-27 / OOS-19）。

    * 端口恰 `load` / `list_active` / `create` / `update` / `disable` 五方法；
    * `create` 重名 → `ConflictError`（409）；
    * `disable` **只改状态、保留行**（软删 / 停用，可恢复），`list_active` 过滤之；
    * `seed` 幂等且**不覆盖**既有行（运行期改名 / 停用不被配置回滚）。
    """
    from ib.core import ConflictError, ProjectRegistryEntry
    from ib.core.ports import ProjectRegistryStore
    from ib.ledger.projects import MemoryProjectRegistryStore

    for method in ("load", "list_active", "create", "update", "disable"):
        assert callable(getattr(ProjectRegistryStore, method, None)), f"端口缺方法 {method}"

    store = MemoryProjectRegistryStore()
    entry = ProjectRegistryEntry(
        project_id="p_x", name="原名", status="active", created_at="t0", updated_at="t0"
    )
    created = store.create(entry)
    assert created.status == "active" and created.name == "原名"

    with pytest.raises(ConflictError):
        store.create(entry)

    # seed：p_x 已存在（不覆盖），p_y 新增（1 条）。
    inserted = store.seed(
        [
            ProjectRegistryEntry(
                project_id="p_x", name="配置名", status="disabled", created_at="t9", updated_at="t9"
            ),
            ProjectRegistryEntry(
                project_id="p_y", name="Y", status="active", created_at="t9", updated_at="t9"
            ),
        ]
    )
    assert inserted == 1
    assert store.load("p_x").name == "原名", "seed 覆盖了既有注册表行（运行期状态被回滚）"

    disabled = store.disable("p_x")
    assert disabled is not None and disabled.status == "disabled"
    # 数据保留：行仍在（软删，不物理删除）。
    assert store.load("p_x") is not None and store.load("p_x").status == "disabled"
    assert {e.project_id for e in store.list_active()} == {"p_y"}
    assert store.disable("p_ghost") is None
    assert store.update(
        ProjectRegistryEntry(
            project_id="p_ghost", name="g", status="active", created_at="t", updated_at="t"
        )
    ) is None


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-005 项目注册表：SQLite / 内存语义一致
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_005_project_registry_memory_sqlite_parity(tmp_path) -> None:
    """US-IB-36 ~ US-IB-37；ADR-37 / IFC-IB-370（同一套端口一致性）。"""
    from ib.core import ProjectRegistryEntry
    from ib.ledger.projects import MemoryProjectRegistryStore, SqliteProjectRegistryStore

    sqlite_store = SqliteProjectRegistryStore(str(tmp_path / "ledger.sqlite3"))
    mem_store = MemoryProjectRegistryStore()

    seed = [
        ProjectRegistryEntry(
            project_id="p_a", name="A", status="active", created_at="t", updated_at="t"
        ),
        ProjectRegistryEntry(
            project_id="p_b", name="B", status="active", created_at="t", updated_at="t"
        ),
    ]
    for store in (sqlite_store, mem_store):
        assert store.seed(seed) == 2
        assert store.seed(seed) == 0, "seed 非幂等"
        assert [e.project_id for e in store.list_active()] == ["p_a", "p_b"]
        store.update(
            ProjectRegistryEntry(
                project_id="p_a", name="A2", status="active", created_at="t", updated_at="t"
            )
        )
        assert store.load("p_a").name == "A2"
        store.disable("p_a")
        assert store.load("p_a").status == "disabled"
        assert [e.project_id for e in store.list_active()] == ["p_b"]


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-006 手写迁移 005：快照单源一致 + kb_default 前向迁移幂等
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_006_project_migration_snapshot_and_rebind_idempotent(tmp_path) -> None:
    """US-IB-40 / AC-IB-40-04；ADR-41 / IFC-IB-377 / OQ-IB-30。

    * `005_projects.sql` 快照与 `schema.project_registry_ddl_script()` **语义同一**；
    * 既有落在 `kb_default` 的 `documents` / `chunks` / `chunk_image` **前向改隶**到
      `project_id`，并为每个项目登记 `kb_id == project_id` 的知识库行；
    * 迁移**幂等**：重放两次结果**逐行一致**（迁移家族纪律：幂等、可前向）。
    """
    from ib.ledger.schema import ensure_schema, project_registry_ddl_script

    snapshot = (_repo_root() / "src" / "deploy" / "migrations" / "005_projects.sql").read_text(
        encoding="utf-8"
    )
    script = project_registry_ddl_script()
    assert _normalize_sql(snapshot) == _normalize_sql(script), "005 快照与 DDL 单源不一致"

    conn = sqlite3.connect(str(tmp_path / "ledger.sqlite3"))
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        ensure_schema(conn)
        conn.execute(
            "INSERT INTO projects (project_id, name, active_collection_version, "
            "embedding_model_id, dim, created_at) "
            "VALUES ('p_x', 'X', '1', 'bge-m3', 1024, '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO kbs (kb_id, project_id, name, created_at) "
            "VALUES ('kb_default', 'p_x', '默认', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO documents (doc_id, project_id, kb_id, doc_name, ext, size_bytes, "
            "content_sha256, status, created_at, updated_at) "
            "VALUES ('d1', 'p_x', 'kb_default', 'a.txt', 'txt', 3, 'h', 'indexed', "
            "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO chunks (chunk_id, doc_id, project_id, kb_id, chunk_index, content_hash, "
            "locator, source_kind, page_or_section, indexed_model, indexed_dim) "
            "VALUES ('c1', 'd1', 'p_x', 'kb_default', 0, 'h', 'l', 'text', 'p1', 'bge-m3', 1024)"
        )
        conn.execute(
            "INSERT INTO chunk_image (image_row_id, project_id, kb_id, doc_id, page_or_section, "
            "image_id, source_kind, locator, doc_name, created_at) "
            "VALUES ('i1', 'p_x', 'kb_default', 'd1', 'p1', 'img', 'embedded_image', 'p1:i1', "
            "'a.txt', '2026-01-01T00:00:00Z')"
        )
        conn.commit()

        conn.executescript(script)
        first = _kb_snapshot(conn)
        conn.executescript(script)  # 重放：幂等
        second = _kb_snapshot(conn)
    finally:
        conn.close()

    assert first == second, "005 前向迁移非幂等（重放改变了结果）"
    assert first["documents"] == [("d1", "p_x")], first["documents"]
    assert first["chunks"] == [("c1", "p_x")], first["chunks"]
    assert first["chunk_image"] == [("i1", "p_x")], first["chunk_image"]
    assert ("p_x", "p_x") in first["kbs"], f"未为项目登记 kb_id == project_id 的知识库行：{first['kbs']}"


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-007 LLM 未配置态：缺 Key 非致命，其余必填项仍 fail-fast
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_007_startup_missing_llm_key_is_not_fatal() -> None:
    """US-IB-39 / AC-IB-39-02；ADR-39 **Option C** / IFC-IB-369 / OI-2（用户裁决 2026-10-07）。

    破除首启死锁：Key 载体改为 DB、唯一写入口是管理端点，故**缺 Key 不得阻断启动**；
    但**其余必填项仍 fail-fast**（不放宽）。`LlmConfig.api_key_env` 键名**不删**（语义降级为
    「历史 / 兼容登记」）。
    """
    from ib.config import (
        IB_RUNTIME_ENV_KEYS,
        ConfigurationResolver,
        DictConfigurationSource,
        LlmConfig,
    )

    base = {
        "offline_mode": False,
        "vectorstore": {"backend": "memory"},
        "embedding": {"backend": "fake"},
        "llm": {"backend": "openai_compatible", "api_key_env": "IB_LLM_API_KEY"},
    }

    # 空 env（无 IB_LLM_API_KEY）→ **零错误**：缺 LLM Key 非致命。
    assert ConfigurationResolver(DictConfigurationSource(dict(base))).validate(env={}) == []

    # 键名不删：字段仍在且登记在运行期键集合内。
    assert LlmConfig.api_key_env == "IB_LLM_API_KEY"
    assert "IB_LLM_API_KEY" in set(IB_RUNTIME_ENV_KEYS)

    # 其余必填仍 fail-fast：qdrant 缺 URL / http embedding 缺 URL。
    qdrant = {**base, "vectorstore": {"backend": "qdrant"}}
    errs = ConfigurationResolver(DictConfigurationSource(qdrant)).validate(env={})
    assert errs and "IB_QDRANT_URL" in " ".join(str(e) for e in errs), errs

    http_embedding = {**base, "embedding": {"backend": "http"}}
    resolver = ConfigurationResolver(DictConfigurationSource(http_embedding))
    assert resolver.validate(env={}), "http embedding 缺 IB_EMBED_URL 却未 fail-fast"
    assert resolver.validate(env={"IB_EMBED_URL": "http://127.0.0.1:1"}) == []


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-008 users.project_id 无唯一约束（OQ-IB-28「零迁移」；1:N）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_008_accounts_project_id_has_no_unique_constraint(tmp_path) -> None:
    """US-IB-37 / AC-IB-37-03；OQ-IB-28 / ADR-21-R1（N:1）/ ADR-40 ③。

    「零迁移」= DB 侧**不**加 `users.project_id` 唯一约束。本用例同时做**结构断言**
    （唯一约束只在 `username` 上）与**功能断言**（同一项目可建多个账号）。
    """
    from ib.ledger.accounts import SqliteAccountStore
    from ib.ledger.schema import ACCOUNT_DDL_STATEMENTS

    users_ddl = next(
        s
        for s in ACCOUNT_DDL_STATEMENTS
        if s.strip().upper().startswith("CREATE TABLE IF NOT EXISTS USERS")
    )
    project_line = next(
        line for line in users_ddl.splitlines() if line.strip().startswith("project_id")
    )
    assert "UNIQUE" not in project_line.upper(), (
        f"users.project_id 被加上唯一约束（OQ-IB-28 零迁移被破坏）：{project_line!r}"
    )
    assert "UNIQUE" in users_ddl.upper(), "users 表丢失 username 唯一约束"

    store = SqliteAccountStore(str(tmp_path / "ledger.sqlite3"))
    try:
        first = store.create_user("ops_1", "hash", "ops", "p_x")
        second = store.create_user("ops_2", "hash", "ops", "p_x")
        assert first.project_id == second.project_id == "p_x"
        assert first.user_id != second.user_id
        assert {u.username for u in store.list_users("p_x")} == {"ops_1", "ops_2"}
    finally:
        store.close()


# --------------------------------------------------------------------------- #
# TC-UNIT-R18-009 台账权限位必须保留 group 位（DEFECT-R18-01 回归锁）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R18_009_ledger_mode_keeps_group_share(tmp_path) -> None:
    """REQ-NFR-IB-20 / B22；DEFECT-R18-01 回归锁。

    台账**不是**单进程私有文件：`ib-web`（属主）与 `ib-worker`（**非属主**，靠共同组
    `ib`）**两个**服务账号共享读写。把权限位收成 `0600` 会摘掉 group 位，令 `ib-worker`
    启动即 `sqlite3.OperationalError: unable to open database file`；其单元为
    `Restart=always`，故表现为**无限重启**，而 `ib-web` 与健康检查**全部正常**
    —— 2026-10-07 生产事故的完整成因。

    本用例把「**group 位不得为 0**」钉成回归项：将来任何人再把它收紧到 `0600`，
    这里必红。权限位先按**常量**核（任何平台都真跑），再在 POSIX 上核对文件系统上的
    实际位（Windows 的 `os.chmod` 只有只读位语义，表达不了 `0660`）。
    """
    from ib.ledger.llm_key import LEDGER_FILE_MODE, SqliteLlmKeyStore

    mode = LEDGER_FILE_MODE
    assert mode == 0o660, f"台账权限位常量应为 0660，实得 {oct(mode)}"
    # 逐位断言：即便将来只改常量，也让「group 位被摘」这一失败语义单独可读
    assert mode & stat.S_IRGRP, "group 读位被摘 → ib-worker 打不开台账（DEFECT-R18-01）"
    assert mode & stat.S_IWGRP, "group 写位被摘 → ib-worker 无法写入台账"
    assert not mode & stat.S_IROTH, "other 位应被去掉（REQ-NFR-IB-20 的收紧意图）"
    assert mode != 0o600, "台账不可为 0600（DEFECT-R18-01）"

    if os.name != "posix":
        pytest.skip("POSIX 权限位语义：Windows 的 chmod 表达不了 0660（常量断言已在上方跑过）")

    db_path = tmp_path / "ledger.sqlite3"
    store = SqliteLlmKeyStore(str(db_path))
    try:
        on_disk = stat.S_IMODE(os.stat(db_path).st_mode)
        assert on_disk == 0o660, f"台账实际权限位应为 0660，实得 {oct(on_disk)}"
        # 幂等：二次构造不得翻转模式（ib-worker 侧 chmod 会 EPERM 静默吸收）
        SqliteLlmKeyStore(str(db_path)).close()
        assert stat.S_IMODE(os.stat(db_path).st_mode) == 0o660, "二次装配翻转了台账权限位"
    finally:
        store.close()
