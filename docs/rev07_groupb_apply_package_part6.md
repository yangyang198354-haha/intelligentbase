<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package_part6</artifact>
  <path>docs/rev07_groupb_apply_package_part6.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_04 模块详细设计）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/module_design.md</targets>
</file_header>

# REV-07 APPLY-READY 修订包 · 第 6 册 — 模块文档指令（§3 模块详情 / §4.2.2 / §5 / §7.4 / §8 / §9 / §11）

> **权威条数声明（取代第 5 册的「31 条」表述）**：模块文档共 **`R7-M-01 ~ R7-M-42`（42 条）**：第 5 册 `R7-M-01 ~ R7-M-16`（16 条：头 / §1 总览 / §2 契约），第 6 册 `R7-M-17 ~ R7-M-42`（26 条：§3 模块详情 / §4.2.2 / §5 / §7.4 / §8 / §9 / §11）。
> **全包最终条数**：`R7-A-*` = 20 + `R7-M-*` = 42 + `R7-T-*` = 13 → **75 条**。第 1 册 §0.1 的「58 条」、第 2 册表格的「60 条」、第 5 册的「31 条」均为**中途估值**，以本声明为准。

## 1. §3 模块详情增补（MOD-IB-01 / 02 / 16 / 22 / 23 / 24）

### R7-M-17
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）`
- new_string: `- **覆盖需求**: REQ-NFR-IB-01、IB-11、IB-14（可替换性与可测性的结构基础）；**REQ-FUNC-IB-25 / IB-26 / IB-27（R7，辅：只承载新增契约与第 14 个端口，见 IFC-IB-287）**`
- rationale: REV-07-1 —— MOD-IB-01 作为 L0 契约模块，须在覆盖需求列登记其对三条新需求的**辅覆盖**（主覆盖见 §9.1）。

### R7-M-18
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `  - IFC-IB-012: 异常类型层次 `IbError` → `ConfigError` / `ScopeViolationError` / `DependencyUnavailableError` / `ValidationError``
- old_string: `（空：纯插入）`
- new_string:
```text
  - **IFC-IB-287（R7 新增）**: 端口 `DefinitionDocumentStore`（`Protocol`，5 方法：`load` / `save` / `validate` / `derive` / `editable_field_whitelist`）+ 数据结构 `DefinitionDocument` / `ExpertSpecInput` / `RouteSpecInput` / `ToolGrantSpec` / `OrchestrationSpecInput` / `ConditionalEdgeSpec` / `DerivedView` / `ValidationErrorItem` / `ValidationReport` / `SaveResult`（字段级定义见 §2.1 末四行）。**类型化**（`name: type` + 可空性）；**frozen dataclass / Protocol，纯 stdlib、零第三方依赖**；**无实现体**。
```
- rationale: REV-07-5 —— 第 14 个端口的契约落点必须在 MOD-IB-01 的接口清单中出现（否则「定义于 MOD-IB-01」的说法无落点）。

### R7-M-19
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
- **职责**: 装载全局配置与**项目级**配置；凭据仅从环境变量读取；启动期校验必填项并给出可读错误。
- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）；REQ-NFR-IB-02、IB-07
```
- new_string:
```text
- **职责**: 装载全局配置与**项目级**配置；凭据仅从环境变量读取；启动期校验必填项并给出可读错误；**R7 追加**：装载**定义文档**（项目级）、完备性校验、原子写回与**装配期派生**（framework-free 纯数据层，见 IFC-IB-288~292、IFC-IB-297）。
- **覆盖需求**: REQ-FUNC-IB-01、IB-02、IB-05（上限可配）、IB-22（配置模板）、IB-23（项目级配置）、**IB-25 / IB-26 / IB-27（R7 新增：定义文档的装载 / 白名单 / 完备性校验与派生）**；REQ-NFR-IB-02、IB-07
```
- rationale: REV-07-1 —— 定义文档数据层并入 MOD-IB-02 须在职责与覆盖需求两处同步登记（依赖列仍为 `MOD-IB-01`，**零新增边**）。

### R7-M-20
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `  - IFC-IB-024: `GlobalConfig`（含 `EmbeddingConfig` / `VectorStoreConfig` / `RetrievalConfig` / `ChunkingConfig` / `LlmConfig` / `AuthzConfig` / `LoggingConfig` / `BlobConfig` / `WorkerConfig`）`
- old_string: `（空：纯插入）`
- new_string:
```text
  - **IFC-IB-288（R7 新增）**: `load(project_id: str) -> DefinitionDocument | ConfigError`（文档缺失 / 不可解析均为可读错误；**不静默回退为空文档**）
  - **IFC-IB-289（R7 新增）**: `save(project_id: str, doc: DefinitionDocument, *, expected_content_hash: str | None) -> SaveResult`（**先写临时文件、再原子替换**；`expected_content_hash` 不匹配 → `conflict=True`，**拒绝覆盖**）
  - **IFC-IB-290（R7 新增）**: `validate(doc: DefinitionDocument) -> ValidationReport`（**纯函数**，framework-free；**≥7 类**校验项；`ValidationReport` **不含** `force` / `ignore` / `warn_only`）
  - **IFC-IB-291（R7 新增）**: `derive(doc: DefinitionDocument) -> DerivedView`（**纯函数**；注册表 / 路由阈值 / 图配置的装配期派生；**不落盘、不可反写文档**）
  - **IFC-IB-292（R7 新增）**: `editable_field_whitelist() -> frozenset[str]`（可视化可编辑字段白名单；须与 IFC-IB-290 的校验项**成对维护**）
  - **IFC-IB-297（R7 新增）**: 新增配置**键名**（**仅登记键名，不含值**）：`IB_DEFINITION_DOC_PATH`（定义文档路径）、`IB_VISUAL_CONFIG_ENABLED`（可视化配置页开关）
```
- rationale: REV-07-5 / -4 —— 6 条新契约全部类型化、零依赖；键名登记**不得**附带任何值或默认口令（凭据纪律）。

### R7-M-21
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
- **职责**: 专家规格的**唯一真源**（frozen dataclass + 纯 stdlib）；其余模块的专家相关数据一律由此派生。
- **覆盖需求**: REQ-FUNC-IB-02（专家可配置）；REQ-NFR-IB-01（可复用）
```
- new_string:
```text
- **职责**: 专家规格的**装配期派生注册表**（frozen dataclass + 纯 stdlib）；**R7 措辞修正**：真源已上移至**定义文档**（ADR-15），本模块持有的是**由定义文档在装配期派生并注入**的只读注册表（同 MOD-IB-17 的「纯函数派生」模式）；其余模块的专家相关数据一律由此派生。
- **覆盖需求**: REQ-FUNC-IB-02（专家可配置）、**IB-25 / IB-26 / IB-27（R7：定义文档为该注册表的构造输入与唯一真源，见 ADR-15）**；REQ-NFR-IB-01（可复用）
```

- rationale: REV-07-2 —— ADR-15 的负向后果明令「MOD-IB-16 的『唯一真源』措辞须降级为装配期派生注册表」，此为落地。

### R7-M-22
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `- **覆盖需求**: REQ-FUNC-IB-02（专家可配置）、**IB-25 / IB-26 / IB-27（R7：定义文档为该注册表的构造输入与唯一真源，见 ADR-15）**；REQ-NFR-IB-01（可复用）`
- old_string: `（空：纯插入）`
- new_string:
```text
- **R7 依赖不变声明**: 本模块的**依赖模块仍为 MOD-IB-01**（**零新增边**），对外契约 `IFC-IB-171~179` 的号 / 名 / 签名**一字不动**；R7 只改变**数据来源**（定义文档 → 装配期派生 → 构造注入），不改变模块边界与接口。派生的具体构造由 MOD-IB-02 的 `derive`（IFC-IB-291）完成、由组合根 MOD-IB-23 在装配期注入（见 §5 R7 说明）。
```
- rationale: REV-07-1 —— 依赖与契约不变的显式声明，防止实现者把「数据来源变更」误读为「新增依赖边」。

### R7-M-23
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `- **覆盖需求**: REQ-FUNC-IB-18、IB-19、IB-20、IB-21；AC-IB-09-01~07、AC-IB-11-06`
- old_string: `（空：纯插入）`
- new_string:
```text
- **R7 图编译约束（新增）**: 图的编译输入 = **经准入闸门校验通过的定义文档**派生的 `OrchestrationSpecInput`（IFC-IB-291 → IFC-IB-293）；图**编译一次、进程常驻**，**运行期不得由任何图外输入改变拓扑** —— 节点 / 边集合与条件边**存在性**不是可编辑对象（REQ-FUNC-IB-26 ②）。拓扑变更的唯一路径 = 改定义文档 → 装配期校验 → 重新编译（AC-IB-18-01）。条件边**必须**带 `branch_map`，否则由 IFC-IB-290 拒绝（界面无法判定可达性）。`IFC-IB-231` 的签名**不变**（新增的图配置仍经 `GraphConfig` 参数注入，**不新增参数**）；`IFC-IB-232/233` 与 State 键（含 `MAX_EXPERT_STEPS = 8`）**不变**。
```
- rationale: REV-07-2 —— 「装配期完备性校验 + fail-fast」在编排模块侧的落点：把「拓扑不可编辑」写成模块级约束，并显式声明既有 IFC 签名未变。

### R7-M-24
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23；REQ-NFR-IB-09`
- new_string: `- **覆盖需求**: REQ-FUNC-IB-05、IB-06、IB-09、IB-17、IB-21、IB-23、**IB-25 / IB-27（R7 新增：定义文档的读写端点与装配期准入闸门）**；REQ-NFR-IB-09`
- rationale: REV-07-1 —— 组合根承担装配期闸门与两个新端点，须登记覆盖。

### R7-M-25
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `避免与 FreeArk 现有 `RAG_*` 环境变量约定冲突。`
- old_string: `（空：纯插入）`
- new_string:
```text
- **R7 新增契约与装配序列（可视化配置增量）**:
  - **IFC-IB-293**: 装配期**准入闸门** `admit(doc: DefinitionDocument) -> DerivedView`（内部调用 IFC-IB-290；不通过即**拒绝装配**，抛出聚合**全部** `ValidationErrorItem` 的 `ConfigError`）。
  - **IFC-IB-294**: `GET /api/config/definition` → `200 DefinitionDocument`（+ 派生视图摘要）| `403`（归属断言失败）| `503`（**fail-closed**：读不到文档即明确报错，**不返回空文档**）。
  - **IFC-IB-295**: `PUT /api/config/definition` → `200 SaveResult` | `400`（校验不通过：逐条 `path` / `code` / `message`）| `403` | `409`（乐观并发冲突，含可读冲突回执，**不静默覆盖**）| `503`（**fail-closed**）。
  - **R7 装配序列（显式化，任一步失败即启动失败）**: `装载定义文档（IFC-IB-288）→ 准入闸门（IFC-IB-293，内含 IFC-IB-290）→ 派生注册表 / 图配置（IFC-IB-291）→ 构造并注入（MOD-IB-16 / 17 / 19 / 22）→ 图编译一次常驻`。闸门位于**序列第一步**（ADR-16）。
  - **鉴权与凭据纪律（强制，扩展到全部新端点）**: 沿用 IFC-IB-247 口径，**仅允许 `Authorization` 头 / 中间件鉴权**；两个新端点**不接受** `?token=`；错误体**不回显任何凭据值**（AC-IB-18-04）；归属断言失败一律 `403`（**不因「是不是你的配置」而区分 `404`** —— 定义文档按 `project_id` 归属，同 §1.4 第 2 条精神）。
  - **R7 配置键不变声明**: 除 IFC-IB-297 新增的两个键名（`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）外，§5 装配表的**既有开关名与默认值一字不动**；**新增键名不含任何值**。
```
- rationale: REV-07-1 / -2 / -4 —— 闸门与端点的契约、装配序列与鉴权/凭据纪律集中落在一处，且不新增参数、不改既有键名。

### R7-M-26
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
- **职责**: 上传/列表/删除/重试/重建页 + 问答页；仅通过类型化 HTTP/SSE 契约与后端交互。
- **覆盖需求**: REQ-FUNC-IB-09、IB-17
```
- new_string:
```text
- **职责**: 上传/列表/删除/重试/重建页 + 问答页 + **可视化配置页（R7）**；仅通过类型化 HTTP/SSE 契约与后端交互。
- **覆盖需求**: REQ-FUNC-IB-09、IB-17、**IB-25（主）、IB-26（并列主，与 MOD-IB-22）、IB-27（辅）**
```
- rationale: REV-07-1 —— 可视化视图的主覆盖落在前端模块（与 §9.1 新增三行的主 / 辅归属保持一致）。

### R7-M-27
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `对齐 ADR-13「故障与空结果可区分」。`
- old_string: `（空：纯插入）`
- new_string:
```text
- **R7 可视化配置页约束（IFC-IB-296）**:
  - **视图侧零持久化**：**不得**以 `localStorage` / `IndexedDB` / 独立后端表作为真源（ADR-14）；未提交草稿若存在，须在界面**显式标注「未提交（可丢弃）」**且**不得**作为下次载入源。
  - **白名单制**：只渲染 / 只提交 IFC-IB-292 白名单内的字段；**不得**提供运行期增删图节点、改变拓扑或编辑条件边存在性的入口（REQ-FUNC-IB-26；ADR-14 强制约束③）。
  - **编排图只读渲染**：用图可视化库渲染 `OrchestrationSpecInput` 产生的图（节点参数可编辑、**拓扑不可编辑**）；条件边须能按 `branch_map` 表达分支可达性。
  - **以文档为准刷新**：服务端返回的文档更新后，界面**必须以文档为准**刷新，**不得**用陈旧视图反向覆盖（AC-IB-17-03）；`409` 冲突须给出可读回执而非静默丢弃。
  - **凭据不回显**：配置项只显示**键名**，不显示任何值 / 掩码 / 前缀（AC-IB-17-05）。
  - **离线与数据本地化**：图可视化库及其传递依赖须**随构建产物本地打包**；**禁止运行期 CDN 加载**与任何外发请求（AC-IB-17-06、REQ-NFR-IB-08）。
  - **前端不做校验的最终裁决者**：前端预校验仅为体验优化；**服务端校验器（IFC-IB-290）为唯一裁决者**（界面编辑与直接改文档**一视同仁**）。
```
- rationale: REV-07-4 / -5 —— 前端约束必须可逐条核验（每条约对应一个 AC），且明确「前端预校验不是裁决者」。

---

## 2. §4 / §5 / §7.4 / §8 增补

### R7-M-28
- target_file: `docs/module_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `### 4.3 分层视图`
- old_string: `（空：纯插入）`
- new_string:
```text
### 4.2.2 R7 无环性再声明（可视化配置增量后）

**结论：DAG 拓扑在 R7 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：R7 的全部新增落在 **MOD-IB-01 / 02 / 23 / 24** 内部（契约与第 14 个端口 / 定义文档数据层 / 装配期闸门与端点 / 可视化视图约束），**§4.1 依赖边清单逐行未改**；因此 `w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **为何不新增模块（编号即拓扑序的边界情形）**：见 §1「R7 补充纪律」。要点：定义文档数据层**必然被组合根 MOD-IB-23 依赖**，而新模块只能取 **≥27** 的编号 → 会产生 `23 → 27` 的边，**违反 `w(A) > w(B)`**；替代的独立服务进程方案则净增第 5 个 systemd 单元（与 C-IB-08 / ADR-03 冲突）。故并入既有模块。
- **新端口不引入新边**：`DefinitionDocumentStore`（IFC-IB-287）定义于 **MOD-IB-01（L0）**；其生产适配器 `FileDefinitionDocumentStore` 由 **MOD-IB-23 在装配期构造**（复用既有边 `23 → 01 / 02`），MOD-IB-02 的实现只依赖 MOD-IB-01（既有边），**二者均不产生新边**。
- **既有单一入口纪律未被绕开**：定义文档是**项目级**工件，`Scope` 仍为必填（ADR-04）；「取定义文档 / 派生结果的唯一入口」与 `CollectionResolver` 的单一入口纪律同构（§2.2 R7 增记）。
- 因此「编号即拓扑序」继续适用于 GROUP_C，并**追加一条边界纪律**：**新增工件若被低编号模块（尤其组合根）依赖，不得新开编号更高的模块**。
```
- rationale: REV-07-6 —— 覆盖矩阵与无环性必须「同步更新」（PM 明令）；本条给出与 §4.2 / §4.2.1 同构的再声明，且把边界纪律写进 GROUP_C 约束。

### R7-M-29
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| `ConfigurationSource` | 文件 + 环境变量 | 测试用固定字典 | `IB_CONFIG_SOURCE=file\|dict` |`
- old_string: `（空：纯插入）`
- new_string:
```text
| `DefinitionDocumentStore`（**R7 新增**） | `FileDefinitionDocumentStore`（本地文件；原子写 + 语义哈希乐观并发） | `InMemoryDefinitionDocumentStore`（内存字典 + 同一校验器） | `IB_DEFINITION_DOC_PATH`（路径）；`IB_VISUAL_CONFIG_ENABLED=true\|false` |
```
- rationale: REV-07-1 / -5 —— 装配表为「所有适配器选择的唯一集中处」，新端口必须有生产装配与离线替身两列（与 §8 替身清单成对）。

### R7-M-30
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `**一键离线**：`IB_OFFLINE_MODE=1` 等价于把上表全部置为「离线/测试」列（AC-IB-15-01、附录 D）。`
- old_string: `（空：纯插入）`
- new_string:
```text
> **R7 装配说明（定义文档）**：① 定义文档的**装配期装载 → 准入闸门 → 派生 → 注入**序列见 §3 MOD-IB-23；② 一键离线下 `DefinitionDocumentStore` 取「离线/测试」列（`InMemoryDefinitionDocumentStore`），**装配期闸门与校验器照常执行**（离线亦可验证 AC-IB-18-01/02/05）；③ 新增键 `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED` **只登记键名**，其取值（含路径中的任何敏感信息）一律不进文档、不进日志（凭据纪律）。
```

- rationale: REV-07-4 —— 离线语义必须覆盖新增端口，否则「一键离线」在 R7 后出现未声明的例外。

### R7-M-31
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| **WSGI 工作进程**（R1 新增）`
- old_string: `（空：纯插入）`
- new_string:
```text
| **定义文档（装配期）**（R7 新增） | 文档缺失 / 不可解析 / 完备性校验不通过 | **拒绝装配，服务不启动**（fail-fast）；错误逐条定位到 `path` / `code` / `message`（**不回显凭据值**） | 部署者见启动失败日志（界面尚不可用） | ERROR | **fail-closed（装配期）** |
| **定义文档（运行期读）**（R7 新增） | 运行期文档不可读（被移走 / 权限变化） | `GET /api/config/definition` 返回 `503`（**不返回空文档**）；**问答主链路不受影响**（派生结果已于装配期常驻内存，不重新读文档） | 「配置暂时不可读，请稍后重试」 | ERROR | **fail-closed（配置读）**；对问答链路无影响 |
```
- rationale: REV-07-2 —— 新失败面必须进降级矩阵；本条同时厘清「装配期 fail-closed」与「运行期对问答无影响」的时间轴分离。

### R7-M-32
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| `ConfigurationSource` | 文件 + 环境变量 | 固定字典 | 必填校验与可读错误 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| `DefinitionDocumentStore`（**R7 新增**） | `FileDefinitionDocumentStore` | `InMemoryDefinitionDocumentStore` | 装载失败 / 原子写回 / 乐观并发冲突（`conflict=True`）/ 完备性校验拒绝 / 白名单边界 |
```
- rationale: REV-07-1 / -5 —— 替身清单与装配表逐项对应（离线可测是 REQ-NFR-IB-14 的硬要求）。

### R7-M-33
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `、MOD-IB-14（`fingerprint`）。`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 追加的离线可测单元**（纯函数、无外部 IO）：**MOD-IB-02** 的 `validate`（IFC-IB-290）与 `derive`（IFC-IB-291）—— 前者对 **≥7 类**校验项逐条可测（AC-IB-18-01/02/05），后者对派生结果做结构等价断言；配合 `InMemoryDefinitionDocumentStore` 即可在**无任何外部服务**下完成装配期全链路离线验证（AC-IB-18-05）。
```
- rationale: REV-07-5 —— 「可离线单测」是 REQ-FUNC-IB-27 与 AC-IB-18-05 的明文要求，须在离线单元清单中显式登记。

---

## 3. §9 覆盖率矩阵与计数同步

### R7-M-34
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-24，**24/24 全覆盖**）`
- new_string: `### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-27，**27/27 全覆盖**；R7 同步计数，v1.2.0 需求总数）`
- rationale: REV-07-3 —— 矩阵标题的范围与计数同步（需求计数语境）。

### R7-M-35
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| IB-24 | 索引重建 | **MOD-IB-14** / 12, 13 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| IB-25 | 可视化配置界面（定义文档的图形视图；round-trip 回写；**无第二真源**；数据不出本地） | **MOD-IB-24** / 02, 01, 23 |
| IB-26 | 可编辑范围（节点参数与专家集合；**不含**运行期改图；白名单制；条件边须显式分支映射） | **MOD-IB-24, MOD-IB-22** / 02, 01 |
| IB-27 | 装配期完备性校验与 fail-fast 准入闸门（可读定位；**无**强制继续开关；界面与直改文档一视同仁；默认专家恰好一个） | **MOD-IB-23, MOD-IB-02** / 01, 24 |
```
- rationale: REV-07-1（首要项）—— 每条新需求必须有**主**覆盖模块；三条各自指定主模块（含一条双主，与既有 IB-11 / IB-15 的双主写法一致），辅覆盖列出契约 / 数据层 / 编排 / 视图的支撑关系。

### R7-M-36
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**无缺口**：24 条 REQ-FUNC 每条至少一个「主」模块，且每条均可被至少一个 AC 验证。`
- new_string: `**无缺口**：**27 条 REQ-FUNC**（R7 同步计数；R1 / R2 时点基线 24 条）每条至少一个「主」模块，且每条均可被至少一个 AC 验证（R7 新增 3 条见上三行，AC 落点分别为 AC-IB-17-01~06、AC-IB-17-04 / AC-IB-18-01、AC-IB-18-01~06）。`
- rationale: REV-07-3 —— §9.1 结论句同步；并给出新需求到 AC 的可核验映射。

### R7-M-37
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| NFR-14 | 可测试性 | **MOD-IB-01** / §8 替身清单 |`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 说明（NFR 覆盖不变）**：R7 **不新增 NFR 条目**，14 条 NFR 的主 / 辅归属**一行未改**。新增结构对 NFR 的作用为**既有条目的加固**：`DefinitionDocumentStore`（IFC-IB-287）服务 **NFR-11（可维护性 / 模块边界）**；`validate` / `derive`（IFC-IB-290 / 291）为纯函数 + 替身齐备，服务 **NFR-14（可测试性）**；装配期闸门服务 **NFR-02（可配置性）**；「数据不出本地 + 前端禁止 CDN」服务 **NFR-08**。
```

- rationale: REV-07-1（「§9.2 NFR 覆盖同步」）—— 明确「同步 = 声明未变 + 说明加固关系」，避免读者以为 R7 遗漏了 NFR 侧更新。

### R7-M-38
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**结论：24/24 REQ-FUNC + 14 REQ-NFR 覆盖情况在 R1 下不变，无新增缺口。**`
- new_string: `**结论：27/27 REQ-FUNC（R7 同步计数；R1 时点基线为 24/24）+ 14 REQ-NFR 覆盖情况在 R1 下不变，无新增缺口。**`
- rationale: REV-07-3 —— 计数同步；历史时点以括注保留（R1 结论行不回改事实）。

### R7-M-39
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**结论：24/24 REQ-FUNC + 14 REQ-NFR 覆盖不变，无新增缺口；R2 的新增只**加固**既有覆盖，不改任何既有主/辅归属。**`
- new_string: `**结论：27/27 REQ-FUNC（R7 同步计数；R2 时点基线为 24/24）+ 14 REQ-NFR 覆盖不变，无新增缺口；R2 的新增只**加固**既有覆盖，不改任何既有主/辅归属。**`
- rationale: REV-07-3 —— 同上（R2 节）。

### R7-M-40
- target_file: `docs/module_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）`
- old_string: `（空：纯插入）`
- new_string:
```text
### 9.5 R7 覆盖率再声明（可视化配置增量）

**结论：27/27 REQ-FUNC（R7 同步计数；R1 / R2 时点基线 24/24）+ 14 REQ-NFR 覆盖达成，无新增缺口。**

- **三条新增需求均有主模块**：IB-25 → **MOD-IB-24** / 02, 01, 23；IB-26 → **MOD-IB-24, MOD-IB-22** / 02, 01；IB-27 → **MOD-IB-23, MOD-IB-02** / 01, 24（见 §9.1 末三行）。
- **施工前置条件 ≠ 覆盖缺口**：REQ-FUNC-IB-25 / 26 / 27 的落地**有施工顺序前置** ——「专家 / 路由 / 编排 / 工具授权的定义须先外置为数据、且为单一真源」（即 REQ-FUNC-IB-01 / IB-02 的**实现落差**）；`requirements_spec.md` §2.7 前言已明示该前提「**不在本节新增需求**」。本文件**不把该前置计为覆盖缺口**：三条需求均已有**主模块 + 类型化接口落点**，受影响的只是**施工先后**（定义外置先于界面填充真实内容）。
- **REV-07-6 判定 = (a) 可登记的前置条件 / 风险，本轮继续**（另见 `architecture_design.md` §8 [ARCH-ASSUMPTION-A7] 与 §10.1）。若 PM / 用户改判 (b)，本修订整体回退并回 GROUP_A 立项 —— **该裁定权不在本代理**。
- **模块与依赖不变**：R7 **未新增模块、未新增依赖边**（§1 R7 补充纪律、§4.2.2）；`IFC-IB-001~286` 与 13 个既有端口名一字不动（新增 287~297 为纯追加，`IFC-IB-285` 仍预留）。
- **无在库悬置项**：`implementation_plan.md`（GROUP_C）内的「24/24 PASS」为**离线自检用例数**，与本文件的 REQ 计数 **27** 属**不同口径**，本文件**不得**据此改写该文件。

```

- rationale: REV-07-1 / -6 —— 覆盖率「再声明」是与 §9.3 / §9.4 同构的审计范式；此处把 REV-07-6 的判定与「≠ 覆盖缺口」的论证同时落纸。

---

## 4. §11 自检声明

### R7-M-41
- target_file: `docs/module_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `- **门控标准 1（REQ → MOD 全覆盖）**：§9.1 逐条列出 24 条 REQ-FUNC，**每条均有主模块**，无缺口；§9.2 覆盖 14 条 REQ-NFR。`
- new_string: `- **门控标准 1（REQ → MOD 全覆盖）**：§9.1 逐条列出 **27 条 REQ-FUNC**（R7 同步计数：新增 IB-25 / IB-26 / IB-27 三行，各有主模块），**每条均有主模块**，无缺口；§9.2 覆盖 14 条 REQ-NFR（R7 未变）。`
- rationale: REV-07-3 —— 自检节与 §9.1 计数一致（同一语境）。

### R7-M-42
- target_file: `docs/module_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `**未写入任何凭据或配置值**（只登记键名）；本阶段**止于 GROUP_B**。`
- old_string: `（空：纯插入）`
- new_string:
```text
    - **R7 自检（可视化配置增量，GROUP_A REV-06 下游贯通）**：
      - **覆盖同步**：§9.1 由 24/24 同步为 **27/27 REQ-FUNC**（新增 IB-25 / IB-26 / IB-27，各有主模块），§9.2 NFR 覆盖未变（14 条，另见该节 R7 说明）；§9.3 / §9.4 结论句以括注保留历史基线；**§9.5 给出 R7 再声明**（含「施工前置条件 ≠ 覆盖缺口」）。
      - **零新增模块 / 零新增依赖边**：模块数仍 **26**；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 23 / 24（§1 R7 补充纪律给出「为何不新增 MOD-IB-27」的编号论证；§4.2.2 给出无环性再声明）。
      - **类型化未降级**：新增 `IFC-IB-287~297`（11 条）全部为 `name: type` + 可空性的**类型化契约**（IFC-IB-287 为端口 Protocol + 结构定义），均为 **frozen dataclass / 纯 stdlib、零第三方依赖**；`ValidationReport` 结构上**不含** `force` / `ignore` / `warn_only`（「无强制继续开关」= **类型层事实**）。
      - **编号纪律未破**：`IFC-IB-001~286` 一字不动；新增 287~297 为**纯追加**；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。
      - **施工前置已登记且不阻断**：§9.5 显式声明前置与其非缺口性质；**REV-07-6 判定 = (a)**；本轮**未**设计 REQ-FUNC-IB-01 / IB-02 的实现方案（超 GROUP_B 边界，需求侧亦未立项）。
      - **边界合规**：R7 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为**离线自检用例数**，与本文件 REQ 计数 27 **不同口径**）；**未写入任何凭据或配置值**（只登记键名：`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；本阶段**止于 GROUP_B**。
```

- rationale: REV-07-3 / -6 —— R7 自检须与 R1 / R2 自检同构，并把「不得混淆两种 24」写成显式条目。
