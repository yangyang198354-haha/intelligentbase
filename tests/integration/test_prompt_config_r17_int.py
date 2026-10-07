"""[REV-17 / ADR-36] 保存期 ↔ 装配期**同一校验入口** + 通用内置安全网破死锁。

覆盖 REV-17 的两条**结构性**保证（此前只测到装配期，保存期没有覆盖面）：

  1. **同序同条**：同一份非法文档，走 `PUT /api/config/definition`（保存期）与走
     装配期 `admit_two_domains`，回执的校验项**逐条同序、同码、同路径**。REV-17 之前
     提示词域只在装配期查，于是「页面上存得下、重启装配才炸」是可能的（ADR-33 的漏洞）。
  2. **死锁已破**：`PUT definition` 新增一个**不在 `_DEFAULT_SPECS`** 的专家 → 保存成功、
     装配成功、`resolved_from == "builtin_fallback"`。旧口径下这条路是死的
     （`PUT definition` 要求非空兜底；`PUT prompts/<新专家>/fallback` 又因「专家未登记」404）。

另附只读回显契约：`GET /api/config/prompts` 的每位专家带 `builtin_fallback`（只读展示用，
**不**提供写入口 —— 写入口只有 `main` / `fallback` 两层文件）。

离线纪律：内存定义文档 + 内存提示词存储；无网络；无任何真实凭据。
"""

from __future__ import annotations

import json
import os

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
DEF = "/api/config/definition"
LIST = "/api/config/prompts"


def _put_definition(client, document: dict, expected_hash: str):
    return client.put(
        DEF,
        data=json.dumps({"document": document, "expected_content_hash": expected_hash}),
        content_type="application/json",
        **AUTH,
    )


def _seed_orphan_prompt(deps, project_id: str = "p_alpha"):
    """塞一个**孤儿提示词文件**（目录有、定义文档未登记）以制造提示词域错误。"""
    from ib.config import InMemoryExpertPromptStore
    from ibweb.composition import build_application

    deps.prompt_stores[project_id] = InMemoryExpertPromptStore(
        project_id, documents={"ghost-expert": {"main": "孤儿提示词（未登记专家）"}}
    )
    build_application(deps)  # 重绑全局 deps，让端点的 `_prompt_refs_for` 看到新 store


def _items_of_http(payload: dict) -> list[tuple[str, str]]:
    return [(i["path"], i["code"]) for i in payload["error"]["items"]]


# --------------------------------------------------------------------------- #
# 1 · 保存期 ↔ 装配期：同一入口、同序同条（ADR-33 / IFC-IB-364）
# --------------------------------------------------------------------------- #


def test_TC_INT_R17_save_and_assembly_report_identical_items_in_order(http_app):
    """同一份非法文档 → PUT 回执 ≡ 装配期 `admit_two_domains` 的校验项（顺序也一致）。"""
    from ib.config import document_from_json
    from ib.core import ConfigError
    from ib.experts import BUILTIN_FALLBACKS

    from ibweb.composition import admit_two_domains, known_tool_param_specs

    deps, Client = http_app
    _seed_orphan_prompt(deps)
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]

    bad = json.loads(json.dumps(doc))
    bad["experts"][0]["cn_label"] = "   "  # 定义域（应排在最先）
    bad["tool_grants"][0]["tool_names"] = ["ghost-tool"]  # 工具域（次之）
    # 提示词域错误来自 `_seed_orphan_prompt`（应排在最后）

    resp = _put_definition(client, bad, doc["content_hash"])
    assert resp.status_code == 400, resp.content
    http_items = _items_of_http(json.loads(resp.content))

    codes = [code for _path, code in http_items]
    assert "expert_text_missing" in codes
    assert "tool_grant_tool_unknown" in codes
    assert "prompt_orphan_file" in codes, "保存期必须**一并**校验提示词域（REV-17 新收口）"
    # 域间顺序固定：定义域 → 工具域 → 提示词域
    assert codes.index("expert_text_missing") < codes.index("tool_grant_tool_unknown")
    assert codes.index("tool_grant_tool_unknown") < codes.index("prompt_orphan_file")

    # 装配期：同一份文档、同一份 refs、同一份工具规格 → 必须逐条同序同码同路径
    submitted = document_from_json(
        "p_alpha", json.dumps(bad), builtin_fallbacks=BUILTIN_FALLBACKS
    )
    refs = deps.prompt_stores["p_alpha"].list_refs()
    try:
        admit_two_domains(
            submitted,
            store=deps.definition_store,
            prompt_refs=refs,
            tool_specs=known_tool_param_specs(),
        )
    except ConfigError as exc:
        assembly_items = [
            (item.path, item.code) for item in getattr(exc, "validation_items", ())
        ]
    else:  # pragma: no cover - 走到这里说明闸门**放行**了非法文档，是安全缺陷
        raise AssertionError("装配期闸门放行了非法文档（准入闸门失效）")

    assert assembly_items == http_items, "保存期与装配期必须同序同条（ADR-33 单一校验入口）"


def test_TC_INT_R17_illegal_doc_leaves_stored_config_untouched(http_app):
    """fail-safe：保存期校验不通过 → 既有在用配置**逐位不变**（不半写入）。"""
    deps, Client = http_app
    _seed_orphan_prompt(deps)
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]
    base = doc["content_hash"]

    bad = json.loads(json.dumps(doc))
    bad["experts"].append(
        {
            "name": "孤儿占用者",
            "cn_label": "",
            "keywords": [],
            "exemplars": [],
            "is_data_expert": False,
            "is_delegating": False,
            "is_default": False,
        }
    )
    assert _put_definition(client, bad, base).status_code == 400
    assert deps.definition_store.load("p_alpha").content_hash == base


# --------------------------------------------------------------------------- #
# 2 · 通用内置安全网：破「界面新增专家」死锁
# --------------------------------------------------------------------------- #


def test_TC_INT_R17_new_expert_without_any_prompt_file_can_be_saved_and_admitted(http_app):
    """新增一个**不在 `_DEFAULT_SPECS`** 的专家：保存成功 + 装配成功 + 回落通用内置兜底。"""
    from ib.experts import BUILTIN_FALLBACK_DEFAULT, builtin_fallback_for
    from ibweb.composition import admit_two_domains, known_tool_param_specs

    deps, Client = http_app
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]
    base = doc["content_hash"]

    new_name = "brand-new-expert"
    assert new_name not in {e["name"] for e in doc["experts"]}
    assert builtin_fallback_for(new_name) == BUILTIN_FALLBACK_DEFAULT

    draft = json.loads(json.dumps(doc))
    draft["experts"].append(
        {
            "name": new_name,
            "cn_label": "界面新增专家",
            "keywords": ["新词"],
            "exemplars": [],
            "is_data_expert": False,
            "is_delegating": False,
            "is_default": False,
        }
    )
    # ① 保存：**不**需要先写任何提示词文件（旧口径下这一步 400「缺兜底提示词」）
    saved = _put_definition(client, draft, base)
    assert saved.status_code == 200, saved.content

    # ② 装配：提示词目录里该专家**一层文件都没有**，仍必须准予装配
    stored = deps.definition_store.load("p_alpha")
    view = admit_two_domains(
        stored,
        store=deps.definition_store,
        prompt_refs=deps.prompt_stores["p_alpha"].list_refs(),
        tool_specs=known_tool_param_specs(),
    )
    bundle = next(b for b in view.prompt_bundles if b.expert_name == new_name)
    assert bundle.resolved_from == "builtin_fallback"
    assert bundle.effective_prompt == BUILTIN_FALLBACK_DEFAULT
    assert bundle.effective_prompt.strip(), "生效提示词恒非空（ADR-29 由结构保证）"

    # ③ 反证：写入口仍只有两层文件 —— 未登记进定义文档的专家照样写不进（反越域）
    assert client.put(
        f"{LIST}/not-in-document/fallback",
        data=json.dumps({"content": "x"}),
        content_type="application/json",
        **AUTH,
    ).status_code == 404


def test_TC_INT_R17_new_expert_without_prompt_passes_save_but_orphan_still_fails(http_app):
    """反证「通用兜底」**没有**顺手放开越域：孤儿文件仍被拒（不是把校验整体关掉）。"""
    deps, Client = http_app
    _seed_orphan_prompt(deps)
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]

    resp = _put_definition(client, doc, doc["content_hash"])
    assert resp.status_code == 400, resp.content
    assert any(code == "prompt_orphan_file" for _p, code in _items_of_http(json.loads(resp.content)))


# --------------------------------------------------------------------------- #
# 3 · 只读回显契约（内置兜底可见，但不开第二写入口）
# --------------------------------------------------------------------------- #


def test_TC_INT_R17_prompt_list_exposes_readonly_builtin_fallback(http_app):
    """列表回执带每位专家的 `builtin_fallback`（只读展示）；顶层键集**不变**（5 键）。"""
    from ib.experts import builtin_fallback_for

    deps, Client = http_app
    got = Client().get(LIST, **AUTH)
    assert got.status_code == 200, got.content
    payload = json.loads(got.content)
    # 红线：顶层键集不变（加成式只能落在既有键**内部**）
    assert set(payload) == {
        "experts",
        "tool_param_specs",
        "available_tools",
        "layout",
        "config_key_names",
    }
    for entry in payload["experts"]:
        assert entry["builtin_fallback"] == builtin_fallback_for(entry["name"])
        assert entry["builtin_fallback"].strip()
    # 目录口径：`fallback.md` 亦可缺（REV-17 起回落代码内置兜底）
    assert "皆缺" in payload["layout"]["naming_rule"]
    assert "fallback.md 不得缺" not in payload["layout"]["naming_rule"]


def test_TC_INT_R17_write_paths_are_only_the_two_layers(http_app):
    """写入口纪律：只有 `main` / `fallback` 两层可写；不存在写内置兜底的端点。"""
    deps, Client = http_app
    client = Client()
    for bad_layer in ("builtin", "builtin_fallback", "default"):
        assert client.put(
            f"{LIST}/freeark-expert/{bad_layer}",
            data=json.dumps({"content": "x"}),
            content_type="application/json",
            **AUTH,
        ).status_code == 404
