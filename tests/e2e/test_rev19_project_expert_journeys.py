"""[REV-19 / GROUP_D] 端到端关键路径 —— 项目域专家集隔离（US-IB-41/43/44/45）。

每个用例在 docstring 标注所属 **US-IB-NN**（用户故事级覆盖的证据）。
关键路径 = Must Have 故事（US-IB-41 / US-IB-43 / US-IB-44 / US-IB-45 均属 Must Have）。

覆盖 REV-19 中**只有走完整旅程才成立**的验收标准：

  * AC-IB-43-01 / AC-IB-43-03（项目内闭环路由：只用本项目专家集，绝不调用他项目 / demo 专家）；
  * AC-IB-44-01 / 44-03 / 44-04 / 44-05 / 44-06（新建项目创建期播种 → 重启重装配 → 开箱闭环）；
  * AC-IB-45-02（非 demo 项目的可用专家集不含三专家）；
  * AC-IB-42-05（保存后**未重启**仍用既有配置，**重启后**生效 —— 沿用 ADR-32）。

离线口径：fake LLM + 内存会话 + 临时目录定义 / 提示词载体；不触网、不碰生产路径。
「重启」以**新进程视角重新装载 + 重新装配**模拟（与生产手工重启走同一装配序列）。
"""

from __future__ import annotations

import json

from conftest import R13_ADMIN_PASSWORD, bearer, change_password, login, request_ctx

DEF = "/api/config/definition"
DEF_PATH_HEADER = "HTTP_X_IB_PROJECT"

#: 测试内占位口令（**非生产凭据**，性质同 conftest 的 `groupd-offline-token`）。
_ADMIN_NEW_PW = "Rev19-E2E-Admin-New!"


def _graph_spec():
    from ib.core import ConditionalEdgeSpec, EdgeSpec, OrchestrationSpecInput

    return OrchestrationSpecInput(
        nodes=("route", "expert", "general", "gate", "aggregate"),
        conditional_edges=(
            ConditionalEdgeSpec(from_node="route", branch_map=(("expert", "expert"),)),
        ),
        edges=(
            EdgeSpec(from_node="START", to_node="route"),
            EdgeSpec(from_node="expert", to_node="gate"),
            EdgeSpec(from_node="gate", to_node="aggregate"),
            EdgeSpec(from_node="general", to_node="aggregate"),
            EdgeSpec(from_node="aggregate", to_node="END"),
        ),
    )


def _spec(name, *, is_default=False, keywords=()):
    from ib.core import ExpertSpecInput

    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}",
        keywords=tuple(keywords),
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _view(*specs):
    from ib.core import DerivedView

    return DerivedView(experts=tuple(specs), capability_digest="", graph_config=_graph_spec())


def _doc(project_id: str, expert_names: tuple[str, ...], *, tau: float = 0.65):
    """构造一份合法定义文档（恰一个默认专家 + 单一默认编排流），供文件载体落盘。"""
    from ib.config import build_definition_document
    from ib.core import RouteSpecInput, ToolGrantSpec

    experts = tuple(
        _spec(name, is_default=(i == 0), keywords=(f"kw{name}",))
        for i, name in enumerate(expert_names)
    )
    return build_definition_document(
        project_id=project_id,
        experts=experts,
        route=RouteSpecInput(
            tau=tau, margin=0.05, max_expert_steps=8, default_expert=expert_names[0]
        ),
        orchestration=_graph_spec(),
        tool_grants=tuple(
            ToolGrantSpec(expert_name=name, tool_names=("search_knowledge",))
            for name in expert_names
        ),
    )


def _run_graph(deps, registry, project_id: str, question: str, session_key: str):
    """以**指定专家集 + 编排**跑一次完整问答，返回事件列表（端到端链路）。"""
    from ib.core import GraphConfig, Scope
    from ib.orchestration import build_graph
    from ib.routing import IntentRouter
    from ib.streaming import MemorySessionStore

    scope = Scope(project_id=project_id)
    bound = deps.bind_tools(scope)
    orch = build_graph(
        llm=deps.llm,
        experts=registry.experts,
        tools=bound,
        sessions=MemorySessionStore(),
        config=GraphConfig(),
        router=IntentRouter(experts=registry),
        scope=scope,
        tools_by_expert={name: bound for name in registry.names()},
    )
    return list(orch.run(question, ctx=request_ctx(project_id), session_key=session_key))


# --------------------------------------------------------------------------- #
# US-IB-43（项目内闭环）+ US-IB-41（硬隔离）
# 溯源：AC-IB-43-01 / 43-03 / 41-02（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R19_001_project_question_routes_only_within_project_set(deps):
    """US-IB-43：项目内提问只在**本项目专家集**内路由 / 聚合，绝不调用他项目专家。

    **REV-20（ADR-50）契约翻转**：原「对照组 = demo 三专家集命中 `inspection-expert`」不再
    成立（三专家退役，`builtin_expert_registry()` 亦为唯一 `kb-agent`）；隔离改由「项目 A 的
    路由结果 ∈ A 的项目集」+「端到端链路不出现任何业务域专家名」表达。
    """
    from ib.core import Scope
    from ib.experts import builtin_expert_registry, resolve_expert_registry
    from ib.routing import IntentRouter

    q = "巡检一下 PLC 故障，顺便看看能耗"

    # 项目 A 自己的专家集：默认 alpha-agent + alpha-ops（覆盖巡检 / 故障）
    reg_a = resolve_expert_registry(
        "p_alpha",
        view=_view(
            _spec("alpha-agent", is_default=True, keywords=("能耗", "用电")),
            _spec("alpha-ops", keywords=("巡检", "故障", "plc")),
        ),
    )

    # REV-20：内置注册表 == 唯一通用 kb-agent（无任何业务域专家）
    assert builtin_expert_registry().names() == ("kb-agent",)

    # AC-IB-43-01 / 43-03：项目 A 内提问只在 A 的专家集内路由，不回退他项目专家
    d_a = IntentRouter(experts=reg_a).classify_experts(q, scope=Scope(project_id="p_alpha"))
    assert set(d_a.experts) <= {"alpha-agent", "alpha-ops"}, d_a.experts

    # 端到端跑通一问一答：单版融合答案 + 终结 done；事件面不出现业务域专家
    events = _run_graph(deps, reg_a, "p_alpha", q, "p_alpha:e2e_r19_1")
    kinds = [str(e.kind) for e in events]
    assert kinds.count("content") == 1, f"非单版答案：{kinds}"
    assert kinds[-1] == "done", kinds
    blob = " ".join(str(e) for e in events)
    for retired in ("freeark-expert", "inspection-expert", "sanheng-knowledge"):
        assert retired not in blob, f"端到端链路出现业务域专家：{retired}"


# --------------------------------------------------------------------------- #
# US-IB-44（新建项目默认种子）+ US-IB-45（三专家归属 demo）
# 溯源：AC-IB-44-01 / 44-03 / 44-04 / 44-05 / 44-06 / 45-02（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R19_002_new_project_seed_then_closed_loop(deps, tmp_path):
    """US-IB-44：创建期播种 → 「重启」重装配 → 新项目开箱完成问答闭环。

    **REV-20（ADR-48 / ADR-51）**：种子提示词**在创建期落盘**（`<root>/<pid>/<expert>/main.md`），
    文件载体构造不再注入任何内置兜底映射。
    """
    from ib.config import FileDefinitionDocumentStore
    from ib.core import Scope
    from ib.experts import resolve_expert_registry
    from ibweb.composition import known_tool_names, seed_project

    defs = tmp_path / "defs"
    prompts = tmp_path / "prompts"

    # ① 创建期播种（AC-IB-44-01 / 44-03）：按项目落地定义 + **提示词落盘**
    res = seed_project("proj_new", definition_dir=str(defs), prompt_root=str(prompts))
    assert res.created is True
    assert res.expert_names == ("kb-agent",), res.expert_names
    assert res.orchestration == "default"
    assert (defs / "proj_new.json").is_file(), "未按项目落地种子定义文档"
    assert (prompts / "proj_new" / "kb-agent" / "main.md").is_file(), "未落盘种子提示词 main.md"

    # ② 「重启」重装配视角：从磁盘读回 → 准入派生
    store = FileDefinitionDocumentStore(str(defs), known_tools=known_tool_names())
    doc = store.load("proj_new")

    # AC-IB-44-01 / 44-04：默认专家恰一个（内置不可删兜底 KB agent）；AC-IB-45-02：无业务域专家
    reg = resolve_expert_registry("proj_new", view=store.derive(doc))
    assert reg.names() == ("kb-agent",)
    assert reg.default_name() == "kb-agent"

    # AC-IB-44-06：单一默认编排流程（无用户自定义 DAG 入口，OOS-21）
    nodes = set(doc.orchestration.nodes)
    assert {"route", "expert", "general", "gate", "aggregate"} <= nodes, nodes
    assert len(doc.route and [doc.route.default_expert]) == 1

    # AC-IB-44-05：开箱即可闭环（检索 → 作答），无需先手工配置
    events = _run_graph(deps, reg, "proj_new", "本项目知识库里有什么？", "proj_new:e2e_r19_2")
    kinds = [str(e.kind) for e in events]
    assert kinds.count("content") == 1, f"新项目未能给出单版答案：{kinds}"
    assert kinds[-1] == "done", kinds


# --------------------------------------------------------------------------- #
# US-IB-42（按项目保存）
# 溯源：AC-IB-42-05（保存后未重启仍用既有配置；重启后生效 —— ADR-32）（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R19_003_save_definition_takes_effect_only_after_restart(accounts_app, tmp_path):
    """US-IB-42：定义保存后**未重启**仍用既有配置（图对象未重建），**重启重装配**后生效。

    **REV-20（ADR-48）**：文件载体构造不再注入内置兜底映射；同时按定义文档专家集**预填
    提示词层**（否则保存期会以 `prompt_missing` fail-closed 拒绝）。
    """
    from ib.config import FileDefinitionDocumentStore, InMemoryExpertPromptStore
    from ibweb.composition import build_application, known_tool_names

    deps, Client = accounts_app

    # 以**文件载体**落盘项目 A / B 的现行定义（生产形态 = 独立目录），再重装配
    store = FileDefinitionDocumentStore(str(tmp_path), known_tools=known_tool_names())
    store.save("p_alpha", _doc("p_alpha", ("alpha-agent",), tau=0.65), expected_content_hash=None)
    store.save("p_beta", _doc("p_beta", ("beta-agent",)), expected_content_hash=None)
    deps.definition_store = store
    for pid in ("p_alpha", "p_beta"):
        loaded = store.load(pid)
        deps.definitions[pid] = loaded
        deps.derived_views[pid] = store.derive(loaded)
        # REV-20（ADR-48 / ADR-51 ③）：每位专家都要在提示词域有可取值
        deps.prompt_stores[pid] = InMemoryExpertPromptStore(
            pid, documents={e.name: {"main": f"# {e.name} 主提示词\n"} for e in loaded.experts}
        )
    build_application(deps)

    client = Client()
    h = bearer(_admin_login(client))

    # 运行期现行图（尚未重启）：以 tau=0.65 装配一次并常驻
    graph_before = deps.orchestrator_for("p_alpha")

    # ① 保存一次变更（tau → 0.72）
    cur = json.loads(client.get(DEF, **h, **{DEF_PATH_HEADER: "p_alpha"}).content)["document"]
    edited = json.loads(json.dumps(cur))
    edited["route"]["tau"] = 0.72
    put = client.put(
        DEF,
        data=json.dumps({"document": edited, "expected_content_hash": cur["content_hash"]}),
        content_type="application/json",
        **h,
        **{DEF_PATH_HEADER: "p_alpha"},
    )
    assert put.status_code == 200, put.content

    # ② REV-26 重新基线（取代 REQ-FUNC-IB-40 / C-IB-40 / ADR-32 的“保存 + 重启后生效”，见 CL-003 与
    #    requirements_spec 取代登记）：保存即热生效——无需重启，编排器已换成新版本（升级前基线 v1 + 本次 v2）。
    after = deps.orchestrator_for("p_alpha")
    assert after is not graph_before, "保存后应已热生效（REV-26 取代“重启后生效”）"
    assert deps.runtime_for("p_alpha").compiled.version == 2

    # ③ 「重启」= 新进程视角：新 store 实例从磁盘读回 → 变更生效
    fresh = FileDefinitionDocumentStore(str(tmp_path), known_tools=known_tool_names())
    reloaded = fresh.load("p_alpha")
    assert reloaded.route.tau == 0.72, "重启重装配后未取到新配置"


def _admin_login(client) -> str:
    """admin 登录 + 改初始口令（生产强制首登改密），返回可用令牌。"""
    r = login(client, "admin", R13_ADMIN_PASSWORD)
    assert r.status_code == 200, r.content
    token = json.loads(r.content)["token"]
    done = change_password(client, token, R13_ADMIN_PASSWORD, _ADMIN_NEW_PW)
    assert done.status_code == 200, done.content
    return token
