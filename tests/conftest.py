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


# --------------------------------------------------------------------------- #
# R13（账户 / 会话）HTTP 夹具
# --------------------------------------------------------------------------- #

#: R13 测试用**占位**口令（**非生产凭据**）：生产初始口令**只**经 `IB_DEFAULT_ADMIN_PASSWORD`
#: 注入，本常量仅用于离线测试装配，性质与 conftest 既有的 `groupd-offline-token` 相同 ——
#: 是「测试替身值」而非任何真实密钥。测试代码与报告中**不出现**任何真实口令 / 令牌。
R13_ADMIN_PASSWORD = "GroupD-Test-Admin-1!"
R13_OPS_PASSWORD = "GroupD-Test-Ops-1!"


def _build_accounts_app(monkeypatch, offline_raw_dict: dict, extra_env: dict) -> tuple:
    """以 `ibweb.accounts.policy` 为鉴权策略装配一份 deps（R13 账户体系「生产形态」）。

    与 `http_app` 的唯一差别：显式注入 `IB_AUTHZ_POLICY_MODULE`（生产必须项），使
    `build_authz` 走 `SessionTokenResolver` + `AccountsPolicy`，而非离线 `EnvTokenResolver`。
    这保证账户 / 会话端点被**真实**账户体系承载（令牌来自 `POST /api/auth/login`）。

    环境变量经 `monkeypatch` 设定并**在整个用例期间保持**（`monkeypatch` 于 teardown 还原）：
    会话 TTL / 续期窗口由视图在**请求期**经 `load_account_settings()` 读取，若只在装配期
    设定、装配后即还原，请求期将回落到默认值（测试会随之失真）。
    """
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    for key in ("IB_LOGIN_MAX_FAILURES", "IB_LOGIN_LOCK_SECONDS"):
        if key not in extra_env:
            monkeypatch.delenv(key, raising=False)
    for key, value in extra_env.items():
        monkeypatch.setenv(key, value)

    d = build_deps(offline_raw_dict, force=True)
    build_application(d)
    return d, Client


@pytest.fixture()
def accounts_app(django_ready, raw, monkeypatch):
    """R13 账户体系 HTTP 夹具（**无**登录失败锁定）：返回 `(deps, Client工厂)`。

    装配后默认管理员 `admin` 已幂等播种，初始口令取自测试占位值（仅经
    `IB_DEFAULT_ADMIN_PASSWORD` 注入）—— 生产口径同此，口令值不入库明文 / 不入日志。
    """
    env = {
        "IB_ACCOUNT_BACKEND": "memory",
        "IB_AUTHZ_POLICY_MODULE": "ibweb.accounts.policy",
        "IB_DEFAULT_ADMIN_PASSWORD": R13_ADMIN_PASSWORD,
        "IB_SESSION_TTL_SECONDS": "3600",
        "IB_SESSION_RENEW_WINDOW_SECONDS": "600",
    }
    return _build_accounts_app(monkeypatch, raw, env)


@pytest.fixture()
def locked_accounts_app(django_ready, raw, monkeypatch):
    """R13 账户体系 HTTP 夹具（**启用**账户级锁定阈值=3）：用于 AC-IB-29-01 锁定回归。"""
    env = {
        "IB_ACCOUNT_BACKEND": "memory",
        "IB_AUTHZ_POLICY_MODULE": "ibweb.accounts.policy",
        "IB_DEFAULT_ADMIN_PASSWORD": R13_ADMIN_PASSWORD,
        "IB_SESSION_TTL_SECONDS": "3600",
        "IB_SESSION_RENEW_WINDOW_SECONDS": "600",
        "IB_LOGIN_MAX_FAILURES": "3",
        "IB_LOGIN_LOCK_SECONDS": "900",
    }
    return _build_accounts_app(monkeypatch, raw, env)


def login(client, username: str, password: str):
    """`POST /api/auth/login`（JSON）——账户体系夹具下的登录助手（返回原始响应）。"""
    import json as _json

    return client.post(
        "/api/auth/login",
        data=_json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )


def bearer(token: str) -> dict:
    """构造 `Authorization: Bearer` 头字典（**只**经头传递，绝不进查询串）。"""
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def change_password(client, token: str, old_password: str, new_password: str):
    """`POST /api/auth/change-password`（JSON）。"""
    import json as _json

    return client.post(
        "/api/auth/change-password",
        data=_json.dumps({"old_password": old_password, "new_password": new_password}),
        content_type="application/json",
        **bearer(token),
    )
