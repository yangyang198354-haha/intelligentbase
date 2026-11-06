# MOD-R29-06 / implements IFC-R29-050..052 / depends MOD-R29-01
"""凭证加解密：`Secret` 脱敏包装、Fernet 实现（`cryptography` 延迟导入）、未配置实现。

ADR-R29-17：无 `cryptography` 的环境下 `import ib.mcp.crypto` 必须成功（开发 venv 现状）；
真实 Fernet 在构造 `FernetSecretCipher` 时才导入。本模块**不** import `ib.mcp.double`（避免 06 ↔ 09 成环）。
"""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

from ib.core.errors import ConfigError

__all__ = [
    "Secret",
    "SecretKeyError",
    "FernetSecretCipher",
    "UnconfiguredSecretCipher",
    "validate_credential_input",
    "validate_header_name",
    "FORBIDDEN_AUTH_HEADERS",
    "SECRET_MAX_CHARS",
]

SECRET_MAX_CHARS = 4096
_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
#: 不得用作自定义鉴权头名的头（传输 / 协议自有头）
FORBIDDEN_AUTH_HEADERS = frozenset(
    {
        "host", "content-length", "content-type", "content-encoding", "transfer-encoding", "connection",
        "accept", "accept-encoding", "cookie", "set-cookie", "upgrade", "te", "trailer", "expect",
        "proxy-authorization", "proxy-connection", "keep-alive", "origin", "referer", "user-agent",
    }
)


class Secret:
    """脱敏包装：repr / str 恒为 `***`；`reveal()` 仅 transport 与 cipher 调用。"""

    __slots__ = ("_v",)

    def __init__(self, value: str) -> None:
        self._v = value

    def reveal(self) -> str:
        return self._v

    def __repr__(self) -> str:
        return "***"

    def __str__(self) -> str:
        return "***"

    def __reduce__(self):  # 防止被 pickle / copy 带出
        raise TypeError("Secret 不可序列化")

    def __eq__(self, other: object) -> bool:  # 恒定时间比较足够（仅测试 / 去重用）
        return isinstance(other, Secret) and self._v == other._v

    def __hash__(self) -> int:
        return hash(("Secret", len(self._v)))


class SecretKeyError(Exception):
    """reason ∈ {secret_key_missing, cryptography_unavailable, token_invalid}；消息不含任何值。"""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class FernetSecretCipher:
    """MultiFernet([primary, *previous])：新钥加密、新旧钥解密。"""

    configured = True

    def __init__(self, primary_key: str, previous_keys: Sequence[str] = ()) -> None:
        try:
            from cryptography.fernet import Fernet, MultiFernet  # 延迟导入（ADR-R29-17）
        except ImportError:
            raise SecretKeyError("cryptography_unavailable") from None
        try:
            fernets = [Fernet(k.strip().encode("ascii")) for k in (primary_key, *previous_keys) if k and k.strip()]
        except Exception:  # noqa: BLE001 - 非法密钥格式：只报键名，不回显值
            raise ConfigError("IB_MCP_SECRET_KEY 不是合法的 Fernet 密钥", key="IB_MCP_SECRET_KEY") from None
        if not fernets:
            raise ConfigError("IB_MCP_SECRET_KEY 不是合法的 Fernet 密钥", key="IB_MCP_SECRET_KEY")
        self._multi = MultiFernet(fernets)
        self._key_id = "fernet:" + hashlib.sha256(primary_key.strip().encode("utf-8")).hexdigest()[:8]

    def encrypt(self, plain: Secret) -> tuple[bytes, str]:
        return self._multi.encrypt(plain.reveal().encode("utf-8")), self._key_id

    def decrypt(self, token: bytes) -> Secret:
        try:
            return Secret(self._multi.decrypt(bytes(token)).decode("utf-8"))
        except Exception:  # noqa: BLE001 - InvalidToken / 解码失败：不含值
            raise SecretKeyError("token_invalid") from None


class UnconfiguredSecretCipher:
    """主密钥未配置：一律拒绝（fail-closed）。"""

    configured = False

    def encrypt(self, plain: Secret) -> tuple[bytes, str]:
        raise SecretKeyError("secret_key_missing")

    def decrypt(self, token: bytes) -> Secret:
        raise SecretKeyError("secret_key_missing")


def validate_header_name(name: str | None) -> str:
    """自定义鉴权头名：token 字符集、≤128、不在禁用集、不以 mcp- 开头。违规 ⇒ ValueError（消息不含值）。"""
    if not isinstance(name, str) or not name or len(name) > 128 or not _TOKEN_RE.match(name):
        raise ValueError("auth_header_name_invalid")
    low = name.lower()
    if low in FORBIDDEN_AUTH_HEADERS or low.startswith("mcp-"):
        raise ValueError("auth_header_name_forbidden")
    return name


def validate_credential_input(secret: str, *, auth_kind: str, header_name: str | None) -> Secret:
    """1–4096 字符、无 CR/LF/NUL；auth_kind=none 不接受凭证；header 名合规。违规 ⇒ ValueError（不含值）。"""
    if auth_kind not in ("bearer", "header"):
        raise ValueError("auth_kind_no_credential")
    if not isinstance(secret, str) or not (1 <= len(secret) <= SECRET_MAX_CHARS):
        raise ValueError("secret_length_invalid")
    if any(c in secret for c in "\r\n\0"):
        raise ValueError("secret_charset_invalid")
    if auth_kind == "header":
        validate_header_name(header_name)
    return Secret(secret)
