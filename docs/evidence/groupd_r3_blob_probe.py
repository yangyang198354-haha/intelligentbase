"""GROUP_D R3 增量 —— FND-GROUP-D-03 复现探针（原文件字节在生产删除路径上未被清理）。

诚实性声明：本探针**只读取依赖替身的内部状态以观测行为**，不修改任何 `src/**` 实现。
它走的是**与 HTTP 视图完全相同**的 scope 派生（`composition.resolve_scope(ctx)` → 项目级
`Scope(project_id=...)`，`kb_ids=None`），因此复现的是生产路径的真实语义。

运行：`PYTHONUTF8=1 IB_OFFLINE_MODE=1 python docs/evidence/groupd_r3_blob_probe.py`
期望现状（缺陷在场）：`blob_deleted=False` 且上传对象在删除后**仍在** BlobStore 内。
"""

from __future__ import annotations

import io
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_SRC), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "groupd-offline-token")

from conftest import offline_raw  # noqa: E402

from ib.context import make_request_context  # noqa: E402
from ib.core import Scope  # noqa: E402
from ibweb.composition import build_deps, resolve_scope  # noqa: E402


def main() -> int:
    deps = build_deps(offline_raw(), force=True)
    ctx = make_request_context(
        project_id="p_alpha", actor_id="tester", session_id="s1", roles=("manager",)
    )
    body = "生产删除路径的原文件清理探针。".encode("utf-8")
    validated = deps.lifecycle.validate_upload("probe.txt", len(body), body[:4096])
    record = deps.lifecycle.submit_upload(ctx, validated, "kb_a", data=io.BytesIO(body))

    store = deps.blobs
    objects = getattr(store, "_objects", None)
    before = len(objects) if objects is not None else -1
    print(f"上传 doc_id                                  = {record.doc_id}")
    print(f"上传后 BlobStore 对象数                        = {before}")
    if objects:
        first = next(iter(objects))
        print(f"  对象键前 3 段 (project, kb, doc)              = {first[:3]}")

    sc = resolve_scope(ctx)  # 与 ibweb/views.py::file_detail_endpoint 完全同源
    print(f"resolve_scope(ctx)                           = {sc}")
    report = deps.lifecycle.delete_document(sc, record.doc_id)
    print(f"delete_document(scope=项目级)                 = {report}")
    after = len(objects) if objects is not None else -1
    print(f"删除后 BlobStore 对象数                        = {after}")
    print(f"台账行（应为 None）                           = {deps.ledger.get_document(Scope('p_alpha'), record.doc_id)}")

    leak = after != 0
    print(f"原文件是否残留（幽灵 blob）？                  = {leak}")
    print(f"blob_deleted 是否为 False（缺陷在场）？        = {report.blob_deleted is False}")
    return 0 if leak else 1


if __name__ == "__main__":
    raise SystemExit(main())
