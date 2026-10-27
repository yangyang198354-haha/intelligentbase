# MOD-R26-12：项目运行时快照编译 / 缓存 / 试运行（ADR-53 / ADR-54）
"""`ib.runtime`：把版本快照编译为不可变运行时配置，并在进程内缓存与原子切换。依赖 `ib.core/config/orchestration`，
不 import `ibweb`（所有外部对象经 `RuntimeDeps` 注入）。"""

from ib.runtime.cache import (
    ConfigVersionExpiredError,
    ProjectRuntimeCache,
    RuntimeLease,
    RuntimeState,
    RuntimeStatus,
)
from ib.runtime.compile import (
    DEFAULT_AGENT_MAX_STEPS,
    CompiledProjectConfig,
    ExemplarVectorCache,
    RuntimeDeps,
    compile_project_config,
)
from ib.runtime.trial import TrialBusyError, TrialLimits, TrialRunner, ValidationFailed

__all__ = [
    "ConfigVersionExpiredError",
    "ProjectRuntimeCache",
    "RuntimeLease",
    "RuntimeState",
    "RuntimeStatus",
    "DEFAULT_AGENT_MAX_STEPS",
    "CompiledProjectConfig",
    "ExemplarVectorCache",
    "RuntimeDeps",
    "compile_project_config",
    "TrialBusyError",
    "TrialLimits",
    "TrialRunner",
    "ValidationFailed",
]
