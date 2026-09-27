"""单测层 R12 增量 —— 流式交付 / 会话 lifecycle 的 R8 契约补测（REV-12-5）。

覆盖 user_stories.md 1.3.0 的 **US-IB-19**（AC-IB-19-02 / 19-03）与 **US-IB-20**
（AC-IB-20-02 / 20-05）在 R8 实现到位后**新可验收**的子句。

与 `test_stream_session_lifecycle_unit_r11.py` 的关系：
  * R11 的 TC-UNIT-067~069 **代码保持原样不动**（本文件只**追加**编号）；
  * 本文件为**新增**用例（TC-UNIT-070 起，编号只增不改）。

边界（如实登记，见 docs/test_report.md §17）：
  * AC-IB-19-02 的**契约/构造函数层**（`CompletionPayload` / `completion_event`，IFC-IB-300/302）
    本轮已实现，故为本层完整覆盖；**端到端**把检索命中装配进 `CompletionPayload` 的接线
    编排层**未实现**（`Orchestrator` 恒传 `payload=None`）→ 该子句登记为残余，不伪造断言。
"""

from __future__ import annotations

import json

from ib.core import (
    DEFAULT_SESSION_PERSISTENCE_POLICY,
    SESSION_STATE_LOSS_OUTCOME,
    CitationItem,
    CompletionPayload,
    SessionPersistencePolicy,
    SessionStateLossOutcome,
)


# --------------------------------------------------------------------------- #
# TC-UNIT-070 —— AC-IB-19-02：完成事件的结构化产物（contract / 构造层）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_070_completion_event_structured_payload_boundaries():
    """[TC-UNIT-070] US-IB-19 / AC-IB-19-02：`completion_event` 的结构化产物语义与边界。

    验收点：
      * 终态事件恰一个、类别为 `done`，且**从不**产 `content`（不拆散混入内容片段）；
      * **不臆造引用**：`payload=None` → `data` 为空串（「未产出结构化产物」）；
      * **空引用不臆造**：空元组 `citations=()` → 编码为可解析的 `[]`（「无引用」是
        一个**可区分的事实**，不与「未产出产物」混淆，AC-IB-19-05）；
      * `had_content` 边界：空内容 vs 有内容可区分；
      * 引用只含**定位信息**（doc_id / doc_name / page_or_section / locator / score），
        绝不含正文全文 / base64 / 内联字节。
    """
    from ib.streaming import completion_event, completion_payload_json
    from ib.core import StreamEventKind

    # 1) 未产出结构化产物：data 为空串（与既有 StreamEvent(DONE) 逐字节等价）
    none_done = completion_event(None)
    assert str(none_done.kind) == "done" == str(StreamEventKind.DONE)
    assert none_done.data == "", "缺省载荷不得臆造任何引用清单"

    # 2) 空引用（无命中）：仍如实编码为 []，不臆造来源
    empty = CompletionPayload(citations=(), had_content=False)
    empty_done = completion_event(empty)
    parsed = json.loads(empty_done.data)
    assert parsed["citations"] == [], "空元组必须编码为空数组，而非臆造来源"
    assert parsed["had_content"] is False, "空内容边界须如实反映"
    # 逐字一致：`completion_payload_json` 与 `completion_event` 同源（无第二编码点）
    assert completion_payload_json(empty) == empty_done.data

    # 3) had_content 边界可区分（有内容）
    has_text = completion_event(CompletionPayload(citations=(), had_content=True))
    assert json.loads(has_text.data)["had_content"] is True

    # 4) 有引用：只含定位信息，绝不含正文 / 字节 / base64
    payload = CompletionPayload(
        citations=(
            CitationItem(
                doc_id="doc-1",
                doc_name="设备手册.pdf",
                page_or_section="第 3 页",
                locator="§3.2",
                score=0.91,
            ),
        ),
        had_content=True,
    )
    hit_done = completion_event(payload)
    assert str(hit_done.kind) == "done"
    hit = json.loads(hit_done.data)
    assert len(hit["citations"]) == 1
    cite = hit["citations"][0]
    assert cite == {
        "doc_id": "doc-1",
        "doc_name": "设备手册.pdf",
        "page_or_section": "第 3 页",
        "locator": "§3.2",
        "score": 0.91,
    }
    lowered = hit_done.data.lower()
    assert "base64" not in lowered and "data:image" not in lowered, "引用不得内联字节"
    # 引用条目只登记**定位**，不含命中正文全文
    assert "content" not in cite and "text" not in cite

    # 5) 终态事件只产 done（从不产 content）——「一次性给出，不拆散混入内容片段」
    for evt in (none_done, empty_done, has_text, hit_done):
        assert str(evt.kind) == "done"


# --------------------------------------------------------------------------- #
# TC-UNIT-071 —— AC-IB-19-03：思考分区默认不可见 / 可见性白名单
# --------------------------------------------------------------------------- #


def test_TC_UNIT_071_reasoning_invisible_by_default_whitelist():
    """[TC-UNIT-071] US-IB-19 / AC-IB-19-03：思考分区**默认不可见**，且可见性为白名单。

    验收点（默认形态）：
      * `reasoning` 默认**不可见**（该能力可选、默认不启用）；启用后的呈递由
        `IB_REASONING_STREAM_ENABLED` 与前端共同决定，不改变纯函数的默认口径；
      * 可见集合是**白名单**：未登记的类别（含内部子任务产物）一律默认不可见；
      * 两分区 kind 互异、绝不混帧（一帧只承载一个事件）。
    """
    from ib.core import StreamEvent, StreamEventKind
    from ib.streaming import USER_VISIBLE_KINDS, is_user_visible, to_sse

    # 默认不可见：reasoning（AC-IB-19-03）
    assert is_user_visible(StreamEventKind.REASONING) is False
    assert is_user_visible("reasoning") is False
    assert "reasoning" not in USER_VISIBLE_KINDS, "reasoning 不得在可见白名单内"

    # 可见白名单：契约明列的面向用户类别
    for kind in ("content", "degraded", "related_images", "error", "done", "confirmation_required"):
        assert is_user_visible(kind) is True, kind
    # 未登记类别默认不可见（内部子任务产物绝不外流，AC-IB-19-04 的结构事实）
    assert is_user_visible("internal_subtask") is False
    assert is_user_visible("subagent_partial") is False

    # 既有 6 个 kind 逐位不变，confirmation_required 为**追加**（第 7 个）
    values = [k.value for k in StreamEventKind]
    assert values[:6] == ["reasoning", "content", "degraded", "related_images", "error", "done"]
    assert values[6:] == ["confirmation_required"]

    # 不混帧：两分区 kind 互异，各帧只承载一个事件
    reasoning = StreamEvent(StreamEventKind.REASONING, "正在分析…")
    content = StreamEvent(StreamEventKind.CONTENT, "正式答复")
    assert str(reasoning.kind) != str(content.kind)
    for evt in (reasoning, content):
        assert to_sse(evt).count("event:") == 1
    assert reasoning.data not in content.data


# --------------------------------------------------------------------------- #
# TC-UNIT-072 —— AC-IB-20-02 / 20-05：持久化策略与状态丢失结局的**类型层**声明
# --------------------------------------------------------------------------- #


def test_TC_UNIT_072_session_persistence_policy_and_loss_outcome_declared():
    """[TC-UNIT-072] US-IB-20 / AC-IB-20-02 / 20-05：持久化策略与「状态丢失」结局的类型层声明。

    验收点：
      * `SessionPersistencePolicy` 取值域 `{in_process, external}`，**默认 `in_process`**
        （进程内，重启即失忆 —— 这本身是安全失败方向，AC-IB-20-02）；
      * `SessionStateLossOutcome` **唯一取值** `fail_closed_restart_required`
        —— 使「重启丢弃待确认状态 = 安全失败」成为**类型层事实**（AC-IB-20-05）；
      * 配置默认值显式声明：`GlobalConfig` 中 `confirmation_gate_enabled` /
        `reasoning_stream_enabled` 均默认 `False`，`session.persistence_policy` 默认 `in_process`。
    """
    from ib.config import GlobalConfig

    # 取值域（唯一取值 → 类型层不可表达「默认放行」）
    assert tuple(SessionPersistencePolicy.__args__) == ("in_process", "external")
    assert tuple(SessionStateLossOutcome.__args__) == ("fail_closed_restart_required",)
    assert DEFAULT_SESSION_PERSISTENCE_POLICY == "in_process"
    assert SESSION_STATE_LOSS_OUTCOME == "fail_closed_restart_required"

    # 配置默认值（显式声明；未声明即取安全默认）
    cfg = GlobalConfig()
    assert cfg.session.persistence_policy == "in_process"
    assert cfg.confirmation_gate_enabled is False, "确认门默认必须关闭（零行为差异）"
    assert cfg.reasoning_stream_enabled is False, "思考分区默认不启用（AC-IB-19-03）"


# --------------------------------------------------------------------------- #
# TC-UNIT-073 —— AC-IB-20-05：can_resume 三判据 fail-closed 纯函数穷举
# --------------------------------------------------------------------------- #


def test_TC_UNIT_073_can_resume_fail_closed_matrix():
    """[TC-UNIT-073] US-IB-20 / AC-IB-20-04 / 20-05：`can_resume` 纯函数的 fail-closed 穷举。

    三判据（任一不满足即 `False`）：状态丢失 / 待确认中间态归属不符 / 未携决策。
    另加加固：载荷里的决策不得指向**另一个** gate_id。全套穷举，确保「默认拒绝」。
    """
    from ib.core import ConfirmationDecision, ConfirmationGateState, ConfirmationPrompt, SessionState
    from ib.orchestration import ResumePayload, can_resume

    prompt = ConfirmationPrompt(gate_id="g1", expert_name="data-expert", summary="确认执行写操作？")
    gate = ConfirmationGateState(gate_id="g1", prompt=prompt, decision=None)
    state = SessionState(gate=gate)
    approve = ResumePayload(decision=ConfirmationDecision(gate_id="g1", approved=True))

    # 正向：待确认中间态 + 归属一致 + 携决策 → 允许（批准 / 拒绝均由上层各自处置）
    assert can_resume(state, "g1", approve) is True
    assert can_resume(state, "g1", ResumePayload(decision=ConfirmationDecision("g1", False))) is True

    # 判据①：状态丢失（进程重启后内存后端读回 None）→ 拒绝
    assert can_resume(None, "g1", approve) is False
    # 判据②：无待确认中间态 / gate_id 归属不符 → 拒绝
    assert can_resume(SessionState(gate=None), "g1", approve) is False
    assert can_resume(state, "other", approve) is False
    assert can_resume(state, "", approve) is False  # 空 gate_id 不得放行
    # 判据③：未携决策（payload 缺省 / decision 缺省）→ 拒绝
    assert can_resume(state, "g1", None) is False
    assert can_resume(state, "g1", ResumePayload()) is False
    # 加固：载荷决策指向**另一个** gate_id → 拒绝（不得错配执行）
    assert can_resume(state, "g1", ResumePayload(decision=ConfirmationDecision("g2", True))) is False

    # 残缺载荷**绝不**被补成「默认批准」：缺 gate_id / 缺字段 → decision 保持 None
    for raw in (
        {},
        {"decision": None},
        {"decision": {"approved": True}},  # 缺 gate_id
        {"decision": {"gate_id": "g1"}},   # 缺 approved
        {"decision": "approve"},           # 非映射
        None,
    ):
        assert ResumePayload.from_dict(raw).decision is None, raw
        assert can_resume(state, "g1", ResumePayload.from_dict(raw)) is False, raw
