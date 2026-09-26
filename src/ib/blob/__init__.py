"""
@module MOD-IB-12
@implements IFC-IB-131 put / 132 get / 133 delete / 134 exists
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author sub_agent_software_developer

原文件 BlobStore（module_design.md §3 MOD-IB-12 / ADR-05；OQ-IB-01 = CONFIRMED_ON）。

**内容寻址（sha256）** 是这里的核心不变量（§6.2 幂等键表）：
  * 同内容不重复占空间（重复上传只增加台账行，不增加磁盘占用）；
  * `sha256` 同时是**删除对账**的锚点（`BlobRef.sha256`）；
  * 重建（MOD-IB-14）依赖原始文件可重放——这正是 OQ-IB-01 选择「开启落盘」的原因
    （不落盘则切分参数变更后无法重建，只能要求用户重传）。

安全约束（**这是本模块最需要防守的边界**）：
  * 路径段一律经 `_safe_segment()` 白名单校验，杜绝 `../` 路径穿越（不可信输入来自
    上传文件的文件名/项目/知识库标识）；
  * 写入采用「临时文件 + `os.replace`」原子替换，避免半截文件被后续重建读到；
  * **功能关闭时显式失败**（`DisabledBlobStore` 抛 `DependencyUnavailableError` → 503），
    不静默返回成功（§7.4 BlobStore 行：fail-closed）。
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import tempfile
import threading
from typing import Any, BinaryIO

from ib.core import (
    BlobRef,
    DependencyUnavailableError,
    Scope,
    ScopeViolationError,
)

__all__ = [
    "FsBlobStore",
    "InMemoryBlobStore",
    "DisabledBlobStore",
    "build_blob_store",
    "kb_segment",
    "sha256_of",
    "safe_segment",
]

#: 路径段白名单：字母数字 + `.` `_` `-`。**刻意不含 `/` `\` `:`** —— 它们既是路径分隔符，
#: 也是 Windows 盘符/ADS 的组成部分。`..` 另行显式拒绝。
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

#: 单次读取的块大小（流式哈希，避免把大文件整体读入内存）。
_CHUNK_SIZE = 1024 * 1024


def safe_segment(value: str, *, field: str) -> str:
    """校验并返回可安全用作路径段的字符串。不合法即抛 `ScopeViolationError`。

    拒绝项：空串、`..`、含路径分隔符、含白名单外字符。
    """
    if not value or value in (".", "..") or not _SEGMENT_RE.match(value):
        raise ScopeViolationError(
            f"{field} 含非法字符，已拒绝用于构造存储路径（仅允许字母数字与 . _ -）"
        )
    return value


def sha256_of(data: bytes) -> str:
    """字节串的 sha256 十六进制摘要（`sha256_of` 与流式 `_sha256_stream` 结果必须一致）。"""
    return hashlib.sha256(data).hexdigest()


def kb_segment(kb_id: str | None) -> str:
    """知识库维度的**存储段名**（ADR-05 布局第 2 段）—— **唯一真源**（R4 / FND-GROUP-D-03）。

    规则只有一条：**空串 / `None` → `"default"`**。

    之所以把它收成函数、而不是在各处散写 `x or "default"`：项目级 scope（`kb_ids=None`）
    与台账里的「无 kb」（空串）是**同一个语义**，但历史上写路径、删路径、读路径
    （`blob_ref_for`）**各自手写**了这条规则。只要有一处写法不一致，就会出现
    「文件按真实 kb 落盘、删除却在 `default` 段查找」→ 删不到 → 原文件成孤儿
    （FND-GROUP-D-03 的根因）。把规则收敛到此一处，三处推导在结构上不可能再分叉。
    """
    return kb_id or "default"


class InMemoryBlobStore:
    """内存 BlobStore（离线替身）。

    `delete(scope, doc_id)` 的语义与 `FsBlobStore` 对齐：删除该 doc 下的**全部** blob，
    返回删除个数（同 doc 重复上传不同内容会产生多个 sha256 对象）。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key: (project_id, kb_id, doc_id, sha256, ext) -> bytes
        self._objects: dict[tuple[str, str, str, str, str], bytes] = {}
        self._refs: dict[str, tuple[str, str, str, str]] = {}  # rel_path -> key 前缀

    def put(self, scope: Scope, doc_id: str, data: BinaryIO, ext: str) -> BlobRef:
        payload = data.read()
        if isinstance(payload, str):  # pragma: no cover - 防御
            payload = payload.encode("utf-8")
        project_id = safe_segment(scope.project_id, field="project_id")
        kb_id = safe_segment(kb_segment(scope.kb_ids[0] if scope.kb_ids else None), field="kb_id")
        doc_id = safe_segment(doc_id, field="doc_id")
        ext = safe_segment((ext or "").lstrip("."), field="ext")
        digest = sha256_of(payload)
        rel_path = f"{project_id}/{kb_id}/{doc_id}/{digest}.{ext}"
        with self._lock:
            self._objects[(project_id, kb_id, doc_id, digest, ext)] = payload
            self._refs[rel_path] = (project_id, kb_id, doc_id, ext)
        return BlobRef(sha256=digest, rel_path=rel_path, size_bytes=len(payload))

    def get(self, blob_ref: BlobRef) -> bytes | None:
        with self._lock:
            key = self._key_of(blob_ref)
            return self._objects.get(key) if key is not None else None

    def delete(self, scope: Scope, doc_id: str) -> int:
        project_id = safe_segment(scope.project_id, field="project_id")
        kb_id = safe_segment(kb_segment(scope.kb_ids[0] if scope.kb_ids else None), field="kb_id")
        doc_id = safe_segment(doc_id, field="doc_id")
        with self._lock:
            doomed = [
                key for key in self._objects if key[0] == project_id and key[1] == kb_id and key[2] == doc_id
            ]
            for key in doomed:
                self._objects.pop(key, None)
            for rel_path in [p for p, prefix in self._refs.items() if prefix[:3] == (project_id, kb_id, doc_id)]:
                self._refs.pop(rel_path, None)
            return len(doomed)

    def exists(self, blob_ref: BlobRef) -> bool:
        with self._lock:
            key = self._key_of(blob_ref)
            return key in self._objects if key is not None else False

    def _key_of(self, blob_ref: BlobRef) -> tuple[str, str, str, str, str] | None:
        """由 `rel_path` 反查 key（`rel_path` 是 `put` 的产物，故结构可信）。"""
        parts = blob_ref.rel_path.split("/")
        if len(parts) != 4:
            return None
        project_id, kb_id, doc_id, filename = parts
        try:
            digest, _dot, ext = filename.rpartition(".")
        except ValueError:  # pragma: no cover
            return None
        if digest != blob_ref.sha256:
            # rel_path 与 sha256 不一致 = 引用被篡改或构造错误，拒答（fail-closed）
            return None
        return (project_id, kb_id, doc_id, blob_ref.sha256, ext)


class FsBlobStore:
    """文件系统 BlobStore（生产；ADR-05）。

    布局：`<blob_root>/<project_id>/<kb_id>/<doc_id>/<sha256>.<ext>`
      * 前两级（project / kb）使「按 scope 删除」退化为**删目录**，不会误伤其他项目；
      * `doc_id` 级目录让同一文档的不同版本内容并存，便于对账与回溯；
      * 文件名为内容摘要 —— 同一内容天然去重。

    写入为「临时文件 + `os.replace`」：`os.replace` 在同文件系统内是原子操作，
    因此**不存在被读取到半截文件的窗口**（重建会读这些文件，必须原子）。
    """

    def __init__(self, root: str) -> None:
        if not root:
            raise DependencyUnavailableError("BlobStore 根目录未配置", dependency="blob")
        self._root = os.path.abspath(root)
        os.makedirs(self._root, exist_ok=True)

    @property
    def root(self) -> str:
        return self._root

    def _doc_dir(self, scope: Scope, doc_id: str) -> str:
        project_id = safe_segment(scope.project_id, field="project_id")
        kb_id = safe_segment(kb_segment(scope.kb_ids[0] if scope.kb_ids else None), field="kb_id")
        doc_id = safe_segment(doc_id, field="doc_id")
        return os.path.join(self._root, project_id, kb_id, doc_id)

    def _abs(self, blob_ref: BlobRef) -> str:
        """`rel_path` -> 绝对路径，并断言结果**仍在 root 之内**（穿越防护的第二道）。"""
        candidate = os.path.abspath(os.path.join(self._root, *blob_ref.rel_path.split("/")))
        if candidate != self._root and not candidate.startswith(self._root + os.sep):
            raise ScopeViolationError("blob 路径越出存储根目录，已拒绝访问")
        return candidate

    def put(self, scope: Scope, doc_id: str, data: BinaryIO, ext: str) -> BlobRef:
        ext = safe_segment((ext or "").lstrip("."), field="ext")
        doc_dir = self._doc_dir(scope, doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        # 1) 流式落临时文件并同时算摘要（大文件不整体进内存）
        digest = hashlib.sha256()
        size = 0
        handle, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=doc_dir)
        try:
            with os.fdopen(handle, "wb") as sink:
                while True:
                    chunk = data.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    if isinstance(chunk, str):  # pragma: no cover - 防御
                        chunk = chunk.encode("utf-8")
                    digest.update(chunk)
                    size += len(chunk)
                    sink.write(chunk)
                sink.flush()
                os.fsync(sink.fileno())
            sha256 = digest.hexdigest()
            rel_path = "/".join(
                [
                    safe_segment(scope.project_id, field="project_id"),
                    safe_segment(
                        kb_segment(scope.kb_ids[0] if scope.kb_ids else None), field="kb_id"
                    ),
                    safe_segment(doc_id, field="doc_id"),
                    f"{sha256}.{ext}",
                ]
            )
            final_path = os.path.join(doc_dir, f"{sha256}.{ext}")
            if os.path.exists(final_path):
                # 内容寻址 + 幂等：同内容已在盘上，丢弃临时文件即可
                os.unlink(temp_path)
                size = os.path.getsize(final_path)
            else:
                os.replace(temp_path, final_path)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:  # pragma: no cover
                    pass
            raise
        return BlobRef(sha256=sha256, rel_path=rel_path, size_bytes=size)

    def get(self, blob_ref: BlobRef) -> bytes | None:
        path = self._abs(blob_ref)
        try:
            with open(path, "rb") as handle:
                return handle.read()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise DependencyUnavailableError(
                f"读取原文件失败（OSError：{type(exc).__name__}）", dependency="blob"
            ) from exc

    def delete(self, scope: Scope, doc_id: str) -> int:
        """删除该文档目录下的全部对象；返回删除的**文件个数**（目录不计）。"""
        doc_dir = self._doc_dir(scope, doc_id)
        if not os.path.isdir(doc_dir):
            return 0
        try:
            names = [n for n in os.listdir(doc_dir) if os.path.isfile(os.path.join(doc_dir, n))]
            count = len(names)
            shutil.rmtree(doc_dir)
            # 顺带清理空的 kb 目录（仅当为空，不递归删非空目录）
            parent = os.path.dirname(doc_dir)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
        except OSError as exc:
            raise DependencyUnavailableError(
                f"删除原文件失败（OSError：{type(exc).__name__}）", dependency="blob"
            ) from exc
        return count

    def exists(self, blob_ref: BlobRef) -> bool:
        return os.path.isfile(self._abs(blob_ref))

    def open_stream(self, blob_ref: BlobRef) -> BinaryIO | None:
        """以流方式打开（供 MOD-IB-05 解析大文件，避免整体读入内存）。"""
        path = self._abs(blob_ref)
        try:
            return open(path, "rb")
        except FileNotFoundError:
            return None


class DisabledBlobStore:
    """**显式关闭**的 BlobStore（`IB_BLOB_STORE_ENABLED=false`）。

    与「装配 `InMemoryBlobStore`」语义完全不同：
      * 内存替身 → 离线自测时功能**可用**（只是不持久）；
      * 本类 → 功能**被关闭**，任何写/读都抛 `DependencyUnavailableError`（→ HTTP 503），
        让「原文件存储不可用」在 API 层可见（§7.4 BlobStore 行要求明确报错）。
    """

    enabled = False

    def __init__(self, *, reason: str = "IB_BLOB_STORE_ENABLED=false") -> None:
        self._reason = reason
        self._warned = False

    def _fail(self) -> None:
        if not self._warned:
            from ib.observability import get_logger

            get_logger("blob").warn("failed", error_code="blob_disabled")
            self._warned = True
        raise DependencyUnavailableError("原文件存储功能已关闭", dependency="blob")

    def put(self, scope: Scope, doc_id: str, data: BinaryIO, ext: str) -> BlobRef:
        self._fail()
        raise AssertionError("unreachable")  # pragma: no cover

    def get(self, blob_ref: BlobRef) -> bytes | None:
        self._fail()
        raise AssertionError("unreachable")  # pragma: no cover

    def delete(self, scope: Scope, doc_id: str) -> int:
        self._fail()
        raise AssertionError("unreachable")  # pragma: no cover

    def exists(self, blob_ref: BlobRef) -> bool:
        return False


def build_blob_store(cfg: Any) -> Any:
    """按配置构造 BlobStore（组合根单点调用）。

    三态（互斥，不叠加）：
      * `IB_OFFLINE_MODE=1` → 内存替身（离线装配不落盘）；
      * `IB_BLOB_STORE_ENABLED=false` → **显式关闭**（fail-closed）；
      * 否则 → 文件系统实现。

    只认这两个开关：module_design §5 冻结了「不新增/不改名任何配置键」，
    因此**不引入** `IB_BLOB_BACKEND` 这类看似方便的新键 —— 一旦引入，就出现了
    「同一个 BlobStore 有两条互斥的开关路径」，而两条路径的优先级无法从文档判断。
    """
    if getattr(cfg, "offline_mode", False):
        return InMemoryBlobStore()
    if not cfg.blob.enabled:
        return DisabledBlobStore()
    return FsBlobStore(cfg.blob.root)


def put_bytes(store: Any, scope: Scope, doc_id: str, payload: bytes, ext: str) -> BlobRef:
    """便捷包装：把 `bytes` 当流交给 `put`（调用方无文件对象时使用）。"""
    return store.put(scope, doc_id, io.BytesIO(payload), ext)
