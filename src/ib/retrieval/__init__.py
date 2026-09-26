"""
@module MOD-IB-15
@implements IFC-IB-161 RetrievalService.search / IFC-IB-162 RetrievalService.search_as_tool
@depends MOD-IB-01, MOD-IB-02, MOD-IB-03, MOD-IB-04, MOD-IB-09, MOD-IB-10
@author sub_agent_software_developer

检索服务（module_design.md §3 MOD-IB-15 / architecture_design.md ADR-13、§「fail-open 读路径」；
REQ-FUNC-IB-14/16/17/23；AC-IB-06-02、AC-IB-08-03/04、AC-IB-13-01/02、AC-IB-14-01/02）。

## 唯一最重要的不变量：**本模块永不抛异常**（IFC-IB-161「无异常出口」）

理由（ADR-13 / REQ-NFR-IB-13/21）：检索是**问答的增强**，不是问答的**前提**。
用户问「今天会议室温度多少」时，知识库挂了不该让整个对话 500 —— 正确答案应该照常给出，
并**明确标注**「本次回答未使用知识库」。这就是 fail-open：依赖故障 → 降级结果 + 空命中 + 可读提示。

**降级必须可见**（AC-IB-14-01）：`degraded=True` + `degrade_reason` 会一路传到
编排层（MOD-IB-22）→ SSE 的 `degraded` 事件 → 前端「当前未接入知识资料库」，用户看得见。

## 「知识库为空」与「依赖故障」必须可区分（AC-IB-14-02）

这两者在 UI 上的正确措辞完全不同，绝不能混：

| 情形 | `degraded` | `degrade_reason` | 正确措辞 |
|------|-----------|------------------|---------|
| 知识库里确实没有相关内容 | `False` | `None` | 「知识库中没有相关资料」 |
| 嵌入服务不可达 / 向量库不可达 / 超时 | `True` | 具体原因 | 「当前未接入知识资料库」 |

把前者报成后者会**误导运维**（去排查一个根本没坏的依赖）；把后者报成前者会**误导用户**
（以为系统真查过了）。因此本模块对所有出口显式赋值，不存在「默认 False 蒙混过关」的路径。
"""

from __future__ import annotations

from typing import Any, Callable

from ib.core import (
    DegradeReason,
    PointFilter,
    RetrievalResult,
    RetrievedChunk,
    Scope,
    ToolResult,
)

__all__ = [
    "RetrievalService",
    "DEGRADED_HINT",
    "EMPTY_HINT",
]

#: 降级时的用户可读提示（前端不应自行编造措辞 —— 措辞是产品口径，收敛在服务端）。
DEGRADED_HINT = "当前未接入知识资料库，以下回答基于通用知识。"

#: 空结果提示（**不是降级**）。
EMPTY_HINT = "知识库中没有检索到相关资料。"


class RetrievalService:
    """检索编排（IFC-IB-161/162）。

    依赖注入（构造期）：`embedder`（MOD-IB-09 端口）、`vectors`（MOD-IB-10 端口）、
    `resolver`（collection 名唯一入口，MOD-IB-09）、`project_provider`（**读路径**提供者）。
    刻意**不**依赖台账：`project_provider` 由组合根注入，其内部读台账取 active 版本 ——
    于是「读哪个版本」这一个事实仍然只有台账一个真源，而本模块保持无存储依赖。
    """

    def __init__(
        self,
        *,
        embedder: Any,
        vectors: Any,
        resolver: Any,
        project_provider: Callable[[str], Any],
        top_k: int = 5,
        score_threshold: float = 0.35,
        candidate_multiplier: int = 4,
        hot_timeout_s: float = 5.0,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._resolver = resolver
        self._project_provider = project_provider
        self._top_k = max(1, int(top_k))
        self._score_threshold = float(score_threshold)
        #: 召回倍数：先多取候选再按阈值过滤，避免「阈值把近邻全滤掉 → 空结果」的假阴性。
        self._candidate_multiplier = max(1, int(candidate_multiplier))
        self._hot_timeout_s = float(hot_timeout_s)

    # ================================================================== #
    # IFC-IB-161 检索（无异常出口）
    # ================================================================== #

    def search(
        self,
        query: str,
        *,
        scope: Scope,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        """检索。**任何异常都在此被转换为降级结果**，调用方（编排/工具）无需 try。

        流程：绑定读路径 collection → 热路径向量化 → 向量查询 → 映射 `RetrievedChunk`。

        `top_k` / `score_threshold` 为 `None` 时取构造期配置；显式传入便于专家级调参。
        """
        from ib.observability import Timer, log_event

        eff_top_k = max(1, int(top_k)) if top_k is not None else self._top_k
        eff_threshold = float(score_threshold) if score_threshold is not None else self._score_threshold

        with Timer() as timer:
            # --- 1) 绑定读路径 collection（重建期间读旧版本，AC-IB-16-03） ---
            try:
                project = self._project_provider(scope.project_id)
                collection = self._resolver.resolve(scope, project)
                self._resolver.assert_prefix(collection, scope.project_id)
                self._vectors.bind_collection(collection)
            except Exception as exc:  # noqa: BLE001 - 端口契约要求无异常出口
                return self._degrade(
                    scope, DegradeReason.VECTORSTORE_UNAVAILABLE, timer, exc, stage="retrieval"
                )

            # --- 2) 热路径向量化（单条 / 短超时 / 少重试；超时即降级） ---
            try:
                vector = self._embedder.embed_query(query, timeout_s=self._hot_timeout_s)
            except Exception as exc:  # noqa: BLE001
                reason = _reason_of(exc, default=DegradeReason.EMBEDDING_UNAVAILABLE)
                return self._degrade(scope, reason, timer, exc, stage="retrieval")

            # --- 3) 查询（KB 级软隔离：filter 恒含 project_id 与 kb_ids） ---
            try:
                candidates = self._vectors.query(
                    vector,
                    scope=scope,
                    top_k=eff_top_k * self._candidate_multiplier,
                    score_threshold=eff_threshold,
                    filter=PointFilter(
                        project_id=scope.project_id,
                        kb_ids=tuple(scope.kb_ids) if scope.kb_ids else None,
                        doc_ids=None,
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                reason = _reason_of(exc, default=DegradeReason.VECTORSTORE_UNAVAILABLE)
                return self._degrade(scope, reason, timer, exc, stage="retrieval")

            # --- 4) 映射为对外的命中结构（**只取需要的字段**，不泄露 payload 全量） ---
            hits = [
                RetrievedChunk(
                    doc_id=point.payload.doc_id,
                    doc_name=point.payload.doc_name,
                    content=point.payload.content,
                    score=float(point.score),
                    page_or_section=point.payload.page_or_section,
                    source_kind=str(point.payload.source_kind),
                    locator=point.payload.locator,
                )
                for point in candidates[:eff_top_k]
            ]

        log_event(
            "retrieval",
            "succeeded" if hits else "empty",
            project_id=scope.project_id,
            elapsed_ms=timer.elapsed_ms,
        )
        # 这里 degraded 恒为 False：走到此处说明**所有依赖都正常**，
        # 空结果只是「知识库里确实没有」—— 与降级是两件事（AC-IB-14-02）。
        return RetrievalResult(
            hits=hits,
            degraded=False,
            degrade_reason=None,
            scope=scope,
            elapsed_ms=timer.elapsed_ms,
            candidate_count=len(candidates),
        )

    # ================================================================== #
    # IFC-IB-162 工具形态
    # ================================================================== #

    def search_as_tool(self, query: str, *, scope: Scope) -> ToolResult:
        """供 MOD-IB-17 绑定的工具形态：把 `RetrievalResult` 压成**可进 LLM 上下文**的文本。

        设计取舍：
          * 命中以 `[n] 文档名 (位置)` + 正文的紧凑格式串接 —— 编号给专家做引用标注；
          * **`ok` 表示「本次调用是否正常完成」**，与 `degraded` 不同：降级时 `ok=True`
            （调用本身成功了，只是没拿到资料），避免编排层把它当异常处理；
          * 无命中时返回 `EMPTY_HINT` 而非空串 —— 空串会让 LLM 以为「工具没输出」而重复调用。
        """
        result = self.search(query, scope=scope)
        if result.degraded:
            return ToolResult(
                ok=True,
                content=DEGRADED_HINT,
                degraded=True,
                degrade_reason=result.degrade_reason,
            )
        if not result.hits:
            return ToolResult(ok=True, content=EMPTY_HINT)
        lines: list[str] = []
        for index, hit in enumerate(result.hits, start=1):
            where = hit.page_or_section or hit.locator or "位置未知"
            lines.append(f"[{index}] {hit.doc_name} ({where})\n{hit.content}")
        return ToolResult(ok=True, content="\n\n".join(lines))

    # ------------------------------------------------------------------ #
    # 降级构造（**单一出口**，避免各处漏填字段）
    # ------------------------------------------------------------------ #

    def _degrade(
        self,
        scope: Scope,
        reason: Any,
        timer: Any,
        exc: BaseException,
        *,
        stage: str,
    ) -> RetrievalResult:
        """构造降级结果。

        日志**只记异常类型与原因码，不记 `str(exc)`**：异常文本可能内嵌 URL（含凭据）、
        检索片段或用户查询（FM-8 字段白名单）。
        """
        from ib.observability import log_event

        log_event(
            "retrieval",
            "degraded",
            project_id=scope.project_id,
            degrade_reason=str(reason),
            error_code=type(exc).__name__,
        )
        return RetrievalResult(
            hits=[],
            degraded=True,
            degrade_reason=reason,
            scope=scope,
            elapsed_ms=getattr(timer, "elapsed_ms", 0),
            candidate_count=0,
        )


# --------------------------------------------------------------------------- #
# 内部辅助
# --------------------------------------------------------------------------- #


def _reason_of(exc: BaseException, *, default: Any) -> Any:
    """异常 → 降级原因码（**超时是独立原因**，因为它指向不同的运维动作）。

    超时通常意味着「服务活着但慢」（扩容 / 调超时），不可达意味着「服务挂了」（拉起 / 检查网络）——
    归成同一个码会让值班同学丢掉最有价值的那条线索。

    判定优先级（从可靠到启发式）：
      1. 异常**自带的结构化标记**（`degrade_reason` / `reason` 属性，若有则最可靠）；
      2. 异常类型或异常链上出现 `TimeoutError`；
      3. 消息文本含 `timeout` / `timed out` / `超时`（**启发式**）。

    为什么需要第 3 条：真实嵌入适配器（MOD-IB-09 `LocalHttpEmbedder._post`）把
    「不可达」与「超时」都收敛为同一种 `DependencyUnavailableError`，只在消息里留下
    `TimeoutError` 字样 —— 没有结构化标记时，文本匹配是唯一可用的线索。
    这是**上游适配器可改进点**（见 code_review MINOR-05：宜在异常上带结构化原因码）。
    """
    for attr in ("degrade_reason", "reason"):
        marker = getattr(exc, attr, None)
        if marker is not None and "timeout" in str(marker).lower():
            return DegradeReason.TIMEOUT
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and len(chain) < 5:
        chain.append(current)
        current = current.__cause__ or current.__context__
    for node in chain:
        if isinstance(node, TimeoutError) or "timeout" in type(node).__name__.lower():
            return DegradeReason.TIMEOUT
    text = str(exc).lower()
    if "timeout" in text or "timed out" in text or "超时" in text:
        return DegradeReason.TIMEOUT
    return default
