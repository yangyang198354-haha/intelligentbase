# REV-18 收口 Apply Package — GR-B 三项待决裁决落档（OI-1 / OI-2 / OI-3）

- **produced_by**: system-architect（GROUP_B / PHASE_03）
- **produced_at**: 2026-10-07
- **basis**: 用户裁决（2026-10-07）就 GR-B 三项待决（OI-1 / OI-2 / OI-3）收口；沿用 ADR-15-R1 / ADR-15-R2 的 amend 子节先例
- **target documents（仅此二文件）**:
  - `docs/architecture_design.md`（当前 `<version>1.10.0</version>` / `<revision>REV-18</revision>`）
  - `docs/module_design.md`（当前 `<version>1.10.0</version>` / `<revision>REV-18</revision>`）
- **NOT touched（强制）**: `src/**`、`tests/**`、`requirements_spec.md`、`user_stories.md`、`implementation_plan.md`、`tech_stack.md`（本轮无须改动）；**不进入 GROUP_C 实现**。

---

## 0. 使用说明（PM 落盘前必读）

1. 每条 EDIT 严格为 **ANCHOR（逐字原样，取自目标文档当前内容）→ REPLACE（逐字新样）**；**ANCHOR 均为目标文档中唯一可匹配的子串 / 整行**（已逐条验重）。
2. 落盘方式：在目标文件中定位 ANCHOR 的**唯一匹配**，以 REPLACE **整段替换**该匹配。
3. **行尾约定**：ANCHOR 文本按 `LF` 书写；目标文件若为 `CRLF`，请以「忽略行尾差异」的方式匹配（内容字节一致即可）。
4. **ADR-21 正文不得改动**：EDIT-AR-01 的 ANCHOR 位于 ADR-21 正文（`**ADR-21: 账户↔项目绑定与角色模型**` 段）**末尾之后**的插入点，且 REPLACE 完整保留原 ANCHOR 行；PM 可对本包做**逐字 / hash 强校验**：ADR-21 段（`- **Status**: Accepted` 至 `  - 负向: 1:1 为硬约束 …` 及其上方 `**ADR-21: …**` 行）在落盘前后**必须逐字不变**。
5. **凭据纪律**：本包**只登记键名 / 表名 / 文件名 / 字段名**，**不含任何口令 / 令牌 / Key / 证书字面量**。
6. 落盘建议标签：`[必落]` = 用户裁决直接要求；`[全文复核]` = 由「全文复核所有引用该计数 / OI 之处」推导出的同步；`[供裁量]` = 为消除同文档内 OI 状态自相矛盾而建议，用户裁决未逐字点名，**PM 可裁量跳过**。

---

## 1. EDIT 清单总览

| EDIT | 目标文件 | 位置（行号，落盘前） | 对应裁决 | 落盘建议 |
|------|----------|----------------------|----------|----------|
| EDIT-AR-01 | architecture_design.md | ADR-21 正文后（L847 后） | A | [必落] |
| EDIT-AR-02 | architecture_design.md | §2.0.9 表 ADR-21 行（L364） | B | [必落] |
| EDIT-AR-03 | architecture_design.md | §2.0.9 R18 复核小结（L382） | B | [必落] |
| EDIT-AR-04 | architecture_design.md | §10.1 OI-1 行（L1392） | C | [必落] |
| EDIT-AR-05 | architecture_design.md | §10.1 OI-2 行（L1393） | C | [必落] |
| EDIT-AR-06 | architecture_design.md | §10.1 OI-3 行（L1394） | C | [必落] |
| EDIT-AR-07 | architecture_design.md | ADR-39 Consequences 负向（L1106） | D | [必落] |
| EDIT-AR-08 | architecture_design.md | §10.3 REV-18 OQ/OPEN ITEM 行（L1495） | E | [必落] |
| EDIT-AR-09 | architecture_design.md | §10.3 REV-18 增量条目（L1490） | B | [全文复核] |
| EDIT-MD-01 | module_design.md | §9.11 OQ/OPEN ITEM 处置（L1534） | F | [必落] |
| EDIT-MD-02 | module_design.md | §11 REV-18 自检 OQ/OPEN ITEM（L1656） | F | [必落] |
| EDIT-AR-10 | architecture_design.md | 头部 REV-18 修订摘要（L50） | B·全文复核 | [全文复核] |
| EDIT-AR-11 | architecture_design.md | ADR-40 Decision ③（L1116） | 一致性 | [供裁量] |
| EDIT-AR-12 | architecture_design.md | [ARCH-ASSUMPTION-A12] 行（L1332） | 一致性 | [供裁量] |
| EDIT-MD-03 | module_design.md | §3 IFC-IB-373 说明（L885） | 一致性 | [供裁量] |
| EDIT-AR-V1/V2 | architecture_design.md | 头部版本号 + revision_history | G（条件） | [供裁量] |
| EDIT-MD-V1/V2 | module_design.md | 头部版本号 + revision_history | G（条件） | [供裁量] |

---

## 2. [必落] 裁决 A–F 直接要求

### EDIT-AR-01 · 裁决 A — 新增 ADR-21-R1（amend 子节）

**目标**：`docs/architecture_design.md`，插入点 = ADR-21 正文末尾（`- **Consequences**:` 之 `负向` 行）之后、紧接着的 `---` 之前；**ADR-21 正文一字不动**（ANCHOR 行在 REPLACE 中完整保留）。

**ANCHOR（逐字原样，整行）**：

```text
  - 负向: 1:1 为硬约束 → 一个运维账户无法跨项目；若用户改判为 1:N 须回 GROUP_A（超本轮范围）。
```

**REPLACE（逐字新样）**：

```text
  - 负向: 1:1 为硬约束 → 一个运维账户无法跨项目；若用户改判为 1:N 须回 GROUP_A（超本轮范围）。

### ADR-21-R1 账户↔项目绑定关系式的收窄：N:1（REV-18 修订子节）

- **Status**: Accepted（REV-18 修订；**本子节为对 ADR-21 的正式修订子节（amend）**，ADR-21 的 ID / Status / Context / Options / Decision / Consequences **一字不动**；本子节**收窄并订正** ADR-21 中「账户↔项目 1:1 绑定」的**关系式歧义**为 **N:1**，ADR-21 的**授权落点与端口结论全部不变**）
- **Context**: 用户裁决（2026-10-07）就 **OI-1**（本文件 §10.1）作出裁定：ADR-21 的「账户↔项目绑定」关系式明确为 **N:1**。关系方既有依据：**DR-15**（一运维账户绑定一个项目）、**OQ-IB-28**（REV-18 裁决：**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**）、**ADR-21**（R13，账户↔项目绑定与角色模型）。**语义裁定**：ADR-21 的「1:1」**以「每账号恰绑一项目」为唯一合法读法** —— 它与 OQ-IB-28 的「1:N」为**同一关系的两侧读法**（账号侧 N → 项目侧 1；反向 1 → N），据此排除「每项目至多一账号」（与 OQ-IB-28 冲突）的歧义读法。既有落点：ADR-40（R18 已按 1:N、零迁移落地，**不**加唯一约束）、`AccountStore`（IFC-IB-310，13 方法一字不动）、`UserRecord.project_id`（单值、可空）。
- **Options**:
  - **Option A（不改 ADR-21，仅在口头 / 单测注释里说明「1:1」读作「每账号恰绑一项目」）**：优—零改动、零迁移。缺—**歧义仍在**：「1:1」在对称语境下可被合法读为「每项目至多一账号」，与 OQ-IB-28 的 1:N 直接冲突；下游（测试门控 / 施工 / 检查清单）须各自解释，口径**不可审计 / 不可回溯**。**已评估未采纳**。
  - **Option B（出 ADR-21-R1 amend 子节，把关系式显式收窄 / 订正为 N:1）** ← **选定**：**ADR-21 正文一字不动**（沿用 ADR-15-R1 / ADR-15-R2 的 amend 先例，**不 supersede**），修订落在本子节；关系式固化为「**每个运维账号恰绑一个项目（N 账号 → 1 项目）；一个项目可有多个运维账号**」。优—歧义被**结构性消除**且**有唯一落点**（可回溯 OQ-IB-28 / DR-15 / ADR-21）；**与既有无 `users.project_id` 唯一约束一致**，**零迁移**；ADR-21 的授权结论（Option A：`AuthzContext(actor_id, project_id, roles)`；admin `project_id=None` 全局）与端口边界**不变**。缺—ADR-21 正文的字面「1:1」仍在，引用该处者须一并标注 **ADR-21-R1**。
  - **Option C（改写 ADR-21 正文，把「1:1」字面直接替换为「N:1」）**：优—字面一致、无二次引用。缺—**违反「编号只增不改」纪律**（ADR-21 为已 Accepted 正文；改写会使 REV-13 的历史留痕失真），且 ADR-15-R1 / ADR-15-R2 已确立「正文一字不动 + amend 子节」先例。**已评估未采纳**。
- **Decision**: **Option B**。**固化后的关系式（N:1）**：**每个运维账号恰绑定一个项目（N 个账号 → 1 个项目）；一个项目可有多个运维账号**。① **数据落点不变**：`UserRecord.project_id`（单值、可空；admin 为 `None`）；**不新增**任何唯一约束（OQ-IB-28「零迁移」）。② **授权落点不变**：仍**只**经 `AuthzContext(actor_id, project_id, roles)` 表达（ADR-21 Option A）；运维账号 `roles=("manager",)`、边界由 `project_id` 强制；admin `project_id=None` 全局。③ **端口不变**：`AccountStore`（IFC-IB-310）方法集一字不动；账号创建的顺序依赖前置校验（目标 `project_id` 须在注册表存在且 `active`，ADR-40 / REQ-FUNC-IB-45）不变。④ **零迁移**：无 DDL 变更、无数据回填。
- **Consequences**:
  - 正向: 「账户↔项目」口径**唯一且可回溯**（本子节 → OQ-IB-28 / DR-15 / ADR-21）；**ADR-21 正文一字不动**（amend 而非 supersede，REV-13 历史留痕完整）；**与既有无 `users.project_id` 唯一约束一致、零迁移**；下游「1:1」引用可统一回链本子节，消除测试门控 / 施工各自解释的风险。
  - 负向: **ADR-21 正文仍保留「1:1」字面**，凡引用该处者**须一并标注 ADR-21-R1**（否则仍可能被误读为「每项目至多一账号」）；本子节为**收窄 / 订正**而非推翻，故**不新增**任何 IFC / 端点 / 迁移足迹。
```

> **排版依据**：与 ADR-15 ↔ ADR-15-R1 的相对位置一致（正文块 … 空行 … `### ADR-15-R1 …`），本子节置于 ADR-21 正文块之后、其后既有 `---` 之前。

---

### EDIT-AR-02 · 裁决 B — §2.0.9 影响复核表 ADR-21 行

**目标**：`docs/architecture_design.md` §2.0.9 表内 ADR-21 行（L364）。

**ANCHOR（逐字原样，整行）**：

```text
| **ADR-21（账户↔项目绑定）** | **待裁决（口径张力）** | R13 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。二者**是否冲突取决于 ADR-21 的 1:1 语义**（「每账号恰绑一项目」→ **不冲突**；「每项目至多一账号」→ **冲突**）。**架构侧不自行改写 ADR-21**，登记为 **OPEN ITEM OI-1**（§10.1）；若判定需修订，另出 **ADR-21-R1**。**本包未改动任何既有 REQ 文本** |
```

**REPLACE（逐字新样）**：

```text
| **ADR-21（账户↔项目绑定）** | **口径补注（已由 ADR-21-R1 承接）** | R13 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。**用户裁决（2026-10-07）已关口径张力**：关系式**收窄 / 订正为 N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），由新增修订子节 **ADR-21-R1** 承接（**ADR-21 正文一字不动**，amend）。ADR-21 的**授权结论 / 端口边界不变**；**零迁移**（不加唯一约束）。**本包未改动任何既有 REQ 文本** |
```

---

### EDIT-AR-03 · 裁决 B — §2.0.9 结论计数（R18 复核小结）

**目标**：`docs/architecture_design.md` §2.0.9 标题下小结句（L382）。

**ANCHOR（逐字原样，整行）**：

```text
**R18 复核小结**：既有 **36 条 ADR 全部已复核**（**不受影响 32 条**；**口径补注 3 条**：ADR-08 / ADR-18 / ADR-28；**待裁决 1 条**：ADR-21，登记 OPEN ITEM OI-1）；**新增 6 条** → ADR 总数 **36 → 42**。**无一条跳过**。R18 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 365` 编号 / 名 / 签名（文字性修订见下方清单）；**端口 17 → 19（纯追加）**；新增 IFC 为 **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）。
```

**REPLACE（逐字新样）**：

```text
**R18 复核小结**：既有 **36 条 ADR 全部已复核**（**不受影响 32 条**；**口径补注 4 条**：ADR-08 / ADR-18 / ADR-28 / **ADR-21**（由新增修订子节 **ADR-21-R1** 承接，其口径张力经**用户裁决 2026-10-07 关闭**）；**待裁决 0 条**）；**新增 6 条** → ADR 总数 **36 → 42**。**无一条跳过**。R18 **不触及**：模块数（26，未新增）、**§4.1 依赖边（零新增边）**、DAG 无环性、既有 `IFC-IB-001 ~ 365` 编号 / 名 / 签名（文字性修订见下方清单）；**端口 17 → 19（纯追加）**；新增 IFC 为 **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）。
```

---

### EDIT-AR-04 · 裁决 C — §10.1 OI-1 行 → CLOSED

**目标**：`docs/architecture_design.md` §10.1（L1392）。

**ANCHOR（逐字原样，整行）**：

```text
| **（REV-18）OI-1：ADR-21「账户↔项目 1:1」与 OQ-IB-28「1:N」的口径张力** | R13 ADR-21 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」。二者**是否冲突取决于 ADR-21 的 1:1 语义**（「每账号恰绑一项目」→ **不冲突**；「每项目至多一账号」→ **冲突**） | **不自行改写 ADR-21**，沿用既有 `UserRecord.project_id`（单值）与 `AccountStore` 方法集（**13 方法一字不动**）；ADR-40 已按「**1:N、零迁移**」落地（**不**加唯一约束） | **登记为 OPEN ITEM，待用户 / PM 裁决**；若判定需修订，架构侧另出 **ADR-21-R1**（amend 子节）；若判定「1:1」为硬约束，须回 GROUP_A 立项（架构层**不发明需求**）。**本包未改动任何既有 REQ 文本** |
```

**REPLACE（逐字新样）**：

```text
| **（REV-18）OI-1：ADR-21「账户↔项目 1:1」与 OQ-IB-28「1:N」的口径张力** | R13 ADR-21 文本含「账户↔项目 **1:1** 绑定」；REV-18 **OQ-IB-28** 裁决为「**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**」 | **用户裁决（2026-10-07）**：关系式明确为 **N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），**由新增修订子节 ADR-21-R1 承接**（**ADR-21 正文一字不动**，amend）；沿用既有 `UserRecord.project_id`（单值）与 `AccountStore` 方法集（**13 方法一字不动**）；ADR-40 已按「**1:N、零迁移**」落地（**不**加唯一约束） | **CLOSED（用户裁决 2026-10-07）** —— 经 **ADR-21-R1** 承接并关闭；**本包未改动任何既有 REQ 文本** |
```

---

### EDIT-AR-05 · 裁决 C — §10.1 OI-2 行 → CLOSED（采纳 ADR-39 Option C）

**目标**：`docs/architecture_design.md` §10.1（L1393）。

**ANCHOR（逐字原样，整行）**：

```text
| **（REV-18）OI-2：LLM Key 首启的供给序（派生后果）** | 用户裁决 Key 存 **DB**、`.env` 仅保留非 LLM Key 的其他密钥（OQ-IB-25 / REQ-NFR-IB-20）；既有装配在「缺 `IB_LLM_API_KEY`」时 `StartupError` → **首启死锁**（DB 无 Key ⇒ 服务不启动 ⇒ 管理界面不可达 ⇒ 无法写入首个 Key） | 架构侧按**派生必要性**给出 **ADR-39 Option C**（放宽为「未配置态」：服务可启动；LLM 依赖路径 **fail-closed**；管理端点始终可达）；**未发明任何业务数值** | **登记为 OPEN ITEM，待用户 / PM 裁决**；若不采纳 Option C，须以 **ADR-39 Option B**（部署期**由用户手工预置** Key）替代；二选一由 PM / 用户定，架构层**不自行拍板** |
```

**REPLACE（逐字新样）**：

```text
| **（REV-18）OI-2：LLM Key 首启的供给序（派生后果）** | 用户裁决 Key 存 **DB**、`.env` 仅保留非 LLM Key 的其他密钥（OQ-IB-25 / REQ-NFR-IB-20）；既有装配在「缺 `IB_LLM_API_KEY`」时 `StartupError` → **首启死锁**（DB 无 Key ⇒ 服务不启动 ⇒ 管理界面不可达 ⇒ 无法写入首个 Key） | **用户裁决（2026-10-07）采纳 ADR-39 Option C**：**缺 Key 非致命**，服务正常启动、LLM 依赖路径 **fail-closed 于调用期**（可读错误、不含任何 Key 信息），管理端点与健康端点始终可达；**其余必填项仍 fail-fast**；**备选 Option B（部署期用户手工预置 Key）不采纳**（见 ADR-39 Consequences 补记） | **CLOSED（用户裁决 2026-10-07）** —— 采纳 **ADR-39 Option C**；Option B **已评估未采纳** |
```

---

### EDIT-AR-06 · 裁决 C — §10.1 OI-3 行 → 保持 OPEN

**目标**：`docs/architecture_design.md` §10.1（L1394）。

**ANCHOR（逐字原样，整行）**：

```text
| **（REV-18）OI-3：LLM Key 掩码口径** | REQ-FUNC-IB-47 约束①要求「只回掩码 / 存在性与更新时间」 | 架构侧将 `LlmKeyStatus.masked` 定为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道），并**以类型层排除明文**（响应类型无明文字段）；具体掩码字面由施工期定，**本包不写死** | **登记为待知悉**（口径已收敛到「无明文可分」）；如需指定掩码字面，由用户在施工期给定 |
```

**REPLACE（逐字新样）**：

```text
| **（REV-18）OI-3：LLM Key 掩码口径** | REQ-FUNC-IB-47 约束①要求「只回掩码 / 存在性与更新时间」 | 架构侧将 `LlmKeyStatus.masked` 定为**不含明文任何前 / 后缀字符的固定占位掩码**（避免长度 / 前缀侧信道），并**以类型层排除明文**（响应类型无明文字段）；具体掩码字面由施工期定，**本包不写死** | **保持 OPEN（施工期定，不阻塞）**：口径已收敛到「无明文可分」；具体掩码字面由用户在施工期指定（**架构层不发明**） |
```

---

### EDIT-AR-07 · 裁决 D — ADR-39 Consequences 补一句

**目标**：`docs/architecture_design.md` ADR-39 `Consequences` 的 `负向` 行（L1106）。**只追加一句**，不改既有文字。

**ANCHOR（逐字原样，整行）**：

```text
  - 负向：**局部放宽**了既有「缺 Key 即启动失败」的 fail-fast（**注**：其余必填配置的 fail-fast **不变**）；须登记 OPEN ITEM **OI-2**（首启序：部署 → 登录 → 设 Key → **由用户手工重启**）；若 PM / 用户不采纳 Option C，则须以 Option B 的**用户手工预置**替代（二选一，架构层不自行拍板）。
```

**REPLACE（逐字新样）**：

```text
  - 负向：**局部放宽**了既有「缺 Key 即启动失败」的 fail-fast（**注**：其余必填配置的 fail-fast **不变**）；须登记 OPEN ITEM **OI-2**（首启序：部署 → 登录 → 设 Key → **由用户手工重启**）；若 PM / 用户不采纳 Option C，则须以 Option B 的**用户手工预置**替代（二选一，架构层不自行拍板）。**REV-18 裁决补记（用户裁决 2026-10-07）**：备选 **Option B（部署期由用户手工预置 Key）已评估未采纳**；**用户已裁决采纳 Option C**（缺 Key 非致命、fail-closed 于调用期，其余必填仍 fail-fast）—— OI-2 据此**关闭**（见 §10.1）。
```

---

### EDIT-AR-08 · 裁决 E — §10.3 自检块 REV-18 OQ/OPEN ITEM 行

**目标**：`docs/architecture_design.md` §10.3（L1495）。

**ANCHOR（逐字原样，整行）**：

```text
- **（REV-18）OQ / OPEN ITEM 未越权**：**ADR-21 的 1:1 口径张力（OI-1）**、**LLM Key 首启供给序（OI-2）**、**掩码字面（OI-3）** 均**登记为 OPEN ITEM**，待用户 / PM 裁决；架构层**不自行改写 ADR-21、不自行拍板业务数值、不新增 REQ、不改 AC**。
```

**REPLACE（逐字新样）**：

```text
- **（REV-18）OQ / OPEN ITEM 处置（用户裁决 2026-10-07 后）**：**OI-1**（ADR-21 的 1:1 口径张力）**已由 ADR-21-R1 承接并关闭**（ADR-21 正文一字不动）；**OI-2**（LLM Key 首启供给序）**已关闭**（采纳 **ADR-39 Option C**，缺 Key 非致命；备选 Option B 已评估未采纳）；**OI-3**（掩码字面）**保持 OPEN**（施工期定，不阻塞）。架构层**未自行改写 ADR-21 正文、未自行拍板业务数值、未新增 REQ、未改 AC**。
```

---

### EDIT-AR-09 · 裁决 B（全文复核） — §10.3 REV-18 增量条目中的计数

**目标**：`docs/architecture_design.md` §10.3（L1490）。**仅改计数与 OI 描述片段**（整行替换）。

**ANCHOR（逐字原样，整行）**：

```text
- **（REV-18）系统管理 / 项目 / LLM Key / 项目域资料增量已贯通**：新增 **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42**（每条含 Context（**REQ 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 全部已复核**：不受影响 **32**、口径补注 **3**（ADR-08 / 18 / 28）、待裁决 **1**（ADR-21，登记 OPEN ITEM OI-1）、**新增 6**、**无一条跳过**）；新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368）；新增 IFC **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）；§1.3 追加 R18 增补段与 2 行、§8 新增 [ARCH-ASSUMPTION-A12]、§9 新增 [TBD-T26] / [TBD-T27]、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）、§10.2 追加「许可面未变」句。
```

**REPLACE（逐字新样）**：

```text
- **（REV-18）系统管理 / 项目 / LLM Key / 项目域资料增量已贯通**：新增 **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42**（每条含 Context（**REQ 引用**）/ Options（**≥2**，含已评估未采纳项）/ Decision / Status / Consequences）；新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 全部已复核**：不受影响 **32**、口径补注 **4**（ADR-08 / 18 / 28 / **21**，其中 ADR-21 由新增修订子节 **ADR-21-R1** 承接）、待裁决 **0**、**新增 6**、**无一条跳过**）；新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368）；新增 IFC **IFC-IB-366 ~ 377**（见 `module_design.md` §2.2.9）；§1.3 追加 R18 增补段与 2 行、§8 新增 [ARCH-ASSUMPTION-A12]、§9 新增 [TBD-T26] / [TBD-T27]、§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3；**OI-1 / OI-2 经用户裁决 2026-10-07 关闭，OI-3 保持 OPEN**）、§10.2 追加「许可面未变」句。
```

---

### EDIT-MD-01 · 裁决 F — module_design.md §9.11 OQ/OPEN ITEM 处置

**目标**：`docs/module_design.md` §9.11（L1534）。

**ANCHOR（逐字原样，整行）**：

```text
- **OQ / OPEN ITEM 处置**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）/ **OI-2**（LLM Key 首启供给序）/ **OI-3**（掩码字面）**保持开放**（`architecture_design.md` §10.1）；架构层只落地「**软删停用 / 零迁移 / 未配置态 fail-closed / 无明文可分**」的安全默认，**不自行改写 ADR-21、不自行拍板业务数值**。
```

**REPLACE（逐字新样）**：

```text
- **OQ / OPEN ITEM 处置（用户裁决 2026-10-07 后）**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）**已由 ADR-21-R1 承接并关闭**、**OI-2**（LLM Key 首启供给序）**已关闭**（采纳 ADR-39 Option C，缺 Key 非致命）、**OI-3**（掩码字面）**保持 OPEN**（施工期定，不阻塞）—— 均见 `architecture_design.md` §10.1；架构层只落地「**软删停用 / 零迁移 / 未配置态 fail-closed / 无明文可分**」的安全默认，**不自行改写 ADR-21 正文、不自行拍板业务数值**。
```

---

### EDIT-MD-02 · 裁决 F — module_design.md §11 REV-18 自检 OQ/OPEN ITEM 行

**目标**：`docs/module_design.md` §11（L1656）。

**ANCHOR（逐字原样，整行）**：

```text
      - **OQ / OPEN ITEM 未越权**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）**登记不裁决**、**OI-2**（LLM Key 首启供给序）、**OI-3**（掩码字面）**保持开放**；架构层**不自行改写 ADR-21、不新增 REQ、不改 AC**。
```

**REPLACE（逐字新样）**：

```text
      - **OQ / OPEN ITEM 未越权**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）**已由用户裁决（2026-10-07）关闭**（经 `architecture_design.md` **ADR-21-R1** 承接，ADR-21 正文一字不动）、**OI-2**（LLM Key 首启供给序）**已关闭**（采纳 ADR-39 Option C）、**OI-3**（掩码字面）**保持 OPEN**；架构层**不自行改写 ADR-21 正文、不新增 REQ、不改 AC**。
```

---

## 3. [全文复核] 计数同步（由「全文复核所有引用该计数之处」推导）

> 结论计数 `不受影响 32 / 口径补注 3 / 待裁决 1 / 新增 6` 在 `architecture_design.md` 共出现 **4 处**：L50（头部 REV-18 修订摘要）、L382（§2.0.9 小结，见 EDIT-AR-03）、L1490（§10.3，见 EDIT-AR-09），以及 **L32（`<revision_history>` REV-18 条目）**。L32 属历史留痕，**建议不改写、改由新增 rev 条目承接**（见 §4 EDIT-AR-V2）；如需就地同步，见 EDIT-AR-10。

### EDIT-AR-10 · 头部 REV-18 修订摘要（L50）计数同步

**目标**：`docs/architecture_design.md` 头部 REV-18 修订摘要段（L50）。**仅改计数与 ADR-21 描述片段**（整行替换）。

**ANCHOR（逐字原样，整行）**：

```text
**（REV-18）系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量**（用户裁决 2026-10-07，REV-18-2；上游 `requirements_spec.md` v1.10.0 / REV-18-2）：① 新增 **ADR-37 ~ ADR-42**（项目注册表承载与软删 / LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析 / LLM 未配置态启动与运行期语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 服务端授权与导航解耦），**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：**不受影响 32 条**、**口径补注 3 条**（ADR-08 Key 取值来源 / ADR-18 复用载体与迁移机制 / ADR-28 项目列表数据源）、**待裁决口径张力 1 条**（ADR-21，登记 OPEN ITEM OI-1，**不自行改写**）、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 增 2 行 + R18 增补段；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**；§9 新增 **[TBD-T26] / [TBD-T27]**；§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3）；§10.2 追加「许可面未变」句；§10.3 追加 R18 自检；⑥ **落点并入既有模块**（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、生效口径（ADR-32 / C-IB-40 / OOS-16）**未改**、`tech_stack.md`（见 Part C：登记型口径修订，无新第三方依赖）。**登记**：**生产后端重启与首次环境变量配置须由用户执行**；`IB_DEFAULT_ADMIN_PASSWORD` 等既有凭据键纪律不变，**LLM Key 不入 `.env`**（载体内 DB，库文件 0600 且属主对齐服务账号）。
```

**REPLACE（逐字新样）**：

```text
**（REV-18）系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量**（用户裁决 2026-10-07，REV-18-2；上游 `requirements_spec.md` v1.10.0 / REV-18-2）：① 新增 **ADR-37 ~ ADR-42**（项目注册表承载与软删 / LLM Key 凭据载体 = DB + 凭据纪律 + 装配期解析 / LLM 未配置态启动与运行期语义 / 运维账号 CRUD 扩展与删除保护 / 项目域 `kb_id` 推导 + 保留归属断言 / 系统管理三分 IA + 服务端授权与导航解耦），**ADR 数 36 → 42**；② 新增 **§2.0.9 REV-18 影响复核表**（**既有 36 条 ADR 逐条复核，无一条跳过**：**不受影响 32 条**、**口径补注 4 条**（ADR-08 Key 取值来源 / ADR-18 复用载体与迁移机制 / ADR-28 项目列表数据源 / **ADR-21 由新增修订子节 ADR-21-R1 承接**）、**待裁决 0 条**、**新增 6 条**）；③ 新增**第 18 / 19 个端口** `ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**端口 17 → 19（纯追加）**；④ §1.3 增 2 行 + R18 增补段；⑤ §8 新增 **[ARCH-ASSUMPTION-A12]**；§9 新增 **[TBD-T26] / [TBD-T27]**；§10.1 新增 REV-18 OPEN ITEM（OI-1 / OI-2 / OI-3；**OI-1 / OI-2 经用户裁决 2026-10-07 关闭，OI-3 保持 OPEN**）；§10.2 追加「许可面未变」句；§10.3 追加 R18 自检；⑥ **落点并入既有模块**（**零新增模块、零新增依赖边**）；⑦ **计数同步**：REQ-FUNC 42/42 → **48/48**（新增 IB-43 ~ IB-48）、NFR 19 → **20**（新增 NFR-20）。**不变**：§1 / §3 ~ §7 的既有结论、模块数（**26，未新增**）、`IFC-IB-001 ~ 365` **号 / 名 / 签名一字不动**（**仅 4 条文字与取值口径修订**，逐条登记于 §2.0.9）、**§4.1 依赖边逐行不变（零新增依赖边）**、DAG 无环、生效口径（ADR-32 / C-IB-40 / OOS-16）**未改**、`tech_stack.md`（见 Part C：登记型口径修订，无新第三方依赖）。**登记**：**生产后端重启与首次环境变量配置须由用户执行**；`IB_DEFAULT_ADMIN_PASSWORD` 等既有凭据键纪律不变，**LLM Key 不入 `.env`**（载体内 DB，库文件 0600 且属主对齐服务账号）。
```

---

## 4. [供裁量] 一致性同步（消除同文档内 OI 状态自相矛盾）

> 以下 3 处并非用户裁决逐字点名，但若不同步，会在**同一文档内**出现「OI-1 / OI-2 已关闭」与「OI-1 / OI-2 仍开放」并存的矛盾。**PM 可裁量跳过**。

### EDIT-AR-11 · ADR-40 Decision ③ 中的 OI-1 措辞

**目标**：`docs/architecture_design.md` ADR-40（L1116）中的 ③ 片段。

**ANCHOR（逐字原样，子串）**：

```text
③ **1:N 零迁移**：**不**加 `users.project_id` 唯一约束；REQ-FUNC-IB-31 正文不改（**注**：与 ADR-21 的 1:1 表述存在**口径张力**，登记为 OPEN ITEM **OI-1**，**本 ADR 不自行改写 ADR-21**）。
```

**REPLACE（逐字新样）**：

```text
③ **1:N 零迁移**：**不**加 `users.project_id` 唯一约束；REQ-FUNC-IB-31 正文不改（**注**：ADR-21 的「1:1」表述已由 **ADR-21-R1** 收窄 / 订正为 **N:1**，口径张力经**用户裁决 2026-10-07 关闭**；本 ADR **不自行改写 ADR-21 正文**）。
```

### EDIT-AR-12 · [ARCH-ASSUMPTION-A12] 行中的 OI-2 / OI-3 措辞

**目标**：`docs/architecture_design.md` A12 行（L1332）末段。

**ANCHOR（逐字原样，子串；含行尾表格竖线）**：

```text
若 PM / 用户不采纳「未配置态」，须以「部署期**由用户手工预置** Key」替代（ADR-39 Option B）；若判定「缺 Key 即启动失败」为硬约束，须回 GROUP_A 立项（架构层**不发明需求**）；掩码字面与库文件属主由施工期 / 部署期定 | **需 PM 知悉**（与 [TBD-T27] 同源；OI-2 / OI-3） |
```

**REPLACE（逐字新样）**：

```text
**用户裁决（2026-10-07）已采纳「未配置态」**（ADR-39 Option C）；备选方案 Option B（部署期**由用户手工预置** Key）**已评估未采纳**；若判定「缺 Key 即启动失败」为硬约束，须回 GROUP_A 立项（架构层**不发明需求**）；掩码字面与库文件属主由施工期 / 部署期定 | **已裁决（2026-10-07）**：**OI-2 关闭**（采纳 Option C）、**OI-3 保持 OPEN**（与 [TBD-T27] 同源） |
```

### EDIT-MD-03 · module_design.md §3 IFC-IB-373 中的 OI-1 措辞

**目标**：`docs/module_design.md` IFC-IB-373 说明（L885）末段。

**ANCHOR（逐字原样，子串）**：

```text
**1:N / 零迁移**：**不**加 `users.project_id` 唯一约束（OQ-IB-28；**注**：与 ADR-21 的 1:1 表述存在口径张力，登记为 OPEN ITEM OI-1，**本件不自行改写 ADR-21**）。
```

**REPLACE（逐字新样）**：

```text
**1:N / 零迁移**：**不**加 `users.project_id` 唯一约束（OQ-IB-28；**注**：ADR-21 的「1:1」表述已由 `architecture_design.md` **ADR-21-R1** 收窄 / 订正为 **N:1**，口径张力经**用户裁决 2026-10-07 关闭**；**本件不自行改写 ADR-21 正文**）。
```

---

## 5. [供裁量] 版本处理（裁决 G）

**建议（供 PM 决定）**：

- **`architecture_design.md`：建议 bump `1.10.0 → 1.10.1`，`REV-18 → REV-18-R1`（patch 级）。** 理由：本轮**新增**一处正式修订子节 **ADR-21-R1**（内容净增）+ 三处 OI 状态登记（OI-1 / OI-2 关闭）与计数同步；**但不新增 ADR 编号（42 不变）、不新增端口（19 不变）、不新增 / 不改 REQ 与 AC、不改任何 IFC 编号 / 名 / 签名、不动依赖边与 DAG**。属「裁决 / 状态登记 + amend 子节」轮，patch 级足以承载，且不误导下游以为有结构变更。
- **`module_design.md`：建议同步 bump `1.10.0 → 1.10.1`，`REV-18 → REV-18-R1`。** 理由：仅同步 OI 状态与一致性措辞；若 PM 采 EDIT-MD-03，则更有必要镜像 architecture 的 revision。
- **`tech_stack.md`：NO_CHANGE（不 bump）**。本轮无技术选型 / 许可 / 依赖变更。
- **若 PM 决定不 bump**：仍建议至少落 **EDIT-AR-V2 / EDIT-MD-V2 的 rev 条目**（以时间为序追加，注明「状态登记轮，无结构变更」），以保持「可追溯」。

### EDIT-AR-V1 · architecture_design.md 头部版本号（条件落盘）

**ANCHOR（逐字原样，整段）**：

```text
  <version>1.10.0</version>
  <revision>REV-18</revision>
```

**REPLACE（逐字新样）**：

```text
  <version>1.10.1</version>
  <revision>REV-18-R1</revision>
```

### EDIT-AR-V2 · architecture_design.md revision_history 追加条目（条件落盘）

**ANCHOR（逐字原样，整行；`</revision_history>` 在本文档唯一）**：

```text
  </revision_history>
```

**REPLACE（逐字新样）**：

```text
    <rev version="1.10.1" revision="REV-18-R1" date="2026-10-07" basis="用户裁决（2026-10-07）：GR-B 三项待决收口 —— OI-1 出 ADR-21-R1（N:1，amend）；OI-2 采纳 ADR-39 Option C；OI-3 保持 OPEN" note="REV-18-R1 裁决收口（状态登记 + amend 子节，无结构变更）：① 新增 **ADR-21-R1**（对 ADR-21 的正式修订子节，**amend**；**ADR-21 正文一字不动**）—— 把「账户↔项目绑定」关系式**收窄 / 订正为 N:1**（每个运维账号恰绑一个项目；一个项目可有多个运维账号），承接 **OI-1**（依据 OQ-IB-28 / DR-15 / ADR-21）；**零迁移**（不加 `users.project_id` 唯一约束），授权落点与端口结论不变。② §2.0.9 影响复核表 ADR-21 行由「待裁决（口径张力）」改为「口径补注（已由 ADR-21-R1 承接）」；**结论计数 32 / 3 / 1 / 6 → 32 / 4 / 0 / 6**。③ §10.1：**OI-1 CLOSED**（经 ADR-21-R1）、**OI-2 CLOSED**（采纳 **ADR-39 Option C**，缺 Key 非致命、fail-closed 于调用期，其余必填仍 fail-fast；备选 Option B 已评估未采纳）、**OI-3 保持 OPEN**（施工期定，不阻塞）。④ ADR-39 Consequences 补记「Option B 已评估未采纳 / 采纳 Option C」；§10.3 自检同步。**不变约束**：ADR 数 42、模块数 26、端口 19、`IFC-IB-001 ~ 377` 号 / 名 / 签名一字不动、§4.1 依赖边逐行不变、DAG 无环、**不新增 REQ / 不改 AC**、**不新增 / 不删 ADR 编号**。需求侧文档与 FreeArk 仓库未改动；未写入任何口令 / 令牌 / Key / 证书字面量（只登记键名 / 表名 / 文件名 / 字段名）。"/>
  </revision_history>
```

### EDIT-MD-V1 · module_design.md 头部版本号（条件落盘）

**ANCHOR（逐字原样，整段）**：

```text
  <version>1.10.0</version>
  <revision>REV-18</revision>
```

**REPLACE（逐字新样）**：

```text
  <version>1.10.1</version>
  <revision>REV-18-R1</revision>
```

### EDIT-MD-V2 · module_design.md revision_history 追加条目（条件落盘）

**ANCHOR（逐字原样，整行；`</revision_history>` 在本文档唯一）**：

```text
  </revision_history>
```

**REPLACE（逐字新样）**：

```text
    <rev no="REV-18-R1" date="2026-10-07" by="system-architect" basis="用户裁决（2026-10-07）：GR-B 三项待决收口（OI-1 / OI-2 / OI-3）；上游 architecture_design.md REV-18-R1（ADR-21-R1）">
      **状态登记 + 一致性措辞轮，无结构变更**（模块数仍 **26**、**端口 19**、**§4.1 依赖边逐行未改**、DAG 无环）：① **OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）**已由 `architecture_design.md` ADR-21-R1 承接并关闭**（关系式收窄 / 订正为 **N:1**；ADR-21 正文一字不动；**零迁移**）；② **OI-2**（LLM Key 首启供给序）**已关闭**（采纳 **ADR-39 Option C**，缺 Key 非致命、fail-closed 于调用期，其余必填仍 fail-fast；备选 Option B 已评估未采纳）；③ **OI-3**（掩码字面）**保持 OPEN**（施工期定，不阻塞）。同步位置：§9.11 OQ / OPEN ITEM 处置、§11 自检。**不变**：`IFC-IB-001 ~ 377` 号 / 名 / 签名一字不动、计数（REQ-FUNC 48/48、NFR 20）、**不新增 REQ / 不改 AC**、生效口径（保存 + 服务重启重装配；ADR-32 / C-IB-40 / OOS-16）未改。需求侧文档只读；未修改 FreeArk 任何文件；未写入任何口令 / 令牌 / Key / 证书字面量（只登记键名 / 表名 / 文件名 / 字段名）。
    </rev>
  </revision_history>
```

---

## 6. 未纳入本包（观察项，仅供 PM 知悉）

- **module_design.md 覆盖 / 映射行中的「1:1」字面**：`§2.2` 端口行（L1332 `AccountStore`「账户↔项目绑定（1:1）」）、`§9.1` REQ 覆盖行（L1385 `IB-32 账户↔项目 **1:1** 绑定`）、`§9.8` R14 追踪行（L1502 `REQ-FUNC-IB-31（账户 : 项目 = 1:1；admin 全局）`）。这些行**镜像需求侧 REQ-FUNC-IB-31 / IB-32 的既有字面**（需求三件套本轮**不得触碰**），且用户裁决 F 的同步范围限定于 §9.11 / §11 / revision_history，故**本包不改**。若 PM 认为须统一为 N:1 口径，建议**另立交付项**（涉及需求侧字面同步，超出本轮边界）。
- **architecture_design.md ADR-21 正文内的「1:1」**（Context 引 DR-15；Consequences 负向）：**按裁决 A 强制一字不动**；其口径已由 ADR-21-R1 收窄，属预期状态（ADR-21-R1 Consequences 已声明此「负向」）。
- **§10.1 R14 OPEN ITEM（L1398）** 中 `REQ-FUNC-IB-31（1:1 绑定）` 的映射引用：该行是 **R14 需求侧缺口 OPEN ITEM**（非 OI-1），且其「1:1」为需求字面引用，**不在本轮范围**。
- **`tech_stack.md`**：本轮无技术选型 / 许可变更，**无需 EDIT**（若 PM bump 版本号口径统一，可另行处理，架构侧无强制项）。

---

## 7. 落盘后校验清单（PM / 复核用）

1. **ADR-21 正文逐字 / hash 未变**（EDIT-AR-01 的 ANCHOR 行在 REPLACE 中原样保留；ADR-21 段无其它改动）。
2. `### ADR-21-R1` 子节位于 ADR-21 正文之后、其后既有 `---` 之前；与 ADR-15 ↔ ADR-15-R1 排版一致。
3. `architecture_design.md` 内 `不受影响 32 / 口径补注 3 / 待裁决 1 / 新增 6` 的**现行态引用**（L50、L382、L1490）**全部**为 `32 / 4 / 0 / 6`（历史 `revision_history` 条目 L32 保持不变，由新增 REV-18-R1 条目承接）。
4. `OI-1` / `OI-2` 在 `architecture_design.md` §10.1 / §10.3、`module_design.md` §9.11 / §11 的**现行态**一致为 **CLOSED**；`OI-3` 一致为 **OPEN**。
5. ADR 总数仍 **42**、模块数仍 **26**、端口仍 **19**、`IFC-IB-*` 编号 / 名 / 签名无改动（本轮**未新增任何 IFC**）。
6. 全文**不含任何口令 / 令牌 / Key / 证书字面量**（只登记键名 / 表名 / 文件名 / 字段名）。
7. 未触碰 `src/**`、`tests/**`、`requirements_spec.md`、`user_stories.md`、`implementation_plan.md`。

---

## 8. ADR-21-R1 全文（本包 EDIT-AR-01 的 REPLACE 内嵌新块，独立摘录以便逐字校验）

```text
### ADR-21-R1 账户↔项目绑定关系式的收窄：N:1（REV-18 修订子节）

- **Status**: Accepted（REV-18 修订；**本子节为对 ADR-21 的正式修订子节（amend）**，ADR-21 的 ID / Status / Context / Options / Decision / Consequences **一字不动**；本子节**收窄并订正** ADR-21 中「账户↔项目 1:1 绑定」的**关系式歧义**为 **N:1**，ADR-21 的**授权落点与端口结论全部不变**）
- **Context**: 用户裁决（2026-10-07）就 **OI-1**（本文件 §10.1）作出裁定：ADR-21 的「账户↔项目绑定」关系式明确为 **N:1**。关系方既有依据：**DR-15**（一运维账户绑定一个项目）、**OQ-IB-28**（REV-18 裁决：**1:N**、**零迁移**、**无 `users.project_id` 唯一约束**）、**ADR-21**（R13，账户↔项目绑定与角色模型）。**语义裁定**：ADR-21 的「1:1」**以「每账号恰绑一项目」为唯一合法读法** —— 它与 OQ-IB-28 的「1:N」为**同一关系的两侧读法**（账号侧 N → 项目侧 1；反向 1 → N），据此排除「每项目至多一账号」（与 OQ-IB-28 冲突）的歧义读法。既有落点：ADR-40（R18 已按 1:N、零迁移落地，**不**加唯一约束）、`AccountStore`（IFC-IB-310，13 方法一字不动）、`UserRecord.project_id`（单值、可空）。
- **Options**:
  - **Option A（不改 ADR-21，仅在口头 / 单测注释里说明「1:1」读作「每账号恰绑一项目」）**：优—零改动、零迁移。缺—**歧义仍在**：「1:1」在对称语境下可被合法读为「每项目至多一账号」，与 OQ-IB-28 的 1:N 直接冲突；下游（测试门控 / 施工 / 检查清单）须各自解释，口径**不可审计 / 不可回溯**。**已评估未采纳**。
  - **Option B（出 ADR-21-R1 amend 子节，把关系式显式收窄 / 订正为 N:1）** ← **选定**：**ADR-21 正文一字不动**（沿用 ADR-15-R1 / ADR-15-R2 的 amend 先例，**不 supersede**），修订落在本子节；关系式固化为「**每个运维账号恰绑一个项目（N 账号 → 1 项目）；一个项目可有多个运维账号**」。优—歧义被**结构性消除**且**有唯一落点**（可回溯 OQ-IB-28 / DR-15 / ADR-21）；**与既有无 `users.project_id` 唯一约束一致**，**零迁移**；ADR-21 的授权结论（Option A：`AuthzContext(actor_id, project_id, roles)`；admin `project_id=None` 全局）与端口边界**不变**。缺—ADR-21 正文的字面「1:1」仍在，引用该处者须一并标注 **ADR-21-R1**。
  - **Option C（改写 ADR-21 正文，把「1:1」字面直接替换为「N:1」）**：优—字面一致、无二次引用。缺—**违反「编号只增不改」纪律**（ADR-21 为已 Accepted 正文；改写会使 REV-13 的历史留痕失真），且 ADR-15-R1 / ADR-15-R2 已确立「正文一字不动 + amend 子节」先例。**已评估未采纳**。
- **Decision**: **Option B**。**固化后的关系式（N:1）**：**每个运维账号恰绑定一个项目（N 个账号 → 1 个项目）；一个项目可有多个运维账号**。① **数据落点不变**：`UserRecord.project_id`（单值、可空；admin 为 `None`）；**不新增**任何唯一约束（OQ-IB-28「零迁移」）。② **授权落点不变**：仍**只**经 `AuthzContext(actor_id, project_id, roles)` 表达（ADR-21 Option A）；运维账号 `roles=("manager",)`、边界由 `project_id` 强制；admin `project_id=None` 全局。③ **端口不变**：`AccountStore`（IFC-IB-310）方法集一字不动；账号创建的顺序依赖前置校验（目标 `project_id` 须在注册表存在且 `active`，ADR-40 / REQ-FUNC-IB-45）不变。④ **零迁移**：无 DDL 变更、无数据回填。
- **Consequences**:
  - 正向: 「账户↔项目」口径**唯一且可回溯**（本子节 → OQ-IB-28 / DR-15 / ADR-21）；**ADR-21 正文一字不动**（amend 而非 supersede，REV-13 历史留痕完整）；**与既有无 `users.project_id` 唯一约束一致、零迁移**；下游「1:1」引用可统一回链本子节，消除测试门控 / 施工各自解释的风险。
  - 负向: **ADR-21 正文仍保留「1:1」字面**，凡引用该处者**须一并标注 ADR-21-R1**（否则仍可能被误读为「每项目至多一账号」）；本子节为**收窄 / 订正**而非推翻，故**不新增**任何 IFC / 端点 / 迁移足迹。
```

---

**（本包完 · 仅登记键名 / 表名 / 文件名 / 字段名，不含任何口令 / 令牌 / Key / 证书字面量）**
