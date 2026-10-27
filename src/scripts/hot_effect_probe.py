# MOD-R26-22 / implements IFC-R26-190：热生效探针（只读 CLI；由用户在目标机部署后执行，不属于 CI）
"""抽样核对“保存后新提问是否都绑定了同一个最新版本”（TBD-T32 / AC-014-04）。

用法：
    IB_PROBE_TOKEN=<令牌> python src/scripts/hot_effect_probe.py --base-url http://127.0.0.1:8000 \
        --project <项目ID> --samples 20

* 令牌**只**从环境变量 `IB_PROBE_TOKEN` 读取（不接受命令行传令牌，不回显）；
* 只调用 `GET /api/config/status` 与 `GET /api/chat/stream`（只读提问），不写任何配置；
* 输出各样本所见版本与收敛耗时分布；`apply_state != ok` 或样本版本不一致 → 退出码 1；参数非法 → 退出码 2。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

_QUESTION = "你好"


def _get(url: str, token: str, project: str, *, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "X-IB-Project": project})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - 仅 http(s)，见 main() 的 scheme 校验
        return resp.read()


def _status(base: str, token: str, project: str) -> dict:
    return json.loads(_get(f"{base}/api/config/status", token, project).decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hot_effect_probe", description="热生效抽样探针（只读）")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--samples", type=int, default=20)
    args = ap.parse_args(argv)

    if not (args.base_url.startswith("http://") or args.base_url.startswith("https://")):
        print("参数错误：--base-url 必须以 http:// 或 https:// 开头", file=sys.stderr)
        return 2
    if not 1 <= args.samples <= 500:
        print("参数错误：--samples 须在 1..500", file=sys.stderr)
        return 2
    token = os.environ.get("IB_PROBE_TOKEN", "").strip()
    if not token:
        print("参数错误：请通过环境变量 IB_PROBE_TOKEN 提供令牌（不接受命令行传令牌）", file=sys.stderr)
        return 2
    base = args.base_url.rstrip("/")

    try:
        st = _status(base, token, args.project)
    except (urllib.error.URLError, ValueError, OSError) as exc:
        print(f"无法读取 /api/config/status：{type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"head 版本 = {st.get('version')}；已应用版本 = {st.get('applied_version')}；状态 = {st.get('apply_state')}")
    bad = st.get("apply_state") != "ok"

    seen: list[int] = []
    latencies: list[float] = []
    for _ in range(args.samples):
        q = urllib.parse.urlencode({"q": _QUESTION, "session_id": f"probe-{uuid.uuid4().hex[:12]}"})
        t0 = time.monotonic()
        try:
            _get(f"{base}/api/chat/stream?{q}", token, args.project)
            latencies.append((time.monotonic() - t0) * 1000.0)
            seen.append(int(_status(base, token, args.project).get("applied_version", -1)))
        except (urllib.error.URLError, ValueError, OSError) as exc:
            print(f"样本失败：{type(exc).__name__}", file=sys.stderr)
            bad = True
    if seen:
        print(f"样本所见已应用版本：{sorted(set(seen))}（共 {len(seen)} 个）")
    if latencies:
        latencies.sort()
        p = lambda r: latencies[min(len(latencies) - 1, int(len(latencies) * r))]  # noqa: E731
        print(f"提问耗时 ms：p50={p(0.5):.0f} p95={p(0.95):.0f} max={latencies[-1]:.0f}")
    if len(set(seen)) > 1:
        print("不一致：样本间出现了不同的已应用版本", file=sys.stderr)
        bad = True
    return 1 if bad else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
