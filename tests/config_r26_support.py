"""REV-26（可视化配置）测试的公共构造助手（纯函数，无 I/O，无凭据）。

测试目录无 `__init__.py`，基名须全局唯一；本文件由 `tests/conftest.py` 把 `tests/` 置于 `sys.path`
之后以 `from config_r26_support import ...` 导入（同 `folder_r25_support.py` 的做法）。
"""

from __future__ import annotations

import json
from typing import Any

from ib.core import (
    ELSE_BRANCH,
    ConditionBranch,
    ConditionPredicate,
    ExpertSpecInput,
    GraphEdge,
    GraphNode,
    GraphSpec,
    KnowledgeScope,
    RouteSpecInput,
    ToolGrantSpec,
)

SEARCH = "search_knowledge"


def expert(
    name: str,
    *,
    default: bool = False,
    keywords: tuple[str, ...] = (),
    status: str = "active",
    max_steps: int | None = None,
    folders: tuple[str, ...] | None = None,
    label: str | None = None,
    exemplars: tuple[str, ...] = (),
) -> ExpertSpecInput:
    scope = KnowledgeScope() if folders is None else KnowledgeScope(mode="folders", folder_ids=tuple(folders))
    return ExpertSpecInput(
        name=name,
        cn_label=label or f"标签-{name}",
        keywords=tuple(keywords),
        exemplars=tuple(exemplars),
        is_data_expert=False,
        is_delegating=False,
        is_default=default,
        status=status,  # type: ignore[arg-type]
        max_steps=max_steps,
        knowledge_scope=scope,
    )


def node(nid: str, kind: str, **kw: Any) -> GraphNode:
    return GraphNode(id=nid, kind=kind, **kw)  # type: ignore[arg-type]


def agent_node(name: str, **kw: Any) -> GraphNode:
    return GraphNode(id=name, kind="agent", expert=name, **kw)


def edge(eid: str, src: str, dst: str, key: str | None = None) -> GraphEdge:
    return GraphEdge(id=eid, source=src, target=dst, branch_key=key)


def graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphSpec:
    return GraphSpec(nodes=tuple(nodes), edges=tuple(edges))


def route_graph(*names: str, default: str | None = None) -> GraphSpec:
    """start → route-1 → 每个 agent → end；__else__ 指向 default（缺省第一个）。"""
    default = default or names[0]
    nodes = [node("start", "start"), node("route-1", "route"), node("end", "end")] + [agent_node(n) for n in names]
    edges = [edge("e-start", "start", "route-1")]
    for i, n in enumerate(names):
        edges.append(edge(f"e-r{i}", "route-1", n, n))
        edges.append(edge(f"e-o{i}", n, "end"))
    edges.append(edge("e-else", "route-1", default, ELSE_BRANCH))
    return graph(nodes, edges)


def keyword_pred(**branches: tuple[str, ...]) -> ConditionPredicate:
    return ConditionPredicate(
        kind="keyword", branches=tuple(ConditionBranch(key=k, keywords=tuple(v)) for k, v in branches.items())
    )


def error_codes(errs: Any) -> list[str]:
    return [e.code for e in errs]


def make_v2_document(
    project_id: str,
    experts: tuple[ExpertSpecInput, ...],
    spec: GraphSpec | None = None,
    *,
    grants: dict[str, tuple[str, ...]] | None = None,
    tau: float = 0.65,
    max_expert_steps: int = 8,
):
    """合法 v2 定义文档（哈希由内容决定）。"""
    from ib.config import build_definition_document
    from ib.core import OrchestrationSpecInput

    names = [e.name for e in experts if e.status == "active"]
    default = next(e.name for e in experts if e.is_default)
    g = spec if spec is not None else route_graph(*names, default=default)
    if grants is None:
        grants = {n: (SEARCH,) for n in names}
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=RouteSpecInput(tau=tau, margin=0.05, max_expert_steps=max_expert_steps, default_expert=default),
        orchestration=OrchestrationSpecInput(nodes=(), conditional_edges=(), edges=()),
        tool_grants=tuple(ToolGrantSpec(expert_name=k, tool_names=v) for k, v in grants.items()),
        schema_version=2,
        graph=g,
    )


def doc_json(doc: Any) -> dict[str, Any]:
    from ib.config import document_to_json

    return json.loads(document_to_json(doc))


def prompt_refs(*names: str):
    """提示词域通过所需的文件引用（每个专家 main 层存在）。"""
    from ib.core import ExpertPromptDocumentRef

    return tuple(
        ExpertPromptDocumentRef(expert_name=n, layer="main", rel_path=f"{n}/main.md",
                                content_hash="sha256:x", exists=True)
        for n in names
    )


# --------------------------------------------------------------------------- #
# 与已装配 deps / HTTP 客户端配合的助手（集成 / E2E 使用）
# --------------------------------------------------------------------------- #

BILLING_PROMPT = "你是账单助手。命中资料时给出来源（文件名与位置）；未检索到依据时明确答复“未检索到”；需要时调用检索工具。"


def v2_with_billing(deps, project_id: str, *, keywords=("发票", "报销"), max_steps: int | None = None,
                    folders: tuple[str, ...] | None = None):
    """在项目当前文档（v1 或 v2）基础上追加 billing-agent，返回 (v2 文档, 新专家提示词补丁)。"""
    from dataclasses import replace

    from ib.config.definition import upgrade_to_v2
    from ib.core import PromptLayers

    cur = upgrade_to_v2(deps.definition_store.load(project_id))
    keep = tuple(e for e in cur.experts if e.name != "billing-agent")
    experts = keep + (expert("billing-agent", keywords=keywords, label="账单助手", max_steps=max_steps, folders=folders),)
    default = cur.route.default_expert
    names = [e.name for e in experts if e.status == "active"]
    g = route_graph(*names, default=default)
    grants = tuple(x for x in cur.tool_grants if x.expert_name != "billing-agent") + (
        ToolGrantSpec("billing-agent", (SEARCH,)),)
    doc = replace(cur, experts=experts, graph=g, tool_grants=grants)
    from ib.config import semantic_hash

    doc = replace(doc, content_hash=semantic_hash(doc))
    return doc, {"billing-agent": PromptLayers(BILLING_PROMPT, None)}


def publish(deps, project_id: str, doc, prompts=None, *, actor: str = "tester", message: str | None = None):
    from ib.confsvc import PublishRequest

    base = deps.version_store.head(project_id).published_version
    return deps.publish_service.publish(
        PublishRequest(project_id=project_id, actor=actor, base_version=base, document=doc,
                       prompts=prompts or {}, message=message)
    )


class ExpertRecorder:
    """记录离线 LLM 替身被哪个 agent 以什么系统提示词构造（测试替身上的观测点，不改产品代码）。"""

    def __init__(self, deps, monkeypatch):
        self.calls: list[tuple[str, str | None]] = []
        orig = deps.llm.build_expert

        def rec(spec, *, system_prompt=None):
            self.calls.append((spec.name, system_prompt))
            return orig(spec, system_prompt=system_prompt)

        monkeypatch.setattr(deps.llm, "build_expert", rec)

    @property
    def experts(self) -> list[str]:
        return [c[0] for c in self.calls]

    def clear(self) -> None:
        self.calls.clear()


def ask(deps, project_id: str, question: str, session: str = "s1", *, lease=None):
    """走真实运行时租约 + 编排器完成一次提问，返回 (事件类型列表, 所用配置版本号)。"""
    from conftest import request_ctx

    lease = lease or deps.runtime_for(project_id)
    events = list(
        lease.compiled.orchestrator.run(question, ctx=request_ctx(project_id), session_key=f"{project_id}:tester:{session}")
    )
    return [str(e.kind) for e in events], lease.compiled.version


class Api:
    """HTTP 客户端助手：admin 首登改密 → 建 ops 账号（view/edit/manage）→ 各账号改密登录 → 带令牌/项目头发请求。

    口令均为测试占位值（非生产凭据，性质同 conftest 的 R13_*_PASSWORD）。
    """

    ADMIN_NEW = "R26-Test-Admin-New-1!"
    USER_PW = "R26-Test-User-Init-1!"
    USER_NEW = "R26-Test-User-New-1!"

    def __init__(self, deps, Client):
        import json as _j

        from conftest import R13_ADMIN_PASSWORD, bearer, change_password, login

        self.deps, self.client, self._json = deps, Client(), _j
        r = login(self.client, "admin", R13_ADMIN_PASSWORD)
        assert r.status_code == 200, r.content
        tok = _j.loads(r.content)["token"]
        assert change_password(self.client, tok, R13_ADMIN_PASSWORD, self.ADMIN_NEW).status_code == 200
        self.tokens = {"admin": tok}
        self._bearer, self._login, self._change = bearer, login, change_password

    def add_user(self, username: str, project: str, level: str) -> str:
        j = self._json
        r = self.client.post(
            "/api/accounts",
            data=j.dumps({"username": username, "password": self.USER_PW, "project_id": project, "config_level": level}),
            content_type="application/json", **self._bearer(self.tokens["admin"]),
        )
        assert r.status_code == 201, r.content
        user_id = j.loads(r.content)["user_id"]
        lr = self._login(self.client, username, self.USER_PW)
        assert lr.status_code == 200, lr.content
        tok = j.loads(lr.content)["token"]
        assert self._change(self.client, tok, self.USER_PW, self.USER_NEW).status_code == 200
        self.tokens[username] = tok
        return user_id

    def call(self, method: str, path: str, who: str = "admin", body: Any = None, project: str | None = "p_alpha",
             force_header: bool = False):
        extra = dict(self._bearer(self.tokens[who]))
        if project and (who == "admin" or force_header):
            extra["HTTP_X_IB_PROJECT"] = project
        kw: dict[str, Any] = {}
        if body is not None:
            kw = {"data": self._json.dumps(body), "content_type": "application/json"}
        resp = getattr(self.client, method.lower())(path, **kw, **extra)
        resp.json_body = None
        try:
            resp.json_body = self._json.loads(resp.content) if resp.content else None
        except Exception:  # noqa: BLE001 - SSE 等非 JSON 响应
            resp.json_body = None
        return resp

    def get(self, path, who="admin", **kw):
        return self.call("GET", path, who, **kw)

    def post(self, path, body=None, who="admin", **kw):
        return self.call("POST", path, who, body if body is not None else {}, **kw)

    def put(self, path, body=None, who="admin", **kw):
        return self.call("PUT", path, who, body if body is not None else {}, **kw)


def publish_body(doc, base_version: int, prompts: dict | None = None, message: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"base_version": base_version, "document": doc_json(doc)}
    if prompts:
        body["prompts"] = {n: {k: v for k, v in (("main", p.main), ("fallback", p.fallback)) if v is not None}
                           for n, p in prompts.items()}
    if message:
        body["message"] = message
    return body


def document_payload(doc) -> dict[str, Any]:
    """定义文档 → HTTP 请求体里的 document（JSON 对象）。"""
    return doc_json(doc)
