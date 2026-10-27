"""
@module MOD-R26-05
@implements IFC-R26-040 ~ 045（快照 / 清单哈希 / 差异 / 三方冲突 / 提示词文本校验）
@depends MOD-R26-01, MOD-R26-02, MOD-R26-04

framework-free、无 I/O 的纯函数（REQ-NFUNC-013）。差异与冲突输出不含提示词正文与凭据：
提示词只给"长度 + 哈希前 8 位"。
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Final, Mapping, Sequence

from ib.core import (
    ConfigError,
    ConfigSnapshot,
    ConflictItem,
    ConflictReceipt,
    DefinitionDocument,
    DiffItem,
    ExpertPromptDocumentRef,
    ExpertSpecInput,
    GraphEdge,
    GraphNode,
    GraphSpec,
    PromptLayers,
    ValidationErrorItem,
)

from .definition import document_from_json, document_to_json, semantic_hash
from .graph import canonical_graph_from_experts

__all__ = [
    "PROMPT_LAYER_MAX_CHARS",
    "build_snapshot",
    "manifest_hash",
    "snapshot_to_json",
    "snapshot_from_json",
    "diff_snapshots",
    "summarize_diff",
    "is_layout_only",
    "detect_conflicts",
    "validate_prompt_texts",
    "prompt_refs_of_snapshot",
]

PROMPT_LAYER_MAX_CHARS: Final[int] = 20000  # INF-4 占位：存储 / 交互上界，不保证模型上下文装得下
_SUMMARY_MAX = 200
_VALUE_MAX = 120


def _h(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# IFC-R26-040 / 041 快照、清单哈希、序列化
# --------------------------------------------------------------------------- #


def build_snapshot(doc: DefinitionDocument, prompts: Mapping[str, PromptLayers]) -> ConfigSnapshot:
    """快照 = 定义文档 + 其专家的两层提示词；只含 `doc.experts` 中的专家，按专家名升序。"""
    names = sorted({e.name for e in doc.experts})
    return ConfigSnapshot(
        definition=doc,
        prompts=tuple((n, prompts.get(n, PromptLayers(None, None))) for n in names),
    )


def _layer_hash(text: str | None) -> str | None:
    return None if text is None else _h(text)


def manifest_hash(snapshot: ConfigSnapshot) -> str:
    payload = {
        "definition": semantic_hash(snapshot.definition),
        "prompts": {
            n: {"main": _layer_hash(pl.main), "fallback": _layer_hash(pl.fallback)}
            for n, pl in snapshot.prompts
        },
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + _h(blob)


def snapshot_to_json(snapshot: ConfigSnapshot) -> str:
    payload = {
        "definition": json.loads(document_to_json(snapshot.definition)),
        "prompts": {n: {"main": pl.main, "fallback": pl.fallback} for n, pl in snapshot.prompts},
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def snapshot_from_json(text: str) -> ConfigSnapshot:
    try:
        data = json.loads(text)
        d = data["definition"]
        project_id = str(d["project_id"])
        doc = document_from_json(project_id, json.dumps(d, ensure_ascii=False))
        prompts = tuple(
            (str(n), PromptLayers(main=_opt_str(v.get("main")), fallback=_opt_str(v.get("fallback"))))
            for n, v in sorted(data.get("prompts", {}).items())
        )
    except ConfigError:
        raise
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ConfigError("配置快照不可解析") from exc
    return ConfigSnapshot(definition=doc, prompts=prompts)


def _opt_str(v: object) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise TypeError("prompt layer")
    return v


# --------------------------------------------------------------------------- #
# IFC-R26-042 差异
# --------------------------------------------------------------------------- #


def _s(v: object) -> str:
    if isinstance(v, (list, tuple)):
        text = ", ".join(str(x) for x in v)
    else:
        text = str(v)
    return text if len(text) <= _VALUE_MAX else text[: _VALUE_MAX - 1] + "…"


def _prompt_digest(text: str | None) -> str | None:
    return None if text is None else f"长度 {len(text)} · 哈希 {_h(text)[:8]}"


def _graph_of(doc: DefinitionDocument) -> GraphSpec:
    return doc.graph if doc.graph is not None else canonical_graph_from_experts(doc.experts, doc.route.default_expert)


def _node_core(n: GraphNode) -> tuple:
    pred = None
    if n.predicate is not None:
        pred = (n.predicate.kind, tuple((b.key, b.keywords) for b in n.predicate.branches))
    return (n.kind, n.expert, n.input_mode, pred, n.message)


def diff_snapshots(base: ConfigSnapshot, new: ConfigSnapshot) -> tuple[DiffItem, ...]:
    """确定性差异（相同输入输出一致，顺序稳定）。"""
    items: list[DiffItem] = []
    bd, nd = base.definition, new.definition
    b_ex = {e.name: e for e in bd.experts}
    n_ex = {e.name: e for e in nd.experts}

    for name in sorted(n_ex.keys() - b_ex.keys()):
        items.append(DiffItem("agent_added", name, "agent", None, _s(n_ex[name].cn_label)))
    for name in sorted(b_ex.keys() - n_ex.keys()):
        items.append(DiffItem("agent_removed", name, "agent", _s(b_ex[name].cn_label), None))
    for name in sorted(b_ex.keys() & n_ex.keys()):
        be, ne = b_ex[name], n_ex[name]
        if be.status != ne.status:
            kind = "agent_disabled" if ne.status == "disabled" else "agent_enabled"
            items.append(DiffItem(kind, name, "status", be.status, ne.status))  # type: ignore[arg-type]
        for fld in ("cn_label", "keywords", "exemplars", "is_data_expert", "is_delegating", "is_default", "max_steps"):
            bv, nv = getattr(be, fld), getattr(ne, fld)
            if bv != nv:
                if fld in ("keywords", "exemplars"):
                    items.append(DiffItem("agent_field", name, fld, f"{len(bv)} 项", f"{len(nv)} 项"))
                else:
                    items.append(DiffItem("agent_field", name, fld, _s(bv), _s(nv)))
        if be.knowledge_scope != ne.knowledge_scope:
            items.append(
                DiffItem(
                    "knowledge_scope",
                    name,
                    "knowledge_scope",
                    f"{be.knowledge_scope.mode}:{len(be.knowledge_scope.folder_ids)}",
                    f"{ne.knowledge_scope.mode}:{len(ne.knowledge_scope.folder_ids)}",
                )
            )

    # 工具授权与参数
    b_gr = {g.expert_name: g for g in bd.tool_grants}
    n_gr = {g.expert_name: g for g in nd.tool_grants}
    for name in sorted(b_gr.keys() | n_gr.keys()):
        bg, ng = b_gr.get(name), n_gr.get(name)
        bt = tuple(sorted(bg.tool_names)) if bg else ()
        nt = tuple(sorted(ng.tool_names)) if ng else ()
        if bt != nt:
            items.append(DiffItem("tool_grant", name, "tool_names", _s(bt), _s(nt)))
        bp = {p.name: p.value for p in bg.param_values} if bg else {}
        np_ = {p.name: p.value for p in ng.param_values} if ng else {}
        for pn in sorted(bp.keys() | np_.keys()):
            if bp.get(pn) != np_.get(pn):
                items.append(DiffItem("tool_param", name, pn, bp.get(pn), np_.get(pn)))

    # 路由参数
    for fld in ("tau", "margin", "max_expert_steps", "default_expert"):
        bv, nv = getattr(bd.route, fld), getattr(nd.route, fld)
        if bv != nv:
            items.append(DiffItem("route_param", "route", fld, _s(bv), _s(nv)))

    # 提示词层
    b_pr, n_pr = dict(base.prompts), dict(new.prompts)
    for name in sorted(b_pr.keys() | n_pr.keys()):
        bl = b_pr.get(name, PromptLayers(None, None))
        nl = n_pr.get(name, PromptLayers(None, None))
        for layer in ("main", "fallback"):
            bt_, nt_ = getattr(bl, layer), getattr(nl, layer)
            if bt_ != nt_:
                items.append(DiffItem("prompt", name, layer, _prompt_digest(bt_), _prompt_digest(nt_)))

    # 图：节点 / 边 / 布局
    bg_, ng_ = _graph_of(bd), _graph_of(nd)
    bn = {n.id: n for n in bg_.nodes}
    nn = {n.id: n for n in ng_.nodes}
    for nid in sorted(nn.keys() - bn.keys()):
        items.append(DiffItem("node_added", nid, "node", None, nn[nid].kind))
    for nid in sorted(bn.keys() - nn.keys()):
        items.append(DiffItem("node_removed", nid, "node", bn[nid].kind, None))
    for nid in sorted(bn.keys() & nn.keys()):
        if _node_core(bn[nid]) != _node_core(nn[nid]):
            items.append(DiffItem("node_changed", nid, "node", bn[nid].kind, nn[nid].kind))
        if (bn[nid].x, bn[nid].y) != (nn[nid].x, nn[nid].y):
            items.append(
                DiffItem(
                    "layout",
                    nid,
                    "position",
                    f"{bn[nid].x:g},{bn[nid].y:g}",
                    f"{nn[nid].x:g},{nn[nid].y:g}",
                )
            )
    be_ = {e.id: e for e in bg_.edges}
    ne_ = {e.id: e for e in ng_.edges}
    for eid in sorted(ne_.keys() - be_.keys()):
        items.append(DiffItem("edge_added", eid, "edge", None, f"{ne_[eid].source}->{ne_[eid].target}"))
    for eid in sorted(be_.keys() - ne_.keys()):
        items.append(DiffItem("edge_removed", eid, "edge", f"{be_[eid].source}->{be_[eid].target}", None))
    for eid in sorted(be_.keys() & ne_.keys()):
        a, b = be_[eid], ne_[eid]
        if (a.source, a.target, a.branch_key) != (b.source, b.target, b.branch_key):
            items.append(
                DiffItem(
                    "edge_changed",
                    eid,
                    "branch_key" if (a.source, a.target) == (b.source, b.target) else "endpoints",
                    f"{a.source}->{a.target}[{a.branch_key}]",
                    f"{b.source}->{b.target}[{b.branch_key}]",
                )
            )
    return tuple(items)


_SUMMARY_LABELS = {
    "agent_added": "新增 agent",
    "agent_removed": "删除 agent",
    "agent_disabled": "停用 agent",
    "agent_enabled": "启用 agent",
    "agent_field": "修改 agent 字段",
    "prompt": "修改 提示词",
    "tool_grant": "修改 工具授权",
    "tool_param": "修改 工具参数",
    "knowledge_scope": "修改 知识范围",
    "route_param": "修改 路由参数",
    "node_added": "新增 节点",
    "node_removed": "删除 节点",
    "node_changed": "修改 节点",
    "edge_added": "新增 连线",
    "edge_removed": "删除 连线",
    "edge_changed": "修改 连线",
    "layout": "调整 布局",
}


def summarize_diff(items: Sequence[DiffItem]) -> str:
    """系统生成的变更摘要（≤200 字符，不含提示词正文）。"""
    if not items:
        return "无变更"
    groups: dict[str, list[str]] = {}
    for it in items:
        ids = groups.setdefault(it.kind, [])
        if it.object_id not in ids:
            ids.append(it.object_id)
    parts = [f"{_SUMMARY_LABELS.get(k, k)} {'、'.join(v)}" for k, v in groups.items()]
    text = "；".join(parts)
    return text if len(text) <= _SUMMARY_MAX else text[: _SUMMARY_MAX - 1] + "…"


def is_layout_only(items: Sequence[DiffItem]) -> bool:
    return bool(items) and all(it.kind == "layout" for it in items)


# --------------------------------------------------------------------------- #
# IFC-R26-043 三方冲突
# --------------------------------------------------------------------------- #

_KIND_GROUP = {
    "agent_added": "agent", "agent_removed": "agent", "agent_disabled": "agent", "agent_enabled": "agent",
    "agent_field": "agent", "tool_grant": "agent", "tool_param": "agent", "knowledge_scope": "agent",
    "prompt": "prompt", "route_param": "route",
    "node_added": "node", "node_removed": "node", "node_changed": "node", "layout": "node",
    "edge_added": "edge", "edge_removed": "edge", "edge_changed": "edge",
}


def _touched(items: Sequence[DiffItem]) -> dict[tuple[str, str], set[str]]:
    out: dict[tuple[str, str], set[str]] = {}
    for it in items:
        out.setdefault((_KIND_GROUP.get(it.kind, it.kind), it.object_id), set()).add(it.field)
    return out


def detect_conflicts(
    base: ConfigSnapshot | None,
    head: ConfigSnapshot,
    submitted: ConfigSnapshot,
) -> ConflictReceipt:
    """两边（head 相对 base、submitted 相对 base）都改动的对象即冲突；不做自动合并。

    base 已被修剪（None）→ base_available=False，conflicts 退化为 head 与 submitted 之间的全部差异对象。
    """
    # 回执里的 base_version / head_version 由发布服务（MOD-R26-13）按真实版本号补全（dataclasses.replace）。
    if base is None:
        touched = _touched(diff_snapshots(head, submitted))
        conflicts = tuple(
            ConflictItem(kind=k, object_id=o, fields=tuple(sorted(f))) for (k, o), f in sorted(touched.items())
        )
        return ConflictReceipt(base_version=-1, head_version=-1, base_available=False, conflicts=conflicts)
    t_head = _touched(diff_snapshots(base, head))
    t_sub = _touched(diff_snapshots(base, submitted))
    conflicts = tuple(
        ConflictItem(kind=k, object_id=o, fields=tuple(sorted(t_head[(k, o)] | t_sub[(k, o)])))
        for (k, o) in sorted(t_head.keys() & t_sub.keys())
    )
    return ConflictReceipt(base_version=-1, head_version=-1, base_available=True, conflicts=conflicts)


def prompt_refs_of_snapshot(snapshot: ConfigSnapshot) -> tuple[ExpertPromptDocumentRef, ...]:
    """快照的提示词层 → 提示词域校验入口所需的文件引用（纯函数）。使“保存路径 / 装配路径”共用 `validate_two_domains`。"""
    refs: list[ExpertPromptDocumentRef] = []
    for name, pl in snapshot.prompts:
        for layer in ("main", "fallback"):
            text = getattr(pl, layer)
            refs.append(
                ExpertPromptDocumentRef(
                    expert_name=name,
                    layer=layer,  # type: ignore[arg-type]
                    rel_path=f"{name}/{layer}.md",
                    content_hash="" if text is None else "sha256:" + _h(text),
                    exists=text is not None and text.strip() != "",
                )
            )
    return tuple(refs)


# --------------------------------------------------------------------------- #
# IFC-R26-044 提示词文本校验
# --------------------------------------------------------------------------- #


def validate_prompt_texts(
    prompts: Mapping[str, PromptLayers],
    *,
    experts: tuple[ExpertSpecInput, ...],
) -> tuple[ValidationErrorItem, ...]:
    """`prompts` 为"生效后的全量"提示词层（None = 该层不存在）。message 不回显正文。"""
    errs: list[ValidationErrorItem] = []
    active = {e.name for e in experts if e.status == "active"}
    for name in sorted(prompts):
        pl = prompts[name]
        p = f"prompts[{name}]"
        if name not in active:
            errs.append(ValidationErrorItem(p, "prompt_orphan_expert", "提示词层对应的专家不存在或已停用"))
            continue
        for layer in ("main", "fallback"):
            text = getattr(pl, layer)
            if text is not None and len(text) > PROMPT_LAYER_MAX_CHARS:
                errs.append(
                    ValidationErrorItem(
                        f"{p}.{layer}", "prompt_too_long", f"提示词超过 {PROMPT_LAYER_MAX_CHARS} 字符上限"
                    )
                )
        if pl.fallback is not None and not pl.fallback.strip():
            errs.append(ValidationErrorItem(f"{p}.fallback", "prompt_fallback_empty", "兜底提示词不得为空白"))
    for name in sorted(active):
        pl = prompts.get(name)
        main_ok = pl is not None and pl.main is not None and pl.main.strip() != ""
        fb_ok = pl is not None and pl.fallback is not None and pl.fallback.strip() != ""
        if not main_ok and not fb_ok:
            errs.append(ValidationErrorItem(f"prompts[{name}]", "prompt_missing", "启用的专家两层提示词皆缺"))
    return tuple(errs)
