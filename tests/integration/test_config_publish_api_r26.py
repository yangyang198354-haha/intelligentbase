"""[REV-26 / GROUP_D] 配置发布 HTTP 端点族（status / definition / validate / preview / publish / versions / rollback / drafts / audit）。

溯源：US-001/002（数据来源）、US-005/006/007/008/013/016/017/018/019/021/023、US-012、US-020（AC-020-03）。
层级：集成（Django 测试客户端 + 真实账户体系 + 真实发布服务/运行时缓存；离线替身）。
"""

from __future__ import annotations

import copy
import json
import re

import pytest
from config_r26_support import (
    Api,
    ExpertRecorder,
    agent_node,
    ask,
    doc_json,
    edge,
    expert,
    graph,
    make_v2_document,
    node,
    publish_body,
    v2_with_billing,
)

from ib.builder.egress import contains_secret_pattern
from ib.core import ELSE_BRANCH, PromptLayers

P = "p_alpha"


@pytest.fixture()
def api(accounts_app):
    deps, Client = accounts_app
    a = Api(deps, Client)
    a.add_user("viewer", P, "view")
    a.add_user("editor", P, "edit")
    a.add_user("manager", P, "manage")
    return a


def _publish(api, who="editor", **kw):
    doc, prompts = v2_with_billing(api.deps, P, **kw)
    base = api.get("/api/config/status", who=who).json_body["version"]
    r = api.post("/api/config/publish", publish_body(doc, base, prompts), who=who)
    return r, doc, prompts


def _codes(resp):
    return [i["code"] for i in resp.json_body["error"]["items"]]


def test_TC_INT_R26_040_status_and_legacy_definition_for_v1_project(api):
    """US-020 / AC-020-01：旧形态项目无需先保存即可读：status 显示 legacy/version 0；definition 返回规范化图（只读展示，文件不动）。"""
    s = api.get("/api/config/status", who="viewer").json_body
    assert (s["version"], s["legacy"], s["schema_version"], s["level"], s["apply_state"]) == (0, True, 1, "view", "ok")
    d = api.get("/api/config/definition", who="viewer").json_body
    assert d["level"] == "view" and d["version"] == 0
    kinds = {n["kind"] for n in d["graph"]["nodes"]}
    assert {"start", "route", "agent", "end"} <= kinds
    assert d["document"]["schema_version"] == 1, "文档本身仍是 v1，未被改写"


def test_TC_INT_R26_041_publish_new_agent_hot_effect_and_response_has_no_restart_hint(api, monkeypatch):
    """US-014 / AC-014-01/02/05、US-013 / AC-013-06：合法图保存 200，响应含新版本号与 applied=true；新提问立即路由到新 agent；响应无“重启”字样。"""
    rec = ExpertRecorder(api.deps, monkeypatch)
    r, doc, _ = _publish(api)
    assert r.status_code == 200 and r.json_body["version"] == 2 and r.json_body["applied"] is True
    assert "重启" not in r.content.decode("utf-8")
    ask(api.deps, P, "我的发票怎么报销", "h1")
    assert rec.experts == ["billing-agent"]
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 2


def test_TC_INT_R26_042_preview_shows_diff_without_effect_and_no_changes_is_422(api):
    """US-016 / AC-016-01/02/03：预览给出“新增 agent / 工具授权”差异，不产生版本；无变更保存 → 422 no_changes，不产生新版本。"""
    doc, prompts = v2_with_billing(api.deps, P)
    r = api.post("/api/config/publish/preview", publish_body(doc, 0, prompts), who="editor")
    kinds = {(i["kind"], i["object_id"]) for i in r.json_body["items"]}
    assert r.status_code == 200 and ("agent_added", "billing-agent") in kinds and ("tool_grant", "billing-agent") in kinds
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0, "取消 = 不提交，在用版本不变"
    cur = api.get("/api/config/definition", who="editor").json_body["document"]
    empty = api.post("/api/config/publish", {"base_version": 0, "document": cur}, who="editor")
    assert empty.status_code == 422 and empty.json_body["error"]["code"] == "no_changes"
    assert api.get("/api/config/versions", who="editor").json_body["items"] == []


def test_TC_INT_R26_043_cycle_rejected_400_with_nodes_and_version_unchanged(api):
    """US-013 / AC-013-01/05：绕过界面直接提交含环图 → 400 validation_error 逐条错误（含环上节点），在用版本不变。"""
    doc, prompts = v2_with_billing(api.deps, P)
    g = doc.graph
    nodes = list(g.nodes)
    edges = [e for e in g.edges if e.id not in ("e-o0", "e-o1")] + [
        edge("c1", "kb-agent", "billing-agent"), edge("c2", "billing-agent", "kb-agent"), edge("c3", "billing-agent", "end")]
    bad = make_v2_document(P, doc.experts, graph(nodes, edges))
    r = api.post("/api/config/publish", publish_body(bad, 0, prompts), who="editor")
    assert r.status_code == 400 and r.json_body["error"]["code"] == "validation_error"
    cyc = [i for i in r.json_body["error"]["items"] if i["code"] == "graph_cycle"]
    assert cyc and "kb-agent" in cyc[0]["message"] and "billing-agent" in cyc[0]["message"]
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0


@pytest.mark.parametrize("mutate,code", [
    ("unconnected", "graph_unreachable_from_start"),
    ("no_end_path", "graph_no_path_to_end"),
    ("no_else", "graph_branch_else_missing"),
])
def test_TC_INT_R26_044_graph_errors_surface_through_http_with_paths(api, mutate, code):
    """US-013 / AC-013-02/03、US-006 / AC-006-02：未连线节点 / 无通向结束的路径 / 路由缺 __else__ 均被拒并指出对象。"""
    doc, prompts = v2_with_billing(api.deps, P)
    nodes, edges = list(doc.graph.nodes), list(doc.graph.edges)
    if mutate == "unconnected":
        nodes.append(node("orphan", "join"))
    elif mutate == "no_end_path":
        edges = [e for e in edges if e.id != "e-o1"]
    else:
        edges = [e for e in edges if e.id != "e-else"]
    bad = make_v2_document(P, doc.experts, graph(nodes, edges))
    r = api.post("/api/config/publish", publish_body(bad, 0, prompts), who="editor")
    assert r.status_code == 400 and code in _codes(r)
    hit = next(i for i in r.json_body["error"]["items"] if i["code"] == code)
    assert hit["path"].startswith("graph.")


def test_TC_INT_R26_045_field_validation_errors_name_the_field(api):
    """US-006 / AC-006-03/04、US-007 / AC-007-02、US-008 / AC-008-02、US-019 / AC-019-04：字段级错误指出字段与范围，在用配置不变。"""
    base = lambda **kw: v2_with_billing(api.deps, P, **kw)  # noqa: E731
    doc, prompts = base()
    r = api.post("/api/config/publish", publish_body(make_v2_document(P, doc.experts, doc.graph, tau=-1.0), 0, prompts), who="editor")
    assert r.status_code == 400 and any(i["path"] == "route.tau" for i in r.json_body["error"]["items"])

    kw = base(keywords=("资料",))   # 与 kb-agent 的关键词“资料”撞车
    r2 = api.post("/api/config/publish", publish_body(kw[0], 0, kw[1]), who="editor")
    assert "expert_keyword_collision" in _codes(r2)
    msg = next(i["message"] for i in r2.json_body["error"]["items"] if i["code"] == "expert_keyword_collision")
    assert "kb-agent" in msg and "billing-agent" in msg

    steps = base(max_steps=0)
    r3 = api.post("/api/config/publish", publish_body(steps[0], 0, steps[1]), who="editor")
    assert any(i["path"].endswith("max_steps") for i in r3.json_body["error"]["items"])

    d4, p4 = base()
    j = publish_body(d4, 0, p4)
    for g in j["document"]["tool_grants"]:
        if g["expert_name"] == "billing-agent":
            g["param_values"] = [{"name": "search_knowledge.top_k", "value": "5000"}]
    r4 = api.post("/api/config/publish", j, who="editor")
    assert r4.status_code == 400 and any("top_k" in i["path"] + i["message"] for i in r4.json_body["error"]["items"])

    p5 = {"billing-agent": PromptLayers("x" * 20001, None)}
    r5 = api.post("/api/config/publish", publish_body(d4, 0, p5), who="editor")
    too_long = [i for i in r5.json_body["error"]["items"] if i["code"] == "prompt_too_long"]
    assert too_long and "20000" in too_long[0]["message"]
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0


def test_TC_INT_R26_046_default_expert_cannot_be_removed_or_disabled(api):
    """US-005 / AC-005-02：删除/停用默认专家被拒。"""
    doc, prompts = v2_with_billing(api.deps, P)
    only_billing = make_v2_document(P, (expert("billing-agent", default=True),), graph(
        [node("start", "start"), node("end", "end"), agent_node("billing-agent")],
        [edge("a", "start", "billing-agent"), edge("b", "billing-agent", "end")]), grants={"billing-agent": ("search_knowledge",)})
    j = publish_body(only_billing, 0, prompts)
    j["document"]["route"]["default_expert"] = "kb-agent"          # 默认专家仍指向已删除的 kb-agent
    r = api.post("/api/config/publish", j, who="editor")
    assert r.status_code == 400
    disabled = make_v2_document(P, (expert("kb-agent", default=True, status="disabled"), expert("billing-agent")),
                                graph([node("start", "start"), node("end", "end"), agent_node("billing-agent")],
                                      [edge("a", "start", "billing-agent"), edge("b", "billing-agent", "end")]))
    r2 = api.post("/api/config/publish", publish_body(disabled, 0, prompts), who="editor")
    assert "expert_default_disabled" in _codes(r2)


def test_TC_INT_R26_047_stale_base_returns_409_receipt_and_keeps_first_save(api):
    """US-018 / AC-018-01（重点）：甲先保存 → 乙基于旧版本保存被拒 409，回执含冲突对象清单；当前版本仍为甲的版本，甲的改动未被覆盖。"""
    a, pa = v2_with_billing(api.deps, P, max_steps=2)
    ra = api.post("/api/config/publish", publish_body(a, 0, pa), who="editor")
    assert ra.status_code == 200 and ra.json_body["version"] == 2
    b, pb = v2_with_billing(api.deps, P, max_steps=6)   # 乙仍基于 0
    # v2_with_billing 读取的是甲保存后的文件态；此处强制把乙的基线设为 0（陈旧）
    rb = api.post("/api/config/publish", publish_body(b, 0, pb), who="manager")
    assert rb.status_code == 409 and rb.json_body["error"]["code"] == "conflict"
    receipt = rb.json_body["error"]["receipt"]
    assert receipt["head_version"] == 2 and receipt["base_version"] == 0
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 2
    cur = api.get("/api/config/definition", who="viewer").json_body["document"]
    assert next(e for e in cur["experts"] if e["name"] == "billing-agent")["max_steps"] == 2


def test_TC_INT_R26_048_conflict_receipt_lists_overlapping_objects(api):
    """AC-018-01：两人都改了同一对象才出现在冲突清单里（对象/字段级）。"""
    first, pf = v2_with_billing(api.deps, P, max_steps=2)
    assert api.post("/api/config/publish", publish_body(first, 0, pf), who="editor").status_code == 200
    # 乙基于旧版 1（基线）修改同一 agent（新增并设不同步数）
    second, ps = v2_with_billing(api.deps, P, max_steps=7)
    r = api.post("/api/config/publish", publish_body(second, 1, ps), who="manager")
    assert r.status_code == 409
    objs = {(c["kind"], c["object_id"]) for c in r.json_body["error"]["receipt"]["conflicts"]}
    assert ("agent", "billing-agent") in objs


def test_TC_INT_R26_049_versions_history_diff_detail_and_rollback(api, monkeypatch):
    """US-017 / AC-017-01/02：版本历史含版本号/保存人/时间/摘要；回滚产生新版本且内容与目标一致，5 秒内（此处：立即）新提问使用新版本。"""
    rec = ExpertRecorder(api.deps, monkeypatch)
    r1, d1, p1 = _publish(api, who="editor")                 # v1 基线, v2 含 billing
    d_only = make_v2_document(P, (expert("kb-agent", default=True, label="知识库助手"),),
                              grants={"kb-agent": ("search_knowledge",)})
    d_only = copy.deepcopy(d_only)
    r2 = api.post("/api/config/publish", publish_body(d_only, 2, None), who="editor")   # v3 删除 billing
    assert r1.status_code == 200 and r2.status_code == 200 and r2.json_body["version"] == 3
    hist = api.get("/api/config/versions", who="viewer").json_body
    assert hist["head"] == 3 and [i["version"] for i in hist["items"]] == [3, 2, 1]
    assert all(i["actor"] and i["created_at"] and i["summary"] for i in hist["items"])
    assert hist["items"][-1]["kind"] == "baseline" and hist["items"][0]["summary"].startswith("删除 agent")
    detail = api.get("/api/config/versions/2", who="viewer").json_body
    assert any(e["name"] == "billing-agent" for e in detail["document"]["experts"])
    diff = api.get("/api/config/versions/2/diff?against=3", who="viewer").json_body
    assert any(i["kind"] == "agent_removed" and i["object_id"] == "billing-agent" for i in diff["items"]) or \
        any(i["kind"] == "agent_added" for i in diff["items"])
    rb = api.post("/api/config/rollback", {"target_version": 2, "base_version": 3}, who="manager")
    assert rb.status_code == 200 and rb.json_body["version"] == 4
    ask(api.deps, P, "我的发票怎么报销", "rb")
    assert rec.experts[-1] == "billing-agent"
    last = api.get("/api/config/versions", who="viewer").json_body["items"][0]
    assert (last["kind"], last["rolled_back_to"]) == ("rollback", 2)
    audit = api.get("/api/config/audit?action=config.rollback", who="manager").json_body["items"]
    assert len(audit) == 1 and audit[0]["version_before"] == 3 and audit[0]["version_after"] == 4


def test_TC_INT_R26_050_rollback_requires_manage_and_rejects_unknown_target(api):
    """US-017 / AC-017-03：只有编辑档 → 403 且提示所需档位“manage”；目标版本不存在 → 404。"""
    _publish(api)
    r = api.post("/api/config/rollback", {"target_version": 1, "base_version": 2}, who="editor")
    assert r.status_code == 403 and r.json_body["error"]["required_level"] == "manage"
    miss = api.post("/api/config/rollback", {"target_version": 99, "base_version": 2}, who="manager")
    assert miss.status_code == 404


def test_TC_INT_R26_051_v1_first_save_creates_baseline_v1_then_user_v2(api):
    """US-020 / AC-020-03、A07：旧项目首次保存 → 版本历史出现升级前基线 v1（等价于升级前行为）与用户 v2。"""
    _publish(api)
    items = api.get("/api/config/versions", who="viewer").json_body["items"]
    assert [(i["version"], i["kind"]) for i in items] == [(2, "publish"), (1, "baseline")]
    base = api.get("/api/config/versions/1", who="viewer").json_body
    assert [e["name"] for e in base["document"]["experts"]] == ["kb-agent"], "基线 = 升级前的单专家形态（规范化后）"


def test_TC_INT_R26_052_layout_only_save_persists_positions_and_keeps_routing(api, monkeypatch):
    """US-012 / AC-012-01/02：只改节点位置的保存成功，刷新后位置一致；保存前后 20 个固定提问路由结果完全一致（20/20）。"""
    _publish(api)
    questions = ["我的发票怎么报销", "报销流程", "发票开具", "资料在哪里", "检索一下文档", "知识库里的问题", "天气如何", "你好",
                 "查资料", "文档检索", "发票", "报销", "问答", "知识", "开发票", "怎么报销发票", "随便聊聊", "再见", "帮我查一下", "谢谢"]
    rec = ExpertRecorder(api.deps, monkeypatch)
    before = []
    for i, q in enumerate(questions):
        rec.clear(); ask(api.deps, P, q, f"b{i}"); before.append(tuple(rec.experts))
    cur = api.get("/api/config/definition", who="editor").json_body["document"]
    moved = copy.deepcopy(cur)
    for n in moved["graph"]["nodes"][:3]:
        n["x"] += 123.0; n["y"] += 45.0
    r = api.post("/api/config/publish", {"base_version": 2, "document": moved}, who="editor")
    assert r.status_code == 200 and r.json_body["version"] == 3
    reread = api.get("/api/config/definition", who="viewer").json_body["document"]["graph"]["nodes"]
    for a, b in zip(moved["graph"]["nodes"][:3], reread[:3]):
        assert (a["x"], a["y"]) == (b["x"], b["y"])
    after = []
    for i, q in enumerate(questions):
        rec.clear(); ask(api.deps, P, q, f"a{i}"); after.append(tuple(rec.experts))
    assert before == after and len(before) == 20
    # 差异清单只含布局项（is_layout_only），不含任何语义变更
    pv = api.get("/api/config/versions/3/diff?against=2", who="editor").json_body
    assert pv["items"] and pv["layout_only"] is True


def test_TC_INT_R26_053_drafts_save_list_get_delete_and_owner_isolation(api):
    """US-018 / AC-018-03：另存草稿副本不影响在用版本；仅本人可见（他人读取 404）；可删除。"""
    doc, _ = v2_with_billing(api.deps, P)
    c = api.post("/api/config/drafts", {"label": "我的副本", "base_version": 0, "document": doc_json(doc)}, who="editor")
    assert c.status_code == 201
    did = c.json_body["draft_id"]
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0
    assert [d["draft_id"] for d in api.get("/api/config/drafts", who="editor").json_body["items"]] == [did]
    assert api.get(f"/api/config/drafts/{did}", who="editor").json_body["document"]["experts"]
    assert api.get(f"/api/config/drafts/{did}", who="manager").status_code == 404
    assert api.get("/api/config/drafts", who="manager").json_body["items"] == []
    assert api.call("DELETE", f"/api/config/drafts/{did}", "editor").status_code == 204
    assert api.get(f"/api/config/drafts/{did}", who="editor").status_code == 404


def test_TC_INT_R26_054_audit_saved_and_rejected_records_without_prompt_text(api):
    """US-023 / AC-023-01/02：成功保存新增 1 条审计（动作/版本前后/对象清单/结果 saved）；校验失败新增 rejected 记录含错误码，不含提示词全文与凭据。"""
    secret_prompt = "审计不应出现的提示词全文-UNIQUE-777"
    doc, _ = v2_with_billing(api.deps, P)
    assert api.post("/api/config/publish", publish_body(doc, 0, {"billing-agent": PromptLayers(secret_prompt, None)}), who="editor").status_code == 200
    bad = make_v2_document(P, doc.experts, doc.graph, tau=-5.0)
    assert api.post("/api/config/publish", publish_body(bad, 2, {"billing-agent": PromptLayers(secret_prompt + "x", None)}), who="editor").status_code == 400
    items = api.get("/api/config/audit?action=config.publish", who="manager").json_body["items"]
    saved = [i for i in items if i["result"] == "saved"]
    rejected = [i for i in items if i["result"] == "rejected"]
    assert len(saved) == 1 and saved[0]["version_before"] == 0 and saved[0]["version_after"] == 2
    assert any(o.startswith("agent_added:billing-agent") for o in saved[0]["object_summary"])
    assert rejected and "route_threshold_out_of_range" in (rejected[0]["detail_code"] or "")
    whole = json.dumps(items, ensure_ascii=False)
    assert secret_prompt not in whole and not contains_secret_pattern(whole)


def test_TC_INT_R26_055_audit_is_append_only_405_and_manage_only_403(api):
    """US-023 / AC-023-03/04：对审计端点的修改/删除请求 → 405，记录不变；无管理权限 → 403。"""
    _publish(api)
    before = api.get("/api/config/audit", who="manager").json_body
    for m in ("PUT", "POST", "PATCH", "DELETE"):
        assert api.call(m, "/api/config/audit", "manager", {} if m != "DELETE" else None).status_code == 405, m
    assert api.get("/api/config/audit", who="manager").json_body == before
    for who in ("viewer", "editor"):
        r = api.get("/api/config/audit", who=who)
        assert r.status_code == 403 and r.json_body["error"]["required_level"] == "manage"


def test_TC_INT_R26_056_audit_record_364_days_old_is_still_listed(api):
    """US-023 / AC-023-05：364 天前产生的审计记录（保留 1 年）管理档仍可查到，字段完整。"""
    from datetime import datetime, timedelta, timezone

    from ib.core import ConfigAuditEntry

    ts = (datetime.now(timezone.utc) - timedelta(days=364)).strftime("%Y-%m-%dT%H:%M:%SZ")
    api.deps.config_audit_store.record(ConfigAuditEntry(
        timestamp=ts, project=P, actor="old-actor", action="config.publish", changed_field_names=("agent",),
        result="saved", detail_code=None, version_before=3, version_after=4, object_summary=("agent:x",)))
    got = [i for i in api.get("/api/config/audit?limit=500", who="manager").json_body["items"] if i["actor"] == "old-actor"]
    assert got and got[0]["timestamp"] == ts and got[0]["version_after"] == 4 and got[0]["object_summary"] == ["agent:x"]


def test_TC_INT_R26_057_prompt_and_definition_payloads_have_no_credentials(api):
    """US-019 / AC-019-03、US-001 / AC-001-03：对 definition / prompts / versions / diff / preview / audit / 错误回执做凭据模式扫描，命中数 = 0；
    无工具授权的 agent 的 tool_count = 0（卡片显示“无”）。"""
    api.deps.llm_key_store  # 系统已配置 LLM Key 的场景由装配期决定；扫描针对响应体
    r, doc, prompts = _publish(api)
    bodies = [r.content]
    for path in ("/api/config/definition", "/api/config/prompts", "/api/config/prompts/kb-agent/main", "/api/config/versions",
                 "/api/config/versions/2", "/api/config/versions/2/diff", "/api/config/catalog", "/api/config/status"):
        bodies.append(api.get(path, who="manager").content)
    bodies.append(api.get("/api/config/audit", who="manager").content)
    bodies.append(api.post("/api/config/publish/preview", publish_body(doc, 2, prompts), who="editor").content)
    bodies.append(api.post("/api/config/publish", publish_body(make_v2_document(P, doc.experts, doc.graph, tau=-1.0), 2, prompts),
                           who="editor").content)
    scan = [b for b in bodies if re.search(rb"sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY", b)]
    assert scan == []
    noop = make_v2_document(P, (expert("kb-agent", default=True), expert("bare")), grants={"kb-agent": ("search_knowledge",)})
    api.post("/api/config/publish", publish_body(noop, 2, {"bare": PromptLayers("你是 bare。", None)}), who="editor")
    agents = {a["name"]: a for a in api.get("/api/config/definition", who="viewer").json_body["derived"]["agents"]}
    assert agents["bare"]["tool_count"] == 0 and agents["kb-agent"]["tool_count"] == 1


def test_TC_INT_R26_058_card_data_for_hover_and_prompt_full_text(api):
    """US-001 / AC-001-01、US-002 / AC-002-01/02：悬停卡片数据（中文标签/主提示词存在/前 120 字符/工具数）与提示词全文逐字一致；
    只有 fallback 的 agent 标注主提示词不存在、兜底可见。"""
    doc, prompts = v2_with_billing(api.deps, P)
    r = api.post("/api/config/publish", publish_body(doc, 0, prompts), who="editor")
    assert r.status_code == 200
    ag = {a["name"]: a for a in api.get("/api/config/definition", who="viewer").json_body["derived"]["agents"]}
    b = ag["billing-agent"]
    assert b["prompt_main_present"] is True and b["prompt_main_head"] == prompts["billing-agent"].main[:120] and b["tool_count"] == 1
    full = api.get("/api/config/prompts/billing-agent/main", who="viewer").json_body["content"]
    assert full == prompts["billing-agent"].main
    # 兜底-only：先去掉主层再读
    api.deps.prompt_stores[P].delete_layer("billing-agent", "main")
    api.deps.prompt_stores[P].save_layer("billing-agent", "fallback", "仅兜底提示词全文", expected_hash=None)
    assert api.get("/api/config/prompts/billing-agent/main", who="viewer").status_code == 404
    assert api.get("/api/config/prompts/billing-agent/fallback", who="viewer").json_body["content"] == "仅兜底提示词全文"


def test_TC_INT_R26_059_temperature_cannot_be_edited(api):
    """US-021 / AC-021-03（DEF-R26-002 已修复）：直接 PUT / 发布请求体里任何位置的 temperature → 400 field_not_editable
    （指明字段位置），不落盘、不产生版本。"""
    cur = api.get("/api/config/definition", who="editor").json_body["document"]
    before_hash = cur["content_hash"]
    for where in ("route", "top", "expert"):
        d = copy.deepcopy(cur)
        if where == "route":
            d["route"]["temperature"] = 0.9
        elif where == "top":
            d["temperature"] = 0.9
        else:
            d["experts"][0]["temperature"] = 0.9
        r = api.put("/api/config/definition", {"document": d, "expected_content_hash": before_hash}, who="editor")
        assert r.status_code == 400 and r.json_body["error"]["code"] == "validation_error", where
        items = r.json_body["error"]["items"]
        assert [i["code"] for i in items] == ["field_not_editable"], where
        assert items[0]["path"].endswith("temperature") and (where == "top" or where in items[0]["path"]), items
        # 新发布端点同口径
        base = api.get("/api/config/status", who="editor").json_body["version"]
        rp = api.post("/api/config/publish", {"base_version": base, "document": d}, who="editor")
        assert rp.status_code == 400 and [i["code"] for i in rp.json_body["error"]["items"]] == ["field_not_editable"], where
    assert api.get("/api/config/status", who="editor").json_body["version"] == 0, "不写版本"
    assert api.get("/api/config/definition", who="editor").json_body["document"]["content_hash"] == before_hash
    persisted = api.get("/api/config/definition", who="editor").json_body["document"]
    assert "temperature" not in json.dumps(persisted)
    assert "temperature" not in api.get("/api/config/catalog", who="editor").content.decode()


def test_TC_INT_R26_060_legacy_put_endpoints_are_publish_wrappers_with_hot_effect(api):
    """CL-003 / IFC-R26-132：旧 PUT definition/prompts 退化为发布包装：保存即热生效并产生版本，响应保持旧形状 + version。"""
    cur = api.get("/api/config/definition", who="editor").json_body["document"]
    d = copy.deepcopy(cur)
    d["route"]["tau"] = 0.72
    r = api.put("/api/config/definition", {"document": d, "expected_content_hash": cur["content_hash"]}, who="editor")
    assert r.status_code == 200 and r.json_body["ok"] is True and r.json_body["version"] == 2
    assert api.deps.runtime_for(P).compiled.version == 2
    pr = api.put("/api/config/prompts/kb-agent/fallback", {"content": "新的兜底提示词", "expected_hash": ""}, who="editor")
    assert pr.status_code == 200
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 3
    stale = api.put("/api/config/definition", {"document": d, "expected_content_hash": cur["content_hash"]}, who="editor")
    assert stale.status_code == 409
