"""集成测试层 —— R13 部署面增量（HTTPS 落点 / 键登记 / 凭据纪律 / 迁移单源）。

覆盖 US-IB-28（登录与账号通道经 HTTPS 部署）与 REQ-NFR-IB-15 / IB-16 / IB-17 的
**静态可验证面**：nginx TLS 模板、环境键登记、迁移 `003_accounts.sql` 与运行时 schema 的
列级单源一致、部署检查清单 [B15]~[B20]。

溯源：每个用例在 docstring 标注 **US-IB-NN / AC-IB-NN-NN**。
约束：纯文本 / SQLite 读取，不触网、不起服务、不改任何 `src/**`。
"""

from __future__ import annotations

import pathlib
import sqlite3

from ib.config import IB_ENV_KEYS, IB_RUNTIME_ENV_KEYS

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_NGINX = _ROOT / "src" / "deploy" / "nginx" / "intelligentbase.conf.example"
_ENV_EXAMPLE = _ROOT / "src" / "deploy" / "env.example"
_CHECKLISTS = _ROOT / "src" / "deploy" / "checklists.txt"
_MIGRATION_003 = _ROOT / "src" / "deploy" / "migrations" / "003_accounts.sql"

#: R13（IFC-IB-312）应在唯一真源 `ib.config` 登记的 9 个键名。
_R13_KEYS = (
    "IB_ACCOUNT_BACKEND",
    "IB_SESSION_TTL_SECONDS",
    "IB_SESSION_RENEW_WINDOW_SECONDS",
    "IB_DEFAULT_ADMIN_USERNAME",
    "IB_DEFAULT_ADMIN_PASSWORD",
    "IB_PASSWORD_MIN_LENGTH",
    "IB_LOGIN_MAX_FAILURES",
    "IB_LOGIN_LOCK_SECONDS",
    "IB_AUTHZ_POLICY_MODULE",
)


# --------------------------------------------------------------------------- #
# TC-INT-120 nginx TLS 模板（HTTPS 落点；明文只在回环）
# --------------------------------------------------------------------------- #


def test_TC_INT_120_nginx_template_terminates_tls_and_keeps_plaintext_loopback():
    """US-IB-28 / AC-IB-28-01、AC-IB-28-02；REQ-NFR-IB-16。

    ① 服务入口为 `listen 443 ssl` 且声明证书（AC-IB-28-01）；
    ② 明文 HTTP 入口**只做跳转**（301 → https）或拒绝，不在其上传凭据（AC-IB-28-02）；
    ③ 业务进程绑 **回环** `127.0.0.1`（明文不对外）；
    ④ `Authorization` 原样透传（认证不走 Cookie）；
    ⑤ 模板**零证书 / 私钥材料**（仅占位符）。
    """
    text = _NGINX.read_text(encoding="utf-8")
    assert "listen 443 ssl" in text, "缺少 HTTPS 服务入口"
    assert "ssl_certificate " in text and "ssl_certificate_key " in text
    assert "<REPLACE_ME_path_to_server_crt>" in text  # 路径为占位符，非真实证书
    assert "server 127.0.0.1:18080" in text, "业务端口必须只绑回环（明文不对外）"
    assert "proxy_set_header Authorization $http_authorization" in text, "Authorization 必须透传"
    assert "proxy_buffering off" in text, "SSE 硬条件缺失"

    # HTTP 块：跳转而非承载明文登录
    assert "return 301 https://$host$request_uri" in text or "return 444" in text
    assert "listen 80" in text

    # 零证书 / 私钥材料（防「模板里顺手贴了真证书」）
    for marker in ("BEGIN CERTIFICATE", "BEGIN PRIVATE KEY", "BEGIN RSA PRIVATE KEY"):
        assert marker not in text, f"模板含真实证书材料：{marker}"


# --------------------------------------------------------------------------- #
# TC-INT-121 键登记 / 凭据纪律 / 迁移单源一致
# --------------------------------------------------------------------------- #


def test_TC_INT_121_runtime_keys_registered_and_credentials_disciplined():
    """US-IB-28 / REQ-NFR-IB-15（C-IB-09）；US-IB-27 / AC-IB-27-02。

    * R13 的 9 个键名在**唯一真源** `ib.config.IB_RUNTIME_ENV_KEYS` 登记（可集中审计），
      且**不得**混入声明「不得新增 / 改名」的 `IB_ENV_KEYS`；
    * `env.example` 只登记**键名 + 占位符**（`<REPLACE_ME…>`），不含任何真实口令；
    * 迁移 003 的 `users.password_hash` / `sessions.token_digest` 只承载**摘要**列，
      无任何口令 / 令牌**明文**列；含绑定与枚举 CHECK。
    """
    for key in _R13_KEYS:
        assert key in IB_RUNTIME_ENV_KEYS, f"{key} 未在 ib.config 登记（FND-R13-01 回归守卫）"
        assert key not in IB_ENV_KEYS, f"{key} 不得混入冻结的 IB_ENV_KEYS"

    env_text = _ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "IB_DEFAULT_ADMIN_PASSWORD=<REPLACE_ME" in env_text, "口令键必须只给占位符"
    assert "IB_AUTHZ_POLICY_MODULE=<REPLACE_ME" in env_text

    sql = _MIGRATION_003.read_text(encoding="utf-8")
    assert "password_hash" in sql and "token_digest" in sql
    assert "CREATE TABLE IF NOT EXISTS users" in sql and "CREATE TABLE IF NOT EXISTS sessions" in sql
    assert "CHECK (role IN ('admin', 'ops'))" in sql
    assert "CHECK (role = 'admin' OR project_id IS NOT NULL)" in sql, "1:1 绑定约束缺失"
    # 明文列名不得出现（password_hash / token_digest 是摘要列；裸 password / token 列是隐患）
    lowered = sql.lower()
    assert "\n    password " not in lowered and " password text" not in lowered
    assert " token " not in lowered and " token text" not in lowered

    check_text = _CHECKLISTS.read_text(encoding="utf-8")
    for item in ("[B15]", "[B16]", "[B17]", "[B18]", "[B19]", "[B20]"):
        assert item in check_text, f"部署检查清单缺少 {item}"


def test_TC_INT_122_migration_single_source_column_parity(tmp_path):
    """US-IB-28 / REQ-FUNC-IB-30（IFC-IB-330）：迁移 003 与运行时 schema **列级单源一致**。

    对**同一份** `003_accounts.sql` 与 `ib.ledger.schema.ensure_schema()` 分别建表，
    断言 `users` / `sessions` 的列集合完全一致 —— 为 MINOR-R13-05（「单源一致性无机器断言」）
    补一条可执行的列级断言（语句级字节一致仍不在本用例范围）。
    """
    from ib.ledger.schema import ensure_schema

    runtime = sqlite3.connect(":memory:")
    try:
        ensure_schema(runtime)
        runtime_users = [row[1] for row in runtime.execute("PRAGMA table_info(users)")]
        runtime_sessions = [row[1] for row in runtime.execute("PRAGMA table_info(sessions)")]
    finally:
        runtime.close()

    migrated = sqlite3.connect(":memory:")
    try:
        migrated.executescript(_MIGRATION_003.read_text(encoding="utf-8"))
        migrated_users = [row[1] for row in migrated.execute("PRAGMA table_info(users)")]
        migrated_sessions = [row[1] for row in migrated.execute("PRAGMA table_info(sessions)")]
    finally:
        migrated.close()

    assert runtime_users == migrated_users, "users 列与迁移 003 漂移"
    assert runtime_sessions == migrated_sessions, "sessions 列与迁移 003 漂移"
