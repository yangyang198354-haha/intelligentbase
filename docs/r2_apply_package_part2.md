<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part2</artifact>
  <path>docs/r2_apply_package_part2.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P2</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/module_design.md（条目 MD-09 ~ MD-16）</targets>
  <scope_boundary>只含编辑指令（锚点 + 新内容）。不含实现代码、伪代码、部署脚本、凭据或键值。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part2/7）— module_design.md（MD-09 ~ MD-16）

> 施加方式同 part1：用「锚点」在 `docs/module_design.md` 唯一定位（锚点为原文照抄），把锚点整段替换为「新内容」。多锚点条目以 A/B/C 标出。

---

### MD-09 · module_design.md — §3 MOD-IB-09 R2 增补（L-03 对接）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
- **外部依赖**: 本基座 `ib-embed` HTTP 服务；HTTP 客户端（stdlib）
```
新内容（保留锚点行，其后追加）:
```text
- **外部依赖**: 本基座 `ib-embed` HTTP 服务；HTTP 客户端（stdlib）
- **R2 增补（L-03 服务端对接）**:
  - IFC-IB-275: `InProcessBgeM3Embedder`（**第三种适配器形态**，本模块**之内**实现）。**不 import MOD-IB-26**——否则产生 `09 → 26` 的非法反向依赖边。装配由 `IB_EMBED_BACKEND=inproc` 选择。
  - **客户端 ↔ 线协议对接表（服务端必须逐条遵守；此表是「已落盘客户端事实」的登记，不是新设计）**：
    | 项 | 客户端已落盘事实（`src/ib/embedding/__init__.py`） | 服务端义务 |
    |----|-----------------------------------------------|------------|
    | 路径 / 请求体 | `POST /embed`，体 `{"texts": [...], "model": ..., "mode": "document"\|"query"}` | 沿用 `/embed`；**不改 `/v1/embeddings`**（改即制造服务端与客户端不同步的 v1 断点） |
    | 响应键 | 读 `vectors` | 返回 `vectors` |
    | 长度 | `len(vectors) != len(texts)` 即抛 `DependencyUnavailableError` | **必须等长**，绝不返回部分向量 |
    | 维度 | `len(vec) != dim` 即抛 | 必须 `== dim == 1024` |
    | 健康 | `GET /healthz` 读 `ok` / `detail`，**永不抛** | 永不 5xx、永不异常 |
    | 预热 | `POST /warmup` 超时 `max(cold_timeout, 300s)`、重试 1、失败仅 WARN | **幂等**；快速失败而非挂死到超时 |
    | 自描述 | `POST /descriptor` 读五字段；失败回落配置值 | 字段名与 MOD-IB-01 `EmbedderDescriptor` **逐字段一致** |
    | 重试分类 | `if exc.code < 500: break`（4xx 不重试） | 错误码分类必须与「4xx=配置/请求错、5xx=暂时故障」严格对齐 |
- **R2 形态一致性强约束**：`http` / `inproc` / `fake` 三形态必须通过**同一套端口一致性测试**（沿用 AC-IB-06-05 的做法）——`descriptor()` 五字段逐字段一致、`dim` / `normalized` 一致、同文本余弦 ≈ 1；否则形态切换会**静默改变写入语义**。
```

### MD-10 · module_design.md — §3 MOD-IB-13 R2 五条（M-02）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
- **外部依赖**: 无（第三方库经 MOD-IB-05/06/08/09/10 隔离）
```
新内容（保留锚点行，其后追加）:
```text
- **外部依赖**: 无（第三方库经 MOD-IB-05/06/08/09/10 隔离）
- **R2 增补（M-02：页面图 ↔ 文块绑定）**:
  - **根因（留痕）**：页面文字块与水印/插图 OCR 块此前出自**两次解析产出**，检索命中文字块时**无任何指向同页图片的引用**，导致问答链路「图明明在库里却取不到」。R2 把该关联**在入库期固化**，而不是在检索期做启发式猜测。
  - IFC-IB-277: `bind_page_images(parsed: ParsedDocument, *, doc_id: str) -> list[PageImageBinding]`（**纯函数、无 IO**）：按 `page_or_section` 把该页的 `PageImageRef` 聚合为一条 `PageImageBinding`。同一页的图文块共享同一 `page_or_section` 键即完成绑定；**不向 `ParsedChunk` 追加字段**（避免改动 IFC-IB-009 契约）。
  - IFC-IB-278: `persist_page_images(scope: Scope, doc_id: str, bindings: Sequence[PageImageBinding]) -> int`：按幂等键写入关联表；时机为**向量写入成功之后、台账置 `indexed` 之前**（与 ADR-07 写序一致，保证「`indexed` ⇒ 关联已就绪」）。
  - IFC-IB-279: 关联持久化模型 `ChunkImageRecord`（字段级）：`project_id: str`；`kb_id: str`；`doc_id: str`；`page_or_section: str`；`image_id: str`；`source_kind: str`；`locator: str`；`blob_ref: str | None`；`doc_name: str`；`created_at: str`。**幂等键** = `(project_id, kb_id, doc_id, page_or_section, image_id)`（重跑覆盖同一行，不产生重复）。
  - IFC-IB-280: `process_pending`（IFC-IB-143，**签名与返回类型不变**）的 R2 步骤扩展——七步 → 九步：在**切分**之后、**向量化**之前插入 ① `bind_page_images`；在**写入**之后、**台账置位**之前插入 ② `persist_page_images`。两步**不得**改变既有失败粒度（文档级仍整体 `failed`，页级仍只跳过该页 —— §6.4 不变）。
  - IFC-IB-281（**删除零改动不变式声明**）：`delete_document(scope, doc_id)`（IFC-IB-144）**签名、返回类型与语义一字不改**；关联行随 `(project_id, kb_id, doc_id)` **级联删除**（同一事务内按 scope 删除），故 `DeleteReport` 三个计数（`vectors_deleted` / `blob_deleted` / `ledger_deleted`）语义不变；删除重放对账（IFC-IB-131 `list_orphan_doc_ids`）**不新增用例**。**本项不需要新代码路径，故不引入新 IFC 签名 —— 仅登记为不变式。**
```

### MD-11 · module_design.md — §3 MOD-IB-21 R2（related_images 载荷）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
  - IFC-IB-225: `to_sse(event: StreamEvent) -> str`（`event:` / `data:` 帧编码）
```
新内容（保留锚点行，其后追加）:
```text
  - IFC-IB-225: `to_sse(event: StreamEvent) -> str`（`event:` / `data:` 帧编码）
  - IFC-IB-282（R2）: `related_images` 事件的**载荷类型化** = `RelatedImagesPayload`（§2.1）。`data` 为该结构的 JSON 编码；**只传 `image_id` 与 `url_path`（站内相对路径），绝不内联图片字节或 base64** —— 帧体积有界，不阻塞流。事件在 `content` 之后、`done` 之前发出；**无图时不发该事件**（而非发空载荷）。`StreamEventKind` 的取值集合**不变**（`related_images` 早已在 IFC-IB-224 中枚举，R2 只定义其 data）。
```

### MD-12 · module_design.md — §3 MOD-IB-23 R2（图片端点）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
- **外部依赖**: `django`、`djangorestframework`、`waitress`（主 WSGI）、`gunicorn`（备 WSGI）；并发升级路径见 tech_stack §1（Gunicorn + `uvicorn.workers.UvicornWorker`，默认关闭）
```
新内容（保留锚点行，其后追加）:
```text
- **外部依赖**: `django`、`djangorestframework`、`waitress`（主 WSGI）、`gunicorn`（备 WSGI）；并发升级路径见 tech_stack §1（Gunicorn + `uvicorn.workers.UvicornWorker`，默认关闭）
- **R2 新增端点（M-02 读路径）**:
  - IFC-IB-283: `GET /api/files/{doc_id}/images/{image_id}` → `200`（`Content-Type: image/*`，字节流，可缓存）| `403`（归属断言失败）| `404`（文档或图片不存在；**不区分「不存在」与「不属于你」**，避免存在性探测 —— 沿用 §1.4 第 2 条口径）| `503`（BlobStore 不可用；**fail-closed**：直接报错，不返回占位图）。
  - **鉴权纪律（强制）**：沿用 IFC-IB-247 的口径，**仅允许 `Authorization` 头** / 中间件鉴权；本端点**不接受** `?token=`（MOD-IB-21 的鉴权纪律对**全部**端点生效，R2 显式扩展到图片端点）。
  - **单一取图入口**：前端与 SSE 载荷一律只引 `url_path`，字节一律经本端点按需获取。
  - `GET /healthz/deps`（IFC-IB-249）的字段集合**不变**：取图依赖 BlobStore，其健康语义已由既有字段与 §7.4 覆盖，**不新增字段**。
```

### MD-13 · module_design.md — §3 MOD-IB-24 R2（渲染约束）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
- **外部依赖**: Vue 3、Vite、构建产物由 `ib-web` 静态托管
```
新内容（保留锚点行，其后追加）:
```text
- **外部依赖**: Vue 3、Vite、构建产物由 `ib-web` 静态托管
- **R2 渲染约束（IFC-IB-284）**:
  - `related_images` 事件到达时，在**该轮回答下方**以缩略图行渲染（点击经 IFC-IB-283 取原图）；**不得**插入正文中间，**不得**改写 `content` 文本。
  - 渲染顺序 = 载荷顺序（服务端按 `page_or_section` 升序给出，**前端不重排**）。
  - 图片加载失败 / 端点 `403` / `404` / `503` → **静默隐藏该缩略图**（不弹错误、不中断流、**不追加降级文案**）。降级文案**只对 `degraded` 事件负责** —— 避免同一观察点出现两种降级语义，对齐 ADR-13「故障与空结果可区分」。
```

### MD-14 · module_design.md — §3 MOD-IB-25 R2（第二份环境模板键）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
  - IFC-IB-265: Qdrant 安装检查清单（专用用户 / `storage`+`snapshots` 目录 / unit 文件 / `LimitNOFILE`）
```
新内容（保留锚点行，其后追加）:
```text
  - IFC-IB-265: Qdrant 安装检查清单（专用用户 / `storage`+`snapshots` 目录 / unit 文件 / `LimitNOFILE`）
  - IFC-IB-286（R2）: `ib-embed` 的 `EnvironmentFile` 模板（**第二份 `.env.example`**，与 `ib-web` 的键集合**分离**）。**只登记键名、不含任何值**；键名清单见 `tech_stack.md` §1.2，语义与默认值见 `docs/ib_embed_service_contract.md` §9。**凭据纪律**：该服务**不需要任何令牌**，不得向该文件写入任何凭据（加进去就是净增凭据面）。
  - R2 重申：IFC-IB-261 的**单元清单不变**（`ib-embed` 单元**早已存在**；L-03 缺的是**模块归属与契约**，不是单元文件）；IFC-IB-263 的「只报键名、不回显值、非零码退出」纪律对第二份模板同样生效。
```

### MD-15 · module_design.md — §3 新增 MOD-IB-26 小节（摘要视图）

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
- **外部依赖**: `systemd`
```
新内容（保留锚点行，其后追加新小节；新小节插在 §3 末、`## 4.` 之前）:
```text
- **外部依赖**: `systemd`

### MOD-IB-26 ib-embed 服务端 (L2；服务端进程)

> **R2 新增（L-03 补齐）**。**本节为摘要视图**；唯一权威为 `docs/ib_embed_service_contract.md`，二者冲突时**以契约文件为准**。本模块**不含部署配置**（部署配置属 MOD-IB-25）。

- **职责**: bge-m3 常驻推理服务的**线协议实现与模块归属**；单模型常驻、CPU-only、有界并发 + 有界队列、超限快速失败（绝不无界排队）。
- **覆盖需求**: REQ-FUNC-IB-15（本地 embedding，服务端侧）；REQ-FUNC-IB-22（`ib-embed` 单元交付物）；REQ-NFR-IB-03（检索性能的服务端侧）；REQ-NFR-IB-10（CPU-only 可运行）
- **公开接口契约（HTTP 线协议）**:
  - IFC-IB-266: `POST /embed`（请求 `texts`/`model`/`mode`；响应 `vectors`/`dim`/`model_id`/`normalized`/`count`/`elapsed_ms`；**保序**；**绝不返回部分向量**）
  - IFC-IB-267: 维度权威性与**三方一致性**（服务端真实维度 → 客户端 `IB_EMBED_DIM` → `CollectionSpec.dim`；三者任一不符须在最早可发现处失败）
  - IFC-IB-268: 错误码表与统一错误体 `{code, detail, max_batch?, retry_after_s?}`，含**分类不变式：`4xx/409 = 重试无用`，`5xx = 重试可能有用`**
  - IFC-IB-269: `GET /healthz`（**永不 5xx、永不抛**；客户端只读 `ok` / `detail`，其余字段为附加且向后兼容）
  - IFC-IB-270: `POST /warmup`（**幂等**；须在 300s 量级内完成或快速失败，**不得挂死到超时**）
  - IFC-IB-271: `POST /descriptor` → `EmbedderDescriptor`（五字段与 MOD-IB-01 **逐字段一致**，不得新增/改名）
  - IFC-IB-272: 批上限 / 单条截断保前缀 / **服务端 `MAX_BATCH` ≥ 客户端 `cold_batch_size`** 硬约束（错误体回显 `max_batch`，使配置错配一眼可定位）
  - IFC-IB-273: 冷/热双路径超时纪律的**单一落点** —— **服务端不区分冷热**（无状态 HTTP），冷热差异全部由**客户端的两个实例**承载
  - IFC-IB-274: 形态可逆（`http`/`inproc`/`fake`）+ 服务端配置**键名**清单 + 端口一致性测试
- **依赖模块**: MOD-IB-01（契约 / 枚举）、MOD-IB-02（配置）、MOD-IB-04（可观测性）
- **外部依赖**: 服务端推理运行时（候选与许可见 `tech_stack.md` §1「Embedding 推理运行时」行）；bge-m3 本地权重（**离线加载**）
- **不被 import 声明（R2 强制）**: 本模块**不被任何模块 import** —— 上层只经 `Embedder` 端口（MOD-IB-09）与线协议访问（与 MOD-IB-10 对 Qdrant 服务同构）。这是 §4.2 无环论证在本模块上的**唯一依据**，也是「形态可逆」成立的前提（进程内形态不得依赖服务端）。
```

### MD-16 · module_design.md — §4.1 依赖边清单新增一条

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
MOD-IB-25 → 01, 02, 04（交付物形态，非编译期依赖）
```
新内容（保留锚点行，其后追加一行）:
```text
MOD-IB-25 → 01, 02, 04（交付物形态，非编译期依赖）
MOD-IB-26 → 01, 02, 04（**本模块不被任何模块 import**；只走线协议，非编译期依赖）
```

---

（part2 结束；续见 `docs/r2_apply_package_part3.md`）
