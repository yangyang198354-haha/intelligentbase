# MOD-012 / implements IFC-001~012（资料库目录、移动、修订、批量上传端点）；IFC-007 的 PATCH 分支由 views.file_detail_endpoint 委托至此
"""资料库 HTTP 层：薄层，只做“请求翻译 -> 调 `ib.library` / `ib.lifecycle` -> 异常翻状态码”。

* 鉴权：`Authorization: Bearer`（中间件已解出）；写端点前置 `_require_manage`（无权限 403），
  浏览端点只要求已认证主体（不要求管理权限，CL-008/OQ-07）。`?token=` 等一律由既有中间件 400。
* 作用域：`composition.resolve_scope(ctx)`；`kb_id == project_id`。`project_id` 只取服务端结论。
* 错误体沿用 `{"error": {"code", "message"}}`；冲突附同级键 `conflicts`，校验限额附 `error.details`。
  状态码：校验 400 / 无权限 403 / 不存在或不属于本项目 404 / 冲突 409 / 依赖不可用 503。
* 按资源 id 访问非本项目资源 -> 404（与“不存在”不可区分，CL-010）。
"""

from __future__ import annotations

import re
from typing import Any

from rest_framework import status

from ib.core import NotFoundError
from ib.core.library import (
    EntryRef,
    LibraryConflictError,
    LibraryValidationError,
    NameClash,
)
from ib.lifecycle import RejectedUpload
from ib.library.uploads import ManifestEntry
from ibweb import composition
from ibweb.authz import get_policy
from ibweb.serializers import LibraryFileSerializer, LibraryFolderSerializer
from ibweb.views import _ctx_of, _json, _json_body, _require_manage, error_response

__all__ = [
    "library_endpoint",
    "library_folders_endpoint",
    "library_folder_endpoint",
    "library_move_endpoint",
    "rename_file_endpoint",
    "file_revision_endpoint",
    "uploads_endpoint",
    "upload_item_endpoint",
    "upload_batch_endpoint",
]

_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ACTIONS = ("overwrite", "skip", "rename")
_MAX_MOVE_ENTRIES = 200
_MAX_PAGE_SIZE = 100


# --------------------------------------------------------------------------- #
# 通用辅助
# --------------------------------------------------------------------------- #


def _bad(message: str) -> LibraryValidationError:
    return LibraryValidationError(message, code="bad_request")


def _check_id(value: Any, *, allow_empty: bool = False, what: str = "id") -> str:
    """ID 参数格式：32 位小写十六进制（或空串 = 根）；其余 -> 400 bad_request。"""
    if not isinstance(value, str) or not (_ID_RE.match(value) or (allow_empty and value == "")):
        raise _bad(f"参数 {what} 格式不合法")
    return value


def _info(kind: str, entry_id: str, name: str) -> dict[str, str]:
    return {"kind": kind, "id": entry_id, "name": name}


def _conflicts_of(exc: LibraryConflictError) -> list[dict[str, Any]]:
    rel_paths = list((exc.details or {}).get("rel_paths", []) or [])
    out: list[dict[str, Any]] = []
    for i, clash in enumerate(exc.clashes):
        item: dict[str, Any] = {"existing": _info(clash.kind, clash.entry_id, clash.name)}
        if i < len(exc.initiators):
            who = exc.initiators[i]
            item["entry"] = _info(who.kind, who.entry_id, who.name)
        if i < len(rel_paths):
            item["rel_path"] = rel_paths[i]
        out.append(item)
    return out


def _error(exc: BaseException, *, entry: NameClash | None = None) -> Any:
    """目录域异常 -> 响应（携带 `conflicts` / `details`）；其余异常走既有单点映射。"""
    if isinstance(exc, LibraryConflictError):
        body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
        conflicts = _conflicts_of(exc)
        if entry is not None:
            for item in conflicts:
                item.setdefault("entry", _info(entry.kind, entry.entry_id, entry.name))
        if conflicts:
            body["conflicts"] = conflicts
        return _json(body, status.HTTP_409_CONFLICT)
    if isinstance(exc, LibraryValidationError):
        error: dict[str, Any] = {"code": exc.code, "message": exc.message}
        if exc.details:
            error["details"] = dict(exc.details)
        return _json({"error": error}, status.HTTP_400_BAD_REQUEST)
    return error_response(exc)


def _method_not_allowed() -> Any:
    return _json({"error": {"code": "method_not_allowed", "message": "不支持的方法"}}, status.HTTP_405_METHOD_NOT_ALLOWED)


def _int_param(raw: Any, *, name: str, default: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(str(raw))
    except ValueError as exc:
        raise _bad(f"参数 {name} 必须是整数") from exc


def _str_field(body: dict[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = body.get(key)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise _bad(f"字段 {key} 缺失或类型不对")
    return value


def _resolutions_of(body: dict[str, Any]) -> dict[str, str]:
    raw = body.get("resolutions")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise _bad("resolutions 必须是对象")
    for key, action in raw.items():
        if not isinstance(key, str) or action not in _ACTIONS:
            raise _bad("resolutions 的取值必须是 overwrite / skip / rename")
    return dict(raw)


def _folder_json(folder: Any) -> dict[str, Any]:
    return dict(LibraryFolderSerializer(folder).data)


# --------------------------------------------------------------------------- #
# IFC-001 / 002 / 003 / 004 / 005 / 006：目录
# --------------------------------------------------------------------------- #


def library_endpoint(request: Any) -> Any:
    """`GET /api/library` —— 浏览（已认证成员即可）。"""
    if request.method != "GET":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _ctx_of(request)
        folder_id = _check_id(request.GET.get("folder_id", ""), allow_empty=True, what="folder_id")
        page = _int_param(request.GET.get("page"), name="page", default=1)
        if page < 1:
            raise _bad("参数 page 必须 >= 1")
        page_size = min(_int_param(request.GET.get("page_size"), name="page_size", default=50), _MAX_PAGE_SIZE)
        scope = composition.resolve_scope(ctx)
        view = deps.library.browse(scope, folder_id, page=page, page_size=page_size)
        can_manage = bool(get_policy(request).can_manage(ctx.authz))
    except Exception as exc:  # noqa: BLE001 - 统一经 _error 单点映射
        return _error(exc)
    items = [_folder_json(f) for f in view.folders] + [dict(LibraryFileSerializer(v).data) for v in view.files]
    return _json(
        {
            "folder": _folder_json(view.folder) if view.folder is not None else None,
            "breadcrumb": [{"folder_id": c.folder_id, "name": c.name} for c in view.breadcrumb],
            "items": items,
            "total": view.total,
            "page": view.page,
            "page_size": view.page_size,
            "permissions": {"can_manage": can_manage},
        },
        status.HTTP_200_OK,
    )


def library_folders_endpoint(request: Any) -> Any:
    """`POST /api/library/folders` —— 新建文件夹。"""
    if request.method != "POST":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        body = _json_body(request)
        parent_id = _check_id(body.get("parent_id", ""), allow_empty=True, what="parent_id")
        name = _str_field(body, "name")
        folder = deps.library.create_folder(composition.resolve_scope(ctx), parent_id, name)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _json(_folder_json(folder), status.HTTP_201_CREATED)


def library_folder_endpoint(request: Any, folder_id: str) -> Any:
    """`GET|PATCH|DELETE /api/library/folders/{folder_id}` —— 详情 / 重命名 / 分步删除。"""
    deps = composition.get_deps()
    try:
        if request.method == "GET":
            ctx = _ctx_of(request)
            detail = deps.library.folder_detail(
                composition.resolve_scope(ctx), _check_id(folder_id, what="folder_id")
            )
            return _json(
                {
                    "folder": _folder_json(detail.folder),
                    "subtree_folders": detail.subtree_folders,
                    "subtree_files": detail.subtree_files,
                },
                status.HTTP_200_OK,
            )
        if request.method == "PATCH":
            ctx = _require_manage(request)
            body = _json_body(request)
            folder = deps.library.rename_folder(
                composition.resolve_scope(ctx), _check_id(folder_id, what="folder_id"), _str_field(body, "name")
            )
            return _json(_folder_json(folder), status.HTTP_200_OK)
        if request.method == "DELETE":
            ctx = _require_manage(request)
            body = _json_body(request)
            if body.get("confirm") is not True:
                raise LibraryValidationError("删除文件夹需要二次确认（confirm=true）", code="confirm_required")
            max_files = body.get("max_files")
            if max_files is not None and (
                isinstance(max_files, bool) or not isinstance(max_files, int) or not 1 <= max_files <= 500
            ):
                raise _bad("max_files 必须是 1..500 的整数")
            step = deps.library.delete_folder_step(
                composition.resolve_scope(ctx), _check_id(folder_id, what="folder_id"), max_files=max_files
            )
            return _json(
                {
                    "done": step.done,
                    "deleted_files": step.deleted_files,
                    "deleted_folders": step.deleted_folders,
                    "failed": [
                        {"doc_id": f.doc_id, "name": f.name, "path": f.path, "error_code": f.error_code}
                        for f in step.failed
                    ],
                    "remaining_files": step.remaining_files,
                },
                status.HTTP_200_OK,
            )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _method_not_allowed()


def library_move_endpoint(request: Any) -> Any:
    """`POST /api/library/move` —— 移动文件 / 文件夹（单事务全有全无）。"""
    if request.method != "POST":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        body = _json_body(request)
        raw_entries = body.get("entries")
        if not isinstance(raw_entries, list) or not 1 <= len(raw_entries) <= _MAX_MOVE_ENTRIES:
            raise _bad(f"entries 必须是 1..{_MAX_MOVE_ENTRIES} 项的数组")
        entries: list[EntryRef] = []
        for item in raw_entries:
            if not isinstance(item, dict) or item.get("kind") not in ("file", "folder"):
                raise _bad("entries 的每一项需含 kind（file / folder）与 id")
            entries.append(EntryRef(item["kind"], _check_id(item.get("id"), what="entries.id")))
        target = _check_id(body.get("target_folder_id", ""), allow_empty=True, what="target_folder_id")
        outcome = deps.library.move(composition.resolve_scope(ctx), entries, target, _resolutions_of(body))
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    ref_json = lambda r: {"kind": r.kind, "id": r.entry_id}  # noqa: E731
    return _json(
        {
            "moved": [ref_json(r) for r in outcome.moved],
            "skipped": [ref_json(r) for r in outcome.skipped],
            "renamed": [{"id": r.entry_id, "kind": r.kind, "new_name": n} for r, n in outcome.renamed],
            "overwritten": [{"id": d} for d in outcome.overwritten_doc_ids],
        },
        status.HTTP_200_OK,
    )


# --------------------------------------------------------------------------- #
# IFC-007 / 008 / 009：文件改名与更新
# --------------------------------------------------------------------------- #


def rename_file_endpoint(request: Any, doc_id: str) -> Any:
    """`PATCH /api/files/{doc_id}` —— 文件重命名（不改三时间与状态；不得改扩展名）。"""
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        body = _json_body(request)
        scope = composition.resolve_scope(ctx)
        record = deps.library.rename_file(scope, _check_id(doc_id, what="doc_id"), _str_field(body, "name"))
        item = dict(LibraryFileSerializer(deps.library.file_view(scope, record)).data)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _json(item, status.HTTP_200_OK)


def file_revision_endpoint(request: Any, doc_id: str) -> Any:
    """`POST|DELETE /api/files/{doc_id}/revision` —— 更新文件内容 / 丢弃未完成或失败的更新。"""
    deps = composition.get_deps()
    live = None
    try:
        ctx = _require_manage(request)
        scope = composition.resolve_scope(ctx)
        doc_id = _check_id(doc_id, what="doc_id")
        live = deps.ledger.get_document(scope, doc_id)
        if live is None or live.revision_of is not None:
            raise NotFoundError("文件不存在或不在当前项目内")  # 含跨项目：与“不存在”不可区分
        if request.method == "POST":
            upload = request.FILES.get("file")
            if upload is None:
                raise _bad("缺少文件字段 file")
            on_conflict = request.POST.get("on_conflict", "fail") or "fail"
            if on_conflict not in ("fail", "rename"):
                raise _bad("on_conflict 必须是 fail 或 rename")
            head = upload.read(4096)
            upload.seek(0)
            verdict = deps.lifecycle.classify_upload(upload.name or "", int(upload.size), head)
            if isinstance(verdict, RejectedUpload):
                raise LibraryValidationError(verdict.message, code=verdict.reason.value.lower())
            result = deps.lifecycle.submit_revision(
                ctx, doc_id, verdict, data=upload, new_name=upload.name or "", on_conflict=on_conflict
            )
            if not result.changed:
                return _json({"changed": False, "reason": "CONTENT_UNCHANGED"}, status.HTTP_200_OK)
            fresh = deps.ledger.get_document(scope, doc_id) or result.live
            return _json(
                {
                    "changed": True,
                    "item": dict(LibraryFileSerializer(deps.library.file_view(scope, fresh)).data),
                    "final_name": result.final_name,
                },
                status.HTTP_202_ACCEPTED,
            )
        if request.method == "DELETE":
            discarded = deps.lifecycle.discard_revision(scope, doc_id)
            return _json({"discarded": bool(discarded)}, status.HTTP_200_OK)
    except Exception as exc:  # noqa: BLE001
        entry = NameClash("file", live.doc_id, live.doc_name) if live is not None else None
        return _error(exc, entry=entry)
    return _method_not_allowed()


# --------------------------------------------------------------------------- #
# IFC-010 / 011 / 012：批量上传
# --------------------------------------------------------------------------- #


def uploads_endpoint(request: Any) -> Any:
    """`POST /api/uploads` —— 批次计划（dry_run）/ 提交；任何 4xx 都不产生批次、目录或文件。"""
    if request.method != "POST":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        body = _json_body(request)
        target = _check_id(body.get("target_folder_id", ""), allow_empty=True, what="target_folder_id")
        dry_run = body.get("dry_run", False)
        if not isinstance(dry_run, bool):
            raise _bad("dry_run 必须是布尔值")
        raw_entries = body.get("entries")
        if not isinstance(raw_entries, list):
            raise _bad("entries 必须是数组")
        entries: list[ManifestEntry] = []
        for raw in raw_entries:
            if not isinstance(raw, dict):
                raise _bad("entries 的每一项必须是对象")
            idx, size, rel = raw.get("client_idx"), raw.get("size"), raw.get("rel_path")
            if isinstance(idx, bool) or not isinstance(idx, int) or isinstance(size, bool) or not isinstance(size, int):
                raise _bad("client_idx / size 必须是整数")
            if not isinstance(rel, str):
                raise _bad("rel_path 必须是字符串")
            entries.append(ManifestEntry(idx, rel, size))
        plan = deps.uploads.plan(
            ctx,
            composition.resolve_scope(ctx),
            target_folder_id=target,
            entries=entries,
            resolutions=_resolutions_of(body),
            commit=not dry_run,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _json(
        {
            "batch_id": plan.batch_id,
            "total": plan.total,
            "limits": {
                "max_files": plan.limits.max_files,
                "max_total_bytes": plan.limits.max_total_bytes,
                "max_depth": plan.limits.max_depth,
                "max_file_bytes": plan.limits.max_file_bytes,
            },
            "items": [
                {
                    "client_idx": p.client_idx,
                    "rel_path": p.rel_path,
                    "final_rel_path": p.final_rel_path,
                    "action": p.action,
                    "reason_code": p.reason_code,
                    "target_doc_id": p.target_doc_id,
                }
                for p in plan.items
            ],
            "conflicts": [
                {"rel_path": c.rel_path, "kind": c.kind, "existing_id": c.existing_id, "existing_name": c.existing_name}
                for c in plan.conflicts
            ],
            "accepted_count": plan.accepted_count,
            "skipped_count": plan.skipped_count,
        },
        status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED,
    )


def _multipart_file(request: Any) -> Any:
    """取 multipart 的 `file` 字段。Django 只为 POST 填充 `request.FILES`，PUT 需显式解析。"""
    if request.method == "POST":
        return request.FILES.get("file")
    if not (request.content_type or "").startswith("multipart/form-data"):
        raise _bad("请求体必须是 multipart/form-data")
    from django.http.multipartparser import MultiPartParser, MultiPartParserError

    try:
        _, files = MultiPartParser(request.META, request, request.upload_handlers, request.encoding).parse()
    except MultiPartParserError as exc:
        raise _bad("multipart 请求体无法解析") from exc
    return files.get("file")


def upload_item_endpoint(request: Any, batch_id: str, client_idx: int) -> Any:
    """`PUT /api/uploads/{batch_id}/items/{client_idx}` —— 逐文件上传（幂等）。"""
    if request.method != "PUT":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        scope = composition.resolve_scope(ctx)
        batch_id = _check_id(batch_id, what="batch_id")
        if int(client_idx) < 0:
            raise _bad("client_idx 必须 >= 0")
        upload = _multipart_file(request)
        if upload is None:
            raise _bad("缺少文件字段 file")
        head = upload.read(4096)
        upload.seek(0)
        result = deps.uploads.accept_item(
            ctx,
            scope,
            batch_id,
            int(client_idx),
            filename=upload.name or "",
            size_bytes=int(upload.size),
            head=head,
            data=upload,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _json(
        {
            "client_idx": result.client_idx,
            "state": result.state,
            "reason_code": result.reason_code,
            "doc_id": result.doc_id,
            "final_rel_path": result.final_rel_path,
        },
        status.HTTP_200_OK,
    )


def upload_batch_endpoint(request: Any, batch_id: str) -> Any:
    """`GET /api/uploads/{batch_id}` —— 批次汇总（页面刷新后恢复）。"""
    if request.method != "GET":
        return _method_not_allowed()
    deps = composition.get_deps()
    try:
        ctx = _require_manage(request)
        summary = deps.uploads.summary(composition.resolve_scope(ctx), _check_id(batch_id, what="batch_id"))
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return _json(
        {
            "batch_id": summary.batch.batch_id,
            "target_folder_id": summary.batch.target_folder_id,
            "total": summary.total,
            "accepted": summary.accepted,
            "skipped": summary.skipped,
            "failed": summary.failed,
            "pending": summary.pending,
            "items": [
                {
                    "client_idx": i.client_idx,
                    "rel_path": i.rel_path,
                    "final_rel_path": i.final_rel_path,
                    "state": i.state,
                    "reason_code": i.reason_code,
                    "doc_id": i.doc_id,
                }
                for i in summary.items
            ],
        },
        status.HTTP_200_OK,
    )

