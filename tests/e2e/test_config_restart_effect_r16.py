"""[REV-16-2 / GROUP_D] 端到端关键路径：保存 → 重启重装配生效 · 越界拒绝不变 · FreeArk 对齐。

每个用例在 docstring 标注所属 **US-IB-NN**（用户故事级覆盖的证据）。
关键路径 = Must Have 故事（US-IB-30 ~ US-IB-34 均属 Must Have）。

「重启」在离线环境下以**新进程视角重新装载 + 重新装配**模拟：新建 store 实例从磁盘
读回、`load_prompt_directory` 重新装载、`admit_two_domains` 重新校验并派生 —— 与生产
`ib-web` / `ib-worker` 手工重启后走同一装配序列（ADR-32 / IFC-IB-353）。
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
LIST = "/api/config/prompts"
DEF = "/api/config/definition"


# --------------------------------------------------------------------------- #
# US-IB-32（保存后经服务重启生效）+ US-IB-33（经文件落盘、跨重启保留）
# 溯源：AC-IB-32-01 / 32-03 / 33-01 / 33-03（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_022_save_then_restart_reassembly_takes_effect(tmp_path, django_ready, raw):
    """US-IB-32 + US-IB-33：HTTP 保存主提示词（原子落盘）→ 「重启」重装配 → 新配置生效。"""
    from django.test import Client

    from ib.config import FsExpertPromptStore, load_prompt_directory
    from ibweb.composition import (
        admit_two_domains,
        build_application,
        build_deps,
        known_tool_param_specs,
    )

    d = build_deps(raw, force=True)
    # 用**文件系统** store 装配（生产形态：独立 markdown 目录，落地到 tmp_path）
    d.prompt_stores["p_alpha"] = FsExpertPromptStore(str(tmp_path), "p_alpha")
    build_application(d)
    client = Client()

    # ① 保存（AC-IB-33-01：写入文件并持久保留）
    main_md = tmp_path / "p_alpha" / "freeark-expert" / "main.md"
    put = client.put(
        f"{LIST}/freeark-expert/main",
        data=json.dumps({"content": "重启后生效的主提示词：先澄清需求再执行"}),
        content_type="application/json",
        **AUTH,
    )
    assert put.status_code == 200, put.content
    assert json.loads(put.content)["saved"] is True
    assert main_md.read_text(encoding="utf-8").strip().startswith("重启后生效")

    # ② 保存不触发运行期热重载 / 图重编译（ADR-32 / C-IB-40：图对象保持同一实例）
    assert d.orchestrator_for("p_alpha") is d.orchestrator_for("p_alpha")

    # ③ 「重启」= 新进程视角：新 store 实例读盘 + 重新装载目录 + 重新装配（AC-IB-32-03）
    fresh_store = FsExpertPromptStore(str(tmp_path), "p_alpha")
    bundle = fresh_store.load_bundle("freeark-expert", doc_fallback="文档兜底")
    assert bundle.resolved_from == "main_file"
    assert bundle.effective_prompt.startswith("重启后生效")

    refs = load_prompt_directory(str(tmp_path), "p_alpha")
    view = admit_two_domains(
        d.definitions["p_alpha"],
        store=d.definition_store,
        prompt_refs=refs,
        tool_specs=known_tool_param_specs(),
    )
    by = {b.expert_name: b for b in view.prompt_bundles}
    assert by["freeark-expert"].effective_prompt.startswith("重启后生效")
    assert by["freeark-expert"].resolved_from == "main_file"
    # 其余专家未被牵连（分层/按专家隔离）
    assert all(
        b.effective_prompt.strip() for b in view.prompt_bundles
    )


# --------------------------------------------------------------------------- #
# US-IB-31（工具授权越界被拒且既有配置不变）+ ADR-16（无强制继续绕过）
# 溯源：AC-IB-31-03 / AC-IB-30-04（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_023_out_of_scope_grant_rejected_and_config_unchanged(http_app):
    """US-IB-31：提交越界工具授权 → 400 且既有在用配置不变；装配期闸门无绕过路径。"""
    import inspect

    from ibweb.composition import admit, admit_two_domains

    deps, Client = http_app
    client = Client()
    doc = json.loads(client.get(DEF, **AUTH).content)["document"]
    base = doc["content_hash"]

    bad = json.loads(json.dumps(doc))
    bad["tool_grants"][0]["tool_names"] = ["ghost-tool"]  # 引用不存在的工具
    resp = client.put(
        DEF,
        data=json.dumps({"document": bad, "expected_content_hash": base}),
        content_type="application/json",
        **AUTH,
    )
    assert resp.status_code == 400, resp.content
    items = json.loads(resp.content)["error"]["items"]
    assert any(i["code"] == "tool_grant_tool_unknown" for i in items)

    # fail-safe：既有在用配置逐位不变（未被半写入破坏）
    stored = deps.definition_store.load("p_alpha")
    assert stored.content_hash == base
    assert stored.tool_grants == deps.definitions["p_alpha"].tool_grants

    # 装配期闸门在**类型层**不提供 force/ignore/warn_only（ADR-16：不存在绕过）
    assert set(inspect.signature(admit).parameters) == {"doc", "store"}
    assert not (
        set(inspect.signature(admit_two_domains).parameters)
        & {"force", "ignore", "warn_only", "warnOnly"}
    )


# --------------------------------------------------------------------------- #
# US-IB-34：示例项目专家定义与 FreeArk 注册表 100% 对齐（含专家名）
# 溯源：AC-IB-34-01 / 34-02 / 34-04（关键路径）
# 备注：AC-IB-34-03（FreeArk 未被修改）为**跨仓只读事实**，离线不可自证 —— 见 test_plan 不可测试项。
# --------------------------------------------------------------------------- #


def test_TC_E2E_024_demo_project_experts_aligned_with_freeark(http_app):
    """US-IB-34：示例项目默认专家集与 FreeArk 专家注册表严格对齐（专家名 + cn_label + 工具名）。"""
    import ib.experts as experts
    from ibweb.composition import known_tool_names

    deps, Client = http_app

    # 对齐后的专家标识（与只读参考 FreeArk:.../experts.py 的 EXPERT_SPECS 逐字段一致）
    assert experts.names() == ("freeark-expert", "inspection-expert", "sanheng-knowledge")
    assert experts.cn_map() == {
        "freeark-expert": "系统管家",
        "inspection-expert": "巡检诊断",
        "sanheng-knowledge": "三恒知识",
    }

    # 每个已装配项目的默认种子专家集 = 对齐集（AC-IB-34-04：默认专家集为对齐后的定义）
    assert deps.definitions, "装配未产出任何项目的定义文档"
    for _pid, doc in deps.definitions.items():
        assert {e.name for e in doc.experts} == set(experts.names())
        # 工具集合以「工具名对齐」为准（参数为显式排除维，ADR-31）
        for grant in doc.tool_grants:
            assert set(grant.tool_names) <= set(known_tool_names())
            assert not grant.param_values or all(
                pv.name.split(".")[0] in known_tool_names() for pv in grant.param_values
            )

    # 示例项目锚点 = demo（AC-IB-34-04）：`src/deploy/config.example.json`
    repo = pathlib.Path(__file__).resolve().parents[2]
    example = json.loads((repo / "src" / "deploy" / "config.example.json").read_text(encoding="utf-8"))
    assert "demo" in example["projects"], "示例项目锚点应为 demo（OQ-IB-23）"

    # 端点回执的专家名与注册表同源（不存在第二真源）
    payload = json.loads(Client().get(LIST, **AUTH).content)
    assert {e["name"] for e in payload["experts"]} == set(experts.names())
