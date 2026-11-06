"""REV-29（MCP 外部工具适配）测试的公共构造助手（离线；无外网；无真实凭据）。

测试目录无 `__init__.py`，基名须全局唯一；由 tests/conftest.py 把 tests/ 置于 sys.path，
以 `from mcp_r29_support import ...` 导入（同 advisor_r28_support.py / config_r26_support.py 做法）。

测试替身（均为替身，不改产品代码）：
  * `FakeMcpServer` / `FakeMcpTransport` / `FakeResolver`：产品自带的离线替身（src/ib/mcp/double.py）；
  * `Harness`：在已装配的 `deps.mcp` 上，经**真实 HTTP 管理端点**登记 / 验证 / 启用 / 审核 / 开放 Server；
  * 凭证主密钥：测试内生成的合法 Fernet 密钥形态（urlsafe-base64 的 32 字节常量），**非真实密钥**；
    cryptography 未安装 ⇒ 产品 make_secret_cipher(offline=True) 回落 ReversibleTestCipher（报告记账 cipher=test）。
"""

from __future__ import annotations

import base64
import json
import time as _time
from typing import Any, Mapping, Sequence

from advisor_r28_support import P, SEARCH, advisor_document, advisor_prompts, build_app  # noqa: F401
from config_r26_support import Api, publish_body  # noqa: F401

#: 合法 Fernet 形态的测试占位主密钥（32 个 'k'）；非真实密钥
SECRET_KEY = base64.urlsafe_b64encode(b"k" * 32).decode()
#: 测试占位令牌（canary：流程结束后在日志 / 审计 / 响应 / 台账明文中命中数必须为 0）
CANARY_TOKEN = "CANARY-TOKEN-r29-7f3a91c2d4"
PUBLIC_IP = "93.184.216.34"


def tool(name: str = "search", *, desc: str = "查询客户资料", props: Mapping[str, Any] | None = None,
         required: Sequence[str] = ("q",), annotations: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    """一个 MCP 工具描述（服务方 tools/list 的一项）。"""
    properties = dict(props) if props is not None else {"q": {"type": "string"}}
    t: dict[str, Any] = {
        "name": name,
        "description": desc,
        "inputSchema": {"type": "object", "properties": properties, "required": list(required)},
    }
    if annotations is not None:
        t["annotations"] = dict(annotations)
    t.update(extra)
    return t


class Harness:
    """HTTP 层夹具：登记 → 凭证 → 验证 / 启用 → 审核 → 开放 → 授权发布，全程走产品真实端点。"""

    def __init__(self, deps: Any, api: Api):
        self.deps, self.api, self.b = deps, api, deps.mcp
        self.servers: dict[str, Any] = {}
        self.wire: list[bytes] = []  # 本夹具 API 客户端收到的全部响应体（canary 全流程扫描用）
        real = api.call

        def recording(method, path, who="admin", body=None, project="p_alpha", force_header=False):
            resp = real(method, path, who, body, project, force_header)
            try:
                self.wire.append(bytes(resp.content))
            except Exception:  # noqa: BLE001 - SSE 流式响应无 content
                pass
            return resp

        api.call = recording  # type: ignore[method-assign]

    # -- Server ------------------------------------------------------------ #
    def add(self, server_id: str = "crm", tools: Sequence[Mapping[str, Any]] | None = None, *, era: str = "modern",
            bearer: str | None = CANARY_TOKEN, host: str | None = None, scope: str = "shared", list_changed: bool = False,
            page_size: int = 100, auth: str | None = None, project_cred: str | None = None) -> Any:
        """在 deps.mcp 的传输替身上挂一个 FakeMcpServer 并经 HTTP 登记（不含启用）。"""
        from ib.mcp.double import FakeMcpServer

        host = host or f"{server_id}.example.com"
        url = f"https://{host}/mcp"
        srv = FakeMcpServer(era=era, tools=list(tools if tools is not None else [tool()]), page_size=page_size,
                            required_bearer=bearer, list_changed=list_changed)  # type: ignore[arg-type]
        self.b.resolver.set(host, [PUBLIC_IP])
        self.b.transport.add_server(url, srv)
        kind = auth or ("bearer" if bearer else "none")
        body: dict[str, Any] = {"server_id": server_id, "description": f"{server_id} 测试服务",
                                "transport": "streamable_http", "endpoint_url": url, "auth_kind": kind,
                                "data_categories": ["query_text"], "credential_scope": scope}
        r = self.api.post("/api/mcp/servers", body)
        assert r.status_code == 201, (r.status_code, r.json_body)
        if bearer and kind != "none":
            if scope == "shared":
                rc = self.api.put(f"/api/mcp/servers/{server_id}/credentials", {"scope": "shared", "secret": bearer})
            else:
                rc = self.api.put(f"/api/mcp/servers/{server_id}/credentials", {"scope": "discovery", "secret": bearer})
            assert rc.status_code == 200, rc.json_body
        self.servers[server_id] = srv
        return srv

    def enable(self, server_id: str = "crm") -> dict:
        r = self.api.post(f"/api/mcp/servers/{server_id}/enable")
        assert r.status_code == 200, (r.status_code, r.json_body)
        return r.json_body

    def tools(self, server_id: str | None = None, **flt: str) -> list[dict]:
        q = "&".join(f"{k}={v}" for k, v in ({"server_id": server_id, **flt} if server_id else flt).items())
        r = self.api.get("/api/mcp/tools" + (f"?{q}" if q else ""))
        assert r.status_code == 200, r.json_body
        return r.json_body["items"]

    def tool_id(self, local_name: str) -> int:
        for t in self.tools():
            if t["local_name"] == local_name:
                return int(t["tool_id"])
        raise AssertionError(f"工具不存在：{local_name}")

    def approve(self, local_name: str, risk: str = "read_only", *, hidden: Sequence[str] = (), ack: bool = False) -> dict:
        tid = self.tool_id(local_name)
        det = self.api.get(f"/api/mcp/tools/{tid}").json_body
        r = self.api.post(f"/api/mcp/tools/{tid}/review", {
            "decision": "approve", "expected_fingerprint": det["observed"]["fingerprint"], "risk": risk,
            "hidden_params": list(hidden), "ack_tenant_params": ack})
        assert r.status_code == 200, (r.status_code, r.json_body)
        return r.json_body

    def open(self, server_id: str, projects: Sequence[str] = (P,), *, open_all: bool = False) -> None:
        r = self.api.put(f"/api/mcp/servers/{server_id}/open", {"open_all": open_all, "project_ids": list(projects)})
        assert r.status_code == 200, r.json_body

    def ready(self, server_id: str = "crm", tools: Sequence[Mapping[str, Any]] | None = None, *,
              projects: Sequence[str] = (P,), risk: str = "read_only", **kw: Any) -> Any:
        """登记 + 启用 + 逐个审核通过 + 开放给 projects。返回 FakeMcpServer。"""
        srv = self.add(server_id, tools, **kw)
        self.enable(server_id)
        for t in self.tools(server_id):
            if t["state"] == "pending_review":
                self.approve(t["local_name"], risk)
        self.open(server_id, projects)
        return srv

    # -- 授权 -------------------------------------------------------------- #
    def grant(self, project: str = P, **by_expert: Sequence[str]) -> Any:
        """直接经发布服务发布 v2 文档（kb-agent / advisor 等授权）。by_expert: {'kb_agent': (...)}。"""
        from advisor_r28_support import publish_advisor

        grants = {k.replace("_", "-"): tuple(v) for k, v in by_expert.items()}
        return publish_advisor(self.deps, project, grants=grants)

    def publish_http(self, grants: Mapping[str, Sequence[str]], *, who: str = "admin", project: str = P):
        """经 HTTP 发布（用于校验失败分支）。grants: {专家名: 工具元组}。"""
        doc = advisor_document(project, grants={k: tuple(v) for k, v in grants.items()})
        base = self.api.get("/api/config/status", who=who, project=project).json_body["version"]
        return self.api.post("/api/config/publish", publish_body(doc, base, advisor_prompts()), who=who, project=project,
                             force_header=True), doc

    def invoke(self, local_name: str, args: Mapping[str, Any] | None = None, *, project: str = P, turn: str | None = None,
               timeout: int = 30, cap: int = 5, actor: str = "u1") -> Any:
        """直接用运行时调用器调用一次（不经 LLM）：用于黑盒验证“某状态下出站是否为 0”。"""
        import uuid

        from ib.mcp.runtime import ExternalToolBinding, bind_mcp_turn

        rec = self.b.stores.tools.get_by_local_name(local_name)
        snap = rec.approved or rec.observed
        bnd = ExternalToolBinding(project_id=project, local_name=rec.local_name, display_name=rec.display_name, server_id=rec.server_id,
                                  remote_name=rec.remote_name, bound_fingerprint=snap.fingerprint, input_schema=snap.input_schema, trial=False)
        with bind_mcp_turn({"turn_id": turn or uuid.uuid4().hex, "actor_id": actor}):
            return self.b.invoker.invoke(bnd, args if args is not None else {"q": "x"}, mcp_timeout_s=timeout, mcp_max_calls_per_turn=cap)

    @staticmethod
    def n_calls(srv: Any, name: str | None = None) -> int:
        return len([r for r in srv.request_log if r.method == "tools/call" and (name is None or r.name == name)])

    def enable_runtime_projects(self, monkeypatch: Any, tmp_path: Any) -> None:
        """让 POST /api/projects 可用：定义文档改用文件型存储（离线内存存储不含运行期新建项目）。同 R28 TC-E2E-R28-003 做法。"""
        import os

        from ib.config import FileDefinitionDocumentStore
        from ibweb.composition import known_tool_names

        monkeypatch.setenv("IB_DEFINITION_DOC_PATH", str(tmp_path / "defs"))
        monkeypatch.setenv("IB_EXPERT_PROMPT_DIR", str(tmp_path / "prompts"))
        os.makedirs(tmp_path / "defs", exist_ok=True)
        old = self.deps.definition_store
        new = FileDefinitionDocumentStore(str(tmp_path / "defs"), known_tools=known_tool_names())
        for pid in list(self.deps.projects):  # 既有项目的当前定义文档迁入文件型存储（GrantIndex 遍历全部活动项目）
            new.save(pid, old.load(pid), expected_content_hash=None)
        self.deps.definition_store = new

    def create_project(self, project_id: str, *, advisor: bool = False) -> None:
        """admin 运行期新建项目并补种子提示词（离线提示词库为内存态：经提示词端口写入，等价生产 Fs 目录）。"""
        from ib.config import advisor_seed_prompt, kb_agent_seed_prompt

        r = self.api.post("/api/projects", {"project_id": project_id, "name": f"运行期项目 {project_id}", "enable_advisor": advisor})
        assert r.status_code == 201, r.content
        store = self.deps.prompt_stores[project_id]
        store.save_layer("kb-agent", "main", kb_agent_seed_prompt(), expected_hash=None)
        if advisor:
            store.save_layer("advisor", "main", advisor_seed_prompt(), expected_hash=None)

    def settle(self, project: str = P, timeout: float = 5.0) -> None:
        """等待该项目的后台重编译（admin 操作触发的 refresh_async）结束，再同步刷新一次，消除“后台线程 vs 断言”的竞态。"""
        cache = self.deps.runtime_cache
        end = _time.monotonic() + timeout
        while _time.monotonic() < end:
            ent = cache._entries.get(project)  # 只读观测缓存内部的“编译中”标志；不改判定逻辑
            if ent is None or not ent.building:
                break
            _time.sleep(0.02)
        cache.refresh_now(project)

    def audit_rows(self, **flt: Any) -> list:
        return list(self.b.stores.audit.query(limit=500, offset=0, **{k: flt.get(k) for k in (
            "server_id", "tool_name", "project_id", "kind", "ts_from", "ts_to")}))


def make_harness(monkeypatch, *, secret: bool = True, raw_extra: Mapping[str, Any] | None = None, **env: str) -> Harness:
    """装配账户体系 deps（含 MCP 离线运行时）+ admin/编辑/查看账号 + Harness。raw_extra：并入配置字典的键（如 mcp_enabled）。"""
    from advisor_r28_support import app_env
    from conftest import _build_accounts_app, offline_raw

    e = dict(env)
    if secret:
        e.setdefault("IB_MCP_SECRET_KEY", SECRET_KEY)
    raw = offline_raw()
    raw.update(dict(raw_extra or {}))
    deps, Client = _build_accounts_app(monkeypatch, raw, app_env(monkeypatch, **e))
    api = Api(deps, Client)
    api.add_user("editor", P, "edit")
    api.add_user("viewer", P, "view")
    api.add_user("ed_beta", "p_beta", "edit")
    api.add_user("mgr_alpha", P, "manage")
    api.add_user("mgr_beta", "p_beta", "manage")
    return Harness(deps, api)


def dumps_all(*objs: Any) -> str:
    """把若干对象序列化为一个大字符串（用于 canary 命中数检查）。"""
    out = []
    for o in objs:
        if isinstance(o, (bytes, bytearray)):
            out.append(bytes(o).decode("utf-8", "replace"))
        elif isinstance(o, str):
            out.append(o)
        else:
            out.append(json.dumps(o, ensure_ascii=False, default=str))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# 无 Django 的"世界"：存储 + 替身 Server + 客户端 + 调用器 + 目录服务（单元 / 集成用）
# --------------------------------------------------------------------------- #

import time as _time


class World:
    """离线最小世界：内存 SQLite 存储 + FakeMcpServer + FakeMcpTransport + McpClient + McpInvoker + McpCatalogService。

    不经 HTTP 与组合根，直接装配产品类（真实实现，仅传输 / 解析器 / 密码器为替身）。
    """

    def __init__(self, tools: Sequence[Mapping[str, Any]] | None = None, *, era: str = "modern", bearer: str | None = CANARY_TOKEN,
                 server_id: str = "crm", list_changed: bool = False, page_size: int = 100, transport_cls: Any = None,
                 clock: Any = None, scope: str = "shared", allow: frozenset = frozenset()):
        from ib.core.types import McpServer, McpServerLimits
        from ib.ledger.mcp_store import build_mcp_stores
        from ib.mcp.catalog import McpCatalogService
        from ib.mcp.client import McpClient
        from ib.mcp.crypto import Secret
        from ib.mcp.double import FakeMcpServer, FakeMcpTransport, FakeResolver, ReversibleTestCipher
        from ib.mcp.runtime import McpBreaker, McpInvoker
        from ib.webtools.netguard import DomainRules

        import uuid

        self.uid = uuid.uuid4().hex[:8]  # 回合登记簿是进程级的：回合 id 必须按世界唯一化，避免用例间串用预算
        self.server_id = server_id
        self.url = f"https://{server_id}.example.com/mcp"
        self.stores = build_mcp_stores(None, backend="memory")
        self.cipher = ReversibleTestCipher(SECRET_KEY)
        self.resolver = FakeResolver({f"{server_id}.example.com": [PUBLIC_IP]})
        self.server = FakeMcpServer(era=era, tools=list(tools if tools is not None else [tool()]), required_bearer=bearer,  # type: ignore[arg-type]
                                    list_changed=list_changed, page_size=page_size)
        self.allow = allow
        cls = transport_cls or FakeMcpTransport
        self.transport = cls({self.url: self.server}, resolver=self.resolver,
                             rules_factory=lambda: (DomainRules((), ()), frozenset(self.allow)))
        self.client = McpClient(self.transport)
        self.breaker = McpBreaker()
        self.offset = 0.0
        self.clock = clock or (lambda: _time.monotonic() + self.offset)
        self.invoker = McpInvoker(stores=self.stores, cipher=self.cipher, client=self.client, breaker=self.breaker,
                                  clock=self.clock, enabled=True)
        self.changed: list[str] = []
        self.catalog = McpCatalogService(
            stores=self.stores, cipher=self.cipher, client=self.client, audit=self.stores.audit, clock=lambda: "2026-11-05T00:00:00Z",
            gov_reader=self.stores.governance.get, on_tools_changed=self.changed.append)
        auth = "bearer" if bearer else "none"
        self.stores.servers.create(McpServer(
            server_id, "d", "streamable_http", self.url, auth, None, scope, "platform", None, False, ("query_text",),
            "registered", "unknown", None, None, None, False, None, None, 0, McpServerLimits(),
            "2026-11-05T00:00:00Z", "t", "2026-11-05T00:00:00Z", "t"))
        if bearer:
            key = "@shared" if scope == "shared" else "@discovery"
            tok, kid = self.cipher.encrypt(Secret(bearer))
            self.stores.credentials.put(server_id, key, tok, kid, actor="t", now="2026-11-05T00:00:00Z")

    # -- 生命周期 ---------------------------------------------------------- #
    def go_live(self, projects: Sequence[str] = (P,), *, risk: str = "read_only", approve: bool = True) -> None:
        """验证 → 启用 → 刷新 → 审核全部 → 对 projects 开放。"""
        out = self.catalog.verify(self.server_id, actor="t")
        assert out.ok, out.category
        self.stores.servers.set_admin_state(self.server_id, "enabled", actor="t", now="2026-11-05T00:00:00Z")
        self.catalog.refresh(self.server_id, actor="t")
        if approve:
            for t in self.stores.tools.list(server_id=self.server_id):
                if t.state == "pending_review":
                    self.approve(t.tool_id, risk)
        self.stores.servers.set_open(self.server_id, open_all=False, project_ids=tuple(projects), actor="t", now="2026-11-05T00:00:00Z")

    def approve(self, tool_id: int, risk: str = "read_only", hidden: Sequence[str] = ()) -> Any:
        rec = self.stores.tools.get(tool_id)
        return self.catalog.approve(tool_id, expected_fingerprint=rec.observed.fingerprint, risk=risk, hidden_params=hidden,
                                    llm_description=None, ack_tenant_params=True, actor="t")

    def rec(self, remote: str = "search") -> Any:
        return self.stores.tools.get_by_local_name(f"mcp__{self.server_id}__{remote}")

    def binding(self, remote: str = "search", project: str = P, *, fingerprint: str | None = None) -> Any:
        from ib.mcp.runtime import ExternalToolBinding

        r = self.rec(remote)
        snap = r.approved or r.observed  # 未审核的工具没有 approved：用 observed 构造（模拟悬空 / 绕过的绑定）
        return ExternalToolBinding(project_id=project, local_name=r.local_name, display_name=r.display_name, server_id=self.server_id,
                                   remote_name=r.remote_name, bound_fingerprint=fingerprint or snap.fingerprint,
                                   input_schema=snap.input_schema, trial=False)

    def call(self, args: Mapping[str, Any] | None = None, *, remote: str = "search", project: str = P, turn: str | None = "t1",
             timeout: int = 30, cap: int = 5, actor: str = "u1") -> Any:
        """在一个用户回合作用域里调用一次（turn=None ⇒ 无作用域）。"""
        from contextlib import nullcontext

        from ib.mcp.runtime import bind_mcp_turn

        ctx = bind_mcp_turn({"turn_id": f"{self.uid}:{turn}", "actor_id": actor}) if turn is not None else nullcontext()
        with ctx:
            return self.invoker.invoke(self.binding(remote, project), args if args is not None else {"q": "x"},
                                       mcp_timeout_s=timeout, mcp_max_calls_per_turn=cap)

    def n_calls(self, name: str | None = None) -> int:
        return len([r for r in self.server.request_log if r.method == "tools/call" and (name is None or r.name == name)])

    def audit(self, **kw: Any) -> list:
        return list(self.stores.audit.query(limit=500, offset=0, **{k: kw.get(k) for k in (
            "server_id", "tool_name", "project_id", "kind", "ts_from", "ts_to")}))
