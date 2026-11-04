"""[REV-28 / GROUP_D] 单元：地址防护 / 域名名单 / 联网策略（MOD-R28-02）。

分层：unit（单模块纯函数，解析器为注入的假解析器，不做真实 DNS，不发任何网络请求）。
溯源：AC-015-02/03、AC-016-01/02/04/07、REQ-NFUNC-004（SSRF 拒绝集 ≥30 条放行 0）。
"""

from __future__ import annotations

import time

import pytest

from ib.core import ToolGrantSpec, ToolParamValue, WebGovernance
from ib.webtools.netguard import (
    DomainRules,
    UrlGuard,
    WebBlocked,
    is_address_allowed,
    parse_domain_list,
)
from ib.webtools.policy import effective_limits, validate_web_grants

PUBLIC_IP = "93.184.216.34"


def _resolver(mapping):
    """假解析器：字面 IP 原样返回；其余查表；查不到抛错（模拟 DNS 失败）。"""
    import ipaddress

    def _r(host, port, timeout_s):
        try:
            ipaddress.ip_address(host.strip("[]"))
            return (host.strip("[]"),)
        except ValueError:
            pass
        if host in mapping:
            return tuple(mapping[host])
        raise OSError("nxdomain")

    return _r


def _check(url, mapping=None, rules=None):
    g = UrlGuard(rules or DomainRules((), ()), resolver=_resolver(mapping or {}))
    return g.check(url, deadline=time.monotonic() + 5)


# --------------------------------------------------------------------------- #
# SSRF 拒绝集（≥30 条，放行 0）
# --------------------------------------------------------------------------- #

#: (说明, URL, 假解析表)——每条都必须被拒绝；列表长度由 TC-UNIT-R28-002 守卫 ≥ 30。
SSRF_REJECT = [
    ("loopback-127.0.0.1", "http://127.0.0.1/", {}),
    ("loopback-127.1.2.3", "http://127.1.2.3/", {}),
    ("loopback-8000端口（AC-015-02 原例）", "http://127.0.0.1:8000/", {}),
    ("private-10.0.0.5", "http://10.0.0.5/", {}),
    ("private-10.255.255.255", "http://10.255.255.255/", {}),
    ("private-172.16.0.1", "http://172.16.0.1/", {}),
    ("private-172.31.255.254", "https://172.31.255.254/", {}),
    ("private-192.168.1.1", "http://192.168.1.1/", {}),
    ("metadata-169.254.169.254", "http://169.254.169.254/latest/meta-data/", {}),
    ("linklocal-169.254.0.1", "http://169.254.0.1/", {}),
    ("cgnat-100.64.0.1", "http://100.64.0.1/", {}),
    ("cgnat-100.127.255.254", "http://100.127.255.254/", {}),
    ("unspecified-0.0.0.0", "http://0.0.0.0/", {}),
    ("this-network-0.1.2.3", "http://0.1.2.3/", {}),
    ("ietf-192.0.0.8", "http://192.0.0.8/", {}),
    ("benchmark-198.18.0.1", "http://198.18.0.1/", {}),
    ("benchmark-198.19.255.255", "http://198.19.255.255/", {}),
    ("multicast-224.0.0.1", "http://224.0.0.1/", {}),
    ("multicast-239.255.255.255", "http://239.255.255.255/", {}),
    ("reserved-240.0.0.1", "http://240.0.0.1/", {}),
    ("broadcast-255.255.255.255", "http://255.255.255.255/", {}),
    ("ipv6-loopback", "http://[::1]/", {}),
    ("ipv6-unspecified", "http://[::]/", {}),
    ("ipv6-ula-fc00", "http://[fc00::1]/", {}),
    ("ipv6-ula-fd12", "http://[fd12:3456::1]/", {}),
    ("ipv6-linklocal", "http://[fe80::1]/", {}),
    ("ipv6-multicast", "http://[ff02::1]/", {}),
    ("ipv4-mapped-loopback", "http://[::ffff:127.0.0.1]/", {}),
    ("ipv4-mapped-private-10", "http://[::ffff:10.0.0.1]/", {}),
    ("ipv4-mapped-metadata", "http://[::ffff:169.254.169.254]/", {}),
    ("nat64-embedded-loopback", "http://[64:ff9b::7f00:1]/", {}),
    ("aws-ipv6-metadata", "http://[fd00:ec2::254]/", {}),
    ("decimal-ip-obfuscation", "http://2130706433/", {"2130706433": ("127.0.0.1",)}),
    ("hex-ip-obfuscation", "http://0x7f.0.0.1/", {"0x7f.0.0.1": ("127.0.0.1",)}),
    ("DNS->private-10", "http://internal.example.com/", {"internal.example.com": ("10.1.2.3",)}),
    ("DNS->metadata", "http://meta.example.com/", {"meta.example.com": ("169.254.169.254",)}),
    ("DNS->loopback(localhost)", "http://localhost/", {"localhost": ("127.0.0.1", "::1")}),
    ("DNS->cgnat", "http://cg.example.com/", {"cg.example.com": ("100.64.9.9",)}),
    ("DNS 多记录含一条私有（rebinding）", "http://rebind.example.com/", {"rebind.example.com": (PUBLIC_IP, "10.0.0.1")}),
    ("DNS->ipv6-ula", "http://v6.example.com/", {"v6.example.com": ("fd00::5",)}),
    ("DNS->ipv4-mapped-private", "http://map.example.com/", {"map.example.com": ("::ffff:192.168.0.1",)}),
    ("scheme-file", "file:///etc/passwd", {}),
    ("scheme-ftp", "ftp://example.com/x", {"example.com": (PUBLIC_IP,)}),
    ("scheme-gopher", "gopher://example.com/", {"example.com": (PUBLIC_IP,)}),
    ("scheme-javascript", "javascript:alert(1)", {}),
    ("scheme-data", "data:text/plain,hello", {}),
    ("userinfo", "http://user:pw@example.com/", {"example.com": (PUBLIC_IP,)}),
    ("userinfo-偷渡内网", "http://example.com@127.0.0.1/", {}),
    ("port-8080", "http://example.com:8080/", {"example.com": (PUBLIC_IP,)}),
    ("port-22", "http://example.com:22/", {"example.com": (PUBLIC_IP,)}),
    ("port-6379", "http://example.com:6379/", {"example.com": (PUBLIC_IP,)}),
    ("ipv6-zone-id", "http://[fe80::1%25eth0]/", {}),
    ("CRLF 注入", "http://example.com/\r\nHost: evil", {"example.com": (PUBLIC_IP,)}),
    ("内部空白", "http://exam ple.com/", {}),
    ("空串", "", {}),
    ("DNS 解析失败（fail-closed）", "http://nonexistent.example.com/", {}),
]


@pytest.mark.parametrize("case", SSRF_REJECT, ids=[c[0] for c in SSRF_REJECT])
def test_TC_UNIT_R28_001_ssrf_reject_set_every_entry_blocked(case):
    """AC-015-02 / REQ-NFUNC-004：拒绝集每一条都被拒绝（放行 0）。"""
    _desc, url, mapping = case
    with pytest.raises(WebBlocked):
        _check(url, mapping)


def test_TC_UNIT_R28_002_ssrf_reject_set_size_at_least_30():
    """REQ-NFUNC-004 口径守卫：拒绝集条数 ≥ 30，且覆盖 DNS 私有 / IPv6 / IPv4-mapped / 169.254.169.254 / 100.64/10。"""
    assert len(SSRF_REJECT) >= 30
    urls = " ".join(u for _d, u, _m in SSRF_REJECT)
    assert "169.254.169.254" in urls and "100.64.0.1" in urls
    assert "[::ffff:" in urls and "[fd" in urls and "[fe80" in urls
    assert sum(1 for _d, _u, m in SSRF_REJECT if m and any(k for k in m if not k[0].isdigit() and k != "example.com")) >= 5


def test_TC_UNIT_R28_003_reject_reason_is_short_code_without_topology():
    """拒绝原因只暴露枚举短码，不回显解析结果与内网拓扑。"""
    with pytest.raises(WebBlocked) as ei:
        _check("http://internal.example.com/", {"internal.example.com": ("10.1.2.3",)})
    assert ei.value.kind == "private_address"
    assert "10.1.2.3" not in str(ei.value) and "internal" not in str(ei.value)


def test_TC_UNIT_R28_004_scheme_reason_codes():
    """AC-015-03：file:// 与 ftp:// 的原因是 scheme_not_allowed（仅 http / https）。"""
    for url in ("file:///etc/passwd", "ftp://example.com/"):
        with pytest.raises(WebBlocked) as ei:
            _check(url, {"example.com": (PUBLIC_IP,)})
        assert ei.value.kind == "scheme_not_allowed"


@pytest.mark.parametrize(
    "url,mapping",
    [
        ("https://example.com/a", {"example.com": (PUBLIC_IP,)}),
        ("http://example.com/a?x=1", {"example.com": (PUBLIC_IP,)}),
        ("https://example.com:443/a", {"example.com": (PUBLIC_IP,)}),
        ("http://8.8.8.8/", {}),
        ("https://1.1.1.1/dns", {}),
        ("http://[2606:4700:4700::1111]/", {}),
        ("https://sub.example.org/p", {"sub.example.org": ("93.184.216.35", "2606:2800:220:1::1")}),
    ],
)
def test_TC_UNIT_R28_005_public_targets_allowed_positive_control(url, mapping):
    """与拒绝集成对的正例：公网目标放行，且钉住的是已校验的字面 IP、保留原主机名。"""
    t = _check(url, mapping)
    assert t.scheme in ("http", "https") and t.port in (80, 443)
    assert t.pinned_ip == (mapping.get(t.host) or (t.host.strip("[]"),))[0]


def test_TC_UNIT_R28_006_is_address_allowed_denied_networks_table():
    """18 个拒绝网段与 is_global 取交：代表地址逐一判定。"""
    denied = ["0.0.0.0", "10.1.1.1", "100.64.1.1", "127.0.0.2", "169.254.169.254", "172.20.0.1", "192.0.0.1",
              "192.168.0.1", "198.18.1.1", "224.0.0.5", "240.0.0.9", "::1", "fc00::2", "fe80::2", "ff00::1",
              "64:ff9b::1", "::ffff:10.0.0.1", "fd00:ec2::254", "fe80::1%eth0", "not-an-ip", ""]
    for a in denied:
        assert is_address_allowed(a) is False, a
    for a in ("8.8.8.8", "93.184.216.34", "1.1.1.1", "2606:4700:4700::1111", "::ffff:8.8.8.8"):
        assert is_address_allowed(a) is True, a


def test_TC_UNIT_R28_007_deadline_exhausted_resolve_failed():
    """期限已过 ⇒ 不再解析，fail-closed 为 resolve_failed。"""
    g = UrlGuard(DomainRules((), ()), resolver=_resolver({"example.com": (PUBLIC_IP,)}))
    with pytest.raises(WebBlocked) as ei:
        g.check("https://example.com/", deadline=time.monotonic() - 1)
    assert ei.value.kind == "resolve_failed"


@pytest.mark.parametrize(
    "url",
    ["http://localhost/", "http://LOCALHOST/", "http://localhost./", "http://2130706433/", "http://0x7f.1/", "http://127.1/",
     "http://017700000001/", "http://0x7f000001/", "http://0/", "http://[::1]/"],
)
def test_TC_UNIT_R28_008_real_default_resolver_local_forms_all_rejected_no_external_dns(url):
    """AC-015-02：用产品**真实的默认解析器**（getaddrinfo + 线程池）验证本机 / 数字混淆写法（十进制 / 十六进制 / 八进制 / 省略段 / localhost 各写法）
    全部被拒。仅涉及 hosts 文件与数字地址解析，不依赖外网 DNS（无外部服务调用）。"""
    from ib.webtools.fetch import default_resolver

    g = UrlGuard(DomainRules((), ()), resolver=default_resolver)
    with pytest.raises(WebBlocked) as ei:
        g.check(url, deadline=time.monotonic() + 5)
    assert ei.value.kind == "private_address"


# --------------------------------------------------------------------------- #
# 域名名单（AC-016-01/02/04）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_010_allowlist_permits_listed_and_subdomain_rejects_other():
    """AC-016-01：白名单 example.com ⇒ example.com 及子域放行，other.org 被拒（domain_not_allowed）。"""
    rules = DomainRules(allow=("example.com",), deny=())
    mp = {"example.com": (PUBLIC_IP,), "www.example.com": (PUBLIC_IP,), "other.org": (PUBLIC_IP,), "notexample.com": (PUBLIC_IP,)}
    assert _check("https://example.com/p", mp, rules).host == "example.com"
    assert _check("https://www.example.com/p", mp, rules).host == "www.example.com"
    for url in ("https://other.org/p", "https://notexample.com/p"):
        with pytest.raises(WebBlocked) as ei:
            _check(url, mp, rules)
        assert ei.value.kind == "domain_not_allowed"


def test_TC_UNIT_R28_011_denylist_wins_over_allowlist():
    """AC-016-02：同一域名同时在白、黑名单 ⇒ 黑名单优先。"""
    rules = DomainRules(allow=("example.com",), deny=("example.com",))
    with pytest.raises(WebBlocked) as ei:
        _check("https://example.com/p", {"example.com": (PUBLIC_IP,)}, rules)
    assert ei.value.kind == "host_blocked"
    # 子域继承黑名单
    r2 = DomainRules(allow=(), deny=("bad.com",))
    with pytest.raises(WebBlocked):
        _check("https://a.bad.com/", {"a.bad.com": (PUBLIC_IP,)}, r2)
    assert _check("https://good.com/", {"good.com": (PUBLIC_IP,)}, r2).host == "good.com"


def test_TC_UNIT_R28_012_parse_domain_list_valid_and_invalid_positions():
    """AC-016-04：非法项（含空格 / 协议头 / 路径 / 端口）指出第几项；合法项小写去重；空项忽略但不占序号。"""
    valid, bad = parse_domain_list("Example.com, a.b-c.org\n\nexample.com")
    assert valid == ("example.com", "a.b-c.org") and bad == ()
    valid, bad = parse_domain_list("ok.com, http://evil.com, has space.com, a.com/path, b.com:8080, -x.com, ok2.com")
    assert valid == ("ok.com", "ok2.com")
    assert bad == (2, 3, 4, 5, 6)
    assert parse_domain_list("") == ((), ()) and parse_domain_list("   ") == ((), ())


# --------------------------------------------------------------------------- #
# 策略：有效上限与保存期校验（AC-016-03/07）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_020_effective_limits_min_of_param_global_hard():
    """AC-016-07 / AC-016-03：有效上限 = min(工具参数, 全局, 硬上限)。"""
    caps = WebGovernance(max_calls_per_turn=5, max_fetch_bytes_per_turn=1_048_576, max_seconds_per_turn=30)
    e = effective_limits({"max_calls_per_turn": "3", "max_bytes_per_turn": "500000"}, caps)
    assert (e.max_calls, e.max_bytes, e.max_seconds) == (3, 500000, 30)
    e = effective_limits({"max_calls_per_turn": "8"}, caps)  # 参数大于全局 ⇒ 取全局
    assert e.max_calls == 5
    e = effective_limits({}, WebGovernance(max_calls_per_turn=20, max_fetch_bytes_per_turn=5_242_880, max_seconds_per_turn=120))
    assert (e.max_calls, e.max_bytes, e.max_seconds) == (20, 5_242_880, 120)
    e = effective_limits({"max_calls_per_turn": "abc", "max_bytes_per_turn": "-1"}, caps)  # 非法参数忽略
    assert (e.max_calls, e.max_bytes) == (5, 1_048_576)


def _grant(*pv):
    return (ToolGrantSpec("advisor", ("web_fetch", "web_search"), tuple(ToolParamValue(n, v) for n, v in pv)),)


def test_TC_UNIT_R28_021_validate_web_grants_over_global_rejected_within_accepted():
    """AC-016-07：保存每轮 3 次 / 500KB 成功；每轮 8 次被拒并指出“超出全局上限（5 次）”。"""
    caps = WebGovernance(max_calls_per_turn=5, max_fetch_bytes_per_turn=1_048_576)
    assert validate_web_grants(_grant(("web_fetch.max_calls_per_turn", "3"), ("web_fetch.max_bytes_per_turn", "500000")), caps) == ()
    errs = validate_web_grants(_grant(("web_fetch.max_calls_per_turn", "8")), caps)
    assert [e.code for e in errs] == ["web_limit_exceeds_global"]
    assert "超出全局上限（5 次）" in errs[0].message
    errs = validate_web_grants(_grant(("web_search.max_calls_per_turn", "6")), caps)
    assert [e.code for e in errs] == ["web_limit_exceeds_global"]
    errs = validate_web_grants(_grant(("web_fetch.max_bytes_per_turn", "2000000")), caps)
    assert [e.code for e in errs] == ["web_limit_exceeds_global"] and "字节" in errs[0].message


def test_TC_UNIT_R28_022_validate_web_grants_invalid_domain_item_position():
    """AC-016-04：域名清单第几项非法逐条指出。"""
    caps = WebGovernance()
    errs = validate_web_grants(_grant(("web_fetch.allow_domains", "ok.com, http://x.com"), ("web_fetch.deny_domains", "bad one.com")), caps)
    assert [e.code for e in errs] == ["web_domain_invalid", "web_domain_invalid"]
    assert "第 2 项" in errs[0].message and "第 1 项" in errs[1].message
    assert validate_web_grants(_grant(("web_fetch.allow_domains", "ok.com,sub.ok.org")), caps) == ()
