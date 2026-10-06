"""
@module MOD-IB-16
@implements IFC-IB-171 EXPERT_SPECS / 172 names / 173 keywords_map / 174 cn_map
            IFC-IB-175 fallback_prompts / 176 data_experts / 177 delegating_experts
            IFC-IB-178 default_expert / 179 get
            IFC-IB-349（REV-16-2 加成式）install_prompt_bundles / prompt_bundles / main_prompts
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
"""

from __future__ import annotations

from typing import Sequence

from ib.core import ExpertPromptBundle, ExpertSpec

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
]

# --------------------------------------------------------------------------- #
# 默认专家表（**单一真源**）
# --------------------------------------------------------------------------- #

#: 默认注册表（**REV-16-2 起与 FreeArk 严格对齐，含专家名**；ADR-31）。
#: 三个专家对应「系统管家 / 设备巡检 / 三恒知识」三类正交职责；顺序 = 全系统专家顺序
#: （freeark → inspection → sanheng），与 FreeArk `experts.py` 的 `EXPERT_SPECS` 逐位一致。
#:
#: **硬改名、无并存窗口**（[ARCH-ASSUMPTION-A10] P-3）：专家的 `name` 与 `cn_label` 已按
#: ADR-31 的 10 维对齐表整体改名（映射见 `docs/architecture_design.md` ADR-31），**不保留
#: 旧名的并存窗口**；升级后基于文件的定义文档须使用新专家名。
#:
#: `fallback_prompt` 是**提示文件缺失时的内置兜底**，不是主提示 —— 主提示由独立 markdown
#: 提示词目录（`ExpertPromptStore`，IFC-IB-339）按 `ExpertSpec.name` 加载，缺失时回落到这里，
#: 保证「提示缺失」不会退化成无系统提示（ADR-29）。
#:
#: **兜底提示词必须保留 grounding 护栏**（不得编造 / 说明局限 / 说明适用边界）—— 生产未配
#: `IB_EXPERT_PROMPT_DIR` 时，兜底层**就是生效系统提示词**（`build_prompt_stores` 走
#: `InMemoryExpertPromptStore`，无主提示可回落）。REV-16-2 改名时曾把三条护栏一并删去，
#: 等于**静默降低 groundedness**（DEFECT-R16-4-02），现已补回；后续任何改写都不得只留职责描述。
_DEFAULT_SPECS: list[ExpertSpec] = [
    ExpertSpec(
        name="freeark-expert",
        cn_label="系统管家",
        keywords=(
            "能耗",
            "用电",
            "用量",
            "电费",
            "看板",
            "节能",
            "kwh",
            "刷新",
            "采集",
            "下发",
            "触发",
            "设定",
            "状态",
            "查询",
            "参数",
            "温度",
            "湿度",
            "CO₂",
            "风量",
        ),
        is_data_expert=True,
        fallback_prompt=(
            "你是 FreeArk（自由方舟）系统管家，负责能耗看板、设备实时参数、"
            "设备参数确认式控制和业主人格偏好。故障巡检与三恒知识由专职专家处理。"
            "你无法取得所需数据时应直接说明，不得编造。"
        ),
        is_delegating=True,
        is_default=True,
    ),
    ExpertSpec(
        name="inspection-expert",
        cn_label="巡检诊断",
        keywords=("故障", "巡检", "plc", "离线", "在线", "传感器", "报警", "诊断", "修复"),
        is_data_expert=True,
        fallback_prompt=(
            "你是 FreeArk 巡检诊断专家，结合 PLC 状态与故障汇总定位设备问题。"
            "缺少实时参数或知识库资料时，可转交对应同侪专家获取支撑；"
            "无法取得支撑时，据现场信息给出可执行的排查步骤并说明局限。"
        ),
        is_delegating=True,
        is_default=False,
    ),
    ExpertSpec(
        name="sanheng-knowledge",
        cn_label="三恒知识",
        keywords=(
            "三恒",
            "恒温",
            "恒湿",
            "恒氧",
            "原理",
            "为什么",
            "接口",
            "型号",
            "说明书",
            "接线",
            "图纸",
            "尺寸",
            "热量表",
            "计量表",
            "主控箱",
            "手操器",
            "新风机",
            "modbus",
            "485",
            "毛细管",
        ),
        is_data_expert=False,
        fallback_prompt=(
            "你是三恒系统知识专家，依循三层知识源（RAG 检索 > 三恒行业知识 > 模型已有通用技术知识）"
            "回答原理性问题。需要实时数据支撑时，可委托系统管家获取数据；"
            "无法委托时据已有知识作答，并说明结论的适用边界。"
        ),
        is_delegating=True,
        is_default=False,
    ),
]

#: 当前生效的注册表（`install()` 可整体替换）。
EXPERT_SPECS: list[ExpertSpec] = list(_DEFAULT_SPECS)

#: 派生索引（`install()` 时重建）。
_BY_NAME: dict[str, ExpertSpec] = {spec.name: spec for spec in EXPERT_SPECS}

#: 是否已被接入方显式 `install()`（用于「装配期一次」的校验）。
_installed = False

#: **REV-16-2 提示词分层派生注册表**（IFC-IB-349）：装配期由两域合并注入的只读视图。
_PROMPT_BUNDLES: dict[str, ExpertPromptBundle] = {}


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
    """专家 -> 提示文件缺失时的内置兜底提示。[IFC-IB-175]"""
    return {spec.name: spec.fallback_prompt for spec in EXPERT_SPECS}


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
