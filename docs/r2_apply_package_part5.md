<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part5</artifact>
  <path>docs/r2_apply_package_part5.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P5</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/architecture_design.md（AD-06 ~ AD-11）；docs/tech_stack.md（TS-01 ~ TS-03）</targets>
  <scope_boundary>只含编辑指令（锚点 + 新内容）。不含实现代码、伪代码、部署脚本、凭据或键值。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part5）— architecture_design.md（AD-06~AD-11）+ tech_stack.md（TS-01~TS-03）

---

## 1. architecture_design.md（续）

### AD-06 · ADR-04 之后追加 inline R2 复核句

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — ADR-04-R1 的最后一行为「残留风险」）:
```text
- **残留风险（不变）**：知识库级漏 filter 即泄漏（FM-1）；防护为「类型系统 + 归属断言 + 单入口解析 + 启动期断言」四重。若未来判定须硬隔离，成本仍被收敛在「改解析规则 + 改配置结构」，上层零改动。
```
新内容（保留锚点行，其后追加一行）:
```text
- **残留风险（不变）**：知识库级漏 filter 即泄漏（FM-1）；防护为「类型系统 + 归属断言 + 单入口解析 + 启动期断言」四重。若未来判定须硬隔离，成本仍被收敛在「改解析规则 + 改配置结构」，上层零改动。

**ADR-04-R2 复核**：**R2 不受影响** —— M-02 的图片端点（IFC-IB-283）与关联表（IFC-IB-279）**一律带 `scope`** 并复用归属断言；隔离粒度、`Scope` 必填与 `CollectionResolver` 单入口**均未动**（R2 是 ADR-04 的应用，不是修改）。
```

### AD-07 · ADR-06 之后追加 inline R2 复核句

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — ADR-06-R1 的「不变项」行）:
```text
- 不变项：文本三路径（文本层 / 内嵌图像 OCR / 扫描页栅格化 + OCR）、主 / 回退顺序可配置（由 [TBD-T8] 决定）、**三纯 Python 库均不能渲染故渲染必须另选 `pypdfium2`**、许可合规留痕（**不采纳 PyMuPDF / AGPL-3.0，且明确撤除「内部平台合规」口径**）—— 全部不变。
```
新内容（保留锚点行，其后追加一行）:
```text
- 不变项：文本三路径（文本层 / 内嵌图像 OCR / 扫描页栅格化 + OCR）、主 / 回退顺序可配置（由 [TBD-T8] 决定）、**三纯 Python 库均不能渲染故渲染必须另选 `pypdfium2`**、许可合规留痕（**不采纳 PyMuPDF / AGPL-3.0，且明确撤除「内部平台合规」口径**）—— 全部不变。

**ADR-06-R2 复核**：**R2 不受影响** —— R2 **未引入任何新 PDF 库**；M-02 只**消费**解析已产出的页面图关联信息（`ParsedChunk.page_or_section` / `locator` / `source_kind` 均为既有字段）。**注（R2 新发现，见 [TBD-T18]）**：OCR 链路的 `onnxruntime` 与 R2 的 embedding 推理运行时**同受「目标机 CPU 指令集基线」风险**约束，但该风险**不改变**本 ADR 的库选型结论（缓解与判定见 `tech_stack.md` §5.2）。
```

### AD-08 · ADR-11 之后追加 inline R2 复核句

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — ADR-11-R1 复核的最后一行为「与其他 ADR 的衔接」）:
```text
- 与其他 ADR 的衔接：容量与进程载体的落点在 **ADR-03-R1**；容量参数在 **[TBD-T15]**；模块侧的映射见 `module_design.md` §2.1.1。
```
新内容（保留锚点行，其后追加一行）:
```text
- 与其他 ADR 的衔接：容量与进程载体的落点在 **ADR-03-R1**；容量参数在 **[TBD-T15]**；模块侧的映射见 `module_design.md` §2.1.1。

**ADR-11-R2 复核**：**R2 不受影响** —— 流式仍为 Django 同步视图 + `StreamingHttpResponse` 原生 SSE（Option A），Option B 的量化触发条件与 Option C 的拒绝结论**均未动**；R2 新增的图片端点（IFC-IB-283）是**普通 HTTP 响应（非流式）**，**不占用 SSE 长连接预算**，与 [TBD-T15] 的容量纪律相容；强制约束 (a)「禁止 `?token=`」在 R2 中**扩展到全部端点**（含图片端点）。
```

### AD-09 · ADR-13 之后追加 inline R2 复核句

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — ADR-13-R1 的「复核结论」行）:
```text
- **复核结论**：仅**载体表达形式**变化，契约为**等价升级**；对上层（MOD-IB-15 调用方、MOD-IB-17 工具、MOD-IB-21 流事件）**零语义改动**。
```
新内容（保留锚点行，其后追加一行）:
```text
- **复核结论**：仅**载体表达形式**变化，契约为**等价升级**；对上层（MOD-IB-15 调用方、MOD-IB-17 工具、MOD-IB-21 流事件）**零语义改动**。

**ADR-13-R2 复核**：**R2 不受影响** —— `RetrievalResult` 的字段与降级语义未动；`related_images` 走**独立的流事件**而**不并入** `RetrievalResult`，故「依赖故障 vs 空知识库可区分」（AC-IB-14-02）的不变式保持；R2 另在 `module_design.md` §7.4 为「`ib-embed` 服务不可达」与「页面图不可得」各补一格降级行（前者映射到既有 `degrade_reason`，**不新增枚举值**）。
```

### AD-10 · §9 TBD 清单 — 追加 T16 / T17 / T18

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — §9 表的最后一行，即 TBD-T15 行）:
```text
| **TBD-T15（R1 新增）** | **SSE 并发上限**：单实例可同时承载的 **SSE 长连接数** + 对应 **worker/线程配置**（Waitress `--threads`；Gunicorn `--workers` × `gthread` 线程数），以及达到上限时的实际行为 | REQ-FUNC-IB-21；REQ-NFR-IB-13；**ADR-11-R1 / ADR-03-R1** | 决定 **Option A 的容量参数**；判定**是否触发 Option B 升级路径**（Django 异步视图 + `uvicorn.workers.UvicornWorker`，**仍不含 Channels / Redis**）；实测须同时确认池满时**快速失败 `503`**（fail-closed）**而非排队**，且未拖垮非流式端点 |
```
新内容（保留锚点行，其后追加三行）:
```text
| **TBD-T15（R1 新增）** | **SSE 并发上限**：单实例可同时承载的 **SSE 长连接数** + 对应 **worker/线程配置**（Waitress `--threads`；Gunicorn `--workers` × `gthread` 线程数），以及达到上限时的实际行为 | REQ-FUNC-IB-21；REQ-NFR-IB-13；**ADR-11-R1 / ADR-03-R1** | 决定 **Option A 的容量参数**；判定**是否触发 Option B 升级路径**（Django 异步视图 + `uvicorn.workers.UvicornWorker`，**仍不含 Channels / Redis**）；实测须同时确认池满时**快速失败 `503`**（fail-closed）**而非排队**，且未拖垮非流式端点 |
| **TBD-T16（R2 新增）** | `ib-embed` 服务端的**并发与线程校准**：`IB_EMBED_MAX_CONCURRENCY` / `IB_EMBED_THREADS` / `IB_EMBED_QUEUE_DEPTH` 在目标机的最优值，以及它与 Qdrant / `ib-web` / OCR **同为 CPU 竞争者**时的叠加影响 | REQ-NFR-IB-03；ADR-02；`ib_embed_service_contract.md` §9 | 定服务端并发 / 队列 / 线程参数，并**据实重定** `IB_EMBED_MEMORY_LIMIT_MB`（目标机 11GiB，须与单元文件 `MemoryMax` 一并重定，见契约 §13 第 4 项） |
| **TBD-T17（R2 预留，未分配）** | ——（R2 保留号；目的：防止下游为**同一指标**另起一个号） | — | 供 GROUP_C 追加实测项时**按序取用**；**R2 未使用** |
| **TBD-T18（R2 新增）** | **目标机 CPU 指令集基线实测**：目标机 CPU（Intel i7-3770S / Ivy Bridge）具备 **AVX 但无 AVX2**；须实测候选预编译 wheel（**① 既有 OCR 链路的 `onnxruntime` 系；② R2 的 embedding 推理运行时**）在该机上是否会触发 **SIGILL（非法指令，进程级崩溃，不可捕获）** | REQ-NFR-IB-10；AC-IB-07-05；ADR-02 / ADR-06 / ADR-12 | 决定 wheel 选型 / 是否**自源码编译并关闭 AVX2** / 是否改用纯 Python 后备路径；**不得以「开发机可用」代替目标机实测**（AC-IB-07-05 同精神）。**两条链路同源，须一次性合并评估**，否则排障会归因错误 |
```

### AD-11 · §10.3 自检声明 — 追加 R2 行

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄 — §10.3 的最后一行）:
```text
- **（R1）需求侧与 FreeArk 未受影响**：`requirements_spec.md` / `user_stories.md` **未作任何修改**；`FreeArk` 仓库**任何文件未作任何修改**。
```
新内容（保留锚点行，其后追加）:
```text
- **（R1）需求侧与 FreeArk 未受影响**：`requirements_spec.md` / `user_stories.md` **未作任何修改**；`FreeArk` 仓库**任何文件未作任何修改**。
- **（R2）L-03 补交已闭合**：`ib-embed` 具**模块归属**（MOD-IB-26）与**契约单一落点**（`docs/ib_embed_service_contract.md`，IFC-IB-266~274）；ADR-02 追加 **R2 附注**（Decision 未改）；新增 **§2.0.1 R2 影响复核表**（**受影响 1 条**（ADR-02，仅补附注）／**R2 不受影响 12 条**，无一条跳过），并为 ADR-04 / 06 / 11 / 13 追写 inline 复核句。
- **（R2）不变约束未被破坏**：`IFC-IB-001~265` 一字不动（新增 266~284 / 286；285 预留未分配）；端口数仍 **13**；REQ→MOD 覆盖仍 **24/24 REQ-FUNC + 14 NFR**；依赖图**仍为 DAG**（模块数 25 → 26，新增单边 `26 → {01,02,04}` 且 26 无入边）；**错误码语义映射不变式**（4xx/409 = 重试无用，5xx = 重试可能有用）已随 ADR-02-R2 附注登记。
- **（R2）凭据纪律**：全文仍只登记**键名**；`ib-embed` **不需要任何令牌**；**URL 与文档一律不得出现凭据型查询串**（该纪律在 R2 扩展至**全部**端点，含新增的图片端点）。
```

---

## 2. tech_stack.md（TS-01 ~ TS-03）

### TS-01 · tech_stack.md — 文件头版本与修订号

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
  <version>1.1.0</version>
  <revision>R1</revision>
```
新内容（整段替换锚点）:
```text
  <version>1.2.0</version>
  <revision>R2</revision>
```

### TS-02 · tech_stack.md — 追加 revision_history 条目

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
  </revision_history>
```
新内容（在锚点**之前**插入一条 rev，再保留锚点）:
```text
    <rev version="1.2.0" revision="R2" date="2026-09-26" invocation_id="INV-GROUP_B-INTELBASE-004" note="R2 补交（L-03）：① 「Embedding 推理运行时」行改写为三候选（FlagEmbedding / sentence-transformers / 直接 onnxruntime 载 bge-m3 的 ONNX 导出），补记许可、CPU-only 可用性、传递依赖与指令集基线风险；② §2 许可台账补登传递依赖 torch（BSD-3-Clause）与 transformers（Apache-2.0），均标条件性采纳；③ 新增 §1.2「服务端配置键登记」（只登记键名与语义，不含任何值，覆盖 IFC-IB-286 的第二份 EnvironmentFile）；④ §5.2 新增一行中风险：目标机 CPU 缺 AVX2 致预编译 wheel 触发 SIGILL（同时命中既有 OCR 链路与 R2 的 embedding 推理运行时），缓解与判定指向 [TBD-T18]；⑤ 编号稳定：既有条目类别/行序尽量沿用，被改写者标「（R2 改写）」；未引入 PyMuPDF、未引入 Docker（DR-03）。需求侧文档与 FreeArk 仓库未改动。"/>
  </revision_history>
```

### TS-03 · tech_stack.md — 首部版本行与 R2 修订摘要

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
**版本**: 1.1.0（R1 修订） | **状态**: DRAFT（待 PM 门控评审）| **日期**: 2026-09-25
```
新内容（整段替换锚点）:
```text
**版本**: 1.2.0（R2 补交） | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26

**R2 修订摘要（L-03：`ib-embed` 服务端无模块归属与契约）**：

| 序 | 改动 | 落点 |
|----|------|------|
| 1 | 「Embedding 推理运行时」行**改写为三候选**（含直接 `onnxruntime` 载 ONNX），补许可 / CPU-only 可用性 / 传递依赖 / 指令集基线风险 | §1 该行（标「R2 改写」） |
| 2 | 许可台账**补登传递依赖** `torch` / `transformers`（均条件性采纳） | §2 |
| 3 | 新增 **§1.2 服务端配置键登记**（**只登记键名与语义，不含任何值**） | §1.2（新增） |
| 4 | 新增一行中风险：**目标机缺 AVX2 → 预编译 wheel 触发 SIGILL**（同时命中既有 OCR 链路与 R2 的 embedding 运行时） | §5.2 |
| 5 | **编号与许可稳定**：既有条目的类别、行序、条目名尽量沿用；被改写者标「（R2 改写）」；未引入任何 AGPL / copyleft 新面，**未引入 PyMuPDF、未引入 Docker** | 全文 |
```

---

（part5 结束；许可台账新增行、§1.2 配置键、§5.2 风险行与计数/残余项见 `docs/r2_apply_package_part6.md`）
