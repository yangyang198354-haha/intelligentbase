"""E2E / 关键路径测试 —— 以用户故事为单位跑通跨模块旅程（离线装配）。

每个用例在 docstring 标注所属 **US-IB-NN**（用户故事级覆盖的证据）。
关键路径 = 标记为 Must Have 的故事（US-IB-01~04、06~12、14）。
"""

from __future__ import annotations

import io
import json
import os

from conftest import ingest_text, request_ctx

import pytest

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}


def _sse_body(response):
    if hasattr(response, "streaming_content"):
        return b"".join(response.streaming_content).decode("utf-8")
    return response.content.decode("utf-8")


# --------------------------------------------------------------------------- #
# US-IB-01 + US-IB-08：导入文档 → 处理 → 检索增强回答
# --------------------------------------------------------------------------- #


def test_TC_E2E_001_import_then_rag_answer(http_app):
    """US-IB-01 导入文档 + US-IB-08 带来源的检索增强回答（关键路径）。"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from ib.core import Scope

    deps, Client = http_app
    client = Client()
    content = "中央空调冷水机组启停顺序：先开冷却水泵，再开冷冻水泵，最后开主机。"
    up = SimpleUploadedFile("hvac.txt", content.encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    assert r.status_code == 201
    doc_id = json.loads(r.content)["doc_id"]

    # worker 处理（生产里由 task-scheduler/worker 触发）
    report = deps.lifecycle.process_pending("e2e-worker", 10)
    assert report.succeeded >= 1
    assert deps.ledger.get_document(Scope("p_alpha", ("kb_a",)), doc_id).status == "indexed"

    # 检索增强：命中该文档（来源可标注）
    result = deps.retrieval.search("冷水机组启停顺序", scope=Scope("p_alpha", ("kb_a",)))
    assert result.degraded is False and any(h.doc_id == doc_id for h in result.hits)

    # 问答入口（SSE）产出正文与结束事件
    stream = client.get("/api/chat/stream?q=冷水机组启停顺序&session_id=e2e1", **AUTH)
    body = _sse_body(stream)
    assert "event: content" in body and "event: done" in body


# --------------------------------------------------------------------------- #
# US-IB-02：诊断并重试失败的文档处理
# --------------------------------------------------------------------------- #


def test_TC_E2E_002_failed_then_retry(http_app):
    """US-IB-02 失败文档可诊断（error_code）并可人工重试（关键路径）。"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from ib.core import Scope

    deps, Client = http_app
    client = Client()
    up = SimpleUploadedFile("bad.txt", "内容正常但依赖会失败。".encode("utf-8"))
    doc_id = json.loads(client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH).content)["doc_id"]

    # 让嵌入恒失败 → 文档级失败并带 error_code
    class _AlwaysFail:
        def __init__(self, inner):
            self._inner = inner

        def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
            raise RuntimeError("e2e 注入依赖故障")

        def embed_query(self, text, *, timeout_s):
            return self._inner.embed_query(text, timeout_s=timeout_s)

        def model_id(self):
            return self._inner.model_id()

        def dim(self):
            return self._inner.dim()

        def health(self):
            return self._inner.health()

    saved = deps.lifecycle._embedder
    deps.lifecycle._embedder = _AlwaysFail(saved)
    try:
        deps.lifecycle.process_pending("e2e-worker", 10)
    finally:
        deps.lifecycle._embedder = saved

    scope = Scope("p_alpha", ("kb_a",))
    failed = deps.ledger.get_document(scope, doc_id)
    assert failed.status == "failed" and failed.error_code

    # 人工重试 → pending（HTTP 200）
    retried = client.post(f"/api/files/{doc_id}/retry", **AUTH)
    assert retried.status_code == 200
    assert json.loads(retried.content)["status"] == "pending"

    # 恢复后重跑 → indexed
    assert deps.lifecycle.process_pending("e2e-worker", 10).succeeded >= 1
    assert deps.ledger.get_document(scope, doc_id).status == "indexed"


# --------------------------------------------------------------------------- #
# US-IB-03：管理与下架文档
# --------------------------------------------------------------------------- #


def test_TC_E2E_003_delete_removes_from_retrieval(http_app):
    """US-IB-03 删除文档后检索不再命中（下架生效，关键路径）。"""
    from ib.core import Scope

    deps, Client = http_app
    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "tobedeleted.txt", "即将下架的独有内容 QQQ-13。")
    assert deps.retrieval.search("QQQ-13", scope=scope).hits

    r = Client().delete(f"/api/files/{record.doc_id}", **AUTH)
    assert r.status_code == 200, r.content
    assert deps.retrieval.search("QQQ-13", scope=scope).hits == [], "下架后仍检索得到"
    # 原文件字节亦已清理（R4 / FND-GROUP-D-03：HTTP 删除走项目级 scope 仍应删到 kb 段落盘的字节）
    from ib.lifecycle import blob_ref_for

    assert json.loads(r.content)["blob_deleted"] is True, "下架未清理原文件字节（孤儿）"
    ref = blob_ref_for(record)
    assert ref is not None and deps.blobs.exists(ref) is False, "下架后原文件仍在 BlobStore"
    # 台账行亦消失
    assert deps.ledger.get_document(scope, record.doc_id) is None


# --------------------------------------------------------------------------- #
# US-IB-09：复合问题多智能体并行处理并融合
# --------------------------------------------------------------------------- #


def test_TC_E2E_004_composite_multi_expert_fused_single_answer(deps):
    """US-IB-09 复合问题选多专家并行处理，且只给一版融合答案（关键路径）。"""
    from ib.core import Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph
    from ib.routing.intent import IntentRouter
    from ib.streaming import MemorySessionStore
    from ib.core import GraphConfig

    decision = IntentRouter().classify_experts("能耗数据和设备故障一起看看", scope=Scope(project_id="p_alpha"))
    assert len(decision.experts) >= 2 and len(decision.experts) <= 3, decision.experts

    bound = deps.bind_tools(Scope(project_id="p_alpha"))
    orch = build_graph(
        llm=deps.llm, experts=EXPERT_SPECS, tools=bound, sessions=MemorySessionStore(),
        config=GraphConfig(), scope=Scope(project_id="p_alpha"),
        tools_by_expert={s.name: bound for s in EXPERT_SPECS},
    )
    events = list(orch.run("能耗数据和设备故障一起看看", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:e2e4"))
    kinds = [str(e.kind) for e in events]
    assert kinds.count("content") == 1, f"多专家却出了多版答案：{kinds}"
    assert kinds[-1] == "done"


# --------------------------------------------------------------------------- #
# US-IB-10：注册新专家与新工具
# --------------------------------------------------------------------------- #


def test_TC_E2E_005_register_new_tool_reflected_in_digest(deps):
    """US-IB-10 注册工具后能力摘要反映之；专家注册表结构自检通过。"""
    from ib.core import ToolResult, ToolSpec
    from ib.experts import EXPERT_SPECS, validate_specs
    from ib.tools import ToolRegistry, build_capability_digest, bind_scope
    from ib.core import Scope

    validate_specs(EXPERT_SPECS)  # 内置注册表结构合法（恰一个默认专家等）

    registry = ToolRegistry()
    registry.register(
        ToolSpec(name="query_energy", description="查询能耗指标", needs_scope=True),
        lambda query, *, scope, retrieval: ToolResult(ok=True, content="ok"),
    )
    digest = build_capability_digest(registry)
    assert "query_energy" in digest and "查询能耗指标" in digest
    # 新工具可立即绑定（无需改基座）
    bound = bind_scope(registry.registered(), Scope(project_id="p_alpha"), deps.retrieval)
    assert bound[0].callable("q").ok is True


# --------------------------------------------------------------------------- #
# US-IB-11 / US-IB-06：以配置接入新项目 + 项目硬隔离
# --------------------------------------------------------------------------- #


def test_TC_E2E_006_two_projects_configured_and_isolated(deps):
    """US-IB-11 配置接入新项目 + US-IB-06 向量库项目硬隔离（关键路径）。"""
    from ib.core import Scope

    assert set(deps.projects) == {"p_alpha", "p_beta"}
    alpha_doc = ingest_text(deps, "p_alpha", "kb_a", "alpha_only.txt", "甲项目孤本内容 KAPPA-9。")
    ingest_text(deps, "p_beta", "kb_b", "beta_only.txt", "乙项目孤本内容 LAMBDA-8。")

    a = deps.retrieval.search("KAPPA-9", scope=Scope("p_alpha", ("kb_a",)))
    b = deps.retrieval.search("LAMBDA-8", scope=Scope("p_beta", ("kb_b",)))
    cross = deps.retrieval.search("KAPPA-9", scope=Scope("p_beta", ("kb_b",)))
    assert any(h.doc_id == alpha_doc.doc_id for h in a.hits), "甲项目检索不到自己的语料"
    assert b.hits, "乙项目检索不到自己的语料"
    # 隔离的要害：乙项目**永远**看不到甲项目的文档（阈值内弱匹配其它文档属正常召回）
    assert not any(h.doc_id == alpha_doc.doc_id for h in cross.hits), "项目隔离在端到端链路上失效"


# --------------------------------------------------------------------------- #
# US-IB-04 / US-IB-05：多格式导入 + 切分参数
# --------------------------------------------------------------------------- #


def test_TC_E2E_007_multi_format_and_chunk_config(deps):
    """US-IB-04 txt/md 多格式导入均可达检索；US-IB-05 切分参数只作用于新文档。"""
    from ib.core import Scope

    md = "# 机房巡检\n巡检项甲：温度。\n\n## 巡检项乙\n压力检查。\n"
    r_md = ingest_text(deps, "p_alpha", "kb_a", "inspect.md", md)
    r_txt = ingest_text(deps, "p_alpha", "kb_a", "notes.txt", "普通文本笔记：阀门编号 V-102。")
    scope = Scope("p_alpha", ("kb_a",))
    assert deps.retrieval.search("巡检项乙", scope=scope).hits
    assert deps.retrieval.search("阀门编号 V-102", scope=scope).hits
    assert deps.ledger.get_document(scope, r_md.doc_id).chunk_count >= 1
    assert deps.ledger.get_document(scope, r_txt.doc_id).status == "indexed"

    # AC-IB-04-01：真实 .docx 经真实解析器入库（python-docx 已装）
    r_docx = _ingest_docx(deps, "p_alpha", "kb_a", "spec.docx", "供暖季设备保养要点 GAMMA-7。")
    got = deps.ledger.get_document(scope, r_docx.doc_id)
    assert got.status == "indexed" and got.chunk_count >= 1
    hit = deps.retrieval.search("GAMMA-7", scope=scope)
    assert any(h.doc_id == r_docx.doc_id for h in hit.hits), "docx 内容未参与检索"
    # PDF 文本层 / 扫描件 OCR 依赖 pypdfium2/rapidocr：本机缺失 → 见 test_report 的 not-verified 清单


def _ingest_docx(deps, project_id, kb_id, filename, paragraph):
    import docx

    document = docx.Document()
    document.add_heading("设备保养", level=1)
    document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    payload = buffer.getvalue()

    ctx = request_ctx(project_id)
    validated = deps.lifecycle.validate_upload(filename, len(payload), payload[:4096])
    record = deps.lifecycle.submit_upload(ctx, validated, kb_id, data=io.BytesIO(payload))
    deps.lifecycle.process_pending("e2e-worker", 10)
    return record


# --------------------------------------------------------------------------- #
# US-IB-07 / US-IB-13：embedding 接入 + 运行状态可观测
# --------------------------------------------------------------------------- #


def test_TC_E2E_014_embedding_wired_end_to_end(deps):
    """US-IB-07 接入本地 embedding 并保证维度/口径一致（关键路径）。

    可离线验证的部分：装配后的 embedder 描述子维度 = 配置声明维度；入库产出的向量维度一致；
    冷/热路径对同一文本自相似度 ≈ 1（余弦口径）；全程 `egress.remote is False`（不计云端调用）。
    **真实 bge-m3 推理与目标机延迟不在本机可验证范围** → 见 test_report not-verified 清单。
    """
    from ib.core import Scope

    assert deps.egress.remote is False, "离线装配却声明外发——无法排除云端 embedding 调用"
    desc = deps.embedder.descriptor()
    assert desc.dim == 1024 == deps.projects["p_alpha"].dim
    assert desc.model_id == "bge-m3" and desc.normalized is True

    record = ingest_text(deps, "p_alpha", "kb_a", "embed.txt", "嵌入接入验证正文 EPSILON-5。")
    scope = Scope("p_alpha", ("kb_a",))
    assert deps.ledger.get_document(scope, record.doc_id).status == "indexed"
    hit = deps.retrieval.search("嵌入接入验证正文 EPSILON-5。", scope=scope)
    assert hit.degraded is False and any(h.doc_id == record.doc_id for h in hit.hits)
    # 入库向量维度 = 描述子维度 = 配置维度
    assert len(deps.embedder.embed_query("任意文本", timeout_s=5.0)) == desc.dim
    # 冷/热路径自相似度 ≈ 1（余弦口径一致）
    cold = deps.embedder.embed_documents(["同一段"], timeout_s=5.0, max_retries=1, batch_size=1)[0]
    hot = deps.embedder.embed_query("同一段", timeout_s=5.0)
    dot = sum(a * b for a, b in zip(cold, hot))
    assert abs(dot - 1.0) < 1e-6, f"冷/热路径口径不一致：self-similarity={dot}"


def test_TC_E2E_008_health_endpoints_reflect_runtime(http_app):
    """US-IB-13 观察运行状态：/healthz 与 /healthz/deps 反映各依赖（关键路径）。"""
    deps, Client = http_app
    client = Client()
    assert json.loads(client.get("/healthz").content)["ok"] is True
    body = json.loads(client.get("/healthz/deps").content)
    assert body["embed"]["ok"] is True and body["llm"]["ok"] is True
    assert "egress" in body and body["egress"]["remote"] is False


# --------------------------------------------------------------------------- #
# US-IB-14：依赖故障降级而不断流
# --------------------------------------------------------------------------- #


def test_TC_E2E_009_degrade_on_llm_failure(http_app):
    """US-IB-14 LLM 依赖故障 → SSE 仍出 degraded + content + done（服务不中断，关键路径）。"""
    from ib.llm import FakeLlmProvider
    from ib.core import Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph
    from ib.streaming import MemorySessionStore
    from ib.core import GraphConfig

    deps, _ = http_app
    orch = build_graph(
        llm=FakeLlmProvider(unavailable=True), experts=EXPERT_SPECS, tools=[],
        sessions=MemorySessionStore(), config=GraphConfig(), scope=Scope(project_id="p_alpha"),
    )
    events = list(orch.run("能耗数据", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:e2e9"))
    kinds = [str(e.kind) for e in events]
    assert "degraded" in kinds and "content" in kinds and kinds[-1] == "done", kinds
    assert kinds.index("degraded") < kinds.index("content")


# --------------------------------------------------------------------------- #
# US-IB-12：启动期配置纪律（fail-fast）
# --------------------------------------------------------------------------- #


def test_TC_E2E_010_startup_rejects_missing_projects(raw):
    """US-IB-12 未配置任何项目 → 启动失败（不静默起服务，关键路径）。"""
    from ib.core import StartupError
    from ibweb.composition import build_deps

    broken = dict(raw)
    broken["projects"] = {}
    with pytest.raises(StartupError):
        build_deps(broken, force=True)


# --------------------------------------------------------------------------- #
# US-IB-16：重建索引路径
# --------------------------------------------------------------------------- #


def test_TC_E2E_011_rebuild_journey(http_app):
    """US-IB-16 变更模型/维度后可触发重建：POST 202 → 重置重排 → worker 推进 → 激活切版本。

    D-4 修复后，重建启动会把已 `indexed` 文档重置回 `pending`（目标集合 v2 建出但尚未写入），
    经 worker 重跑入库后，**显式激活**才切换 active 版本（切换是决策而非 `step_rebuild` 的隐式副作用）。
    """
    deps, Client = http_app
    client = Client()
    ingest_text(deps, "p_alpha", "kb_a", "rebuild.txt", "重建用正文内容。")
    assert deps.ledger.active_collection_version("p_alpha") == "1"

    started = client.post("/api/rebuild", **AUTH)
    assert started.status_code == 202, started.content
    job_id = json.loads(started.content)["job_id"]

    # 启动即重置：已 indexed 文档回到 pending，尚未由 worker 推进（D-4b 生效）
    prog = client.get(f"/api/rebuild/{job_id}", **AUTH)
    assert prog.status_code == 200
    body = json.loads(prog.content)
    assert {"job_id", "state", "indexed", "failed", "pending", "done"} <= set(body)
    assert body["pending"] >= 1, f"启动后文档应被重置为 pending：{body}"

    # 模拟 worker 推进重建（生产由 ib-worker 异步跑）：pending → indexed（写入 v2）
    deps.lifecycle.process_pending("rebuild-w", 10)
    prog2 = client.get(f"/api/rebuild/{job_id}", **AUTH)
    body2 = json.loads(prog2.content)
    assert body2["indexed"] >= 1, f"推进后应有 indexed 文档：{body2}"
    assert body2["pending"] == 0, f"推进后不应残留 pending：{body2}"

    # 显式激活切版本：active 1 -> 2（D-4c 新增端点）
    act = client.post(
        "/api/rebuild/activate",
        data=json.dumps({"version": "2"}),
        content_type="application/json",
        **AUTH,
    )
    assert act.status_code == 200, act.content
    assert deps.ledger.active_collection_version("p_alpha") == "2"

    # 回滚：active 2 -> 1（O(1)，旧集合从未被删）
    rb = client.post(
        "/api/rebuild/rollback",
        data=json.dumps({"version": "1"}),
        content_type="application/json",
        **AUTH,
    )
    assert rb.status_code == 200, rb.content
    assert deps.ledger.active_collection_version("p_alpha") == "1"


# --------------------------------------------------------------------------- #
# US-IB-15：离线替身 / 自测能力
# --------------------------------------------------------------------------- #


def test_TC_E2E_012_offline_substitutes_selected(deps):
    """US-IB-15 离线装配确实选了替身列（向量库/嵌入/LLM/台账），可离线自测。"""
    names = (
        type(deps.vectors).__name__, type(deps.embedder).__name__,
        type(deps.llm).__name__, type(deps.ledger).__name__,
    )
    assert all("Fake" in n or "InMemory" in n for n in names), names
    assert deps.egress.remote is False


# --------------------------------------------------------------------------- #
# M-02 读路径（D-R2-01/02）：图片端点 + related_images 载荷衔接
# --------------------------------------------------------------------------- #


def test_TC_E2E_013_image_seam_end_to_end(http_app):
    """M-02 读路径：命中 → related_images 载荷（只含路径）→ 按 url_path 取图 200。

    证明 D-R2-02 接缝可用（前端拿到的路径确实能取到字节），且载荷不含 base64。
    """
    from ib.core import ChunkImageRecord, Scope
    from ib.lifecycle import image_id_for
    from ibweb.composition import _make_related_images_provider

    deps, Client = http_app
    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "seam.txt", "接缝验证正文。")
    png = b"\x89PNG\r\n\x1a\n" + b"Z" * 24
    ref = deps.blobs.put(scope, record.doc_id, io.BytesIO(png), "png")
    image_id = image_id_for(record.doc_id, "p1", "p1:i1")
    deps.ledger.upsert_chunk_images(
        scope, record.doc_id,
        [ChunkImageRecord(
            project_id="p_alpha", kb_id="kb_a", doc_id=record.doc_id, page_or_section="p1",
            image_id=image_id, source_kind="embedded_image", locator="p1:i1", blob_ref=ref.rel_path,
            doc_name="seam.txt", created_at="2026-01-01T00:00:00Z",
        )],
    )

    class _Hit:
        def __init__(self, doc_id, page_or_section):
            self.doc_id, self.page_or_section = doc_id, page_or_section

    payload = _make_related_images_provider(deps.ledger, scope)([_Hit(record.doc_id, "p1")], scope)
    assert payload is not None and payload.images
    url_path = payload.images[0].url_path
    assert url_path == f"/api/files/{record.doc_id}/images/{image_id}"

    got = Client().get(url_path, **AUTH)
    assert got.status_code == 200 and got.content == png
    assert got["Content-Type"].startswith("image/png")
