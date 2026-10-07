"""
@module MOD-IB-23
@implements IFC-IB-241 build_application / build_deps（组合根，module_design §5）
            R2：`related_images` 提供者（命中 → 页面图）在 `orchestrator_for` 内闭包注入
            R7：装配期 fail-fast 准入闸门 admit（IFC-IB-293）；定义文档读写端点
                （IFC-IB-294/295，落在 `ibweb/views.py`）
            IFC-IB-326（R13）：登录限速器的**应用级装配** —— 装配期构建一次存入
                `Deps.login_throttle`，登录端点复用（DEFECT-R13-01 修复）
            IFC-IB-355（REV-16-4）：装配路径改用 `validate_definition_full`（ADR-33 单一入口）
            IFC-IB-360（REV-16-4）：`record_config_audit` 服务 / 用例（第 17 个端口装配注入）
            IFC-IB-362（REV-16-4）：`get_storage_state`（装配期存储态快照）
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

import json
import os
import threading
from dataclasses import dataclass, field, replace
from typing import Any, Sequence

from ib.core import (
    ConfigAuditEntry,
    ConfigError,
    KbRecord,
    ProjectRecord,
    Scope,
    StartupError,
    StorageState,
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
    # REV-16-2（提示词域 / 工具参数；IFC-IB-339 / 340 / 353）
    "build_definition_store",
    "build_prompt_stores",
    "known_tool_param_specs",
    "known_tool_names",
    "admit_two_domains",
    # REV-16-4（配置审计 / 存储态；IFC-IB-360 / 362）
    "record_config_audit",
    "get_storage_state",
    "changed_field_names",
]

#: 基座自带的**唯一**工具：知识库检索（scope 在构造期绑定，见 IFC-IB-183）。
#: 描述文本进入路由提示的能力摘要（IFC-IB-182），故措辞要说清「查什么」而不是「怎么实现」。
#: **不再**在描述里手写「（需要范围绑定）」——`needs_scope=True` 时该后缀由
#: `build_capability_digest` 统一附加；描述里再写一遍会得到重复后缀（R3 修正）。
SEARCH_TOOL_SPEC = ToolSpec(
    name="search_knowledge",
    description="在企业知识库中检索与问题相关的资料片段，返回文件名与位置",
    needs_scope=True,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索关键词或问题，尽量具体、贴近用户原始提问",
            },
        },
        "required": ["query"],
    },
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
    # REV-16-2 提示词域（第二真源，ADR-15-R1）：每项目一份 `ExpertPromptStore`
    # （生产 = 本地 markdown 目录；离线 = 进程内替身）。跨域合并键 = 专家 name。
    prompt_stores: dict[str, Any] = field(default_factory=dict)
    # R13 账户 / 会话存储（第 15 个端口的装配实例；IFC-IB-325）。
    account_store: Any = None
    # REV-16-4 配置审计存储（第 17 个端口的装配实例；IFC-IB-357/358）。
    # **只读审计、非第二真源**（ADR-34）：唯一入口，任何需要「查配置保存记录」的路径
    # 一律经它，**不得**各自读表。
    config_audit_store: Any = None
    # REV-16-4 存储态快照（IFC-IB-361）：**装配期一次性判定**、随后只读 —— 单一来源 =
    # 装配期实际选用的存储实现（IFC-IB-362「直读装配结果，不经第二真源」）。
    storage_state: Any = None
    # R13 登录限速器（IFC-IB-326）：**每应用实例**一份、装配期构建一次并复用。
    # 为什么挂在 Deps 而不是每请求 `build_throttle()`：`LoginThrottle._hits` 是**实例态**，
    # 每请求新建会让来源 IP 的滑动窗口永不累积（DEFECT-R13-01，429 分支不可达）。
    # 为什么不是**进程级全局**：挂在 Deps 上即「每装配实例一份」——每个测试夹具
    # `build_deps(force=True)` 得到全新空窗口，天然保持用例隔离、无跨用例状态泄漏。
    login_throttle: Any = None
    # REV-18 项目注册表（第 18 个端口的装配实例；IFC-IB-367/370）。`Deps.projects` 的
    # **数据源** = `project_registry.list_active()`（ADR-37）；项目 CRUD 端点亦经它。
    project_registry: Any = None
    # REV-18 LLM Key 存储（第 19 个端口的装配实例；IFC-IB-368/371）。**唯一写入口**
    # = `PUT /api/llm-key`；装配期解析为唯一读点。HTTP 层只暴露 `LlmKeyStatus`（不含明文）。
    llm_key_store: Any = None

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

        **REV-16-2**：清单进一步收窄为**本项目定义文档的授权勾选**（ADR-30「最小授权」）——
        经 `build_authorized_tools`（IFC-IB-350）绑定被授权工具并注入工具参数，
        再由 `bind_scope` 完成 scope 闭包注入。默认种子文档对全部专家授予 `search_knowledge`
        且无参数 → 产出与既有「绑定全部已登记工具」逐位一致（不引入行为变化）。
        项目未装配定义文档时回退到既有「绑定全部已登记工具」路径（防御性兼容）。
        """
        from ib.tools import ToolRegistry, bind_scope, build_authorized_tools

        registry = register_builtin_tools(ToolRegistry())
        grants = self._effective_grants(scope.project_id)
        if grants:
            authorized = build_authorized_tools(
                grants, registry=registry, specs=self.tool_param_specs()
            )
            return bind_scope(authorized, scope, self.retrieval)
        return bind_scope(registry.registered(), scope, self.retrieval)

    def _effective_grants(self, project_id: str) -> tuple[Any, ...]:
        """取该项目定义文档的工具授权（无文档 / 无授权 → 空元组，回退既有路径）。"""
        doc = self.definitions.get(project_id)
        return tuple(getattr(doc, "tool_grants", ()) or ())

    def tool_param_specs(self) -> tuple[Any, ...]:
        """可配置工具参数规格（由**唯一登记点**的既有工具声明派生；IFC-IB-340）。"""
        return known_tool_param_specs()

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
    seeded_projects = _seed_projects(cfg, ledger)

    # 2b) REV-18（IFC-IB-370 / ADR-37）：构造**项目注册表**并**幂等首次播种**。
    #     播种以配置为初始数据（`INSERT ... ON CONFLICT DO NOTHING`，**不覆盖既有行**）；
    #     `Deps.projects` 的**数据源由配置快照切换为注册表读出的活动项目**（ADR-37 口径）。
    from ib.ledger import build_project_registry_store

    ledger_path = str(getattr(cfg, "ledger_path", "") or ":memory:")
    project_registry = build_project_registry_store(cfg, ledger_path=ledger_path)
    project_registry.seed(
        _registry_seed_entries(cfg, seeded_projects)
    )
    projects = _projects_from_registry(cfg, ledger, project_registry)

    # 2c) REV-18（IFC-IB-371 / ADR-38 / ADR-39 Option C）：构造 **LLM Key 存储**，
    #     装配期经 `get()` → `resolve_secret()` 解析（**唯一读点**）。缺 Key **不再致命**。
    from ib.ledger import build_llm_key_store

    llm_key_store = build_llm_key_store(cfg, ledger_path=ledger_path)
    llm_key_record = llm_key_store.get()
    resolved_llm_key = llm_key_record.secret if llm_key_record is not None else None

    # 3) 适配器
    vectors = build_vector_store(cfg)
    embedder = build_embedder(cfg)
    blobs = build_blob_store(cfg)
    ocr = build_ocr_engine(enabled=cfg.ocr_enabled)
    renderer = build_page_renderer(enabled=cfg.render_enabled)
    llm = build_llm_provider(cfg, api_key=resolved_llm_key)
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

    # 4d) R13 账户 / 会话（IFC-IB-325）：构造 AccountStore → 幂等种子 → 注入策略模块。
    from ib.ledger import build_account_store
    from ibweb.accounts import load_account_settings

    account_settings = load_account_settings()
    account_store = build_account_store(
        cfg, ledger_path=str(getattr(cfg, "ledger_path", "") or ":memory:")
    )
    _seed_accounts(account_store, account_settings, offline=bool(cfg.offline_mode))

    # 4d-2) REV-16-4 配置审计（IFC-IB-357/358；ADR-34）：与台账**同一 SQLite 文件**、
    #       与账户存储同一条「sqlite 构造失败不静默降级」纪律（审计不可用须 fail-closed）。
    from ib.ledger import build_config_audit_store

    config_audit_store = build_config_audit_store(
        cfg, ledger_path=str(getattr(cfg, "ledger_path", "") or ":memory:")
    )

    # 4e) R13 登录限速（IFC-IB-326 / DEFECT-R13-01）：**装配期构建一次、按请求复用**。
    #     为什么必须在组合根构建：`LoginThrottle` 的滑动窗口计数器 `_hits` 是**实例状态**，
    #     若在每个请求内 `build_throttle()` 新建，则每次都得到空窗口、计数永不累积，
    #     429 分支不可达（来源 IP 维度限速失效）。构建结果存入 `Deps.login_throttle`
    #     （= 每应用实例一份），登录端点经 `_login_throttle()` 取用。
    #     未配置 `IB_LOGIN_MAX_FAILURES` 时 `build_throttle()` 返回 `None` → 不启用（ADR-27）。
    from ibweb.accounts.throttle import build_throttle

    login_throttle = build_throttle()

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
    # 4c-2) REV-16-2 提示词域（第二真源；ADR-15-R1）：装载独立提示词目录（IFC-IB-345）。
    #       序列（IFC-IB-353）：装载定义文档 → 装载提示词目录 → 跨域合并 + 完备性校验
    #       （290 扩展 + 345 + 346）→ 准入闸门（293）→ 派生（291 扩展，含 347 + 349）。
    prompt_stores = build_prompt_stores(cfg, projects)
    tool_specs = known_tool_param_specs()
    definitions: dict[str, Any] = {}
    derived_views: dict[str, Any] = {}
    for project_id in projects:
        doc = definition_store.load(project_id)  # IFC-IB-288
        prompt_store = prompt_stores.get(project_id)
        prompt_refs = prompt_store.list_refs() if prompt_store is not None else ()  # IFC-IB-345
        view = admit_two_domains(  # IFC-IB-353（290 扩展 + 345 + 346 + 347）
            doc,
            store=definition_store,
            prompt_refs=prompt_refs,
            tool_specs=tool_specs,
        )
        definitions[project_id] = doc
        derived_views[project_id] = view
    _inject_derived_experts(next(iter(projects), ""), definitions, derived_views)
    _inject_prompt_bundles(next(iter(projects), ""), derived_views)

    # 4c-3) REV-16-4 存储态快照（IFC-IB-361/362；ADR-35）：**装配期一次性判定**，
    #       来源 = 上面**实际选用**的 definition_store / prompt_stores（直读装配结果，
    #       不经第二真源）。**只暴露**存储态，**不改变**「保存 + 重启重装配」生效口径。
    storage_state = _derive_storage_state(definition_store, prompt_stores)

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
        prompt_stores=prompt_stores,
        account_store=account_store,
        config_audit_store=config_audit_store,
        project_registry=project_registry,
        llm_key_store=llm_key_store,
        storage_state=storage_state,
        login_throttle=login_throttle,
    )
    log_event(
        "startup",
        "succeeded",
        project_id=first_project,
        backend=_backend_summary(cfg),
        # REV-18（ADR-39 ③）：启动日志**显式声明 LLM 是否已配置**（仅布尔，**不含任何 Key 值**）。
        # 缺 Key 非致命故此处仍 `succeeded`；`llm_configured=false` 是运维排障的第一线索。
        llm_configured=bool(resolved_llm_key),
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
        # REV-18：注册表 / LLM Key 后端一并切到内存替身（离线零外部 IO）。
        project_registry_backend="memory",
        llm_key_backend="memory",
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
        # REV-18（IFC-IB-375 / ADR-41）：项目域资料上传以 `kb_id ≡ project_id` 推导 kb，
        # 故须为每个项目登记一个 `kb_id == project_id` 的知识库行（归属断言的判定依据）。
        ledger.upsert_kb(
            KbRecord(kb_id=project_id, project_id=project_id, name=project_id, created_at="")
        )
        out[project_id] = record
    return out


def _registry_seed_entries(cfg: Any, seeded: dict[str, ProjectRecord]) -> list[Any]:
    """由已播种的台账项目派生**注册表首次播种**条目（IFC-IB-370；ADR-37）。

    以 `IB_CONFIG_FILE.projects.<id>` 为初始数据（沿用 `_seed_projects` 语义）；
    状态一律 `active`（新建项目默认启用）。**不携带任何凭据 / 配置取值**。
    """
    from ib.core import ProjectRegistryEntry
    from ib.context import utc_now_iso

    entries: list[Any] = []
    for project_id, record in seeded.items():
        now = getattr(record, "created_at", "") or utc_now_iso()
        entries.append(
            ProjectRegistryEntry(
                project_id=project_id,
                name=getattr(record, "name", project_id) or project_id,
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
    return entries


def _projects_from_registry(cfg: Any, ledger: Any, registry: Any) -> dict[str, ProjectRecord]:
    """由**注册表活动项目**派生 `Deps.projects`（ADR-37 数据源口径切换）。

    排序纪律：**先按 `cfg.projects` 的声明序，再按 `project_id` 升序**补足运行期新建项目
    —— 既保留既有「配置首项目」（`first_project`）语义，又使运行期 CRUD 新建的项目
    出现在「项目枚举 / 切换器」中。台账侧列（collection 版本 / 嵌入规格）从**同一张
    `projects` 表**读出；缺失时回退配置的全局嵌入规格。
    """
    entries = {entry.project_id: entry for entry in registry.list_active()}
    ordered = [pid for pid in cfg.projects if pid in entries]
    ordered += [pid for pid in sorted(entries) if pid not in set(ordered)]
    out: dict[str, ProjectRecord] = {}
    for project_id in ordered:
        entry = entries[project_id]
        record = ledger.get_project(project_id) if hasattr(ledger, "get_project") else None
        out[project_id] = ProjectRecord(
            project_id=project_id,
            name=getattr(entry, "name", project_id) or project_id,
            active_collection_version=getattr(record, "active_collection_version", "") or "1",
            embedding_model_id=getattr(record, "embedding_model_id", "") or cfg.embedding.model_id,
            dim=int(getattr(record, "dim", 0) or cfg.embedding.dim),
            created_at=getattr(record, "created_at", "") or entry.created_at,
        )
    return out


def _seed_accounts(store: Any, settings: Any, *, offline: bool) -> None:
    """幂等播种默认管理员（IFC-IB-314 / IFC-IB-325）。

    口令 hash 由 `IB_DEFAULT_ADMIN_PASSWORD`（0600 EnvironmentFile）经 bcrypt 产生；
    **口令值只在此处短暂存在，绝不写入日志 / 响应 / 返回值**。

    fail-closed 口径：
      * 生产：账户体系已启用但**既无管理员、又未提供初始口令** → `StartupError`
        （否则「配了登录页却没人能登录」是比启动失败更难排障的形态）；
      * 离线：允许缺席（离线自测走 `EnvTokenResolver`，不需要真实账户）；
      * 已有管理员：缺席初始口令不报错（幂等播种本就不覆盖既有口令）。
    """
    password = os.environ.get("IB_DEFAULT_ADMIN_PASSWORD", "")
    try:
        has_admin = any(getattr(user, "role", "") == "admin" for user in store.list_users(None))
    except Exception:  # noqa: BLE001 - 探测失败按「无管理员」处理，交由下面的分支决定
        has_admin = False
    if not password:
        if offline or has_admin:
            return
        raise StartupError(
            "缺少必填环境变量 IB_DEFAULT_ADMIN_PASSWORD（账户体系已启用但尚无管理员账户）。"
            "该值只允许经 0600 EnvironmentFile 注入；只登记键名，不回显值。"
        )
    from ib.ledger import hash_password, seed_default_admin

    seed_default_admin(
        store,
        username=settings.default_admin_username,
        password_hash=hash_password(password),
    )


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

    **REV-16-2**：本函数签名**刻意保持不变**（既有合法性用例逐字断言 `{doc, store}`，且该
    断言保护「不存在 force/ignore/warn_only 绕过」这一类型层事实）。两域聚合准入闸门见
    `admit_two_domains`（IFC-IB-353），本函数仍是其第一段（定义文档域）。
    """
    if store is None:
        deps = get_deps(required=False)
        store = getattr(deps, "definition_store", None)
    if store is None:
        raise StartupError("准入闸门缺少定义文档存储：装配未完成或未注入 definition_store")
    report = store.validate(doc)
    if not report.ok:
        _raise_admission_error(report.errors)
    return store.derive(doc)


def admit_two_domains(
    doc: Any,
    *,
    store: Any | None = None,
    prompt_refs: Any = (),
    tool_specs: Any = (),
    builtin_fallbacks: Any = None,
) -> Any:
    """**[IFC-IB-353 装配序列] 两域聚合准入闸门 + 跨域派生**（REV-16-2）。

    聚合两段校验（任一段不通过即**拒绝装配**，一次性回执**全部**错误）：
      1. 定义文档域 + 工具参数域 + 提示词目录域：`validate_two_domains`
         （IFC-IB-364 = 355 ∪ 345，**与保存路径同一校验入口**，ADR-33 / ADR-36）；
      2. —— 原第 2 段已并入第 1 段，不再单独调用。

    通过后经 `derive_prompt_layers`（IFC-IB-347）产出**跨域合并**的只读派生视图
    （定义文档专家 `name` ↔ 提示词目录子目录按 name join；`DerivedView.prompt_bundles`）。

    **不提供**「强制继续 / 忽略错误」路径（沿用 ADR-16）；`ValidationReport` 的类型层事实不变。

    **REV-16-4（ADR-33）**：第 1 段改用合成纯函数 `validate_definition_full`，
    使**装配路径**与**保存路径**（`PUT /api/config/definition`）的校验集**不再发散**
    （结构性消除 DEFECT-R16-02 根因：保存期漏掉 IFC-IB-346 的工具参数校验）。
    `known_tools` 取**唯一登记点**的工具名集合（与 `build_definition_store` 注入给存储的
    集合同源），故工具名校验语义不变。

    **REV-17（ADR-36）**：改用 `validate_two_domains`，把**提示词域**也拉进这**同一个**
    入口 —— 此前提示词域只在装配期校验，保存期不查，于是「页面上存得下、重启装配才炸」
    成为可能。现在保存与装配共用一条判据、**同序同条**。
    `builtin_fallbacks` 为 `None` 时按 `ib.experts.builtin_fallbacks_for(doc 专家名)` 取，
    保证内置安全网在两条路径上**同源**。
    """
    if store is None:
        deps = get_deps(required=False)
        store = getattr(deps, "definition_store", None)
    if store is None:
        raise StartupError("准入闸门缺少定义文档存储：装配未完成或未注入 definition_store")
    from ib.config import derive_prompt_layers, validate_two_domains

    if builtin_fallbacks is None:
        builtin_fallbacks = builtin_fallbacks_of(doc)

    # IFC-IB-364：定义文档域（290）∪ 工具参数域（346）∪ 提示词目录域（345）；
    # 与保存路径同一入口（ADR-33 / ADR-36）。
    report = validate_two_domains(
        doc,
        known_tools=_known_tool_names(),
        tool_param_specs=tuple(tool_specs),
        prompt_refs=prompt_refs,
        builtin_fallbacks=builtin_fallbacks,
    )
    if report.errors:
        _raise_admission_error(report.errors)
    return derive_prompt_layers(  # IFC-IB-347
        doc, prompt_refs, builtin_fallbacks=builtin_fallbacks
    )


def builtin_fallbacks_of(doc: Any) -> dict[str, str]:
    """给一份定义文档解析**完备**的内置兜底映射（REV-17 / ADR-36）。

    `ibweb` 内**唯一**的安全网取用点：装配路径（`admit_two_domains`）、保存路径
    （`PUT /api/config/definition`）与端点单专家查询（`_doc_fallback_of` 的替代）
    都必须经此处，杜绝三处各自拼默认值而漂移。

    值恒非空（自定义专家回落 `BUILTIN_FALLBACK_DEFAULT`），故下游 `ib.config` 侧
    只需 `mapping.get(name, "")` 即可，**无需知道通用兜底常量的存在**。
    """
    from ib.experts import builtin_fallbacks_for

    return builtin_fallbacks_for([str(getattr(e, "name", "")) for e in getattr(doc, "experts", ()) or ()])


def _raise_admission_error(errors: Any) -> None:
    """聚合全部校验项为一次拒绝（**不静默放行**；错误体不回显任何凭据值）。"""
    errors = tuple(errors)
    details = "；".join(f"[{item.code}] {item.path}: {item.message}" for item in errors)
    err = ConfigError(
        f"定义文档校验不通过（{len(errors)} 项），拒绝装配：{details}",
        key="IB_DEFINITION_DOC_PATH",
    )
    # 结构化附带全部校验项，供端点逐条回执（不回显任何凭据值）。
    try:
        err.validation_items = errors  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - 附带失败不影响拒绝装配这一主语义
        pass
    raise err


# --------------------------------------------------------------------------- #
# REV-16-4 配置审计与存储态（IFC-IB-360 / 362；ADR-34 / ADR-35）
# --------------------------------------------------------------------------- #


def changed_field_names(previous: Any, current: Any) -> tuple[str, ...]:
    """两个定义文档之间的**变更字段名**（IFC-IB-360）。

    **只出字段名 / 结构路径，绝不含任何取值**（ADR-34 / SC-3）：返回如
    `("route.tau", "tool_grants[0].param_values[1]")` 的稳定升序元组。
    `content_hash` / `updated_at` 是**非语义字段**（哈希随内容变、时间戳随保存变），
    一律排除 —— 否则每次保存都会把这两项报成「变更」，审计噪声淹没真正的变更。

    `previous is None`（首次落盘）时，全部语义字段都算「新增」。
    """
    from ib.config import document_to_json

    non_semantic = ("content_hash", "updated_at")

    def _normalize(doc: Any) -> dict[str, Any]:
        if doc is None:
            return {}
        data = json.loads(document_to_json(doc))
        return {key: value for key, value in data.items() if key not in non_semantic}

    return tuple(_diff_field_paths(_normalize(previous), _normalize(current), ""))


def _diff_field_paths(left: Any, right: Any, path: str) -> list[str]:
    """递归求**字段路径**差异（纯结构；列表用下标，字典用键名，绝不落取值）。"""
    out: list[str] = []
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}" if path else str(key)
            if key not in left or key not in right:
                out.append(child)
            else:
                out.extend(_diff_field_paths(left[key], right[key], child))
        return out
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            out.append(path)
        for index, (item_left, item_right) in enumerate(zip(left, right)):
            child = f"{path}[{index}]" if path else f"[{index}]"
            out.extend(_diff_field_paths(item_left, item_right, child))
        return out
    if left != right:
        out.append(path)
    return out


def record_config_audit(entry: ConfigAuditEntry, *, deps: Any = None) -> None:
    """配置审计写入（IFC-IB-360 的服务 / 用例；落在 MOD-IB-23）。

    **审计写与配置写非事务耦合**（ADR-34）：本函数**永不**向调用方抛异常 ——
    审计写失败**不改变**保存结果，但**不静默**：发结构化 `WARN config_audit_write_failed`
    （字段白名单）。审计表**只读审计、非第二真源**（IFC-IB-357）。

    单一入口纪律：审计恒经 `Deps.config_audit_store`（组合根装配注入），**不**各自读表。
    """
    if deps is None:
        deps = get_deps(required=False)
    store = getattr(deps, "config_audit_store", None)
    if store is None:
        # 未装配审计存储：不静默（否则「审计悄悄没写」正是 GAP-R16-04 的原始症状）。
        _warn_audit_write_failed(getattr(entry, "project", None))
        return
    try:
        store.record(entry)
    except Exception:  # noqa: BLE001 - 审计写失败**不得**改变保存结果（非事务耦合）
        _warn_audit_write_failed(getattr(entry, "project", None))


def _warn_audit_write_failed(project_id: str | None) -> None:
    """结构化 WARN（字段白名单；不静默，也不改变保存结果）。

    **本函数自身不得抛异常**（DEFECT-R16-4-01）：它只在「审计写失败」这条
    **旁路**上被调用，而 `record_config_audit` 的契约是**永不**向调用方抛异常
    （ADR-34 / IFC-IB-360）。若本函数自身抛错，旁路会反噬保存结果 —— 已落盘的
    成功保存会被报成 500，被拒保存会被报成 500 而非 400。

    为此两处收口：
      * `log_event` 按本文件既有约定**函数内局部导入**（同 `_assemble` L449 /
        `build_definition_store` L1130），避免模块级未定义（原缺陷即 `NameError`）；
      * 导入与打点**整段 try/except 兜底**：即便日志后端自身抛错，也只吞掉、
        绝不逸出。「不静默」以**尝试打点**为准，而非「打点必成功」。

    字段白名单不变：`project_id` / `error_code` / `level`（**不落任何配置取值**）。
    """
    try:
        from ib.observability import log_event

        log_event(
            "config_audit",
            "config_audit_write_failed",
            project_id=project_id,
            error_code="config_audit_write_failed",
            level="WARN",
        )
    except Exception:  # noqa: BLE001 - 打点自身失败亦不得逸出（旁路永不反噬保存结果）
        pass


def get_storage_state(*, deps: Any = None) -> StorageState:
    """当前存储态（IFC-IB-362；`GET /api/config/storage-state` 的只读来源）。

    **单一来源 = 装配期实际选用的存储实现**（IFC-IB-361 / 362）：直读装配结果
    （`Deps.storage_state` 在 `_assemble` 一次性判定），**不**在请求期从环境变量
    重新推断（否则「实际跑在内存替身」与「端点自称文件态」可能不一致）。
    """
    if deps is None:
        deps = get_deps()
    state = getattr(deps, "storage_state", None)
    if state is not None:
        return state
    # 防御性兜底：理论上装配后恒有；此处按实际存储实例即时派生（语义等价）。
    return _derive_storage_state(
        getattr(deps, "definition_store", None),
        getattr(deps, "prompt_stores", None) or {},
    )


def _derive_storage_state(
    definition_store: Any, prompt_stores: dict[str, Any]
) -> StorageState:
    """由**实际存储实例**派生 `StorageState`（装配期调用一次；IFC-IB-361）。"""
    from ib.config import FileDefinitionDocumentStore, FsExpertPromptStore

    definition_mode = (
        "file" if isinstance(definition_store, FileDefinitionDocumentStore) else "memory"
    )
    prompt_instances = list(prompt_stores.values())
    if prompt_instances and all(isinstance(s, FsExpertPromptStore) for s in prompt_instances):
        prompt_mode = "file"
    else:
        prompt_mode = "memory"
    return StorageState(
        definition_store=definition_mode,  # type: ignore[arg-type]
        prompt_store=prompt_mode,  # type: ignore[arg-type]
        # 「是否已配置」= 对应键名是否提供了非空值（只登记键名，不回显值）。
        definition_store_configured=bool(os.environ.get("IB_DEFINITION_DOC_PATH", "").strip()),
        prompt_store_configured=bool(os.environ.get("IB_EXPERT_PROMPT_DIR", "").strip()),
    )


def _known_tool_names() -> frozenset[str]:
    """已知工具名集合（由**唯一登记点**派生，供校验器判工具授权合法性）。"""
    from ib.tools import ToolRegistry

    return frozenset(register_builtin_tools(ToolRegistry()).names())


def known_tool_names() -> tuple[str, ...]:
    """**既有**工具名（有序），供配置页渲染「工具授权勾选」（ADR-30）。

    勾选**只作用于既有工具集合**，不新增工具本体；名单与装配期校验、运行期绑定同源
    （`register_builtin_tools` 唯一登记点），故不可能出现「界面可勾、装配期不认」的漂移。
    """
    return tuple(sorted(_known_tool_names()))


def known_tool_param_specs() -> tuple[Any, ...]:
    """可配置工具参数规格（IFC-IB-340）：由**唯一登记点**的既有工具 JSON Schema 派生。

    **只覆盖既有工具的既有参数**，不新增工具本体（ADR-30）；派生（而非手写）使规格集与
    工具声明不可能漂移。装配期 `admit` 与端点 / 前端均消费同一份规格。
    """
    from ib.tools import ToolRegistry, derive_tool_param_specs

    return derive_tool_param_specs(register_builtin_tools(ToolRegistry()))


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
        EdgeSpec,
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
        # 普通边**逐条镜像**运行期图（`ib/orchestration` 的 add_edge，见该模块 `_compile_graph`）。
        # 少了这组边，配置页的编排图只剩条件边，`gate` / `aggregate` 会渲染成孤立方块 ——
        # 那正是「文档描述不全」的表现。此处与运行期的一致性由
        # `tests/unit/test_orchestration_edges_consistency.py` 把守（防止两处悄悄漂移）。
        # 注意 `general` **绕过** `gate` 直连 `aggregate`：确认门只作用于 expert 支路。
        edges=(
            EdgeSpec(from_node="START", to_node="route"),
            EdgeSpec(from_node="expert", to_node="gate"),
            EdgeSpec(from_node="gate", to_node="aggregate"),
            EdgeSpec(from_node="general", to_node="aggregate"),
            EdgeSpec(from_node="aggregate", to_node="END"),
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
    from ib.experts import BUILTIN_FALLBACKS
    from ib.observability import log_event

    first = next(iter(projects), "")
    known = _known_tool_names()
    path = os.environ.get("IB_DEFINITION_DOC_PATH", "").strip()
    if not cfg.offline_mode and path:
        # REV-17（ADR-36）：注入**全名域**内置兜底映射，供 `load()` 处置旧文档残留的
        # `fallback_prompt` 键（与内置一致 → 静默丢弃；不一致 → fail-closed 并给出迁移路径）。
        return FileDefinitionDocumentStore(
            path, known_tools=known, builtin_fallbacks=BUILTIN_FALLBACKS
        )
    if not cfg.offline_mode and not path:
        log_event(
            "definition_doc",
            "path_not_configured_using_in_memory_default",
            project_id=first,
        )
    # 每项目一份内置默认文档（一个项目一份定义文档，[ARCH-ASSUMPTION-A6]）。
    seeds = {pid: _default_definition_document(pid, cfg) for pid in projects}
    return InMemoryDefinitionDocumentStore(documents=seeds, known_tools=known)


def build_prompt_stores(cfg: Any, projects: dict[str, ProjectRecord]) -> dict[str, Any]:
    """构造每项目的 `ExpertPromptStore`（IFC-IB-339 的实现选择；ADR-15-R1 第二真源）。

    * **离线模式 / 未配置 `IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED=false`**
      → `InMemoryExpertPromptStore`（进程内替身，无提示词文件 → 生效提示词取**代码内置
      兜底**；REV-17 / ADR-36 起定义文档已不承载提示词文本）；
    * 非离线且 `IB_EXPERT_PROMPT_DIR` 已配置 → `FsExpertPromptStore`（本地 markdown 目录，
      原子写回 + 语义哈希乐观并发）。

    **只登记键名，不读取 / 不回显任何凭据**（`IB_EXPERT_PROMPT_DIR` 是路径而非机密）。
    """
    from ib.config import (
        FsExpertPromptStore,
        InMemoryExpertPromptStore,
        prompt_domain_enabled,
    )

    root = os.environ.get("IB_EXPERT_PROMPT_DIR", "").strip()
    enabled = prompt_domain_enabled()
    use_fs = (not cfg.offline_mode) and bool(root) and enabled
    stores: dict[str, Any] = {}
    for project_id in projects:
        if use_fs:
            stores[project_id] = FsExpertPromptStore(root, project_id)
        else:
            stores[project_id] = InMemoryExpertPromptStore(project_id)
    return stores


def _inject_prompt_bundles(project_id: str, derived_views: dict[str, Any]) -> None:
    """把跨域合并派生的提示词分层结果注入 MOD-IB-16（IFC-IB-349；幂等）。

    同 `_inject_derived_experts`：注册表是进程级单例，取**首个项目**的派生结果。
    """
    from ib.experts import install_prompt_bundles

    view = derived_views.get(project_id)
    if view is None:
        return
    bundles = tuple(getattr(view, "prompt_bundles", ()) or ())
    if bundles:
        install_prompt_bundles(bundles)


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
    from ib.experts import builtin_fallback_for, install_derived

    view = derived_views.get(project_id)
    if view is None:
        return
    specs = [
        ExpertSpec(
            name=e.name,
            cn_label=e.cn_label,
            keywords=tuple(e.keywords),
            is_data_expert=e.is_data_expert,
            # REV-17（ADR-36）：定义文档已不承载提示词文本，兜底据此从**代码内置安全网**
            # 取（`_DEFAULT_SPECS` 派生 → 自定义专家回落 `BUILTIN_FALLBACK_DEFAULT`）。
            # 与 `derive_prompt_layers` 的合并、`validate_prompt_directory` 的判据**同源**。
            fallback_prompt=builtin_fallback_for(e.name),
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
