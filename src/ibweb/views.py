"""
@module MOD-IB-23
@implements IFC-IB-242 ~ IFC-IB-249（HTTP 端点）
            IFC-IB-283（R2）`GET /api/files/{doc_id}/images/{image_id}` 页面图字节
            IFC-IB-294/295（R7）`GET|PUT /api/config/definition` 定义文档读写
            IFC-IB-352（REV-16-2）`/api/config/prompts[/{expert}/{layer}]` 提示词端点族
            IFC-IB-307（R8）`POST /api/chat/resume` 会话续跑（fail-closed 准入顺序）
            IFC-IB-333（R14）`GET /api/projects` 项目枚举（admin 全部 / ops 仅自身）
            IFC-IB-359/360（REV-16-4）`GET /api/config/audit` + 保存路径审计挂钩
            IFC-IB-362（REV-16-4）`GET /api/config/storage-state`
            IFC-IB-372（REV-18）`GET|POST /api/projects` + `PATCH|DELETE /api/projects/{project_id}`
            IFC-IB-373（REV-18）`PATCH|DELETE /api/accounts/{user_id}` + `POST /api/accounts` 顺序前置
            IFC-IB-374（REV-18）`GET|PUT|DELETE /api/llm-key`（唯一写入口）
            IFC-IB-375（REV-18）`POST|GET /api/files` 项目域化（kb_id 由主体 project_id 推导）
@depends MOD-IB-23（authz/composition/serializers/sse）, MOD-IB-11/12/13/14/15/22（服务）
@author software-developer

HTTP 端点（MOD-IB-23 的对外面）。本模块**只做三件事**：

1. 把请求翻成基座类型（`RequestContext` / `Scope` / `bytes`）；
2. 调基座端口；
3. 把结果或异常翻成状态码 + JSON。

任何业务判断都不在这里：**这里是薄层，薄到可以一眼看完**。若某天发现这里出现了
「如果状态是 X 就怎么做」这类领域规则，正确做法是把规则移回 `ib/` 的对应模块，
而不是在此处复制一份。

## `project_id` 的**唯一**来源

一律取 `ctx.authz.project_id`（中间件已按 `Authorization` 头解出）。请求体/查询串中的
`project_id` 一律**忽略**——包括「看起来一致」的情况：一旦开始「校验后采纳」，
就多出一条「什么情况下可以采纳请求值」的分支，而这正是越权漏洞生长的位置。
`X-IB-Project` 与服务端结论不一致时由中间件直接 403（见 `ibweb.authz`）。

## 异常 → 状态码的**单点映射**

| 领域异常 | HTTP | 语义 |
|----------|------|------|
| `ValidationError` | 400 | 扩展名/大小/魔数校验失败 |
| `ScopeViolationError` | 403 | `kb_id` 不属于本项目（**不用 404**，避免存在性探测） |
| `NotFoundError` | 404 | 资源不存在或不在作用域内 |
| `ConflictError` | 409 | 状态冲突（如重试非 failed 文档） |
| `DependencyUnavailableError` | 503 | 台账/Blob 等**权威**依赖不可用（fail-closed） |
| 其他 | 500 | 不回显内部细节 |

映射集中在一处（`_error_response`）而非各视图各写一遍：状态码契约是**对外承诺**，
散落的 `try/except` 迟早会让同一个异常在两个端点上得到不同状态码。

## R2 增量（IFC-IB-283）：页面图字节端点

图片端点**复用同一张映射表**（`NotFoundError`→404 / `DependencyUnavailableError`→503），
并刻意让「跨项目访问」与「行不存在」都落到 `NotFoundError`：合并成同一个状态码是
**反存在性探测**的要求，不是实现上的巧合。`GET /healthz/deps` 的字段集合**不变**
（IFC-IB-283 明文要求）：取图依赖 BlobStore，其健康语义已由既有字段与 §7.4 覆盖。
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from rest_framework import serializers, status

from ib.core import (
    BlobRef,
    ConfigAuditEntry,
    ConfigError,
    ConflictError,
    DependencyUnavailableError,
    DocStatus,
    IbError,
    NotFoundError,
    ProjectRegistryEntry,
    ScopeViolationError,
    StorageState,
    ValidationError,
    new_session_token,
    token_digest,
)
from ib.context import iso_plus_seconds, parse_iso, utc_now_iso
from ib.observability import log_event
from ibweb import composition
from ibweb.accounts import (
    GLOBAL_PROJECT,
    is_global,
    load_account_settings,
    validate_password_strength,
)
from ibweb.accounts.throttle import audit
from ibweb.authz import (
    AUTHZ_ATTR,
    REQUEST_CTX_ATTR,
    get_authz,
    get_policy,
    parse_bearer,
)
from ibweb.serializers import (
    ConfigAuditEntrySerializer,
    DefinitionConfigInputSerializer,
    DefinitionDocumentSerializer,
    DeleteReportSerializer,
    DocumentRecordSerializer,
    EgressDescriptorSerializer,
    FileListEnvelopeSerializer,
    HealthStatusSerializer,
    LlmKeyStatusSerializer,
    ProjectRegistryEntrySerializer,
    RebuildJobSerializer,
    SaveResultSerializer,
    StorageStateSerializer,
    ValidationErrorItemSerializer,
    definition_derived_summary,
)

__all__ = [
    "FileListQuerySerializer",
    "UploadInputSerializer",
    "error_response",
    "files_endpoint",
    "file_detail_endpoint",
    "file_image_endpoint",
    "rebuild_endpoint",
    "rebuild_progress_endpoint",
    "rebuild_activate_endpoint",
    "rebuild_rollback_endpoint",
    "chat_stream_endpoint",
    "healthz_endpoint",
    "healthz_deps_endpoint",
    "definition_config_endpoint",
    # REV-16-2 提示词端点族（IFC-IB-352）
    "prompt_config_endpoint",
    # REV-16-4 配置审计 / 存储态端点（IFC-IB-359 / 362）
    "config_audit_endpoint",
    "storage_state_endpoint",
    # R14 项目上下文（IFC-IB-333）
    "projects_endpoint",
    # R13 账户 / 会话（IFC-IB-316~321）
    "auth_login_endpoint",
    "auth_logout_endpoint",
    "auth_me_endpoint",
    "auth_change_password_endpoint",
    "auth_session_renew_endpoint",
    "accounts_endpoint",
    "account_disable_endpoint",
    "account_reset_password_endpoint",
    # REV-18 项目 CRUD / 账户扩展 / LLM Key（IFC-IB-372 / 373 / 374）
    "project_detail_endpoint",
    "account_detail_endpoint",
    "llm_key_endpoint",
]

#: 分页上限：**服务端硬上限**（不接受客户端指定更大的值）。
#: 客户端传 `page_size=100000` 时不是「报错」而是**截断到上限**：列表页传错参数
#: 不该让用户看到错误页，但也不能让一次请求把整库拉进内存（4GB 的树莓派上很致命）。
MAX_PAGE_SIZE = 100

#: 页面图扩展名 → MIME（**固定表，不用 `mimetypes`**）。
#:
#: 为什么不用 `mimetypes.guess_type`：它在 Windows 上读注册表（`HKEY_CLASSES_ROOT\...\
#: Content Type`），于是**同一份代码在不同机器上给出不同的 `Content-Type`** ——
#: 而 `Content-Type` 是对外契约（IFC-IB-283 写明 `image/*`），不能依赖部署机的注册表。
#: 固定表让「这张图是什么类型」成为可评审、可测试、跨平台一致的事实。
_IMAGE_MIME_BY_EXT = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}

#: 无法判定类型时的回退：**诚实地说「我不知道」**，而不是硬贴一个 `image/png`。
#: `page_or_section` 里的页面图按构造只可能是栅格格式（`source_kind ∈
#: {embedded_image, page_scan}`，见 MOD-IB-13），故正常路径必然命中上表里的某一项；
#: 走到回退说明存储对象不是页面图 —— 此时谎报 `image/*` 会让浏览器按图片解码失败并显示破图。
_UNKNOWN_MIME = "application/octet-stream"


def _image_content_type(rel_path: str) -> str:
    """由存储相对路径的扩展名判定页面图 MIME（未知即回退，见 `_UNKNOWN_MIME`）。"""
    name = (rel_path or "").rsplit("/", 1)[-1]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return _IMAGE_MIME_BY_EXT.get(ext, _UNKNOWN_MIME)


def _blob_ref_of_rel_path(rel_path: str) -> BlobRef:
    """由台账里的存储相对路径**重建** `BlobRef`（读路径专用）。

    `sha256` 从文件名取得（来源与 `ib.blob` 的 `put()` 同构：`<sha256>.<ext>`）——
    这也让 `InMemoryBlobStore._key_of` 的「rel_path 与 sha256 必须一致」校验继续生效
    （构造错误会得到 `None` 而不是读错对象）。
    `size_bytes` 在**读**路径上不参与定位（`get()` 只用 `rel_path`/`sha256`），故填 0：
    伪造一个长度才是错的做法（长度是写路径的产物，读路径无从得知也不必知道）。
    """
    name = (rel_path or "").rsplit("/", 1)[-1]
    sha256 = name.rsplit(".", 1)[0] if "." in name else name
    return BlobRef(sha256=sha256, rel_path=rel_path, size_bytes=0)


def _doc_status_values() -> list[Any]:
    """`DocStatus` 的取值列表（从枚举取，不硬编码字符串 —— 硬编码会在新增状态时失配）。"""
    return list(DocStatus)


class FileListQuerySerializer(serializers.Serializer):
    """`GET /api/files` 的查询参数校验（`page` / `page_size` / `status`）。

    `page_size` 刻意**不设** `max_value`：超限时截断而非 400（见 `MAX_PAGE_SIZE` 的说明）。
    截断发生在 `_list_files` 的取用点，是唯一一处生效点。
    """

    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, default=20)
    status = serializers.ChoiceField(
        required=False,
        allow_null=True,
        allow_blank=True,
        choices=[str(s) for s in _doc_status_values()],
    )


class UploadInputSerializer(serializers.Serializer):
    """`POST /api/files` 的**表单字段**校验（文件字节走 `request.FILES`）。

    **REV-18（IFC-IB-375 / ADR-41）**：请求体**不再接收** `kb` / `kb_id` 字段 ——
    `kb_id` 由**已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`）。
    `project_id` 与 `kb_id` 都**不可由客户端自证**（架构红线 `architecture_design.md:120`），
    故本序列化器不再声明任何字段（DRF 对未知字段默认忽略）。
    """

    #: 空字段集（显式保留结构，声明「请求体不得携带 kb 字段」）。
    pass


# --------------------------------------------------------------------------- #
# 请求/响应辅助
# --------------------------------------------------------------------------- #


def _ctx_of(request: Any) -> Any:
    """取中间件挂上的 `RequestContext`；缺失即视为配置错误（不静默造一个）。"""
    ctx = request.__dict__.get(REQUEST_CTX_ATTR)
    if ctx is None:
        raise DependencyUnavailableError("请求上下文缺失（鉴权中间件未生效）", dependency="authz")
    return ctx


def error_response(exc: BaseException) -> Any:
    """领域异常 → HTTP 响应（**单点映射**，见模块文档表格）。"""
    if isinstance(exc, ValidationError):
        return _json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, ScopeViolationError):
        # 403 而非 404：存在性探测防护（module_design §1.4）
        return _json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_403_FORBIDDEN)
    if isinstance(exc, NotFoundError):
        return _json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_404_NOT_FOUND)
    if isinstance(exc, ConflictError):
        return _json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_409_CONFLICT)
    if isinstance(exc, DependencyUnavailableError):
        # fail-closed：台账/Blob 不可用时**不给半成品结果**（§7.4）
        return _json(
            {"error": {"code": exc.code, "message": str(exc)}},
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if isinstance(exc, IbError):
        return _json({"error": {"code": exc.code, "message": str(exc)}}, status.HTTP_500_INTERNAL_SERVER_ERROR)
    # 非领域异常：**不回显**异常文本（可能含内部路径/参数），只记日志
    log_event("http", "unhandled_error", error_type=type(exc).__name__)
    return _json(
        {"error": {"code": "internal_error", "message": "服务内部错误，请稍后重试"}},
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _json(payload: Any, http_status: int) -> Any:
    from django.http import JsonResponse

    return JsonResponse(payload, status=http_status, json_dumps_params={"ensure_ascii": False})


def _require_manage(request: Any) -> Any:
    """管理动作的权限前置判定；不通过抛 `ScopeViolationError`（→403）。"""
    ctx = _ctx_of(request)
    if not get_policy(request).can_manage(ctx.authz):
        raise ScopeViolationError("当前主体无管理权限（上传/删除/重试/重建）")
    return ctx


# --------------------------------------------------------------------------- #
# IFC-IB-242 / 243：上传与列表
# --------------------------------------------------------------------------- #


def files_endpoint(request: Any) -> Any:
    """`POST /api/files`（multipart）→ `201 DocumentRecord`；`GET` → 分页列表。

    上传路径的**fail-closed**语义：台账或 BlobStore 不可用 → 503。
    这里是唯一允许「因为基础设施问题让用户看到失败」的地方 —— 因为上传的产物
    （原始文件 + 台账行）是**权威数据**，半途失败留下幽灵行比直接报错更难排查。
    """
    if request.method == "GET":
        return _list_files(request)
    if request.method == "POST":
        return _upload_file(request)
    return _json({"error": {"code": "method_not_allowed", "message": "不支持的方法"}}, status.HTTP_405_METHOD_NOT_ALLOWED)


def _upload_file(request: Any) -> Any:
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        # REV-18（IFC-IB-375 / ADR-41）：请求体不再接收 kb 字段；`kb_id` 由已认证主体的
        # `project_id` **推导**（`kb_id ≡ project_id`）—— 范围只认服务端结论，客户端
        # **不可自证**（架构红线 architecture_design.md:120）。
        form = UploadInputSerializer(data={})
        form.is_valid(raise_exception=True)

        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError("缺少文件字段 file")

        scope = composition.resolve_scope(ctx)
        kb_id = scope.project_id
        # **保留**归属断言（IFC-IB-130）；失败仍 403（非 404，避免存在性探测）—— 红线不被削弱。
        deps.ledger.assert_kb_in_project(scope.project_id, kb_id)

        head = upload.read(4096)
        upload.seek(0)
        validated = deps.lifecycle.validate_upload(upload.name or "", int(upload.size), head)
        record = deps.lifecycle.submit_upload(ctx, validated, kb_id, data=upload)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    log_event("upload", "accepted", project_id=record.project_id, doc_id=record.doc_id)
    return _json(DocumentRecordSerializer(record).data, status.HTTP_201_CREATED)


def _list_files(request: Any) -> Any:
    deps = composition.get_deps()
    try:
        ctx = _ctx_of(request)
        query = FileListQuerySerializer(data=request.GET.dict())
        query.is_valid(raise_exception=True)
        data = query.validated_data
        raw_status = (data.get("status") or "").strip()
        scope = composition.resolve_scope(ctx)
        items, total = deps.ledger.list_documents(
            scope,
            page=int(data.get("page", 1)),
            page_size=min(int(data.get("page_size", 20)), MAX_PAGE_SIZE),
            status=raw_status or None,
        )
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    payload = {"items": DocumentRecordSerializer(items, many=True).data, "total": int(total)}
    return _json(payload, status.HTTP_200_OK)


# --------------------------------------------------------------------------- #
# IFC-IB-244 / 245：删除与重试
# --------------------------------------------------------------------------- #


def file_detail_endpoint(request: Any, doc_id: str) -> Any:
    """`DELETE /api/files/{doc_id}` → `200 DeleteReport`；`POST .../retry` → `200 DocumentRecord`。"""
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        scope = composition.resolve_scope(ctx)
        if request.method == "DELETE":
            report = deps.lifecycle.delete_document(scope, doc_id)
            return _json(DeleteReportSerializer(report).data, status.HTTP_200_OK)
        if request.method == "POST":
            record = deps.lifecycle.retry_document(scope, doc_id)
            return _json(DocumentRecordSerializer(record).data, status.HTTP_200_OK)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    return _json({"error": {"code": "method_not_allowed", "message": "不支持的方法"}}, status.HTTP_405_METHOD_NOT_ALLOWED)


# --------------------------------------------------------------------------- #
# IFC-IB-283：页面图字节（R2 / M-02 读路径）
# --------------------------------------------------------------------------- #


def file_image_endpoint(request: Any, doc_id: str, image_id: str) -> Any:
    """`GET /api/files/{doc_id}/images/{image_id}` → 图片字节（IFC-IB-283）。

    **单一取图入口**：`related_images` 载荷里的 `url_path` 指向这里，前端按需取原图。
    载荷里**只放路径、不放字节**（IFC-IB-282）—— base64 内联会让每个事件都带上几百 KB，
    既撑爆 SSE 帧，也让「同一张图被多个会话引用」时重复传输。

    ## 语义（**四条边界，逐条与契约对齐**）

    | 情形 | 状态码 | 说明 |
    |------|--------|------|
    | 正常 | `200` | `Content-Type: image/*`（字节流，可缓存） |
    | 主体无问答权限 | `403` | 与 `chat_stream_endpoint` 同口径（图随问答出现） |
    | 关联行缺失 / 无字节引用 / 字节读不到 | `404` | **不区分「不存在」与「不属于你」**（§1.4 第 2 条） |
    | BlobStore 不可用 | `503` | fail-closed：直接报错，**不返回占位图** |

    「不区分不存在与不属于你」是**安全要求**而不是偷懒：若「不属于你」返回 403 而
    「不存在」返回 404，攻击者就能用状态码差异枚举出「哪些 doc_id 真实存在」——
    这正是存在性探测。故跨项目访问在 `get_chunk_image` 内就退化为「查不到」→ 404。

    **fail-closed 而非占位图**：返回一张灰色占位图会让前端把「存储故障」渲染成一张真图，
    用户与运维都无从察觉知识库的图片已整体不可读。宁可让缩略图静默消失
    （IFC-IB-284 要求前端对 403/404/503 静默隐藏），也不要伪造一张看起来正常的图。

    ## 鉴权纪律

    只认 `Authorization: Bearer <token>`（本函数不做任何令牌解析，由中间件统一完成）。
    查询串里出现 `token` / `api_key` 等键名会被中间件直接 **400** —— 令牌进 URL 会被
    nginx/uvicorn 访问日志完整打印（FreeArk 已实际泄露过一次），故该端点**不接受** `?token=`。
    """
    deps = composition.get_deps()
    if request.method != "GET":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        ctx = _ctx_of(request)
        if not get_policy(request).can_query(ctx.authz):
            # 403（不是 404）：能力不足是**主体**的属性，与资源存在性无关，
            # 回 404 会把「你没权限」伪装成「资源不存在」，排障时误导接入方。
            raise ScopeViolationError("当前主体无问答权限")
        scope = composition.resolve_scope(ctx)
        record = deps.ledger.get_chunk_image(scope, doc_id, image_id)
        if record is None or not record.blob_ref:
            # 关联行不存在 / 未登记字节引用（R2 的页面图确实没有字节，见 MOD-IB-13 类文档）
            raise NotFoundError("图片不存在或当前不可得")
        payload = deps.blobs.get(_blob_ref_of_rel_path(record.blob_ref))
        if payload is None:
            # 行在、字节不在（存储被清理/未同步）：同样是「不可得」，不给半成品
            raise NotFoundError("图片不存在或当前不可得")
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    from django.http import HttpResponse

    response = HttpResponse(payload, content_type=_image_content_type(record.blob_ref))
    # `private`：内容是授权范围相关的（同一 URL 对不同主体可能 403），**不得**被共享缓存存下。
    # 长 `max-age` 是安全的：`image_id` 由 `(doc_id, page_or_section, locator)` 确定性派生，
    # 而 `doc_id` 每次上传新生成 —— 故「同一 URL 的字节永不改变」（IFC-IB-279 的副作用）。
    response["Cache-Control"] = "private, max-age=86400"
    # 禁止浏览器按内容嗅探改判类型：否则一个扩展名骗人的对象会被当成 HTML 执行
    response["X-Content-Type-Options"] = "nosniff"
    return response


# --------------------------------------------------------------------------- #
# IFC-IB-246：重建
# --------------------------------------------------------------------------- #


def rebuild_endpoint(request: Any) -> Any:
    """`POST /api/rebuild` → `202 RebuildJob`（**只启动**，不阻塞等完成）。

    返回 202 而非 200：重建是长任务，任务的**完成**由 `GET /api/rebuild/{job_id}` 轮询。
    若在此同步跑完，请求就会随文档量线性变长，最终撞上网关超时并留下「不知道成功没有」的
    半完成状态。
    """
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        project_id = ctx.authz.project_id
        plan = deps.rebuild.plan_rebuild(project_id)
        job = deps.rebuild.start_rebuild(project_id, plan)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    log_event("rebuild", "started", project_id=ctx.authz.project_id, job_id=job.job_id)
    return _json(RebuildJobSerializer(job).data, status.HTTP_202_ACCEPTED)


def rebuild_activate_endpoint(request: Any) -> Any:
    """`POST /api/rebuild/activate` → 把 active 版本切到请求体里的 `version`（200）。

    请求体为 JSON：`{"version": "2"}`，`version` 是 `plan_rebuild` 产出的目标版本号
    （`to_version`）。切换是**显式决策**（而非 `step_rebuild` 自动触发）：运维需要确认点。
    """
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        project_id = ctx.authz.project_id
        version = _rebuild_version_of(request)
        deps.rebuild.activate_version(project_id, version)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    log_event("rebuild", "activated", project_id=ctx.authz.project_id, version=version)
    return _json({"project_id": ctx.authz.project_id, "active_collection_version": version}, status.HTTP_200_OK)


def rebuild_rollback_endpoint(request: Any) -> Any:
    """`POST /api/rebuild/rollback` → 把 active 版本回滚到请求体里的 `version`（200）。

    回滚不重索引（旧集合从未被删），是 O(1) 的台账单值切换。请求体同上：`{"version": "1"}`。
    """
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        project_id = ctx.authz.project_id
        version = _rebuild_version_of(request)
        deps.rebuild.rollback(project_id, version)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    log_event("rebuild", "rolled_back", project_id=ctx.authz.project_id, version=version)
    return _json({"project_id": ctx.authz.project_id, "active_collection_version": version}, status.HTTP_200_OK)


def _rebuild_version_of(request: Any) -> str:
    """读取并校验重建请求体里的 `version` 字段（返回非空字符串，否则 `ValidationError`）。"""
    try:
        body = json.loads((request.body or b"").decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        raise ValidationError("请求体必须为 JSON 对象")
    if not isinstance(body, dict):
        raise ValidationError("请求体必须为 JSON 对象")
    version = str(body.get("version", "") or "").strip()
    if not version:
        raise ValidationError("缺少字段 version")
    return version


def rebuild_progress_endpoint(request: Any, job_id: str) -> Any:
    """`GET /api/rebuild/{job_id}` → `RebuildProgress`（**只读**，不推进任务）。

    刻意不在这里调 `step_rebuild`：推进是 worker 的职责。若 GET 也推进，那么「监控」
    这个动作就带上了副作用 —— 运维刷新几次页面就可能改变系统状态，且 lease 归属混乱。
    """
    deps = composition.get_deps()
    try:
        ctx = _ctx_of(request)
        project_id = ctx.authz.project_id
        row = deps.ledger.get_rebuild_job(job_id)
        if row is None:
            raise NotFoundError("重建任务不存在")
        if str(row.project_id) != project_id:
            # 跨项目访问：403（避免存在性探测，与 scope 越界同待遇）
            raise ScopeViolationError("重建任务不属于当前项目")
        scope = composition.resolve_scope(ctx)
        indexed = _count(deps, scope, "indexed")
        failed = _count(deps, scope, "failed")
        pending = _count(deps, scope, "pending") + _count(deps, scope, "parsing")
        done = failed == 0 and pending == 0 and indexed > 0
        payload = {
            "job_id": str(job_id),
            "state": str(row.state),
            "indexed": indexed,
            "failed": failed,
            "pending": pending,
            "done": bool(done),
        }
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    return _json(payload, status.HTTP_200_OK)


def _count(deps: Any, scope: Any, doc_status: str) -> int:
    """按状态计数（`page_size=1` 只为拿 `total`，不拉数据 —— 避免为计数读全表）。"""
    _, total = deps.ledger.list_documents(scope, page=1, page_size=1, status=doc_status)
    return int(total)


# --------------------------------------------------------------------------- #
# IFC-IB-247：SSE 问答
# --------------------------------------------------------------------------- #


def chat_stream_endpoint(request: Any) -> Any:
    """`GET /api/chat/stream?session_id=` → `text/event-stream`（原生 SSE）。

    **鉴权只经 `Authorization` 头**：查询串里出现 `token` 会被中间件直接 400
    （`?token=` 会被访问日志完整打印，FreeMark 已实际泄露过一次）。

    语料的检索范围**不在本函数里推导**：它由 `deps.orchestrator_for(project_id)`
    在构造期闭包绑定（ADR-09）。本函数只负责「把 query 和 ctx 交给编排器」。

    **会话标识必填（FND-R11-01 / AC-IB-20-01）**：缺失 / 空白即**显式 4xx 拒绝**，
    **绝不**回退到字面量 `"default"`。回退会让「没传会话标识」与「显式使用名为 default
    的会话」在服务端不可区分，多个客户端于是**静默共用一个会话**（历史互相污染、
    并且把 A 的上下文注入 B 的回答）—— 这类错误既不可见、也无法在日志里定位。
    """
    from ibweb.sse import streaming_sse_response

    deps = composition.get_deps()
    ctx = _ctx_of(request)
    if not get_policy(request).can_query(ctx.authz):
        return error_response(ScopeViolationError("当前主体无问答权限"))

    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    if not query:
        return error_response(ValidationError("缺少查询参数 q"))

    session_id = (request.GET.get("session_id") or "").strip()
    if not session_id:
        # 显式拒绝，不猜测（AC-IB-20-01）。400 属 ValidationError 单点映射。
        return error_response(ValidationError("缺少会话标识 session_id（不得回退到默认会话）"))
    try:
        orchestrator = deps.orchestrator_for(ctx.authz.project_id)
    except IbError as exc:
        return error_response(exc)

    def _events() -> Any:
        log_event("chat", "started", project_id=ctx.authz.project_id, session_id=session_id)
        yield from orchestrator.run(query, ctx=ctx, session_key=ctx.session_key)

    return streaming_sse_response(_events())


def chat_resume_endpoint(request: Any) -> Any:
    """`POST /api/chat/resume` → 续跑 SSE（IFC-IB-307；confirm gate 恢复）。

    ## 准入顺序（**强制**，module_design §3 MOD-IB-23 IFC-IB-307）

    `鉴权（Authorization 头）→ 归属断言（session_key 前缀，FM-7）→ SessionStore.load
    （IFC-IB-221）→ can_resume（IFC-IB-306）→ 续跑（IFC-IB-233）`。

    **任一前置不满足即 fail-closed**，且**不得**退化为「新建会话后重跑」—— 那等于把
    「未经确认的动作」重新执行一遍，正是 ADR-17 约束 4 要防的失败模式。故本端点把
    前置检查**放在打开 SSE 流之前**，以 `403` / `404` / `409` / `503` 显式终止；
    只有在状态与决策都对得上时，才打开续跑流。

    **令牌纪律**：沿用 IFC-IB-247 —— **仅允许 `Authorization` 头**；`?token=` 由中间件
    直接 400。本端点**不接受**查询串令牌（访问日志会完整打印 URL）。

    ## 会话键的**唯一**构造入口（FM-7；MAJOR-1 修复）

    请求体给 `session_key` 时直传（仍经前缀归属断言）；只给 `session_id` 时，键**必须**经
    `ib.context.session_key(project_id, actor_id, session_id)` 构造，`actor_id` 取自
    `ctx.authz.actor_id` —— 与流路径（`chat_stream_endpoint` → `ctx.session_key`）**逐字一致**。
    本视图**不得**自行拼接会话键（此前自造 2 段键导致真实续跑恒 404）。
    """
    from ib.context import assert_session_key, session_key as ib_session_key
    from ib.orchestration import ResumePayload, can_resume
    from ibweb.sse import streaming_sse_response

    deps = composition.get_deps()
    ctx = _ctx_of(request)

    # 1) 鉴权（Authorization 头；查询串令牌已被中间件拒绝）
    if not get_policy(request).can_query(ctx.authz):
        return error_response(ScopeViolationError("当前主体无问答权限"))

    try:
        raw = json.loads((request.body or b"").decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return error_response(ValidationError("请求体必须是合法 JSON 对象"))
    if not isinstance(raw, dict):
        return error_response(ValidationError("请求体必须是 JSON 对象"))

    project_id = ctx.authz.project_id
    session_key = str(raw.get("session_key") or "")
    if not session_key:
        session_id = str(raw.get("session_id") or "").strip()
        if not session_id:
            return error_response(ValidationError("缺少会话标识 session_key / session_id"))
        # 会话键**必须**经**唯一入口** `ib.context.session_key(project_id, actor_id, session_id)`
        # 构造，`actor_id` 取自鉴权结论 `ctx.authz.actor_id` —— 与流路径
        # （`chat_stream_endpoint` → `ctx.session_key`，由 `make_request_context` 产出）**逐字一致**。
        # **禁止**在视图内自造键：此前此处自造 **2 段**键 `f"{project_id}:{session_id}"`，而流路径
        # 写入用的是中间件构造的 **3 段**键 `f"{project_id}:{actor_id}:{session_id}"` —— 两键永不相等，
        # 真实 HTTP 续跑**恒 404**（本端点唯一的存在性入口失效）。段的构造规则只允许存在于 `ib.context`。
        # 注：会话标识本身含 `:` 会破坏前缀断言，唯一入口将 fail-closed 拒绝（→ 403），不静默改写。
        try:
            session_key = ib_session_key(project_id, ctx.authz.actor_id, session_id)
        except ScopeViolationError as exc:
            return error_response(exc)

    # 2) 归属断言（FM-7）：前缀与当前项目不符 → 403（不当作新会话）
    try:
        assert_session_key(session_key, project_id)
    except ScopeViolationError as exc:
        return error_response(exc)

    # 3) 确认门未启用 → 不存在「待确认中间态」，恢复不可用（fail-closed，不新建会话）
    if not bool(getattr(deps.cfg, "confirmation_gate_enabled", False)):
        return error_response(ConflictError("确认门未开启（默认关闭），无可恢复的挂起操作"))

    # 4) SessionStore.load（IFC-IB-221）；存储不可用 → 503（fail-closed）
    try:
        state = deps.sessions.load(session_key)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001 - 会话存储不可用即 fail-closed
        log_event("chat", "resume_store_failed", error_type=type(exc).__name__)
        return error_response(DependencyUnavailableError("会话存储不可用，无法恢复", dependency="session"))
    if state is None:
        return error_response(NotFoundError("会话不存在或已过期，无法恢复（fail-closed）"))

    # 5) can_resume（IFC-IB-306）三判据：状态丢失 / 无待确认中间态 / 未携决策
    gate = getattr(state, "gate", None)
    if gate is None:
        return error_response(NotFoundError("该会话无待确认中间态（不存在 / 已丢失），fail-closed"))
    payload = ResumePayload.from_dict(raw, session_key=session_key)
    if payload.decision is None:
        return error_response(ConflictError("未携带有效决策，拒绝恢复（fail-closed）"))
    # 「请求指向的 gate_id」取自载荷决策（或请求体显式 gate_id），与 `state.gate.gate_id` 做
    # **真实对账**（IFC-IB-306；签名文本一字不改）。此前以 `state.gate` 派生 gate_id 再回传，
    # 使 can_resume 内「状态里的中间态 vs 请求指向的中间态」对账恒为假而空转 —— 现由请求侧给值；
    # 不一致即 fail-closed（False → 409）。
    requested_gate_id = str(getattr(payload.decision, "gate_id", "") or "") or str(raw.get("gate_id") or "")
    if not can_resume(state, requested_gate_id, payload):
        return error_response(ConflictError("决策与会话状态不一致，拒绝恢复（fail-closed）"))

    try:
        orchestrator = deps.orchestrator_for(project_id)
    except IbError as exc:
        return error_response(exc)

    decision = payload.decision
    assert decision is not None  # 上面已判定
    # 6) 续跑：把 ctx 与原决策交给编排层（原提问从 state.turns 取回；**不新建会话**）
    resume_input = {
        "session_key": session_key,
        "decision": {"gate_id": decision.gate_id, "approved": decision.approved},
        "ctx": ctx,
    }

    def _events() -> Any:
        log_event("chat", "resume_started", project_id=project_id, session_id=session_key)
        yield from orchestrator.resume(session_key, resume_input)

    return streaming_sse_response(_events())


# --------------------------------------------------------------------------- #
# IFC-IB-248 / 249：健康检查
# --------------------------------------------------------------------------- #


def healthz_endpoint(request: Any) -> Any:
    """`GET /healthz` → `200 {ok: true}`。**免鉴权**（见 `ibweb.authz` 模块文档）。

    刻意**不**探测依赖：探针的职责是「进程是否还活着」。把依赖探测塞进来会导致
    「Qdrant 抖动 → 编排器重启后端」这种放大故障（重启解决不了外部依赖问题）。
    依赖状态由 `/healthz/deps` 单独暴露，供人工与监控区分使用。
    """
    return _json({"ok": True}, status.HTTP_200_OK)


def healthz_deps_endpoint(request: Any) -> Any:
    """`GET /healthz/deps` → 各依赖健康 + **数据外发声明**（AC-IB-12-05）。"""
    deps = composition.get_deps()
    payload = {
        "qdrant": HealthStatusSerializer(_safe_health(deps.vectors)).data,
        "embed": HealthStatusSerializer(_safe_health(deps.embedder)).data,
        "llm": HealthStatusSerializer(_safe_health(deps.llm)).data,
        "egress": EgressDescriptorSerializer(_egress_of(deps)).data,
    }
    return _json(payload, status.HTTP_200_OK)


def _safe_health(component: Any) -> Any:
    """探测依赖健康；**探测本身失败也算一种健康信息**（不抛、不让 /healthz/deps 500）。

    若探测抛异常就返回 500，那么「依赖挂了」与「探测代码有 bug」在监控上不可区分 ——
    而这两者的处置完全不同。
    """
    from ib.core import HealthStatus

    try:
        return component.health()
    except Exception as exc:  # noqa: BLE001
        return HealthStatus(ok=False, detail=f"探测失败（{type(exc).__name__}）", latency_ms=None)


def _egress_of(deps: Any) -> Any:
    from ib.core import EgressDescriptor

    try:
        return deps.egress or deps.llm.describe_egress()
    except Exception:  # noqa: BLE001 - 外发声明缺失不应让健康端点失败
        return EgressDescriptor(remote=False, endpoint_host="", data_categories=[])


# --------------------------------------------------------------------------- #
# R7（IFC-IB-294 / 295）：定义文档读写端点
#
# 纪律（module_design §3 MOD-IB-23 R7）：
#   * 归属恒取自 `ctx.authz.project_id`（请求体/查询串中的 project_id 一律忽略）；
#   * 读不到 / 写不进定义文档 → **503（fail-closed）**，**不返回空文档**；
#   * 校验不通过 → **400**，逐条回执 `path`/`code`/`message`（**不回显凭据值**）；
#   * 乐观并发冲突 → **409**，含可读冲突回执，**不静默覆盖**；
#   * 界面编辑与直接改文档**一视同仁**（同一校验器 `IFC-IB-290` 裁决）。
# --------------------------------------------------------------------------- #


def definition_config_endpoint(request: Any) -> Any:
    """`GET|PUT /api/config/definition`（IFC-IB-294 / 295）。"""
    if not _visual_config_enabled():
        # 键值**不出现在响应体**（只看行为）：未启用即视为端点不可用。
        return _json(
            {"error": {"code": "not_found", "message": "可视化配置未启用"}},
            status.HTTP_404_NOT_FOUND,
        )
    if request.method == "GET":
        return _get_definition_config(request)
    if request.method == "PUT":
        return _put_definition_config(request)
    return _json(
        {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


def _visual_config_enabled() -> bool:
    """`IB_VISUAL_CONFIG_ENABLED` 开关（默认**开** —— REQ-FUNC-IB-25/26/27 属 v1 范围）。

    **只读键名对应的值用于行为判定，绝不把值写入任何响应体**（IFC-IB-297）。
    """
    raw = os.environ.get("IB_VISUAL_CONFIG_ENABLED")
    if raw is None or str(raw).strip() == "":
        return True
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _read_failure_response() -> Any:
    """定义文档不可读 / 不可写 → 503（fail-closed；**不返回空文档**）。"""
    return _json(
        {
            "error": {
                "code": "dependency_unavailable",
                "message": "定义文档当前不可读（fail-closed：为满足单一真源纪律，不返回空文档）",
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _validation_failure_response(items: Any, message: str) -> Any:
    """校验不通过 → 400，逐条回执（IFC-IB-295）。"""
    return _json(
        {
            "error": {
                "code": "validation_error",
                "message": message,
                "items": [ValidationErrorItemSerializer().to_representation(i) for i in items],
            }
        },
        status.HTTP_400_BAD_REQUEST,
    )


def _get_definition_config(request: Any) -> Any:
    deps = composition.get_deps()
    try:
        ctx = _ctx_of(request)
        project_id = composition.resolve_scope(ctx).project_id
        doc = deps.definition_store.load(project_id)  # IFC-IB-288
        view = deps.definition_store.derive(doc)  # IFC-IB-291
    except ConfigError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    payload = {
        "document": DefinitionDocumentSerializer().to_representation(doc),
        "derived": definition_derived_summary(view),
        "editable_fields": sorted(deps.definition_store.editable_field_whitelist()),
        # **只登记键名，不含任何值**（凭据 / 路径值一律不回显；AC-IB-17-05 / IFC-IB-297）。
        "config_key_names": ["IB_DEFINITION_DOC_PATH", "IB_VISUAL_CONFIG_ENABLED"],
    }
    return _json(payload, status.HTTP_200_OK)


def _put_definition_config(request: Any) -> Any:
    from ib.config import document_from_json, non_editable_changes, validate_two_domains
    from ib.experts import BUILTIN_FALLBACKS

    deps = composition.get_deps()
    submitted = None
    try:
        ctx = _require_manage(request)  # 写操作需管理权限（否则 403）
        actor = ctx.authz.actor_id
        project_id = composition.resolve_scope(ctx).project_id
        raw_body = json.loads(request.body.decode("utf-8") or "{}") if request.body else {}
        form = DefinitionConfigInputSerializer(data=raw_body)
        form.is_valid(raise_exception=True)
        expected = form.validated_data.get("expected_content_hash") or None
        submitted = document_from_json(
            project_id,
            json.dumps(form.validated_data["document"], ensure_ascii=False),
            # REV-17（ADR-36）：旧文档残留的 `fallback_prompt` 键据此分级处置
            # （同内置 → 静默丢弃；不同 → fail-closed 并给出迁移路径），故必须注入。
            builtin_fallbacks=BUILTIN_FALLBACKS,
        )
        current = deps.definition_store.load(project_id)
    except ConfigError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001 - 含 JSON/DRF 校验错误：不合法的请求体 → 400
        return error_response(ValidationError(f"请求体不合法：{type(exc).__name__}"))

    changed = composition.changed_field_names(current, submitted)

    # ① 白名单：非编辑字段（拓扑 / 归属）被改动 → 400
    illegal = non_editable_changes(current, submitted)
    if illegal:
        _audit_definition_save(deps, project_id, actor, changed, "rejected", illegal)
        return _validation_failure_response(illegal, "存在不可编辑字段的变更（REQ-FUNC-IB-26）")

    # ② 完备性校验（服务端为唯一裁决者；界面预校验不作数）→ 400
    #    **REV-16-4（ADR-33）**：改用合成纯函数，与**装配路径**（`admit_two_domains`）
    #    同一校验入口，结构性消除 DEFECT-R16-02 根因（保存期漏掉工具参数校验）。
    #    **REV-17（ADR-36）**：入口升级为 `validate_two_domains`（IFC-IB-364），把**提示词域**
    #    也一并纳入 —— 此前保存期不查提示词目录，于是「页面上存得下、重启装配才炸」成立。
    #    校验对象是 `submitted`（**新提交的文档**），不是 `current` —— 查旧文档等于没查。
    #    提示词引用取**当前目录实况**（保存期不写提示词，故实况 = 生效后装配所见）。
    try:
        prompt_refs = _prompt_refs_for(deps, project_id)
    except DependencyUnavailableError as exc:
        return error_response(exc)  # 目录不可读 → 503（与 GET /api/config/prompts 同口径）
    report = validate_two_domains(
        submitted,
        known_tools=composition.known_tool_names(),
        tool_param_specs=deps.tool_param_specs(),
        prompt_refs=prompt_refs,
        builtin_fallbacks=composition.builtin_fallbacks_of(submitted),
    )
    if not report.ok:
        _audit_definition_save(deps, project_id, actor, changed, "rejected", report.errors)
        return _validation_failure_response(report.errors, "定义文档校验不通过")

    # ③ 原子写回（乐观并发）
    try:
        result = deps.definition_store.save(
            project_id, submitted, expected_content_hash=expected
        )
    except ConfigError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    if result.conflict:
        _audit_definition_save(
            deps, project_id, actor, changed, "rejected", result.errors,
            detail_code="content_hash_conflict",
        )
        return _json(
            {
                "error": {
                    "code": "conflict",
                    "message": "定义文档已被他处修改（乐观并发冲突，未覆盖）",
                    "receipt": SaveResultSerializer().to_representation(result),
                }
            },
            status.HTTP_409_CONFLICT,
        )
    if not result.ok:
        _audit_definition_save(deps, project_id, actor, changed, "rejected", result.errors)
        return _validation_failure_response(result.errors, "写回未生效")

    # ④ **以文档为准**刷新只读派生视图（AC-IB-17-03）；拓扑/注册表的生效点为**下次装配**
    #    （图编译一次常驻，运行期不得由图外输入改变拓扑 —— REQ-FUNC-IB-26 ②）。
    try:
        refreshed = deps.definition_store.load(project_id)
        deps.definitions[project_id] = refreshed
        deps.derived_views[project_id] = deps.definition_store.derive(refreshed)
    except IbError:  # noqa: BLE001 - 刷新失败不影响「已成功写回」这一事实
        pass

    # ⑤ 审计写（IFC-IB-360）：顺序 = 校验 → 落盘 → 审计写；**审计写与配置写非事务耦合**
    #    （失败不改变保存结果，但不静默 —— 见 `record_config_audit`）。
    _audit_definition_save(deps, project_id, actor, changed, "saved", ())

    log_event("definition_config", "saved", project_id=project_id)
    return _json(SaveResultSerializer().to_representation(result), status.HTTP_200_OK)


def _audit_definition_save(
    deps: Any,
    project_id: str,
    actor: str,
    changed_field_names: Any,
    result: str,
    items: Any = (),
    *,
    detail_code: str | None = None,
) -> None:
    """保存路径审计挂钩（IFC-IB-360）。

    `detail_code` **只含字段名 / 错误码**（错误项的 `code` 去重升序），**永不**含取值；
    未显式给出 `detail_code` 时由 `items` 的 `code` 派生。
    """
    codes = sorted({getattr(i, "code", "") for i in (items or ()) if getattr(i, "code", "")})
    effective_detail = detail_code if detail_code is not None else (",".join(codes) or None)
    entry = ConfigAuditEntry(
        timestamp=utc_now_iso(),
        project=project_id,
        actor=actor,
        action="definition.save",
        changed_field_names=tuple(changed_field_names or ()),
        result=result,  # type: ignore[arg-type]
        detail_code=effective_detail,
    )
    composition.record_config_audit(entry, deps=deps)


# --------------------------------------------------------------------------- #
# REV-16-4（IFC-IB-359 / 362）：配置审计与存储态只读端点
# --------------------------------------------------------------------------- #
#
#   * 仅 `Authorization` 头鉴权（`?token=` 由中间件先于路由拒绝）；
#   * `project_id` 只认**服务端结论** `ctx.authz.project_id`（ops 自身项目；
#     admin 经 `X-IB-Project` 选定，未选定为全局哨兵 `*`）—— 请求体一律忽略；
#   * **fail-closed**：审计 / 存储态不可读即 503，**不返回空集合冒充「无记录」**；
#   * **只读**：审计端点无写回配置的路径（IFC-IB-357 无 update/delete）；
#   * 存储态端点**仅暴露**存储态，**不改变**「保存 + 重启重装配」生效口径（ADR-35）。


def _query_int(request: Any, name: str, *, default: int, minimum: int = 0) -> int:
    """读取非负整数查询参数（缺省 / 非法 → `default`；负数夹到 `minimum`）。"""
    raw = request.GET.get(name) if hasattr(request, "GET") else None
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return default
    return max(minimum, value)


def storage_state_endpoint(request: Any) -> Any:
    """`GET /api/config/storage-state`（IFC-IB-362）→ `200 StorageState` | `403` | `503`。

    **单一来源 = 装配期实际选用的存储实现**（直读装配结果，IFC-IB-361）；**仅暴露**
    存储态，**不改变**生效口径，**不引入**运行期热重载（ADR-35）。
    """
    if request.method != "GET":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    deps = composition.get_deps()
    try:
        _require_manage(request)  # 非管理者 → 403（fail-closed，不臆造存储态）
        state = composition.get_storage_state(deps=deps)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    return _json(StorageStateSerializer().to_representation(state), status.HTTP_200_OK)


#: 审计端点一次扫描上限（审计为追加式且写入稀疏；取足够大以得出稳定 `total`）。
_AUDIT_TOTAL_SCAN_LIMIT = 1000


def config_audit_endpoint(request: Any) -> Any:
    """`GET /api/config/audit?limit=&offset=`（IFC-IB-359）。

    → `200 {items, total}` | `403`（归属断言失败）| `503`（fail-closed：审计存储不可读
    即明确报错，**不返回空集合冒充「无记录」**）。**只读**；承载成功与失败两类记录
    （`result ∈ {"saved","rejected"}`）；**字段白名单**：只出字段名与结果码。
    """
    if request.method != "GET":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)  # 非管理者 → 403
        project_id = ctx.authz.project_id  # 服务端结论（只认它，忽略请求体）
        store = getattr(deps, "config_audit_store", None)
        if store is None:
            raise DependencyUnavailableError(
                "配置审计存储不可用（fail-closed：不返回空集合冒充「无记录」）",
                dependency="ledger",
            )
        limit = _query_int(request, "limit", default=50, minimum=0)
        offset = _query_int(request, "offset", default=0, minimum=0)
        all_items = store.list_by_project(
            project_id, limit=_AUDIT_TOTAL_SCAN_LIMIT, offset=0
        )
        total = len(all_items)
        items = all_items[offset : offset + limit]
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    payload = {
        "items": [ConfigAuditEntrySerializer().to_representation(e) for e in items],
        "total": total,
    }
    return _json(payload, status.HTTP_200_OK)


# --------------------------------------------------------------------------- #
# REV-16-2（IFC-IB-352）：独立提示词目录端点族
# --------------------------------------------------------------------------- #
#
# 纪律（module_design §3 MOD-IB-23 REV-16-2）：
#   * 归属恒取自 `ctx.authz.project_id`（请求中的 project_id 一律忽略）；
#   * **仅 `Authorization` 头**鉴权，**不接受** `?token=`（中间件先于路由拒绝）；
#   * 目录不可读 → **503（fail-closed）**，**不返回空集合**；
#   * 校验不通过 → **400**，逐条回执 `path`/`code`/`message`（**不回显提示词正文 / 凭据**）；
#   * 乐观并发冲突 → **409**，含可读回执，**不静默覆盖**；
#   * **保存仅原子落盘，不触发运行期重建**（ADR-32 / C-IB-40：生效口径 = 服务重启后重新装配）。
# --------------------------------------------------------------------------- #

_PROMPT_LAYERS: tuple[str, ...] = ("main", "fallback")


def prompt_config_endpoint(request: Any, expert: str | None = None, layer: str | None = None) -> Any:
    """`/api/config/prompts` 端点族（IFC-IB-352）。

    * `GET  /api/config/prompts`                     → 列表（元数据 + 哈希，**不含正文**）
    * `GET  /api/config/prompts/{expert}/{layer}`    → 单层正文 + 哈希
    * `PUT  /api/config/prompts/{expert}/{layer}`    → 原子保存单层（乐观并发）
    """
    if not _visual_config_enabled():
        # 同 IFC-IB-294：键值**不出现在响应体**（只看行为）。
        return _json(
            {"error": {"code": "not_found", "message": "可视化配置未启用"}},
            status.HTTP_404_NOT_FOUND,
        )
    if expert is None and layer is None:
        if request.method == "GET":
            return _get_prompts_list(request)
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    if layer not in _PROMPT_LAYERS:
        return _json(
            {"error": {"code": "not_found", "message": "提示词层不存在（仅 main / fallback）"}},
            status.HTTP_404_NOT_FOUND,
        )
    if request.method == "GET":
        return _get_prompt_layer(request, str(expert), str(layer))
    if request.method == "PUT":
        return _put_prompt_layer(request, str(expert), str(layer))
    return _json(
        {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


def _prompt_store_for(request: Any) -> tuple[Any, Any]:
    """解析请求归属项目并取该项目提示词存储（缺失即 `DependencyUnavailableError`）。"""
    deps = composition.get_deps()
    ctx = _ctx_of(request)
    project_id = composition.resolve_scope(ctx).project_id
    store = (getattr(deps, "prompt_stores", None) or {}).get(project_id)
    if store is None:
        raise DependencyUnavailableError(
            "提示词存储未装配（fail-closed：不返回空集合）", dependency="expert_prompt_dir"
        )
    return deps, store


def _prompt_refs_for(deps: Any, project_id: str) -> tuple[Any, ...]:
    """取该项目提示词目录的**当前实况引用**（IFC-IB-345）。

    供**保存期**跨域校验使用（REV-17 / ADR-36）：定义文档保存不写提示词文件，故目录实况
    就是「保存后重启装配」所见的那份 —— 这正是本条校验的意义所在（保存即预演装配）。
    目录不可读 → `DependencyUnavailableError`（由调用方转 503，**不**降级成 500，
    也不静默当成空目录放行）。
    """
    store = (getattr(deps, "prompt_stores", None) or {}).get(project_id)
    if store is None:
        return ()
    return tuple(store.list_refs())


def _builtin_fallback_of(deps: Any, project_id: str, expert: str) -> str:
    """该专家的**代码内置兜底**（REV-17 / ADR-36）。

    取代原 `_doc_fallback_of`（后者读定义文档字段，该字段已删）：兜底层不再来自任何
    可写入口，改由 `ib.experts.builtin_fallback_for` 统一解析（与装配期**同源**）。
    """
    from ib.experts import builtin_fallback_for

    return builtin_fallback_for(expert)


def _tool_param_spec_payload(spec: Any) -> dict[str, Any]:
    return {
        "name": spec.name,
        "type": spec.type,
        "default": spec.default,
        "minimum": spec.minimum,
        "maximum": spec.maximum,
        "choices": list(spec.choices) if spec.choices else None,
    }


def _get_prompts_list(request: Any) -> Any:
    deps = composition.get_deps()
    try:
        deps, store = _prompt_store_for(request)
        refs = store.list_refs()  # IFC-IB-345（不可读 → 抛，转 503）
        project_id = getattr(store, "project_id", "")
        doc = (getattr(deps, "definitions", None) or {}).get(project_id)
    except DependencyUnavailableError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    by_expert: dict[str, dict[str, Any]] = {}
    for ref in refs:
        by_expert.setdefault(ref.expert_name, {})[ref.layer] = ref

    experts = []
    for e in getattr(doc, "experts", ()) or ():
        layers: dict[str, Any] = {}
        for layer in _PROMPT_LAYERS:
            ref = by_expert.get(e.name, {}).get(layer)
            layers[layer] = {
                "exists": bool(getattr(ref, "exists", False)),
                "content_hash": getattr(ref, "content_hash", "") if ref is not None else "",
            }
        experts.append(
            {
                "name": e.name,
                "cn_label": e.cn_label,
                "layers": layers,
                # 加成式（REV-17 / ADR-36）：代码内置兜底**只读展示**，供界面在两层文件皆缺时
                # 说明「当前生效的是什么」。它**不是**可写载体 —— 界面不为它开第二写入口。
                "builtin_fallback": _builtin_fallback_of(deps, project_id, e.name),
            }
        )

    payload = {
        "experts": experts,
        # 加成式（IFC-IB-340 / 354）：参数规格供前端生成控件；**只含声明，不含任何凭据**。
        "tool_param_specs": [
            _tool_param_spec_payload(s) for s in composition.known_tool_param_specs()
        ],
        # 既有工具名单（ADR-30）：勾选**只作用于既有工具集合**；与装配期校验同源。
        "available_tools": list(composition.known_tool_names()),
        "layout": {
            "root_key": "IB_EXPERT_PROMPT_DIR",
            "file_pattern": "<root>/<project_id>/<expert_name>/{main.md|fallback.md}",
            # REV-17（ADR-36）：`fallback.md` 亦可缺 —— 两层文件皆缺时回落到**代码内置兜底**，
            # 由 `merge_prompt_layers` 的结构保证「兜底恒非空」。
            "naming_rule": (
                "子目录名 = 专家 name；main.md 可缺，fallback.md 亦可缺"
                "（皆缺时回落代码内置兜底）"
            ),
        },
        # **只登记键名，不含任何值**（IFC-IB-348）。
        "config_key_names": ["IB_EXPERT_PROMPT_DIR", "IB_EXPERT_PROMPT_ENABLED"],
    }
    return _json(payload, status.HTTP_200_OK)


def _get_prompt_layer(request: Any, expert: str, layer: str) -> Any:
    try:
        deps, store = _prompt_store_for(request)
        project_id = getattr(store, "project_id", "")
        refs = store.list_refs()
    except DependencyUnavailableError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    ref = next(
        (r for r in refs if r.expert_name == expert and r.layer == layer), None
    )
    if ref is None or not ref.exists:
        # 「不存在」与「不属于你」**不区分**（反存在性探测；同 §1.4 第 2 条）。
        return _json(
            {"error": {"code": "not_found", "message": "提示词层不存在"}},
            status.HTTP_404_NOT_FOUND,
        )
    try:
        # REV-17（ADR-36）：兜底只取**代码内置**（与装配期同源），不再读定义文档字段。
        # 本端点只在 `ref.exists` 为真的分支里取值，故 `builtin_fallback` 在此仅作
        # `load_bundle` 的形式参数（该层文件已在，合并结果不会用到它）。
        bundle = store.load_bundle(
            expert, builtin_fallback=_builtin_fallback_of(deps, project_id, expert)
        )
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)
    content = bundle.main_prompt if layer == "main" else bundle.fallback_prompt
    if content is None:
        return _json(
            {"error": {"code": "not_found", "message": "提示词层不存在"}},
            status.HTTP_404_NOT_FOUND,
        )
    return _json({"content": content, "content_hash": ref.content_hash}, status.HTTP_200_OK)


def _prompt_result_body(result: Any) -> dict[str, Any]:
    return {
        "saved": result.saved,
        "content_hash": result.content_hash,
        "conflict": any(
            getattr(i, "code", "") == "prompt_content_hash_conflict" for i in result.errors
        ),
        "errors": [ValidationErrorItemSerializer().to_representation(i) for i in result.errors],
    }


def _put_prompt_layer(request: Any, expert: str, layer: str) -> Any:
    try:
        _require_manage(request)  # 写操作需管理权限（否则 403）
        deps, store = _prompt_store_for(request)
        project_id = getattr(store, "project_id", "")
        raw_body = json.loads(request.body.decode("utf-8") or "{}") if request.body else {}
        if not isinstance(raw_body, dict):
            raise ValidationError("请求体必须为 JSON 对象")
        content = raw_body.get("content")
        if not isinstance(content, str):
            raise ValidationError("缺少字符串字段 content")
        expected = raw_body.get("expected_hash")
        if expected is not None and not isinstance(expected, str):
            raise ValidationError("expected_hash 必须为字符串")
        doc = (getattr(deps, "definitions", None) or {}).get(project_id)
        known = {getattr(e, "name", "") for e in getattr(doc, "experts", ()) or ()}
        if known and expert not in known:
            return _json(
                {"error": {"code": "not_found", "message": "专家不存在"}},
                status.HTTP_404_NOT_FOUND,
            )
    except ConfigError:
        return _read_failure_response()
    except ValidationError as exc:
        return error_response(exc)
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    try:
        result = store.save_layer(expert, layer, content, expected_hash=expected)  # IFC-IB-344
    except DependencyUnavailableError:
        return _read_failure_response()
    except IbError as exc:
        return error_response(exc)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)

    conflict = any(getattr(i, "code", "") == "prompt_content_hash_conflict" for i in result.errors)
    if result.saved:
        # 生效口径 = 服务重启后重新装配（ADR-32）：**不**在此重建图 / 热重载。
        log_event("prompt_config", "saved", project_id=project_id, expert=expert, layer=layer)
        return _json(_prompt_result_body(result), status.HTTP_200_OK)
    if conflict:
        return _json(
            {
                "error": {
                    "code": "conflict",
                    "message": "提示词已被他处修改（乐观并发冲突，未覆盖）",
                    "receipt": _prompt_result_body(result),
                }
            },
            status.HTTP_409_CONFLICT,
        )
    return _validation_failure_response(result.errors, "提示词保存未生效")


# --------------------------------------------------------------------------- #
# R14（IFC-IB-333）：项目枚举端点（项目上下文的选择入口）
# --------------------------------------------------------------------------- #
#
# ## 该端点**不是**项目级端点
#
# 全局主体（admin）在**未选定**当前项目时 `effective_project == GLOBAL_PROJECT`（`"*"`），
# 项目级端点因此 fail-closed —— 这是刻意设计（未选项目即不泄露）。但 `GET /api/projects`
# 是 admin **唯一**的引导出口：若它也因「无匹配项目」而 fail-closed，admin 将永远无法
# 选定项目，缺陷不可自愈。故本端点对**未选定项目的全局主体**同样返回 `200`。
#
# ## 授权口径（ADR-28 / IFC-IB-333）
#
#   * 全局主体（admin，`is_global`）→ 返回**全部**已登记项目；
#   * 项目绑定主体（ops）→ **仅返回其自身项目**（`items` 长度恒为 1），**绝不枚举他项目**。
#
# 于是「ops 的可选项集合 = {自身项目}」由服务端裁定，叠加后端 `403 project_mismatch`
# （IFC-IB-334）与前端 `select` 仅 admin 可调用，共三重「结构上不可切换」。
#
# ## 数据源与授权真源
#
# 数据源 = 组合根 `Deps.projects`（`IB_CONFIG_FILE` 的 `projects.<project_id>` 经
# `_seed_projects` 装配）—— **不新增表、不经 ORM、不新增端口 / 模块**。
# 身份判定沿用既有 `_ctx_of` / `get_authz` / `is_global`，**不新增第二套授权逻辑**（ADR-22）。
# `?token=` 出现在查询串时由中间件在其之前显式 `400`（本视图不为此开例外）。


#: `project_id` 允许的字符集（供 `POST /api/projects` 校验）。
#: 收窄到「字母 / 数字 / 下划线 / 连字符」与 collection 命名口径一致，避免项目标识
#: 携带路径分隔符或空白而渗入下游（collection 名 / 前缀断言 / 文件路径拼装）。
_PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def projects_endpoint(request: Any) -> Any:
    """`GET|POST /api/projects`（IFC-IB-333 / REV-18 IFC-IB-372）。

    ## `GET`（数据源 = **项目注册表**；REV-18 口径修订，端点号 / 名 / 签名不变）

    `200 {items: [ProjectSummary]}` | `401` | `4xx`。`ProjectSummary(project_id: str,
    name: str, is_current: bool)`；`is_current` = 该项目是否等于**本请求**的
    `effective_project`（admin 未选定时为全局哨兵，故全部为 `False`）。按 `project_id`
    升序稳定输出。

    **数据源**由配置枚举快照（`Deps.projects`）**切换**为项目注册表
    （`ProjectRegistryStore.list_active()` / `load()`，ADR-37）。**授权口径与
    fail-closed 语义一字不动**：全局主体（admin）见**全部活动项目**；项目绑定主体
    （ops）**仅见自身**（`items` 长度 ≤ 1，绝不枚举他项目）。

    ## `POST`（**仅 admin**；REV-18 IFC-IB-372）

    `{project_id, name}` → `201 ProjectRegistryEntry` | `409`（`project_id` 冲突）
    | `400` | `403`。非 admin 一律服务端 **403**（ADR-42：UI 分组不作为权限机制）。
    """
    deps = composition.get_deps()
    try:
        ctx = _ctx_of(request)
        authz = get_authz(request)
        # 未认证由中间件拦下（401）；此处仅作类型收敛，**不**静默构造主体。
        if authz is None:
            return _json(
                {"error": {"code": "unauthenticated", "message": "缺少或无效的认证凭据"}},
                status.HTTP_401_UNAUTHORIZED,
            )
        if request.method == "GET":
            registry = _project_registry()
            effective = ctx.authz.project_id
            if is_global(authz):
                visible = list(registry.list_active())
            else:
                own = registry.load(authz.project_id)
                # ops 只回自身项目（且须 active）；未登记 / 已停用时不臆造记录。
                visible = [own] if own is not None and own.status == "active" else []
            items = [
                {
                    "project_id": entry.project_id,
                    "name": entry.name,
                    "is_current": entry.project_id == effective,
                }
                for entry in sorted(visible, key=lambda e: e.project_id)
            ]
            return _json({"items": items}, status.HTTP_200_OK)
        if request.method == "POST":
            _require_admin(request)
            payload = _json_body(request)
            project_id = str(payload.get("project_id") or "").strip()
            name = str(payload.get("name") or "").strip()
            if not project_id:
                raise ValidationError("缺少 project_id")
            if not name:
                raise ValidationError("缺少项目名称")
            if _PROJECT_ID_PATTERN.match(project_id) is None:
                raise ValidationError("project_id 只能含字母 / 数字 / 下划线 / 连字符（1~128 字符）")
            now = utc_now_iso()
            created = _project_registry().create(
                ProjectRegistryEntry(
                    project_id=project_id,
                    name=name,
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
            audit("project", outcome="created", status="ok", project_id=project_id)
            deps.reload_projects()
            return _json(ProjectRegistryEntrySerializer(created).data, status.HTTP_201_CREATED)
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    except IbError as exc:
        return error_response(exc)


def project_detail_endpoint(request: Any, project_id: str) -> Any:
    """`PATCH|DELETE /api/projects/{project_id}`（REV-18 IFC-IB-372；**仅 admin**）。

    * `PATCH`（`{name?, status?}`）→ `200 ProjectRegistryEntry` | `404` | `400` | `403`；
    * `DELETE`（**二次确认** `confirm_project_id` 与目标一致，否则 `400`）→
      `200 ProjectRegistryEntry`（**软删 = `status="disabled"`，数据保留、可恢复**，
      OOS-19）| `404` | `403`。

    全程仅 `Authorization` 头；非 admin 一律服务端 `403`。
    """
    try:
        _require_admin(request)
        deps = composition.get_deps()
        registry = _project_registry()
        existing = registry.load(project_id)
        if existing is None:
            raise NotFoundError("项目不存在或不在可见范围内")
        if request.method == "PATCH":
            payload = _json_body(request)
            name = payload.get("name")
            new_status = payload.get("status")
            if name is not None:
                name = str(name).strip()
                if not name:
                    raise ValidationError("项目名称不能为空")
            else:
                name = existing.name
            if new_status is not None:
                new_status = str(new_status).strip()
                if new_status not in ("active", "disabled"):
                    raise ValidationError("status 只能为 active 或 disabled")
            else:
                new_status = existing.status
            updated = registry.update(
                ProjectRegistryEntry(
                    project_id=project_id,
                    name=name,
                    status=new_status,
                    created_at=existing.created_at,
                    updated_at=utc_now_iso(),
                )
            )
            if updated is None:
                raise NotFoundError("项目不存在或不在可见范围内")
            audit("project", outcome="updated", status="ok", project_id=project_id)
            deps.reload_projects()
            return _json(ProjectRegistryEntrySerializer(updated).data, status.HTTP_200_OK)
        if request.method == "DELETE":
            payload = _json_body(request)
            confirm = str(payload.get("confirm_project_id") or "").strip()
            if confirm != project_id:
                raise ValidationError("删除确认不匹配（confirm_project_id 须与目标一致）")
            disabled = registry.disable(project_id)
            if disabled is None:
                raise NotFoundError("项目不存在或不在可见范围内")
            audit("project", outcome="disabled", status="ok", project_id=project_id)
            deps.reload_projects()
            return _json(ProjectRegistryEntrySerializer(disabled).data, status.HTTP_200_OK)
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    except IbError as exc:
        return error_response(exc)


# --------------------------------------------------------------------------- #
# R13（IFC-IB-316 ~ 321）：账户 / 会话端点
# --------------------------------------------------------------------------- #
#
# 全程**仅** `Authorization` 头鉴权（`/api/auth/login` 免鉴权是例外 —— 登录尚无令牌）；
# **不接受** `?token=`（中间件的 `forbidden_token_in_query` 先于公共路径判断，新端点自动受约束）。
#
# 响应**不回显**任何口令 / 令牌 / bcrypt 摘要；`GET /api/auth/me` 与 `GET /api/accounts`
# 只输出 `AccountSummary`（无 `password_hash`）。登录失败**统一** 401，不区分「不存在 / 口令错 / 停用」。


def _account_summary(user: Any) -> dict[str, Any]:
    """`AccountSummary` 的 JSON 形态（IFC-IB-309；**不含 password_hash**）。"""
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "project_id": user.project_id,
        "status": user.status,
        "must_change_password": bool(user.must_change_password),
    }


def _unauthenticated() -> Any:
    """统一凭据错误（401；**不区分**失败原因，防存在性 / 状态探测预言机）。"""
    return _json(
        {"error": {"code": "unauthenticated", "message": "用户名或口令不正确"}},
        status.HTTP_401_UNAUTHORIZED,
    )


def _no_content() -> Any:
    from django.http import HttpResponse

    return HttpResponse(status=204)


def _json_body(request: Any) -> dict[str, Any]:
    """解析 JSON 请求体；非法 → `ValidationError`（→ 400），**不回显原文**。"""
    raw = request.body or b""
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("请求体不是合法 JSON") from exc
    if not isinstance(data, dict):
        raise ValidationError("请求体必须是 JSON 对象")
    return data


def _client_ip(request: Any) -> str:
    """取客户端 IP（经 nginx 时优先 `X-Forwarded-For` 首跳）。仅用于限速，不作鉴权。"""
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.META.get("REMOTE_ADDR") or "").strip()


def _require_admin(request: Any) -> Any:
    """账户 CRUD 的权限前置：必须是**全局主体**（admin）且策略允许管理（→ 否则 403）。

    项目绑定账户（ops）的 `project_id` 非哨兵，故被拦在门外；授权判定仍经注入的
    `AuthzPolicy`（ADR-22），「全局」是主体属性而非第二套授权逻辑。
    """
    ctx = _ctx_of(request)
    authz = get_authz(request)
    if authz is None or not is_global(authz) or not get_policy(request).can_manage(ctx.authz):
        raise ScopeViolationError("该操作仅限管理员账户")
    return ctx


def _account_store() -> Any:
    deps = composition.get_deps()
    store = getattr(deps, "account_store", None)
    if store is None:
        raise DependencyUnavailableError("账户存储不可用", dependency="ledger")
    return store


def _project_registry() -> Any:
    """项目注册表（REV-18 ADR-37；组合根 `Deps.project_registry`）。不可用 → 503 fail-closed。"""
    deps = composition.get_deps()
    registry = getattr(deps, "project_registry", None)
    if registry is None:
        raise DependencyUnavailableError("项目注册表不可用", dependency="ledger")
    return registry


def _llm_key_store() -> Any:
    """LLM Key 存储（REV-18 ADR-38；组合根 `Deps.llm_key_store`）。不可用 → 503 fail-closed。"""
    deps = composition.get_deps()
    store = getattr(deps, "llm_key_store", None)
    if store is None:
        raise DependencyUnavailableError("LLM Key 存储不可用", dependency="ledger")
    return store


def _login_throttle() -> Any:
    """取**应用级**登录限速器（IFC-IB-326）。

    ## 为什么取装配期的那个实例，而不是每请求 `build_throttle()`

    `LoginThrottle` 的滑动窗口计数器 `_hits` 是**实例状态**：每请求新建一个实例，
    就等于每次都拿到一个空窗口 —— `record_failure()` 写进的对象在请求结束时被丢弃，
    计数**永不跨请求累积**，`check()` 恒 `allow=True`，429 分支不可达（DEFECT-R13-01）。

    正确用法是在**组合根装配期**构建一次（`Deps.login_throttle`）并跨请求复用。
    挂在 `Deps` 上即「每应用实例一份」：生产装配幂等故为单例；测试每次 `force` 装配
    得到全新空窗口，用例之间不互相泄漏计数。

    未配置 `IB_LOGIN_MAX_FAILURES` 时 `Deps.login_throttle` 为 `None` → 不启用限速
    （ADR-27 / OQ-IB-12 未裁决前不纳入默认施工）。
    """
    deps = composition.get_deps(required=False)
    return getattr(deps, "login_throttle", None) if deps is not None else None


def auth_login_endpoint(request: Any) -> Any:
    """`POST /api/auth/login`（IFC-IB-316）。

    `200 {token, expires_at, must_change_password, user}` | `401`（统一凭据错误）|
    `429`（条件性限速，OQ-IB-12）| `400`（缺参）。令牌**只在此处一次性返回**，不落库不落日志。
    """
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        payload = _json_body(request)
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        if not username or not password:
            raise ValidationError("缺少用户名或口令")
        store = _account_store()
        now = utc_now_iso()
        user = store.get_user_by_username(username)
        locked = bool(user is not None and user.locked_until and user.locked_until > now)

        # 来源 IP 维度限速（IFC-IB-326）：对**未锁定账户**的尝试生效。
        # 为什么把「取账户 + 判锁定」放在限速判定之前：账户维度锁定是**权威结论**，
        # 已锁定账户必须返回统一 401（AC-IB-29-01：不泄露「已锁定」）；若先按 IP 返回 429，
        # 就会用 429 遮蔽 401，使「账户是否已锁定」可被侧信道区分（TC-INT-118 契约破裂）。
        # 未锁定 / 未知账户仍走 IP 滑动窗口 —— 第 N 次失败后 429（TC-INT-119）。
        throttle = _login_throttle()
        client_ip = _client_ip(request)
        if throttle is not None and not locked and not throttle.check(username, client_ip).allow:
            audit("login", outcome="login_throttled", status="throttled")
            return _json(
                {
                    "error": {
                        "code": "too_many_requests",
                        "message": "登录尝试过于频繁，请稍后再试",
                    }
                },
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        verified = False
        if user is not None and not locked:
            from ib.ledger import verify_password

            verified = verify_password(password, user.password_hash)

        if user is None or not verified:
            if user is not None and not locked:
                store.record_login_failure(user.user_id, now=now)
            if throttle is not None:
                throttle.record_failure(client_ip)
            audit("login", outcome="login_failed", status="rejected")
            return _unauthenticated()

        if user.status != "active":
            audit("login", outcome="login_failed", status="disabled")
            return _unauthenticated()

        store.reset_login_failures(user.user_id)
        if throttle is not None:
            throttle.record_success(client_ip)

        settings = load_account_settings()
        token = new_session_token()
        expires_at = iso_plus_seconds(settings.session_ttl_seconds)
        store.issue_session(user.user_id, token_digest(token), expires_at=expires_at)
        audit("login", outcome="login_success", status="ok")
        return _json(
            {
                "token": token,
                "expires_at": expires_at,
                "must_change_password": bool(user.must_change_password),
                "user": _account_summary(user),
            },
            status.HTTP_200_OK,
        )
    except IbError as exc:
        return error_response(exc)


def auth_logout_endpoint(request: Any) -> Any:
    """`POST /api/auth/logout`（IFC-IB-317）→ `204`（撤销当前会话）| `401`。"""
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    token = parse_bearer(request.META.get("HTTP_AUTHORIZATION", ""))
    if not token:
        return _unauthenticated()
    try:
        _account_store().revoke_session(token_digest(token), now=utc_now_iso())
        audit("logout", outcome="logout", status="ok")
        return _no_content()
    except IbError as exc:
        return error_response(exc)


def auth_me_endpoint(request: Any) -> Any:
    """`GET /api/auth/me`（IFC-IB-318）→ `200 {user_id, username, role, project_id, must_change_password}`。"""
    if request.method != "GET":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        ctx = _ctx_of(request)
        user = _account_store().get_user(ctx.authz.actor_id)
        if user is None:
            return _unauthenticated()
        return _json(
            {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role,
                "project_id": user.project_id,
                "must_change_password": bool(user.must_change_password),
            },
            status.HTTP_200_OK,
        )
    except IbError as exc:
        return error_response(exc)


def auth_change_password_endpoint(request: Any) -> Any:
    """`POST /api/auth/change-password`（IFC-IB-319）。

    `{old_password, new_password}` → `200`（成功后撤销**其他**会话并清除改密态）|
    `400`（强度不满足 / 原口令不正确，**不回显口令**）| `401` | `403`（改密态下仅此端点等）。
    """
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        ctx = _ctx_of(request)
        payload = _json_body(request)
        old_password = str(payload.get("old_password") or "")
        new_password = str(payload.get("new_password") or "")
        store = _account_store()
        user = store.get_user(ctx.authz.actor_id)
        if user is None:
            return _unauthenticated()
        from ib.ledger import hash_password, verify_password

        if not verify_password(old_password, user.password_hash):
            audit("change_password", outcome="bad_old_password", status="rejected")
            return _json(
                {"error": {"code": "bad_old_password", "message": "原口令不正确"}},
                status.HTTP_400_BAD_REQUEST,
            )
        problem = validate_password_strength(new_password)
        if problem:
            return _json(
                {"error": {"code": "weak_password", "message": problem}},
                status.HTTP_400_BAD_REQUEST,
            )
        if new_password == old_password:
            return _json(
                {"error": {"code": "weak_password", "message": "新口令不得与原口令相同"}},
                status.HTTP_400_BAD_REQUEST,
            )
        store.set_password(user.user_id, hash_password(new_password), must_change=False)
        token = parse_bearer(request.META.get("HTTP_AUTHORIZATION", ""))
        keep = token_digest(token) if token else None
        store.revoke_sessions_for_user(user.user_id, now=utc_now_iso(), keep_digest=keep)
        audit("change_password", outcome="password_changed", status="ok")
        return _json({"ok": True, "must_change_password": False}, status.HTTP_200_OK)
    except IbError as exc:
        return error_response(exc)


def auth_session_renew_endpoint(request: Any) -> Any:
    """`POST /api/auth/session/renew`（IFC-IB-320）→ `200 {expires_at}` | `401`（fail-closed）。

    仅当剩余有效期低于 `IB_SESSION_RENEW_WINDOW_SECONDS` 时才真正延长（避免会话无限续期）。
    """
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    token = parse_bearer(request.META.get("HTTP_AUTHORIZATION", ""))
    if not token:
        return _unauthenticated()
    try:
        now = utc_now_iso()
        store = _account_store()
        digest = token_digest(token)
        session = store.resolve_session(digest, now=now)
        if session is None:
            return _unauthenticated()
        settings = load_account_settings()
        remaining = (parse_iso(session.expires_at) - parse_iso(now)).total_seconds()
        if remaining > settings.renew_window_seconds:
            return _json({"expires_at": session.expires_at}, status.HTTP_200_OK)
        new_expires = iso_plus_seconds(settings.session_ttl_seconds)
        renewed = store.renew_session(digest, new_expires_at=new_expires, now=now)
        if renewed is None:
            return _unauthenticated()
        audit("session", outcome="renewed", status="ok")
        return _json({"expires_at": renewed.expires_at}, status.HTTP_200_OK)
    except IbError as exc:
        return error_response(exc)


def accounts_endpoint(request: Any) -> Any:
    """`GET|POST /api/accounts`（IFC-IB-321，**仅 admin**）。

    GET → `200 {items: [AccountSummary]}`（`?project_id=` 可选过滤，缺省 = 全量）；
    POST → `201 AccountSummary` | `409`（用户名冲突）| `400`（强度 / 绑定缺失）| `403`。

    **REV-18（IFC-IB-373 / ADR-40 ②）**：POST **增前置校验** —— 目标 `project_id` 须在
    **项目注册表**（ADR-37）存在且为 `active`，否则 `422`（**顺序依赖：先建项目、后建账号**；
    **不静默创建无主账号**，REQ-FUNC-IB-45）。
    """
    try:
        _require_admin(request)
        store = _account_store()
        if request.method == "GET":
            raw_project = (request.GET.get("project_id") or "").strip()
            users = store.list_users(raw_project or None)
            return _json({"items": [_account_summary(u) for u in users]}, status.HTTP_200_OK)
        if request.method == "POST":
            payload = _json_body(request)
            username = str(payload.get("username") or "").strip()
            password = str(payload.get("password") or "")
            project_id = str(payload.get("project_id") or "").strip()
            role = str(payload.get("role") or "ops").strip() or "ops"
            if not username or not password:
                raise ValidationError("缺少用户名或口令")
            if role != "ops":
                raise ValidationError("账户角色只能为 ops（管理员由种子产生）")
            if not project_id:
                raise ValidationError("ops 账户必须绑定 project_id")
            # REV-18：目标项目须在注册表存在且 active（否则 422；fail-closed，不建无主账号）。
            registry = _project_registry()
            target = registry.load(project_id)
            if target is None or target.status != "active":
                return _json(
                    {
                        "error": {
                            "code": "project_not_active",
                            "message": "目标项目不存在或未启用（请先创建项目再建账号）",
                        }
                    },
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            problem = validate_password_strength(password)
            if problem:
                return _json(
                    {"error": {"code": "weak_password", "message": problem}},
                    status.HTTP_400_BAD_REQUEST,
                )
            from ib.ledger import hash_password

            user = store.create_user(username, hash_password(password), "ops", project_id)
            audit("account", outcome="created", status="ok", project_id=project_id)
            return _json(_account_summary(user), status.HTTP_201_CREATED)
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    except IbError as exc:
        return error_response(exc)


def account_detail_endpoint(request: Any, user_id: str) -> Any:
    """`PATCH|DELETE /api/accounts/{user_id}`（REV-18 IFC-IB-373；**仅 admin**）。

    * `PATCH`（`{project_id?, username?, status?}`；**不回显任何凭据**）→
      `200 AccountSummary` | `404` | `400` | `403`。`project_id` 重绑的目标须在注册表
      存在且 `active`（否则 `400`；由**服务层**校验，端口层不做跨表断言）。
    * `DELETE`（**二次确认** `confirm_username` 与目标一致，否则 `400`；**禁删 `admin`
      或最后一个有效 `admin`** → `409`）→ `200 AccountSummary`（**软删 = `status="disabled"`**）
      | `404` | `403`。

    软删**复用** `set_status`（`AccountStore` 端口方法集不变）；停用后撤销其全部会话。
    """
    try:
        _require_admin(request)
        store = _account_store()
        target = store.get_user(user_id)
        if target is None:
            raise NotFoundError("账户不存在或不在可见范围内")
        if request.method == "PATCH":
            payload = _json_body(request)
            project_id = payload.get("project_id")
            username = payload.get("username")
            new_status = payload.get("status")

            rebind_project: str | None = None
            if project_id is not None:
                rebind_project = str(project_id).strip()
                if not rebind_project:
                    raise ValidationError("project_id 不能为空")
                entry = _project_registry().load(rebind_project)
                if entry is None or entry.status != "active":
                    raise ValidationError("目标项目不存在或未启用")

            if username is not None:
                username = str(username).strip()
                if not username:
                    raise ValidationError("用户名不能为空")

            if new_status is not None:
                new_status = str(new_status).strip()
                if new_status not in ("active", "disabled"):
                    raise ValidationError("status 只能为 active 或 disabled")

            updated = store.update_user(
                user_id,
                project_id=rebind_project,
                username=username,
                status=new_status,
            )
            if updated is None:
                raise NotFoundError("账户不存在或不在可见范围内")
            if new_status == "disabled":
                store.revoke_sessions_for_user(user_id, now=utc_now_iso())
            audit("account", outcome="updated", status="ok")
            return _json(_account_summary(updated), status.HTTP_200_OK)
        if request.method == "DELETE":
            payload = _json_body(request)
            confirm = str(payload.get("confirm_username") or "").strip()
            if confirm != target.username:
                raise ValidationError("删除确认不匹配（confirm_username 须与目标一致）")
            if target.role == "admin":
                # 禁删 admin 或最后一个有效 admin（OQ-IB-29；ADR-40 ①）——服务层判定。
                raise ConflictError("禁止删除管理员账户（含最后一个有效管理员）")
            updated = store.set_status(user_id, "disabled")
            store.revoke_sessions_for_user(user_id, now=utc_now_iso())
            audit("account", outcome="disabled", status="ok")
            return _json(_account_summary(updated), status.HTTP_200_OK)
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    except IbError as exc:
        return error_response(exc)


def llm_key_endpoint(request: Any) -> Any:
    """`GET|PUT|DELETE /api/llm-key`（REV-18 IFC-IB-374；**仅 admin**）。

    * `GET` → `200 LlmKeyStatus`（`configured` / `masked` / `updated_at`；**不含明文**）| `403`；
    * `PUT`（`{secret}`；**唯一写入口**）→ `200 LlmKeyStatus`（**不回显明文**）| `400`（空值）| `403`；
    * `DELETE` → `204`（清空单行）| `403`。

    **凭据纪律（C-IB-42 / REQ-NFR-IB-20）**：错误体 / 日志**不回显明文 / 掩码 / 前缀**；
    Key **不入 `.env` / 不进 git / 不进命令行**。**生效 = 保存 + 服务重启重装配**（ADR-32；
    **重启由用户手工执行**，本层不做运行期热重载）。
    """
    try:
        _require_admin(request)
        store = _llm_key_store()
        if request.method == "GET":
            return _json(LlmKeyStatusSerializer(store.status()).data, status.HTTP_200_OK)
        if request.method == "PUT":
            payload = _json_body(request)
            secret = str(payload.get("secret") or "").strip()
            if not secret:
                raise ValidationError("secret 不能为空")
            result = store.set(secret)
            # 审计只记「已更新」，**绝不**记录 Key 值 / 掩码 / 前缀。
            audit("llm_key", outcome="updated", status="ok")
            return _json(LlmKeyStatusSerializer(result).data, status.HTTP_200_OK)
        if request.method == "DELETE":
            store.clear()
            audit("llm_key", outcome="cleared", status="ok")
            return _no_content()
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    except IbError as exc:
        return error_response(exc)


def account_disable_endpoint(request: Any, user_id: str) -> Any:
    """`POST /api/accounts/{user_id}/disable`（IFC-IB-321）→ `200 AccountSummary`（并撤销其全部会话）。"""
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        _require_admin(request)
        store = _account_store()
        if store.get_user(user_id) is None:
            raise NotFoundError("账户不存在或不在可见范围内")
        updated = store.set_status(user_id, "disabled")
        store.revoke_sessions_for_user(user_id, now=utc_now_iso())
        audit("account", outcome="disabled", status="ok")
        return _json(_account_summary(updated), status.HTTP_200_OK)
    except IbError as exc:
        return error_response(exc)


def account_reset_password_endpoint(request: Any, user_id: str) -> Any:
    """`POST /api/accounts/{user_id}/reset-password`（IFC-IB-321，**条件性** OQ-IB-14）。

    `{new_password}` → `200 {user_id, must_change_password: true}`。新口令**不落日志**；
    重置后撤销其全部会话，并强制其下次登录改密。
    """
    if request.method != "POST":
        return _json(
            {"error": {"code": "method_not_allowed", "message": "不支持的方法"}},
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        _require_admin(request)
        payload = _json_body(request)
        new_password = str(payload.get("new_password") or "")
        store = _account_store()
        if store.get_user(user_id) is None:
            raise NotFoundError("账户不存在或不在可见范围内")
        problem = validate_password_strength(new_password)
        if problem:
            return _json(
                {"error": {"code": "weak_password", "message": problem}},
                status.HTTP_400_BAD_REQUEST,
            )
        from ib.ledger import hash_password

        store.set_password(user_id, hash_password(new_password), must_change=True)
        store.revoke_sessions_for_user(user_id, now=utc_now_iso())
        audit("account", outcome="password_reset", status="ok")
        return _json({"user_id": user_id, "must_change_password": True}, status.HTTP_200_OK)
    except IbError as exc:
        return error_response(exc)
