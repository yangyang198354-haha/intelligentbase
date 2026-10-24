"""[R25 / GROUP_D] 单元 —— 批量上传计划与逐文件受理（MOD-007 / IFC-020）。

溯源：US-001（AC-001-01/02/04）、US-002（AC-002-02/03）、US-007、US-011（AC-011-01~05）、US-015（AC-015-01~04）。
真实 `UploadBatchService` + 内存台账 / 向量库替身；不连任何外部服务。
"""

from __future__ import annotations

import io

import pytest

from folder_r25_support import PID, ctx_of, get_doc, put_file, scope_of

S = scope_of()
MB = 1024 * 1024


def _entries(spec):
    from ib.library.uploads import ManifestEntry

    return [ManifestEntry(i, rel, size) for i, (rel, size) in enumerate(spec)]


def _plan(deps, spec, *, target="", res=None, commit=False, svc=None):
    return (svc or deps.uploads).plan(
        ctx_of(), S, target_folder_id=target, entries=_entries(spec), resolutions=res or {}, commit=commit
    )


def _accept(deps, batch_id, idx, name, data: bytes):
    return deps.uploads.accept_item(
        ctx_of(), S, batch_id, idx, filename=name, size_bytes=len(data), head=data[:4096], data=io.BytesIO(data)
    )


def _svc(deps, **limits):
    from ib.library.uploads import UploadBatchService, UploadLimits

    base = dict(max_files=1000, max_total_bytes=1024 * MB, max_depth=10, max_file_bytes=50 * MB)
    base.update(limits)
    return UploadBatchService(
        tree=deps.tree, batches=deps.upload_batches, lifecycle=deps.lifecycle,
        limits=UploadLimits(**base), batch_ttl_hours=24,
    )


def _no_side_effects(deps, monkeypatch):
    """断言“整体拒绝、不产生半成品”：批次存储不得被写入，根目录保持为空。"""
    calls = []
    orig = deps.upload_batches.create_batch
    monkeypatch.setattr(deps.upload_batches, "create_batch", lambda *a, **k: calls.append(1) or orig(*a, **k))
    return calls


def _root_total(deps):
    return deps.tree.list_children(S, "", page=1, page_size=100).total


# --------------------------------------------------------------------------- #
# US-015 限额
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_050_AC_015_01_over_file_count_rejected_before_anything_is_created(deps, monkeypatch):
    """[TC-UNIT-R25-050] AC-015-01：默认配置 1001 个文件 → limit_files（limit=1000, actual=1001），不产生批次 / 目录 / 文件；恰 1000 个通过。"""
    from ib.core.library import LibraryValidationError

    calls = _no_side_effects(deps, monkeypatch)
    over = [(f"big/f{i}.txt", 10) for i in range(1001)]
    with pytest.raises(LibraryValidationError) as err:
        _plan(deps, over, commit=True)
    assert err.value.code == "limit_files" and dict(err.value.details) == {"limit": 1000, "actual": 1001}
    assert calls == [] and _root_total(deps) == 0
    ok = _plan(deps, over[:1000], commit=False)
    assert ok.total == 1000 and ok.accepted_count == 1000


def test_TC_UNIT_R25_051_AC_015_02_depth_counts_existing_layers(deps, monkeypatch):
    """[TC-UNIT-R25-051] AC-015-02：目标在第 8 层、所选文件夹嵌套 3 层 → 最深第 11 层，整体拒绝；同一文件夹从第 7 层上传（最深第 10 层）通过。"""
    from ib.core.library import LibraryValidationError

    chain = []
    parent = ""
    for i in range(1, 9):
        parent = deps.library.create_folder(S, parent, f"L{i}").folder_id
        chain.append(parent)
    calls = _no_side_effects(deps, monkeypatch)
    spec = [("A/B/C/f.txt", 10)]
    with pytest.raises(LibraryValidationError) as err:
        _plan(deps, spec, target=chain[7], commit=True)  # 第 8 层 + 3 = 11
    assert err.value.code == "depth_exceeded" and err.value.details["actual"] == 11 and err.value.details["limit"] == 10
    assert calls == []
    assert deps.tree.count_subtree(S, chain[7]).folders == 0, "不产生半成品目录"
    ok = _plan(deps, spec, target=chain[6], commit=False)  # 第 7 层 + 3 = 10
    assert ok.accepted_count == 1


def test_TC_UNIT_R25_052_AC_015_03_limits_are_configurable_and_per_file_cap_still_applies(raw):
    """[TC-UNIT-R25-052] AC-015-03：上限配置为 20 层 / 2000 个文件时，1500 个文件、15 层的文件夹通过校验；单文件 50MB 上限仍适用（超限者被跳过）。"""
    from ibweb.composition import build_deps

    raw["upload_batch_max_files"] = 2000
    raw["library_max_depth"] = 20
    deps = build_deps(raw, force=True)
    nested = "/".join(f"d{i}" for i in range(15))
    spec = [(f"{nested}/f{i}.txt", 5) for i in range(1500)]
    plan = deps.uploads.plan(
        ctx_of(), S, target_folder_id="", entries=_entries(spec), resolutions={}, commit=False
    )
    assert plan.limits.max_files == 2000 and plan.limits.max_depth == 20
    assert plan.total == 1500 and plan.accepted_count == 1500
    spec2 = spec[:3] + [(f"{nested}/huge.txt", 51 * MB)]
    p2 = deps.uploads.plan(ctx_of(), S, target_folder_id="", entries=_entries(spec2), resolutions={}, commit=False)
    assert [i.reason_code for i in p2.items if i.action == "skip"] == ["TOO_LARGE"]


def test_TC_UNIT_R25_053_AC_015_04_total_size_limit_boundary(raw, monkeypatch):
    """[TC-UNIT-R25-053] AC-015-04：总大小上限 L（配置 1MB）—— 超过 L 整体拒绝（details 含上限与实际），不产生批次 / 目录 / 文件；总大小恰为 L 通过。"""
    from ib.core.library import LibraryValidationError
    from ibweb.composition import build_deps

    raw["upload_batch_max_total_mb"] = 1
    deps = build_deps(raw, force=True)
    calls = _no_side_effects(deps, monkeypatch)
    limit = MB
    with pytest.raises(LibraryValidationError) as err:
        _plan(deps, [("a/one.txt", limit - 10), ("a/two.txt", 11)], commit=True)
    assert err.value.code == "limit_total_bytes"
    assert dict(err.value.details) == {"limit": limit, "actual": limit + 1}
    assert calls == [] and _root_total(deps) == 0
    exact = _plan(deps, [("a/one.txt", limit - 10), ("a/two.txt", 10)], commit=False)
    assert exact.accepted_count == 2


# --------------------------------------------------------------------------- #
# US-002 / US-001：分类与“跳过”口径、目录延迟创建
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_054_AC_002_02_classification_counts_and_reasons(deps):
    """[TC-UNIT-R25-054] AC-002-02：95 合规 + 3 个不支持类型 + 1 个空文件 + 1 个超 50MB → 接受 95、跳过 5、三数之和 100；跳过原因分别为 UNSUPPORTED_TYPE / EMPTY_FILE / TOO_LARGE。"""
    spec = [(f"f/ok{i}.txt", 100) for i in range(95)]
    spec += [("f/a.exe", 10), ("f/b.dll", 10), ("f/c.markdown", 10), ("f/empty.txt", 0), ("f/huge.pdf", 51 * MB)]
    plan = _plan(deps, spec, commit=False)
    assert plan.total == 100 and plan.accepted_count == 95 and plan.skipped_count == 5
    assert plan.accepted_count + plan.skipped_count == plan.total
    skipped = {i.rel_path: i.reason_code for i in plan.items if i.action == "skip"}
    assert skipped == {
        "f/a.exe": "UNSUPPORTED_TYPE", "f/b.dll": "UNSUPPORTED_TYPE", "f/c.markdown": "UNSUPPORTED_TYPE",
        "f/empty.txt": "EMPTY_FILE", "f/huge.pdf": "TOO_LARGE",
    }


def test_TC_UNIT_R25_055_AC_002_02_magic_mismatch_counts_as_skipped_not_failed(deps):
    """[TC-UNIT-R25-055] AC-002-02（魔数）：扩展名 .pdf 但内容不是 PDF → 逐文件受理时记“跳过”（MAGIC_MISMATCH），汇总 failed=0 且三数之和 = 总数；不入库。"""
    plan = _plan(deps, [("m/fake.pdf", 100), ("m/good.txt", 100)], commit=True)
    r0 = _accept(deps, plan.batch_id, 0, "fake.pdf", b"this is not a pdf at all")
    r1 = _accept(deps, plan.batch_id, 1, "good.txt", b"good content for magic test")
    assert (r0.state, r0.reason_code) == ("skipped", "MAGIC_MISMATCH")
    assert r1.state == "accepted"
    summary = deps.uploads.summary(S, plan.batch_id)
    assert (summary.accepted, summary.skipped, summary.failed, summary.pending) == (1, 1, 0, 0)
    assert summary.accepted + summary.skipped + summary.failed + summary.pending == summary.total == 2
    page = deps.library.browse(S, "", page=1, page_size=50)
    assert [f.name for f in page.folders] == ["m"]
    inner = deps.library.browse(S, page.folders[0].folder_id, page=1, page_size=50)
    assert [v.record.doc_name for v in inner.files] == ["good.txt"], "魔数失败的文件不得入库"


def test_TC_UNIT_R25_056_AC_001_01_hierarchy_preserved(deps):
    """[TC-UNIT-R25-056] AC-001-01：上传 A/x.txt 与 A/B/y.txt → 目标目录下出现 A（含 x.txt 与子文件夹 B），B 内含 y.txt；层级与本地一致。"""
    plan = _plan(deps, [("A/x.txt", 20), ("A/B/y.txt", 20)], commit=True)
    assert [i.final_rel_path for i in plan.items] == ["A/x.txt", "A/B/y.txt"]
    _accept(deps, plan.batch_id, 0, "x.txt", b"x file content one")
    _accept(deps, plan.batch_id, 1, "y.txt", b"y file content two")
    a = deps.library.browse(S, "", page=1, page_size=50).folders[0]
    a_page = deps.library.browse(S, a.folder_id, page=1, page_size=50)
    assert a.name == "A" and [v.record.doc_name for v in a_page.files] == ["x.txt"] and [f.name for f in a_page.folders] == ["B"]
    b_page = deps.library.browse(S, a_page.folders[0].folder_id, page=1, page_size=50)
    assert [v.record.doc_name for v in b_page.files] == ["y.txt"]
    assert [c.name for c in b_page.breadcrumb] == ["A", "B"]


def test_TC_UNIT_R25_057_AC_001_04_no_empty_or_all_skipped_subfolders_created(deps):
    """[TC-UNIT-R25-057] AC-001-04：A 含合规 x.txt、全部被跳过的子文件夹 A/onlybad（z.exe）与魔数失败的 A/fake（q.pdf）→ 只创建 A（内含 x.txt），A 下子文件夹数为 0；z.exe 列入跳过。"""
    plan = _plan(deps, [("A/x.txt", 20), ("A/onlybad/z.exe", 10), ("A/fake/q.pdf", 20)], commit=True)
    assert [(i.rel_path, i.reason_code) for i in plan.items if i.action == "skip"] == [("A/onlybad/z.exe", "UNSUPPORTED_TYPE")]
    _accept(deps, plan.batch_id, 0, "x.txt", "合规文件内容 x".encode())
    _accept(deps, plan.batch_id, 2, "q.pdf", b"not pdf content!!!!!")
    a = deps.library.browse(S, "", page=1, page_size=50).folders[0]
    assert deps.tree.count_subtree(S, a.folder_id).folders == 0, "空 / 全跳过 / 魔数失败的子文件夹均不得被创建"
    assert [v.record.doc_name for v in deps.library.browse(S, a.folder_id, page=1, page_size=50).files] == ["x.txt"]


def test_TC_UNIT_R25_058_AC_002_03_dependency_failure_isolated_per_item_and_retryable(deps, monkeypatch):
    """[TC-UNIT-R25-058] AC-002-03：服务端临时错误（blob 不可用）→ 该项记 failed 并上抛，其余项不受影响；对同 idx 重试成功后 failed 变 accepted；汇总三数之和 = 总数。"""
    from ib.core import DependencyUnavailableError

    plan = _plan(deps, [("r/a.txt", 30), ("r/b.txt", 30), ("r/c.txt", 30)], commit=True)
    ok0 = _accept(deps, plan.batch_id, 0, "a.txt", b"first file content here")
    orig_put = deps.lifecycle._blobs.put

    def broken_put(*a, **k):
        raise DependencyUnavailableError("blob down", dependency="blob")

    monkeypatch.setattr(deps.lifecycle._blobs, "put", broken_put)
    with pytest.raises(DependencyUnavailableError):
        _accept(deps, plan.batch_id, 1, "b.txt", b"second file content here")
    monkeypatch.setattr(deps.lifecycle._blobs, "put", orig_put)
    ok2 = _accept(deps, plan.batch_id, 2, "c.txt", b"third file content here")
    mid = deps.uploads.summary(S, plan.batch_id)
    assert ok0.state == ok2.state == "accepted"
    assert (mid.accepted, mid.skipped, mid.failed, mid.pending) == (2, 0, 1, 0)
    retry = _accept(deps, plan.batch_id, 1, "b.txt", b"second file content here")
    assert retry.state == "accepted"
    end = deps.uploads.summary(S, plan.batch_id)
    assert (end.accepted, end.skipped, end.failed, end.pending) == (3, 0, 0, 0)
    # 补偿：失败那次不得遗留半成品（目录里只有三个文件，且无重复 b.txt）
    r = deps.library.browse(S, deps.library.browse(S, "", page=1, page_size=50).folders[0].folder_id, page=1, page_size=50)
    assert sorted(v.record.doc_name for v in r.files) == ["a.txt", "b.txt", "c.txt"]


def test_TC_UNIT_R25_059_accept_item_is_idempotent_and_checks_declared_size(deps):
    """[TC-UNIT-R25-059] 服务端权威：重复 PUT 返回既有终态不重复入库；实际字节数 > 声明 → 跳过 SIZE_MISMATCH（累计实际 ≤ 声明和 ≤ 总上限）。"""
    plan = _plan(deps, [("i/a.txt", 100), ("i/b.txt", 5)], commit=True)
    first = _accept(deps, plan.batch_id, 0, "a.txt", b"idempotent content")
    again = _accept(deps, plan.batch_id, 0, "a.txt", b"idempotent content")
    assert first.state == again.state == "accepted" and first.doc_id == again.doc_id
    over = _accept(deps, plan.batch_id, 1, "b.txt", b"way more than five bytes")
    assert (over.state, over.reason_code) == ("skipped", "SIZE_MISMATCH")
    folder = deps.library.browse(S, "", page=1, page_size=50).folders[0]
    assert [v.record.doc_name for v in deps.library.browse(S, folder.folder_id, page=1, page_size=50).files] == ["a.txt"]


def test_TC_UNIT_R25_060_batch_not_found_cross_project_and_bad_idx(deps):
    """[TC-UNIT-R25-060] REQ-NFUNC-005：他项目 / 不存在的批次与批次项 → NotFoundError（不可区分）。"""
    from ib.core import NotFoundError, Scope

    plan = _plan(deps, [("i/a.txt", 100)], commit=True)
    with pytest.raises(NotFoundError):
        deps.uploads.summary(Scope("p_beta"), plan.batch_id)
    with pytest.raises(NotFoundError):
        deps.uploads.accept_item(ctx_of(), S, "0" * 32, 0, filename="a.txt", size_bytes=1, head=b"a", data=io.BytesIO(b"a"))
    with pytest.raises(NotFoundError):
        _accept(deps, plan.batch_id, 99, "a.txt", b"zzz")


# --------------------------------------------------------------------------- #
# US-011 同名冲突
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_061_AC_011_01_conflict_listed_and_nothing_changes_until_resolved(deps, monkeypatch):
    """[TC-UNIT-R25-061] AC-011-01 / AC-011-04：D 已有 a.txt，再传 a.txt → dry-run 列出冲突，原文件内容 / 状态 / 向量不变；commit 但未选择 → 409 unresolved_conflict 且不建批次；仅 dry-run 不留下任何变化（关闭对话框 = 取消）。"""
    from ib.core.library import LibraryConflictError

    d = deps.library.create_folder(S, "", "D").folder_id
    old = put_file(deps, "a.txt", "原始内容 冲突前后不变 关键字乙", folder_id=d)
    before = get_doc(deps, old.doc_id)
    calls = _no_side_effects(deps, monkeypatch)
    dry = _plan(deps, [("a.txt", 30)], target=d)
    assert [(c.rel_path, c.kind, c.existing_id, c.existing_name) for c in dry.conflicts] == [("a.txt", "file", old.doc_id, "a.txt")]
    assert dry.items[0].action == "skip" and dry.items[0].reason_code == "CONFLICT_UNRESOLVED"
    with pytest.raises(LibraryConflictError) as err:
        _plan(deps, [("a.txt", 30)], target=d, commit=True)
    assert err.value.code == "unresolved_conflict" and err.value.clashes[0].entry_id == old.doc_id
    assert calls == [], "未决冲突不得创建批次"
    after = get_doc(deps, old.doc_id)
    assert (after.status, after.chunk_count, after.content_sha256, after.indexed_at) == (
        before.status, before.chunk_count, before.content_sha256, before.indexed_at,
    )
    assert deps.library.browse(S, d, page=1, page_size=50).total == 1


@pytest.mark.parametrize(
    "action,expect_action,expect_final,expect_reason",
    [("overwrite", "update", "a.txt", None), ("skip", "skip", None, "USER_SKIPPED"), ("rename", "create", "a (2).txt", None)],
)
def test_TC_UNIT_R25_062_AC_011_02_three_resolutions(deps, action, expect_action, expect_final, expect_reason):
    """[TC-UNIT-R25-062] AC-011-02：覆盖 → 按“更新”处理（target=原 doc）；跳过 → 不入库并计入跳过；两者保留 → 新文件改名 `a (2).txt`。"""
    old = put_file(deps, "a.txt", "原文件内容")
    plan = _plan(deps, [("a.txt", 30)], res={"a.txt": action}, commit=True)
    item = plan.items[0]
    assert (item.action, item.final_rel_path, item.reason_code) == (expect_action, expect_final, expect_reason)
    assert item.target_doc_id == (old.doc_id if action == "overwrite" else None)


def test_TC_UNIT_R25_063_AC_011_02_rename_sequence_skips_taken_numbers(deps):
    """[TC-UNIT-R25-063] AC-011-02：`a (2).txt` 已存在时，自动改名顺延为 `a (3).txt`；原 a.txt 不变。"""
    put_file(deps, "a.txt", "原文件内容 一", process=False)
    put_file(deps, "a (2).txt", "原文件内容 二", process=False)
    plan = _plan(deps, [("a.txt", 30)], res={"a.txt": "rename"}, commit=True)
    assert plan.items[0].final_rel_path == "a (3).txt"
    _accept(deps, plan.batch_id, 0, "a.txt", "新内容三 独立文件".encode())
    names = sorted(v.record.doc_name for v in deps.library.browse(S, "", page=1, page_size=50).files)
    assert names == ["a (2).txt", "a (3).txt", "a.txt"]


def test_TC_UNIT_R25_064_AC_011_05_case_variant_is_a_conflict_and_renames_to_a_2(deps):
    """[TC-UNIT-R25-064] AC-011-05：D 已有 A.txt，上传 a.txt（仅大小写不同）→ 同样列出冲突，选择前不出现 a.txt；选“两者保留”→ `a (2).txt`，A.txt 不变。"""
    old = put_file(deps, "A.txt", "大写文件内容")
    dry = _plan(deps, [("a.txt", 30)])
    assert dry.conflicts and dry.conflicts[0].existing_name == "A.txt"
    assert [v.record.doc_name for v in deps.library.browse(S, "", page=1, page_size=50).files] == ["A.txt"]
    plan = _plan(deps, [("a.txt", 30)], res={"a.txt": "rename"}, commit=True)
    assert plan.items[0].final_rel_path == "a (2).txt"
    _accept(deps, plan.batch_id, 0, "a.txt", "小写文件内容 新".encode())
    names = sorted(v.record.doc_name for v in deps.library.browse(S, "", page=1, page_size=50).files)
    assert names == ["A.txt", "a (2).txt"] and get_doc(deps, old.doc_id).doc_name == "A.txt"


def test_TC_UNIT_R25_065_AC_011_03_folder_overwrite_merges_and_file_conflict_needs_its_own_answer(deps):
    """[TC-UNIT-R25-065] AC-011-03：上传文件夹 A，目标已有同名文件夹 A（含 x.txt、other.txt）——选“覆盖”合并为一个 A；x.txt 冲突仍需单独确认并按更新处理；other.txt 保持不变。"""
    a = deps.library.create_folder(S, "", "A").folder_id
    old_x = put_file(deps, "x.txt", "旧 x 内容", folder_id=a)
    other = put_file(deps, "other.txt", "其他文件 保持不变", folder_id=a)
    spec = [("A/x.txt", 30), ("A/new.txt", 30)]
    dry = _plan(deps, spec, res={"A": "overwrite"})
    assert [(c.rel_path, c.kind) for c in dry.conflicts] == [("A/x.txt", "file")], "文件夹已选覆盖后，剩余冲突是 x.txt"
    plan = _plan(deps, spec, res={"A": "overwrite", "A/x.txt": "overwrite"}, commit=True)
    by_path = {i.rel_path: i for i in plan.items}
    assert (by_path["A/x.txt"].action, by_path["A/x.txt"].target_doc_id) == ("update", old_x.doc_id)
    assert by_path["A/new.txt"].action == "create"
    _accept(deps, plan.batch_id, 0, "x.txt", "新 x 内容 已更新".encode())
    _accept(deps, plan.batch_id, 1, "new.txt", "全新文件 内容".encode())
    folders = deps.library.browse(S, "", page=1, page_size=50).folders
    assert [f.name for f in folders] == ["A"] and folders[0].folder_id == a, "合并为同一个文件夹，而非产生 A (2)"
    merged = deps.library.browse(S, a, page=1, page_size=50)
    assert sorted(v.record.doc_name for v in merged.files) == ["new.txt", "other.txt", "x.txt"]
    assert get_doc(deps, other.doc_id).status == "indexed" and get_doc(deps, other.doc_id).content_sha256 == other.content_sha256


def test_TC_UNIT_R25_066_AC_011_03_folder_rename_and_skip_resolutions(deps):
    """[TC-UNIT-R25-066] AC-011-03 的其余分支：文件夹选“两者保留”→ 整棵子树改用 `A (2)`；选“跳过”→ 整棵子树 USER_SKIPPED。"""
    deps.library.create_folder(S, "", "A")
    spec = [("A/x.txt", 30), ("A/sub/y.txt", 30)]
    renamed = _plan(deps, spec, res={"A": "rename"}, commit=False)
    assert [i.final_rel_path for i in renamed.items] == ["A (2)/x.txt", "A (2)/sub/y.txt"]
    skipped = _plan(deps, spec, res={"A": "skip"}, commit=False)
    assert [(i.action, i.reason_code) for i in skipped.items] == [("skip", "USER_SKIPPED")] * 2
    assert not skipped.conflicts


def test_TC_UNIT_R25_067_AC_007_01_files_land_in_target_folder_not_root(deps):
    """[TC-UNIT-R25-067] AC-007-01：一次选择 3 个合规文件上传到目录 D → D 下出现这 3 个文件，初始“待处理”，根目录下不出现。"""
    d = deps.library.create_folder(S, "", "D").folder_id
    plan = _plan(deps, [(f"f{i}.txt", 30) for i in range(3)], target=d, commit=True)
    for i in range(3):
        r = _accept(deps, plan.batch_id, i, f"f{i}.txt", f"目录内文件 {i} 的内容".encode())
        assert r.state == "accepted"
    page = deps.library.browse(S, d, page=1, page_size=50)
    assert sorted(v.record.doc_name for v in page.files) == ["f0.txt", "f1.txt", "f2.txt"]
    assert {v.record.status for v in page.files} == {"pending"}
    assert deps.library.browse(S, "", page=1, page_size=50).files == ()
    deps.lifecycle.process_pending("w", 10)
    assert {v.record.status for v in deps.library.browse(S, d, page=1, page_size=50).files} == {"indexed"}


def test_TC_UNIT_R25_068_AC_007_02_unsupported_type_skipped_others_land(deps):
    """[TC-UNIT-R25-068] AC-007-02：混选中 1 个不支持类型 → 其余正常入库，不支持者给出原因并不入库。"""
    plan = _plan(deps, [("ok1.txt", 30), ("bad.exe", 30), ("ok2.txt", 30)], commit=True)
    assert plan.accepted_count == 2 and plan.skipped_count == 1
    assert [i.reason_code for i in plan.items if i.action == "skip"] == ["UNSUPPORTED_TYPE"]
    _accept(deps, plan.batch_id, 0, "ok1.txt", "第一个合规文件".encode())
    _accept(deps, plan.batch_id, 2, "ok2.txt", "第二个合规文件".encode())
    assert sorted(v.record.doc_name for v in deps.library.browse(S, "", page=1, page_size=50).files) == ["ok1.txt", "ok2.txt"]
