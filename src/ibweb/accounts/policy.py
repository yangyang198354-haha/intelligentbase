"""
@module MOD-IB-23
@implements IFC-IB-323 内置可注入策略模块 `ibweb.accounts.policy`（暴露 POLICY + resolve_principal）
@depends MOD-IB-03（AuthzPolicy 端口）, MOD-IB-23（accounts 包的 SessionTokenResolver）
@author software-developer

**内置**的可注入策略模块（R13）。接入方在 `IB_AUTHZ_POLICY_MODULE` 中指向本模块即可启用
内建账户体系：

```
IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy
IB_ACCOUNT_BACKEND=sqlite           # 或 memory（离线替身）
```

## 为什么不「自动启用」

本模块**只**在 `IB_AUTHZ_POLICY_MODULE` 显式指向它时才被装配（`build_authz` 的既有语义）。
`build_authz` 里**不**做任何「检测到账户表就自动挂上」的推断 —— 那会造出**第二授权真源**
（ADR-22 / REQ-FUNC-IB-33）。未配置即 `StartupError`（fail-closed，沿用 checklists B9）。

## 授权判定的唯一性

`POLICY` 是 `AuthzPolicy`（IFC-IB-032/033）的实现：**只**回答「能不能管 / 能不能问」。
「这个令牌是谁」由 `resolve_principal`（→ `SessionTokenResolver`）回答。二者职责不混。
"""

from __future__ import annotations

from typing import Any

from ib.core import AuthzContext

__all__ = ["POLICY", "resolve_principal", "AccountsPolicy"]


class AccountsPolicy:
    """内建授权策略（IFC-IB-032/033 的实现之一）。

    语义：
      * `admin`（全局）：可管可问（任意项目，项目由 `X-IB-Project` 选定，AC-IB-24-03）；
      * `ops`（绑定单项目）：可管可问，但**项目边界**由主体自身的 `project_id` 承载 ——
        中间件已保证其 `project_id` 恒等于绑定项目，且声明它项目的请求被 403。

    它是一个**平凡策略**（按角色放行）；真正的边界在「主体构造」与「项目断言」两处，
    而非此处 —— 这种分工使「谁能做什么」集中在端口上，「谁是谁」集中在解析器上。
    """

    name = "ibweb.accounts"

    def can_manage(self, ctx: AuthzContext) -> bool:
        return bool({"admin", "manager"} & set(ctx.roles))

    def can_query(self, ctx: AuthzContext) -> bool:
        return bool({"admin", "manager"} & set(ctx.roles))


#: 模块级策略实例（`build_authz` 的 `_load_policy_module` 读取 `POLICY`）。
POLICY = AccountsPolicy()


def resolve_principal(token: str) -> AuthzContext | None:
    """令牌 → 主体（供 `build_authz` 的通用加载路径调用）。

    账户存储取自**组合根**（`get_deps().account_store`）—— 这样本模块无需在导入期持有
    任何全局状态，`IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy` 的通用加载路径即可工作。
    """
    from ibweb.accounts import SessionTokenResolver
    from ibweb.composition import get_deps

    deps = get_deps()
    store: Any = getattr(deps, "account_store", None)
    if store is None:  # pragma: no cover - 装配保证存在；防御性分支
        return None
    return SessionTokenResolver(store).resolve(token)
