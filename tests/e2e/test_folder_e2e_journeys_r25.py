"""[R25 / GROUP_D] E2E 关键路径 —— 资料管理：文件夹上传与云盘式目录管理（Must Have 故事全覆盖）。

critical path 口径：**替代**（真实 Django 测试客户端 + 真实认证头 + 真实上传 / worker 处理 / 检索管线的多步 API 旅程）；
项目没有浏览器 E2E 框架。每个用例在 docstring 标注 US / AC。
Must Have 故事：US-001~011、US-015、US-017（共 13 个）。离线：内存 / 临时目录 SQLite + 假 embedder / 向量库。
"""

from __future__ import annotations

import io
import json
import sqlite3

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import R13_ADMIN_PASSWORD, bearer, change_password, login, offline_raw
from folder_r25_support import (
    AUTH,
    PID,
    FailingEmbedder,
    browse,
    find_item,
    get_doc,
    hits_containing,
    install_clock,
    jbody,
    jreq,
    names_in,
    put_file,
    put_multipart,
    scope_of,
    search,
    sqlite_deps,
    upload_batch,
)

S = scope_of()


def _mk(client, parent, name, headers=None):
    r = jreq(client, "POST", "/api/library/folders", {"parent_id": parent, "name": name}, headers)
    return r


def _revise(client, doc_id, name, content: str | bytes, **form):
    data = content.encode("utf-8") if isinstance(content, str) else content
    return client.post(f"/api/files/{doc_id}/revision", {"file": SimpleUploadedFile(name, data), **form}, **AUTH)


# --------------------------------------------------------------------------- #
# US-001 / US-002 / US-010：整个文件夹上传 → 汇总 → 浏览 → 索引 → 问答可检索（含引用路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_001_folder_upload_journey_structure_summary_and_retrieval(http_app):
    """[TC-E2E-R25-001] US-001 / US-002 / US-010：选择本地文件夹 A（A/x.txt、A/B/y.md 合规；A/bad.exe 不支持；A/fake/q.pdf 魔数不符；A/empty 目录无文件不会被客户端提交）→
    dry-run → 提交批次 → 逐文件 PUT → 汇总 成功 2 / 跳过 2 / 失败 0（和 = 4）→ 浏览结构与本地一致（空 / 全跳过目录不创建，AC-001-04）→ worker 索引 →
    就 y.md 独有内容检索：命中该文件、chunk 数 > 0、引用路径 `A/B/y.md`（AC-010-01 / AC-014-01）。"""
    deps, Client = http_app
    client = Client()
    files = {
        "A/x.txt": "文件夹上传 x 文件正文 冷却塔".encode(),
        "A/B/y.md": "# y 文档\n\n文件夹上传 y 文件独有内容 板式换热器".encode(),
        "A/bad.exe": b"MZ not allowed",
        "A/fake/q.pdf": b"this is definitely not a pdf",
    }
    entries = [{"client_idx": i, "rel_path": rel, "size": len(b)} for i, (rel, b) in enumerate(files.items())]
    dry = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": True, "entries": entries})
    assert dry.status_code == 200 and jbody(dry)["batch_id"] is None and jbody(dry)["conflicts"] == []
    assert browse(client)["total"] == 0, "dry-run 不得改动资料库"
    plan, results, bid = upload_batch(client, files)
    assert [(r["client_idx"], r["state"]) for r in results] == [(0, "accepted"), (1, "accepted"), (2, "skipped"), (3, "skipped")]
    assert results[2]["reason_code"] == "UNSUPPORTED_TYPE" and results[3]["reason_code"] == "MAGIC_MISMATCH"
    summary = jbody(jreq(client, "GET", f"/api/uploads/{bid}"))
    assert (summary["accepted"], summary["skipped"], summary["failed"], summary["pending"], summary["total"]) == (2, 2, 0, 0, 4)
    assert summary["accepted"] + summary["skipped"] + summary["failed"] == summary["total"]
    skipped_paths = {i["rel_path"]: i["reason_code"] for i in summary["items"] if i["state"] == "skipped"}
    assert skipped_paths == {"A/bad.exe": "UNSUPPORTED_TYPE", "A/fake/q.pdf": "MAGIC_MISMATCH"}
    # 结构
    root = browse(client)
    assert names_in(root) == ["A"]
    a = browse(client, find_item(root, "A")["folder_id"])
    assert names_in(a, "file") == ["x.txt"] and names_in(a, "folder") == ["B"], "fake / bad.exe 所在目录与文件均不得被创建"
    b = browse(client, find_item(a, "B")["folder_id"])
    assert names_in(b, "file") == ["y.md"] and [c["name"] for c in b["breadcrumb"]] == ["A", "B"]
    assert find_item(b, "y.md")["status"] == "pending", "初始状态为待处理"
    # worker 索引 → 问答检索
    deps.lifecycle.process_pending("e2e-w", 10)
    y = find_item(browse(client, b["folder"]["folder_id"]), "y.md")
    assert y["status"] == "indexed" and y["chunk_count"] > 0 and y["indexed_at"]
    res = search(deps, "文件夹上传 y 文件独有内容 板式换热器")
    assert res.degraded is False
    cited = [h for h in res.hits if h.doc_id == y["doc_id"]]
    assert cited and cited[0].doc_path == "A/B/y.md" and cited[0].doc_name == "y.md"


def test_TC_E2E_R25_002_hundred_file_summary_95_5_0_and_monotonic_progress(http_app):
    """[TC-E2E-R25-002] US-002：含 100 个文件（95 合规、3 个不支持类型、1 个空文件、1 个超 50MB）的文件夹 →
    计划阶段已分类；逐文件上传期间“已处理 N / 100”单调不减且结束时 N=100；汇总 成功 95 / 跳过 5 / 失败 0（和 = 100），5 个跳过项带相对路径与原因（AC-002-01/02）。"""
    deps, Client = http_app
    client = Client()
    entries = [{"client_idx": i, "rel_path": f"批/ok{i:03d}.txt", "size": 40} for i in range(95)]
    entries += [
        {"client_idx": 95, "rel_path": "批/a.exe", "size": 5},
        {"client_idx": 96, "rel_path": "批/b.dll", "size": 5},
        {"client_idx": 97, "rel_path": "批/c.markdown", "size": 5},
        {"client_idx": 98, "rel_path": "批/empty.txt", "size": 0},
        {"client_idx": 99, "rel_path": "批/huge.pdf", "size": 51 * 1024 * 1024},
    ]
    plan = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": entries})
    assert plan.status_code == 201
    pb = jbody(plan)
    bid = pb["batch_id"]
    assert (pb["total"], pb["accepted_count"], pb["skipped_count"]) == (100, 95, 5)
    processed = []
    for i in range(95):
        r = put_multipart(client, f"/api/uploads/{bid}/items/{i}", f"ok{i:03d}.txt", f"批量文件 {i} 正文内容".encode())
        assert r.status_code == 200 and jbody(r)["state"] == "accepted"
        s = jbody(jreq(client, "GET", f"/api/uploads/{bid}"))
        processed.append(s["accepted"] + s["skipped"] + s["failed"])
    assert processed == sorted(processed) and processed[0] >= 6 and processed[-1] == 100, "N 单调不减，结束时 N=100"
    end = jbody(jreq(client, "GET", f"/api/uploads/{bid}"))
    assert (end["accepted"], end["skipped"], end["failed"], end["pending"]) == (95, 5, 0, 0)
    reasons = {i["rel_path"]: i["reason_code"] for i in end["items"] if i["state"] == "skipped"}
    assert reasons == {
        "批/a.exe": "UNSUPPORTED_TYPE", "批/b.dll": "UNSUPPORTED_TYPE", "批/c.markdown": "UNSUPPORTED_TYPE",
        "批/empty.txt": "EMPTY_FILE", "批/huge.pdf": "TOO_LARGE",
    }
    folder = find_item(browse(client), "批")
    assert browse(client, folder["folder_id"], page_size=100)["total"] == 95


# --------------------------------------------------------------------------- #
# US-003：云盘式浏览（含分页、跨项目 404 / 归属断言 403）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_003_browse_journey_breadcrumb_back_and_pagination(http_app):
    """[TC-E2E-R25-003] US-003：逐级进入 A → B，页面仅含各目录直接子项，面包屑依次为 [A]、[A,B]，点击面包屑 A 回到 A 的内容；150 个条目分页（每页 ≤100）无重复无遗漏、刷新顺序一致（AC-003-01/02）。"""
    deps, Client = http_app
    client = Client()
    a = jbody(_mk(client, "", "A"))
    b = jbody(_mk(client, a["folder_id"], "B"))
    put_file(deps, "in_a.txt", "A 目录内的文件", folder_id=a["folder_id"], process=False)
    put_file(deps, "in_b.txt", "B 目录内的文件", folder_id=b["folder_id"], process=False)
    in_a, in_b = browse(client, a["folder_id"]), browse(client, b["folder_id"])
    assert names_in(in_a) == ["B", "in_a.txt"] and names_in(in_b) == ["in_b.txt"]
    assert [c["name"] for c in in_a["breadcrumb"]] == ["A"] and [c["name"] for c in in_b["breadcrumb"]] == ["A", "B"]
    assert browse(client, in_b["breadcrumb"][0]["folder_id"]) == in_a, "点击面包屑中的 A 回到 A 的内容"
    big = jbody(_mk(client, "", "大目录"))["folder_id"]
    for i in range(60):
        assert _mk(client, big, f"d{i:03d}").status_code == 201
    for i in range(90):
        put_file(deps, f"f{i:03d}.txt", f"分页文件 {i}", folder_id=big, process=False)
    p1, p2 = browse(client, big, page=1, page_size=100), browse(client, big, page=2, page_size=100)
    assert p1["total"] == 150 and len(p1["items"]) == 100 and len(p2["items"]) == 50
    names = names_in(p1) + names_in(p2)
    assert len(names) == len(set(names)) == 150
    assert names_in(p1)[:60] == [f"d{i:03d}" for i in range(60)], "文件夹在前，其后按名称升序"
    assert browse(client, big, page=1, page_size=100) == p1, "刷新顺序一致"


@pytest.fixture()
def acct(accounts_app):
    deps, Client = accounts_app
    client = Client()
    token = jbody(login(client, "admin", R13_ADMIN_PASSWORD))["token"]
    assert change_password(client, token, R13_ADMIN_PASSWORD, "R25-E2E-Admin-1!").status_code == 200
    created = client.post(
        "/api/accounts",
        data=json.dumps({"username": "ops_e2e25", "password": "GroupD-Test-Ops-1!", "project_id": PID}),
        content_type="application/json",
        **bearer(token),
    )
    assert created.status_code == 201
    ops = jbody(login(client, "ops_e2e25", "GroupD-Test-Ops-1!"))["token"]
    assert change_password(client, ops, "GroupD-Test-Ops-1!", "R25-E2E-Ops-1!").status_code == 200
    return deps, client, token, ops


def _h(token, project=None):
    h = dict(bearer(token))
    if project:
        h["HTTP_X_IB_PROJECT"] = project
    return h


def test_TC_E2E_R25_004_cross_project_404_and_assertion_failure_403_journey(acct):
    """[TC-E2E-R25-004] US-003 / AC-003-03：P1 的成员以目录 id 请求 P2 的目录 → 404，且响应与请求不存在的 id 完全不可区分、不泄露 P2 的目录 / 文件名；
    令牌项目与请求项目头不一致（归属断言失败）→ 403；P2 内容在整个过程中完好；成对：P2 管理者访问自己的目录成功。"""
    deps, client, admin, ops = acct
    p2_dir = jbody(_mk(client, "", "乙项目机密目录", _h(admin, "p_beta")))
    p2_file = put_file(deps, "乙项目机密.txt", "乙项目独有机密内容 余热回收", folder_id=p2_dir["folder_id"], project_id="p_beta")
    cross = jreq(client, "GET", f"/api/library?folder_id={p2_dir['folder_id']}", None, _h(ops))
    ghost = jreq(client, "GET", f"/api/library?folder_id={'c' * 32}", None, _h(ops))
    assert (cross.status_code, ghost.status_code) == (404, 404) and cross.content == ghost.content
    assert "机密" not in cross.content.decode()
    assert jreq(client, "GET", f"/api/library/folders/{p2_dir['folder_id']}", None, _h(ops)).status_code == 404
    mism = jreq(client, "GET", "/api/library", None, _h(ops, "p_beta"))
    assert mism.status_code == 403 and jbody(mism)["error"]["code"] == "project_mismatch"
    own = jreq(client, "GET", f"/api/library?folder_id={p2_dir['folder_id']}", None, _h(admin, "p_beta"))
    assert own.status_code == 200 and names_in(jbody(own)) == ["乙项目机密.txt"]
    assert get_doc(deps, p2_file.doc_id, "p_beta").status == "indexed"
    # 问答隔离：P1 检索不到 P2 的独有内容（AC-010-02）
    leak = search(deps, "乙项目独有机密内容 余热回收", project_id=PID)
    assert leak.degraded is False and not [h for h in leak.hits if h.doc_id == p2_file.doc_id]
    seen = search(deps, "乙项目独有机密内容 余热回收", project_id="p_beta")
    assert [h for h in seen.hits if h.doc_id == p2_file.doc_id]


# --------------------------------------------------------------------------- #
# US-004 / US-005：新建 / 重命名文件夹，并保持检索与引用路径
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_005_create_rename_folder_journey_keeps_files_indexed_and_citation_path(http_app):
    """[TC-E2E-R25-005] US-004 / US-005 / US-016：新建 D → 在 D 新建 `设计`（立即可见、刷新后仍在）→ 同名 / 大小写变体被拒 → 把 `设计` 重命名为 `新名`，
    其内 3 个已索引文件仍在其中且仍为“已索引”，问答引用路径显示 `D/新名/…` 不再出现 `设计`；同级重名被拒且原名保持。"""
    deps, Client = http_app
    client = Client()
    d = jbody(_mk(client, "", "D"))
    sheji = jbody(_mk(client, d["folder_id"], "设计"))
    assert names_in(browse(client, d["folder_id"])) == ["设计"] and names_in(browse(client, sheji["folder_id"])) == []
    for dup in ("设计", " 设计 "):
        assert _mk(client, d["folder_id"], dup).status_code == 409
    for i in range(3):
        put_file(deps, f"d{i}.txt", f"重命名旅程专属内容{i} 冷冻水", folder_id=sheji["folder_id"])
    other = jbody(_mk(client, d["folder_id"], "其它"))
    assert jreq(client, "PATCH", f"/api/library/folders/{other['folder_id']}", {"name": "设计"}).status_code == 409
    assert find_item(browse(client, d["folder_id"]), "其它")["folder_id"] == other["folder_id"], "被拒绝的重命名不改原名"
    ren = jreq(client, "PATCH", f"/api/library/folders/{sheji['folder_id']}", {"name": "新名"})
    assert ren.status_code == 200
    inner = browse(client, sheji["folder_id"])
    assert [i["status"] for i in inner["items"]] == ["indexed"] * 3
    assert [c["name"] for c in inner["breadcrumb"]] == ["D", "新名"]
    res = search(deps, "重命名旅程专属内容1 冷冻水")
    paths = {h.doc_path for h in res.hits}
    assert paths and all(p.startswith("D/新名/") for p in paths) and not any("设计" in p for p in paths)


# --------------------------------------------------------------------------- #
# US-006：递归删除（二次确认 → 删除 → 检索命中 0；部分失败可见 → 恢复）
# --------------------------------------------------------------------------- #


def _delete_loop(client, folder_id, max_files=None):
    out = []
    for _ in range(20):
        body = {"confirm": True}
        if max_files:
            body["max_files"] = max_files
        r = jreq(client, "DELETE", f"/api/library/folders/{folder_id}", body)
        assert r.status_code == 200, r.content
        step = jbody(r)
        out.append(step)
        if step["done"] or step["failed"]:
            break
    return out


def test_TC_E2E_R25_006_delete_folder_journey_confirm_then_retrieval_zero(http_app):
    """[TC-E2E-R25-006] US-006 AC-006-01/02：A 含 2 个子文件夹与 10 个文件 → 详情给出“2 个子文件夹、10 个文件”；未确认（缺 confirm）不删；取消（不调用）后内容原样；
    确认后分步删除至 done，A 及全部内容消失，10 个文件的向量数为 0，用其中任一文件独有关键词检索命中该文件 0 条；其它项目内文件不受影响。"""
    deps, Client = http_app
    client = Client()
    a = jbody(_mk(client, "", "待删"))
    b = jbody(_mk(client, a["folder_id"], "子1"))
    _mk(client, a["folder_id"], "子2")
    ids = []
    for i in range(10):
        ids.append(put_file(deps, f"del{i}.txt", f"删除旅程独有关键词{i} 水泵房", folder_id=(a["folder_id"] if i % 2 else b["folder_id"])).doc_id)
    keep = put_file(deps, "keep.txt", "旅程中保留的文件 水泵房")
    d = jbody(jreq(client, "GET", f"/api/library/folders/{a['folder_id']}"))
    assert (d["subtree_folders"], d["subtree_files"]) == (2, 10)
    assert jreq(client, "DELETE", f"/api/library/folders/{a['folder_id']}", {}).status_code == 400
    assert get_doc(deps, ids[0]) is not None and deps.tree.count_subtree(S, a["folder_id"]).files == 10
    assert [h for h in search(deps, "删除旅程独有关键词4 水泵房").hits if h.doc_id == ids[4]]
    steps = _delete_loop(client, a["folder_id"], max_files=4)
    assert [s["deleted_files"] for s in steps] == [4, 4, 2] and steps[-1]["done"] is True and steps[-1]["failed"] == []
    assert names_in(browse(client)) == ["keep.txt"]
    for i, doc_id in enumerate(ids):
        assert get_doc(deps, doc_id) is None and deps.vectors.delete_doc_everywhere(PID, S, doc_id) == 0
        assert not [h for h in search(deps, f"删除旅程独有关键词{i} 水泵房").hits if h.doc_id == doc_id]
    assert [h for h in search(deps, "旅程中保留的文件 水泵房").hits if h.doc_id == keep.doc_id]
    assert jreq(client, "GET", f"/api/library/folders/{a['folder_id']}").status_code == 404


def test_TC_E2E_R25_007_delete_partial_failure_is_visible_then_recoverable(http_app, monkeypatch):
    """[TC-E2E-R25-007] US-006 AC-006-03 / AC-006-04：1 个文件向量清理失败 → 响应 failed 列出该文件（稳定错误码，无内部细节）、done=false、remaining_files=1；该文件及其目录链仍可见可再次删除，
    且不出现“列表看不到但仍能检索到”；处理中（parsing）的文件一并被删除且 worker 安全退出；向量库恢复后再删 → done=true、命中 0。"""
    deps, Client = http_app
    client = Client()
    a = jbody(_mk(client, "", "部分失败"))["folder_id"]
    sub = jbody(_mk(client, a, "内层"))["folder_id"]
    docs = [put_file(deps, f"p{i}.txt", f"部分失败旅程关键词{i} 阀门", folder_id=(sub if i == 3 else a)) for i in range(6)]
    busy = put_file(deps, "busy.txt", "处理中的文件 阀门", folder_id=a, process=False)
    claimed = deps.ledger.claim_pending("e2e-w", 60, 5)
    assert [c.doc_id for c in claimed] == [busy.doc_id]
    victim = docs[3]
    real = deps.vectors.delete_doc_everywhere

    def flaky(project_id, scope, doc_id):
        if doc_id == victim.doc_id:
            raise RuntimeError("internal qdrant detail: boom")
        return real(project_id, scope, doc_id)

    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", flaky)
    r = jreq(client, "DELETE", f"/api/library/folders/{a}", {"confirm": True})
    assert r.status_code == 200
    step = jbody(r)
    assert step["done"] is False and step["remaining_files"] == 1 and step["deleted_files"] == 6
    assert [f["doc_id"] for f in step["failed"]] == [victim.doc_id] and step["failed"][0]["name"] == "p3.txt"
    assert "qdrant" not in json.dumps(step) and step["failed"][0]["path"] == "部分失败/内层/p3.txt"
    assert find_item(browse(client), "部分失败")["folder_id"] == a
    assert names_in(browse(client, sub)) == ["p3.txt"], "失败文件及其目录链仍可见"
    assert get_doc(deps, busy.doc_id) is None, "处理中的文件也被删除"
    from ib.lifecycle import _DeletedConcurrently

    with pytest.raises(_DeletedConcurrently):
        deps.lifecycle._process_one(claimed[0], "e2e-w")  # worker 稍后到达：安全退出，不写回
    assert not [h for h in search(deps, "处理中的文件 阀门").hits if h.doc_id == busy.doc_id]
    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", real)
    done = jbody(jreq(client, "DELETE", f"/api/library/folders/{a}", {"confirm": True}))
    assert done["done"] is True and done["failed"] == [] and done["deleted_files"] == 1
    assert browse(client)["total"] == 0
    assert not [h for h in search(deps, "部分失败旅程关键词3 阀门").hits if h.doc_id == victim.doc_id]


# --------------------------------------------------------------------------- #
# US-007：多文件上传到指定目录
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_008_multi_file_upload_into_current_folder(http_app):
    """[TC-E2E-R25-008] US-007 AC-007-01/02：在目录 D 一次选择 3 个合规文件 + 1 个不支持类型 → D 下出现 3 个文件（初始“待处理”，随后“已索引”），根目录不出现；
    不支持者给出“不支持的文件类型”（UNSUPPORTED_TYPE）且不入库。"""
    deps, Client = http_app
    client = Client()
    d = jbody(_mk(client, "", "D"))["folder_id"]
    files = {"f1.txt": b"multi one content", "f2.md": b"# two\n\nmulti two content", "bad.exe": b"MZ", "f3.txt": b"multi three content"}
    plan, results, _ = upload_batch(client, files, target=d)
    assert [r["state"] for r in results] == ["accepted", "accepted", "skipped", "accepted"] and results[2]["reason_code"] == "UNSUPPORTED_TYPE"
    inner = browse(client, d)
    assert sorted(names_in(inner)) == ["f1.txt", "f2.md", "f3.txt"] and {i["status"] for i in inner["items"]} == {"pending"}
    assert browse(client)["total"] == 1 and names_in(browse(client)) == ["D"], "根目录下不出现这些文件"
    deps.lifecycle.process_pending("w", 10)
    assert {i["status"] for i in browse(client, d)["items"]} == {"indexed"}


# --------------------------------------------------------------------------- #
# US-008 / US-009：更新（旧版可检索 → 成功切换 / 失败保留旧版）与三个时间
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_009_update_file_journey_success_switch_and_failure_keeps_old(http_app, monkeypatch):
    """[TC-E2E-R25-009] US-008 AC-008-01/02/03：规范.txt 已索引（K1）→ 更新为新版（K2）：更新期间 K1 仍命中、K2 未命中；worker 完成后 状态“已索引”、K1 命中 0、K2 命中、列表仅一条、目录与名称不变；
    再次更新为新版 K3 但索引失败 → 状态显示“更新失败”及原因，旧版（K2）保持可检索，页面不显示为新版已索引；修复后重试成功 → K3 命中、K2 为 0。"""
    deps, Client = http_app
    client = Client()
    folder = jbody(_mk(client, "", "规范库"))["folder_id"]
    live = put_file(deps, "规范.txt", "规范旅程正文 旧版独有关键词甲乙", folder_id=folder)
    assert _revise(client, live.doc_id, "规范.txt", "规范旅程正文 新版独有关键词丙丁").status_code == 202
    item = find_item(browse(client, folder), "规范.txt")
    assert item["status"] == "indexed" and item["update_state"] == "updating"
    assert hits_containing(search(deps, "规范旅程正文 旧版独有关键词甲乙"), "旧版独有关键词甲乙"), "更新期间旧版仍可检索"
    assert not hits_containing(search(deps, "规范旅程正文 新版独有关键词丙丁"), "新版独有关键词丙丁")
    deps.lifecycle.process_pending("w", 10)
    after = browse(client, folder)
    assert names_in(after) == ["规范.txt"] and after["items"][0]["status"] == "indexed" and after["items"][0]["update_state"] is None
    assert after["items"][0]["content_updated_at"]
    assert hits_containing(search(deps, "规范旅程正文 新版独有关键词丙丁"), "新版独有关键词丙丁")
    assert not hits_containing(search(deps, "规范旅程正文 旧版独有关键词甲乙"), "旧版独有关键词甲乙")
    # --- 再次更新，索引失败 ---
    cur = after["items"][0]["doc_id"]
    assert _revise(client, cur, "规范.txt", "规范旅程正文 第三版独有关键词戊己").status_code == 202
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    deps.lifecycle.process_pending("w", 10)
    failed = find_item(browse(client, folder), "规范.txt")
    assert failed["status"] == "indexed" and failed["update_state"] == "update_failed" and failed["update_error_code"]
    assert hits_containing(search(deps, "规范旅程正文 新版独有关键词丙丁"), "新版独有关键词丙丁"), "失败后旧版（当前版）保持可检索"
    assert not hits_containing(search(deps, "规范旅程正文 第三版独有关键词戊己"), "第三版独有关键词戊己")
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    assert jreq(client, "POST", f"/api/files/{cur}/retry").status_code == 200
    deps.lifecycle.process_pending("w", 10)
    assert hits_containing(search(deps, "规范旅程正文 第三版独有关键词戊己"), "第三版独有关键词戊己")
    assert not hits_containing(search(deps, "规范旅程正文 新版独有关键词丙丁"), "新版独有关键词丙丁")
    assert browse(client, folder)["total"] == 1


def test_TC_E2E_R25_010_three_times_and_status_journey(http_app, monkeypatch):
    """[TC-E2E-R25-010] US-009 AC-009-01~04：上传 T1、索引成功 T2、从未更新(—) → 更新于 T3 且新版索引成功 T4（上传时间仍 T1）→ 仅重命名 / 移动后三个时间不变 →
    索引失败的文件 状态“失败”+ 原因 + 索引成功时间“—” → embedding 变更重建后索引成功时间刷新为 T5，上传时间与最近更新时间不变。"""
    deps, Client = http_app
    client = Client()
    clock = install_clock(monkeypatch)
    d = jbody(_mk(client, "", "D"))["folder_id"]
    target = jbody(_mk(client, "", "目标"))["folder_id"]
    up = put_file(deps, "t.txt", "时间旅程正文 甲", folder_id=d, process=False)
    clock.tick(30)
    deps.lifecycle.process_pending("w", 10)
    v1 = find_item(browse(client, d), "t.txt")
    assert v1["uploaded_at"] == "2026-03-01T00:00:00Z" and v1["indexed_at"] == "2026-03-01T00:00:30Z"
    assert v1["content_updated_at"] is None and v1["status"] == "indexed"
    clock.tick(1000)
    assert _revise(client, v1["doc_id"], "t.txt", "时间旅程正文 乙").status_code == 202
    clock.tick(20)
    deps.lifecycle.process_pending("w", 10)
    v2 = find_item(browse(client, d), "t.txt")
    assert v2["uploaded_at"] == v1["uploaded_at"] and v2["content_updated_at"] == "2026-03-01T00:17:30Z" == v2["indexed_at"]
    clock.tick(500)
    assert jreq(client, "PATCH", f"/api/files/{v2['doc_id']}", {"name": "改名.txt"}).status_code == 200
    mv = jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "file", "id": v2["doc_id"]}], "target_folder_id": target})
    assert mv.status_code == 200
    v3 = find_item(browse(client, target), "改名.txt")
    assert (v3["uploaded_at"], v3["content_updated_at"], v3["indexed_at"]) == (v2["uploaded_at"], v2["content_updated_at"], v2["indexed_at"])
    # 失败文件
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    put_file(deps, "bad.txt", "会失败的文件", folder_id=d)
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    bad = find_item(browse(client, d), "bad.txt")
    assert bad["status"] == "failed" and bad["error_code"] and bad["indexed_at"] is None
    deps.lifecycle.retry_document(S, bad["doc_id"])
    # 重建：T5
    clock.tick(86400)
    job = deps.rebuild.start_rebuild(PID, deps.rebuild.plan_rebuild(PID))
    deps.lifecycle.process_pending("rw", 50)
    deps.rebuild.step_rebuild(job, "rw", 50)
    deps.rebuild.activate_version(PID, "2")
    v5 = find_item(browse(client, target), "改名.txt")
    assert v5["indexed_at"] == "2026-03-02T00:25:50Z" and v5["indexed_at"] != v3["indexed_at"]
    assert (v5["uploaded_at"], v5["content_updated_at"], v5["status"]) == (v3["uploaded_at"], v3["content_updated_at"], "indexed")
    assert find_item(browse(client, d), "bad.txt")["status"] == "indexed" and up.doc_id


# --------------------------------------------------------------------------- #
# US-010：失败文件无命中且显示“失败”；上传内容均可被检索
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_011_all_upload_paths_are_retrievable_and_failed_is_not(http_app, monkeypatch):
    """[TC-E2E-R25-011] US-010 AC-010-01/03：文件夹上传、目录内上传、更新后的新内容都可检索（引用来源含该文件且 chunk 数 > 0）；索引失败的文件检索无命中且列表状态为“失败”（不是已索引）。"""
    deps, Client = http_app
    client = Client()
    upload_batch(client, {"X/Y/folder.txt": "文件夹上传的检索内容 蓄冷罐".encode()})
    d = jbody(_mk(client, "", "D"))["folder_id"]
    upload_batch(client, {"inside.txt": "目录内上传的检索内容 蓄冷罐".encode()}, target=d)
    legacy = jbody(client.post("/api/files", {"file": SimpleUploadedFile("legacy.txt", "旧入口上传的检索内容 蓄冷罐".encode())}, **AUTH))
    deps.lifecycle.process_pending("w", 10)
    inside = find_item(browse(client, d), "inside.txt")
    assert _revise(client, inside["doc_id"], "inside.txt", "更新后的新内容 蓄冷罐 独有标记").status_code == 202
    deps.lifecycle.process_pending("w", 10)
    for q in ("文件夹上传的检索内容 蓄冷罐", "旧入口上传的检索内容 蓄冷罐", "更新后的新内容 蓄冷罐 独有标记"):
        res = search(deps, q)
        assert res.degraded is False and res.hits, q
    folder_hit = [h for h in search(deps, "文件夹上传的检索内容 蓄冷罐").hits if h.doc_name == "folder.txt"]
    assert folder_hit and folder_hit[0].doc_path == "X/Y/folder.txt"
    assert [h for h in search(deps, "旧入口上传的检索内容 蓄冷罐").hits if h.doc_id == legacy["doc_id"] and h.doc_path == "legacy.txt"]
    for item in browse(client, d)["items"] + [find_item(browse(client), "legacy.txt")]:
        assert item["status"] == "indexed" and item["chunk_count"] > 0
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(deps.lifecycle._embedder))
    upload_batch(client, {"bad_one.txt": "索引会失败的内容 蓄冷罐 失败标记".encode()}, target=d)
    deps.lifecycle.process_pending("w", 10)
    bad = find_item(browse(client, d), "bad_one.txt")
    assert bad["status"] == "failed" and bad["error_code"]
    assert not [h for h in search(deps, "索引会失败的内容 蓄冷罐 失败标记").hits if h.doc_id == bad["doc_id"]]


# --------------------------------------------------------------------------- #
# US-011：同名冲突
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_012_name_conflict_journey_three_resolutions_case_and_cancel(http_app):
    """[TC-E2E-R25-012] US-011 AC-011-01/02/04/05：D 已有 a.txt 与 A2.txt —— 再传 a.txt：dry-run 列出冲突，选择前原文件内容 / 状态 / 向量不变；关闭对话框（不提交）= 取消，资料库无变化；
    “两者保留”→ `a (2).txt`（再来一次顺延 `a (3).txt`），原文件不变；“跳过”→ 不入库并计入跳过；“覆盖”→ 按更新处理（旧向量移除、重新索引、列表仍只有一个 a.txt）；
    大小写变体 `a2.txt` 同样触发冲突，选“两者保留”→ `a2 (2).txt`，`A2.txt` 不变。"""
    deps, Client = http_app
    client = Client()
    d = jbody(_mk(client, "", "D"))["folder_id"]
    orig = put_file(deps, "a.txt", "原始内容 同名冲突旅程 旧标记", folder_id=d)
    upper = put_file(deps, "A2.txt", "大写原文件内容", folder_id=d)
    before = get_doc(deps, orig.doc_id)
    ent = [{"client_idx": 0, "rel_path": "a.txt", "size": 60}]

    def plan(res=None, dry=False, entries=ent):
        return jreq(client, "POST", "/api/uploads", {"target_folder_id": d, "dry_run": dry, "entries": entries, "resolutions": res or {}})

    dry = plan(dry=True)
    assert dry.status_code == 200 and jbody(dry)["conflicts"][0]["existing_id"] == orig.doc_id
    assert browse(client, d)["total"] == 2, "选择前不出现新文件"
    assert plan().status_code == 409, "未选择就提交 → 409，不创建批次"
    after = get_doc(deps, orig.doc_id)
    assert (after.status, after.chunk_count, after.content_sha256) == (before.status, before.chunk_count, before.content_sha256)
    assert [h for h in search(deps, "原始内容 同名冲突旅程 旧标记").hits if h.doc_id == orig.doc_id], "向量不变"

    def run(res, content, rel="a.txt"):
        p = plan(res, entries=[{"client_idx": 0, "rel_path": rel, "size": 200}])
        assert p.status_code == 201, p.content
        b = jbody(p)
        r = put_multipart(client, f"/api/uploads/{b['batch_id']}/items/0", rel.split("/")[-1], content)
        return b, jbody(r)

    _, r1 = run({"a.txt": "rename"}, "改名保留的新文件内容 一".encode())
    _, r2 = run({"a.txt": "rename"}, "改名保留的新文件内容 二".encode())
    assert (r1["final_rel_path"], r2["final_rel_path"]) == ("a (2).txt", "a (3).txt")
    assert sorted(names_in(browse(client, d))) == ["A2.txt", "a (2).txt", "a (3).txt", "a.txt"]
    assert get_doc(deps, orig.doc_id).content_sha256 == before.content_sha256
    _, rs = run({"a.txt": "skip"}, "跳过的内容".encode())
    assert (rs["state"], rs["reason_code"]) == ("skipped", "USER_SKIPPED") and browse(client, d)["total"] == 4
    pb, ro = run({"a.txt": "overwrite"}, "覆盖后的新内容 同名冲突旅程 新标记".encode())
    assert pb["items"][0]["action"] == "update" and ro["state"] == "accepted"
    deps.lifecycle.process_pending("w", 10)
    assert sorted(names_in(browse(client, d))) == ["A2.txt", "a (2).txt", "a (3).txt", "a.txt"], "列表中仍只有一个 a.txt"
    assert hits_containing(search(deps, "覆盖后的新内容 同名冲突旅程 新标记"), "新标记")
    assert not hits_containing(search(deps, "原始内容 同名冲突旅程 旧标记"), "旧标记"), "旧向量已移除"
    # 大小写变体
    cd = plan(dry=True, entries=[{"client_idx": 0, "rel_path": "a2.txt", "size": 60}])
    assert jbody(cd)["conflicts"][0]["existing_name"] == "A2.txt"
    _, rc = run({"a2.txt": "rename"}, "小写变体的新内容".encode(), rel="a2.txt")
    assert rc["final_rel_path"] == "a2 (2).txt" and get_doc(deps, upper.doc_id).doc_name == "A2.txt"


def test_TC_E2E_R25_013_folder_conflict_merge_journey_and_update_name_collision(http_app):
    """[TC-E2E-R25-013] US-011 AC-011-03 + US-008 AC-008-07：上传文件夹 A，目标已有同名文件夹 A（含 x.txt、other.txt）→ 选“覆盖”合并为一个 A，x.txt 冲突需单独确认并按更新处理，other.txt 不变；
    更新 `规范.txt` 时新文件名 `规范V2.MD` 与同目录 `规范v2.md` 仅大小写不同 → 409 冲突；“覆盖”= 以 `规范v2.md` 为更新目标（`规范.txt` 不变）；“两者保留”→ `规范V2 (2).MD`。"""
    deps, Client = http_app
    client = Client()
    a = jbody(_mk(client, "", "A"))["folder_id"]
    old_x = put_file(deps, "x.txt", "旧 x 文件内容 合并旅程", folder_id=a)
    other = put_file(deps, "other.txt", "other 文件内容 合并旅程", folder_id=a)
    ent = [{"client_idx": 0, "rel_path": "A/x.txt", "size": 100}, {"client_idx": 1, "rel_path": "A/new.txt", "size": 100}]
    r = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": ent, "resolutions": {"A": "overwrite"}})
    assert r.status_code == 409 and [c["rel_path"] for c in jbody(r)["conflicts"]] == ["A/x.txt"], "文件夹已选覆盖，x.txt 仍需单独确认"
    r = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": ent, "resolutions": {"A": "overwrite", "A/x.txt": "overwrite"}})
    assert r.status_code == 201
    bid = jbody(r)["batch_id"]
    assert put_multipart(client, f"/api/uploads/{bid}/items/0", "x.txt", "新 x 文件内容 合并旅程 已更新".encode()).status_code == 200
    assert put_multipart(client, f"/api/uploads/{bid}/items/1", "new.txt", "全新文件内容 合并旅程".encode()).status_code == 200
    deps.lifecycle.process_pending("w", 10)
    root = browse(client)
    assert names_in(root) == ["A"] and find_item(root, "A")["folder_id"] == a, "两个 A 合并为一个"
    assert sorted(names_in(browse(client, a))) == ["new.txt", "other.txt", "x.txt"]
    assert get_doc(deps, other.doc_id).content_sha256 == other.content_sha256 and get_doc(deps, other.doc_id).status == "indexed"
    assert hits_containing(search(deps, "新 x 文件内容 合并旅程 已更新"), "已更新") and not hits_containing(search(deps, "旧 x 文件内容 合并旅程"), "旧 x")
    assert get_doc(deps, old_x.doc_id) is None, "x.txt 按更新处理：旧存活行被替换"
    # US-008 AC-008-07
    d = jbody(_mk(client, "", "D2"))["folder_id"]
    x = put_file(deps, "规范.txt", "规范 X 内容", folder_id=d)
    y = put_file(deps, "规范v2.md", "规范 Y 内容", folder_id=d)
    c = _revise(client, x.doc_id, "规范V2.MD", "更新的新内容")
    assert c.status_code == 409 and jbody(c)["conflicts"][0]["existing"]["id"] == y.doc_id
    assert sorted(names_in(browse(client, d))) == ["规范.txt", "规范v2.md"] and browse(client, d)["total"] == 2
    ok = _revise(client, x.doc_id, "规范V2.MD", "更新的新内容", on_conflict="rename")
    assert ok.status_code == 202 and jbody(ok)["final_name"] == "规范V2 (2).MD"
    deps.lifecycle.process_pending("w", 10)
    assert sorted(names_in(browse(client, d))) == ["规范V2 (2).MD", "规范v2.md"]
    ov = _revise(client, y.doc_id, "规范V2.MD", "覆盖到 Y 的新内容")
    assert ov.status_code == 202
    deps.lifecycle.process_pending("w", 10)
    assert browse(client, d)["total"] == 2 and "规范V2 (2).MD" in names_in(browse(client, d)), "X 不变，条目数不变"


# --------------------------------------------------------------------------- #
# US-013：移动
# --------------------------------------------------------------------------- #


def test_TC_E2E_R25_014_move_journey_keeps_retrieval_and_updates_citation_path(http_app):
    """[TC-E2E-R25-014] US-013（Should，随旅程覆盖）AC-013-01/02/03/04：移动文件与整个文件夹，检索命中数不变，引用路径同步；冲突需选择；移入自身 / 超层级被拒、原结构不变。"""
    deps, Client = http_app
    client = Client()
    a, b, c = (jbody(_mk(client, "", n))["folder_id"] for n in ("A", "B", "C"))
    x = put_file(deps, "x.txt", "移动旅程专属内容 乙二醇", folder_id=a)
    before = {h.doc_id for h in search(deps, "移动旅程专属内容 乙二醇").hits}
    mv = jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "file", "id": x.doc_id}], "target_folder_id": b})
    assert mv.status_code == 200 and names_in(browse(client, a)) == [] and names_in(browse(client, b)) == ["x.txt"]
    res = search(deps, "移动旅程专属内容 乙二醇")
    assert {h.doc_id for h in res.hits} == before and [h.doc_path for h in res.hits if h.doc_id == x.doc_id] == ["B/x.txt"]
    mv2 = jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "folder", "id": b}], "target_folder_id": c})
    assert mv2.status_code == 200
    assert [h.doc_path for h in search(deps, "移动旅程专属内容 乙二醇").hits if h.doc_id == x.doc_id] == ["C/B/x.txt"]
    bad = jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "folder", "id": c}], "target_folder_id": b})
    assert bad.status_code == 400 and jbody(bad)["error"]["code"] == "move_into_self"
    assert names_in(browse(client, c)) == ["B"]


# --------------------------------------------------------------------------- #
# US-015：上限整体拒绝，不产生半成品
# --------------------------------------------------------------------------- #


@pytest.fixture()
def small_limits_app(django_ready, raw):
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    raw["upload_batch_max_total_mb"] = 1
    d = build_deps(raw, force=True)
    build_application(d)
    return d, Client


def test_TC_E2E_R25_015_limits_reject_whole_upload_without_leftovers(small_limits_app):
    """[TC-E2E-R25-015] US-015 AC-015-01/02/04（+AC-015-03 可配置）：1001 个文件 → 400 `limit_files`（limit 1000 / actual 1001）；目标第 8 层再传 3 层嵌套 → 400 `depth_exceeded`，
    同一文件夹从第 7 层上传通过；总大小超过 L → 400 `limit_total_bytes`（limit / actual），恰为 L 通过；任一拒绝后资料库中无任何新目录 / 文件 / 批次。"""
    deps, Client = small_limits_app  # 默认 1000 个文件 / 10 层，仅把总大小上限配置为 1MB（AC-015-03：数值可配置）
    client = Client()
    r = jreq(client, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [{"client_idx": i, "rel_path": f"m/f{i}.txt", "size": 3} for i in range(1001)]})
    assert r.status_code == 400 and jbody(r)["error"]["code"] == "limit_files" and jbody(r)["error"]["details"] == {"limit": 1000, "actual": 1001}
    assert browse(client)["total"] == 0
    parent, chain = "", []
    for i in range(1, 9):
        parent = jbody(_mk(client, parent, f"L{i}"))["folder_id"]
        chain.append(parent)
    nested = [{"client_idx": 0, "rel_path": "A/B/C/f.txt", "size": 5}]
    r = jreq(client, "POST", "/api/uploads", {"target_folder_id": chain[7], "dry_run": False, "entries": nested})
    assert r.status_code == 400 and jbody(r)["error"]["code"] == "depth_exceeded" and jbody(r)["error"]["details"]["actual"] == 11
    assert browse(client, chain[7])["total"] == 0, "整体拒绝：第 8 层目录下没有产生半成品"
    ok = jreq(client, "POST", "/api/uploads", {"target_folder_id": chain[6], "dry_run": False, "entries": nested})
    assert ok.status_code == 201
    # AC-015-04：L=1MB（通过配置）
    sclient = client
    limit = 1024 * 1024
    over = jreq(sclient, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [
        {"client_idx": 0, "rel_path": "z/a.txt", "size": limit - 10}, {"client_idx": 1, "rel_path": "z/b.txt", "size": 11}]})
    assert over.status_code == 400 and jbody(over)["error"]["code"] == "limit_total_bytes"
    assert jbody(over)["error"]["details"] == {"limit": limit, "actual": limit + 1}
    assert names_in(browse(sclient)) == ["L1"], "总大小超限整体拒绝：根目录里除前面建的 L1 外没有 z 等任何新目录"
    exact = jreq(sclient, "POST", "/api/uploads", {"target_folder_id": "", "dry_run": False, "entries": [
        {"client_idx": 0, "rel_path": "z/a.txt", "size": limit - 10}, {"client_idx": 1, "rel_path": "z/b.txt", "size": 10}]})
    assert exact.status_code == 201


# --------------------------------------------------------------------------- #
# US-017：既有平铺文件上线后归入根目录
# --------------------------------------------------------------------------- #


def _downgrade_to_legacy(db_path: str) -> None:
    """把已升级的台账还原为“上线前”的 001 形态（去掉 6 个新列与四张新表 / 新索引）。"""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=OFF")
    for stmt in (
        "DROP INDEX IF EXISTS uq_documents_name", "DROP INDEX IF EXISTS uq_documents_revision",
        "DROP INDEX IF EXISTS idx_documents_folder",
        "DROP TABLE IF EXISTS folders", "DROP TABLE IF EXISTS upload_batch_items",
        "DROP TABLE IF EXISTS upload_batches", "DROP TABLE IF EXISTS doc_purge_queue",
    ):
        con.execute(stmt)
    for col in ("folder_id", "name_key", "uploaded_at", "content_updated_at", "indexed_at", "revision_of"):
        con.execute(f"ALTER TABLE documents DROP COLUMN {col}")
    con.commit()
    cols = {r[1] for r in con.execute("PRAGMA table_info(documents)")}
    assert "folder_id" not in cols and "revision_of" not in cols, "前置：台账已还原为上线前形态"
    con.close()


def test_TC_E2E_R25_016_legacy_flat_library_upgrade_all_files_in_root_and_still_searchable(django_ready, tmp_path, monkeypatch):
    """[TC-E2E-R25-016] US-017 AC-017-01/02：上线前项目有 N=5 个平铺文件（M=3 个已索引、1 个失败、1 个待处理，含仅大小写不同的历史重名）→ 台账还原为老库形态后按生产路径
    （`ensure_schema`，即 ib-web 的 ExecStartPre）升级 → 根目录列出全部 5 个文件，3 个仍为“已索引”，名称 / 大小 / 上传时间与上线前一致；任一已索引文件的独有内容仍可被检索；
    把其中一个文件移动到新建文件夹后仍可命中，且删除 / 更新 / 重命名行为与新上传文件一致；升级再重复一次（再次重启）结果不变。"""
    from django.test import Client
    from ibweb.composition import build_application

    deps = sqlite_deps(tmp_path, offline_raw(), monkeypatch)  # 真实 SQLite 台账（临时目录）
    build_application(deps)
    client = Client()
    token = jbody(login(client, "admin", R13_ADMIN_PASSWORD))["token"]
    assert change_password(client, token, R13_ADMIN_PASSWORD, "R25-E2E-Admin-2!").status_code == 200
    H = {**bearer(token), "HTTP_X_IB_PROJECT": PID}  # 真实账户体系令牌（全局管理员，显式声明项目）
    ledger_path = deps.cfg.ledger_path
    ids = {}
    for name, text in (("手册.txt", "旧库手册独有内容 锅炉房"), ("Report.txt", "旧库大写报告独有内容 锅炉房"), ("report.txt", "旧库小写报告独有内容 锅炉房")):
        ids[name] = put_file(deps, name if name != "report.txt" else "tmp_report.txt", text).doc_id
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(deps.lifecycle._embedder))
    ids["坏.txt"] = put_file(deps, "坏.txt", "上线前就失败的文件").doc_id
    monkeypatch.undo()
    ids["待.md"] = put_file(deps, "待.md", "# 上线前待处理", process=False).doc_id
    # 历史重名：把 tmp_report.txt 改成与 Report.txt 仅大小写不同的名字（老库无同名约束，直接 SQL）
    con = sqlite3.connect(ledger_path)
    con.execute("UPDATE documents SET doc_name='report.txt' WHERE doc_id=?", (ids["report.txt"],))
    con.commit()
    con.close()
    before = {
        r.doc_id: (r.doc_name, r.size_bytes, r.created_at, r.status)
        for r in deps.ledger.list_documents(S, page=1, page_size=100, status=None)[0]
    }
    assert len(before) == 5 and sum(1 for v in before.values() if v[3] == "indexed") == 3
    _downgrade_to_legacy(ledger_path)
    from ib.ledger import schema

    for _ in range(2):  # 升级并重复一次“重启”：幂等
        c = sqlite3.connect(ledger_path)
        schema.ensure_schema(c)
        c.close()
    root = browse(client, '', H)
    assert root["total"] == 5 and sorted(names_in(root, "file")) == sorted(v[0] for v in before.values()) and names_in(root, "folder") == []
    by_id = {i["doc_id"]: i for i in root["items"]}
    for doc_id, (name, size, created, status) in before.items():
        item = by_id[doc_id]
        assert (item["name"], item["size_bytes"], item["uploaded_at"], item["status"]) == (name, size, created, status)
    assert sum(1 for i in root["items"] if i["status"] == "indexed") == 3
    res = search(deps, "旧库手册独有内容 锅炉房")
    assert res.degraded is False and [h for h in res.hits if h.doc_id == ids["手册.txt"] and h.doc_path == "手册.txt"]
    # AC-017-02：移动后仍可命中；删除 / 更新 / 重命名与新文件一致
    f = jbody(_mk(client, "", "整理后", H))["folder_id"]
    assert jreq(client, "POST", "/api/library/move", {"entries": [{"kind": "file", "id": ids["手册.txt"]}], "target_folder_id": f}, H).status_code == 200
    moved = [h for h in search(deps, "旧库手册独有内容 锅炉房").hits if h.doc_id == ids["手册.txt"]]
    assert moved and moved[0].doc_path == "整理后/手册.txt"
    assert jreq(client, "PATCH", f"/api/files/{ids['手册.txt']}", {"name": "手册改.txt"}, H).status_code == 200
    assert client.post(f"/api/files/{ids['手册.txt']}/revision", {"file": SimpleUploadedFile("手册改.txt", "旧库手册更新后的新内容 锅炉房 新标记".encode())}, **H).status_code == 202
    deps.lifecycle.process_pending("w", 10)
    assert hits_containing(search(deps, "旧库手册更新后的新内容 锅炉房 新标记"), "新标记")
    assert not hits_containing(search(deps, "旧库手册独有内容 锅炉房"), "手册独有内容")
    new_id = find_item(browse(client, f, H), "手册改.txt")["doc_id"]
    assert client.delete(f"/api/files/{new_id}", **H).status_code == 200
    assert not hits_containing(search(deps, "旧库手册更新后的新内容 锅炉房 新标记"), "新标记")
    # 历史重名行显示名不变，且仍可被重命名 / 删除
    assert sorted(names_in(browse(client, '', H), "file")).count("Report.txt") == 1 and "report.txt" in names_in(browse(client, '', H), "file")
