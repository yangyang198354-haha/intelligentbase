"""集成测试层 —— REV-19 增量（可视化配置项目域切换 + 创建期种子 + 专家域 fail-closed）。

逐条溯源 REV-19 的需求 / AC / ADR：

  * AC-IB-42-01（配置页按项目域加载 —— 切到项目 B 加载 B 的定义，非 A / 非全局一份）；
  * AC-IB-42-02（保存只写回当前项目，项目 A 不受影响）；
  * AC-IB-42-03（重载与编辑结果一致 —— round-trip 无漂移）；
  * AC-IB-42-06（不回显任何凭据 / 路径值；零 Cookie）；
  * AC-IB-41-01（两项目各自专家集，互不可见）；
  * AC-IB-41-04（未登记 / 越界项目 → 拒绝 + 结构化日志 + 不回退）；
  * AC-IB-44-01（`POST /api/projects` 创建期**同步**播种默认定义文档）；
  * AC-IB-45-02 / AC-IB-45-03（非 demo 项目不出现三专家 / 不可调用）；
  * AC-IB-43-05（未登记 / 越界项目的问答请求 fail-closed，不回退）。

红线：非 admin 一律服务端 403（ADR-42）；全程零 `Set-Cookie`；凭据只经环境变量注入，
测试内不出现任何真实 token / key。离线：内存账户 + 内存 / 临时目录定义存储 + Django test
Client，不触网、不碰生产路径。

**观测项（DEFECT-R19-D-01）**：`test_TC_INT_R19_006` 断言专家域 fail-closed 路径产出**结构化
日志**（`log_event("expert_domain", …, project_id=…, reason=…)`，见 `module_design.md` §13 /
ADR-47 / AC-IB-41-04）；当前实现只抛结构化异常，**未**产出该日志 → 本用例**如实失败**。
"""

from __future__ import annotations

import json

from conftest import R13_ADMIN_PASSWORD, bearer, change_password, login

DEF = "/api/config/definition"
DEF_PATH_HEADER = "HTTP_X_IB_PROJECT"

#: 测试内占位口令（**非生产凭据**，性质同 conftest 的 `groupd-offline-token`）。
_ADMIN_NEW_PW = "Rev19-Admin-New!"


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


def _valid_doc(project_id: str, expert_names: tuple[str, ...]):
    """构造一份**合法**定义文档（恰一个默认专家，单一默认编排流，OOS-21）。"""
    from ib.config import build_definition_document
    from ib.core import (
        ConditionalEdgeSpec,
        EdgeSpec,
        ExpertSpecInput,
        OrchestrationSpecInput,
        RouteSpecInput,
        ToolGrantSpec,
    )

    experts = tuple(
        ExpertSpecInput(
            name=name,
            cn_label=f"标签{name}",
            keywords=(f"kw{name}",),
            exemplars=(),
            is_data_expert=False,
            is_delegating=False,
            is_default=(i == 0),
        )
        for i, name in enumerate(expert_names)
    )
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=RouteSpecInput(
            tau=0.65, margin=0.05, max_expert_steps=8, default_expert=expert_names[0]
        ),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "expert", "general", "gate", "aggregate"),
            conditional_edges=(
                ConditionalEdgeSpec(
                    from_node="route",
                    branch_map=(("expert", "expert"), ("general", "general")),
                ),
            ),
            edges=(
                EdgeSpec(from_node="START", to_node="route"),
                EdgeSpec(from_node="expert", to_node="gate"),
                EdgeSpec(from_node="gate", to_node="aggregate"),
                EdgeSpec(from_node="general", to_node="aggregate"),
                EdgeSpec(from_node="aggregate", to_node="END"),
            ),
        ),
        tool_grants=tuple(
            ToolGrantSpec(expert_name=name, tool_names=("search_knowledge",))
            for name in expert_names
        ),
    )


def _inject_definitions(deps, docs: dict):
    """把**按项目不同**的定义文档注入当前 deps 并重绑全局（供端点按项目域加载）。"""
    from ib.config import InMemoryDefinitionDocumentStore
    from ibweb.composition import build_application, known_tool_names

    deps.definition_store = InMemoryDefinitionDocumentStore(
        documents=docs, known_tools=known_tool_names()
    )
    build_application(deps)


# --------------------------------------------------------------------------- #
# TC-INT-R19-001 —— AC-IB-42-01：配置页按项目域加载（B 的定义 ≠ A 的定义）
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_001_config_page_loads_per_project_definition(accounts_app):
    """US-IB-42 / AC-IB-42-01；OQ-IB-32(b) / ADR-44。

    切换作用域到项目 B → 页面加载**项目 B** 的专家定义（非项目 A / 非全局唯一一份）。
    """
    deps, Client = accounts_app
    _inject_definitions(
        deps,
        {
            "p_alpha": _valid_doc("p_alpha", ("alpha-agent",)),
            "p_beta": _valid_doc("p_beta", ("beta-agent",)),
        },
    )
    client = Client()
    h = bearer(_login_admin(client))

    a = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_alpha"}).content)["document"]
    b = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_beta"}).content)["document"]

    assert [e["name"] for e in a["experts"]] == ["alpha-agent"]
    assert [e["name"] for e in b["experts"]] == ["beta-agent"]
    assert a["project_id"] == "p_alpha" and b["project_id"] == "p_beta"


# --------------------------------------------------------------------------- #
# TC-INT-R19-002 —— AC-IB-42-02：保存只写回当前项目，项目 A 不受影响
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_002_save_writes_only_current_project(accounts_app):
    """US-IB-42 / AC-IB-42-02；`<root>/<project_id>/<expert_name>/` 语义 / ADR-44。

    在项目 B 下编辑并保存 → 只写回项目 B 的定义文档；项目 A 的定义**逐位不变**。
    """
    deps, Client = accounts_app
    docs = {
        "p_alpha": _valid_doc("p_alpha", ("alpha-agent",)),
        "p_beta": _valid_doc("p_beta", ("beta-agent",)),
    }
    _inject_definitions(deps, docs)
    client = Client()
    h = bearer(_login_admin(client))

    alpha_hash_before = deps.definition_store.load("p_alpha").content_hash
    beta = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_beta"}).content)["document"]
    edited = json.loads(json.dumps(beta))
    edited["experts"][0]["cn_label"] = "项目B专用标签"

    put = client.put(
        DEF,
        data=json.dumps({"document": edited, "expected_content_hash": beta["content_hash"]}),
        content_type="application/json",
        **h,
        **{DEF_PATH_HEADER: "p_beta"},
    )
    assert put.status_code == 200, put.content

    b_after = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_beta"}).content)["document"]
    a_after = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_alpha"}).content)["document"]
    assert b_after["experts"][0]["cn_label"] == "项目B专用标签", "项目 B 未写入"
    assert a_after["experts"][0]["cn_label"] == "标签alpha-agent", "项目 A 被牵连改动"
    assert deps.definition_store.load("p_alpha").content_hash == alpha_hash_before


# --------------------------------------------------------------------------- #
# TC-INT-R19-003 —— AC-IB-42-03：重载与编辑结果一致（round-trip 无漂移）
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_003_save_then_reload_roundtrip(accounts_app):
    """US-IB-42 / AC-IB-42-03；REQ-FUNC-IB-25 / IFC-IB-383。

    一次成功的按项目保存后，重新载入该项目定义 → 与编辑结果一致（无漂移）。
    """
    deps, Client = accounts_app
    _inject_definitions(deps, {"p_beta": _valid_doc("p_beta", ("beta-agent",))})
    client = Client()
    h = bearer(_login_admin(client))

    beta = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_beta"}).content)["document"]
    edited = json.loads(json.dumps(beta))
    edited["route"]["tau"] = 0.72

    put = client.put(
        DEF,
        data=json.dumps({"document": edited, "expected_content_hash": beta["content_hash"]}),
        content_type="application/json",
        **h,
        **{DEF_PATH_HEADER: "p_beta"},
    )
    assert put.status_code == 200, put.content

    reloaded = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_beta"}).content)["document"]
    assert reloaded["route"]["tau"] == 0.72, "round-trip 出现漂移"
    assert reloaded["content_hash"] == json.loads(put.content)["content_hash"]


# --------------------------------------------------------------------------- #
# TC-INT-R19-004 —— AC-IB-42-06：配置页回执不回显凭据，且不破坏前端红线
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_004_config_response_echoes_no_credentials(accounts_app):
    """US-IB-42 / AC-IB-42-06；C-IB-02 / IFC-IB-297。

    GET/PUT 回执**只登记键名**、不含任何凭据 / 路径值；全程零 `Set-Cookie`（前端红线）。
    """
    deps, Client = accounts_app
    _inject_definitions(deps, {"p_alpha": _valid_doc("p_alpha", ("alpha-agent",))})
    client = Client()
    h = bearer(_login_admin(client))

    resp = client.get(DEF, **h, **{DEF_PATH_HEADER: "p_alpha"})
    assert resp.status_code == 200, resp.content
    assert not resp.cookies, "配置页不得下发任何 Cookie（前端红线）"
    payload = json.loads(resp.content)
    # 只登记键名（值不回显）：键名集合固定，且响应体不含任何凭据样态。
    assert payload["config_key_names"] == ["IB_DEFINITION_DOC_PATH", "IB_VISUAL_CONFIG_ENABLED"]
    raw = resp.content.decode("utf-8")
    for bad in ("sk-", "Bearer ", "password", "secret", "token"):
        assert bad not in raw, f"配置回执疑似回显凭据样态：{bad!r}"


# --------------------------------------------------------------------------- #
# TC-INT-R19-005 —— AC-IB-41-04（前半）：未登记项目 fail-closed，不回退
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_005_unregistered_project_failclosed_no_fallback(accounts_app):
    """US-IB-41 / AC-IB-41-04；REQ-NFR-IB-21 / ADR-47。

    请求未登记项目域的专家编排 → 显式拒绝（`StartupError`），**不回退**其他项目作用域。
    """
    from ib.core import StartupError

    deps, _Client = accounts_app
    try:
        deps.orchestrator_for("never_registered")
    except StartupError as exc:
        assert "never_registered" in str(exc), "拒绝信息须含项目标识"
    else:
        raise AssertionError("未登记项目未被 fail-closed 拒绝（存在回退面）")


# --------------------------------------------------------------------------- #
# TC-INT-R19-006 —— AC-IB-41-04（后半）：专家域 fail-closed 须产出结构化日志
#   预期 FAIL —— DEFECT-R19-D-01（见文件头注释）
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_006_expert_domain_failclosed_emits_structured_log(accounts_app, monkeypatch):
    """US-IB-41 / AC-IB-41-04；module_design §13 / ADR-47。

    AC 明文要求「拒绝并产出**结构化日志**（含项目标识与原因）」，设计落点为
    `log_event("expert_domain", <code>, project_id=…, reason=…)`。本用例以探针记录
    专家域 fail-closed 路径的全部 `log_event` 调用，断言其中存在一条**含项目标识**的
    专家域结构化日志 —— 满足「结构化日志可溯源到项目」的可观测性要求。
    """
    import ib.observability as obs

    captured: list[tuple] = []
    real = obs.log_event

    def _spy(stage, outcome, **kw):
        captured.append((stage, outcome, dict(kw)))
        return real(stage, outcome, **kw)

    monkeypatch.setattr(obs, "log_event", _spy)

    deps, _Client = accounts_app
    try:
        deps.orchestrator_for("never_registered")
    except Exception:  # noqa: BLE001 - 拒绝本身已在 TC-INT-R19-005 断言
        pass

    expert_logs = [c for c in captured if "expert" in str(c[0]).lower()]
    assert expert_logs, (
        "专家域 fail-closed 未产出结构化日志（log_event('expert_domain', …)）："
        f"实际捕获 {captured!r} —— DEFECT-R19-D-01"
    )
    assert any(c[2].get("project_id") == "never_registered" for c in expert_logs), (
        "专家域结构化日志未携带项目标识"
    )

    # ------------------------------------------------------------------ #
    # 追加断言（DEFECT-R19-D-01 补强）：AC-IB-41-04 明文要求日志「含项目标识与**原因**」。
    #
    # 关键正确性：必须观察**实际发出**的记录（经 `LOG_FIELDS` 白名单过滤后真正落地的
    # 日志行），而**不能**用上面 `_spy` 捕获的调用侧 kwargs —— 后者位于白名单过滤
    # **之前**：即便有人把 `reason` 从 `LOG_FIELDS` 里摘掉，白名单会**静默丢弃**它，
    # 而探针仍看得到 → 对白名单的破坏断言**假绿**。故此处改在**发射处**（stage logger
    # 的 handler）截获落地 JSON 行：
    #   * (a) 调用侧去掉 `reason=…` 实参 → 落地行无 `reason` → 变红；
    #   * (b) 白名单摘掉 `"reason"` → `redact()` 丢弃 → 落地行无 `reason` → 变红。
    # ------------------------------------------------------------------ #
    import logging
    import re as _re

    emitted: list[dict] = []

    class _CaptureEmitted(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                parsed = json.loads(record.getMessage())
            except Exception:  # noqa: BLE001 - 非 JSON 行与本次断言无关
                return
            if isinstance(parsed, dict):
                emitted.append(parsed)

    stage_logger = logging.getLogger("intelligentbase.expert_domain")
    capture_handler = _CaptureEmitted()
    stage_logger.addHandler(capture_handler)
    try:
        try:
            deps.orchestrator_for("never_registered")
        except Exception:  # noqa: BLE001 - 拒绝本身已在 TC-INT-R19-005 断言
            pass
    finally:
        stage_logger.removeHandler(capture_handler)

    failclosed_emitted = [
        row
        for row in emitted
        if row.get("stage") == "expert_domain"
        and row.get("project_id") == "never_registered"
    ]
    assert failclosed_emitted, (
        "未观察到**实际发出**的专家域 fail-closed 结构化日志（经白名单落地的行）："
        f"{emitted!r}"
    )
    emitted_reasons = [row.get("reason") for row in failclosed_emitted]
    assert all(isinstance(item, str) and item.strip() for item in emitted_reasons), (
        "实际发出的结构化日志未携带**非空** reason："
        f"reasons={emitted_reasons!r} —— AC-IB-41-04（含项目标识与原因）"
    )
    assert all(_re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in emitted_reasons), (
        "reason 非**结构化短码**（疑似自由正文）："
        f"reasons={emitted_reasons!r} —— module_design §13 / ADR-47"
    )


# --------------------------------------------------------------------------- #
# TC-INT-R19-007 —— AC-IB-41-01：两项目各自专家集，互不可见
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_007_two_projects_independent_expert_sets(accounts_app):
    """US-IB-41 / AC-IB-41-01；REQ-FUNC-IB-49 / REQ-NFR-IB-21 / ADR-43。

    项目 A 与项目 B 各自的专家集相互隔离：查看 A 只显示 A 的专家，B 的专家不可见。
    """
    deps, Client = accounts_app
    _inject_definitions(
        deps,
        {
            "p_alpha": _valid_doc("p_alpha", ("alpha-agent",)),
            "p_beta": _valid_doc("p_beta", ("beta-agent",)),
        },
    )
    client = Client()
    h = bearer(_login_admin(client))

    a = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_alpha"}).content)["document"]
    a_names = {e["name"] for e in a["experts"]}
    assert a_names == {"alpha-agent"}
    assert "beta-agent" not in a_names, "项目 A 可见了他项目专家"


# --------------------------------------------------------------------------- #
# TC-INT-R19-008 —— AC-IB-44-01：创建期同步播种默认定义文档
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_008_create_project_seeds_default_document(accounts_app, monkeypatch, tmp_path):
    """US-IB-44 / AC-IB-44-01；REQ-FUNC-IB-52 / ADR-45 / IFC-IB-385。

    `POST /api/projects` 注册表写入成功后**同步调用**种子化：为新建项目 P 写
    `<dir>/P.json`（含恰一个「查询本项目知识库」agent = 默认专家）+ 单一默认编排流。
    """
    monkeypatch.setenv("IB_DEFINITION_DOC_PATH", str(tmp_path))
    deps, Client = accounts_app
    client = Client()
    h = bearer(_login_admin(client))

    r = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "newproj", "name": "新项目"}),
        content_type="application/json",
        **h,
    )
    assert r.status_code == 201, r.content

    seed_file = tmp_path / "newproj.json"
    assert seed_file.is_file(), "创建期未按项目落地种子定义文档"
    doc = json.loads(seed_file.read_text(encoding="utf-8"))
    assert [e["name"] for e in doc["experts"]] == ["kb-agent"], "新建项目默认专家应恰为 1 个 KB agent"
    assert doc["route"]["default_expert"] == "kb-agent"
    assert len(doc["orchestration"]["nodes"]) > 0, "种子须含单一默认编排流"


# --------------------------------------------------------------------------- #
# TC-INT-R19-009 —— AC-IB-45-02 / AC-IB-45-03：非 demo 种子不含 / 不可调用三专家
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_009_non_demo_seed_excludes_demo_experts(tmp_path):
    """US-IB-45 / AC-IB-45-02、AC-IB-45-03；OQ-IB-35(a) / OQ-IB-34(a) / ADR-45。

    非 demo 项目（新建）的种子定义**不出现**三专家中任何一个；以该种子视图路由「本应由
    demo 专属专家处理」的问句 → 由本项目专家集处理，**不调用**三专家（硬隔离）。
    """
    from ib.config import FileDefinitionDocumentStore
    from ib.core import Scope
    from ib.experts import DEMO_EXPERT_NAMES, resolve_expert_registry
    from ib.routing import IntentRouter
    from ibweb.composition import seed_project

    defs = tmp_path / "defs"
    res = seed_project("proj_nondemo", definition_dir=str(defs), prompt_root=str(tmp_path / "p"))
    assert res.created is True

    store = FileDefinitionDocumentStore(str(defs), known_tools=frozenset())
    doc = store.load("proj_nondemo")
    names = {e.name for e in doc.experts}
    assert not (names & set(DEMO_EXPERT_NAMES)), f"非 demo 项目种子出现三专家：{names}"

    view = resolve_expert_registry("proj_nondemo", view=store.derive(doc))
    d = IntentRouter(experts=view).classify_experts(
        "巡检一下 PLC 故障", scope=Scope(project_id="proj_nondemo")
    )
    assert not (set(d.experts) & set(DEMO_EXPERT_NAMES)), "非 demo 项目调用了三专家"


# --------------------------------------------------------------------------- #
# TC-INT-R19-010 —— AC-IB-43-05：越界项目问答 fail-closed，不回退
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_010_question_out_of_scope_project_failclosed(accounts_app):
    """US-IB-43 / AC-IB-43-05；REQ-NFR-IB-21 / ADR-47。

    未登记 / 越界项目的问答请求 → fail-closed 拒绝（非 200），**不回退**到其他项目。
    """
    deps, Client = accounts_app
    client = Client()
    h = bearer(_login_admin(client))

    resp = client.get(
        "/api/chat/stream",
        {"q": "随便问一句", "session_id": "s1"},
        **h,
        **{DEF_PATH_HEADER: "never_registered"},
    )
    assert resp.status_code != 200, "越界项目问答未被拒绝"
    assert resp.status_code >= 400
    body = resp.content.decode("utf-8", errors="replace")
    assert "never_registered" in body or "startup_error" in body, body


# --------------------------------------------------------------------------- #
# TC-INT-R19-011 —— `reload_projects()` 须同步刷新装配期每项目工件
# --------------------------------------------------------------------------- #


def test_TC_INT_R19_011_hot_registered_project_gets_prompt_store(accounts_app, monkeypatch, tmp_path):
    """US-IB-42 / AC-IB-42-01 延伸；IFC-IB-339 / 345 / 352。

    缺陷现象：`prompt_stores` / `definitions` / `derived_views` 皆为**装配期一次性**构建，
    而 `reload_projects()` 此前只刷新 `projects` —— 于是**热登记**的项目在 `prompt_stores`
    中缺条目，`/api/config/prompts` 对该项目 fail-closed **503**（定义文档因经单实例存储
    按需读取而不受影响，故线上表现为「提示词区不可用、定义页正常」）。

    本用例断言：`POST /api/projects` 之后，新项目三份工件齐备且提示词列表端点 **200**。
    """
    from ib.config import FileDefinitionDocumentStore
    from ibweb.composition import known_tool_names

    # 与生产同构：定义域取**文件态**。离线夹具默认走内存默认文档，`seed_project` 落盘的
    # 文件它读不到 —— 那样就测不到「种子落盘 → 热重载装载」这条真实链路。
    monkeypatch.setenv("IB_DEFINITION_DOC_PATH", str(tmp_path))
    deps, Client = accounts_app
    deps.definition_store = FileDefinitionDocumentStore(
        str(tmp_path), known_tools=known_tool_names()
    )

    client = Client()
    h = bearer(_login_admin(client))

    r = client.post(
        "/api/projects",
        data=json.dumps({"project_id": "hotproj", "name": "热登记项目"}),
        content_type="application/json",
        **h,
    )
    assert r.status_code == 201, r.content

    assert "hotproj" in deps.prompt_stores, "热登记项目未补入 prompt_stores → /api/config/prompts 将 503"
    assert "hotproj" in deps.definitions, "热登记项目未补入 definitions → 提示词区列不出专家"
    assert "hotproj" in deps.derived_views, "热登记项目未补入 derived_views"

    resp = client.get("/api/config/prompts", **h, **{DEF_PATH_HEADER: "hotproj"})
    assert resp.status_code == 200, resp.content
    payload = json.loads(resp.content)
    assert [e["name"] for e in payload["experts"]] == ["kb-agent"]
    assert set(payload["experts"][0]["layers"]) == {"main", "fallback"}
