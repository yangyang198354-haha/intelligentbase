# MOD-R28-05 / implements IFC-R28-007 / depends MOD-R28-01, 02, 03, 04
"""联网工具 web_search / web_fetch 的声明与实现（ADR-R28-03 / 06 / 08）。

LLM 只可见 `query` / `url`；超时、条数、域名名单、上限等一律是平台限制类参数（config_parameters），
由 ib.tools 的“配置胜出”包装注入。两个工具都永不抛异常。
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from ib.core import EgressDescriptor, SearchProvider, SearchQuery, ToolResult, ToolSpec, WebGovernance, WebGovernanceStore
from ib.observability import log_event

from .fetch import SafeFetcher
from .gate import (
    WebCall,
    WebEgressGate,
    check_outbound_text,
    current_web_turn,
    fence_untrusted,
    sanitize_untrusted,
)
from .netguard import DomainRules, WebBlocked, parse_domain_list
from .policy import effective_limits
from .search import NullSearchProvider

__all__ = [
    "WEB_SEARCH_SPEC",
    "WEB_FETCH_SPEC",
    "WebRuntime",
    "NullWebRuntime",
    "web_search_tool",
    "web_fetch_tool",
    "register_web_tools",
    "PHRASE_QUERY_EMPTY",
    "PHRASE_NOT_CONFIGURED",
    "PHRASE_FETCH_DISABLED",
    "PHRASE_SEARCH_TIMEOUT",
    "PHRASE_BUDGET",
    "PHRASE_TARGET_BLOCKED",
    "PHRASE_TYPE_UNSUPPORTED",
    "PHRASE_TOO_LARGE",
    "PHRASE_SITE_REFUSED",
    "PHRASE_NO_CONTENT",
]

#: web_search 检索词长度上限（= 提供方上限）。[P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]
SEARCH_QUERY_MAX_CHARS = 128
PHRASE_QUERY_EMPTY = "检索词为空"
PHRASE_NOT_CONFIGURED = "联网服务未配置"
PHRASE_FETCH_DISABLED = "当前未开启网页抓取"
PHRASE_SEARCH_TIMEOUT = "联网检索超时"
PHRASE_BUDGET = "已达本轮联网上限"
PHRASE_TARGET_BLOCKED = "目标地址不被允许"
PHRASE_TYPE_UNSUPPORTED = "内容类型不支持"
PHRASE_TOO_LARGE = "内容超限"
PHRASE_SITE_REFUSED = "目标网站拒绝了访问"
PHRASE_NO_CONTENT = "该网页无可用内容"
_PHRASE_NO_TURN = "联网不可用：缺少回合上下文"
_PHRASE_FETCH_TIMEOUT = "网页抓取超时"
_PHRASE_SEARCH_FAILED = "联网检索失败"
_PHRASE_FETCH_FAILED = "网页抓取失败"
_PHRASE_REJECTED = "请求内容不被允许"
_PHRASE_BUSY = "联网服务繁忙，请稍后再试"
_PHRASE_UNAVAILABLE = "联网服务暂不可用"
_PHRASE_NO_RESULT = "联网检索未找到相关结果"

WEB_SEARCH_SPEC = ToolSpec(
    name="web_search",
    description="在互联网检索公开信息，返回若干条（标题、摘要、网址）。检索词须由用户问题概括而来，不得包含知识库原文。",
    needs_scope=False,
    parameters={
        "type": "object",
        # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求] query 1–128 字符（2.1.0：原 200）
        "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 128}},
        "required": ["query"],
    },
    config_parameters={
        # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求] count 1–50（2.1.0：原 1..10）
        "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
        "timeout_s": {"type": "integer", "default": 10, "minimum": 1, "maximum": 30},
        "lang": {"type": "string", "default": ""},
        # AQ6=A：保留字段以兼容已保存配置；DeepSeek 适配器忽略、不发送本地化信息
        "region": {"type": "string", "default": ""},
        "max_calls_per_turn": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
    },
    timeout_param="timeout_s",
    route_visible=False,
    external=True,
)

WEB_FETCH_SPEC = ToolSpec(
    name="web_fetch",
    description="读取一个公开网页的正文文本。网址须来自用户提供或检索结果。",
    needs_scope=False,
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string", "minLength": 1, "maxLength": 2048}},
        "required": ["url"],
    },
    config_parameters={
        "timeout_s": {"type": "integer", "default": 15, "minimum": 1, "maximum": 60},
        "max_chars": {"type": "integer", "default": 8000, "minimum": 500, "maximum": 20000},
        "allow_domains": {"type": "string", "default": ""},
        "deny_domains": {"type": "string", "default": ""},
        "allowed_types": {"type": "string", "default": "text/html,text/plain"},
        "max_calls_per_turn": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        "max_bytes_per_turn": {"type": "integer", "default": 1048576, "minimum": 10000, "maximum": 5242880},
    },
    timeout_param="timeout_s",
    route_visible=False,
    external=True,
)


@dataclass(frozen=True, slots=True)
class WebRuntime:
    provider: SearchProvider
    fetcher: SafeFetcher | None  # None ⇒ 抓取总开关关闭（IB_WEB_FETCH_ENABLED=0，缺省）
    gate: WebEgressGate | None
    governance: WebGovernanceStore | None

    def egress_descriptors(self) -> tuple[EgressDescriptor, ...]:
        out: list[EgressDescriptor] = []
        try:
            d = self.provider.describe_egress()
            if d.remote:
                out.append(d)
        except Exception:  # noqa: BLE001
            pass
        if self.fetcher is not None:
            out.append(EgressDescriptor(remote=True, endpoint_host="*", data_categories=["web_fetch_url"]))
        return tuple(out)


#: 未装配联网时的等价运行时：搜索未配置、抓取关闭。
NullWebRuntime = WebRuntime(provider=NullSearchProvider(), fetcher=None, gate=None, governance=None)


def _blocked_text(kind: str) -> str:
    return {
        "budget_exceeded": PHRASE_BUDGET,
        "busy": _PHRASE_BUSY,
        "outbound_rejected": _PHRASE_REJECTED,
        "not_configured": PHRASE_NOT_CONFIGURED,
        "audit_failed": _PHRASE_UNAVAILABLE,
    }.get(kind, PHRASE_TARGET_BLOCKED)


def _fail(content: str) -> ToolResult:
    return ToolResult(ok=False, content=content)


def _host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "")[:253]
    except ValueError:
        return ""


def web_search_tool(
    query: str,
    *,
    runtime: WebRuntime,
    max_results: int = 5,
    timeout_s: int = 10,
    lang: str = "",
    region: str = "",
    max_calls_per_turn: int = 5,
) -> ToolResult:
    try:
        return _web_search(query, runtime, max_results, timeout_s, lang, region, max_calls_per_turn)
    except Exception:  # noqa: BLE001 - 契约：永不抛
        return _fail(_PHRASE_SEARCH_FAILED)


def _web_search(query, runtime, max_results, timeout_s, lang, region, max_calls) -> ToolResult:
    turn_pair = current_web_turn()
    if turn_pair is None:
        return _fail(_PHRASE_NO_TURN)
    turn, budget = turn_pair
    q = (query or "").strip() if isinstance(query, str) else ""
    if not q:
        # AC-014-09：空 / 全空白 ⇒ 不出站、不占预算、不写审计
        return _fail(PHRASE_QUERY_EMPTY)
    # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求] 超过 128 字符 ⇒ 截断（不拒绝），再过出站文本闸
    q = q[:SEARCH_QUERY_MAX_CHARS].rstrip()
    provider = runtime.provider
    if isinstance(provider, NullSearchProvider) or runtime.gate is None:
        return _fail(PHRASE_NOT_CONFIGURED)
    caps: WebGovernance = turn.caps
    limits = effective_limits({"max_calls_per_turn": str(int(max_calls))}, caps)
    try:
        budget.reserve_call(limit=limits.max_calls)
        if budget.remaining_seconds() <= 0:
            raise WebBlocked("budget_exceeded")
        check_outbound_text(q, kind="query", private_texts=turn.private_texts)
        sq = SearchQuery(
            text=q,
            max_results=max(1, min(50, int(max_results))),
            lang=(lang or None),
            region=(region or None),
            timeout_s=max(0.5, min(float(timeout_s), budget.remaining_seconds())),
        )
        host = provider.describe_egress().endpoint_host
        budget.record_host(host)
        t0 = time.monotonic()
        outcome = runtime.gate.run(
            WebCall("web_search", host, 0),
            lambda: provider.search(sq),
            project_id=turn.project_id,
            actor_id=turn.actor_id,
        )
    except WebBlocked as exc:
        budget.record_event("web_search", exc.kind, 0)
        return _fail(_blocked_text(exc.kind))
    elapsed = time.monotonic() - t0
    budget.charge_seconds(elapsed)
    ms = int(elapsed * 1000)
    if outcome.error is not None:
        budget.record_event("web_search", outcome.error, ms)
        if outcome.error == "timeout":
            return _fail(PHRASE_SEARCH_TIMEOUT)
        if outcome.error == "not_configured":
            return _fail(PHRASE_NOT_CONFIGURED)
        return _fail(_PHRASE_SEARCH_FAILED)
    budget.record_event("web_search", "ok", ms)
    if not outcome.hits:
        return ToolResult(ok=True, content=_PHRASE_NO_RESULT)
    lines: list[str] = []
    for i, h in enumerate(outcome.hits, 1):
        title = sanitize_untrusted(h.title, max_chars=200)
        snippet = sanitize_untrusted(h.snippet, max_chars=800)  # [ASSUMPTION A-13] 容纳 summary（约 600–800 字）
        url = sanitize_untrusted(h.url, max_chars=500)
        lines.append(f"{i}. {title}\n{snippet}\n{url}")
    budget.record_text("\n".join(lines))
    return ToolResult(ok=True, content=fence_untrusted("search", "\n".join(lines)))


def web_fetch_tool(
    url: str,
    *,
    runtime: WebRuntime,
    timeout_s: int = 15,
    max_chars: int = 8000,
    allow_domains: str = "",
    deny_domains: str = "",
    allowed_types: str = "text/html,text/plain",
    max_calls_per_turn: int = 5,
    max_bytes_per_turn: int = 1_048_576,
) -> ToolResult:
    try:
        return _web_fetch(
            url, runtime, timeout_s, max_chars, allow_domains, deny_domains, allowed_types,
            max_calls_per_turn, max_bytes_per_turn,
        )
    except Exception:  # noqa: BLE001 - 契约：永不抛
        return _fail(_PHRASE_FETCH_FAILED)


def _web_fetch(url, runtime, timeout_s, max_chars, allow_domains, deny_domains, allowed_types,
               max_calls, max_bytes) -> ToolResult:
    # AQ4=A：总开关关闭 ⇒ 在预算 / 出站闸 / 审计 / 并发闸之前短路（出站 0、不写审计、不占预算）
    if runtime.fetcher is None:
        log_event("web", "fetch_disabled")
        return _fail(PHRASE_FETCH_DISABLED)
    turn_pair = current_web_turn()
    if turn_pair is None:
        return _fail(_PHRASE_NO_TURN)
    turn, budget = turn_pair
    target = (url or "").strip() if isinstance(url, str) else ""
    if not target or runtime.gate is None:
        return _fail(_PHRASE_REJECTED if not target else PHRASE_NOT_CONFIGURED)
    allow, _bad_a = parse_domain_list(allow_domains)
    deny, _bad_d = parse_domain_list(deny_domains)  # 运行期非法项忽略（保存期已校验）
    rules = DomainRules(allow=allow, deny=deny)
    types = tuple(t.strip().lower() for t in (allowed_types or "").split(",") if t.strip()) or ("text/html", "text/plain")
    limits = effective_limits(
        {"max_calls_per_turn": str(int(max_calls)), "max_bytes_per_turn": str(int(max_bytes))}, turn.caps
    )
    try:
        budget.reserve_call(limit=limits.max_calls)
        remaining_bytes = limits.max_bytes - budget.bytes_used()
        if remaining_bytes <= 0 or budget.remaining_seconds() <= 0:
            raise WebBlocked("budget_exceeded")
        check_outbound_text(target, kind="url", private_texts=turn.private_texts)
        fetcher = runtime.fetcher
        budget.record_host(_host_of(target))
        t0 = time.monotonic()
        result = runtime.gate.run(
            WebCall("web_fetch", _host_of(target), remaining_bytes),
            lambda: fetcher.fetch(
                target,
                rules=rules,
                timeout_s=max(0.5, min(float(timeout_s), budget.remaining_seconds())),
                max_bytes=remaining_bytes,
                max_chars=int(max_chars),
                allowed_types=types,
            ),
            project_id=turn.project_id,
            actor_id=turn.actor_id,
        )
    except WebBlocked as exc:
        budget.record_event("web_fetch", exc.kind, 0)
        return _fail(_blocked_text(exc.kind))
    elapsed = time.monotonic() - t0
    budget.charge_seconds(elapsed)
    ms = int(elapsed * 1000)
    # DEF-001：已读取的字节无条件计入回合预算（含超限 / 失败的读取）；耗尽后下一次调用在出站前即被拒
    budget.charge_bytes(result.bytes_read)
    if not result.ok:
        budget.record_event("web_fetch", result.error or "error", ms)
        if result.error == "blocked":
            return _fail(PHRASE_TARGET_BLOCKED)
        if result.error == "timeout":
            return _fail(_PHRASE_FETCH_TIMEOUT)
        if result.error == "content_type_unsupported":
            return _fail(PHRASE_TYPE_UNSUPPORTED)
        if result.error == "content_too_large":
            return _fail(PHRASE_TOO_LARGE)
        # DEF-005/006（AC-015-07）：被站点拒绝（401/403/429）与无可用内容（其余 4xx/5xx、空正文）可区分，且不带状态码
        if result.error == "http_error" and result.status in (401, 403, 429):
            return _fail(PHRASE_SITE_REFUSED)
        if result.error in ("http_error", "empty_content"):
            return _fail(PHRASE_NO_CONTENT)
        return _fail(_PHRASE_FETCH_FAILED)
    budget.record_event("web_fetch", "ok", ms)
    title = sanitize_untrusted(result.title, max_chars=200)
    final_url = sanitize_untrusted(result.final_url, max_chars=500)
    body = sanitize_untrusted(result.text, max_chars=int(max_chars))
    budget.record_text(body)
    return ToolResult(ok=True, content=fence_untrusted("fetch", f"标题：{title}\n网址：{final_url}\n正文：\n{body}"))


def register_web_tools(registry, runtime: WebRuntime) -> None:
    """经 functools.partial 绑定 runtime；runtime 缺省等价 NullWebRuntime（调用方传入）。"""
    registry.register(WEB_SEARCH_SPEC, functools.partial(web_search_tool, runtime=runtime))
    registry.register(WEB_FETCH_SPEC, functools.partial(web_fetch_tool, runtime=runtime))
