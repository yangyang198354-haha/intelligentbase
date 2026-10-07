# REV-18 GROUP_B Apply-Ready 包（Part C：`docs/tech_stack.md` 增量 + Part D：校对清单）

```xml
<apply_ready_package_part>
  <artifact>tech_stack</artifact>
  <target_file>docs/tech_stack.md</target_file>
  <revision>REV-18</revision>
  <producer>system-architect</producer>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
  <date>2026-10-07</date>
  <edits>EDIT-TECH-01 ~ EDIT-TECH-05（共 5 处）</edits>
</apply_ready_package_part>
```

> 目标文档当前状态：**v1.4.0 / REV-13**。

---

## ■ 版本决策（producer 明示 rationale，供 PM 采信或否决）

**决策**：**版本 1.4.0 → 1.4.1（`revision=REV-18`），作「登记型补丁修订」**（**不新增任何第三方选型 / 依赖**）。

**Rationale**：
1. REV-18 的 LLM Key 载体改由 **DB**（ADR-38 / OQ-IB-25），**未引入任何新第三方组件**（载体 = 既有 SQLite / stdlib `sqlite3`，复用既有手写迁移机制）—— 故 **§1 选型表不新增行、§2 许可台账不新增条目、§1.1 不新增留痕**。
2. **但** `tech_stack.md` 的 `<credential_policy>`（第 23 行）现称「目标机凭据**一律经环境变量注入**」，且 §1「配置载体」行称「凭据仅环境变量」—— **该表述在本轮后将成为不实陈述**（LLM Key 载体内 DB）。为**不产生假陈述**（对齐 R17 ADR 修订所立「消解假陈述」纪律），须作**最小事实订正**：将口径收窄为「**除外 LLM Key**：LLM Key 经 DB；其余密钥仍经环境变量」。
3. 该修订**性质 = 登记型补丁**（同 R10「登记型修订，选型未变」先例）：**无新第三方依赖 / 无新选型 / 无键名改名**，故取 **补丁位**（1.4.0 → 1.4.1）而非次版本位。

**若 PM 判定 tech_stack 本轮不应改动**：则退化为在本文件顶部登记一行「**REV-18: 无变更**（理由：LLM Key 载体内 DB，但复用既有 SQLite 组件、无新选型）」，并**知悉**第 23 行 / §1「配置载体」行的「一律经环境变量」将与本轮架构侧 ADR-38 口径**不一致**（须在 GR-B 记录该已知偏差）。**producer 建议采纳补丁修订以消除不实陈述**（见 EDIT-TECH-02 / 04）。

---

## ■ EDIT-TECH-01 — `file_header` 版本 / 修订号 / 调用号 / 更新时间 / 输入指针

**位置**：`file_header`（第 6、7、11、13 行；第 15 ~ 18 行）。

**REPLACE-1（版本 / 修订 / 调用号 / 更新时间）**：

**ANCHOR（old_string）**：
```
  <version>1.4.0</version>
  <revision>REV-13</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04b 技术选型</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-007</invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-10-06</updated_at>
```

**REPLACE（new_string）**：
```
  <version>1.4.1</version>
  <revision>REV-18</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04b 技术选型</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
  <created_at>2026-09-25</created_at>
  <updated_at>2026-10-07</updated_at>
```

**REPLACE-2（输入指针）**：

**ANCHOR（old_string）**：
```
    <input path="docs/requirements_spec.md" version="1.4.0" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.4.0" status="APPROVED" note="R7 新增登记：可视化配置的 AC 落点（AC-IB-17-01~06 / AC-IB-18-01~06）为 §4.5 新增项与 §1.3 凭据纪律的直接依据"/>
    <input path="docs/architecture_design.md" version="1.5.0" revision="REV-13" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/module_design.md" version="1.5.0" revision="REV-13" status="DRAFT_FOR_GATE_REVIEW"/>
```

**REPLACE（new_string）**：
```
    <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED" note="REV-18 新增登记：系统管理三分 / 项目 CRUD / LLM Key / 项目域资料的 AC 落点为 §1 凭据口径与 §6 自检的直接依据"/>
    <input path="docs/architecture_design.md" version="1.10.0" revision="REV-18" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/module_design.md" version="1.10.0" revision="REV-18" status="DRAFT_FOR_GATE_REVIEW"/>
```

---

## ■ EDIT-TECH-02 — `<credential_policy>` 凭据口径收窄（消除不实陈述）

**位置**：`file_header/credential_policy`（第 23 行）。

**ANCHOR（old_string）**：
```
  <credential_policy>本文档不记录任何密钥、令牌、口令或证书。目标机凭据**一律经环境变量注入**（REQ-NFR-IB-07 / C-IB-02）。所有条目仅登记「配置键名」，不登记值。</credential_policy>
```

**REPLACE（new_string）**：
```
  <credential_policy>本文档不记录任何密钥、令牌、口令或证书。目标机凭据**除 LLM Key 外**均经环境变量注入（REQ-NFR-IB-07 / C-IB-02）；**LLM Key 属唯一例外**：其载体为**数据库**（同一 SQLite 台账，库文件 **0600** 且属主对齐服务账号；REQ-FUNC-IB-47 / REQ-NFR-IB-20 / C-IB-42 / ADR-38），**不入 `.env`**，唯一写入口为管理端点。所有条目仅登记「配置键名」，不登记值。</credential_policy>
```

---

## ■ EDIT-TECH-03 — `revision_history` 追加 REV-18 条目

**位置**：`revision_history` 内，REV-13 条目（`<rev version="1.4.0" revision="REV-13" …>`）之后、`</revision_history>` 之前。

**ANCHOR（插入点边界，逐字）**：
```
    <rev version="1.4.0" revision="REV-13" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-007" author="system-architect" note="REV-13 认证与商用界面重构增量（GROUP_A REV-13 下游贯通：REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）：① §1 新增三行 —— 前端 UI 组件库 Element Plus（MIT，DR-13）、前端路由 vue-router（MIT，hash 模式）、口令哈希库 bcrypt（Apache-2.0，DR-11）；② §1.1 留痕 5 项已评估未采纳（Cookie 会话 / JWT 自包含令牌 / 独立鉴权服务 / Django contrib.auth+ORM 迁移 / 运行期 CDN 加载 Element Plus）；③ 新增 §1.4 客户端配置键登记（只登记键名 IB_AUTH_LOGIN_PATH / IB_AUTH_SESSION_STORAGE_KEY，不含任何值）；④ §2 台账新增三行（Element Plus / vue-router / bcrypt，均采纳）+ （R13）遗留合规动作追加；⑤ 新增 §2.2 前端依赖许可登记（方法同 R10，结论暂标 [待核实]）；⑥ §4.5 新增第 13~18 项（默认管理员种子与首登强制改密 / 零 Cookie / token-query 全端点 4xx / IB_AUTHZ_POLICY_MODULE 未配置即启动失败 / HTTPS 生效 / 前端自包含与凭据不回显）；⑦ §5.2 新增一行中风险（bcrypt cost 与阈值标定，以 [TBD-T22] 为准）、§5.3 新增一行低风险（Element Plus 传递依赖许可与体积 + 口令/令牌泄露缓解）；⑧ 硬约束未松动：未引入 Docker / Redis / PyMuPDF / Cookie 会话 / Django ORM / contrib.auth；禁止运行期 CDN。仅登记键名，未写入任何凭据值。"/>
  </revision_history>
```

**REPLACE（new_string，REV-13 条目 + REV-18 条目）**：
```
    <rev version="1.4.0" revision="REV-13" date="2026-10-06" invocation_id="INV-GROUP_B-INTELBASE-007" author="system-architect" note="REV-13 认证与商用界面重构增量（GROUP_A REV-13 下游贯通：REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）：① §1 新增三行 —— 前端 UI 组件库 Element Plus（MIT，DR-13）、前端路由 vue-router（MIT，hash 模式）、口令哈希库 bcrypt（Apache-2.0，DR-11）；② §1.1 留痕 5 项已评估未采纳（Cookie 会话 / JWT 自包含令牌 / 独立鉴权服务 / Django contrib.auth+ORM 迁移 / 运行期 CDN 加载 Element Plus）；③ 新增 §1.4 客户端配置键登记（只登记键名 IB_AUTH_LOGIN_PATH / IB_AUTH_SESSION_STORAGE_KEY，不含任何值）；④ §2 台账新增三行（Element Plus / vue-router / bcrypt，均采纳）+ （R13）遗留合规动作追加；⑤ 新增 §2.2 前端依赖许可登记（方法同 R10，结论暂标 [待核实]）；⑥ §4.5 新增第 13~18 项（默认管理员种子与首登强制改密 / 零 Cookie / token-query 全端点 4xx / IB_AUTHZ_POLICY_MODULE 未配置即启动失败 / HTTPS 生效 / 前端自包含与凭据不回显）；⑦ §5.2 新增一行中风险（bcrypt cost 与阈值标定，以 [TBD-T22] 为准）、§5.3 新增一行低风险（Element Plus 传递依赖许可与体积 + 口令/令牌泄露缓解）；⑧ 硬约束未松动：未引入 Docker / Redis / PyMuPDF / Cookie 会话 / Django ORM / contrib.auth；禁止运行期 CDN。仅登记键名，未写入任何凭据值。"/>
    <rev version="1.4.1" revision="REV-18" date="2026-10-07" invocation_id="INV-GROUP_B-INTELBASE-012" author="system-architect" note="REV-18 **登记型补丁修订**（GROUP_A REV-18-2 下游贯通：系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）：**无新第三方依赖、无新选型、无键名改名**（LLM Key 载体 = 既有 SQLite / stdlib sqlite3，复用既有手写 scoped 迁移机制；项目注册表同）。唯一实质订正 = **凭据载体口径**：`<credential_policy>`（第 23 行）与 §1「配置载体」行的「**一律经环境变量注入**」收窄为「**除外 LLM Key**：LLM Key 经 DB（库文件 0600 且属主对齐服务账号）；其余密钥仍经环境变量」—— **消除与 ADR-38 口径的不一致（不产生假陈述）**；新增键名 `IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND` **只在 `module_design.md` §2.2.9 / §5 登记，本文档不重复登记值**。§1 选型表**未新增行**；§1.1 **未新增留痕**；§2 许可台账**未新增条目**（无新组件，REQ-NFR-IB-12 合规）。硬约束未松动：未引入 Docker / Redis / Redis / PyMuPDF / Cookie 会话 / Django ORM / contrib.auth；未引入第三方密钥管理服务。仅登记键名，未写入任何凭据值。**性质 = 登记型修订，选型未变**（同 R10 先例；GROUP_B 可复核）。"/>
  </revision_history>
```

---

## ■ EDIT-TECH-04 — §1「配置载体」行凭据口径同步

**位置**：§1 技术选型表「配置载体」行（第 108 行）。

**ANCHOR（old_string）**：
```
| 配置载体 | 配置文件（YAML/JSON）+ 环境变量覆盖（凭据仅环境变量） | — | REQ-FUNC-IB-01/02；[ARCH-ASSUMPTION-A1] | REQ-NFR-IB-02/07 | 低 | 仓库仅含 `.env.example`（无真实值）；启动期校验必填项；**（R1）配置装载不依赖 Django settings 机制**（保持 `ConfigurationSource` 端口的独立性，便于离线单测与跨项目复用） |
```

**REPLACE（new_string）**：
```
| 配置载体 | 配置文件（YAML/JSON）+ 环境变量覆盖（**凭据：除 LLM Key 外**经环境变量；**LLM Key 载体内 DB**） | — | REQ-FUNC-IB-01/02；[ARCH-ASSUMPTION-A1]；**（REV-18）REQ-FUNC-IB-47 / REQ-NFR-IB-20 / C-IB-42 / ADR-38** | REQ-NFR-IB-02/07 | 低 | 仓库仅含 `.env.example`（无真实值）；启动期校验必填项（**（REV-18）LLM Key 未配置非致命，fail-closed 于调用期**，ADR-39）；**（R1）配置装载不依赖 Django settings 机制**（保持 `ConfigurationSource` 端口的独立性，便于离线单测与跨项目复用）；**（REV-18）LLM Key 的载体 = 同一 SQLite 台账（库文件 0600 且属主对齐服务账号），唯一写入口为管理端点，不入 `.env`** |
```

---

## ■ EDIT-TECH-05 — §6 自检声明追加 REV-18 块

**位置**：§6 末尾（R13 版本订正说明行，第 440 行）之后的适当位置（建议紧随 R13 自检块之后、R2 自检块之前，或文档 §6 末）。

**ANCHOR（old_string，R13 版本订正说明行，逐字）**：
```
- **（R13）版本订正说明**：任务文本称本文件由 1.3.0 升 1.4.0；**实际起版为 1.3.1**（R7 + R10 传递依赖许可登记，`author=software-developer`）→ 本提案为 **1.3.1 → 1.4.0 / REV-13**。
```

**REPLACE（new_string，R13 行 + REV-18 块）**：
```
- **（R13）版本订正说明**：任务文本称本文件由 1.3.0 升 1.4.0；**实际起版为 1.3.1**（R7 + R10 传递依赖许可登记，`author=software-developer`）→ 本提案为 **1.3.1 → 1.4.0 / REV-13**。
- **（REV-18）登记型补丁修订的技术面结论**：① **无新第三方依赖 / 无新选型 / 无键名改名** —— LLM Key 载体（DB）与项目注册表均复用**既有 SQLite（stdlib `sqlite3`）** 与**既有手写 scoped 迁移机制**（新增迁移 `005_projects.sql` / `006_llm_key.sql`，属交付物，非选型）；§1 选型表**未新增行**、§1.1 **未新增留痕**、§2 许可台账**未新增条目**。② **唯一实质订正 = 凭据载体口径**：`<credential_policy>` 与 §1「配置载体」行由「**一律经环境变量**」收窄为「**除外 LLM Key**：LLM Key 经 DB（库文件 **0600** 且属主对齐服务账号）；其余密钥仍经环境变量」（REQ-FUNC-IB-47 / REQ-NFR-IB-20 / C-IB-42 / ADR-38）—— 目的是**消除与架构侧 ADR-38 的口径不一致（不产生假陈述）**。
- **（REV-18）凭据纪律（新增口径）**：本文档**只登记键名 / 表名 / 文件层名**；**LLM Key 的字面量（明文 / 掩码 / 前缀）不在本文件出现**；`IB_LLM_API_KEY` **不再作为 LLM Key 来源**；新增键 `IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND` 的**语义**在 `module_design.md` §2.2.9（本文件不重复登记值）。**未写入任何密钥 / 令牌 / 口令 / 证书字面量。**
- **（REV-18）禁项与硬约束未松动**：**未引入 Docker / 容器化**（DR-03）、**未引入 Redis / RabbitMQ**（C-IB-08）、**未引入 PyMuPDF 或任何 AGPL / copyleft 组件**（REQ-NFR-IB-12）、**未引入 Cookie 会话**（DR-10）、**未引入 Django ORM / `contrib.auth`**（ADR-07-R1）、**未引入第三方密钥管理服务**（LLM Key 载体内自有 DB，OOS-18 为扩展点预留）；端口契约仍 **framework-free**（新增契约全部落在 MOD-IB-01，纯 stdlib）。
- **（REV-18）未改动他处**：`FreeArk` 仓库**任何文件未作修改**（全程只读）；需求侧文档（`requirements_spec.md` / `user_stories.md` v1.10.0）**只读未改**；`architecture_design.md` / `module_design.md` 的既有结论**未改写**（REV-18 只追加）；`implementation_plan.md`（GROUP_C）**未改**；本阶段**止于 GROUP_B**。
- **（REV-18）版本口径**：本轮起版 = **1.4.0（REV-13）** → 本提案为 **1.4.0 → 1.4.1 / REV-18**（**登记型补丁**；理由见文件顶部「版本决策」）。
```

---

# Part D — 合并校对清单与落地自检

## D.1 三文档 EDIT 总览（按落盘顺序）

| 序 | 文件（本包） | 目标文档 | EDIT 数 | 编号 |
|----|-------------|----------|--------|------|
| 1 | `docs/rev18_groupb_apply_package.md`（Main） | `docs/architecture_design.md` | 11 | EDIT-ARCH-01 ~ 11 |
| 2 | `docs/rev18_groupb_apply_package_part2.md` | `docs/module_design.md` | 20 | EDIT-MOD-01 ~ 20 |
| 3 | `docs/rev18_groupb_apply_package_part3.md`（本件） | `docs/tech_stack.md` | 5 | EDIT-TECH-01 ~ 05 |
| | | **合计** | **36** | |

**落盘顺序**：EDIT-ARCH-01→11 → EDIT-MOD-01→20 → EDIT-TECH-01→05。

## D.2 落盘后强校验（PM 逐项复核）

- [ ] **A1 版本链**：三文档 `file_header` 的 `<version>` / `<revision>` / `<invocation_id>INV-GROUP_B-INTELBASE-012` 均已更新；`revision_history` 均追加 REV-18 条目且旧条目一字未动。
- [ ] **A2 计数一致**：`architecture_design.md` **ADR 数 42**（36 + 6）；`module_design.md` **模块数 26**（未变）、**端口数 19**（17 + 2）；**REQ-FUNC 48/48**、**NFR 20**（19 + 1）—— 三处计数（§1 / §9.1 / §11）互相一致。
- [ ] **A3 编号连续**：新增 ADR = **37 / 38 / 39 / 40 / 41 / 42**（无跳号、无重号）；新增 IFC = **366 ~ 377**（连续 12 条）；`IFC-IB-285` 仍预留、`IFC-IB-131` 登记不修。
- [ ] **A4 锚点唯一**：各 EDIT 的 `ANCHOR` 在落盘前**在目标文档中唯一匹配**（尤其 `### MOD-IB-xx` 级标题、`## 3. / ## 10.` 级标题）；`INSERT` 型不误改边界行。
- [ ] **A5 §4.1 零改动**：`module_design.md` §4.1 依赖边清单**逐行未改**（PM 应 `git diff` 确认该段无 diff）。
- [ ] **A6 无代码**：三文档增量**不含任何函数体 / 伪代码实现**（IFC 签名为 `name: type` 声明式，合规）。
- [ ] **A7 凭据纪律**：全包与落盘结果**不含任何口令 / 令牌 / Key / 证书字面量**——仅键名 / 头名 / 表名 / 字段名 / 文件层名 / 结果码。
- [ ] **A8 未越界**：`requirements_spec.md`、`user_stories.md`、`phase_status.md`、`src/**`、`tests/**`、`implementation_plan.md` 及 C/D 阶段文档**均未触碰**；FreeArk **只读未改**。

## D.3 producer 静态自检（4 维，落盘前）

| 维度 | 结论 |
|------|------|
| **输入锚定** | 每个 ADR 的 Context 均引 REQ-*（ADR-37: IB-44/45；ADR-38: IB-47/NFR-20/C-IB-42；ADR-39: IB-47/NFR-20；ADR-40: IB-45/46/31；ADR-41: IB-48/C-IB-43；ADR-42: IB-43）；tech_stack 修订行均带 REQ-* 与 ADR-* 溯源；无无依据决策 |
| **逻辑一致** | ADR 选型互不冲突（分层单体 / SQLite / 复用既有端口纪律）；模块依赖图仍为 DAG（§4.2.8 再声明）；tech_stack 修订与架构决策一致（ADR-38 ↔ 凭据口径） |
| **需求覆盖** | REQ-FUNC **48/48**（IB-43~48 各落主模块）；NFR **20**（NFR-20 落 MOD-IB-11/23）；无缺口 |
| **格式合规** | 三文档均有合规 file_header；每个 ADR 五要素（Context/Options/Decision/Status/Consequences）齐备、Options **≥2**（含已评估未采纳项）；每个模块含 ID/职责/接口契约/依赖；**无代码实现** |

## D.4 OPEN ITEMS / ASSUMPTION 汇总（须在 GR-B 门控记录）

| 编号 | 事项 | 落点 | 处置 |
|------|------|------|------|
| **OI-1** | ADR-21「账户↔项目 1:1」与 OQ-IB-28「1:N、零迁移」的口径张力 | `architecture_design.md` §2.0.9 / §10.1 | **登记不裁决**；架构侧**不自行改写 ADR-21**；若判需修订，另出 ADR-21-R1 |
| **OI-2** | LLM Key **首启供给序**（沿用 fail-fast 则死锁） | `architecture_design.md` §10.1；ADR-39 | 架构侧给 **ADR-39 Option C**（未配置态 fail-closed）；**待用户 / PM 二选一**（Option B 部署期用户手工预置为备选） |
| **OI-3** | LLM Key **掩码字面** | `architecture_design.md` §10.1 | 口径已收敛到「无明文可分」；具体掩码字面**由用户在施工期定** |
| **[ARCH-ASSUMPTION-A12]** | LLM 未配置态启动语义 + 库文件 0600 / 属主 + 掩码口径 | `architecture_design.md` §8 | **需 PM 知悉**；与 [TBD-T27] 同源 |
| **[TBD-T26]** | 项目注册表规模 / 查询开销 / 播种耗时 | `architecture_design.md` §9 | 目标机实测后定索引 / 分页 |
| **[TBD-T27]** | LLM Key 库文件实际 mode / owner + 写入时延 | `architecture_design.md` §9 | 真机验证（检查清单 B22） |

## D.5 生产事实登记（写入交付说明，**不得设计为代理自动执行**）

- **生产后端重启**与**首次环境变量配置**须**由用户执行**（本轮特别登记）。本包所有「重启后生效」的口径，一律写作「**由用户手工执行 `ib-web` / `ib-worker` 重启**」；ADR-32（保存 + 服务重启重装配）**生效口径不变**。
- LLM Key **唯一写入口** = `PUT /api/llm-key`；`.env` 的 `IB_LLM_API_KEY` **停止作为 Key 来源**；承载**库文件 0600 且属主对齐服务账号**。

---

**Part C / Part D 结束。** 全包共 3 文件、36 处 EDIT。请 PM 按 D.1 顺序机械落盘，并以 D.2 逐项强校验。
