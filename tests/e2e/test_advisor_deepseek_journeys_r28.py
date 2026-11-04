"""[REV-28 / GROUP_D-004] E2E 级旅程：DeepSeek 联网搜索（离线替身）/ 替身仅限离线（US-020）/ 抓取失败三种短语。

分层：e2e（多步 HTTP + 真实 SSE 流；真实账户鉴权 + 发布协议 + 运行时编译 + 出站闸 + 审计；LLM 为脚本化替身，
搜索提供方 = 真实 `DeepSeekSearchProvider` 适配器 + `FakeDeepSeekTransport` 替身，抓取 = `SafeFetcher` + 假传输 + 假 DNS）。
critical path 口径：替代（无浏览器 E2E 框架，后端多步 HTTP / SSE 旅程）。
autouse 夹具断言**零真实网络连接**（画像 P11-3：自动化测试禁止调用真实端点）；哨兵 Key 为测试占位串。
期望值来自 docs/external_api/deepseek_search_fetch.md 与 user_stories 4.0.0，不取自被测代码输出。
溯源：TC-E2E-R28-013 ← US-014 / 016 / 018（AC-014-07~10、AC-016-09、AC-018-05 / 06）；
      TC-E2E-R28-014 ← US-020 / 018（AC-020-01 / 03、AC-018-05）；TC-E2E-R28-015 ← US-015（AC-015-07）。
"""

from __future__ import annotations

import json
import re
import socket

import pytest
from advisor_r28_support import (
    KB_TEXT,
    P,
    FakeTransport,
    ScriptedLlm,
    advisor_document,
    advisor_prompts,
    chat,
    faithful_advisor,
    html_page,
    publish_advisor,
    resolver_map,
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
from ib.webtools.deepseek_double import FakeDeepSeekTransport, empty_results, error_reply, ok_results, search_item
from ib.webtools.fetch import SafeFetcher
from ib.webtools.search import FakeSearchProvider

KEY = "R28-E2E-SENTINEL-KEY-NOT-A-REAL-CREDENTIAL-5521"
WEB_GRANT = {"advisor": ("web_search", "web_fetch")}
NOTE = "未能联网检索到最新信息"
HITS = [
    search_item(title="上海天气预报", url="https://wx.example.com/sh", snippet="明天多云", summary="明天多云转阴 18-24 度"),
    search_item(title="天气网", url="https://tq.example.org/sh", snippet="降水", summary="周边降水概率 20%"),
]
GENERAL = understanding(("general",), "通用问题", "")
Q_WEB, Q_KB = "明天上海天气怎样？", "退货期限是多久"
TABLE = {Q_KB: understanding(("knowledge",), Q_KB, Q_KB)}


class SpyTransport(FakeDeepSeekTransport):
    def __init__(self, script=(), **kw):
        kw.setdefault("expected_key", KEY)
        super().__init__(script, **kw)
        self.raw: list[dict] = []

    def post_json(self, url, *, headers, body, timeout_s, max_reply_bytes):
        self.raw.append({"url": url, "headers": dict(headers), "body": body})
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


def _one(frames):
    kinds = [e for e, _d in frames]
    assert kinds.count("done") == 1 and kinds[-1] == "done" and "error" not in kinds, kinds
    cs = [d for e, d in frames if e == "content"]
    assert len(cs) == 1, cs
    return cs[0]


def _cite(result: str) -> str:
    pairs = re.findall(r"^\d+\. (.+)\n(?:.*)\n(https?://\S+)$", result, re.M)
    return "来自互联网：" + "；".join(f"{t}（{u}）" for t, u in pairs)


# =========================================================================== #
# TC-E2E-R28-013：DeepSeek 联网搜索旅程
# =========================================================================== #


def test_TC_E2E_R28_013_deepseek_search_journey_grant_ask_five_errors_empty_cap_canary_audit_via_sse(api, monkeypatch):
    """US-014 / 016 / 018（Must）。① 查看档不能发布 ② 编辑者经 HTTP 发布授权 web_search（每轮上限 3）③ SSE 提问：成功有来源 + 请求符合资料
    ④ 依次 401 / 402 / 429 / 500 / 504：每轮 HTTP 200、单条答复含降级说明、无状态码 / 错误原文 / Key；kb 问题不受影响 ⑤ 200 空数组：如实说明、网址 ⊆ 返回
    ⑥ 一轮 5 次检索：替身请求 ≤3 ⑦ canary 在检索词里 ⇒ 不出站 ⑧ 审计只含 host 不含查询原文 ⑨ 恢复后成功。"""
    deps = api.deps
    seen: list[str] = []
    state = {"canary": "CANARY-E2E-INTERNAL-0123456789ABCDEF"}

    def adv(c):
        if "天气" in c.prompt:
            r = c.use_tool("web_search", query="上海明天天气")
            seen.append(r)
            return _cite(r) if r.startswith("【联网内容") else (
                "未检索到相关结果，以下为常识性回答。" if "未找到相关结果" in r else f"{NOTE}，以下为常识性回答，可能不是最新信息。")
        if "密钥外发" in c.prompt:
            seen.append(c.use_tool("web_search", query=f"{state['canary']} 是什么"))
            seen.append(c.use_tool("web_search", query="今日金价"))
            return "来自互联网：已检索。"
        if "狂搜" in c.prompt:
            seen.extend(c.use_tool("web_search", query=f"检索{i}") for i in range(5))
            return "来自互联网：已有结果；后续检索已达本轮联网上限。"
        return faithful_advisor()(c)

    order = [401, 402, 429, 500, 504]
    tr = SpyTransport([ok_results(HITS)] + [error_reply(s) for s in order] + [empty_results(), ok_results(HITS), ok_results(HITS), ok_results(HITS),
                                                                               ok_results(HITS), ok_results(HITS), ok_results(HITS)])
    set_web(deps, provider=DeepSeekSearchProvider(KEY, transport=tr))
    doc = advisor_document(P, grants=WEB_GRANT, params={"advisor": web_params(search={"max_calls_per_turn": 3})})
    body = publish_body(doc, 0, advisor_prompts())
    assert api.post("/api/config/publish", body, who="viewer").status_code == 403  # ①
    pub = api.post("/api/config/publish", body, who="editor")  # ②
    assert pub.status_code == 200 and pub.json_body["applied"] is True, pub.content
    state["kb_on"] = False
    ScriptedLlm(deps, monkeypatch,
                scripts={"kb-agent": lambda c: KB_TEXT + (f" 内部编号：{state['canary']}（仅限内部）" if state["kb_on"] else ""), "advisor": adv},
                understander=table_understander({**TABLE, "密钥外发": GENERAL, "狂搜": GENERAL}, GENERAL))

    st, fr, _ = chat(api, Q_WEB, "n1", who="editor")  # ③
    assert st == 200
    a0 = _one(fr)
    assert "上海天气预报" in a0 and "https://wx.example.com/sh" in a0 and ADVISOR_APOLOGY_TEXT not in a0
    assert tr.raw[0]["url"] == "https://api.deepseek.com/v1/tools/search" and tr.raw[0]["headers"]["Authorization"] == f"Bearer {KEY}"
    assert set(json.loads(tr.raw[0]["body"])) == {"query", "count", "need_content"}

    for i, s in enumerate(order):  # ④
        st, fr, _ = chat(api, Q_WEB, f"d{i}", who="editor")
        a = _one(fr)
        assert st == 200 and NOTE in a and ADVISOR_APOLOGY_TEXT not in a and str(s) not in a and KEY not in a and "Bearer" not in a
        st2, fr2, _ = chat(api, Q_KB, f"k{i}", who="editor")
        assert st2 == 200 and "7 天" in _one(fr2)
    assert len(tr.requests) == 6

    st, fr, _ = chat(api, Q_WEB, "empty", who="editor")  # ⑤
    a5 = _one(fr)
    assert st == 200 and "未检索到相关结果" in a5 and not re.findall(r"https?://", a5) and seen[-1] == "联网检索未找到相关结果"
    assert len(tr.requests) == 7

    n0 = len(tr.requests)  # ⑥
    st, fr, _ = chat(api, "狂搜一下", "cap", who="editor")
    assert st == 200 and _one(fr) and len(tr.requests) - n0 == 3
    state["kb_on"] = True  # ⑦ 专业问题的 kb 输出含 canary，进入同一会话的助手历史
    st, fr, _ = chat(api, Q_KB, "can", who="editor")
    assert st == 200 and _one(fr)
    n1 = len(tr.requests)
    st, fr, _ = chat(api, "密钥外发测试", "can", who="editor")
    assert st == 200 and _one(fr) and seen[-2] == "请求内容不被允许" and seen[-1].startswith("【联网内容") and len(tr.requests) - n1 == 1
    assert all(state["canary"] not in r["body"].decode("utf-8") for r in tr.raw)

    audit = [e for e in deps.config_audit_store.list_by_project(P) if e.action == "web.search"]  # ⑧
    assert audit and all("host:api.deepseek.com" in e.object_summary and "上海明天天气" not in repr(e) and state["canary"] not in repr(e) for e in audit)
    assert KEY not in repr(deps.config_audit_store.list_by_project(P))

    # ⑨ 恢复：脚本末尾仍有成功回复
    st, fr, _ = chat(api, Q_WEB, "recover", who="editor")
    assert st == 200 and "上海天气预报" in _one(fr)


# =========================================================================== #
# TC-E2E-R28-014：替身仅限离线 / 生产装配（US-020）
# =========================================================================== #


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


def test_TC_E2E_R28_014_fake_provider_only_offline_journey_prod_fake_refused_deepseek_key_sources_via_sse(django_ready, accounts_app, monkeypatch, tmp_path):
    """US-020 / 018（Must）。① 离线 + 替身提供方：SSE 联网旅程可执行（AC-020-03）② 非离线 + fake ⇒ StartupError（含键名、不含值，替身构造 0 次）（AC-020-01）
    ③ 非离线 + deepseek + 仅环境 Key ⇒ SSE 联网成功（请求头为该 Key）④ 存储 Key 优先于环境 ⑤ 删除存储与环境 Key ⇒ 联网降级（HTTP 200）、kb 问题正常
    ⑥ 全程真实传输类被替身替换，零触网。"""
    from django.test import Client

    import ib.webtools.search as search_mod
    from ibweb.composition import StartupError, build_application, build_deps

    # ① 离线 + 替身
    deps0, client_cls = accounts_app
    api0 = Api(deps0, client_cls)
    api0.add_user("editor", P, "edit")
    set_web(deps0, provider=FakeSearchProvider([web_outcome(("上海天气预报", "明天多云", "https://wx.example.com/sh"))]))
    publish_advisor(deps0, P, grants=WEB_GRANT)

    def adv0(c):
        r = c.use_tool("web_search", query="上海明天天气")
        return _cite(r) if r.startswith("【联网内容") else NOTE

    ScriptedLlm(deps0, monkeypatch, scripts={"kb-agent": lambda c: KB_TEXT, "advisor": adv0}, understander=table_understander(TABLE, GENERAL))
    st, fr, _ = chat(api0, Q_WEB, "off1", who="editor")
    a = _one(fr)
    assert st == 200 and "上海天气预报" in a and "https://wx.example.com/sh" in a

    # ② 非离线 + fake
    _prod_env(monkeypatch)
    built = {"fake": 0}
    real = search_mod.FakeSearchProvider

    class _Counting(real):  # type: ignore[misc, valid-type]
        def __init__(self, *a, **k):
            built["fake"] += 1
            super().__init__(*a, **k)

    monkeypatch.setattr(search_mod, "FakeSearchProvider", _Counting)
    with pytest.raises(StartupError) as ei:
        build_deps(_prod_raw(tmp_path, web_search_provider="fake"), force=True)
    assert "IB_WEB_SEARCH_PROVIDER" in str(ei.value) and "fake" not in str(ei.value).lower() and built["fake"] == 0

    # ③~⑤ 非离线 deepseek：Key 来源切换
    holder = {}
    key_env, key_db = KEY + "-ENV", KEY + "-DB"

    class _Factory:
        def __new__(cls):
            holder["tr"] = SpyTransport([ok_results(HITS)] * 3, expected_key=holder["expect"])
            return holder["tr"]

    monkeypatch.setattr(ds, "UrllibPostTransport", _Factory)

    def run_stage(stage):
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
        a_ = Api(d, Client)
        s1, f1, _ = chat(a_, Q_WEB, f"p_{stage}")
        s2, f2, _ = chat(a_, Q_KB, f"pk_{stage}")
        assert s1 == 200 and s2 == 200 and "7 天" in _one(f2)
        return d, seen, _one(f1)

    monkeypatch.setenv("IB_LLM_API_KEY", key_env)
    holder["expect"] = key_env
    d1, _s1, a1 = run_stage("env")
    assert "上海天气预报" in a1 and holder["tr"].requests[0].authorization_ok is True
    d1.llm_key_store.set(key_db)
    holder["expect"] = key_db
    d2, _s2, a2 = run_stage("db")
    assert "上海天气预报" in a2 and holder["tr"].requests[0].authorization_ok is True  # 存储优先（环境变量仍是 key_env）
    d2.llm_key_store.clear()
    monkeypatch.delenv("IB_LLM_API_KEY")
    _d3, s3, a3 = run_stage("none")
    assert s3["r"] == "联网服务未配置" and "暂未配置" in a3 and ADVISOR_APOLOGY_TEXT not in a3 and key_db not in a3 and key_env not in a3


# =========================================================================== #
# TC-E2E-R28-015：抓取 403 / 404 / 空正文 三种失败短语
# =========================================================================== #


def test_TC_E2E_R28_015_fetch_failure_journey_403_404_blank_have_distinct_reasons_no_status_no_empty_body_via_sse(api, monkeypatch):
    """US-015（Must）AC-015-07。顾问经 SSE 依次读取 5 个网址：403 拒绝 / 404 无内容 / 200 空白页 / 不支持类型 / 正常页 ⇒
    ① 整轮 HTTP 200、单条答复、无 error ② 正常页返回围栏正文（正例）③ 403 与 404 的失败短语可区分（拒绝 ≠ 无可用内容）
    ④ 200 空白页不得以“成功 + 空正文”返回，且与 403 短语可区分 ⑤ 全部失败短语不含状态码数字与错误原文。"""
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
        return "来自互联网：正常页；其余网页无法读取。"

    set_web(deps, fetcher=SafeFetcher(transport=tr_f, resolver=resolver_map({}, default=("93.184.216.34",))))
    publish_advisor(deps, P, grants=WEB_GRANT)
    ScriptedLlm(deps, monkeypatch, scripts={"kb-agent": lambda c: KB_TEXT, "advisor": adv}, understander=table_understander({}, GENERAL))
    st, fr, _ = chat(api, "请读取这个网页", "f1", who="editor")
    assert st == 200 and "正常页" in _one(fr)  # ①
    assert res["ok"].startswith("【联网内容") and "正文 ABC" in res["ok"]  # ②
    assert res["denied"].strip() and res["gone"].strip() and res["denied"] != res["gone"]  # ③
    blank = res["blank"]
    assert blank.strip() and not (blank.startswith("【联网内容") and re.search(r"正文：\n\s*\n", blank)) and blank != res["denied"]  # ④
    for k in ("denied", "gone", "blank", "pdf"):  # ⑤
        v = res[k]
        assert not v.startswith("【联网内容") and "403" not in v and "404" not in v and "ERRTEXT-R28" not in v, (k, v)
