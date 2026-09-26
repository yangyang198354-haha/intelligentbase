"""单元测试层 4/N —— kb 存储段单一真源（R4 / FND-GROUP-D-03）。

覆盖验收标准：AC-IB-03-02（切分块与向量一并清理，不留下孤儿数据）。

被测事实：`ib.blob.kb_segment(kb_id)` 是「kb 维度的存储段名」的**唯一真源**，规则只有一条
「空串 / `None` → `"default"`」。写路径（`FsBlobStore._doc_dir` / `InMemoryBlobStore.put`）、
读路径（`ib.lifecycle.blob_ref_for`）与删除路径（`ib.lifecycle._blob_scope_of`）三处**必须同源**。
历史缺陷（FND-GROUP-D-03）正是三处各写一份同样的规则、其中删除路径漏写 → 「文件按真实 kb 落盘、
删除却在 `default` 段查找」→ 删不到 → 原文件成孤儿。

**突变敏感性（自证）**：本文件直接断言纯函数的取值与三处推导的一致性；若把 `kb_segment` 回退为
恒等（`return kb_id`，丢失「空 → default」规则）或把 `_blob_scope_of` 回退为「沿用调用方 scope」，
下列断言将失败（见 `docs/test_report.md` R4 突变自证节）。
"""

from __future__ import annotations

import os

from ib.blob import FsBlobStore, kb_segment
from ib.core import DocumentRecord, Scope
from ib.lifecycle import _blob_scope_of, blob_ref_for


def _record(*, kb_id: str, sha: str = "a" * 64) -> DocumentRecord:
    """构造一条最小台账记录（字段齐备，值无凭据）。"""
    return DocumentRecord(
        doc_id="doc-055",
        project_id="p_alpha",
        kb_id=kb_id,
        doc_name="sample.txt",
        ext="txt",
        size_bytes=3,
        content_sha256=sha,
        blob_ref=None,
        status="pending",
        error_code=None,
        chunk_count=0,
        indexed_collection_version=None,
        target_collection_version=None,
        lease_owner=None,
        lease_expires_at=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def test_TC_UNIT_055_kb_segment_is_single_source_of_truth(tmp_path):
    """[TC-UNIT-055] `kb_segment` 规则唯一，且写/读/删三处推导同源（AC-IB-03-02）。

    断言：
      1. 规则本身：`None` / `""` → `"default"`；非空 kb 原样返回；
      2. 读路径 `blob_ref_for`（`kb_id=""` 记录）产出第 2 段 == `kb_segment("")` == `"default"`；
      3. 写路径 `FsBlobStore._doc_dir`（项目级 scope `kb_ids=None`）与显式空 kb 段落到**同一**目录段；
      4. 删除路径 `_blob_scope_of` 由**记录**派生（携带真实 kb），落到与写路径**同一**目录段。
    """
    # 1) 规则本身（唯一真源）
    assert kb_segment(None) == "default"
    assert kb_segment("") == "default"
    assert kb_segment("kb_a") == "kb_a"

    # 2) 读路径：blob_ref_for 的 kb 段 = kb_segment(record.kb_id)
    ref = blob_ref_for(_record(kb_id=""))
    assert ref is not None
    assert ref.rel_path.split("/")[1] == kb_segment("") == "default"

    # 3) 写路径：项目级 scope（kb_ids=None）与显式空 kb 段的目录段一致
    fs = FsBlobStore(str(tmp_path / "blobs"))
    assert fs._doc_dir(Scope("p_alpha"), "doc-055") == fs._doc_dir(
        Scope("p_alpha", ("",)), "doc-055"
    )
    assert fs._doc_dir(Scope("p_alpha"), "doc-055").split(os.sep)[-2] == "default"

    # 4) 删除路径：由记录派生的 scope 与写路径同段（kb 级记录 → kb 段）
    derived = _blob_scope_of(_record(kb_id="kb_a"))
    assert derived.project_id == "p_alpha"
    assert derived.kb_ids == ("kb_a",), f"删除 scope 未携带记录的真实 kb：{derived}"
    assert fs._doc_dir(derived, "doc-055") == fs._doc_dir(Scope("p_alpha", ("kb_a",)), "doc-055")

    # 5) 空 kb 记录：删除 scope 归一为项目级（kb_ids=None），与写路径 default 段一致
    derived_empty = _blob_scope_of(_record(kb_id=""))
    assert derived_empty.kb_ids is None
    assert fs._doc_dir(derived_empty, "doc-055").split(os.sep)[-2] == "default"
