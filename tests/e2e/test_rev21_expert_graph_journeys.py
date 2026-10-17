"""[REV-21 / GROUP_D] 端到端关键路径 —— 编排图「专家节点实显」（US-IB-51 / US-IB-52 / US-IB-54）。

每个用例在 docstring 标注所属 **US-IB-NN**（用户故事级覆盖的证据）。
关键路径 = Must Have 故事（US-IB-51 / US-IB-52 / US-IB-54 均属 Must Have）。

覆盖 REV-21 中**只有走完整旅程才成立**的验收标准：

  * AC-IB-51-01 / 51-03（走「配置专家 → 打开配置页 → 看编排图」全程，图上逐专家成节点）；
  * AC-IB-52-01（专家集合**新增**专家并保存后，图上新出现该专家节点，总数与集合一致）；
  * AC-IB-52-02（专家集合**删除**专家后，图上不再出现该节点，图仍可读 + 完整）；
  * AC-IB-52-03（图仍只读：拓扑不可编辑 —— 编排不在可编辑白名单，无改图入口）；
  * AC-IB-54-02（专家节点数与专家集合规模一致）。

离线口径：内存替身定义文档 / 提示词存储 + 离线 Bearer 令牌；不触网、不碰生产路径。
「保存并经服务重启后生效」以**端点写回 → 以文档为准重读**的机制层覆盖（ADR-32 口径，
与既有 R7 / REV-19 E2E 同一策略）。
"""

from __future__ import annotations

import json
import os

from ib.config import (
    InMemoryDefinitionDocumentStore,
    InMemoryExpertPromptStore,
    build_definition_document,
)
from ib.core import (
    ConditionalEdgeSpec,
    EdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
)

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
DEF = "/api/config/definition"

_STRUCTURAL = {"route", "general", "gate", "aggregate"}
_PLACEHOLDER = "expert"


def _expert(name: str, *, is_default: bool = False) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}",
        keywords=(f"k{name}",),
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _graph_spec() -> OrchestrationSpecInput:
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


def _doc(names: tuple[str, ...]):
    experts = tuple(_expert(n, is_default=(i == 0)) for i, n in enumerate(names))
    return build_definition_document(
        project_id="p_alpha",
        experts=experts,
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert=names[0]),
        orchestration=_graph_spec(),
        tool_grants=(),
    )


def _setup_project(deps, names: tuple[str, ...]) -> None:
    """把 `p_alpha` 装成 `names` 专家集：内存定义文档 + 各专家 `main` 提示词层。"""
    deps.definition_store = InMemoryDefinitionDocumentStore(
        documents={"p_alpha": _doc(names)}, known_tools=frozenset({"search_knowledge"})
    )
    _set_prompts(deps, names)


def _set_prompts(deps, names: tuple[str, ...]) -> None:
    """把该项目提示词域置为 `names`（各专家 `main` 层）—— 模拟「提示词先落盘 / 目录先清理」。

    跨域校验（`validate_two_domains`）要求：定义文档声明的每位专家**皆有**提示词
    （否则 `prompt_missing`），且目录**不得**含未登记专家的孤儿文件（否则 `prompt_orphan_file`）。
    故「新增专家」前须先落盘其提示词，「删除专家」前须先清理其提示词目录 —— 这正是生产口径。
    """
    deps.prompt_stores["p_alpha"] = InMemoryExpertPromptStore(
        "p_alpha", documents={n: {"main": f"# {n} 主提示词\n"} for n in names}
    )


def _expert_nodes(derived: dict) -> list[str]:
    return sorted(n for n in derived["nodes"] if n not in _STRUCTURAL)


def _put_document(client, document: dict, expected: str):
    return client.put(
        DEF,
        data=json.dumps({"document": document, "expected_content_hash": expected}),
        content_type="application/json",
        **AUTH,
    )


# --------------------------------------------------------------------------- #
# US-IB-52（专家集合变更后图随之更新）+ US-IB-51（实显）+ US-IB-54（规模一致）
# 溯源：AC-IB-52-01 / 51-01 / 51-03 / 54-02（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R21_001_add_expert_grows_graph(http_app):
    """US-IB-52：在专家集合**新增**一位专家并保存后，编排图上**新出现**该专家节点，
    专家节点总数与专家集合一致（AC-IB-52-01 / AC-IB-54-02）；图仍只读（AC-IB-52-03）。

    旅程：① 打开配置页（GET）看到 2 专家图 → ② 保存新增第 3 位专家（PUT）→
    ③ 以文档为准重读（GET）→ 图上出现 3 个专家节点、占位节点零残留。
    """
    deps, Client = http_app
    _setup_project(deps, ("a", "b"))
    client = Client()

    # ① 打开配置页：逐专家成节点、占位节点不残留
    first = json.loads(client.get(DEF, **AUTH).content)
    assert _expert_nodes(first["derived"]) == ["a", "b"], first["derived"]["nodes"]
    assert _PLACEHOLDER not in first["derived"]["nodes"]
    # AC-IB-52-03：编排（拓扑）**不在**可编辑白名单 ⇒ 界面无改图入口
    assert "orchestration" not in first["editable_fields"], first["editable_fields"]

    # ② 保存新增第 3 位专家：先按其落盘提示词（生产口径），再保存定义文档
    _set_prompts(deps, ("a", "b", "c"))
    edited = json.loads(json.dumps(first["document"]))
    edited["experts"].append(
        {
            "name": "c",
            "cn_label": "标签c",
            "keywords": ["kc"],
            "exemplars": [],
            "is_data_expert": False,
            "is_delegating": False,
            "is_default": False,
        }
    )
    saved = _put_document(client, edited, first["document"]["content_hash"])
    assert saved.status_code == 200, saved.content
    assert json.loads(saved.content)["ok"] is True

    # ③ 以文档为准重读：图上新出现 c；专家节点总数 == 专家集合规模
    after = json.loads(client.get(DEF, **AUTH).content)
    assert _expert_nodes(after["derived"]) == ["a", "b", "c"], after["derived"]["nodes"]
    assert _PLACEHOLDER not in after["derived"]["nodes"]
    assert len(_expert_nodes(after["derived"])) == len(after["document"]["experts"]) == 3
    # 条件边仍一条、分支覆盖逐专家 + general；结构节点保留
    assert len(after["derived"]["conditional_edges"]) == 1
    assert ["c", "c"] in after["derived"]["conditional_edges"][0]["branch_map"]
    assert _STRUCTURAL <= set(after["derived"]["nodes"])


# --------------------------------------------------------------------------- #
# US-IB-52（删除专家）+ US-IB-54（删除后仍可读 + 完整）
# 溯源：AC-IB-52-02 / 54-01 / 54-02（关键路径）
# --------------------------------------------------------------------------- #


def test_TC_E2E_R21_002_remove_expert_keeps_graph_readable_and_complete(http_app):
    """US-IB-52：在专家集合**删除**一位专家后，编排图上**不再出现**该节点，且图仍满足
    「可读 + 完整」（结构节点与主干边齐全，节点数==专家集规模）（AC-IB-52-02 / AC-IB-54-01 / 54-02）。

    旅程：① 3 专家项目 GET 看到 3 节点 → ② 保存删除第 3 位（PUT）→ ③ 重读 GET 图上只剩 2 专家节点。
    """
    deps, Client = http_app
    _setup_project(deps, ("a", "b", "c"))
    client = Client()

    first = json.loads(client.get(DEF, **AUTH).content)
    assert _expert_nodes(first["derived"]) == ["a", "b", "c"], first["derived"]["nodes"]

    # ② 保存删除第 3 位：先清理其提示词目录（生产口径，避免 `prompt_orphan_file`），再保存定义文档
    _set_prompts(deps, ("a", "b"))
    edited = json.loads(json.dumps(first["document"]))
    edited["experts"] = [e for e in edited["experts"] if e["name"] != "c"]
    saved = _put_document(client, edited, first["document"]["content_hash"])
    assert saved.status_code == 200, saved.content

    after = json.loads(client.get(DEF, **AUTH).content)
    d = after["derived"]
    assert "c" not in d["nodes"], d["nodes"]
    assert ["c", "c"] not in d["conditional_edges"][0]["branch_map"]
    assert _expert_nodes(d) == ["a", "b"]
    assert len(_expert_nodes(d)) == len(after["document"]["experts"]) == 2

    # 图仍「可读 + 完整」：结构节点与主干边齐全（gate / aggregate 不成孤立方块）
    assert _STRUCTURAL <= set(d["nodes"]), d["nodes"]
    for edge in (
        {"from_node": "START", "to_node": "route"},
        {"from_node": "gate", "to_node": "aggregate"},
        {"from_node": "general", "to_node": "aggregate"},
        {"from_node": "aggregate", "to_node": "END"},
    ):
        assert edge in d["edges"], edge
    assert [e for e in d["edges"] if e["from_node"] in ("a", "b")] == [
        {"from_node": "a", "to_node": "gate"},
        {"from_node": "b", "to_node": "gate"},
    ], d["edges"]
