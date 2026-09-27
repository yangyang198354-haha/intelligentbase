"""单测层 R12 增量 —— 定义文档**专家内部**路由关键词校验的补测（BLK-R8-02 / REV-12-5）。

溯源：`docs/user_stories.md` AC-IB-18-02；`docs/architecture_design.md` ADR-16；
`src/ib/config/definition.py` 校验第 12 项（R8 纯追加）：
  * 空 / 纯空白关键词 → `expert_keyword_empty`；
  * 归一化（`strip().lower()`）后重复 → `expert_keyword_duplicate`。
背景：第 10 项只判「**跨**专家撞车」，把「**同一**专家内」的空 / 重复留给派生安装期的
`ib.experts.validate_specs`（ValueError 兜底）。BLK-R8-02 指出：直接改文档的写入路径在
`validate` 通过后才走到派生安装，若文档层放行，则错误定位（哪个专家、哪个词）与
`ValidationErrorItem` 可读回执都会丢失，且违背 REQ-FUNC-IB-27 的 fail-fast 口径。

与既有 TC-UNIT-062/065（`test_definition_uniqueness_r8.py` / `_extra_r8.py`）的关系：
  * 后者测**跨**专家撞车（第 10 项）；本文件测**专家内部**（第 12 项），并加**对照**：
    跨专家撞车仍报旧码 `expert_keyword_collision`，**不**被新码误报；
  * 既有编号与断言**保持原样不动**，本文件只**追加**（TC-UNIT-074 起）。

分层依据（test_plan §2）：仅调用 `ib.config.definition.validate` 纯函数 + frozen 数据结构，
无 I/O，故为**单元级**。纪律：测试代码不含任何真实 token/key/密码。
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
# 构造助手（关键词显式传入，避免派生基线干扰新增校验）
# --------------------------------------------------------------------------- #


def _expert(
    name: str,
    keywords: tuple[str, ...],
    *,
    is_default: bool = False,
) -> ExpertSpecInput:
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}",
        keywords=keywords,
        exemplars=(),
        is_data_expert=False,
        fallback_prompt=f"prompt-{name}",
        is_delegating=False,
        is_default=is_default,
    )


def _doc(*experts: ExpertSpecInput):
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


def _items(report, code: str):
    return [i for i in report.errors if i.code == code]


# --------------------------------------------------------------------------- #
# TC-UNIT-074 —— BLK-R8-02：专家内部空关键词 → expert_keyword_empty
# --------------------------------------------------------------------------- #


def test_TC_UNIT_074_intra_expert_empty_keyword():
    """[TC-UNIT-074] US-IB-18 / AC-IB-18-02（BLK-R8-02）：**同一专家内**空关键词被定位报出。

    验收点：
      * 空串 `""` / 纯空白 `"   "` → `expert_keyword_empty`，每个各一条；
      * path 精确到 `experts[{name}].keywords[{原文}]`（原文，非归一化值）；
      * 空关键词**不**误报为 `expert_keyword_duplicate`（避免同词两报）；
      * 仅「跨专家」有同词、且各自非空时，**不**产生内部空码（对照，防止新码范围外溢）。
    """
    # 空串 + 纯空白：各一条，path 用原文
    rep = validate(_doc(_expert("a", ("", "   ", "正常词"), is_default=True)))
    empties = _items(rep, "expert_keyword_empty")
    assert len(empties) == 2, [(i.path, i.message) for i in empties]
    assert {i.path for i in empties} == {"experts[a].keywords[]", "experts[a].keywords[   ]"}
    assert rep.ok is False
    # 空关键词不得同时被报为「重复」
    assert "expert_keyword_duplicate" not in _codes(rep), "空关键词被误报为重复"

    # 对照：跨专家同词（均非空）→ 仍报旧码，且**不**产生内部空码
    cross = validate(_doc(_expert("a", ("共享",), is_default=True), _expert("b", ("共享",))))
    assert "expert_keyword_collision" in _codes(cross)
    assert "expert_keyword_empty" not in _codes(cross)
    assert "expert_keyword_duplicate" not in _codes(cross)


# --------------------------------------------------------------------------- #
# TC-UNIT-075 —— BLK-R8-02：专家内部归一化重复 → expert_keyword_duplicate
# --------------------------------------------------------------------------- #


def test_TC_UNIT_075_intra_expert_normalized_duplicate_and_no_misreport():
    """[TC-UNIT-075] US-IB-18 / AC-IB-18-02（BLK-R8-02）：**同一专家内**归一化重复被定位报出。

    验收点：
      * 大小写 / 首尾空白差异（`"KWH"` vs `" kwh "`）归一化后相同 → `expert_keyword_duplicate`；
      * 每对重复逐条报出（首见者持有，后续各一条），path 用后续词原文；
      * **对照（关键）**：跨专家撞车仍报旧码 `expert_keyword_collision`，**不**被新码
        `expert_keyword_duplicate` 误报（新码不越界到跨专家场景）；
      * **对照**：全不相同关键词的合法文档 → `ok=True` 且**无任何**新码（无误报）。
    """
    # 同一专家内归一化重复：a 内 "KWH" 与 " kwh " 归一化后相同
    rep = validate(_doc(_expert("a", ("KWH", " kwh ", "其他"), is_default=True)))
    dups = _items(rep, "expert_keyword_duplicate")
    assert len(dups) == 1, [(i.path, i.message) for i in dups]
    assert dups[0].path == "experts[a].keywords[ kwh ]", dups[0].path
    assert "KWH" in dups[0].message
    assert rep.ok is False

    # 三词两两重复：首见者持有，后续两词各一条（不按对数倍增）
    tri = validate(_doc(_expert("a", ("k1", "k1", "K1"), is_default=True)))
    tri_dups = _items(tri, "expert_keyword_duplicate")
    assert len(tri_dups) == 2, [(i.path, i.message) for i in tri_dups]
    assert {i.path for i in tri_dups} == {"experts[a].keywords[k1]", "experts[a].keywords[K1]"}

    # 对照①：跨专家同词 → 旧码，**不**误报新码
    cross = validate(_doc(_expert("a", ("用电",), is_default=True), _expert("b", ("用电",))))
    assert "expert_keyword_collision" in _codes(cross), "跨专家撞车码丢失（旧契约被破坏）"
    assert "expert_keyword_duplicate" not in _codes(cross), "新码越界误报跨专家场景"
    assert "expert_keyword_empty" not in _codes(cross)

    # 对照②：全不相同 → 合法，无任何新码
    ok = validate(
        _doc(
            _expert("a", ("用电", "电压"), is_default=True),
            _expert("b", ("电流", "电阻")),
        )
    )
    assert ok.ok is True, [(i.code, i.path) for i in ok.errors]
    assert not ({"expert_keyword_duplicate", "expert_keyword_empty"} & _codes(ok))
