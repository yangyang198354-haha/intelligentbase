"""
@module MOD-IB-17
@implements IFC-IB-181 register_tool / 182 build_capability_digest / 183 bind_scope
            IFC-IB-350（REV-16-2）build_authorized_tools / validate_grants
@depends MOD-IB-01, MOD-IB-15, MOD-IB-16
@author software-developer

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

import functools
from typing import Any, Callable, Sequence

from ib.core import (
    BoundTool,
    RegisteredTool,
    Scope,
    ToolGrantSpec,
    ToolParamSpec,
    ToolParamValidationError,
    ToolResult,
    ToolSpec,
    ValidationErrorItem,
)

__all__ = [
    "ToolRegistry",
    "build_capability_digest",
    "register_tool",
    "bind_scope",
    "default_registry",
    # REV-16-2（IFC-IB-350）
    "build_authorized_tools",
    "validate_grants",
    "derive_tool_param_specs",
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

    **REV-16-2**：`BoundTool` 输入不再一律透传 —— 若其可调用对象仍需要 `scope` / `retrieval`
    注入（`build_authorized_tools` 产出的「已注入参数、但尚未绑定 scope」的形态），则在此
    完成 scope 闭包注入；不需要注入的（调用方已自行绑定的无参工具）仍原样透传。
    """
    bound: list[BoundTool] = []
    for item in tools:
        if isinstance(item, BoundTool):
            if _needs_scope_binding(item.callable):
                bound.append(
                    BoundTool(
                        name=item.name,
                        description=item.description,
                        callable=_make_bound_callable(item, item.callable, scope, retrieval),
                        parameters=getattr(item, "parameters", None),
                    )
                )
            else:
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
                parameters=getattr(spec, "parameters", None),
            )
        )
    return bound


def _needs_scope_binding(fn: Any) -> bool:
    """可调用对象是否仍接受 `scope` / `retrieval` 关键字（据此决定是否需再绑一次）。"""
    import inspect

    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):  # pragma: no cover - 内建/极端包装
        return False
    return "scope" in params or "retrieval" in params


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


# --------------------------------------------------------------------------- #
# REV-16-2 工具授权与参数绑定（IFC-IB-350；ADR-30）
#
# 口径（用户裁决，OQ-IB-19 / DR-19）：**对既有工具集的授权勾选 + 工具参数可配**；
# **不含新增 / 自定义工具本体**。因此本模块**不提供**任何新增工具本体的入口 ——
# 工具本体仍只经 `register_tool`（IFC-IB-181，签名不变）登记。
#
# 参数命名约定：`<tool_name>.<param_name>` 的限定形式声明归属工具；不含 `.` 时视为
# 全局参数（无工具归属）。该约定使「未授权工具带参」可被确定性检出（IFC-IB-346）。
# --------------------------------------------------------------------------- #


def _owner_tool(param_name: str) -> str | None:
    if "." not in param_name:
        return None
    tool, _, param = param_name.partition(".")
    return tool if tool and param else None


def _bare_param(param_name: str) -> str:
    """`<tool>.<param>` 限定名 → 裸参数名（注入实现时用裸名，限定名仅用于声明归属）。"""
    return param_name.split(".", 1)[1] if "." in param_name else param_name


#: JSON Schema 类型 → `ToolParamSpec.type` 的确定性映射（成对维护，防规格与工具漂移）。
_JSON_TYPE_TO_PARAM: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


def derive_tool_param_specs(registry: ToolRegistry) -> tuple[ToolParamSpec, ...]:
    """由**唯一登记点**的工具声明派生可配置参数规格（IFC-IB-340；ADR-30）。**纯函数**。

    **只覆盖既有工具的既有参数**，不新增工具本体；规格集由工具 JSON Schema **派生**，
    故与工具声明**不可能漂移**（同 FND-GROUP-D-01 的收敛精神）。参数名用
    `<tool>.<param>` 限定形式声明归属工具（IFC-IB-346 据此判「未授权工具带参」）。
    """
    specs: list[ToolParamSpec] = []
    for item in registry.registered():
        schema = item.spec.parameters or {}
        props = schema.get("properties") if isinstance(schema, dict) else None
        if not isinstance(props, dict):
            continue
        for prop_name, prop in props.items():
            if not isinstance(prop, dict):
                continue
            param_type = _JSON_TYPE_TO_PARAM.get(prop.get("type"))
            if param_type is None:
                continue
            default = prop.get("default")
            minimum = prop.get("minimum")
            maximum = prop.get("maximum")
            enum = prop.get("enum")
            specs.append(
                ToolParamSpec(
                    name=f"{item.spec.name}.{prop_name}",
                    type=param_type,  # type: ignore[arg-type]
                    default="" if default is None else str(default),
                    minimum=float(minimum) if isinstance(minimum, (int, float)) else None,
                    maximum=float(maximum) if isinstance(maximum, (int, float)) else None,
                    choices=tuple(str(c) for c in enum) if isinstance(enum, list) else None,
                )
            )
    return tuple(specs)


def _coerce(spec: ToolParamSpec, raw: str) -> Any:
    """按声明类型把字符串取值转成 Python 值（校验已由 `validate_tool_params` 前置）。"""
    if spec.type == "str":
        return raw
    if spec.type == "bool":
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if spec.type == "int":
        return int(float(raw))
    return float(raw)


def validate_grants(
    grants: tuple[ToolGrantSpec, ...],
    *,
    registry: ToolRegistry,
) -> tuple[ValidationErrorItem, ...]:
    """授权合法性校验（IFC-IB-350）。**纯函数**（无 I/O）。

    检出：**引用不存在的工具**（`tool_names` 未在注册表）/ **未登记工具带参**
    （参数名限定归属的工具不在注册表内）。**不提供**新增工具本体的校验路径。
    """
    errors: list[ValidationErrorItem] = []
    known = set(registry.names())
    for grant in grants:
        for tool in grant.tool_names:
            if tool not in known:
                errors.append(
                    ValidationErrorItem(
                        path=f"tool_grants[{grant.expert_name}].tool_names[{tool}]",
                        code="tool_grant_tool_unknown",
                        message=f"工具 '{tool}' 不在已知工具注册表内",
                    )
                )
        for pv in grant.param_values:
            owner = _owner_tool(pv.name)
            if owner is not None and owner not in known:
                errors.append(
                    ValidationErrorItem(
                        path=f"tool_grants[{grant.expert_name}].param_values[{pv.name}]",
                        code="tool_param_tool_unregistered",
                        message=f"参数 '{pv.name}' 归属的工具 '{owner}' 未登记（工具本体不提供运行期新增）",
                    )
                )
    return tuple(errors)


def build_authorized_tools(
    grants: tuple[ToolGrantSpec, ...],
    *,
    registry: ToolRegistry,
    specs: tuple[ToolParamSpec, ...] = (),
) -> list[BoundTool]:
    """按**授权勾选**绑定工具并注入**工具参数**（IFC-IB-350）。**最小授权不变**。

    产出顺序 = `grants` 顺序 × 各 `tool_names` 顺序（同名工具只绑定一次）。
    参数经 `param_values` **闭包注入**：实现以 `functools.partial(fn, **裸参名)` 承载，故
    配置值作为**默认值**绑定 —— 调用方（LLM 工具调用循环）显式给出的同名实参**优先**
    （不对抗运行期必需参数，如检索的 `query`），未被调用方给出时配置值生效。
    引用不存在的工具 / 参数未被任何 spec 声明 → 抛 `ToolParamValidationError`（fail-fast；
    先经 `validate_grants`）。

    **scope 绑定分工**：本函数只注入参数，**不**绑定 `scope`（构造期无 scope）；产出即为
    「未绑 scope 的 `BoundTool`」，由 `bind_scope`（IFC-IB-183）完成 scope 闭包注入 ——
    两段绑定语义分属两个契约，互不越界（ADR-09）。
    """
    spec_by_name = {s.name: s for s in specs}
    known = set(registry.names())
    bound: list[BoundTool] = []
    seen: set[str] = set()
    for grant in grants:
        authorized = set(grant.tool_names)
        params: dict[str, Any] = {}
        for pv in grant.param_values:
            owner = _owner_tool(pv.name)
            if owner is not None and owner not in authorized:
                raise ToolParamValidationError(
                    f"参数 '{pv.name}' 归属工具 '{owner}'，但该工具未授权给专家 '{grant.expert_name}'"
                )
            spec = spec_by_name.get(pv.name)
            if spec is None:
                raise ToolParamValidationError(
                    f"参数 '{pv.name}' 未被任何 ToolParamSpec 声明（拒绝装配）"
                )
            params[pv.name] = _coerce(spec, pv.value)
        for tool in grant.tool_names:
            if tool in seen:
                continue
            if tool not in known:
                raise ToolParamValidationError(f"工具 '{tool}' 不在已知工具注册表内（拒绝装配）")
            seen.add(tool)
            registered = registry.get(tool)
            assert registered is not None  # 由 `known` 保证
            bound.append(_wrap_with_params(registered, params))
    return bound


def _param_belongs(param_name: str, tool_spec: ToolSpec) -> bool:
    """判断参数是否归属某工具：限定名按前缀；裸名按该工具 JSON Schema 的 properties。"""
    owner = _owner_tool(param_name)
    if owner is not None:
        return owner == tool_spec.name
    schema = tool_spec.parameters or {}
    properties = schema.get("properties") if isinstance(schema, dict) else None
    return bool(isinstance(properties, dict) and param_name in properties)


def _wrap_with_params(registered: RegisteredTool, params: dict[str, Any]) -> BoundTool:
    """把工具参数闭包进调用，产出**未绑 scope** 的 `BoundTool`。

    参数以**裸参名**经 `functools.partial` 绑定 —— 于是：
      * 声明期用 `<tool>.<param>` 限定名判归属（`_param_belongs`，防同名参数跨工具误注入）；
      * 注入期用裸名（实现的关键字参数），且 partial 绑定的是**默认值**，
        调用方显式给出的同名实参优先（不对抗运行期必需参数）。
    """
    spec = registered.spec
    fn = registered.fn
    owned = {_bare_param(k): v for k, v in params.items() if _param_belongs(k, spec)}
    bound_fn: Callable[..., Any] = functools.partial(fn, **owned) if owned else fn
    return BoundTool(
        name=spec.name,
        description=spec.description,
        callable=bound_fn,
        parameters=getattr(spec, "parameters", None),
    )
