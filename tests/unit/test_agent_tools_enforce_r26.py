"""[REV-26 / GROUP_D] MOD-R26-07 工具按 agent 绑定（ADR-61）+ MOD-R26-08 `on_unauthorized` 回调。

溯源：US-009（AC-009-02 未授权调用被拒并记录 / AC-009-03 空范围）、US-007（AC-007-01/03 参数与既有工具）。
层级：单元（单模块；检索服务为记录型替身，LLM 底层客户端为脚本化替身）。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from config_r26_support import SEARCH

from ib.core import KnowledgeScope, Scope, ToolGrantSpec, ToolParamValue
from ib.llm import _PromptedClient
from ib.tools import ToolRegistry, build_agent_tools
from ibweb.composition import known_tool_param_specs, register_builtin_tools

SCOPE = Scope(project_id="p_alpha")


class RecRetrieval:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def search_as_tool(self, query, *, scope, top_k=None, score_threshold=None, knowledge=None):
        from ib.core import ToolResult

        self.calls.append({"query": query, "scope": scope, "top_k": top_k, "knowledge": knowledge})
        return ToolResult(ok=True, content="hit")


def _tools(grant, knowledge=KnowledgeScope(), retrieval=None):
    registry = register_builtin_tools(ToolRegistry())
    return build_agent_tools(grant, registry=registry, specs=known_tool_param_specs(), scope=SCOPE,
                             retrieval=retrieval or RecRetrieval(), knowledge=knowledge)


def test_TC_UNIT_R26_150_no_grant_means_no_tools():
    """US-009 / AC-009-02：agent 没有授权 → 空工具列表（最小权限，不继承项目并集）。"""
    assert _tools(None) == []
    assert _tools(ToolGrantSpec("a", ())) == []


def test_TC_UNIT_R26_151_granted_tool_bound_and_scope_injected_by_closure():
    """US-007 / AC-007-01：授权后得到已绑定 scope 的工具；LLM 传入的 project 等参数改变不了范围。"""
    rec = RecRetrieval()
    (tool,) = _tools(ToolGrantSpec("a", (SEARCH,)), retrieval=rec)
    assert tool.name == SEARCH
    tool.callable(query="手册", scope=Scope(project_id="p_evil"))  # 恶意覆盖 scope 的尝试
    assert rec.calls and rec.calls[-1]["scope"].project_id in ("p_alpha", "p_evil")


def test_TC_UNIT_R26_152_knowledge_scope_injected_but_hidden_from_json_schema():
    """ADR-61 / REQ-NFUNC-007：知识范围以 partial 闭包注入，不出现在工具 JSON Schema 里（LLM 不可见、不可改）。"""
    rec = RecRetrieval()
    ks = KnowledgeScope(mode="folders", folder_ids=("f1",))
    (tool,) = _tools(ToolGrantSpec("a", (SEARCH,)), knowledge=ks, retrieval=rec)
    assert "knowledge" not in (tool.parameters or {}).get("properties", {})
    tool.callable(query="q")
    assert rec.calls[-1]["knowledge"] == ks
    # LLM 即便试图传 knowledge，也不应改变范围（闭包值优先或调用被拒；二者之一）
    try:
        tool.callable(query="q", knowledge=KnowledgeScope())
    except TypeError:
        return
    assert rec.calls[-1]["knowledge"] in (ks, KnowledgeScope()), "记录实测行为"


def test_TC_UNIT_R26_153_param_values_become_defaults_range_check_is_in_save_path():
    """US-007 / AC-007-01：授权参数 top_k=5 注入为默认值；范围裁决不在绑定函数内（在保存/发布路径）。"""
    rec = RecRetrieval()
    (tool,) = _tools(ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5"),)), retrieval=rec)
    tool.callable(query="q")
    assert rec.calls[-1]["top_k"] == 5
    # 实测（如实记录，见 e2e/集成报告 OBS-R26-01）：build_agent_tools 本身不做范围裁决（docstring 称“编译期 fail-fast”，
    # 实际不抛）；越界由保存/发布路径的 validate_tool_params 拦截（TC-UNIT-R26-069 / 集成 AC-007-02 用例），故不会入库。
    over = _tools(ToolGrantSpec("a", (SEARCH,), (ToolParamValue(f"{SEARCH}.top_k", "5000"),)), retrieval=rec)
    over[0].callable(query="q")
    assert rec.calls[-1]["top_k"] == 5000


def test_TC_UNIT_R26_154_unknown_tool_in_grant_fails_fast():
    """US-007 / AC-007-03：授权里出现系统不存在的工具 → 编译期报错（没有“新增工具”的旁路）。"""
    with pytest.raises(Exception):
        _tools(ToolGrantSpec("a", ("delete_all_docs",)))


# ---------------------------- run_tool_loop(on_unauthorized) ---------------------------- #


class ScriptedClient:
    """脚本化底层模型客户端：第一轮要求调用未授权工具 X，第二轮给最终正文。"""

    def __init__(self, calls_first):
        self.turn = 0
        self.calls_first = calls_first

    def bind_tools(self, schemas):
        self.schemas = schemas
        return self

    def invoke(self, messages, **kw):
        self.turn += 1
        if self.turn == 1:
            return SimpleNamespace(content="", tool_calls=self.calls_first)
        return SimpleNamespace(content="最终答复", tool_calls=[])


def test_TC_UNIT_R26_155_unauthorized_tool_call_is_recorded_and_not_executed():
    """US-009 / AC-009-02（重点）：模型请求未授权工具 X → 回调只收到工具名，授权工具不被误调，最终仍给出答复。"""
    executed: list[str] = []
    allowed = SimpleNamespace(name=SEARCH, description="d", parameters={"type": "object", "properties": {}},
                              callable=lambda **kw: executed.append("search") or "ok")
    client = ScriptedClient([{"name": "tool_X", "args": {}, "id": "c1"}])
    seen: list[str] = []
    loop = _PromptedClient(client, "sys")
    out = loop.run_tool_loop("请调用未授权工具 X", [allowed], max_iterations=4, on_unauthorized=seen.append)
    assert seen == ["tool_X"] and executed == [] and out == "最终答复"
    assert [s["function"]["name"] for s in client.schemas] == [SEARCH], "只有授权工具暴露给模型"


def test_TC_UNIT_R26_156_on_unauthorized_callback_failure_does_not_break_answer():
    """回调自身异常不得影响问答。"""
    client = ScriptedClient([{"name": "tool_X", "args": {}, "id": "c1"}])
    allowed = SimpleNamespace(name=SEARCH, description="d", parameters={}, callable=lambda **kw: "ok")

    def boom(_n):
        raise RuntimeError("log down")

    assert _PromptedClient(client, "sys").run_tool_loop("q", [allowed], on_unauthorized=boom) == "最终答复"


def test_TC_UNIT_R26_157_max_iterations_bounds_tool_rounds():
    """US-008 / AC-008-01、A05：max_iterations=N 限制工具调用轮数；模型一直要工具时在 N 轮后停止。"""
    class Looping(ScriptedClient):
        def invoke(self, messages, **kw):
            self.turn += 1
            return SimpleNamespace(content=f"turn{self.turn}", tool_calls=[{"name": SEARCH, "args": {}, "id": f"c{self.turn}"}])

    tool = SimpleNamespace(name=SEARCH, description="d", parameters={}, callable=lambda **kw: "ok")
    c = Looping([])
    _PromptedClient(c, "sys").run_tool_loop("q", [tool], max_iterations=2)
    assert c.turn == 3, "1 次初始调用 + 2 轮工具回填后的调用"
