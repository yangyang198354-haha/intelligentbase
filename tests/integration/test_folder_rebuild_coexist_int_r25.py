"""[R25 / GROUP_D] 集成 —— 文件更新 / 删除 / 重命名与索引重建（collection 版本切换）共存（MOD-008 / ADR-007）。

边界：`ib.lifecycle`（修订晋升）↔ `ib.rebuild`（激活 / 补晋升）↔ `ib.ledger.tree` ↔ 向量库（多 collection 版本）↔ 检索。
溯源：REQ-NFUNC-004（与重建共存）、AC-008-02（更新期间旧版可检索）、AC-009-04（重建刷新索引成功时间）、AC-006-02。
离线：内存台账 / 向量库 / 假 embedder。
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
    sqlite_deps,
    update_file,
)

S = scope_of()
K1 = "共存旧版关键词甲乙"
K2 = "共存新版关键词丙丁"


def _start_rebuild_and_reindex(deps, *, finish: bool = False):
    """启动重建并让 worker 把存活文档重新索引到目标版本。

    `finish=False`：任务仍处于在飞状态（planned / running），写路径被重定向到目标版本；
    `finish=True`：再调一次 `step_rebuild`，任务进入 `succeeded`（已重建完成、尚未激活）。
    """
    plan = deps.rebuild.plan_rebuild(PID)
    job = deps.rebuild.start_rebuild(PID, plan)
    deps.lifecycle.process_pending("rebuild-w", 50)
    if finish:
        deps.rebuild.step_rebuild(job, "rebuild-w", 50)
    return job


def test_TC_INT_R25_050_update_during_rebuild_defers_promotion_until_activation(deps):
    """[TC-INT-R25-050] ADR-007 / REQ-NFUNC-004 / AC-008-02：重建在途时更新文件 ——
    修订行索引成功但“推迟晋升”（旧版仍是存活行、仍可检索、新内容暂不可检索）；激活新版本后补晋升：旧内容命中 0、新内容命中；单条记录；旧向量被清理。"""
    live = put_file(deps, "共存.txt", f"共存测试正文 {K1}")
    _start_rebuild_and_reindex(deps)
    assert deps.ledger.active_collection_version(PID) == "1"
    assert get_doc(deps, live.doc_id).indexed_collection_version == "2", "前置：存活行已被重建重新索引到目标版本"
    res = update_file(deps, live.doc_id, "共存.txt", f"共存测试正文 {K2}")
    deps.lifecycle.process_pending("w", 10)
    rev = get_doc(deps, res.revision.doc_id)
    assert rev.status == "indexed" and rev.revision_of == live.doc_id, "修订行已索引但尚未晋升"
    assert get_doc(deps, live.doc_id) is not None, "存活行仍在"
    # 重建在途：读路径读旧 active 版本 —— 旧版继续可检索，新版暂不可检索
    mid_old = search(deps, f"共存测试正文 {K1}")
    assert mid_old.degraded is False and [h for h in hits_containing(mid_old, K1) if h.doc_id == live.doc_id]
    assert not hits_containing(search(deps, f"共存测试正文 {K2}"), K2)
    listing = deps.library.browse(S, "", page=1, page_size=50).files
    assert len(listing) == 1 and listing[0].searchable is False and listing[0].update_state == "updating"
    # 激活（守卫：无 failed / pending / parsing）→ 补晋升
    deps.rebuild.activate_version(PID, "2")
    assert deps.ledger.active_collection_version(PID) == "2"
    after = deps.library.browse(S, "", page=1, page_size=50)
    assert [v.record.doc_name for v in after.files] == ["共存.txt"] and after.total == 1
    new_rec = after.files[0].record
    assert new_rec.doc_id == res.revision.doc_id and new_rec.revision_of is None and new_rec.content_updated_at
    assert after.files[0].searchable is True and after.files[0].update_state is None
    assert get_doc(deps, live.doc_id) is None
    now_new = search(deps, f"共存测试正文 {K2}")
    assert now_new.degraded is False and hits_containing(now_new, K2)
    assert not hits_containing(search(deps, f"共存测试正文 {K1}"), K1), "激活后旧内容命中必须为 0"
    assert deps.tree.list_purge(10) == [] and deps.vectors.delete_doc_everywhere(PID, S, live.doc_id) == 0


def test_TC_INT_R25_051_worker_cycle_promotes_ready_revision_after_activation(deps, monkeypatch):
    """[TC-INT-R25-051] MOD-011 / ADR-007：激活时补晋升失败（best-effort）不影响切换；worker 下一轮 `promote_ready_revisions` 完成晋升（成对：失败 → 未晋升；恢复 → 晋升）。"""
    live = put_file(deps, "共存2.txt", f"补晋升测试 {K1}")
    _start_rebuild_and_reindex(deps)
    res = update_file(deps, live.doc_id, "共存2.txt", f"补晋升测试 {K2}")
    deps.lifecycle.process_pending("w", 10)
    def boom(*a, **k):
        raise RuntimeError("promote failed")

    monkeypatch.setattr(deps.rebuild, "_revision_promoter", boom)  # 装配期已绑定的补晋升钩子
    deps.rebuild.activate_version(PID, "2")  # 钩子失败被吞，切换成功
    assert deps.ledger.active_collection_version(PID) == "2"
    assert get_doc(deps, live.doc_id) is not None, "补晋升失败：存活行仍在，旧版内容仍可见"
    assert deps.lifecycle.promote_ready_revisions(PID) == 1  # worker 下一轮的同一入口
    assert get_doc(deps, live.doc_id) is None and get_doc(deps, res.revision.doc_id).revision_of is None
    assert hits_containing(search(deps, f"补晋升测试 {K2}"), K2) and not hits_containing(search(deps, f"补晋升测试 {K1}"), K1)


def test_TC_INT_R25_052_failed_update_does_not_block_activation_but_failed_document_does(deps, monkeypatch):
    """[TC-INT-R25-052] MOD-008：失败计数排除修订行 —— 更新失败不挡住版本切换；成对：普通文档失败仍拒绝切换（AC-IB-16-04 基线口径不变）。"""
    from ib.core import ConflictError

    live = put_file(deps, "共存3.txt", f"失败不阻塞 {K1}")
    _start_rebuild_and_reindex(deps)
    update_file(deps, live.doc_id, "共存3.txt", f"失败不阻塞 {K2}")
    real = deps.lifecycle._embedder
    monkeypatch.setattr(deps.lifecycle, "_embedder", FailingEmbedder(real))
    deps.lifecycle.process_pending("w", 10)  # 修订行失败
    bad = put_file(deps, "bad.txt", "普通文档 将失败", process=True)  # 普通文档失败
    assert get_doc(deps, bad.doc_id).status == "failed"
    with pytest.raises(ConflictError):
        deps.rebuild.activate_version(PID, "2")
    assert deps.ledger.active_collection_version(PID) == "1"
    deps.lifecycle.delete_document(S, bad.doc_id)  # 只剩失败的修订行
    deps.rebuild.activate_version(PID, "2")
    assert deps.ledger.active_collection_version(PID) == "2", "失败的修订行不应阻塞切换"
    assert get_doc(deps, live.doc_id) is not None and get_doc(deps, live.doc_id).status == "indexed"
    monkeypatch.setattr(deps.lifecycle, "_embedder", real)
    assert hits_containing(search(deps, f"失败不阻塞 {K1}"), K1), "旧版在切换后仍可检索"


def test_TC_INT_R25_053_delete_and_rename_during_rebuild_leave_no_stale_hits(deps):
    """[TC-INT-R25-053] REQ-NFUNC-004 / AC-006-02：重建在途时删除文件 —— 跨版本清理向量，检索命中 0；重命名仅改台账，激活后引用名称为新名；重建不改变目录结构与上传时间。"""
    d = deps.library.create_folder(S, "", "目录").folder_id
    gone = put_file(deps, "删我.txt", "重建期间被删的专属内容 乙", folder_id=d)
    keep = put_file(deps, "改名.txt", "重建期间被改名的专属内容 丙", folder_id=d)
    t_up = get_doc(deps, keep.doc_id).uploaded_at
    _start_rebuild_and_reindex(deps)
    deps.lifecycle.delete_document(S, gone.doc_id)
    deps.library.rename_file(S, keep.doc_id, "改名后.txt")
    assert not [h for h in search(deps, "重建期间被删的专属内容 乙").hits if h.doc_id == gone.doc_id]
    deps.rebuild.activate_version(PID, "2")
    assert deps.vectors.delete_doc_everywhere(PID, S, gone.doc_id) == 0, "两个版本集合里都不应残留"
    res = search(deps, "重建期间被改名的专属内容 丙")
    top = [h for h in res.hits if h.doc_id == keep.doc_id]
    assert top and (top[0].doc_name, top[0].doc_path) == ("改名后.txt", "目录/改名后.txt")
    rec = get_doc(deps, keep.doc_id)
    assert rec.folder_id == d and rec.uploaded_at == t_up and rec.content_updated_at is None


def test_TC_INT_R25_054_AC_009_04_rebuild_refreshes_indexed_time_not_upload_or_update_time(deps, monkeypatch):
    """[TC-INT-R25-054] AC-009-04：重建重新索引完成于 T5 → 索引成功时间 = T5（不再是 T2），上传时间 T1 与最近更新时间（“—”）不变，状态 indexed，目录位置不变；激活后保持。"""
    clock = install_clock(monkeypatch)
    d = deps.library.create_folder(S, "", "D").folder_id
    rec = put_file(deps, "t.txt", f"索引时间刷新 {K1}", folder_id=d)
    v1 = get_doc(deps, rec.doc_id)
    t1, t2 = v1.uploaded_at, v1.indexed_at
    clock.tick(7200)
    _start_rebuild_and_reindex(deps, finish=True)
    deps.rebuild.activate_version(PID, "2")
    v2 = get_doc(deps, rec.doc_id)
    assert v2.indexed_at == "2026-03-01T02:00:00Z" and v2.indexed_at != t2
    assert (v2.uploaded_at, v2.content_updated_at, v2.status, v2.folder_id) == (t1, None, "indexed", d)


@pytest.fixture(params=["memory", "sqlite"])
def xdeps(request, raw, tmp_path, monkeypatch):
    """重建共存 succeeded 窗口用例的两后端装配（内存替身 / 真实 SQLite 台账）。"""
    from ibweb.composition import build_deps

    if request.param == "memory":
        return build_deps(raw, force=True)
    return sqlite_deps(tmp_path, raw, monkeypatch)


def test_TC_INT_R25_055_DEF_R25_001_update_after_rebuild_succeeded_before_activation_keeps_file_searchable(xdeps):
    """[TC-INT-R25-055] 缺陷回归（DEF-R25-001 已修复，REQ-NFUNC-004 / REQ-NFUNC-001 / AC-008-02；由 GUARD 冻结翻转为正向断言）：
    重建任务已 `succeeded`（全部文档已重建到 v2）但尚未激活时更新文件 ——
    修订行写入 v2（indexed_collection_version == "2"），revision_of 仍指向存活行，晋升被推迟；
    激活 v2 后：新内容命中（new_hits 非空）、旧内容命中 0（old_hits == []）、view.searchable is True、列表中仅一条该文件记录。
    内存 / SQLite 两后端参数化。"""
    deps = xdeps
    live = put_file(deps, "窗口.txt", f"窗口测试正文 {K1}")
    _start_rebuild_and_reindex(deps, finish=True)
    assert [str(j.state) for j in deps.ledger.list_rebuild_jobs(PID)] == ["succeeded"]
    res = update_file(deps, live.doc_id, "窗口.txt", f"窗口测试正文 {K2}")
    deps.lifecycle.process_pending("w", 10)
    rev = get_doc(deps, res.revision.doc_id)
    assert rev.indexed_collection_version == "2", "修订行应写入重建目标版本 v2"
    assert rev.status == "indexed" and rev.revision_of == live.doc_id, "revision_of 仍指向存活行（晋升被推迟）"
    assert get_doc(deps, live.doc_id) is not None, "存活行仍在，未被立即晋升"
    # 激活前读路径仍读 v1：旧内容仍可检索
    assert hits_containing(search(deps, f"窗口测试正文 {K1}"), K1)
    deps.rebuild.activate_version(PID, "2")
    assert deps.ledger.active_collection_version(PID) == "2"
    old_hits = hits_containing(search(deps, f"窗口测试正文 {K1}"), K1)
    new_hits = hits_containing(search(deps, f"窗口测试正文 {K2}"), K2)
    assert new_hits, "激活后新内容必须可检索"
    assert old_hits == [], "激活后旧内容命中必须为 0"
    page = deps.library.browse(S, "", page=1, page_size=50)
    assert len(page.files) == 1 and page.total == 1, "列表中只有一条该文件记录"
    view = page.files[0]
    assert view.record.doc_name == "窗口.txt" and view.record.doc_id == res.revision.doc_id and view.record.revision_of is None
    assert view.record.status == "indexed" and view.searchable is True
    assert get_doc(deps, live.doc_id) is None
    assert deps.vectors.delete_doc_everywhere(PID, S, live.doc_id) == 0, "旧文档向量在两个版本集合中均已清理"


def test_TC_INT_R25_056_new_upload_in_succeeded_window_is_searchable_after_activation(xdeps):
    """[TC-INT-R25-056] 与 055 成对（REQ-NFUNC-004 / AC-010-01）：重建 succeeded、未激活窗口内的**普通新上传**，激活后可检索（命中 > 0）、状态 indexed、searchable True。
    注：该窗口内新上传激活后丢失属基线（HEAD 65490cf）既有缺陷，随 DEF-R25-001 修复一并消除。"""
    deps = xdeps
    put_file(deps, "前.txt", f"窗口前文件 {K1}")
    _start_rebuild_and_reindex(deps, finish=True)
    assert [str(j.state) for j in deps.ledger.list_rebuild_jobs(PID)] == ["succeeded"]
    fresh = put_file(deps, "窗口新传.txt", "窗口内新上传专属内容 戊己")
    assert get_doc(deps, fresh.doc_id).status == "indexed"
    assert get_doc(deps, fresh.doc_id).indexed_collection_version == "2", "新上传应写入目标版本 v2"
    deps.rebuild.activate_version(PID, "2")
    hits = [h for h in search(deps, "窗口内新上传专属内容 戊己").hits if h.doc_id == fresh.doc_id]
    assert hits, "激活后窗口内新上传的文件必须可检索"
    names = {v.record.doc_name: v for v in deps.library.browse(S, "", page=1, page_size=50).files}
    assert set(names) == {"前.txt", "窗口新传.txt"} and names["窗口新传.txt"].searchable is True
    assert hits_containing(search(deps, f"窗口前文件 {K1}"), K1), "窗口前的文件同样可检索（成对）"


def _other_version_plan(deps, to_version: str):
    import dataclasses

    plan = deps.rebuild.plan_rebuild(PID)
    return dataclasses.replace(plan, to_version=to_version, target_collection=f"ib_{PID}_v{to_version}")


def test_TC_INT_R25_057_start_different_target_while_succeeded_unactivated_conflicts(xdeps):
    """[TC-INT-R25-057] GR-C-002-F01 行为变更：存在 succeeded 未激活任务时，启动**不同目标版本**的新重建 → ConflictError（HTTP 映射 409）；
    不新增任务行、不新建目标集合。"""
    from ib.core import ConflictError
    from ibweb.views import error_response

    deps = xdeps
    put_file(deps, "冲突.txt", f"冲突测试 {K1}")
    job = _start_rebuild_and_reindex(deps, finish=True)
    assert [str(j.state) for j in deps.ledger.list_rebuild_jobs(PID)] == ["succeeded"]
    other = _other_version_plan(deps, "3")
    with pytest.raises(ConflictError) as ei:
        deps.rebuild.start_rebuild(PID, other)
    assert error_response(ei.value).status_code == 409
    jobs = deps.ledger.list_rebuild_jobs(PID)
    assert [(j.job_id, j.to_version, str(j.state)) for j in jobs] == [(job.job_id, "2", "succeeded")]
    assert deps.ledger.find_rebuild_job(PID, "3") is None


def test_TC_INT_R25_058_start_new_rebuild_after_activation_succeeds(xdeps):
    """[TC-INT-R25-058] GR-C-002-F01 成对：激活 v2 后再启动下一版本（v3）重建 → 成功，新任务行存在且为非终态。"""
    deps = xdeps
    put_file(deps, "激活后.txt", f"激活后重建 {K1}")
    _start_rebuild_and_reindex(deps, finish=True)
    deps.rebuild.activate_version(PID, "2")
    plan = deps.rebuild.plan_rebuild(PID)
    assert (plan.from_version, plan.to_version) == ("2", "3")
    job3 = deps.rebuild.start_rebuild(PID, plan)
    row = deps.ledger.find_rebuild_job(PID, "3")
    assert row is not None and row.job_id == job3.job_id and str(row.state) in ("planned", "running")


def test_TC_INT_R25_059_start_same_target_again_is_idempotent_in_succeeded_window(xdeps):
    """[TC-INT-R25-059] GR-C-002-F01 / IFC-IB-152 §6.2：succeeded 未激活窗口内，同目标版本重复启动 → 幂等返回同一任务（job_id 相同、状态 succeeded），任务行不增加。"""
    deps = xdeps
    put_file(deps, "幂等.txt", f"幂等测试 {K1}")
    job = _start_rebuild_and_reindex(deps, finish=True)
    again = deps.rebuild.start_rebuild(PID, deps.rebuild.plan_rebuild(PID))
    assert again.job_id == job.job_id and str(again.state) == "succeeded"
    assert len(deps.ledger.list_rebuild_jobs(PID)) == 1
