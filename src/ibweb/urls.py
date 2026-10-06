"""
@module MOD-IB-23
@implements IFC-IB-242 ~ IFC-IB-249 路由表
            IFC-IB-283（R2）`/api/files/{doc_id}/images/{image_id}` 路由
            IFC-IB-294/295（R7）`/api/config/definition` 路由
            IFC-IB-352（REV-16-2）`/api/config/prompts[/{expert}/{layer}]` 提示词端点族路由
            IFC-IB-307（R8）`/api/chat/resume` 路由
            IFC-IB-316 ~ IFC-IB-321（R13）账户 / 会话路由
            IFC-IB-333（R14）`/api/projects` 项目枚举路由
            IFC-IB-359 / 362（REV-16-4）`/api/config/audit` + `/api/config/storage-state` 路由
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
    # R8（IFC-IB-307）：会话续跑。**仅 `Authorization` 头鉴权**（不接受 `?token=`）；
    # 准入顺序与前置换检查见 `views.chat_resume_endpoint`（fail-closed，不新建会话）。
    path("api/chat/resume", views.chat_resume_endpoint, name="ib-chat-resume"),
    # R7（IFC-IB-294/295）：定义文档读写。**单一真源**端点（GET 读 / PUT 原子写回）。
    path("api/config/definition", views.definition_config_endpoint, name="ib-config-definition"),
    # REV-16-2（IFC-IB-352）：提示词端点族（第二真源，ADR-15-R1）。
    # 列表路由必须在 `<str:expert>` 之前（否则会被当作 expert 名捕获）。
    path("api/config/prompts", views.prompt_config_endpoint, name="ib-config-prompts"),
    path(
        "api/config/prompts/<str:expert>/<str:layer>",
        views.prompt_config_endpoint,
        name="ib-config-prompt-layer",
    ),
    # REV-16-4（IFC-IB-359 / 362）：配置审计（只读）与存储态（只读）。
    # **字面量路由必须先于 `api/config/definition` 之外的任何前缀捕获**（此处无冲突）：
    # `audit` / `storage-state` 均为独立字面量，不会被 `prompts/<str:expert>` 捕获。
    # 仅 `Authorization` 头鉴权；`?token=` 由中间件先于路由拒绝（4xx）。
    path("api/config/audit", views.config_audit_endpoint, name="ib-config-audit"),
    path(
        "api/config/storage-state",
        views.storage_state_endpoint,
        name="ib-config-storage-state",
    ),
    # R14（IFC-IB-333）：项目枚举（admin 见全部 / ops 仅见自身）。
    # **不是**项目级端点：全局主体未选定项目时也返回 200（否则 admin 无法引导选择项目）。
    # 仅 `Authorization` 头鉴权；`?token=` 由中间件先于路由拒绝（4xx）。
    path("api/projects", views.projects_endpoint, name="ib-projects"),
    # R13（IFC-IB-316~321）：账户 / 会话。
    # 登录是**唯一**免鉴权端点（尚无令牌），但它**仍**受 `?token=` 4xx 纪律约束；
    # 其余端点一律只认 `Authorization: Bearer`（不接受 `?token=`，中间件先于路由拒绝）。
    path("api/auth/login", views.auth_login_endpoint, name="ib-auth-login"),
    path("api/auth/logout", views.auth_logout_endpoint, name="ib-auth-logout"),
    path("api/auth/me", views.auth_me_endpoint, name="ib-auth-me"),
    path("api/auth/change-password", views.auth_change_password_endpoint, name="ib-auth-change-password"),
    path("api/auth/session/renew", views.auth_session_renew_endpoint, name="ib-auth-session-renew"),
    path("api/accounts", views.accounts_endpoint, name="ib-accounts"),
    path("api/accounts/<str:user_id>/disable", views.account_disable_endpoint, name="ib-account-disable"),
    path(
        "api/accounts/<str:user_id>/reset-password",
        views.account_reset_password_endpoint,
        name="ib-account-reset-password",
    ),
]
