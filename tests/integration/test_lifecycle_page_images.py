"""集成测试层 2/N —— 入库管线写序（九步）+ 页面图绑定/持久化/级联（M-02 写路径）。

覆盖 IFC-IB-277/278/279/280/281（AC-IB-04-*、AC-IB-16-02、M-02）；离线，真实 SQLite/内存台账。
"""

from __future__ import annotations

from conftest import ingest_text, request_ctx

import pytest


# --------------------------------------------------------------------------- #
# 工具的记录代理（观察真实调用顺序，不改实现）
# --------------------------------------------------------------------------- #


class _Recorder:
    """透明代理：记录「(适配器名, 方法名)」调用序列，其余行为原样转发。"""

    def __init__(self, target, name, log):
        object.__setattr__(self, "_t", target)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_log", log)

    def __getattr__(self, attr):
        real = getattr(self._t, attr)
        if callable(real):
            def _wrapped(*args, **kwargs):
                self._log.append((self._name, attr))
                return real(*args, **kwargs)

            return _wrapped
        return real


def _fresh_lifecycle(deps, *, embedder=None, vectors=None, ledger=None, log=None):
    """用记录代理包住依赖，构造一个与组合根同构的 DocumentLifecycle。"""
    from ib.lifecycle import DocumentLifecycle

    log = log if log is not None else []
    return DocumentLifecycle(
        ledger=_Recorder(ledger or deps.ledger, "ledger", log),
        blobs=deps.blobs,
        parsers=deps.parsers,
        chunker=deps.chunker,
        embedder=_Recorder(embedder or deps.embedder, "embedder", log),
        vectors=_Recorder(vectors or deps.vectors, "vectors", log),
        resolver=deps.collections,
        ocr=deps.ocr,
        renderer=deps.renderer,
        chunking_spec=deps.cfg.chunking_spec,
        project_provider=lambda pid: deps.projects[pid],
    ), log


# --------------------------------------------------------------------------- #
# IFC-IB-280 九步写序
# --------------------------------------------------------------------------- #


def test_TC_INT_010_write_order_vector_then_images_then_chunks_then_mark(deps):
    """[TC-INT-010] 写序不变式：向量 upsert → 页面图持久化 → 块元数据 → 置位（IFC-IB-278/280）。"""
    from ib.core import Scope
    import io

    lifecycle, log = _fresh_lifecycle(deps)
    ctx = request_ctx("p_alpha")
    body = "设备台账：冷冻水泵 3 台。运行记录见附录。"
    validated = lifecycle.validate_upload("ledger.txt", len(body.encode()), body.encode()[:4096])
    lifecycle.submit_upload(ctx, validated, "kb_a", data=io.BytesIO(body.encode()))
    report = lifecycle.process_pending("w-order", 10)
    assert report.succeeded == 1 and report.failed == 0

    def first(name, method):
        for i, entry in enumerate(log):
            if entry == (name, method):
                return i
        raise AssertionError(f"未观察到调用 {name}.{method}；实际序列：{log}")

    e = first("embedder", "embed_documents")
    u = first("vectors", "upsert")
    ci = first("ledger", "upsert_chunk_images")
    c = first("ledger", "upsert_chunks")
    m = first("ledger", "mark_indexed")
    assert e < u, "向量化必须发生在写库之前"
    assert u < ci, "页面图关联必须在向量写入之后（IFC-IB-278）"
    assert ci < c, "页面图关联必须在块元数据之前"
    assert c < m, "置位必须是最后一步（ADR-07：先向量后台账）"
    # 置位之后不得再有任何写入
    assert not any(entry[1] in {"upsert", "upsert_chunks", "upsert_chunk_images"} for entry in log[m + 1:]), log


def test_TC_INT_011_process_pending_empty_queue_and_state(deps):
    """[TC-INT-011] 空队列 → 全零报告（不抛）；处理成功后状态机落到 indexed。"""
    from ib.core import Scope

    empty = deps.lifecycle.process_pending("w-empty", 10)
    assert (empty.processed, empty.succeeded, empty.failed, empty.skipped) == (0, 0, 0, 0)

    record = ingest_text(deps, "p_alpha", "kb_a", "state.txt", "状态机验证内容。")
    got = deps.ledger.get_document(Scope("p_alpha", ("kb_a",)), record.doc_id)
    assert got.status == "indexed" and got.chunk_count >= 1


# --------------------------------------------------------------------------- #
# IFC-IB-277 / 279 页面图绑定（纯函数 + 幂等键）
# --------------------------------------------------------------------------- #


def _image_doc(doc_id="doc-x"):
    from ib.core import ParsedChunk, ParsedDocument

    return ParsedDocument(
        chunks=[
            ParsedChunk("第 2 页图 1 的 OCR 文本", "p2", "image_ocr", "p2:i1", image_ref="r1"),
            ParsedChunk("第 1 页正文", "p1", "text", "p1:t1"),
            ParsedChunk("第 2 页图 2 的 OCR 文本", "p2", "image_ocr", "p2:i2", image_ref="r2"),
            ParsedChunk("第 1 页图 1 的 OCR 文本", "p1", "image_ocr", "p1:i1", image_ref="r3"),
            ParsedChunk("整页扫描", "p3", "page_scan", "p3:s1", image_ref="r4"),
        ],
        page_count=3,
    )


def test_TC_INT_012_bind_page_images_aggregation_determinism(deps):
    """[TC-INT-012] 按 page_or_section 聚合；image_id 确定性派生；同输入同输出（IFC-IB-277/279）。"""
    from ib.core import ChunkImageRecord
    from ib.lifecycle import bind_page_images, image_id_for

    doc = _image_doc()
    first = bind_page_images(doc, doc_id="doc-x")
    second = bind_page_images(doc, doc_id="doc-x")
    assert [b.page_or_section for b in first] == ["p1", "p2", "p3"], "未按 page_or_section 升序聚合"
    # p1 一页两图（正文块不算图），p2 两图，p3 一图
    assert [len(b.images) for b in first] == [1, 2, 1]
    # 页内按 image_id 升序
    p2 = next(b for b in first if b.page_or_section == "p2")
    assert [i.image_id for i in p2.images] == sorted(i.image_id for i in p2.images)
    # 确定性：两次绑定逐字段相等
    assert [(b.page_or_section, tuple(i.image_id for i in b.images)) for b in first] == \
           [(b.page_or_section, tuple(i.image_id for i in b.images)) for b in second]
    # 纯函数无归属（身份由 persist 用 scope 补全）
    assert all(b.project_id == "" and b.kb_id == "" for b in first)
    # image_id 是确定性派生（非随机/自增），且与 idempotent_key 的键空间一致
    assert image_id_for("doc-x", "p2", "p2:i1") == image_id_for("doc-x", "p2", "p2:i1")
    assert ChunkImageRecord.idempotent_key("p", "k", "d", "p2", "img-1") == ("p", "k", "d", "p2", "img-1")
    # 字节引用诚实为空（R1 解析器未落盘）
    assert all(i.blob_ref is None for b in first for i in b.images)


def test_TC_INT_013_persist_page_images_idempotent_and_stale_purged(deps):
    """[TC-INT-013] 持久化幂等；二次解析图变少 → 陈旧关联清除（IFC-IB-281 零改动不变式）。"""
    from ib.core import Scope
    from ib.lifecycle import bind_page_images

    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "scan.txt", "占位正文。")
    doc = _image_doc(record.doc_id)

    n1 = deps.lifecycle.persist_page_images(scope, record.doc_id, bind_page_images(doc, doc_id=record.doc_id))
    n2 = deps.lifecycle.persist_page_images(scope, record.doc_id, bind_page_images(doc, doc_id=record.doc_id))
    assert n1 == n2 == 4, f"幂等重跑行数应一致，得到 {n1}/{n2}"
    assert len(deps.ledger.list_chunk_images(scope, record.doc_id)) == 4

    # 新版本只剩 1 图 → 陈旧 3 行必须清除
    from ib.core import ParsedChunk, ParsedDocument

    smaller = ParsedDocument(
        chunks=[ParsedChunk("只剩一图", "p1", "image_ocr", "p1:i1", image_ref="r")],
        page_count=1,
    )
    n3 = deps.lifecycle.persist_page_images(scope, record.doc_id, bind_page_images(smaller, doc_id=record.doc_id))
    assert n3 == 1
    rows = deps.ledger.list_chunk_images(scope, record.doc_id)
    assert len(rows) == 1, "陈旧页面图关联未清除"


def test_TC_INT_014_delete_cascades_page_images(deps):
    """[TC-INT-014] 删除文档 → 页面图关联级联清除，DeleteReport 三计数语义不变（IFC-IB-281）。"""
    from ib.core import Scope
    from ib.lifecycle import bind_page_images

    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "cascade.txt", "级联验证正文。")
    deps.lifecycle.persist_page_images(scope, record.doc_id, bind_page_images(_image_doc(record.doc_id), doc_id=record.doc_id))
    assert deps.ledger.list_chunk_images(scope, record.doc_id)

    report = deps.lifecycle.delete_document(scope, record.doc_id)
    assert report.ledger_deleted is True
    assert deps.ledger.list_chunk_images(scope, record.doc_id) == [], "doc 删除后仍有页面图关联残留"
    # 删除后该行对读路径不可见（get_document 返回 None）
    assert deps.ledger.get_document(scope, record.doc_id) is None


# --------------------------------------------------------------------------- #
# §6.4 文档级失败隔离
# --------------------------------------------------------------------------- #


def test_TC_INT_015_document_failure_does_not_stop_batch(deps):
    """[TC-INT-015] 单文档失败不中断本批：一篇失败、一篇成功（§6.4）。"""
    from ib.core import Scope
    import io

    class _FlakyEmbedder:
        def __init__(self, inner):
            self._inner = inner

        def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
            if any("BOOM" in t for t in texts):
                raise RuntimeError("注入的嵌入故障")
            return self._inner.embed_documents(texts, timeout_s=timeout_s, max_retries=max_retries, batch_size=batch_size)

        def embed_query(self, text, *, timeout_s):
            return self._inner.embed_query(text, timeout_s=timeout_s)

        def model_id(self):
            return self._inner.model_id()

        def dim(self):
            return self._inner.dim()

        def health(self):
            return self._inner.health()

        def warmup(self, *, timeout_s=0.0):
            return True

    lifecycle, _ = _fresh_lifecycle(deps, embedder=_FlakyEmbedder(deps.embedder))
    ctx = request_ctx("p_alpha")
    for name, text in (("good.txt", "正常内容 GOOD。"), ("bad.txt", "含 BOOM 标记的内容。")):
        validated = lifecycle.validate_upload(name, len(text.encode()), text.encode()[:4096])
        lifecycle.submit_upload(ctx, validated, "kb_a", data=io.BytesIO(text.encode()))

    report = lifecycle.process_pending("w-flaky", 10)
    assert report.processed == 2
    assert report.succeeded >= 1 and report.failed >= 1, f"未实现失败隔离：{report}"
    # 失败文档落到 failed 且带错误码，成功文档不受影响
    scope = Scope("p_alpha", ("kb_a",))
    items, _ = deps.ledger.list_documents(scope, page=1, page_size=50, status=None)
    by_name = {r.doc_name: r for r in items}
    assert "good.txt" in by_name and "bad.txt" in by_name
    assert by_name["bad.txt"].status == "failed" and by_name["bad.txt"].error_code
    assert by_name["good.txt"].status == "indexed"


def test_TC_INT_016_retry_only_from_failed(deps):
    """[TC-INT-016] 人工重试仅接受 failed → pending；对非 failed 报 409（IFC-IB-245）。"""
    from ib.core import ConflictError, Scope
    import io

    class _AlwaysFail:
        def __init__(self, inner):
            self._inner = inner

        def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
            raise RuntimeError("恒定失败")

        def embed_query(self, text, *, timeout_s):
            return self._inner.embed_query(text, timeout_s=timeout_s)

        def model_id(self):
            return self._inner.model_id()

        def dim(self):
            return self._inner.dim()

        def health(self):
            return self._inner.health()

    lifecycle, _ = _fresh_lifecycle(deps, embedder=_AlwaysFail(deps.embedder))
    ctx = request_ctx("p_alpha")
    body = "重试验证。"
    validated = lifecycle.validate_upload("retry.txt", len(body.encode()), body.encode()[:4096])
    record = lifecycle.submit_upload(ctx, validated, "kb_a", data=io.BytesIO(body.encode()))
    lifecycle.process_pending("w-retry", 10)
    scope = Scope("p_alpha", ("kb_a",))
    assert deps.ledger.get_document(scope, record.doc_id).status == "failed"

    updated = lifecycle.retry_document(scope, record.doc_id)
    assert updated.status == "pending"
    # 已 pending（非 failed）→ 409
    with pytest.raises(ConflictError):
        lifecycle.retry_document(scope, record.doc_id)
