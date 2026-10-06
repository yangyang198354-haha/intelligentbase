"""
@module MOD-IB-02
@implements IFC-IB-343 load_prompt_bundle / 344 save_prompt_layer / 345 load_prompt_directory
            + validate_prompt_directory / 346 validate_tool_params / 347 derive_prompt_layers
            / 348 键名登记（IB_EXPERT_PROMPT_DIR / IB_EXPERT_PROMPT_ENABLED）
@depends MOD-IB-01
@author software-developer

**独立提示词目录数据层**（REV-16-2，module_design.md §3 MOD-IB-02）。

真源边界（ADR-15-R1）：定义文档 = **结构与配置域**持久化态唯一真源；独立 markdown
提示词目录 = **提示词域**持久化态唯一真源；装配期**按域合并**（合并键 = 专家 `name`）。
两域**内容不得重叠**：定义文档不得承载主提示词正文，提示词目录不得承载专家元数据。
**越域写入即视为违规**（由装配期校验拒绝，IFC-IB-345）。

物理布局（[ARCH-ASSUMPTION-A10]，REV-16-3 已确认）::

    <root>/<project_id>/<expert_name>/main.md      # 主提示词（**可缺**）
    <root>/<project_id>/<expert_name>/fallback.md  # 兜底提示词（**不得缺**）

`<root>` 经 `IB_EXPERT_PROMPT_DIR` 注入；其值**只登记键名**，不进文档、不进日志。

纯函数不变式：`merge_prompt_layers` / `validate_prompt_directory` / `validate_tool_params` /
`load_prompt_bundle` 均为**纯函数**（同输入同输出、无副作用 —— `load_prompt_bundle` 除按
`ref.rel_path` 读取文件外无其它 I/O），可在离线无服务端环境下直接单测（REQ-NFR-IB-19）。

本模块**只允许 stdlib + `ib.core`**（framework-free 不变式）。
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from hashlib import sha256
from typing import Iterable

from ib.core import (
    ConfigError,
    DefinitionDocument,
    DependencyUnavailableError,
    DerivedView,
    ExpertPromptBundle,
    ExpertPromptDocumentRef,
    PromptDirectoryLayout,
    PromptNotFoundError,
    PromptSaveResult,
    ToolGrantSpec,
    ToolParamSpec,
    ValidationErrorItem,
)

from .definition import derive as _derive_document

__all__ = [
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

#: 独立提示词目录根路径（**仅登记键名，不含值**）。
EXPERT_PROMPT_DIR_KEY = "IB_EXPERT_PROMPT_DIR"
#: 提示词域开关（**仅登记键名，不含值**）。
EXPERT_PROMPT_ENABLED_KEY = "IB_EXPERT_PROMPT_ENABLED"

MAIN_FILENAME = "main.md"
FALLBACK_FILENAME = "fallback.md"
LAYER_FILENAMES: dict[str, str] = {"main": MAIN_FILENAME, "fallback": FALLBACK_FILENAME}


# --------------------------------------------------------------------------- #
# 键名开关与哈希
# --------------------------------------------------------------------------- #


def prompt_domain_enabled() -> bool:
    """`IB_EXPERT_PROMPT_ENABLED` 开关（默认**开** —— REQ-FUNC-IB-37/41 属 v1 范围）。

    只读键名对应的值用于行为判定，**绝不把值写入任何响应体 / 日志**（IFC-IB-348）。
    """
    raw = os.environ.get(EXPERT_PROMPT_ENABLED_KEY)
    if raw is None or str(raw).strip() == "":
        return True
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def prompt_content_hash(content: str) -> str:
    """提示词正文的语义哈希（纯函数；乐观并发判据，同 IFC-IB-289 精神）。"""
    return "sha256:" + sha256(content.encode("utf-8")).hexdigest()


def _err(path: str, code: str, message: str) -> ValidationErrorItem:
    return ValidationErrorItem(path=path, code=code, message=message)


def _entry_name(path: str) -> str:
    """取路径的条目名（`rel_path` 的父目录名），用于「命名不符」判定。"""
    normalized = path.replace("\\", "/").rstrip("/")
    parent = normalized.rsplit("/", 2)
    return parent[-2] if len(parent) >= 2 else ""


# --------------------------------------------------------------------------- #
# 跨域合并（IFC-IB-343；ADR-29）
# --------------------------------------------------------------------------- #


def merge_prompt_layers(
    expert_name: str,
    *,
    main_content: str | None,
    fallback_content: str | None,
    doc_fallback: str,
) -> ExpertPromptBundle:
    """**跨域合并纯函数**（IFC-IB-343 的合并内核；ADR-29）。

    优先级：`main_content`（提示词域主层）> `fallback_content`（提示词域兜底层）
    > `doc_fallback`（结构与配置域兜底字段）。

    **兜底恒非空**：三层皆空 → 抛 `PromptNotFoundError`（`effective_prompt` 永不空白）。
    """
    main = (main_content or "").strip()
    fallback_file = (fallback_content or "").strip()
    fallback_doc = (doc_fallback or "").strip()

    if main:
        return ExpertPromptBundle(
            expert_name=expert_name,
            main_prompt=main_content or "",
            fallback_prompt=fallback_file or fallback_doc,
            effective_prompt=main_content or "",
            resolved_from="main_file",
        )
    if fallback_file:
        return ExpertPromptBundle(
            expert_name=expert_name,
            main_prompt=None,
            fallback_prompt=fallback_content or "",
            effective_prompt=fallback_content or "",
            resolved_from="fallback_file",
        )
    if fallback_doc:
        return ExpertPromptBundle(
            expert_name=expert_name,
            main_prompt=None,
            fallback_prompt=doc_fallback,
            effective_prompt=doc_fallback,
            resolved_from="definition_doc_fallback",
        )
    raise PromptNotFoundError(
        f"专家 {expert_name!r} 无任何可用提示词（主 / 兜底 / 定义文档兜底皆空）",
        code="prompt_fallback_empty",
    )


def load_prompt_bundle(
    expert_name: str,
    *,
    refs: tuple[ExpertPromptDocumentRef, ...],
    doc_fallback: str,
) -> ExpertPromptBundle:
    """由提示词文件引用装载并合并分层提示词（IFC-IB-343；**纯函数 + 端口协作**）。

    **主存在 → 用主；主缺失 → 回退兜底**；**兜底为空即非法**（raise `PromptNotFoundError`）。
    `resolved_from` 记录取值来源（供界面可观测，IFC-IB-354）。

    内容经 `ref.rel_path` 读取（存在且非空方计入）；`ref.exists` 为 False 或缺文件时视为
    该层缺失。**不落盘、不反写任一真源**（ADR-15-R1）。
    """
    main_content: str | None = None
    fallback_content: str | None = None
    for ref in refs:
        if ref.expert_name != expert_name:
            continue
        if not ref.exists:
            continue
        text = _read_rel_path(ref.rel_path)
        if text is None:
            continue
        if ref.layer == "main":
            main_content = text
        elif ref.layer == "fallback":
            fallback_content = text
    return merge_prompt_layers(
        expert_name,
        main_content=main_content,
        fallback_content=fallback_content,
        doc_fallback=doc_fallback,
    )


def _read_rel_path(rel_path: str) -> str | None:
    """读取 `rel_path` 指向的文件；缺失 / 不可读返回 `None`（**静默视为缺失层**）。"""
    if not rel_path:
        return None
    try:
        if not os.path.isfile(rel_path):
            return None
        with open(rel_path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# 目录装载与完备性校验（IFC-IB-345）
# --------------------------------------------------------------------------- #


def load_prompt_directory(root: str, project_id: str) -> tuple[ExpertPromptDocumentRef, ...]:
    """装载独立提示词目录（IFC-IB-345）。**目录不可读 → 明确报错**（不静默返回空）。

    目录不存在视为「尚无提示词」→ 返回空元组（首次运行合法）；存在但非目录 / 不可读 → 抛
    `DependencyUnavailableError`（fail-closed，避免把「读不到」与「本就为空」混为一谈）。
    """
    if not root or not project_id:
        return ()
    base = os.path.join(root, project_id)
    if not os.path.exists(base):
        return ()
    if not os.path.isdir(base):
        raise DependencyUnavailableError(
            "提示词目录不可读（IB_EXPERT_PROMPT_DIR 指向的不是目录）",
            dependency="expert_prompt_dir",
        )
    refs: list[ExpertPromptDocumentRef] = []
    try:
        entries = sorted(os.listdir(base))
    except OSError as exc:
        raise DependencyUnavailableError(
            "提示词目录不可读（IB_EXPERT_PROMPT_DIR）", dependency="expert_prompt_dir"
        ) from exc
    for expert_name in entries:
        expert_dir = os.path.join(base, expert_name)
        if not os.path.isdir(expert_dir):
            continue
        for layer, filename in LAYER_FILENAMES.items():
            rel_path = os.path.join(expert_dir, filename)
            exists = os.path.isfile(rel_path)
            content_hash = ""
            if exists:
                text = _read_rel_path(rel_path)
                content_hash = prompt_content_hash(text) if text is not None else ""
            refs.append(
                ExpertPromptDocumentRef(
                    expert_name=expert_name,
                    layer=layer,  # type: ignore[arg-type]
                    rel_path=rel_path,
                    content_hash=content_hash,
                    exists=exists,
                )
            )
    return tuple(refs)


def validate_prompt_directory(
    refs: tuple[ExpertPromptDocumentRef, ...],
    *,
    doc: DefinitionDocument,
) -> tuple[ValidationErrorItem, ...]:
    """提示词目录完备性校验（IFC-IB-345）。**纯函数**。

    检出：**孤儿提示词文件**（目录有、文档未登记）/ **命名不符**（子目录名 != 专家 name）/
    **缺兜底**（`fallback.md` 缺失且文档 `fallback_prompt` 为空）。错误体只出
    `path` / `code` / `message`（**不回显提示词正文**）。
    """
    errors: list[ValidationErrorItem] = []
    known = {e.name for e in doc.experts}
    doc_fallback = {e.name: e.fallback_prompt for e in doc.experts}

    for ref in refs:
        parent = _entry_name(ref.rel_path)
        if parent and parent != ref.expert_name:
            errors.append(
                _err(
                    f"prompt_directory[{ref.expert_name}]",
                    "prompt_naming_mismatch",
                    f"提示词子目录名 '{parent}' 与专家 name '{ref.expert_name}' 不符"
                    f"（目录名必须 = 专家 name，[ARCH-ASSUMPTION-A10]）",
                )
            )
        if ref.expert_name not in known:
            errors.append(
                _err(
                    f"prompt_directory[{ref.expert_name}]",
                    "prompt_orphan_file",
                    f"提示词目录含未在定义文档登记的专家 '{ref.expert_name}'（孤儿文件，禁止越域）",
                )
            )

    # 缺兜底：某专家无可用 fallback 层（目录无 fallback.md）且文档兜底为空。
    for name in sorted(known):
        has_fallback_file = any(
            r.expert_name == name and r.layer == "fallback" and r.exists for r in refs
        )
        if not has_fallback_file and not (doc_fallback.get(name) or "").strip():
            errors.append(
                _err(
                    f"prompt_directory[{name}]",
                    "prompt_fallback_missing",
                    f"专家 '{name}' 缺兜底提示词（fallback.md 缺失且文档 fallback_prompt 为空）",
                )
            )
    return tuple(errors)


# --------------------------------------------------------------------------- #
# 工具参数校验（IFC-IB-346；ADR-30）
# --------------------------------------------------------------------------- #

_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _tool_of(param_name: str) -> str | None:
    """参数名的工具归属（`<tool>.<param>` 限定形式；不含 `.` 时返回 `None`）。"""
    if "." not in param_name:
        return None
    tool, _, param = param_name.partition(".")
    return tool if tool and param else None


def validate_tool_params(
    grants: tuple[ToolGrantSpec, ...],
    *,
    specs: tuple[ToolParamSpec, ...],
) -> tuple[ValidationErrorItem, ...]:
    """工具参数校验（IFC-IB-346）。**纯函数**；**不提供**新增工具本体的校验路径。

    检出：**越界**（< minimum / > maximum）/ **类型不符**（不满足 `type`）/ **未知参数**
    （spec 未声明）/ **choices 不匹配** / **未授权工具带参**（参数名以 `<tool>.` 限定且该
    工具不在该专家 `tool_names` 内）。错误体只出 `path` / `code` / `message`。
    """
    errors: list[ValidationErrorItem] = []
    spec_by_name = {s.name: s for s in specs}

    for grant in grants:
        authorized = set(grant.tool_names)
        for pv in grant.param_values:
            path = f"tool_grants[{grant.expert_name}].param_values[{pv.name}]"
            spec = spec_by_name.get(pv.name)
            if spec is None:
                errors.append(
                    _err(path, "tool_param_unknown", f"参数 '{pv.name}' 未被任何 ToolParamSpec 声明")
                )
                continue
            owner_tool = _tool_of(pv.name)
            if owner_tool is not None and owner_tool not in authorized:
                errors.append(
                    _err(
                        path,
                        "tool_param_unauthorized_tool",
                        f"参数 '{pv.name}' 归属工具 '{owner_tool}'，但该工具未授权给专家 "
                        f"'{grant.expert_name}'",
                    )
                )
                continue
            error = _check_param_value(path, spec, pv.value)
            if error is not None:
                errors.append(error)
    return tuple(errors)


def _check_param_value(path: str, spec: ToolParamSpec, raw: str) -> ValidationErrorItem | None:
    """单值校验：类型 → 枚举 → 上下界（顺序固定，保证回执稳定）。"""
    if spec.choices is not None and raw not in spec.choices:
        return _err(
            path,
            "tool_param_choice_invalid",
            f"参数 '{spec.name}' 取值 '{raw}' 不在枚举 {list(spec.choices)!r} 内",
        )
    if spec.type == "str":
        return None
    if spec.type == "bool":
        if raw.strip().lower() not in _BOOL_TRUE | _BOOL_FALSE:
            return _err(path, "tool_param_type_mismatch", f"参数 '{spec.name}' 需为 bool，收到 '{raw}'")
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _err(path, "tool_param_type_mismatch", f"参数 '{spec.name}' 需为 {spec.type}，收到 '{raw}'")
    if spec.type == "int" and value != int(value):
        return _err(path, "tool_param_type_mismatch", f"参数 '{spec.name}' 需为 int，收到 '{raw}'")
    if spec.minimum is not None and value < spec.minimum:
        return _err(
            path, "tool_param_out_of_range", f"参数 '{spec.name}' 低于下界 {spec.minimum}（收到 {raw}）"
        )
    if spec.maximum is not None and value > spec.maximum:
        return _err(
            path, "tool_param_out_of_range", f"参数 '{spec.name}' 高于上界 {spec.maximum}（收到 {raw}）"
        )
    return None


# --------------------------------------------------------------------------- #
# 跨域派生（IFC-IB-347）
# --------------------------------------------------------------------------- #


def with_prompt_bundles(
    view: DerivedView, bundles: Iterable[ExpertPromptBundle]
) -> DerivedView:
    """把提示词分层结果并入只读派生视图（**加成式扩展**，IFC-IB-347）。

    `Dataclasses.replace` 只替换 `prompt_bundles`，**不落盘、不可反写任一真源**（ADR-15-R1）。
    """
    return replace(view, prompt_bundles=tuple(bundles))


def derive_prompt_layers(
    doc: DefinitionDocument,
    prompt_refs: tuple[ExpertPromptDocumentRef, ...],
) -> DerivedView:
    """跨域合并派生（IFC-IB-347）。**纯函数**；**不落盘、不可反写任一真源**。

    定义文档专家 `name` ↔ 提示词目录子目录**按 name join**；产出 prompt bundle 并并入
    派生视图（`DerivedView.prompt_bundles`）。**不新增参数到既有 IFC-IB-291**
    （`derive` 签名文本不变，本函数为其合并扩展的**独立**入口）。
    """
    bundles = [
        load_prompt_bundle(e.name, refs=prompt_refs, doc_fallback=e.fallback_prompt)
        for e in doc.experts
    ]
    return with_prompt_bundles(_derive_document(doc), bundles)


# --------------------------------------------------------------------------- #
# 存储实现（端口 `ExpertPromptStore`，IFC-IB-339）
# --------------------------------------------------------------------------- #


def _assert_safe_expert_name(expert_name: str) -> None:
    """拒绝可能逃逸目录树的专家名（路径分隔符 / `..`）—— 防目录穿越。"""
    if (
        not expert_name
        or not expert_name.strip()
        or expert_name in {".", ".."}
        or "/" in expert_name
        or "\\" in expert_name
        or os.sep in expert_name
    ):
        raise ConfigError("专家 name 不合法（不得含路径分隔符）", key=EXPERT_PROMPT_DIR_KEY)


class FsExpertPromptStore:
    """**生产**提示词目录存储：本地 markdown 目录 + 原子替换 + 语义哈希乐观并发。

    * 构造即绑定一个项目（`<root>/<project_id>/`，一项目一目录树）；
    * `save_layer` 先写同目录临时文件 → `os.replace` **原子替换**；`expected_hash`
      不匹配 → `saved=False` 且**不落盘**（拒绝覆盖）；
    * 数据不出本机（无任何网络调用）；错误体**不回显正文 / 凭据**。
    """

    def __init__(self, root: str, project_id: str) -> None:
        self._root = root
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        return self._project_id

    def _expert_dir(self, expert_name: str) -> str:
        _assert_safe_expert_name(expert_name)
        return os.path.join(self._root, self._project_id, expert_name)

    def _layer_path(self, expert_name: str, layer: str) -> str:
        filename = LAYER_FILENAMES.get(layer)
        if filename is None:
            raise ConfigError(f"未知提示词层 {layer!r}（仅支持 main / fallback）", key=EXPERT_PROMPT_DIR_KEY)
        return os.path.join(self._expert_dir(expert_name), filename)

    def load_bundle(self, expert_name: str, *, doc_fallback: str) -> ExpertPromptBundle:
        return load_prompt_bundle(
            expert_name, refs=self._refs_for(expert_name), doc_fallback=doc_fallback
        )

    def _refs_for(self, expert_name: str) -> tuple[ExpertPromptDocumentRef, ...]:
        refs = []
        for layer, filename in LAYER_FILENAMES.items():
            rel_path = os.path.join(self._expert_dir(expert_name), filename)
            exists = os.path.isfile(rel_path)
            content_hash = ""
            if exists:
                with open(rel_path, encoding="utf-8") as fh:
                    content_hash = prompt_content_hash(fh.read())
            refs.append(
                ExpertPromptDocumentRef(
                    expert_name=expert_name,
                    layer=layer,  # type: ignore[arg-type]
                    rel_path=rel_path,
                    content_hash=content_hash,
                    exists=exists,
                )
            )
        return tuple(refs)

    def save_layer(
        self,
        expert_name: str,
        layer: str,
        content: str,
        *,
        expected_hash: str | None,
    ) -> PromptSaveResult:
        path = self._layer_path(expert_name, layer)
        current = ""
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                current = prompt_content_hash(fh.read())
        if layer == "fallback" and not (content or "").strip():
            return PromptSaveResult(
                saved=False,
                ref=ExpertPromptDocumentRef(expert_name, layer, path, current, os.path.isfile(path)),  # type: ignore[arg-type]
                content_hash=current,
                errors=(
                    _err(
                        f"prompt[{expert_name}].fallback",
                        "prompt_fallback_empty",
                        "兜底提示词不得为空（ADR-29：兜底恒非空）",
                    ),
                ),
            )
        if expected_hash is not None and expected_hash != current:
            return PromptSaveResult(
                saved=False,
                ref=ExpertPromptDocumentRef(expert_name, layer, path, current, os.path.isfile(path)),  # type: ignore[arg-type]
                content_hash=current,
                errors=(
                    _err(
                        f"prompt[{expert_name}].{layer}",
                        "prompt_content_hash_conflict",
                        "提示词已被他处修改（乐观并发冲突，拒绝覆盖）",
                    ),
                ),
            )
        self._atomic_write(path, content)
        new_hash = prompt_content_hash(content)
        return PromptSaveResult(
            saved=True,
            ref=ExpertPromptDocumentRef(expert_name, layer, path, new_hash, True),  # type: ignore[arg-type]
            content_hash=new_hash,
            errors=(),
        )

    def list_refs(self) -> tuple[ExpertPromptDocumentRef, ...]:
        return load_prompt_directory(self._root, self._project_id)

    def delete_layer(self, expert_name: str, layer: str) -> None:
        path = self._layer_path(expert_name, layer)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:  # pragma: no cover - 删除失败不改变主语义
                pass

    def layout(self) -> PromptDirectoryLayout:
        return PromptDirectoryLayout(
            root_key=EXPERT_PROMPT_DIR_KEY,
            file_pattern="<root>/<project_id>/<expert_name>/{main.md|fallback.md}",
            naming_rule="子目录名 = 专家 name（ADR-15-R1 合并键的物理实现）；main.md 可缺，fallback.md 不得缺",
        )

    def _atomic_write(self, path: str, content: str) -> None:
        directory = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".ib_prompt_", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)  # 原子替换（同目录内 rename）
        except BaseException:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            raise


class InMemoryExpertPromptStore:
    """进程内提示词存储（**离线 / 测试替身**；module_design.md §8）。

    同一合并 / 校验语义与生产实现一致：`save_layer` 同样实施兜底非空与乐观并发判据，
    使离线用例能覆盖真实分支（REQ-NFR-IB-19）。
    """

    def __init__(
        self,
        project_id: str,
        *,
        documents: "dict[str, dict[str, str]] | None" = None,
    ) -> None:
        #: `expert_name -> {layer: content}`
        self._docs: dict[str, dict[str, str]] = {
            name: dict(layers) for name, layers in (documents or {}).items()
        }
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        return self._project_id

    def load_bundle(self, expert_name: str, *, doc_fallback: str) -> ExpertPromptBundle:
        layers = self._docs.get(expert_name, {})
        return merge_prompt_layers(
            expert_name,
            main_content=layers.get("main"),
            fallback_content=layers.get("fallback"),
            doc_fallback=doc_fallback,
        )

    def save_layer(
        self,
        expert_name: str,
        layer: str,
        content: str,
        *,
        expected_hash: str | None,
    ) -> PromptSaveResult:
        _assert_safe_expert_name(expert_name)
        if layer not in LAYER_FILENAMES:
            raise ConfigError(f"未知提示词层 {layer!r}（仅支持 main / fallback）", key=EXPERT_PROMPT_DIR_KEY)
        layers = self._docs.setdefault(expert_name, {})
        current_text = layers.get(layer)
        current = prompt_content_hash(current_text) if current_text is not None else ""
        exists = current_text is not None
        ref = ExpertPromptDocumentRef(
            expert_name=expert_name,
            layer=layer,  # type: ignore[arg-type]
            rel_path=f"{expert_name}/{LAYER_FILENAMES[layer]}",
            content_hash=current,
            exists=exists,
        )
        if layer == "fallback" and not (content or "").strip():
            return PromptSaveResult(
                saved=False,
                ref=ref,
                content_hash=current,
                errors=(
                    _err(
                        f"prompt[{expert_name}].fallback",
                        "prompt_fallback_empty",
                        "兜底提示词不得为空（ADR-29：兜底恒非空）",
                    ),
                ),
            )
        if expected_hash is not None and expected_hash != current:
            return PromptSaveResult(
                saved=False,
                ref=ref,
                content_hash=current,
                errors=(
                    _err(
                        f"prompt[{expert_name}].{layer}",
                        "prompt_content_hash_conflict",
                        "提示词已被他处修改（乐观并发冲突，拒绝覆盖）",
                    ),
                ),
            )
        layers[layer] = content
        new_hash = prompt_content_hash(content)
        return PromptSaveResult(
            saved=True,
            ref=replace(ref, content_hash=new_hash, exists=True),
            content_hash=new_hash,
            errors=(),
        )

    def list_refs(self) -> tuple[ExpertPromptDocumentRef, ...]:
        refs: list[ExpertPromptDocumentRef] = []
        for expert_name in sorted(self._docs):
            for layer, filename in LAYER_FILENAMES.items():
                text = self._docs[expert_name].get(layer)
                refs.append(
                    ExpertPromptDocumentRef(
                        expert_name=expert_name,
                        layer=layer,  # type: ignore[arg-type]
                        rel_path=f"{expert_name}/{filename}",
                        content_hash=prompt_content_hash(text) if text is not None else "",
                        exists=text is not None,
                    )
                )
        return tuple(refs)

    def delete_layer(self, expert_name: str, layer: str) -> None:
        layers = self._docs.get(expert_name)
        if layers is not None:
            layers.pop(layer, None)

    def layout(self) -> PromptDirectoryLayout:
        return PromptDirectoryLayout(
            root_key=EXPERT_PROMPT_DIR_KEY,
            file_pattern="<root>/<project_id>/<expert_name>/{main.md|fallback.md}",
            naming_rule="子目录名 = 专家 name（ADR-15-R1 合并键的物理实现）；main.md 可缺，fallback.md 不得缺",
        )
