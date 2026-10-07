"""集成测试层 4/N —— ibweb HTTP 契约（Django test Client；离线装配）。

覆盖 IFC-IB-242~249、IFC-IB-250、IFC-IB-283、IC-IB-01（查询串令牌一律 400）；
鉴权走 `Authorization: Bearer`（离线共享令牌经环境变量注入，测试代码不含真实凭据）。
"""

from __future__ import annotations

import io
import json
import os

import pytest

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}


def _client(http_app):
    _, Client = http_app
    return Client()


# --------------------------------------------------------------------------- #
# 健康检查（免鉴权）
# --------------------------------------------------------------------------- #


def test_TC_INT_029_healthz_public(http_app):
    """[TC-INT-029] /healthz 免鉴权 200；/healthz/deps 暴露依赖健康与外发声明。"""
    client = _client(http_app)
    r = client.get("/healthz")
    assert r.status_code == 200 and json.loads(r.content)["ok"] is True
    r2 = client.get("/healthz/deps")
    assert r2.status_code == 200
    body = json.loads(r2.content)
    assert {"qdrant", "embed", "llm", "egress"} <= set(body)
    assert body["egress"]["remote"] is False, "离线装配却声明了数据外发"


# --------------------------------------------------------------------------- #
# 鉴权（IFC-IB-250 / AC-IB-11-05）
# --------------------------------------------------------------------------- #


def test_TC_INT_030_requires_bearer_token(http_app):
    """[TC-INT-030] 业务端点缺令牌 → 401（不是静默通过）。"""
    client = _client(http_app)
    r = client.get("/api/files")
    assert r.status_code == 401 and json.loads(r.content)["error"]["code"] == "unauthenticated"
    bad = client.get("/api/files", HTTP_AUTHORIZATION="Bearer wrong-token")
    assert bad.status_code == 401


def test_TC_INT_031_token_in_query_always_400(http_app):
    """[TC-INT-031] 查询串出现 token/api_key → 一律 400（IC-IB-01 令牌不得进 URL）。"""
    client = _client(http_app)
    for path in ("/api/files?token=x", "/api/chat/stream?q=hi&access_token=y", "/api/files?api_key=z"):
        r = client.get(path, **AUTH)
        assert r.status_code == 400, f"{path} 未拒绝查询串令牌"
        assert json.loads(r.content)["error"]["code"] == "token_in_query_forbidden"


def test_TC_INT_032_project_header_mismatch_403(http_app):
    """[TC-INT-032] X-IB-Project 与令牌所属项目不一致 → 403（project_id 只认服务端结论）。"""
    client = _client(http_app)
    r = client.get("/api/files", HTTP_X_IB_PROJECT="p_beta", **AUTH)  # 令牌属 p_alpha
    assert r.status_code == 403 and json.loads(r.content)["error"]["code"] == "project_mismatch"
    # 一致则放行
    ok = client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **AUTH)
    assert ok.status_code == 200


# --------------------------------------------------------------------------- #
# 上传 / 列表 / 删除 / 重试（IFC-IB-242~245）
# --------------------------------------------------------------------------- #


def test_TC_INT_033_upload_list_delete_roundtrip(http_app):
    """[TC-INT-033] 上传 → 列表 → 删除 全链路；字段契约按白名单投影。"""
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = _client(http_app)
    upload = SimpleUploadedFile("manual.txt", "楼宇自控手册正文。".encode("utf-8"), content_type="text/plain")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": upload}, **AUTH)
    assert r.status_code == 201, r.content
    record = json.loads(r.content)
    assert {"doc_id", "status", "doc_name", "kb_id"} <= set(record)
    # 内部调度字段不得泄漏
    assert not ({"lease_owner", "lease_expires_at", "blob_ref", "target_collection_version"} & set(record))

    listing = json.loads(client.get("/api/files", **AUTH).content)
    assert listing["total"] >= 1 and any(i["doc_id"] == record["doc_id"] for i in listing["items"])

    # 先让 worker 处理（生产里 worker 与后端并行跑），使 collection 已绑定
    deps = http_app[0]
    deps.lifecycle.process_pending("w-http", 10)

    deleted = client.delete(f"/api/files/{record['doc_id']}", **AUTH)
    assert deleted.status_code == 200, deleted.content
    assert json.loads(deleted.content)["ledger_deleted"] is True


def test_TC_INT_041_delete_before_bind_succeeds(http_app):
    """[TC-INT-041] 未绑定 collection 的项目删除刚上传的文档 → **成功**（R3 修复 FND-GROUP-D-02 的**正向回归守卫**）。

    修复前：删除路径假定「向量库恰好已被别处绑定」，而组合根启动期只 `ensure_collection`（建库）
    而**不** `bind_collection`，于是「上传后立刻删除」（本项目尚无事发生）必抛 `StartupError`
    → HTTP 500，且台账行残留（用户以为删了、内容仍在作答）。
    修复后：删除路径经 `CollectionResolver` 自绑写路径 collection，「本项目尚无派生物」自然收敛为
    `vectors_deleted=0` 的**成功**，台账行被删除。

    **R4 强化**：FND-GROUP-D-03 修复后，本路径的 `blob_deleted` 不再是「恒 False 的布尔」，
    而应**如实为 True** 且原文件字节确实被清理（此前只按实断言为布尔）。本条现同时守卫
    「未绑库删除不 500」（FND-GROUP-D-02）与「原文件字节被清理」（FND-GROUP-D-03）。

    本条**正向断言修复后的真值**；若退回 500、台账行残留或原文件残留，将**响亮失败**。
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    from ib.core import Scope
    from ib.lifecycle import blob_ref_for

    client = _client(http_app)  # 该夹具每次 fresh 装配 → collection 尚未绑定
    deps = http_app[0]
    up = SimpleUploadedFile("fresh.txt", "刚上传还没被 worker 处理。".encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    assert r.status_code == 201
    record = json.loads(r.content)

    # 删除前取得台账记录，以便删除后核对原文件引用是否已失效（R4）
    stored = deps.ledger.get_document(Scope("p_alpha"), record["doc_id"])
    ref = blob_ref_for(stored)
    assert ref is not None and deps.blobs.exists(ref), "前置：上传应已落盘原文件"

    deleted = client.delete(f"/api/files/{record['doc_id']}", **AUTH)
    assert deleted.status_code == 200, deleted.content
    body = json.loads(deleted.content)
    assert body["ledger_deleted"] is True
    assert body["vectors_deleted"] == 0, "本项目尚无事发生，不应有任何向量被删"
    # R4：HTTP 删除（项目级 scope）应仍能按记录的真实 kb 段清理原文件字节
    assert body["blob_deleted"] is True, f"原文件字节未被清理（FND-GROUP-D-03 复发？）：{body}"
    assert deps.blobs.exists(ref) is False, "删除后原文件仍在 BlobStore（孤儿）"
    # 删除已生效：列表不再包含该 doc_id
    still = json.loads(client.get("/api/files", **AUTH).content)
    assert all(i["doc_id"] != record["doc_id"] for i in still["items"]), "删除后列表仍含该文档"
    # 语义不变：已不存在（不在作用域内）再删仍 404（NotFoundError → 404）
    assert client.delete(f"/api/files/{record['doc_id']}", **AUTH).status_code == 404


def test_TC_INT_034_upload_validation_400(http_app):
    """[TC-INT-034] 改名攻击（内容与扩展名不符）→ 400（魔数校验）。"""
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = _client(http_app)
    fake = SimpleUploadedFile("evil.pdf", b"this is plain text, not a pdf", content_type="application/pdf")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": fake}, **AUTH)
    assert r.status_code == 400 and json.loads(r.content)["error"]["code"]


def test_TC_INT_035_upload_kb_derived_from_subject(http_app):
    """[TC-INT-035] REV-18（IFC-IB-375 / ADR-41）：**请求体 kb 字段被忽略**，`kb_id` 由主体推导。

    ADR-41 把「kb_id 由客户端提交、服务端仅断言归属」改为「`kb_id ≡ project_id`，
    请求体不再接收 kb 字段」——客户端**不可自证范围**。故本用例从「越权 kb → 403」改写为
    「提交 `kb_id=kb_b`（属 p_beta）时该字段**被忽略**，落库 kb_id 为**主体项目** `p_alpha`」。
    这既守住「范围只认服务端结论」，也让「上传到外项目 KB」在**结构上不可达**（比 403 更强）。

    归属断言路径见 `test_TC_INT_035b_assert_kb_in_project_retained`（`assert_kb_in_project` 保留，
    失败仍 403 —— 红线不削弱）。
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = _client(http_app)
    up = SimpleUploadedFile("x.txt", "内容".encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_b", "file": up}, **AUTH)  # kb_b 属 p_beta → 应被忽略
    assert r.status_code == 201, r.content
    record = json.loads(r.content)
    assert record["kb_id"] == "p_alpha", "kb_id 必须由主体 project_id 推导（kb_b 应被忽略）"


def test_TC_INT_035b_assert_kb_in_project_retained(http_app):
    """[TC-INT-035b] REV-18（C-IB-43）：`assert_kb_in_project` 归属断言**保留**且失败仍 403。

    直测台账端口（HTTP 层因 `kb_id ≡ project_id` 已结构上不可达外项目 kb，故在端口层
    证明断言未被削弱）：`assert_kb_in_project("p_alpha", "kb_b")`（kb_b 属 p_beta）
    → 抛 `ScopeViolationError`（→ HTTP 403，非 404，反存在性探测）。
    """
    deps = http_app[0]
    from ib.core import ScopeViolationError

    # 归属合法（kb_id ≡ project_id）：p_alpha 的 kb 行由 _seed_projects 登记为 "p_alpha"。
    deps.ledger.assert_kb_in_project("p_alpha", "p_alpha")
    # 归属非法（跨项目 kb）：必须 fail-closed 抛 ScopeViolationError（→ 403）。
    raised = False
    try:
        deps.ledger.assert_kb_in_project("p_alpha", "kb_b")
    except ScopeViolationError:
        raised = True
    assert raised, "assert_kb_in_project 未对外项目 kb 抛 ScopeViolationError（红线被削弱？）"


# --------------------------------------------------------------------------- #
# 页面图字节端点（IFC-IB-283）
# --------------------------------------------------------------------------- #


def _seed_image(deps, project_id="p_alpha", kb_id="kb_a"):
    """造一条「有字节」的页面图关联（真实 BlobStore + 真实台账行）。"""
    from ib.core import ChunkImageRecord, Scope
    from ib.lifecycle import image_id_for
    from conftest import ingest_text

    scope = Scope(project_id, (kb_id,))
    record = ingest_text(deps, project_id, kb_id, "drawing.txt", "占位正文，供图关联落底。")
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    ref = deps.blobs.put(scope, record.doc_id, io.BytesIO(png), "png")
    image_id = image_id_for(record.doc_id, "p1", "p1:i1")
    deps.ledger.upsert_chunk_images(
        scope, record.doc_id,
        [
            ChunkImageRecord(
                project_id=project_id, kb_id=kb_id, doc_id=record.doc_id, page_or_section="p1",
                image_id=image_id, source_kind="embedded_image", locator="p1:i1",
                blob_ref=ref.rel_path, doc_name="drawing.txt", created_at="2026-01-01T00:00:00Z",
            )
        ],
    )
    return record.doc_id, image_id, png


def test_TC_INT_036_image_endpoint_200_with_fixed_mime(http_app):
    """[TC-INT-036] 页面图 200：字节流 + 固定表 Content-Type（不依赖部署机注册表）+ 反嗅探头。"""
    deps, Client = http_app
    doc_id, image_id, png = _seed_image(deps)
    r = Client().get(f"/api/files/{doc_id}/images/{image_id}", **AUTH)
    assert r.status_code == 200, r.content
    assert r["Content-Type"].startswith("image/png")
    assert r["X-Content-Type-Options"] == "nosniff"
    assert "private" in r["Cache-Control"]
    assert r.content == png


def test_TC_INT_037_image_endpoint_404_variants(http_app):
    """[TC-INT-037] 关联行缺失 / 无字节引用 / 跨项目 → 一律 404（反存在性探测）。"""
    deps, Client = http_app
    doc_id, image_id, _ = _seed_image(deps)
    # 不存在的 image_id
    assert Client().get(f"/api/files/{doc_id}/images/img-nope", **AUTH).status_code == 404
    # 不存在的 doc_id
    assert Client().get("/api/files/no-such-doc/images/img-x", **AUTH).status_code == 404
    # 跨项目：p_beta 的令牌访问 p_alpha 的行 → 查不到 → 404（不区分不存在与不属于你）
    from ib.context import make_request_context
    from ibweb import composition

    saved = composition.get_deps()
    original_principal = saved.principal_resolver

    class _BetaResolver:
        def resolve(self, token):
            return make_request_context(project_id="p_beta", actor_id="u", session_id="s").authz

    saved.principal_resolver = _BetaResolver()
    try:
        r = Client().get(f"/api/files/{doc_id}/images/{image_id}", **AUTH)
        assert r.status_code == 404, r.content
    finally:
        saved.principal_resolver = original_principal


def test_TC_INT_038_image_endpoint_query_token_400(http_app):
    """[TC-INT-038] 图片端点也不接受 `?token=` → 400。"""
    deps, Client = http_app
    doc_id, image_id, _ = _seed_image(deps)
    r = Client().get(f"/api/files/{doc_id}/images/{image_id}?token=x", **AUTH)
    assert r.status_code == 400


# --------------------------------------------------------------------------- #
# SSE 问答端点（IFC-IB-247）
# --------------------------------------------------------------------------- #


def test_TC_INT_039_chat_stream_sse_contract(http_app):
    """[TC-INT-039] 问答端点：缺 q → 400；正常 → text/event-stream 且事件序列合法。"""
    client = _client(http_app)
    assert client.get("/api/chat/stream", **AUTH).status_code == 400

    r = client.get("/api/chat/stream?q=设备故障怎么排查&session_id=s-contract", **AUTH)
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/event-stream")
    body = b"".join(r.streaming_content).decode("utf-8") if hasattr(r, "streaming_content") else r.content.decode("utf-8")
    assert "event: content" in body, body
    assert "event: done" in body
    # reasoning 必须早于 content；done 必须最后
    assert body.index("event: reasoning") < body.index("event: content")
    assert body.rstrip().endswith("data:")


# --------------------------------------------------------------------------- #
# 重建端点（IFC-IB-246）——只启动不阻塞
# --------------------------------------------------------------------------- #


def test_TC_INT_040_rebuild_start_returns_202(http_app):
    """[TC-INT-040] POST /api/rebuild → 202 RebuildJob（长任务只启动，不阻塞）。"""
    client = _client(http_app)
    r = client.post("/api/rebuild", **AUTH)
    assert r.status_code == 202, r.content
    body = json.loads(r.content)
    assert body["job_id"] and "state" in body
    prog = client.get(f"/api/rebuild/{body['job_id']}", **AUTH)
    assert prog.status_code == 200 and "job_id" in json.loads(prog.content)
    assert client.get("/api/rebuild/no-such-job", **AUTH).status_code == 404
