"""[REV-29 / GROUP_D] 单元：MCP 线协议（纯函数）——报文构造、SSE、x-mcp-header、失败分类、公网明文 http 字符串判定。

分层：unit。溯源：US-002 / 008 / 019 / 013。
"""

from __future__ import annotations

import json

import pytest

from ib.core.types import MCP_LEGACY_VERSION, MCP_MODERN_VERSION
from ib.mcp.wire import (
    ProtocolError,
    ResponseTooLarge,
    build_call,
    build_discover,
    build_initialize,
    build_list,
    build_listen,
    classify_http_failure,
    encode_header_value,
    iter_sse_events,
    parse_jsonrpc_response,
    plain_http_allowed,
    x_mcp_headers,
)

SCHEMA = {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}


def test_TC_UNIT_R29_100_modern_discover_headers_and_body_AC_002_01():
    h, b = build_discover("modern", 7)
    msg = json.loads(b)
    assert msg["method"] == "server/discover" and msg["id"] == 7
    assert h["MCP-Protocol-Version"] == MCP_MODERN_VERSION and h["Mcp-Method"] == "server/discover"


def test_TC_UNIT_R29_101_legacy_initialize_has_no_version_header_and_asks_legacy_version_AC_002_01():
    h, b = build_initialize(1)
    assert "MCP-Protocol-Version" not in h and json.loads(b)["params"]["protocolVersion"] == MCP_LEGACY_VERSION


def test_TC_UNIT_R29_102_call_modern_mirrors_name_and_x_mcp_header_AC_019_01():
    schema = {"type": "object", "properties": {"region": {"type": "string", "x-mcp-header": "Region"}, "q": {"type": "string"}}}
    h, b = build_call("modern", "search", {"region": "华东", "q": "x"}, 3, session_id=None, input_schema=schema)
    assert h["Mcp-Method"] == "tools/call" and h["Mcp-Name"] == "search"
    assert h["Mcp-Param-Region"].startswith("=?base64?")  # 非 ASCII 走哨兵编码
    assert json.loads(b)["params"]["arguments"] == {"region": "华东", "q": "x"}


def test_TC_UNIT_R29_103_call_legacy_carries_session_and_no_mirror_headers():
    h, _ = build_call("legacy", "search", {"q": "x"}, 3, session_id="sess-1", input_schema=SCHEMA)
    assert h["MCP-Session-Id"] == "sess-1" and "Mcp-Method" not in h


@pytest.mark.parametrize("name", ["", "x" * 129])
def test_TC_UNIT_R29_104_call_rejects_bad_remote_name(name):
    with pytest.raises(ValueError):
        build_call("modern", name, {}, 1, session_id=None, input_schema=SCHEMA)


def test_TC_UNIT_R29_105_header_injection_rejected_AC_008_01():
    """头值含 CR/LF ⇒ 构造即拒绝（失败分支）；正常值通过（正例）。"""
    with pytest.raises(ValueError):
        build_call("legacy", "t", {}, 1, session_id="a\r\nX-Evil: 1", input_schema=SCHEMA)
    assert build_call("legacy", "t", {}, 1, session_id="ok-1", input_schema=SCHEMA)


def test_TC_UNIT_R29_106_encode_header_value_round_trip_rules():
    assert encode_header_value("abc") == "abc"
    assert encode_header_value(" lead").startswith("=?base64?") and encode_header_value("中").startswith("=?base64?")
    assert encode_header_value("=?base64?x?=").startswith("=?base64?")


def test_TC_UNIT_R29_107_x_mcp_headers_bool_number_and_skips_missing():
    schema = {"type": "object", "properties": {"a": {"x-mcp-header": "A"}, "b": {"x-mcp-header": "B"}, "c": {"x-mcp-header": "C"}}}
    assert x_mcp_headers(schema, {"a": True, "b": 3}) == {"Mcp-Param-A": "true", "Mcp-Param-B": "3"}


def test_TC_UNIT_R29_108_list_and_listen_builders():
    h, b = build_list("modern", "cur-1", 5, session_id=None)
    assert json.loads(b)["params"]["cursor"] == "cur-1" and h["Mcp-Method"] == "tools/list"
    lh, lb = build_listen(9)
    assert json.loads(lb)["method"] == "subscriptions/listen" and json.loads(lb)["params"]["notifications"]["toolsListChanged"] is True


def test_TC_UNIT_R29_110_sse_events_comments_ignored_and_split_chunks():
    chunks = [b": keep\n\nda", b'ta: {"a":1}\n\n', b"data: x\ndata: y\n\n"]
    assert list(iter_sse_events(chunks, max_bytes=1000)) == [b'{"a":1}', b"x\ny"]


def test_TC_UNIT_R29_111_sse_over_limit_raises_AC_019_06():
    with pytest.raises(ResponseTooLarge):
        list(iter_sse_events([b"data: " + b"x" * 200 + b"\n\n"], max_bytes=100))


def test_TC_UNIT_R29_112_parse_jsonrpc_outcomes_AC_019_04():
    ok = parse_jsonrpc_response(b'{"jsonrpc":"2.0","id":1,"result":{"content":[]}}', expect_id=1)
    assert ok.result is not None and ok.result_type == "complete"
    er = parse_jsonrpc_response(b'{"jsonrpc":"2.0","id":1,"error":{"code":-32602,"message":"m"}}', expect_id=1)
    assert er.error is not None and er.error["code"] == -32602
    for bad in (b"not json", b'{"jsonrpc":"1.0","id":1}', b'{"jsonrpc":"2.0","id":2,"result":{}}',
                b'{"jsonrpc":"2.0","id":1,"result":{"resultType":"mystery"}}', b'{"jsonrpc":"2.0","id":true,"result":{}}'):
        with pytest.raises(ProtocolError):
            parse_jsonrpc_response(bad, expect_id=1)
    it = parse_jsonrpc_response(b'{"jsonrpc":"2.0","id":1,"result":{"resultType":"input_required"}}', expect_id=1)
    assert it.result_type == "input_required"  # AC-019-07 的线协议侧


def test_TC_UNIT_R29_113_http_failure_classification_AC_002_02():
    assert classify_http_failure(401, b"").kind == "auth_failed" and classify_http_failure(403, b"").kind == "auth_failed"
    assert classify_http_failure(302, b"").kind == "address_blocked"  # AC-008-03
    assert classify_http_failure(503, b"").kind == "unreachable" and classify_http_failure(429, b"").kind == "unreachable"
    body = json.dumps({"error": {"code": -32022, "message": "m", "data": {"supported": [MCP_LEGACY_VERSION]}}}).encode()
    f = classify_http_failure(400, body)
    assert f.kind == "modern_error" and f.supported == (MCP_LEGACY_VERSION,)
    assert classify_http_failure(400, b"junk").era_fallback is True  # 老服务端：尝试 legacy
    assert classify_http_failure(404, b"").era_fallback is True
    assert classify_http_failure(418, b"").kind == "protocol_error"


@pytest.mark.parametrize("url,allow,want", [
    ("https://crm.example.com/mcp", frozenset(), True),
    ("http://crm.example.com/mcp", frozenset(), False),                       # AC-008-05：公网明文
    ("http://10.0.0.8:9000/mcp", frozenset({("10.0.0.8", 9000)}), True),      # 名单内精确主机 + 端口
    ("http://10.0.0.8:9001/mcp", frozenset({("10.0.0.8", 9000)}), False),
    ("http://10.0.0.9:9000/mcp", frozenset({("10.0.0.8", 9000)}), False),
    ("http://127.0.0.1:9100/", frozenset({("127.0.0.1", 9100)}), True),
    ("ftp://crm.example.com/", frozenset(), False), ("file:///etc/passwd", frozenset(), False),
    ("javascript:alert(1)", frozenset(), False), ("HTTP://CRM.EXAMPLE.COM/", frozenset(), False),
    ("http://crm.example.com:80/", frozenset({("crm.example.com", 80)}), True),
    ("http://crm.example.com/", frozenset({("crm.example.com", 80)}), True),  # 缺省端口 80
    ("", frozenset(), False), ("http://[::1]:99999/", frozenset(), False),
])
def test_TC_UNIT_R29_114_plain_http_allowed_string_decision_before_dns_AC_008_05(url, allow, want):
    assert plain_http_allowed(url, allow) is want
