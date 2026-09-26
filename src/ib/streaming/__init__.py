"""
@module MOD-IB-21
@implements IFC-IB-221 SessionStore.load / 222 save / 223 delete
            IFC-IB-224 StreamEvent / 225 to_sse
            IFC-IB-282（R2）`related_images` 事件的**载荷类型化**（RelatedImagesPayload）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

流式契约与会话状态（module_design.md §3 MOD-IB-21；ADR-11-R1；REQ-FUNC-IB-20/21；
AC-IB-14-01）。

## 本模块只做「事件 → 帧」的编码，**不认识 Web 框架**

`to_sse()` 产出的就是一个字符串。谁把它写进 HTTP 响应体，本模块不关心 ——
R1 里承载者是 **Django `StreamingHttpResponse`**（原生 SSE，同步 WSGI，Waitress 主 /
Gunicorn 备，**无 Channels、无 Redis**），但这一点是实现细节而非本模块契约。
好处是实测过的：若将来换框架，本模块与它的全部单测**零改动**。

## 事件类型是**对外契约**（前端逐条 switch）

`kind ∈ {reasoning, content, degraded, related_images, error, done}`。
其中 `degraded` 是**产品要求**而非技术细节（AC-IB-14-01）：检索降级必须让**用户看见**
「当前未接入知识资料库」，否则用户会把「基于通用知识的回答」误当成「查过知识库的答案」——
这是最危险的一类误导（回答看似更权威，实际依据更弱）。

## SSE 帧格式的三条纪律

1. **`event:` 一行 + `data:` 一行 + 空行**：SSE 规范以空行分隔事件；漏掉空行会让浏览器
   把多个事件合并成一个，表现为「前端只收到最后一条」。
2. **数据中的换行必须逐行加 `data:` 前缀**：SSE 的 `data:` 只覆盖**单行**，
   把含 `\n` 的 Markdown 直接塞进去会破坏帧结构，浏览器只能拿到第一行。
3. **本模块不做 JSON 包装**：`data` 是**已序列化好的字符串**，由调用方决定是 JSON 还是纯文本。
   在这里强制 JSON 会把「推理片段 / 正文 / 图片引用」这些异构载荷塞进同一个 schema，
   前端的 switch 会变得异常脆弱。

## 会话键的 fail-closed 隔离（FM-7）

`session_key` 采用 `<project_id>:<session_id>` 结构。`load()` 在键前缀与自身项目不符时
**返回 `None`**（拒绝），而不是把别的项目的会话返回给调用方。这条防线不依赖调用方传对
参数 —— 传错时得到的是「没有会话」，而不是「别人的会话」。

## `StreamEvent` 只有**一个**定义（本模块只做别名）

事件类型定义在 `ib.core`（IFC-IB-224 的契约层），本模块 `StreamEvent = ib.core.StreamEvent`
是**直接别名**。理由不是风格洁癖：两处各写一个同名类时，`isinstance(evt, ib.core.StreamEvent)`
会静默为假 —— 而契约一致性断言恰恰都是这么写的，它失效时不报错，只在将来某次重构里
才暴露「以为在检查、其实从没检查过」。别名让两种写法**恒等**，这个坑从结构上不存在。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Sequence

from ib.core import RelatedImageItem, RelatedImagesPayload, SessionState, StreamEventKind
from ib.core import StreamEvent as _CoreStreamEvent

__all__ = [
    "StreamEvent",
    "to_sse",
    "degraded_event",
    "related_images_event",
    "related_images_json",
    "related_images_of",
    "related_image_url",
    "IMAGE_ENDPOINT_TEMPLATE",
    "MemorySessionStore",
    "session_key_for",
    "project_of_session_key",
    "SSE_CONTENT_TYPE",
    "SSE_HEADERS",
    "SessionState",
]

#: 图片字节端点的**站内相对路径模板**（IFC-IB-283）。
#:
#: 放在本模块而非 MOD-IB-23，因为 `url_path` 是 `related_images` 载荷（IFC-IB-282）的字段，
#: 而载荷的出入口就在本模块；Django URLconf 用**同一字面量**注册，由自检
#: `selfcheck.py::related_images_event_contract` 断言二者一致（模板漂移会立刻失败，
#: 而不是变成「前端 404 但没人知道为什么」）。
IMAGE_ENDPOINT_TEMPLATE = "/api/files/{doc_id}/images/{image_id}"


def related_image_url(doc_id: str, image_id: str) -> str:
    """构造单张关联图的站内相对路径（**只给路径，不给字节** —— IFC-IB-282）。"""
    return IMAGE_ENDPOINT_TEMPLATE.format(doc_id=doc_id, image_id=image_id)


def related_images_json(payload: RelatedImagesPayload) -> str:
    """把载荷编码为 JSON 文本（只含 `image_id` / `url_path` 等短字段；**无 base64**）。"""
    import json

    return json.dumps(
        {
            "images": [
                {
                    "image_id": item.image_id,
                    "doc_id": item.doc_id,
                    "doc_name": item.doc_name,
                    "page_or_section": item.page_or_section,
                    "url_path": item.url_path,
                }
                for item in payload.images
            ]
        },
        ensure_ascii=False,
    )


def related_images_event(payload: RelatedImagesPayload | None) -> StreamEvent | None:
    """构造 `related_images` 事件；**无图返回 `None`**（IFC-IB-282：无图不发事件）。

    把「空即不发」这条纪律放在**构造函数**里而不是调用点：调用点散落多处时，
    「忘了判空」会发出一个空载荷事件，前端会渲染出一条空缩略图行 ——
    这类「看起来正常工作」的错误最难发现。返回 `None` 让**类型系统**替调用方把关。
    """
    if payload is None or not payload.images:
        return None
    return StreamEvent(StreamEventKind.RELATED_IMAGES, related_images_json(payload))


def related_images_of(items: Sequence[RelatedImageItem]) -> RelatedImagesPayload:
    """便捷构造：把条目列表包成载荷（保序 —— 前端**不得重排**，IFC-IB-284）。"""
    return RelatedImagesPayload(images=tuple(items))

#: SSE 响应头（`X-Accel-Buffering: no` 是**必需**的：nginx 默认缓冲整个响应体，
#: 会让流式退化成「等全部生成完再一次性下发」——看起来像卡住，实际是中间层在攒）。
SSE_CONTENT_TYPE = "text/event-stream"

SSE_HEADERS = {
    "Content-Type": SSE_CONTENT_TYPE,
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}
# 注意：**不得**在此加 `Connection` / `Keep-Alive` / `Transfer-Encoding` 等 hop-by-hop 头。
# 它们是逐跳头，按 PEP 3333 由 WSGI 服务器（Waitress/nginx）管理，应用设置会被
# Waitress 以 `AssertionError: Connection is a "hop-by-hop" header` 拒绝（生产真机复现）。
# 长连接的语义由 `--channel-timeout`（Waitress）与 `proxy_read_timeout`（nginx）负责。


#: [IFC-IB-224] **契约类型的直接别名**（不另立同名类）。
#:
#: 同名双类型是本仓最不该出现的一类缺陷：`isinstance(event, ib.core.StreamEvent)`
#: 会**静默为假**，而契约一致性检查恰好大量使用这类断言 —— 它不生效时不报错，
#: 只会在未来的重构里突然暴露「原来自以为在检查的东西从没检查过」。
#: 别名保证 `ib.streaming.StreamEvent is ib.core.StreamEvent`，两种写法永远等价。
StreamEvent = _CoreStreamEvent


def to_sse(event: StreamEvent) -> str:
    """[IFC-IB-225] 把事件编码为 SSE 帧（`event:` / `data:` 逐行 + 结尾空行）。"""
    lines = [f"event: {event.kind}"]
    payload = event.data if event.data is not None else ""
    if payload == "":
        lines.append("data:")
    else:
        # 逐行加前缀 —— 单行 `data:` 承载不了多行内容（见模块文档纪律 2）
        for line in payload.split("\n"):
            lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def session_key_for(project_id: str, session_id: str) -> str:
    """构造带项目前缀的会话键。

    `project_id` 必须非空 —— 空项目前缀会让所有项目的会话挤进同一命名空间，
    隔离防线随之失效（而且是**静默**失效：一切照常工作，只是不再隔离）。
    """
    if not project_id:
        raise ValueError("project_id 不得为空（会话键必须带项目前缀以维持隔离）")
    if not session_id:
        raise ValueError("session_id 不得为空")
    if ":" in project_id:
        raise ValueError("project_id 不得含 ':'（会破坏键前缀解析）")
    return f"{project_id}:{session_id}"


def project_of_session_key(session_key: str) -> str:
    """从会话键取出项目前缀；格式非法返回 `""`（调用方据此拒绝，而不是猜测）。"""
    if not session_key or ":" not in session_key:
        return ""
    return session_key.split(":", 1)[0]


class MemorySessionStore:
    """进程内会话状态（IFC-IB-221~223；`IB_SESSION_BACKEND=memory`）。

    **生产默认就是它**（模块文档明列「内存实现即替身」）：v1 的目标是单实例部署，
    引入外部会话存储会带来一个与知识库无关的新故障面（且会话丢失只是「粘性失效」，
    不影响正确性）。代价是**重启即失忆**，这是有意识的取舍，不是遗漏。

    三条实现纪律：
      * **线程安全**：WSGI 多线程下并发请求会同时读写同一会话；
      * **按项目隔离**（FM-7）：键前缀不符 → 拒绝（返回 `None` / 静默丢弃）；
      * **条数上限 + 空闲回收**：内存会话若不设上限，长期运行必然缓慢泄漏
        （表现为「跑了两周后内存不降」）。上限策略是**按最后访问时间淘汰最旧的**，
        因为「最近聊过的会话」被再次打开的概率远高于陈旧会话。
    """

    def __init__(self, *, max_sessions: int = 2000, idle_ttl_s: float = 24 * 3600) -> None:
        self._lock = threading.RLock()
        #: session_key -> (state, last_access_ts)
        self._items: dict[str, tuple[SessionState, float]] = {}
        self._max_sessions = max(1, int(max_sessions))
        self._idle_ttl_s = float(idle_ttl_s)

    # --- 端口方法 --- #

    def load(self, session_key: str) -> SessionState | None:
        """[IFC-IB-221] 读取；键前缀与项目不符 → **拒绝**（返回 `None`，FM-7）。"""
        if not project_of_session_key(session_key):
            return None
        with self._lock:
            self._evict_locked()
            item = self._items.get(session_key)
            if item is None:
                return None
            state, _ = item
            self._items[session_key] = (state, time.time())
            # 返回**浅拷贝**的消息列表：调用方对返回列表的 append 不应写回存储
            return SessionState(
                messages=list(state.messages),
                last_expert=state.last_expert,
                sticky_turns_left=state.sticky_turns_left,
            )

    def save(self, session_key: str, state: SessionState) -> None:
        """[IFC-IB-222] 写入。键非法即**静默丢弃**（不抛异常 —— 会话持久化失败不该打断问答）。"""
        if not project_of_session_key(session_key) or state is None:
            return
        with self._lock:
            self._items[session_key] = (state, time.time())
            self._evict_locked()

    def delete(self, session_key: str) -> None:
        """[IFC-IB-223] 删除（幂等）。"""
        with self._lock:
            self._items.pop(session_key, None)

    # --- 运维辅助（非端口方法） --- #

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    # --- 内部 --- #

    def _evict_locked(self) -> None:
        """淘汰：先按空闲超时清理，再按最旧访问时间压到上限之内（**必须在持锁时调用**）。"""
        now = time.time()
        if self._idle_ttl_s > 0:
            for key in [k for k, (_, ts) in self._items.items() if now - ts > self._idle_ttl_s]:
                self._items.pop(key, None)
        overflow = len(self._items) - self._max_sessions
        if overflow > 0:
            oldest = sorted(self._items.items(), key=lambda item: item[1][1])[:overflow]
            for key, _ in oldest:
                self._items.pop(key, None)


def degraded_event(reason: Any, *, hint: str = "") -> StreamEvent:
    """构造 `degraded` 事件的便捷入口（AC-IB-14-01：降级必须对用户可见）。

    `data` 形如 `{"reason": "vectorstore_unavailable", "hint": "..."}`，
    但**只输出已序列化文本**，本模块不引入 JSON 编码职责。
    """
    import json

    return StreamEvent(
        StreamEventKind.DEGRADED,
        json.dumps({"reason": str(reason), "hint": hint or ""}, ensure_ascii=False),
    )
