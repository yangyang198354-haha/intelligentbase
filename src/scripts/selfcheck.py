#!/usr/bin/env python
"""
@module MOD-IB-23（自我验证；**非** GROUP_D 的正式测试套件）
@implements 离线自检：装配 / 端口一致性 / 隔离 / 降级 / SSE / 鉴权纪律
@depends 全部模块（作为装配入口）
@author sub_agent_software_developer

离线自检脚本（`python scripts/selfcheck.py`）。

## 与 GROUP_D 测试套件的边界（必须说清，否则会互相以为对方覆盖了）

本脚本是 GROUP_C 的**自我验证**：证明「我写的实现能装配、能跑、关键纪律没被破坏」。
它**不是**交付物意义上的测试套件 —— 没有覆盖率目标、没有参数化矩阵、没有回归基线的维护。
正式测试套件是 GROUP_D 的职责，本脚本的用例**不应**被当作已完成的测试。

## 为什么只允许 InMemory / SQLite 替身

判据是「离线装配下关键行为成立」，不是「真实依赖的连通性」。刻意不连任何外部服务：
FreeArk 生产库、真实 Qdrant、DeepSeek、ib-embed 一律**不触达**。
反过来，若这里开始连真依赖，脚本就会在 CI 里变成「网络抖动即失败」的噪音源。

## 输出约定

每个用例打印 `PASS` / `FAIL(<原因>)`，末尾打印汇总。**任何 FAIL 都以非零码退出**，
避免「红着退出但没人看」。
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from typing import Any, Callable

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

#: 自检专用离线装配（**在导入任何 ib 模块之前**设定）。
_OFFLINE_ENV = {
    "IB_OFFLINE_MODE": "1",
    "IB_CONFIG_SOURCE": "dict",
    "IB_OFFLINE_TOKEN": "selfcheck-offline-token",
    "IB_LOG_LEVEL": "ERROR",
}
for _k, _v in _OFFLINE_ENV.items():
    os.environ.setdefault(_k, _v)

_RESULTS: list[tuple[str, bool, str]] = []


def _case(name: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def _decorator(fn: Callable[[], None]) -> Callable[[], None]:
        def _runner() -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - 自检要报告失败原因而不是崩掉
                detail = f"{type(exc).__name__}: {exc}"
                _RESULTS.append((name, False, detail))
                print(f"FAIL  {name}\n      {detail}")
                traceback.print_exc(limit=3)
            else:
                _RESULTS.append((name, True, ""))
                print(f"PASS  {name}")

        _runner.__name__ = fn.__name__
        return _runner

    return _decorator


# --------------------------------------------------------------------------- #
# 离线装配的配置（**完整键名按 module_design §5**，不新增/改名）
# --------------------------------------------------------------------------- #

OFFLINE_RAW: dict[str, Any] = {
    "config_source": "dict",
    "offline_mode": True,
    "ledger_backend": "memory",
    "blob": {"enabled": True, "root": os.path.join(_SRC, ".selfcheck_blobs")},
    "retrieval": {"top_k": 3, "score_threshold": 0.0, "candidate_multiplier": 2},
    "vectorstore": {"backend": "memory"},
    "embedding": {"backend": "fake"},
    "llm": {"backend": "fake"},
    "projects": {
        "p_alpha": {
            "name": "自检项目 A",
            "active_collection_version": "1",
            "embedding_model_id": "bge-m3",
            "dim": 1024,
            "kb_ids": ["kb_a"],
        },
        "p_beta": {
            "name": "自检项目 B",
            "active_collection_version": "1",
            "embedding_model_id": "bge-m3",
            "dim": 1024,
            "kb_ids": ["kb_b"],
        },
    },
}


def _deps() -> Any:
    from ibweb.composition import build_deps

    return build_deps(OFFLINE_RAW)


def _project_record(project_id: str) -> Any:
    from ib.core import ProjectRecord

    return ProjectRecord(
        project_id=project_id,
        name=project_id,
        active_collection_version="1",
        embedding_model_id="bge-m3",
        dim=1024,
        created_at="",
    )


def _kb_record(project_id: str, kb_id: str) -> Any:
    from ib.core import KbRecord

    return KbRecord(kb_id=kb_id, project_id=project_id, name=kb_id, created_at="")


# --------------------------------------------------------------------------- #
# 用例
# --------------------------------------------------------------------------- #


@_case("core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）")
def core_framework_free() -> None:
    """在**干净子进程**里导入 `ib.core`，断言 `sys.modules` 无第三方顶层包。

    必须用子进程：主进程已经导入了 django / drf，`sys.modules` 早就不干净了，
    在主进程断言等于什么都没断言。
    """
    code = (
        "import sys;"
        "import ib.core;"
        # 允许的顶层模块：stdlib + 自身包
        "std=set(sys.stdlib_module_names);"
        "bad=sorted({m.split('.')[0] for m in sys.modules"
        " if not m.startswith('_') and m.split('.')[0] not in std"
        " and m.split('.')[0] not in {'ib','scripts','__main__','six'}});"
        "print(','.join(bad))"
    )
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code],
        cwd=_SRC,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise AssertionError(f"子进程导入 ib.core 失败：{proc.stderr.strip()[-400:]}")
    leaked = proc.stdout.strip()
    if leaked:
        raise AssertionError(f"ib/core 引入了第三方顶层包：{leaked}")


@_case("no_forbidden_web_carrier：无 FastAPI/uvicorn/channels/redis 依赖")
def no_forbidden_web_carrier() -> None:
    """扫描源码中的 import 与声明式依赖，确认载体纪律未被破坏。

    只扫 `import` 语句，不扫注释/文档 —— 本文件的注释里就写着这些名字（说明为什么禁用），
    若连注释一起扫，用例会永远失败。
    """
    import ast
    import pathlib

    banned = {"fastapi", "uvicorn", "channels", "redis", "celery", "flask"}
    offenders: list[str] = []
    for path in pathlib.Path(_SRC).rglob("*.py"):
        if any(part in {".venv", "__pycache__", "node_modules"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            else:
                continue
            for name in names:
                if name in banned:
                    offenders.append(f"{path.relative_to(_SRC)}:{node.lineno} -> {name}")
    if offenders:
        raise AssertionError("发现禁用载体依赖：" + "; ".join(sorted(offenders)))


@_case("no_pymupdf：全仓无 fitz / PyMuPDF 引用（AGPL-3.0 硬约束）")
def no_pymupdf() -> None:
    import ast
    import pathlib

    offenders: list[str] = []
    for path in pathlib.Path(_SRC).rglob("*.py"):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            else:
                continue
            if any(n in {"fitz", "pymupdf"} for n in names):
                offenders.append(f"{path.relative_to(_SRC)}:{node.lineno}")
    if offenders:
        raise AssertionError("发现 PyMuPDF 引用（许可硬约束禁止）：" + ", ".join(offenders))


@_case("port_conformance：替身与端口签名一致（VectorStore/Ledger/Blob/Embedder）")
def port_conformance() -> None:
    """逐个检查端口方法与替身实现的**参数名集合**是否一致。

    参数名一致不是吹毛求疵：`bind_scope` 靠**参数名**注入 `scope` / `retrieval`，
    端口实现若把 `scope` 改名成 `scope_obj`，工具绑定会静默失效（LLM 侧拿到未绑定的
    scope）—— 这类缺陷在运行期表现为「检索不到东西」，极难定位。
    """
    import inspect

    from ib.blob import InMemoryBlobStore
    from ib.core import ports as P
    from ib.embedding import FakeEmbedder, InProcessBgeM3Embedder, LocalHttpEmbedder
    from ib.ledger import InMemoryLedgerRepository
    from ib.vectorstore import InMemoryVectorStore

    # R2：Embedder 的**三形态**都必须过同一端口检查（契约 §8「形态可逆」）。
    # 进程内形态与 HTTP 形态是两份独立实现（有意不共享代码），任一方漂移都要在此暴露。
    pairs = [
        (P.VectorStore, InMemoryVectorStore),
        (P.LedgerRepository, InMemoryLedgerRepository),
        (P.BlobStore, InMemoryBlobStore),
        (P.Embedder, FakeEmbedder),
        (P.Embedder, LocalHttpEmbedder),
        (P.Embedder, InProcessBgeM3Embedder),
    ]
    problems: list[str] = []
    for port, impl in pairs:
        for name, member in vars(port).items():
            if name.startswith("_"):
                continue
            target = getattr(impl, name, None)
            if target is None:
                problems.append(f"{impl.__name__} 缺方法 {name}")
                continue
            want = {
                p
                for p in inspect.signature(member).parameters
                if p not in {"self", "cls"}
            }
            got = {
                p
                for p in inspect.signature(target).parameters
                if p not in {"self", "cls"}
            }
            if want != got:
                problems.append(
                    f"{port.__name__}.{name}: 端口参数 {sorted(want)} != 实现 {sorted(got)}"
                )
    if problems:
        raise AssertionError("；".join(problems))


@_case("authz_injection_required：生产模式未注入策略即启动失败，且只报键名")
def authz_injection_required() -> None:
    from ib.core import StartupError
    from ibweb.authz import build_authz

    saved = os.environ.pop("IB_AUTHZ_POLICY_MODULE", None)
    try:
        try:
            build_authz(offline_mode=False, project_id="p1")
        except StartupError as exc:
            msg = str(exc)
            assert "IB_AUTHZ_POLICY_MODULE" in msg, f"错误信息未点名缺失的键：{msg}"
            return
        raise AssertionError("生产模式未注入 AuthzPolicy 却未启动失败（AC-IB-11-05 被破坏）")
    finally:
        if saved is not None:
            os.environ["IB_AUTHZ_POLICY_MODULE"] = saved


@_case("config_error_reports_key_only：配置校验只报键名，不回显值")
def config_error_reports_key_only() -> None:
    """构造一个必然失败的配置，确认错误信息里**没有**任何真实值。

    判据是「值不出现在消息里」，而不是「消息非空」——后者可以通过随便报个字符串通过。
    """
    marker = "SUPER-SECRET-MARKER-VALUE"
    from ib.config import DictConfigurationSource, ConfigurationResolver

    resolver = ConfigurationResolver(
        DictConfigurationSource(
            {
                "offline_mode": False,
                "vectorstore": {"backend": marker},
                "llm": {"backend": "openai_compatible", "api_key_env": "IB_SELFCHECK_ABSENT_KEY"},
                "embedding": {"backend": "fake"},
            }
        )
    )
    errors = resolver.validate(env={})  # 空环境 → LLM key 必缺
    assert errors, "非法后端取值 + 缺失凭据，却一条校验错误都没有"
    joined = " ".join(str(e) for e in errors)
    assert marker not in joined, f"配置校验回显了取值：{joined}"
    assert "IB_SELFCHECK_ABSENT_KEY" in joined or "IB_VECTORSTORE_BACKEND" in joined, (
        f"错误信息未包含键名：{joined}"
    )


@_case("magic_sniff_rejects_renamed_file：改名攻击被拒（扩展名与内容不符）")
def magic_sniff_rejects_renamed_file() -> None:
    from ib.core import ValidationError
    from ib.lifecycle import DocumentLifecycle

    deps = _deps()
    lifecycle: DocumentLifecycle = deps.lifecycle
    # 正例：合法 txt（文本系无固定魔数，判定为「无 NUL 且可按 UTF-8/GBK 解码」）
    lifecycle.validate_upload("ok.txt", 12, "知识库内容".encode("utf-8"))
    # 负例 1：把文本改成 .pdf → 无 PDF 魔数 → 拒绝（改名攻击的典型形态）
    try:
        lifecycle.validate_upload("evil.pdf", 12, b"hello world\n")
    except ValidationError:
        pass
    else:
        raise AssertionError("扩展名声称 pdf 但无 PDF 魔数，却通过了校验")
    # 负例 2：.txt 里塞二进制（含 NUL）→ 拒绝（否则二进制会被当文本灌进索引）
    try:
        lifecycle.validate_upload("binary.txt", 8, b"\x00\x01\x02\x03")
    except ValidationError:
        pass
    else:
        raise AssertionError("含 NUL 的二进制内容被当作 txt 通过校验")
    # 负例 3：不支持的扩展名 → 拒绝（只回显扩展名，不回显用户内容）
    try:
        lifecycle.validate_upload("shell.exe", 8, b"MZ\x90\x00")
    except ValidationError as exc:
        assert "exe" in str(exc), f"错误信息未点明扩展名：{exc}"
    else:
        raise AssertionError("不支持的扩展名通过了校验")


@_case("ledger_state_machine_and_lease：SQLite 台账状态机 + 单租约（WAL）")
def ledger_state_machine_and_lease() -> None:
    """在临时 SQLite 上验证：pending → claim → indexed，且第二个 worker 无法重复认领。

    刻意用**真实 SQLite**（而非 InMemory 替身）：租约的「条件 UPDATE + 单写事务」
    语义只在真库上才成立，内存替身的加锁实现再正确也证明不了 SQL 语句写对了。
    仍是本地文件，不触网。
    """
    import tempfile

    from ib.core import DocStatus, Scope
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    with tempfile.TemporaryDirectory() as tmp:
        repo = SqliteLedgerRepository(os.path.join(tmp, "ledger.sqlite3"))
        try:
            scope = Scope(project_id="p1", kb_ids=("kb1",))
            repo.upsert_project(_project_record("p1"))
            repo.upsert_kb(_kb_record("p1", "kb1"))
            # 归属断言：未登记的 kb_id 必须被拒（越权请求不得留下任何痕迹）
            from ib.core import ScopeViolationError

            try:
                repo.create_document(Scope(project_id="p1", kb_ids=("kb_missing",)), "x.txt", "txt", 1, "h", None)
            except ScopeViolationError:
                pass
            else:
                raise AssertionError("未登记的知识库通过了归属断言")

            doc = repo.create_document(scope, "a.txt", "txt", 11, "sha-abc", None)
            assert doc.status == str(DocStatus.PENDING)

            first = repo.claim_pending("worker-1", 300, 5)
            assert [d.doc_id for d in first] == [doc.doc_id], "首个 worker 未认领到 pending 文档"
            # 第二个 worker 不得再认领同一篇（否则同一文档被处理两次，索引里出现重复块）
            second = repo.claim_pending("worker-2", 300, 5)
            assert second == [], f"文档被重复认领：{[d.doc_id for d in second]}"

            repo.mark_indexed(scope, doc.doc_id, "1", 3)
            got = repo.get_document(scope, doc.doc_id)
            assert got is not None and got.status == str(DocStatus.INDEXED)
            assert got.chunk_count == 3

            # 未过期的租约不得被回收（否则正在处理的文档会被第二个 worker 抢走重复处理）
            assert int(repo.reap_expired_leases("2000-01-01T00:00:00Z")) == 0
            # 另一篇被认领的文档：租约到期后必须回到 pending（崩溃 worker 的残留要能自愈）
            doc2 = repo.create_document(scope, "b.txt", "txt", 5, "sha-def", None)
            assert [d.doc_id for d in repo.claim_pending("worker-1", 300, 5)] == [doc2.doc_id]
            assert int(repo.reap_expired_leases("2999-01-01T00:00:00Z")) == 1
            healed = repo.get_document(scope, doc2.doc_id)
            assert healed is not None and healed.status == str(DocStatus.PENDING), (
                f"崩溃 worker 的残留未回到 pending：{getattr(healed, 'status', None)}"
            )
        finally:
            repo.close()  # 不关连接会导致 Windows 上临时目录无法删除（PermissionError）


@_case("isolation_scope_required：检索降级时 filter 仍含 project_id，且跨项目不可见")
def isolation_scope_required() -> None:
    """跨项目隔离：A 项目写入的向量，B 项目检索不到。"""
    deps = _deps()
    from ib.core import PointPayload, Scope, VectorPoint

    p_alpha = Scope(project_id="p_alpha")
    p_beta = Scope(project_id="p_beta")
    vector = [0.1] * 1024
    deps.vectors.bind_collection("ib_p_alpha_v1")
    deps.vectors.upsert(
        [
            VectorPoint(
                id="pt-1",
                vector=vector,
                payload=PointPayload(
                    project_id="p_alpha",
                    kb_id="kb_a",
                    doc_id="d1",
                    doc_name="a.txt",
                    chunk_index=0,
                    content="alpha 专属内容",
                    locator="l1",
                    source_kind="text",
                    page_or_section="1",
                    content_hash="h1",
                    indexed_model="bge-m3",
                    indexed_dim=1024,
                    created_at="",
                    blob_ref=None,
                    schema_version=1,
                ),
            )
        ],
        wait=True,
    )
    hits_alpha = deps.vectors.query(
        vector, scope=p_alpha, top_k=5, score_threshold=0.0, filter=None
    )
    assert len(hits_alpha) == 1, f"本项目内应命中 1 条，实际 {len(hits_alpha)}"
    # B 项目：即便绑定到 A 的集合名，filter 里的 project_id 仍会把它挡掉
    deps.vectors.bind_collection("ib_p_alpha_v1")
    hits_beta = deps.vectors.query(
        vector, scope=p_beta, top_k=5, score_threshold=0.0, filter=None
    )
    assert hits_beta == [], f"跨项目泄露：B 项目检索到 {len(hits_beta)} 条 A 项目数据"

    # 反向断言：集合名与 payload 的 project_id 不一致时必须**拒绝写入**（而非静默写入）
    from ib.core import ScopeViolationError, VectorPoint as VP

    deps.vectors.bind_collection("ib_p_beta_v1")
    try:
        deps.vectors.upsert([VP(id="pt-2", vector=vector, payload=hits_alpha[0].payload)], wait=True)
    except ScopeViolationError:
        pass
    else:
        raise AssertionError("跨项目写入未被拒绝（collection 与 payload 的 project_id 不一致却写入成功）")


@_case("retrieval_fail_open：embedding 不可用时降级而非抛异常（MOD-IB-15 永不抛）")
def retrieval_fail_open() -> None:
    """把 embedder 换成一个必然超时的实现，检索必须返回 degraded=True 而不是抛。"""
    deps = _deps()
    from ib.core import DependencyUnavailableError, Scope
    from ib.retrieval import RetrievalService

    class _BrokenEmbedder:
        def embed_documents(self, texts: Any, **kw: Any) -> Any:
            raise DependencyUnavailableError("selfcheck: 故意不可用", dependency="embedding")

        def embed_query(self, text: str, *, timeout_s: float) -> Any:
            raise DependencyUnavailableError("selfcheck: 故意不可用", dependency="embedding")

        def health(self) -> Any:
            from ib.core import HealthStatus

            return HealthStatus(ok=False, detail="selfcheck")

        def warmup(self) -> None:
            return None

        def descriptor(self) -> Any:
            raise NotImplementedError

    svc = RetrievalService(
        embedder=_BrokenEmbedder(),
        vectors=deps.vectors,
        resolver=deps.collections,
        project_provider=lambda pid: deps.projects[pid],
        top_k=3,
        score_threshold=0.0,
        candidate_multiplier=2,
        hot_timeout_s=0.05,
    )
    result = svc.search("任意问题", scope=Scope(project_id="p_alpha"))
    assert result.degraded is True, "embedding 不可用却未标记降级"
    assert result.degrade_reason is not None
    # 工具形态也必须失败开放（ok=True + degraded）—— 否则编排会因为工具抛异常而中断整轮问答
    tool_result = svc.search_as_tool("任意问题", scope=Scope(project_id="p_alpha"))
    assert getattr(tool_result, "ok", False) is True, "工具形态未失败开放"


@_case("retrieval_happy_path：读路径**不降级**且能命中（防止『一切静默降级』掩盖缺陷）")
def retrieval_happy_path() -> None:
    """依赖齐备时必须 `degraded=False` 且真的召回。

    这个用例是被一次真实缺陷逼出来的：检索层把**任何**异常都转成 `degraded=True`
    （fail-open 是正确设计），于是「读路径 provider 抛 NameError」这种硬缺陷表现为
    「知识库永远为空」而不报错 —— 只看 degraded 断言完全测不出来。因此这里必须
    断言 `degraded is False` **并且** `hits` 非空：两条都过，才说明整条读路径是通的
    （provider → resolver → embedder → vectorstore → 映射）。
    """
    deps = _deps()
    from ib.core import Scope

    scope = Scope(project_id="p_alpha")  # isolation 用例已在此项目写入 1 个向量点
    result = deps.retrieval.search("任意问题", scope=scope)
    assert result.degraded is False, (
        f"读路径处于降级状态（degrade_reason={result.degrade_reason}）—— "
        "依赖齐备时降级即为缺陷，且会被 fail-open 语义掩盖"
    )
    assert result.hits, "读路径未召回任何内容（向量已写入却查不到）"
    assert result.hits[0].doc_id == "d1"
    # 工具形态：文本必须包含可读定位信息（LLM 需要能说出「来自哪个文件」）
    tool_result = deps.retrieval.search_as_tool("任意问题", scope=scope)
    assert tool_result.ok is True and tool_result.degraded is False
    assert "a.txt" in tool_result.content, tool_result.content[:200]


@_case("sse_frame_and_done_terminator：SSE 帧格式与 done 终止条件")
def sse_frame_and_done_terminator() -> None:
    from ib.core import StreamEvent, StreamEventKind
    from ib.streaming import to_sse
    from ibweb.sse import encode_events

    frames = list(
        encode_events(
            iter(
                [
                    StreamEvent(StreamEventKind.REASONING, "正在分析问题…"),
                    StreamEvent(StreamEventKind.CONTENT, "答案"),
                    StreamEvent(StreamEventKind.DONE),
                ]
            )
        )
    )
    joined = "".join(frames)
    assert "event: reasoning" in joined and "event: content" in joined, joined
    assert "event: done" in joined
    assert joined.endswith("\n\n"), "SSE 帧未以空行结束（浏览器不会派发该事件）"

    # 异常路径：生成器中途抛错也必须以 done 结尾（否则前端永远转圈）
    def _boom() -> Any:
        yield StreamEvent(StreamEventKind.CONTENT, "半句")
        raise RuntimeError("selfcheck boom")

    frames2 = "".join(encode_events(_boom()))
    assert "event: error" in frames2, frames2
    assert "event: done" in frames2, "异常路径未补 done 事件"
    assert "selfcheck boom" not in frames2, "错误事件回显了内部异常文本（信息泄漏）"


@_case("orchestration_events_order：degraded 先于 content，且只发一条 content")
def orchestration_events_order() -> None:
    """编排事件顺序是本项目最容易被破坏的对外契约之一（见 Orchestrator.run 文档）。"""
    deps = _deps()

    class _LlmStub:
        """最小 LLM 替身：路由把问题定向到 knowledge-expert，而该专家**必然失败**。

        这样一次运行就能同时覆盖三件事：条件边 fan-out、专家级降级、聚合。
        """

        def build_router(self) -> Any:
            class _Role:
                name = "router"

                def __init__(self) -> None:
                    self.impl = lambda prompt: '{"experts": ["knowledge-expert"]}'

            return _Role()

        def build_expert(self, spec: Any) -> Any:
            class _Broken:
                name = str(getattr(spec, "name", "expert"))

                def __init__(self) -> None:
                    self.impl = self._invoke

                def _invoke(self, prompt: str) -> str:
                    raise RuntimeError("selfcheck: 专家不可用")

            return _Broken()

        def build_aggregator(self) -> Any:
            class _Agg:
                name = "aggregator"

                def __init__(self) -> None:
                    self.impl = lambda prompt: "最终答案"

            return _Agg()

        def health(self) -> Any:
            from ib.core import HealthStatus

            return HealthStatus(ok=True)

        def describe_egress(self) -> Any:
            from ib.core import EgressDescriptor

            return EgressDescriptor(remote=False, endpoint_host="", data_categories=[])

    from ib.context import make_request_context
    from ib.core import GraphConfig, Scope
    from ib.experts import EXPERT_SPECS
    from ib.orchestration import build_graph

    orchestrator = build_graph(
        llm=_LlmStub(),
        experts=EXPERT_SPECS,
        tools=[],
        sessions=deps.sessions,
        config=GraphConfig(max_expert_steps=8),
        router=None,
        scope=Scope(project_id="p_alpha"),
        tools_by_expert={},
    )
    ctx = make_request_context(project_id="p_alpha", actor_id="u1", session_id="s1")
    events = list(orchestrator.run("测试问题", ctx=ctx, session_key=ctx.session_key))
    kinds = [str(e.kind) for e in events]
    assert kinds[-1] == "done", f"流未以 done 结尾：{kinds}"
    assert kinds.count("content") == 1, f"content 事件应恰为 1 条，实际 {kinds.count('content')}：{kinds}"
    assert "degraded" in kinds, f"专家失败却无 degraded 事件：{kinds}"
    assert kinds.index("degraded") < kinds.index("content"), (
        f"degraded 必须早于 content（否则用户会把提示当成答案补充）：{kinds}"
    )
    # 内部分工词不得出现在正文（AC-IB-09-03）
    content = [e.data for e in events if str(e.kind) == "content"][0]
    for label in ("router", "expert", "聚合", "专家", "knowledge-expert"):
        assert label not in content, f"正文暴露了内部分工词汇 {label!r}：{content}"


@_case("orchestration_scope_bound_at_build：工具在构造期绑定 scope，运行期无法更改")
def orchestration_scope_bound_at_build() -> None:
    """ADR-09 的结构性保证：`BoundTool` 无参数，LLM 侧**无法**指定 scope。"""
    import inspect

    deps = _deps()
    from ib.core import Scope

    bound = deps.bind_tools(Scope(project_id="p_alpha"))
    assert bound, "未产出任何已绑定工具"
    for tool in bound:
        params = set(inspect.signature(tool.callable).parameters)
        assert not ({"scope", "retrieval"} & params), (
            f"已绑定工具暴露了 {sorted(params)}（scope/retrieval 必须完全封闭在闭包内）"
        )
    # 不同项目的绑定必须是不同闭包（复用会把 A 的 scope 带给 B）
    other = deps.bind_tools(Scope(project_id="p_beta"))
    assert other[0].callable is not bound[0].callable, "不同项目的工具绑定复用了同一闭包"

    # 显式传 scope 也必须**无效**：构造期绑定是唯一真源（覆盖而非 setdefault）。
    # 用一个记录型检索替身直接观测被注入的 scope —— 只看「不抛异常」区分不出两种实现。
    from ib.core import ToolResult
    from ib.tools import ToolRegistry, bind_scope

    seen: list[str] = []

    class _RecordingRetrieval:
        def search_as_tool(self, query: str, *, scope: Any) -> Any:
            seen.append(scope.project_id)
            return ToolResult(ok=True, content="hit")

    def _impl(query: str, *, scope: Any, retrieval: Any) -> Any:
        return retrieval.search_as_tool(query, scope=scope)

    registry = ToolRegistry()
    registry.register(
        __import__("ib.core", fromlist=["ToolSpec"]).ToolSpec(name="t", description="d", needs_scope=True),
        _impl,
    )
    tool = bind_scope(registry.registered(), Scope(project_id="p_alpha"), _RecordingRetrieval())[0]
    tool.callable("问题", scope=Scope(project_id="p_beta"))
    assert seen == ["p_alpha"], (
        f"调用方传入的 scope 覆盖了构造期绑定（实际使用 {seen}）—— 跨项目读取路径"
    )


@_case("http_contract_offline：离线装配下端点状态码/头纪律（含 ?token= 显式 400）")
def http_contract_offline() -> None:
    """用 Django 测试客户端跑离线装配的端点。**不连任何外部服务**。"""
    os.environ["DJANGO_SETTINGS_MODULE"] = "ibweb.settings"
    os.environ["IB_CONFIG_SOURCE"] = "dict"

    # 先装配再 `django.setup()`：`apps.ready()` 会调 `build_deps()`，而 `ready()` 在
    # `django.setup()` 内部执行 —— 若不先注入配置字典，ready() 会因为
    # `IB_CONFIG_SOURCE=dict` 而报「未注入配置字典」（顺序依赖，且失败信息会指向错误方向）。
    from ibweb.composition import build_application, build_deps

    deps = build_deps(OFFLINE_RAW)

    import django

    django.setup()
    build_application(deps)

    from django.test import Client

    client = Client()
    token = os.environ["IB_OFFLINE_TOKEN"]
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # /healthz 免鉴权
    assert client.get("/healthz").status_code == 200
    r = client.get("/healthz/deps")
    assert r.status_code == 200, r.content
    payload = r.json()
    assert set(payload) == {"qdrant", "embed", "llm", "egress"}, payload
    assert "data_categories" in payload["egress"]

    # 无令牌 → 401（**不是** 静默放行）
    r = client.get("/api/files")
    assert r.status_code == 401, f"缺少令牌却得到 {r.status_code}"
    # 令牌进查询串 → 显式 400（?token= 纪律）
    r = client.get("/api/files?token=whatever")
    assert r.status_code == 400, f"?token= 应显式 400，实际 {r.status_code}"
    # 有效令牌 → 200 + 分页外壳
    r = client.get("/api/files", **auth)
    assert r.status_code == 200, r.content
    assert set(r.json()) == {"items", "total"}

    # 上传：合法 txt 走通 201
    from django.core.files.uploadedfile import SimpleUploadedFile

    upload = SimpleUploadedFile("note.txt", "知识库内容示例".encode("utf-8"), content_type="text/plain")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": upload}, **auth)
    assert r.status_code == 201, r.content
    doc = r.json()
    assert doc["status"] == "pending" and doc["doc_name"] == "note.txt"

    # 上传：魔数不符 → 400（声明 pdf 但内容是纯文本）
    bad = SimpleUploadedFile("note.pdf", b"not a pdf at all\n", content_type="application/pdf")
    r = client.post("/api/files", {"kb_id": "kb_a", "file": bad}, **auth)
    assert r.status_code == 400, f"魔数不符应 400，实际 {r.status_code}"

    # 上传：kb_id 不属于本项目 → 403（**不是** 404）
    r = client.post("/api/files", {"kb_id": "kb_b", "file": SimpleUploadedFile("n2.txt", b"hi\n")}, **auth)
    assert r.status_code == 403, f"跨项目 kb_id 应 403，实际 {r.status_code}"

    # 重试非 failed 文档 → 409
    r = client.post(f"/api/files/{doc['doc_id']}/retry", **auth)
    assert r.status_code == 409, f"重试 pending 文档应 409，实际 {r.status_code}"

    # 删除不存在的文档 → 404
    r = client.delete("/api/files/does-not-exist", **auth)
    assert r.status_code == 404, f"删除不存在文档应 404，实际 {r.status_code}"

    # SSE：头纪律 + 流以 done 结尾
    r = client.get("/api/chat/stream?q=测试问题", **auth)
    assert r.status_code == 200, getattr(r, "content", b"")
    assert r["Content-Type"].startswith("text/event-stream"), r["Content-Type"]
    assert r["X-Accel-Buffering"] == "no", "缺少 X-Accel-Buffering: no（nginx 会缓冲，首字节永不外发）"
    body = b"".join(r.streaming_content).decode("utf-8")
    assert "event: done" in body, body[:400]

    # 重建：启动 202，进度 200
    r = client.post("/api/rebuild", **auth)
    assert r.status_code in (202, 409), r.content
    if r.status_code == 202:
        job_id = r.json()["job_id"]
        r2 = client.get(f"/api/rebuild/{job_id}", **auth)
        assert r2.status_code == 200, r2.content
        assert set(r2.json()) == {"job_id", "state", "indexed", "failed", "pending", "done"}


# --------------------------------------------------------------------------- #
# R2 用例（L-03：ib-embed 服务端；M-02：页面图关联 / 读路径）
# --------------------------------------------------------------------------- #


def _http_json(
    method: str, url: str, payload: Any = None, *, timeout: float = 10.0
) -> tuple[int, Any, dict[str, str]]:
    """极简 HTTP 客户端（**只用 stdlib**）：返回 `(status, 解析后的 JSON 或原始文本, 头)`。

    刻意不引入 `requests`：IB-EMBED 的客户端侧就以「零第三方依赖」为纪律，自检脚本
    同守该纪律，才能在最小环境里跑起来。`urllib.error.HTTPError` 本身带响应体，
    故 4xx/5xx 也能读到统一错误体。
    """
    import json as _json
    import urllib.error
    import urllib.request

    data = None if payload is None else _json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"} if data else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - 本机回环
            raw = response.read().decode("utf-8")
            status = int(response.status)
            headers = {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        status = int(exc.code)
        headers = {k.lower(): v for k, v in (exc.headers or {}).items()}
    try:
        return status, _json.loads(raw), headers
    except Exception:  # noqa: BLE001 - 非 JSON 响应原样返回（便于在断言信息里看到）
        return status, raw, headers


def _serve_ib_embed(cfg: Any, runtime: Any) -> tuple[Any, str]:
    """在**回环的随机端口**上启动一个 ib-embed 实例，返回 `(httpd, base_url)`。

    端口用 `0`（内核分配）：自检与任何本地服务都不冲突，也不需要清理固定端口占用。
    """
    import threading

    from ib_embed.server import build_http_server

    httpd = build_http_server(cfg, runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=httpd.serve_forever, name="ib-embed-selfcheck", daemon=True)
    thread.start()
    host, port = httpd.server_address[0], httpd.server_address[1]
    return httpd, f"http://{host}:{port}"


@_case("ib_embed_config_keys：11 个键的键名清单 + 缺权重目录即拒绝（只报键名）")
def ib_embed_config_keys() -> None:
    """配置契约（IFC-IB-274 / tech_stack §1.2）：键名清单是**闭集**，不得增删。"""
    from ib_embed.config import DEFAULT_KEYS, ConfigError, load_config

    expected = {
        "IB_EMBED_HOST",
        "IB_EMBED_PORT",
        "IB_EMBED_MODEL_ID",
        "IB_EMBED_DIM",
        "IB_EMBED_MODEL_PATH",
        "IB_EMBED_MAX_BATCH",
        "IB_EMBED_MAX_TOKENS",
        "IB_EMBED_MAX_CONCURRENCY",
        "IB_EMBED_QUEUE_DEPTH",
        "IB_EMBED_THREADS",
        "IB_EMBED_MEMORY_LIMIT_MB",
    }
    assert set(DEFAULT_KEYS) == expected, f"键名清单漂移：{sorted(set(DEFAULT_KEYS) ^ expected)}"
    assert len(DEFAULT_KEYS) == 11, f"键数应为 11，实际 {len(DEFAULT_KEYS)}"

    # 缺 IB_EMBED_MODEL_PATH → ConfigError，且消息**只含键名**
    try:
        load_config({})
    except ConfigError as exc:
        assert "IB_EMBED_MODEL_PATH" in str(exc), f"错误消息未指明键名：{exc}"
    else:
        raise AssertionError("缺 IB_EMBED_MODEL_PATH 却通过了配置校验")

    # 只读 IB_EMBED_* 前缀：塞入客户端键（IB_EMBED_URL）不得被服务端误当配置项
    cfg = load_config({"IB_EMBED_MODEL_PATH": "/opt/bge-m3", "IB_EMBED_URL": "http://x"})
    assert cfg.model_path == "/opt/bge-m3"
    assert cfg.model_id == "bge-m3" and cfg.dim == 1024, cfg


@_case("ib_embed_isolation：ib_embed 不 import ib；且无任何 ib.* 模块 import ib_embed（C8）")
def ib_embed_isolation() -> None:
    """C8 的结构性校验：MOD-IB-26 **不被任何模块引用**，且自身不依赖 `ib.*`。"""
    import importlib
    import pathlib
    import re
    import sys

    pkg_dir = pathlib.Path(_SRC) / "ib_embed"
    assert pkg_dir.is_dir(), f"缺少 {pkg_dir}"

    # 1) 服务端包内不得出现 `import ib.` / `from ib.`（包括 `ib.core` 契约）
    offenders: list[str] = []
    for path in sorted(pkg_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s*(?:from\s+ib[.\s]|import\s+ib[.\s])", text, re.MULTILINE):
            offenders.append(f"{path.name}:{text[:match.start()].count(chr(10)) + 1}")
    assert not offenders, f"ib_embed 依赖了 ib.*（C8）：{offenders}"

    # 2) 全仓（*除* selfcheck 自身与 ib_embed 包）不得出现 `import ib_embed`
    repo_offenders: list[str] = []
    for path in sorted((pathlib.Path(_SRC)).rglob("*.py")):
        if pkg_dir in path.parents:
            continue
        if path.name == "selfcheck.py":
            continue  # 自检脚本**必须**能装配它（否则无从验证线协议）
        text = path.read_text(encoding="utf-8")
        if re.search(r"^\s*(?:from\s+ib_embed|import\s+ib_embed)", text, re.MULTILINE):
            repo_offenders.append(str(path.relative_to(pathlib.Path(_SRC))))
    assert not repo_offenders, f"有模块 import 了 ib_embed（违反 C8 单向隔离）：{repo_offenders}"

    # 3) 导入 ib_embed.server 之后，`sys.modules` 里不得出现新的 ib.* 模块
    before = {name for name in sys.modules if name == "ib" or name.startswith("ib.")}
    importlib.import_module("ib_embed.server")
    after = {name for name in sys.modules if name == "ib" or name.startswith("ib.")}
    assert after <= before, f"导入 ib_embed.server 引入了 ib.* 模块：{sorted(after - before)}"


@_case("embed_three_form_conformance：http/inproc/fake 三形态通过同一端口一致性检查")
def embed_three_form_conformance() -> None:
    """契约 §8「形态可逆」：三形态的端口方法**参数名集合**与 descriptor 字段集必须一致。

    参数名一致不是风格问题：`LocalHttpEmbedder` 与 `InProcessBgeM3Embedder` 是**两份独立
    实现**（有意不共享代码，见 `inproc.py` 模块文档），任何一方被改动都可能静默漂移。
    """
    import inspect

    from ib.core import ports as P
    from ib.embedding import FakeEmbedder, InProcessBgeM3Embedder, LocalHttpEmbedder

    def _params(fn: Any) -> set[str]:
        return {p for p in inspect.signature(fn).parameters if p not in {"self", "cls"}}

    problems: list[str] = []
    for impl in (LocalHttpEmbedder, InProcessBgeM3Embedder, FakeEmbedder):
        for name, member in vars(P.Embedder).items():
            if name.startswith("_"):
                continue
            target = getattr(impl, name, None)
            if target is None:
                problems.append(f"{impl.__name__} 缺方法 {name}")
                continue
            want, got = _params(member), _params(target)
            if want != got:
                problems.append(f"{impl.__name__}.{name}: 端口 {sorted(want)} != 实现 {sorted(got)}")
    assert not problems, "；".join(problems)

    # descriptor 五字段逐字段一致（不联网：inproc 未加载时回落配置声明值，http 的
    # descriptor() 会尝试连接 —— 故此处**只比较字段集**，不调用 http 形态的 descriptor）
    inproc = InProcessBgeM3Embedder(model_id="bge-m3", dim=1024, model_path="/nowhere")
    fake = FakeEmbedder(dim=1024, model_id="bge-m3")
    for impl in (inproc, fake):
        fields = set(impl.descriptor().__dataclass_fields__)
        assert fields == {"model_id", "dim", "normalized", "max_tokens", "device"}, (impl, fields)
        assert impl.descriptor().dim == impl.dim() == 1024
        assert impl.descriptor().normalized is True

    # inproc 未配置权重目录 → **可读错误**而非 import 期崩溃（IFC-IB-275）
    from ib.core import DependencyUnavailableError

    broken = InProcessBgeM3Embedder(model_id="bge-m3", dim=1024, environ={})
    try:
        broken.embed_query("x", timeout_s=1.0)
    except DependencyUnavailableError as exc:
        assert "IB_EMBED_MODEL_PATH" in str(exc), f"错误不可读（未指明键名）：{exc}"
    else:
        raise AssertionError("缺权重目录却成功做了推理")

    # `build_embedder` 的取值域扩展为 {http, inproc, fake}（键名与默认值不变）
    from ib.embedding import build_embedder

    class _Cfg:
        class embedding:  # noqa: N801 - 复刻配置对象的形状
            backend = "inproc"
            dim = 1024
            model_id = "bge-m3"
            url = ""
            cold_timeout_s = 120.0
            cold_max_retries = 3
            cold_batch_size = 16
            hot_timeout_s = 3.0
            hot_max_retries = 1

    assert isinstance(build_embedder(_Cfg()), InProcessBgeM3Embedder), "inproc 未映射到进程内形态"
    # `http` 仍是**默认落点**：值域扩展不得改变既有默认（否则升级即静默换形态）
    _Cfg.embedding.backend = "bogus"
    assert isinstance(build_embedder(_Cfg()), LocalHttpEmbedder), "未知值未回落到默认 http 形态"


@_case("ib_embed_wire_protocol：healthz 永不 5xx / 保序 / 批上限 / 过载快速失败 / 绝无部分向量")
def ib_embed_wire_protocol() -> None:
    """对**真实监听的回环端口**发请求（真 socket、真 JSON、真状态码）。

    运行时用 `FakeRuntime`（确定性伪向量）：C5 明令「不得在测试中联网下载 bge-m3 权重」，
    故真实推理不在自检范围内（见 code_review_report 的「本地不可验证项」）。
    """
    from ib_embed.config import EmbedConfig
    from ib_embed.runtime import FakeRuntime, InferenceUnavailable, RuntimeBatch, UnavailableRuntime

    def _cfg(**over: Any) -> Any:
        base = dict(
            host="127.0.0.1",
            port=0,
            model_id="bge-m3",
            dim=1024,
            model_path="/opt/bge-m3",
            max_batch=4,
            max_tokens=64,
            max_concurrency=1,
            queue_depth=0,
            threads=1,
            memory_limit_mb=64,
        )
        base.update(over)
        return EmbedConfig(**base)  # type: ignore[arg-type]

    runtime = FakeRuntime(dim=1024, model_id="bge-m3")
    httpd, base = _serve_ib_embed(_cfg(), runtime)
    try:
        # /healthz：未加载 → 200 且 ok=false（**永不 5xx、永不抛**）
        status, body, _ = _http_json("GET", f"{base}/healthz")
        assert status == 200, f"healthz 应恒 200，实际 {status}"
        assert body["ok"] is False and "detail" in body, body

        # /embed 未就绪 → 503（5xx = 重试可能有用）
        status, body, _ = _http_json(
            "POST", f"{base}/embed", {"texts": ["a"], "model": "bge-m3", "mode": "document"}
        )
        assert status == 503 and body["code"] == "model_not_ready", (status, body)

        # /warmup 幂等：两次都 200
        for _ in range(2):
            status, body, _ = _http_json("POST", f"{base}/warmup", {"model": "bge-m3"})
            assert status == 200 and body["ok"] is True, (status, body)

        # /descriptor：**恰好**五个字段（IFC-IB-271 逐字段一致，不得增删）
        status, body, _ = _http_json("POST", f"{base}/descriptor", {"model": "bge-m3"})
        assert status == 200, (status, body)
        assert set(body) == {"model_id", "dim", "normalized", "max_tokens", "device"}, body
        assert body["dim"] == 1024 and body["model_id"] == "bge-m3"

        # /embed 正常：**保序** + 数量/维度三方一致
        texts = ["第一段内容", "第二段内容", "第三段内容"]
        status, body, _ = _http_json(
            "POST", f"{base}/embed", {"texts": texts, "model": "bge-m3", "mode": "document"}
        )
        assert status == 200, (status, body)
        assert body["count"] == len(texts) and len(body["vectors"]) == len(texts), body
        assert body["dim"] == 1024 and all(len(v) == 1024 for v in body["vectors"])
        swapped = list(reversed(texts))
        status2, body2, _ = _http_json(
            "POST", f"{base}/embed", {"texts": swapped, "model": "bge-m3", "mode": "document"}
        )
        assert status2 == 200
        assert body2["vectors"] == list(reversed(body["vectors"])), "向量未按入参位置保序"
        # 规范性：每个向量 L2 范数 ≈ 1
        for vec in body["vectors"]:
            norm = sum(float(v) * float(v) for v in vec) ** 0.5
            assert abs(norm - 1.0) < 1e-6, f"向量未归一化：norm={norm}"

        # 批上限：4xx + 回显 max_batch（使「客户端 cold_batch > 服务端 MAX_BATCH」一眼可定位）
        status, body, _ = _http_json(
            "POST", f"{base}/embed", {"texts": ["x"] * 5, "model": "bge-m3", "mode": "document"}
        )
        assert status == 400 and body["code"] == "batch_too_large" and body["max_batch"] == 4, body

        # 跨模型 → 409（4xx = 重试无用）
        status, body, _ = _http_json(
            "POST", f"{base}/embed", {"texts": ["x"], "model": "other", "mode": "document"}
        )
        assert status == 409 and body["code"] == "model_mismatch", (status, body)

        # 请求体不合法 → 400（枚举 / 类型 / 空数组）
        for payload in (
            {"texts": ["x"], "model": "bge-m3", "mode": "bogus"},
            {"texts": "x", "model": "bge-m3", "mode": "document"},
            {"texts": [], "model": "bge-m3", "mode": "document"},
            {"texts": ["x"], "model": "bge-m3"},
        ):
            status, body, _ = _http_json("POST", f"{base}/embed", payload)
            assert status == 400 and body["code"] == "invalid_request", (payload, status, body)

        # 路由纪律：未知路径 404（GET 与 POST 一致），/embed 不接受 GET
        assert _http_json("GET", f"{base}/nope")[0] == 404
        assert _http_json("POST", f"{base}/nope", {"texts": ["x"]})[0] == 404
        assert _http_json("GET", f"{base}/embed")[0] == 404
    finally:
        httpd.shutdown()
        httpd.server_close()

    # 未就绪运行时：healthz 仍 200 且给出**可读原因**（可观测优先），/embed 503
    broken_httpd, broken_base = _serve_ib_embed(_cfg(), UnavailableRuntime("权重目录不存在"))
    try:
        status, body, _ = _http_json("GET", f"{broken_base}/healthz")
        assert status == 200 and body["ok"] is False and "权重目录不存在" in body["detail"], body
        status, body, _ = _http_json(
            "POST", f"{broken_base}/embed", {"texts": ["x"], "model": "bge-m3", "mode": "document"}
        )
        assert status == 503 and body["code"] == "model_not_ready", (status, body)
    finally:
        broken_httpd.shutdown()
        broken_httpd.server_close()

    # **绝不返回部分向量**：运行时少给一个 → 整批 500（不是「给一半」）
    class _ShortRuntime:
        def load(self) -> int:
            return 1

        def is_loaded(self) -> bool:
            return True

        def embed(self, texts: Any, *, batch_size: int, max_tokens: int) -> Any:
            return RuntimeBatch(vectors=tuple((0.0,) * 1024 for _ in list(texts)[:1]))

        def descriptor(self) -> Any:
            from ib_embed.runtime import RuntimeDescriptor

            return RuntimeDescriptor("bge-m3", 1024, True, 64, "cpu")

    short_httpd, short_base = _serve_ib_embed(_cfg(), _ShortRuntime())
    try:
        status, body, _ = _http_json(
            "POST", f"{short_base}/embed", {"texts": ["a", "b"], "model": "bge-m3", "mode": "document"}
        )
        assert status == 500 and body["code"] == "internal_error", f"数量不符应整批失败：{status} {body}"
    finally:
        short_httpd.shutdown()
        short_httpd.server_close()

    # 维度参差 → 同样整批 500（不上抛「不可解释的向量」）
    class _RaggedRuntime(_ShortRuntime):
        def embed(self, texts: Any, *, batch_size: int, max_tokens: int) -> Any:
            return RuntimeBatch(vectors=((0.0,) * 1024, (0.0,) * 8))

    ragged_httpd, ragged_base = _serve_ib_embed(_cfg(), _RaggedRuntime())
    try:
        status, body, _ = _http_json(
            "POST", f"{ragged_base}/embed", {"texts": ["a", "b"], "model": "bge-m3", "mode": "document"}
        )
        assert status == 500 and body["code"] == "internal_error", (status, body)
    finally:
        ragged_httpd.shutdown()
        ragged_httpd.server_close()

    # 推理超预算 → 503/504 且**先报错后回收**（此处只验证推理异常被转成可重试码）
    class _FailingRuntime(_ShortRuntime):
        def embed(self, texts: Any, *, batch_size: int, max_tokens: int) -> Any:
            raise InferenceUnavailable("模拟权重卸载")

    failing_httpd, failing_base = _serve_ib_embed(_cfg(), _FailingRuntime())
    try:
        status, body, _ = _http_json(
            "POST", f"{failing_base}/embed", {"texts": ["a"], "model": "bge-m3", "mode": "document"}
        )
        assert status == 503 and body["code"] == "model_not_ready", (status, body)
    finally:
        failing_httpd.shutdown()
        failing_httpd.server_close()

    # 过载：容量 1 + 一个卡住的推理 → 第二个请求**快速失败**并给 retry_after_s
    import threading
    import time as _time

    class _GateRuntime:
        def __init__(self) -> None:
            self.entered = threading.Event()
            self.gate = threading.Event()

        def load(self) -> int:
            return 1

        def is_loaded(self) -> bool:
            return True

        def embed(self, texts: Any, *, batch_size: int, max_tokens: int) -> Any:
            self.entered.set()
            self.gate.wait(timeout=20)
            return RuntimeBatch(vectors=tuple((0.0,) * 1024 for _ in list(texts)))

        def descriptor(self) -> Any:
            from ib_embed.runtime import RuntimeDescriptor

            return RuntimeDescriptor("bge-m3", 1024, True, 64, "cpu")

    gate = _GateRuntime()
    gate_httpd, gate_base = _serve_ib_embed(_cfg(), gate)
    first: dict[str, Any] = {}

    def _first_request() -> None:
        first["result"] = _http_json(
            "POST", f"{gate_base}/embed", {"texts": ["a"], "model": "bge-m3", "mode": "document"}, timeout=30
        )

    try:
        worker = threading.Thread(target=_first_request, name="selfcheck-gate", daemon=True)
        worker.start()
        assert gate.entered.wait(timeout=10), "首个请求未进入推理（门未触发）"
        _time.sleep(0.05)  # 让首个请求完成准入登记
        status, body, headers = _http_json(
            "POST", f"{gate_base}/embed", {"texts": ["b"], "model": "bge-m3", "mode": "document"}, timeout=10
        )
        assert status == 503 and body["code"] == "overloaded", f"超限未快速失败：{status} {body}"
        assert headers.get("retry-after") == str(body["retry_after_s"]), headers
        gate.gate.set()
        worker.join(timeout=20)
        assert first["result"][0] == 200, f"被压住的请求最终应成功：{first['result']}"
    finally:
        gate.gate.set()
        gate_httpd.shutdown()
        gate_httpd.server_close()


@_case("page_image_binding_and_ledger：聚合/确定性/幂等/级联删除（InMemory + SQLite）")
def page_image_binding_and_ledger() -> None:
    """IFC-IB-277/278/279/281 的行为验证。

    刻意在**真实 SQLite** 上再跑一遍级联：`ON DELETE CASCADE` 是 SQL 层语义，
    内存替身的 `mark_deleted` 对齐写对了也证明不了 DDL 写对了。
    """
    import tempfile

    from ib.core import (
        ChunkImageRecord,
        PageImageBinding,
        PageImageRef,
        ParsedChunk,
        ParsedDocument,
        Scope,
    )
    from ib.lifecycle import bind_page_images, image_id_for
    from ib.ledger import InMemoryLedgerRepository
    from ib.ledger.sqlite_repo import SqliteLedgerRepository
    from ib.lifecycle import DocumentLifecycle  # noqa: F401 - 确认导出面未变

    parsed = ParsedDocument(
        chunks=[
            ParsedChunk(content="第 3 页正文", page_or_section="p3", source_kind="page_scan", locator="p3:s1"),
            ParsedChunk(
                content="第 3 页插图 OCR",
                page_or_section="p3",
                source_kind="image_ocr",
                locator="p3:i1",
                image_ref="p3:embedded",
            ),
            ParsedChunk(content="第 1 页正文", page_or_section="p1", source_kind="page_scan", locator="p1:s1"),
            ParsedChunk(
                content="第 1 页内嵌图",
                page_or_section="p1",
                source_kind="image_ocr",
                locator="p1:i1",
                image_ref="p1:embedded",
            ),
            ParsedChunk(
                content="第 1 页整页栅格",
                page_or_section="p1",
                source_kind="page_scan",
                locator="p1:raster",
                image_ref="p1:raster",
            ),
        ],
        page_count=3,
    )
    bindings = bind_page_images(parsed, doc_id="doc-1")
    assert [b.page_or_section for b in bindings] == ["p1", "p3"], f"分页未按 key 聚合：{bindings}"
    p1 = bindings[0]
    # p1 有两条关联：内嵌图 + 整页栅格（两者都是页面图，只是来源不同）
    assert len(p1.images) == 2, f"p1 的关联条数错误：{p1.images}"
    assert {img.source_kind for img in p1.images} == {"embedded_image", "page_scan"}, (
        f"图片种类映射错误：{p1.images}"
    )
    # 页内顺序 = `image_id` 升序（**确定性**排序，而非解析遍历顺序）
    ids = [img.image_id for img in p1.images]
    assert ids == sorted(ids), f"页内图片未按 image_id 升序：{ids}"
    assert len(set(ids)) == len(ids), f"同一页出现重复 image_id：{ids}"
    for binding in bindings:
        for image in binding.images:
            assert image.page_or_section == binding.page_or_section, "图被挂到了别的页"
    assert p1.doc_id == "doc-1" and p1.project_id == "" and p1.kb_id == "", "纯函数不得伪造归属"
    assert all(img.blob_ref is None for b in bindings for img in b.images), (
        "页面图字节在 R1/R2 未落盘，blob_ref 必须为 None（诚实登记，不伪造路径）"
    )
    # 确定性：同输入恒得同 image_id（幂等键的前提）
    again = bind_page_images(parsed, doc_id="doc-1")
    assert again == bindings, "同一解析产出两次绑定结果不一致（image_id 非确定性）"
    assert image_id_for("doc-1", "p1", "p1:i1") in ids
    # 文本块（无 image_ref）不得被当成图
    assert sum(len(b.images) for b in bindings) == 3, "非图片块被误当成页面图"

    def _records(scope: Scope, doc_id: str, count: int) -> list[Any]:
        out: list[Any] = []
        for index in range(count):
            out.append(
                ChunkImageRecord(
                    project_id=scope.project_id,
                    kb_id=scope.kb_ids[0],
                    doc_id=doc_id,
                    page_or_section=f"p{index}",
                    image_id=f"img-{index}",
                    source_kind="embedded_image",
                    locator=f"p{index}:i1",
                    blob_ref=None,
                    doc_name="scan.pdf",
                    created_at="2026-01-01T00:00:00Z",
                )
            )
        return out

    def _exercise(repo: Any, scope: Scope) -> None:
        repo.upsert_project(_project_record(scope.project_id))
        repo.upsert_kb(_kb_record(scope.project_id, scope.kb_ids[0]))
        doc = repo.create_document(scope, "scan.pdf", "pdf", 10, "sha-1", None)

        key = ChunkImageRecord.idempotent_key(scope.project_id, scope.kb_ids[0], doc.doc_id, "p1", "img-x")
        assert key == (scope.project_id, scope.kb_ids[0], doc.doc_id, "p1", "img-x"), key

        first = _records(scope, doc.doc_id, 3)
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, first)) == 3
        # 幂等：重跑覆盖同一行（不产生重复）——「重试/重建/重试后再重建」都靠这条
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, first)) == 3
        assert len(repo.list_chunk_images(scope, doc.doc_id)) == 3
        # 二次解析产出变少 → 陈旧关联行必须被清掉（否则用户会看到已不存在的图）
        assert int(repo.upsert_chunk_images(scope, doc.doc_id, _records(scope, doc.doc_id, 1))) == 1
        remaining = repo.list_chunk_images(scope, doc.doc_id)
        assert [r.image_id for r in remaining] == ["img-0"], remaining
        got = repo.get_chunk_image(scope, doc.doc_id, "img-0")
        assert got is not None and got.doc_name == "scan.pdf" and got.blob_ref is None
        assert repo.get_chunk_image(scope, doc.doc_id, "img-none") is None
        # 跨项目不可见（FM-3）：换成别的 project_id 一律查不到
        assert repo.get_chunk_image(Scope(project_id="other", kb_ids=scope.kb_ids), doc.doc_id, "img-0") is None
        assert repo.list_chunk_images(Scope(project_id="other", kb_ids=scope.kb_ids), doc.doc_id) == []

        # IFC-IB-281：删除文档 → 关联行**级联**消失（签名/语义零改动）
        report = repo.mark_deleted(scope, doc.doc_id)
        assert isinstance(report, bool) or report is None
        assert repo.get_document(scope, doc.doc_id) is None
        assert repo.list_chunk_images(scope, doc.doc_id) == [], "删除后仍残留页面图关联行"

    _exercise(InMemoryLedgerRepository(), Scope(project_id="p_mem", kb_ids=("kb1",)))

    with tempfile.TemporaryDirectory() as tmp:
        repo = SqliteLedgerRepository(os.path.join(tmp, "ledger.sqlite3"))
        try:
            _exercise(repo, Scope(project_id="p_sql", kb_ids=("kb1",)))
        finally:
            repo.close()


@_case("lifecycle_nine_step_order：向量写入 → 页面图落关联 → 块元数据 → 置位（IFC-IB-280）")
def lifecycle_nine_step_order() -> None:
    """九步管线的**写序**验证：`indexed` ⇒ 关联与块元数据均已就绪。

    写序是正确性的核心（ADR-07）：若先置位后写关联，就会出现「台账说 indexed 但图取不到」
    的窗口。此处用**记录型代理**观测真实调用顺序（不是读代码猜顺序）。
    """
    import io

    from ib.core import Scope
    from ib.lifecycle import DocumentLifecycle

    deps = _deps()
    events: list[str] = []

    class _RecordingLedger:
        def __init__(self, inner: Any) -> None:
            self._inner = inner

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def upsert_chunk_images(self, scope: Any, doc_id: str, records: Any) -> int:
            events.append("persist_page_images")
            return int(self._inner.upsert_chunk_images(scope, doc_id, records))

        def upsert_chunks(self, scope: Any, doc_id: str, records: Any) -> int:
            events.append("upsert_chunks")
            return int(self._inner.upsert_chunks(scope, doc_id, records))

        def mark_indexed(self, scope: Any, doc_id: str, version: str, count: int) -> None:
            events.append("mark_indexed")
            return self._inner.mark_indexed(scope, doc_id, version, count)

    class _RecordingVectors:
        def __init__(self, inner: Any) -> None:
            self._inner = inner

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def upsert(self, points: Any, wait: bool = True) -> Any:
            events.append("vector_upsert")
            return self._inner.upsert(points, wait=wait)

        def delete_by_doc(self, scope: Any, doc_id: str) -> int:
            events.append("vector_delete")
            return int(self._inner.delete_by_doc(scope, doc_id))

    lifecycle = DocumentLifecycle(
        ledger=_RecordingLedger(deps.ledger),
        blobs=deps.blobs,
        parsers=deps.parsers,
        chunker=deps.chunker,
        embedder=deps.embedder,
        vectors=_RecordingVectors(deps.vectors),
        resolver=deps.collections,
        ocr=deps.ocr,
        renderer=deps.renderer,
        chunking_spec=deps.cfg.chunking_spec,
        project_provider=lambda pid: deps.projects.get(pid) or _project_record(pid),
    )

    from ib.context import make_request_context

    ctx = make_request_context(project_id="p_alpha", actor_id="u1", session_id="s1")
    body = "九步管线自检内容。".encode("utf-8")
    validated = lifecycle.validate_upload("nine.txt", len(body), body[:64])
    record = lifecycle.submit_upload(ctx, validated, "kb_a", data=io.BytesIO(body))
    report = lifecycle.process_pending("selfcheck-worker", 5)
    assert report.processed >= 1 and report.failed == 0, report
    indexed = deps.ledger.get_document(Scope(project_id="p_alpha", kb_ids=("kb_a",)), record.doc_id)
    assert indexed is not None and indexed.status == "indexed", indexed

    assert events, "未观测到任何写操作（记录型代理未生效）"
    order = [name for name in events]
    assert "vector_upsert" in order and "persist_page_images" in order and "mark_indexed" in order, order
    assert order.index("vector_upsert") < order.index("persist_page_images"), (
        f"页面图关联必须写在向量之后：{order}"
    )
    assert order.index("persist_page_images") < order.index("upsert_chunks"), f"块元数据顺序错：{order}"
    assert order.index("upsert_chunks") < order.index("mark_indexed"), f"置位必须最后：{order}"
    # 失败粒度未被两个新步骤细化：整批仍只有 succeeded/failed/skipped 三档
    assert set(report.__dataclass_fields__) == {"processed", "succeeded", "failed", "skipped"}


@_case("related_images_events：无图不发 / 载荷只有路径 / 模板与 URLconf 一致")
def related_images_events() -> None:
    """IFC-IB-282：事件只在有图时出现，载荷只含短字段（**绝不内联 base64**）。"""
    import json

    from ib.core import RelatedImageItem, RelatedImagesPayload
    from ib.streaming import (
        IMAGE_ENDPOINT_TEMPLATE,
        related_image_url,
        related_images_event,
        related_images_json,
        related_images_of,
    )

    # 无图 → **不发事件**（把纪律放在构造函数里，调用点忘判空也不会发出空事件）
    assert related_images_event(None) is None
    assert related_images_event(RelatedImagesPayload(images=())) is None

    items = [
        RelatedImageItem(
            image_id="img-a",
            doc_id="d1",
            doc_name="图纸.pdf",
            page_or_section="p1",
            url_path=related_image_url("d1", "img-a"),
        ),
        RelatedImageItem(
            image_id="img-b",
            doc_id="d1",
            doc_name="图纸.pdf",
            page_or_section="p2",
            url_path=related_image_url("d1", "img-b"),
        ),
    ]
    payload = related_images_of(items)
    event = related_images_event(payload)
    assert event is not None and str(event.kind) == "related_images", event
    decoded = json.loads(related_images_json(payload))
    assert [img["image_id"] for img in decoded["images"]] == ["img-a", "img-b"], "载荷未保序"
    assert set(decoded["images"][0]) == {
        "image_id",
        "doc_id",
        "doc_name",
        "page_or_section",
        "url_path",
    }, decoded["images"][0]
    assert "base64" not in related_images_json(payload).lower()
    assert related_image_url("d1", "img-a") == "/api/files/d1/images/img-a"
    assert IMAGE_ENDPOINT_TEMPLATE == "/api/files/{doc_id}/images/{image_id}"

    # 模板与 URLconf **必须**指向同一路径：前端拿到 url_path 却 404，是最难查的一类漂移
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")
    os.environ["IB_CONFIG_SOURCE"] = "dict"
    from ibweb.composition import build_application, build_deps

    deps = build_deps(OFFLINE_RAW)
    import django

    django.setup()
    build_application(deps)

    from django.urls import reverse

    assert reverse("ib-file-image", kwargs={"doc_id": "d1", "image_id": "img-a"}) == related_image_url(
        "d1", "img-a"
    ), "URLconf 与 IMAGE_ENDPOINT_TEMPLATE 不一致（前端会 404 而服务端日志一片正常）"

    # /healthz/deps 的字段集合**不变**（IFC-IB-283 明文要求）
    from django.test import Client

    auth = {"HTTP_AUTHORIZATION": f"Bearer {os.environ['IB_OFFLINE_TOKEN']}"}
    payload_keys = set(Client().get("/healthz/deps", **auth).json())
    assert payload_keys == {"qdrant", "embed", "llm", "egress"}, payload_keys


@_case("file_image_endpoint：200 / 404（含跨项目）/ 403 / 503 / ?token= 400（IFC-IB-283）")
def file_image_endpoint() -> None:
    """图片端点的四条边界 + 鉴权纪律。**不连任何外部服务**（内存台账 + 内存 BlobStore）。"""
    import io

    from ib.core import ChunkImageRecord, DependencyUnavailableError, Scope

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")
    os.environ["IB_CONFIG_SOURCE"] = "dict"
    from ibweb.composition import build_application, build_deps

    deps = build_deps(OFFLINE_RAW)
    import django

    django.setup()
    build_application(deps)

    png = b"\x89PNG\r\n\x1a\n" + b"selfcheck-page-image"
    scope = Scope(project_id="p_alpha", kb_ids=("kb_a",))
    doc = deps.ledger.create_document(scope, "scan.pdf", "pdf", len(png), "sha-img", None)
    ref = deps.blobs.put(scope, doc.doc_id, io.BytesIO(png), "png")
    deps.ledger.upsert_chunk_images(
        scope,
        doc.doc_id,
        [
            ChunkImageRecord(
                project_id=scope.project_id,
                kb_id="kb_a",
                doc_id=doc.doc_id,
                page_or_section="p1",
                image_id="img-1",
                source_kind="embedded_image",
                locator="p1:i1",
                blob_ref=ref.rel_path,
                doc_name="scan.pdf",
                created_at="2026-01-01T00:00:00Z",
            )
        ],
    )
    # 另一项目里的同名文档（用于验证「跨项目 → 404 而非 403」，反存在性探测）
    other_scope = Scope(project_id="p_beta", kb_ids=("kb_b",))
    other_doc = deps.ledger.create_document(other_scope, "scan.pdf", "pdf", len(png), "sha-img2", None)
    other_ref = deps.blobs.put(other_scope, other_doc.doc_id, io.BytesIO(png), "png")
    deps.ledger.upsert_chunk_images(
        other_scope,
        other_doc.doc_id,
        [
            ChunkImageRecord(
                project_id="p_beta",
                kb_id="kb_b",
                doc_id=other_doc.doc_id,
                page_or_section="p1",
                image_id="img-1",
                source_kind="embedded_image",
                locator="p1:i1",
                blob_ref=other_ref.rel_path,
                doc_name="scan.pdf",
                created_at="2026-01-01T00:00:00Z",
            )
        ],
    )

    from django.test import Client

    auth = {"HTTP_AUTHORIZATION": f"Bearer {os.environ['IB_OFFLINE_TOKEN']}"}
    url = f"/api/files/{doc.doc_id}/images/img-1"

    # 200：字节 + image/* + 可缓存 + nosniff
    client = Client()
    r = client.get(url, **auth)
    assert r.status_code == 200, getattr(r, "content", b"")
    assert r["Content-Type"] == "image/png", r["Content-Type"]
    assert r["Cache-Control"].startswith("private"), r["Cache-Control"]
    assert r["X-Content-Type-Options"] == "nosniff"
    assert r.content == png, "返回的字节与存储不一致"

    # 404：图片不存在 / 文档不存在 / 跨项目（**与「不属于你」同一状态码**）
    assert client.get(f"/api/files/{doc.doc_id}/images/img-none", **auth).status_code == 404
    assert client.get("/api/files/no-such-doc/images/img-1", **auth).status_code == 404
    assert client.get(f"/api/files/{other_doc.doc_id}/images/img-1", **auth).status_code == 404, (
        "跨项目图片必须 404（403 会变成存在性探测预言机）"
    )

    # blob_ref 为空（R2 页面图的真实形态：解析器 OCR 完即弃）→ 404，不给占位图。
    # 注意 `upsert_chunk_images` 是**先删后写（同 doc_id）**，故此处把 img-1 一并重放，
    # 否则后面的 403/503 用例会因行已被清掉而退化成 404（测不到目标分支）。
    deps.ledger.upsert_chunk_images(
        scope,
        doc.doc_id,
        [
            ChunkImageRecord(
                project_id="p_alpha",
                kb_id="kb_a",
                doc_id=doc.doc_id,
                page_or_section="p1",
                image_id="img-1",
                source_kind="embedded_image",
                locator="p1:i1",
                blob_ref=ref.rel_path,
                doc_name="scan.pdf",
                created_at="2026-01-01T00:00:00Z",
            ),
            ChunkImageRecord(
                project_id="p_alpha",
                kb_id="kb_a",
                doc_id=doc.doc_id,
                page_or_section="p1",
                image_id="img-nobytes",
                source_kind="page_scan",
                locator="p1:raster",
                blob_ref=None,
                doc_name="scan.pdf",
                created_at="2026-01-01T00:00:00Z",
            ),
        ],
    )
    assert client.get(f"/api/files/{doc.doc_id}/images/img-nobytes", **auth).status_code == 404
    assert client.get(url, **auth).status_code == 200, "重放后 img-1 应仍可取出（幂等写入被打断）"

    # ?token= 进查询串 → 中间件 400（图片端点不例外）
    assert client.get(f"{url}?token=whatever", **auth).status_code == 400

    # 405：非 GET
    assert client.post(url, **auth).status_code == 405

    # 403：主体无问答权限（换一个**全新的 Client**，否则中间件缓存了上一次的策略）
    original_policy = deps.policy

    class _DenyQuery:
        def can_manage(self, authz: Any) -> bool:
            return True

        def can_query(self, authz: Any) -> bool:
            return False

    deps.policy = _DenyQuery()
    try:
        assert Client().get(url, **auth).status_code == 403, "无问答权限应 403"
    finally:
        deps.policy = original_policy

    # 503：BlobStore 不可用 → fail-closed（**不返回占位图**）
    original_blobs = deps.blobs

    class _BrokenBlobs:
        def get(self, blob_ref: Any) -> bytes:
            raise DependencyUnavailableError("BlobStore 不可用（自检注入）", dependency="blob")

        def put(self, *args: Any, **kwargs: Any) -> Any:
            raise DependencyUnavailableError("BlobStore 不可用（自检注入）", dependency="blob")

        def delete(self, *args: Any, **kwargs: Any) -> int:
            raise DependencyUnavailableError("BlobStore 不可用（自检注入）", dependency="blob")

    deps.blobs = _BrokenBlobs()
    try:
        r = Client().get(url, **auth)
        assert r.status_code == 503, f"BlobStore 不可用应 503，实际 {r.status_code}"
        assert b"\x89PNG" not in r.content, "503 不得返回任何图片字节（占位图也是伪造）"
    finally:
        deps.blobs = original_blobs


@_case("frontend_image_discipline：走封装层取图 / 无裸 axios / 无 v-html / 不改写正文")
def frontend_image_discipline() -> None:
    """IFC-IB-284 + IC-IB-01 的静态纪律检查（前端为 TS，Python 侧只能做源码级断言）。

    断言前**剥掉注释**：本项目的文件头注释是契约的载体，其中必然出现
    `Authorization` / `?token=` 这类词（正是为了说明「为什么不用它」）。
    直接按子串判会把「解释了禁令的注释」误判成「违反了禁令的代码」。
    """
    import pathlib
    import re

    def _strip_comments(text: str) -> str:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)  # 块注释（含 JSDoc）
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)  # 模板注释
        text = re.sub(r"^[ \t]*//.*$", "", text, flags=re.MULTILINE)  # 行注释
        return text

    root = pathlib.Path(_SRC) / "frontend" / "src"
    chat_source = (root / "views" / "ChatPage.vue").read_text(encoding="utf-8")
    client_ts = (root / "api" / "client.ts").read_text(encoding="utf-8")
    chat = _strip_comments(chat_source)
    page = chat

    assert "fetchFileImage" in client_ts, "API 客户端缺少 IFC-IB-283 取图方法"
    assert "/images/" in client_ts, "API 客户端未拼出图片端点路径"
    assert "fetchFileImage" in page, "ChatPage 未经 API 客户端取图（IC-IB-01）"

    # 裸 axios / 自行拼令牌 / v-html / 查询串传令牌：出现在**代码**里即为违规
    assert "axios" not in page, "页面里出现了 axios（IC-IB-01 要求统一走封装层）"
    assert "Authorization" not in page, "页面里自行拼了令牌（必须只由 client.ts 拼）"
    assert "v-html" not in page, "页面使用了 v-html（XSS 通道）"
    assert "token=" not in page, "页面把令牌放进了查询串"
    # 页面不直接取字节（必须只经 client）
    assert "fetch(" not in page, "页面里出现了裸 fetch（应经 ApiClient.fetchFileImage）"

    # related_images 必须落在正文之外：正文只用插值，事件与正文分开处理
    assert "turn.answer +=" in page, "content 事件的渲染方式被改写（正文必须仍为纯文本插值）"
    assert "related_images" in page and "images: []" in page
    # 渲染位置：缩略图行出现在正文之后（源码顺序即模板顺序）
    assert page.index('class="answer"') < page.index('class="thumbs"'), "缩略图行必须渲染在正文之后"
    # 图绝不被塞进正文变量
    assert "turn.answer +=" in page and "answer: ''" in page
    assert not re.search(r"answer\s*\+=.*(img|image|url_path)", page), "缩略图被塞进了正文文本"

    # 取图失败静默隐藏：catch 分支不得产出任何降级/错误文案（降级文案只对 degraded 负责）
    assert "turn.degraded" in page
    assert not re.search(r"(image|图片).{0,16}(降级|提示|文案)", page), (
        "图片路径出现降级文案（IFC-IB-284 要求静默隐藏）"
    )
    # blob URL 必须被释放（不释放则整页图片常驻内存）
    assert "revokeObjectURL" in page, "未释放 blob URL（内存泄漏）"
    # 无裸 axios（全前端目录，注释已剥）
    for path in sorted(root.rglob("*.vue")) + sorted(root.rglob("*.ts")):
        text = _strip_comments(path.read_text(encoding="utf-8"))
        assert "from 'axios'" not in text and 'from "axios"' not in text, f"{path.name} 裸用 axios"


@_case("deploy_templates_have_no_secrets：部署模板只含占位符，无真实凭据")
def deploy_templates_have_no_secrets() -> None:
    """扫描 `deploy/` 下的模板文件，确认没有真实凭据（正则命中即失败）。

    这是「凭据只走环境变量」纪律的自动化兜底 —— 靠人肉 review `.env.example` 迟早会漏。
    """
    import pathlib
    import re

    patterns = [
        re.compile(r"sk-[A-Za-z0-9]{16,}"),
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        re.compile(r"ey[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."),  # JWT
    ]
    deploy_dir = pathlib.Path(_SRC) / "deploy"
    offenders: list[str] = []
    for path in sorted(deploy_dir.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            if pat.search(text):
                offenders.append(f"{path.relative_to(_SRC)} 命中 {pat.pattern}")
    if offenders:
        raise AssertionError("模板中出现疑似真实凭据：" + "; ".join(offenders))


def main() -> int:
    print("=" * 72)
    print("intelligentbase 离线自检（GROUP_C 自我验证；正式测试套件属 GROUP_D）")
    print("=" * 72)

    cases = [
        core_framework_free,
        no_forbidden_web_carrier,
        no_pymupdf,
        port_conformance,
        authz_injection_required,
        config_error_reports_key_only,
        magic_sniff_rejects_renamed_file,
        ledger_state_machine_and_lease,
        isolation_scope_required,
        retrieval_happy_path,
        retrieval_fail_open,
        sse_frame_and_done_terminator,
        orchestration_events_order,
        http_contract_offline,
        deploy_templates_have_no_secrets,
        # ---- R2 增量（L-03：ib-embed 服务端；M-02：页面图关联 / 读路径） ----
        ib_embed_config_keys,
        ib_embed_isolation,
        embed_three_form_conformance,
        ib_embed_wire_protocol,
        page_image_binding_and_ledger,
        lifecycle_nine_step_order,
        related_images_events,
        file_image_endpoint,
        frontend_image_discipline,
    ]
    for case in cases:
        case()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    total = len(_RESULTS)
    print("-" * 72)
    print(f"自检结果：{passed}/{total} 通过")
    if passed != total:
        print("失败项：")
        for name, ok, detail in _RESULTS:
            if not ok:
                print(f"  - {name}: {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
