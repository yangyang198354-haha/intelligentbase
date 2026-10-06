"""
@module MOD-IB-01
@implements IFC-IB-012 (异常类型层次 IbError -> ConfigError / ScopeViolationError /
                       DependencyUnavailableError / ValidationError)
            IFC-IB-341 (REV-16-2) PromptNotFoundError / ToolParamValidationError
@depends (none)
@author software-developer

异常层次。**framework-free**：仅使用 stdlib。

设计原则：
  * 异常**只承载错误码与键名**，绝不承载正文、检索片段原文或凭据（FM-8 日志泄漏防护）。
  * `ScopeViolationError` 单独成类，因为它在 HTTP 层必须映射为 **403**（而非 404），
    以避免「存在性探测」。
"""

from __future__ import annotations


class IbError(Exception):
    """基座异常根类。所有自定义异常均可被单点捕获。"""

    code: str = "ib_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.code}] {self.message}"


class ConfigError(IbError):
    """配置缺失 / 非法。

    **只允许记录键名，不得回显值**（REQ-NFR-IB-07 / IFC-IB-023 / AC-IB-12-03）。
    """

    code = "config_error"

    def __init__(self, message: str, *, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


class ScopeViolationError(IbError):
    """`kb_id` 不属于给定 `project_id`，或 scope 越界。

    HTTP 映射：**403**（不得返回 404 —— 避免存在性探测，module_design §1.4）。
    """

    code = "scope_violation"


class DependencyUnavailableError(IbError):
    """外部依赖不可用 / 超时（embedding / vectorstore / llm / OCR / 渲染 / 可选库缺失）。

    检索层把它转成 `RetrievalResult(degraded=True, ...)`（fail-open，ADR-13）；
    台账 / BlobStore 则保留为 503（fail-closed）。
    """

    code = "dependency_unavailable"

    def __init__(self, message: str, *, dependency: str | None = None) -> None:
        super().__init__(message)
        self.dependency = dependency


class ValidationError(IbError):
    """上传校验失败（扩展名 / 大小 / 魔数签名）。HTTP 映射：400。"""

    code = "validation_error"

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class NotFoundError(IbError):
    """资源不存在。HTTP 映射：404。"""

    code = "not_found"


class ConflictError(IbError):
    """状态冲突（如对非 `failed` 文档执行重试）。HTTP 映射：409。"""

    code = "conflict"


class StartupError(IbError):
    """启动期必填校验失败（AC-IB-11-05 / AC-IB-12-03）。

    组合根在 `AuthzPolicy` 未注入时抛出此异常 —— **进程不得启动**（不得静默放行）。
    """

    code = "startup_error"


class PromptNotFoundError(IbError):
    """提示词不存在 / 兜底层为空（IFC-IB-341，REQ-FUNC-IB-37 / ADR-29）。

    HTTP 映射：**404**（单层不存在）或 **400**（`fallback` 层为空 —— 装配期校验拒绝）。
    **错误体只出可读原因，绝不回显提示词正文或任何凭据值。**
    """

    code = "prompt_not_found"


class ToolParamValidationError(IbError):
    """工具参数校验失败（IFC-IB-341 / IFC-IB-346，REQ-FUNC-IB-39 / ADR-30）。

    HTTP 映射：**400**（越界 / 类型不符 / 未知参数 / 未授权工具带参）。装配期则 **fail-fast**
    拒绝启动（复用 ADR-16 闸门）。**不提供**新增工具本体的路径。
    """

    code = "tool_param_validation"


__all__ = [
    "IbError",
    "ConfigError",
    "ScopeViolationError",
    "DependencyUnavailableError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "StartupError",
    "PromptNotFoundError",
    "ToolParamValidationError",
]
