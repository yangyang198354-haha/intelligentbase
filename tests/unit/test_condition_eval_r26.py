"""[REV-26 / GROUP_D] MOD-R26-02 `evaluate_condition`：条件分支仅关键词 / upstream_degraded（A03，无代码执行入口）。

溯源：US-006 / AC-006-02、US-011 / AC-011-05 / AC-011-06（OQ-R26-A03）。层级：单元。
"""

from __future__ import annotations

from config_r26_support import keyword_pred

from ib.config.graph import DEGRADED_BRANCH, evaluate_condition
from ib.core import ELSE_BRANCH, ConditionPredicate


def test_TC_UNIT_R26_040_keyword_hit_returns_branch_key():
    """A03：命中关键词 → 返回该分支键；大小写与首尾空白不敏感。"""
    p = keyword_pred(billing=("发票", "Invoice"), tech=("报错",))
    assert evaluate_condition(p, query="  我的INVOICE怎么开 ", upstream_degraded=False) == "billing"
    assert evaluate_condition(p, query="系统报错了", upstream_degraded=False) == "tech"


def test_TC_UNIT_R26_041_no_hit_returns_else():
    """A03：无命中 → __else__。"""
    p = keyword_pred(billing=("发票",))
    assert evaluate_condition(p, query="今天天气", upstream_degraded=False) == ELSE_BRANCH


def test_TC_UNIT_R26_042_first_declared_branch_wins():
    """分支声明顺序即优先级（确定性）。"""
    p = keyword_pred(first=("甲",), second=("甲",))
    assert evaluate_condition(p, query="甲", upstream_degraded=False) == "first"


def test_TC_UNIT_R26_043_upstream_degraded_predicate():
    """A03：upstream_degraded 谓词 → 'degraded' / __else__，与 query 无关。"""
    p = ConditionPredicate(kind="upstream_degraded")
    assert evaluate_condition(p, query="任意", upstream_degraded=True) == DEGRADED_BRANCH
    assert evaluate_condition(p, query="任意", upstream_degraded=False) == ELSE_BRANCH


def test_TC_UNIT_R26_044_query_is_never_interpreted_as_code():
    """US-011 / AC-011-06：用户问题里的表达式/代码样式文本只当字面量比较，不被求值。"""
    p = keyword_pred(k=("__import__('os')",))
    payload = "__import__('os').system('echo x') ; 1+1"
    assert evaluate_condition(p, query=payload, upstream_degraded=False) == "k"  # 字面子串命中
    assert evaluate_condition(keyword_pred(k=("2",)), query="1+1", upstream_degraded=False) == ELSE_BRANCH


def test_TC_UNIT_R26_045_blank_keyword_never_matches():
    """边界：空白关键词不匹配任何文本（防全匹配）。"""
    p = keyword_pred(k=("   ",))
    assert evaluate_condition(p, query="任意文本", upstream_degraded=False) == ELSE_BRANCH
