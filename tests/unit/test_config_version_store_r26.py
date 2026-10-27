"""[REV-26 / GROUP_D] MOD-R26-06 版本存储（SQLite 与内存替身同一套语义）：begin / commit / abort / claim_stale / 修剪 / 草稿 / 评审缓存。

溯源：US-014（AC-014-03 失败保留旧版）、US-017（AC-017-01/02/04 版本列表、回滚基础、保留 50）、US-018（AC-018-01 CAS 陈旧基线）、
US-020（AC-020-03 / A07 升级前基线 v1）、US-023（AC-023-01 审计与发布同事务，REQ-NFUNC-006）、US-018（AC-018-03 草稿副本）。
层级：单元（单模块；SQLite 用 pytest tmp_path 临时文件，无外部依赖）。
"""

from __future__ import annotations

import pytest
from config_r26_support import expert, make_v2_document

from ib.config.versioning import build_snapshot, manifest_hash
from ib.core import (
    ConfigAuditEntry,
    ConflictError,
    DependencyUnavailableError,
    NewVersion,
    PromptLayers,
    ValidationError,
)
from ib.ledger.config_audit import MemoryConfigAuditStore, SqliteConfigAuditStore
from ib.ledger.config_versions import (
    MemoryBuilderEvalCache,
    MemoryConfigDraftStore,
    MemoryConfigVersionStore,
    SqliteBuilderEvalCache,
    SqliteConfigDraftStore,
    SqliteConfigVersionStore,
)

NOW = "2026-10-27T00:00:00Z"
LATER = "2026-10-27T00:10:00Z"


def _snap(max_steps=None):
    ex = (expert("a", default=True, max_steps=max_steps), expert("b"))
    return build_snapshot(make_v2_document("p", ex), {e.name: PromptLayers(f"{e.name} 提示词", None) for e in ex})


def _nv(snap, kind="publish", actor="u1", summary="s", rolled=None):
    return NewVersion(kind, actor, summary, rolled, manifest_hash(snap))


def _audit(action="config.publish", before=0, after=1, result="saved"):
    return ConfigAuditEntry(
        timestamp=NOW, project="p", actor="u1", action=action, changed_field_names=("agent",), result=result,  # type: ignore[arg-type]
        detail_code=None, version_before=before, version_after=after, object_summary=("agent:a",),
    )


@pytest.fixture(params=["sqlite", "memory"])
def env(request, tmp_path):
    """(store, audit_store)：两种实现跑同一套断言。"""
    if request.param == "sqlite":
        path = str(tmp_path / "ledger.db")
        store = SqliteConfigVersionStore(path)
        audit = SqliteConfigAuditStore(path)
        yield store, audit
        store.close()
        audit.close()
    else:
        audit = MemoryConfigAuditStore()
        yield MemoryConfigVersionStore(audit_sink=audit), audit


def _publish(store, snap, base, *, audit=None, now=NOW, baseline=None, keep=50, **nvkw):
    res = store.begin_publish("p", base_version=base, new=_nv(snap, **nvkw), snapshot=snap,
                              extra_baseline=baseline, now=now, stale_after_s=30.0)
    assert res.outcome == "ok", res
    store.commit_publish("p", res.version, now=now, keep=keep, audit=audit)
    return res


def test_TC_UNIT_R26_100_virtual_head_then_publish_roundtrip(env):
    """US-017 / AC-017-01：无版本行时 head=0（虚拟版本）；发布后 head 前进，列表含版本号/保存人/时间/摘要。"""
    store, _ = env
    assert store.head("p").published_version == 0 and store.head("p").pending_version is None
    s = _snap()
    r = _publish(store, s, 0, summary="新增 agent a")
    assert r.version == 1 and store.head("p").published_version == 1
    rec, got = store.get_version("p", 1)
    assert (rec.actor, rec.summary, rec.status, rec.kind, rec.created_at) == ("u1", "新增 agent a", "published", "publish", NOW)
    assert manifest_hash(got) == manifest_hash(s)
    assert [x.version for x in store.list_versions("p", limit=10, before_version=None)] == [1]


def test_TC_UNIT_R26_101_cas_stale_base_rejected_and_head_unchanged(env):
    """US-018 / AC-018-01：基于陈旧版本的发布 → stale_base，回执当前 head；head 不变，甲的版本未被覆盖。"""
    store, _ = env
    _publish(store, _snap(), 0)                # 甲：v1
    res = store.begin_publish("p", base_version=0, new=_nv(_snap(2)), snapshot=_snap(2),
                              extra_baseline=None, now=NOW, stale_after_s=30.0)  # 乙仍基于 0
    assert res.outcome == "stale_base" and res.head_version == 1 and res.version is None
    assert store.head("p").published_version == 1 and store.head("p").pending_version is None


def test_TC_UNIT_R26_102_pending_blocks_second_begin_busy(env):
    """US-018：存在 pending 时第二次 begin 回 busy（单飞串行点），不产生第二个 pending。"""
    store, _ = env
    s = _snap()
    first = store.begin_publish("p", base_version=0, new=_nv(s), snapshot=s, extra_baseline=None, now=NOW, stale_after_s=30.0)
    again = store.begin_publish("p", base_version=0, new=_nv(s), snapshot=s, extra_baseline=None, now=NOW, stale_after_s=30.0)
    assert first.outcome == "ok" and again.outcome == "busy" and again.pending_version == first.version
    assert store.get_version("p", first.version) is None, "pending 版本对读路径不可见（只有 published 可读）"


def test_TC_UNIT_R26_103_v1_project_first_publish_stores_baseline_then_user_version(env):
    """US-020 / AC-020-03、A07：虚拟 head=0 时首次发布同事务先存“升级前基线”v1 再存用户 v2。"""
    store, _ = env
    base_snap, user_snap = _snap(), _snap(3)
    res = store.begin_publish("p", base_version=0, new=_nv(user_snap), snapshot=user_snap,
                              extra_baseline=base_snap, now=NOW, stale_after_s=30.0)
    assert res.outcome == "ok" and res.version == 2
    store.commit_publish("p", 2, now=NOW, keep=50)
    v1, snap1 = store.get_version("p", 1)
    assert (v1.kind, v1.actor, v1.parent_version) == ("baseline", "system", 0)
    assert manifest_hash(snap1) == manifest_hash(base_snap)
    v2, _ = store.get_version("p", 2)
    assert v2.parent_version == 1 and store.head("p").published_version == 2
    # 再次发布不会重复写基线
    r3 = store.begin_publish("p", base_version=2, new=_nv(base_snap), snapshot=base_snap,
                             extra_baseline=base_snap, now=NOW, stale_after_s=30.0)
    assert r3.version == 3


def test_TC_UNIT_R26_104_abort_clears_pending_keeps_head_and_hides_version(env):
    """US-014 / AC-014-03：应用失败 abort → pending 清除、head 仍为旧版、该版本不可读/不入列表。"""
    store, _ = env
    _publish(store, _snap(), 0)
    s2 = _snap(2)
    res = store.begin_publish("p", base_version=1, new=_nv(s2), snapshot=s2, extra_baseline=None, now=NOW, stale_after_s=30.0)
    assert store.abort_publish("p", res.version, reason_code="apply_failed", now=LATER) is True
    h = store.head("p")
    assert (h.published_version, h.pending_version) == (1, None)
    assert store.get_version("p", res.version) is None
    assert [x.version for x in store.list_versions("p", limit=10, before_version=None)] == [1]
    # abort 后可继续发布，且版本号单调不复用
    nxt = store.begin_publish("p", base_version=1, new=_nv(s2), snapshot=s2, extra_baseline=None, now=LATER, stale_after_s=30.0)
    assert nxt.outcome == "ok" and nxt.version == res.version + 1


def test_TC_UNIT_R26_105_claim_stale_pending_only_after_threshold_and_only_once(env):
    """CR-002：陈旧 pending 才可被认领（CAS 只一个调用方成功）；未陈旧返回 None。"""
    store, _ = env
    s = _snap()
    res = store.begin_publish("p", base_version=0, new=_nv(s), snapshot=s, extra_baseline=None, now=NOW, stale_after_s=30.0)
    assert store.claim_stale_pending("p", now="2026-10-27T00:00:10Z", stale_after_s=30.0) is None
    assert store.claim_stale_pending("p", now=LATER, stale_after_s=30.0) == res.version
    assert store.claim_stale_pending("p", now=LATER, stale_after_s=30.0) is None  # 已被认领
    assert store.abort_publish("p", res.version, reason_code="recovered", now=LATER) is True
    assert store.head("p").pending_version is None


def test_TC_UNIT_R26_106_retention_keeps_latest_50_plus_head(env):
    """US-017 / AC-017-04：保留最近 50 个版本；第 51 个提交后最旧的不再可回滚，其余 50 个仍可读。"""
    store, _ = env
    base = 0
    for i in range(51):
        base = _publish(store, _snap(1 + (i % 8)), base, keep=50, summary=f"v{i + 1}").version
    versions = [x.version for x in store.list_versions("p", limit=500, before_version=None)]
    assert len(versions) == 50 and versions[0] == 51 and versions[-1] == 2
    assert store.get_version("p", 1) is None and store.get_version("p", 2) is not None


def test_TC_UNIT_R26_107_prune_all_keeps_head_even_when_keep_is_one(env):
    """worker 维护：prune_all(keep=1) 仍保留 head；返回被删数量。"""
    store, _ = env
    base = 0
    for i in range(4):
        base = _publish(store, _snap(1 + i), base, keep=50).version
    removed = store.prune_all(keep=1)
    assert removed == 3 and store.head("p").published_version == 4
    assert store.get_version("p", 4) is not None


def test_TC_UNIT_R26_108_audit_commits_atomically_with_publish(env):
    """US-023 / AC-023-01、REQ-NFUNC-006：审计行与“置 published/更新 head”同事务；提交后审计与版本同时可见。"""
    store, audit = env
    _publish(store, _snap(), 0, audit=_audit(before=0, after=1))
    rows = audit.list_by_project("p", limit=10)
    assert len(rows) == 1
    r = rows[0]
    assert (r.action, r.result, r.version_before, r.version_after, r.object_summary) == (
        "config.publish", "saved", 0, 1, ("agent:a",))
    assert store.head("p").published_version == 1


def test_TC_UNIT_R26_109_audit_failure_means_publish_does_not_take_effect(env):
    """REQ-NFUNC-006 / CR-009：审计写失败 → 提交整体失败：版本仍为 pending、head 未前进、无审计行。"""
    store, audit = env
    s = _snap()
    res = store.begin_publish("p", base_version=0, new=_nv(s), snapshot=s, extra_baseline=None, now=NOW, stale_after_s=30.0)
    bad = _audit(result="BOGUS")  # SQLite CHECK(result IN (saved, rejected)) 拒绝；内存 sink 同样拒绝
    if isinstance(store, MemoryConfigVersionStore):
        class _Boom:
            def record(self, entry):
                raise RuntimeError("audit down")

        store._audit_sink = _Boom()
        bad = _audit()
    with pytest.raises(Exception):
        store.commit_publish("p", res.version, now=NOW, keep=50, audit=bad)
    h = store.head("p")
    assert h.published_version == 0 and h.pending_version == res.version
    assert store.get_version("p", res.version) is None
    assert audit.list_by_project("p", limit=10) == ()


def test_TC_UNIT_R26_110_memory_store_without_audit_sink_refuses_audited_commit():
    """内存替身无审计后端时拒绝带审计的提交（fail-closed）。"""
    store = MemoryConfigVersionStore()
    s = _snap()
    res = store.begin_publish("p", base_version=0, new=_nv(s), snapshot=s, extra_baseline=None, now=NOW, stale_after_s=30.0)
    with pytest.raises(DependencyUnavailableError):
        store.commit_publish("p", res.version, now=NOW, keep=50, audit=_audit())
    assert store.head("p").published_version == 0


def test_TC_UNIT_R26_111_commit_requires_pending_status(env):
    """重复提交 / 提交不存在的版本 → ConflictError，不改变 head。"""
    store, _ = env
    _publish(store, _snap(), 0)
    with pytest.raises(ConflictError):
        store.commit_publish("p", 1, now=NOW, keep=50)
    with pytest.raises(ConflictError):
        store.commit_publish("p", 99, now=NOW, keep=50)
    assert store.head("p").published_version == 1


def test_TC_UNIT_R26_112_versions_are_isolated_per_project(env):
    """AC-019-01 / AC-010-04：版本读取按 project_id 隔离，不可用别的项目的版本号读到内容。"""
    store, _ = env
    _publish(store, _snap(), 0)
    assert store.get_version("other", 1) is None
    assert store.list_versions("other", limit=10, before_version=None) == ()
    assert store.head("other").published_version == 0


def test_TC_UNIT_R26_113_list_versions_pagination_before_cursor(env):
    """AC-017-01：版本历史按版本号倒序，before 游标翻页。"""
    store, _ = env
    base = 0
    for i in range(5):
        base = _publish(store, _snap(1 + i), base).version
    page1 = store.list_versions("p", limit=2, before_version=None)
    page2 = store.list_versions("p", limit=2, before_version=page1[-1].version)
    assert [v.version for v in page1] == [5, 4] and [v.version for v in page2] == [3, 2]


@pytest.fixture(params=["sqlite", "memory"])
def drafts(request, tmp_path):
    if request.param == "sqlite":
        s = SqliteConfigDraftStore(str(tmp_path / "d.db"))
        yield s
        s.close()
    else:
        yield MemoryConfigDraftStore()


def test_TC_UNIT_R26_114_drafts_owner_isolation_quota_and_size(drafts):
    """US-018 / AC-018-03：草稿副本仅本人可读（他人读取 = 不存在）；每人每项目 ≤N；单个 ≤1 MiB；名称 1..60。"""
    rec = drafts.save("p", "u1", label="我的副本", base_version=3, payload_json='{"x":1}', now=NOW, max_per_owner=2)
    assert drafts.load("p", "u1", rec.draft_id)[1] == '{"x":1}'
    assert drafts.load("p", "u2", rec.draft_id) is None, "他人草稿与不存在同形"
    assert drafts.load("other", "u1", rec.draft_id) is None
    assert drafts.list("p", "u2") == ()
    drafts.save("p", "u1", label="第二个", base_version=3, payload_json="{}", now=NOW, max_per_owner=2)
    with pytest.raises(ValidationError) as q:
        drafts.save("p", "u1", label="第三个", base_version=3, payload_json="{}", now=NOW, max_per_owner=2)
    assert q.value.field == "draft_quota"
    with pytest.raises(ValidationError):
        drafts.save("p", "u3", label="x", base_version=0, payload_json="y" * (1024 * 1024 + 1), now=NOW, max_per_owner=2)
    with pytest.raises(ValidationError):
        drafts.save("p", "u3", label="  ", base_version=0, payload_json="{}", now=NOW, max_per_owner=2)
    with pytest.raises(ValidationError):
        drafts.save("p", "u3", label="n" * 61, base_version=0, payload_json="{}", now=NOW, max_per_owner=2)
    assert drafts.delete("p", "u2", rec.draft_id) is False
    assert drafts.delete("p", "u1", rec.draft_id) is True


def test_TC_UNIT_R26_115_drafts_purge_older_than(drafts):
    """worker 维护：过期草稿清理按 created_at 截止。"""
    drafts.save("p", "u1", label="old", base_version=0, payload_json="{}", now="2026-01-01T00:00:00Z", max_per_owner=5)
    drafts.save("p", "u1", label="new", base_version=0, payload_json="{}", now=NOW, max_per_owner=5)
    assert drafts.purge_older_than("2026-06-01T00:00:00Z") == 1
    assert [d.label for d in drafts.list("p", "u1")] == ["new"]


@pytest.fixture(params=["sqlite", "memory"])
def eval_cache(request, tmp_path):
    if request.param == "sqlite":
        c = SqliteBuilderEvalCache(str(tmp_path / "e.db"))
        yield c
        c.close()
    else:
        yield MemoryBuilderEvalCache()


def test_TC_UNIT_R26_116_eval_cache_first_writer_wins_and_purge(eval_cache):
    """A04：评审缓存“先写者赢”（缓存期内同输入同结果）；purge 按 keep / 截止时间清理。"""
    eval_cache.put("k1", rubric_version="r26.1", result_json='{"a":1}', now=NOW)
    eval_cache.put("k1", rubric_version="r26.1", result_json='{"a":2}', now=LATER)
    assert eval_cache.get("k1") == '{"a":1}'
    assert eval_cache.get("missing") is None
    eval_cache.put("k2", rubric_version="r26.1", result_json="{}", now="2026-01-01T00:00:00Z")
    assert eval_cache.purge(keep=100, older_than_iso="2026-06-01T00:00:00Z") >= 1
    assert eval_cache.get("k2") is None and eval_cache.get("k1") is not None
