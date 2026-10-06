"""集成测试层 10/N —— R7 定义文档（单一真源）+ 装配闸门 + 配置端点（IFC-IB-288~296）。

覆盖用户故事：**US-IB-17**（可视化配置：定义文档单一真源 / 白名单 / 往返等价 / 文档为准）、
**US-IB-18**（非法配置装配期 fail-fast / 不静默回退 / 不提供强制继续）。
对应验收标准：AC-IB-17-01/02/03/04/05/06、AC-IB-18-01/02/04/06。

分层依据（test_plan §2）：跨模块协作（`ib.config` ↔ `ib.core` ↔ `ibweb.composition` ↔
`ibweb.views`），含端口接缝与 HTTP 契约，故为**集成级**。单模块纯函数用例见
`tests/unit/test_definition_config_r7.py`。

离线纪律：全程临时文件系统 + 内存替身；无外部网络；测试代码不含真实凭据
（共享令牌来自 `IB_OFFLINE_TOKEN` 占位符）。
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

from conftest import offline_raw

from ib.config import (
    FileDefinitionDocumentStore,
    InMemoryDefinitionDocumentStore,
    build_definition_document,
    document_to_json,
    semantic_hash,
)
from ib.core import (
    ConditionalEdgeSpec,
    ConfigError,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    ToolGrantSpec,
)

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
PATH = "/api/config/definition"

_FRONTEND = pathlib.Path(__file__).resolve().parents[2] / "src" / "frontend"
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _frontend_deps_tracked_by_git() -> list[str]:
    """列出**被 git 跟踪**的 `src/frontend/node_modules/**` 条目（R10 修复：环境自适应判定）。

    分发纪律的判定面是「**仓库是否分发前端依赖**」（`node_modules` **不得入库**），
    而非「磁盘上是否已 `npm ci`」——后者是本地开发 / CI 在 R10 起的**必需**步骤，
    与「依赖不入库」**互不冲突**。故以 **git 跟踪状态**为不变量：
    - 未装依赖：跟踪列表为空 → 通过；
    - 已装但未被跟踪（经 `.gitignore` 忽略）：仍为空 → 通过；
    - 依赖被 `git add -f` 强加入库：非空 → **失败**（不变量被破坏）。

    选用 `git ls-files`（**直接**查询「是否入库」，即不变量本体）而非 `git check-ignore`
    （只校验忽略**规则**是否存在，属间接证据）：前者恰好等价于要守护的不变量。
    """
    proc = subprocess.run(
        ["git", "ls-files", "--", "src/frontend/node_modules"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"git ls-files 执行失败：{proc.stderr.strip()}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


# --------------------------------------------------------------------------- #
# 构造助手
# --------------------------------------------------------------------------- #


def _expert(name: str, cn_label: str | None = None, *, is_default: bool = False) -> ExpertSpecInput:
    """构造一位专家（**关键词 / 标签随 name 派生**，R8 起两位专家互不撞车）。

    R8 说明：`validate` 于 R8 纯追加两项装配期校验（跨专家关键词撞车 / `cn_label` 唯一性），
    故**合法基线**要求每位专家的 `keywords` 与 `cn_label` 互异。此处以 `name` 派生默认值
    （`keywords=(f"k{name}",)`、`cn_label=f"标签{name}"`）—— 仅为**夹具数据**变更，
    不改变任何断言语义（既有断言仍表达「基线合法 → admit 通过」）。
    """
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}" if cn_label is None else cn_label,
        keywords=(f"k{name}",),
        exemplars=(),
        is_data_expert=False,
        fallback_prompt=f"prompt-{name}",
        is_delegating=False,
        is_default=is_default,
    )


def _doc(project_id: str = "p_alpha", **overrides):
    base = dict(
        project_id=project_id,
        experts=(_expert("a", is_default=True), _expert("b")),
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="a"),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
        ),
        tool_grants=(ToolGrantSpec("a", ("search_knowledge",)),),
    )
    base.update(overrides)
    return build_definition_document(**base)


def _file_store(tmp_path, *, project_id: str = "p1") -> FileDefinitionDocumentStore:
    return FileDefinitionDocumentStore(
        str(tmp_path / f"{project_id}.definition.json"), known_tools=frozenset({"search_knowledge"})
    )


def _strip_comments(text: str) -> str:
    import re

    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"^[ \t]*//.*$", "", text, flags=re.MULTILINE)
    return text


# --------------------------------------------------------------------------- #
# TC-INT-079 —— AC-IB-17-01：定义文档是唯一持久化真源（原子写回、无第二副本）
# --------------------------------------------------------------------------- #


def test_TC_INT_079_definition_store_is_single_persistent_source(tmp_path):
    """[TC-INT-079] US-IB-17 / AC-IB-17-01：写回落到**定义文档**这一份本地文件，无第二副本。

    对应 AC：「变更被写回定义文档（唯一真源）；重载后内容与保存结果一致；
    系统中不存在任何独立于定义文档的第二份持久化副本」。
    """
    store = _file_store(tmp_path)
    doc = _doc("p1")
    result = store.save("p1", doc, expected_content_hash=None)
    assert result.ok is True and result.conflict is False

    # 目录内**恰好一个**文件：无临时文件残留、无第二份持久化副本
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["p1.definition.json"], f"定义文档目录出现多余文件（第二副本/临时残留）：{files}"

    # 文件内容即文档序列化（稳定键序），可人读 diff
    assert (tmp_path / "p1.definition.json").read_text(encoding="utf-8") == document_to_json(doc)

    # 重载逐字一致（无漂移）
    reloaded = store.load("p1")
    assert reloaded.content_hash == doc.content_hash
    assert document_to_json(reloaded) == document_to_json(doc)

    # 覆盖写（新内容）后仍只有一份文件，且内容已更新
    updated = _doc("p1", route=RouteSpecInput(0.72, 0.05, 8, "a"))
    assert store.save("p1", updated, expected_content_hash=reloaded.content_hash).ok is True
    assert sorted(p.name for p in tmp_path.iterdir()) == ["p1.definition.json"]
    assert store.load("p1").route.tau == 0.72


# --------------------------------------------------------------------------- #
# TC-INT-080 —— AC-IB-17-02：经存储的往返不产生语义漂移
# --------------------------------------------------------------------------- #


def test_TC_INT_080_store_roundtrip_has_no_semantic_drift(tmp_path):
    """[TC-INT-080] US-IB-17 / AC-IB-17-02：写入 → 重载 → 原样回写，语义哈希不变、逐项无增删改。"""
    store = _file_store(tmp_path)
    original = _doc("p1")
    store.save("p1", original, expected_content_hash=None)
    loaded = store.load("p1")

    assert semantic_hash(loaded) == semantic_hash(original)
    assert len(loaded.experts) == len(original.experts)
    assert loaded.route == original.route
    assert tuple(loaded.orchestration.nodes) == tuple(original.orchestration.nodes)
    assert tuple(loaded.tool_grants) == tuple(original.tool_grants)

    # 「打开后不做任何修改直接回写」→ 成功且哈希不变（乐观并发基线一致）
    again = store.save("p1", loaded, expected_content_hash=loaded.content_hash)
    assert again.ok is True and again.conflict is False
    assert store.load("p1").content_hash == loaded.content_hash == original.content_hash


# --------------------------------------------------------------------------- #
# TC-INT-081 —— AC-IB-17-03 / AC-IB-17-01：以文档为准；乐观并发拒绝静默覆盖
# --------------------------------------------------------------------------- #


def test_TC_INT_081_document_is_authoritative_and_conflicts_are_rejected(tmp_path):
    """[TC-INT-081] US-IB-17 / AC-IB-17-03：界面外改动以**文档**为准刷新；陈旧视图回写被 409 拒绝且不落盘。

    对应 AC：「界面以定义文档为准刷新，不得用视图内的陈旧副本反向覆盖文档；
    不一致的内容不被静默丢弃，而是以可读方式报告」。
    """
    store = _file_store(tmp_path)
    v1 = _doc("p1")
    store.save("p1", v1, expected_content_hash=None)

    # 模拟「界面之外被改动」：直接改写定义文档文件
    v2 = _doc("p1", route=RouteSpecInput(0.80, 0.05, 8, "a"))
    (tmp_path / "p1.definition.json").write_text(document_to_json(v2), encoding="utf-8")
    assert store.load("p1").route.tau == 0.80, "重载未以文档为准"

    # 带**陈旧**基线回写 → 冲突：不覆盖、不落盘，给可读回执
    stale = store.save("p1", _doc("p1", route=RouteSpecInput(0.10, 0.05, 8, "a")), expected_content_hash=v1.content_hash)
    assert stale.ok is False and stale.conflict is True
    assert stale.errors and all(i.path and i.code and i.message for i in stale.errors)
    assert any(i.code == "content_hash_conflict" for i in stale.errors)
    assert json.loads((tmp_path / "p1.definition.json").read_text(encoding="utf-8"))["route"]["tau"] == 0.80

    # 带**当前**基线回写 → 成功，落盘为新内容
    v3 = _doc("p1", route=RouteSpecInput(0.30, 0.05, 8, "a"))
    fresh = store.save("p1", v3, expected_content_hash=store.load("p1").content_hash)
    assert fresh.ok is True and store.load("p1").route.tau == 0.30


# --------------------------------------------------------------------------- #
# TC-INT-082 —— AC-IB-18-06 / AC-IB-18-02：装配期准入闸门 fail-fast（聚合全部校验项）
# --------------------------------------------------------------------------- #


def test_TC_INT_082_admit_gate_rejects_aggregating_all_items():
    """[TC-INT-082] US-IB-18 / AC-IB-18-06 + AC-IB-18-02：`admit` 在装配期拒绝非法定义，
    **聚合全部**校验项且无强制继续通道。对应「错误在装配期即被报出，不推迟到首次提问」。
    """
    from ibweb.composition import admit

    store = InMemoryDefinitionDocumentStore(known_tools=frozenset({"search_knowledge"}))
    bad = _doc(
        "p1",
        experts=(_expert("a", is_default=True), _expert("a", is_default=True)),  # 重名 + 两个默认
        route=RouteSpecInput(1.5, 0.05, 0, "ghost"),  # 阈值越界 + 默认专家未知
        tool_grants=(ToolGrantSpec("a", ("ghost-tool",)),),  # 未知工具
    )
    from ib.config import validate as _validate

    expected = _validate(bad, known_tools=frozenset({"search_knowledge"}))
    assert expected.ok is False and len(expected.errors) >= 5

    try:
        admit(bad, store=store)
        raise AssertionError("非法定义竟通过装配期闸门")
    except ConfigError as exc:
        msg = str(exc)
        assert "拒绝装配" in msg and f"{len(expected.errors)} 项" in msg, msg
        items = getattr(exc, "validation_items", None)
        assert items is not None, "聚合的校验项未随异常附带（无法逐条回执）"
        assert len(items) == len(expected.errors), (len(items), len(expected.errors))
        assert {i.code for i in items} == {i.code for i in expected.errors}
        for i in items:
            assert i.path and i.code and i.message

    # 合法定义 → 通过闸门并派生出装配所需只读视图（确定性）
    good = _doc("p1")
    view = admit(good, store=store)
    assert [e.name for e in view.experts] == ["a", "b"]
    assert admit(good, store=store) == view


# --------------------------------------------------------------------------- #
# TC-INT-083 —— AC-IB-18-06 / AC-IB-17-01：文档缺失 / 损坏**不静默回退**
# --------------------------------------------------------------------------- #


def test_TC_INT_083_missing_or_corrupt_document_never_silently_falls_back(tmp_path):
    """[TC-INT-083] US-IB-18 / AC-IB-18-06：定义文档缺失或不可解析时显式报错，绝不静默当作空文档。

    若静默回退为空文档，装配会「成功」但配置全部丢失 —— 这正是 fail-fast 要杜绝的形态。
    """
    missing = FileDefinitionDocumentStore(str(tmp_path / "absent.json"))
    for loader in (missing.load,):
        try:
            loader("p1")
            raise AssertionError("缺失文档竟未报错")
        except ConfigError as exc:
            assert "IB_DEFINITION_DOC_PATH" in str(exc) or "IB_DEFINITION_DOC_PATH" in getattr(exc, "key", "")

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{ 这不是 JSON", encoding="utf-8")
    try:
        FileDefinitionDocumentStore(str(corrupt)).load("p1")
        raise AssertionError("损坏文档竟未报错")
    except ConfigError:
        pass

    # 结构合法但非对象（JSON 数组）→ 亦按不可解析处理
    array_json = tmp_path / "array.json"
    array_json.write_text("[1, 2, 3]", encoding="utf-8")
    try:
        FileDefinitionDocumentStore(str(array_json)).load("p1")
        raise AssertionError("非对象文档竟未报错")
    except ConfigError:
        pass

    # 内存替身：未登记项目 / missing 标志 → 同样显式报错
    mem = InMemoryDefinitionDocumentStore(documents={"p_alpha": _doc("p_alpha")})
    assert mem.load("p_alpha").project_id == "p_alpha"
    try:
        mem.load("p_beta")
        raise AssertionError("未登记项目竟返回文档")
    except ConfigError:
        pass
    try:
        InMemoryDefinitionDocumentStore(missing=True).load("p_alpha")
        raise AssertionError("missing 标志未生效")
    except ConfigError:
        pass
    # 该用例不改变离线装配口径
    assert offline_raw()["offline_mode"] is True


# --------------------------------------------------------------------------- #
# TC-INT-084 —— AC-IB-17-01/04/05 + AC-IB-18-01/04：配置端点契约矩阵
# --------------------------------------------------------------------------- #


def test_TC_INT_084_definition_endpoint_contract_matrix(http_app):
    """[TC-INT-084] US-IB-17/18：`GET|PUT /api/config/definition` 状态码矩阵与单一真源往返。

    覆盖：200（读/写）/ 400（校验 + 拓扑 + 查询串令牌）/ 401（缺令牌）/ 403（项目不符）/
    405（方法不允许）/ 409（乐观并发）；并核验响应体**只登记键名、不含任何凭据值**。
    """
    deps, Client = http_app
    client = Client()

    # --- GET 200：唯一的真源投影 + 白名单 + 只登记键名 ---
    got = client.get(PATH, **AUTH)
    assert got.status_code == 200, got.content
    payload = json.loads(got.content)
    assert set(payload) == {"document", "derived", "editable_fields", "config_key_names"}
    assert payload["config_key_names"] == ["IB_DEFINITION_DOC_PATH", "IB_VISUAL_CONFIG_ENABLED"]
    assert "orchestration" not in payload["editable_fields"]
    assert payload["derived"]["expert_names"] and payload["derived"]["nodes"]
    # 凭据值不出现在响应体（此处令牌为环境变量占位符）；只出现**键名**
    assert TOKEN not in got.content.decode("utf-8")
    assert "IB_DEFINITION_DOC_PATH" in payload["config_key_names"]

    # --- 鉴权 / 方法 / 令牌纪律 ---
    assert client.get(PATH).status_code == 401
    assert client.get(PATH, HTTP_AUTHORIZATION="Bearer wrong-token").status_code == 401
    assert client.get(PATH, HTTP_X_IB_PROJECT="p_beta", **AUTH).status_code == 403
    assert client.get(PATH + "?token=x", **AUTH).status_code == 400
    assert client.post(PATH, **AUTH).status_code == 405
    assert client.delete(PATH, **AUTH).status_code == 405

    # --- PUT 200：白名单内编辑 → 写回定义文档 → GET 以文档为准（无漂移）---
    document = payload["document"]
    edited = json.loads(json.dumps(document))
    edited["route"]["tau"] = 0.72
    edited["experts"][1]["cn_label"] = "改过的标签"
    saved = client.put(
        PATH,
        data=json.dumps({"expected_content_hash": document["content_hash"], "document": edited}),
        content_type="application/json",
        **AUTH,
    )
    assert saved.status_code == 200, saved.content
    assert set(json.loads(saved.content)) == {"ok", "content_hash", "conflict", "errors"}
    assert json.loads(saved.content)["ok"] is True

    after = json.loads(client.get(PATH, **AUTH).content)
    assert after["document"]["route"]["tau"] == 0.72
    assert after["document"]["experts"][1]["cn_label"] == "改过的标签"
    assert after["document"]["content_hash"] == deps.definitions["p_alpha"].content_hash
    assert deps.definitions["p_alpha"].route.tau == 0.72

    # --- PUT 400：非法（默认专家不唯一）→ 逐条定位，指向 experts ---
    dup = json.loads(json.dumps(after["document"]))
    dup["experts"][1]["is_default"] = True
    rejected = client.put(PATH, data=json.dumps({"document": dup}), content_type="application/json", **AUTH)
    assert rejected.status_code == 400, rejected.content
    err = json.loads(rejected.content)["error"]
    assert err["code"] == "validation_error"
    assert any(i["code"] == "expert_default_count" for i in err["items"])
    for item in err["items"]:
        assert set(item) >= {"path", "code", "message"}
    # 非法配置不得静默生效：文档仍为上次合法值
    assert json.loads(client.get(PATH, **AUTH).content)["document"]["route"]["tau"] == 0.72

    # --- PUT 400：拓扑变更（界面不可写）→ field_not_editable ---
    topo = json.loads(json.dumps(after["document"]))
    topo["orchestration"]["nodes"].append("evil")
    blocked = client.put(PATH, data=json.dumps({"document": topo}), content_type="application/json", **AUTH)
    assert blocked.status_code == 400, blocked.content
    assert any(i["code"] == "field_not_editable" for i in json.loads(blocked.content)["error"]["items"])

    # --- PUT 400：**只**改普通边（nodes / conditional_edges 均不变）→ 仍为 field_not_editable ---
    # 断言的是**行为**而非清单：真正的拦截是 `_semantic_payload` 整块比较，
    # 「只比 nodes / conditional_edges」的实现会在此漏网。
    # 加的那条边 `expert -> aggregate` **通过 validate**（端点真实、非自环、不重复）——
    # 于是这条请求只能被「非可编辑字段」拦下，排除了「其实是校验失败」的误判。
    seed_edges = [
        {"from_node": "START", "to_node": "route"},
        {"from_node": "expert", "to_node": "gate"},
        {"from_node": "gate", "to_node": "aggregate"},
        {"from_node": "general", "to_node": "aggregate"},
        {"from_node": "aggregate", "to_node": "END"},
    ]
    edge_topo = json.loads(json.dumps(after["document"]))
    assert edge_topo["orchestration"]["edges"] == seed_edges, (
        "文档契约要求 `edges` 恒存在且为内置默认主干（缺则配置页 gate/aggregate 渲染成孤立方块）"
    )
    # 派生视图摘要同样要出 `edges` —— 配置页画图读的是 `derived`，不是 `document`
    assert after["derived"]["edges"] == seed_edges, "派生视图摘要漏掉 edges，配置页拿不到主干"
    edge_topo["orchestration"]["edges"] = seed_edges + [{"from_node": "expert", "to_node": "aggregate"}]
    edge_blocked = client.put(
        PATH, data=json.dumps({"document": edge_topo}), content_type="application/json", **AUTH
    )
    assert edge_blocked.status_code == 400, edge_blocked.content
    assert any(
        i["code"] == "field_not_editable" for i in json.loads(edge_blocked.content)["error"]["items"]
    )
    # 未落盘：文档仍为上次合法值
    assert json.loads(client.get(PATH, **AUTH).content)["document"]["orchestration"]["edges"] == seed_edges

    # --- PUT 409：乐观并发冲突（陈旧基线），不静默覆盖 ---
    stale = json.loads(json.dumps(after["document"]))
    stale["route"]["tau"] = 0.99
    conflict = client.put(
        PATH,
        data=json.dumps({"expected_content_hash": "sha256:deadbeef", "document": stale}),
        content_type="application/json",
        **AUTH,
    )
    assert conflict.status_code == 409, conflict.content
    body = json.loads(conflict.content)
    assert body["error"]["code"] == "conflict" and body["error"]["receipt"]["conflict"] is True
    assert json.loads(client.get(PATH, **AUTH).content)["document"]["route"]["tau"] == 0.72


# --------------------------------------------------------------------------- #
# TC-INT-085 —— AC-IB-18-01：装配期「装载 → 准入 → 派生 → 注入」序列
# --------------------------------------------------------------------------- #


def test_TC_INT_085_assembly_loads_admits_derives_and_injects(deps):
    """[TC-INT-085] US-IB-18 / AC-IB-18-01：装配按序装载并准入定义文档，派生结果注入运行期注册表；
    编排图**编译一次常驻**（同一项目复用同一编排器对象）。
    """
    import ib.experts as experts

    assert set(deps.definitions) == {"p_alpha", "p_beta"}
    assert deps.definitions["p_alpha"] is not deps.definitions["p_beta"], "两项目共享了同一文档对象"
    assert isinstance(deps.definition_store, InMemoryDefinitionDocumentStore)

    view = deps.derived_views["p_alpha"]
    assert tuple(e.name for e in view.experts) == experts.names(), "派生注册表 != 定义文档专家集"
    assert view.capability_digest and "search_knowledge" in view.capability_digest
    assert experts.default_expert() == deps.definitions["p_alpha"].route.default_expert

    # 图配置取自文档（max_expert_steps=8 默认）
    from ibweb.composition import _graph_config

    assert _graph_config(deps.cfg, deps.definitions["p_alpha"].route).max_expert_steps == 8

    # 编排图编译一次常驻：同项目两次取用为**同一对象**
    assert deps.orchestrator_for("p_alpha") is deps.orchestrator_for("p_alpha")
    assert deps.orchestrator_for("p_alpha") is not deps.orchestrator_for("p_beta")


# --------------------------------------------------------------------------- #
# TC-INT-086 —— AC-IB-17-04/05/06：视图侧纪律（IFC-IB-296；**源码级**）
# --------------------------------------------------------------------------- #


def test_TC_INT_086_view_side_discipline_is_source_level_only():
    """[TC-INT-086] US-IB-17 / AC-IB-17-04/05/06：配置页的**源码级**纪律断言。

    断言面：本地打包无 CDN、视图侧零持久化（localStorage / IndexedDB）、拓扑只读
    （只读渲染标志 + 无增删节点/边的入口）、只展示键名、无 `v-html`（XSS 通道）。

    **诚实边界（NOT_TESTABLE）**：真实**运行期渲染**（Vue 挂载 / 画布交互）**无法离线验证** ——
    本用例**只做源码级 + 分发纪律**断言，**不**声称页面已能渲染（详见报告 §12 NOT_TESTABLE 清单）。
    R10 起前端依赖已可本地 `npm ci` 安装，但「已装 / 未装」**与本用例无关**：本用例守护的是
    「**前端依赖不随仓库分发**」这一与磁盘状态**无关**的不变量（见末尾断言）。
    """
    src_root = _FRONTEND / "src"
    assert src_root.is_dir(), "前端源码目录不存在"

    cfg_raw = (src_root / "views" / "ConfigPage.vue").read_text(encoding="utf-8")
    cfg = _strip_comments(cfg_raw)
    package_json = (_FRONTEND / "package.json").read_text(encoding="utf-8")

    # 本地打包（依赖声明 + 源码 import）；运行期禁 CDN
    assert "@vue-flow/core" in package_json
    assert "@vue-flow/core" in cfg

    sources = sorted(src_root.rglob("*.vue")) + sorted(src_root.rglob("*.ts"))
    index_html = _FRONTEND / "index.html"
    if index_html.is_file():
        sources.append(index_html)
    assert sources, "未找到任何前端源文件"
    for path in sources:
        text = _strip_comments(path.read_text(encoding="utf-8")).lower()
        for bad in ("cdn.", "unpkg.com", "jsdelivr", "cdnjs", "https://unpkg"):
            assert bad not in text, f"{path.name} 含 CDN 引用：{bad}（AC-IB-17-06）"

    # 视图侧零持久化：除 client.ts / main.ts 的**会话令牌**（IC-IB-01）外不得用持久化存储
    for path in sources:
        if path.name in ("client.ts", "main.ts"):
            continue
        text = _strip_comments(path.read_text(encoding="utf-8"))
        assert "localStorage" not in text, f"{path.name} 使用 localStorage（视图侧零持久化）"
        assert "indexedDB" not in text and "IndexedDB" not in text, f"{path.name} 使用 IndexedDB"

    # 拓扑只读：只读渲染标志存在，且**无**增删节点 / 增删边的入口
    assert "nodes-draggable" in cfg and "connectable" in cfg, "编排图未设为只读渲染"
    import re

    assert not re.search(r"\b(addNode|removeNode|deleteNode|addEdge|removeEdge|deleteEdge)\b", cfg), (
        "配置页出现图拓扑编辑入口（REQ-FUNC-IB-26 ②）"
    )
    assert "v-html" not in cfg, "配置页使用了 v-html（XSS 通道）"

    # 只展示键名（凭据值一律不回显）
    assert "config_key_names" in cfg
    # 未提交草稿须显式标注「可丢弃」
    assert "未提交" in cfg_raw

    # 分发纪律（R10 修复）：前端依赖**不随仓库分发** —— `src/frontend/node_modules/**`
    # 不得被 git 跟踪。原 R7 断言「磁盘上不存在该目录」把「本地未装依赖」误当不变量，
    # 与 R10 起必需的 `npm ci` 冲突（已装即必失败）；此处改判**入库状态**，与磁盘无关：
    # 未装 / 已装但被 gitignore → 通过；被 `git add -f` 强加入库 → 失败（守护同一不变量，不弱化）。
    tracked = _frontend_deps_tracked_by_git()
    assert tracked == [], (
        "前端依赖不应随仓库分发：以下 src/frontend/node_modules 条目已被 git 跟踪 → "
        f"{tracked[:5]}{' …（截断）' if len(tracked) > 5 else ''}"
    )


# --------------------------------------------------------------------------- #
# TC-INT-087 —— AC-IB-18-02 / AC-IB-18-06：R8 两项新增校验经装配闸门与 PUT 端点 fail-fast
# --------------------------------------------------------------------------- #


def test_TC_INT_087_r8_uniqueness_fails_fast_through_admit_and_endpoint(http_app):
    """[TC-INT-087] US-IB-18 / AC-IB-18-02 + AC-IB-18-06：R8 纯追加的两项校验
    （跨专家关键词撞车 / `cn_label` 重复）不仅在纯函数层成立，且**经装配闸门与配置端点
    同样 fail-fast**、逐条回传错误码与定位，非法配置不静默生效。

    单元边界分支见 `tests/unit/test_definition_uniqueness_extra_r8.py`（TC-UNIT-065/066）；
    本用例只覆盖**跨模块**的接缝（`ib.config` ↔ `ibweb.composition.admit` ↔ 端点）。
    """
    from ib.config import validate as _validate
    from ibweb.composition import admit

    deps, Client = http_app
    store = deps.definition_store

    # --- 装配闸门：关键词撞车 + 标签重复同时命中 → 聚合拒绝（含两项新错误码）---
    illegal = build_definition_document(
        project_id="p_alpha",
        experts=(
            ExpertSpecInput("a", "同标签", ("撞车词",), (), False, "pa", False, True),
            ExpertSpecInput("b", "同标签", ("撞车词",), (), False, "pb", False, False),
        ),
        route=RouteSpecInput(0.65, 0.05, 8, "a"),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
        ),
        tool_grants=(),
    )
    expected = _validate(illegal, known_tools=frozenset({"search_knowledge"}))
    assert expected.ok is False
    assert {"expert_keyword_collision", "expert_cn_label_duplicate"} <= {i.code for i in expected.errors}
    try:
        admit(illegal, store=store)
        raise AssertionError("非法定义竟通过装配期闸门")
    except ConfigError as exc:
        items = getattr(exc, "validation_items", None)
        assert items is not None and len(items) == len(expected.errors)
        assert {"expert_keyword_collision", "expert_cn_label_duplicate"} <= {i.code for i in items}
        for i in items:
            assert i.path and i.code and i.message

    # --- 配置端点：白名单内编辑（cn_label / keywords）即可触发两项新校验，400 逐条回执 ---
    client = Client()
    doc = json.loads(client.get(PATH, **AUTH).content)["document"]

    dup_label = json.loads(json.dumps(doc))
    dup_label["experts"][1]["cn_label"] = dup_label["experts"][0]["cn_label"]  # 与首个专家同名标签
    rejected_label = client.put(
        PATH,
        data=json.dumps({"expected_content_hash": doc["content_hash"], "document": dup_label}),
        content_type="application/json",
        **AUTH,
    )
    assert rejected_label.status_code == 400, rejected_label.content
    label_items = json.loads(rejected_label.content)["error"]["items"]
    assert any(i["code"] == "expert_cn_label_duplicate" for i in label_items), label_items
    for i in label_items:
        assert i["path"] and i["code"] and i["message"]

    dup_kw = json.loads(json.dumps(doc))
    dup_kw["experts"][1]["keywords"] = list(dup_kw["experts"][0]["keywords"])  # 关键词集合整体撞车
    rejected_kw = client.put(
        PATH,
        data=json.dumps({"expected_content_hash": doc["content_hash"], "document": dup_kw}),
        content_type="application/json",
        **AUTH,
    )
    assert rejected_kw.status_code == 400, rejected_kw.content
    kw_items = json.loads(rejected_kw.content)["error"]["items"]
    assert any(i["code"] == "expert_keyword_collision" for i in kw_items), kw_items

    # 非法配置不得静默生效：文档仍为上一次合法值（content_hash 未变）
    still = json.loads(client.get(PATH, **AUTH).content)["document"]
    assert still["content_hash"] == doc["content_hash"]
