"""
@module MOD-IB-23
@implements IFC-IB-241 build_application / build_deps（组合根，module_design §5）
            R2：`related_images` 提供者（命中 → 页面图）在 `orchestrator_for` 内闭包注入
            R7：装配期 fail-fast 准入闸门 admit（IFC-IB-293）；定义文档读写端点
                （IFC-IB-294/295，落在 `ibweb/views.py`）
@depends MOD-IB-01 ~ MOD-IB-22
@author software-developer

**唯一装配点**（module_design §5 的组合根装配表在本文件的 `build_deps` 里逐行兑现）。

## 这个文件为什么必须是唯一入口

「哪个后端被用上了」这件事，如果分散在多处判断，就会出现**只有生产才成立的组合**：
例如开发用内存台账（重启即丢）、生产用 SQLite 台账，而某处代码却在启动期假定台账一定有行。
把所有 `IB_*_BACKEND` 分支收在一个函数里，装配结果就变成**一个可打印、可断言的对象**
（`Deps`），排障时直接看它，而不是靠猜。

## 启动期做三件「宁可在启动时失败」的事

1. **必填校验**（`validate_required`）：缺 `IB_LLM_API_KEY` 之类的错误，若推迟到首个请求，
   表现是「用户上传后卡住」；启动即失败则 systemd 会重试并给出清晰的键名。
2. **AuthzPolicy 注入断言**：见 `ibweb.authz` 模块文档（静默 403 是最难查的故障形态）。
3. **台账播种 + collection 就绪 + 前缀断言（FM-5）**：项目/知识库是配置实体，
   启动时写进台账；并逐个 `ensure_collection` + `assert_prefix`。
   不做的后果很具体：`active_collection_version` 会抛「项目未登记」，
   而**每一次上传**都会因归属断言失败而 403 —— 一个只有真正跑起来才暴露的窟窿。

## 每项目一份编排器（而不是每请求一份）

`orchestration.build_graph(scope=...)` 的 scope 是**装配期**参数，因此「一个图 = 一个 scope」。
按 `project_id` 缓存，既保持「scope 构造期绑定」的安全语义（ADR-09），
又不必每个请求都重编译一次 StateGraph。工具在同一处按项目绑定 ——
**绑定后的闭包只在进程内复用，不跨项目**，因为缓存键就是 project_id。
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field, replace
from typing import Any, Sequence

from ib.core import (
    ConfigError,
    KbRecord,
    ProjectRecord,
    Scope,
    StartupError,
    ToolResult,
    ToolSpec,
)
from ib.config import (
    ConfigurationResolver,
    DictConfigurationSource,
    FileConfigurationSource,
    read_secret,
    resolve_project_config,
    validate_required,
)

__all__ = [
    "Deps",
    "build_deps",
    "get_deps",
    "set_deps",
    "is_bootstrapped",
    "build_application",
    "resolve_scope",
    "register_builtin_tools",
    "admit",
    "SEARCH_TOOL_SPEC",
]

#: 基座自带的**唯一**工具：知识库检索（scope 在构造期绑定，见 IFC-IB-183）。
#: 描述文本进入路由提示的能力摘要（IFC-IB-182），故措辞要说清「查什么」而不是「怎么实现」。
#: **不再**在描述里手写「（需要范围绑定）」——`needs_scope=True` 时该后缀由
#: `build_capability_digest` 统一附加；描述里再写一遍会得到重复后缀（R3 修正）。
SEARCH_TOOL_SPEC = ToolSpec(
    name="search_knowledge",
    description="在企业知识库中检索与问题相关的资料片段，返回文件名与位置",
    needs_scope=True,
)


@dataclass
class Deps:
    """装配结果（**可打印、可断言**的单一装配事实）。

    字段顺序即装配顺序，便于 `print(deps)` 时人工核对。
    """

    cfg: Any
    config_resolver: ConfigurationResolver
    ledger: Any
    blobs: Any
    parsers: Any
    chunker: Any
    embedder: Any
    vectors: Any
    collections: Any
    ocr: Any
    renderer: Any
    llm: Any
    sessions: Any
    policy: Any
    principal_resolver: Any
    lifecycle: Any
    retrieval: Any
    rebuild: Any
    projects: dict[str, ProjectRecord]
    egress: Any
    capability_digest: str
    # R7 定义文档（单一真源）：存储端口 + 每项目已装载文档 / 已派生只读视图。
    definition_store: Any = None
    definitions: dict[str, Any] = field(default_factory=dict)
    derived_views: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._orchestrators: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # 每项目一份编排器（工具按项目绑定）
    # ------------------------------------------------------------------ #

    def orchestrator_for(self, project_id: str) -> Any:
        """取（或构造）该项目的作用域绑定编排器。未登记项目 → 明确报错，不回退默认。"""
        with self._lock:
            existing = self._orchestrators.get(project_id)
            if existing is not None:
                return existing
        if project_id not in self.projects:
            raise StartupError(f"项目未在配置中登记：{project_id}（不得回退到其他项目的作用域）")
        scope = Scope(project_id=project_id)
        bound_tools = self.bind_tools(scope)

        from ib.experts import EXPERT_SPECS
        from ib.orchestration import build_graph
        from ib.routing import IntentRouter

        # R7：图配置 / 路由阈值一律取自**已准入的定义文档**（单一真源，ADR-15）；
        #     未装配定义文档时回退既有常量（与 R1~R6 行为逐位一致）。
        route = getattr(self.definitions.get(project_id), "route", None)

        # L1 语义路由的向量化走 embedding 热路径；失败时 SemanticRouter 自己吞掉（fail-open）
        semantic = _build_semantic_router(self.embedder, project_id, route)
        router = IntentRouter(llm_provider=self.llm, semantic=semantic)
        graph = build_graph(
            llm=self.llm,
            experts=EXPERT_SPECS,
            tools=bound_tools,
            sessions=self.sessions,
            config=_graph_config(self.cfg, route),
            router=router,
            scope=scope,
            tools_by_expert={name: bound_tools for name in _expert_names()},
            # R2（M-02 读路径）：命中 → 页面图的映射在**组合根**注入（编排层不认识知识库）
            related_images_provider=_make_related_images_provider(self.ledger, scope),
        )
        with self._lock:
            self._orchestrators[project_id] = graph
        return graph

    def bind_tools(self, scope: Scope) -> list[Any]:
        """把 scope 与检索服务闭包进工具（**每项目一次**；绝不跨项目复用）。

        工具的**实现形态**刻意写成「带 `scope` / `retrieval` 关键字的普通函数」：
        `ib.tools.bind_scope` 会把这两个值注入闭包并产出无参 `BoundTool`，
        于是 LLM 侧在结构上无法指定 scope（ADR-09）。

        注册表是**本项目专属的新实例**（不是进程级 `default_registry`）：闭包持有本请求的
        scope，绝不可跨请求复用。工具的**清单**则来自唯一的登记点 `register_builtin_tools`，
        因此「实际被绑定的工具」与「能力摘要里声称的工具」不可能漂移（FND-GROUP-D-01）。
        """
        from ib.tools import ToolRegistry, bind_scope

        registry = register_builtin_tools(ToolRegistry())
        return bind_scope(registry.registered(), scope, self.retrieval)

    def close(self) -> None:
        """释放资源（flush 向量库写缓冲）。关机路径调用，**失败不抛**（尽力而为）。"""
        try:
            self.vectors.flush()
        except Exception:  # noqa: BLE001 - 关机清理失败不应掩盖真正的关机原因
            pass


def _search_tool(query: str, *, scope: Scope, retrieval: Any) -> ToolResult:
    """知识库检索工具的实现体。

    `scope` / `retrieval` 由 `bind_scope` 在构造期注入（**不由调用方指定**）——
    因此 LLM 传什么都改变不了检索范围。`search_as_tool` 永不抛异常（降级时 `ok=True`
    + `degraded=True`），故这里不需要 try。
    """
    return retrieval.search_as_tool(query, scope=scope)


def register_builtin_tools(registry: Any) -> Any:
    """把**基座自带工具**登记进给定注册表（`ToolRegistry`），返回同一注册表。

    ## 为什么必须是唯一登记点（FND-GROUP-D-01 的根因修复）

    登记动作此前只发生在 `Deps.bind_tools()` 内的**局部**注册表里，而能力摘要
    （IFC-IB-182）走的是**进程级 `default_registry`** —— 两处各写一遍工具清单，
    于是摘要恒为空串、L2 路由提示恒为「（无可用工具）」（契约宣称的能力对路由不可见）。
    把清单收敛到本函数后，「实际被 `bind_tools` 绑定的工具」与「摘要里声称的工具」
    由**同一段代码**派生，不可能再漂移。

    ## 为什么登记进进程级注册表**不**构成跨项目泄漏

    注册表里存的是 `ToolSpec`（纯声明）与**未绑定的**实现函数：`scope` 是实现的
    关键字参数，只有在 `bind_scope(...)` 构造期才被闭包注入（ADR-09）。因此
    进程级注册表里**不存在任何项目作用域**；`bind_tools()` 仍然每项目新建注册表，
    「每项目一次、绝不跨项目复用」的纪律不变。
    """
    registry.register(SEARCH_TOOL_SPEC, _search_tool)
    return registry


def _make_related_images_provider(ledger: Any, scope: Scope) -> Any:
    """构造「命中 → 关联图片」提供者（R2 / M-02 读路径的生产者）。

    ## 为什么这个函数在组合根而不在编排层

    它同时需要**两件业务知识**：台账里有哪些 `chunk_image` 关联行、以及图片端点的
    URL 模板。编排层被明确要求「业务零依赖」（IFC-IB-231），故映射只能在这里闭包注入；
    编排层只负责「在 `content` 之后调用它、把非空结果发成事件」。

    ## 结构（**一次查表，不做启发式猜测**）

    `hits` 里的每个 `(doc_id, page_or_section)` 直接对应 `chunk_image` 的索引列
    （`idx_chunk_image_scope` / `idx_chunk_image_doc`），故「这段回答引用了哪些图」
    是一次按 key 的**查表**而非检索期的猜测 —— 这正是 M-02 根因修复的落点：
    图文块在**入库期**就共享同一个 `page_or_section`，检索期只需沿该键回溯。

    ## 保序与去重

    顺序 = `hits` 顺序（`hits` 本身按相关性），同一 `doc_id` 内按 `(page_or_section,
    image_id)` 升序（台账 `ORDER BY` 已保证，IFC-IB-279）。去重键用 `image_id`
    （它是 `(doc_id, page_or_section, locator)` 的确定性派生值，全局唯一）。

    ## 空结果即 `None`

    返回 `None` 而非空载荷：让「无图」这一个事实只有**一种**表示，
    下游 `related_images_event()` 的「空即不发」判断因此不会漏。
    """
    from ib.core import RelatedImageItem, RelatedImagesPayload
    from ib.streaming import related_image_url

    def _provider(hits: Sequence[Any], provider_scope: Scope) -> RelatedImagesPayload | None:
        keys: list[tuple[str, str]] = []
        seen_keys: set[tuple[str, str]] = set()
        for hit in hits or ():
            doc_id = str(getattr(hit, "doc_id", "") or "")
            if not doc_id:
                continue
            key = (doc_id, str(getattr(hit, "page_or_section", "") or ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            keys.append(key)
        if not keys:
            return None
        items: list[RelatedImageItem] = []
        seen_images: set[str] = set()
        for doc_id, page_or_section in keys:
            for record in ledger.list_chunk_images(provider_scope, doc_id):
                if page_or_section and record.page_or_section != page_or_section:
                    continue
                if record.image_id in seen_images:
                    continue
                seen_images.add(record.image_id)
                items.append(
                    RelatedImageItem(
                        image_id=record.image_id,
                        doc_id=record.doc_id,
                        doc_name=record.doc_name,
                        page_or_section=record.page_or_section,
                        url_path=related_image_url(record.doc_id, record.image_id),
                    )
                )
        return RelatedImagesPayload(images=tuple(items)) if items else None

    return _provider


# --------------------------------------------------------------------------- #
# IFC-IB-241 组装
# --------------------------------------------------------------------------- #


def build_application(deps: Deps | None = None) -> Any:
    """[IFC-IB-241] 返回 `WSGIApplication`。

    R1 语义：由 v1.0.0 的 `ASGIApp` 改为 `WSGIApplication`，**装配语义不变** ——
    `deps` 仍是唯一注入来源；未显式传入时使用已装配的 `Deps`（`apps.ready()` 已建好）。
    """
    if deps is not None:
        set_deps(deps)
    if get_deps(required=False) is None:
        # `manage.py check` / `runserver` 等路径不会先调 build_deps，此处补齐
        build_deps()

    from django.core.wsgi import get_wsgi_application

    return get_wsgi_application()


# --------------------------------------------------------------------------- #
# 装配（唯一入口）
# --------------------------------------------------------------------------- #

_DEPS: Deps | None = None
_DEPS_LOCK = threading.Lock()


def _config_source() -> Any:
    """按 `IB_CONFIG_SOURCE` 选择配置来源（`file` 默认 / `dict` 供离线自测注入）。"""
    source_kind = os.environ.get("IB_CONFIG_SOURCE", "file").strip() or "file"
    if source_kind == "dict":
        raw = _DICT_OVERRIDE.get("raw")
        if raw is None:
            raise StartupError(
                "IB_CONFIG_SOURCE=dict 但未注入配置字典：离线自测请用 "
                "build_deps(raw=...)，否则改回 IB_CONFIG_SOURCE=file"
            )
        return DictConfigurationSource(raw)
    path = os.environ.get("IB_CONFIG_FILE", "").strip()
    if not path:
        raise StartupError("缺少必填环境变量 IB_CONFIG_FILE（配置文件路径）。只登记键名，不回显值。")
    return FileConfigurationSource(path)


#: `IB_CONFIG_SOURCE=dict` 时的进程内配置载体（仅离线自测使用）。
_DICT_OVERRIDE: dict[str, Any] = {}


def build_deps(raw: dict[str, Any] | None = None, *, force: bool = False) -> Deps:
    """装配全部适配器与服务（幂等；重复调用返回同一 `Deps`）。

    `raw` 只用于离线自测（`IB_CONFIG_SOURCE=dict` 的进程内配置）。
    """
    global _DEPS
    with _DEPS_LOCK:
        if _DEPS is not None and not force:
            return _DEPS
        if raw is not None:
            _DICT_OVERRIDE["raw"] = raw
        deps = _assemble()
        _DEPS = deps
        return deps


def set_deps(deps: Deps | None) -> None:
    """显式设置装配结果（供 `build_application(deps)` 与测试注入）。"""
    global _DEPS
    with _DEPS_LOCK:
        _DEPS = deps


def get_deps(*, required: bool = True) -> Deps | None:
    """取装配结果；`required=True` 且尚未装配 → `StartupError`（不隐式再装配，
    避免半配置状态下被静默接受）。"""
    if _DEPS is None and required:
        raise StartupError("组合根尚未装配：请先调用 build_deps()（唯一装配点）")
    return _DEPS


def is_bootstrapped() -> bool:
    return _DEPS is not None


def _assemble() -> Deps:
    """真正的装配动作（`build_deps` 加锁后调用）。"""
    from ib.blob import build_blob_store
    from ib.chunking import SlidingWindowChunker
    from ib.embedding import build_embedder, collection_spec_for
    from ib.ledger import build_ledger, load_project_record
    from ib.llm import build_llm_provider
    from ib.lifecycle import DocumentLifecycle
    from ib.observability import configure_logging, log_event
    from ib.ocr import build_ocr_engine
    from ib.parsing import default_registry
    from ib.rebuild import RebuildAwareProjectProvider, RebuildService
    from ib.rendering import build_page_renderer
    from ib.retrieval import RetrievalService
    from ib.streaming import MemorySessionStore
    from ib.tools import build_capability_digest
    from ib.tools import default_registry as default_tool_registry
    from ib.vectorstore import build_vector_store

    resolver = ConfigurationResolver(_config_source())
    cfg = resolver.global_config()
    cfg = _offline_view(cfg)

    # 1) 必填校验：**只报键名**（AC-IB-12-03）
    errors = resolver.validate()
    if errors:
        keys = "；".join(getattr(e, "key", "") or str(e) for e in errors)
        raise StartupError(f"启动期配置校验失败（共 {len(errors)} 项，仅列键名）：{keys}")

    configure_logging(cfg.logging.level, json_lines=cfg.logging.json_lines)

    # 2) 台账 + 项目登记（配置是项目/知识库的真源）
    ledger = build_ledger(cfg)
    projects = _seed_projects(cfg, ledger)

    # 3) 适配器
    vectors = build_vector_store(cfg)
    embedder = build_embedder(cfg)
    blobs = build_blob_store(cfg)
    ocr = build_ocr_engine(enabled=cfg.ocr_enabled)
    renderer = build_page_renderer(enabled=cfg.render_enabled)
    llm = build_llm_provider(cfg)
    sessions = MemorySessionStore(max_sessions=2000, idle_ttl_s=24 * 3600)
    collections = _CollectionResolver()

    # 3b) collection 就绪 + 前缀断言（FM-5 / AC-IB-12-03）
    _ensure_collections(vectors, collections, projects)

    read_provider = _make_read_provider(ledger, cfg)
    write_provider = RebuildAwareProjectProvider(ledger, read_provider)

    # 4) 服务
    lifecycle = DocumentLifecycle(
        ledger=ledger,
        blobs=blobs,
        parsers=default_registry,
        chunker=SlidingWindowChunker(),
        embedder=embedder,
        vectors=vectors,
        resolver=collections,
        ocr=ocr,
        renderer=renderer,
        chunking_spec=cfg.chunking_spec,
        project_provider=write_provider,  # 写路径：重建期间写目标版本
        max_upload_bytes=cfg.max_upload_mb * 1024 * 1024,
        cold_timeout_s=cfg.embedding.cold_timeout_s,
        cold_max_retries=cfg.embedding.cold_max_retries,
        cold_batch_size=cfg.embedding.cold_batch_size,
        lease_seconds=cfg.worker.lease_seconds,
    )
    retrieval = RetrievalService(
        embedder=embedder,
        vectors=vectors,
        resolver=collections,
        project_provider=read_provider,  # 读路径：重建期间仍读旧版本（AC-IB-16-03）
        top_k=cfg.retrieval.top_k,
        score_threshold=cfg.retrieval.score_threshold,
        candidate_multiplier=cfg.retrieval.candidate_multiplier,
        hot_timeout_s=cfg.embedding.hot_timeout_s,
    )
    rebuild = RebuildService(
        ledger=ledger,
        vectors=vectors,
        lifecycle=lifecycle,
        resolver=collections,
        project_provider=write_provider,
        current_factors=lambda: _fingerprint_factors(cfg),
        batch_limit=cfg.worker.batch_limit,
    )

    # 5) 鉴权（未注入即启动失败）
    from ibweb.authz import build_authz

    first_project = next(iter(projects), "")
    policy, principal_resolver = build_authz(
        offline_mode=cfg.offline_mode, project_id=first_project
    )

    # 4b) 能力摘要（IFC-IB-182）：把自带工具登记进**进程级默认注册表**。
    #     这一步是 FND-GROUP-D-01 的接线修复：`IntentRouter._capability_digest()` 走的是
    #     无参 `build_capability_digest()`（即默认注册表），因此摘要能否派生**取决于装配期
    #     有没有在这里登记**。登记源与 `bind_tools` 是同一个函数 → 摘要与实绑工具不漂移。
    register_builtin_tools(default_tool_registry)

    # 4c) R7 定义文档准入闸门（ADR-16）：装载 → 校验 → 派生 → 注入（任一步失败即启动失败）。
    #     闸门位于装配序列**第一步**精神：在构造并注入运行期注册表 / 图配置之前完成。
    #     序列：IFC-IB-288 装载 → IFC-IB-293 准入（内含 IFC-IB-290）→ IFC-IB-291 派生
    #           → 注入 MOD-IB-16/17/19/22 → 图编译一次常驻（首个请求时在 orchestrator_for）。
    definition_store = build_definition_store(cfg, projects)
    definitions: dict[str, Any] = {}
    derived_views: dict[str, Any] = {}
    for project_id in projects:
        doc = definition_store.load(project_id)  # IFC-IB-288
        view = admit(doc, store=definition_store)  # IFC-IB-293（内含 IFC-IB-290 / 291）
        definitions[project_id] = doc
        derived_views[project_id] = view
    _inject_derived_experts(next(iter(projects), ""), definitions, derived_views)

    deps = Deps(
        cfg=cfg,
        config_resolver=resolver,
        ledger=ledger,
        blobs=blobs,
        parsers=default_registry,
        chunker=SlidingWindowChunker(),
        embedder=embedder,
        vectors=vectors,
        collections=collections,
        ocr=ocr,
        renderer=renderer,
        llm=llm,
        sessions=sessions,
        policy=policy,
        principal_resolver=principal_resolver,
        lifecycle=lifecycle,
        retrieval=retrieval,
        rebuild=rebuild,
        projects=projects,
        egress=llm.describe_egress(),
        # 由**刚登记过自带工具的**注册表派生（与 bind_tools 同一清单）
        capability_digest=build_capability_digest(),
        definition_store=definition_store,
        definitions=definitions,
        derived_views=derived_views,
    )
    log_event(
        "startup",
        "succeeded",
        project_id=first_project,
        backend=_backend_summary(cfg),
        egress_remote=bool(getattr(deps.egress, "remote", False)),
        egress_host=getattr(deps.egress, "endpoint_host", "") or "",
        egress_data=",".join(str(c) for c in getattr(deps.egress, "data_categories", []) or []),
    )
    return deps


def _offline_view(cfg: Any) -> Any:
    """离线模式下把配置**视图**整体切到替身列（module_design §5「一键离线」）。

    用 `replace` 得到一个**新的** `GlobalConfig` 而不改原件：装配需要的是「以替身跑」，
    而打印出来的配置仍应是运维实际填写的值 —— 否则排障时会误以为「生产配的就是内存后端」。
    """
    if not cfg.offline_mode:
        return cfg
    return replace(
        cfg,
        ledger_backend="memory",
        ocr_enabled=False,
        render_enabled=False,
        embedding=replace(cfg.embedding, backend="fake"),
        vectorstore=replace(cfg.vectorstore, backend="memory"),
        llm=replace(cfg.llm, backend="fake"),
    )


def _seed_projects(cfg: Any, ledger: Any) -> dict[str, ProjectRecord]:
    """把配置里的项目/知识库写进台账（幂等）。**没有项目配置即启动失败**。"""
    from ib.config import resolve_project_config as _resolve

    if not cfg.projects:
        raise StartupError("未配置任何项目：请在配置中至少登记一个 projects.<project_id>")
    out: dict[str, ProjectRecord] = {}
    for project_id in cfg.projects:
        project_cfg = _resolve(cfg, project_id)
        existing = ledger.get_project(project_id) if hasattr(ledger, "get_project") else None
        version = getattr(existing, "active_collection_version", "") or project_cfg.active_collection_version
        record = ProjectRecord(
            project_id=project_id,
            name=project_cfg.name,
            active_collection_version=version,
            embedding_model_id=cfg.embedding.model_id,
            dim=cfg.embedding.dim,
            created_at=getattr(existing, "created_at", "") or "",
        )
        ledger.upsert_project(record)
        for kb_id in getattr(project_cfg, "kb_ids", ()) or ():
            ledger.upsert_kb(KbRecord(kb_id=kb_id, project_id=project_id, name=kb_id, created_at=""))
        out[project_id] = record
    return out


def _ensure_collections(vectors: Any, collections: Any, projects: dict[str, ProjectRecord]) -> None:
    """逐项目建 collection 并断言前缀与项目一致（FM-5）。

    启动期做这件事的收益：**把「collection 名被写错」从运行期偶发命中错误，变成启动即失败**。
    Qdrant 侧若不可达，这里就会抛 → systemd 重试（这正是 fail-fast 想要的形态）。
    """
    from ib.embedding import collection_spec_for

    for project in projects.values():
        spec = collection_spec_for(project)
        collections.assert_prefix(spec.collection, project.project_id)
        vectors.ensure_collection(spec)


def _make_read_provider(ledger: Any, cfg: Any) -> Any:
    """读路径的 `ProjectRecord` 提供者（每次现取，使重建切换后读路径立刻跟上）。

    本函数在装配期注册，但**运行期才被调用** —— 因此 `load_project_record` 必须在此处
    局部导入，不能依赖 `_assemble()` 里的模块级导入（那是我踩过的坑：闭包引用了一个
    在定义作用域内不存在的名字，`NameError` 直到第一次检索才暴露，而检索层把
    **任何**异常都转成 `degraded`，于是缺陷表现为「知识库永远检索不到东西」而不是报错 ——
    最难定位的一类静默故障）。
    """
    from ib.ledger import load_project_record

    def _provider(project_id: str) -> ProjectRecord:
        return load_project_record(ledger, cfg, project_id)

    return _provider


def _fingerprint_factors(cfg: Any) -> dict[str, Any]:
    """当前生效的指纹因子（IFC-IB-156 的入参来源，**全部来自配置**，无隐藏常量）。"""
    return {
        "model_id": cfg.embedding.model_id,
        "dim": cfg.embedding.dim,
        "chunk_size": cfg.chunking.chunk_size,
        "chunk_overlap": cfg.chunking.chunk_overlap,
        "normalizer_version": cfg.chunking.normalizer_version,
        "parser_version": _PARSER_VERSION,
        "schema_version": cfg.collection_schema_version,
    }


#: 解析器实现版本（解析逻辑变更须**手动**递增 —— 它是重建指纹的一个因子，
#: 不递增就会让「换了 PDF 解析路径但没重建」的库处于新旧混排状态）。
_PARSER_VERSION = "pypdf-1"

def _graph_config(cfg: Any, route: Any = None) -> Any:
    """编排图配置（IFC-IB-231）。R7：`max_expert_steps` 优先取自定义文档的路由参数。

    用 `getattr(route, ...)` 而非点取，使「未装配定义文档」的历史路径仍回退到既有常量
    （module_design §7.1：`MAX_EXPERT_STEPS=8`），R1~R6 行为逐位不变。
    """
    from ib.core import GraphConfig

    steps = getattr(route, "max_expert_steps", None)
    max_steps = int(steps) if isinstance(steps, int) and steps >= 1 else 8
    return GraphConfig(
        max_expert_steps=max_steps,
        confirmation_gate_enabled=bool(getattr(cfg, "confirmation_gate_enabled", False)),
        max_history_messages=cfg.session.max_history_messages,
        aggregation_forbids_internal_labels=True,
    )


def _expert_names() -> tuple[str, ...]:
    from ib.experts import names

    return names()


# --------------------------------------------------------------------------- #
# R7 定义文档（单一真源）：装配期准入闸门与派生注入（IFC-IB-288/290/291/293）
# --------------------------------------------------------------------------- #


def admit(doc: Any, *, store: Any | None = None) -> Any:
    """**[IFC-IB-293] 装配期准入闸门**（ADR-16）。

    语义：`validate(doc)`（IFC-IB-290）不通过 → **拒绝装配**，抛出**聚合全部**
    `ValidationErrorItem` 的 `ConfigError`；通过 → `derive(doc)`（IFC-IB-291）返回只读视图。

    **不提供**「强制继续 / 忽略错误」参数，且 `ValidationReport` 在类型层就**无法**表达
    带病继续（ADR-16）—— 因此本闸门不存在绕过路径。

    `store` 省略时取当前已装配 `Deps.definition_store`（供端点复用同一校验器）。
    """
    if store is None:
        deps = get_deps(required=False)
        store = getattr(deps, "definition_store", None)
    if store is None:
        raise StartupError("准入闸门缺少定义文档存储：装配未完成或未注入 definition_store")
    report = store.validate(doc)
    if not report.ok:
        details = "；".join(f"[{item.code}] {item.path}: {item.message}" for item in report.errors)
        err = ConfigError(
            f"定义文档校验不通过（{len(report.errors)} 项），拒绝装配：{details}",
            key="IB_DEFINITION_DOC_PATH",
        )
        # 结构化附带全部校验项，供端点逐条回执（不回显任何凭据值）。
        try:
            err.validation_items = report.errors  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - 附带失败不影响拒绝装配这一主语义
            pass
        raise err
    return store.derive(doc)


def _known_tool_names() -> frozenset[str]:
    """已知工具名集合（由**唯一登记点**派生，供校验器判工具授权合法性）。"""
    from ib.tools import ToolRegistry

    return frozenset(register_builtin_tools(ToolRegistry()).names())


def _default_definition_document(project_id: str, cfg: Any) -> Any:
    """由**既有默认值**构造一份内置默认定义文档（离线 / 未配置路径时的种子）。

    专家取自 `ib.experts.EXPERT_SPECS`（其本身在装配期由定义文档派生 —— 首次装配时即
    内置默认），路由阈值取自 `ib.routing.DEFAULT_TAU/MARGIN`，`max_expert_steps=8`，
    工具授权对全部专家授予 `search_knowledge` —— 与 `Deps.bind_tools` 的实际绑定逐位一致，
    故派生结果 == 既有默认注册表，**不引入行为变化**。
    """
    from ib.config import build_definition_document
    from ib.core import (
        ConditionalEdgeSpec,
        ExpertSpecInput,
        OrchestrationSpecInput,
        RouteSpecInput,
        ToolGrantSpec,
    )
    from ib.experts import EXPERT_SPECS, default_expert
    from ib.routing import DEFAULT_MARGIN, DEFAULT_TAU

    exemplars_map = _load_exemplars(project_id)
    experts = tuple(
        ExpertSpecInput(
            name=spec.name,
            cn_label=spec.cn_label,
            keywords=tuple(spec.keywords),
            exemplars=tuple(exemplars_map.get(spec.name, ())),
            is_data_expert=spec.is_data_expert,
            fallback_prompt=spec.fallback_prompt,
            is_delegating=spec.is_delegating,
            is_default=spec.is_default,
        )
        for spec in EXPERT_SPECS
    )
    route = RouteSpecInput(
        tau=DEFAULT_TAU,
        margin=DEFAULT_MARGIN,
        max_expert_steps=8,
        default_expert=default_expert(),
    )
    orchestration = OrchestrationSpecInput(
        nodes=("route", "expert", "general", "gate", "aggregate"),
        conditional_edges=(
            ConditionalEdgeSpec(
                from_node="route",
                branch_map=(("expert", "expert"), ("general", "general")),
            ),
        ),
    )
    grants = tuple(
        ToolGrantSpec(expert_name=spec.name, tool_names=("search_knowledge",)) for spec in EXPERT_SPECS
    )
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=route,
        orchestration=orchestration,
        tool_grants=grants,
    )


def build_definition_store(cfg: Any, projects: dict[str, ProjectRecord]) -> Any:
    """按配置选择定义文档存储（IFC-IB-288/289 的实现选择）。

    * 离线模式 → `InMemoryDefinitionDocumentStore`（内置默认文档种子）；
    * 非离线且 `IB_DEFINITION_DOC_PATH` 已配置 → `FileDefinitionDocumentStore`（原子写回）；
    * 非离线但**未配置** `IB_DEFINITION_DOC_PATH` → 内存默认文档 + WARN
      （显式记录，**不静默当作空文档** —— 对齐 IFC-IB-288 的「不静默回退」纪律）。
    """
    from ib.config import FileDefinitionDocumentStore, InMemoryDefinitionDocumentStore
    from ib.observability import log_event

    first = next(iter(projects), "")
    known = _known_tool_names()
    path = os.environ.get("IB_DEFINITION_DOC_PATH", "").strip()
    if not cfg.offline_mode and path:
        return FileDefinitionDocumentStore(path, known_tools=known)
    if not cfg.offline_mode and not path:
        log_event(
            "definition_doc",
            "path_not_configured_using_in_memory_default",
            project_id=first,
        )
    # 每项目一份内置默认文档（一个项目一份定义文档，[ARCH-ASSUMPTION-A6]）。
    seeds = {pid: _default_definition_document(pid, cfg) for pid in projects}
    return InMemoryDefinitionDocumentStore(documents=seeds, known_tools=known)


def _inject_derived_experts(
    project_id: str,
    definitions: dict[str, Any],
    derived_views: dict[str, Any],
) -> None:
    """把定义文档派生的专家表注入 MOD-IB-16（R7 装配期派生注入）。

    v1 专家注册表为**进程级单例**，故取**首个项目**的派生结果（多项目定义分歧需独立实例，
    同 `ib.experts.install()` 文档既有口径）。`install_derived` 幂等，重复装配不抛。
    """
    from ib.core import ExpertSpec
    from ib.experts import install_derived

    view = derived_views.get(project_id)
    if view is None:
        return
    specs = [
        ExpertSpec(
            name=e.name,
            cn_label=e.cn_label,
            keywords=tuple(e.keywords),
            is_data_expert=e.is_data_expert,
            fallback_prompt=e.fallback_prompt,
            is_delegating=e.is_delegating,
            is_default=e.is_default,
        )
        for e in view.experts
    ]
    if specs:
        install_derived(specs)


def _build_semantic_router(embedder: Any, project_id: str, route: Any = None) -> Any:
    """构造语义路由（L1）。**没有示例句就返回 `None`** → L1 自动跳过（fail-open，不停机）。

    R7：`tau` / `margin` 优先取自定义文档的路由参数；缺省时用 `ib.routing` 的既有默认常量
    （`DEFAULT_TAU` / `DEFAULT_MARGIN`），故未装配定义文档时行为不变。
    """
    from ib.routing import DEFAULT_MARGIN, DEFAULT_TAU, SemanticRouter

    exemplars = _load_exemplars(project_id)
    if not exemplars:
        return None

    tau = getattr(route, "tau", None)
    margin = getattr(route, "margin", None)
    tau = float(tau) if isinstance(tau, (int, float)) else DEFAULT_TAU
    margin = float(margin) if isinstance(margin, (int, float)) else DEFAULT_MARGIN

    def _embed_texts(texts: list[str]) -> list[list[float]]:
        # 范例与查询必须落在**同一向量空间**，故用同一个 embedder。
        # 冷路径批量接口正合适：范例装载是低频、批量的（不是每请求一次）。
        return [list(vector) for vector in embedder.embed_documents(
            list(texts), timeout_s=30.0, max_retries=1, batch_size=len(texts) or 1
        )]

    return SemanticRouter(
        embed_texts=_embed_texts,
        exemplars_provider=lambda pid: exemplars if pid == project_id else {},
        tau=tau,
        margin=margin,
    )


def _load_exemplars(project_id: str) -> dict[str, list[str]]:
    """示例句来源：配置文件同目录下的 `<project_id>.exemplars.json`（可选）。

    可选而非必填：没有示例句时 L0（关键词）与 L2（LLM）仍能工作，
    语义路由只是「更省一次 LLM 调用」的优化，不该成为启动的硬前提。
    """
    import json
    from pathlib import Path

    path = Path(os.environ.get("IB_EXEMPLARS_DIR", ".")) / f"{project_id}.exemplars.json"
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - 示例句损坏不该阻断启动
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for expert, lines in raw.items():
        if isinstance(lines, list):
            out[str(expert)] = [str(line) for line in lines if str(line).strip()]
    return out


def _backend_summary(cfg: Any) -> str:
    """装配后端摘要（**只含开关名，不含凭据/端点**）。"""
    return (
        f"vectorstore={cfg.vectorstore.backend},embed={cfg.embedding.backend},"
        f"llm={cfg.llm.backend},ledger={cfg.ledger_backend},"
        f"ocr={'on' if cfg.ocr_enabled else 'off'},render={'on' if cfg.render_enabled else 'off'},"
        f"offline={int(bool(cfg.offline_mode))}"
    )


class _CollectionResolver:
    """`CollectionResolver` 端口的进程内实现（薄转发，便于装配期替换与断言）。"""

    def __init__(self) -> None:
        from ib.embedding import CollectionResolver

        self._impl = CollectionResolver()

    def resolve(self, scope: Scope, project: ProjectRecord) -> str:
        return self._impl.resolve(scope, project)

    def assert_prefix(self, collection: str, project_id: str) -> None:
        return self._impl.assert_prefix(collection, project_id)


def resolve_scope(ctx: Any) -> Scope:
    """由请求上下文派生 `Scope`（**唯一**来源是服务端鉴权结论）。

    KB 维度默认 `None`（项目内全部知识库）：v1 不提供「本次只看某个 KB」的入参，
    因为请求体不可信 —— 要支持就该由配置或鉴权结论给出，而不是读请求参数。
    """
    return Scope(project_id=ctx.authz.project_id)
