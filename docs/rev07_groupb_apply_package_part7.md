<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package_part7</artifact>
  <path>docs/rev07_groupb_apply_package_part7.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_04b 技术选型）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/tech_stack.md</targets>
</file_header>

# REV-07 APPLY-READY 修订包 · 第 7 册 — 技术栈指令 + 落盘后核验清单

> 本册含 `R7-T-01 ~ R7-T-13`（13 条，target 均为 `docs/tech_stack.md`）与两份收尾核验表（§2 落盘后核验清单 / §3 不变量核对表）。
> **全包最终条数**：`R7-A-*` = 20 + `R7-M-*` = 42 + `R7-T-*` = 13 → **75 条**。

## 1. `docs/tech_stack.md` 指令（R7-T-01 ~ R7-T-13）

### R7-T-01
- target_file: `docs/tech_stack.md`
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

### R7-T-02
- target_file: `docs/tech_stack.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `  <updated_at>2026-09-26</updated_at>`
- new_string: `  <updated_at>2026-09-27</updated_at>`
- rationale: 修订日期同步为 REV-07 日期。

### R7-T-03
- target_file: `docs/tech_stack.md`
- action: `REPLACE`
- anchor（= old_string，唯一）:
```text
    <input path="docs/requirements_spec.md" version="1.1.0" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.2.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/module_design.md" version="1.2.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW"/>
```
- new_string:
```text
    <input path="docs/requirements_spec.md" version="1.2.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.2.0" status="APPROVED" note="R7 新增登记：可视化配置的 AC 落点（AC-IB-17-01~06 / AC-IB-18-01~06）为 §4.5 新增项与 §1.3 凭据纪律的直接依据"/>
    <input path="docs/architecture_design.md" version="1.3.0" revision="R7" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/module_design.md" version="1.3.0" revision="R7" status="DRAFT_FOR_GATE_REVIEW"/>
```
- rationale: REV-07-7 —— 需求侧引用版本 1.1.0 → 1.2.0；架构 / 模块文档引用同步为 1.3.0（R7）；并**新增登记 `user_stories.md`**（R7 的验证项直接引用其 AC，登记后才可追溯）。

### R7-T-04
- target_file: `docs/tech_stack.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `  </revision_history>`
- old_string: `（空：纯插入）`
- new_string:
```text
    <rev version="1.3.0" revision="R7" date="2026-09-27" invocation_id="INV-GROUP_B-INTELBASE-005" note="R7 增量贯通（GROUP_A REV-06 裁决：诉求③「UI 可视化配置」纳入 v1，新增 REQ-FUNC-IB-25/26/27）：① 新增「前端图可视化库」行 = Vue Flow（@vue-flow/core，MIT，R7 经外部核实：包内 LICENSE 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024），要求随构建产物本地打包、禁止运行期 CDN；② §1.1 留痕 5 项已评估未采纳（AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / 运行期 CDN 加载）；③ 新增 §1.3 客户端配置键登记（只登记键名 IB_DEFINITION_DOC_PATH / IB_VISUAL_CONFIG_ENABLED，不含任何值）；④ §2 台账登记 Vue Flow（MIT，采纳）与传递依赖（条件性采纳 + [待核实]，须锁定版本后逐包复核）；⑤ §4.5 新增第 10~12 项（前端产物零外发依赖、装配期 fail-fast 实测、定义文档凭据明文扫描）；⑥ §5.3 新增两行低风险（定义文档被写入凭据明文 / 图库传递依赖的许可与体积，以 [TBD-T20] 实测为准）；⑦ 硬约束未松动：未引入 Docker / Redis / PyMuPDF，端口契约仍 framework-free。需求侧文档与 FreeArk 仓库未改动；未写入任何凭据或配置值（只登记键名）。"/>
```
- rationale: REV-07-7 —— 新增 R7 修订历史行；历史行（1.0.0 / R1 / R2）**不回改**。

### R7-T-05
- target_file: `docs/tech_stack.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `**版本**: 1.2.0（R2 补交） | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-26`
- new_string: `**版本**: 1.3.0（R7 增量） | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-09-27`
- rationale: 文档头版本行同步（版本号 + 状态 + 日期）。

### R7-T-06
- target_file: `docs/tech_stack.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `**版本策略说明**：本表给出`
- old_string: `（空：纯插入）`
- new_string:
```text
**R7 修订摘要（GROUP_A REV-06 下游贯通：诉求③「UI 可视化配置」纳入 v1）**：

| 序 | 改动 | 落点 |
|----|------|------|
| 1 | 新增「**前端图可视化库**」行 = **Vue Flow（`@vue-flow/core`，MIT）**（选型理由 / 许可 / 离线本地打包 / 传递依赖待核实） | §1（新行，标「R7 新增」） |
| 2 | §1.1 留痕 **5 项已评估未采纳**：AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / **运行期 CDN 加载** | §1.1 |
| 3 | 新增 **§1.3 客户端配置键登记**（只登记键名与语义，**不含任何值**） | §1.3（新增） |
| 4 | §2 台账登记 **Vue Flow（MIT，采纳）** 与**传递依赖（条件性采纳 + `[待核实]`）** | §2 |
| 5 | §4.5 新增第 **10~12** 项：前端产物**零外发依赖**、**装配期 fail-fast 实测**、**定义文档凭据明文扫描** | §4.5 |
| 6 | §5.3 新增两行低风险：定义文档被写入凭据明文 / 图库传递依赖的许可与体积（[TBD-T20]） | §5.3 |
| 7 | **禁项与硬约束未松动**：未引入 Docker / Redis / PyMuPDF；图库**禁 CDN**；端口契约仍 framework-free | 全文 |

```

- rationale: REV-07-4 —— 与既有 R1 / R2 修订摘要（表格形式）保持一致；「新增了什么、落在哪」一表可核。

### R7-T-07
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `**（R1）前端不受后端框架切换影响：Vue 3 + Vite 不变** |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **前端图可视化库（R7 新增）** | **Vue Flow**（`@vue-flow/core`） | 主版本随实现锁定（建议 `^1`）；部署时锁定 | 可视化配置页需渲染编排图（节点 / 条件边 / 分支可达性），Vue 3 生态内成熟首选：组件化节点与边、视口与缩放、**只读模式**（节点不可拖拽、不可连线）开箱可用；**MIT 许可**；可**随构建产物本地打包**（满足离线 + 数据不出本地，AC-IB-17-06） | REQ-FUNC-IB-25、IB-26；AC-IB-17-02、AC-IB-17-06；REQ-NFR-IB-08 | 中 | **MIT（R7 经外部核实：包内 `LICENSE` 为标准 MIT 文本，© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024）**；**传递依赖**（D3 系 / `@vueuse/core` 等）须在锁定版本后**逐包核实并登记**（未核实者标 `[待核实]`），见 §2 与 [TBD-T20]；**禁止运行期 CDN 加载**；**只读渲染优先**（拓扑不可编辑，ADR-14 / ADR-15） |
```
- rationale: REV-07-4 —— 技术选型表「每项须有 Rationale / 关联 REQ-* / 风险」的门控要求在本行逐列满足；风险列显式指向 [TBD-T20]。

### R7-T-08
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| 本地 LLM（v1） | 与 DR-04 冲突；显著加重目标机 CPU/内存压力。**保留 v2 经同一端口接入** | ADR-08 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **AntV X6（R7 新增）** | 图编辑能力更强（拖拽连线、布局算法齐备），但**框架无关的独立图引擎**在本项目「只读渲染 + 白名单表单」的前提下属**能力过剩**；引入自成一体的图形栈与主题体系，与既有 Vue 3 组件体系叠两套心智模型。**已评估未采纳** | REQ-FUNC-IB-26；ADR-14 |
| **LogicFlow（R7 新增）** | 国产流程编排图库，流程图语义贴合；但生态与社区规模小于 Vue Flow，且其**编辑导向**（锚点 / 连线）与「**拓扑不可编辑**」硬约束需要额外裁剪。**已评估未采纳** | REQ-FUNC-IB-26；ADR-14 |
| **React Flow（R7 新增）** | 与 Vue Flow 同源、成熟度最高；但**要求 React 运行时**，与既有前端栈（Vue 3 + Vite）冲突，为单一页面引入第二前端框架不可接受。**已评估未采纳** | REQ-FUNC-IB-25；ADR-11 |
| **自绘 SVG / 直接使用 D3（R7 新增）** | 零新依赖、产物体积最小；但需自实现节点布局、边路由、缩放平移与命中测试，**维护与回归成本显著高于引入成熟库**（D3 许可仍需登记）。**已评估未采纳**；**保留为回退路径**：若将来要求「零新增前端依赖」，可回退至此并在 §2 补登 D3 许可 | REQ-FUNC-IB-25；REQ-NFR-IB-11 |
| **运行期 CDN 加载图库（R7 新增）** | 免打包、可远程热更；但**违反「数据不出本地 / 离线可用」**（AC-IB-17-06），并引入外部可用性与供应链风险。**已评估未采纳（并明令禁止）** | REQ-NFR-IB-08；AC-IB-17-06 |
```
- rationale: REV-07-4 —— 「已评估未采纳」留痕是门控标准 3 的组成；本组留痕同时封死「用 CDN 省事」这条最可能的违规捷径。

### R7-T-09
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `破坏 ADR-02-R2 附注的单一落点。`
- old_string: `（空：纯插入）`
- new_string:
```text
### 1.3 客户端配置键登记（**R7 新增**；只登记键名与语义，**不含任何值**）

> **用途**：REV-07（可视化配置）为 `ib-web` 侧新增两个配置键（IFC-IB-297）。与 §1.2 的分工：**§1.2 = `ib-embed` 服务端键**（不得在此补服务端超时 / 重试键），**本节 = `ib-web` 客户端键**。语义与校验规则以 `module_design.md` §3 MOD-IB-02 / MOD-IB-23 为准；键名的唯一权威落点为 `module_design.md` §2.2.2（IFC-IB-297）。

| 键名 | 语义（一句话） | 关联 IFC |
|------|---------------|----------|
| `IB_DEFINITION_DOC_PATH` | 定义文档的本地文件路径（**一项目一文档**；[ARCH-ASSUMPTION-A6]）；装配期由准入闸门读取 | IFC-IB-288 / IFC-IB-293 / IFC-IB-297 |
| `IB_VISUAL_CONFIG_ENABLED` | 可视化配置页与定义文档端点（`GET` / `PUT`）的开关；关闭时端点不注册、界面不提供入口 | IFC-IB-294 / IFC-IB-295 / IFC-IB-297 |

**凭据纪律（强制）**：上述键**只登记键名**。定义文档内**只允许出现键名**（如凭据型配置项**的名称**），**不得出现任何值**；界面与校验错误信息**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；`?token=` / `?key=` 类凭据型查询串纪律（§3）**扩展至全部新端点**（含定义文档的 `GET` / `PUT`）。若 `IB_DEFINITION_DOC_PATH` 的路径本身含敏感信息，须经**环境变量**注入且**不得**写入文档、日志或响应。
```

- rationale: REV-07-4 / -7 —— 新键必须有登记落点；采用**新增 §1.3** 而非并入 §1.2（§1.2 的服务端边界被 R2 明令封闭，混入客户端键会破坏该边界）。

### R7-T-10
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| Vue 3 / Vite | MIT | 宽松 | 采纳 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **Vue Flow（`@vue-flow/core`）（R7 新增）** | **MIT** | 宽松 | **采纳**（可视化配置页的编排图渲染）。**R7 经外部核实**：包内 `LICENSE` 为标准 MIT 文本（© webkid GmbH 2019–2024 / Burak Cakmakoglu 2021–2024） |
| **Vue Flow 的传递依赖（R7 新增）** | **待逐包核实**（D3 系一般为 ISC / BSD 类、`@vueuse/core` 为 MIT，**均须以发行包内 `LICENSE` 复核**） | 预计宽松 | **条件性采纳 + `[待核实]`**：锁定版本后逐包登记；**任一传递依赖出现 copyleft / AGPL 面即须回 §1 重新选型**（**不得**沿用「内部平台合规」豁免，REQ-NFR-IB-12）；传递依赖的许可留痕规则见本节末段 |
```

- rationale: REV-07-4 —— 「许可必须经外部核实或标 `[待核实]`」；主体已核实（采纳）、传递依赖未核实（条件性采纳 + 标记），两态分明。

### R7-T-11
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| 9 | 前端（Vue 3 + Vite）构建产物可托管并完成一次端到端问答 | REQ-FUNC-IB-09/17；**前端不受后端框架切换影响（R1）** |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **10** | **（R7）前端产物零外发依赖**：图可视化库及全部前端依赖**随构建产物本地打包**；产物体内**不得**出现指向公网 CDN / 字体 / 图床的引用 | 断网状态下可视化配置页可正常加载与渲染；构建产物内公网 URL 扫描**零命中**（AC-IB-17-06；REQ-NFR-IB-08） |
| **11** | **（R7）装配期 fail-fast 实测**：故意提交一份非法定义文档（如条件边缺分支映射 / 默认专家为 0 个或 2 个 / 工具授权引用不存在的工具），观察装配行为 | **拒绝装配、服务不启动**；错误**逐条定位**到 `path` / `code` / `message` 且**不回显凭据值**；**不存在**「启动成功、首次提问才失败」的路径（AC-IB-18-01 / 02 / 03 / 04 / 06） |
| **12** | **（R7）定义文档凭据明文扫描**：定义文档、`.env.example` 与全部响应体扫描 | **零命中**任何凭据型**值**（只允许出现**键名**）；`GET /api/config/definition` 的响应体内**无**任何凭据值或掩码残留（AC-IB-17-05 / AC-IB-18-04；§1.3 纪律） |
```

- rationale: REV-07-4 —— 新选型与硬约束需要「可复查证据」的落点（本清单的既有纪律）；第 11 项把「无强制继续开关」转为**可观测的实测判据**。

### R7-T-12
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| 反向代理缓冲破坏 SSE | 部署检查项：禁用响应缓冲（`X-Accel-Buffering: no`） |`
- old_string: `（空：纯插入）`
- new_string:
```text
| **（R7 新增）定义文档被写入凭据明文** | 缓解：定义文档**只允许出现键名**（§1.3）；界面与校验错误**不回显**凭据值（AC-IB-17-05 / AC-IB-18-04）；§4.5 第 12 项加入「定义文档凭据明文扫描」；仓库内**不得**出现除 `.env.example` 之外的任何真实值 |
| **（R7 新增）图可视化库传递依赖的许可与体积** | 缓解：主体 `@vue-flow/core` 的 **MIT 已外部核实**；传递依赖（D3 系 / `@vueuse/core`）**锁定版本后逐包复核并登记**于 §2（未核实者标 `[待核实]`，出现 copyleft 面则回 §1 重选）；体积与渲染规模上界以 **[TBD-T20]** 实测为准；**禁止 CDN**（AC-IB-17-06） |
```

- rationale: REV-07-4 —— 新增面必进风险汇总（本文件纪律：风险表不得遗漏新增组件面）。

### R7-T-13
- target_file: `docs/tech_stack.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `- **（R2）未改动他处**：`
- old_string: `（空：纯插入）`
- new_string:
```text
- **（R7）可视化配置增量的技术面结论**：① 新增**前端图可视化库 = Vue Flow（`@vue-flow/core`，MIT，R7 经外部核实）**（§1 新行）；§1.1 留痕 **5 项**已评估未采纳（AntV X6 / LogicFlow / React Flow / 自绘 SVG-D3 / **运行期 CDN 加载**）；② §2 台账登记 Vue Flow（**MIT，采纳**）与**传递依赖（条件性采纳 + `[待核实]`）**；③ 新增 **§1.3 客户端配置键登记**（只登记键名 `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`，**不含任何值**）；④ §4.5 新增第 **10~12** 项（前端产物**零外发依赖**、**装配期 fail-fast 实测**、**定义文档凭据明文扫描**）；⑤ §5.3 新增两行低风险（定义文档被写入凭据明文 / 图库传递依赖的许可与体积，后者以 [TBD-T20] 实测为准）。
- **（R7）禁项与硬约束未松动**：**未引入 Docker / 容器化**（DR-03）、**未引入 Redis / RabbitMQ**（C-IB-08）、**未引入 PyMuPDF 或任何 AGPL / copyleft 组件**（REQ-NFR-IB-12）；图库**随构建产物本地打包、禁止运行期 CDN**（数据不出本地，AC-IB-17-06）；**端口契约仍 framework-free**（新增契约落在 MOD-IB-01，纯 stdlib / frozen dataclass，零第三方依赖）。
- **（R7）凭据纪律**：§1.3 **只登记键名**；定义文档内**只允许出现键名**；全文**不含任何键值**；`?token=` / `?key=` 纪律由 §3 **扩展至全部新端点**（含定义文档的 `GET` / `PUT`）。
- **（R7）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`architecture_design.md` / `module_design.md` 的 R1 / R2 结论**未改写**（R7 只追加）；`implementation_plan.md`（GROUP_C）**未改动**（其 L471 / L603 / L621 / L732 的「24/24 PASS」为**离线自检用例数**，与本表的 REQ 计数口径无关，**不得混淆**）。
```

- rationale: 自检节须与 R1 / R2 自检同构；并把禁项、凭据纪律、未改动他处三项逐条落纸（PM 门控会逐条核验）。

---

## 2. 落盘后核验清单（PM 用；三条各跑一遍）

1. **锚点命中率**：75 条指令全部按序执行，**报错数 = 0**；任一「未找到匹配」须**停下核对原文**（全角 / 半角、行尾空格、代码 span 内的 `\|`），**不得**退化为整文件 Write（历史事故 KE-REQ-011 / KE-REQ-019）。
2. **`<file_header>` 一致性**：三份文档均 `<version>1.3.0</version>`、`<revision>R7</revision>`；`<input>` 中 `requirements_spec.md` / `user_stories.md` 均为 `1.2.0`；架构 / 模块文档互引均为 `1.3.0`；正文版本行与 `<file_header>` 一致；`<status>` 均为 `DRAFT_FOR_GATE_REVIEW`。
3. **修订历史**：三份文档各**追加** 1 行 R7（含 `invocation_id="INV-GROUP_B-INTELBASE-005"`）；R1 / R2（及 tech_stack 的 1.0.0）历史行**逐字未改**。
4. **计数同步（仅需求计数语境）**：`27/27` 与 `27 条 REQ-FUNC` 在 `module_design.md` §9.1 / §9.3 / §9.4 / §9.5 / §11 与 `architecture_design.md` §10.3 中一致出现；**`implementation_plan.md` L471 / L603 / L621 / L732 的「24/24 PASS」逐字未动**（如被改动，须立即回滚）。
5. **编号纪律**：`IFC-IB-285` 全文仍为「预留未分配」；`IFC-IB-287~297` 恰好 11 条且无重号；既有重号 `IFC-IB-131` 仍登记不修。
6. **禁项复核**：三份文档全文搜索 `Docker` 应只出现在「禁止 / 不采纳」语境；无 `CDN` 采纳类表述；无任何形如 `sk-` / `ghp_` / `-----BEGIN` 的字符串；无凭据型 query string 示例。
7. **越界复核**：`docs/requirements_spec.md` / `docs/user_stories.md` / `docs/ib_embed_service_contract.md` / `implementation_plan.md` / FreeArk 仓库**均无改动**（`git status` 应仅显示三份目标文档 + 本修订包文件）。

## 3. 不变量核对表（落盘后逐行勾选）

| # | 不变量 | 期望 | 出处 |
|---|--------|------|------|
| 1 | 模块数 | **26**（未新增；无 `MOD-IB-27`） | module_design §1 / §4.1 |
| 2 | §4.1 依赖边清单 | **逐行未改**（零新增边） | module_design §4.1 / §4.2.2 |
| 3 | 端口数 | **13 → 14**（新增 `DefinitionDocumentStore`，纯追加） | architecture §2.0.1 小结 / module_design §2.2 |
| 4 | IFC 编号 | `001~286` 一字不动；新增 **287~297**（11 条）；**285 仍预留** | module_design §2.2.1 / §2.2.2 |
| 5 | ADR 数 | **13 → 16**（ADR-14 / 15 / 16，各含 ≥2 方案与未采纳留痕） | architecture §2.0.2 / §10.3 |
| 6 | REQ 覆盖 | **27/27 REQ-FUNC + 14 NFR**（24/24 → 27/27 同步） | module_design §9.1 / §9.5 |
| 7 | 既有 ADR 复核 | ADR-01~13 **逐条声明「R7 不受影响」**（无一条跳过） | architecture §2.0.2 |
| 8 | 装配期闸门 | `ValidationReport` **无** `force` / `ignore` / `warn_only` | module_design §2.1 / §3 MOD-IB-02 |
| 9 | 单一真源 | 视图侧**零持久化**；派生**不落盘、不可反写** | architecture ADR-14 / ADR-15；module_design §3 MOD-IB-24 / MOD-IB-16 |
| 10 | 凭据 | 仅登记**键名**（`IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED`）；**无任何值** | tech_stack §1.3 / §6 |
| 11 | 许可 | Vue Flow **MIT 已外部核实**；传递依赖标 `[待核实]` | tech_stack §1 / §2 / §5.3 |
| 12 | 前置条件 | `[ARCH-ASSUMPTION-A7]` + §10.1 行 + module_design §9.5 均已落纸 | architecture §8 / §10.1；module_design §9.5 |

**REV-07-6 判定（最终口径）**：**(a) 可登记的前置条件 / 风险，本轮继续；不构成施工阻断（不报 BLOCKED）**。若 PM / 用户改判 **(b)**，则本包整体作废并回 GROUP_A 立项 —— 该裁量权不在 system-architect。
