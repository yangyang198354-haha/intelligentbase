"""单元测试层 7/N —— R8 定义文档「唯一性」校验的**边界分支补测**（IFC-IB-290；离线可跑）。

文件：`tests/unit/test_definition_uniqueness_extra_r8.py`（基名与既有
`tests/unit/test_definition_uniqueness_r8.py` **不同**以免 pytest 模块名撞车）。

溯源：本文件为 **FND-R7-01（MAJOR）** 修复的**补测**（software-developer 已在
`tests/unit/test_definition_uniqueness_r8.py` 就 TC-UNIT-062~064 覆盖主路径；本文件只补
其**未覆盖的边界分支**，避免重复造轮子）。设计依据：`docs/architecture_design.md` ADR-16、
`docs/user_stories.md` AC-IB-18-02。

补齐缺口（相对 TC-UNIT-062/063）：
  * 空 / 纯空白关键词**不**误报为撞车（`validate` 第 10 项 `continue` 分支）；
  * **三名及以上**专家同词 / 同标签时的报错条数与 path 归属（首见者持有，逐个后续专家各一条）；
  * 关键词撞车与 `cn_label` 重复**相互独立**、可同时产出（两项校验不互相吞并）；
  * 归一化的组合形态（大小写 + 首尾空白叠加）与**精确 path 定位**。

分层依据（test_plan §2）：只调用 `ib.config.definition.validate` 与 `ib.core` 的 frozen
数据结构 —— 单模块纯函数、无 I/O，故为**单元级**。

纪律：测试代码不含任何真实 token/key/密码。
编号延续既有 `TC-UNIT-*` 序列（既有最高为 TC-UNIT-064）。
"""

from __future__ import annotations

from ib.config import build_definition_document, validate
from ib.core import (
    ConditionalEdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
)


# --------------------------------------------------------------------------- #
# 构造助手（**关键词 / 标签随 name 派生**的合法基线，避免与新增校验相互干扰）
# --------------------------------------------------------------------------- #


def _expert(
    name: str,
    cn_label: str | None = None,
    keywords: tuple[str, ...] | None = None,
    *,
    is_default: bool = False,
) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}" if cn_label is None else cn_label,
        keywords=(f"k{name}",) if keywords is None else keywords,
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _doc(*experts: ExpertSpecInput):
    """把给定专家组装成一份定义文档；路由 `default_expert` 取自其中的默认专家。"""
    default = next(e.name for e in experts if e.is_default)
    names = tuple(e.name for e in experts)
    return build_definition_document(
        project_id="p1",
        experts=tuple(experts),
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert=default),
        orchestration=OrchestrationSpecInput(
            nodes=("route",) + names,
            conditional_edges=(
                ConditionalEdgeSpec(from_node="route", branch_map=tuple((n, n) for n in names)),
            ),
        ),
    )


def _codes(report) -> set[str]:
    return {item.code for item in report.errors}


# --------------------------------------------------------------------------- #
# TC-UNIT-065 —— AC-IB-18-02：关键词撞车的**边界分支**补测
# --------------------------------------------------------------------------- #


def test_TC_UNIT_065_keyword_collision_edge_branches():
    """[TC-UNIT-065] US-IB-18 / AC-IB-18-02：跨专家关键词撞车的边界分支。

    覆盖 TC-UNIT-062 未触及的分支：空 / 纯空白关键词跳过；三名以上专家的报错条数与
    path 归属；大小写 + 首尾空白**叠加**的归一；错误 path 的精确形态。
    """
    # 空 / 纯空白关键词**不**算撞车（非「路由命中」范畴；由专家内校验承担）—— 无误报
    blank = validate(_doc(_expert("a", keywords=("", "  "), is_default=True), _expert("b", keywords=("", "故障"))))
    assert "expert_keyword_collision" not in _codes(blank), "空关键词被误报为撞车"

    # 三名专家同词：以「首见者」为归属，逐个后续专家各一条（a↔b、a↔c），不按对数倍增
    tri = validate(
        _doc(
            _expert("a", keywords=("共享",), is_default=True),
            _expert("b", keywords=("共享",)),
            _expert("c", keywords=("共享",)),
        )
    )
    tri_items = [i for i in tri.errors if i.code == "expert_keyword_collision"]
    assert len(tri_items) == 2, [(i.path, i.message) for i in tri_items]
    assert {i.path for i in tri_items} == {
        "experts[b].keywords[共享]",
        "experts[c].keywords[共享]",
    }
    assert all("'a'" in i.message for i in tri_items), tri_items

    # 归一化叠加：大小写 + 首尾空白同时不同（" KWH " vs "kwh"）仍判为撞车
    combo = validate(_doc(_expert("a", keywords=(" KWH ",), is_default=True), _expert("b", keywords=("kwh",))))
    assert combo.ok is False and "expert_keyword_collision" in _codes(combo)

    # 精确 path 定位：分母 = 后见专家名，下标 = 原样关键词（非归一化值）
    item = next(
        i
        for i in validate(_doc(_expert("a", keywords=("用电",), is_default=True), _expert("b", keywords=("用电",)))).errors
        if i.code == "expert_keyword_collision"
    )
    assert item.path == "experts[b].keywords[用电]" and item.message


# --------------------------------------------------------------------------- #
# TC-UNIT-066 —— AC-IB-18-02：cn_label 唯一性的**边界分支**与两项校验独立性
# --------------------------------------------------------------------------- #


def test_TC_UNIT_066_cn_label_edge_branches_and_independence():
    """[TC-UNIT-066] US-IB-18 / AC-IB-18-02：`cn_label` 唯一性的边界分支，及与关键词撞车的独立性。

    覆盖 TC-UNIT-063 未触及的分支：三名以上专家同标签的报错条数与 path 归属；空白填充 +
    精确重复的组合；以及「关键词撞车」与「标签重复」**同时触发时两条错误码并存**（互不吞并）。
    """
    # 三名专家同标签 → 以首见者为归属，逐个后续专家各一条
    tri = validate(
        _doc(
            _expert("a", "同名", is_default=True),
            _expert("b", "同名"),
            _expert("c", "同名"),
        )
    )
    tri_items = [i for i in tri.errors if i.code == "expert_cn_label_duplicate"]
    assert len(tri_items) == 2, [(i.path, i.message) for i in tri_items]
    assert {i.path for i in tri_items} == {"experts[b].cn_label", "experts[c].cn_label"}
    assert all("'a'" in i.message for i in tri_items), tri_items

    # 空白填充撞车（" 同名 " vs "同名"）仍判为重复
    padded = validate(_doc(_expert("a", " 同名 ", is_default=True), _expert("b", "同名")))
    assert padded.ok is False and "expert_cn_label_duplicate" in _codes(padded)

    # 全空白标签**不**计入重复（由既有第 5 项 expert_text_missing 单独报出，避免重复告警）
    all_blank = validate(_doc(_expert("a", "   ", is_default=True), _expert("b", "  ")))
    assert "expert_cn_label_duplicate" not in _codes(all_blank)
    assert "expert_text_missing" in _codes(all_blank)

    # 两项校验**相互独立**：同一文档同时撞词 + 同标签 → 两条错误码并存
    both = validate(
        _doc(
            _expert("a", "同标签", ("共享",), is_default=True),
            _expert("b", "同标签", ("共享",)),
        )
    )
    assert both.ok is False
    assert {"expert_cn_label_duplicate", "expert_keyword_collision"} <= _codes(both)
