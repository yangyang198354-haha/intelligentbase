<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part3</artifact>
  <path>docs/r2_apply_package_part3.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P3</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/module_design.md（MD-17 ~ MD-22）；docs/architecture_design.md（AD-01 ~ AD-05）</targets>
  <scope_boundary>只含编辑指令（锚点 + 新内容）。不含实现代码、伪代码、部署脚本、凭据或键值。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part3）— module_design.md（MD-17~MD-22）+ architecture_design.md（AD-01~AD-05）

---

## 1. module_design.md（续）

### MD-17 · §4.2 无环证明 — R2 补句

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
**该性质是设计约束而非巧合**：模块编号按**拓扑序**分配，新增模块须选取「大于其全部依赖编号」的编号；若出现「新需求使某模块需要依赖编号更大的模块」，则说明**分层被破坏**，必须先重构分层（例如下沉契约或引入端口），不得直接加边。这条纪律写在此处，作为后续 GROUP_C 的架构约束。
```
新内容（保留锚点段，其后追加）:
```text
**该性质是设计约束而非巧合**：模块编号按**拓扑序**分配，新增模块须选取「大于其全部依赖编号」的编号；若出现「新需求使某模块需要依赖编号更大的模块」，则说明**分层被破坏**，必须先重构分层（例如下沉契约或引入端口），不得直接加边。这条纪律写在此处，作为后续 GROUP_C 的架构约束。

**R2 补句（新增模块的权值校验）**：R2 新增的 `MOD-IB-26` 只有三条出边 `→ 01, 02, 04`，且 `w(26) = 26 > max{w(01), w(02), w(04)} = 4` —— 权值严格递减的性质**保持不变**；同时 26 号模块**没有任何入边**（不被任何模块 import），因此**不可能出现在任何环上**。**结论：R2 后依赖图仍为 DAG。**
```

### MD-18 · §4.3 分层视图 — 补一行

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
L2  MOD-IB-06  08  09(含 CollectionResolver)  10
```
新内容（整段替换锚点）:
```text
L2  MOD-IB-06  08  09(含 CollectionResolver)  10   26(独立服务端进程；不被任何模块 import)
```

### MD-19 · §5 组合根装配表 — Embedder 行与形态可逆说明

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
| `Embedder` | `LocalHttpEmbedder`（→ `ib-embed`） | `FakeEmbedder` | `IB_EMBED_BACKEND=http\|fake` |
```
新内容（整段替换锚点）:
```text
| `Embedder` | `LocalHttpEmbedder`（→ `ib-embed`，MOD-IB-26 服务端） | `FakeEmbedder` / `InProcessBgeM3Embedder` | `IB_EMBED_BACKEND=http\|inproc\|fake`（**R2 仅扩展值域；键名与默认值 `http` 不变**） |
```
**并在该表之后追加一段说明**（锚点 = 表后的一句 `**一键离线**：...`，在其**之前**插入；若定位不便，可与上表同段落一并插入）:
```text
> **R2 形态可逆开关说明**：`inproc` = 进程内 `InProcessBgeM3Embedder`（位于 **MOD-IB-09 之内**，**不 import MOD-IB-26**）；切换代价 = 改一个配置值 +（可选）停用 `ib-embed` 单元，**不改任何上层模块、不改 IFC 签名、不改任何既有键名**。三形态须通过**同一套端口一致性测试**（见 §3 MOD-IB-09）。默认保持 `http`：进程内形态的模型内存 × worker 数风险与「与 onnxruntime 同进程」的内存叠加峰值（[TBD-T4']）仍未实测。
> （R2 附：`IB_EMBED_BACKEND` 的**值域**扩展与 `IB_OFFLINE_MODE=1` 的一键离线语义**相容**——离线时仍取该表的「离线/测试」列。）
```

### MD-20 · §7.4 降级矩阵 — 新增两行

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
| **Embedding** | 热路径超时（短超时触发） | 同上，`degrade_reason=timeout` | 同上 | WARN | fail-open |
```
新内容（保留锚点行，其后追加两行）:
```text
| **Embedding** | 热路径超时（短超时触发） | 同上，`degrade_reason=timeout` | 同上 | WARN | fail-open |
| **ib-embed 服务（MOD-IB-26）** | 不可达 / 未预热（`model_not_ready`）/ 队列满（`overloaded`）/ 服务端推理超时（`inference_timeout`） | 检索侧 `degraded=True`：不可达 → `degrade_reason=embedding_unavailable`；热路径超时 → `timeout`；**问答继续**。冷路径（入库）**不在此列**：由客户端重试预算承载，耗尽则**文档级** `failed` + `error_code`（**不阻塞其他文档**） | 「当前未接入知识资料库」 | WARN | fail-open（读路径）；冷路径为文档级失败隔离 |
| **页面图（M-02）** | 关联行缺失 / 图片字节不可得（Blob `503`、原文件已删、`blob_ref` 为空） | `related_images` **不发事件**（有图才发）；图片端点返回 `404` / `503`；**检索与回答不受影响**（图是增强项，不是前提） | 无感（缩略图静默隐藏） | WARN | fail-open（增强项） |
```

### MD-21 · §9 覆盖率 — 三处更新

目标文件：`docs/module_design.md`

**A · §9.1 表 IB-15 行**
锚点（唯一；原文照抄）:
```text
| IB-15 | 本地 embedding（bge-m3） | **MOD-IB-09** / 10 |
```
新内容（整段替换锚点）:
```text
| IB-15 | 本地 embedding（bge-m3） | **MOD-IB-09, MOD-IB-26** / 10（09 = 客户端端口与冷热双路径；26 = 服务端线协议） |
```

**B · §9.2 表 NFR-10 行**
锚点（唯一；原文照抄）:
```text
| NFR-10 | 可移植性与算力适配 | **MOD-IB-09** / 25 |
```
新内容（整段替换锚点）:
```text
| NFR-10 | 可移植性与算力适配 | **MOD-IB-09** / 25, 26 |
```

**C · §9.3 之后新增 §9.4**
锚点（唯一；原文照抄）:
```text
- 因此 §9.1 / §9.2 矩阵逐行有效，无需改动；本文档仍满足门控「REQ → MOD 全覆盖」标准。
```
新内容（保留锚点行，其后追加小节）:
```text
- 因此 §9.1 / §9.2 矩阵逐行有效，无需改动；本文档仍满足门控「REQ → MOD 全覆盖」标准。

### 9.4 R2 覆盖率再声明（L-03 增量）

**结论：24/24 REQ-FUNC + 14 REQ-NFR 覆盖不变，无新增缺口；R2 的新增只**加固**既有覆盖，不改任何既有主/辅归属。**

- **REQ-FUNC-IB-15**（本地 embedding）：R2 前只有 `MOD-IB-09`（端口 + 客户端）承载，**服务端无模块归属**——这正是 L-03；R2 由 `MOD-IB-26` 补上服务端侧（主覆盖并列：09 = 端口/客户端，26 = 服务端线协议）。
- **M-02（页面图绑定）不新增 REQ**：它落在 REQ-FUNC-IB-10 / IB-11（解析并产出页面图）与 IB-14 / IB-17（检索、供专家使用）的**既有语义**之内，故只**增辅覆盖**（MOD-IB-01 / 13 / 21 / 23 / 24），**不新增需求条目、不改变 24/24 的判定**。
- 若 PM 认为「图片回溯」应升格为**独立 REQ**，须回**需求侧**立项 —— 架构层**不自行新增 REQ**（见残余项 R-5）。
```

### MD-22 · §11 自检声明 — R2 段

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
  - **凭据纪律**：仍只记「凭据走环境变量」（IFC-IB-262/263），无任何真实值。
```
新内容（保留锚点行，其后追加）:
```text
  - **凭据纪律**：仍只记「凭据走环境变量」（IFC-IB-262/263），无任何真实值。
  - **R2 自检（L-03 补交）**：
    - **补交完整**：MOD-IB-26 具备模块归属（§1 / §3）、依赖边与无环论证（§4.1 / §4.2）、类型化契约（IFC-IB-266~274，正文单列文件）、装配与可逆开关（§5）、降级行（§7.4）、覆盖行（§9）。**「有单元文件与客户端、无模块归属」的状态已消除。**
    - **编号只增不改**：`IFC-IB-001~265` 的号/名/签名/字段集一字不动；新增 266~284 与 286，285 预留未分配；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。
    - **DAG 无环**：新增单边仅 `26 → {01,02,04}`，且 26 号无入边（不被 import）→ 权值严格递减性质保持（§4.2 R2 补句）。
    - **契约单一落点**：MOD-IB-26 正文以 `docs/ib_embed_service_contract.md` 为准，§3 为摘要视图，**全文无第二份口径**。
    - **边界合规**：R2 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；**未写入任何凭据或配置值**（只登记键名）；本阶段**止于 GROUP_B**。
```

---

## 2. architecture_design.md（AD-01 ~ AD-05）

### AD-01 · architecture_design.md — 文件头版本与修订号

目标文件：`docs/architecture_design.md`
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

### AD-02 · architecture_design.md — 追加 revision_history 条目

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄）:
```text
  </revision_history>
```
新内容（在锚点**之前**插入一条 rev，再保留锚点）:
```text
    <rev version="1.2.0" revision="R2" date="2026-09-26" invocation_id="INV-GROUP_B-INTELBASE-004" note="R2 补交（L-03：ib-embed 服务端无模块归属与契约）：① 追加 ADR-02-R2 附注——ib-embed 的服务端归属成立（MOD-IB-26，补齐既有 Option B 决策的落点，Decision/Options/Consequences 未改）、冷/热双路径单一落点在客户端、形态可逆值域显式化为 http|inproc|fake；并随附登记「错误码语义映射不变式」（4xx/409=重试无用，5xx=重试可能有用）；② 新增 §2.0.1 R2 影响复核表（ADR-01~13 逐条：ADR-02 受影响（仅补附注）、其余 12 条 R2 不受影响），并为 ADR-04/06/11/13 追加 inline R2 复核句；③ §9 TBD 清单补 [TBD-T16]（ib-embed 并发与线程校准）与 [TBD-T18]（目标机 CPU 指令集 AVX2 基线实测），并声明 [TBD-T17] 为预留未分配；④ §10.3 自检追加 R2 行。不变约束：模块数 25→26（仅追加）、端口 13、IFC-IB 001~265 一字不动（新增 266~284/286）、DAG 无环、覆盖 24/24 REQ-FUNC + 14 NFR。需求侧文档与 FreeArk 仓库未改动。"/>
  </revision_history>
```

### AD-03 · architecture_design.md — 首部版本行与 R2 摘要

目标文件：`docs/architecture_design.md`
锚点（唯一；原文照抄）:
```text
**版本**: 1.1.0（R1 修订）| **状态**: DRAFT（待 PM 门控评审）| **日期**: 2026-09-25
```
新内容（整段替换锚点）:
```text
**版本**: 1.2.0（R2 补交）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26
**R2 修订摘要（L-03：`ib-embed` 服务端无模块归属与完整契约）**: 追加 **ADR-02-R2 附注**（服务端归属成立 = 新增 MOD-IB-26；冷/热单一落点在客户端；形态可逆值域 `http|inproc|fake`），新增 **§2.0.1 R2 影响复核表**（**受影响 1 条：ADR-02（仅补附注）**；**R2 不受影响 12 条**：ADR-01 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 10 / 11 / 12 / 13），并为 ADR-04 / 06 / 11 / 13 追写 inline R2 复核句；§9 补 **[TBD-T16] / [TBD-T18]** 并声明 **[TBD-T17] 预留未分配**。**不变**：§1 / §3~§7 的结论、模块数与端口数、`IFC-IB-001~265`、REQ→MOD 覆盖矩阵、DAG 无环（R2 只追加）。
```

---

（part3 结束；ADR-02-R2 附注与 §2.0.1 表见 `docs/r2_apply_package_part4.md`）
