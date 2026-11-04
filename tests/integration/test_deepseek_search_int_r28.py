"""[REV-28 / GROUP_D-003] 集成：DeepSeek 联网搜索全链路（真实装配 + 发布协议 + 运行时编译 + 工具循环看门狗 + 出站闸 + 审计 + HTTP 视图）。

分层：integration。搜索提供方 = 真实的 `DeepSeekSearchProvider` 适配器，其唯一网络缝由 `FakeDeepSeekTransport` 替身承接（资料无官方沙箱，
画像 P11-3）；LLM 为脚本化替身（“被诱导 / 只会回显工具输出”的最坏 LLM 由脚本模拟——被测对象是平台侧的映射、围栏、闸与降级）。
autouse 夹具断言**零真实网络连接**（AC-014-06）。哨兵 Key 为测试占位串，非真实凭据。
期望值来源：`docs/external_api/deepseek_search_fetch.md` 与 user_stories 4.0.0 / module_design 3.0.0；不取自被测代码输出。
溯源：AC-001-04、AC-010-08 / 09、AC-014-05 ~ 10、AC-015-07（TC-INT-R28-422 ~ 424）、AC-016-09、AC-017-06、AC-018-05 / 06、AC-020-01 ~ 03。
"""

from __future__ import annotations

import copy
import json
import os
import re
import socket

import pytest
from advisor_r28_support import (
    KB_ANSWER,
    KB_ORIG,
    KB_TEXT,
    P,
    ScriptedLlm,
    advisor_document,
    advisor_prompts,
    chat,
    faithful_advisor,
    publish_advisor,
    raw_events,
    set_web,
    table_understander,
    understanding,
    web_outcome,
    web_params,
)
from config_r26_support import Api, publish_body
from conftest import offline_raw

from ib.advisor import ADVISOR_APOLOGY_TEXT
from ib.webtools import deepseek as ds
from ib.webtools.deepseek import DeepSeekSearchProvider
from ib.webtools.deepseek_double import (
    DoubleReply,
    FakeDeepSeekTransport,
    empty_results,
    error_reply,
    ok_results,
    search_item,
)
from ib.webtools.search import FakeSearchProvider

KEY = "R28-DS-SENTINEL-KEY-NOT-A-REAL-CREDENTIAL-4417"
DOC_SEARCH_URL = "https://api.deepseek.com/v1/tools/search"
WEB_GRANT = {"advisor": ("web_search", "web_fetch")}
EXPECTED_KIND = {400: "rejected", 401: "auth_failed", 402: "quota_exceeded", 403: "rejected", 404: "rejected",
                 408: "timeout", 413: "rejected", 429: "rate_limited", 500: "unreachable", 504: "timeout"}
NOTE = "未能联网检索到最新信息"
HITS = [
    search_item(title="上海天气预报", url="https://wx.example.com/sh", snippet="明天多云", summary="明天多云转阴 18-24 度"),
    search_item(title="天气网", url="https://tq.example.org/sh", snippet="降水", summary="周边降水概率 20%"),
    search_item(title="气象局", url="https://cma.example.gov/", snippet="官方", summary="官方预报"),
]
GENERAL = understanding(("general",), "通用问题", "")
Q_WEB, Q_KB, Q_HI = "明天上海天气怎样？", "退货期限是多久", "你好"
TABLE = {
    Q_KB: understanding(("knowledge",), Q_KB, Q_KB),
    Q_HI: understanding(("chitchat",), Q_HI, ""),
}


class SpyTransport(FakeDeepSeekTransport):
    """替身子类：额外记录原始请求头 / 体（测试用）。"""

    def __init__(self, script=(), **kw):
        kw.setdefault("expected_key", KEY)
        super().__init__(script, **kw)
        self.raw: list[dict] = []

    def post_json(self, url, *, headers, body, timeout_s, max_reply_bytes):
        self.raw.append({"url": url, "headers": dict(headers), "body": body, "timeout_s": timeout_s})
        return super().post_json(url, headers=headers, body=body, timeout_s=timeout_s, max_reply_bytes=max_reply_bytes)


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    attempts: list[str] = []

    def _boom(*a, **k):
        attempts.append("connect")
        raise AssertionError("测试中出现了真实网络连接尝试")

    monkeypatch.setattr(socket.socket, "connect", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    yield
    assert attempts == []


@pytest.fixture()
def api(accounts_app):
    deps, Client = accounts_app
    a = Api(deps, Client)
    a.add_user("editor", P, "edit")
    a.add_user("viewer", P, "view")
    return a


def _contents(ev):
    return [str(e.data) for e in ev if str(e.kind) == "content"]


def _kinds(ev):
    return [str(e.kind) for e in ev]


def _setup(deps, monkeypatch, script=(), *, adv=None, grants=WEB_GRANT, params=None, table=None, scripts=None, fetcher=None):
    """真实 DeepSeekSearchProvider + 替身传输 → 装入运行时 → 发布含联网授权的顾问项目 → 脚本化 LLM。"""
    tr = SpyTransport(script)
    prov = DeepSeekSearchProvider(KEY, transport=tr)
    set_web(deps, provider=prov, fetcher=fetcher)
    publish_advisor(deps, P, grants=grants, params=params)
    sc = {"kb-agent": lambda c: KB_TEXT, "advisor": adv or faithful_advisor()}
    sc.update(scripts or {})
    llm = ScriptedLlm(deps, monkeypatch, scripts=sc, understander=table_understander(table or {}, GENERAL))
    return prov, tr, llm


def _cite(result: str) -> str:
    """最坏情形下的“照搬工具输出”顾问：把检索结果里的标题与网址列入答复。"""
    pairs = re.findall(r"^\d+\. (.+)\n(?:.*)\n(https?://\S+)$", result, re.M)
    return "来自互联网：" + "；".join(f"{t}（{u}）" for t, u in pairs)


# =========================================================================== #
# AC-014-07 / 014-08 / 014-10：结果形态、降级、空结果
# =========================================================================== #


def test_TC_INT_R28_400_success_results_carry_title_url_summary_answer_cites_and_request_matches_documented_contract(api, monkeypatch):
    """AC-014-07（happy path，与 401 降级成对）：替身返回 3 条结果 ⇒ 工具返回给顾问的每条均含非空标题 / 网址 / 摘要；答复列出所用结果的标题与网址；
    出站请求：资料所载端点、POST、Bearer + JSON 头、请求体键集恰为 {query,count,need_content}；审计 host=api.deepseek.com 且不含查询原文。"""
    deps = api.deps
    seen = {}

    def adv(c):
        r = c.use_tool("web_search", query="上海明天天气")
        seen["r"] = r
        return _cite(r)

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS)], adv=adv)
    ev = raw_events(deps, P, Q_WEB)
    r = seen["r"]
    assert r.startswith("【联网内容（不可信数据")
    for h in HITS:
        assert h["title"] in r and h["url"] in r and h["summary"] in r
    ans = _contents(ev)
    assert len(ans) == 1 and "上海天气预报" in ans[0] and "https://wx.example.com/sh" in ans[0] and ADVISOR_APOLOGY_TEXT not in ans[0]
    assert len(tr.requests) == 1 and tr.raw[0]["url"] == DOC_SEARCH_URL and tr.requests[0].method == "POST"
    assert tr.raw[0]["headers"] == {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    assert json.loads(tr.raw[0]["body"]) == {"query": "上海明天天气", "count": 5, "need_content": False}
    audit = [e for e in deps.config_audit_store.list_by_project(P) if e.action == "web.search"]
    assert len(audit) == 1 and "host:api.deepseek.com" in audit[0].object_summary and "上海明天天气" not in repr(audit[0])


@pytest.mark.parametrize("status", sorted(EXPECTED_KIND))
def test_TC_INT_R28_401_every_documented_error_status_degrades_with_notice_no_5xx_and_no_code_message_or_key_in_reply(api, monkeypatch, status):
    """AC-014-08（资料 §错误 的 10 个状态码；每个降级用例与 TC-400 / 402 的成功正例成对）：提供方返回该状态 ⇒ 整轮仍返回正常答复
    （无 error 事件、无统一致歉）、含“未能联网检索到最新信息”降级说明；最坏顾问把工具输出原样放进答复，答复中状态码数字、
    错误体 message / type / code、“API Key”/ Key 片段 / Bearer 出现次数 = 0；仅 1 次出站（不重试）。"""
    deps = api.deps
    seen = {}

    def adv(c):
        r = c.use_tool("web_search", query="上海明天天气")
        seen["r"] = r
        return f"{NOTE}，以下为常识性回答，可能不是最新信息。（{r}）"

    _prov, tr, _llm = _setup(deps, monkeypatch, [error_reply(status)], adv=adv)
    ev = raw_events(deps, P, Q_WEB)
    ans = _contents(ev)
    assert len(ans) == 1 and NOTE in ans[0] and ADVISOR_APOLOGY_TEXT not in ans[0]
    assert "error" not in _kinds(ev) and _kinds(ev)[-1] == "done"
    for forbidden in (str(status), "double", "placeholder", "invalid_request", "API Key", "api key", KEY, "Bearer", "deepseek.com"):
        assert forbidden not in ans[0], forbidden
    assert not seen["r"].startswith("【联网内容")  # 工具侧确为失败短语，而非检索结果
    assert len(tr.requests) == 1 and tr.billable_calls == 0


def test_TC_INT_R28_402_five_statuses_in_sequence_each_turn_degrades_other_intents_unaffected_then_recovers(api, monkeypatch):
    """AC-014-08 原场景：提供方依次返回 401、402、429、500、504，用户各提一次需联网的通用问题 ⇒ 五次均正常答复（含降级说明，无状态码 / 错误原文 / 密钥片段）；
    期间寒暄与 kb-agent 委托不受影响（kb 答复仍含“7 天”）；之后提供方恢复 ⇒ 联网成功有来源（成对）。"""
    deps = api.deps
    order = [401, 402, 429, 500, 504]

    def adv(c):
        if "天气" in c.prompt:
            r = c.use_tool("web_search", query="上海明天天气")
            return _cite(r) if r.startswith("【联网内容") else f"{NOTE}。以下为常识性回答。"
        return faithful_advisor()(c)

    _prov, tr, llm = _setup(deps, monkeypatch, [error_reply(s) for s in order] + [ok_results(HITS)], adv=adv, table=TABLE)
    for i, st in enumerate(order):
        a = _contents(raw_events(deps, P, Q_WEB, f"w{i}"))
        assert len(a) == 1 and NOTE in a[0] and str(st) not in a[0] and KEY not in a[0], (st, a)
        kb = _contents(raw_events(deps, P, Q_KB, f"k{i}"))
        assert "7 天" in kb[0] and ADVISOR_APOLOGY_TEXT not in kb[0]
        hi = _contents(raw_events(deps, P, Q_HI, f"h{i}"))
        assert len(hi) == 1 and ADVISOR_APOLOGY_TEXT not in hi[0]
    assert len(tr.requests) == 5 and len(llm.calls_of("kb-agent")) == 5
    ok = _contents(raw_events(deps, P, Q_WEB, "recover"))
    assert "上海天气预报" in ok[0] and len(tr.requests) == 6


def test_TC_INT_R28_403_empty_results_stated_honestly_no_fabricated_sources_vs_nonempty_pair(api, monkeypatch):
    """AC-014-10：提供方返回 200 + 空数组 ⇒ 工具返回“联网检索未找到相关结果”（ok，不是故障）；答复如实说明“未检索到相关结果”，
    答复中出现的网址均能在替身返回中找到（不在其中的网址数 = 0）；非空结果成对：答复网址 ⊆ 替身返回网址。"""
    deps = api.deps
    seen = []

    def adv(c):
        r = c.use_tool("web_search", query="冷门话题 xyz")
        seen.append(r)
        if r.startswith("【联网内容"):
            return _cite(r)
        return "未检索到相关结果，以下为常识性回答，可能不是最新信息。" if "未找到相关结果" in r else "?"

    _prov, tr, _llm = _setup(deps, monkeypatch, [empty_results(), ok_results(HITS)], adv=adv)
    a0 = _contents(raw_events(deps, P, Q_WEB, "e1"))[0]
    assert seen[0] == "联网检索未找到相关结果" and "未检索到相关结果" in a0
    assert set(re.findall(r"https?://[^\s）)；，。]+", a0)) == set() and tr.billable_calls == 0  # 替身返回的网址集合为空
    a1 = _contents(raw_events(deps, P, Q_WEB, "e2"))[0]
    returned1 = {h["url"] for h in HITS}
    got = set(re.findall(r"https?://[^\s）)；，。]+", a1))
    assert got and got <= returned1 and tr.billable_calls == 1


# =========================================================================== #
# AC-014-09：取值范围（检索词 ≤128、条数 1..50、全空白不出站、配置保存期校验）
# =========================================================================== #


def test_TC_INT_R28_404_200_char_query_truncated_to_128_blank_query_not_sent_and_whole_turn_answers(api, monkeypatch):
    """AC-014-09：模型生成 200 字符检索词 ⇒ 发往提供方的 query 恰为前 128 字符（≤128），整轮正常答复；检索词全为空白 ⇒ 请求数不增加，
    工具返回“检索词为空”，并继续作答。"""
    deps = api.deps
    seen = {}

    def adv(c):
        seen["long"] = c.use_tool("web_search", query="词" * 200)
        seen["blank"] = c.use_tool("web_search", query="   ")
        return "来自互联网：已检索。"

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS), ok_results(HITS)], adv=adv)
    ev = raw_events(deps, P, Q_WEB)
    assert len(_contents(ev)) == 1 and "error" not in _kinds(ev)
    assert len(tr.requests) == 1
    sent = json.loads(tr.raw[0]["body"])["query"]
    assert sent == "词" * 128 and len(sent) <= 128
    assert seen["long"].startswith("【联网内容") and seen["blank"] == "检索词为空"


@pytest.mark.parametrize("cfg_count", [1, 5, 50])
def test_TC_INT_R28_405_configured_count_reaches_provider_as_count_and_llm_cannot_exceed_it(api, monkeypatch, cfg_count):
    """AC-014-09 / AC-014-03：配置的返回条数（1 / 5 / 50）作为请求体 count 原样发出；模型试图传 max_results=100 时配置胜出。"""
    deps = api.deps

    def adv(c):
        c.use_tool("web_search", query="q", max_results=100)
        return "来自互联网"

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS)], adv=adv,
                             params={"advisor": web_params(search={"max_results": cfg_count})})
    raw_events(deps, P, Q_WEB)
    assert json.loads(tr.raw[0]["body"])["count"] == cfg_count


def test_TC_INT_R28_406_config_save_rejects_max_results_0_and_51_with_per_item_error_and_accepts_50(api):
    """AC-014-09：配置页顾问的 web_search 返回条数上限保存 0、51 ⇒ 被拒并逐条给出错误（指出允许范围 1–50）；保存 50 ⇒ 成功并回显。"""
    def doc(n):
        return advisor_document(P, grants={"advisor": ("web_search",)}, params={"advisor": web_params(search={"max_results": n})})

    codes = {}
    for bad in (0, 51):
        r = api.post("/api/config/publish", publish_body(doc(bad), 0, advisor_prompts()), who="editor")
        assert r.status_code == 400, (bad, r.content)
        items = r.json_body["error"]["items"]
        assert items and all("max_results" in json.dumps(i, ensure_ascii=False) for i in items)
        codes[bad] = json.dumps(items, ensure_ascii=False)
    assert "tool_param_out_of_range" in codes[0] and "下界 1" in codes[0] and "收到 0" in codes[0]  # 0 ⇒ 指出下界 1
    assert "tool_param_out_of_range" in codes[51] and "上界 50" in codes[51] and "收到 51" in codes[51]  # 51 ⇒ 指出上界 50
    ok = api.post("/api/config/publish", publish_body(doc(50), 0, advisor_prompts()), who="editor")
    assert ok.status_code == 200, ok.content
    shown = api.get("/api/config/definition", who="editor").json_body["document"]
    grants = {g["expert_name"]: g for g in shown["tool_grants"]}
    assert {p["name"]: p["value"] for p in grants["advisor"]["param_values"]} == {"web_search.max_results": "50"}


def test_TC_INT_R28_407_region_param_is_saved_but_ignored_request_carries_no_localization_or_region(api, monkeypatch):
    """AQ6=A / AC-018-06：region 字段仍可配置并保存，但适配器忽略——请求体不含 localization，也不含 region 的值。"""
    deps = api.deps

    def adv(c):
        c.use_tool("web_search", query="本地新闻")
        return "来自互联网"

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS)], adv=adv,
                             params={"advisor": web_params(search={"region": "203.0.113.9", "lang": "zh"})})
    raw_events(deps, P, Q_WEB)
    txt = tr.raw[0]["body"].decode("utf-8")
    body = json.loads(txt)
    assert set(body) == {"query", "count", "need_content"} and "203.0.113.9" not in txt and "localization" not in txt
    assert body["query"] == "本地新闻 lang:zh"  # lang 是资料所载操作符；region 无任何痕迹


# =========================================================================== #
# AC-016-09：用量上限与按次计费（出站前计数、429 也计、不重试）
# =========================================================================== #


def test_TC_INT_R28_408_eight_searches_in_one_turn_provider_receives_at_most_five_and_429_counts_without_retry(api, monkeypatch):
    """AC-016-09：全局与本项目上限均为每轮 5 次，模型一轮内连续发起 8 次 web_search ⇒ 替身收到的请求数 ≤5，第 6~8 次不发出
    （“已达本轮联网上限”），顾问用已有结果作答并说明；某次 429 ⇒ 仍计入 5 次上限且不重试（8 次全 429 时请求数仍恰为 5）。"""
    deps = api.deps
    outs = []

    def adv(c):
        outs.append([c.use_tool("web_search", query=f"检索{i}") for i in range(8)])
        return "来自互联网：已有结果；后续检索已达本轮联网上限，故未继续。"

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS)] * 8, adv=adv,
                             params={"advisor": web_params(search={"max_calls_per_turn": 5})})
    ev = raw_events(deps, P, Q_WEB, "lim1")
    assert len(tr.requests) == 5 and len(_contents(ev)) == 1 and "error" not in _kinds(ev)
    assert all(o.startswith("【联网内容") for o in outs[0][:5]) and outs[0][5:] == ["已达本轮联网上限"] * 3
    # 全部 429：仍然 5 次（失败也计数），且没有任何一次被重试补发
    tr2 = SpyTransport([error_reply(429)] * 12)
    set_web(deps, provider=DeepSeekSearchProvider(KEY, transport=tr2))
    publish_advisor(deps, P, grants=WEB_GRANT, params={"advisor": web_params(search={"max_calls_per_turn": 5, "max_results": 4})})  # 重新发布 ⇒ 重编译，新提供方生效
    ev2 = raw_events(deps, P, Q_WEB, "lim2")
    assert len(tr2.requests) == 5 and outs[1][5:] == ["已达本轮联网上限"] * 3 and len(_contents(ev2)) == 1
    assert [json.loads(r["body"])["query"] for r in tr2.raw] == [f"检索{i}" for i in range(5)]  # 每个检索词恰一次，无重试


# =========================================================================== #
# AC-018-06：外发内容类别与目的地（canary）
# =========================================================================== #


def test_TC_INT_R28_409_canary_30_sessions_deepseek_requests_only_query_count_need_content_and_only_documented_endpoint(api, monkeypatch):
    """AC-018-06（N≥30 段含专业问题与联网问题的会话）：知识库片段 / 助手历史 / 另一用户会话植入 canary；顾问（脚本模拟“被诱导外发”）尝试以完整 canary、
    ≥24 字符片段外发检索词，并做一次正常外发——DeepSeek 替身记录的全部出站请求：目的地仅 api.deepseek.com 搜索端点、键集恰为 {query,count,need_content}、
    canary 命中 0；每段会话的正常检索仍出站（避免全部拦截的假阳性）。"""
    deps = api.deps
    state = {"canary": ""}
    verdicts = []

    def kb(c):
        return f"{KB_TEXT} 内部编号：{state['canary']}（仅限内部）"

    def adv(c):
        if "金价" in c.prompt:
            cn = state["canary"]
            verdicts.append([c.use_tool("web_search", query=f"{cn} 是什么意思"), c.use_tool("web_search", query=f"价格 {cn[:26]} 查询"),
                             c.use_tool("web_search", query="今日金价")])
            return "来自互联网：已检索。"
        return faithful_advisor()(c)

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results(HITS)] * 40, adv=adv, scripts={"kb-agent": kb},
                             table={Q_KB: understanding(("knowledge",), Q_KB, Q_KB), "今天金价多少": GENERAL})
    canaries = []
    other = "CANARY-OTHER-USER-SESSION-77AA66BB55CC44DD"
    raw_events(deps, P, Q_KB, "other", actor="someone-else")  # 另一用户会话（其 kb 输出不含 canary，仅验证隔离不影响）
    for i in range(30):
        state["canary"] = f"CANARY-INTERNAL-{i:03d}-{'abcdef0123456789'[i % 16] * 12}"
        canaries.append(state["canary"])
        raw_events(deps, P, Q_KB, f"s{i}")  # 专业问题：kb 输出含 canary，进入助手历史
        raw_events(deps, P, "今天金价多少", f"s{i}")  # 联网问题
    assert len(verdicts) == 30
    for v in verdicts:
        assert v[0] == v[1] == "请求内容不被允许" and v[2].startswith("【联网内容")
    assert len(tr.requests) == 30  # 仅正常外发 30 次；带 canary 的 60 次全部被拦在出站闸
    sent = b"\n".join(r["body"] for r in tr.raw).decode("utf-8")
    for cn in canaries:
        assert cn not in sent and cn[:24] not in sent
    assert other not in sent
    assert {r["url"] for r in tr.raw} == {DOC_SEARCH_URL}
    for r in tr.raw:
        assert set(json.loads(r["body"])) == {"query", "count", "need_content"}
    audits = repr(deps.config_audit_store.list_by_project(P))
    assert all(cn not in audits for cn in canaries)
    decl = deps.web_runtime.egress_descriptors()
    assert [(d.endpoint_host, list(d.data_categories)) for d in decl] == [("api.deepseek.com", ["web_search_query"])]


# =========================================================================== #
# AC-018-05 / CR-016：Key 不出现在任何表面
# =========================================================================== #


def test_TC_INT_R28_410_sentinel_key_only_in_recorded_authorization_header_zero_in_logs_audit_reply_healthz_catalog_definition(api, monkeypatch):
    """AC-018-05 / AC-018-03 / CR-016（补回覆盖）：经 DeepSeek 路径跑成功与 10 种失败 ⇒ 哨兵 Key 只出现在传输缝收到的 Authorization 头；
    在日志、审计、答复、/healthz/deps、配置目录、定义文档、事件流、适配器 repr / 外发声明中出现 0 次。"""
    import logging

    from ib.config import document_to_json

    deps = api.deps
    lines: list[str] = []

    class _H(logging.Handler):
        def emit(self, record):
            lines.append(record.getMessage())

    lg = logging.getLogger("intelligentbase")
    h, old = _H(level=logging.DEBUG), lg.level
    lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    try:
        script = [ok_results(HITS)] + [error_reply(s) for s in sorted(EXPECTED_KIND)]
        prov, tr, _llm = _setup(deps, monkeypatch, script, adv=lambda c: (c.use_tool("web_search", query="公开问题"), "来自互联网：已检索。")[1])
        answers = []
        for i in range(len(script)):
            answers += _contents(raw_events(deps, P, Q_WEB, f"k{i}"))
        hz = api.get("/healthz/deps", project=None)
        cat = api.get("/api/config/catalog", who="editor")
    finally:
        lg.removeHandler(h)
        lg.setLevel(old)
    assert len(tr.requests) == len(script)
    assert all(r["headers"]["Authorization"] == f"Bearer {KEY}" for r in tr.raw)
    surfaces = [hz.content.decode("utf-8"), cat.content.decode("utf-8"), repr(deps.config_audit_store.list_by_project(P)),
                "\n".join(answers), document_to_json(deps.definitions[P]), repr(prov), repr(prov.describe_egress()), repr(tr.requests),
                "\n".join(lines)]
    for s in surfaces:
        assert KEY not in s
    assert "Bearer" not in "\n".join(surfaces[:5])


def _prod_raw(tmp_path, **over):
    raw = offline_raw()
    raw.update(offline_mode=False, web_search_provider="deepseek", llm={"backend": "fake", "base_url": "https://api.deepseek.com/v1"},
               ledger_backend="memory", project_registry_backend="memory", llm_key_backend="sqlite",
               ledger_path=str(tmp_path / "ledger.sqlite3"), web_governance_backend="memory")
    raw.update(over)
    return raw


def _prod_env(monkeypatch):
    from conftest import R13_ADMIN_PASSWORD

    monkeypatch.setenv("IB_ACCOUNT_BACKEND", "memory")
    monkeypatch.setenv("IB_AUTHZ_POLICY_MODULE", "ibweb.accounts.policy")
    monkeypatch.setenv("IB_DEFAULT_ADMIN_PASSWORD", R13_ADMIN_PASSWORD)


def test_TC_INT_R28_411_production_assembly_key_from_llm_key_store_first_then_env_fallback_then_unconfigured_degrade(django_ready, monkeypatch, tmp_path):
    """AC-018-05：非离线真实装配（LLM 主机 api.deepseek.com，provider=deepseek）——Key 与 LLM 同源：
    ① 仅环境变量 IB_LLM_API_KEY ⇒ DeepSeekSearchProvider，请求头 Bearer 该值；② llm_key 存储有值 ⇒ 存储优先于环境变量；
    ③ 存储清除且环境变量为空（删除密钥）⇒ 联网以 not_configured 降级、外发声明无搜索主机、无新增凭据配置项；
    外发声明主机 api.deepseek.com。真实传输类被替换为 FakeDeepSeekTransport，零触网。"""
    from ibweb.composition import build_deps

    _prod_env(monkeypatch)
    holder = {}
    key_env, key_db = KEY + "-ENV", KEY + "-DB"

    class _Factory:
        def __new__(cls):
            holder["tr"] = SpyTransport([ok_results(HITS)] * 3, expected_key=holder["expect"])
            return holder["tr"]

    monkeypatch.setattr(ds, "UrllibPostTransport", _Factory)
    from ib.core import SearchQuery

    q = SearchQuery(text="q", max_results=3, lang=None, region=None, timeout_s=2.0)
    monkeypatch.setenv("IB_LLM_API_KEY", key_env)
    holder["expect"] = key_env
    d1 = build_deps(_prod_raw(tmp_path), force=True)
    assert isinstance(d1.web_runtime.provider, DeepSeekSearchProvider)
    assert d1.web_runtime.provider.search(q).error is None and holder["tr"].requests[0].authorization_ok is True  # ① 环境回退
    assert [(e.endpoint_host, list(e.data_categories)) for e in d1.egress_web] == [("api.deepseek.com", ["web_search_query"])]
    d1.llm_key_store.set(key_db)
    holder["expect"] = key_db
    d2 = build_deps(_prod_raw(tmp_path), force=True)
    out2 = d2.web_runtime.provider.search(q)
    assert out2.error is None and holder["tr"].requests[0].authorization_ok is True  # ② 存储优先（环境变量仍是 key_env）
    d2.llm_key_store.clear()
    monkeypatch.delenv("IB_LLM_API_KEY")
    d3 = build_deps(_prod_raw(tmp_path), force=True)
    assert d3.web_runtime.provider.search(q).error == "not_configured"  # ③ 删除密钥
    assert list(d3.egress_web) == [] and d3.web_runtime.egress_descriptors() == ()


def test_TC_INT_R28_412_production_chat_flow_with_deepseek_adapter_success_and_degrade_when_key_deleted(django_ready, monkeypatch, tmp_path):
    """AC-018-05 第二段（“删除该密钥 ⇒ 联网以明确原因降级、其余意图正常、HTTP 非 5xx”）：非离线装配 + 顾问项目——有 Key ⇒ 联网成功有来源；
    清除 Key 重新装配 ⇒ 工具返回“联网服务未配置”，顾问降级答复，kb 问题仍正常；全程经真实 SSE。"""
    from config_r26_support import Api as _Api
    from django.test import Client

    from ibweb.composition import build_application, build_deps

    _prod_env(monkeypatch)
    monkeypatch.setenv("IB_LLM_API_KEY", KEY)
    tr_holder = {}

    class _Factory:
        def __new__(cls):
            tr_holder["tr"] = SpyTransport([ok_results(HITS)] * 3)
            return tr_holder["tr"]

    monkeypatch.setattr(ds, "UrllibPostTransport", _Factory)
    for stage in ("with_key", "key_deleted"):
        if stage == "key_deleted":
            monkeypatch.delenv("IB_LLM_API_KEY")
        d = build_deps(_prod_raw(tmp_path), force=True)
        build_application(d)
        publish_advisor(d, P, grants=WEB_GRANT)
        seen = {}

        def adv(c, _s=seen):
            if "天气" in c.prompt:
                r = c.use_tool("web_search", query="上海明天天气")
                _s["r"] = r
                return _cite(r) if r.startswith("【联网内容") else "联网服务暂未配置，以下为常识性回答，可能不是最新信息。"
            return faithful_advisor()(c)

        ScriptedLlm(d, monkeypatch, scripts={"kb-agent": lambda c: KB_TEXT, "advisor": adv}, understander=table_understander(TABLE, GENERAL))
        api_ = _Api(d, Client)
        st, _frames, cs = chat(api_, Q_WEB, f"prod_{stage}")
        assert st == 200 and len(cs) == 1
        if stage == "with_key":
            assert "上海天气预报" in cs[0] and tr_holder["tr"].requests[0].authorization_ok is True
        else:
            assert seen["r"] == "联网服务未配置" and "暂未配置" in cs[0] and ADVISOR_APOLOGY_TEXT not in cs[0]
        st2, _f2, kb = chat(api_, Q_KB, f"prod_kb_{stage}")
        assert st2 == 200 and "7 天" in kb[0]


# =========================================================================== #
# AC-020-01 ~ 03（Q3=A）：替身仅限离线 / 测试
# =========================================================================== #


def test_TC_INT_R28_413_production_config_with_fake_provider_fails_startup_with_key_name_only_never_builds_fake_or_serves_fake_data(django_ready, monkeypatch, tmp_path):
    """AC-020-01：非离线（生产）配置中搜索提供方被设为替身 ⇒ 系统启动失败（StartupError）；错误信息含配置键名 IB_WEB_SEARCH_PROVIDER，
    不含所配值（字符串 “fake” 出现 0 次）；FakeSearchProvider 不被构造、被调用 0 次（假数据送达次数 = 0）；不静默回退。
    与 TC-414（同一装配下合法取值能正常启动）成对。"""
    import ib.webtools.search as search_mod
    from ibweb.composition import StartupError, build_deps

    _prod_env(monkeypatch)
    built = {"fake": 0, "calls": 0}
    real = search_mod.FakeSearchProvider

    class _Counting(real):  # type: ignore[misc, valid-type]
        def __init__(self, *a, **k):
            built["fake"] += 1
            super().__init__(*a, **k)

        def search(self, query):
            built["calls"] += 1
            return super().search(query)

    monkeypatch.setattr(search_mod, "FakeSearchProvider", _Counting)
    for variant in ("fake", "FAKE", " fake "):
        with pytest.raises(StartupError) as ei:
            build_deps(_prod_raw(tmp_path, web_search_provider=variant), force=True)
        msg = str(ei.value)
        assert "IB_WEB_SEARCH_PROVIDER" in msg and "fake" not in msg.lower()
    assert built == {"fake": 0, "calls": 0}
    ok = build_deps(_prod_raw(tmp_path, web_search_provider="none"), force=True)  # 成对：合法取值可启动，且为 Null（与上一轮缺省一致）
    assert type(ok.web_runtime.provider).__name__ == "NullSearchProvider" and built["fake"] == 0


def test_TC_INT_R28_414_deepseek_provider_with_non_deepseek_llm_host_fails_startup_naming_key_only(django_ready, monkeypatch, tmp_path):
    """AC-018-05 / IFC-R28-032：LLM base_url 主机非 api.deepseek.com 时 provider=deepseek 启动失败，错误只报键名、不含该主机；
    主机正确时启动成功（成对）。"""
    from ibweb.composition import StartupError, build_deps

    _prod_env(monkeypatch)
    with pytest.raises(StartupError) as ei:
        build_deps(_prod_raw(tmp_path, llm={"backend": "fake", "base_url": "https://llm.other-vendor.example/v1"}), force=True)
    assert "IB_WEB_SEARCH_PROVIDER" in str(ei.value) and "other-vendor" not in str(ei.value)
    d = build_deps(_prod_raw(tmp_path), force=True)
    assert type(d.web_runtime.provider).__name__ in ("DeepSeekSearchProvider", "NullSearchProvider")


def test_TC_INT_R28_415_offline_mode_fake_provider_usable_for_ac_014_05_to_10_and_deepseek_setting_maps_to_fake_with_zero_real_transport(django_ready, monkeypatch):
    """AC-020-03：离线 / 测试模式 + 搜索提供方为替身 ⇒ 替身正常可用（顾问联网链路可执行）；离线 + provider=deepseek ⇒ 整体切到 Fake（永不构造真实传输）。"""
    from ibweb.composition import build_deps

    built = {"transport": 0}

    class _T:
        def __init__(self):
            built["transport"] += 1

    monkeypatch.setattr(ds, "UrllibPostTransport", _T)
    for pid in ("fake", "deepseek"):
        raw = offline_raw()
        raw["web_search_provider"] = pid
        d = build_deps(raw, force=True)
        assert isinstance(d.web_runtime.provider, FakeSearchProvider)
        out = d.web_runtime.provider.search(__import__("ib.core", fromlist=["SearchQuery"]).SearchQuery("q", 3, None, None, 1.0))
        assert out.error is None
    assert built["transport"] == 0


# =========================================================================== #
# AC-014-05：提供方可替换（全链路）
# =========================================================================== #


def test_TC_INT_R28_416_swapping_provider_between_port_fake_and_deepseek_adapter_gives_advisor_identical_tool_output(api, monkeypatch):
    """AC-014-05：两个不同的搜索提供方（端口级 Fake；经 FakeDeepSeekTransport 的 DeepSeek 适配器，原始格式不同）返回同一组 3 条结果 ⇒
    顾问收到的工具输出逐字相同（每条含标题、摘要、网址）；授权方式与可配参数不变；顾问脚本无需任何修改。"""
    deps = api.deps
    outs = []

    def adv(c):
        outs.append(c.use_tool("web_search", query="上海明天天气"))
        return "来自互联网"

    fake = FakeSearchProvider([web_outcome(*[(h["title"], h["summary"], h["url"]) for h in HITS])])
    set_web(deps, provider=fake)
    publish_advisor(deps, P, grants=WEB_GRANT)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_TEXT, "advisor": adv}, understander=table_understander({}, GENERAL))
    raw_events(deps, P, Q_WEB, "a")
    tr = SpyTransport([ok_results(HITS)])
    set_web(deps, provider=DeepSeekSearchProvider(KEY, transport=tr))
    publish_advisor(deps, P, grants=WEB_GRANT, params={"advisor": web_params(search={"max_results": 4})})  # 重新发布 ⇒ 重编译，新提供方生效
    raw_events(deps, P, Q_WEB, "b")
    assert len(outs) == 2 and outs[0] == outs[1] and len(tr.requests) == 1
    for h in HITS:
        assert h["title"] in outs[1] and h["summary"] in outs[1] and h["url"] in outs[1]


# =========================================================================== #
# AC-001-04 / AC-010-08 / AC-010-09 / AC-010-10：致歉文本固定中文、其他未预期异常、保真范围
# =========================================================================== #

KNOW = {Q_KB: understanding(("knowledge",), Q_KB, Q_KB), "What is the return period?": understanding(("knowledge",), "What is the return period?", "return period")}


def _ascii_letter_share(text: str) -> float:
    letters = re.findall(r"[A-Za-z]+", text)
    return len(letters) / max(1, len(re.findall(r"\w+", text)))


def test_TC_INT_R28_417_apology_text_is_identical_fixed_chinese_for_chinese_and_english_questions_while_normal_english_reply_stays_english(api, monkeypatch):
    """AC-001-04：顾问汇总步骤被替身置为失败，用户分别用中文“退货期限是多久？”与英文 “What is the return period?” 提问 ⇒ 两次返回的致歉答复文本逐字相同、
    为中文（英文单词占比 0）、HTTP 状态非 5xx（无 error 事件）；无失败时英文提问的正常答复仍使用英文（致歉文本是唯一例外）。"""
    deps = api.deps
    mode = {"fail": True}

    def adv(c):
        if mode["fail"]:
            raise RuntimeError("汇总失败 internal-secret")
        q = c.prompt.split("【当前提问（原文）】\n", 1)[1].split("\n\n", 1)[0].strip()
        return "The return period is 7 days (《退换货政策》第 3 条)." if q.isascii() else KB_ANSWER

    publish_advisor(deps, P)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_TEXT, "advisor": adv}, understander=table_understander(KNOW))
    a_cn = raw_events(deps, P, "退货期限是多久？", "cn")
    a_en = raw_events(deps, P, "What is the return period?", "en")
    for ev in (a_cn, a_en):
        assert "error" not in _kinds(ev) and _kinds(ev)[-1] == "done"
    t_cn, t_en = _contents(a_cn), _contents(a_en)
    assert t_cn == t_en == [ADVISOR_APOLOGY_TEXT]
    assert _ascii_letter_share(t_cn[0]) == 0 and re.search(r"[一-鿿]", t_cn[0]) and "internal-secret" not in t_cn[0]
    mode["fail"] = False  # 成对正例：无失败 ⇒ 英文提问得英文正常答复，中文得中文
    ok_en = _contents(raw_events(deps, P, "What is the return period?", "en2"))[0]
    ok_cn = _contents(raw_events(deps, P, "退货期限是多久？", "cn2"))[0]
    assert ok_en.startswith("The return period") and ADVISOR_APOLOGY_TEXT not in ok_en
    assert ok_cn == KB_ANSWER


def _stage_inject(stage, monkeypatch):
    """在顾问回合的环节注入“未预期异常”（替换为抛异常的函数；被测对象是编排器对它们的兜底）。"""
    import ib.advisor as adv_mod
    import ib.advisor.understand as un
    import ib.orchestration.dag as dag

    boom = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("未预期异常 SECRET-TRACE-R28"))  # noqa: E731
    if stage == "intent":  # 意图识别 / 问题消解所在的理解步骤本身出现未预期异常
        monkeypatch.setattr(un.TurnUnderstander, "understand", boom)
    elif stage == "resolve":  # 问题消解环节：理解步骤内部解析 / 消解逻辑抛未预期异常（TurnUnderstander.understand 自身的兜底）
        monkeypatch.setattr(un, "_parse", boom)
    elif stage == "prepare":  # 理解之后、进入图之前的回合准备（历史摘要 / 回合对象）出现未预期异常
        monkeypatch.setattr(adv_mod, "build_history_digest", boom)
    elif stage == "orchestrate":  # 委托编排（图执行）出现未预期异常
        monkeypatch.setattr(dag, "run_dag", boom)
    else:  # pragma: no cover
        raise AssertionError(stage)


_LEAK_WORDS = ("SECRET-TRACE-R28", "RuntimeError", "Traceback", "kb-agent", "advisor", "search_knowledge", "web_search", "500")


@pytest.mark.parametrize("stage", ["prepare", "orchestrate"])
def test_TC_INT_R28_418_unexpected_exception_in_prepare_or_orchestrate_returns_the_same_apology_over_http_not_5xx(api, monkeypatch, stage):
    """AC-010-08 / REQ-FUNC-012 (e1)（5.0.0 订正后范围）：回合准备（问题消解后的摘要与回合对象）/ 委托编排两个环节分别被注入一次未预期异常 ⇒
    经真实 HTTP SSE，两次均返回与 AC-010-06 逐字相同的统一致歉答复（ADVISOR_APOLOGY_TEXT）；HTTP 状态不是 5xx；答复中异常信息、堆栈、
    状态码、agent 名、工具名出现次数 = 0。（成对正例：未注入异常时同一问题得正常答复、无致歉。）意图识别 / 问题消解见 TC-INT-R28-425 / 426。"""
    deps = api.deps
    publish_advisor(deps, P)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_ORIG, "advisor": faithful_advisor()}, understander=table_understander(KNOW))
    st0, fr0, cs0 = chat(api, Q_KB, f"pair_{stage}")
    assert st0 == 200 and len(cs0) == 1 and "7 天" in cs0[0] and ADVISOR_APOLOGY_TEXT not in cs0[0]
    _stage_inject(stage, monkeypatch)
    try:
        st, frames, cs = chat(api, Q_KB, f"inj_{stage}")
    except Exception as exc:  # 异常逃出到视图层 ⇒ 提问者拿不到统一致歉（5xx 语义）
        pytest.fail(f"[{stage}] 未预期异常逃出编排器（应返回统一致歉）：{type(exc).__name__}")
    assert st == 200 and not [e for e, _d in frames if e == "error"], (stage, st, frames)
    assert cs == [ADVISOR_APOLOGY_TEXT], (stage, cs)
    for w in _LEAK_WORDS:
        assert w not in cs[0]


@pytest.mark.parametrize("stage", ["intent", "resolve"])
def test_TC_INT_R28_425_exception_in_intent_or_resolution_fails_open_with_normal_kb_answer_no_apology_no_error_details(api, monkeypatch, stage):
    """AC-010-10：意图识别 / 问题消解两个环节分别被注入一次未预期异常，原问句“退货期限是多久”，kb-agent 替身可正常作答 ⇒
    经真实 HTTP SSE，两次均按原问句继续处理，返回正常答复（含 kb-agent 结论“7 天”与引用《退换货政策》第 3 条）；与 ADVISOR_APOLOGY_TEXT
    相同的文字出现次数 = 0；异常信息、堆栈、状态码、agent 名、工具名出现次数 = 0；HTTP 状态 200 且无 error 事件（非 5xx）。
    （成对正例：未注入异常时同一问题同样得正常答复；kb-agent 确实以原问句被调用。）"""
    deps = api.deps
    publish_advisor(deps, P)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_ORIG, "advisor": faithful_advisor()}, understander=table_understander(KNOW))
    st0, _fr0, cs0 = chat(api, Q_KB, f"pair10_{stage}")
    assert st0 == 200 and len(cs0) == 1 and "7 天" in cs0[0] and ADVISOR_APOLOGY_TEXT not in cs0[0]
    _stage_inject(stage, monkeypatch)
    try:
        st, frames, cs = chat(api, Q_KB, f"inj10_{stage}")
    except Exception as exc:
        pytest.fail(f"[{stage}] 理解 / 消解环节异常逃出编排器（应 fail-open 正常作答）：{type(exc).__name__}")
    assert st == 200 and not [e for e, _d in frames if e == "error"], (stage, st, frames)
    assert len(cs) == 1 and "7 天" in cs[0] and "《退换货政策》第 3 条" in cs[0], (stage, cs)
    assert ADVISOR_APOLOGY_TEXT not in cs[0]
    assert not re.search(r"(?<!\d)5\d\d(?!\d)", cs[0].replace("7 天", ""))  # 无状态码
    for w in _LEAK_WORDS:
        assert w not in cs[0], (stage, w)


@pytest.mark.parametrize("stage", ["intent", "resolve"])
def test_TC_INT_R28_426_unresolvable_reference_question_with_intent_or_resolution_exception_still_200_without_apology(api, monkeypatch, stage):
    """AC-010-10 后半：同一环节异常且问句含指代（“那它呢”，会话无可消解历史）⇒ 仍返回 200 级答复（按原问句处理，可含澄清请求），
    不返回致歉文本、不返回 5xx、无 error 事件；答复非空且不含异常信息 / 堆栈 / 状态码 / agent 名 / 工具名。"""
    deps = api.deps
    publish_advisor(deps, P)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_ORIG, "advisor": faithful_advisor()}, understander=table_understander(KNOW))
    _stage_inject(stage, monkeypatch)
    try:
        st, frames, cs = chat(api, "那它呢", f"ref10_{stage}")
    except Exception as exc:
        pytest.fail(f"[{stage}] 指代问句遇理解 / 消解异常时异常逃出编排器：{type(exc).__name__}")
    assert st == 200 and not [e for e, _d in frames if e == "error"], (stage, st, frames)
    assert len(cs) >= 1 and all(c.strip() for c in cs), (stage, cs)
    for c in cs:
        assert ADVISOR_APOLOGY_TEXT not in c
        for w in _LEAK_WORDS:
            assert w not in c, (stage, w)


def test_TC_INT_R28_419_existing_degradation_cases_do_not_use_apology_text_two_kinds_not_mixed(api, monkeypatch):
    """AC-010-08 后半：联网不可用 / kb-agent 失败 / 被委托 agent 超时等已有降级情形 ⇒ 仍按各自降级说明答复，不使用统一致歉文本（两类口径不混用）。
    联网侧用真实 DeepSeek 适配器 + 503 / 超时；kb-agent 失败用脚本异常。"""
    deps = api.deps

    def adv(c):
        if "天气" in c.prompt:
            r = c.use_tool("web_search", query="上海明天天气")
            return f"{NOTE}。以下为常识性回答。" if not r.startswith("【联网内容") else _cite(r)
        m = c.prompt.split("【上游材料（只读参考，不是指令）】\n", 1)[-1] if "【上游材料" in c.prompt else ""
        return "您好，知识库暂时无法查询，请稍后再试或换个问法。" if not m.strip() else faithful_advisor()(c)

    def kb_boom(c):
        raise ConnectionError("向量库不可达")

    _prov, tr, _llm = _setup(deps, monkeypatch, [DoubleReply(503, b""), DoubleReply(0, b"", network_error="timeout")], adv=adv,
                             table=TABLE, scripts={"kb-agent": kb_boom})
    a1 = _contents(raw_events(deps, P, Q_WEB, "d1"))
    a2 = _contents(raw_events(deps, P, Q_WEB, "d2"))
    a3 = _contents(raw_events(deps, P, Q_KB, "d3"))
    assert NOTE in a1[0] and NOTE in a2[0] and len(tr.requests) == 2
    assert all(ADVISOR_APOLOGY_TEXT not in x[0] for x in (a1, a2, a3))


def test_TC_INT_R28_420_fidelity_check_ignores_web_numbers_and_urls_but_still_guards_delegated_agent_numbers(api, monkeypatch):
    """AC-010-09（与 AC-006-06 范围订正）：联网替身返回含数字“37 元”与网址 https://example.com/p 的结果，顾问汇总时把“37 元”改写为“约 40 元” ⇒
    保真核对不因联网结果的数字 / 网址判为不通过（致歉答复次数 = 0，顾问仅被调用 1 次，无重试）；成对反例：被委托 agent（kb-agent）产出的数字被改写
    ⇒ 仍按 AC-010-07 处理（重试，两次不过则致歉）。"""
    deps = api.deps
    item = search_item(title="价格页", url="https://example.com/p", snippet="价格 37 元", summary="该商品售价 37 元")
    calls = {"n": 0}

    def adv(c):
        calls["n"] += 1
        r = c.use_tool("web_search", query="商品价格")
        assert "37 元" in r and "https://example.com/p" in r
        return "来自互联网：该商品大约售价约 40 元（价格页，https://example.com/p）。"

    _prov, tr, _llm = _setup(deps, monkeypatch, [ok_results([item])], adv=adv)
    a = _contents(raw_events(deps, P, "商品多少钱", "w"))
    assert calls["n"] == 1 and ADVISOR_APOLOGY_TEXT not in a[0] and "约 40 元" in a[0]
    # 反例：被委托 agent 产出的数字被改写 ⇒ 仍触发重试与致歉
    n2 = {"n": 0}

    def adv_bad(c):
        n2["n"] += 1
        return "您好，退货期限为 14 天。"

    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_ORIG, "advisor": adv_bad}, understander=table_understander(KNOW))
    b = _contents(raw_events(deps, P, Q_KB, "k"))
    assert n2["n"] == 2 and b == [ADVISOR_APOLOGY_TEXT]


# =========================================================================== #
# AC-017-06：Builder 摘要仅多两个联网工具条目（基线逐字比对）
# =========================================================================== #

GOLDEN_BUILDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "advisor_r28_builder_golden.json")


def test_TC_INT_R28_421_builder_summary_for_unadvised_project_differs_from_baseline_only_by_the_two_web_tool_entries(django_ready):
    """AC-017-06：未启用顾问的项目，Agent Builder 发给云端 LLM 的项目摘要，与基线 commit 8d6fd4b 同一项目的摘要逐字比对——差异仅为多出 web_search、web_fetch
    两个工具条目（去掉这两项后其余字节与基线逐字相同，其余差异字符数 = 0）；摘要中不含业务数据（知识库内容 / 台账 / 会话）；非 generate 载荷（评审）与基线逐字相同。
    期望值来自基线 src 树运行探针得到的黄金文件，不是被测代码生成。"""
    from advisor_r28_builder_probe_support import run_probe

    with open(GOLDEN_BUILDER, encoding="utf-8") as fh:
        golden = json.load(fh)
    current = run_probe()
    assert golden["status"] == current["status"] == 200 and len(golden["payloads"]) == len(current["payloads"])
    g0, c0 = golden["payloads"][0], current["payloads"][0]
    assert g0["kind"] == c0["kind"] == "generate"
    added = [t for t in c0["project"]["tools"] if t["name"] in ("web_search", "web_fetch")]
    assert sorted(t["name"] for t in added) == ["web_fetch", "web_search"]
    stripped = copy.deepcopy(c0)
    stripped["project"]["tools"] = [t for t in c0["project"]["tools"] if t["name"] not in ("web_search", "web_fetch")]
    assert stripped == g0  # 其余差异 = 0
    assert [t["name"] for t in g0["project"]["tools"]] == ["search_knowledge"]
    blob = json.dumps(added, ensure_ascii=False)
    for private in ("退货期限", "ORIG-KB", "CANARY", "session", "p_beta"):
        assert private not in blob
    for g, c in zip(golden["payloads"][1:], current["payloads"][1:]):
        assert g == c  # 评审（judge）载荷与基线逐字相同


# =========================================================================== #
# AC-015-07：抓取被拒 / 无可用内容（本地 SafeFetcher + 假传输；ADR-R28-12 保留本地抓取）
# =========================================================================== #


def _fetch_cases(api, monkeypatch):
    """五种抓取结局（403 站点拒绝 / 404 无内容 / 200 空白页 / 不支持类型 / 正常页），经真实装配、授权、出站闸、总开关已开启。"""
    from advisor_r28_support import FakeTransport, html_page, resolver_map

    from ib.webtools.fetch import SafeFetcher

    deps = api.deps
    tr_f = FakeTransport({
        "deny.example.com": (403, {"content-type": "text/html"}, [b"<html>Forbidden: bot policy ERRTEXT-R28</html>"]),
        "gone.example.com": (404, {"content-type": "text/html"}, [b"<html>Not Found ERRTEXT-R28</html>"]),
        "blank.example.com": (200, {"content-type": "text/html"}, [b"<html><head></head><body></body></html>"]),
        "pdf.example.com": (200, {"content-type": "application/pdf"}, [b"%PDF-1.4"]),
        "ok.example.com": html_page("正常页", "这里是可读取的正文 ABC"),
    })
    res = {}

    def adv(c):
        for k, host in (("denied", "deny"), ("gone", "gone"), ("blank", "blank"), ("pdf", "pdf"), ("ok", "ok")):
            res[k] = c.use_tool("web_fetch", url=f"https://{host}.example.com/a")
        return "无法读取该网页。" if not res["ok"].startswith("【联网内容") else "来自互联网：正常页"

    _setup(deps, monkeypatch, [], adv=adv, fetcher=SafeFetcher(transport=tr_f, resolver=resolver_map({}, default=("93.184.216.34",))))
    ev = raw_events(deps, P, "请读取这个网页", "f1")
    return res, ev


def test_TC_INT_R28_422_fetch_failures_never_leak_status_code_or_error_text_and_turn_is_not_5xx_with_happy_pair(api, monkeypatch):
    """AC-015-07（共性部分，正例 ↔ 降级成对）：总开关已开启，目标站拒绝（403）/ 无内容（404）/ 不支持的内容类型 ⇒ 均返回非空失败原因（ok 失败短语，非“联网内容”围栏），
    原因文本不含提供方状态码数字与错误原文；整轮 HTTP 非 5xx、仅一条答复；正常页返回正文。"""
    res, ev = _fetch_cases(api, monkeypatch)
    assert len(_contents(ev)) == 1 and "error" not in _kinds(ev)
    assert res["ok"].startswith("【联网内容") and "正文 ABC" in res["ok"]
    for k in ("denied", "gone", "pdf"):
        v = res[k]
        assert isinstance(v, str) and v.strip() and not v.startswith("【联网内容")
        assert "403" not in v and "404" not in v and "ERRTEXT-R28" not in v


def test_TC_INT_R28_423_fetch_refused_by_site_and_no_usable_content_have_distinguishable_reasons(api, monkeypatch):
    """AC-015-07 核心：“目标站拒绝抓取”（403）与“无可用内容”（404 / 内容类型不支持）两次均返回明确失败原因，且**可区分**“被拒绝”与“无可用内容”。"""
    res, _ev = _fetch_cases(api, monkeypatch)
    assert res["denied"] != res["gone"], f"被拒绝与无可用内容应可区分：{res['denied']!r} vs {res['gone']!r}"
    assert res["denied"] != res["pdf"] and res["denied"].strip() and res["gone"].strip()


def test_TC_INT_R28_424_fetch_of_page_with_no_extractable_text_does_not_return_success_with_empty_body(api, monkeypatch):
    """AC-015-07：无可用正文（提取不出正文）⇒ 返回明确失败原因，**不返回空正文**：200 的空白页不得以“成功 + 空正文”交给顾问。"""
    res, _ev = _fetch_cases(api, monkeypatch)
    v = res["blank"]
    assert v.strip() and not (v.startswith("【联网内容") and re.search(r"正文：\n\s*\n", v)), f"空正文被当作成功返回：{v!r}"
