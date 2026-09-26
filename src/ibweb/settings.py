"""
@module MOD-IB-23
@implements 收窄 Django 配置（REQ-NFR-IB-09；module_design §2.1.1 载体映射）
@depends (stdlib + django)
@author software-developer

**收窄配置**：只启用「承载 HTTP」所必需的部分。

## 刻意不启用的组件，以及为什么

| 组件 | 不启用的理由 |
|------|--------------|
| `django.contrib.auth` / `admin` | 基座不内置业务鉴权模型（`AuthzPolicy` 由接入方注入）。启用 auth 会**反向绑架**我们的角色语义到 Django 的 user/group 上，正是 ADR-13-R1 要避免的耦合 |
| `django.contrib.sessions` | 本服务**无状态**：令牌每次经 `Authorization` 头携带（IC-IB-01）。session 一旦启用，就会有人拿它当隐式身份来源 —— FreeArk 已因「裸 axios 偷用 session」踩过一次 |
| `django.contrib.contenttypes` | 仅 auth/admin 需要 |
| ORM / `DATABASES` | 台账是自管 SQL 的 SQLite（ADR-07-R1）。**若把台账搬进 ORM**，就同时丢掉 WAL/busy_timeout/租约条件 UPDATE 这三样实现细节的控制权 |
| DRF 默认认证类 | 默认的 `SessionAuthentication` 依赖 `contrib.auth`。置空并由 `ibweb.authz` 在中间件里做鉴权，使「未授权」只有一个来源 |
| 可浏览 API（BrowsableAPI） | 依赖模板系统；生产不需要，且它会**回显请求内容**，与「日志不留正文」的纪律相冲突 |

## 三个容易被默认值坑到的设置

1. `DATA_UPLOAD_MAX_MEMORY_SIZE`：Django 默认仅 2.5MB。本项目允许 50MB 文档，若不抬高，
   大文件会在**我们自己的校验之前**被 Django 以 `RequestDataTooBig` 拒掉 ——
   用户拿到的是框架的英文 500/400，而不是我们的中文可读提示。
2. `ALLOWED_HOSTS`：生产必须显式配置。空列表在 `DEBUG=False` 下会让**所有**请求得到 400，
   表现为「服务起来了但全部不可访问」，且日志里只有一行 `Invalid HTTP_HOST header`。
3. `SECRET_KEY`：本服务不用签名/会话，但 Django 要求非空。生产**要求经环境变量注入**
   （仓库内不得出现真实值）；离线模式生成一次性随机值，避免把开发密钥写进被跟踪的文件。
"""

from __future__ import annotations

import os

# --------------------------------------------------------------------------- #
# 路径与开关
# --------------------------------------------------------------------------- #

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: `IB_OFFLINE_MODE=1` → 本机自测装配（全替身、无外网、不连生产库）。
#: 显式读环境变量而不走 `ib.config`：本文件在 `django.setup()` **之前**被导入，
#: 此时基座尚未装配，只能依赖最原始的环境变量。
OFFLINE_MODE = os.environ.get("IB_OFFLINE_MODE", "0").strip() in ("1", "true", "True", "yes")

DEBUG = OFFLINE_MODE  # 生产恒 False（离线模式才允许调试便利）

# --------------------------------------------------------------------------- #
# 安全
# --------------------------------------------------------------------------- #

_SECRET_KEY = os.environ.get("IB_DJANGO_SECRET_KEY", "").strip()
if not _SECRET_KEY:
    if OFFLINE_MODE:
        # 离线：一次性随机值。**不落盘、不写默认常量** ——
        # 写死的开发密钥一旦随仓库分发，就会有人在生产忘记覆盖。
        import secrets

        _SECRET_KEY = secrets.token_urlsafe(48)
    else:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            "缺少必填环境变量 IB_DJANGO_SECRET_KEY（只登记键名，不回显值）。"
            "本服务不使用签名/会话，但 Django 要求 SECRET_KEY 非空。"
        )
SECRET_KEY = _SECRET_KEY

if OFFLINE_MODE:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
else:
    _hosts = os.environ.get("IB_ALLOWED_HOSTS", "").strip()
    ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]
    if not ALLOWED_HOSTS:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            "缺少必填环境变量 IB_ALLOWED_HOSTS（逗号分隔）。")
    # 生产不允许携带调试信息回显（Django 的调试页会打印局部变量，可能含正文/凭据）
    DEBUG = False

CSRF_COOKIE_SECURE = not OFFLINE_MODE
SESSION_COOKIE_SECURE = not OFFLINE_MODE
SECURE_CONTENT_TYPE_NOSNIFF = True

# --------------------------------------------------------------------------- #
# 应用
# --------------------------------------------------------------------------- #

INSTALLED_APPS = [
    # 只装自己：Django 的其余 contrib 应用本服务一件都不用（见模块文档表格）
    "ibweb.apps.IbWebConfig",
]

MIDDLEWARE = [
    # 唯一中间件：鉴权 + 请求上下文构造（定义在 `ibweb.authz`，与策略注入同处一文件，
    # 因为「谁鉴权」与「怎么鉴权」必须一起评审）。**刻意保持只有一层** ——
    # 中间件顺序是隐性依赖，层数越多越难推理「谁在什么时候改了 request」。
    "ibweb.authz.AuthMiddleware",
]

ROOT_URLCONF = "ibweb.urls"
WSGI_APPLICATION = "ibweb.wsgi.application"

TEMPLATES: list[dict] = []  # 无模板渲染（禁用可浏览 API）
DATABASES: dict = {}  # 不经 ORM；台账是自管 SQL 的 SQLite（ADR-07-R1）

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
APPEND_SLASH = False  # 不做隐式 301：前端契约里的路径必须逐字匹配（避免重定向丢 Authorization）

# --------------------------------------------------------------------------- #
# 请求体上限
# --------------------------------------------------------------------------- #

#: 见模块文档「容易被默认值坑到」第 1 条。
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024 * 1024
#: 超过此值的文件落到临时文件而非内存（4GB 内存的目标机上必须避免大文件常驻内存）。
FILE_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024
#: 真实的 50MB 上限由 `DocumentLifecycle.validate_upload` 把关（唯一真源，可测）。
#: 此处只做「别让框架比我们更早拒绝」的兜底。

# --------------------------------------------------------------------------- #
# DRF
# --------------------------------------------------------------------------- #

REST_FRAMEWORK = {
    # 认证/权限**全部置空**：鉴权只在 `ibweb.middleware.AuthMiddleware` 一处发生。
    # 若同时存在两套判断，就会出现「DRF 放行、中间件拦住」或反之的隐蔽不一致。
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.JSONParser",
    ],
    # 序列化时保留 `None`（字段契约里有「可空」语义：`| None` 必须原样出现在响应里，
    # 否则前端无法区分「值为空」与「字段不存在」）
    "COERCE_DECIMAL_TO_STRING": False,
}

# --------------------------------------------------------------------------- #
# 日志
# --------------------------------------------------------------------------- #

LOG_LEVEL = os.environ.get("IB_LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # 不干扰 ib.observability 已建立的 logger
    "formatters": {"plain": {"format": "%(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
        # swallows：吞掉 Django 默认的 mail_admins 处理器路径（本服务无邮件依赖）
        "null": {"class": "logging.NullHandler"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.security": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.server": {"handlers": ["null"], "level": "ERROR", "propagate": False},
    },
}
