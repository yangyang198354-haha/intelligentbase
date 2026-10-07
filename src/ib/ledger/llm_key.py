"""
@module MOD-IB-11
@implements IFC-IB-371 SqliteLlmKeyStore / MemoryLlmKeyStore（LLM Key 单行表适配器）
            IFC-IB-368 LlmKeyStore 端口（3 方法）的 SQL / 内存两实现
@depends MOD-IB-01（端口与结构）, MOD-IB-11（schema）
@author software-developer

LLM Key 的持久化（REV-18 增量；module_design.md §3 MOD-IB-11；ADR-38 / IFC-IB-371）。

## 单行表 = 全局唯一（以结构保证）

`llm_key(id INTEGER PRIMARY KEY CHECK(id=1), secret, updated_at)` —— **单行**由
`CHECK(id=1)` 表达，故「全局唯一一个 Key」是**表结构层面的事实**（OQ-IB-26；
项目级 / 多供应商 = OOS-18，为扩展点预留，本轮不做）。

## 凭据纪律（C-IB-42 / REQ-NFR-IB-20，硬约束）

  * **唯一写入口** = HTTP `PUT /api/llm-key`（本模块的 `set()` 是其底层）；
  * `get()` 返回的 `LlmKeyRecord.secret` **仅用于组合根装配期解析**（唯一读点），
    **绝不写入任何日志 / 响应 / 审计**；
  * 对外只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`）——
    **类型层不含明文字段**；`masked` 为固定占位掩码（不含明文任何前 / 后缀字符）；
  * 承载**库文件 0660（组 `ib` 共享）且属主对齐服务账号**（部署检查清单 B22；属主对齐由
    **用户**在部署期执行，本模块只做 best-effort 收紧权限位）。
    **不可用 `0600`** —— 见下节的「两个服务账号」硬约束（DEFECT-R18-01，2026-10-07 生产事故）；
  * Key **不入 `.env` / 不进 git / 不进命令行与 shell history**（B23）。

## 同一 SQLite 台账

`SqliteLlmKeyStore` 与台账 / 账户 / 审计 / 注册表指向**同一** `IB_LEDGER_PATH`
（ADR-38：不引入第二个存储后端）；**WAL + `busy_timeout` 必开**（沿用 MOD-IB-11）。

**由此推出一条硬约束**：这个文件不是单一进程的私有文件 —— 它由**两个** systemd
服务账号共享读写（`ib-web` = 属主，`ib-worker` = 非属主，靠共同组 `ib`）。故其权限位
**必须保留 group 位**；任何把它收成 `0600` 的动作都会让 `ib-worker` 打不开台账。
**WAL 边车 `-wal` / `-shm` 同受此约束**（`-shm` 打开时**必须**读写），且它们**不是**
按 umask 创建、而是由 SQLite 复制库文件创建时的 mode —— 故只对齐主文件不够。
详情与生产复现见 `_harden_file_permissions` 的 docstring。
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any

from ib.context import utc_now_iso
from ib.core import (
    DependencyUnavailableError,
    LLM_KEY_MASK,
    LlmKeyRecord,
    LlmKeyStatus,
    StartupError,
)
from ib.ledger.schema import ensure_schema, missing_llm_key_columns

__all__ = [
    "SqliteLlmKeyStore",
    "MemoryLlmKeyStore",
    "build_llm_key_store",
]

#: 台账（= LLM Key 承载库）权限位：`0660`。
#:
#: **不可用 `0600`** —— 该文件由 `ib-web`（属主）与 `ib-worker`（**非属主**，靠共同组 `ib`）
#: **两个**服务账号共享读写。摘掉 group 位会让 `ib-worker` 启动即
#: `sqlite3.OperationalError: unable to open database file`，并在其单元 `Restart=always`
#: 下**无限重启**（DEFECT-R18-01，2026-10-07 生产事故）。
#: 详见 `SqliteLlmKeyStore._harden_file_permissions` 的 docstring 与 `checklists.txt` B22。
LEDGER_FILE_MODE = 0o660

#: WAL 边车后缀：台账开 WAL 后，SQLite 还会同时用到这两个同级文件。
#:
#: `-shm` 打开时**必须读写**，故其 mode 与主库文件**同等承重** —— 只 chmod 主文件不够。
#: 生产已实测（DEFECT-R18-01 复现）：主库 `0660`、`-wal` `0660`，而 `-shm` 卡在 `0600`，
#: `ib-worker` 依旧 `unable to open database file`。
LEDGER_SIDECAR_SUFFIXES = ("-wal", "-shm")


def _harden_targets(path: str) -> tuple[tuple[str, str], ...]:
    """返回 `_harden_file_permissions` 需逐一收紧的 `(路径, kind)`。

    `kind` 是结构化 WARN 的诊断字段（`db` / `wal` / `shm`）—— 日志白名单里**没有**
    `path`，故用 `kind` 区分失败的是哪一个，避免又出现「知道失败了但不知道失败在哪」。
    """
    return ((path, "db"), *((f"{path}{suffix}", suffix.lstrip("-")) for suffix in LEDGER_SIDECAR_SUFFIXES))


def _status_of(record: LlmKeyRecord | None) -> LlmKeyStatus:
    """由装配期记录派生**不含明文**的对外状态视图。"""
    if record is None:
        return LlmKeyStatus(configured=False, masked="", updated_at=None)
    return LlmKeyStatus(configured=True, masked=LLM_KEY_MASK, updated_at=record.updated_at)


class SqliteLlmKeyStore:
    """`LlmKeyStore` 的 SQLite 实现（同一 SQLite 台账的单行表；IFC-IB-371）。"""

    def __init__(self, path: str, *, busy_timeout_ms: int = 5000) -> None:
        self._path = path or ":memory:"
        self._busy_timeout_ms = busy_timeout_ms
        self._local = threading.local()
        self._connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()
        if self._path != ":memory:":
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._bootstrap()

    # --- 连接管理（与 config_audit / accounts 同构） --- #

    def _connect(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            uri = "file:ib_llm_key_mem?mode=memory&cache=shared"
            connection = sqlite3.connect(
                uri,
                uri=True,
                check_same_thread=False,
                isolation_level=None,
                timeout=self._busy_timeout_ms / 1000.0,
            )
        else:
            connection = sqlite3.connect(
                self._path,
                check_same_thread=False,
                isolation_level=None,
                timeout=self._busy_timeout_ms / 1000.0,
            )
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _conn(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            try:
                connection = self._connect()
            except sqlite3.Error as exc:
                raise DependencyUnavailableError(
                    f"LLM Key 存储连接失败（sqlite：{type(exc).__name__}）", dependency="ledger"
                ) from exc
            self._local.connection = connection
            with self._connections_lock:
                self._connections.append(connection)
        return connection

    def _bootstrap(self) -> None:
        connection = self._conn()
        try:
            ensure_schema(connection)  # 含 LLM_KEY_DDL_STATEMENTS（幂等）
        except sqlite3.Error as exc:
            raise DependencyUnavailableError(
                f"LLM Key 存储初始化失败（sqlite：{type(exc).__name__}）", dependency="ledger"
            ) from exc
        missing = missing_llm_key_columns(connection)
        if missing:
            tables = "；".join(f"{t}:{','.join(cols)}" for t, cols in missing.items())
            raise StartupError(
                f"LLM Key 表结构不完整（缺少列）：{tables}。"
                "请先执行 `python -m ibweb.bootstrap --ensure-schema`。"
            )
        self._harden_file_permissions()

    def _harden_file_permissions(self) -> None:
        """best-effort 收紧承载库**及其 WAL 边车**权限位至 `0660`（REQ-NFR-IB-20 / B22）。

        ## 为什么是 `0660` 而不是 `0600`（DEFECT-R18-01，2026-10-07 生产事故）

        本模块与台账指向**同一**文件，而该文件由**两个**服务账号共享：`ib-web`
        （属主，读写）与 `ib-worker`（**非属主**，靠共同组 `ib` 读写）。`0600` 把
        **group 位**一并摘掉，后果是 `ib-worker` 一启动就
        `sqlite3.OperationalError: unable to open database file`；又因其单元是
        `Restart=always`，表现为**无限重启**（`NRestarts` 单调爬升），而 `ib-web`
        与服务健康检查**全部正常**，故症状极具迷惑性。

        同源前车之鉴：`ib/blob/__init__.py:226-230` 已对「web 进程写、worker 进程读，
        二者分属不同 systemd 用户」留过注释并对齐 `0664`。

        故此处**只去掉 other 位、保留 group 位**：非 `ib` 账号读不到，两个服务账号
        仍共享。机密边界是**两道**：① 目录 `/var/lib/intelligentbase` 与
        `/var/lib/intelligentbase/ledger`（均 `0770 ib-web:ib`）—— 非 `ib` 账号根本
        无法进入；② 本 chmod（目录被误配宽松时的纵深防御）。

        ## 为什么必须连 WAL 边车一起 chmod（DEFECT-R18-01 生产复现，同日）

        台账开 WAL，SQLite 还会用到同级文件 `-wal` 与 `-shm`；**`-shm` 打开时必须
        读写**，故它的 mode 与主库文件**同等承重**。**只 chmod 主文件是不够的** ——
        生产实测：主库已是 `0660`、`-wal` 也是 `0660`，而 `-shm` 停在 `0600`，
        `ib-worker` 依旧报同一个 `unable to open database file`（新版代码已生效、
        主库已修好，故障却原样复现）。

        边车的 mode **不是**由部署机 umask 决定，而是由 SQLite **在创建时复制库文件
        当时的 mode**。这就制造了一个顺序陷阱：`sqlite3.connect()` 发生在 `_bootstrap`
        开头，**早于本方法**；若库文件那一刻还是 `0600`，SQLite 就把 `-shm` 建成
        `0600`，而本方法随后只修好了主文件 —— 边车被漏下，故障照旧。故本方法**必须**
        逐个覆盖 `-wal` / `-shm` 自身，不能指望「主文件对了边车就对」。

        边车**可能尚不存在**（`-wal` 常在首次写入后才出现）：那是**正常**情形，跳过
        即可 —— 它稍后创建时会复制库文件**彼时**的 mode，而主库文件已由本方法对齐。
        反过来说，正因为创建时机不确定，逐个覆盖边车才是唯一稳妥的做法。

        `os.chmod` 只对**属主**（或 root）生效 —— `ib-worker` 侧调用会 `EPERM`，被
        下方 `except OSError` 吸收，不影响其启动；但**不再静默**：失败会发一条结构化
        WARN（`error_code=ledger_chmod_failed:<异常类>`，`kind` 标出 db / wal / shm）。
        否则「收紧失败」与「收紧成功」在日志里无从区分 —— 这正是本次事故迟迟定不到
        位的直接原因。

        **属主对齐服务账号**由**用户**在部署期执行（本模块无法在不改变运行身份的前提下
        完成属主变更）；失败**不**阻断启动（权限的最终判据是部署检查清单 B22 的人工核对）。
        """
        if os.name == "nt" or self._path == ":memory:":
            return
        for target, kind in _harden_targets(self._path):
            try:
                os.chmod(target, LEDGER_FILE_MODE)
            except FileNotFoundError:
                continue  # 边车尚未创建：正常情形，见 docstring
            except OSError as exc:
                from ib.observability import get_logger  # noqa: PLC0415  (同 sqlite_repo 的局部导入)

                get_logger("ledger").warn(
                    "warned",
                    error_code=f"ledger_chmod_failed:{type(exc).__name__}",
                    kind=kind,
                )

    def close(self) -> None:
        with self._connections_lock:
            connections = list(self._connections)
            self._connections.clear()
        for connection in connections:
            try:
                connection.close()
            except sqlite3.Error:
                pass
        self._local = threading.local()

    # --- LlmKeyStore（恰好 3 方法） --- #

    def get(self) -> LlmKeyRecord | None:
        """取全局唯一 Key（**装配期唯一读点**；未配置返回 `None`）。"""
        row = self._conn().execute(
            "SELECT secret, updated_at FROM llm_key WHERE id = 1"
        ).fetchone()
        if row is None:
            return None
        return LlmKeyRecord(secret=str(row[0]), updated_at=str(row[1]))

    def set(self, secret: str) -> LlmKeyStatus:
        """写入 / 覆盖单行 Key（`ON CONFLICT(id) DO UPDATE`），返回**不含明文**的状态视图。"""
        now = utc_now_iso()
        self._conn().execute(
            "INSERT INTO llm_key (id, secret, updated_at) VALUES (1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET secret = excluded.secret, updated_at = excluded.updated_at",
            (secret, now),
        )
        return LlmKeyStatus(configured=True, masked=LLM_KEY_MASK, updated_at=now)

    def clear(self) -> None:
        """清空单行（回到 LLM 未配置态）。幂等。"""
        self._conn().execute("DELETE FROM llm_key WHERE id = 1")

    # --- 对外状态（非端口方法；端点 / 健康检查用） --- #

    def status(self) -> LlmKeyStatus:
        """派生**不含明文**的状态视图（`GET /api/llm-key` 与 `/healthz/deps` 共用）。"""
        return _status_of(self.get())


class MemoryLlmKeyStore:
    """`LlmKeyStore` 的内存实现（离线 / 测试替身，IFC-IB-371）。

    * **纯 stdlib**、进程内、线程安全（单锁）；
    * 语义与 `SqliteLlmKeyStore` **对齐**（同一套端口一致性自检）：单值全局唯一、
      `set` 覆盖、`clear` 幂等。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._record: LlmKeyRecord | None = None

    def get(self) -> LlmKeyRecord | None:
        with self._lock:
            return self._record

    def set(self, secret: str) -> LlmKeyStatus:
        with self._lock:
            self._record = LlmKeyRecord(secret=secret, updated_at=utc_now_iso())
            return _status_of(self._record)

    def clear(self) -> None:
        with self._lock:
            self._record = None

    def status(self) -> LlmKeyStatus:
        with self._lock:
            return _status_of(self._record)


def build_llm_key_store(cfg: Any, *, ledger_path: str) -> Any:
    """按配置构造 LLM Key 存储（组合根单点调用；IFC-IB-369）。

    后端键 = `IB_LLM_KEY_BACKEND`（`sqlite` 默认 / `memory`）。`sqlite` 后端构造失败
    **不静默降级**为内存实现 —— 凭据载体不可用必须 fail-closed。
    """
    from ib.core.ports import LlmKeyStore  # noqa: F401  (端口一致性自证)

    if getattr(cfg, "llm_key_backend", "sqlite") == "memory":
        return MemoryLlmKeyStore()
    return SqliteLlmKeyStore(ledger_path)
