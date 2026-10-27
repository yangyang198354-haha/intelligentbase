"""[REV-26 / GROUP_D] MOD-R26-03 配置访问档位（view / edit / manage）。

溯源：US-010（AC-010-01/03/04）、US-017 / AC-017-03、US-023 / AC-023-04、US-004 / AC-004-04、US-009 / AC-009-04、
US-024 / AC-024-06、US-028 / AC-028-04、US-029 / AC-029-05（动作 → 所需档位表）、OQ-R26-A01。层级：单元。
"""

from __future__ import annotations

import pytest

from ib.config.access import (
    REQUIRED_LEVEL,
    allows,
    can_grant,
    config_level_of,
    level_token,
    roles_with_level,
)
from ib.core import AuthzContext


def _ctx(roles, project="p_alpha"):
    return AuthzContext(actor_id="u", project_id=project, roles=tuple(roles))


def test_TC_UNIT_R26_050_action_level_table_is_exact():
    """US-010 / US-017 / US-023：动作所需档位表固定（改动即失败）。"""
    assert REQUIRED_LEVEL == {
        "read": "view", "validate": "edit", "preview": "edit", "publish": "edit", "draft": "edit",
        "trial": "edit", "builder": "edit", "rollback": "manage", "adopt_drift": "manage",
        "grant_access": "manage", "read_audit": "manage",
    }


@pytest.mark.parametrize(
    "level,allowed",
    [
        ("view", {"read"}),
        ("edit", {"read", "validate", "preview", "publish", "draft", "trial", "builder"}),
        ("manage", set(REQUIRED_LEVEL)),
    ],
)
def test_TC_UNIT_R26_051_allows_matrix(level, allowed):
    """AC-010-01 / AC-017-03：三档各自允许的动作集合。"""
    got = {a for a in REQUIRED_LEVEL if allows(level, a)}
    assert got == allowed


def test_TC_UNIT_R26_052_unknown_action_fail_closed():
    """未知动作一律拒绝（fail-closed），连 manage 也不例外。"""
    assert allows("manage", "delete_everything") is False


def test_TC_UNIT_R26_053_level_resolution_rules():
    """OQ-R26-A01 / ADR-60：admin 恒 manage；cfg:<level> 令牌取最高；仅 manager 无令牌视为 manage；无角色为 view。"""
    assert config_level_of(_ctx(["admin"])) == "manage"
    assert config_level_of(_ctx(["manager", "cfg:view"])) == "view"
    assert config_level_of(_ctx(["manager", "cfg:view", "cfg:edit"])) == "edit"
    assert config_level_of(_ctx(["manager"])) == "manage"  # 旧令牌 / 离线策略
    assert config_level_of(_ctx([])) == "view"
    assert config_level_of(_ctx(["cfg:bogus"])) == "view"  # 未知令牌不抬权
    assert config_level_of(_ctx(["cfg:view", "admin"])) == "manage"


def test_TC_UNIT_R26_054_unknown_token_never_escalates():
    """安全：形似令牌的角色（如 'cfg:manage ' 带空白、大小写变形）不被识别为 manage。"""
    for r in ("cfg:manage ", "CFG:manage", "cfg:MANAGE", "xcfg:manage"):
        assert config_level_of(_ctx([r])) == "view", r


def test_TC_UNIT_R26_055_roles_with_level_replaces_existing_token():
    """档位令牌替换：去掉旧 cfg:* 后追加新令牌，其余角色保留。"""
    assert roles_with_level(("manager", "cfg:view"), "edit") == ("manager", "cfg:edit")
    assert level_token("manage") == "cfg:manage"
    with pytest.raises(ValueError):
        level_token("root")  # type: ignore[arg-type]


def test_TC_UNIT_R26_056_can_grant_requires_manage_and_same_project():
    """AC-010-02 / AC-010-04：授予档位须 manage 且目标项目 == 授予者所在项目（跨项目拒绝）。"""
    mgr = _ctx(["manager", "cfg:manage"], "p_alpha")
    assert can_grant(mgr, grantor_project_id="p_alpha", target_project_id="p_alpha") is True
    assert can_grant(mgr, grantor_project_id="p_alpha", target_project_id="p_beta") is False
    assert can_grant(_ctx(["manager", "cfg:edit"]), grantor_project_id="p_alpha", target_project_id="p_alpha") is False
    assert can_grant(mgr, grantor_project_id="p_alpha", target_project_id="") is False
