"""R9 守约探针（只读，仅测试侧）：直接验证 test_ib_embed_wire._request_bounded 的重试边界。

证明四件事（对应 REV-09-1/2 的硬边界）：
  A. 连接级异常（ConnectionAbortedError）前两次抛出 → 第 3 次成功（≤3 次尝试 + 退避）。
  B. 非连接级异常（TimeoutError）→ **不重试**（attempts=1），原样冒泡。
  C. 连接级异常持续 → 恰好 3 次尝试后**原样抛出**（不静默通过）。
  D. AssertionError → **绝不捕获**（attempts=1，原样冒泡）——「不吞断言」的直接证据。
  E. HTTPError(500) → **不重试**（attempts=1），状态码 500 原样返回（不改写状态码）。

不联网、不碰 src/；仅 importlib 加载测试文件并猴补 urllib.request.urlopen。
"""

from __future__ import annotations

import importlib.util
import io
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "tests" / "integration" / "test_ib_embed_wire.py"

_spec = importlib.util.spec_from_file_location("wire_mod_r9", TARGET)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


class _FakeResp:
    status = 200

    def __init__(self, payload: bytes = b'{"ok": true}') -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def run_case(name, side_effect):
    calls = {"n": 0}
    original = urllib.request.urlopen

    def fake(req, timeout=None):
        calls["n"] += 1
        outcome = side_effect(calls["n"])
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    urllib.request.urlopen = fake
    started = time.perf_counter()
    result = None
    error = None
    try:
        result = mod._request_bounded("REQ", timeout=1)
    except BaseException as exc:  # noqa: BLE001 - 探针需观测所有异常类型
        error = exc
    finally:
        urllib.request.urlopen = original
    elapsed = time.perf_counter() - started
    print(
        f"{name}: attempts={calls['n']} result={result} "
        f"raised={type(error).__name__ if error else None} elapsed={elapsed:.3f}s"
    )
    return calls["n"], result, error


print("module:", TARGET.name)
print("_MAX_ATTEMPTS =", mod._MAX_ATTEMPTS, "| backoff =", mod._RETRY_BACKOFF_S, "s")

# A：连接级瞬态 → 有界重试后成功
run_case(
    "A_conn_aborted_then_ok",
    lambda n: ConnectionAbortedError("WinError 10053") if n <= 2 else _FakeResp(),
)

# B：非连接级异常 → 不重试
run_case("B_non_conn_timeout", lambda n: TimeoutError("not a connection error"))

# C：连接级持续 → 3 次尝试后原样抛出
run_case("C_conn_persistent", lambda n: ConnectionResetError("WinError 10054"))

# D：AssertionError → 绝不捕获（不吞断言）
run_case("D_assertion_error", lambda n: AssertionError("must not be swallowed"))

# E：HTTPError(500) → 不重试，状态码原样返回
run_case(
    "E_http_500",
    lambda n: urllib.error.HTTPError(
        "http://127.0.0.1/x", 500, "err", {}, io.BytesIO(b'{"code": "internal_error"}')
    ),
)
