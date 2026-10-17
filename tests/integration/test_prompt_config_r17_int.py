"""[REV-17 → **REV-20 修订**] 保存期 ↔ 装配期**同一校验入口**。

覆盖 REV-17 的**结构性**保证（保存期与装配期同一条判据）：

  1. **同序同条**：同一份非法文档，走 `PUT /api/config/definition`（保存期）与走
     装配期 `admit_two_domains`，回执的校验项**逐条同序、同码、同路径**。REV-17 之前
     提示词域只在装配期查，于是「页面上存得下、重启装配才炸」是可能的（ADR-33 的漏洞）。
  2. **契约翻转（REV-20 / OQ-IB-42=B / ADR-48）**：原口径「新增专家无需任何提示词文件，
     回落代码内置兜底」；代码内置兜底退役后，新增专家**必须先在项目提示词目录落盘
     `main.md`**（或 `fallback.md`），否则保存期即 `prompt_missing` 拒绝 —— 
     「破死锁」的手段由**创建期落盘 / 回填迁移**承担，而非代码兜底。

另附回执契约：`GET /api/config/prompts` 的专家条目**不再**带 `builtin_fallback`
（字段随代码内置兜底一并删除；写入口仍只有 `main` / `fallback` 两层文件）。

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
    """塞一个**孤儿提示词文件**（目录有、定义文档未登记）以制造提示词域错误。

    **REV-20**：同时保留内置种子（`kb-agent/main.md`），否则文档内专家会额外触发
    `prompt_missing`，使本用例的「孤儿」判据被淹没。
    """
    from ib.config import InMemoryExpertPromptStore
    from ibweb.composition import _seed_prompt_documents, build_application

    documents = dict(_seed_prompt_documents())
    documents["ghost-expert"] = {"main": "孤儿提示词（未登记专家）"}
    deps.prompt_stores[project_id] = InMemoryExpertPromptStore(project_id, documents=documents)
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
    submitted = document_from_json("p_alpha", json.dumps(bad))
    refs = deps.prompt_stores["p_alpha"].list_refs()
    try:
        admit_two_domains(
            submitted,
            store=deps.definition_store,
            prompt_refs=refs,
            tool_specs=known_tool_param_specs(),
            prompt_store=deps.prompt_stores["p_alpha"],
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
# 2 · **REV-20 新契约**：新增专家必须先在项目提示词目录落盘
# --------------------------------------------------------------------------- #


def test_TC_INT_R17_new_expert_without_prompt_file_is_rejected_then_admitted_after_landing(
    http_app,
):
    """**契约翻转（REV-20 / OQ-IB-42=B / ADR-48）**：原 REV-17 口径「新增专家无需任何提示词
    文件，回落通用内置兜底」；代码内置兜底退役后，同一路径改为**保存期 fail-closed**
    （`prompt_missing`），并在**先落盘 `main.md`** 之后恢复可保存 / 可装配。
    """
    from ibweb.composition import admit_two_domains, known_tool_param_specs

    deps, Client = http_app
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]
    base = doc["content_hash"]

    new_name = "brand-new-expert"
    assert new_name not in {e["name"] for e in doc["experts"]}

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
    # ① 未落盘任何提示词文件 → 保存期即拒绝（两层皆缺 → prompt_missing）
    rejected = _put_definition(client, draft, base)
    assert rejected.status_code == 400, rejected.content
    assert any(
        code == "prompt_missing"
        for _path, code in _items_of_http(json.loads(rejected.content))
    )

    # ② 「先落盘」步（模拟运维在项目提示词目录写入 main.md）→ 保存成功
    store = deps.prompt_stores["p_alpha"]
    assert store.save_layer(new_name, "main", "# 新专家主提示词\n", expected_hash=None).saved
    saved = _put_definition(client, draft, base)
    assert saved.status_code == 200, saved.content

    # ③ 装配：生效提示词来自**项目提示词目录**（来源可核验），恒非空
    stored = deps.definition_store.load("p_alpha")
    view = admit_two_domains(
        stored,
        store=deps.definition_store,
        prompt_refs=store.list_refs(),
        tool_specs=known_tool_param_specs(),
        prompt_store=store,
    )
    bundle = next(b for b in view.prompt_bundles if b.expert_name == new_name)
    assert bundle.resolved_from == "main_file"
    assert bundle.effective_prompt == "# 新专家主提示词\n"
    assert bundle.effective_prompt.strip(), "生效提示词恒非空"

    # ④ 反证：写入口仍只有两层文件 —— 未登记进定义文档的专家照样写不进（反越域）
    assert client.put(
        f"{LIST}/not-in-document/fallback",
        data=json.dumps({"content": "x"}),
        content_type="application/json",
        **AUTH,
    ).status_code == 404


def test_TC_INT_R17_orphan_still_fails_while_missing_prompt_is_rejected(http_app):
    """反证：孤儿文件仍被拒（不是把提示词域校验整体关掉）。"""
    deps, Client = http_app
    _seed_orphan_prompt(deps)
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]

    resp = _put_definition(client, doc, doc["content_hash"])
    assert resp.status_code == 400, resp.content
    assert any(code == "prompt_orphan_file" for _p, code in _items_of_http(json.loads(resp.content)))


# --------------------------------------------------------------------------- #
# 3 · 回执契约（**REV-20**：`builtin_fallback` 字段已删除）
# --------------------------------------------------------------------------- #


def test_TC_INT_R17_prompt_list_contract_has_no_builtin_fallback_field(http_app):
    """**契约翻转（REV-20 / ADR-48）**：原回执每位专家带 `builtin_fallback`（只读展示）；
    代码内置兜底整体退役后该字段**删除**，专家条目键集收窄为
    `{name, cn_label, layers}`；顶层键集**不变**（5 键）。"""
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
        assert set(entry) == {"name", "cn_label", "layers"}, entry
        assert set(entry["layers"]) == {"main", "fallback"}
    # 目录口径：`fallback.md` 亦可缺；**两层皆缺 → prompt_missing**
    assert "皆缺" in payload["layout"]["naming_rule"]
    assert "fallback.md 不得缺" not in payload["layout"]["naming_rule"]


def test_TC_INT_R17_write_paths_are_only_the_two_layers(http_app):
    """写入口纪律：只有 `main` / `fallback` 两层可写；不存在写内置兜底的端点。

    **REV-20**：内置兜底已退役，`builtin` / `builtin_fallback` / `default` 三个层名
    在任何专家下都不存在可写端点（未登记专家 → 404；已登记专家 → 未知层被拒）。
    """
    deps, Client = http_app
    client = Client()
    for bad_layer in ("builtin", "builtin_fallback", "default"):
        assert client.put(
            f"{LIST}/kb-agent/{bad_layer}",
            data=json.dumps({"content": "x"}),
            content_type="application/json",
            **AUTH,
        ).status_code in (400, 404)
        # 未登记专家的写入口一律 404（反存在性探测）
        assert client.put(
            f"{LIST}/freeark-expert/{bad_layer}",
            data=json.dumps({"content": "x"}),
            content_type="application/json",
            **AUTH,
        ).status_code == 404
