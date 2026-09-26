"""
@module MOD-IB-06
@implements IFC-IB-061 available / IFC-IB-062 recognize / IFC-IB-063 descriptor
            IFC-IB-064 NullOcrEngine
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author software-developer

OCR 端口与适配（module_design.md §3 MOD-IB-06 / ADR-12）。

**降级是显式装配选择，而非散落的异常捕获**（ADR-12 Decision）：
  * 引擎可用 -> `RapidOcrEngine`；
  * 引擎不可用 / 功能关闭 -> 装配 `NullOcrEngine`，其 `recognize()` 返回 `""` 并记 WARNING，
    扫描页按「无文本」处理，**文档仍可 indexed**（AC-IB-04-07）。

`rapidocr-onnxruntime` 与 `onnxruntime` 一律**延迟导入** —— 缺失时不影响本模块可导入性。
"""

from __future__ import annotations

import threading
from typing import Any

from ib.core import DependencyUnavailableError, OcrDescriptor

__all__ = ["RapidOcrEngine", "NullOcrEngine", "StubOcrEngine", "detect_image_format"]

#: 图像魔数（与 MOD-IB-13 的 `_detect_image_format` 同一套探测逻辑，ADR 参考 FreeArk 模式）。
_MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
_MAGIC_JPEG = b"\xff\xd8\xff"


def detect_image_format(head: bytes) -> str | None:
    """按魔数探测图像格式（不信任扩展名）。返回 `"png"` / `"jpeg"` / `None`。"""
    if head.startswith(_MAGIC_PNG):
        return "png"
    if head.startswith(_MAGIC_JPEG):
        return "jpeg"
    return None


class NullOcrEngine:
    """不可用 OCR 的显式替身（IFC-IB-064）。

    `available() -> False`，`recognize() -> ""`，并记录 WARNING。
    装配它的语义是「本机没有 OCR，扫描页按无文本处理」—— 这是**被设计的降级路径**。
    """

    engine_id = "null_ocr"

    def __init__(self, *, reason: str = "OCR 引擎未装配（IB_OCR_ENABLED=false 或依赖缺失）") -> None:
        self._reason = reason
        self._warned = False

    def available(self) -> bool:
        return False

    def recognize(self, image: bytes, fmt: str) -> str:
        if not self._warned:
            from ib.observability import get_logger

            get_logger("ocr").warn("skipped", engine_id=self.engine_id, error_code="ocr_unavailable")
            self._warned = True
        return ""

    def descriptor(self) -> OcrDescriptor:
        return OcrDescriptor(engine_id=self.engine_id, available=False)


class StubOcrEngine:
    """**仅供测试**：返回固定文本，用于验证「OCR 路径被走到」。

    命名上刻意与 `NullOcrEngine` 区分，避免被误装配到生产（ADR-12）。
    """

    engine_id = "stub_ocr"

    def __init__(self, text: str = "stub-ocr-text") -> None:
        self._text = text

    def available(self) -> bool:
        return True

    def recognize(self, image: bytes, fmt: str) -> str:
        return self._text

    def descriptor(self) -> OcrDescriptor:
        return OcrDescriptor(engine_id=self.engine_id, available=True)


class RapidOcrEngine:
    """RapidOCR 适配（IFC-IB-061~063 的生产实现；ADR-12）。

    * **懒加载单例**：首次 `recognize()` 才加载权重（避免启动即吃内存，[TBD-T3]/[TBD-T4']）；
    * `available()` 只探测「可导入」与「已加载」两态，**不触发**权重加载；
    * 单张图失败**不抛异常**，记 WARNING 返回 `""` —— 页级失败不得升级为文档级失败（AC-IB-04-07）。
    """

    engine_id = "rapidocr_onnxruntime"

    def __init__(self, *, min_confidence: float = 0.5, thread_safe: bool = True) -> None:
        self._engine: Any = None
        self._import_error: str | None = None
        self._lock = threading.Lock() if thread_safe else None
        self._min_confidence = min_confidence

    def _load(self) -> Any:
        if self._engine is not None:
            return self._engine
        if self._lock is not None:
            with self._lock:
                if self._engine is None:
                    self._engine = self._do_load()
        else:  # pragma: no cover - 非线程安全分支
            self._engine = self._do_load()
        return self._engine

    def _do_load(self) -> Any:
        try:
            from rapidocr_onnxruntime import RapidOCR  # 延迟导入：重依赖
        except ImportError as exc:
            self._import_error = str(exc)
            raise DependencyUnavailableError(
                "rapidocr-onnxruntime 未安装，无法提供 OCR", dependency="rapidocr"
            ) from exc
        return RapidOCR()

    def available(self) -> bool:
        """可用性探测：已加载，或可导入。**不加载权重**。"""
        if self._engine is not None:
            return True
        if self._import_error is not None:
            return False
        import importlib.util

        return importlib.util.find_spec("rapidocr_onnxruntime") is not None

    def recognize(self, image: bytes, fmt: str) -> str:
        """图像 -> 文本。任何失败一律降级为空串 + WARNING（不抛异常）。"""
        from ib.observability import get_logger

        log = get_logger("ocr")
        if not image:
            return ""
        try:
            engine = self._load()
        except DependencyUnavailableError:
            log.warn("skipped", engine_id=self.engine_id, error_code="ocr_unavailable")
            return ""
        try:
            result, _elapse = engine(image)
        except Exception as exc:  # noqa: BLE001 - 单图失败不得升级
            log.warn("failed", engine_id=self.engine_id, error_code=type(exc).__name__)
            return ""
        if not result:
            return ""
        lines: list[str] = []
        for item in result:
            # RapidOCR 返回 [(box, text, score), ...]
            try:
                _box, text, score = item[0], item[1], item[2]
            except (IndexError, TypeError):
                continue
            if score is not None and float(score) < self._min_confidence:
                continue
            if text:
                lines.append(str(text).strip())
        return "\n".join(line for line in lines if line)

    def descriptor(self) -> OcrDescriptor:
        return OcrDescriptor(engine_id=self.engine_id, available=self.available())


def build_ocr_engine(*, enabled: bool) -> Any:
    """按开关构造 OCR 引擎（组合根单点调用）。

    `enabled=True` 但依赖缺失时，**仍返回 `RapidOcrEngine`**（其 `available()` 为 False，
    `recognize()` 自降级），以便启动期能如实报告「已配置但不可用」的差异。
    """
    if not enabled:
        return NullOcrEngine(reason="IB_OCR_ENABLED=false")
    return RapidOcrEngine()
