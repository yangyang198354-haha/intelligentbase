"""
@module MOD-IB-11
@implements IFC-IB-120 create_document / 121 get_document / 122 list_documents
            IFC-IB-123 set_status / 124 claim_pending / 125 renew_lease
            IFC-IB-126 reap_expired_leases / 127 mark_indexed / 128 mark_deleted
            IFC-IB-129 active_collection_version + activate_collection_version
            IFC-IB-130 assert_kb_in_project / 131 list_chunks + list_orphan_doc_ids
            （IFC-IB-131 组内扩展）upsert_chunks —— 见 deviation D-07
@depends MOD-IB-01, MOD-IB-02, MOD-IB-04
@author software-developer

台账（module_design.md §3 MOD-IB-11 / §6 / ADR-10）。

台账是「**可见性的唯一权威**」：谁属于哪个项目、文档是什么状态、哪一批向量应当存在，
一律以本模块为准。故所有方法**都带 `scope`**（除租约类方法 —— 它们是 worker 级、跨项目的
队列操作，返回的记录自带 `project_id`，调用方据此再构造 scope）。

三个不可让步的实现约束：
  1. **任何删除/更新都以 `(project_id[, kb_id], doc_id)` 限定** —— 绝不按名字或裸 id 命中（FM-3）；
  2. **状态机收敛在一处**：`_assert_transition()` 是唯一的合法性判定，散落的 if 会让状态图失真；
  3. **租约 = 条件 UPDATE**：认领/续租都必须能被并发安全地判定成败（ADR-10），
     不能用「先查后写」这种在并发下必然出错的写法。

`InMemoryLedgerRepository` 与 `SqliteLedgerRepository` **语义对齐**（状态机、租约、归属断言、
孤儿对账），故可互换用于离线单测（AC-IB-15-01）。
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Protocol, Sequence, runtime_checkable

from ib.context import iso_plus_seconds, utc_now_iso
from ib.core import (
    ChunkImageRecord,
    ChunkRecord,
    ConflictError,
    DependencyUnavailableError,
    DocStatus,
    DocumentRecord,
    KbRecord,
    NotFoundError,
    ProjectRecord,
    Scope,
    ScopeViolationError,
    StartupError,
)

__all__ = [
    "InMemoryLedgerRepository",
    "SqliteLedgerRepository",
    "RebuildJobStore",
    "RebuildJobRow",
    "build_ledger",
    "load_project_record",
    "assert_no_half_state",
    # R13（IFC-IB-313~315）：账户 / 会话存储
    "SqliteAccountStore",
    "MemoryAccountStore",
    "seed_default_admin",
    "build_account_store",
    "hash_password",
    "verify_password",
    # REV-16-4（IFC-IB-357/358）：配置审计存储
    "SqliteConfigAuditStore",
    "MemoryConfigAuditStore",
    "build_config_audit_store",
    # REV-18（IFC-IB-370/371）：项目注册表 / LLM Key 存储
    "SqliteProjectRegistryStore",
    "MemoryProjectRegistryStore",
    "build_project_registry_store",
    "SqliteLlmKeyStore",
    "MemoryLlmKeyStore",
    "build_llm_key_store",
]


# --------------------------------------------------------------------------- #
# 状态机（§6.1）—— 唯一合法性判定
# --------------------------------------------------------------------------- #

#: 允许的状态迁移（§6.1 表）。`indexed -> *` 只允许经重建重入（由 MOD-IB-14 显式置回 pending）。
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"parsing", "failed"}),
    "parsing": frozenset({"indexed", "failed", "pending"}),
    "indexed": frozenset({"pending"}),
    "failed": frozenset({"pending"}),
}


def _assert_transition(current: str, target: str, *, doc_id: str) -> None:
    """校验状态迁移合法性（§6.1）。相同状态视为幂等 no-op，放行。"""
    if current == target:
        return
    allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ConflictError(
            f"文档状态迁移非法：{current} -> {target}（doc_id 已省略以避免日志泄露；见 §6.1 状态机）"
        )
    del doc_id  # 仅用于可读性，本函数不输出任何标识（FM-8）


def assert_no_half_state(record: DocumentRecord) -> None:
    """不变量断言（§6.1）：`indexed` ⇒ 必须已记录 `indexed_collection_version` 且 `chunk_count >= 0`。

    在 `mark_indexed` 之后与读路径解析 collection 之前各调一次 —— 半成品状态如果存在，
    应当在**写入点**就炸掉，而不是等到检索时表现为「查不到」。
    """
    if record.status == "indexed" and not record.indexed_collection_version:
        raise DependencyUnavailableError(
            "台账不变量被破坏：文档状态为 indexed 但缺少 indexed_collection_version",
            dependency="ledger",
        )


#: 重建任务的**终态**：不可再被认领/推进（`RebuildState` 的取值域）。
TERMINAL_REBUILD_STATES: frozenset[str] = frozenset({"succeeded", "failed", "activated", "rolled_back"})


# --------------------------------------------------------------------------- #
# 重建任务存储（IFC-IB-151~155 的持久化基座；见 deviation D-07）
# --------------------------------------------------------------------------- #


@runtime_checkable
class RebuildJobStore(Protocol):
    """重建任务的持久化端口（**非** module_design 冻结 IFC 清单内的组内扩展）。

    为什么需要持久化而非内存字典：AC-IB-16 要求「断点续跑」，进程重启后必须能继续；
    且 `(project_id, target_version)` 需唯一以支持幂等重入（§6.2）。
    """

    def create_rebuild_job(
        self,
        *,
        project_id: str,
        from_version: str,
        to_version: str,
        target_collection: str,
        doc_count: int,
    ) -> "RebuildJobRow": ...

    def get_rebuild_job(self, job_id: str) -> "RebuildJobRow | None": ...

    def find_rebuild_job(self, project_id: str, to_version: str) -> "RebuildJobRow | None": ...

    def set_rebuild_state(
        self, job_id: str, state: str, *, lease_owner: str | None = None, lease_seconds: int | None = None
    ) -> None: ...

    def claim_rebuild_job(self, job_id: str, lease_owner: str, lease_seconds: int) -> bool: ...

    def list_rebuild_jobs(self, project_id: str) -> list["RebuildJobRow"]: ...


class RebuildJobRow:
    """重建任务行（轻量值对象；`types.py` 的 `RebuildJob` 只承载对外的两字段视图）。"""

    __slots__ = (
        "job_id",
        "project_id",
        "from_version",
        "to_version",
        "target_collection",
        "doc_count",
        "state",
        "lease_owner",
        "lease_expires_at",
        "created_at",
        "updated_at",
    )

    def __init__(
        self,
        *,
        job_id: str,
        project_id: str,
        from_version: str,
        to_version: str,
        target_collection: str,
        doc_count: int,
        state: str,
        lease_owner: str | None = None,
        lease_expires_at: str | None = None,
        created_at: str = "",
        updated_at: str = "",
    ) -> None:
        self.job_id = job_id
        self.project_id = project_id
        self.from_version = from_version
        self.to_version = to_version
        self.target_collection = target_collection
        self.doc_count = doc_count
        self.state = state
        self.lease_owner = lease_owner
        self.lease_expires_at = lease_expires_at
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:  # pragma: no cover - 调试友好
        return (
            f"RebuildJobRow(job_id={self.job_id!r}, project_id={self.project_id!r}, "
            f"from_version={self.from_version!r}, to_version={self.to_version!r}, state={self.state!r})"
        )


# --------------------------------------------------------------------------- #
# 内存实现（离线替身）
# --------------------------------------------------------------------------- #


class InMemoryLedgerRepository:
    """`LedgerRepository` + `RebuildJobStore` 的内存实现（AC-IB-15-01 的离线装配）。

    * **纯 stdlib**、进程内、线程安全（单锁）；
    * 语义与 SQLite 实现对齐（含状态机校验、租约到期回收、孤儿对账）；
    * **不模拟** SQLite 的锁竞争语义 —— 那是 `busy_timeout` 的职责，属真机验证项
      （IFC-IB-264），离线替身不应假装覆盖它。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._projects: dict[str, ProjectRecord] = {}
        self._kbs: dict[str, KbRecord] = {}
        self._documents: dict[str, DocumentRecord] = {}
        self._chunks: dict[str, list[ChunkRecord]] = {}
        #: 页面图关联行（R2 / M-02）：按 `doc_id` 分桶，先删后写（幂等，与 chunks 同构）。
        self._chunk_images: dict[str, list[ChunkImageRecord]] = {}
        self._jobs: dict[str, RebuildJobRow] = {}

    # --- 播种（组合根 / 自测用；非端口方法） --- #

    def upsert_project(self, project: ProjectRecord) -> None:
        with self._lock:
            self._projects[project.project_id] = project

    def get_project(self, project_id: str) -> ProjectRecord | None:
        with self._lock:
            return self._projects.get(project_id)

    def upsert_kb(self, kb: KbRecord) -> None:
        with self._lock:
            if kb.project_id not in self._projects:
                raise ScopeViolationError("知识库所属项目未登记")
            self._kbs[kb.kb_id] = kb

    def list_kbs(self, project_id: str) -> list[KbRecord]:
        with self._lock:
            return [kb for kb in self._kbs.values() if kb.project_id == project_id]

    # --- 作用域判定 --- #

    def _assert_kb(self, project_id: str, kb_id: str) -> None:
        kb = self._kbs.get(kb_id)
        if kb is None or kb.project_id != project_id:
            raise ScopeViolationError("知识库不属于该项目（归属断言失败）")

    def assert_kb_in_project(self, project_id: str, kb_id: str) -> None:
        with self._lock:
            self._assert_kb(project_id, kb_id)

    def _in_scope(self, record: DocumentRecord, scope: Scope) -> bool:
        if record.project_id != scope.project_id:
            return False
        if scope.kb_ids is not None and record.kb_id not in scope.kb_ids:
            return False
        return True

    def _require(self, scope: Scope, doc_id: str) -> DocumentRecord:
        record = self._documents.get(doc_id)
        if record is None or not self._in_scope(record, scope):
            raise NotFoundError("文档不存在或不在当前作用域内")
        return record

    # --- 文档 CRUD --- #

    def create_document(
        self,
        scope: Scope,
        doc_name: str,
        ext: str,
        size_bytes: int,
        content_sha256: str,
        blob_ref: str | None,
    ) -> DocumentRecord:
        with self._lock:
            kb_id = scope.kb_ids[0] if scope.kb_ids else ""
            self._assert_kb(scope.project_id, kb_id)
            now = utc_now_iso()
            record = DocumentRecord(
                doc_id=uuid.uuid4().hex,
                project_id=scope.project_id,
                kb_id=kb_id,
                doc_name=doc_name,
                ext=ext,
                size_bytes=size_bytes,
                content_sha256=content_sha256,
                blob_ref=blob_ref,
                status="pending",
                error_code=None,
                chunk_count=0,
                indexed_collection_version=None,
                target_collection_version=None,
                lease_owner=None,
                lease_expires_at=None,
                created_at=now,
                updated_at=now,
            )
            self._documents[record.doc_id] = record
            return record

    def get_document(self, scope: Scope, doc_id: str) -> DocumentRecord | None:
        with self._lock:
            record = self._documents.get(doc_id)
            if record is None or not self._in_scope(record, scope):
                return None
            return record

    def list_documents(
        self, scope: Scope, *, page: int, page_size: int, status: DocStatus | None
    ) -> tuple[list[DocumentRecord], int]:
        with self._lock:
            items = [
                record
                for record in self._documents.values()
                if self._in_scope(record, scope) and (status is None or record.status == status)
            ]
            items.sort(key=lambda item: (item.created_at, item.doc_id), reverse=True)
            total = len(items)
            start = max(0, (max(1, page) - 1) * max(1, page_size))
            return items[start : start + max(1, page_size)], total

    def set_status(
        self, scope: Scope, doc_id: str, status: DocStatus, *, error_code: str | None
    ) -> None:
        with self._lock:
            record = self._require(scope, doc_id)
            target = str(status)
            _assert_transition(record.status, target, doc_id=doc_id)
            # 离开 `parsing` 即释放租约：否则「failed 的文档仍持有租约」会挡住后续重试。
            holds_lease = target == "parsing"
            self._documents[doc_id] = _replace(
                record,
                status=target,
                error_code=error_code,
                updated_at=utc_now_iso(),
                lease_owner=record.lease_owner if holds_lease else None,
                lease_expires_at=record.lease_expires_at if holds_lease else None,
            )

    def mark_indexed(
        self, scope: Scope, doc_id: str, collection_version: str, chunk_count: int
    ) -> None:
        with self._lock:
            record = self._require(scope, doc_id)
            _assert_transition(record.status, "indexed", doc_id=doc_id)
            updated = _replace(
                record,
                status="indexed",
                error_code=None,
                chunk_count=chunk_count,
                indexed_collection_version=collection_version,
                target_collection_version=None,
                lease_owner=None,
                lease_expires_at=None,
                updated_at=utc_now_iso(),
            )
            assert_no_half_state(updated)
            self._documents[doc_id] = updated

    def mark_deleted(self, scope: Scope, doc_id: str) -> None:
        with self._lock:
            self._require(scope, doc_id)
            self._documents.pop(doc_id, None)
            self._chunks.pop(doc_id, None)
            # R2（IFC-IB-281 的级联删除不变式）：关联行随文档一并清除。
            # SQLite 侧由 `ON DELETE CASCADE` 完成；内存替身须显式对齐，
            # 否则「删除后仍能取到图」会在离线自测与生产之间产生语义分叉。
            self._chunk_images.pop(doc_id, None)

    # --- 租约（ADR-10） --- #

    def claim_pending(self, lease_owner: str, lease_seconds: int, limit: int) -> list[DocumentRecord]:
        with self._lock:
            now = utc_now_iso()
            candidates = [
                record
                for record in self._documents.values()
                if record.status == "pending"
                and (record.lease_expires_at is None or record.lease_expires_at < now)
            ]
            candidates.sort(key=lambda item: (item.created_at, item.doc_id))
            claimed: list[DocumentRecord] = []
            expires = iso_plus_seconds(lease_seconds)
            for record in candidates[: max(0, limit)]:
                updated = _replace(
                    record,
                    status="parsing",
                    lease_owner=lease_owner,
                    lease_expires_at=expires,
                    updated_at=now,
                )
                self._documents[record.doc_id] = updated
                claimed.append(updated)
            return claimed

    def renew_lease(self, doc_id: str, lease_owner: str, lease_seconds: int) -> bool:
        with self._lock:
            record = self._documents.get(doc_id)
            if record is None or record.lease_owner != lease_owner:
                return False
            self._documents[doc_id] = _replace(
                record, lease_expires_at=iso_plus_seconds(lease_seconds), updated_at=utc_now_iso()
            )
            return True

    def reap_expired_leases(self, now: str) -> int:
        with self._lock:
            reaped = 0
            for doc_id, record in list(self._documents.items()):
                if (
                    record.status == "parsing"
                    and record.lease_expires_at is not None
                    and record.lease_expires_at < now
                ):
                    self._documents[doc_id] = _replace(
                        record,
                        status="pending",
                        lease_owner=None,
                        lease_expires_at=None,
                        updated_at=utc_now_iso(),
                    )
                    reaped += 1
            for job_id, job in list(self._jobs.items()):
                if (
                    job.state == "running"
                    and job.lease_expires_at is not None
                    and job.lease_expires_at < now
                ):
                    job.state = "planned"
                    job.lease_owner = None
                    job.lease_expires_at = None
                    job.updated_at = utc_now_iso()
                    reaped += 1
            return reaped

    # --- collection 版本（ADR-05 单值切换） --- #

    def active_collection_version(self, project_id: str) -> str:
        with self._lock:
            project = self._projects.get(project_id)
            if project is None:
                raise StartupError("项目未登记（请检查项目配置）")
            return project.active_collection_version

    def activate_collection_version(self, project_id: str, version: str) -> None:
        with self._lock:
            project = self._projects.get(project_id)
            if project is None:
                raise StartupError("项目未登记（请检查项目配置）")
            self._projects[project_id] = _replace(project, active_collection_version=version)

    # --- 块元数据 --- #

    def upsert_chunks(self, scope: Scope, doc_id: str, chunks: Sequence[ChunkRecord]) -> int:
        """写入块元数据（IFC-IB-131 组内扩展，见 deviation D-07）。

        先删后写（同 `doc_id`）：重跑不产生重复行 —— 与向量侧的 delete-then-write 同构。
        """
        with self._lock:
            self._require(scope, doc_id)
            self._chunks[doc_id] = list(chunks)
            return len(chunks)

    def list_chunks(self, scope: Scope, doc_id: str) -> list[ChunkRecord]:
        with self._lock:
            record = self._documents.get(doc_id)
            if record is None or not self._in_scope(record, scope):
                return []
            return sorted(self._chunks.get(doc_id, []), key=lambda item: item.chunk_index)

    def list_orphan_doc_ids(self, project_id: str, existing: list[str]) -> list[str]:
        """台账存在但向量侧不存在的文档（删除重放对账；IFC-IB-131）。"""
        with self._lock:
            known = set(existing)
            return sorted(
                record.doc_id
                for record in self._documents.values()
                if record.project_id == project_id and record.doc_id not in known
            )

    # --- 页面图关联（R2 / M-02：IFC-IB-278 / IFC-IB-283）--- #

    def upsert_chunk_images(
        self, scope: Scope, doc_id: str, records: Sequence[ChunkImageRecord]
    ) -> int:
        """幂等写入页面图关联行（先删后写，同 `doc_id`）—— 语义与 `upsert_chunks` 同构。"""
        with self._lock:
            self._require(scope, doc_id)
            self._chunk_images[doc_id] = list(records)
            return len(records)

    def list_chunk_images(self, scope: Scope, doc_id: str) -> list[ChunkImageRecord]:
        with self._lock:
            record = self._documents.get(doc_id)
            if record is None or not self._in_scope(record, scope):
                return []
            return sorted(
                self._chunk_images.get(doc_id, []),
                key=lambda item: (item.page_or_section, item.image_id),
            )

    def get_chunk_image(
        self, scope: Scope, doc_id: str, image_id: str
    ) -> ChunkImageRecord | None:
        with self._lock:
            record = self._documents.get(doc_id)
            if record is None or not self._in_scope(record, scope):
                return None
            for row in self._chunk_images.get(doc_id, []):
                if row.image_id == image_id:
                    return row
            return None

    # --- 重建任务 --- #

    def create_rebuild_job(
        self,
        *,
        project_id: str,
        from_version: str,
        to_version: str,
        target_collection: str,
        doc_count: int,
    ) -> RebuildJobRow:
        with self._lock:
            existing = self.find_rebuild_job(project_id, to_version)
            if existing is not None:
                return existing
            now = utc_now_iso()
            job = RebuildJobRow(
                job_id=uuid.uuid4().hex,
                project_id=project_id,
                from_version=from_version,
                to_version=to_version,
                target_collection=target_collection,
                doc_count=doc_count,
                state="planned",
                created_at=now,
                updated_at=now,
            )
            self._jobs[job.job_id] = job
            return job

    def get_rebuild_job(self, job_id: str) -> RebuildJobRow | None:
        with self._lock:
            return self._jobs.get(job_id)

    def find_rebuild_job(self, project_id: str, to_version: str) -> RebuildJobRow | None:
        with self._lock:
            for job in self._jobs.values():
                if job.project_id == project_id and job.to_version == to_version:
                    return job
            return None

    def set_rebuild_state(
        self,
        job_id: str,
        state: str,
        *,
        lease_owner: str | None = None,
        lease_seconds: int | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise NotFoundError("重建任务不存在")
            job.state = state
            job.updated_at = utc_now_iso()
            if lease_owner is not None:
                job.lease_owner = lease_owner
            job.lease_expires_at = (
                iso_plus_seconds(lease_seconds) if lease_seconds is not None else None
            )

    def claim_rebuild_job(self, job_id: str, lease_owner: str, lease_seconds: int) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            if job.state in TERMINAL_REBUILD_STATES:
                return False
            job.state = "running"
            job.lease_owner = lease_owner
            job.lease_expires_at = iso_plus_seconds(lease_seconds)
            job.updated_at = utc_now_iso()
            return True

    def list_rebuild_jobs(self, project_id: str) -> list[RebuildJobRow]:
        with self._lock:
            return [job for job in self._jobs.values() if job.project_id == project_id]

    def reset_documents_for_rebuild(self, project_id: str, to_version: str) -> int:
        """重建启动：把该项目下 `indexed`/`failed` 文档重置回 `pending`（D-4b，与 SQLite 语义对齐）。"""
        with self._lock:
            reset = 0
            for doc_id, record in list(self._documents.items()):
                if record.project_id == project_id and record.status in ("indexed", "failed"):
                    self._documents[doc_id] = _replace(
                        record,
                        status="pending",
                        error_code=None,
                        target_collection_version=to_version,
                        lease_owner=None,
                        lease_expires_at=None,
                        updated_at=utc_now_iso(),
                    )
                    reset += 1
            return reset


def _replace(record: Any, **changes: Any) -> Any:
    """`dataclasses.replace` 的薄封装（集中一处，便于将来切到自定义值对象）。"""
    from dataclasses import replace

    return replace(record, **changes)


# --------------------------------------------------------------------------- #
# 项目记录装配（配置声明 + 台账持久值的合并点）
# --------------------------------------------------------------------------- #


def load_project_record(ledger: Any, cfg: Any, project_id: str) -> ProjectRecord:
    """构造 `ProjectRecord`：**元数据来自配置，active 版本来自台账**（ADR-05）。

    拆分的理由：`active_collection_version` 是**运行期可变**的（重建会改），
    其余字段（名称/维度/模型）是**部署期固定**的。把可变的放进台账、固定的放进配置，
    就避免了「重建时去改配置文件」这种危险做法。
    """
    project_cfg = cfg.project(project_id) if hasattr(cfg, "project") else cfg.projects[project_id]
    version = ledger.active_collection_version(project_id)
    return ProjectRecord(
        project_id=project_id,
        name=getattr(project_cfg, "name", project_id),
        active_collection_version=version,
        embedding_model_id=cfg.embedding.model_id,
        dim=cfg.embedding.dim,
        created_at=getattr(project_cfg, "created_at", "") or utc_now_iso(),
    )


def build_ledger(cfg: Any) -> Any:
    """按配置构造台账（组合根单点调用）。

    `sqlite` 后端构造失败时**不静默降级**为内存实现 —— 台账不可用必须 fail-closed
    （§7.4：上传/删除/列表返回 503），而不是悄悄换成「重启即丢」的内存台账。
    """
    if getattr(cfg, "ledger_backend", "sqlite") == "memory":
        return InMemoryLedgerRepository()
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    return SqliteLedgerRepository(cfg.ledger_path)


def __getattr__(name: str) -> Any:
    """惰性导出 `SqliteLedgerRepository`（PEP 562）。

    为什么不用顶层 import：`sqlite_repo` 反向 import 本模块的 `RebuildJobRow` /
    `_assert_transition` / `assert_no_half_state`，顶层互导会在「先导入 sqlite_repo」
    的路径上命中**部分初始化的模块**。惰性属性访问消除该导入顺序依赖。

    R13：账户 / 会话存储（`ib.ledger.accounts`）同样惰性导出 —— 其 `bcrypt` 依赖为
    **可选**（缺失时只在真正调用哈希时给可读错误），顶层导入会把「缺 bcrypt」提前
    变成「import ib.ledger 就炸」。

    REV-16-4：配置审计存储（`ib.ledger.config_audit`）同样惰性导出，与账户存储保持
    一致的导入面节奏（审计存储与台账共用同一 SQLite 文件，无独立可选依赖）。
    """
    if name == "SqliteLedgerRepository":
        from ib.ledger.sqlite_repo import SqliteLedgerRepository as _impl

        return _impl
    if name in {
        "SqliteAccountStore",
        "MemoryAccountStore",
        "seed_default_admin",
        "build_account_store",
        "hash_password",
        "verify_password",
    }:
        from ib.ledger import accounts as _accounts

        return getattr(_accounts, name)
    if name in {
        "SqliteConfigAuditStore",
        "MemoryConfigAuditStore",
        "build_config_audit_store",
    }:
        from ib.ledger import config_audit as _config_audit

        return getattr(_config_audit, name)
    if name in {
        "SqliteProjectRegistryStore",
        "MemoryProjectRegistryStore",
        "build_project_registry_store",
    }:
        from ib.ledger import projects as _projects

        return getattr(_projects, name)
    if name in {
        "SqliteLlmKeyStore",
        "MemoryLlmKeyStore",
        "build_llm_key_store",
    }:
        from ib.ledger import llm_key as _llm_key

        return getattr(_llm_key, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
