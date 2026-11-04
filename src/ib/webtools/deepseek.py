# MOD-R28-03 / implements IFC-R28-029 / depends MOD-R28-01
"""DeepSeek 搜索适配器（stdlib urllib；ib.webtools 内搜索侧唯一的网络代码）。

出处：所有端点 / 字段 / 状态码只来自 `docs/external_api/deepseek_search_fetch.md`（画像 P11-3），
调用处以 `[P11: …§节名]` 标注；资料未写明的数值与取舍标 `[ASSUMPTION A-nn]`（architecture_design 开放问题）。

纪律：
* 请求体只含 `query` / `count` / `need_content`，绝不发送资料中的“用户原始问题”与“IP 型本地化”两个可选字段（REQ-NFUNC-005）；
* 只按 HTTP 状态码映射错误，**不读取、不记录、不回显错误体**；
* 单次尝试、不重试（A-15）；不跟随重定向（A-18），避免把 `Authorization` 头转发给第三方；
* Key 只在适配器内拼进请求头，不进日志 / 异常 / `repr` / `health()` / `describe_egress()`。
"""

from __future__ import annotations

import http.client
import json
import logging
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Final, Literal, Mapping, Protocol
from urllib.parse import urlsplit

from ib.core import DEEPSEEK_API_HOST as _CORE_DEEPSEEK_API_HOST
from ib.core import EgressDescriptor, HealthStatus, SearchErrorKind, SearchHit, SearchOutcome, SearchQuery

__all__ = [
    "DEEPSEEK_API_HOST",
    "DEEPSEEK_SEARCH_URL",
    "DEEPSEEK_QUERY_MAX_CHARS",
    "DEEPSEEK_COUNT_MAX",
    "SEARCH_REPLY_MAX_BYTES",
    "LANG_PATTERN",
    "TransportError",
    "HttpReply",
    "HttpPostTransport",
    "UrllibPostTransport",
    "encode_search_request",
    "map_search_status",
    "parse_search_results",
    "DeepSeekSearchProvider",
]

_log = logging.getLogger("intelligentbase")

# [P11: docs/external_api/deepseek_search_fetch.md:§端点与鉴权]
DEEPSEEK_API_HOST: Final[str] = _CORE_DEEPSEEK_API_HOST
DEEPSEEK_SEARCH_URL: Final[str] = "https://api.deepseek.com/v1/tools/search"
# [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]
DEEPSEEK_QUERY_MAX_CHARS: Final[int] = 128
DEEPSEEK_COUNT_MAX: Final[int] = 50
#: 响应体读取上限。[ASSUMPTION A-14] 资料无响应大小数值；count<=50 且 need_content=false 时远低于此。
SEARCH_REPLY_MAX_BYTES: Final[int] = 2 * 1024 * 1024
#: `lang` 格式。[ASSUMPTION A-16] 资料仅有 `lang:zh,en` 一个示例，严格限定以防经配置注入 site: 等其他操作符。
LANG_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z]{2,3}(,[A-Za-z]{2,3}){0,4}")
_CHUNK = 64 * 1024


class TransportError(Exception):
    """仅网络层失败（超时 / 不可达）；HTTP 状态码（含 4xx / 5xx）一律走 HttpReply，不抛。"""

    def __init__(self, kind: Literal["timeout", "unreachable"]) -> None:
        super().__init__(kind)
        self.kind: Literal["timeout", "unreachable"] = kind


@dataclass(frozen=True, slots=True)
class HttpReply:
    status: int
    body: bytes  # 至多 max_reply_bytes
    oversize: bool = False  # 响应体超过 max_reply_bytes ⇒ True（适配器映射为 bad_response）


class HttpPostTransport(Protocol):
    """唯一网络缝：生产 = UrllibPostTransport，测试 = FakeDeepSeekTransport。"""

    def post_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes,
        timeout_s: float,
        max_reply_bytes: int,
    ) -> HttpReply: ...


class UrllibPostTransport:
    """生产传输：stdlib urllib.request（风格同 ib/embedding LocalHttpEmbedder）。

    * opener 不含 HTTPRedirectHandler：3xx 由 HTTPDefaultErrorHandler 抛 HTTPError，原样作为状态码返回（A-18）；
    * 证书校验用 ssl 默认上下文；代理环境变量行为同 urllib 默认（ProxyHandler()，A-19）；
    * 总期限 = 调用时刻 + timeout_s：连接 / 读取的套接字超时取 timeout_s，分块读取时检查总期限。
    """

    def __init__(self) -> None:
        self._opener = urllib.request.OpenerDirector()
        for handler in (
            urllib.request.ProxyHandler(),
            urllib.request.HTTPHandler(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            urllib.request.HTTPDefaultErrorHandler(),
            urllib.request.HTTPErrorProcessor(),
        ):
            self._opener.add_handler(handler)

    def post_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes,
        timeout_s: float,
        max_reply_bytes: int,
    ) -> HttpReply:
        if not url.lower().startswith("https://"):
            raise TransportError("unreachable")
        deadline = time.monotonic() + max(0.1, float(timeout_s))
        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with self._opener.open(request, timeout=max(0.1, float(timeout_s))) as resp:  # noqa: S310 - https 固定端点
                return self._read(resp, int(resp.status), deadline, max_reply_bytes)
        except urllib.error.HTTPError as exc:
            # 任何非 2xx 状态：只取状态码，不读取错误体（不记录、不回显）。
            code = int(exc.code)
            exc.close()
            return HttpReply(status=code, body=b"")
        except TransportError:
            raise
        except TimeoutError as exc:
            raise TransportError("timeout") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise TransportError("timeout") from exc
            raise TransportError("unreachable") from exc
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            raise TransportError("unreachable") from exc

    @staticmethod
    def _read(resp, status: int, deadline: float, max_reply_bytes: int) -> HttpReply:
        chunks: list[bytes] = []
        total = 0
        while True:
            if time.monotonic() > deadline:
                raise TransportError("timeout")
            chunk = resp.read(_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > max_reply_bytes:
                return HttpReply(status=status, body=b"", oversize=True)
            chunks.append(chunk)
        return HttpReply(status=status, body=b"".join(chunks))


def encode_search_request(query: SearchQuery) -> bytes:
    """UTF-8 JSON；键集合恰为 {query, count, need_content}。

    * query = SearchQuery.text；`lang` 合法（A-16）⇒ 末尾追加 ` lang:<lang>`（资料所载操作符），先截基础文本使总长 ≤128；
    * count = SearchQuery.max_results（1..50）；need_content 显式写 false，不依赖缺省；
    * region 被忽略（AQ6）；不含资料中其余两个可选字段（原始问题、IP 型本地化），见模块文档串。
    """
    text = query.text
    lang = (query.lang or "").strip()
    q = text[:DEEPSEEK_QUERY_MAX_CHARS]
    if lang:
        if LANG_PATTERN.fullmatch(lang):
            suffix = f" lang:{lang}"
            base = text[: DEEPSEEK_QUERY_MAX_CHARS - len(suffix)].rstrip()
            if base:
                q = base + suffix
        else:
            _log.warning("deepseek search: lang ignored (invalid format)")
    payload = {
        "query": q,  # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]
        "count": int(query.max_results),  # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]
        "need_content": False,  # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求]
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def map_search_status(status: int) -> SearchErrorKind | None:
    """只依据状态码映射；200 ⇒ None。[P11: docs/external_api/deepseek_search_fetch.md:§错误]"""
    s = int(status)
    if s == 200:
        return None
    if s in (400, 413):
        return "rejected"  # 请求非法 / 请求体过大，需修改请求，不重试
    if s == 401:
        return "auth_failed"  # Key 缺失或无效
    if s == 402:
        return "quota_exceeded"  # 余额不足（本轮不重试）
    if s in (408, 504):
        return "timeout"
    if s == 429:
        return "rate_limited"  # 账户级 QPS
    if s >= 500:
        return "unreachable"  # 500 及其他 5xx：SearchErrorKind 无 server_error，沿用“提供方不可用”类
    if 400 <= s < 500:
        return "rejected"  # [ASSUMPTION] 资料只在 Fetch 下列出 403 / 404；Search 未列的 4xx 一律 rejected
    return "bad_response"  # 3xx（A-18，不跟随重定向）与其他非常规状态


def parse_search_results(
    body: bytes, *, limit: int
) -> tuple[tuple[SearchHit, ...], SearchErrorKind | None]:
    """解析 200 响应。[P11: docs/external_api/deepseek_search_fetch.md:§Search 响应]

    JSON 非法 / 顶层非对象 / 无 results 数组 ⇒ ((), bad_response)；results == [] ⇒ ((), None)（空结果不是故障）；
    映射 title、url、summary（空则 snippet；[ASSUMPTION A-13]）；url 缺失或非 http(s) 的条目丢弃；
    原数组非空而全部被丢弃 ⇒ bad_response；保持返回顺序（A-20），截取前 limit 条；未知字段忽略。
    """
    try:
        data = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return (), "bad_response"
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return (), "bad_response"
    raw = data["results"]
    if not raw:
        return (), None
    cap = max(1, int(limit))
    hits: list[SearchHit] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            continue
        url = url.strip()
        try:
            parts = urlsplit(url)
        except ValueError:
            continue
        if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
            continue
        title = item.get("title")
        summary = item.get("summary")
        snippet = item.get("snippet")
        text = summary if isinstance(summary, str) and summary.strip() else (snippet if isinstance(snippet, str) else "")
        hits.append(SearchHit(title=title.strip() if isinstance(title, str) else "", snippet=text.strip(), url=url))
        if len(hits) >= cap:
            break
    if not hits:
        return (), "bad_response"
    return tuple(hits), None


class DeepSeekSearchProvider:
    """实现 SearchProvider 端口；search 永不抛；单次尝试、不重试（A-15）。"""

    provider_id = "deepseek"

    def __init__(self, api_key: str, *, transport: HttpPostTransport) -> None:
        key = (api_key or "").strip() if isinstance(api_key, str) else ""
        if not key:
            raise ValueError("api_key 不得为空")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in key):
            raise ValueError("api_key 含非法字符")  # 防请求头注入；消息不含 Key
        if transport is None:
            raise ValueError("transport 必须显式传入（无默认真实传输）")
        self._api_key = key
        self._transport = transport

    def __repr__(self) -> str:
        return "DeepSeekSearchProvider(provider_id='deepseek')"

    def search(self, query: SearchQuery) -> SearchOutcome:
        t0 = time.monotonic()

        def _ms() -> int:
            return int((time.monotonic() - t0) * 1000)

        try:
            if not query.text.strip():
                return SearchOutcome((), "rejected", 0)  # 全空白检索词不出站
            body = encode_search_request(query)
            headers = {
                "Authorization": f"Bearer {self._api_key}",  # [P11: docs/external_api/deepseek_search_fetch.md:§端点与鉴权]
                "Content-Type": "application/json",  # [P11: docs/external_api/deepseek_search_fetch.md:§端点与鉴权]
            }
            reply = self._transport.post_json(
                DEEPSEEK_SEARCH_URL,
                headers=headers,
                body=body,
                timeout_s=float(query.timeout_s),
                max_reply_bytes=SEARCH_REPLY_MAX_BYTES,
            )
            if reply.oversize:
                return SearchOutcome((), "bad_response", _ms())
            kind = map_search_status(reply.status)
            if kind is not None:
                return SearchOutcome((), kind, _ms())
            hits, parse_err = parse_search_results(reply.body, limit=int(query.max_results))
            if parse_err is not None:
                return SearchOutcome((), parse_err, _ms())
            return SearchOutcome(hits, None, _ms())
        except TransportError as exc:
            return SearchOutcome((), exc.kind, _ms())
        except Exception:  # noqa: BLE001 - 端口契约：永不抛；不记录异常细节（可能含请求上下文）
            return SearchOutcome((), "bad_response", _ms())

    def health(self) -> HealthStatus:
        # 不外呼：资料无免费探测接口，且成功调用计费。[P11: docs/external_api/deepseek_search_fetch.md:§限流与计费]
        return HealthStatus(ok=True, detail="configured")

    def describe_egress(self) -> EgressDescriptor:
        return EgressDescriptor(remote=True, endpoint_host=DEEPSEEK_API_HOST, data_categories=["web_search_query"])
