"""
@module MOD-IB-07
@implements IFC-IB-071 Chunker.split
@depends MOD-IB-01, MOD-IB-02
@author sub_agent_software_developer

切分器（module_design.md §3 MOD-IB-07）。

**纯 CPU、纯逻辑、零外部 IO** —— 属 AC-IB-15-02 的「离线可测纯逻辑单元」。
实现为**两级滑窗**：
  1. 先按解析器给出的语义边界（页 / 段落 / 标题）切段 —— 保留 `page_or_section` 溯源；
  2. 段内再按 `chunk_size` / `chunk_overlap` 滑窗 —— 保证单块不超长。

切分参数变更**不自动**作用于既有文档（AC-IB-05-03）：本模块无任何写入动作，
是否重切由 MOD-IB-14 索引重建的指纹变化决定。
"""

from __future__ import annotations

from ib.core import ChunkingSpec, ParsedChunk, ParsedDocument

__all__ = ["SlidingWindowChunker", "normalize", "split_text"]


def normalize(text: str, *, version: str = "v1") -> str:
    """文本归一化（`normalizer_version` 参与索引指纹）。

    v1 规则（刻意保守，只做**不改变语义**的规整）：
      * 统一换行符；折叠行内连续空白；压缩 3 个以上连续空行；
      * **不做**大小写折叠 / 去标点 / 词干化 —— 这些会改变语义，属检索质量调优范畴。
    """
    if version != "v1":  # 未知版本不猜测语义，直接原样返回（可被上层指纹察觉）
        return text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out_lines: list[str] = []
    blank_run = 0
    for raw_line in text.split("\n"):
        line = " ".join(raw_line.split())
        if not line:
            blank_run += 1
            if blank_run > 2:
                continue
        else:
            blank_run = 0
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """对单段文本做滑窗切分（IFC-IB-071 的内核）。

    切分点**优先落在自然边界**（换行 > 句末标点 > 空格），避免把句子劈成两半；
    找不到合适边界时才硬切。保证滑窗**始终前进**（`chunk_overlap < chunk_size` 由配置校验保证）。
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正整数")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须满足 0 <= overlap < chunk_size")
    stripped = text.strip()
    if not stripped:
        return []
    if len(stripped) <= chunk_size:
        return [stripped]

    boundaries = ("\n", "。", "！", "？", "；", ".", "!", "?", ";")
    pieces: list[str] = []
    start = 0
    total = len(stripped)
    while start < total:
        end = min(start + chunk_size, total)
        if end < total:
            # 在 [start + 60% chunk_size, end] 区间内回退到最近的自然边界
            floor = start + max(chunk_size * 3 // 5, 1)
            cut = -1
            for marker in boundaries:
                idx = stripped.rfind(marker, floor, end)
                if idx > cut:
                    cut = idx + len(marker) if marker in "。！？；.!?;" else idx + 1
            if cut > start:
                end = cut
        piece = stripped[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= total:
            break
        next_start = end - chunk_overlap
        # 防御：滑窗必须前进，否则死循环
        start = next_start if next_start > start else start + max(1, chunk_size - chunk_overlap)
    return pieces


class SlidingWindowChunker:
    """`Chunker` 端口的生产实现（IFC-IB-071）。"""

    def split(self, doc: ParsedDocument, spec: ChunkingSpec) -> list[ParsedChunk]:
        """把 `ParsedDocument` 切成最终入库块。

        * 空块 / 纯空白块被过滤（不产生「空 chunk」污染向量库）；
        * 每块的 `page_or_section` / `locator` / `source_kind` 沿用其来源段 —— 溯源不丢。
        """
        out: list[ParsedChunk] = []
        for section in doc.chunks:
            body = normalize(section.content, version=spec.normalizer_version)
            if not body:
                continue
            for piece in split_text(body, spec.chunk_size, spec.chunk_overlap):
                out.append(
                    ParsedChunk(
                        content=piece,
                        page_or_section=section.page_or_section,
                        source_kind=section.source_kind,
                        locator=section.locator,
                        image_ref=section.image_ref,
                    )
                )
        return out
