"""[R25 / GROUP_D] 单元 —— 新配置键（偏差 D-04）、上传批次存储、ib-worker 周期动作（MOD-003 / MOD-009 / MOD-011）。

溯源：US-015（AC-015-03 数值可配置）、US-002（批次汇总恒等）、REQ-NFUNC-007（部分失败隔离）、
REQ-NFUNC-001/004（清理队列 / 补晋升由 worker 周期驱动）。
“永不抛异常 / 非致命”类契约（worker 周期动作）配有覆盖失败分支的用例，并与正例成对。
"""

from __future__ import annotations

import types

import pytest

from folder_r25_support import PID, get_doc, install_clock, put_file, scope_of, search, sqlite_deps, update_file

S = scope_of()


# --------------------------------------------------------------------------- #
# D-04：配置越界 / 非整数抛 ConfigError（带键名，不回显值）
# --------------------------------------------------------------------------- #


def _resolve(**overrides):
    from ib.config import resolve_global_config
    from ib.core import RawConfig

    return resolve_global_config(RawConfig(values=dict(overrides), source="test"))


def test_TC_UNIT_R25_100_new_config_keys_defaults():
    """[TC-UNIT-R25-100] MOD-009 / AC-015-01：默认 单次 1000 个文件、总大小 1024MB、10 层、批次 TTL 24 小时（总大小默认值只在配置一处）。"""
    cfg = _resolve()
    assert (cfg.upload_batch_max_files, cfg.upload_batch_max_total_mb, cfg.library_max_depth, cfg.upload_batch_ttl_hours) == (
        1000, 1024, 10, 24,
    )


@pytest.mark.parametrize(
    "key,env_key,low,high",
    [
        ("upload_batch_max_files", "IB_UPLOAD_BATCH_MAX_FILES", 1, 10000),
        ("upload_batch_max_total_mb", "IB_UPLOAD_BATCH_MAX_TOTAL_MB", 1, 102400),
        ("library_max_depth", "IB_LIBRARY_MAX_DEPTH", 1, 64),
        ("upload_batch_ttl_hours", "IB_UPLOAD_BATCH_TTL_HOURS", 1, 720),
    ],
)
def test_TC_UNIT_R25_101_D04_out_of_range_raises_config_error_with_key_only(key, env_key, low, high):
    """[TC-UNIT-R25-101] 偏差 D-04：越界（低于下界 / 高于上界）或非整数 → `ConfigError`（异常类型即 D-04 的实际口径，非设计字面 StartupError），携带键名，消息不回显配置值；
    边界值（下界 / 上界）合法。"""
    from ib.core import ConfigError

    for bad in (low - 1, high + 1, "abc", "12.5"):
        with pytest.raises(ConfigError) as err:
            _resolve(**{key: bad})
        assert err.value.key == env_key
    with pytest.raises(ConfigError) as echo:
        _resolve(**{key: 987654321})
    assert "987654321" not in str(echo.value), "配置值不得回显（只报键名）"
    assert getattr(_resolve(**{key: low}), key) == low
    assert getattr(_resolve(**{key: high}), key) == high
    assert getattr(_resolve(**{key: str(low)}), key) == low, "字符串形态（环境变量）的整数同样接受"


def test_TC_UNIT_R25_102_D04_composition_fails_fast_on_bad_value(raw):
    """[TC-UNIT-R25-102] 偏差 D-04（启动期 fail-fast）：`build_deps` 遇到越界配置同样抛 ConfigError（进程起不来），不是静默回落默认值。"""
    from ib.core import ConfigError
    from ibweb.composition import build_deps

    raw["library_max_depth"] = 0
    with pytest.raises(ConfigError):
        build_deps(raw, force=True)


def test_TC_UNIT_R25_103_new_keys_are_runtime_env_keys():
    """[TC-UNIT-R25-103] 环境变量映射：四个新键登记在 `IB_RUNTIME_ENV_KEYS`，可由环境变量覆盖。"""
    from ib.config import IB_RUNTIME_ENV_KEYS

    assert {
        "IB_UPLOAD_BATCH_MAX_FILES", "IB_UPLOAD_BATCH_MAX_TOTAL_MB", "IB_LIBRARY_MAX_DEPTH", "IB_UPLOAD_BATCH_TTL_HOURS",
    } <= set(IB_RUNTIME_ENV_KEYS)


def test_TC_UNIT_R25_104_max_upload_over_proxy_limit_warns_but_keeps_value(monkeypatch):
    """[TC-UNIT-R25-104] ADR-003：`max_upload_mb > 60` 记 WARNING（error_code=max_upload_mb_exceeds_proxy_limit）但取值不变；60 及以下不告警（成对）。"""
    events = []
    monkeypatch.setattr("ib.observability.log_event", lambda stage, outcome, **kw: events.append((stage, outcome, kw)))
    assert _resolve(max_upload_mb=60).max_upload_mb == 60
    assert not [e for e in events if e[2].get("error_code") == "max_upload_mb_exceeds_proxy_limit"]
    assert _resolve(max_upload_mb=61).max_upload_mb == 61
    warned = [e for e in events if e[2].get("error_code") == "max_upload_mb_exceeds_proxy_limit"]
    assert len(warned) == 1 and warned[0][0] == "startup" and warned[0][1] == "warned"


# --------------------------------------------------------------------------- #
# MOD-003：批次存储（内存 / SQLite 一致）
# --------------------------------------------------------------------------- #


@pytest.fixture(params=["memory", "sqlite"])
def bdeps(request, raw, tmp_path, monkeypatch):
    from ibweb.composition import build_deps

    if request.param == "memory":
        return build_deps(raw, force=True)
    return sqlite_deps(tmp_path, raw, monkeypatch)


def _plans(n):
    from ib.ledger.upload_batches import BatchItemPlan

    return [
        BatchItemPlan(i, f"d/f{i}.txt", f"d/f{i}.txt", "skip" if i == n - 1 else "create", 10, None, "USER_SKIPPED" if i == n - 1 else None)
        for i in range(n)
    ]


def test_TC_UNIT_R25_105_batch_store_summary_identity_and_terminal_idempotence(bdeps):
    """[TC-UNIT-R25-105] 批次汇总恒等：accepted+skipped+failed+pending == total；skip 项初始即 skipped；终态幂等（重复 mark 不改变）；failed 可重试为 accepted。"""
    rec = bdeps.upload_batches.create_batch(S, target_folder_id="", items=_plans(4), ttl_hours=24)
    st = bdeps.upload_batches.summarize(S, rec.batch_id)
    assert (st.total, st.accepted, st.skipped, st.failed, st.pending) == (4, 0, 1, 0, 3)
    mark = bdeps.upload_batches.mark_item
    mark(S, rec.batch_id, 0, state="accepted", reason_code=None, doc_id="d0", final_rel_path=None)
    mark(S, rec.batch_id, 1, state="failed", reason_code="SERVER_ERROR", doc_id=None, final_rel_path=None)
    again = mark(S, rec.batch_id, 0, state="failed", reason_code="X", doc_id=None, final_rel_path=None)
    assert again.state == "accepted" and again.doc_id == "d0", "终态幂等：accepted 不可被改写"
    retried = mark(S, rec.batch_id, 1, state="accepted", reason_code=None, doc_id="d1", final_rel_path=None)
    assert retried.state == "accepted"
    st2 = bdeps.upload_batches.summarize(S, rec.batch_id)
    assert (st2.accepted, st2.skipped, st2.failed, st2.pending) == (2, 1, 0, 1)
    assert st2.accepted + st2.skipped + st2.failed + st2.pending == st2.total == 4


def test_TC_UNIT_R25_106_batch_store_project_scoping_and_expiry(bdeps):
    """[TC-UNIT-R25-106] 批次按项目隔离（他项目 get → None、summarize → NotFoundError）；TTL 到期后 purge_expired 清理批次及其项（未到期不清理）。"""
    from datetime import datetime, timedelta, timezone

    from ib.core import NotFoundError, Scope

    def at(delta):
        return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")

    rec = bdeps.upload_batches.create_batch(S, target_folder_id="", items=_plans(3), ttl_hours=1)
    other = Scope("p_beta")
    assert bdeps.upload_batches.get_batch(other, rec.batch_id) is None
    with pytest.raises(NotFoundError):
        bdeps.upload_batches.summarize(other, rec.batch_id)
    assert bdeps.upload_batches.purge_expired(at(timedelta(minutes=30))) == 0
    assert bdeps.upload_batches.get_batch(S, rec.batch_id) is not None
    assert bdeps.upload_batches.purge_expired(at(timedelta(hours=2))) == 1
    assert bdeps.upload_batches.get_batch(S, rec.batch_id) is None
    assert bdeps.upload_batches.get_item(S, rec.batch_id, 0) is None


# --------------------------------------------------------------------------- #
# MOD-011：worker 周期动作（正例 + 非致命失败分支）
# --------------------------------------------------------------------------- #


@pytest.fixture()
def wapp(http_app):
    return http_app[0]


def test_TC_UNIT_R25_110_worker_cycle_happy_path_summary_keys_and_purge(wapp, monkeypatch):
    """[TC-UNIT-R25-110] 正例：run_once 摘要含 promoted / purged / batches_expired；清理队列中的项被排空；到期批次被清理（batches_expired==1）。"""
    from ibweb.worker import run_once

    from datetime import datetime, timezone

    from folder_r25_support import ctx_of
    from ib.library.uploads import ManifestEntry

    live = put_file(wapp, "w.txt", "worker 周期动作正例 内容甲")
    update_file(wapp, live.doc_id, "w.txt", "worker 周期动作正例 内容乙 已更新")
    wapp.lifecycle.process_pending("w", 10)  # 晋升后旧行入清理队列并被立即排空（best-effort）
    assert get_doc(wapp, live.doc_id) is None
    wapp.tree.enqueue_purge(PID, PID, "ghost-doc", "test")  # 人工放入一个待清理项
    plan = wapp.uploads.plan(
        ctx_of(), S, target_folder_id="", entries=[ManifestEntry(0, "a.txt", 5)], resolutions={}, commit=True,
    )
    # 批次到期时间按真实墙钟计算（iso_plus_seconds），时钟从“现在”起快进 25 小时
    clock = install_clock(monkeypatch, start=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    clock.tick(25 * 3600)
    summary = run_once(lease_owner="r25-w", limit=10, reap=False)
    assert {"promoted", "purged", "batches_expired"} <= set(summary)
    assert wapp.tree.list_purge(10) == [], "清理队列已被本轮周期动作排空"
    assert summary["batches_expired"] == 1 and wapp.upload_batches.get_batch(S, plan.batch_id) is None


def test_TC_UNIT_R25_111_worker_cycle_actions_are_non_fatal_and_isolated(wapp, monkeypatch):
    """[TC-UNIT-R25-111] 反例：补晋升 / 清理排空 / 批次清理任一抛异常，run_once 都不外抛，其余动作照常执行（隔离）；对应计数保持 0。与 110 正例成对。"""
    from ibweb.worker import run_once

    wapp.tree.enqueue_purge(PID, PID, "ghost-doc-2", "test")

    def boom(*a, **k):
        raise RuntimeError("injected")

    monkeypatch.setattr(wapp.lifecycle, "promote_ready_revisions", boom)
    monkeypatch.setattr(wapp.upload_batches, "purge_expired", boom)
    summary = run_once(lease_owner="r25-w", limit=10, reap=False)
    assert summary["promoted"] == 0 and summary["batches_expired"] == 0
    assert summary["purged"] == 1, "补晋升失败不得阻断清理队列排空"
    monkeypatch.setattr(wapp.lifecycle, "drain_purge_queue", boom)
    summary2 = run_once(lease_owner="r25-w", limit=10, reap=False)
    assert summary2["purged"] == 0, "清理排空失败 → 摘要记 0，且不抛"


def test_TC_UNIT_R25_112_worker_known_projects_union_registry_and_config_with_fallback():
    """[TC-UNIT-R25-112] M-SA-018：已知项目集合 = 注册表活动项目 ∪ deps.projects（运行期新建项目只在注册表）；注册表读失败时只用回退集合，不抛。"""
    from ibweb.worker import _known_project_ids

    registry = types.SimpleNamespace(list_active=lambda: [types.SimpleNamespace(project_id="p_runtime"), types.SimpleNamespace(project_id="p_alpha")])
    deps = types.SimpleNamespace(project_registry=registry, projects={"p_alpha": object(), "p_beta": object()})
    assert sorted(_known_project_ids(deps)) == ["p_alpha", "p_beta", "p_runtime"]

    def broken():
        raise RuntimeError("registry down")

    deps2 = types.SimpleNamespace(project_registry=types.SimpleNamespace(list_active=broken), projects={"p_alpha": object()})
    assert _known_project_ids(deps2) == ["p_alpha"]
