"""单元测试 —— LLM 工具调用循环（function-calling；MOD-IB-20 内部实现）。

覆盖 IFC-IB-212（专家角色）补齐的工具执行路径：把 `BoundTool` 交给 LLM **真正执行**，
而不是只把工具名/描述当文字拼进 prompt（后者正是聊天检索不落地的根因 —— 工具被描述
却从未执行）。

全部离线：用 langchain-core 的 `AIMessage`/`ToolMessage`（requirements-offline 已含）
+ 一个脚本化假客户端，不触网、不 import langchain-openai。
"""

from __future__ import annotations

from ib.core import BoundTool, ToolResult


def _bound_search(record: list) -> BoundTool:
    """构造一个会记录 query 的检索工具（替身），供断言「工具真的被调用」。"""

    def _call(query=None, **kwargs):
        record.append(query)
        return ToolResult(ok=True, content=f"命中片段：{query}")

    return BoundTool(
        name="search_knowledge",
        description="在企业知识库中检索与问题相关的资料片段",
        callable=_call,
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )


class _ScriptedClient:
    """脚本化客户端：`bind_tools` 记录 schema，`invoke` 依序弹出预置响应。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self.bound_schemas = None

    def bind_tools(self, schemas):
        self.bound_schemas = schemas
        return self

    def invoke(self, messages):
        return self._responses.pop(0)


def test_TC_UNIT_076_tool_schema_from_bound_tool():
    """[TC-UNIT-076] `_tool_schema`：BoundTool → OpenAI function schema（参数取自 parameters）。"""
    from ib.llm import _tool_schema

    schema = _tool_schema(_bound_search([]))
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "search_knowledge"
    assert schema["function"]["parameters"]["required"] == ["query"]
    # 无 parameters 的工具退化为空对象 schema（无参工具）
    bare = _tool_schema(BoundTool(name="t", description="d", callable=lambda: ToolResult(ok=True, content="x")))
    assert bare["function"]["parameters"] == {"type": "object", "properties": {}}


def test_TC_UNIT_077_tool_call_parts_both_shapes():
    """[TC-UNIT-077] `_tool_call_parts`：dict 与属性对象两种形态都正确拆解。"""
    from ib.llm import _tool_call_parts

    assert _tool_call_parts({"name": "t", "args": {"q": "1"}, "id": "c1"}) == ("t", {"q": "1"}, "c1")
    assert _tool_call_parts({"name": "t"}) == ("t", {}, "")

    class _Obj:
        name = "u"
        args = {"q": "2"}
        id = "c2"

    assert _tool_call_parts(_Obj()) == ("u", {"q": "2"}, "c2")


def test_TC_UNIT_078_execute_tool_calls_bound_callable():
    """[TC-UNIT-078] `_execute_tool`：真正执行 callable、取 content；异常 → 可读占位。"""
    from ib.llm import _execute_tool

    seen = []
    tool = _bound_search(seen)
    assert _execute_tool(tool, {"query": "冷冻水泵"}) == "命中片段：冷冻水泵"
    assert seen == ["冷冻水泵"]

    def _boom(**kw):
        raise RuntimeError("down")

    assert _execute_tool(BoundTool(name="b", description="", callable=_boom), {}) == "（工具执行失败）"


def test_TC_UNIT_079_run_tool_loop_executes_tool_then_answers():
    """[TC-UNIT-079] 工具循环：模型先请求检索 → 执行工具 → 回填结果 → 得最终正文。

    缺陷根因的**正向回归守卫**：修复前工具从未被执行（只被描述）；本用例断言
    `BoundTool.callable` 被真正调用、检索结果进入第二轮上下文、schema 交给 `bind_tools`。
    """
    from langchain_core.messages import AIMessage

    from ib.llm import _PromptedClient

    seen = []
    tool = _bound_search(seen)
    client = _ScriptedClient([
        AIMessage(
            content="",
            tool_calls=[{"name": "search_knowledge", "args": {"query": "冷冻水泵启动顺序"}, "id": "call_1"}],
        ),
        AIMessage(content="先开冷却水泵，再开冷冻水泵。"),
    ])
    impl = _PromptedClient(client, "你是设备运维助手。")
    text = impl.run_tool_loop("用户问题：冷冻水泵的正确启动顺序", tools=[tool])

    assert text == "先开冷却水泵，再开冷冻水泵。"
    assert seen == ["冷冻水泵启动顺序"], "工具 callable 未被真正执行"
    assert client.bound_schemas is not None, "未把工具 schema 交给 bind_tools"


def test_TC_UNIT_080_run_tool_loop_no_tool_call_returns_directly():
    """[TC-UNIT-080] 模型未请求工具时，直接返回首轮正文（不强制检索）。"""
    from langchain_core.messages import AIMessage

    from ib.llm import _PromptedClient

    client = _ScriptedClient([AIMessage(content="这是通用知识回答。")])
    impl = _PromptedClient(client, "助手")
    assert impl.run_tool_loop("问题", tools=[_bound_search([])]) == "这是通用知识回答。"


def test_TC_UNIT_081_run_tool_loop_ignores_unknown_tool():
    """[TC-UNIT-081] 未知工具被忽略（回填「未知工具」），循环继续到最终正文。"""
    from langchain_core.messages import AIMessage

    from ib.llm import _PromptedClient

    client = _ScriptedClient([
        AIMessage(content="", tool_calls=[{"name": "ghost_tool", "args": {}, "id": "c"}]),
        AIMessage(content="忽略未知工具后作答。"),
    ])
    impl = _PromptedClient(client, "助手")
    assert impl.run_tool_loop("问题", tools=[_bound_search([])]) == "忽略未知工具后作答。"


def test_TC_UNIT_082_run_tool_loop_respects_max_iterations():
    """[TC-UNIT-082] 工具循环受 `max_iterations` 上限约束：到上限即停止，不再往返。"""
    from langchain_core.messages import AIMessage

    from ib.llm import _PromptedClient

    seen = []
    call = {"name": "search_knowledge", "args": {"query": "q"}, "id": "c"}
    responses = [AIMessage(content="", tool_calls=[call]) for _ in range(5)]
    client = _ScriptedClient(responses)
    impl = _PromptedClient(client, "助手")
    text = impl.run_tool_loop("问题", tools=[_bound_search(seen)], max_iterations=2)

    assert len(seen) == 2, f"应恰好执行 2 轮工具，实际 {len(seen)}"
    assert text == ""  # 最后一轮仍是工具调用、无正文
