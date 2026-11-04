# MOD-R28-03 / implements IFC-R28-030 / depends deepseek.py（同模块族）
"""DeepSeek 搜索的离线替身（无任何网络导入）。

资料“测试替身”节：无官方沙箱，测试只能用项目自有替身，按资料的字段与错误码构造响应；自动化测试禁止调用真实端点。
[P11: docs/external_api/deepseek_search_fetch.md:§测试替身]

错误体的 message / type / code 取值是测试占位，**不代表 DeepSeek 真实值**——适配器不依赖它们（只看状态码）。
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping, Sequence

from .deepseek import (
    DEEPSEEK_COUNT_MAX,
    DEEPSEEK_QUERY_MAX_CHARS,
    DEEPSEEK_SEARCH_URL,
    HttpReply,
    TransportError,
)

__all__ = [
    "DoubleRequest",
    "DoubleReply",
    "search_item",
    "ok_results",
    "empty_results",
    "error_reply",
    "FakeDeepSeekTransport",
    "DOUBLE_ERROR_STATUSES",
]

#: 资料列出的错误码。[P11: docs/external_api/deepseek_search_fetch.md:§错误]
DOUBLE_ERROR_STATUSES: tuple[int, ...] = (400, 401, 402, 403, 404, 408, 413, 429, 500, 504)


@dataclass(frozen=True, slots=True)
class DoubleRequest:
    """替身记录的“出站请求”（供 canary / 载荷断言）。Key 值本身不记录。"""

    url: str
    method: str  # 恒 "POST"
    header_names: tuple[str, ...]
    authorization_ok: bool  # 是否为 "Bearer <expected_key>"
    body: dict[str, Any]  # 解析后的 JSON 请求体（非法 JSON ⇒ {}）
    timeout_s: float


@dataclass(frozen=True, slots=True)
class DoubleReply:
    status: int
    body: bytes
    delay_s: float = 0.0  # > timeout_s 时替身抛 TransportError("timeout")（不真实睡眠）
    network_error: Literal["timeout", "unreachable"] | None = None


def search_item(*, title: str, url: str, snippet: str, summary: str, **extra: Any) -> dict[str, Any]:
    """按资料补全其余字段。[P11: docs/external_api/deepseek_search_fetch.md:§Search 响应]"""
    item: dict[str, Any] = {
        "rerank_score": 2.0,  # 0–3
        "title": title,
        "url": url,
        "snippet": snippet,
        "summary": summary,
        "content": "",  # need_content=false 时恒为空串
        "site_name": "example.test",
        "site_icon": None,
        "date": "2026-11-01T00:00:00Z",  # UTC，RFC 3339
        "authority": 3,  # 0–4，-1 未知
    }
    item.update(extra)
    return item


def _json_body(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def ok_results(items: Sequence[Mapping[str, Any]]) -> DoubleReply:
    """200 + {"results":[…]}。"""
    return DoubleReply(200, _json_body({"results": [dict(i) for i in items]}))


def empty_results() -> DoubleReply:
    """200 + {"results": []}（没有匹配时返回空数组）。"""
    return DoubleReply(200, _json_body({"results": []}))


def error_reply(status: int) -> DoubleReply:
    """OpenAI 兼容错误格式。[P11: docs/external_api/deepseek_search_fetch.md:§错误]"""
    if status not in DOUBLE_ERROR_STATUSES:
        raise ValueError(f"替身只构造资料列出的错误码：{DOUBLE_ERROR_STATUSES}")
    body = {"error": {"message": f"double-placeholder-{status}", "type": "double_placeholder", "param": None, "code": f"double_{status}"}}
    return DoubleReply(status, _json_body(body))


class FakeDeepSeekTransport:
    """实现 HttpPostTransport；按资料校验请求，通过后依序取脚本项（脚本耗尽 ⇒ 200 空结果）。"""

    def __init__(
        self,
        script: Sequence["DoubleReply | Callable[[DoubleRequest], DoubleReply]"] = (),
        *,
        expected_key: str = "TEST-KEY-NOT-REAL",
        strict: bool = True,
    ) -> None:
        self._script = list(script)
        self._expected_key = expected_key
        self._strict = bool(strict)
        self._lock = threading.Lock()
        self._i = 0
        self.requests: list[DoubleRequest] = []
        self.billable_calls = 0  # 仅“200 且 results 非空”时 +1（资料计费口径）

    @staticmethod
    def _header(headers: Mapping[str, str], name: str) -> str | None:
        for k, v in headers.items():
            if k.lower() == name.lower():
                return v
        return None

    def _validate(self, headers: Mapping[str, str], authorization_ok: bool, body: dict[str, Any], body_ok: bool) -> int | None:
        # [P11: docs/external_api/deepseek_search_fetch.md:§Search 请求、§错误]
        if not authorization_ok:
            return 401
        ctype = (self._header(headers, "Content-Type") or "").lower()
        if not ctype.startswith("application/json") or not body_ok:
            return 400
        q = body.get("query")
        if not isinstance(q, str) or not q.strip() or len(q) > DEEPSEEK_QUERY_MAX_CHARS:
            return 400
        if "count" in body:
            c = body["count"]
            if not isinstance(c, int) or isinstance(c, bool) or not (1 <= c <= DEEPSEEK_COUNT_MAX):
                return 400
        if "need_content" in body and not isinstance(body["need_content"], bool):
            return 400
        return None

    def post_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes,
        timeout_s: float,
        max_reply_bytes: int,
    ) -> HttpReply:
        if self._strict and url != DEEPSEEK_SEARCH_URL:
            raise AssertionError("FakeDeepSeekTransport: URL 不等于资料所载 Search 端点（测试编写错误）")
        parsed: dict[str, Any] = {}
        body_ok = False
        try:
            obj = json.loads(body.decode("utf-8"))
            if isinstance(obj, dict):
                parsed, body_ok = obj, True
        except (ValueError, UnicodeDecodeError):
            pass
        auth = self._header(headers, "Authorization")
        authorization_ok = auth == f"Bearer {self._expected_key}"
        req = DoubleRequest(
            url=url,
            method="POST",
            header_names=tuple(headers.keys()),
            authorization_ok=authorization_ok,
            body=parsed,
            timeout_s=float(timeout_s),
        )
        with self._lock:
            self.requests.append(req)
            invalid = self._validate(headers, authorization_ok, parsed, body_ok) if self._strict else None
            if invalid is not None:
                reply = error_reply(invalid)
            else:
                step = self._script[self._i] if self._i < len(self._script) else None
                self._i += 1
                reply = None
        if reply is None:
            reply = empty_results() if step is None else (step(req) if callable(step) else step)
        if reply.network_error is not None:
            raise TransportError(reply.network_error)
        if reply.delay_s > float(timeout_s):
            raise TransportError("timeout")
        if reply.status == 200 and self._is_nonempty_results(reply.body):
            with self._lock:
                self.billable_calls += 1
        if len(reply.body) > int(max_reply_bytes):
            return HttpReply(status=reply.status, body=b"", oversize=True)
        return HttpReply(status=reply.status, body=reply.body)

    @staticmethod
    def _is_nonempty_results(body: bytes) -> bool:
        try:
            obj = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return False
        return isinstance(obj, dict) and isinstance(obj.get("results"), list) and len(obj["results"]) > 0
