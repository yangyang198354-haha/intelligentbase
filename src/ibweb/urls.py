"""
@module MOD-IB-23
@implements IFC-IB-242 ~ IFC-IB-249 路由表
            IFC-IB-283（R2）`/api/files/{doc_id}/images/{image_id}` 路由
@depends MOD-IB-23（views）
@author software-developer

URLconf（路径 → 视图的**全量**映射）。

## 为什么用显式 `path()` 列表，不用 `DefaultRouter`

DRF 的 `DefaultRouter` 会按视图集自动生成 URL（含 `.json` 后缀变体、`api-root` 页面）。
自动生成意味着**路径拼写不再出现在代码评审的 diff 里** —— 而路径是对外契约的一部分，
改一个字符就要前端同步改。把每条路径写出来，评审时能逐条对照 module_design 的端点表。

## 没有斜杠变体

`APPEND_SLASH=False`（见 `ibweb.settings`）。Django 默认的「缺尾斜杠 → 301 重定向」在
本服务里有额外风险：**重定向可能丢掉 `Authorization` 头**（取决于客户端），
表现为「用 curl 能过、用某些客户端 401」。因此路径必须逐字匹配，不做隐式重定向。
"""

from __future__ import annotations

from django.urls import path

from ibweb import views

__all__ = ["urlpatterns"]

urlpatterns = [
    path("healthz", views.healthz_endpoint, name="ib-healthz"),
    path("healthz/deps", views.healthz_deps_endpoint, name="ib-healthz-deps"),
    path("api/files", views.files_endpoint, name="ib-files"),
    path("api/files/<str:doc_id>", views.file_detail_endpoint, name="ib-file-detail"),
    path("api/files/<str:doc_id>/retry", views.file_detail_endpoint, name="ib-file-retry"),
    # R2（IFC-IB-283）：页面图字节。**字面量必须与 `ib.streaming.IMAGE_ENDPOINT_TEMPLATE`
    # 一致** —— 前端拿到的 `url_path` 就是按那个模板拼的，二者漂移会表现为「前端 404
    # 但服务端日志一片正常」。自检 `related_images_event_contract` 会断言二者相等。
    path(
        "api/files/<str:doc_id>/images/<str:image_id>",
        views.file_image_endpoint,
        name="ib-file-image",
    ),
    path("api/rebuild", views.rebuild_endpoint, name="ib-rebuild"),
    # 字面量路由必须在 `<str:job_id>` 之前：否则 `activate`/`rollback` 会被当成 job_id 捕获。
    path("api/rebuild/activate", views.rebuild_activate_endpoint, name="ib-rebuild-activate"),
    path("api/rebuild/rollback", views.rebuild_rollback_endpoint, name="ib-rebuild-rollback"),
    path("api/rebuild/<str:job_id>", views.rebuild_progress_endpoint, name="ib-rebuild-progress"),
    path("api/chat/stream", views.chat_stream_endpoint, name="ib-chat-stream"),
]
