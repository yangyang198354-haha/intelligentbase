"""
@module MOD-IB-23
@implements IFC-IB-326 LoginThrottle + 账户认证审计事件（**条件性**，ADR-27 / OQ-IB-12 / OQ-IB-13）
@depends MOD-IB-04（结构化日志白名单）
@author software-developer

登录限速与认证审计（R13，**条件性**）。

## 为什么是「条件性」

`OQ-IB-12`（限速阈值 / 锁定窗口）与 `OQ-IB-13`（审计事件取值域）**未裁决**，故 ADR-27 明文
规定：**裁决前不纳入默认施工**。本模块因此只提供**可注入、可关闭**的实现：

  * 未设置 `IB_LOGIN_MAX_FAILURES` → 不启用限速（`build_throttle()` 返回 `None`）；
  * 账户级锁定由 `AccountStore.record_login_failure` 承载（阈值/窗口**注入**给存储），
    本模块负责的是 **`client_ip` 维度的滑动窗口**（防「挑用户名爆破」）；
  * 审计事件经 `ib.observability.log_event` 输出 —— **只记枚举与计数**，
    **不含口令、不含令牌、`username` 不作为自由文本字段**（防日志泄露，FM-8）。

## 为什么审计事件走日志而不是新表

ADR-27 / IFC-IB-326 明示落点为 MOD-IB-04 的结构化日志（**不新增表**）。这样审计面与
既有的「字段白名单 + 脱敏」纪律完全一致 —— 不需要为审计另建一条可能绕过白名单的通道。
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

__all__ = ["ThrottleDecision", "LoginThrottle", "build_throttle", "audit"]

#: 触发限速后返回给客户端的统一文案（**不区分**失败原因，防探测）。
_THROTTLE_MESSAGE = "登录尝试过于频繁，请稍后再试"


@dataclass(frozen=True, slots=True)
class ThrottleDecision:
    """限速判定结果。`allow=False` 时 `retry_after_seconds` 给出建议等待秒数。"""

    allow: bool
    retry_after_seconds: int = 0


class LoginThrottle:
    """按 `client_ip` 计的**固定窗口**登录限速（进程内）。

    仅覆盖「同一来源 IP 的连续失败」这一维度；账户维度由 `AccountStore` 的计数/锁定承载。
    进程内实现意味着多 worker 各自计数 —— 对单机单进程（Waitress）部署足够；
    跨进程共享需外部存储，属后续增量（不引入新依赖是本轮约束）。
    """

    def __init__(self, *, max_attempts: int, window_seconds: int) -> None:
        self._max_attempts = max(1, int(max_attempts))
        self._window = max(1, int(window_seconds))
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}

    def _prune(self, key: str, now_ts: float) -> list[float]:
        cutoff = now_ts - self._window
        recent = [t for t in self._hits.get(key, []) if t > cutoff]
        if recent:
            self._hits[key] = recent
        else:
            self._hits.pop(key, None)
        return recent

    def check(self, username: str, client_ip: str, *, now: str = "") -> ThrottleDecision:
        """是否可以继续尝试登录（`now` 仅作日志/兼容，本实现用单调时钟）。"""
        del username, now  # 不以 username 为键：避免「挑用户名爆破」分散计数（OQ-IB-13 待裁决）
        key = client_ip or "unknown"
        now_ts = time.monotonic()
        with self._lock:
            recent = self._prune(key, now_ts)
            if len(recent) >= self._max_attempts:
                oldest = min(recent)
                retry = max(1, int(self._window - (now_ts - oldest)) + 1)
                return ThrottleDecision(allow=False, retry_after_seconds=retry)
        return ThrottleDecision(allow=True)

    def record_failure(self, client_ip: str) -> None:
        key = client_ip or "unknown"
        now_ts = time.monotonic()
        with self._lock:
            self._prune(key, now_ts)
            self._hits.setdefault(key, []).append(now_ts)

    def record_success(self, client_ip: str) -> None:
        key = client_ip or "unknown"
        with self._lock:
            self._hits.pop(key, None)


def build_throttle() -> LoginThrottle | None:
    """按环境变量构造限速器；未配置 `IB_LOGIN_MAX_FAILURES` → `None`（不启用，ADR-27）。"""
    raw = os.environ.get("IB_LOGIN_MAX_FAILURES", "").strip()
    if not raw:
        return None
    try:
        max_attempts = int(raw)
    except ValueError:
        return None
    window = 0
    raw_window = os.environ.get("IB_LOGIN_LOCK_SECONDS", "").strip()
    if raw_window:
        try:
            window = int(raw_window)
        except ValueError:
            window = 0
    return LoginThrottle(max_attempts=max_attempts, window_seconds=window or 900)


def audit(event: str, *, outcome: str = "", status: str = "", project_id: str = "") -> None:
    """发出认证审计事件（IFC-IB-326）。

    **只允许枚举 / 计数 / 项目 id**：`username` / `user_id` / 口令 / 令牌一律不入参
    （函数签名本身就不接受它们 —— 想写进去也写不进）。

    落点经 `log_event(stage, outcome, **extra)`（IFC-IB-042）：第二位置参数**就是**
    `outcome`，故它只能出现在位置参数上；把它再放进 `**extra` 会 `TypeError`
    （多值），而这正是「审计事件写不出去」的静默故障源 —— 本函数因此只传
    `status` / `project_id` 两个白名单内的附加字段。
    """
    from ib.observability import log_event

    fields: dict[str, str] = {}
    if status:
        fields["status"] = status
    if project_id:
        fields["project_id"] = project_id
    log_event("auth", outcome or event, **fields)
