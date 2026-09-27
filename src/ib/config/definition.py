"""
@module MOD-IB-02
@implements IFC-IB-288, IFC-IB-289, IFC-IB-290, IFC-IB-291, IFC-IB-292
@depends MOD-IB-01
@author software-developer

**定义文档数据层**（R7 增量，module_design.md §3 MOD-IB-02 / IFC-IB-288~292）。

单一真源纪律（ADR-15）：定义文档是「专家 / 路由 / 编排 / 工具授权」的**唯一**真源；
本模块只负责其**装载（load）/ 完备性校验（validate）/ 只读派生（derive）/ 原子写回（save）/
可编辑白名单（editable_field_whitelist）**。可视化视图**不得**另存一份数据（第二真源）。

纯函数不变式：`validate` 与 `derive` 为**纯函数**（同输入同输出、无 I/O、无副作用），
可在无网络、无服务端的环境下被离线用例直接调用（REQ-FUNC-IB-27 / REV-07-5）。

类型层事实（ADR-16）：`ValidationReport` 的字段集**不含** force / ignore / warn_only，
故「带病继续」在本层**无法表达**。校验失败 → 装配期 fail-fast 拒绝启动（IFC-IB-293）。

本模块**只允许 stdlib + `ib.core`**（framework-free 不变式；`ib.core` 是唯一允许的层内依赖）。
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from hashlib import sha256
from typing import Any

from ib.core import (
    ConfigError,
    ConditionalEdgeSpec,
    DefinitionDocument,
    DerivedView,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    SaveResult,
    ToolGrantSpec,
    ValidationErrorItem,
    ValidationReport,
)

__all__ = [
    "SUPPORTED_SCHEMA_VERSION",
    "DEFAULT_MAX_EXPERT_STEPS",
    "content_hash_conflict_item",
    "semantic_hash",
    "editable_field_whitelist",
    "non_editable_changes",
    "validate",
    "derive",
    "build_definition_document",
    "document_from_json",
    "document_to_json",
    "FileDefinitionDocumentStore",
    "InMemoryDefinitionDocumentStore",
    "NON_EDITABLE_FIELDS",
]

SUPPORTED_SCHEMA_VERSION = 1
DEFAULT_MAX_EXPERT_STEPS = 8

#: 可编辑白名单**之外**的显式清单（供审核与前端对照；等价于「白名单的补集」中语义敏感的项）。
#: 拓扑相关字段**永久不可编辑**（REQ-FUNC-IB-26 ②）：节点 / 边集合与条件边存在性。
NON_EDITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "project_id",
        "content_hash",
        "updated_at",
        "orchestration",
        "orchestration.nodes",
        "orchestration.conditional_edges",
    }
)


# --------------------------------------------------------------------------- #
# 语义哈希（乐观并发判据；IFC-IB-289）
# --------------------------------------------------------------------------- #


def _semantic_payload(doc: DefinitionDocument) -> dict[str, Any]:
    """构造**语义载荷**：显式排除 `content_hash` 与 `updated_at`（二者非语义内容）。"""
    return {
        "schema_version": doc.schema_version,
        "project_id": doc.project_id,
        "experts": [
            {
                "name": e.name,
                "cn_label": e.cn_label,
                "keywords": list(e.keywords),
                "exemplars": list(e.exemplars),
                "is_data_expert": e.is_data_expert,
                "fallback_prompt": e.fallback_prompt,
                "is_delegating": e.is_delegating,
                "is_default": e.is_default,
            }
            for e in doc.experts
        ],
        "route": {
            "tau": doc.route.tau,
            "margin": doc.route.margin,
            "max_expert_steps": doc.route.max_expert_steps,
            "default_expert": doc.route.default_expert,
        },
        "orchestration": {
            "nodes": list(doc.orchestration.nodes),
            "conditional_edges": [
                {"from_node": ce.from_node, "branch_map": [list(b) for b in ce.branch_map]}
                for ce in doc.orchestration.conditional_edges
            ],
        },
        "tool_grants": [
            {"expert_name": g.expert_name, "tool_names": list(g.tool_names)} for g in doc.tool_grants
        ],
    }


def semantic_hash(doc: DefinitionDocument) -> str:
    """语义哈希（纯函数）。同语义内容 → 同哈希；与 `updated_at` 无关。"""
    blob = json.dumps(_semantic_payload(doc), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + sha256(blob.encode("utf-8")).hexdigest()


def content_hash_conflict_item(expected: str, current: str) -> ValidationErrorItem:
    """构造一条可读的乐观并发冲突项（IFC-IB-289；**不回显任何凭据值**）。"""
    return ValidationErrorItem(
        path="content_hash",
        code="content_hash_conflict",
        message=f"定义文档已被他处修改：期望 {expected[:24]}…，当前 {current[:24]}…（拒绝覆盖）",
    )


# --------------------------------------------------------------------------- #
# 可编辑字段白名单（IFC-IB-292；REQ-FUNC-IB-26 ①）
# --------------------------------------------------------------------------- #


def editable_field_whitelist() -> frozenset[str]:
    """可编辑字段白名单（IFC-IB-292）。

    **仅**「节点参数 + 专家集合」可编辑（REQ-FUNC-IB-26）：专家实体的各字段、路由参数、
    工具授权可改；**图拓扑不可改**（节点 / 边集合、条件边存在性 → 见 `NON_EDITABLE_FIELDS`）。
    """
    return frozenset(
        {
            # 专家集合（可增删专家实体）=「专家集合」可编辑对象
            "experts",
            "experts[].name",
            "experts[].cn_label",
            "experts[].keywords",
            "experts[].exemplars",
            "experts[].is_data_expert",
            "experts[].fallback_prompt",
            "experts[].is_delegating",
            "experts[].is_default",
            # 路由参数（节点参数）
            "route.tau",
            "route.margin",
            "route.max_expert_steps",
            "route.default_expert",
            # 工具授权（节点参数）
            "tool_grants",
            "tool_grants[].expert_name",
            "tool_grants[].tool_names",
        }
    )


# --------------------------------------------------------------------------- #
# 完备性校验（IFC-IB-290；纯函数，≥7 类校验项）
# --------------------------------------------------------------------------- #


def _err(path: str, code: str, message: str) -> ValidationErrorItem:
    return ValidationErrorItem(path=path, code=code, message=message)


def non_editable_changes(
    current: DefinitionDocument,
    submitted: DefinitionDocument,
) -> tuple[ValidationErrorItem, ...]:
    """检出**白名单之外**字段是否被改动（IFC-IB-292 / REQ-FUNC-IB-26 ①）。

    纯函数。服务端以此拒绝「绕过界面直改文档」试图改动拓扑 / 归属等不可编辑字段
    （界面编辑与直接改文档**一视同仁**）。服务端管理的派生字段（`content_hash` /
    `updated_at`）不参与比较（它们由服务端重算，非「编辑对象」）。
    """
    items: list[ValidationErrorItem] = []
    if submitted.schema_version != current.schema_version:
        items.append(_err("schema_version", "field_not_editable", "schema_version 不在可编辑白名单内"))
    if submitted.project_id != current.project_id:
        items.append(_err("project_id", "field_not_editable", "project_id 不在可编辑白名单内"))
    if _semantic_payload(submitted)["orchestration"] != _semantic_payload(current)["orchestration"]:
        items.append(
            _err(
                "orchestration",
                "field_not_editable",
                "图拓扑（编排节点 / 条件边）不可运行期编辑（REQ-FUNC-IB-26 ②）",
            )
        )
    return tuple(items)


def validate(
    doc: DefinitionDocument,
    *,
    known_tools: frozenset[str] | set[str] | None = None,
) -> ValidationReport:
    """定义文档完备性校验（IFC-IB-290）。**纯函数**：无 I/O、无副作用、同输入同输出。

    覆盖类别（≥7）：
      1. schema 版本受支持；
      2. project_id 非空；
      3. 专家集合非空、名字唯一；
      4. **默认专家恰好一个**（REQ-FUNC-IB-26 ③ 不得被绕过）；
      5. 专家文本字段非空（`cn_label` / `fallback_prompt`）；
      6. 路由 `default_expert` 必须是已知专家；阈值在合法域内；
      7. 编排节点非空；条件边**必须**显式 `branch_map` 且端点均在节点集合内（REQ-FUNC-IB-26 ④）；
      8. 工具授权：专家名已知、工具名在已知注册表内、同一专家不重复授权；
      9. `content_hash` 非空；
      10. **跨专家路由关键词撞车**（R8 追加；归一化 = `strip().lower()`，见下方实现注释）；
      11. **`cn_label` 唯一性**（R8 追加；去首尾空白后比较）。

    第 10 / 11 类为 **R8 纯追加**：既有 1~9 类的语义与顺序**一字未改**，新增项仅在末尾追加。
    `known_tools` 为空集时不校验工具名（离线可测；装配期由组合根传入真实注册表）。
    """
    errors: list[ValidationErrorItem] = []

    # 1. schema 版本
    if doc.schema_version != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            _err(
                "schema_version",
                "schema_version_unsupported",
                f"不支持的 schema_version={doc.schema_version}（仅支持 {SUPPORTED_SCHEMA_VERSION}）",
            )
        )

    # 2. project_id
    if not doc.project_id:
        errors.append(_err("project_id", "project_id_missing", "project_id 不得为空"))

    # 3. 专家集合
    names = [e.name for e in doc.experts]
    if not names:
        errors.append(_err("experts", "experts_empty", "专家集合不得为空"))
    seen: set[str] = set()
    for e in doc.experts:
        if e.name in seen:
            errors.append(_err(f"experts[{e.name}]", "expert_name_duplicate", f"专家名重复：{e.name}"))
        seen.add(e.name)

    # 4. 默认专家恰好一个
    defaults = [e.name for e in doc.experts if e.is_default]
    if len(defaults) != 1:
        errors.append(
            _err(
                "experts",
                "expert_default_count",
                f"默认专家必须恰好一个，当前 {len(defaults)} 个（{', '.join(defaults) or '无'}）",
            )
        )

    # 5. 专家文本字段
    for e in doc.experts:
        if not e.cn_label.strip():
            errors.append(_err(f"experts[{e.name}].cn_label", "expert_text_missing", "cn_label 不得为空"))
        if not e.fallback_prompt.strip():
            errors.append(
                _err(f"experts[{e.name}].fallback_prompt", "expert_text_missing", "fallback_prompt 不得为空")
            )

    # 6. 路由
    if names and doc.route.default_expert not in names:
        errors.append(
            _err(
                "route.default_expert",
                "route_default_unknown",
                f"default_expert='{doc.route.default_expert}' 不在专家集合内",
            )
        )
    if not (0.0 <= doc.route.tau <= 1.0):
        errors.append(_err("route.tau", "route_threshold_out_of_range", "tau 必须落于 [0,1]"))
    if not (0.0 <= doc.route.margin <= 1.0):
        errors.append(_err("route.margin", "route_threshold_out_of_range", "margin 必须落于 [0,1]"))
    if doc.route.max_expert_steps < 1:
        errors.append(
            _err("route.max_expert_steps", "route_threshold_out_of_range", "max_expert_steps 必须 >= 1")
        )

    # 7. 编排
    node_set = set(doc.orchestration.nodes)
    if not doc.orchestration.nodes:
        errors.append(_err("orchestration.nodes", "orchestration_nodes_empty", "编排节点集合不得为空"))
    for ce in doc.orchestration.conditional_edges:
        if not ce.branch_map:
            errors.append(
                _err(
                    f"orchestration.conditional_edges[{ce.from_node}]",
                    "conditional_edge_branch_map_empty",
                    "条件边必须显式声明 branch_map（否则界面无法判定可达性）",
                )
            )
        if ce.from_node not in node_set:
            errors.append(
                _err(
                    f"orchestration.conditional_edges[{ce.from_node}].from_node",
                    "conditional_edge_node_unknown",
                    f"条件边起点 '{ce.from_node}' 不在节点集合内",
                )
            )
        for branch_key, target in ce.branch_map:
            if target not in node_set:
                errors.append(
                    _err(
                        f"orchestration.conditional_edges[{ce.from_node}].branch_map[{branch_key}]",
                        "conditional_edge_node_unknown",
                        f"条件边分支目标 '{target}' 不在节点集合内",
                    )
                )

    # 8. 工具授权
    known = frozenset(known_tools) if known_tools else None
    granted_experts: set[str] = set()
    for g in doc.tool_grants:
        if names and g.expert_name not in names:
            errors.append(
                _err(
                    f"tool_grants[{g.expert_name}]",
                    "tool_grant_expert_unknown",
                    f"工具授权指向未知专家 '{g.expert_name}'",
                )
            )
        if g.expert_name in granted_experts:
            errors.append(
                _err(
                    f"tool_grants[{g.expert_name}]",
                    "tool_grant_duplicate_expert",
                    f"专家 '{g.expert_name}' 被重复授权",
                )
            )
        granted_experts.add(g.expert_name)
        if known is not None:
            for t in g.tool_names:
                if t not in known:
                    errors.append(
                        _err(
                            f"tool_grants[{g.expert_name}].tool_names[{t}]",
                            "tool_grant_tool_unknown",
                            f"工具 '{t}' 不在已知工具注册表内",
                        )
                    )

    # 9. content_hash
    if not doc.content_hash:
        errors.append(_err("content_hash", "content_hash_missing", "content_hash 不得为空"))

    # 10. 跨专家路由关键词撞车（ADR-16 校验项枚举 / AC-IB-18-02；R8 **纯追加**）
    #     口径（R8 实现决策）：归一化 = `strip().lower()`。
    #       * `lower()` 对齐**路由消费方** `ib/routing/intent.py::_keyword_hits`
    #         （`keyword.lower() in text.lower()`）—— 大小写不同、小写后相同的两个关键词
    #         在运行期同样会撞车，故必须按大小写不敏感判定；
    #       * `strip()` 去掉首尾空白 —— 带空白的关键词几乎必然是录入错误，其去空白形态
    #         仍会与对方在含空白的文本上重叠命中，去空白后判定可稳定捕获。
    #     本项**只在跨专家之间**判定（同一专家内的空/重复关键词由
    #     `ib.experts.validate_specs` 在派生安装期以 ValueError 兜底，语义与顺序均不改）。
    #     撞车 → L0「关键词唯一命中」判据并列命中、路由结果不可复现，故装配期 fail-fast 拒绝。
    kw_owner: dict[str, str] = {}
    for e in doc.experts:
        for kw in e.keywords:
            normalized = kw.strip().lower()
            if not normalized:
                continue  # 空关键词非「撞车」范畴（由专家内校验承担）
            holder = kw_owner.get(normalized)
            if holder is not None and holder != e.name:
                errors.append(
                    _err(
                        f"experts[{e.name}].keywords[{kw}]",
                        "expert_keyword_collision",
                        f"路由关键词撞车：'{kw}' 同时归属专家 '{holder}' 与 '{e.name}'"
                        f"（会导致路由并列命中、结果不可复现）",
                    )
                )
            else:
                kw_owner[normalized] = e.name

    # 11. cn_label（面向用户中文标签）唯一性（ADR-16 校验项枚举 / AC-IB-18-02；R8 **纯追加**）
    #     口径：去首尾空白后比较 —— 标签是**展示串**，空白填充在界面上不可见，故必须视为重复；
    #     大小写差异在界面可见，故不做大小写归一。空标签由第 5 项 `expert_text_missing` 单独报出，
    #     此处跳过空值以免重复告警。重复标签会使前端推理折叠框无法区分专家。
    label_owner: dict[str, str] = {}
    for e in doc.experts:
        label = e.cn_label.strip()
        if not label:
            continue
        holder = label_owner.get(label)
        if holder is not None and holder != e.name:
            errors.append(
                _err(
                    f"experts[{e.name}].cn_label",
                    "expert_cn_label_duplicate",
                    f"专家中文标签重复：'{e.cn_label}' 同时归属专家 '{holder}' 与 '{e.name}'"
                    f"（前端推理折叠框无法区分专家）",
                )
            )
        else:
            label_owner[label] = e.name

    return ValidationReport(ok=not errors, errors=tuple(errors))


# --------------------------------------------------------------------------- #
# 只读派生（IFC-IB-291；纯函数）
# --------------------------------------------------------------------------- #


def _capability_digest(grants: tuple[ToolGrantSpec, ...]) -> str:
    """工具授权能力摘要（确定性）。空授权 → 空串（对齐既有 `build_capability_digest` 语义）。"""
    if not grants:
        return ""
    lines: list[str] = []
    for g in sorted(grants, key=lambda x: x.expert_name):
        tools = ", ".join(sorted(g.tool_names))
        lines.append(f"- {g.expert_name}: {tools}")
    return "\n".join(lines)


def derive(doc: DefinitionDocument) -> DerivedView:
    """派生**只读视图**（IFC-IB-291）。**纯函数**：结果不落盘、不可反写文档。

    产出装配期注入所需的三项：专家集合、能力摘要、图配置（编排规格）。
    拓扑在此**固化**为不可变元组 —— 运行期不得由任何图外输入改变（REQ-FUNC-IB-26 ②）。
    """
    return DerivedView(
        experts=tuple(doc.experts),
        capability_digest=_capability_digest(doc.tool_grants),
        graph_config=OrchestrationSpecInput(
            nodes=tuple(doc.orchestration.nodes),
            conditional_edges=tuple(doc.orchestration.conditional_edges),
        ),
    )


# --------------------------------------------------------------------------- #
# 构造与序列化
# --------------------------------------------------------------------------- #


def build_definition_document(
    *,
    project_id: str,
    experts: tuple[ExpertSpecInput, ...],
    route: RouteSpecInput,
    orchestration: OrchestrationSpecInput,
    tool_grants: tuple[ToolGrantSpec, ...] = (),
    schema_version: int = SUPPORTED_SCHEMA_VERSION,
    updated_at: str = "",
) -> DefinitionDocument:
    """构造定义文档并计算其语义哈希（`content_hash` 由内容决定，不由调用方指定）。"""
    draft = DefinitionDocument(
        schema_version=schema_version,
        project_id=project_id,
        content_hash="",
        experts=experts,
        route=route,
        orchestration=orchestration,
        tool_grants=tool_grants,
        updated_at=updated_at,
    )
    return replace(draft, content_hash=semantic_hash(draft))


def document_to_json(doc: DefinitionDocument) -> str:
    """序列化为 JSON 文本（稳定键序，便于人读 diff 与哈希复核）。"""
    payload = _semantic_payload(doc)
    payload["content_hash"] = doc.content_hash
    payload["updated_at"] = doc.updated_at
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def document_from_json(project_id: str, text: str) -> DefinitionDocument:
    """从 JSON 文本反序列化。结构非法 → 抛 `ConfigError`（可读原因，**不静默回退**）。"""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ConfigError("定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）", key="IB_DEFINITION_DOC_PATH") from exc
    if not isinstance(data, dict):
        raise ConfigError("定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）", key="IB_DEFINITION_DOC_PATH")
    try:
        experts = tuple(
            ExpertSpecInput(
                name=str(e["name"]),
                cn_label=str(e.get("cn_label", "")),
                keywords=tuple(str(k) for k in e.get("keywords", [])),
                exemplars=tuple(str(x) for x in e.get("exemplars", [])),
                is_data_expert=bool(e.get("is_data_expert", False)),
                fallback_prompt=str(e.get("fallback_prompt", "")),
                is_delegating=bool(e.get("is_delegating", False)),
                is_default=bool(e.get("is_default", False)),
            )
            for e in data.get("experts", [])
        )
        route_d = data.get("route", {}) or {}
        route = RouteSpecInput(
            tau=float(route_d.get("tau", 0.65)),
            margin=float(route_d.get("margin", 0.05)),
            max_expert_steps=int(route_d.get("max_expert_steps", DEFAULT_MAX_EXPERT_STEPS)),
            default_expert=str(route_d.get("default_expert", "")),
        )
        orch_d = data.get("orchestration", {}) or {}
        conditional = tuple(
            ConditionalEdgeSpec(
                from_node=str(ce["from_node"]),
                branch_map=tuple((str(b[0]), str(b[1])) for b in ce.get("branch_map", [])),
            )
            for ce in orch_d.get("conditional_edges", [])
        )
        orchestration = OrchestrationSpecInput(
            nodes=tuple(str(n) for n in orch_d.get("nodes", [])),
            conditional_edges=conditional,
        )
        grants = tuple(
            ToolGrantSpec(
                expert_name=str(g["expert_name"]),
                tool_names=tuple(str(t) for t in g.get("tool_names", [])),
            )
            for g in data.get("tool_grants", [])
        )
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ConfigError("定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）", key="IB_DEFINITION_DOC_PATH") from exc

    doc = DefinitionDocument(
        schema_version=int(data.get("schema_version", SUPPORTED_SCHEMA_VERSION)),
        project_id=str(data.get("project_id", project_id)),
        content_hash=str(data.get("content_hash", "")),
        experts=experts,
        route=route,
        orchestration=orchestration,
        tool_grants=grants,
        updated_at=str(data.get("updated_at", "")),
    )
    # 内容哈希以**重算**为准：文件里的 content_hash 若被手改，重算可使其失效（乐观并发可信）。
    return replace(doc, content_hash=semantic_hash(doc), project_id=project_id)


# --------------------------------------------------------------------------- #
# 存储实现（端口 `DefinitionDocumentStore`，IFC-IB-288/289/290/291/292）
# --------------------------------------------------------------------------- #


class InMemoryDefinitionDocumentStore:
    """进程内定义文档存储（**测试替身**；module_design.md §8）。

    同一 `validate` / `derive` / `editable_field_whitelist` 语义与生产实现一致，
    且 `save` 同样实施乐观并发判据 —— 使离线用例能覆盖真实并发分支。
    """

    def __init__(
        self,
        initial: DefinitionDocument | None = None,
        *,
        known_tools: frozenset[str] | set[str] | None = None,
        missing: bool = False,
        documents: "dict[str, DefinitionDocument] | None" = None,
    ) -> None:
        self._docs: dict[str, DefinitionDocument] = dict(documents) if documents else {}
        if initial is not None:
            self._docs[initial.project_id] = initial
        self._known_tools = frozenset(known_tools) if known_tools else None
        self._missing = missing

    def load(self, project_id: str) -> DefinitionDocument:
        if self._missing or project_id not in self._docs:
            raise ConfigError(
                "定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）",
                key="IB_DEFINITION_DOC_PATH",
            )
        return self._docs[project_id]

    def save(
        self,
        project_id: str,
        doc: DefinitionDocument,
        *,
        expected_content_hash: str | None,
    ) -> SaveResult:
        existing = self._docs.get(project_id)
        current = existing.content_hash if existing is not None else None
        if expected_content_hash is not None and expected_content_hash != current:
            item = content_hash_conflict_item(expected_content_hash or "", current or "")
            return SaveResult(ok=False, content_hash=current or "", conflict=True, errors=(item,))
        stored = doc if doc.content_hash == semantic_hash(doc) else _rehash(doc)
        self._docs[project_id] = stored
        return SaveResult(ok=True, content_hash=stored.content_hash, conflict=False, errors=())

    def validate(self, doc: DefinitionDocument) -> ValidationReport:
        return validate(doc, known_tools=self._known_tools)

    def derive(self, doc: DefinitionDocument) -> DerivedView:
        return derive(doc)

    def editable_field_whitelist(self) -> frozenset[str]:
        return editable_field_whitelist()


def _rehash(doc: DefinitionDocument) -> DefinitionDocument:
    return replace(doc, content_hash=semantic_hash(doc))


class FileDefinitionDocumentStore:
    """**生产**定义文档存储：本地文件 + 原子替换 + 语义哈希乐观并发（IFC-IB-288/289）。

    * `load`：读 `<path>`；缺失 / 不可解析 → `ConfigError`（不做静默空文档回退）。
    * `save`：先写同目录临时文件 → `os.replace` **原子替换**；`expected_content_hash`
      不匹配 → `SaveResult(conflict=True)` 且**不落盘**（拒绝覆盖）。

    数据不出本机（无任何网络调用），契约符合 [ARCH-ASSUMPTION-A6]「一个项目一份本地文件」。
    """

    def __init__(
        self,
        path: str,
        *,
        known_tools: frozenset[str] | set[str] | None = None,
    ) -> None:
        self._path = path
        self._known_tools = frozenset(known_tools) if known_tools else None

    @property
    def path(self) -> str:
        return self._path

    def load(self, project_id: str) -> DefinitionDocument:
        if not self._path or not os.path.isfile(self._path):
            raise ConfigError("定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）", key="IB_DEFINITION_DOC_PATH")
        try:
            with open(self._path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            raise ConfigError("定义文档缺失或不可解析（IB_DEFINITION_DOC_PATH）", key="IB_DEFINITION_DOC_PATH") from exc
        return document_from_json(project_id, text)

    def save(
        self,
        project_id: str,
        doc: DefinitionDocument,
        *,
        expected_content_hash: str | None,
    ) -> SaveResult:
        current: str | None = None
        if os.path.isfile(self._path):
            try:
                current = self.load(project_id).content_hash
            except ConfigError:
                current = None
        if expected_content_hash is not None and expected_content_hash != current:
            item = content_hash_conflict_item(expected_content_hash or "", current or "")
            return SaveResult(ok=False, content_hash=current or "", conflict=True, errors=(item,))
        stored = doc if doc.content_hash == semantic_hash(doc) else _rehash(doc)
        self._atomic_write(document_to_json(stored))
        return SaveResult(ok=True, content_hash=stored.content_hash, conflict=False, errors=())

    def validate(self, doc: DefinitionDocument) -> ValidationReport:
        return validate(doc, known_tools=self._known_tools)

    def derive(self, doc: DefinitionDocument) -> DerivedView:
        return derive(doc)

    def editable_field_whitelist(self) -> frozenset[str]:
        return editable_field_whitelist()

    def _atomic_write(self, text: str) -> None:
        directory = os.path.dirname(os.path.abspath(self._path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".ib_def_", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._path)  # 原子替换（同目录内 rename）
        except BaseException:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            raise
