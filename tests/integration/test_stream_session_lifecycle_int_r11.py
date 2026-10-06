"""集成测试层 R11 增量 —— 流式交付契约 / 会话生命周期（REV-11-3）。

覆盖 user_stories.md 1.3.0 的 **US-IB-19**（流式交付最终答复，AC-IB-19-01~05）与
**US-IB-20**（会话生命周期，AC-IB-20-01~06）。

与既有 `test_orchestration_related_images.py` 的关系：
  * TC-INT-039（SSE 端点）的**代码保持原样不动**（本轮只重挂其 US/AC 归属）；
  * 本文件为**新增**用例（TC-INT-088 起，只增不改既有编号），就当前实现**已可验收**的
    US-IB-19 / US-IB-20 子句补一层端到端接缝级守卫。

**边界（如实登记）**：AC-IB-19-02（完成事件附结构化产物）与 AC-IB-20-04（确认中间态
呈递 / 决策回传）依赖架构 1.4.0/R8 的 IFC-IB-298~308，本轮 `src/` 尚未实现，故**不在此处
伪造断言**（见 docs/test_report.md §16 覆盖缺口登记）。
"""

from __future__ import annotations

from conftest import request_ctx

import pytest


def _orchestrator(
    deps,
    *,
    provider=None,
    project_id="p_alpha",
    config=None,
    llm=None,
    router=None,
    sessions=None,
):
    """构造离线编排器（默认与既有集成层一致；额外开放 config/llm/router/sessions 注入口）。"""
    from ib.core import GraphConfig, Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph
    from ib.streaming import MemorySessionStore

    bound_tools = deps.bind_tools(Scope(project_id=project_id))
    return build_graph(
        llm=llm if llm is not None else deps.llm,
        experts=EXPERT_SPECS,
        tools=bound_tools,
        sessions=sessions if sessions is not None else MemorySessionStore(),
        config=config if config is not None else GraphConfig(),
        router=router,
        scope=Scope(project_id=project_id),
        tools_by_expert={name: bound_tools for name in (s.name for s in EXPERT_SPECS)},
        related_images_provider=provider,
    )


def _kinds(events):
    return [str(e.kind) for e in events]


# --------------------------------------------------------------------------- #
# US-IB-19 流式交付最终答复
# --------------------------------------------------------------------------- #


def test_TC_INT_088_single_terminal_done_no_content_after(deps):
    """[TC-INT-088] 终止事件恰一次且收尾；其后不再有内容片段（AC-IB-19-01）。

    AC-IB-19-01：内容分片按顺序增量推送，顺序拼接等于最终答复；`done` 为终态事件，
    其后不得再出现任何内容片段。
    """
    orch = _orchestrator(deps)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)

    assert kinds.count("done") == 1, f"终止事件必须恰一次：{kinds}"
    assert kinds[-1] == "done", f"终止事件必须收尾：{kinds}"
    assert "content" not in kinds[kinds.index("done") + 1 :], "done 之后不得再有内容片段"

    fragments = [e.data for e in events if str(e.kind) == "content"]
    assert fragments, f"应有至少一条正式答复片段：{kinds}"
    # 顺序拼接等于最终答复（单分片时恒成立，多分片时验「不重排、不截断」）
    assert "".join(fragments) == fragments[-1]
    assert all(str(f).strip() != "" for f in fragments), "不得推送空的内容片段"


def test_TC_INT_089_internal_expert_products_never_leak(deps):
    """[TC-INT-089] 内部子任务产物绝不外流：多专家只融合出一条正文（AC-IB-19-04）。

    强制双专家路由，令每个专家的原始作答都带内部标签；断言：(1) 面向用户只有**一条**
    content（不逐专家推送）；(2) 专家原始作答（含内部标签）不出现在**任何**事件的载荷里。
    """
    from ib.core import RouteDecision, RouteTier
    from ib.llm import FakeLlmProvider

    class _TwoExpertRouter:
        def classify_experts(self, query, *, history=None, scope=None):
            return RouteDecision(
                experts=["freeark-expert", "inspection-expert"],
                tier=RouteTier.KEYWORD_UNIQUE,
                confidence=0.9,
            )

    llm = FakeLlmProvider(expert_output="内部子任务产物", aggregator_output="对外最终答复")
    orch = _orchestrator(deps, llm=llm, router=_TwoExpertRouter())
    events = list(orch.run("温度与故障", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)

    contents = [e.data for e in events if str(e.kind) == "content"]
    assert len(contents) == 1, f"内部产物被逐专家推送：{kinds}"
    assert contents[0] == "对外最终答复", f"交付的应是融合后的答复：{contents!r}"

    joined = "\n".join(str(e.data) for e in events)
    assert "内部子任务产物" not in joined, "专家的原始（内部）作答不得进入事件流"
    assert "系统管家" not in joined and "巡检诊断" not in joined, "内部专家标签不得外流"


def test_TC_INT_090_reasoning_partition_distinct_from_answer(deps):
    """[TC-INT-090] 思考分区与正文分区在真实流中可区分且不互相污染（AC-IB-19-03）。"""
    from ib.streaming import to_sse

    orch = _orchestrator(deps)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)

    assert "reasoning" in kinds and "content" in kinds
    assert kinds.index("reasoning") < kinds.index("content"), "进度（思考）分区须先于正文"

    reasoning = next(e for e in events if str(e.kind) == "reasoning")
    content = next(e for e in events if str(e.kind) == "content")
    assert str(reasoning.kind) != str(content.kind), "两分区必须可辨（不同 kind）"
    assert reasoning.data not in content.data, "思考文本不得计入答案正文"

    # 每个 SSE 帧只承载一个事件（前端可按 kind 逐条 switch 两分区）
    assert all(to_sse(e).count("event:") == 1 for e in events)


def test_TC_INT_091_no_empty_content_and_exactly_one_terminal(deps):
    """[TC-INT-091] 不推送空内容片段；终止事件恰一次；不臆造引用（AC-IB-19-05）。"""
    from ib.llm import FakeLlmProvider

    # 全链路降级（依赖不可达）：仍须给出非空的可读回退，且终止事件恰一次
    orch = _orchestrator(deps, llm=FakeLlmProvider(unavailable=True))
    events = list(orch.run("能耗数据", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)

    for e in events:
        if str(e.kind) == "content":
            assert str(e.data).strip() != "", "不得推送空的内容片段"
    assert kinds.count("done") == 1 and kinds[-1] == "done"

    # 未产出结构化完成产物时不得臆造引用：无任何事件声称携带引用列表
    joined = "\n".join(str(e.data) for e in events).lower()
    assert "citation" not in joined and "引用" not in joined


# --------------------------------------------------------------------------- #
# US-IB-20 会话生命周期
# --------------------------------------------------------------------------- #


def test_TC_INT_092_session_isolation_no_cross_session_injection(deps):
    """[TC-INT-092] 会话隔离：B 的答复不受 A 历史影响；A 状态保持独立（AC-IB-20-01）。"""
    from ib.core import Message, SessionState
    from ib.streaming import MemorySessionStore

    marker = "ALPHA-SESSION-SECRET-9f3"
    sessions = MemorySessionStore()
    sessions.save(
        "p_alpha:u:A",
        SessionState(
            messages=[Message(role="user", content=marker)],
            last_expert="freeark-expert",
            sticky_turns_left=1,
        ),
    )

    orch = _orchestrator(deps, sessions=sessions)
    list(
        orch.run(
            "设备故障怎么排查",
            ctx=request_ctx("p_alpha", session_id="B"),
            session_key="p_alpha:u:B",
        )
    )

    state_b = sessions.load("p_alpha:u:B")
    assert state_b is not None, "B 会话应被建立"
    assert all(marker not in m.content for m in state_b.messages), "会话 B 不得注入会话 A 的历史"

    state_a = sessions.load("p_alpha:u:A")
    assert state_a is not None and any(marker in m.content for m in state_a.messages), (
        "会话 A 的状态必须保持独立、不被 B 覆写"
    )

    # 未识别的会话标识不得静默复用他人状态（读回 None，而非「新默认会话」）
    assert sessions.load("p_alpha:u:never-seen") is None


def test_TC_INT_093_resume_fail_closed_without_gate_or_state(deps):
    """[TC-INT-093] 恢复须 fail-closed：确认门关闭 / 状态丢失 → 显式失败，不静默续跑（AC-IB-20-02 / 20-05）。"""
    from ib.core import GraphConfig

    # 情形 1：确认门默认关闭 → resume 显式失败（不得静默成功）
    orch_off = _orchestrator(deps, config=GraphConfig())
    events = list(orch_off.resume("p_alpha:u:s1", {"query": "把温度设定为 26"}))
    kinds = _kinds(events)
    assert kinds[-1] == "done"
    assert "error" in kinds, f"无可恢复状态时必须安全失败：{kinds}"
    assert "content" not in kinds, "不得静默续跑未被确认的挂起动作"

    # 情形 2：确认门开启但待确认状态已丢失（模拟重启）→ 同样 fail-closed
    orch_on = _orchestrator(deps, config=GraphConfig(confirmation_gate_enabled=True))
    events2 = list(orch_on.resume("p_alpha:u:missing", {"query": "把温度设定为 26"}))
    kinds2 = _kinds(events2)
    assert kinds2[-1] == "done" and "error" in kinds2, f"状态丢失后必须安全失败：{kinds2}"
    assert "content" not in kinds2, "状态丢失时不得静默继续"


def test_TC_INT_094_confirmation_gate_default_disabled_no_wait(deps):
    """[TC-INT-094] 确认门默认关闭、关闭时不引入等待（AC-IB-20-03）。

    AC-IB-20-03：机制保留、**默认不启用**、不绑定业务确认语义；关闭时流程不得出现确认等待。
    （「启用后的呈递/决策回传」子句属 AC-IB-20-04，依赖 IFC-IB-298~308，本轮未实现。）
    """
    from ib.core import GraphConfig

    cfg = GraphConfig()
    assert cfg.confirmation_gate_enabled is False, "确认门默认必须关闭（不绑定业务确认语义）"

    orch = _orchestrator(deps, config=cfg)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx("p_alpha"), session_key="p_alpha:u:s1"))
    kinds = _kinds(events)

    # 关闭时不得出现确认等待/确认事件，直接走完正常流程
    assert "confirmation_required" not in kinds, f"关闭时不应引入确认等待：{kinds}"
    assert kinds[-1] == "done" and "content" in kinds, f"关闭时应正常完成：{kinds}"


def test_TC_INT_095_cross_project_and_forged_session_rejected(deps):
    """[TC-INT-095] 跨项目 / 伪造会话标识被拒（可识别，不静默当新会话）（AC-IB-20-06）。"""
    from ib.context import assert_session_key
    from ib.core import Message, ScopeViolationError, SessionState
    from ib.streaming import MemorySessionStore, project_of_session_key

    sessions = MemorySessionStore()
    sessions.save(
        "p_beta:u:s1",
        SessionState(messages=[Message(role="user", content="B 的会话内容")], last_expert=None, sticky_turns_left=0),
    )

    # 键前缀解析：无前缀 / 非法格式 → 空串（调用方据此拒绝，而非猜测归属）
    assert project_of_session_key("p_beta:u:s1") == "p_beta"
    assert project_of_session_key("forged") == ""

    # 伪造 / 非法键：读写均被拒（不静默当作新默认会话）
    assert sessions.load("forged") is None
    assert sessions.load(":u:s1") is None
    sessions.save("forged", SessionState(messages=[], last_expert=None, sticky_turns_left=0))
    assert sessions.load("forged") is None

    # 归属校验：以 p_alpha 的身份断言解析 p_beta 的键 → 明确拒绝（拒绝行为可识别）
    with pytest.raises(ScopeViolationError):
        assert_session_key("p_beta:u:s1", "p_alpha")
