# MOD-R26-13 / implements IFC-R26-121：草稿副本服务（owner 隔离；每人每项目 <=10；单个 <=1 MiB）
from __future__ import annotations

from typing import Callable

from ib.core import ConfigDraftStore, DraftRecord

DRAFT_MAX_PER_OWNER = 10


class ConfigDraftService:
    """草稿是用户显式的服务端副本，**不是载入源**（ADR-59）：运行期与发布路径从不读取它。"""

    def __init__(self, *, store: ConfigDraftStore, clock: Callable[[], str]) -> None:
        self._store = store
        self._clock = clock

    def save(self, project_id: str, owner: str, *, label: str, base_version: int, payload_json: str) -> DraftRecord:
        return self._store.save(
            project_id,
            owner,
            label=label,
            base_version=int(base_version),
            payload_json=payload_json,
            now=self._clock(),
            max_per_owner=DRAFT_MAX_PER_OWNER,
        )

    def list(self, project_id: str, owner: str) -> tuple[DraftRecord, ...]:
        return self._store.list(project_id, owner)

    def load(self, project_id: str, owner: str, draft_id: str) -> tuple[DraftRecord, str] | None:
        return self._store.load(project_id, owner, draft_id)

    def delete(self, project_id: str, owner: str, draft_id: str) -> bool:
        return self._store.delete(project_id, owner, draft_id)
