# MOD-R26-11 / implements IFC-R26-102：把未信任的模型输出适配为合法草案（纯函数）
"""适配器：**任何来自模型的字符串都当不可信文本**（REQ-NFUNC-008）——不执行、不解释为权限。

规则：不存在的工具 → 移除；目录名 → 在项目目录内按 NFC + casefold 匹配到 folder_id，匹配不到 → 移除；
工具参数未声明 / 越界 / 类型不符 → 调整为默认值（无默认则移除）；max_steps 越界 → 默认 4；name / 中文标签与现有 agent
重复 → 保留值并标记（**不覆盖**，加入画布前须改名）；检索类缺三项条款 → clause_missing；业务专有词 → term_blocked；
字段超长 → 截断。
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from .types import AdaptationNote, AgentDraft, BuilderUnavailable, ParamDigest, ProjectContext

__all__ = ["RawDraft", "parse_raw_draft", "adapt_draft", "draft_to_fields"]

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")
_KW_MAX, _KW_ITEM_MAX, _EX_MAX, _EX_ITEM_MAX, _LABEL_MAX = 20, 32, 10, 200, 32


@dataclass(frozen=True, slots=True)
class RawDraft:
    fields: Mapping[str, Any]


def parse_raw_draft(text: str) -> RawDraft:
    """容错解析：剥代码围栏 / 前后缀文字，取第一个完整 JSON 对象。失败 → BuilderUnavailable(parse_failed)。"""
    s = (text or "").strip()
    s = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", s)
    start = s.find("{")
    if start < 0:
        raise BuilderUnavailable("parse_failed", "模型输出不是 JSON")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(s[start : i + 1])
                except json.JSONDecodeError as exc:
                    raise BuilderUnavailable("parse_failed", "模型输出不是合法 JSON") from exc
                if not isinstance(obj, dict):
                    raise BuilderUnavailable("parse_failed", "模型输出不是 JSON 对象")
                return RawDraft(fields=obj)
    raise BuilderUnavailable("parse_failed", "模型输出的 JSON 不完整")


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).casefold().strip()


def _str(v: Any) -> str:
    return v if isinstance(v, str) else ("" if v is None else str(v))


def _str_list(v: Any) -> list[str]:
    if not isinstance(v, (list, tuple)):
        return []
    return [x.strip() for x in v if isinstance(x, str) and x.strip()]


def _coerce_param(spec: ParamDigest, value: Any) -> str | int | float | bool | None:
    """按声明类型 / 范围收敛取值；不合法返回 None（调用方改用默认值）。"""
    try:
        if spec.type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.lower() in ("true", "false"):
                return value.lower() == "true"
            return None
        if spec.type in ("int", "float"):
            if isinstance(value, bool):
                return None
            num = float(value)
            if spec.type == "int":
                if num != int(num):
                    return None
                num = int(num)
            if (spec.minimum is not None and num < spec.minimum) or (spec.maximum is not None and num > spec.maximum):
                return None
            return num
        text = _str(value)
        if spec.choices and text not in spec.choices:
            return None
        return text
    except (TypeError, ValueError):
        return None


def adapt_draft(
    raw: RawDraft, ctx: ProjectContext, *, source: Literal["generated", "optimized"]
) -> tuple[AgentDraft, tuple[AdaptationNote, ...]]:
    f, c = raw.fields, ctx.constraints
    notes: list[AdaptationNote] = []

    def note(code: str, field: str, msg: str) -> None:
        notes.append(AdaptationNote(code, field, msg))  # type: ignore[arg-type]

    # ---- name / 标签（冲突只标记，不覆盖） ----
    name = re.sub(r"[^a-z0-9_-]+", "-", _str(f.get("name")).strip().lower()).strip("-_")[:48] or "new-agent"
    if not _NAME_RE.match(name):
        name = "new-agent"
    if name in c.reserved_names or any(a.name == name for a in ctx.agents):
        note("name_conflict", "name", f"name「{name}」与现有 agent 或保留名重复，加入画布前须改名")
    label = _str(f.get("cn_label")).strip()
    if len(label) > _LABEL_MAX:
        label = label[:_LABEL_MAX]
        note("truncated", "cn_label", "中文标签超过 32 字符，已截断")
    if label and any(_norm(a.cn_label) == _norm(label) for a in ctx.agents):
        note("label_conflict", "cn_label", f"中文标签「{label}」与现有 agent 重复，加入画布前须改名")

    # ---- 提示词（超长截断） ----
    main = _str(f.get("main_prompt")).strip()
    fb = _str(f.get("fallback_prompt")).strip()
    if len(main) > c.prompt_max_chars:
        main = main[: c.prompt_max_chars]
        note("truncated", "main_prompt", f"主提示词超过 {c.prompt_max_chars} 字符，已截断")
    if len(fb) > c.prompt_max_chars:
        fb = fb[: c.prompt_max_chars]
        note("truncated", "fallback_prompt", f"兜底提示词超过 {c.prompt_max_chars} 字符，已截断")

    # ---- 路由字段 ----
    kws = [k[:_KW_ITEM_MAX] for k in _str_list(f.get("keywords"))]
    if len(kws) > _KW_MAX:
        kws = kws[:_KW_MAX]
        note("truncated", "keywords", f"关键词超过 {_KW_MAX} 条，已截断")
    exs = [e[:_EX_ITEM_MAX] for e in _str_list(f.get("exemplars"))]
    if len(exs) > _EX_MAX:
        exs = exs[:_EX_MAX]
        note("truncated", "exemplars", f"示例句超过 {_EX_MAX} 条，已截断")

    # ---- 工具 / 参数 ----
    tool_by_name = {t.name: t for t in ctx.tools}
    tools: list[str] = []
    for t in _str_list(f.get("tool_names")):
        if t in tool_by_name:
            if t not in tools:
                tools.append(t)
        else:
            note("tool_removed", "tool_names", f"工具「{t[:40]}」不存在于本项目，已移除")
    specs = {p.name: p for t in tools for p in tool_by_name[t].params}
    specs_bare = {p.name.split(".", 1)[-1]: p for p in specs.values()}
    params: list[tuple[str, str | int | float | bool]] = []
    seen: set[str] = set()
    raw_params = f.get("tool_params")
    for item in raw_params if isinstance(raw_params, (list, tuple)) else []:
        if not (isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], str)):
            continue
        pname, value = item[0], item[1]
        spec = specs.get(pname) or specs_bare.get(pname)
        if spec is None:
            note("param_adjusted", "tool_params", f"参数「{pname[:40]}」未被所选工具声明，已移除")
            continue
        coerced = _coerce_param(spec, value)
        if coerced is None:
            if spec.default is None:
                note("param_adjusted", "tool_params", f"参数「{spec.name}」取值不合法且无默认值，已移除")
                continue
            coerced = spec.default
            note("param_adjusted", "tool_params", f"参数「{spec.name}」取值越界或类型不符，已调整为默认值")
        if spec.name not in seen:
            seen.add(spec.name)
            params.append((spec.name, coerced))

    # ---- 知识范围（目录名 → folder_id） ----
    by_key = {_norm(fo.path): fo.folder_id for fo in ctx.folders}
    by_key.update({_norm(fo.path.rsplit("/", 1)[-1]): fo.folder_id for fo in ctx.folders if _norm(fo.path.rsplit("/", 1)[-1]) not in by_key})
    folder_ids: list[str] = []
    wanted = f.get("knowledge_folders", f.get("knowledge_folder_ids"))
    for nm in _str_list(wanted):
        fid = by_key.get(_norm(nm)) or (nm if nm in {fo.folder_id for fo in ctx.folders} else None)
        if fid is None:
            note("folder_removed", "knowledge_folder_ids", f"资料目录「{nm[:40]}」不存在于本项目，已移除")
        elif fid not in folder_ids:
            folder_ids.append(fid)

    # ---- max_steps ----
    lo, hi = c.max_steps_range
    steps_raw = f.get("max_steps")
    if isinstance(steps_raw, bool) or not isinstance(steps_raw, int) or not (lo <= steps_raw <= hi):
        if steps_raw is not None:
            note("steps_adjusted", "max_steps", f"最大步数超出 {lo}..{hi}，已调整为默认 {c.max_steps_default}")
        steps = c.max_steps_default
    else:
        steps = steps_raw

    # ---- 检索类条款 / 业务专有词 ----
    if any(tool_by_name[t].is_retrieval for t in tools):
        for clause_id, alts in c.grounding_clauses:
            if not any(a in main for a in alts):
                note("clause_missing", "main_prompt", f"检索类 agent 的主提示词缺少条款：{clause_id}")
    blob = _norm("\n".join([main, fb, label, *kws, *exs]))
    for term in c.blocked_terms:
        if _norm(term) in blob:
            note("term_blocked", "main_prompt", "文本含不允许的业务专有词")
            break

    draft = AgentDraft(
        name=name, cn_label=label, main_prompt=main, fallback_prompt=fb, keywords=tuple(kws),
        exemplars=tuple(exs), is_data_expert=bool(f.get("is_data_expert", False)),
        is_delegating=bool(f.get("is_delegating", False)), tool_names=tuple(tools), tool_params=tuple(params),
        knowledge_folder_ids=tuple(folder_ids), max_steps=steps, source=source,
    )
    return draft, tuple(notes)


def draft_to_fields(d: AgentDraft) -> dict[str, Any]:
    """草案 → 适配器输入形态（用于对用户编辑后的草案重新计算适配说明）。目录以 folder_id 给出。"""
    return {
        "name": d.name, "cn_label": d.cn_label, "main_prompt": d.main_prompt, "fallback_prompt": d.fallback_prompt,
        "keywords": list(d.keywords), "exemplars": list(d.exemplars), "is_data_expert": d.is_data_expert,
        "is_delegating": d.is_delegating, "tool_names": list(d.tool_names),
        "tool_params": [list(p) for p in d.tool_params], "knowledge_folders": list(d.knowledge_folder_ids),
        "max_steps": d.max_steps,
    }
