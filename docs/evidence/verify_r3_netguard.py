"""独立复核（verifier）—— C12 网络守卫 pytest 插件。

用审计钩子（`socket.connect`）记录**全量测试运行期间的每一次 TCP 连接尝试**，
并区分回环 / 非回环。运行结束后把命中写到 stderr。

用法（从项目根）：
  PYTHONPATH=docs/evidence python -m pytest tests/ -q -p verify_r3_netguard

非回环命中会以 `!!! NETGUARD NONLOOPBACK ...` 打到 stderr；零命中即证明离线。
"""

from __future__ import annotations

import ipaddress
import os
import sys

_CONNECTS: list[str] = []


def _is_loopback(addr) -> bool:
    try:
        if isinstance(addr, (tuple, list)) and addr:
            host = addr[0]
        else:
            host = addr
        if not isinstance(host, str):
            return False
        # Unix domain socket 路径不是回环（本用例集不使用，单独标注）
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except Exception:  # noqa: BLE001
        return False


def _hook(event: str, args) -> None:
    if event != "socket.connect":
        return
    try:
        sock, addr = args[0], args[1]
        fam = getattr(sock, "family", None)
        # 只关心 AF_INET / AF_INET6
        if fam is not None and str(fam) not in ("AddressFamily.AF_INET", "AddressFamily.AF_INET6", "2", "10"):
            return
        if not _is_loopback(addr):
            _CONNECTS.append(repr(addr))
            print(f"!!! NETGUARD NONLOOPBACK connect -> {addr!r}", file=sys.stderr, flush=True)
    except Exception:  # noqa: BLE001
        pass


if os.environ.get("IB_NETGUARD", "1") == "1":
    sys.addaudithook(_hook)


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    print(
        f"\n=== NETGUARD 摘要：非回环连接尝试次数 = {len(_CONNECTS)} ===",
        file=sys.stderr,
        flush=True,
    )
    if _CONNECTS:
        for item in sorted(set(_CONNECTS)):
            print(f"  !!! {item}", file=sys.stderr, flush=True)
    else:
        print("  （零命中 —— 全程离线）", file=sys.stderr, flush=True)
