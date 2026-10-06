"""单元测试层 —— R13 增量（账户 / 会话 / 令牌 / 授权端口协作）。

覆盖 REV-13 新增的**模块内行为**（单模块、无 HTTP、无 Django）：
  * MOD-IB-01 令牌原语（IFC-IB-311）与 `AccountStore` 端口两实现；
  * MOD-IB-11 bcrypt 口令 / `MemoryAccountStore` / `SqliteAccountStore` / 幂等种子；
  * MOD-IB-23 `SessionTokenResolver`（令牌 → 主体）/ 内置 `AccountsPolicy` / `LoginThrottle`。

溯源：每个用例在 docstring 标注 **US-IB-NN / AC-IB-NN-NN**（验收标准级覆盖证据）。
离线约束：纯 stdlib + 临时目录 SQLite，不触网、不连任何外部依赖（conftest 附录 D 口径）。
凭据纪律：不出现任何真实口令 / 令牌；仅用于装配的**测试占位**值（见 conftest 说明）。
"""

from __future__ import annotations

import inspect
import sqlite3

import pytest

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import (
    AuthzContext,
    ConflictError,
    PasswordPolicy,
    SessionRecord,
    StartupError,
    UserRecord,
)
from ib.ledger.accounts import (
    MemoryAccountStore,
    SqliteAccountStore,
    hash_password,
    seed_default_admin,
    verify_password,
)
from ib.core import new_session_token, token_digest, token_digest_matches
from ibweb.accounts import (
    GLOBAL_PROJECT,
    SessionTokenResolver,
    effective_roles,
    password_policy,
    validate_password_strength,
)
from ibweb.accounts.policy import POLICY as ACCOUNTS_POLICY
from ibweb.accounts.throttle import LoginThrottle, audit, build_throttle
from ibweb.authz import build_authz


#: 测试用**占位**口令（非生产凭据；生产初始口令仅经 `IB_DEFAULT_ADMIN_PASSWORD` 注入）。
_PW = "GroupD-Test-Password-1!"


def _seeded_store() -> tuple[MemoryAccountStore, UserRecord, str]:
    store = MemoryAccountStore()
    user = store.create_user("admin", hash_password(_PW), "admin", None)
    token = new_session_token()
    return store, user, token


# --------------------------------------------------------------------------- #
# TC-UNIT-083 令牌原语（IFC-IB-311）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_083_token_primitives_are_opaque_and_digest_only():
    """US-IB-25 / AC-IB-25-01：令牌不透明、唯一、服务端只存摘要（令牌原文不入库）。

    REQ-FUNC-IB-29 约束①（不透明）：令牌不可由客户端凭据推导 —— 两次生成必不同；
    约束⑤（令牌不入日志）在存储侧表现为「库中只有 sha256 摘要」。
    """
    a, b = new_session_token(), new_session_token()
    assert a != b, "两次令牌生成不得相同（否则可预测）"
    assert a.isalnum() or "-" in a or "_" in a  # URL-safe
    assert len(a) >= 32, "令牌熵不足（应 ≥32 字符）"

    digest = token_digest(a)
    assert len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest)
    assert token_digest(a) == digest, "同一令牌摘要必须稳定"
    assert token_digest_matches(a, digest) is True
    assert token_digest_matches(b, digest) is False
    assert token_digest("") == token_digest("") and token_digest_matches("", digest) is False

    # 存储层只认摘要：把令牌**原文**当摘要去解析，必然解析不到（证明存的是摘要）。
    store, user, token = _seeded_store()
    store.issue_session(user.user_id, token_digest(token), expires_at=iso_plus_seconds(600))
    assert store.resolve_session(token, now=utc_now_iso()) is None, "原文令牌不得能直接命中原文字段"
    assert store.resolve_session(token_digest(token), now=utc_now_iso()) is not None


# --------------------------------------------------------------------------- #
# TC-UNIT-084 MemoryAccountStore 端口语义
# --------------------------------------------------------------------------- #


def test_TC_UNIT_084_memory_store_creation_semantics():
    """US-IB-22 / US-IB-23 / AC-IB-22-01、AC-IB-23-01、AC-IB-23-02。

    新建账户一律 `must_change_password=True`（首登强制改密，ADR-20）；
    用户名唯一（1 账户 1 名）；`ops` 必须绑定项目（1:1 绑定不可悬空）。
    """
    store = MemoryAccountStore()
    admin = store.create_user("admin", hash_password(_PW), "admin", None)
    assert admin.role == "admin" and admin.project_id is None
    assert admin.status == "active" and admin.must_change_password is True

    ops = store.create_user("ops_a", hash_password(_PW), "ops", "p_alpha")
    assert ops.role == "ops" and ops.project_id == "p_alpha"
    assert ops.must_change_password is True

    # 用户名唯一 → 冲突
    with pytest.raises(ConflictError):
        store.create_user("ops_a", hash_password(_PW), "ops", "p_beta")

    # ops 未绑定项目 → 拒绝（AC-IB-23-02：账户 : 项目 = 1 : 1）
    with pytest.raises(ConflictError):
        store.create_user("ops_no_proj", hash_password(_PW), "ops", None)

    # 列表可按项目过滤（跨项目不可见 → 项目边界）
    assert [u.username for u in store.list_users("p_alpha")] == ["ops_a"]
    assert [u.username for u in store.list_users("p_beta")] == []
    assert {u.username for u in store.list_users(None)} == {"admin", "ops_a"}


# --------------------------------------------------------------------------- #
# TC-UNIT-085 bcrypt 口令哈希与校验
# --------------------------------------------------------------------------- #


def test_TC_UNIT_085_password_hash_is_bcrypt_and_never_plaintext():
    """US-IB-22 / AC-IB-22-03（REQ-NFR-IB-15）：口令只落 bcrypt 摘要，永不落明文。

    仓储中不得出现口令原文；校验失败一律 `False`（fail-closed，含损坏摘要）。
    """
    digest = hash_password(_PW)
    assert digest != _PW and _PW not in digest
    assert digest.startswith(("$2a$", "$2b$", "$2y$")), "非 bcrypt 摘要"
    assert verify_password(_PW, digest) is True
    assert verify_password(_PW + "x", digest) is False
    # fail-closed：空 / 损坏摘要不得抛异常，一律 False
    assert verify_password("", digest) is False
    assert verify_password(_PW, "") is False
    assert verify_password(_PW, "not-a-bcrypt-hash") is False

    # 落库的是摘要：存储中的 password_hash 是 bcrypt 摘要，口令原文不出现在任何字段
    store = MemoryAccountStore()
    user = store.create_user("ops_b", hash_password(_PW), "ops", "p_alpha")
    assert user.password_hash.startswith("$2") and verify_password(_PW, user.password_hash)
    import dataclasses

    assert all(_PW not in str(getattr(user, f.name)) for f in dataclasses.fields(user))


# --------------------------------------------------------------------------- #
# TC-UNIT-086 会话签发 / 校验 / 过期 / 撤销（fail-closed）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_086_session_issue_resolve_expiry_revoke():
    """US-IB-25 / AC-IB-25-01、AC-IB-25-02：有效可解析；过期 / 撤销 / 未知一律不可解析。"""
    store, user, token = _seeded_store()
    digest = token_digest(token)

    session = store.issue_session(user.user_id, digest, expires_at=iso_plus_seconds(600))
    assert isinstance(session, SessionRecord)
    assert session.token_digest == digest and session.revoked_at is None
    resolved = store.resolve_session(digest, now=utc_now_iso())
    assert resolved is not None and resolved.user_id == user.user_id

    # 未知摘要 → None
    assert store.resolve_session(token_digest("nope"), now=utc_now_iso()) is None

    # 已过期 → None（AC-IB-25-02）
    expired_token = new_session_token()
    store.issue_session(user.user_id, token_digest(expired_token), expires_at=iso_plus_seconds(-5))
    assert store.resolve_session(token_digest(expired_token), now=utc_now_iso()) is None

    # 撤销 → None（登出，AC-IB-25-02）
    store.revoke_session(digest, now=utc_now_iso())
    assert store.resolve_session(digest, now=utc_now_iso()) is None
    # 幂等
    store.revoke_session(digest, now=utc_now_iso())


# --------------------------------------------------------------------------- #
# TC-UNIT-087 会话续期（滑动窗口；不重置 issued_at）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_087_renew_session_slides_expiry_without_changing_issued_at():
    """US-IB-25 / AC-IB-25-03：临近过期可续期 → `expires_at` 被延长，用户无需重登。

    本轮实现为**滑动窗口**：续期只改 `expires_at` / `last_seen_at`，`issued_at`（绝对起点）
    保持不变 —— 即「延长有效期」而非「重开会话」。过期 / 已撤销的会话**不可**续期（fail-closed）。
    """
    store, user, token = _seeded_store()
    digest = token_digest(token)
    original = store.issue_session(user.user_id, digest, expires_at=iso_plus_seconds(120))

    later = iso_plus_seconds(3600)
    renewed = store.renew_session(digest, new_expires_at=later, now=utc_now_iso())
    assert renewed is not None
    assert renewed.expires_at == later and renewed.expires_at != original.expires_at
    assert renewed.issued_at == original.issued_at, "续期不得重置绝对起点（issued_at）"

    # 已过期 → 不可续期
    store2, user2, token2 = _seeded_store()
    d2 = token_digest(token2)
    store2.issue_session(user2.user_id, d2, expires_at=iso_plus_seconds(-1))
    assert store2.renew_session(d2, new_expires_at=iso_plus_seconds(600), now=utc_now_iso()) is None

    # 已撤销 → 不可续期
    store.revoke_session(digest, now=utc_now_iso())
    assert store.renew_session(digest, new_expires_at=iso_plus_seconds(600), now=utc_now_iso()) is None


# --------------------------------------------------------------------------- #
# TC-UNIT-088 批量撤销（停用 / 改密 / 重置口令时「撤销其余会话」）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_088_revoke_sessions_for_user_all_and_keep_current():
    """US-IB-23 / AC-IB-23-03（停用后不得再登录）与 US-IB-22（改密撤销其余会话）。

    `keep_digest` 语义：改密时保留**当前**会话，撤销其余；停用 / 重置口令时不保留任何会话。
    """
    store, user, token = _seeded_store()
    keep = token_digest(token)
    other1, other2 = token_digest(new_session_token()), token_digest(new_session_token())
    store.issue_session(user.user_id, keep, expires_at=iso_plus_seconds(600))
    store.issue_session(user.user_id, other1, expires_at=iso_plus_seconds(600))
    store.issue_session(user.user_id, other2, expires_at=iso_plus_seconds(600))

    revoked = store.revoke_sessions_for_user(user.user_id, now=utc_now_iso(), keep_digest=keep)
    assert revoked == 2
    assert store.resolve_session(keep, now=utc_now_iso()) is not None
    assert store.resolve_session(other1, now=utc_now_iso()) is None
    assert store.resolve_session(other2, now=utc_now_iso()) is None

    # 不保留 → 全部撤销（停用 / 重置口令路径）
    assert store.revoke_sessions_for_user(user.user_id, now=utc_now_iso()) == 1
    assert store.resolve_session(keep, now=utc_now_iso()) is None


# --------------------------------------------------------------------------- #
# TC-UNIT-089 默认管理员幂等种子
# --------------------------------------------------------------------------- #


def test_TC_UNIT_089_seed_default_admin_is_idempotent_and_protects_password():
    """US-IB-22 / AC-IB-22-01：`admin` 全局账户 + 首登强制改密；重复播种不覆盖既有口令。"""
    store = MemoryAccountStore()
    first = seed_default_admin(store, username="admin", password_hash=hash_password(_PW))
    assert first.role == "admin" and first.project_id is None
    assert first.must_change_password is True and first.status == "active"

    # 幂等：第二次播种返回既有记录，且**不改写**口令摘要。
    other_hash = hash_password(_PW + "-different")
    second = seed_default_admin(store, username="admin", password_hash=other_hash)
    assert second.user_id == first.user_id
    assert second.password_hash == first.password_hash != other_hash


# --------------------------------------------------------------------------- #
# TC-UNIT-090 SessionTokenResolver：令牌 → 主体（fail-closed）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_090_resolver_maps_token_to_authz_context_fail_closed():
    """US-IB-27 / AC-IB-27-01；US-IB-24 / AC-IB-24-03；US-IB-23 / AC-IB-23-03。

    解析结果落入既有 `AuthzContext`；解析器**只做身份映射、不做授权判定**。
    fail-closed：未知 / 已撤销 / 已过期 / 已停用一律返回 `None`。
    """
    store = MemoryAccountStore()
    admin = store.create_user("admin", hash_password(_PW), "admin", None)
    ops = store.create_user("ops_a", hash_password(_PW), "ops", "p_alpha")
    resolver = SessionTokenResolver(store)

    admin_token = new_session_token()
    store.issue_session(admin.user_id, token_digest(admin_token), expires_at=iso_plus_seconds(600))
    ctx = resolver.resolve(admin_token)
    assert isinstance(ctx, AuthzContext)
    assert ctx.actor_id == admin.user_id
    assert ctx.project_id == GLOBAL_PROJECT, "admin 是全局主体（哨兵而非 None）"
    assert "admin" in ctx.roles

    ops_token = new_session_token()
    store.issue_session(ops.user_id, token_digest(ops_token), expires_at=iso_plus_seconds(600))
    ctx2 = resolver.resolve(ops_token)
    assert ctx2 is not None and ctx2.project_id == "p_alpha" and ctx2.roles == ("manager",)

    # 解析器无授权方法（AC-IB-27-03：不存在与 AuthzPolicy 并列的第二套授权真源）
    assert not hasattr(resolver, "can_manage") and not hasattr(resolver, "can_query")

    # fail-closed 四态
    assert resolver.resolve("") is None
    assert resolver.resolve(new_session_token()) is None  # 未知
    store.revoke_session(token_digest(ops_token), now=utc_now_iso())
    assert resolver.resolve(ops_token) is None  # 已撤销
    exp_user = store.create_user("ops_b", hash_password(_PW), "ops", "p_alpha")
    exp_token = new_session_token()
    store.issue_session(exp_user.user_id, token_digest(exp_token), expires_at=iso_plus_seconds(-1))
    assert resolver.resolve(exp_token) is None  # 已过期
    store.set_status(admin.user_id, "disabled")
    assert resolver.resolve(admin_token) is None  # 已停用

    assert effective_roles(admin) == ("admin",)
    assert effective_roles(ops) == ("manager",)


# --------------------------------------------------------------------------- #
# TC-UNIT-091 口令强度策略（服务端唯一裁决者）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_091_password_strength_policy():
    """US-IB-22 / AC-IB-22-02：新口令须满足强度约束（阈值见 OQ-IB-11，本轮取保守默认）。"""
    assert password_policy(min_length=12).min_length == 12
    policy = PasswordPolicy(min_length=8, require_classes=2)
    assert validate_password_strength("ValidPass1", policy) is None
    assert validate_password_strength("short1!", policy) is not None  # 长度不足
    assert validate_password_strength("alllowercase", policy) is not None  # 仅 1 类
    # 返回原因是**可读中文**且不含口令本身
    reason = validate_password_strength("alllowercase", policy)
    assert "alllowercase" not in reason


# --------------------------------------------------------------------------- #
# TC-UNIT-092 内置策略 / 限速 / 审计（条件性，ADR-27）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_092_accounts_policy_throttle_and_audit():
    """US-IB-27 / AC-IB-27-01；US-IB-29 / AC-IB-29-01、AC-IB-29-02。

    * `AccountsPolicy` 以角色放行（admin / manager 可管可问），**不做身份映射**；
    * `LoginThrottle` 按来源 IP 的固定窗口计数；
    * `build_throttle()` 未配置 `IB_LOGIN_MAX_FAILURES` 时返回 `None`（不启用）；
    * `audit()` 的签名**不接受** username / user_id / 口令 / 令牌（审计零凭据字段）。
    """
    # 策略：按角色
    assert ACCOUNTS_POLICY.can_manage(AuthzContext("u", "p_alpha", ("manager",))) is True
    assert ACCOUNTS_POLICY.can_query(AuthzContext("u", GLOBAL_PROJECT, ("admin",))) is True
    assert ACCOUNTS_POLICY.can_manage(AuthzContext("u", "p_alpha", ())) is False

    # 限速：窗口内到达阈值即拒绝
    throttle = LoginThrottle(max_attempts=2, window_seconds=900)
    assert throttle.check("anyone", "10.0.0.1").allow is True
    throttle.record_failure("10.0.0.1")
    throttle.record_failure("10.0.0.1")
    decision = throttle.check("anyone", "10.0.0.1")
    assert decision.allow is False and decision.retry_after_seconds >= 1
    assert throttle.check("anyone", "10.0.0.2").allow is True, "限速按来源 IP 维度，不跨 IP 扩散"
    throttle.record_success("10.0.0.1")
    assert throttle.check("anyone", "10.0.0.1").allow is True

    # 条件性：未配置 → 不启用（ADR-27 / OQ-IB-12）
    import os

    saved = os.environ.pop("IB_LOGIN_MAX_FAILURES", None)
    try:
        assert build_throttle() is None
        os.environ["IB_LOGIN_MAX_FAILURES"] = "3"
        built = build_throttle()
        assert isinstance(built, LoginThrottle)
    finally:
        os.environ.pop("IB_LOGIN_MAX_FAILURES", None)
        if saved is not None:
            os.environ["IB_LOGIN_MAX_FAILURES"] = saved

    # 审计签名不含任何凭据字段（AC-IB-29-02）
    params = set(inspect.signature(audit).parameters)
    assert params == {"event", "outcome", "status", "project_id"}
    assert not ({"username", "user_id", "password", "token", "token_digest"} & params)
    audit("login", outcome="login_success", status="ok")  # 不抛异常即通过（落点经日志白名单）


# --------------------------------------------------------------------------- #
# TC-UNIT-093 SqliteAccountStore 真实存储路径（IFC-IB-313）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_093_sqlite_store_roundtrip_and_constraints(tmp_path):
    """US-IB-23 / AC-IB-23-01、AC-IB-23-02；US-IB-25 / AC-IB-25-01。

    真实 SQLite 路径与内存替身同语义；双实现均**拒绝**「ops 无项目」的非法绑定
    （差异：Sqlite 由 CHECK 兜底抛 `IntegrityError`，内存实现抛 `ConflictError` ——
    两者都 fail-closed，错误类型差异见 test_report 观察项）。
    """
    store = SqliteAccountStore(str(tmp_path / "ledger.sqlite3"))
    try:
        user = store.create_user("ops_a", hash_password(_PW), "ops", "p_alpha")
        assert store.get_user_by_username("ops_a").user_id == user.user_id
        assert store.get_user(user.user_id).project_id == "p_alpha"
        assert store.list_users("p_alpha")[0].username == "ops_a"
        assert store.list_users("p_beta") == []

        token = new_session_token()
        store.issue_session(user.user_id, token_digest(token), expires_at=iso_plus_seconds(600))
        assert store.resolve_session(token_digest(token), now=utc_now_iso()) is not None
        store.revoke_session(token_digest(token), now=utc_now_iso())
        assert store.resolve_session(token_digest(token), now=utc_now_iso()) is None

        # 用户名唯一
        with pytest.raises(ConflictError):
            store.create_user("ops_a", hash_password(_PW), "ops", "p_alpha")
        # ops 无项目 → 存储层 CHECK 兜底（fail-closed）
        with pytest.raises((sqlite3.IntegrityError, ConflictError)):
            store.create_user("ops_no_proj", hash_password(_PW), "ops", None)
    finally:
        store.close()

    # 内存替身对同一非法绑定也 fail-closed（端口一致性）
    mem = MemoryAccountStore()
    with pytest.raises((sqlite3.IntegrityError, ConflictError)):
        mem.create_user("ops_no_proj", hash_password(_PW), "ops", None)


# --------------------------------------------------------------------------- #
# TC-UNIT-094 与既有注入式 AuthzPolicy 端口的协作（REQ-FUNC-IB-33）
# --------------------------------------------------------------------------- #


def test_TC_UNIT_094_authz_port_collaboration_fail_closed(monkeypatch):
    """US-IB-27 / AC-IB-27-02、AC-IB-27-03。

    生产环境缺 `IB_AUTHZ_POLICY_MODULE` → `StartupError`（fail-closed，不静默降级）；
    显式注入 `ibweb.accounts.policy` → 返回 `(POLICY, PrincipalResolver)`，解析器为
    `resolve(token)` 方法形态（适配裸函数）。授权判定**仍**只经注入的 `AuthzPolicy`。
    """
    monkeypatch.delenv("IB_AUTHZ_POLICY_MODULE", raising=False)
    with pytest.raises(StartupError):
        build_authz(offline_mode=False, project_id="p_alpha")

    monkeypatch.setenv("IB_AUTHZ_POLICY_MODULE", "ibweb.accounts.policy")
    policy, resolver = build_authz(offline_mode=False, project_id="p_alpha")
    assert policy is ACCOUNTS_POLICY and policy.name == "ibweb.accounts"
    assert hasattr(resolver, "resolve"), "注入的裸函数必须适配成 .resolve(token) 方法"

    # 离线模式：不要求策略模块（既有离线替身保留，仅限离线自测）
    monkeypatch.delenv("IB_AUTHZ_POLICY_MODULE", raising=False)
    monkeypatch.setenv("IB_OFFLINE_TOKEN", "groupd-offline-token")
    offline_policy, offline_resolver = build_authz(offline_mode=True, project_id="p_alpha")
    assert offline_policy is not None and hasattr(offline_resolver, "resolve")
