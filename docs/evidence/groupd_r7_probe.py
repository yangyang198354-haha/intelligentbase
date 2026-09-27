"""GROUP_D R7 探针：确认定义层/闸门/端点的**真实**行为（只读，不修改 src/）。

用途：在编写 R7 新增用例前，先探明实现行为（尤其「路由关键词撞车」「admit 聚合」等
任务书与实现之间可能存在的落差），避免把猜测写成断言。
"""

from __future__ import annotations

import inspect
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
sys.path.insert(0, str(_SRC))

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("IB_OFFLINE_MODE", "1")
os.environ.setdefault("IB_CONFIG_SOURCE", "dict")
os.environ.setdefault("IB_OFFLINE_TOKEN", "groupd-offline-token")
os.environ.setdefault("IB_LOG_LEVEL", "ERROR")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibweb.settings")

from ib.config import (  # noqa: E402
    InMemoryDefinitionDocumentStore,
    build_definition_document,
    editable_field_whitelist,
    non_editable_changes,
    validate,
)
from ib.core import (  # noqa: E402
    ConditionalEdgeSpec,
    ConfigError,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    ToolGrantSpec,
    ValidationReport,
)

KNOWN = frozenset({"search_knowledge"})


def _doc(**over):
    base = dict(
        project_id="p1",
        experts=(
            ExpertSpecInput("a", "A", ("alpha", "共同"), ("e1",), True, "prompt-a", False, True),
            ExpertSpecInput("b", "B", ("beta", "共同"), ("e2",), False, "prompt-b", False, False),
        ),
        route=RouteSpecInput(0.65, 0.05, 8, "a"),
        orchestration=OrchestrationSpecInput(("route", "a", "b"), (ConditionalEdgeSpec("route", (("a", "a"),)),)),
        tool_grants=(ToolGrantSpec("a", ("search_knowledge",)),),
    )
    base.update(over)
    return build_definition_document(**base)


print("== ValidationReport fields ==", set(ValidationReport.__dataclass_fields__))
print("== admit signature ==", inspect.signature(__import__("ibweb.composition", fromlist=["admit"]).admit))
print("== whitelist ==", sorted(editable_field_whitelist()))

good = _doc()
r = validate(good, known_tools=KNOWN)
print("== good.ok ==", r.ok, [e.code for e in r.errors])

# 1) 路由关键词撞车（AC-IB-18-02 列举项之一）
collide = _doc(
    experts=(
        ExpertSpecInput("a", "A", ("共同",), ("e1",), True, "p", False, True),
        ExpertSpecInput("b", "B", ("共同",), ("e2",), False, "p", False, False),
    )
)
rc = validate(collide, known_tools=KNOWN)
print("== keyword collision .ok ==", rc.ok, [e.code for e in rc.errors])

# 2) 非法项聚合（必填缺失 + 专家重复 + 默认专家两个 + 未知工具 + 阈值越界 + 条件边空）
bad = _doc(
    experts=(
        ExpertSpecInput("a", "A", ("k",), (), True, "p", False, True),
        ExpertSpecInput("a", "B", ("k",), (), False, "p", False, True),
    ),
    route=RouteSpecInput(1.5, 0.05, 0, "ghost"),
    tool_grants=(ToolGrantSpec("a", ("ghost-tool",)),),
)
rb = validate(bad, known_tools=KNOWN)
print("== bad ok ==", rb.ok)
print("== bad codes ==", sorted({e.code for e in rb.errors}))
print("== bad count ==", len(rb.errors))

# 3) admit 聚合 + validation_items
from ibweb.composition import admit  # noqa: E402

store = InMemoryDefinitionDocumentStore(known_tools=KNOWN)
try:
    admit(bad, store=store)
    print("== admit bad: DID NOT RAISE ==")
except ConfigError as exc:
    items = getattr(exc, "validation_items", None)
    print("== admit bad raised ConfigError ==")
    print("   n_errors_in_msg_suffix:", str(exc).count("["))
    print("   validation_items:", len(items) if items else items)

print("== admit good -> ==", type(admit(good, store=store)).__name__)

# 4) non_editable_changes
changed = _doc(
    orchestration=OrchestrationSpecInput(
        ("route", "a", "b", "evil"), (ConditionalEdgeSpec("route", (("a", "a"),)),)
    )
)
print("== non_editable(topology) ==", [i.code for i in non_editable_changes(good, changed)])
print("== non_editable(tau) ==", non_editable_changes(good, _doc(route=RouteSpecInput(0.7, 0.05, 8, "a"))))

# 5) build_deps 离线装配
from ibweb.composition import build_application, build_deps  # noqa: E402

OFFLINE_RAW = {
    "config_source": "dict",
    "offline_mode": True,
    "ledger_backend": "memory",
    "blob": {"enabled": True, "root": os.path.join(str(_SRC), ".groupd_blobs")},
    "retrieval": {"top_k": 3, "score_threshold": 0.0, "candidate_multiplier": 2},
    "vectorstore": {"backend": "memory"},
    "embedding": {"backend": "fake"},
    "llm": {"backend": "fake"},
    "projects": {
        "p_alpha": {"name": "A", "active_collection_version": "1", "embedding_model_id": "bge-m3", "dim": 1024, "kb_ids": ["kb_a"]},
        "p_beta": {"name": "B", "active_collection_version": "1", "embedding_model_id": "bge-m3", "dim": 1024, "kb_ids": ["kb_b"]},
    },
}
deps = build_deps(OFFLINE_RAW, force=True)
print("== deps.definitions ==", sorted(deps.definitions))
print("== derived experts ==", [e.name for e in deps.derived_views["p_alpha"].experts])
print("== store type ==", type(deps.definition_store).__name__)

import django  # noqa: E402

django.setup()
build_application(deps)
from django.test import Client  # noqa: E402

client = Client()
AUTH = {"HTTP_AUTHORIZATION": f"Bearer {os.environ['IB_OFFLINE_TOKEN']}"}
g = client.get("/api/config/definition", **AUTH)
print("== GET status ==", g.status_code, "keys:", sorted(g.json().keys()) if g.status_code == 200 else g.content[:200])
print("== GET no-auth ==", client.get("/api/config/definition").status_code)
print("== GET wrong-project ==", client.get("/api/config/definition", HTTP_X_IB_PROJECT="p_beta", **AUTH).status_code)
print("== POST ==", client.post("/api/config/definition", **AUTH).status_code)
print("== DELETE ==", client.delete("/api/config/definition", **AUTH).status_code)
print("== GET ?token=x ==", client.get("/api/config/definition?token=x", **AUTH).status_code)

payload = g.json()
doc = payload["document"]
print("== config_key_names ==", payload["config_key_names"])
print("== editable_fields has orchestration? ==", "orchestration" in payload["editable_fields"])
print("== token value leaked in body? ==", os.environ["IB_OFFLINE_TOKEN"] in g.content.decode("utf-8"))

doc2 = json.loads(json.dumps(doc))
doc2["route"]["tau"] = 0.72
p = client.put(
    "/api/config/definition",
    data=json.dumps({"expected_content_hash": doc["content_hash"], "document": doc2}),
    content_type="application/json",
    **AUTH,
)
print("== PUT ok status ==", p.status_code, sorted(p.json().keys()) if p.status_code == 200 else p.content[:200])

# 405 detection: PUT with stale hash
p2 = client.put(
    "/api/config/definition",
    data=json.dumps({"expected_content_hash": "sha256:deadbeef", "document": doc2}),
    content_type="application/json",
    **AUTH,
)
print("== PUT stale status ==", p2.status_code)

# 403 via policy? offline AllowAllPolicy → can_manage True; project mismatch handled by middleware?
print("== PUT wrong-project ==", client.put(
    "/api/config/definition",
    data=json.dumps({"document": doc2}),
    content_type="application/json",
    HTTP_X_IB_PROJECT="p_beta",
    **AUTH,
).status_code)

print("PROBE-DONE")
