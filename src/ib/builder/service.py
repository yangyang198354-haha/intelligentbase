# MOD-R26-11 / implements IFC-R26-104：Builder 服务（生成 / 评估 / 优化 / 评审已有 agent）
"""对配置发布 / 任何写配置端口**无依赖**（类型层即无法发布，REQ-FUNC-021）：所有入口只产出草案与评审结果。

LLM 判定项结果经 `BuilderEvalCache` 持久化（OQ-R26-A04）：缓存期内同输入同分；LLM 不可用 / 超时 → 降级为
`coverage="rules_only"`，规则项照常给出。
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Callable, Literal, Mapping

from ib.core import ConfigSnapshot

from .adapt import RawDraft, adapt_draft, draft_to_fields, parse_raw_draft
from .egress import (
    BUILDER_INSTRUCTION_MAX_CHARS,
    EgressGuard,
    OutboundPayload,
    check_requirement,
)
from .rubric import LLM_CHECK_IDS, RUBRIC_VERSION, evaluate_draft, rubric_cache_key
from .types import (
    AdaptationNote,
    AgentDraft,
    BuilderBusy,
    BuilderUnavailable,
    EgressRejected,
    ExpertNotFound,
    FieldChange,
    ProjectContext,
    RubricResult,
)

__all__ = ["BuilderService"]

_ASSETS = Path(__file__).resolve().parent / "assets"


def _asset(name: str) -> str:
    return (_ASSETS / name).read_text(encoding="utf-8")


def _digest(text: str | None) -> str | None:
    if text is None:
        return None
    import hashlib

    return f"长度 {len(text)} · 哈希 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]}"


class BuilderService:
    def __init__(
        self,
        *,
        guard: EgressGuard,
        cache,
        context_provider: Callable[[str, str], ProjectContext],
        clock: Callable[[], str],
        model_id: str,
    ) -> None:
        self._guard = guard
        self._cache = cache
        self._ctx = context_provider
        self._clock = clock
        self._model_id = model_id

    # ------------------------------------------------------------------ #

    def generate(
        self, project_id: str, actor: str, requirement: str
    ) -> tuple[AgentDraft, tuple[AdaptationNote, ...], RubricResult]:
        req = check_requirement(requirement)
        ctx = self._ctx(project_id, actor)
        text = self._guard.send(
            OutboundPayload(kind="generate", requirement_text=req, project_digest=ctx),
            system=_asset("generate.md"), project_id=project_id, actor=actor,
        )
        draft, notes = adapt_draft(parse_raw_draft(text), ctx, source="generated")
        # [ASSUMPTION] 评分所用的适配说明一律由“最终草案”重新计算（与 /evaluate 同源），保证同一草案在生成结果与
        # 再次评估里得分一致；返回给用户的 `notes` 仍是本次适配实际移除 / 调整的清单。
        return draft, notes, self._rate(project_id, actor, draft, self._notes_for(draft, ctx), ctx, allow_llm=True)

    def evaluate(self, project_id: str, actor: str, draft: AgentDraft, *, allow_llm: bool = True) -> RubricResult:
        ctx = self._ctx(project_id, actor)
        notes = self._notes_for(draft, ctx)
        return self._rate(project_id, actor, draft, notes, ctx, allow_llm=allow_llm)

    def optimize(
        self, project_id: str, actor: str, draft: AgentDraft, instruction: str | None
    ) -> tuple[AgentDraft, tuple[AdaptationNote, ...], RubricResult, RubricResult, tuple[FieldChange, ...]]:
        """单轮优化，不自动循环。"""
        ctx = self._ctx(project_id, actor)
        return self._optimize(project_id, actor, draft, instruction, ctx, kind="optimize")

    def review_existing(
        self, project_id: str, actor: str, expert: str, mode: Literal["evaluate", "optimize"],
        instruction: str | None, *, published: ConfigSnapshot,
    ) -> tuple[RubricResult, AgentDraft | None, tuple[FieldChange, ...]]:
        """评审（或优化）已发布配置里的一个 agent：载荷只含被选 agent 的提示词与配置；服务端不写任何配置。"""
        ctx_full = self._ctx(project_id, actor)
        draft = _draft_of_existing(published, expert)
        # 评审对象自身不与自己“重名 / 标签撞车 / 关键词撞车”
        ctx = replace(ctx_full, agents=tuple(a for a in ctx_full.agents if a.name != expert))
        if mode == "evaluate":
            return self._rate(project_id, actor, draft, self._notes_for(draft, ctx), ctx, allow_llm=True), None, ()
        new, _notes, before, _after, changes = self._optimize(
            project_id, actor, draft, instruction, ctx, kind="review_existing"
        )
        return before, new, changes

    # ------------------------------------------------------------------ #

    def _notes_for(self, draft: AgentDraft, ctx: ProjectContext) -> tuple[AdaptationNote, ...]:
        """对（可能被用户编辑过的）草案重新计算适配说明——服务端不信任客户端回传的说明。"""
        _d, notes = adapt_draft(RawDraft(draft_to_fields(draft)), ctx, source="generated")
        return notes

    def _rate(
        self, project_id: str, actor: str, draft: AgentDraft, notes: tuple[AdaptationNote, ...],
        ctx: ProjectContext, *, allow_llm: bool,
    ) -> RubricResult:
        if not allow_llm:
            return evaluate_draft(draft, notes, ctx, llm_checks=None)
        key = rubric_cache_key(draft, notes, ctx, model_id=self._model_id)
        cached = self._cache.get(key)
        if cached is not None:
            try:
                checks = _checks_from_json(cached)
            except (ValueError, TypeError, KeyError):
                checks = None
            if checks is not None:
                return replace(evaluate_draft(draft, notes, ctx, llm_checks=checks), cache_hit=True)
        try:
            text = self._guard.send(
                OutboundPayload(kind="judge", selected_agent=draft, rubric_items=LLM_CHECK_IDS),
                system=_asset("judge.md"), project_id=project_id, actor=actor,
            )
            checks = _checks_from_raw(parse_raw_draft(text))
        except (BuilderUnavailable, BuilderBusy, EgressRejected):
            return evaluate_draft(draft, notes, ctx, llm_checks=None)  # 降级：只给规则项，如实标注 coverage
        self._cache.put(
            key, rubric_version=RUBRIC_VERSION, result_json=_checks_to_json(checks), now=self._clock()
        )
        return evaluate_draft(draft, notes, ctx, llm_checks=checks)

    def _optimize(
        self, project_id: str, actor: str, draft: AgentDraft, instruction: str | None, ctx: ProjectContext,
        *, kind: Literal["optimize", "review_existing"],
    ):
        instr = (instruction or "").strip()
        if len(instr) > BUILDER_INSTRUCTION_MAX_CHARS:
            raise EgressRejected("requirement_too_long")
        notes0 = self._notes_for(draft, ctx)
        before = self._rate(project_id, actor, draft, notes0, ctx, allow_llm=True)
        items = tuple(
            f"{d.dimension}/{d.check_id}: {d.evidence}" for d in before.deductions
        )[:30]
        text = self._guard.send(
            OutboundPayload(
                kind=kind, instruction_text=instr or None, project_digest=ctx, selected_agent=draft,
                rubric_items=items,
            ),
            system=_asset("optimize.md"), project_id=project_id, actor=actor,
        )
        raw = parse_raw_draft(text)
        fields = dict(raw.fields)
        fields["name"], fields["cn_label"] = draft.name, draft.cn_label  # 优化不改名
        new, notes = adapt_draft(RawDraft(fields), ctx, source="optimized")
        after = self._rate(project_id, actor, new, self._notes_for(new, ctx), ctx, allow_llm=True)
        return new, notes, before, after, _changes(draft, new)


def _checks_to_json(checks: Mapping[str, tuple[bool, str]]) -> str:
    return json.dumps({k: [bool(v[0]), v[1]] for k, v in sorted(checks.items())}, ensure_ascii=False)


def _checks_from_json(text: str) -> dict[str, tuple[bool, str]]:
    data = json.loads(text)
    return {str(k): (bool(v[0]), str(v[1])) for k, v in data.items() if k in LLM_CHECK_IDS}


def _checks_from_raw(raw: RawDraft) -> dict[str, tuple[bool, str]]:
    checks = raw.fields.get("checks")
    if not isinstance(checks, dict):
        raise BuilderUnavailable("parse_failed", "质检结果格式不正确")
    out: dict[str, tuple[bool, str]] = {}
    for cid in LLM_CHECK_IDS:
        item = checks.get(cid)
        if isinstance(item, dict):
            out[cid] = (bool(item.get("pass", True)), str(item.get("quote", ""))[:200])
        else:
            out[cid] = (True, "")
    return out


def _changes(old: AgentDraft, new: AgentDraft) -> tuple[FieldChange, ...]:
    out: list[FieldChange] = []
    for fld in ("main_prompt", "fallback_prompt"):
        a, b = getattr(old, fld), getattr(new, fld)
        if a != b:
            out.append(FieldChange(fld, _digest(a), _digest(b), "提示词已调整（段落级差异由前端持有两份文本时展示）"))
    for fld in ("keywords", "exemplars", "tool_names", "tool_params", "knowledge_folder_ids"):
        a, b = getattr(old, fld), getattr(new, fld)
        if a != b:
            out.append(FieldChange(fld, f"{len(a)} 项", f"{len(b)} 项", "列表字段已调整"))
    for fld in ("is_data_expert", "is_delegating", "max_steps"):
        a, b = getattr(old, fld), getattr(new, fld)
        if a != b:
            out.append(FieldChange(fld, str(a), str(b), "参数已调整"))
    return tuple(out)


def _draft_of_existing(snap: ConfigSnapshot, expert: str) -> AgentDraft:
    spec = next((e for e in snap.definition.experts if e.name == expert and e.status == "active"), None)
    if spec is None:
        raise ExpertNotFound(expert)
    layers = dict(snap.prompts).get(expert)
    grant = next((g for g in snap.definition.tool_grants if g.expert_name == expert), None)
    params: list[tuple[str, str | int | float | bool]] = []
    if grant is not None:
        params = [(p.name, p.value) for p in grant.param_values]
    return AgentDraft(
        name=spec.name, cn_label=spec.cn_label,
        main_prompt=(layers.main if layers and layers.main else "") or "",
        fallback_prompt=(layers.fallback if layers and layers.fallback else "") or "",
        keywords=tuple(spec.keywords), exemplars=tuple(spec.exemplars),
        is_data_expert=spec.is_data_expert, is_delegating=spec.is_delegating,
        tool_names=tuple(grant.tool_names) if grant else (), tool_params=tuple(params),
        knowledge_folder_ids=tuple(spec.knowledge_scope.folder_ids),
        max_steps=spec.max_steps if spec.max_steps is not None else 4, source="cloned",
    )
