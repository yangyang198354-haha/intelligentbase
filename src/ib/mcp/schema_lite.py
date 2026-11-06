# MOD-R29-02 / implements IFC-R29-014, IFC-R29-015 / depends MOD-R29-01
"""有界 JSON Schema 子集：内联本地 `$ref`、入参预检、LLM 可见 schema 投影（纯函数，无网络）。

规范要求（`[WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/index.md，2026-11-05]`）：
默认方言 2020-12；**不得**自动解引用网络 `$ref`；组合关键字须有资源上限。
本校验只是**预检**，权威校验在 Server 侧。
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import AbstractSet, Any, Mapping

__all__ = [
    "SchemaUnsupportedError",
    "SchemaViolation",
    "inline_local_refs",
    "validate_args",
    "project_llm_schema",
    "x_mcp_header_violation",
    "MAX_NODES",
]

MAX_NODES = 5000
_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")  # RFC 7230 token
_HEADER_TYPES = ("integer", "string", "boolean")


class SchemaUnsupportedError(ValueError):
    """schema 无法内联 / 递归 / 体积或深度超限 / 含网络 `$ref`。"""


@dataclass(frozen=True, slots=True)
class SchemaViolation:
    path: str
    code: str  # type|required|enum|const|range|length|additional|composition|depth


# --------------------------------------------------------------------------- #
# $ref 内联
# --------------------------------------------------------------------------- #


def _resolve_pointer(root: Mapping[str, Any], ref: str) -> Any:
    if ref == "#":
        return root
    if not ref.startswith("#/"):
        raise SchemaUnsupportedError("non_local_ref")
    node: Any = root
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, Mapping) and key in node:
            node = node[key]
        elif isinstance(node, list) and key.isdigit() and int(key) < len(node):
            node = node[int(key)]
        else:
            raise SchemaUnsupportedError("ref_unresolved")
    return node


def inline_local_refs(schema: Mapping[str, Any], *, max_depth: int, max_bytes: int) -> dict[str, Any]:
    """把本地 `$ref` 内联展开；网络 `$ref` / 递归 / 超深 / 超大 ⇒ SchemaUnsupportedError。"""
    if not isinstance(schema, Mapping):
        raise SchemaUnsupportedError("not_object")
    counter = {"n": 0}

    def walk(node: Any, depth: int, stack: tuple[str, ...]) -> Any:
        counter["n"] += 1
        if counter["n"] > MAX_NODES:
            raise SchemaUnsupportedError("too_many_nodes")
        if depth > max_depth:
            raise SchemaUnsupportedError("too_deep")
        if isinstance(node, Mapping):
            ref = node.get("$ref")
            if isinstance(ref, str):
                if not ref.startswith("#"):
                    raise SchemaUnsupportedError("non_local_ref")
                if ref in stack:
                    raise SchemaUnsupportedError("recursive_ref")
                target = _resolve_pointer(schema, ref)
                merged = walk(target, depth + 1, stack + (ref,))
                extra = {k: v for k, v in node.items() if k != "$ref"}
                if extra and isinstance(merged, dict):
                    merged = {**merged, **{k: walk(v, depth + 1, stack) for k, v in extra.items()}}
                return merged
            return {str(k): walk(v, depth + 1, stack) for k, v in node.items() if k not in ("$defs", "definitions") or depth > 0}
        if isinstance(node, list):
            return [walk(v, depth + 1, stack) for v in node]
        return node

    out = walk(schema, 0, ())
    try:
        size = len(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        raise SchemaUnsupportedError("not_json") from None
    if size > max_bytes:
        raise SchemaUnsupportedError("too_large")
    return out  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# 入参预检
# --------------------------------------------------------------------------- #


def _is_type(value: Any, t: str) -> bool:
    if t == "string":
        return isinstance(value, str)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "integer":
        return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer())
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "object":
        return isinstance(value, Mapping)
    if t == "array":
        return isinstance(value, (list, tuple))
    if t == "null":
        return value is None
    return True  # 未知 type 名：不据此拒绝（子集）


def _check(schema: Any, value: Any, path: str, depth: int, max_depth: int, out: list[SchemaViolation]) -> None:
    if len(out) >= 50:
        return
    if depth > max_depth:
        out.append(SchemaViolation(path, "depth"))
        return
    if not isinstance(schema, Mapping):
        return  # true / 非映射 schema：不约束
    if "const" in schema and value != schema["const"]:
        out.append(SchemaViolation(path, "const"))
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        out.append(SchemaViolation(path, "enum"))
    t = schema.get("type")
    if isinstance(t, str):
        types: tuple[str, ...] = (t,)
    elif isinstance(t, list):
        types = tuple(x for x in t if isinstance(x, str))
    else:
        types = ()
    if types and not any(_is_type(value, x) for x in types):
        out.append(SchemaViolation(path, "type"))
        return
    # 组合关键字（有界：不展开超出 depth 的递归）
    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        for i, sub in enumerate(all_of[:20]):
            _check(sub, value, path, depth + 1, max_depth, out)
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        ok = False
        for sub in any_of[:20]:
            tmp: list[SchemaViolation] = []
            _check(sub, value, path, depth + 1, max_depth, tmp)
            if not tmp:
                ok = True
                break
        if not ok:
            out.append(SchemaViolation(path, "composition"))
    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and one_of:
        matched = 0
        for sub in one_of[:20]:
            tmp = []
            _check(sub, value, path, depth + 1, max_depth, tmp)
            if not tmp:
                matched += 1
        if matched != 1:
            out.append(SchemaViolation(path, "composition"))
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        lo, hi = schema.get("minimum"), schema.get("maximum")
        if isinstance(lo, (int, float)) and not isinstance(lo, bool) and value < lo:
            out.append(SchemaViolation(path, "range"))
        if isinstance(hi, (int, float)) and not isinstance(hi, bool) and value > hi:
            out.append(SchemaViolation(path, "range"))
        elo, ehi = schema.get("exclusiveMinimum"), schema.get("exclusiveMaximum")
        if isinstance(elo, (int, float)) and not isinstance(elo, bool) and value <= elo:
            out.append(SchemaViolation(path, "range"))
        if isinstance(ehi, (int, float)) and not isinstance(ehi, bool) and value >= ehi:
            out.append(SchemaViolation(path, "range"))
    if isinstance(value, str):  # pattern 被有意忽略（避免 ReDoS）
        mn, mx = schema.get("minLength"), schema.get("maxLength")
        if isinstance(mn, int) and not isinstance(mn, bool) and len(value) < mn:
            out.append(SchemaViolation(path, "length"))
        if isinstance(mx, int) and not isinstance(mx, bool) and len(value) > mx:
            out.append(SchemaViolation(path, "length"))
    if isinstance(value, (list, tuple)):
        mn, mx = schema.get("minItems"), schema.get("maxItems")
        if isinstance(mn, int) and not isinstance(mn, bool) and len(value) < mn:
            out.append(SchemaViolation(path, "length"))
        if isinstance(mx, int) and not isinstance(mx, bool) and len(value) > mx:
            out.append(SchemaViolation(path, "length"))
        items = schema.get("items")
        if isinstance(items, Mapping):
            for i, v in enumerate(list(value)[:1000]):
                _check(items, v, f"{path}[{i}]", depth + 1, max_depth, out)
    if isinstance(value, Mapping):
        props = schema.get("properties")
        props = props if isinstance(props, Mapping) else {}
        req = schema.get("required")
        if isinstance(req, list):
            for r in req:
                if isinstance(r, str) and r not in value:
                    out.append(SchemaViolation(f"{path}.{r}", "required"))
        for k, v in value.items():
            if k in props:
                _check(props[k], v, f"{path}.{k}", depth + 1, max_depth, out)
            else:
                ap = schema.get("additionalProperties")
                if ap is False:
                    out.append(SchemaViolation(f"{path}.{k}", "additional"))
                elif isinstance(ap, Mapping):
                    _check(ap, v, f"{path}.{k}", depth + 1, max_depth, out)


def validate_args(schema: Mapping[str, Any], args: Mapping[str, Any], *, max_depth: int) -> tuple[SchemaViolation, ...]:
    """有界子集预检；忽略 pattern；永不解引用网络 `$ref`；无异常外泄。"""
    try:
        flat = inline_local_refs(schema, max_depth=max(2, int(max_depth)), max_bytes=1_048_576)
    except SchemaUnsupportedError:
        return (SchemaViolation("$", "composition"),)
    except Exception:  # noqa: BLE001
        return (SchemaViolation("$", "composition"),)
    out: list[SchemaViolation] = []
    try:
        _check(flat, args, "$", 0, int(max_depth) + 2, out)
    except RecursionError:
        out.append(SchemaViolation("$", "depth"))
    except Exception:  # noqa: BLE001
        out.append(SchemaViolation("$", "composition"))
    return tuple(out)


# --------------------------------------------------------------------------- #
# LLM 可见 schema 投影
# --------------------------------------------------------------------------- #


def _sanitize(text: str, max_chars: int) -> str:
    from ib.webtools.gate import sanitize_untrusted

    return sanitize_untrusted(text, max_chars=max_chars)


def _project(node: Any, desc_max: int) -> Any:
    if isinstance(node, Mapping):
        out: dict[str, Any] = {}
        for k, v in node.items():
            if k in ("x-mcp-header", "$schema", "title", "$id", "$comment"):
                continue
            if k == "description" and isinstance(v, str):
                out[k] = _sanitize(v, desc_max)
            elif k == "properties" and isinstance(v, Mapping):
                out[k] = {str(pk): _project(pv, desc_max) for pk, pv in v.items()}
            else:
                out[k] = _project(v, desc_max)
        return out
    if isinstance(node, list):
        return [_project(v, desc_max) for v in node]
    return node


def project_llm_schema(
    schema: Mapping[str, Any],
    *,
    hidden: AbstractSet[str],
    fixed: AbstractSet[str],
    desc_max: int = 300,
) -> dict[str, Any]:
    """IFC-R29-015：内联本地 ref → 移除屏蔽/固定属性及 required 项 → 净化描述 → 去 x-mcp-header/$schema/title。"""
    flat = inline_local_refs(schema, max_depth=16, max_bytes=1_048_576)
    out = _project(copy.deepcopy(flat), desc_max)
    out["type"] = "object"
    drop = set(hidden) | set(fixed)
    props = out.get("properties")
    if isinstance(props, dict):
        for name in list(props):
            if name in drop:
                del props[name]
    else:
        out["properties"] = {}
    req = out.get("required")
    if isinstance(req, list):
        kept = [r for r in req if isinstance(r, str) and r not in drop]
        if kept:
            out["required"] = kept
        else:
            out.pop("required", None)
    return out


# --------------------------------------------------------------------------- #
# x-mcp-header 标注合规（供 rules.check_discovered_tool 与 wire 共用）
# --------------------------------------------------------------------------- #


def _find_header_annotations(node: Any, path: tuple[str, ...], found: list[tuple[tuple[str, ...], Any]]) -> None:
    if isinstance(node, Mapping):
        for k, v in node.items():
            if k == "x-mcp-header":
                found.append((path, v))
            else:
                _find_header_annotations(v, path + (str(k),), found)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _find_header_annotations(v, path + (str(i),), found)


def x_mcp_header_violation(input_schema: Mapping[str, Any]) -> str | None:
    """`x-mcp-header` 约束：非空 token、全局唯一（大小写不敏感）、仅 integer/string/boolean、静态可达
    （只能直接标在根 `properties.<name>` 上）。违规返回原因码；合规 None。
    [WEB: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http.md，2026-11-05]"""
    found: list[tuple[tuple[str, ...], Any]] = []
    try:
        _find_header_annotations(input_schema, (), found)
    except RecursionError:
        return "too_deep"
    if not found:
        return None
    seen: set[str] = set()
    props = input_schema.get("properties") if isinstance(input_schema, Mapping) else None
    for path, value in found:
        if not (len(path) == 2 and path[0] == "properties" and isinstance(props, Mapping)):
            return "not_statically_reachable"
        if not isinstance(value, str) or not value or not _TOKEN_RE.match(value):
            return "name_not_token"
        key = value.lower()
        if key in seen:
            return "duplicate"
        seen.add(key)
        prop = props.get(path[1])
        t = prop.get("type") if isinstance(prop, Mapping) else None
        if t not in _HEADER_TYPES:
            return "type_not_allowed"
    return None
