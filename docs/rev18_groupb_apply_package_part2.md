# REV-18 GROUP_B Apply-Ready 包（Part B：`docs/module_design.md` 增量）

```xml
<apply_ready_package_part>
  <artifact>module_design</artifact>
  <target_file>docs/module_design.md</target_file>
  <revision>REV-18</revision>
  <producer>system-architect</producer>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
  <date>2026-10-07</date>
  <edits>EDIT-MOD-01 ~ EDIT-MOD-20（共 20 处）</edits>
</apply_ready_package_part>
```

> 目标文档当前状态：**v1.9.0 / REV-17**（§2.2 端口 17、末条 IFC-IB-365、§11 末块为 REV-17 自检）。
> **本件含 20 处 EDIT**（主包 §1 索引中的「EDIT-MOD-01 ~ 16」为**估算**；**以此 20 处为准**）。**按编号升序落盘**；各 `ANCHOR` 在本件内**互不重叠**，故可顺序执行。
> **零新增模块**（仍 MOD-IB-01 ~ 26，共 26 个）；**端口 17 → 19（纯追加）**；新增 IFC **IFC-IB-366 ~ 377**；**§4.1 依赖边逐行不变（零新增边）**。

---

## ■ EDIT-MOD-01 — `file_header` 版本 / 修订号 / 调用号

**位置**：文档最前端 `file_header`（第 6、7、11 行）。

**ANCHOR（old_string）**：
```
  <version>1.9.0</version>
  <revision>REV-17</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04 模块详细设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-011</invocation_id>
```

**REPLACE（new_string）**：
```
  <version>1.10.0</version>
  <revision>REV-18</revision>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / PHASE_04 模块详细设计</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-012</invocation_id>
```

---

## ■ EDIT-MOD-02 — `file_header/inputs` 输入指针同步

**位置**：`file_header/inputs`（第 46 ~ 48 行）。

**ANCHOR（old_string）**：
```
    <input path="docs/requirements_spec.md" version="1.7.0" revision="REV-16-3" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.8.0" revision="REV-16-4" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.9.0" revision="REV-17" status="DRAFT_FOR_GATE_REVIEW"/>
```

**REPLACE（new_string）**：
```
    <input path="docs/requirements_spec.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <input path="docs/user_stories.md" version="1.10.0" revision="REV-18-2" status="APPROVED"/>
    <input path="docs/architecture_design.md" version="1.10.0" revision="REV-18" status="DRAFT_FOR_GATE_REVIEW"/>
```

---

## ■ EDIT-MOD-03 — `revision_history` 追加 REV-18 条目

**位置**：`revision_history` 内，REV-17 条目（`<rev no="REV-17" …>`）之后、`</revision_history>` 之前。

**ANCHOR（插入点边界，逐字）**：REV-17 条目末句与其后的闭合标签：
```
    </rev>
  </revision_history>
```

**INSERT（在 `</rev>` 与 `</revision_history>` 之间插入）**：
```
    <rev no="REV-18" date="2026-10-07" by="system-architect" invocation_id="INV-GROUP_B-INTELBASE-012" basis="GROUP_A REV-18-2 下游贯通（系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传：REQ-FUNC-IB-43~48 / REQ-NFR-IB-20 / C-IB-42 / C-IB-43 / OOS-17~19 / DR-20 / DR-21；用户裁决 2026-10-07：OQ-IB-25~31 一次拍板）；上游 architecture_design.md 1.10.0（REV-18），对应 ADR-37~42 / §2.0.9">
      **不新增模块、不新增依赖边**（模块数仍 **26**，**§4.1 依赖边清单逐行未改（零新增边）**，DAG 无环，§4.2.8 再声明）：**端口 17 → 19**（纯追加）—— 第 18 个端口 `ProjectRegistryStore`（IFC-IB-367，**ADR-37**）与第 19 个端口 `LlmKeyStore`（IFC-IB-368，**ADR-38**），**均定义于 MOD-IB-01（L0）**。**类型化契约落点**：端口与结构（`ProjectRegistryEntry` / `ProjectStatus` / `LlmKeyStatus` / `update_user`，IFC-IB-366~368）→ **MOD-IB-01**；REV-18 键名登记与启动校验口径（`IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND`；**LLM Key 未配置非致命**，IFC-IB-369）→ **MOD-IB-02**；SQL 适配器与 DDL 单源（`005_projects.sql` / `006_llm_key.sql`，IFC-IB-370 / 371）→ **MOD-IB-11**（**同一 SQLite 台账与同一手写 scoped 迁移机制**；**库文件 0600 且属主对齐服务账号**）；项目 CRUD / 账号扩展 / LLM Key 端点 / 上传项目域化与装配期解析（IFC-IB-372~375）→ **MOD-IB-23**；系统管理三分 IA 与项目域上传视图（IFC-IB-376）→ **MOD-IB-24**；迁移 `005` / `006` 与部署检查清单 B21~B23（IFC-IB-377）→ **MOD-IB-25**。新增 IFC 编号 **366 ~ 377**（12 条，全部类型化、frozen dataclass / Protocol / 纯 stdlib、零第三方依赖；**IFC-IB-285 仍预留未分配**；既有重号 IFC-IB-131 **登记不修**）。**既有 `IFC-IB-001 ~ 365` 的号 / 名 / 签名一字不动** —— **仅 7 条文字与取值口径修订**（`IFC-IB-024` / 242 / 243 / 262 / 263 / 321 / 333，逐条登记于 **§2.2.9**）。**计数同步**：REQ-FUNC **42/42 → 48/48**（新增 IB-43~48，§9.1）、NFR **19 → 20**（新增 NFR-20，§9.2）。**红线未破（强制）**：`kb_id` **由已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`），**请求体不再接收 kb 字段**，**保留** `LedgerRepository.assert_kb_in_project`（IFC-IB-130）归属断言，失败仍 **403**（ADM-41；不削弱 `architecture_design.md:120`「范围不可由客户端自证」）。**「UI 分组不是权限机制」**：系统管理三分（IFC-IB-376）**仅体验优化**，非 admin 一律**服务端 403**（ADR-42；授权唯一经注入的 `AuthzPolicy`）。**生效口径未变**：**保存 + 服务重启重装配**（ADR-32 / C-IB-40 / OOS-16），**不引运行期热重载**；**登记：生产后端重启与首次环境变量配置须由用户执行**。**凭据纪律（新增）**：LLM Key **载体 = DB**（**不入 `.env` / 不进 git / 不进命令行**）；**唯一写入口** = `PUT /api/llm-key`；HTTP 只回 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），**不回显明文为类型层事实**；`masked` 为**不含明文任何前 / 后缀字符的固定占位掩码**。增补位置：§1 REV-18 补充纪律段、§2.2 端口行与增记、§2.2.9 REV-18 IFC 段号索引与文字修订索引、§3 的 MOD-IB-01 / 02 / 11 / 23 / 24 / 25 增补、§4.2.8 无环性再声明、§5 装配表行与说明、§8 替身行与离线可测单元、§9.1 六行 + §9.2 一行 + §9.11 覆盖率再声明、§11 自检。**OPEN ITEM**：OI-1（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力，登记不裁决）/ OI-2（LLM Key 首启供给序）/ OI-3（掩码字面）—— 见 `architecture_design.md` §10.1。需求侧文档只读；未修改 FreeArk 任何文件；未写入任何口令 / 令牌 / 密钥字面量（只登记键名 / 表名 / 文件层名 / 头名）。
    </rev>
```

---

## ■ EDIT-MOD-04 — 标题下版次行更新

**位置**：`# 模块详细设计 — intelligentbase` 之后的版次行（第 57 行）。

**ANCHOR（old_string）**：
```
**版本**: 1.8.0 (REV-16-4) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-06
```

**REPLACE（new_string）**：
```
**版本**: 1.10.0 (REV-18) | **状态**: DRAFT_FOR_GATE_REVIEW | **日期**: 2026-10-07
```

---

## ■ EDIT-MOD-05 — §1 追加「REV-18 补充纪律与性质」段

**位置**：§1 现有补充纪律段的最后一段（R14 补充纪律段，第 119 行）之后。

**ANCHOR（old_string，R14 段末句）**：
```
**追踪**：IFC-IB-333 / 334 服务 REQ-FUNC-IB-31 / IB-32（admin 全局 / ops 项目边界）与 US-IB-24 / AC-IB-24-03；对其余需求的映射见 §9.8。
```

**REPLACE（new_string，R14 段末句 + REV-18 段）**：
```
**追踪**：IFC-IB-333 / 334 服务 REQ-FUNC-IB-31 / IB-32（admin 全局 / ops 项目边界）与 US-IB-24 / AC-IB-24-03；对其余需求的映射见 §9.8。

**REV-18 补充纪律与性质（系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量；ADR-37 ~ ADR-42）**：REV-18 **零新增模块**（仍 **MOD-IB-01 ~ MOD-IB-26**，共 26 个）、**零新增依赖边**；**端口 17 → 19**（**纯追加**）：第 18 个端口 `ProjectRegistryStore`（IFC-IB-367，`load` / `list_active` / `create` / `update` / `disable` 方法集）、第 19 个端口 `LlmKeyStore`（IFC-IB-368，`get` / `set` / `clear` 方法集），**均定义于 MOD-IB-01（L0）**。新增工件并入既有模块：契约与端口 → **MOD-IB-01**；键名登记与启动校验口径（IFC-IB-369）→ **MOD-IB-02**；SQL 适配器与 DDL 单源（IFC-IB-370 / 371）→ **MOD-IB-11**（**复用同一 SQLite 台账与手写 scoped 迁移机制**；新增迁移 `005_projects.sql` / `006_llm_key.sql`）；项目 CRUD / 账号扩展 / LLM Key 端点 / 上传项目域化（IFC-IB-372 ~ 375）→ **MOD-IB-23**；系统管理三分 IA 与项目域上传视图（IFC-IB-376）→ **MOD-IB-24**；迁移与检查清单 B21 ~ B23（IFC-IB-377）→ **MOD-IB-25**。**编号即拓扑序的边界情形**在本轮**再次适用**：项目注册表 / LLM Key 的装载与解析**必然被组合根 `MOD-IB-23` 依赖 / 承载**，若新开模块只能取 **≥27** 编号 → 产生 `23 → 27` 边，**违反 `w(A) > w(B)`，构造性无环证明失效**（该先例 R7 已就 `MOD-IB-27` 否决；见 §4.2.8）。**红线纪律（强制）**：① 项目域资料的 `kb_id` **由已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`），**请求体不再接收 kb 字段**，且 **保留** `assert_kb_in_project`（IFC-IB-130）归属断言（失败 `403`）—— **不削弱** `architecture_design.md:120`「范围不可由客户端自证」（ADR-41 / C-IB-43）；② **UI 分组不是权限机制** —— 系统管理三分的导航可见性**仅体验优化**，授权判定**唯一经注入的 `AuthzPolicy`**，非 admin 一律**服务端 403**（ADR-42；ADR-22 复用）。**生效口径未变**：**保存 + 服务重启重装配**（ADR-32 / C-IB-40 / OOS-16），**不引运行期热重载**；**登记：生产后端重启与首次环境变量配置须由用户执行**。
```

---

## ■ EDIT-MOD-06 — §2.2 端口表新增 2 行（端口 17 → 19）

**位置**：§2.2 端口清单表末行（`| \\`ConfigAuditStore\\`（**REV-16-4 新增**） … |`）之后。

**ANCHOR（old_string，表末行，逐字）**：
```
| `ConfigAuditStore`（**REV-16-4 新增**） | 2 | IFC-IB-357（端口）+ IFC-IB-356（结构） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-11（生产实现）/ §3 MOD-IB-23（装配与端点） |
```

**REPLACE（new_string，表末行 + 2 新行）**：
```
| `ConfigAuditStore`（**REV-16-4 新增**） | 2 | IFC-IB-357（端口）+ IFC-IB-356（结构） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-11（生产实现）/ §3 MOD-IB-23（装配与端点） |
| `ProjectRegistryStore`（**REV-18 新增**） | 5 | IFC-IB-367（端口）+ IFC-IB-367（结构 `ProjectRegistryEntry` / `ProjectStatus`） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-11（生产实现）/ §3 MOD-IB-23（装配与端点） |
| `LlmKeyStore`（**REV-18 新增**） | 3 | IFC-IB-368（端口）+ IFC-IB-368（结构 `LlmKeyStatus`） | §3 MOD-IB-01（端口与结构）/ §3 MOD-IB-11（生产实现）/ §3 MOD-IB-23（装配与端点） |
```

---

## ■ EDIT-MOD-07 — §2.2 增补段（REV-18 增记，第 18 / 19 个端口）

**位置**：§2.2 增记段末（REV-16-4 增记段，第 222 行）之后、「方法数订正说明」（第 224 行）之前。

**ANCHOR（old_string，REV-16-4 增记段末句）**：
```
所有需要「查配置保存记录」的路径**不得**各自读表，一律经**组合根**装配注入的 `ConfigAuditStore` **唯一入口**（同 `CollectionResolver` / `DefinitionDocumentStore` 精神）。
```

**REPLACE（new_string，REV-16-4 增记段末句 + REV-18 增记段）**：
```
所有需要「查配置保存记录」的路径**不得**各自读表，一律经**组合根**装配注入的 `ConfigAuditStore` **唯一入口**（同 `CollectionResolver` / `DefinitionDocumentStore` 精神）。

**REV-18 增记（第 18 / 19 个端口）**：`ProjectRegistryStore`（IFC-IB-367）为**第 18 个端口**（17 → 18，**纯追加**，**5 方法**：`load` / `list_active` / `create` / `update` / `disable`），`LlmKeyStore`（IFC-IB-368）为**第 19 个端口**（18 → 19，**纯追加**，**3 方法**：`get` / `set` / `clear`）。**工件分别不同**：`ProjectRegistryStore` 管**项目注册表**（运行期可变状态：项目 CRUD + 软删 / 停用），与 `LedgerRepository`（项目 / 知识库 / 文档 / 块元数据）**表不同、职责不同**；`LlmKeyStore` 管**单一全局 LLM Key**（**单行表，以结构保证全局唯一**，OOS-18 为扩展点预留），与 `AccountStore`（账户 / 会话）**工件不同**。**二者与 `LedgerRepository` / `AccountStore` / `ConfigAuditStore` 共用同一 SQLite 文件与同一手写 scoped 迁移机制**（`005_projects.sql` / `006_llm_key.sql`；ADR-18 / ADR-26 复用）。**唯一入口纪律**：① 项目枚举（`GET /api/projects`，IFC-IB-333）**数据源由配置枚举切换为注册表**（登记型口径修订；端点号 / 名 / 签名与 fail-closed 语义一字不动），所有需要「按项目 id 校验存在性 / 取活动项目」的路径**不得**各自读配置或各自建表，一律经**组合根**装配注入的 `ProjectRegistryStore` **唯一入口**；② LLM Key 的**装配期读取为唯一读点**（经 `resolve_secret()`；ADR-38），HTTP 层**只写不读明文**，一律经**组合根**装配注入的 `LlmKeyStore` **唯一入口**。**凭据纪律**：`LlmKeyStore` 承载的**库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20）；HTTP 只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），**类型层不含明文字段**。**离线替身**：`MemoryProjectRegistryStore`（IFC-IB-370）/ `MemoryLlmKeyStore`（IFC-IB-371），经 `IB_PROJECT_REGISTRY_BACKEND=memory` / `IB_LLM_KEY_BACKEND=memory` 装配。
```

---

## ■ EDIT-MOD-08 — 新增 §2.2.9 REV-18 IFC 索引与文字修订索引

**位置**：§2.2.8 末（REV-17 编号规范段，第 363 行）之后、`## 3. 模块详情`（第 365 行）之前。

**ANCHOR（插入点边界，逐字；为 §2.2.8 末段）**：
```
以上 2 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**；**不含任何口令 / 令牌 / 密钥字面量，也不含任何配置取值**（只登记键名 / 头名 / 字段名 / 结果码）。

## 3. 模块详情
```

**REPLACE（new_string）**：
```
以上 2 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**；**不含任何口令 / 令牌 / 密钥字面量，也不含任何配置取值**（只登记键名 / 头名 / 字段名 / 结果码）。

### 2.2.9 REV-18 新增 IFC 索引（IFC-IB-366 ~ 377）与文字修订索引

| IFC 段 | 归属模块 | 内容 | 权威落点 |
|--------|----------|------|----------|
| IFC-IB-366 | MOD-IB-01 | `AccountStore.update_user(user_id: str, *, project_id: str \| None = None, username: str \| None = None, status: AccountStatus \| None = None) -> UserRecord \| None`（**加成式扩展** `AccountStore`；其**既有 13 方法文本不改**；**不接受 / 不回显任何口令 / 令牌**；`project_id` 重绑须目标项目存在且 `active`，由服务层校验） | §3 MOD-IB-01（本件） |
| IFC-IB-367 | MOD-IB-01 | **端口** `ProjectRegistryStore`（`Protocol`，5 方法：`load(project_id) -> ProjectRegistryEntry \| None` / `list_active() -> tuple[ProjectRegistryEntry, ...]` / `create(entry) -> ProjectRegistryEntry` / `update(entry) -> ProjectRegistryEntry \| None` / `disable(project_id) -> ProjectRegistryEntry \| None`）+ **结构** `ProjectRegistryEntry(project_id: str, name: str, status: ProjectStatus, created_at: str, updated_at: str)` / `ProjectStatus = Literal["active","disabled"]`（**frozen dataclass / Literal，纯 stdlib，无实现体**） | §3 MOD-IB-01（本件） |
| IFC-IB-368 | MOD-IB-01 | **端口** `LlmKeyStore`（`Protocol`，3 方法：`get() -> LlmKeyRecord \| None` / `set(secret) -> LlmKeyStatus` / `clear() -> None`）+ **结构** `LlmKeyStatus(configured: bool, masked: str, updated_at: str \| None)` / `LlmKeyRecord(secret: str, updated_at: str)`（**`LlmKeyRecord.secret` 仅用于装配期解析，绝不进入任何响应类型**；**frozen dataclass，纯 stdlib，无实现体**） | §3 MOD-IB-01（本件） |
| IFC-IB-369 | MOD-IB-02 | REV-18 配置**键名登记与启动校验口径**（**仅登记键名，不含任何值**）：`IB_PROJECT_REGISTRY_BACKEND`（取值 `sqlite` 默认 / `memory`）；`IB_LLM_KEY_BACKEND`（取值 `sqlite` 默认 / `memory`）；**启动校验口径修订**：`LlmConfig` 的 `api_key_env`（IFC-IB-024）**语义降级**为「历史 / 兼容登记」——**LLM Key 未配置非致命**（`configured=false`，服务可启动；LLM 依赖路径 **fail-closed** 于调用期）；**其余必填项仍 fail-fast** | §3 MOD-IB-02（本件） |
| IFC-IB-370 | MOD-IB-11 | `SqliteProjectRegistryStore`（实现 IFC-IB-367）：**同一 SQLite 台账**的 `projects` 表适配器（**DDL 单源 = 手写迁移 `005_projects.sql`**，IFC-IB-377）；软删 = 置 `status="disabled"`（**不删行**）；**装配期幂等首次播种**（以 `IB_CONFIG_FILE.projects.<id>` 为初始数据，`INSERT … ON CONFLICT DO NOTHING` 语义，**不覆盖既有行**）；`MemoryProjectRegistryStore`（离线替身，同一端口一致性测试） | §3 MOD-IB-11（本件） |
| IFC-IB-371 | MOD-IB-11 | `SqliteLlmKeyStore`（实现 IFC-IB-368）：**同一 SQLite 台账**的 `llm_key` 表适配器（**DDL 单源 = 手写迁移 `006_llm_key.sql`**，IFC-IB-377；**单行表** `llm_key(id INTEGER PRIMARY KEY CHECK(id=1), secret TEXT NOT NULL, updated_at TEXT NOT NULL)`，**以结构保证全局唯一**）；**承载库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；部署检查清单 B22）；**WAL + `busy_timeout` 必开**；`MemoryLlmKeyStore`（离线替身） | §3 MOD-IB-11（本件） |
| IFC-IB-372 | MOD-IB-23 | 项目 CRUD 端点族（**仅 `admin`**，非 admin 一律 `403`）：`GET /api/projects`（**数据源切换**为注册表；登记型口径修订，端点号 / 名 / 签名不变）→ `200 {items: list[ProjectSummary]}`；`POST /api/projects`（`{project_id, name}`）→ `201 ProjectRegistryEntry` \| `409`（`project_id` 冲突）\| `400`；`PATCH /api/projects/{project_id}`（`{name?, status?}`）→ `200 ProjectRegistryEntry` \| `404` \| `400`；`DELETE /api/projects/{project_id}`（**二次确认**：`confirm_project_id` 与目标一致，否则 `400`）→ `200 ProjectRegistryEntry`（**软删 = `status="disabled"`，不物理级联**，OOS-19）\| `404` \| `403`；**全程仅 `Authorization` 头，不接受 `?token=`** | §3 MOD-IB-23（本件） |
| IFC-IB-373 | MOD-IB-23 | 账户扩展端点（**仅 `admin`**）与顺序依赖：`PATCH /api/accounts/{user_id}`（`{project_id?, username?, status?}`；**不回显任何凭据**）→ `200 AccountSummary` \| `404` \| `400` \| `403`；`DELETE /api/accounts/{user_id}`（**二次确认** `confirm_username`，否则 `400`；**禁删 `admin` 或最后一个有效 `admin`** → `409`）→ `200 AccountSummary`（**软删 = `status="disabled"`**）\| `404` \| `403`；**`POST /api/accounts` 增前置**：目标 `project_id` 须在注册表存在且 `active`，否则 `422`（**顺序依赖：先建项目、后建账号**，REQ-FUNC-IB-45）；`AccountStore` 端口**方法集不变**（软删复用 `set_status`；编辑经 IFC-IB-366 `update_user`；**「最后管理员」判定在服务层**） | §3 MOD-IB-23（本件） |
| IFC-IB-374 | MOD-IB-23 | LLM Key 端点（**仅 `admin`**）：`GET /api/llm-key` → `200 LlmKeyStatus`（`configured` / `masked` / `updated_at`；**不含明文**）\| `403`；`PUT /api/llm-key`（`{secret}`；**唯一写入口**）→ `200 LlmKeyStatus`（**不回显明文**）\| `400`（空值）\| `403`；`DELETE /api/llm-key` → `204`（清空单行）\| `403`。**装配期解析**：组合根经 `LlmKeyStore.get()` → `resolve_secret()`（**唯一读点**）；`configured=false` 时**服务正常启动**，LLM 依赖路径 **fail-closed**（`DependencyUnavailableError`-类，**不含任何 Key 信息**；ADR-39）；**生效 = 保存 + 服务重启重装配**（ADR-32；**重启由用户手工执行**）；错误体**不回显明文 / 掩码 / 前缀** | §3 MOD-IB-23（本件） |
| IFC-IB-375 | MOD-IB-23 | 上传 / 台账端点的**项目域化**（登记型口径修订，行号不变）：`POST /api/files`（IFC-IB-242）/ `GET /api/files`（IFC-IB-243）等**请求体不再接收 kb 字段**；`kb_id` **由已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`）；**保留** `LedgerRepository.assert_kb_in_project(project_id, kb_id)`（IFC-IB-130）**归属断言**，失败仍 **403**（**不因「是不是你的」区分 404**）——**不削弱** `architecture_design.md:120`「范围不可由客户端自证」（ADR-41 / C-IB-43） | §3 MOD-IB-23（本件） |
| IFC-IB-376 | MOD-IB-24 | **前端系统管理三分 IA 与项目域上传视图**：父级导航「**系统管理**」下挂三子项（**账户管理** / **项目管理** / **LLM Key 管理**）；**资料管理**保持**独立顶级**，视图由「知识库」改为「**项目域**」；新增**项目管理页**（项目 CRUD + 软删二次确认）与 **LLM Key 管理页**（写入 / 清除；**只显示 `configured` / `masked` / `updated_at`，不回显明文**，**不显示任何「重启后生效」以外的即时生效暗示**）；**授权与导航解耦（强制）**：UI 分组可见性**仅体验优化**，**非 admin 的服务端 `403` 为唯一裁决者**（ADR-42）；**生效口径显式提示**：「保存成功；**重启 `ib-web` / `ib-worker` 后生效**，重启由用户手工执行」 | §3 MOD-IB-24（本件） |
| IFC-IB-377 | MOD-IB-25 | 交付物：手写迁移 **`005_projects.sql`**（前向、幂等：`CREATE TABLE IF NOT EXISTS projects …` + 索引）与 **`006_llm_key.sql`**（单行表 + `CHECK(id=1)`）；部署检查清单**新增 B21 ~ B23**（**B21** 项目注册表迁移幂等可前向可回滚；**B22** LLM Key 承载**库文件 0600 且属主对齐服务账号**；**B23** LLM Key **不入 `.env` / 不进 git / 不进命令行**，`grep` 零命中） | §3 MOD-IB-25（本件） |

**REV-18 文字修订索引（7 条；只改文字与取值口径，号 / 名 / 签名一字不动）**：

| IFC | 修订内容 |
|-----|----------|
| `IFC-IB-024` | `LlmConfig.api_key_env` **语义降级**为「历史 / 兼容登记」——LLM Key 来源改由 DB 装配期解析（ADR-38 / ADR-39）；字段名与类型不变 |
| `IFC-IB-242` | `POST /api/files` **请求体不再接收 kb 字段**；`kb_id` 由已认证主体的 `project_id` 推导；**保留** `assert_kb_in_project` 归属断言（失败 `403`）；端点号 / 名 / 签名不变 |
| `IFC-IB-243` | `GET /api/files` 同上：**请求体 / 查询串不再接收 kb 字段**；`kb_id` 由已认证主体的 `project_id` 推导；端点号 / 名 / 签名不变 |
| `IFC-IB-262` | `.env.example` 模板**凭据纪律收窄**：`.env` **仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**；新增键名 `IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND`（**只登记键名**） |
| `IFC-IB-263` | 启动期校验**口径修订**：**LLM Key 未配置非致命**（fail-closed 于调用期，ADR-39）；**其余必填项仍 fail-fast**；「只报键名、不回显值、非零码退出」纪律不变 |
| `IFC-IB-321` | 账户端点族**补齐** `PATCH /api/accounts/{user_id}` / `DELETE /api/accounts/{user_id}`（软删 + 二次确认 + 禁删 admin 与最后管理员）；`POST /api/accounts` **增前置**（目标项目须存在且 `active`）；**号 / 名 / 既有方法签名不变** |
| `IFC-IB-333` | `GET /api/projects` **数据源**由配置枚举 `Deps.projects` 改为**项目注册表**（ADR-37）；**端点号 / 名 / 签名与 fail-closed 语义不变** |

**REV-18 编号规范（强制，延续 R2 / R7 / R8 / R13 / R14 / REV-16-2 / REV-16-4 / REV-17）**：新增号只许**追加**（本轮取 **366 ~ 377**）；`IFC-IB-001 ~ 365` 的**号 / 名 / 签名一字不动**（**仅上表 7 条文字与取值口径修订**，逐条登记）；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。**端口 17 → 19（纯追加）**；**模块数不变（26）**；**零新增依赖边**。以上 12 条 IFC 全部为**类型化契约**（`name: type` + 可空性），**不含任何实现体**；**不含任何口令 / 令牌 / 密钥字面量，也不含任何配置取值**（只登记键名 / 头名 / 表名 / 字段名 / 文件层名 / 结果码）。

## 3. 模块详情
```

---

## ■ EDIT-MOD-09 — MOD-IB-01 增补（IFC-IB-366 ~ 368）

**位置**：MOD-IB-01 详情内，`IFC-IB-361` 条目（第 425 行）之后、`- **依赖模块**: 无`（第 427 行）之前。

**ANCHOR（插入点边界，逐字）**：
```
- **依赖模块**: 无
- **外部依赖**: 无

### MOD-IB-02 配置 (L0)
```

**REPLACE（new_string）**：
```
  - **IFC-IB-366（REV-18 新增）**: `AccountStore.update_user(user_id: str, *, project_id: str | None = None, username: str | None = None, status: AccountStatus | None = None) -> UserRecord | None`（**加成式扩展** `AccountStore`，其**既有 13 方法文本一字不改**；**不接受 / 不回显任何口令 / 令牌**；`project_id` 重绑的目标项目须**存在且 `active`**，由**服务层**校验 —— 端口层不做跨表断言）。
  - **IFC-IB-367（REV-18 新增）**: 端口 `ProjectRegistryStore`（`Protocol`，**5 方法**：`load(project_id: str) -> ProjectRegistryEntry | None` / `list_active() -> tuple[ProjectRegistryEntry, ...]` / `create(entry: ProjectRegistryEntry) -> ProjectRegistryEntry` / `update(entry: ProjectRegistryEntry) -> ProjectRegistryEntry | None` / `disable(project_id: str) -> ProjectRegistryEntry | None`）+ 数据结构 `ProjectRegistryEntry(project_id: str, name: str, status: ProjectStatus, created_at: str, updated_at: str)`、`ProjectStatus = Literal["active","disabled"]`。**frozen dataclass / Literal，纯 stdlib、零第三方依赖**；**无实现体**（生产实现见 MOD-IB-11）。
  - **IFC-IB-368（REV-18 新增）**: 端口 `LlmKeyStore`（`Protocol`，**3 方法**：`get() -> LlmKeyRecord | None` / `set(secret: str) -> LlmKeyStatus` / `clear() -> None`）+ 数据结构 `LlmKeyStatus(configured: bool, masked: str, updated_at: str | None)`、`LlmKeyRecord(secret: str, updated_at: str)`。**类型层事实**：`LlmKeyRecord.secret` **仅用于装配期解析**（组合根唯一读点），**绝不进入任何 HTTP 响应类型**；`LlmKeyStatus` **不含明文字段**（对外只承载 `configured` / `masked` / `updated_at`）。**frozen dataclass，纯 stdlib、零第三方依赖**；**无实现体**（生产实现见 MOD-IB-11）。

- **依赖模块**: 无
- **外部依赖**: 无

### MOD-IB-02 配置 (L0)
```

---

## ■ EDIT-MOD-10 — MOD-IB-02 增补（IFC-IB-369）

**位置**：MOD-IB-02 详情内，`IFC-IB-364` 条目（第 469 行）之后、`### MOD-IB-03 请求上下文 (L0)` 之前。

**ANCHOR（插入点边界，逐字）**：
```
### MOD-IB-03 请求上下文 (L0)
```

**REPLACE（new_string）**：
```
  - **IFC-IB-369（REV-18 新增）**: REV-18 配置**键名登记与启动校验口径**（**仅登记键名，不含任何值**）：
    - `IB_PROJECT_REGISTRY_BACKEND`：项目注册表存储后端，取值 `sqlite`（默认）或 `memory`（离线 / 测试替身）。
    - `IB_LLM_KEY_BACKEND`：LLM Key 存储后端，取值 `sqlite`（默认）或 `memory`（离线 / 测试替身）。
    - **启动校验口径修订（登记型）**：`LlmConfig.api_key_env`（IFC-IB-024）**语义降级**为「历史 / 兼容登记」—— **LLM Key 未配置非致命**（`configured=false`，服务可启动；LLM 依赖路径 **fail-closed** 于调用期，ADR-39）；**其余必填配置项仍 fail-fast**；`.env` **仅保留非 LLM Key 的其他密钥**（REQ-NFR-IB-20）。

### MOD-IB-03 请求上下文 (L0)
```

---

## ■ EDIT-MOD-11 — MOD-IB-11 增补（IFC-IB-370 / 371）

**位置**：MOD-IB-11 详情内，`IFC-IB-358` 条目（第 612 行）与「依赖模块 / 外部依赖」行（第 613 ~ 614 行）之后、`### MOD-IB-12 原文件 BlobStore (L3)` 之前。

**ANCHOR（插入点边界，逐字）**：
```
### MOD-IB-12 原文件 BlobStore (L3)
```

**REPLACE（new_string）**：
```
  - **IFC-IB-370（REV-18 新增）**: `SqliteProjectRegistryStore`（实现 `ProjectRegistryStore`，IFC-IB-367）：**同一 SQLite 台账**的 `projects` 表适配器（**DDL 单源 = 手写迁移 `005_projects.sql`**，IFC-IB-377；沿用 IFC-IB-313 的「适配器 ↔ 迁移单源」先例）。**软删 = 置 `status="disabled"`（不删行）**；**装配期幂等首次播种**：以 `IB_CONFIG_FILE.projects.<id>` 为初始数据（沿用 `_seed_projects` 语义），`INSERT … ON CONFLICT DO NOTHING`（**不覆盖既有注册表行**）。**纪律**：**WAL + `busy_timeout` 必开**（沿用 MOD-IB-11 既有约束）；表内**只承载项目标识 / 名称 / 状态 / 时间戳，不承载任何凭据 / 配置取值**。**离线替身** `MemoryProjectRegistryStore`（同一端口一致性测试）。**advisory（非强制）**：注册表与文档 / 账户 / 审计表**逻辑分区**（表名前缀 / 仓库内分文件）。
  - **IFC-IB-371（REV-18 新增）**: `SqliteLlmKeyStore`（实现 `LlmKeyStore`，IFC-IB-368）：**同一 SQLite 台账**的 `llm_key` 表适配器（**DDL 单源 = 手写迁移 `006_llm_key.sql`**，IFC-IB-377）；**单行表**（`CHECK(id=1)`，**以结构保证全局唯一**，OOS-18 为扩展点预留）。**承载库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20；检查清单 B22）；**WAL + `busy_timeout` 必开**；**明文只可经 `get()` 供组合根装配期解析，绝不写入任何日志 / 响应 / 审计**（ADR-38）。**离线替身** `MemoryLlmKeyStore`（同一端口一致性测试）。

### MOD-IB-12 原文件 BlobStore (L3)
```

> **注**：本轮 MOD-IB-11 的「覆盖需求」行与「依赖模块 / 外部依赖」行**不改**（SQLite / bcrypt 既有依赖不变；无新第三方）。

---

## ■ EDIT-MOD-12 — MOD-IB-23 增补（IFC-IB-372 ~ 375）

**位置**：MOD-IB-23 详情内，REV-16-4 段（第 830 行）之后、`### MOD-IB-24 Web 前端 (L5)`（第 832 行）之前。

**ANCHOR（插入点边界，逐字）**：
```
### MOD-IB-24 Web 前端 (L5)
```

**REPLACE（new_string）**：
```
- **REV-18 新增端点与装配扩展（系统管理 / 项目 / LLM Key / 项目域上传；全程仅 `Authorization` 头，不接受 `?token=`；ADR-37~42）**:
  - IFC-IB-372（**项目 CRUD**，**仅 `admin`**；非 admin 一律 `403`）：**数据源切换**——`GET /api/projects` 由组合根 `Deps.projects`（配置枚举快照）改为**项目注册表**（IFC-IB-367；**端点号 / 名 / 签名与 fail-closed 语义一字不动**）；`POST /api/projects`（`{project_id, name}`）→ `201 ProjectRegistryEntry` | `409`（`project_id` 冲突）| `400`；`PATCH /api/projects/{project_id}`（`{name?, status?}`）→ `200 ProjectRegistryEntry` | `404` | `400`；`DELETE /api/projects/{project_id}`（**二次确认** `confirm_project_id` 与目标一致，否则 `400`）→ `200 ProjectRegistryEntry`（**软删 = `status="disabled"`，数据保留、可恢复；不做物理级联删除**，OOS-19）| `404` | `403`。
  - IFC-IB-373（**账户扩展 + 顺序依赖**，**仅 `admin`**）：`PATCH /api/accounts/{user_id}`（编辑 `project_id?` / `username?` / `status?`；**不回显任何凭据**）→ `200 AccountSummary` | `404` | `400` | `403`；`DELETE /api/accounts/{user_id}`（**二次确认** `confirm_username` 与目标一致，否则 `400`；**禁删 `admin` 或最后一个有效 `admin`** → `409`）→ `200 AccountSummary`（**软删 = `status="disabled"`**）| `404` | `403`；**`POST /api/accounts`（IFC-IB-321）增前置**：目标 `project_id` 须在**项目注册表**存在且 `active`，否则 `422`（**顺序依赖：先建项目、后建账号**，REQ-FUNC-IB-45；**不静默创建无主账号**）。**`AccountStore` 端口方法集不变**（软删复用 `set_status`；编辑经 IFC-IB-366 `update_user`；**「最后管理员」判定在服务层**，非端口层）。**1:N / 零迁移**：**不**加 `users.project_id` 唯一约束（OQ-IB-28；**注**：与 ADR-21 的 1:1 表述存在口径张力，登记为 OPEN ITEM OI-1，**本件不自行改写 ADR-21**）。
  - IFC-IB-374（**LLM Key**，**仅 `admin`**）：`GET /api/llm-key` → `200 LlmKeyStatus`（`configured` / `masked` / `updated_at`；**不含明文**）| `403`；`PUT /api/llm-key`（`{secret}`；**唯一写入口**）→ `200 LlmKeyStatus`（**不回显明文**）| `400`（空值）| `403`；`DELETE /api/llm-key` → `204`（清空单行）| `403`。**装配期解析（唯一读点）**：组合根经 `LlmKeyStore.get()`（IFC-IB-368）取 `LlmKeyRecord.secret` → `resolve_secret()`；`configured=false` 时**服务正常启动**，LLM 依赖路径以 `DependencyUnavailableError`-类**可读错误 fail-closed**（**不含任何 Key 信息**；ADR-39）。**生效 = 保存 + 服务重启重装配**（ADR-32；**不引运行期热重载**；**重启由用户手工执行**）。**凭据纪律（强制）**：错误体 / 日志**不回显明文 / 掩码 / 前缀**；Key **不入 `.env` / 不进 git / 不进命令行**。
  - IFC-IB-375（**上传 / 台账项目域化**；登记型口径修订，端点号 / 名 / 签名 / 行号不变）：`POST /api/files`（IFC-IB-242）/ `GET /api/files`（IFC-IB-243）等**请求体不再接收 kb 字段**；`kb_id` **由已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`）；**保留** `LedgerRepository.assert_kb_in_project(project_id, kb_id)`（IFC-IB-130）**归属断言**，失败仍 **403**（**不因「是不是你的」区分 404**）——**不削弱** `architecture_design.md:120`「范围不可由客户端自证」（ADR-41 / C-IB-43）。既有 `kb_default` 数据迁移到归属项目 KB（随迁移家族交付；幂等、前向）。
  - **REV-18 装配序列扩展（显式化，任一步失败即拒绝装配）**：`装载配置（IFC-IB-369）→ 构造 ProjectRegistryStore（370）→ 幂等首次播种（370）→ 构造 LlmKeyStore（371）→ 解析 LLM Key（`resolve_secret`；未配置非致命，ADR-39）→ 构造并注入（MOD-IB-16 / 20 / 22）→ 图编译一次常驻`。**注册表播种与 Key 解析均不改变既有 R7 / R13 的装配前置顺序**（并列，互不短路）。
  - **REV-18 鉴权与凭据纪律（强制）**：沿用 IFC-IB-247 口径，**仅允许 `Authorization` 头 / 中间件鉴权**；全部新端点**不接受** `?token=`；**授权真源仍唯一**（注入的 `AuthzPolicy`，ADR-22）；**非 admin 一律服务端 `403`** —— **UI 分组不作为权限机制**（ADR-42）。

### MOD-IB-24 Web 前端 (L5)
```

---

## ■ EDIT-MOD-13 — MOD-IB-24 增补（IFC-IB-376）

**位置**：MOD-IB-24 详情内，REV-16-4 配置页内存态块（第 885 行）之后、`### MOD-IB-25 部署运维 (L5)` 之前。

**ANCHOR（插入点边界，逐字）**：
```
### MOD-IB-25 部署运维 (L5)
```

**REPLACE（new_string）**：
```
- **REV-18 系统管理三分 IA 与项目域上传约束（IFC-IB-376）**:
  - **信息架构**：父级导航「**系统管理**」下挂**三子项**（**账户管理** / **项目管理** / **LLM Key 管理**）；既有账户管理页**迁移**至子项；**资料管理**保持**独立顶级**，其视图由「知识库」改为「**项目域**」（对齐 ADR-41）。
  - **项目管理页**：项目 CRUD + **软删二次确认**（确认值 = 目标 `project_id`）；**软删**呈现为「**停用（数据保留、可恢复）**」，**不得**呈现为「永久删除」。
  - **LLM Key 管理页**：写入（`PUT`）/ 清除（`DELETE`）；界面**只显示** `configured` / `masked` / `updated_at`；**不得**回显明文 / 前缀 / 完整长度；**不得**呈现为「即时生效」——保存成功后**必须**提示「**保存成功；重启 `ib-web` / `ib-worker` 后生效**，**重启由用户手工执行**」（ADR-32 / C-IB-40 / C-IB-38）。
  - **项目域上传视图**：**移除**「知识库标识」输入框（REQ-FUNC-IB-48；`kb_id` 由服务端按已认证主体推导）；上传 / 列表页**不接收**用户输入的 kb 字段。
  - **授权与导航解耦（强制）**：三分导航的可见性 / 可点性**仅体验优化**；**授权判定唯一在服务端**（注入的 `AuthzPolicy`），**非 admin 的服务端 `403` 为唯一裁决者**；**不得**以导航隐藏替代服务端拒绝（ADR-42 / ADR-22）。
  - **路由**：`vue-router`（hash）**新增父级节点**「系统管理」，既有账户管理 hash **迁移**（**不引入 nginx `try_files` 回退**，ADR-23 精神）。
  - **凭据不回显 / 视图侧零持久化**：沿用 IFC-IB-296 / IFC-IB-354 / IFC-IB-363 口径 —— 只显示**键名 / 状态**，不显示任何值 / 掩码 / 前缀；**不得**以 `localStorage` / `IndexedDB` / 独立后端表充当真源。

### MOD-IB-25 部署运维 (L5)
```

---

## ■ EDIT-MOD-14 — MOD-IB-25 增补（IFC-IB-377）

**位置**：MOD-IB-25 详情内，R13 交付物块（第 912 行）之后、`### MOD-IB-26 ib-embed 服务端 (L2；服务端进程)` 之前。

**ANCHOR（插入点边界，逐字）**：
```
### MOD-IB-26 ib-embed 服务端 (L2；服务端进程)
```

**REPLACE（new_string）**：
```
- **REV-18 交付物（迁移 / 检查清单）**:
  - IFC-IB-377: 手写迁移 **`005_projects.sql`**（前向、幂等：`CREATE TABLE IF NOT EXISTS projects(project_id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)` + 索引）与 **`006_llm_key.sql`**（单行表：`CREATE TABLE IF NOT EXISTS llm_key(id INTEGER PRIMARY KEY CHECK(id=1), secret TEXT NOT NULL, updated_at TEXT NOT NULL)`）。经既有 `ibweb.bootstrap --ensure-schema`（`ExecStartPre`）应用。**回滚策略**：新表为**纯追加**，回滚 = **代码回滚**（旧代码忽略新表，无需破坏性 DDL）。
  - 部署检查清单**新增项 B21 ~ B23**（与 `src/deploy/checklists.txt` 同步）：
    - **B21** 项目注册表迁移**幂等可前向可回滚**：`005_projects.sql` 幂等重放无副作用；代码回滚后旧版本可正常启动（忽略新表）。
    - **B22** LLM Key 承载**库文件 mode 0600 且属主对齐服务账号**（`ls -l` 可复查；`stat` 断言 mode / owner）—— REQ-NFR-IB-20。
    - **B23** LLM Key **不入 `.env` / 不进 git / 不进命令行**：`IB_LLM_API_KEY` **不再作为 LLM Key 来源**；仓库与日志对 Key 字面量 `grep` 零命中（沿用 B14 / B19 纪律）。
  - **REV-18 重申**：IFC-IB-261 的**单元清单不变**（**四单元**；系统管理 / 项目 / LLM Key 均内建，**不新增 systemd 单元**，DR-20）；IFC-IB-263 的「只报键名、不回显值、非零码退出」纪律对 REV-18 新键名同样生效，**且 LLM Key 未配置为唯一例外（非致命，ADR-39）**。

### MOD-IB-26 ib-embed 服务端 (L2；服务端进程)
```

---

## ■ EDIT-MOD-15 — 新增 §4.2.8 REV-18 无环性再声明

**位置**：§4.2.7 末（第 1050 行）之后、`### 4.3 分层视图` 之前。

**ANCHOR（插入点边界，逐字）**：
```
### 4.3 分层视图
```

**REPLACE（new_string）**：
```
### 4.2.8 REV-18 无环性再声明（零新增依赖边）

**结论：DAG 拓扑在 REV-18 下不变，无环证明（§4.2）继续成立。**

- **零新增依赖边**：REV-18 新增全部落在 **MOD-IB-01 / 02 / 11 / 23 / 24 / 25** 内部（项目注册表 / LLM Key 的类型化契约与第 18 / 19 个端口 / 键名登记与启动校验口径 / 同一 SQLite 适配器与迁移单源 / 项目 CRUD 与账户扩展与 LLM Key 端点与项目域上传 / 系统管理三分 IA / 迁移与检查清单），**§4.1 依赖边清单逐行未改**；`w(MOD-IB-n) = n` 严格递减的构造性证明**不受影响**。
- **不新增模块**：与 R7 / R8 / R13 / R14 / REV-16-2 / REV-16-4 同理 —— 项目注册表 / LLM Key **必然被组合根 `MOD-IB-23` 依赖 / 承载**，若新开模块只能取 **≥27** 编号 → 产生 `23 → 27` 边，**违反 `w(A) > w(B)`**；故并入既有模块（§4.2.2 边界纪律继续适用；ADR-37 / ADR-38）。
- **既有边被复用而非新增**：`ProjectRegistryStore`（IFC-IB-367）与 `LlmKeyStore`（IFC-IB-368）端口与结构在 **MOD-IB-01**（L0）；其生产适配器在 **MOD-IB-11**（既有边 `11 → 01`，不新增）；键名登记与启动校验口径在 **MOD-IB-02**（既有边 `02 → 01`）；端点与装配在 **MOD-IB-23**（既有边 `23 → 01/02/…/22`）；前端 **MOD-IB-24 → 23**（既有）；迁移与检查清单 **MOD-IB-25 → 01/02/04**（既有）。
- **单一入口纪律未被绕开**：项目枚举唯一入口 = 组合根经 `ProjectRegistryStore`（IFC-IB-367）取得；LLM Key 装配期读取唯一入口 = 组合根经 `LlmKeyStore`（IFC-IB-368）+ `resolve_secret()`；授权判定仍**只**经注入的 `AuthzPolicy`（IFC-IB-032/033）；前端仍**只**经 HTTP/SSE 契约（MOD-IB-24 → MOD-IB-23）取数，**不新增任何绕过路径**（ADR-22 / ADR-42）。
- **红线未被绕开**：项目域资料的 `kb_id` 由服务端推导，请求体**不再**接收 kb 字段，**保留** `assert_kb_in_project`（IFC-IB-130）—— 范围**仍不可由客户端自证**（`architecture_design.md:120` 未削弱）。
- 「编号即拓扑序」继续适用于 GROUP_C；REV-18 的**边界纪律同 §4.2.2 末句**：新增工件若被低编号模块（尤其组合根）依赖，**不得新开编号更高的模块**。

### 4.3 分层视图
```

---

## ■ EDIT-MOD-16 — §5 装配表新增 2 行 + REV-18 装配说明

**REPLACE-1（§5 装配表末行）**：

**ANCHOR（old_string，`ExpertPromptStore` 行，逐字）**：
```
| `ExpertPromptStore`（**REV-16-2 新增**） | `FsExpertPromptStore`（独立 markdown 目录；原子写 + 语义哈希乐观并发，与 `DefinitionDocumentStore` 同纪律） | `InMemoryExpertPromptStore`（内存字典 + 同一合并 / 校验器） | `IB_EXPERT_PROMPT_DIR`（路径）；`IB_EXPERT_PROMPT_ENABLED=true\|false` |
```

**REPLACE（new_string，末行 + 2 新行）**：
```
| `ExpertPromptStore`（**REV-16-2 新增**） | `FsExpertPromptStore`（独立 markdown 目录；原子写 + 语义哈希乐观并发，与 `DefinitionDocumentStore` 同纪律） | `InMemoryExpertPromptStore`（内存字典 + 同一合并 / 校验器） | `IB_EXPERT_PROMPT_DIR`（路径）；`IB_EXPERT_PROMPT_ENABLED=true\|false` |
| `ProjectRegistryStore`（**REV-18 新增**） | `SqliteProjectRegistryStore`（落在 MOD-IB-11；同一 SQLite 台账；手写迁移 `005_projects.sql`；软删 = 状态列；装配期幂等首次播种） | `MemoryProjectRegistryStore`（内存字典 + 同一端口一致性测试） | `IB_PROJECT_REGISTRY_BACKEND=sqlite\|memory` |
| `LlmKeyStore`（**REV-18 新增**） | `SqliteLlmKeyStore`（落在 MOD-IB-11；同一 SQLite 台账；手写迁移 `006_llm_key.sql`；单行表全局唯一；库文件 0600 且属主对齐服务账号） | `MemoryLlmKeyStore`（内存单值 + 同一端口一致性测试） | `IB_LLM_KEY_BACKEND=sqlite\|memory` |
```

**REPLACE-2（§5 装配说明追加 REV-18 段）**：

**位置**：§5 REV-16-2 装配说明段（第 1101 行）之后、`---`（第 1103 行）之前。

**ANCHOR（old_string，REV-16-2 装配说明段末句）**：
```
⑤ **两个持久化载体并存不等于第二真源**（真源按域唯一，ADR-15-R1）；**禁止**把提示词正文写入定义文档，或把专家元数据写入提示词目录。
```

**REPLACE（new_string）**：
```
⑤ **两个持久化载体并存不等于第二真源**（真源按域唯一，ADR-15-R1）；**禁止**把提示词正文写入定义文档，或把专家元数据写入提示词目录。

> **REV-18 装配说明（项目注册表 / LLM Key）**：① **装配序列**见 §3 MOD-IB-23（IFC-IB-372 ~ 374）；一键离线下 `ProjectRegistryStore` / `LlmKeyStore` 取「离线/测试」列（`Memory*`），**装配期播种与端口一致性照常执行**（离线亦可验证项目 CRUD / Key 管理）。② 新增键 `IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND` **只登记键名**，其取值一律不进文档、不进日志。③ **凭据纪律（新增口径）**：**LLM Key 载体 = DB**（**不入 `.env` / 不进 git / 不进命令行**）；**唯一写入口** = `PUT /api/llm-key`；**装配期读取为唯一读点**（`resolve_secret()`）；HTTP 层只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），**不回显明文为类型层事实**；承载**库文件 0600 且属主对齐服务账号**（REQ-NFR-IB-20）。④ **`.env` 仅保留非 LLM Key 的其他密钥**；`IB_LLM_API_KEY` **停止作为 LLM Key 来源**（登记型口径修订）。⑤ **生效口径**：保存仅落库 / 落盘，**重启后重新装配方生效**（ADR-32 / C-IB-40）；**不提供**运行期热重载 / 热重编译入口；**登记：生产后端重启与首次环境变量配置须由用户执行**。⑥ **UI 分组不作为权限机制**：系统管理三分由服务端 `403` 兜底（ADR-42）。
```

---

## ■ EDIT-MOD-17 — §8 替身表新增 2 行 + REV-18 离线可测单元

**REPLACE-1（§8 替身表末行）**：

**ANCHOR（old_string，`ExpertPromptStore` 行，逐字）**：
```
| `ExpertPromptStore`（REV-16-2 新增） | `FsExpertPromptStore`（独立 markdown 目录，生产 / 离线同一合并·校验器） | `InMemoryExpertPromptStore`（内存字典） | REQ-NFR-IB-19；离线可验证：主缺失回退兜底、孤儿文件拒绝、缺兜底拒绝、参数越界拒绝 |
```

**REPLACE（new_string，末行 + 2 新行）**：
```
| `ExpertPromptStore`（REV-16-2 新增） | `FsExpertPromptStore`（独立 markdown 目录，生产 / 离线同一合并·校验器） | `InMemoryExpertPromptStore`（内存字典） | REQ-NFR-IB-19；离线可验证：主缺失回退兜底、孤儿文件拒绝、缺兜底拒绝、参数越界拒绝 |
| `ProjectRegistryStore`（**REV-18 新增**） | `SqliteProjectRegistryStore`（同一 SQLite 台账；`005_projects.sql`） | `MemoryProjectRegistryStore` | 项目 CRUD 状态机、软删 / 停用语义、装配期幂等首次播种、`project_id` 冲突 |
| `LlmKeyStore`（**REV-18 新增**） | `SqliteLlmKeyStore`（同一 SQLite 台账；`006_llm_key.sql`；单行表） | `MemoryLlmKeyStore` | 全局唯一（单行）、`configured` / `unconfigured` 两态、明文不进响应类型、清除语义 |
```

**REPLACE-2（§8 追加 REV-18 离线可测单元）**：

**ANCHOR（old_string，R13 离线可测单元段，逐字）**：
```
**R13 追加的离线可测单元**（**纯函数、无外部 IO、无第三方依赖**）：**MOD-IB-01** 的令牌原语 `new_session_token` / `token_digest` / `token_digest_matches`（IFC-IB-311，含「常量时间比较」与「只存摘要」的判据）。配合 **`MemoryAccountStore`**（§8 替身）即可在**无任何外部服务**下完成「登录 → 改密态 → 改密 → 续期 → 登出」的**全链路离线验证**（REQ-NFR-IB-18）。
```

**REPLACE（new_string，R13 段 + REV-18 段）**：
```
**R13 追加的离线可测单元**（**纯函数、无外部 IO、无第三方依赖**）：**MOD-IB-01** 的令牌原语 `new_session_token` / `token_digest` / `token_digest_matches`（IFC-IB-311，含「常量时间比较」与「只存摘要」的判据）。配合 **`MemoryAccountStore`**（§8 替身）即可在**无任何外部服务**下完成「登录 → 改密态 → 改密 → 续期 → 登出」的**全链路离线验证**（REQ-NFR-IB-18）。

**REV-18 追加的离线可测单元**（**纯函数 / 内存替身，无外部 IO、无第三方依赖**）：配合 **`MemoryProjectRegistryStore`**（IFC-IB-370）与 **`MemoryLlmKeyStore`**（IFC-IB-371）即可在**无任何外部服务**下完成「先建项目 → 建账号（顺序依赖校验）→ 编辑 / 软删账号 → 项目软删 / 停用 → 写 / 清 LLM Key → 未配置态 fail-closed」的**全链路离线验证**（REQ-FUNC-IB-43 ~ 48 / REQ-NFR-IB-20）；`LlmKeyStatus` **不含明文字段**可作**结构断言**（「不回显明文」= 类型层可测事实）。
```

---

## ■ EDIT-MOD-18 — §9.1 覆盖率矩阵新增 6 行 + 计数行同步

**REPLACE-1（§9.1 标题）**：

**ANCHOR（old_string）**：
```
### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-42，**42/42 全覆盖**；REV-16-2 同步计数）
```

**REPLACE（new_string）**：
```
### 9.1 功能需求（REQ-FUNC-IB-01 ~ IB-48，**48/48 全覆盖**；REV-18 同步计数）
```

**REPLACE-2（§9.1 表末行 + 6 新行）**：

**ANCHOR（old_string，`IB-42` 行，逐字）**：
```
| IB-42 | 示例项目专家定义与 FreeArk **100% 对齐**（含专家名；工具参数排除） | **MOD-IB-01, MOD-IB-16** / 02, 24（ADR-31） |
```

**REPLACE（new_string，IB-42 行 + 6 新行）**：
```
| IB-42 | 示例项目专家定义与 FreeArk **100% 对齐**（含专家名；工具参数排除） | **MOD-IB-01, MOD-IB-16** / 02, 24（ADR-31） |
| IB-43 | **系统管理三分** IA（账户管理 / 项目管理 / LLM Key 管理；**UI 分组非权限机制**） | **MOD-IB-24** / 23, 01（ADR-42） |
| IB-44 | 项目管理（**项目 CRUD + 项目注册表**） | **MOD-IB-23, MOD-IB-11** / 01, 24（ADR-37） |
| IB-45 | 项目与账号的**顺序依赖**（先建项目、后建账号；**1:N 零迁移**） | **MOD-IB-23, MOD-IB-11** / 01, 24（ADR-40；OQ-IB-28） |
| IB-46 | 账号**查看 / 编辑 / 删除**（软删 + 二次确认 + 删除保护） | **MOD-IB-23, MOD-IB-11** / 01, 24（ADR-40） |
| IB-47 | **LLM Key 管理**（增 / 改 / 删；载体 = DB；只回状态 / 掩码） | **MOD-IB-23, MOD-IB-11** / 01, 02, 24（ADR-38 / ADR-39；REQ-NFR-IB-20） |
| IB-48 | **项目域资料上传**（取代「知识库标识」输入；`kb_id` 由项目推导） | **MOD-IB-23, MOD-IB-24** / 11, 01（ADR-41；C-IB-43） |
```

**REPLACE-3（§9.1 计数小结行）**：

**ANCHOR（old_string）**：
```
**无缺口**：**36 条 REQ-FUNC**（R13 同步计数；R1 / R2 基线 24、R7 27）每条至少一个「主」模块，且每条均可被至少一个 AC 验证（R13 新增 9 条见上九行；AC 落点以 GROUP_A 包 §2 为权威，本矩阵的 AC 配对标 [INFERRED]）。
```

**REPLACE（new_string）**：
```
**无缺口**：**48 条 REQ-FUNC**（REV-18 同步计数；沿革：R1 / R2 基线 24、R7 27、R13 36、REV-16-2 42）每条至少一个「主」模块，且每条均可被至少一个 AC 验证（REV-18 新增 IB-43 ~ IB-48 六行见上；AC 落点以 GROUP_A 包 §2 为权威，本矩阵的 AC 配对标 [INFERRED]）。
```

---

## ■ EDIT-MOD-19 — §9.2 新增 NFR-20 行 + 新增 §9.11 覆盖率再声明

**REPLACE-1（§9.2 标题）**：

**ANCHOR（old_string）**：
```
### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-19）
```

**REPLACE（new_string）**：
```
### 9.2 非功能需求（REQ-NFR-IB-01 ~ IB-20）
```

**REPLACE-2（§9.2 表末行 + NFR-20 行）**：

**ANCHOR（old_string，`NFR-19` 行，逐字）**：
```
| NFR-19 | 可视化配置的一致性 / 可观测 / **fail-safe**（提示词与工具授权） | **MOD-IB-02, MOD-IB-23** / 01, 16, 24 |
```

**REPLACE（new_string，NFR-19 行 + NFR-20 行）**：
```
| NFR-19 | 可视化配置的一致性 / 可观测 / **fail-safe**（提示词与工具授权） | **MOD-IB-02, MOD-IB-23** / 01, 16, 24 |
| NFR-20 | **LLM Key 存储与呈现纪律**（载体 = DB；库文件 **0600** 且属主对齐服务账号；`.env` 仅非 LLM Key 密钥；**不回显明文 / 掩码不含明文前后缀**） | **MOD-IB-11, MOD-IB-23** / 01, 02, 25（ADR-38；C-IB-42） |
```

**REPLACE-3（§9.10 块末之后、新增 §9.11）**：

**位置**：§9.10 块末（第 1423 行）之后、`## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）`（第 1425 行）之前。

**ANCHOR（插入点边界，逐字；为 §9.10 块末行 + §10 标题两行的边界）**：
```
- **架构侧对应**：`architecture_design.md` 1.8.0（REV-16-4）的 **ADR-33 / ADR-34 / ADR-35**、**§2.0.7 R16-4 影响复核表**、[ARCH-ASSUMPTION-A11]、[TBD-T25]、§10.1 / §10.2 / §10.3 R16-4 行；`tech_stack.md` **未改（无新第三方依赖）**。

## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）
```

**REPLACE（new_string）**：
```
- **架构侧对应**：`architecture_design.md` 1.8.0（REV-16-4）的 **ADR-33 / ADR-34 / ADR-35**、**§2.0.7 R16-4 影响复核表**、[ARCH-ASSUMPTION-A11]、[TBD-T25]、§10.1 / §10.2 / §10.3 R16-4 行；`tech_stack.md` **未改（无新第三方依赖）**。

### 9.11 REV-18 覆盖率再声明（系统管理 / 项目 / LLM Key / 项目域资料增量）

**结论：REQ 覆盖 42/42 → 48/48（REQ-FUNC）+ 19 → 20（REQ-NFR），无新增缺口。覆盖归属见 §9.1 / §9.2 增行。**

- **新增覆盖归属**：IB-43（系统管理三分 IA）→ MOD-IB-24（主）/ 23, 01；IB-44（项目 CRUD + 注册表）→ MOD-IB-23, MOD-IB-11（主）/ 01, 24；IB-45（顺序依赖）→ MOD-IB-23, MOD-IB-11（主）/ 01, 24；IB-46（账号查看 / 编辑 / 删除）→ MOD-IB-23, MOD-IB-11（主）/ 01, 24；IB-47（LLM Key 管理）→ MOD-IB-23, MOD-IB-11（主）/ 01, 02, 24；IB-48（项目域资料上传）→ MOD-IB-23, MOD-IB-24（主）/ 11, 01。**NFR-20**（LLM Key 存储与呈现纪律）→ MOD-IB-11, MOD-IB-23（主）/ 01, 02, 25。
- **模块与依赖不变**：模块数仍 **26**、端口 17 → **19**（纯追加）、**§4.1 依赖边逐行未改**（§4.2.8）。
- **追踪落点**：IFC-IB-366 ~ 368（契约与端口）→ ADR-37 / ADR-38；IFC-IB-369（键名与启动校验口径）→ ADR-38 / ADR-39；IFC-IB-370 / 371（适配器与迁移单源）→ ADR-37 / ADR-38；IFC-IB-372 ~ 375（端点与项目域化）→ ADR-37 / ADR-40 / ADR-41 / ADR-42；IFC-IB-376（前端 IA）→ ADR-42；IFC-IB-377（迁移与检查清单）→ ADR-26 / ADR-38。
- **OQ / OPEN ITEM 处置**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）/ **OI-2**（LLM Key 首启供给序）/ **OI-3**（掩码字面）**保持开放**（`architecture_design.md` §10.1）；架构层只落地「**软删停用 / 零迁移 / 未配置态 fail-closed / 无明文可分**」的安全默认，**不自行改写 ADR-21、不自行拍板业务数值**。
- **红线守护**：项目域资料 `kb_id` 由服务端推导、请求体不再接收 kb、**保留** `assert_kb_in_project`（403）；**UI 分组非权限机制**（服务端 `403` 为唯一裁决者）。
- **架构侧对应**：`architecture_design.md` 1.10.0（REV-18）的 **ADR-37 / ADR-38 / ADR-39 / ADR-40 / ADR-41 / ADR-42**、**§2.0.9 R18 影响复核表**、[ARCH-ASSUMPTION-A12]、[TBD-T26] / [TBD-T27]、§10.1 / §10.2 / §10.3 R18 行；`tech_stack.md` 为**登记型口径修订**（凭据载体说明收窄，**无新第三方依赖**，见主包 Part C）。

## 10. FreeArk 参考模块映射（只读对照，说明复用与改写边界）
```

---

## ■ EDIT-MOD-20 — §11 自检声明追加 REV-18 自检块

**位置**：§11 末尾（REV-17 自检块末行，第 1531 行）之后（文档末尾）。

**ANCHOR（old_string，逐字，REV-17 自检块末行）**：
```
      - **边界合规**：REV-17 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**（全程只读）；需求侧文档只读未改（落盘载体措辞的同步**另立交付项**）；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
```

**REPLACE（new_string，REV-17 末行 + REV-18 自检块）**：
```
      - **边界合规**：REV-17 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**（全程只读）；需求侧文档只读未改（落盘载体措辞的同步**另立交付项**）；`tech_stack.md` **未改（无新第三方依赖）**；本阶段**止于 GROUP_B**。
    - **REV-18 自检（系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量，GROUP_A REV-18-2 下游贯通）**：
      - **覆盖同步**：§9.1 由 42/42 同步为 **48/48 REQ-FUNC**（新增 IB-43 ~ IB-48，各有主模块），§9.2 NFR 由 19 同步为 **20**（新增 NFR-20）；**§9.11 给出 R18 再声明**。
      - **零新增模块 / 零新增依赖边**：模块数仍 **26**；**§4.1 依赖边清单逐行未改**；新增工件并入 MOD-IB-01 / 02 / 11 / 23 / 24 / 25（§1 REV-18 补充纪律段给出「为何不新增 MOD-IB-27」的编号论证；§4.2.8 给出无环性再声明）。
      - **端口 17 → 19（纯追加）**：`ProjectRegistryStore`（IFC-IB-367）/ `LlmKeyStore`（IFC-IB-368），**均定义于 MOD-IB-01（L0）**；适配器在 **MOD-IB-11**（既有边 `11 → 01`，不新增）。
      - **类型化未降级 / 编号纪律未破**：新增 `IFC-IB-366 ~ 377`（12 条）全部为 `name: type` + 可空性的**类型化契约**，均为 **frozen dataclass / Protocol / Literal / 纯 stdlib，零第三方依赖**；`IFC-IB-001 ~ 365` 的号 / 名 / 签名**一字不动**（**仅 7 条文字与取值口径修订**，逐条登记于 §2.2.9：`IFC-IB-024` / 242 / 243 / 262 / 263 / 321 / 333）；**`IFC-IB-285` 仍预留未分配**；既有重号 `IFC-IB-131` **登记不修**（残余项 R-9）。**`AccountStore` 的 13 方法文本一字不改**（编辑经 IFC-IB-366 `update_user` **加成式扩展**）。
      - **红线未破（强制）**：项目域资料 `kb_id` **由已认证主体的 `project_id` 推导**（`kb_id ≡ project_id`），**请求体不再接收 kb 字段**，**保留** `assert_kb_in_project`（IFC-IB-130），失败仍 **403** —— **不削弱** `architecture_design.md:120`「范围不可由客户端自证」（ADR-41 / C-IB-43）。
      - **授权真源唯一 + UI 分组非权限机制为事实**：系统管理三分的导航可见性**仅体验优化**；授权判定仍**只**经注入的 `AuthzPolicy`（`IFC-IB-032/033` 未改）；**非 admin 一律服务端 `403`**（ADR-42）。
      - **账本 / 删除语义为契约事实**：`ProjectStatus` / `AccountStatus` 的 `disabled` 使「**软删 / 停用（数据保留、可恢复）**」成为**类型层事实**；项目 / 账号删除均**二次确认**且**不物理级联**（OOS-19）；**禁删 `admin` 或最后管理员**在**服务层**拦截。
      - **LLM Key 凭据纪律（新增口径）为类型层事实**：`LlmKeyStore` 承载**单一全局 Key**（单行表，`CHECK(id=1)`）；**装配期读取为唯一读点**（`resolve_secret()`）；HTTP 只暴露 `LlmKeyStatus`（`configured` / `masked` / `updated_at`），`LlmKeyStatus` **不含明文字段**（「不回显明文」= **类型层事实**）；`.env` **仅保留非 LLM Key 的其他密钥**，`IB_LLM_API_KEY` **停止作为 LLM Key 来源**；承载**库文件 0600 且属主对齐服务账号**（NFR-20 / 检查清单 B22）。
      - **未配置态 fail-closed 为契约事实**：`configured=false` 时服务**正常启动**，LLM 依赖路径以**可读错误 fail-closed**（**不含任何 Key 信息**；ADR-39）；**破除首启死锁**；**其余必填配置仍 fail-fast**（`IFC-IB-263` 修订口径）。
      - **生效口径未变**：**保存 + 服务重启重装配**（ADR-32 / C-IB-40 / OOS-16）；**不提供**运行期热重载 / 热重编译入口；**登记：生产后端重启与首次环境变量配置须由用户执行**（架构 / 部署文档只写「由用户执行」的动作）。
      - **OQ / OPEN ITEM 未越权**：**OI-1**（ADR-21 1:1 与 OQ-IB-28 1:N 的口径张力）**登记不裁决**、**OI-2**（LLM Key 首启供给序）、**OI-3**（掩码字面）**保持开放**；架构层**不自行改写 ADR-21、不新增 REQ、不改 AC**。
      - **凭据纪律**：全文只登记**键名** / **头名** / **表名** / **字段名** / **文件层名**；**未写入任何配置取值、口令 / 令牌 / Key / 证书字面量**；令牌仅经 `Authorization` 头；`?token=` 纪律对全部新端点（`/api/projects*`、`/api/accounts*`、`/api/llm-key`）生效。
      - **边界合规**：REV-18 增量**不含实现代码**（无函数体、无伪代码）；**未修改 FreeArk 任何文件**（全程只读）；需求侧文档只读未改；`implementation_plan.md`（GROUP_C）**未改**；`tech_stack.md` **为登记型口径修订（凭据载体说明收窄，无新第三方依赖）**；本阶段**止于 GROUP_B**。
```

---

**Part B 结束。** 继续见 `docs/rev18_groupb_apply_package_part3.md`（Part C：`tech_stack.md` 增量 + Part D：合并校对清单）。
