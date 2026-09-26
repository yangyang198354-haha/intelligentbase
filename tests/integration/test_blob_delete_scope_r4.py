"""集成测试层 9/N —— R4 增量回归：FND-GROUP-D-03（原文件字节在删除路径成孤儿）。

覆盖验收标准：
  * AC-IB-03-02「切分块与向量一并清理，不留下孤儿数据」；
  * AC-IB-03-03「已删不可检索」。

**被测修复**（`INV-GROUP_C-INTELBASE-004`）：
  * `src/ib/blob/__init__.py::kb_segment` —— kb 存储段名的**唯一真源**（空/`None` → `"default"`）；
  * `src/ib/lifecycle/__init__.py::_blob_scope_of` —— 删除 scope 由**台账记录**派生，
    不再沿用调用方 scope（HTTP 删除路径经 `resolve_scope` 得到的是**项目级** scope，
    `kb_ids=None` → `"default"` 段；而上传按**真实 kb** 落盘 → 旧实现删不到）。

**缺陷原状**：`blob_deleted` 恒 `False`、原文件字节成孤儿（磁盘/内存残留已删文档原始内容）。

**突变敏感性（自证，见 `docs/test_report.md` R4 突变自证节）**：
  * 若把 `_blob_scope_of` 回退为「返回调用方 scope」→ `TC-INT-074/075` 的**文件系统断言**失败
    （`on_disk` 仍存在、`blob_deleted` 为 `False`）；
  * 若把 `kb_segment` 回退为恒等（`return kb_id`）→ `TC-UNIT-055` 失败（default 段丢失）；
  * 若把 `blob_deleted` 改为恒 `True` → `TC-INT-076`（本无 blob）失败。

**离线纪律**：全程 SQLite / InMemory / 临时文件系统根（`tmp_path`）；不连任何生产库 / Qdrant /
DeepSeek / 外部服务。依赖替身仅用于「装配」，不遮蔽被测逻辑。
"""

from __future__ import annotations

import io
import json
import os
import pathlib

from django.core.files.uploadedfile import SimpleUploadedFile

from ib.blob import FsBlobStore
from ib.core import Scope
from ib.lifecycle import blob_ref_for
from ibweb.composition import resolve_scope

from conftest import request_ctx

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}


def _swap_real_fs(deps, tmp_path) -> FsBlobStore:
    """把装配里的 BlobStore 换成**真实文件系统**实现（根目录在测试临时目录）。

    只替换**依赖实现**（内存替身 → 真实 FsBlobStore），不改动任何被测逻辑；
    这样「删除后磁盘上是否还有该 doc 的字节」才可被**文件系统级**断言。
    """
    fs = FsBlobStore(str(tmp_path / "blobs"))
    deps.blobs = fs
    deps.lifecycle._blobs = fs  # noqa: SLF001 - 测试装配替换依赖实现（非遮蔽被测逻辑）
    return fs


def _disk_bytes_under(root: str) -> list[pathlib.Path]:
    return [p for p in pathlib.Path(root).rglob("*") if p.is_file()]


# --------------------------------------------------------------------------- #
# AC-IB-03-02：kb 级上传 → 项目级删除（错配路径）后，磁盘无任何残留字节
# --------------------------------------------------------------------------- #


def test_TC_INT_074_kb_upload_project_scope_delete_purges_real_bytes(deps, tmp_path):
    """[TC-INT-074] kb 级上传 + 项目级 scope 删除 → `blob_deleted=True` 且**磁盘上不残留任何字节**（AC-IB-03-02）。

    这是 FND-GROUP-D-03 的错配对：上传走 kb 级 scope（落真实 kb 段），删除走与 HTTP 视图**同源**的
    项目级 scope（`resolve_scope` → `kb_ids=None`）。修复前删除在 `default` 段查找 → 删 0 个 → 孤儿。

    本用例对 `FsBlobStore.root` 做**真实文件系统断言**（`is_file` / `exists`），而非仅断言返回值。
    """
    fs = _swap_real_fs(deps, tmp_path)
    body = "R4 原文件字节清理（kb 级上传 / 项目级删除）。".encode("utf-8")
    record = deps.lifecycle.submit_upload(
        request_ctx("p_alpha"),
        deps.lifecycle.validate_upload("r4_kb.txt", len(body), body[:4096]),
        "kb_a",
        data=io.BytesIO(body),
    )
    ref = blob_ref_for(record)
    assert ref is not None, "有内容的上传必须可推导原文件引用"
    on_disk = pathlib.Path(fs.root, *ref.rel_path.split("/"))
    assert on_disk.is_file(), "前置：kb 级上传应把原文件落盘到真实根目录"
    assert on_disk.parent.name == record.doc_id and on_disk.parent.parent.name == "kb_a"

    # 与 HTTP 删除路径同源的 scope（项目级，kb_ids=None）—— 即缺陷触发条件
    view_scope = resolve_scope(request_ctx("p_alpha"))
    assert view_scope.kb_ids is None, "HTTP 视图 scope 必须为项目级，否则本用例未在复现真实路径"
    report = deps.lifecycle.delete_document(view_scope, record.doc_id)

    assert report.blob_deleted is True, f"删除未清理原文件：{report}"
    assert report.ledger_deleted is True
    # 真实文件系统断言：字节、doc 目录、空 kb 目录都不再存在
    assert not on_disk.exists(), f"磁盘上仍残留该 doc 的 blob 字节（孤儿）：{on_disk}"
    assert not on_disk.parent.exists(), "doc 目录未清理"
    assert not on_disk.parent.parent.exists(), "空 kb 目录未清理"
    assert _disk_bytes_under(fs.root) == [], "存储根下仍有残留文件"


def test_TC_INT_075_http_delete_purges_real_bytes_no_orphan(http_app, tmp_path):
    """[TC-INT-075] 真实 Django HTTP `DELETE /api/files/{id}` 路径 + 真实 FsBlobStore → 磁盘无残留（AC-IB-03-02）。

    复用 `docs/evidence/groupd_r3_blob_probe.py` 的构造方式（发送真实 HTTP 请求），
    对核验者给出的**同一条真实 HTTP 路径**做文件系统级断言：修复前 `blob_deleted=False` 且对象残留；
    修复后 `blob_deleted=True` 且存储根下无任何文件。
    """
    deps, Client = http_app
    fs = _swap_real_fs(deps, tmp_path)
    client = Client()

    payload = "R4 HTTP 真实路径原文件清理样本。".encode("utf-8")
    up = SimpleUploadedFile("r4_http.txt", payload, content_type="text/plain")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    assert r.status_code == 201, r.content
    doc_id = json.loads(r.content)["doc_id"]

    uploaded = _disk_bytes_under(fs.root)
    assert len(uploaded) == 1, f"上传后应恰有 1 个原文件字节，实为 {uploaded}"
    on_disk = uploaded[0]
    assert on_disk.parent.name == doc_id, "落盘 doc 目录应与台账 doc_id 一致"

    d = client.delete(f"/api/files/{doc_id}", **AUTH)
    assert d.status_code == 200, d.content
    body = json.loads(d.content)
    assert body["blob_deleted"] is True, f"HTTP 删除未清理原文件：{body}"
    assert body["ledger_deleted"] is True

    assert not on_disk.exists(), "真实 HTTP 删除后磁盘上仍有该 doc 的 blob 字节（孤儿）"
    assert _disk_bytes_under(fs.root) == [], "存储根下仍有残留文件"
    assert deps.ledger.get_document(Scope("p_alpha"), doc_id) is None


# --------------------------------------------------------------------------- #
# AC-IB-03-02：本无 blob（D-08 `data=None` 路径）→ 不得虚报 True
# --------------------------------------------------------------------------- #


def test_TC_INT_076_delete_without_blob_reports_false(deps, tmp_path):
    """[TC-INT-076] `content_sha256` 为空的 D-08 路径删除 → `blob_deleted is False`（**不得恒 True 掩盖**）。

    `submit_upload(..., data=None)` 不落盘原文件（deviation D-08），故删除时**无字节可删**，
    正确结论是 `False`。这条与 TC-INT-074/075 互补：一个主张「确有且已删 → True」，
    一个主张「本无 → False」——两者一起把 `blob_deleted` 钉在**如实**语义上。
    """
    fs = _swap_real_fs(deps, tmp_path)
    record = deps.lifecycle.submit_upload(
        request_ctx("p_alpha"),
        deps.lifecycle.validate_upload("r4_noblob.txt", 5, b"nob01"),
        "kb_a",
        data=None,
    )
    assert record.content_sha256 == "", "data=None 路径不应有内容摘要"
    assert blob_ref_for(record) is None, "无内容摘要 → 不可推导原文件引用"

    report = deps.lifecycle.delete_document(resolve_scope(request_ctx("p_alpha")), record.doc_id)
    assert report.blob_deleted is False, f"本无原文件却报已删除（虚报清理成功）：{report}"
    assert report.ledger_deleted is True, "本无 blob 不应影响删除成功"
    assert _disk_bytes_under(fs.root) == [], "本无 blob 却出现了落盘文件"


# --------------------------------------------------------------------------- #
# AC-IB-03-02：跨项目不误删
# --------------------------------------------------------------------------- #


def test_TC_INT_077_cross_project_delete_does_not_touch_other_project_blob(deps, tmp_path):
    """[TC-INT-077] 删除项目 A 的 doc 不误删项目 B 的同内容 / 同 doc_id blob（隔离不变式）。

    存储布局为 `<root>/<project>/<kb>/<doc>/<sha>.<ext>`，前两级保证删除退化为**删目录**而不误伤；
    本用例同时覆盖「同内容不同 project」（真实上传，doc_id 不同，sha 相同）与
    「同 doc_id 不同 project」（人为放置，验证按 project 隔离而非按文件名/sha 全局匹配）。
    """
    fs = _swap_real_fs(deps, tmp_path)
    shared = "跨项目同一内容字节 SAME-077。".encode("utf-8")

    rec_a = deps.lifecycle.submit_upload(
        request_ctx("p_alpha"),
        deps.lifecycle.validate_upload("iso_a.txt", len(shared), shared[:4096]),
        "kb_a",
        data=io.BytesIO(shared),
    )
    rec_b = deps.lifecycle.submit_upload(
        request_ctx("p_beta"),
        deps.lifecycle.validate_upload("iso_b.txt", len(shared), shared[:4096]),
        "kb_b",
        data=io.BytesIO(shared),
    )
    ref_b = blob_ref_for(rec_b)
    assert ref_b is not None
    b_on_disk = pathlib.Path(fs.root, *ref_b.rel_path.split("/"))
    assert b_on_disk.is_file(), "前置：p_beta 的原文件应已落盘"

    # 人为在 p_beta 下放置与 rec_a **同 doc_id** 的同内容 blob
    same_doc_ref = fs.put(Scope("p_beta", ("kb_b",)), rec_a.doc_id, io.BytesIO(shared), "txt")
    same_on_disk = pathlib.Path(fs.root, *same_doc_ref.rel_path.split("/"))
    assert same_on_disk.is_file(), "前置：p_beta 的同 doc_id blob 应已落盘"

    report = deps.lifecycle.delete_document(resolve_scope(request_ctx("p_alpha")), rec_a.doc_id)
    assert report.blob_deleted is True, f"p_alpha 的 doc 未清理：{report}"

    assert b_on_disk.is_file(), "删除 p_alpha 的 doc 误删了 p_beta 的同内容 blob（跨项目越界）"
    assert same_on_disk.is_file(), "删除 p_alpha 的 doc 误删了 p_beta 的同 doc_id blob（跨项目越界）"
    assert deps.ledger.get_document(Scope("p_beta"), rec_b.doc_id) is not None, "p_beta 台账行被误删"


# --------------------------------------------------------------------------- #
# 不回归 FND-GROUP-D-02：fresh 装配 + 项目级 scope 删除「尚无事发生」的文档仍成功
# --------------------------------------------------------------------------- #


def test_TC_INT_078_fresh_project_scope_delete_succeeds_without_pending_ghost(http_app):
    """[TC-INT-078] fresh 装配（collection 未绑定）+ 项目级 scope 删除刚上传文档 → 200、无幽灵（不回归 FND-GROUP-D-02）。

    与 `TC-INT-041` 互补：此处额外断言「删除后 worker 不再认领（无 pending 幽灵）」，即删除的
    **读路径权威**性质在 R4 改动后依然成立；并显式区分「无 500」错误形态。
    """
    deps, Client = http_app  # fresh 装配：启动期只 ensure_collection，未 bind
    client = Client()
    up = SimpleUploadedFile("r4_fresh.txt", "刚上传还没被 worker 处理。".encode("utf-8"))
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **AUTH)
    assert r.status_code == 201, r.content
    doc_id = json.loads(r.content)["doc_id"]

    d = client.delete(f"/api/files/{doc_id}", **AUTH)
    assert d.status_code == 200, f"删除返回非 200（FND-GROUP-D-02 复发？）：{d.status_code} {d.content}"
    body = json.loads(d.content)
    assert body["ledger_deleted"] is True
    assert body["vectors_deleted"] == 0, "本项目尚无派生物，不应删到向量"

    # 无 pending 幽灵：台账行已删 → worker 不认领
    assert deps.ledger.get_document(Scope("p_alpha"), doc_id) is None
    proc = deps.lifecycle.process_pending("r4-w", 10)
    assert proc.processed == 0 and proc.succeeded == 0, f"已删文档仍被认领（幽灵）：{proc}"
