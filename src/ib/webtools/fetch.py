# MOD-R28-02 / implements IFC-R28-004（安全抓取） / depends MOD-R28-01, netguard
"""安全抓取：逐跳重校验、钉住已校验 IP、限时限量、lxml 正文抽取（ADR-R28-03 / 04）。

本文件与 `search.py` 是 `ib.webtools` 内仅有的允许持有 http.client / ssl / socket 导入的位置
（selfcheck `web_egress_single_exit`）。
"""

from __future__ import annotations

import http.client
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Iterator, Literal, Mapping, Protocol
from urllib.parse import urljoin

from .netguard import DomainRules, GuardedTarget, Resolver, UrlGuard, WebBlocked, WebBlockKind

__all__ = [
    "FetchErrorKind",
    "FetchResult",
    "RawResponse",
    "FetchTransport",
    "SafeFetcher",
    "extract_text",
    "PinnedTransport",
    "default_resolver",
]

FetchErrorKind = Literal[
    "blocked",
    "timeout",
    "unreachable",
    "http_error",
    "content_type_unsupported",
    "content_too_large",
    "decode_failed",
    "extract_unavailable",
    "empty_content",
    "not_configured",
]


@dataclass(frozen=True, slots=True)
class FetchResult:
    ok: bool
    final_url: str
    title: str
    text: str  # ≤ max_chars；净化前的原始抽取文本
    error: FetchErrorKind | None
    blocked: WebBlockKind | None
    status: int | None
    bytes_read: int
    truncated: bool


class RawResponse:
    """传输层返回的原始响应：状态码、小写键头、正文分块迭代器。"""

    def __init__(self, status: int, headers: Mapping[str, str], chunks: Iterator[bytes], closer=None) -> None:
        self.status = status
        self.headers = {str(k).lower(): str(v) for k, v in headers.items()}
        self.chunks = chunks
        self._closer = closer

    def close(self) -> None:
        if self._closer is not None:
            try:
                self._closer()
            except Exception:  # noqa: BLE001
                pass


class FetchTransport(Protocol):
    def request(self, target: GuardedTarget, *, headers: Mapping[str, str], timeout_s: float) -> RawResponse: ...


# --------------------------------------------------------------------------- #
# 默认解析器（getaddrinfo + 隔离小线程池）
# --------------------------------------------------------------------------- #

_DNS_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ib-dns")
_DNS_INFLIGHT = threading.BoundedSemaphore(4)


def default_resolver(host: str, port: int, timeout_s: float) -> tuple[str, ...]:
    """getaddrinfo + 隔离小线程池（≤4）；池满 / 超时 / 失败 ⇒ WebBlocked('resolve_failed')。"""
    if timeout_s <= 0:
        raise WebBlocked("resolve_failed")
    if not _DNS_INFLIGHT.acquire(blocking=False):
        raise WebBlocked("resolve_failed")

    def _work() -> tuple[str, ...]:
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        finally:
            _DNS_INFLIGHT.release()
        out: list[str] = []
        for info in infos:
            a = str(info[4][0])
            if a not in out:
                out.append(a)
        return tuple(out)

    try:
        future = _DNS_POOL.submit(_work)
    except Exception:  # noqa: BLE001
        _DNS_INFLIGHT.release()
        raise WebBlocked("resolve_failed") from None
    try:
        return future.result(timeout=timeout_s)
    except FutureTimeout:
        raise WebBlocked("resolve_failed") from None
    except Exception:  # noqa: BLE001
        raise WebBlocked("resolve_failed") from None


# --------------------------------------------------------------------------- #
# 生产传输：钉 IP 的 http.client 连接
# --------------------------------------------------------------------------- #


class _PinnedHTTP(http.client.HTTPConnection):
    def __init__(self, ip: str, port: int, timeout: float) -> None:
        super().__init__(ip, port, timeout=timeout)


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, ip: str, port: int, sni_host: str, timeout: float) -> None:
        self._sni_host = sni_host
        self._pin_ctx = ssl.create_default_context()
        super().__init__(ip, port, timeout=timeout, context=self._pin_ctx)

    def connect(self) -> None:  # 连接已校验的字面 IP，证书与 SNI 校验用原主机名
        sock = socket.create_connection((self.host, self.port), self.timeout)
        try:
            self.sock = self._pin_ctx.wrap_socket(sock, server_hostname=self._sni_host)
        except Exception:
            sock.close()
            raise


# IFC-R29-031：公开别名（供 ib.mcp.transport 复用钉 IP 连接；不改行为）
PinnedHTTPConnection = _PinnedHTTP
PinnedHTTPSConnection = _PinnedHTTPS


class PinnedTransport:
    """仅 GET；固定头；不带 Cookie / Authorization / Referer；不读环境代理（直连钉定 IP）。"""

    def request(self, target: GuardedTarget, *, headers: Mapping[str, str], timeout_s: float) -> RawResponse:
        timeout = max(0.1, float(timeout_s))
        if target.scheme == "https":
            conn: http.client.HTTPConnection = _PinnedHTTPS(target.pinned_ip, target.port, target.host, timeout)
        else:
            conn = _PinnedHTTP(target.pinned_ip, target.port, timeout)
        default_port = 443 if target.scheme == "https" else 80
        host_header = target.host if target.port == default_port else f"{target.host}:{target.port}"
        try:
            conn.putrequest("GET", target.path_query, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", host_header)
            for k, v in headers.items():
                conn.putheader(k, v)
            conn.endheaders()
            resp = conn.getresponse()
        except Exception:
            conn.close()
            raise

        def _chunks() -> Iterator[bytes]:
            while True:
                block = resp.read(8192)
                if not block:
                    return
                yield block

        return RawResponse(resp.status, dict((k.lower(), v) for k, v in resp.getheaders()), _chunks(), conn.close)


# --------------------------------------------------------------------------- #
# 正文抽取
# --------------------------------------------------------------------------- #

_DROP_TAGS = ("script", "style", "nav", "footer", "aside", "noscript", "iframe", "title")
_BLOCK_TAGS = frozenset(
    "p div section article header main li ul ol table tr h1 h2 h3 h4 h5 h6 blockquote pre br hr form fieldset dd dt dl".split()
)


def _charset_of(content_type: str) -> str | None:
    for part in content_type.split(";")[1:]:
        k, _, v = part.strip().partition("=")
        if k.strip().lower() == "charset" and v.strip():
            return v.strip().strip('"').strip("'")
    return None


def _squeeze(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\r", "\n").split("\n")]
    out: list[str] = []
    for line in lines:
        if line:
            out.append(line)
    return "\n".join(out)


def extract_text(body: bytes, content_type: str, *, max_chars: int) -> tuple[str, str]:
    """(title, text)。text/plain 直接解码；text/html 用 lxml.html（惰性 import；缺失 ⇒ 抛 ImportError）。"""
    ctype = content_type.split(";")[0].strip().lower()
    charset = _charset_of(content_type)
    if ctype == "text/plain":
        text = body.decode(charset or "utf-8", errors="replace")
        return "", _squeeze(text)[: max(0, int(max_chars))]
    import lxml.html  # 惰性 import；缺失时 ImportError 由调用方映射为 extract_unavailable

    parser = lxml.html.HTMLParser(encoding=charset or None, remove_comments=True, remove_pis=True)
    root = lxml.html.document_fromstring(body, parser=parser)
    title = ""
    titles = root.xpath("//title")
    if titles:
        title = " ".join((titles[0].text_content() or "").split())[:200]
    for tag in _DROP_TAGS:
        for el in root.xpath(f"//{tag}"):
            el.drop_tree()
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        if el.tag.lower() in _BLOCK_TAGS:
            el.text = "\n" + (el.text or "")
            el.tail = "\n" + (el.tail or "")
    text = _squeeze(root.text_content() or "")
    return title, text[: max(0, int(max_chars))]


# --------------------------------------------------------------------------- #
# SafeFetcher
# --------------------------------------------------------------------------- #


class SafeFetcher:
    def __init__(
        self,
        *,
        transport: FetchTransport | None = None,
        resolver: Resolver | None = None,
        max_redirects: int = 3,
        user_agent: str = "intelligentbase-fetch/1",
    ) -> None:
        self._transport: FetchTransport = transport or PinnedTransport()
        self._resolver = resolver
        self._max_redirects = int(max_redirects)
        self._ua = user_agent

    def _fail(self, url: str, error: FetchErrorKind, *, blocked: WebBlockKind | None = None,
              status: int | None = None, nbytes: int = 0) -> FetchResult:
        return FetchResult(False, url, "", "", error, blocked, status, nbytes, False)

    def fetch(
        self,
        url: str,
        *,
        rules: DomainRules,
        timeout_s: float,
        max_bytes: int,
        max_chars: int,
        allowed_types: tuple[str, ...],
    ) -> FetchResult:
        """永不抛；总期限 = 调用时刻 + timeout_s。"""
        try:
            return self._fetch(url, rules, float(timeout_s), int(max_bytes), int(max_chars), tuple(allowed_types))
        except Exception:  # noqa: BLE001 - 契约：永不抛
            return self._fail(url, "unreachable")

    def _fetch(self, url: str, rules: DomainRules, timeout_s: float, max_bytes: int, max_chars: int,
               allowed_types: tuple[str, ...]) -> FetchResult:
        deadline = time.monotonic() + timeout_s
        guard = UrlGuard(rules, resolver=self._resolver)
        headers = {
            "User-Agent": self._ua,
            "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        current = url
        hops = 0
        while True:
            try:
                target = guard.check(current, deadline=deadline)
            except WebBlocked as exc:
                return self._fail(current, "blocked", blocked=exc.kind)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return self._fail(current, "timeout")
            try:
                resp = self._transport.request(target, headers=headers, timeout_s=remaining)
            except (socket.timeout, TimeoutError):
                return self._fail(current, "timeout")
            except (OSError, ssl.SSLError, http.client.HTTPException):
                return self._fail(current, "unreachable")
            try:
                status = int(resp.status)
                if 300 <= status < 400:
                    location = resp.headers.get("location", "")
                    if not location:
                        return self._fail(current, "http_error", status=status)
                    hops += 1
                    if hops > self._max_redirects:
                        return self._fail(current, "blocked", blocked="too_many_redirects", status=status)
                    current = urljoin(current, location.strip())
                    continue
                if not (200 <= status < 300):
                    return self._fail(current, "http_error", status=status)
                ctype_full = resp.headers.get("content-type", "")
                ctype = ctype_full.split(";")[0].strip().lower()
                if ctype not in {t.strip().lower() for t in allowed_types}:
                    return self._fail(current, "content_type_unsupported", status=status)
                buf = bytearray()
                try:
                    for chunk in resp.chunks:
                        buf.extend(chunk)
                        if len(buf) > max_bytes:
                            return self._fail(current, "content_too_large", status=status, nbytes=len(buf))
                        if time.monotonic() > deadline:
                            return self._fail(current, "timeout", status=status, nbytes=len(buf))
                except (socket.timeout, TimeoutError):
                    return self._fail(current, "timeout", status=status, nbytes=len(buf))
                except (OSError, ssl.SSLError, http.client.HTTPException):
                    return self._fail(current, "unreachable", status=status, nbytes=len(buf))
                try:
                    title, text = extract_text(bytes(buf), ctype_full, max_chars=max_chars + 1)
                except ImportError:
                    return self._fail(current, "extract_unavailable", status=status, nbytes=len(buf))
                except (LookupError, UnicodeError):
                    return self._fail(current, "decode_failed", status=status, nbytes=len(buf))
                except Exception:  # noqa: BLE001 - 解析器对畸形文档的异常
                    return self._fail(current, "decode_failed", status=status, nbytes=len(buf))
                if not text.strip():  # DEF-006：提取不出正文 ⇒ 失败（不以成功 + 空正文交付）
                    return self._fail(current, "empty_content", status=status, nbytes=len(buf))
                truncated = len(text) > max_chars
                return FetchResult(True, current, title, text[:max_chars], None, None, status, len(buf), truncated)
            finally:
                resp.close()
