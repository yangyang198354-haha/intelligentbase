"""E2E / 关键路径测试 —— R13 增量：账户体系完整用户旅程（离线装配）。

关键路径 = REV-13 的 Must Have 账户故事（US-IB-21 ~ US-IB-25、US-IB-27）。
每个用例在 docstring 标注所属 **US-IB-NN / AC-IB-NN-NN**（用户故事级覆盖的证据）。
离线约束：内存账户存储 + Django test Client，不触网。
"""

from __future__ import annotations

import json

from conftest import R13_ADMIN_PASSWORD, R13_OPS_PASSWORD, bearer, change_password, login

_ADMIN_NEW_PW = "GroupD-E2E-Admin-1!"
_OPS_NEW_PW = "GroupD-E2E-Ops-1!"


# --------------------------------------------------------------------------- #
# TC-E2E-020 账户体系完整旅程：首登改密 → 建ops → ops登录改密 → 项目内全功能 → 跨项目拒绝
# --------------------------------------------------------------------------- #


def test_TC_E2E_020_admin_to_ops_full_account_journey(accounts_app):
    """US-IB-21 + US-IB-22 + US-IB-23 + US-IB-24 + US-IB-25（关键路径）。

    旅程（每一步都是可观察断言）：
      ① admin 用初始口令登录 → 强制改密态；
      ② 改密前访问业务端点 → 403 `password_change_required`（服务端受限会话）；
      ③ 改密成功 → 业务端点放行；
      ④ admin 创建绑定 p_alpha 的 ops 账户；
      ⑤ ops 首登（强制改密）→ 改密；
      ⑥ ops 在绑定项目内完成**管理动作**（上传）→ 允许（全功能，非只读）；
      ⑦ ops 声明项目 B → 403（跨项目边界隔离）；
      ⑧ ops 登出 → 其令牌 401；admin 停用 ops → ops 无法再登录。
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    deps, Client = accounts_app
    client = Client()

    # ① 首登
    r = login(client, "admin", R13_ADMIN_PASSWORD)
    assert r.status_code == 200
    admin_token = json.loads(r.content)["token"]
    assert json.loads(r.content)["must_change_password"] is True

    # ② 改密前受限
    blocked = client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(admin_token))
    assert blocked.status_code == 403
    assert json.loads(blocked.content)["error"]["code"] == "password_change_required"

    # ③ 改密放行
    assert change_password(client, admin_token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW).status_code == 200
    assert client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(admin_token)).status_code == 200

    # ④ 建 ops（绑定 p_alpha）
    created = client.post(
        "/api/accounts",
        data=json.dumps({"username": "ops_j", "password": R13_OPS_PASSWORD, "project_id": "p_alpha"}),
        content_type="application/json",
        **bearer(admin_token),
    )
    assert created.status_code == 201
    assert json.loads(created.content)["project_id"] == "p_alpha"

    # ⑤ ops 首登 + 改密
    ops_login = login(client, "ops_j", R13_OPS_PASSWORD)
    assert ops_login.status_code == 200 and json.loads(ops_login.content)["must_change_password"] is True
    ops_token = json.loads(ops_login.content)["token"]
    assert change_password(client, ops_token, R13_OPS_PASSWORD, _OPS_NEW_PW).status_code == 200

    # ⑥ 项目内全功能（上传是管理动作）
    up = SimpleUploadedFile("ops.txt", "运维账户项目内上传正文。".encode("utf-8"), content_type="text/plain")
    uploaded = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **bearer(ops_token))
    assert uploaded.status_code == 201, uploaded.content

    # ⑦ 跨项目拒绝
    crossed = client.get("/api/files", HTTP_X_IB_PROJECT="p_beta", **bearer(ops_token))
    assert crossed.status_code == 403

    # ⑧ 登出 → 401；停用后不得登录
    assert client.post("/api/auth/logout", **bearer(ops_token)).status_code == 204
    assert client.get("/api/auth/me", **bearer(ops_token)).status_code == 401
    ops_id = deps.account_store.get_user_by_username("ops_j").user_id
    assert client.post(f"/api/accounts/{ops_id}/disable", **bearer(admin_token)).status_code == 200
    assert login(client, "ops_j", _OPS_NEW_PW).status_code == 401


# --------------------------------------------------------------------------- #
# TC-E2E-021 无令牌旁路旅程：查询串令牌全端点拒绝 + 离线令牌不得触达账户管理
# --------------------------------------------------------------------------- #


def test_TC_E2E_021_no_paste_token_bypass_journey(accounts_app):
    """US-IB-21 / AC-IB-21-03、AC-IB-21-04（关键路径）。

    遍历前端会触达的各视图对应端点：不存在任何「令牌可经 URL 进入」的合法途径 ——
    `?token=` / `?access_token=` 一律 400；登录仅接受 JSON 体（用户名 + 口令）；
    全响应零 `Set-Cookie`（客户端不携带会话 Cookie）。
    """
    client = accounts_app[1]()
    token = json.loads(login(client, "admin", R13_ADMIN_PASSWORD).content)["token"]

    for path in (
        "/api/files?token=leaked",
        "/api/accounts?token=leaked",
        "/api/auth/me?access_token=leaked",
        "/healthz?token=leaked",
        "/api/chat/stream?q=hi&token=leaked",
    ):
        r = client.get(path, **bearer(token))
        assert r.status_code == 400, path
        assert json.loads(r.content)["error"]["code"] == "token_in_query_forbidden"
        assert len(r.cookies) == 0

    # 登录端点在**公共路径判定之前**即受查询串纪律约束
    r = client.post("/api/auth/login?token=leaked", data="{}", content_type="application/json")
    assert r.status_code == 400 and json.loads(r.content)["error"]["code"] == "token_in_query_forbidden"
