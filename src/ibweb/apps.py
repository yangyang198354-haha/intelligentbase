"""
@module MOD-IB-23
@implements IFC-IB-263 启动期必填校验（AC-IB-12-03） / §2.1.1 lifespan 等价物
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

启动钩子（`AppConfig.ready()`）—— FastAPI `lifespan` 的 Django 等价物（module_design §2.1.1）。

## 为什么启动校验必须**在启动期**做

配置缺项的失败形态有一种非常坏的分布：**它在启动时完全看不出来**。
服务健康（`/healthz` 200）、列表能查（`GET /api/files` 返回空）、直到用户上传第一个文件
才在某个深层调用里抛 `KeyError` —— 而那时排障的人看到的是 500，第一反应通常怀疑业务代码。

把校验提前到 `ready()`，失败形态就变成：**进程起不来 + systemd 日志里一行明确的中文键名**。
这是把「难以定位的运行期故障」换成「一眼可见的启动故障」，属于纯收益的取舍（AC-IB-12-03）。

## 只做校验，不做业务初始化

`ready()` 里不启动线程、不建连接池、不注册信号 —— 那些都放在 systemd 单元与 `manage.py` 子命令里。
理由是 Django 的 `ready()` 在**同一进程内可能被调用两次**（`django.setup()` 与某些管理命令），
在其中启动线程会静默产生第二份后台任务（表现为「同一个文档被处理两次」）。
`build_deps()` 本身有幂等保护，但「幂等的装配」不该成为「可以在 ready() 里随便放副作用」的借口。
"""

from __future__ import annotations

from django.apps import AppConfig

__all__ = ["IbWebConfig"]


class IbWebConfig(AppConfig):
    name = "ibweb"
    verbose_name = "intelligentbase 知识库基座"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """启动期校验 + 装配（幂等）。任何失败都让进程**直接起不来**。"""
        from ib.observability import get_logger, log_event
        from ibweb import composition

        if composition.is_bootstrapped():
            # wsgi.py 已先装配（正常生产路径）：只记录检查通过，不重复装配
            get_logger("startup").event("succeeded", note="deps_already_built")
            return

        get_logger("startup").event("started")
        deps = composition.build_deps()
        # 输出装配摘要 + 外发声明（IFC-IB-215 / NFR-08：外发行为必须在配置层可追溯）。
        # 仅开关名与主机名，无凭据、无正文。`data_categories` 拼成单字符串传入 ——
        # 白名单对序列值只渲染成 `<list len=N>`，那等于没有声明。
        egress = deps.egress
        categories = list(getattr(egress, "data_categories", []) or [])
        log_event(
            "startup",
            "succeeded",
            count=len(deps.projects),
            egress_remote=bool(getattr(egress, "remote", False)),
            egress_host=str(getattr(egress, "endpoint_host", "") or ""),
            egress_data=",".join(str(c) for c in categories),
        )
