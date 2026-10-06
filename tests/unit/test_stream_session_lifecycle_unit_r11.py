"""单测层 R11 增量 —— 流式交付契约 / 会话生命周期（REV-11-3）。

覆盖 user_stories.md 1.3.0 新增的两条用户故事：

  * **US-IB-19**（流式交付最终答复，AC-IB-19-01~05）
  * **US-IB-20**（会话生命周期，AC-IB-20-01~06）

与既有 `test_core_config_chunk_parse_stream.py` 的关系：
  * TC-UNIT-016 / TC-UNIT-017 / TC-UNIT-018 / TC-UNIT-022 的**代码保持原样不动**
    （本轮只「重挂」其 US/AC 归属，见 docs/test_plan.md §15）；
  * 本文件为**新增**用例（TC-UNIT-067 起，只增不改既有编号），就 US-IB-19 / US-IB-20
    中**当前实现已可验收**的子句补一层显式守卫。

**边界（如实登记）**：US-IB-19 的「完成事件附结构化产物」子句（AC-IB-19-02）与 US-IB-20
的「确认中间态呈递/决策回传」子句（AC-IB-20-04）依赖架构 1.4.0/R8 的 IFC-IB-298~308，
本轮 `src/` 尚未实现，故**不在此处伪造断言**（见 docs/test_report.md §16 的覆盖缺口登记）。
"""

from __future__ import annotations


# --------------------------------------------------------------------------- #
# US-IB-19 流式交付最终答复
# --------------------------------------------------------------------------- #


def test_TC_UNIT_067_internal_labels_stripped_from_visible_text():
    """[TC-UNIT-067] 内部子任务标识在交付前被确定性清洗（AC-IB-19-04）。

    AC-IB-19-04 要求「内部子任务产物绝不作为面向用户的内容片段出现」。实现侧有两道防线：
    提示词约束 + 确定性清洗 `_strip_internal_labels`。本条只验**确定性那一层**（可编程、可复现）：
    内部分工词汇一旦出现在交付文本里，必被删除，而事实内容保留。
    """
    from ib.core import GraphConfig
    from ib.orchestration import AGGREGATION_FORBIDDEN_LABELS, _strip_internal_labels

    cfg = GraphConfig()  # aggregation_forbids_internal_labels=True（默认）
    raw = "路由到巡检诊断专家后，聚合结果如下：电压偏高。"
    cleaned = _strip_internal_labels(raw, cfg)

    for label in ("路由到", "巡检诊断", "专家", "聚合"):
        assert label not in cleaned, f"内部标识 {label!r} 未被清洗：{cleaned!r}"
    assert "电压偏高" in cleaned, "清洗必须保守：只删分工词，不得丢事实内容"

    # 清洗开关可关（内部调试模式）——关闭时原样返回（配置被如实遵守）
    cfg_off = GraphConfig(aggregation_forbids_internal_labels=False)
    assert _strip_internal_labels(raw, cfg_off) == raw

    # 清洗词表是内部标识的最小集合（覆盖 AC-IB-19-04 关心的「子任务/分工」措辞）
    assert {"路由到", "专家", "聚合"} <= set(AGGREGATION_FORBIDDEN_LABELS)


def test_TC_UNIT_068_reasoning_and_content_are_distinct_single_event_frames():
    """[TC-UNIT-068] 思考分区与正文分区可区分，且一帧只承载一个事件（AC-IB-19-03）。

    AC-IB-19-03 要求：思考片段（若有）与正式答复**分区可辨**，不得混帧；思考文本不计入
    答案正文。本层只验「事件种类互异 + SSE 帧不混载」这条**编码层**不变量（默认不出现思考
    片段属装配层行为，见 TC-INT-090）。
    """
    from ib.core import StreamEvent, StreamEventKind
    from ib.streaming import to_sse

    reasoning = StreamEvent(StreamEventKind.REASONING, "正在分析问题…")
    content = StreamEvent(StreamEventKind.CONTENT, "最终答复正文")

    # 分区可辨：思考与正文是不同的 `kind`
    assert str(reasoning.kind) != str(content.kind)
    assert str(reasoning.kind) == "reasoning" and str(content.kind) == "content"

    # 一帧只承载一个事件（不混帧）——否则前端无法按 kind 逐条 switch
    for evt in (reasoning, content):
        frame = to_sse(evt)
        assert frame.count("event:") == 1, f"帧混载了多个事件：{frame!r}"
        assert frame.endswith("\n\n")

    # 思考片段不并入正文文本（两分区的载荷各自独立）
    assert reasoning.data not in content.data
    assert content.data not in reasoning.data


# --------------------------------------------------------------------------- #
# US-IB-20 会话生命周期
# --------------------------------------------------------------------------- #


def test_TC_UNIT_069_session_state_lost_on_restart_is_fail_closed():
    """[TC-UNIT-069] 会话状态在重启中丢失 → 读回 None（安全失败的存储底座）（AC-IB-20-05）。

    AC-IB-20-05 要求「待确认状态在重启中丢失须以安全失败结束，不得静默续跑」。其**存储层
    前置条件**是：进程重启（新的内存存储）不得复活旧会话 —— 否则「状态丢失」根本不会被上层
    感知，静默续跑就有了物质基础。本条固化这条前置语义（进程内存储即生产默认后端）。
    """
    from ib.core import Message, SessionState
    from ib.streaming import MemorySessionStore

    key = "p_alpha:u1:s1"
    store = MemorySessionStore()
    store.save(
        key,
        SessionState(
            messages=[Message(role="user", content="上一轮提问")],
            last_expert="freeark-expert",
            sticky_turns_left=1,
        ),
    )
    assert store.load(key) is not None

    # 模拟进程重启：全新存储不携带任何既有会话 → 读回 None（不静默复活/继续）
    restarted = MemorySessionStore()
    assert restarted.load(key) is None, "重启后不得静默复活旧会话（fail-closed 的存储底座）"

    # 删除幂等：显式结束的会话不得复现
    store.delete(key)
    store.delete(key)
    assert store.load(key) is None
