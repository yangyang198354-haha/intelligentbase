"""
@module MOD-IB-23
@implements IFC-IB-322 SessionTokenResolver（内置 PrincipalResolver）
            IFC-IB-326 LoginThrottle + 认证审计事件（**条件性**，ADR-27）
            账户装配期的配置读取（IFC-IB-312 键名；口令策略 / TTL / 种子用户名）
@depends MOD-IB-01（端口与令牌原语）, MOD-IB-03（上下文）, MOD-IB-11（账户存储）
@author software-developer

账户与会话的**接入层**（R13 增量；module_design.md §3 MOD-IB-23）。

## 两个必须分开的东西

```
Authorization: Bearer <token>
        │  第 1 件：令牌 → 主体（PrincipalResolver = SessionTokenResolver，本模块）
        ▼
   AuthzContext(actor_id, project_id, roles)
        │  第 2 件：主体 → 能不能做（AuthzPolicy，注入；本包 policy.py 是内置实现之一）
        ▼
   can_manage / can_query
```

`SessionTokenResolver` **只做第 1 件**：把令牌换成主体。它**不做任何授权判定** ——
判定仍只经注入的 `AuthzPolicy`（ADR-22；「第二授权真源」是被明令禁止的）。

## 全局主体与项目绑定

`admin` 是**全局**账户（`project_id IS NULL`），`ops` 绑定单项目。为把「全局」表达在
既有的 `AuthzContext.project_id: str` 上（该字段的契约受 IFC-IB-001~308 保护、**一字不动**），
全局主体用哨兵值 `GLOBAL_PROJECT`（`"*"`）标记，而非 `None`。中间件据此判定「该主体可操作
任意项目」，并允许 `X-IB-Project` 为其选定当前项目（AC-IB-24-03）。

## 凭据纪律

令牌**只**从 `Authorization` 头进入；本层只做 sha256 摘要后查表（`token_digest`）。
口令校验经 `ib.ledger.accounts.verify_password`（bcrypt）。本层**不记录**任何口令 / 令牌。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ib.context import utc_now_iso
from ib.core import (
    AccountStatus,
    AuthzContext,
    PasswordPolicy,
    StartupError,
    UserRecord,
    token_digest,
)

__all__ = [
    "GLOBAL_PROJECT",
    "AccountSettings",
    "load_account_settings",
    "password_policy",
    "validate_password_strength",
    "effective_roles",
    "SessionTokenResolver",
]

#: 全局主体的 `AuthzContext.project_id` 哨兵值。
#: 为什么用 `"*"` 而不是 `None`：`AuthzContext.project_id` 的类型（`str`）受
#: 「IFC-IB-001~308 一字不动」保护；哨兵值使全局语义在**不动机场字段**的前提下显式可读
#: （见 implementation_plan §19 的 [DEVIATION] 说明）。
GLOBAL_PROJECT = "*"

#: 会话有效期默认值（秒）。design 标注 [TBD-T22]（OQ-IB-09 待裁决）；此处取 12 小时，
#: 经 `IB_SESSION_TTL_SECONDS` 可覆盖。给默认值而非「未声明即启动失败」的理由：TTL 是
#: 可用性参数（不是安全开关），一个保守默认不会造成 fail-open。
_DEFAULT_SESSION_TTL_SECONDS = 12 * 3600

#: 续期窗口默认值（秒）：剩余有效期低于它才允许 `renew`（避免会话无限续期）。
_DEFAULT_RENEW_WINDOW_SECONDS = 3600

#: 默认管理员用户名（**用户名非机密**，故给默认值；口令**必须**经环境变量注入）。
_DEFAULT_ADMIN_USERNAME = "admin"

#: 口令最小长度默认值（OQ-IB-11 待裁决；保守取值）。
_DEFAULT_PASSWORD_MIN_LENGTH = 8


@dataclass(frozen=True, slots=True)
class AccountSettings:
    """账户装配期设置（全部来自环境变量；**不含任何口令 / 密钥**）。"""

    account_backend: str
    session_ttl_seconds: int
    renew_window_seconds: int
    default_admin_username: str
    password_min_length: int


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise StartupError(f"环境变量 {name} 必须为整数（只登记键名，不回显值）") from exc


def load_account_settings() -> AccountSettings:
    """读取账户相关环境变量（IFC-IB-312 的键名）。

    `IB_DEFAULT_ADMIN_PASSWORD` **不在此读取** —— 它在装配期由种子步骤单独取值，
    且**绝不**进入任何返回结构（口令值不进内存中的「设置对象」）。
    """
    return AccountSettings(
        account_backend=os.environ.get("IB_ACCOUNT_BACKEND", "sqlite").strip() or "sqlite",
        session_ttl_seconds=_env_int("IB_SESSION_TTL_SECONDS", _DEFAULT_SESSION_TTL_SECONDS),
        renew_window_seconds=_env_int(
            "IB_SESSION_RENEW_WINDOW_SECONDS", _DEFAULT_RENEW_WINDOW_SECONDS
        ),
        default_admin_username=os.environ.get(
            "IB_DEFAULT_ADMIN_USERNAME", _DEFAULT_ADMIN_USERNAME
        ).strip()
        or _DEFAULT_ADMIN_USERNAME,
        password_min_length=_env_int("IB_PASSWORD_MIN_LENGTH", _DEFAULT_PASSWORD_MIN_LENGTH),
    )


def password_policy(min_length: int | None = None) -> PasswordPolicy:
    """口令强度策略（`require_classes=2`：小写 / 大写 / 数字 / 符号 中至少命中 2 类）。"""
    if min_length is None:
        min_length = load_account_settings().password_min_length
    return PasswordPolicy(min_length=max(1, int(min_length)), require_classes=2)


def validate_password_strength(password: str, policy: PasswordPolicy | None = None) -> str | None:
    """校验口令强度（服务端**唯一裁决者**）。

    返回 `None` 表示通过；否则返回可读中文原因（**不含口令本身**，AC-IB-18-04 精神）。
    """
    policy = policy or password_policy()
    if len(password) < policy.min_length:
        return f"口令长度不足（至少 {policy.min_length} 位）"
    classes = 0
    if any(ch.islower() for ch in password):
        classes += 1
    if any(ch.isupper() for ch in password):
        classes += 1
    if any(ch.isdigit() for ch in password):
        classes += 1
    if any(not ch.isalnum() for ch in password):
        classes += 1
    if classes < policy.require_classes:
        return f"口令复杂度不足（至少需包含 {policy.require_classes} 类字符：大小写 / 数字 / 符号）"
    return None


def effective_roles(user: UserRecord) -> tuple[str, ...]:
    """账户角色 → `AuthzContext.roles` 的映射（ADR-21）。

    `admin` → `("admin",)`（全局）；`ops` → `("manager",)`（等价既有 manager 语义，
    项目边界由 `project_id` 承载）。**仅做身份映射，不做授权判定**。
    """
    return ("admin",) if user.role == "admin" else ("manager",)


class SessionTokenResolver:
    """令牌 → 主体（IFC-IB-322；`PrincipalResolver` 的内置实现）。

    fail-closed 链：`token_digest_matches`/查表 → `resolve_session`（未过期未撤销）→
    反查 `UserRecord`（存在且 `status="active"`）→ 构造 `AuthzContext`。**任一不满足返回 `None`**。

    与 `EnvTokenResolver` 一样，`resolve` **不抛异常**（抛异常会被承载层当作 500）。
    """

    def __init__(self, store: Any, *, now_fn: Any = utc_now_iso) -> None:
        self._store = store
        self._now = now_fn

    def resolve(self, token: str) -> AuthzContext | None:
        if not token:
            return None
        digest = token_digest(token)
        session = self._store.resolve_session(digest, now=self._now())
        if session is None:
            return None
        user = self._store.get_user(session.user_id)
        if user is None or user.status != "active":
            return None
        roles = effective_roles(user)
        # 全局（admin）用哨兵；绑定账户用其项目 id。
        project_id = user.project_id if user.project_id is not None else GLOBAL_PROJECT
        return AuthzContext(actor_id=user.user_id, project_id=project_id, roles=roles)


def is_global(authz: AuthzContext) -> bool:
    """该主体是否为**全局**主体（可操作任意项目）。仅 `admin` 账户成立（ADR-21）。"""
    return authz.project_id == GLOBAL_PROJECT


#: 账户状态字面量的显式再导出（便于调用方做 `status == "active"` 判定，避免字符串漂移）。
ACTIVE: AccountStatus = "active"
DISABLED: AccountStatus = "disabled"
