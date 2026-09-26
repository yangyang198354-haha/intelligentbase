"""集成测试层 7/N —— 补齐若干验收标准的具体条款（校验边界 / 错误码 / 核心零业务耦合）。

覆盖：AC-IB-01-03（大小上限）、AC-IB-04-04（不支持的格式）、AC-IB-02-03（仅失败可重试）、
AC-IB-03-04（删除不存在 → 404）、AC-IB-11-06（编排核心不依赖业务域模块）。
全部离线；上传校验走真实 `validate_upload`，HTTP 走 Django test Client。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", "src"))


# --------------------------------------------------------------------------- #
# AC-IB-01-03 / AC-IB-04-04：上传前校验边界（服务端硬闸）
# --------------------------------------------------------------------------- #


def test_TC_INT_055_oversize_upload_rejected_before_ledger(deps):
    """[TC-INT-055] 超限文件 → ValidationError（可读、含上限）且不落台账（AC-IB-01-03）。"""
    from ib.core import Scope, ValidationError

    with __import__("pytest").raises(ValidationError) as exc:
        deps.lifecycle.validate_upload("big.txt", 60 * 1024 * 1024, b"x" * 16)
    assert "上限" in str(exc.value)
    _, total = deps.ledger.list_documents(Scope("p_alpha", ("kb_a",)), page=1, page_size=50, status=None)
    assert total == 0


def test_TC_INT_056_unsupported_format_rejected_with_readable_reason(deps):
    """[TC-INT-056] 白名单外格式（.xlsx）→ ValidationError，原因指明格式与支持清单（AC-IB-04-04）。"""
    from ib.core import Scope, ValidationError

    with __import__("pytest").raises(ValidationError) as exc:
        deps.lifecycle.validate_upload("book.xlsx", 100, b"PK\x03\x04" + b"0" * 12)
    msg = str(exc.value)
    assert ".xlsx" in msg and ("支持" in msg or "格式" in msg)
    _, total = deps.ledger.list_documents(Scope("p_alpha", ("kb_a",)), page=1, page_size=50, status=None)
    assert total == 0


def test_TC_INT_057_retry_non_failed_conflicts_with_current_state(deps):
    """[TC-INT-057] 非 failed 文档重试 → ConflictError，回显当前状态且不改动数据（AC-IB-02-03）。"""
    from ib.core import ConflictError, Scope
    from conftest import ingest_text

    record = ingest_text(deps, "p_alpha", "kb_a", "ok.txt", "已成功入库内容。")
    scope = Scope("p_alpha", ("kb_a",))
    assert deps.ledger.get_document(scope, record.doc_id).status == "indexed"
    try:
        deps.lifecycle.retry_document(scope, record.doc_id)
        raise AssertionError("非 failed 文档竟可重试")
    except ConflictError as exc:
        assert "failed" in str(exc) and "indexed" in str(exc), "错误信息未回显当前状态"
    assert deps.ledger.get_document(scope, record.doc_id).status == "indexed", "被拒的重试改动了数据"


def test_TC_INT_058_delete_nonexistent_returns_404(http_app):
    """[TC-INT-058] 删除不存在的文档 id → HTTP 404（AC-IB-03-04）。"""
    _, Client = http_app
    r = Client().delete("/api/files/no-such-doc-id", **AUTH)
    assert r.status_code == 404, r.content
    assert json.loads(r.content)["error"]["code"] == "not_found"


def test_TC_INT_058b_retry_non_failed_returns_409(http_app):
    """[TC-INT-058b] 非 failed 文档经 HTTP 重试 → 409（views 的 ConflictError→409 映射，AC-IB-02-03）。"""
    from conftest import ingest_text

    deps, Client = http_app
    record = ingest_text(deps, "p_alpha", "kb_a", "http-ok.txt", "已成功入库内容。")
    r = Client().post(f"/api/files/{record.doc_id}/retry", **AUTH)
    assert r.status_code == 409, r.content
    assert json.loads(r.content)["error"]["code"] == "conflict"


# --------------------------------------------------------------------------- #
# AC-IB-06-02：知识库级软隔离（同一项目内，kb 作用域过滤）
# --------------------------------------------------------------------------- #


def test_TC_INT_060_kb_level_soft_isolation():
    """[TC-INT-060] 同一项目内按 kb 作用域检索互不可见（AC-IB-06-02，软隔离 filter）。"""
    from conftest import ingest_text, offline_raw
    from ib.core import Scope
    from ibweb.composition import build_deps

    raw = offline_raw()
    raw["projects"]["p_alpha"]["kb_ids"] = ["kb_a", "kb_c"]
    deps = build_deps(raw, force=True)
    da = ingest_text(deps, "p_alpha", "kb_a", "a.txt", "知识库A独有内容 OMEGA-1。")
    dc = ingest_text(deps, "p_alpha", "kb_c", "c.txt", "知识库C独有内容 SIGMA-2。")

    a = deps.retrieval.search("OMEGA-1", scope=Scope("p_alpha", ("kb_a",)))
    c = deps.retrieval.search("OMEGA-1", scope=Scope("p_alpha", ("kb_c",)))
    assert any(h.doc_id == da.doc_id for h in a.hits)
    assert not any(h.doc_id == da.doc_id for h in c.hits), "kb_c 作用域看到了 kb_a 的文档"
    both = deps.retrieval.search("独有内容", scope=Scope("p_alpha", ("kb_a", "kb_c")))
    assert {h.doc_id for h in both.hits} >= {da.doc_id, dc.doc_id}


# --------------------------------------------------------------------------- #
# AC-IB-11-06：编排核心不依赖任何业务域模块
# --------------------------------------------------------------------------- #


def test_TC_INT_059_orchestration_core_has_no_business_domain_coupling():
    """[TC-INT-059] 干净解释器导入 `ib.orchestration` 不得带入 Django/DRF 等业务载体（AC-IB-11-06）。

    编排骨架应只依赖基座自身端口/类型；业务上下文由调用方构造后透传。
    """
    code = (
        "import ib.orchestration, sys;"
        "forbidden=[m for m in sys.modules if m in {'django','rest_framework','freearkweb'} "
        "or m.startswith(('django.','rest_framework.'))];"
        "print(' '.join(sorted(forbidden)) if forbidden else 'CLEAN')"
    )
    env = dict(os.environ, PYTHONPATH=_SRC, PYTHONUTF8="1")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code], capture_output=True, text=True, env=env, timeout=60
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "CLEAN", f"编排核心引入了业务载体依赖：{proc.stdout.strip()}"
