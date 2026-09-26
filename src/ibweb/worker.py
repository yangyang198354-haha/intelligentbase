"""
@module MOD-IB-23
@implements IFC-IB-261 `ib-worker` 单元的入口（入库队列 + 重建推进）
@depends MOD-IB-23（composition）, MOD-IB-13（lifecycle）, MOD-IB-14（rebuild）
@author sub_agent_software_developer

后台 worker 入口：`python -m ibweb.worker [--once]`。

## 为什么 worker **不**跑在 Web 进程里

文档解析 + OCR + 向量化是分钟级、吃 CPU/内存的重活（目标机是 4GB 内存的树莓派）。
若放在 Web 进程内（后台线程），一次大文件 OCR 就会把等待 SSE 的请求一起拖住 ——
表现为「问答卡顿」与「上传后服务变慢」，而两者根因是同一条线程池。
拆成独立 systemd 单元后，重活的内存峰值与崩溃都被限制在自己的进程里：worker 被 OOM
杀掉时 Web 仍然可服务，systemd 会按 `Restart=` 拉起 worker。

## 队列与租约（不引入 Redis/Celery）

队列就是台账表本身（`status=pending` + 租约列）。认领用**条件 UPDATE** 实现，
因此多个 worker 不会重复处理同一篇文档，且不需要额外的中间件 —— 少一个必须运维的组件，
也少一处「消息重复投递」的失败面（ADR-07-R1）。

## 三层任务，顺序不敏感但**都必须收敛**

1. `reap_expired_leases`：崩溃 worker 遗留的 `parsing` 行回到 `pending`（否则永远卡住）；
2. `process_pending`：真正的入库；
3. 每个在飞的重建任务推进一步（`step_rebuild`）。

**注意**：本进程**不**调用 `activate_version`。版本切换是决策点（`done=True` 后由
运维/管理端点显式触发），让 worker 自动切换会把「重建完成」变成隐式行为，
出问题时无法回答「是谁切的、什么时候切的」。
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from typing import Any

__all__ = ["run_once", "main"]


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")
    import django

    django.setup()


def run_once(*, lease_owner: str, limit: int, reap: bool = True) -> dict[str, Any]:
    """执行一轮：回收 → 入库 → 重建推进。返回本轮摘要（供日志与自测断言）。"""
    from ib.context import utc_now_iso
    from ib.core import NotFoundError, RebuildJob
    from ib.observability import log_event
    from ibweb import composition

    deps = composition.get_deps()
    summary: dict[str, Any] = {"reaped": 0, "processed": 0, "succeeded": 0, "failed": 0, "rebuilds": 0}

    if reap:
        try:
            summary["reaped"] = int(deps.ledger.reap_expired_leases(utc_now_iso()))
        except Exception as exc:  # noqa: BLE001 - 回收失败不该阻断入库
            log_event("worker", "reap_failed", error_type=type(exc).__name__)

    report = deps.lifecycle.process_pending(lease_owner, limit)
    summary["processed"] = report.processed
    summary["succeeded"] = report.succeeded
    summary["failed"] = report.failed

    # 重建推进：逐个在飞任务走一步（每步内部自己会续租）
    for project_id in list(deps.projects.keys()):
        try:
            jobs = [j for j in deps.ledger.list_rebuild_jobs(project_id) if str(j.state) in ("planned", "running")]
        except Exception as exc:  # noqa: BLE001
            log_event("worker", "rebuild_list_failed", error_type=type(exc).__name__)
            continue
        for row in jobs:
            try:
                progress = deps.rebuild.step_rebuild(
                    RebuildJob(job_id=str(row.job_id), state=str(row.state)), lease_owner, limit
                )
            except NotFoundError:
                continue
            except Exception as exc:  # noqa: BLE001 - 单个重建失败不影响其他任务
                log_event("worker", "rebuild_step_failed", error_type=type(exc).__name__)
                continue
            summary["rebuilds"] += 1
            log_event(
                "worker",
                "rebuild_step",
                project_id=project_id,
                indexed=progress.indexed,
                failed=progress.failed,
                pending=progress.pending,
                done=progress.done,
            )

    log_event("worker", "cycle", **summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。`--once` 跑一轮即退出（供 systemd oneshot 或验收脚本使用）。"""
    parser = argparse.ArgumentParser(prog="ib-worker", description="intelligentbase 入库/重建 worker")
    parser.add_argument("--once", action="store_true", help="只跑一轮后退出")
    parser.add_argument("--interval", type=float, default=5.0, help="空闲轮询间隔秒数（默认 5）")
    parser.add_argument("--limit", type=int, default=8, help="每轮最多处理的文档数（默认 8）")
    parser.add_argument("--worker-id", default="", help="租约持有者标识（默认 hostname:pid）")
    args = parser.parse_args(argv)

    _setup_django()

    import socket

    lease_owner = args.worker_id or f"{socket.gethostname()}:{os.getpid()}"

    if args.once:
        run_once(lease_owner=lease_owner, limit=args.limit)
        return 0

    stopping = {"flag": False}

    def _stop(signum: int, frame: Any) -> None:  # noqa: ARG001
        # 收到信号只置标志：让**当前这一轮**跑完再退。
        # 若直接退出，正在处理的文档会留下 `parsing` 行，要等到租约超时才会被回收 ——
        # 部署重启频繁时，这些行会持续堆积成「看起来卡住」的文档。
        stopping["flag"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    from ib.observability import log_event

    log_event("worker", "started", lease_owner=lease_owner)
    while not stopping["flag"]:
        try:
            run_once(lease_owner=lease_owner, limit=args.limit)
        except Exception as exc:  # noqa: BLE001 - 单轮失败不能杀死 worker（否则 systemd 反复重启）
            log_event("worker", "cycle_failed", error_type=type(exc).__name__)
        # 用可中断的睡眠：`time.sleep` 期间收到 SIGTERM，Python 会等 sleep 结束才处理 →
        # 最长 5 秒的关机延迟。切成小片后信号几乎立即可见。
        deadline = time.monotonic() + max(0.1, args.interval)
        while not stopping["flag"] and time.monotonic() < deadline:
            time.sleep(0.2)
    log_event("worker", "stopped", lease_owner=lease_owner)
    return 0


if __name__ == "__main__":  # pragma: no cover - 进程入口
    sys.exit(main())
