"""
@module MOD-IB-19
@implements IFC-IB-201 classify_experts / 202 parse_route_output / 203 guard_against_misroute
@depends MOD-IB-01, MOD-IB-16, MOD-IB-17, MOD-IB-18
@author sub_agent_software_developer

意图路由内核（module_design.md §3 MOD-IB-19 / §7.2 四级降级表；REQ-FUNC-IB-19；
AC-IB-09-04/05/06/07、AC-IB-15-03）。

## 唯一不可违反的承诺：**任何一级失败都不得导致无人应答**

四级降级 + 粘性 + OOD + 默认专家的全部意义，就是让「绝不会有『没有专家回答』这一结局」
成为**结构性事实**：每一级的失败分支都指向下一级，最后一级（默认专家）是确定性兜底。
唯一例外是**可信的 OOD 信号**（显式 `[]`）—— 那是「有意交给通用应答节点」，
不是「没人应答」（§7.1 的 `general` 节点）。

## 「只看当前提问」：剥离历史

路由**绝不能**把对话历史喂给分类器。原因很具体：用户先问「能耗多少」，再问「那故障呢」，
若把历史拼进去，分类器会被前文的「能耗」带偏，把追问也判给能耗专家 —— 表现为
「用户明明换了话题，系统却还在答上一个话题」。因此：

  * `classify_experts(query=...)` 的 `query` **已经是当前提问**（由调用方剥离历史，
    组合根在 MOD-IB-23 用 IFC-IB-202 同族的 `current_query` 助手完成）；
  * `history` 只用于**受控例外**：粘性（承接上一轮专家）—— 且仅在当前提问**零信号**时生效。

## 三级兜底的优先级（高 → 低）

```
LLM 命中非空（经护栏修正）
  → 关键词命中（L0/L3）
    → 粘性（上一轮专家，仅当当前提问零信号）
      → 可信 OOD（LLM 显式 [] 且无关键词、无粘性）
        → 默认专家
```

**粘性优先于 OOD**：有上一轮专家时优先承接对话 —— 否则「那故障呢」这类极短追问会被
判为闲聊而掉进通用应答节点，用户感觉「聊到一半被甩出系统」。
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from ib.core import Message, RouteDecision, RouteTier, Scope

__all__ = [
    "parse_route_output",
    "guard_against_misroute",
    "IntentRouter",
    "MAX_ROUTE_EXPERTS",
    "current_query",
]

#: 单次路由最多选中的专家数（限制并发与成本；复合意图很少真的涉及三个以上领域）。
MAX_ROUTE_EXPERTS = 3

#: 从脏输出中抠出 JSON 数组（LLM 常在数组前后夹散文或 ```json 围栏）。
_JSON_ARRAY_RE = re.compile(r"\[.*?\]", re.DOTALL)

#: 历史前缀的常见标记（剥离历史时用）。组合根可替换为项目自己的标记。
_HISTORY_MARKERS = ("[历史对话]", "历史对话：", "【历史】")

#: 路由提示词模板。`{experts}`/`{capabilities}` 由注册表与工具表派生（单一真源）。
ROUTER_PROMPT = """你是意图路由分类器。可用专家：
{experts}

可用工具能力：
{capabilities}

规则：
1. 单一意图只选 1 个；只有明确同时涉及多个领域时才选多个。
2. 都不沾边则返回空数组 []。
3. 只输出 JSON 数组，元素是上面的专家 id（如 ["{first_expert}"]）。不要解释、不要代码围栏。

用户问题：{query}
"""


def current_query(text: str) -> str:
    """剥离历史前缀，只留**当前提问**（路由的唯一输入）。

    为什么需要显式剥离而不是「让调用方注意」：历史一旦进入路由输入，误路由是**静默**的
    —— 结果看起来合法（选中了某个专家），只是选错了。这类错误极难从日志发现，
    所以在入口处做一次确定性剥离，比指望每个调用点都记得更可靠。
    """
    if not text:
        return ""
    latest = text
    for marker in _HISTORY_MARKERS:
        index = latest.rfind(marker)
        if index >= 0:
            latest = latest[index + len(marker) :]
    # 兼底：多轮拼接常用“上一轮问：...”这类结构，取最后一个换行块之后的完整段落。
    for cut in ("\n用户：", "\nUser:", "\nHuman:"):
        index = latest.rfind(cut)
        if index >= 0:
            latest = latest[index + len(cut) :]
    return latest.strip()


# --------------------------------------------------------------------------- #
# IFC-IB-202 脏输出容错（纯函数）
# --------------------------------------------------------------------------- #


def parse_route_output(raw: str) -> list[str]:
    """[IFC-IB-202] 从 LLM 原始输出解析合法专家名（**去重保序**）；畸形输入返回 `[]`。

    为什么必须容错而不能「解析失败就报错」：路由 LLM 的输出是**自然语言模型的产物**，
    偶发地夹带散文、```json 围栏、多打一个数组是常态而非异常。把这类噪声升级为错误
    会让问答随机失败；而只取「能认出来的专家名」则退化得优雅：认出几个用几个，
    一个都没认出就走下一级兜底。

    实现要点：**遍历所有**数组片段（LLM 偶尔先输出一个示例数组再输出真实结果），
    返回**第一个**含合法专家的数组；若所有数组都合法但全为空/全是未知名，返回 `[]`
    （这为 OOD 判定保留「确实说了空数组」这一信息，见 `parse_route_output_ex`）。
    """
    names, _saw_array = parse_route_output_ex(raw)
    return names


def parse_route_output_ex(raw: str) -> tuple[list[str], bool]:
    """内部扩展：额外返回 `saw_array`（是否成功解析出**任一** JSON 数组）。

    `saw_array=True` 且无合法专家 = 「LLM 明确表态不属任何领域」→ 可信 OOD 信号；
    `saw_array=False` = 「输出无法解析」→ **不是** OOD，应继续走兜底（可能是模型抽风，
    不该因此把用户丢进通用应答）。
    这是本模块唯一超出 IFC-IB-202 契约的能力，作为**增量**提供，不改变契约行为。
    """
    from ib.experts import names as expert_names

    if not raw:
        return [], False
    valid = set(expert_names())
    saw_array = False
    for match in _JSON_ARRAY_RE.finditer(raw):
        try:
            payload = json.loads(match.group(0))
        except Exception:  # noqa: BLE001 - 该片段不是合法 JSON，继续找下一段
            continue
        if not isinstance(payload, list):
            continue
        saw_array = True
        seen: set[str] = set()
        out: list[str] = []
        for item in payload:
            if isinstance(item, str) and item in valid and item not in seen:
                seen.add(item)
                out.append(item)
        if out:
            return out[:MAX_ROUTE_EXPERTS], True
    return [], saw_array


# --------------------------------------------------------------------------- #
# IFC-IB-203 误路由护栏（纯函数）
# --------------------------------------------------------------------------- #


def guard_against_misroute(decision: RouteDecision, scores: dict[str, float]) -> RouteDecision:
    """[IFC-IB-203] 纠正两类**高置信**误路由。`scores` 为语义打分（可为 `{}`）。

    情形 1（无工具专家接了数据问题）：选中集合**全部**是无数据工具的专家，
    但语义打分显示某个**持数据工具**的专家明显更贴近 → 改派数据专家。
    真实故障形态：用户问「现在有多少故障」，却被答「我是知识库专家，无法查询实时数据」
    —— 用户看到的是**推诿**，体验上等同于故障。

    情形 2（数据问题落到了没有该工具的专家）：只选中一个数据专家，但它不在
    语义打分的前列，而另一个数据专家分数明显更高 → 改派之。
    真实故障形态：问「过去七天能耗」，路由到巡检专家，而巡检专家没有用量工具，
    只能答「我手头只能查设备状态」。

    **爆炸半径最小化**：只有当「语义打分**高置信**地指向另一个专家」时才介入。
    语义层不可用（`scores` 为空）时**一律不改** —— 护栏没有证据时不行动，
    否则它自己就成了新的误路由来源（用一个不确定的猜测覆盖 LLM 的明确判断）。

    `confidence` 与 `tier` 随改派更新：改派后应记为 `KEYWORD_FALLBACK` 级
    （确定性修正，而非模型判断），且置信度取新证据的分数，避免审计时把改派结果
    误读为「LLM 的判断」。
    """
    from ib.experts import data_experts

    if not decision.experts:
        return decision
    tools_owners = set(data_experts())
    if not tools_owners:
        return decision

    # 找一个**非当前选中**、但语义打分明显最高的数据专家
    candidate: str | None = None
    candidate_score = 0.0
    for name, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])):
        if name in tools_owners and name not in decision.experts:
            candidate = name
            candidate_score = float(score)
            break
    if candidate is None:
        return decision

    selected_all_tool_less = all(name not in tools_owners for name in decision.experts)
    selected_single_without_edge = len(decision.experts) == 1 and decision.experts[0] in tools_owners
    if not (selected_all_tool_less or selected_single_without_edge):
        return decision
    # 证据门槛：候选必须真的比当前选中更贴近（严格占优），否则不改派
    best_selected = max((float(scores.get(name, 0.0)) for name in decision.experts), default=0.0)
    if candidate_score <= best_selected:
        return decision
    return RouteDecision(
        experts=[candidate],
        tier=RouteTier.KEYWORD_FALLBACK,
        confidence=candidate_score,
    )


# --------------------------------------------------------------------------- #
# IFC-IB-201 路由入口
# --------------------------------------------------------------------------- #


class IntentRouter:
    """四级降级路由 + 粘性 + OOD + 默认专家（IFC-IB-201）。

    `llm_provider` 与 `semantic` 都是**可选的**：
      * `llm_provider=None` → 无 L2（LLM）能力，退化为「关键词 + 粘性 + 默认」；
      * `semantic=None` → 无 L1 能力，同时护栏失去语义证据（因此不介入）。
    两者皆无时路由仍然**永远不会无人应答** —— 这是本类的核心承诺。
    """

    def __init__(
        self,
        *,
        llm_provider: Any = None,
        semantic: Any = None,
        max_experts: int = MAX_ROUTE_EXPERTS,
    ) -> None:
        self._llm = llm_provider
        self._semantic = semantic
        self._max_experts = max(1, int(max_experts))

    # ------------------------------------------------------------------ #

    def classify_experts(
        self,
        query: str,
        *,
        history: Sequence[Message] = (),
        scope: Scope,
        allow_ood: bool = False,
    ) -> RouteDecision:
        """[IFC-IB-201] 返回 `RouteDecision`。**永不抛异常**。

        `allow_ood=True` 时允许返回 `experts=[]`（交给通用应答节点）；
        默认 `False` 表示「空结果按默认专家处理」（保守：宁可多用一个专家，也不要无人应答）。
        """
        from ib.experts import default_expert, names as expert_names

        try:
            text = current_query(query)
            valid = set(expert_names())

            # --- L0/L1：关键词唯一命中 → 语义高置信（都是「不必问 LLM」的快速路径） ---
            keyword_hits = self._keyword_hits(text)
            if len(keyword_hits) == 1:
                return RouteDecision(
                    experts=keyword_hits, tier=RouteTier.KEYWORD_UNIQUE, confidence=1.0
                )
            scores = self._semantic_scores(text, scope)
            if self._semantic is not None:
                picked = None
                try:
                    picked = self._semantic.route(text, scope=scope)
                except Exception:  # noqa: BLE001 - 语义层 fail-open，异常等同「不确定」
                    picked = None
                if picked in valid:
                    return RouteDecision(
                        experts=[picked],
                        tier=RouteTier.SEMANTIC,
                        confidence=float(scores.get(picked, 0.0)),
                    )

            # --- L2：LLM 分类（temperature=0） ---
            llm_names: list[str] = []
            llm_said_ood = False
            if self._llm is not None:
                raw = self._invoke_router(text)
                if raw:
                    llm_names, saw_array = parse_route_output_ex(raw)
                    llm_said_ood = saw_array and not llm_names
            if llm_names:
                decision = RouteDecision(
                    experts=llm_names[: self._max_experts],
                    tier=RouteTier.LLM,
                    confidence=0.0,
                )
                # 护栏只在「有语义证据」时介入（无证据不行动，避免护栏自身成为误路由源）
                return guard_against_misroute(decision, scores) if scores else decision

            # --- L3：关键词多重命中 ---
            if keyword_hits:
                return RouteDecision(
                    experts=keyword_hits[: self._max_experts],
                    tier=RouteTier.KEYWORD_FALLBACK,
                    confidence=0.0,
                )

            # --- 粘性：承接上一轮专家（仅当前提问零信号时） ---
            sticky = self._sticky_expert(history, valid)
            if sticky is not None:
                return RouteDecision(experts=[sticky], tier=RouteTier.STICKY, confidence=0.0)

            # --- 可信 OOD：LLM 明确表态不属任何领域，且无关键词、无粘性 ---
            if allow_ood and llm_said_ood:
                return RouteDecision(experts=[], tier=RouteTier.OOD, confidence=0.0)

            # --- 默认专家（确定性兜底，绝不留「无人应答」） ---
            fallback = default_expert()
            return RouteDecision(experts=[fallback], tier=RouteTier.DEFAULT, confidence=0.0)
        except Exception:  # noqa: BLE001 - IFC-IB-201 要求无异常出口
            from ib.experts import default_expert

            return RouteDecision(
                experts=[default_expert()], tier=RouteTier.DEFAULT, confidence=0.0
            )

    # ------------------------------------------------------------------ #

    def _keyword_hits(self, text: str) -> list[str]:
        """按注册表关键词命中的专家（保注册表顺序，确定性）。"""
        from ib.experts import keywords_map

        lowered = text.lower()
        hits: list[str] = []
        for expert, keywords in keywords_map().items():
            if any(keyword.lower() in lowered for keyword in keywords):
                hits.append(expert)
        return hits

    def _semantic_scores(self, text: str, scope: Scope) -> dict[str, float]:
        """语义打分（供护栏用）。不可用时 `{}`（等同无证据）。"""
        if self._semantic is None:
            return {}
        try:
            return self._semantic.scores_for(text, scope=scope)
        except Exception:  # noqa: BLE001
            return {}

    def _sticky_expert(self, history: Sequence[Message], valid: set[str]) -> str | None:
        """粘性：从**历史**里推断「上一轮用户问题」命中的专家。

        取**最后一条用户消息**而不是「上一轮专家状态」：历史里没有「上轮专家」字段
        （那是会话状态，由 MOD-IB-21 持有），故从最后一条用户提问反推 —— 与 FreeArk
        生产实现同构，且不引入新的状态耦合。
        """
        if not history:
            return None
        last_user = None
        for message in reversed(list(history)):
            if getattr(message, "role", "") in ("user", "human"):
                last_user = message
                break
        if last_user is None:
            return None
        hits = self._keyword_hits(current_query(str(getattr(last_user, "content", ""))))
        for name in hits:
            if name in valid:
                return name
        return None

    def _invoke_router(self, text: str) -> str:
        """调用路由 LLM 角色，返回原始文本。任何失败返回 `""`（→ 走下一级兜底）。

        调用形态的兼容层：`LlmRole.impl` 由 MOD-IB-20 提供，可能是 langchain 的
        `Runnable`（`.invoke`）或普通可调用对象。这里容忍两种形态，**不**在
        MOD-IB-19 里 import langchain（保持 framework-free，可离线单测）。
        """
        try:
            role = self._llm.build_router()
        except Exception:  # noqa: BLE001
            return ""
        impl = getattr(role, "impl", None)
        if impl is None:
            return ""
        prompt = ROUTER_PROMPT.format(
            experts=self._expert_lines(),
            capabilities=self._capability_digest(),
            first_expert=self._first_expert(),
            query=text,
        )
        try:
            if hasattr(impl, "invoke"):
                result = impl.invoke(prompt)
            elif callable(impl):
                result = impl(prompt)
            else:
                return ""
            return _text_of(result)
        except Exception:  # noqa: BLE001 - 路由分类失败必须降级而非中断
            return ""

    @staticmethod
    def _expert_lines() -> str:
        from ib.experts import EXPERT_SPECS

        return "\n".join(
            f"- {spec.name}（{spec.cn_label}）：关键词 {'/'.join(spec.keywords[:8])}"
            for spec in EXPERT_SPECS
        )

    @staticmethod
    def _capability_digest() -> str:
        from ib.tools import build_capability_digest

        return build_capability_digest() or "（无可用工具）"

    @staticmethod
    def _first_expert() -> str:
        from ib.experts import names

        return names()[0]


def _text_of(result: Any) -> str:
    """把 LLM 返回对象压成文本（兼容 str / 带 `.content` 的消息对象 / 列表）。"""
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
