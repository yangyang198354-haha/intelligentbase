"""[REV-26 / GROUP_D] 三档权限（查看 / 编辑 / 管理）在 HTTP 层的服务端强制与跨项目隔离。

溯源：US-010（AC-010-01/02/03/04）、US-002（AC-002-03/04）、US-004 / AC-004-04、US-009 / AC-009-04、US-011 / AC-011-04（服务端部分）、
US-017 / AC-017-03、US-019 / AC-019-01、US-023 / AC-023-04、US-029 / AC-029-05、US-024 / AC-024-06、OQ-R26-A01。
层级：集成（真实账户体系 / 授权中间件 / 视图层）。走真实 Bearer 令牌，不使用框架“强制认证”捷径。
"""

from __future__ import annotations

import pytest
from config_r26_support import Api, publish_body, v2_with_billing

P, Q = "p_alpha", "p_beta"

READ_PATHS = ["/api/config/status", "/api/config/definition", "/api/config/catalog", "/api/config/versions",
              "/api/config/prompts", "/api/config/prompts/kb-agent/main"]


@pytest.fixture()
def api(accounts_app):
    deps, Client = accounts_app
    a = Api(deps, Client)
    for name, level in (("viewer", "view"), ("editor", "edit"), ("manager", "manage")):
        a.uid = getattr(a, "uid", {})
        a.uid[name] = a.add_user(name, P, level)
    a.add_user("beta_mgr", Q, "manage")
    return a


def _denied(resp, need):
    assert resp.status_code == 403, (resp.status_code, resp.content[:200])
    assert resp.json_body["error"]["code"] == "permission_denied"
    assert resp.json_body["error"]["required_level"] == need


def _write_calls(api):
    doc, prompts = v2_with_billing(api.deps, P)
    body = publish_body(doc, 0, prompts)
    return {
        "validate": lambda who: api.post("/api/config/validate", body, who=who),
        "preview": lambda who: api.post("/api/config/publish/preview", body, who=who),
        "publish": lambda who: api.post("/api/config/publish", body, who=who),
        "drafts": lambda who: api.post("/api/config/drafts", {"label": "x", "base_version": 0, "document": body["document"]}, who=who),
        "trial": lambda who: api.post("/api/config/trial", {**body, "query": "你好", "session_id": "s"}, who=who),
        "builder": lambda who: api.post("/api/builder/draft", {"requirement": "做一个客服助手"}, who=who),
        "builder_eval": lambda who: api.post("/api/builder/evaluate", {"draft": {}}, who=who),
        "prompt_put": lambda who: api.put("/api/config/prompts/kb-agent/main", {"content": "x", "expected_hash": ""}, who=who),
        "def_put": lambda who: api.put("/api/config/definition", {"document": body["document"]}, who=who),
    }


def test_TC_INT_R26_070_view_level_reads_everything_but_every_write_is_403_edit(api):
    """US-010 / AC-010-01、US-002 / AC-002-03、US-004 / AC-004-04、US-009 / AC-009-04、US-024 / AC-024-06、US-029 / AC-029-05：
    查看档可读图/提示词全文/版本；所有写接口（含 Builder、试运行、旧提示词保存）直接调用均 403，响应含所需档位“edit”。"""
    for p in READ_PATHS:
        r = api.get(p, who="viewer")
        assert r.status_code == 200, (p, r.status_code)
    assert api.get("/api/config/prompts/kb-agent/main", who="viewer").json_body["content"]
    for name, call in _write_calls(api).items():
        _denied(call("viewer"), "edit")
    assert api.get("/api/config/status", who="viewer").json_body["version"] == 0, "403 之后配置未变"


def test_TC_INT_R26_071_view_and_edit_cannot_use_manage_actions(api):
    """US-017 / AC-017-03、US-023 / AC-023-04、US-010：回滚 / 采纳漂移 / 档位管理 / 审计只有管理档；编辑档 → 403 所需档位“manage”。"""
    for who in ("viewer", "editor"):
        _denied(api.post("/api/config/rollback", {"target_version": 1, "base_version": 0}, who=who), "manage")
        _denied(api.post("/api/config/adopt-drift", {"base_version": 0}, who=who), "manage")
        _denied(api.get("/api/config/access", who=who), "manage")
        _denied(api.put(f"/api/config/access/{api.uid['viewer']}", {"config_level": "edit"}, who=who), "manage")
        _denied(api.get("/api/config/audit", who=who), "manage")


def test_TC_INT_R26_072_edit_level_can_write(api):
    """US-010：编辑档可校验 / 预览 / 保存 / 存草稿 / 试运行 / 调用 Builder（Builder 在无 LLM Key 的离线替身下返回的是业务错误而非 403）。"""
    calls = _write_calls(api)
    assert calls["validate"]("editor").status_code == 200
    assert calls["preview"]("editor").status_code == 200
    assert calls["drafts"]("editor").status_code == 201
    assert calls["trial"]("editor").status_code == 200
    assert calls["builder"]("editor").status_code != 403
    assert calls["publish"]("editor").status_code == 200


def test_TC_INT_R26_073_manager_grants_level_with_audit_and_effect(api):
    """US-010 / AC-010-02（重点）：管理档把 viewer 由“查看”改为“编辑” → viewer 重新请求即可保存；审计新增 1 条 access.grant：
    操作人、目标账号、变更前档位“view”、变更后档位“edit”、时间。"""
    uid = api.uid["viewer"]
    _denied(api.post("/api/config/validate", {"base_version": 0, "document": {}}, who="viewer"), "edit")
    r = api.put(f"/api/config/access/{uid}", {"config_level": "edit"}, who="manager")
    assert r.status_code == 200 and r.json_body["config_level"] == "edit"
    doc, prompts = v2_with_billing(api.deps, P)
    assert api.post("/api/config/publish", publish_body(doc, 0, prompts), who="viewer").status_code == 200
    rows = [i for i in api.get("/api/config/audit?action=access.grant&limit=500", who="manager").json_body["items"]
            if f"user:{uid}" in i["object_summary"] and "to:edit" in i["object_summary"]]
    assert len(rows) == 1
    assert "from:view" in rows[0]["object_summary"] and rows[0]["actor"] == api.uid["manager"] and rows[0]["timestamp"]
    listed = {i["username"]: i["config_level"] for i in api.get("/api/config/access", who="manager").json_body["items"]}
    assert listed["viewer"] == "edit" and listed["editor"] == "edit" and listed["manager"] == "manage"


def test_TC_INT_R26_074_grant_validation_and_last_manager_protection(api):
    """US-010：非法档位 400；不存在 / 他项目账号 404；不能降级本项目最后一个管理档账号（409 last_manager）。"""
    mid = api.uid["manager"]
    assert api.put(f"/api/config/access/{mid}", {"config_level": "root"}, who="manager").status_code == 400
    assert api.put("/api/config/access/ghost-user", {"config_level": "view"}, who="manager").status_code == 404
    beta_uid = next(i["user_id"] for i in api.get("/api/accounts?project_id=p_beta", who="admin").json_body["items"])
    assert api.put(f"/api/config/access/{beta_uid}", {"config_level": "view"}, who="manager").status_code == 404
    last = api.put(f"/api/config/access/{mid}", {"config_level": "view"}, who="manager")
    assert last.status_code == 409 and last.json_body["error"]["code"] == "last_manager"
    assert next(i for i in api.get("/api/config/access", who="manager").json_body["items"] if i["user_id"] == mid)["config_level"] == "manage"


def test_TC_INT_R26_075_cross_project_writes_never_touch_other_project(api):
    """US-010 / AC-010-04（重点）：项目 A 的编辑档账号对项目 B 发起写请求（请求体与请求头都声明项目 B）→ 按其已认证项目归属处理或被拒，
    项目 B 的任何配置不变。"""
    doc, prompts = v2_with_billing(api.deps, P)
    body = publish_body(doc, 0, prompts)
    body["project_id"] = Q
    body["document"]["project_id"] = Q
    # 头部声明项目 B → 与令牌归属不一致 → 403
    hdr = api.call("POST", "/api/config/publish", "editor", body, project=Q, force_header=True)
    assert hdr.status_code == 403 and hdr.json_body["error"]["code"] == "project_mismatch"
    # 仅请求体声明项目 B → 忽略，按已认证项目 A 处理
    ok = api.post("/api/config/publish", body, who="editor")
    assert ok.status_code == 200
    assert api.get("/api/config/status", who="beta_mgr").json_body["version"] == 0
    beta_doc = api.get("/api/config/definition", who="beta_mgr").json_body["document"]
    assert [e["name"] for e in beta_doc["experts"]] == ["kb-agent"] and beta_doc["project_id"] == Q
    assert api.get("/api/config/versions", who="beta_mgr").json_body["items"] == []
    assert api.get("/api/config/status", who="editor").json_body["version"] == 2


def test_TC_INT_R26_076_other_project_account_cannot_read_and_response_does_not_leak_names(api):
    """US-010 / AC-010-03、US-019 / AC-019-01、US-002 / AC-002-04：他项目账号读取本项目的定义/提示词/版本历史/审计 → 403，
    响应不含本项目内的专家名，也不区分“不存在”与“不属于你”。"""
    doc, prompts = v2_with_billing(api.deps, P)
    assert api.post("/api/config/publish", publish_body(doc, 0, prompts), who="editor").status_code == 200
    forbidden = ["/api/config/definition", "/api/config/prompts", "/api/config/prompts/billing-agent/main",
                 "/api/config/versions", "/api/config/versions/2", "/api/config/audit", "/api/config/status"]
    seen = set()
    for p in forbidden:
        r = api.call("GET", p, "beta_mgr", project=P, force_header=True)
        assert r.status_code == 403, (p, r.status_code)
        text = r.content.decode("utf-8")
        assert "billing-agent" not in text and "账单助手" not in text
        seen.add(r.json_body["error"]["code"])
    assert seen == {"project_mismatch"}
    ghost = api.call("GET", "/api/config/prompts/no-such-agent/main", "beta_mgr", project=P, force_header=True)
    assert ghost.status_code == 403 and ghost.json_body == api.call(
        "GET", "/api/config/prompts/billing-agent/main", "beta_mgr", project=P, force_header=True).json_body


def test_TC_INT_R26_077_admin_is_always_manage_and_needs_project_selection(api):
    """OQ-R26-A01 / ADR-60：admin 恒为管理档（经 X-IB-Project 选定项目）；未选定项目 → 不得越界读取（4xx）。"""
    s = api.get("/api/config/status", who="admin", project=P).json_body
    assert s["level"] == "manage"
    r = api.get("/api/config/status", who="admin", project=None)
    assert r.status_code in (400, 403, 404, 422), r.status_code
    assert api.get("/api/config/audit", who="admin", project=Q).status_code == 200


def test_TC_INT_R26_078_new_account_default_level_is_manage_and_invalid_level_rejected(api):
    """OQ-R26-A01：账号创建缺省档位 manage（存量 ops 口径）；显式非法档位 → 400。"""
    api.add_user("legacy_like", P, "manage")
    assert api.get("/api/config/status", who="legacy_like").json_body["level"] == "manage"
    from conftest import bearer

    r = api.client.post("/api/accounts", data='{"username":"nolevel","password":"R26-Test-User-Init-1!","project_id":"p_alpha"}',
                        content_type="application/json", **bearer(api.tokens["admin"]))
    assert r.status_code == 201 and r.json()["config_level"] == "manage"
    bad = api.client.post("/api/accounts", data='{"username":"badlvl","password":"R26-Test-User-Init-1!","project_id":"p_alpha","config_level":"root"}',
                          content_type="application/json", **bearer(api.tokens["admin"]))
    assert bad.status_code == 400


def test_TC_INT_R26_079_unauthenticated_and_wrong_token_get_401_not_config(api):
    """US-019：无令牌 / 伪造令牌访问配置端点 → 401，不泄露任何配置内容（走真实中间件，不用强制认证捷径）。"""
    from django.test import Client

    c = Client()
    for p in ("/api/config/status", "/api/config/definition", "/api/builder/draft", "/api/config/audit"):
        r = c.get(p)
        assert r.status_code == 401 and b"kb-agent" not in r.content
    r2 = c.get("/api/config/status", HTTP_AUTHORIZATION="Bearer forged-token-value")
    assert r2.status_code == 401
    r3 = c.get("/api/config/status?token=" + api.tokens["editor"])  # 令牌放查询串无效
    assert r3.status_code in (400, 401) and b"kb-agent" not in r3.content   # 令牌不得经查询串传递：被拒（实测 400）
