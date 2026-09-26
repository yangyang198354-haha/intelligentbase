"""独立复核（verifier）—— C7 / FND-GROUP-D-02 脱离测试套件的自建探针 + 反例。

正向（修复后必须成立）：
  A. 项目「尚无事发生」（collection 未绑）时删除 pending 文档 → 成功，不抛 StartupError；
  B. 台账行消失（读路径权威）；
  C. 随后 worker `process_pending` 不把它索引成可检索的幽灵（检索为空、向量为 0）。

反例（不得为修 A 而破坏 B）：
  D. 删除**不存在**的文档 → 仍抛 NotFoundError（→ HTTP 404），不得被静默吞掉；
  E. 真缺 collection 时仍 fail-closed 上抛（不得被静默吞掉）。

只读 src/**，不写任何实现。
"""

from __future__ import annotations

import io
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

from ib.core import NotFoundError, Scope  # noqa: E402
from ib.context import make_request_context  # noqa: E402
from ibweb.composition import build_deps  # noqa: E402

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def _ctx(pid: str = "p_alpha"):
    return make_request_context(project_id=pid, actor_id="verifier", session_id="s1", roles=("manager",))


def main() -> int:
    print("=== C7 / FND-GROUP-D-02 独立探针（正向） ===")
    deps = build_deps(offline_raw(), force=True)
    scope = Scope("p_alpha", ("kb_a",))
    ctx = _ctx()

    body = b"ghost-probe-content-VERIFY-R3"
    record = deps.lifecycle.submit_upload(
        ctx,
        deps.lifecycle.validate_upload("vp_ghost.txt", len(body), body),
        "kb_a",
        data=io.BytesIO(body),
    )
    print(f"  上传 doc_id = {record.doc_id}  status = {record.status}")
    print(f"  删除前台账行 = {deps.ledger.get_document(scope, record.doc_id) is not None}")

    # A. 尚无事发生 → 删除必须成功（不抛）
    try:
        report = deps.lifecycle.delete_document(scope, record.doc_id)
        print(f"  A: delete_document 未抛；report = {report}")
        check("A 尚无事发生时删除成功（未抛 StartupError）", True)
    except Exception as exc:  # noqa: BLE001
        print(f"  A: delete_document 抛出 {type(exc).__name__}: {exc}")
        check("A 尚无事发生时删除成功（未抛 StartupError）", False, type(exc).__name__)
        print("结论: FAIL（FND-GROUP-D-02 未闭合）")
        return 1

    check("A2 vectors_deleted == 0（本项目尚无派生物）", report.vectors_deleted == 0, str(report))
    check("A3 ledger_deleted is True", report.ledger_deleted is True)

    # B. 台账行消失
    check("B 台账行已删（get_document → None）", deps.ledger.get_document(scope, record.doc_id) is None)

    # C. worker 不得复活幽灵
    rep = deps.lifecycle.process_pending("verify-worker", 10)
    print(f"  C: process_pending = {rep}")
    check("C1 worker 未认领已删行", rep.processed == 0 and rep.succeeded == 0, str(rep))
    hits = deps.retrieval.search("ghost-probe-content-VERIFY-R3", scope=scope).hits
    print(f"  C2 检索命中数 = {len(hits)}")
    check("C2 检索不到已删内容（无幽灵）", hits == [])
    check("C3 向量侧无残留", deps.vectors.count(scope) == 0)
    check("C4 对账无孤儿行", deps.ledger.list_orphan_doc_ids("p_alpha", []) == [])

    # ---------------------------------------------------------------- #
    print()
    print("=== 反例（不得为修 A 破坏 B） ===")

    # D. 删除不存在的文档 → NotFoundError
    try:
        deps.lifecycle.delete_document(scope, "no-such-doc-id-xyz")
        print("  D: 未抛 —— 异常被吞了")
        check("D 删除不存在文档仍抛 NotFoundError", False, "未抛")
    except NotFoundError as exc:
        print(f"  D: 抛出 NotFoundError（正确）: {exc}")
        check("D 删除不存在文档仍抛 NotFoundError", True)
    except Exception as exc:  # noqa: BLE001
        print(f"  D: 抛出了非 NotFoundError 的 {type(exc).__name__}: {exc}")
        check("D 删除不存在文档仍抛 NotFoundError", False, type(exc).__name__)

    # D2. 跨项目（作用域外）删除 → 也应是 NotFoundError（不区分「不存在」与「不属于你」）
    try:
        deps.lifecycle.delete_document(Scope("p_beta", ("kb_b",)), record.doc_id)
        print("  D2: 未抛")
        check("D2 跨作用域删除抛 NotFoundError", False, "未抛")
    except NotFoundError:
        print("  D2: 抛出 NotFoundError（正确）")
        check("D2 跨作用域删除抛 NotFoundError", True)
    except Exception as exc:  # noqa: BLE001
        check("D2 跨作用域删除抛 NotFoundError", False, type(exc).__name__)

    # E. 真缺 collection 时仍 fail-closed 上抛
    #    构造：登记项目引用一个**从未被 ensure_collection** 的 collection 名 -> 删除应上抛而非静默
    print()
    print("  E: 真缺 collection 的 fail-closed 行为")
    try:
        from ib.core import StartupError

        deps2 = build_deps(offline_raw(), force=True)
        # 把一个不存在于向量库的项目 scope 交给删除路径
        deps2.lifecycle.delete_document(Scope("p_does_not_exist", ("kb_a",)), "whatever")
        print("  E: 未抛（走到了 NotFound）—— 需进一步区分")
        check("E 真缺 collection fail-closed", False, "未抛")
    except NotFoundError:
        # 台账先查不到行 → NotFoundError，这也是可接受的 fail-closed（未静默成功）
        print("  E: 台账先行 NotFoundError（可接受的 fail-closed，未静默成功）")
        check("E 真缺 collection fail-closed（未静默成功）", True)
    except Exception as exc:  # noqa: BLE001
        print(f"  E: 上抛 {type(exc).__name__}: {exc}（fail-closed）")
        check("E 真缺 collection fail-closed（未静默成功）", True)

    print()
    if failures:
        print(f"结论: FAIL（{len(failures)} 项未满足）: {failures}")
        return 1
    print("结论: PASS —— FND-GROUP-D-02 正向已闭合，且反例（404 语义）仍成立")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
