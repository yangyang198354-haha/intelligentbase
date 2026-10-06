"""
@module MOD-IB-22
@implements IFC-IB-231 build_graph / 232 run / 233 resume
            R2：`related_images` 事件的**生产接缝**（新增可选关键字 `related_images_provider`；
            载荷类型化与「空即不发」纪律属 IFC-IB-282 / MOD-IB-21）
            IFC-IB-305（R8）`ResumePayload` 类型化恢复载荷
            IFC-IB-306（R8）`can_resume` fail-closed 三判据（纯函数）
            IFC-IB-302（R8）终态经 `completion_event` 单发（MOD-IB-21）
            REV-12-2（G2）专家交接：`is_delegating` / `delegating_experts()` 落地为**计划展开**
@depends MOD-IB-01, MOD-IB-02, MOD-IB-03, MOD-IB-04, MOD-IB-16, MOD-IB-17,
         MOD-IB-18, MOD-IB-19, MOD-IB-20, MOD-IB-21
@author software-developer

编排图（module_design.md §3 MOD-IB-22 / §7.1 图结构 / §7.2 四级路由；ADR-09 / ADR-11-R1；
REQ-FUNC-IB-18/19/20/21；AC-IB-09-01~07、AC-IB-11-06）。

## 图长什么样

```
            ┌─────────┐
   START ──▶│  route  │   路由：调 MOD-IB-19 得 RouteDecision
            └────┬────┘
                 │ 条件边 _fan_out
      ┌──────────┼───────────┐
      ▼          ▼           ▼
   ┌──────┐  ┌──────┐   ┌─────────┐
   │expert│  │expert│ … │ general │   并行多实例（同一节点被 Send 多次）
   └───┬──┘  └───┬──┘   └────┬────┘
       └────┬────┘           │
            ▼                │
        ┌───────┐            │
        │ gate  │            │   步数上限 + 写操作确认门（默认关闭，OQ-IB-07）
        └───┬───┘            │
            └───────┬────────┘
                    ▼
              ┌───────────┐
              │ aggregate │   融合（禁止暴露内部分工，AC-IB-09-03）
              └─────┬─────┘
                    ▼
                   END
```

## 「业务零依赖」是本图的硬约束（IFC-IB-231）

`build_graph()` **不构造任何业务内容**：人格文本、身份措辞、scope 绑定的工具
一律由调用方在**参数里**构造完成。这条纪律的收益很实在 —— 编排层不知道「谁是用户」、
「哪个项目」、「我们卖什么」，因此可以被任何接入方复用，且**单测时不需要造业务上下文**。

## 并行扇出用 `Send`，不用「循环 + 索引」

`_fan_out` 返回 `list[Send]`，LangGraph 会为每个 `Send` 起一个 `expert` 实例并行执行，
结果经 `Annotated[..., operator.add]` 归并。相比「循环调用 N 次」，这个写法的收益是
**并发性来自框架的结构而非手写线程**：并行度、异常隔离、结果归并顺序都由同一条声明决定。

## 为什么 `expert_results` 用 `operator.add` 归并

并行分支各自产出一部分结果，归并必须是**拼接**（`operator.add`）而非「后写覆盖前写」。
若用默认的覆盖语义，多个专家并行时只有一个的结果能活下来 —— 表现为
「明明路由到了两个专家，回答里只有一个的观点」，且不报任何错。

## 同步 vs 异步（R1 的现实约束）

冻结契约写的是 `AsyncIterator[StreamEvent]`，但 R1 把承载者定为
**Django 同步 WSGI + `StreamingHttpResponse`**（无 Channels/无 Redis）。
在同步 WSGI 线程里驱动 async 迭代器意味着要在视图里自建事件循环，收益为负、风险为正。
故本模块**以同步迭代器为主入口**（`run`），并保留 `arun` / `aresume`
（真异步迭代）以匹配契约形状并供支持 async 的宿主使用。两条路径共享**同一张图与同一套节点**，
不存在行为分叉。
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, Any, Iterator, Sequence, TypedDict

from ib.core import (
    ConfirmationDecision,
    ConfirmationGateState,
    ConfirmationPrompt,
    ExpertResult,
    GraphConfig,
    Message,
    RequestContext,
    RouteDecision,
    RouteTier,
    Scope,
    SessionState,
    SessionTurn,
    StartupError,
    StreamEventKind,
)

__all__ = [
    "MAX_EXPERT_STEPS",
    "GraphState",
    "Orchestrator",
    "build_graph",
    "run",
    "resume",
    "arun",
    "aresume",
    "StreamEvent",
    "AGGREGATION_FORBIDDEN_LABELS",
    # REV-16-2（IFC-IB-351）
    "forbidden_labels",
    # R8（IFC-IB-305 / 306）
    "ResumePayload",
    "can_resume",
]

#: 专家步数上限（module_design §7.1 明文常量；防「委托链」无限展开）。
#: 为什么是 8：单轮问答最多涉及 3 个专家（`MAX_ROUTE_EXPERTS`），每次专家最多 2 步
#: （检索 + 作答），再加聚合 —— 8 步足够覆盖最复杂的合法路径，又能拦住失控的委托环。
MAX_EXPERT_STEPS = 8

#: 聚合输出中**禁止出现**的**结构性**内部标识（AC-IB-09-03：不得暴露内部分工）。
#: 这些词一旦出现在用户可见回答里，就等于把「内部有几个专家、怎么分工」告诉了用户 ——
#: 既破坏产品一致性，也会让用户困惑「我到底在跟谁说话」。
#:
#: **REV-16-2 迁移态（ADR-31 Decision 第 4 条）**：专家中文标签的禁止集合**不再硬编码为
#: 唯一真源** —— 目标形态是由**活体专家注册表派生的只读视图** `forbidden_labels(cn_map)`
#: （IFC-IB-351；使骨架**不承载业务中文名**，对齐 ADR-09）。重构期间，本常量保留**结构性**
#: 词（路由 / 专家 / 聚合等），专家中文标签由 `forbidden_labels()` 并入；且必须取
#: **旧 ∪ 新** label 并集（`系统管家` / `巡检诊断` / `知识库问答` / `数据管家` / `三恒知识`），
#: 确保 AC-IB-09-03 **不回退**。**禁止只换名**（只删旧名或只加新名都会造成漏网或误伤）。
_STRUCTURAL_FORBIDDEN_LABELS = (
    "路由到",
    "专家",
    "expert",
    "router",
    "聚合",
    "agent",
)

#: **过渡态并集**（旧 ∪ 新专家中文标签）。重构完成（`forbidden_labels` 成为唯一来源）后，
#: 本常量可退化为空元组 —— 但在本增量内**必须保留并集**，否则历史回答里的旧标签会漏网。
_TRANSITION_EXPERT_LABELS = (
    # 旧名（改名前的专家中文标签；历史回答可能仍含）
    "数据管家",
    "知识库问答",
    "巡检诊断",
    # 新名（REV-16-2 FreeArk 对齐后的专家中文标签）
    "系统管家",
    "三恒知识",
)

#: 兼容常量（既有引用不变）：结构化禁止词 ∪ 过渡态并集。
AGGREGATION_FORBIDDEN_LABELS = _STRUCTURAL_FORBIDDEN_LABELS + _TRANSITION_EXPERT_LABELS


def forbidden_labels(cn_map: "dict[str, str]") -> tuple[str, ...]:
    """由**活体专家注册表**派生「聚合阶段禁止出现的专家中文标签」全集（IFC-IB-351）。

    **纯函数 / 派生视图**：替代硬编码清单，使骨架**不承载业务中文名**（对齐 ADR-09）。
    用途：AC-IB-09-03「不得暴露内部分工」。

    目标形态为「仅由 `cn_map` 派生」；**过渡态**（本增量）返回
    `结构化禁止词 ∪ 过渡态并集 ∪ cn_map 取值`，确保旧 / 新标签双向覆盖、不回退。
    """
    labels: list[str] = list(_STRUCTURAL_FORBIDDEN_LABELS)
    labels.extend(_TRANSITION_EXPERT_LABELS)
    if cn_map:
        labels.extend(cn_map.values())
    # 去重且保序（顺序稳定 → 清洗结果确定）
    seen: set[str] = set()
    ordered: list[str] = []
    for label in labels:
        if label and label not in seen:
            seen.add(label)
            ordered.append(label)
    return tuple(ordered)


def _active_forbidden_labels() -> tuple[str, ...]:
    """运行期取活体注册表标签并入（注册表未装配时退回过渡态并集）。"""
    try:
        from ib.experts import cn_map as _cn_map

        return forbidden_labels(_cn_map())
    except Exception:  # noqa: BLE001 - 清洗是兜底，派生失败不得让聚合失败
        return AGGREGATION_FORBIDDEN_LABELS


# --------------------------------------------------------------------------- #
# IFC-IB-305 / 306：恢复载荷与 fail-closed 判据（R8）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ResumePayload:
    """恢复载荷（IFC-IB-305）。

    **类型化** `IFC-IB-233` 的既有 `payload: dict`（**不改 `IFC-IB-233` 的签名文本与
    参数个数**，沿用 IFC-IB-282 的「只定义载荷类型、不改父签名」先例）。

    `decision is None` = **未携带决策**（`can_resume` 据此 fail-closed）。
    """

    session_key: str = ""
    decision: ConfirmationDecision | None = None

    @classmethod
    def from_dict(cls, raw: Any, *, session_key: str = "") -> "ResumePayload":
        """由原始 `dict`（HTTP 请求体 / 既有调用方）构造。

        容错解析：`decision` 支持 `ConfirmationDecision` 实例、或形如
        `{"gate_id": ..., "approved": bool}` 的映射；无法解析为一则**显式**决策时，
        `decision` 保持 `None`（即「未携带决策」，由 `can_resume` fail-closed 拒绝）——
        **绝不**把残缺载荷补成「默认批准」（那正是 AC-IB-20-05 明令禁止的「默认放行」）。
        """
        if isinstance(raw, ResumePayload):
            return raw
        data = raw if isinstance(raw, dict) else {}
        raw_decision = data.get("decision")
        decision: ConfirmationDecision | None = None
        if isinstance(raw_decision, ConfirmationDecision):
            decision = raw_decision
        elif isinstance(raw_decision, dict) and "gate_id" in raw_decision and "approved" in raw_decision:
            decision = ConfirmationDecision(
                gate_id=str(raw_decision.get("gate_id", "")),
                approved=bool(raw_decision.get("approved", False)),
            )
        return cls(
            session_key=str(data.get("session_key", session_key) or session_key),
            decision=decision,
        )


def can_resume(state: SessionState | None, gate_id: str, payload: ResumePayload | None) -> bool:
    """[IFC-IB-306] 是否允许恢复（**纯函数**，无 IO；fail-closed）。

    ## 三判据（任一不满足即 `False`；AC-IB-20-04 / 20-05）

    1. **状态丢失**：`state is None`（进程重启后内存后端读回 `None`）→ `False`；
    2. **归属不符**：`state.gate is None`（无待确认中间态）或 `state.gate.gate_id != gate_id`
       → `False`（决策/恢复请求指向的中间态与状态里的不是同一个 → 拒绝）；
    3. **未携决策**：`payload is None` 或 `payload.decision is None` → `False`。

    另加一条**fail-closed 加固**（实现决策，属保守方向、不放松任何判据）：
    `payload.decision.gate_id` 必须等于 `gate_id` —— 载荷里的决策不得指向**另一个**中间态。

    ## 为什么必须纯函数 + fail-closed

    该判据是「重启丢弃待确认状态 = 安全失败」的**唯一执行点**（AC-IB-20-05）。
    纯函数使其可离线穷举三判据的每一种组合；fail-closed 使其**默认拒绝** ——
    任何判据实现出错的后果是「拒绝恢复」（用户需重新发起），而非「静默执行未经确认的动作」。
    """
    if state is None:
        return False
    gate = getattr(state, "gate", None)
    if gate is None:
        return False
    if not gate_id or str(getattr(gate, "gate_id", "")) != str(gate_id):
        return False
    if payload is None or getattr(payload, "decision", None) is None:
        return False
    decision = payload.decision
    if str(getattr(decision, "gate_id", "")) != str(gate_id):
        return False
    return True


def _requested_gate_id(payload: ResumePayload | None, raw: Any) -> str:
    """恢复请求**指向的**中间态 id（`can_resume` 的 `gate_id` 入参；IFC-IB-306）。

    **必须是「请求指向的中间态」，而不是从 `state` 派生的中间态**：若从
    `state.gate` 派生 `gate_id` 再回传，`can_resume` 内「状态里的中间态 vs 请求指向的
    中间态」对账（`state.gate.gate_id != gate_id`）**恒为假而空转** —— 这正是本轮修复的
    病灶（请求指向别的中间态却仍被放行）。

    取自载荷的 `decision.gate_id`（决策是「恢复到哪个中间态」的权威声明）；决策未声明
    非空 `gate_id` 时回退到请求体显式的顶层 `gate_id`。均缺失则返回 `""` → `can_resume`
    fail-closed 拒绝。**不在此处判定**，判定权仍留给纯函数 `can_resume`。
    """
    decision = getattr(payload, "decision", None)
    requested = str(getattr(decision, "gate_id", "") or "")
    if not requested and isinstance(raw, dict):
        requested = str(raw.get("gate_id") or "")
    return requested


class GraphState(TypedDict, total=False):
    """图状态（module_design §7.1 明列的全部键）。

    reducer 只加在两个**并行归并**的键上（`messages` / `expert_results`）；
    其余键是单写者（route 写 `plan`/`route_tier`，gate 写 `step_count`），
    给它们加 `operator.add` 会让计数类字段被反复累加成天文数字。
    """

    messages: Annotated[list[Message], operator.add]
    expert_results: Annotated[list[ExpertResult], operator.add]
    plan: list[tuple[str, str]]
    route_tier: str
    query: str
    degraded: bool
    step_count: int


class Orchestrator:
    """编排服务的对外门面（IFC-IB-231 的产物）。

    持有编译后的图、会话存储、专家注册表视图与 scope 绑定工具。
    **每个请求**调用 `run()`；`scope` 与工具绑定在装配时（每请求）完成。
    """

    def __init__(
        self,
        *,
        graph: Any,
        router: Any,
        sessions: Any,
        config: GraphConfig,
        scope: Scope,
        llm: Any,
        tools_by_expert: dict[str, list[Any]] | None = None,
        related_images_provider: Any = None,
        confirmation_prompt_builder: Any = None,
    ) -> None:
        self._graph = graph
        self._router = router
        self._sessions = sessions
        self._config = config
        self._scope = scope
        self._llm = llm
        self._tools_by_expert = tools_by_expert or {}
        #: R2 增量接缝（**可选关键字**，缺省 `None` = 完全不发 `related_images` 事件）。
        self._related_images_provider = related_images_provider
        #: R8（ADR-17）确认话术构造器接缝（**可选关键字**）。缺省 `None` = 即使
        #: `confirmation_gate_enabled=True` 也**不触发**确认门（骨架不生成业务话术，
        #: 无话术构造器即无可呈递内容）。见 `docs/code_review_report.md` 设计缺口登记。
        self._confirmation_prompt_builder = confirmation_prompt_builder

    # ------------------------------------------------------------------ #
    # IFC-IB-232 同步主入口
    # ------------------------------------------------------------------ #

    def run(
        self, query: str, *, ctx: RequestContext, session_key: str
    ) -> Iterator[Any]:
        """[IFC-IB-232] 执行一轮问答，逐条产出 `StreamEvent`（同步迭代器）。

        事件顺序刻意固定：`reasoning`（进度）→ `confirmation_required`（仅确认门启用时）
        或 `degraded`（若有）→ `content`（最终答案）→ `related_images`（若有，R2）→ `done`。
        **`degraded` 必须在正文之前到达**：前端据此决定是否显示「当前未接入知识资料库」
        的提示条，若晚于正文到达，提示会出现在答案下方，用户会把它当成对答案的补充说明
        （语义完全错了）。同理 `related_images` **必须在 `content` 之后**：缩略图是对
        **已给出的回答**的补充，先出图会让用户先看到一堆图片再等答案（顺序反了）。

        **只发一条 `content`（最终答案），不逐专家发**。这一点是被实测行为逼出来的：
        若把每个专家的原始作答都作为 `content` 发出去、再发聚合结果，单专家场景下**同一段
        文字会出现两次**（聚合对单结果不改写），双专家场景下则是「先给两段、再给一段改写」
        ——用户看到的是答案被推翻重写。与其伪造逐字流式，不如让 UI 用 `reasoning` 显示
        「正在分析」，正文一次到位。

        R8：本方法委托给 `_run_inner(..., gate=True)`，使 `resume` 能复用同一实现但**跳过**
        确认门（否则续跑会再次触发确认门而自我死锁）。
        """
        yield from self._run_inner(query, ctx=ctx, session_key=session_key, gate=True)

    def _run_inner(
        self, query: str, *, ctx: RequestContext, session_key: str, gate: bool
    ) -> Iterator[Any]:
        """`run` 的实现体（`gate` 参数区分「新问答」与「恢复续跑」）。"""
        from ib.streaming import StreamEvent, completion_event

        history = self._load_history(session_key)
        decision = self._decide(query, history=history, scope=self._scope)

        # 路由事件（reasoning 折叠框内容；不含内部分工，只给进度感）
        yield StreamEvent(StreamEventKind.REASONING, "正在分析问题…")

        # R8（ADR-17）：确认中间态。开关关闭 / 无话术构造器 → 零行为差异（不触发）。
        if gate:
            gate_events = self._maybe_gate(query, decision, session_key=session_key, ctx=ctx)
            if gate_events is not None:
                for event in gate_events:
                    yield event
                return

        if not decision.experts:
            yield from self._run_general(query, session_key=session_key, history=history)
            return

        initial: GraphState = {
            "query": query,
            "messages": list(history) + [Message(role="user", content=query)],
            "expert_results": [],
            "plan": self._expand_plan(query, decision),
            "route_tier": str(decision.tier),
            "degraded": False,
            "step_count": 0,
        }
        collected: list[ExpertResult] = []
        for chunk in self._stream_graph(initial):
            for result in chunk.get("expert_results", []) or []:
                collected.append(result)
        # 降级提示（至多一条，且必须在正文之前）
        first_degraded = next((r for r in collected if r.degraded), None)
        if first_degraded is not None:
            for event in self._emit_degraded(first_degraded):
                yield event
        answer = self._aggregate(query, collected)
        yield StreamEvent(StreamEventKind.CONTENT, answer)
        for event in self._related_images_events():
            yield event
        self._save_history(session_key, history, query, answer, decision)
        # R8（IFC-IB-302）：终态经 `completion_event` 单发（`payload=None` → `data=""`，
        # 与既有 `StreamEvent(DONE)` 逐字节相同；未产出结构化产物即不臆造引用，AC-IB-19-05）。
        yield completion_event(None)

    def resume(self, session_key: str, payload: dict) -> Iterator[Any]:
        """[IFC-IB-233] 恢复被确认门挂起的会话。

        语义（R8；AC-IB-20-04 / 20-05）：
          * 确认门未开启 → `error` + `done`（**不静默成功** —— 静默成功会让调用方以为
            写操作已执行）；
          * 会话不存在 / 待确认状态丢失 / 未携决策 / 归属不符（`can_resume` = `False`）
            → `error` + `done`（**fail-closed**，**不新建会话、不重跑**）；
          * 三门全过且决策为**批准** → 自该中间态继续（复用 `_run_inner(gate=False)`）；
          * 三门全过但决策为**拒绝** → 明确终止，不执行待确认动作。

        载荷经 `ResumePayload.from_dict` 类型化；残缺载荷一律视为「未携决策」（fail-closed）。
        """
        from ib.streaming import StreamEvent, completion_event

        if not self._config.confirmation_gate_enabled:
            yield StreamEvent(
                StreamEventKind.ERROR,
                "确认门未开启（OQ-IB-07 默认关闭），无可恢复的挂起操作",
            )
            yield completion_event(None)
            return

        raw = payload or {}
        state = None
        try:
            state = self._sessions.load(session_key)
        except Exception:  # noqa: BLE001 - 存储读取失败即「状态不可得」→ fail-closed
            state = None
        resume_payload = ResumePayload.from_dict(raw, session_key=session_key)
        # 「请求指向的 gate_id」取自载荷决策（或请求体显式 gate_id），**不**从 state 派生 ——
        # 否则 can_resume 内的归属对账空转（见 `_requested_gate_id`）。
        gate_id = _requested_gate_id(resume_payload, raw)
        if not can_resume(state, gate_id, resume_payload):
            yield StreamEvent(
                StreamEventKind.ERROR,
                "会话不存在、待确认状态已丢失或未携带有效决策，无法恢复（fail-closed）",
            )
            yield completion_event(None)
            return

        decision = resume_payload.decision
        assert decision is not None  # can_resume 已保证
        if not decision.approved:
            # 决策为「拒绝」：不执行待确认动作，以可识别终态收束（**不续跑**）。
            yield StreamEvent(StreamEventKind.ERROR, "用户未批准该待确认动作，已终止且未执行")
            yield completion_event(None)
            return

        query = self._pending_query_of(state)
        ctx = raw.get("ctx")
        if ctx is None or not query:
            # 缺少续跑所需的上下文 / 原提问：**不臆造**，fail-closed。
            yield StreamEvent(StreamEventKind.ERROR, "缺少续跑上下文或原提问，无法恢复（fail-closed）")
            yield completion_event(None)
            return
        # 续跑：跳过确认门（否则再次触发确认而自我死锁）。
        yield from self._run_inner(query, ctx=ctx, session_key=session_key, gate=False)

    def _pending_query_of(self, state: SessionState) -> str:
        """待确认中间态所挂起的**原提问**（存于 `SessionState.turns` 的末条 user 轮）。

        续跑所需的「原提问」由骨架在挂起时写入 `turns`（见 `_persist_gate`）——
        这是**最小一致**的承载（设计未规定恢复载荷携带原提问，见报告设计缺口登记）。
        """
        for turn in reversed(tuple(getattr(state, "turns", ()) or ())):
            if str(getattr(turn, "role", "")) == "user" and str(getattr(turn, "text", "")):
                return str(turn.text)
        return ""

    # ------------------------------------------------------------------ #
    # R8（ADR-17）：确认中间态（装配语义见 module_design §3 MOD-IB-22）
    # ------------------------------------------------------------------ #

    def _maybe_gate(
        self, query: str, decision: RouteDecision, *, session_key: str, ctx: RequestContext
    ) -> Iterator[Any] | None:
        """确认门判定入口。返回 `None` = **不触发**（正常继续）；返回事件迭代器 = **已挂起**。

        ## 零行为差异的两种情形（任一即不触发）

        1. `confirmation_gate_enabled=False`（**默认**）—— ADR-17 约束 1。此时不写 `gate`
           状态、不发 `confirmation_required`，`resume` 亦不可用。
        2. 开关为 `True` 但组合根**未注入确认话术构造器** —— 骨架**不生成业务话术**
           （IFC-IB-301 / ADR-09），无话术即无可呈递内容，故不触发（而非呈递空话术）。

        ## 骨架不判定「哪些动作需要确认」

        业务判定由**注入的构造器**完成（`confirmation_prompt_builder`，组合根提供）：它返回
        `None` 表示本轮无需确认 → 不触发；返回 `ConfirmationPrompt` → 构造
        `ConfirmationGateState` 并挂起。骨架只做「构造 → 落状态 → 呈递一个事件」。

        **fail-closed**：开关已启用而话术构造**抛异常**时，**不**继续正常问答
        （继续会执行未经确认的动作），而是以 `error` + 终态安全终止。
        """
        if not bool(getattr(self._config, "confirmation_gate_enabled", False)):
            return None
        builder = self._confirmation_prompt_builder
        if builder is None:
            return None
        try:
            prompt = builder(query, decision=decision, scope=self._scope)
        except Exception as exc:  # noqa: BLE001 - 已启用确认门却无法造话术 → fail-closed
            from ib.observability import log_event

            log_event("chat", "confirmation_prompt_failed", error_type=type(exc).__name__)
            return self._gate_error_events("确认话术构造失败，已安全终止（fail-closed）")
        if prompt is None:
            return None
        gate_id = str(getattr(prompt, "gate_id", "") or "")
        if not gate_id:
            # 无法对账（resume 必然 fail-closed）的中间态不呈现 —— 呈递不可恢复的门是缺陷。
            return None
        gate = ConfirmationGateState(gate_id=gate_id, prompt=prompt, decision=None)
        self._persist_gate(session_key, gate, query=query)
        return self._gate_suspend_events(gate)

    def _gate_suspend_events(self, gate: ConfirmationGateState) -> Iterator[Any]:
        """挂起时的**恰一条** `confirmation_required` + 终态单发（保持流可正常收束）。"""
        from ib.streaming import completion_event, confirmation_required_event

        yield confirmation_required_event(gate)
        yield completion_event(None)

    def _gate_error_events(self, message: str) -> Iterator[Any]:
        """确认门 fail-closed 的可读失败（`error` + 终态单发；**不发 content**）。"""
        from ib.streaming import StreamEvent, completion_event

        yield StreamEvent(StreamEventKind.ERROR, message)
        yield completion_event(None)

    def _persist_gate(self, session_key: str, gate: ConfirmationGateState, *, query: str) -> None:
        """把待确认中间态写入会话（保留既有历史；同时记录原提问以便续跑）。

        * 既有 `messages` / `last_expert` / `sticky_turns_left` **原样保留**（不因挂起而丢历史）；
        * `turns` 追加一条 user 轮承载**原提问**（续跑用 `_pending_query_of` 取回）；
        * `session_key` / `project_id` / `updated_at` 一并补齐（`can_resume` / 归属断言需要）。

        写入失败**不抛**：与 `_save_history` 同口径 —— 会话写入不可用不该让请求 500。
        """
        try:
            prev = self._sessions.load(session_key)
        except Exception:  # noqa: BLE001
            prev = None
        from ib.streaming import project_of_session_key

        messages = list(getattr(prev, "messages", ()) or ())
        messages.append(Message(role="user", content=query))
        turns = tuple(getattr(prev, "turns", ()) or ()) + (
            SessionTurn(role="user", text=query, created_at=_now_iso()),
        )
        state = SessionState(
            messages=messages,
            last_expert=getattr(prev, "last_expert", None),
            sticky_turns_left=int(getattr(prev, "sticky_turns_left", 0) or 0),
            session_key=session_key,
            project_id=project_of_session_key(session_key),
            actor_id=str(getattr(prev, "actor_id", "") or ""),
            turns=turns,
            gate=gate,
            updated_at=_now_iso(),
        )
        try:
            self._sessions.save(session_key, state)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # REV-12-2（G2）：专家交接 —— 计划展开
    # ------------------------------------------------------------------ #

    def _expand_plan(self, query: str, decision: RouteDecision) -> list[tuple[str, str]]:
        """把「路由命中的专家」展开为图计划（含 G2 **单跳交接**，REV-12-2）。

        * **关闭**（`expert_handoff_enabled=False`，默认）→ 与既有行为**逐位一致**：
          `[(name, self._prompt_of(name)) for name in decision.experts]`（`is_delegating` 不参与）。
          这保证了「非交接的常规作答路径」在任何配置下都原样保留（护栏③）。
        * **开启** → 对每个命中且属 `delegating_experts()` 的专家，把其**默认同侪**
          （`default_expert()`）以**单跳**补入计划（若尚未在计划内）；计划条数受
          `min(config.max_expert_steps, MAX_EXPERT_STEPS)` 约束（**往返次数上限**，护栏①）。
          `_fan_out` 仍以 `step_count > max_expert_steps → general` 做二次上限校验（纵深防线）。

        护栏②（敏感写操作强制人工确认）**不在本函数内判定**：它复用确认门
        （`_maybe_gate` / IFC-IB-301/307/308，默认关闭）—— 骨架不判定「哪些动作需要确认」。

        **未决设计项（登记为缺口，不擅自决定）**：本函数**不判定「哪一轮需要交接」**；
        其触发仅由 `expert_handoff_enabled` 开关控制，交接目标取「默认同侪」这一确定性选择，
        并无业务触发规则（见 `docs/code_review_report.md` 设计缺口登记 GAP-R8-02）。
        """
        if not bool(getattr(self._config, "expert_handoff_enabled", False)):
            # 默认关闭：与 G2 之前**严格逐位零差异** —— 直接按 `decision.experts` 原序、原样
            # 展开，**不做去重 / 过滤**（任何 `seen` 去重都会让重复命中的计划被静默改写，
            # 从而让默认路径与既有行为产生差异，破坏「关闭即零行为差异」这条护栏③的前提）。
            return [
                (str(name), self._prompt_of(str(name))) for name in (decision.experts or ())
            ]

        from ib.experts import default_expert, delegating_experts

        # 开启分支：**保留**去重（避免同一专家被重复补入）与上限约束。
        base: list[str] = []
        seen: set[str] = set()
        for name in decision.experts or ():
            key = str(name)
            if key and key not in seen:
                base.append(key)
                seen.add(key)

        cap = max(1, min(int(getattr(self._config, "max_expert_steps", MAX_EXPERT_STEPS)), MAX_EXPERT_STEPS))
        delegating = set(delegating_experts())
        delegate = default_expert()
        expanded = list(base)
        if delegate:
            for name in list(base):
                if len(expanded) >= cap:
                    break
                if name in delegating and delegate not in seen:
                    expanded.append(delegate)
                    seen.add(delegate)
        return [(name, self._prompt_of(name)) for name in expanded]

    # ------------------------------------------------------------------ #
    # 异步变体（契约形状兼容；供支持 async 的宿主使用）
    # ------------------------------------------------------------------ #

    async def arun(self, query: str, *, ctx: RequestContext, session_key: str) -> Any:
        """真异步迭代版本（`run` 的 async 孪生；**同一张图、同一套节点**）。

        R8：与 `run` 共享 `_expand_plan` / 终态单发口径，使两条路径**不分叉**
        （确认门的呈递在 `run` 侧实现；async 宿主若需确认门，应经 `_maybe_gate` 同源扩展）。
        """
        from ib.streaming import StreamEvent, completion_event

        history = self._load_history(session_key)
        decision = self._decide(query, history=history, scope=self._scope)
        yield StreamEvent(StreamEventKind.REASONING, "正在分析问题…")
        if not decision.experts:
            for event in self._run_general(query, session_key=session_key, history=history):
                yield event
            return
        initial: GraphState = {
            "query": query,
            "messages": list(history) + [Message(role="user", content=query)],
            "expert_results": [],
            "plan": self._expand_plan(query, decision),
            "route_tier": str(decision.tier),
            "degraded": False,
            "step_count": 0,
        }
        collected: list[ExpertResult] = []
        async for chunk in self._astream_graph(initial):
            for result in chunk.get("expert_results", []) or []:
                collected.append(result)
        first_degraded = next((r for r in collected if r.degraded), None)
        if first_degraded is not None:
            for event in self._emit_degraded(first_degraded):
                yield event
        answer = self._aggregate(query, collected)
        yield StreamEvent(StreamEventKind.CONTENT, answer)
        for event in self._related_images_events():
            yield event
        self._save_history(session_key, history, query, answer, decision)
        yield completion_event(None)

    async def aresume(self, session_key: str, payload: dict) -> Any:
        """[IFC-IB-233] 的 async 孪生（与同步 `resume` 同口径，见其 docstring）。"""
        from ib.streaming import StreamEvent, completion_event

        if not self._config.confirmation_gate_enabled:
            yield StreamEvent(StreamEventKind.ERROR, "确认门未开启（OQ-IB-07 默认关闭）")
            yield completion_event(None)
            return
        raw = payload or {}
        try:
            state = self._sessions.load(session_key)
        except Exception:  # noqa: BLE001
            state = None
        resume_payload = ResumePayload.from_dict(raw, session_key=session_key)
        # 同 `resume`：gate_id 取「请求指向的中间态」，不从 state 派生（对账不得空转）。
        gate_id = _requested_gate_id(resume_payload, raw)
        if not can_resume(state, gate_id, resume_payload):
            yield StreamEvent(StreamEventKind.ERROR, "会话不存在或未携带有效决策，无法恢复（fail-closed）")
            yield completion_event(None)
            return
        decision = resume_payload.decision
        if decision is not None and not decision.approved:
            yield StreamEvent(StreamEventKind.ERROR, "用户未批准该待确认动作，已终止且未执行")
            yield completion_event(None)
            return
        query = self._pending_query_of(state)  # type: ignore[arg-type]
        ctx = raw.get("ctx")
        if ctx is None or not query:
            yield StreamEvent(StreamEventKind.ERROR, "缺少续跑上下文或原提问，无法恢复（fail-closed）")
            yield completion_event(None)
            return
        async for event in self.arun(query, ctx=ctx, session_key=session_key):
            yield event

    # ------------------------------------------------------------------ #
    # 内部：路由 / 图驱动 / 聚合 / 会话
    # ------------------------------------------------------------------ #

    def _decide(self, query: str, *, history: Sequence[Message], scope: Scope) -> RouteDecision:
        try:
            return self._router.classify_experts(query, history=history, scope=scope)
        except Exception:  # noqa: BLE001 - 路由失败不得让问答失败（REQ-FUNC-IB-19）
            from ib.experts import default_expert

            return RouteDecision(
                experts=[default_expert()], tier=RouteTier.DEFAULT, confidence=0.0
            )

    def _prompt_of(self, expert: str) -> str:
        """专家系统提示词。**REV-16-2（ADR-29）**：优先取跨域合并派生的**生效提示词**
        （`effective_prompt` = 主提示文件 > 兜底文件 > 定义文档兜底；装配期注入，IFC-IB-349）。
        未注入分层结果时回退既有 `spec.fallback_prompt`（R7 行为逐位不变）。
        """
        from ib.experts import fallback_prompts, get, prompt_bundles

        bundle = prompt_bundles().get(expert)
        if bundle is not None and bundle.effective_prompt.strip():
            return bundle.effective_prompt
        spec = get(expert)
        if spec is not None:
            return spec.fallback_prompt
        return fallback_prompts().get(expert, "")

    def _stream_graph(self, initial: GraphState) -> Iterator[dict]:
        """驱动已编译的图（同步），逐个产出**节点增量**（已剥掉节点名外壳）。

        `stream_mode="updates"` 的原始形状是 `{节点名: 该节点的状态增量}`，
        而并行扇出会让同一个 `expert` 节点名出现多次（每个 `Send` 一次）。
        调用方只关心增量内容，故在此处统一脱壳 —— 把「LangGraph 的流形状」这件事
        收在本方法里，`run()` 只面对「增量字典」。图不可用时降级为单个降级结果而非抛异常。
        """
        try:
            for chunk in self._graph.stream(initial, stream_mode="updates"):
                for _node, update in (chunk or {}).items():
                    if isinstance(update, dict):
                        yield update
        except Exception:  # noqa: BLE001 - 图执行异常不该让问答 500（fail-open）
            yield {"expert_results": [self._degraded_result("graph")]}

    async def _astream_graph(self, initial: GraphState) -> Any:
        try:
            async for chunk in self._graph.astream(initial, stream_mode="updates"):
                for _node, update in (chunk or {}).items():
                    if isinstance(update, dict):
                        yield update
        except Exception:  # noqa: BLE001
            yield {"expert_results": [self._degraded_result("graph")]}

    def _run_general(self, query: str, *, session_key: str, history: Sequence[Message]) -> Iterator[Any]:
        """通用应答路径（OOD 或路由为空）：不检索、不暴露分工。

        REV-12-2 护栏③：**不交接亦有人应答** —— 本路径在任何配置下都产出可读正文，
        使「无人应答」在结构上不可能（handoff 绝不是唯一出口）。
        """
        from ib.streaming import StreamEvent, completion_event

        text = self._general_answer(query)
        yield StreamEvent(StreamEventKind.CONTENT, text)
        self._save_history(
            session_key,
            history,
            query,
            text,
            RouteDecision(experts=[], tier=RouteTier.OOD, confidence=0.0),
        )
        yield completion_event(None)

    def _general_answer(self, query: str) -> str:
        try:
            role = self._llm.build_aggregator()
            impl = getattr(role, "impl", None)
            if impl is None:
                return "这个问题我不太确定，请补充一些细节，或换个更具体的问法。"
            prompt = f"请直接、简洁地回答下面的问题，不要提及任何内部分工或专家名称：\n{query}"
            result = impl.invoke(prompt) if hasattr(impl, "invoke") else impl(prompt)
            return _text_of(result) or "这个问题我不太确定，请补充一些细节。"
        except Exception:  # noqa: BLE001 - 通用应答失败也必须给出可读回退
            return "抱歉，暂时无法回答这个问题，请稍后再试。"

    def _degraded_result(self, reason: str) -> ExpertResult:
        return ExpertResult(
            expert="",
            content="",
            degraded=True,
            degrade_reason=reason,
        )

    def _emit_degraded(self, result: ExpertResult) -> Iterator[Any]:
        """降级事件（AC-IB-14-01：可见、措辞由服务端统一给出）。"""
        from ib.retrieval import DEGRADED_HINT
        from ib.streaming import degraded_event

        yield degraded_event(result.degrade_reason or "unknown", hint=DEGRADED_HINT)

    def _render(self, result: ExpertResult) -> str:
        """单个专家结果 → 用户可见文本。

        **多专家时不加任何人名/角色前缀**（AC-IB-09-03）：专家名一旦出现，
        用户就会开始追问「为什么是巡检专家回答我」，而内部分工是**实现细节**。
        天然的分段（空行）已足够让读者感到「这是几块内容的融合」。
        """
        if result.degraded and not result.content:
            return ""
        return result.content

    def _aggregate(self, query: str, results: Sequence[ExpertResult]) -> str:
        """融合多专家结果。**禁止暴露内部分工**（AC-IB-09-03）。

        只有一个专家时不调 LLM 二次加工：那只会增加延迟与「改写走样」的风险，
        没有任何信息增益。多专家时才融合，且输出经**确定性清洗**
        （`_strip_internal_labels`）—— 光靠提示词要求「不要提分工」不可靠，
        必须有一层确定性的兜底过滤。
        """
        texts = [self._render(result) for result in results if self._render(result)]
        if not texts:
            return "抱歉，暂时无法从知识库中获取答案，请稍后再试。"
        if len(texts) == 1:
            return _strip_internal_labels(texts[0], self._config)
        joined = "\n\n".join(texts)
        try:
            role = self._llm.build_aggregator()
            impl = getattr(role, "impl", None)
            if impl is None:
                return _strip_internal_labels(joined, self._config)
            prompt = (
                "把下面几点融合成一段连贯的回答。要求：不要提及任何内部分工、专家名称或角色；"
                "重复内容合并；保持事实不变。\n\n" + joined
            )
            merged = _text_of(impl.invoke(prompt) if hasattr(impl, "invoke") else impl(prompt))
            return _strip_internal_labels(merged or joined, self._config)
        except Exception:  # noqa: BLE001 - 聚合失败时退回「拼接」，不丢内容
            return _strip_internal_labels(joined, self._config)

    def _related_images_events(self) -> Iterator[Any]:
        """产出 `related_images` 事件（**至多一条**；无图 / 无 provider / 出错都不产出）。

        ## 为什么是「注入 provider」而不是「在这里查台账」

        编排层**不认识知识库**（模块文档「业务零依赖」）：它不知道 `doc_id`、
        `page_or_section`、URL 模板这些领域概念，也不该知道。故「命中 → 图片」的映射
        由组合根以 **provider 闭包** 注入（`ibweb/composition.orchestrator_for`），
        编排层只负责**在正确的时机**调用它并把结果发成事件。

        ## 时机与降级

        * 只在 `content` **之后**、`done` **之前**调用（IFC-IB-282）；
        * provider 抛异常 → **fail-open**：只记一条日志、不发事件。理由与检索降级一致 ——
          「图片没出来」不该让**已经产出的回答**失败，更不该中断 SSE 流
          （前端对「无图」与「取图失败」都只做静默隐藏，IFC-IB-284）。
        * 返回空载荷/`None` → 不发事件（「空即不发」在 `related_images_event` 内强制）。
        """
        if self._related_images_provider is None:
            return
        try:
            from ib.streaming import related_images_event

            payload = self._related_images_provider((), self._scope)
            event = related_images_event(payload)
        except Exception as exc:  # noqa: BLE001 - 取图失败不得影响已产出的回答
            from ib.observability import log_event

            log_event("chat", "related_images_failed", error_type=type(exc).__name__)
            return
        if event is not None:
            yield event

    def _load_history(self, session_key: str) -> list[Message]:
        """取会话历史（失败即空历史 —— 失去上下文只是体验降级，不该中断问答）。"""
        try:
            state = self._sessions.load(session_key)
        except Exception:  # noqa: BLE001
            return []
        if state is None:
            return []
        limit = max(0, int(self._config.max_history_messages))
        messages = list(state.messages)
        return messages[-limit:] if limit else []

    def _save_history(
        self,
        session_key: str,
        history: Sequence[Message],
        query: str,
        answer: str,
        decision: RouteDecision,
    ) -> None:
        """追加本轮消息并落会话（失败即忽略 —— 会话写入是 fail-closed 的**体验**功能，
        绝不因它不可用而让已经产出的回答丢失）。"""
        limit = max(0, int(self._config.max_history_messages))
        messages = list(history)
        messages.append(Message(role="user", content=query))
        messages.append(Message(role="assistant", content=answer))
        if limit:
            messages = messages[-limit:]
        last_expert = decision.experts[0] if decision.experts else None
        try:
            self._sessions.save(
                session_key,
                SessionState(
                    messages=messages,
                    last_expert=last_expert,
                    sticky_turns_left=max(0, int(self._config.max_history_messages) and 1 or 0),
                ),
            )
        except Exception:  # noqa: BLE001
            pass


# --------------------------------------------------------------------------- #
# IFC-IB-231 构图
# --------------------------------------------------------------------------- #

#: `build_graph` 的产物（进程内单例，供模块级 `run`/`resume` 使用 —— 契约规定
#: `run` 是模块级函数且不带图参数，故必须有一个装配期注入的引用）。
_ORCHESTRATOR: Orchestrator | None = None


def build_graph(
    *,
    llm: Any,
    experts: Any,
    tools: Sequence[Any],
    sessions: Any,
    config: GraphConfig,
    router: Any = None,
    scope: Scope | None = None,
    tools_by_expert: dict[str, list[Any]] | None = None,
    related_images_provider: Any = None,
    confirmation_prompt_builder: Any = None,
) -> Orchestrator:
    """[IFC-IB-231] 构造并编译编排图，返回可直接 `run()` 的 `Orchestrator`。

    **业务零依赖**：本函数不构造人格文本、不解析身份、不决定 scope ——
    全部由调用方在参数中给出（ADR-09 语义段）。
    `router` 缺省时按 `llm + 语义路由` 现造一个（便于最小装配与单测）。

    `related_images_provider` 是 **R2 新增的可选关键字**（向后兼容的超集，
    与 `submit_upload(data=...)` 的 `D-08` 同一先例）：缺省 `None` 时行为与 R1 逐字相同，
    不产出任何 `related_images` 事件。显式传 `None` 与不传等价 —— 不存在「必须显式关闭」的陷阱。

    `confirmation_prompt_builder` 是 **R8 新增的可选关键字**（同一「兼容超集」先例）：
    确认门的话术**构造器**（由接入方提供业务话术，骨架不生成，IFC-IB-301 / ADR-09）。
    缺省 `None` 时：即便 `config.confirmation_gate_enabled=True` 也**不触发**确认门
    （无可呈递内容）。**不使用 `confirmation_prompt_builder` 时 IFC-IB-231 的
    `GraphConfig` 传入参数与既有调用逐字相同**（R7 图配置约束不被绕过）。
    """
    if config is None:
        raise StartupError("GraphConfig 必填（缺失即启动失败，不静默使用默认步数上限）")
    if config.max_expert_steps <= 0:
        raise StartupError("GraphConfig.max_expert_steps 必须为正数")
    if sessions is None:
        raise StartupError("SessionStore 必填（缺失即启动失败）")
    if scope is None:
        raise StartupError("scope 必填（编排必须显式绑定访问范围，禁止运行期推断）")

    from ib.routing import IntentRouter

    effective_router = router or IntentRouter(llm_provider=llm, semantic=None)
    graph = _compile_graph(
        llm=llm,
        experts=experts,
        tools=list(tools),
        config=config,
        scope=scope,
        tools_by_expert=tools_by_expert or {},
    )
    orchestrator = Orchestrator(
        graph=graph,
        router=effective_router,
        sessions=sessions,
        config=config,
        scope=scope,
        llm=llm,
        tools_by_expert=tools_by_expert or {},
        related_images_provider=related_images_provider,
        confirmation_prompt_builder=confirmation_prompt_builder,
    )
    global _ORCHESTRATOR
    _ORCHESTRATOR = orchestrator
    return orchestrator


def _compile_graph(
    *,
    llm: Any,
    experts: Any,
    tools: list[Any],
    config: GraphConfig,
    scope: Scope,
    tools_by_expert: dict[str, list[Any]],
) -> Any:
    """编译 StateGraph（route → 条件边 fan-out → expert×N / general → gate → aggregate）。"""
    try:
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Send
    except Exception as exc:  # noqa: BLE001
        raise StartupError("langgraph 不可用（编排依赖）") from exc

    builder = StateGraph(GraphState)

    def _route(state: GraphState) -> dict:
        """route 节点：把计划与路由层级落到状态（真正的分类在 `Orchestrator._decide` 已完成）。

        图节点**不做 IO**（不调检索、不调 LLM）—— 分类结果由调用方在初始状态里给定。
        这不是偷懒：节点一旦带 IO，图就必须在装配了全部依赖的前提下才能测，
        而现在这张图可以只用「初始状态 + 假 llm」单测。
        """
        plan = list(state.get("plan") or [])
        # 计划条数即为本轮需要的专家步数；上限校验放在 `_fan_out`（它才是决策点）
        return {"plan": plan, "step_count": len(plan), "degraded": bool(state.get("degraded", False))}

    def _fan_out(state: GraphState) -> Any:
        """条件边：按计划并行扇出（AC-IB-09-02 复合意图同时命中多个专家）。

        超过步数上限时**不再扇出**，直接走 `general` —— 上限的意义是拦住失控的委托链，
        而「到达上限」本身不是错误，故不能抛异常（那会把可控的降级变成故障）。

        这里刻意**只返回 `Send` 列表、不返回专家名列表**：返回名称列表会被 LangGraph 当成
        「路由到某个叫这个名字的节点」而节点不存在；`Send` 才是「同一节点开多个实例」。
        """
        plan = list(state.get("plan") or [])
        if not plan or int(state.get("step_count", 0)) > config.max_expert_steps:
            return "general"
        return [
            Send("expert", {"query": state.get("query", ""), "expert": name, "prompt": prompt})
            for name, prompt in plan
        ]

    def _expert(payload: dict) -> dict:
        """expert 节点：单专家作答（工具已按 scope 绑定，此处只见无参工具）。

        并行分支**只能写带 reducer 的键**（这里是 `expert_results`）：多个实例同时写
        非 reducer 键会被 LangGraph 判为冲突而报错 —— 所以步数这类单值状态一律不在
        并行分支里写。
        """
        return {"expert_results": [_run_expert(payload, llm, tools_by_expert)]}

    def _general_node(state: GraphState) -> dict:
        return {
            "expert_results": [
                ExpertResult(
                    expert="",
                    content=_general_text(state.get("query", ""), llm),
                    degraded=False,
                    degrade_reason=None,
                )
            ]
        }

    def _gate(state: GraphState) -> dict:
        """gate 节点：步数上限判定 + 写操作确认门（默认关闭，OQ-IB-07）。

        确认门**默认关闭**是一个有意的最小权限选择：写操作（改设备参数）的风险远高于读，
        在没有人机确认流程之前，宁可让这类请求落到「专家声明自己无法执行」，
        也不要让模型自动改生产设备。

        本节点**回写 `{}`**（不重述上游结果）：重述会与 `operator.add` 归并叠加，
        使同一份专家结果在状态里出现两次 —— 表现为「回答里的每句话都重复了一遍」，
        而且不会报任何错。
        """
        return {}

    def _aggregate_node(state: GraphState) -> dict:
        """聚合节点：仅做顺序保证（最终文本融合在 `Orchestrator._aggregate` 里完成，
        以便聚合也走同一条「禁止暴露内部分工」的确定性清洗）。

        同样回写 `{}`（理由见 `_gate`）。
        """
        return {}

    builder.add_node("route", _route)
    builder.add_node("expert", _expert)
    builder.add_node("general", _general_node)
    builder.add_node("gate", _gate)
    builder.add_node("aggregate", _aggregate_node)
    builder.add_edge(START, "route")
    builder.add_conditional_edges("route", _fan_out, ["expert", "general"])
    builder.add_edge("expert", "gate")
    builder.add_edge("gate", "aggregate")
    builder.add_edge("general", "aggregate")
    builder.add_edge("aggregate", END)
    return builder.compile()


def _run_expert(payload: dict, llm: Any, tools_by_expert: dict[str, list[Any]]) -> ExpertResult:
    """执行一个专家：调用其 LLM 角色，附带该专家被授权工具的能力摘要。

    失败语义（严格按要求）：**降级而非抛出** —— 一个专家挂了不该让整轮问答失败，
    其他专家的结果仍然有用于用户（`degraded=True` 会让事件流里出现提示）。
    """
    expert = str(payload.get("expert", ""))
    query = str(payload.get("query", ""))
    prompt = str(payload.get("prompt", ""))
    try:
        from ib.experts import get

        spec = get(expert)
        if spec is None:
            return ExpertResult(
                expert=expert, content="", degraded=True, degrade_reason="unknown_expert"
            )
        role = llm.build_expert(spec)
        impl = getattr(role, "impl", None)
        if impl is None:
            return ExpertResult(expert=expert, content="", degraded=True, degrade_reason="llm_unavailable")
        tools = tools_by_expert.get(expert, [])
        full_prompt = f"{prompt}\n\n用户问题：{query}"
        # 工具调用循环：真正的 function-calling（LLM 自主决定是否/何时检索，多轮往返）。
        # 若 provider 未实现工具循环（离线替身 `FakeLlmProvider` 等），回退到单次文本补全 ——
        # 与既有行为逐位一致（替身的输出与 prompt 无关，见 llm._role_callable）。
        loop = getattr(impl, "run_tool_loop", None)
        if callable(loop) and tools:
            text = loop(full_prompt, tools=tools)
        else:
            result = impl.invoke(full_prompt) if hasattr(impl, "invoke") else impl(full_prompt)
            text = _text_of(result)
        if not text:
            return ExpertResult(expert=expert, content="", degraded=True, degrade_reason="empty_response")
        return ExpertResult(expert=expert, content=text, degraded=False, degrade_reason=None)
    except Exception as exc:  # noqa: BLE001 - 专家级失败必须降级（REQ-NFR-IB-13）
        reason = "timeout" if _is_timeout(exc) else "llm_unavailable"
        return ExpertResult(expert=expert, content="", degraded=True, degrade_reason=reason)


def _general_text(query: str, llm: Any) -> str:
    """通用回答（`general` 节点）。失败给出可读回退而非空串。"""
    try:
        role = llm.build_aggregator()
        impl = getattr(role, "impl", None)
        if impl is None:
            return "抱歉，暂时无法回答这个问题。"
        prompt = f"请直接、简洁地回答：\n{query}"
        text = _text_of(impl.invoke(prompt) if hasattr(impl, "invoke") else impl(prompt))
        return text or "抱歉，暂时无法回答这个问题。"
    except Exception:  # noqa: BLE001
        return "抱歉，暂时无法回答这个问题，请稍后再试。"


# --------------------------------------------------------------------------- #
# 模块级入口（IFC-IB-232 / 233 的契约形状）
# --------------------------------------------------------------------------- #


def run(query: str, *, ctx: RequestContext, session_key: str) -> Iterator[Any]:
    """[IFC-IB-232] 模块级入口（委托给 `build_graph` 装配的编排器）。"""
    if _ORCHESTRATOR is None:
        raise StartupError("编排器未装配：请先调用 build_graph()")
    return _ORCHESTRATOR.run(query, ctx=ctx, session_key=session_key)


def resume(session_key: str, payload: dict) -> Iterator[Any]:
    """[IFC-IB-233] 模块级入口。"""
    if _ORCHESTRATOR is None:
        raise StartupError("编排器未装配：请先调用 build_graph()")
    return _ORCHESTRATOR.resume(session_key, payload)


def arun(query: str, *, ctx: RequestContext, session_key: str) -> Any:
    """[IFC-IB-232] 的异步变体。"""
    if _ORCHESTRATOR is None:
        raise StartupError("编排器未装配：请先调用 build_graph()")
    return _ORCHESTRATOR.arun(query, ctx=ctx, session_key=session_key)


def aresume(session_key: str, payload: dict) -> Any:
    """[IFC-IB-233] 的异步变体。"""
    if _ORCHESTRATOR is None:
        raise StartupError("编排器未装配：请先调用 build_graph()")
    return _ORCHESTRATOR.aresume(session_key, payload)


# --------------------------------------------------------------------------- #
# 内部辅助
# --------------------------------------------------------------------------- #


def _strip_internal_labels(text: str, config: GraphConfig) -> str:
    """确定性清洗：去掉内部分工词汇（AC-IB-09-03 的兜底实现）。

    `aggregation_forbids_internal_labels=False` 时不清洗（供「明示分工」的内部调试模式）。
    清洗是**保守的**：只删词，不重写句子 —— 重写需要语义理解，而确定性代码给不出可靠的
    改写，宁可有轻微语句不顺，也不要引入新的事实错误。
    """
    if not config.aggregation_forbids_internal_labels or not text:
        return text
    cleaned = text
    for label in _active_forbidden_labels():
        cleaned = cleaned.replace(label, "")
    # 清洗后的多余空白收拢（避免出现「由  负责」这类空洞）
    return "\n".join(" ".join(line.split()) for line in cleaned.split("\n")).strip()


def _text_of(result: Any) -> str:
    """LLM 返回对象 → 文本（兼容 str / 带 `.content` 的消息 / 列表）。"""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    content = getattr(result, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(result, (list, tuple)) and result:
        return _text_of(result[0])
    return str(result)


def _is_timeout(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    return "timeout" in type(exc).__name__.lower() or "超时" in str(exc)


def _now_iso() -> str:
    """UTC 时间戳（ISO8601）。用于 `SessionState.updated_at` / `SessionTurn.created_at`。

    只取 UTC、带时区偏移，使跨进程/跨机器的会话时间戳**可直接比较**（本地时间会因时区
    不同而产生看似「时间倒流」的假象）。
    """
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


#: 延迟导入以便 `__all__` 暴露（`StreamEvent` 定义在 MOD-IB-21，避免循环 import）。
from ib.streaming import StreamEvent  # noqa: E402
