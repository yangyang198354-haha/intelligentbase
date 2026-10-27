"""[REV-26 / GROUP_D] 存量项目平滑升级：v1 旧形态项目上线后（未重新保存）`legacy` 固定拓扑与 `dag` 路径对 20 个固定提问的路由/作答专家集合一致；
上线与提问全程不改写定义文档文件（字节级零改写）。

溯源：US-020（AC-020-01/02）、REQ-NFUNC-012、ADR-58（IB_GRAPH_RUNTIME 开关）。层级：集成。
"""

from __future__ import annotations

import hashlib
import pathlib

import pytest
from config_r26_support import SEARCH, ExpertRecorder, ask

from ib.config import FileDefinitionDocumentStore, InMemoryExpertPromptStore, build_definition_document
from ib.core import (
    ConditionalEdgeSpec,
    EdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    ToolGrantSpec,
)

P = "p_alpha"
QUESTIONS = [
    "我的发票怎么报销", "报销流程是什么", "开发票需要什么", "知识库里有什么", "帮我检索文档", "资料在哪里", "问答功能怎么用",
    "你好", "今天天气", "谢谢", "发票和资料都要查", "查一下知识", "报销 发票 资料", "随便聊聊", "再见", "什么是检索",
    "文档管理", "FAQ 在哪", "常见问题", "没有关键词的一句话",
]


def _v1_doc():
    ex = (
        ExpertSpecInput("kb-agent", "知识库助手", ("知识库", "资料", "文档", "检索"), (), True, False, True),
        ExpertSpecInput("faq-agent", "财务助手", ("发票", "报销"), (), False, False, False),
    )
    orch = OrchestrationSpecInput(
        nodes=("route", "expert", "general", "gate", "aggregate"),
        conditional_edges=(ConditionalEdgeSpec(from_node="route", branch_map=(("expert", "expert"), ("general", "general"))),),
        edges=(EdgeSpec("START", "route"), EdgeSpec("expert", "gate"), EdgeSpec("gate", "aggregate"),
               EdgeSpec("general", "aggregate"), EdgeSpec("aggregate", "END")),
    )
    return build_definition_document(
        project_id=P, experts=ex, route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="kb-agent"),
        orchestration=orch, tool_grants=(ToolGrantSpec("kb-agent", (SEARCH,)), ToolGrantSpec("faq-agent", (SEARCH,))),
    )


def _boot(tmp_path, monkeypatch, runtime):
    from ibweb.composition import build_application, build_deps, known_tool_names

    from conftest import offline_raw

    monkeypatch.setenv("IB_GRAPH_RUNTIME", runtime)
    deps = build_deps(offline_raw(), force=True)
    store = FileDefinitionDocumentStore(str(tmp_path / runtime), known_tools=known_tool_names())
    store.save(P, _v1_doc(), expected_content_hash=None)
    for pid in ("p_beta",):
        pass
    deps.definition_store = store
    loaded = store.load(P)
    deps.definitions[P] = loaded
    deps.derived_views[P] = store.derive(loaded)
    deps.prompt_stores[P] = InMemoryExpertPromptStore(P, documents={e.name: {"main": f"你是 {e.name}。"} for e in loaded.experts})
    build_application(deps)
    return deps, store


def _def_file(tmp_path, runtime) -> pathlib.Path:
    files = list((tmp_path / runtime).rglob("*.json"))
    assert files, "定义文档文件应已落盘"
    return files[0]


def _answers(deps, monkeypatch):
    rec = ExpertRecorder(deps, monkeypatch)
    out = []
    for i, q in enumerate(QUESTIONS):
        rec.clear()
        kinds, _v = ask(deps, P, q, f"q{i}")
        out.append((tuple(sorted(rec.experts)), kinds.count("done")))
    return out


def test_TC_INT_R26_130_dag_and_legacy_runtime_agree_on_20_questions_without_resave(tmp_path, monkeypatch):
    """US-020 / AC-020-01（重点）：旧形态多专家项目未重新保存，dag 路径与 legacy 固定拓扑对 20 个固定提问的作答专家集合完全一致（20/20），
    每次恰好 1 个完成事件；运行版本为虚拟版本 0。"""
    deps_legacy, _ = _boot(tmp_path, monkeypatch, "legacy")
    assert deps_legacy.runtime_for(P).compiled.dag is None and deps_legacy.runtime_for(P).compiled.version == 0
    legacy = _answers(deps_legacy, monkeypatch)
    deps_dag, _ = _boot(tmp_path, monkeypatch, "dag")
    assert deps_dag.runtime_for(P).compiled.dag is not None and deps_dag.runtime_for(P).compiled.version == 0
    dag = _answers(deps_dag, monkeypatch)
    assert len(legacy) == len(dag) == 20
    mismatches = [(q, a, b) for q, a, b in zip(QUESTIONS, legacy, dag) if a != b]
    assert mismatches == [], f"不一致 {len(mismatches)}/20：{mismatches[:3]}"
    assert all(done == 1 for _e, done in dag)
    assert any(len(e) >= 1 and "faq-agent" in e for e, _ in dag) and any("kb-agent" in e for e, _ in dag)


def test_TC_INT_R26_131_rollout_and_questions_do_not_rewrite_definition_file(tmp_path, monkeypatch):
    """US-020 / AC-020-02：上线（装配 + 冷编译 + 提问 + 读配置页）后，既有项目定义文档文件哈希与上线前完全一致（零改写）。"""
    deps, _store = _boot(tmp_path, monkeypatch, "dag")
    f = _def_file(tmp_path, "dag")
    before = hashlib.sha256(f.read_bytes()).hexdigest()
    mtime = f.stat().st_mtime_ns
    _answers(deps, monkeypatch)
    deps.runtime_cache.invalidate(P)
    deps.runtime_for(P)
    deps.publish_service.current(P)
    assert hashlib.sha256(f.read_bytes()).hexdigest() == before and f.stat().st_mtime_ns == mtime
    assert deps.version_store.head(P).published_version == 0, "未保存 → 不产生版本行"


def test_TC_INT_R26_132_graph_runtime_switch_rejects_unknown_value(monkeypatch):
    """ADR-58：IB_GRAPH_RUNTIME 只接受 dag / legacy，其余值启动即失败（只登记键名，不回显值）。"""
    from ibweb.composition import build_deps

    from conftest import offline_raw
    from ib.core import StartupError

    monkeypatch.setenv("IB_GRAPH_RUNTIME", "turbo")
    with pytest.raises(StartupError) as ei:
        build_deps(offline_raw(), force=True)
    assert "turbo" not in str(ei.value)
