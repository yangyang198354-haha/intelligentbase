"""
@module MOD-IB-02
@implements IFC-IB-021 ConfigurationSource.load / IFC-IB-022 resolve_project_config
            IFC-IB-023 validate_required（只报键名，不回显值）/ IFC-IB-024 GlobalConfig
            IFC-IB-288~292（R7 定义文档数据层）
            IFC-IB-343~348（REV-16-2 独立提示词目录数据层 / 工具参数校验 / 键名登记）
@depends MOD-IB-01
@author software-developer

配置装载与校验（module_design.md §3 MOD-IB-02）。

三条硬纪律：
  1. **凭据只走环境变量**（REQ-NFR-IB-07 / C-IB-02）。`GlobalConfig` 只登记**环境变量名**，
     永不持有密钥值；值的读取唯一入口是 `read_secret()`，且其返回值**不得**进入日志或响应。
  2. **配置键名不得新增 / 改名**（module_design §3 MOD-IB-23 R1 声明）。全部 `IB_*` 键在
     `IB_ENV_KEYS` 中登记，与 `deploy/env.example` 一一对应。
  3. **配置装载不依赖 Django settings 机制**（tech_stack §1），保持 `ConfigurationSource`
     端口的独立性 —— 便于离线单测与跨项目复用。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from ib.core import ConfigError, RawConfig

__all__ = [
    "IB_ENV_KEYS",
    "SUPPORTED_EXTS",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "RetrievalConfig",
    "ChunkingConfig",
    "LlmConfig",
    "AuthzConfig",
    "LoggingConfig",
    "BlobConfig",
    "WorkerConfig",
    "SessionConfig",
    "ProjectConfig",
    "GlobalConfig",
    "FileConfigurationSource",
    "DictConfigurationSource",
    "ConfigurationResolver",
    "read_secret",
    "validate_required",
    # R7 定义文档数据层（IFC-IB-288~292）
    "SUPPORTED_SCHEMA_VERSION",
    "DEFAULT_MAX_EXPERT_STEPS",
    "semantic_hash",
    "editable_field_whitelist",
    "non_editable_changes",
    "validate",
    "validate_definition_full",
    "derive",
    "build_definition_document",
    "document_to_json",
    "document_from_json",
    "content_hash_conflict_item",
    "FileDefinitionDocumentStore",
    "InMemoryDefinitionDocumentStore",
    "NON_EDITABLE_FIELDS",
    # REV-16-2 提示词域数据层（IFC-IB-343 ~ 348）
    "EXPERT_PROMPT_DIR_KEY",
    "EXPERT_PROMPT_ENABLED_KEY",
    "MAIN_FILENAME",
    "FALLBACK_FILENAME",
    "LAYER_FILENAMES",
    "prompt_domain_enabled",
    "prompt_content_hash",
    "merge_prompt_layers",
    "load_prompt_bundle",
    "load_prompt_directory",
    "validate_prompt_directory",
    "validate_tool_params",
    "derive_prompt_layers",
    "with_prompt_bundles",
    "FsExpertPromptStore",
    "InMemoryExpertPromptStore",
]

# --------------------------------------------------------------------------- #
# 键名登记（唯一真源；禁止在别处硬编码 IB_* 字符串）
# --------------------------------------------------------------------------- #

#: 装配开关（module_design.md §5；**不得新增 / 改名**）。
IB_ENV_KEYS: tuple[str, ...] = (
    "IB_VECTORSTORE_BACKEND",
    "IB_EMBED_BACKEND",
    "IB_LLM_BACKEND",
    "IB_OCR_ENABLED",
    "IB_RENDER_ENABLED",
    "IB_LEDGER_BACKEND",
    "IB_BLOB_STORE_ENABLED",
    "IB_SESSION_BACKEND",
    "IB_CONFIG_SOURCE",
    "IB_OFFLINE_MODE",
)

#: 非装配类环境变量（仅登记键名，值不入仓库）。
IB_RUNTIME_ENV_KEYS: tuple[str, ...] = (
    "IB_CONFIG_FILE",
    "IB_LEDGER_PATH",
    "IB_BLOB_ROOT",
    "IB_QDRANT_URL",
    "IB_EMBED_URL",
    "IB_EMBED_MODEL_ID",
    "IB_EMBED_DIM",
    # R2（L-03）：`inproc` 形态（IB_EMBED_BACKEND=inproc）所需的**本地权重目录**。
    # 该键名**早已登记**在服务端键清单（tech_stack.md §1.2 / ib_embed_service_contract.md §9），
    # 此处**只是把它登记进客户端集合**，语义与默认值均不变 —— **不新增、不改名任何键**。
    "IB_EMBED_MODEL_PATH",
    "IB_LLM_BASE_URL",
    "IB_LLM_MODEL",
    "IB_LLM_API_KEY",
    "IB_LOG_LEVEL",
    "IB_WORKER_LEASE_SECONDS",
    "IB_MAX_UPLOAD_MB",
    "IB_CHUNK_SIZE",
    "IB_CHUNK_OVERLAP",
    "IB_RETRIEVAL_TOP_K",
    "IB_RETRIEVAL_SCORE_THRESHOLD",
    # R7（IFC-IB-297）：定义文档路径与可视化开关。**只登记键名**（值不入仓库、不入响应体）。
    #   IB_DEFINITION_DOC_PATH —— 定义文档本地文件路径（[ARCH-ASSUMPTION-A6]：一项目一文件）
    #   IB_VISUAL_CONFIG_ENABLED —— 可视化配置页开关（前端据此决定是否渲染配置视图）
    "IB_DEFINITION_DOC_PATH",
    "IB_VISUAL_CONFIG_ENABLED",
    # R8（IFC-IB-304）：会话 / 确认中间态 / 思考分区的键名登记。**只登记键名**（值不入仓库、
    # 不入响应体）。三个键**全部有安全默认**，未声明不报错（与 IB_SESSION_PERSISTENCE_POLICY
    # 的「须显式声明」区别见下：后者的显式性由 §5 部署模板（IFC-IB-262）承担，见 MOD-IB-23）。
    #   IB_CONFIRMATION_GATE_ENABLED —— 确认中间态开关，**默认 false**（ADR-17 约束 1：默认关闭
    #                                 即零行为差异；OQ-IB-07 保持开放）。
    #   IB_SESSION_PERSISTENCE_POLICY —— 会话持久化策略，取值 `in_process`（默认）或 `external`。
    #   IB_REASONING_STREAM_ENABLED —— 思考分区流式开关，**默认 false**（AC-IB-19-03）。
    "IB_CONFIRMATION_GATE_ENABLED",
    "IB_SESSION_PERSISTENCE_POLICY",
    "IB_REASONING_STREAM_ENABLED",
    # R13（IFC-IB-312）：账户 / 会话 / 令牌的键名登记。**只登记键名，不含任何值**；
    # 本条**不进入 `IB_ENV_KEYS`**（那是 MOD-IB-01 的核心装配开关集合，声明「不得新增 / 改名」），
    # 账户后端的选择由 MOD-IB-23 组合根在装配期读取（`ib/ledger/accounts.py::build_account_store`）。
    #   IB_ACCOUNT_BACKEND —— 账户存储后端，取值 `sqlite`（默认）或 `memory`（离线 / 测试替身）。
    #   IB_SESSION_TTL_SECONDS —— 会话有效期（秒）。**默认值 TBD**（[ARCH-ASSUMPTION-A9] / OQ-IB-09 /
    #                            [TBD-T22]）；实现取保守默认（见 ibweb/accounts/__init__.py），非安全开关。
    #   IB_SESSION_RENEW_WINDOW_SECONDS —— 续期窗口（剩余有效期低于该值才允许 `renew`），
    #                                     使会话**不能**被无限续期（每次续期只补足窗口，不延长绝对寿命）。
    #   IB_DEFAULT_ADMIN_USERNAME —— 默认管理员用户名（**默认 `admin`；用户名非机密**，可入文档）。
    #   IB_DEFAULT_ADMIN_PASSWORD —— 默认管理员**初始口令**：**值只允许经 0600 `EnvironmentFile` 注入**；
    #                               **代码 / 文档 / 日志 / 响应中不得出现其字面量**（C-IB-09 / REQ-NFR-IB-15）。
    #   IB_PASSWORD_MIN_LENGTH —— 口令最小长度（**策略细节 TBD**；OQ-IB-11）。
    #   IB_LOGIN_MAX_FAILURES / IB_LOGIN_LOCK_SECONDS —— 登录失败阈值与锁定窗口（**条件性**：
    #                               OQ-IB-12 未裁决前不启用；ADR-27；未设置即不限速）。
    #   IB_AUTHZ_POLICY_MODULE —— **既有键，语义与默认不变**；其**可取值**新增内置账户模块路径
    #                               `ibweb.accounts.policy`（沿用 R2「仅扩展值域；键名与默认值不变」先例）。
    "IB_ACCOUNT_BACKEND",
    "IB_SESSION_TTL_SECONDS",
    "IB_SESSION_RENEW_WINDOW_SECONDS",
    "IB_DEFAULT_ADMIN_USERNAME",
    "IB_DEFAULT_ADMIN_PASSWORD",
    "IB_PASSWORD_MIN_LENGTH",
    "IB_LOGIN_MAX_FAILURES",
    "IB_LOGIN_LOCK_SECONDS",
    "IB_AUTHZ_POLICY_MODULE",
    # REV-16-2（IFC-IB-348）：独立提示词目录的键名登记。**只登记键名，不含任何值**
    #（路径值不入仓库、不入文档、不入日志）。
    #   IB_EXPERT_PROMPT_DIR —— 独立提示词目录根路径（<root>/<project_id>/<expert_name>/）。
    #   IB_EXPERT_PROMPT_ENABLED —— 提示词域开关，**默认 true**（REQ-FUNC-IB-37/41 属 v1 范围）。
    "IB_EXPERT_PROMPT_DIR",
    "IB_EXPERT_PROMPT_ENABLED",
)

#: v1 支持的 4 种格式（**OQ-IB-02 默认值**：其余格式按扩展点预留，不实现）。
SUPPORTED_EXTS: tuple[str, ...] = ("pdf", "docx", "md", "txt")

#: 必须存在凭据类环境变量的后端（校验时**只报键名**）。
_CREDENTIAL_KEYS_BY_BACKEND: Mapping[str, str] = {
    "openai_compatible": "IB_LLM_API_KEY",
    "http": "IB_EMBED_URL",  # 非凭据，但为真实后端的必填端点
}

_TRUEY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def _as_bool(raw: Any, *, default: bool, key: str) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in _TRUEY:
        return True
    if text in _FALSY:
        return False
    raise ConfigError(f"配置键 {key} 不是合法布尔值", key=key)


def _as_int(raw: Any, *, default: int, key: str) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"配置键 {key} 不是合法整数", key=key) from exc


def _as_float(raw: Any, *, default: float, key: str) -> float:
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"配置键 {key} 不是合法数值", key=key) from exc


# --------------------------------------------------------------------------- #
# 子配置（IFC-IB-024）
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EmbeddingConfig:
    """embedding 配置。冷 / 热双路径超时与重试分离（AC-IB-07-03 / ADR-02）。"""

    backend: str = "http"  # IB_EMBED_BACKEND
    url: str = "http://127.0.0.1:8100"  # IB_EMBED_URL
    model_id: str = "bge-m3"  # IB_EMBED_MODEL_ID
    dim: int = 1024  # IB_EMBED_DIM（bge-m3 稠密维度）
    cold_timeout_s: float = 120.0  # 冷路径：入库可慢
    cold_max_retries: int = 3
    cold_batch_size: int = 16
    hot_timeout_s: float = 3.0  # 热路径：超时即降级（fail-open）
    hot_max_retries: int = 1


@dataclass(frozen=True)
class VectorStoreConfig:
    """向量库配置。`api_key_env` 只记**环境变量名**。"""

    backend: str = "qdrant"  # IB_VECTORSTORE_BACKEND
    url: str = "http://127.0.0.1:6333"  # IB_QDRANT_URL（REST：健康与回退）
    grpc_port: int = 6334  # 主通道
    on_disk_vectors: bool = False
    hnsw_m: int = 16
    hnsw_ef_construct: int = 128
    hnsw_ef_search: int = 64
    rest_fallback: bool = True


@dataclass(frozen=True)
class RetrievalConfig:
    """检索配置（OQ-IB-06：**不硬编码效果阈值**，全部可配 + 可观测）。"""

    top_k: int = 5
    score_threshold: float = 0.35  # 余弦口径；须由 [TBD-T12] 在目标机校准
    candidate_multiplier: int = 4  # 取回候选数 = top_k * multiplier，用于 candidate_count


@dataclass(frozen=True)
class ChunkingConfig:
    """切分配置。参数变更**不自动**作用于既有文档（AC-IB-05-03）。"""

    chunk_size: int = 800
    chunk_overlap: int = 120
    normalizer_version: str = "v1"


@dataclass(frozen=True)
class LlmConfig:
    """LLM 配置。凭据仅经 `api_key_env` 指向的环境变量获取。"""

    backend: str = "openai_compatible"  # IB_LLM_BACKEND
    base_url: str = "https://api.deepseek.com/v1"  # IB_LLM_BASE_URL
    model: str = "deepseek-chat"  # IB_LLM_MODEL
    api_key_env: str = "IB_LLM_API_KEY"  # 只登记键名
    router_temperature: float = 0.0  # 路由必须确定性（AC-IB-09-07）
    expert_temperature: float = 0.3
    aggregator_temperature: float = 0.3
    request_timeout_s: float = 60.0


@dataclass(frozen=True)
class AuthzConfig:
    """鉴权配置。基座**不内置**业务鉴权模型 —— 策略由接入方注入（ADR-11 / NFR-09）。"""

    policy: str = "injected"  # `deny_all` 仅用于显式离线装配
    require_injected_policy: bool = True  # 未注入即启动失败（AC-IB-11-05）


@dataclass(frozen=True)
class LoggingConfig:
    """日志配置。字段白名单 + 脱敏（FM-8）。"""

    level: str = "INFO"  # IB_LOG_LEVEL
    json_lines: bool = True


@dataclass(frozen=True)
class BlobConfig:
    """原文件存储配置（OQ-IB-01 已确认 ON）。"""

    enabled: bool = True  # IB_BLOB_STORE_ENABLED
    root: str = "./var/blobs"  # IB_BLOB_ROOT


@dataclass(frozen=True)
class WorkerConfig:
    """入库 worker 配置（ADR-10 租约）。"""

    lease_seconds: int = 300  # IB_WORKER_LEASE_SECONDS
    batch_limit: int = 8
    poll_interval_s: float = 2.0
    max_retries: int = 3  # 重试上限；超限进 failed（不允许无限自动重试）


@dataclass(frozen=True)
class SessionConfig:
    """会话配置（OQ-IB-08：会话内隔离、不跨会话注入、长度上限可配）。"""

    backend: str = "memory"  # IB_SESSION_BACKEND
    #: R8（IFC-IB-304 / IFC-IB-299）：会话持久化策略，取值 `in_process`（默认）或 `external`。
    #: 该键**须显式声明**（AC-IB-20-02），声明载体是 `ib-web` 单元的 EnvironmentFile 模板
    #: （IFC-IB-262）；未声明时取安全默认 `in_process`（进程内，重启即失忆 —— 这本身是
    #: 安全失败方向，与 `SessionStateLossOutcome` 的唯一取值一致）。
    persistence_policy: str = "in_process"  # IB_SESSION_PERSISTENCE_POLICY
    max_history_messages: int = 20
    sticky_turns: int = 1


@dataclass(frozen=True)
class ProjectConfig:
    """项目级配置（IFC-IB-022）。**新项目接入只需新增一条此记录，核心代码零改动**（REQ-FUNC-IB-01）。"""

    project_id: str
    name: str
    active_collection_version: str
    embedding_model_id: str
    dim: int
    kb_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GlobalConfig:
    """全局配置（IFC-IB-024）。装配开关的取值域与默认值见 module_design §5。"""

    config_source: str = "file"  # IB_CONFIG_SOURCE
    offline_mode: bool = False  # IB_OFFLINE_MODE
    ledger_backend: str = "sqlite"  # IB_LEDGER_BACKEND
    ledger_path: str = "./var/ledger/ledger.sqlite3"  # IB_LEDGER_PATH
    max_upload_mb: int = 50  # IB_MAX_UPLOAD_MB
    allowed_exts: tuple[str, ...] = SUPPORTED_EXTS
    ocr_enabled: bool = True  # IB_OCR_ENABLED
    render_enabled: bool = True  # IB_RENDER_ENABLED
    #: R8（IFC-IB-304）：确认中间态开关。**默认 False** —— 默认关闭即零行为差异
    #: （ADR-17 约束 1）。为 True 时若组合根未注入确认话术构造器，仍不触发确认门
    #: （骨架不生成业务话术，见 MOD-IB-22 / IFC-IB-301）。
    confirmation_gate_enabled: bool = False  # IB_CONFIRMATION_GATE_ENABLED
    #: R8（IFC-IB-304）：思考分区流式开关。**默认 False**（AC-IB-19-03：默认不渲染）。
    reasoning_stream_enabled: bool = False  # IB_REASONING_STREAM_ENABLED
    collection_schema_version: int = 1
    payload_schema_version: int = 1
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vectorstore: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    authz: AuthzConfig = field(default_factory=AuthzConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    blob: BlobConfig = field(default_factory=BlobConfig)
    worker: WorkerConfig = field(default_factory=WorkerConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    projects: Mapping[str, ProjectConfig] = field(default_factory=dict)

    @property
    def chunking_spec(self) -> Any:
        """便利属性：转成契约层 `ChunkingSpec`（避免调用方重复拼装）。"""
        from ib.core import ChunkingSpec

        return ChunkingSpec(
            chunk_size=self.chunking.chunk_size,
            chunk_overlap=self.chunking.chunk_overlap,
            normalizer_version=self.chunking.normalizer_version,
        )


# --------------------------------------------------------------------------- #
# 凭据读取（唯一入口；值永不入配置对象 / 日志 / 响应）
# --------------------------------------------------------------------------- #


def read_secret(env_name: str, *, env: Mapping[str, str] | None = None) -> str | None:
    """从环境变量读取凭据。

    **这是全仓读取密钥的唯一入口。** 返回值只允许传给适配器构造参数，
    禁止写日志、禁止进 HTTP 响应、禁止进异常消息。
    """
    source = os.environ if env is None else env
    value = source.get(env_name)
    if value is None or value == "":
        return None
    return value


# --------------------------------------------------------------------------- #
# 配置源（IFC-IB-021）
# --------------------------------------------------------------------------- #


def _flatten(values: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """把嵌套映射拍平为 `a.b.c` 形式，便于键级覆盖合并。"""
    flat: dict[str, Any] = {}
    for key, value in values.items():
        path = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(_flatten(value, prefix=f"{path}."))
        else:
            flat[path] = value
    return flat


def _unflatten(flat: Mapping[str, Any]) -> dict[str, Any]:
    """`a.b.c` -> 嵌套 dict。"""
    root: MutableMapping[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(".")
        cursor: MutableMapping[str, Any] = root
        for part in parts[:-1]:
            nxt = cursor.get(part)
            if not isinstance(nxt, MutableMapping):
                nxt = {}
                cursor[part] = nxt
            cursor = nxt
        cursor[parts[-1]] = value
    return dict(root)


class FileConfigurationSource:
    """文件 + 环境变量合并（IFC-IB-021 的生产实现）。

    合并优先级（后者覆盖前者）：**文件默认值 < 配置文件内容 < 环境变量**。
    YAML 支持为**可选**（PyYAML 缺失时该文件类型报 `ConfigError`，JSON 不受影响）。
    """

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._env = os.environ if env is None else env
        configured = path if path is not None else self._env.get("IB_CONFIG_FILE")
        self._path = Path(configured) if configured else None

    def _load_file(self) -> dict[str, Any]:
        if self._path is None:
            return {}
        if not self._path.exists():
            # 配置文件不存在不是致命错误（可全量由环境变量驱动），但须可见。
            return {}
        text = self._path.read_text(encoding="utf-8")
        suffix = self._path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            try:
                import yaml  # 延迟导入：YAML 为可选依赖
            except ImportError as exc:  # pragma: no cover - 取决于环境
                raise ConfigError(
                    "解析 YAML 配置需要 PyYAML（可改用 .json 配置文件）",
                    key="IB_CONFIG_FILE",
                ) from exc
            loaded = yaml.safe_load(text) or {}
        else:
            loaded = json.loads(text) if text.strip() else {}
        if not isinstance(loaded, Mapping):
            raise ConfigError("配置文件根节点必须是映射（dict）", key="IB_CONFIG_FILE")
        return dict(loaded)

    def _env_overrides(self) -> dict[str, Any]:
        """环境变量覆盖。`IB_MAX_UPLOAD_MB` -> `max_upload_mb`（去掉前缀并小写）。"""
        out: dict[str, Any] = {}
        for key in IB_ENV_KEYS + IB_RUNTIME_ENV_KEYS:
            value = self._env.get(key)
            if value is None or value == "":
                continue
            out[key[len("IB_") :].lower()] = value
        return out

    def load(self) -> RawConfig:
        """合并三层（默认值由 `GlobalConfig` 提供，故此处只合文件 + 环境变量）。"""
        merged = _flatten(self._load_file())
        merged.update(_flatten(self._env_overrides()))
        source = str(self._path) if self._path else "env_only"
        return RawConfig(values=_unflatten(merged), source=source)


class DictConfigurationSource:
    """固定字典配置源（IFC-IB-021 的测试/离线实现；`IB_CONFIG_SOURCE=dict`）。"""

    def __init__(self, values: Mapping[str, Any], *, source: str = "dict") -> None:
        self._values = dict(values)
        self._source = source

    def load(self) -> RawConfig:
        return RawConfig(values=dict(self._values), source=self._source)


# --------------------------------------------------------------------------- #
# 解析：RawConfig -> GlobalConfig / ProjectConfig（IFC-IB-022）
# --------------------------------------------------------------------------- #


def _section(raw: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = raw.get(name)
    return value if isinstance(value, Mapping) else {}


def resolve_global_config(raw: RawConfig) -> GlobalConfig:
    """把 `RawConfig` 解析为 `GlobalConfig`（缺失项取默认值；类型非法抛 `ConfigError`）。"""
    values: Mapping[str, Any] = raw.values

    emb = _section(values, "embedding")
    vec = _section(values, "vectorstore")
    ret = _section(values, "retrieval")
    chk = _section(values, "chunking")
    llm = _section(values, "llm")
    az = _section(values, "authz")
    log = _section(values, "logging")
    blob = _section(values, "blob")
    worker = _section(values, "worker")
    session = _section(values, "session")

    embedding = EmbeddingConfig(
        backend=str(emb.get("backend", EmbeddingConfig.backend)),
        url=str(emb.get("url", EmbeddingConfig.url)),
        model_id=str(emb.get("model_id", EmbeddingConfig.model_id)),
        dim=_as_int(emb.get("dim"), default=EmbeddingConfig.dim, key="IB_EMBED_DIM"),
        cold_timeout_s=_as_float(
            emb.get("cold_timeout_s"), default=EmbeddingConfig.cold_timeout_s, key="embedding.cold_timeout_s"
        ),
        cold_max_retries=_as_int(
            emb.get("cold_max_retries"), default=EmbeddingConfig.cold_max_retries, key="embedding.cold_max_retries"
        ),
        cold_batch_size=_as_int(
            emb.get("cold_batch_size"), default=EmbeddingConfig.cold_batch_size, key="embedding.cold_batch_size"
        ),
        hot_timeout_s=_as_float(
            emb.get("hot_timeout_s"), default=EmbeddingConfig.hot_timeout_s, key="embedding.hot_timeout_s"
        ),
        hot_max_retries=_as_int(
            emb.get("hot_max_retries"), default=EmbeddingConfig.hot_max_retries, key="embedding.hot_max_retries"
        ),
    )
    vectorstore = VectorStoreConfig(
        backend=str(vec.get("backend", VectorStoreConfig.backend)),
        url=str(vec.get("url", VectorStoreConfig.url)),
        grpc_port=_as_int(vec.get("grpc_port"), default=VectorStoreConfig.grpc_port, key="vectorstore.grpc_port"),
        on_disk_vectors=_as_bool(
            vec.get("on_disk_vectors"), default=VectorStoreConfig.on_disk_vectors, key="vectorstore.on_disk_vectors"
        ),
        hnsw_m=_as_int(vec.get("hnsw_m"), default=VectorStoreConfig.hnsw_m, key="vectorstore.hnsw_m"),
        hnsw_ef_construct=_as_int(
            vec.get("hnsw_ef_construct"), default=VectorStoreConfig.hnsw_ef_construct, key="vectorstore.hnsw_ef_construct"
        ),
        hnsw_ef_search=_as_int(
            vec.get("hnsw_ef_search"), default=VectorStoreConfig.hnsw_ef_search, key="vectorstore.hnsw_ef_search"
        ),
    )
    retrieval = RetrievalConfig(
        top_k=_as_int(ret.get("top_k"), default=RetrievalConfig.top_k, key="IB_RETRIEVAL_TOP_K"),
        score_threshold=_as_float(
            ret.get("score_threshold"),
            default=RetrievalConfig.score_threshold,
            key="IB_RETRIEVAL_SCORE_THRESHOLD",
        ),
        candidate_multiplier=_as_int(
            ret.get("candidate_multiplier"),
            default=RetrievalConfig.candidate_multiplier,
            key="retrieval.candidate_multiplier",
        ),
    )
    chunking = ChunkingConfig(
        chunk_size=_as_int(chk.get("chunk_size"), default=ChunkingConfig.chunk_size, key="IB_CHUNK_SIZE"),
        chunk_overlap=_as_int(
            chk.get("chunk_overlap"), default=ChunkingConfig.chunk_overlap, key="IB_CHUNK_OVERLAP"
        ),
        normalizer_version=str(chk.get("normalizer_version", ChunkingConfig.normalizer_version)),
    )
    if chunking.chunk_overlap >= chunking.chunk_size:
        raise ConfigError(
            "IB_CHUNK_OVERLAP 必须小于 IB_CHUNK_SIZE（否则滑窗不前进）",
            key="IB_CHUNK_OVERLAP",
        )
    llm_cfg = LlmConfig(
        backend=str(llm.get("backend", LlmConfig.backend)),
        base_url=str(llm.get("base_url", LlmConfig.base_url)),
        model=str(llm.get("model", LlmConfig.model)),
        api_key_env=str(llm.get("api_key_env", LlmConfig.api_key_env)),
        router_temperature=_as_float(
            llm.get("router_temperature"), default=LlmConfig.router_temperature, key="llm.router_temperature"
        ),
        expert_temperature=_as_float(
            llm.get("expert_temperature"), default=LlmConfig.expert_temperature, key="llm.expert_temperature"
        ),
        aggregator_temperature=_as_float(
            llm.get("aggregator_temperature"), default=LlmConfig.aggregator_temperature, key="llm.aggregator_temperature"
        ),
        request_timeout_s=_as_float(
            llm.get("request_timeout_s"), default=LlmConfig.request_timeout_s, key="llm.request_timeout_s"
        ),
    )
    if llm_cfg.router_temperature != 0.0:
        # 路由必须确定性（AC-IB-09-07）；此处不静默纠正，而是显式拒绝非法配置。
        raise ConfigError("路由 temperature 必须为 0（AC-IB-09-07）", key="llm.router_temperature")

    authz = AuthzConfig(
        policy=str(az.get("policy", AuthzConfig.policy)),
        require_injected_policy=_as_bool(
            az.get("require_injected_policy"),
            default=AuthzConfig.require_injected_policy,
            key="authz.require_injected_policy",
        ),
    )
    logging_cfg = LoggingConfig(
        level=str(log.get("level", values.get("log_level", LoggingConfig.level))).upper(),
        json_lines=_as_bool(log.get("json_lines"), default=LoggingConfig.json_lines, key="logging.json_lines"),
    )
    blob_cfg = BlobConfig(
        enabled=_as_bool(blob.get("enabled", values.get("blob_store_enabled")), default=BlobConfig.enabled, key="IB_BLOB_STORE_ENABLED"),
        root=str(blob.get("root", values.get("blob_root", BlobConfig.root))),
    )
    worker_cfg = WorkerConfig(
        lease_seconds=_as_int(
            worker.get("lease_seconds", values.get("worker_lease_seconds")),
            default=WorkerConfig.lease_seconds,
            key="IB_WORKER_LEASE_SECONDS",
        ),
        batch_limit=_as_int(worker.get("batch_limit"), default=WorkerConfig.batch_limit, key="worker.batch_limit"),
        poll_interval_s=_as_float(
            worker.get("poll_interval_s"), default=WorkerConfig.poll_interval_s, key="worker.poll_interval_s"
        ),
        max_retries=_as_int(worker.get("max_retries"), default=WorkerConfig.max_retries, key="worker.max_retries"),
    )
    session_cfg = SessionConfig(
        backend=str(session.get("backend", values.get("session_backend", SessionConfig.backend))),
        persistence_policy=str(
            session.get(
                "persistence_policy",
                values.get("session_persistence_policy", SessionConfig.persistence_policy),
            )
        ),
        max_history_messages=_as_int(
            session.get("max_history_messages"),
            default=SessionConfig.max_history_messages,
            key="session.max_history_messages",
        ),
        sticky_turns=_as_int(
            session.get("sticky_turns"), default=SessionConfig.sticky_turns, key="session.sticky_turns"
        ),
    )

    # 项目级配置：`projects: {<project_id>: {...}}`
    raw_projects = values.get("projects")
    projects: dict[str, ProjectConfig] = {}
    if isinstance(raw_projects, Mapping):
        for pid, payload in raw_projects.items():
            if not isinstance(payload, Mapping):
                raise ConfigError("projects 下每项必须是映射", key="projects")
            projects[str(pid)] = ProjectConfig(
                project_id=str(pid),
                name=str(payload.get("name", pid)),
                active_collection_version=str(payload.get("active_collection_version", "1")),
                embedding_model_id=str(payload.get("embedding_model_id", embedding.model_id)),
                dim=_as_int(payload.get("dim"), default=embedding.dim, key=f"projects.{pid}.dim"),
                kb_ids=tuple(str(k) for k in payload.get("kb_ids", ()) or ()),
            )

    allowed = values.get("allowed_exts")
    allowed_exts = (
        tuple(str(e).lower().lstrip(".") for e in allowed)
        if isinstance(allowed, (list, tuple)) and allowed
        else SUPPORTED_EXTS
    )

    return GlobalConfig(
        config_source=str(values.get("config_source", GlobalConfig.config_source)),
        offline_mode=_as_bool(values.get("offline_mode"), default=False, key="IB_OFFLINE_MODE"),
        ledger_backend=str(values.get("ledger_backend", GlobalConfig.ledger_backend)),
        ledger_path=str(values.get("ledger_path", GlobalConfig.ledger_path)),
        max_upload_mb=_as_int(values.get("max_upload_mb"), default=GlobalConfig.max_upload_mb, key="IB_MAX_UPLOAD_MB"),
        allowed_exts=allowed_exts,
        ocr_enabled=_as_bool(values.get("ocr_enabled"), default=True, key="IB_OCR_ENABLED"),
        render_enabled=_as_bool(values.get("render_enabled"), default=True, key="IB_RENDER_ENABLED"),
        confirmation_gate_enabled=_as_bool(
            values.get("confirmation_gate_enabled"),
            default=GlobalConfig.confirmation_gate_enabled,
            key="IB_CONFIRMATION_GATE_ENABLED",
        ),
        reasoning_stream_enabled=_as_bool(
            values.get("reasoning_stream_enabled"),
            default=GlobalConfig.reasoning_stream_enabled,
            key="IB_REASONING_STREAM_ENABLED",
        ),
        collection_schema_version=_as_int(
            values.get("collection_schema_version"),
            default=GlobalConfig.collection_schema_version,
            key="collection_schema_version",
        ),
        payload_schema_version=_as_int(
            values.get("payload_schema_version"),
            default=GlobalConfig.payload_schema_version,
            key="payload_schema_version",
        ),
        embedding=replace(embedding),
        vectorstore=replace(vectorstore),
        retrieval=replace(retrieval),
        chunking=replace(chunking),
        llm=replace(llm_cfg),
        authz=replace(authz),
        logging=replace(logging_cfg),
        blob=replace(blob_cfg),
        worker=replace(worker_cfg),
        session=replace(session_cfg),
        projects=projects,
    )


def resolve_project_config(cfg: GlobalConfig, project_id: str) -> ProjectConfig:
    """取项目级配置（IFC-IB-022）。

    未登记的项目**显式报错**而不回退到全局默认 —— 否则「新项目忘了配」会静默落到
    某个共享 collection 上，正是 FM-5 要防的失败模式。
    """
    try:
        return cfg.projects[project_id]
    except KeyError as exc:
        raise ConfigError(
            f"未登记的项目配置：projects.{project_id} 缺失（不得回退到全局默认）",
            key=f"projects.{project_id}",
        ) from exc


# --------------------------------------------------------------------------- #
# 校验（IFC-IB-023）—— **只报键名，不回显值**
# --------------------------------------------------------------------------- #


def validate_required(
    cfg: GlobalConfig, *, env: Mapping[str, str] | None = None
) -> list[ConfigError]:
    """启动期必填校验（IFC-IB-023 / AC-IB-12-03）。

    返回 `list[ConfigError]`（空列表 = 通过）。**每个错误只含键名，不含值**，
    故可直接打印到启动日志而不泄露凭据。
    """
    errors: list[ConfigError] = []
    source = os.environ if env is None else env

    if cfg.offline_mode:
        # 离线模式下不要求任何真实后端凭据（全部走替身）。
        return errors

    # 1) 真实后端所需的凭据/端点（按后端条件判定）
    needed: list[tuple[str, str]] = []
    if cfg.llm.backend == "openai_compatible":
        needed.append(("IB_LLM_API_KEY", cfg.llm.api_key_env))
    if cfg.embedding.backend == "http":
        needed.append(("IB_EMBED_URL", "IB_EMBED_URL"))
    if cfg.embedding.backend == "inproc":
        # R2（IFC-IB-274 / IFC-IB-275）：进程内形态直接载本地权重，不经 HTTP。
        # 键名复用服务端已有登记的 `IB_EMBED_MODEL_PATH`（本地权重目录），非新增键。
        needed.append(("IB_EMBED_MODEL_PATH", "IB_EMBED_MODEL_PATH"))
    if cfg.vectorstore.backend == "qdrant":
        needed.append(("IB_QDRANT_URL", "IB_QDRANT_URL"))

    for label, env_key in needed:
        if read_secret(env_key, env=source) is None:
            errors.append(
                ConfigError(f"启动校验失败：缺少必填环境变量 {label}", key=label)
            )

    # 2) 装配开关的取值域
    choices = {
        "IB_VECTORSTORE_BACKEND": (cfg.vectorstore.backend, {"qdrant", "memory"}),
        # R2（IFC-IB-274）：值域由 {http, fake} **扩展为** {http, inproc, fake}。
        # 键名与默认值 `http` **不变**；上层模块、IFC 签名亦不改（形态可逆）。
        "IB_EMBED_BACKEND": (cfg.embedding.backend, {"http", "inproc", "fake"}),
        "IB_LLM_BACKEND": (cfg.llm.backend, {"openai_compatible", "fake"}),
        "IB_LEDGER_BACKEND": (cfg.ledger_backend, {"sqlite", "memory"}),
        # R8（IFC-IB-304）：`IB_SESSION_BACKEND` 的**值域扩展**为 {memory, external}；
        # 键名与默认值（`memory`）**不变**（沿用 R2 对 `IB_EMBED_BACKEND` 的「仅扩展值域」先例）。
        "IB_SESSION_BACKEND": (cfg.session.backend, {"memory", "external"}),
        # R8（IFC-IB-304 / IFC-IB-299）：会话持久化策略值域（in_process 默认 / external）。
        "IB_SESSION_PERSISTENCE_POLICY": (
            cfg.session.persistence_policy,
            {"in_process", "external"},
        ),
        "IB_CONFIG_SOURCE": (cfg.config_source, {"file", "dict"}),
    }
    for key, (value, allowed) in choices.items():
        if value not in allowed:
            errors.append(
                ConfigError(f"配置键 {key} 取值非法（允许：{'/'.join(sorted(allowed))}）", key=key)
            )

    # 3) 维度与模型一致性
    if cfg.embedding.dim <= 0:
        errors.append(ConfigError("嵌入维度必须为正整数", key="IB_EMBED_DIM"))

    # 4) 台账路径与 blob 根非空
    if not cfg.ledger_path:
        errors.append(ConfigError("台账路径不得为空", key="IB_LEDGER_PATH"))
    if cfg.blob.enabled and not cfg.blob.root:
        errors.append(ConfigError("Blob 根目录不得为空", key="IB_BLOB_ROOT"))

    return errors


class ConfigurationResolver:
    """装载 + 解析 + 校验的组合封装，供组合根单点使用。"""

    def __init__(self, source: Any) -> None:
        self._source = source
        self._raw: RawConfig | None = None
        self._cfg: GlobalConfig | None = None

    @property
    def raw(self) -> RawConfig:
        if self._raw is None:
            self._raw = self._source.load()
        return self._raw

    def global_config(self) -> GlobalConfig:
        if self._cfg is None:
            self._cfg = resolve_global_config(self.raw)
        return self._cfg

    def resolve_project_config(self, project_id: str) -> ProjectConfig:
        return resolve_project_config(self.global_config(), project_id)

    def validate(self, *, env: Mapping[str, str] | None = None) -> list[ConfigError]:
        return validate_required(self.global_config(), env=env)


# --------------------------------------------------------------------------- #
# R7 定义文档数据层（IFC-IB-288~292）—— 在文件末尾导入，确保子模块可依赖已就绪的
# `ib.core` 契约，且不产生包初始化期的循环导入。
# --------------------------------------------------------------------------- #
from .definition import (  # noqa: E402  (循环导入防护：置于模块末尾)
    DEFAULT_MAX_EXPERT_STEPS,
    NON_EDITABLE_FIELDS,
    SUPPORTED_SCHEMA_VERSION,
    FileDefinitionDocumentStore,
    InMemoryDefinitionDocumentStore,
    build_definition_document,
    content_hash_conflict_item,
    derive,
    document_from_json,
    document_to_json,
    editable_field_whitelist,
    non_editable_changes,
    semantic_hash,
    validate,
    validate_definition_full,
)
from .prompts import (  # noqa: E402  (REV-16-2 提示词域；同「置于模块末尾」防护)
    EXPERT_PROMPT_DIR_KEY,
    EXPERT_PROMPT_ENABLED_KEY,
    FALLBACK_FILENAME,
    LAYER_FILENAMES,
    MAIN_FILENAME,
    FsExpertPromptStore,
    InMemoryExpertPromptStore,
    derive_prompt_layers,
    load_prompt_bundle,
    load_prompt_directory,
    merge_prompt_layers,
    prompt_content_hash,
    prompt_domain_enabled,
    validate_prompt_directory,
    validate_tool_params,
    with_prompt_bundles,
)
