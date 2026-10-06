"""
@module MOD-IB-23
@implements IFC-IB-247 SSE 承载（`StreamingHttpResponse` 原生 SSE）
@depends MOD-IB-21（`StreamEvent` / `to_sse` / `SSE_HEADERS`）
@author software-developer

SSE 响应构造（MOD-IB-21 的事件编码 + Django 的 `StreamingHttpResponse`）。

## 为什么是 `StreamingHttpResponse`，而不是 Channels/ASGI

R1 架构决策：WSGI（Waitress 主 / Gunicorn 备）承载。SSE 不需要 WebSocket 的双向能力，
`StreamingHttpResponse` 逐块写出即可。引入 Channels 会连带引入 Redis 与 ASGI 服务器，
把「一个 WSGI 进程」变成「ASGI + 消息中间件 + 第二个进程」——为了单向文本流，代价不成比例。

WAITRESS 的一个关键细节：**Waitress 会缓冲同步生成器的输出**，只有当缓冲区满或生成器结束时
才真正 flush。这意味着「首字节延迟」可能高到用户以为页面卡住。已知的可行做法是让生成器
在事件之间保持**足够小的输出**并依赖 `X-Accel-Buffering: no` 关掉前置 nginx 的缓冲。
本模块把 `X-Accel-Buffering: no` 放进 `SSE_HEADERS`（源头在 MOD-IB-21），
使「忘记关缓冲」这件事不可能发生。

## 异常必须在流内收敛，不能让它冒泡成 500

流已经开始写出后，HTTP 状态码**已经发出去**了（200 + `text/event-stream`）。此时抛异常，
客户端看到的是「连接被截断」——前端无法区分「回答完了」与「服务挂了」，只能等超时。
因此本模块在生成器内部捕获异常，转成 `error` 事件 + 紧跟一个 `done` 事件：
**流总是以 `done` 结尾**，这是前端唯一需要依赖的终止条件。
"""

from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any, Iterator

__all__ = ["streaming_sse_response", "encode_events"]


def encode_events(events: Iterator[Any]) -> Iterator[str]:
    """把 `StreamEvent` 迭代器编码为 SSE 帧文本，并在异常时补 `error` + `done`。

    错误信息**只输出异常类型与一句话原因**，不回显堆栈、请求内容或检索片段 ——
    流是对外的，任何回显都会同时成为「信息泄漏面」与「日志不留正文」纪律的漏洞。
    """
    from ib.core import StreamEvent, StreamEventKind
    from ib.streaming import to_sse

    finished = False
    try:
        for event in events:
            yield to_sse(event)
            if str(getattr(event, "kind", "")) == str(StreamEventKind.DONE):
                finished = True
    except Exception as exc:  # noqa: BLE001 - 见模块文档「异常必须在流内收敛」
        # 超时等可预期故障给出**具体**文案；其余异常一律用通用文案，不回显细节。
        message = getattr(exc, "public_message", None) or "生成回答时发生错误，请稍后重试"
        payload = json.dumps(
            {"code": type(exc).__name__, "message": message},
            ensure_ascii=False,
        )
        yield to_sse(StreamEvent(StreamEventKind.ERROR, payload))
    finally:
        if not finished:
            # 无论正常结束、异常退出还是客户端提前断开，都补上 `done`：
            # 前端只认 `done`，缺少它就会一直转圈（最典型的表现是「回答显示了但没停」）。
            yield to_sse(StreamEvent(StreamEventKind.DONE, ""))


def streaming_sse_response(events: Iterator[Any], *, status: int = 200) -> Any:
    """构造 SSE `StreamingHttpResponse`（少量头，全部来自 MOD-IB-21 的 `SSE_HEADERS`）。"""
    from django.http import StreamingHttpResponse
    from ib.streaming import SSE_CONTENT_TYPE, SSE_HEADERS

    response = StreamingHttpResponse(
        encode_events(bounded_events(events, ORCHESTRATION_STREAM_TIMEOUT_S)),
        status=status,
        content_type=SSE_CONTENT_TYPE,
    )
    for key, value in SSE_HEADERS.items():
        # `content_type` 已由构造参数写入，重复设置会覆盖为同一值（无害），此处直接全量铺上，
        # 保证「头集合只有一个来源」，避免两处各写一半而漏掉 `X-Accel-Buffering`。
        response[key] = value
    return response


#: 编排流**总**预算（秒）。硬超时兜底：即便编排内部某处**阻塞**（既不产出也不抛异常，
#: 例如底层 I/O 卡死），流也必定在此预算内以 `done` 收尾 —— 前端「生成中…」绝不会
#: 无限期转圈。正常路径数秒内结束，此值只防「未知卡死」，不限制正常回答。
ORCHESTRATION_STREAM_TIMEOUT_S = 90.0


class OrchestrationTimeout(Exception):
    """编排流在预算内既未结束也未产出下一事件时抛出（由 `bounded_events` 消费线程抛出）。"""

    public_message = "回答超时，请稍后重试"


def bounded_events(events: Iterator[Any], timeout_s: float) -> Iterator[Any]:
    """在后台线程驱动源生成器，消费端按**墙钟预算**拉取事件。

    为什么需要后台线程：编排器是同步生成器，内部的阻塞调用（SQLite / 网络）会**卡在
    消费线程里**，此时 `encode_events` 的 `try/finally → done` 兜底根本执行不到 ——
    「既不产出、也不抛异常」意味着流永远到不了 `done`。把源生成器搬到守护线程里驱动，
    消费端就能在预算耗尽时主动抛 `OrchestrationTimeout`，由 `encode_events` 收敛为
    `error + done`。守护线程无需 join：正常结束或客户端提前断开都无害（进程退出即回收）。
    """
    q: "queue.Queue[tuple[bool, Any]]" = queue.Queue()

    def _produce() -> None:
        try:
            for event in events:
                q.put((False, event))
        except Exception as exc:  # noqa: BLE001 - 源异常搬到消费线程重抛，走 error+done 兜底
            q.put((True, exc))
        else:
            q.put((True, None))

    threading.Thread(target=_produce, name="ib-sse-orchestrator", daemon=True).start()

    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise OrchestrationTimeout()
        try:
            end, payload = q.get(timeout=remaining)
        except queue.Empty:
            raise OrchestrationTimeout() from None
        if end:
            if payload is None:
                return
            raise payload
        yield payload
