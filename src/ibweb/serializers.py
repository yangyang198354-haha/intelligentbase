"""
@module MOD-IB-23
@implements IFC-IB-242~249 响应体字段契约（module_design §3 MOD-IB-23）
@depends MOD-IB-01（领域类型）, MOD-IB-11/12/14（台账/Blob/重建类型）
@author sub_agent_software_developer

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
