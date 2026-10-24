"""[R25 / GROUP_D] 单元 —— 目录树 / 条目台账存储与目录服务（MOD-002 / MOD-006；IFC-015 / IFC-019）。

内存替身与 **真实 SQLite 台账（临时目录）** 参数化，同一套断言（端口一致性，M-SA-001）。
溯源：US-003 / 004 / 005 / 006 / 013 / 016 / 012 / 017；偏差 D-03、D-06。
"""

from __future__ import annotations

import pytest

from folder_r25_support import PID, get_doc, put_file, scope_of, search, sqlite_deps


@pytest.fixture(params=["memory", "sqlite"])
def tdeps(request, raw, tmp_path, monkeypatch):
    from ibweb.composition import build_deps

    if request.param == "memory":
        return build_deps(raw, force=True)
    return sqlite_deps(tmp_path, raw, monkeypatch)


S = scope_of()


def _names(page):
    return [f.name for f in page.folders], [v.record.doc_name for v in page.files]


# --------------------------------------------------------------------------- #
# US-004 / US-016：新建文件夹、同名（不区分大小写）、层级上限
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_010_create_folder_visible_and_persistent(tdeps):
    """[TC-UNIT-R25-010] AC-004-01：在目录 D 新建 `设计` → D 下立即出现且为空；重新读取仍存在。"""
    d = tdeps.library.create_folder(S, "", "D")
    f = tdeps.library.create_folder(S, d.folder_id, "设计")
    assert f.depth == 2 and f.parent_id == d.folder_id
    page = tdeps.library.browse(S, d.folder_id, page=1, page_size=50)
    assert _names(page) == (["设计"], [])
    assert [c.name for c in page.breadcrumb] == ["D"]
    sub = tdeps.library.browse(S, f.folder_id, page=1, page_size=50)
    assert sub.total == 0


def test_TC_UNIT_R25_011_duplicate_folder_name_rejected_case_insensitive(tdeps):
    """[TC-UNIT-R25-011] AC-004-02 / AC-016-03：同名（含仅大小写不同）新建与重命名均 409，目录下仍只有原条目、原名不变。"""
    from ib.core.library import LibraryConflictError

    d = tdeps.library.create_folder(S, "", "D")
    design = tdeps.library.create_folder(S, d.folder_id, "Design")
    other = tdeps.library.create_folder(S, d.folder_id, "Other")
    for dup in ("Design", "design", "DESIGN"):
        with pytest.raises(LibraryConflictError) as err:
            tdeps.library.create_folder(S, d.folder_id, dup)
        assert err.value.code == "name_conflict" and err.value.clashes[0].entry_id == design.folder_id
    with pytest.raises(LibraryConflictError):
        tdeps.library.rename_folder(S, other.folder_id, "DESIGN")
    page = tdeps.library.browse(S, d.folder_id, page=1, page_size=50)
    assert sorted(_names(page)[0]) == ["Design", "Other"], "被拒绝的新建 / 重命名不得改动目录"


def test_TC_UNIT_R25_012_depth_limit_10_counts_absolute_layers(tdeps):
    """[TC-UNIT-R25-012] AC-004-03：根下一级 = 第 1 层，第 10 层目录内再建 → 拒绝（depth_exceeded）；第 10 层本身可建。"""
    from ib.core.library import LibraryValidationError

    parent = ""
    for i in range(1, 11):
        parent = tdeps.library.create_folder(S, parent, f"L{i}").folder_id  # 第 10 层成功
    with pytest.raises(LibraryValidationError) as err:
        tdeps.library.create_folder(S, parent, "L11")
    assert err.value.code == "depth_exceeded"


@pytest.mark.parametrize("bad,code", [("", "name_empty"), ("a/b", "name_illegal_char"), ("a\\b", "name_illegal_char"), ("x" * 256, "name_too_long")])
def test_TC_UNIT_R25_013_invalid_folder_names_create_nothing(tdeps, bad, code):
    """[TC-UNIT-R25-013] AC-016-01 / AC-016-02：非法名称新建与重命名都被拒绝，且不创建 / 不修改任何条目。"""
    from ib.core.library import EntryNameError

    keep = tdeps.library.create_folder(S, "", "合法")
    with pytest.raises(EntryNameError) as err:
        tdeps.library.create_folder(S, "", bad)
    assert err.value.code == code
    with pytest.raises(EntryNameError):
        tdeps.library.rename_folder(S, keep.folder_id, bad)
    assert tdeps.library.rename_folder(S, keep.folder_id, "2026 规范 v2").name == "2026 规范 v2"
    assert _names(tdeps.library.browse(S, "", page=1, page_size=50)) == (["2026 规范 v2"], [])


# --------------------------------------------------------------------------- #
# US-003：浏览 / 分页 / 面包屑 / 稳定排序
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_014_pagination_150_entries_no_dup_no_gap_stable_order(tdeps):
    """[TC-UNIT-R25-014] AC-003-02：150 个条目分页（≤100/页）无重复无遗漏，文件夹在前再按名称升序；多次读取顺序一致；page_size 截断到 100。"""
    parent = tdeps.library.create_folder(S, "", "big").folder_id
    for i in range(60):
        tdeps.library.create_folder(S, parent, f"dir{i:03d}")
    for i in range(90):
        put_file(tdeps, f"f{i:03d}.txt", f"文件内容 {i}", folder_id=parent, process=False)
    first = tdeps.library.browse(S, parent, page=1, page_size=100)
    second = tdeps.library.browse(S, parent, page=2, page_size=100)
    assert first.total == 150 and len(first.folders) + len(first.files) == 100
    assert len(second.folders) + len(second.files) == 50
    seen = [f.name for f in first.folders + second.folders] + [v.record.doc_name for v in first.files + second.files]
    assert len(seen) == 150 and len(set(seen)) == 150
    assert [f.name for f in first.folders] == [f"dir{i:03d}" for i in range(60)], "文件夹在前且按名称升序"
    assert [v.record.doc_name for v in first.files] == [f"f{i:03d}.txt" for i in range(40)]
    again = tdeps.library.browse(S, parent, page=1, page_size=100)
    assert _names(again) == _names(first)
    huge = tdeps.library.browse(S, parent, page=1, page_size=10_000)
    assert huge.page_size == 100 and len(huge.folders) + len(huge.files) == 100, "page_size 必须截断到 100"


def test_TC_UNIT_R25_015_breadcrumb_and_unknown_folder_not_found(tdeps):
    """[TC-UNIT-R25-015] AC-003-01：A/B 的面包屑依次为 [A]、[A,B]；不存在的目录 id → NotFoundError。"""
    from ib.core import NotFoundError

    a = tdeps.library.create_folder(S, "", "A")
    b = tdeps.library.create_folder(S, a.folder_id, "B")
    assert [c.name for c in tdeps.library.browse(S, a.folder_id, page=1, page_size=50).breadcrumb] == ["A"]
    assert [c.name for c in tdeps.library.browse(S, b.folder_id, page=1, page_size=50).breadcrumb] == ["A", "B"]
    with pytest.raises(NotFoundError):
        tdeps.library.browse(S, "0" * 32, page=1, page_size=50)


def test_TC_UNIT_R25_016_cross_project_folder_id_is_not_found_not_leaked(tdeps):
    """[TC-UNIT-R25-016] AC-003-03：P1 以 P2 的目录 id 访问 → NotFoundError，与不存在的 id 不可区分（异常类与消息均相同）。"""
    from ib.core import NotFoundError, Scope

    other = tdeps.library.create_folder(Scope("p_beta"), "", "X-secret")
    with pytest.raises(NotFoundError) as cross:
        tdeps.library.browse(S, other.folder_id, page=1, page_size=50)
    with pytest.raises(NotFoundError) as missing:
        tdeps.library.browse(S, "f" * 32, page=1, page_size=50)
    assert type(cross.value) is type(missing.value) and str(cross.value) == str(missing.value)
    assert "X-secret" not in str(cross.value)
    for op in (
        lambda: tdeps.library.rename_folder(S, other.folder_id, "hijack"),
        lambda: tdeps.library.folder_detail(S, other.folder_id),
        lambda: tdeps.library.delete_folder_step(S, other.folder_id),
    ):
        with pytest.raises(NotFoundError):
            op()
    assert tdeps.library.browse(Scope("p_beta"), "", page=1, page_size=50).folders[0].name == "X-secret", "他项目目录未被改动"


# --------------------------------------------------------------------------- #
# US-005 / US-012：重命名后归属 / 状态 / 引用路径
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_017_rename_folder_keeps_contents_status_and_updates_citation_path(tdeps):
    """[TC-UNIT-R25-017] AC-005-01：重命名文件夹后其内 3 个已索引文件仍在其中、仍为 indexed；检索引用路径为 `新名/…`，不再出现旧名。"""
    old = tdeps.library.create_folder(S, "", "旧名")
    docs = [put_file(tdeps, f"d{i}.txt", f"重命名专属内容{i} 风机盘管", folder_id=old.folder_id) for i in range(3)]
    tdeps.library.rename_folder(S, old.folder_id, "新名")
    page = tdeps.library.browse(S, old.folder_id, page=1, page_size=50)
    assert [v.record.status for v in page.files] == ["indexed"] * 3
    assert [c.name for c in page.breadcrumb] == ["新名"]
    res = search(tdeps, "重命名专属内容0 风机盘管")
    assert res.degraded is False and res.hits
    paths = {h.doc_path for h in res.hits}
    assert paths and all(p.startswith("新名/") for p in paths), paths
    assert not any("旧名" in p for p in paths)
    assert {h.doc_id for h in res.hits} <= {d.doc_id for d in docs}


def test_TC_UNIT_R25_018_rename_file_keeps_status_times_and_rejects_ext_change(tdeps):
    """[TC-UNIT-R25-018] AC-012-01 / AC-012-02：文件重命名后状态与三时间不变、引用显示新名；同目录重名 409；任何扩展名变化（含改为另一受支持类型）400 且名称不变。"""
    from ib.core.library import LibraryConflictError, LibraryValidationError

    rec = put_file(tdeps, "旧.txt", "改名专属正文 冷水机组")
    put_file(tdeps, "新.txt", "占位另一个文件")
    before = get_doc(tdeps, rec.doc_id)
    renamed = tdeps.library.rename_file(S, rec.doc_id, "更新后的名称.txt")
    assert renamed.doc_name == "更新后的名称.txt" and renamed.status == "indexed"
    assert (renamed.uploaded_at, renamed.content_updated_at, renamed.indexed_at) == (
        before.uploaded_at, before.content_updated_at, before.indexed_at,
    ), "重命名不得改变三个时间"
    res = search(tdeps, "改名专属正文 冷水机组")
    top = [h for h in res.hits if h.doc_id == rec.doc_id]
    assert top and top[0].doc_name == "更新后的名称.txt" and top[0].doc_path == "更新后的名称.txt"
    assert not any(h.doc_name == "旧.txt" for h in res.hits)
    with pytest.raises(LibraryConflictError):
        tdeps.library.rename_file(S, rec.doc_id, "新.txt")
    for ext_change in ("x.md", "x.docx", "x.exe", "x"):
        with pytest.raises(LibraryValidationError) as err:
            tdeps.library.rename_file(S, rec.doc_id, ext_change)
        assert err.value.code == "ext_change_not_allowed"
    assert get_doc(tdeps, rec.doc_id).doc_name == "更新后的名称.txt"


# --------------------------------------------------------------------------- #
# US-013：移动（含 D-06 覆盖语义）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_020_move_file_and_folder_preserve_retrieval_and_update_path(tdeps):
    """[TC-UNIT-R25-020] AC-013-01 / AC-013-02：移动文件与整个文件夹后原位置无、新位置有，状态仍 indexed，检索命中数不变且路径同步为新位置。"""
    from ib.core.library import EntryRef

    a = tdeps.library.create_folder(S, "", "A").folder_id
    b = tdeps.library.create_folder(S, "", "B").folder_id
    c = tdeps.library.create_folder(S, "", "C").folder_id
    x = put_file(tdeps, "x.txt", "移动单文件专属 空调箱", folder_id=a)
    before = {h.doc_id for h in search(tdeps, "移动单文件专属 空调箱").hits}
    out = tdeps.library.move(S, [EntryRef("file", x.doc_id)], b, {})
    assert [r.entry_id for r in out.moved] == [x.doc_id]
    assert _names(tdeps.library.browse(S, a, page=1, page_size=50)) == ([], [])
    assert _names(tdeps.library.browse(S, b, page=1, page_size=50)) == ([], ["x.txt"])
    res = search(tdeps, "移动单文件专属 空调箱")
    assert {h.doc_id for h in res.hits} == before
    assert [h.doc_path for h in res.hits if h.doc_id == x.doc_id] == ["B/x.txt"]
    # 文件夹整体移动：A 含 5 个文件
    folder = tdeps.library.create_folder(S, "", "Pack").folder_id
    ids = [put_file(tdeps, f"p{i}.txt", f"整体移动专属{i} 新风机组", folder_id=folder).doc_id for i in range(5)]
    tdeps.library.move(S, [EntryRef("folder", folder)], c, {})
    assert "Pack" not in _names(tdeps.library.browse(S, "", page=1, page_size=50))[0]
    moved = tdeps.library.browse(S, folder, page=1, page_size=50)
    assert [cr.name for cr in moved.breadcrumb] == ["C", "Pack"] and len(moved.files) == 5
    res2 = search(tdeps, "整体移动专属3 新风机组")
    assert any(h.doc_id == ids[3] and h.doc_path == "C/Pack/p3.txt" for h in res2.hits)


def test_TC_UNIT_R25_021_move_rejections_leave_structure_unchanged(tdeps):
    """[TC-UNIT-R25-021] AC-013-04：移动到自身 / 子孙、超 10 层均拒绝（move_into_self / depth_exceeded），原结构不变。"""
    from ib.core.library import EntryRef, LibraryValidationError

    a = tdeps.library.create_folder(S, "", "A").folder_id
    b = tdeps.library.create_folder(S, a, "B").folder_id
    for target in (a, b):
        with pytest.raises(LibraryValidationError) as err:
            tdeps.library.move(S, [EntryRef("folder", a)], target, {})
        assert err.value.code == "move_into_self"
    deep = ""
    for i in range(1, 10):
        deep = tdeps.library.create_folder(S, deep, f"D{i}").folder_id  # 第 9 层
    with pytest.raises(LibraryValidationError) as err:
        tdeps.library.move(S, [EntryRef("folder", a)], deep, {})  # A+B 共 2 层 → 第 11 层
    assert err.value.code == "depth_exceeded"
    assert [c.name for c in tdeps.library.browse(S, b, page=1, page_size=50).breadcrumb] == ["A", "B"]
    assert "A" in _names(tdeps.library.browse(S, "", page=1, page_size=50))[0]


def test_TC_UNIT_R25_021b_move_to_other_project_target_is_rejected_structure_unchanged(tdeps):
    """[TC-UNIT-R25-021b] AC-013-04（跨项目）：目标目录属于其他项目 → 拒绝（NotFoundError，与不存在不可区分，A-10 / CL-010），原结构不变；他项目的目录也不被改动。"""
    from ib.core import NotFoundError, Scope
    from ib.core.library import EntryRef

    mine = tdeps.library.create_folder(S, "", "mine").folder_id
    doc = put_file(tdeps, "m.txt", "跨项目移动前", folder_id=mine, process=False)
    theirs = tdeps.library.create_folder(Scope("p_beta"), "", "theirs").folder_id
    for entry in (EntryRef("file", doc.doc_id), EntryRef("folder", mine)):
        with pytest.raises(NotFoundError):
            tdeps.library.move(S, [entry], theirs, {})
    assert get_doc(tdeps, doc.doc_id).folder_id == mine
    assert tdeps.library.browse(Scope("p_beta"), theirs, page=1, page_size=50).total == 0
    assert "mine" in _names(tdeps.library.browse(S, "", page=1, page_size=50))[0]


def test_TC_UNIT_R25_022_move_conflict_requires_resolution_and_is_all_or_nothing(tdeps):
    """[TC-UNIT-R25-022] AC-013-03：目标有同名条目且未给处理方式 → 409 并带冲突列表，台账完全不变（含同批无冲突条目也不移动）。"""
    from ib.core.library import EntryRef, LibraryConflictError

    src = tdeps.library.create_folder(S, "", "src").folder_id
    dst = tdeps.library.create_folder(S, "", "dst").folder_id
    clash_old = put_file(tdeps, "same.txt", "目标侧旧内容", folder_id=dst)
    same = put_file(tdeps, "same.txt", "来源侧同名内容", folder_id=src)
    free = put_file(tdeps, "free.txt", "无冲突文件", folder_id=src)
    with pytest.raises(LibraryConflictError) as err:
        tdeps.library.move(S, [EntryRef("file", same.doc_id), EntryRef("file", free.doc_id)], dst, {})
    assert err.value.clashes[0].entry_id == clash_old.doc_id
    assert err.value.initiators and err.value.initiators[0].entry_id == same.doc_id
    assert _names(tdeps.library.browse(S, src, page=1, page_size=50))[1] == ["free.txt", "same.txt"]
    assert _names(tdeps.library.browse(S, dst, page=1, page_size=50))[1] == ["same.txt"]
    assert get_doc(tdeps, clash_old.doc_id) is not None


def test_TC_UNIT_R25_023_move_conflict_skip_rename_and_noop(tdeps):
    """[TC-UNIT-R25-023] AC-013-03 / AC-011-02：移动冲突选 skip → 不动；选 rename → `x (2).txt`；移到当前所在目录视为 skipped。"""
    from ib.core.library import EntryRef

    src = tdeps.library.create_folder(S, "", "src").folder_id
    dst = tdeps.library.create_folder(S, "", "dst").folder_id
    put_file(tdeps, "x.txt", "目标侧", folder_id=dst)
    a = put_file(tdeps, "x.txt", "来源 A", folder_id=src)
    out = tdeps.library.move(S, [EntryRef("file", a.doc_id)], dst, {a.doc_id: "skip"})
    assert [r.entry_id for r in out.skipped] == [a.doc_id] and not out.moved
    assert _names(tdeps.library.browse(S, src, page=1, page_size=50))[1] == ["x.txt"]
    out2 = tdeps.library.move(S, [EntryRef("file", a.doc_id)], dst, {a.doc_id: "rename"})
    assert out2.renamed and out2.renamed[0][1] == "x (2).txt"
    assert _names(tdeps.library.browse(S, dst, page=1, page_size=50))[1] == ["x (2).txt", "x.txt"]
    noop = tdeps.library.move(S, [EntryRef("file", a.doc_id)], dst, {})
    assert [r.entry_id for r in noop.skipped] == [a.doc_id] and not noop.moved


def test_TC_UNIT_R25_024_D06_move_overwrite_file_replaces_target_and_purges_vectors(tdeps):
    """[TC-UNIT-R25-024] 偏差 D-06（文件）：移动冲突选“覆盖” → 目标侧同名文件被替换（移出台账并清理向量），来源文件原样落到目标，检索旧内容命中 0。"""
    from ib.core.library import EntryRef

    src = tdeps.library.create_folder(S, "", "src").folder_id
    dst = tdeps.library.create_folder(S, "", "dst").folder_id
    old = put_file(tdeps, "x.txt", "被覆盖前的内容 旧版标记甲乙", folder_id=dst)
    new = put_file(tdeps, "x.txt", "覆盖后的内容 新版标记丙丁", folder_id=src)
    assert [h.doc_id for h in search(tdeps, "被覆盖前的内容 旧版标记甲乙").hits if h.doc_id == old.doc_id], "前置：旧内容可检索"
    out = tdeps.library.move(S, [EntryRef("file", new.doc_id)], dst, {new.doc_id: "overwrite"})
    assert [r.entry_id for r in out.moved] == [new.doc_id] and old.doc_id in out.overwritten_doc_ids
    assert get_doc(tdeps, old.doc_id) is None, "被覆盖的文件必须移出台账"
    assert get_doc(tdeps, new.doc_id).folder_id == dst
    assert _names(tdeps.library.browse(S, dst, page=1, page_size=50))[1] == ["x.txt"], "目标目录里只剩一个 x.txt"
    res = search(tdeps, "被覆盖前的内容 旧版标记甲乙")
    assert res.degraded is False and not [h for h in res.hits if h.doc_id == old.doc_id]
    assert tdeps.tree.list_purge(50) == [] or all(p.doc_id != old.doc_id for p in tdeps.tree.list_purge(50)), "清理队列已排空（立即 drain）"
    assert [h for h in search(tdeps, "覆盖后的内容 新版标记丙丁").hits if h.doc_id == new.doc_id], "来源文件仍可检索"


def test_TC_UNIT_R25_025_D06_move_overwrite_folder_merges_recursively(tdeps):
    """[TC-UNIT-R25-025] 偏差 D-06（文件夹）：移动冲突选“覆盖” → 两个同名文件夹合并为一个；同名文件被替换，目标侧独有文件、来源独有文件、子文件夹（递归合并）全部保留，来源文件夹消失。"""
    from ib.core.library import EntryRef

    s = tdeps.library.create_folder(S, "", "S").folder_id
    t = tdeps.library.create_folder(S, "", "T").folder_id
    a_src = tdeps.library.create_folder(S, s, "A").folder_id
    a_dst = tdeps.library.create_folder(S, t, "A").folder_id
    sub_src = tdeps.library.create_folder(S, a_src, "sub").folder_id
    sub_dst = tdeps.library.create_folder(S, a_dst, "SUB").folder_id  # 仅大小写不同 → 同名递归合并
    old_x = put_file(tdeps, "x.txt", "目标侧 x 旧", folder_id=a_dst)
    keep_o = put_file(tdeps, "other.txt", "目标侧独有", folder_id=a_dst)
    new_x = put_file(tdeps, "x.txt", "来源侧 x 新", folder_id=a_src)
    only_y = put_file(tdeps, "y.txt", "来源侧独有", folder_id=a_src)
    deep_src = put_file(tdeps, "deep.txt", "来源子目录文件", folder_id=sub_src)
    deep_dst = put_file(tdeps, "deep_keep.txt", "目标子目录文件", folder_id=sub_dst)
    out = tdeps.library.move(S, [EntryRef("folder", a_src)], t, {a_src: "overwrite"})
    assert [r.entry_id for r in out.moved] == [a_src] and old_x.doc_id in out.overwritten_doc_ids
    top = tdeps.library.browse(S, t, page=1, page_size=50)
    assert [f.name for f in top.folders] == ["A"] and top.folders[0].folder_id == a_dst, "合并进目标侧已有文件夹"
    assert "A" not in [f.name for f in tdeps.library.browse(S, s, page=1, page_size=50).folders], "来源文件夹消失"
    merged = tdeps.library.browse(S, a_dst, page=1, page_size=50)
    assert sorted(v.record.doc_name for v in merged.files) == ["other.txt", "x.txt", "y.txt"]
    assert {v.record.doc_id for v in merged.files} == {keep_o.doc_id, new_x.doc_id, only_y.doc_id}, "x.txt 是来源侧的新文件"
    assert get_doc(tdeps, old_x.doc_id) is None
    assert [f.name for f in merged.folders] == ["SUB"], "同名子文件夹递归合并为一个（保留目标侧名称）"
    sub = tdeps.library.browse(S, sub_dst, page=1, page_size=50)
    assert sorted(v.record.doc_name for v in sub.files) == ["deep.txt", "deep_keep.txt"]
    assert {v.record.doc_id for v in sub.files} == {deep_src.doc_id, deep_dst.doc_id}


def test_TC_UNIT_R25_026_D06_move_overwrite_across_kinds_is_rejected(tdeps):
    """[TC-UNIT-R25-026] 偏差 D-06 边界：文件与文件夹之间不能互相覆盖 → bad_request，台账不变。"""
    from ib.core.library import EntryRef, LibraryValidationError

    dst = tdeps.library.create_folder(S, "", "dst").folder_id
    tdeps.library.create_folder(S, dst, "name.txt")  # 文件夹占用了名称
    src = tdeps.library.create_folder(S, "", "src").folder_id
    f = put_file(tdeps, "name.txt", "文件", folder_id=src)
    with pytest.raises(LibraryValidationError) as err:
        tdeps.library.move(S, [EntryRef("file", f.doc_id)], dst, {f.doc_id: "overwrite"})
    assert err.value.code == "bad_request"
    assert get_doc(tdeps, f.doc_id).folder_id == src


# --------------------------------------------------------------------------- #
# US-003：uploaded / 存活解析；US-006：子树计数
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_030_count_subtree_and_resolve_live_paths(tdeps):
    """[TC-UNIT-R25-030] AC-006-01：子树计数 = 2 个子文件夹、10 个文件（不含修订行）；resolve_live 返回当前目录路径，不存活 id 不在结果中。"""
    a = tdeps.library.create_folder(S, "", "A").folder_id
    b = tdeps.library.create_folder(S, a, "B").folder_id
    tdeps.library.create_folder(S, a, "C")
    ids = []
    for i in range(10):
        ids.append(put_file(tdeps, f"n{i}.txt", f"子树文件{i}", folder_id=(a if i < 5 else b), process=False).doc_id)
    detail = tdeps.library.folder_detail(S, a)
    assert (detail.subtree_folders, detail.subtree_files) == (2, 10)
    live = tdeps.tree.resolve_live(PID, ids[:1] + ids[7:8] + ["ghost"])
    assert live[ids[0]].path == "A/n0.txt" and live[ids[7]].path == "A/B/n7.txt" and "ghost" not in live


def test_TC_UNIT_R25_031_list_documents_include_revisions_d03(tdeps):
    """[TC-UNIT-R25-031] 偏差 D-03：`list_documents(include_revisions)` —— 默认（True）含修订行（重建口径）；False 不含；存活行两种口径都在。"""
    live = put_file(tdeps, "rev.txt", "旧版正文 修订行口径")
    from folder_r25_support import update_file

    res = update_file(tdeps, live.doc_id, "rev.txt", "新版正文 修订行口径 已更新")
    assert res.changed and res.revision is not None
    kw = {"page": 1, "page_size": 100, "status": None}
    ids_with = {r.doc_id for r in tdeps.ledger.list_documents(S, include_revisions=True, **kw)[0]}
    ids_without = {r.doc_id for r in tdeps.ledger.list_documents(S, include_revisions=False, **kw)[0]}
    ids_default = {r.doc_id for r in tdeps.ledger.list_documents(S, **kw)[0]}
    assert res.revision.doc_id in ids_with and live.doc_id in ids_with
    assert res.revision.doc_id not in ids_without and live.doc_id in ids_without
    assert ids_default == ids_with, "默认值保持基线行为（含修订行，重建计数口径）"


def test_TC_UNIT_R25_032_port_declares_include_revisions_d03():
    """[TC-UNIT-R25-032] 偏差 D-03（端口一致性）：`LedgerRepository.list_documents` 端口、SQLite 实现与内存实现的参数名集合一致且含 include_revisions=True。"""
    import inspect

    from ib.core.ports import LedgerRepository
    from ib.ledger import InMemoryLedgerRepository
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    sigs = {
        cls.__name__: inspect.signature(cls.list_documents)
        for cls in (LedgerRepository, InMemoryLedgerRepository, SqliteLedgerRepository)
    }
    names = {k: set(v.parameters) - {"self"} for k, v in sigs.items()}
    assert len({frozenset(v) for v in names.values()}) == 1, names
    for sig in sigs.values():
        assert sig.parameters["include_revisions"].default is True
