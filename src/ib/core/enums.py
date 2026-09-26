"""
@module MOD-IB-01
@implements IFC-IB-011 (枚举: DocStatus / SourceKind / DegradeReason / RouteTier / StreamEventKind)
@depends (none)
@author sub_agent_software_developer

契约层枚举。**framework-free**：仅使用 stdlib `enum`。

全部枚举继承 `str`，因此可直接与文档/JSON 中的字符串字面量互操作
（例如 `DocStatus.PENDING == "pending"` 为真），便于 DRF Serializer 与 SQLite 存储层直接使用。

**`__str__` / `__format__` 一律返回 `value`（由 `WireStrEnum` 统一提供）**：
这是必须显式处理的坑 —— `class X(str, Enum)` 的默认 `str(X.A)` 在 Python 3.11+ 返回
`"X.A"` 而非 `"a"`，会把 `"DocStatus.PENDING"` 这类**非契约字面量**写进 SQLite /
SSE 帧 / JSON 响应，而 `==` 比较却是 True，形成「测试看起来对、落库值是错的」这类隐蔽缺陷。
"""


from __future__ import annotations

from enum import Enum


class WireStrEnum(str, Enum):
    """`str` 枚举的**线格式**基类：字符串化即取 `value`。

    统一在此处修正 `str`/`f-string`/`format()` 三种字符串化路径，避免每个调用点各写
    `.value` 而漏掉一处（漏掉即产生脏值）。
    """

    def __str__(self) -> str:
        return str(self.value)

    def __format__(self, format_spec: str) -> str:
        return format(str(self.value), format_spec)


class DocStatus(WireStrEnum):
    """文档入库状态机（module_design.md §6.1）。

    `pending -> parsing -> indexed`；任一步失败 -> `failed`（终态，需人工重试）。
    """

    PENDING = "pending"
    PARSING = "parsing"
    INDEXED = "indexed"
    FAILED = "failed"


class SourceKind(WireStrEnum):
    """切分块来源，决定溯源定位方式（page / section）。"""

    TEXT = "text"
    IMAGE_OCR = "image_ocr"
    PAGE_SCAN = "page_scan"


class DegradeReason(WireStrEnum):
    """检索降级原因（ADR-13）。

    取值使 AC-IB-13-02「仅凭日志即可定位失败依赖」成立：
    每个取值唯一对应一个失败依赖。
    """

    EMBEDDING_UNAVAILABLE = "embedding_unavailable"
    VECTORSTORE_UNAVAILABLE = "vectorstore_unavailable"
    TIMEOUT = "timeout"


class RouteTier(WireStrEnum):
    """意图路由档位（module_design.md §7.2 四级降级 + 粘性 / OOD / 默认）。"""

    KEYWORD_UNIQUE = "L0_keyword_unique"
    SEMANTIC = "L1_semantic"
    LLM = "L2_llm"
    KEYWORD_FALLBACK = "L3_keyword_fallback"
    STICKY = "sticky"
    OOD = "ood"
    DEFAULT = "default"


class StreamEventKind(WireStrEnum):
    """SSE 流事件类型（IFC-IB-224 / §7.3）。

    降级必须在流内可见（AC-IB-14-01 的界面落点）= `DEGRADED` 事件。
    """

    REASONING = "reasoning"
    CONTENT = "content"
    DEGRADED = "degraded"
    RELATED_IMAGES = "related_images"
    ERROR = "error"
    DONE = "done"


class RebuildState(WireStrEnum):
    """索引重建任务状态（MOD-IB-14）。`RebuildJob.state` 的取值域。"""

    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ACTIVATED = "activated"
    ROLLED_BACK = "rolled_back"


__all__ = [
    "WireStrEnum",
    "DocStatus",
    "SourceKind",
    "DegradeReason",
    "RouteTier",
    "StreamEventKind",
    "RebuildState",
]
