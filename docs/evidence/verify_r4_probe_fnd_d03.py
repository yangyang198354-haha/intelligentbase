"""独立核验探针（verifier 自建，**不复用** developer / 既有 verifier 的任何探针）。

FND-GROUP-D-03 对抗性证伪：删除文档后原文件字节是否仍成孤儿、`blob_deleted` 是否如实。

与既有探针的差别（刻意另起炉灶）：
  * 数据面用**真实 FsBlobStore**（根目录在临时目录），断言 `is_file` / `rglob` / 目录存在性，
    而不是只看返回值或内存替身；
  * 走**真实 Django HTTP**（`django.test.Client` → `ibweb.views` → `resolve_scope` 项目级 scope）；
  * 残留判定口径统一为「**遍历整个 blob 根**，文件数为 0」——不针对单一预期路径断言，
    这样「删到了别的段、真正落盘的那段还在」也会被抓到。

覆盖：
  P1 (a) kb 级上传 → 项目级删除（HTTP 真实路径）      —— 缺陷原始触发条件
  P2 (a-对照) kb 级上传 → kb 级删除（直连 lifecycle）  —— 排除探针构造误差
  P3 (b) 项目级上传 → 项目级删除（kb_id="" 直连）      —— 合成构造（见下方诚实标注）
  P4 (c) kb 级上传 → kb 级删除（第二条 kb）            —— 组合完整性
  P5 记录同源性实证：`record.kb_id` 与 `put` 落盘段的实际目录名一致
  P6 越权哨兵：用**另一个 kb** 的 scope 删除 → 404 且磁盘无变化（不得借记录派生越权删）

**诚实标注（P3）**：项目级上传（`kb_id=""`）**不是** HTTP 可达路径 ——
`UploadInputSerializer.kb_id` 为 `allow_blank=False`，且 `submit_upload` 会
`assert_kb_in_project(project, kb_id)`。因此 P3 通过直接调 lifecycle 构造
（并先 `upsert_kb("")` 造出空 kb 行），只为覆盖「上传 scope 与删除 scope 都是项目级」这一**组合**，
不代表生产存在该入口。P1/P2/P4 才是真实可达路径。

用法：`PYTHONUTF8=1 IB_OFFLINE_MODE=1 python docs/evidence/verify_r4_probe_fnd_d03.py`
退出码 0 = 全部 PASS；1 = 有 FAIL。全程离线（SQLite/内存/临时目录），不连任何外部服务。
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
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "verify-r4-offline-token")
os.environ.setdefault("IB_LOG_LEVEL", "ERROR")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

RAW: dict = {
    "config_source": "dict",
    "offline_mode": True,
    "ledger_backend": "memory",
    "blob": {"enabled": True, "root": ""},
    "retrieval": {"top_k": 3, "score_threshold": 0.0, "candidate_multiplier": 2},
    "vectorstore": {"backend": "memory"},
    "embedding": {"backend": "fake"},
    "llm": {"backend": "fake"},
    "projects": {
        "p_alpha": {
            "name": "探针项目 A",
            "active_collection_version": "1",
            "embedding_model_id": "bge-m3",
            "dim": 1024,
            "kb_ids": ["kb_a", "kb_b"],
        },
    },
}

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" :: {detail}" if detail else ""))


def all_files(root: str) -> list[str]:
    """blob 根下**全部**文件的相对路径（口径统一：不预设段名）。"""
    base = pathlib.Path(root)
    if not base.exists():
        return []
    return sorted(str(p.relative_to(base)).replace("\\", "/") for p in base.rglob("*") if p.is_file())


def dirs_under(root: str) -> list[str]:
    base = pathlib.Path(root)
    if not base.exists():
        return []
    return sorted(str(p.relative_to(base)).replace("\\", "/") for p in base.rglob("*") if p.is_dir())


def build_fs_app(blob_root: str):
    """fresh 装配 + Django setup + 把 BlobStore 换成真实 FsBlobStore（根在 blob_root）。"""
    from ib.blob import FsBlobStore
    from ibweb.composition import build_application, build_deps

    raw = json.loads(json.dumps(RAW))
    raw["blob"]["root"] = blob_root
    deps = build_deps(raw, force=True)
    import django

    django.setup()
    build_application(deps)

    fs = FsBlobStore(blob_root)
    deps.blobs = fs
    deps.lifecycle._blobs = fs
    return deps, fs


def upload_http(client, auth: dict, kb_id: str, filename: str, payload: bytes) -> str:
    from django.core.files.uploadedfile import SimpleUploadedFile

    up = SimpleUploadedFile(filename, payload, content_type="text/plain")
    r = client.post("/api/files", {"kb_id": kb_id, "file": up}, **auth)
    assert r.status_code == 201, f"上传失败 {r.status_code}: {r.content!r}"
    return json.loads(r.content)["doc_id"]


def main() -> int:
    from ib.core import KbRecord, Scope
    from ib.lifecycle import blob_ref_for
    from ibweb.composition import resolve_scope

    tmp = tempfile.mkdtemp(prefix="verify-r4-")
    try:
        root = os.path.join(tmp, "blobs")
        deps, fs = build_fs_app(root)
        from django.test import Client

        auth = {"HTTP_AUTHORIZATION": f"Bearer {os.environ['IB_OFFLINE_TOKEN']}"}
        client = Client()

        def ctx(project_id: str = "p_alpha"):
            from ib.context import make_request_context

            return make_request_context(
                project_id=project_id, actor_id="verifier", session_id="s1", roles=("manager",)
            )

        # ---------- P5：记录同源性实证 ---------- #
        body_a = "P1/P5 样本：kb 级上传后删除必须清掉真实字节。".encode("utf-8")
        doc_a = upload_http(client, auth, "kb_a", "p5_kb_a.txt", body_a)
        rec_a = deps.ledger.get_document(Scope("p_alpha"), doc_a)
        ref_a = blob_ref_for(rec_a)
        on_disk_a = pathlib.Path(root, *ref_a.rel_path.split("/"))
        seg_from_ref = ref_a.rel_path.split("/")[1]
        seg_from_disk = on_disk_a.parent.parent.name
        check(
            "P5 record.kb_id 与 put 落盘段同源（实证）",
            rec_a.kb_id == "kb_a" and seg_from_ref == seg_from_disk == "kb_a" and on_disk_a.is_file(),
            f"record.kb_id={rec_a.kb_id!r} ref段={seg_from_ref!r} 磁盘段={seg_from_disk!r}",
        )

        # ---------- P1：kb 级上传 → 项目级删除（真实 HTTP） ---------- #
        view_scope = resolve_scope(ctx())
        check(
            "P1 前置：HTTP 视图 scope 为项目级（kb_ids=None，缺陷触发条件）",
            view_scope.kb_ids is None and view_scope.project_id == "p_alpha",
            f"view_scope={view_scope}",
        )
        before = all_files(root)
        d = client.delete(f"/api/files/{doc_a}", **auth)
        rep = json.loads(d.content) if d.status_code == 200 else {}
        residue = all_files(root)
        check(
            "P1 HTTP 删除返回 200 且 blob_deleted 为 True",
            d.status_code == 200 and rep.get("blob_deleted") is True,
            f"status={d.status_code} body={rep}",
        )
        check(
            "P1 删除后真实根目录 0 残留字节（rglob 全根）",
            residue == [],
            f"删除前={before} 删除后={residue}",
        )
        check(
            "P1 本用例自身字节已消失（单例归因，不与其他用例级联）",
            not on_disk_a.exists(),
            f"own_file={on_disk_a} exists={on_disk_a.exists()}",
        )
        check(
            "P1 doc 目录与空 kb 目录均已消失",
            not (pathlib.Path(root) / "p_alpha" / "kb_a" / doc_a).exists()
            and not (pathlib.Path(root) / "p_alpha" / "kb_a").exists(),
            f"剩余目录={dirs_under(root)}",
        )
        check(
            "P1 台账行已删除",
            deps.ledger.get_document(Scope("p_alpha"), doc_a) is None,
        )

        # ---------- P2：kb 级上传 → kb 级删除（对照组，排除探针构造误差） ---------- #
        body_c = "P2 对照：kb 级删除同一样本应同样清空。".encode("utf-8")
        rec_c = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p2_ctrl.txt", len(body_c), body_c[:4096]),
            "kb_a",
            data=io.BytesIO(body_c),
        )
        ref_c = blob_ref_for(rec_c)
        on_disk_c = pathlib.Path(root, *ref_c.rel_path.split("/"))
        assert on_disk_c.is_file()
        rep_c = deps.lifecycle.delete_document(Scope("p_alpha", ("kb_a",)), rec_c.doc_id)
        check(
            "P2 对照组 kb 级删除：本用例自身字节已消失",
            not on_disk_c.exists(),
            f"own_file={on_disk_c} exists={on_disk_c.exists()}",
        )
        check(
            "P2 对照组 kb 级删除：blob_deleted=True 且全根 0 残留",
            rep_c.blob_deleted is True and all_files(root) == [],
            f"report={rep_c} 残留={all_files(root)}",
        )

        # ---------- P4：kb 级上传（第二条 kb）→ kb 级删除 ---------- #
        body_d = "P4 组合：第二条 kb 上传 + kb 级删除。".encode("utf-8")
        rec_d = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p4_kb_b.txt", len(body_d), body_d[:4096]),
            "kb_b",
            data=io.BytesIO(body_d),
        )
        ref_d = blob_ref_for(rec_d)
        check(
            "P4 前置：落盘段为 kb_b",
            pathlib.Path(root, *ref_d.rel_path.split("/")).is_file()
            and ref_d.rel_path.split("/")[1] == "kb_b",
            f"rel_path={ref_d.rel_path}",
        )
        own_d = pathlib.Path(root, *ref_d.rel_path.split("/"))
        rep_d = deps.lifecycle.delete_document(Scope("p_alpha", ("kb_b",)), rec_d.doc_id)
        check(
            "P4 (c) 组合：本用例自身字节已消失",
            not own_d.exists(),
            f"own_file={own_d} exists={own_d.exists()}",
        )
        check(
            "P4 (c) 组合 kb 级上传→kb 级删除：blob_deleted=True 且全根 0 残留",
            rep_d.blob_deleted is True and all_files(root) == [],
            f"report={rep_d} 残留={all_files(root)}",
        )

        # ---------- P3：项目级上传 → 项目级删除（合成构造，见文件头诚实标注） ---------- #
        deps.ledger.upsert_kb(KbRecord(kb_id="", project_id="p_alpha", name="(空 kb)", created_at=""))
        body_b = "P3 合成：项目级上传 + 项目级删除。".encode("utf-8")
        rec_b = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p3_proj.txt", len(body_b), body_b[:4096]),
            "",
            data=io.BytesIO(body_b),
        )
        ref_b = blob_ref_for(rec_b)
        check(
            "P3 (b) 项目级上传落盘段为 default 且 record.kb_id 为空",
            rec_b.kb_id == "" and ref_b.rel_path.split("/")[1] == "default",
            f"record.kb_id={rec_b.kb_id!r} rel_path={ref_b.rel_path}",
        )
        own_b = pathlib.Path(root, *ref_b.rel_path.split("/"))
        rep_b = deps.lifecycle.delete_document(resolve_scope(ctx()), rec_b.doc_id)
        check(
            "P3 (b) 组合：本用例自身字节已消失",
            not own_b.exists(),
            f"own_file={own_b} exists={own_b.exists()}",
        )
        check(
            "P3 (b) 组合 项目级上传→项目级删除：blob_deleted=True 且全根 0 残留",
            rep_b.blob_deleted is True and all_files(root) == [],
            f"report={rep_b} 残留={all_files(root)}",
        )

        # ---------- P7：无 blob（D-08 data=None）→ 不得虚报 True ---------- #
        rec_f = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p7_noblob.txt", 5, b"nob01"),
            "kb_a",
            data=None,
        )
        rep_f = deps.lifecycle.delete_document(resolve_scope(ctx()), rec_f.doc_id)
        check(
            "P7 无原文件（data=None）删除如实报 blob_deleted=False（不得恒 True 掩盖）",
            rep_f.blob_deleted is False and blob_ref_for(rec_f) is None,
            f"report={rep_f} sha256={rec_f.content_sha256!r}",
        )

        # ---------- P6：越权哨兵 —— 用另一个 kb 的 scope 删除 ---------- #
        body_e = "P6 哨兵：错配 kb scope 不得删到任何字节。".encode("utf-8")
        rec_e = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p6_sentinel.txt", len(body_e), body_e[:4096]),
            "kb_a",
            data=io.BytesIO(body_e),
        )
        ref_e = blob_ref_for(rec_e)
        on_disk_e = pathlib.Path(root, *ref_e.rel_path.split("/"))
        assert on_disk_e.is_file()
        from ib.core import NotFoundError

        raised = ""
        try:
            deps.lifecycle.delete_document(Scope("p_alpha", ("kb_b",)), rec_e.doc_id)
        except NotFoundError as exc:
            raised = type(exc).__name__
        except Exception as exc:  # noqa: BLE001
            raised = f"UNEXPECTED:{type(exc).__name__}"
        check(
            "P6 用错配 kb scope 删除 → NotFoundError 且字节保留（不越权删）",
            raised == "NotFoundError" and on_disk_e.is_file(),
            f"raised={raised!r} 字节仍在={on_disk_e.is_file()}",
        )
        # 收尾：清干净 P6 的哨兵文档，确认无遗留（必须在 P8 之前，否则 P8 会把哨兵算成幽灵）
        deps.lifecycle.delete_document(Scope("p_alpha", ("kb_a",)), rec_e.doc_id)
        check("P6 收尾后全根 0 残留", all_files(root) == [], f"残留={all_files(root)}")

        # ---------- P8：不回归 FND-GROUP-D-02（fresh 装配 + 项目级删除 → 无 pending 幽灵） ---------- #
        body_g = "P8 fresh 装配下项目级删除刚上传的文档。".encode("utf-8")
        rec_g = deps.lifecycle.submit_upload(
            ctx(),
            deps.lifecycle.validate_upload("p8_fresh.txt", len(body_g), body_g[:4096]),
            "kb_a",
            data=io.BytesIO(body_g),
        )
        rep_g = deps.lifecycle.delete_document(resolve_scope(ctx()), rec_g.doc_id)
        proc_g = deps.lifecycle.process_pending("verify-r4-worker", 10)
        check(
            "P8 不回归 FND-GROUP-D-02：项目级删除成功(非500路径) 且 worker 不再认领（无 pending 幽灵）",
            rep_g.ledger_deleted is True
            and rep_g.blob_deleted is True
            and proc_g.processed == 0
            and proc_g.succeeded == 0
            and all_files(root) == [],
            f"report={rep_g} process={proc_g} 残留={all_files(root)}",
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok, _ in RESULTS if not ok]
    print("-" * 72)
    print(f"TOTAL={len(RESULTS)} PASS={len(RESULTS) - len(failed)} FAIL={len(failed)}")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
