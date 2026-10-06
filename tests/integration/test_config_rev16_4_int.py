"""[REV-16-4 / GROUP_D] 配置审计端点 · 存储态端点 · 保存 fail-safe（集成级）。

本文件为**测试工程师（GROUP_D）独立补充**的集成级用例，走**真实 HTTP 契约** +
离线装配（内存 ledger → `MemoryConfigAuditStore`），无网络、无真实凭据。

覆盖 REV-16-4 的四处变更：
  * **DEFECT-R16-02 修复的 fail-safe 性质**（TC-INT-141，**强制负例**）：非法工具参数
    保存 → 400，且随后 GET 读回**保存前**取值（在用的定义文档**未被改写**）；
  * `GET /api/config/storage-state`（IFC-IB-362）—— 存储态只读投影，不回显键值；
  * `GET /api/config/audit`（IFC-IB-359）—— 成功与失败**均**记录；只读、字段白名单；
  * 两端点的只读纪律（方法 / `?token=`）。

分层依据（test_plan §2）：跨 `ibweb.views` ↔ `ibweb.serializers` ↔ `ibweb.composition`
↔ `ib.config.*` ↔ `ib.ledger.*` ↔ Django 中间件 → **集成级**。
"""

from __future__ import annotations

import json
import os

AUTH = {"HTTP_AUTHORIZATION": f"Bearer {os.environ.get('IB_OFFLINE_TOKEN', 'groupd-offline-token')}"}
DEF = "/api/config/definition"
AUDIT = "/api/config/audit"
STORAGE = "/api/config/storage-state"


def _get_def(client) -> dict:
    resp = client.get(DEF, **AUTH)
    assert resp.status_code == 200, resp.content
    return json.loads(resp.content)["document"]


def _put_def(client, doc: dict, expected: str | None = None):
    body = {"document": doc}
    if expected is not None:
        body["expected_content_hash"] = expected
    return client.put(DEF, data=json.dumps(body), content_type="application/json", **AUTH)


# --------------------------------------------------------------------------- #
# [强制负例] DEFECT-R16-02 修复的 **fail-safe** 性质 —— 不只是状态码
# 溯源：AC-IB-30-04「保存内容不合法 → 被完备性校验拒绝，既有在用配置保持不变」
#
# 本用例同时断言两件事（缺一不可）：
#   (i)  携带**非法工具参数**的 PUT 返回 **400**；
#   (ii) **随后** GET 同一配置返回**保存前**的取值 —— 即在用配置未被半写入覆盖。
# 只断言 400 不足以证明 fail-safe：缺陷版本正是「400 但没有/有落盘」的模糊态。
# --------------------------------------------------------------------------- #


def test_TC_INT_141_failed_save_is_failsafe_via_subsequent_get(http_app):
    deps, Client = http_app
    client = Client()

    before = _get_def(client)  # 保存前的完整在用定义文档
    base = before["content_hash"]
    stored_before = deps.definition_store.load("p_alpha")

    bad = json.loads(json.dumps(before))
    # `search_knowledge.nope` 未被任何 ToolParamSpec 声明 —— 属「保存内容不合法」
    bad["tool_grants"][0]["param_values"] = [{"name": "search_knowledge.nope", "value": "1"}]
    resp = _put_def(client, bad, expected=base)

    # (i) 非法工具参数保存 → 400（完备性校验拒绝）
    assert resp.status_code == 400, (
        f"DEFECT-R16-02 未被修复：非法工具参数保存应 400，实测 {resp.status_code}；{resp.content!r}"
    )

    # (ii) 随后 GET 读回**保存前**取值（在用配置未被改写）
    after = _get_def(client)
    assert after == before, "fail-safe 被破坏：非法保存后 GET 读回的配置与保存前不一致"
    # 存储层亦逐位不变（GET 只是投影；此为第二重独立取证）
    stored_after = deps.definition_store.load("p_alpha")
    assert stored_after.content_hash == stored_before.content_hash
    assert stored_after.tool_grants == stored_before.tool_grants

    # 对照：合法参数保存 → 200（证明 400 由「非法」触发，而非校验器一律拒绝）
    good = json.loads(json.dumps(before))
    good["tool_grants"][0]["param_values"] = [
        {"name": "search_knowledge.query", "value": "占位查询词"}
    ]
    ok = _put_def(client, good, expected=base)
    assert ok.status_code == 200, ok.content


# --------------------------------------------------------------------------- #
# IFC-IB-361 / 362（ADR-35）：存储态只读投影 —— 仅暴露存储态，不回显任何键值
# 溯源：AC-IB-33-02（未启用持久化 → 明确提示「配置仅内存生效、不跨重启保留」）
# --------------------------------------------------------------------------- #


def test_TC_INT_142_storage_state_endpoint_reports_memory_without_values(http_app):
    deps, Client = http_app
    resp = Client().get(STORAGE, **AUTH)
    assert resp.status_code == 200, resp.content
    payload = json.loads(resp.content)

    # 字段白名单：恰四键，绝无路径值 / 键值（ADR-35：只登记键名与否）
    assert set(payload) == {
        "definition_store",
        "prompt_store",
        "definition_store_configured",
        "prompt_store_configured",
    }
    # 离线装配 = 内存定义文档 store + 内存提示词 store
    assert payload["definition_store"] == "memory"
    assert payload["prompt_store"] == "memory"
    assert payload["definition_store_configured"] is False
    assert payload["prompt_store_configured"] is False
    # 单一来源 = 装配期实际选用的存储实现（IFC-IB-361）：HTTP 回执与装配结果直读一致
    from ibweb.composition import get_storage_state

    state = get_storage_state(deps=deps)
    assert payload == {
        "definition_store": state.definition_store,
        "prompt_store": state.prompt_store,
        "definition_store_configured": bool(state.definition_store_configured),
        "prompt_store_configured": bool(state.prompt_store_configured),
    }
    # 响应体不得出现任何环境变量**取值**（只允许键名与否；此处连键名都不出现）
    text = resp.content.decode("utf-8")
    assert "IB_DEFINITION_DOC_PATH" not in text
    assert os.path.sep not in text


# --------------------------------------------------------------------------- #
# IFC-IB-359 / 360（ADR-34）：审计端点 —— 成功与失败**均**可查询；字段白名单
# 溯源：AC-IB-32-02（生效记录「谁 / 何时 / 改了哪些字段 / 结果」可查询）
# --------------------------------------------------------------------------- #


def _audit_items(client) -> list[dict]:
    resp = client.get(AUDIT, **AUTH)
    assert resp.status_code == 200, resp.content
    body = json.loads(resp.content)
    assert set(body) == {"items", "total"}
    assert body["total"] == len(body["items"])
    return body["items"]


def test_TC_INT_143_audit_records_successful_save(http_app):
    deps, Client = http_app
    client = Client()

    doc = _get_def(client)
    doc["tool_grants"][0]["param_values"] = [
        {"name": "search_knowledge.query", "value": "占位查询词"}
    ]
    put = _put_def(client, doc, expected=doc["content_hash"])
    assert put.status_code == 200, put.content

    items = _audit_items(client)
    assert items, "成功保存后审计应有记录（AC-IB-32-02：可查询）"
    saved = [e for e in items if e["result"] == "saved"]
    assert saved, "成功保存应记 result=saved"
    last = saved[-1]
    # 字段白名单：恰七键，且含「谁 / 何时 / 改了哪些字段」
    assert set(last) == {
        "timestamp",
        "project",
        "actor",
        "action",
        "changed_field_names",
        "result",
        "detail_code",
    }
    assert last["project"] == "p_alpha"
    assert last["actor"]  # 「谁」
    assert last["timestamp"]  # 「何时」
    assert last["action"] == "definition.save"
    assert isinstance(last["changed_field_names"], list)
    # 变更字段名指向 param_values（「改了哪些字段」；只出字段名，不含取值）
    assert any("param_values" in name for name in last["changed_field_names"])
    assert "占位查询词" not in json.dumps(items, ensure_ascii=False)


def test_TC_INT_144_audit_records_rejected_save(http_app):
    deps, Client = http_app
    client = Client()

    doc = _get_def(client)
    bad = json.loads(json.dumps(doc))
    bad["tool_grants"][0]["tool_names"] = ["nope-tool"]
    resp = _put_def(client, bad, expected=doc["content_hash"])
    assert resp.status_code == 400, resp.content

    items = _audit_items(client)
    rejected = [e for e in items if e["result"] == "rejected"]
    assert rejected, "被拒保存也应记审计（ADR-34：成功与失败均记录）"
    last = rejected[-1]
    # `detail_code` 只含**错误码**（不回显任何取值）
    assert last["detail_code"] is not None
    assert "tool_grant_tool_unknown" in last["detail_code"]


# --------------------------------------------------------------------------- #
# 只读纪律（IFC-IB-357：端口无 update / delete；REV-16-4 旧口径不变）
# --------------------------------------------------------------------------- #


def test_TC_INT_145_readonly_audit_and_storage_state_discipline(http_app):
    import inspect

    import ib.core as core
    from ib.ledger.config_audit import MemoryConfigAuditStore, SqliteConfigAuditStore

    deps, Client = http_app
    client = Client()

    # 端口 / 实现类型层排除 update / delete（审核只读）
    port_methods = {
        n
        for n, _ in inspect.getmembers(core.ConfigAuditStore, predicate=inspect.isfunction)
        if not n.startswith("_")
    }
    assert port_methods == {"record", "list_by_project"}
    for impl in (MemoryConfigAuditStore, SqliteConfigAuditStore):
        assert not hasattr(impl, "update") and not hasattr(impl, "delete")

    # 方法纪律：仅 GET（POST → 405 method_not_allowed）
    for path in (AUDIT, STORAGE):
        post = client.post(path, data="{}", content_type="application/json", **AUTH)
        assert post.status_code == 405, post.content
        assert json.loads(post.content)["error"]["code"] == "method_not_allowed"

    # 契约纪律（IC-IB-01）：两端点亦不接受 `?token=`（中间件先于路由拒绝 → 4xx）
    for path in (AUDIT, STORAGE):
        resp = client.get(f"{path}?token=placeholder", **AUTH)
        assert resp.status_code == 400, resp.content


def test_TC_INT_146_save_and_assembly_share_one_validation_entry(http_app):
    """保存路径与装配路径共用 `validate_definition_full` —— 判据一致，杜绝漂移。"""
    import ib.core as core
    from ibweb.composition import admit_two_domains

    deps, Client = http_app
    client = Client()

    doc = _get_def(client)
    base = doc["content_hash"]
    bad = json.loads(json.dumps(doc))
    bad["tool_grants"][0]["param_values"] = [{"name": "search_knowledge.nope", "value": "1"}]

    # 保存路径：非法参数 → 400 `tool_param_unknown`
    resp = _put_def(client, bad, expected=base)
    assert resp.status_code == 400, resp.content
    save_codes = {i["code"] for i in json.loads(resp.content)["error"]["items"]}
    assert "tool_param_unknown" in save_codes

    # 装配路径：同一非法文档 → 同一错误码（同一校验入口）
    from dataclasses import replace

    stored = deps.definition_store.load("p_alpha")
    bad_doc = replace(
        stored,
        tool_grants=(
            core.ToolGrantSpec(
                stored.experts[0].name,
                ("search_knowledge",),
                (core.ToolParamValue("search_knowledge.nope", "1"),),
            ),
        ),
    )
    import pytest

    with pytest.raises(core.ConfigError) as ei:
        admit_two_domains(
            bad_doc, store=deps.definition_store, prompt_refs=(), tool_specs=deps.tool_param_specs()
        )
    assert "tool_param_unknown" in {i.code for i in ei.value.validation_items}


# --------------------------------------------------------------------------- #
# [DEFECT-R16-4-01，如实失败] 审计写失败**非致命**契约未满足
# 溯源：AC-IB-32-04（保存失败 → 既有配置不变，fail-safe）/ ADR-34（审计是旁路，非第二真源）
#
# 规格：IFC-IB-360 / ADR-34 明确「审计写失败**不改变**保存结果，但**不静默** —— 发结构化
#       `WARN config_audit_write_failed`」。故 `record_config_audit` **永不**向调用方抛异常。
# 实测：`_warn_audit_write_failed`（composition.py:968）引用模块级 `log_event`，而后者在
#       composition.py 中**仅**以函数内局部导入引入 → 触发 `NameError`；异常从
#       `record_config_audit` 逸出。此为「审计旁路」契约被破坏（保存已落盘却向客户端报 500）。
# 修复属 software-developer 职责；本代理**只报告、不改 `src/`**。
# --------------------------------------------------------------------------- #


def test_TC_INT_147_audit_write_failure_must_be_non_fatal_DEFECT_R16_4_01(http_app):
    import ib.core as core
    from ibweb import composition

    deps, Client = http_app

    entry = core.ConfigAuditEntry(
        timestamp="2026-10-07T00:00:00Z",
        project="p_alpha",
        actor="tester",
        action="definition.save",
        changed_field_names=("tool_grants[0]",),
        result="saved",
        detail_code=None,
    )

    # (a) 审计存储缺失 → 应发 WARN 并返回（不抛）
    composition.record_config_audit(
        entry, deps=type("D", (), {"config_audit_store": None})()
    )

    # (b) 审计存储写入抛错 → 应发 WARN 并返回（不抛；保存结果不受影响）
    broken = type(
        "BrokenStore",
        (),
        {"record": lambda self, e: (_ for _ in ()).throw(RuntimeError("audit backend down"))},
    )()
    composition.record_config_audit(
        entry, deps=type("D", (), {"config_audit_store": broken})()
    )
