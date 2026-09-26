"""
@module MOD-IB-23
@implements IFC-IB-263 启动期 schema 初始化（systemd `ExecStartPre` 调用）
@depends MOD-IB-11（schema DDL 单一真源）
@author sub_agent_software_developer

启动前 bootstrap：`python -m ibweb.bootstrap --ensure-schema`。

## 为什么单独一个入口，而不是塞进 `wsgi.py` 的模块级代码

WSGI 入口在**每次**被 import 时执行（含 `manage.py check`、任何脚本）。把建表放在那里，
就会让「只是想跑一次静态检查」也去动生产库文件。

单独入口 + systemd `ExecStartPre` 的组合有明确的语义：**部署时执行一次、失败即中止启动、
成功不留运行期副作用**。这也让「建表」在 systemd 日志里有一行独立记录，
而不是混在 Web 启动日志里。

## 建表逻辑**只有一处**：台账仓储的构造

`SqliteLedgerRepository.__init__` 内部已调 `ensure_schema()` 并校验列完整性
（缺列即抛 `DependencyUnavailableError` —— 不带着残缺结构启动）。
本模块因此**不重复**写 DDL 或 PRAGMA：只负责「按配置找到库文件、构造-关闭一次仓储、
把失败翻译成明确的退出码」。复制一份 DDL 到这里的诱惑很大，但那正是「两处 schema
迟早不一致」的起点。

## 为什么建表失败必须非零码退出

`ensure_schema()` 的失败几乎总是环境问题（目录不存在、权限不对、磁盘只读）。
若吞掉错误继续启动，第一次上传会以 500 暴露问题，而那时排障的人看到的是业务错误，
不会想到「schema 根本没建起来」。
"""

from __future__ import annotations

import argparse
import os
import sys

__all__ = ["ensure_schema_main", "main"]


def ensure_schema_main() -> int:
    """按 `IB_LEDGER_PATH` 建/校验台账 schema（幂等）。

    退出码：0 成功（含「内存台账无需建表」）；2 配置缺失；3 目录不可创建；4 建表失败。
    """
    from ib.config import ConfigurationResolver, FileConfigurationSource

    source_kind = os.environ.get("IB_CONFIG_SOURCE", "file").strip() or "file"
    if source_kind == "dict":
        # `dict` 源只在离线自测中使用（配置字典在进程内，命令行进程拿不到）
        print("IB_CONFIG_SOURCE=dict：离线自测装配，跳过 schema 初始化", file=sys.stderr)
        return 0

    path = os.environ.get("IB_CONFIG_FILE", "").strip()
    if not path:
        print("缺少必填环境变量 IB_CONFIG_FILE（只登记键名，不回显值）", file=sys.stderr)
        return 2

    resolver = ConfigurationResolver(FileConfigurationSource(path))
    cfg = resolver.global_config()
    if getattr(cfg, "ledger_backend", "sqlite") == "memory":
        print("IB_LEDGER_BACKEND=memory：内存台账无需 schema 初始化", file=sys.stderr)
        return 0

    ledger_path = str(cfg.ledger_path)
    parent = os.path.dirname(os.path.abspath(ledger_path))
    if parent:
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            print(f"台账目录不可创建：{parent!r}（{type(exc).__name__}）", file=sys.stderr)
            return 3

    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    try:
        repo = SqliteLedgerRepository(ledger_path)  # 构造期即 ensure_schema + 列校验
    except Exception as exc:  # noqa: BLE001 - 启动前入口需要把任何失败翻成退出码
        print(f"台账 schema 初始化失败（{type(exc).__name__}）", file=sys.stderr)
        return 4
    try:
        print(f"台账 schema 就绪（{ledger_path}）", file=sys.stderr)
    finally:
        repo.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ibweb.bootstrap", description="intelligentbase 启动前初始化")
    parser.add_argument(
        "--ensure-schema",
        action="store_true",
        help="幂等建立台账 SQLite schema（systemd ExecStartPre 使用）",
    )
    args = parser.parse_args(argv)
    if not args.ensure_schema:
        parser.print_help()
        return 2
    return ensure_schema_main()


if __name__ == "__main__":  # pragma: no cover - 进程入口
    sys.exit(main())
