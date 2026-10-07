"""
@module MOD-IB-23
@implements IFC-IB-242~249 响应体字段契约（module_design §3 MOD-IB-23）
            IFC-IB-294/295（R7）定义文档读写字段契约
            IFC-IB-356（REV-16-4）`ConfigAuditEntry` 投影（字段名 / 结果码白名单）
            IFC-IB-361（REV-16-4）`StorageState` 投影（只出存储态）
@depends MOD-IB-01（领域类型）, MOD-IB-11/12/14（台账/Blob/重建类型）
@author software-developer

HTTP 出入参的类型边界（**唯一**允许把领域 dataclass 翻成 JSON 的地方）。

## 为什么字段必须**逐个写出来**，而不是自动展开 dataclass

本模块的字段表就是端点的对外契约。若用 `dataclasses.asdict(record)` 之类自动展开：

1. **新增领域字段会静默出现在响应里** —— 领域模型里加一个内部字段（如 `lease_owner`、
   `target_collection_version`），它就会自动泄漏到 API 上，且没有任何一条测试会失败。
   `lease_owner` 这类字段是**实现细节**，把它暴露出去等于把内部的租约/多 worker 机制
   变成对外承诺 —— 一旦有人依赖它，就再也不能改了。
2. **响应会随内部重构漂移** —— 前端契约需要的是「字段名与含义稳定」，而不是「与 dataclass 同构」。

因此这里坚持逐字段声明：**多写 10 行，换契约不被内部重构带跑**。

## `status` 用裸字符串而非枚举

`DocStatusLiteral` 是 Literal 类型，序列化时直接输出字符串值。前端只需按字符串比较；
若在此处转成枚举再转回字符串，只会多一层可能出错的转换。
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

__all__ = [
    "DocumentRecordSerializer",
    "DeleteReportSerializer",
    "RebuildJobSerializer",
    "RebuildProgressSerializer",
    "HealthStatusSerializer",
    "EgressDescriptorSerializer",
    "FileListEnvelopeSerializer",
    "RebuildProgressEnvelopeSerializer",
    # R7 定义文档（IFC-IB-294/295）
    "DefinitionDocumentSerializer",
    "DefinitionConfigInputSerializer",
    "SaveResultSerializer",
    "ValidationErrorItemSerializer",
    "definition_derived_summary",
    # REV-16-4 配置审计 / 存储态（IFC-IB-356 / 361）
    "ConfigAuditEntrySerializer",
    "StorageStateSerializer",
    # REV-18 项目注册表 / LLM Key（IFC-IB-372 / 374）
    "ProjectRegistryEntrySerializer",
    "LlmKeyStatusSerializer",
]


class _DataclassSerializer(serializers.Serializer):
    """把 frozen dataclass 按**显式字段表**读出为 dict。

    基类刻意保持极简：不提供 `create()` / `update()`（本层只做输出渲染，
    不承担领域对象的构造 —— 领域对象的构造有不变式（如 `Scope` 的 `kb_ids` 校验），
    把它交给反序列化只会绕过那些不变式）。
    """

    #: 子类必须覆盖：`字段名 -> 取值来源属性名`（同名字段可写 `None` 表示同名）。
    _fields: dict[str, str | None] = {}

    def to_representation(self, instance: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, attr in self._fields.items():
            out[name] = getattr(instance, attr or name, None)
        return out


class DocumentRecordSerializer(_DataclassSerializer):
    """`DocumentRecord` 的对外投影。

    **刻意不输出**：`lease_owner` / `lease_expires_at`（内部调度细节）、
    `blob_ref`（服务端存储定位，不应成为前端契约）、`target_collection_version`
    （重建期内部状态）。前端需要的是「这篇文档现在怎么样」，不是「它落在哪个集合里」。
    """

    _fields = {
        "doc_id": None,
        "kb_id": None,
        "doc_name": None,
        "ext": None,
        "size_bytes": None,
        "content_sha256": None,
        "status": None,
        "error_code": None,
        "chunk_count": None,
        "created_at": None,
        "updated_at": None,
    }


class DeleteReportSerializer(_DataclassSerializer):
    """`DeleteReport` 三字段**全量**输出。

    三个字段都是布尔/计数，前端可据此判断「是否真的清干净了」。若只回 `{"ok": true}`，
    排障时就无法区分「向量删了但原文件还在」（残留）与「都删干净了」。
    """

    _fields = {"vectors_deleted": None, "blob_deleted": None, "ledger_deleted": None}


class RebuildJobSerializer(_DataclassSerializer):
    """`RebuildJob`（枚举字符串直出）。"""

    _fields = {"job_id": None, "state": None}


class RebuildProgressSerializer(_DataclassSerializer):
    """`RebuildProgress`。`done=True` 才允许切换版本（AC-IB-16-04 的前置条件）。"""

    _fields = {"indexed": None, "failed": None, "pending": None, "done": None}


class RebuildProgressEnvelopeSerializer(_DataclassSerializer):
    """`GET /api/rebuild/{job_id}` 的响应体：进度 + 任务身份。"""

    _fields = {"job_id": None, "state": None, "indexed": None, "failed": None, "pending": None, "done": None}


class HealthStatusSerializer(_DataclassSerializer):
    """`HealthStatus`（`detail` 不得含凭据或正文 —— 由提供方保证，见 IFC-IB-010）。"""

    _fields = {"ok": None, "detail": None, "latency_ms": None}


class EgressDescriptorSerializer(_DataclassSerializer):
    """数据外发边界声明（AC-IB-12-05：外发必须可追溯）。"""

    _fields = {"remote": None, "endpoint_host": None, "data_categories": None}


class FileListEnvelopeSerializer(serializers.Serializer):
    """`GET /api/files` 的响应外壳：`{items: [...], total: int}`。

    `total` 是**过滤后的总数**（不是当前页长度）：分页控件的页数依赖它。
    """

    items = DocumentRecordSerializer(many=True)
    total = serializers.IntegerField()


# --------------------------------------------------------------------------- #
# R7 定义文档（IFC-IB-294 / 295；module_design §3 MOD-IB-23/24）
#
# 字段**逐个写出**（同本模块总纪律）：新增领域字段不得静默进/出响应。
# 反序列化只接受 `document` 整体 + 乐观并发 `expected_content_hash`；
# **不接受** `project_id`（归属恒取自服务端鉴权结论，不信请求体）。
# --------------------------------------------------------------------------- #


class _ExpertSpecInputSerializer(_DataclassSerializer):
    _fields = {
        "name": None,
        "cn_label": None,
        "keywords": None,
        "exemplars": None,
        "is_data_expert": None,
        # REV-17（ADR-36）：`fallback_prompt` 已移出定义文档 —— 提示词文本只由
        # 独立提示词目录（main.md / fallback.md）与代码内置安全网承载，定义文档回归纯结构配置。
        "is_delegating": None,
        "is_default": None,
    }


class _ConditionalEdgeSpecSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> dict[str, Any]:
        # `branch_map` 输出为 `[[branch_key, target_node], ...]`（**保序**，供界面判定可达性）。
        return {
            "from_node": instance.from_node,
            "branch_map": [[str(k), str(t)] for k, t in instance.branch_map],
        }


class _EdgeSpecSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> dict[str, Any]:
        # 普通边（无条件转移）：界面据此画出 `expert → gate → aggregate` 这条主干，
        # 缺了它这些节点会渲染成孤立方块。
        return {"from_node": instance.from_node, "to_node": instance.to_node}


class _RouteSpecInputSerializer(_DataclassSerializer):
    _fields = {"tau": None, "margin": None, "max_expert_steps": None, "default_expert": None}


class _OrchestrationSpecInputSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "nodes": list(instance.nodes),
            "conditional_edges": [
                _ConditionalEdgeSpecSerializer().to_representation(ce) for ce in instance.conditional_edges
            ],
            "edges": [_EdgeSpecSerializer().to_representation(e) for e in instance.edges],
        }


class _ToolGrantSpecSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> dict[str, Any]:
        # `param_values` 必须**逐值**输出（REV-16-4 / DEFECT-R16-01）：
        # 工具授权携带的参数值是定义文档的一部分（IFC-IB-340），
        # 若沿用自动 `_fields` 展开只输出 `expert_name` / `tool_names`，
        # 则「GET 读回 → PUT 原样写回」会**静默丢参**（读回再写回不再等价）。
        # 因此与 `_EdgeSpecSerializer` 同纪律：手写 `to_representation`，
        # 显式保全字段。`param_values` 保序输出为 `[{"name","value"}, ...]`。
        return {
            "expert_name": instance.expert_name,
            "tool_names": list(instance.tool_names),
            "param_values": [
                {"name": pv.name, "value": pv.value} for pv in getattr(instance, "param_values", ())
            ],
        }


class DefinitionDocumentSerializer(serializers.Serializer):
    """`DefinitionDocument` 的对外投影（IFC-IB-294）。

    只输出定义文档的**内容字段**：不含任何凭据（定义文档本就不应含凭据；
    `ValidationErrorItem` 只出 `path`/`code`/`message`）。
    """

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "schema_version": instance.schema_version,
            "project_id": instance.project_id,
            "content_hash": instance.content_hash,
            "experts": [_ExpertSpecInputSerializer().to_representation(e) for e in instance.experts],
            "route": _RouteSpecInputSerializer().to_representation(instance.route),
            "orchestration": _OrchestrationSpecInputSerializer().to_representation(instance.orchestration),
            "tool_grants": [_ToolGrantSpecSerializer().to_representation(g) for g in instance.tool_grants],
            "updated_at": instance.updated_at,
        }


class ValidationErrorItemSerializer(_DataclassSerializer):
    """单条校验项（**只出** `path`/`code`/`message`；不回显任何凭据值）。"""

    _fields = {"path": None, "code": None, "message": None}


class SaveResultSerializer(serializers.Serializer):
    """`SaveResult` 的对外投影（IFC-IB-295）。`conflict=True` 时含可读冲突回执。"""

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "ok": instance.ok,
            "content_hash": instance.content_hash,
            "conflict": instance.conflict,
            "errors": [ValidationErrorItemSerializer().to_representation(e) for e in instance.errors],
        }


class DefinitionConfigInputSerializer(serializers.Serializer):
    """`PUT /api/config/definition` 入参（IFC-IB-295）。

    * `document`：完整定义文档（JSON 对象）；
    * `expected_content_hash`：乐观并发基（可选；缺省表示「不校验并发」）。

    **刻意不接受** `project_id`：归属恒取自服务端鉴权结论（见模块文档）。
    """

    expected_content_hash = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    document = serializers.JSONField()


class ConfigAuditEntrySerializer(serializers.Serializer):
    """`ConfigAuditEntry` 的对外投影（IFC-IB-356 / 359；`GET /api/config/audit`）。

    **字段白名单**：`changed_field_names` **只含字段名**、`detail_code` **只含字段名 /
    错误码** —— **永不**输出任何配置取值或凭据（ADR-34）。手写 `to_representation`
    （同本模块总纪律：字段逐个写出，新增领域字段不得静默进/出响应）。
    """

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "timestamp": instance.timestamp,
            "project": instance.project,
            "actor": instance.actor,
            "action": instance.action,
            "changed_field_names": list(instance.changed_field_names),
            "result": instance.result,
            "detail_code": instance.detail_code,
        }


class StorageStateSerializer(serializers.Serializer):
    """`StorageState` 的对外投影（IFC-IB-361 / 362；`GET /api/config/storage-state`）。

    **只暴露**存储态（`memory` / `file` + 是否已配置），**不含**任何键值 / 路径值
    （ADR-35：只登记键名与否，不回显值）。
    """

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "definition_store": instance.definition_store,
            "prompt_store": instance.prompt_store,
            "definition_store_configured": bool(instance.definition_store_configured),
            "prompt_store_configured": bool(instance.prompt_store_configured),
        }


# --------------------------------------------------------------------------- #
# REV-18 项目注册表 / LLM Key（IFC-IB-372 / 374）
#
# 同本模块总纪律：字段逐个写出；**绝不**用 `dataclasses.asdict` 自动展开 ——
# 对 `LlmKeyStatus` 尤其致命：其字段集**天然不含明文**，但一旦改成自动展开，
# 未来给 `LlmKeyStatus` 加一个内部字段就会把它静默送上 API。
# --------------------------------------------------------------------------- #


class ProjectRegistryEntrySerializer(_DataclassSerializer):
    """`ProjectRegistryEntry` 的对外投影（IFC-IB-372 的 `201` / `200` 响应体）。

    只出注册表五字段；`project_id` **不是**凭据，可安全外露。
    """

    _fields = {
        "project_id": None,
        "name": None,
        "status": None,
        "created_at": None,
        "updated_at": None,
    }


class LlmKeyStatusSerializer(serializers.Serializer):
    """`LlmKeyStatus` 的对外投影（IFC-IB-368 / 374；`GET|PUT /api/llm-key`）。

    **手写 `to_representation`**（先于 `_DataclassSerializer` 自动路径）：显式只出
    `configured` / `masked` / `updated_at` 三字段。`masked` 是**固定占位符**
    （`LLM_KEY_MASK`），**不含明文的任何前缀 / 后缀 / 长度信息** —— 这是一条
    「存在性可披露、取值不可披露」的**契约**，不是实现细节（ADR-38）。
    """

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "configured": bool(instance.configured),
            "masked": instance.masked,
            "updated_at": instance.updated_at,
        }


def definition_derived_summary(view: Any) -> dict[str, Any]:
    """派生视图摘要（IFC-IB-294 的「+ 派生视图摘要」）。

    只暴露**只读派生结果**（专家名 / 能力摘要 / 图节点与条件边）—— 供界面只读渲染，
    **不含**任何真源写入口（视图侧零持久化，ADR-14）。凭据一律不出现。
    """
    return {
        "capability_digest": view.capability_digest,
        "expert_names": [e.name for e in view.experts],
        "nodes": list(view.graph_config.nodes),
        "conditional_edges": [
            _ConditionalEdgeSpecSerializer().to_representation(ce) for ce in view.graph_config.conditional_edges
        ],
        "edges": [_EdgeSpecSerializer().to_representation(e) for e in view.graph_config.edges],
    }
