"""
@module MOD-IB-23
@implements IFC-IB-241 `WSGIApplication`（WSGI 入口点）
@depends MOD-IB-23（composition）
@author software-developer

WSGI 入口（Waitress 主 / Gunicorn 备）。

## 装配在**导入时**发生

`application = build_application(build_deps())` 位于模块顶层：WSGI 服务器 `import` 本模块
就等于「装配 + 校验」一次。若把装配推迟到第一个请求（惰性），那么「配置缺项」的失败形态
会退化成「服务健康但第一个用户请求 500」——而 systemd 上看不到任何异常，只有用户先发现。
放在导入时，配置错误会直接让进程退出，systemd 报 `start-limit`，运维立刻能看到。

## 没有 ASGI 入口

R1 架构决策：`ASGIApp` → `WSGIApplication`。**不提供 `asgi.py`** —— 存在一个未被使用的
ASGI 入口只会诱导别人「顺手切到 uvicorn」。SSE 由 `StreamingHttpResponse` 承载，
不需要 ASGI；多进程扩展由 Waitress 的 `--threads` 承担。
"""

from __future__ import annotations

import os

# Django 设置必须在任何 Django 导入之前就位（本文件被 WSGI 服务器直接 import）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

from ibweb.composition import build_application, build_deps  # noqa: E402

#: WSGI 服务器寻找的可调用对象名（gunicorn/waitress 均默认取 `application`）。
application = build_application(build_deps())

__all__ = ["application"]
