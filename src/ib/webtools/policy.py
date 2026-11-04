# MOD-R28-02 / implements IFC-R28-003（策略部分） / depends MOD-R28-01, netguard
"""联网策略：有效上限与保存期校验（纯函数）。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from ib.core import (
    WEB_BYTES_HARD_MAX,
    WEB_CALLS_HARD_MAX,
    WEB_SECONDS_HARD_MAX,
    ToolGrantSpec,
    ValidationErrorItem,
    WebGovernance,
)

from .netguard import parse_domain_list

__all__ = ["EffectiveLimits", "effective_limits", "validate_web_grants", "WEB_TOOL_NAMES"]

WEB_TOOL_NAMES = ("web_search", "web_fetch")

#: [ASSUMPTION A-16] 与 deepseek.LANG_PATTERN 同一正则（此处不 import deepseek，避免 policy 依赖网络模块）。
_LANG_RE = re.compile(r"[A-Za-z]{2,3}(,[A-Za-z]{2,3}){0,4}")


@dataclass(frozen=True, slots=True)
class EffectiveLimits:
    max_calls: int  # min(工具参数, 全局, 硬上限)
    max_bytes: int
    max_seconds: int


def _as_int(raw: object) -> int | None:
    try:
        v = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if v != int(v):
        return None
    return int(v)


def effective_limits(param_values: Mapping[str, str], caps: WebGovernance) -> EffectiveLimits:
    """工具参数（裸名 `max_calls_per_turn` / `max_bytes_per_turn`，缺省视为不限）与全局、硬上限取小。"""
    calls = [caps.max_calls_per_turn, WEB_CALLS_HARD_MAX]
    nbytes = [caps.max_fetch_bytes_per_turn, WEB_BYTES_HARD_MAX]
    secs = [caps.max_seconds_per_turn, WEB_SECONDS_HARD_MAX]
    c = _as_int(param_values.get("max_calls_per_turn", ""))
    if c is not None and c > 0:
        calls.append(c)
    b = _as_int(param_values.get("max_bytes_per_turn", ""))
    if b is not None and b > 0:
        nbytes.append(b)
    return EffectiveLimits(max_calls=min(calls), max_bytes=min(nbytes), max_seconds=min(secs))


def validate_web_grants(
    grants: tuple[ToolGrantSpec, ...], caps: WebGovernance
) -> tuple[ValidationErrorItem, ...]:
    """保存期校验（纯函数）：域名清单格式、次数 / 字节超出全局上限。

    未授权联网工具却带其参数 ⇒ 沿用既有 `tool_param_unauthorized_tool`（不在此重复）。
    """
    errors: list[ValidationErrorItem] = []
    for grant in grants:
        for pv in grant.param_values:
            path = f"tool_grants[{grant.expert_name}].param_values[{pv.name}]"
            if pv.name in ("web_fetch.allow_domains", "web_fetch.deny_domains"):
                _valid, bad = parse_domain_list(pv.value)
                for n in bad:
                    errors.append(
                        ValidationErrorItem(
                            path=path,
                            code="web_domain_invalid",
                            message=f"域名清单第 {n} 项格式非法（须为不含协议头 / 路径 / 端口 / 空格的域名）",
                        )
                    )
            elif pv.name == "web_search.lang":
                # [ASSUMPTION A-16] 严格格式，防经 lang 注入 site: 等其他查询操作符
                if (pv.value or "").strip() and not _LANG_RE.fullmatch(pv.value.strip()):
                    errors.append(
                        ValidationErrorItem(
                            path=path,
                            code="web_lang_invalid",
                            message="语言代码格式非法（示例：zh 或 zh,en）",
                        )
                    )
            elif pv.name in ("web_search.max_calls_per_turn", "web_fetch.max_calls_per_turn"):
                v = _as_int(pv.value)
                if v is not None and v > caps.max_calls_per_turn:
                    errors.append(
                        ValidationErrorItem(
                            path=path,
                            code="web_limit_exceeds_global",
                            message=f"超出全局上限（{caps.max_calls_per_turn} 次）",
                        )
                    )
            elif pv.name == "web_fetch.max_bytes_per_turn":
                v = _as_int(pv.value)
                if v is not None and v > caps.max_fetch_bytes_per_turn:
                    errors.append(
                        ValidationErrorItem(
                            path=path,
                            code="web_limit_exceeds_global",
                            message=f"超出全局上限（{caps.max_fetch_bytes_per_turn} 字节）",
                        )
                    )
    return tuple(errors)
