"""
@module MOD-IB-26
@implements IFC-IB-274（服务端配置键清单，键名与默认值）
            IFC-IB-267（维度三方一致性中的「服务端启动期交叉校验」一侧）
@depends —
@author sub_agent_software_developer

`ib-embed` 服务端配置（**仅** `IB_EMBED_*` 的 11 个键；见 docs/ib_embed_service_contract.md §9）。

三条纪律（不可协商）：

1. **只登记键名、不回显值**：任何报错只允许说「哪个键」，不得把值写进消息或日志
   （对齐 IFC-IB-263 / AC-IB-12-03，本模块与 MOD-IB-25 共用同一纪律）。
2. **不新增超时/重试键**：冷/热双路径的差异**全部在客户端**（IFC-IB-273 单一落点）。
   本服务**没有** `IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*` —— 加了就是把冷热纪律双落点化。
   本模块内部确有「单批推理预算」「排队等待上限」两个常量，但它们是**实现常量**（见
   `server.py` 的 `INFERENCE_BUDGET_S` / `QUEUE_WAIT_S`），不是配置面，不进入本文件的键清单。
3. **不引入凭据**：本服务不需要任何令牌；本模块**不认识**任何 `*TOKEN*` / `*KEY*` 键。

包外隔离：本包是**独立顶层包**，不被任何模块 import（C8 / 契约 §2）——
它只依赖标准库，且**不** import `ib.*`（服务端与业务基座之间只有线协议）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

__all__ = [
    "DEFAULT_KEYS",
    "ConfigError",
    "EmbedConfig",
    "REQUIRED_KEYS",
    "load_config",
]

#: 11 个键的默认值。`IB_EMBED_MODEL_PATH` **无默认**（离线加载必需，见契约 §9）。
DEFAULT_KEYS: dict[str, str | None] = {
    "IB_EMBED_HOST": "127.0.0.1",
    "IB_EMBED_PORT": "8100",
    "IB_EMBED_MODEL_ID": "bge-m3",
    "IB_EMBED_DIM": "1024",
    "IB_EMBED_MODEL_PATH": None,
    "IB_EMBED_MAX_BATCH": "64",
    "IB_EMBED_MAX_TOKENS": "8192",
    "IB_EMBED_MAX_CONCURRENCY": "1",
    "IB_EMBED_QUEUE_DEPTH": "8",
    "IB_EMBED_THREADS": "2",
    "IB_EMBED_MEMORY_LIMIT_MB": "2560",
}

#: 无默认、缺失即拒绝启动的键。`IB_EMBED_MODEL_PATH` 是唯一一个 —— 权重目录
#: 无法猜（契约 §9：离线加载必需，AC-IB-12-04 第 2 项）。
REQUIRED_KEYS: tuple[str, ...] = ("IB_EMBED_MODEL_PATH",)

_INT_KEYS: tuple[str, ...] = (
    "IB_EMBED_PORT",
    "IB_EMBED_DIM",
    "IB_EMBED_MAX_BATCH",
    "IB_EMBED_MAX_TOKENS",
    "IB_EMBED_MAX_CONCURRENCY",
    "IB_EMBED_QUEUE_DEPTH",
    "IB_EMBED_THREADS",
    "IB_EMBED_MEMORY_LIMIT_MB",
)


class ConfigError(RuntimeError):
    """配置非法或缺失。**消息只含键名**，绝不含值（IFC-IB-263 纪律）。"""


@dataclass(frozen=True, slots=True)
class EmbedConfig:
    """`ib-embed` 的不可变配置快照。"""

    host: str
    port: int
    model_id: str
    dim: int
    model_path: str
    max_batch: int
    max_tokens: int
    max_concurrency: int
    queue_depth: int
    threads: int
    memory_limit_mb: int

    def as_loggable(self) -> dict[str, object]:
        """启动日志用：**只含非敏感项**（无凭据；`model_path` 属本机路径，仅 DEBUG 才需要）。"""
        return {
            "host": self.host,
            "port": self.port,
            "model_id": self.model_id,
            "dim": self.dim,
            "max_batch": self.max_batch,
            "max_tokens": self.max_tokens,
            "max_concurrency": self.max_concurrency,
            "queue_depth": self.queue_depth,
            "threads": self.threads,
            "memory_limit_mb": self.memory_limit_mb,
        }


def _read(environ: Mapping[str, str], key: str) -> str | None:
    raw = environ.get(key)
    if raw is None:
        return None
    raw = raw.strip()
    return raw or None


def load_config(environ: Mapping[str, str] | None = None) -> EmbedConfig:
    """从环境变量装载配置。任何非法/缺失 → `ConfigError`（消息只含键名）。

    **只读 `IB_EMBED_*` 键**：不消费任何凭据类环境变量 —— 这是「无凭据面」的代码级保证。
    """
    env: Mapping[str, str] = os.environ if environ is None else environ

    resolved: dict[str, str] = {}
    for key, default in DEFAULT_KEYS.items():
        value = _read(env, key)
        if value is None:
            if default is None:
                raise ConfigError(f"缺少必填配置键：{key}")
            value = default
        resolved[key] = value

    numbers: dict[str, int] = {}
    for key in _INT_KEYS:
        raw = resolved[key]
        try:
            numbers[key] = int(raw)
        except ValueError as exc:  # 消息只含键名，不回显值
            raise ConfigError(f"配置键 {key} 不是合法整数") from exc

    if not (1 <= numbers["IB_EMBED_PORT"] <= 65535):
        raise ConfigError("配置键 IB_EMBED_PORT 越界")
    if numbers["IB_EMBED_DIM"] <= 0:
        raise ConfigError("配置键 IB_EMBED_DIM 必须为正")
    if numbers["IB_EMBED_MAX_BATCH"] <= 0:
        raise ConfigError("配置键 IB_EMBED_MAX_BATCH 必须为正")
    if numbers["IB_EMBED_MAX_TOKENS"] <= 0:
        raise ConfigError("配置键 IB_EMBED_MAX_TOKENS 必须为正")
    if numbers["IB_EMBED_MAX_CONCURRENCY"] <= 0:
        raise ConfigError("配置键 IB_EMBED_MAX_CONCURRENCY 必须为正（有界并发不许为 0）")
    if numbers["IB_EMBED_QUEUE_DEPTH"] < 0:
        raise ConfigError("配置键 IB_EMBED_QUEUE_DEPTH 不得为负")
    if numbers["IB_EMBED_THREADS"] <= 0:
        raise ConfigError("配置键 IB_EMBED_THREADS 必须为正")
    if numbers["IB_EMBED_MEMORY_LIMIT_MB"] <= 0:
        raise ConfigError("配置键 IB_EMBED_MEMORY_LIMIT_MB 必须为正")

    return EmbedConfig(
        host=resolved["IB_EMBED_HOST"],
        port=numbers["IB_EMBED_PORT"],
        model_id=resolved["IB_EMBED_MODEL_ID"],
        dim=numbers["IB_EMBED_DIM"],
        model_path=resolved["IB_EMBED_MODEL_PATH"],
        max_batch=numbers["IB_EMBED_MAX_BATCH"],
        max_tokens=numbers["IB_EMBED_MAX_TOKENS"],
        max_concurrency=numbers["IB_EMBED_MAX_CONCURRENCY"],
        queue_depth=numbers["IB_EMBED_QUEUE_DEPTH"],
        threads=numbers["IB_EMBED_THREADS"],
        memory_limit_mb=numbers["IB_EMBED_MEMORY_LIMIT_MB"],
    )
