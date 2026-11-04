# MOD-R28-02..05 联网工具包（ib.webtools）；不 import ib.retrieval / vectorstore / blob / streaming / context / ledger / ib_embed
"""联网工具库：地址防护、安全抓取、搜索端口适配、出站闸与预算、联网工具。

本包为 ib-web 进程内的库（ADR-R28-03/10）；编排层（ib.orchestration）不 import 本包，
经组合根注入（基线 ADR-09）。导入本包本身不触发任何网络动作，也不要求 lxml 可用。
"""

from __future__ import annotations

__all__: list[str] = []
