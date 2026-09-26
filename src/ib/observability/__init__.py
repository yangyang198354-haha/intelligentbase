"""
@module MOD-IB-04
@implements IFC-IB-041 get_logger / IFC-IB-042 log_event / IFC-IB-043 Timer
            IFC-IB-044 emit_degrade / IFC-IB-045 redact
@depends MOD-IB-01
@author sub_agent_software_developer

可观测性（module_design.md §3 MOD-IB-04 / architecture §7.2）。

**字段白名单 + 脱敏（FM-8）是本模块存在的核心理由**：日志里出现文档正文、
检索片段原文或凭据，就是一次不可撤回的泄漏。因此：

  * `log_event()` 只接受 `LOG_FIELDS` 白名单内的命名参数 —— 想写别的东西**写不进去**；
  * `redact()` 对任意 dict 做白名单过滤 + 敏感键名模式屏蔽，供异常路径兜底调用；
  * `Timer` 输出 `elapsed_ms`，使 AC-IB-13-02「仅凭日志定位失败依赖」成立。

日志级别经环境变量可调（AC-IB-13-03），且**不经 Django LOGGING 配置**作为唯一来源
（tech_stack §1：保持本模块为单一落点）。
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any, Callable, Iterable, Iterator, Mapping

from ib.core import DegradeReason

__all__ = [
    "LOG_FIELDS",
    "SENSITIVE_KEY_PATTERNS",
    "StructuredLogger",
    "Timer",
    "get_logger",
    "log_event",
    "emit_degrade",
    "redact",
    "add_degrade_sink",
    "remove_degrade_sink",
    "degrade_scope",
    "configure_logging",
    "REDACTED",
]

#: 允许进入日志的字段白名单（architecture §7.2 + FM-8）。
#: 注意：**没有** `content` / `text` / `chunk` / `query` / `payload` / `api_key` 等键 —— 这是刻意的。
LOG_FIELDS: frozenset[str] = frozenset(
    {
        "request_id",
        "project_id",
        "kb_id",
        "doc_id",
        "doc_name",
        "stage",
        "outcome",
        "elapsed_ms",
        "error_code",
        "degrade_reason",
        "status",
        "count",
        "score",
        "model_id",
        "dim",
        "collection",
        "tier",
        "kind",
        "engine_id",
        "available",
        "level",
        "worker",
        "version",
        "leases_reaped",
        "vectors",
        "blob",
        "size_bytes",
        # --- 外发边界声明专用三键（IFC-IB-215 / NFR-08）---
        # 为什么必须新增：`EgressDescriptor` 要求「输出至启动日志与 /healthz/deps」，
        # 而白名单之外的一切键都会被**静默丢弃**。实测发现的失败形态：首个版本的启动钩子
        # 打了 `egress_remote` / `egress_host`，两个键都不在白名单内 —— 日志行里字段凭空消失
        # 且不报任何错，需求（「外发行为在配置层可追溯」）就此悄悄落空。
        # 只新增三个**精确键名**（而非放宽匹配规则），且 data_categories 由调用方拼成
        # 单个短字符串传入 —— 不引入任何可用于输出任意正文的通道。
        "egress_remote",
        "egress_host",
        "egress_data",
        # 装配后端摘要（`vectorstore=memory,embed=fake,...`）。
        # 同样是「实测才发现被丢弃」的键：不带它，排障时无法从一行日志看出**当前生效的
        # 是哪个后端** —— 而「以为在连 Qdrant，其实跑在内存替身」是最难发现的一类事故。
        # 与 `kind` / `stage` / `status` 同级的短标签，值上限仍由 redact 的 120 字符截断兜底。
        "backend",
    }
)

#: 敏感键名模式 —— 命中即整体替换为 `[REDACTED]`（不做部分掩码，避免格式暗示长度）。
SENSITIVE_KEY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"api[_-]?key",
        r"secret",
        r"token",
        r"passw(or)?d",
        r"credential",
        r"\bauth\b",
        r"private[_-]?key",
        r"session[_-]?id",
        r"\bcontent\b",
        r"\btext\b",
        r"\bchunk[s]?\b",
        r"\bquery\b",
        r"\bprompt\b",
        r"\bpayload\b",
        r"\banswer\b",
    )
)

REDACTED = "[REDACTED]"

_DEGRADE_SINKS: list[Callable[[DegradeReason, str], None]] = []
_SINKS_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# 脱敏（IFC-IB-045）
# --------------------------------------------------------------------------- #


def redact(fields: Mapping[str, Any]) -> dict[str, Any]:
    """对任意 dict 做**白名单 + 键名模式**双重过滤（IFC-IB-045）。

    语义：**默认丢弃**。键不在白名单内 -> 丢弃；键命中敏感模式 -> 换成 `[REDACTED]`；
    白名单内的值只保留标量与短字符串（长字符串截断，避免正文借 `doc_name` 之名溜进来）。
    """
    out: dict[str, Any] = {}
    for key, value in fields.items():
        name = str(key)
        if any(p.search(name) for p in SENSITIVE_KEY_PATTERNS):
            out[name] = REDACTED
            continue
        if name not in LOG_FIELDS:
            continue
        if isinstance(value, str):
            out[name] = value if len(value) <= 120 else value[:117] + "..."
        elif value is None or isinstance(value, (int, float, bool)):
            out[name] = value
        elif isinstance(value, Iterable):
            out[name] = f"<{type(value).__name__} len={len(list(value))}>"  # type: ignore[arg-type]
        else:
            out[name] = f"<{type(value).__name__}>"
    return out


# --------------------------------------------------------------------------- #
# 结构化日志（IFC-IB-041 / 042）
# --------------------------------------------------------------------------- #

_LOGGER_NAME = "intelligentbase"


def configure_logging(level: str = "INFO", *, json_lines: bool = True) -> None:
    """初始化基础 logger（幂等）。级别可被 `IB_LOG_LEVEL` 覆盖（AC-IB-13-03）。"""
    env_level = os.environ.get("IB_LOG_LEVEL")
    effective = (env_level or level or "INFO").upper()
    root = logging.getLogger(_LOGGER_NAME)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(message)s") if json_lines else logging.Formatter("%(asctime)s %(message)s")
        )
        root.addHandler(handler)
    root.setLevel(getattr(logging, effective, logging.INFO))
    root.propagate = False


class StructuredLogger:
    """结构化日志器（IFC-IB-041）。

    每次输出一行 JSON（`json_lines=True`），**只含白名单字段**。
    """

    def __init__(self, stage: str, *, json_lines: bool = True) -> None:
        self.stage = stage
        self.json_lines = json_lines
        self._log = logging.getLogger(f"{_LOGGER_NAME}.{stage}")

    def event(self, outcome: str, **fields: Any) -> None:
        """打点（IFC-IB-042 的实现体）。

        `**fields` 里凡不在白名单 / 命中敏感模式的键，都会被 `redact()` 丢弃或屏蔽 ——
        调用方**无法**意外把正文写进日志。
        """
        payload = redact({"stage": self.stage, "outcome": outcome, **fields})
        level = _level_for(outcome, payload)
        message = json.dumps(payload, ensure_ascii=False, sort_keys=True) if self.json_lines else str(payload)
        self._log.log(level, message)

    # 便捷方法
    def debug(self, outcome: str, **fields: Any) -> None:
        self.event(outcome, **fields)

    def info(self, outcome: str, **fields: Any) -> None:
        self.event(outcome, **fields)

    def warn(self, outcome: str, **fields: Any) -> None:
        self.event(outcome, **{**fields, "level": "WARN"})

    def error(self, outcome: str, **fields: Any) -> None:
        self.event(outcome, **{**fields, "level": "ERROR"})


def _level_for(outcome: str, payload: Mapping[str, Any]) -> int:
    """由 outcome / 显式 level / degrade_reason 推断日志级别。"""
    explicit = str(payload.get("level", "")).upper()
    if explicit in ("ERROR", "WARN", "WARNING", "INFO", "DEBUG"):
        return getattr(logging, "WARNING" if explicit == "WARN" else explicit)
    if outcome in ("failed", "error", "unavailable", "startup_failed"):
        return logging.ERROR
    if payload.get("degrade_reason"):
        return logging.WARNING
    if outcome in ("degraded", "skipped", "warned", "missing"):
        return logging.WARNING
    return logging.INFO


def get_logger(stage: str) -> StructuredLogger:
    """取某阶段的日志器（IFC-IB-041）。"""
    return StructuredLogger(stage)


def log_event(
    stage: str,
    outcome: str,
    *,
    project_id: str | None = None,
    kb_id: str | None = None,
    doc_id: str | None = None,
    elapsed_ms: int | None = None,
    error_code: str | None = None,
    degrade_reason: DegradeReason | None = None,
    **extra: Any,
) -> None:
    """模块级打点函数（IFC-IB-042），签名与 module_design 一致。

    额外字段经 `**extra` 传入，仍受白名单约束。
    """
    fields: dict[str, Any] = {}
    for key, value in (
        ("project_id", project_id),
        ("kb_id", kb_id),
        ("doc_id", doc_id),
        ("elapsed_ms", elapsed_ms),
        ("error_code", error_code),
        ("degrade_reason", degrade_reason.value if isinstance(degrade_reason, DegradeReason) else degrade_reason),
    ):
        if value is not None:
            fields[key] = value
    fields.update(extra)
    get_logger(stage).event(outcome, **fields)


# --------------------------------------------------------------------------- #
# 计时（IFC-IB-043）
# --------------------------------------------------------------------------- #


class Timer:
    """上下文管理式计时（IFC-IB-043）。产出整数毫秒，**不含任何正文**。"""

    __slots__ = ("_started", "elapsed_ms")

    def __init__(self) -> None:
        self._started: float = 0.0
        self.elapsed_ms: int = 0

    def __enter__(self) -> "Timer":
        self._started = time.perf_counter()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()

    def stop(self) -> int:
        if self._started:
            self.elapsed_ms = int((time.perf_counter() - self._started) * 1000)
            self._started = 0.0
        return self.elapsed_ms


def timed(fn: Callable[..., Any]) -> Callable[..., Any]:
    """装饰器形式：把耗时写入 `fn.__last_elapsed_ms__`（仅供自测与诊断）。"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        timer = Timer()
        with timer:
            result = wrapper.__wrapped__(*args, **kwargs)  # type: ignore[attr-defined]
        wrapper.__last_elapsed_ms__ = timer.elapsed_ms  # type: ignore[attr-defined]
        return result

    wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
    wrapper.__last_elapsed_ms__ = 0  # type: ignore[attr-defined]
    return wrapper


# --------------------------------------------------------------------------- #
# 降级事件（IFC-IB-044）—— 使「降级在流内可见」成为结构性能力
# --------------------------------------------------------------------------- #


def emit_degrade(reason: DegradeReason | str, *, stage: str) -> None:
    """发射降级事件（IFC-IB-044）。

    两件事：① 写一条含 `degrade_reason` 的 WARN 日志（留痕，AC-IB-13-01）；
    ② 通知已注册的 sink —— SSE 层借此把降级**转成流内 `degraded` 事件**（AC-IB-14-01）。
    """
    value = reason.value if isinstance(reason, DegradeReason) else str(reason)
    get_logger(stage).event("degraded", degrade_reason=value)
    with _SINKS_LOCK:
        sinks = tuple(_DEGRADE_SINKS)
    for sink in sinks:
        try:
            sink(DegradeReason(value) if value in DegradeReason._value2member_map_ else DegradeReason.EMBEDDING_UNAVAILABLE, stage)
        except Exception:  # noqa: BLE001 - sink 故障绝不影响主流程
            continue


def add_degrade_sink(sink: Callable[[DegradeReason, str], None]) -> None:
    """注册降级事件接收器（SSE 流装配期调用）。"""
    with _SINKS_LOCK:
        if sink not in _DEGRADE_SINKS:
            _DEGRADE_SINKS.append(sink)


def remove_degrade_sink(sink: Callable[[DegradeReason, str], None]) -> None:
    """注销降级事件接收器（流结束必调，避免 sink 泄漏）。"""
    with _SINKS_LOCK:
        try:
            _DEGRADE_SINKS.remove(sink)
        except ValueError:
            pass


class degrade_scope:
    """上下文管理器：在 `with` 块内把降级事件收集到列表（SSE 层用法）。

        with degrade_scope() as events:
            ...
        # events: list[tuple[DegradeReason, str]]
    """

    def __init__(self) -> None:
        self.events: list[tuple[DegradeReason, str]] = []

    def _sink(self, reason: DegradeReason, stage: str) -> None:
        self.events.append((reason, stage))

    def __enter__(self) -> list[tuple[DegradeReason, str]]:
        add_degrade_sink(self._sink)
        return self.events

    def __exit__(self, *exc_info: Any) -> None:
        remove_degrade_sink(self._sink)


def iter_redacted(fields: Mapping[str, Any]) -> Iterator[tuple[str, Any]]:
    """便利函数：以 `(key, value)` 迭代脱敏结果（不改变语义，仅便于测试断言）。"""
    yield from redact(fields).items()
