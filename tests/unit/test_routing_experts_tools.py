"""单元测试层 2/N —— 语义路由 / 意图路由 / 专家注册表 / 工具绑定 / 护栏。

覆盖 AC-IB-09-01~07、AC-IB-10-01~05、AC-IB-15-02/03；全部纯逻辑、离线。
"""

from __future__ import annotations

import pytest

# --------------------------------------------------------------------------- #
# MOD-IB-18 语义路由纯函数（IFC-IB-191/192；AC-IB-15-03）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_023_cosine_properties():
    """[TC-UNIT-023] 余弦：同向=1、正交=0、零向量不除零、维度不符报错。"""
    from ib.routing.semantic import cosine

    assert cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 2.0])


def test_TC_UNIT_024_score_experts_takes_max():
    """[TC-UNIT-024] 每专家取「范例最大余弦」；空范例不参与。"""
    from ib.routing.semantic import score_experts

    scores = score_experts([1.0, 0.0], {"a": [[1.0, 0.0], [0.0, 1.0]], "b": [], "c": [[0.0, 1.0]]})
    assert scores["a"] == pytest.approx(1.0)
    assert scores["c"] == pytest.approx(0.0)
    assert "b" not in scores


def test_TC_UNIT_025_decide_tau_and_margin():
    """[TC-UNIT-025] decide 的两个门限：低于 tau 穿透；分差不足穿透。"""
    from ib.routing.semantic import decide

    assert decide({"a": 0.9, "b": 0.1}, tau=0.65, margin=0.05) == "a"
    assert decide({"a": 0.5, "b": 0.1}, tau=0.65, margin=0.05) is None  # 不过 tau
    assert decide({"a": 0.9, "b": 0.88}, tau=0.65, margin=0.05) is None  # 分差不足（复合意图）
    assert decide({}, tau=0.65, margin=0.05) is None


def test_TC_UNIT_026_semantic_router_project_partition_and_failopen():
    """[TC-UNIT-026] 语义路由按项目分区；装载/推理失败一律穿透 None（FM-6）。"""
    from ib.core import Scope
    from ib.routing.semantic import SemanticRouter

    exemplars = {"p_alpha": {"data-expert": ["能耗数据"]}}
    router = SemanticRouter(
        embed_texts=lambda texts: [[1.0, 0.0] for _ in texts],
        exemplars_provider=lambda pid: exemplars.get(pid, {}),
    )
    assert router.route("能耗", scope=Scope(project_id="p_alpha")) == "data-expert"
    # 未登记项目的范例：不得回落他项目 → None
    assert router.route("能耗", scope=Scope(project_id="p_beta")) is None

    def _boom(texts):
        raise RuntimeError("embed down")

    broken = SemanticRouter(embed_texts=_boom, exemplars_provider=lambda pid: {"data-expert": ["x"]})
    assert broken.route("x", scope=Scope(project_id="p_alpha")) is None
    assert broken.scores_for("x", scope=Scope(project_id="p_alpha")) == {}


# --------------------------------------------------------------------------- #
# MOD-IB-19 意图路由（IFC-IB-201/202/203；AC-IB-09-01~07）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_027_parse_route_output_dirty():
    """[TC-UNIT-027] 脏输出解析：代码围栏 / 散文 / 非法名 / 空数组（AC-IB-15-03）。"""
    from ib.routing.intent import parse_route_output, parse_route_output_ex

    assert parse_route_output('```json\n["data-expert"]\n```') == ["data-expert"]
    assert parse_route_output('好的，结果是 ["inspection-expert", "knowledge-expert"] 请查收') == [
        "inspection-expert",
        "knowledge-expert",
    ]
    # 非法专家名被过滤
    assert parse_route_output('["nonexistent-expert"]') == []
    # 畸形输入不抛异常
    assert parse_route_output("完全没有数组") == []
    assert parse_route_output("") == []
    # 空数组 → saw_array=True（可信 OOD 信号），但无专家
    names, saw = parse_route_output_ex("[]")
    assert names == [] and saw is True
    _, saw2 = parse_route_output_ex("没有数组")
    assert saw2 is False


def test_TC_UNIT_028_current_query_strips_history():
    """[TC-UNIT-028] 路由输入剥离历史前缀，只留当前提问。"""
    from ib.routing.intent import current_query

    text = "[历史对话]用户：能耗多少\n助手：100\n[历史对话]用户：那上个季度呢\n用户：现在呢"
    stripped = current_query(text)
    assert "现在呢" in stripped
    assert "能耗多少" not in stripped


def test_TC_UNIT_029_keyword_unique_single_expert():
    """[TC-UNIT-029] 关键词唯一命中 → 恰选一个专家，无额外分支（AC-IB-09-01）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    decision = IntentRouter().classify_experts("设备故障怎么排查", scope=Scope(project_id="p1"))
    assert decision.experts == ["inspection-expert"]
    assert decision.tier == "L0_keyword_unique"


def test_TC_UNIT_030_composite_multi_expert_parallel_candidates():
    """[TC-UNIT-030] 复合问题选中多专家（AC-IB-09-02 的选路侧）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    decision = IntentRouter().classify_experts("能耗数据和设备故障一起看看", scope=Scope(project_id="p1"))
    assert set(decision.experts) >= {"data-expert", "inspection-expert"}, decision.experts
    assert len(decision.experts) <= 3


def test_TC_UNIT_031_never_empty_answer():
    """[TC-UNIT-031] 任何输入都不得出现无人应答（AC-IB-09-04）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    for query in ("随便聊聊天气", "……", "?????", "一个完全没有任何领域信号的问题"):
        decision = IntentRouter().classify_experts(query, scope=Scope(project_id="p1"))
        assert decision.experts, f"出现无人应答：{query!r}"
        assert decision.tier == "default"


def test_TC_UNIT_032_ood_when_allowed():
    """[TC-UNIT-032] LLM 明确空数组 + allow_ood → OOD（纯寒暄，AC-IB-09-06）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    class _Llm:
        def build_router(self):
            class _R:
                impl = staticmethod(lambda prompt: "[]")

            return _R()

    router = IntentRouter(llm_provider=_Llm())
    assert router.classify_experts("你好", scope=Scope(project_id="p1"), allow_ood=True).tier == "ood"
    # 不允许 OOD 时退回默认专家（保守：宁可多用一个专家）
    assert router.classify_experts("你好", scope=Scope(project_id="p1")).experts == ["data-expert"]


def test_TC_UNIT_033_llm_failure_falls_back_deterministically():
    """[TC-UNIT-033] 路由 LLM 调不动时回退关键词，仍不得无人应答（AC-IB-09-04）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    class _BrokenLlm:
        def build_router(self):
            raise RuntimeError("router unavailable")

    decision = IntentRouter(llm_provider=_BrokenLlm()).classify_experts(
        "设备故障", scope=Scope(project_id="p1")
    )
    assert decision.experts == ["inspection-expert"]


def test_TC_UNIT_034_sticky_expert_from_history():
    """[TC-UNIT-034] 零信号追问承接上一轮专家（AC-IB-09-05）。"""
    from ib.core import Message, Scope
    from ib.routing.intent import IntentRouter

    history = [Message(role="user", content="设备故障怎么处理"), Message(role="assistant", content="…")]
    decision = IntentRouter().classify_experts(
        "那再详细点", history=history, scope=Scope(project_id="p1")
    )
    assert decision.experts == ["inspection-expert"]
    assert decision.tier == "sticky"


def test_TC_UNIT_035_guard_reroutes_to_data_expert():
    """[TC-UNIT-035] 护栏：无工具专家接了数据问题且语义高置信指向数据专家 → 改派（IFC-IB-203）。"""
    from ib.core import RouteDecision
    from ib.routing.intent import guard_against_misroute

    decision = RouteDecision(experts=["knowledge-expert"], tier="L2_llm", confidence=0.0)
    scores = {"data-expert": 0.9, "knowledge-expert": 0.1}
    fixed = guard_against_misroute(decision, scores)
    assert fixed.experts == ["data-expert"]
    assert fixed.tier == "L3_keyword_fallback"
    # 无证据时不介入（护栏不得成为新的误路由源）
    assert guard_against_misroute(decision, {}).experts == ["knowledge-expert"]


def test_TC_UNIT_036_router_determinism_same_input_same_route():
    """[TC-UNIT-036] 同一问题重复提交得到相同路由（AC-IB-09-07）。"""
    from ib.core import Scope
    from ib.routing.intent import IntentRouter

    router = IntentRouter()
    results = {tuple(router.classify_experts("能耗看板", scope=Scope(project_id="p1")).experts) for _ in range(5)}
    assert results == {("data-expert",)}


# --------------------------------------------------------------------------- #
# MOD-IB-16 专家注册表（IFC-IB-171~179；AC-IB-10-01/04）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_037_expert_registry_and_derived_views():
    """[TC-UNIT-037] 注册表单一真源：顺序稳定，派生视图自动包含（AC-IB-10-01/04）。"""
    from ib import experts

    first = experts.names()
    assert first == experts.names(), "顺序不稳定"
    assert experts.default_expert() in first
    assert set(experts.keywords_map()) == set(first)
    assert set(experts.cn_map()) == set(first)
    assert set(experts.fallback_prompts()) == set(first)
    assert set(experts.data_experts()) <= set(first)
    # 默认专家恰好一个
    assert sum(1 for s in experts.EXPERT_SPECS if s.is_default) == 1


def test_TC_UNIT_038_validate_specs_rejects_bad_registry():
    """[TC-UNIT-038] 结构性约束校验：空表 / 重名 / 零个或多个默认专家（AC-IB-10-04）。"""
    from ib.core import ExpertSpec
    from ib.experts import validate_specs

    def spec(name, default=False):
        return ExpertSpec(
            name=name, cn_label=name, keywords=(f"k{name}",), is_data_expert=False,
            fallback_prompt="p", is_delegating=False, is_default=default,
        )

    with pytest.raises(ValueError):
        validate_specs([])
    with pytest.raises(ValueError):
        validate_specs([spec("a", True), spec("a")])
    with pytest.raises(ValueError):
        validate_specs([spec("a"), spec("b")])  # 无默认
    with pytest.raises(ValueError):
        validate_specs([spec("a", True), spec("b", True)])  # 两个默认
    validate_specs([spec("a", True), spec("b")])  # 合法


def test_TC_UNIT_039_get_missing_expert_returns_none():
    """[TC-UNIT-039] 取不存在的专家返回 None 而非抛异常（路由优雅未命中）。"""
    from ib.experts import get

    assert get("definitely-not-an-expert") is None
    assert get("data-expert") is not None


# --------------------------------------------------------------------------- #
# MOD-IB-17 工具绑定（IFC-IB-181/182/183；AC-IB-10-03）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_040_capability_digest_from_registry():
    """[TC-UNIT-040] 能力摘要由注册表派生，缺失描述返回空串不抛错（AC-IB-10-03）。"""
    from ib.core import ToolSpec, ToolResult
    from ib.tools import ToolRegistry, build_capability_digest

    registry = ToolRegistry()
    registry.register(
        ToolSpec(name="query_metrics", description="查询设备实时指标", needs_scope=True),
        lambda **kw: ToolResult(ok=True, content="ok"),
    )
    digest = build_capability_digest(registry)
    assert "query_metrics" in digest and "查询设备实时指标" in digest
    assert "需要范围绑定" in digest

    class _Boom:
        def registered(self):
            raise RuntimeError("registry broken")

    assert build_capability_digest(_Boom()) == ""


def test_TC_UNIT_041_bind_scope_override_impossible():
    """[TC-UNIT-041] 构造期绑定是唯一真源，调用方传 scope 无法覆盖（AC-IB-10-03 / 跨项目防线）。"""
    from ib.core import Scope, ToolResult, ToolSpec
    from ib.tools import ToolRegistry, bind_scope

    seen: list[str] = []

    class _RecordingRetrieval:
        def search_as_tool(self, query, *, scope):
            seen.append(scope.project_id)
            return ToolResult(ok=True, content="hit")

    def _impl(query, *, scope, retrieval):
        return retrieval.search_as_tool(query, scope=scope)

    registry = ToolRegistry()
    registry.register(ToolSpec(name="t", description="d", needs_scope=True), _impl)
    tool = bind_scope(registry.registered(), Scope(project_id="p_alpha"), _RecordingRetrieval())[0]
    tool.callable("问题", scope=Scope(project_id="p_beta"))
    assert seen == ["p_alpha"], f"调用方 scope 覆盖了构造期绑定：{seen}"


def test_TC_UNIT_042_bind_scope_hides_scope_params():
    """[TC-UNIT-042] 已绑定工具不暴露 scope/retrieval 参数（ADR-09 结构性保证）。"""
    import inspect

    from ib.core import Scope, ToolResult, ToolSpec
    from ib.tools import ToolRegistry, bind_scope

    registry = ToolRegistry()
    registry.register(
        ToolSpec(name="search", description="d", needs_scope=True),
        lambda query="", *, scope, retrieval: ToolResult(ok=True, content="x"),
    )
    tool = bind_scope(registry.registered(), Scope(project_id="p1"), object())[0]
    params = set(inspect.signature(tool.callable).parameters)
    assert not ({"scope", "retrieval"} & params), params
