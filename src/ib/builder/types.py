# MOD-R26-11 / implements IFC-R26-100：Builder 值对象与异常（零 I/O）
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

__all__ = [
    "AgentDraft",
    "AdaptationNote",
    "Deduction",
    "RubricResult",
    "FieldChange",
    "AgentDigest",
    "ParamDigest",
    "ToolDigest",
    "FolderDigest",
    "ProjectConstraints",
    "ProjectContext",
    "BuilderUnavailable",
    "BuilderBusy",
    "EgressRejected",
    "ExpertNotFound",
]


@dataclass(frozen=True, slots=True)
class AgentDraft:
    name: str  # 同专家命名规则；1..48
    cn_label: str  # 1..32
    main_prompt: str  # 1..20000
    fallback_prompt: str  # 1..20000
    keywords: tuple[str, ...]  # <=20
    exemplars: tuple[str, ...]  # <=10
    is_data_expert: bool
    is_delegating: bool
    tool_names: tuple[str, ...]
    tool_params: tuple[tuple[str, str | int | float | bool], ...]
    knowledge_folder_ids: tuple[str, ...]
    max_steps: int
    source: Literal["generated", "optimized", "cloned", "blank"]


@dataclass(frozen=True, slots=True)
class AdaptationNote:
    code: Literal[
        "tool_removed", "folder_removed", "param_adjusted", "steps_adjusted", "name_conflict",
        "label_conflict", "clause_missing", "term_blocked", "requirement_not_adopted", "truncated",
    ]
    field: str
    message: str  # 可读；不含凭据 / 提示词全文


@dataclass(frozen=True, slots=True)
class Deduction:
    dimension: Literal["completeness", "adaptation", "routing", "prompt", "safety"]
    check_id: str
    field: str
    points: int
    evidence: str  # <=200 字符；无 evidence 不产生扣分


@dataclass(frozen=True, slots=True)
class RubricResult:
    rubric_version: str
    total: int  # 0..100
    grade: Literal["fail", "pass", "excellent"]
    dimension_scores: Mapping[str, int]
    deductions: tuple[Deduction, ...]
    coverage: Literal["full", "rules_only"]
    cache_hit: bool = False


@dataclass(frozen=True, slots=True)
class FieldChange:
    field: str
    before: str | None
    after: str | None
    note: str


@dataclass(frozen=True, slots=True)
class AgentDigest:
    name: str
    cn_label: str
    keywords: tuple[str, ...] = ()
    exemplars: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParamDigest:
    name: str  # 限定名 `<tool>.<param>` 或裸名，与 ToolParamSpec.name 一致
    type: Literal["int", "float", "bool", "str"]
    minimum: float | None = None
    maximum: float | None = None
    default: str | int | float | bool | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolDigest:
    name: str
    description: str = ""
    params: tuple[ParamDigest, ...] = ()
    is_retrieval: bool = False  # 检索类（受 REQ-FUNC-IB-56 三项条款约束）


@dataclass(frozen=True, slots=True)
class FolderDigest:
    folder_id: str
    path: str  # 目录路径名（展示用）


#: REQ-FUNC-IB-56 的三项内容要求（引用来源 / 无命中如实告知 / 工具使用契约）：条款 id → 任一命中即满足的关键词。
GROUNDING_CLAUSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("citation", ("引用", "来源", "出处")),
    ("honest_no_hit", ("没有找到", "未找到", "无命中", "如实", "不得编造", "不要编造", "不编造", "无法确认")),
    ("tool_contract", ("工具", "检索", "search_knowledge", "调用")),
)
#: 项目内禁止出现的业务专有词（REQ-FUNC-IB-58）。
BLOCKED_TERMS: tuple[str, ...] = ("freeark", "自由方舟", "三恒")


@dataclass(frozen=True, slots=True)
class ProjectConstraints:
    max_steps_range: tuple[int, int] = (1, 8)
    max_steps_default: int = 4
    reserved_names: tuple[str, ...] = ("general", "start", "end")
    prompt_max_chars: int = 20000
    grounding_clauses: tuple[tuple[str, tuple[str, ...]], ...] = GROUNDING_CLAUSES
    blocked_terms: tuple[str, ...] = BLOCKED_TERMS


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """由组合根构造（只含白名单类别：既有 agent 摘要 / 工具声明 / 目录名 / 约束）。"""

    project_id: str
    agents: tuple[AgentDigest, ...] = ()
    tools: tuple[ToolDigest, ...] = ()
    folders: tuple[FolderDigest, ...] = ()
    constraints: ProjectConstraints = field(default_factory=ProjectConstraints)


class BuilderUnavailable(Exception):
    def __init__(
        self,
        reason: Literal["llm_unconfigured", "network", "timeout", "rejected", "parse_failed", "audit_failed"],
        message: str = "",
    ) -> None:
        super().__init__(message or reason)
        self.reason = reason


class BuilderBusy(Exception):
    pass


class EgressRejected(Exception):
    def __init__(
        self,
        code: Literal["egress_secret_detected", "egress_payload_too_large", "requirement_empty", "requirement_too_long"],
    ) -> None:
        super().__init__(code)
        self.code = code


class ExpertNotFound(Exception):
    """review_existing 指向的专家不存在或已停用（→ 404）。"""
