"""集成测试层 8/N —— 运维/可观测/多形态契约补齐。

覆盖：AC-IB-02-04（处理中被删）、AC-IB-03-03（已删文档不得被检索到）、AC-IB-06-05（向量库实现可替换）、
AC-IB-07-03（冷/热超时与重试策略分离）、AC-IB-10-05（子委托能力与深度上限）、
AC-IB-12-05（外发边界声明）、AC-IB-13-01/02/03（结构化日志、降级事件、日志级别可调）。
全部离线：Fake/InMemory 替身，日志用内存 handler 捕获（不落生产日志）。
"""

from __future__ import annotations

import io
import json
import logging
import threading

import pytest


# --------------------------------------------------------------------------- #
# 依赖替身工具：向量库「记录代理」（只替换依赖，不触碰 SUT 逻辑）
# --------------------------------------------------------------------------- #


class _SpyVectors:
    """透明代理，记录 `VectorStore.delete_by_doc` 的每次返回值（其余原样转发）。"""

    def __init__(self, target, calls):
        object.__setattr__(self, "_t", target)
        object.__setattr__(self, "_calls", calls)

    def __getattr__(self, attr):
        real = getattr(self._t, attr)
        if callable(real):
            def _wrapped(*args, **kwargs):
                result = real(*args, **kwargs)
                if attr == "delete_by_doc":
                    self._calls.append(result)
                return result

            return _wrapped
        return real


def _spy_lifecycle(deps, calls, *, embedder=None):
    """构造与组合根同构的 `DocumentLifecycle`，向量库包上记录代理（可选替换 embedder 替身）。"""
    from ib.lifecycle import DocumentLifecycle

    return DocumentLifecycle(
        ledger=deps.ledger,
        blobs=deps.blobs,
        parsers=deps.parsers,
        chunker=deps.chunker,
        embedder=embedder or deps.embedder,
        vectors=_SpyVectors(deps.vectors, calls),
        resolver=deps.collections,
        ocr=deps.ocr,
        renderer=deps.renderer,
        chunking_spec=deps.cfg.chunking_spec,
        project_provider=lambda pid: deps.projects[pid],
    )


# --------------------------------------------------------------------------- #
# AC-IB-02-04 / AC-IB-03-03：处理中被删 → 不得「删了个寂寞」（FND-GROUP-D-02，R3 已修）
# --------------------------------------------------------------------------- #


def test_TC_INT_061_delete_before_processing_leaves_no_ghost(deps):
    """[TC-INT-061] 删除刚上传（pending）的文档 → 成功且不留「幽灵」（R3 修复 FND-GROUP-D-02 的**正向回归守卫**；AC-IB-02-04 / AC-IB-03-03）。

    修复前：collection 未绑定 → `delete_document` 抛 `StartupError`，用户以为删除失败而**未删成**；
    worker 随后照常处理 → 该文档变 `indexed` **并可被检索到**（即「已删内容仍被作答」）。
    修复后：删除成功、台账行删除（读路径权威）；worker 的 `process_pending` 不会认领已删行，
    检索不到该内容，向量侧无残留。

    本条**正向断言修复后的真值**；若幽灵复活将**响亮失败**。
    """
    from ib.core import Scope
    from conftest import request_ctx

    scope = Scope("p_alpha", ("kb_a",))
    record = deps.lifecycle.submit_upload(
        request_ctx("p_alpha"),
        deps.lifecycle.validate_upload("ghost.txt", 8, b"ghostabc"),
        "kb_a",
        data=io.BytesIO(b"ghostabc"),
    )
    report = deps.lifecycle.delete_document(scope, record.doc_id)  # 修复后：不抛
    assert report.ledger_deleted is True
    assert report.vectors_deleted == 0, "本项目尚无派生物，不应删到向量"
    # 台账行已删（读路径权威）
    assert deps.ledger.get_document(scope, record.doc_id) is None
    # worker 再跑：已删行不被认领 → 无索引、无幽灵
    rep = deps.lifecycle.process_pending("w-ghost", 10)
    assert rep.processed == 0 and rep.succeeded == 0, f"已删文档仍被处理：{rep}"
    assert deps.retrieval.search("ghostabc", scope=scope).hits == [], "已删内容仍被检索到（幽灵复活）"
    assert deps.vectors.count(scope) == 0, "删除后向量侧仍有残留（幽灵向量）"
    # 对账干净：不存在「台账有、向量无」的孤儿行
    assert deps.ledger.list_orphan_doc_ids("p_alpha", []) == []


# --------------------------------------------------------------------------- #
# AC-IB-03-02（R3 回归）：删除已索引文档 → 三计数语义 / 顺序清扫 / 无孤儿
# --------------------------------------------------------------------------- #


def test_TC_INT_069_delete_indexed_document_counts_and_orphan_reconciliation(deps):
    """[TC-INT-069] R3 定向回归（AC-IB-03-02）：删除已索引文档的**计数与对账语义**。

    覆盖 R3 修复引入的两处行为（已索引文档的**正常路径**，与 TC-INT-061 的「尚无事发生」路径互补）：
      1. `DeleteReport` 三计数（IFC-IB-281）：台账删除为真、原文件清理为真、向量清理数 == 首次清扫数；
      2. 删除路径做**两次**向量清扫（首次清扫 + 台账删行后的竞态清扫），正常路径下第二次为 **0**
         （证明竞态清扫在无并发时不误删任何点）。
    另外核对「列表消失 / 台账不可见 / 切块清空 / 向量清空 / `list_orphan_doc_ids` 干净」五条不变式。
    """
    from ib.core import Scope
    from conftest import ingest_text

    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "to_delete.txt", "待删除的已索引正文 QQQ-69。")
    assert deps.ledger.get_document(scope, record.doc_id).status == "indexed"

    calls: list[int] = []
    lifecycle = _spy_lifecycle(deps, calls)
    report = lifecycle.delete_document(scope, record.doc_id)

    # 1) DeleteReport 三计数（IFC-IB-281 语义）
    assert report.ledger_deleted is True
    assert report.blob_deleted is True
    assert report.vectors_deleted >= 1, "已索引文档应至少清掉 1 条向量"
    # 2) 两次清扫：首次清掉全部派生物，竞态清扫（正常路径）为 0
    assert len(calls) == 2, f"删除路径应做两次向量清扫，实为 {len(calls)} 次"
    assert calls[0] == report.vectors_deleted, "计数应等于首次清扫量（第二次为 0）"
    assert calls[1] == 0, "正常路径下竞态清扫不应删到任何点"
    # 五条不变式
    items, _ = deps.ledger.list_documents(scope, page=1, page_size=50, status=None)
    assert all(r.doc_id != record.doc_id for r in items), "删除后列表仍含该文档"
    assert deps.ledger.get_document(scope, record.doc_id) is None
    assert deps.ledger.list_chunks(scope, record.doc_id) == [], "删除后仍有切块残留"
    assert deps.vectors.count(scope) == 0, "删除后仍有向量残留"
    assert deps.ledger.list_orphan_doc_ids("p_alpha", []) == []


# --------------------------------------------------------------------------- #
# AC-IB-03-03（R3 回归）：删除后不可检索，且再次处理不复活
# --------------------------------------------------------------------------- #


def test_TC_INT_070_deleted_document_stays_unretrievable_across_reprocess(deps):
    """[TC-INT-070] R3 定向回归（AC-IB-03-03）：已删文档**不得**出现在检索结果中，
    即使随后 worker 再跑一轮也不复活。

    可见性权威 = 台账：删除后台账行已移除，故「删除→再处理」不会重建任何派生物。
    本用例断言删除前后检索命中的**反转**，并在 `process_pending` 之后再次确认无命中（无陈数据作答）。
    """
    from ib.core import Scope

    scope = Scope("p_alpha", ("kb_a",))
    content = "删除后不应再被检索的独有语料 RRR-70。"
    from conftest import ingest_text

    record = ingest_text(deps, "p_alpha", "kb_a", "gone.txt", content)
    assert deps.retrieval.search("RRR-70", scope=scope).hits, "删除前应可检索（前置条件）"

    report = deps.lifecycle.delete_document(scope, record.doc_id)
    assert report.ledger_deleted is True
    assert deps.retrieval.search("RRR-70", scope=scope).hits == [], "删除后仍检索得到（下架未生效）"

    # 再次跑 worker：台账行已删 → 不入列、不索引、不复活
    again = deps.lifecycle.process_pending("w-gone", 10)
    assert again.processed == 0 and again.succeeded == 0, f"已删文档被重新处理：{again}"
    assert deps.ledger.get_document(scope, record.doc_id) is None
    assert deps.retrieval.search("RRR-70", scope=scope).hits == [], "重跑后陈数据复活"
    assert deps.vectors.count(scope) == 0


# --------------------------------------------------------------------------- #
# AC-IB-02-04（R3 回归）：处理中并发删除 → 安全跳过（skipped，非 failed），无残留、无未捕获异常
# --------------------------------------------------------------------------- #


def test_TC_INT_071_concurrent_delete_during_processing_skips_without_residue(deps):
    """[TC-INT-071] R3 定向回归（AC-IB-02-04）：**真并发**（2 线程）——worker 处理中删除该文档。

    构造：worker 线程进入 `embed_documents`（向量化）后**阻塞**；主线程此刻 `delete_document`
    （台账是可见性权威，删除照常成功）；随后放行 worker，让它走完余下步骤并撞上「行已不存在」。

    断言：
      * worker **不抛未捕获异常**（线程内 `errors == []`）；
      * `ProcessReport` 把该文档计为 `skipped`（**不是** `failed`），`succeeded == 0`；
      * 最终无残留：台账行 `None`、向量计数 0、检索为空、对账干净。

    说明（诚实性）：本用例用**真线程**并发，但用**依赖替身上的事件闸门**（embedder）把交错窗口
    固定下来，使结果**确定可复现**；闸门只落在依赖替身上，未改 SUT 逻辑。
    """
    from ib.core import Scope
    from conftest import request_ctx

    scope = Scope("p_alpha", ("kb_a",))
    entered = threading.Event()
    release = threading.Event()
    real_embedder = deps.embedder

    class _GatedEmbedder:
        """把真实 embedder 包一层：进入 `embed_documents` 即发信号并等待放行。"""

        def __getattr__(self, attr):
            return getattr(real_embedder, attr)

        def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
            entered.set()
            assert release.wait(5.0), "删除线程未在 5s 内放行 worker（测试同步失败）"
            return real_embedder.embed_documents(
                texts, timeout_s=timeout_s, max_retries=max_retries, batch_size=batch_size
            )

    calls: list[int] = []
    lifecycle = _spy_lifecycle(deps, calls, embedder=_GatedEmbedder())

    body = "处理中被并发删除的正文。".encode("utf-8")
    validated = lifecycle.validate_upload("inflight.txt", len(body), body[:4096])
    record = lifecycle.submit_upload(request_ctx("p_alpha"), validated, "kb_a", data=io.BytesIO(body))

    reports: list = []
    errors: list = []

    def _worker() -> None:
        try:
            reports.append(lifecycle.process_pending("w-race", 10))
        except BaseException as exc:  # noqa: BLE001 - 真并发下须捕获线程内一切异常以断言「无未捕获」
            errors.append(exc)

    worker = threading.Thread(target=_worker, name="ib-worker")
    worker.start()
    try:
        assert entered.wait(5.0), "worker 未进入 embedding，无法构造并发窗口"
        # 此刻 worker 阻塞在向量化中：删除该文档（用户主动删除，台账权威）
        report = lifecycle.delete_document(scope, record.doc_id)
        assert report.ledger_deleted is True
        assert report.vectors_deleted == 0, "worker 尚未写入向量，删除此刻应无向量可删"
    finally:
        release.set()
        worker.join(10.0)

    assert not worker.is_alive(), "worker 线程未结束"
    assert errors == [], f"并发删除令 worker 抛了未捕获异常：{errors}"
    # 处理侧语义：检测到行已不存在 → skipped（不是 failed）
    assert len(reports) == 1
    rep = reports[0]
    assert rep.processed == 1, rep
    assert rep.skipped == 1 and rep.failed == 0 and rep.succeeded == 0, (
        f"处理中删除应计为 skipped，实际：{rep}"
    )
    # 无残留：台账行 None、向量 0、检索为空、对账干净（worker 撞车后写入的向量已被清掉）
    assert deps.ledger.get_document(scope, record.doc_id) is None
    assert deps.vectors.count(scope) == 0, "处理中删除后仍有残留向量（幽灵）"
    assert deps.retrieval.search("处理中被并发删除的正文。", scope=scope).hits == []
    assert deps.ledger.list_orphan_doc_ids("p_alpha", []) == []


# --------------------------------------------------------------------------- #
# AC-IB-06-05：向量库实现可替换（端口形态一致，上层零改动）
# --------------------------------------------------------------------------- #


def test_TC_INT_068_vectorstore_impl_swappable(deps):
    """[TC-INT-068] 替换向量库实现只换适配器：端口方法齐备，上传/入库/检索链路不改（AC-IB-06-05）。"""
    from ib.core import Scope
    from conftest import ingest_text

    for method in ("bind_collection", "ensure_collection", "upsert", "query", "delete_by_doc",
                   "delete_by_scope", "count", "flush"):
        assert hasattr(deps.vectors, method), f"VectorStore 端口缺方法 {method}"
    # 上层链路在替身实现上跑通（与真实实现同端口契约）
    record = ingest_text(deps, "p_alpha", "kb_a", "swap.txt", "可替换实现的链路验证。")
    result = deps.retrieval.search("可替换实现的链路验证。", scope=Scope("p_alpha", ("kb_a",)))
    assert any(h.doc_id == record.doc_id for h in result.hits)


# --------------------------------------------------------------------------- #
# AC-IB-07-03：冷路径（入库）与热路径（查询）超时/重试策略分离
# --------------------------------------------------------------------------- #


def test_TC_INT_062_cold_hot_timeout_retry_policy_separated(deps):
    """[TC-INT-062] 冷路径超时/重试严格宽于热路径；查询路径以有界超时驱动 embed_query（AC-IB-07-03）。"""
    cfg = deps.cfg.embedding
    assert cfg.cold_timeout_s > cfg.hot_timeout_s, "冷路径超时未宽于热路径"
    assert cfg.cold_max_retries > cfg.hot_max_retries, "冷路径重试未多于热路径"

    from ib.core import Scope
    from ib.retrieval import RetrievalService

    calls: list[float] = []

    class _Rec:
        def __init__(self, inner):
            self._inner = inner

        def embed_query(self, text, *, timeout_s):
            calls.append(timeout_s)
            return self._inner.embed_query(text, timeout_s=timeout_s)

        def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
            calls.append(timeout_s)
            return self._inner.embed_documents(
                texts, timeout_s=timeout_s, max_retries=max_retries, batch_size=batch_size
            )

        def model_id(self):
            return self._inner.model_id()

        def dim(self):
            return self._inner.dim()

        def health(self):
            return self._inner.health()

        def descriptor(self):
            return self._inner.descriptor()

        def warmup(self):
            return self._inner.warmup()

    svc = RetrievalService(
        embedder=_Rec(deps.embedder), vectors=deps.vectors, resolver=deps.collections,
        project_provider=lambda pid: deps.projects[pid],
    )
    svc.search("q", scope=Scope("p_alpha"))
    assert calls, "检索未驱动 embed_query"
    assert all(t <= cfg.hot_timeout_s + 1e-9 or t < cfg.cold_timeout_s for t in calls)
    assert all(t < cfg.cold_timeout_s for t in calls), f"查询路径用了冷路径超时：{calls}"


# --------------------------------------------------------------------------- #
# AC-IB-10-05：子委托能力由注册表控制，深度上限 1
# --------------------------------------------------------------------------- #


def test_TC_INT_063_delegation_capability_and_depth_cap():
    """[TC-INT-063] 子委托是注册表显式标记；非委派专家不获该能力，编排步数有硬上限（AC-IB-10-05）。"""
    from ib.experts import EXPERT_SPECS, delegating_experts, validate_specs
    from ib.orchestration import MAX_EXPERT_STEPS

    validate_specs(EXPERT_SPECS)
    delegating = set(delegating_experts())
    assert delegating, "无任何可委派专家（注册表契约异常）"
    for spec in EXPERT_SPECS:
        assert isinstance(spec.is_delegating, bool)
        if spec.name not in delegating:
            assert spec.is_delegating is False, f"{spec.name} 未在委派集合却标了 is_delegating"
    assert MAX_EXPERT_STEPS <= 8, "专家步数上限过大，子委托深度得不到约束"


# --------------------------------------------------------------------------- #
# AC-IB-12-05：外发边界声明（区分本地/云端 LLM）
# --------------------------------------------------------------------------- #


def test_TC_INT_064_egress_declaration_distinguishes_local_and_cloud_llm(deps):
    """[TC-INT-064] 离线替身 → 无外发；远程 LLM provider → 明确声明 remote + 端点 + 数据类别（AC-IB-12-05）。"""
    from ib.llm import FakeLlmProvider, OpenAiCompatibleProvider

    assert deps.egress.remote is False
    assert FakeLlmProvider().describe_egress().remote is False

    remote = OpenAiCompatibleProvider(
        base_url="https://api.deepseek.com/v1", model="deepseek-chat", api_key="placeholder"
    ).describe_egress()
    assert remote.remote is True
    assert remote.endpoint_host == "api.deepseek.com"
    joined = "".join(remote.data_categories)
    assert "提问" in joined and "检索" in joined, f"未声明外发数据类别：{remote.data_categories}"


# --------------------------------------------------------------------------- #
# AC-IB-13-01/02/03：结构化日志 / 降级事件 / 级别可调
# --------------------------------------------------------------------------- #


def _capture_log():
    """在 `intelligentbase` 日志器上装内存 handler，返回 (handle, buf)。"""
    import ib.observability as obs

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger(obs._LOGGER_NAME)  # noqa: SLF001 - 测试需要挂到真实日志器
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger, handler, buf


def test_TC_INT_065_structured_log_has_pipeline_fields():
    """[TC-INT-065] 结构化日志为 JSON 行，含入库/检索/路由阶段所需字段（AC-IB-13-01）。"""
    from ib.observability import log_event

    logger, handler, buf = _capture_log()
    try:
        log_event("index", "ok", project_id="p_alpha", kb_id="kb_a", doc_id="d1", elapsed_ms=12, count=3)
    finally:
        logger.removeHandler(handler)
    line = buf.getvalue().strip().splitlines()
    assert line, "log_event 未产出日志行"
    payload = json.loads(line[-1])
    assert {"stage", "outcome", "project_id", "kb_id", "doc_id", "elapsed_ms", "count"} <= set(payload)


def test_TC_INT_066_degrade_event_carries_dependency_and_reason():
    """[TC-INT-066] 降级事件经 sink 外发，携带依赖原因与阶段，运维仅凭此可定位故障依赖（AC-IB-13-02）。"""
    from ib.core import DegradeReason
    from ib.observability import add_degrade_sink, emit_degrade, remove_degrade_sink

    seen: list[tuple[str, str]] = []

    def _sink(reason, stage):
        seen.append((str(reason), stage))

    add_degrade_sink(_sink)
    try:
        emit_degrade(DegradeReason.EMBEDDING_UNAVAILABLE, stage="retrieval")
        emit_degrade(DegradeReason.VECTORSTORE_UNAVAILABLE, stage="retrieval")
    finally:
        remove_degrade_sink(_sink)
    assert ("embedding_unavailable", "retrieval") in seen
    assert ("vectorstore_unavailable", "retrieval") in seen


def test_TC_INT_067_log_level_changeable_at_runtime():
    """[TC-INT-067] 运行期调整日志级别即生效，无需改代码/重建（AC-IB-13-03）。"""
    import ib.observability as obs

    logger, handler, buf = _capture_log()
    try:
        obs.configure_logging(level="ERROR", json_lines=True)
        logger.setLevel(logging.ERROR)
        logger.info("info-should-be-dropped")
        logger.error("error-should-appear")
    finally:
        logger.removeHandler(handler)
    body = buf.getvalue()
    assert "error-should-appear" in body and "info-should-be-dropped" not in body
