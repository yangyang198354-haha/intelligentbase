<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part1</artifact>
  <path>docs/r2_apply_package_part1.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P1</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03：ib-embed 服务端无模块归属与契约）</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>
    <target path=docs/module_design.md from=1.1.0-R1 to=1.2.0-R2/>
    <target path=docs/architecture_design.md from=1.1.0-R1 to=1.2.0-R2/>
    <target path=docs/tech_stack.md from=1.1.0-R1 to=1.2.0-R2/>
  </targets>
  <authoritative_contract path=docs/ib_embed_service_contract.md note=MOD-IB-26 正文唯一落点（IFC-IB-266~274）；本包只做「归属补齐 + 摘要视图 + 引用」/>
  <scope_boundary>本包只含编辑指令（锚点 + 新内容）。不含实现代码、不含伪代码、不含部署脚本、不含任何凭据值或配置键值。</scope_boundary>
  <security_note>全文只登记配置键名，不含任何真实值；未向 FreeArk 仓库（只读参考）写入任何文件。</security_note>
</file_header>

# R2 APPLY-READY 修订包（part1/7）— intelligentbase（L-03 补交）

**性质**：把上一次调用（`INV-GROUP_B-INTELBASE-003`）中只存在于**会话文本**的 R2 设计，落盘为**可机械执行**的编辑指令。
**施加方式**：本包自身是**新增小文件**；三份目标文档（`module_design.md` >50KB、`architecture_design.md`、`tech_stack.md`）**不做整文件重写**，一律由 PM 以「锚点 + 新内容」逐条 Edit。**锚点均为原文照抄**（含全角括号与原始空格），可直接用于 Edit 定位；替换范围为**锚点整段**。

**分册索引（全 7 册）**：

| 册 | 内容 |
|----|------|
| part1（本册） | 总则（不变式 6 条）+ `module_design.md` MD-01 ~ MD-08 |
| part2 | `module_design.md` MD-09 ~ MD-16 |
| part3 | `module_design.md` MD-17 ~ MD-22 + `architecture_design.md` AD-01 ~ AD-03 |
| part4 | `architecture_design.md` AD-04 ~ AD-05 |
| part5 | `architecture_design.md` AD-06 ~ AD-11 + `tech_stack.md` TS-01 ~ TS-03 |
| part6 | `tech_stack.md` TS-04 ~ TS-07 |
| part7 | `tech_stack.md` TS-08 ~ TS-10 + 条目计数 + 施加顺序与校验 + 残余项 R-1 ~ R-9 |

**本次 R2 做的两件事**：
1. **补齐 L-03**：`ib-embed` 此前「只有 systemd 单元与客户端，缺服务端模块归属与完整契约」→ 新增 **MOD-IB-26**，契约单列 `docs/ib_embed_service_contract.md`（已落盘）。
2. **M-02 页面图 ↔ 文块绑定**：把「问图不出图」的结构性根因（页面文字块与图片块分属两次解析产出、彼此无引用）消灭在**入库期**，并给出读路径取图端点与前端渲染约束。

---

## 0. 不变式与编号规范（施加前必读）

| # | 不变式 | 内容 |
|---|--------|------|
| 1 | **编号只增不改** | `IFC-IB-001 ~ 265` 的号、名、签名、字段集**一字不动**（含既有重号现状，见 part7 残余项 R-9）；`MOD-IB-01~25`、13 个端口名、`ADR-01~13`、`FM-1~8`、`TBD-T1~T15` 一律不变，**只做追加** |
| 2 | **错误码语义映射不变式** | `4xx/409 = 重试无用`（配置或请求问题）；`5xx = 重试可能有用`（暂时故障）。这是客户端「4xx 不重试」（`if exc.code < 500: break`）能够成立的前提，**不得把暂时性故障放进 4xx** |
| 3 | **契约单一落点** | MOD-IB-26 的正文只在 `docs/ib_embed_service_contract.md`；`module_design.md` §3 是**摘要视图**，冲突时以契约文件为准 |
| 4 | **形态可逆** | `IB_EMBED_BACKEND ∈ {http, inproc, fake}`：**键名与默认值 `http` 不变**，仅扩展值域；`inproc` 实现位于 MOD-IB-09 之内，**不 import MOD-IB-26** |
| 5 | **DAG 纪律** | 新增模块须取大于其全部依赖的编号；新增单边仅 `MOD-IB-26 → {01,02,04}`，且 26 号**无入边**（不被任何模块 import） |
| 6 | **凭据纪律** | 只登记**键名**；`ib-embed` 不需要任何令牌；文档与 URL 一律不得出现凭据型查询串（禁 `?token=`，对全部端点生效） |

---

## 1. module_design.md（条目 MD-01 ~ MD-08）

### MD-01 · module_design.md — 文件头版本与修订号

目标文件：`docs/module_design.md`
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

### MD-02 · module_design.md — 追加 revision_history 条目

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
  </revision_history>
```
新内容（在锚点**之前**插入一条 rev，再保留锚点）:
```text
  <rev no="R2" date="2026-09-26" by="sub_agent_system_architect" invocation_id="INV-GROUP_B-INTELBASE-004" basis="PM 补交要求（L-03：ib-embed 服务端无模块归属与完整契约）">
    新增 MOD-IB-26「ib-embed 服务端」（26 大于其全部依赖 {01,02,04}，编号即拓扑序仍成立，且本模块不被任何模块 import）。新增 IFC 编号：266~274（MOD-IB-26 线协议，正文以 docs/ib_embed_service_contract.md 为准）、275（MOD-IB-09 的 InProcessBgeM3Embedder 第三适配器）、276~284（M-02 页面图绑定：MOD-IB-01 数据结构 / MOD-IB-13 五条 / MOD-IB-21 related_images 载荷 / MOD-IB-23 图片端点 / MOD-IB-24 渲染约束）、286（MOD-IB-25 第二份 EnvironmentFile 模板）；IFC-IB-285 预留未分配。既有 MOD-IB-01~25、IFC-IB-001~265、端口名、DAG 拓扑与 REQ 覆盖率矩阵一字不动（纯追加）。增补位置：§1 总览行与计数、§2.1 三行数据结构、§2.2.1 R2 IFC 段号索引、§3 的 MOD-IB-09/13/21/23/24/25 增补与 MOD-IB-26 新小节（摘要视图）、§4.1 一条新依赖边、§4.2 R2 无环补句、§4.3 分层一行、§5 装配表 IB_EMBED_BACKEND 值域扩展、§7.4 两行降级、§9.1/§9.2 覆盖更新与 §9.4 再声明、§11 R2 自检。
  </rev>
  </revision_history>
```

### MD-03 · module_design.md — inputs 登记契约文件

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
  </inputs>
```
新内容（在锚点**之前**插入一行 input）:
```text
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW" note="MOD-IB-26 契约唯一落点；本文件 §3 MOD-IB-26 为摘要视图，冲突时以其为准"/>
  </inputs>
```

### MD-04 · module_design.md — 首部版本行与 R2 性质

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
**版本**: 1.1.0 (R1) | **状态**: DRAFT（待 PM 门控评审）| **日期**: 2026-09-25
```
新内容（整段替换锚点）:
```text
**版本**: 1.2.0 (R2) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26
**R2 性质**: 本修订为**补交式增量**（L-03：`ib-embed` 此前只有 systemd 单元与客户端、缺服务端模块归属与完整契约），**只追加、不改写**：新增 MOD-IB-26 与 IFC-IB-266~284 / 286（IFC-IB-285 预留）。既有 MOD-IB-01~25、IFC-IB-001~265、13 个端口名与 DAG 拓扑**一字不动**。MOD-IB-26 的契约**唯一落点**为 `docs/ib_embed_service_contract.md`，本文件 §3 为其**摘要视图**，二者冲突时以契约文件为准。
```

### MD-05 · module_design.md — §1 模块计数与纪律补句

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
25 个模块。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4）。
```
新内容（整段替换锚点）:
```text
26 个模块（R2 新增 MOD-IB-26）。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4；R2 新增单边的权值校验见 §4.2）。

**R2 补充纪律**：MOD-IB-26 是**唯一**「不被任何模块 import」的服务端模块（上层只经 `Embedder` 端口与线协议访问，与 MOD-IB-10 对 Qdrant 服务的形态同构），因此它**不引入任何入边**，也不可能出现在任何依赖环上。若将来有人 `import` 本模块，会**同时**破坏 DAG 纪律与「形态可逆」（进程内形态不得依赖服务端）。
```

### MD-06 · module_design.md — §1 模块总览表新增 MOD-IB-26 行

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
| MOD-IB-25 | 部署运维 | L5 | 四个 systemd 单元、EnvironmentFile 模板、启动校验、检查清单 | 01,02,04 |
```
新内容（保留锚点行，其后追加一行）:
```text
| MOD-IB-25 | 部署运维 | L5 | 四个 systemd 单元、EnvironmentFile 模板、启动校验、检查清单 | 01,02,04 |
| MOD-IB-26 | ib-embed 服务端 | L2（服务端进程；不被任何模块 import） | bge-m3 常驻推理服务的**线协议实现与模块归属**；单模型、CPU-only、有界并发 + 有界队列 | 01,02,04 |
```

### MD-07 · module_design.md — §2.1 新增页面图关联数据结构

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
| `RequestContext` | `request_id: str`；`session_key: str`；`scope_token: str`；`authz: AuthzContext` |
```
新内容（保留锚点行，其后追加三行）:
```text
| `RequestContext` | `request_id: str`；`session_key: str`；`scope_token: str`；`authz: AuthzContext` |
| `PageImageRef`（R2 新增，定义于 MOD-IB-01） | `image_id: str`；`page_or_section: str`；`source_kind: Literal["embedded_image","page_scan"]`；`locator: str`；`blob_ref: str \| None`；`caption: str \| None` |
| `PageImageBinding`（R2 新增，定义于 MOD-IB-01） | `project_id: str`；`kb_id: str`；`doc_id: str`；`page_or_section: str`；`images: tuple[PageImageRef, ...]` |
| `RelatedImageItem` / `RelatedImagesPayload`（R2 新增，定义于 MOD-IB-01） | `RelatedImageItem`: `image_id: str`；`doc_id: str`；`doc_name: str`；`page_or_section: str`；`url_path: str`。`RelatedImagesPayload`: `images: tuple[RelatedImageItem, ...]` |
```

**注（须随该处一并写入，作为 §2.1 表下的说明）**:
```text
**R2 说明（字段集不变式）**：以上三行为**追加**，既有两个结构（`ParsedChunk` / `RetrievedChunk`）的字段集**不变**——页面图的图文关联经**独立结构 + 独立关联表**承载，不改 `IFC-IB-009` / `IFC-IB-007` 的既有字段（编号只增不改）。
```

### MD-08 · module_design.md — §2.2.1 新增 R2 IFC 段号索引

目标文件：`docs/module_design.md`
锚点（唯一；原文照抄）:
```text
`CollectionResolver` 归入 MOD-IB-09 所在层（L2，无外部依赖，仅依赖 MOD-IB-01/02）：它是**唯一**把 `Scope` 映射为 collection 名的地方（ADR-04 可升级性设计），因此必须由所有需要 collection 名的上层模块共用，而非各自拼接字符串。
```
新内容（保留锚点段，其后追加小节）:
```text
`CollectionResolver` 归入 MOD-IB-09 所在层（L2，无外部依赖，仅依赖 MOD-IB-01/02）：它是**唯一**把 `Scope` 映射为 collection 名的地方（ADR-04 可升级性设计），因此必须由所有需要 collection 名的上层模块共用，而非各自拼接字符串。

### 2.2.1 R2 新增 IFC 段号索引（追加式编号；IFC-IB-001~265 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-266 ~ 274 | MOD-IB-26 | `/embed`、`/healthz`、`/warmup`、`/descriptor` 线协议；维度三方一致性；批上限与截断；错误码表与 4xx/5xx 分类不变式；冷/热单一落点；形态可逆 | `docs/ib_embed_service_contract.md` §3~§9（唯一落点） |
| IFC-IB-275 | MOD-IB-09 | `InProcessBgeM3Embedder`（第三适配器）+ 客户端 ↔ 线协议对接表 | §3 MOD-IB-09（本文件） |
| IFC-IB-276 | MOD-IB-01 | `PageImageRef` / `PageImageBinding` / `RelatedImagesPayload` 字段级定义 | §2.1（本文件） |
| IFC-IB-277 ~ 281 | MOD-IB-13 | M-02 五条：`bind_page_images` / `persist_page_images` / 关联模型字段 / `process_pending` R2 步骤 / 删除零改动不变式 | §3 MOD-IB-13（本文件） |
| IFC-IB-282 | MOD-IB-21 | `related_images` 流事件的载荷类型化 | §3 MOD-IB-21（本文件） |
| IFC-IB-283 | MOD-IB-23 | 图片字节端点（鉴权 + scope 断言 + fail 语义） | §3 MOD-IB-23（本文件） |
| IFC-IB-284 | MOD-IB-24 | 前端 `related_images` 渲染约束 | §3 MOD-IB-24（本文件） |
| IFC-IB-285 | —（预留） | **预留未分配**：R2 显式占位，供 GROUP_C 追加时按序取用，不得回收再用或改义 | — |
| IFC-IB-286 | MOD-IB-25 | `ib-embed` 的第二份 EnvironmentFile 模板（只登记键名；见 `tech_stack.md` §1.2） | §3 MOD-IB-25（本文件） |

**R2 编号规范（强制）**：新增号只许**追加**；`IFC-IB-001 ~ 265` 的号、名、签名、字段集**一字不动**。既有重号现状（`IFC-IB-131` 同时出现在 MOD-IB-11 与 MOD-IB-12 的清单中）**登记但不修正**——任何重排都会打断下游引用（见 part7 残余项 R-9）。
```

---

（part1 结束；续见 `docs/r2_apply_package_part2.md`）
