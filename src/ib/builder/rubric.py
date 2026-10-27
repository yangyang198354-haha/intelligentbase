# MOD-R26-11 / implements IFC-R26-103：自评（五维；94 分规则项 + 6 分 LLM 判定项，OQ-R26-A04）
"""自评 `r26.1`。**规则项同输入必然同分**；LLM 判定项（3 项 × 2 分）的结果由服务层持久化缓存，缓存期内同输入同分；
缓存失效后的残余差异如实标注（`coverage` / `cache_hit`）。每条扣分必须带 evidence，无 evidence 不扣分。

维度满分：完整性与格式 20 / 项目适配度 25 / 路由质量 15 / 提示词质量 25（规则 19 + LLM 6）/ 安全与约束 15。
`llm_checks is None` → `coverage="rules_only"`：LLM 项不计分也不扣分，总分按规则项满分 94 折算为 100 制。
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Final, Mapping, Sequence

from .egress import contains_secret_pattern
from .types import AdaptationNote, AgentDraft, Deduction, ProjectContext, RubricResult

__all__ = ["RUBRIC_VERSION", "LLM_CHECK_IDS", "RULE_MAX", "evaluate_draft", "rubric_cache_key"]

RUBRIC_VERSION: Final[str] = "r26.1"
LLM_CHECK_IDS: Final[tuple[str, ...]] = (
    "prompt_role_consistent",
    "prompt_no_contradiction",
    "prompt_no_guardrail_conflict",
)
_LLM_POINTS = 2
RULE_MAX: Final[int] = 94
_MAX = {"completeness": 20, "adaptation": 25, "routing": 15, "prompt": 25, "safety": 15}
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")
_PLACEHOLDER = ("todo", "xxx", "lorem", "占位", "待补充", "此处填写")
_OVERRIDE = ("忽略之前的指令", "忽略以上指令", "ignore previous", "ignore all previous", "无视系统")
_ROLE = ("你是", "你的角色", "角色", "you are")


def _ev(s: str) -> str:
    return s if len(s) <= 200 else s[:199] + "…"


def _kw_norm(k: str) -> str:
    return k.strip().lower()


def evaluate_draft(
    draft: AgentDraft,
    notes: Sequence[AdaptationNote],
    ctx: ProjectContext,
    *,
    llm_checks: Mapping[str, tuple[bool, str]] | None,
) -> RubricResult:
    ded: list[Deduction] = []
    score = dict(_MAX)  # 先给满分再扣
    if llm_checks is None:
        score["prompt"] -= len(LLM_CHECK_IDS) * _LLM_POINTS  # 规则口径下 prompt 满分 19

    def deduct(dim: str, check: str, field: str, pts: int, evidence: str) -> None:
        ev = _ev(evidence.strip())
        if not ev or pts <= 0:
            return  # 无 evidence 不产生扣分
        take = min(pts, score[dim])
        if take <= 0:
            return
        score[dim] -= take
        ded.append(Deduction(dim, check, field, take, ev))  # type: ignore[arg-type]

    c = ctx.constraints
    lo, hi = c.max_steps_range

    # ---- D1 完整性与格式（20） ----
    if not _NAME_RE.match(draft.name):
        deduct("completeness", "name_format", "name", 4, f"name={draft.name[:48]!r} 不符合命名规则")
    if not draft.cn_label.strip() or len(draft.cn_label) > 32:
        deduct("completeness", "label_present", "cn_label", 3, f"中文标签长度 {len(draft.cn_label)}（须 1..32）")
    if not draft.main_prompt.strip():
        deduct("completeness", "main_prompt_present", "main_prompt", 5, "主提示词为空")
    if not draft.fallback_prompt.strip():
        deduct("completeness", "fallback_prompt_present", "fallback_prompt", 3, "兜底提示词为空")
    for fld, text in (("main_prompt", draft.main_prompt), ("fallback_prompt", draft.fallback_prompt)):
        if len(text) > c.prompt_max_chars:
            deduct("completeness", "length_limits", fld, 3, f"{fld} 长度 {len(text)} 超过 {c.prompt_max_chars}")
            break
    if not (lo <= draft.max_steps <= hi):
        deduct("completeness", "max_steps_valid", "max_steps", 2, f"max_steps={draft.max_steps} 不在 {lo}..{hi}")

    # ---- D2 项目适配度（25）：证据 = 适配说明条目 ----
    weights = {
        "tool_removed": ("adaptation", "tool_adapted", "tool_names", 2, 6),
        "folder_removed": ("adaptation", "folder_adapted", "knowledge_folder_ids", 2, 5),
        "param_adjusted": ("adaptation", "param_adapted", "tool_params", 2, 4),
        "steps_adjusted": ("adaptation", "steps_adapted", "max_steps", 2, 2),
        "name_conflict": ("adaptation", "name_unique", "name", 4, 4),
        "label_conflict": ("adaptation", "label_unique", "cn_label", 4, 4),
    }
    spent: dict[str, int] = {}
    for n in notes:
        spec = weights.get(n.code)
        if spec is None:
            continue
        dim, check, fld, per, cap = spec
        room = cap - spent.get(check, 0)
        if room > 0:
            take = min(per, room)
            spent[check] = spent.get(check, 0) + take
            deduct(dim, check, fld, take, n.message)

    # ---- D3 路由质量（15） ----
    if not draft.keywords:
        deduct("routing", "keywords_present", "keywords", 5, "未提供任何路由关键词")
    others = {_kw_norm(k): a.name for a in ctx.agents if a.name != draft.name for k in a.keywords}
    clash = next((k for k in draft.keywords if _kw_norm(k) in others), None)
    if clash is not None:
        deduct("routing", "keywords_no_collision", "keywords", 5, f"关键词「{clash[:32]}」与 agent「{others[_kw_norm(clash)]}」撞车")
    if len(draft.exemplars) < 2:
        deduct("routing", "exemplars_min", "exemplars", 3, f"示例句 {len(draft.exemplars)} 条（建议 >= 2）")
    norm_kws = [_kw_norm(k) for k in draft.keywords]
    if len(set(norm_kws)) != len(norm_kws) or any(len(k) > 32 or not k for k in norm_kws):
        deduct("routing", "keywords_clean", "keywords", 2, "关键词存在重复 / 空 / 超长项")

    # ---- D4 提示词质量（规则 19） ----
    low = draft.main_prompt.lower()
    if len(draft.main_prompt.strip()) < 50:
        deduct("prompt", "prompt_min_length", "main_prompt", 4, f"主提示词仅 {len(draft.main_prompt.strip())} 字符（建议 >= 50）")
    if not any(r in low for r in _ROLE):
        deduct("prompt", "prompt_role_stated", "main_prompt", 3, "主提示词未说明角色（如“你是……”）")
    retrieval = {t.name for t in ctx.tools if t.is_retrieval}
    if retrieval & set(draft.tool_names):
        for clause_id, alts in c.grounding_clauses:
            if not any(a in draft.main_prompt for a in alts):
                deduct("prompt", f"clause_{clause_id}", "main_prompt", 3, f"检索类 agent 的主提示词缺少条款 {clause_id}")
    hit = next((p for p in _PLACEHOLDER if p in low), None)
    if hit is not None:
        deduct("prompt", "prompt_no_placeholder", "main_prompt", 3, f"主提示词含占位文本「{hit}」")
    if llm_checks is not None:
        for cid in LLM_CHECK_IDS:
            passed, quote = llm_checks.get(cid, (True, ""))
            if not passed:
                deduct("prompt", cid, "main_prompt", _LLM_POINTS, quote)  # 无引用片段则不扣分

    # ---- D5 安全与约束（15） ----
    blob = "\n".join([draft.main_prompt, draft.fallback_prompt, draft.cn_label, *draft.keywords, *draft.exemplars])
    bl = blob.lower()
    term = next((t for t in c.blocked_terms if t.lower() in bl), None)
    if term is not None:
        deduct("safety", "no_business_terms", "main_prompt", 5, "文本含不允许的业务专有词")
    if contains_secret_pattern(blob):
        deduct("safety", "no_secret_text", "main_prompt", 5, "文本疑似含密钥 / 口令")
    ov = next((p for p in _OVERRIDE if p in bl), None)
    if ov is not None:
        deduct("safety", "no_override_phrase", "main_prompt", 3, f"主提示词含越权措辞「{ov}」")
    known = {t.name for t in ctx.tools}
    bad = [t for t in draft.tool_names if t not in known]
    if bad:
        deduct("safety", "tools_known", "tool_names", 2, f"工具「{bad[0][:40]}」不在本项目")

    rule_total = sum(score.values())
    if llm_checks is None:
        total = round(rule_total * 100 / RULE_MAX)
        coverage = "rules_only"
    else:
        total = rule_total
        coverage = "full"
    total = max(0, min(100, total))
    grade = "fail" if total < 60 else ("excellent" if total >= 90 else "pass")
    return RubricResult(
        rubric_version=RUBRIC_VERSION,
        total=total,
        grade=grade,  # type: ignore[arg-type]
        dimension_scores=dict(score),
        deductions=tuple(ded),
        coverage=coverage,  # type: ignore[arg-type]
        cache_hit=False,
    )


def rubric_cache_key(draft: AgentDraft, notes: Sequence[AdaptationNote], ctx: ProjectContext, *, model_id: str) -> str:
    """评审缓存键：同 (草案, 适配说明, 项目上下文, 模型) → 同键。上下文只取影响评审的部分（agent 名 / 标签 / 关键词 / 工具名）。"""
    payload = {
        "v": RUBRIC_VERSION,
        "model": model_id,
        "draft": [
            draft.name, draft.cn_label, draft.main_prompt, draft.fallback_prompt, list(draft.keywords),
            list(draft.exemplars), draft.is_data_expert, draft.is_delegating, list(draft.tool_names),
            [list(p) for p in draft.tool_params], list(draft.knowledge_folder_ids), draft.max_steps,
        ],
        "notes": sorted([n.code, n.field] for n in notes),
        "ctx": {
            "agents": sorted([a.name, a.cn_label, list(a.keywords)] for a in ctx.agents),
            "tools": sorted([t.name, t.is_retrieval] for t in ctx.tools),
        },
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "rb-" + hashlib.sha256(blob.encode("utf-8")).hexdigest()
