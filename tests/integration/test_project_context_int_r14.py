"""集成测试层 —— R14 增量（全局管理员「当前项目」选择与 `X-IB-Project` 传播）。

覆盖 `GET /api/projects`（IFC-IB-333）的授权口径与 `X-IB-Project` 头契约（IFC-IB-334），
及其对 R13 回归缺陷的修复效果：全局管理员（`users.project_id IS NULL`）在选定当前项目后，
**项目级端点可用**；未选定项目时**仍 fail-closed**（未选项目即不泄露）。

溯源（现有 AC 映射，见 `architecture_design.md` §10.1 R14 OPEN ITEM）：
  * US-IB-24 / **AC-IB-24-03**（admin 不受项目绑定限制，可访问任一项目）；
  * **AC-IB-24-02**（ops 跨项目 403）；
  * REQ-FUNC-IB-31（账户 : 项目 = 1:1；admin 全局）；
  * REQ-FUNC-IB-23（多项目隔离 fail-closed）。

离线约束：内存账户存储 + 内存台账 + 内存定义文档存储 + Django test Client，不触网。
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

#: 测试用**占位**口令（非生产凭据）。
_ADMIN_NEW_PW = "GroupD-Admin-New-R14!"
_OPS_NEW_PW = "GroupD-Ops-New-R14!"


def _client(accounts_app):
    _, Client = accounts_app
    return Client()


def _login_admin(client) -> str:
    """登录默认管理员（admin，全局主体）并完成首登强制改密，返回已解锁令牌。"""
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
    return r


def _login_ops(client, username="ops_a") -> str:
    r = login(client, username, R13_OPS_PASSWORD)
    assert r.status_code == 200, r.content
    token = json.loads(r.content)["token"]
    done = change_password(client, token, R13_OPS_PASSWORD, _OPS_NEW_PW)
    assert done.status_code == 200, done.content
    return token


def _projects(client, token, **extra):
    return client.get("/api/projects", **bearer(token), **extra)


# --------------------------------------------------------------------------- #
# TC-INT-123 项目枚举端点：非项目级端点 + 全局主体未选定项目也 200 + 零 Cookie
#
# **编号更正（REV-14 / INV-GROUP-D-INTELBASE-014）**：本组用例最初套用 TC-INT-120~122，
# 与 R13 已登记并占用同号的 `tests/integration/test_accounts_deploy_int_r13.py`
# （TC-INT-120 nginx TLS 模板 / TC-INT-121 运行时键登记 / TC-INT-122 迁移列级一致，
# 见 `docs/test_plan.md` §18.2）**撞号**。为恢复「编号唯一、只增不改」纪律，本组整体后移
# 至 **TC-INT-123~125**（既有 105~122 一字不改）。登记为 **R14-DEF-01**（追踪性缺陷）。
# --------------------------------------------------------------------------- #


def test_TC_INT_123_projects_endpoint_is_not_project_scoped(accounts_app):
    """US-IB-24 / AC-IB-24-03；REQ-FUNC-IB-31。

    全局主体（admin）**未选定**当前项目（`effective_project == "*"`）时，`GET /api/projects`
    仍必须 `200` 并返回**全部**已登记项目 —— 否则 admin 永远无法引导「选择项目」这一步
    （该端点是 fail-closed 的唯一出口）。`?token=` 仍 `4xx`；未认证 `401`；零 `Set-Cookie`。
    """
    client = _client(accounts_app)
    # 凭据纪律：未认证 401、查询串令牌 4xx（中间件先于路由拒绝）。
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects?token=x").status_code == 400
    assert client.get("/api/projects?access_token=x").status_code == 400

    token = _login_admin(client)
    r = _projects(client, token)
    assert r.status_code == 200, r.content
    assert "Set-Cookie" not in r.headers, "项目枚举响应不得出现 Set-Cookie（零 Cookie）"

    items = json.loads(r.content)["items"]
    by_id = {i["project_id"]: i for i in items}
    assert set(by_id) == {"p_alpha", "p_beta"}, by_id.keys()
    assert by_id["p_alpha"]["name"] == "测试项目 A"
    assert by_id["p_beta"]["name"] == "测试项目 B"
    # 未选定项目 ⇒ effective_project 为全局哨兵 ⇒ 全部 is_current=False。
    assert all(i["is_current"] is False for i in items), items
    # 每项字段集合固定（契约：project_id / name / is_current）。
    for item in items:
        assert set(item) == {"project_id", "name", "is_current"}, item


# --------------------------------------------------------------------------- #
# TC-INT-124 admin 选定项目后项目级端点可用；未选定 / 未知项目仍 fail-closed
# --------------------------------------------------------------------------- #


def test_TC_INT_124_admin_selects_project_unblocks_project_endpoints(accounts_app):
    """US-IB-24 / AC-IB-24-03；REQ-FUNC-IB-23。

    * 无 `X-IB-Project` ⇒ 项目级端点（可视化配置）fail-closed `503`（**未选项目即不泄露**）；
    * 带 `X-IB-Project: p_alpha` ⇒ `200`（R13 回归缺陷修复的直接证据）；
    * 未知项目名 ⇒ 服务端**不校验存在性**，`effective_project` 即为该串 ⇒ 仍 `503`；
    * `GET /api/projects` 的 `is_current` 反映**本请求**的 `effective_project`。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    # 未选定项目：项目级端点 fail-closed（刻意设计，不是故障）。
    assert client.get("/api/config/definition", **h).status_code == 503

    # 选定 p_alpha：项目级端点可用（同时验证项目枚举的 is_current）。
    ok = client.get("/api/config/definition", **h, HTTP_X_IB_PROJECT="p_alpha")
    assert ok.status_code == 200, ok.content

    cur = json.loads(_projects(client, token, HTTP_X_IB_PROJECT="p_alpha").content)["items"]
    by_id = {i["project_id"]: i for i in cur}
    assert by_id["p_alpha"]["is_current"] is True and by_id["p_beta"]["is_current"] is False, cur

    # 未知项目名不校验存在性 ⇒ 项目级端点仍 fail-closed（不泄露）。
    ghost = client.get("/api/config/definition", **h, HTTP_X_IB_PROJECT="p_ghost")
    assert ghost.status_code == 503, ghost.content


# --------------------------------------------------------------------------- #
# TC-INT-125 ops 仅见自身（结构上不可切换）；跨项目头 403 project_mismatch
# --------------------------------------------------------------------------- #


def test_TC_INT_125_ops_sees_only_own_project_and_cross_project_is_403(accounts_app):
    """US-IB-24 / AC-IB-24-02；REQ-FUNC-IB-31 / IB-32。

    ops 的项目列表**恒为 1 项**（自身项目，`is_current=True`）—— 服务端裁定「可见集合」，
    ops 侧**结构上不可**枚举他项目 / 切换。叠加 `X-IB-Project` 头契约：与绑定不符 ⇒
    `403 project_mismatch`；等于自身 / 缺省 ⇒ 放行。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    _create_ops(client, admin_token, "ops_a", "p_alpha")
    ops_token = _login_ops(client, "ops_a")
    h = bearer(ops_token)

    listed = _projects(client, ops_token)
    assert listed.status_code == 200, listed.content
    items = json.loads(listed.content)["items"]
    assert len(items) == 1, f"ops 必须仅见自身项目，实际 {items}"
    assert items[0]["project_id"] == "p_alpha" and items[0]["is_current"] is True, items

    # 跨项目头 → 403 project_mismatch（IC-IB-334 的项目边界断言）。
    mismatch = client.get("/api/config/definition", **h, HTTP_X_IB_PROJECT="p_beta")
    assert mismatch.status_code == 403, mismatch.content
    assert json.loads(mismatch.content)["error"]["code"] == "project_mismatch"

    # 与自身一致 / 缺省 → 放行（ops 的 effective_project 恒为其绑定项目）。
    assert client.get("/api/config/definition", **h, HTTP_X_IB_PROJECT="p_alpha").status_code == 200
    assert client.get("/api/config/definition", **h).status_code == 200


# --------------------------------------------------------------------------- #
# TC-INT-126 `/api/projects` 方法纪律：非 GET/POST 一律 405 + POST 仅 admin（REV-18）+ 零 Cookie
# --------------------------------------------------------------------------- #


def test_TC_INT_126_projects_endpoint_method_discipline(accounts_app):
    """US-IB-24 / AC-IB-24-03；IFC-IB-333 / REV-18 IFC-IB-372。

    REV-18 起 `/api/projects` **集合路径**新增 `POST`（项目创建，**仅 admin**；IFC-IB-372）——
    故非 `GET` / `POST` 的方法仍一律 `405 method_not_allowed`；`POST` 由「一律 405」改为
    「admin 合法创建 / ops 一律 403」。任何方法下都**不得**出现 `Set-Cookie`（零 Cookie 纪律）。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    admin_h = bearer(admin_token)

    for method in ("put", "delete", "patch"):
        resp = getattr(client, method)("/api/projects", **admin_h)
        assert resp.status_code == 405, (method, resp.status_code, resp.content)
        assert json.loads(resp.content)["error"]["code"] == "method_not_allowed", resp.content
        assert "Set-Cookie" not in resp.headers, f"{method} 出现 Set-Cookie"

    # 正常 GET 仍 200（方法纪律不误伤读路径）。
    assert client.get("/api/projects", **admin_h).status_code == 200

    # REV-18：POST 非法体 → 400（不再是 405）；合法体 → 201（admin 可创建）。
    bad = client.post("/api/projects", data="{}", content_type="application/json", **admin_h)
    assert bad.status_code == 400, bad.content
    assert "Set-Cookie" not in bad.headers
    ok = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_r18", "name": "R18 项目"}),
        content_type="application/json",
        **admin_h,
    )
    assert ok.status_code == 201, ok.content
    assert json.loads(ok.content)["project_id"] == "p_r18"
    assert "Set-Cookie" not in ok.headers

    # ops 侧：POST → 403（非 admin 一律服务端 403；ADR-42：UI 分组不是权限机制）。
    _create_ops(client, admin_token, "ops_a", "p_alpha")
    ops_token = _login_ops(client, "ops_a")
    ops_post = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_ops", "name": "越权"}),
        content_type="application/json",
        **bearer(ops_token),
    )
    assert ops_post.status_code == 403, ops_post.content
    assert "Set-Cookie" not in ops_post.headers


# --------------------------------------------------------------------------- #
# TC-INT-127 顺序依赖（先建项目、后建账号）+ 停用项目的 ops → 空列表（不枚举他项目）
# --------------------------------------------------------------------------- #


def test_TC_INT_127_ops_with_unregistered_project_sees_empty_not_others(accounts_app):
    """US-IB-24 / AC-IB-24-02；REQ-FUNC-IB-31 / IB-23 / IB-45；REV-18 IFC-IB-373。

    REV-18 顺序依赖：`POST /api/accounts` 的目标 `project_id` 须在**项目注册表**存在且
    `active`，否则 **422**（不静默创建无主账号）。既有「ops 见空列表而非枚举他项目」不变量
    改由「**停用**项目的 ops」验证：先建 `p_gamma` → 建 `ops_g` → 软删（停用）`p_gamma`，
    则 `ops_g` 的项目列表**必须为空**（`list_active()` 不含停用项目），且其声明他项目仍被
    `403 project_mismatch` 拦下（边界不因自身项目停用而放宽）。
    """
    client = _client(accounts_app)
    admin_token = _login_admin(client)
    admin_h = bearer(admin_token)

    # 1) 顺序依赖：绑定**未登记**项目 → 422（不创建无主账号）。
    unregistered = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": "ops_g", "password": R13_OPS_PASSWORD, "project_id": "p_gamma"}
        ),
        content_type="application/json",
        **admin_h,
    )
    assert unregistered.status_code == 422, unregistered.content
    assert json.loads(unregistered.content)["error"]["code"] == "project_not_active"

    # 2) 先建项目（admin），再建账号 → 201。
    created = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_gamma", "name": "伽马"}),
        content_type="application/json",
        **admin_h,
    )
    assert created.status_code == 201, created.content
    _create_ops(client, admin_token, "ops_g", "p_gamma")
    ops_token = _login_ops(client, "ops_g")
    assert json.loads(_projects(client, ops_token).content)["items"], "启用项目的 ops 应见自身项目"

    # 3) 停用 p_gamma（软删，二次确认）→ ops_g 见空列表（不枚举他项目）。
    disabled = client.delete(
        "/api/projects/p_gamma",
        data=json.dumps({"confirm_project_id": "p_gamma"}),
        content_type="application/json",
        **admin_h,
    )
    assert disabled.status_code == 200, disabled.content
    assert json.loads(disabled.content)["status"] == "disabled"
    items = json.loads(_projects(client, ops_token).content)["items"]
    assert items == [], f"停用项目的 ops 必须见空列表，实际 {items}"

    # 4) 声明他项目 → 403 project_mismatch（边界不因自身项目停用而放宽）。
    foreign = client.get(
        "/api/config/definition", **bearer(ops_token), HTTP_X_IB_PROJECT="p_alpha"
    )
    assert foreign.status_code == 403, foreign.content
    assert json.loads(foreign.content)["error"]["code"] == "project_mismatch"


# --------------------------------------------------------------------------- #
# TC-INT-128 枚举稳定性：project_id 升序 + 头值空白归一 + 未知头全 False
# --------------------------------------------------------------------------- #


def test_TC_INT_128_projects_ordering_and_header_normalization(accounts_app):
    """US-IB-24 / AC-IB-24-03；IFC-IB-333 / 334。

    * 列表按 `project_id` **升序**稳定输出（前端选择器顺序可复现）；
    * `X-IB-Project` 首尾空白由中间件 `strip` 归一（`"  p_alpha  "` ≡ `"p_alpha"`），
      `is_current` 随之正确翻转、项目级端点亦放行；
    * **未知**头值不校验存在性：全 `is_current=False`，且项目级端点 fail-closed（503）。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    ids = [i["project_id"] for i in json.loads(_projects(client, token).content)["items"]]
    assert ids == sorted(ids) == ["p_alpha", "p_beta"], f"项目列表未按 project_id 升序：{ids}"

    # 首尾空白归一：等同 p_alpha（中间件 strip）。
    padded = json.loads(
        _projects(client, token, HTTP_X_IB_PROJECT="  p_alpha  ").content
    )["items"]
    assert {i["project_id"]: i["is_current"] for i in padded} == {
        "p_alpha": True,
        "p_beta": False,
    }, padded
    assert client.get(
        "/api/config/definition", **h, HTTP_X_IB_PROJECT="  p_alpha  "
    ).status_code == 200

    # 未知头值：不校验存在性 ⇒ 全 False；项目级端点仍 fail-closed。
    ghost = json.loads(_projects(client, token, HTTP_X_IB_PROJECT="p_ghost").content)["items"]
    assert all(i["is_current"] is False for i in ghost), ghost
    assert client.get(
        "/api/config/definition", **h, HTTP_X_IB_PROJECT="p_ghost"
    ).status_code == 503
