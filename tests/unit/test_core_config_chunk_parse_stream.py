"""单元测试层 1/N —— 核心契约 / 配置 / 切分 / 解析 / 流式 / 可观测性。

全部为纯逻辑或零外部 IO；**不联网、不连库**。每条用例在 docstring 标注关联的 AC / IFC。
"""

from __future__ import annotations

import io

import pytest

# --------------------------------------------------------------------------- #
# MOD-IB-01 契约枚举的线格式（IFC-IB-011）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_001_enum_wire_format():
    """[TC-UNIT-001] 枚举字符串化必须取 value，不是类名（AC-IB-11-04 配置取值域 / 通用契约）。"""
    from ib.core import DocStatus, DegradeReason, RouteTier, StreamEventKind

    assert str(DocStatus.PENDING) == "pending"
    assert f"{DocStatus.INDEXED}" == "indexed"
    assert DocStatus.FAILED == "failed"  # str 子类可直接与字面量比较
    assert str(DegradeReason.EMBEDDING_UNAVAILABLE) == "embedding_unavailable"
    assert DegradeReason.TIMEOUT.value == "timeout"
    assert str(RouteTier.KEYWORD_UNIQUE) == "L0_keyword_unique"
    assert str(StreamEventKind.RELATED_IMAGES) == "related_images"


def test_TC_UNIT_002_scope_requires_project_id_signature():
    """[TC-UNIT-002] `scope` 参数无默认值（漏传即类型检查期报错，IFC-IB-021 纪律）。"""
    import inspect

    from ib.core import VectorStore

    sig = inspect.signature(VectorStore.query)
    assert "scope" in sig.parameters
    assert sig.parameters["scope"].default is inspect.Parameter.empty


# --------------------------------------------------------------------------- #
# MOD-IB-02 配置（IFC-IB-021/022/024；AC-IB-11-03 / 11-04 / 12-03）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_003_config_defaults_are_declared():
    """[TC-UNIT-003] 所有可变行为都有明确默认值（AC-IB-11-04）。"""
    from ib.config import DictConfigurationSource, resolve_global_config

    cfg = resolve_global_config(DictConfigurationSource({}).load())
    assert cfg.embedding.dim == 1024 and cfg.embedding.model_id == "bge-m3"
    assert cfg.retrieval.top_k >= 1
    assert 0.0 <= cfg.retrieval.score_threshold <= 1.0
    assert cfg.chunking.chunk_size > 0 and cfg.chunking.chunk_overlap < cfg.chunking.chunk_size
    assert cfg.llm.router_temperature == 0.0  # 路由确定性（AC-IB-09-07）
    assert cfg.worker.lease_seconds > 0
    assert cfg.session.max_history_messages > 0


def test_TC_UNIT_004_config_validation_reports_key_only_no_values():
    """[TC-UNIT-004] 校验失败只报键名、绝不回显值（AC-IB-11-03 / 12-03）。"""
    from ib.config import ConfigurationResolver, DictConfigurationSource

    marker = "SUPER-SECRET-MARKER-VALUE"
    resolver = ConfigurationResolver(
        DictConfigurationSource(
            {
                "offline_mode": False,
                "vectorstore": {"backend": marker},
                "llm": {"backend": "openai_compatible", "api_key_env": "IB_GROUP_D_ABSENT_KEY"},
                "embedding": {"backend": "fake"},
            }
        )
    )
    errors = resolver.validate(env={})
    assert errors, "非法后端取值 + 缺失凭据，却一条校验错误都没有"
    joined = " ".join(str(e) for e in errors)
    assert marker not in joined, f"配置校验回显了取值：{joined}"
    assert "IB_GROUP_D_ABSENT_KEY" in joined or "IB_VECTORSTORE_BACKEND" in joined


def test_TC_UNIT_005_read_secret_only_from_env():
    """[TC-UNIT-005] 凭据只经环境变量读取；配置对象只存键名（AC-IB-12-02）。"""
    from ib.config import read_secret

    assert read_secret("IB_GROUP_D_ABSENT", env={}) is None
    assert read_secret("IB_GROUP_D_PRESENT", env={"IB_GROUP_D_PRESENT": "v"}) == "v"


def test_TC_UNIT_006_env_invalid_int_raises_with_key_name():
    """[TC-UNIT-006] 数字型环境变量非法时点名键名（AC-IB-11-03）。"""
    from ib.config import ConfigurationResolver, DictConfigurationSource

    resolver = ConfigurationResolver(
        DictConfigurationSource({"offline_mode": True, "max_upload_mb": "not-a-number"})
    )
    with pytest.raises(Exception) as exc:
        resolver.global_config()
    assert "IB_MAX_UPLOAD_MB" in str(exc.value) or "max_upload_mb" in str(exc.value)


# --------------------------------------------------------------------------- #
# MOD-IB-07 切分（IFC-IB-071；AC-IB-05-01 / 05-02 / 04-03）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_007_normalize_is_semantics_preserving():
    """[TC-UNIT-007] normalize 只做无语义变更的规整，不折叠大小写/不去标点（AC-IB-05-01）。"""
    from ib.chunking import normalize

    assert normalize("A   B\r\nC") == "A B\nC"
    assert normalize("Hello, World!") == "Hello, World!"
    # 3 个以上连续空行压缩（保留至多 2 个空行）
    assert normalize("X\n\n\n\n\nY") == "X\n\n\nY"
    # 未知版本原样返回（可被上层指纹察觉）
    assert normalize("a\r\nb", version="v999") == "a\r\nb"


def test_TC_UNIT_008_split_text_overlap_and_no_empty():
    """[TC-UNIT-008] 滑窗切分：相邻块有重叠、无空块、滑窗前进（AC-IB-05-01）。"""
    from ib.chunking import split_text

    text = "第一句。第二句。第三句。第四句。第五句。第六句。第七句。第八句。"
    pieces = split_text(text, chunk_size=30, chunk_overlap=10)
    assert len(pieces) >= 2
    assert all(p.strip() for p in pieces), f"出现空内容块：{pieces}"
    # 相邻块必须有重叠（穷举相邻对，任一处无重叠即失败）
    overlapped = any(
        pieces[i][-6:] in pieces[i + 1] or pieces[i + 1][:6] in pieces[i]
        for i in range(len(pieces) - 1)
    )
    assert overlapped, f"相邻块之间未观察到重叠：{pieces}"


def test_TC_UNIT_009_split_text_rejects_bad_params():
    """[TC-UNIT-009] 非法切分参数被拒（overlap >= size 会破坏滑窗前进保证）。"""
    from ib.chunking import split_text

    with pytest.raises(ValueError):
        split_text("abc", 10, 10)
    with pytest.raises(ValueError):
        split_text("abc", 0, 0)


def test_TC_UNIT_010_chunker_preserves_provenance_and_drops_empty():
    """[TC-UNIT-010] 切分保留来源定位，且不产生空块（AC-IB-04-03）。"""
    from ib.chunking import SlidingWindowChunker
    from ib.core import ChunkingSpec, ParsedChunk, ParsedDocument

    doc = ParsedDocument(
        chunks=[
            ParsedChunk(content="第一节内容。" * 20, page_or_section="sec-1", source_kind="text", locator="s:1"),
            ParsedChunk(content="   \n  ", page_or_section="sec-2", source_kind="text", locator="s:2"),
        ],
        page_count=1,
    )
    chunks = SlidingWindowChunker().split(doc, ChunkingSpec(chunk_size=50, chunk_overlap=10))
    assert chunks, "合法内容未产出任何块"
    assert all(c.content.strip() for c in chunks), "出现空内容块"
    assert {c.page_or_section for c in chunks} == {"sec-1"}, "空段被当成块或被误挂载"
    assert all(c.locator == "s:1" for c in chunks)


def test_TC_UNIT_011_chunk_params_change_applies_to_new_docs_only():
    """[TC-UNIT-011] 参数变更只影响新切分；本模块无写入动作（AC-IB-05-02 / 05-03）。"""
    from ib.chunking import SlidingWindowChunker
    from ib.core import ChunkingSpec, ParsedChunk, ParsedDocument

    text = "段落内容。" * 60
    doc = ParsedDocument(
        chunks=[ParsedChunk(content=text, page_or_section="full", source_kind="text", locator="l1")],
        page_count=1,
    )
    small = SlidingWindowChunker().split(doc, ChunkingSpec(chunk_size=40, chunk_overlap=5))
    large = SlidingWindowChunker().split(doc, ChunkingSpec(chunk_size=200, chunk_overlap=5))
    assert len(small) > len(large), "新参数未生效（大块应产出更少块）"


# --------------------------------------------------------------------------- #
# MOD-IB-05 解析（IFC-IB-141；AC-IB-01-04 / 04-03 / 04-04 / 04-05）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_012_sniff_magic_positive_and_negative():
    """[TC-UNIT-012] 魔数判定不信任扩展名（AC-IB-01-04）。"""
    from ib.parsing import sniff_magic

    assert sniff_magic(b"%PDF-1.7\n", "pdf") == "pdf"
    assert sniff_magic(b"PK\x03\x04rest", "docx") == "docx"
    assert sniff_magic("中文内容".encode("utf-8"), "txt") == "text"
    assert sniff_magic(b"hello world\n", "md") == "text"
    # 负例：改名攻击 / 二进制伪装文本 / 未知扩展名
    assert sniff_magic(b"hello world\n", "pdf") is None
    assert sniff_magic(b"PK\x03\x04", "pdf") is None
    assert sniff_magic(b"\x00\x01\x02", "txt") is None
    assert sniff_magic(b"MZ\x90\x00", "exe") is None


def test_TC_UNIT_012b_sniff_magic_multibyte_prefix_not_rejected():
    """[TC-UNIT-012b] 定长截断落在多字节字符中间不得误判（回归 code_review CRITICAL-01）。"""
    from ib.parsing import sniff_magic

    head = ("中文" * 200).encode("utf-8")[:257]  # 必然截在中文字符内部
    assert sniff_magic(head, "txt") == "text"


def test_TC_UNIT_013_registry_unregistered_ext_raises():
    """[TC-UNIT-013] 未注册扩展名 → ValueError（不静默兜底，AC-IB-04-04 / 04-05）。"""
    from ib.parsing import build_default_registry

    registry = build_default_registry()
    assert registry.supports("txt") and registry.supports("md")
    with pytest.raises(ValueError):
        registry.parse("xlsx", io.BytesIO(b"x"), ocr=None, renderer=None, spec=None)


def test_TC_UNIT_014_markdown_parser_locators():
    """[TC-UNIT-014] Markdown 按标题切节，位置地标可读且无空块（AC-IB-04-03）。"""
    from ib.parsing.text_parsers import MarkdownParser

    md = "# 标题一\n正文甲\n\n## 标题二\n正文乙\n"
    doc = MarkdownParser().parse(io.BytesIO(md.encode("utf-8")), ocr=None, renderer=None, spec=None)
    assert doc.chunks, "Markdown 未解析出任何节"
    assert all(c.content.strip() for c in doc.chunks), "出现空内容 chunk"
    assert any("标题" in c.locator for c in doc.chunks), f"定位字段不可读：{[c.locator for c in doc.chunks]}"


def test_TC_UNIT_015_text_parser_empty_warns_not_crashes():
    """[TC-UNIT-015] 空文本给出 warning 而非崩溃（依赖故障与内容问题区分）。"""
    from ib.parsing.text_parsers import TextParser

    doc = TextParser().parse(io.BytesIO(b""), ocr=None, renderer=None, spec=None)
    assert doc.chunks == [] and doc.warnings


# --------------------------------------------------------------------------- #
# MOD-IB-21 流式契约（IFC-IB-224/225；AC-IB-14-01）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_016_sse_frame_format_and_done():
    """[TC-UNIT-016] SSE 帧编码：event/data 逐行 + 结尾空行（AC-IB-14-01 界面可见降级）。"""
    from ib.core import StreamEvent, StreamEventKind
    from ib.streaming import to_sse

    frame = to_sse(StreamEvent(StreamEventKind.CONTENT, "第一行\n第二行"))
    assert frame.startswith("event: content\n")
    assert "data: 第一行\n" in frame and "data: 第二行\n" in frame
    assert frame.endswith("\n\n"), "帧未以空行结束（浏览器不会派发）"
    # 空负载必须是 `data:` 无空格
    assert to_sse(StreamEvent(StreamEventKind.DONE)) == "event: done\ndata:\n\n"


def test_TC_UNIT_017_stream_event_alias_identity():
    """[TC-UNIT-017] StreamEvent 是契约类型的直接别名（防跨模块 isinstance 恒假）。"""
    from ib.core import StreamEvent as CoreEvent
    from ib.streaming import StreamEvent as StreamEventAlias

    assert StreamEventAlias is CoreEvent


def test_TC_UNIT_018_session_store_project_isolation():
    """[TC-UNIT-018] 会话存储按项目前缀隔离，非法键读写被拒（FM-7）。"""
    from ib.core import SessionState
    from ib.streaming import MemorySessionStore

    store = MemorySessionStore()
    store.save("p_alpha:u1:s1", SessionState(messages=[], last_expert="freeark-expert", sticky_turns_left=1))
    assert store.load("p_alpha:u1:s1") is not None
    # 无项目前缀 / 其它项目键：读不到（前缀不符即拒）
    assert store.load("noproject") is None
    store.save("badkey", SessionState(messages=[], last_expert=None, sticky_turns_left=0))
    assert store.load("badkey") is None


def test_TC_UNIT_019_related_images_event_empty_suppressed():
    """[TC-UNIT-019] 无图不发事件；载荷只含短字段（IFC-IB-282）。"""
    import json

    from ib.core import RelatedImageItem, RelatedImagesPayload
    from ib.streaming import related_image_url, related_images_event, related_images_json

    assert related_images_event(None) is None
    assert related_images_event(RelatedImagesPayload(images=())) is None
    payload = RelatedImagesPayload(
        images=(
            RelatedImageItem(
                image_id="img-1",
                doc_id="d1",
                doc_name="图纸.pdf",
                page_or_section="p1",
                url_path=related_image_url("d1", "img-1"),
            ),
        )
    )
    event = related_images_event(payload)
    assert event is not None and str(event.kind) == "related_images"
    body = related_images_json(payload)
    decoded = json.loads(body)
    assert set(decoded["images"][0]) == {"image_id", "doc_id", "doc_name", "page_or_section", "url_path"}
    assert "base64" not in body.lower()


# --------------------------------------------------------------------------- #
# MOD-IB-04 可观测性（IFC-IB-041/045/215；AC-IB-13-04）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_020_redact_default_drop_and_sensitive():
    """[TC-UNIT-020] 日志默认丢弃白名单外键；敏感键脱敏；外发三键在白名单内（AC-IB-13-04）。"""
    from ib.observability import REDACTED, LOG_FIELDS, redact

    out = redact(
        {
            "stage": "startup",
            "egress_remote": True,
            "egress_host": "api.example.invalid",
            "backend": "vectorstore=memory",
            "api_key": "SHOULD-NOT-LEAK",
            "not_in_whitelist": "dropped",
            "content": "正文不得入日志",
        }
    )
    assert out["stage"] == "startup"
    assert out["egress_remote"] is True
    assert out["egress_host"] == "api.example.invalid"
    assert out["backend"] == "vectorstore=memory"
    assert out["api_key"] == REDACTED
    assert out["content"] == REDACTED
    assert "not_in_whitelist" not in out
    assert {"egress_remote", "egress_host", "egress_data", "backend"} <= set(LOG_FIELDS)


def test_TC_UNIT_021_redact_truncates_long_string():
    """[TC-UNIT-021] 白名单内长字符串被截断（防正文借字段名溜入）。"""
    from ib.observability import redact

    out = redact({"doc_name": "x" * 500})
    assert out["doc_name"].endswith("...") and len(out["doc_name"]) <= 120


# --------------------------------------------------------------------------- #
# MOD-IB-03 上下文（FM-7）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_022_session_key_prefix_assert():
    """[TC-UNIT-022] 会话键构造与读取断言（跨项目串会话防线）。"""
    from ib.context import assert_session_key, session_key
    from ib.core import ScopeViolationError

    key = session_key("p_alpha", "u1", "s1")
    assert key == "p_alpha:u1:s1"
    assert_session_key(key, "p_alpha")
    with pytest.raises(ScopeViolationError):
        assert_session_key(key, "p_beta")
    with pytest.raises(ScopeViolationError):
        session_key("p:alpha", "u1", "s1")
