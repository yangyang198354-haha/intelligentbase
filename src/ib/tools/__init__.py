"""
@module MOD-IB-17
@implements IFC-IB-181 register_tool / 182 build_capability_digest / 183 bind_scope
@depends MOD-IB-01, MOD-IB-15, MOD-IB-16
@author sub_agent_software_developer

工具注册与能力摘要（module_design.md §3 MOD-IB-17；ADR-09；REQ-FUNC-IB-03/17/23）。

## 本模块承担的是**隔离语义**，不是「工具管理」

三件事在这里发生，且都围绕同一个目标 —— **让「检索」永远不可能越过 scope 的边界**：

1. **注册**（IFC-IB-181）：工具以「声明 + 实现」成对登记，声明（`ToolSpec`）是路由提示的
   唯一素材来源。
2. **能力摘要**（IFC-IB-182）：由注册表**纯函数派生**，注入路由提示，让 LLM 知道「有哪些
   能力可用」。**必须纯派生**：手写摘要会与真实工具集漂移，LLM 于是「知道一个不存在的工具」
   或「不知道一个存在的工具」，后者直接表现为「明明能查数据却回答不知道」。
   异常时返回 `""` 而非抛出 —— 摘要只是提示增强，不该阻断整个问答。
3. **构造期 scope 绑定**（IFC-IB-183）：把 `scope` 与 `RetrievalService` 闭包进工具，
   产出**无参**的 `BoundTool`。

## 为什么 scope 必须在**构造期**绑定（ADR-09 的核心）

若把 `scope` 作为工具参数暴露给 LLM，就等于把「访问哪个项目的数据」交给模型决定 ——
模型可以（因提示注入或被诱导）传一个别的 `project_id`，而工具层毫无察觉。构造期绑定后：

  * LLM **在结构上无法**表达「换一个项目检索」这件事（没有这个参数）；
  * `scope` 来自请求鉴权上下文（MOD-IB-23 解析，不信请求体），全链路单一来源；
  * 一次问答内的所有工具调用**必然**落在同一 scope 内，不存在中途漂移。

代价是「一次装配只能服务一个 scope」，所以绑定发生在**每请求**（而非进程启动期）——
这是把安全性放在装配便利性之前的自觉取舍。
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from ib.core import BoundTool, RegisteredTool, Scope, ToolResult, ToolSpec

__all__ = [
    "ToolRegistry",
    "build_capability_digest",
    "register_tool",
    "bind_scope",
    "default_registry",
]

#: 摘要中每个工具的简述长度上限（防止超长 description 挤占提示预算）。
_MAX_DESC_CHARS = 200


class ToolRegistry:
    """工具注册表（进程级，装配期填充）。

    * **同名覆盖**：便于灰度替换实现而不改动调用方（与解析器注册表同一约定）；
    * **保序**：`registered()` 保持注册顺序，摘要文本因此稳定 —— 摘要进入提示后，
      顺序变化会改变 LLM 的输入（进而可能改变输出），固定顺序让「同样的输入得到同样的回答」
      这一可调试性成立。
    """

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, spec: ToolSpec, fn: Callable[..., ToolResult]) -> None:
        """[IFC-IB-181] 登记工具。`spec.name` 是唯一键（同名覆盖）。"""
        if not spec.name or not spec.name.strip():
            raise ValueError("工具 name 不得为空")
        if not callable(fn):
            raise TypeError(f"工具 {spec.name!r} 的实现不可调用")
        self._tools[spec.name] = RegisteredTool(spec=spec, fn=fn)

    def registered(self) -> list[RegisteredTool]:
        """全部已登记工具（注册顺序）。"""
        return list(self._tools.values())

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def __len__(self) -> int:
        return len(self._tools)


#: 进程级默认注册表（组合根在装配期填充；离线单测可自建独立实例以避免相互影响）。
default_registry = ToolRegistry()


# --------------------------------------------------------------------------- #
# IFC-IB-181（模块级便捷入口）
# --------------------------------------------------------------------------- #


def register_tool(spec: ToolSpec, fn: Callable[..., ToolResult]) -> None:
    """[IFC-IB-181] 向默认注册表登记工具。"""
    default_registry.register(spec, fn)


# --------------------------------------------------------------------------- #
# IFC-IB-182 能力摘要（纯函数）
# --------------------------------------------------------------------------- #


def build_capability_digest(registry: ToolRegistry | None = None) -> str:
    """[IFC-IB-182] 由注册表派生能力摘要（**纯函数**；异常时返回 `""`）。

    输出形如：`- query_metrics: 查询设备实时指标（需要范围绑定）`，每行一个工具。

    **异常一律吞掉并返回空串**（契约明文要求）：能力摘要是提示的增强项，
    它的失败绝不该让用户拿不到回答 —— 没有摘要的问答只是「可能少用一次工具」，
    而抛异常则是「整轮问答失败」。两害相权，取前者。
    """
    try:
        reg = registry if registry is not None else default_registry
        lines: list[str] = []
        for item in reg.registered():
            desc = " ".join((item.spec.description or "").split())
            if len(desc) > _MAX_DESC_CHARS:
                desc = desc[: _MAX_DESC_CHARS - 1] + "…"
            suffix = "（需要范围绑定）" if item.spec.needs_scope else ""
            lines.append(f"- {item.spec.name}: {desc}{suffix}")
        return "\n".join(lines)
    except Exception:  # noqa: BLE001 - 契约要求：摘要失败不得上升为问答失败
        return ""


# --------------------------------------------------------------------------- #
# IFC-IB-183 构造期绑定
# --------------------------------------------------------------------------- #


def bind_scope(
    tools: Sequence[Any],
    scope: Scope,
    retrieval: Any,
) -> list[BoundTool]:
    """[IFC-IB-183] 把 `scope` 与检索服务**闭包**进工具，产出无参 `BoundTool`。

    两种入参形态都接受：
      * `RegisteredTool`（声明 + 实现）—— 实现以 `fn(**kwargs)` 调用，此处注入
        `scope` / `retrieval`（若实现接受这两个关键字）；
      * 已构造的 `BoundTool` —— 视为「调用方已完成绑定」，原样透传（便于上层组合）。

    **每个请求都要重新绑定**：闭包持有的是本请求的 scope，绝不可跨请求复用 —— 复用会把
    A 用户的 scope 泄漏给 B 用户的问答（跨项目数据泄露，最严重的一类缺陷）。
    """
    bound: list[BoundTool] = []
    for item in tools:
        if isinstance(item, BoundTool):
            bound.append(item)
            continue
        spec = getattr(item, "spec", None)
        fn = getattr(item, "fn", None)
        if spec is None or fn is None:
            raise TypeError(f"无法绑定的工具对象：{type(item).__name__}（应为 RegisteredTool 或 BoundTool）")
        bound.append(
            BoundTool(
                name=spec.name,
                description=spec.description,
                callable=_make_bound_callable(spec, fn, scope, retrieval),
            )
        )
    return bound


def _make_bound_callable(
    spec: ToolSpec, fn: Callable[..., Any], scope: Scope, retrieval: Any
) -> Callable[..., ToolResult]:
    """构造闭包：把 scope / retrieval 注入实现，**不暴露给调用方**。"""
    import inspect

    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):  # pragma: no cover - 内建/装饰器包装的极端情况
        params = {}

    accepts_scope = "scope" in params
    accepts_retrieval = "retrieval" in params
    accepts_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())

    def _bound(*args: Any, **kwargs: Any) -> ToolResult:
        """无参（或少量业务参数）调用形态。scope 由闭包提供，调用方无从指定。

        **必须覆盖而非 `setdefault`**：`setdefault` 会让 `_bound(scope=别的项目)`
        成功改写作用域，与本函数声明的「调用方无从指定」直接矛盾。一旦上层（或将来接入的
        LLM 工具调用循环）把模型输出的参数原样透传，这就是一条现成的跨项目读取路径。
        构造期绑定必须是**唯一**真源，故此处强制写入。
        """
        call_kwargs = dict(kwargs)
        if accepts_scope or accepts_kwargs:
            call_kwargs["scope"] = scope
        if accepts_retrieval or accepts_kwargs:
            call_kwargs["retrieval"] = retrieval
        result = fn(*args, **call_kwargs)
        if isinstance(result, ToolResult):
            return result
        # 宽松兼容：实现返回字符串时包成 ToolResult（避免因返回类型细节让整轮问答失败）
        return ToolResult(ok=True, content=str(result))

    _bound.__name__ = f"bound__{spec.name}"
    _bound.__doc__ = spec.description
    return _bound
