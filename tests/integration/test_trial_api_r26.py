"""[REV-26 / GROUP_D] 保存前试运行（`POST /api/config/trial`，SSE）与 agent 运行时权限（知识范围、工具授权）端到端。

溯源：US-029（AC-029-01~05）、US-009（AC-009-01/02/03）、US-007（AC-007-01）、REQ-FUNC-023、ADR-61 / ADR-62。
层级：集成（真实视图层 + 真实编译 + 真实检索管线/台账目录树；LLM 为离线替身）。
"""

from __future__ import annotations

import pytest
from config_r26_support import (
    Api,
    ExpertRecorder,
    ask,
    doc_json,
    edge,
    graph,
    make_v2_document,
    publish,
    publish_body,
    v2_with_billing,
)
from folder_r25_support import put_file

from ib.core import PromptLayers

P = "p_alpha"
MANUAL = "产品手册专属内容 空调机组 保养周期 半年一次"
POLICY = "内部制度专属内容 报销流程 财务审批 三级签字"


@pytest.fixture()
def env(accounts_app):
    deps, Client = accounts_app
    api = Api(deps, Client)
    api.add_user("viewer", P, "view")
    api.add_user("editor", P, "edit")
    api.add_user("manager", P, "manage")
    return deps, api


def _sse(resp) -> str:
    return b"".join(resp.streaming_content).decode("utf-8") if resp.streaming else resp.content.decode("utf-8")


def _trial_body(doc, prompts, query="我的发票怎么报销", sid="t1"):
    b = publish_body(doc, 0, prompts)
    b.update({"query": query, "session_id": sid})
    return b


def test_TC_INT_R26_140_trial_uses_draft_while_production_keeps_serving_old_version(env, monkeypatch):
    """US-029 / AC-029-01（重点）：草稿含未保存的新 agent（关键词“发票”）→ 试运行由该 agent 作答并标注“试运行”；
    同一时刻正式提问同一问题仍按在用版本（不路由到新 agent）。"""
    deps, api = env
    rec = ExpertRecorder(deps, monkeypatch)
    doc, prompts = v2_with_billing(deps, P)
    r = api.post("/api/config/trial", _trial_body(doc, prompts), who="editor")
    body = _sse(r)
    assert r.status_code == 200 and r["Content-Type"].startswith("text/event-stream")
    assert "试运行" in body and "event: done" in body
    assert rec.experts == ["billing-agent"]
    rec.clear()
    _kinds, ver = ask(deps, P, "我的发票怎么报销", "prod")
    assert rec.experts == ["kb-agent"] and ver == 0


def test_TC_INT_R26_141_trial_leaves_no_formal_session_version_or_publish_audit(env):
    """US-029 / AC-029-02：试运行会话不进入正式会话存储；在用版本仍为 N；审计无新的“保存”记录（仅 config.trial）。"""
    deps, api = env
    doc, prompts = v2_with_billing(deps, P)
    before_keys = set(deps.sessions._items)
    _sse(api.post("/api/config/trial", _trial_body(doc, prompts), who="editor"))
    assert set(deps.sessions._items) == before_keys
    assert not any("trial" in k for k in deps.sessions._items)
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 0
    rows = api.get("/api/config/audit?limit=500", who="manager").json_body["items"]
    assert [r["action"] for r in rows if r["action"].startswith("config.")] == ["config.trial"]


def test_TC_INT_R26_142_trial_with_cycle_rejected_400_without_llm_call(env, monkeypatch):
    """US-029 / AC-029-03：草稿含环 → 400 并列出环上节点（与保存校验同口径）；未调用任何 LLM（出站/构造 agent 次数 = 0）。"""
    deps, api = env
    rec = ExpertRecorder(deps, monkeypatch)
    doc, prompts = v2_with_billing(deps, P)
    edges = [e for e in doc.graph.edges if e.id not in ("e-o0", "e-o1")] + [
        edge("c1", "kb-agent", "billing-agent"), edge("c2", "billing-agent", "kb-agent"), edge("c3", "billing-agent", "end")]
    bad = make_v2_document(P, doc.experts, graph(list(doc.graph.nodes), edges))
    r = api.post("/api/config/trial", _trial_body(bad, prompts), who="editor")
    assert r.status_code == 400 and r.json_body["error"]["code"] == "validation_error"
    cyc = next(i for i in r.json_body["error"]["items"] if i["code"] == "graph_cycle")
    assert "kb-agent" in cyc["message"] and "billing-agent" in cyc["message"]
    assert rec.calls == [] and deps.llm.complete_calls == []


def test_TC_INT_R26_143_trial_concurrency_limit_returns_429_trial_busy(env):
    """US-029 / REQ-NFUNC：单项目并发 1：第一个试运行未结束时第二个 → 429 trial_busy（不排队）；第一个结束后恢复。"""
    deps, api = env
    doc, prompts = v2_with_billing(deps, P)
    first = api.post("/api/config/trial", _trial_body(doc, prompts, sid="a"), who="editor")   # 迭代器未消费 = 占用名额
    second = api.post("/api/config/trial", _trial_body(doc, prompts, sid="b"), who="manager")
    assert second.status_code == 429 and second.json_body["error"]["code"] == "trial_busy"
    _sse(first)
    third = api.post("/api/config/trial", _trial_body(doc, prompts, sid="c"), who="manager")
    assert third.status_code == 200
    _sse(third)


@pytest.mark.parametrize("sid", ["", "a:b", "x" * 65])
def test_TC_INT_R26_144_trial_input_validation(env, sid):
    """输入校验：session_id 须 1..64 字符且不含冒号；query 须 1..2000 字符。"""
    deps, api = env
    doc, prompts = v2_with_billing(deps, P)
    assert api.post("/api/config/trial", _trial_body(doc, prompts, sid=sid), who="editor").status_code == 400
    assert api.post("/api/config/trial", _trial_body(doc, prompts, query="  "), who="editor").status_code == 400


# -------------------- agent 运行时权限：知识范围 / 工具授权（真实检索管线） -------------------- #


def _scoped_agent(deps):
    put_file(deps, "手册.txt", MANUAL, rel_dirs=("产品手册",), project_id=P)
    put_file(deps, "制度.txt", POLICY, rel_dirs=("内部制度",), project_id=P)
    from ibweb.composition import _project_folder_index

    ids = {path: fid for fid, path in _project_folder_index(deps, P).items()}
    doc, prompts = v2_with_billing(deps, P, folders=(ids["产品手册"],))
    publish(deps, P, doc, prompts)
    return ids


def _search_tool(deps, agent):
    (tool,) = [t for t in deps.runtime_for(P).compiled.view.agents[agent].tools if t.name == "search_knowledge"]
    return tool


def test_TC_INT_R26_145_folder_scope_never_returns_chunks_from_other_folders(env):
    """US-009 / AC-009-01、US-029 / AC-029-04（重点）：agent 的知识范围仅“产品手册”，提问只在“内部制度”里才有答案 →
    检索结果不含“内部制度”任何片段（答复为“未检索到”提示）；成对正例：范围内内容可检索到。无范围限制的 kb-agent 两者都能检索（对照）。"""
    deps, _api = env
    _scoped_agent(deps)
    tool = _search_tool(deps, "billing-agent")
    out_policy = tool.callable(query=POLICY).content
    assert "内部制度专属内容" not in out_policy and "制度.txt" not in out_policy
    assert "产品手册专属内容" in tool.callable(query=MANUAL).content
    kb = _search_tool(deps, "kb-agent")
    assert "内部制度专属内容" in kb.callable(query=POLICY).content, "对照：未设范围的 agent 可检索全库"


def test_TC_INT_R26_146_empty_scope_returns_zero_hits_and_honest_hint(env):
    """US-009 / AC-009-03：知识范围为空（folders + 空）→ 检索返回 0 片段，不以既有知识冒充；非降级。"""
    deps, _api = env
    put_file(deps, "手册.txt", MANUAL, rel_dirs=("产品手册",), project_id=P)
    from ib.core import KnowledgeScope

    doc, prompts = v2_with_billing(deps, P)
    from dataclasses import replace

    ex = tuple(replace(e, knowledge_scope=KnowledgeScope(mode="folders", folder_ids=())) if e.name == "billing-agent" else e
               for e in doc.experts)
    publish(deps, P, replace(doc, experts=ex), prompts)
    res = _search_tool(deps, "billing-agent").callable(query=MANUAL)
    assert res.ok and not res.degraded and "产品手册专属内容" not in res.content


def test_TC_INT_R26_147_each_agent_only_gets_its_own_granted_tools(env):
    """US-009 / AC-009-02、ADR-61：agent 只拿到自己被授权的工具（不是项目并集）；没有授权的 agent 工具列表为空。"""
    deps, _api = env
    from config_r26_support import expert, make_v2_document, route_graph

    ex = (expert("kb-agent", default=True), expert("bare-agent", keywords=("裸",)))
    doc = make_v2_document(P, ex, route_graph("kb-agent", "bare-agent", default="kb-agent"), grants={"kb-agent": ("search_knowledge",)})
    publish(deps, P, doc, {"bare-agent": PromptLayers("你是 bare。", None)})
    agents = deps.runtime_for(P).compiled.view.agents
    assert [t.name for t in agents["kb-agent"].tools] == ["search_knowledge"]
    assert agents["bare-agent"].tools == ()
    assert agents["bare-agent"].max_steps == 4, "A05：缺省单 agent 步数 4"


def test_TC_INT_R26_148_tool_param_top_k_takes_effect_for_that_agent_only(env):
    """US-007 / AC-007-01：给 billing-agent 的 search_knowledge 设 top_k=1 保存生效 → 该 agent 检索最多 1 条，kb-agent 不受影响。"""
    deps, api = env
    for i in range(4):
        put_file(deps, f"d{i}.txt", f"共同关键内容 同样的句子 变化{i} 空调", project_id=P)
    doc, prompts = v2_with_billing(deps, P)
    from dataclasses import replace

    from ib.core import ToolGrantSpec, ToolParamValue

    grants = tuple(g for g in doc.tool_grants if g.expert_name != "billing-agent") + (
        ToolGrantSpec("billing-agent", ("search_knowledge",), (ToolParamValue("search_knowledge.top_k", "1"),)),)
    assert api.post("/api/config/publish", publish_body(replace(doc, tool_grants=grants), 0, prompts), who="editor").status_code == 200
    q = "共同关键内容 同样的句子 空调"
    one = _search_tool(deps, "billing-agent").callable(query=q).content
    many = _search_tool(deps, "kb-agent").callable(query=q).content
    assert one.count("[1]") == 1 and "[2]" not in one
    assert "[2]" in many
