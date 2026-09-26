"""
@module MOD-IB-23
@implements IFC-IB-250 鉴权注入点 / AC-IB-11-05（401/403 而非静默）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-03, MOD-IB-04
@author sub_agent_software_developer

鉴权与请求上下文（MOD-IB-23 的**唯一鉴权入口**）。

## 两件事必须被分开，否则一定出漏洞

```
Authorization: Bearer <token>
        │  ← 第 1 件：令牌 → 主体（PrincipalResolver，接入方提供，业务相关）
        ▼
   AuthzContext(actor_id, project_id, roles)
        │  ← 第 2 件：主体 → 能不能做（AuthzPolicy，IFC-IB-032/033）
        ▼
   can_manage / can_query
```

基座**只**定义第 2 件的端口（`AuthzPolicy`），第 1 件由接入方注入 —— 因为「令牌长什么样、
怎么换主体」完全取决于接入方的账号体系，基座一旦内置就会变成「所有项目都用我们的账号模型」。

## 「未注入即启动失败」（AC-IB-11-05）

生产环境下若没有 `IB_AUTHZ_POLICY_MODULE`，组合根**直接启动失败**。理由是本项目最不希望出现的
失败形态：带着 `DenyAllPolicy` 启动，服务看起来健康（`/healthz` 200），但**每一个**真实请求都
静默 403 —— 排障成本极高，且很容易被误判为「前端 bug」。

## 令牌纪律（硬约束，代码里显式拒绝）

* 只认 `Authorization: Bearer <token>`；
* 查询串中出现 `token` / `access_token` / `api_key` → **400**，不是忽略。
  令牌进 URL 就会被 nginx/uvicorn 访问日志完整打印（FreeArk 已实际发生过一次 WS 令牌泄露），
  所以「能用但违规」的写法必须当场失败，否则它会一直扩散。

## 常量时间比较

令牌比对一律用 `hmac.compare_digest`：逐字符提前返回的比较函数会让攻击者按响应时间
逐位猜出令牌（经典时序侧信道），而正确写法只多一行。

## 公共端点

`/healthz` 与 `/healthz/deps` **不要求鉴权**：探针（systemd/负载均衡/监控）通常拿不到业务令牌，
要求鉴权会让「服务是否活着」这件事变得无法独立观测。二者输出中**不含业务数据**，
`/healthz/deps` 只暴露依赖连通性与「数据外发到哪个主机、外发哪几类数据」的合规声明。
"""

from __future__ import annotations

import hmac
import os
from typing import Any, Protocol, runtime_checkable

from ib.core import AuthzContext, ScopeViolationError, StartupError
from ib.context import (
    AllowAllPolicy,
    DenyAllPolicy,
    make_request_context,
)

__all__ = [
    "PrincipalResolver",
    "EnvTokenResolver",
    "AuthMiddleware",
    "build_authz",
    "parse_bearer",
    "forbidden_token_in_query",
    "PUBLIC_PATHS",
    "REQUEST_CTX_ATTR",
]

#: 请求对象上挂载 `RequestContext` 的属性名（视图只用 `get_request_context(request)` 取）。
REQUEST_CTX_ATTR = "ib_ctx"

#: 免鉴权路径（见模块文档「公共端点」）。
PUBLIC_PATHS = ("/healthz", "/healthz/deps")

#: 命中即拒绝的查询串键名（小写比较）。
_FORBIDDEN_QUERY_KEYS = ("token", "access_token", "api_key", "apikey", "authorization", "secret")


@runtime_checkable
class PrincipalResolver(Protocol):
    """令牌 → 主体。接入方提供（基座不定义账号体系）。"""

    def resolve(self, token: str) -> AuthzContext | None:
        """返回主体；令牌无效/过期返回 `None`（**不得抛异常**：抛异常会被当作 500）。"""
        ...


class EnvTokenResolver:
    """与**单个**环境变量中的令牌比对（离线自测与最小接入用）。

    刻意只支持单令牌：多令牌/多租户映射属于账号体系的职责，一旦在这里长出来，
    就会变成第二个认证真源（与接入方的策略模块并存），从而产生「策略说 A、解析器说 B」的分歧。
    """

    def __init__(
        self,
        *,
        token_env: str,
        project_id: str,
        actor_id: str = "service-account",
        roles: tuple[str, ...] = ("manager",),
    ) -> None:
        self._token_env = token_env
        self._project_id = project_id
        self._actor_id = actor_id
        self._roles = tuple(roles)
        raw = os.environ.get(token_env, "")
        if not raw:
            # 只报键名，不回显值（AC-IB-12-03）
            raise StartupError(f"缺少必填环境变量 {token_env}（离线自测的共享令牌）。只登记键名，不回显值。")
        self._expected = raw

    def resolve(self, token: str) -> AuthzContext | None:
        if not token:
            return None
        if not hmac.compare_digest(token.encode("utf-8"), self._expected.encode("utf-8")):
            return None
        return AuthzContext(actor_id=self._actor_id, project_id=self._project_id, roles=self._roles)


def parse_bearer(header_value: str) -> str:
    """从 `Authorization` 头取出 bearer 令牌；格式不符返回 `""`。

    只接受 `Bearer`（大小写不敏感）。刻意**不**支持裸令牌或 `Basic`：宽松解析会让
    「把令牌当用户名密码塞进 URL」这类写法也能通过，正是要杜绝的方向。
    """
    if not header_value:
        return ""
    parts = header_value.strip().split(None, 1)
    if len(parts) != 2:
        return ""
    scheme, token = parts[0].lower(), parts[1].strip()
    if scheme != "bearer":
        return ""
    return token


def forbidden_token_in_query(query: dict[str, Any]) -> str:
    """查询串里是否出现凭据类键名 → 返回命中的键名（空串表示没有）。"""
    for key in query.keys():
        if str(key).lower() in _FORBIDDEN_QUERY_KEYS:
            return str(key)
    return ""


def build_authz(*, offline_mode: bool, project_id: str) -> tuple[Any, PrincipalResolver]:
    """装配 `(AuthzPolicy, PrincipalResolver)`（组合根单点调用）。

    * 生产：要求 `IB_AUTHZ_POLICY_MODULE` 指向一个模块，内含 `POLICY`（`AuthzPolicy` 实现）
      与 `resolve_principal(token) -> AuthzContext | None`。缺失即 `StartupError`。
    * 离线：`AllowAllPolicy` + `EnvTokenResolver(IB_OFFLINE_TOKEN)`。
      **离线也不跳过鉴权** —— 否则「401 路径」永远测不到，而它是安全相关路径。
    """
    module_path = os.environ.get("IB_AUTHZ_POLICY_MODULE", "").strip()
    if module_path:
        return _load_policy_module(module_path)
    if offline_mode:
        resolver = EnvTokenResolver(token_env="IB_OFFLINE_TOKEN", project_id=project_id)
        return AllowAllPolicy(), resolver
    raise StartupError(
        "未注入 AuthzPolicy：生产装配必须设置 IB_AUTHZ_POLICY_MODULE（内含 POLICY 与 "
        "resolve_principal）。缺口即启动失败，不允许带 DenyAllPolicy 静默启动（AC-IB-11-05）。"
    )


def _load_policy_module(module_path: str) -> tuple[Any, PrincipalResolver]:
    import importlib

    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # noqa: BLE001
        raise StartupError(
            f"IB_AUTHZ_POLICY_MODULE={module_path!r} 无法导入（{type(exc).__name__}）"
        ) from exc
    policy = getattr(module, "POLICY", None)
    if policy is None:
        raise StartupError(f"策略模块 {module_path!r} 缺少 POLICY（AuthzPolicy 实现）")
    resolver = getattr(module, "resolve_principal", None)
    if resolver is None:
        raise StartupError(
            f"策略模块 {module_path!r} 缺少 resolve_principal(token) -> AuthzContext | None"
        )
    return policy, resolver


# --------------------------------------------------------------------------- #
# 中间件（唯一鉴权发生地）
# --------------------------------------------------------------------------- #


class AuthMiddleware:
    """把 HTTP 请求翻成 `RequestContext`，并在此**唯一一处**决定 401/403。

    视图里再判一次权限是冗余的 —— 两份判断迟早会分叉；因此视图只从
    `request.ib_ctx` 取上下文，不重复推导身份。
    """

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response
        self._policy = None
        self._resolver: PrincipalResolver | None = None

    # --- Django middleware 协议 --- #

    def __call__(self, request: Any) -> Any:
        from django.http import JsonResponse

        # 0) 凭据不得出现在查询串（显式拒绝，见模块文档）
        hit = forbidden_token_in_query(dict(request.GET))
        if hit:
            return _problem(
                400,
                "token_in_query_forbidden",
                f"参数 {hit!r} 不得出现在查询串中：令牌只允许经 Authorization 头传递"
                "（查询串会被访问日志完整记录）。",
            )

        path = request.path or ""
        if path in PUBLIC_PATHS:
            request.__dict__[REQUEST_CTX_ATTR] = None
            return self.get_response(request)

        policy, resolver = self._deps()
        token = parse_bearer(request.META.get("HTTP_AUTHORIZATION", ""))
        if not token:
            return _problem(401, "unauthenticated", "缺少 Authorization: Bearer 令牌")
        authz = resolver.resolve(token)
        if authz is None:
            # 不区分「令牌不存在」与「令牌过期」：区分等于给攻击者一个探测预言机
            return _problem(401, "unauthenticated", "令牌无效或已过期")

        # project_id 只认服务端结论（module_design：不信请求体/查询串）
        claimed = (request.META.get("HTTP_X_IB_PROJECT") or "").strip()
        if claimed and claimed != authz.project_id:
            return _problem(
                403,
                "project_mismatch",
                "请求声明的项目与令牌所属项目不一致（project_id 只以令牌为准）",
            )

        session_id = _session_id_of(request)
        try:
            ctx = make_request_context(
                project_id=authz.project_id,
                actor_id=authz.actor_id,
                session_id=session_id,
                roles=tuple(authz.roles),
            )
        except ScopeViolationError as exc:
            return _problem(400, "invalid_session_id", str(exc))

        request.__dict__[REQUEST_CTX_ATTR] = ctx
        # 策略附在请求上供视图做动作级判定（can_manage / can_query）
        request.__dict__["ib_policy"] = policy
        return self.get_response(request)

    # --- 内部 --- #

    def _deps(self) -> tuple[Any, PrincipalResolver]:
        """从已装配的组合根取 `(policy, resolver)`（延迟取，保证中间件在装配前可被实例化）。"""
        if self._policy is None or self._resolver is None:
            from ibweb.composition import get_deps

            deps = get_deps()
            self._policy = deps.policy
            self._resolver = deps.principal_resolver
        return self._policy, self._resolver


def _session_id_of(request: Any) -> str:
    """取会话 id（查询串 `session_id`，或默认按 actor 归一）。

    只接受**标识符**而非凭据，故允许出现在查询串。缺省时归一为 `default`，
    使「不开多会话」的前端无需构造参数。
    """
    raw = (request.GET.get("session_id") or "").strip()
    if not raw:
        return "default"
    # 会话 id 会拼进 `project:actor:session` 键，含冒号会破坏前缀断言
    return raw.replace(":", "-")[:128]


def _problem(status: int, code: str, message: str) -> Any:
    """统一错误响应（**不回显任何请求内容**，只给机器码 + 可读中文）。"""
    from django.http import JsonResponse

    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def get_policy(request: Any) -> Any:
    """从请求取策略（视图用）。未鉴权路径返回 `DenyAllPolicy`（最保守）。"""
    return request.__dict__.get("ib_policy") or DenyAllPolicy()
