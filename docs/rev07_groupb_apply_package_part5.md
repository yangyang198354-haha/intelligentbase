<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package_part5</artifact>
  <path>docs/rev07_groupb_apply_package_part5.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_04 模块详细设计）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/module_design.md</targets>
</file_header>

# REV-07 APPLY-READY 修订包 · 第 5 册 — 模块文档指令（头 / §1 总览 / §2 契约）

> **权威分册与条数声明（本册起生效，取代第 1 册 §0.1 与第 2 册的表格）**：本包共 **7 册 / 64 条**指令 —— 架构文档 `R7-A-01 ~ R7-A-20`（**20 条**）、模块文档 `R7-M-01 ~ R7-M-31`（**31 条**：第 5 册 `M-01 ~ M-16`、第 6 册 `M-17 ~ M-31`）、技术栈 `R7-T-01 ~ R7-T-13`（**13 条**，第 7 册）。第 1 册 §0.1 的「58 条」与第 2 册表格的「60 条 / M-01~M-26」均为**中途估值**，以本声明为准（条数只影响执行清单，不影响任何一条指令的锚点与内容）。

## 1. `docs/module_design.md` 指令（R7-M-01 ~ R7-M-16）

### R7-M-01
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
  <version>1.2.0</version>
  <revision>R2</revision>
```
- new_string:
```text
  <version>1.3.0</version>
  <revision>R7</revision>
```
- rationale: REV-07 版本号规则（1.2.0 → 1.3.0（R7））。

### R7-M-02
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.1.0" status="DRAFT_FOR_GATE_REVIEW"/>
```
- new_string:
```text
    <input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.2.0" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.3.0" revision="R7" status="DRAFT_FOR_GATE_REVIEW"/>
```
- rationale: REV-07-7 —— 需求侧引用版本 1.1.0 → 1.2.0；架构文档引用版本同步为修订后的 1.3.0（R7）。

### R7-M-03
- target_file: `docs/module_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `  </revision_history>`
- old_string: `（空：纯插入）`
- new_string:
```text
    <rev no="R7" date="2026-09-27" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-005" basis="GROUP_A REV-06 下游贯通（诉求③「UI 可视化配置」纳入 v1：REQ-FUNC-IB-25 / IB-26 / IB-27）">
      **不新增模块、不新增依赖边**（REV-07-1）：定义文档数据层（装载 / 完备性校验 / 原子写回 / 装配期派生）并入 MOD-IB-02；契约与**第 14 个端口** `DefinitionDocumentStore` 并入 MOD-IB-01；可视化端点与装配期 fail-fast 准入闸门并入 MOD-IB-23；可视化视图（白名单表单 + 编排图只读渲染）并入 MOD-IB-24。新增 IFC 编号 287~297（11 条，全部类型化、frozen dataclass / Protocol、零第三方依赖）；IFC-IB-285 仍预留未分配。既有 MOD-IB-01~26、IFC-IB-001~286、13 个既有端口名、§4.1 依赖边清单、DAG 拓扑与既有 REQ 覆盖归属**一字不动**（纯追加；零新增边的再声明见 §4.2.2）。增补位置：§0 门控证据行与 §1 总览行（计数 24/24 → 27/27）、R7 性质段与 R7 补充纪律段、§2.1 四行数据结构与 R7 字段集说明、§2.2 端口行与 R7 增记、§2.2.2 R7 IFC 段号索引、§3 的 MOD-IB-01/02/16/22/23/24 增补、§4.2.2 R7 无环性再声明、§5 装配表行与 R7 说明、§7.4 两行降级、§8 替身行与离线可测单元、§9.1 三行覆盖与计数同步、§9.2 R7 说明、§9.5 R7 覆盖率再声明、§11 R7 自检。**REV-07-6 施工前置判定 = (a) 可登记前置条件 / 风险，本轮继续**（见 §9.5）。未修改 FreeArk 任何文件；需求侧文档只读；未写入任何凭据或配置值（只登记键名）。
    </rev>
```
- rationale: REV-07-7 —— 新增 R7 修订历史行；历史行（R1 / R2）**不回改**。

### R7-M-04
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**版本**: 1.2.0 (R2) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26`
- new_string: `**版本**: 1.3.0 (R7) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-27`
- rationale: 文档头版本行同步（版本号 + 状态 + 日期）。

### R7-M-05
- target_file: `docs/module_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `二者冲突时以契约文件为准。`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 性质**: 本修订为**追加式增量**（GROUP_A REV-06 裁决：诉求③「UI 可视化配置」纳入 v1，新增 REQ-FUNC-IB-25 / IB-26 / IB-27），**只追加、不改写**：**不新增模块、不新增依赖边**。定义文档的**数据层**（装载 `IFC-IB-288` / 完备性校验 `IFC-IB-290` / 原子写回 `IFC-IB-289` / 装配期派生 `IFC-IB-291` / 白名单 `IFC-IB-292` / 新增键名 `IFC-IB-297`）并入 **MOD-IB-02**；契约（端口 + 数据结构）并入 **MOD-IB-01**；可视化端点与**装配期准入闸门**（`IFC-IB-293~295`）并入 **MOD-IB-23**；可视化视图约束（`IFC-IB-296`）并入 **MOD-IB-24**。新增 `IFC-IB-287 ~ 297`（**IFC-IB-285 仍预留未分配**）。既有 MOD-IB-01~26、`IFC-IB-001~286`、13 个既有端口名、§4.1 依赖边清单与 DAG 拓扑**一字不动**（零新增边的再声明见 §4.2.2）。**REV-07-6 施工前置判定 = (a) 可登记的前置条件 / 风险，本轮继续**（见 §9.5；另见 `architecture_design.md` [ARCH-ASSUMPTION-A7]）。
```

- rationale: REV-07-1 / -5 —— 与既有 R2 性质 / R1 性质段同构的「本轮性质」声明；置于版本行之后、R2 性质段之前，保持「最新修订在前」的既有排布。

### R7-M-06
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `（§9，24/24 REQ-FUNC 全覆盖）`
- new_string: `（§9，**27/27 REQ-FUNC 全覆盖**；R7 同步计数，v1.2.0 需求总数）`
- rationale: REV-07-3 —— 门控证据行计数同步（需求计数语境；24 → 27）。

### R7-M-07
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `26 个模块（R2 新增 MOD-IB-26）。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4；R2 新增单边的权值校验见 §4.2）。`
- new_string: `26 个模块（R2 新增 MOD-IB-26；**R7 未新增模块**——REV-07-1：可视化配置的落点并入既有模块，理由见下方 R7 补充纪律）。**编号即拓扑序**：每个模块的依赖编号均小于自身 → DAG 无环（证明见 §4；R2 新增单边的权值校验见 §4.2；**R7 零新增依赖边的再声明见 §4.2.2**）。`
- rationale: REV-07-1 / -6 —— 总览首句须显式声明「未新增模块」并指向论证落点，避免门控四处寻找「MOD-IB-27」。

### R7-M-08
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `会**同时**破坏 DAG 纪律与「形态可逆」（进程内形态不得依赖服务端）。`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 补充纪律（编号即拓扑序的边界情形）**：REV-07 曾评估「新增 `MOD-IB-27` 承载定义文档数据层」，**予以否决**：定义文档数据层是 **L0 纯数据工件**，**必然被组合根 `MOD-IB-23` 依赖**；而新模块只能取 **≥27** 的编号，于是产生 `23 → 27` 的边，违反 `w(A) > w(B)`，**构造性无环证明失效**（§4.2）。替代方案（独立服务进程 + 线协议，形态对齐 MOD-IB-26）则**净增第 5 个 systemd 单元**与新故障域，与 C-IB-08（最小组成面）与 ADR-03（四单元结论）冲突。故按 REV-07-1 将落点**并入既有模块**。**该边界情形固化为纪律**：当新工件被**低编号模块（尤其组合根）依赖**时，**不得新开编号更高的模块**——只能并入既有模块，或先把契约下沉（与 §4.2「分层被破坏须先重构分层」同源）。
```
- rationale: REV-07-1 / -6 —— 把「为什么没有 MOD-IB-27」从隐含推理变为**书面纪律**，同时供 §4.2.2 与 ADR-15-D 交叉引用（三处同源，杜绝口径分叉）。

### R7-M-09
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `| MOD-IB-02 | 配置 | L0 | 装载并校验 全局配置 / 项目级配置；注入凭据（仅环境变量） | 01 |`
- new_string: `| MOD-IB-02 | 配置 | L0 | 装载并校验 全局配置 / 项目级配置；注入凭据（仅环境变量）；**R7**：定义文档的装载 / 完备性校验 / 原子写回 / 装配期派生（IFC-IB-288~292、297） | 01 |`
- rationale: REV-07-1 —— 总览表职责列同步（依赖列**不变**，零新增边）。

### R7-M-10
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `| MOD-IB-16 | 专家注册表 | L4 | 专家规格的**唯一真源**（frozen dataclass，framework-free 纯数据） | 01 |`
- new_string: `| MOD-IB-16 | 专家注册表 | L4 | **装配期派生注册表**（由定义文档在装配期构造并注入；R7 前表述为「唯一真源」——真源已上移至定义文档，见 ADR-15；仍为 frozen dataclass，framework-free 纯数据） | 01 |`
- rationale: REV-07-2 —— 「唯一真源」措辞与 ADR-15 的「定义文档为持久化态唯一真源」对齐，消除两处口径冲突（这是 ADR-15 负向后果中已声明的必改项）。

### R7-M-11
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
| MOD-IB-22 | 编排图 | L4 | StateGraph：route → fan-out → expert/general → gate → aggregate | 01,02,03,04,16,17,18,19,20,21 |
| MOD-IB-23 | HTTP API 与组合根 | L5 | 唯一装配点；REST + SSE 端点；鉴权注入；健康检查 | 01,02,03,04 + 全部装配目标 |
| MOD-IB-24 | Web 前端 | L5 | 上传/列表/删除/重试/重建页 + 问答页 + 类型化 API 客户端 | 23（仅 HTTP/SSE 契约） |
```
- new_string:
```text
| MOD-IB-22 | 编排图 | L4 | StateGraph：route → fan-out → expert/general → gate → aggregate；**R7**：图编译输入 = 经准入闸门校验通过的定义文档，**拓扑不可编辑**（运行期不得由图外输入改变节点/边） | 01,02,03,04,16,17,18,19,20,21 |
| MOD-IB-23 | HTTP API 与组合根 | L5 | 唯一装配点；REST + SSE 端点；鉴权注入；健康检查；**R7**：装配期 **fail-fast 准入闸门**（拒绝装配而非带病运行）+ 定义文档的 GET / PUT 端点 | 01,02,03,04 + 全部装配目标 |
| MOD-IB-24 | Web 前端 | L5 | 上传/列表/删除/重试/重建页 + 问答页 + 类型化 API 客户端；**R7**：可视化配置页（编排图只读渲染 + 白名单表单；**视图侧零持久化**） | 23（仅 HTTP/SSE 契约） |
```
- rationale: REV-07-1 —— 三行相邻（22 / 23 / 24）合并为一条块替换，减少落盘次数；**依赖列逐字保留**（零新增边）。

### R7-M-12
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `` `RelatedImagesPayload`: `images: tuple[RelatedImageItem, ...]` ``
- old_string: `（空：纯插入）`
- new_string:
```text
| `DefinitionDocument`（R7 新增，定义于 MOD-IB-01） | `schema_version: int`；`project_id: str`；`content_hash: str`；`experts: tuple[ExpertSpecInput, ...]`；`route: RouteSpecInput`；`orchestration: OrchestrationSpecInput`；`tool_grants: tuple[ToolGrantSpec, ...]`；`updated_at: str` |
| `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec`（R7 新增，定义于 MOD-IB-01） | `ExpertSpecInput`: `name: str`；`cn_label: str`；`keywords: tuple[str, ...]`；`exemplars: tuple[str, ...]`；`is_data_expert: bool`；`fallback_prompt: str`；`is_delegating: bool`；`is_default: bool`。`RouteSpecInput`: `tau: float`；`margin: float`；`max_expert_steps: int`；`default_expert: str`。`ToolGrantSpec`: `expert_name: str`；`tool_names: tuple[str, ...]` |
| `OrchestrationSpecInput` / `ConditionalEdgeSpec`（R7 新增，定义于 MOD-IB-01） | `OrchestrationSpecInput`: `nodes: tuple[str, ...]`；`conditional_edges: tuple[ConditionalEdgeSpec, ...]`。`ConditionalEdgeSpec`: `from_node: str`；`branch_map: tuple[tuple[str, str], ...]`（元素为 `(branch_key: str, target_node: str)` 的有序对；**缺失或为空即非法** —— 界面无法判定可达性，由 IFC-IB-290 拒绝） |
| `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult`（R7 新增，定义于 MOD-IB-01） | `DerivedView`: `experts: tuple[ExpertSpecInput, ...]`；`capability_digest: str`；`graph_config: OrchestrationSpecInput`。`ValidationErrorItem`: `path: str`；`code: str`；`message: str`（**不回显任何凭据值**）。`ValidationReport`: `ok: bool`；`errors: tuple[ValidationErrorItem, ...]`（**无 `force` / `ignore` / `warn_only` 字段**）。`SaveResult`: `ok: bool`；`content_hash: str`；`conflict: bool`；`errors: tuple[ValidationErrorItem, ...]` |
```
- rationale: REV-07-5 —— 全部新结构**类型化**（`name: type` + 可空性）、frozen dataclass、零第三方依赖；`ValidationReport` 的字段集是刻意设计（类型层事实）。

### R7-M-13
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `（编号只增不改）。`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 说明（字段集不变式续）**：以上四行为**追加**，R1 / R2 既有结构（`ParsedChunk` / `RetrievedChunk` 与 R2 三行）的字段集**均不变**。`ValidationReport` 的字段集是**刻意**的：除 `ok` / `errors` 外**不存在** `force` / `ignore` / `warn_only`，使 REQ-FUNC-IB-27「**不提供**强制继续 / 忽略错误开关」成为**类型层事实**而非纪律约定（ADR-16）。`DerivedView` 为**只读派生结果**：不落盘、不可反写文档；`ValidationErrorItem` 只出 `path` / `code` / `message`，**不回显任何凭据值**（AC-IB-18-04）。全部结构为 **frozen dataclass / 纯 stdlib**（REV-07-5）。
```
- rationale: REV-07-5 / -2 —— 把「无强制继续开关」「派生只读」「不回显凭据」三项写成字段级不变式，供门控以结构证据核验。

### R7-M-14
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| `SessionStore` | 3 | IFC-IB-221~223 | §3 MOD-IB-21 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| `DefinitionDocumentStore`（**R7 新增**） | 5 | IFC-IB-287（端口）+ IFC-IB-288~292（方法） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-02（装载·校验·写回·派生·白名单） |
```
- rationale: REV-07-5 —— 端口清单新增一行，且置于表末（**纯追加**，不打乱既有行序）。

### R7-M-15
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `而非各自拼接字符串。`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 增记（第 14 个端口）**：`DefinitionDocumentStore`（IFC-IB-287）为**第 14 个端口**（13 → 14，**纯追加**）。它与 `ConfigurationSource` 的区别是**工件不同**：后者装载进程级配置（凭据只登记键名），前者装载**项目级定义文档**（专家 / 路由 / 编排 / 工具授权）并保证 round-trip 一致性（乐观并发 + 原子写）。所有需要「按项目取定义文档 / 派生结果」的上层模块（MOD-IB-16 / 17 / 19 / 22）**不得**各自读文件或各自解析，一律由组合根在**装配期**经该端口取得派生物后构造注入（同 `CollectionResolver` 的「唯一入口」精神；ADR-15）。
```

- rationale: REV-07-5 —— 端口清单的「唯一入口」纪律须与本文件既有的 `CollectionResolver` 段落同构表述，避免出现第二种取定义文档的方式。

### R7-M-16
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `（见 part7 残余项 R-9）。`
- old_string: `（空：纯插入）`
- new_string:
```text
### 2.2.2 R7 新增 IFC 段号索引（追加式编号；IFC-IB-001~286 一字不动）

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-287 | MOD-IB-01 | 端口 `DefinitionDocumentStore`（Protocol，5 方法）+ `DefinitionDocument` / `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec` / `OrchestrationSpecInput` / `ConditionalEdgeSpec` / `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult` 的字段级定义 | §2.1、§3 MOD-IB-01（本文件） |
| IFC-IB-288 | MOD-IB-02 | `load(project_id: str) -> DefinitionDocument \| ConfigError`（文档缺失或不可解析均为可读错误，**不静默回退为空文档**） | §3 MOD-IB-02 |
| IFC-IB-289 | MOD-IB-02 | `save(project_id: str, doc: DefinitionDocument, *, expected_content_hash: str \| None) -> SaveResult`（**先写临时文件、再原子替换**；`expected_content_hash` 不匹配即返回 `conflict=True` 并**拒绝覆盖**） | §3 MOD-IB-02 |
| IFC-IB-290 | MOD-IB-02 | `validate(doc: DefinitionDocument) -> ValidationReport`（**纯函数**，framework-free；≥7 类校验项；**不含强制继续开关**） | §3 MOD-IB-02 |
| IFC-IB-291 | MOD-IB-02 | `derive(doc: DefinitionDocument) -> DerivedView`（**纯函数**；注册表 / 阈值 / 图配置的装配期派生；**不落盘、不可反写**） | §3 MOD-IB-02 |
| IFC-IB-292 | MOD-IB-02 | `editable_field_whitelist() -> frozenset[str]`（可视化可编辑字段白名单；须与 IFC-IB-290 的校验项**成对维护**） | §3 MOD-IB-02 |
| IFC-IB-293 | MOD-IB-23 | 装配期**准入闸门**：`admit(doc: DefinitionDocument) -> DerivedView`（内部调用 IFC-IB-290；不通过即**拒绝装配**，抛出聚合全部 `ValidationErrorItem` 的 `ConfigError`） | §3 MOD-IB-23 |
| IFC-IB-294 | MOD-IB-23 | `GET /api/config/definition` → `200 DefinitionDocument`（+ 派生视图摘要）\| `403`（归属断言失败）\| `503`（**fail-closed**：读不到文档即明确报错，**不返回空文档**） | §3 MOD-IB-23 |
| IFC-IB-295 | MOD-IB-23 | `PUT /api/config/definition` → `200 SaveResult` \| `400`（校验不通过：逐条 `path` / `code` / `message`）\| `403` \| `409`（乐观并发冲突，**含可读冲突回执**）\| `503`（**fail-closed**） | §3 MOD-IB-23 |
| IFC-IB-296 | MOD-IB-24 | 可视化配置页的**渲染与编辑约束**（编排图只读渲染 + 白名单表单 + 未提交草稿显式标注 + 凭据不回显） | §3 MOD-IB-24 |
| IFC-IB-297 | MOD-IB-02 | 新增环境变量**键名**（**仅登记键名，不含任何值**）：`IB_DEFINITION_DOC_PATH`、`IB_VISUAL_CONFIG_ENABLED`（见 `tech_stack.md` §1.2） | §3 MOD-IB-02 |

**R7 编号规范（强制，延续 R2）**：新增号只许**追加**；`IFC-IB-001 ~ 286` 的号、名、签名、字段集**一字不动**；**`IFC-IB-285` 仍预留未分配**（不得被本轮占用或改义）；既有重号（`IFC-IB-131`）**登记不修**（残余项 R-9）。以上 11 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**。
```

- rationale: REV-07-5 / -1 —— 与 §2.2.1（R2 IFC 段号索引）同构的 R7 索引，使「新增了哪些号、归属谁、落哪」有单一可核验入口；末尾重申 `IFC-IB-285` 预留与「不占不改」纪律。
