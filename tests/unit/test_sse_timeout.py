"""单元测试层 —— SSE 硬超时兜底（`ibweb.sse.bounded_events` / `encode_events`）。

覆盖问答流「**必然以 done 收尾**」的兜底语义：
  * `bounded_events`：正常透传事件并在源结束时终止；
  * `bounded_events`：源**阻塞**（既不产出也不抛异常）时，按墙钟预算抛 `OrchestrationTimeout`；
  * `encode_events`：超时收敛为 `error`（带明确文案）+ `done`，前端不再无限「生成中…」。

溯源：R15 问答卡死根因修复（SSE 硬超时兜底 + SQLite journal_mode 去重）。
离线约束：纯 stdlib + 生成器替身，不触网、不连 Django。
"""

from __future__ import annotations

import threading

import pytest

from ib.core import StreamEvent, StreamEventKind
from ibweb.sse import OrchestrationTimeout, bounded_events, encode_events


def _block_forever():
    """「阻塞」源生成器：永不产出事件、永不结束（模拟底层 I/O 卡死）。"""
    if False:  # pragma: no cover - 仅为声明生成器
        yield
    threading.Event().wait()  # 永久阻塞，不产出任何事件


def test_bounded_events_passes_through_and_terminates():
    source = (
        StreamEvent(kind, data)
        for kind, data in [
            (StreamEventKind.REASONING, "分析中"),
            (StreamEventKind.CONTENT, "答案"),
            (StreamEventKind.DONE, ""),
        ]
    )
    out = list(bounded_events(source, timeout_s=5.0))
    assert [e.kind for e in out] == [
        StreamEventKind.REASONING,
        StreamEventKind.CONTENT,
        StreamEventKind.DONE,
    ]


def test_bounded_events_times_out_when_source_blocks():
    with pytest.raises(OrchestrationTimeout):
        list(bounded_events(_block_forever(), timeout_s=0.2))


def test_bounded_events_rethrows_source_exception_in_consumer():
    def boom():
        if False:  # pragma: no cover - 仅为声明生成器
            yield
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        list(bounded_events(boom(), timeout_s=5.0))


def test_encode_events_timeout_yields_error_then_done():
    frames = list(encode_events(bounded_events(_block_forever(), timeout_s=0.2)))
    assert frames  # 至少 error + done
    # 收尾帧必须是 done（前端唯一终止条件）
    assert frames[-1] == "event: done\ndata:\n\n"
    # 超时要给出明确文案，而不是笼统的「发生错误」
    assert any("回答超时" in frame for frame in frames)


def test_encode_events_normal_stream_ends_with_done():
    source = (StreamEvent(StreamEventKind.CONTENT, "答案") for _ in [0])
    frames = list(encode_events(source))
    assert frames[-1] == "event: done\ndata:\n\n"
