"""[REV-17 / ADR-36] 提示词兜底层重定位的**通道与安全网**单元覆盖。

覆盖三件在 REV-17 之前**没有覆盖面**的事（都是本次修订要堵的真缺陷）：

  1. **system 位真的生效**：合并后的生效提示词必须进 `build_expert(system_prompt=...)`，
     human 位只留用户问题本身。此前它被拼进 human 前缀，system 位恒为代码内置兜底 ——
     即「配置页编辑的 markdown 主提示词从未成为系统提示」。
  2. **内置安全网恒非空**：`main.md` / `fallback.md` 两层皆缺时回落
     `BUILTIN_FALLBACK_DEFAULT`，由此 ADR-29 的「兜底恒非空」由**结构**保证。
  3. **legacy 键分级处置**：旧定义文档残留的 `experts[].fallback_prompt` 与内置一致时
     静默丢弃、不一致时 fail-closed 并指明迁移目标（绝不静默丢用户写的提示词）。

另附 `_clients` 缓存上界断言（装配期常量不变式；ADR-36 硬规则）。

离线纪律：进程内替身 + 临时文件系统；无网络；无任何真实凭据。
"""

from __future__ import annotations

import json

import pytest

from ib.core import ConfigError, LlmRole
from ib.experts import (
    BUILTIN_FALLBACK_DEFAULT,
    BUILTIN_FALLBACKS,
    builtin_fallback_for,
    builtin_fallbacks_for,
)
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


# --------------------------------------------------------------------------- #
# 1 · system 位（通道矫正）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R17_effective_prompt_goes_to_system_slot():
    """合并后的生效提示词进 system 位；human 位**只**含用户问题（不重复人格文本）。"""
    from ib.orchestration import _run_expert

    llm = _RecordingLlm()
    merged = "你是系统管家（装配期由两域合并派生）。"
    result = _run_expert(
        {"expert": "freeark-expert", "query": "设备怎么巡检？", "prompt": merged}, llm, {}
    )

    assert result.degraded is False, result.degrade_reason
    assert llm.calls == [("freeark-expert", merged)], "生效提示词必须经 system_prompt 传入"
    assert llm.record["human"] == "设备怎么巡检？", "human 位只能有用户问题"
    # 旧口径的 human 前缀拼接（`f"{prompt}\n\n用户问题：{query}"`）**必须**消失
    assert "用户问题：" not in llm.record["human"]
    assert merged not in llm.record["human"], "人格文本不得回填 human（否则同一段出现两次）"


def test_TC_UNIT_R17_empty_prompt_becomes_none_not_empty_string():
    """空串 `prompt` → 传 `None`（`prompt or None`）。

    空串会让 `_make_langchain_client` 返回**裸客户端**（无 system 注入、无 `run_tool_loop`），
    症状是**静默**同时失去 system 消息与 function-calling。传 `None` 则让 `build_expert`
    明确回落到 `spec.fallback_prompt`（内置安全网），两个能力都保住。
    """
    from ib.orchestration import _run_expert

    llm = _RecordingLlm()
    result = _run_expert({"expert": "freeark-expert", "query": "q", "prompt": ""}, llm, {})
    assert result.degraded is False
    assert llm.calls == [("freeark-expert", None)]
    assert llm.record["human"] == "q"


def test_TC_UNIT_R17_whitespace_prompt_never_reaches_client_bare(monkeypatch):
    """全空白 `prompt` 虽被原样传下（`"   "` 真值），但实现 `strip()` 后回落内置兜底 ——
    **真实的 `build_expert`** 必须把它变成非空系统提示，system 位不得塌成裸客户端。

    这条走真实 provider（拦掉客户端构造），断言的是「两段式防线的第二段」真的在：
    `_run_expert` 的 `or None` 挡不住空白串，靠的是 `build_expert` 的 `strip()`。
    """
    from ib.experts import get
    from ib.orchestration import _run_expert

    provider, recorded = _bare_provider(monkeypatch)
    _run_expert({"expert": "freeark-expert", "query": "q", "prompt": "   "}, provider, {})

    assert recorded[-1]["system_prompt"] == get("freeark-expert").fallback_prompt
    assert recorded[-1]["system_prompt"].strip(), "system 位恒非空（否则静默失去工具循环）"


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
    provider._base_url = "http://127.0.0.1:1/v1"  # noqa: SLF001 - 占位，永不发出请求
    provider._model = "placeholder-model"
    provider._api_key = "placeholder"  # noqa: S105 - 占位，非真实凭据
    provider._timeout = 1.0
    provider._router_temperature = 0.0
    provider._expert_temperature = 0.3
    provider._aggregator_temperature = 0.2
    provider._lock = threading.Lock()
    provider._clients = {}
    return provider, recorded


def test_TC_UNIT_R17_build_expert_uses_system_prompt_else_builtin_fallback(monkeypatch):
    """给了 `system_prompt` 就用它；缺省 / 全空白 → 回落 `spec.fallback_prompt`（内置安全网）。"""
    from ib.experts import get

    provider, recorded = _bare_provider(monkeypatch)
    spec = get("freeark-expert")

    provider.build_expert(spec, system_prompt="装配期合并结果")
    assert recorded[-1]["system_prompt"] == "装配期合并结果"

    provider.build_expert(spec)
    assert recorded[-1]["system_prompt"] == spec.fallback_prompt

    provider.build_expert(spec, system_prompt="   ")
    assert recorded[-1]["system_prompt"] == spec.fallback_prompt
    # 恒非空 —— 专家路径永不塌成裸客户端
    assert all(r["system_prompt"] for r in recorded)


def test_TC_UNIT_R17_clients_cache_bounded_by_experts(monkeypatch):
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
# 3 · 通用内置安全网（破「界面新增专家」死锁）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R17_builtin_fallback_covers_unregistered_expert():
    """未登记专家（`_DEFAULT_SPECS` 之外）也**恒**有非空内置兜底 —— 死锁由此打破。

    死锁原形：`PUT definition`（加专家 c）要求非空兜底 → `PUT prompts/c/fallback` 又因
    「专家未登记」直接 404。故**必须**有通用兜底，而不是「每个专家各自登记一份」。
    """
    from ib.config import merge_prompt_layers

    ghost = "brand-new-expert-not-in-defaults"
    assert ghost not in set(BUILTIN_FALLBACKS)
    assert builtin_fallback_for(ghost) == BUILTIN_FALLBACK_DEFAULT
    assert BUILTIN_FALLBACK_DEFAULT.strip()

    bundle = merge_prompt_layers(
        ghost,
        main_content=None,
        fallback_content=None,
        builtin_fallback=builtin_fallback_for(ghost),
    )
    assert bundle.resolved_from == "builtin_fallback"
    assert bundle.effective_prompt == BUILTIN_FALLBACK_DEFAULT
    # 「兜底非空」（ADR-29）由结构保证，不再依赖文档层校验放行
    assert bundle.fallback_prompt.strip()


def test_TC_UNIT_R17_builtin_fallbacks_for_is_total():
    """`builtin_fallbacks_for` 对任意名字列表都是**全函数**（无 KeyError / 无空洞）。"""
    names = ["freeark-expert", "幽灵专家", ""]
    got = builtin_fallbacks_for(names)
    assert set(got) == set(names)
    assert all(v.strip() for v in got.values())
    assert got["freeark-expert"] != BUILTIN_FALLBACK_DEFAULT, "已登记专家应取自己的专属兜底"


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
# 4 · legacy 键分级处置
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


def test_TC_UNIT_R17_legacy_key_identical_to_builtin_is_dropped_silently():
    """与内置兜底**逐字相同** → 静默丢弃（零信息损失）—— 生产种子文档正是这一支。"""
    from ib.config import document_from_json

    name = "freeark-expert"
    builtins = builtin_fallbacks_for([name])
    doc = document_from_json(
        "p1", _legacy_doc_text(name=name, fallback=builtins[name]), builtin_fallbacks=builtins
    )
    assert [e.name for e in doc.experts] == [name]
    # 字段已被移除：解析结果里根本没有承载这段文本的位置（也就无从「静默生效」）
    assert not hasattr(doc.experts[0], "fallback_prompt")


def test_TC_UNIT_R17_legacy_key_differing_from_builtin_fails_closed():
    """与内置**不同** → 抛 `ConfigError` 并指明迁移目标；错误消息**不回显正文**。"""
    from ib.config import document_from_json

    name = "freeark-expert"
    builtins = builtin_fallbacks_for([name])
    secret_body = "用户手写的、绝不能静默丢掉的一段提示词"
    with pytest.raises(ConfigError) as excinfo:
        document_from_json(
            "p1", _legacy_doc_text(name=name, fallback=secret_body), builtin_fallbacks=builtins
        )
    message = str(excinfo.value)
    assert name in message
    assert "fallback.md" in message, "必须指明迁移目标"
    assert secret_body not in message, "错误消息不得回显提示词正文（IFC-IB-348 纪律）"
    # 只报长度，便于运维核对是哪一处
    assert str(len(secret_body)) in message


def test_TC_UNIT_R17_legacy_key_without_injected_map_is_ignored():
    """未注入内置映射（2 参调用方）→ 一律忽略：向后兼容既有调用点，不制造假失败。"""
    from ib.config import document_from_json

    doc = document_from_json(
        "p1", _legacy_doc_text(name="freeark-expert", fallback="任意文本")
    )
    assert [e.name for e in doc.experts] == ["freeark-expert"]


def test_TC_UNIT_R17_unregistered_expert_legacy_key_is_ignored():
    """映射里查不到该专家（空映射）→ 忽略：无从判定「是否等价」，故不误杀。"""
    from ib.config import document_from_json

    doc = document_from_json(
        "p1", _legacy_doc_text(name="幽灵", fallback="x"), builtin_fallbacks={}
    )
    assert [e.name for e in doc.experts] == ["幽灵"]


# --------------------------------------------------------------------------- #
# 5 · 与运行期配置源无关的守卫：`offline_raw` 只用于保证本文件不触碰真实配置
# --------------------------------------------------------------------------- #


def test_TC_UNIT_R17_offline_raw_has_no_definition_doc_path():
    """守卫：本文件全程走内存定义文档，不得依赖任何真实定义文档路径。"""
    raw = offline_raw()
    assert "IB_DEFINITION_DOC_PATH" not in json.dumps(raw)
    assert raw["offline_mode"] is True
