"""[REV-26 / GROUP_D] E2E 关键路径（Must Have 故事的多步完整旅程；Django 测试客户端 + 真实账户体系 + 离线替身，无浏览器）。

critical path 口径：替代（后端多步 API 旅程；浏览器内交互无可用无头浏览器，见 e2e_test_report 的“未验证”清单）。
溯源：J1 = US-004/024/027/016/014/011/017/023；J2 = US-018/015/014；J3 = US-020/017；J4 = US-010/019/009。
"""

from __future__ import annotations

import json

from config_r26_support import Api, ExpertRecorder, BILLING_PROMPT, ask, publish_body, v2_with_billing
from folder_r25_support import put_file

from ib.core import PromptLayers

P, Q = "p_alpha", "p_beta"
GOOD = ("你是账单助手。命中资料时必须引用来源（文件名与位置）；检索不到依据时如实说明“未检索到”；凡涉及事实必须先调用检索工具 search_knowledge。")


def _cloud(deps):
    draft = {"name": "billing-agent", "cn_label": "账单助手", "main_prompt": GOOD, "fallback_prompt": "请稍后再试。",
             "keywords": ["发票", "报销"], "exemplars": ["发票怎么开", "怎么报销"], "tool_names": ["search_knowledge"],
             "tool_params": [], "knowledge_folders": [], "max_steps": 4}
    judge = {"checks": {c: {"pass": True, "quote": ""} for c in (
        "prompt_role_consistent", "prompt_no_contradiction", "prompt_no_guardrail_conflict")}}
    deps.llm.complete_output = lambda s, u: json.dumps(judge if json.loads(u)["kind"] == "judge" else draft, ensure_ascii=False)


def _team(accounts_app):
    deps, Client = accounts_app
    api = Api(deps, Client)
    api.add_user("editor", P, "edit")
    api.add_user("manager", P, "manage")
    api.add_user("viewer", P, "view")
    return deps, api


def test_TC_E2E_R26_001_builder_to_hot_effect_to_rollback_journey(accounts_app, monkeypatch):
    """J1（US-024/027/016/014/017/023，Must）：
    ① 编辑档用自然语言生成草案（不落盘）→ ② 修改草案并发起保存预览（差异含“新增 agent”）→ ③ 确认保存（热生效，无重启）→
    ④ 终端用户的新提问被路由到新 agent → ⑤ 管理档回滚 → ⑥ 新提问回到旧行为 → ⑦ 审计完整记录 生成外发/保存/回滚。"""
    deps, api = _team(accounts_app)
    rec = ExpertRecorder(deps, monkeypatch)
    _cloud(deps)
    d = api.post("/api/builder/draft", {"requirement": "做一个处理发票报销的客服助手"}, who="editor")
    assert d.status_code == 200 and d.json_body["draft"]["name"] == "billing-agent"            # ①
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 0
    doc, prompts = v2_with_billing(deps, P)
    prompts = {"billing-agent": PromptLayers(GOOD + "（用户修改）", None)}
    pv = api.post("/api/config/publish/preview", publish_body(doc, 0, prompts), who="editor")  # ②
    assert any(i["kind"] == "agent_added" and i["object_id"] == "billing-agent" for i in pv.json_body["items"])
    ok = api.post("/api/config/publish", publish_body(doc, 0, prompts), who="editor")           # ③
    assert ok.status_code == 200 and ok.json_body["applied"] is True
    rec.clear(); _k, ver = ask(deps, P, "我的发票怎么报销", "e1")                               # ④
    assert ver == 2 and rec.experts == ["billing-agent"] and rec.calls[0][1] == GOOD + "（用户修改）"
    rb = api.post("/api/config/rollback", {"target_version": 1, "base_version": 2, "message": "回退到基线"}, who="manager")  # ⑤
    assert rb.status_code == 200 and rb.json_body["version"] == 3
    rec.clear(); _k, ver = ask(deps, P, "我的发票怎么报销", "e2")                               # ⑥
    assert ver == 3 and rec.experts == ["kb-agent"]
    actions = [a["action"] for a in api.get("/api/config/audit?limit=500", who="manager").json_body["items"]]   # ⑦
    for needed in ("builder.egress", "config.publish", "config.rollback", "access.grant"):
        assert needed in actions, needed
    versions = api.get("/api/config/versions", who="viewer").json_body["items"]
    assert [v["version"] for v in versions] == [3, 2, 1] and versions[0]["summary"] == "回退到基线"


def test_TC_E2E_R26_002_concurrent_edit_conflict_journey(accounts_app, monkeypatch):
    """J2（US-018/015/014，Must）：甲乙基于同一版本编辑；甲先保存成功；乙保存 → 409 冲突回执；乙“另存草稿副本”→ 乙重新载入后基于新版本合并保存成功；
    甲的改动全程未被覆盖；进行中的回答（旧租约）不受影响。"""
    deps, api = _team(accounts_app)
    rec = ExpertRecorder(deps, monkeypatch)
    base = api.get("/api/config/status", who="editor").json_body["version"]
    inflight = deps.runtime_for(P)                                    # 某回答开始时持有的租约（版本 0）
    a_doc, a_pr = v2_with_billing(deps, P, max_steps=2)               # 甲
    assert api.post("/api/config/publish", publish_body(a_doc, base, a_pr), who="editor").status_code == 200
    b_doc, b_pr = v2_with_billing(deps, P, max_steps=6)               # 乙（仍基于 base）
    conflict = api.post("/api/config/publish", publish_body(b_doc, base, b_pr), who="manager")
    assert conflict.status_code == 409 and conflict.json_body["error"]["receipt"]["conflicts"]
    saved = api.post("/api/config/drafts", {"label": "乙的改动", "base_version": base, "document": publish_body(b_doc, base)["document"],
                                            "prompts": {"billing-agent": {"main": b_pr["billing-agent"].main}}}, who="manager")
    assert saved.status_code == 201
    head = api.get("/api/config/status", who="manager").json_body["version"]
    reloaded = api.get("/api/config/definition", who="manager").json_body["document"]
    assert next(e for e in reloaded["experts"] if e["name"] == "billing-agent")["max_steps"] == 2, "甲的改动在位"
    merged = json.loads(json.dumps(reloaded))
    for e in merged["experts"]:
        if e["name"] == "billing-agent":
            e["max_steps"] = 6
    ok = api.post("/api/config/publish", {"base_version": head, "document": merged}, who="manager")
    assert ok.status_code == 200 and ok.json_body["version"] == head + 1
    _k, v_old = ask(deps, P, "我的发票怎么报销", "inflight", lease=inflight)
    assert v_old == 0 and rec.experts[-1] == "kb-agent", "进行中的回答仍绑定开始时的版本"
    assert deps.runtime_for(P).compiled.version == head + 1


def test_TC_E2E_R26_003_legacy_project_upgrade_save_and_return_to_baseline_journey(accounts_app, monkeypatch):
    """J3（US-020/017，Must）：旧形态项目 ① 未保存即可正常提问（版本 0）→ ② 首次保存（先存升级前基线 v1，再存用户 v2）→
    ③ 管理档回滚到基线 v1 → ④ 行为与升级前等价（同样的提问由同样的专家作答）。"""
    deps, api = _team(accounts_app)
    rec = ExpertRecorder(deps, monkeypatch)
    qs = ["我的发票怎么报销", "知识库里有什么", "你好"]
    def run(tag):
        out = []
        for i, q in enumerate(qs):
            rec.clear(); ask(deps, P, q, f"{tag}{i}"); out.append(tuple(rec.experts))
        return out
    before = run("a")                                                                 # ①
    assert deps.runtime_for(P).compiled.version == 0
    doc, pr = v2_with_billing(deps, P)
    assert api.post("/api/config/publish", publish_body(doc, 0, pr), who="editor").json_body["version"] == 2      # ②
    assert [(v["version"], v["kind"]) for v in api.get("/api/config/versions", who="viewer").json_body["items"]] == [(2, "publish"), (1, "baseline")]
    assert run("b")[0] == ("billing-agent",)
    assert api.post("/api/config/rollback", {"target_version": 1, "base_version": 2}, who="manager").status_code == 200   # ③
    assert run("c") == before                                                         # ④


def test_TC_E2E_R26_004_permissions_and_cross_project_isolation_journey(accounts_app):
    """J4（US-010/019/009，Must）：查看档保存被拒 → 管理档升级其档位（审计）→ 该账号保存成功 → 另一项目 p_beta 全程不受影响且无法读到本项目内容。"""
    deps, api = _team(accounts_app)
    api.add_user("beta_mgr", Q, "manage")
    doc, pr = v2_with_billing(deps, P)
    body = publish_body(doc, 0, pr)
    denied = api.post("/api/config/publish", body, who="viewer")
    assert denied.status_code == 403 and denied.json_body["error"]["required_level"] == "edit"
    uid = next(i["user_id"] for i in api.get("/api/config/access", who="manager").json_body["items"] if i["username"] == "viewer")
    assert api.put(f"/api/config/access/{uid}", {"config_level": "edit"}, who="manager").status_code == 200
    assert api.post("/api/config/publish", body, who="viewer").status_code == 200
    grants = [a for a in api.get("/api/config/audit?action=access.grant&limit=500", who="manager").json_body["items"]
              if f"user:{uid}" in a["object_summary"] and "to:edit" in a["object_summary"]]
    assert len(grants) == 1
    assert api.get("/api/config/status", who="beta_mgr").json_body["version"] == 0
    leak = api.call("GET", "/api/config/definition", "beta_mgr", project=P, force_header=True)
    assert leak.status_code == 403 and b"billing-agent" not in leak.content
    beta = api.get("/api/config/definition", who="beta_mgr").json_body["document"]
    assert [e["name"] for e in beta["experts"]] == ["kb-agent"] and beta["project_id"] == Q
