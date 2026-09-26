"""
@module MOD-IB-26
@implements IFC-IB-266 ~ IFC-IB-274（ib-embed 服务端线协议；契约唯一落点：
            docs/ib_embed_service_contract.md）
@depends —（**不 import 任何 `ib.*`**：服务端与业务基座之间**只有线协议**）
@author sub_agent_software_developer

`ib-embed` —— bge-m3 常驻 embedding 推理服务（MOD-IB-26）。

**包级隔离声明（强制，C8）**

* 本包是**独立顶层包**（`src/ib_embed/`），**不被任何模块 import** —— 上层只经
  MOD-IB-09 的 `Embedder` 端口与线协议访问它（与 MOD-IB-10 对 Qdrant 服务的形态同构）。
  进程内形态 `InProcessBgeM3Embedder` 位于 **MOD-IB-09 之内**，**不 import 本包**
  （否则产生 `09 → 26` 的非法反向依赖边）。
* 本包**只依赖标准库**，且**不** import `ib.*`：这样「形态可逆」才成立 ——
  把 `IB_EMBED_BACKEND` 从 `http` 切到 `inproc` 时，可以**停用**本服务而业务进程零耦合。
* **无凭据面**：仅监听回环、无鉴权、不认识任何令牌键（契约 §9「凭据纪律」）。

**模块划分**

| 文件 | 职责 |
|------|------|
| `config.py`  | 11 个 `IB_EMBED_*` 键 → 不可变 `EmbedConfig`；缺失/非法只报**键名** |
| `runtime.py` | 可替换的 `RuntimePort` + 惰性加载（缺库→可读原因，**不启动崩溃**） |
| `server.py`  | `POST /embed`、`GET /healthz`、`POST /warmup`、`POST /descriptor` 的线协议 |

本包**不含部署配置**（systemd 单元与环境变量模板属 MOD-IB-25 / IFC-IB-286）。
"""

from __future__ import annotations

__all__: list[str] = []
