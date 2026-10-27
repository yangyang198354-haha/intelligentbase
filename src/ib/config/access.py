"""
@module MOD-R26-03
@implements IFC-R26-020 配置访问档位（view / edit / manage）纯函数
@depends MOD-R26-01

ADR-60：档位映射到现有账号与项目授权，不改 `AuthzPolicy` 端口。纯函数，无 I/O。
"""

from __future__ import annotations

from typing import Final, Literal, Mapping

from ib.core import LEVEL_RANK, AuthzContext, ConfigLevel

__all__ = [
    "LEVEL_TOKEN_PREFIX",
    "ConfigAction",
    "REQUIRED_LEVEL",
    "config_level_of",
    "allows",
    "level_token",
    "roles_with_level",
    "can_grant",
]

LEVEL_TOKEN_PREFIX: Final[str] = "cfg:"

ConfigAction = Literal[
    "read", "validate", "preview", "publish", "draft", "trial", "builder",
    "rollback", "adopt_drift", "grant_access", "read_audit",
]

REQUIRED_LEVEL: Final[Mapping[str, ConfigLevel]] = {
    "read": "view",
    "validate": "edit",
    "preview": "edit",
    "publish": "edit",
    "draft": "edit",
    "trial": "edit",
    "builder": "edit",
    "rollback": "manage",
    "adopt_drift": "manage",
    "grant_access": "manage",
    "read_audit": "manage",
}


def config_level_of(authz: AuthzContext) -> ConfigLevel:
    """admin 恒 manage；含 `cfg:<level>` 令牌取最高有效档；仅 manager 无令牌（旧令牌 / 离线策略）视为 manage；
    无任何角色 → view（已通过项目授权的主体）。"""
    roles = authz.roles
    if "admin" in roles:
        return "manage"
    best: ConfigLevel | None = None
    for r in roles:
        if r.startswith(LEVEL_TOKEN_PREFIX):
            lv = r[len(LEVEL_TOKEN_PREFIX):]
            if lv in LEVEL_RANK and (best is None or LEVEL_RANK[lv] > LEVEL_RANK[best]):
                best = lv  # type: ignore[assignment]
    if best is not None:
        return best
    if "manager" in roles:
        return "manage"
    return "view"


def allows(level: ConfigLevel, action: ConfigAction) -> bool:
    need = REQUIRED_LEVEL.get(action)
    if need is None:
        return False  # 未知动作 fail-closed
    return LEVEL_RANK[level] >= LEVEL_RANK[need]


def level_token(level: ConfigLevel) -> str:
    if level not in LEVEL_RANK:
        raise ValueError("unknown config level")
    return f"{LEVEL_TOKEN_PREFIX}{level}"


def roles_with_level(roles: tuple[str, ...], level: ConfigLevel) -> tuple[str, ...]:
    """去掉既有 `cfg:*` 令牌后追加指定档位令牌。"""
    kept = tuple(r for r in roles if not r.startswith(LEVEL_TOKEN_PREFIX))
    return kept + (level_token(level),)


def can_grant(grantor: AuthzContext, *, grantor_project_id: str, target_project_id: str) -> bool:
    """授予档位：要求 manage，且目标项目 == 授予者所在（admin 经 X-IB-Project 选定的）项目。"""
    if config_level_of(grantor) != "manage":
        return False
    return bool(target_project_id) and target_project_id == grantor_project_id
