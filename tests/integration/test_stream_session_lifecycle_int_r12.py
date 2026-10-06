"""集成测试层 R12 增量 —— 确认中间态 / 续跑 / 流式终态的端到端接缝补测（REV-12-5）。

覆盖 user_stories.md 1.3.0 的 **US-IB-19**（AC-IB-19-02）与 **US-IB-20**
（AC-IB-20-02 / 20-03 / 20-04 / 20-05），聚焦架构 1.4.0/R8（IFC-IB-298~308）到位后
**新可验收**的子句：

  * 确认门**挂起**：`confirmation_required` **恰一次**、会话**挂起**（无 content、无空帧）、
    终态单发、待确认中间态**已落库**（AC-IB-20-04）；
  * **HTTP 续跑成功**：以**真实流路径键**（`{project}:{actor}:{session_id}`，3 段）预置
    待确认中间态 → `POST /api/chat/resume` 携决策 → 续跑至终态 `done`（AC-IB-20-04）；
  * **fail-closed 负例**：gate_id 不符 / 无决策 / 会话或中间态丢失（404/409）、
    自造 **2 段**键不得命中真实会话（404，MAJOR-1 守卫）；
  * **确认门默认关闭**：零行为差异（无等待、无确认事件），关闭/无话术构造器/构造抛异常
    三态均不静默放行（AC-IB-20-03）；
  * **完成事件的终态边界**：`done` 恰一次、其后无 content、且**不臆造**结构化引用
    （`data` 为空串，而非伪造的引用清单）（AC-IB-19-02 / 19-05）；
  * **FND-R11-01**：`GET /api/chat/stream` 缺 `session_id` → **400**，
    **不得**静默回退到默认会话；显式合法 session_id → 正常（AC-IB-20-01）。

与 `test_stream_session_lifecycle_int_r11.py` 的关系：R11 的 TC-INT-088~095 断言与编号
**保持原样不动**；本文件只**追加**（TC-INT-096 起）。

**边界（如实登记，见 docs/test_report.md §17）**：AC-IB-19-02 的**端到端**「把检索命中装配
进 `CompletionPayload`」在编排层**未接线**（`Orchestrator._run_inner` 恒传 `payload=None`），
故本层只断言「**不臆造**引用」一侧；「有命中 → 产物含命中」一侧登记为残余，不以空断言充数。

离线约束：InMemory/Fake/进程内 Django test client，零外部网络，无 Docker。
"""

from __future__ import annotations

import json
import os

from conftest import offline_raw, request_ctx

import pytest

#: 离线共享令牌经环境变量注入（测试代码不含真实凭据；?token= 仍须被拒）。
TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}

#: 离线 EnvTokenResolver 的主体：actor_id="service-account"，project_id=首个项目 "p_alpha"。
#: 流路径写入用的会话键 = `{project}:{actor}:{session_id}`（3 段，唯一入口 `ib.context.session_key`）。
PROJECT = "p_alpha"
ACTOR = "service-account"


# --------------------------------------------------------------------------- #
# 夹具与助手
# --------------------------------------------------------------------------- #


@pytest.fixture()
def gate_app(django_ready):
    """确认门**已启用**的 HTTP 装配（`confirmation_gate_enabled=True`）。

    返回 `(deps, Client工厂)`。`Client()` 每次新建（中间件按请求解析策略，复用会缓存）。
    """
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    raw = offline_raw()
    raw["confirmation_gate_enabled"] = True
    d = build_deps(raw, force=True)
    build_application(d)
    return d, Client


def _annotated_builder(gate_id="g-1", summary="确认执行写操作？"):
    """接入方提供的确认话术构造器（骨架不生成业务话术，ADR-09）。"""

    def _build(query, *, decision=None, scope=None):
        from ib.core import ConfirmationPrompt

        return ConfirmationPrompt(gate_id=gate_id, expert_name="freeark-expert", summary=summary)

    return _build


def _gate_orchestrator(deps, *, sessions, builder, enabled=True, llm=None, router=None, project_id=PROJECT):
    """构造带确认门接缝的离线编排器（复用 build_graph 的**公开**参数）。"""
    from ib.core import GraphConfig, Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph

    bound_tools = deps.bind_tools(Scope(project_id=project_id))
    return build_graph(
        llm=llm if llm is not None else deps.llm,
        experts=EXPERT_SPECS,
        tools=bound_tools,
        sessions=sessions,
        config=GraphConfig(confirmation_gate_enabled=enabled),
        router=router,
        scope=Scope(project_id=project_id),
        tools_by_expert={name: bound_tools for name in (s.name for s in EXPERT_SPECS)},
        confirmation_prompt_builder=builder,
    )


def _preset_gate_session(deps, key, *, gate_id="g-9", query="把温度设定为 26"):
    """在 `deps.sessions` 里预置一个**待确认中间态**（模拟「门已呈递、等待决策」）。"""
    from ib.core import ConfirmationGateState, ConfirmationPrompt, SessionState, SessionTurn

    deps.sessions.save(
        key,
        SessionState(
            messages=[],
            last_expert=None,
            sticky_turns_left=0,
            session_key=key,
            project_id=key.split(":")[0],
            turns=(SessionTurn(role="user", text=query, created_at=""),),
            gate=ConfirmationGateState(
                gate_id=gate_id,
                prompt=ConfirmationPrompt(gate_id=gate_id, expert_name="freeark-expert", summary="确认执行写操作？"),
            ),
        ),
    )
    return gate_id


def _kinds(events):
    return [str(e.kind) for e in events]


def _sse_body(response) -> str:
    raw = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
    return raw.decode("utf-8")


def _post_resume(client, body, **extra):
    return client.post(
        "/api/chat/resume",
        data=json.dumps(body),
        content_type="application/json",
        **AUTH,
        **extra,
    )


# --------------------------------------------------------------------------- #
# TC-INT-096 —— AC-IB-20-04：确认门挂起（恰一次呈递、无 content、落库）
# --------------------------------------------------------------------------- #


def test_TC_INT_096_gate_suspend_presents_once_and_persists(deps):
    """[TC-INT-096] US-IB-20 / AC-IB-20-04：确认门挂起时只呈递一次、挂起会话、终态单发。

    验收点：
      * 事件序列**恰为** `reasoning → confirmation_required → done`：无 content、
        无空帧（呈递帧带 gate_id/expert_name/summary，终态帧为空即为空非占位）；
      * `confirmation_required` **恰一次**、`done` **恰一次**且收尾（挂起不导致流悬空）；
      * 待确认中间态**已落库**（`gate` 与 `gate_id` 可对账；原提问落 `turns` 供续跑取回）。
    """
    from ib.streaming import MemorySessionStore

    sessions = MemorySessionStore()
    key = f"{PROJECT}:u:gate-suspend"
    orch = _gate_orchestrator(deps, sessions=sessions, builder=_annotated_builder("g-1"))

    events = list(orch.run("把温度设定为 26", ctx=request_ctx(PROJECT), session_key=key))
    kinds = _kinds(events)

    assert kinds.count("confirmation_required") == 1, f"呈递必须恰一次：{kinds}"
    assert kinds.count("done") == 1 and kinds[-1] == "done", f"终态必须恰一次且收尾：{kinds}"
    assert "content" not in kinds, f"挂起不得产出正文（用户尚未确认）：{kinds}"

    # 呈递帧载荷：最小字段 + 可对账 gate_id
    presented = next(e for e in events if str(e.kind) == "confirmation_required")
    payload = json.loads(presented.data)
    assert payload["gate_id"] == "g-1" and payload["expert_name"] == "freeark-expert" and payload["summary"]

    # 无空帧：除终态外每一帧都带非空载荷
    for e in events:
        if str(e.kind) != "done":
            assert str(e.data).strip() != "", f"不得推送空帧：{e}"

    # 待确认中间态已落库（挂起 = 会话保持在该中间态）
    state = sessions.load(key)
    assert state is not None and state.gate is not None, "挂起后待确认中间态必须落库"
    assert state.gate.gate_id == "g-1" and state.gate.decision is None, "落库时 decision 必须为空（待决策）"
    assert any(t.role == "user" and t.text == "把温度设定为 26" for t in state.turns), "原提问须可续跑取回"


# --------------------------------------------------------------------------- #
# TC-INT-097 —— AC-IB-20-04：批准续跑 → 终态 done，中间态清除
# --------------------------------------------------------------------------- #


def test_TC_INT_097_approved_resume_reaches_done_and_clears_gate(deps):
    """[TC-INT-097] US-IB-20 / AC-IB-20-04：携「批准」决策续跑至终态 `done`，且不自我死锁。

    验收点：续跑产出 content + 终态 done；**不得**再次出现 `confirmation_required`
    （否则续跑会再次触发确认而自我死锁）；续跑完成后待确认中间态被清除。
    """
    from ib.streaming import MemorySessionStore

    sessions = MemorySessionStore()
    key = f"{PROJECT}:u:gate-resume"
    orch = _gate_orchestrator(deps, sessions=sessions, builder=_annotated_builder("g-1"))

    # 先挂起
    list(orch.run("把温度设定为 26", ctx=request_ctx(PROJECT), session_key=key))
    assert sessions.load(key).gate is not None

    # 再以「批准」续跑
    events = list(
        orch.resume(
            key,
            {
                "session_key": key,
                "decision": {"gate_id": "g-1", "approved": True},
                "ctx": request_ctx(PROJECT),
            },
        )
    )
    kinds = _kinds(events)

    assert "error" not in kinds, f"批准续跑不得失败：{kinds}"
    assert "content" in kinds, f"续跑应产出正文：{kinds}"
    assert kinds.count("done") == 1 and kinds[-1] == "done"
    assert "confirmation_required" not in kinds, "续跑不得再次触发确认门（自我死锁）"
    assert sessions.load(key).gate is None, "续跑完成后待确认中间态须被清除"


# --------------------------------------------------------------------------- #
# TC-INT-098 —— AC-IB-20-04 / 20-05：续跑的 fail-closed 负例族
# --------------------------------------------------------------------------- #


def test_TC_INT_098_resume_fail_closed_matrix_no_rerun(deps):
    """[TC-INT-098] US-IB-20 / AC-IB-20-04 / 20-05：三种前置不满足即 fail-closed，不静默放行。

    覆盖（每条均须 `error` + 终态，且**无 content** —— 即「不重跑未经确认的动作」）：
      * 无待确认中间态（state 存在但 `gate=None`）；
      * 中间态存在但**未携决策**；
      * 决策指向**另一个** gate_id（归属不符）；
      * 决策为**拒绝**（`approved=False`）——明确终止，不执行待确认动作、不续跑。
    """
    from ib.core import SessionState
    from ib.streaming import MemorySessionStore

    sessions = MemorySessionStore()
    orch = _gate_orchestrator(deps, sessions=sessions, builder=_annotated_builder("g-1"))

    # (a) 无待确认中间态
    sessions.save(f"{PROJECT}:u:no-gate", SessionState(messages=[], last_expert=None, sticky_turns_left=0))
    a = list(orch.resume(f"{PROJECT}:u:no-gate", {"ctx": request_ctx(PROJECT)}))
    assert "error" in _kinds(a) and "content" not in _kinds(a) and _kinds(a)[-1] == "done"

    # (b) 未携决策
    _preset_gate_session(deps, f"{PROJECT}:u:no-decision", gate_id="g-1")
    b = list(orch.resume(f"{PROJECT}:u:no-decision", {"ctx": request_ctx(PROJECT)}))
    assert "error" in _kinds(b) and "content" not in _kinds(b) and _kinds(b)[-1] == "done"

    # (c) 决策指向另一个 gate_id（归属不符）
    _preset_gate_session(deps, f"{PROJECT}:u:mismatch", gate_id="g-1")
    c = list(
        orch.resume(
            f"{PROJECT}:u:mismatch",
            {"decision": {"gate_id": "g-OTHER", "approved": True}, "ctx": request_ctx(PROJECT)},
        )
    )
    assert "error" in _kinds(c) and "content" not in _kinds(c) and _kinds(c)[-1] == "done"

    # (d) 决策为拒绝 → 明确终止、不执行、不续跑
    _preset_gate_session(deps, f"{PROJECT}:u:rejected", gate_id="g-1")
    d = list(
        orch.resume(
            f"{PROJECT}:u:rejected",
            {"decision": {"gate_id": "g-1", "approved": False}, "ctx": request_ctx(PROJECT)},
        )
    )
    assert "error" in _kinds(d) and "content" not in _kinds(d) and _kinds(d)[-1] == "done"


# --------------------------------------------------------------------------- #
# TC-INT-099 —— AC-IB-20-04：HTTP 续跑成功（真实流路径键 / MAJOR-1）
# --------------------------------------------------------------------------- #


def test_TC_INT_099_http_resume_success_with_real_stream_key(gate_app):
    """[TC-INT-099] US-IB-20 / AC-IB-20-04：`POST /api/chat/resume` 以**真实流路径键**续跑成功。

    预置待确认中间态时使用**流路径写入**的同一键 `{project}:{actor}:{session_id}`（3 段）——
    请求只给 `session_id`，视图经**唯一入口** `ib.context.session_key(project, actor, session_id)`
    重建同一键（MAJOR-1：视图不得自造 2 段键，否则真实续跑恒 404）。
    """
    deps, Client = gate_app
    sid = "s-r12-ok"
    key = f"{PROJECT}:{ACTOR}:{sid}"
    _preset_gate_session(deps, key, gate_id="g-1")

    r = _post_resume(
        Client(),
        {"session_id": sid, "decision": {"gate_id": "g-1", "approved": True}},
    )
    assert r.status_code == 200, r.content
    assert r["Content-Type"].startswith("text/event-stream")

    body = _sse_body(r)
    assert "event: content" in body, body
    assert "event: done" in body
    assert body.index("event: content") < body.index("event: done")

    # 续跑完成后待确认中间态被清除（同一 key）
    assert deps.sessions.load(key) is not None and deps.sessions.load(key).gate is None


# --------------------------------------------------------------------------- #
# TC-INT-100 —— AC-IB-20-01 / 20-04 / 20-05：HTTP 续跑负例族（含 MAJOR-1 守卫）
# --------------------------------------------------------------------------- #


def test_TC_INT_100_http_resume_negatives_and_selfmade_key_404(gate_app):
    """[TC-INT-100] US-IB-20：续跑准入 fail-closed 的负例族（HTTP 层，确认门已启用）。

    验收点：
      * 会话不存在 → **404**；中间态丢失（state 无 gate）→ **404**；
      * 自造 **2 段**键 `{project}:{session_id}` → **404**（不得命中 3 段真实会话，MAJOR-1 守卫）；
      * 未携决策 / gate_id 不符 → **409**；
      * `?token=` → **400**（令牌纪律，中间件先拒）。

    注：**确认门未启用 → 409** 单列于 TC-INT-104，避免与本用例共用相互覆盖的全局装配。
    """
    deps, Client = gate_app
    real_key = f"{PROJECT}:{ACTOR}:s-guard"
    _preset_gate_session(deps, real_key, gate_id="g-1")

    # 会话不存在 → 404
    assert _post_resume(Client(), {"session_id": "no-such", "decision": {"gate_id": "g-1", "approved": True}}).status_code == 404

    # 中间态丢失（state 存在但无 gate）→ 404
    from ib.core import SessionState

    deps.sessions.save(f"{PROJECT}:{ACTOR}:s-nogate", SessionState(messages=[], last_expert=None, sticky_turns_left=0))
    assert _post_resume(Client(), {"session_id": "s-nogate", "decision": {"gate_id": "g-1", "approved": True}}).status_code == 404

    # 自造 2 段键 → 404（真实会话在 3 段键下，2 段键不得命中）
    selfmade = _post_resume(Client(), {"session_key": f"{PROJECT}:s-guard", "decision": {"gate_id": "g-1", "approved": True}})
    assert selfmade.status_code == 404, selfmade.content
    # 对照：真实 3 段键（经 session_id 唯一入口）能命中，不是 404
    assert _post_resume(Client(), {"session_id": "s-guard"}).status_code == 409  # 命中会话但未携决策 → 409（非 404）

    # 未携决策 → 409
    assert _post_resume(Client(), {"session_id": "s-guard", "decision": None}).status_code == 409

    # gate_id 不符 → 409
    assert (
        _post_resume(Client(), {"session_id": "s-guard", "decision": {"gate_id": "g-OTHER", "approved": True}}).status_code
        == 409
    )

    # 确认门未启用 → 409
    # （单列于 TC-INT-104）

    # ?token= 出现在查询串 → 400（中间件先拒，不进视图）
    bad = Client().post(
        "/api/chat/resume?token=x",
        data=json.dumps({"session_id": "s-guard", "decision": {"gate_id": "g-1", "approved": True}}),
        content_type="application/json",
        **AUTH,
    )
    assert bad.status_code == 400, bad.content


# --------------------------------------------------------------------------- #
# TC-INT-101 —— AC-IB-20-01（FND-R11-01）：stream 缺 session_id → 400
# --------------------------------------------------------------------------- #


def test_TC_INT_101_stream_missing_session_id_400_no_default_fallback(http_app):
    """[TC-INT-101] US-IB-20 / AC-IB-20-01（FND-R11-01）：缺 `session_id` → **400**，不回退默认会话。

    验收点：
      * 缺 `session_id`（仅 `q`）→ **400** 且响应体为 JSON 错误（**绝**不是 SSE 流）——
        回退到字面量默认会话会让「没传会话标识」与「显式用名为 default 的会话」不可区分，
        多客户端静默共用会话、历史互相污染；
      * 显式合法 `session_id` → **200**、`text/event-stream`（正常路径不受影响）。
    """
    _, Client = http_app

    missing = Client().get("/api/chat/stream?q=设备故障怎么排查", **AUTH)
    assert missing.status_code == 400, missing.content
    assert not missing["Content-Type"].startswith("text/event-stream"), "缺会话标识不得开流"
    body = json.loads(missing.content)
    assert body["error"]["code"] and body["error"]["message"]

    ok = Client().get("/api/chat/stream?q=设备故障怎么排查&session_id=s-fnd-r11-01", **AUTH)
    assert ok.status_code == 200
    assert ok["Content-Type"].startswith("text/event-stream")


# --------------------------------------------------------------------------- #
# TC-INT-102 —— AC-IB-20-03：确认门默认关闭 / 无话术 / 抛异常 的零行为差异
# --------------------------------------------------------------------------- #


def test_TC_INT_102_gate_disabled_or_unavailable_zero_behavior_difference(deps):
    """[TC-INT-102] US-IB-20 / AC-IB-20-03：确认门未生效的三种形态均为**零行为差异**。

    验收点：
      * 开关**关闭**（即使注入了话术构造器）→ 正常流程，无 `confirmation_required`；
      * 开关**开启但未注入构造器** → 同上（骨架不生成业务话术，无可呈递内容，故不触发）；
      * 两者的事件序列**逐位相同**（关闭 vs 无构造器不引入任何差异）；
      * 开关**开启且构造器抛异常** → fail-closed（`error` + 终态，**不发 content**），
        绝不静默继续执行未经确认的动作。
    """
    from ib.streaming import MemorySessionStore

    q = "设备故障怎么排查"

    off = list(
        _gate_orchestrator(deps, sessions=MemorySessionStore(), builder=_annotated_builder("g-1"), enabled=False)
        .run(q, ctx=request_ctx(PROJECT), session_key=f"{PROJECT}:u:off")
    )
    none_builder = list(
        _gate_orchestrator(deps, sessions=MemorySessionStore(), builder=None, enabled=True)
        .run(q, ctx=request_ctx(PROJECT), session_key=f"{PROJECT}:u:none")
    )
    assert "confirmation_required" not in _kinds(off) and _kinds(off)[-1] == "done"
    assert "confirmation_required" not in _kinds(none_builder) and _kinds(none_builder)[-1] == "done"
    assert _kinds(off) == _kinds(none_builder), f"关闭 vs 无构造器必须零差异：{_kinds(off)} / {_kinds(none_builder)}"

    def _boom(query, *, decision=None, scope=None):
        raise RuntimeError("话术构造失败")

    failed = list(
        _gate_orchestrator(deps, sessions=MemorySessionStore(), builder=_boom, enabled=True)
        .run(q, ctx=request_ctx(PROJECT), session_key=f"{PROJECT}:u:boom")
    )
    assert "error" in _kinds(failed) and _kinds(failed)[-1] == "done"
    assert "content" not in _kinds(failed), "已启用确认门却造话术失败时不得静默继续执行"


# --------------------------------------------------------------------------- #
# TC-INT-103 —— AC-IB-19-02 / 19-05：终态 done 不臆造结构化引用
# --------------------------------------------------------------------------- #


def test_TC_INT_103_terminal_done_no_fabricated_citations(deps):
    """[TC-INT-103] US-IB-19 / AC-IB-19-02 / 19-05：终态 `done` 恰一次、收尾、不臆造引用。

    验收点（真实编排路径，非构造层）：
      * `done` 事件**恰一次**且为末事件，其后无 `content`；
      * 未产出结构化产物时，`done.data` 为**空串**（「无产物」），而**不是**伪造的
        `{"citations": [...]}` —— 亦非空的引用清单（后者是「有产物但无命中」的形态）；
      * 流内**不存在**任何解析为含 `citations` 键的事件载荷（不臆造引用）。
    """
    from ib.streaming import MemorySessionStore

    orch = _gate_orchestrator(deps, sessions=MemorySessionStore(), builder=None, enabled=False)
    events = list(orch.run("设备故障怎么排查", ctx=request_ctx(PROJECT), session_key=f"{PROJECT}:u:term"))
    kinds = _kinds(events)

    assert kinds.count("done") == 1 and kinds[-1] == "done"
    assert "content" not in kinds[kinds.index("done") + 1 :], "done 之后不得再有内容片段"

    done = next(e for e in events if str(e.kind) == "done")
    assert done.data == "", "未产出结构化产物时 done 载荷必须为空串，不得臆造引用清单"

    # 任何事件载荷都不得是一个含 citations 键的 JSON 对象（不臆造引用）
    for e in events:
        try:
            parsed = json.loads(e.data)
        except (ValueError, TypeError):
            continue
        assert not (isinstance(parsed, dict) and "citations" in parsed), f"臆造了引用载荷：{e}"


# --------------------------------------------------------------------------- #
# TC-INT-104 —— AC-IB-20-03：确认门未启用时 HTTP 续跑 → 409（不新建会话）
# --------------------------------------------------------------------------- #


def test_TC_INT_104_http_resume_without_gate_enabled_409(http_app):
    """[TC-INT-104] US-IB-20 / AC-IB-20-03：确认门**未启用**时 `POST /api/chat/resume` → **409**。

    默认（门关闭）下不存在「待确认中间态」，恢复**不可用**；视图须**显式 409** 终止，
    **不得**退化为「新建会话后重跑」——那等于把未经确认的动作重新执行（ADR-17 约束 4 / AC-IB-20-05）。
    本用例单列，使用独立（门关闭）装配，避免与 TC-INT-100 的全局装配相互覆盖。
    """
    off_deps, Client = http_app
    assert bool(getattr(off_deps.cfg, "confirmation_gate_enabled", False)) is False

    r = _post_resume(Client(), {"session_id": "s-whatever", "decision": {"gate_id": "g-1", "approved": True}})
    assert r.status_code == 409, r.content
    body = json.loads(r.content)
    assert body["error"]["code"] == "conflict"
    # 不得开流（未新建会话、未重跑）
    assert not r["Content-Type"].startswith("text/event-stream")
