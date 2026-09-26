<file_header>
  <project>intelligentbase</project>
  <artifact>ib_embed_service_contract</artifact>
  <path>docs/ib_embed_service_contract.md</path>
  <doc_id>IFC-INTELBASE-EMBED-001</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04 模块详细设计（R2 增量：L-03）</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-003</invocation_id>
  <created_at>2026-09-26</created_at>
  <owns>MOD-IB-26 ib-embed 常驻 embedding 推理服务</owns>
  <implements>IFC-IB-266 ~ IFC-IB-274</implements>
  <module_dependencies>MOD-IB-01, MOD-IB-02, MOD-IB-04（其余模块**不得** import 本模块）</module_dependencies>
  <related_frozen>
    <item>MOD-IB-09（`Embedder` 端口 + 客户端，IFC-IB-090~096）——**已落盘**，本契约以其为事实基线</item>
    <item>MOD-IB-25（部署交付物，IFC-IB-261/262/286）——本模块**不含**部署配置</item>
    <item>ADR-02（形态与双路径纪律）/ ADR-03（systemd 裸装）/ ADR-04（隔离无关项）</item>
  </related_frozen>
  <readonly_reference path="FreeArk 仓库" note="只读参考；未修改任何文件"/>
  <readonly_reference path="src/ib/embedding/__init__.py" note="客户端实现（已落盘）：路径 `/embed`、键 `texts`/`model`/`mode`、响应键 `vectors` 均以本文件为准"/>
  <readonly_reference path="src/deploy/systemd/ib-embed.service" note="单元文件已存在（交付物，属 MOD-IB-25）；本文件只登记其契约相关口径"/>
  <scope_boundary>服务端 HTTP 契约、错误语义、维度/批量一致性、冷热双路径口径、形态可逆、配置**键名**清单、库选型与 CPU-only 约束。**不含实现代码、不含伪代码、不含部署配置、不含任何凭据值或密钥。**</scope_boundary>
  <security_note>全文只登记**配置键名**，不含任何真实值。服务仅监听回环，不引入新的凭据面。</security_note>
</file_header>

# ib-embed 服务端契约 — bge-m3 常驻推理服务（MOD-IB-26）

**版本**：1.0.0（R2 新增） | **状态**：DRAFT（待 PM 门控评审） | **日期**：2026-09-26
**归属**：MOD-IB-26（R2 新增模块；编号 26 > 其全部依赖 {01, 02, 04}，满足 §4 的「编号即拓扑序」）
**为什么单列此文件**：L-03 指出 `ib-embed` 此前**只有单元文件与客户端、没有服务端模块归属与完整契约**。本文件是该契约的**单一落点**，`module_design.md` §3 MOD-IB-26 为摘要视图，二者冲突时**以本文件为准**（并须回写 `module_design.md`）。

---

## 1. 事实基线：契约不是新设计的，而是「把已落盘的客户端事实写成设计」

`src/ib/embedding/__init__.py`（MOD-IB-09，v1 已落盘）已经**硬编码**了本服务的线协议：

| 客户端已落盘事实 | 来源 | 本契约的处置 |
|---|---|---|
| `POST /embed`，请求体 `{"texts": [...], "model": ..., "mode": "document"\|"query"}` | `embed_documents` / `embed_query` | **沿用**（不改为 `/v1/embeddings`，理由见 §11） |
| 响应键 `vectors`（`parsed.get("vectors")`） | `_vectors_from` | **沿用** |
| 长度不符即 `raise DependencyUnavailableError("ib-embed 返回的向量数量与请求不符")` | `_vectors_from` | 服务端**必须**返回 `len(vectors) == len(texts)`，否则客户端直接判为依赖不可用 |
| 维度不符即抛（`len(vec) != self._dim`） | `_vectors_from` | 服务端**必须**返回 `len(vec) == dim == 1024`（IFC-IB-267） |
| `GET /healthz` 读 `ok` / `detail`，**永不抛** | `health()` | 沿用（IFC-IB-269） |
| `POST /warmup` 体 `{"model": ...}`，超时 `max(cold_timeout, 300.0)`、重试 1、失败仅 WARN | `warmup()` | 沿用；服务端须**幂等**（IFC-IB-270） |
| `POST /descriptor` 读 `model_id`/`dim`/`normalized`/`max_tokens`/`device`；失败回落配置值；注释声明「`dim` 是写入正确性的前提，优先信任服务端真实值」 | `descriptor()` | 沿用；字段名与 MOD-IB-01 `EmbedderDescriptor` **逐字段一致**（IFC-IB-271） |
| 4xx **不重试**（`if exc.code < 500: break`）；5xx 才重试；退避 `min(0.5*2^n, 4.0)` | `_post` | 错误码分类必须与「4xx=配置/请求错、5xx=暂时故障」严格对齐（IFC-IB-268） |
| 默认 `cold_timeout=120s / cold_retries=3 / cold_batch=16 / hot_timeout=3s / hot_retries=1` | 构造函数默认值 | 服务端**不得**依赖这些值做内部决策；冷热差异全部在客户端（IFC-IB-273） |
| `IB_EMBED_URL=http://127.0.0.1:8100`、`IB_EMBED_MODEL_ID=bge-m3`、`IB_EMBED_DIM=1024` | `src/deploy/env.example` | 服务端默认值须与之吻合（IFC-IB-274） |

**结论**：服务端契约若另起一套（`/v1/embeddings` + `embeddings[][]`），将**同时**打破「客户端已落盘」与「ADR-03 已登记 `/embed` `/healthz`」两处一致性，且无架构收益。故本契约**冻结为 `/embed` 系列**。

---

## 2. 服务形态与网络面

| 项 | 取值 | 依据 |
|---|---|---|
| 进程形态 | **独立常驻进程**（systemd 单元 `ib-embed`），单实例 | ADR-02 Option B |
| 监听 | 回环 `127.0.0.1:8100`（默认；键 `IB_EMBED_HOST` / `IB_EMBED_PORT`） | 单元文件 `--host 127.0.0.1 --port 8100` |
| 鉴权 | **无**（回环专用，不暴露到内网其他主机） | 与单元文件注释一致；**不得**为此引入新令牌（最小凭据面） |
| 模型 | bge-m3 稠密，**单模型常驻**；跨模型请求一律 `409`，不做运行时换模型 | ADR-02「单例常驻」 |
| 设备 | `device ∈ {"cpu"}`；**CPU-only 为默认且不得强依赖 GPU** | DR-05 / REQ-NFR-IB-10；目标机 GTX 960（Maxwell）不被现代 PyTorch/onnxruntime 支持 |
| 并发 | 有界并发 + **有界队列**；超限**快速失败**，绝不无界排队 | ADR-02（排队会把「慢」放大为「全链路超时」） |
| 依赖方向 | 本模块**不被任何模块 import**（与 MOD-IB-10 ↔ Qdrant 服务同构：只走线协议） | 编号纪律（见 §10） |

---

## 3. `POST /embed`（IFC-IB-266）

### 3.1 请求

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `texts` | `array[string]` | 是 | 非空；`len(texts) <= IB_EMBED_MAX_BATCH`；元素为字符串 | 批内顺序即响应顺序（**保序契约**） |
| `model` | `string` | 是 | 须等于当前已加载模型标识（默认 `bge-m3`） | 不等 → `409 model_mismatch` |
| `mode` | `"document"` \| `"query"` | 是 | 枚举 | bge-m3 稠密**不区分**指令前缀，两种 mode 输出同源同分布；保留该字段是为了**换模型时不必改客户端**（AC-IB-07-05 可替换性） |

### 3.2 响应 `200`

| 字段 | 类型 | 说明 |
|---|---|---|
| `vectors` | `array[array[float]]` | **`len(vectors) == len(texts)`**，且每个内层长度 **== `dim` == 1024**；顺序与 `texts` 一一对应 |
| `dim` | `int` | 恒 `1024`（bge-m3 稠密）；**权威值**（IFC-IB-267） |
| `model_id` | `string` | 实际加载的模型标识 |
| `normalized` | `bool` | 恒 `true`（**L2 归一化后返回**，向量模长 ≈ 1；AC-IB-07-02/04） |
| `count` | `int` | 恒 `== len(texts)`（冗余自检字段，供运维/测试一眼核对） |
| `elapsed_ms` | `int` | 服务端推理耗时（不含网络与客户端排队） |
| `truncated_indices` | `array[int]` | **可选**，仅当发生单条截断时出现（见 §4.2）；客户端忽略未知字段，故向后兼容 |

**失败响应**：绝不返回「部分向量」。要么整体成功，要么整体错误（见 §5）。理由：客户端在长度不符时抛错，部分成功等价于一次凭据不明的不一致写入风险。

---

## 4. 维度、批量与截断（IFC-IB-267 / IFC-IB-272）

### 4.1 三方一致性（**硬约束**）

`dim` 在**三处**必须一致，任一不一致都必须在最早可发现的时刻失败：

| 位置 | 载体 | 不一致后果 |
|---|---|---|
| 服务端真实维度 | `/descriptor` 的 `dim`、`/embed` 的 `dim` | —（真源） |
| 客户端配置 | `IB_EMBED_DIM=1024` | 客户端按配置校验，不符即抛（已落盘行为） |
| 向量库 collection | `CollectionSpec.dim`（`ProjectRecord.dim`） | **写坏 collection**（Qdrant 拒写或写入不可解释的向量），是最严重一类数据损坏 |

- 服务端 `dim` **不得**由配置覆盖为与权重不符的值：`IB_EMBED_DIM` 在服务端仅作**启动期交叉校验**用（不匹配则启动失败，不回退）。
- 客户端 `descriptor()` 失败时回落配置值的既有行为**保持不变**；本契约只保证「服务端在可用时提供权威值」。

### 4.2 批上限与截断

| 项 | 规则 | 键 |
|---|---|---|
| 批上限 | `len(texts) > MAX_BATCH` → `400 batch_too_large`，错误体回显 `max_batch` | `IB_EMBED_MAX_BATCH`（默认 **64**） |
| **批上限一致性硬约束** | 服务端 `MAX_BATCH` **必须 ≥** 客户端冷路径批量（默认 16，可配）。若运维把客户端 `cold_batch_size` 调大而服务端未同步 → 冷路径**必然** 400 且不重试 → **整批文档入库失败**。故错误体**回显 `max_batch`**，使配置错配可被一眼定位 | 同上 |
| 单条超长 | bge-m3 上限 8192 token；超长**截断保前缀**并继续（不失败），在 `truncated_indices` 中标注 + WARNING 日志。理由：入库路径不应因单条超长而让**整篇文档** `failed`（失败粒度纪律：块级可丢，文档级不轻弃） | `IB_EMBED_MAX_TOKENS`（默认 8192） |
| 截断后为空 | 按 `400 invalid_request` | — |

---

## 5. 错误码表（IFC-IB-268）

**统一错误体**：`{"code": string, "detail": string, "max_batch"?: int, "retry_after_s"?: int}`
**纪律**：`detail` 与日志**均不得回显输入文本**（正文属敏感面；凭据纪律见 §9）。

| HTTP | `code` | 触发条件 | 客户端行为（已落盘语义） | 归类 |
|---|---|---|---|---|
| 400 | `invalid_request` | 体非法 / `texts` 空 / 非字符串数组 / `mode` 越界 | **不重试**（4xx 中断） | 请求错 |
| 400 | `batch_too_large` | `len(texts) > max_batch` | **不重试**；须人工调小批量或调大服务端上限 | 配置错配 |
| 409 | `model_mismatch` | `model` ≠ 已加载模型 | **不重试**（409 属 4xx） | 配置错配 |
| 503 | `model_not_ready` | 进程已监听但权重未加载完 / 未预热 | **冷路径重试有效**（3 次预算内大概率恢复）；**热路径不重试** → 立即降级 | 暂时故障 |
| 503 | `overloaded` | 并发 + 队列已满 | 快速降级；回显 `retry_after_s` | 容量（fail-closed） |
| 504 | `inference_timeout` | 服务端自身单批推理超预算 | 属 5xx → 冷路径计入重试预算；热路径 1 次重试后降级 | 暂时故障 |
| 500 | `internal_error` | 其它未分类异常 | 5xx → 重试（受客户端预算限制） | 缺陷 |

**分类不变式**：`4xx/409 =「重试无用」`（配置或请求问题），`5xx =「重试可能有用」`。此不变式是客户端「4xx 不重试」实现能够成立的前提，**不得**把暂时性故障放进 4xx。

---

## 6. 健康、预热与自描述

### 6.1 `GET /healthz`（IFC-IB-269）

`200`，**永不抛异常、永不 5xx**（客户端 `health()` 依赖此性质）：

`{"ok": bool, "detail": string, "model_id": string, "dim": int, "model_loaded": bool, "warm": bool, "queue_depth": int, "inflight": int}`

- 客户端只读 `ok` / `detail`；其余为 R2 附加字段（被忽略即兼容）。
- 映射到 IFC-IB-249 的 `embed: HealthStatus(ok, detail, latency_ms)`，其中 `latency_ms` 由**客户端**计时。
- 未就绪时 `ok=false` + 可读 `detail`（如「模型权重尚未加载完成」）；**不含正文、不含路径细节**。

### 6.2 `POST /warmup`（IFC-IB-270）

`200`，**幂等**（已预热则立即返回，不重复加载）：`{"ok": bool, "loaded_ms": int, "model_id": string}`

- 客户端调用超时为 `max(cold_timeout, 300s)`、重试 1、失败仅 WARN（已落盘）→ 服务端**必须**把「加载」做成可在 300s 量级内完成或可取消的操作；若权重缺失应快速失败（`internal_error`）而非挂死到超时。
- `loaded_ms` 用于回填 **[TBD-T3]**（冷启动加载耗时）。

### 6.3 `POST /descriptor`（IFC-IB-271）

请求 `{"model": string}` → `200 EmbedderDescriptor`：

| 字段 | 类型 | 取值/约束 |
|---|---|---|
| `model_id` | `string` | `bge-m3`（与 `IB_EMBED_MODEL_ID` 一致） |
| `dim` | `int` | `1024`（权威） |
| `normalized` | `bool` | `true` |
| `max_tokens` | `int` | `8192`（截断阈值，见 §4.2） |
| `device` | `string` | `"cpu"`（GPU 若可用则内部切换为 `"cuda"`，**上层无感**，REQ-NFR-IB-10） |

**字段名与 MOD-IB-01 的 `EmbedderDescriptor` 逐字段一致**（不得新增/改名），使 `descriptor()` 的解析与契约同源。

---

## 7. 冷/热双路径超时纪律的「单一落点」（IFC-IB-273，对齐 ADR-02 / AC-IB-07-03）

**核心口径：服务端不区分冷热（无状态 HTTP），冷热差异全部由客户端的两个实例承载。** 这正是 ADR-02「同一 HTTP 契约、两个客户端实例」的含义。

| 路径 | 客户端（已落盘） | 服务端职责 | 失败终局 |
|---|---|---|---|
| **冷（入库）** | `cold_timeout_s=120`、`cold_max_retries=3`、`cold_batch_size=16`（可配） | 队列内**等待**（不拒绝）；超 `IB_EMBED_QUEUE_DEPTH` 才 `503 overloaded` | 重试耗尽 → 文档置 `failed` + `error_code`（不阻塞其他文档） |
| **热（查询）** | `hot_timeout_s=3`、`hot_max_retries=1` | 队列满即 `503 overloaded`，**不排队** | 超时 → `DependencyUnavailableError` → MOD-IB-15 转 `degraded`（`degrade_reason=timeout`）→ 问答继续 |

**服务端不得做的事**：为「让冷路径更成功」而引入无界队列 —— 那会把热路径一起拖死，违反「有界延迟」原则。冷路径的容忍度来自**客户端重试预算**，不来自服务端排队。
**服务端必须做的事**：① 并发与队列**显式配置**（`IB_EMBED_MAX_CONCURRENCY` / `IB_EMBED_QUEUE_DEPTH`），不依赖默认值；② 超限**快速失败**并回显 `retry_after_s`；③ `/healthz` 暴露 `queue_depth` / `inflight` 使降级可观测（AC-IB-13-02）。

---

## 8. 形态可逆：`standalone` ↔ `in-process`（IFC-IB-274）

| 项 | 说明 |
|---|---|
| 配置键 | `IB_EMBED_BACKEND ∈ {http, fake, inproc}`；**键名与默认值 `http` 不变**，仅**扩展值域** |
| `http` | 生产默认：客户端 `LocalHttpEmbedder` → 本服务 |
| `inproc` | 进程内实现 `InProcessBgeM3Embedder`，**位于 MOD-IB-09 之内**（不 import MOD-IB-26 —— 否则产生 09→26 非法边）；触发条件：`[TBD-T1/T3]` 显示服务开销不可接受 |
| `fake` | 离线/测试（既有） |
| 切换代价 | 改一个配置值 + （可选）停用 `ib-embed` 单元；**不改任何上层模块、不改 IFC 签名、不改任何既有键名**（ADR-02 的「换适配器类 + 改一行装配配置」） |
| **一致性要求** | 三形态必须通过**同一套线协议/端口一致性测试**（对齐 AC-IB-06-05 的做法）：`descriptor()` 五字段**逐字段一致**、`dim`/`normalized` 一致、同文本余弦 ≈ 1；否则形态切换会**静默改变写入语义** |
| 进程内形态的记录在案风险 | 模型内存 × worker 数（ADR-02 Option A 的缺点原样成立）；与 onnxruntime（OCR）同进程的叠加峰值 `[TBD-T4']` —— 这也正是**默认保持 `http`** 的理由 |

---

## 9. 服务端配置键（**R2 新增；仅新增、不改名**）

> 与 `ib-web.env`（`src/deploy/env.example`，其键与 `module_design` §5 逐项对应）**分离**：本节键属**另一份文件**（`ib-embed` 的 EnvironmentFile）。本节即该键名的**设计评审记录**（`env.example` 头部要求的正是此路径）。
> 本文件**只登记键名、默认值与语义**，不产出模板文件、不产出部署配置（架构阶段边界）。

| 键 | 默认 | 语义 | 备注 |
|---|---|---|---|
| `IB_EMBED_HOST` | `127.0.0.1` | 监听地址 | 回环；不得改绑 0.0.0.0（无鉴权） |
| `IB_EMBED_PORT` | `8100` | 监听端口 | 须与客户端 `IB_EMBED_URL` 一致 |
| `IB_EMBED_MODEL_ID` | `bge-m3` | 模型标识 | 与 `ib-web` 侧同名键须一致 |
| `IB_EMBED_DIM` | `1024` | 启动期**交叉校验**用维度 | 与权重不符 → 启动失败（不回退） |
| `IB_EMBED_MODEL_PATH` | 无默认（必填） | 本地权重目录 | **离线加载**必需（AC-IB-12-04 第 2 项） |
| `IB_EMBED_MAX_BATCH` | `64` | 单批上限 | 必须 ≥ 客户端 `cold_batch_size` |
| `IB_EMBED_MAX_TOKENS` | `8192` | 单条截断阈值 | §4.2 |
| `IB_EMBED_MAX_CONCURRENCY` | `1` | 推理并发 | CPU 单模型；`[TBD-T16]` 校准 |
| `IB_EMBED_QUEUE_DEPTH` | `8` | 有界队列深度 | 满即 `503 overloaded` |
| `IB_EMBED_THREADS` | `2` | 推理线程数 | 避免与 Qdrant / web / OCR 抢核；`[TBD-T16]` 校准 |
| `IB_EMBED_MEMORY_LIMIT_MB` | `2560` | 文档化 `MemoryMax` 依据 | 目标机 11GiB → 该值须按 `[TBD-T4]`/`[TBD-T16]` 重定 |

**凭据纪律**：本服务**不需要任何令牌**；上表无任何值写入仓库；不得把任何令牌/密钥放进 `ib-embed.env`（它不需要，加了就是净增凭据面）。

---

## 10. 库选型（服务端 bge-m3 运行时）与 CPU-only 约束

| 候选 | 许可 | CPU-only 形态 | 优 | 缺 |
|---|---|---|---|---|
| **`FlagEmbedding`（首选）** | MIT | 支持；`use_fp16=False`，`device="cpu"` | BAAI 官方，对 bge 系列适配最直接 | 传递依赖 `torch` + `transformers`（重） |
| `sentence-transformers`（备选） | Apache-2.0 | 支持 | 社区成熟、API 稳 | 同样引入 `torch`；bge-m3 支持须逐版本核实 |
| 直接 `onnxruntime`（备选，最轻） | MIT | 支持 | 无 `torch`，内存/启动最优；与既有 OCR 链路同栈（MOD-IB-06 已用） | 须自备 bge-m3 的 ONNX 导出与 tokenizer，且**池化与归一化须自实现**（错误实现会静默降低检索质量） |

- **最终择一必须在目标机以 `[TBD-T1]`/`[TBD-T3]`/`[TBD-T4]`/`[TBD-T18]` 实测为依据**（不预先拍板；与 `tech_stack.md` §1「Embedding 推理运行时」行一致）。
- **三候选均宽松许可，均 CPU-only 可用**；**`bge-m3` 权重为 MIT**（已登记）。
- **依赖纪律**：`torch` / `transformers` / `onnxruntime` 属**新增第三方依赖**，须在 `tech_stack.md` §2 台账**逐项登记**（`torch` BSD-3-Clause、`transformers` Apache-2.0、`onnxruntime` MIT 已在册）并在锁定版本后按发行包 `LICENSE` 复核。
- **禁止项（R2 复核重申）**：**不得引入 PyMuPDF（AGPL-3.0）**；**不得引入 Docker / 任何容器化形态**（DR-03）。本模块两者皆无需要。
- **`[TBD-T18]`（R2 新增风险）**：目标机 CPU 为 **Intel i7-3770S（Ivy Bridge）**，具备 AVX 但**不具备 AVX2**。部分 `torch` / `onnxruntime` 官方 wheel 以 AVX2 为基线编译，在此类 CPU 上可能触发**非法指令（SIGILL）**。**须在部署前实测**；缓解：选非 AVX2 基线的 wheel，或自源码编译（关 AVX2），或改选 `sentence-transformers`/纯 numpy 后备路径。**不得以「开发机可用」代替目标机实测**（AC-IB-07-05 同精神）。

---

## 11. 已评估未采纳：`POST /v1/embeddings` + `embeddings[][]`

| 项 | 内容 |
|---|---|
| 方案 | 采用 OpenAI 兼容面（`/v1/embeddings`，响应 `{"data":[{"embedding":[...]}], "model":..., "usage":...}`） |
| 优点 | 与业界生态一致；未来若以 TEI/Ollama 等替代实现，客户端可直接复用 |
| 未采纳理由 | ① **客户端已落盘**：`src/ib/embedding/__init__.py` 明确 POST `/embed` 且读 `vectors`，改路径即制造「服务端与客户端不同步」的 v1 断点；② **ADR-03 已登记** `ib-embed`（`/embed`、`/healthz`），改路径会使两份文档与单元文件三方不一致；③ 编号稳定性原则要求「能不改就不改」；④ 本基座只需单模型单稠密路径，OpenAI 兼容面的额外结构（`usage`/`data` 包装）无收益 |
| 若 PM 坚持改名的成本 | 1 处客户端路径常量 + 1 处响应键 + ADR-03 一处文字 + 本文件整体改写；**无架构影响**（不涉及模块、依赖边、IFC 号段） |
| 留痕 | 若未来以第三方推理服务器替代本服务（ADR-02 Option C 被重新评估），兼容面可经 **MOD-IB-09 的适配器**引入，**不需要**改变本服务的契约 |

---

## 12. 与编号体系的映射（R2 新增，既有编号 001~265 不动）

| IFC | 内容 |
|---|---|
| IFC-IB-266 | `POST /embed` 请求/响应结构（§3） |
| IFC-IB-267 | 维度权威性与三方一致性（§4.1） |
| IFC-IB-268 | 错误码表与统一错误体、4xx/5xx 分类不变式（§5） |
| IFC-IB-269 | `GET /healthz`（§6.1） |
| IFC-IB-270 | `POST /warmup`（§6.2） |
| IFC-IB-271 | `POST /descriptor`（§6.3） |
| IFC-IB-272 | 批上限、截断与「服务端 MAX_BATCH ≥ 客户端 cold_batch」硬约束（§4.2） |
| IFC-IB-273 | 冷/热双路径超时纪律的单一落点（§7） |
| IFC-IB-274 | 形态可逆（`http`/`inproc`/`fake`）+ 服务端配置键清单 + 端口一致性测试（§8、§9） |
| IFC-IB-275（在 `module_design.md` MOD-IB-09） | `InProcessBgeM3Embedder` 第三适配器 + 客户端 ↔ 线协议对接表 |

## 13. 残留与待判（不阻塞本契约落地）

1. **`/embed` 作为正式路径的确认**（§11）——若不确认，须同步改客户端常量与 ADR-03 文字。
2. **服务端库最终择一**（§10）——须目标机实测 `[TBD-T1/T3/T4/T18]` 后定，属 GROUP_C 实施判定。
3. **`ib-embed.env` 是否作为独立模板文件**（§9）——建议独立（避免污染 `ib-web.env` 的键集合）；须 PM 确认。
4. **`IB_EMBED_MEMORY_LIMIT_MB` 与单元文件 `MemoryMax=2560M` 的数值**——既有单元文件注释按「物理 4GB」写就，而目标机实为 **11GiB**：数值与注释须在 `[TBD-T4]` 实测后一并重定（**仅参数与注释，不改契约**）。
