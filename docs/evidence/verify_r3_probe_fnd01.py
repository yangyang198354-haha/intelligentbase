"""独立复核（verifier）—— C6 / FND-GROUP-D-01 脱离测试套件的自建探针。

不复用 groupd_*/ groupc_* 探针，独立断言：
  1) 离线装配后 `Deps.capability_digest` 非空且含 `search_knowledge`；
  2) `IntentRouter._capability_digest()`（L2 路由实际取到的摘要）同样非空、含该工具；
  3) 不再是占位串「（无可用工具）」；
  4) 摘要与「实际被 bind_tools 绑定的工具清单」一致（防「摘要声称有、实绑没有」的反向漂移）。

只读 src/**，不写任何实现。
"""

from __future__ import annotations

import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (str(_ROOT / "src"), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "verify-r3-offline-token")

from conftest import offline_raw  # noqa: E402

from ib.core import Scope  # noqa: E402
from ib.routing.intent import IntentRouter  # noqa: E402
from ib.tools import build_capability_digest  # noqa: E402
from ibweb.composition import build_deps  # noqa: E402

PLACEHOLDER = "（无可用工具）"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def main() -> int:
    print("=== C6 / FND-GROUP-D-01 独立探针 ===")
    deps = build_deps(offline_raw(), force=True)

    digest = deps.capability_digest
    print(f"  deps.capability_digest repr = {digest!r}")
    check("Deps.capability_digest 非空", digest != "")
    check("含 search_knowledge", "search_knowledge" in digest)

    # 纯函数口径
    pure = build_capability_digest()
    check("与 build_capability_digest() 相等", digest == pure, f"pure={pure!r}")

    # L2 路由实际取到的摘要
    prompt_digest = IntentRouter._capability_digest()
    print(f"  IntentRouter._capability_digest() repr = {prompt_digest!r}")
    check("路由摘要非空", prompt_digest != "")
    check("路由摘要不是占位串", prompt_digest != PLACEHOLDER)
    check("路由摘要含 search_knowledge", "search_knowledge" in prompt_digest)
    check("路由摘要 == Deps 摘要", prompt_digest == digest)

    # 反向漂移：摘要声称的工具 必须 == bind_tools 实际绑定的工具
    bound = deps.bind_tools(Scope("p_alpha", ("kb_a",)))
    bound_names = sorted(t.name for t in bound)
    claimed_names = sorted(
        line.split(":", 1)[0].lstrip("- ").strip() for line in digest.splitlines() if line.strip()
    )
    print(f"  摘要声称的工具 = {claimed_names}")
    print(f"  bind_tools 实绑工具 = {bound_names}")
    check("摘要声称集合 == 实绑集合", claimed_names == bound_names)

    # 旧缺陷的反证：注册表若为空，摘要必为空 —— 证明摘要函数本身正确、此前是接线遗漏
    from ib.tools import ToolRegistry, build_capability_digest as bcd

    check("空注册表 → 空摘要（摘要函数本身正确）", bcd(ToolRegistry()) == "")

    print()
    if failures:
        print(f"结论: FAIL（{len(failures)} 项未满足）: {failures}")
        return 1
    print("结论: PASS —— FND-GROUP-D-01 已闭合（摘要非空、含自带工具、路由侧可见、与实绑一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
