# MOD-R29-02 包入口（REV-29：agent 工具调用的 MCP 适配）
"""`ib.mcp`：MCP 客户端、运行时与管理服务（进程内库，ib-web 内使用）。

纪律（selfcheck `mcp_egress_single_exit`）：
  * 本包中**只有** `transport.py` 允许 import 网络库（http.client / socket / ssl / urllib）；
  * 不得 import `ib.retrieval / ib.vectorstore / ib.blob / ib.streaming / ib.context / ib.ledger / ib_embed`；
  * `ib.webtools / ib.orchestration / ib.tools / ib.runtime` 不得 import 本包（经 `RuntimeDeps` 的 Callable 注入）。
包入口不导入任何子模块，避免无谓的导入开销与环。
"""
