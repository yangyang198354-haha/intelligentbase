"""[REV-28 / GROUP_D-003] 单元：DeepSeek 搜索适配器、离线替身、Key 解析、提供方工厂的离线 / 生产闸、配置校验（MOD-R28-03）。

分层：unit（全部经 `FakeDeepSeekTransport` / 打桩 opener；autouse 夹具断言**零真实网络连接**，AC-014-06）。
期望值出处：`docs/external_api/deepseek_search_fetch.md`（端点 / 请求头 / 字段范围 / 错误码）与 module_design IFC-R28-029 状态码映射表；
**没有任何期望值取自被测代码的输出**。哨兵 Key 为测试占位串，非真实凭据。
溯源：AC-014-05~10、AC-016-09、AC-018-05 / 06、AC-020-01~03（及 REQ-NFUNC-005 / 006 / 011）。
"""

from __future__ import annotations

import dataclasses
import http.client
import io
import json
import logging
import re
import socket
import ssl
import urllib.error
from types import SimpleNamespace

import pytest
from advisor_r28_support import web_outcome

from ib.config import ConfigurationResolver, DictConfigurationSource
from ib.core import ConfigError, SearchHit, SearchOutcome, SearchQuery, WebGovernance
from ib.llm import resolve_llm_api_key
from ib.webtools import deepseek as ds
from ib.webtools.deepseek import DeepSeekSearchProvider, HttpReply, TransportError, UrllibPostTransport
from ib.webtools.deepseek_double import (
    DoubleReply,
    FakeDeepSeekTransport,
    empty_results,
    error_reply,
    ok_results,
    search_item,
)
from ib.webtools.gate import WebEgressGate, WebTurn, bind_web_turn
from ib.webtools.search import (
    FakeSearchProvider,
    NullSearchProvider,
    WebSearchSettings,
    build_search_provider,
    register_search_provider,
)
from ib.webtools.tools import (
    PHRASE_BUDGET,
    PHRASE_QUERY_EMPTY,
    PHRASE_SEARCH_TIMEOUT,
    WebRuntime,
    web_search_tool,
)

KEY = "R28-DS-SENTINEL-KEY-NOT-A-REAL-CREDENTIAL-9917"
# 资料 §端点与鉴权 / §Search 请求 的字面值（独立于被测常量）
DOC_SEARCH_URL = "https://api.deepseek.com/v1/tools/search"
DOC_HOST = "api.deepseek.com"
# 设计表（module_design IFC-R28-029 状态码映射；资料 §错误 列出的状态码）
EXPECTED_KIND = {
    400: "rejected", 401: "auth_failed", 402: "quota_exceeded", 403: "rejected", 404: "rejected",
    408: "timeout", 413: "rejected", 429: "rate_limited", 500: "unreachable", 504: "timeout",
}
HITS3 = [
    search_item(title="标题甲", url="https://a.example.com/1", snippet="短摘要甲", summary="长摘要甲"),
    search_item(title="标题乙", url="https://b.example.com/2", snippet="短摘要乙", summary="长摘要乙"),
    search_item(title="标题丙", url="https://c.example.com/3", snippet="短摘要丙", summary="长摘要丙"),
]


class SpyTransport(FakeDeepSeekTransport):
    """替身子类：额外记录原始请求头 / 体（测试用，不改产品代码）。"""

    def __init__(self, script=(), **kw):
        kw.setdefault("expected_key", KEY)
        super().__init__(script, **kw)
        self.raw: list[dict] = []

    def post_json(self, url, *, headers, body, timeout_s, max_reply_bytes):
        self.raw.append({"url": url, "headers": dict(headers), "body": body, "timeout_s": timeout_s})
        return super().post_json(url, headers=headers, body=body, timeout_s=timeout_s, max_reply_bytes=max_reply_bytes)


def _q(text="天气", n=5, lang=None, region=None, timeout=3.0):
    return SearchQuery(text=text, max_results=n, lang=lang, region=region, timeout_s=timeout)


def _prov(script=(), key=KEY):
    tr = SpyTransport(script)
    return DeepSeekSearchProvider(key, transport=tr), tr


def _scrub(out: SearchOutcome) -> str:
    return repr(dataclasses.replace(out, elapsed_ms=0))


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """AC-014-06：自动化测试发往真实端点（任何外网）的连接数 = 0；一旦有人尝试连接即失败。"""
    attempts: list[str] = []

    def _boom(*a, **k):
        attempts.append("connect")
        raise AssertionError("测试中出现了真实网络连接尝试")

    monkeypatch.setattr(socket.socket, "connect", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    yield
    assert attempts == []


class _LogCapture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record):
        self.lines.append(record.getMessage())


@pytest.fixture()
def logs():
    lg = logging.getLogger("intelligentbase")
    h, old = _LogCapture(), lg.level
    lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    yield h
    lg.removeHandler(h)
    lg.setLevel(old)


# --------------------------------------------------------------------------- #
# 请求契约（AC-014-06 / 014-09 / 018-06；AQ6）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_200_request_contract_url_method_headers_and_body_keys_exactly_query_count_need_content():
    """AC-018-06 / AC-014-07（happy path，与 206 的降级成对）：POST 到资料所载 Search 端点；请求头恰为 Authorization Bearer + Content-Type；
    请求体键集恰为 {query,count,need_content}，need_content=false；200 非空 ⇒ 3 条命中且计费口径 +1。"""
    p, tr = _prov([ok_results(HITS3)])
    out = p.search(_q("上海明天天气", 3))
    assert out.error is None and len(out.hits) == 3
    assert len(tr.raw) == 1 and tr.raw[0]["url"] == DOC_SEARCH_URL
    assert tr.requests[0].method == "POST" and tr.requests[0].authorization_ok is True
    assert tr.raw[0]["headers"] == {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    body = json.loads(tr.raw[0]["body"].decode("utf-8"))
    assert set(body) == {"query", "count", "need_content"}
    assert body == {"query": "上海明天天气", "count": 3, "need_content": False}
    assert tr.billable_calls == 1  # 资料 §限流与计费：200 且结果非空才计费


def test_TC_UNIT_R28_201_body_never_carries_localization_or_original_question_and_region_is_ignored():
    """AC-018-06 / AQ6=A：无论 region / lang 如何配置，请求体不含 localization、ori_question，也不含 region 的值；region 被适配器忽略。"""
    p, tr = _prov([ok_results(HITS3)] * 3)
    p.search(_q("天气", 5, region="203.0.113.7"))
    p.search(_q("天气", 5, lang="zh,en", region="CN"))
    p.search(_q("天气", 5, region=""))
    for raw in tr.raw:
        txt = raw["body"].decode("utf-8")
        body = json.loads(txt)
        assert set(body) == {"query", "count", "need_content"}
        assert "localization" not in txt and "ori_question" not in txt
        assert "203.0.113.7" not in txt and "CN" not in txt and "region" not in txt
    # region 不改变请求：有无 region 的 query/count 完全一致
    b0, b2 = (json.loads(tr.raw[i]["body"]) for i in (0, 2))
    assert b0 == b2


@pytest.mark.parametrize("n", [1, 63, 127, 128])
def test_TC_UNIT_R28_202_query_up_to_128_unicode_chars_sent_unchanged_and_over_128_rejected_at_query_construction(n):
    """AC-014-09 / 资料 §Search 请求（query 1–128 Unicode 字符）：128 字符整段发送不变（CJK 以字符计）；SearchQuery 拒绝 129+ 字符。"""
    text = "汉" * n
    p, tr = _prov([ok_results(HITS3)])
    p.search(_q(text))
    assert json.loads(tr.raw[0]["body"])["query"] == text
    if n == 128:
        with pytest.raises(ValueError):
            _q("汉" * 129)
        with pytest.raises(ValueError):
            _q("")


def test_TC_UNIT_R28_203_lang_suffix_keeps_total_within_128_and_invalid_lang_ignored_with_warning_without_value(logs):
    """AC-014-09 / 资料 §Search 请求（lang:zh,en 操作符）：合法 lang ⇒ 末尾追加 ` lang:zh,en`，总长 ≤128（基础文本被截）；
    非法 lang（试图注入 site: 操作符）⇒ 忽略，请求体 query 原样，日志不含该值。"""
    p, tr = _prov([ok_results(HITS3)] * 3)
    p.search(_q("汉" * 128, lang="zh,en"))
    sent = json.loads(tr.raw[0]["body"])["query"]
    assert len(sent) <= 128 and sent.endswith(" lang:zh,en") and sent.startswith("汉")
    p.search(_q("天气", lang="zh,en"))
    assert json.loads(tr.raw[1]["body"])["query"] == "天气 lang:zh,en"
    evil = "zh site:evil.example"
    p.search(_q("天气", lang=evil))
    assert json.loads(tr.raw[2]["body"])["query"] == "天气"
    assert not any("evil.example" in ln for ln in logs.lines)


@pytest.mark.parametrize("count", [1, 5, 50])
def test_TC_UNIT_R28_204_count_in_1_to_50_sent_as_integer_and_out_of_range_rejected_at_query_construction(count):
    """AC-014-09 / 资料 §Search 请求（count 1–50 整数）：1、5、50 原样作为整数发送；0、51、-1、布尔值被 SearchQuery 拒绝。"""
    p, tr = _prov([ok_results(HITS3)])
    p.search(_q("天气", count))
    sent = json.loads(tr.raw[0]["body"])["count"]
    assert sent == count and type(sent) is int
    if count == 50:
        for bad in (0, 51, -1, True):
            with pytest.raises(ValueError):
                _q("天气", bad)


def test_TC_UNIT_R28_205_blank_query_never_leaves_process_zero_requests():
    """AC-014-09：全空白检索词 ⇒ 不向提供方出站（请求数 0），返回 rejected。与 200 正常检索成对。"""
    p, tr = _prov([ok_results(HITS3)])
    for blank in ("   ", "\t\n", "　"):
        out = p.search(_q(blank))
        assert (out.hits, out.error) == ((), "rejected")
    assert tr.requests == [] and tr.raw == []
    ok = p.search(_q("天气"))
    assert ok.error is None and len(tr.requests) == 1  # 正例：非空检索词正常出站


# --------------------------------------------------------------------------- #
# 响应解析：200 非空 / 200 空 / 非常形态（AC-014-07 / 014-10）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_206_success_hits_carry_nonempty_title_url_summary_in_order_and_unknown_fields_ignored():
    """AC-014-07：每条命中含非空标题、网址、摘要（summary 优先，缺则 snippet）；保持返回顺序；未知字段忽略；超出 limit 的截断。"""
    items = [
        search_item(title="甲", url="https://a.example.com/1", snippet="短甲", summary="长甲", brand_new_field={"x": 1}),
        search_item(title="乙", url="https://b.example.com/2", snippet="只有短摘要乙", summary=""),
        search_item(title="丙", url="http://c.example.com/3", snippet="短丙", summary="长丙"),
        search_item(title="丁", url="https://d.example.com/4", snippet="短丁", summary="长丁"),
    ]
    p, tr = _prov([ok_results(items)])
    out = p.search(_q("q", 3))
    assert out.error is None
    assert out.hits == (
        SearchHit(title="甲", snippet="长甲", url="https://a.example.com/1"),
        SearchHit(title="乙", snippet="只有短摘要乙", url="https://b.example.com/2"),
        SearchHit(title="丙", snippet="长丙", url="http://c.example.com/3"),
    )
    assert all(h.title and h.snippet and h.url for h in out.hits)


def test_TC_UNIT_R28_207_empty_results_is_not_a_fault_no_error_no_hits_and_not_billable():
    """AC-014-10：200 + 空数组 ⇒ error=None、hits=()（如实空结果，不是故障）；资料 §限流与计费：空结果不计费。"""
    p, tr = _prov([empty_results(), ok_results(HITS3)])
    out = p.search(_q("冷门词"))
    assert out.error is None and out.hits == ()
    assert tr.billable_calls == 0
    ok = p.search(_q("热门词"))  # 成对正例
    assert ok.error is None and len(ok.hits) == 3 and tr.billable_calls == 1


@pytest.mark.parametrize(
    "reply",
    [
        DoubleReply(200, b"not json"),
        DoubleReply(200, b"[]"),
        DoubleReply(200, b"{}"),
        DoubleReply(200, b'{"results": "x"}'),
        DoubleReply(200, b'{"results": {"a": 1}}'),
        DoubleReply(200, json.dumps({"results": [{"title": "t", "url": "ftp://x.example/1", "summary": "s"}]}).encode()),
        DoubleReply(200, json.dumps({"results": [{"title": "t", "summary": "s"}, {"title": "u", "url": "javascript:alert(1)"}]}).encode()),
        DoubleReply(200, json.dumps({"results": [1, "x", None]}).encode()),
        DoubleReply(204, b""),
        DoubleReply(302, b""),
    ],
)
def test_TC_UNIT_R28_208_malformed_or_unusable_success_shapes_map_to_bad_response_never_raise(reply):
    """设计表“200 但 JSON 非法 / 无 results 数组 / 条目全不可用 ⇒ bad_response”，非 200 的 2xx 与 3xx ⇒ bad_response；永不抛。"""
    p, _tr = _prov([reply])
    out = p.search(_q("q"))
    assert (out.hits, out.error) == ((), "bad_response")


def test_TC_UNIT_R28_209_oversize_reply_maps_to_bad_response_and_pair_with_normal_reply():
    """响应体超过读取上限 ⇒ bad_response（不解析）；上限内的正常响应成对通过。"""
    big = DoubleReply(200, b'{"results": [], "pad": "' + b"x" * (ds.SEARCH_REPLY_MAX_BYTES + 10) + b'"}')
    p, _tr = _prov([big, ok_results(HITS3)])
    assert p.search(_q("q")).error == "bad_response"
    assert p.search(_q("q")).error is None


# --------------------------------------------------------------------------- #
# 错误映射、不重试、不泄露（AC-014-08 / 016-09 / 018-05）
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("status", sorted(EXPECTED_KIND))
def test_TC_UNIT_R28_210_every_documented_error_status_maps_to_designed_kind_single_attempt_and_no_leak(status):
    """AC-014-08（资料 §错误 列出的 10 个状态码，与 200 正例 TC-200 成对）：映射到设计的降级类别；hits 为空；
    单次尝试（请求数恰为 1，不重试）；结果中不出现状态码、错误体 message / type / code、Key。"""
    p, tr = _prov([error_reply(status)])
    out = p.search(_q("q"))
    assert (out.hits, out.error) == ((), EXPECTED_KIND[status])
    assert len(tr.requests) == 1 and tr.billable_calls == 0
    text = _scrub(out)
    for forbidden in (str(status), "double-placeholder", "double_placeholder", f"double_{status}", "invalid_request", KEY):
        assert forbidden not in text


@pytest.mark.parametrize("status", [401, 402, 429, 500, 504, 400])
def test_TC_UNIT_R28_211_error_body_content_is_never_read_swapping_message_changes_nothing(status):
    """设计：适配器只看状态码、不读错误体。把错误体换成任意文本（含像 Key 的串、HTML、非 JSON）⇒ 映射结果与输出完全不变，输出不含该文本。"""
    bodies = [
        json.dumps({"error": {"message": "Your key sk-LEAKY-1234567890 is invalid; pay 7 USD", "type": "x", "param": None, "code": "c"}}).encode(),
        b"<html><body>Bad Gateway KEY=abc</body></html>",
        b"",
    ]
    outs = []
    for b in bodies:
        p, _tr = _prov([DoubleReply(status, b)])
        out = p.search(_q("q"))
        outs.append(_scrub(out))
        assert out.error == EXPECTED_KIND[status]
        assert "LEAKY" not in repr(out) and "Bad Gateway" not in repr(out)
    assert len(set(outs)) == 1


def test_TC_UNIT_R28_212_unlisted_4xx_5xx_are_designed_fallbacks_rejected_and_unreachable():
    """设计表“其他 4xx ⇒ rejected、500 及其他 5xx ⇒ unreachable”：409、422 ⇒ rejected；502、503 ⇒ unreachable。"""
    for st, kind in ((409, "rejected"), (422, "rejected"), (502, "unreachable"), (503, "unreachable")):
        p, tr = _prov([DoubleReply(st, b"")])
        assert p.search(_q("q")).error == kind and len(tr.requests) == 1


def test_TC_UNIT_R28_213_network_level_failures_map_to_timeout_or_unreachable_and_unexpected_exceptions_to_bad_response_without_leak():
    """设计：套接字超时 ⇒ timeout；DNS / 连接 / TLS ⇒ unreachable；意外异常 ⇒ bad_response 且异常内容（含 Key）不外泄；永不抛。"""
    p, _ = _prov([DoubleReply(0, b"", network_error="timeout"), DoubleReply(0, b"", network_error="unreachable"),
                  DoubleReply(200, b"{}", delay_s=99.0)])
    assert p.search(_q("q")).error == "timeout"
    assert p.search(_q("q")).error == "unreachable"
    assert p.search(_q("q", timeout=1.0)).error == "timeout"  # 延迟 > 超时 ⇒ 超时

    class _Boom:
        def post_json(self, *a, **k):
            raise RuntimeError(f"leaky internal {KEY}")

    out = DeepSeekSearchProvider(KEY, transport=_Boom()).search(_q("q"))
    assert (out.hits, out.error) == ((), "bad_response") and KEY not in repr(out) and "leaky" not in repr(out)


def test_TC_UNIT_R28_214_no_retry_each_attempt_is_one_request_429_then_500_then_success_gives_exactly_three_requests():
    """AQ8=A / AC-016-09：不重试——三次 search（429、500、成功）恰产生 3 次请求；失败的两次不会被适配器内部补发；第三次成功。"""
    p, tr = _prov([error_reply(429), error_reply(500), ok_results(HITS3)])
    assert p.search(_q("q")).error == "rate_limited" and len(tr.requests) == 1
    assert p.search(_q("q")).error == "unreachable" and len(tr.requests) == 2
    ok = p.search(_q("q"))
    assert ok.error is None and len(ok.hits) == 3 and len(tr.requests) == 3


def test_TC_UNIT_R28_215_timeout_seconds_are_passed_to_transport_per_query():
    """资料未给超时数值，平台期限由查询携带：query.timeout_s 原样传给传输缝（资源约束参数断言）。"""
    p, tr = _prov([ok_results(HITS3), ok_results(HITS3)])
    p.search(_q("q", timeout=2.5))
    p.search(_q("q", timeout=7.0))
    assert [r["timeout_s"] for r in tr.raw] == [2.5, 7.0]


# --------------------------------------------------------------------------- #
# Key 卫生（AC-018-05 / CR-016）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_216_sentinel_key_appears_only_in_recorded_authorization_header_zero_elsewhere(logs):
    """AC-018-05 / CR-016：哨兵 Key 只出现在传输缝收到的 Authorization 头（1 次/请求）；在 repr / str / health() / describe_egress() /
    全部降级结果 / 日志 / 构造期异常消息中出现 0 次。"""
    script = [ok_results(HITS3), empty_results()] + [error_reply(s) for s in sorted(EXPECTED_KIND)]
    p, tr = _prov(script)
    outs = [p.search(_q("q")) for _ in script]
    surfaces = [repr(p), str(p), repr(p.health()), repr(p.describe_egress()), repr(tr.requests), "\n".join(logs.lines)]
    surfaces += [repr(o) for o in outs]
    for s in surfaces:
        assert KEY not in s
    assert [r["headers"]["Authorization"] for r in tr.raw] == [f"Bearer {KEY}"] * len(script)
    for bad in ("", "   ", None, "k\nInjected: 1", "k\r\nX: y"):
        with pytest.raises(ValueError) as ei:
            DeepSeekSearchProvider(bad, transport=tr)  # type: ignore[arg-type]
        assert KEY not in str(ei.value) and "Injected" not in str(ei.value)
    with pytest.raises(ValueError) as ei2:
        DeepSeekSearchProvider(KEY, transport=None)  # type: ignore[arg-type]
    assert KEY not in str(ei2.value)


def test_TC_UNIT_R28_217_health_declares_configured_without_network_and_egress_is_deepseek_host_with_search_category_only():
    """AC-018-03：health() 不外呼（零连接，由 autouse 夹具兜底）；外发声明 remote=True、主机 api.deepseek.com、数据类别仅 web_search_query。"""
    p, tr = _prov()
    h = p.health()
    assert h.ok is True and h.detail == "configured" and tr.requests == []
    e = p.describe_egress()
    assert (e.remote, e.endpoint_host, list(e.data_categories)) == (True, DOC_HOST, ["web_search_query"])
    assert p.provider_id == "deepseek"


def test_TC_UNIT_R28_218_double_validates_request_like_documented_and_rejects_wrong_key_with_401():
    """替身自身与资料一致（场景可信度）：Key 不符 ⇒ 401；缺 Content-Type / 非法字段 ⇒ 400；合法 ⇒ 按脚本；适配器遇 401 ⇒ auth_failed。"""
    tr = SpyTransport([ok_results(HITS3)], expected_key="ANOTHER-KEY")
    out = DeepSeekSearchProvider(KEY, transport=tr).search(_q("q"))
    assert out.error == "auth_failed" and tr.requests[0].authorization_ok is False
    tr2 = FakeDeepSeekTransport([ok_results(HITS3)], expected_key=KEY)
    good = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    body = json.dumps({"query": "q", "count": 3, "need_content": False}).encode()
    assert tr2.post_json(DOC_SEARCH_URL, headers={"Authorization": f"Bearer {KEY}"}, body=body, timeout_s=1, max_reply_bytes=999).status == 400
    bad_count = json.dumps({"query": "q", "count": 51}).encode()
    assert tr2.post_json(DOC_SEARCH_URL, headers=good, body=bad_count, timeout_s=1, max_reply_bytes=999).status == 400
    assert tr2.post_json(DOC_SEARCH_URL, headers=good, body=body, timeout_s=1, max_reply_bytes=1 << 20).status == 200
    with pytest.raises(ValueError):
        error_reply(418)  # 替身只构造资料列出的错误码


# --------------------------------------------------------------------------- #
# 与联网工具层的衔接（AC-014-05 / 014-09 / 016-09）
# --------------------------------------------------------------------------- #


class _Audit:
    def __init__(self):
        self.entries = []

    def record(self, e):
        self.entries.append(e)


def _rt(provider):
    gate = WebEgressGate(audit=_Audit(), clock=lambda: "2026-11-03T00:00:00Z")
    return WebRuntime(provider=provider, fetcher=None, gate=gate, governance=None)


def _turn(caps=None):
    return WebTurn("t-ds", "p_alpha", "tester", (), caps or WebGovernance(max_calls_per_turn=5))


def test_TC_UNIT_R28_219_two_providers_same_three_hits_yield_identical_tool_output_structure_title_summary_url():
    """AC-014-05 / 014-07：FakeSearchProvider（端口级）与 DeepSeekSearchProvider（经 FakeDeepSeekTransport）返回同一组 3 条结果 ⇒
    工具对顾问的返回逐字相同（每条含标题、摘要、网址），顾问侧无需修改。"""
    fake = FakeSearchProvider([web_outcome(*[(h["title"], h["summary"], h["url"]) for h in HITS3])])
    p, _tr = _prov([ok_results(HITS3)])
    with bind_web_turn(_turn()):
        a = web_search_tool("天气", runtime=_rt(fake), max_results=3)
    with bind_web_turn(_turn()):
        b = web_search_tool("天气", runtime=_rt(p), max_results=3)
    assert a.ok and b.ok and a.content == b.content
    for h in HITS3:
        assert h["title"] in b.content and h["summary"] in b.content and h["url"] in b.content


def test_TC_UNIT_R28_220_tool_layer_truncates_query_to_128_clamps_count_and_skips_blank_before_provider():
    """AC-014-09：模型生成 200 字符检索词 ⇒ 发往提供方的 query ≤128（恰为前 128 字符）；max_results 100 ⇒ 50、0 ⇒ 1；
    全空白检索词 ⇒ 固定短语“检索词为空”，请求数不增加。"""
    p, tr = _prov([ok_results(HITS3)] * 5)
    rt = _rt(p)
    long_q = "词" * 200
    with bind_web_turn(_turn(WebGovernance(max_calls_per_turn=10))):
        r = web_search_tool(long_q, runtime=rt, max_results=100)
        web_search_tool("天气", runtime=rt, max_results=0)
        blank = web_search_tool("   ", runtime=rt)
    assert r.ok
    b0 = json.loads(tr.raw[0]["body"])
    assert b0["query"] == "词" * 128 and len(b0["query"]) <= 128 and b0["count"] == 50
    assert json.loads(tr.raw[1]["body"])["count"] == 1
    assert (blank.ok, blank.content) == (False, PHRASE_QUERY_EMPTY) and len(tr.requests) == 2


@pytest.mark.parametrize("status", sorted(EXPECTED_KIND))
def test_TC_UNIT_R28_221_tool_result_for_every_error_status_is_fixed_phrase_without_code_message_or_key(status):
    """AC-014-08（与 TC-219 成功正例成对）：每个资料列出的错误状态 ⇒ 工具返回固定降级短语（408 / 504 为“联网检索超时”，其余为“联网检索失败”），
    ok=False；内容不含状态码、错误体文本、Key；审计仍写一条出站记录。"""
    p, tr = _prov([error_reply(status)])
    audit = _Audit()
    rt = WebRuntime(provider=p, fetcher=None, gate=WebEgressGate(audit=audit, clock=lambda: "2026-11-03T00:00:00Z"), governance=None)
    with bind_web_turn(_turn()):
        r = web_search_tool("q", runtime=rt)
    expect = PHRASE_SEARCH_TIMEOUT if EXPECTED_KIND[status] == "timeout" else "联网检索失败"
    assert (r.ok, r.content) == (False, expect)
    for forbidden in (str(status), "double", "placeholder", KEY, "Bearer"):
        assert forbidden not in r.content
    assert len(tr.requests) == 1 and [e.action for e in audit.entries] == ["web.search"]


def test_TC_UNIT_R28_222_per_turn_call_limit_5_with_eight_calls_provider_receives_at_most_five_and_429_still_counts():
    """AC-016-09：全局与本项目上限均为每轮 5 次，一轮内连续 8 次 web_search ⇒ 替身收到的请求数 ≤5，第 6~8 次不出站（“已达本轮联网上限”）；
    即使每次都是 429（失败）也计入上限、且不重试。成功轮作为正例。"""
    p, tr = _prov([ok_results(HITS3)] * 8)
    rt = _rt(p)
    with bind_web_turn(_turn()):
        res = [web_search_tool(f"q{i}", runtime=rt) for i in range(8)]
    assert len(tr.requests) == 5
    assert [r.ok for r in res] == [True] * 5 + [False] * 3 and all(r.content == PHRASE_BUDGET for r in res[5:])
    p2, tr2 = _prov([error_reply(429)] * 8)
    with bind_web_turn(_turn()):
        res2 = [web_search_tool(f"q{i}", runtime=_rt(p2)) for i in range(8)]
    assert len(tr2.requests) == 5 and [r.content for r in res2[5:]] == [PHRASE_BUDGET] * 3


# --------------------------------------------------------------------------- #
# 真实传输（UrllibPostTransport）：以打桩 opener 验证，不触网（AC-014-06）
# --------------------------------------------------------------------------- #


class _Resp:
    def __init__(self, status=200, chunks=(b'{"results": []}',)):
        self.status = status
        self._chunks = list(chunks)

    def read(self, n=-1):
        return self._chunks.pop(0) if self._chunks else b""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _post(tr, **over):
    kw = dict(headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, body=b"{}", timeout_s=2.0, max_reply_bytes=1024)
    kw.update(over)
    return tr.post_json(DOC_SEARCH_URL, **kw)


def test_TC_UNIT_R28_223_urllib_transport_builds_post_with_documented_headers_and_returns_status_and_body(monkeypatch):
    """资料 §端点与鉴权：真实传输构造 POST 请求，头含 Authorization Bearer 与 Content-Type JSON；打桩 opener 不触网；200 ⇒ HttpReply(200, 正文)。"""
    tr = UrllibPostTransport()
    seen = {}

    def fake_open(req, timeout=None):
        seen.update(method=req.get_method(), url=req.full_url, headers={k.lower(): v for k, v in req.header_items()},
                    data=req.data, timeout=timeout)
        return _Resp(200, [b'{"results"', b': []}'])

    monkeypatch.setattr(tr._opener, "open", fake_open)
    rep = _post(tr, body=b'{"query":"q"}')
    assert (rep.status, rep.body, rep.oversize) == (200, b'{"results": []}', False)
    assert seen["method"] == "POST" and seen["url"] == DOC_SEARCH_URL and seen["data"] == b'{"query":"q"}'
    assert seen["headers"]["authorization"] == f"Bearer {KEY}" and seen["headers"]["content-type"] == "application/json"
    assert seen["timeout"] == 2.0


@pytest.mark.parametrize("code", [400, 401, 402, 403, 404, 408, 413, 429, 500, 504, 302])
def test_TC_UNIT_R28_224_urllib_transport_returns_http_error_status_without_reading_error_body(monkeypatch, code):
    """设计：任何非 2xx 只取状态码、不读取错误体（3xx 不跟随）；HTTPError 的 fp 不被 read。"""
    tr = UrllibPostTransport()

    class _Fp(io.BytesIO):
        def read(self, *a, **k):  # pragma: no cover - 被调用即失败
            raise AssertionError("错误体不应被读取")

    def fake_open(req, timeout=None):
        raise urllib.error.HTTPError(DOC_SEARCH_URL, code, "msg", {}, _Fp(b'{"error": {"message": "SECRET"}}'))  # type: ignore[arg-type]

    monkeypatch.setattr(tr._opener, "open", fake_open)
    rep = _post(tr)
    assert (rep.status, rep.body) == (code, b"")


def test_TC_UNIT_R28_225_urllib_transport_maps_network_errors_to_timeout_or_unreachable_and_rejects_non_https(monkeypatch):
    """设计：超时（TimeoutError / URLError(TimeoutError)）⇒ timeout；DNS / 连接 / TLS / HTTP 层异常 ⇒ unreachable；非 https 地址 ⇒ unreachable 且不调用 opener。"""
    tr = UrllibPostTransport()
    calls = {"n": 0}
    cases = [
        (TimeoutError("t"), "timeout"),
        (urllib.error.URLError(TimeoutError("t")), "timeout"),
        (urllib.error.URLError("connection refused"), "unreachable"),
        (ConnectionResetError("reset"), "unreachable"),
        (ssl.SSLError("bad cert"), "unreachable"),
        (http.client.RemoteDisconnected("closed"), "unreachable"),
    ]
    for exc, kind in cases:
        def fake_open(req, timeout=None, _e=exc):
            calls["n"] += 1
            raise _e

        monkeypatch.setattr(tr._opener, "open", fake_open)
        with pytest.raises(TransportError) as ei:
            _post(tr)
        assert ei.value.kind == kind, exc
    n_before = calls["n"]
    with pytest.raises(TransportError) as ei2:
        tr.post_json("http://api.deepseek.com/v1/tools/search", headers={}, body=b"{}", timeout_s=1.0, max_reply_bytes=10)
    assert ei2.value.kind == "unreachable" and calls["n"] == n_before


def test_TC_UNIT_R28_226_urllib_transport_flags_oversize_and_never_follows_redirects():
    """A-14 / A-18：响应体超过上限 ⇒ oversize=True、正文丢弃；opener 不含重定向处理器（3xx 不转发 Authorization 头）。"""
    tr = UrllibPostTransport()
    handlers = {type(h).__name__ for h in tr._opener.handlers}
    assert "HTTPRedirectHandler" not in handlers and {"HTTPSHandler", "HTTPDefaultErrorHandler"} <= handlers
    tr._opener.open = lambda req, timeout=None: _Resp(200, [b"x" * 600, b"y" * 600])  # type: ignore[method-assign]
    rep = _post(tr, max_reply_bytes=1024)
    assert rep.oversize is True and rep.body == b""
    tr._opener.open = lambda req, timeout=None: _Resp(200, [b"x" * 600])  # type: ignore[method-assign]
    ok = _post(tr, max_reply_bytes=1024)
    assert ok.oversize is False and ok.body == b"x" * 600


# --------------------------------------------------------------------------- #
# 提供方工厂：离线 / 生产闸（AC-020-01 / 020-03）与 Key 缺失降级（AC-018-05）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_227_factory_rejects_fake_in_production_by_key_name_only_and_never_constructs_fake(monkeypatch):
    """AC-020-01：非离线 + provider=fake ⇒ ConfigError(key=IB_WEB_SEARCH_PROVIDER)，错误信息不含所配值 “fake”；FakeSearchProvider 不被构造，
    假数据送达次数 = 0（不静默回退）。对照 AC-020-03：离线 + fake ⇒ 可用。"""
    import ib.webtools.search as search_mod

    built = {"n": 0}
    real = search_mod.FakeSearchProvider

    class _Counting(real):  # type: ignore[misc, valid-type]
        def __init__(self, *a, **k):
            built["n"] += 1
            super().__init__(*a, **k)

    monkeypatch.setattr(search_mod, "FakeSearchProvider", _Counting)
    with pytest.raises(ConfigError) as ei:
        build_search_provider(WebSearchSettings("fake"), KEY, offline=False)
    assert ei.value.key == "IB_WEB_SEARCH_PROVIDER" and "fake" not in str(ei.value).lower() and KEY not in str(ei.value)
    assert built["n"] == 0
    for variant in (" FAKE ", "Fake"):
        with pytest.raises(ConfigError):
            build_search_provider(WebSearchSettings(variant), KEY, offline=False)
    assert built["n"] == 0
    prov = build_search_provider(WebSearchSettings("fake"), None, offline=True)  # AC-020-03 正例
    assert isinstance(prov, _Counting) and built["n"] == 1
    out = prov.search(_q("q"))
    assert out.error is None


def test_TC_UNIT_R28_228_factory_matrix_none_deepseek_offline_online_and_missing_key_degrades_to_null_with_warning(monkeypatch, logs):
    """AC-020-03 / AC-018-05 / 缺省行为：none ⇒ Null（与上一轮一致，remote=False）；deepseek+离线 ⇒ Fake 且不构造真实传输；
    deepseek+在线+Key ⇒ DeepSeekSearchProvider（注入传输）；deepseek+在线+无 Key（None/空/空白）⇒ Null + WARNING，日志不含任何 Key；
    未登记标识 ⇒ ConfigError(键名)；内置标识不可登记。"""
    built = {"transport": 0}

    class _CountingTransport:
        def __init__(self):
            built["transport"] += 1

    monkeypatch.setattr(ds, "UrllibPostTransport", _CountingTransport)
    n = build_search_provider(WebSearchSettings("none"), KEY, offline=False)
    assert isinstance(n, NullSearchProvider) and n.describe_egress().remote is False
    assert n.search(_q("q")).error == "not_configured"
    off = build_search_provider(WebSearchSettings("deepseek"), KEY, offline=True)
    assert isinstance(off, FakeSearchProvider) and built["transport"] == 0
    tr = SpyTransport([ok_results(HITS3)])
    on = build_search_provider(WebSearchSettings("deepseek"), f"  {KEY}  ", offline=False, transport=tr)
    assert isinstance(on, DeepSeekSearchProvider) and built["transport"] == 0
    assert on.search(_q("q")).error is None and tr.raw[0]["headers"]["Authorization"] == f"Bearer {KEY}"  # 空白被裁剪
    for missing in (None, "", "   "):
        d = build_search_provider(WebSearchSettings("deepseek"), missing, offline=False, transport=tr)
        assert isinstance(d, NullSearchProvider)
    assert any("not_configured" in ln for ln in logs.lines) and all(KEY not in ln for ln in logs.lines)
    with pytest.raises(ConfigError) as ei:
        build_search_provider(WebSearchSettings("nosuchvendor"), KEY, offline=False)
    assert ei.value.key == "IB_WEB_SEARCH_PROVIDER" and KEY not in str(ei.value)
    for builtin in ("none", "deepseek", "fake"):
        with pytest.raises(ValueError):
            register_search_provider(builtin, lambda s, k: NullSearchProvider())


def _validate(**over):
    base = {"vectorstore": {"backend": "memory"}, "embedding": {"backend": "fake"}, "llm": {"backend": "fake"}}
    base.update(over)
    return ConfigurationResolver(DictConfigurationSource(base)).validate(env={})


def test_TC_UNIT_R28_229_config_validation_rejects_fake_in_production_and_reports_key_name_only():
    """AC-020-01：非离线配置里 web_search_provider=fake ⇒ 校验失败（启动失败的来源），仅含键名 IB_WEB_SEARCH_PROVIDER，所配值字符串出现 0 次；
    任意其他非法取值同样被拒；离线模式下 fake 不报错（AC-020-03）；none / deepseek(+DeepSeek 主机) 通过。"""
    errs = _validate(offline_mode=False, web_search_provider="fake")
    hit = [e for e in errs if getattr(e, "key", "") == "IB_WEB_SEARCH_PROVIDER"]
    assert len(hit) == 1 and "fake" not in str(hit[0]).lower()
    bogus = _validate(offline_mode=False, web_search_provider="zzz-unique-bogus")
    assert [e.key for e in bogus if e.key == "IB_WEB_SEARCH_PROVIDER"] and all("zzz-unique-bogus" not in str(e) for e in bogus)
    assert _validate(offline_mode=True, web_search_provider="fake") == []
    assert _validate(offline_mode=False, web_search_provider="none") == []
    ok = _validate(offline_mode=False, web_search_provider="deepseek", llm={"backend": "fake", "base_url": "https://api.deepseek.com/v1"})
    assert ok == []


def test_TC_UNIT_R28_230_deepseek_provider_requires_deepseek_llm_host_failure_names_key_only_not_the_host_value():
    """AC-018-05 / IFC-R28-032：LLM base_url 主机非 api.deepseek.com 时 provider=deepseek 启动校验失败，错误只报键名、不含所配主机；
    可疑变体（子域、前缀、userinfo 伪装、空值、非法 URL）一律失败；正确主机（含端口 / 大小写）通过。"""
    evil_hosts = ["https://api.deepseek.com.evil.example/v1", "https://evil-api.deepseek.com/v1", "https://api.deepseek.com@evil.example/v1",
                  "https://other.example.org/v1", "", "not a url", "https://[::1"]
    for u in evil_hosts:
        errs = _validate(offline_mode=False, web_search_provider="deepseek", llm={"backend": "fake", "base_url": u})
        hit = [e for e in errs if e.key == "IB_WEB_SEARCH_PROVIDER"]
        assert len(hit) == 1, u
        for frag in ("evil", "other.example", "not a url"):
            assert frag not in str(hit[0])
    for u in ("https://API.DeepSeek.com/v1", "https://api.deepseek.com:443/v1"):
        assert _validate(offline_mode=False, web_search_provider="deepseek", llm={"backend": "fake", "base_url": u}) == []


# --------------------------------------------------------------------------- #
# Key 解析（与 LLM 同源）与运行时装配（AC-018-05）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R28_231_resolve_llm_api_key_prefers_store_then_env_and_returns_none_when_both_empty(monkeypatch):
    """AC-018-05 / IFC-R28-031：与 LLM 同源——台账（llm_key 存储）优先；其为空 / 空白时回退 IB_LLM_API_KEY；两者皆空 ⇒ None；结果裁剪空白。"""
    cfg = SimpleNamespace(llm=SimpleNamespace(api_key_env="IB_LLM_API_KEY"))
    monkeypatch.setenv("IB_LLM_API_KEY", "ENV-KEY-R28")
    assert resolve_llm_api_key(cfg, " DB-KEY-R28 ") == "DB-KEY-R28"
    for blank in (None, "", "   "):
        assert resolve_llm_api_key(cfg, blank) == "ENV-KEY-R28"
    monkeypatch.delenv("IB_LLM_API_KEY")
    assert resolve_llm_api_key(cfg, None) is None and resolve_llm_api_key(cfg, "  ") is None
    assert resolve_llm_api_key(cfg, "DB-ONLY") == "DB-ONLY"


def test_TC_UNIT_R28_232_web_runtime_assembly_uses_resolved_llm_key_in_authorization_header_and_missing_key_degrades(monkeypatch):
    """AC-018-05：组合根 build_web_runtime（非离线、deepseek）——Key 取自 resolve_llm_api_key（台账优先、环境回退），只出现在请求头；
    删除 Key（台账与环境皆空）⇒ 联网以 not_configured 降级（工具层固定短语“联网服务未配置”），无新增凭据配置项。"""
    from ibweb.composition import build_web_runtime

    cfg = SimpleNamespace(web_search_provider="deepseek", offline_mode=False, web_fetch_enabled=False,
                          llm=SimpleNamespace(api_key_env="IB_LLM_API_KEY"))
    holder = {}

    class _Factory:
        def __new__(cls):
            holder["tr"] = SpyTransport([ok_results(HITS3)] * 4)
            return holder["tr"]

    monkeypatch.setattr(ds, "UrllibPostTransport", _Factory)
    monkeypatch.delenv("IB_LLM_API_KEY", raising=False)
    # 1) 台账 Key
    rt = build_web_runtime(cfg, audit=_Audit(), governance=None, api_key=resolve_llm_api_key(cfg, KEY))
    assert isinstance(rt.provider, DeepSeekSearchProvider)
    assert rt.provider.search(_q("q")).error is None
    assert holder["tr"].raw[0]["headers"]["Authorization"] == f"Bearer {KEY}"
    assert [d.endpoint_host for d in rt.egress_descriptors()] == [DOC_HOST]
    # 2) 仅环境回退
    monkeypatch.setenv("IB_LLM_API_KEY", KEY)
    rt2 = build_web_runtime(cfg, audit=_Audit(), governance=None, api_key=resolve_llm_api_key(cfg, None))
    assert isinstance(rt2.provider, DeepSeekSearchProvider) and rt2.provider.search(_q("q")).error is None
    assert holder["tr"].raw[0]["headers"]["Authorization"] == f"Bearer {KEY}"
    # 3) 删除 Key ⇒ 降级
    monkeypatch.delenv("IB_LLM_API_KEY")
    rt3 = build_web_runtime(cfg, audit=_Audit(), governance=None, api_key=resolve_llm_api_key(cfg, None))
    assert isinstance(rt3.provider, NullSearchProvider) and rt3.egress_descriptors() == ()
    with bind_web_turn(_turn()):
        r = web_search_tool("q", runtime=rt3)
    assert (r.ok, r.content) == (False, "联网服务未配置")
    # 离线配置：永不构造真实传输，且 deepseek 切到 Fake
    cfg_off = SimpleNamespace(web_search_provider="deepseek", offline_mode=True, web_fetch_enabled=False,
                              llm=SimpleNamespace(api_key_env="IB_LLM_API_KEY"))
    holder.clear()
    rt4 = build_web_runtime(cfg_off, audit=_Audit(), governance=None, api_key=KEY)
    assert isinstance(rt4.provider, FakeSearchProvider) and "tr" not in holder


def test_TC_UNIT_R28_233_source_discipline_endpoint_constant_no_unused_outbound_field_names_bearer_only_in_adapter():
    """REQ-NFUNC-005 / 006 源码纪律：适配器源码不含未使用的外发字段名（ori_question / localization）；Bearer 头只在 deepseek.py 构造；
    端点常量等于资料所载 URL；search.py 仍无网络导入（selfcheck 同口径，此处为单元级守卫）。"""
    import pathlib

    root = pathlib.Path(ds.__file__).parent
    text = (root / "deepseek.py").read_text(encoding="utf-8")
    assert "ori_question" not in text and "localization" not in text and "Bearer" in text
    for path in sorted(root.glob("*.py")):
        if path.name not in ("deepseek.py", "deepseek_double.py"):
            assert "Bearer" not in path.read_text(encoding="utf-8"), path.name
    assert ds.DEEPSEEK_SEARCH_URL == DOC_SEARCH_URL and ds.DEEPSEEK_API_HOST == DOC_HOST
    assert (ds.DEEPSEEK_QUERY_MAX_CHARS, ds.DEEPSEEK_COUNT_MAX) == (128, 50)
    import re

    dbl = (root / "deepseek_double.py").read_text(encoding="utf-8")
    imports = " | ".join(ln.strip() for ln in dbl.splitlines() if re.match(r"\s*(import|from)\s", ln))
    for banned in ("socket", "ssl", "urllib", "http.client", "requests", "httpx"):
        assert banned not in imports, (banned, imports)  # 替身无网络导入


def test_TC_UNIT_R28_234_apology_text_is_single_fixed_chinese_constant_without_ascii_words_digits_or_internal_names():
    """AC-001-04：致歉文本是唯一的固定中文常量（不随提问语言变化）：含中文、英文单词 0 个、数字（状态码样式）0 个、内部名（agent / 工具 / 路由）0 个；
    `advisor_apology_text()` 恒返回该常量（逐字相同）。"""
    from ib.advisor import ADVISOR_APOLOGY_TEXT, advisor_apology_text

    t = ADVISOR_APOLOGY_TEXT
    assert isinstance(t, str) and advisor_apology_text() == t == advisor_apology_text()
    assert re.search(r"[一-鿿]", t) and "抱歉" in t
    assert not re.search(r"[A-Za-z]", t) and not re.search(r"\d", t)
    for w in ("kb-agent", "advisor", "web_search", "web_fetch", "search_knowledge", "路由", "状态码", "异常"):
        assert w not in t
