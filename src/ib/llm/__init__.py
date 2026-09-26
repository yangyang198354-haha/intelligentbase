"""
@module MOD-IB-20
@implements IFC-IB-211 build_router / 212 build_expert / 213 build_aggregator
            IFC-IB-214 health / 215 describe_egress
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

LLM 端点抽象（module_design.md §3 MOD-IB-20；ADR-08；REQ-FUNC-IB-18/19/21；DR-04；
AC-IB-12-05、AC-IB-09-07）。

## 三个角色在端口**内部**构造，provider 细节不外泄

编排层（MOD-IB-22）只说「给我路由角色」「给我专家角色」，**不知道**背后是
云端 OpenAI 兼容端点、本地模型还是测试替身。这条边界让「换模型」成为一个装配期改动，
不动任何编排代码 —— 也正因为如此，本模块是**唯一**允许 import langchain 的地方
（`langchain-openai` 属它的外部依赖），其余模块保持 framework-free。

## 三档温度是**行为契约**，不是调参偏好

| 角色 | 温度 | 理由 |
|------|------|------|
| 路由分类器（`build_router`） | **0** | 同一句提问必须**恒得同一路由**（AC-IB-09-07）。有随机性就无法复现「为什么走了这个专家」，路由问题将无法定位 |
| 专家（`build_expert`） | 略高 | 作答需要自然表达，允许有限随机 |
| 聚合器（`build_aggregator`） | 低 | 融合多个专家结果，需要稳定与忠实，不需要创意 |

路由温度为 0 是**硬性**的：它不是「推荐值」，而是「可复现性」与「随机路由」之间的取舍，
后者会让生产事故无法复现。

## 外发边界必须显式声明（AC-IB-12-05）

云端 LLM 意味着「用户的提问 + 检索到的知识片段」会**离开内网**。这件事不能只写在文档里 ——
它必须是一个**可被程序读取**的声明（`EgressDescriptor`），以便：

  * `/healthz/deps` 直接对外暴露「数据外发到哪儿、外发哪几类数据」（IFC-IB-249）；
  * 合规评审与部署检查清单有**机器可核验**的依据，而不是人去翻代码。

## 依赖版本 pin（不可放宽）

`langchain-openai` **必须 `<0.3`**。0.3.x 移除了 `_convert_chunk_to_generation_chunk`
（本项目流式解析所依赖的内部符号），会静默地让流式输出退化成「一次性返回」——
FreeArk 已有过一次生产漂移（见 CLAUDE.md 开发约定 7）。本模块在装配期做**版本断言**，
把这个曾经靠人记住的约定变成启动即失败的硬检查。
"""

from __future__ import annotations

import threading
from typing import Any

from ib.core import (
    EgressDescriptor,
    ExpertSpec,
    HealthStatus,
    LlmRole,
)

__all__ = [
    "OpenAiCompatibleProvider",
    "FakeLlmProvider",
    "build_llm_provider",
    "assert_langchain_openai_version",
    "REQUIRED_LANGCHAIN_OPENAI_SPEC",
    "DEFAULT_REMOTE_DATA_CATEGORIES",
    "PROMPT_HEADER",
]

#: 依赖约束（**不可放宽**，见模块文档）。
REQUIRED_LANGCHAIN_OPENAI_SPEC = ">=0.2,<0.3"

#: 外发数据类别（面向合规的可读声明；新增外发内容必须同步修订此处）。
DEFAULT_REMOTE_DATA_CATEGORIES = [
    "用户提问文本",
    "检索命中的知识片段（含文件名与位置）",
    "系统提示（专家人格与工具能力摘要）",
    "对话历史（按会话配置的窗口）",
]

#: 注入到每个角色实现里的提示头（provider 层统一，避免各角色各自拼装而漂移）。
PROMPT_HEADER = "你是企业内部知识问答助手。"


def assert_langchain_openai_version() -> str:
    """装配期断言 `langchain-openai` 版本符合 pin，不符即 `StartupError`。

    返回实际版本串（供启动日志）。**导入失败**也视为不满足（生产必须装得上）。
    这里刻意不做「警告后继续」：流式退化是**静默**的（接口仍工作，只是不再逐字推送），
    靠日志警告几乎不可能在部署当天被发现，必须以启动失败迫使其修正。
    """
    from ib.core import StartupError

    try:
        from importlib.metadata import version

        actual = version("langchain-openai")
    except Exception as exc:  # noqa: BLE001
        raise StartupError(
            f"未安装 langchain-openai（要求 {REQUIRED_LANGCHAIN_OPENAI_SPEC}）：{type(exc).__name__}"
        ) from exc
    if not _satisfies(actual, "<0.3"):
        raise StartupError(
            f"langchain-openai 版本不满足约束 {REQUIRED_LANGCHAIN_OPENAI_SPEC}（实测 {actual}）。"
            "0.3.x 移除了 _convert_chunk_to_generation_chunk，会导致流式输出静默退化为一次性返回。"
        )
    return actual


def _satisfies(version_str: str, constraint: str) -> bool:
    """"0.3.x 以上"判定（只支持 `<X.Y` 形式，够用且无第三方依赖）。"""
    if not constraint.startswith("<"):
        return True
    try:
        bound = constraint[1:].strip()
        target = tuple(int(part) for part in bound.split("."))
        actual = tuple(
            int(part)
            for part in version_str.split("+")[0].split(".")[: len(target)]
            if part.isdigit()
        )
    except (ValueError, TypeError):  # pragma: no cover - 版本串异常时不阻断启动
        return True
    return actual < target


class OpenAiCompatibleProvider:
    """OpenAI 兼容端点（生产：云端 DeepSeek；ADR-08）。

    **惰性构造客户端**：`langchain_openai` 只在首次 `build_*` 时导入，因此本类可以在
    没有安装 langchain 的环境里被 import（离线单测只装配 `FakeLlmProvider`，
    不需要把 langchain 拖进依赖树）。
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        router_temperature: float = 0.0,
        expert_temperature: float = 0.6,
        aggregator_temperature: float = 0.2,
        request_timeout_s: float = 60.0,
    ) -> None:
        if not base_url or not model:
            from ib.core import StartupError

            raise StartupError("LLM base_url 与 model 必填（缺失即启动失败，不静默降级为假实现）")
        if not api_key:
            from ib.core import StartupError

            raise StartupError(
                "LLM API key 缺失：请通过环境变量注入（键名见 IB_* 配置，禁止写入代码或配置文件）"
            )
        self._base_url = base_url
        self._model = model
        self._api_key = api_key
        self._router_temperature = float(router_temperature)
        self._expert_temperature = float(expert_temperature)
        self._aggregator_temperature = float(aggregator_temperature)
        self._timeout = float(request_timeout_s)
        self._lock = threading.Lock()
        self._clients: dict[tuple[float, str | None], Any] = {}

    # --- 端口方法 --- #

    def build_router(self) -> LlmRole:
        """[IFC-IB-211] 路由分类角色，**temperature=0**（可复现性是硬要求）。"""
        return LlmRole(
            role="router",
            temperature=0.0,
            impl=self._client(0.0, "只输出 JSON 数组，不要任何解释或代码围栏。"),
        )

    def build_expert(self, spec: ExpertSpec) -> LlmRole:
        """[IFC-IB-212] 专家角色。人格文本优先取自 `spec.fallback_prompt`
        （主提示由接入方按 `spec.name` 加载后经 `system_prompt` 覆盖）。"""
        return LlmRole(
            role="expert",
            temperature=self._expert_temperature,
            impl=self._client(self._expert_temperature, spec.fallback_prompt),
        )

    def build_aggregator(self) -> LlmRole:
        """[IFC-IB-213] 聚合角色（低温度：融合要忠实、稳定）。"""
        return LlmRole(
            role="aggregator",
            temperature=self._aggregator_temperature,
            impl=self._client(
                self._aggregator_temperature,
                "把多方结果融合为一段回答，不要提及内部分工或专家名称。",
            ),
        )

    def health(self) -> HealthStatus:
        """[IFC-IB-214] 健康探测。**永不抛异常**（健康检查不该打挂自己）。"""
        import time

        from ib.core import DependencyUnavailableError

        started = time.monotonic()
        try:
            client = self._client(self._router_temperature, None)
            # 最小代价探测：单 token 请求
            if hasattr(client, "invoke"):
                client.invoke("ping")
            latency = int((time.monotonic() - started) * 1000)
            return HealthStatus(ok=True, detail=f"model={self._model}", latency_ms=latency)
        except DependencyUnavailableError as exc:
            return HealthStatus(ok=False, detail=str(exc), latency_ms=None)
        except Exception as exc:  # noqa: BLE001
            return HealthStatus(
                ok=False,
                detail=f"LLM 探测失败（{type(exc).__name__}）",
                latency_ms=int((time.monotonic() - started) * 1000),
            )

    def describe_egress(self) -> EgressDescriptor:
        """[IFC-IB-215] 数据外发边界声明（**远程=True**，含端点主机名）。"""
        return EgressDescriptor(
            remote=True,
            endpoint_host=_host_of(self._base_url),
            data_categories=list(DEFAULT_REMOTE_DATA_CATEGORIES),
        )

    # --- 内部 --- #

    def _client(self, temperature: float, system_prompt: str | None) -> Any:
        """构造（并缓存）一个可调用客户端。

        缓存键含 `system_prompt`：不同专家的系统提示必须落到**不同实例**，
        否则会出现「A 专家的人格被 B 专家复用」的串味回答。
        """
        key = (temperature, system_prompt)
        with self._lock:
            cached = self._clients.get(key)
            if cached is not None:
                return cached
            client = _make_langchain_client(
                base_url=self._base_url,
                model=self._model,
                api_key=self._api_key,
                temperature=temperature,
                timeout=self._timeout,
                system_prompt=system_prompt,
            )
            self._clients[key] = client
            return client


class FakeLlmProvider:
    """离线替身（AC-IB-15-01）。

    刻意**不是**「永远返回固定串」的假货，而是**脚本化**的：按角色区分回答，
    并能模拟故障（`unavailable` / `timeout`）以便验证降级路径。
    `egress.remote=False` —— 离线装配下数据不出机器，这一点必须如实反映在健康/合规输出里。
    """

    def __init__(
        self,
        *,
        router_output: str = "[]",
        expert_output: str = "（离线替身的示例回答）",
        aggregator_output: str = "（离线替身的聚合回答）",
        unavailable: bool = False,
        timeout: bool = False,
    ) -> None:
        self.router_output = router_output
        self.expert_output = expert_output
        self.aggregator_output = aggregator_output
        self._unavailable = unavailable
        self._timeout = timeout

    def _guard(self) -> None:
        from ib.core import DependencyUnavailableError

        if self._unavailable:
            raise DependencyUnavailableError("FakeLlmProvider: 依赖不可达（模拟）", dependency="llm")
        if self._timeout:
            raise DependencyUnavailableError("FakeLlmProvider: 超时（模拟）", dependency="llm")

    def build_router(self) -> LlmRole:
        return LlmRole(role="router", temperature=0.0, impl=self._role_callable(self.router_output))

    def build_expert(self, spec: ExpertSpec) -> LlmRole:
        text = f"[{spec.cn_label}] {self.expert_output}"
        return LlmRole(role="expert", temperature=0.6, impl=self._role_callable(text))

    def build_aggregator(self) -> LlmRole:
        return LlmRole(role="aggregator", temperature=0.2, impl=self._role_callable(self.aggregator_output))

    def health(self) -> HealthStatus:
        try:
            self._guard()
        except Exception as exc:  # noqa: BLE001
            return HealthStatus(ok=False, detail=str(exc), latency_ms=0)
        return HealthStatus(ok=True, detail="fake", latency_ms=0)

    def describe_egress(self) -> EgressDescriptor:
        return EgressDescriptor(remote=False, endpoint_host="", data_categories=[])

    def _role_callable(self, text: str) -> Any:
        def _call(prompt: str = "") -> str:
            self._guard()
            return text

        return _call


def build_llm_provider(cfg: Any) -> Any:
    """按配置构造 LLM provider（组合根单点调用）。

    离线模式下**返回即抛**：`IB_OFFLINE_MODE=1` 时装配 `FakeLlmProvider` 是组合根的职责，
    本函数若在离线模式被调用，说明装配表写错了（应显式选 `fake` 后端），
    静默返回真实 provider 会让离线测试意外触网。
    """
    if getattr(cfg, "offline_mode", False) and cfg.llm.backend != "fake":
        from ib.core import StartupError

        raise StartupError(
            "离线模式（IB_OFFLINE_MODE=1）下 LLM 后端必须显式为 fake，拒绝对外发起请求"
        )
    if cfg.llm.backend == "fake":
        return FakeLlmProvider()
    if cfg.llm.backend != "openai_compatible":
        from ib.core import StartupError

        raise StartupError(f"未知的 LLM 后端：{cfg.llm.backend!r}")
    from ib.config import read_secret

    api_key = read_secret(cfg.llm.api_key_env)
    if not api_key:
        from ib.core import StartupError

        raise StartupError(
            f"未读取到 LLM API key（环境变量 {cfg.llm.api_key_env} 为空）；"
            "密钥只允许经环境变量注入，禁止写入任何被跟踪的文件"
        )
    assert_langchain_openai_version()
    return OpenAiCompatibleProvider(
        base_url=cfg.llm.base_url,
        model=cfg.llm.model,
        api_key=api_key,
        router_temperature=cfg.llm.router_temperature,
        expert_temperature=cfg.llm.expert_temperature,
        aggregator_temperature=cfg.llm.aggregator_temperature,
        request_timeout_s=cfg.llm.request_timeout_s,
    )


def _make_langchain_client(
    *,
    base_url: str,
    model: str,
    api_key: str,
    temperature: float,
    timeout: float,
    system_prompt: str | None,
) -> Any:
    """构造 langchain 客户端（**唯一** import langchain 的位置）。"""
    try:
        from langchain_openai import ChatOpenAI
    except Exception as exc:  # noqa: BLE001
        from ib.core import DependencyUnavailableError

        raise DependencyUnavailableError(
            "langchain-openai 不可用（请安装并满足 <0.3 约束）", dependency="llm"
        ) from exc
    client = ChatOpenAI(
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
        max_retries=1,
    )
    if system_prompt:
        # 以「提示头 + 角色提示」的方式注入系统消息；对编排层仍只暴露 `.invoke(text)`，
        # 故 langchain 的消息结构不会外泄到 MOD-IB-22。
        return _PromptedClient(client, f"{PROMPT_HEADER}\n{system_prompt}")
    return client


class _PromptedClient:
    """把系统提示前置到用户输入的最简包装（对编排层暴露 `.invoke(text)`）。"""

    def __init__(self, client: Any, system_prompt: str) -> None:
        self._client = client
        self._system_prompt = system_prompt

    def invoke(self, prompt: str, **kwargs: Any) -> Any:
        return self._client.invoke(
            [("system", self._system_prompt), ("human", prompt)], **kwargs
        )

    def __call__(self, prompt: str) -> Any:
        return self.invoke(prompt)


def _host_of(url: str) -> str:
    """从 URL 取主机名（仅用于合规声明，不含路径 —— 路径可能含端点 id）。"""
    try:
        from urllib.parse import urlparse

        return urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001  # pragma: no cover
        return ""
