# MOD-R28-02 / implements IFC-R28-003（地址防护） / depends MOD-R28-01
"""URL 地址防护：解析一次、逐址校验、钉住已校验 IP（ADR-R28-03 第 4、5 点）。

本文件不含任何网络连接代码，只含解析（经可注入的 `Resolver`）与判定。
拒绝原因只以枚举短码对外暴露，不回显解析结果与内部拓扑。
"""

from __future__ import annotations

import ipaddress
import re
import time
from dataclasses import dataclass
from typing import Callable, Literal
from urllib.parse import urlsplit

__all__ = [
    "WebBlockKind",
    "WebBlocked",
    "DomainRules",
    "parse_domain_list",
    "GuardedTarget",
    "Resolver",
    "UrlGuard",
    "DENIED_NETWORKS",
    "NEVER_ALLOW_NETWORKS",
    "is_address_allowed",
    "URL_MAX_CHARS",
]

WebBlockKind = Literal[
    "scheme_not_allowed",
    "userinfo_not_allowed",
    "port_not_allowed",
    "host_blocked",
    "domain_not_allowed",
    "resolve_failed",
    "private_address",
    "too_many_redirects",
    "budget_exceeded",
    "busy",
    "outbound_rejected",
    "not_configured",
    "audit_failed",
]

URL_MAX_CHARS = 2048


class WebBlocked(Exception):
    """联网动作被拒绝。对外只暴露枚举短码。"""

    def __init__(self, kind: WebBlockKind) -> None:
        super().__init__(kind)
        self.kind: WebBlockKind = kind


# --------------------------------------------------------------------------- #
# 域名名单
# --------------------------------------------------------------------------- #

_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def _valid_domain(item: str) -> bool:
    if not item or len(item) > 253 or item.startswith(".") or item.endswith("."):
        return False
    labels = item.split(".")
    if len(labels) < 1:
        return False
    return all(_LABEL_RE.match(label) for label in labels)


def parse_domain_list(raw: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """逗号 / 换行分隔 → (合法域名, 非法项的 1 起始序号)。

    含内部空格、协议头、路径、端口、通配符以外字符（本版不支持通配符）⇒ 非法；空项被忽略但占序号。
    域名统一小写。
    """
    valid: list[str] = []
    invalid: list[int] = []
    if not raw or not raw.strip():
        return (), ()
    parts = [p for p in re.split(r"[,\n]", raw)]
    idx = 0
    for part in parts:
        item = part.strip()
        if not item:
            continue
        idx += 1
        low = item.lower()
        if _valid_domain(low):
            if low not in valid:
                valid.append(low)
        else:
            invalid.append(idx)
    return tuple(valid), tuple(invalid)


@dataclass(frozen=True, slots=True)
class DomainRules:
    allow: tuple[str, ...]  # 小写 ASCII 域名；匹配 = 等于或为其子域
    deny: tuple[str, ...]  # 黑名单优先

    @staticmethod
    def _match(host: str, domains: tuple[str, ...]) -> bool:
        return any(host == d or host.endswith("." + d) for d in domains)

    def verdict(self, host: str) -> WebBlockKind | None:
        h = host.lower().rstrip(".")
        if self._match(h, self.deny):
            return "host_blocked"
        if self.allow and not self._match(h, self.allow):
            return "domain_not_allowed"
        return None

    def permits(self, host: str) -> bool:
        return self.verdict(host) is None


# --------------------------------------------------------------------------- #
# 地址判定
# --------------------------------------------------------------------------- #

_DENIED_CIDRS = (
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "224.0.0.0/4",
    "240.0.0.0/4",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
    "ff00::/8",
    "64:ff9b::/96",
    "::ffff:0:0/96",
    "fd00:ec2::254/128",
)
DENIED_NETWORKS = tuple(ipaddress.ip_network(c) for c in _DENIED_CIDRS)
_MAPPED = ipaddress.ip_network("::ffff:0:0/96")


# MOD-R29-04 / IFC-R29-030：内网允许名单"绝不放行集"（链路本地 / 元数据 / 保留段；映射内嵌同判）
_NEVER_ALLOW_CIDRS = (
    "169.254.0.0/16",
    "fe80::/10",
    "fd00:ec2::254/128",
    "0.0.0.0/8",
    "224.0.0.0/4",
    "240.0.0.0/4",
    "ff00::/8",
)
NEVER_ALLOW_NETWORKS = tuple(ipaddress.ip_network(c) for c in _NEVER_ALLOW_CIDRS)
# 允许名单命中时可被放行的地址类：回环 / RFC1918 / CGNAT / ULA
_INTERNAL_ALLOWABLE = tuple(
    ipaddress.ip_network(c)
    for c in ("127.0.0.0/8", "::1/128", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "fc00::/7")
)


def is_address_allowed(addr: str, *, internal_allowed: bool = False) -> bool:
    """项目自有拒绝网段 与 `is_global` 取交：两个条件都满足才放行。

    `internal_allowed=True`（仅 MCP 允许名单命中时）只跳过 私有/回环/CGNAT 判定，永不放行 NEVER_ALLOW_NETWORKS。
    """
    if "%" in addr:  # IPv6 zone id
        return False
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip in _MAPPED:
        embedded = ip.ipv4_mapped
        if embedded is None:
            return False
        return is_address_allowed(str(embedded), internal_allowed=internal_allowed)
    if internal_allowed:
        for net in NEVER_ALLOW_NETWORKS:
            if ip.version == net.version and ip in net:
                return False
        for net in _INTERNAL_ALLOWABLE:
            if ip.version == net.version and ip in net:
                return True
    for net in DENIED_NETWORKS:
        if ip.version == net.version and ip in net:
            return False
    return bool(ip.is_global)


# --------------------------------------------------------------------------- #
# 解析器类型（默认实现在 fetch.py，使网络相关导入只出现在 fetch.py / search.py）
# --------------------------------------------------------------------------- #

Resolver = Callable[[str, int, float], tuple[str, ...]]

@dataclass(frozen=True, slots=True)
class GuardedTarget:
    scheme: Literal["http", "https"]
    host: str  # 原主机名（SNI / Host 头 / 证书校验用）
    port: int  # 80 | 443
    pinned_ip: str  # 已校验的字面 IP（连接用）
    path_query: str


_ALLOWED_PORTS = (80, 443)


class UrlGuard:
    def __init__(
        self,
        rules: DomainRules,
        *,
        resolver: Resolver | None = None,
        dns_timeout_s: float = 3.0,
        allowed_ports: frozenset[int] | None = frozenset({80, 443}),
        internal_allow: frozenset[tuple[str, int]] = frozenset(),
    ) -> None:
        self._rules = rules
        self._allowed_ports = allowed_ports  # None ⇒ 任意 1–65535（MCP）
        self._internal_allow = frozenset((str(h).lower().rstrip("."), int(p)) for h, p in internal_allow)
        self._resolver: Resolver | None = resolver  # None ⇒ 惰性取 fetch.default_resolver（本文件不持有任何网络导入）
        self._dns_timeout_s = float(dns_timeout_s)

    def check(self, url: str, *, deadline: float) -> GuardedTarget:
        """`deadline` 为 `time.monotonic()` 口径的绝对期限。违规抛 WebBlocked。"""
        if not isinstance(url, str) or not url or len(url) > URL_MAX_CHARS:
            raise WebBlocked("scheme_not_allowed")
        # 控制字符 / 内部空白（含 CR LF TAB NUL）一律拒绝，防请求走私与解析歧义
        if any(ord(c) < 0x21 or ord(c) == 0x7F for c in url.strip()):
            raise WebBlocked("scheme_not_allowed")
        try:
            parts = urlsplit(url.strip())
        except ValueError:
            raise WebBlocked("scheme_not_allowed") from None
        scheme = (parts.scheme or "").lower()
        if scheme not in ("http", "https"):
            raise WebBlocked("scheme_not_allowed")
        netloc = parts.netloc
        if "@" in netloc:
            raise WebBlocked("userinfo_not_allowed")
        try:
            port_raw = parts.port
        except ValueError:
            raise WebBlocked("port_not_allowed") from None
        host_raw = parts.hostname
        if not host_raw:
            raise WebBlocked("scheme_not_allowed")
        port = port_raw if port_raw is not None else (443 if scheme == "https" else 80)
        if self._allowed_ports is None:
            if not (1 <= port <= 65535):
                raise WebBlocked("port_not_allowed")
        elif port not in self._allowed_ports:
            raise WebBlocked("port_not_allowed")
        host = host_raw.lower().rstrip(".")
        try:
            host_ascii = host.encode("idna").decode("ascii")
        except UnicodeError:
            raise WebBlocked("host_blocked") from None
        if not host_ascii:
            raise WebBlocked("host_blocked")
        verdict = self._rules.verdict(host_ascii)
        if verdict is not None:
            raise WebBlocked(verdict)
        remaining = deadline - time.monotonic()
        timeout = min(self._dns_timeout_s, remaining)
        if timeout <= 0:
            raise WebBlocked("resolve_failed")
        try:
            resolver = self._resolver
            if resolver is None:
                from .fetch import default_resolver

                resolver = default_resolver
            addrs = tuple(resolver(host_ascii, port, timeout))
        except WebBlocked:
            raise
        except Exception:  # noqa: BLE001
            raise WebBlocked("resolve_failed") from None
        if not addrs:
            raise WebBlocked("resolve_failed")
        internal_ok = (host_ascii, port) in self._internal_allow
        for a in addrs:
            if not is_address_allowed(str(a), internal_allowed=internal_ok):
                raise WebBlocked("private_address")
        path = parts.path or "/"
        path_query = path + ("?" + parts.query if parts.query else "")
        return GuardedTarget(
            scheme=scheme,  # type: ignore[arg-type]
            host=host_ascii,
            port=port,
            pinned_ip=str(addrs[0]),
            path_query=path_query,
        )
