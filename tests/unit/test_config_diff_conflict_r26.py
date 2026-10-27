"""[REV-26 / GROUP_D] MOD-R26-05 版本化纯函数：快照 / 清单哈希 / 差异 / 三方冲突 / 提示词文本校验。

溯源：US-016（AC-016-01/03）、US-018（AC-018-01）、US-012（布局差异）、US-019（AC-019-03/04）、US-023（AC-023-01 摘要）。
层级：单元（纯函数）。
"""

from __future__ import annotations

from dataclasses import replace

from config_r26_support import SEARCH, expert, make_v2_document

from ib.config.versioning import (
    PROMPT_LAYER_MAX_CHARS,
    build_snapshot,
    detect_conflicts,
    diff_snapshots,
    is_layout_only,
    manifest_hash,
    snapshot_from_json,
    snapshot_to_json,
    summarize_diff,
    validate_prompt_texts,
)
from ib.core import PromptLayers, ToolGrantSpec, ToolParamValue


def _snap(experts=None, prompts=None, **kw):
    experts = experts or (expert("a", default=True), expert("b"))
    doc = make_v2_document("p", experts, **kw)
    layers = prompts if prompts is not None else {e.name: PromptLayers(f"{e.name} 主提示词", None) for e in experts}
    return build_snapshot(doc, layers)


def test_TC_UNIT_R26_080_snapshot_json_roundtrip_and_manifest_hash_stable():
    """US-017 / AC-017-02：快照往返不丢字段，清单哈希稳定（回滚得到“内容一致”的版本的判据）。"""
    s = _snap()
    back = snapshot_from_json(snapshot_to_json(s))
    assert manifest_hash(back) == manifest_hash(s)
    assert back.prompts == s.prompts and back.definition.graph == s.definition.graph


def test_TC_UNIT_R26_081_manifest_hash_covers_prompts():
    """清单哈希含提示词两层：仅改提示词文本也改变哈希。"""
    a = _snap()
    b = _snap(prompts={"a": PromptLayers("changed", None), "b": PromptLayers("b 主提示词", None)})
    assert manifest_hash(a) != manifest_hash(b)


def test_TC_UNIT_R26_082_diff_added_agent_and_tool_grant_summary():
    """US-016 / AC-016-01：新增 1 个 agent + 修改 1 处工具授权 → 差异含 agent_added、tool_grant（+工具名）。"""
    base = _snap()
    new_experts = (expert("a", default=True), expert("b"), expert("billing", label="账单助手"))
    doc = make_v2_document("p", new_experts, grants={"a": (SEARCH,), "b": (SEARCH,), "billing": (SEARCH,)})
    new = build_snapshot(doc, {**dict(base.prompts), "billing": PromptLayers("账单", None)})
    items = diff_snapshots(base, new)
    kinds = {(i.kind, i.object_id) for i in items}
    assert ("agent_added", "billing") in kinds
    assert ("tool_grant", "billing") in kinds
    assert any(i.kind == "node_added" and i.object_id == "billing" for i in items)
    summary = summarize_diff(items)
    assert "新增 agent billing" in summary and "修改 工具授权 billing" in summary


def test_TC_UNIT_R26_083_diff_prompt_shows_digest_not_text():
    """US-019 / AC-019-03：差异中提示词只给“长度 + 哈希前 8 位”，不含正文。"""
    secret_text = "秘密提示词正文-" + "x" * 40
    base = _snap()
    new = _snap(prompts={"a": PromptLayers(secret_text, None), "b": PromptLayers("b 主提示词", None)})
    items = [i for i in diff_snapshots(base, new) if i.kind == "prompt"]
    assert len(items) == 1 and items[0].object_id == "a" and items[0].field == "main"
    assert "长度" in (items[0].after or "") and "哈希" in (items[0].after or "")
    assert secret_text not in (items[0].before or "") + (items[0].after or "")
    assert secret_text not in summarize_diff(tuple(items))


def test_TC_UNIT_R26_084_diff_is_deterministic_and_empty_for_identical():
    """AC-016-03：无改动 → 空差异且摘要为“无变更”；同输入同输出。"""
    s = _snap()
    assert diff_snapshots(s, s) == ()
    assert summarize_diff(()) == "无变更"
    t = _snap(experts=(expert("a", default=True, max_steps=3), expert("b")))
    assert diff_snapshots(s, t) == diff_snapshots(s, t)


def test_TC_UNIT_R26_085_layout_only_detection():
    """US-012：只移动节点 → 差异全为 layout，is_layout_only 为真；混有其他差异则为假。"""
    s = _snap()
    nodes = tuple(replace(n, x=n.x + 40) if n.id == "a" else n for n in s.definition.graph.nodes)
    moved = build_snapshot(make_v2_document("p", s.definition.experts, replace(s.definition.graph, nodes=nodes)), dict(s.prompts))
    items = diff_snapshots(s, moved)
    assert items and is_layout_only(items)
    assert not is_layout_only(items + (diff_snapshots(s, _snap(experts=(expert("a", default=True, max_steps=2), expert("b"))))[0],))
    assert is_layout_only(()) is False


def test_TC_UNIT_R26_086_diff_covers_param_route_scope_and_status():
    """US-007/008/009/005：工具参数、最大步数、路由参数、知识范围、停用状态都出现在差异里。"""
    s = _snap()
    ex = (expert("a", default=True, max_steps=2, folders=("f1",)), expert("b", status="disabled"))
    doc = make_v2_document("p", ex, grants={"a": (SEARCH,)}, tau=0.7)
    doc = replace(doc, tool_grants=(ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5"),)),))
    new = build_snapshot(doc, {"a": PromptLayers("a 主提示词", None), "b": PromptLayers("b 主提示词", None)})
    kinds = {i.kind for i in diff_snapshots(s, new)}
    assert {"agent_field", "knowledge_scope", "agent_disabled", "tool_param", "route_param"} <= kinds


def test_TC_UNIT_R26_087_conflict_only_when_both_sides_touch_same_object():
    """US-018 / AC-018-01：甲、乙都改了同一对象才冲突；各改各的不冲突（不做自动合并）。"""
    base = _snap()
    head = _snap(experts=(expert("a", default=True, max_steps=2), expert("b")))     # 甲改 a
    sub_same = _snap(experts=(expert("a", default=True, max_steps=5), expert("b")))  # 乙也改 a
    sub_other = _snap(experts=(expert("a", default=True), expert("b", max_steps=3)))  # 乙改 b
    hit = detect_conflicts(base, head, sub_same)
    assert hit.base_available and [(c.kind, c.object_id) for c in hit.conflicts] == [("agent", "a")]
    assert "max_steps" in hit.conflicts[0].fields
    assert detect_conflicts(base, head, sub_other).conflicts == ()


def test_TC_UNIT_R26_088_conflict_with_pruned_base_degrades_to_all_differences():
    """基线版本已被修剪（base=None）→ base_available=False，退化为 head 与提交之间的全部差异对象。"""
    head = _snap(experts=(expert("a", default=True, max_steps=2), expert("b")))
    sub = _snap(experts=(expert("a", default=True, max_steps=5), expert("b")))
    r = detect_conflicts(None, head, sub)
    assert r.base_available is False and any(c.object_id == "a" for c in r.conflicts)


def test_TC_UNIT_R26_089_validate_prompt_texts_rules():
    """US-019 / AC-019-04：提示词 >20000 字符被拒（含字段名与上限）；兜底层空白被拒；启用专家两层皆缺被拒；孤儿层被拒。"""
    ex = (expert("a", default=True), expert("b", status="disabled"))
    too_long = "x" * (PROMPT_LAYER_MAX_CHARS + 1)
    errs = validate_prompt_texts({"a": PromptLayers(too_long, None)}, experts=ex)
    hit = [e for e in errs if e.code == "prompt_too_long"]
    assert hit and hit[0].path == "prompts[a].main" and str(PROMPT_LAYER_MAX_CHARS) in hit[0].message
    assert too_long not in hit[0].message
    assert validate_prompt_texts({"a": PromptLayers("x" * PROMPT_LAYER_MAX_CHARS, None)}, experts=ex) == ()  # 边界：恰好上限
    codes = {e.code for e in validate_prompt_texts({"a": PromptLayers("ok", "   ")}, experts=ex)}
    assert "prompt_fallback_empty" in codes
    assert {e.code for e in validate_prompt_texts({"a": PromptLayers(None, None)}, experts=ex)} == {"prompt_missing"}
    assert "prompt_orphan_expert" in {e.code for e in validate_prompt_texts(
        {"a": PromptLayers("ok", None), "b": PromptLayers("x", None)}, experts=ex)}


def test_TC_UNIT_R26_090_summary_capped_at_200_chars():
    """AC-017-01：变更摘要一句话且 ≤200 字符。"""
    base = _snap()
    many = tuple(expert(f"n{i}", default=(i == 0)) for i in range(40))
    doc = make_v2_document("p", many)
    new = build_snapshot(doc, {e.name: PromptLayers("t", None) for e in many})
    assert len(summarize_diff(diff_snapshots(base, new))) <= 200
