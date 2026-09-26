"""
@module MOD-IB-05
@implements IFC-IB-051 DocumentParser.supports / IFC-IB-052 DocumentParser.parse
            IFC-IB-053 registry.register（**新增格式不改主动线**）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

解析器注册表与格式分派（module_design.md §3 MOD-IB-05 / ADR-06 / ADR-12）。

**开放-封闭**（AC-IB-04-05）：新增格式只需 `registry.register(ext, parser)`，
生命周期（MOD-IB-13）、切分（MOD-IB-07）、入库管线（MOD-IB-13）**零改动**。

**OCR / 渲染以参数注入**（`parse(source, *, ocr, renderer, spec)`），
本模块**不静态依赖** MOD-IB-06 / MOD-IB-08 —— 这是 §4.2 单向铁律中「跨层反向依赖通过端口注入
解决」的具体落点：L1 的解析器需要 L2 的 OCR，但不能形成 05 → 06 的依赖边。

**魔数签名探测**同时是 MOD-IB-13 三重校验（IFC-IB-141）的第三步，故本模块导出
`sniff_magic()` 作为**唯一**签名判定实现，避免两处各写一份判定而漂移。
"""

from __future__ import annotations

import codecs
from typing import Any, BinaryIO

from ib.config import SUPPORTED_EXTS
from ib.core import ChunkingSpec, ParsedDocument

__all__ = [
    "SUPPORTED_EXTS",
    "ParserRegistry",
    "default_registry",
    "sniff_magic",
    "ext_of",
    "RegexFallbackParser",
]

# --------------------------------------------------------------------------- #
# 魔数（签名）—— 「不信任扩展名」的唯一判定实现
# --------------------------------------------------------------------------- #

#: `%PDF-`：PDF 文件头。
MAGIC_PDF = b"%PDF-"
#: `PK\x03\x04`：ZIP 容器（OOXML / docx 的基础容器）。
MAGIC_ZIP = b"PK\x03\x04"

#: 文本系扩展名（无固定魔数，按「可否解码为文本」判定）。
_TEXT_EXTS = ("txt", "md")


def ext_of(filename: str) -> str:
    """从文件名取规范化扩展名（小写、无点）。无扩展名返回 `""`。"""
    _, dot, ext = (filename or "").rpartition(".")
    if not dot:
        return ""
    return ext.strip().lower()


def _decodes_as(head: bytes, encoding: str) -> bool:
    """判断 `head` 是否为 `encoding` 的**合法前缀**（允许末字节不完整）。

    为什么必须用增量解码器（`final=False`）而不是 `head.decode(encoding)`：
    `head` 是被**定长截断**的片头，末字节极可能落在多字节字符中间。中文在 UTF-8 下
    占 3 字节，256 字节截断几乎必然切在字符内部 —— 用严格整体解码会把
    **完全合法的中文文本**判为「内容与扩展名不符」（真实缺陷，见 code_review CRITICAL-01）。
    增量解码器遇到末尾不完整序列会**缓存而非报错**，只在遇到真正非法的字节序列时抛错。
    """
    decoder = codecs.getincrementaldecoder(encoding)("strict")
    try:
        decoder.decode(head, False)
    except UnicodeDecodeError:
        return False
    return True


def sniff_magic(head: bytes, ext: str) -> str | None:
    """按魔数判定 `head` 是否符合 `ext` 的容器特征（IFC-IB-141 第三步）。

    返回：
      * 探测到的格式标识（`"pdf"` / `"docx"` / `"text"`）—— 校验通过；
      * `None` —— 校验**不通过**（扩展名与真实内容不符）。

    **为什么必须做第三步**：仅凭扩展名/Filename 判定会放行「改名攻击」
    （如把 exe/zip 改名为 .pdf），进而在后续解析路径中触发非预期的解析器分支（FM 类风险）。
    文本系（txt/md）无固定魔数，改判「不含 NUL 字节且可按 UTF-8/GBK 解码」——
    这仍是**内容判定**，不是扩展名信任。
    """
    ext = (ext or "").lower()
    if ext == "pdf":
        return "pdf" if head.startswith(MAGIC_PDF) else None
    if ext == "docx":
        # 更严格：OOXML 的 docx 必须在 ZIP 容器中的 [Content_Types].xml 声明 word 类型。
        # 此处只做「ZIP 容器」层判定（不解压，避免 zip bomb 风险），
        # 深度判定交由 `DocxParser.parse` 在 python-docx 打开失败时给出文档级 failed。
        return "docx" if head.startswith(MAGIC_ZIP) else None
    if ext in _TEXT_EXTS:
        if b"\x00" in head:
            return None
        # UTF-8 优先，退 GBK —— 两者都用「合法前缀」判定（见 `_decodes_as`）
        if _decodes_as(head, "utf-8") or _decodes_as(head, "gbk"):
            return "text"
        return None
    return None


# --------------------------------------------------------------------------- #
# 注册表（IFC-IB-053）
# --------------------------------------------------------------------------- #


class ParserRegistry:
    """扩展名 -> `DocumentParser` 的分派表。

    * 注册是**幂等覆盖**（同扩展名重复注册以最后一次为准），便于测试替换与灰度；
    * `supports()` 反映注册结果，而非硬编码扩展名清单 —— 故新增格式不触碰本类；
    * `parse()` 是生命周期（MOD-IB-13）的**唯一**解析入口，OCR/渲染在此处注入。
    """

    def __init__(self) -> None:
        self._parsers: dict[str, Any] = {}

    def register(self, ext: str, parser: Any) -> None:
        """注册解析器（IFC-IB-053）。`ext` 归一化：小写、去点、去空白。"""
        key = (ext or "").strip().lower().lstrip(".")
        if not key:
            raise ValueError("注册解析器时 ext 不得为空")
        self._parsers[key] = parser

    def unregister(self, ext: str) -> None:
        self._parsers.pop((ext or "").strip().lower().lstrip("."), None)

    def supports(self, ext: str) -> bool:
        """IFC-IB-051（注册表层）。"""
        return (ext or "").strip().lower().lstrip(".") in self._parsers

    def extensions(self) -> tuple[str, ...]:
        return tuple(sorted(self._parsers))

    def parser_for(self, ext: str) -> Any | None:
        return self._parsers.get((ext or "").strip().lower().lstrip("."))

    def parse(
        self,
        ext: str,
        source: BinaryIO,
        *,
        ocr: Any,
        renderer: Any,
        spec: ChunkingSpec,
    ) -> ParsedDocument:
        """IFC-IB-052 的分派入口。未注册的扩展名 -> `ValueError`（不猜测、不静默返回空）。"""
        parser = self.parser_for(ext)
        if parser is None:
            raise ValueError(
                f"未注册的扩展名：{ext!r}（已注册：{', '.join(self.extensions()) or '无'}）"
            )
        return parser.parse(source, ocr=ocr, renderer=renderer, spec=spec)


class RegexFallbackParser:
    """**最后兜底**解析器（无扩展名 / 未知扩展名的纯文本内容）。

    仅当调用方**明确**选择装配它时才生效（默认注册表**不注册**它）——
    否则「静默兜底」会掩盖「格式不支持」这一必须显式反馈的事实。
    """

    ext = ""

    def supports(self, ext: str) -> bool:
        return True

    def parse(
        self, source: BinaryIO, *, ocr: Any, renderer: Any, spec: ChunkingSpec
    ) -> ParsedDocument:
        from ib.parsing.text_parsers import decode_bytes

        raw = source.read()
        if isinstance(raw, str):  # pragma: no cover - 防御
            raw = raw.encode("utf-8")
        text = decode_bytes(raw)
        chunks = []
        if text.strip():
            from ib.core import ParsedChunk

            chunks.append(
                ParsedChunk(
                    content=text,
                    page_or_section="full",
                    source_kind="text",
                    locator="line:1",
                    image_ref=None,
                )
            )
        return ParsedDocument(chunks=chunks, page_count=1, warnings=["使用兜底解析器（按纯文本处理）"])


# --------------------------------------------------------------------------- #
# 默认注册表（组合根与自测共用的**唯一**构造点）
# --------------------------------------------------------------------------- #


def build_default_registry(*, include_fallback: bool = False) -> ParserRegistry:
    """构造内置四格式解析器（OQ-IB-02 采纳默认：pdf / docx / md / txt）。

    延迟导入具体解析器实现（`text_parsers` / `pdf_parser`），使解析器实现内部的
    第三方库仍保持惰性 —— 本函数本身**不导入任何第三方库**。
    """
    from ib.parsing.pdf_parser import PdfParser
    from ib.parsing.text_parsers import DocxParser, MarkdownParser, TextParser

    registry = ParserRegistry()
    if "txt" in SUPPORTED_EXTS:
        registry.register("txt", TextParser())
    if "md" in SUPPORTED_EXTS:
        registry.register("md", MarkdownParser())
    if "docx" in SUPPORTED_EXTS:
        registry.register("docx", DocxParser())
    if "pdf" in SUPPORTED_EXTS:
        registry.register("pdf", PdfParser())
    if include_fallback:
        registry.register("", RegexFallbackParser())
    return registry


#: 模块级默认注册表 —— 生命周期与组合根共用（**避免多处各建一份而分派不一致**）。
default_registry = build_default_registry()
