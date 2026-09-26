"""GROUP_C R3 symptom probe（只读；不写入仓库任何路径，不触网，不连生产库）。

运行：PYTHONUTF8=1 python /path/to/groupc_r3_probe.py   （cwd = intelligentbase 根）
"""
import io
import pathlib
import sys

_ROOT = pathlib.Path.cwd()
# 脚本位于 docs/evidence/ 下，运行入口是仓库根 —— 显式把根与 src 放进 sys.path
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tests.conftest import ingest_text, offline_raw, request_ctx  # noqa: E402
from ibweb.composition import build_deps  # noqa: E402
from ib.core import Scope, VectorPoint  # noqa: E402
from ib.routing.intent import IntentRouter  # noqa: E402


def section(title: str) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------- FND-01
section("FND-GROUP-D-01  capability_digest / 路由提示")
deps = build_deps(offline_raw(), force=True)
print("deps.capability_digest  =", repr(deps.capability_digest))
print("router prompt           =", repr(IntentRouter._capability_digest()))
print("bind_tools(p_alpha)     =", [t.name for t in deps.bind_tools(Scope(project_id="p_alpha"))])
print("digest 含 search_knowledge ?", "search_knowledge" in deps.capability_digest)
print("摘要与实绑工具一致 ?      ",
      [t.name for t in deps.bind_tools(Scope(project_id="p_alpha"))] == ["search_knowledge"])

# ---------------------------------------------------------------- FND-02 主窗口
section("FND-GROUP-D-02 (a) 尚无事发生 → 删除必须成功，且不留幽灵")
scope = Scope("p_alpha", ("kb_a",))
print("启动后已建 collection   =", sorted(deps.vectors._collections))
print("删除前 store 绑定       =", deps.vectors._bound_collection)
rec = deps.lifecycle.submit_upload(
    request_ctx("p_alpha"),
    deps.lifecycle.validate_upload("probe.txt", 9, b"probe-abc"),
    "kb_a",
    data=io.BytesIO(b"probe-abc"),
)
print("上传                    =", rec.doc_id, rec.status)
report = deps.lifecycle.delete_document(scope, rec.doc_id)
print("delete_document         =", report)
print("台账行（应为 None）     =", deps.ledger.get_document(scope, rec.doc_id))
print("worker process_pending  =", deps.lifecycle.process_pending("probe-worker", 10))
print("worker 后台账行         =", deps.ledger.get_document(scope, rec.doc_id))
print("retrieval hits（应为 []）=", deps.retrieval.search("probe-abc", scope=scope).hits)
print("vectors count（应为 0） =", deps.vectors.count(scope))

# ---------------------------------------------------------------- FND-02 竞态 A
section("FND-GROUP-D-02 (b) worker 写入向量后、置位前被删 → skipped 且无残留")
deps = build_deps(offline_raw(), force=True)
scope = Scope("p_alpha", ("kb_a",))
rec = deps.lifecycle.submit_upload(
    request_ctx("p_alpha"),
    deps.lifecycle.validate_upload("race.txt", 20, b"race-content-abcdefg"),
    "kb_a",
    data=io.BytesIO(b"race-content-abcdefg"),
)
inner = deps.vectors
seed = {"scope": scope, "doc_id": rec.doc_id}


class RaceAtUpsert:
    """在 worker 的 upsert 之前插入一次真实 delete_document（模拟用户并发删除）。"""

    def __init__(self):
        self.fired = False

    def __getattr__(self, name):
        return getattr(inner, name)

    def upsert(self, points, *, wait):
        if not self.fired:
            self.fired = True
            deps.lifecycle.delete_document(seed["scope"], seed["doc_id"])
        return inner.upsert(points, wait=wait)


racer = RaceAtUpsert()
deps.lifecycle._vectors = racer
print("process_pending         =", deps.lifecycle.process_pending("race-worker", 10))
print("删除确在 upsert 时发生 =", racer.fired)
print("台账行（应为 None）     =", deps.ledger.get_document(scope, rec.doc_id))
print("vectors count（应为 0） =", deps.vectors.count(scope))
print("retrieval hits（应为 []）=",
      deps.retrieval.search("race-content-abcdefg", scope=scope).hits)

# ---------------------------------------------------------------- FND-02 竞态 B
section("FND-GROUP-D-02 (c) 第一次向量清扫之后、删台账之前被 worker 写入 → 竞态清扫必须清掉")
deps = build_deps(offline_raw(), force=True)
scope = Scope("p_alpha", ("kb_a",))
rec = ingest_text(deps, "p_alpha", "kb_a", "indexed.txt", "已经索引好的正文内容。")
print("入库后 vectors count    =", deps.vectors.count(scope))
inner = deps.vectors
coll = inner._collections["ib_p_alpha_v1"]
seed_payload = next(iter(coll.points.values()))[1]


class RogueWriter:
    """删除路径完成第 1 次向量清扫后，worker「就地」写入一个点（幽灵候选）。"""

    def __init__(self):
        self.calls = 0
        self.injected = False

    def __getattr__(self, name):
        return getattr(inner, name)

    def delete_by_doc(self, scope, doc_id):
        out = inner.delete_by_doc(scope, doc_id)
        self.calls += 1
        if self.calls == 1 and not self.injected:
            self.injected = True
            inner.upsert(
                [VectorPoint(id=f"{doc_id}#rogue", vector=[0.0] * 1024, payload=seed_payload)],
                wait=True,
            )
        return out


rogue = RogueWriter()
deps.lifecycle._vectors = rogue
report = deps.lifecycle.delete_document(scope, rec.doc_id)
print("delete_document         =", report)
print("delete_by_doc 调用次数  =", rogue.calls, "(清扫 + 竞态清扫 = 2)")
print("幽灵点在窗口内写入 ?    ", rogue.injected)
print("vectors count（应为 0） =", inner.count(scope))
print("台账行（应为 None）     =", deps.ledger.get_document(scope, rec.doc_id))
print("retrieval hits（应为 []）=", deps.retrieval.search("已经索引好的正文内容。", scope=scope).hits)

# ---------------------------------------------------------------- 既有语义不变
section("既有语义不变：不存在 → NotFoundError（404）；先删派生物后删台账")
from ib.core import NotFoundError  # noqa: E402

try:
    deps.lifecycle.delete_document(scope, "不存在的-doc-id")
    print("NotFoundError 未抛出 —— 异常！")
except NotFoundError as exc:
    print("delete 不存在文档       = NotFoundError ->", exc)
