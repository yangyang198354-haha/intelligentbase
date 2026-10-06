"""[REV-16-4 / GROUP_D] 配置审计 · 统合校验入口 · 存储态（单元级）。

本文件为**测试工程师（GROUP_D）独立补充**的单元级用例，覆盖 REV-16-4 的四处变更：

  1. `validate_definition_full`（IFC-IB-355 = IFC-IB-290 ∪ IFC-IB-346）—— 合成纯函数；
  2. `ConfigAuditEntry`（IFC-IB-356）/ `ConfigAuditStore` 端口（IFC-IB-357）/
     `SqliteConfigAuditStore`（IFC-IB-358）—— 只读追加式审计，**无 update / delete**；
  3. `StorageState`（IFC-IB-361）—— 存储态取值域与语义（`memory` = 仅内存生效）；
  4. `changed_field_names`（IFC-IB-360）派生 —— 只出字段名，绝不含取值（SC-3）。

逐条溯源至 `user_stories.md` 的 AC-IB-30-04 / AC-IB-31-02 / AC-IB-32-02 / AC-IB-33-02。
分层依据（test_plan §2）：单函数 / 单模块纯行为 → **单元级**；不启 HTTP、不连网。
"""

from __future__ import annotations

import inspect
from dataclasses import fields, replace
from typing import get_args

import ib.core as core
from ib.config import validate_definition_full
from ib.ledger.config_audit import (
    MemoryConfigAuditStore,
    SqliteConfigAuditStore,
    build_config_audit_store,
)


def _entry(
    *,
    project: str = "p_alpha",
    actor: str = "tester",
    action: str = "definition.save",
    changed: tuple[str, ...] = ("tool_grants[0].param_values[0]",),
    result: str = "saved",
    detail_code: str | None = None,
    timestamp: str = "2026-10-07T00:00:00Z",
) -> core.ConfigAuditEntry:
    return core.ConfigAuditEntry(
        timestamp=timestamp,
        project=project,
        actor=actor,
        action=action,
        changed_field_names=changed,
        result=result,  # type: ignore[arg-type]
        detail_code=detail_code,
    )


# --------------------------------------------------------------------------- #
# IFC-IB-355 / ADR-33：`validate_definition_full` 是「保存路径 ∪ 装配路径」的**唯一入口**
# 溯源：AC-IB-30-04（保存内容不合法 → 被完备性校验拒绝）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_123_validate_definition_full_unions_both_domains_in_fixed_order(deps):
    """定义文档域 ∪ 工具参数域按固定顺序合并；纯函数，无旁路字段。"""
    doc = deps.definitions["p_alpha"]
    specs = deps.tool_param_specs()

    # 同时制造「定义文档域」错误（未知工具）与「工具参数域」错误（未知参数）
    bad = replace(
        doc,
        tool_grants=(
            core.ToolGrantSpec(
                doc.experts[0].name,
                ("ghost-tool",),
                (core.ToolParamValue("search_knowledge.nope", "1"),),
            ),
        ),
    )

    report = validate_definition_full(
        bad, known_tools=("search_knowledge",), tool_param_specs=specs
    )

    assert report.ok is False
    codes = [item.code for item in report.errors]
    assert "tool_grant_tool_unknown" in codes  # 定义文档域（validate / IFC-IB-290）
    assert "tool_param_unknown" in codes  # 工具参数域（validate_tool_params / IFC-IB-346）
    # 固定顺序：定义文档域在前，工具参数域在后（端点回执稳定可预期）
    assert codes.index("tool_grant_tool_unknown") < codes.index("tool_param_unknown")

    # 纯函数：合法文档 → ok，且报告字段集恰为 {ok, errors}（ADR-16：无 force/ignore/warn_only）
    ok_report = validate_definition_full(
        doc, known_tools=("search_knowledge",), tool_param_specs=specs
    )
    assert ok_report.ok is True
    assert {f.name for f in fields(ok_report)} == {"ok", "errors"}

    # 纯函数：无 I/O —— 源码内不得出现 open/os.environ/socket/subprocess 等副作用调用
    source = inspect.getsource(validate_definition_full)
    for forbidden in ("open(", "os.environ", "socket", "subprocess", "requests"):
        assert forbidden not in source


# --------------------------------------------------------------------------- #
# IFC-IB-357 / 358：审计端口「恰好两个方法」，两种实现语义对齐（追加式、只读）
# 溯源：AC-IB-32-02（生效记录可查询 —— 谁 / 何时 / 改了哪些字段 / 结果）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_124_audit_store_append_only_roundtrip(tmp_path):
    """Memory / Sqlite 两实现的读取语义对齐：只追加、按项目过滤、稳定升序、limit/offset。"""
    for store in (
        MemoryConfigAuditStore(),
        SqliteConfigAuditStore(str(tmp_path / "audit.sqlite3")),
    ):
        store.record(_entry(changed=("a",), timestamp="t1"))
        store.record(_entry(changed=("b",), result="rejected", detail_code="tool_param_unknown"))
        store.record(_entry(project="p_beta", changed=("c",)))

        items = store.list_by_project("p_alpha")
        assert [e.changed_field_names for e in items] == [("a",), ("b",)]  # 追加序 + 项目过滤
        assert items[1].result == "rejected"
        assert items[1].detail_code == "tool_param_unknown"

        # limit / offset 分页（端点 `?limit=&offset=` 的底层契约）
        assert [e.changed_field_names for e in store.list_by_project("p_alpha", limit=1, offset=1)] == [
            ("b",)
        ]
        # 项目隔离：p_beta 只见自己那条
        assert [e.project for e in store.list_by_project("p_beta")] == ["p_beta"]
        if hasattr(store, "close"):
            store.close()


def test_TC_UNIT_125_audit_surface_is_read_only_and_value_free():
    """端口 / 实现**无** update / delete；`ConfigAuditEntry` 不承载任何配置取值（SC-3）。"""
    port_methods = {
        name
        for name, _ in inspect.getmembers(core.ConfigAuditStore, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    assert port_methods == {"record", "list_by_project"}

    for impl in (MemoryConfigAuditStore, SqliteConfigAuditStore):
        for forbidden in ("update", "delete", "remove", "clear", "purge"):
            assert not hasattr(impl, forbidden), f"{impl.__name__} 不得暴露 {forbidden}"
        assert hasattr(impl, "record") and hasattr(impl, "list_by_project")

    # 结构层不含任何承载「取值 / 凭据」的字段（只出字段名与结果码）
    entry_fields = {f.name for f in fields(core.ConfigAuditEntry)}
    assert entry_fields == {
        "timestamp",
        "project",
        "actor",
        "action",
        "changed_field_names",
        "result",
        "detail_code",
    }
    assert not {n for n in entry_fields if "value" in n or "secret" in n or "token" in n}


def test_TC_UNIT_126_storage_state_domain_and_semantics(deps):
    """`StorageState` 取值域 `{memory,file}`；离线装配 = memory/memory 且未配置。"""
    from ibweb.composition import get_storage_state

    assert get_args(core.StoreMode) == ("memory", "file")
    assert {f.name for f in fields(core.StorageState)} == {
        "definition_store",
        "prompt_store",
        "definition_store_configured",
        "prompt_store_configured",
    }

    state = get_storage_state(deps=deps)
    # 离线装配：内存定义文档 store + 内存提示词 store；两键均未配置
    assert state.definition_store == "memory"
    assert state.prompt_store == "memory"
    assert state.definition_store_configured is False
    assert state.prompt_store_configured is False
    # `memory` 即「配置仅内存生效、不跨重启保留」（ADR-35 / AC-IB-33-02）
    assert "memory" in (state.definition_store, state.prompt_store)
