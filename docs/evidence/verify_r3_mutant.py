"""独立复核（verifier）—— C5 突变测试插件：证明三个翻转用例是**载荷性**守卫。

只改**运行时**对象（不动任何 `src/**` 文件），把 R3 的修复「回退」到修复前行为，
再跑那三个翻转用例。若它们是真正的正向守卫，则必须**响亮失败**。

用法：
  PYTHONPATH=docs/evidence python -m pytest <三个翻转用例> -q -p verify_r3_mutant --mutant=fnd01
  PYTHONPATH=docs/evidence python -m pytest <三个翻转用例> -q -p verify_r3_mutant --mutant=fnd02
  （不带 --mutant 即无突变，作对照，应全 PASS）

突变定义：
  fnd01 = 摘要函数恒返回 ""（等价于「自带工具没登记进默认注册表」的修复前接线）
  fnd02 = `DocumentLifecycle._bind_write_collection` 变为 no-op
          （等价于修复前「删除路径假定 collection 已绑定」→ 未绑时 delete_by_doc 抛 StartupError）
"""

from __future__ import annotations

import sys


def pytest_addoption(parser):
    parser.addoption("--mutant", action="store", default="none", help="fnd01 | fnd02 | none")


def _apply(which: str) -> None:
    if which == "fnd01":
        import ib.tools as tools

        def _empty(registry=None):  # noqa: ARG001
            return ""

        tools.build_capability_digest = _empty
        print("\n>>> MUTANT fnd01 已注入：build_capability_digest 恒返回 ''", file=sys.stderr)

    elif which == "fnd02":
        from ib.lifecycle import DocumentLifecycle

        def _noop(self, scope, project_id):  # noqa: ARG001
            return None

        DocumentLifecycle._bind_write_collection = _noop
        print("\n>>> MUTANT fnd02 已注入：_bind_write_collection 变为 no-op（回退 FND-02 修复）",
              file=sys.stderr)

    elif which != "none":
        raise SystemExit(f"未知 --mutant={which}")


def pytest_configure(config):
    which = config.getoption("--mutant")
    if which != "none":
        _apply(which)
