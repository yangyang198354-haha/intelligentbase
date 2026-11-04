# MOD-R28-03 / implements IFC-R28-005 / depends MOD-R28-01
"""搜索提供方：端口配置、注册表、Null、Fake、提供方工厂（离线 / 生产闸）。

本文件不含任何网络代码（不 import urllib.request / http.client / socket / ssl）：
DeepSeek 适配器及其唯一网络缝在 `deepseek.py`，由 `build_search_provider` 在非离线分支惰性 import
（selfcheck `web_egress_single_exit` 保持“search.py 无网络导入”的断言）。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Sequence

from ib.core import (
    ConfigError,
    EgressDescriptor,
    HealthStatus,
    SearchOutcome,
    SearchProvider,
    SearchQuery,
)

if TYPE_CHECKING:  # 仅类型检查：运行期不 import deepseek（惰性）
    from .deepseek import HttpPostTransport

__all__ = [
    "WebSearchSettings",
    "SearchProviderFactory",
    "register_search_provider",
    "build_search_provider",
    "NullSearchProvider",
    "FakeSearchProvider",
    "registered_provider_ids",
]

_log = logging.getLogger("intelligentbase")

#: 内置标识；与之重名的登记一律 ValueError（IFC-R28-005）。
_BUILTIN_IDS = ("none", "deepseek", "fake")


@dataclass(frozen=True, slots=True)
class WebSearchSettings:
    # "none" | "deepseek" | "fake"（fake 仅 offline=True 可构造）| 已登记的扩展标识。
    # 2.1.0：删除 base_url——端点是 deepseek.py 的常量（ADR-R28-11 D4）。
    provider_id: str = "none"


SearchProviderFactory = Callable[[WebSearchSettings, "str | None"], SearchProvider]

_REGISTRY: dict[str, SearchProviderFactory] = {}
_REG_LOCK = threading.Lock()


def register_search_provider(provider_id: str, factory: SearchProviderFactory) -> None:
    """重复登记或与内置标识（none / deepseek / fake）重名 ⇒ ValueError。"""
    pid = (provider_id or "").strip()
    if not pid:
        raise ValueError("provider_id 不得为空")
    if pid in _BUILTIN_IDS:
        raise ValueError(f"搜索提供方标识为内置保留: {pid}")
    with _REG_LOCK:
        if pid in _REGISTRY:
            raise ValueError(f"搜索提供方已登记: {pid}")
        _REGISTRY[pid] = factory


def registered_provider_ids() -> tuple[str, ...]:
    with _REG_LOCK:
        return tuple(_REGISTRY)


class NullSearchProvider:
    """未配置联网搜索时的提供方：search ⇒ not_configured；describe_egress ⇒ remote=False。"""

    provider_id = "none"

    def search(self, query: SearchQuery) -> SearchOutcome:
        return SearchOutcome((), "not_configured", 0)

    def health(self) -> HealthStatus:
        return HealthStatus(ok=True, detail="not_configured")

    def describe_egress(self) -> EgressDescriptor:
        return EgressDescriptor(remote=False, endpoint_host="", data_categories=[])


class FakeSearchProvider:
    """离线替身（C-R28-02）；与生产适配器过同一套端口一致性测试。"""

    def __init__(
        self,
        script: Sequence["SearchOutcome | Callable[[SearchQuery], SearchOutcome]"] = (),
        *,
        latency_s: float = 0.0,
        provider_id: str = "fake",
    ) -> None:
        self._script = list(script)
        self._latency_s = float(latency_s)
        self.provider_id = provider_id
        self.calls: list[SearchQuery] = []
        self._lock = threading.Lock()
        self._i = 0

    def search(self, query: SearchQuery) -> SearchOutcome:
        t0 = time.monotonic()
        with self._lock:
            self.calls.append(query)
            step = self._script[self._i] if self._i < len(self._script) else None
            self._i += 1
        try:
            if self._latency_s > 0:
                time.sleep(self._latency_s)
            if step is None:
                outcome = SearchOutcome((), None, 0)
            elif callable(step):
                outcome = step(query)
            else:
                outcome = step
        except Exception:  # noqa: BLE001 - 端口契约：永不抛
            return SearchOutcome((), "bad_response", int((time.monotonic() - t0) * 1000))
        if outcome.error is not None and outcome.hits:
            outcome = SearchOutcome((), outcome.error, outcome.elapsed_ms)
        return outcome

    def health(self) -> HealthStatus:
        return HealthStatus(ok=True, detail="fake")

    def describe_egress(self) -> EgressDescriptor:
        return EgressDescriptor(remote=True, endpoint_host="fake.invalid", data_categories=["web_search_query"])


def build_search_provider(
    settings: WebSearchSettings,
    api_key: str | None,
    *,
    offline: bool,
    transport: "HttpPostTransport | None" = None,
) -> SearchProvider:
    """提供方工厂（IFC-R28-005；REQ-FUNC-019 / ADR-R28-13）。

    "none" ⇒ Null；"fake" 且 offline ⇒ Fake；"fake" 且非离线 ⇒ ConfigError（键名，不含所配值；Fake 不被构造）；
    "deepseek" 且 offline ⇒ Fake（离线永不触网）；"deepseek" 且非离线：api_key 为空 ⇒ Null 并记 WARNING，
    否则 DeepSeekSearchProvider（transport 缺省为真实 UrllibPostTransport，仅在此分支构造）；
    其他已登记标识 ⇒ factory；未登记 ⇒ ConfigError（不含 api_key）。
    """
    pid = (settings.provider_id or "none").strip().lower() or "none"
    if pid == "none":
        return NullSearchProvider()
    if pid == "fake":
        if not offline:
            raise ConfigError("IB_WEB_SEARCH_PROVIDER 取值不允许用于非离线配置", key="IB_WEB_SEARCH_PROVIDER")
        return FakeSearchProvider()
    if pid == "deepseek":
        if offline:
            return FakeSearchProvider()
        if not (api_key or "").strip():
            _log.warning("web search provider deepseek degraded to not_configured (api key unavailable)")
            return NullSearchProvider()
        from .deepseek import DeepSeekSearchProvider, UrllibPostTransport  # 惰性：search.py 自身无网络导入

        return DeepSeekSearchProvider(str(api_key).strip(), transport=transport or UrllibPostTransport())
    with _REG_LOCK:
        factory = _REGISTRY.get(pid)
    if factory is None:
        raise ConfigError("IB_WEB_SEARCH_PROVIDER 取值未登记", key="IB_WEB_SEARCH_PROVIDER")
    return factory(settings, api_key)
