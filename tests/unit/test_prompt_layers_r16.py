"""[REV-16-2] 独立提示词目录 + 提示词分层 + 工具授权/参数（MOD-IB-01/02/16/17）。

覆盖：US-IB-29（提示词主/兜底分层与编辑）、US-IB-30（回退兜底且不回显为空）、
US-IB-31（工具授权勾选 + 工具参数可配）。对应 IFC-IB-337~350 / REQ-FUNC-IB-37~39、
REQ-NFR-IB-19。

离线纪律：纯函数 + 临时文件系统 + 进程内替身；无网络；无任何真实凭据。
"""

from __future__ import annotations

import os

import pytest

from ib.config import (
    FsExpertPromptStore,
    InMemoryExpertPromptStore,
    build_definition_document,
    derive_prompt_layers,
    load_prompt_directory,
    merge_prompt_layers,
    prompt_content_hash,
    validate_prompt_directory,
    validate_tool_params,
)
from ib.core import (
    ConditionalEdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    PromptDirectoryLayout,
    PromptNotFoundError,
    RouteSpecInput,
    Scope,
    ToolGrantSpec,
    ToolParamSpec,
    ToolParamValidationError,
    ToolParamValue,
    ToolResult,
)
from ib.tools import (
    ToolRegistry,
    bind_scope,
    build_authorized_tools,
    derive_tool_param_specs,
    validate_grants,
)


# --------------------------------------------------------------------------- #
# 构造助手
# --------------------------------------------------------------------------- #


def _expert(name: str, *, is_default: bool = False, fallback: str | None = None) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}",
        keywords=(f"k{name}",),
        exemplars=(),
        is_data_expert=False,
        fallback_prompt=f"doc::{name}" if fallback is None else fallback,
        is_delegating=False,
        is_default=is_default,
    )


def _doc(project_id: str = "p1", experts=None):
    experts = tuple(experts or (_expert("a", is_default=True), _expert("b")))
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert=experts[0].name),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
        ),
        tool_grants=(ToolGrantSpec(experts[0].name, ("search_knowledge",)),),
    )


def _tool_registry():
    """构造一个**测试专用**工具注册表：`search_knowledge` 带可选 int 参数 `top_k`。

    真实基座的 `search_knowledge` 只有必填 `query`（由 LLM 提供，不构成可配旋钮）；
    故「工具参数可配」的注入语义（配置作默认 / 调用方优先）在此用可选参数验证。
    """
    from ib.core import ToolSpec

    registry = ToolRegistry()
    spec = ToolSpec(
        name="search_knowledge",
        description="检索",
        needs_scope=True,
        parameters={
            "type": "object",
            "properties": {"top_k": {"type": "integer", "default": 3, "minimum": 1, "maximum": 50}},
            "required": [],
        },
    )

    def _impl(*, top_k: int = 3, **_: object) -> ToolResult:
        return ToolResult(ok=True, content=f"top_k={top_k}")

    registry.register(spec, _impl)
    return registry, derive_tool_param_specs(registry)


# --------------------------------------------------------------------------- #
# IFC-IB-343：分层合并（主 > 兜底文件 > 文档兜底；兜底恒非空）
# --------------------------------------------------------------------------- #


def test_merge_layers_priority_then_never_blank():
    # 主存在 → 用主（resolved_from=main_file）
    b = merge_prompt_layers("a", main_content="MAIN", fallback_content="FB", doc_fallback="DOC")
    assert b.effective_prompt == "MAIN" and b.main_prompt == "MAIN" and b.resolved_from == "main_file"
    # 主缺失 → 回退兜底文件
    b = merge_prompt_layers("a", main_content=None, fallback_content="FB", doc_fallback="DOC")
    assert b.effective_prompt == "FB" and b.main_prompt is None and b.resolved_from == "fallback_file"
    # 两层皆缺 → 文档兜底
    b = merge_prompt_layers("a", main_content="", fallback_content="", doc_fallback="DOC")
    assert b.effective_prompt == "DOC" and b.resolved_from == "definition_doc_fallback"
    # 三层皆空 → 非法（effective_prompt 永不空白，ADR-29）
    with pytest.raises(PromptNotFoundError):
        merge_prompt_layers("a", main_content=None, fallback_content="", doc_fallback="   ")


def test_prompt_content_hash_is_semantic_and_stable():
    assert prompt_content_hash("x") == prompt_content_hash("x")
    assert prompt_content_hash("x") != prompt_content_hash("y")
    assert prompt_content_hash("x").startswith("sha256:")


# --------------------------------------------------------------------------- #
# IFC-IB-345：目录装载 + 完备性校验（孤儿 / 命名不符 / 缺兜底）
# --------------------------------------------------------------------------- #


def _write_prompt(root, project_id, expert, layer, text):
    d = os.path.join(root, project_id, expert)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{layer}.md"), "w", encoding="utf-8") as fh:
        fh.write(text)


def test_load_prompt_directory_missing_is_empty_not_error(tmp_path):
    assert load_prompt_directory(str(tmp_path / "absent"), "p1") == ()


def test_validate_prompt_directory_detects_orphan_naming_and_missing_fallback(tmp_path):
    doc = _doc("p1")  # 专家 a / b
    root = str(tmp_path)
    _write_prompt(root, "p1", "a", "fallback", "fb-a")
    _write_prompt(root, "p1", "ghost", "fallback", "fb-ghost")  # 孤儿
    refs = load_prompt_directory(root, "p1")
    codes = {e.code for e in validate_prompt_directory(refs, doc=doc)}
    assert "prompt_orphan_file" in codes
    # b 无 fallback.md 且文档兜底非空（doc::b）→ 不算缺兜底
    assert "prompt_fallback_missing" not in codes

    # 文档兜底为空 + 无 fallback.md → 缺兜底
    bare = _doc("p1", experts=(_expert("a", is_default=True, fallback=""),))
    codes2 = {e.code for e in validate_prompt_directory((), doc=bare)}
    assert "prompt_fallback_missing" in codes2


def test_validate_prompt_directory_naming_mismatch(tmp_path):
    # 目录名与 ref.expert_name 不符（手工构造 ref）—— 用真实装载难以制造，故直接构造
    from ib.core import ExpertPromptDocumentRef

    ref = ExpertPromptDocumentRef("a", "main", os.path.join(str(tmp_path), "WRONG", "main.md"), "", False)
    codes = {e.code for e in validate_prompt_directory((ref,), doc=_doc("p1"))}
    assert "prompt_naming_mismatch" in codes


# --------------------------------------------------------------------------- #
# IFC-IB-344：保存（原子 + 乐观并发 + 兜底非空 fail-safe），两实现语义一致
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "store_factory",
    [
        lambda tmp: InMemoryExpertPromptStore("p1"),
        lambda tmp: FsExpertPromptStore(str(tmp), "p1"),
    ],
)
def test_save_layer_conflict_and_empty_fallback_rejected(tmp_path, store_factory):
    store = store_factory(tmp_path)
    # 首次保存成功
    first = store.save_layer("a", "main", "hello", expected_hash=None)
    assert first.saved is True and first.content_hash == prompt_content_hash("hello")
    # 错的 expected_hash → 冲突，不落盘
    conflict = store.save_layer("a", "main", "world", expected_hash="sha256:deadbeef")
    assert conflict.saved is False
    assert any(e.code == "prompt_content_hash_conflict" for e in conflict.errors)
    # 兜底为空 → 非法（fail-safe）
    empty = store.save_layer("a", "fallback", "   ", expected_hash=None)
    assert empty.saved is False
    assert any(e.code == "prompt_fallback_empty" for e in empty.errors)
    # 正确的 expected_hash → 成功覆盖
    ok = store.save_layer("a", "main", "world", expected_hash=first.content_hash)
    assert ok.saved is True and ok.content_hash == prompt_content_hash("world")


def test_fs_store_atomic_write_and_layout(tmp_path):
    store = FsExpertPromptStore(str(tmp_path), "p1")
    store.save_layer("a", "fallback", "fb", expected_hash=None)
    path = os.path.join(str(tmp_path), "p1", "a", "fallback.md")
    assert os.path.isfile(path)
    assert open(path, encoding="utf-8").read() == "fb"
    layout = store.layout()
    assert isinstance(layout, PromptDirectoryLayout)
    assert layout.root_key == "IB_EXPERT_PROMPT_DIR"
    assert "<expert_name>" in layout.file_pattern
    # 删除层
    store.delete_layer("a", "fallback")
    assert not os.path.isfile(path)


def test_store_rejects_path_traversal_expert_name(tmp_path):
    from ib.core import ConfigError

    store = FsExpertPromptStore(str(tmp_path), "p1")
    with pytest.raises(ConfigError):
        store.save_layer("..", "main", "x", expected_hash=None)


# --------------------------------------------------------------------------- #
# IFC-IB-346：工具参数校验（越界 / 类型 / 未知 / 枚举 / 未授权带参）
# --------------------------------------------------------------------------- #


def test_validate_tool_params_all_error_classes():
    specs = (
        ToolParamSpec("t.query", "str", "", None, None, None),
        ToolParamSpec("t.n", "int", "0", 1.0, 5.0, None),
        ToolParamSpec("t.mode", "str", "a", None, None, ("a", "b")),
        ToolParamSpec("other.x", "str", "", None, None, None),  # 已声明但归属未授权工具
    )
    grant = ToolGrantSpec(
        "e1",
        ("t",),
        (
            ToolParamValue("t.n", "9"),  # 越界
            ToolParamValue("t.mode", "z"),  # 枚举不符
            ToolParamValue("t.unknown", "1"),  # 未知参数（无 spec）
            ToolParamValue("other.x", "1"),  # 未授权工具带参
        ),
    )
    codes = {e.code for e in validate_tool_params((grant,), specs=specs)}
    assert {"tool_param_out_of_range", "tool_param_choice_invalid", "tool_param_unknown", "tool_param_unauthorized_tool"} <= codes
    # 类型不符（int 收到非数）
    bad_type = ToolGrantSpec("e1", ("t",), (ToolParamValue("t.n", "abc"),))
    assert {e.code for e in validate_tool_params((bad_type,), specs=specs)} == {"tool_param_type_mismatch"}
    # 合法
    good = ToolGrantSpec("e1", ("t",), (ToolParamValue("t.n", "3"), ToolParamValue("t.mode", "b")))
    assert validate_tool_params((good,), specs=specs) == ()


def test_derive_tool_param_specs_from_registry_and_authorized_binding():
    registry, derived = _tool_registry()
    assert {s.name for s in derived} == {"search_knowledge.top_k"}
    assert derived[0].type == "int" and derived[0].minimum == 1 and derived[0].maximum == 50

    # 授权勾选 → 最小授权；参数经闭包注入（配置作默认，调用方显式实参优先）
    grants = (
        ToolGrantSpec("e1", ("search_knowledge",), (ToolParamValue("search_knowledge.top_k", "7"),)),
    )
    assert validate_grants(grants, registry=registry) == ()
    authorized = build_authorized_tools(grants, registry=registry, specs=derived)
    assert [t.name for t in authorized] == ["search_knowledge"]
    bound = bind_scope(authorized, Scope(project_id="p1"), object())[0]
    assert bound.callable().content == "top_k=7"
    assert bound.callable(top_k=2).content == "top_k=2"


def test_authorized_binding_rejects_unknown_tool_and_unregistered_param():
    registry, derived = _tool_registry()
    with pytest.raises(ToolParamValidationError):
        build_authorized_tools(
            (ToolGrantSpec("e1", ("nope",)),), registry=registry, specs=()
        )
    with pytest.raises(ToolParamValidationError):
        build_authorized_tools(
            (ToolGrantSpec("e1", ("search_knowledge",), (ToolParamValue("search_knowledge.zzz", "1"),)),),
            registry=registry,
            specs=derived,
        )
    assert {e.code for e in validate_grants((ToolGrantSpec("e1", ("nope",)),), registry=registry)} == {
        "tool_grant_tool_unknown"
    }


# --------------------------------------------------------------------------- #
# IFC-IB-347 / 349：跨域合并派生 + 注入注册表
# --------------------------------------------------------------------------- #


def test_derive_prompt_layers_joins_by_expert_name_and_installs(tmp_path):
    doc = _doc("p1")
    root = str(tmp_path)
    _write_prompt(root, "p1", "a", "main", "MAIN-A")
    _write_prompt(root, "p1", "a", "fallback", "FB-A")
    _write_prompt(root, "p1", "b", "fallback", "FB-B")
    refs = load_prompt_directory(root, "p1")
    view = derive_prompt_layers(doc, refs)
    by_name = {b.expert_name: b for b in view.prompt_bundles}
    assert by_name["a"].effective_prompt == "MAIN-A" and by_name["a"].resolved_from == "main_file"
    assert by_name["b"].effective_prompt == "FB-B" and by_name["b"].resolved_from == "fallback_file"

    from ib.experts import install_prompt_bundles, main_prompts, prompt_bundles

    install_prompt_bundles(view.prompt_bundles)
    assert main_prompts().get("a") == "MAIN-A"
    assert prompt_bundles()["b"].effective_prompt == "FB-B"


def test_derive_prompt_layers_without_files_uses_doc_fallback():
    view = derive_prompt_layers(_doc("p1"), ())
    by_name = {b.expert_name: b for b in view.prompt_bundles}
    assert by_name["a"].effective_prompt == "doc::a"
    assert by_name["a"].resolved_from == "definition_doc_fallback"
