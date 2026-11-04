# MOD-R28-16 / REQ-NFUNC-008：顾问意图 / 上下文评测运行脚本（目标机手工运行；评测集由用户提供，脚本不内置合成集）
"""用法：
    python src/scripts/advisor_eval.py --intent-set <jsonl> --context-set <jsonl> [--report <path>]

评测集（JSON Lines，UTF-8，由用户提供）：
  * 意图集每行：{"query": str, "history": [{"role": "user|assistant", "content": str}, ...]?, "gold_intent": str,
                 "gold_topic": str?}
  * 上下文集每行：{"history": [...], "query": str, "gold_resolved": str, "gold_topic": str?}

指标（`ib.advisor.metrics`）与阈值：意图 top-1 ≥ 0.90、指代消解 ≥ 0.85、话题切换 F1 ≥ 0.85、
“专业问题误判为通用并联网外发”比例 ≤ 0.02。

LLM：从环境读取 `IB_LLM_BASE_URL` / `IB_LLM_MODEL` / `IB_LLM_API_KEY`（密钥只读环境，不打印、不写报告）。
离线单测只用替身验证统计逻辑（`evaluate()` 接受任意带 `understand()` 的对象）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Iterable, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

THRESHOLDS = {"intent_top1": 0.90, "resolution": 0.85, "topic_f1": 0.85, "knowledge_to_web_max": 0.02}
INTENT_LABELS = ("knowledge", "general", "delegate", "chitchat", "refuse", "unknown")


def read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise SystemExit(f"{path}:{i} 不是合法 JSON") from exc
            if not isinstance(row, dict):
                raise SystemExit(f"{path}:{i} 须为 JSON 对象")
            rows.append(row)
    return rows


def _history(row: dict[str, Any]) -> list[Any]:
    from ib.core import Message

    return [Message(role=str(m.get("role", "user")), content=str(m.get("content", ""))) for m in row.get("history") or []]


def _top_intent(u: Any) -> str:
    return u.intents[0] if getattr(u, "intents", ()) else "unknown"


def evaluate(understander: Any, intent_rows: Sequence[dict[str, Any]], context_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """纯统计：对每行调用 `understander.understand(query, history)`，经 `ib.advisor.metrics` 汇总。"""
    from ib.advisor import metrics as M

    gold_i: list[str] = []
    pred_i: list[str] = []
    pred_all: list[tuple[str, ...]] = []
    gold_t: list[str] = []
    pred_t: list[str] = []
    for row in intent_rows:
        u = understander.understand(str(row.get("query", "")), _history(row))
        gold_i.append(str(row.get("gold_intent", "")))
        pred_i.append(_top_intent(u))
        pred_all.append(tuple(u.intents))
        if row.get("gold_topic"):
            gold_t.append(str(row["gold_topic"]))
            pred_t.append(str(u.topic))
    gold_r: list[str] = []
    pred_r: list[str] = []
    for row in context_rows:
        u = understander.understand(str(row.get("query", "")), _history(row))
        gold_r.append(str(row.get("gold_resolved", "")))
        pred_r.append(str(u.resolved_query))
        if row.get("gold_topic"):
            gold_t.append(str(row["gold_topic"]))
            pred_t.append(str(u.topic))
    result = {
        "counts": {"intent": len(gold_i), "context": len(gold_r), "topic": len(gold_t)},
        "intent_top1": M.intent_top1_accuracy(gold_i, pred_i),
        "confusion": M.confusion_matrix(gold_i, pred_i, INTENT_LABELS),
        "resolution": M.resolution_accuracy(gold_r, pred_r),
        "topic_f1": M.topic_f1(gold_t, pred_t),
        "knowledge_to_web": M.knowledge_to_web_rate(gold_i, pred_all),
    }
    result["verdict"] = {
        "intent_top1": result["intent_top1"] >= THRESHOLDS["intent_top1"],
        "resolution": result["resolution"] >= THRESHOLDS["resolution"],
        "topic_f1": result["topic_f1"] >= THRESHOLDS["topic_f1"],
        "knowledge_to_web": result["knowledge_to_web"] <= THRESHOLDS["knowledge_to_web_max"],
    }
    result["thresholds"] = dict(THRESHOLDS)
    result["pass"] = all(result["verdict"].values())
    return result


def _build_real_understander() -> Any:
    from ib.advisor import TurnUnderstander
    from ib.config import ConfigurationResolver, FileConfigurationSource
    from ib.llm import build_llm_provider

    cfg = ConfigurationResolver(FileConfigurationSource()).global_config()
    api_key = os.environ.get("IB_LLM_API_KEY", "").strip() or None
    return TurnUnderstander(llm=build_llm_provider(cfg, api_key=api_key))


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="顾问意图 / 上下文评测（目标机手工运行）")
    ap.add_argument("--intent-set", required=True, help="意图评测集 jsonl（由用户提供）")
    ap.add_argument("--context-set", required=True, help="上下文评测集 jsonl（由用户提供）")
    ap.add_argument("--report", help="可选：把结果 JSON 写到该路径")
    args = ap.parse_args(list(argv) if argv is not None else None)
    result = evaluate(_build_real_understander(), read_jsonl(args.intent_set), read_jsonl(args.context_set))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
