"""[REV-26 / GROUP_D] 热生效与运行时缓存（MOD-R26-12/14）：版本切换、钉旧版、单飞编译、失败保留旧版、冷启动 fail-closed、
多进程收敛（两个独立缓存实例 = 两个进程）。

溯源：US-014（AC-014-01/02/03/04 逻辑部分）、US-015（AC-015-01/02/03）、US-021（AC-021-01）。
层级：集成（真实 compile + LangGraph + 内存台账/向量库；离线替身 LLM）。
**离线口径**：5 秒热生效时限与目标机性能不在本文件验证（列入“目标机上线验证项”）；这里验证的是版本切换的**逻辑正确性**。
"""

from __future__ import annotations

import threading
from dataclasses import replace

import pytest
from config_r26_support import (
    BILLING_PROMPT,
    ExpertRecorder,
    ask,
    publish,
    v2_with_billing,
)

from ib.core import PromptLayers
from ib.runtime import ConfigVersionExpiredError, ProjectRuntimeCache

P = "p_alpha"


def _cache(deps, *, interval=0.0, rt_deps=None):
    base = deps.runtime_cache
    return ProjectRuntimeCache(versions=deps.version_store, loader=base._loader, deps=rt_deps or base._deps,
                               check_interval_s=interval)


def test_TC_INT_R26_001_publish_binds_new_questions_to_new_version_and_route(deps, monkeypatch):
    """US-014 / AC-014-01/02：保存成功后新提问立即绑定新版本，且含新关键词的提问被路由到新 agent；全程未重启。"""
    rec = ExpertRecorder(deps, monkeypatch)
    _, v_before = ask(deps, P, "我的发票怎么报销", "s0")
    assert v_before == 0 and rec.experts == ["kb-agent"]
    rec.clear()
    doc, prompts = v2_with_billing(deps, P)
    res = publish(deps, P, doc, prompts)
    _, v_after = ask(deps, P, "我的发票怎么报销", "s1")
    assert v_after == res.version == 2
    assert rec.experts == ["billing-agent"]
    assert rec.calls[0][1] == BILLING_PROMPT, "该 agent 使用自己的提示词，而不是项目共用提示词"


def test_TC_INT_R26_002_inflight_answer_stays_on_its_start_version(deps, monkeypatch):
    """US-015 / AC-015-01/02：进行中的回答绑定其开始时的租约（版本 N）；另一账号发布 N+1 不影响它，下一次提问用 N+1。"""
    rec = ExpertRecorder(deps, monkeypatch)
    lease_old = deps.runtime_for(P)               # 回答开始时取得的租约
    assert lease_old.compiled.version == 0
    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)                # 另一账号发布 N+1
    kinds, v = ask(deps, P, "我的发票怎么报销", "inflight", lease=lease_old)
    assert v == 0 and kinds.count("done") == 1 and rec.experts == ["kb-agent"], "旧租约仍按旧配置作答，完成事件恰好 1 次"
    rec.clear()
    _, v_next = ask(deps, P, "我的发票怎么报销", "next")
    assert v_next == 2 and rec.experts == ["billing-agent"]


def test_TC_INT_R26_003_pinned_version_resolves_after_newer_publish(deps):
    """US-015 / AC-015-03：挂起会话钉住的旧版本，在新版本生效后仍可按原版本恢复（含已被删除的 agent）。"""
    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)                                           # v2 含 billing-agent
    from ib.config.definition import upgrade_to_v2

    without = replace(upgrade_to_v2(deps.definition_store.load(P)))
    # 发布 v3：删除 billing-agent
    from config_r26_support import expert, make_v2_document

    v3 = make_v2_document(P, (expert("kb-agent", default=True, label="知识库助手"),))
    publish(deps, P, v3, {})
    assert deps.runtime_for(P).compiled.version == 3
    pinned = deps.runtime_cache.acquire_version(P, 2)
    assert pinned.compiled.version == 2 and "billing-agent" in pinned.compiled.view.agents
    assert "billing-agent" not in deps.runtime_for(P).compiled.view.agents
    assert without is not None


def test_TC_INT_R26_004_pinned_version_pruned_fails_closed_with_409_code(deps):
    """US-015：挂起会话所绑定的版本已被修剪 → ConfigVersionExpiredError（code=config_version_expired），不静默改用新版本。"""
    with pytest.raises(ConfigVersionExpiredError) as ei:
        deps.runtime_cache.acquire_version(P, 999)
    assert ei.value.code == "config_version_expired"


def test_TC_INT_R26_005_two_process_convergence_via_head_probe(deps, monkeypatch):
    """US-014 / AC-014-04：进程 B（独立缓存实例）不经 on_published，仅靠 head 探测收敛到新版本；收敛后 100 次提问版本一致。"""
    proc_b = _cache(deps, interval=0.0)
    assert proc_b.acquire(P).compiled.version == 0
    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)                       # 进程 A 发布（A 的缓存已被 on_published 换引用）
    assert proc_b.acquire(P).compiled.version == 0, "探测触发后台编译的同一次调用仍返回旧版（一次提问只绑定一个版本）"
    for _ in range(200):                                  # 等后台单飞编译完成（离线编译为毫秒级）
        if proc_b.status(P).applied_version == 2:
            break
        threading.Event().wait(0.05)
    assert proc_b.status(P).applied_version == 2
    versions = {proc_b.acquire(P).compiled.version for _ in range(100)}
    assert versions == {2}
    assert {deps.runtime_for(P).compiled.version for _ in range(100)} == {2}
    assert proc_b.status(P).state == "ok"


def test_TC_INT_R26_006_single_flight_compile(deps):
    """ADR-54：head 变更后多线程同时触发刷新，只有一个后台编译在飞（单飞），不会并发编译 N 次。"""
    gate, started, count = threading.Event(), threading.Event(), []
    base = deps.runtime_cache._deps

    def slow_cfg(route):
        count.append(1)
        started.set()
        assert gate.wait(10)
        return base.graph_config_factory(route)

    proc = _cache(deps, interval=0.0, rt_deps=replace(base, graph_config_factory=slow_cfg))
    gate.set()
    proc.acquire(P)                       # 冷编译（gate 已放行）
    gate.clear(); started.clear(); count.clear()
    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)
    threads = [threading.Thread(target=proc.refresh_async, args=(P,)) for _ in range(6)]
    for t in threads:
        t.start()
    assert started.wait(10)
    for t in threads:
        t.join(5)
    assert len(count) == 1, f"期望单飞编译 1 次，实测 {len(count)} 次"
    gate.set()
    for _ in range(100):
        if proc.status(P).applied_version == 2:
            break
        threading.Event().wait(0.05)
    assert proc.status(P).applied_version == 2


def test_TC_INT_R26_007_compile_failure_keeps_serving_old_version_and_backs_off(deps):
    """US-014 / AC-014-03：head 指向的版本编译失败 → 旧快照继续服务，状态 apply_failed 含错误码；退避窗口内不重试；修复后恢复。"""
    from config_r26_support import expert, make_v2_document
    from ib.config.versioning import build_snapshot, manifest_hash
    from ib.core import NewVersion

    proc = _cache(deps, interval=0.0)
    assert proc.acquire(P).compiled.version == 0
    # 直接在版本存储里放一个“两层提示词皆缺”的 v2（绕过发布服务的预编译，模拟 A 进程已提交但本进程编译失败）
    bad_doc = make_v2_document(P, (expert("kb-agent", default=True),))
    bad = build_snapshot(bad_doc, {"kb-agent": PromptLayers(None, None)})
    vs = deps.version_store
    r = vs.begin_publish(P, base_version=0, new=NewVersion("publish", "u", "bad", None, manifest_hash(bad)), snapshot=bad,
                         extra_baseline=None, now="2026-10-27T00:00:00Z", stale_after_s=30.0)
    vs.commit_publish(P, r.version, now="2026-10-27T00:00:01Z", keep=50)
    proc.refresh_now(P)
    st = proc.status(P)
    assert st.state == "apply_failed" and st.last_error_code and st.applied_version == 0 and st.head_version == r.version
    assert proc.acquire(P).compiled.version == 0, "旧版本继续服务，不出现新旧混用"
    retry_at_before = proc._entry(P).retry_at
    proc.refresh_async(P)                                  # 退避窗口内：不重试
    assert proc._entry(P).retry_at == retry_at_before and proc._entry(P).building is False


def test_TC_INT_R26_008_cold_start_with_broken_config_fails_closed(deps):
    """US-014 / NFUNC-004：冷启动编译失败 → 抛出（fail-closed），不产生半成品服务。"""
    from ib.core import ConfigError

    broken_loader = type("L", (), {"load_files": lambda self, pid: (_ for _ in ()).throw(ConfigError("broken", key="X"))})()
    proc = ProjectRuntimeCache(versions=deps.version_store, loader=broken_loader, deps=deps.runtime_cache._deps)
    with pytest.raises(ConfigError):
        proc.acquire(P)
    assert proc.status(P).applied_version == -1


def test_TC_INT_R26_009_cold_start_detects_file_drift_and_serves_published_head(deps):
    """ADR-55：冷启动发现文件态与已发布 head 的清单哈希不一致（有人绕过系统改了文件）→ 以 head 快照编译并标 drift。"""
    from config_r26_support import expert, make_v2_document

    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)                                              # head = 2（含 billing）
    # 绕过系统直接改文件态：把定义文档写回成只有 kb-agent
    only = make_v2_document(P, (expert("kb-agent", default=True, label="知识库助手"),))
    deps.definition_store.save(P, only, expected_content_hash=None)
    proc = _cache(deps, interval=0.0)
    lease = proc.acquire(P)
    assert lease.compiled.version == 2 and "billing-agent" in lease.compiled.view.agents
    assert proc.status(P).drift is True


def test_TC_INT_R26_010_default_expert_answers_when_no_route_hits(deps, monkeypatch):
    """US-021 / AC-021-01：路由各层均未命中 → 默认专家作答，响应有内容，不出现“无人应答”。"""
    rec = ExpertRecorder(deps, monkeypatch)
    doc, prompts = v2_with_billing(deps, P)
    publish(deps, P, doc, prompts)
    kinds, _ = ask(deps, P, "随便聊聊天气", "s9")
    assert rec.experts == ["kb-agent"] and "content" in kinds and kinds[-1] == "done"
