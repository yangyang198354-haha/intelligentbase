<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part4</artifact>
  <path>docs/r2_apply_package_part4.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P4</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/architecture_design.md（AD-04 ~ AD-05：ADR-02-R2 附注 + §2.0.1 R2 影响复核表）</targets>
  <authoritative_contract path=docs/ib_embed_service_contract.md note=ADR-02-R2 附注的正文依据（服务端契约唯一落点）/这是本包对 ADR-02 的**唯一**改动：只加附注，不动 Decision/>
  <scope_boundary>只含编辑指令（锚点 + 新内容）。不含实现代码、伪代码、部署脚本、凭据或键值。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part4）— architecture_design.md（AD-04 ~ AD-05）

---

### AD-04 · architecture_design.md — ADR-02-R2 附注（L-03 补交）

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — 它是 **ADR-02-R1 复核**小节的最后一行）:
```text
- 与 Web 层的唯一关联是「Web 多 worker」这一**前提**（R1 下由 Waitress/Gunicorn 的 worker/线程配置承载，见 ADR-03-R1 与 [TBD-T15]），不改变本 ADR 的任何决策。
```
新内容（保留锚点行，其后追加附注块）:
```text
- 与 Web 层的唯一关联是「Web 多 worker」这一**前提**（R1 下由 Waitress/Gunicorn 的 worker/线程配置承载，见 ADR-03-R1 与 [TBD-T15]），不改变本 ADR 的任何决策。

**ADR-02-R2 附注（L-03 补交：`ib-embed` 的模块归属与契约单一落点）**

- **归属成立，且不改变本 ADR 的任何决策**：ADR-02 Option B 选定「本基座**自带**的轻量 HTTP 服务 + 独立 systemd 单元」。L-03 指出该服务此前**只有 systemd 单元与客户端、缺服务端模块归属与完整契约** —— R2 补上 **MOD-IB-26**（`module_design.md` §1 / §3）与**单列契约** `docs/ib_embed_service_contract.md`（IFC-IB-266~274）。**Options / Decision / Consequences 一字未改**，本条只是把既定决策的**落点补齐并写实**：从「有一个单元文件」升级为「有一个有归属、有契约、可被测试与门控的模块」。
- **冷/热双路径的单一落点仍成立，且落点在客户端（写成可测试口径）**：服务端**无状态、不区分冷热**；「冷路径（批量 / 长超时 / 多重试）vs 热路径（单条 / 短超时 / 少重试）」由**同一 HTTP 契约的两个客户端实例**承载（IFC-IB-273）。**服务端不得**为「让冷路径更成功」引入无界队列（那会把热路径一起拖死，违反有界延迟原则）；**服务端必须**显式配置并发与队列，并在超限时快速失败、回显 `retry_after_s`，同时以 `/healthz` 暴露 `queue_depth` / `inflight` 使降级可观测（AC-IB-13-02）。
- **形态可逆仍成立，且值域显式化**：`IB_EMBED_BACKEND ∈ {http, inproc, fake}`（**键名与默认值 `http` 不变**，仅**扩展值域**）。`inproc` 实现 `InProcessBgeM3Embedder` **位于 MOD-IB-09 之内**（**不 import MOD-IB-26**），故「切回进程内不改任何上层模块」这句话在 R2 之后仍是**类型可验证**的（见 `module_design.md` §4.1 / §4.2）。默认保持 `http` 的理由不变：进程内形态的模型内存 × worker 数风险（Option A 的缺点原样成立）与「与 onnxruntime（OCR）同进程」的叠加峰值 [TBD-T4']。
- **错误码语义映射不变式（R2 新增，随附注登记）**：`4xx / 409 = 「重试无用」`（配置或请求问题），`5xx = 「重试可能有用」`（暂时故障）。**这是客户端「4xx 不重试」实现（`if exc.code < 500: break`）能够成立的前提**：不得把暂时性故障放进 4xx；服务端也不得引入该分类之外的失败表达（例如用 `200` + 部分向量表示失败 —— 客户端在长度不符时会直接判为依赖不可用）。
- **单一落点纪律**：MOD-IB-26 的契约正文只在 `docs/ib_embed_service_contract.md`；`module_design.md` §3 是**摘要视图**，冲突时以契约文件为准并须回写摘要。
```

### AD-05 · architecture_design.md — 新增 §2.0.1 R2 影响复核表

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — 它是 §2.0 的**复核小结**段）:
```text
**复核小结**：受影响 **5 条**（ADR-03 / 07 / 08 / 11 / 13，其中 **ADR-11 为核心重写**）；不受影响 **8 条**（ADR-01 / 02 / 04 / 05 / 06 / 09 / 10 / 12，ADR-01 另有契约编号更正）。**无一条 ADR 未复核**。所有改动**不触及**模块数（25）、端口数（13）、IFC-IB 编号体系与 REQ→MOD 覆盖矩阵。
```
新内容（保留锚点段，其后追加小节）:
```text
**复核小结**：受影响 **5 条**（ADR-03 / 07 / 08 / 11 / 13，其中 **ADR-11 为核心重写**）；不受影响 **8 条**（ADR-01 / 02 / 04 / 05 / 06 / 09 / 10 / 12，ADR-01 另有契约编号更正）。**无一条 ADR 未复核**。所有改动**不触及**模块数（25）、端口数（13）、IFC-IB 编号体系与 REQ→MOD 覆盖矩阵。

### 2.0.1 R2 影响复核表（R2 补交：`ib-embed` 服务端归属 + M-02 页面图绑定）

> **口径**：R2 是**追加式增量**（新增模块 1 个、新增 IFC 段、新增读路径端点与关联表），**不改既有契约**。凡决策客体未被 R2 增量触及者，一律**显式声明「R2 不受影响」**，以便门控区分「已检查」与「漏检查」。以下逐条覆盖 ADR-01 ~ ADR-13（**无一条跳过**）。

| ADR | R2 复核结论 | 一句话理由 |
|-----|-------------|-----------|
| ADR-01 | **R2 不受影响** | Qdrant 端口与 collection 维度声明未动；M-02 的图片关联落在**台账（SQLite）**而非向量库 payload，不触碰 `PointPayload` / `CollectionSpec`（IFC-IB-001~012、100~110 不变） |
| **ADR-02** | **受影响（仅补附注；Decision / Options / Consequences 不变）** | 见上方 **ADR-02-R2 附注**：补齐 `ib-embed` 的服务端模块归属（MOD-IB-26）与契约单一落点；形态可逆**值域**显式化 |
| ADR-03 | **R2 不受影响** | systemd 单元清单仍为四个（`ib-embed` 单元**早已存在**）；R2 未新增单元、未改 `ib-web` 载体；第二份 `EnvironmentFile`（IFC-IB-286）是 ADR-03 既定做法「每单元一个 EnvironmentFile」的**补齐**，非新决策 |
| ADR-04 | **R2 不受影响** | 隔离机制未动：`Scope` 仍**必填**、`CollectionResolver` 仍为**唯一**解析入口；M-02 的图片端点与关联表**一律带 `scope` 并复用归属断言**（IFC-IB-283 的 403/404 口径与 §1.4 第 2 条一致）——是 ADR-04 的**应用**而非修改 |
| ADR-05 | **R2 不受影响** | 原文件内容寻址与重建流程未动；`ChunkImageRecord` 是**派生关联元数据**（可由原文件重建），**不成为新的真源**；重建时随文档重跑再生，**不改 `fingerprint` 因子** |
| ADR-06 | **R2 不受影响** | PDF 库选型与三路径未动；M-02 消费的是解析**已产出**的页面图信息，**不引入任何新 PDF 库**（尤其**未引入 PyMuPDF / AGPL-3.0**） |
| ADR-07 | **R2 不受影响** | 台账仍为 SQLite + `LedgerRepository` 端口 + 自管 SQL + **手写 scoped 迁移**；新增关联**表**经同一端口与同一迁移纪律落地，**不经 Django ORM**；写序仍为「向量成功后才置 `indexed`」 |
| ADR-08 | **R2 不受影响** | LLM 端点抽象与外发边界未动；M-02 **不外发图片字节**（`related_images` 只传**站内** `url_path`），`describe_egress()` 的 `data_categories` **无需扩项** |
| ADR-09 | **R2 不受影响** | 骨架业务零依赖未动；`related_images` 是流事件的**既有 `kind`**（IFC-IB-224 早已枚举），R2 只定义其**载荷类型**，不向骨架注入业务语义 |
| ADR-10 | **R2 不受影响** | 异步入库仍以台账表为队列；`bind_page_images` 为**纯函数**、`persist_page_images` 在同事务内，**不新增任务类型、不改租约语义** |
| ADR-11 | **R2 不受影响** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；新端点 IFC-IB-283 是**普通 HTTP 响应（非流式）**，不占用 worker 长连接预算，与 [TBD-T15] 的容量纪律相容；「禁止 `?token=`」纪律在 R2 **扩展到全部端点**（含图片端点） |
| ADR-12 | **R2 不受影响** | OCR 与渲染**两个端口**及降级语义未动；M-02 把 OCR 产出的页面图**关联**到同页文字块，是**消费**既有的 `ParsedChunk.page_or_section` / `locator` / `source_kind`，不改端口签名 |
| ADR-13 | **R2 不受影响** | `RetrievalResult` 字段与降级语义未动；`related_images` 走**独立的流事件**而非并入 `RetrievalResult`，故「故障 vs 空结果可区分」的不变式不受影响；R2 另为 §7.4 增补一格降级行 |

**R2 复核小结**：**受影响 1 条**（ADR-02，且**仅补附注**）；**R2 不受影响 12 条**（ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13）。**无一条 ADR 未复核**。R2 的所有改动**不触及**：端口数（13）、`IFC-IB-001~265` 编号体系、REQ→MOD 覆盖矩阵（仍 24/24 + 14）与 DAG 无环性（模块数 25 → 26，纯追加）。
```

---

（part4 结束；ADR-04 / 06 / 11 / 13 的 inline 复核句、§9 TBD 追加、§10.3 自检行见 `docs/r2_apply_package_part5.md`）
