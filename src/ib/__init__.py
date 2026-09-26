"""
@module MOD-IB-01..MOD-IB-22
@implements (package root; see sub-modules)
@depends (none)
@author software-developer

intelligentbase —— 通用 RAG + 多智能体可复用基座（reusable base library）。

分层（module_design.md §4.3 单向铁律：依赖只向下层）：

    L0  ib.core        ib.config      ib.context     ib.observability
    L1  ib.parsing     ib.chunking
    L2  ib.ocr         ib.rendering   ib.embedding   ib.vectorstore
    L3  ib.ledger      ib.blob        ib.lifecycle   ib.rebuild   ib.retrieval
    L4  ib.experts     ib.tools       ib.routing     ib.llm
        ib.streaming   ib.orchestration
    L5  ibweb（Django 组合根 / HTTP 层，独立包）

不变式：
  * `ib.core` 零第三方依赖（framework-free），Django/DRF 类型只允许出现在 ibweb 内。
  * 所有第三方重依赖一律函数内延迟导入，缺失时抛 DependencyUnavailableError。
"""

__version__ = "1.0.0"

__all__ = ["__version__"]
