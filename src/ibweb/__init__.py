"""
@module MOD-IB-23
@implements IFC-IB-241 build_application / 242~249 HTTP 端点 / 250 鉴权注入
@depends MOD-IB-01 ~ MOD-IB-22（全部装配，见 module_design §5）
@author sub_agent_software_developer

Django 承载层（MOD-IB-23）—— **唯一装配点**。

## 为什么这里只有「薄层」

`ib/`（MOD-IB-01~22）是 framework-free 的基座：它不认识 HTTP、不认识 Django、不认识请求对象。
本包把 Django 世界翻成基座能懂的类型（`RequestContext` / `Scope` / `bytes`），再把基座的结果
翻回 HTTP（`JsonResponse` / SSE 帧）。

这条边界的收益是可验证的：**基座的全部单测都不需要 Django**，而 Django 侧只剩「参数解析 +
调端口 + 状态码映射」这三种机械动作，评审时一眼能看完。

## 不变式（module_design §2.1.1 强制）

Django / DRF 类型**只允许出现在 `src/ibweb/`**，不得向 `src/ib/` 反向渗透。
`ib/` 里的每一处都不 import 本包 —— 若某天出现「基座需要知道 request」，那是分层被破坏的信号，
正确做法是新增端口，而不是把 Django 传下去。

## 请求数据的两个不可信来源（必须显式处理）

1. **`project_id` 一律取自服务端鉴权结论**（`AuthzContext.project_id`），**绝不取自请求体或
   查询串**。若请求带了 `X-IB-Project` 且与服务端结论不一致 → `403`（明确拒绝，
   而不是「忽略请求值」—— 忽略会让攻击者无法察觉自己的越权尝试已被拦，也让我们失去观测）。
2. **令牌只允许经 `Authorization` 头传递**。查询串里出现 `token`/`access_token` 参数时
   **显式 400**：这类令牌会被 nginx / uvicorn 访问日志**完整打印**，FreeArk 已实际发生过
   一次 WS 令牌经 `?token=` 泄露（见项目记忆 `freeark-ws-token-query-string-leak`）。
   静默忽略查询串令牌不够 —— 必须让违规调用方当场失败，否则「反正也能用」的写法会继续扩散。
"""

#: 本包版本（与 `ib.__version__` 各自独立：Web 层可单独回滚）。
__version__ = "1.0.0"
