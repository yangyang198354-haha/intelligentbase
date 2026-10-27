# MOD-R26-12 / implements IFC-R26-110 / depends MOD-R26-01, 02, 04, 05, 07, 09, 10
"""版本快照 → 不可变的运行时配置（编译产物）。

`compile_project_config` 把一个 `ConfigSnapshot`（定义文档 + 提示词两层）编译成 `CompiledProjectConfig`：
`ProjectRuntimeView`（专家 / 提示词 / 每 agent 的工具与步数）+ 路由器 + DAG（或旧固定拓扑图）+ `Orchestrator`。
任一步失败抛 `ConfigError` / `StartupError` 等，**不产生半成品**。v1 文档先在内存中 canonical 规范化（文件不动）。
本模块不 import `ibweb`，所有外部依赖经 `RuntimeDeps` 注入（可离线单测）。
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from ib.core import (
    AgentRuntime,
    ConfigError,
    ConfigSnapshot,
    ExpertSpec,
    GraphConfig,
    ProjectRuntimeView,
    PromptLayers,
    Scope,
)

__all__ = [
    "RuntimeDeps",
    "ExemplarVectorCache",
    "CompiledProjectConfig",
    "compile_project_config",
    "DEFAULT_AGENT_MAX_STEPS",
]

#: 单 agent 最大步数缺省值（OQ-R26-A05：= 工具调用轮数；范围 1..8）。
DEFAULT_AGENT_MAX_STEPS = 4


class ExemplarVectorCache:
    """示例句向量按文本哈希的进程级缓存：换版编译只重算变更的文本（NFUNC-001 的编译耗时控制）。"""

    def __init__(self, max_entries: int = 4096) -> None:
        self._max = max(16, int(max_entries))
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}

    def embed(self, texts: list[str], embed_fn: Callable[[list[str]], list[list[float]]]) -> list[list[float]]:
        keys = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
        with self._lock:
            missing = [(k, t) for k, t in zip(keys, texts) if k not in self._vectors]
        if missing:
            fresh = embed_fn([t for _k, t in missing])
            with self._lock:
                if len(self._vectors) + len(missing) > self._max:
                    self._vectors.clear()
                for (k, _t), vec in zip(missing, fresh):
                    self._vectors[k] = list(vec)
        with self._lock:
            return [list(self._vectors[k]) for k in keys if k in self._vectors]


@dataclass(frozen=True)
class RuntimeDeps:
    """由组合根构造的只读依赖包（编译所需的一切外部对象；`ib.runtime` 不 import `ibweb`）。"""

    llm: Any
    retrieval: Any
    embedder: Any
    sessions: Any
    tool_registry_factory: Callable[[], Any]
    tool_param_specs: tuple[Any, ...]
    graph_config_factory: Callable[[Any], GraphConfig]
    related_images_provider_factory: Callable[[Scope], Any]
    exemplar_vector_cache: ExemplarVectorCache = field(default_factory=ExemplarVectorCache)
    graph_runtime: Literal["dag", "legacy"] = "dag"
    #: 示例句种子来源（旧部署的 `<project>.exemplars.json`）：定义文档里完全没有示例句时才回落到它。
    exemplar_seed: Callable[[str], dict[str, list[str]]] | None = None
    #: 项目 → 含 confirm 节点的图所需的进程内检查点（跨版本共享，使挂起会话可按原版本恢复；重启即丢 = fail-closed）。
    checkpointer_for: Callable[[str], Any] | None = None


@dataclass(frozen=True)
class CompiledProjectConfig:
    project_id: str
    version: int  # 试运行 = -1
    view: ProjectRuntimeView
    dag: Any  # CompiledDag | None
    orchestrator: Any
    manifest_hash: str
    source: Literal["files", "snapshot"]


def _spec_of(e: Any) -> ExpertSpec:
    # 与 `ib.experts._spec_from_input` 同源的转换（运行期 `ExpertSpec.fallback_prompt` 恒为空串，ADR-48）。
    return ExpertSpec(
        name=e.name, cn_label=e.cn_label, keywords=tuple(e.keywords), is_data_expert=e.is_data_expert,
        fallback_prompt="", is_delegating=e.is_delegating, is_default=e.is_default,
    )


def compile_project_config(
    project_id: str,
    version: int,
    snapshot: ConfigSnapshot,
    *,
    deps: RuntimeDeps,
    source: Literal["files", "snapshot"],
    trial: bool = False,
) -> CompiledProjectConfig:
    from ib.config.definition import upgrade_to_v2
    from ib.config.graph import validate_graph
    from ib.config.prompts import merge_prompt_layers
    from ib.config.versioning import manifest_hash
    from ib.experts import ExpertRegistryView
    from ib.orchestration import build_graph
    from ib.orchestration.dag import compile_dag
    from ib.routing import DEFAULT_MARGIN, DEFAULT_TAU, IntentRouter, SemanticRouter
    from ib.tools import build_agent_tools

    doc = snapshot.definition
    if doc.schema_version != 2 or doc.graph is None:
        doc = upgrade_to_v2(doc)  # v1：读时规范化（内存），不改文件（ADR-58 / NFUNC-012）
    graph = doc.graph
    assert graph is not None
    active = tuple(e for e in doc.experts if getattr(e, "status", "active") == "active")
    if not active:
        raise ConfigError("没有启用的专家，无法编译运行时配置", key="IB_DEFINITION_DOC_PATH")
    errs = validate_graph(graph, experts=doc.experts, default_expert=doc.route.default_expert)
    if errs:
        raise ConfigError(
            "编排图校验未通过：" + "；".join(f"[{i.code}] {i.path}" for i in errs[:5]), key="IB_DEFINITION_DOC_PATH"
        )
    scope = Scope(project_id=project_id)

    # 提示词：每个启用专家 main > fallback；两层皆缺 → PromptNotFoundError（fail-closed，ADR-48）
    layers = dict(snapshot.prompts)
    bundles = {
        e.name: merge_prompt_layers(
            e.name,
            main_content=layers.get(e.name, PromptLayers(None, None)).main,
            fallback_content=layers.get(e.name, PromptLayers(None, None)).fallback,
        )
        for e in active
    }

    specs = tuple(_spec_of(e) for e in active)
    default_spec = next((s for s in specs if s.name == doc.route.default_expert), None)
    if default_spec is None:
        raise ConfigError("默认专家不在启用专家集内", key="IB_DEFINITION_DOC_PATH")
    registry = ExpertRegistryView(project_id=project_id, experts=specs, default_expert=default_spec)

    # 每 agent 只拿到自己被授权的工具（参数 / 知识范围闭包注入）
    grants = {g.expert_name: g for g in doc.tool_grants}
    tool_registry = deps.tool_registry_factory()
    node_mode = {n.expert: n.input_mode for n in graph.nodes if n.kind == "agent"}
    agents: dict[str, AgentRuntime] = {}
    for e in active:
        tools = build_agent_tools(
            grants.get(e.name), registry=tool_registry, specs=deps.tool_param_specs, scope=scope,
            retrieval=deps.retrieval, knowledge=e.knowledge_scope,
        )
        agents[e.name] = AgentRuntime(
            name=e.name,
            system_prompt=bundles[e.name].effective_prompt,
            tools=tuple(tools),
            max_steps=int(e.max_steps) if e.max_steps else DEFAULT_AGENT_MAX_STEPS,
            input_mode=node_mode.get(e.name, "query_only"),
        )

    view = ProjectRuntimeView(
        version=int(version),
        experts=specs,
        default_expert=doc.route.default_expert,
        prompts={n: b.effective_prompt for n, b in bundles.items()},
        prompt_sources={n: b.resolved_from for n, b in bundles.items()},
        cn_labels={s.name: s.cn_label for s in specs},
        agents=agents,
        graph=graph,
        max_expert_steps=int(doc.route.max_expert_steps),
    )

    # 语义路由（L1）：示例句以定义文档为准（F-6）；全无示例句时回落到旧种子文件
    exemplars = {e.name: [x for x in e.exemplars if str(x).strip()] for e in active if e.exemplars}
    if not exemplars and deps.exemplar_seed is not None:
        seed = deps.exemplar_seed(project_id) or {}
        exemplars = {k: v for k, v in seed.items() if k in agents and v}
    semantic = None
    if exemplars:
        cache = deps.exemplar_vector_cache
        embedder = deps.embedder

        def _raw_embed(texts: list[str]) -> list[list[float]]:
            return [list(v) for v in embedder.embed_documents(
                list(texts), timeout_s=30.0, max_retries=1, batch_size=len(texts) or 1)]

        def _embed_texts(texts: list[str]) -> list[list[float]]:
            return cache.embed(list(texts), _raw_embed)

        semantic = SemanticRouter(
            embed_texts=_embed_texts,
            exemplars_provider=lambda pid, _ex=exemplars: _ex if pid == project_id else {},
            tau=float(doc.route.tau) if doc.route.tau is not None else DEFAULT_TAU,
            margin=float(doc.route.margin) if doc.route.margin is not None else DEFAULT_MARGIN,
        )
    router = IntentRouter(llm_provider=deps.llm, semantic=semantic, experts=registry)
    config = deps.graph_config_factory(doc.route)

    dag = None
    if deps.graph_runtime != "legacy":
        has_confirm = any(n.kind == "confirm" for n in graph.nodes)
        checkpointer = None
        if has_confirm:
            if deps.checkpointer_for is not None:
                checkpointer = deps.checkpointer_for(project_id if not trial else f"{project_id}#trial")
            else:
                from langgraph.checkpoint.memory import MemorySaver

                checkpointer = MemorySaver()
        dag = compile_dag(graph, view=view, router=router, llm=deps.llm, config=config, scope=scope,
                          checkpointer=checkpointer)

    orchestrator = build_graph(
        llm=deps.llm,
        experts=specs,
        tools=[],
        sessions=deps.sessions,
        config=config,
        router=router,
        scope=scope,
        tools_by_expert={n: list(a.tools) for n, a in agents.items()},
        related_images_provider=deps.related_images_provider_factory(scope),
        view=view,
        dag=dag,
    )
    return CompiledProjectConfig(
        project_id=project_id,
        version=int(version),
        view=view,
        dag=dag,
        orchestrator=orchestrator,
        manifest_hash=manifest_hash(snapshot),
        source=source,
    )
