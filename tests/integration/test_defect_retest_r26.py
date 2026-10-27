"""[REV-26 / GROUP_D 复测] DEF-R26-001 / DEF-R26-002 修复的补充 AC 断言（只加不删；与 TC-INT-R26-024 / 059 互补）。

溯源：US-021 / AC-021-02（步数上限，A05 / REQ-NFUNC-010）、AC-021-03（temperature 不可编辑）。
层级：集成（真实 LangGraph / 真实发布管线 / Django 测试客户端；离线替身）。
"""

from __future__ import annotations

import copy
import json

import pytest
from config_r26_support import Api, agent_node, edge, expert, graph, keyword_pred, node, publish_body, v2_with_billing

from ib.core import ELSE_BRANCH
from test_dag_execution_r26 import Spy, _deploy, _run, _status

P = "p_alpha"


def _fan(names):
    nodes = [node("start", "start"), node("end", "end")] + [agent_node(n) for n in names]
    edges = [edge(f"s{i}", "start", n) for i, n in enumerate(names)] + [edge(f"o{i}", n, "end") for i, n in enumerate(names)]
    return tuple(expert(n, default=(i == 0)) for i, n in enumerate(names)), graph(nodes, edges)


def _x_then_fan(extra):
    names = ["x"] + extra
    nodes = [node("start", "start"), node("end", "end")] + [agent_node(n) for n in names]
    edges = [edge("e0", "start", "x")] + [edge(f"f{i}", "x", c) for i, c in enumerate(extra)] + [
        edge(f"o{i}", c, "end") for i, c in enumerate(extra)]
    return tuple(expert(n, default=(n == "x")) for n in names), graph(nodes, edges)


def test_TC_INT_R26_150_parallel_from_start_exactly_cap(deps, monkeypatch):
    """US-021 / AC-021-02：起点直接并行 3 个 agent、上限 2 → 恰好执行 2 个，第 3 个 skipped_step_cap，仍有答复。"""
    spy = Spy(deps, monkeypatch)
    experts, g = _fan(["a1", "a2", "a3"])
    out = _run(deps, _deploy(deps, experts, g, max_expert_steps=2), "问题")
    ran = [n for n in ("a1", "a2", "a3") if _status(out, n) == ["ran"]]
    assert ran == ["a1", "a2"] and len(spy.prompts) == 2
    assert _status(out, "a3") == ["skipped_step_cap"] and out.results


def test_TC_INT_R26_151_cap_not_over_applied_when_budget_suffices(deps, monkeypatch):
    """US-021 / AC-021-02（反例，防过度截断）：上限 8、1 + 3 并行 → 4 个全部执行，无 skipped_step_cap。"""
    spy = Spy(deps, monkeypatch)
    experts, g = _x_then_fan(["c1", "c2", "c3"])
    out = _run(deps, _deploy(deps, experts, g, max_expert_steps=8), "问题")
    assert [_status(out, n) for n in ("x", "c1", "c2", "c3")] == [["ran"]] * 4
    assert len(spy.prompts) == 4
    assert not any(t.status == "skipped_step_cap" for t in out.trace)


def test_TC_INT_R26_152_cap_three_with_one_plus_three_runs_exactly_three(deps, monkeypatch):
    """US-021 / AC-021-02：上限 3、1 + 3 并行 → 恰好执行 3 个（x、c1、c2），c3 被截。"""
    spy = Spy(deps, monkeypatch)
    experts, g = _x_then_fan(["c1", "c2", "c3"])
    out = _run(deps, _deploy(deps, experts, g, max_expert_steps=3), "问题")
    assert [n for n in ("x", "c1", "c2", "c3") if _status(out, n) == ["ran"]] == ["x", "c1", "c2"]
    assert len(spy.prompts) == 3 and _status(out, "c3") == ["skipped_step_cap"]


def test_TC_INT_R26_153_inactive_branch_does_not_consume_step_budget(deps, monkeypatch):
    """US-021 / AC-021-02、US-011：条件分支未激活的 agent 不占步数；上限 2、x 后条件只激活 c1 → x、c1 都执行，c2 为 skipped_inactive（非 step_cap）。"""
    spy = Spy(deps, monkeypatch)
    names = ["x", "c1", "c2"]
    experts = tuple(expert(n, default=(n == "x")) for n in names)
    nodes = [node("start", "start"), node("end", "end"), node("cond", "condition", predicate=keyword_pred(inv=("发票",)))] + [
        agent_node(n) for n in names]
    edges = [edge("e0", "start", "x"), edge("e1", "x", "cond"), edge("e2", "cond", "c1", "inv"),
             edge("e3", "cond", "c2", ELSE_BRANCH), edge("o1", "c1", "end"), edge("o2", "c2", "end")]
    out = _run(deps, _deploy(deps, experts, graph(nodes, edges), max_expert_steps=2), "发票问题")
    assert _status(out, "x") == ["ran"] and _status(out, "c1") == ["ran"]
    assert _status(out, "c2") == ["skipped_inactive"]
    assert len(spy.prompts) == 2


# ----------------------------------------------------------------------------- AC-021-03


@pytest.fixture()
def api(accounts_app):
    deps, Client = accounts_app
    a = Api(deps, Client)
    a.add_user("editor", P, "edit")
    a.add_user("manager", P, "manage")
    return a


def _v2_body(api):
    doc, prompts = v2_with_billing(api.deps, P)
    return publish_body(doc, 0, prompts)


def _items(r):
    return r.json_body["error"]["items"]


def test_TC_INT_R26_154_graph_node_temperature_rejected_on_publish_validate_preview(api):
    """US-021 / AC-021-03：v2 图节点（graph.nodes[i]）里的 temperature → 三个入口均 400 validation_error + field_not_editable，path 指明节点；版本仍 0。"""
    for ep in ("/api/config/publish", "/api/config/validate", "/api/config/publish/preview"):
        body = _v2_body(api)
        body["document"]["graph"]["nodes"][1]["temperature"] = 0.7
        r = api.post(ep, body, who="editor")
        assert r.status_code == 400 and r.json_body["error"]["code"] == "validation_error", ep
        its = _items(r)
        assert [i["code"] for i in its] == ["field_not_editable"], (ep, its)
        assert its[0]["path"] == "graph.nodes[1].temperature", its
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0


def test_TC_INT_R26_155_positive_control_same_body_without_temperature_publishes(api):
    """US-021 / AC-021-03（正例）：同一请求体去掉 temperature 后正常发布 200（证明 400 由 temperature 引起，而非其他校验）。"""
    body = _v2_body(api)
    bad = copy.deepcopy(body)
    bad["document"]["route"]["temperature"] = 0.5
    assert api.post("/api/config/publish", bad, who="editor").status_code == 400
    r = api.post("/api/config/publish", body, who="editor")
    assert r.status_code == 200 and r.json_body["version"] == 2


def test_TC_INT_R26_156_temperature_rejection_writes_rejected_audit_and_no_version(api):
    """US-021 / AC-021-03、US-023 / AC-023-02：temperature 被拒时写 rejected 审计（含 field_not_editable），不含 temperature 数值，且不产生版本。"""
    body = _v2_body(api)
    body["document"]["temperature"] = 0.987654
    assert api.post("/api/config/publish", body, who="editor").status_code == 400
    items = api.get("/api/config/audit?action=config.publish", who="manager").json_body["items"]
    rej = [i for i in items if i["result"] == "rejected"]
    assert rej and "field_not_editable" in (rej[0]["detail_code"] or "")
    assert "0.987654" not in json.dumps(items, ensure_ascii=False)
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0
