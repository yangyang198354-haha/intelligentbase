"""
@module MOD-IB-08
@implements IFC-IB-081 available / IFC-IB-082 render_page
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

页面渲染端口与 pypdfium2 适配（module_design.md §3 MOD-IB-08 / ADR-06 / ADR-12）。

**为什么渲染必须独立于 OCR**：OCR 由 `rapidocr-onnxruntime` 提供，渲染由 `pypdfium2` 提供，
二者许可与依赖完全不同；合并会把两者强绑（ADR-12 Decision）。且 `pypdf` / `pdfminer.six` /
`pdfplumber` **三个纯 Python 库都不具备渲染能力** —— 扫描页整页栅格化只能另选。

**严禁 PyMuPDF（fitz）**：AGPL-3.0 传染性，REQ-NFR-IB-12 明令否决（ADR-06）。
本模块若需改动渲染内核，只允许在上述宽松许可库中选择。
"""

from __future__ import annotations

import io
import threading
from typing import Any, BinaryIO

__all__ = ["PdfiumRenderer", "NullRenderer", "build_page_renderer", "MAX_RENDER_PIXELS"]


#: 单页栅格化像素上限（防超大页面把内存打爆）。A4@300dpi ≈ 2480x3508 ≈ 8.7M 像素。
MAX_RENDER_PIXELS = 40_000_000


class NullRenderer:
    """渲染不可用的显式替身（返回 `None`）。装配语义：扫描页路径不可用，文本层路径正常。"""

    engine_id = "null_renderer"

    def available(self) -> bool:
        return False

    def render_page(self, source: BinaryIO, page_index: int, dpi: int) -> bytes | None:
        from ib.observability import get_logger

        get_logger("render").warn("skipped", engine_id=self.engine_id, error_code="render_unavailable")
        return None


class PdfiumRenderer:
    """pypdfium2 适配（IFC-IB-081~082 的生产实现）。

    * 延迟导入 `pypdfium2`（缺失即 `available()->False`，`render_page()->None`）；
    * 每次调用**独立打开文档** —— `source` 是调用方的文件对象，渲染不得改变其读位置语义
      之外的副作用；故读取全部字节后在内存中开文档；
    * 单页渲染失败 / 超限返回 `None`（不抛异常），由 MOD-IB-05 记为页级 WARNING。
    """

    engine_id = "pypdfium2"

    def __init__(self, *, scale_dpi: int = 200) -> None:
        self._default_dpi = scale_dpi
        self._lock = threading.Lock()

    def available(self) -> bool:
        import importlib.util

        return importlib.util.find_spec("pypdfium2") is not None

    def render_page(self, source: BinaryIO, page_index: int, dpi: int) -> bytes | None:
        from ib.observability import get_logger

        log = get_logger("render")
        if page_index < 0:
            return None
        try:
            import pypdfium2 as pdfium  # 延迟导入：重依赖 + 架构相关 wheel
        except ImportError:
            log.warn("skipped", engine_id=self.engine_id, error_code="pypdfium2_missing")
            return None

        effective_dpi = dpi if dpi > 0 else self._default_dpi
        scale = effective_dpi / 72.0
        try:
            data = source.read()
            if isinstance(data, str):  # pragma: no cover - 防御
                data = data.encode("latin-1")
            with self._lock:  # pdfium 非线程安全
                pdf = pdfium.PdfDocument(io.BytesIO(data))
                try:
                    if page_index >= len(pdf):
                        return None
                    page = pdf[page_index]
                    try:
                        width = int(page.get_width() * scale)
                        height = int(page.get_height() * scale)
                        if width <= 0 or height <= 0:
                            return None
                        if width * height > MAX_RENDER_PIXELS:
                            log.warn(
                                "skipped",
                                engine_id=self.engine_id,
                                error_code="page_too_large",
                            )
                            return None
                        bitmap = page.render(scale=scale)
                        try:
                            image = bitmap.to_pil()
                            buf = io.BytesIO()
                            image.save(buf, format="PNG")
                            return buf.getvalue()
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
                finally:
                    pdf.close()
        except Exception as exc:  # noqa: BLE001 - 页级失败不得升级为文档级失败
            log.warn("failed", engine_id=self.engine_id, error_code=type(exc).__name__)
            return None

    def descriptor(self) -> Any:
        from ib.core import OcrDescriptor

        return OcrDescriptor(engine_id=self.engine_id, available=self.available())


def build_page_renderer(*, enabled: bool) -> Any:
    """按开关构造渲染器（组合根单点调用）。"""
    if not enabled:
        return NullRenderer()
    return PdfiumRenderer()
