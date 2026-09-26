"""
@module MOD-IB-05（实现细节）
@implements IFC-IB-051, IFC-IB-052 —— txt / md / docx 三个解析器
@depends MOD-IB-01, MOD-IB-04, MOD-IB-05（包内注册表）
@author sub_agent_software_developer

纯文本 / Markdown / DOCX 解析器。

设计纪律：
  * **不做切分**：此处只产出「语义段」（页 / 标题节 / 段落），最终滑窗切分归 MOD-IB-07。
    这样「解析」与「切分」两个变更源解耦 —— 换切分参数不必重写解析器（AC-IB-05-03）。
  * **页级失败不升级**：单段异常只记 `warnings`，文档仍可 indexed（AC-IB-04-07）。
  * **编码探测是最小集**（utf-8 / utf-8-sig / gbk），不做 chardet 之类统计猜编码 ——
    猜测错误会静默产出乱码文本，比显式失败更糟。
"""

from __future__ import annotations

from typing import Any, BinaryIO

from ib.core import ChunkingSpec, ParsedChunk, ParsedDocument

__all__ = ["TextParser", "MarkdownParser", "DocxParser", "decode_bytes"]


#: 编码尝试顺序。GBK 放最后：它对任意字节序列的容忍度最高（最容易「猜错还不报错」）。
_ENCODINGS = ("utf-8-sig", "utf-8", "gbk")


def decode_bytes(raw: bytes) -> str:
    """按固定顺序解码；全部失败则以 `errors="replace"` 解出可读文本并保留替换字符。"""
    if not raw:
        return ""
    for encoding in _ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class TextParser:
    """`txt` 解析器：整体作为一个语义段（`page_or_section="full"`）。"""

    ext = "txt"

    def supports(self, ext: str) -> bool:
        return (ext or "").lower().lstrip(".") == "txt"

    def parse(
        self, source: BinaryIO, *, ocr: Any, renderer: Any, spec: ChunkingSpec
    ) -> ParsedDocument:
        raw = source.read()
        if isinstance(raw, str):  # pragma: no cover - 防御
            raw = raw.encode("utf-8")
        text = decode_bytes(raw)
        warnings: list[str] = []
        if not text.strip():
            warnings.append("文本为空（0 个非空白字符）")
        chunks: list[ParsedChunk] = []
        if text.strip():
            chunks.append(
                ParsedChunk(
                    content=text,
                    page_or_section="full",
                    source_kind="text",
                    locator="line:1",
                    image_ref=None,
                )
            )
        return ParsedDocument(chunks=chunks, page_count=1, warnings=warnings)


class MarkdownParser:
    """`md` 解析器：按 ATX 标题（`#`）切节，节标题进入 `page_or_section`。

    不渲染 Markdown、不剥离语法 —— 保留原文可提升检索召回（用户提问常带原文措辞），
    且避免引入 Markdown 解析依赖。
    代码围栏（``` ``` ```）内的 `#` 不视为标题（常见误判点）。
    """

    ext = "md"

    def supports(self, ext: str) -> bool:
        return (ext or "").lower().lstrip(".") in ("md", "markdown")

    def parse(
        self, source: BinaryIO, *, ocr: Any, renderer: Any, spec: ChunkingSpec
    ) -> ParsedDocument:
        raw = source.read()
        if isinstance(raw, str):  # pragma: no cover - 防御
            raw = raw.encode("utf-8")
        text = decode_bytes(raw)
        warnings: list[str] = []
        if not text.strip():
            warnings.append("文本为空（0 个非空白字符）")
            return ParsedDocument(chunks=[], page_count=1, warnings=warnings)

        lines = text.split("\n")
        sections: list[tuple[str, list[str]]] = []
        current_title = "前言"
        current_lines: list[str] = []
        in_fence = False
        heading_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                current_lines.append(line)
                continue
            if not in_fence and stripped.startswith("#"):
                # 归一化标题级别：连续 # 后跟空格或行尾
                hashes = len(stripped) - len(stripped.lstrip("#"))
                rest = stripped[hashes:]
                if hashes <= 6 and (rest == "" or rest.startswith(" ")):
                    if current_lines or sections:
                        sections.append((current_title, current_lines))
                        current_lines = []
                    heading_count += 1
                    current_title = rest.strip() or f"标题{heading_count}"
                    continue
            current_lines.append(line)
        sections.append((current_title, current_lines))

        chunks: list[ParsedChunk] = []
        for title, body_lines in sections:
            body = "\n".join(body_lines).strip()
            if not body and not title:
                continue
            chunks.append(
                ParsedChunk(
                    content=body if body else title,
                    page_or_section=title,
                    source_kind="text",
                    locator=f"section:{title}",
                    image_ref=None,
                )
            )
        if not chunks:
            warnings.append("未解析出任何非空节")
        return ParsedDocument(chunks=chunks, page_count=1, warnings=warnings)


class DocxParser:
    """`docx` 解析器：段落按「空行分块」，标题样式（Heading N）作为 `page_or_section`。

    * `python-docx` **延迟导入**；缺失 -> `DependencyUnavailableError`（**文档级 failed**，
      因为这是环境配置问题，而非页级内容问题）；
    * 表格内容按行拼接（`cell1 | cell2`），避免表格文本丢失（常见解析器缺陷）；
    * 内嵌图像**不做 OCR**：docx 内嵌图多为装饰性图表，OCR 收益不确定，
      且 `python-docx` 取图的 API 稳定性差；这是**显式的范围裁剪**，已记入 `warnings`。
    """

    ext = "docx"

    def supports(self, ext: str) -> bool:
        return (ext or "").lower().lstrip(".") == "docx"

    def parse(
        self, source: BinaryIO, *, ocr: Any, renderer: Any, spec: ChunkingSpec
    ) -> ParsedDocument:
        from ib.core import DependencyUnavailableError

        try:
            import docx  # 延迟导入：python-docx
        except ImportError as exc:
            raise DependencyUnavailableError(
                "python-docx 未安装，无法解析 docx（pip install python-docx）", dependency="python-docx"
            ) from exc

        warnings: list[str] = []
        try:
            document = docx.Document(source)
        except Exception as exc:  # noqa: BLE001 - 打开失败 = 文档不可解析，显式失败
            raise DependencyUnavailableError(
                f"docx 打开失败：{type(exc).__name__}", dependency="python-docx"
            ) from exc

        chunks: list[ParsedChunk] = []
        current_title = "正文"
        buffer: list[str] = []

        def flush() -> None:
            body = "\n".join(buffer).strip()
            buffer.clear()
            if body:
                chunks.append(
                    ParsedChunk(
                        content=body,
                        page_or_section=current_title,
                        source_kind="text",
                        locator=f"section:{current_title}",
                        image_ref=None,
                    )
                )

        for paragraph in document.paragraphs:
            text = (paragraph.text or "").strip()
            style = (getattr(paragraph.style, "name", "") or "").strip()
            is_heading = style.lower().startswith("heading") or style.startswith("标题")
            if is_heading and text:
                flush()
                current_title = text
                continue
            if not text:
                flush()  # 空段落作为分段边界
                continue
            buffer.append(text)
        flush()

        # 表格：按行拼为独立段落（保留在末尾，溯源标记为 table:N）
        for index, table in enumerate(getattr(document, "tables", []) or [], start=1):
            rows: list[str] = []
            for row in table.rows:
                cells = [(cell.text or "").strip().replace("\n", " ") for cell in row.cells]
                if any(cells):
                    rows.append(" | ".join(cells))
            body = "\n".join(rows).strip()
            if body:
                chunks.append(
                    ParsedChunk(
                        content=body,
                        page_or_section=current_title,
                        source_kind="text",
                        locator=f"table:{index}",
                        image_ref=None,
                    )
                )

        if not chunks:
            warnings.append("docx 未解析出任何非空段落")
        warnings.append("docx 内嵌图像未做 OCR（显式范围裁剪）")
        return ParsedDocument(chunks=chunks, page_count=1, warnings=warnings)
