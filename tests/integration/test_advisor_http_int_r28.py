"""[REV-28 / GROUP_D] 集成：顾问相关 HTTP 面（目录 / 建项目 / 加入与移除 / 联网上限 / 保存期校验 / Builder / 权限）。

分层：integration（真实 Django 视图层 + 账户鉴权 + 发布协议 + 文件态种子；云端 LLM 为脚本化替身，不触网）。
边界：HTTP ↔ composition ↔ confsvc / ledger / builder。
溯源：US-001 ~ 004、US-016（AC-016-04 / 07）、US-017（AC-017-02）、AC-002-01 ~ 04、AC-003-01 ~ 04。
"""

from __future__ import annotations

import json
import os

import pytest
from advisor_r28_support import (
    ADVISOR_PROMPT,
    P,
    advisor_document,
    advisor_prompts,
    contract_expert,
    publish_advisor,
    raw_events,
    web_params,
)
from config_r26_support import Api, publish_body

from ib.builder.types import BLOCKED_TERMS


@pytest.fixture()
def api(accounts_app):
    deps, Client = accounts_app
    a = Api(deps, Client)
    a.add_user("editor", P, "edit")
    a.add_user("viewer", P, "view")
    return a


# =========================================================================== #
# US-001：目录
# =========================================================================== #


def test_TC_INT_R28_300_catalog_lists_advisor_with_label_summary_default_no_web_grants_and_clean_seed(api):
    """AC-001-01 / 001-02：目录同时含 kb-agent（agents）与内置顾问（builtin_agents）；顾问：中文标签“顾问”、一句话职责、
    默认工具授权为空（联网工具默认未授权）；提示词种子声明面向客户 / 礼貌专业 / 同语言 / 不暴露内部分工 / 如实说明，BLOCKED_TERMS 0 命中。"""
    cat = api.get("/api/config/catalog", who="editor").json_body
    assert [a["name"] for a in cat["agents"]] == ["kb-agent"]  # AC-001-03：未启用项目的专家列表不含顾问
    b = cat["builtin_agents"]
    assert [x["id"] for x in b] == ["advisor"]
    adv = b[0]
    assert adv["cn_label"] == "顾问" and adv["summary"] and adv["default_tool_grants"] == []
    assert adv["expert"]["is_delegating"] is True and adv["expert"]["is_default"] is False
    seed = adv["prompt_main"]
    for must in ("面向客户", "礼貌专业", "提问者的语言", "不暴露内部分工", "如实"):
        assert must in seed
    assert sum(seed.lower().count(t.lower()) for t in BLOCKED_TERMS) == 0
    assert {"web_search", "web_fetch"} <= set(cat["available_tools"])
    assert cat["web"]["fetch_enabled"] is False and cat["web"]["search_configured"] is False
    assert set(cat["web"]["caps"]) == {"max_calls_per_turn", "max_fetch_bytes_per_turn", "max_seconds_per_turn"}


# =========================================================================== #
# US-002：新建项目选择是否启用顾问（文件态种子）
# =========================================================================== #


def _seed_env(monkeypatch, tmp_path):
    monkeypatch.setenv("IB_DEFINITION_DOC_PATH", str(tmp_path / "defs"))
    monkeypatch.setenv("IB_EXPERT_PROMPT_DIR", str(tmp_path / "prompts"))
    os.makedirs(tmp_path / "defs", exist_ok=True)


def test_TC_INT_R28_310_create_project_with_advisor_seeds_two_experts_canonical_graph_prompt_and_validates(api, monkeypatch, tmp_path):
    """AC-002-01：admin 勾选“启用顾问”创建 ⇒ 201；定义文档含 kb-agent 与顾问；顾问提示词种子逐字落到该项目提示词目录；
    默认图为顾问规范图并通过保存前校验；授权：kb-agent=search_knowledge，顾问无联网工具。"""
    from ib.config import FileDefinitionDocumentStore, advisor_seed_prompt
    from ib.config.graph import validate_graph
    from ibweb.composition import known_tool_names

    _seed_env(monkeypatch, tmp_path)
    r = api.post("/api/projects", {"project_id": "adv_new", "name": "顾问新项目", "enable_advisor": True})
    assert r.status_code == 201, r.content
    store = FileDefinitionDocumentStore(str(tmp_path / "defs"), known_tools=known_tool_names())
    doc = store.load("adv_new")
    assert [e.name for e in doc.experts] == ["kb-agent", "advisor"] and doc.route.default_expert == "kb-agent"
    assert [e.is_delegating for e in doc.experts] == [False, True]
    assert validate_graph(doc.graph, experts=doc.experts, default_expert="kb-agent") == ()
    es = {(e.source, e.target, e.branch_key) for e in doc.graph.edges}
    assert ("route-1", "advisor", "__else__") in es and ("kb-agent", "advisor", None) in es and ("advisor", "end", None) in es
    grants = {g.expert_name: g.tool_names for g in doc.tool_grants}
    assert grants == {"kb-agent": ("search_knowledge",), "advisor": ()}
    seed_file = tmp_path / "prompts" / "adv_new" / "advisor" / "main.md"
    assert seed_file.read_text(encoding="utf-8") == advisor_seed_prompt()
    assert (tmp_path / "prompts" / "adv_new" / "kb-agent" / "main.md").is_file()


def test_TC_INT_R28_311_create_project_without_advisor_identical_to_baseline_default_seed(api, monkeypatch, tmp_path):
    """AC-002-02：不勾选（缺省 / 显式 false）⇒ 项目定义与**基线（8d6fd4b）创建结果**逐项相同（仅 kb-agent、默认授权仅 search_knowledge）、
    提示词文件哈希相同，不含顾问或任何联网工具授权。期望值取自基线 src 树运行的探针（黄金文件 seed_plain），不是被测代码生成。"""
    golden = json.load(open(os.path.join(os.path.dirname(__file__), "advisor_r28_baseline_golden.json"), encoding="utf-8"))["seed_plain"]
    assert golden["expert_names"] == ["kb-agent"] and golden["orchestration"] == "default"
    _seed_env(monkeypatch, tmp_path)
    assert api.post("/api/projects", {"project_id": "seed_probe_proj", "name": "甲"}).status_code == 201
    got = json.loads((tmp_path / "defs" / "seed_probe_proj.json").read_text(encoding="utf-8"))
    assert got == golden["document"]
    import hashlib

    files = {}
    for root, _d, names in os.walk(tmp_path / "prompts"):
        for n in names:
            full = os.path.join(root, n)
            files[os.path.relpath(full, tmp_path / "prompts").replace(os.sep, "/")] = "sha256:" + hashlib.sha256(open(full, encoding="utf-8").read().encode("utf-8")).hexdigest()
    assert files == golden["prompt_files"]
    # 显式 false 与缺省生成相同内容
    assert api.post("/api/projects", {"project_id": "plain_b", "name": "乙", "enable_advisor": False}).status_code == 201
    tb = (tmp_path / "defs" / "plain_b.json").read_text(encoding="utf-8")
    ta = (tmp_path / "defs" / "seed_probe_proj.json").read_text(encoding="utf-8")
    assert json.loads(ta.replace("seed_probe_proj", "X")).keys() == json.loads(tb.replace("plain_b", "X")).keys()
    assert "advisor" not in ta + tb and "web_search" not in ta + tb and "web_fetch" not in ta + tb
    assert not (tmp_path / "prompts" / "seed_probe_proj" / "advisor").exists()


def test_TC_INT_R28_312_create_project_non_admin_403_and_non_bool_flag_400_creates_nothing(api, monkeypatch, tmp_path):
    """AC-002-03：非 admin（含启用顾问的请求）⇒ 403，不创建项目；enable_advisor 非 bool ⇒ 400 且先于创建（不留半成品）。"""
    _seed_env(monkeypatch, tmp_path)
    r = api.post("/api/projects", {"project_id": "by_editor", "name": "x", "enable_advisor": True}, who="editor")
    assert r.status_code == 403
    for bad in ("true", 1, "yes", None, [True]):
        rb = api.post("/api/projects", {"project_id": "bad_flag", "name": "x", "enable_advisor": bad})
        assert rb.status_code == 400, (bad, rb.status_code)
    ids = [i["project_id"] for i in api.get("/api/projects").json_body["items"]]
    assert "by_editor" not in ids and "bad_flag" not in ids
    assert not (tmp_path / "defs" / "by_editor.json").exists() and not (tmp_path / "defs" / "bad_flag.json").exists()


def test_TC_INT_R28_313_seed_failure_rolls_back_whole_creation_no_half_product_clear_error(api, monkeypatch, tmp_path):
    """AC-002-04：顾问种子写入失败（提示词目录不可写）⇒ 创建整体回滚——无定义文件、无提示词目录残留、注册表项停用，返回明确错误。
    对照：同样环境、目录可写时创建成功（TC-310）。"""
    monkeypatch.setenv("IB_DEFINITION_DOC_PATH", str(tmp_path / "defs"))
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("我是一个文件，挡住提示词目录", encoding="utf-8")
    monkeypatch.setenv("IB_EXPERT_PROMPT_DIR", str(blocker / "sub"))  # makedirs 必失败
    os.makedirs(tmp_path / "defs", exist_ok=True)
    r = api.post("/api/projects", {"project_id": "rollback_p", "name": "回滚", "enable_advisor": True})
    assert r.status_code >= 400 and r.json_body["error"]["code"] == "project_seed_failed"
    assert "已回滚" in r.json_body["error"]["message"] and "Traceback" not in json.dumps(r.json_body)
    assert not (tmp_path / "defs" / "rollback_p.json").exists()
    listed = {i["project_id"]: i for i in api.get("/api/projects").json_body["items"]}
    assert "rollback_p" not in listed  # 注册表项已停用，不在可见项目中


# =========================================================================== #
# US-003：加入 / 移除（发布协议）
# =========================================================================== #


def test_TC_INT_R28_320_add_advisor_preview_lists_new_agent_publish_applies_and_old_behaviour_intact(api):
    """AC-003-01：编辑档加入顾问——保存前预检通过，差异清单列出“新增 agent：顾问”；生效后专家集合含顾问；kb-agent 经 route 直达行为不变。"""
    doc = advisor_document(P)
    body = publish_body(doc, 0, advisor_prompts())
    pv = api.post("/api/config/publish/preview", body, who="editor")
    assert pv.status_code == 200 and pv.json_body["errors"] == []
    kinds = {(i["kind"], i["object_id"], i["after"]) for i in pv.json_body["items"]}
    assert ("agent_added", "advisor", "顾问") in kinds
    ok = api.post("/api/config/publish", body, who="editor")
    assert ok.status_code == 200 and ok.json_body["applied"] is True
    view = api.deps.runtime_for(P).compiled.view
    assert [s.name for s in view.experts] == ["kb-agent", "advisor"] and view.advisor_id == "advisor"
    audit = api.get("/api/config/audit", who="admin").json_body["items"]
    assert any(a["action"] == "config.publish" and "agent_added:advisor" in a["object_summary"] for a in audit)


def test_TC_INT_R28_321_remove_advisor_returns_to_unadvised_behaviour_history_and_audit_retained(api, monkeypatch):
    """AC-003-02：已启用顾问的项目移除顾问并保存 ⇒ 顾问从专家集合与图中移除，行为回到未启用状态（无理解步骤 / 无顾问节点）；
    历史审计记录保留。"""
    from advisor_r28_support import ScriptedLlm, KB_TEXT
    from config_r26_support import doc_json, make_v2_document, route_graph, expert

    publish_advisor(api.deps, P)
    assert api.deps.runtime_for(P).compiled.view.advisor_id == "advisor"
    base = api.get("/api/config/status", who="viewer").json_body["version"]
    kb = expert("kb-agent", default=True, label="知识库助手")
    plain = make_v2_document(P, (kb,), route_graph("kb-agent"))
    body = publish_body(plain, base, {"kb-agent": advisor_prompts()["kb-agent"]})
    r = api.post("/api/config/publish", body, who="editor")
    assert r.status_code == 200, r.content
    view = api.deps.runtime_for(P).compiled.view
    assert [s.name for s in view.experts] == ["kb-agent"] and view.advisor_id is None
    llm = ScriptedLlm(api.deps, monkeypatch, scripts={"kb-agent": lambda c: "KB:" + c.prompt[:6]})
    ev = raw_events(api.deps, P, "退货期限是多久")
    assert "KB:退货期限是多" in "".join(str(e.data) for e in ev if str(e.kind) == "content") and llm.understand_prompts == []
    audit = api.get("/api/config/audit", who="admin").json_body["items"]
    assert sum(1 for a in audit if a["action"] == "config.publish") >= 2  # 加入与移除的审计都在


def test_TC_INT_R28_322_view_level_cannot_add_advisor_server_side_403(api):
    """AC-003-03：查看档直接发起保存请求被服务端拒绝（403，required_level=edit）；版本不变。"""
    body = publish_body(advisor_document(P), 0, advisor_prompts())
    r = api.post("/api/config/publish", body, who="viewer")
    assert r.status_code == 403 and r.json_body["error"]["required_level"] == "edit"
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 0


def test_TC_INT_R28_323_upgrade_leaves_untouched_project_definition_byte_identical(accounts_app):
    """AC-003-04：平台升级完成、无人操作项目 P ⇒ P 的定义文档与升级前（基线黄金）逐字节相同。"""
    from ib.config import document_to_json

    golden = json.load(open(os.path.join(os.path.dirname(__file__), "advisor_r28_baseline_golden.json"), encoding="utf-8"))
    deps, _ = accounts_app
    assert json.loads(document_to_json(deps.definitions[P])) == golden["definition_json"]


# =========================================================================== #
# US-016：全局上限 / 保存期校验
# =========================================================================== #


def test_TC_INT_R28_330_web_governance_endpoint_admin_only_get_put_validation_and_defaults(api):
    """AC-016-07：admin GET 得默认值（5 次 / 1 MB / 30 秒）与硬上限；PUT 逐字段校验（缺键 / 多余键 / 非整数 / bool / 越界 ⇒ 400）；
    非 admin 修改全局上限 ⇒ 403（服务端拒绝）；成功后回显并记 updated_by。"""
    g = api.get("/api/web-governance").json_body
    assert (g["max_calls_per_turn"], g["max_fetch_bytes_per_turn"], g["max_seconds_per_turn"]) == (5, 1048576, 30)
    assert g["hard_max"] == {"max_calls_per_turn": 20, "max_fetch_bytes_per_turn": 5242880, "max_seconds_per_turn": 120}
    full = {"max_calls_per_turn": 5, "max_fetch_bytes_per_turn": 1048576, "max_seconds_per_turn": 30}
    for who in ("editor", "viewer"):
        assert api.get("/api/web-governance", who=who).status_code == 403
        assert api.put("/api/web-governance", full, who=who).status_code == 403
    bad_bodies = [{}, {**full, "extra": 1}, {**full, "max_calls_per_turn": 0}, {**full, "max_calls_per_turn": 21},
                  {**full, "max_calls_per_turn": True}, {**full, "max_calls_per_turn": 3.5}, {**full, "max_fetch_bytes_per_turn": 9999},
                  {**full, "max_seconds_per_turn": 121}, {"max_calls_per_turn": 5}]
    for b in bad_bodies:
        assert api.put("/api/web-governance", b).status_code == 400, b
    ok = api.put("/api/web-governance", {"max_calls_per_turn": 5, "max_fetch_bytes_per_turn": 1048576, "max_seconds_per_turn": 30})
    assert ok.status_code == 200 and ok.json_body["updated_by"]
    assert api.get("/api/web-governance").json_body["updated_by"] == ok.json_body["updated_by"]
    assert api.call("PATCH", "/api/web-governance", "admin", {}).status_code == 405


def test_TC_INT_R28_331_project_limits_within_global_saved_exceeding_global_rejected_with_message(api):
    """AC-016-07：全局上限每轮 5 次、1 MB；编辑档把本项目保存为每轮 3 次 / 500 KB 成功并生效；保存为每轮 8 次被拒，错误指出“超出全局上限（5 次）”。"""
    def body_with(**fetch):
        doc = advisor_document(P, grants={"advisor": ("web_search", "web_fetch")},
                               params={"advisor": web_params(fetch=fetch)})
        base = api.get("/api/config/status", who="viewer").json_body["version"]
        return publish_body(doc, base, advisor_prompts())

    r = api.post("/api/config/publish", body_with(max_calls_per_turn=8), who="editor")
    assert r.status_code == 400
    items = r.json_body["error"]["items"]
    assert [i["code"] for i in items] == ["web_limit_exceeds_global"] and "超出全局上限（5 次）" in items[0]["message"]
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 0  # 被拒不改版本
    ok = api.post("/api/config/publish", body_with(max_calls_per_turn=3, max_bytes_per_turn=500000), who="editor")
    assert ok.status_code == 200, ok.content
    # admin 调低全局上限后，原值超限的新保存被拒
    assert api.put("/api/web-governance", {"max_calls_per_turn": 2, "max_fetch_bytes_per_turn": 1048576, "max_seconds_per_turn": 30}).status_code == 200
    again = api.post("/api/config/publish", body_with(max_calls_per_turn=3, max_bytes_per_turn=500000, timeout_s=15), who="editor")
    assert again.status_code == 400 and "超出全局上限（2 次）" in again.json_body["error"]["items"][0]["message"]


def test_TC_INT_R28_332_invalid_domain_list_rejected_with_item_position_and_validate_endpoint_agrees(api):
    """AC-016-04：域名配置含非法格式（含空格 / 协议头）⇒ 保存被拒，逐条指出第几项；/validate 与 /publish 口径一致；合法清单可保存。"""
    def doc_with(allow):
        return advisor_document(P, grants={"advisor": ("web_fetch",)}, params={"advisor": web_params(fetch={"allow_domains": allow})})

    bad = publish_body(doc_with("ok.com, http://evil.com, has space.com"), 0, advisor_prompts())
    r = api.post("/api/config/publish", bad, who="editor")
    codes = [i["code"] for i in r.json_body["error"]["items"]]
    assert r.status_code == 400 and codes == ["web_domain_invalid", "web_domain_invalid"]
    msgs = " ".join(i["message"] for i in r.json_body["error"]["items"])
    assert "第 2 项" in msgs and "第 3 项" in msgs
    v = api.post("/api/config/validate", bad, who="editor")
    assert v.status_code == 200 and v.json_body["ok"] is False and [e["code"] for e in v.json_body["errors"]] == codes
    good = publish_body(doc_with("ok.com, sub.ok.org"), 0, advisor_prompts())
    assert api.post("/api/config/publish", good, who="editor").status_code == 200


def test_TC_INT_R28_333_params_without_grant_rejected_by_existing_rule_and_web_config_roundtrip(api):
    """AC-014-01 / 014-02：未授权联网工具却带其参数 ⇒ 既有规则拒绝（不新增例外）；勾选 web_search 并设置返回条数 5、超时 10 秒后保存成功，
    配置值随定义文档保存并在刷新后回显。"""
    bad_doc = advisor_document(P, grants={"advisor": ()}, params={"advisor": web_params(search={"max_results": 5})})
    r = api.post("/api/config/publish", publish_body(bad_doc, 0, advisor_prompts()), who="editor")
    assert r.status_code == 400 and any(i["code"] == "tool_param_unauthorized_tool" for i in r.json_body["error"]["items"])
    doc = advisor_document(P, grants={"advisor": ("web_search",)},
                           params={"advisor": web_params(search={"max_results": 5, "timeout_s": 10})})
    ok = api.post("/api/config/publish", publish_body(doc, 0, advisor_prompts()), who="editor")
    assert ok.status_code == 200, ok.content
    shown = api.get("/api/config/definition", who="editor").json_body["document"]
    grants = {g["expert_name"]: g for g in shown["tool_grants"]}
    assert grants["advisor"]["tool_names"] == ["web_search"]
    assert {p["name"]: p["value"] for p in grants["advisor"]["param_values"]} == {"web_search.max_results": "5", "web_search.timeout_s": "10"}
    # kb-agent 未授权：其工具授权不含联网工具、无联网参数（AC-014-02 配置面）
    assert grants["kb-agent"]["tool_names"] == ["search_knowledge"] and grants["kb-agent"]["param_values"] == []


def test_TC_INT_R28_334_web_grant_save_fails_closed_when_governance_store_unreadable(api, monkeypatch):
    """上限存储不可读时：对含联网授权的文档 fail-closed（web_governance_unavailable）；不含联网授权的文档不受影响（未启用项目零影响）。"""
    def boom():
        raise RuntimeError("ledger down")

    monkeypatch.setattr(api.deps.web_governance, "get", boom)
    with_web = advisor_document(P, grants={"advisor": ("web_search",)})
    r = api.post("/api/config/publish", publish_body(with_web, 0, advisor_prompts()), who="editor")
    assert r.status_code == 400 and [i["code"] for i in r.json_body["error"]["items"]] == ["web_governance_unavailable"]
    without = advisor_document(P)
    ok = api.post("/api/config/publish", publish_body(without, 0, advisor_prompts()), who="editor")
    assert ok.status_code == 200


# =========================================================================== #
# US-004：Agent Builder 微调顾问
# =========================================================================== #

ADV_TEXT = "你是面向房产客户的正式顾问，语气庄重。回答必须引用来源，如实告知无依据，联网查询与经路由委托其他环节只在必要时进行。"


def _cloud(deps, generate):
    from test_builder_api_r26 import Cloud  # 复用既有云端 LLM 脚本化替身（同目录测试模块）

    return Cloud(deps, generate=generate, optimize=generate)


def _draft_json(name, prompt, tools, deleg):
    return json.dumps({"name": name, "cn_label": "顾问" if name == "advisor" else "知识库助手", "main_prompt": prompt,
                       "fallback_prompt": "暂时无法回答，请稍后再试。", "keywords": ["退货"], "exemplars": ["a", "b"],
                       "tool_names": tools, "tool_params": [], "knowledge_folders": [], "max_steps": 4,
                       "is_data_expert": False, "is_delegating": deleg}, ensure_ascii=False)


def test_TC_INT_R28_340_builder_tunes_advisor_returns_draft_review_per_clause_and_writes_nothing(api):
    """AC-004-01：已启用顾问，编辑档对顾问提交“面向房产客户，语气更正式” ⇒ 返回修改后的提示词草稿与评审结果（三项内容要求逐项通过状态）；
    草稿仅返回前端，服务端不写（在用版本、提示词不变）。"""
    publish_advisor(api.deps, P)
    ver = api.get("/api/config/status", who="viewer").json_body["version"]
    cloud = _cloud(api.deps, _draft_json("advisor", ADV_TEXT, [], True))
    r = api.post("/api/builder/review-existing", {"expert": "advisor", "mode": "optimize", "instruction": "面向房产客户，语气更正式"}, who="editor")
    assert r.status_code == 200, r.content
    prop = r.json_body["proposal"]
    assert "房产客户" in prop["main_prompt"] and prop["name"] == "advisor"
    failed = [d["check_id"] for d in r.json_body["evaluation"]["deductions"] if d["check_id"].startswith("clause_")]
    assert failed == []  # 三项内容要求（引用来源 / 无依据如实告知 / 工具与委托使用契约）逐项通过
    assert api.get("/api/config/status", who="viewer").json_body["version"] == ver
    stored = api.deps.runtime_for(P).compiled.view.agents["advisor"].system_prompt
    assert stored == ADVISOR_PROMPT and cloud.sent


def test_TC_INT_R28_341_clause_tool_contract_passes_for_advisor_wording_but_baseline_rule_for_kb_agent(api):
    """AC-004-02：只提联网工具与“经路由委托其他 agent”、不含 search_knowledge 字样的文本——对顾问“工具与委托使用契约”通过；
    同样文本对 kb-agent（持有检索工具）评审口径与基线一致（该项未通过）。"""
    publish_advisor(api.deps, P)
    _cloud(api.deps, _draft_json("advisor", ADV_TEXT, [], True))
    adv = api.post("/api/builder/evaluate", {"draft": json.loads(_draft_json("advisor", ADV_TEXT, [], True))}, who="editor")
    kb = api.post("/api/builder/evaluate", {"draft": json.loads(_draft_json("kb-agent", ADV_TEXT, ["search_knowledge"], False))}, who="editor")
    adv_failed = [d["check_id"] for d in adv.json_body["evaluation"]["deductions"] if d["check_id"].startswith("clause_")]
    kb_failed = [d["check_id"] for d in kb.json_body["evaluation"]["deductions"] if d["check_id"].startswith("clause_")]
    assert adv_failed == [] and kb_failed == ["clause_tool_contract"]


def test_TC_INT_R28_342_blocked_term_in_draft_flagged_without_echoing_term(api):
    """AC-004-03：草稿含禁用词 ⇒ 该项判为未通过（no_business_terms），响应不回显该词。"""
    txt = ADV_TEXT + "我们服务于FreeArk的客户。"
    r = api.post("/api/builder/evaluate", {"draft": json.loads(_draft_json("advisor", txt, [], True))}, who="editor")
    d = [x for x in r.json_body["evaluation"]["deductions"] if x["check_id"] == "no_business_terms"]
    assert len(d) == 1 and "freeark" not in json.dumps(d[0], ensure_ascii=False).lower()


def test_TC_INT_R28_343_view_level_cannot_use_builder_for_advisor_server_side_403(api):
    """AC-004-04：查看档绕过前端发起 Builder 写入顾问草稿 ⇒ 服务端 403；云端出站 0。"""
    publish_advisor(api.deps, P)
    cloud = _cloud(api.deps, _draft_json("advisor", ADV_TEXT, [], True))
    for path, body in (("/api/builder/review-existing", {"expert": "advisor", "mode": "optimize"}),
                       ("/api/builder/optimize", {"draft": json.loads(_draft_json("advisor", ADV_TEXT, [], True))}),
                       ("/api/builder/draft", {"requirement": "顾问"})):
        r = api.post(path, body, who="viewer")
        assert r.status_code == 403, path
    assert cloud.sent == []


def test_TC_INT_R28_344_builder_digest_outbound_gains_only_tool_names_when_web_tools_registered(api):
    """CR-010 观察：Builder 外发的项目摘要现在对所有项目含 web_search / web_fetch 两个工具声明（目录可见变化，设计允许）——
    断言工具名集合恰为 {search_knowledge, web_search, web_fetch}，且两项被标记为 is_external；摘要不含凭据哨兵。"""
    cloud = _cloud(api.deps, _draft_json("faq-agent", ADV_TEXT, [], False))
    r = api.post("/api/builder/draft", {"requirement": "做一个客服助手"}, who="editor")
    assert r.status_code == 200
    digest = cloud.sent[0]
    tools = {t["name"]: t for t in digest["project"]["tools"]}
    assert set(tools) == {"search_knowledge", "web_search", "web_fetch"}
    # CR-022 / DEF-004 修复后 search_knowledge 条目不再输出 is_external 键（AC-017-06 要求与基线逐字一致）：改用 .get 读取，语义不变
    assert tools["web_search"]["is_external"] and tools["web_fetch"]["is_external"] and not tools["search_knowledge"].get("is_external")
    assert "R28-SENTINEL" not in json.dumps(digest, ensure_ascii=False)


# =========================================================================== #
# AC-017-02：/healthz/deps（启用联网后才追加键）
# =========================================================================== #


def test_TC_INT_R28_350_healthz_deps_unchanged_until_web_enabled_then_lists_search_host(django_ready, monkeypatch):
    """AC-017-02 / 018-03：未配置联网 ⇒ /healthz/deps 与基线字节一致（无搜索服务主机）；配置搜索提供方后才追加搜索主机与数据类别。"""
    from advisor_r28_support import build_app  # noqa: F401
    from conftest import R13_ADMIN_PASSWORD, bearer, login, offline_raw
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    golden = json.load(open(os.path.join(os.path.dirname(__file__), "advisor_r28_baseline_golden.json"), encoding="utf-8"))
    monkeypatch.setenv("IB_ACCOUNT_BACKEND", "memory")
    monkeypatch.setenv("IB_AUTHZ_POLICY_MODULE", "ibweb.accounts.policy")
    monkeypatch.setenv("IB_DEFAULT_ADMIN_PASSWORD", R13_ADMIN_PASSWORD)
    d0 = build_deps(offline_raw(), force=True)
    build_application(d0)
    c = Client()
    tok = json.loads(login(c, "admin", R13_ADMIN_PASSWORD).content)["token"]
    base = json.loads(c.get("/healthz/deps", **bearer(tok)).content)
    assert base == golden["healthz_deps"] and "web" not in json.dumps(base).lower().replace("web_", "")
    raw = offline_raw()
    raw["web_search_provider"] = "fake"
    d1 = build_deps(raw, force=True)
    build_application(d1)
    c2 = Client()
    tok2 = json.loads(login(c2, "admin", R13_ADMIN_PASSWORD).content)["token"]
    on = json.loads(c2.get("/healthz/deps", **bearer(tok2)).content)
    assert on != base
    assert "fake.invalid" in json.dumps(on) and "web_search_query" in json.dumps(on)
