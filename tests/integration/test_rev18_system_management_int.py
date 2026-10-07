"""集成测试层 —— REV-18 增量（系统管理三分：账户 / 项目 / LLM Key + 顺序依赖）。

覆盖 REV-18 新增端点的 HTTP 契约（`architecture_design.md` ADR-37 ~ ADR-42 +
`module_design.md` IFC-IB-372 ~ IFC-IB-374）：

  * `POST /api/projects`（建）/ `PATCH|DELETE /api/projects/{project_id}`（改 / 软删）；
  * `PATCH|DELETE /api/accounts/{user_id}`（改 / 软删）+ `POST /api/accounts` 顺序依赖（422）；
  * `GET|PUT|DELETE /api/llm-key`（掩码 + 存在性 + 更新时间；**绝不回明文**）。

**红线**（`code_review_report.md` 逐条取证）：
  * 授权：仅 admin（非 admin 一律服务端 403；ADR-42「UI 分组非权限机制」）；
  * 顺序依赖：建账号的目标项目须在注册表存在且 active，否则 422（REQ-FUNC-IB-45）；
  * 二次确认：项目软删须 `confirm_project_id`、账户软删须 `confirm_username`，不符 400；
  * 禁删 admin → 409；软删 = `status="disabled"`（数据保留，可恢复，OOS-19）；
  * 凭据纪律：LLM Key 只经 `PUT /api/llm-key` 写入；任何响应只回掩码 / 存在性 / 更新时间，
    **绝不含明文**；`?token=` 一律 4xx；全程零 `Set-Cookie`。

离线约束：内存账户存储 + 内存项目注册表 + 内存 LLM Key 存储 + Django test Client，不触网。
"""

from __future__ import annotations

import json

from conftest import (
    R13_ADMIN_PASSWORD,
    R13_OPS_PASSWORD,
    bearer,
    change_password,
    login,
)

#: 测试用**占位**口令（非生产凭据，性质同 conftest 的 `groupd-offline-token`）。
_ADMIN_NEW_PW = "Rev18-Admin-New!"
_OPS_NEW_PW = "Rev18-Ops-New!"
#: 测试用**占位** LLM Key（**非真实密钥**；仅用于验证「写入后只回掩码、不回明文」）。
_FAKE_SECRET = "sk-rev18-placeholder-not-a-real-key-0000"


def _client(accounts_app):
    _, Client = accounts_app
    return Client()


def _login_admin(client) -> str:
    r = login(client, "admin", R13_ADMIN_PASSWORD)
    assert r.status_code == 200, r.content
    token = json.loads(r.content)["token"]
    done = change_password(client, token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW)
    assert done.status_code == 200, done.content
    return token


def _create_ops(client, admin_token, username="ops_a", project_id="p_alpha"):
    r = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": username, "password": R13_OPS_PASSWORD, "project_id": project_id}
        ),
        content_type="application/json",
        **bearer(admin_token),
    )
    assert r.status_code == 201, r.content
    return json.loads(r.content)


def _login_ops(client, username="ops_a") -> str:
    r = login(client, username, R13_OPS_PASSWORD)
    assert r.status_code == 200, r.content
    token = json.loads(r.content)["token"]
    done = change_password(client, token, R13_OPS_PASSWORD, _OPS_NEW_PW)
    assert done.status_code == 200, done.content
    return token


def _admin_user_id(client, admin_token) -> str:
    items = json.loads(client.get("/api/accounts", **bearer(admin_token)).content)["items"]
    return next(u["user_id"] for u in items if u["username"] == "admin")


# --------------------------------------------------------------------------- #
# TC-INT-148 项目注册表全生命周期：建 → 查 → 改 → 软删（二次确认）+ 冲突 / 非法 400
# --------------------------------------------------------------------------- #


def test_TC_INT_148_project_registry_lifecycle(accounts_app):
    """US-IB-43 / IFC-IB-372；ADR-37（同库 projects 表 + 软删）+ ADR-42（仅 admin）。

    建（201）→ 列表含新项目 → 重名 409 / 非法 `project_id` 400 → 改名 200 →
    软删确认不符 400 → 软删 200（`status="disabled"`）→ 列表不再含该项目。全程零 `Set-Cookie`。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    base = json.loads(client.get("/api/projects", **h).content)["items"]
    assert {i["project_id"] for i in base} == {"p_alpha", "p_beta"}

    created = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_gamma", "name": "伽马项目"}),
        content_type="application/json",
        **h,
    )
    assert created.status_code == 201, created.content
    assert "Set-Cookie" not in created.headers
    body = json.loads(created.content)
    assert set(body) == {"project_id", "name", "status", "created_at", "updated_at"}, body
    assert body["project_id"] == "p_gamma" and body["status"] == "active"

    listed = json.loads(client.get("/api/projects", **h).content)["items"]
    assert "p_gamma" in {i["project_id"] for i in listed}

    # 重名冲突 → 409
    dup = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_gamma", "name": "另一个"}),
        content_type="application/json",
        **h,
    )
    assert dup.status_code == 409, dup.content

    # 非法 project_id（含路径分隔符）→ 400（不渗入下游 collection / 路径拼装）
    bad = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p/bad", "name": "坏"}),
        content_type="application/json",
        **h,
    )
    assert bad.status_code == 400, bad.content

    # 改名 → 200
    renamed = client.patch(
        "/api/projects/p_gamma",
        data=json.dumps({"name": "伽马项目（改）"}),
        content_type="application/json",
        **h,
    )
    assert renamed.status_code == 200, renamed.content
    assert json.loads(renamed.content)["name"] == "伽马项目（改）"

    # 二次确认不符 → 400
    wrong = client.delete(
        "/api/projects/p_gamma",
        data=json.dumps({"confirm_project_id": "p_delta"}),
        content_type="application/json",
        **h,
    )
    assert wrong.status_code == 400, wrong.content

    # 软删 → 200 status=disabled（数据保留）
    disabled = client.delete(
        "/api/projects/p_gamma",
        data=json.dumps({"confirm_project_id": "p_gamma"}),
        content_type="application/json",
        **h,
    )
    assert disabled.status_code == 200, disabled.content
    assert json.loads(disabled.content)["status"] == "disabled"

    after = json.loads(client.get("/api/projects", **h).content)["items"]
    assert "p_gamma" not in {i["project_id"] for i in after}, "软删项目仍出现在活动列表"


# --------------------------------------------------------------------------- #
# TC-INT-149 项目端点授权：非 admin 一律 403；未知项目 404；?token= 4xx
# --------------------------------------------------------------------------- #


def test_TC_INT_149_project_endpoint_admin_only_and_token_discipline(accounts_app):
    """US-IB-43 / AC-IB-24-02；IFC-IB-372；ADR-42（UI 分组非权限机制）。

    ops 对项目**写**端点一律服务端 403（不因前端隐藏入口而放行）；未知项目 404；
    `?token=` 一律 400（令牌不得进 URL，中间件先行）。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    _create_ops(client, admin_token, "ops_a", "p_alpha")
    ops_token = _login_ops(client, "ops_a")
    ops_h = bearer(ops_token)
    admin_h = bearer(admin_token)

    assert client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_z", "name": "z"}),
        content_type="application/json",
        **ops_h,
    ).status_code == 403
    assert client.patch(
        "/api/projects/p_alpha",
        data=json.dumps({"name": "x"}),
        content_type="application/json",
        **ops_h,
    ).status_code == 403
    assert client.delete(
        "/api/projects/p_alpha",
        data=json.dumps({"confirm_project_id": "p_alpha"}),
        content_type="application/json",
        **ops_h,
    ).status_code == 403

    # 未知项目 → 404（admin 亦然）
    assert client.patch(
        "/api/projects/p_ghost",
        data=json.dumps({"name": "x"}),
        content_type="application/json",
        **admin_h,
    ).status_code == 404

    # 查询串令牌一律 4xx（令牌只经 Authorization 头）
    assert client.get("/api/projects?token=x", **admin_h).status_code == 400
    assert client.get("/api/llm-key?token=x", **admin_h).status_code == 400
    assert client.get("/api/accounts?access_token=x", **admin_h).status_code == 400


# --------------------------------------------------------------------------- #
# TC-INT-150 账户改 / 删（PATCH / DELETE）：重绑 / 改名 / 停用 + 禁删 admin(409) + 二次确认
# --------------------------------------------------------------------------- #


def test_TC_INT_150_account_patch_and_soft_delete(accounts_app):
    """US-IB-44 / IFC-IB-373；ADR-40（PATCH/DELETE + 软删 + 禁删 admin → 409 + 二次确认）。

    改名 200 / 未知用户 404 / 禁删 admin 409 / 确认不符 400 / 软删 ops 200（随后登录 401）。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    h = bearer(admin_token)
    ops = _create_ops(client, admin_token, "ops_a", "p_alpha")

    renamed = client.patch(
        f"/api/accounts/{ops['user_id']}",
        data=json.dumps({"username": "ops_a2"}),
        content_type="application/json",
        **h,
    )
    assert renamed.status_code == 200, renamed.content
    assert json.loads(renamed.content)["username"] == "ops_a2"

    unknown = client.patch(
        "/api/accounts/no-such-user",
        data=json.dumps({"username": "x"}),
        content_type="application/json",
        **h,
    )
    assert unknown.status_code == 404, unknown.content

    # 禁删 admin → 409（含最后一个有效管理员）
    admin_id = _admin_user_id(client, admin_token)
    forbidden = client.delete(
        f"/api/accounts/{admin_id}",
        data=json.dumps({"confirm_username": "admin"}),
        content_type="application/json",
        **h,
    )
    assert forbidden.status_code == 409, forbidden.content

    # 二次确认不符 → 400
    wrong = client.delete(
        f"/api/accounts/{ops['user_id']}",
        data=json.dumps({"confirm_username": "someone-else"}),
        content_type="application/json",
        **h,
    )
    assert wrong.status_code == 400, wrong.content

    # 软删 ops → 200 status=disabled；其后登录 401（会话撤销 + 停用不可登录）
    done = client.delete(
        f"/api/accounts/{ops['user_id']}",
        data=json.dumps({"confirm_username": "ops_a2"}),
        content_type="application/json",
        **h,
    )
    assert done.status_code == 200, done.content
    assert json.loads(done.content)["status"] == "disabled"
    assert login(client, "ops_a2", R13_OPS_PASSWORD).status_code == 401
    assert "Set-Cookie" not in done.headers


# --------------------------------------------------------------------------- #
# TC-INT-151 顺序依赖：先建项目、后建账号（未登记项目 → 422，不建无主账号）
# --------------------------------------------------------------------------- #


def test_TC_INT_151_account_create_requires_active_project(accounts_app):
    """US-IB-45 / IFC-IB-373；REQ-FUNC-IB-45（先建项目、后建账号）。

    绑定**未登记**项目 → 422 `project_not_active`；先建项目 → 建账号 201（正例）。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    h = bearer(admin_token)

    missing = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": "ops_g", "password": R13_OPS_PASSWORD, "project_id": "p_gamma"}
        ),
        content_type="application/json",
        **h,
    )
    assert missing.status_code == 422, missing.content
    assert json.loads(missing.content)["error"]["code"] == "project_not_active"

    assert client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_gamma", "name": "伽马"}),
        content_type="application/json",
        **h,
    ).status_code == 201
    ok = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": "ops_g", "password": R13_OPS_PASSWORD, "project_id": "p_gamma"}
        ),
        content_type="application/json",
        **h,
    )
    assert ok.status_code == 201, ok.content
    assert json.loads(ok.content)["project_id"] == "p_gamma"


# --------------------------------------------------------------------------- #
# TC-INT-152 LLM Key 生命周期：未配置 → PUT → 掩码回执 → DELETE → 未配置
# --------------------------------------------------------------------------- #


def test_TC_INT_152_llm_key_lifecycle_masked_only(accounts_app):
    """US-IB-46 / IFC-IB-374；ADR-38（单行表；`PUT` 唯一写入口）+ C-IB-42。

    `GET` 初期 `configured=False` → `PUT` 后 `configured=True` 且**只回掩码**（响应体不含明文）
    → 空值 400 → `DELETE` 204 → 回到未配置。
    """
    from ib.core import LLM_KEY_MASK

    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    initial = client.get("/api/llm-key", **h)
    assert initial.status_code == 200, initial.content
    body0 = json.loads(initial.content)
    assert set(body0) == {"configured", "masked", "updated_at"}, body0
    assert body0["configured"] is False and body0["updated_at"] is None

    put = client.put(
        "/api/llm-key",
        data=json.dumps({"secret": _FAKE_SECRET}),
        content_type="application/json",
        **h,
    )
    assert put.status_code == 200, put.content
    body1 = json.loads(put.content)
    assert body1["configured"] is True and body1["masked"] == LLM_KEY_MASK
    assert body1["updated_at"]
    # 凭据纪律：响应体**绝不**含明文（连前缀都不含）
    assert _FAKE_SECRET not in put.content.decode("utf-8")
    assert "sk-rev18" not in put.content.decode("utf-8")

    got = json.loads(client.get("/api/llm-key", **h).content)
    assert got["configured"] is True and got["masked"] == LLM_KEY_MASK

    empty = client.put(
        "/api/llm-key",
        data=json.dumps({"secret": "   "}),
        content_type="application/json",
        **h,
    )
    assert empty.status_code == 400, empty.content

    cleared = client.delete("/api/llm-key", **h)
    assert cleared.status_code == 204, cleared.content
    after = json.loads(client.get("/api/llm-key", **h).content)
    assert after["configured"] is False


# --------------------------------------------------------------------------- #
# TC-INT-153 LLM Key 授权 + 零 Cookie + 方法纪律
# --------------------------------------------------------------------------- #


def test_TC_INT_153_llm_key_admin_only_and_no_cookie(accounts_app):
    """US-IB-46 / IFC-IB-374；ADR-42（仅 admin）+ 零 Cookie 纪律。

    非 admin 对 `GET`/`PUT`/`DELETE` 一律 403；不支持的方法 405；全程零 `Set-Cookie`。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    _create_ops(client, admin_token, "ops_a", "p_alpha")
    ops_token = _login_ops(client, "ops_a")
    ops_h = bearer(ops_token)

    assert client.get("/api/llm-key", **ops_h).status_code == 403
    assert client.put(
        "/api/llm-key",
        data=json.dumps({"secret": _FAKE_SECRET}),
        content_type="application/json",
        **ops_h,
    ).status_code == 403
    assert client.delete("/api/llm-key", **ops_h).status_code == 403

    admin_h = bearer(admin_token)
    assert client.post("/api/llm-key", **admin_h).status_code == 405
    for resp in (
        client.get("/api/llm-key", **admin_h),
        client.put(
            "/api/llm-key",
            data=json.dumps({"secret": _FAKE_SECRET}),
            content_type="application/json",
            **admin_h,
        ),
    ):
        assert "Set-Cookie" not in resp.headers
