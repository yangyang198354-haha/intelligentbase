"""
@module MOD-IB-03
@implements IFC-IB-031 RequestContext / IFC-IB-032 can_manage / IFC-IB-033 can_query
            IFC-IB-034 DenyAllPolicy（默认拒绝；未注入即启动失败）
@depends MOD-IB-01
@author software-developer

请求上下文与鉴权端口（module_design.md §3 MOD-IB-03）。

本模块是 **FM-7（会话键碰撞）/ FM-2（写入侧错绑 scope）** 的一次性落点：
  * `session_key()` 是会话键构造的**唯一入口**（`{project_id}:{actor_id}:{session_id}`）；
  * `assert_session_key()` 是读取侧的**前缀断言**（不符即拒，fail-closed）；
  * `DenyAllPolicy` 是默认策略，`build_application` 在未注入真实策略时**拒绝启动**。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ib.core import AuthzContext, AuthzPolicy, RequestContext, ScopeViolationError

__all__ = [
    "AuthzContext",
    "RequestContext",
    "AuthzPolicy",
    "DenyAllPolicy",
    "AllowAllPolicy",
    "session_key",
    "assert_session_key",
    "new_request_id",
    "make_request_context",
    "actor_scope",
    "utc_now_iso",
    "parse_iso",
    "iso_plus_seconds",
]

#: 时间戳格式：UTC + 秒级精度 + `Z` 后缀。
#: 秒级精度是**刻意的**（见 `utc_now_iso` 说明）。
_ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_iso() -> str:
    """当前 UTC 时间戳（`2026-01-01T00:00:00Z`）。

    三点设计取舍（均与租约判定的正确性直接相关）：
      1. **秒级精度 + 定长**：`lease_expires_at` 的比较在 SQLite 里是**字符串比较**
         （见 `ib.ledger` 的条件 UPDATE），定长格式才能保证字典序 == 时间序；
      2. **UTC + `Z`**：避免本地时区写入、跨机比较错位；
      3. 不返回 `datetime`：字符串可直接进台账、日志与 lease 字段，减少转换点。
    """
    return datetime.now(timezone.utc).strftime(_ISO_FORMAT)


def parse_iso(value: str) -> datetime:
    """解析 `utc_now_iso()` 产出的时间戳；解析失败抛 `ValueError`（不静默取当前时间）。"""
    return datetime.strptime(value, _ISO_FORMAT).replace(tzinfo=timezone.utc)


def iso_plus_seconds(seconds: int) -> str:
    """`utc_now_iso()` + N 秒（租约到期时间）。负数即过去（用于构造已过期租约）。"""
    from datetime import timedelta

    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime(_ISO_FORMAT)


class DenyAllPolicy:
    """默认鉴权策略：**两者恒返回 False**（IFC-IB-034）。

    基座不带业务鉴权模型，故默认姿态是「拒绝一切」。组合根在**未注入**真实策略时
    直接 `StartupError`（AC-IB-11-05），而不是带着 `DenyAllPolicy` 启动 —— 后者会让
    所有请求静默 403，掩盖装配遗漏。
    """

    name = "deny_all"

    def can_manage(self, ctx: AuthzContext) -> bool:
        return False

    def can_query(self, ctx: AuthzContext) -> bool:
        return False


class AllowAllPolicy:
    """**仅供离线自测**：恒放行。

    显式命名并在装配期要求 `IB_OFFLINE_MODE=1` 才被接受（见 `ibweb.composition`），
    避免它被误当成「省事的默认值」带上生产。
    """

    name = "allow_all"

    def can_manage(self, ctx: AuthzContext) -> bool:
        return True

    def can_query(self, ctx: AuthzContext) -> bool:
        return True


# --------------------------------------------------------------------------- #
# 会话键（FM-7）
# --------------------------------------------------------------------------- #


def session_key(project_id: str, actor_id: str, session_id: str) -> str:
    """会话键构造的**唯一入口**：`f"{project_id}:{actor_id}:{session_id}"`。

    冒号是分隔符，故三段自身不得含冒号 —— 否则键会被错误还原（可伪造前缀）。
    """
    for label, value in (("project_id", project_id), ("actor_id", actor_id), ("session_id", session_id)):
        if not value:
            raise ScopeViolationError(f"会话键字段 {label} 不得为空")
        if ":" in value:
            raise ScopeViolationError(f"会话键字段 {label} 不得包含 ':'（会破坏前缀断言的可靠性）")
    return f"{project_id}:{actor_id}:{session_id}"


def assert_session_key(key: str, project_id: str) -> None:
    """读取前的最长前缀断言（FM-7：不符即拒，**fail-closed**）。"""
    prefix = f"{project_id}:"
    if not key.startswith(prefix):
        raise ScopeViolationError("会话键前缀与当前项目不符，已拒绝读取（FM-7）")


def actor_scope(project_id: str, roles: tuple[str, ...] = ()) -> AuthzContext:
    """构造鉴权主体（供 HTTP 中间件调用）。"""
    return AuthzContext(actor_id=f"actor:{project_id}", project_id=project_id, roles=roles)


# --------------------------------------------------------------------------- #
# 请求上下文
# --------------------------------------------------------------------------- #


def new_request_id() -> str:
    """生成请求 id（不透明，仅用于日志与线程 id 拼装）。"""
    return uuid.uuid4().hex


def make_request_context(
    *,
    project_id: str,
    actor_id: str,
    session_id: str,
    roles: tuple[str, ...] = (),
    request_id: str | None = None,
) -> RequestContext:
    """装配期构造 `RequestContext`（机械段）。

    `scope_token` 只是**不透明字符串**（日志/线程 id 拼装用），骨架不解释其语义；
    真正的知识库范围经工具闭包绑定，**不出现在此处**（ADR-09）。
    """
    key = session_key(project_id, actor_id, session_id)
    return RequestContext(
        request_id=request_id or new_request_id(),
        session_key=key,
        scope_token=f"{project_id}:{uuid.uuid4().hex[:8]}",
        authz=AuthzContext(actor_id=actor_id, project_id=project_id, roles=roles),
    )
