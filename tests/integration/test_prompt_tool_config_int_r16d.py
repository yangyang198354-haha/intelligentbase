"""[REV-16-2 / GROUP_D] 提示词端点开关 · 兜底可见性 · 唯一登记点 · 两域闸门 · 保存回读保真。

本文件为**测试工程师（GROUP_D）独立补充**的集成级用例，走**真实 HTTP 契约** +
离线装配（`InMemoryExpertPromptStore`），无网络、无真实凭据。逐条溯源至
AC-IB-30-01/02/04/06、31-02/03/04、32-*。

分层依据（test_plan §2）：跨 `ibweb.views` ↔ `ibweb.serializers` ↔
`ibweb.composition` ↔ `ib.config.*` ↔ Django 中间件 → **集成级**。

**本文件含两条「如实失败」的验收用例**（记 DEFECT-R16-01 / R16-02），用于把
GROUP_C 实现缺陷固化为可复现证据；缺陷修复属 software_developer 职责，本代理不修改 `src/`。
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

import pytest

import ib.core as core

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
LIST = "/api/config/prompts"
DEF = "/api/config/definition"


def _layer(expert: str, layer: str) -> str:
    return f"{LIST}/{expert}/{layer}"


def _put_layer(client, expert: str, layer: str, body: dict):
    return client.put(
        _layer(expert, layer), data=json.dumps(body), content_type="application/json", **AUTH
    )


def _get_def(client) -> dict:
    resp = client.get(DEF, **AUTH)
    assert resp.status_code == 200, resp.content
    return json.loads(resp.content)["document"]


def _put_def(client, doc: dict, expected: str | None = None):
    body = {"document": doc}
    if expected is not None:
        body["expected_content_hash"] = expected
    return client.put(
        DEF, data=json.dumps(body), content_type="application/json", **AUTH
    )


# --------------------------------------------------------------------------- #
# IFC-IB-352：可视化配置总开关关闭 → 提示词端点族整体 404（只看行为，键值不外泄）
# 溯源：AC-IB-33-02（未启用时明确提示，不静默成功）
# --------------------------------------------------------------------------- #


def test_TC_INT_134_visual_switch_off_returns_404(http_app, monkeypatch):
    deps, Client = http_app
    monkeypatch.setenv("IB_VISUAL_CONFIG_ENABLED", "false")
    client = Client()

    for resp in (
        client.get(LIST, **AUTH),
        client.get(_layer("freeark-expert", "main"), **AUTH),
        _put_layer(client, "freeark-expert", "main", {"content": "x"}),
    ):
        assert resp.status_code == 404, resp.content
        assert json.loads(resp.content)["error"]["code"] == "not_found"


# --------------------------------------------------------------------------- #
# ADR-29 / AC-IB-30-06：主缺失 → 兜底可见且生效（界面可观测 resolvedFrom=fallback）
# 溯源：AC-IB-30-01、AC-IB-30-02、AC-IB-30-06
# --------------------------------------------------------------------------- #


def test_TC_INT_135_fallback_visible_when_main_missing(http_app):
    deps, Client = http_app
    client = Client()

    # 仅保存兜底层（main.md 依法可缺）
    ok = _put_layer(client, "freeark-expert", "fallback", {"content": "兜底提示词：先问清需求"})
    assert ok.status_code == 200, ok.content
    assert json.loads(ok.content)["saved"] is True

    listed = json.loads(client.get(LIST, **AUTH).content)
    fe = next(e for e in listed["experts"] if e["name"] == "freeark-expert")
    assert fe["layers"]["main"]["exists"] is False  # 主缺失
    assert fe["layers"]["fallback"]["exists"] is True  # 兜底在

    # 单层读：主 404，兜底 200 + 正文（重新读取与编辑内容一致，AC-IB-30-02）
    assert client.get(_layer("freeark-expert", "main"), **AUTH).status_code == 404
    got = client.get(_layer("freeark-expert", "fallback"), **AUTH)
    assert got.status_code == 200, got.content
    assert json.loads(got.content)["content"] == "兜底提示词：先问清需求"

    # 装配派生：主缺失 → 生效提示词取自兜底文件，且恒非空
    from ib.config import load_prompt_directory

    deps.prompt_stores  # noqa: B018 - 端点族已装配（结构断言）
    deps_doc = deps.definitions["p_alpha"]
    bundles = {b.expert_name: b for b in deps.definition_store.derive(deps_doc).prompt_bundles}
    # 内存 store 的兜底来自文档；此处主要验证「生效提示词恒非空」这一 ADR-29 事实
    assert all(b.effective_prompt.strip() for b in bundles.values())


# --------------------------------------------------------------------------- #
# ADR-30 / REQ-FUNC-IB-03：工具与参数均**由唯一登记点派生**（界面 / 校验 / 绑定同源）
# 溯源：AC-IB-31-01、AC-IB-31-04（既有工具集 + 既有参数，不新增工具本体）
# --------------------------------------------------------------------------- #


def test_TC_INT_136_single_registration_point_tools_and_params(http_app):
    from ibweb.composition import known_tool_names, known_tool_param_specs

    assert known_tool_names() == ("search_knowledge",)
    specs = known_tool_param_specs()
    assert [s.name for s in specs] == ["search_knowledge.query"]

    deps, Client = http_app
    payload = json.loads(Client().get(LIST, **AUTH).content)
    # 端点回执与装配期校验同源
    assert payload["available_tools"] == list(known_tool_names())
    assert {s["name"] for s in payload["tool_param_specs"]} == {s.name for s in specs}


# --------------------------------------------------------------------------- #
# ADR-16 / IFC-IB-353：两域聚合闸门（真实 deps）—— 非法参数拒绝装配、合法通过并派生
# 溯源：AC-IB-30-04（校验拒绝）、AC-IB-31-03（既有配置不变 / 拒绝）
# --------------------------------------------------------------------------- #


def test_TC_INT_137_admit_two_domains_rejects_and_passes(http_app):
    from ibweb.composition import admit_two_domains

    deps, Client = http_app
    doc = deps.definitions["p_alpha"]
    specs = deps.tool_param_specs()

    bad = replace(
        doc,
        tool_grants=(
            core.ToolGrantSpec(
                doc.experts[0].name,
                ("search_knowledge",),
                (core.ToolParamValue("search_knowledge.nope", "1"),),
            ),
        ),
    )
    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(bad, store=deps.definition_store, prompt_refs=(), tool_specs=specs)
    assert "tool_param_unknown" in {i.code for i in ei.value.validation_items}

    # 合法文档 → 通过并产出跨域合并派生视图（生效提示词恒非空）
    view = admit_two_domains(doc, store=deps.definition_store, prompt_refs=(), tool_specs=specs)
    assert view.prompt_bundles and all(b.effective_prompt.strip() for b in view.prompt_bundles)


# --------------------------------------------------------------------------- #
# AC-IB-31-03：保存期拒绝「引用不存在的工具」，且**既有在用配置保持不变**
# --------------------------------------------------------------------------- #


def test_TC_INT_138_definition_save_rejects_unknown_tool_and_preserves_config(http_app):
    deps, Client = http_app
    client = Client()
    doc = _get_def(client)
    base = doc["content_hash"]

    bad = json.loads(json.dumps(doc))
    bad["tool_grants"][0]["tool_names"] = ["nope-tool"]
    resp = _put_def(client, bad, expected=base)
    assert resp.status_code == 400, resp.content
    items = json.loads(resp.content)["error"]["items"]
    assert any(i["code"] == "tool_grant_tool_unknown" for i in items)
    # 既有在用配置未被半写入破坏（fail-safe）
    assert deps.definition_store.load("p_alpha").content_hash == base


# --------------------------------------------------------------------------- #
# [DEFECT-R16-02] 保存期未对工具参数做完整校验 → 非法参数被接受并落盘
# 溯源：AC-IB-30-04「保存内容不合法 → 被完备性校验拒绝，既有在用配置保持不变」
# 期望：400 + 既有配置不变；实际：200 + 配置被改写（下次装配将拒绝 → 违背 fail-safe）
# --------------------------------------------------------------------------- #


def test_TC_INT_139_definition_save_rejects_invalid_tool_param_DEFECT_R16_02(http_app):
    deps, Client = http_app
    client = Client()
    doc = _get_def(client)
    base = doc["content_hash"]

    bad = json.loads(json.dumps(doc))
    # search_knowledge.nope 未被任何 ToolParamSpec 声明 —— 属「保存内容不合法」
    bad["tool_grants"][0]["param_values"] = [{"name": "search_knowledge.nope", "value": "1"}]
    resp = _put_def(client, bad, expected=base)

    after = deps.definition_store.load("p_alpha").content_hash
    assert resp.status_code == 400, (
        f"DEFECT-R16-02：定义文档保存期未校验工具参数 —— 非法写已被接受 "
        f"(status={resp.status_code}, store_changed={after != base})；"
        "param 校验仅在装配期（admit_two_domains）生效，可致下次重启装配失败"
    )
    assert after == base, "DEFECT-R16-02：非法保存改写了既有在用配置（违背 fail-safe）"


# --------------------------------------------------------------------------- #
# [DEFECT-R16-01] 定义文档 GET 未序列化 tool_grants[].param_values → 往返静默丢失
# 溯源：AC-IB-31-02 / AC-IB-31-04（工具授权与参数「重新读取定义」须与编辑内容一致）
# 期望：GET 回执含 param_values，且 GET→PUT 往返不丢参；实际：GET 缺字段 → 界面无法回显
# --------------------------------------------------------------------------- #


def test_TC_INT_140_definition_roundtrip_preserves_param_values_DEFECT_R16_01(http_app):
    from ibweb.serializers import DefinitionDocumentSerializer

    deps, Client = http_app
    client = Client()

    # 直接对序列化器取证（不依赖 HTTP 往返也能复现）
    serialized = DefinitionDocumentSerializer().to_representation(deps.definitions["p_alpha"])
    grant_keys = set(serialized["tool_grants"][0])
    assert "param_values" in grant_keys, (
        f"DEFECT-R16-01：_ToolGrantSpecSerializer 仅输出 {sorted(grant_keys)}，"
        "遗漏 param_values → GET /api/config/definition 无法回显工具参数"
    )

    doc = _get_def(client)
    doc["tool_grants"][0]["param_values"] = [
        {"name": "search_knowledge.query", "value": "占位查询词"}
    ]
    put = _put_def(client, doc, expected=doc["content_hash"])
    assert put.status_code == 200, put.content

    stored = deps.definition_store.load("p_alpha")
    assert stored.tool_grants[0].param_values == (
        core.ToolParamValue("search_knowledge.query", "占位查询词"),
    ), "保存写入未生效"

    # 重新读取定义（AC-IB-31-02）：GET→PUT 往返后参数取值须一致
    reloaded = _get_def(client)
    grant = next(g for g in reloaded["tool_grants"] if g["expert_name"] == "freeark-expert")
    assert grant.get("param_values") == [
        {"name": "search_knowledge.query", "value": "占位查询词"}
    ], (
        "DEFECT-R16-01：GET 未回读 param_values —— 一次「GET 草稿 → PUT 保存」往返即"
        "静默清空已配置的工具参数"
    )
