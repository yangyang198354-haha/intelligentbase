"""
@module MOD-IB-14
@implements IFC-IB-151 plan_rebuild / 152 start_rebuild / 153 step_rebuild
            IFC-IB-154 activate_version / 155 rollback / 156 fingerprint
@depends MOD-IB-01, MOD-IB-02, MOD-IB-03, MOD-IB-04, MOD-IB-11, MOD-IB-12, MOD-IB-13
@author sub_agent_software_developer

索引重建（module_design.md §3 MOD-IB-14 / §6.5 序列；architecture_design.md ADR-05:235-236；
REQ-FUNC-IB-24 / DR-07）。

**为什么需要重建**：切分参数、解析器版本、归一化版本、嵌入模型或维度的任一变更，
都会让「旧向量」与「新配置」不再自洽。就地改写会经历一段**新旧混杂**的窗口
（部分文档新、部分文档旧，检索结果自相矛盾且无法解释）。因此重建的策略是
**「另建一个 collection 版本，全部写完再原子切换」**：

```
plan_rebuild（算指纹 → 定新版本号 → 建目标 collection）
   → step_rebuild（循环：驱动入库管线 → 续租 → 统计）
       ↓ 全部目标文档 indexed
   → activate_version（台账单值切换 active_collection_version）
       ↓
   读路径瞬时切到新集合（旧集合保留 → 回滚窗口）
```

四条硬性语义（AC-IB-16-01~04）：
  1. **`from_version` 由台账推导**，不接受调用方传入 —— 否则并发重建会读到错误基线；
  2. **单文档失败即不切换**（`activate_version` 在 `failed > 0` 时抛 `ConflictError`）
     —— 「切换即完整」是这条流水线的核心承诺；
  3. **重建期间读路径仍读旧集合**（`active_collection_version` 只在最后一步变），
     服务可用但内容非最新 —— 这是刻意的取舍，而非缺陷；
  4. **回滚 = 把 active 指回旧版本**，因为旧集合从未被删除，所以回滚是 O(1) 且可逆。

## 写路径 vs 读路径的版本重定向（本模块最不显然的一处设计）

重建的**难点不在「怎么写」，而在「写去哪儿」**：入库管线（MOD-IB-13）从
`ProjectRecord.active_collection_version` 推导 collection 名，而重建期间该值**必须仍是旧版本**
（③要求读路径不变）。若不做处理，重建写出的向量会落进**旧集合**，随后把 active 切到
一个**空的目标集合** —— 结果是「切换成功后检索全空」，且没有任何异常提示。

解法不引入新端口：把「写路径的 `ProjectRecord` 提供者」与「读路径的提供者」**在组合根分开装配**
（`RebuildAwareProjectProvider` 包住基础 provider，仅在存在未完成重建任务时把
`active_collection_version` 替换为任务的目标版本）。于是：
  * **写路径**（MOD-IB-13 的 `project_provider`）→ 重建期间指向目标版本，且
    `mark_indexed` 记录的 `indexed_collection_version` 也就是目标版本（供 AC-IB-16-02 的
    「重跑跳过已达目标版本的文档」判定）；
  * **读路径**（MOD-IB-15 的 `project_provider`）→ 始终指向台账 active 版本（AC-IB-16-03）。
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from ib.core import (
    ConflictError,
    DependencyUnavailableError,
    NotFoundError,
    RebuildJob,
    RebuildPlan,
    RebuildProgress,
    RebuildState,
    Scope,
)

__all__ = [
    "RebuildService",
    "RebuildAwareProjectProvider",
    "fingerprint",
    "FINGERPRINT_FACTORS",
    "RebuildState",
]

#: 指纹参与因子（顺序**有意固定**：改变顺序会改变所有历史指纹，必须视为破坏性变更）。
FINGERPRINT_FACTORS = (
    "model_id",
    "dim",
    "chunk_size",
    "chunk_overlap",
    "parser_version",
    "normalizer_version",
    "schema_version",
)

#: 指纹前缀长度（IFC-IB-156 规定取前 8 位十六进制）。
FINGERPRINT_LEN = 8

#: 重建任务的**未完成**状态集合（用于判定是否处于重建中）。
#: `planned` 是 `RebuildState` 的初态（枚举里**没有** `pending` —— 那是文档状态，见 D-4a）。
IN_FLIGHT_REBUILD_STATES = ("planned", "running")

#: 重建任务的事件间隔：任务级租约 600s > 单批最长处理时间，避免同批被两个 worker 抢。
REBUILD_LEASE_SECONDS = 600


def fingerprint(
    model_id: str,
    dim: int,
    chunk_size: int,
    chunk_overlap: int,
    parser_version: str,
    normalizer_version: str,
    schema_version: int,
) -> str:
    """索引指纹（IFC-IB-156，**纯函数**，可离线单测）。

    指纹回答的是唯一一个问题：**「当前配置是否与旧索引自洽？」**
    因此只纳入**会改变向量语义**的因子 —— 其中任一项变化，旧向量都不可复用：
      * 模型/维度：换模型即换向量空间（即使维度相同也不可复用）；
      * 切分参数：块边界变了，块内容与数量都变；
      * 解析器/归一化版本：同样的字节可能抽出不同的文本；
      * `schema_version`：payload 结构变更会使旧点的字段语义漂移。

    刻意**不**纳入：`top_k`、`score_threshold`、`collection_version` —— 它们是**查询期**参数
    或重建的**产物**，纳入会让「仅调检索阈值」触发一次全量重建（昂贵且无收益）。

    拼接采用 `key=value` + `\\x1f`（ASCII 单元分隔符）而非逗号：值里若含逗号会让
    `("a,b","c")` 与 `("a","b,c")` 撞成同一串 —— 用不可打印分隔符消除该歧义。
    """
    parts = [
        f"model_id={model_id}",
        f"dim={int(dim)}",
        f"chunk_size={int(chunk_size)}",
        f"chunk_overlap={int(chunk_overlap)}",
        f"parser_version={parser_version}",
        f"normalizer_version={normalizer_version}",
        f"schema_version={int(schema_version)}",
    ]
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return digest[:FINGERPRINT_LEN]


class RebuildAwareProjectProvider:
    """写路径的 `ProjectRecord` 提供者（见模块文档「写路径 vs 读路径」）。

    行为：若该项目存在 `pending`/`running` 的重建任务，则返回的 `ProjectRecord` 的
    `active_collection_version` 被替换为**任务的目标版本**；否则原样返回。

    为什么读的是**任务行**而不是新增一个「当前目标版本」字段：`rebuild_jobs` 表已在
    冻结的表结构里（`UNIQUE(project_id, to_version)`），且任务生命周期与「是否应重定向」
    完全同步（切完即 `activated`，重定向自动失效）—— 少一份需要同步的状态。
    """

    def __init__(self, ledger: Any, base_provider: Callable[[str], Any]) -> None:
        self._ledger = ledger
        self._base_provider = base_provider

    def __call__(self, project_id: str) -> Any:
        project = self._base_provider(project_id)
        target = self.target_version(project_id)
        if target is None:
            return project
        import dataclasses

        return dataclasses.replace(project, active_collection_version=target)

    def target_version(self, project_id: str) -> str | None:
        """当前正在进行的重建目标版本；无则 `None`。"""
        for job in self._ledger.list_rebuild_jobs(project_id):
            if str(job.state) in IN_FLIGHT_REBUILD_STATES:
                return str(job.to_version)
        return None


class RebuildService:
    """重建编排（IFC-IB-151~155）。

    依赖经构造期注入：台账（`LedgerRepository` + `RebuildJobStore`）、向量库（`VectorStore`）、
    以及**入库管线**（MOD-IB-13）。复用 13 意味着重建不需要第二套解析/切分/入库逻辑 ——
    这正是「重建 = 用新配置重跑一遍入库」这一朴素定义在代码上的直接体现。
    """

    def __init__(
        self,
        *,
        ledger: Any,
        vectors: Any,
        lifecycle: Any,
        resolver: Any,
        project_provider: Callable[[str], Any],
        current_factors: Callable[[], dict[str, Any]],
        batch_limit: int = 50,
    ) -> None:
        self._ledger = ledger
        self._vectors = vectors
        self._lifecycle = lifecycle
        self._resolver = resolver
        #: **写路径**提供者（应为 `RebuildAwareProjectProvider`），与读路径分离装配。
        self._project_provider = project_provider
        #: 返回**当前生效**的因子字典（由组合根从配置构造）—— 与历史指纹比对。
        self._current_factors = current_factors
        self._batch_limit = batch_limit

    # ================================================================== #
    # IFC-IB-151 计划
    # ================================================================== #

    def plan_rebuild(self, project_id: str) -> RebuildPlan:
        """算指纹、定新版本号、给出待重建文档数（**只规划，不改任何状态**）。

        `to_version` 取「当前 active + 1」而不是时间戳：版本号需要**单调可读**
        （`v1 → v2 → v3` 一眼看出先后），且只有递增整数才能保证「字典序 == 时间序」
        （时间戳字符串虽定长可比，但会出现「同一秒两次重建」的冲突）。
        """
        project = self._base_project(project_id)
        from_version = str(self._ledger.active_collection_version(project_id))
        to_version = str(int(from_version) + 1)
        target_collection = f"ib_{project_id}_v{to_version}"
        # 唯一入口：目标 collection 名必须经 CollectionResolver 认可（FM-5 前缀一致性）
        active = self._resolver.resolve(Scope(project_id=project_id), project)
        if active != f"ib_{project_id}_v{from_version}":
            raise DependencyUnavailableError(
                "台账 active 版本与 CollectionResolver 推导结果不一致（FM-5）",
                dependency="ledger",
            )
        self._resolver.assert_prefix(target_collection, project_id)
        return RebuildPlan(
            from_version=from_version,
            to_version=to_version,
            target_collection=target_collection,
            doc_count=self._count(project_id, status=None),
            changed_factors=self._changed_factors(project, to_version),
        )

    def _base_project(self, project_id: str) -> Any:
        """取**基础**（不带重建重定向）项目记录，用于推导「当前 active 集合」。"""
        project = self._project_provider(project_id)
        target = self._target_of(project_id)
        if target is not None:
            return self._without_redirect(project, target)
        return project

    def _target_of(self, project_id: str) -> str | None:
        for job in self._ledger.list_rebuild_jobs(project_id):
            if str(job.state) in IN_FLIGHT_REBUILD_STATES:
                return str(job.to_version)
        return None

    @staticmethod
    def _without_redirect(project: Any, redirect_version: str) -> Any:
        """把被重定向的 `active_collection_version` 还原为「重定向版本的上一版」。

        重建是「active + 1」生成的，故上一版即 `int(redirect) - 1` —— 无需回溯历史。
        """
        import dataclasses

        return dataclasses.replace(
            project, active_collection_version=str(int(redirect_version) - 1)
        )

    def _changed_factors(self, project: Any, to_version: str) -> list[str]:
        """与**目标集合的既有 spec** 比对，给出确凿可判定的变化因子。

        诚实原则：无法判定的因子**不臆造**（返回空列表即「无确凿变化」）。
        调用方据指纹决定是否真的需要重建；本方法不代替该判断。
        """
        factors = dict(self._current_factors())
        info = self._vectors.collection_info(_spec(project, f"ib_{project.project_id}_v{to_version}"))
        if info is None:
            return []
        changed: list[str] = []
        if "dim" in factors and int(factors["dim"]) != int(info.dim):
            changed.append("dim")
        return changed

    # ================================================================== #
    # IFC-IB-152 启动
    # ================================================================== #

    def start_rebuild(self, project_id: str, plan: RebuildPlan) -> RebuildJob:
        """建目标 collection + 建任务行。**幂等**（§6.2：`(project_id, to_version)` 唯一）。

        **先建 collection 再建任务**：反过来的话，任务一旦被 worker 认领却发现集合不存在，
        会以「每篇文档都失败」的形式收场（噪音大且难判因）。
        """
        existing = self._ledger.find_rebuild_job(project_id, plan.to_version)
        if existing is not None:
            # 同一目标版本重复启动 → **幂等返回同一任务行**，不重开（§6.2 唯一键；
            # 使「重建可中断可恢复」在任务层面也是幂等的，AC-IB-16-02）。
            return RebuildJob(job_id=existing.job_id, state=str(existing.state))
        if self._target_of(project_id) is not None:
            # 不同目标版本且仍在进行中 → 真冲突：并发重建会同时写两个目标集合，
            # 切换时后到者胜出，前者成为无人认领的孤儿集合。
            raise ConflictError("该项目已有进行中的重建任务（目标版本不同），拒绝并发启动")
        project = self._base_project(project_id)
        target_spec = _spec(project, plan.target_collection)
        self._vectors.ensure_collection(target_spec)

        job = self._ledger.create_rebuild_job(
            project_id=project_id,
            from_version=plan.from_version,
            to_version=plan.to_version,
            target_collection=plan.target_collection,
            doc_count=plan.doc_count,
        )
        # D-4b：把已 indexed/failed 的文档重置回 pending 并标记目标版本。否则 worker
        # 认领不到任何文档，`done` 判据还会被旧 indexed 计数骗成假阳性（目标集合空）。
        self._ledger.reset_documents_for_rebuild(project_id, plan.to_version)
        return RebuildJob(job_id=job.job_id, state=str(job.state))

    # ================================================================== #
    # IFC-IB-153 步进
    # ================================================================== #

    def step_rebuild(self, job: RebuildJob, lease_owner: str, limit: int) -> RebuildProgress:
        """认领任务并推进一批文档。**单文档失败不中断**，只记账。

        返回的 `pending` 是「该项目仍未完成的文档数」；`done` 为真表示「可以切换了」，
        但本方法**不**自己调用 `activate_version`：切换是**决策**而非**步骤**，
        由显式调用触发，避免「某一次恰好凑齐就自动切换」的隐式行为（运维需要一个确认点）。

        续租：重入 `claim_rebuild_job`（非终态即重新写入租约）—— 冻结端口没有独立的
        `renew_rebuild_lease`，重入 claim 是等价且更少的 API 面。
        """
        claimed = self._ledger.claim_rebuild_job(job.job_id, lease_owner, REBUILD_LEASE_SECONDS)
        if not claimed:
            row = self._ledger.get_rebuild_job(job.job_id)
            if row is None:
                raise NotFoundError("重建任务不存在")
            return RebuildProgress(
                indexed=self._count(row.project_id, status="indexed"),
                failed=self._count(row.project_id, status="failed"),
                pending=self._count(row.project_id, status="pending"),
                done=str(row.state) not in IN_FLIGHT_REBUILD_STATES,
            )

        row = self._ledger.get_rebuild_job(job.job_id)
        project_id = row.project_id
        # 驱动入库管线（写路径 provider 会把目标版本重定向进 ProjectRecord）。
        # 注：入库队列是**全局**的（IFC-IB-143 无项目参数），本步可能顺带推进其他项目的待
        # 索引文档 —— 那不是错误：每篇文档都按自己的项目/active 版本落库（见 code_review MINOR-03）。
        self._lifecycle.process_pending(lease_owner, min(max(1, limit), self._batch_limit))
        # 续租（等价的重新认领）
        self._ledger.claim_rebuild_job(job.job_id, lease_owner, REBUILD_LEASE_SECONDS)

        indexed = self._count(project_id, status="indexed")
        failed = self._count(project_id, status="failed")
        pending = self._count(project_id, status="pending") + self._count(
            project_id, status="parsing"
        )
        done = failed == 0 and pending == 0 and indexed > 0
        if done:
            self._ledger.set_rebuild_state(job.job_id, "succeeded")
        return RebuildProgress(indexed=indexed, failed=failed, pending=pending, done=done)

    def _count(self, project_id: str, *, status: str | None) -> int:
        """统计该项目下处于 `status` 的**未删除**文档数（`status=None` 为全部）。"""
        _, total = self._ledger.list_documents(
            Scope(project_id=project_id), page=1, page_size=1, status=status
        )
        return total

    # ================================================================== #
    # IFC-IB-154 原子切换
    # ================================================================== #

    def activate_version(self, project_id: str, version: str) -> None:
        """把 active 版本切到 `version`（**台账单值写入 = 原子切换**，ADR-05:235）。

        守卫（缺一不可）：
          1. 目标集合**必须已存在**（否则切过去就是个空集合 —— 最危险的一类静默故障）；
          2. 该项目**不得有 `failed` 文档**（AC-IB-16-04：单文档失败即不切换）；
          3. 不得有仍在 `pending`/`parsing` 的文档（切换即声明「已完整」）。

        切换后写路径立即打向新集合、读路径立即读新集合 —— **不存在混合读窗口**，
        因为读路径每次都是从台账读 `active_collection_version` 再经 resolver 推导集合名。
        """
        project = self._base_project(project_id)
        collection = f"ib_{project_id}_v{version}"
        self._resolver.assert_prefix(collection, project_id)
        if self._vectors.collection_info(_spec(project, collection)) is None:
            raise DependencyUnavailableError(
                f"目标 collection {collection} 不存在，拒绝切换（切换即完整）",
                dependency="vectorstore",
            )
        failed = self._count(project_id, status="failed")
        if failed:
            raise ConflictError(f"存在 {failed} 篇失败文档，拒绝切换版本（AC-IB-16-04）")
        unfinished = self._count(project_id, status="pending") + self._count(
            project_id, status="parsing"
        )
        if unfinished:
            raise ConflictError(f"仍有 {unfinished} 篇文档未完成索引，拒绝切换版本")
        # 台账单值切换：读路径的**唯一**真源（IFC-IB-129）
        self._ledger.activate_collection_version(project_id, version)
        job = self._ledger.find_rebuild_job(project_id, version)
        if job is not None:
            self._ledger.set_rebuild_state(job.job_id, "activated")

    # ================================================================== #
    # IFC-IB-155 回滚
    # ================================================================== #

    def rollback(self, project_id: str, version: str) -> None:
        """回滚 = 把 active 指回旧版本。

        因为重建**从不删除旧集合**，回滚不需要重新索引（O(1)）。这就是「新集合 + 原子切换」
        相对「就地覆盖」的最大运维收益：切错了可以立刻退回去，且新旧数据都在。
        """
        project = self._base_project(project_id)
        collection = f"ib_{project_id}_v{version}"
        self._resolver.assert_prefix(collection, project_id)
        if self._vectors.collection_info(_spec(project, collection)) is None:
            raise NotFoundError(f"回滚目标 collection {collection} 不存在（已人工删除？）")
        self._ledger.activate_collection_version(project_id, version)
        from ib.observability import log_event

        log_event("rebuild", "rolled_back", project_id=project_id)
        # 把已完成/已切换的任务标记为 rolled_back（任务行是「是否应重定向写路径」的依据，
        # 若停留在 activated 会让写路径继续指向被回滚的版本 —— 必须一并收敛）。
        for job in self._ledger.list_rebuild_jobs(project_id):
            if str(job.state) in ("succeeded", "activated"):
                self._ledger.set_rebuild_state(job.job_id, "rolled_back")


# --------------------------------------------------------------------------- #
# 内部辅助
# --------------------------------------------------------------------------- #


def _spec(project: Any, collection: str) -> Any:
    """由项目记录 + 指定 collection 名派生 `CollectionSpec`（维度取自项目，不硬编码）。"""
    import dataclasses

    from ib.embedding import collection_spec_for

    return dataclasses.replace(collection_spec_for(project), collection=collection)
