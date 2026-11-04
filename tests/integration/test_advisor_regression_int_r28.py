"""[REV-28 / GROUP_D] 集成：未启用顾问项目的“同输入逐字相同”回归集（REQ-NFUNC-001 / GR-C-001 条件 2）。

分层：integration（真实装配 + 真实运行时 + 真实 HTTP 视图；LLM 为内置离线替身 / 脚本化替身）。
黄金文件 `advisor_r28_baseline_golden.json` 由**基线 commit 8d6fd4b 的 src 树**运行 `tests/advisor_r28_probe_support.py` 生成
（`git archive 8d6fd4b src` 解出），期望值**不是**用被测代码生成的；本文件用当前 src 重跑探针并逐项比对。
唯一允许的差异：可授权工具列表 / 参数规格恰好多出 web_search、web_fetch 及其参数（AC-017-05，展示变化，行为零变化）；
配置目录响应仅追加 builtin_agents / web 两个键（顾问入口所需，非行为变化）。
溯源：AC-017-01 ~ 017-05、AC-010-05、AC-001-03、AC-003-04。
"""

from __future__ import annotations

import json
import os

import pytest
from advisor_r28_support import (
    KB_TEXT,
    P,
    FakeTransport,
    ScriptedLlm,
    advisor_document,
    faithful_advisor,
    html_page,
    publish_advisor,
    raw_events,
    resolver_map,
    set_web,
    table_understander,
    understanding,
    web_outcome,
)

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "advisor_r28_baseline_golden.json")


@pytest.fixture(scope="module")
def golden():
    with open(GOLDEN_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def current(django_ready):
    from advisor_r28_probe_support import run_probe

    return run_probe()


def test_TC_INT_R28_100_unadvised_project_33_questions_identical_answers_events_routing_and_outbound_payloads(golden, current):
    """AC-017-01：N=33(≥30) 条代表性问句——答复文本、流式事件序列、路由（LLM 路由提示词哈希）、外发给 LLM 的载荷
    （专家系统提示词哈希 + 用户提示词原文）与基线逐项一致。"""
    g, c = golden["per_question"], current["per_question"]
    assert len(g) >= 30 and len(g) == len(c)
    assert golden["questions"] == current["questions"]
    for a, b in zip(g, c):
        assert a["q"] == b["q"]
        assert a["events"] == b["events"], a["q"]
        assert a["llm_calls"] == b["llm_calls"], a["q"]
        assert a["router_prompts"] == b["router_prompts"], a["q"]
    # 非平凡：基线每条问句确实产生了专家调用与 content 事件（避免“空对空相等”）
    assert all(any(e[0] == "content" and e[1] for e in x["events"]) for x in g)
    assert sum(len(x["llm_calls"]) for x in g) >= 30


def test_TC_INT_R28_101_healthz_deps_egress_declaration_equals_baseline_and_has_no_search_host(golden, current):
    """AC-017-02：GET /healthz/deps 数据外发声明与基线一致，未出现搜索服务主机（未配置联网时 egress_web 为空 ⇒ 不追加键）。"""
    assert current["healthz_deps"] == golden["healthz_deps"]
    blob = json.dumps(current["healthz_deps"], ensure_ascii=False)
    assert "fake.invalid" not in blob and "web_search" not in blob and "web_fetch" not in blob


def test_TC_INT_R28_102_definition_default_graph_validation_grants_seeds_byte_identical(golden, current):
    """AC-017-03 / AC-001-03 / AC-003-04：kb-agent 种子、默认授权、运行参数、定义文档、默认图、校验结果与基线逐项（字节）相同；
    专家注册表不含顾问；运行时视图无 advisor_id。"""
    for key in ("definition_json", "validate_default_graph", "default_graph", "tool_grants", "kb_seed_hash", "expert_specs",
                "agents_prompt_hash", "agents_tools", "prompts_experts", "view_advisor_id", "config_version"):
        assert current[key] == golden[key], key
    assert golden["validate_default_graph"] == []
    assert [e[0] for e in current["expert_specs"]] == ["kb-agent"] and current["view_advisor_id"] is None
    assert current["agents_tools"] == {"kb-agent": ["search_knowledge"]}
    assert current["tool_grants"] == [["kb-agent", ["search_knowledge"], []]]


def test_TC_INT_R28_103_authorizable_tool_list_gains_exactly_web_search_and_web_fetch_rest_unchanged(golden, current):
    """AC-017-05：配置页“可授权工具”列表恰好多出 web_search、web_fetch 2 项，其余项与顺序不变；参数规格同口径（仅新增 web_* 前缀项）。"""
    base_tools, now_tools = golden["prompts_available_tools"], current["prompts_available_tools"]
    assert base_tools == ["search_knowledge"]
    assert [t for t in now_tools if t not in ("web_search", "web_fetch")] == base_tools  # 其余项与顺序不变
    assert sorted(set(now_tools) - set(base_tools)) == ["web_fetch", "web_search"] and len(now_tools) == len(base_tools) + 2
    base_specs, now_specs = golden["prompts_tool_param_specs"], current["prompts_tool_param_specs"]
    assert [s for s in now_specs if s.startswith("search_knowledge.")] == base_specs
    assert {s.split(".")[0] for s in now_specs} == {"search_knowledge", "web_search", "web_fetch"}
    assert current["prompts_keys"] == golden["prompts_keys"]


def test_TC_INT_R28_104_catalog_response_only_gains_builtin_agents_and_web_keys(golden, current):
    """配置目录响应仅追加 builtin_agents / web 两个键（AC-001-01 顾问入口所需）；既有键不变。"""
    assert set(golden["catalog_keys"]) <= set(current["catalog_keys"])
    assert sorted(set(current["catalog_keys"]) - set(golden["catalog_keys"])) == ["builtin_agents", "web"]


def test_TC_INT_R28_105_unadvised_project_30_questions_never_call_web_tools_nor_expose_them_to_agents(accounts_app, monkeypatch):
    """AC-017-05 行为面：联网替身（搜索提供方 / 抓取传输）已装配，但未启用顾问且从未授权联网工具的项目，N=30 条问句——
    两项联网工具调用次数 = 0（提供方调用 0、出站请求 0），未授权 agent 的函数调用工具列表中两项出现 0 次；答复不含顾问/致歉文案；理解步骤 0 次。"""
    from ib.advisor import ADVISOR_APOLOGY_TEXT
    from ib.webtools.fetch import SafeFetcher
    from ib.webtools.search import FakeSearchProvider

    deps, _ = accounts_app
    prov = FakeSearchProvider([web_outcome(("x", "y", "https://z.example.com/"))] * 40)
    tr = FakeTransport({"example.com": html_page("t", "b")})
    set_web(deps, provider=prov, fetcher=SafeFetcher(transport=tr, resolver=resolver_map({}, default=("93.184.216.34",))))
    seen_tools = []

    def kb(c):
        seen_tools.append(tuple(c.tool_names))
        return "KB:" + c.prompt[:20]

    llm = ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": kb}, understander=lambda p: (_ for _ in ()).throw(AssertionError("不应调用理解步骤")))
    questions = [f"代表性问句 {i}：退货 保修 运费 发票" if i % 2 else f"请问第 {i} 个问题 http://127.0.0.1/ 联网查一下" for i in range(30)]
    for i, q in enumerate(questions):
        ev = raw_events(deps, P, q, f"u{i}")
        cs = [str(e.data) for e in ev if str(e.kind) == "content"]
        assert len(cs) == 1 and ADVISOR_APOLOGY_TEXT not in cs[0] and "KB:" in cs[0]
    assert len(seen_tools) == 30 and set(seen_tools) == {("search_knowledge",)}
    assert prov.calls == [] and tr.count == 0 and llm.understand_prompts == []


def test_TC_INT_R28_106_kb_agent_path_identical_with_and_without_advisor_in_project(accounts_app, monkeypatch):
    """AC-017-04：已启用顾问的项目，kb-agent 的系统提示词、工具授权、步数、收到的问题——与未启用时逐项一致；顾问的存在不影响 kb-agent 路径。"""
    deps, _ = accounts_app
    calls0 = []
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: (calls0.append((c.prompt, tuple(c.tool_names))), KB_TEXT)[1]})
    raw_events(deps, P, "退货期限是多久", "n0")
    v0 = deps.runtime_for(P).compiled.view
    sys0, tools0, steps0 = v0.agents["kb-agent"].system_prompt, [t.name for t in v0.agents["kb-agent"].tools], v0.agents["kb-agent"].max_steps
    publish_advisor(deps, P)
    calls1 = []
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: (calls1.append((c.prompt, tuple(c.tool_names))), KB_TEXT)[1], "advisor": faithful_advisor()},
                understander=table_understander({"退货期限是多久": understanding(("knowledge",), "退货期限是多久", "退货期限是多久")}))
    raw_events(deps, P, "退货期限是多久", "n1")
    v1 = deps.runtime_for(P).compiled.view
    a = v1.agents["kb-agent"]
    assert a.system_prompt.strip() and v1.advisor_id == "advisor"
    assert [t.name for t in a.tools] == tools0 == ["search_knowledge"] and a.max_steps == steps0
    assert calls1 == calls0 and len(calls0) == 1  # 收到的问题（含 prompt 字节）与工具列表完全相同
    assert "advisor" not in [t for t in tools0]


def test_TC_INT_R28_107_adding_advisor_does_not_change_other_agents_or_default_expert(accounts_app):
    """AC-001-03 / 003-01：未加入顾问的项目，专家集合 / 工具授权与升级前逐项相同、顾问不出现在专家列表 / 路由候选；加入后才出现。"""
    deps, _ = accounts_app
    v = deps.runtime_for(P).compiled.view
    assert [s.name for s in v.experts] == ["kb-agent"] and v.advisor_id is None and v.default_expert == "kb-agent"
    publish_advisor(deps, P)
    v2 = deps.runtime_for(P).compiled.view
    assert [s.name for s in v2.experts] == ["kb-agent", "advisor"] and v2.advisor_id == "advisor" and v2.default_expert == "kb-agent"
    assert [s.name for s in deps.runtime_for("p_beta").compiled.view.experts] == ["kb-agent"]  # 其它项目不受影响
