"""[REV-29 / GROUP_D] 单元：真实 Fernet 契约（cryptography）+ CI 门禁守卫（GR-C-003 条件 1，CR-001）。

分层：unit。溯源：US-006（AC-006-01 / 03 / 04）。

门禁语义：
  * cryptography 已安装：契约用例照常运行；
  * 未安装且环境变量 IB_REQUIRE_CRYPTO != 1（开发机）：契约用例 SKIP（原因：cryptography 未安装），不得计 PASS；
  * 未安装且 IB_REQUIRE_CRYPTO=1（CI）：守卫用例与全部契约用例 **失败**而非 skip，CI 不会静默变绿。
"""

from __future__ import annotations

import base64
import importlib
import os

import pytest
from mcp_r29_support import SECRET_KEY

from ib.core.errors import ConfigError
from ib.mcp.crypto import FernetSecretCipher, Secret, SecretKeyError

REQUIRE = os.environ.get("IB_REQUIRE_CRYPTO") == "1"
PLAIN = "S3cr3t-Canary-Value-91ac"
OLD_KEY = base64.urlsafe_b64encode(b"o" * 32).decode()


def _crypto_available() -> bool:
    try:
        importlib.import_module("cryptography.fernet")
        return True
    except ImportError:
        return False


@pytest.fixture()
def crypto():
    """可用 ⇒ 返回模块；不可用 ⇒ REQUIRE 时失败，否则 skip。"""
    if _crypto_available():
        return importlib.import_module("cryptography.fernet")
    if REQUIRE:
        pytest.fail("IB_REQUIRE_CRYPTO=1 但 cryptography 不可导入：CI 必须装真实依赖并跑 Fernet 契约（ADR-R29-17）")
    pytest.skip("cryptography 未安装（开发机现状）；Fernet 契约在 CI（IB_REQUIRE_CRYPTO=1）必跑")


def test_TC_UNIT_R29_220_require_crypto_guard_fails_instead_of_skipping_in_ci():
    """守卫：IB_REQUIRE_CRYPTO=1 且 cryptography 不可导入 ⇒ 失败（不 skip）。其余情形通过。
    本用例不依赖被测代码：只检查 环境开关 × 依赖可用性 的组合。"""
    if not REQUIRE:
        pytest.skip("IB_REQUIRE_CRYPTO 未设置（开发机）：守卫仅在 CI 门禁口径下有意义；本机验证见报告“IB_REQUIRE_CRYPTO=1 本机演示”")
    assert _crypto_available(), "IB_REQUIRE_CRYPTO=1 ⇒ cryptography 必须已安装（CI 不得静默跳过 Fernet 契约）"


def test_TC_UNIT_R29_221_fernet_round_trip_and_ciphertext_has_no_plaintext(crypto):
    c = FernetSecretCipher(SECRET_KEY)
    assert c.configured is True
    tok, key_id = c.encrypt(Secret(PLAIN))
    assert PLAIN.encode() not in tok and key_id.startswith("fernet:")
    assert c.decrypt(tok).reveal() == PLAIN


def test_TC_UNIT_R29_222_multifernet_old_key_decrypts_new_key_encrypts(crypto):
    """AC-006-03 轮换：旧钥令牌可被 (新钥, 旧钥) 解开；新钥产出的令牌旧钥单独解不开。"""
    old = FernetSecretCipher(OLD_KEY)
    tok_old, _ = old.encrypt(Secret(PLAIN))
    rotated = FernetSecretCipher(SECRET_KEY, (OLD_KEY,))
    assert rotated.decrypt(tok_old).reveal() == PLAIN
    tok_new, _ = rotated.encrypt(Secret(PLAIN))
    with pytest.raises(SecretKeyError):
        old.decrypt(tok_new)


def test_TC_UNIT_R29_223_bad_token_error_does_not_leak_value(crypto):
    c = FernetSecretCipher(SECRET_KEY)
    for bad in (b"garbage", b"", base64.urlsafe_b64encode(b"x" * 64)):
        with pytest.raises(SecretKeyError) as ei:
            c.decrypt(bad)
        assert ei.value.reason == "token_invalid" and PLAIN not in str(ei.value)


def test_TC_UNIT_R29_224_invalid_key_format_raises_config_error_without_value(crypto):
    """非法主密钥格式 ⇒ ConfigError（键名），消息不含所配值。"""
    bad = "not-a-fernet-key-VALUE-xyz"
    with pytest.raises(ConfigError) as ei:
        FernetSecretCipher(bad)
    assert ei.value.key == "IB_MCP_SECRET_KEY" and bad not in str(ei.value)


def test_TC_UNIT_R29_225_composition_picks_real_fernet_when_available(crypto):
    from ibweb.composition import make_secret_cipher

    assert isinstance(make_secret_cipher(SECRET_KEY, offline=True), FernetSecretCipher)
    assert isinstance(make_secret_cipher(SECRET_KEY, offline=False), FernetSecretCipher)
