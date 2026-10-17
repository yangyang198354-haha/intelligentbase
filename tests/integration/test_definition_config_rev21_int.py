"""集成测试层 —— REV-21 编排图「专家节点实显」端点契约（IFC-IB-393；ADR-52）。

覆盖用户故事：**US-IB-51**（实显本项目实际配置的专家）、**US-IB-52**（专家集合变更后图随之更新）、
**US-IB-53**（边 / 结构节点一致且可区分）。
对应验收标准：AC-IB-51-01/02/03/04、AC-IB-52-01、AC-IB-53-01/02、AC-IB-54-02。

分层依据（`test_plan.md` §2）：覆盖**跨模块**接缝 —— `ibweb.views`（HTTP 端点）↔
`ibweb.serializers`（显示投影展开）↔ `ib.config` 定义文档存储（装载 → 派生）⇒ **集成级**。
纯函数展开的分支覆盖见 `tests/unit/test_orchestration_expert_nodes_r21.py`。

离线纪律：全程内存替身定义文档存储；无外部网络；测试代码不含真实凭据。
**被测源码 `src/**` 全程只读**。
"""

from __future__ import annotations

import json
import os

from ib.config import InMemoryDefinitionDocumentStore, build_definition_document
from ib.core import (
    ConditionalEdgeSpec,
    EdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
)

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
PATH = "/api/config/definition"

_STRUCTURAL = {"route", "general", "gate", "aggregate"}
_PLACEHOLDER = "expert"


def _expert(name: str, cn_label: str, *, is_default: bool = False) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=cn_label,
        keywords=(f"k{name}",),
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _placeholder_orchestration() -> OrchestrationSpecInput:
    """内置默认编排流（专家以单一字面量占位节点 `expert` 表达；schema 本轮未改）。"""
    return OrchestrationSpecInput(
        nodes=("route", _PLACEHOLDER, "general", "gate", "aggregate"),
        conditional_edges=(
            ConditionalEdgeSpec("route", ((_PLACEHOLDER, _PLACEHOLDER), ("general", "general"))),
        ),
        edges=(
            EdgeSpec("START", "route"),
            EdgeSpec(_PLACEHOLDER, "gate"),
            EdgeSpec("gate", "aggregate"),
            EdgeSpec("general", "aggregate"),
            EdgeSpec("aggregate", "END"),
        ),
    )


def _doc(experts: tuple[ExpertSpecInput, ...]):
    return build_definition_document(
        project_id="p_alpha",
        experts=experts,
        route=RouteSpecInput(
            tau=0.65, margin=0.05, max_expert_steps=8, default_expert=experts[0].name
        ),
        orchestration=_placeholder_orchestration(),
        tool_grants=(),
    )


def _install_document(deps, doc) -> None:
    """把 `p_alpha` 的定义文档换成给定文档（模拟「已装配 / 已保存」的项目实况）。

    GET 端点请求期直读 `deps.definition_store`，故替换存储即等价于「该项目文档如此」。
    """
    deps.definition_store = InMemoryDefinitionDocumentStore(
        documents={"p_alpha": doc}, known_tools=frozenset({"search_knowledge"})
    )


# --------------------------------------------------------------------------- #
# TC-INT-R21-001 —— AC-IB-51-02/04 + [ARCH-ASSUMPTION-A16]：端点信封与 derived 键契约
# --------------------------------------------------------------------------- #


def test_TC_INT_R21_001_default_doc_envelope_and_derived_keys(http_app):
    """[TC-INT-R21-001] US-IB-51 / AC-IB-51-02 + AC-IB-51-04：`GET /api/config/definition` 的
    默认文档（唯一 kb-agent）经端点返回时 —— 恰一个专家节点、标签取 `cn_label`，且信封**顶层键**
    与 `derived` **既有 5 键键名**不变（仅新增 `experts`），既有消费者不受影响（[ARCH-ASSUMPTION-A16]）。
    """
    deps, Client = http_app
    payload = json.loads(Client().get(PATH, **AUTH).content)

    # 顶层键**未增**：仍为既有四键
    assert set(payload) == {"document", "derived", "editable_fields", "config_key_names"}, set(payload)
    # derived 既有 5 键键名不变；本轮仅**新增** experts（加成式契约）
    existing_five = {"capability_digest", "expert_names", "nodes", "conditional_edges", "edges"}
    assert existing_five <= set(payload["derived"]), set(payload["derived"])
    assert set(payload["derived"]) == existing_five | {"experts"}, set(payload["derived"])

    # 默认文档（REV-20/ADR-50：唯一 kb-agent）⇒ 恰一个专家节点；占位节点不残留
    d = payload["derived"]
    assert d["expert_names"] == ["kb-agent"], d["expert_names"]
    assert "kb-agent" in d["nodes"]
    assert _PLACEHOLDER not in d["nodes"], d["nodes"]
    assert d["experts"] == [
        {"name": "kb-agent", "cn_label": d["experts"][0]["cn_label"], "is_default": True}
    ]
    assert d["experts"][0]["cn_label"], d["experts"]
    # experts 条目**不含**工具授权摘要（OQ-IB-53=A）
    for entry in d["experts"]:
        assert set(entry) == {"name", "cn_label", "is_default"}, entry
    # 结构节点保留且与专家节点不相交
    assert _STRUCTURAL <= set(d["nodes"]), d["nodes"]


# --------------------------------------------------------------------------- #
# TC-INT-R21-002 —— AC-IB-51-01/03、AC-IB-53-01/02、AC-IB-54-02：多专家端点逐专家展开
# --------------------------------------------------------------------------- #


def test_TC_INT_R21_002_multi_expert_projection_through_endpoint(http_app):
    """[TC-INT-R21-002] US-IB-51/53 / AC-IB-51-01 + AC-IB-51-03 + AC-IB-53-01/02 + AC-IB-54-02：
    两专家项目经端点返回时 —— 逐专家成节点、**不含**字面量 `expert`、条件边仍为**一条**且分支覆盖
    逐专家 + `general`、普通边逐专家镜像且主干边保留、结构节点保留。
    """
    deps, Client = http_app
    _install_document(deps, _doc((_expert("a", "标签a", is_default=True), _expert("b", "标签b"))))

    payload = json.loads(Client().get(PATH, **AUTH).content)
    d = payload["derived"]

    # 逐专家成节点、占位节点零残留、节点数 == 专家集规模
    assert "a" in d["nodes"] and "b" in d["nodes"], d["nodes"]
    assert _PLACEHOLDER not in d["nodes"], d["nodes"]
    expert_nodes = sorted(n for n in d["nodes"] if n not in _STRUCTURAL)
    assert expert_nodes == ["a", "b"] == sorted(d["expert_names"])
    # 结构节点保留
    assert _STRUCTURAL <= set(d["nodes"]), d["nodes"]

    # 单条件边：branch_map 逐专家 + general（与运行期 fan-out 语义一致）
    assert len(d["conditional_edges"]) == 1, d["conditional_edges"]
    ce = d["conditional_edges"][0]
    assert ce["from_node"] == "route"
    assert ce["branch_map"] == [["a", "a"], ["b", "b"], ["general", "general"]], ce["branch_map"]

    # 普通边逐专家镜像 + 主干边原样保留
    assert d["edges"] == [
        {"from_node": "START", "to_node": "route"},
        {"from_node": "a", "to_node": "gate"},
        {"from_node": "b", "to_node": "gate"},
        {"from_node": "gate", "to_node": "aggregate"},
        {"from_node": "general", "to_node": "aggregate"},
        {"from_node": "aggregate", "to_node": "END"},
    ], d["edges"]
    # 专家标识取自定义文档集合（标签 + 默认标记）
    assert d["experts"] == [
        {"name": "a", "cn_label": "标签a", "is_default": True},
        {"name": "b", "cn_label": "标签b", "is_default": False},
    ], d["experts"]


# --------------------------------------------------------------------------- #
# TC-INT-R21-003 —— 冲突负例：专家名与结构节点 / 合成端点同名 ⇒ 端点 503（fail-closed）
# --------------------------------------------------------------------------- #


def test_TC_INT_R21_003_conflicting_expert_name_returns_503_not_500(http_app):
    """[TC-INT-R21-003] US-IB-51/53 / AC-IB-51-01 + AC-IB-53-02：专家名与结构节点 `route` 同名时，
    显示投影展开抛 `ConfigError`，经**既有 fail-closed 通道**返回 **503**（而非 500、亦非静默改名
    后的半成品信封）。这是「装配期错误不得产出半成品」的端点面证据。
    """
    deps, Client = http_app
    _install_document(deps, _doc((_expert("route", "冲突标签", is_default=True),)))

    resp = Client().get(PATH, **AUTH)
    assert resp.status_code == 503, (resp.status_code, resp.content)
    body = json.loads(resp.content)
    assert body["error"]["code"] == "dependency_unavailable", body
    # **不返回半成品信封**：不得出现 document / derived 键（否则等于静默改名后照常渲染）
    assert "derived" not in body and "document" not in body, body


def test_TC_INT_R21_003b_conflict_names_never_silently_renamed_via_endpoint(http_app):
    """[TC-INT-R21-003b] 各冲突名（`gate` / `START` / `END`）经端点均得 503，**不**产出任何
    含「改名后节点」的信封。参数化替代：逐名逐一断言（每条独立 http_app 夹具，隔离存储）。
    """
    for name in ("gate", "START", "END"):
        deps, Client = http_app
        _install_document(deps, _doc((_expert(name, "冲突标签", is_default=True),)))
        resp = Client().get(PATH, **AUTH)
        assert resp.status_code == 503, (name, resp.status_code, resp.content)
        text = resp.content.decode("utf-8")
        # 不得出现「原名加后缀」的变体（静默改名的形态）
        assert f"{name}_" not in text, (name, text)
