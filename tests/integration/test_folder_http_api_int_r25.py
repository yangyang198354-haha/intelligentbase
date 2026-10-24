"""[R25 / GROUP_D] 集成 —— 资料库 HTTP 接口（**真实 Django**：URLconf、中间件、鉴权、multipart 解析）。

边界：`ibweb.library_views` ↔ Django（MultiPartParser / request.POST / URL 反解 / 中间件）↔ `ib.library` ↔ 台账。
GR-C-001 条件：
  * CR-001：批次 PUT 逐文件上传的 multipart 手动解析、更新端点的 `on_conflict` 表单参数 —— 本文件在真实 Django 下实跑。
  * CR-002：旧入口 `POST /api/files` 在根目录同名时返回 409（含大小写变体）。
溯源：US-001/002/003/005/007/008/011/012/013/015；REQ-NFUNC-005（权限 / 跨项目 404 / 归属断言 403）。
离线：Django 测试客户端 + 内存台账 / 向量库，不触网。
"""

from __future__ import annotations

import io
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import R13_ADMIN_PASSWORD, bearer, change_password, login
from folder_r25_support import (
    AUTH,
    PID,
    browse,
    find_item,
    get_doc,
    jbody,
    jreq,
    names_in,
    put_file,
    put_multipart,
    scope_of,
    search,
    upload_batch,
)

S = scope_of()
BIG = 3 * 1024 * 1024  # > Django FILE_UPLOAD_MAX_MEMORY_SIZE(2.5MB) → TemporaryUploadedFile 分支


def _client(http_app):
    return http_app[1]()


# --------------------------------------------------------------------------- #
# CR-001：批次 PUT 的 multipart 解析（真实 Django）
# --------------------------------------------------------------------------- #


def test_TC_INT_R25_001_CR001_batch_put_small_multipart_parsed_and_ingested(http_app):
    """[TC-INT-R25-001] CR-001：`PUT /api/uploads/{b}/items/{i}` 的 multipart 经 MultiPartParser 手动解析 —— 小文件内存分支：200 accepted、文件落到计划的目录、
    原样落盘（blob 字节 = 上传字节）、worker 处理后可检索。"""
    deps, Client = http_app
    client = Client()
    payload = "批次上传的小文件正文 空调水系统".encode("utf-8")
    plan, results, batch_id = upload_batch(client, {"项目/子/doc.txt": payload})
    assert results[0]["state"] == "accepted" and results[0]["final_rel_path"] == "项目/子/doc.txt" and results[0]["doc_id"]
    doc = get_doc(deps, results[0]["doc_id"])
    assert doc.doc_name == "doc.txt" and doc.size_bytes == len(payload) and doc.status == "pending"
    from ib.lifecycle import blob_ref_for

    ref = blob_ref_for(doc)
    assert ref is not None and deps.blobs.exists(ref)
    top = browse(client)
    assert names_in(top) == ["项目"]
    sub = browse(client, find_item(top, "项目")["folder_id"])
    inner = browse(client, find_item(sub, "子")["folder_id"])
    assert names_in(inner, "file") == ["doc.txt"] and [c["name"] for c in inner["breadcrumb"]] == ["项目", "子"]
    deps.lifecycle.process_pending("w", 10)
    assert [h for h in search(deps, "批次上传的小文件正文 空调水系统").hits if h.doc_id == doc.doc_id]


def test_TC_INT_R25_002_CR001_batch_put_large_file_temp_upload_branch(http_app):
    """[TC-INT-R25-002] CR-001：> 2.5MB 的文件走 Django 临时文件上传分支 —— PUT 手动解析同样成功，落盘字节数与大小一致；声明大小 < 实际 → SIZE_MISMATCH 跳过（服务端权威）。"""
    deps, Client = http_app
    client = Client()
    body = (b"abcdefghij" * 1024) * 300  # 3,072,000 B > 2.5MB
    assert len(body) > 2_621_440
    _, results, _ = upload_batch(client, {"big/large.txt": body})
    assert results[0]["state"] == "accepted"
    doc = get_doc(deps, results[0]["doc_id"])
    assert doc.size_bytes == len(body)
    from ib.lifecycle import blob_ref_for

    ref = blob_ref_for(doc)
    assert deps.blobs.exists(ref)
    # 声明的大小小于真实大小 → 跳过 SIZE_MISMATCH，不入库
    _, r2, _ = upload_batch(client, {"big2/liar.txt": b"x" * 5000}, declared={"big2/liar.txt": 100})
    assert (r2[0]["state"], r2[0]["reason_code"], r2[0]["doc_id"]) == ("skipped", "SIZE_MISMATCH", None)
    assert "big2" not in names_in(browse(client)), "SIZE_MISMATCH 不得留下空目录"


def test_TC_INT_R25_003_CR001_batch_put_is_idempotent_and_error_paths(http_app):
    """[TC-INT-R25-003] CR-001：重复 PUT 返回既有终态且不重复入库；非 multipart 的 PUT → 400；multipart 缺 file 字段 → 400；GET/POST 该路由 → 405；
    无令牌 → 401；查询串带 token → 400（既有中间件）；不存在 / 他项目批次 → 404。"""
    from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

    deps, Client = http_app
    client = Client()
    plan, results, batch_id = upload_batch(client, {"idem/a.txt": b"idempotent put content"})
    again = put_multipart(client, f"/api/uploads/{batch_id}/items/0", "a.txt", b"idempotent put content")
    assert again.status_code == 200 and jbody(again)["doc_id"] == results[0]["doc_id"]
    assert len([i for i in browse(client, find_item(browse(client), "idem")["folder_id"])["items"]]) == 1
    # 非 multipart
    r = client.put(f"/api/uploads/{batch_id}/items/0", data=b"raw", content_type="application/octet-stream", **AUTH)
    assert r.status_code == 400 and jbody(r)["error"]["code"] == "bad_request"
    # multipart 但没有 file 字段
    plan2 = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [{"client_idx": 0, "rel_path": "n.txt", "size": 5}]})
    bid2 = jbody(plan2)["batch_id"]
    body = encode_multipart(BOUNDARY, {"other": "value"})
    no_file = client.put(f"/api/uploads/{bid2}/items/0", data=body, content_type=MULTIPART_CONTENT, **AUTH)
    assert no_file.status_code == 400 and jbody(no_file)["error"]["code"] == "bad_request"
    assert client.get(f"/api/uploads/{bid2}/items/0", **AUTH).status_code == 405
    assert client.post(f"/api/uploads/{bid2}/items/0", **AUTH).status_code == 405
    assert client.put(f"/api/uploads/{bid2}/items/0", data=body, content_type=MULTIPART_CONTENT).status_code == 401
    assert client.put(f"/api/uploads/{bid2}/items/0?token=x", data=body, content_type=MULTIPART_CONTENT, **AUTH).status_code == 400
    missing = put_multipart(client, f"/api/uploads/{'0' * 32}/items/0", "n.txt", b"hello")
    assert missing.status_code == 404
    bad_id = put_multipart(client, "/api/uploads/not-a-batch-id/items/0", "n.txt", b"hello")
    assert bad_id.status_code == 400
    neg = put_multipart(client, f"/api/uploads/{bid2}/items/1", "n.txt", b"hello")
    assert neg.status_code == 404, "client_idx 超出批次范围 → 批次项不存在"


def test_TC_INT_R25_004_CR001_batch_put_magic_mismatch_and_dependency_failure_503(http_app, monkeypatch):
    """[TC-INT-R25-004] CR-001 / AC-002-02 / AC-002-03：魔数不符 → 200 跳过 MAGIC_MISMATCH；依赖故障（blob 不可用）→ 503 且该项记 failed，其余项不受影响；同 idx 重试成功。"""
    from ib.core import DependencyUnavailableError

    deps, Client = http_app
    client = Client()
    plan = jbody(jreq(client, "POST", "/api/uploads", {
        "target_folder_id": "", "dry_run": False,
        "entries": [{"client_idx": 0, "rel_path": "f/fake.pdf", "size": 100}, {"client_idx": 1, "rel_path": "f/ok.txt", "size": 100}, {"client_idx": 2, "rel_path": "f/ok2.txt", "size": 100}],
    }))
    bid = plan["batch_id"]
    r0 = put_multipart(client, f"/api/uploads/{bid}/items/0", "fake.pdf", b"not really a pdf")
    assert jbody(r0)["reason_code"] == "MAGIC_MISMATCH" and jbody(r0)["state"] == "skipped"
    real_put = deps.lifecycle._blobs.put

    def broken(*a, **k):
        raise DependencyUnavailableError("blob down", dependency="blob")

    monkeypatch.setattr(deps.lifecycle._blobs, "put", broken)
    r1 = put_multipart(client, f"/api/uploads/{bid}/items/1", "ok.txt", b"second file content")
    assert r1.status_code == 503
    monkeypatch.setattr(deps.lifecycle._blobs, "put", real_put)
    r2 = put_multipart(client, f"/api/uploads/{bid}/items/2", "ok2.txt", b"third file content")
    assert r2.status_code == 200 and jbody(r2)["state"] == "accepted"
    mid = jbody(jreq(client, "GET", f"/api/uploads/{bid}"))
    assert (mid["accepted"], mid["skipped"], mid["failed"], mid["pending"]) == (1, 1, 1, 0)
    r1b = put_multipart(client, f"/api/uploads/{bid}/items/1", "ok.txt", b"second file content")
    assert r1b.status_code == 200 and jbody(r1b)["state"] == "accepted"
    end = jbody(jreq(client, "GET", f"/api/uploads/{bid}"))
    assert (end["accepted"], end["skipped"], end["failed"], end["pending"]) == (2, 1, 0, 0)
    assert end["accepted"] + end["skipped"] + end["failed"] + end["pending"] == end["total"] == 3


# --------------------------------------------------------------------------- #
# CR-001：更新端点 on_conflict 表单参数（request.POST）
# --------------------------------------------------------------------------- #


def _revise(client, doc_id, name, content: bytes | str, **form):
    data = content.encode("utf-8") if isinstance(content, str) else content
    return client.post(
        f"/api/files/{doc_id}/revision",
        {"file": SimpleUploadedFile(name, data), **form},
        **AUTH,
    )


def test_TC_INT_R25_005_CR001_revision_on_conflict_form_param(http_app):
    """[TC-INT-R25-005] CR-001：`POST /api/files/{id}/revision` 的 `on_conflict` 取自 multipart 表单（request.POST）——
    缺省 / fail → 409 name_conflict 且 `conflicts` 列出冲突条目；rename → 202 且 final_name 为 `… (2).md`；非法取值 → 400；冲突时双方内容与名称不变。"""
    deps, Client = http_app
    client = Client()
    x = put_file(deps, "规范.txt", "X 的原内容 甲")
    y = put_file(deps, "规范v2.md", "Y 的原内容 乙")
    r = _revise(client, x.doc_id, "规范V2.MD", "新内容 丙")
    assert r.status_code == 409, r.content
    body = jbody(r)
    assert body["error"]["code"] == "name_conflict"
    assert body["conflicts"][0]["existing"] == {"kind": "file", "id": y.doc_id, "name": "规范v2.md"}
    assert body["conflicts"][0]["entry"]["id"] == x.doc_id
    assert (get_doc(deps, x.doc_id).doc_name, get_doc(deps, y.doc_id).doc_name) == ("规范.txt", "规范v2.md")
    assert _revise(client, x.doc_id, "规范V2.MD", "新内容 丙", on_conflict="fail").status_code == 409
    assert _revise(client, x.doc_id, "规范V2.MD", "新内容 丙", on_conflict="bogus").status_code == 400
    ok = _revise(client, x.doc_id, "规范V2.MD", "新内容 丙", on_conflict="rename")
    assert ok.status_code == 202, ok.content
    ok_body = jbody(ok)
    assert ok_body["changed"] is True and ok_body["final_name"] == "规范V2 (2).MD"
    assert ok_body["item"]["update_state"] == "updating" and ok_body["item"]["status"] == "indexed"
    deps.lifecycle.process_pending("w", 10)
    names = names_in(browse(client), "file")
    assert sorted(names) == ["规范V2 (2).MD", "规范v2.md"]


def test_TC_INT_R25_006_revision_unchanged_discard_and_error_mapping(http_app):
    """[TC-INT-R25-006] AC-008-06 / AC-008-03 / IFC-008~009：内容相同 → 200 CONTENT_UNCHANGED（不重新索引）；不支持类型 / 空文件 / 魔数不符 → 400 且错误码取 UploadRejection 小写；
    更新中再次更新 → 409 update_in_progress 之外，pending 存活行 → doc_busy；DELETE 丢弃失败 / 待处理的更新 → 200 discarded；缺文件字段 → 400；他项目 / 不存在 → 404。"""
    deps, Client = http_app
    client = Client()
    live = put_file(deps, "u.txt", "更新端点专属内容 原版")
    snapshot = get_doc(deps, live.doc_id)
    same = _revise(client, live.doc_id, "u.txt", "更新端点专属内容 原版")
    assert same.status_code == 200 and jbody(same) == {"changed": False, "reason": "CONTENT_UNCHANGED"}
    after_same = get_doc(deps, live.doc_id)
    assert (after_same.doc_id, after_same.status, after_same.indexed_at, after_same.content_updated_at, after_same.chunk_count) == (
        snapshot.doc_id, snapshot.status, snapshot.indexed_at, snapshot.content_updated_at, snapshot.chunk_count,
    )
    assert deps.tree.get_revision_of(S, live.doc_id) is None, "内容未变化：不建修订行、不重新索引"
    assert jbody(_revise(client, live.doc_id, "u.exe", "x"))["error"]["code"] == "unsupported_type"
    assert jbody(_revise(client, live.doc_id, "u.txt", b""))["error"]["code"] == "empty_file"
    assert jbody(_revise(client, live.doc_id, "u.pdf", "not a pdf"))["error"]["code"] == "magic_mismatch"
    assert client.post(f"/api/files/{live.doc_id}/revision", {}, **AUTH).status_code == 400
    assert _revise(client, "0" * 32, "u.txt", "zzz").status_code == 404
    assert _revise(client, "short", "u.txt", "zzz").status_code == 400
    started = _revise(client, live.doc_id, "u.txt", "更新端点专属内容 新版")
    assert started.status_code == 202
    gone = jreq(client, "DELETE", f"/api/files/{live.doc_id}/revision")
    assert gone.status_code == 200 and jbody(gone) == {"discarded": True}
    assert jbody(jreq(client, "DELETE", f"/api/files/{live.doc_id}/revision")) == {"discarded": False}
    pending = put_file(deps, "p.txt", "尚未索引的文件", process=False)
    busy = _revise(client, pending.doc_id, "p.txt", "换一个内容")
    assert busy.status_code == 409 and jbody(busy)["error"]["code"] == "doc_busy"


def test_TC_INT_R25_007_retry_endpoint_retries_failed_revision(http_app, monkeypatch):
    """[TC-INT-R25-007] IFC-013：`POST /api/files/{id}/retry` —— 存活行 indexed 且其修订行 failed → 重试的是修订行（修订行回到 pending，存活行不动）；成功后切换。"""
    from folder_r25_support import FailingEmbedder

    deps, Client = http_app
    client = Client()
    live = put_file(deps, "rt.txt", "重试端点 旧版内容")
    assert _revise(client, live.doc_id, "rt.txt", "重试端点 新版内容").status_code == 202
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    deps.lifecycle.process_pending("w", 10)
    item = find_item(browse(client), "rt.txt")
    assert item["status"] == "indexed" and item["update_state"] == "update_failed" and item["update_error_code"]
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    r = jreq(client, "POST", f"/api/files/{live.doc_id}/retry")
    assert r.status_code == 200, r.content
    assert deps.tree.get_revision_of(S, live.doc_id).status == "pending" and get_doc(deps, live.doc_id).status == "indexed"
    deps.lifecycle.process_pending("w", 10)
    item2 = find_item(browse(client), "rt.txt")
    assert item2["update_state"] is None and item2["content_updated_at"]


# --------------------------------------------------------------------------- #
# CR-002：旧入口 POST /api/files 根目录同名 → 409
# --------------------------------------------------------------------------- #


def _post_legacy(client, name, content="旧入口正文"):
    return client.post("/api/files", {"file": SimpleUploadedFile(name, content.encode("utf-8"))}, **AUTH)


def test_TC_INT_R25_010_CR002_legacy_post_files_same_name_in_root_returns_409(http_app):
    """[TC-INT-R25-010] CR-002：旧入口 `POST /api/files`（根目录）同名 → 409 name_conflict（含仅大小写不同的 `LEGACY.TXT`）；首个文件原样保留；
    不同名仍 201（成对）；旧入口的文件在资料库根目录可见。"""
    deps, Client = http_app
    client = Client()
    first = _post_legacy(client, "legacy.txt", "第一份")
    assert first.status_code == 201, first.content
    dup = _post_legacy(client, "legacy.txt", "第二份")
    assert dup.status_code == 409 and jbody(dup)["error"]["code"] == "name_conflict", dup.content
    case = _post_legacy(client, "LEGACY.TXT", "第三份")
    assert case.status_code == 409 and jbody(case)["error"]["code"] == "name_conflict"
    listing = jbody(client.get("/api/files", **AUTH))
    assert [i["doc_name"] for i in listing["items"]] == ["legacy.txt"], "被拒绝的上传不得产生台账行"
    other = _post_legacy(client, "other.txt", "另一份")
    assert other.status_code == 201
    assert sorted(names_in(browse(client), "file")) == ["legacy.txt", "other.txt"]
    # 仅根目录同名冲突：子目录里同名文件不冲突
    folder = deps.library.create_folder(S, "", "sub").folder_id
    put_file(deps, "legacy.txt", "子目录里的同名文件", folder_id=folder, process=False)
    assert deps.library.browse(S, folder, page=1, page_size=50).total == 1


def test_TC_INT_R25_011_CR002_create_document_same_name_in_root_raises_conflict(http_app):
    """[TC-INT-R25-011] CR-002（port 层）：`create_document` 对根目录同名抛 LibraryConflictError(name_conflict)，不留台账行；与上传管线的入库行为一致。"""
    from ib.core.library import LibraryConflictError

    deps, _ = http_app
    from conftest import request_ctx

    ctx = request_ctx(PID)
    v = deps.lifecycle.validate_upload("dup.txt", 10, b"0123456789")
    deps.lifecycle.submit_upload(ctx, v, PID, data=io.BytesIO(b"0123456789"))
    with pytest.raises(LibraryConflictError) as err:
        deps.lifecycle.submit_upload(ctx, v, PID, data=io.BytesIO(b"abcdefghij"))
    assert err.value.code == "name_conflict"
    assert deps.library.browse(S, "", page=1, page_size=50).total == 1


def test_TC_INT_R25_012_list_files_hides_revision_rows(http_app):
    """[TC-INT-R25-012] IFC-013：兼容端点 `GET /api/files` 不返回修订行（总数与条目均不含）。"""
    deps, Client = http_app
    client = Client()
    live = put_file(deps, "vis.txt", "兼容列表 旧版")
    assert _revise(client, live.doc_id, "vis.txt", "兼容列表 新版").status_code == 202
    listing = jbody(client.get("/api/files", **AUTH))
    assert listing["total"] == 1 and [i["doc_id"] for i in listing["items"]] == [live.doc_id]


# --------------------------------------------------------------------------- #
# 浏览 / 目录 / 移动 / 改名 端点
# --------------------------------------------------------------------------- #


def test_TC_INT_R25_020_browse_endpoint_contract_and_param_validation(http_app):
    """[TC-INT-R25-020] IFC-001 / AC-003-01/02：浏览返回 folder/breadcrumb/items/total/page/page_size/permissions；page_size 截断到 100；非整数 → 400；page<1 → 400；非法 / 不存在的 id → 400 / 404；
    `?token=` → 400；无令牌 → 401。"""
    deps, Client = http_app
    client = Client()
    a = jbody(jreq(client, "POST", "/api/library/folders", {"parent_id": "", "name": "A"}))
    b = jbody(jreq(client, "POST", "/api/library/folders", {"parent_id": a["folder_id"], "name": "B"}))
    page = browse(client, b["folder_id"])
    assert set(page) == {"folder", "breadcrumb", "items", "total", "page", "page_size", "permissions"}
    assert [c["name"] for c in page["breadcrumb"]] == ["A", "B"] and page["folder"]["folder_id"] == b["folder_id"]
    assert page["permissions"] == {"can_manage": True}
    assert browse(client, page_size=100000)["page_size"] == 100
    for q in ("page_size=abc", "page=0", "page=x", "folder_id=zzz"):
        assert jreq(client, "GET", f"/api/library?{q}").status_code == 400, q
    assert jreq(client, "GET", f"/api/library?folder_id={'1' * 32}").status_code == 404
    assert jreq(client, "GET", "/api/library?token=abc").status_code == 400
    assert jreq(client, "GET", "/api/library", headers={}).status_code == 401
    assert jreq(client, "POST", "/api/library").status_code == 405


def test_TC_INT_R25_021_folder_endpoints_validation_conflict_and_delete_confirm(http_app):
    """[TC-INT-R25-021] IFC-003~005 / AC-004-01/02/03 / AC-016-01~03 / AC-006-01：新建 201；非法名称 400 + 稳定码；同名（含大小写）409 + conflicts；第 10 层再建 400 depth_exceeded；
    改名 200 / 同名 409；删除缺 confirm → 400 confirm_required；详情给出子树计数；确认删除 → done。"""
    deps, Client = http_app
    client = Client()
    mk = lambda parent, name: jreq(client, "POST", "/api/library/folders", {"parent_id": parent, "name": name})  # noqa: E731
    d = jbody(mk("", "D"))
    assert mk(d["folder_id"], "设计").status_code == 201
    dup = mk(d["folder_id"], "设计")
    assert dup.status_code == 409 and jbody(dup)["error"]["code"] == "name_conflict" and jbody(dup)["conflicts"][0]["existing"]["name"] == "设计"
    assert mk(d["folder_id"], "DESIGN").status_code == 201, "不同字符（设计 vs DESIGN）互不冲突"
    assert mk(d["folder_id"], "design").status_code == 409, "仅大小写不同 → 与 DESIGN 同名"
    for bad, code in (("", "bad_request"), ("a/b", "name_illegal_char"), ("a\\b", "name_illegal_char"), ("x" * 256, "name_too_long"), ("  ", "bad_request")):
        r = mk(d["folder_id"], bad)
        assert r.status_code == 400 and jbody(r)["error"]["code"] == code, (bad, r.content)
    assert jreq(client, "POST", "/api/library/folders", {"parent_id": d["folder_id"]}).status_code == 400
    assert mk("1" * 32, "x").status_code == 404 and mk("bad id", "x").status_code == 400
    parent = ""
    for i in range(1, 11):
        r = mk(parent, f"L{i}")
        assert r.status_code == 201, (i, r.content)
        parent = jbody(r)["folder_id"]
    deep = mk(parent, "L11")
    assert deep.status_code == 400 and jbody(deep)["error"]["code"] == "depth_exceeded"
    # 改名
    ren = jreq(client, "PATCH", f"/api/library/folders/{d['folder_id']}", {"name": "D2"})
    assert ren.status_code == 200 and jbody(ren)["name"] == "D2"
    other = jbody(mk("", "Other"))
    assert jreq(client, "PATCH", f"/api/library/folders/{other['folder_id']}", {"name": "d2"}).status_code == 409
    # 删除
    put_file(deps, "x.txt", "删除确认", folder_id=d["folder_id"], process=False)
    detail = jbody(jreq(client, "GET", f"/api/library/folders/{d['folder_id']}"))
    assert detail["subtree_folders"] == 2 and detail["subtree_files"] == 1
    assert jreq(client, "DELETE", f"/api/library/folders/{d['folder_id']}", {}).status_code == 400
    assert jbody(jreq(client, "DELETE", f"/api/library/folders/{d['folder_id']}", {"confirm": False}))["error"]["code"] == "confirm_required"
    assert jreq(client, "DELETE", f"/api/library/folders/{d['folder_id']}", {"confirm": True, "max_files": 0}).status_code == 400
    done = jbody(jreq(client, "DELETE", f"/api/library/folders/{d['folder_id']}", {"confirm": True}))
    assert done["done"] is True and done["deleted_files"] == 1 and done["failed"] == [] and done["remaining_files"] == 0


def test_TC_INT_R25_022_move_endpoint_contract_conflict_and_overwrite(http_app):
    """[TC-INT-R25-022] IFC-006 / AC-013-01/03/04 / D-06：移动 200；冲突无 resolution → 409 + conflicts[]（含发起方 entry），台账不变；overwrite → 200 且 overwritten 列出被替换文件；
    移到自身 → 400 move_into_self；文件与文件夹互相覆盖 → 400；他项目 / 不存在 → 404；entries 越界 → 400。"""
    deps, Client = http_app
    client = Client()
    mk = lambda parent, name: jbody(jreq(client, "POST", "/api/library/folders", {"parent_id": parent, "name": name}))  # noqa: E731
    src, dst = mk("", "src"), mk("", "dst")
    old = put_file(deps, "x.txt", "目标侧旧文件 内容", folder_id=dst["folder_id"])
    new = put_file(deps, "x.txt", "来源侧新文件 内容", folder_id=src["folder_id"])
    body = {"entries": [{"kind": "file", "id": new.doc_id}], "target_folder_id": dst["folder_id"]}
    r = jreq(client, "POST", "/api/library/move", body)
    assert r.status_code == 409 and jbody(r)["error"]["code"] == "name_conflict"
    c = jbody(r)["conflicts"][0]
    assert c["existing"]["id"] == old.doc_id and c["entry"]["id"] == new.doc_id
    assert get_doc(deps, new.doc_id).folder_id == src["folder_id"]
    ok = jreq(client, "POST", "/api/library/move", {**body, "resolutions": {new.doc_id: "overwrite"}})
    assert ok.status_code == 200, ok.content
    out = jbody(ok)
    assert out["moved"] == [{"kind": "file", "id": new.doc_id}] and out["overwritten"] == [{"id": old.doc_id}]
    assert get_doc(deps, old.doc_id) is None and get_doc(deps, new.doc_id).folder_id == dst["folder_id"]
    into_self = jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "folder", "id": src["folder_id"]}], "target_folder_id": src["folder_id"]})
    assert into_self.status_code == 400 and jbody(into_self)["error"]["code"] == "move_into_self"
    assert jreq(client, "POST", "/api/library/move", {"entries": [], "target_folder_id": ""}).status_code == 400
    assert jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "file", "id": "1" * 32}], "target_folder_id": ""}).status_code == 404
    assert jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "weird", "id": "1" * 32}], "target_folder_id": ""}).status_code == 400
    assert jreq(client, "POST", "/api/library/move", {**body, "resolutions": {new.doc_id: "explode"}}).status_code == 400


def test_TC_INT_R25_023_rename_file_endpoint_ext_change_and_conflict(http_app):
    """[TC-INT-R25-023] IFC-007 / AC-012-01/02：`PATCH /api/files/{id}` 改名 200（状态与三时间不变）；同目录重名 409；改扩展名（含改为另一受支持类型）400 ext_change_not_allowed；他项目 / 不存在 404。"""
    deps, Client = http_app
    client = Client()
    a = put_file(deps, "旧.txt", "改名端点 内容 甲")
    put_file(deps, "新.txt", "改名端点 内容 乙")
    before = find_item(browse(client), "旧.txt")
    ok = jreq(client, "PATCH", f"/api/files/{a.doc_id}", {"name": "更好的名称.txt"})
    assert ok.status_code == 200
    item = jbody(ok)
    assert item["name"] == "更好的名称.txt" and item["status"] == "indexed"
    assert (item["uploaded_at"], item["content_updated_at"], item["indexed_at"]) == (before["uploaded_at"], before["content_updated_at"], before["indexed_at"])
    assert jreq(client, "PATCH", f"/api/files/{a.doc_id}", {"name": "新.txt"}).status_code == 409
    for new_name in ("a.md", "a.docx", "a.exe"):
        r = jreq(client, "PATCH", f"/api/files/{a.doc_id}", {"name": new_name})
        assert r.status_code == 400 and jbody(r)["error"]["code"] == "ext_change_not_allowed", new_name
    assert jreq(client, "PATCH", f"/api/files/{'1' * 32}", {"name": "x.txt"}).status_code == 404
    assert get_doc(deps, a.doc_id).doc_name == "更好的名称.txt"


# --------------------------------------------------------------------------- #
# 批次计划端点
# --------------------------------------------------------------------------- #


def test_TC_INT_R25_030_plan_endpoint_limits_conflicts_and_no_partial_products(http_app):
    """[TC-INT-R25-030] IFC-010 / AC-015-01 / AC-015-02 / AC-011-01：超限 → 400 limit_files（error.details 含 limit/actual）且不产生批次 / 目录 / 文件；
    dry_run=true → 200 含 conflicts 且不落批次；dry_run=false 且冲突未决 → 409 unresolved_conflict + conflicts；解决后 → 201。"""
    deps, Client = http_app
    client = Client()
    entries = [{"client_idx": i, "rel_path": f"big/f{i}.txt", "size": 1} for i in range(1001)]
    r = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": entries})
    assert r.status_code == 400
    err = jbody(r)["error"]
    assert err["code"] == "limit_files" and err["details"] == {"limit": 1000, "actual": 1001}
    assert browse(client)["total"] == 0
    # 深度：从根上传嵌套 11 层 → 400 depth_exceeded
    rel = "/".join(f"d{i}" for i in range(11)) + "/f.txt"
    deep = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [{"client_idx": 0, "rel_path": rel, "size": 5}]})
    assert deep.status_code == 400 and jbody(deep)["error"]["code"] == "depth_exceeded"
    assert browse(client)["total"] == 0, "整体拒绝不产生半成品目录"
    old = put_file(deps, "a.txt", "同名冲突端点 原文件")
    ent = [{"client_idx": 0, "rel_path": "a.txt", "size": 20}]
    dry = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": True, "entries": ent})
    assert dry.status_code == 200 and jbody(dry)["batch_id"] is None
    assert jbody(dry)["conflicts"] == [{"rel_path": "a.txt", "kind": "file", "existing_id": old.doc_id, "existing_name": "a.txt"}]
    commit = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": ent})
    assert commit.status_code == 409 and jbody(commit)["error"]["code"] == "unresolved_conflict" and jbody(commit)["conflicts"]
    resolved = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": ent, "resolutions": {"a.txt": "rename"}})
    assert resolved.status_code == 201 and jbody(resolved)["items"][0]["final_rel_path"] == "a (2).txt"
    # 非法请求体
    assert jreq(client, "POST", "/api/uploads", {"entries": "x"}).status_code == 400
    assert jreq(client, "POST", "/api/uploads", {"entries": [{"client_idx": True, "rel_path": "a.txt", "size": 1}]}).status_code == 400
    assert jreq(client, "POST", "/api/uploads", {"dry_run": "yes", "entries": ent}).status_code == 400
    assert jreq(client, "POST", "/api/uploads", {"target_folder_id": "1" * 32, "entries": ent}).status_code == 404


# --------------------------------------------------------------------------- #
# 权限（真实认证头）：无管理权限 403 / 浏览不要求管理权限 / 跨项目 404 / 归属断言 403
# --------------------------------------------------------------------------- #


@pytest.fixture()
def readonly_member(http_app, monkeypatch):
    """项目成员（已认证、非管理者）：离线策略的 can_manage 判否；其余认证链路（令牌→主体）保持真实。"""
    from ib.context import AllowAllPolicy

    monkeypatch.setattr(AllowAllPolicy, "can_manage", lambda self, ctx: False)
    return http_app


def test_TC_INT_R25_040_non_manager_gets_403_on_every_write_endpoint_and_nothing_changes(http_app, monkeypatch):
    """[TC-INT-R25-040] AC-001-03 / AC-005-03 / AC-008-04 / REQ-NFUNC-005：无管理权限的成员对全部写端点（建 / 改名 / 删 / 移动 / 上传计划 / 逐文件上传 / 更新 / 丢弃更新 / 文件改名 / 批次汇总）→ 403，
    资料库不产生任何目录或文件，已有文件内容 / 状态 / 向量不变；浏览仍可（permissions.can_manage=false）。成对：同一请求在管理者身份下成功。"""
    from ib.context import AllowAllPolicy

    deps, Client = http_app
    client = Client()
    folder = jbody(jreq(client, "POST", "/api/library/folders", {"parent_id": "", "name": "既有"}))
    doc = put_file(deps, "keep.txt", "只读成员不得改动 内容", folder_id=folder["folder_id"])
    before = get_doc(deps, doc.doc_id)
    plan_ok = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": True, "entries": [{"client_idx": 0, "rel_path": "n/new.txt", "size": 5}]})
    assert plan_ok.status_code == 200, "管理者身份下同一请求成功"
    monkeypatch.setattr(AllowAllPolicy, "can_manage", lambda self, ctx: False)
    writes = [
        ("POST", "/api/library/folders", {"parent_id": "", "name": "新建"}),
        ("PATCH", f"/api/library/folders/{folder['folder_id']}", {"name": "改名"}),
        ("DELETE", f"/api/library/folders/{folder['folder_id']}", {"confirm": True}),
        ("POST", "/api/library/move", {"entries": [{"kind": "file", "id": doc.doc_id}], "target_folder_id": ""}),
        ("POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [{"client_idx": 0, "rel_path": "n/new.txt", "size": 5}]}),
        ("GET", f"/api/uploads/{'1' * 32}", None),
        ("PATCH", f"/api/files/{doc.doc_id}", {"name": "x.txt"}),
        ("DELETE", f"/api/files/{doc.doc_id}/revision", None),
    ]
    for method, path, body in writes:
        r = jreq(client, method, path, body)
        assert r.status_code == 403, (method, path, r.content)
    assert put_multipart(client, f"/api/uploads/{'1' * 32}/items/0", "n.txt", b"hello").status_code == 403
    assert _revise(client, doc.doc_id, "keep.txt", "试图更新").status_code == 403
    after = get_doc(deps, doc.doc_id)
    assert (after.doc_name, after.content_sha256, after.status, after.folder_id, after.chunk_count) == (
        before.doc_name, before.content_sha256, before.status, before.folder_id, before.chunk_count,
    )
    assert deps.tree.get_revision_of(S, doc.doc_id) is None
    top = browse(client)
    assert names_in(top) == ["既有"] and top["permissions"] == {"can_manage": False}, "浏览不要求管理权限；无新建目录"
    inner = browse(client, folder["folder_id"])
    assert names_in(inner) == ["keep.txt"] and inner["permissions"]["can_manage"] is False
    assert [h for h in search(deps, "只读成员不得改动 内容").hits if h.doc_id == doc.doc_id], "向量不变"


@pytest.fixture()
def acct(accounts_app):
    deps, Client = accounts_app
    client = Client()
    pw = "R25-Admin-New-1!"
    token = jbody(login(client, "admin", R13_ADMIN_PASSWORD))["token"]
    assert change_password(client, token, R13_ADMIN_PASSWORD, pw).status_code == 200
    ops_pw, ops_new = "GroupD-Test-Ops-1!", "R25-Ops-New-1!"
    created = client.post(
        "/api/accounts",
        data=json.dumps({"username": "ops_r25", "password": ops_pw, "project_id": PID}),
        content_type="application/json",
        **bearer(token),
    )
    assert created.status_code == 201, created.content
    ops_token = jbody(login(client, "ops_r25", ops_pw))["token"]
    assert change_password(client, ops_token, ops_pw, ops_new).status_code == 200
    return deps, client, token, ops_token


def _h(token, project=None):
    h = dict(bearer(token))
    if project:
        h["HTTP_X_IB_PROJECT"] = project
    return h


def test_TC_INT_R25_041_cross_project_id_access_is_404_indistinguishable_and_assertion_failure_is_403(acct):
    """[TC-INT-R25-041] AC-003-03 / REQ-NFUNC-005（真实账户体系令牌）：P1 成员以目录 id 访问 P2 的目录 → 404，响应体与访问一个不存在的 id 逐字相同，不泄露 P2 目录名；
    其余按资源 id 的入口（详情 / 改名 / 删除 / 移动 / 文件改名 / 批次）同样 404；请求项目头与令牌所属项目不一致（归属断言失败）→ 403 project_mismatch。"""
    deps, client, admin, ops = acct
    p2_folder = jbody(jreq(client, "POST", "/api/library/folders", {"parent_id": "", "name": "P2-秘密目录"}, _h(admin, "p_beta")))
    p2_doc = put_file(deps, "p2.txt", "乙项目专属文件", folder_id=p2_folder["folder_id"], project_id="p_beta", process=False)
    fid = p2_folder["folder_id"]
    cross = jreq(client, "GET", f"/api/library?folder_id={fid}", None, _h(ops))  # ops 绑定 p_alpha
    missing = jreq(client, "GET", f"/api/library?folder_id={'a' * 32}", None, _h(ops))
    assert cross.status_code == missing.status_code == 404
    assert cross.content == missing.content, "跨项目与不存在必须不可区分"
    assert "P2-秘密目录" not in cross.content.decode()
    attempts = [
        ("GET", f"/api/library/folders/{fid}", None),
        ("PATCH", f"/api/library/folders/{fid}", {"name": "hijack"}),
        ("DELETE", f"/api/library/folders/{fid}", {"confirm": True}),
        ("POST", "/api/library/move", {"entries": [{"kind": "folder", "id": fid}], "target_folder_id": ""}),
        ("POST", "/api/library/move", {"entries": [{"kind": "file", "id": p2_doc.doc_id}], "target_folder_id": ""}),
        ("PATCH", f"/api/files/{p2_doc.doc_id}", {"name": "hijack.txt"}),
        ("DELETE", f"/api/files/{p2_doc.doc_id}/revision", None),
        ("POST", "/api/uploads", {"target_folder_id": fid, "dry_run": True, "entries": [{"client_idx": 0, "rel_path": "a.txt", "size": 5}]}),
    ]
    for method, path, body in attempts:
        r = jreq(client, method, path, body, _h(ops))
        assert r.status_code == 404, (method, path, r.status_code, r.content)
    # 他项目的数据完好
    still = browse(client, "", _h(admin, "p_beta"))
    assert names_in(still) == ["P2-秘密目录"] and get_doc(deps, p2_doc.doc_id, "p_beta").doc_name == "p2.txt"
    # 归属断言失败：ops 声明他项目 → 403（而非 404）
    mismatch = jreq(client, "GET", "/api/library", None, _h(ops, "p_beta"))
    assert mismatch.status_code == 403 and jbody(mismatch)["error"]["code"] == "project_mismatch"
    # 成对：admin（全局）以 P2 身份访问同一目录 → 200
    ok = jreq(client, "GET", f"/api/library?folder_id={fid}", None, _h(admin, "p_beta"))
    assert ok.status_code == 200 and jbody(ok)["folder"]["name"] == "P2-秘密目录"
    # 他项目批次同样 404
    plan = jbody(jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [{"client_idx": 0, "rel_path": "z.txt", "size": 5}]}, _h(admin, "p_beta")))
    assert jreq(client, "GET", f"/api/uploads/{plan['batch_id']}", None, _h(ops)).status_code == 404


def test_TC_INT_R25_042_ops_member_can_manage_own_project_library(acct):
    """[TC-INT-R25-042] 成对正例：绑定本项目的运维账户（管理角色）可在本项目完成 建目录 → 批次上传 → 浏览，permissions.can_manage=true。"""
    deps, client, admin, ops = acct
    mk = jreq(client, "POST", "/api/library/folders", {"parent_id": "", "name": "运维目录"}, _h(ops))
    assert mk.status_code == 201
    target = jbody(mk)["folder_id"]
    _, results, _ = upload_batch(client, {"子/a.txt": b"ops uploads a file here"}, target=target, headers=_h(ops))
    assert results[0]["state"] == "accepted"
    listing = browse(client, "", _h(ops))
    assert names_in(listing) == ["运维目录"] and listing["permissions"]["can_manage"] is True
    assert names_in(browse(client, target, _h(ops))) == ["子"]
