"""集成测试层 5/N —— 编排事件序列 + `related_images` 接缝（D-R2-02 验收）。

覆盖 IFC-IB-232（事件顺序）、IFC-IB-282（`related_images` 载荷只含路径、内容之后发出）、
D-R2-02（「注入非空命中 → 事件到达前端载荷」证明接缝可用，且不伪造命中）。
"""

from __future__ import annotations

import json

from conftest import ingest_text, request_ctx

import pytest


def _orchestrator(deps, *, provider=None, project_id="p_alpha"):
    from ib.core import GraphConfig, Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph
    from ib.streaming import MemorySessionStore

    bound_tools = deps.bind_tools(Scope(project_id=project_id))
    return build_graph(
        llm=deps.llm,
        experts=EXPERT_SPECS,
        tools=bound_tools,
        sessions=MemorySessionStore(),
        config=GraphConfig(),
        scope=Scope(project_id=project_id),
        tools_by_expert={name: bound_tools for name in (s.name for s in EXPERT_SPECS)},
        related_images_provider=provider,
    )


def _kinds(events):
    return [str(e.kind) for e in events]


# --------------------------------------------------------------------------- #
# IFC-IB-232 事件顺序
# --------------------------------------------------------------------------- #


def test_TC_INT_042_event_order_reasoning_content_done(deps):
    """[TC-INT-042] 事件顺序：reasoning → content → done；恰一条 content（不逐专家重复）。"""
    orch = _orchestrator(deps)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)
    assert kinds[0] == "reasoning"
    assert kinds[-1] == "done"
    assert kinds.count("content") == 1, f"content 出现 {kinds.count('content')} 次：{kinds}"
    assert kinds.index("reasoning") < kinds.index("content") < kinds.index("done")


def test_TC_INT_043_degraded_precedes_content(deps):
    """[TC-INT-043] 降级提示必须在正文之前到达（否则会被当成为答案的补充说明）。"""
    from ib.llm import FakeLlmProvider
    from ib.core import GraphConfig, Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph
    from ib.streaming import MemorySessionStore

    broken_llm = FakeLlmProvider(unavailable=True)
    orch = build_graph(
        llm=broken_llm,
        experts=EXPERT_SPECS,
        tools=[],
        sessions=MemorySessionStore(),
        config=GraphConfig(),
        scope=Scope(project_id="p_alpha"),
    )
    events = list(orch.run("能耗数据", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s2"))
    kinds = _kinds(events)
    assert "degraded" in kinds, f"依赖故障却无 degraded 事件：{kinds}"
    assert kinds.index("degraded") < kinds.index("content") < kinds.index("done")


# --------------------------------------------------------------------------- #
# D-R2-02 `related_images` 接缝：映射半 + 发送半
# --------------------------------------------------------------------------- #


def test_TC_INT_044_provider_maps_hits_to_payload_paths_only(deps):
    """[TC-INT-044] 生产者把非空命中映射为载荷：只含站内相对路径，绝无 base64（IFC-IB-282）。"""
    from ib.core import ChunkImageRecord, Scope
    from ib.lifecycle import image_id_for
    from ibweb.composition import _make_related_images_provider

    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "atlas.txt", "图册占位正文。")
    image_id = image_id_for(record.doc_id, "p3", "p3:i1")
    deps.ledger.upsert_chunk_images(
        scope, record.doc_id,
        [ChunkImageRecord(
            project_id="p_alpha", kb_id="kb_a", doc_id=record.doc_id, page_or_section="p3",
            image_id=image_id, source_kind="embedded_image", locator="p3:i1", blob_ref=None,
            doc_name="atlas.txt", created_at="2026-01-01T00:00:00Z",
        )],
    )

    provider = _make_related_images_provider(deps.ledger, scope)

    class _Hit:
        def __init__(self, doc_id, page_or_section):
            self.doc_id = doc_id
            self.page_or_section = page_or_section

    # 空命中 → None（「无图」只有一种表示）
    assert provider([], scope) is None
    # 非空命中 → 载荷；确定性 + 幂等
    payload = provider([_Hit(record.doc_id, "p3")], scope)
    payload2 = provider([_Hit(record.doc_id, "p3")], scope)
    assert payload is not None and len(payload.images) == 1
    item = payload.images[0]
    assert item.image_id == image_id and item.doc_id == record.doc_id
    assert item.url_path == f"/api/files/{record.doc_id}/images/{image_id}"
    assert [i.image_id for i in payload.images] == [i.image_id for i in payload2.images]

    from ib.streaming import related_images_event, related_images_json

    body = related_images_json(payload)
    assert "base64" not in body.lower()
    assert set(json.loads(body)["images"][0]) == {"image_id", "doc_id", "doc_name", "page_or_section", "url_path"}
    event = related_images_event(payload)
    assert event is not None and str(event.kind) == "related_images"


def test_TC_INT_045_provider_is_project_scoped(deps):
    """[TC-INT-045] 生产者按 provider scope 隔离：跨项目 / 不存在的 doc → None（不泄漏存在性）。"""
    from ib.core import ChunkImageRecord, Scope
    from ib.lifecycle import image_id_for
    from ibweb.composition import _make_related_images_provider

    scope_alpha = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "alpha.txt", "甲项目正文。")
    deps.ledger.upsert_chunk_images(
        scope_alpha, record.doc_id,
        [ChunkImageRecord(
            project_id="p_alpha", kb_id="kb_a", doc_id=record.doc_id, page_or_section="p1",
            image_id=image_id_for(record.doc_id, "p1", "p1:i1"), source_kind="embedded_image",
            locator="p1:i1", blob_ref=None, doc_name="alpha.txt", created_at="2026-01-01T00:00:00Z",
        )],
    )

    class _Hit:
        def __init__(self, doc_id, page_or_section):
            self.doc_id = doc_id
            self.page_or_section = page_or_section

    # provider 以 p_beta 为 scope：即便命中携带 p_alpha 的 doc_id，也查不到 → None
    provider_beta = _make_related_images_provider(deps.ledger, Scope("p_beta", ("kb_b",)))
    assert provider_beta([_Hit(record.doc_id, "p1")], Scope("p_beta", ("kb_b",))) is None
    # 不存在的 doc → None
    provider_alpha = _make_related_images_provider(deps.ledger, scope_alpha)
    assert provider_alpha([_Hit("no-such-doc", "p1")], scope_alpha) is None


def test_TC_INT_046_orchestrator_emits_related_images_after_content(deps):
    """[TC-INT-046] 发送半：provider 非空 → 事件在 content 之后、done 之前到达（接缝可用）。

    这条证明的是「**给定非空命中，事件确实能到前端载荷**」——即 D-R2-02 要求的、
    当前生产因上游不产命中而恒为空的接缝**本身是通的**。此处**手工注入**非空载荷，
    不伪造检索命中。
    """
    from ib.core import RelatedImageItem, RelatedImagesPayload
    from ib.streaming import related_image_url

    injected = RelatedImagesPayload(
        images=(
            RelatedImageItem(
                image_id="img-42", doc_id="d42", doc_name="图纸.pdf", page_or_section="p1",
                url_path=related_image_url("d42", "img-42"),
            ),
        )
    )

    def _provider(hits, scope):
        return injected

    orch = _orchestrator(deps, provider=_provider)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s3"))
    kinds = _kinds(events)
    assert "related_images" in kinds, f"接缝未产出事件：{kinds}"
    assert kinds.index("content") < kinds.index("related_images") < kinds.index("done")
    payload = next(e for e in events if str(e.kind) == "related_images")
    assert "base64" not in str(payload.data).lower()
    assert "img-42" in str(payload.data) and "/api/files/d42/images/img-42" in str(payload.data)


def test_TC_INT_047_orchestrator_suppresses_empty_and_provider_errors(deps):
    """[TC-INT-047] 空载荷 → 不发事件；provider 抛异常 → fail-open 不发事件、不中断（IFC-IB-282）。"""

    def _empty(hits, scope):
        return None

    def _boom(hits, scope):
        raise RuntimeError("取图失败")

    for provider in (_empty, _boom):
        orch = _orchestrator(deps, provider=provider)
        events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s4"))
        kinds = _kinds(events)
        assert "related_images" not in kinds, f"不应发事件：{kinds}"
        assert kinds[-1] == "done" and "content" in kinds


def test_TC_INT_048_production_wiring_passes_empty_hits_registered(deps):
    """[TC-INT-048] 复现 D-R2-02 已登记行为（非缺陷）：

    生产装配的编排器在 `_related_images_events()` 里恒以**空命中元组**调用 provider
    （R1 编排器未执行工具、未收集命中）。故即便库中**确有**图关联行，生产路径也永不出图。

    本条固化该行为，并**同时证明接缝本身可用**（TC-INT-044/046 已证）：
    缺的是「上游把命中传进来」，不是「下游发不出事件」。
    """
    from ib.core import ChunkImageRecord, Scope
    from ib.lifecycle import image_id_for

    scope = Scope("p_alpha", ("kb_a",))
    record = ingest_text(deps, "p_alpha", "kb_a", "wired.txt", "接线验证正文。")
    deps.ledger.upsert_chunk_images(
        scope, record.doc_id,
        [ChunkImageRecord(
            project_id="p_alpha", kb_id="kb_a", doc_id=record.doc_id, page_or_section="p1",
            image_id=image_id_for(record.doc_id, "p1", "p1:i1"), source_kind="embedded_image",
            locator="p1:i1", blob_ref=None, doc_name="wired.txt", created_at="2026-01-01T00:00:00Z",
        )],
    )
    # 生产编排器（组合根产出，注入真实 provider）
    orch = deps.orchestrator_for("p_alpha")
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s5"))
    kinds = _kinds(events)
    assert "related_images" not in kinds, (
        "生产路径开始出图——请重新评估 D-R2-02 登记（这属于行为变更，需更新登记与文档）"
    )
