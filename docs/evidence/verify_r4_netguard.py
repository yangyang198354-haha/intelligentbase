"""独立核验探针（verifier 自建）：把整套 GROUP_D 测试跑在**非回环出网即失败**的守卫下。

目的（对抗性）：证明「全量套件通过」不是靠连外部服务得来的，且**未触碰目标机 192.168.31.133**。
做法：在 `pytest.main()` 之前给 `socket.socket.connect` / `connect_ex` / `socket.create_connection`
装上守卫 —— 目标地址不是回环（`127.0.0.0/8`、`::1`）就**抛异常**，并记录被拦截的目标。
本探针**只统计与拦截**，不修改任何被测代码或测试代码。

用法：`PYTHONUTF8=1 python docs/evidence/verify_r4_netguard.py`
退出码 = pytest 的退出码（并为出网拦截单独提示）。允许且仅允许回环。
"""

from __future__ import annotations

import pathlib
import socket
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

BLOCKED: list[str] = []
ALLOWED_LOOPBACK: list[str] = []


def _is_loopback(host: object) -> bool:
    text = str(host)
    if text in ("", "localhost", "::1", "0.0.0.0", "::"):
        return True
    if text.startswith("127."):
        return True
    # 抽象命名空间 / Unix socket（AF_UNIX 的 addr 是 str 路径，不走本守卫的分支）
    return False


def _record(host: object) -> bool:
    if _is_loopback(host):
        ALLOWED_LOOPBACK.append(str(host))
        return True
    BLOCKED.append(str(host))
    return False


_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_create_connection = socket.create_connection


def _guard_connect(self, address):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) and address else address
    if not _record(host):
        raise AssertionError(f"EGRESS_BLOCKED: 非回环连接被核验守卫拦截 -> {host}")
    return _real_connect(self, address)


def _guard_connect_ex(self, address):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) and address else address
    if not _record(host):
        raise AssertionError(f"EGRESS_BLOCKED: 非回环连接被核验守卫拦截 -> {host}")
    return _real_connect_ex(self, address)


def _guard_create_connection(address, *args, **kwargs):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) and address else address
    if not _record(host):
        raise AssertionError(f"EGRESS_BLOCKED: 非回环连接被核验守卫拦截 -> {host}")
    return _real_create_connection(address, *args, **kwargs)


socket.socket.connect = _guard_connect  # type: ignore[method-assign]
socket.socket.connect_ex = _guard_connect_ex  # type: ignore[method-assign]
socket.create_connection = _guard_create_connection  # type: ignore[assignment]


def main() -> int:
    import pytest

    code = pytest.main(["-q", "tests/unit", "tests/integration", "tests/e2e"])
    print("-" * 72)
    print(f"NETGUARD 回环连接次数 = {len(ALLOWED_LOOPBACK)}；唯一样本 = {sorted(set(ALLOWED_LOOPBACK))[:5]}")
    print(f"NETGUARD 拦截的非回环目标数 = {len(BLOCKED)}")
    if BLOCKED:
        print("NETGUARD 被拦截目标（去重） = " + ", ".join(sorted(set(BLOCKED))))
        print("NETGUARD 结论: 存在出网尝试（判定失败）")
        return 1 if code == 0 else code
    print("NETGUARD 结论: ZERO_NON_LOOPBACK_EGRESS（未触碰 192.168.31.133 或任何外部主机）")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
