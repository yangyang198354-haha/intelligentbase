# REV-26 ADR-57 / 假设 A-R26-01：固化 LangGraph 行为契约（离线，不连任何外部服务）。
# 契约失败 = 层归一化 DAG 编译方案的前提不成立，须回 GROUP_B。
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class _S(TypedDict, total=False):
    outputs: Annotated[dict, lambda a, b: {**(a or {}), **(b or {})}]
    trace: Annotated[list, operator.add]


def _node(name: str):
    def _run(state: _S) -> dict[str, Any]:
        return {"outputs": {name: "ok"}, "trace": [name]}

    return _run


def _build_layered(active_branch: list[str], *, with_relay: bool = True):
    """route(1) -> a/b/r(2) -> [c(3)] -> join(4)。with_relay=True：a、b 经中继 ra、rb 补到第 3 层（层归一化）。"""
    g = StateGraph(_S)
    for n in ("route", "a", "b", "c", "join", "r"):
        g.add_node(n, _node(n))
    g.add_edge(START, "route")
    g.add_conditional_edges("route", lambda s: list(active_branch), ["a", "b", "r"])
    if with_relay:
        for src in ("a", "b"):
            g.add_node(f"relay_{src}", _node(f"relay_{src}"))
            g.add_edge(src, f"relay_{src}")
            g.add_edge(f"relay_{src}", "join")
    else:
        g.add_edge("a", "join")
        g.add_edge("b", "join")
    g.add_edge("r", "c")
    g.add_edge("c", "join")
    g.add_edge("join", END)
    return g.compile()


def test_without_relay_join_may_run_twice_which_is_why_layering_is_required():
    # 反证：未层归一化（边跨层不等）时 join 会被触发两次——ADR-57 选 E 的依据。
    out = _build_layered(["a", "r"], with_relay=False).invoke({})
    assert out["trace"].count("join") == 2


def test_join_runs_once_when_two_upstreams_in_same_superstep():
    # a / b 在同一超步完成；join（两条入边）只运行一次。
    out = _build_layered(["a", "b"]).invoke({})
    assert out["trace"].count("join") == 1
    assert {"a", "b"} <= set(out["trace"])


def test_join_runs_when_only_one_upstream_active_no_deadlock():
    # 只激活一路时，join 不死等未被激活的上游（add_edge 逐条写法）。
    out = _build_layered(["a"]).invoke({})
    assert out["trace"].count("join") == 1
    assert "b" not in out["trace"]


def test_relay_aligns_layers_join_runs_once_after_all_active_arrive():
    # a（层 2）与经中继的 c（层 3 路径更长）同被激活：join 在 c 之后只运行一次，且晚于 a、c。
    out = _build_layered(["a", "r"]).invoke({})
    tr = out["trace"]
    assert tr.count("join") == 1
    assert tr.index("join") > tr.index("c") and tr.index("join") > tr.index("a")


def test_conditional_edges_return_list_runs_parallel_next_superstep():
    out = _build_layered(["a", "b"]).invoke({})
    assert out["outputs"].keys() >= {"a", "b", "join"}
    # 并行写入同一 reducer 键不丢数据
    assert out["outputs"]["a"] == "ok" and out["outputs"]["b"] == "ok"


def test_interrupt_before_with_memory_saver_suspend_and_resume():
    g = StateGraph(_S)
    for n in ("pre", "confirm", "post"):
        g.add_node(n, _node(n))
    g.add_edge(START, "pre")
    g.add_edge("pre", "confirm")
    g.add_edge("confirm", "post")
    g.add_edge("post", END)
    app = g.compile(checkpointer=MemorySaver(), interrupt_before=["confirm"])
    cfg = {"configurable": {"thread_id": "t-r26"}}
    mid = app.invoke({}, cfg)
    assert mid["trace"] == ["pre"]  # 在 confirm 之前挂起
    assert app.get_state(cfg).next == ("confirm",)
    done = app.invoke(None, cfg)  # 恢复
    assert done["trace"] == ["pre", "confirm", "post"]


def test_interrupt_state_lost_with_new_saver_is_not_resumable():
    # 重启 = 新 MemorySaver：旧线程无挂起态（A06 fail-closed 的前提）。
    g = StateGraph(_S)
    for n in ("pre", "confirm"):
        g.add_node(n, _node(n))
    g.add_edge(START, "pre")
    g.add_edge("pre", "confirm")
    g.add_edge("confirm", END)
    app1 = g.compile(checkpointer=MemorySaver(), interrupt_before=["confirm"])
    cfg = {"configurable": {"thread_id": "t-lost"}}
    app1.invoke({}, cfg)
    app2 = g.compile(checkpointer=MemorySaver(), interrupt_before=["confirm"])
    assert app2.get_state(cfg).next == ()
