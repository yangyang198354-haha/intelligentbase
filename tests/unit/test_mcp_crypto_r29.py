"""[REV-29 / GROUP_D] 单元：凭证加解密端口层——同一套 SecretCipher 契约跑 ReversibleTestCipher 与 UnconfiguredSecretCipher，
Secret 脱敏，输入校验，组合根 make_secret_cipher 分支。开发机（无 cryptography）也必跑。

分层：unit。溯源：US-006（AC-006-01 / 04 / 06）。真实 Fernet 契约见 test_mcp_crypto_fernet_r29.py。
"""

from __future__ import annotations

import copy
import importlib.util
import pickle

import pytest
from mcp_r29_support import SECRET_KEY

from ib.core.errors import ConfigError
from ib.mcp.crypto import (
    FernetSecretCipher,
    Secret,
    SecretKeyError,
    UnconfiguredSecretCipher,
    validate_credential_input,
    validate_header_name,
)
from ib.mcp.double import ReversibleTestCipher

HAS_CRYPTO = importlib.util.find_spec("cryptography") is not None
PLAIN = "S3cr3t-Canary-Value-91ac"


def test_TC_UNIT_R29_200_secret_is_redacted_everywhere_AC_006_01():
    """AC-006-01 / 04：Secret 的 repr/str/f-string/pickle/deepcopy 都不带值；reveal 才给值。"""
    s = Secret(PLAIN)
    assert repr(s) == "***" and str(s) == "***" and f"{s}" == "***" and f"{s!r}" == "***"
    assert PLAIN not in repr([s]) and PLAIN not in str({"k": s})
    with pytest.raises(TypeError):
        pickle.dumps(s)
    with pytest.raises(TypeError):
        copy.deepcopy(s)
    assert s.reveal() == PLAIN


def test_TC_UNIT_R29_201_reversible_cipher_round_trip_and_no_plaintext_in_token_AC_006_01():
    c = ReversibleTestCipher(SECRET_KEY)
    assert c.configured is True
    tok, key_id = c.encrypt(Secret(PLAIN))
    assert isinstance(tok, bytes) and PLAIN.encode() not in tok and key_id
    assert c.decrypt(tok).reveal() == PLAIN


def test_TC_UNIT_R29_202_reversible_cipher_wrong_key_and_garbage_fail_without_value():
    """失败分支：错误主密钥 / 乱码令牌 ⇒ SecretKeyError(token_invalid)，消息不含明文。"""
    good = ReversibleTestCipher(SECRET_KEY)
    tok, _ = good.encrypt(Secret(PLAIN))
    other = ReversibleTestCipher("another-primary-key-value")
    for bad_tok in (tok, b"garbage", b"", b"TESTCIPHER:zz.12345678"):
        with pytest.raises(SecretKeyError) as ei:
            other.decrypt(bad_tok)
        assert ei.value.reason == "token_invalid" and PLAIN not in str(ei.value)


def test_TC_UNIT_R29_203_previous_key_still_decrypts_new_key_encrypts():
    """轮换：新钥加密、旧钥令牌仍可解（正例）。"""
    old = ReversibleTestCipher("old-key")
    tok_old, _ = old.encrypt(Secret(PLAIN))
    rotated = ReversibleTestCipher("new-key", ("old-key",))
    assert rotated.decrypt(tok_old).reveal() == PLAIN
    tok_new, _ = rotated.encrypt(Secret("x"))
    with pytest.raises(SecretKeyError):
        old.decrypt(tok_new)


def test_TC_UNIT_R29_204_unconfigured_cipher_fail_closed_AC_006_06():
    """AC-006-06：未配置主密钥 ⇒ 加密 / 解密一律 secret_key_missing（fail-closed），且 configured=False。"""
    u = UnconfiguredSecretCipher()
    assert u.configured is False
    for fn in (lambda: u.encrypt(Secret(PLAIN)), lambda: u.decrypt(b"x")):
        with pytest.raises(SecretKeyError) as ei:
            fn()
        assert ei.value.reason == "secret_key_missing" and PLAIN not in str(ei.value)


def test_TC_UNIT_R29_205_reversible_cipher_without_keys_refuses_to_encrypt():
    with pytest.raises(SecretKeyError) as ei:
        ReversibleTestCipher("").encrypt(Secret(PLAIN))
    assert ei.value.reason == "secret_key_missing"


@pytest.mark.parametrize("bad", ["", "a" * 4097, "x\ny", "x\r", "x\0y", 5, None])
def test_TC_UNIT_R29_206_credential_input_rejected_AC_006_06(bad):
    with pytest.raises(ValueError) as ei:
        validate_credential_input(bad, auth_kind="bearer", header_name=None)  # type: ignore[arg-type]
    assert "x\ny" not in str(ei.value)


def test_TC_UNIT_R29_207_credential_input_accepted_and_none_kind_refused():
    assert validate_credential_input("a" * 4096, auth_kind="bearer", header_name=None).reveal() == "a" * 4096
    assert validate_credential_input("v", auth_kind="header", header_name="X-Api-Key").reveal() == "v"
    with pytest.raises(ValueError):
        validate_credential_input("v", auth_kind="none", header_name=None)  # none 鉴权不接受凭证


@pytest.mark.parametrize("name", ["Host", "content-length", "Cookie", "Authorization-X y", "mcp-session-id", "", "a" * 129, "带中文"])
def test_TC_UNIT_R29_208_auth_header_name_rejected(name):
    with pytest.raises(ValueError):
        validate_header_name(name)


def test_TC_UNIT_R29_209_auth_header_name_accepted():
    assert validate_header_name("X-Api-Key") == "X-Api-Key"


# -- 组合根 make_secret_cipher 四个分支（ADR-R29-17）-------------------------- #


def test_TC_UNIT_R29_210_make_secret_cipher_unconfigured_when_no_key():
    from ibweb.composition import make_secret_cipher

    for key in (None, "", "   "):
        for offline in (True, False):
            c = make_secret_cipher(key, offline=offline)
            assert isinstance(c, UnconfiguredSecretCipher) and c.configured is False


def test_TC_UNIT_R29_211_make_secret_cipher_offline_branch_matches_cryptography_availability():
    """offline=True：cryptography 可导入 ⇒ Fernet；不可导入 ⇒ ReversibleTestCipher。期望由 find_spec 独立判定，不取自被测代码。"""
    from ibweb.composition import make_secret_cipher

    c = make_secret_cipher(SECRET_KEY, offline=True)
    assert isinstance(c, FernetSecretCipher if HAS_CRYPTO else ReversibleTestCipher)
    assert c.configured is True


def test_TC_UNIT_R29_212_make_secret_cipher_production_never_returns_test_cipher_AC_006_01():
    """非离线：永不返回 ReversibleTestCipher——不可导入 cryptography 时启动失败（ConfigError，键名，不含值）。"""
    from ibweb.composition import make_secret_cipher

    if HAS_CRYPTO:
        assert isinstance(make_secret_cipher(SECRET_KEY, offline=False), FernetSecretCipher)
        return
    with pytest.raises(ConfigError) as ei:
        make_secret_cipher(SECRET_KEY, offline=False)
    assert ei.value.key == "IB_MCP_SECRET_KEY" and SECRET_KEY not in str(ei.value)


def test_TC_UNIT_R29_213_production_rejects_fake_transport_AC_NFUNC_005():
    """非离线 + IB_MCP_TRANSPORT=fake ⇒ ConfigError(IB_MCP_TRANSPORT)，消息不含所配值；http 取值通过（正例）。"""
    from ib.config import GlobalConfig, validate_required

    errs = validate_required(GlobalConfig(mcp_transport="fake"), env={})
    assert any(getattr(e, "key", None) == "IB_MCP_TRANSPORT" for e in errs)
    ok = validate_required(GlobalConfig(mcp_transport="http"), env={})
    assert not [e for e in ok if getattr(e, "key", None) == "IB_MCP_TRANSPORT"]
