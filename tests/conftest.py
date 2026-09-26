"""GROUP_D 正式测试套件的公共夹具（intelligentbase）。

职责边界：
  * 本目录是 **GROUP_D 的正式测试套件**（与 `src/scripts/selfcheck.py` 的开发自检**不同**：
    自检由 software-developer 编写、证明「实现能装配」；本套件负责验收标准级覆盖与门控度量）。
  * **离线约束**：一律 SQLite/内存/替身；不连接任何生产数据库、真实 Qdrant、DeepSeek API、
    ib-embed 真实服务或任何外部网络端点（附录 D「无外部依赖」）。ib-embed 线协议用例只在
    **回环随机端口**起真 HTTP（本机 socket，无外部依赖）。
  * **凭据纪律**：测试代码内不出现任何真实 token/key/密码，一切凭据走环境变量占位符。

环境（开发机 Python 3.14.6，见 R1 偏差 D-03；tech_stack 约束为 >=3.11,<3.14）：
  运行前在 `src/` 同级执行即可，无需额外设置 —— 本文件在导入期设定离线环境。
"""

from __future__ import annotations

import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# --- 必须在导入任何 ib / ibweb / ib_embed 之前设定（离线装配的唯一环境前提） ---
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "groupd-offline-token")
os.environ.setdefault("IB_LOG_LEVEL", "ERROR")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

import pytest  # noqa: E402

#: 离线自测装配（键名与 selfcheck 一致；值均为本机临时路径/替身标识，无凭据）。
OFFLINE_RAW: dict = {
    "config_source": "dict",
    "offline_mode": True,
    "ledger_backend": "memory",
    "blob": {"enabled": True, "root": os.path.join(str(_SRC), ".groupd_blobs")},
    "retrieval": {"top_k": 3, "score_threshold": 0.0, "candidate_multiplier": 2},
    "vectorstore": {"backend": "memory"},
    "embedding": {"backend": "fake"},
    "llm": {"backend": "fake"},
    "projects": {
        "p_alpha": {
            "name": "测试项目 A",
            "active_collection_version": "1",
            "embedding_model_id": "bge-m3",
            "dim": 1024,
            "kb_ids": ["kb_a"],
        },
        "p_beta": {
            "name": "测试项目 B",
            "active_collection_version": "1",
            "embedding_model_id": "bge-m3",
            "dim": 1024,
            "kb_ids": ["kb_b"],
        },
    },
}


def offline_raw() -> dict:
    """每次返回一份**深拷贝**，避免用例之间共享可变配置字典。"""
    import copy

    return copy.deepcopy(OFFLINE_RAW)


@pytest.fixture()
def raw() -> dict:
    return offline_raw()


@pytest.fixture()
def deps(raw):
    """函数级 fresh 装配（`force=True`）：每个用例一份干净的 InMemory 台账/向量库。"""
    from ibweb.composition import build_deps

    return build_deps(raw, force=True)


@pytest.fixture(scope="session")
def django_ready():
    """一次性 `django.setup()`（必须在 `build_deps` 之后，`apps.ready()` 才不报缺字典）。"""
    from ibweb.composition import build_application, build_deps

    d = build_deps(offline_raw(), force=True)
    import django

    django.setup()
    build_application(d)
    return True


def request_ctx(project_id: str, actor_id: str = "tester", session_id: str = "s1"):
    """构造离线 `RequestContext`（供 lifecycle 上传路径使用）。"""
    from ib.context import make_request_context

    return make_request_context(
        project_id=project_id, actor_id=actor_id, session_id=session_id, roles=("manager",)
    )


def ingest_text(deps, project_id: str, kb_id: str, filename: str, content: str):
    """把一段文本经**真实上传+处理管线**送进库（返回 DocumentRecord）。

    走 `validate_upload` → `submit_upload` → `process_pending`，即生产同一条路径；
    不绕过校验、不手工造向量（否则集成测试就失去了「接缝真实」的意义）。
    """
    import io

    ctx = request_ctx(project_id)
    head = content.encode("utf-8")[:4096]
    validated = deps.lifecycle.validate_upload(filename, len(content.encode("utf-8")), head)
    record = deps.lifecycle.submit_upload(
        ctx, validated, kb_id, data=io.BytesIO(content.encode("utf-8"))
    )
    deps.lifecycle.process_pending("groupd-worker", 10)
    return record


@pytest.fixture()
def http_app(django_ready, raw):
    """HTTP 层用例夹具：先确保 Django 已 setup，再 fresh 装配并设为当前全局 deps。

    返回 `(deps, Client工厂)`：`Client()` 每次都新建 —— 中间件按请求解析策略，
    复用一个 Client 会缓存上一次的策略（见 selfcheck 注释）。
    """
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    d = build_deps(raw, force=True)
    build_application(d)
    return d, Client
