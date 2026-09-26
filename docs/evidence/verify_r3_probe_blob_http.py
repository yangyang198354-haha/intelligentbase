"""独立复核（verifier）—— C8 / FND-GROUP-D-03 独立探针（**走真实 HTTP 路径**）。

目的：排除「探针构造误差」（例如探针自己用了错误的 scope）。
本探针**不手工造 scope**，而是走 Django test Client 的 `DELETE /api/files/{id}`，
即 `ibweb/views.py::file_detail_endpoint` → `composition.resolve_scope(ctx)` 的
生产同源路径。另设对照组：同一份数据用 **kb 级 scope** 直接调 `delete_document`，
若 kb 级能删掉而 HTTP 级删不掉，则证明根因是 scope 维度不一致，而非 BlobStore 缺陷。

只读 src/**，不写任何实现。
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (str(_ROOT / "src"), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "verify-r3-offline-token")
os.environ.setdefault("IB_LOG_LEVEL", "ERROR")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

from conftest import offline_raw  # noqa: E402

from ib.core import Scope  # noqa: E402
from ibweb.composition import build_application, build_deps, resolve_scope  # noqa: E402

TOKEN = os.environ["IB_OFFLINE_TOKEN"]
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def _blob_keys(store):
    objs = getattr(store, "_objects", None)
    return list(objs.keys()) if objs is not None else []


def main() -> int:
    import django

    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import Client

    deps = build_deps(offline_raw(), force=True)
    django.setup()
    build_application(deps)

    print("=== C8 / FND-GROUP-D-03 独立探针（真实 HTTP 路径） ===")
    client = Client()

    # ---------------- 组 1：真实 HTTP DELETE ----------------
    print("\n--- 组 1：HTTP DELETE /api/files/{id}（生产同源路径）---")
    up = SimpleUploadedFile("vp_http_blob.txt", "VERIFY-R3 HTTP blob 对照样本。".encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    print(f"  上传 HTTP 状态 = {r.status_code}")
    check("上传返回 201", r.status_code == 201, str(r.status_code))
    doc = json.loads(r.content)
    doc_id = doc["doc_id"]

    keys_before = _blob_keys(deps.blobs)
    print(f"  上传后 BlobStore 对象数 = {len(keys_before)}")
    for k in keys_before:
        print(f"    key(project, kb, doc, sha256[], ext) = {k[:3]}")
    check("上传确实落盘了原文件", len(keys_before) >= 1, str(len(keys_before)))

    # 复刻视图的 scope 派生，显式打印以证明「不是探针自己造错 scope」
    from ib.context import make_request_context

    ctx = make_request_context(
        project_id="p_alpha", actor_id="tester", session_id="s1", roles=("manager",)
    )
    view_scope = resolve_scope(ctx)
    print(f"  resolve_scope(ctx)（视图实际用）= {view_scope}  [kb_ids={view_scope.kb_ids}]")
    check("视图 scope 的 kb_ids 确为 None（项目级）", view_scope.kb_ids is None, str(view_scope.kb_ids))

    d = client.delete(f"/api/files/{doc_id}", **AUTH)
    print(f"  HTTP DELETE 状态 = {d.status_code}")
    body = json.loads(d.content) if d.status_code == 200 else {}
    print(f"  DeleteReport = {body}")
    check("删除返回 200", d.status_code == 200, str(d.status_code))
    check("ledger_deleted is True", body.get("ledger_deleted") is True, str(body.get("ledger_deleted")))

    keys_after = _blob_keys(deps.blobs)
    orphaned = [k for k in keys_after if k[2] == doc_id]
    print(f"  删除后 BlobStore 对象数 = {len(keys_after)}；本 doc 残留 = {len(orphaned)}")
    print(f"  blob_deleted 字段 = {body.get('blob_deleted')!r}")
    check("【缺陷】blob_deleted 恒为 False", body.get("blob_deleted") is False, repr(body.get("blob_deleted")))
    check("【缺陷】原文件成为孤儿（仍在 BlobStore 内）", len(orphaned) >= 1, f"残留 {len(orphaned)} 个")
    check("【对照】台账行已删（删除本身生效）", deps.ledger.get_document(Scope("p_alpha"), doc_id) is None)

    # ---------------- 组 2：kb 级 scope 对照 ----------------
    print("\n--- 组 2：对照组 —— 同一数据用 kb 级 scope 删除 ---")
    deps2 = build_deps(offline_raw(), force=True)
    build_application(deps2)
    client2 = Client()
    up2 = SimpleUploadedFile("vp_kb_blob.txt", "VERIFY-R3 kb 级对照样本。".encode("utf-8"))
    r2 = client2.post("/api/files", {"kb_id": "kb_a", "file": up2}, **AUTH)
    doc2 = json.loads(r2.content)["doc_id"]
    before2 = _blob_keys(deps2.blobs)
    print(f"  上传后对象数 = {len(before2)}")
    rep2 = deps2.lifecycle.delete_document(Scope("p_alpha", ("kb_a",)), doc2)
    after2 = _blob_keys(deps2.blobs)
    print(f"  kb 级 delete_document report = {rep2}")
    print(f"  删除后对象数 = {len(after2)}")
    check("【对照】kb 级 scope 能删掉原文件（blob_deleted True）", rep2.blob_deleted is True, str(rep2))
    check("【对照】kb 级删除后无孤儿", len(after2) == 0, str(len(after2)))

    # ---------------- 结论 ----------------
    print()
    print("=== 判定 ===")
    scope_mismatch = (body.get("blob_deleted") is False) and (rep2.blob_deleted is True)
    check("根因确为 scope 维度不一致（项目级 vs kb 级）", scope_mismatch)
    if scope_mismatch:
        print("  → 非探针构造误差：同一 BlobStore，kb 级可删、HTTP 项目级删不掉。")
        print("  → 上传按 kb 落盘（lifecycle 构造 Scope(kb_ids=(record.kb_id,))），")
        print("     HTTP 删除用 resolve_scope → Scope(project_id)（kb_ids=None）→ BlobStore 回退 'default' → 删到 0 个。")

    print()
    if failures:
        print(f"结论: 缺陷在场（{len(failures)} 项确认）: {failures}")
        return 1
    print("结论: 未复现缺陷")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
