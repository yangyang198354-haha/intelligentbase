#!/usr/bin/env python
"""
@module MOD-IB-23
@implements 运维入口（`check` / `selfcheck` / 离线装配探针）
@depends MOD-IB-23（composition）
@author sub_agent_software_developer

Django 管理入口。**刻意保持极薄**：不注册自定义命令包（`ibweb/management/`），
因为本服务只有三个真实需求 ——

* `python manage.py check`：Django 自身的配置体检（收窄配置下必须零错误）；
* `python -m ibweb.worker`：后台任务（入口在 `ibweb.worker`，不需要 Django 命令壳）；
* `python scripts/selfcheck.py`：离线一键自检（不触网、不连生产库）。

多一层命令壳只会让「运维到底该跑哪条命令」变得含糊。
"""

from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - 依赖缺失时的可读提示
        raise ImportError(
            "无法导入 Django。请先安装依赖：pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)
