"""集成测试层 1/N —— 组合根装配 + 检索服务（真实上传管线 + 隔离 + fail-open）。

覆盖 AC-IB-02-*、AC-IB-03-*（项目硬隔离）、AC-IB-15-01（检索降级可见）、AC-IB-16-03；
全部离线：内存台账 / 内存向量库 / FakeEmbedder。
"""

from __future__ import annotations

from conftest import ingest_text, request_ctx

import pytest


# --------------------------------------------------------------------------- #
# MOD-IB-23 组合根装配（IFC-IB-241）
# --------------------------------------------------------------------------- #


def test_TC_INT_001_composition_assembly_is_assertable(deps):
    """[TC-INT-001] 装配结果是一个可断言的单一事实：各端口齐备、项目已登记、前缀已断言。"""
    from ib.core import Scope, StartupError

    for field in (
        "cfg", "config_resolver", "ledger", "blobs", "parsers", "chunker", "embedder",
        "vectors", "collections", "ocr", "renderer", "llm", "sessions", "policy",
        "principal_resolver", "lifecycle", "retrieval", "rebuild", "projects", "egress",
    ):
        assert getattr(deps, field) is not None, f"Deps.{field} 未装配"
    assert set(deps.projects) == {"p_alpha", "p_beta"}
    # 自带的唯一工具经 bind_tools 暴露（每项目绑定）
    tool_names = {tool.name for tool in deps.bind_tools(Scope(project_id="p_alpha"))}
    assert tool_names == {"search_knowledge"}
    # 离线：数据不外发，健康/合规输出必须如实反映
    assert getattr(deps.egress, "remote", False) is False
    # collection 前缀断言已在装配期通过（拿不到就说明前缀不符）
    for pid in deps.projects:
        deps.collections.assert_prefix(deps.collections.resolve(Scope(project_id=pid), deps.projects[pid]), pid)
    # 未登记项目：明确报错，不回退其它项目作用域
    with pytest.raises(StartupError):
        deps.orchestrator_for("p_nonexistent")


def test_TC_INT_002_per_project_orchestrator_cached(deps):
    """[TC-INT-002] 每项目一份编排器（同项目复用同一对象，不同项目不同对象）。"""
    a1 = deps.orchestrator_for("p_alpha")
    a2 = deps.orchestrator_for("p_alpha")
    b1 = deps.orchestrator_for("p_beta")
    assert a1 is a2 and a1 is not b1


# --------------------------------------------------------------------------- #
# MOD-IB-15 检索（IFC-IB-161/162）
# --------------------------------------------------------------------------- #


def test_TC_INT_003_retrieval_happy_path_end_to_end(deps):
    """[TC-INT-003] 检索命中：真实上传→处理→检索，返回命中文档而非降级。"""
    from ib.core import Scope

    content = "温度传感器故障排查手册。第一步检查供电，第二步测量信号。"
    record = ingest_text(deps, "p_alpha", "kb_a", "handbook.txt", content)
    assert record.status == "pending"  # 处理前
    assert deps.ledger.get_document(Scope("p_alpha", ("kb_a",)), record.doc_id).status == "indexed"

    result = deps.retrieval.search(content, scope=Scope(project_id="p_alpha", kb_ids=("kb_a",)))
    assert result.degraded is False, f"正常路径不应降级：{result.degrade_reason}"
    assert result.hits, "命中为空——入库与检索未接通"
    top = result.hits[0]
    assert top.doc_id == record.doc_id
    assert "温度传感器" in top.content


def test_TC_INT_004_retrieval_project_hard_isolation(deps):
    """[TC-INT-004] 项目硬隔离：p_beta 检索不到 p_alpha 的语料（AC-IB-03-*）。"""
    from ib.core import Scope

    content = "甲项目专属的秘密工艺参数 A-9。"
    ingest_text(deps, "p_alpha", "kb_a", "secret.txt", content)

    leak = deps.retrieval.search("秘密工艺参数", scope=Scope(project_id="p_beta", kb_ids=("kb_b",)))
    assert leak.degraded is False
    assert leak.hits == [], "跨项目检索到语料——硬隔离失效"


def test_TC_INT_005_retrieval_failopen_embedder_down(deps):
    """[TC-INT-005] 检索 fail-open：embedder 故障 → degraded 结果，绝不抛（AC-IB-15-01）。"""
    from ib.core import DegradeReason, Scope
    from ib.retrieval import RetrievalService

    class _BrokenEmbedder:
        def embed_query(self, text, *, timeout_s):
            raise RuntimeError("fake embedder down")

    service = RetrievalService(
        embedder=_BrokenEmbedder(), vectors=deps.vectors, resolver=deps.collections,
        project_provider=lambda pid: deps.projects[pid],
    )
    result = service.search("任意问题", scope=Scope(project_id="p_alpha"))
    assert result.degraded is True and result.hits == []
    assert result.degrade_reason == DegradeReason.EMBEDDING_UNAVAILABLE


def test_TC_INT_006_retrieval_failopen_vectorstore_down(deps):
    """[TC-INT-006] 检索 fail-open：向量库故障 → degraded，绝不抛。"""
    from ib.core import DegradeReason, Scope
    from ib.retrieval import RetrievalService

    class _BrokenVectors:
        def bind_collection(self, collection):
            pass

        def query(self, *a, **kw):
            raise RuntimeError("vectorstore down")

    service = RetrievalService(
        embedder=deps.embedder, vectors=_BrokenVectors(), resolver=deps.collections,
        project_provider=lambda pid: deps.projects[pid],
    )
    result = service.search("任意问题", scope=Scope(project_id="p_alpha"))
    assert result.degraded is True and result.hits == []
    assert result.degrade_reason == DegradeReason.VECTORSTORE_UNAVAILABLE


def test_TC_INT_007_search_as_tool_shapes(deps):
    """[TC-INT-007] 工具形态：降级/空/命中三态均为 ok=True（不触发编排层异常路径）。"""
    from ib.core import Scope
    from ib.retrieval import RetrievalService

    class _BrokenEmbedder:
        def embed_query(self, text, *, timeout_s):
            raise RuntimeError("down")

    broken = RetrievalService(
        embedder=_BrokenEmbedder(), vectors=deps.vectors, resolver=deps.collections,
        project_provider=lambda pid: deps.projects[pid],
    )
    degraded = broken.search_as_tool("q", scope=Scope(project_id="p_alpha"))
    assert degraded.ok is True and degraded.degraded is True

    empty = deps.retrieval.search_as_tool("库里没有的词", scope=Scope(project_id="p_alpha"))
    assert empty.ok is True and empty.degraded is False and empty.content.strip()

    content = "锅炉安全阀定期校验规程。"
    ingest_text(deps, "p_alpha", "kb_a", "valve.txt", content)
    hit = deps.retrieval.search_as_tool(content, scope=Scope(project_id="p_alpha"))
    assert hit.ok is True and "valve.txt" in hit.content


# --------------------------------------------------------------------------- #
# IFC-IB-183 工具作用域绑定（构造期绑定无法被调用方覆盖）
# --------------------------------------------------------------------------- #


def test_TC_INT_008_bound_tool_scope_cannot_be_overridden(deps):
    """[TC-INT-008] 组合根绑定的检索工具：调用方传 scope 也改变不了检索范围。"""
    from ib.core import Scope

    content = "只有 p_alpha 才有的内容 ZZZ-77。"
    ingest_text(deps, "p_alpha", "kb_a", "only_a.txt", content)
    tools = deps.bind_tools(Scope(project_id="p_beta"))
    search = next(t for t in tools if t.name == "search_knowledge")
    # 调用方尝试用 scope=hack 覆盖：绑定闭包应忽略之，仍按 p_beta 检索（结果为空）
    result = search.callable("ZZZ-77", scope=Scope(project_id="p_alpha"))
    assert "only_a.txt" not in (result.content or ""), "调用方 scope 覆盖了构造期绑定"


# --------------------------------------------------------------------------- #
# FND-GROUP-D-01（R3 已修复）：能力摘要非空且对路由可见（AC-IB-10-03）
# --------------------------------------------------------------------------- #


def test_TC_INT_009_capability_digest_reflects_builtin_tools(deps):
    """[TC-INT-009] 能力摘要非空且含自带工具（R3 修复 FND-GROUP-D-01 的**正向回归守卫**）。

    契约 IFC-IB-182 与路由提示模板 `ROUTER_PROMPT{capabilities}` 要求能力摘要**由注册表派生**。
    修复前：组合根的 `Deps.capability_digest` 走**进程级空注册表**，自带工具只进 `bind_tools()`
    的**局部**注册表 → 摘要恒为空串、L2 路由提示恒为「（无可用工具）」。R3 把工具清单收敛为
    唯一登记点 `register_builtin_tools`，并在装配期登记进 `default_registry`。

    本条**正向断言修复后的真值**：摘要非空、含 `search_knowledge`，且路由提示不再是「（无可用工具）」。
    若接线再次断开（缺陷复发），本用例将**响亮失败** —— 这正是回归闸门的意义。
    """
    from ib.routing.intent import IntentRouter
    from ib.tools import build_capability_digest

    # 组合根的摘要是「默认注册表」的派生值，二者必然相等（自洽）
    assert deps.capability_digest == build_capability_digest()
    # 修复后真值：非空，且含唯一自带工具
    assert deps.capability_digest != "", "能力摘要为空——FND-GROUP-D-01 复发（装配接线又断开）"
    assert "search_knowledge" in deps.capability_digest
    # 路由提示侧不再是「无工具」占位（AC-IB-10-03：能力对 L2 路由可见）
    prompt_digest = IntentRouter._capability_digest()
    assert prompt_digest != "（无可用工具）", "路由提示仍为『无可用工具』——缺陷复发"
    assert "search_knowledge" in prompt_digest
    assert prompt_digest == deps.capability_digest


# --------------------------------------------------------------------------- #
# MOD-IB-10 向量库：项目即 collection（结构性硬隔离）+ 维度不变式（US-IB-06）
# --------------------------------------------------------------------------- #


def test_TC_INT_054_vectorstore_collection_per_project_and_dim_invariant(deps):
    """[TC-INT-054] 项目即 collection：命名含项目、跨项目不可见、按 scope 清理、维度不变式。"""
    from dataclasses import replace

    from ib.core import Scope
    from ib.embedding import collection_spec_for

    scope_a = Scope("p_alpha", ("kb_a",))
    scope_b = Scope("p_beta", ("kb_b",))
    record_a = ingest_text(deps, "p_alpha", "kb_a", "va.txt", "甲项目向量语料 AAAA。")
    ingest_text(deps, "p_beta", "kb_b", "vb.txt", "乙项目向量语料 BBBB。")

    coll_a = deps.collections.resolve(scope_a, deps.projects["p_alpha"])
    coll_b = deps.collections.resolve(scope_b, deps.projects["p_beta"])
    assert coll_a != coll_b and "p_alpha" in coll_a and "p_beta" in coll_b

    deps.vectors.bind_collection(coll_a)
    assert deps.vectors.count(scope_a) >= 1
    # 绑定 alpha 的 collection 时，beta 在该 collection 内 0 点（结构性隔离，不依赖 filter）
    assert deps.vectors.count(scope_b) == 0

    # 按 scope 清理只影响本项目
    removed = deps.vectors.delete_by_scope(scope_a)
    assert removed >= 1 and deps.vectors.count(scope_a) == 0
    deps.vectors.bind_collection(coll_b)
    assert deps.vectors.count(scope_b) >= 1, "清理甲项目误伤乙项目"

    # 维度不变式：同 collection 换维度 → 显式报错（重建流程依赖，FM-4）
    spec = collection_spec_for(deps.projects["p_alpha"])
    deps.vectors.bind_collection(coll_a)
    with pytest.raises(ValueError):
        deps.vectors.ensure_collection(replace(spec, dim=spec.dim + 1))
    # 反证：清理后该 doc 不再可检索
    assert deps.retrieval.search("甲项目向量语料 AAAA", scope=scope_a).hits == []


# --------------------------------------------------------------------------- #
# AC-IB-10-03：能力摘要与实绑工具「不可能漂移」（防漂移不变式）
# --------------------------------------------------------------------------- #


def test_TC_INT_073_capability_digest_matches_bound_tools(deps):
    """[TC-INT-073] 防漂移不变式（AC-IB-10-03）：`bind_tools` 实际绑定的工具名集合，
    必须与能力摘要里列出的工具名集合**逐名相等**。

    这是 FND-GROUP-D-01 的**结构性根治断言**：R3 把工具清单收敛为唯一登记点
    `register_builtin_tools`，「实际被绑定的工具」与「摘要里声称的工具」由同一段代码派生。
    本用例不检查具体文案，只检查两个集合相等 —— 任何一侧新增/漏登记都会立刻暴露。
    """
    from ib.core import Scope
    from ib.tools import build_capability_digest

    def _bound_names(project_id: str) -> set[str]:
        return {tool.name for tool in deps.bind_tools(Scope(project_id=project_id))}

    def _digest_names(digest: str) -> set[str]:
        names = set()
        for line in digest.splitlines():
            text = line.strip()
            if text.startswith("- ") and ":" in text:
                names.add(text[2:].split(":", 1)[0].strip())
        return names

    digest_names = _digest_names(deps.capability_digest)
    assert digest_names, "能力摘要未列出任何工具（无法建立不变式）"
    assert digest_names == _bound_names("p_alpha"), (
        f"摘要与实绑工具漂移：digest={digest_names} bound={_bound_names('p_alpha')}"
    )
    assert digest_names == _digest_names(build_capability_digest())
    # 跨项目：绑定集合不因项目而变（登记点唯一，scope 只在绑定期注入）
    assert _bound_names("p_beta") == digest_names
    assert "search_knowledge" in digest_names


