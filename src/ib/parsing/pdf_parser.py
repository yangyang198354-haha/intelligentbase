"""
@module MOD-IB-05（实现细节）
@implements IFC-IB-051, IFC-IB-052 —— PDF 三路径解析器
@depends MOD-IB-01, MOD-IB-04, MOD-IB-05（包内注册表）
@author software-developer

PDF 三路径解析（module_design.md §3 MOD-IB-05 / ADR-06；AC-IB-04-05/06/07）：

  路径 1 —— **文本层**：`pypdf`（主）→ `pdfminer.six`（回退）→ `pdfplumber`（可选）
  路径 2 —— **内嵌图像 OCR**：抽取页内位图 → `OcrEngine.recognize` → `source_kind="image_ocr"`
  路径 3 —— **扫描页栅格化 + OCR**：`PageRenderer.render_page` → OCR → `source_kind="page_scan"`

**严禁 PyMuPDF（fitz）**：AGPL-3.0 传染性许可已被否决（ADR-06 / REQ-NFR-IB-12）。
本文件任何改动都不得引入它，也不得沿用「内部平台合规」口径为其开脱。

三条纪律：
  * **页级失败不升级**（AC-IB-04-07）：单页抽取/渲染/OCR 失败只记 `warnings`，
    文档仍可 indexed；只有「三种文本引擎全部缺失」这种**环境级**问题才抛异常（文档 failed）；
  * **`warnings` 不含正文**（FM-8）：只记页号与原因码；
  * **无正文时不留空 chunk**：三路径均无产出则不为该页生成块。
"""

from __future__ import annotations

from typing import Any, BinaryIO

from ib.core import ChunkingSpec, DependencyUnavailableError, ParsedChunk, ParsedDocument

__all__ = ["PdfParser", "MIN_TEXT_CHARS", "PDF_TEXT_ENGINES"]

#: 一页文本达到该字符数即认为「有文本层」，不再走 OCR 路径。
#: 阈值不可过低（页眉/页脚的水印字符会误判为「有文本」而整页跳过 OCR）。
MIN_TEXT_CHARS = 24

#: 文本层引擎优先级（主 / 回退 / 可选）。顺序即优先级，前一个失败或产出为空则尝试下一个。
PDF_TEXT_ENGINES = ("pypdf", "pdfminer", "pdfplumber")

#: 单页栅格化 DPI（扫描页 OCR 的精度/耗时折中）。
DEFAULT_RENDER_DPI = 200


class PdfParser:
    """`pdf` 解析器（IFC-IB-051~052）。"""

    ext = "pdf"

    def supports(self, ext: str) -> bool:
        return (ext or "").lower().lstrip(".") == "pdf"

    # ------------------------------------------------------------------ #
    # 主入口
    # ------------------------------------------------------------------ #

    def parse(
        self, source: BinaryIO, *, ocr: Any, renderer: Any, spec: ChunkingSpec
    ) -> ParsedDocument:
        data = source.read()
        if isinstance(data, str):  # pragma: no cover - 防御
            data = data.encode("latin-1")
        if not data.startswith(b"%PDF-"):
            # 防御：魔数校验应在 MOD-IB-13 完成；此处再拦一次，避免把非 PDF 交给引擎
            raise DependencyUnavailableError("输入不是 PDF（缺少 %PDF- 头）", dependency="pypdf")

        page_texts, page_count, engine, engine_warnings = self._extract_text_layer(data)
        warnings: list[str] = list(engine_warnings)
        if page_count <= 0:
            page_count = len(page_texts) or 1

        chunks: list[ParsedChunk] = []
        ocr_available = self._ocr_available(ocr)
        render_available = self._render_available(renderer)

        for index in range(page_count):
            text = (page_texts[index] if index < len(page_texts) else "").strip()
            page_label = f"p{index + 1}"
            locator = f"page:{index + 1}"

            if len(text) >= MIN_TEXT_CHARS:
                chunks.append(
                    ParsedChunk(
                        content=text,
                        page_or_section=page_label,
                        source_kind="text",
                        locator=locator,
                        image_ref=None,
                    )
                )
                continue

            # 路径 2：内嵌图像 OCR
            if ocr_available:
                embedded = self._page_image_texts(data, index, ocr)
                if embedded is not None:
                    chunks.append(
                        ParsedChunk(
                            content=embedded,
                            page_or_section=page_label,
                            source_kind="image_ocr",
                            locator=locator,
                            image_ref=f"{page_label}:embedded",
                        )
                    )
                    continue

            # 路径 3：整页栅格化 + OCR
            if ocr_available and render_available:
                scanned = self._page_scan_text(data, index, ocr, renderer)
                if scanned is not None:
                    chunks.append(
                        ParsedChunk(
                            content=scanned,
                            page_or_section=page_label,
                            source_kind="page_scan",
                            locator=locator,
                            image_ref=f"{page_label}:raster",
                        )
                    )
                    continue

            # 三路径均无产出：显式记录（**不含正文**，FM-8）
            if not text:
                if not ocr_available:
                    warnings.append(f"{page_label}: 无文本层且 OCR 未装配（按无文本处理）")
                elif not render_available:
                    warnings.append(f"{page_label}: 无文本层且渲染不可用（按无文本处理）")
                else:
                    warnings.append(f"{page_label}: 三路径均未产出文本（按无文本处理）")
            else:
                warnings.append(f"{page_label}: 文本层过短（{len(text)} 字符）且 OCR 未产出")

        if not chunks:
            warnings.append("全文档三路径均未产出文本（文档将 indexed 但无可检索内容）")
        return ParsedDocument(chunks=chunks, page_count=page_count, warnings=warnings)

    # ------------------------------------------------------------------ #
    # 路径 1：文本层
    # ------------------------------------------------------------------ #

    def _extract_text_layer(
        self, data: bytes
    ) -> tuple[list[str], int, str | None, list[str]]:
        """按优先级尝试文本引擎。返回 `(每页文本, 页数, 生效引擎, warnings)`。

        三种引擎**全部不可导入**时抛 `DependencyUnavailableError` —— 这是环境配置错误
        （属「文档 failed」），不是页级内容问题。
        """
        warnings: list[str] = []
        missing: list[str] = []
        for engine in PDF_TEXT_ENGINES:
            extractor = getattr(self, f"_text_via_{engine}", None)
            if extractor is None:  # pragma: no cover - 防御
                continue
            try:
                page_texts, page_count = extractor(data)
            except ImportError:
                missing.append(engine)
                continue
            except Exception as exc:  # noqa: BLE001 - 引擎级失败 -> 尝试下一个引擎
                warnings.append(f"文本引擎 {engine} 失败：{type(exc).__name__}")
                continue
            if page_count > 0:
                if engine != "pypdf":
                    warnings.append(f"文本层由回退引擎 {engine} 提供")
                return page_texts, page_count, engine, warnings
        if missing and len(missing) == len(PDF_TEXT_ENGINES):
            raise DependencyUnavailableError(
                "未安装任何 PDF 文本引擎（pypdf / pdfminer.six / pdfplumber），无法解析 PDF",
                dependency="pdf",
            )
        return [], 0, None, warnings

    def _text_via_pypdf(self, data: bytes) -> tuple[list[str], int]:
        """主引擎：`pypdf`。"""
        import io

        import pypdf  # 延迟导入

        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = list(getattr(reader, "pages", []) or [])
        texts: list[str] = []
        for page in pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001 - 单页失败留空，由上层走 OCR 路径
                texts.append("")
        return texts, len(pages)

    def _text_via_pdfminer(self, data: bytes) -> tuple[list[str], int]:
        """回退引擎：`pdfminer.six`（逐页 `PDFPage.get_pages` + `TextConverter`）。

        逐页解析（而非整篇一次）是为了**保留页边界** —— 页号是检索溯源的组成部分
        （`page_or_section` / `locator`），丢失页边界会使引用回指失真。
        """
        import io

        from pdfminer.converter import TextConverter  # 延迟导入
        from pdfminer.layout import LAParams
        from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
        from pdfminer.pdfpage import PDFPage

        page_texts: list[str] = []
        resource_manager = PDFResourceManager()
        with io.BytesIO(data) as stream:
            for page in PDFPage.get_pages(stream):
                sink = io.StringIO()
                device = TextConverter(resource_manager, sink, laparams=LAParams())
                interpreter = PDFPageInterpreter(resource_manager, device)
                try:
                    interpreter.process_page(page)
                except Exception:  # noqa: BLE001 - 单页失败留空，由上层走 OCR 路径
                    pass
                finally:
                    device.close()
                page_texts.append(sink.getvalue())
        return page_texts, len(page_texts)

    def _text_via_pdfplumber(self, data: bytes) -> tuple[list[str], int]:
        """可选引擎：`pdfplumber`。"""
        import io

        import pdfplumber  # 延迟导入

        texts: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:  # noqa: BLE001
                    texts.append("")
        return texts, len(texts)

    # ------------------------------------------------------------------ #
    # 路径 2：内嵌图像 OCR
    # ------------------------------------------------------------------ #

    def _page_image_texts(self, data: bytes, page_index: int, ocr: Any) -> str | None:
        """抽取页内位图并 OCR。无图像或未产出文本时返回 `None`（交由下一路径）。"""
        from ib.ocr import detect_image_format

        images = self._page_images(data, page_index)
        if not images:
            return None
        parts: list[str] = []
        for image in images:
            fmt = detect_image_format(image[:8])
            if fmt is None:
                continue
            try:
                text = ocr.recognize(image, fmt)
            except Exception:  # noqa: BLE001 - OCR 端口契约要求不抛；此处仍防御
                text = ""
            if text and text.strip():
                parts.append(text.strip())
        if not parts:
            return None
        return "\n".join(parts)

    def _page_images(self, data: bytes, page_index: int) -> list[bytes]:
        """经由 `pypdf` 抽取页内图像字节。失败返回空列表（页级降级）。"""
        try:
            import io

            import pypdf
        except ImportError:
            return []
        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = list(getattr(reader, "pages", []) or [])
            if page_index >= len(pages):
                return []
            page = pages[page_index]
            out: list[bytes] = []
            for image in list(getattr(page, "images", []) or []):
                payload = getattr(image, "data", None)
                if isinstance(payload, (bytes, bytearray)) and payload:
                    out.append(bytes(payload))
            return out
        except Exception:  # noqa: BLE001 - 页级降级
            return []

    # ------------------------------------------------------------------ #
    # 路径 3：扫描页栅格化 + OCR
    # ------------------------------------------------------------------ #

    def _page_scan_text(
        self, data: bytes, page_index: int, ocr: Any, renderer: Any
    ) -> str | None:
        import io

        from ib.ocr import detect_image_format

        try:
            # renderer 需要可读的 file object；每次独立构造，避免共享读位置状态
            rendered = renderer.render_page(io.BytesIO(data), page_index, DEFAULT_RENDER_DPI)
        except Exception:  # noqa: BLE001 - 端口契约要求不抛；此处仍防御
            return None
        if not rendered:
            return None
        fmt = detect_image_format(rendered[:8])
        if fmt is None:
            return None
        try:
            text = ocr.recognize(rendered, fmt)
        except Exception:  # noqa: BLE001
            return None
        if not text or not text.strip():
            return None
        return text.strip()

    # ------------------------------------------------------------------ #
    # 能力探测（一次探测，避免逐页重复 import 探测）
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ocr_available(ocr: Any) -> bool:
        try:
            return bool(ocr.available())
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def _render_available(renderer: Any) -> bool:
        try:
            return bool(renderer.available())
        except Exception:  # noqa: BLE001
            return False
