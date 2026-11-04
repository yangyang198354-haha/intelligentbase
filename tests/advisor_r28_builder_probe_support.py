"""REV-28（GROUP_D-003）AC-017-06 基线对比探针（独立运行；不 import conftest，以便把 `IB_SRC` 指向任一份 src 树）。

记录“未启用顾问项目”的 Agent Builder 在生成草案时发给云端 LLM 的完整载荷（含项目摘要）。
黄金 `tests/integration/advisor_r28_builder_golden.json` 由**基线 commit 8d6fd4b 的 src 树**运行本探针产生
（`git archive 8d6fd4b src` 解出后以 `IB_SRC=<解出目录>/src` 运行）——期望值不是用被测代码生成的。

运行：IB_SRC=<src 目录> python tests/advisor_r28_builder_probe_support.py > out.json
"""

from __future__ import annotations

import copy
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.environ.get("IB_SRC") or os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
for _k, _v in (("PYTHONUTF8", "1"), ("IB_OFFLINE_MODE", "1"), ("IB_CONFIG_SOURCE", "dict"), ("IB_OFFLINE_TOKEN", "groupd-offline-token"),
               ("IB_LOG_LEVEL", "ERROR"), ("DJANGO_SETTINGS_MODULE", "ibweb.settings")):
    os.environ.setdefault(_k, _v)

RAW = {
    "config_source": "dict", "offline_mode": True, "ledger_backend": "memory",
    "blob": {"enabled": True, "root": os.path.join(_SRC, ".probe_blobs")},
    "retrieval": {"top_k": 3, "score_threshold": 0.0, "candidate_multiplier": 2},
    "vectorstore": {"backend": "memory"}, "embedding": {"backend": "fake"}, "llm": {"backend": "fake"},
    "projects": {
        "p_alpha": {"name": "测试项目 A", "active_collection_version": "1", "embedding_model_id": "bge-m3", "dim": 1024, "kb_ids": ["kb_a"]},
    },
}

REQUIREMENT = "做一个回答产品手册问题的客服助手，只能检索产品手册"
DRAFT = {"name": "faq-agent", "cn_label": "常见问题助手", "main_prompt": "你是常见问题助手，引用来源，未找到时如实告知，通过检索工具作答。",
         "fallback_prompt": "暂时无法回答，请稍后再试。", "keywords": ["常见问题"], "exemplars": ["这个怎么用", "手册里怎么说"],
         "tool_names": ["search_knowledge"], "tool_params": [], "knowledge_folders": [], "max_steps": 4,
         "is_data_expert": False, "is_delegating": False}


def run_probe() -> dict:
    from django.test import Client
    from ibweb.composition import build_application, build_deps

    deps = build_deps(copy.deepcopy(RAW), force=True)
    import django

    django.setup()
    build_application(deps)
    sent: list[str] = []

    def _answer(system, user):
        sent.append(user)
        return json.dumps(DRAFT, ensure_ascii=False)

    deps.llm.complete_output = _answer
    auth = {"HTTP_AUTHORIZATION": "Bearer " + os.environ["IB_OFFLINE_TOKEN"]}
    c = Client()
    r = c.post("/api/builder/draft", data=json.dumps({"requirement": REQUIREMENT}), content_type="application/json",
               **auth, **{"HTTP_X_IB_PROJECT": "p_alpha"})
    return {"status": r.status_code, "payloads": [json.loads(s) for s in sent]}


if __name__ == "__main__":
    json.dump(run_probe(), sys.stdout, ensure_ascii=False, sort_keys=True, indent=1)
