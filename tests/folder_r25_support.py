"""[R25 / GROUP_D] 文件夹上传与云盘式目录管理 —— 测试公共助手（非用例文件，不以 test_ 开头）。

只提供**确定性、离线**的小工具：内存 / 临时目录 SQLite 装配、经真实上传管线入库、检索辅助、
HTTP（Django 测试客户端）助手。所有数据均为测试内造的占位文本，不含任何凭据。
"""

from __future__ import annotations

import io
import json
import os
from typing import Any, Iterable

TOKEN = os.environ.get("IB_OFFLINE_TOKEN", "groupd-offline-token")
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {TOKEN}"}
PID = "p_alpha"  # 离线令牌所属项目；资料库 kb_id ≡ project_id


def scope_of(project_id: str = PID):
    from ib.core import Scope

    return Scope(project_id=project_id, kb_ids=None)


def sqlite_deps(tmp_path, raw: dict | None = None, monkeypatch: Any = None):
    """以**真实 SQLite 台账 / 目录树 / 批次存储**（临时目录）+ 临时 blob 根装配 deps。

    离线模式 (`offline_mode=True`) 会把台账强制切回内存替身，因此这里关闭 offline_mode，并按
    “生产形态”注入账户体系所需的**测试占位**环境（内存账户后端 + 账户策略模块 + 占位初始口令，
    非任何生产凭据）；向量库 / 嵌入 / LLM 仍是 memory / fake 替身，不触网。
    """
    from conftest import R13_ADMIN_PASSWORD, offline_raw
    from ibweb.composition import build_deps

    assert monkeypatch is not None, "sqlite_deps 需要 monkeypatch 以设置并还原环境变量"
    for key, value in {
        "IB_ACCOUNT_BACKEND": "memory",
        "IB_AUTHZ_POLICY_MODULE": "ibweb.accounts.policy",
        "IB_DEFAULT_ADMIN_PASSWORD": R13_ADMIN_PASSWORD,
    }.items():
        monkeypatch.setenv(key, value)
    cfg = raw if raw is not None else offline_raw()
    cfg["offline_mode"] = False
    cfg["ledger_backend"] = "sqlite"
    cfg["ledger_path"] = str(tmp_path / "ledger.sqlite3")
    cfg["blob"] = {"enabled": True, "root": str(tmp_path / "blobs")}
    deps = build_deps(cfg, force=True)
    from ib.ledger.sqlite_repo import SqliteLedgerRepository

    assert isinstance(deps.ledger, SqliteLedgerRepository), "前置：必须是真实 SQLite 台账（否则 sqlite 参数化形同虚设）"
    return deps


def ctx_of(project_id: str = PID):
    from conftest import request_ctx

    return request_ctx(project_id)


def put_file(
    deps: Any,
    name: str,
    content: str | bytes,
    *,
    folder_id: str = "",
    rel_dirs: Iterable[str] = (),
    project_id: str = PID,
    process: bool = True,
    on_conflict: str = "fail",
):
    """经真实管线入库一个文件到目录（classify → submit_library_document → 可选 process_pending）。"""
    from ib.lifecycle import DocumentPlacement, RejectedUpload

    data = content.encode("utf-8") if isinstance(content, str) else content
    verdict = deps.lifecycle.classify_upload(name, len(data), data[:4096])
    assert not isinstance(verdict, RejectedUpload), verdict
    record = deps.lifecycle.submit_library_document(
        ctx_of(project_id),
        verdict,
        project_id,
        placement=DocumentPlacement(
            folder_id=folder_id, rel_dirs=tuple(rel_dirs), name=name, on_conflict=on_conflict  # type: ignore[arg-type]
        ),
        data=io.BytesIO(data),
    )
    if process:
        deps.lifecycle.process_pending("r25-worker", 50)
    return record


def update_file(deps: Any, doc_id: str, new_name: str, content: str | bytes, *, project_id: str = PID, on_conflict: str = "fail"):
    from ib.lifecycle import RejectedUpload

    data = content.encode("utf-8") if isinstance(content, str) else content
    verdict = deps.lifecycle.classify_upload(new_name, len(data), data[:4096])
    assert not isinstance(verdict, RejectedUpload), verdict
    return deps.lifecycle.submit_revision(
        ctx_of(project_id), doc_id, verdict, data=io.BytesIO(data), new_name=new_name, on_conflict=on_conflict  # type: ignore[arg-type]
    )


def get_doc(deps: Any, doc_id: str, project_id: str = PID):
    return deps.ledger.get_document(scope_of(project_id), doc_id)


def search(deps: Any, text: str, project_id: str = PID):
    from ib.core import Scope

    return deps.retrieval.search(text, scope=Scope(project_id=project_id, kb_ids=(project_id,)))


def hit_doc_ids(result: Any) -> list[str]:
    return [h.doc_id for h in result.hits]


def hits_containing(result: Any, needle: str) -> list[Any]:
    """命中正文含 needle 的命中（用于"旧关键词命中 0"类断言：fake 向量库阈值为 0，别的文档也会被召回）。"""
    return [h for h in result.hits if needle in (h.content or "")]


# --------------------------------------------------------------------------- #
# HTTP 助手（Django 测试客户端；离线共享令牌 → p_alpha，管理者）
# --------------------------------------------------------------------------- #


def jreq(client: Any, method: str, path: str, body: dict | None = None, headers: dict | None = None):
    h = dict(AUTH if headers is None else headers)
    fn = getattr(client, method.lower())
    if body is None:
        return fn(path, **h)
    return fn(path, data=json.dumps(body), content_type="application/json", **h)


def jbody(resp: Any) -> dict:
    return json.loads(resp.content)


def put_multipart(client: Any, path: str, name: str, payload: bytes, headers: dict | None = None, content_type: str = "application/octet-stream"):
    """`PUT` multipart（Django 测试客户端对 PUT 不自动编码 multipart，需手工 encode_multipart）。"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

    body = encode_multipart(BOUNDARY, {"file": SimpleUploadedFile(name, payload, content_type=content_type)})
    return client.put(path, data=body, content_type=MULTIPART_CONTENT, **(AUTH if headers is None else headers))


def upload_batch(client: Any, files: dict[str, bytes], *, target: str = "", resolutions: dict | None = None, declared: dict[str, int] | None = None, headers: dict | None = None):
    """走 HTTP：计划(commit) → 逐文件 PUT。返回 (plan_resp_body, [item_resp_body...], batch_id)。"""
    entries = [
        {"client_idx": i, "rel_path": rel, "size": (declared or {}).get(rel, len(data))}
        for i, (rel, data) in enumerate(files.items())
    ]
    plan = jreq(
        client,
        "POST",
        "/api/uploads",
        {"target_folder_id": target, "dry_run": False, "entries": entries, "resolutions": resolutions or {}},
        headers,
    )
    assert plan.status_code == 201, plan.content
    body = jbody(plan)
    results = []
    for i, (rel, data) in enumerate(files.items()):
        name = rel.split("/")[-1]
        r = put_multipart(client, f"/api/uploads/{body['batch_id']}/items/{i}", name, data, headers)
        assert r.status_code == 200, r.content
        results.append(jbody(r))
    return body, results, body["batch_id"]


def browse(client: Any, folder_id: str = "", headers: dict | None = None, **query: Any) -> dict:
    qs = "&".join([f"folder_id={folder_id}"] + [f"{k}={v}" for k, v in query.items()])
    r = jreq(client, "GET", f"/api/library?{qs}", None, headers)
    assert r.status_code == 200, r.content
    return jbody(r)


def names_in(listing: dict, kind: str | None = None) -> list[str]:
    return [i["name"] for i in listing["items"] if kind is None or i["kind"] == kind]


def find_item(listing: dict, name: str) -> dict:
    for item in listing["items"]:
        if item["name"] == name:
            return item
    raise AssertionError(f"目录中无条目 {name!r}：{names_in(listing)}")


# --------------------------------------------------------------------------- #
# 可控时钟（台账时间戳是秒级 UTC；用例需要“T5 晚于 T2”时不依赖 sleep）
# --------------------------------------------------------------------------- #


class Clock:
    def __init__(self, start: str) -> None:
        from datetime import datetime, timezone

        self._t = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def now(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def tick(self, seconds: int = 60) -> str:
        from datetime import timedelta

        self._t += timedelta(seconds=seconds)
        return self.now()


def install_clock(monkeypatch: Any, start: str = "2026-03-01T00:00:00Z") -> Clock:
    """把所有 `ib.*` / `ibweb.*` 模块里的 `utc_now_iso` 换成可控时钟（teardown 由 monkeypatch 还原）。"""
    import sys

    clock = Clock(start)
    for name, module in list(sys.modules.items()):
        if module is not None and (name == "ib" or name.startswith(("ib.", "ibweb"))) and hasattr(module, "utc_now_iso"):
            monkeypatch.setattr(module, "utc_now_iso", clock.now)
    return clock


class FailingEmbedder:
    """包装真实 embedder：`embed_documents` 恒失败（模拟新版“解析 / 索引失败”），查询向量化照常。"""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def embed_documents(self, texts, *, timeout_s, max_retries, batch_size):
        raise RuntimeError("r25 注入：入库依赖故障")

    def embed_query(self, text, *, timeout_s):
        return self._inner.embed_query(text, timeout_s=timeout_s)

    def model_id(self):
        return self._inner.model_id()

    def dim(self):
        return self._inner.dim()

    def health(self):
        return self._inner.health()
