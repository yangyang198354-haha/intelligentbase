"""[REV-29 / GROUP_D] 单元：出网防护（SSRF）——地址拒绝集 N≥30、允许名单精确放行、绝不放行集、默认值回归。

分层：unit（UrlGuard 注入假解析器，无套接字）。溯源：US-027 / 002 / 004 / 008。
"""

from __future__ import annotations

import ipaddress
import time

import pytest

from ib.webtools.netguard import DomainRules, UrlGuard, WebBlocked

TABLE = {
    "loop.t": ("127.0.0.1",), "a10.t": ("10.1.2.3",), "a172.t": ("172.16.5.4",), "a192.t": ("192.168.1.1",),
    "meta.t": ("169.254.169.254",), "cgnat.t": ("100.64.0.1",), "bench.t": ("198.18.0.1",), "zero.t": ("0.0.0.0",),
    "mcast.t": ("224.0.0.1",), "resv.t": ("240.0.0.1",), "v6lo.t": ("::1",), "v6ula.t": ("fc00::1",),
    "v6ll.t": ("fe80::1",), "v6meta.t": ("fd00:ec2::254",), "mapped.t": ("::ffff:127.0.0.1",),
    "mappedmeta.t": ("::ffff:169.254.169.254",), "nat64.t": ("64:ff9b::7f00:1",), "mixed.t": ("93.184.216.34", "10.0.0.5"),
    "empty.t": (), "good.t": ("93.184.216.34",), "zone.t": ("fe80::1%eth0",), "ok10.t": ("10.0.0.8",),
    "ok127.t": ("127.0.0.1",), "okcg.t": ("100.64.0.5",), "linkloc.t": ("169.254.10.1",), "ulaallow.t": ("fc00::5",),
    "rebind.t": ("169.254.169.254",),
}


def _resolver(host: str, port: int, timeout: float):
    if host in TABLE:
        return TABLE[host]
    ipaddress.ip_address(host)
    return (host,)


REJECTS = [
    "http://loop.t:9000/", "http://a10.t:9000/", "http://a172.t:9000/", "http://a192.t:9000/", "http://meta.t:80/",
    "http://cgnat.t:9000/", "http://bench.t:9000/", "http://zero.t:9000/", "http://mcast.t:9000/", "http://resv.t:9000/",
    "http://v6lo.t:9000/", "http://v6ula.t:9000/", "http://v6ll.t:9000/", "http://v6meta.t:9000/", "http://mapped.t:9000/",
    "http://mappedmeta.t:9000/", "http://nat64.t:9000/", "http://mixed.t:9000/", "http://empty.t:9000/",
    "http://127.0.0.1:9000/", "http://169.254.169.254/", "http://[::1]:9000/", "http://[fd00:ec2::254]/", "http://[fe80::1]:80/",
    "ftp://good.t/", "file:///etc/passwd", "http://user:pw@good.t/", "https://good.t:0/", "https://good.t:65536/",
    "http://zone.t:9000/", "javascript:alert(1)", "http://good.t:99999/",
    "http://2130706433/", "http://0x7f000001/", "http://0177.0.0.1/", "http://127.1/", "http://[::ffff:7f00:1]/",
]


def _guard(**kw):
    return UrlGuard(DomainRules((), ()), resolver=_resolver, allowed_ports=None, **kw)


@pytest.mark.parametrize("url", REJECTS)
def test_TC_UNIT_R29_120_reject_set_AC_027_02(url):
    """AC-027-02：地址拒绝集（共 38 条 ≥ 30；含十进制 / 十六进制 / 八进制 IP 写法、IPv6 回环与 ULA、解析到私有的域名）全部被拒；允许名单为空。"""
    with pytest.raises(WebBlocked):
        _guard().check(url, deadline=time.monotonic() + 30)


def test_TC_UNIT_R29_121_reject_set_size_and_public_pass_through_positive_AC_027_02():
    """集合规模 ≥ 30；正例：公网 https 任意端口放行（MCP 允许任意端口）。"""
    assert len(REJECTS) >= 30
    t = _guard().check("https://good.t:8443/x?y=1", deadline=time.monotonic() + 30)
    assert t.port == 8443 and t.scheme == "https" and t.pinned_ip == "93.184.216.34"  # 钉 IP


def test_TC_UNIT_R29_122_dns_rebinding_public_then_private_blocked_AC_027_02():
    """先公后私的 DNS 重绑：每次 check 重新解析，第二次解析为私有地址时被拒。"""
    seq = [("93.184.216.34",), ("10.0.0.5",)]

    def rebind(host, port, timeout):
        return seq.pop(0) if len(seq) > 1 else seq[0]

    g = UrlGuard(DomainRules((), ()), resolver=rebind, allowed_ports=None)
    assert g.check("https://rb.t/", deadline=time.monotonic() + 30).pinned_ip == "93.184.216.34"
    with pytest.raises(WebBlocked):
        g.check("https://rb.t/", deadline=time.monotonic() + 30)


ALLOW = frozenset({("ok10.t", 9000), ("ok127.t", 9100), ("okcg.t", 9200), ("ulaallow.t", 9000),
                   ("meta.t", 80), ("linkloc.t", 8080), ("rebind.t", 443), ("169.254.169.254", 80), ("169.254.10.1", 8080)})


@pytest.mark.parametrize("url", ["http://ok10.t:9000/", "http://ok127.t:9100/", "http://okcg.t:9200/", "http://ulaallow.t:9000/"])
def test_TC_UNIT_R29_123_internal_allow_exact_host_port_passes_AC_027_03(url):
    """AC-027-03：回环 / 私有 / CGNAT / ULA 经名单按精确主机 + 端口放行（正例）。"""
    assert _guard(internal_allow=ALLOW).check(url, deadline=time.monotonic() + 30).scheme == "http"


@pytest.mark.parametrize("url", ["http://ok10.t:9001/", "http://a10.t:9000/", "http://loop.t:9100/", "http://cgnat.t:9200/"])
def test_TC_UNIT_R29_124_internal_allow_does_not_widen_AC_027_03(url):
    """AC-027-03：同主机别端口 / 别主机同端口仍被拒（名单不放大）。"""
    with pytest.raises(WebBlocked):
        _guard(internal_allow=ALLOW).check(url, deadline=time.monotonic() + 30)


@pytest.mark.parametrize("url", ["http://meta.t:80/", "http://linkloc.t:8080/", "https://rebind.t:443/",
                                 "http://169.254.169.254:80/", "http://169.254.10.1:8080/"])
def test_TC_UNIT_R29_125_never_allow_set_even_when_in_allowlist_AC_027_07(url):
    """AC-027-07：链路本地 / 云元数据地址即使在名单内也永不放行（含域名解析到元数据地址）。"""
    with pytest.raises(WebBlocked):
        _guard(internal_allow=ALLOW).check(url, deadline=time.monotonic() + 30)


def test_TC_UNIT_R29_126_default_guard_still_80_443_only_regression_NFUNC_001():
    """默认值回归（REQ-NFUNC-001）：未传新参数的 UrlGuard 仍只允许 80/443，行为与 R28 一致。"""
    g = UrlGuard(DomainRules((), ()), resolver=_resolver)
    for url in ("http://good.t:8080/", "https://good.t:8443/"):
        with pytest.raises(WebBlocked) as ei:
            g.check(url, deadline=time.monotonic() + 30)
        assert ei.value.kind == "port_not_allowed"
    assert g.check("https://good.t/", deadline=time.monotonic() + 30).port == 443
