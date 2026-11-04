# MOD-R28-10 顾问核心库（ib.advisor）：回合理解、输入块渲染、事实保真守卫、评测指标。不 import ib.webtools / ib_embed。
"""顾问核心库（纯函数 + 注入式 LLM）；本包不依赖任何业务层或联网实现（ADR-R28-01 / 02 / 09）。"""

from __future__ import annotations

from .compose import (
    ADVISOR_APOLOGY_TEXT,
    AdvisorTurn,
    advisor_apology_text,
    render_advisor_input,
)
from .fidelity import (
    ApologyReason,
    check_fidelity,
    exceeds_quote_limit,
    protected_spans,
    retry_instruction,
)
from .understand import (
    ADVISOR_HISTORY_MAX_CHARS,
    ADVISOR_HISTORY_MAX_MESSAGES,
    HistoryDigest,
    Intent,
    Topic,
    TurnUnderstander,
    TurnUnderstanding,
    build_history_digest,
    passthrough,
    private_texts_of_history,
)

__all__ = [
    "ADVISOR_APOLOGY_TEXT",
    "AdvisorTurn",
    "advisor_apology_text",
    "render_advisor_input",
    "ApologyReason",
    "check_fidelity",
    "exceeds_quote_limit",
    "protected_spans",
    "retry_instruction",
    "ADVISOR_HISTORY_MAX_CHARS",
    "ADVISOR_HISTORY_MAX_MESSAGES",
    "HistoryDigest",
    "Intent",
    "Topic",
    "TurnUnderstander",
    "TurnUnderstanding",
    "build_history_digest",
    "passthrough",
    "private_texts_of_history",
]
