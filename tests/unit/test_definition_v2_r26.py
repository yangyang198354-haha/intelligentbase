"""[REV-26 / GROUP_D] MOD-R26-04 定义文档 v2：往返、哈希稳定、校验、白名单。

溯源：US-020（AC-020-01/02/03）、US-006（AC-006-03/04）、US-008（AC-008-02）、US-007（AC-007-02）、US-021（AC-021-03）、
US-005（AC-005-02）、US-012（AC-012-01）、US-009（知识范围合法性）。层级：单元（纯函数）。
"""

from __future__ import annotations

import json
from hashlib import sha256

from config_r26_support import SEARCH, doc_json, expert, make_v2_document, prompt_refs, route_graph

from ib.config import (
    build_definition_document,
    document_from_json,
    document_to_json,
    editable_field_whitelist,
    non_editable_changes,
    semantic_hash,
    validate,
    validate_two_domains,
)
from ib.config.definition import upgrade_to_v2
from ib.core import (
    KnowledgeScope,
    OrchestrationSpecInput,
    RouteSpecInput,
    ToolGrantSpec,
    ToolParamValue,
)

TOOLS = frozenset({SEARCH})


def _v1_doc(project="p"):
    from ib.core import ConditionalEdgeSpec, EdgeSpec, ExpertSpecInput

    ex = (
        ExpertSpecInput("kb-agent", "知识库助手", ("知识库", "资料"), (), True, False, True),
        ExpertSpecInput("faq", "常见问题", ("faq",), (), False, False, False),
    )
    orch = OrchestrationSpecInput(
        nodes=("route", "expert", "general", "gate", "aggregate"),
        conditional_edges=(ConditionalEdgeSpec(from_node="route", branch_map=(("expert", "expert"), ("general", "general"))),),
        edges=(
            EdgeSpec("START", "route"), EdgeSpec("expert", "gate"), EdgeSpec("gate", "aggregate"),
            EdgeSpec("general", "aggregate"), EdgeSpec("aggregate", "END"),
        ),
    )
    return build_definition_document(
        project_id=project, experts=ex,
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="kb-agent"),
        orchestration=orch,
        tool_grants=(ToolGrantSpec("kb-agent", (SEARCH,)),),
    )


def _legacy_hash(doc) -> str:
    """独立重算 REV-25 口径的语义哈希（不含任何 REV-26 新键）：验证“存量哈希逐位不变”。"""
    payload = {
        "schema_version": doc.schema_version,
        "project_id": doc.project_id,
        "experts": [
            {"name": e.name, "cn_label": e.cn_label, "keywords": list(e.keywords), "exemplars": list(e.exemplars),
             "is_data_expert": e.is_data_expert, "is_delegating": e.is_delegating, "is_default": e.is_default}
            for e in doc.experts
        ],
        "route": {"tau": doc.route.tau, "margin": doc.route.margin,
                  "max_expert_steps": doc.route.max_expert_steps, "default_expert": doc.route.default_expert},
        "orchestration": {
            "nodes": list(doc.orchestration.nodes),
            "conditional_edges": [{"from_node": c.from_node, "branch_map": [list(b) for b in c.branch_map]}
                                  for c in doc.orchestration.conditional_edges],
            "edges": [{"from_node": e.from_node, "to_node": e.to_node} for e in doc.orchestration.edges],
        },
        "tool_grants": [{"expert_name": g.expert_name, "tool_names": list(g.tool_names),
                         "param_values": [{"name": p.name, "value": p.value} for p in g.param_values]}
                        for g in doc.tool_grants],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + sha256(blob.encode("utf-8")).hexdigest()


def test_TC_UNIT_R26_060_v1_hash_is_bit_identical_to_legacy_formula():
    """US-020 / AC-020-02：存量 v1 文档的语义哈希与 REV-25 口径逐位一致（REV-26 新键仅在非默认值时出现）。"""
    doc = _v1_doc()
    assert doc.content_hash == _legacy_hash(doc)
    assert semantic_hash(doc) == _legacy_hash(doc)


def test_TC_UNIT_R26_061_v1_serialization_has_no_new_keys_and_roundtrips():
    """US-020 / AC-020-02：v1 序列化不含 graph/status/max_steps/knowledge_scope；往返后哈希不变（文件不会被改写）。"""
    doc = _v1_doc()
    payload = json.loads(document_to_json(doc))
    assert "graph" not in payload
    assert all(not ({"status", "max_steps", "knowledge_scope"} & set(e)) for e in payload["experts"])
    back = document_from_json("p", document_to_json(doc))
    assert back.content_hash == doc.content_hash and back.schema_version == 1 and back.graph is None


def test_TC_UNIT_R26_062_upgrade_to_v2_is_pure_equivalent_and_roundtrips():
    """US-020 / AC-020-03：v1 → v2 规范化：专家/路由/授权不变，orchestration 置空，graph 为规范化默认图，往返一致。"""
    v1 = _v1_doc()
    v2 = upgrade_to_v2(v1)
    assert v2.schema_version == 2 and v2.graph is not None
    assert v2.experts == v1.experts and v2.route == v1.route and v2.tool_grants == v1.tool_grants
    assert v2.orchestration.nodes == ()
    assert v1.schema_version == 1, "upgrade_to_v2 不得原地改动 v1 对象"
    assert upgrade_to_v2(v2) is v2
    again = document_from_json("p", document_to_json(v2))
    assert again.content_hash == v2.content_hash and again.graph == v2.graph
    assert validate(v2, known_tools=TOOLS).ok


def test_TC_UNIT_R26_063_v2_new_keys_only_when_non_default():
    """哈希稳定：v2 专家取默认值时不输出 status/max_steps/knowledge_scope；非默认值才出现（且影响哈希）。"""
    plain = make_v2_document("p", (expert("a", default=True), expert("b")))
    pj = doc_json(plain)
    assert all(not ({"status", "max_steps", "knowledge_scope"} & set(e)) for e in pj["experts"])
    tuned = make_v2_document("p", (expert("a", default=True), expert("b", max_steps=3, folders=("f1",))))
    tj = doc_json(tuned)
    b = next(e for e in tj["experts"] if e["name"] == "b")
    assert b["max_steps"] == 3 and b["knowledge_scope"] == {"mode": "folders", "folder_ids": ["f1"]}
    assert plain.content_hash != tuned.content_hash


def test_TC_UNIT_R26_064_position_change_changes_hash_but_not_topology():
    """US-012 / AC-012-01/02：节点位置属文档内容（保存后持久化）；位置变化 → 哈希变化，拓扑与校验结论不变。"""
    from dataclasses import replace

    base = make_v2_document("p", (expert("a", default=True), expert("b")))
    moved_nodes = tuple(replace(n, x=n.x + 50) if n.id == "a" else n for n in base.graph.nodes)
    moved = make_v2_document("p", base.experts, replace(base.graph, nodes=moved_nodes))
    assert moved.content_hash != base.content_hash
    assert {(e.source, e.target, e.branch_key) for e in moved.graph.edges} == {
        (e.source, e.target, e.branch_key) for e in base.graph.edges}
    assert validate(moved, known_tools=TOOLS).ok


def test_TC_UNIT_R26_065_semantic_hash_ignores_updated_at():
    """乐观并发判据：updated_at 不参与语义哈希。"""
    from dataclasses import replace

    d = make_v2_document("p", (expert("a", default=True),))
    assert semantic_hash(replace(d, updated_at="2026-01-01T00:00:00Z")) == semantic_hash(d)


def test_TC_UNIT_R26_066_validate_v2_expert_field_rules():
    """US-008 / AC-008-02、US-005 / AC-005-02：max_steps 范围 1..8；默认专家不得停用；已停用专家不得持有工具授权。"""
    def codes(doc):
        return {e.code for e in validate(doc, known_tools=TOOLS).errors}

    for bad in (0, -1, 9, True):
        d = make_v2_document("p", (expert("a", default=True, max_steps=bad), expert("b")))  # type: ignore[arg-type]
        assert "expert_max_steps_range" in codes(d), bad
    for ok in (1, 4, 8):
        assert "expert_max_steps_range" not in codes(make_v2_document("p", (expert("a", default=True, max_steps=ok),)))
    dis_default = make_v2_document("p", (expert("a", default=True, status="disabled"), expert("b")),
                                   route_graph("b", default="b"))
    assert "expert_default_disabled" in codes(dis_default)
    granted = make_v2_document("p", (expert("a", default=True), expert("b", status="disabled")),
                               route_graph("a"), grants={"a": (SEARCH,), "b": (SEARCH,)})
    assert "tool_grant_expert_disabled" in codes(granted)


def test_TC_UNIT_R26_067_validate_route_params_negative_tau_rejected():
    """US-006 / AC-006-03：tau = -1 → route.tau 路径 + route_threshold_out_of_range。"""
    d = make_v2_document("p", (expert("a", default=True),), tau=-1.0)
    errs = validate(d, known_tools=TOOLS).errors
    assert any(e.path == "route.tau" and e.code == "route_threshold_out_of_range" for e in errs)


def test_TC_UNIT_R26_068_cross_expert_keyword_collision_names_both_experts():
    """US-006 / AC-006-04：同一关键词配在两个专家上 → expert_keyword_collision，消息含涉及的专家。"""
    d = make_v2_document("p", (expert("a", default=True, keywords=("发票",)), expert("b", keywords=("发票",))))
    errs = [e for e in validate(d, known_tools=TOOLS).errors if e.code == "expert_keyword_collision"]
    assert errs and "a" in errs[0].message and "b" in errs[0].message


def test_TC_UNIT_R26_069_tool_param_out_of_range_rejected_by_param_domain():
    """US-007 / AC-007-02：top_k 超出工具声明上限 → 工具参数域拒绝，路径指向该参数。"""
    from ibweb.composition import known_tool_names, known_tool_param_specs

    doc = make_v2_document("p", (expert("a", default=True),), grants={"a": (SEARCH,)})
    from dataclasses import replace

    grant = ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5000"),))
    bad = replace(doc, tool_grants=(grant,))
    rep = validate_two_domains(bad, known_tools=known_tool_names(), tool_param_specs=known_tool_param_specs(),
                           prompt_refs=prompt_refs("a"))
    assert not rep.ok and any("top_k" in e.path or "top_k" in e.message for e in rep.errors)
    ok_grant = ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5"),))
    good = replace(doc, tool_grants=(ok_grant,))
    assert validate_two_domains(good, known_tools=known_tool_names(), tool_param_specs=known_tool_param_specs(),
                           prompt_refs=prompt_refs("a")).ok


def test_TC_UNIT_R26_070_knowledge_scope_invalid_shapes():
    """US-009：知识范围非法形态（all 却带目录 / 未知模式）被拒；folders+空 = 合法的“无知识范围”。"""
    from dataclasses import replace

    base = make_v2_document("p", (expert("a", default=True),))
    def with_scope(ks):
        e = replace(base.experts[0], knowledge_scope=ks)
        return {x.code for x in validate(replace(base, experts=(e,)), known_tools=TOOLS).errors}

    assert "knowledge_scope_invalid" in with_scope(KnowledgeScope(mode="all", folder_ids=("f",)))
    assert "knowledge_scope_invalid" in with_scope(KnowledgeScope(mode="bogus"))  # type: ignore[arg-type]
    assert "knowledge_scope_invalid" not in with_scope(KnowledgeScope(mode="folders", folder_ids=()))


def test_TC_UNIT_R26_071_known_folder_ids_checks_existence():
    """US-025 / AC-025-02、US-009：知识范围引用不存在的目录 → 提供 known_folder_ids 时被拒（校验与装配同入口）。"""
    from dataclasses import replace

    base = make_v2_document("p", (expert("a", default=True, folders=("f1", "ghost")),))
    rep = validate_two_domains(base, known_tools=TOOLS, known_folder_ids=frozenset({"f1"}), prompt_refs=prompt_refs("a"))
    assert not rep.ok
    assert validate_two_domains(replace(base), known_tools=TOOLS, known_folder_ids=frozenset({"f1", "ghost"}),
                               prompt_refs=prompt_refs("a")).ok


def test_TC_UNIT_R26_072_non_editable_changes_v1_v2_rules():
    """US-021 / AC-021-03：v1→v1 拓扑变更仍 field_not_editable；允许 1→2（带 graph）；禁止 2→1 降级与 project_id 变更。"""
    from dataclasses import replace

    from ib.core import EdgeSpec

    v1 = _v1_doc()
    v2 = upgrade_to_v2(v1)
    assert non_editable_changes(v1, v2) == ()
    assert {i.code for i in non_editable_changes(v2, v1)} == {"field_not_editable"}
    tampered = replace(v1, orchestration=replace(v1.orchestration, edges=v1.orchestration.edges + (EdgeSpec("general", "gate"),)))
    assert any(i.path == "orchestration" for i in non_editable_changes(v1, tampered))
    assert any(i.path == "project_id" for i in non_editable_changes(v1, replace(v1, project_id="other")))
    assert non_editable_changes(v1, replace(v2, graph=None)) != ()  # 声明 v2 却不带 graph → 不是合法升级


def test_TC_UNIT_R26_073_whitelist_has_new_fields_and_no_temperature():
    """US-021 / AC-021-03、US-006 / AC-006-03：白名单含 REV-26 新增字段；没有 temperature 的入口。"""
    wl = editable_field_whitelist()
    assert {"experts[].status", "experts[].max_steps", "experts[].knowledge_scope", "graph", "graph.nodes",
            "graph.edges"} <= set(wl)
    assert not any("temperature" in f for f in wl)


def test_TC_UNIT_R26_074_tool_grants_hash_covers_param_values():
    """AC-007-01：改工具参数必须改变语义哈希（否则乐观并发形同虚设）。"""
    from dataclasses import replace

    d = make_v2_document("p", (expert("a", default=True),))
    changed = replace(d, tool_grants=(ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5"),)),))
    assert semantic_hash(changed) != semantic_hash(d)
