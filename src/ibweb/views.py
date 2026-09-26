"""
@module MOD-IB-23
@implements IFC-IB-242 ~ IFC-IB-249（HTTP 端点）
            IFC-IB-283（R2）`GET /api/files/{doc_id}/images/{image_id}` 页面图字节
@depends MOD-IB-23（authz/composition/serializers/sse）, MOD-IB-11/12/13/14/15/22（服务）
@author sub_agent_software_developer

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

from typing import Any

from rest_framework import serializers, status

from ib.core import (
    BlobRef,
    ConflictError,
    DependencyUnavailableError,
    DocStatus,
    IbError,
    NotFoundError,
    ScopeViolationError,
    ValidationError,
)
from ib.observability import log_event
from ibweb import composition
from ibweb.authz import REQUEST_CTX_ATTR, get_policy
from ibweb.serializers import (
    DeleteReportSerializer,
    DocumentRecordSerializer,
    EgressDescriptorSerializer,
    FileListEnvelopeSerializer,
    HealthStatusSerializer,
    RebuildJobSerializer,
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
    "chat_stream_endpoint",
    "healthz_endpoint",
    "healthz_deps_endpoint",
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

    只声明 `kb_id`：`project_id` **刻意不接受**（见模块文档「project_id 的唯一来源」）。
    """

    kb_id = serializers.CharField(required=True, max_length=64, allow_blank=False)


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
        form = UploadInputSerializer(data={"kb_id": request.POST.get("kb_id", "")})
        form.is_valid(raise_exception=True)
        kb_id = str(form.validated_data["kb_id"])

        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError("缺少文件字段 file")

        scope = composition.resolve_scope(ctx)
        # 归属断言先行：越权请求**不得**在磁盘或台账留下任何痕迹
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
        query = FileListQuerySerializer(data=dict(request.GET))
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
    """
    from ibweb.sse import streaming_sse_response

    deps = composition.get_deps()
    ctx = _ctx_of(request)
    if not get_policy(request).can_query(ctx.authz):
        return error_response(ScopeViolationError("当前主体无问答权限"))

    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    if not query:
        return error_response(ValidationError("缺少查询参数 q"))

    session_id = (request.GET.get("session_id") or "default").strip() or "default"
    try:
        orchestrator = deps.orchestrator_for(ctx.authz.project_id)
    except IbError as exc:
        return error_response(exc)

    def _events() -> Any:
        log_event("chat", "started", project_id=ctx.authz.project_id, session_id=session_id)
        yield from orchestrator.run(query, ctx=ctx, session_key=ctx.session_key)

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
