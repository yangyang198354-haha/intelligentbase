"""[REV-16-2] 提示词端点族契约 + 装配序列（IFC-IB-352 / 353）。

覆盖 US-IB-29/30/31（提示词分层编辑、工具授权与参数保存）。走**真实 HTTP 契约** +
离线装配（`InMemoryExpertPromptStore`），无网络、无真实凭据。

分层依据（test_plan §2）：跨 `ibweb.views` ↔ `ibweb.composition` ↔ `ib.config.prompts`
↔ Django 中间件（鉴权 / `?token=` 纪律），属**集成级**。
"""

from __future__ import annotations

import json
import os

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
LIST = "/api/config/prompts"


def _layer_path(expert: str, layer: str) -> str:
    return f"{LIST}/{expert}/{layer}"


def _put_layer(client, expert: str, layer: str, body: dict):
    return client.put(
        _layer_path(expert, layer),
        data=json.dumps(body),
        content_type="application/json",
        **AUTH,
    )


# --------------------------------------------------------------------------- #
# 装配序列（IFC-IB-353）：每项目一份提示词存储 + 跨域合并派生注入
# --------------------------------------------------------------------------- #


def test_TC_INT_R16_assembly_installs_prompt_stores_and_bundles(deps):
    assert set(deps.prompt_stores) == {"p_alpha", "p_beta"}
    for view in deps.derived_views.values():
        # 无提示词文件 → 代码内置安全网兜底 → 每位专家都有生效提示词（恒非空）
        # REV-17（ADR-36）：第三值由 `definition_doc_fallback` 改为 `builtin_fallback`。
        assert view.prompt_bundles
        assert all(b.effective_prompt.strip() for b in view.prompt_bundles)
        assert all(b.resolved_from == "builtin_fallback" for b in view.prompt_bundles)

    from ib.experts import prompt_bundles

    installed = prompt_bundles()
    assert set(installed) == {"freeark-expert", "inspection-expert", "sanheng-knowledge"}


# --------------------------------------------------------------------------- #
# GET /api/config/prompts（IFC-IB-352）：列表只出元数据 + 哈希，不出正文
# --------------------------------------------------------------------------- #


def test_TC_INT_R16_prompt_list_contract(http_app):
    deps, Client = http_app
    client = Client()
    got = client.get(LIST, **AUTH)
    assert got.status_code == 200, got.content
    payload = json.loads(got.content)
    assert set(payload) == {
        "experts",
        "tool_param_specs",
        "available_tools",
        "layout",
        "config_key_names",
    }
    # 既有工具名单（勾选只作用于既有工具集合；不新增工具本体）
    assert payload["available_tools"] == ["search_knowledge"]
    names = {e["name"] for e in payload["experts"]}
    assert names == {"freeark-expert", "inspection-expert", "sanheng-knowledge"}
    for e in payload["experts"]:
        assert set(e["layers"]) == {"main", "fallback"}
        assert set(e["layers"]["main"]) == {"exists", "content_hash"}
    # 尚未保存任何提示词 → 全不存在
    assert all(not e["layers"]["main"]["exists"] for e in payload["experts"])
    # 参数规格由既有工具派生（不含新增工具本体）
    assert {s["name"] for s in payload["tool_param_specs"]} == {"search_knowledge.query"}
    # **只登记键名，不含任何值**
    assert payload["config_key_names"] == ["IB_EXPERT_PROMPT_DIR", "IB_EXPERT_PROMPT_ENABLED"]
    # **只读回执不含正文**（凭据与正文均不外泄）；令牌值不出现在响应体
    assert TOKEN not in got.content.decode("utf-8")


# --------------------------------------------------------------------------- #
# GET/PUT 单层（IFC-IB-352）：200 / 400 / 404 / 409 / 401
# --------------------------------------------------------------------------- #


def test_TC_INT_R16_prompt_layer_get_save_conflict_and_validation(http_app):
    deps, Client = http_app
    client = Client()

    # 未保存 → 404（不区分「不存在」与「不属于你」）
    assert client.get(_layer_path("freeark-expert", "main"), **AUTH).status_code == 404
    # 非法层名 → 404
    assert client.get(_layer_path("freeark-expert", "other"), **AUTH).status_code == 404

    # PUT main → 200 保存成功
    ok = _put_layer(client, "freeark-expert", "main", {"content": "你是系统管家。"})
    assert ok.status_code == 200, ok.content
    save = json.loads(ok.content)
    assert save["saved"] is True and save["content_hash"].startswith("sha256:")

    # GET 单层 → 正文 + 哈希
    got = client.get(_layer_path("freeark-expert", "main"), **AUTH)
    assert got.status_code == 200, got.content
    body = json.loads(got.content)
    assert body["content"] == "你是系统管家。"
    assert body["content_hash"] == save["content_hash"]

    # 列表：main 存在且哈希一致
    listed = json.loads(client.get(LIST, **AUTH).content)
    fe = next(e for e in listed["experts"] if e["name"] == "freeark-expert")
    assert fe["layers"]["main"]["exists"] is True
    assert fe["layers"]["main"]["content_hash"] == save["content_hash"]

    # 乐观并发冲突：错误的 expected_hash → 409，且不覆盖
    conflict = _put_layer(
        client,
        "freeark-expert",
        "main",
        {"content": "改", "expected_hash": "sha256:deadbeef"},
    )
    assert conflict.status_code == 409, conflict.content
    assert json.loads(conflict.content)["error"]["code"] == "conflict"
    assert json.loads(client.get(_layer_path("freeark-expert", "main"), **AUTH).content)["content"] == "你是系统管家。"

    # 兜底层不得为空 → 400（fail-safe）
    empty = _put_layer(client, "freeark-expert", "fallback", {"content": "   "})
    assert empty.status_code == 400, empty.content
    items = json.loads(empty.content)["error"]["items"]
    assert any(i["code"] == "prompt_fallback_empty" for i in items)

    # 未知专家 → 404
    assert _put_layer(client, "ghost", "main", {"content": "x"}).status_code == 404

    # 缺令牌 → 401/403（中间件先行）
    assert client.get(LIST).status_code in (401, 403)
    assert client.put(_layer_path("freeark-expert", "main"), data="{}", content_type="application/json").status_code in (401, 403)


def test_TC_INT_R16_prompt_endpoint_rejects_query_token(http_app):
    """模块级鉴权纪律：**不接受** `?token=`（中间件先于路由拒绝）。"""
    deps, Client = http_app
    client = Client()
    got = client.get(f"{LIST}?token={TOKEN}")
    assert got.status_code in (400, 401, 403), got.status_code
    assert got.status_code != 200


def test_TC_INT_R16_prompt_save_does_not_rebuild_graph(http_app):
    """ADR-32 / C-IB-40：保存仅原子落盘，**不触发运行期重建**（图对象保持同一实例）。"""
    deps, Client = http_app
    client = Client()
    before = deps.orchestrator_for("p_alpha")
    ok = _put_layer(client, "freeark-expert", "fallback", {"content": "兜底"})
    assert ok.status_code == 200, ok.content
    after = deps.orchestrator_for("p_alpha")
    assert before is after  # 未重建编排图
