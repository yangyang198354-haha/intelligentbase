"""[REV-26 / GROUP_D] MOD-R26-09 检索知识范围（ADR-62）与路由候选集 `restrict_to`；MOD-R26-08 LLM 客户端有界 LRU。

溯源：US-009（AC-009-01 目录范围检索不越界 / AC-009-03 空范围 0 命中且不查向量库）、US-029（AC-029-04）、
US-006（AC-006-01 路由）、US-014（LRU 随热生效版本增长有界）。
层级：单元（真实内存向量库 + FakeEmbedder 经真实入库管线；范围解析器为端口替身）。
"""

from __future__ import annotations

from conftest import ingest_text

from ib.core import KnowledgeScope, Scope
from ib.llm import OpenAiCompatibleProvider
from ib.retrieval import RetrievalService

P = "p_alpha"
SC = Scope(project_id=P, kb_ids=(P,))
DOC_A = "手册专属内容 空调机组 风机盘管 保养周期"
DOC_B = "制度专属内容 报销流程 财务审批 内部制度"


class CountingVectors:
    """向量库代理：只数 query 次数（注入给被测服务的依赖，不是打在被测模块上的补丁）。"""

    def __init__(self, inner):
        self._inner, self.queries = inner, []

    def query(self, *a, **kw):
        self.queries.append(kw.get("filter"))
        return self._inner.query(*a, **kw)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class Resolver:
    def __init__(self, mapping, truncated=False, fail=False):
        self.mapping, self.truncated, self.fail, self.calls = mapping, truncated, fail, 0

    def live_doc_ids(self, project_id, folder_ids, *, limit):
        self.calls += 1
        if self.fail:
            raise RuntimeError("ledger down (simulated)")
        ids = tuple(i for f in folder_ids for i in self.mapping.get(f, ()))
        return ids, self.truncated


def _svc(deps, resolver):
    vectors = CountingVectors(deps.vectors)
    svc = RetrievalService(
        embedder=deps.embedder, vectors=vectors, resolver=deps.collections,
        project_provider=deps.retrieval._project_provider, top_k=5, score_threshold=0.0,
        entry_resolver=deps.retrieval._entry_resolver, doc_scope_resolver=resolver,
    )
    return svc, vectors


def _setup(deps):
    a = ingest_text(deps, P, P, "manual.txt", DOC_A)
    b = ingest_text(deps, P, P, "policy.txt", DOC_B)
    return a.doc_id, b.doc_id


def test_TC_UNIT_R26_160_folder_scope_never_returns_out_of_scope_documents(deps):
    """US-009 / AC-009-01：范围 = 目录“产品手册”时，只在“内部制度”里才有答案的问题 → 无来自制度目录的片段；
    成对正例：同范围内文档可被检索到。"""
    a, b = _setup(deps)
    svc, vectors = _svc(deps, Resolver({"manual": (a,), "policy": (b,)}))
    res = svc.search(DOC_B, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("manual",)))
    assert res.degraded is False
    assert b not in {h.doc_id for h in res.hits}
    pos = svc.search(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("manual",)))
    assert a in {h.doc_id for h in pos.hits}
    assert vectors.queries and all(f.doc_ids == (a,) and f.project_id == P for f in vectors.queries)


def test_TC_UNIT_R26_161_empty_scope_zero_hits_and_vector_store_not_queried(deps):
    """US-009 / AC-009-03：空范围 → 0 命中、不查询向量库、degraded=False（空范围 ≠ 依赖故障）。"""
    _setup(deps)
    svc, vectors = _svc(deps, Resolver({}))
    res = svc.search(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=()))
    assert res.hits == () or list(res.hits) == []
    assert res.degraded is False and vectors.queries == []
    tool = svc.search_as_tool(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=()))
    assert tool.ok and not tool.degraded


def test_TC_UNIT_R26_162_scope_resolving_to_no_live_docs_is_zero_hit(deps):
    """目录存在但其中无存活文档 → 0 命中（不回落到全库）。"""
    _setup(deps)
    svc, vectors = _svc(deps, Resolver({"empty": ()}))
    res = svc.search(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("empty",)))
    assert list(res.hits) == [] and res.degraded is False and vectors.queries == []


def test_TC_UNIT_R26_163_resolver_failure_degrades_fail_closed_not_full_library(deps):
    """ADR-13：解析器故障 → 降级（ledger_unavailable），绝不回落为全库检索；与“空范围”可区分。"""
    _setup(deps)
    svc, vectors = _svc(deps, Resolver({}, fail=True))
    res = svc.search(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("manual",)))
    assert res.degraded is True and list(res.hits) == [] and vectors.queries == []


def test_TC_UNIT_R26_164_truncated_scope_post_filters_and_never_crosses_boundary(deps):
    """ADR-62 偏差 #4：范围过大被截断 → 不加 doc_ids，以已解析集合后过滤——可能漏召回，但绝不越界。"""
    a, b = _setup(deps)
    svc, vectors = _svc(deps, Resolver({"manual": (a,), "policy": (b,)}, truncated=True))
    res = svc.search(DOC_B, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("manual",)))
    assert b not in {h.doc_id for h in res.hits}
    assert vectors.queries and vectors.queries[-1].doc_ids is None


def test_TC_UNIT_R26_165_mode_all_or_none_behaves_like_baseline(deps):
    """兼容：knowledge=None / mode="all" → 全库检索，不调用范围解析器。"""
    a, b = _setup(deps)
    resolver = Resolver({"manual": (a,)})
    svc, _ = _svc(deps, resolver)
    for ks in (None, KnowledgeScope()):
        res = svc.search(DOC_B, scope=SC, knowledge=ks)
        assert b in {h.doc_id for h in res.hits}
    assert resolver.calls == 0


def test_TC_UNIT_R26_166_project_id_always_in_filter_cross_project_isolation(deps):
    """AC-010-04 / AC-019-01：即使带范围，PointFilter.project_id 恒为当前项目。"""
    a, _b = _setup(deps)
    svc, vectors = _svc(deps, Resolver({"manual": (a,)}))
    svc.search(DOC_A, scope=SC, knowledge=KnowledgeScope(mode="folders", folder_ids=("manual",)))
    assert {f.project_id for f in vectors.queries} == {P}


def test_TC_UNIT_R26_167_router_restrict_to_limits_candidates(deps):
    """US-006 / AC-006-01、MOD-R26-09：restrict_to 限定路由候选与默认回落；None 时行为不变。"""
    from ib.core import ExpertSpec
    from ib.experts import ExpertRegistryView
    from ib.routing import IntentRouter

    def sp(n, kw, d=False):
        return ExpertSpec(name=n, cn_label=n, keywords=kw, is_data_expert=False, fallback_prompt="",
                          is_delegating=False, is_default=d)

    a, b = sp("billing", ("发票",)), sp("kb", ("资料",), True)
    router = IntentRouter(experts=ExpertRegistryView(project_id=P, experts=(a, b), default_expert=b))
    sc = Scope(project_id=P)
    assert router.classify_experts("我的发票怎么报销", scope=sc).experts == ["billing"]
    limited = router.classify_experts("我的发票怎么报销", scope=sc, restrict_to=["kb"])
    assert "billing" not in limited.experts


def test_TC_UNIT_R26_168_llm_client_cache_is_bounded_lru(monkeypatch):
    """US-014：热生效后提示词随版本变化，旧版本客户端不再被引用 → 客户端缓存有界（LRU 淘汰）。

    底层网络客户端工厂以 monkeypatch 替身化（外部依赖边界，不连网）。
    """
    import ib.llm as llm_mod

    made = []
    monkeypatch.setattr(llm_mod, "_make_langchain_client", lambda **kw: made.append(kw["system_prompt"]) or object())
    p = OpenAiCompatibleProvider(base_url="http://offline.invalid", model="m", api_key="placeholder-not-a-secret",
                                 client_cache_max=3)
    for i in range(10):
        p._client(0.6, f"prompt-v{i}")
    assert len(p._clients) == 3
    assert list(k[1] for k in p._clients) == ["prompt-v7", "prompt-v8", "prompt-v9"]
    first = p._client(0.6, "prompt-v7")  # 命中并刷新最近使用
    p._client(0.6, "prompt-v10")
    assert ("prompt-v7" in [k[1] for k in p._clients]) and first is p._client(0.6, "prompt-v7")
    assert len(made) == 11, "命中缓存不重复构造"
