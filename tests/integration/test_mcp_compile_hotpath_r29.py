"""[REV-29 / GROUP_D] 集成：授权 → 保存期校验 → 编译（真实 langgraph 运行时）→ 热生效 → 调用期实时准入。

分层：integration（MOD-R29-16 授权校验 ↔ MOD-R29-18 编译/编排钩子 ↔ MOD-R29-13 注册器 ↔ MOD-R29-12 调用器；真实发布协议与运行时缓存；LLM 为脚本化替身）。
溯源：US-013 / 016 / 017 / 019 / 020 / 007 / 015。
"""

from __future__ import annotations

import re

import pytest
from advisor_r28_support import P, ScriptedLlm, chat
from mcp_r29_support import CANARY_TOKEN, Harness, make_harness, tool

from ib.mcp.result import FENCE_OPEN, MCP_PHRASES

EXT = "mcp__crm__search"
BETA = "p_beta"


@pytest.fixture()
def h(monkeypatch) -> Harness:
    return make_harness(monkeypatch)


def _tools_of(h: Harness, agent: str, project: str = P) -> list[str]:
    return [t.name for t in h.deps.runtime_for(project).compiled.view.agents[agent].tools]


def _codes(resp) -> set[str]:
    return {i["code"] for i in resp.json_body["error"]["items"]}


def test_TC_INT_R29_1000_grant_gives_tool_only_to_granted_agent_and_runtime_enforces_AC_016_01_04_019_01(h, monkeypatch):
    srv = h.ready("crm", [tool("search")])
    assert EXT not in _tools_of(h, "kb-agent") if "kb-agent" in h.deps.runtime_for(P).compiled.view.agents else True
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT), "advisor": ()}, who="editor")
    assert resp.status_code == 200, resp.json_body
    assert EXT in _tools_of(h, "kb-agent") and EXT not in _tools_of(h, "advisor")  # 差异：新增授权只给 kb-agent
    seen: dict = {}
    unauth: list = []

    def kb(c):
        seen["kb_tools"] = c.tool_names
        seen["result"] = c.use_tool(EXT, q="客户A")
        return "KB:" + seen["result"]

    def adv(c):
        seen["adv_tools"] = c.tool_names
        c._on_unauth = unauth.append
        seen["adv_try"] = c.use_tool(EXT, q="越权尝试")
        return "ADV"

    ScriptedLlm(h.deps, monkeypatch, scripts={"kb-agent": kb, "advisor": adv})
    st, frames, cs = chat(h.api, "退货期限", "g1")
    assert st == 200 and EXT in seen["kb_tools"] and EXT not in seen["adv_tools"]
    assert seen["result"].startswith(FENCE_OPEN) and "ok:search" in seen["result"]  # AC-019-01：结果以围栏数据交给 agent
    assert h.n_calls(srv) == 1, "顾问越权调用被拒：替身只收到 kb-agent 的 1 次调用"
    assert unauth == [EXT] and "未授权" in seen["adv_try"]
    rec = [a for a in h.audit_rows(kind="call") if a.action == "call"]
    assert len(rec) == 1 and rec[0].project_id == P and rec[0].tool_name == EXT


def test_TC_INT_R29_1001_publish_takes_effect_without_restart_and_grant_removal_revokes_AC_016_01(h):
    h.ready("crm", [tool("search")])
    before = h.deps.runtime_for(P).compiled.version
    assert EXT not in _tools_of(h, "kb-agent")
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT), "advisor": ()}, who="editor")
    assert resp.status_code == 200 and resp.json_body["applied"] is True
    lease = h.deps.runtime_for(P)
    assert lease.compiled.version == resp.json_body["previous_version"] + 1 > before and EXT in [t.name for t in lease.compiled.view.agents["kb-agent"].tools]
    # 取消授权 ⇒ 立即不在工具列表
    resp2, _ = h.publish_http({"kb-agent": ("search_knowledge",), "advisor": ()}, who="editor")
    assert resp2.status_code == 200 and EXT not in _tools_of(h, "kb-agent")


@pytest.mark.parametrize("mutate,code", [
    ("ghost", "mcp_tool_unknown"), ("rereview", "mcp_tool_needs_rereview"), ("offline", "mcp_tool_offline"),
    ("srv_disabled", "mcp_server_unavailable"), ("not_open", "mcp_server_not_open"), ("tool_disabled", "mcp_tool_not_enabled"),
])
def test_TC_INT_R29_1002_save_rejects_unusable_grants_with_per_tool_errors_whole_config_unsaved_AC_016_02_03(h, mutate, code):
    srv = h.ready("crm", [tool("search", desc="机密描述-不得泄露")], projects=(P,))
    name = EXT
    if mutate == "ghost":
        name = "mcp__crm__ghost"
    elif mutate == "rereview":
        srv.mutate_tool("search", description="新")
        h.api.post("/api/mcp/servers/crm/refresh")
    elif mutate == "offline":
        srv.remove_tool("search")
        h.api.post("/api/mcp/servers/crm/refresh")
    elif mutate == "srv_disabled":
        h.api.post("/api/mcp/servers/crm/disable")
    elif mutate == "not_open":
        h.open("crm", ())
    elif mutate == "tool_disabled":
        h.api.post(f"/api/mcp/tools/{h.tool_id(EXT)}/state", {"enabled": False})
    v0 = h.api.get("/api/config/status").json_body["version"]
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", name), "advisor": ()}, who="editor")
    assert resp.status_code == 400 and code in _codes(resp), resp.json_body
    items = resp.json_body["error"]["items"]
    assert any(name in i["path"] for i in items), "逐条错误指出工具名"
    assert "机密描述" not in resp.content.decode("utf-8") and "inputSchema" not in resp.content.decode("utf-8")  # 不泄露描述 / schema
    assert h.api.get("/api/config/status").json_body["version"] == v0, "整份配置不被保存"


def test_TC_INT_R29_1003_cross_project_grant_rejected_without_leak_AC_016_03_007_03(h):
    h.b.resolver.set("erp.example.com", ["93.184.216.34"])
    r = h.api.post("/api/mcp/servers", {"server_id": "erp", "description": "d", "transport": "streamable_http", "endpoint_url": "https://erp.example.com/mcp",
                                        "auth_kind": "none" if False else "bearer", "data_categories": ["query_text"], "scope_kind": "project", "owner_project": P})
    assert r.status_code == 201
    from ib.mcp.double import FakeMcpServer

    srv = FakeMcpServer(tools=[tool("secret_tool", desc="A项目专属-描述")], required_bearer=CANARY_TOKEN)
    h.b.transport.add_server("https://erp.example.com/mcp", srv)
    h.api.put("/api/mcp/servers/erp/credentials", {"scope": "shared", "secret": CANARY_TOKEN})
    h.enable("erp"); h.approve("mcp__erp__secret_tool")
    h.grant(kb_agent=("search_knowledge", "mcp__erp__secret_tool"))  # A 自己可授权
    assert h.invoke("mcp__erp__secret_tool", project=P).ok
    n = h.n_calls(srv)
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", "mcp__erp__secret_tool"), "advisor": ()}, who="ed_beta", project=BETA)
    assert resp.status_code == 400 and "mcp_server_not_open" in _codes(resp)
    assert "A项目专属" not in resp.content.decode("utf-8")
    assert h.invoke("mcp__erp__secret_tool", project=BETA, turn="b1").ok is False and h.n_calls(srv) == n  # 调用被拒、B 的数据未被读取


def test_TC_INT_R29_1004_runtime_created_project_has_no_servers_and_is_denied_until_opened_AC_007_02_05_M_PM_010(h, monkeypatch, tmp_path):
    """运行期新建项目（M-PM-010，N=1）：创建后看不到任何 Server；开放前授权被拒、直接调用成功次数 = 0；admin 开放后才可授权与调用。"""
    h.enable_runtime_projects(monkeypatch, tmp_path)
    srv = h.ready("crm", [tool("search")], projects=(P,))
    h.create_project("fresh_proj")
    h.api.add_user("ed_fresh", "fresh_proj", "edit")
    assert h.api.get("/api/mcp/servers", who="ed_fresh", project=None, force_header=True).json_body["items"] == []
    n = h.n_calls(srv)
    assert h.invoke(EXT, project="fresh_proj").ok is False and h.n_calls(srv) == n
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT)}, who="ed_fresh", project="fresh_proj") if False else (None, None)
    from advisor_r28_support import advisor_prompts
    from config_r26_support import publish_body

    cur = h.deps.publish_service.current("fresh_proj").definition
    import dataclasses

    from ib.config import semantic_hash
    from ib.core import ToolGrantSpec

    grants = tuple(dataclasses.replace(g, tool_names=g.tool_names + (EXT,)) if g.expert_name == "kb-agent" else g for g in cur.tool_grants)
    doc = dataclasses.replace(cur, tool_grants=grants)
    doc = dataclasses.replace(doc, content_hash=semantic_hash(doc))
    head = h.api.get("/api/config/status", who="ed_fresh", project=None, force_header=True).json_body["version"]
    body = publish_body(doc, head)
    bad = h.api.post("/api/config/publish", body, who="ed_fresh", project=None, force_header=True)
    assert bad.status_code == 400 and "mcp_server_not_open" in _codes(bad)
    h.open("crm", (P, "fresh_proj"))  # admin 显式开放给新建项目（须为活动项目）
    ok = h.api.post("/api/config/publish", body, who="ed_fresh", project=None, force_header=True)
    assert ok.status_code == 200, ok.json_body
    assert h.invoke(EXT, project="fresh_proj", turn="fp1").ok and h.n_calls(srv) == n + 1


def test_TC_INT_R29_1005_stale_grant_tolerated_on_unrelated_save_flagged_in_catalog_and_auto_recovers_AC_017_01_02_03_04(h, monkeypatch):
    srv = h.ready("crm", [tool("search")])
    h.grant(kb_agent=("search_knowledge", EXT))
    lease_before = h.deps.runtime_for(P)
    srv.mutate_tool("search", description="含新指令的描述")
    h.api.post("/api/mcp/servers/crm/refresh")
    assert h.b.stores.tools.get_by_local_name(EXT).state == "needs_rereview"
    # 配置页标注失效原因
    cat = h.api.get("/api/config/catalog", who="editor", project=None, force_header=True).json_body
    gs = [x for x in cat["mcp"]["grant_status"] if x["local_name"] == EXT]
    assert gs and gs[0]["valid"] is False and gs[0]["reason"] == "tool_needs_rereview"
    # 已缓存的旧装配仍在运行：调用被拒，出站 0（不依赖重启 / 下次保存）
    n = h.n_calls(srv)
    seen: dict = {}
    ScriptedLlm(h.deps, monkeypatch, scripts={"kb-agent": lambda c: seen.setdefault("r", c.use_tool(EXT, q="x")) and "KB", "advisor": lambda c: "ADV"})
    st, _, _ = chat(h.api, "退货期限", "s-stale")
    assert st == 200 and seen["r"] == MCP_PHRASES["tool_needs_rereview"] and h.n_calls(srv) == n
    # 修改无关配置（提示词文本）并保存：失效授权不触发整体拒绝；授权记录保留
    from advisor_r28_support import KB_PROMPT, advisor_document, advisor_prompts
    from config_r26_support import publish_body
    from ib.core import PromptLayers

    doc = advisor_document(P, grants={"kb-agent": ("search_knowledge", EXT)})
    prompts = advisor_prompts()
    prompts["kb-agent"] = PromptLayers(KB_PROMPT + " 另外请保持礼貌。", None)
    head = h.api.get("/api/config/status", who="editor", project=None, force_header=True).json_body["version"]
    ok = h.api.post("/api/config/publish", publish_body(doc, head, prompts), who="editor", project=None, force_header=True)
    assert ok.status_code == 200, ok.json_body
    assert EXT in [t for g in h.deps.publish_service.current(P).definition.tool_grants for t in g.tool_names]
    # 复审通过 ⇒ 授权自动恢复；新装配下调用成功（AC-017-03 / 013-04）
    h.approve(EXT)
    h.settle()  # 复审通过会触发后台 refresh_async；等其结束后再断言新装配已绑定新指纹
    seen.clear()
    st2, _, _ = chat(h.api, "退货期限", "s-recover")
    assert st2 == 200 and seen["r"].startswith(FENCE_OPEN) and h.n_calls(srv) == n + 1
    assert lease_before is not None


def test_TC_INT_R29_1006_dangling_grant_tolerated_at_compile_tool_dropped_AC_005_05(h):
    """Server 被绕过清理地删除（脏数据）：编译容忍悬空授权——工具被剔除、编译成功、问答不失败。"""
    h.ready("crm", [tool("search")])
    h.grant(kb_agent=("search_knowledge", EXT))
    assert EXT in _tools_of(h, "kb-agent")
    h.b.stores.servers.delete_cascade("crm")
    h.settle()
    st = h.deps.runtime_cache.status(P)
    assert st.state == "ok" and st.last_error_code is None
    assert EXT not in _tools_of(h, "kb-agent") and "search_knowledge" in _tools_of(h, "kb-agent")


def test_TC_INT_R29_1007_registrar_store_failure_aborts_compile_keeps_old_snapshot_then_recovers(h, monkeypatch):
    """台账不可读 ⇒ 编译失败（fail-closed 且可见）、保留旧快照；恢复后自动编译成功。"""
    h.ready("crm", [tool("search")])
    h.grant(kb_agent=("search_knowledge", EXT))
    old_version = h.deps.runtime_for(P).compiled.version
    real = h.b.stores.tools.get_by_local_name

    def boom(name):
        raise RuntimeError("ledger down")

    monkeypatch.setattr(h.b.stores.tools, "get_by_local_name", boom)
    h.settle()
    st = h.deps.runtime_cache.status(P)
    assert st.applied_version == old_version and h.deps.runtime_for(P).compiled.version == old_version  # 旧快照仍在服务
    assert EXT in _tools_of(h, "kb-agent")
    monkeypatch.setattr(h.b.stores.tools, "get_by_local_name", real)
    h.deps.runtime_cache._entries[P].retry_at = 0.0  # 跳过退避等待（缓存内部时钟；不改判定逻辑）
    h.settle()
    assert h.deps.runtime_cache.status(P).state == "ok"


def test_TC_INT_R29_1008_external_param_whitelist_only_timeout_and_calls_AC_020_04(h):
    h.ready("crm", [tool("search")])
    from advisor_r28_support import advisor_document, advisor_prompts
    from config_r26_support import publish_body
    from ib.core import ToolParamValue

    def put(pname, val):
        d = advisor_document(P, grants={"kb-agent": ("search_knowledge", EXT)}, params={"kb-agent": (ToolParamValue(f"{EXT}.{pname}", val),)})
        head = h.api.get("/api/config/status", who="editor", project=None, force_header=True).json_body["version"]
        return h.api.post("/api/config/publish", publish_body(d, head, advisor_prompts()), who="editor", project=None, force_header=True)

    bad = put("q", "x")
    assert bad.status_code == 400 and "mcp_param_forbidden" in _codes(bad)  # 只允许两个限制参数
    assert put("mcp_timeout_s", "999").status_code == 400
    assert put("mcp_timeout_s", "0").status_code == 400
    assert put("mcp_timeout_s", "10").status_code == 200  # 正例：在上层上限内


def test_TC_INT_R29_1009_llm_visible_schema_hides_fixed_and_hidden_params_and_names_are_function_safe_AC_015_01(h):
    h.add("crm", [tool("search", props={"q": {"type": "string"}, "tenant": {"type": "string"}, "debug": {"type": "boolean"}}, required=("q", "tenant")),
                  tool("a" * 90, desc="超长名")])
    h.enable("crm")
    h.approve("mcp__crm__search", hidden=("debug",), ack=True)
    h.approve(h.tools("crm")[1]["local_name"] if h.tools("crm")[1]["local_name"] != "mcp__crm__search" else h.tools("crm")[0]["local_name"])
    h.open("crm", (P,))
    tid = h.tool_id("mcp__crm__search")
    assert h.api.put(f"/api/mcp/tools/{tid}/bindings/{P}", {"fixed_args": {"tenant": "a-001"}}).status_code == 200
    names = [t["local_name"] for t in h.tools("crm")]
    h.grant(kb_agent=("search_knowledge", *names))
    spec = None
    for t in h.deps.runtime_for(P).compiled.view.agents["kb-agent"].tools:
        if t.name == "mcp__crm__search":
            spec = t
    assert spec is not None
    params = getattr(spec, "parameters", None) or getattr(getattr(spec, "spec", None), "parameters", None)
    props = (params or {}).get("properties", {})
    assert "q" in props and "tenant" not in props and "debug" not in props, props  # 固定 / 屏蔽的参数 LLM 不可见
    for n in names:
        assert re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", n), n  # LLM 函数名字符集假设 A-R29-2（目标机探针见人工验证清单）


def test_TC_INT_R29_1010_advisor_granted_external_tool_callable_and_budgeted_per_turn_unauthorized_still_denied_DEF_R29_005(h, monkeypatch):
    """US-016 “授权给 kb-agent、顾问等 agent”：顾问被授权外部工具时调用成功，预算按用户回合计数（与非顾问 agent 一致：全局 5 次/回合，
    第 6 次起 turn_limit，替身只收到 5 次）；成对：顾问未授权时同样的调用仍被拒（替身 0 次，AC-016-04）。（DEF-R29-005 修复后翻转。）"""
    srv = h.ready("crm", [tool("search")])
    resp, _ = h.publish_http({"kb-agent": ("search_knowledge",), "advisor": (EXT,)}, who="editor")
    assert resp.status_code == 200, resp.json_body  # 保存通过
    outs: list = []
    ScriptedLlm(h.deps, monkeypatch, scripts={"kb-agent": lambda c: "KB", "advisor": lambda c: (outs.extend(c.use_tool(EXT, q="x") for _ in range(7)), "ADV")[1]})
    st, _, _ = chat(h.api, "你好", "adv1")
    assert st == 200 and EXT in [t.name for t in h.deps.runtime_for(P).compiled.view.agents["advisor"].tools]
    assert len(outs) == 7
    assert [o.startswith(FENCE_OPEN) and "ok:search" in o for o in outs[:5]] == [True] * 5, outs[:5]  # 前 5 次成功（围栏结果）
    assert outs[5] == MCP_PHRASES["turn_limit"] and outs[6] == MCP_PHRASES["turn_limit"], outs[5:]  # 回合预算：与非顾问一致
    assert MCP_PHRASES["no_turn_scope"] not in outs
    assert h.n_calls(srv) == 5

    # 成对：顾问未授权 ⇒ 仍被拒，替身 0 次
    h2 = make_harness(monkeypatch)
    srv2 = h2.ready("crm", [tool("search")])
    resp2, _ = h2.publish_http({"kb-agent": ("search_knowledge", EXT), "advisor": ()}, who="editor")
    assert resp2.status_code == 200, resp2.json_body
    seen: dict = {}
    ScriptedLlm(h2.deps, monkeypatch, scripts={"kb-agent": lambda c: "KB", "advisor": lambda c: seen.setdefault("r", c.use_tool(EXT, q="x")) and "ADV"})
    assert chat(h2.api, "你好", "adv2")[0] == 200
    assert EXT not in [t.name for t in h2.deps.runtime_for(P).compiled.view.agents["advisor"].tools]
    assert "未授权" in seen["r"] and not seen["r"].startswith(FENCE_OPEN) and h2.n_calls(srv2) == 0
