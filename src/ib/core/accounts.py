"""
@module MOD-IB-01
@implements IFC-IB-311 令牌原语（new_session_token / token_digest / token_digest_matches）
@depends (none)
@author software-developer

令牌原语（R13 增量）。**纯函数，仅 stdlib `secrets` / `hashlib` / `hmac`**，零第三方依赖。

## 为什么令牌「存摘要」而不是「存原文」（ADR-19）

会话令牌在数据库里以 **SHA-256 摘要**形式存放。于是「读到了库」不等于「拿到了可用令牌」：
即便台账文件被拷走，攻击者也无法从摘要反推出能被服务接受的令牌原文。这与口令用 bcrypt
（慢哈希）是同一思路的两个变体 —— 令牌本身熵足够高（256-bit），故用快速哈希即可，
真正需要的是**单向性**；口令熵低，故用**慢**哈希抵御离线爆破。

## 为什么比较用 `hmac.compare_digest`（常量时间）

逐字符提前返回的比较函数会让攻击者按响应时间逐位猜出令牌（经典时序侧信道）。
正确写法只多一行，因此没有理由不写。注意：本函数是**兜底**比较（如离线态共享令牌）；
正常路径上「摘要 vs 摘要」的查表比较不构成时序面（攻击者无法构造部分命中）。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

__all__ = ["new_session_token", "token_digest", "token_digest_matches"]

#: 令牌字节熵：`secrets.token_urlsafe(32)` = 32 字节 = 256 bit。
#: 为什么不是更短：令牌是**唯一**的持有型凭据（无 Cookie / 无二次因子），
#: 离线爆破的下界必须足够高；32 字节在 URL-safe 编码后为 43 字符，长度代价可忽略。
_TOKEN_BYTES = 32


def new_session_token() -> str:
    """生成新的会话令牌（IFC-IB-311）：URL-safe 的 256-bit 随机串。

    使用 `secrets`（OS 熵源）而**不是** `random`：后者是可预测的 Mersenne Twister，
    其输出可被观察若干次后反推内部状态 —— 对持有型凭据是致命的。
    """
    return secrets.token_urlsafe(_TOKEN_BYTES)


def token_digest(token: str) -> str:
    """令牌 → SHA-256 hex 摘要（IFC-IB-311）。**服务端只存此值**。

    对空串也返回合法 hex（不抛异常）：调用方（解析器）在拿到空令牌时应返回 `None`，
    不必为此处增加一条异常路径。
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_digest_matches(token: str, digest: str) -> bool:
    """常量时间比较 `token` 的摘要与给定摘要（IFC-IB-311）。

    用于「已知摘要」场景的兜底比对（如离线自测的共享令牌）。正常会话解析走查表，
    不经过本函数。
    """
    if not token or not digest:
        return False
    return hmac.compare_digest(token_digest(token), digest)
