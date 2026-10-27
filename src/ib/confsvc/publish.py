# MOD-R26-13 / implements IFC-R26-120 / depends MOD-R26-01, 02, 04, 05（ADR-55 发布协议）
"""配置发布服务：预览 / 发布 / 回滚 / 采纳漂移 / 崩溃恢复。

发布协议（单进程内串行点 = 版本存储的 `BEGIN IMMEDIATE`）：
  1 核对 base == head（乐观 CAS）→ 2 统一校验（`validator` ∪ `validate_prompt_texts`）→ 3 差异（空 → no_changes）→
  4 `begin_publish` 占 pending（v1 项目同事务先写“升级前基线”）→ 5 `precompile`（失败 = apply_failed，**尚未写盘**）→
  6 写文件（先提示词层，**定义文档最后**）→ 7 `commit_publish` → 8 `on_published` 令本进程立即换引用 + 审计。
任一步在 6/7 失败：依升级前快照还原文件并 `abort_publish`，在用版本不变。崩溃遗留的陈旧 pending 由 `recover` 认领还原。
本服务只经注入的端口 / 回调访问外部，库内可离线单测；审计只记对象 id / 类别，不含提示词正文与凭据。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Literal, Mapping

from ib.config.versioning import (
    build_snapshot,
    detect_conflicts,
    diff_snapshots,
    is_layout_only,
    manifest_hash,
    summarize_diff,
    validate_prompt_texts,
)
from ib.core import (
    ConfigAuditEntry,
    ConfigSnapshot,
    ConflictReceipt,
    DefinitionDocument,
    DiffItem,
    IbError,
    NewVersion,
    PromptLayers,
    ValidationErrorItem,
)

__all__ = [
    "PublishRequest",
    "PublishPreview",
    "PublishResult",
    "PublishError",
    "ConfigPublishService",
]

_MESSAGE_MAX = 200


@dataclass(frozen=True, slots=True)
class PublishRequest:
    project_id: str
    actor: str
    base_version: int
    document: DefinitionDocument
    prompts: Mapping[str, PromptLayers]  # 只含本次变更的专家；PromptLayers 内 None = 不变，main 为 "" = 删除该层
    message: str | None = None
    #: 旧端点（`PUT /api/config/definition|prompts`）退化为发布包装时沿用其审计动作名与“变更字段路径”（REV-26 IFC-R26-132）。
    audit_action: str = "config.publish"
    audit_fields: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class PublishPreview:
    base_version: int
    head_version: int
    items: tuple[DiffItem, ...]
    layout_only: bool
    errors: tuple[ValidationErrorItem, ...]


@dataclass(frozen=True, slots=True)
class PublishResult:
    version: int
    previous_version: int
    content_hash: str


PublishCode = Literal[
    "validation_error", "conflict", "config_busy", "no_changes", "apply_failed", "version_not_found", "drift_detected"
]


class PublishError(IbError):
    def __init__(
        self,
        code: PublishCode,
        message: str,
        *,
        items: tuple[ValidationErrorItem, ...] = (),
        receipt: ConflictReceipt | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.items = items
        self.receipt = receipt


class ConfigPublishService:
    def __init__(
        self,
        *,
        versions: Any,
        definition_store: Any,
        prompt_store_for: Callable[[str], Any],
        loader: Any,
        precompile: Callable[[str, int, ConfigSnapshot], Any],
        on_published: Callable[[str, int, Any], None],
        audit: Any,
        validator: Callable[[ConfigSnapshot], tuple[ValidationErrorItem, ...]],
        clock: Callable[[], str],
        keep_versions: int = 50,
        pending_stale_s: float = 30.0,
    ) -> None:
        self._versions = versions
        self._defs = definition_store
        self._prompt_store_for = prompt_store_for
        self._loader = loader
        self._precompile = precompile
        self._on_published = on_published
        self._audit = audit
        self._validator = validator
        self._clock = clock
        self._keep = int(keep_versions)
        self._stale_s = float(pending_stale_s)

    # ------------------------------------------------------------------ #
    # 读
    # ------------------------------------------------------------------ #

    def current(self, project_id: str) -> ConfigSnapshot:
        """文件态 → 快照（v1 规范化由 loader 负责，不改文件）。"""
        return self._loader.load_files(project_id)

    def _merge(self, cur: ConfigSnapshot, req: PublishRequest) -> ConfigSnapshot:
        """请求 = 文档 + 变更的提示词层；其余层沿用当前文件态。"""
        have = dict(cur.prompts)
        # 新专家的提示词可能已先于定义文档落盘（创建期落盘，ADR-51）：当前快照没有的专家，从文件态补读其两层
        extra = [e.name for e in req.document.experts if e.name not in have]
        reader = getattr(self._loader, "load_layers", None)
        if extra and callable(reader):
            have.update(reader(req.project_id, extra))
        merged: dict[str, PromptLayers] = {}
        for e in req.document.experts:
            base = have.get(e.name, PromptLayers(None, None))
            patch = req.prompts.get(e.name)
            main, fb = base.main, base.fallback
            if patch is not None:
                if patch.main is not None:
                    main = None if patch.main == "" else patch.main
                if patch.fallback is not None:
                    fb = patch.fallback
            merged[e.name] = PromptLayers(main, fb)
        return build_snapshot(req.document, merged)

    def _errors(self, snap: ConfigSnapshot) -> tuple[ValidationErrorItem, ...]:
        errs = list(self._validator(snap))
        errs.extend(validate_prompt_texts(dict(snap.prompts), experts=snap.definition.experts))
        return tuple(errs)

    def _receipt(self, project_id: str, base_version: int, head_version: int, submitted: ConfigSnapshot) -> ConflictReceipt:
        base = self._versions.get_version(project_id, base_version) if base_version > 0 else None
        head = self._versions.get_version(project_id, head_version) if head_version > 0 else None
        head_snap = head[1] if head else self.current(project_id)
        base_snap = base[1] if base else (self.current(project_id) if base_version == 0 and head_version == 0 else None)
        receipt = detect_conflicts(base_snap, head_snap, submitted)
        return replace(receipt, base_version=base_version, head_version=head_version)

    def candidate(self, req: PublishRequest) -> ConfigSnapshot:
        """请求 → 候选快照（文档 + 合并后的提示词层）；只读，不校验、不写（供 validate / 试运行使用）。"""
        return self._merge(self.current(req.project_id), req)

    def validate(self, req: PublishRequest) -> tuple[ValidationErrorItem, ...]:
        """与发布同一校验入口（`validator` ∪ `validate_prompt_texts`）；不要求 base 版本匹配。"""
        return self._errors(self.candidate(req))

    def preview(self, req: PublishRequest) -> PublishPreview:
        head = self._versions.head(req.project_id)
        cur = self.current(req.project_id)
        new = self._merge(cur, req)
        if req.base_version != head.published_version:
            raise PublishError(
                "conflict", "配置已被他人更新，请重新载入",
                receipt=self._receipt(req.project_id, req.base_version, head.published_version, new),
            )
        items = diff_snapshots(cur, new)
        return PublishPreview(
            base_version=req.base_version,
            head_version=head.published_version,
            items=items,
            layout_only=is_layout_only(items),
            errors=self._errors(new),
        )

    # ------------------------------------------------------------------ #
    # 写
    # ------------------------------------------------------------------ #

    def publish(self, req: PublishRequest) -> PublishResult:
        cur = self.current(req.project_id)
        return self._apply(
            req.project_id, req.actor, req.base_version, self._merge(cur, req), cur,
            kind="publish", rolled_back_to=None, message=req.message, action=req.audit_action,
            fields=req.audit_fields,
        )

    def rollback(
        self, project_id: str, actor: str, *, target_version: int, base_version: int, message: str | None
    ) -> PublishResult:
        found = self._versions.get_version(project_id, int(target_version))
        if found is None:
            raise PublishError("version_not_found", "目标版本不存在或已被修剪")
        cur = self.current(project_id)
        return self._apply(
            project_id, actor, base_version, found[1], cur,
            kind="rollback", rolled_back_to=int(target_version), message=message, action="config.rollback",
        )

    def adopt_drift(self, project_id: str, actor: str, *, base_version: int) -> PublishResult:
        """把“文件态相对已发布版本的漂移”登记为新版本（不写文件）。无漂移 → no_changes。"""
        head = self._versions.head(project_id)
        head_rec = self._versions.get_version(project_id, head.published_version) if head.published_version else None
        files = self.current(project_id)
        if head_rec is not None and manifest_hash(head_rec[1]) == manifest_hash(files):
            raise PublishError("no_changes", "文件态与已发布版本一致，无漂移")
        return self._apply(
            project_id, actor, base_version, files, files,
            kind="adopt", rolled_back_to=None, message=None, action="config.adopt_drift", write_files=False,
        )

    def _apply(
        self,
        project_id: str,
        actor: str,
        base_version: int,
        new: ConfigSnapshot,
        cur: ConfigSnapshot,
        *,
        kind: str,
        rolled_back_to: int | None,
        message: str | None,
        action: str,
        write_files: bool = True,
        fields: tuple[str, ...] | None = None,
    ) -> PublishResult:
        if self._versions.head(project_id).pending_version is not None:
            self.recover(project_id)  # 陈旧 pending（崩溃遗留）先回收；未陈旧则下面 begin 回执 busy
        head = self._versions.head(project_id)
        if base_version != head.published_version:
            self._audit_rejected(project_id, actor, action, (), "conflict", head.published_version)
            raise PublishError(
                "conflict", "配置已被他人更新，请重新载入",
                receipt=self._receipt(project_id, base_version, head.published_version, new),
            )
        errors = self._errors(new)
        if errors:
            # AC-023-02：校验失败的保存也有审计（result=rejected，detail 只含错误码，不含提示词正文与取值）
            codes = ",".join(sorted({e.code for e in errors if getattr(e, "code", "")}))[:200] or "validation_error"
            self._audit_rejected(project_id, actor, action, (), codes, head.published_version)
            raise PublishError("validation_error", "配置校验未通过", items=errors)
        items = diff_snapshots(cur, new)
        if not items and kind in ("publish", "rollback"):
            raise PublishError("no_changes", "没有任何变更")
        summary = (message or "").strip()[:_MESSAGE_MAX] or summarize_diff(items)
        nv = NewVersion(kind, actor, summary, rolled_back_to, manifest_hash(new))  # type: ignore[arg-type]
        now = self._clock()
        begin = self._versions.begin_publish(
            project_id, base_version=base_version, new=nv, snapshot=new,
            extra_baseline=cur if head.published_version == 0 else None,
            now=now, stale_after_s=self._stale_s,
        )
        if begin.outcome == "busy":
            raise PublishError("config_busy", "另一次保存正在进行，请稍后重试")
        if begin.outcome == "stale_base":
            raise PublishError(
                "conflict", "配置已被他人更新，请重新载入",
                receipt=self._receipt(project_id, base_version, begin.head_version, new),
            )
        version = int(begin.version or 0)
        try:
            compiled = self._precompile(project_id, version, new)  # 失败 → 尚未写盘
        except Exception as exc:  # noqa: BLE001
            self._versions.abort_publish(project_id, version, reason_code="apply_failed", now=self._clock())
            self._audit_rejected(project_id, actor, action, items, "apply_failed", head.published_version)
            raise PublishError("apply_failed", "新配置编译失败，已保持原配置生效") from exc
        # CR-009 / REQ-NFUNC-006：成功审计行与“置 published / 更新 head”**同一事务**提交；
        # 审计写不进 → 提交整体回滚 → 走下面的还原 + abort 分支，发布整体失败（不存在“已生效但无审计”）。
        audit_entry = self._entry(
            project_id, actor, action, items, "saved", None, head.published_version, version, fields=fields
        )
        try:
            if write_files:
                self._sync_files(project_id, cur, new)
            self._versions.commit_publish(
                project_id, version, now=self._clock(), keep=self._keep, audit=audit_entry
            )
        except Exception as exc:  # noqa: BLE001
            try:
                if write_files:
                    self._sync_files(project_id, new, cur)  # 依升级前快照还原
            finally:
                self._versions.abort_publish(project_id, version, reason_code="write_failed", now=self._clock())
            self._audit_rejected(project_id, actor, action, items, "write_failed", head.published_version)
            raise PublishError("apply_failed", "写入配置失败，已还原并保持原配置生效") from exc
        try:
            self._on_published(project_id, version, compiled)
        except Exception:  # noqa: BLE001 - 已提交的发布不回滚；运行时缓存的 head 探测会在节流窗口内收敛到新版本
            pass
        return PublishResult(
            version=version,
            previous_version=int(begin.head_version),
            content_hash=new.definition.content_hash,
        )

    # ------------------------------------------------------------------ #
    # 文件同步（先提示词层，定义文档最后）
    # ------------------------------------------------------------------ #

    def _sync_files(self, project_id: str, current: ConfigSnapshot | None, target: ConfigSnapshot) -> None:
        store = self._prompt_store_for(project_id)
        have = dict(current.prompts) if current is not None else {}
        for name, layers in target.prompts:
            old = have.get(name, PromptLayers(None, None))
            for layer in ("main", "fallback"):
                want, was = getattr(layers, layer), getattr(old, layer)
                if current is not None and want == was:
                    continue
                if want is None:
                    store.delete_layer(name, layer)
                else:
                    res = store.save_layer(name, layer, want, expected_hash=None)
                    if not res.saved:
                        raise IbError("提示词层写入失败", code="prompt_write_failed")
        keep = {n for n, _ in target.prompts}
        for name in sorted(set(have) - keep):  # 被删除的专家：清其提示词目录（否则装配期判孤儿文件）
            store.delete_layer(name, "main")
            store.delete_layer(name, "fallback")
        res_def = self._defs.save(project_id, target.definition, expected_content_hash=None)
        if not getattr(res_def, "ok", False):
            raise IbError("定义文档写入失败", code="definition_write_failed")

    # ------------------------------------------------------------------ #
    # 崩溃恢复
    # ------------------------------------------------------------------ #

    def recover(self, project_id: str) -> int | None:
        """认领陈旧 pending → 依 head 快照完整还原文件 → abort。返回被中止的版本号。"""
        version = self._versions.claim_stale_pending(project_id, now=self._clock(), stale_after_s=self._stale_s)
        if version is None:
            return None
        head = self._versions.head(project_id)
        found = self._versions.get_version(project_id, head.published_version) if head.published_version else None
        try:
            if found is not None:
                self._sync_files(project_id, None, found[1])
        finally:
            self._versions.abort_publish(project_id, version, reason_code="recovered", now=self._clock())
        return version

    # ------------------------------------------------------------------ #
    # 审计（只记对象 id / 类别）
    # ------------------------------------------------------------------ #

    def _entry(
        self, project_id: str, actor: str, action: str, items: tuple[DiffItem, ...], result: str,
        detail: str | None, before: int, after: int | None, fields: tuple[str, ...] | None = None,
    ) -> ConfigAuditEntry:
        return ConfigAuditEntry(
            timestamp=self._clock(),
            project=project_id,
            actor=actor,
            action=action,
            changed_field_names=(tuple(fields) if fields is not None else tuple(sorted({i.kind for i in items})))[:50],
            result=result,  # type: ignore[arg-type]
            detail_code=detail,
            version_before=before,
            version_after=after,
            object_summary=tuple(dict.fromkeys(f"{i.kind}:{i.object_id}" for i in items))[:50],
        )

    def _audit_rejected(
        self, project_id: str, actor: str, action: str, items: tuple[DiffItem, ...], code: str, before: int
    ) -> None:
        # 被拒绝 / 失败的保存的审计为尽力而为（该次操作本身没有产生任何生效变更，REQ-NFUNC-006 的“每次保存 / 回滚 / 权限变更”
        # 指成功生效的变更，其审计已并入提交事务）；失败不遮盖原始错误。
        try:
            self._audit.record(self._entry(project_id, actor, action, items, "rejected", code, before, None))
        except Exception:  # noqa: BLE001
            pass
