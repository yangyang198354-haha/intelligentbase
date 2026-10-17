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
            REV-19（AC-IB-41-04 / ADR-47 / IFC-IB-380）：`orchestrator_for` 的专家域
                fail-closed 路径**并发结构化日志** `log_event("expert_domain", …)`（含
                项目标识与原因；不含任何凭据 / 提示词正文）；**fail-closed 语义一字不动**
@depends MOD-IB-01 ~ MOD-IB-22
@author software-developer

**唯一装配点**（module_design §5 的组合根装配表在本文件的 `build_deps` 里逐行兑现）。

## 这个文件为什么必须是唯一入口

「哪个后端被用上了」这件事，如果分散在多处判断，就会出现**只有生产才成立的组合**：
例如开发用内存台账（重启即丢）、生产用 SQLite 台账，而某处代码却在启动期假定台账一定有行。
把所有 `IB_*_BACKEND` 分支收在一个函数里，装配结果就变成**一个可打印、可断言的对象**
（`Deps`），排障时直接看它，而不是靠猜。

## 启动期做三件「宁可在启动时失败」的事

1. **必填校验**（`validate_required`）：缺 `IB_EMBED_URL` / `IB_QDRANT_URL` 之类的错误，若推迟到
   首个请求，表现是「用户上传后卡住」；启动即失败则 systemd 会重试并给出清晰的键名。
   **REV-18 订正**：此处原举例为 `IB_LLM_API_KEY`，但该键自 ADR-39 Option C 起**已不在启动必填之列**
   （Key 载体改为 DB；沿用旧口径会造成「首启死锁」）—— 详见 `ib/config/__init__.py::validate_required`。
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
    DependencyUnavailableError,
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

    def reload_projects(self) -> None:
        """热重载项目快照：CRUD 后立即刷新并重建编排器缓存，无需重启服务。

        **同时补齐装配期一次性构建的每项目工件**（`prompt_stores` / `definitions` /
        `derived_views`）：此前只刷新 `projects`，导致热登记项目在 `prompt_stores` 中缺条目，
        `/api/config/prompts` 对该项目 fail-closed 返回 503（定义文档因经单实例存储按需读取
        而不受影响，故此前表现为「配置页提示词区不可用、定义页正常」）。

        **同时补齐台账侧的项目行与知识库行**（`kb_id == project_id`）：缺行会让该项目的
        资料上传被归属断言拦成 403（详见 `_ensure_project_ledger_rows`）。
        """
        fresh = _projects_from_registry(self.cfg, self.ledger, self.project_registry)
        _ensure_collections(self.vectors, self.collections, fresh)
        # 运行期新建项目同样需要台账的 `projects` 行与 `kb_id == project_id` 的知识库行，
        # 否则该项目的资料上传恒 403（`_seed_projects` 只覆盖 `cfg.projects`）。
        _ensure_project_ledger_rows(self.ledger, fresh)
        with self._lock:
            self.projects = fresh
            self._orchestrators = {}
        self._sync_project_artifacts(fresh)

    def _sync_project_artifacts(self, projects: dict[str, ProjectRecord]) -> None:
        """把每项目工件收敛到当前快照（`reload_projects` 专用；装配序列见 `_assemble`）。

        * `prompt_stores`：**整表重建**（构造无 I/O，顺带剔除已不在快照的项目）；
        * `definitions` / `derived_views`：**只补缺失项目**，走与装配期**同一个**
          「装载 → 提示词引用 → 两域准入 → 派生」序列；已装配项目**不重跑**
          （不重复注入派生视图、不重读文件），故热重载对在跑项目零扰动。

        定义文档**装载不到**的项目（如未配置 `IB_DEFINITION_DOC_PATH` 时定义域取内存默认，
        新项目在装配期存储里无文档）→ **不静默**：记 ERROR 级结构化日志后跳过该项目的
        `definitions` / `derived_views` 补充，**绝不**把「项目创建 / 改名」变成 500
        （`orchestrator_for` 对缺派生视图已有显式防御性回落）。
        """
        self.prompt_stores = build_prompt_stores(self.cfg, projects)
        tool_specs = known_tool_param_specs()
        for project_id in projects:
            if project_id in self.definitions:
                continue
            try:
                doc, view = _load_and_admit(
                    self.definition_store, self.prompt_stores.get(project_id), project_id, tool_specs
                )
            except ConfigError:
                from ib.observability import log_event

                log_event(
                    "definition_doc",
                    "reload_skipped_unloadable_project",
                    project_id=project_id,
                    reason="definition_document_unavailable",
                    level="ERROR",
                )
                continue
            self.definitions[project_id] = doc
            self.derived_views[project_id] = view

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
            # REV-19（AC-IB-41-04 / module_design §13 / ADR-47）：专家域 fail-closed **拒绝**时
            # **并发结构化日志**（含项目标识与原因，**不含任何凭据 / 提示词正文**），
            # 级别 ERROR（§13 明列）。`reason` 为**结构化短码**而非自由正文。
            # 打点**不改** fail-closed 语义：仍抛 `StartupError`、**不回退**其他项目作用域。
            from ib.observability import log_event

            log_event(
                "expert_domain",
                "failclosed",
                project_id=project_id,
                reason="unregistered_project",
                level="ERROR",
            )
            raise StartupError(f"项目未在配置中登记：{project_id}（不得回退到其他项目的作用域）")
        scope = Scope(project_id=project_id)
        bound_tools = self.bind_tools(scope)

        from ib.core import ExpertRegistryError
        from ib.experts import resolve_expert_registry
        from ib.orchestration import build_graph
        from ib.routing import IntentRouter

        # R7：图配置 / 路由阈值一律取自**已准入的定义文档**（单一真源，ADR-15）；
        #     未装配定义文档时回退既有常量（与 R1~R6 行为逐位一致）。
        route = getattr(self.definitions.get(project_id), "route", None)

        # REV-19（ADR-43 / ADR-47）：**本项目**专家集取自本项目派生视图 —— 进程级全局
        # `EXPERT_SPECS` **退出生产装配主路径**（消除跨项目泄漏）。未见派生视图（防御性 /
        # 离线）时回退既有全局默认，行为与 R1~R18 逐位一致。解析 fail-closed（IFC-IB-380）。
        project_view = self.derived_views.get(project_id)
        if project_view is not None:
            try:
                registry = resolve_expert_registry(project_id, view=project_view)
            except ExpertRegistryError as exc:
                # IFC-IB-380 fail-closed：**构造 `ExpertRegistryView` 失败**（空专家集 /
                # 默认专家缺失或非唯一）→ **结构化日志 + 原样重抛**（fail-closed 语义一字不动，
                # **不回退**全局默认、**不回退**其他项目）。`reason` 取异常自带的结构化短码。
                from ib.observability import log_event

                log_event(
                    "expert_domain",
                    "failclosed",
                    project_id=project_id,
                    reason=str(getattr(exc, "reason", "") or "expert_registry_invalid"),
                    level="ERROR",
                )
                raise
            expert_specs = registry.experts
            expert_names = registry.names()
        else:
            from ib.experts import EXPERT_SPECS

            registry = None
            expert_specs = tuple(EXPERT_SPECS)
            expert_names = _expert_names()

        # L1 语义路由的向量化走 embedding 热路径；失败时 SemanticRouter 自己吞掉（fail-open）
        semantic = _build_semantic_router(self.embedder, project_id, route)
        router = IntentRouter(llm_provider=self.llm, semantic=semantic, experts=registry)
        graph = build_graph(
            llm=self.llm,
            experts=expert_specs,
            tools=bound_tools,
            sessions=self.sessions,
            config=_graph_config(self.cfg, route),
            router=router,
            scope=scope,
            tools_by_expert={name: bound_tools for name in expert_names},
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


def _load_and_admit(
    definition_store: Any,
    prompt_store: Any,
    project_id: str,
    tool_specs: Any,
) -> tuple[Any, Any]:
    """单项目「装载定义文档 → 取提示词引用 → 两域准入 → 派生只读视图」。

    装配期（`_assemble` 4c-2）与热重载（`Deps._sync_project_artifacts`）**共用本序列**，
    避免两条路径漂移（同 `admit_two_domains` 的「唯一入口」纪律）。
    """
    doc = definition_store.load(project_id)  # IFC-IB-288
    prompt_refs = prompt_store.list_refs() if prompt_store is not None else ()  # IFC-IB-345
    view = admit_two_domains(  # IFC-IB-353（290 扩展 + 345 + 346 + 347）
        doc,
        store=definition_store,
        prompt_refs=prompt_refs,
        tool_specs=tool_specs,
        prompt_store=prompt_store,
    )
    _log_prompt_sources(project_id, view)
    return doc, view


def _log_prompt_sources(project_id: str, view: Any) -> None:
    """**IFC-IB-392 / ADR-48 决定 4**：装配期发出 `prompt_source` 结构化日志（**不含正文**）。

    为什么必须打这条：生效提示词来源收窄为 `{main_file, fallback_file}` 后，「回落
    `fallback_file`」是**语义降级**（main.md 缺失或未落盘），ADR-48 明文要求它**不得静默**
    —— 否则运维只看到「答得还行」，看不出「主提示词其实没生效」（对齐 REQ-NFR-IB-22）。
    字段只出 `project_id` / `expert` / `source`（结构化短码），**不回显任何提示词正文**。
    """
    from ib.observability import log_event

    for bundle in tuple(getattr(view, "prompt_bundles", ()) or ()):
        log_event(
            "prompt_source",
            "resolved_from",
            project_id=project_id,
            expert=bundle.expert_name,
            source=bundle.resolved_from,
        )


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
    # 3c) 逐项目补齐台账项目行 + 知识库行（IFC-IB-130 归属断言的判定依据；幂等）
    _ensure_project_ledger_rows(ledger, projects)

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
        doc, view = _load_and_admit(
            definition_store, prompt_stores.get(project_id), project_id, tool_specs
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


def _ensure_project_ledger_rows(ledger: Any, projects: dict[str, ProjectRecord]) -> None:
    """逐项目补齐台账侧的 `projects` 行与 `kb_id == project_id` 的知识库行（**幂等**）。

    REV-18（IFC-IB-375 / ADR-41）起，项目域资料上传的 kb 由主体 `project_id` **推导**
    （`kb_id ≡ project_id`），服务端以台账 `kbs` 表做归属断言
    （`assert_kb_in_project` → 失败抛 `ScopeViolationError` → HTTP **403**）。

    这两行**只**在 `_seed_projects` 里按 **`cfg.projects`** 登记；而 ADR-37 之后
    `Deps.projects` 的数据源是**注册表活动项目** —— 运行期经 `POST /api/projects`
    新建的项目不在 `cfg.projects` 里 ⇒ 台账缺 `projects` 行 ⇒ `upsert_kb` 先抛
    「知识库所属项目未登记」，`kbs` 行随之缺失 ⇒ **对该项目的任何上传恒 403**
    （前端表现为「当前令牌无权操作该项目或该知识库」）。

    顺序**必须**「先项目行、后知识库行」：`upsert_kb` 会校验项目已登记。
    `upsert_project` 的 `ON CONFLICT` 只更新 `name` / `embedding_model_id` / `dim`，
    **不**回写 `active_collection_version` / `created_at`，故对既有行无副作用。

    与 `_ensure_collections` 同级收敛：装配期与热重载（`reload_projects`）各调一次，
    既覆盖运行期新建项目，也使既有缺行项目在下次装配 / 项目 CRUD 后自愈。
    """
    for project_id, project in projects.items():
        ledger.upsert_project(project)
        ledger.upsert_kb(
            KbRecord(kb_id=project_id, project_id=project_id, name=project_id, created_at="")
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
    prompt_store: Any | None = None,
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
    **REV-20（ADR-48）**：原 `builtin_fallbacks` 传递链**已删除** —— 代码内置兜底退役后，
    提示词域判据自足（两层皆缺 → `prompt_missing`），**无需**任何内置映射注入。

    **REV-20（ADR-51 决定 ③）keyword-only `prompt_store`**：装配期由 `_load_and_admit`
    传入该项目的 `ExpertPromptStore`，使正文经**端口方法** `load_bundle` 取值 ——
    否则**离线 / 内存态**的 `InMemoryExpertPromptStore`（其 refs 为合成路径、无对应文件）
    的「种子预填」无法被 refs-读盘路径消费，装配期会误报 `prompt_missing`。
    """
    if store is None:
        deps = get_deps(required=False)
        store = getattr(deps, "definition_store", None)
    if store is None:
        raise StartupError("准入闸门缺少定义文档存储：装配未完成或未注入 definition_store")
    from ib.config import derive_prompt_layers, validate_two_domains

    # IFC-IB-364：定义文档域（290）∪ 工具参数域（346）∪ 提示词目录域（345）；
    # 与保存路径同一入口（ADR-33 / ADR-36）。
    report = validate_two_domains(
        doc,
        known_tools=_known_tool_names(),
        tool_param_specs=tuple(tool_specs),
        prompt_refs=prompt_refs,
    )
    if report.errors:
        _raise_admission_error(report.errors)
    return derive_prompt_layers(doc, prompt_refs, store=prompt_store)  # IFC-IB-347


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

    **REV-19（ADR-45 Option C 保留）**：本函数是**装配期兜底**（对未落盘项目构造内置默认
    种子），语义**等价既有逐项目种子**（取「内置默认专家集」= 代码安全网）。**新建项目**的
    创建期播种不走此处 —— 走 `seed_project`（IFC-IB-385，种子 = 内置默认单例 1 个 KB agent）。
    """
    from ib.experts import EXPERT_SPECS, default_expert

    return _definition_document_from_specs(
        project_id, specs=tuple(EXPERT_SPECS), default_name=default_expert()
    )


def _definition_document_from_specs(project_id: str, *, specs: Any, default_name: str) -> Any:
    """由一组专家规格构造定义文档（**单一编排流**，OOS-21）。

    复用者：装配期兜底 `_default_definition_document`（内置默认专家集）与创建期播种
    `seed_project`（IFC-IB-385：非 demo = 内置默认单例；demo = 三对齐专家）。
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
        for spec in specs
    )
    route = RouteSpecInput(
        tau=DEFAULT_TAU,
        margin=DEFAULT_MARGIN,
        max_expert_steps=8,
        default_expert=default_name,
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
        ToolGrantSpec(expert_name=spec.name, tool_names=("search_knowledge",)) for spec in specs
    )
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=route,
        orchestration=orchestration,
        tool_grants=grants,
    )


def seed_project(
    project_id: str,
    *,
    registry_view: Any = None,
    definition_dir: str | None = None,
    prompt_root: str | None = None,
) -> Any:
    """**项目创建播种**（IFC-IB-385 扩展 / **IFC-IB-390**；REQ-FUNC-IB-52 / IB-54 / IB-57；ADR-45 / ADR-50 / ADR-51）。

    在项目注册表写入成功后由 `POST /api/projects` **同步**调用：

      * 写 `<definition_dir>/<project_id>.json`（该项目专家集 + **单一默认编排流**，OOS-21）；
      * **IFC-IB-390（REV-20 新增）**：写 `<prompt_root>/<project_id>/<expert>/main.md`
        —— 正文取自**仓库种子资产**（`ib.config.kb_agent_seed_prompt`，IFC-IB-389），
        使新建项目的 kb-agent 提示词**有项目域可编辑载体**（REQ-FUNC-IB-54 / OQ-IB-43=C）；
      * 建提示词目录骨架（每专家一子目录）。

    **种子真源（REV-20 / ADR-50）**：**任何项目**（含 `demo`）= **内置默认单例**
    （1 个 KB 问答 agent，IFC-IB-381 / REQ-FUNC-IB-57）—— `demo` 分支**已删除**、
    三专家机制退役。`registry_view` 省略时取内置默认单例视图。

    **幂等**（文档 / 提示词文件**已存在不覆盖** —— 避免重装配覆盖用户编辑）；
    **原子回滚**（任一子步失败 → 删除已写入的半成品 + 明确异常，**不静默**）。
    离线 / 未配置载体（`definition_dir` 与 `prompt_root` 均不可用）→ 不落盘，返回
    `created=False`（装配期兜底仍生效，等价既有逐项目种子）。

    **既有项目**的提示词回填**不**走本函数（受「已存在不覆盖」约束）—— 走**一次性回填
    迁移** `backfill_project_prompts`（IFC-IB-391；ADR-51 决定 ②；**须用户手工执行**）。
    """
    import os as _os

    from ib.core import SeedResult
    from ib.experts import builtin_default_registry

    if definition_dir is None:
        definition_dir = _os.environ.get("IB_DEFINITION_DOC_PATH", "").strip()
    if prompt_root is None:
        prompt_root = _os.environ.get("IB_EXPERT_PROMPT_DIR", "").strip()

    chosen = registry_view if registry_view is not None else builtin_default_registry()
    names = tuple(chosen.names())
    seed_note = "builtin_default_seed"

    written_doc: str | None = None
    created_dirs: list[str] = []
    created_prompts: list[str] = []
    try:
        if definition_dir:
            from ib.config import FileDefinitionDocumentStore

            store = FileDefinitionDocumentStore(definition_dir, known_tools=_known_tool_names())
            target = store._path_for(project_id)
            if _os.path.isfile(target):
                return SeedResult(
                    created=False,
                    document_path=target,
                    prompt_root=prompt_root or "",
                    expert_names=names,
                    orchestration="default",
                    notes=("already_seeded", "not_overwritten"),
                )
            doc = _definition_document_from_specs(
                project_id, specs=tuple(chosen.experts), default_name=chosen.default_name()
            )
            store.save(project_id, doc, expected_content_hash=None)
            written_doc = target

        if prompt_root:
            from ib.config import FsExpertPromptStore, kb_agent_seed_prompt

            seed_text = kb_agent_seed_prompt()
            prompt_store = FsExpertPromptStore(prompt_root, project_id)
            for expert in names:
                d = _os.path.join(prompt_root, project_id, expert)
                _os.makedirs(d, exist_ok=True)
                created_dirs.append(d)
                # IFC-IB-390：落盘主提示词；**已存在不覆盖**（幂等，保护用户编辑）
                main_path = _os.path.join(d, "main.md")
                if not _os.path.isfile(main_path):
                    result = prompt_store.save_layer(expert, "main", seed_text, expected_hash=None)
                    if not result.saved:
                        raise ConfigError(
                            f"创建期提示词落盘失败（expert={expert}，IB_EXPERT_PROMPT_DIR）"
                        )
                    created_prompts.append(main_path)

        return SeedResult(
            created=True,
            document_path=written_doc or "",
            prompt_root=prompt_root or "",
            expert_names=names,
            orchestration="default",
            notes=(seed_note,),
        )
    except BaseException:
        # 原子回滚：删除半成品（不静默 —— 异常向上传播由调用方回滚注册表项）。
        for p in created_prompts:
            if _os.path.isfile(p):
                try:
                    _os.remove(p)
                except OSError:
                    pass
        if written_doc and _os.path.isfile(written_doc):
            try:
                _os.remove(written_doc)
            except OSError:
                pass
        for d in created_dirs:
            try:
                _os.removedirs(d)
            except OSError:
                pass
        raise


def backfill_project_prompts(
    project_ids: Any = None,
    *,
    prompt_root: str | None = None,
    backup_dir: str | None = None,
) -> Any:
    """**一次性回填迁移**（**IFC-IB-391**；ADR-51 决定 ②；OQ-IB-44=C）。

    对**给定项目**（缺省 = 注册表全部活动项目）写 / **覆盖**
    `<prompt_root>/<project_id>/kb-agent/main.md` 为**种子资产正文**（IFC-IB-389），
    使既有项目具备项目域提示词载体（「提示词来自项目目录」成立，REQ-FUNC-IB-55）。

    **纪律（强制，C-IB-38 / C-IB-52）**：
      * **非运行期行为** —— 仅由运维脚本在**用户手工执行**时调用；**不**接入任何启动路径；
      * **先备份**：`backup_dir` 非空时，把被覆盖的原文件**逐字复制**到
        `<backup_dir>/<project_id>/<expert>/main.md`（不存在则跳过）；
      * **失败即回滚**：任一项失败 → 用备份还原已覆盖项并抛异常（**不静默**）；
      * **覆盖不静默**：逐项目返回结构化结果（**`MigrationResult` 元组**，IFC-IB-378），
        供迁移报告与交付说明逐项目列出「被覆盖 / 新建」；
      * **不含任何凭据**（只读写提示词文件）。

    **返回**：`tuple[MigrationResult, ...]`（每项目一项；`affected=1`，`backup_path` 为备份
    路径或 `None`，`notes` 记 `overwritten` / `created` 与专家名）。
    """
    import os as _os

    from ib.config import EXPERT_PROMPT_DIR_KEY, FsExpertPromptStore, kb_agent_seed_prompt
    from ib.core import MigrationResult
    from ib.experts import BUILTIN_DEFAULT_KB_AGENT

    root = (prompt_root or _os.environ.get("IB_EXPERT_PROMPT_DIR", "")).strip()
    if not root:
        raise DependencyUnavailableError(
            "回填迁移缺少提示词目录（IB_EXPERT_PROMPT_DIR）", dependency="expert_prompt_dir"
        )
    if project_ids is None:
        deps = get_deps(required=False)
        project_ids = sorted(getattr(deps, "projects", {}) or {})

    expert = BUILTIN_DEFAULT_KB_AGENT.name
    seed_text = kb_agent_seed_prompt()  # 资产缺失即 fail-closed 上抛（不静默）

    results: list[Any] = []
    covered: list[tuple[str, str]] = []  # (target, backup_path) —— 失败回滚用
    for project_id in list(project_ids):
        target = _os.path.join(root, project_id, expert, "main.md")
        existed = _os.path.isfile(target)
        backup_path: str | None = None
        if existed and backup_dir:
            backup_path = _os.path.join(backup_dir, project_id, expert, "main.md")
            try:
                import shutil

                _os.makedirs(_os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(target, backup_path)
            except OSError as exc:
                raise ConfigError(
                    f"回填迁移备份失败（project_id={project_id}，迁移中止，不静默）",
                    key=EXPERT_PROMPT_DIR_KEY,
                ) from exc
        try:
            store = FsExpertPromptStore(root, project_id)
            res = store.save_layer(expert, "main", seed_text, expected_hash=None)
            if not res.saved:
                raise ConfigError(f"回填迁移落盘失败（project_id={project_id}）")
        except BaseException:
            # 失败即回滚：用备份还原已覆盖项，再上抛（不静默）。
            import shutil

            for tgt, bak in covered:
                try:
                    shutil.copy2(bak, tgt)
                except OSError:
                    pass
            raise
        if backup_path:
            covered.append((target, backup_path))
        results.append(
            MigrationResult(
                applied=True,
                backup_path=backup_path,
                affected=1,
                notes=("overwritten" if existed else "created", f"expert={expert}"),
            )
        )
    return tuple(results)


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
        # **REV-20（ADR-48 决定 3）**：不再注入任何内置兜底映射 —— legacy `fallback_prompt`
        # 键改为一律 fail-closed（比对基准已随代码内置兜底层退役；见 `ib.config.definition`）。
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
            # **REV-20（ADR-48 / ADR-51 决定 ③）**：离线 / 内存态**由种子内容预填**
            # kb-agent 的 `main` 层 —— 代码内置兜底已退役，不预填则「两层皆缺」
            # 会在装配期以 `prompt_missing` 拒绝装配（[ARCH-ASSUMPTION-A14]）。
            stores[project_id] = InMemoryExpertPromptStore(
                project_id, documents=_seed_prompt_documents()
            )
    return stores


def _seed_prompt_documents() -> dict[str, dict[str, str]]:
    """离线 / 内存态预填文档（IFC-IB-389 / ADR-51 决定 ③）。

    返回 `{专家名: {层: 正文}}` —— 用**仓库种子资产正文**预填内置 kb-agent 的 `main` 层。
    仅用于**离线 / 内存态**（无 `IB_EXPERT_PROMPT_DIR`）；生产走 `FsExpertPromptStore`。
    """
    from ib.config import kb_agent_seed_prompt
    from ib.experts import BUILTIN_DEFAULT_KB_AGENT

    return {BUILTIN_DEFAULT_KB_AGENT.name: {"main": kb_agent_seed_prompt()}}


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
            # **REV-20（ADR-48 决定 1+4）**：代码内置兜底已整体退役，本字段**去驱动化**
            # （不再参与任何运行期提示词取值）。提示词正文来自**项目提示词目录**
            # （创建期落盘 / 回填迁移 / 离线预填），故此处恒为空串。
            fallback_prompt="",
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
