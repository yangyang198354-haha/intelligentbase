"""[REV-26 / GROUP_D] MOD-R26-13 发布协议（ADR-55）：预览 / 发布 / 冲突 / 回滚 / 采纳漂移 / 崩溃恢复。

溯源：US-014（AC-014-03）、US-016（AC-016-02/03）、US-017（AC-017-02）、US-018（AC-018-01）、US-020（AC-020-03 / A07）、
US-023（AC-023-01/02 审计）、US-013（AC-013-01 校验失败在用版本不变）、REQ-NFUNC-006（审计与发布同事务，CR-009）、CR-002。
层级：单元（单模块；文件/编译/审计均为注入的替身，故障点可逐步注入）。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from config_r26_support import SEARCH, error_codes, expert, make_v2_document

from ib.config.versioning import build_snapshot, manifest_hash
from ib.confsvc import ConfigPublishService, PublishError, PublishRequest
from ib.core import PromptLayers, ValidationErrorItem
from ib.ledger.config_audit import MemoryConfigAuditStore
from ib.ledger.config_versions import MemoryConfigVersionStore

PID = "p"


class Files:
    """文件态替身：定义文档 + 提示词层；记录写入顺序，可在指定步骤注入故障。"""

    def __init__(self, doc, prompts):
        self.doc, self.prompts, self.log = doc, dict(prompts), []
        self.fail_on = None  # ("prompt", name, layer) | ("definition",)

    # loader
    def load_files(self, project_id):
        return build_snapshot(self.doc, self.prompts)

    def load_layers(self, project_id, names):
        return {n: self.prompts.get(n, PromptLayers(None, None)) for n in names}

    # definition store
    def save(self, project_id, doc, expected_content_hash=None):
        self.log.append("definition")
        if self.fail_on == ("definition",):
            self.fail_on = None  # 一次性故障：随后的还原写入必须成功
            raise OSError("disk full (simulated)")
        self.doc = doc
        return SimpleNamespace(ok=True)

    # prompt store
    def save_layer(self, name, layer, text, expected_hash=None):
        self.log.append(f"prompt:{name}:{layer}")
        if self.fail_on == ("prompt", name, layer):
            self.fail_on = None  # 一次性故障
            raise OSError("disk full (simulated)")
        cur = self.prompts.get(name, PromptLayers(None, None))
        self.prompts[name] = PromptLayers(text if layer == "main" else cur.main, text if layer == "fallback" else cur.fallback)
        return SimpleNamespace(saved=True)

    def delete_layer(self, name, layer):
        self.log.append(f"delete:{name}:{layer}")
        cur = self.prompts.get(name, PromptLayers(None, None))
        self.prompts[name] = PromptLayers(None if layer == "main" else cur.main, None if layer == "fallback" else cur.fallback)
        if self.prompts[name] == PromptLayers(None, None):
            del self.prompts[name]


def make_env(*, validator=None, precompile=None, on_published=None):
    ex = (expert("a", default=True), expert("b"))
    doc = make_v2_document(PID, ex)
    files = Files(doc, {"a": PromptLayers("a 主", None), "b": PromptLayers("b 主", None)})
    audit = MemoryConfigAuditStore()
    store = MemoryConfigVersionStore(audit_sink=audit)
    calls = SimpleNamespace(precompiled=[], published=[])

    def _pre(pid, ver, snap):
        calls.precompiled.append(ver)
        return ("compiled", ver)

    def _on(pid, ver, compiled):
        calls.published.append((ver, compiled))

    clock = iter(f"2026-10-27T00:00:{i:02d}Z" for i in range(1, 60))
    svc = ConfigPublishService(
        versions=store, definition_store=files, prompt_store_for=lambda pid: files, loader=files,
        precompile=precompile or _pre, on_published=on_published or _on, audit=audit,
        validator=validator or (lambda snap: ()), clock=lambda: next(clock), keep_versions=50, pending_stale_s=30.0,
    )
    return svc, files, store, audit, calls


def _req(files, base=0, *, experts=None, prompts=None, doc=None, message=None):
    if doc is None:
        ex = experts or files.doc.experts
        doc = make_v2_document(PID, ex)
    return PublishRequest(project_id=PID, actor="u1", base_version=base, document=doc, prompts=prompts or {}, message=message)


def _changed(files, max_steps=3):
    return make_v2_document(PID, (expert("a", default=True, max_steps=max_steps), expert("b")))


def test_TC_UNIT_R26_120_v1_first_publish_writes_baseline_and_user_version_with_audit():
    """US-020 / AC-020-03、A07、AC-023-01：首次发布 → v1(baseline)+v2；审计含 前0→后2、对象清单、结果 saved；on_published 收到编译产物。"""
    svc, files, store, audit, calls = make_env()
    res = svc.publish(_req(files, 0, doc=_changed(files)))
    assert (res.version, res.previous_version) == (2, 1)
    assert store.get_version(PID, 1)[0].kind == "baseline"
    assert store.head(PID).published_version == 2
    rows = audit.list_by_project(PID, limit=10)
    # 审计的“前”= 发布前的在用版本（虚拟 0，基线 v1 是同事务的内部落点），“后”= 用户版本 2
    assert len(rows) == 1 and (rows[0].action, rows[0].result, rows[0].version_before, rows[0].version_after) == ("config.publish", "saved", 0, 2)
    assert any(o.startswith("agent_field:a") for o in rows[0].object_summary)
    assert calls.precompiled == [2] and calls.published == [(2, ("compiled", 2))]
    assert files.doc.experts[0].max_steps == 3, "文件态已同步为新文档"


def test_TC_UNIT_R26_121_prompts_written_before_definition_document():
    """ADR-55：先写提示词层，定义文档最后写（崩溃窗口内文档不会指向缺失的提示词）。"""
    svc, files, *_ = make_env()
    new_doc = make_v2_document(PID, (expert("a", default=True), expert("b"), expert("c")),
                               grants={"a": (SEARCH,), "b": (SEARCH,), "c": (SEARCH,)})
    svc.publish(_req(files, 0, doc=new_doc, prompts={"c": PromptLayers("c 主", None)}))
    assert files.log.index("prompt:c:main") < files.log.index("definition")
    assert files.log[-1] == "definition"


def test_TC_UNIT_R26_122_stale_base_conflict_has_receipt_and_rejected_audit():
    """US-018 / AC-018-01、AC-023-02：基于陈旧版本 → conflict 回执（含冲突对象清单、版本号），在用版本不变，写 rejected 审计。"""
    svc, files, store, audit, _ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))                         # 甲：v2 (a.max_steps=2)
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, doc=_changed(files, 5)))                      # 乙：仍基于 0
    err = ei.value
    assert err.code == "conflict" and err.receipt is not None
    assert (err.receipt.base_version, err.receipt.head_version) == (0, 2)
    assert store.head(PID).published_version == 2
    assert files.doc.experts[0].max_steps == 2, "甲的改动未被覆盖"
    rej = [r for r in audit.list_by_project(PID, limit=10) if r.result == "rejected"]
    assert rej and rej[-1].detail_code == "conflict"


def test_TC_UNIT_R26_123_validation_failure_keeps_version_and_audits_codes_only():
    """US-013 / AC-013-01、AC-023-02：校验失败 → validation_error(带逐条 items)，不占 pending，审计 rejected 只含错误码。"""
    bad = ValidationErrorItem("graph", "graph_cycle", "图中存在环：a, b")
    svc, files, store, audit, calls = make_env(validator=lambda snap: (bad,))
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, doc=_changed(files)))
    assert ei.value.code == "validation_error" and error_codes(ei.value.items) == ["graph_cycle"]
    assert store.head(PID).published_version == 0 and store.head(PID).pending_version is None
    assert calls.precompiled == [] and files.log == []
    row = audit.list_by_project(PID, limit=10)[-1]
    assert row.result == "rejected" and "graph_cycle" in (row.detail_code or "")
    assert "a, b" not in str(row), "审计不含错误消息正文"


def test_TC_UNIT_R26_124_prompt_text_validation_runs_in_publish_path():
    """US-019 / AC-019-04：提示词 >20000 字符在发布路径被拒（与保存同入口），在用配置不变。"""
    svc, files, store, *_ = make_env()
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, prompts={"a": PromptLayers("x" * 20001, None)}))
    assert "prompt_too_long" in error_codes(ei.value.items)
    assert store.head(PID).published_version == 0 and files.prompts["a"].main == "a 主"


def test_TC_UNIT_R26_125_no_changes_creates_no_version():
    """US-016 / AC-016-03：无任何改动 → no_changes，不产生新版本。"""
    svc, files, store, *_ = make_env()
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, doc=files.doc))
    assert ei.value.code == "no_changes" and store.head(PID).published_version == 0


def test_TC_UNIT_R26_126_precompile_failure_nothing_written_and_old_version_serves():
    """US-014 / AC-014-03：新配置编译失败 → apply_failed，尚未写盘、pending 已 abort、在用版本不变。"""
    def boom(pid, ver, snap):
        raise RuntimeError("compile failed (simulated)")

    svc, files, store, audit, calls = make_env(precompile=boom)
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, doc=_changed(files)))
    assert ei.value.code == "apply_failed"
    assert files.log == [] and files.doc.experts[0].max_steps is None
    h = store.head(PID)
    assert h.pending_version is None
    # v1 项目首次保存：升级前基线 v1 与 pending 同事务落点，故 head 前进到基线（内容 == 升级前文件态，行为等价）
    assert h.published_version == 1 and store.get_version(PID, 1)[0].kind == "baseline"
    assert calls.published == []


def _seeded():
    """已发布到 head=2（基线 v1 + 用户 v2）的环境，故障注入用例的“在用版本”因此是确定的 2。"""
    svc, files, store, audit, calls = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))
    calls.published.clear()
    files.log.clear()
    return svc, files, store, audit, calls


@pytest.mark.parametrize("fail_on", [("prompt", "a", "main"), ("definition",)])
def test_TC_UNIT_R26_127_write_failure_restores_files_and_aborts(fail_on):
    """ADR-55：写文件中途失败 → 依升级前快照还原、abort pending、apply_failed，在用版本不变（head 仍为 2）。"""
    svc, files, store, audit, calls = _seeded()
    before = (files.doc, dict(files.prompts))
    files.fail_on = fail_on
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 2, doc=_changed(files, 6), prompts={"a": PromptLayers("新的 a 主提示词", None)}))
    assert ei.value.code == "apply_failed"
    files.fail_on = None
    assert files.doc == before[0] and files.prompts == before[1], "文件态已还原到升级前"
    h = store.head(PID)
    assert (h.published_version, h.pending_version) == (2, None)
    assert calls.published == []
    assert audit.list_by_project(PID, limit=10)[-1].result == "rejected"


def test_TC_UNIT_R26_128_audit_write_failure_means_publish_not_effective():
    """REQ-NFUNC-006 / CR-009（重点验证）：审计写失败 → 发布不生效：文件还原、head 不前进、on_published 未调用。"""
    svc, files, store, audit, calls = _seeded()
    ok_record = audit.record
    state = {"saved": 0}

    def flaky(entry):
        if entry.result == "saved":
            state["saved"] += 1
            raise RuntimeError("audit store down (simulated)")
        ok_record(entry)

    audit.record = flaky  # 注入：成功审计写不进
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 2, doc=_changed(files, 6)))
    assert ei.value.code == "apply_failed" and state["saved"] == 1
    assert store.head(PID).published_version == 2 and store.head(PID).pending_version is None
    assert files.doc.experts[0].max_steps == 2, "文件态已还原为 v2 的内容"
    assert calls.published == []
    assert len([r for r in audit.list_by_project(PID, limit=50) if r.result == "saved"]) == 1, "没有留下“已生效”的审计行"


def test_TC_UNIT_R26_141_first_save_failure_on_v1_project_leaves_equivalent_baseline_head():
    """US-020 / AC-020-03、A07（观察项）：v1 旧项目首次保存在写文件阶段失败 → 文件态还原；
    head 停在“升级前基线 v1”（内容 == 升级前文件态，等价，可回滚/可继续保存），pending 清除。"""
    svc, files, store, audit, calls = make_env()
    pre = manifest_hash(build_snapshot(files.doc, files.prompts))
    files.fail_on = ("definition",)
    with pytest.raises(PublishError):
        svc.publish(_req(files, 0, doc=_changed(files, 6)))
    files.fail_on = None
    h = store.head(PID)
    assert (h.published_version, h.pending_version) == (1, None)
    assert manifest_hash(store.get_version(PID, 1)[1]) == pre == manifest_hash(build_snapshot(files.doc, files.prompts))
    svc.publish(_req(files, 1, doc=_changed(files, 6)))   # 之后可基于基线 v1 继续保存
    assert store.head(PID).published_version == 3


def test_TC_UNIT_R26_129_on_published_failure_does_not_roll_back_commit():
    """ADR-54：换引用回调失败不回滚已提交的发布（运行时缓存的 head 探测会收敛到新版本）。"""
    def boom(pid, ver, compiled):
        raise RuntimeError("install failed")

    svc, files, store, *_ = make_env(on_published=boom)
    res = svc.publish(_req(files, 0, doc=_changed(files)))
    assert store.head(PID).published_version == res.version == 2


def test_TC_UNIT_R26_130_rollback_creates_new_version_with_target_content():
    """US-017 / AC-017-02：当前 v(N+2)，回滚到 N → 新版本 N+3，内容与 N 一致；审计 action=config.rollback；文件态还原。"""
    svc, files, store, audit, _ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))          # v1 baseline, v2
    svc.publish(_req(files, 2, doc=_changed(files, 5)))          # v3
    svc.publish(_req(files, 3, doc=_changed(files, 7)))          # v4
    res = svc.rollback(PID, "mgr", target_version=2, base_version=4, message=None)
    assert res.version == 5 and store.head(PID).published_version == 5
    rec, snap = store.get_version(PID, 5)
    assert (rec.kind, rec.rolled_back_to) == ("rollback", 2)
    assert manifest_hash(snap) == manifest_hash(store.get_version(PID, 2)[1])
    assert files.doc.experts[0].max_steps == 2
    last = audit.list_by_project(PID, limit=50)[-1]
    assert (last.action, last.version_before, last.version_after, last.actor) == ("config.rollback", 4, 5, "mgr")


def test_TC_UNIT_R26_131_rollback_target_missing_or_stale_base():
    """目标版本不存在/已被修剪 → version_not_found；回滚基于陈旧 head → conflict。"""
    svc, files, store, *_ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))
    with pytest.raises(PublishError) as a:
        svc.rollback(PID, "mgr", target_version=99, base_version=2, message=None)
    assert a.value.code == "version_not_found"
    with pytest.raises(PublishError) as b:
        svc.rollback(PID, "mgr", target_version=1, base_version=0, message=None)
    assert b.value.code == "conflict"


def test_TC_UNIT_R26_132_rollback_to_baseline_v1_restores_pre_upgrade_state():
    """A07：回滚到升级前基线 v1，文件态回到升级前文档（允许降级写回，这是回滚的目的）。"""
    svc, files, store, *_ = make_env()
    before = files.doc
    svc.publish(_req(files, 0, doc=_changed(files, 2)))
    svc.rollback(PID, "mgr", target_version=1, base_version=2, message=None)
    assert manifest_hash(build_snapshot(files.doc, files.prompts)) == manifest_hash(store.get_version(PID, 1)[1])
    assert files.doc.content_hash == before.content_hash


def test_TC_UNIT_R26_133_recover_stale_pending_restores_files_from_head_snapshot():
    """CR-002：崩溃遗留的陈旧 pending → recover 认领、依 head 快照还原文件并 abort；之后可正常发布。"""
    svc, files, store, audit, _ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))                    # head=2
    # 模拟崩溃：begin 后写了半截文件就消失
    half = build_snapshot(_changed(files, 8), {"a": PromptLayers("半截", None), "b": PromptLayers("b 主", None)})
    res = store.begin_publish(PID, base_version=2, new=SimpleNamespace(kind="publish", actor="u", summary="half",
                              rolled_back_to=None, manifest_hash=manifest_hash(half)), snapshot=half,
                              extra_baseline=None, now="2026-10-26T00:00:00Z", stale_after_s=30.0)
    files.prompts["a"] = PromptLayers("半截", None)
    assert svc.recover(PID) == res.version
    assert files.prompts["a"].main == "a 主" and files.doc.experts[0].max_steps == 2
    assert store.head(PID).pending_version is None
    svc.publish(_req(files, 2, doc=_changed(files, 4)))                    # 恢复后可继续发布
    assert store.head(PID).published_version >= 3


def test_TC_UNIT_R26_134_non_stale_pending_reports_config_busy():
    """CR-002：未陈旧的 pending（另一次保存进行中）→ config_busy；不强行回收。"""
    svc, files, store, *_ = make_env()
    store.begin_publish(PID, base_version=0, new=SimpleNamespace(kind="publish", actor="u", summary="x", rolled_back_to=None,
                        manifest_hash="m"), snapshot=build_snapshot(files.doc, files.prompts), extra_baseline=None,
                        now="2026-10-27T00:00:50Z", stale_after_s=30.0)
    with pytest.raises(PublishError) as ei:
        svc.publish(_req(files, 0, doc=_changed(files)))
    assert ei.value.code == "config_busy"


def test_TC_UNIT_R26_135_removed_agent_prompts_are_cleaned():
    """US-005 / AC-005-01：删除 agent 的发布同时清理其提示词目录（否则装配期判孤儿文件）。"""
    svc, files, *_ = make_env()
    doc = make_v2_document(PID, (expert("a", default=True),))
    svc.publish(_req(files, 0, doc=doc))
    assert "b" not in files.prompts and "a" in files.prompts


def test_TC_UNIT_R26_136_preview_returns_diff_and_conflict_without_writing():
    """US-016 / AC-016-01/02：预览返回差异清单（不写盘、不产生版本）；基线陈旧同样回 conflict。"""
    svc, files, store, audit, calls = make_env()
    p = svc.preview(_req(files, 0, doc=_changed(files, 3)))
    assert any(i.kind == "agent_field" and i.object_id == "a" for i in p.items) and not p.layout_only and p.errors == ()
    assert files.log == [] and store.head(PID).published_version == 0 and audit.list_by_project(PID, limit=5) == ()
    svc.publish(_req(files, 0, doc=_changed(files, 3)))
    with pytest.raises(PublishError) as ei:
        svc.preview(_req(files, 0, doc=_changed(files, 4)))
    assert ei.value.code == "conflict"


def test_TC_UNIT_R26_137_adopt_drift_registers_files_as_new_version_without_writing_files():
    """ADR-55：采纳漂移 = 把文件态登记为新版本（不写文件）；无漂移 → no_changes。"""
    svc, files, store, *_ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 2)))                    # head=2，文件=版本 2
    with pytest.raises(PublishError) as a:
        svc.adopt_drift(PID, "mgr", base_version=2)
    assert a.value.code == "no_changes"
    files.doc = _changed(files, 6)                                           # 有人绕过系统直接改了文件
    files.log.clear()
    res = svc.adopt_drift(PID, "mgr", base_version=2)
    assert res.version == 3 and files.log == []
    assert store.get_version(PID, 3)[0].kind == "adopt"


def test_TC_UNIT_R26_138_candidate_and_validate_are_read_only():
    """US-029：candidate/validate 只读（试运行入口）：不写盘、不占 pending、不要求 base 匹配。"""
    svc, files, store, audit, _ = make_env()
    cand = svc.candidate(_req(files, 99, doc=_changed(files, 3)))
    assert cand.definition.experts[0].max_steps == 3
    assert svc.validate(_req(files, 99, doc=_changed(files, 3))) == ()
    assert files.log == [] and store.head(PID).pending_version is None and audit.list_by_project(PID, limit=5) == ()


def test_TC_UNIT_R26_139_user_message_overrides_system_summary_and_is_capped():
    """AC-017-01：保存人填写的说明优先于系统摘要，且 ≤200 字符。"""
    svc, files, store, *_ = make_env()
    svc.publish(_req(files, 0, doc=_changed(files, 3), message="m" * 500))
    assert store.get_version(PID, 2)[0].summary == "m" * 200
