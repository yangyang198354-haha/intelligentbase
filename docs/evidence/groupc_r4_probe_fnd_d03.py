"""GROUP_C R4 自验探针 —— FND-GROUP-D-03（原文件字节在删除路径成孤儿）修复后的正向判据。

只读 `src/**`；不写仓库任何实现路径（临时目录用 tempfile）。不触网、不连生产库 / Qdrant /
DeepSeek / HuggingFace。走**与 HTTP 视图同源**的 scope 派生（`composition.resolve_scope`
→ 项目级 `Scope(project_id=...)`，`kb_ids=None`）。

判据（修复后的真值）：
  1. 走真实 Django HTTP DELETE：`blob_deleted is True`，且该 doc 在 BlobStore 内**无残留**；
  2. 对照组（kb 级 scope 直接调用）同样删净 —— 证明修复对两种 scope 都成立；
  3. 「本无 blob」（`data=None` 的 D-08 路径）→ `blob_deleted is False`（**不虚报 True**）；
  4. 用**真实文件系统** FsBlobStore 复跑：删除后磁盘上该 doc 目录**不存在**（无孤儿文件），
     且空的 kb 目录被清理；`blob_deleted is True`；
  5. 跨项目隔离：删 p_alpha 的 doc **不影响** p_beta 的 blob；
  6. 不回归 FND-GROUP-D-02：项目级 scope 删除「尚无事发生」的文档仍成功（不抛 StartupError），
     `vectors_deleted == 0`、台账行为 None、`process_pending` 不再认领。

运行：`PYTHONUTF8=1 python docs/evidence/groupc_r4_probe_fnd_d03.py`（cwd = 仓库根）
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (str(_ROOT / "src"), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "groupc-r4-offline-token")
os.environ.setdefault("IB_LOG_LEVEL", "ERROR")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

from conftest import offline_raw  # noqa: E402

from ib.blob import FsBlobStore, kb_segment  # noqa: E402
from ib.context import make_request_context  # noqa: E402
from ib.core import Scope  # noqa: E402
from ib.lifecycle import blob_ref_for  # noqa: E402
from ibweb.composition import build_application, build_deps, resolve_scope  # noqa: E402

TOKEN = os.environ["IB_OFFLINE_TOKEN"]
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def _mem_keys(store) -> list:
    objs = getattr(store, "_objects", None)
    return list(objs.keys()) if objs is not None else []


def main() -> int:
    import django

    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import Client

    deps = build_deps(offline_raw(), force=True)
    django.setup()
    build_application(deps)

    print("=== GROUP_C R4 / FND-GROUP-D-03 探针（真实 HTTP 路径 + 文件系统路径）===")
    client = Client()

    # ---------------- 组 1：真实 HTTP DELETE（项目级 scope）----------------
    print("\n--- 组 1：HTTP DELETE /api/files/{id}（resolve_scope → 项目级）---")
    up = SimpleUploadedFile("r4_http.txt", "R4 HTTP 原文件清理样本。".encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    check("上传返回 201", r.status_code == 201, str(r.status_code))
    doc = json.loads(r.content)
    doc_id = doc["doc_id"]

    before = _mem_keys(deps.blobs)
    check("上传确实落盘了原文件", len(before) >= 1, str(len(before)))
    print(f"  上传后 BlobStore 对象 = {[k[:3] for k in before]}")

    ctx = make_request_context(
        project_id="p_alpha", actor_id="tester", session_id="s1", roles=("manager",)
    )
    view_scope = resolve_scope(ctx)
    check(
        "视图 scope 的 kb_ids 确为 None（项目级，即缺陷触发条件）",
        view_scope.kb_ids is None,
        str(view_scope.kb_ids),
    )

    d = client.delete(f"/api/files/{doc_id}", **AUTH)
    body = json.loads(d.content) if d.status_code == 200 else {}
    print(f"  HTTP DELETE 状态 = {d.status_code}；DeleteReport = {body}")
    check("删除返回 200", d.status_code == 200, str(d.status_code))
    check("ledger_deleted is True", body.get("ledger_deleted") is True, str(body.get("ledger_deleted")))
    check(
        "【修复】blob_deleted is True（确删到原文件）",
        body.get("blob_deleted") is True,
        repr(body.get("blob_deleted")),
    )

    after = _mem_keys(deps.blobs)
    orphaned = [k for k in after if k[2] == doc_id]
    print(f"  删除后对象数 = {len(after)}；本 doc 残留 = {len(orphaned)}")
    check("【修复】原文件无孤儿（BlobStore 内无本 doc 残留）", len(orphaned) == 0, f"残留 {len(orphaned)}")
    check("台账行已删", deps.ledger.get_document(Scope("p_alpha"), doc_id) is None)

    # ---------------- 组 2：kb 级 scope 对照组（回归不变） ----------------
    print("\n--- 组 2：对照组 —— 同一数据用 kb 级 scope 直接删除 ---")
    deps2 = build_deps(offline_raw(), force=True)
    build_application(deps2)
    rec2 = deps2.lifecycle.submit_upload(
        make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)),
        deps2.lifecycle.validate_upload("r4_kb.txt", 8, b"r4-kb-ab"),
        "kb_a",
        data=io.BytesIO(b"r4-kb-ab"),
    )
    rep2 = deps2.lifecycle.delete_document(Scope("p_alpha", ("kb_a",)), rec2.doc_id)
    print(f"  kb 级 delete_document = {rep2}")
    check("kb 级 scope 仍能删净（blob_deleted True）", rep2.blob_deleted is True, str(rep2))
    check("kb 级删除后对象数为 0", len(_mem_keys(deps2.blobs)) == 0, str(len(_mem_keys(deps2.blobs))))

    # ---------------- 组 3：本无 blob（data=None / D-08 路径）→ False ----------------
    print("\n--- 组 3：本无 blob（data=None）→ blob_deleted 必须为 False（不虚报） ---")
    rec3 = deps2.lifecycle.submit_upload(
        make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)),
        deps2.lifecycle.validate_upload("r4_noblob.txt", 5, b"r4-no"),
        "kb_a",
        data=None,
    )
    check("无内容 → blob_ref_for 为 None", blob_ref_for(rec3) is None)
    rep3 = deps2.lifecycle.delete_document(resolve_scope(
        make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",))
    ), rec3.doc_id)
    print(f"  data=None delete_document = {rep3}")
    check("【正确置位】本无 blob → blob_deleted is False", rep3.blob_deleted is False, str(rep3.blob_deleted))
    check("本无 blob 删除仍成功（ledger_deleted True）", rep3.ledger_deleted is True)

    # ---------------- 组 4：真实文件系统 FsBlobStore ----------------
    print("\n--- 组 4：真实文件系统 FsBlobStore（磁盘无孤儿文件 + 空 kb 目录清理） ---")
    tmp_root = tempfile.mkdtemp(prefix="ib-r4-blobs-")
    try:
        fs = FsBlobStore(tmp_root)
        deps3 = build_deps(offline_raw(), force=True)
        build_application(deps3)
        deps3.blobs = fs
        deps3.lifecycle._blobs = fs
        rec4 = deps3.lifecycle.submit_upload(
            make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)),
            deps3.lifecycle.validate_upload("r4_fs.txt", 10, b"r4-fs-abcde"),
            "kb_a",
            data=io.BytesIO(b"r4-fs-abcde"),
        )
        ref = blob_ref_for(rec4)
        on_disk = pathlib.Path(tmp_root, *ref.rel_path.split("/"))
        print(f"  期望落盘文件 = {on_disk}（存在={on_disk.is_file()}）")
        check("落盘文件存在（写路径 kb 段）", on_disk.is_file())
        check("落盘 kb 段与 kb_segment 一致", on_disk.parts[-3] == kb_segment("kb_a"), str(on_disk.parts[-3]))

        rep4 = deps3.lifecycle.delete_document(
            resolve_scope(
                make_request_context(
                    project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)
                )
            ),
            rec4.doc_id,
        )
        print(f"  项目级 scope delete_document = {rep4}")
        check("【修复】磁盘上原文件已移除（无孤儿文件）", not on_disk.exists())
        check("【修复】doc 目录已清理", not on_disk.parent.exists())
        check("空 kb 目录已清理", not on_disk.parent.parent.exists(), str(on_disk.parent.parent))
        check("【修复】FsBlobStore 路径 blob_deleted is True", rep4.blob_deleted is True, str(rep4))

        # ---------------- 组 5：跨项目隔离 ----------------
        print("\n--- 组 5：跨项目隔离 —— 删 p_alpha 不伤 p_beta ---")
        rec_a = deps3.lifecycle.submit_upload(
            make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)),
            deps3.lifecycle.validate_upload("iso_a.txt", 6, b"iso-aa"),
            "kb_a",
            data=io.BytesIO(b"iso-aa"),
        )
        rec_b = deps3.lifecycle.submit_upload(
            make_request_context(project_id="p_beta", actor_id="t", session_id="s", roles=("manager",)),
            deps3.lifecycle.validate_upload("iso_b.txt", 6, b"iso-bb"),
            "kb_b",
            data=io.BytesIO(b"iso-bb"),
        )
        ref_b = blob_ref_for(rec_b)
        b_on_disk = pathlib.Path(tmp_root, *ref_b.rel_path.split("/"))
        check("p_beta 的 blob 已落盘（前置条件）", b_on_disk.is_file())
        deps3.lifecycle.delete_document(
            resolve_scope(
                make_request_context(
                    project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)
                )
            ),
            rec_a.doc_id,
        )
        check("【隔离】删除 p_alpha 的 doc 后 p_beta 的 blob 仍在", b_on_disk.is_file())
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    # ---------------- 组 6：不回归 FND-GROUP-D-02 ----------------
    print("\n--- 组 6：不回归 FND-GROUP-D-02（尚无事发生 → 删除成功，不留幽灵） ---")
    deps4 = build_deps(offline_raw(), force=True)
    build_application(deps4)  # 启动期只 ensure_collection，不 bind
    rec5 = deps4.lifecycle.submit_upload(
        make_request_context(project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)),
        deps4.lifecycle.validate_upload("r4_ghost.txt", 8, b"fileapp2"),
        "kb_a",
        data=io.BytesIO(b"fileapp2"),
    )
    try:
        rep5 = deps4.lifecycle.delete_document(
            resolve_scope(
                make_request_context(
                    project_id="p_alpha", actor_id="t", session_id="s", roles=("manager",)
                )
            ),
            rec5.doc_id,
        )
        check("删除未抛（无 StartupError）", True)
    except Exception as exc:  # noqa: BLE001
        rep5 = None
        check("删除未抛（无 StartupError）", False, f"{type(exc).__name__}: {exc}")
    if rep5 is not None:
        print(f"  delete_document = {rep5}")
        check("vectors_deleted == 0（本项目尚无派生物）", rep5.vectors_deleted == 0, str(rep5.vectors_deleted))
        check("台账行为 None", deps4.ledger.get_document(Scope("p_alpha"), rec5.doc_id) is None)
        proc = deps4.lifecycle.process_pending("r4-w", 10)
        check("process_pending 不再认领已删文档", proc.processed == 0 and proc.succeeded == 0, str(proc))
        check("原文件亦无孤儿", len(_mem_keys(deps4.blobs)) == 0, str(len(_mem_keys(deps4.blobs))))

    print("\n=== 判定 ===")
    if failures:
        print(f"结论: {len(failures)} 项未达判据: {failures}")
        return 1
    print("结论: 全部判据通过（FND-GROUP-D-03 修复成立，且未回归 FND-GROUP-D-02）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
