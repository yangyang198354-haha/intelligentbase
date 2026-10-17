"""[REV-17 → **REV-20 修订**] 提示词「通道 + 非空性 + legacy 键」单元覆盖。

覆盖三件真缺陷（原 REV-17 引入，本文件在 REV-20 下按新契约改写）：

  1. **system 位真的生效**：合并后的生效提示词必须进 `build_expert(system_prompt=...)`，
     human 位只留用户问题本身。此前它被拼进 human 前缀，system 位恒为兜底 ——
     即「配置页编辑的 markdown 主提示词从未成为系统提示」。
  2. **代码内置安全网退役**（**契约翻转**，REV-20 / OQ-IB-42=B / ADR-48）：
     内置注册表的 `ExpertSpec.fallback_prompt` 字段已**去驱动化**（恒为空串，不参与任何
     运行期提示词取值）；「生效系统提示词恒非空」改由**创建期落盘 + 装配期 fail-closed**
     （`prompt_missing`）保证 —— 两层皆缺不再回落内置文案，而是**抛错**。
  3. **legacy 键一律 fail-closed**（**契约翻转**）：旧定义文档残留的
     `experts[].fallback_prompt` 不再「与内置逐字比对后分级」，因比对基准已随安全网删除
     —— 只要出现即拒绝装载并指明迁移目标 `main.md`（绝不静默丢用户写的提示词）。

另附 `_clients` 缓存上界断言（装配期常量不变式；ADR-36 硬规则）。

离线纪律：进程内替身 + 临时文件系统；无网络；无任何真实凭据。
"""

from __future__ import annotations

import json

import pytest

from ib.core import ConfigError, ExpertSpec, LlmRole, PromptNotFoundError
from ib.llm import OpenAiCompatibleProvider

from tests.conftest import offline_raw

# --------------------------------------------------------------------------- #
# 替身：记录 `build_expert` 收到的系统位与 impl 收到的 human 位
# --------------------------------------------------------------------------- #


class _RecordingImpl:
    """记录被投喂的 human 文本，回一个非空答复（避免 `empty_response` 降级掩盖断言）。"""

    def __init__(self, record: dict) -> None:
        self._record = record

    def invoke(self, prompt: str, **kwargs):
        self._record["human"] = prompt
        return "专家答复"


class _RecordingLlm:
    """只实现 `_run_expert` 用到的端口：记录 `system_prompt`，回一个记录型 impl。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []
        self.record: dict = {}

    def build_expert(self, spec, *, system_prompt: str | None = None) -> LlmRole:
        self.calls.append((spec.name, system_prompt))
        return LlmRole(role="expert", temperature=0.0, impl=_RecordingImpl(self.record))


def _kb_agent_spec() -> ExpertSpec:
    """内置注册表唯一专家（`fallback_prompt` 已去驱动化 = 空串）。"""
    from ib.experts import BUILTIN_DEFAULT_KB_AGENT

    return BUILTIN_DEFAULT_KB_AGENT


def _synthetic_spec(*, fallback_prompt: str) -> ExpertSpec:
    """合成一个带非空 `fallback_prompt` 字段的专家 —— 仅用于验证**通用透传机制**仍在
    （内置注册表已不再使用该字段，故不能用内置专家来验证这条机制）。"""
    return ExpertSpec(
        name="synthetic",
        cn_label="合成",
        keywords=("合成",),
        is_data_expert=False,
        fallback_prompt=fallback_prompt,
        is_delegating=False,
        is_default=True,
    )


# --------------------------------------------------------------------------- #
# 1 · system 位（通道矫正）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R20_effective_prompt_goes_to_system_slot():
    """合并后的生效提示词进 system 位；human 位**只**含用户问题（不重复人格文本）。"""
    from ib.orchestration import _run_expert

    llm = _RecordingLlm()
    merged = "你是知识库助手（装配期由项目提示词目录派生）。"
    result = _run_expert({"expert": "kb-agent", "query": "资料里怎么说的？", "prompt": merged}, llm, {})

    assert result.degraded is False, result.degrade_reason
    assert llm.calls == [("kb-agent", merged)], "生效提示词必须经 system_prompt 传入"
    assert llm.record["human"] == "资料里怎么说的？", "human 位只能有用户问题"
    # 旧口径的 human 前缀拼接（`f"{prompt}\n\n用户问题：{query}"`）**必须**消失
    assert "用户问题：" not in llm.record["human"]
    assert merged not in llm.record["human"], "人格文本不得回填 human（否则同一段出现两次）"


def test_TC_UNIT_R20_empty_prompt_becomes_none_not_empty_string():
    """空串 `prompt` → 传 `None`（`prompt or None`）。

    `_clients` 以 `(temperature, system_prompt)` 为键；空串与 `None` 语义不同，
    故本函数保证「未取到提示词」时统一走 `None`，两种情形都可观测、可断言。
    """
    from ib.orchestration import _run_expert

    llm = _RecordingLlm()
    result = _run_expert({"expert": "kb-agent", "query": "q", "prompt": ""}, llm, {})
    assert result.degraded is False
    assert llm.calls == [("kb-agent", None)]
    assert llm.record["human"] == "q"


# --------------------------------------------------------------------------- #
# 2 · `OpenAiCompatibleProvider.build_expert` 的回落语义 + `_clients` 上界
# --------------------------------------------------------------------------- #


def _bare_provider(monkeypatch) -> tuple[OpenAiCompatibleProvider, list]:
    """绕开 `__init__` 的凭据闸门造一个 `OpenAiCompatibleProvider`，并拦住真实客户端构造。

    `_client` 只依赖 `_base_url` / `_model` / `_api_key` / `_timeout` / `_lock` / `_clients`
    与 `_*_temperature`，故可 `object.__new__` 后手工补齐 —— 离线环境无 langchain-openai，
    真实构造必然 ImportError。值均为占位符，**无任何真实凭据**。
    """
    import threading

    import ib.llm as llm_mod

    recorded: list[dict] = []

    def _fake_client(**kwargs):
        recorded.append(kwargs)
        return {"fake": True, **kwargs}

    monkeypatch.setattr(llm_mod, "_make_langchain_client", _fake_client)
    provider = object.__new__(OpenAiCompatibleProvider)
    provider._base_url = "http://127.0.0.1:1/v1"  # noqa: S105 - 占位，永不发出请求
    provider._model = "placeholder-model"
    provider._api_key = "placeholder"  # noqa: S105 - 占位，非真实凭据
    provider._timeout = 1.0
    provider._router_temperature = 0.0
    provider._expert_temperature = 0.3
    provider._aggregator_temperature = 0.2
    provider._lock = threading.Lock()
    provider._clients = {}
    return provider, recorded


def test_TC_UNIT_R20_build_expert_passthrough_and_de_driven_registry(monkeypatch):
    """**契约翻转（REV-20 / ADR-48）**：原 REV-17 断言「缺省 / 全空白 → 回落
    `spec.fallback_prompt`（代码内置安全网）且恒非空」；REV-20 后：

      * 内置注册表唯一专家的 `fallback_prompt` 已**去驱动化**（恒空串）；
      * `build_expert` 的「缺省 → 回落 `spec.fallback_prompt`」**通用透传机制仍在**
        （对任何显式构造的 spec 都成立），但**不再是**代码内置安全网。
    """
    provider, recorded = _bare_provider(monkeypatch)

    # 显式给了 system_prompt 就用它
    provider.build_expert(_kb_agent_spec(), system_prompt="装配期合并结果")
    assert recorded[-1]["system_prompt"] == "装配期合并结果"

    # 通用透传机制：合成 spec 的字段值被如实回落
    provider.build_expert(_synthetic_spec(fallback_prompt="SB"))
    assert recorded[-1]["system_prompt"] == "SB"

    # 内置注册表：该字段恒空串（去驱动化 —— 提示词取值不再来自代码常量）
    provider.build_expert(_kb_agent_spec())
    assert recorded[-1]["system_prompt"] == ""
    assert _kb_agent_spec().fallback_prompt == ""


def test_TC_UNIT_R20_clients_cache_bounded_by_experts(monkeypatch):
    """`_clients` 上界 = 专家数 + 3（路由 / 专家 / 聚合三类固定角色各一份）。

    该断言守的是 ADR-36 的**硬规则**：`system_prompt` 只允许是装配期常量。一旦有人把
    请求期变量（用户问题 / 会话历史）拼进来，这个上界会随请求数增长 —— 即内存泄漏，
    且会把「同人格共用实例」的前提悄悄破坏掉。
    """
    from ib.experts import EXPERT_SPECS, get

    provider, _ = _bare_provider(monkeypatch)
    names = [s.name for s in EXPERT_SPECS]
    for name in names:
        # 同一专家重复构建（模拟每次装配/每轮问答）不得新增缓存项
        provider.build_expert(get(name), system_prompt=f"prompt-for-{name}")
        provider.build_expert(get(name), system_prompt=f"prompt-for-{name}")
    provider.build_router()
    provider.build_aggregator()
    provider._client(0.0, None)  # health() 的探测客户端（裸客户端，独立键）

    assert len(provider._clients) == len(set(names)) + 3
    assert len(provider._clients) <= len(names) + 3


# --------------------------------------------------------------------------- #
# 3 · 未落盘专家的 fail-closed（**替代原「通用内置安全网」**）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R20_expert_without_prompt_files_fails_closed():
    """**契约翻转（REV-20 / ADR-48）**：原口径下「未登记 / 未落盘专家恒有非空内置兜底」
    用于打破「界面新增专家」死锁；REV-20 删除代码内置提示词后，同场景改为
    **`PromptNotFoundError(code="prompt_missing")`** —— 死锁改由**创建期落盘**
    （ADR-51 / IFC-IB-390）+ **回填迁移**（IFC-IB-391）打破，不再由代码兜底打破。
    """
    from ib.config import merge_prompt_layers

    ghost = "brand-new-expert-not-in-registry"
    with pytest.raises(PromptNotFoundError) as excinfo:
        merge_prompt_layers(ghost, main_content=None, fallback_content=None)
    assert excinfo.value.code == "prompt_missing"
    # 落盘两层之一即恢复可用（新的破死锁路径）
    bundle = merge_prompt_layers(ghost, main_content="# 新专家提示词\n", fallback_content=None)
    assert bundle.resolved_from == "main_file"
    assert bundle.effective_prompt.strip()


def test_TC_UNIT_R17_definition_doc_no_longer_requires_fallback_prompt():
    """定义域校验项 5 只剩 `cn_label`；`experts[].fallback_prompt` 已出可编辑白名单。"""
    from ib.config import build_definition_document, editable_field_whitelist, validate
    from ib.core import (
        ConditionalEdgeSpec,
        ExpertSpecInput,
        OrchestrationSpecInput,
        RouteSpecInput,
    )

    def _build(cn_label: str):
        # REV-17（ADR-36）：`ExpertSpecInput` 已无 `fallback_prompt` —— 新专家照样能构造。
        spec = ExpertSpecInput(
            name="c",
            cn_label=cn_label,
            keywords=(),
            exemplars=(),
            is_data_expert=False,
            is_delegating=False,
            is_default=True,
        )
        return build_definition_document(
            project_id="p1",
            experts=(spec,),
            route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="c"),
            orchestration=OrchestrationSpecInput(
                nodes=("route", "c"),
                conditional_edges=(ConditionalEdgeSpec("route", (("c", "c"),)),),
            ),
        )

    report = validate(_build("新专家"))
    assert not [e for e in report.errors if e.path.endswith("fallback_prompt")]
    assert "experts[].fallback_prompt" not in editable_field_whitelist()

    # 反证：`cn_label` 为空仍然报错（收窄的是字段，不是整个校验项）
    blank = _build("   ")
    assert any(
        e.code == "expert_text_missing" and e.path.endswith("cn_label")
        for e in validate(blank).errors
    )


# --------------------------------------------------------------------------- #
# 4 · legacy 键：**REV-20 起一律 fail-closed**
# --------------------------------------------------------------------------- #


def _legacy_doc_text(*, name: str, fallback: str) -> str:
    """构造一份「带已移除 fallback_prompt 键」的旧文档 JSON（最小可解析结构）。"""
    return json.dumps(
        {
            "schema_version": 1,
            "project_id": "p1",
            "experts": [
                {"name": name, "cn_label": "标签", "fallback_prompt": fallback, "is_default": True}
            ],
            "route": {
                "tau": 0.65,
                "margin": 0.05,
                "max_expert_steps": 6,
                "default_expert": name,
            },
            "orchestration": {"nodes": [name], "conditional_edges": [], "edges": []},
            "tool_grants": [],
        }
    )


@pytest.mark.parametrize(
    ("name", "fallback"),
    [
        ("kb-agent", ""),            # 与「曾经的内置兜底」相同的情形（现在无从比对）
        ("kb-agent", "用户手写的、绝不能静默丢掉的一段提示词"),
        ("幽灵", "x"),               # 未登记专家
    ],
)
def test_TC_UNIT_R20_legacy_key_always_fails_closed(name: str, fallback: str):
    """**契约翻转（REV-20 / ADR-48 决定 3）**：原 REV-17 口径按「与内置逐字比对」分级
    （相同→静默丢弃 / 不同→fail-closed）；比对基准随代码内置提示词一并删除后，
    **一律 fail-closed** —— 只要残留 `fallback_prompt` 键即拒绝装载。

    断言：① 抛 `ConfigError`；② 指明专家名与迁移目标 `main.md`；③ **不回显正文**、
    只报长度（IFC-IB-348 纪律）。
    """
    from ib.config import document_from_json

    with pytest.raises(ConfigError) as excinfo:
        document_from_json("p1", _legacy_doc_text(name=name, fallback=fallback))
    message = str(excinfo.value)
    assert name in message
    assert "main.md" in message, "必须指明迁移目标"
    assert str(len(fallback.strip())) in message, "只报长度，便于运维核对"
    if fallback.strip():
        assert fallback not in message, "错误消息不得回显提示词正文（IFC-IB-348 纪律）"


# --------------------------------------------------------------------------- #
# 5 · 与运行期配置源无关的守卫：`offline_raw` 只用于保证本文件不触碰真实配置
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R17_offline_raw_has_no_definition_doc_path():
    """守卫：本文件全程走内存定义文档，不得依赖任何真实定义文档路径。"""
    raw = offline_raw()
    assert "IB_DEFINITION_DOC_PATH" not in json.dumps(raw)
    assert raw["offline_mode"] is True
