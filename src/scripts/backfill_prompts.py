#!/usr/bin/env python
"""**一次性提示词回填迁移入口**（IFC-IB-391 / ADR-51 决定 ②；**须用户手工执行**）。

## 这个脚本为什么必须手工执行（而不是接入启动路径）

REV-20（ADR-48）删除了**代码内置提示词兜底**：提示词正文的**唯一**来源变成项目提示词目录
（`main.md` / `fallback.md`），两层皆缺即装配期 `prompt_missing` fail-closed。既有项目若从未
落盘过提示词文件，重启后会**装配失败**。回填把内置 `kb-agent` 的种子正文（仓库资产
`src/ib/expert_seeds/kb-agent.md`，IFC-IB-389）写入 `<root>/<project_id>/kb-agent/main.md`。

**绝不自动执行**（C-IB-38）：自动回填会在一次重启里静默**覆盖用户手工编辑过的提示词**，
且没有回滚点。故能力只以本脚本形式提供，由运维显式决定「什么时候、面向哪些项目」。

## 纪律（由 `ibweb.composition.backfill_project_prompts` 强制）

  * **先备份**：`--backup-dir` 非空时，被覆盖的原文件逐字复制到
    `<backup-dir>/<project_id>/<expert>/main.md`；
  * **失败即回滚**：任一项失败 → 用备份还原已覆盖项并抛异常（**不静默**）；
  * **覆盖不静默**：逐项目输出「被覆盖 / 新建」；
  * **不含任何凭据**：只读写提示词文件，不回显正文。

## 用法（在生产机上、以服务账号身份）

    IB_EXPERT_PROMPT_DIR=/var/lib/intelligentbase/prompts \\
      python src/scripts/backfill_prompts.py --backup-dir /var/lib/intelligentbase/backup-prompts

    # 只回填指定项目（不必装配应用；适合抖出故障时的最小面操作）
    python src/scripts/backfill_prompts.py --prompt-root <root> --projects demo,Freeark

退出码：0 = 全部成功；1 = 有失败（已回滚，**不会**留下半成品）；2 = 用法 / 环境错误。
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="backfill_prompts",
        description="一次性提示词回填迁移（IFC-IB-391；须用户手工执行，非运行期行为）",
    )
    parser.add_argument(
        "--prompt-root",
        default="",
        help="提示词目录根（缺省取环境变量 IB_EXPERT_PROMPT_DIR；两者皆空即报错）",
    )
    parser.add_argument(
        "--backup-dir",
        default="",
        help="被覆盖文件的备份目录（强烈建议提供：这是唯一的回滚点）",
    )
    parser.add_argument(
        "--projects",
        default="",
        help="逗号分隔的项目 ID 列表；缺省 = 注册表全部活动项目（需应用可装配）",
    )
    return parser.parse_args(argv)


def _resolve_projects(explicit: str) -> list[str] | None:
    """显式列表优先；否则尝试装配应用取「注册表全部活动项目」。"""
    if explicit.strip():
        return [p.strip() for p in explicit.split(",") if p.strip()]
    from ibweb.composition import build_deps, get_deps

    try:
        if get_deps(required=False) is None:
            build_deps(None, force=True)
        deps = get_deps(required=False)
        return sorted(getattr(deps, "projects", {}) or {})
    except Exception as exc:  # noqa: BLE001 - 装配不可用时给出可读指引，不静默
        print(
            f"[backfill] 无法从注册表解析项目列表（{type(exc).__name__}）；"
            f"请显式传入 --projects。",
            file=sys.stderr,
        )
        return None


def main(argv: list[str] | None = None) -> int:
    _root = pathlib.Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    args = _parse_args(argv if argv is not None else sys.argv[1:])
    prompt_root = (args.prompt_root or os.environ.get("IB_EXPERT_PROMPT_DIR", "")).strip()
    if not prompt_root:
        print(
            "[backfill] 缺少提示词目录：请传 --prompt-root 或设置 IB_EXPERT_PROMPT_DIR。",
            file=sys.stderr,
        )
        return 2
    backup_dir = args.backup_dir.strip() or None
    if backup_dir is None:
        print(
            "[backfill][WARN] 未提供 --backup-dir：被覆盖的原文件**没有回滚点**"
            "（迁移一旦失败将无法自动还原）。",
            file=sys.stderr,
        )

    projects = _resolve_projects(args.projects)
    if not projects:
        print("[backfill] 项目列表为空：无可回填对象。", file=sys.stderr)
        return 2

    from ibweb.composition import backfill_project_prompts

    print(f"[backfill] 目标目录 = {prompt_root}，项目数 = {len(projects)}")
    try:
        results = backfill_project_prompts(
            projects, prompt_root=prompt_root, backup_dir=backup_dir
        )
    except Exception as exc:  # noqa: BLE001 - 失败已回滚；如实报错，不静默
        print(f"[backfill][FAIL] 迁移中止（已回滚）：{exc}", file=sys.stderr)
        return 1

    for project_id, res in zip(projects, results):
        action = "overwritten" if "overwritten" in res.notes else "created"
        print(
            f"[backfill] {project_id}: {action}（covered={res.affected}，"
            f"backup={res.backup_path or 'None'}）"
        )
    print("[backfill] 完成：所有目标项目均已具备项目域提示词载体（main.md）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
