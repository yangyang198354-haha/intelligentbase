"""[R25 / GROUP_D] 单元 —— 文件更新（影子修订）、三个时间、检索存活过滤、分步删除（MOD-004/005/006）。

溯源：US-006（AC-006-01~04）、US-008（AC-008-01~07）、US-009（AC-009-01~03）、US-010（AC-010-03）、
US-012、US-014（AC-014-01/02）；偏差 D-03 / D-05。
“降级 / fail-open”类用例一律与 happy-path 正例成对（通用经验）。
"""

from __future__ import annotations

import pytest

from folder_r25_support import (
    PID,
    FailingEmbedder,
    get_doc,
    hits_containing,
    install_clock,
    put_file,
    scope_of,
    search,
    update_file,
)

S = scope_of()
K1 = "旧版独有关键词甲乙丙"
K2 = "新版独有关键词丁戊己"


def _file_view(deps, doc_id):
    from ibweb.serializers import LibraryFileSerializer

    rec = get_doc(deps, doc_id)
    return dict(LibraryFileSerializer(deps.library.file_view(S, rec)).data)


# --------------------------------------------------------------------------- #
# US-008：更新（正例 + 失败反例成对）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_070_AC_008_01_02_update_keeps_old_searchable_then_switches_atomically(deps, monkeypatch):
    """[TC-UNIT-R25-070] AC-008-01 / AC-008-02：更新提交后、新版索引完成前，旧版 K1 仍可检索（新版 K2 尚不可检索）；索引成功后 K2 命中、K1 命中 0、列表仅一条记录、目录与名称不变、
    最近更新时间 = 本次更新时间、上传时间不变。"""
    clock = install_clock(monkeypatch)
    folder = deps.library.create_folder(S, "", "规范库").folder_id
    live = put_file(deps, "规范.txt", f"规范正文 {K1}", folder_id=folder)
    t_upload = get_doc(deps, live.doc_id).uploaded_at
    clock.tick(3600)
    res = update_file(deps, live.doc_id, "规范.txt", f"规范正文 {K2}")
    assert res.changed and res.revision is not None
    # --- 更新提交后，索引完成前 ---
    old_view = _file_view(deps, live.doc_id)
    assert old_view["status"] == "indexed" and old_view["update_state"] == "updating"
    before = search(deps, f"规范正文 {K1}")
    assert before.degraded is False
    assert [h for h in hits_containing(before, K1) if h.doc_id == live.doc_id], "AC-008-02：旧版在新版索引成功前继续可检索"
    assert not hits_containing(search(deps, f"规范正文 {K2}"), K2), "新版尚未索引成功，不得提前可检索"
    # --- 索引完成（worker 处理修订行 → 单事务晋升）---
    clock.tick(60)
    deps.lifecycle.process_pending("w", 10)
    after = search(deps, f"规范正文 {K2}")
    assert after.degraded is False and hits_containing(after, K2), "K2 应命中新版"
    assert not hits_containing(search(deps, f"规范正文 {K1}"), K1), "新版索引成功后 K1 命中必须为 0"
    page = deps.library.browse(S, folder, page=1, page_size=50)
    assert [v.record.doc_name for v in page.files] == ["规范.txt"], "列表中仅有一条记录，所在目录与名称不变"
    new_rec = page.files[0].record
    assert new_rec.status == "indexed" and new_rec.folder_id == folder
    assert new_rec.uploaded_at == t_upload, "上传时间不变"
    # ADR-006：content_updated_at 在“内容被替换”的晋升事务中写入（REQ-FUNC-009“最近一次内容被替换的时间”），与 indexed_at 同刻
    assert new_rec.content_updated_at == "2026-03-01T01:01:00Z" == new_rec.indexed_at
    assert new_rec.content_updated_at > t_upload, "最近更新时间非空且晚于上传时间"
    assert page.files[0].update_state is None
    assert get_doc(deps, live.doc_id) is None, "旧存活行已被单事务替换"
    assert deps.tree.get_revision_of(S, new_rec.doc_id) is None


def test_TC_UNIT_R25_071_AC_008_03_failed_update_keeps_old_version_searchable_and_is_retryable(deps, monkeypatch):
    """[TC-UNIT-R25-071] AC-008-03（反例）：新版索引失败 → 状态“更新失败”+ 原因码，旧版仍 indexed 且 K1 仍可检索、K2 不可检索；
    与正例成对：恢复后重试 → 晋升成功，K2 命中、K1 为 0。"""
    live = put_file(deps, "规范.txt", f"规范正文 {K1}")
    res = update_file(deps, live.doc_id, "规范.txt", f"规范正文 {K2}")
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    deps.lifecycle.process_pending("w", 10)
    view = _file_view(deps, live.doc_id)
    assert view["status"] == "indexed", "页面不得显示为“已索引（新版）”之外的失败态：旧版保持已索引"
    assert view["update_state"] == "update_failed" and view["update_error_code"], "必须暴露更新失败及原因码"
    assert get_doc(deps, res.revision.doc_id).status == "failed"
    still = search(deps, f"规范正文 {K1}")
    assert still.degraded is False and [h for h in hits_containing(still, K1) if h.doc_id == live.doc_id]
    assert not hits_containing(search(deps, f"规范正文 {K2}"), K2)
    # --- 正例：可重试，恢复后切换成功 ---
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    retried = deps.lifecycle.retry_revision(S, live.doc_id)
    assert retried.status == "pending"
    deps.lifecycle.process_pending("w", 10)
    assert hits_containing(search(deps, f"规范正文 {K2}"), K2)
    assert not hits_containing(search(deps, f"规范正文 {K1}"), K1)


def test_TC_UNIT_R25_072_AC_008_03_discard_failed_revision_and_busy_guards(deps, monkeypatch):
    """[TC-UNIT-R25-072] AC-008-03 / ADR-004：失败的更新可丢弃（旧版不受影响）；parsing 中的更新不可丢弃（update_in_progress）；存活行 pending 时不可更新（doc_busy）。"""
    from ib.core.library import LibraryConflictError

    live = put_file(deps, "规范.txt", f"规范正文 {K1}")
    res = update_file(deps, live.doc_id, "规范.txt", f"规范正文 {K2}")
    # parsing 中的修订不可丢弃
    rev_id = res.revision.doc_id
    deps.ledger.claim_pending("w", 60, 5)  # 修订行 pending → parsing
    assert get_doc(deps, rev_id).status == "parsing"
    with pytest.raises(LibraryConflictError) as err:
        deps.lifecycle.discard_revision(S, live.doc_id)
    assert err.value.code == "update_in_progress"
    with pytest.raises(LibraryConflictError) as err2:
        update_file(deps, live.doc_id, "规范.txt", "又一个版本 内容不同")
    assert err2.value.code == "update_in_progress"
    # 置为 failed 后可丢弃，旧版仍在
    from ib.core import DocStatus

    deps.ledger.set_status(S, rev_id, DocStatus.FAILED, error_code="X")
    assert deps.lifecycle.discard_revision(S, live.doc_id) is True
    assert get_doc(deps, rev_id) is None and get_doc(deps, live.doc_id).status == "indexed"
    assert deps.lifecycle.discard_revision(S, live.doc_id) is False, "无修订可丢弃 → False"
    # 存活行 pending（刚上传未索引）→ doc_busy
    fresh = put_file(deps, "new.txt", "刚上传 尚未索引", process=False)
    with pytest.raises(LibraryConflictError) as err3:
        update_file(deps, fresh.doc_id, "new.txt", "刚上传 又换了内容")
    assert err3.value.code == "doc_busy"


def test_TC_UNIT_R25_073_AC_008_05_format_change_shows_new_name_keeps_position_and_upload_time(deps, monkeypatch):
    """[TC-UNIT-R25-073] AC-008-05：用不同格式 / 不同名的新文件更新 —— 被接受；条目显示新文件名（含新扩展名），目录与上传时间不变，K2 命中、K1 为 0。"""
    clock = install_clock(monkeypatch)
    folder = deps.library.create_folder(S, "", "D").folder_id
    live = put_file(deps, "规范.txt", f"规范正文 {K1}", folder_id=folder)
    t_up = get_doc(deps, live.doc_id).uploaded_at
    clock.tick(120)
    res = update_file(deps, live.doc_id, "规范v2.md", f"# 规范 v2\n\n{K2}")
    assert res.changed and res.final_name == "规范v2.md"
    deps.lifecycle.process_pending("w", 10)
    page = deps.library.browse(S, folder, page=1, page_size=50)
    assert [(v.record.doc_name, v.record.ext) for v in page.files] == [("规范v2.md", "md")], "显示新文件名，不再显示旧名"
    rec = page.files[0].record
    assert rec.folder_id == folder and rec.uploaded_at == t_up and rec.status == "indexed"
    res_k2 = search(deps, f"规范 v2 {K2}")
    assert [h for h in hits_containing(res_k2, K2) if h.doc_name == "规范v2.md"]
    assert not hits_containing(search(deps, f"规范正文 {K1}"), K1)


def test_TC_UNIT_R25_074_AC_008_06_identical_content_is_unchanged_noop(deps, monkeypatch):
    """[TC-UNIT-R25-074] AC-008-06：内容与现有完全相同 → changed=False，不建修订行；状态、索引成功时间、最近更新时间、向量数均不变。"""
    clock = install_clock(monkeypatch)
    live = put_file(deps, "same.txt", f"完全相同的内容 {K1}")
    before = get_doc(deps, live.doc_id)
    clock.tick(500)
    res = update_file(deps, live.doc_id, "same.txt", f"完全相同的内容 {K1}")
    assert res.changed is False and res.revision is None
    after = get_doc(deps, live.doc_id)
    assert (after.status, after.indexed_at, after.content_updated_at, after.chunk_count, after.updated_at) == (
        before.status, before.indexed_at, before.content_updated_at, before.chunk_count, before.updated_at,
    )
    assert deps.tree.get_revision_of(S, live.doc_id) is None
    # 成对：内容哪怕只差一个字符 → 视为变化
    assert update_file(deps, live.doc_id, "same.txt", f"完全相同的内容 {K1}!").changed is True


def test_TC_UNIT_R25_075_AC_008_07_update_name_collision_conflict_overwrite_rename(deps):
    """[TC-UNIT-R25-075] AC-008-07：用 `规范V2.MD`（与同目录另一条目 `规范v2.md` 仅大小写不同）更新 `规范.txt` ——
    ① 默认 on_conflict=fail → 409 并列出冲突条目，双方名称 / 内容 / 状态不变；② “覆盖”= 以冲突条目 Y 为更新目标（X 不变，条目数不变）；③ “两者保留”= X 更新后改名为 `规范V2 (2).MD`，Y 不变。"""
    from ib.core.library import LibraryConflictError

    d = deps.library.create_folder(S, "", "D").folder_id
    x = put_file(deps, "规范.txt", f"X 的内容 {K1}", folder_id=d)
    y = put_file(deps, "规范v2.md", "Y 的内容 原始", folder_id=d)
    with pytest.raises(LibraryConflictError) as err:
        update_file(deps, x.doc_id, "规范V2.MD", f"新内容 {K2}")
    assert err.value.code == "name_conflict" and err.value.clashes[0].entry_id == y.doc_id
    assert (get_doc(deps, x.doc_id).doc_name, get_doc(deps, y.doc_id).doc_name) == ("规范.txt", "规范v2.md")
    assert deps.tree.get_revision_of(S, x.doc_id) is None and deps.tree.get_revision_of(S, y.doc_id) is None
    assert deps.library.browse(S, d, page=1, page_size=50).total == 2
    # ③ 两者保留并自动改名
    res = update_file(deps, x.doc_id, "规范V2.MD", f"新内容 {K2}", on_conflict="rename")
    assert res.final_name == "规范V2 (2).MD"
    deps.lifecycle.process_pending("w", 10)
    names = sorted(v.record.doc_name for v in deps.library.browse(S, d, page=1, page_size=50).files)
    assert names == ["规范V2 (2).MD", "规范v2.md"], "目录下无同名（不区分大小写）条目"
    assert get_doc(deps, y.doc_id).doc_name == "规范v2.md"
    # ② 覆盖：改为以 Y 为更新目标，X（现 `规范V2 (2).MD`）不变，条目数不变
    x_now = [v.record for v in deps.library.browse(S, d, page=1, page_size=50).files if v.record.doc_name.startswith("规范V2 (2)")][0]
    res2 = update_file(deps, y.doc_id, "规范V2.MD", "覆盖到 Y 的新内容 戊戊")
    assert res2.changed
    deps.lifecycle.process_pending("w", 10)
    page = deps.library.browse(S, d, page=1, page_size=50)
    assert page.total == 2 and x_now.doc_id in {v.record.doc_id for v in page.files}, "X 保持不变，条目数不变"


# --------------------------------------------------------------------------- #
# US-009：三个时间
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_076_AC_009_01_02_three_times_semantics(deps, monkeypatch):
    """[TC-UNIT-R25-076] AC-009-01 / AC-009-02：上传 T1、索引成功 T2（T2≥T1）、从未更新 → 最近更新为 null；更新于 T3、索引成功 T4 → 上传仍 T1、更新 T3、索引 T4；
    仅重命名 / 移动后三个时间均不变。"""
    clock = install_clock(monkeypatch)
    rec = put_file(deps, "t.txt", f"时间语义 {K1}", process=False)
    clock.tick(30)
    deps.lifecycle.process_pending("w", 10)
    v1 = _file_view(deps, rec.doc_id)
    t1, t2 = v1["uploaded_at"], v1["indexed_at"]
    assert (t1, t2) == ("2026-03-01T00:00:00Z", "2026-03-01T00:00:30Z") and t2 >= t1
    assert v1["content_updated_at"] is None and v1["status"] == "indexed"
    clock.tick(1000)
    res = update_file(deps, rec.doc_id, "t.txt", f"时间语义 {K2}")
    t_submit = clock.now()
    clock.tick(20)
    deps.lifecycle.process_pending("w", 10)
    t4 = clock.now()
    new_id = deps.library.browse(S, "", page=1, page_size=50).files[0].record.doc_id
    v2 = _file_view(deps, new_id)
    # 最近更新时间 = 内容被替换（晋升）的时刻 T3（ADR-006）；索引成功时间 T4 在同一事务写入；上传时间仍为 T1
    t3 = v2["content_updated_at"]
    assert v2["uploaded_at"] == t1 and t3 is not None and t3 >= t_submit and v2["indexed_at"] == t4
    assert t3 > t2, "更新后最近更新时间晚于首次索引成功时间"
    # 重命名 / 移动不改三个时间
    clock.tick(500)
    dest = deps.library.create_folder(S, "", "dest").folder_id
    from ib.core.library import EntryRef

    deps.library.rename_file(S, new_id, "改名后.txt")
    deps.library.move(S, [EntryRef("file", new_id)], dest, {})
    v3 = _file_view(deps, new_id)
    assert (v3["uploaded_at"], v3["content_updated_at"], v3["indexed_at"]) == (t1, t3, t4)
    assert v3["name"] == "改名后.txt"


def test_TC_UNIT_R25_077_AC_009_03_failed_and_pending_show_no_indexed_time(deps, monkeypatch):
    """[TC-UNIT-R25-077] AC-009-03：失败的文件状态为 failed、带原因码、索引成功时间为 null；处理中 / 待处理同样为 null。
    成对：同一文件重试成功后才出现索引成功时间。"""
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    bad = put_file(deps, "bad.txt", "会失败的文件内容")
    v = _file_view(deps, bad.doc_id)
    assert v["status"] == "failed" and v["error_code"] and v["indexed_at"] is None
    pending = put_file(deps, "wait.txt", "还在排队的文件", process=False)
    assert _file_view(deps, pending.doc_id)["indexed_at"] is None and _file_view(deps, pending.doc_id)["status"] == "pending"
    claimed = deps.ledger.claim_pending("w", 60, 5)
    assert claimed and _file_view(deps, claimed[0].doc_id)["status"] == "parsing"
    assert _file_view(deps, claimed[0].doc_id)["indexed_at"] is None
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    deps.lifecycle.retry_document(S, bad.doc_id)
    deps.lifecycle.process_pending("w", 10)
    ok = _file_view(deps, bad.doc_id)
    assert ok["status"] == "indexed" and ok["indexed_at"]


def test_TC_UNIT_R25_078_AC_009_04_reindex_after_rebuild_refreshes_indexed_time_only(deps, monkeypatch):
    """[TC-UNIT-R25-078] AC-009-04：embedding 变更后重建重新索引完成于 T5 → 索引成功时间 = T5（不再是 T2），上传时间仍 T1，最近更新仍为 null，状态 indexed，目录位置不变。"""
    clock = install_clock(monkeypatch)
    d = deps.library.create_folder(S, "", "D").folder_id
    rec = put_file(deps, "r.txt", f"重建前后 {K1}", folder_id=d)
    before = _file_view(deps, rec.doc_id)
    clock.tick(86400)
    plan = deps.rebuild.plan_rebuild(PID)
    job = deps.rebuild.start_rebuild(PID, plan)
    deps.lifecycle.process_pending("rebuild-w", 10)
    deps.rebuild.step_rebuild(job, "rebuild-w", 10)
    after = _file_view(deps, rec.doc_id)
    t5 = "2026-03-02T00:00:00Z"
    assert after["indexed_at"] == t5 and before["indexed_at"] != t5
    assert after["uploaded_at"] == before["uploaded_at"] and after["content_updated_at"] is None
    assert after["status"] == "indexed" and get_doc(deps, rec.doc_id).folder_id == d


# --------------------------------------------------------------------------- #
# 检索存活过滤：happy-path 正例 与 降级反例成对（MOD-005）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_080_retrieval_alive_filter_happy_path_not_degraded_with_ledger_name_and_path(deps):
    """[TC-UNIT-R25-080] 正例：依赖齐备 → degraded=False 且有命中；命中的名称 / 路径 = 台账当前值（目录路径含目录链）。"""
    a = deps.library.create_folder(S, "", "技术文档").folder_id
    b = deps.library.create_folder(S, a, "设计").folder_id
    rec = put_file(deps, "方案.txt", "存活过滤正例专属内容 蒸汽加湿", folder_id=b)
    root_rec = put_file(deps, "根文件.txt", "根目录文件的专属内容 排烟风机")
    res = search(deps, "存活过滤正例专属内容 蒸汽加湿")
    assert res.degraded is False and res.degrade_reason is None
    top = [h for h in res.hits if h.doc_id == rec.doc_id]
    assert top and (top[0].doc_name, top[0].doc_path) == ("方案.txt", "技术文档/设计/方案.txt"), "AC-014-01"
    res2 = search(deps, "根目录文件的专属内容 排烟风机")
    root_hit = [h for h in res2.hits if h.doc_id == root_rec.doc_id][0]
    assert root_hit.doc_path == "根文件.txt" and not root_hit.doc_path.startswith("/"), "AC-014-02：根目录仅显示文件名"


def test_TC_UNIT_R25_081_retrieval_filters_non_live_hits_but_is_not_degraded(deps):
    """[TC-UNIT-R25-081] 正例（空结果 ≠ 故障）：命中全部不存活（台账行已删、向量成孤儿）→ degraded=False 且 hits==[]。"""
    rec = put_file(deps, "ghost.txt", "孤儿向量专属内容 冷凝水泵")
    assert [h for h in search(deps, "孤儿向量专属内容 冷凝水泵").hits if h.doc_id == rec.doc_id]
    deps.ledger.mark_deleted(S, rec.doc_id)  # 只删台账行，向量仍在（模拟崩溃留下的孤儿）
    res = search(deps, "孤儿向量专属内容 冷凝水泵")
    assert res.degraded is False and res.hits == []


def test_TC_UNIT_R25_082_retrieval_ledger_resolve_failure_is_fail_closed_ledger_unavailable(deps, monkeypatch):
    """[TC-UNIT-R25-082] 反例：存活解析故障 → degraded=True，原因 LEDGER_UNAVAILABLE，hits==[]（fail-closed，不返回未核验命中）；与 080 正例成对（同一数据，恢复后正常命中）。"""
    from ib.core import DegradeReason

    rec = put_file(deps, "x.txt", "解析故障专属内容 新风换气")
    ok = search(deps, "解析故障专属内容 新风换气")
    assert ok.degraded is False and [h for h in ok.hits if h.doc_id == rec.doc_id]
    real = deps.tree.resolve_live

    def boom(*a, **k):
        raise RuntimeError("ledger down")

    monkeypatch.setattr(deps.tree, "resolve_live", boom)
    bad = search(deps, "解析故障专属内容 新风换气")
    assert bad.degraded is True and bad.degrade_reason == DegradeReason.LEDGER_UNAVAILABLE and bad.hits == []
    monkeypatch.setattr(deps.tree, "resolve_live", real)
    again = search(deps, "解析故障专属内容 新风换气")
    assert again.degraded is False and [h for h in again.hits if h.doc_id == rec.doc_id]


def test_TC_UNIT_R25_083_retrieval_without_entry_resolver_is_baseline_behaviour(deps):
    """[TC-UNIT-R25-083] 兼容：未注入 entry_resolver 时与基线一致（不过滤、不回填路径）——孤儿向量仍被返回，doc_path 为空串。"""
    from ib.core import Scope
    from ib.retrieval import RetrievalService

    rec = put_file(deps, "base.txt", "基线行为专属内容 回风口")
    deps.ledger.mark_deleted(S, rec.doc_id)
    svc = RetrievalService(
        embedder=deps.embedder, vectors=deps.vectors, resolver=deps.collections,
        project_provider=deps.retrieval._project_provider, top_k=3, score_threshold=0.0, entry_resolver=None,
    )
    res = svc.search("基线行为专属内容 回风口", scope=Scope(project_id=PID, kb_ids=(PID,)))
    assert res.degraded is False
    assert [h for h in res.hits if h.doc_id == rec.doc_id and h.doc_path == ""]


def test_TC_UNIT_R25_084_AC_010_03_failed_file_not_retrievable_and_listed_failed(deps, monkeypatch):
    """[TC-UNIT-R25-084] AC-010-03：索引失败的文件检索无命中，列表中状态为“失败”（不是已索引）；成对：同批次的正常文件可检索。"""
    ok = put_file(deps, "ok.txt", "正常文件专属内容 风机盘管 一")
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(deps.lifecycle._embedder))
    bad = put_file(deps, "bad.txt", "失败文件专属内容 风机盘管 二")
    assert _file_view(deps, bad.doc_id)["status"] == "failed"
    res = search(deps, "失败文件专属内容 风机盘管 二")
    assert not [h for h in res.hits if h.doc_id == bad.doc_id]
    assert [h for h in search(deps, "正常文件专属内容 风机盘管 一").hits if h.doc_id == ok.doc_id]


# --------------------------------------------------------------------------- #
# US-006：递归删除（分步、失败隔离、与检索一致）
# --------------------------------------------------------------------------- #


def _tree_with_files(deps, n=10):
    a = deps.library.create_folder(S, "", "待删").folder_id
    b = deps.library.create_folder(S, a, "子1").folder_id
    deps.library.create_folder(S, a, "子2")
    docs = []
    for i in range(n):
        docs.append(put_file(deps, f"del{i}.txt", f"删除专属关键词{i} 离心机", folder_id=(a if i % 2 else b)))
    return a, docs


def test_TC_UNIT_R25_090_AC_006_01_02_recursive_delete_removes_everything_and_retrieval_zero(deps):
    """[TC-UNIT-R25-090] AC-006-01 / AC-006-02：删除前 detail 给出“2 个子文件夹、10 个文件”且不改任何数据；确认删除后目录与文件全部消失，
    向量数为 0，用其中任一文件独有关键词检索命中该文件 0 条；成对：同项目的其它文件不受影响。"""
    a, docs = _tree_with_files(deps)
    keep = put_file(deps, "keep.txt", "保留文件专属关键词 离心机")
    detail = deps.library.folder_detail(S, a)
    assert (detail.subtree_folders, detail.subtree_files) == (2, 10)
    assert deps.tree.count_subtree(S, a).files == 10, "确认前（含取消）不改任何数据"
    assert [h for h in search(deps, "删除专属关键词3 离心机").hits if h.doc_id == docs[3].doc_id]
    step = deps.library.delete_folder_step(S, a)
    assert (step.done, step.deleted_files, step.deleted_folders, step.failed, step.remaining_files) == (True, 10, 3, (), 0)
    assert deps.library.browse(S, "", page=1, page_size=50).folders == ()
    for d in docs:
        assert get_doc(deps, d.doc_id) is None
        assert deps.vectors.delete_doc_everywhere(PID, S, d.doc_id) == 0, "向量库中该文件向量数应已为 0"
        assert not [h for h in search(deps, f"删除专属关键词{docs.index(d)} 离心机").hits if h.doc_id == d.doc_id]
    assert [h for h in search(deps, "保留文件专属关键词 离心机").hits if h.doc_id == keep.doc_id]


def test_TC_UNIT_R25_091_AC_006_03_partial_failure_keeps_file_visible_then_recovers(deps, monkeypatch):
    """[TC-UNIT-R25-091] AC-006-03（反例）：1 个文件向量清理失败 → failed 列出该文件（稳定错误码，不含异常文本），其余删除；该文件及其目录链仍可见（可再次删除），
    不出现“列表看不到但仍能检索到”；成对：向量库恢复后再次删除 → done=True，目录消失，检索命中 0。"""
    a, docs = _tree_with_files(deps)
    victim = docs[3]
    real = deps.vectors.delete_doc_everywhere

    def flaky(project_id, scope, doc_id):
        if doc_id == victim.doc_id:
            raise RuntimeError("secret-internal-detail: qdrant down")
        return real(project_id, scope, doc_id)

    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", flaky)
    step = deps.library.delete_folder_step(S, a)
    assert step.done is False and step.deleted_files == 9 and step.remaining_files == 1
    assert [f.doc_id for f in step.failed] == [victim.doc_id]
    assert step.failed[0].name == victim.doc_name and step.failed[0].error_code == "internal_error"
    assert "secret-internal-detail" not in repr(step), "错误只用稳定码，不带异常文本"
    # 失败文件仍可见（其目录链保留），且仍存活
    chain_ids = {f.folder_id for f in deps.tree.list_subtree_folders(S, a)} | {a}
    assert get_doc(deps, victim.doc_id) is not None and get_doc(deps, victim.doc_id).folder_id in chain_ids
    assert deps.tree.get_folder(S, a) is not None
    assert [v.record.doc_id for v in deps.library.browse(S, get_doc(deps, victim.doc_id).folder_id, page=1, page_size=50).files] == [victim.doc_id]
    # 恢复
    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", real)
    done = deps.library.delete_folder_step(S, a)
    assert done.done is True and done.failed == () and done.deleted_files == 1
    assert deps.tree.get_folder(S, a) is None
    assert not [h for h in search(deps, "删除专属关键词3 离心机").hits if h.doc_id == victim.doc_id]


def test_TC_UNIT_R25_092_delete_step_budget_makes_progress_and_resumes(deps):
    """[TC-UNIT-R25-092] ADR-008：每步最多 max_files 个文件，done=False 时重复调用可续；最终 done=True（无状态、可恢复）。"""
    a, docs = _tree_with_files(deps, n=7)
    steps = []
    while True:
        step = deps.library.delete_folder_step(S, a, max_files=3)
        steps.append(step)
        if step.done:
            break
        assert step.deleted_files <= 3 and step.remaining_files > 0
        assert len(steps) < 10
    assert [s.deleted_files for s in steps] == [3, 3, 1]
    assert deps.tree.get_folder(S, a) is None


def test_TC_UNIT_R25_093_AC_006_04_delete_while_parsing_worker_exits_safely_without_resurrecting_vectors(deps):
    """[TC-UNIT-R25-093] AC-006-04：文件正处于“处理中”时确认删除 → 删除成功，该文件不在列表也不在向量库；随后 worker 对该（已被删除的）行的处理安全退出，不崩溃、不重新写入向量。"""
    a = deps.library.create_folder(S, "", "处理中").folder_id
    rec = put_file(deps, "busy.txt", "处理中被删除的专属内容 空气处理机", folder_id=a, process=False)
    claimed = deps.ledger.claim_pending("w", 60, 5)
    assert [c.doc_id for c in claimed] == [rec.doc_id] and get_doc(deps, rec.doc_id).status == "parsing"
    step = deps.library.delete_folder_step(S, a)
    assert step.done is True and step.deleted_files == 1
    assert get_doc(deps, rec.doc_id) is None
    from ib.lifecycle import _DeletedConcurrently

    # worker 带着旧的认领记录继续跑：只会得到受控的“并发删除”信号（process_pending 据此安全跳过），绝不写回向量 / 台账
    with pytest.raises(_DeletedConcurrently):
        deps.lifecycle._process_one(claimed[0], "w")
    assert get_doc(deps, rec.doc_id) is None
    res = search(deps, "处理中被删除的专属内容 空气处理机")
    assert res.degraded is False and not [h for h in res.hits if h.doc_id == rec.doc_id]
    assert deps.vectors.delete_doc_everywhere(PID, S, rec.doc_id) == 0


def test_TC_UNIT_R25_094_delete_file_cascades_revision_row(deps):
    """[TC-UNIT-R25-094] MOD-004：删除带在途修订行的存活文件 → 修订行与存活行一并删除（向量→blob→台账），检索 K1/K2 均为 0。"""
    live = put_file(deps, "casc.txt", f"级联删除 {K1}")
    res = update_file(deps, live.doc_id, "casc.txt", f"级联删除 {K2}")
    deps.lifecycle.delete_document(S, live.doc_id)
    assert get_doc(deps, live.doc_id) is None and get_doc(deps, res.revision.doc_id) is None
    deps.lifecycle.process_pending("w", 10)
    assert not hits_containing(search(deps, f"级联删除 {K1}"), K1)
    assert not hits_containing(search(deps, f"级联删除 {K2}"), K2)


# --------------------------------------------------------------------------- #
# 清理队列（D-05）：失败保留 + attempts+1，恢复后出队
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R25_095_purge_queue_failure_keeps_item_bumps_attempts_and_hides_orphans(deps, monkeypatch):
    """[TC-UNIT-R25-095] 清理队列故障：向量清理失败 → 队列项保留且 attempts+1，不外抛；期间孤儿向量对检索不可见；恢复后出队、向量物理消失（成对）。"""
    live = put_file(deps, "p.txt", f"清理队列 {K1}")
    update_file(deps, live.doc_id, "p.txt", f"清理队列 {K2}")
    real = deps.vectors.delete_doc_everywhere

    def boom(*a, **k):
        raise RuntimeError("vector store down")

    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", boom)
    deps.lifecycle.process_pending("w", 10)  # 晋升 → 旧 doc 入队 → 立即清理失败
    queued = deps.tree.list_purge(10)
    assert [q.doc_id for q in queued] == [live.doc_id] and queued[0].attempts >= 1
    assert deps.lifecycle.drain_purge_queue() == 0, "失败不外抛，返回出队数 0"
    assert deps.tree.list_purge(10)[0].attempts > queued[0].attempts
    res = search(deps, f"清理队列 {K1}")
    assert res.degraded is False and not hits_containing(res, K1), "孤儿向量对检索不可见（存活过滤）"
    monkeypatch.setattr(deps.vectors, "delete_doc_everywhere", real)
    assert deps.lifecycle.drain_purge_queue() == 1
    assert deps.tree.list_purge(10) == []
    assert real(PID, S, live.doc_id) == 0, "旧向量已物理消失"
