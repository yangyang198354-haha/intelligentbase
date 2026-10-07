# REV-18 GROUP_B Apply-Ready 包（Main：前言 + Part A 架构增量）

```xml
<apply_ready_package>
  <project>intelligentbase</project>
  <producer>system-architect</producer>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
  <phase>GROUP_B / PHASE_03（架构设计）+ PHASE_04（模块详细设计）</phase>
  <revision>REV-18 / REV-18-2 下游贯通</revision>
  <date>2026-10-07</date>
  <landing_owner>pm-orchestrator（机械落盘；producer 不直接写目标文件）</landing_owner>
</apply_ready_package>
```

> **本包性质**：**apply-ready 编辑包**（不是最终文档）。producer（system-architect）**不得**直接写入 `docs/architecture_design.md` / `docs/module_design.md` / `docs/tech_stack.md`；由 PM **机械落盘**每一处 `ANCHOR / REPLACE / INSERT`。
> **本包不含实现代码**（无函数体、无伪代码级实现），**不含任何口令 / 令牌 / Key / 证书字面量**（只登记字段名 / 键名 / 掩码口径 / 文件权限 0600），**未触碰** `docs/requirements_spec.md`、`docs/user_stories.md`、`docs/phase_status.md`、`src/**`、`tests/**`，**未触碰** FreeArk 任何文件（全程只读）。

---

## 0. 落盘顺序与总览

### 0.1 文件清单与落盘顺序（严格按序）

| 序 | 文件 | 内容 | 目标文档 |
|----|------|------|----------|
| 1 | `docs/rev18_groupb_apply_package.md`（本文件） | 前言 / TOC / 落盘顺序 / REV-18 影响复核小结 / OPEN ITEM / **Part A：`architecture_design.md` 增量（EDIT-ARCH-01 ~ 11）** | `docs/architecture_design.md` |
| 2 | `docs/rev18_groupb_apply_package_part2.md` | **Part B：`module_design.md` 增量（EDIT-MOD-01 ~ 16）** | `docs/module_design.md` |
| 3 | `docs/rev18_groupb_apply_package_part3.md` | **Part C：`tech_stack.md` 增量（EDIT-TECH-01 ~ 04）** + **Part D：合并校对清单 + 落地自检** | `docs/tech_stack.md` + 校对 |

**落盘顺序**：A → B → C → D 校对。**同一文档内按 EDIT 编号升序落盘**；每个 EDIT 的 `ANCHOR` 均在该文档**当前状态**下唯一匹配（相邻 EDIT 的锚点互不重叠，故顺序可执行）。

### 0.2 每处 EDIT 的格式约定（统一）

```
■ EDIT-XXX-NN  ← 目标文件 + 位置说明
ANCHOR（old_string，逐字）：<必须唯一匹配的原文片段>
REPLACE（new_string，逐字）：<替换后文本>
```
- `INSERT` 型：`ANCHOR` 给出**插入点前后的边界行**，新文本插在两者之间（**不改动边界行本身**）。
- `REPLACE` 型：`ANCHOR` 整块被 `REPLACE` 整块替换。
- 所有 `ANCHOR` 中的 `&lt;` / `&gt;` 为**文档中的字面 XML 转义**（`file_header` 内），照抄即可。

### 0.3 REV-18 影响复核小结（供 GR-B 门控；**ADR-01 ~ 36 逐条不跳**）

承接 `docs/requirements_spec.md` v1.10.0 / **REV-18-2**（APPROVED）与 `docs/user_stories.md` v1.10.0 / **REV-18-2**（APPROVED），`architecture_design.md` v1.9.0 / REV-17（末条 ADR-36）的**既有 36 条 ADR 逐条复核结论**：

| 分类 | 条数 | ADR |
|------|------|-----|
| **不受影响** | 32 | ADR-01 / 02 / 03 / 04 / 05 / 06 / 07 / 09 / 10 / 11 / 12 / 13 / 14 / 15（含 -R1 / -R2）/ 16 / 17 / 19 / 20 / 22 / 23 / 24 / 25 / 27 / 29 / 30 / 31 / 32 / 33 / 34 / 35 / 36 + **ADR-26**（判「不受影响，且 REV-18 是其应用」）|
| **口径补注**（决策未动，仅登记取值来源 / 数据源的变更） | 3 | ADR-08（Key 取值来源 env → DB 装配期解析；ADR-08 的端口 / 外发边界结论**一字未动**）、ADR-18（REV-18 **复用**其「同一 SQLite 台账 + 手写 scoped 迁移」载体与机制）、ADR-28（`GET /api/projects` **数据源**由配置枚举改为项目注册表；端点号 / 名 / 签名与 fail-closed 语义**一字不动**）|
| **待裁决（口径张力，登记为 OPEN ITEM）** | 1 | **ADR-21**（R13 文本含「账户↔项目 **1:1** 绑定」；REV-18 OQ-IB-28 裁决为「**1:N**、零迁移、无 `users.project_id` 唯一约束」。是否冲突取决于 ADR-21 的 1:1 语义。**架构侧不自行改写 ADR-21**，见 §0.4 OI-1）|
| **新增** | 6 | **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42** |
| **合计** | **36 既有 + 6 新增 = 42** | **无一条跳过**（ADR-01 ~ ADR-36 全部在上述三类中出现）|

**AD 计数**：**36 → 42**。**不触及**：模块数（**26，未新增**）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 365` 的**号 / 名 / 签名一字不动**（**4 条文字与取值口径修订**，逐条登记于 Part B §2.2.9）。**端口 17 → 19（纯追加）**。**REQ→MOD 覆盖 42/42 → 48/48（REQ-FUNC）+ 19 → 20（REQ-NFR）**。

### 0.4 OPEN ITEMS（**登记，不发明**；请 PM / 用户裁决）

| 编号 | 事项 | 事实 | 架构侧处置（不外扩） | 影响面 |
|------|------|------|---------------------|--------|
| **OI-1** | ADR-21「账户↔项目 1:1 绑定」与 REV-18 OQ-IB-28「1:N、零迁移」的口径张力 | R13 ADR-21 的 1:1 若意为「**每账号恰绑一个项目**」则**不冲突**（本基座 `UserRecord.project_id` 本就单值）；若意为「**每项目至多一账号**」则与裁决**冲突**（裁决明令**不**加 `users.project_id` 唯一约束）| **不自行改写 ADR-21**。本包在 §0.3 将其列为「待裁决」；若判定需修订，架构侧另出 **ADR-21-R1**（amend 子节）| 若判「冲突」：需在 `requirements_spec.md` 明确 REQ-FUNC-IB-32 是否随之改 1:N（本包**未**改动任何既有 REQ 文本） |
| **OI-2** | LLM Key **首启**的供给序（派生后果，非新需求） | 用户裁决：Key 存 **DB**、`.env` 仅保留非 LLM Key 的其他密钥（OQ-IB-25 / REQ-NFR-IB-20）。既有装配在「缺 `IB_LLM_API_KEY`」时 `StartupError`；若沿用，则**首启 DB 无 Key → 服务不启动 → 管理界面不可达 → 无法写入首个 Key = 死锁** | 架构侧按**派生必要性**给出 **ADR-39**（放宽为「未配置态」：服务可启动；LLM 依赖路径 **fail-closed**；Key 管理端点始终可达），并登记本 OPEN ITEM。**未发明任何业务数值** | 若不采纳 ADR-39 的放宽，则须给出「部署期预置 Key」的**用户手工步骤**（属 C-IB-38 口径）；二选一由 PM / 用户裁决 |
| **OI-3** | LLM Key 的**掩码口径** | REQ-FUNC-IB-47 约束①要求「只回掩码 / 存在性与更新时间」 | 架构侧将 `LlmKeyStatus.masked` 定为**固定占位掩码**（**不含明文任何前 / 后缀字符**，避免长度 / 前缀侧信道），并**以类型层排除明文**（响应类型无明文字段）。具体掩码字面由施工期定，**本包不写死** | 无（口径已收敛到「无明文可分」） |

### 0.5 与本轮登记的生产事实（须写入交付说明，**不得设计为代理自动执行**）

- **生产后端重启与首次环境变量配置须由用户执行**（本轮特别登记）。本包所有「重新装配方能生效」的口径，一律写作「**由用户手工执行 `ib-web` / `ib-worker` 重启**」；**不得**设计为代理自动重启 / 自动改 `.env`。ADR-32（保存 + 服务重启重装配）**生效口径不变**。
- Key 的**唯一写入口** = `PUT /api/llm-key`（ADR-38）；`.env` 的 `IB_LLM_API_KEY` **停止作为 Key 来源**（登记型口径修订，见 EDIT-ARCH-08 后的 ADR-38 Consequences 与 EDIT-MOD-09）。

---

## 1. EDIT 索引（合并）

| EDIT | 目标文件 | 位置 | 类型 | 摘要 |
|------|----------|------|------|------|
| EDIT-ARCH-01 | architecture_design.md | `file_header` | REPLACE | version 1.9.0→1.10.0 / revision REV-17→REV-18 / invocation→012 |
| EDIT-ARCH-02 | architecture_design.md | `file_header/inputs` | REPLACE | 输入指针 → requirements_spec 1.10.0/REV-18-2；user_stories 1.10.0/REV-18-2 |
| EDIT-ARCH-03 | architecture_design.md | `file_header/revision_history` 末 | INSERT | 追加 `<rev version="1.10.0" revision="REV-18" .../>` |
| EDIT-ARCH-04 | architecture_design.md | 顶部修订摘要区（REV-17 摘要在前） | INSERT | 追加「（REV-18）…」修订摘要块；并改版次行 |
| EDIT-ARCH-05 | architecture_design.md | §1.3 可替换点表末 + 增补段末 | INSERT | 新增 2 行（`ProjectRegistryStore` / `LlmKeyStore`）+ REV-18 增补段 |
| EDIT-ARCH-06 | architecture_design.md | §2.0.9（R17 表之后、ADR-01 之前） | INSERT | 新增 §2.0.9 REV-18 影响复核表（ADR-01~36 不跳）+ REV-18 文字修订 IFC 登记 |
| EDIT-ARCH-07 | architecture_design.md | §2 末（ADR-36 之后、`## 3.` 之前） | INSERT | 新增 ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42 |
| EDIT-ARCH-08 | architecture_design.md | §8 架构假设表 A11 行后 | INSERT | 新增 `[ARCH-ASSUMPTION-A12]`（Key 未配置态 + 库文件权限）|
| EDIT-ARCH-09 | architecture_design.md | §9 TBD 表 T25 行后 | INSERT | 新增 `[TBD-T26]` / `[TBD-T27]` |
| EDIT-ARCH-10 | architecture_design.md | §10.1（REV-17 OPEN ITEM 行之后） | INSERT | 新增 REV-18 OPEN ITEM 行（OI-1 / OI-2 / OI-3） |
| EDIT-ARCH-11 | architecture_design.md | §10.2 末 / §10.3 末 | INSERT | §10.2 追加「（REV-18）许可面未变」句；§10.3 追加 REV-18 自检块（含生产重启由用户执行登记）|

---

# Part A — `docs/architecture_design.md` 增量

> 目标文档当前状态：v1.9.0 / REV-17（末条 ADR-36）。以下 EDIT 按编号升序落盘。

---

## ■ EDIT-ARCH-01 — `file_header` 版本 / 修订号 / 调用号

**位置**：文档最前端 `file_header` 内（第 6~11 行区域）。

**ANCHOR（old_string）**：
```
  <version>1.9.0</version>
  <revision>REV-17</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_03 系统架构设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-011</invocation_id>
```

**REPLACE（new_string）**：
```
  <version>1.10.0</version>
  <revision>REV-18</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_03 系统架构设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
```

---

## ■ EDIT-ARCH-02 — `file_header/inputs` 输入指针同步

**位置**：`file_header/inputs` 第 15~16 行。

**ANCHOR（old_string）**：
```
    <input path="docs/requirements_spec.md" version="1.7.0" revision="REV-16-3" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.8.0" revision="REV-16-4" status="APPROVED"/>
```

**REPLACE（new_string）**：
```
    <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
```

---

## ■ EDIT-ARCH-03 — `file_header/revision_history` 追加 REV-18 条目

**位置**：`file_header/revision_history` 内，**REV-17 条目之后、`</revision_history>` 之前**。

**ANCHOR（插入点边界，逐字）**：
```
FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
  </revision_history>
```

**INSERT（在 `"/>` 与 `</revision_history>` 之间插入新行）**：
```
    <rev version="1.10.0" revision="REV-18" date="2026-10-07" invocation_id="INV-GROUP_B-INTELBASE-012" basis="用户裁决（2026-10-07，REV-18-2）：OQ-IB-25 ~ OQ-IB-31 七条一次性拍板并登记 DR-21（Key 存 DB + 重启生效 / Key 全局唯一 / 删项目=软删停用 / 账号沿用现状 / 禁删 admin 与最后管理员 + 二次确认 / kb 由项目推导 / 父级「系统管理」+三子项）；上游 requirements_spec.md 1.10.0（REV-18-2）/ user_stories.md 1.10.0（REV-18-2）" note="REV-18 下游贯通（系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）：① 新增 **ADR-37**（项目注册表承载与软删语义）、**ADR-38**（LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析）、**ADR-39**（LLM 未配置态启动 / 运行期语义，破除首启死锁）、**ADR-40**（运维账号 CRUD 扩展 / 顺序依赖 / 删除保护）、**ADR-41**（项目域 `kb_id` 推导 + 保留归属断言 + kb_default 迁移）、**ADR-42**（系统管理三分 IA + 服务端授权与导航解耦）；每条含 Context（REQ 引用）/ Options（≥2，含已评估未采纳）/ Decision / Status / Consequences；**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：32 条不受影响、3 条口径补注（ADR-08 / 18 / 28）、1 条待裁决口径张力（ADR-21，登记 OPEN ITEM）、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 追加 R18 增补段与 2 行；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**、§9 新增 **[TBD-T26] / [TBD-T27]**、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）、§10.2 追加「许可面未变」句、§10.3 追加 R18 自检；⑥ 落点并入既有模块（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。不变约束：模块数 26、端口 17 → 19（纯追加）、`IFC-IB-001 ~ 365` 号 / 名 / 签名一字不动（仅 4 条文字口径修订，登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增边）**、DAG 无环、**不引运行期热重载**（ADR-32 / C-IB-40 / OOS-16）。**登记：生产后端重启与首次环境变量配置须由用户执行**（架构 / 部署文档只写「由用户执行」的动作）。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / 密钥字面量。"/>
```

---

## ■ EDIT-ARCH-04 — 顶部修订摘要区追加「（REV-18）」块 + 版次行

**位置**：顶部「**（REV-17）提示词兜底层重定位增量**…」段落之后、「**R1 修订摘要**」之前；版次行在标题下第一行。

**REPLACE-1（版次行）**：

**ANCHOR（old_string）**：
```
**版本**: 1.9.0（REV-17 增量）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-07
```

**REPLACE（new_string）**：
```
**版本**: 1.10.0（REV-18 增量）| **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-07
```

**INSERT-2（修订摘要块）**：

**ANCHOR（插入点边界，逐字）**：以下两行连续出现，新块插在二者之间：
```
**R1 修订摘要**: 后端 Web 框架 **FastAPI → Django（+ DRF）**（用户明确指定，非建议）；流式载体改为 **Django 同步视图 + `StreamingHttpResponse` 原生 SSE**（**不引 Channels、不引 Redis**）；受影响 ADR **5 条**（ADR-03 / 07 / 08 / 11 / 13），其中 **ADR-11 全文重写（ADR-11-R1）**，逐条复核见 §2.0；模块数 / 端口数 / IFC-IB 编号 / 覆盖矩阵**均未变**（改动仅载体说明）。
```

**INSERT（在该行**之前**插入）**：
```

**（REV-18）系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量**（用户裁决 2026-10-07，REV-18-2；上游 `requirements_spec.md` v1.10.0 / REV-18-2）：① 新增 **ADR-37 ~ ADR-42**（项目注册表承载与软删 / LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析 / LLM 未配置态启动与运行期语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 服务端授权与导航解耦），**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：**不受影响 32 条**、**口径补注 3 条**（ADR-08 Key 取值来源 / ADR-18 复用载体与迁移机制 / ADR-28 项目列表数据源）、**待裁决口径张力 1 条**（ADR-21，登记 OPEN ITEM OI-1，**不自行改写**）、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 增 2 行 + R18 增补段；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**；§9 新增 **[TBD-T26] / [TBD-T27]**；§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）；§10.2 追加「许可面未变」句；§10.3 追加 R18 自检；⑥ **落点并入既有模块**（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、生效口径（ADR-32 / C-IB-40 / OOS-16）**未改**、`tech_stack.md`（见 Part C：登记型口径修订，无新第三方依赖）。**登记**：**生产后端重启与首次环境变量配置须由用户执行**；`IB_DEFAULT_ADMIN_PASSWORD` 等既有凭据键纪律不变，**LLM Key 不入 `.env`**（载体内 DB，库文件 0600 且属主对齐服务账号）。
```

> 说明：`INSERT` 块以**空行开头**，使 `**（REV-18）…**` 段与上方 REV-17 段分隔。落盘后，顶部摘要区的段序为：REV-17 → **（REV-18）** → R1。

---

## ■ EDIT-ARCH-05 — §1.3 可替换点表新增 2 行 + R18 增补段

**位置**：§1.3 表格末行（`| 配置审计（**REV-16-4 新增**） … |`）之后。

**ANCHOR（old_string，表末行，逐字）**：
```
| 配置审计（**REV-16-4 新增**） | `ConfigAuditStore`（IFC-IB-357） | `SqliteConfigAuditStore`（同一 SQLite 台账；**只读审计，append-only**） | 新增适配器（如接 DB / 日志中心，上层零改动） | REQ-NFR-IB-19 / IB-06；AC-IB-32-02 |
```

**REPLACE（new_string，表末行 + 2 新行）**：
```
| 配置审计（**REV-16-4 新增**） | `ConfigAuditStore`（IFC-IB-357） | `SqliteConfigAuditStore`（同一 SQLite 台账；**只读审计，append-only**） | 新增适配器（如接 DB / 日志中心，上层零改动） | REQ-NFR-IB-19 / IB-06；AC-IB-32-02 |
| 项目注册表（**REV-18 新增**） | `ProjectRegistryStore`（IFC-IB-367） | `SqliteProjectRegistryStore`（**同一 SQLite 台账**；手写迁移 `005_projects.sql`；**软删 = 状态列**） | 新增适配器（如接 DB / 配置中心，上层零改动） | REQ-FUNC-IB-44 / IB-45；ADR-37；REQ-NFR-IB-11 |
| LLM Key 载体（**REV-18 新增**） | `LlmKeyStore`（IFC-IB-368） | `SqliteLlmKeyStore`（**同一 SQLite 台账**；手写迁移 `006_llm_key.sql`；**单行表，全局唯一**） | 新增适配器（如接密钥管理服务，上层零改动） | REQ-FUNC-IB-47；REQ-NFR-IB-20；C-IB-42；ADR-38；REQ-NFR-IB-11 |
```

**INSERT-2（R18 增补段）**：

**ANCHOR（插入点边界，逐字，为 §1.3 最后一段的末句）**：
```
③ **两个持久化载体并存**（定义文档 + 提示词目录）**不构成重叠第二真源**（真源按域唯一）；**禁止**将任一域的内容重复写入另一域。
```

**INSERT（在该行**之后**插入）**：
```

**（REV-18）项目注册表与 LLM Key 载体的可替换点显式化**：① **项目注册表**经**第 18 个端口** `ProjectRegistryStore`（IFC-IB-367）抽象 —— 项目管理（CRUD + 软删 / 停用）从「配置枚举（`IB_CONFIG_FILE` 的 `projects.<id>`，装配期 `_seed_projects` 只读快照）」升格为「**运行期可变状态的唯一载体**」；`GET /api/projects`（IFC-IB-333）**数据源切换**为注册表（**端点号 / 名 / 签名与 fail-closed 语义一字不动**，登记型口径修订）；换为 DB / 配置中心时**上层零改动**（REQ-NFR-IB-11；ADR-37）。② **LLM Key 载体**经**第 19 个端口** `LlmKeyStore`（IFC-IB-368）抽象 —— **单一全局 Key**（单行表，以**结构**保证唯一，OOS-18 为扩展点预留）；装配期由组合根经 `resolve_secret()` 读取（**唯一读点**）；HTTP 层只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`）—— **不回显明文为类型层事实**（响应类型无明文字段；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**，避免长度 / 前缀侧信道）；承载**库文件 0600 且属主对齐服务账号**（ADR-38 / REQ-NFR-IB-20）。③ **`.env` 仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**（登记型口径修订；见 ADR-38 Consequences 与 `tech_stack.md` Part C）。④ **生效口径不变**：Key / 项目 / 账号的**保存与变更一律经「保存 + 服务重启重装配」生效**（ADR-32 / C-IB-40 / OOS-16），**不引运行期热重载**；**重启由用户手工执行**。
```

---

## ■ EDIT-ARCH-06 — 新增 §2.0.9 REV-18 影响复核表

**位置**：§2.0.8 的「R17 被修订 IFC 逐条登记…」段落之后、`### ADR-01 向量库抽象层…` 之前。

**ANCHOR（插入点边界，逐字；为 §2.0.8 末尾段落）**：
```
**R17 被修订 IFC 逐条登记**（**只改文字 / 取值口径，不改号 / 名 / 签名**）：`IFC-IB-212`（`build_expert` 补 keyword-only `system_prompt`；消解假陈述 docstring）、`IFC-IB-287`（`ExpertSpecInput` 去 `fallback_prompt` 字段）、`IFC-IB-290`（定义域校验项 5 只留 `cn_label`；白名单去该键）、`IFC-IB-292`（`_semantic_payload` 去该键 → 一次性内容哈希变更）、`IFC-IB-338`（`resolved_from` 第三值更名）、`IFC-IB-339`（`load_bundle` 形参改名）、`IFC-IB-343`（`merge_prompt_layers` 第三分支 + 形参改名）、`IFC-IB-345`（`validate_prompt_directory` 缺兜底判据收窄）、`IFC-IB-347`（`derive_prompt_layers` 形参改名）、`IFC-IB-355`（`validate_definition_full` 被更上层合成入口包含，**自身不变**）。**新增**：`IFC-IB-364`（`validate_two_domains`）、`IFC-IB-365`（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `builtin_fallback_for` / `builtin_fallbacks_for`）。
```

**INSERT（在该段**之后**插入）**：
```

### 2.0.9 REV-18 影响复核表（系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量）

> **背景**：`requirements_spec.md` v1.10.0 / **REV-18-2**（APPROVED）新增 REQ-FUNC-IB-43 ~ IB-48、REQ-NFR-IB-20、C-IB-42 / C-IB-43、OOS-17 ~ OOS-19、DR-20 / DR-21，并就 OQ-IB-25 ~ OQ-IB-31 七条一次拍板。本节对 v1.9.0 的 **36 条 ADR（ADR-01 ~ ADR-36）逐条复核**并登记新增 6 条，作为「设计未因需求增量而漂移」的可审计证据。**无一条跳过**。

| ADR | 结论 | 说明 |
|-----|------|------|
| ADR-01 ~ ADR-13 | **不受影响** | 向量库 / embedding / 解析 / OCR / 渲染 / 台账 / Blob / 会话 / 鉴权 / 配置 / 检索契约均未动（含 ADR-03 部署拓扑、ADR-04 项目 / 知识库隔离与 collection 解析、ADR-05 原始文件、ADR-06 解析、ADR-07 台账、ADR-09 依赖反转、ADR-10 租约、ADR-11 流式、ADR-12 CPU 适配、ADR-13 边界校验）。**注**：**ADR-08（LLM 端点抽象与数据外发边界）决策未动** —— Key 的**取值来源**改由 **DB 装配期解析**（ADR-38），属**口径补注**；ADR-08 的端口边界 / 供应商可配 / 外发声明结论**一字未动** |
| ADR-14（可视化编辑模型） | **不受影响** | 「显式 round-trip + 视图零持久化 + 白名单制」纪律未动 |
| ADR-15 / ADR-15-R1 / ADR-15-R2（真源边界） | **不受影响** | 真源分域（定义文档 = 结构 / 配置域；提示词目录 = 提示词域）一字未动；REV-18 **不触**提示词文本载体 |
| ADR-16（装配期 fail-fast 闸门） | **不受影响，且 REV-18 复用其机制** | 闸门与 `ValidationReport`（不含 `force` / `ignore` / `warn_only`）未动；REV-18 的新增装配（注册表装载与幂等播种 / Key 解析 / 账号存在性前置）沿用「任一步失败即拒绝装配」纪律 |
| ADR-17（确认中间态） | **不受影响** | 承载方式与状态丢失语义未动 |
| ADR-18（账户 / 会话落点与载体） | **不受影响，且 REV-18 复用其载体与迁移机制** | 「**同一 SQLite 台账 + 手写 scoped 迁移 + WAL + `busy_timeout`**」未动；项目注册表（`005_projects.sql`）与 LLM Key 表（`006_llm_key.sql`）**复用**该载体与迁移机制（ADR-37 / ADR-38） |
| ADR-19（不透明服务端会话令牌） | **不受影响** | 无 Cookie、只存摘要、仅 `Authorization` 头、`?token=` 一律 4xx 未动；REV-18 的新端点沿用该纪律 |
| ADR-20（bcrypt 口令存储与首登强制改密） | **不受影响** | 口令哈希与受限会话未动；REV-18 的账号编辑 / 删除**不新增口令回显路径** |
| **ADR-21（账户↔项目绑定）** | **待裁决（口径张力）** | R13 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。二者**是否冲突取决于 ADR-21 的 1:1 语义**（「每账号恰绑一项目」→ **不冲突**；「每项目至多一账号」→ **冲突**）。**架构侧不自行改写 ADR-21**，登记为 **OPEN ITEM OI-1**（§10.1）；若判定需修订，另出 **ADR-21-R1**。**本包未改动任何既有 REQ 文本** |
| ADR-22（单一授权真源） | **不受影响，且 REV-18 是其应用** | 授权判定仍只经注入的 `AuthzPolicy`；**ADR-42 明令**「**UI 分组不作为权限机制**、非 admin 一律**服务端 403**」——即 REV-18 复用 ADR-22 纪律 |
| ADR-23（前端路由与守卫） | **不受影响** | `vue-router`（hash）与鉴权守卫未动；REV-18 的「系统管理父级导航」为**路由树内新增节点**，不引入 nginx `try_files` 回退 |
| ADR-24（粘贴令牌入口废除） | **不受影响** | 无旁路未动 |
| ADR-25（HTTPS 落点） | **不受影响** | TLS 终止与证书策略未动 |
| ADR-26（迁移 / 种子 / 回滚） | **不受影响，且 REV-18 是其应用** | 手写 scoped 迁移纪律未动；REV-18 新增迁移 `005` / `006` 走**同一机制**（前向、幂等；新表为**纯追加**，回滚 = 代码回滚） |
| ADR-27（登录限速与审计，条件性） | **不受影响** | 条件性未动；REV-18 不把项目 / Key 变更纳入限速面 |
| **ADR-28（项目上下文选择与传播）** | **不受影响；口径补注** | 显式选择 + 显式传播（`X-IB-Project`）+ fail-closed 语义**一字不动**；**仅** `GET /api/projects`（IFC-IB-333）的**数据源**由「配置枚举 `Deps.projects`」改为「**项目注册表**」（ADR-37）—— 登记型口径修订，**端点号 / 名 / 签名不变** |
| ADR-29（提示词主 / 兜底分层） | **不受影响** | 分层与回退方向未动 |
| ADR-30（工具授权与参数） | **不受影响** | 勾选 + 参数可配、不新增工具本体未动 |
| ADR-31（FreeArk 严格对齐） | **不受影响** | 10 维对齐与工具参数排除项未动；FreeArk 全程只读 |
| ADR-32（配置生效口径） | **不受影响，且 REV-18 沿用其生效口径** | 「**保存 + 服务重启重装配**」**一字未动**；REV-18 的 Key / 项目 / 账号变更**一律按 ADR-32 生效**（**不引热重载**，OOS-16 维持）；**重启由用户手工执行** |
| ADR-33（保存期单校验入口） | **不受影响** | `validate_two_domains`（IFC-IB-364）与其等价性未动；REV-18 不触定义域 / 工具域 / 提示词域校验 |
| ADR-34（配置审计） | **不受影响** | 只读审计 / 非第二真源未动；REV-18 **不**把项目 / Key / 账号变更写入 `config_audit`（顶层键集与审计面均不变） |
| ADR-35（内存态提示暴露） | **不受影响** | `GET /api/config/storage-state` 与 `StorageState` 未动 |
| ADR-36（提示词兜底层重定位） | **不受影响** | 文件两层 + 代码内置安全网未动 |
| **ADR-37 ~ ADR-42** | **新增** | 项目注册表承载与软删 / LLM Key 凭据载体 = DB + 装配期解析 / LLM 未配置态语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 授权与导航解耦；每条含 Context（REQ 引用）/ Options（≥2）/ Decision / Status / Consequences |

**R18 复核小结**：既有 **36 条 ADR 全部已复核**（**不受影响 32 条**；**口径补注 3 条**：ADR-08 / ADR-18 / ADR-28；**待裁决 1 条**：ADR-21，登记 OPEN ITEM OI-1）；**新增 6 条** → ADR 总数 **36 → 42**。**无一条跳过**。R18 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 365` 编号 / 名 / 签名（文字性修订见下方清单）；**端口 17 → 19（纯追加）**；新增 IFC 为 **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）。

**R18 被修订 IFC 逐条登记**（**只改文字与取值口径，不改号 / 名 / 签名**）：`IFC-IB-024`（`LlmConfig.api_key_env` **语义降级**为「历史 / 兼容登记」——LLM Key 来源改由 DB 装配期解析，ADR-38 / ADR-39）、`IFC-IB-262` / `IFC-IB-263`（凭据纪律由「**一律经环境变量注入**」收窄为「**除外 LLM Key**：LLM Key 经 DB；其余密钥仍经环境变量」；启动校验口径改为「**LLM Key 未配置非致命**（fail-closed 于调用期）」，其余必填项仍 fail-fast）、`IFC-IB-321`（账户端点族**补齐** `PATCH /api/accounts/{user_id}` / `DELETE /api/accounts/{user_id}`（软删 + 二次确认 + 禁删 admin 与最后管理员）；`POST /api/accounts` **增前置**：目标 `project_id` 须在注册表存在且 `active`；**号 / 名 / 既有方法签名不变**）、`IFC-IB-333`（`GET /api/projects` **数据源**由配置枚举改为项目注册表；**号 / 名 / 签名不变**）。**新增**：`IFC-IB-366`（`update_user`，**加成式扩展** `AccountStore`，其既有 13 方法文本不改）、`IFC-IB-367`（端口 `ProjectRegistryStore` + 结构）、`IFC-IB-368`（端口 `LlmKeyStore` + `LlmKeyStatus`）、`IFC-IB-369`（REV-18 键名登记与启动校验口径）、`IFC-IB-370` / `IFC-IB-371`（SQL 适配器与 DDL 单源 `005` / `006`）、`IFC-IB-372 ~ IFC-IB-375`（项目 CRUD / 账号扩展 / LLM Key 端点 / 项目域上传与装配期解析）、`IFC-IB-376`（前端系统管理 IA）、`IFC-IB-377`（部署检查清单 B21 ~ B23）。

---
```

> 说明：`INSERT` 块以**空行开头**并以 `---` 结尾，使 §2.0.9 与 `### ADR-01` 之间保留既有空行分隔。

---

## ■ EDIT-ARCH-07 — §2 末尾新增 ADR-37 ~ ADR-42

**位置**：§2 末（ADR-36 小节之后、`## 3. 多项目隔离…` 之前）。

**ANCHOR（插入点边界，逐字）**：
```
## 3. 多项目隔离：链路落点与跨项目泄漏失败模式
```

**INSERT（在该行**之前**插入）**：
```
### ADR-37 项目注册表的承载、落点与软删语义

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-44（项目管理：项目 CRUD + 项目注册表）、REQ-FUNC-IB-45（**先建项目、后建账号**的顺序依赖 → 「项目存在」成为可校验事实）；OQ-IB-27（用户裁决 2026-10-07：**引入项目注册表承载运行期可变状态**，**删项目 = 软删 / 停用**，物理级联删除移出 = OOS-19）、OQ-IB-29（删除须二次确认）、DR-21。**现状**：`GET /api/projects`（IFC-IB-333）的数据源是组合根 `Deps.projects`（由 `IB_CONFIG_FILE` 的 `projects.<project_id>` 经 `_seed_projects` 装配的**只读快照**）——**无法承载运行期 CRUD**。
- **Options**:
  - **Option A 仅回写配置文件（`IB_CONFIG_FILE`）**：优—零新表，复用 `DefinitionDocumentStore` 式「先写临时文件、再原子替换」纪律。缺—（1）把**运行期可变状态**与「**配置 = 装配期只读输入**」混淆；（2）写文件与装配期读存在并发竞争与半写风险；（3）**与 OQ-IB-27 裁决不符**（用户明确要求「引入注册表承载运行期可变状态」）。**（已评估未采纳）**
  - **Option B 引入项目注册表（SQLite 新表 + 手写迁移 + 独立端口）** ← **选定**：优—与既有 `LedgerRepository` / `AccountStore` / `ConfigAuditStore` **同库同机制**（ADR-07 / ADR-18 / ADR-26 复用）；软删 = 状态列；与裁决一致；上层（检索 / 台账 / 定义文档）**零改动**（项目标识仍是字符串）。缺—新增第 18 个端口与一张表；`Deps.projects` 语义由「配置快照」变为「注册表读出的活动项目」。
  - **Option C 独立轻量文件注册表（JSON 状态文件）**：优—不触库。缺—与既有「**同一 SQLite 台账 + 手写 scoped 迁移**」纪律**分叉**，净增**第二持久化机制**；并发 / 事务语义弱于 SQLite。**（已评估未采纳）**
- **Decision**: **Option B**。① 引入**第 18 个端口** `ProjectRegistryStore`（IFC-IB-367，定义于 **MOD-IB-01** 零依赖层：`ProjectRegistryEntry` / `ProjectStatus` 结构 + 端口方法集）+ **SQLite 适配器** `SqliteProjectRegistryStore`（**MOD-IB-11**，**DDL 单源 = 手写迁移 `005_projects.sql`**）+ `MemoryProjectRegistryStore` 替身。② `GET /api/projects`（IFC-IB-333）**数据源切换**为注册表（**登记型口径修订**：端点号 / 名 / 签名与 fail-closed 语义**一字不动**）。③ **装配期幂等首次播种**：以 `IB_CONFIG_FILE.projects.<id>` 为**初始数据**（沿用 `_seed_projects` 语义；离线取 memory 替身；`INSERT … ON CONFLICT DO NOTHING` 语义，**不覆盖既有注册表行**）。④ **软删 / 停用**：`DELETE /api/projects/{project_id}` = `status="disabled"`（**数据保留、可恢复**），**不做物理级联删除**（OOS-19）；删除须**二次确认**（确认值 = 目标 `project_id`，不一致即 `400`）。⑤ **零新增模块、零新增依赖边**（复用既有边 `23 → 01 / 11`）。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-44 / IB-45；复用同库迁移纪律（ADR-18 / ADR-26）；软删使误删可恢复（OQ-IB-29）；上层零改动（项目标识仍为字符串，`Scope` 契约不动）。
  - 负向：新增第 18 个端口与一张表 + **一处 `GET /api/projects` 数据源口径修订**（登记于 §2.0.9）；`Deps.projects` 由「配置快照」变为「注册表读出的活动项目」，**既有基于配置快照的离线用例须相应调整**（属施工期影响，非契约变更）；注册表规模 / 查询开销待实测（**[TBD-T26]**）。

### ADR-38 LLM Key 的持久化载体（DB）、凭据纪律与装配期解析

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-47（LLM Key 管理：增 / 改 / 删）、REQ-NFR-IB-20（Key 存储与呈现纪律：载体 = 数据库；库文件 0600 且属主对齐服务账号；`.env` 仅保留非 LLM Key 的其他密钥；5 判据）、C-IB-42（LLM Key 凭据纪律，载体 = DB）；OQ-IB-25（用户裁决 2026-10-07：Key 存 **DB**；生效 = 保存 + 服务重启重装配；**非 `.env`**）、OQ-IB-26（**Key 全局唯一一个**；项目级 / 每项目 / 多供应商 = 移出 = OOS-18）、DR-21。**现状**：`LlmConfig.api_key_env`（默认 `IB_LLM_API_KEY`）+ 启动校验要求存在，否则 `StartupError`。
- **Options**:
  - **Option A 界面写回 0600 `.env`**（原草拟推荐路径）：优—零新表，复用环境变量纪律。缺—**与用户裁决不符**（OQ-IB-25 明确否决）；运行期写凭据文件 + 与 systemd `EnvironmentFile` 语义冲突；写回后**仍须重启**（与 Option B 同等）。**（已评估未采纳）**
  - **Option B 界面写 DB 表（装配期读取）** ← **选定**：优—裁决选定；**不落 `.env`**；权限可 0600 + 属主对齐；与既有 SQLite 同库同迁移机制；明文**不回显**可做成类型层事实。缺—新增第 19 个端口与一张表；凭据载体由「环境变量」改为「DB」→ 须登记修订 `tech_stack.md` 凭据纪律与「配置载体」行（Part C）。
  - **Option C 保持仅环境变量（现状）**：优—零改动。缺—与「**界面管理 Key**」的 REQ-FUNC-IB-47 直接冲突。**（已评估未采纳）**
- **Decision**: **Option B**。① 引入**第 19 个端口** `LlmKeyStore`（IFC-IB-368，定义于 **MOD-IB-01**：`LlmKeyStatus` 结构 + 端口方法集）+ **SQLite 适配器** `SqliteLlmKeyStore`（**MOD-IB-11**，**DDL 单源 = 手写迁移 `006_llm_key.sql`**，**单行表** `llm_key(id=1, secret, updated_at)`）+ `MemoryLlmKeyStore` 替身。② **全局唯一一个 Key** —— 以**单行表结构**保证（OOS-18 为扩展点预留，**不**做项目级 / 多供应商）。③ **装配期由组合根经 `resolve_secret()` 读取（唯一读点）**；HTTP 层只暴露 `LlmKeyStatus`（`configured: bool` / `masked: str` / `updated_at: str | None`）—— **不回显明文为类型层事实**（响应类型无明文字段）；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道；口径见 §10.1 OI-3）。④ **唯一写入口** = `PUT /api/llm-key`；删除 = `DELETE /api/llm-key`（清空单行）。⑤ **承载库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；部署检查清单 B22）；`.env` 仅保留非 LLM Key 的其他密钥。⑥ **生效口径 = 保存 + 服务重启重装配**（**ADR-32 不变**；**不引热重载**，OOS-16 维持）；重启**由用户手工执行**。⑦ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-47 / REQ-NFR-IB-20 / C-IB-42；Key **不入 `.env` / 不进 git / 不进命令行或 shell history**（唯一写入口为管理端点）；同库同迁移；明文不回显为结构事实。
  - 负向：新增第 19 个端口与一张表；**凭据载体由环境变量改为 DB** → 须修订 `tech_stack.md` 的 `<credential_policy>` 与 §1「配置载体」行（**登记型口径修订，无新第三方依赖**，见 Part C）；库文件权限与属主须真机实测（**[TBD-T27]**）；`api_key_env` 字段语义降级须登记（IFC-IB-024，见 §2.0.9）。

### ADR-39 LLM 未配置态的启动与运行期语义（破除首启死锁）

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-47（Key 经**管理界面**增 / 改 / 删）、REQ-NFR-IB-20、ADR-38（Key 载体 = DB）。**派生事实**：若沿用既有「装配期缺 `IB_LLM_API_KEY` 即 `StartupError`」，则**首启 DB 无 Key → 服务不启动 → 管理界面不可达 → 无法写入首个 Key**，构成**死锁**（Key 的唯一写入口是管理端点）。**本 ADR 决策的是「未配置态」的语义**，非任何业务数值。
- **Options**:
  - **Option A 保持 fail-fast（缺 Key 即 `StartupError`）**：优—fail-fast 一致。缺—**首启死锁**（见 Context）；对「先部署、后配 Key」的常见序不友好。**（已评估未采纳）**
  - **Option B 保持 fail-fast + 部署期预置种子 Key（手工写库 / CLI）**：优—保留 fail-fast。缺—预置步骤须「**由用户执行**」（C-IB-38 口径）；引入**第二条写 Key 通道**（与「唯一写入口 = 管理端点」张力）；且对纯界面管理诉求不友好。**（已评估未采纳）**
  - **Option C 放宽为「未配置态」（fail-closed 于调用期）** ← **选定**：装配期 Key 解析结果三态 `configured` / `unconfigured`；`unconfigured` 时**服务正常启动**，LLM 依赖路径 **fail-closed**（调用期以可读、**不含任何 Key 信息**的错误拒绝），管理端点与健康端点**始终可达**。
- **Decision**: **Option C**。① 装配期 Key 解析结果 `configured` / `unconfigured`；**缺 Key 不再致命**（**仅** LLM Key 放宽，**其余必填项仍 fail-fast**）。② `unconfigured` 时：`GET /api/llm-key` → `configured=false`；**LLM 依赖路径**（问答 / 路由 LLM 档 / 聚合）以 `DependencyUnavailableError`-类可读错误 **fail-closed** —— **不得**回落到「无 Key 静默出空答案」。③ 启动日志与 `/healthz/deps` 的 `llm` 字段**显式声明 LLM 未配置**（**不含任何 Key 值**）。④ 配置成功后**仍须服务重启重装配方生效**（ADR-32）。⑤ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：破除首启死锁；满足 REQ-FUNC-IB-47 的界面可达性；fail-closed 不静默（对齐 ADR-13「故障与空结果可区分」精神）。
  - 负向：**局部放宽**了既有「缺 Key 即启动失败」的 fail-fast（**注**：其余必填配置的 fail-fast **不变**）；须登记 OPEN ITEM **OI-2**（首启序：部署 → 登录 → 设 Key → **由用户手工重启**）；若 PM / 用户不采纳 Option C，则须以 Option B 的**用户手工预置**替代（二选一，架构层不自行拍板）。

### ADR-40 运维账号 CRUD 扩展、顺序依赖与删除保护

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-45（**先建项目、后建账号**→创建账号须校验项目存在；OQ-IB-28 裁决 1:N、**零迁移**）、REQ-FUNC-IB-46（账号**查看 / 编辑 / 删除**）、REQ-FUNC-IB-31（既有创建 / 查看 / 停用，**正文不改**）；OQ-IB-28（**零迁移**：**不**加 `users.project_id` 唯一约束）、OQ-IB-29（**禁删 `admin` 与最后一个有效 `admin`**；删除须**二次确认**；**优先软删**）、OOS-19（物理级联删除移出）。
- **Options**:
  - **Option A 硬删除账号（`DELETE` 真删行）**：优—语义直白。缺—不可恢复，**与 OQ-IB-29「软删优先」不符**；且会随账号消失丢失审计线索。**（已评估未采纳）**
  - **Option B 软删 / 停用（复用既有 `AccountStatus="disabled"`）+ 删除保护 + 二次确认** ← **选定**：优—**复用既有 `set_status`**（IFC-IB-310，方法集**不变**）、**零迁移**（无新列，符合 OQ-IB-28）；`disabled` 已表达「不可登录」。缺—「最后管理员」判定须读 `list_users`（规模小，可接受）。
  - **Option C 新增独立 `deleted_at` 列（真软删时间戳）**：优—可区分「停用」与「删除」。缺—需迁移，**触碰 OQ-IB-28 的「零迁移」裁决**；`disabled` 已足够表达「不可登录」。**（已评估未采纳）**
- **Decision**: **Option B**。① **新增端点**（并入 **MOD-IB-23**）：`PATCH /api/accounts/{user_id}`（编辑：`project_id` 重绑 / `username` / `status`；**不回显任何凭据**）、`DELETE /api/accounts/{user_id}`（软删 = 置 `disabled`；**二次确认** `confirm_username` 与目标 `username` 一致否则 `400`；**禁止删除 `admin` 或最后一个有效 `admin`** → `409`）。② **创建账号的顺序依赖**：`POST /api/accounts` **增前置校验** —— 目标 `project_id` 须在**项目注册表**（ADR-37）存在且为 `active`，否则 `422` / `400` 可读错误（**不静默创建无主账号**）。③ **1:N 零迁移**：**不**加 `users.project_id` 唯一约束；REQ-FUNC-IB-31 正文不改（**注**：与 ADR-21 的 1:1 表述存在**口径张力**，登记为 OPEN ITEM **OI-1**，**本 ADR 不自行改写 ADR-21**）。④ **删除账号不随项目级联**（软删项目亦不删除其账号，保留可恢复）。⑤ `AccountStore` 端口**方法集不变**（软删复用 `set_status`；编辑经 IFC-IB-366 `update_user` —— **加成式扩展**，其既有 13 方法文本不改）；**「最后管理员」判定在服务层**（非端口层）。⑥ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-45 / IB-46；**零迁移**（OQ-IB-28）；复用既有 `status` 与 `AccountStore`；删除保护与二次确认降低误操作风险。
  - 负向：新增 2 个端点与 1 个端口方法（`update_user`，**加成式扩展**）；「最后管理员」判定引入一次 `list_users` 读（规模小）；`PATCH` 编辑须**严格不回显口令 / 令牌**（沿用 IFC-IB-321 / IFC-IB-324 纪律）。

### ADR-41 项目域资料的 `kb_id` 推导、归属断言保留与 `kb_default` 迁移

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-48（**项目域文件上传取代「知识库标识」输入**）；C-IB-43（「取代知识库标识」**必须不破坏架构红线 `docs/architecture_design.md:120`**；REV-18-2：**`kb_id ≡ project_id`**，**请求体不再接收 kb 字段**，**保留** `assert_kb_in_project`）；OQ-IB-30（用户裁决 2026-10-07：**项目级单 DB**；`kb_id` **由已认证主体的 `project_id` 推导**；请求体不再接收 kb 字段；既有 `kb_default` 数据**迁移到归属项目 KB**；**保留** `assert_kb_in_project`，失败 `403`）；DR-21。
- **Options**:
  - **Option A 由客户端继续提交 `kb` 字段，服务端仅断言归属（现状 + 断言）**：优—改动最小。缺—**违反 C-IB-43 / OQ-IB-30**（请求体**不应**再接收 kb 字段）；客户端仍可自证范围，与 §1.4 第 2 条「**范围不可由客户端自证**」精神存在张力；「知识库标识」输入框须**移除**（REQ-FUNC-IB-48）。
  - **Option B `kb_id` 由已认证主体的 `project_id` 推导（`kb_id ≡ project_id`），请求体不再接收 kb 字段，且**保留** `assert_kb_in_project`** ← **选定**：优—**范围只能来自服务端结论**（对齐 §1.4 第 2 条与 ADR-04 / ADR-28 约束③）；请求体**收缩**；**红线 120 的归属断言仍生效**（防回归）。缺—既有 `kb_default` 数据须**一次性迁移**到归属项目 KB；上传 / 列表端点的请求体形状变化（属施工期影响）。
  - **Option C 由客户端提交并**直接**作为 `kb_id`（不做推导、不做断言）**：优—零改动。缺—**直接违反红线 `architecture_design.md:120`**（「范围不可由客户端自证」）与 C-IB-43。**（已评估未采纳）**
- **Decision**: **Option B**。① HTTP 层**由已认证主体解析 `project_id`**，**据此推导** `kb_id`（`kb_id ≡ project_id`）；**请求体不再接收 `kb` 字段**（既有字段**移除**）。② **保留** `LedgerRepository.assert_kb_in_project(project_id, kb_id)`（IFC-IB-130）**归属断言**；失败仍 `403`（**非 404**，避免存在性探测）—— **红线 `architecture_design.md:120` 不被破坏**（这是 C-IB-43 的硬要求）。③ **`kb_default` 数据迁移**：既有落在 `kb_default` 的行**迁移到归属项目 KB**（一次性迁移，随迁移家族交付；幂等、前向）。④ 上传 / 列表 / 删除端点（IFC-IB-242 / 243 / 244）**请求体形状收缩**（去掉 kb 字段）—— **登记型口径修订**（号 / 名 / 签名不变），见 §2.0.9 与 `module_design.md` §2.2.9。⑤ 零新增模块、零新增依赖边。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-48 / C-IB-43 / OQ-IB-30；**范围只认服务端结论**（红线 120 加固而非削弱）；请求体收缩、界面简化（移除「知识库标识」输入）。
  - 负向：`kb_default` 一次性**数据迁移**（须幂等、可前向；回滚 = 代码回滚 + 数据保留）；上传 / 列表端点的**既有请求体契约形状变化**（须在 `requirements_spec.md` 侧同步口径 —— **本包不改需求文档**，登记为交付说明）；**保留** `assert_kb_in_project` 使「客户端自证」在结构上不可绕过。

### ADR-42 系统管理三分的信息架构与服务端授权解耦

- **Status**: Accepted
- **Context**: REQ-FUNC-IB-43（**系统管理**三分：账户管理 / 项目管理 / LLM Key 管理）；OQ-IB-31（用户裁决 2026-10-07：父级「**系统管理**」含**三子项**；既有账户管理**移入**；**资料管理**仍为独立顶级，视图改为**项目域**；**UI 分组不得视为权限机制** —— 非 admin 一律**服务端 403**）；REQ-NFR-IB-09 / IB-16；ADR-22（单一授权真源）。
- **Options**:
  - **Option A 三分项各自为顶级导航项（不设父级）**：优—改动最小。缺—**与 OQ-IB-31 裁决不符**（裁决要求父级「系统管理」+ 三子项）。**（已评估未采纳）**
  - **Option B 父级「系统管理」下挂三子项（账户管理 / 项目管理 / LLM Key 管理），资料管理独立顶级且视图改为项目域** ← **选定**：优—符合裁决；导航分组清晰；**授权仍只经服务端 `AuthzPolicy`**（UI 分组**不作为**权限机制）。缺—路由树新增父级节点；既有账户管理页**迁移**到子项（须处理既有路由 / 深链）。
  - **Option C 以 UI 分组**兼任**权限边界（仅 admin 可见 / 可操作）**：优—体验直观。缺—**违反 ADR-22 单一授权真源**与「**UI 分组不得视为权限机制**」裁决；前端可见性可被绕过，**服务端必须**仍 `403`。**（已评估未采纳）**
- **Decision**: **Option B**。① **信息架构**：父级「**系统管理**」含三子项（**账户管理** / **项目管理** / **LLM Key 管理**）；**资料管理**保持**独立顶级**，其视图由「知识库」改为「**项目域**」（对齐 ADR-41）。② **授权与导航解耦（强制）**：UI 分组的可见性 / 可点性**仅为体验优化**；**授权判定唯一经服务端**（注入的 `AuthzPolicy`，ADR-22）；**非 admin 一律服务端 `403`** —— 「UI 分组不是权限机制」为**架构层事实**，不得以导航隐藏替代服务端拒绝。③ 前端路由：`vue-router`（hash）**新增父级节点**，既有账户管理路由**迁移**（保留 hash，不引入 `try_files`）。④ 落点并入 **MOD-IB-24**（前端 IA）；**零新增模块、零新增依赖边**。
- **Consequences**:
  - 正向：满足 REQ-FUNC-IB-43 / OQ-IB-31；导航分组与授权解耦，**不产生第二授权真源**（ADR-22 复用）；资料管理视图与 ADR-41 的项目域口径一致。
  - 负向：既有账户管理页的**路由 / 深链迁移**（施工期影响）；**前端改密态与权限可见性仅为体验优化**的口径须在 UI 文案与测试中显式（服务端为唯一裁决者）。

```

> 说明：`INSERT` 块以**空行开头**，使 ADR-42 末尾与 `## 3.` 之间保留空行分隔。

---

## ■ EDIT-ARCH-08 — §8 架构假设新增 `[ARCH-ASSUMPTION-A12]`

**位置**：§8 表格末行（`| **ARCH-ASSUMPTION-A11** … |`）之后。

**ANCHOR（old_string，A11 行，逐字）**：
```
| **ARCH-ASSUMPTION-A11**（REV-16-4 新增） | **配置审计记录的保留策略（容量上界 / 轮转 / 清理）在 v1 未定**：`config_audit` 表**只增不删**（append-only），具体保留时长 / 条数上界 / 归档方式**由部署阶段标定** | REQ-NFR-IB-19 / AC-IB-32-02 只要求「存在可查询的记录」，**未规定保留策略**；需求侧无对应 REQ | 若需限额：新增一个清理任务即可（**上层零改动**）；若需长期留存：换/接外部存储只替换 `ConfigAuditStore` 适配器（IFC-IB-357） | **需 PM 知悉**（保留策略；架构层不自行拍板数值；与 [TBD-T25] 同源） |
```

**REPLACE（new_string，A11 行 + A12 行）**：
```
| **ARCH-ASSUMPTION-A11**（REV-16-4 新增） | **配置审计记录的保留策略（容量上界 / 轮转 / 清理）在 v1 未定**：`config_audit` 表**只增不删**（append-only），具体保留时长 / 条数上界 / 归档方式**由部署阶段标定** | REQ-NFR-IB-19 / AC-IB-32-02 只要求「存在可查询的记录」，**未规定保留策略**；需求侧无对应 REQ | 若需限额：新增一个清理任务即可（**上层零改动**）；若需长期留存：换/接外部存储只替换 `ConfigAuditStore` 适配器（IFC-IB-357） | **需 PM 知悉**（保留策略；架构层不自行拍板数值；与 [TBD-T25] 同源） |
| **ARCH-ASSUMPTION-A12**（REV-18 新增） | **LLM Key「未配置态」的启动语义 + 承载库文件权限口径**（架构侧取值）：① 装配期 Key 解析结果 `configured` / `unconfigured`；**`unconfigured` 非致命**（服务正常启动；LLM 依赖路径 **fail-closed** 于调用期；`GET /api/llm-key` 返 `configured=false`）—— 见 **ADR-39**；② Key **承载库文件权限 0600 且属主对齐服务账号**（REQ-NFR-IB-20；部署检查清单 B22）；③ **掩码口径** = **不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道）。**唯一写入口** = `PUT /api/llm-key`；**生效 = 保存 + 服务重启重装配**（ADR-32），**重启由用户手工执行** | REQ-FUNC-IB-47 / REQ-NFR-IB-20 规定「界面管理 Key」「载体 = DB」「库文件 0600」与「只回掩码 / 存在性 / 更新时间」，但**未规定首启缺 Key 的启动语义**（否则构成首启死锁，见 OI-2），亦未逐字规定掩码字面 | 若 PM / 用户不采纳「未配置态」，须以「部署期**由用户手工预置** Key」替代（ADR-39 Option B）；若判定「缺 Key 即启动失败」为硬约束，须回 GROUP_A 立项（架构层**不发明需求**）；掩码字面与库文件属主由施工期 / 部署期定 | **需 PM 知悉**（与 [TBD-T27] 同源；OI-2 / OI-3） |
```

---

## ■ EDIT-ARCH-09 — §9 TBD 清单新增 `[TBD-T26]` / `[TBD-T27]`

**位置**：§9 表格末行（`| **TBD-T25（REV-16-4 新增）** … |`）之后。

**ANCHOR（old_string，T25 行，逐字）**：
```
| **TBD-T25（REV-16-4 新增）** | **配置审计表增长与查询开销**：`config_audit` 在目标规模的**行数增长曲线 / 单文件体积**，`GET /api/config/audit`（IFC-IB-359）与 `GET /api/config/storage-state`（IFC-IB-362）的响应耗时，及「审计写失败」实际发生率 | REQ-NFR-IB-19；REQ-NFR-IB-06；AC-IB-32-02；ADR-34 / ADR-35；[ARCH-ASSUMPTION-A11] | 定保留 / 轮转策略与是否需要归档；量化「保存成功但记录缺失」窗口。**未经实测前不得给出容量 / 时延结论** |
```

**REPLACE（new_string，T25 行 + T26 / T27 行）**：
```
| **TBD-T25（REV-16-4 新增）** | **配置审计表增长与查询开销**：`config_audit` 在目标规模的**行数增长曲线 / 单文件体积**，`GET /api/config/audit`（IFC-IB-359）与 `GET /api/config/storage-state`（IFC-IB-362）的响应耗时，及「审计写失败」实际发生率 | REQ-NFR-IB-19；REQ-NFR-IB-06；AC-IB-32-02；ADR-34 / ADR-35；[ARCH-ASSUMPTION-A11] | 定保留 / 轮转策略与是否需要归档；量化「保存成功但记录缺失」窗口。**未经实测前不得给出容量 / 时延结论** |
| **TBD-T26（REV-18 新增）** | **项目注册表的规模与查询开销**：`projects` 表在目标规模的**行数上界 / 单文件体积增量**，`GET /api/projects`（IFC-IB-333）与项目 CRUD 端点的响应耗时，及**装配期幂等首次播种**（以 `IB_CONFIG_FILE.projects.<id>` 为初始数据）的耗时 | REQ-FUNC-IB-44 / IB-45；REQ-NFR-IB-11；ADR-37 | 定注册表是否需要索引 / 分页；量化 `Deps.projects` 由「配置快照」变为「注册表读出」后的装配期增量。**未经实测前不得给出容量 / 时延结论** |
| **TBD-T27（REV-18 新增）** | **LLM Key 承载库文件的实际权限与属主**：库文件（含 `llm_key` 表的 SQLite 文件）在目标机的**实际 mode（须 0600）与 owner（须对齐服务账号）**、`busy_timeout` 下的写入耗时，以及 `SqliteLlmKeyStore` 的读写争用；另含 **AVX2 / SIGILL 与本轮无涉的确认**（本轮**未**引入任何新 wheel） | REQ-NFR-IB-20；REQ-FUNC-IB-47；C-IB-42；ADR-38 / ADR-39；[ARCH-ASSUMPTION-A12] | 定库文件权限 / 属主的**真机验证**口径（部署检查清单 B22）；确认「Key 不入 `.env` / 不进 git / 不进命令行」的端到端可复查证据。**未经实测前不得给出权限 / 时延结论** |
```

---

## ■ EDIT-ARCH-10 — §10.1 新增 REV-18 OPEN ITEM 行

**位置**：§10.1 表格末行（`| **（REV-17）`general` / 无专家路径的人格串不可配置** … |`）之后。

**ANCHOR（old_string，REV-17 行，逐字）**：
```
| **（REV-17）`general` / 无专家路径的人格串不可配置** | 落定 ADR-36 的 system 位通道时暴露的**既有不对称事实**：专家路径的 system 提示词由**两域合并**派生（可配置，ADR-29 / ADR-36），而 **`general`（无专家 / 聚合）路径**的 system 是 `build_aggregator()` 内的**硬编码串**，**不经**提示词目录、**不可配置** | 保持现状：**本 ADR 不顺手扩围** —— `general` 路径压根不走 `_run_expert`（走 `build_aggregator()`），其可配置化属**新能力**（须新增 REQ / AC 与提示词层级定义），不在 REV-17 的收窄范围内 | **登记为 OPEN ITEM，待用户 / PM 裁决**；若要求 `general` 人格可配，须回 GROUP_A 立项（**架构层不发明需求、不新增 AC、不自行扩围**） |
```

**REPLACE（new_string，REV-17 行 + 3 个 REV-18 行）**：
```
| **（REV-17）`general` / 无专家路径的人格串不可配置** | 落定 ADR-36 的 system 位通道时暴露的**既有不对称事实**：专家路径的 system 提示词由**两域合并**派生（可配置，ADR-29 / ADR-36），而 **`general`（无专家 / 聚合）路径**的 system 是 `build_aggregator()` 内的**硬编码串**，**不经**提示词目录、**不可配置** | 保持现状：**本 ADR 不顺手扩围** —— `general` 路径压根不走 `_run_expert`（走 `build_aggregator()`），其可配置化属**新能力**（须新增 REQ / AC 与提示词层级定义），不在 REV-17 的收窄范围内 | **登记为 OPEN ITEM，待用户 / PM 裁决**；若要求 `general` 人格可配，须回 GROUP_A 立项（**架构层不发明需求、不新增 AC、不自行扩围**） |
| **（REV-18）OI-1：ADR-21「账户↔项目 1:1」与 OQ-IB-28「1:N」的口径张力** | R13 ADR-21 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。二者**是否冲突取决于 ADR-21 的 1:1 语义**（「每账号恰绑一项目」→ **不冲突**；「每项目至多一账号」→ **冲突**） | **不自行改写 ADR-21**，沿用既有 `UserRecord.project_id`（单值）与 `AccountStore` 方法集（**13 方法一字不动**）；ADR-40 已按「**1:N、零迁移**」落地（**不**加唯一约束） | **登记为 OPEN ITEM，待用户 / PM 裁决**；若判定需修订，架构侧另出 **ADR-21-R1**（amend 子节）；若判定「1:1」为硬约束，须回 GROUP_A 立项（架构层**不发明需求**）。**本包未改动任何既有 REQ 文本** |
| **（REV-18）OI-2：LLM Key 首启的供给序（派生后果）** | 用户裁决 Key 存 **DB**、`.env` 仅保留非 LLM Key 的其他密钥（OQ-IB-25 / REQ-NFR-IB-20）；既有装配在「缺 `IB_LLM_API_KEY`」时 `StartupError` → **首启死锁**（DB 无 Key ⇒ 服务不启动 ⇒ 管理界面不可达 ⇒ 无法写入首个 Key） | 架构侧按**派生必要性**给出 **ADR-39 Option C**（放宽为「未配置态」：服务可启动；LLM 依赖路径 **fail-closed**；管理端点始终可达）；**未发明任何业务数值** | **登记为 OPEN ITEM，待用户 / PM 裁决**；若不采纳 Option C，须以 **ADR-39 Option B**（部署期**由用户手工预置** Key）替代；二选一由 PM / 用户定，架构层**不自行拍板** |
| **（REV-18）OI-3：LLM Key 掩码口径** | REQ-FUNC-IB-47 约束①要求「只回掩码 / 存在性与更新时间」 | 架构侧将 `LlmKeyStatus.masked` 定为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道），并**以类型层排除明文**（响应类型无明文字段）；具体掩码字面由施工期定，**本包不写死** | **登记为待知悉**（口径已收敛到「无明文可分」）；如需指定掩码字面，由用户在施工期给定 |
```

---

## ■ EDIT-ARCH-11 — §10.2 末追加「许可面未变」句 + §10.3 末追加 REV-18 自检块

**REPLACE-1（§10.2 末句）**：

**位置**：§10.2 末尾（紧接「完整选型与风险表见 `tech_stack.md`。」之前的「（REV-16-4）许可面未变…」段之后）；本 EDIT 在「完整选型与风险表见 `tech_stack.md`。」**之前**插入一段。

**ANCHOR（old_string，逐字）**：
```
**（REV-16-4）许可面未变**：本增量**未引入任何第三方组件** —— 配置审计落点复用**同一 SQLite**（stdlib `sqlite3`）与既有手写迁移机制（`003_accounts.sql` → `004_config_audit.sql`）；其余新增均为 frozen dataclass / Protocol / 纯 stdlib。故本节许可台账**不变**（`tech_stack.md` 记 **NO_CHANGE**）。

完整选型与风险表见 `tech_stack.md`。
```

**REPLACE（new_string）**：
```
**（REV-16-4）许可面未变**：本增量**未引入任何第三方组件** —— 配置审计落点复用**同一 SQLite**（stdlib `sqlite3`）与既有手写迁移机制（`003_accounts.sql` → `004_config_audit.sql`）；其余新增均为 frozen dataclass / Protocol / 纯 stdlib。故本节许可台账**不变**（`tech_stack.md` 记 **NO_CHANGE**）。

**（REV-18）许可面未变**：本增量**未引入任何第三方组件** —— 项目注册表与 LLM Key 载体均复用**同一 SQLite**（stdlib `sqlite3`）与既有手写 scoped 迁移机制（新增迁移 `005_projects.sql` / `006_llm_key.sql`）；其余新增均为 frozen dataclass / Protocol / 纯 stdlib。故本节许可台账**不变**（`tech_stack.md` 为**登记型口径修订**——凭据载体说明由「一律经环境变量」收窄为「**除外 LLM Key**」，**无新第三方依赖**，见 Part C）。

完整选型与风险表见 `tech_stack.md`。
```

**REPLACE-2（§10.3 末追加）**：

**位置**：§10.3 末尾（REV-17 自检块的最后一行之后，文档末尾）。

**ANCHOR（old_string，逐字，REV-17 自检末行）**：
```
- **（REV-17）凭据与仓库纪律**：全文**只登记键名 / 头名 / 表名 / 文件层名**；提示词正文与定义文档**不回显任何凭据值**；令牌仅经 `Authorization` 头，`?token=` 纪律对全部既有端点有效；**未写入任何口令 / 令牌 / 密钥字面量**；`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档**只读未改**（落盘载体措辞的同步**另立交付项**）；本阶段**止于 GROUP_B**。
```

**REPLACE（new_string，REV-17 末行 + REV-18 自检块）**：
```
- **（REV-17）凭据与仓库纪律**：全文**只登记键名 / 头名 / 表名 / 文件层名**；提示词正文与定义文档**不回显任何凭据值**；令牌仅经 `Authorization` 头，`?token=` 纪律对全部既有端点有效；**未写入任何口令 / 令牌 / 密钥字面量**；`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档**只读未改**（落盘载体措辞的同步**另立交付项**）；本阶段**止于 GROUP_B**。
- **（REV-18）系统管理 / 项目 / LLM Key / 项目域资料增量已贯通**：新增 **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42**（每条含 Context（**REQ 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 全部已复核**：不受影响 **32**、口径补注 **3**（ADR-08 / 18 / 28）、待裁决 **1**（ADR-21，登记 OPEN ITEM OI-1）、**新增 6**、**无一条跳过**）；新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368）；新增 IFC **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）；§1.3 追加 R18 增补段与 2 行、§8 新增 [ARCH-ASSUMPTION-A12]、§9 新增 [TBD-T26] / [TBD-T27]、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）、§10.2 追加「许可面未变」句。
- **（REV-18）不变约束未被破坏**：模块数仍 **26**（**未新增模块**）、端口 17 → **19**（**纯追加**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9：`IFC-IB-024` / `262` / `263` / `321` / `333`）、**§4.1 依赖边逐行不变（零新增依赖边）**、依赖图**仍为 DAG**（再声明见 `module_design.md` §4.2.8）；REQ→MOD 覆盖 **48/48 REQ-FUNC（由 42 同步）+ 20 NFR（由 19 同步）**。
- **（REV-18）红线未被破坏（强制）**：REQ-FUNC-IB-48 / C-IB-43 的「**取代知识库标识**」**未**削弱 `architecture_design.md:120`（「**范围不可由客户端自证**」）—— `kb_id` **由已认证主体的 `project_id` 推导**，**请求体不再接收 kb 字段**，且**保留** `LedgerRepository.assert_kb_in_project`（IFC-IB-130）归属断言，失败仍 **403**（非 404）。**「UI 分组不是权限机制」**：ADR-42 明令非 admin 一律**服务端 403**（授权唯一经注入的 `AuthzPolicy`，ADR-22 复用）。
- **（REV-18）凭据纪律（新增口径）**：① LLM Key **载体 = DB**（**不入 `.env`**、**不进 git**、**不进命令行 / shell history**）；**唯一写入口** = `PUT /api/llm-key`；HTTP 只回 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），**不回显明文为类型层事实**；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**；承载**库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；[ARCH-ASSUMPTION-A12]；检查清单 B22）。② `.env` **仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**（登记型口径修订，`IFC-IB-024` / `262` / `263`）。③ 全文**只登记键名 / 头名 / 表名 / 字段名 / 文件名**；**未写入任何口令 / 令牌 / Key / 证书字面量**；令牌仅经 `Authorization` 头，`?token=` 纪律对**全部新端点**有效（`/api/projects*`、`/api/accounts*`、`/api/llm-key`）。
- **（REV-18）生效口径与运维动作（登记，不自动执行）**：Key / 项目 / 账号的保存与变更**一律经「保存 + 服务重启重装配」生效**（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载、**不重编译编排图**；**登记：生产后端重启与首次环境变量配置须由用户执行** —— 架构 / 部署文档只写「由用户执行」的动作，**不设计为代理自动执行**。
- **（REV-18）OQ / OPEN ITEM 未越权**：**ADR-21 的 1:1 口径张力（OI-1）**、**LLM Key 首启供给序（OI-2）**、**掩码字面（OI-3）** 均**登记为 OPEN ITEM**，待用户 / PM 裁决；架构层**不自行改写 ADR-21、不自行拍板业务数值、不新增 REQ、不改 AC**。
- **（REV-18）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` v1.10.0 / `user_stories.md` v1.10.0）**只读未改**；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **仅登记型口径修订**（凭据载体说明收窄，**无新第三方依赖**，见 Part C）；本阶段**止于 GROUP_B**。
```

---

**Part A 结束。** 继续见 `docs/rev18_groupb_apply_package_part2.md`（Part B：`module_design.md` 增量）。
