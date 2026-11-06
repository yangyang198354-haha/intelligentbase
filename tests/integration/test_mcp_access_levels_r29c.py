"""[REV-29 / GROUP_D / 缺陷回流第 3 轮] 集成：访问控制 AC 口径同步（user_stories 3.0.0，CP-002 Q3=A）补强。

口径：匿名 → 401；项目 view / edit 档越权 → 403。AC-026-03 的正例“查询本项目审计”按**项目 manage 档（read_audit）**验证
（src/ibweb/mcp_views.py audit_endpoint：非 admin 须 config_views.require_level(request, "read_audit")；AC 原文“项目配置者”在此指 manage 档）。
分层：integration（真实账户鉴权 + 真实视图 + 真实 authz 档位表 + 内存台账 + 替身传输）。
"""

from __future__ import annotations

import json

import pytest
from mcp_r29_support import P, advisor_document, advisor_prompts, make_harness, publish_body, tool

EXT = "mcp__crm__search"


@pytest.fixture()
def h(monkeypatch):
    return make_harness(monkeypatch)


def test_TC_INT_R29_1110_anonymous_save_grants_401_view_403_edit_200_zero_change_AC_016_05(h):
    """AC-016-05：匿名保存授权 → 401；view 档 → 403；两种情形下配置版本与授权记录变化 = 0；edit 档保存成功（正例成对）。"""
    h.ready("crm", [tool("search")])
    ver0 = h.api.get("/api/config/status").json_body["version"]
    doc = advisor_document(P, grants={"kb-agent": ("search_knowledge", EXT), "advisor": ()})
    body = json.dumps(publish_body(doc, ver0, advisor_prompts()))
    anon = h.api.client.post("/api/config/publish", data=body, content_type="application/json", HTTP_X_IB_PROJECT=P)
    assert anon.status_code == 401
    viewer, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT), "advisor": ()}, who="viewer")
    assert viewer.status_code == 403
    assert h.api.get("/api/config/status").json_body["version"] == ver0, "越权保存后配置版本不变"
    assert h.b.stores.tools.get_by_local_name(EXT).state == "enabled"
    ok, _ = h.publish_http({"kb-agent": ("search_knowledge", EXT), "advisor": ()}, who="editor")
    assert ok.status_code == 200 and h.api.get("/api/config/status").json_body["version"] > ver0


def test_TC_INT_R29_1111_audit_manage_level_200_edit_view_403_anonymous_401_AC_026_03(h):
    """AC-026-03（3.0.0）：项目 manage 档（read_audit）查询只得本项目记录，他项目 0 条；edit / view 档 403；匿名 401；
    权限边界成对：同一请求仅档位不同，结果由 200 变 403。"""
    BETA = "p_beta"
    h.ready("crm", [tool("search")], projects=(P, BETA))
    for proj in (P, P, BETA):
        assert h.invoke(EXT, project=proj).ok
    r = h.api.get("/api/mcp/audit?kind=call", who="mgr_alpha", project=None, force_header=True)
    assert r.status_code == 200
    items = r.json_body["items"]
    assert r.json_body["total"] >= 2 and {i["project_id"] for i in items} == {P} and not any(i["project_id"] == BETA for i in items)
    for who in ("editor", "viewer"):
        assert h.api.get("/api/mcp/audit?kind=call", who=who, project=None, force_header=True).status_code == 403, who
    assert h.api.client.get("/api/mcp/audit?kind=call").status_code == 401
