"""集成测试层（补充）—— REV-18 增量：无覆盖的裁决口径与「按裁决属预期行为」的边界。

本文件补齐 `test_rev18_system_management_int.py`（TC-INT-148 ~ 153）**未覆盖**的口径，
逐条溯源 REV-18 的需求 / AC / ADR：

  * AC-IB-37-03（1:N，一个项目可有多个运维账号；OQ-IB-28「零迁移」）；
  * REQ-FUNC-IB-45（顺序依赖的**错误码顺序**：422 先于 400 / 409）；
  * AC-IB-38-03 / ADR-40 ④（删账号**不随项目级联**）；
  * AC-IB-36-03 / OOS-19（软删 / 停用 = **数据保留**，不物理级联删库）；
  * AC-IB-39-01（未配置态 `masked == ""`）；
  * AC-IB-39-03 / C-IB-42（审计只记 `outcome`；**任何**响应体（含错误体）不含明文）；
  * AC-IB-40-02 / AC-IB-40-03（kb 由主体推导 + 文件列表项目域隔离）；
  * **D-R18-01**：运行期新建项目在「配置侧登记 + 用户手工重启」前不能检索 / 上传 ——
    **已裁决的交付边界**（ADR-32 在项目维度的自然延伸），**不是缺陷**；断言的是
    **清晰的边界错误**（`scope_violation` / `startup_error`），而非崩溃或静默错误结果。

红线：非 admin 一律服务端 403（ADR-42）；Key 只经 `PUT /api/llm-key` 写入且**绝不回显明文**；
全程零 `Set-Cookie`。离线：内存账户 + 内存注册表 + 内存 Key 存储 + Django test Client，不触网。
"""

from __future__ import annotations

import json

from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import R13_ADMIN_PASSWORD, R13_OPS_PASSWORD, bearer, change_password, login

#: 测试用**占位**口令 / Key（**非生产凭据**，性质同 conftest 的 `groupd-offline-token`）。
_ADMIN_NEW_PW = "Rev18X-Admin-New!"
_OPS_NEW_PW = "Rev18X-Ops-New!"
_FAKE_SECRET = "sk-rev18-extra-placeholder-not-a-real-key-0000"


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


def _create_ops(client, admin_token, username, project_id):
    r = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": username, "password": R13_OPS_PASSWORD, "project_id": project_id}
        ),
        content_type="application/json",
        **bearer(admin_token),
    )
    return r


def _body(response) -> str:
    if hasattr(response, "streaming_content"):
        return b"".join(response.streaming_content).decode("utf-8", errors="replace")
    return response.content.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# TC-INT-154 1:N：同一项目可有多个运维账号（OQ-IB-28「零迁移」）
# --------------------------------------------------------------------------- #


def test_TC_INT_154_multiple_accounts_per_project(accounts_app):
    """US-IB-37 / AC-IB-37-03；OQ-IB-28 / ADR-21-R1（N:1）/ ADR-40 ③。

    「唯一」= **账号归属项目唯一**，而非「一个项目有且仅有一个账号」：同一项目建第二个
    账号必须 **201**（不加 `users.project_id` 唯一约束）。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    first = _create_ops(client, token, "ops_a1", "p_alpha")
    assert first.status_code == 201, first.content
    second = _create_ops(client, token, "ops_a2", "p_alpha")
    assert second.status_code == 201, second.content

    body1, body2 = json.loads(first.content), json.loads(second.content)
    assert body1["project_id"] == body2["project_id"] == "p_alpha"
    assert body1["user_id"] != body2["user_id"]

    listed = json.loads(client.get("/api/accounts", **h).content)["items"]
    bound = {u["username"] for u in listed if u["project_id"] == "p_alpha"}
    assert {"ops_a1", "ops_a2"} <= bound, f"同项目多账号未同时出现在账户列表：{bound}"


# --------------------------------------------------------------------------- #
# TC-INT-155 顺序依赖的错误码顺序：422 先于 400 / 409
# --------------------------------------------------------------------------- #


def test_TC_INT_155_project_check_error_code_ordering(accounts_app):
    """US-IB-37 / AC-IB-37-02；REQ-FUNC-IB-45 约束①（先建项目、后建账号）。

    `POST /api/accounts` 的判定序（服务层）：
      参数缺失 → **400** → 目标项目未登记 / 未启用 → **422** → 口令强度 → 400 → 创建冲突 → 409。
    故「项目不存在」应压过**口令强度**（400）与**用户名冲突**（409）；而**参数缺失**更靠前。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)
    assert _create_ops(client, token, "ops_a", "p_alpha").status_code == 201

    # 项目不存在 + 参数缺失 → 400（缺参先于项目校验）。
    missing_fields = client.post(
        "/api/accounts",
        data=json.dumps({"password": R13_OPS_PASSWORD, "project_id": "p_missing"}),
        content_type="application/json",
        **h,
    )
    assert missing_fields.status_code == 400, missing_fields.content

    # 项目不存在 + 弱口令 → 422（项目校验先于口令强度）。
    weak = client.post(
        "/api/accounts",
        data=json.dumps({"username": "ops_w", "password": "x", "project_id": "p_missing"}),
        content_type="application/json",
        **h,
    )
    assert weak.status_code == 422, weak.content
    assert json.loads(weak.content)["error"]["code"] == "project_not_active"

    # 项目不存在 + 用户名已被占用 → 422（项目校验先于创建冲突 409）。
    conflict = client.post(
        "/api/accounts",
        data=json.dumps(
            {"username": "ops_a", "password": R13_OPS_PASSWORD, "project_id": "p_missing"}
        ),
        content_type="application/json",
        **h,
    )
    assert conflict.status_code == 422, conflict.content
    assert json.loads(conflict.content)["error"]["code"] == "project_not_active"

    # 对照：项目存在 + 用户名冲突 → 409（顺序依赖不掩盖真实冲突）。
    dup = _create_ops(client, token, "ops_a", "p_alpha")
    assert dup.status_code == 409, dup.content

    # 对照：项目存在 + 弱口令 → 400。
    weak_ok_project = client.post(
        "/api/accounts",
        data=json.dumps({"username": "ops_w2", "password": "x", "project_id": "p_alpha"}),
        content_type="application/json",
        **h,
    )
    assert weak_ok_project.status_code == 400, weak_ok_project.content


# --------------------------------------------------------------------------- #
# TC-INT-156 软删项目不级联账号（ADR-40 ④）
# --------------------------------------------------------------------------- #


def test_TC_INT_156_project_soft_delete_does_not_cascade_accounts(accounts_app):
    """US-IB-38 / AC-IB-38-03；ADR-40 ④（删除账号不随项目级联）。

    软删项目后：项目不再出现在活动列表（`GET /api/projects`），但**其账号仍在且仍 active**
    ——「软删项目亦不删除其账号，保留可恢复」。
    """
    deps, _ = accounts_app
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    created = _create_ops(client, token, "ops_a", "p_alpha")
    assert created.status_code == 201, created.content
    ops = json.loads(created.content)

    disabled = client.delete(
        "/api/projects/p_alpha",
        data=json.dumps({"confirm_project_id": "p_alpha"}),
        content_type="application/json",
        **h,
    )
    assert disabled.status_code == 200, disabled.content
    assert json.loads(disabled.content)["status"] == "disabled"

    # 项目不再在活动列表（列表 = 活动项目）。
    listed = json.loads(client.get("/api/projects", **h).content)["items"]
    assert "p_alpha" not in {i["project_id"] for i in listed}
    # 但注册表行仍在（可恢复，非物理删除）。
    assert deps.project_registry.load("p_alpha").status == "disabled"

    # 账号未被级联删除 / 停用。
    accounts = json.loads(client.get("/api/accounts", **h).content)["items"]
    target = next((u for u in accounts if u["user_id"] == ops["user_id"]), None)
    assert target is not None, "软删项目把其账号一起删除了（ADR-40 ④ 被破坏）"
    assert target["status"] == "active", target
    assert target["project_id"] == "p_alpha"


# --------------------------------------------------------------------------- #
# TC-INT-157 软删项目数据保留：不物理级联删库（OOS-19）
# --------------------------------------------------------------------------- #


def test_TC_INT_157_project_soft_delete_retains_ledger_documents(accounts_app):
    """US-IB-36 / AC-IB-36-03；OQ-IB-27 / OOS-19（物理级联删除移出本轮）。

    软删项目后其**台账数据仍在**（数据保留、可恢复）：上传的文档行数不变、doc_id 仍在。
    """
    from ib.core import Scope

    deps, _ = accounts_app
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    up = SimpleUploadedFile("keep.txt", "保留内容".encode("utf-8"))
    uploaded = client.post("/api/files", {"file": up}, HTTP_X_IB_PROJECT="p_alpha", **h)
    assert uploaded.status_code == 201, uploaded.content
    doc_id = json.loads(uploaded.content)["doc_id"]

    def _docs():
        items, total = deps.ledger.list_documents(
            Scope("p_alpha"), page=1, page_size=50, status=None
        )
        return total, {d.doc_id for d in items}

    before_total, before_ids = _docs()
    assert before_total >= 1 and doc_id in before_ids

    disabled = client.delete(
        "/api/projects/p_alpha",
        data=json.dumps({"confirm_project_id": "p_alpha"}),
        content_type="application/json",
        **h,
    )
    assert disabled.status_code == 200, disabled.content

    after_total, after_ids = _docs()
    assert after_total == before_total, "软删项目改变了台账行数（物理级联删除？OOS-19）"
    assert doc_id in after_ids, "软删项目删除了台账文档（数据未保留）"


# --------------------------------------------------------------------------- #
# TC-INT-158 LLM Key 未配置态：masked == ""（AC-IB-39-01）
# --------------------------------------------------------------------------- #


def test_TC_INT_158_llm_key_unconfigured_masked_is_empty(accounts_app):
    """US-IB-39 / AC-IB-39-01 / AC-IB-39-02；ADR-38 / ADR-39 Option C。

    未配置态：`configured=False`、`masked==""`、`updated_at=None`；写入 → 掩码非空；
    清空 → **回到同一未配置态**（掩码同样为空，不残留上一次的掩码）。
    """
    from ib.core import LLM_KEY_MASK

    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    initial = json.loads(client.get("/api/llm-key", **h).content)
    assert set(initial) == {"configured", "masked", "updated_at"}, initial
    assert initial["configured"] is False
    assert initial["masked"] == "", initial
    assert initial["updated_at"] is None

    put = json.loads(
        client.put(
            "/api/llm-key",
            data=json.dumps({"secret": _FAKE_SECRET}),
            content_type="application/json",
            **h,
        ).content
    )
    assert put["configured"] is True and put["masked"] == LLM_KEY_MASK

    assert client.delete("/api/llm-key", **h).status_code == 204
    after = json.loads(client.get("/api/llm-key", **h).content)
    assert after["configured"] is False and after["masked"] == "" and after["updated_at"] is None


# --------------------------------------------------------------------------- #
# TC-INT-159 审计只记 outcome：不含 Key 值 / 掩码 / 前缀（C-IB-42）
# --------------------------------------------------------------------------- #


def test_TC_INT_159_llm_key_audit_never_records_secret(accounts_app, monkeypatch):
    """US-IB-39 / AC-IB-39-03；C-IB-42 / REQ-NFR-IB-20（审计只记 `outcome`）。

    捕获全部 `log_event` 调用：写入 / 清空 Key 后，**任何**审计载荷都不得含明文 Key、
    掩码（`LLM_KEY_MASK`）或明文前缀（`sk-`）。
    """
    from ib.core import LLM_KEY_MASK
    import ib.observability as observability

    captured: list[str] = []
    real_log_event = observability.log_event

    def _spy(*args, **kwargs):
        captured.append(json.dumps([args, kwargs], ensure_ascii=False, default=str))
        return real_log_event(*args, **kwargs)

    monkeypatch.setattr(observability, "log_event", _spy)

    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    assert client.put(
        "/api/llm-key",
        data=json.dumps({"secret": _FAKE_SECRET}),
        content_type="application/json",
        **h,
    ).status_code == 200
    assert client.delete("/api/llm-key", **h).status_code == 204

    joined = "\n".join(captured)
    assert _FAKE_SECRET not in joined, "审计载荷含明文 Key"
    assert LLM_KEY_MASK not in joined, "审计载荷含掩码"
    assert "sk-" not in joined, "审计载荷含明文前缀"
    # 事件本身仍在（不静默）——只记 outcome。
    assert '"updated"' in joined and '"cleared"' in joined, joined


# --------------------------------------------------------------------------- #
# TC-INT-160 任何响应体（含错误体）不含明文 Key（AC-IB-39-03）
# --------------------------------------------------------------------------- #


def test_TC_INT_160_no_response_body_contains_plaintext_key(accounts_app):
    """US-IB-39 / AC-IB-39-03；C-IB-42（任何 API 不得回显明文 Key）。

    成功体与**错误体**（空值 400 / 查询串令牌 400）一律不得出现明文（连前缀都不含）；
    错误体亦不得回显掩码。
    """
    from ib.core import LLM_KEY_MASK

    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    put = client.put(
        "/api/llm-key",
        data=json.dumps({"secret": _FAKE_SECRET}),
        content_type="application/json",
        **h,
    )
    get = client.get("/api/llm-key", **h)
    empty = client.put(
        "/api/llm-key",
        data=json.dumps({"secret": "   "}),
        content_type="application/json",
        **h,
    )
    bad_query = client.get("/api/llm-key?token=x", **h)

    for response, label in (
        (put, "PUT 成功体"),
        (get, "GET 成功体"),
    ):
        text = _body(response)
        assert _FAKE_SECRET not in text, f"{label} 回显了明文 Key"
        assert "sk-" not in text, f"{label} 回显了明文前缀"

    assert empty.status_code == 400, empty.content
    assert bad_query.status_code == 400, bad_query.content
    for response, label in ((empty, "空值错误体"), (bad_query, "查询串令牌错误体")):
        text = _body(response)
        assert _FAKE_SECRET not in text and "sk-" not in text, f"{label} 回显了明文"
        assert LLM_KEY_MASK not in text, f"{label} 回显了掩码"


# --------------------------------------------------------------------------- #
# TC-INT-161 D-R18-01：运行期新建项目的可用性边界（**按裁决属预期行为**）
# --------------------------------------------------------------------------- #


def test_TC_INT_161_runtime_project_usable_only_after_config_registration_and_restart(accounts_app):
    """US-IB-36 / US-IB-37 / US-IB-44；**D-R18-01（已裁决的交付边界）** / ADR-32 / ADR-37 / ADR-41。

    运行期经 `POST /api/projects` 新建的项目：**可建账号、可被 `GET /api/projects` 枚举**；
    但**检索 / 上传须等「配置侧登记 + 由用户手工重启服务」后才完全可用**
    （`load_project_record` 对不在配置文件中的项目抛 `ConfigError` 类错误；`kb_id ≡ project_id`
    时上传路径拿不到归属登记）。用户已明确接受此能力边界 —— **登记为交付边界，非缺陷**。

    本用例断言的是**清晰的边界错误**（HTTP 层面为 `scope_violation` / `startup_error`，
    均带可读消息），**不是**崩溃、也不是静默的错误结果。
    """
    deps, _ = accounts_app
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    created = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "p_gamma", "name": "伽马项目"}),
        content_type="application/json",
        **h,
    )
    assert created.status_code == 201, created.content
    assert json.loads(created.content)["status"] == "active"

    # 边界内的能力：可建账号。
    account = _create_ops(client, token, "ops_g", "p_gamma")
    assert account.status_code == 201, account.content
    assert json.loads(account.content)["project_id"] == "p_gamma"

    # 边界内的能力：可被枚举。
    listed = json.loads(client.get("/api/projects", **h).content)["items"]
    assert "p_gamma" in {i["project_id"] for i in listed}

    # 边界之外：上传 fail-closed（kb 归属登记须由配置侧播种 + 重启）—— 403，可读错误。
    up = SimpleUploadedFile("g.txt", "内容".encode("utf-8"))
    upload = client.post("/api/files", {"file": up}, HTTP_X_IB_PROJECT="p_gamma", **h)
    assert upload.status_code == 403, upload.content
    assert json.loads(upload.content)["error"]["code"] == "scope_violation"

    # 边界之外：检索路径在**调用期** fail-closed —— 清晰边界错误（点名项目未登记），非静默。
    chat = client.get(
        "/api/chat/stream?q=%E4%BD%A0%E5%A5%BD&session_id=d-r18-01", HTTP_X_IB_PROJECT="p_gamma", **h
    )
    assert chat.status_code == 500, _body(chat)
    chat_body = json.loads(_body(chat))
    assert chat_body["error"]["code"] == "startup_error", chat_body
    assert "p_gamma" in chat_body["error"]["message"], chat_body

    # 对照：已登记项目（配置侧播种）上传正常 —— 边界确实只在「未登记项目」上。
    ok = client.post(
        "/api/files", {"file": SimpleUploadedFile("a.txt", "内容".encode("utf-8"))},
        HTTP_X_IB_PROJECT="p_alpha", **h,
    )
    assert ok.status_code == 201, ok.content

    # 注册表侧确为「配置快照 + 运行期状态」两源：Deps.projects 仍只有配置登记的两个项目。
    assert set(getattr(deps, "projects", {}).keys()) == {"p_alpha", "p_beta"}


# --------------------------------------------------------------------------- #
# TC-INT-162 资料列表按项目域隔离（AC-IB-40-03）
# --------------------------------------------------------------------------- #


def test_TC_INT_162_file_list_is_project_scoped(accounts_app):
    """US-IB-40 / AC-IB-40-03；ADR-41 / OQ-IB-30（资料管理改项目域视图）。

    上传到 `p_alpha` 的文档只在 `p_alpha` 项目域可见；`p_beta` 项目域**看不到**它
    （请求体不携带 kb 字段，范围由已认证主体的 `project_id` 决定）。
    """
    client = _client(accounts_app)
    token = _login_admin(client)
    h = bearer(token)

    up = SimpleUploadedFile("scope.txt", "内容".encode("utf-8"))
    uploaded = client.post("/api/files", {"file": up}, HTTP_X_IB_PROJECT="p_alpha", **h)
    assert uploaded.status_code == 201, uploaded.content
    doc_id = json.loads(uploaded.content)["doc_id"]

    alpha = json.loads(client.get("/api/files", HTTP_X_IB_PROJECT="p_alpha", **h).content)
    assert any(item["doc_id"] == doc_id for item in alpha["items"]), alpha

    beta = json.loads(client.get("/api/files", HTTP_X_IB_PROJECT="p_beta", **h).content)
    assert all(item["doc_id"] != doc_id for item in beta["items"]), beta
    assert beta["total"] == 0, f"p_beta 项目域看到了 p_alpha 的文件：{beta}"
