"""
@module MOD-IB-16
@implements IFC-IB-171 EXPERT_SPECS / 172 names / 173 keywords_map / 174 cn_map
            IFC-IB-175 fallback_prompts / 176 data_experts / 177 delegating_experts
            IFC-IB-178 default_expert / 179 get
            IFC-IB-349（REV-16-2 加成式）install_prompt_bundles / prompt_bundles / main_prompts
            IFC-IB-365（REV-17）—— **REV-20 整体退役**（代码内置提示词安全网删除；ADR-48 / ADR-50）
            IFC-IB-379（REV-19）ExpertRegistryView / 380 resolve_expert_registry /
            381 builtin_default_registry（+ builtin_expert_registry；**REV-20 口径修订**：
                二者同值 = 唯一 kb-agent 单例，三专家机制退役）
@depends MOD-IB-01
@author software-developer

专家注册表（module_design.md §3 MOD-IB-16；REQ-FUNC-IB-02；REQ-NFR-IB-01）。

**本模块只有数据与纯函数**：不 import langchain / langgraph / 任何适配器
（module_design 明列「外部依赖：无，framework-free」）。理由很具体 ——
路由（MOD-IB-18/19）需要在**离线单测**里被反复调用（AC-IB-15-03 要求纯逻辑可测），
若专家表间接拉进 langchain，路由的每次单测都要加载一个沉重的 LLM 依赖树。

## 为什么必须「单一真源」

历史上同一份专家元数据被复制到 5 个模块（路由关键词表、提示兜底表、前端中文标签、
委托清单、数据专家护栏表）。加一个专家要改 5 处，必然出现「路由认识它、提示不认识」
这类**半成品专家**（表现为路由选中后拿到空提示，回答质量莫名劣化）。本模块把
「专家有哪些、叫什么、关键词是什么、是否持数据工具、是否可委托、谁是默认」
收敛为**一处声明**，其余全部**派生**（`names()` / `keywords_map()` / `cn_map()` /
`fallback_prompts()` / `data_experts()` / `delegating_experts()` / `default_expert()`）。

## 顺序即契约

`EXPERT_SPECS` 的**列表顺序是全系统专家顺序**，所有派生视图保持该序。
这一点不是风格问题：`default_expert()` 的兜底分支取首个元素，前端的专家标签顺序、
路由并列命中的去重顺序都依赖它 —— 顺序变化会改变可观测输出，故视作契约的一部分。

## 可配置（REQ-FUNC-IB-02）

`install(specs)` 允许接入方在**装配期**整体替换注册表（基座默认给出一组可直接运行的
示例专家）。`install` 只允许在装配期调用一次，且会做唯一性校验 —— 允许运行期热改
会让「路由关键词」在请求中途变化，产生无法复现的路由结果。

## REV-19 语义澄清（ADR-43 / ADR-47；IFC-IB-381）

本模块零参访问器（`names()` / `keywords_map()` / `cn_map()` / `data_experts()` /
`delegating_experts()` / `default_expert()` / `get()` / `fallback_prompts()`）**号 / 名 /
签名一字未改**，但语义澄清为「**内置默认专家集**（代码内置**安全网**；**非项目真源**）」
（对齐 REV-17 对 `fallback_prompts` 的同款澄清）。**项目真源** = 每项目装配期派生的只读视图
`ExpertRegistryView`（IFC-IB-379，`resolve_expert_registry` 构造）；生产装配主路径一律消费
**本项目视图**，进程级 `EXPERT_SPECS` **退出生产装配主路径**（仅离线 / 未配置路径作兜底）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

from ib.core import DerivedView, ExpertPromptBundle, ExpertRegistryError, ExpertSpec

__all__ = [
    "EXPERT_SPECS",
    "names",
    "keywords_map",
    "cn_map",
    "fallback_prompts",
    "data_experts",
    "delegating_experts",
    "default_expert",
    "get",
    "install",
    "install_derived",
    "validate_specs",
    # REV-16-2（IFC-IB-349）
    "install_prompt_bundles",
    "prompt_bundles",
    "main_prompts",
    # REV-19（IFC-IB-379 ~ 381）
    "ExpertRegistryView",
    "resolve_expert_registry",
    "builtin_default_registry",
    "builtin_expert_registry",
    "BUILTIN_DEFAULT_KB_AGENT",
    # REV-20（ADR-48 / ADR-50）：
    #   * 原 REV-17（ADR-36）的 BUILTIN_FALLBACK_DEFAULT / BUILTIN_FALLBACKS /
    #     builtin_fallback_for / builtin_fallbacks_for **整体退役**（不在此导出）；
    #   * 原 REV-19 的 DEMO_EXPERT_NAMES **退役**（三专家机制取消）。
]

# --------------------------------------------------------------------------- #
# 默认专家表（**单一真源**）
# --------------------------------------------------------------------------- #

#: **内置默认 KB 检索 agent**（IFC-IB-381；REQ-FUNC-IB-52 / IB-57 / OQ-IB-33(a) / OQ-IB-46(b)）。
#:
#: **REV-20（ADR-50）起「默认三专家」机制整体退役** —— 原先的 `_DEFAULT_SPECS`
#: （`freeark-expert` / `inspection-expert` / `sanheng-knowledge`，ADR-31 的 FreeArk 严格对齐集）
#: **一并退役**（`builtin_expert_registry()` 不再返回它们、`DEMO_EXPERT_NAMES` 删除）。
#: 本单例是**唯一**内置专家：既是**新建项目的种子真源**，也是**未落盘 / 未配置项目的回落**。
#:
#: **`fallback_prompt` 字段已「去驱动化」**（REV-20 / ADR-48 决定 1+4）：定义文档早已不承载
#: 提示词文本（REV-17），代码内置提示词安全网（原 IFC-IB-365）**整体退役**后，本字段
#: **不再参与任何运行期提示词取值**，故留空串。提示词正文由**仓库 markdown 种子资产**
#: （`ib.config.kb_agent_seed_prompt`，IFC-IB-389）经**创建期落盘**（ADR-51）写入
#: `<root>/<project_id>/kb-agent/main.md`。
#:
#: **标签不得与 ADR-31 已退场的旧标签同字**（旧值见 `selfcheck.py` 的反向断言）：
#: 仓库级 grep 归零由 `test_TC_UNIT_122_repo_grep_zero_old_slugs_and_labels` 把关。
BUILTIN_DEFAULT_KB_AGENT: ExpertSpec = ExpertSpec(
    name="kb-agent",
    cn_label="知识库助手",
    keywords=("知识库", "资料", "文档", "检索", "问答", "知识", "查资料"),
    is_data_expert=True,
    fallback_prompt="",
    is_delegating=False,
    is_default=True,
)

#: 当前生效的注册表（`install()` 可整体替换）。
#: **REV-20（ADR-50）**：初始值 = **唯一**内置单例（三专家退役；未落盘项目回落 = 本单例）。
EXPERT_SPECS: list[ExpertSpec] = [BUILTIN_DEFAULT_KB_AGENT]

#: 派生索引（`install()` / `install_derived()` 时重建）。
_BY_NAME: dict[str, ExpertSpec] = {spec.name: spec for spec in EXPERT_SPECS}

#: 是否已被接入方显式 `install()`（用于「装配期一次」的校验）。
_installed = False

#: **REV-16-2 提示词分层派生注册表**（IFC-IB-349）：装配期由两域合并注入的只读视图。
_PROMPT_BUNDLES: dict[str, ExpertPromptBundle] = {}

# --------------------------------------------------------------------------- #
# REV-20（ADR-48）：**代码内置提示词安全网已整体退役**
#
# 原 REV-17 / ADR-36 的代码安全网（`_BUILTIN_FALLBACK_PROMPTS` /
# `BUILTIN_FALLBACK_DEFAULT` 及其派生访问器）**整体删除**。理由与后果见 ADR-48：
#   * 提示词文本的**唯一可写载体** = 项目提示词目录（`main.md` / `fallback.md`）；
#   * 「生效系统提示词恒非空」**不再**由代码常量保证，改由**创建期落盘**（ADR-51 / IFC-IB-390）
#     + **装配期 fail-closed**（`prompt_missing`，`ib.config.validate_prompt_directory`）保证；
#   * 因 `ib.config` 侧不再需要「全名域内置兜底映射」，本模块**不再导出**任何兜底常量
#     （原 IFC-IB-365 整体退役）。
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# 校验与装配
# --------------------------------------------------------------------------- #


def validate_specs(specs: Sequence[ExpertSpec]) -> None:
    """校验注册表的**结构性约束**，不合法即 `ValueError`（启动期快速失败）。

    约束（每条都对应一个真实的故障模式）：
      1. 非空 —— 空注册表会让路由必然落到「无专家」，问答退化成无系统提示的裸模型；
      2. 名字唯一且非空 —— 重名会让 `get()` 静默返回其一（另一个永远不可达）；
      3. **默认专家恰好一个** —— 零个则 OOD/零信号时无人应答（违反 REQ-FUNC-IB-19
         「任何一级失败都不得导致无人应答」）；多个则默认专家的选择依赖列表顺序这类
         隐式事实，会出现「改个顺序就换了默认专家」的诡异回归；
      4. 关键词非空且无重复项 —— 重复项会**虚高**关键词命中计数，使「唯一命中」判据失真。
    """
    if not specs:
        raise ValueError("专家注册表不得为空（否则路由必然无人应答）")
    seen: set[str] = set()
    defaults = 0
    for spec in specs:
        if not spec.name or not spec.name.strip():
            raise ValueError("专家 name 不得为空")
        if spec.name in seen:
            raise ValueError(f"专家 name 重复：{spec.name!r}（重名会让 get() 静默丢弃其一）")
        seen.add(spec.name)
        if not spec.keywords:
            raise ValueError(f"专家 {spec.name!r} 的 keywords 不得为空")
        if len(set(spec.keywords)) != len(spec.keywords):
            raise ValueError(f"专家 {spec.name!r} 的 keywords 含重复项（会虚高命中计数）")
        if spec.is_default:
            defaults += 1
    if defaults != 1:
        raise ValueError(f"必须恰好有一个默认专家（当前 {defaults} 个，见 REQ-FUNC-IB-19 兜底要求）")


def install(specs: Sequence[ExpertSpec]) -> None:
    """装配期整体替换注册表（REQ-FUNC-IB-02）。

    **只允许一次**：允许二次替换意味着运行期可热改路由关键词，同一句提问在前一刻与
    后一刻路由到不同专家，而日志里看不到任何「配置变了」的痕迹 —— 不可复现的路由结果
    是最难查的一类问题。接入方若有多个项目需要不同专家表，应装配多个应用实例。
    """
    global _installed
    if _installed:
        raise RuntimeError("专家注册表已装配，禁止二次 install()（避免运行期热改导致路由不可复现）")
    validate_specs(specs)
    global EXPERT_SPECS
    EXPERT_SPECS = list(specs)
    _BY_NAME.clear()
    _BY_NAME.update({spec.name: spec for spec in EXPERT_SPECS})
    _installed = True


def install_derived(specs: Sequence[ExpertSpec]) -> None:
    """**装配期派生注入**（R7，ADR-15）：由定义文档派生的专家表注入注册表。

    与 `install()` 的区别（**这是刻意的**）：
      * **幂等可重复**：组合根在每次装配（含测试的 `build_deps(force=True)` 重复装配）都应能
        注入最新派生结果，故**不**受 `_installed` 一次性护栏约束 —— 该护栏只约束接入方对
        `install()` 的显式替换，不约束「由单一真源派生」这一机械化路径。
      * **不改写真源**：本函数只替换**派生**注册表（`EXPERT_SPECS` / `_BY_NAME`），
        不触碰定义文档（定义文档是唯一真源，由 MOD-IB-02 / MOD-IB-23 持有）。

    结构性约束沿用 `validate_specs`（空表 / 重名 / 默认专家不唯一 → `ValueError` 快速失败）。
    **IFC-IB-171~179 的号 / 名 / 签名不变**（R7 只改数据来源，不改模块边界）。
    """
    validate_specs(specs)
    global EXPERT_SPECS
    EXPERT_SPECS = list(specs)
    _BY_NAME.clear()
    _BY_NAME.update({spec.name: spec for spec in EXPERT_SPECS})


# --------------------------------------------------------------------------- #
# 派生访问器（IFC-IB-172 ~ 179）
# --------------------------------------------------------------------------- #


def names() -> tuple[str, ...]:
    """全部专家 id（**顺序 = 注册表顺序**）。[IFC-IB-172]"""
    return tuple(spec.name for spec in EXPERT_SPECS)


def keywords_map() -> dict[str, tuple[str, ...]]:
    """专家 -> 关键词。[IFC-IB-173]"""
    return {spec.name: spec.keywords for spec in EXPERT_SPECS}


def cn_map() -> dict[str, str]:
    """专家 -> 面向用户的中文标签（仅用于推理折叠框，不进正式答复）。[IFC-IB-174]"""
    return {spec.name: spec.cn_label for spec in EXPERT_SPECS}


def fallback_prompts() -> dict[str, str]:
    """专家 -> 派生注册表 `ExpertSpec.fallback_prompt` 字段的只读投影。[IFC-IB-175]

    **REV-20（ADR-48 决定 1）语义澄清**：该字段已**去驱动化** —— 代码内置提示词安全网
    （原 `builtin_fallback_for()`，真源 `_DEFAULT_SPECS`）**整体删除**后，本视图取自
    `EXPERT_SPECS`，其 `fallback_prompt` **恒为空串**（装配期 `_inject_derived_experts`
    显式置空）。**本视图不再参与任何运行期提示词取值** —— 生效提示词来自项目提示词目录
    （`main.md` / `fallback.md`），两层皆缺即装配期 `prompt_missing` fail-closed。
    """
    return {spec.name: spec.fallback_prompt for spec in EXPERT_SPECS}


# --------------------------------------------------------------------------- #
# REV-20（ADR-48）退役说明：原 `builtin_fallback_for` / `builtin_fallbacks_for` /
# `_BuiltinFallbackMap` / `BUILTIN_FALLBACKS` 已**整体删除**（见上方退役说明段）。
# 「生效提示词恒非空」现由创建期落盘 + 装配期 fail-closed 保证。
# --------------------------------------------------------------------------- #


def data_experts() -> tuple[str, ...]:
    """持有数据工具的专家（护栏：数据类问题不可落到无工具专家，否则必然胡编）。[IFC-IB-176]"""
    return tuple(spec.name for spec in EXPERT_SPECS if spec.is_data_expert)


def delegating_experts() -> tuple[str, ...]:
    """可子委托同侪的专家。[IFC-IB-177]

    **REV-12-2（G2）落地**：本派生视图与 `is_delegating` 不再是死字段 —— 编排层
    （MOD-IB-22 `Orchestrator._expand_plan`）在计划展开时**消费**本集合：仅当路由命中的
    专家属于本集合，才允许把手上的问题**单跳转交**给同侪（受 `max_expert_steps` /
    `MAX_EXPERT_STEPS` 步数上限约束，且**保留**不通交时的常规作答路径）。
    本函数仍是**纯数据派生**，不含任何转交判定逻辑（转交时机与目标由编排层决定）。
    """
    return tuple(spec.name for spec in EXPERT_SPECS if spec.is_delegating)


def default_expert() -> str:
    """默认专家（零信号兜底）。[IFC-IB-178]

    `validate_specs` 已保证全系统恰好一个 `is_default`，故这里的回落分支在正常装配下
    不可达 —— 保留它是为了「有人绕过 `install()` 直接改 `EXPERT_SPECS`」时不至于抛异常。
    """
    for spec in EXPERT_SPECS:
        if spec.is_default:
            return spec.name
    return EXPERT_SPECS[0].name  # pragma: no cover - 见 docstring


def get(name: str) -> ExpertSpec | None:
    """按名取专家；不存在返回 `None`（**不抛异常** —— 路由容错需要「优雅未命中」）。[IFC-IB-179]"""
    return _BY_NAME.get(name)


# --------------------------------------------------------------------------- #
# REV-16-2 提示词分层派生注册表（IFC-IB-349，**加成式扩展**）
#
# 目标：为上层（提示组装 / 前端可观测）提供「主 / 兜底 / 生效」三态提示词，而**不改变**
# IFC-IB-171~179 的号 / 名 / 签名。其中 `fallback_prompts()`（IFC-IB-175）语义**不变** ——
# 其仍返回**兜底层**（非空）。
#
# 本注册表持有的是**由两域在装配期合并派生并注入**的只读结果（ADR-15-R1）：
# 结构与配置域（定义文档）+ 提示词域（独立 markdown 目录）。禁止运行期热改（ADR-32）。
# --------------------------------------------------------------------------- #


def install_prompt_bundles(bundles: "dict[str, ExpertPromptBundle] | object") -> None:
    """装配期注入提示词分层派生结果（IFC-IB-349）。**幂等可重复**（同 `install_derived`）。

    `bundles` 可为 `dict[str, ExpertPromptBundle]` 或 `ExpertPromptBundle` 的可迭代。
    **只替换派生注册表**，不触碰任一真源；**不提供**运行期热重载入口（ADR-32 / C-IB-40）。
    """
    global _PROMPT_BUNDLES
    if isinstance(bundles, dict):
        items = list(bundles.values())
    else:
        items = list(bundles)  # type: ignore[arg-type]
    _PROMPT_BUNDLES = {b.expert_name: b for b in items}


def prompt_bundles() -> dict[str, ExpertPromptBundle]:
    """专家 `name` → 主 / 兜底 / 生效提示词（IFC-IB-349）。返回副本，防调用方改动注册表。"""
    return dict(_PROMPT_BUNDLES)


def main_prompts() -> dict[str, str | None]:
    """专家 `name` → 主提示词（IFC-IB-349；**可缺**，缺失为 `None`）。"""
    return {name: bundle.main_prompt for name, bundle in _PROMPT_BUNDLES.items()}


# --------------------------------------------------------------------------- #
# REV-19（ADR-43 / ADR-45 / ADR-47）：每项目专家注册表只读视图
#
# 为什么要把「专家集」做成**装配期派生的 frozen 视图**（而不是继续读进程级全局）：
# 进程级 `EXPERT_SPECS` 是**单例**且可被 rebind —— 多项目下「后装配项目覆盖先装配项目」
# 的专家集，是**跨项目泄漏**（REQ-FUNC-IB-49 / C-IB-44 / OOS-20 明令禁止）。把每个项目的
# 专家集在装配期解析为一个不可变值对象，随装配产物显式注入消费点，跨项目泄漏面**结构性消除**。
#
# C-IB-45 两条不变量成为**类型层事实**：`default_expert` 是**必填非空字段**（不可表达为
# `None`/缺失），故「默认专家恰好一个 / 永不无应答」不依赖任何运行期「校验放行」。
# --------------------------------------------------------------------------- #

# REV-20（ADR-50）：`DEMO_EXPERT_NAMES` **已退役** —— 「默认三专家」机制取消，
# `demo` 项目种子亦为唯一内置 kb-agent（`builtin_expert_registry()` 与
# `builtin_default_registry()` 同值）。


@dataclass(frozen=True, slots=True)
class ExpertRegistryView:
    """**每项目专家注册表只读视图**（IFC-IB-379，ADR-43）。

    * `project_id`：本视图所属项目（**唯一**上下文，无跨项目回退）；
    * `experts`：冻结后的专家元组（**顺序 = 注册表顺序**，即契约的一部分）；
    * `default_expert`：默认专家（**必填、非空、不可为 `None`**）；
    * `by_name`：按名索引（`__post_init__` 派生，只读 `MappingProxyType`）。

    **不变量（结构保证）**：`experts` 非空；`default_expert.name ∈ {e.name for e in experts}`。
    """

    project_id: str
    experts: tuple[ExpertSpec, ...]
    default_expert: ExpertSpec
    #: 派生索引（只读；不参与 `__init__` / `__eq__`，见 `__post_init__`）。
    by_name: Mapping[str, ExpertSpec] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "by_name", MappingProxyType({spec.name: spec for spec in self.experts})
        )

    # --- 派生访问器（**纯函数**，IFC-IB-379） --- #

    def names(self) -> tuple[str, ...]:
        """全部专家 id（**顺序 = 注册表顺序**）。"""
        return tuple(spec.name for spec in self.experts)

    def default_name(self) -> str:
        """默认专家 id（**恒有值** —— `default_expert` 必填非空，见 C-IB-45）。"""
        return self.default_expert.name

    def keywords_map(self) -> dict[str, tuple[str, ...]]:
        """专家 -> 关键词。"""
        return {spec.name: spec.keywords for spec in self.experts}

    def cn_map(self) -> dict[str, str]:
        """专家 -> 面向用户的中文标签。"""
        return {spec.name: spec.cn_label for spec in self.experts}

    def data_experts(self) -> tuple[str, ...]:
        """持有数据工具的专家。"""
        return tuple(spec.name for spec in self.experts if spec.is_data_expert)

    def delegating_experts(self) -> tuple[str, ...]:
        """可子委托同侪的专家。"""
        return tuple(spec.name for spec in self.experts if spec.is_delegating)

    def get(self, name: str) -> ExpertSpec | None:
        """按名取专家；不存在返回 `None`（**不抛异常**）。"""
        return self.by_name.get(name)


def _spec_from_input(entry: "object") -> ExpertSpec:
    """把定义文档派生条目（`ExpertSpecInput`）转成运行期 `ExpertSpec`。

    **REV-20（ADR-48 决定 1+4）**：定义文档不承载提示词文本、代码内置兜底已退役，
    故 `fallback_prompt` 恒为空串 —— 提示词正文由**创建期落盘**（ADR-51）+ **装配期
    fail-closed**（`prompt_missing`）保证，**不**在此处解析任何兜底。
    与 `ibweb.composition._inject_derived_experts` 的转换**同源**（单一真源）。
    """
    return ExpertSpec(
        name=entry.name,  # type: ignore[attr-defined]
        cn_label=entry.cn_label,  # type: ignore[attr-defined]
        keywords=tuple(entry.keywords),  # type: ignore[attr-defined]
        is_data_expert=entry.is_data_expert,  # type: ignore[attr-defined]
        fallback_prompt="",
        is_delegating=entry.is_delegating,  # type: ignore[attr-defined]
        is_default=entry.is_default,  # type: ignore[attr-defined]
    )


def resolve_expert_registry(project_id: str, *, view: DerivedView) -> ExpertRegistryView:
    """装配期由组合根调用，从派生视图构造该项目 `ExpertRegistryView`（IFC-IB-380）。

    **纯函数**（同输入同输出，无 I/O）；**fail-closed**（ADR-47 / REQ-NFR-IB-21）：
    专家集为空 / 默认专家缺失或非唯一 → 抛 `ExpertRegistryError(project_id, reason)`，
    **不回退**全局默认、**不回退**其他项目（与专家集硬隔离一致）。
    """
    experts = tuple(_spec_from_input(e) for e in view.experts)
    if not experts:
        raise ExpertRegistryError(project_id, "empty_expert_set")
    defaults = [spec for spec in experts if spec.is_default]
    if len(defaults) != 1:
        raise ExpertRegistryError(
            project_id, "default_expert_not_unique" if defaults else "default_expert_missing"
        )
    return ExpertRegistryView(project_id=project_id, experts=experts, default_expert=defaults[0])


#: **内置默认 KB 检索 agent**（IFC-IB-381）—— 定义见本文件上部「默认专家表」段
#: （REV-20 / ADR-50：三专家退役后本单例是**唯一**内置专家；`fallback_prompt` 已去驱动化）。


def builtin_default_registry() -> ExpertRegistryView:
    """**新建项目 / 未落盘项目的种子视图**（IFC-IB-381，REQ-FUNC-IB-52 / IB-57）。

    = **恰 1 个** 内置默认 KB 问答 agent（`is_default=True`，内置**不可删**）。
    `project_id` 取空串（本视图**与项目无关**，是「新建项目」的**模板**）。
    **REV-20（ADR-50）**：本视图**同时是「未落盘 / 未配置项目」的回落**。
    """
    return ExpertRegistryView(
        project_id="", experts=(BUILTIN_DEFAULT_KB_AGENT,), default_expert=BUILTIN_DEFAULT_KB_AGENT
    )


def builtin_expert_registry() -> ExpertRegistryView:
    """**内置默认专家集**视图（IFC-IB-381 语义；**REV-20 / ADR-50 口径修订**）。

    **REV-20 起与 `builtin_default_registry()` 同值**：三专家（`freeark-expert` /
    `inspection-expert` / `sanheng-knowledge`）机制**退役**，`DEMO_EXPERT_NAMES` 已删除，
    `demo` 项目种子**亦**为唯一 kb-agent（REQ-FUNC-IB-57 / OQ-IB-46(b) / OQ-IB-47(c)）。
    函数的**号 / 名 / 签名一字不变**（仅语义澄清）。
    """
    return builtin_default_registry()
