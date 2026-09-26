"""
@module MOD-IB-13
@implements IFC-IB-141 validate_upload / 142 submit_upload / 143 process_pending
            IFC-IB-144 delete_document / 145 retry_document
            IFC-IB-277 bind_page_images / 278 persist_page_images / 279 ChunkImageRecord 持久化
            IFC-IB-280 process_pending R2 步骤扩展（七步 → 九步）
            IFC-IB-281 delete_document 零改动不变式（关联行按 scope 级联删除）
@depends MOD-IB-01, MOD-IB-02, MOD-IB-03, MOD-IB-04, MOD-IB-05, MOD-IB-07, MOD-IB-09, MOD-IB-10, MOD-IB-11, MOD-IB-12
@author sub_agent_software_developer

文档生命周期（module_design.md §3 MOD-IB-13 / §6 / ADR-07）。

管线：`校验 → 落盘 → 解析 → 切分 → 向量化 → 写库 → 置位`（AC-IB-01-02/03/04）。
R2 之后为**九步**：`… → 切分 → ①绑定页面图 → 向量化 → 写库 → ②持久化页面图 → 块元数据 → 置位`
（IFC-IB-280；两个新步骤**不改变**既有失败粒度）。

**写序是正确性的核心**（ADR-07）：向量 → 台账置位。若先置位后写向量，
则存在「台账说 indexed 但检索不到」的窗口；反过来（先写向量、后置位）最坏情况是
「向量在、台账仍是 parsing」，由租约超时回收后重跑覆盖（幂等键保证不产生重复）。
R2 的页面图关联行亦遵循同一写序：**向量写成功之后、置 `indexed` 之前**落关联，
使「`indexed` ⇒ 关联已就绪」成为不变式（IFC-IB-278）。

**幂等**（§6.2）：写前 `delete_by_doc`（delete-then-write）+ 点 id = `doc_id#chunk_index`，
因此重跑/重试/重建都安全。页面图关联行同理：幂等键 `(project_id, kb_id, doc_id,
page_or_section, image_id)`，重跑覆盖同一行（IFC-IB-279）。

**失败粒度**（§6.4）：文档级失败 → `failed` + `error_code`，不阻塞其他文档；
页级失败（OCR/渲染）由 MOD-IB-05 记 `warnings`，文档仍可 `indexed`。
R2 的两个新步骤同样**不细化**失败粒度（仍只有「文档级失败」与「页级跳过」两档）。

**重试次数上限靠构造满足**：本管线**没有自动重试**（只有人工重试 IFC-IB-145 与租约超时回收，
后者只回收 `parsing` 态），因此不存在无限重试；失败即终态 `failed`。
"""

from __future__ import annotations

import hashlib
import io
from typing import Any, BinaryIO, Callable, Sequence

from ib.blob import kb_segment
from ib.context import utc_now_iso
from ib.core import (
    BlobRef,
    ChunkImageRecord,
    ChunkRecord,
    ConflictError,
    DependencyUnavailableError,
    DocStatus,
    DocumentRecord,
    DeleteReport,
    NotFoundError,
    PageImageBinding,
    PageImageRef,
    ParsedChunk,
    ParsedDocument,
    PointPayload,
    ProcessReport,
    ProjectRecord,
    RequestContext,
    Scope,
    ValidationError,
    ValidatedUpload,
    VectorPoint,
)
from ib.observability import Timer, get_logger, log_event
from ib.vectorstore import point_id_for

__all__ = [
    "DocumentLifecycle",
    "ERROR_CODES",
    "MAX_UPLOAD_BYTES",
    "MAGIC_HEAD_BYTES",
    "blob_ref_for",
    "bind_page_images",
]

#: 上传大小上限（默认 50MB）。体积上限是**显式配置项**而非魔法数：太大则解析/向量化
#: 在单请求/单任务里不可控，太小则业务受限。
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

#: 魔数校验需要的头部字节数（够 `%PDF-` 与 `PK\x03\x04` 判定，也够一段文本编码探测）。
MAGIC_HEAD_BYTES = 4096

#: 冷路径默认参数（可被组合根经配置覆盖）。
COLD_TIMEOUT_S = 120.0
COLD_MAX_RETRIES = 3
COLD_BATCH_SIZE = 16

#: 任务租约时长（秒）。取 300s：远大于单文档处理时长，又不会让崩溃任务长期占位。
LEASE_SECONDS = 300

#: 失败原因码（**只记码，不记内容**，FM-8）。使用者可据此定位到具体阶段。
ERROR_CODES: dict[str, str] = {
    "validate": "E_VALIDATE",
    "blob_missing": "E_BLOB_MISSING",
    "blob_unavailable": "E_BLOB_UNAVAILABLE",
    "parse": "E_PARSE",
    "parse_unsupported": "E_PARSE_UNSUPPORTED",
    "chunk": "E_CHUNK",
    "embed": "E_EMBED",
    "vectorstore": "E_VECTORSTORE",
    "ledger": "E_LEDGER",
    "deleted_concurrently": "E_DELETED_CONCURRENTLY",
    "unknown": "E_UNKNOWN",
}


def blob_ref_for(record: DocumentRecord) -> BlobRef | None:
    """由台账记录**推导**原文件引用（纯函数）。

    为什么是「推导」而不是「读取台账里的 `blob_ref` 字段」：冻结的台账端口（IFC-IB-120~131）
    没有任何「更新 blob_ref」的契约，而 `doc_id` 在入库时后才由台账生成 ——
    若把路径存进台账，就会出现「先建行后落盘」却无处回写的死结。
    路径本身是 `(project_id, kb_id, doc_id, sha256, ext)` 的**纯函数**，故推导即可，
    且推导比存储更不易漂移（少一份需要同步的状态）。

    `content_sha256` 为空表示该行未经原文件持久化（deviation D-08 的 `data=None` 路径）。

    **R4 / FND-GROUP-D-03**：kb 段经 `ib.blob.kb_segment` 推导（**不再就地手写
    `record.kb_id or "default"`**）。该函数是写路径（`FsBlobStore` / `InMemoryBlobStore`）
    与本函数**共用**的单一真源 —— 三者此前各写一份同样的「空 → default」规则，
    任一处写错都会让「读/删找不到写时落盘的段」，正是孤儿根因。
    """
    if not record.content_sha256:
        return None
    return BlobRef(
        sha256=record.content_sha256,
        rel_path="/".join(
            [
                record.project_id,
                kb_segment(record.kb_id),
                record.doc_id,
                f"{record.content_sha256}.{record.ext}",
            ]
        ),
        size_bytes=record.size_bytes,
    )


# --------------------------------------------------------------------------- #
# R2（M-02 / IFC-IB-277）：页面图 ↔ 文块绑定 —— **纯函数、无 IO**
# --------------------------------------------------------------------------- #

#: `ParsedChunk.source_kind` -> `PageImageRef.source_kind` 的映射。
#:
#: 两张表不能直接复用同一个取值：`ParsedChunk` 说的是「这一块**是怎么被解析出来的**」
#: （`image_ocr` = 内嵌图 OCR / `page_scan` = 整页栅格化 OCR），而 `PageImageRef` 说的是
#: 「这张**图**是什么」。前者是解析路径，后者是资产种类 —— 混用会让下游无法区分
#: 「这页的图是内嵌的，还是整页扫出来的」（二者的检索/回显代价完全不同）。
_IMAGE_KIND_BY_SOURCE = {"image_ocr": "embedded_image", "page_scan": "page_scan"}


def image_id_for(doc_id: str, page_or_section: str, locator: str) -> str:
    """由 `(doc_id, page_or_section, locator)` **确定性**派生 `image_id`。

    为什么确定性：`image_id` 是幂等键的一部分（IFC-IB-279）。若用自增序号或随机 id，
    重跑（重试 / 重建）会产生**新的** image_id，旧行不被覆盖 → 图片列表随重跑膨胀，
    且前端缓存全部失效。确定性派生让「同一张图 = 同一个 id」成为可推导的事实。
    """
    raw = f"{doc_id}\x1f{page_or_section}\x1f{locator}".encode("utf-8")
    return "img-" + hashlib.blake2b(raw, digest_size=8).hexdigest()


def bind_page_images(parsed: ParsedDocument, *, doc_id: str) -> list[PageImageBinding]:
    """[IFC-IB-277] 按 `page_or_section` 把页面图聚合为绑定（**纯函数、无 IO**）。

    机制（M-02 的根因修复）：解析产出的**图文块共享 `page_or_section` 键**，
    因此「命中某页文字块 → 该页有哪些图」是一次按 key 的查表，而不是检索期的启发式猜测。
    本函数把该 key 关系**在入库期固化**为若干 `PageImageBinding`。

    `project_id` / `kb_id` 在此**留空**：本函数没有 scope（纯函数无 IO 也就没有项目上下文）。
    身份由 `persist_page_images(scope, …)` 用**当前 scope** 补全 —— 这样也顺带保证了
    「关联行的项目/知识库归属只能来自 scope」，不存在从解析内容里伪造归属的可能。

    `blob_ref` 一律为 `None`：见类文档「页面图字节」一节 —— R1 解析器在内存里取出
    页面图供 OCR 后即弃，未落 BlobStore，故此刻**没有**可引用的字节（诚实登记，
    不伪造路径）。字节持久化是已登记的 P1 残余（见 `docs/code_review_report.md`）。

    排序：按 `(page_or_section, image_id)` 升序 —— 与台账 `ORDER BY page_or_section, image_id`
    一致，故「服务端给出的顺序」在整条链路上唯一（IFC-IB-284 要求前端**不得重排**）。
    """
    buckets: dict[str, list[PageImageRef]] = {}
    for chunk in parsed.chunks:
        ref = _page_image_ref_of(chunk, doc_id=doc_id)
        if ref is None:
            continue
        buckets.setdefault(ref.page_or_section, []).append(ref)
    bindings: list[PageImageBinding] = []
    for page_or_section in sorted(buckets):
        images = tuple(sorted(buckets[page_or_section], key=lambda item: item.image_id))
        bindings.append(
            PageImageBinding(
                project_id="",
                kb_id="",
                doc_id=doc_id,
                page_or_section=page_or_section,
                images=images,
            )
        )
    return bindings


def _page_image_ref_of(chunk: ParsedChunk, *, doc_id: str) -> PageImageRef | None:
    """从解析块提取页面图引用；非图片块返回 `None`（**不臆造**图）。"""
    if not chunk.image_ref:
        return None
    kind = _IMAGE_KIND_BY_SOURCE.get(chunk.source_kind)
    if kind is None:
        # 带 `image_ref` 却是别的 source_kind：契约上不该发生，容忍而不猜测
        return None
    return PageImageRef(
        image_id=image_id_for(doc_id, chunk.page_or_section, chunk.locator),
        page_or_section=chunk.page_or_section,
        source_kind=kind,  # type: ignore[arg-type] - 取值受 `_IMAGE_KIND_BY_SOURCE` 约束
        locator=chunk.locator,
        blob_ref=None,
        caption=None,
    )


class DocumentLifecycle:
    """入库管线编排（IFC-IB-141~145）。

    依赖全部经构造期注入（组合根是唯一装配点），本类**不 import 任何具体适配器**。
    """

    def __init__(
        self,
        *,
        ledger: Any,
        blobs: Any,
        parsers: Any,
        chunker: Any,
        embedder: Any,
        vectors: Any,
        resolver: Any,
        ocr: Any,
        renderer: Any,
        chunking_spec: Any,
        project_provider: Callable[[str], ProjectRecord],
        max_upload_bytes: int = MAX_UPLOAD_BYTES,
        cold_timeout_s: float = COLD_TIMEOUT_S,
        cold_max_retries: int = COLD_MAX_RETRIES,
        cold_batch_size: int = COLD_BATCH_SIZE,
        lease_seconds: int = LEASE_SECONDS,
    ) -> None:
        self._ledger = ledger
        self._blobs = blobs
        self._parsers = parsers
        self._chunker = chunker
        self._embedder = embedder
        self._vectors = vectors
        self._resolver = resolver
        self._ocr = ocr
        self._renderer = renderer
        self._chunking_spec = chunking_spec
        self._project_provider = project_provider
        self._max_upload_bytes = max_upload_bytes
        self._cold_timeout_s = cold_timeout_s
        self._cold_max_retries = cold_max_retries
        self._cold_batch_size = cold_batch_size
        self._lease_seconds = lease_seconds

    # ================================================================== #
    # IFC-IB-141 上传三重校验
    # ================================================================== #

    def validate_upload(
        self, filename: str, size_bytes: int, head: bytes
    ) -> ValidatedUpload:
        """扩展名 → 大小 → **魔数签名**（AC-IB-01-02/03/04）。

        顺序刻意从「便宜且确定」到「需要读内容」：扩展名（字符串）→ 大小（整数）→ 魔数（字节）。
        任何一步失败都抛 `ValidationError`（→ HTTP 400），**不返回半校验对象**。
        """
        from ib.parsing import SUPPORTED_EXTS, ext_of, sniff_magic

        ext = ext_of(filename or "")
        if not ext:
            raise ValidationError("文件名缺少扩展名，无法判定格式")
        if ext not in SUPPORTED_EXTS:
            # 只回显扩展名与支持列表（均为键名级信息，不含用户内容）
            raise ValidationError(
                f"不支持的文件格式 .{ext}（支持：{', '.join('.' + e for e in SUPPORTED_EXTS)}）"
            )
        if size_bytes is None or int(size_bytes) <= 0:
            raise ValidationError("文件为空")
        if int(size_bytes) > self._max_upload_bytes:
            raise ValidationError(
                f"文件超出大小上限（{self._max_upload_bytes // (1024 * 1024)}MB）"
            )
        detected = sniff_magic(head or b"", ext)
        if detected is None:
            # 关键防线：扩展名与真实内容不符（改名攻击 / 伪装上传）
            raise ValidationError("文件内容与扩展名不符（魔数签名校验失败）")
        return ValidatedUpload(
            filename=filename,
            ext=ext,
            size_bytes=int(size_bytes),
            detected_mime=detected,
        )

    # ================================================================== #
    # IFC-IB-142 登记上传
    # ================================================================== #

    def submit_upload(
        self,
        ctx: RequestContext,
        validated: ValidatedUpload,
        kb_id: str,
        *,
        data: BinaryIO | None = None,
    ) -> DocumentRecord:
        """登记上传：**落盘 + 建台账行（pending）**，不在请求内做重活（IFC-IB-142）。

        `data` 是 `IFC-IB-142` 之外的**增量关键字参数**（deviation D-08）：冻结签名没有
        原始字节通道，而 §7.4 要求 BlobStore 故障在上传请求内 fail-closed（503），
        故原始流必须在此处落地。关键字参数不改变既有位置参数语义 —— 向后兼容的超集。

        执行顺序与补偿（§7.4「不产生半成品状态」）：
          1. 归属断言（越权请求不得在磁盘/台账留下任何痕迹）；
          2. 读入原始流（**已被 `validate_upload` 限长**，故内存占用有上界）并算 sha256；
          3. 建台账行（此时 `content_sha256` 已确定，路径可由 `blob_ref_for` 纯函数推导）；
          4. 落盘（用台账给出的**权威 `doc_id`** 构造路径）；
          5. 第 4 步失败 → **补偿删除**第 3 步的台账行后再抛出（避免「看得见但读不到」的 pending 幽灵）。
        """
        scope = _scope_of(ctx, kb_id)
        self._ledger.assert_kb_in_project(scope.project_id, kb_id)

        content_sha256 = ""
        size_bytes = validated.size_bytes
        payload: bytes | None = None
        if data is not None:
            payload = data.read()
            if isinstance(payload, str):  # pragma: no cover - 防御
                payload = payload.encode("utf-8")
            if len(payload) > self._max_upload_bytes:
                raise ValidationError(
                    f"文件超出大小上限（{self._max_upload_bytes // (1024 * 1024)}MB）"
                )
            content_sha256 = hashlib.sha256(payload).hexdigest()
            size_bytes = len(payload)

        record = self._ledger.create_document(
            scope,
            validated.filename,
            validated.ext,
            size_bytes,
            content_sha256,
            None,
        )
        if payload is not None:
            try:
                ref = self._blobs.put(scope, record.doc_id, io.BytesIO(payload), validated.ext)
            except Exception:
                self._compensate_upload(scope, record.doc_id)
                raise
            if ref.sha256 != content_sha256:  # pragma: no cover - 不一致说明存储被篡改
                self._compensate_upload(scope, record.doc_id)
                raise DependencyUnavailableError("原文件摘要与台账记录不一致", dependency="blob")
        log_event(
            "indexing",
            "accepted",
            project_id=scope.project_id,
            doc_id=record.doc_id,
            kb_id=kb_id,
        )
        return record

    def _compensate_upload(self, scope: Scope, doc_id: str) -> None:
        """补偿：删除刚落盘的台账行（best-effort，失败只记日志）。"""
        try:
            self._ledger.mark_deleted(scope, doc_id)
        except Exception as exc:  # noqa: BLE001 - 补偿失败不改写原始异常
            get_logger("indexing").warn(
                "failed", error_code=f"compensate_failed:{type(exc).__name__}", doc_id=doc_id
            )

    # ================================================================== #
    # IFC-IB-278 页面图关联持久化（R2 / M-02）
    # ================================================================== #

    def persist_page_images(
        self, scope: Scope, doc_id: str, bindings: Sequence[PageImageBinding]
    ) -> int:
        """[IFC-IB-278] 幂等写入页面图关联行，返回写入行数。

        时机由 `_process_one` 保证：**向量写入成功之后、台账置 `indexed` 之前** ——
        于是「台账说 `indexed` ⇒ 关联已就绪」成立（与 ADR-07 的写序同源）。

        归属由**本方法的 scope 参数**决定（而非 `bindings` 里的空值）：
        `bind_page_images` 是纯函数、拿不到项目上下文，故身份只能在此补全，
        这也在结构上排除了「解析内容伪造归属」的可能（FM-3）。
        """
        if not bindings:
            # 仍要调用一次台账：清掉该文档**上一轮**可能残留的关联行
            # （例如新版本解析不再产出任何图）。「什么都不做」会留下陈旧关联 ——
            # 那会让用户看到一张已经不存在的图（比看不到更糟）。
            return int(self._ledger.upsert_chunk_images(scope, doc_id, []))
        record = self._ledger.get_document(scope, doc_id)
        if record is None:
            raise NotFoundError("文档不存在或不在当前作用域内")
        kb_id = _kb_id_of(scope, bindings)
        created_at = utc_now_iso()
        records = [
            ChunkImageRecord(
                project_id=scope.project_id,
                kb_id=kb_id,
                doc_id=doc_id,
                page_or_section=binding.page_or_section,
                image_id=image.image_id,
                source_kind=image.source_kind,
                locator=image.locator,
                blob_ref=image.blob_ref,
                doc_name=record.doc_name,
                created_at=created_at,
            )
            for binding in bindings
            for image in binding.images
        ]
        return int(self._ledger.upsert_chunk_images(scope, doc_id, records))

    # ================================================================== #
    # IFC-IB-143 批量处理
    # ================================================================== #

    def process_pending(self, lease_owner: str, limit: int) -> ProcessReport:
        """认领 + 处理一批 `pending` 文档（worker 调用）。

        * 单个文档失败**不中断**本批（§6.4）；
        * 并发删除的文档计为 `skipped`（不是失败）—— 用户主动删除不是系统故障；
        * 处理中周期性 `renew_lease`，长任务不会被回收器抢走。
        """
        claimed = self._ledger.claim_pending(lease_owner, lease_seconds=self._lease_seconds, limit=limit)
        processed = succeeded = failed = skipped = 0
        for record in claimed:
            processed += 1
            try:
                outcome = self._process_one(record, lease_owner)
            except _DeletedConcurrently:
                skipped += 1
                continue
            except NotFoundError as exc:
                # 处理期间台账行消失 ⇒ 用户并发删除。台账是**可见性权威**：行已删即
                # 「安全跳过」，绝不让本次残留的派生物复活（R3 / FND-GROUP-D-02）。
                # 判别用「行确实不在」而非「抛了 NotFoundError」——后者也可能来自别处
                # （如项目未登记），那属于真故障，必须仍走 `failed` 路径，不得被吞。
                scope = Scope(project_id=record.project_id, kb_ids=(record.kb_id,))
                if self._ledger.get_document(scope, record.doc_id) is not None:
                    failed += 1
                    self._fail_document(record, exc)
                    continue
                self._discard_written_vectors(scope, record.doc_id)
                skipped += 1
                log_event(
                    "indexing",
                    "skipped",
                    project_id=record.project_id,
                    doc_id=record.doc_id,
                    reason="deleted_concurrently",
                )
                continue
            except Exception as exc:  # noqa: BLE001 - 文档级失败必须被吞掉，否则整批停摆
                failed += 1
                self._fail_document(record, exc)
                continue
            if outcome:
                succeeded += 1
            else:
                skipped += 1
        return ProcessReport(
            processed=processed, succeeded=succeeded, failed=failed, skipped=skipped
        )

    def _fail_document(self, record: DocumentRecord, exc: BaseException) -> None:
        """文档级失败：分类 → 置 `failed` → 记日志（`process_pending` 的两处失败路径共用）。"""
        code = _classify(exc)
        self._mark_failed(record, code)
        log_event(
            "indexing",
            "failed",
            project_id=record.project_id,
            doc_id=record.doc_id,
            error_code=code,
        )

    def _discard_written_vectors(self, scope: Scope, doc_id: str) -> None:
        """**尽力而为**地清掉本进程为该文档写过的向量（并发删除后的清扫）。

        为什么这里吞异常：本方法运行在「台账行已消失」这一**已判定的事实**之上 —— 文档对
        读路径已不可见，清扫失败不该把结果从 `skipped` 翻成 `failed`（那是把用户的主动删除
        报成系统故障）。真正的兜底是 `delete_document` 第 4 步的竞态清扫；此处只记 WARNING。
        """
        try:
            self._vectors.delete_by_doc(scope, doc_id)
        except Exception as exc:  # noqa: BLE001 - 见 docstring：尽力而为，删除侧另有兜底
            get_logger("indexing").warn(
                "warned",
                error_code=f"ghost_cleanup_failed:{type(exc).__name__}",
                doc_id=doc_id,
            )

    def _process_one(self, record: DocumentRecord, lease_owner: str) -> bool:
        """处理单个文档。返回 `True` 表示成功置位，`False` 表示安全跳过。

        **R2 步骤扩展（IFC-IB-280）：七步 → 九步**，新增两步插在固定位置：
        第 4 步 `bind_page_images`（切分之后、向量化之前）与
        第 7 步 `persist_page_images`（向量写入之后、台账置位之前）。
        两步**不改变**既有失败粒度：任一步抛出的异常仍走同一条
        「文档级 `failed` + `error_code`」路径（§6.4），页级降级仍只在 MOD-IB-05 内部。
        """
        scope = Scope(project_id=record.project_id, kb_ids=(record.kb_id,))
        # 0) 【R3】认领与处理之间可能已被删除：台账行是可见性权威，行已删即安全跳过，
        #    不再产出任何派生物（否则「用户以为删了、内容仍在作答」，FND-GROUP-D-02）。
        if self._ledger.get_document(scope, record.doc_id) is None:
            raise _DeletedConcurrently()
        with Timer() as timer:
            # 1) 取原始文件（引用由记录纯推导）
            blob_ref = blob_ref_for(record)
            if blob_ref is None:
                raise DependencyUnavailableError("文档缺少原文件引用", dependency="blob")
            payload = self._blobs.get(blob_ref)
            if payload is None:
                raise DependencyUnavailableError("原文件缺失或不可读", dependency="blob")

            # 2) 解析（页级降级在 MOD-IB-05 内部消化）
            try:
                parsed: ParsedDocument = self._parsers.parse(
                    record.ext,
                    io.BytesIO(payload),
                    ocr=self._ocr,
                    renderer=self._renderer,
                    spec=self._chunking_spec,
                )
            except ValueError as exc:
                # 未注册扩展名等 —— 属文档级失败（不是依赖故障）
                raise _DocumentFailed("解析器未注册或输入非法") from exc

            # 3) 切分
            chunks = self._chunker.split(parsed, self._chunking_spec)
            self._renew(record.doc_id, lease_owner)

            # 4) 【R2 新增】绑定页面图（纯函数，无 IO，不产生新的失败面）
            bindings = bind_page_images(parsed, doc_id=record.doc_id)

            # 5) 冷路径向量化（批量 / 长超时 / 多重试）
            texts = [chunk.content for chunk in chunks]
            vectors = (
                self._embedder.embed_documents(
                    texts,
                    timeout_s=self._cold_timeout_s,
                    max_retries=self._cold_max_retries,
                    batch_size=self._cold_batch_size,
                )
                if texts
                else []
            )
            if texts and len(vectors) != len(texts):
                raise DependencyUnavailableError("向量数量与文本数量不符", dependency="embedder")
            self._renew(record.doc_id, lease_owner)

            # 6) 写库：先绑 collection（唯一样本来自 CollectionResolver，FM-5）
            project = self._project_provider(record.project_id)
            collection = self._resolver.resolve(scope, project)
            self._resolver.assert_prefix(collection, record.project_id)
            from ib.embedding import collection_spec_for

            self._vectors.bind_collection(collection)
            self._vectors.ensure_collection(collection_spec_for(project))
            # delete-then-write：重跑覆盖同一批点（§6.2）
            self._vectors.delete_by_doc(scope, record.doc_id)
            points = [
                VectorPoint(
                    id=point_id_for(record.doc_id, index),
                    vector=vector,
                    payload=_payload_for(
                        record, chunk, index, vector, project, blob_ref.rel_path if blob_ref else None
                    ),
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors))
            ]
            if points:
                self._vectors.upsert(points, wait=True)
            self._renew(record.doc_id, lease_owner)

            # 7) 【R2 新增】持久化页面图关联 —— 必须在向量写入**之后**、
            #    台账置位**之前**（IFC-IB-278 / ADR-07 写序）。
            self.persist_page_images(scope, record.doc_id, bindings)

            # 8) 块元数据
            self._ledger.upsert_chunks(
                scope,
                record.doc_id,
                [
                    ChunkRecord(
                        chunk_id=f"{record.doc_id}#{index}",
                        doc_id=record.doc_id,
                        project_id=record.project_id,
                        kb_id=record.kb_id,
                        chunk_index=index,
                        content_hash=_content_hash(chunk.content),
                        locator=chunk.locator,
                        source_kind=chunk.source_kind,
                        page_or_section=chunk.page_or_section,
                        indexed_model=self._embedder.model_id(),
                        indexed_dim=self._embedder.dim(),
                    )
                    for index, chunk in enumerate(chunks)
                ],
            )

            # 9) 置位（**最后**一步：先向量后台账，ADR-07）
            self._ledger.mark_indexed(
                scope, record.doc_id, project.active_collection_version, len(chunks)
            )
        log_event(
            "indexing",
            "succeeded",
            project_id=record.project_id,
            doc_id=record.doc_id,
            elapsed_ms=timer.elapsed_ms,
            page_images=len(bindings),
        )
        return True

    def _renew(self, doc_id: str, lease_owner: str) -> None:
        """续租。失败不抛 —— 续租失败只意味着可能被回收，重跑是幂等的。"""
        try:
            self._ledger.renew_lease(doc_id, lease_owner, self._lease_seconds)
        except Exception as exc:  # noqa: BLE001
            get_logger("indexing").warn(
                "warned", error_code=f"renew_failed:{type(exc).__name__}", doc_id=doc_id
            )

    def _mark_failed(self, record: DocumentRecord, code: str) -> None:
        """置为 `failed` + `error_code`。台账不可用时不掩盖原始错误（只记日志）。"""
        scope = Scope(project_id=record.project_id, kb_ids=(record.kb_id,))
        try:
            self._ledger.set_status(scope, record.doc_id, DocStatus.FAILED, error_code=code)
        except (NotFoundError, ConflictError):
            # 并发删除或状态已被他方推进 —— 都不是故障，安全退出
            pass
        except DependencyUnavailableError:
            get_logger("indexing").error(
                "failed", error_code="ledger_unavailable", doc_id=record.doc_id
            )

    # ================================================================== #
    # IFC-IB-144 删除
    # ================================================================== #

    def delete_document(self, scope: Scope, doc_id: str) -> DeleteReport:
        """删除文档：向量 → 原文件 → 台账行（顺序即「先删派生物，后删权威」）。

        为什么台账行最后删：台账是**可见性的权威**。若先删行、后删向量，崩溃时会留下
        「看不见但检索得到」的幽灵向量（最危险的一类残留）；反过来崩溃则留下
        「看得见但索引已空」的行，可由 `list_orphan_doc_ids` 对账修复，且用户重试删除即可。

        **IFC-IB-281（R2 删除零改动不变式）**：本方法的**签名、返回类型与语义一字未改**。
        页面图关联行不在此处显式删除：它们随 `documents` 行**级联删除**
        （SQLite 侧由 `chunk_image.doc_id … ON DELETE CASCADE` 在**同一事务内**完成；
        内存替身由 `mark_deleted` 显式对齐）。因此 `DeleteReport` 的三个计数
        （`vectors_deleted` / `blob_deleted` / `ledger_deleted`）**语义不变**，
        删除重放对账（IFC-IB-131 `list_orphan_doc_ids`）亦**不新增用例**。

        **R3（FND-GROUP-D-02）两处修正，均不减损上面的不变式**：

        1. **向量删除前先自绑 collection**（`_bind_write_collection`）。此前删除**假定**
           向量库「恰好已被别处绑定」；但组合根在启动期只 `ensure_collection`（建库）而
           **不** `bind_collection`，于是「上传后立刻删除」（本项目尚无事发生）必然抛
           `StartupError` → HTTP 500、台账行残留 → worker 稍后照常索引，用户以为删了的
           内容仍在作答。绑 collection 的唯一真源仍是 `CollectionResolver`（FM-5），
           绝无 `ib_<project>_v1` 之类的静默回退。
        2. **台账行删除后做一次「竞态清扫」**（第二次 `delete_by_doc`）。清的是
           「worker 在本次删除的向量清扫与台账行删除之间重新写入的点」——
           那正是「行已删但仍可被检索到」的最后一小段窗口（AC-IB-02-04）。

        清扫**不做宽泛的异常吞噬**：向量库真故障（`DependencyUnavailableError`）照旧
        上抛为 503。「本项目尚无任何派生物」由第 1 步的显式绑定自然收敛为
        `vectors_deleted == 0` 的**成功** —— 组合根启动期已对每个登记项目
        `ensure_collection`（`composition._ensure_collections`），故此刻的状态是
        「collection 已建但为空」，而非「collection 不存在」；后者对 Qdrant 会以异常
        上抛（fail-closed 503），是**刻意保留**的诚实失败，不被本方法吞掉。

        **R4（FND-GROUP-D-03）原文件删除的单一真源**：第 2 步的原文件删除改用
        `_blob_scope_of(record)`（由**台账记录**派生），而非调用方传入的 `scope`。
        调用方在 HTTP 路径上是**项目级** scope（`resolve_scope` → `kb_ids=None`），
        BlobStore 会把它归为 `default` 段；而文件上传时是按真实 kb 落盘的 →
        旧实现删不到 → 原文件成孤儿且 `blob_deleted` 恒 False（违反 AC-IB-03-02/03）。
        现由记录派生删除 scope，其 kb 段与写入时同源，故 `blob_deleted` 正确置位
        （确有且已删 → True；本无 → False）。`DeleteReport` 三计数语义与签名**不变**
        （IFC-IB-281 仍成立）。
        """
        record = self._ledger.get_document(scope, doc_id)
        if record is None:
            raise NotFoundError("文档不存在或不在当前作用域内")

        # 1) 派生物之一：向量（先自绑 collection，再删；FM-5 唯一真源）
        self._bind_write_collection(scope, record.project_id)
        vectors_deleted = int(self._vectors.delete_by_doc(scope, doc_id))

        # 2) 派生物之二：原文件字节
        blob_deleted = self._blobs.delete(_blob_scope_of(record), doc_id) > 0

        # 3) 权威：台账行（**最后**删，顺序不变）
        self._ledger.mark_deleted(scope, doc_id)

        # 4) 【R3】竞态清扫：清掉窗口内被 worker 重新写入的点（正常路径恒为 0）
        vectors_deleted += int(self._vectors.delete_by_doc(scope, doc_id))

        log_event("deletion", "succeeded", project_id=scope.project_id, doc_id=doc_id)
        return DeleteReport(
            vectors_deleted=vectors_deleted,
            blob_deleted=bool(blob_deleted),
            ledger_deleted=True,
        )

    def _bind_write_collection(self, scope: Scope, project_id: str) -> None:
        """把向量库绑到该项目的**写路径** collection（与 `_process_one` 第 6 步同源）。

        组合根启动期只 `ensure_collection`（建库）而**不** `bind_collection` —— 绑定此前
        只在写路径/读路径**惰性**发生。删除若继续假定「已被别处绑定」，就会在
        「本项目尚无事发生」的窗口内抛 `StartupError`（FND-GROUP-D-02）。
        这里现取现绑，使删除**不依赖**别的调用点先跑过。
        """
        project = self._project_provider(project_id)
        collection = self._resolver.resolve(scope, project)
        self._resolver.assert_prefix(collection, project_id)
        self._vectors.bind_collection(collection)

    # ================================================================== #
    # IFC-IB-145 人工重试
    # ================================================================== #

    def retry_document(self, scope: Scope, doc_id: str) -> DocumentRecord:
        """人工重试：**仅 `failed → pending`**（否则 409，IFC-IB-245）。"""
        record = self._ledger.get_document(scope, doc_id)
        if record is None:
            raise NotFoundError("文档不存在或不在当前作用域内")
        if record.status != "failed":
            raise ConflictError(f"仅 failed 状态的文档可重试（当前：{record.status}）")
        self._ledger.set_status(scope, doc_id, DocStatus.PENDING, error_code=None)
        updated = self._ledger.get_document(scope, doc_id)
        if updated is None:  # pragma: no cover
            raise DependencyUnavailableError("重试后读取台账失败", dependency="ledger")
        return updated


# --------------------------------------------------------------------------- #
# 内部辅助
# --------------------------------------------------------------------------- #


class _DeletedConcurrently(Exception):
    """文档在处理过程中被并发删除（安全跳过，不计为失败）。"""


class _DocumentFailed(Exception):
    """文档级失败（内容/格式问题，非依赖故障）—— 计入 `failed` 并带 `E_PARSE` 类码。"""


def _scope_of(ctx: RequestContext, kb_id: str) -> Scope:
    """由请求上下文 + 知识库构造 scope。`project_id` 来自上下文而**非请求体**（IFC-IB-241 纪律）。"""
    return Scope(project_id=ctx.authz.project_id, kb_ids=(kb_id,) if kb_id else None)


def _blob_scope_of(record: DocumentRecord) -> Scope:
    """由**台账记录**派生原文件存储 scope（R4 / FND-GROUP-D-03 的单一真源）。

    为什么不能沿用调用方传入的 `scope`：HTTP 删除路径的 scope 来自
    `ibweb/composition.resolve_scope`，它是**项目级**的（`kb_ids=None`）—— BlobStore 把
    `None` 归为 `default` 段，而上传时文件是按**真实 kb** 落盘的。于是删除会在 `default`
    段查找、查不到 → 返回 0 → 原文件成孤儿且 `blob_deleted` 恒 False（FND-GROUP-D-03）。

    `record` 是 `delete_document` 内 `get_document(scope, doc_id)` 的返回值，**已通过
    scope 过滤**（project 必相同、kb 若被限定亦相同），故据其 `kb_id` 构造的删除 scope
    与写入时 `BlobStore.put` 的 kb 段**同源**（`record.kb_id` 与 `safe_segment`/`kb_segment`
    的输入同出一处 —— 见 `submit_upload` 与 `sqlite_repo.create_document`）。
    项目级上传时 `record.kb_id == ""`，经 `kb_segment` 归一为 `default`，与落盘段一致。

    这样**不构成越权删除**：`project_id` 与记录相同、`kb_id` 属同一项目内的记录归属，
    且路径段仍经 `safe_segment` 白名单与 `_abs` 根目录断言两道防护。
    """
    return Scope(project_id=record.project_id, kb_ids=(record.kb_id,) if record.kb_id else None)


def _kb_id_of(scope: Scope, bindings: Sequence[PageImageBinding]) -> str:
    """为关联行确定 `kb_id`：**scope 优先**，其次绑定里的值，最后空串。

    顺序刻意如此：scope 是鉴权/隔离的权威（FM-3），绑定里的 `kb_id` 只是纯函数的残留
    （`bind_page_images` 拿不到 scope，故留空）。项目级 scope（`kb_ids=None`）时二者都空，
    此时空串是**诚实**的取值 —— 台账的 `idx_chunk_image_scope` 索引仍按 project 可用。
    """
    if scope.kb_ids:
        return scope.kb_ids[0]
    for binding in bindings:
        if binding.kb_id:
            return binding.kb_id
    return ""


def _content_hash(text: str) -> str:
    """块内容摘要（前 16 位十六进制）。用于「内容未变则不必重写」的快速比对。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _classify(exc: Exception) -> str:
    """异常 → 失败原因码。**只输出码，不输出异常文本**（FM-8）。"""
    if isinstance(exc, _DocumentFailed):
        return ERROR_CODES["parse"]
    if isinstance(exc, ValidationError):
        return ERROR_CODES["validate"]
    if isinstance(exc, DependencyUnavailableError):
        dependency = (exc.dependency or "").lower()
        if "blob" in dependency:
            return ERROR_CODES["blob_unavailable"]
        if "embed" in dependency:
            return ERROR_CODES["embed"]
        if "qdrant" in dependency or "vector" in dependency:
            return ERROR_CODES["vectorstore"]
        if "ledger" in dependency or "sqlite" in dependency:
            return ERROR_CODES["ledger"]
        if "parse" in dependency or "pdf" in dependency or "docx" in dependency:
            return ERROR_CODES["parse"]
        return ERROR_CODES["unknown"]
    if isinstance(exc, NotFoundError):
        return ERROR_CODES["deleted_concurrently"]
    return ERROR_CODES["unknown"]


def _payload_for(
    record: DocumentRecord,
    chunk: ParsedChunk,
    index: int,
    vector: Any,
    project: ProjectRecord,
    blob_rel_path: str | None,
) -> PointPayload:
    """构造向量点 payload（§2.1 的 15 个字段，字段名与契约逐字一致）。"""
    return PointPayload(
        project_id=record.project_id,
        kb_id=record.kb_id,
        doc_id=record.doc_id,
        doc_name=record.doc_name,
        chunk_index=index,
        content=chunk.content,
        locator=chunk.locator,
        source_kind=chunk.source_kind,
        page_or_section=chunk.page_or_section,
        content_hash=_content_hash(chunk.content),
        indexed_model=project.embedding_model_id,
        indexed_dim=len(vector),
        created_at=record.updated_at,
        blob_ref=blob_rel_path,
        schema_version=1,
    )
