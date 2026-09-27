"""单元测试层 6/N —— R8 定义文档装配期「唯一性」校验（IFC-IB-290；纯函数，离线可跑）。

文件：`tests/unit/test_definition_uniqueness_r8.py`（基名与既有
`tests/unit/test_definition_data_layer_r7.py` **不同**以免 pytest 模块名撞车）。

溯源：本文件为 **FND-R7-01（MAJOR）** 修复的验证用例（登记处：
`docs/test_report.md` §12.6 / §12.10；设计依据：`docs/architecture_design.md` ADR-16、
`docs/user_stories.md` AC-IB-18-02）。覆盖 `validate` 的两项**新增**校验：
  1. 跨专家「路由关键词撞车」→ `expert_keyword_collision`；
  2. `cn_label` 唯一性 → `expert_cn_label_duplicate`。

分层依据（test_plan §2）：只调用 `ib.config.definition.validate` 与 `ib.core` 的 frozen 数据结构
（+ 只读引用 `ib.experts.EXPERT_SPECS` 的默认数据），单模块纯函数、无 I/O —— 故为**单元级**。

纪律：测试代码不含任何真实 token/key/密码；所有「凭据」均为环境变量占位符或显式标注的假值。
编号延续既有 `TC-UNIT-*` 序列（既有最高为 TC-UNIT-061）。
"""

from __future__ import annotations

from ib.config import build_definition_document, validate
from ib.core import (
    ConditionalEdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
)
from ib.experts import EXPERT_SPECS, cn_map, default_expert, keywords_map


# --------------------------------------------------------------------------- #
# 构造助手（**关键词 / 标签互不撞车**的合法基线，避免与新增校验相互干扰）
# --------------------------------------------------------------------------- #


def _expert(
    name: str,
    cn_label: str,
    keywords: tuple[str, ...],
    *,
    is_default: bool = False,
) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=cn_label,
        keywords=keywords,
        exemplars=(),
        is_data_expert=False,
        fallback_prompt=f"prompt-{name}",
        is_delegating=False,
        is_default=is_default,
    )


def _doc(
    a_keywords: tuple[str, ...],
    b_keywords: tuple[str, ...],
    *,
    a_label: str = "甲专家",
    b_label: str = "乙专家",
):
    """两位专家的定义文档（a 为默认专家）。关键词 / 标签由调用方给定。"""
    return build_definition_document(
        project_id="p1",
        experts=(
            _expert("a", a_label, a_keywords, is_default=True),
            _expert("b", b_label, b_keywords),
        ),
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="a"),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec(from_node="route", branch_map=(("a", "a"),)),),
        ),
    )


def _codes(report) -> set[str]:
    return {item.code for item in report.errors}


def _default_derived_document():
    """按 `ibweb.composition._default_definition_document` 的同一口径，由默认注册表派生文档。

    只做「默认注册表 → 定义文档」的等价映射（不改任何默认数据），用于证明**默认装配仍应通过**。
    """
    experts = tuple(
        ExpertSpecInput(
            name=s.name,
            cn_label=s.cn_label,
            keywords=tuple(s.keywords),
            exemplars=(),
            is_data_expert=s.is_data_expert,
            fallback_prompt=s.fallback_prompt,
            is_delegating=s.is_delegating,
            is_default=s.is_default,
        )
        for s in EXPERT_SPECS
    )
    names = tuple(s.name for s in EXPERT_SPECS)
    return build_definition_document(
        project_id="p_default",
        experts=experts,
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert=default_expert()),
        orchestration=OrchestrationSpecInput(
            nodes=("route",) + names,
            conditional_edges=(ConditionalEdgeSpec(from_node="route", branch_map=tuple((n, n) for n in names)),),
        ),
        tool_grants=(),
    )


# --------------------------------------------------------------------------- #
# TC-UNIT-062 —— AC-IB-18-02：跨专家「路由关键词撞车」被拒（通过 + 拒绝两分支）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_062_cross_expert_keyword_collision_is_rejected():
    """[TC-UNIT-062] US-IB-18 / AC-IB-18-02：不同专家的关键词撞车 → 装配期 fail-fast 拒绝。

    口径（R8）：归一化 = `strip().lower()`（`lower` 对齐路由消费方
    `ib/routing/intent.py::_keyword_hits` 的 `keyword.lower() in text.lower()`；`strip` 去首尾空白）。
    正向：互不相交（含大小写不同者）→ 通过；反向：精确重复 / 大小写撞车 / 空白撞车 → 逐类拒绝，
    错误**可定位**（含冲突关键词与两个专家名）。
    """
    # 通过分支：关键词集合互不相交（大小写不同者亦不相交）
    assert validate(_doc(("用电", "KWH"), ("故障", "巡检"))).ok is True
    assert _codes(validate(_doc(("用电", "KWH"), ("故障", "巡检")))) == set()

    # 拒绝分支一：精确重复
    report = validate(_doc(("用电", "参数"), ("参数", "故障")))
    assert report.ok is False
    assert "expert_keyword_collision" in _codes(report)
    item = next(i for i in report.errors if i.code == "expert_keyword_collision")
    assert item.path and item.message
    assert "参数" in item.message and "'a'" in item.message and "'b'" in item.message, item

    # 拒绝分支二：大小写撞车（KWH vs kwh 归一化后相同）
    ci = validate(_doc(("用电", "KWH"), ("kwh", "故障")))
    assert ci.ok is False and "expert_keyword_collision" in _codes(ci)

    # 拒绝分支三：首尾空白撞车（" 参数 " 去空白后与 "参数" 相同）
    ws = validate(_doc(("参数",), (" 参数 ",)))
    assert ws.ok is False and "expert_keyword_collision" in _codes(ws)

    # 同一专家内的重复**不**属于跨专家撞车（由 ib.experts.validate_specs 在派生安装期兜底）
    same_expert = validate(_doc(("用电", "用电"), ("故障",)))
    assert "expert_keyword_collision" not in _codes(same_expert)


# --------------------------------------------------------------------------- #
# TC-UNIT-063 —— AC-IB-18-02：cn_label 唯一性被拒（通过 + 拒绝两分支）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_063_duplicate_cn_label_is_rejected():
    """[TC-UNIT-063] US-IB-18 / AC-IB-18-02：不同专家的 `cn_label` 重复 → 拒绝（前端无法区分专家）。

    口径（R8）：去首尾空白后比较 —— 空白填充在界面上不可见，必须视为重复；大小写差异界面可见，不归一。
    空标签由既有第 5 项 `expert_text_missing` 单独报出，本项跳过空值以免重复告警。
    """
    # 通过分支：标签互异
    ok = validate(_doc(("用电",), ("故障",), a_label="数据管家", b_label="巡检诊断"))
    assert ok.ok is True and "expert_cn_label_duplicate" not in _codes(ok)

    # 拒绝分支一：精确重复
    dup = validate(_doc(("用电",), ("故障",), a_label="同名标签", b_label="同名标签"))
    assert dup.ok is False and "expert_cn_label_duplicate" in _codes(dup)
    item = next(i for i in dup.errors if i.code == "expert_cn_label_duplicate")
    assert item.path == "experts[b].cn_label" and item.message
    assert "同名标签" in item.message and "'a'" in item.message and "'b'" in item.message, item

    # 拒绝分支二：空白填充撞车（"同名标签 " 与 "同名标签" 去空白后相同）
    pad = validate(_doc(("用电",), ("故障",), a_label="同名标签", b_label="同名标签 "))
    assert pad.ok is False and "expert_cn_label_duplicate" in _codes(pad)

    # 空标签不计入「重复」（由 expert_text_missing 单独报出，避免重复告警）
    both_empty = validate(_doc(("用电",), ("故障",), a_label="   ", b_label=""))
    assert "expert_cn_label_duplicate" not in _codes(both_empty)
    assert "expert_text_missing" in _codes(both_empty)

    # 大小写差异**不**视为重复（标签是展示串，界面可区分）
    cased = validate(_doc(("用电",), ("故障",), a_label="KWH", b_label="kwh"))
    assert "expert_cn_label_duplicate" not in _codes(cased)


# --------------------------------------------------------------------------- #
# TC-UNIT-064 —— 默认装配不回归：默认专家表无撞车 / 无重标签 → validate 通过
# --------------------------------------------------------------------------- #


def test_TC_UNIT_064_default_registry_has_no_collisions_and_validates_ok():
    """[TC-UNIT-064] 未改 `EXPERT_SPECS` 默认数据的前提下，默认注册表**无**跨专家关键词撞车、
    `cn_label` **唯一**，故补齐两项校验后**默认装配仍应通过**（不回归）。

    这一条是对新增校验的**反向护栏**：若默认数据本身撞车，则装配将被 fail-fast 拒绝 —— 属设计不允许。
    """
    # 原始默认数据层面：跨专家关键词无交集（同口径归一化），标签唯一
    normalized: dict[str, str] = {}
    for name, kws in keywords_map().items():
        for kw in kws:
            key = kw.strip().lower()
            assert key, f"默认专家 {name} 含空关键词（不应出现）"
            assert key not in normalized or normalized[key] == name, (
                f"默认专家表出现跨专家关键词撞车：'{kw}' 归属 {normalized.get(key)} 与 {name}"
            )
            normalized[key] = name
    labels = [label.strip() for label in cn_map().values()]
    assert len(labels) == len(set(labels)), f"默认专家 cn_label 不唯一：{labels}"

    # 文档层面：默认派生文档通过全部校验，且**不含**两项新增错误码
    report = validate(_default_derived_document())
    assert report.ok is True, f"默认装配竟被拒绝：{report.errors}"
    assert "expert_keyword_collision" not in _codes(report)
    assert "expert_cn_label_duplicate" not in _codes(report)
    assert _codes(report) == set()
