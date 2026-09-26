"""单元测试层 3/N —— ib_embed 配置/内核、Embedder 三形态、台账（状态机/租约/页面图关联）。

覆盖 AC-IB-06-04、AC-IB-07-01/02、AC-IB-10-*（间接）、AC-IB-16-02、R2 契约 IFC-IB-266~286（部分）；
台账用例刻意用**真实 SQLite**（租约的条件 UPDATE 语义只在真库上成立）。
"""

from __future__ import annotations

import io
import os
import tempfile

import pytest

# --------------------------------------------------------------------------- #
# MOD-IB-26 ib-embed 配置（IFC-IB-274；契约 §1.2）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_043_ib_embed_config_keys_closed_set():
    """[TC-UNIT-043] 恰 11 个 IB_EMBED_* 键，闭集不得增删。"""
    from ib_embed.config import DEFAULT_KEYS

    expected = {
        "IB_EMBED_HOST", "IB_EMBED_PORT", "IB_EMBED_MODEL_ID", "IB_EMBED_DIM",
        "IB_EMBED_MODEL_PATH", "IB_EMBED_MAX_BATCH", "IB_EMBED_MAX_TOKENS",
        "IB_EMBED_MAX_CONCURRENCY", "IB_EMBED_QUEUE_DEPTH", "IB_EMBED_THREADS",
        "IB_EMBED_MEMORY_LIMIT_MB",
    }
    assert set(DEFAULT_KEYS) == expected
    assert len(DEFAULT_KEYS) == 11


def test_TC_UNIT_044_ib_embed_missing_model_path_reports_key_only():
    """[TC-UNIT-044] 缺 IB_EMBED_MODEL_PATH 即拒绝启动，且只报键名不回显值（IFC-IB-274）。"""
    from ib_embed.config import ConfigError, load_config

    with pytest.raises(ConfigError) as exc:
        load_config({})
    assert "IB_EMBED_MODEL_PATH" in str(exc.value)

    # 非法整数：只报键名
    with pytest.raises(ConfigError) as exc2:
        load_config({"IB_EMBED_MODEL_PATH": "/opt/bge-m3", "IB_EMBED_DIM": "not-int-9999"})
    assert "IB_EMBED_DIM" in str(exc2.value)
    assert "not-int-9999" not in str(exc2.value)


def test_TC_UNIT_045_ib_embed_consumes_only_ib_keys():
    """[TC-UNIT-045] 只读 IB_EMBED_* 前缀；客户端键不得被误当服务端配置。"""
    from ib_embed.config import load_config

    cfg = load_config({"IB_EMBED_MODEL_PATH": "/opt/bge-m3", "IB_EMBED_URL": "http://x"})
    assert cfg.model_path == "/opt/bge-m3"
    assert cfg.model_id == "bge-m3" and cfg.dim == 1024
    # 客户端键（IB_EMBED_URL）不在服务端 DEFAULT_KEYS 闭集内，不得出现在配置面上
    assert not hasattr(cfg, "url")
    # as_loggable 无凭据/无敏感项；模型权重路径亦不应进入日志
    loggable = cfg.as_loggable()
    credentialish = {"api_key", "token", "secret", "password", "credential", "authorization"}
    assert not (credentialish & set(loggable)), f"日志字段含凭据类键：{sorted(set(loggable))}"
    assert "model_path" not in loggable, "模型权重路径不应进入可日志字段"


# --------------------------------------------------------------------------- #
# MOD-IB-26 ib-embed 运行时替身（IFC-IB-275/277 相关）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_046_fake_runtime_deterministic_and_normalized():
    """[TC-UNIT-046] 服务端替身：确定性、归一化、保序、未加载即 503 语义。"""
    from ib_embed.runtime import FakeRuntime, InferenceUnavailable

    runtime = FakeRuntime(dim=64, model_id="fake-bge-m3")
    with pytest.raises(InferenceUnavailable):
        runtime.embed(["x"], batch_size=1, max_tokens=8)  # 未加载
    runtime.load()
    batch1 = runtime.embed(["甲乙", "丙丁"], batch_size=8, max_tokens=8)
    batch2 = runtime.embed(["甲乙", "丙丁"], batch_size=8, max_tokens=8)
    assert batch1.vectors == batch2.vectors, "同输入两次结果不一致（非确定性）"
    assert len(batch1.vectors) == 2 and all(len(v) == 64 for v in batch1.vectors)
    for vec in batch1.vectors:
        norm = sum(float(v) * float(v) for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6
    # 保序：反转入参 → 反转出参
    rev = runtime.embed(["丙丁", "甲乙"], batch_size=8, max_tokens=8).vectors
    assert rev == tuple(reversed(batch1.vectors))


def test_TC_UNIT_047_fake_runtime_load_failure():
    """[TC-UNIT-047] 权重加载失败 → InferenceUnavailable（可读错误，非崩溃）。"""
    from ib_embed.runtime import FakeRuntime, InferenceUnavailable

    runtime = FakeRuntime(dim=8)
    runtime.fail_next_load()
    with pytest.raises(InferenceUnavailable):
        runtime.load()


# --------------------------------------------------------------------------- #
# MOD-IB-09 Embedder 三形态（AC-IB-07-01/02；契约 §8 形态可逆）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_048_fake_embedder_cold_hot_self_similarity():
    """[TC-UNIT-048] 冷/热两路径同文向量自相似≈1（AC-IB-07-02）。"""
    from ib.embedding import FakeEmbedder, cosine

    embedder = FakeEmbedder(dim=256, model_id="fake-bge-m3")
    docs = embedder.embed_documents(["某段业务文本"], timeout_s=1.0, max_retries=1, batch_size=4)
    query = embedder.embed_query("某段业务文本", timeout_s=1.0)
    assert len(docs) == 1 and len(query) == 256
    assert cosine(docs[0], query) == pytest.approx(1.0, abs=1e-9)
    # 不同文本相似度显著更低
    other = embedder.embed_query("完全不同的词汇组合", timeout_s=1.0)
    assert cosine(query, other) < 0.99


def test_TC_UNIT_049_embedder_descriptor_five_fields():
    """[TC-UNIT-049] descriptor 恰五字段且 dim 与声明一致（各形态一致）。"""
    from ib.embedding import FakeEmbedder, InProcessBgeM3Embedder

    for impl in (
        FakeEmbedder(dim=1024, model_id="bge-m3"),
        InProcessBgeM3Embedder(model_id="bge-m3", dim=1024, model_path="/nowhere"),
    ):
        descriptor = impl.descriptor()
        assert set(descriptor.__dataclass_fields__) == {"model_id", "dim", "normalized", "max_tokens", "device"}
        assert descriptor.dim == impl.dim() == 1024
        assert descriptor.normalized is True


def test_TC_UNIT_050_inproc_missing_weights_is_readable_error():
    """[TC-UNIT-050] inproc 缺权重目录 → 可读 DependencyUnavailableError 指名键，而非导入崩溃（IFC-IB-275）。"""
    from ib.core import DependencyUnavailableError
    from ib.embedding import InProcessBgeM3Embedder

    broken = InProcessBgeM3Embedder(model_id="bge-m3", dim=1024, environ={})
    with pytest.raises(DependencyUnavailableError) as exc:
        broken.embed_query("x", timeout_s=1.0)
    assert "IB_EMBED_MODEL_PATH" in str(exc.value)


def test_TC_UNIT_051_build_embedder_value_domain_and_default():
    """[TC-UNIT-051] build_embedder 值域 {http,inproc,fake}；未知值回落默认 http。"""
    from ib.embedding import FakeEmbedder, InProcessBgeM3Embedder, LocalHttpEmbedder, build_embedder

    class _Cfg:
        class embedding:
            backend = "inproc"
            dim = 1024
            model_id = "bge-m3"
            url = ""
            cold_timeout_s = 120.0
            cold_max_retries = 3
            cold_batch_size = 16
            hot_timeout_s = 3.0
            hot_max_retries = 1

    assert isinstance(build_embedder(_Cfg()), InProcessBgeM3Embedder)
    _Cfg.embedding.backend = "fake"
    assert isinstance(build_embedder(_Cfg()), FakeEmbedder)
    _Cfg.embedding.backend = "bogus"
    assert isinstance(build_embedder(_Cfg()), LocalHttpEmbedder), "未知值未回落默认 http"


# --------------------------------------------------------------------------- #
# MOD-IB-11 台账：状态机 / 单租约（AC-IB-06-04、AC-IB-16-02）
# --------------------------------------------------------------------------- #


def _project(pid: str):
    from ib.core import ProjectRecord

    return ProjectRecord(
        project_id=pid, name=pid, active_collection_version="1",
        embedding_model_id="bge-m3", dim=1024, created_at="",
    )


def _kb(pid: str, kb_id: str):
    from ib.core import KbRecord

    return KbRecord(kb_id=kb_id, project_id=pid, name=kb_id, created_at="")


def test_TC_UNIT_052_sqlite_ledger_state_machine_and_single_lease():
    """[TC-UNIT-052] SQLite 状态机 pending→indexed + 单租约 + 租约回收（AC-IB-16-02）。"""
    from ib.core import DocStatus, Scope, ScopeViolationError
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    with tempfile.TemporaryDirectory() as tmp:
        repo = SqliteLedgerRepository(os.path.join(tmp, "ledger.sqlite3"))
        try:
            scope = Scope(project_id="p1", kb_ids=("kb1",))
            repo.upsert_project(_project("p1"))
            repo.upsert_kb(_kb("p1", "kb1"))
            # 归属断言：未登记 kb_id 被拒
            with pytest.raises(ScopeViolationError):
                repo.create_document(Scope(project_id="p1", kb_ids=("kb_missing",)), "x.txt", "txt", 1, "h", None)

            doc = repo.create_document(scope, "a.txt", "txt", 11, "sha-a", None)
            assert doc.status == str(DocStatus.PENDING)
            first = repo.claim_pending("w1", 300, 5)
            assert [d.doc_id for d in first] == [doc.doc_id]
            # 第二个 worker 不得重复认领
            assert repo.claim_pending("w2", 300, 5) == []
            repo.mark_indexed(scope, doc.doc_id, "1", 3)
            got = repo.get_document(scope, doc.doc_id)
            assert got is not None and got.status == "indexed" and got.chunk_count == 3
            # 未过期租约不回收
            assert int(repo.reap_expired_leases("2000-01-01T00:00:00Z")) == 0
            # 未注册 kb 的认领：另一篇 -> 过期回收回 pending
            doc2 = repo.create_document(scope, "b.txt", "txt", 5, "sha-b", None)
            assert [d.doc_id for d in repo.claim_pending("w1", 300, 5)] == [doc2.doc_id]
            assert int(repo.reap_expired_leases("2999-01-01T00:00:00Z")) == 1
            healed = repo.get_document(scope, doc2.doc_id)
            assert healed is not None and healed.status == "pending"
        finally:
            repo.close()


def test_TC_UNIT_053_chunk_images_idempotent_and_cascade():
    """[TC-UNIT-053] 页面图关联：幂等重跑 + 陈旧行清除 + doc 删除级联（IFC-IB-279/281）。"""
    from ib.core import ChunkImageRecord, Scope
    from ib.ledger import InMemoryLedgerRepository
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    def _records(scope, doc_id, count):
        return [
            ChunkImageRecord(
                project_id=scope.project_id, kb_id=scope.kb_ids[0], doc_id=doc_id,
                page_or_section=f"p{i}", image_id=f"img-{i}", source_kind="embedded_image",
                locator=f"p{i}:i1", blob_ref=None, doc_name="scan.pdf", created_at="2026-01-01T00:00:00Z",
            )
            for i in range(count)
        ]

    def _exercise(repo, scope):
        repo.upsert_project(_project(scope.project_id))
        repo.upsert_kb(_kb(scope.project_id, scope.kb_ids[0]))
        doc = repo.create_document(scope, "scan.pdf", "pdf", 10, "sha-1", None)
        key = ChunkImageRecord.idempotent_key(scope.project_id, scope.kb_ids[0], doc.doc_id, "p1", "img-x")
        assert key == (scope.project_id, scope.kb_ids[0], doc.doc_id, "p1", "img-x")
        first = _records(scope, doc.doc_id, 3)
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, first)) == 3
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, first)) == 3  # 幂等
        assert len(repo.list_chunk_images(scope, doc.doc_id)) == 3
        # 二次解析变少 → 陈旧行清除
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, _records(scope, doc.doc_id, 1))) == 1
        assert [r.image_id for r in repo.list_chunk_images(scope, doc.doc_id)] == ["img-0"]
        # 跨项目不可见
        assert repo.get_chunk_image(Scope(project_id="other", kb_ids=scope.kb_ids), doc.doc_id, "img-0") is None
        # 删除 → 级联
        repo.mark_deleted(scope, doc.doc_id)
        assert repo.list_chunk_images(scope, doc.doc_id) == []

    _exercise(InMemoryLedgerRepository(), Scope(project_id="p_mem", kb_ids=("kb1",)))
    with tempfile.TemporaryDirectory() as tmp:
        repo = SqliteLedgerRepository(os.path.join(tmp, "ledger.sqlite3"))
        try:
            _exercise(repo, Scope(project_id="p_sql", kb_ids=("kb1",)))
        finally:
            repo.close()


def test_TC_UNIT_054_sqlite_ledger_pragma_on_connect():
    """[TC-UNIT-054] WAL / busy_timeout 是连接级 PRAGMA（必须在连上设置）。"""
    from ib.ledger.schema import PRAGMA_STATEMENTS

    joined = " ".join(PRAGMA_STATEMENTS).lower()
    assert "journal_mode" in joined and "wal" in joined
    assert "busy_timeout" in joined
