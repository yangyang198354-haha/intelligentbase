"""集成测试层 —— R13 增量（账户 / 会话 / 账户 CRUD / 项目边界 / 无令牌旁路）。

加载 `ibweb.accounts.policy` 作为**鉴权策略**（生产形态），经真实 `POST /api/auth/login`
取得令牌后，覆盖 `ibweb.urls` 的 R13 端点（IFC-IB-316~321）与中间件纪律
（`ibweb/authz.py`：`?token=` 全端点 4xx / 改密态 allowlist / 项目边界 403 / 零 Set-Cookie）。

溯源：每个用例在 docstring 标注 **US-IB-NN / AC-IB-NN-NN**。
离线约束：内存账户存储 + Django test Client，不触网、不连外部依赖。
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

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import new_session_token, token_digest

#: 测试用**占位**口令（非生产凭据）。改密后的新口令，用于解锁 admin 会话。
_ADMIN_NEW_PW = "GroupD-Admin-New-1!"
_OPS_NEW_PW = "GroupD-Ops-New-1!"


def _client(accounts_app):
    _, Client = accounts_app
    return Client()


def _admin_user_id(deps) -> str:
    return deps.account_store.get_user_by_username("admin").user_id


def _login_admin(client) -> str:
    """登录默认管理员并**完成首登强制改密**，返回已解锁的令牌。"""
    r = login(client, "admin", R13_ADMIN_PASSWORD)
    assert r.status_code == 200, r.content
    token = json.loads(r.content)["token"]
    done = change_password(client, token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW)
    assert done.status_code == 200, done.content
    return token


def _create_ops(client, admin_token, username="ops_a", project_id="p_alpha", password=None):
    return client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": username, "password": password or R13_OPS_PASSWORD, "project_id": project_id}
        ),
        content_type="application/json",
        **bearer(admin_token),
    )


# --------------------------------------------------------------------------- #
# TC-INT-105 登录成功（签发令牌 / 零 Cookie / 不回显凭据）
# --------------------------------------------------------------------------- #


def test_TC_INT_105_login_success_issues_token_without_credentials_echo(accounts_app):
    """US-IB-21 / AC-IB-21-01；US-IB-25 / AC-IB-25-04。

    正确用户名 + 口令 → 200 并签发**不透明**令牌；响应**不含**口令 / bcrypt 摘要；
    全程**零 `Set-Cookie`**（无 Cookie 会话）。
    """
    client = _client(accounts_app)
    r = login(client, "admin", R13_ADMIN_PASSWORD)
    assert r.status_code == 200, r.content
    body = json.loads(r.content)
    assert body["token"] and len(body["token"]) >= 32
    assert body["must_change_password"] is True, "默认管理员首登必须处于强制改密态"
    assert body["user"]["role"] == "admin" and body["user"]["project_id"] is None
    text = r.content.decode("utf-8")
    assert "password_hash" not in text and R13_ADMIN_PASSWORD not in text
    assert "token\"" in text  # 唯一一次令牌下发点

    # 令牌可用（经 Authorization 头）
    me = client.get("/api/auth/me", **bearer(body["token"]))
    assert me.status_code == 200
    assert json.loads(me.content)["username"] == "admin"

    # 零 Set-Cookie（登录 + 后续请求）
    assert len(r.cookies) == 0 and "Set-Cookie" not in r.headers
    assert len(me.cookies) == 0 and "Set-Cookie" not in me.headers


# --------------------------------------------------------------------------- #
# TC-INT-106 登录失败：统一 401（反账户枚举）
# --------------------------------------------------------------------------- #


def test_TC_INT_106_login_failure_is_uniform_anti_enumeration(accounts_app):
    """US-IB-21 / AC-IB-21-02：未知账户与错口令返回**逐字相同**的 401，不签发令牌。"""
    client = _client(accounts_app)
    unknown = login(client, "ghost-user", R13_ADMIN_PASSWORD)
    wrong_pw = login(client, "admin", "Wrong-Password-9!")
    assert unknown.status_code == 401 and wrong_pw.status_code == 401
    assert unknown.content == wrong_pw.content, "两种失败必须同文（防存在性探测预言机）"
    body = json.loads(unknown.content)
    assert body["error"]["code"] == "unauthenticated"
    assert "token" not in body
    assert "ghost-user" not in unknown.content.decode("utf-8")  # 不回显输入

    # 缺参 → 400（与凭据错误区分；不泄露账户状态）
    assert login(client, "", "").status_code == 400


# --------------------------------------------------------------------------- #
# TC-INT-107 首登强制改密：服务端受限会话（allowlist）
# --------------------------------------------------------------------------- #


def test_TC_INT_107_first_login_restricted_session_allowlist(accounts_app):
    """US-IB-22 / AC-IB-22-01、AC-IB-22-02。

    改密态下**仅**放行 `GET /api/auth/me`、`POST /api/auth/change-password`、
    `POST /api/auth/logout`；其余端点一律 403 `password_change_required`；
    改密成功后业务端点放行。
    """
    client = _client(accounts_app)
    token = json.loads(login(client, "admin", R13_ADMIN_PASSWORD).content)["token"]

    assert client.get("/api/auth/me", **bearer(token)).status_code == 200
    for path in ("/api/files", "/api/accounts", "/api/config/definition"):
        r = client.get(path, **bearer(token))
        assert r.status_code == 403, f"{path} 应在改密态被拒"
        assert json.loads(r.content)["error"]["code"] == "password_change_required"
    assert client.post("/api/accounts", data="{}", content_type="application/json", **bearer(token)).status_code == 403

    # 改密成功 → 放行
    done = change_password(client, token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW)
    assert done.status_code == 200 and json.loads(done.content)["must_change_password"] is False
    assert client.get("/api/auth/me", **bearer(token)).status_code == 200
    assert client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(token)).status_code == 200


# --------------------------------------------------------------------------- #
# TC-INT-108 改密校验与「撤销其余会话」
# --------------------------------------------------------------------------- #


def test_TC_INT_108_change_password_validation_and_session_revocation(accounts_app):
    """US-IB-22 / AC-IB-22-02；US-IB-25 / AC-IB-25-01。

    原口令错 → 400 `bad_old_password`；弱口令 → 400 `weak_password`；与原口令相同 → 400；
    成功后撤销**其余**会话、保留当前会话。
    """
    client = _client(accounts_app)
    token1 = _login_admin(client)
    # 第二次登录（此时已非改密态）→ 第二个会话
    r2 = login(client, "admin", _ADMIN_NEW_PW)
    assert r2.status_code == 200 and json.loads(r2.content)["must_change_password"] is False
    token2 = json.loads(r2.content)["token"]

    assert change_password(client, token1, "wrong-old", "NewPass-123!").status_code == 400
    assert change_password(client, token1, _ADMIN_NEW_PW, "short").status_code == 400
    assert change_password(client, token1, _ADMIN_NEW_PW, _ADMIN_NEW_PW).status_code == 400

    ok = change_password(client, token1, _ADMIN_NEW_PW, "GroupD-Admin-New-2!")
    assert ok.status_code == 200
    # 当前会话保留，其余会话被撤销
    assert client.get("/api/auth/me", **bearer(token1)).status_code == 200
    assert client.get("/api/auth/me", **bearer(token2)).status_code == 401


# --------------------------------------------------------------------------- #
# TC-INT-109 会话校验 / 登出撤销 / 续期（滑动窗口）
# --------------------------------------------------------------------------- #


def test_TC_INT_109_session_validate_logout_renew(accounts_app):
    """US-IB-25 / AC-IB-25-01、AC-IB-25-03。

    * 有效令牌经头访问 → 200（AC-IB-25-01）；
    * 登出撤销当前会话 → 同一令牌 401；
    * 续期：剩余有效期**大于**续期窗口时不提前延长；**临近过期**时延长 expires_at。
    """
    deps, Client = accounts_app
    client = Client()
    token = _login_admin(client)
    admin_id = _admin_user_id(deps)

    # 登出 → 撤销（独立令牌，避免影响后续续期断言）
    other = new_session_token()
    deps.account_store.issue_session(admin_id, token_digest(other), expires_at=iso_plus_seconds(600))
    assert client.get("/api/auth/me", **bearer(other)).status_code == 200
    assert client.post("/api/auth/logout", **bearer(other)).status_code == 204
    assert client.get("/api/auth/me", **bearer(other)).status_code == 401

    # 续期 A：离到期还远（>600s 窗口）→ 不改动 expires_at
    near = new_session_token()
    far_session = deps.account_store.issue_session(
        admin_id, token_digest(near), expires_at=iso_plus_seconds(3000)
    )
    r = client.post("/api/auth/session/renew", **bearer(near))
    assert r.status_code == 200 and json.loads(r.content)["expires_at"] == far_session.expires_at

    # 续期 B：临近过期（120s < 600s 窗口）→ 延长
    soon = new_session_token()
    soon_session = deps.account_store.issue_session(
        admin_id, token_digest(soon), expires_at=iso_plus_seconds(120)
    )
    r2 = client.post("/api/auth/session/renew", **bearer(soon))
    assert r2.status_code == 200
    renewed = json.loads(r2.content)["expires_at"]
    assert renewed > soon_session.expires_at, "临近过期必须被延长"
    assert renewed > iso_plus_seconds(600)

    # 无效 / 空令牌 → 401
    assert client.post("/api/auth/session/renew").status_code == 401
    assert client.post("/api/auth/session/renew", **bearer(new_session_token())).status_code == 401


# --------------------------------------------------------------------------- #
# TC-INT-110 过期会话 → 401（fail-closed）
# --------------------------------------------------------------------------- #


def test_TC_INT_110_expired_session_rejected_401(accounts_app):
    """US-IB-25 / AC-IB-25-02：过期令牌访问受保护接口 → 401。"""
    deps, Client = accounts_app
    client = Client()
    _login_admin(client)
    admin_id = _admin_user_id(deps)
    expired = new_session_token()
    deps.account_store.issue_session(admin_id, token_digest(expired), expires_at=iso_plus_seconds(-30))

    r = client.get("/api/auth/me", **bearer(expired))
    assert r.status_code == 401 and json.loads(r.content)["error"]["code"] == "unauthenticated"
    assert client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(expired)).status_code == 401


# --------------------------------------------------------------------------- #
# TC-INT-111 账户 CRUD（仅 admin）：创建 / 列表 / 停用 / 重置
# --------------------------------------------------------------------------- #


def test_TC_INT_111_account_crud_admin_only(accounts_app):
    """US-IB-23 / AC-IB-23-01、AC-IB-23-02、AC-IB-23-03。

    创建 ops 并绑定单一项目；用户名冲突 409；非 ops 角色 / 缺绑定 / 弱口令 → 400；
    停用后其会话被撤销且**无法再登录**；重置口令 → 强制改密且撤销其会话。
    """
    deps, Client = accounts_app
    client = Client()
    admin = _login_admin(client)

    created = _create_ops(client, admin, "ops_a", "p_alpha")
    assert created.status_code == 201, created.content
    summary = json.loads(created.content)
    assert summary["role"] == "ops" and summary["project_id"] == "p_alpha"
    assert summary["must_change_password"] is True
    assert "password_hash" not in created.content.decode("utf-8")
    # 1:1 绑定：单一 project_id 字符串（非集合）
    assert isinstance(summary["project_id"], str) and summary["project_id"] == "p_alpha"

    # 冲突 / 非法入参
    assert _create_ops(client, admin, "ops_a", "p_beta").status_code == 409  # 不可二次绑定
    assert _create_ops(client, admin, "ops_c", "").status_code == 400  # 缺项目
    assert _create_ops(client, admin, "ops_d", "p_alpha", "weak").status_code == 400  # 弱口令
    role_admin = client.post(
        "/api/accounts",
        data=json.dumps({"username": "x", "password": R13_OPS_PASSWORD, "project_id": "p_alpha", "role": "admin"}),
        content_type="application/json",
        **bearer(admin),
    )
    assert role_admin.status_code == 400

    # 列表（admin 全局可见）
    listing = json.loads(client.get("/api/accounts", **bearer(admin)).content)
    names = {item["username"] for item in listing["items"]}
    assert {"admin", "ops_a"} <= names
    assert deps.account_store.list_users("p_beta") == []  # ops_a 不属 p_beta

    # ops 登录（首登改密态）后停用 → 会话被撤销 + 无法登录
    ops_login = login(client, "ops_a", R13_OPS_PASSWORD)
    assert ops_login.status_code == 200
    ops_token = json.loads(ops_login.content)["token"]
    change_password(client, ops_token, R13_OPS_PASSWORD, _OPS_NEW_PW)
    assert client.get("/api/auth/me", **bearer(ops_token)).status_code == 200

    ops_id = deps.account_store.get_user_by_username("ops_a").user_id
    disabled = client.post(f"/api/accounts/{ops_id}/disable", **bearer(admin))
    assert disabled.status_code == 200 and json.loads(disabled.content)["status"] == "disabled"
    assert client.get("/api/auth/me", **bearer(ops_token)).status_code == 401, "停用须撤销会话"
    assert login(client, "ops_a", _OPS_NEW_PW).status_code == 401, "停用后不得登录（AC-IB-23-03）"

    # 重置口令 → 强制改密 + 撤销会话
    reset = client.post(
        f"/api/accounts/{ops_id}/reset-password",
        data=json.dumps({"new_password": "GroupD-Ops-Reset-1!"}),
        content_type="application/json",
        **bearer(admin),
    )
    assert reset.status_code == 200 and json.loads(reset.content)["must_change_password"] is True

    # 未知用户 → 404
    assert client.post("/api/accounts/nope/disable", **bearer(admin)).status_code == 404
    assert client.post(
        "/api/accounts/nope/reset-password",
        data=json.dumps({"new_password": "GroupD-X-Reset-1!"}),
        content_type="application/json",
        **bearer(admin),
    ).status_code == 404


# --------------------------------------------------------------------------- #
# TC-INT-112 非管理员账户越权 → 403
# --------------------------------------------------------------------------- #


def test_TC_INT_112_non_admin_account_ops_forbidden_403(accounts_app):
    """US-IB-23 / AC-IB-23-04：ops 执行账户创建 / 停用 / 列表 → 403。"""
    deps, Client = accounts_app
    client = Client()
    admin = _login_admin(client)
    assert _create_ops(client, admin, "ops_a", "p_alpha").status_code == 201

    ops_token = json.loads(login(client, "ops_a", R13_OPS_PASSWORD).content)["token"]
    change_password(client, ops_token, R13_OPS_PASSWORD, _OPS_NEW_PW)

    assert client.get("/api/accounts", **bearer(ops_token)).status_code == 403
    assert _create_ops(client, ops_token, "ops_z", "p_alpha").status_code == 403
    ops_id = deps.account_store.get_user_by_username("ops_a").user_id
    assert client.post(f"/api/accounts/{ops_id}/disable", **bearer(ops_token)).status_code == 403


# --------------------------------------------------------------------------- #
# TC-INT-113 项目边界隔离（ops 全功能但跨项目 403；admin 全局）
# --------------------------------------------------------------------------- #


def test_TC_INT_113_project_boundary_isolation_and_global_admin(accounts_app):
    """US-IB-24 / AC-IB-24-01、AC-IB-24-02、AC-IB-24-03。

    ops 在绑定项目内**拥有全功能**（非只读，可上传）；跨项目声明 → 403；admin 可访问任一项目。
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    deps, Client = accounts_app
    client = Client()
    admin = _login_admin(client)
    assert _create_ops(client, admin, "ops_a", "p_alpha").status_code == 201

    ops_token = json.loads(login(client, "ops_a", R13_OPS_PASSWORD).content)["token"]
    change_password(client, ops_token, R13_OPS_PASSWORD, _OPS_NEW_PW)

    # 项目内全功能：上传（管理动作）被允许（AC-IB-24-01）
    up = SimpleUploadedFile("r13.txt", "账户边界测试正文。".encode("utf-8"), content_type="text/plain")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": up}, **bearer(ops_token))
    assert r.status_code == 201, r.content

    # 跨项目：声明项目 B → 403（AC-IB-24-02）
    crossed = client.get("/api/files", HTTP_X_IB_PROJECT="p_beta", **bearer(ops_token))
    assert crossed.status_code == 403
    assert json.loads(crossed.content)["error"]["code"] == "project_mismatch"

    # 不声明项目 → 使用绑定项目（p_alpha）→ 200
    assert client.get("/api/files", **bearer(ops_token)).status_code == 200

    # admin（全局）：可访问任一项目（AC-IB-24-03）
    assert client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(admin)).status_code == 200
    assert client.get("/api/files", HTTP_X_IB_PROJECT="p_beta", **bearer(admin)).status_code == 200


# --------------------------------------------------------------------------- #
# TC-INT-114 停用账户登录被拒
# --------------------------------------------------------------------------- #


def test_TC_INT_114_disabled_account_login_rejected(accounts_app):
    """US-IB-23 / AC-IB-23-03：已停用账户尝试登录 → 拒绝（统一 401）。"""
    deps, Client = accounts_app
    client = Client()
    admin = _login_admin(client)
    assert _create_ops(client, admin, "ops_a", "p_alpha").status_code == 201
    ops_id = deps.account_store.get_user_by_username("ops_a").user_id
    client.post(f"/api/accounts/{ops_id}/disable", **bearer(admin))

    r = login(client, "ops_a", R13_OPS_PASSWORD)
    assert r.status_code == 401 and json.loads(r.content)["error"]["code"] == "unauthenticated"


# --------------------------------------------------------------------------- #
# TC-INT-115 粘贴令牌入口移除：`?token=` / `?access_token=` 全端点 4xx
# --------------------------------------------------------------------------- #


def test_TC_INT_115_query_token_forbidden_on_all_endpoints(accounts_app):
    """US-IB-21 / AC-IB-21-04（REQ-FUNC-IB-28 约束②）。

    `?token=` / `?access_token=` 在**全部**端点（含免鉴权的 `/healthz` 与 `/api/auth/login`）
    一律 400 `token_in_query_forbidden` —— 令牌只允许经 `Authorization` 头。
    """
    client = _client(accounts_app)
    token = json.loads(login(client, "admin", R13_ADMIN_PASSWORD).content)["token"]

    cases = [
        ("get", "/api/files?token=x"),
        ("get", "/api/auth/me?token=x"),
        ("get", "/api/accounts?access_token=x"),
        ("get", "/healthz?token=x"),
        ("get", "/api/chat/stream?q=hi&token=x"),
        ("post", "/api/auth/login?token=x"),
        ("post", "/api/auth/logout?access_token=x"),
    ]
    for method, path in cases:
        # 即使带合法 Authorization，也**先**被查询串纪律拒绝
        r = getattr(client, method)(path, **bearer(token))
        assert r.status_code == 400, f"{method.upper()} {path} 未被拒绝"
        assert json.loads(r.content)["error"]["code"] == "token_in_query_forbidden"


# --------------------------------------------------------------------------- #
# TC-INT-116 全响应零 Set-Cookie（无 Cookie 会话）
# --------------------------------------------------------------------------- #


def test_TC_INT_116_zero_set_cookie_across_endpoints(accounts_app):
    """US-IB-25 / AC-IB-25-04：登录 / me / accounts / files 响应均**不设 Cookie**。"""
    client = _client(accounts_app)
    login_resp = login(client, "admin", R13_ADMIN_PASSWORD)
    token = json.loads(login_resp.content)["token"]
    change_password(client, token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW)

    responses = [
        login_resp,
        client.get("/api/auth/me", **bearer(token)),
        client.get("/api/accounts", **bearer(token)),
        client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **bearer(token)),
        client.post("/api/auth/session/renew", **bearer(token)),
    ]
    for r in responses:
        assert len(r.cookies) == 0, f"{r.request['PATH_INFO']} 设置了 Cookie"
        assert "Set-Cookie" not in r.headers


# --------------------------------------------------------------------------- #
# TC-INT-117 离线替身令牌不得成为账户端点旁路（无隐藏旁路）
# --------------------------------------------------------------------------- #


def test_TC_INT_117_offline_token_cannot_reach_account_admin(http_app):
    """US-IB-21 / AC-IB-21-03；US-IB-27 / AC-IB-27-01。

    默认离线装配（`EnvTokenResolver`，非账户体系）：离线共享令牌可访问**业务**端点
    （既有离线自测依赖，OQ-IB-15），但**不得**获得管理员账户能力 —— `/api/accounts`
    必须 403（离线令牌主体非「全局」，不存在绕开账户体系的隐藏旁路）。
    """
    import os

    deps, Client = http_app
    client = Client()
    offline = {"HTTP_AUTHORIZATION": f"Bearer {os.environ['IB_OFFLINE_TOKEN']}"}
    assert client.get("/api/files", **offline).status_code == 200  # 既有离线依赖保留
    r = client.get("/api/accounts", **offline)
    assert r.status_code == 403, "离线共享令牌不得触达账户管理（无旁路）"


# --------------------------------------------------------------------------- #
# TC-INT-118 登录失败锁定（账户维度，AC-IB-29-01）
# --------------------------------------------------------------------------- #


def test_TC_INT_118_account_lockout_after_threshold(locked_accounts_app):
    """US-IB-29 / AC-IB-29-01（阈值可配置）：连续失败达阈值后，即使口令正确也被拒绝。

    阈值经 `IB_LOGIN_MAX_FAILURES` **装配期注入**账户存储（`_max_failures`），
    由 `record_login_failure` 计数并写 `locked_until`。锁定后统一 401（不泄露「已锁定」）。
    """
    client = _client(locked_accounts_app)
    for _ in range(3):
        assert login(client, "admin", "Wrong-Password-9!").status_code == 401
    locked = login(client, "admin", R13_ADMIN_PASSWORD)
    assert locked.status_code == 401, "达阈值后正确口令亦须被拒（锁定生效）"
    assert json.loads(locked.content)["error"]["code"] == "unauthenticated"


# --------------------------------------------------------------------------- #
# TC-INT-119 登录失败限速（来源 IP 维度，IFC-IB-326）—— 回归守卫（DEFECT-R13-01 已修复）
# --------------------------------------------------------------------------- #


def test_TC_INT_119_ip_dimension_throttle_returns_429(locked_accounts_app):
    """US-IB-29 / AC-IB-29-01（来源 IP 维度）—— **DEFECT-R13-01 回归守卫**。

    期望（IFC-IB-326 / `LoginThrottle` 语义）：同一来源 IP 连续失败达阈值（`IB_LOGIN_MAX_FAILURES`）
    后，再次尝试应返回 **429** `too_many_requests`。

    历史注记（DEFECT-R13-01，**现已修复**）：修复前 `views.auth_login_endpoint` **每次请求**都
    `build_throttle()` 新建一个 `LoginThrottle` 实例，`record_failure()` 写进的是这个**请求级临时对象**，
    请求结束即随 GC 丢弃 —— 进程内滑动窗口计数**从不跨请求累积**，故 `check()` 恒为 allow，
    429 分支不可达；本用例当时失败即为该缺陷的**可执行证据**。该缺陷已由
    **INV-GROUP_C-INTELBASE-013** 修复（把 `LoginThrottle` 提升为**组合期单例**
    `Deps.login_throttle`，按请求复用），并经独立复跑方 INV-GROUP_C-VERIFY-REV13-1 确认；
    本用例现为**回归守卫** —— IP 维度限速若再退化即再次失败。

    本用例以**不同用户名**（未知账户）发起连续失败，规避账户维度锁定，从而**单独**检验 IP 维度；
    IP 维度限速生效时，第 4 次必为 429（修复后实测序列 `[401,401,401,429]`）。
    """
    client = _client(locked_accounts_app)
    statuses = [login(client, f"ghost_{i}", "Wrong-Password-9!").status_code for i in range(4)]
    assert statuses[:3] == [401, 401, 401], statuses
    assert statuses[3] == 429, (
        "IP 维度限速未生效：连续失败后仍未返回 429。"
        f"实际状态序列={statuses}（DEFECT-R13-01：build_throttle() 每请求新建，计数不跨请求累积）"
    )
