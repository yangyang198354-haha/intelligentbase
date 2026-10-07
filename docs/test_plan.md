---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-TP-001 |
| 标题 | intelligentbase 智能知识库基座 —— 测试计划 |
| 产出代理 | test-engineer |
| 调用 ID | **REV-18 增量（GROUP_D / PHASE_07~09：系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）= INV-GROUP_D-INTELBASE-019**（见 §23）；**R16-4 缺陷闭合复跑（DEFECT-R16-4-01）= INV-GROUP_D-INTELBASE-017**（见 §21）；**R16-4 增量（REV-16-4）= INV-GROUP_D-INTELBASE-016**（见 §21）；**R16-2 增量（REV-16-2）= INV-GROUP_D-INTELBASE-015**（见 §20）；**R14 增量（REV-14）= INV-GROUP_D-INTELBASE-014**（见 §19）；INV-GROUP_D-INTELBASE-010（R12 增量）；R13 增量 = INV-GROUP_D-INTELBASE-012（见 §18）；原 INV-GROUP_D-INTELBASE-001 ~ -009 |
| revision | **REV-18**（系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传；新增 unit 8 + integration 9 + 前端 1（另 5 例 REV-18 前端用例由 GROUP_C 实现期落地）；见 §23）。**前序：REV-17**（提示词兜底层重定位 —— 提示词文本移出定义文档 / 合并结果进 system 位 / 通用内置安全网破「界面新增专家」死锁；新增 unit 13 + integration 6 + 前端 1；见 §22）。**前序：REV-16-4**（DEFECT-R16-01 / R16-02 修复 + GAP-R16-03 / R16-04 落地 —— 独立复跑、强制负例与覆盖率回补；**DEFECT-R16-4-01 修复后整套复跑闭合**；见 §21） |
| 项目 | intelligentbase |
| 阶段 | GROUP_D / PHASE_07（测试计划）+ R7 增量（US-IB-17 / US-IB-18「UI 可视化配置」纳入测试范围）+ **R8 增量（FND-R7-01 修复回归：装配期唯一性校验）** + **R9 增量（FLAKE-IB-01 测试侧稳定性治理：连接级有界重试）** + **R10 增量（前端冒烟测试层正式化：`src/frontend/tests/frontend.smoke.test.js` 6 例纳入测试计划）** + **R11 增量（REQ-FUNC-IB-20 测试补全：US-IB-19「流式交付最终答复」/ US-IB-20「会话生命周期」纳入测试范围，含 5 条既有用例重挂 + 13 条新增）** + **R12 增量（R8 实现到位后的补测轮 REV-12-5：闭合 AC-IB-19-02 / AC-IB-20-04，补全 19-03 / 20-02 / 20-03 / 20-05 与 FND-R11-01 / BLK-R8-02，新增 16 条）** + **R13 增量（REV-13：US-IB-21 ~ US-IB-29 账户体系 / 会话 / 前端商用界面纳入测试范围；新增 32 条 Python + 7 条前端；登记 DEFECT-R13-01）** + **R14 增量（REV-14：R13 回归缺陷修复的独立测试补测与验证 —— `GET /api/projects`（IFC-IB-333）/ `X-IB-Project` 传播（IFC-IB-334）/ 前端 `projectContext`（IFC-IB-335）/ `client.ts` 单一注入点（IFC-IB-336）纳入测试范围；新增 Python 3 条 + 前端 4 条；更正 R14 用例编号撞号并登记 R14-DEF-01）** + **R16-4 增量（REV-16-4：DEFECT-R16-01 / R16-02 修复的 fail-safe 复跑 + GAP-R16-03 / R16-04 覆盖回补；新增 Python 11 条（unit 4 + integration 7）+ 前端 1 条（TC-FE-024）；登记 DEFECT-R16-4-01）** |
| 版本 | **2.3.0（REV-18 增量（INV-GROUP_D-INTELBASE-019））**：Python 三层用例数 **327 → 351**（unit 149 → **157** / integration 154 → **170** / e2e 24 → 24；新增 unit **8**（`tests/unit/test_rev18_system_mgmt_unit.py`）+ integration **9**（`tests/integration/test_rev18_system_management_extra_int.py`））；前端冒烟 **29 → 35**（独立层；REV-18 组 6 例 = GROUP_C 实现期落地的 30~34 + 本代理新增的 35）；`selfcheck.py` **51/51**（不变）；**未改 `src/**`**（只读）、**未 commit / push / deploy**）<br>**2.2.0（REV-17 提示词兜底层重定位（INV-GROUP_D-INTELBASE-018））**：Python 三层用例数 **308 → 327**（unit 136 → **149** / integration 148 → **154** / e2e 24 → 24；新增 unit **13**（`tests/unit/test_prompt_system_slot_r17.py`）+ integration **6**（`tests/integration/test_prompt_config_r17_int.py`））；前端冒烟 **28 → 29**（独立层，新增 REV-17 用例）；`selfcheck.py` **50/50 → 51/51**（新增 `r17_build_expert_system_slot`）；**未改 `src/**`**（只读）、**未 commit / push / deploy**）<br>**2.1.0（R16-4 缺陷闭合复跑（DEFECT-R16-4-01，INV-GROUP_D-INTELBASE-017））**：**用例数不变（308 = unit 136 / integration 148 / e2e 24；前端 28 独立层）**，纯**复跑 + 回填** —— Python 三层 **308/308 全绿**（`TC-INT-147` FAIL → PASS，`TC-INT-139 / 140 / 141` 保持 PASS）；前端冒烟 28/28、`selfcheck.py` 50/50、`compileall` / `vue-tsc` EXIT 0；**未改 `src/**` / `tests/**`**（只读复跑 + 回填文档）、**未 commit / push / deploy**）<br>2.0.0（R16-4 增量（REV-16-4，INV-GROUP_D-INTELBASE-016））**：Python 三层 **297 → 308**（unit 132 → **136** / integration 141 → **148** / e2e 24 → 24；新增 unit **4**（TC-UNIT-123~126）+ integration **7**（TC-INT-141~147）；**307 pass / 1 fail** —— 唯一 FAIL = **DEFECT-R16-4-01**（审计写失败非致命契约未满足，如实失败））；**R16-2 的 TC-INT-139 / TC-INT-140 已由 FAIL 转 PASS**；前端冒烟 **27 → 28/28**（独立层，新增 TC-FE-024）、`selfcheck.py` **50/50**、`compileall` EXIT 0、`vue-tsc` EXIT 0；R16-2 两处 MAJOR 缺陷已修复、两处 MAJOR 缺口（AC-IB-32-02 / 33-02）已覆盖（见 §21）；**未改 `src/**`**（只读）、**未 commit / push / deploy**）**<br>1.9.0（**R14 增量（REV-14，INV-GROUP-D-INTELBASE-014）**：`GET /api/projects`（IFC-IB-333）/ `X-IB-Project` 传播（IFC-IB-334）/ 前端 `projectContext`（IFC-IB-335）/ `client.ts` 单一注入点（IFC-IB-336）纳入测试范围；对 REV-14 修复做**独立测试补测与验证**。Python 三层用例数 **242 → 245**（unit 95→95 / integration **126→129** / e2e 21→21；净增 3 条 —— TC-INT-126~128；另把 GROUP_C 的 R14 用例由撞号的 120~122 **更正为 123~125**，计数不变，**编号只增不改**）；前端冒烟层 **17 → 21** 例（R14 组由 4 例扩至 8 例）、仍自立一层不计入 245；登记 **R14-DEF-01**（R14 用例撞号 TC-INT-120~122，与 R13 既有占号冲突）与 R14 观测项）<br>1.8.0（**R13 增量（REV-13）**：US-IB-21 ~ US-IB-29 纳入测试范围；Python 三层用例数 **200 → 239**（unit 76→95 / integration 105→123 / e2e 19→21；其中 **+7 为基线对账项**，见 §18.6）；前端冒烟层 **6 → 13** 例、仍自立一层不计入 239；新增登记 **DEFECT-R13-01**（IP 维度限速未生效））<br>1.7.0（**R12 增量（REV-12-5，补测轮）**：R8 设计（IFC-IB-298~308）**已落地于 `src/`**，本轮把 R11 登记的 2 项「未覆盖」AC（AC-IB-19-02 / AC-IB-20-04）**闭合**、4 项「部分覆盖」补全，并回补 **FND-R11-01**（`/api/chat/stream` 缺 `session_id` → 400）与 **BLK-R8-02**（专家**内部**关键词空/重复 → `expert_keyword_empty` / `expert_keyword_duplicate`）；**Python 三层用例数 184 → 200**（unit 70→76 / integration 96→105 / e2e 18→19，编号只增不改）；**前端冒烟层 6 例仍自立一层、不计入 200**）<br>1.6.1（R11 修复补丁：§3.2 主登记表 TC-INT-039 的归属列补齐为 US-IB-19 / AC-IB-19-01；用例数不变 184）<br>1.6.0（R11 增量：171 → 184；US-IB-19 / US-IB-20 纳入；5 条重挂 + 13 条新增）<br>R10 = 1.5.1（用例数不变 171；前端冒烟层 6 例独立计数）<br>R9 = 1.4.0（用例数不变 171；FLAKE-IB-01 → MITIGATED）<br>**版本线**：1.0.0(R1) → 1.1.0(R3) → 1.2.0(R7) → 1.3.0(R8) → 1.4.0(R9) → 1.5.0(R10) → 1.5.1(R10 修复) → 1.6.0(R11) → 1.6.1(R11 修复补丁) → **1.7.0(R12 补测)** → 1.8.0(R13) → 1.9.0(R14) → **2.0.0(R16-4)** → **2.1.0(R16-4 缺陷闭合复跑)** → **2.2.0(REV-17)**；执行报告文件版本线另见 `docs/test_report.md`） |
| status | DRAFT（待 PM 门控；**§22 为 REV-17 增量，判定 SUCCESS —— 三层 327/327 全绿 + 前端 29/29 + 自检 51/51，零回归**） |
| 创建日期 | 2026-09-26 |
| 更新日期 | 2026-10-07（**REV-18 增量 = INV-GROUP_D-INTELBASE-019**：系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传 —— AC↔TC 追溯矩阵与门控口径见 §23；**R16-4 缺陷闭合复跑（DEFECT-R16-4-01）= INV-GROUP_D-INTELBASE-017**；R14 增量见 §19） |
| 上游输入 | **REV-18 增量新增输入**：`docs/user_stories.md`（**1.10.0 / REV-18-2 / APPROVED**，US-IB-35 ~ US-IB-40 与 AC-IB-35-01 ~ AC-IB-40-04 共 22 组，见其第 1364~1543 行）、`docs/requirements_spec.md`（**1.10.0 / REV-18-2 / APPROVED**，§2.11 / §2.11.1 / §6.0 DR-21；REQ-FUNC-IB-43~48 / REQ-NFR-IB-20 / C-IB-42~43 / OOS-18~19）、`docs/architecture_design.md`（**1.10.2 / REV-18-R2 / APPROVED**，ADR-37~ADR-42 见第 1084~1160 行、ADR-21-R1 见第 851~862 行）、`docs/module_design.md`（**1.10.2 / REV-18-R2 / APPROVED**，IFC-IB-366~377；端口 17→19）、`docs/implementation_plan.md`（**2.13.0 / REV-18**，§25 见第 1744~1825 行）、`docs/code_review_report.md`（REV-18，§22 见第 2707~2809 行；CRITICAL=0 / MAJOR=0 / MINOR=4）、GROUP_C 实现门控 **GR-C-013 = PASS_WITH_CONDITIONS**（D-R18-01 / CRED-01 非阻塞）、`src/**` + `tests/**`（`src/` 只读）；**以下为历史阶段输入**：`docs/user_stories.md`（**1.4.0 / APPROVED，29 US**；R11 新增 US-IB-19 / US-IB-20，**R13 新增 US-IB-21 ~ US-IB-29，29 组 AC-IB-21-* ~ AC-IB-29-***；GROUP_C R13 实现门控 **GR-C-009 = PASS_WITH_CONDITIONS**）、`docs/requirements_spec.md`（**1.3.0 / APPROVED**，含 REQ-FUNC-IB-20 承接（US-IB-19/20）与 REQ-FUNC-IB-25/26/27）、`docs/implementation_plan.md`（**2.6.0 / R11–R12**，GROUP_C 门控 GR-C-005 = R7_PASS；其文件头 `<status>` 字段仍为 DRAFT，以 `docs/phase_status.md` 为权威）、`docs/architecture_design.md`（**1.4.0 / R8**，ADR-17 + IFC-IB-298~308）/ `docs/module_design.md`（**1.4.0 / R8**，§9.6 逐 AC 归属）/ `docs/tech_stack.md`（**1.3.0 / R7**）、`docs/code_review_report.md`（R7 增量 §12）、`docs/cicd_pipeline.md`（**1.1.1 / R10**，阶段9 定义）；**R14 增量新增输入**：`docs/rev14_project_context_apply_package.md`（REV-14 工作包）、`docs/architecture_design.md`（**1.6.0 / REV-14**，ADR-28 + §2.0.5 + §10.1 R14 OPEN ITEM）/ `docs/module_design.md`（**1.6.0 / REV-14**，IFC-IB-333~336）、GROUP_C R14 实现门控 **GR-C-010 = PASS_WITH_CONDITIONS**（open_item_3 = R14-L-01）、`src/ib/**` + `src/ibweb/**` + `src/ib_embed/**` + `src/frontend/**`（只读）；**R16-4 增量新增输入**：`docs/user_stories.md`（**1.7.0 / REV-16-4**，AC-IB-30-04 / 31-03 / 32-02 / 33-02）、`docs/architecture_design.md`（**1.8.0 / REV-16-4**，ADR-33 / ADR-34 / ADR-35）、`docs/module_design.md`（**1.8.0 / REV-16-4**，IFC-IB-355 ~ 363）、`docs/implementation_plan.md`（**2.11.0 / REV-16-4**，§23）、`docs/code_review_report.md`（§20，CRITICAL=0 / MAJOR=0 / MINOR=4）、GROUP_C 实现门控 **GR-C-012 = PASS_WITH_CONDITIONS**、`src/**` + `tests/**`（`src/` 只读）；**REV-17 增量新增输入**：`docs/architecture_design.md`（**1.9.0 / REV-17**，ADR-36 / ADR-15-R2 / §2.0.8）、`docs/module_design.md`（**1.9.0 / REV-17**，IFC-IB-364 / IFC-IB-365 / §2.2.8）、`docs/requirements_spec.md`（**1.8.0 / REV-17**，REQ-FUNC-IB-37/38/41 与 C-IB-41）、`docs/implementation_plan.md`（**2.12.0 / REV-17**，§24）、`src/ib/**` + `src/ibweb/**` + `src/frontend/**`（只读） |
| 下游产物 | `docs/test_report.md`（PHASE_08/09 执行报告；R7 增量见其 §12、R8 增量见其 §13、R9 增量见其 §14、R10 增量见其 §15、R11 增量见其 §16、R12 增量见其 §17、R13 增量见其 §18、R14 增量见其 §19、R16-2 增量见其 §20、**R16-4 增量见其 §21**、**REV-18 增量见其 §23**） |
| 环境约束 | 全部测试离线可跑：SQLite/内存替身/临时文件系统；**严禁**连接生产库 / 真实 Qdrant / DeepSeek / bge-m3 真实服务 / 任何外部网络 |
| 凭据纪律 | 任何 secret 只经环境变量注入，测试代码与夹具中不含真实 token/key/密码 |
---

# intelligentbase 测试计划（GROUP_D / PHASE_07）

> 本计划是 GROUP_D 的测试总纲。测试用例**一律**溯源至 `user_stories.md` 的验收标准（AC-IB-NN-NN）；
> 无 AC 溯源的用例视为幻觉用例，不予收录。执行结果与原始输出见 `docs/test_report.md`。

---

## §1 测试策略

### 1.1 测试目标

| # | 目标 | 度量 |
|---|------|------|
| G1 | 用户故事级功能正确：**20** 个 US 的验收标准在离线装配下被真实执行验证 | 可测 AC 覆盖率 **100%（90/90）**；11 项 NOT_TESTABLE 不计（见 §5）。**R12 进展**：AC-IB-19-02 / AC-IB-20-04 已闭合（R8 实现到位，见 §16）；AC-IB-19-02 / 19-03 / 20-02 的部分契约/部署子句登记为**残余**（§16.5） |
| G2 | 关键路径端到端可用：Must Have 故事的完整用户旅程跑通 | 关键路径 E2E 覆盖率 100%（**16/16** Must Have US，含 US-IB-17/18 与 R11 新增 US-IB-19/20；R12 新增 TC-E2E-019 强化 US-IB-20 旅程） |
| G3 | 依赖故障可降级不中断：检索 fail-open、台账/字节 fail-closed | 降级场景用例全绿 |
| G4 | 项目/知识库隔离：结构化（collection-per-project）+ 软隔离（filter）双重验证 | 隔离用例全绿 |
| G5 | 契约纪律：`?token=` 一律 400、令牌不进 URL、外发边界如实声明 | 契约用例全绿 |
| G6 | 定义文档单一真源：可视化编辑**只**写回定义文档，无第二副本；非法配置装配期 fail-fast | US-IB-17/18 用例全绿 + 装配闸门聚合校验项 |
| G7 | 可回归：所有结论由真实命令 + exit code 支撑，偏差可追溯 | 原始输出留档 `docs/evidence/` |

### 1.2 范围

**In-scope（可离线验证）**
- L0 核心类型/枚举/错误码/配置解析与校验/契约纪律
- L1 切分、解析（txt/md/docx）、魔数校验、SSE 帧、会话存储、脱敏
- L2 路由（意图/语义）、专家注册表、工具注册与作用域绑定、能力摘要
- L3 检索（fail-open）、向量库端口（替身）、embedding 三形态（含回环真 HTTP 对拍）
- L4 入库生命周期、页面图关联（M-02 写路径）、删除级联、重试状态机
- L5 WSGI HTTP 契约（Django test Client）、编排事件序列、`related_images` 接缝
- `ib_embed`（MOD-IB-26）线协议、11 键闭集配置、C8 零耦合

**Out-of-scope（本机不可验证，登记为 not-verified，见报告 §6）**
- 真实 bge-m3 推理 / 目标机推理延迟
- onnxruntime 真实运行、PDF 文本层与扫描件 OCR（依赖 `pypdf*` / `pypdfium2` / `rapidocr`，本机缺失）
- 真实 Qdrant 部署与重启持久化
- 前端 `npm install` / `vue-tsc` / `vite build`（无 node 工具链执行）
- 部署（systemd、开机自启）——属 GROUP_E，**本轮不触碰**

### 1.3 测试环境

| 项 | 值 |
|----|-----|
| 开发机 | Windows 11，Python **3.14.6**（见 §7 偏差 DEV-01） |
| 测试框架 | pytest 9.1.1 + pytest-cov 7.1.0 |
| Web 载体 | Django 6.0.6 + DRF 3.17.1（`ibweb.test_settings` 风格：SQLite/内存） |
| 离线开关 | `IB_OFFLINE_MODE=1`、`IB_CONFIG_SOURCE=dict`、`IB_OFFLINE_TOKEN`（测试占位符）、`IB_LOG_LEVEL=ERROR` |
| 替身 | InMemory 台账 / InMemory 向量库 / FakeEmbedder / FakeLlmProvider |
| 回环真 HTTP | `ib_embed.server` 起 `127.0.0.1:0`（本机 socket，无外部依赖） |
| 覆盖率 | coverage 7.15.0，`--cov=ib --cov=ibweb --cov=ib_embed` |

环境在 `tests/conftest.py` 导入期一次性设定，测试无需额外配置即可离线运行。

### 1.4 覆盖率目标与门控阈值

| 级别 | 默认门控阈值 | 说明 |
|------|-------------|------|
| 单元测试 | 通过率 ≥ **80%** 方可进入集成测试 | 通过率 = pass / (pass + fail)，skip/blocked 不计入分母 |
| 集成测试 | 通过率 ≥ **90%** 方可进入 E2E 测试 | 同上 |
| E2E / 关键路径 | 关键路径（Must Have US）覆盖率 **100%** | 关键路径 = US-IB-01/02/03/04/06/07/08/09/10/11/12/14 + **US-IB-17/18**（共 **14** 个 Must Have US） |

PM 未在本轮 `special_instructions` 中覆盖阈值，故采用默认值（与 `docs/module_design.md` §12 声明一致）。

---

## §2 测试级别分类规则

对每个 AC，按其 Given/When/Then 涉及的模块范围固定分类：

| 级别 | 判定规则 | TC 前缀 |
|------|---------|---------|
| 单元（UNIT） | Given/When/Then 仅涉及单个函数/方法/类/纯数据结构的行为 | `TC-UNIT-NNN` |
| 集成（INT） | 涉及两个及以上模块协作（或端口接缝、HTTP 契约、线协议） | `TC-INT-NNN` |
| E2E | 描述完整用户操作路径（入口 → 出口，一条旅程） | `TC-E2E-NNN` |

同一 AC 可被多级别用例覆盖；分类一经确定，全篇一致。

---

## §3 测试用例清单

共 **200** 个用例：单元 76 / 集成 105 / E2E 19。所有用例 ID、所属 US、关联 AC、前置、动作、预期如下。（R3 增量：§3.2 新增 TC-INT-069/070/071/073，并翻转 TC-INT-009/041/061 为正向回归守卫，详见 §9。R4 增量：新增 TC-UNIT-055 与 TC-INT-074~078，并强化既有守卫 TC-INT-041 / TC-E2E-003，详见 §10。**R7 增量**：新增 16 条（单元 TC-UNIT-056~061 / 集成 TC-INT-079~086 / E2E TC-E2E-015~016），落在 **§11**；另，任务书简报所称「148 例」与实测不符 —— 实测基线为 **149 例**，其中 `TC-INT-072`（`test_ops_contract.py`，R5/R6 重建修复轮引入、见 `docs/deployment_report.md`）此前未登记入本文件，本轮行 **诚实标注** 而不掩盖。**R8 增量**：登记 software-developer 交付的 TC-UNIT-062~064（3 条，此前未入册）+ 本代理新增 TC-UNIT-065/066、TC-INT-087（3 条），合计净增 **6** 条，落在 **§12**。**R11 增量**：就 REQ-FUNC-IB-20 的新 US-IB-19 / US-IB-20 **补测 13 条**（单元 TC-UNIT-067~069 / 集成 TC-INT-088~095 / E2E TC-E2E-017~018），并把 5 条既有流式/会话用例**重挂**到正确 US/AC（TC-UNIT-016/017/018/022、TC-INT-039）；落 **§15**。**既有 171 条编号一律不变**；新增能力中「完成事件附结构化产物」（AC-IB-19-02）与「确认中间态呈递/决策回传」（AC-IB-20-04）依赖架构 1.4.0/R8 的 IFC-IB-298~308、本轮 `src/` 未实现 → 如实登记覆盖缺口，不伪造断言。**R12 增量**：R8 实现已落地，就 AC-IB-19-02 / AC-IB-20-04 **闭合** + 其余补测 **新增 16 条**（单元 TC-UNIT-070~075 / 集成 TC-INT-096~104 / E2E TC-E2E-019），落 **§16**；**既有 184 条编号一律不变**。）

### 3.1 单元测试（76）

文件：`tests/unit/test_core_config_chunk_parse_stream.py`（23）、`tests/unit/test_routing_experts_tools.py`（20）、`tests/unit/test_embed_ledger.py`（12）、`tests/unit/test_blob_kb_segment.py`（1）、`tests/unit/test_definition_data_layer_r7.py`（6，R7 新增）、`tests/unit/test_definition_uniqueness_r8.py`（3，R8 / software-developer 交付）、`tests/unit/test_definition_uniqueness_extra_r8.py`（2，R8 / test-engineer 补测）、`tests/unit/test_stream_session_lifecycle_unit_r11.py`（**3，R11 新增**）、`tests/unit/test_stream_session_lifecycle_unit_r12.py`（**4，R12 新增**）、`tests/unit/test_definition_keyword_intra_r12.py`（**2，R12 新增**）。

| TC-ID | 关联 US | 关联 AC | 前置 | 动作 | 预期结果 |
|-------|--------|--------|------|------|---------|
| TC-UNIT-001 | US-IB-13/14 | AC-IB-13-04/14-01 | 枚举定义 | 读各枚举的 wire 值 | 值与契约字符串一致，可 JSON 序列化 |
| TC-UNIT-002 | US-IB-11 | AC-IB-11-02 | Scope 类型 | 构造带/不带 project_id 的 Scope | 项目作用域为必填签名，缺失即拒 |
| TC-UNIT-003 | US-IB-11 | AC-IB-11-04 | 默认配置表 | 读取各项默认值 | 可变行为均有显式默认，无硬编码主机/端口 |
| TC-UNIT-004 | US-IB-11/12 | AC-IB-11-03/12-03 | 缺项/非法配置 | 校验配置 | 报错仅列**键名**，不含值/凭据 |
| TC-UNIT-005 | US-IB-11/12 | AC-IB-11-04/12-02 | secret 类键 | 读取 secret | 仅从环境变量取，未配置则报错不落默认 |
| TC-UNIT-006 | US-IB-11/12 | AC-IB-11-03/12-03 | 非法整型 env | 解析 | 抛错并指明键名 |
| TC-UNIT-007 | US-IB-11 | AC-IB-11-04 | 原始配置 | normalize | 语义保持（仅补齐默认，不改语义） |
| TC-UNIT-008 | US-IB-05/04 | AC-IB-05-01/04-03 | 长文本 | 切分 | 相邻块有重叠，无空块 |
| TC-UNIT-009 | US-IB-05 | AC-IB-05-01 | 非法块参数 | 切分 | 显式拒绝非法参数 |
| TC-UNIT-010 | US-IB-05 | AC-IB-05-01 | 多段文本 | 切分 | 保留溯源地标，丢弃空内容 |
| TC-UNIT-011 | US-IB-05/16 | AC-IB-05-02/03 | 已入库文档 | 改切分参数 | 仅新文档用新参数，旧文档不自动重切 |
| TC-UNIT-012 | US-IB-01 | AC-IB-01-04 | 正/负样本 | sniff_magic | 伪造扩展名被识破 |
| TC-UNIT-012b | US-IB-01 | AC-IB-01-04 | 多字节前缀截断 | sniff_magic | 截断的多字节序列不误拒 |
| TC-UNIT-013 | US-IB-04 | AC-IB-04-05 | 未注册扩展名 | 注册表解析 | 显式报错；新格式可注册 |
| TC-UNIT-014 | US-IB-04 | AC-IB-04-01/03 | Markdown 文档 | 解析 | 溯源地标可读（标题层级/段落序号） |
| TC-UNIT-015 | US-IB-04 | AC-IB-04-03 | 空文本 | 解析 | 记 WARNING，不崩 |
| TC-UNIT-016 | US-IB-19（R11 重挂，原 US-IB-08） | AC-IB-19-01（R11 重挂，原 AC-IB-08-01） | 事件流 | 渲染 SSE 帧 | 帧格式合法，done 收尾（终态事件恰一次；注：19-02 的结构化完成载荷见 §15 缺口登记） |
| TC-UNIT-017 | US-IB-19（R11 重挂，原 US-IB-08） | AC-IB-19-01（R11 重挂，原 AC-IB-08-01） | StreamEvent 别名 | 比较 | 别名恒等（同一对象；流式交付契约只有一个事件类型定义） |
| TC-UNIT-018 | US-IB-20（R11 重挂，原 US-IB-11） | AC-IB-20-01（R11 重挂，原 AC-IB-11-02） | 两会话 | 会话存储 | 项目间会话隔离（会话 A/B 不互相注入） |
| TC-UNIT-019 | US-IB-15 | AC-IB-15-01 | 空载荷 | 生成 related_images 事件 | 空即抑制，不发事件 |
| TC-UNIT-020 | US-IB-02/13 | AC-IB-02-01/13-04 | 含敏感键字段 | redact | 敏感键丢弃/掩码，日志无凭据 |
| TC-UNIT-021 | US-IB-13 | AC-IB-13-04 | 超长字符串 | redact | 截断，不长吐 |
| TC-UNIT-022 | US-IB-20（R11 重挂，原 US-IB-11） | AC-IB-20-06（R11 重挂，原 AC-IB-11-02） | 会话键 | 断言前缀 | 非法/跨项目前缀被拒（拒绝可识别） |
| TC-UNIT-023 | US-IB-07/08 | AC-IB-07-02 | 向量对 | cosine | 值域与性质正确（自相似=1、对称） |
| TC-UNIT-024 | US-IB-09 | AC-IB-09-02 | 专家分值 | score_experts | 取每专家最大命中分 |
| TC-UNIT-025 | US-IB-09 | AC-IB-09-01 | τ/边际参数 | decide | 单专家/多专家/空按阈值判定 |
| TC-UNIT-026 | US-IB-09 | AC-IB-09-01 | 语义路由 | SemanticRouter | 项目分区，故障 fail-open |
| TC-UNIT-027 | US-IB-15 | AC-IB-15-03 | 脏输出（围栏/散文/非法名/空数组） | 解析 | 提取合法专家；无合法则安全回退 |
| TC-UNIT-028 | US-IB-09 | AC-IB-09-05 | 带历史的查询 | current_query | 剥离历史取当前问句 |
| TC-UNIT-029 | US-IB-09 | AC-IB-09-01 | 单域问句 | 路由 | 恰一个专家，无额外分支 |
| TC-UNIT-030 | US-IB-09 | AC-IB-09-02 | 复合问句 | 路由 | 多专家并行候选（2~3） |
| TC-UNIT-031 | US-IB-09 | AC-IB-09-04 | 极端输入 | 路由 | 任何情况下不出现「无人应答」 |
| TC-UNIT-032 | US-IB-09 | AC-IB-09-04/06 | 域外问句 | 路由 | 转通用路径，不调工具 |
| TC-UNIT-033 | US-IB-09 | AC-IB-09-04 | 分类器故障 | 路由 | 确定性关键词回退，落默认专家 |
| TC-UNIT-034 | US-IB-09 | AC-IB-09-05 | 上一轮专家 | 路由 | 承接粘性专家 |
| TC-UNIT-035 | US-IB-09 | AC-IB-09-04 | 触发护栏的输入 | 路由 | 重路由至数据专家 |
| TC-UNIT-036 | US-IB-09 | AC-IB-09-07 | 同问句重复 | 路由 | 同输入同结果（确定性） |
| TC-UNIT-037 | US-IB-10 | AC-IB-10-01/02/04 | 专家注册表 | 加载与派生视图 | 派生视图自动含新专家，顺序稳定，缺提示文件走兜底 |
| TC-UNIT-038 | US-IB-10 | AC-IB-10-01/02 | 非法注册表 | validate_specs | 结构非法被拒（如多默认专家） |
| TC-UNIT-039 | US-IB-10 | AC-IB-10-01 | 不存在的专家 | get | 返回 None，不抛 |
| TC-UNIT-040 | US-IB-10 | AC-IB-10-03 | 已注册工具 | build_capability_digest | 摘要由名称+描述派生；空/异常返回空串不抛 |
| TC-UNIT-041 | US-IB-10/11 | AC-IB-10-03/11-06 | 已绑作用域工具 | 调用方传 scope 覆盖 | 绑定闭包忽略之（override 不可能） |
| TC-UNIT-042 | US-IB-10 | AC-IB-10-03 | 作用域参数 | bind_scope | 隐藏 scope 形参，不外泄 |
| TC-UNIT-043 | US-IB-07 | AC-IB-07-01 | ib_embed 配置 | 加载 | 仅消费 11 键闭集，未知键报错 |
| TC-UNIT-044 | US-IB-07 | AC-IB-07-01 | 缺 MODEL_PATH | 加载 | 键名级报错，不回显值 |
| TC-UNIT-045 | US-IB-07/12 | AC-IB-07-01/12-02 | ib_embed 配置 | 检查消费键与日志字段 | 只吃 `IB_EMBED_*`；日志无凭据、不含 model_path |
| TC-UNIT-046 | US-IB-07 | AC-IB-07-02 | FakeRuntime | 向量化 | 确定性、保序、归一化 |
| TC-UNIT-047 | US-IB-07 | AC-IB-07-01 | 加载失败 | FakeRuntime | 返回可读错误，不崩 |
| TC-UNIT-048 | US-IB-07 | AC-IB-07-02 | FakeEmbedder | 冷/热路径 | 同文自相似度 ≈ 1 |
| TC-UNIT-049 | US-IB-07 | AC-IB-07-01 | fake/inproc | descriptor | 恰五字段，字段集一致 |
| TC-UNIT-050 | US-IB-07 | AC-IB-07-01 | inproc 缺权重 | 构造 | DependencyUnavailableError 且点名 `IB_EMBED_MODEL_PATH` |
| TC-UNIT-051 | US-IB-07 | AC-IB-07-01 | 各 backend 值 | build_embedder | 值域 {http,inproc,fake}，未知回退 http |
| TC-UNIT-052 | US-IB-03/06 | AC-IB-03-02/06-04 | SQLite 台账 | 状态机/单租约/reap | 状态迁移合法，同时仅一租约，超时回收 |
| TC-UNIT-053 | US-IB-03/06 | AC-IB-03-02/06-04 | 图片关联行 | 幂等写/陈旧清理/级联 | 键幂等、陈旧行清理、删文档级联，跨项目不可见 |
| TC-UNIT-054 | US-IB-06 | AC-IB-06-01 | SQLite 连接 | PRAGMA | WAL + busy_timeout 生效 |
| TC-UNIT-055 | US-IB-03 | AC-IB-03-02 | `kb_segment` / `blob_ref_for` / `_blob_scope_of` | 校验规则与三处推导同源 | **（R4 新增）** `None`/`""` → `"default"`；写/读/删三路径落到同一 kb 段——FND-GROUP-D-03 单一真源不变式 |
| TC-UNIT-062 | US-IB-18 | AC-IB-18-02 | 两位专家（合法/撞词/大小写/空白/同专家内重复） | `validate` 判跨专家关键词撞车 | **（R8 登记）** 互不相交 → 通过；精确/大小写/空白重复 → `expert_keyword_collision` 且含冲突词与两专家名；同专家内重复不报 |
| TC-UNIT-063 | US-IB-18 | AC-IB-18-02 | 两位专家（合法/同标签/空白填充/空标签/大小写） | `validate` 判 `cn_label` 唯一 | **（R8 登记）** 互异 → 通过；精确/空白填充重复 → `expert_cn_label_duplicate`（`path=experts[b].cn_label`）；空标签由 `expert_text_missing` 承担；大小写不归一 |
| TC-UNIT-064 | US-IB-18 | AC-IB-18-02 | 默认注册表 + 默认派生文档 | 校验默认数据无撞车/无重标签 | **（R8 登记）** 默认 `keywords_map()`/`cn_map()` 无跨专家撞车、标签唯一；默认派生文档 `validate.ok is True` 且无误报（反向护栏） |
| TC-UNIT-065 | US-IB-18 | AC-IB-18-02 | 空/纯空白关键词；三名专家同词；大小写+空白叠加 | `validate` 关键词撞车的边界分支 | **（R8 新增）** 空/纯空白不误报；三名专家同词 → 2 条（首见者持有，`experts[b]/[c]` 各一）；叠加归一判撞车；精确 path `experts[b].keywords[<原样>]` |
| TC-UNIT-066 | US-IB-18 | AC-IB-18-02 | 三名专家同标签；全空白标签；同时撞词+同标签 | `validate` 标签唯一性的边界分支与两项独立性 | **（R8 新增）** 三名同标签 → 2 条且 path 归属正确；全空白跳过（交 `expert_text_missing`）；两项校验独立（两错误码并存） |
| TC-UNIT-067（R11 新增） | US-IB-19 | AC-IB-19-04 | 含内部分工词的交付文本；开关关/开 | `_strip_internal_labels` 确定性清洗 | **（R11 新增）** 内部标识（路由到/巡检诊断/专家/聚合）被删净、事实内容保留；开关关闭时原样返回——内部子任务产物不外流的确定性兜底 |
| TC-UNIT-068（R11 新增） | US-IB-19 | AC-IB-19-03 | thinking/content 两类事件 | `to_sse` 编码 + kind 比较 | **（R11 新增）** 两分区 kind 互异（可辨）、一帧只承载一个事件（不混帧）、思考文本不并入正文 |
| TC-UNIT-069（R11 新增） | US-IB-20 | AC-IB-20-05 | 已存会话 + 模拟进程重启 | `MemorySessionStore` 读写 | **（R11 新增）** 重启后的新存储读回 `None`（不静默复活旧会话）——状态丢失 fail-closed 的存储底座；delete 幂等 |
| TC-UNIT-070（R12 新增） | US-IB-19 | AC-IB-19-02 | `completion_event` 载荷 `None` / 空元组 / 有引用 | 构造终态事件并解析载荷 | **（R12 新增）** `None`→`data==""`（不臆造）；空元组→`[]`（可区分事实）；`had_content` 边界可辨；引用只含定位（无正文/字节/base64）；终态恒为 `done`（从不产 content） |
| TC-UNIT-071（R12 新增） | US-IB-19 | AC-IB-19-03 | `StreamEventKind` / `USER_VISIBLE_KINDS` | `is_user_visible` + kind 枚举 | **（R12 新增）** `reasoning` 默认**不可见**且不入白名单；6 个面向用户 kind 可见；未登记 kind 默认不可见（内部产物不外流）；既有 6 kind 逐位不变、`confirmation_required` 为追加第 7 |
| TC-UNIT-072（R12 新增） | US-IB-20 | AC-IB-20-02/20-05 | `SessionPersistencePolicy` / `SessionStateLossOutcome` / `GlobalConfig` 默认 | 读类型取值域与配置默认 | **（R12 新增）** 策略取值域 `{in_process, external}`、默认 `in_process`；状态丢失结局**唯一取值** `fail_closed_restart_required`（类型层不可表达「默认放行」）；`confirmation_gate_enabled`/`reasoning_stream_enabled` 默认 `False` |
| TC-UNIT-073（R12 新增） | US-IB-20 | AC-IB-20-04/20-05 | `SessionState`/`ConfirmationGateState`/`ResumePayload` | `can_resume` 三判据穷举 + `from_dict` 残缺载荷 | **（R12 新增）** 状态丢失/无中间态/gate_id 不符/未携决策/决策指向他门 → 全 `False`；残缺载荷恒 `decision=None`（绝不补成「默认批准」） |
| TC-UNIT-074（R12 新增） | US-IB-18 | AC-IB-18-02 | 单专家含空/纯空白关键词 | `validate` 专家**内部**关键词校验（第 12 项） | **（R12 新增 / BLK-R8-02）** `""`/`"   "` → `expert_keyword_empty`（各一条，path 用原文）；空词不误报为重复；跨专家非空同词不产生内部空码（范围不外溢） |
| TC-UNIT-075（R12 新增） | US-IB-18 | AC-IB-18-02 | 单专家归一化重复（大小写/空白）+ 跨专家对照 + 全异对照 | `validate` 专家**内部**重复校验（第 12 项） | **（R12 新增 / BLK-R8-02）** 归一化重复 → `expert_keyword_duplicate`（首见者持有，path 用后续词原文）；跨专家仍报旧码 `expert_keyword_collision`、**不**被新码误报；全异文档 `ok=True` 无误报 |

### 3.2 集成测试（105）

文件：`test_composition_retrieval.py`（11）、`test_lifecycle_page_images.py`（7）、`test_ib_embed_wire.py`（12）、`test_http_contract.py`（13）、`test_orchestration_related_images.py`（7）、`test_embed_conformance.py`（5）、`test_gaps_acceptance.py`（7）、`test_ops_contract.py`（**12**）、`test_blob_delete_scope_r4.py`（5）、`test_definition_config_r7.py`（**9**：R7 新增 8 + R8 新增 TC-INT-087）、`test_stream_session_lifecycle_int_r11.py`（**8，R11 新增**）、`test_stream_session_lifecycle_int_r12.py`（**9，R12 新增**）。

> **计数订正（诚实标注）**：`test_ops_contract.py` 实为 **12** 例（含 R5/R6 重建修复轮引入的 `TC-INT-072`，见 `docs/deployment_report.md` §… ），此前本计划记为 11 —— 导致「集成 78 / 合计 148」的旧计数比实测少 1。本轮以**实测**为准：基线 **149**（单元 56 / 集成 79 / E2E 14）。

| TC-ID | 关联 US | 关联 AC | 前置 | 动作 | 预期结果 |
|-------|--------|--------|------|------|---------|
| TC-INT-001 | US-IB-11 | AC-IB-11-01 | 组合根装配 | 检查各端口/项目/前缀/工具 | 端口齐备、前缀断言通过、未登记项目报 StartupError |
| TC-INT-002 | US-IB-11 | AC-IB-11-01 | 装配 | 取两项目编排器 | 同项目复用同一对象，不同项目不同 |
| TC-INT-003 | US-IB-01/06/08 | AC-IB-01-05/06-01/08-01 | 真实上传管线 | 上传→处理→检索 | 命中该文档且不降级 |
| TC-INT-004 | US-IB-06/11 | AC-IB-06-02/11-02 | 甲项目语料 | 乙项目检索 | 空命中（项目硬隔离） |
| TC-INT-005 | US-IB-14/07 | AC-IB-14-01/07-03 | embedder 故障 | 检索 | degraded 结果，reason=EMBEDDING_UNAVAILABLE，不抛 |
| TC-INT-006 | US-IB-14 | AC-IB-14-03 | 向量库故障 | 检索 | degraded，reason=VECTORSTORE_UNAVAILABLE，不抛 |
| TC-INT-007 | US-IB-08/14 | AC-IB-08-02/14-02 | 三态 | search_as_tool | 降级/空/命中均 ok=True |
| TC-INT-008 | US-IB-10 | AC-IB-10-03 | 绑定 p_beta 工具 | 调用方传 scope=p_alpha | 覆盖无效，不泄漏甲项目内容 |
| TC-INT-009 | US-IB-10 | AC-IB-10-03 | 组合根 | 读 capability_digest + 路由提示 | **（R3 翻转）** 摘要非空且含 `search_knowledge`；路由提示非「（无可用工具）」——FND-GROUP-D-01 回归守卫 |
| TC-INT-010 | US-IB-04/16 | AC-IB-04-06 | `_process_one` 记录代理 | 处理一份含图文档 | 写序：向量 → 页面图 → 块 → mark_indexed |
| TC-INT-011 | US-IB-16 | AC-IB-16-02 | 空队列 | process_pending | 无操作且报告状态正确 |
| TC-INT-012 | US-IB-04 | AC-IB-04-06 | 解析结果 | bind_page_images | 按页聚合，确定性输出 |
| TC-INT-013 | US-IB-04/03 | AC-IB-04-06/03-02 | 图片绑定 | persist_page_images | 幂等，陈旧行被清理 |
| TC-INT-014 | US-IB-03 | AC-IB-03-02 | 含图文档 | 删除 | 级联清理页面图与台账行 |
| TC-INT-015 | US-IB-14/16 | AC-IB-14-04/16-04 | 单文档失败 | 批处理 | 单文档失败不影响其他文档 |
| TC-INT-016 | US-IB-02/16 | AC-IB-02-02/16-02 | failed 文档 | 重试 | 仅 failed 可重试；重试幂等无重复块 |
| TC-INT-017 | US-IB-07 | AC-IB-07-01 | 回环 ib_embed 服务 | GET /healthz | 永不 5xx |
| TC-INT-018 | US-IB-07 | AC-IB-07-01 | 服务 | POST /embed | 保序，维度以服务端为准 |
| TC-INT-019 | US-IB-07 | AC-IB-07-01 | 超批上限 | POST /embed | 回显 max_batch 并拒绝超批 |
| TC-INT-020 | US-IB-07 | AC-IB-07-01 | 模型不匹配 | POST /embed | 409 |
| TC-INT-021 | US-IB-07/14 | AC-IB-07-01/14-01 | 未 ready | POST /embed | 503（不返回部分向量） |
| TC-INT-022 | US-IB-07 | AC-IB-07-01 | 非法请求体 | POST /embed | 400，且无部分结果 |
| TC-INT-023 | US-IB-07 | AC-IB-07-01 | 参差输出 | POST /embed | 500，且不返回部分向量 |
| TC-INT-024 | US-IB-07/13 | AC-IB-07-01/13-02 | 过载（并发 1/队列 0） | POST /embed | 503 + retry_after_s |
| TC-INT-025 | US-IB-07 | AC-IB-07-01 | 服务 | POST /warmup ×2 | 幂等 |
| TC-INT-026 | US-IB-07/14 | AC-IB-07-01/14-01 | 加载失败 | POST /warmup | 快速失败 500 |
| TC-INT-027 | US-IB-07 | AC-IB-07-01 | 服务 | GET /descriptor | 恰五字段 |
| TC-INT-028 | US-IB-07 | AC-IB-07-01 | 服务 | 未知路径 + 查询串 | 404；查询串被丢弃 |
| TC-INT-029 | US-IB-13/12 | AC-IB-13-02/12-05 | HTTP 客户端 | GET /healthz、/healthz/deps | 免鉴权 200；依赖健康与 egress.remote=False 如实 |
| TC-INT-030 | US-IB-11 | AC-IB-11-05 | 无/错令牌 | GET /api/files | 401，不静默通过 |
| TC-INT-031 | US-IB-11 | AC-IB-11-05 | 查询串含令牌 | 各端点 | 一律 400 `token_in_query_forbidden`（IC-IB-01） |
| TC-INT-032 | US-IB-11 | AC-IB-11-05 | X-IB-Project 不符 | GET /api/files | 403 `project_mismatch` |
| TC-INT-033 | US-IB-01/03 | AC-IB-01-01/03-01/03-02 | 上传件 | 上传→列表→删除 | 201/字段白名单/删除生效 |
| TC-INT-034 | US-IB-01 | AC-IB-01-02/01-04 | 伪造扩展名 | 上传 | 400，不落台账 |
| TC-INT-035 | US-IB-11/06 | AC-IB-11-05/06-02 | 他项目 kb_id | 上传 | 403，不留痕 |
| TC-INT-036 | US-IB-04/03 | AC-IB-04-06 | 有字节的图关联 | GET 图片 | 200 + 固定 MIME + nosniff + private cache |
| TC-INT-037 | US-IB-03/11 | AC-IB-03-03/11-02 | 图关联 | 多 404 变体（缺行/无字节/跨项目） | 一律 404，反存在性探测 |
| TC-INT-038 | US-IB-11 | AC-IB-11-05 | 图片端点 | `?token=` | 400 |
| TC-INT-039 | US-IB-19（R11 重挂，原 US-IB-08） | AC-IB-19-01（R11 重挂，原 AC-IB-08-01） | SSE 端点 | 缺 q / 正常请求 | 400 / text/event-stream，事件序合法 |
| TC-INT-040 | US-IB-16 | AC-IB-16-01 | 重建端点 | POST /api/rebuild | 202 + job_id，进度可查 |
| TC-INT-041 | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配未绑库 | 上传后立即删除 | **（R3 翻转，R4 强化）** 200 且 `ledger_deleted=True`、`vectors_deleted=0`、`blob_deleted=True` 且原文件引用失效，列表消失，再删 404——FND-GROUP-D-02 + FND-GROUP-D-03 回归守卫 |
| TC-INT-042 | US-IB-09 | AC-IB-09-03 | 编排器 | 运行一次问答 | 事件序 reasoning→content→done，content 仅一条 |
| TC-INT-043 | US-IB-14 | AC-IB-14-01 | LLM 故障 | 运行问答 | degraded 早于 content，done 收尾 |
| TC-INT-044 | US-IB-04 | AC-IB-04-06 | 有图关联的命中 | 调 provider | 载荷只含站内路径，绝无 base64 |
| TC-INT-045 | US-IB-11 | AC-IB-11-02 | provider 作用域 | 跨项目命中 | None，不泄漏存在性 |
| TC-INT-046 | US-IB-04 | AC-IB-04-06 | 注入非空载荷 | 运行问答 | 事件在 content 后、done 前到达（接缝可用） |
| TC-INT-047 | US-IB-14 | AC-IB-14-01 | 空载荷 / provider 抛错 | 运行问答 | 不发事件、不中断（fail-open） |
| TC-INT-048 | US-IB-04 | AC-IB-04-06 | 生产编排器 + 库中有图 | 运行问答 | 固化 D-R2-02：生产恒不发图（登记行为，非缺陷） |
| TC-INT-049 | US-IB-07 | AC-IB-07-01 | 三 backend | build_embedder | 三形态同构描述子，方法齐备 |
| TC-INT-050 | US-IB-07 | AC-IB-07-01 | 干净解释器 | 导入 ib_embed 全模块 | 零 `ib.*` 耦合（C8） |
| TC-INT-051 | US-IB-07 | AC-IB-07-02 | 回环服务 | LocalHttpEmbedder 冷/热 | 保序、维度一致、冷热对齐、健康可读 |
| TC-INT-052 | US-IB-14 | AC-IB-14-01 | 不可达 base_url | embed_query | DependencyUnavailableError；health 不抛 |
| TC-INT-053 | US-IB-11 | AC-IB-11-03 | 非法 backend | 配置校验 | 值域闭集被拒 |
| TC-INT-054 | US-IB-06/16 | AC-IB-06-01/06-04/16-01 | 两项目 | count/清理/维度不变式 | 项目即 collection；按 scope 清理；换维度显式报错 |
| TC-INT-055 | US-IB-01 | AC-IB-01-03 | 超限文件 | validate_upload | ValidationError（含上限），不落台账 |
| TC-INT-056 | US-IB-04 | AC-IB-04-04 | `.xlsx` | validate_upload | 可读报错点名格式与支持清单，不落台账 |
| TC-INT-057 | US-IB-02 | AC-IB-02-03 | indexed 文档 | retry_document | ConflictError 回显当前状态，数据不变 |
| TC-INT-058 | US-IB-03 | AC-IB-03-04 | 不存在的 doc_id | HTTP 删除 | 404 `not_found` |
| TC-INT-058b | US-IB-02 | AC-IB-02-03 | indexed 文档 | HTTP 重试 | 409 `conflict` |
| TC-INT-059 | US-IB-11 | AC-IB-11-06 | 干净解释器 | 导入 ib.orchestration | 无 Django/DRF 业务载体耦合 |
| TC-INT-060 | US-IB-06 | AC-IB-06-02 | 同项目两 kb | 按 kb 作用域检索 | 互不可见（软隔离 filter） |
| TC-INT-061 | US-IB-02/03 | AC-IB-02-04/03-03 | 未绑库 fresh 装配 | 上传→删→ worker 处理 | **（R3 翻转）** 删除成功、台账行消失、worker 不认领、检索为空、无向量残留——FND-GROUP-D-02 回归守卫 |
| TC-INT-069 | US-IB-03 | AC-IB-03-02 | 已索引文档 | 删除并观测 `DeleteReport` 与清扫次数 | **（R3 新增）** 三计数语义 + 两次清扫（第二次为 0）+ 列表/台账/切块/向量/对账五不变式 |
| TC-INT-070 | US-IB-03 | AC-IB-03-03 | 已索引文档 | 删除 → 再跑 `process_pending` | **（R3 新增）** 删除后不可检索；重跑不复活（可见性权威 = 台账） |
| TC-INT-071 | US-IB-02 | AC-IB-02-04 | pending 文档 + 真并发（2 线程） | worker 处理中被删除 | **（R3 新增，真并发）** 计数为 `skipped`（非 failed），无未捕获异常，无残留 |
| TC-INT-073 | US-IB-10 | AC-IB-10-03 | 组合根 | 绑定工具名集合 vs 摘要工具名集合 | **（R3 新增）** 两集合逐名相等（防漂移不变式），跨项目一致 |
| TC-INT-062 | US-IB-07 | AC-IB-07-03 | 冷/热配置 | 读配置 + 驱动检索 | cold 超时/重试严格宽于 hot；查询走有界超时 |
| TC-INT-063 | US-IB-10 | AC-IB-10-05 | 专家注册表 | 读委派标记 + 步数上限 | 非委派专家不获子委托；深度有硬上限 |
| TC-INT-064 | US-IB-12 | AC-IB-12-05 | 离线/远程 LLM | describe_egress | 离线 remote=False；远程 remote=True + 端点 + 数据类别 |
| TC-INT-065 | US-IB-13 | AC-IB-13-01 | 内存日志 handler | log_event | JSON 行含阶段/结果/项目/文档/耗时/计数字段 |
| TC-INT-066 | US-IB-13/14 | AC-IB-13-02/14-01 | degrade sink | emit_degrade ×2 | sink 收到 (reason, stage)，可定位故障依赖 |
| TC-INT-067 | US-IB-13 | AC-IB-13-03 | 内存日志 handler | 运行期改级别 | 立即生效，无需改代码/重建 |
| TC-INT-068 | US-IB-06 | AC-IB-06-05 | 替身向量库 | 端口方法 + 上层链路 | 端口齐备，上传/入库/检索链路不改即可跑通 |
| TC-INT-074 | US-IB-03 | AC-IB-03-02 | kb 级上传 + 项目级 scope 删除（错配路径） | 删除并做**真实文件系统**断言 | **（R4 新增）** `blob_deleted=True`；`FsBlobStore.root` 下该 doc 字节/目录/空 kb 目录**全部不存在**——FND-GROUP-D-03 回归守卫 |
| TC-INT-075 | US-IB-03 | AC-IB-03-02 | 真实 Django HTTP DELETE + 真实 `FsBlobStore` | 上传→HTTP 删除→磁盘核验 | **（R4 新增）** `blob_deleted=True`；存储根下无任何残留文件（复用 R3 探针构造方式，同一条真实 HTTP 路径） |
| TC-INT-076 | US-IB-03 | AC-IB-03-02 | `data=None`（D-08，`content_sha256` 为空） | 删除并观 `blob_deleted` | **（R4 新增）** 本无原文件 → `blob_deleted is False`（**不得恒 True 掩盖**）；删除仍成功 |
| TC-INT-077 | US-IB-03 | AC-IB-03-02 | 跨项目：p_alpha / p_beta 同内容 + 同 doc_id | 删 p_alpha 的 doc | **（R4 新增）** p_beta 的同内容/同 doc_id blob **仍在**（不越界误删） |
| TC-INT-078 | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配 + 项目级 scope，未处理文档 | 上传→HTTP 删除→再跑 worker | **（R4 新增）** 200（无 500）、`vectors_deleted=0`、台账行消失、worker 不再认领（不回归 FND-GROUP-D-02） |
| TC-INT-087 | US-IB-18 | AC-IB-18-02/18-06 | 非法文档（撞词 + 同标签）+ 真实端点 | `admit` 闸门 + `PUT /api/config/definition` | **（R8 新增）** 装配闸门聚合拒绝（`validation_items` 含两新码且条数一致）；端点改 `cn_label`/`keywords` → 400 逐条回执两新码；非法配置不静默生效（`content_hash` 未变）——FND-R7-01 跨模块回归守卫 |

| TC-INT-088（R11 新增） | US-IB-19 | AC-IB-19-01 | 编排器（单专家） | `run` 全事件序列 | **（R11 新增）** `done` 恰一次且收尾、其后无内容片段；内容分片顺序拼接 == 最终答复；无空内容片段 |
| TC-INT-089（R11 新增） | US-IB-19 | AC-IB-19-04 | 强制双专家路由（fake llm 双标签作答） | `run` 事件载荷 | **（R11 新增）** 面向用户只有一条 `content`（不逐专家推送）；专家原始作答与内部标签（数据管家/巡检诊断）不出现在任何事件 |
| TC-INT-090（R11 新增） | US-IB-19 | AC-IB-19-03 | 编排器真实流 | reasoning 与 content 分区 | **（R11 新增）** 两分区 kind 互异且进度先于正文；思考文本不并入正文；每帧只承载一个事件 |
| TC-INT-091（R11 新增） | US-IB-19 | AC-IB-19-05 | 全链路降级（fake llm unavailable） | `run` 事件序列 | **（R11 新增）** 不推送空内容片段；终止事件恰一次；无任何事件臆造引用列表 |
| TC-INT-092（R11 新增） | US-IB-20 | AC-IB-20-01 | 共享会话存储 + 会话 A 预置标记 | 在会话 B 跑一轮 | **（R11 新增）** B 的历史不含 A 的标记（不跨会话注入）；A 状态保持独立不被覆写；未识别的会话标识读回 `None` |
| TC-INT-093（R11 新增） | US-IB-20 | AC-IB-20-02/20-05 | 确认门关 / 门开但状态丢失 | `resume` 两情形 | **（R11 新增）** 两情形均 `error`+`done` 安全失败，**无** `content`（不静默续跑挂起动作） |
| TC-INT-094（R11 新增） | US-IB-20 | AC-IB-20-03 | 默认 `GraphConfig` | 跑一轮正常问答 | **（R11 新增）** 确认门默认关闭；关闭时不出现确认等待事件，直接正常完成 |
| TC-INT-095（R11 新增） | US-IB-20 | AC-IB-20-06 | 跨项目键 + 伪造/非法键 | 存储读写 + 归属断言 | **（R11 新增）** 无前缀 / 非法键读写均被拒（不静默当新会话）；跨项目归属断言抛 `ScopeViolationError`（拒绝可识别） |
| TC-INT-096（R12 新增） | US-IB-20 | AC-IB-20-04 | 确认门启用 + 注入话术构造器 | `run` 全事件序列 + 会话落库 | **（R12 新增）** 事件恰为 `reasoning → confirmation_required → done`；呈递恰一次、无 content、无空帧（除终态）；待确认中间态落库（`gate` 可对账、原提问入 `turns`） |
| TC-INT-097（R12 新增） | US-IB-20 | AC-IB-20-04 | 已挂起会话 + 携「批准」决策 | `resume` 续跑 | **（R12 新增）** 续跑产出 content + 终态 `done`；不再触发 `confirmation_required`（不自我死锁）；中间态被清除 |
| TC-INT-098（R12 新增） | US-IB-20 | AC-IB-20-04/20-05 | 无中间态 / 无决策 / gate_id 不符 / 决策为拒 | `resume` 四种负例 | **（R12 新增）** 四种均 `error` + 终态、**无** content（不重跑未经确认的动作） |
| TC-INT-099（R12 新增） | US-IB-20 | AC-IB-20-04 | 真实 HTTP + 真实流路径键（3 段） | `POST /api/chat/resume` 携决策 | **（R12 新增 / MAJOR-1）** 200 + `text/event-stream`，content 后 done；续跑后中间态清除——视图经唯一入口重建同键（不自造 2 段键） |
| TC-INT-100（R12 新增） | US-IB-20 | AC-IB-20-01/20-04/20-05 | 会话不存在 / 无 gate / 自造 2 段键 / 无决策 / gate_id 不符 / `?token=` | HTTP 续跑负例族 | **（R12 新增 / MAJOR-1 守卫）** 404（不存在/无 gate/2 段键）、409（无决策/不符）、400（`?token=`）；自造 2 段键**不得**命中 3 段真实会话 |
| TC-INT-101（R12 新增） | US-IB-20 | AC-IB-20-01 | 缺 `session_id` / 显式合法 `session_id` | `GET /api/chat/stream` | **（R12 新增 / FND-R11-01）** 缺 `session_id` → **400** 且**不开流**（不回退默认会话）；显式合法 → 200 + `text/event-stream` |
| TC-INT-102（R12 新增） | US-IB-20 | AC-IB-20-03 | 门关（有构造器）/ 门开无构造器 / 构造抛异常 | `run` 事件序列对比 | **（R12 新增）** 前两态零行为差异（序列逐位相同、无 `confirmation_required`）；构造抛异常 → fail-closed（`error`+终态，**无** content） |
| TC-INT-103（R12 新增） | US-IB-19 | AC-IB-19-02/19-05 | 真实 `run` | 终态载荷解析 | **（R12 新增）** `done` 恰一次且收尾、其后无 content；未产出产物时 `done.data==""`（**不臆造**引用清单）；无任何事件载荷含 `citations` 键 |
| TC-INT-104（R12 新增） | US-IB-20 | AC-IB-20-03 | 确认门未启用（独立装配） | `POST /api/chat/resume` | **（R12 新增）** **409** `conflict`、**不开流**（不新建会话、不重跑） |

> **R7 集成用例明细**（TC-INT-079~086，8 条）不在本表重复列出，见 **§11.2**（R7 增量清单）；本表 TC-INT-087 为 R8 新增的跨模块接缝用例，TC-INT-088~095 为 R11 新增的流式交付 / 会话生命周期用例（明细见 **§15**），TC-INT-096~104 为 R12 新增（明细见 **§16**）。

### 3.3 E2E / 关键路径（19）

文件：`tests/e2e/test_user_journeys.py`。关键路径以 Must Have 故事标注（R7 新增 TC-E2E-015/016；R11 新增 TC-E2E-017/018；R12 新增 TC-E2E-019）。

| TC-ID | 关联 US | 关联 AC | 旅程 | 预期结果 |
|-------|--------|--------|------|---------|
| TC-E2E-001（关键路径） | US-IB-01 + US-IB-08 | AC-IB-01-01/01-05/08-01 | HTTP 上传 → worker 处理 → 检索命中 → SSE 问答 | 201→indexed→命中→content+done |
| TC-E2E-002（关键路径） | US-IB-02 | AC-IB-02-01/02-02 | 依赖故障 → 失败可诊断 → 人工重试 → 恢复 | failed(error_code)→HTTP 重试 200→indexed |
| TC-E2E-003（关键路径） | US-IB-03 | AC-IB-03-02/03-03 | 入库 → 删除 → 再检索 | 删除 200，检索不再命中，台账行消失，**原文件字节亦清理（R4 强化）** |
| TC-E2E-004（关键路径） | US-IB-09 | AC-IB-09-02/09-03 | 复合问题 → 多专家 → 融合 | ≥2 专家，仅一条 content，done 收尾 |
| TC-E2E-005（关键路径） | US-IB-10 | AC-IB-10-01/10-03/10-04 | 注册新工具 → 能力摘要 → 立即绑定 | 摘要含新工具，绑定即用；内置注册表结构合法 |
| TC-E2E-006（关键路径） | US-IB-11 + US-IB-06 | AC-IB-11-01/11-02/06-02 | 两项目配置 → 各自入库 → 交叉检索 | 各见己方语料；乙项目看不到甲项目文档 |
| TC-E2E-007（关键路径） | US-IB-04 + US-IB-05 | AC-IB-04-01/04-03/05-02 | 多格式（md/txt/docx）导入 + 切分参数 | 均可达检索；docx 真实解析入库 |
| TC-E2E-008 | US-IB-13 | AC-IB-13-01/13-02 | 观察运行状态 | /healthz 与 /healthz/deps 反映各依赖 |
| TC-E2E-009（关键路径） | US-IB-14 | AC-IB-14-01 | LLM 依赖故障 → 降级不断流 | degraded 早于 content，仍出 done |
| TC-E2E-010（关键路径） | US-IB-12 | AC-IB-12-03 | 未配置项目 → 启动 | StartupError（fail-fast，不静默起服务） |
| TC-E2E-011 | US-IB-16 | AC-IB-16-01/16-04 | 重建索引旅程 | 202 → 进度 indexed ≥ 1 |
| TC-E2E-012 | US-IB-15 | AC-IB-15-01/15-04 | 离线替身装配 | 替身列齐备，egress.remote=False |
| TC-E2E-013 | US-IB-04 | AC-IB-04-06 | 图片接缝端到端 | 命中 → related_images 路径 → 按 url_path 取图 200 |
| TC-E2E-014（关键路径） | US-IB-07 | AC-IB-07-01/07-02 | embedding 接入端到端 | 维度一致、入库→检索通、冷热自相似≈1、无外发 |
| TC-E2E-015（关键路径，R7 新增） | US-IB-17 | AC-IB-17-01/17-02/17-03/17-04 | 打开配置页 → 编辑白名单字段保存 → 重载以文档为准无漂移 → 改拓扑被拒 → 他处改动后重载以文档为准、陈旧回写 409 | 写回唯一真源、无第二副本、往返无漂移、拓扑不可编辑、不反向覆盖 |
| TC-E2E-016（关键路径，R7 新增） | US-IB-18 | AC-IB-18-01/18-02/18-04/18-06 | 合法即装配且图编译一次常驻 → 非法提交 400 定位条目不静默生效 → 装配闸门聚合拒绝 → 缺失文档显式报错 | 装配期 fail-fast、聚合全部校验项、无强制继续、错误体无凭据值 |
| TC-E2E-017（关键路径，R11 新增） | US-IB-19 | AC-IB-19-01/19-05 | 文档入库 → 真实 HTTP `GET /api/chat/stream` → 逐帧 SSE | 200 + `text/event-stream`；恰一个 `done` 且收尾；正文片段非空 |
| TC-E2E-018（关键路径，R11 新增） | US-IB-20 | AC-IB-20-01 | 两个显式 `session_id` 各跑一轮真实 HTTP SSE | 两会话各自独立成流、各恰一次终态收尾、互不阻断 |
| TC-E2E-019（关键路径，R12 新增） | US-IB-20 | AC-IB-20-04/20-05 | 普通会话（无门）→ 预置待确认中间态 → `POST /api/chat/resume` 携决策续跑 → 中间态清除 → 对已恢复会话再恢复被拒 | 默认零等待成流；续跑 200 SSE content+done；中间态清除后再走普通问答正常；再恢复 404（不重跑）、无决策 409 |

---

## §4 AC → TC 覆盖矩阵（可测性判定）

> 判定口径：`Tested` = 有至少一条**真实执行**的 TC 覆盖；`NOT_TESTABLE` = 本机不可验证（原因见 §5）。
> 可测 AC：**90**（101 - 11 NOT_TESTABLE）；**已覆盖 90/90 = 100%**（R12 起，AC-IB-19-02 / AC-IB-20-04 已闭合；0 项未覆盖）；不可测 AC：11（已登记，不参与通过率）；AC 总数 **101**（1.3.0 / 20 US，R11 新增 US-IB-19/20 共 11 组）。
> R7 新增 12 组 AC（AC-IB-17-01~06、AC-IB-18-01~06）逐条映射见本表末与 §11.2；其中
> AC-IB-17-05 / AC-IB-17-06 为 `Tested（部分）`（服务端/源码级已覆盖，前端**运行期**子句离线不可验，见 §5 附表）。
> **R11 新增 11 组 AC**（AC-IB-19-01~05 / AC-IB-20-01~06）逐条映射见本表末与 §15.3。
> **R12 起**：AC-IB-19-02 / AC-IB-20-04 由「未覆盖」转 `Tested`；AC-IB-20-01 / 20-03 转 **`Tested`（完整）**（FND-R11-01 已修复、门启用行为已覆盖）；AC-IB-19-03 / 20-02 / 20-05 转 `Tested（完整，残余登记见 §16.5）`；AC-IB-19-02 端到端「命中→产物」装配来源登记为残余（§16.5）。

| AC | 级别 | 覆盖 TC | 判定 |
|----|------|---------|------|
| AC-IB-01-01 | INT/E2E | TC-INT-033, TC-E2E-001 | Tested |
| AC-IB-01-02 | INT | TC-INT-034（服务端 4xx）；前端浏览器侧拦截属前端，未验证 | Tested（服务端部分） |
| AC-IB-01-03 | INT | TC-INT-055 | Tested |
| AC-IB-01-04 | UNIT/INT | TC-UNIT-012, TC-UNIT-012b, TC-INT-034 | Tested |
| AC-IB-01-05 | INT/E2E | TC-INT-003, TC-E2E-001 | Tested |
| AC-IB-01-06 | — | — | NOT_TESTABLE（页面自动刷新为纯前端行为，本轮无前端运行环境） |
| AC-IB-02-01 | UNIT/E2E | TC-UNIT-020, TC-E2E-002 | Tested |
| AC-IB-02-02 | INT/E2E | TC-INT-016, TC-E2E-002 | Tested |
| AC-IB-02-03 | INT | TC-INT-057, TC-INT-058b | Tested |
| AC-IB-02-04 | INT | TC-INT-061, TC-INT-071（R3 回归：处理中删除安全跳过 skipped） | Tested |
| AC-IB-03-01 | INT | TC-INT-033 | Tested |
| AC-IB-03-02 | INT/UNIT/E2E | TC-INT-033, TC-INT-014, TC-INT-041, TC-INT-069, TC-INT-074, TC-INT-075, TC-INT-076, TC-INT-077, TC-INT-078, TC-UNIT-055, TC-E2E-003 | Tested |
| AC-IB-03-03 | E2E/INT | TC-E2E-003, TC-INT-061, TC-INT-070, TC-INT-078 | Tested |
| AC-IB-03-04 | INT | TC-INT-058 | Tested |
| AC-IB-04-01 | E2E/UNIT | TC-E2E-007, TC-UNIT-014 | Tested |
| AC-IB-04-02 | — | — | NOT_TESTABLE（PDF 文本层解析需 pypdf/pdfminer，本机缺失） |
| AC-IB-04-03 | E2E/UNIT | TC-E2E-007, TC-UNIT-014, TC-UNIT-008 | Tested |
| AC-IB-04-04 | INT | TC-INT-056 | Tested |
| AC-IB-04-05 | UNIT | TC-UNIT-013 | Tested |
| AC-IB-04-06 | — | — | NOT_TESTABLE（扫描页 OCR 需 pypdfium2 + rapidocr，本机缺失） |
| AC-IB-04-07 | — | — | NOT_TESTABLE（图片 OCR 引擎缺失；仅降级跳过分支可测） |
| AC-IB-05-01 | UNIT | TC-UNIT-008, TC-UNIT-009, TC-UNIT-010 | Tested |
| AC-IB-05-02 | UNIT/E2E | TC-UNIT-011, TC-E2E-007 | Tested |
| AC-IB-05-03 | UNIT/E2E | TC-UNIT-011, TC-E2E-011 | Tested |
| AC-IB-06-01 | INT | TC-INT-003, TC-INT-054（结构等价于 InMemory；真实 Qdrant 未验证） | Tested（替身） |
| AC-IB-06-02 | INT/E2E | TC-INT-060, TC-INT-004, TC-E2E-006 | Tested |
| AC-IB-06-03 | — | — | NOT_TESTABLE（真实 Qdrant 重启持久化需部署，属 GROUP_E） |
| AC-IB-06-04 | INT | TC-INT-054, TC-INT-014 | Tested |
| AC-IB-06-05 | INT | TC-INT-068 | Tested |
| AC-IB-07-01 | E2E/INT | TC-E2E-014, TC-INT-049（维度一致 + 无云端调用；真实 bge-m3 推理未验证） | Tested（结构） |
| AC-IB-07-02 | UNIT/INT/E2E | TC-UNIT-048, TC-INT-051, TC-E2E-014 | Tested |
| AC-IB-07-03 | INT | TC-INT-062 | Tested |
| AC-IB-07-04 | — | — | NOT_TESTABLE（许可类型为文档性结论，无运行期可断言行为） |
| AC-IB-07-05 | — | — | NOT_TESTABLE（目标机推理延迟需目标机实测） |
| AC-IB-08-01 | INT/E2E | TC-E2E-001（TC-INT-039 已于 R11 重挂至 AC-IB-19-01） | Tested |
| AC-IB-08-02 | INT | TC-INT-007 | Tested |
| AC-IB-08-03 | INT | TC-INT-003, TC-INT-005 | Tested |
| AC-IB-08-04 | — | — | NOT_TESTABLE（千级文档 P95 延迟需目标机实测校准） |
| AC-IB-09-01 | UNIT | TC-UNIT-029 | Tested |
| AC-IB-09-02 | UNIT/E2E | TC-UNIT-030, TC-E2E-004 | Tested |
| AC-IB-09-03 | E2E/INT | TC-E2E-004, TC-INT-042 | Tested |
| AC-IB-09-04 | UNIT | TC-UNIT-031, TC-UNIT-032, TC-UNIT-033 | Tested |
| AC-IB-09-05 | UNIT | TC-UNIT-034 | Tested |
| AC-IB-09-06 | UNIT | TC-UNIT-032 | Tested |
| AC-IB-09-07 | UNIT | TC-UNIT-036 | Tested |
| AC-IB-10-01 | UNIT/E2E | TC-UNIT-037, TC-E2E-005 | Tested |
| AC-IB-10-02 | UNIT | TC-UNIT-037, TC-UNIT-038 | Tested |
| AC-IB-10-03 | UNIT/INT/E2E | TC-UNIT-040, TC-E2E-005, TC-INT-009, TC-INT-073（R3 修复后：摘要非空且与实绑工具一致） | Tested |
| AC-IB-10-04 | UNIT/E2E | TC-UNIT-037, TC-E2E-005 | Tested |
| AC-IB-10-05 | INT | TC-INT-063 | Tested |
| AC-IB-11-01 | E2E/INT | TC-E2E-006, TC-INT-001 | Tested |
| AC-IB-11-02 | INT/E2E | TC-INT-004, TC-INT-054, TC-E2E-006 | Tested |
| AC-IB-11-03 | UNIT | TC-UNIT-004, TC-UNIT-006 | Tested |
| AC-IB-11-04 | UNIT | TC-UNIT-003, TC-UNIT-005 | Tested |
| AC-IB-11-05 | INT | TC-INT-030, TC-INT-032, TC-INT-035 | Tested |
| AC-IB-11-06 | INT | TC-INT-059 | Tested |
| AC-IB-12-01 | — | — | NOT_TESTABLE（systemd 常驻/自启属部署，GROUP_E 冻结） |
| AC-IB-12-02 | UNIT | TC-UNIT-005（secret 仅环境变量注入）；仓库凭据扫描见报告 §6 | Tested |
| AC-IB-12-03 | UNIT/E2E | TC-UNIT-004, TC-UNIT-006, TC-E2E-010 | Tested |
| AC-IB-12-04 | — | — | NOT_TESTABLE（目标机原生依赖真装真跑属部署） |
| AC-IB-12-05 | INT | TC-INT-064, TC-INT-029 | Tested |
| AC-IB-13-01 | INT | TC-INT-065 | Tested |
| AC-IB-13-02 | INT | TC-INT-066, TC-INT-005, TC-INT-006 | Tested |
| AC-IB-13-03 | INT | TC-INT-067 | Tested |
| AC-IB-13-04 | UNIT | TC-UNIT-020, TC-UNIT-021 | Tested |
| AC-IB-14-01 | INT/E2E | TC-INT-005, TC-E2E-009 | Tested |
| AC-IB-14-02 | INT | TC-INT-007 | Tested |
| AC-IB-14-03 | INT | TC-INT-006 | Tested |
| AC-IB-14-04 | — | — | NOT_TESTABLE（单图 OCR 失败分支需 OCR 引擎，本机缺失） |
| AC-IB-14-05 | INT/E2E | TC-E2E-012, TC-INT-005, TC-INT-006 | Tested |
| AC-IB-15-01 | E2E | TC-E2E-012, TC-E2E-009 | Tested |
| AC-IB-15-02 | UNIT | TC-UNIT-001 ~ TC-UNIT-042 | Tested |
| AC-IB-15-03 | UNIT | TC-UNIT-027 | Tested |
| AC-IB-15-04 | INT/E2E | TC-INT-003, TC-E2E-001 | Tested |
| AC-IB-16-01 | E2E/INT | TC-E2E-011, TC-INT-054 | Tested |
| AC-IB-16-02 | INT/E2E | TC-E2E-011, TC-INT-016 | Tested |
| AC-IB-16-03 | INT | TC-INT-054 | Tested |
| AC-IB-16-04 | INT/E2E | TC-INT-015, TC-E2E-011 | Tested |
| AC-IB-17-01 | INT/E2E | TC-INT-079, TC-INT-081, TC-INT-084, TC-E2E-015 | Tested |
| AC-IB-17-02 | UNIT/INT/E2E | TC-UNIT-058, TC-INT-080, TC-E2E-015 | Tested |
| AC-IB-17-03 | INT/E2E | TC-INT-081, TC-INT-084, TC-INT-086, TC-E2E-015 | Tested |
| AC-IB-17-04 | UNIT/INT | TC-UNIT-059, TC-INT-084, TC-INT-086, TC-E2E-015 | Tested |
| AC-IB-17-05 | UNIT/INT | TC-UNIT-060, TC-INT-084, TC-INT-086 | Tested（部分）——定义层/端点/源码级已覆盖；前端**渲染期**不回显子句属前端运行期，离线不可验（§5 附表） |
| AC-IB-17-06 | INT | TC-INT-086 | Tested（部分）——「数据不出本机 + 本地打包无 CDN」已覆盖；「**禁 Docker / 全物理机裸装**运行形态」属部署，本轮冻结（§5 附表） |
| AC-IB-18-01 | UNIT/INT/E2E | TC-UNIT-061, TC-INT-085, TC-E2E-016 | Tested |
| AC-IB-18-02 | UNIT/INT/E2E | TC-UNIT-057, TC-UNIT-062~066, TC-UNIT-074, TC-UNIT-075, TC-INT-082, TC-INT-087, TC-E2E-016 | **Tested（完整，R8 起；R12 补齐专家内部项）**——全部非法项（含跨专家「路由关键词撞车」`expert_keyword_collision`、「cn_label 重复」`expert_cn_label_duplicate`，及 R12 补测的**专家内部**空/重复 `expert_keyword_empty` / `expert_keyword_duplicate`）均被拒并定位；FND-R7-01 → CLOSED_VERIFIED（报告 §13.8）、BLK-R8-02 → CLOSED_VERIFIED（报告 §17） |
| AC-IB-18-03 | UNIT/E2E | TC-UNIT-057, TC-UNIT-061, TC-E2E-016 | Tested |
| AC-IB-18-04 | UNIT/INT | TC-UNIT-060, TC-INT-082, TC-INT-084, TC-E2E-016 | Tested |
| AC-IB-18-05 | UNIT | TC-UNIT-056 | Tested |
| AC-IB-18-06 | INT/E2E | TC-INT-082, TC-INT-083, TC-E2E-016 | Tested |
| AC-IB-19-01 | UNIT/INT/E2E | TC-UNIT-016, TC-UNIT-017, TC-INT-039, TC-INT-088, TC-E2E-017 | Tested |
| AC-IB-19-02 | UNIT/INT | TC-UNIT-070, TC-INT-103 | **Tested（机制层完整，R12 起）**——`completion_event` 结构化载荷语义与边界（`None`→空 / 空元组→`[]` / `had_content` 边界 / 引用只含定位）、终态恰一次且不做内容分片、不臆造引用均覆盖；**端到端**「检索命中→`CompletionPayload` 装配来源」登记为**残余**（编排恒传 `payload=None`，见 §16.5） |
| AC-IB-19-03 | UNIT/INT | TC-UNIT-068, TC-UNIT-071, TC-INT-090 | **Tested（R12 起覆盖默认口径）**——`reasoning` 默认不可见、可见性白名单、不混帧、「默认不出思考」（`IB_REASONING_STREAM_ENABLED` 默认 `False`）已覆盖；**启用后可见**的端上呈递属前端运行期，离线不可验（残余 §16.5） |
| AC-IB-19-04 | UNIT/INT | TC-UNIT-067, TC-INT-089 | Tested |
| AC-IB-19-05 | INT/E2E | TC-INT-091, TC-INT-103, TC-E2E-017 | Tested |
| AC-IB-20-01 | UNIT/INT/E2E | TC-UNIT-018, TC-INT-092, TC-INT-101, TC-E2E-018 | **Tested（完整，R12 起）**——会话隔离 + 「会话标识缺失须**显式 400 拒绝**、不得静默用默认会话」已覆盖（`GET /api/chat/stream` 缺 `session_id` → 400）；FND-R11-01 已修复 → CLOSED_VERIFIED（报告 §17） |
| AC-IB-20-02 | UNIT/INT | TC-UNIT-072, TC-INT-093 | **Tested（R12 起覆盖配置层声明）**——状态丢失 fail-closed + 持久化策略类型/配置默认（`SessionPersistencePolicy`、默认 `in_process`）已覆盖；「**部署文档**显式声明」属部署面，登记为残余（§16.5） |
| AC-IB-20-03 | INT | TC-INT-094, TC-INT-102, TC-INT-104 | **Tested（完整，R12 起）**——机制保留且默认关闭、关闭时不引入等待（零行为差异：门关 vs 无构造器序列逐位相同）、门未启用时恢复 409 均覆盖 |
| AC-IB-20-04 | UNIT/INT/E2E | TC-UNIT-073, TC-INT-096, TC-INT-097, TC-INT-099, TC-E2E-019 | **Tested（完整，R12 起）**——确认中间态呈递（`confirmation_required` 恰一次、无 content、落库）+ 决策回传恢复（HTTP 真实流路径键续跑至 `done`、不自我死锁）+ 负例 fail-closed 全族 |
| AC-IB-20-05 | UNIT/INT/E2E | TC-UNIT-069, TC-UNIT-072, TC-UNIT-073, TC-INT-093, TC-INT-098, TC-E2E-019 | **Tested（完整，R12 起）**——状态丢失/未携决策 fail-closed、`can_resume` 三判据穷举、携决策续跑、决策为拒即终止均覆盖 |
| AC-IB-20-06 | UNIT/INT | TC-UNIT-022, TC-INT-095 | Tested |

---

## §5 不可测试项（NOT_TESTABLE）

| AC-ID | 原因 | 影响 / 去向 |
|-------|------|------------|
| AC-IB-01-06 | 页面按周期自动刷新为纯前端行为，本轮无前端运行环境 | 前端构建/交互验证登记为 not-verified（报告 §6） |
| AC-IB-04-02 | PDF 文本层解析依赖 `pypdf`/`pdfminer.six`，本机均未安装 | 报告 §6 not-verified；PDF 相关代码覆盖率低（`pdf_parser.py` 12%） |
| AC-IB-04-06 | 扫描页整页渲染 OCR 依赖 `pypdfium2` + `rapidocr_onnxruntime`，本机缺失 | 同上 |
| AC-IB-04-07 | 图片 OCR 引擎缺失；仅「不可用时跳过 + WARNING」分支可测 | 同上 |
| AC-IB-06-03 | 真实 Qdrant 重启持久化需部署实例，属 GROUP_E | 报告 §6 not-verified |
| AC-IB-07-04 | 许可类型为文档性结论，无运行期可断言行为 | 由 `docs/tech_stack.md` §2 台账承载 |
| AC-IB-07-05 | 目标机 CPU 推理延迟需目标机以目标语料实测 | 报告 §6 not-verified；本机数据不可替代 |
| AC-IB-08-04 | 千级文档 P95 延迟需目标机实测校准 | 同上 |
| AC-IB-12-01 | systemd 常驻/开机自启属部署，GROUP_E 本轮冻结 | 报告 §6 not-verified；**不得触碰** |
| AC-IB-12-04 | 目标机原生依赖真装真跑属部署 | 同上 |
| AC-IB-14-04 | 单图 OCR 失败分支需 OCR 引擎，本机缺失 | 报告 §6 not-verified |

**合计**：**101** AC 中 **11** 项标注 NOT_TESTABLE（10.9%），其余 **90** 项可测；其中 **90** 项有用例覆盖（**100%**，R12 起，**0 项未覆盖**）——AC-IB-19-02 / AC-IB-20-04 已于 R12（R8 实现到位后）闭合（见 §16）
（其中 AC-IB-17-05 / AC-IB-17-06 为 `Tested（部分）`；AC-IB-19-03 / 20-02 为 `Tested`（残余见 §16.5）；**AC-IB-18-02 自 R8 起为 `Tested`（完整）**）。

### 5.1 R7 部分不可验证子句（**仍计入 79/79，不改变 NOT_TESTABLE 计数**；诚实标注）

| AC-ID | 已覆盖部分 | **不可验证**子句 | 理由 / 去向 |
|-------|-----------|----------------|------------|
| AC-IB-17-05 | 定义层「只出现键名不含凭据值」（TC-UNIT-060）、端点响应不含凭据值（TC-INT-084）、源码「只展示 `config_key_names`」（TC-INT-086） | 界面**渲染期**不回显、前端产物中不暴露凭据值 | 需前端运行期（浏览器挂载/交互），无自动化浏览器环境 → 报告 §6 NV-09 / §15.6 NV-R7-01 |
| AC-IB-17-06 | 「数据不出本机 + 依赖本地打包、运行期无 CDN」（TC-INT-086 源码级 + 定义层无网络调用） | 「可在**禁 Docker、全物理机直部署、组件裸装**形态下运行」 | 属部署形态，GROUP_E 本轮冻结（同 AC-IB-12-01/04 口径） |
| AC-IB-18-02 | 全部非法项均被拒并定位；无强制继续通道（TC-UNIT-057 / TC-UNIT-062~066 / TC-INT-082 / TC-INT-087 / TC-E2E-016） | **（R8 起无不可验证子句）** | 原第 7 类「路由关键词撞车」及第 8 类「`cn_label` 重复」已由 GROUP_C R8 补齐、经本轮回归 **CLOSED_VERIFIED**（报告 §13.8）→ 本行由 `Tested（部分）` 转 **`Tested`（完整）** |

---

## §6 门控与度量定义

| 度量 | 公式 | 门控 |
|------|------|------|
| 通过率 | `pass / (pass + fail) × 100%`（skip 与 blocked 不计入分母） | 单元 ≥ 80%；集成 ≥ 90% |
| 算术自洽 | `total = pass + fail + skip + blocked`（精确等式，无四舍五入） | 必须成立 |
| AC 覆盖率 | `已覆盖可测 AC / 可测 AC 总数` | 100% |
| 关键路径覆盖率 | `有 E2E 用例的 Must Have US / Must Have US 总数` | 100% |
| 计数方法 | pytest 原始输出（`docs/evidence/*.log`）逐条对应 TC-ID | 可追溯 |

---

## §7 已知环境偏差

| ID | 偏差 | 处置 |
|----|------|------|
| DEV-01 | 开发机 Python **3.14.6**，而 `docs/tech_stack.md` 约束为 `>=3.11,<3.14`（承 R1 偏差 D-03） | 登记；全部用例在 3.14.6 上真实跑通，但**不得**据此断言生产（3.11~3.13）行为等价 |
| DEV-02 | 本机 `langchain-openai` 1.3.3，违反 R1 冻结 pin `>=0.2,<0.3` | 远程 LLM 装配路径（`openai_compatible`）在本机被版本守卫拦下；`describe_egress` 于类级验证（TC-INT-064） |
| DEV-03 | `pypdf`/`pdfminer`/`pdfplumber`/`pypdfium2`/`rapidocr`/`FlagEmbedding`/`qdrant_client` 未安装（仅 `docx`、`onnxruntime` 可用） | 直接导致 §5 的 PDF/OCR/Qdrant not-verified 项 |
| **FLAKE-IB-01** | Windows 回环真 HTTP 偶发 `ConnectionAbortedError: [WinError 10053]`（`tests/integration/test_ib_embed_wire.py`，命中 **TC-INT-025** / **TC-INT-026** 的 `/warmup` 用例） | **MINOR（测试环境偶发，非产品缺陷）**。R8 实测：全量集成 14 次 / 4 次、单文件 8 次 / 1 次命中；每次命中后重跑即通过。登记保持 **OPEN**（**不**据「未复现」声称已修复）；缓解建议（测试侧连接级有界重试，**不放松断言**）见报告 §13.9，本轮**未实施**。<br>**R9 更新（INV-GROUP_D-INTELBASE-006）**：测试侧缓解建议**已实施**——`test_ib_embed_wire.py` 传输助手对 `ConnectionAbortedError`/`ConnectionResetError` 做**有限有界重试**（≤3 次尝试 + 0.05s 退避，**仅**连接级瞬态，**绝不**吞断言）；机制经探针确证（报告 §14.3），复跑单文件 10/10 绿、集成层 8/8 绿。状态 **OPEN → MITIGATED**（**不声称 CLOSED**，见报告 §14.5）。详细见 §13 |

---

## §8 与实施计划/模块设计的对照

- 模块覆盖：`implementation_plan.md` 声明 26 模块（MOD-IB-01~26）。本轮测试触达 MOD-IB-01~26 中除「纯部署 unit」（MOD-IB-25 systemd）外的全部；MOD-IB-26（`ib_embed`）以真实回环 HTTP 覆盖。**R7 增量**触达 MOD-IB-02（定义文档数据层）、MOD-IB-23（装配闸门 / 端点 / 组合根注入）、MOD-IB-24（可视化配置页，源码级）。
- 契约纪律：IC-IB-01（无裸 axios / 令牌不进 URL）→ TC-INT-031/038；C8（`ib_embed` 零耦合）→ TC-INT-050；`related_images`（IFC-IB-282）→ TC-UNIT-019 + TC-INT-044/046/047/048；**R7** IFC-IB-288~292（定义层）→ TC-UNIT-056~061 + TC-INT-079~081/083；IFC-IB-293（装配闸门）→ TC-INT-082；IFC-IB-294/295（端点）→ TC-INT-084；IFC-IB-296（视图侧纪律）→ TC-INT-086。
- 偏差登记：FND-GROUP-D-01（能力摘要恒空）、FND-GROUP-D-02（未绑库删除 500 + 幽灵文档）、D-R2-02（生产相关图恒空，登记行为）详见报告 §5；**R7 新发现 FND-R7-01（定义文档校验器未覆盖 ADR-16/REQ-FUNC-IB-27 ① 列举的两类校验项）详见报告 §12.6**。

---

## §9 R3 增量（缺陷回归与门控；追加，不改写 §1~§8）

> 触发：software-developer 完成 `INV-GROUP_C-INTELBASE-003`（R3 修复 FND-GROUP-D-02 / FND-GROUP-D-01）。
> 本轮为 **GROUP_D 增量**（`INV-GROUP_D-INTELBASE-002`）：翻转「缺陷固化用例」为正向守卫、补 R3 定向回归、
> 补一条**真并发**用例、重跑并执行串行通过率门控。**未修改任何 `src/**` 实现代码**。

### 9.1 三个「缺陷固化用例」→ 正向回归守卫（翻转）

| 原用例（固化缺陷） | 新用例（正向守卫） | 文件 | 断言要点 |
|---|---|---|---|
| `test_TC_INT_009_capability_digest_registry_gap_is_registered` | `test_TC_INT_009_capability_digest_reflects_builtin_tools` | `test_composition_retrieval.py` | `deps.capability_digest` 非空且含 `search_knowledge`；`IntentRouter._capability_digest()` ≠「（无可用工具）」且含 `search_knowledge` |
| `test_TC_INT_041_delete_before_bind_is_500` | `test_TC_INT_041_delete_before_bind_succeeds` | `test_http_contract.py` | DELETE → 200；`ledger_deleted=True`、`vectors_deleted=0`；列表消失；再删 404 |
| `test_TC_INT_061_ghost_document_after_failed_delete_is_registered` | `test_TC_INT_061_delete_before_processing_leaves_no_ghost` | `test_ops_contract.py` | 删不抛；`ledger_deleted=True`；台账行 `None`；worker 不认领（`processed=0`）；检索 `[]`；向量 0；对账干净 |

守卫串 `偏差已消除——请更新缺陷登记` / `DID NOT RAISE` **已随翻转移除**；若两缺陷复发，上述三用例将**响亮失败**。

### 9.2 新增回归用例（R3 行为定向）

| TC-ID | 文件 | 关联 AC | 覆盖的 R3 行为 |
|-------|------|---------|---------------|
| TC-INT-069 | `test_ops_contract.py` | AC-IB-03-02 | 已索引文档删除的 `DeleteReport` 三计数；删除路径**两次**向量清扫（首次清全部、竞态清扫为 0）；列表/台账/切块/向量/对账五不变式 |
| TC-INT-070 | `test_ops_contract.py` | AC-IB-03-03 | 删除后不可检索；再次 `process_pending` **不复活**（可见性权威 = 台账） |
| TC-INT-071 | `test_ops_contract.py` | AC-IB-02-04 | **真并发（2 线程）**：worker 处理中被删 → 计为 `skipped`（非 failed）、无未捕获异常、无残留向量 |
| TC-INT-073 | `test_composition_retrieval.py` | AC-IB-10-03 | 防漂移不变式：`bind_tools` 绑定工具名集合 == 摘要工具名集合，跨项目一致 |

**覆盖缺口说明（不凑数）**：三条 AC 在 §4 已有映射（AC-IB-03-02 ← TC-INT-033/014/E2E-003；AC-IB-03-03 ← TC-E2E-003/TC-INT-061；AC-IB-02-04 ← TC-INT-061）。新增用例填补的是**R3 修复行为**的缺口 —— 三计数与「第二次清扫为 0」、删除后重跑不复活、并发删除的 `skipped` 分类 —— 这些在修复前不存在可断言的正确行为，故非重复。
**AC 归属订正（诚实标注）**：任务书把「无可用工具/能力摘要路由提示可见性」记于 AC-IB-02-04；按 `user_stories.md` 原文，该可见性属 **AC-IB-10-03**，AC-IB-02-04 实为「处理中删除安全退出」。本轮**两条都已覆盖**（TC-INT-073 / TC-INT-071），避免因编号错配漏测。

### 9.3 真并发/竞态用例（对应 developer 登记的 R3-RISK-01）

TC-INT-071 用**真线程**（`threading.Thread`）跑 `process_pending`，并用**依赖替身（embedder）上的事件闸门**把交错窗口固定：

- worker 进入 `embed_documents` 即阻塞 → 主线程此刻执行 `delete_document`（此时 worker 确在「处理中」）→ 放行 worker；
- worker 走完剩余步骤撞上「台账行已不存在」→ 依 R3 的 `_DeletedConcurrently` / `NotFoundError` 分类分支计为 `skipped`，并 `_discard_written_vectors` 清掉本次写入的向量。

**诚实边界**：闸门落在**依赖替身**上（未改 SUT 逻辑），故交错可复现；本轮**未做**多进程/多 worker 压测，未构造「进程级崩溃落在两次清扫之间」的更窄时序 —— 该窗口仍由 `list_orphan_doc_ids` 对账 + 删除幂等兜底（developer 的确定性探针 `groupc_r3_probe.py` 用例 (c) 覆盖其因果链）。R3-RISK-01 的「真多进程压测」仍留待目标机阶段。

### 9.4 门控与覆盖复核

- 门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、算术自洽、可测 AC 100%、关键路径 100%）；执行结果见 `docs/test_report.md` §10。
- 用例总数 138 → **142**（集成 69 → 73）；`--collect-only` 计数与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r3_collect.log`）。
- §4 覆盖矩阵已同步更新 AC-IB-02-04 / AC-IB-03-02 / AC-IB-03-03 / AC-IB-10-03 四行。

### 9.5 本轮新发现缺陷（登记，不改实现）

| ID | 现象 | 级别 | 复现 | 处置 |
|----|------|------|------|------|
| FND-GROUP-D-03 | 生产 HTTP 删除路径（`resolve_scope` → 项目级 `Scope(kb_ids=None)`）下，原文件字节**未被删除**：`DeleteReport.blob_deleted` 恒为 `False`，BlobStore 中的原文件成为**孤儿**（磁盘/内存残留已删文档的原始内容） | MAJOR（保留/隐私 + 磁盘泄漏；非崩溃、不影响检索正确性） | `PYTHONUTF8=1 IB_OFFLINE_MODE=1 python docs/evidence/groupd_r3_blob_probe.py`（`docs/evidence/groupd_r3_blob_probe.log`） | 路由 software_developer：删除时按**文档所属 kb** 构造删除 scope（或 BlobStore 删除改为按 `project_id + doc_id` 匹配）。**测试侧未改实现** |
| FLAKE-IB-01 | `tests/integration/test_ib_embed_wire.py` 回环真 HTTP 用例**偶发** `ConnectionAbortedError: [WinError 10053]`（本会话 9 次集成层运行中出现 2 次，命中 `TC-INT-027` / `TC-INT-025` 各一次；单文件单独运行 3/3 通过；随后全量套件 5/5 连续通过） | MINOR（测试环境偶发，非产品缺陷；**与 R3 无关**） | 反复运行 `python -m pytest tests/integration -q` 观测 | 属 Windows 回环 socket 偶发；登记为环境偏差，不计入门控失败；如需根治可在测试侧对**连接级**错误做有限重试（不放松任何断言） |

---

## §10 R4 增量（FND-GROUP-D-03 回归与门控；追加，不改写 §1~§9）

> 触发：software-developer 完成 `INV-GROUP_C-INTELBASE-004`（R4 修复 FND-GROUP-D-03）。
> 本轮为 **GROUP_D R4 增量**（`INV-GROUP_D-INTELBASE-003`）：为已修缺陷补**真实、突变敏感**的回归用例，
> 重跑全量套件并执行串行通过率门控。**未修改任何 `src/**` 实现代码**（见 `docs/test_report.md` §11.9）。

### 10.1 被测修复（供用例溯源）

| 修复点 | 文件 | 语义 |
|--------|------|------|
| `kb_segment(kb_id)` | `src/ib/blob/__init__.py` | kb 存储段名的**唯一真源**：空串 / `None` → `"default"`；写（`FsBlobStore._doc_dir`/`InMemoryBlobStore`）、读（`blob_ref_for`）、删三处收敛为同一函数 |
| `_blob_scope_of(record)` | `src/ib/lifecycle/__init__.py` | `delete_document` 第 2 步改由**台账记录**派生删除 scope（携带真实 kb），不再沿用调用方传入的项目级 scope |

缺陷原状（`groupd_r3_blob_probe.py` 复现）：HTTP 删除经 `resolve_scope` 得项目级 `Scope(kb_ids=None)` →
`"default"` 段查找 → 删 0 个 → 原文件成孤儿且 `blob_deleted` 恒 `False`。

### 10.2 新增用例清单（TC ↔ AC）

| TC-ID | 文件 | 关联 US | 关联 AC | 覆盖的 R4 行为 |
|-------|------|--------|--------|---------------|
| TC-UNIT-055 | `tests/unit/test_blob_kb_segment.py` | US-IB-03 | AC-IB-03-02 | `kb_segment` 规则唯一（`None`/`""` → `"default"`）；写/读/删三路径落到同一 kb 段（单一真源不变式） |
| TC-INT-074 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | kb 级上传 + 项目级 scope 删除（错配路径）：`blob_deleted=True` 且**真实文件系统**上无残留字节/目录 |
| TC-INT-075 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 真实 Django HTTP `DELETE` + 真实 `FsBlobStore`：磁盘无任何残留文件 |
| TC-INT-076 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | `data=None`（D-08）本无 blob → `blob_deleted is False`（不得恒 True 掩盖） |
| TC-INT-077 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 跨项目不误删（同内容 + 同 doc_id 两种构造） |
| TC-INT-078 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配 + 项目级 scope 删除未处理文档仍 200、不回归 FND-GROUP-D-02、无 pending 幽灵 |

### 10.3 既有守卫的 R4 强化

| 用例 | 文件 | 强化点 |
|------|------|--------|
| TC-INT-041 | `test_http_contract.py` | 由「`blob_deleted` 为布尔（按实）」强化为「`blob_deleted is True` 且原文件引用失效」——同一守卫现同时覆盖 FND-GROUP-D-02 与 FND-GROUP-D-03 |
| TC-E2E-003（关键路径） | `test_user_journeys.py` | 旅程末尾新增「原文件字节已清理」断言（`blob_deleted is True` 且 `blobs.exists(ref) is False`） |

### 10.4 突变敏感性自证（新用例如何抓住回退）

在**仓库副本**（`.r4_mutant_check/`，测试后已删除；真实 `src/` 全程只读）上施加两处回退：

| 突变 | 施加方式 | 结果 | 证据 |
|------|---------|------|------|
| A：`_blob_scope_of` 回退为项目级（旧写法） | `return Scope(project_id=record.project_id)` | **6 failed / 2 passed**：TC-UNIT-055、TC-INT-074、TC-INT-075、TC-INT-077、TC-INT-041、TC-E2E-003 失败 | `docs/evidence/groupd_r4_mutation.log` |
| B：`kb_segment` 回退为恒等（丢失 default 规则） | `return kb_id` | **1 failed / 5 passed**：TC-UNIT-055 失败 | 同上 |

- 突变 A 下仍通过的 2 条 = TC-INT-076（本无 blob → 仍为 False，符合预期语义）与 TC-INT-078（FND-GROUP-D-02 守卫，与被突变点无关）。
- 突变 B 只命中 TC-UNIT-055：集成用例均用 kb 级上传（`kb_segment("kb_a") == "kb_a"` 不受影响），故 `kb_segment` 规则敏感度由单元级 TC-UNIT-055 承载；`_blob_scope_of` 敏感度由 TC-INT-074/075/077 承载。二者合起来覆盖任务书要求的「两处回退都会失败」。

### 10.5 门控与覆盖复核

- 门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、算术自洽、可测 AC 100%、关键路径 100%）；执行结果见 `docs/test_report.md` §11。
- 用例总数 142 → **148**（单元 55 → 56、集成 73 → 78、E2E 14 不变）；`--collect-only` 计数与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r4_collect.log`）。
- §4 覆盖矩阵 AC-IB-03-02 / AC-IB-03-03 两行已同步更新。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未使用 `-k`/`--deselect`/`--ignore`。

---

## §11 R7 增量（US-IB-17 / US-IB-18「UI 可视化配置」纳入测试范围；追加，不改写 §9~§10）

> 触发：REV-07-4（源自协调者裁决第 3 项）—— GROUP_B R7（1.3.0，ADR-14/15/16、IFC-IB-287~297）与
> GROUP_C R7（`implementation_plan.md` 2.3.0/R7，§15）已把 REQ-FUNC-IB-25/26/27 落地为代码，
> 现将其对应的 **US-IB-17 / US-IB-18**（均 Must Have）纳入 GROUP_D 测试范围。
> 本轮为 **GROUP_D R7 增量**（`INV-GROUP_D-INTELBASE-004`）：补覆盖矩阵、实现并执行新增用例、
> 重跑串行通过率门控。**未修改任何 `src/**` 实现代码**（见报告 §12.8）。

### 11.1 施工顺序前置（US-IB-17/18 的落地前提）

US-IB-17 / US-IB-18 的落地**前置**是「专家 / 路由 / 编排 / 工具授权已**外置为数据**且为**单一真源**」
（REQ-FUNC-IB-01 / REQ-FUNC-IB-02 的实现落差，见 `docs/agent_platform_research.md` §3.3 P0）。
该落差已由 **`DefinitionDocumentStore` 端口（IFC-IB-287，第 14 端口）+ `src/ib/config/definition.py`**
（IFC-IB-288~292）闭合：可视化只写回定义文档，不存在第二真源；否则可视化会沦为第二真源（风险 R-1）。

**测试口径**：本轮为「定义外置」这一前置直接建立断言 —— 单一真源/原子写回（TC-INT-079）、
往返无漂移（TC-INT-080）、乐观并发拒绝静默覆盖（TC-INT-081）、装配期装载→准入→派生→注入（TC-INT-085）。
即：只有前置成立，US-IB-17 的「无第二副本」与 US-IB-18 的「装配期拒绝」才可被断言。

### 11.2 新增用例清单（TC ↔ US ↔ AC）

共新增 **16** 条（单元 6 / 集成 8 / E2E 2）。全部为**正向断言**；0 skip / 0 xfail / 无 monkeypatch 掩盖。

| TC-ID | 文件 :: 用例名 | US | AC | 断言要点 |
|-------|---------------|----|----|---------|
| TC-UNIT-056 | `tests/unit/test_definition_data_layer_r7.py::test_TC_UNIT_056_validate_is_framework_free_and_pure` | US-IB-18 | AC-IB-18-05 | 干净解释器 import 定义层且 `sys.modules` 无 django/DRF/langchain/langgraph；`validate`/`derive`/`semantic_hash` 纯函数（同输入同输出） |
| TC-UNIT-057 | `::test_TC_UNIT_057_each_illegal_category_is_rejected_with_locator` | US-IB-18 | AC-IB-18-02、18-03 | 12 类非法样例逐类被拒且产出预期 code + 非空 `path/code/message`；边界取值 0.0/1.0 通过 |
| TC-UNIT-058 | `::test_TC_UNIT_058_roundtrip_is_semantically_equivalent` | US-IB-17 | AC-IB-17-02 | 文档→JSON→文档语义等价、逐项无增删改、往返幂等、哈希与 `updated_at` 无关 |
| TC-UNIT-059 | `::test_TC_UNIT_059_whitelist_excludes_topology_and_non_editable_changes_detects_it` | US-IB-17 | AC-IB-17-04 | 白名单含「专家集合 + 节点参数」、不含拓扑/归属；拓扑变更检出 `field_not_editable`；白名单内变更不报 |
| TC-UNIT-060 | `::test_TC_UNIT_060_errors_carry_locators_without_credential_values` | US-IB-18 | AC-IB-18-04、18-02 | `ValidationReport` 字段恰 `{ok,errors}`（无 force/ignore/warn_only）；错误项恰 `{path,code,message}`；校验结果与环境凭据值无关、错误体无凭据值 |
| TC-UNIT-061 | `::test_TC_UNIT_061_valid_passes_and_default_expert_invariant_is_not_bypassable` | US-IB-18 | AC-IB-18-01、18-03 | 合法即通过并派生视图；默认专家 0 个/≥2 个一律拒；`validate`/`admit` 签名无强制继续参数 |
| TC-INT-079 | `tests/integration/test_definition_config_r7.py::test_TC_INT_079_definition_store_is_single_persistent_source` | US-IB-17 | AC-IB-17-01 | 写回后目录**恰一份**文件（无临时残留/无第二副本）；文件内容 == `document_to_json`；重载逐字一致 |
| TC-INT-080 | `::test_TC_INT_080_store_roundtrip_has_no_semantic_drift` | US-IB-17 | AC-IB-17-02 | 写入→重载→原样回写，语义哈希不变、逐项无增删改 |
| TC-INT-081 | `::test_TC_INT_081_document_is_authoritative_and_conflicts_are_rejected` | US-IB-17 | AC-IB-17-03、17-01 | 界面外改动以文档为准；陈旧基线回写 → `conflict=True` 且**不落盘**（含 `content_hash_conflict` 可读回执）；当前基线回写成功 |
| TC-INT-082 | `::test_TC_INT_082_admit_gate_rejects_aggregating_all_items` | US-IB-18 | AC-IB-18-06、18-02 | `admit` 拒绝装配 + **聚合全部**校验项（`validation_items` 条数与 code 集合与 `validate` 一致）；合法定义通过且派生确定性 |
| TC-INT-083 | `::test_TC_INT_083_missing_or_corrupt_document_never_silently_falls_back` | US-IB-18 | AC-IB-18-06、17-01 | 文件缺失/损坏/非对象 JSON、内存未登记项目/`missing` 标志 → 一律 `ConfigError`（不静默回退空文档） |
| TC-INT-084 | `::test_TC_INT_084_definition_endpoint_contract_matrix` | US-IB-17/18 | AC-IB-17-01/04/05、18-01/04 | `GET|PUT /api/config/definition` 状态码矩阵 200/400/401/403/405/409；写回后 GET 以文档为准且 `deps.definitions` 同步；响应不含凭据值、只登记键名 |
| TC-INT-085 | `::test_TC_INT_085_assembly_loads_admits_derives_and_injects` | US-IB-18 | AC-IB-18-01 | 装配装载两项目文档（对象不共享）、派生注册表 == 文档专家集、图配置取自文档、编排图**编译一次常驻**（同项目同一对象） |
| TC-INT-086 | `::test_TC_INT_086_view_side_discipline_is_source_level_only` | US-IB-17 | AC-IB-17-04/05/06 | 源码级：本地打包无 CDN、视图侧零持久化、拓扑只读（无增删节点/边入口）、仅展示键名、无 `v-html`；**分发纪律（R10 修复）**：断言 `src/frontend/node_modules/**` **未被 git 跟踪**（`git ls-files`，环境自适应、与磁盘是否已装依赖无关）——守护「前端依赖不随仓库分发」不变量 |
| TC-E2E-015（关键路径） | `tests/e2e/test_user_journeys.py::test_TC_E2E_015_visual_config_roundtrip_is_single_source` | US-IB-17 | AC-IB-17-01/02/03/04 | 完整旅程：读 → 编辑保存 → 重载无漂移 → 改拓扑被拒 → 他处改动后以文档为准、陈旧回写 409 且不覆盖 |
| TC-E2E-016（关键路径） | `::test_TC_E2E_016_invalid_config_refused_at_assembly` | US-IB-18 | AC-IB-18-01/02/04/06 | 完整旅程：合法即装配且图常驻 → 非法提交 400 定位且不静默生效 → 装配闸门聚合拒绝 → 缺失文档显式报错 → 错误体无凭据值 |

**覆盖缺口判定（不凑数）**：12 组 AC 此前在 §4 中**无任何映射**（US-IB-17/18 属 REV-06 新增诉求），
故新增 16 条均为**首次覆盖**而非重复。TC-UNIT-058 与 TC-INT-080 分属「纯函数往返」与「经存储往返」
两个不同语义面（后者含原子写回与乐观并发基线），非重复。

### 11.3 覆盖与计数复核

- 用例总数：**149 → 165**（单元 56 → 62、集成 79 → 87、E2E 14 → 16）。
  `--collect-only` 与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r7_collect.log`）。
- 全部 US：**18 / 18** 均有用户故事级（E2E）覆盖（新增 US-IB-17 → TC-E2E-015、US-IB-18 → TC-E2E-016）。
- 关键路径：**14 / 14** Must Have US = 100%（US-IB-17/18 均 Must Have）。
- 可测 AC：**79 / 79** = 100%（11 项 NOT_TESTABLE 见 §5；3 项 `Tested（部分）` 见 §5.1）。
- §4 覆盖矩阵已同步新增 AC-IB-17-01~06 / AC-IB-18-01~06 共 12 行。

### 11.4 门控与度量

门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、E2E 关键路径 100%、算术自洽、可测 AC 100%）；
执行结果（命令 + EXIT + 原始计数）见 `docs/test_report.md` **§12**。

---

## §12 R8 增量（FND-R7-01 修复回归：装配期唯一性校验；追加，不改写 §9~§11）

> 触发：REV-08-2（协调者裁决 A）—— GROUP_C R8（software-developer `INV-GROUP_C-INTELBASE-007`）在
> `src/ib/config/definition.py::validate()` **纯追加**两项装配期校验（跨专家关键词撞车 `expert_keyword_collision` /
> `cn_label` 唯一性 `expert_cn_label_duplicate`），即 **FND-R7-01（报告 §12.6，MAJOR）** 的修复。
> 本轮为 **GROUP_D R8 增量**（`INV-GROUP_D-INTELBASE-005`）：修复陈旧夹具、补测新校验、重跑串行门控、补全 FLAKE-IB-01 登记。
> **未修改任何 `src/**` 实现代码**（见报告 §13.11）。

### 12.1 被测修复（供用例溯源）

| 项 | 契约/来源 | 语义 |
|----|----------|------|
| 校验项 10 | ADR-16 / AC-IB-18-02 / REQ-FUNC-IB-27 ① | 跨专家**路由关键词撞车**：归一化 `strip().lower()`（对齐 `ib/routing/intent.py::_keyword_hits`），不同专家归一后同词 → `expert_keyword_collision`，`path=experts[<专家>].keywords[<原样词>]` |
| 校验项 11 | ADR-16 / AC-IB-18-02 | `cn_label` **唯一性**：去首尾空白后比较（界面不可见空白视为重复，大小写可见不归一）；重复 → `expert_cn_label_duplicate`，`path=experts[<专家>].cn_label`；空标签由既有第 5 项 `expert_text_missing` 承担 |
| 纯追加纪律 | 实现注释 L362~411 | 既有 1~9 类校验语义与顺序**一字未改**，新增项仅末尾追加 |

### 12.2 陈旧夹具修复（D-R8-01，仅改夹具数据、断言语义不变）

`tests/unit/test_definition_data_layer_r7.py` 与 `tests/integration/test_definition_config_r7.py` 的 `_expert` 夹具
原让两位专家**共用** `cn_label="标签"` / `keywords=("k",)`（修复前「仅因缺陷而合法」）；新增校验后该基线被判非法 →
**TC-UNIT-056/057/061、TC-INT-082** 四个**正向**「基线合法」用例转为失败。**判定：夹具陈旧，非真实回归。**
修法：`_expert` 默认值改为**随 name 派生**（`cn_label=f"标签{name}"`、`keywords=(f"k{name}",)`）；**未删除/削弱任何断言**。
（若修复时发现某失败实为真实回归，须立即 BLOCKED —— 本轮经逐条核验**无**此类情形。）

### 12.3 新增/补测用例清单（TC ↔ US ↔ AC）

| TC-ID | 文件 | US | AC | 断言要点 |
|-------|------|----|----|---------|
| TC-UNIT-062（R8 登记） | `tests/unit/test_definition_uniqueness_r8.py` | US-IB-18 | AC-IB-18-02 | 关键词撞车：通过 + 精确/大小写/空白重复 → 拒绝并定位；同专家内重复不报 |
| TC-UNIT-063（R8 登记） | 同上 | US-IB-18 | AC-IB-18-02 | `cn_label` 唯一：通过 + 精确/空白重复 → 拒绝（`path=experts[b].cn_label`）；空跳过；大小写不归一 |
| TC-UNIT-064（R8 登记） | 同上 | US-IB-18 | AC-IB-18-02 | 默认注册表无撞车/无重标签；默认派生文档 `validate.ok is True`（反向护栏） |
| TC-UNIT-065（R8 新增） | `tests/unit/test_definition_uniqueness_extra_r8.py` | US-IB-18 | AC-IB-18-02 | 空/纯空白关键词不误报；三名专家同词 → 2 条且 path 归属；大小写+空白叠加；精确 path |
| TC-UNIT-066（R8 新增） | 同上 | US-IB-18 | AC-IB-18-02 | 三名专家同标签 → 2 条且 path 归属；全空白跳过；两项校验独立（两错误码并存） |
| TC-INT-087（R8 新增） | `tests/integration/test_definition_config_r7.py` | US-IB-18 | AC-IB-18-02/18-06 | 跨模块接缝：`admit` 聚合拒绝（含两新码）；`PUT /api/config/definition` → 400 逐条回执两新码；非法配置不静默生效 |

**覆盖缺口判定（不凑数）**：TC-UNIT-062~064 已覆盖主路径（此前未入册，本轮**首次登记**）；本轮只补其空缺
（空关键词跳过 / 三名专家条数与归属 / 两项校验独立性）与**跨模块接缝**（`admit` + 端点），非重复。

### 12.4 覆盖与计数复核

- 用例总数：**165 → 171**（单元 62 → **67**、集成 87 → **88**、E2E 16 不变）；净增 6 = developer 交付 3 + 本代理新增 3。
  `--collect-only` 与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r8_collect.log`，171 tests collected）。
- 覆盖矩阵：**AC-IB-18-02 由 `Tested（部分）` 转 `Tested`（完整）**；`AC-IB-18-06` 增加跨模块接缝证据。
  可测 AC **79/79**（不变）；全部 US **18/18**、关键路径 **14/14** Must Have US（不变）。
- **FND-R7-01 → CLOSED_VERIFIED**（判据逐条对照见报告 §13.8）。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未用 `-k`/`--deselect`/`--ignore`。

### 12.5 FLAKE-IB-01 登记补全（REV-08-2 第 4 项）

| 栏位 | 内容 |
|------|------|
| 触发条件 | Windows 11 + Python 3.14.6；`ib_embed.server` 以 `ThreadingHTTPServer`（HTTP/1.1 长连接）绑 `127.0.0.1:0` 起真实回环 HTTP；`/warmup` 用例每次新建并 shutdown server；**不可确定性复现** |
| 涉及用例 | `test_ib_embed_wire.py` 的 **TC-INT-025**（warmup 幂等）/ **TC-INT-026**（warmup 失败快速失败 500）——连接级抖动，非断言失败 |
| 稳定性证据 | R8 实测：全量集成 **14 次 / 4 次**命中（≈28.6%）；单文件 **8 次 / 1 次**命中（12.5%）；命中后**立即重跑即通过**。历史：R3 9/2、R4 5/0、R7 全量 0 命中。现场回溯留档 `docs/evidence/groupd_r8_flake_ib01_TC_INT_026.log` |
| 缓解建议（**本轮未实施**） | 在测试请求助手对**连接级异常**（`ConnectionAbortedError`/`ConnectionResetError`，WinError 10053/10054）做**有限有界重试**（≤3 次 + 短退避），**仅**重试连接/读取阶段，**绝不**吞掉断言失败或改写状态码断言；可选：`Connection: close` 或 POST 前 `/healthz` 就绪握手 |
| 处置边界 | **未**改动该测试文件（保留现场证据供 PM 裁决）；**未**改动任何 `src/**` |

### 12.6 门控与度量

门控定义沿用 §6；执行结果（命令 + EXIT + 原始计数；单元 67/67、集成 88/88、E2E 16/16、全量 171/171、
selfcheck 31/31）见 `docs/test_report.md` **§13**。

---

## §13 R9 增量（FLAKE-IB-01 测试侧稳定性治理：连接级有界重试；追加，不改写 §9~§12）

> 触发：**REV-09-1/2（协调者裁决 A）**——处置 **FLAKE-IB-01**（§7 登记，MINOR，测试环境偶发）：
> Windows 回环真 HTTP 偶发 `ConnectionAbortedError[WinError 10053]` / `ConnectionResetError[WinError 10054]`，
> 命中 `tests/integration/test_ib_embed_wire.py` 的 **TC-INT-025 / TC-INT-026**（`/warmup` 用例）。
> 本轮为 **GROUP_D R9 增量**（`INV-GROUP_D-INTELBASE-006`）：在**测试请求助手**内做**有限有界重试**，
> 重跑全量并复跑抖动靶点。**未修改任何 `src/**` 实现代码**（见报告 §14.7）。

### 13.1 治理措施（测试侧；断言语义零变更）

**唯一改动文件**：`tests/integration/test_ib_embed_wire.py`（`+48 / -10`）；改动**仅**在 `_Server.get` / `_Server.post`
共用的**传输助手**（引出 `_request_bounded`）；文件内 **12 条用例的 Setup/Action/Assertion 一字未动**。

| 项 | 设定 | 说明 |
|----|------|------|
| 重试对象 | `(ConnectionAbortedError, ConnectionResetError)` | **仅**这两类连接级瞬态异常（WinError 10053/10054） |
| 尝试上限 | `_MAX_ATTEMPTS = 3`（≤3 次尝试 = ≤2 次重试） | **有限有界**，绝不无限重试 |
| 退避 | `_RETRY_BACKOFF_S = 0.05`（秒） | 短退避 |
| 用尽后 | 裸 `raise` 原样抛出最后一次异常 | 失败**可观测**，绝不静默通过 |
| 明确排除 | `HTTPError`（4xx/5xx）**不重试**，状态码原样返回；`AssertionError` / 其他异常**不捕获** | **不**改写状态码/语义断言；**不**吞断言 |

**硬边界守约（对照 REV-09-1/2，逐条）**：

| 边界 | 实现 | 证据 |
|------|------|------|
| 仅重试连接建立/读取阶段的连接级瞬态 | 单一 `except _CONNECTION_LEVEL_ERRORS` 分支 | 探针 A（`attempts=3` 吸收） |
| 绝不吞断言失败 | 无 `except Exception` / 裸 `except`；`AssertionError` 非 `ConnectionError` 子类 | 探针 D（`attempts=1`，AssertionError 冒泡） |
| 不重写状态码/语义断言 | `except HTTPError` 原样返回 `exc.code` | 探针 E（500 原样） |
| 不得 skip/xfail/assert True 掩盖 | 全文件 0 skip / 0 xfail | 全量日志；`--collect-only` 171 |
| 计数用尽后原样抛出 | 裸 `raise` | 探针 C（`attempts=3`，`ConnectionResetError` 抛出） |

> 守约探针：`docs/evidence/groupd_r9_retry_probe.py` → `groupd_r9_retry_probe.log`（猴补 `urlopen` 直接驱动重试助手）。

### 13.2 FLAKE-IB-01 状态同步

| 栏位 | R8 | **R9（本轮）** |
|------|----|--------------|
| 状态 | OPEN | **MITIGATED**（测试侧治理已实施且机制经探针确证；**不声称 CLOSED**） |
| 治理 | 仅登记 + 缓解建议（未实施） | 传输助手**有界重试**已落地（≤3 次尝试 + 0.05s 退避） |
| 稳定性证据 | 全量集成 14/4 命中、单文件 8/1 命中 | 修复后：单文件 **10/10 绿**、集成层 **8/8 绿** |
| 诚实边界 | 不据「未复现」声称已修复 | 「零复发」无法用有限样本**确证**（8 次集成层全绿在 28.6% 基线下偶然概率 ≈6.8%）；若抖动持续超 3 次窗口，用例仍**响亮失败**（设计使然）→ 届时应升级为环境/产品根因排查 |

### 13.3 覆盖与计数复核

- 用例总数**不变**：**171**（unit 67 / integration 88 / e2e 16）——本轮为**治理 + 复跑**，不扩充/不收缩测试面。
- 可测 AC **79/79**、全部 US **18/18**、关键路径 **14/14** Must Have US（**均不变**）。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未用 `-k`/`--deselect`/`--ignore`。

### 13.4 门控与度量

门控定义沿用 §6；执行结果（命令 + EXIT + 原始计数；单元 67/67、集成 88/88、E2E 16/16、全量 171/171、
selfcheck 31/31；含抖动靶点复跑）见 `docs/test_report.md` **§14**。

---

## §14 R10 增量（前端冒烟测试层正式化；追加，不改写 §9~§13）

> 触发：**REV-10-2**（协调者裁决「前端构建阻断修复轮」第 2 项）——GROUP_C R10（REV-10-1，software-developer
> `INV-GROUP_C-INTELBASE-008`）已消除前端构建阻断：`package-lock.json` 同步纳入 `@vue-flow/core`（锁定 1.48.2 / MIT）
> 及 14 个传递依赖、`ConfigPage.vue` 纳入版本控制、去除未用导入；并搭建前端冒烟测试入口
> `src/frontend/tests/frontend.smoke.test.js`（6 例，Node 20 内置 `node:test`，**零新增依赖**）。
> 本轮为 **GROUP_D R10 增量**（`INV-GROUP_D-INTELBASE-007`）：把该**前端冒烟层正式纳入测试计划**、建立溯源、复跑证据。
> **未修改任何 `src/**` 实现代码 / 未修改任何测试代码**（见报告 §15.8）。

### 14.1 前端冒烟测试层（新层，6 例；**独立计数，不并入 Python 171**）

前端冒烟测试文件 `src/frontend/tests/frontend.smoke.test.js`（`@module MOD-IB-24` / `@implements IFC-IB-296`）
由 software-developer 产出；**本层由 `test-engineer` 正式收录、逐条溯源并列入测试计划**（**未改写其任何断言**）。

| TC-ID | 用例（`it`）| 断言面 | US | AC 溯源 | NFR 溯源 | 判定 |
|-------|------------|--------|----|---------|---------|------|
| TC-FE-001 | package.json 声明 `@vue-flow/core`（+ `vue`）依赖 | 依赖声明（工程结构） | US-IB-17 | AC-IB-17-06（「本地打包」**前置**：依赖须为工程声明） | REQ-NFR-IB-12（依赖/许可台账以声明与锁为真源） | PASS |
| TC-FE-002 | `package-lock.json` 与 `package.json` 同步（根 deps 一致 + 传递闭包锁定） | 锁↔声明同步 | —（**工程不变量**；R10 根因守卫） | AC-IB-17-06（可 `npm ci` 复现的**本地打包**能力） | REQ-NFR-IB-08（离线/不外发前提） | PASS |
| TC-FE-003 | ConfigPage.vue 从本地包导入 Vue Flow 与样式（非 CDN） | 源码 import 本地包 + 基础/主题样式 | US-IB-17 | AC-IB-17-06 | REQ-FUNC-IB-25 | PASS |
| TC-FE-004 | 编排图只读不变量（`nodes-draggable=false` / `connectable=false`、无增删**图节点**入口） | 拓扑只读 | US-IB-17 | AC-IB-17-04（界面不提供运行期增删图节点 / 改变拓扑） | REQ-FUNC-IB-26 | PASS |
| TC-FE-005 | 源码与入口零外发 CDN 引用（5 类公网 CDN 主机名零命中） | 源码级不外发 | US-IB-17 | AC-IB-17-06 | REQ-NFR-IB-08 | PASS |
| TC-FE-006 | 构建产物存在且 `dist/index.html` 无绝对外链（**条件式**：`dist/` 存在方断言其内容） | 构建产物级不外发 | US-IB-17 | AC-IB-17-06（「本地打包」的**产物级**证据） | REQ-NFR-IB-08 | PASS |

**溯源说明（据实，不硬凑 AC）**：
- 与「配置页 / 依赖锁 / 本地打包」相关的断言落在 **AC-IB-17-04**（拓扑只读）与 **AC-IB-17-06**（本地打包、不外发）。
- **AC-IB-17-01/02/03**（单一真源 / 往返等价 / 以文档为准）与 **AC-IB-18-02**（装配期拒绝非法配置）**不由本层覆盖**
  —— 它们由 Python 层（TC-UNIT-057/058/062~066、TC-INT-079~087、TC-E2E-015/016）承担；本层**不重复、不替证**。
- **AC-IB-17-05**（凭据只出现键名、前端**渲染期**不回显）**本层不覆盖**（本层无任何凭据渲染断言），其判定**维持不变**（见 §14.3）。
- `REQ-NFR-IB-12`（许可）仅作**间接**溯源：TC-FE-002 的锁同步守卫使 `tech_stack.md` §2.1 登记的许可证集合与锁内实际集合一致
  （台账以锁为真源）；**许可类型本身为文档性结论**（同 AC-IB-07-04 / §5 口径，NOT_TESTABLE）。

### 14.2 运行方式与 CI 接入点

| 项 | 值 |
|----|----|
| 运行命令 | `cd src/frontend && npm test`（= `node --test`，Node 20 内置 `node:test`；**零新增依赖**） |
| 前置条件 | 用例 TC-FE-006 依赖 `dist/`（`npm run build` 产物）**存在**；不存在时以 `t.diagnostic(...)` 标注并**跳过产物断言**（属**前置条件判断**，非削弱断言）；CI 中因**先 build 后 test**，产物必然存在 |
| CI 接入 | `.github/workflows/ci.yml` **阶段9**：`working-directory: src/frontend` → `npm ci && npm run build && npm test`；与 `docs/cicd_pipeline.md` **1.1.1 / R10** 阶段9 定义逐字同步 |
| 守护的回归 | **锁同步**（`package-lock.json` ↔ `package.json`）—— 正是 R10 中 `npm ci` 因锁失同步 `EUSAGE` 失败的**根因守卫**；接入阶段9 后该守卫获**强制力**（此前仅开发机可跑） |

### 14.3 覆盖矩阵更新（仅列因本轮而**变**者）

| AC | 变更前（§4 / §5.1） | **变更后（R10）** | 依据 |
|----|--------------------|------------------|------|
| AC-IB-17-06 | `Tested（部分）`：源码级「本地打包 + 无 CDN」已覆盖；「**禁 Docker / 全物理机裸装**」属部署，冻结 | 维持 `Tested（部分）`，但「本地打包 + 无 CDN」子句的**验证面上移**：由「源码级」（TC-INT-086）扩为「**源码级 + 构建产物级**」（新增 TC-FE-001/003/005/006）；**仍未闭合**的仅剩「禁 Docker 裸装运行形态」（属 GROUP_E 部署，冻结） | 新增 TC-FE 层证据；`dist/index.html` 仅含相对 `/assets/*` 引用（实测） |
| AC-IB-17-05 | `Tested（部分）`：定义层/端点/源码级已覆盖；**前端渲染期不回显凭据**不可验 | **维持 `Tested（部分）`，判定不变**（TC-FE 层**无**凭据渲染断言，**不得**因新增前端层而升级） | 诚实边界：本层未断言凭据渲染 |
| AC-IB-17-04 | `Tested` | 维持 `Tested`（TC-FE-004 提供**前端源码级**只读拓扑佐证，属**补强**而非新覆盖判定） | — |
| AC-IB-18-02 | `Tested`（完整，R8 起） | **维持 `Tested`（完整）**；本层不涉及 | — |

> **诚实边界（构建 ≠ 渲染）**：R10 使 `npm ci` / `npm run build` **可执行并通过**（developer + 独立 verifier 亲跑，见报告 §15），
> 故「前端**构建可行性**」**不再**是 not-verified；但**浏览器内的实际渲染 / 交互**（Vue Flow 挂载画布）仍**无自动化执行环境**，
> 该子句**仍不可验**（报告 §6 NV-07 / §12.7 NV-R7-01 口径相应**收窄**，见报告 §15.6）。

### 14.4 计数口径（前端层与 Python 层**分列**）

- **Python 层（既有三层，算术不变）**：unit **67** + integration **88** + e2e **16** = **171**（本轮**不增删 / 不改名**）。
- **前端层（新层，独立计数）**：TC-FE-001 ~ TC-FE-006 = **6**。
- **口径纪律**：前端 6 例**不并入** Python 的 171 算术（跨运行时 / 跨测试框架，混算即口径污染）；两层各自独立给出门控结论。

### 14.5 门控与度量

- **前端层门控**：**6/6 = 100% PASSED**（本层阈值为「全通过」，与 E2E 关键路径同口径）。
- **Python 三层门控**：沿用 §6；执行结果（命令 + EXIT + 原始计数）见 `docs/test_report.md` **§15**。
- **本轮新发现 → 已修复（R10 修复，REV-10-2 续）**：Python 用例 **TC-INT-086** 原含「显式断言 `@vue-flow/core` **未安装**（磁盘不存在）」的
  边界固化语句（R7 期产物），与 R10 必需的 `npm ci` 冲突 —— **任何已装 `node_modules` 的树内该断言必失败**（曾复现 170 passed / 1 failed）。
  **修复机制**：将该「磁盘存在性」近似判定改为对**原始不变量**——「**前端依赖不随仓库分发**」——的正确、环境自适应判定：
  经 `subprocess` 调 `git ls-files -- src/frontend/node_modules`（**直接**查询入库状态，只读 git 索引、从不 stat 工作树），
  断言结果为空；**未装 / 已装但被 gitignore 均通过，被 `git add -f` 强加入库则失败**（不弱化、不 skip/xfail）。
  该用例为 **GROUP_D / PHASE_09 自有产物**（非 software-developer）。机制、两种磁盘态演示与**负向对照**证据见 `docs/test_report.md` §15.5 与 `docs/evidence/groupd_r10_tcint086_guard.log`。
  **复跑**：已装 `node_modules` 工作树 `python -m pytest tests -q` = **171 passed（EXIT=0）**；`tests/integration` = **88 passed**。

---

## §15 R11 增量（REQ-FUNC-IB-20 测试补全：US-IB-19 / US-IB-20 纳入测试范围；追加，不改写 §9~§14）

> **本轮定位**：`REQ-FUNC-IB-20`（流式输出契约与会话生命周期）在 REV-11-1 补出 **US-IB-19**（流式交付最终答复，AC-IB-19-01~05）与 **US-IB-20**（会话生命周期，AC-IB-20-01~06），共 **11 组 G/W/T**；REV-11-2 在架构 1.4.0/R8 落 **ADR-17 + IFC-IB-298~308**（设计层）。本轮（REV-11-3）为 GROUP_D 测试补全：**重挂 5 条既有用例** + **新增 13 条用例**，把新 AC 纳入测试范围。
>
> **边界纪律（重要）**：本轮**仅动 `tests/`、`docs/test_plan.md`、`docs/test_report.md`**，**不改 `src/` 任何既有实现行为**。架构 1.4.0/R8 的 **IFC-IB-298~308 为设计层产物、本轮 `src/` 尚未实现**（经全仓 grep + `phase_status.md` + `implementation_plan.md` 交叉核实）——故对本轮**未实现**的接口**不伪造断言、不写红测**，一律在 §15.5 如实登记为**覆盖缺口**，交 PM 路由 developer。

### 15.1 用例变更清单（重挂 5 + 新增 13；**既有 171 条编号一律不变**）

| 类别 | 用例 ID | 变更 | 依据 |
|------|---------|------|------|
| 重挂 | TC-UNIT-016 | US-IB-08 → **US-IB-19**；AC-IB-08-01 → **AC-IB-19-01** | SSE 帧渲染 / done 收尾 = 流式交付契约（user_stories.md §US-IB-19 下游挂接） |
| 重挂 | TC-UNIT-017 | US-IB-08 → **US-IB-19**；AC-IB-08-01 → **AC-IB-19-01** | `StreamEvent` 别名恒等 = 流式交付契约「只有一个事件类型定义」 |
| 重挂 | TC-INT-039 | US-IB-08 → **US-IB-19**；AC-IB-08-01 → **AC-IB-19-01** | SSE 端点（缺 q → 400 / 正常 → `text/event-stream`）= 流式交付契约入出口 |
| 重挂 | TC-UNIT-018 | US-IB-11 → **US-IB-20**；AC-IB-11-02 → **AC-IB-20-01** | 会话存储按项目隔离 = 会话隔离（user_stories.md §US-IB-20 下游挂接） |
| 重挂 | TC-UNIT-022 | US-IB-11 → **US-IB-20**；AC-IB-11-02 → **AC-IB-20-06** | 会话键前缀断言 / 非法前缀被拒 = 跨项目 / 伪造会话拒绝 |
| 新增 | TC-UNIT-067~069 | 新增 3 条（单元） | 见 §15.3 |
| 新增 | TC-INT-088~095 | 新增 8 条（集成） | 见 §15.3 |
| 新增 | TC-E2E-017~018 | 新增 2 条（E2E / 关键路径） | 见 §15.3 |

### 15.2 重挂判定（逐条：真实测试意图 → 归属 AC）

| 用例 | 真实测试意图 | 归属判定 | 理由 |
|------|-------------|---------|------|
| TC-UNIT-016 | `to_sse` 帧格式（event/data 逐行 + 结尾空行）、done 帧收尾 | **AC-IB-19-01** | 该 AC 明写「以明确的终止事件结束」，帧合法性与 done 收尾是其编码层落点 |
| TC-UNIT-017 | `ib.streaming.StreamEvent is ib.core.StreamEvent` | **AC-IB-19-01** | 流式交付契约「只有一个事件类型定义」，防跨模块 `isinstance` 恒假 |
| TC-INT-039 | SSE 端点：缺 `q` → 400；正常 → `text/event-stream` + 合法事件序 | **AC-IB-19-01** | 端点入出口与事件序是「增量推送 + 终止事件」的契约边界 |
| TC-UNIT-018 | `MemorySessionStore` 按项目前缀隔离读写 | **AC-IB-20-01** | 该 AC 明写「会话 A/B 隔离、不跨会话注入」 |
| TC-UNIT-022 | `session_key` 构造 + `assert_session_key` 前缀断言（非法/跨项目被拒） | **AC-IB-20-06** | 该 AC 明写「跨项目 / 伪造会话标识被拒且可识别」 |

> **未强制重挂者（如实声明）**：user_stories.md §US-IB-20 下游挂接建议「评估 **TC-INT-042**（事件序 reasoning→content→done、content 仅一条）是否改挂 US-IB-19」——该条**保持原归属 US-IB-09 / AC-IB-09-03 不变**（其核心断言是「聚合暴露内部分工」的守卫，属 US-IB-09 的验收面），R11 新增的 TC-INT-088/090 已从 US-IB-19 侧覆盖同一行为，**不为凑指标强制重挂**。

### 15.3 新增用例清单（TC ↔ US ↔ AC）

| TC-ID | 层 | 文件 | 关联 US | 关联 AC | 断言要点 |
|-------|----|------|--------|--------|---------|
| TC-UNIT-067 | 单元 | `tests/unit/test_stream_session_lifecycle_unit_r11.py` | US-IB-19 | AC-IB-19-04 | `_strip_internal_labels` 删净内部分工词（路由到/巡检诊断/专家/聚合）、事实内容保留；开关关闭时原样返回 |
| TC-UNIT-068 | 单元 | 同上 | US-IB-19 | AC-IB-19-03 | reasoning/content 两 kind 互异；一帧只承载一个事件；思考文本不并入正文 |
| TC-UNIT-069 | 单元 | 同上 | US-IB-20 | AC-IB-20-05 | 模拟重启的**新** `MemorySessionStore` 读回 `None`（不静默复活）；delete 幂等 |
| TC-INT-088 | 集成 | `tests/integration/test_stream_session_lifecycle_int_r11.py` | US-IB-19 | AC-IB-19-01 | `done` 恰一次且收尾；其后无 content；分片拼接 == 最终答复；无空内容片段 |
| TC-INT-089 | 集成 | 同上 | US-IB-19 | AC-IB-19-04 | 强制双专家：面向用户仅一条 content；专家原始作答与内部标签（数据管家/巡检诊断）不出现在任何事件 |
| TC-INT-090 | 集成 | 同上 | US-IB-19 | AC-IB-19-03 | 真实流中 reasoning 先于 content、两 kind 可辨、思考不并入正文、每帧单事件 |
| TC-INT-091 | 集成 | 同上 | US-IB-19 | AC-IB-19-05 | 全链路降级仍非空回退；不推空内容片段；`done` 恰一次；不臆造引用 |
| TC-INT-092 | 集成 | 同上 | US-IB-20 | AC-IB-20-01 | 会话 B 历史不含 A 的标记；A 状态独立不被覆写；未识别会话读回 `None` |
| TC-INT-093 | 集成 | 同上 | US-IB-20 | AC-IB-20-02/20-05 | 门关 / 状态丢失两情形均 `error`+`done` 安全失败，**无** content |
| TC-INT-094 | 集成 | 同上 | US-IB-20 | AC-IB-20-03 | 默认 `confirmation_gate_enabled=False`；关闭时不出现确认等待、正常完成 |
| TC-INT-095 | 集成 | 同上 | US-IB-20 | AC-IB-20-06 | 无前缀/非法键读写被拒；跨项目归属断言抛 `ScopeViolationError` |
| TC-E2E-017 | E2E | `tests/e2e/test_user_journeys.py` | US-IB-19 | AC-IB-19-01/19-05 | 真实 HTTP SSE：200 + `text/event-stream`；`done` 恰一次且收尾；内容帧非空 |
| TC-E2E-018 | E2E | 同上 | US-IB-20 | AC-IB-20-01 | 两个显式 `session_id` 各跑一轮：各自独立成流、各恰一次终态收尾、互不阻断 |

### 15.4 覆盖与计数复核

- **计数**：unit **67 → 70**、integration **88 → 96**、e2e **16 → 18**；合计 **171 → 184**（前端冒烟 6 例仍**独立计数、不并入**）。
- **US 覆盖**：20/20 US 均有 ≥1 条用例；新 US-IB-19 由 8 条、US-IB-20 由 6 条用例承接。
- **Must Have 关键路径 E2E 覆盖**：**16/16 = 100%**（含 R11 新增的 US-IB-19 / US-IB-20，各由 TC-E2E-017/018 承接）。
- **可测 AC 覆盖**：**88/90 = 97.8%**（2 项缺口见 §15.5）。
- **算术**：184 = 70 + 96 + 18。

### 15.5 覆盖缺口登记（IFC-IB-298~308 本轮未实现；**只登记不擅修**）

架构 1.4.0/R8 定义的 11 条类型化接口（IFC-IB-298~308）在 `src/` **尚未落地**（全仓 grep 无 `CompletionPayload` / `completion_event` / `is_user_visible` / `SessionPersistencePolicy` / `SessionStateLossOutcome` / `ConfirmationGateState` / `can_resume` / `ResumePayload` / `confirmation_required` / `POST /api/chat/resume` / `IB_CONFIRMATION_GATE_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_REASONING_STREAM_ENABLED`）。

| AC | 缺口内容 | 依赖接口 | 本轮处置 |
|----|---------|---------|---------|
| AC-IB-19-02 | 完成事件（`done`）附结构化产物（≥ 引用列表），一次性、不臆造 | `CompletionPayload` / `CitationItem` / `completion_event`（IFC-IB-300/302） | **未覆盖**（无断言；不写红测） |
| AC-IB-19-03 | 「默认不出现思考片段；启用后可辨」（`IB_REASONING_STREAM_ENABLED`） | IFC-IB-302 | **部分覆盖**（kind 可辨/不混帧/不并入正文已测；开关未实现） |
| AC-IB-20-02 | 持久化策略须在**配置 + 部署文档**显式声明 | `SessionPersistencePolicy`（IFC-IB-304/305） | **部分覆盖**（状态丢失 fail-closed 已测；策略声明未实现） |
| AC-IB-20-03 | 「机制保留、默认不启用」的**启用后行为** | IFC-IB-301 | **部分覆盖**（默认关闭 + 关闭不等待已测） |
| AC-IB-20-04 | 确认中间态**呈递**与**决策回传** | `confirmation_required` 事件 + `POST /api/chat/resume`（IFC-IB-301/307/308） | **未覆盖**（无断言；不写红测） |
| AC-IB-20-05 | 「携带决策自中间态**续跑**」 | `ResumePayload` / `can_resume`（IFC-IB-306/308） | **部分覆盖**（未携带/状态丢失 fail-closed 已测；携带决策续跑未实现） |

**另登记一项既有实现缺陷（FND-R11-01，MAJOR）**：
- **现象**：`src/ibweb/views.py` 的 `chat_stream_endpoint` 对缺失 `session_id` 以字面量 `"default"` 静默兜底（`request.GET.get("session_id") or "default"`）——即所有未携带 `session_id` 的调用方**共享同一个默认会话**，历史随之互相注入。
- **AC 依据**：**AC-IB-20-01** 明写「会话标识被正确识别（沿用其既有历史）**或显式拒绝**（**不静默新建 / 使用默认会话**）」。
- **处置**：**只登记、不擅修**（`src/` 属软件代理职责）；本轮**不写红测**（避免红套件），registry 交 PM 路由 developer。
- **本轮测试边界**：TC-INT-092 / TC-E2E-018 仅使用**显式** `session_id`，故不依赖该兜底行为；该缺陷**不使任何既有断言失败**。

### 15.6 突变敏感性自证（证明新增守卫为**载荷性**，非空转）

| 突变 | 期望失效的用例 | 实测 |
|------|--------------|------|
| 清空 `AGGREGATION_FORBIDDEN_LABELS` | TC-UNIT-067 | **FAIL**（内部标识未被清洗） |
| 令 `_aggregate` 返回逐专家拼接（内部产物外流） | TC-INT-089 | **FAIL**（content 未融合为单一答复） |
| 令 `resume` 静默产出 content+done（无门校验） | TC-INT-093 | **FAIL**（未携带状态却静默续跑） |
| 令 `GraphConfig` 默认 `confirmation_gate_enabled=True` | TC-INT-094 | **FAIL**（默认须关闭） |
| 令 `MemorySessionStore.load` 忽略隔离（任何键都返回状态） | TC-INT-092 | **FAIL**（跨会话注入） |
| 令 `run` 产出两个 `done` | TC-INT-088 | **FAIL**（终止事件须恰一次） |
| 令重启后的新存储读回旧状态 | TC-UNIT-069 | **FAIL**（状态丢失须 fail-closed） |

（突变以临时 monkeypatch 在**进程内**执行，**未改动 `src/` 文件**；证据见 `docs/test_report.md` §16.4。）

### 15.7 门控与度量

- **三层门控**（沿用 §6）：unit **70/70 = 100%**（≥80% 门槛 **PASSED**）、integration **96/96 = 100%**（≥90% 门槛 **PASSED**）、e2e **18/18**；合计 **184/184 = 100%**（EXIT=0，0 skip/xfail）。
- **前端冒烟层**（独立）：沿用 R10，**6/6**。
- **命令与原始输出**见 `docs/test_report.md` §16 与 `docs/evidence/groupd_r11_*.log`。
- **门控结论（本代理自评）**：三层全绿、算术一致、编号只增不改 → 建议 **PASS_WITH_CONDITIONS**；**唯一条件** = §15.5 的 2 项 AC 未覆盖 + 4 项部分覆盖（待 IFC-IB-298~308 实现轮闭合）+ FND-R11-01 待路由 developer。

### 15.8 R11 修复补丁留痕（1.6.1）

- **修复项（有界，仅一处文本 + 版本行）**：§3.2 集成测试主登记表的 **TC-INT-039** 行，「关联 US / 关联 AC」两列由旧值 `US-IB-08` / `AC-IB-08-01` **补齐**为 `US-IB-19（R11 重挂，原 US-IB-08）` / `AC-IB-19-01（R11 重挂，原 AC-IB-08-01）`，行文风格与 §3.1 已重挂的 4 条单元行（TC-UNIT-016/017/018/022）**完全对齐**。
- **内部一致性自检**：修复后 §3.2 与 **§15.1 变更清单**（TC-INT-039 重挂行）、**§15.2 归属判定**（TC-INT-039 → AC-IB-19-01）、**§4（AC→TC 矩阵）**（`AC-IB-08-01` 行标注「TC-INT-039 已于 R11 重挂至 AC-IB-19-01」、`AC-IB-19-01` 行列出 TC-INT-039）以及 `docs/test_report.md` **§16.2(A)** **完全一致**，此前「主登记表自相矛盾」已消除。
- **范围纪律**：**未改**任何其它用例行、任何断言、`tests/**`、`src/**`、`docs/test_report.md` 既有结论；用例数仍 **184**（unit 70 / integration 96 / e2e 18），**编号只增不改**。

---

## §16 R12 增量（R8 实现到位后的补测轮 REV-12-5：闭合 AC-IB-19-02 / AC-IB-20-04 并补全其余；追加，不改写 §9~§15）

> **本轮定位**：R11（§15）登记 AC-IB-19-02 / AC-IB-20-04 因「IFC-IB-298~308 未实现」而**未覆盖**、且 19-03 / 20-02 / 20-03 / 20-05 仅**部分覆盖**。R8 实现（`CompletionPayload` / `completion_event` / `is_user_visible` / `ConfirmationGateState` / `can_resume` / `ResumePayload` / `POST /api/chat/resume` / `IB_REASONING_STREAM_ENABLED` / `IB_SESSION_PERSISTENCE_POLICY` / `IB_CONFIRMATION_GATE_ENABLED`）**已落地于 `src/`**。本轮（REV-12-5）据此**补齐测试**：闭合 2 项未覆盖 AC、补全 4 项部分覆盖、回补 **FND-R11-01** 与 **BLK-R8-02** 的修正/负例。
>
> **边界纪律（重要）**：本轮**仅动 `tests/`、`docs/test_plan.md`、`docs/test_report.md`、`docs/evidence/groupd_r12_*.log`**；**不改 `src/` 任何实现**（实现已收口），**不改** `docs/phase_status.md` 与设计真源四文档（`architecture_design` / `module_design` / `requirements_spec` / `user_stories`）。既有断言**不削弱**、**不新增 skip/xfail**、编号**只增不改**、AC 一律 G/W/T 语义对齐。

### 16.1 新增用例清单（16 条；**既有 184 条编号一律不变**）

| TC-ID | 层 | 文件 | 关联 US | 关联 AC | 断言要点 |
|-------|----|------|--------|--------|---------|
| TC-UNIT-070 | 单元 | `tests/unit/test_stream_session_lifecycle_unit_r12.py` | US-IB-19 | AC-IB-19-02 | `completion_event`：`None`→空串（不臆造）、空元组→`[]`（可区分）、`had_content` 边界、引用只含定位（无正文/字节）、终态恒 `done` |
| TC-UNIT-071 | 单元 | 同上 | US-IB-19 | AC-IB-19-03 | `reasoning` 默认不可见且不入 `USER_VISIBLE_KINDS`；未登记 kind 默认不可见；既有 6 kind 逐位不变、`confirmation_required` 为追加第 7 |
| TC-UNIT-072 | 单元 | 同上 | US-IB-20 | AC-IB-20-02/20-05 | 策略取值域/默认、状态丢失结局唯一取值、`GlobalConfig` 默认 `False` |
| TC-UNIT-073 | 单元 | 同上 | US-IB-20 | AC-IB-20-04/20-05 | `can_resume` 三判据穷举（含决策指向他门）+ `ResumePayload.from_dict` 残缺载荷恒 `None` |
| TC-UNIT-074 | 单元 | `tests/unit/test_definition_keyword_intra_r12.py` | US-IB-18 | AC-IB-18-02 | 专家内部空/纯空白关键词 → `expert_keyword_empty`；不误报重复；跨专家非空同词不产生内部空码 |
| TC-UNIT-075 | 单元 | 同上 | US-IB-18 | AC-IB-18-02 | 专家内部归一化重复 → `expert_keyword_duplicate`；跨专家仍报 `expert_keyword_collision`（不误报新码）；全异文档无误报 |
| TC-INT-096 | 集成 | `tests/integration/test_stream_session_lifecycle_int_r12.py` | US-IB-20 | AC-IB-20-04 | 门挂起：`confirmation_required` 恰一次、无 content、无空帧、终态单发、中间态落库 |
| TC-INT-097 | 集成 | 同上 | US-IB-20 | AC-IB-20-04 | 批准续跑 → content+done；不再次触发门；中间态清除 |
| TC-INT-098 | 集成 | 同上 | US-IB-20 | AC-IB-20-04/20-05 | 续跑四负例（无中间态/无决策/不符/决策为拒）均 `error`+终态、无 content |
| TC-INT-099 | 集成 | 同上 | US-IB-20 | AC-IB-20-04 | HTTP 真实流路径键续跑成功（200 SSE）；视图经唯一入口重建同键（MAJOR-1） |
| TC-INT-100 | 集成 | 同上 | US-IB-20 | AC-IB-20-01/20-04/20-05 | HTTP 续跑负例族：404/409/400；自造 **2 段**键不得命中 3 段真实会话（MAJOR-1 守卫） |
| TC-INT-101 | 集成 | 同上 | US-IB-20 | AC-IB-20-01 | `GET /api/chat/stream` 缺 `session_id` → **400** 且不开流（FND-R11-01）；显式合法 → 200 SSE |
| TC-INT-102 | 集成 | 同上 | US-IB-20 | AC-IB-20-03 | 门关 vs 门开无构造器 → 事件序列逐位相同（零行为差异）；构造抛异常 → fail-closed（无 content） |
| TC-INT-103 | 集成 | 同上 | US-IB-19 | AC-IB-19-02/19-05 | 真实 `run`：`done` 恰一次且收尾；`done.data==""`（不臆造）；无任何载荷含 `citations` 键 |
| TC-INT-104 | 集成 | 同上 | US-IB-20 | AC-IB-20-03 | 门未启用时恢复 → **409** `conflict`、不开流（不新建会话、不重跑） |
| TC-E2E-019 | E2E | `tests/e2e/test_user_journeys.py` | US-IB-20 | AC-IB-20-04/20-05 | 真实 HTTP 旅程：默认无等待成流 → 预置中间态 → 携决策续跑 200 SSE 完成 → 中间态清除 → 再恢复 404、无决策 409 |

> **既有用例零改动**：TC-UNIT-016~069、TC-INT-001~095、TC-E2E-001~018 的**代码与断言一字未改**；TC-UNIT-062 / TC-UNIT-065（跨专家撞车守卫）**未被削弱**（R12 的 TC-UNIT-074/075 另测**专家内部**项，见 §16.4 对照）。

### 16.2 覆盖闭合判定（逐项）

| AC | R11 状态（§15.5） | R12 状态 | 依据 TC | 备注 |
|----|------------------|---------|---------|------|
| AC-IB-19-02 | 未覆盖 | **Tested（机制层完整）** | TC-UNIT-070, TC-INT-103 | 端到端「命中→产物」装配来源登记残余（§16.5） |
| AC-IB-19-03 | 部分 | **Tested**（默认口径） | TC-UNIT-068/071, TC-INT-090 | 「启用后可见」端上呈递属前端运行期（残余 §16.5） |
| AC-IB-20-01 | 部分（FND-R11-01） | **Tested（完整）** | TC-UNIT-018, TC-INT-092/101, TC-E2E-018 | FND-R11-01 已修复并守住 |
| AC-IB-20-02 | 部分 | **Tested**（配置层） | TC-UNIT-072, TC-INT-093 | 「部署文档声明」属部署面（残余 §16.5） |
| AC-IB-20-03 | 部分 | **Tested（完整）** | TC-INT-094/102/104 | 含门启用后行为 |
| AC-IB-20-04 | 未覆盖 | **Tested（完整）** | TC-UNIT-073, TC-INT-096/097/099, TC-E2E-019 | 呈递 + 决策回传恢复 + 负例全族 |
| AC-IB-20-05 | 部分 | **Tested（完整）** | TC-UNIT-069/072/073, TC-INT-093/098, TC-E2E-019 | 含携决策续跑 |

### 16.3 覆盖与计数复核

- **计数**：unit **70 → 76**（+6）、integration **96 → 105**（+9）、e2e **18 → 19**（+1）；合计 **184 → 200**（前端冒烟 6 例仍**独立计数、不并入**）。
- **US 覆盖**：20/20 US 均有 ≥1 条用例；US-IB-18 增 2 条、US-IB-19 增 3 条、US-IB-20 增 11 条。
- **Must Have 关键路径 E2E 覆盖**：**16/16 = 100%**（US-IB-20 旅程由 TC-E2E-018/019 双覆盖）。
- **可测 AC 覆盖**：**90/90 = 100%**（0 项未覆盖；残余见 §16.5）。
- **算术**：**200 = 76 + 105 + 19**；全绿 **200 passed, 0 failed, 0 skipped, 0 xfail**。

### 16.4 突变敏感性自证（证明 R12 新增守卫为**载荷性**，非空转）

| 突变 | 期望失效的用例 | 实测 |
|------|--------------|------|
| 令 `completion_event(None)` 改为输出 `{"citations": []}` | TC-UNIT-070 / TC-INT-103 | **FAIL**（未产出产物须为空串，不得伪造成空引用清单） |
| 令 `completion_payload_json` 对空元组输出 `None` | TC-UNIT-070 | **FAIL**（空元组须编码为 `[]`） |
| 令 `USER_VISIBLE_KINDS` 加入 `"reasoning"` | TC-UNIT-071 | **FAIL**（默认不得可见） |
| 令 `can_resume` 缺 `payload.decision` 时返回 `True` | TC-UNIT-073 / TC-INT-098 | **FAIL**（未携决策须 fail-closed） |
| 令 `chat_stream_endpoint` 缺 `session_id` 回退 `"default"` | TC-INT-101 | **FAIL**（须 400，不得静默回退） |
| 令 `chat_resume_endpoint` 自造 2 段键 | TC-INT-099 / TC-INT-100 | **FAIL**（真实 3 段会话恒 404） |
| 令专家内部校验把空词跳过（不报 `expert_keyword_empty`） | TC-UNIT-074 | **FAIL**（空词须被定位） |
| 令专家内部重复改用跨专家码 `expert_keyword_collision` | TC-UNIT-075 | **FAIL**（内部项须报 `expert_keyword_duplicate`） |

（突变以临时 monkeypatch 在**进程内**执行，**未改动 `src/` 文件**；证据见 `docs/test_report.md` §17。）

### 16.5 残余登记（**如实登记，不以空断言充数**）

| AC | 已覆盖部分 | **残余（未断言）子句** | 理由 / 去向 |
|----|-----------|----------------------|------------|
| AC-IB-19-02 | `completion_event` 契约/编码语义、`had_content` 边界、不臆造引用、终态不拆分 | **端到端**把检索命中装配为 `CompletionPayload.citations` | 编排层 `Orchestrator._run_inner` 恒传 `payload=None`（未接线），本轮不擅改 `src/`；登记交 PM/developer（报告 §17） |
| AC-IB-19-03 | `reasoning` 默认不可见、白名单、不混帧、`IB_REASONING_STREAM_ENABLED` 默认 `False` | **启用后**思考分区的端上可见呈递 | 属前端运行期（浏览器挂载/交互），离线无自动化浏览器环境（同 §5 口径） |
| AC-IB-20-02 | 持久化策略类型/配置默认（`in_process`）、状态丢失 fail-closed | 「持久化策略须在**部署文档**显式声明」 | 属部署面（GROUP_E），本轮冻结（同 AC-IB-12-01/04 口径）|

> **不再存在的缺口**：R11 §15.5 所列 2 项「未覆盖」（AC-IB-19-02 / AC-IB-20-04）已由本轮闭合；FND-R11-01（`chat_stream_endpoint` 缺 `session_id` 静默兜底默认会话）已由 developer 修复、本轮以 TC-INT-101 守住（**CLOSED_VERIFIED**，报告 §17）。BLK-R8-02（专家内部关键词空/重复）由 TC-UNIT-074/075 覆盖（**CLOSED_VERIFIED**，报告 §17）。

### 16.6 门控与度量

- **三层门控**（沿用 §6）：unit **76/76 = 100%**（≥80% 门槛 **PASSED**）、integration **105/105 = 100%**（≥90% 门槛 **PASSED**）、e2e **19/19**；合计 **200/200 = 100%**（EXIT=0，0 skip/xfail）。
- **前端冒烟层**（独立）：沿用 R10，**6/6**。
- **命令与原始输出**见 `docs/test_report.md` §17 与 `docs/evidence/groupd_r12_*.log`。
- **门控结论（本代理自评）**：三层全绿、算术一致、编号只增不改、2 项未覆盖 AC 闭合 → 建议 **PASS**；残余 3 项（§16.5）**不阻塞**通过率，仅登记待后续轮（前端运行期 / 部署面 / 端到端装配来源）。

---

## §18 R13 增量（REV-13：账户体系 / 会话 / 前端商用界面纳入测试范围）

> 触发：**REV-13（Task REV-13-4）**。上游 GROUP_C R13 实现门控 **GR-C-009 = PASS_WITH_CONDITIONS**（42 文件，CRITICAL 0）。
> 调用 ID：**INV-GROUP_D-INTELBASE-012**。本轮把 `user_stories.md` **1.4.0** 新增的 **US-IB-21 ~ US-IB-29**（29 组 AC）纳入测试范围，
> 新增 **32 条 Python 用例**（unit 12 / integration 18 / e2e 2）与 **7 条前端冒烟用例**（TC-FE-007 ~ TC-FE-013，计入前端独立层）。
> 硬约束：**未改 `src/**`**、**未改 `docs/phase_status.md`**、**未 commit / 未 push / 未部署**；测试代码内**无任何真实凭据**（口令占位符仅经 `IB_DEFAULT_ADMIN_PASSWORD` 注入）。
> **编号只增不改**：既有最高编号为 TC-UNIT-082 / TC-INT-104 / TC-E2E-019 / TC-FE-006；本轮新增一律紧接其后续编，既有用例**未改一行**。

### 18.1 测试策略与范围（R13）

- **范围（in-scope）**：US-IB-21 用户名/口令登录与「零粘贴令牌入口」；US-IB-22 首登强制改密；US-IB-23 账户 CRUD + 1:1 项目绑定 + ops 403；US-IB-24 项目内全功能 / 跨项目 403 / admin 全局；US-IB-25 会话携带·过期·续期·无 Cookie；US-IB-26 前端商用界面（源码结构层）；US-IB-27 与既有 `AuthzPolicy` 端口协作（**零第二授权真源** / fail-closed）；US-IB-28 HTTPS 部署**静态可验证面**；US-IB-29 登录失败限速与审计（`[INFERRED]`）。
- **范围（out-of-scope）**：生产 TLS **运行期握手**、真实浏览器**渲染与交互**、外部网络 / 真实 Qdrant / DeepSeek / bge-m3（离线约束）。
- **测试环境**：Python 3.14.6 / pytest 9.1.1 / Django 6.0.6 / bcrypt 5.0.0；内存账户存储 + `SqliteAccountStore`（临时文件）；Django test Client（进程内）；前端 `node --test`（Node 内建，**零新增依赖**）。
- **夹具（`tests/conftest.py` 新增）**：
  - `accounts_app` —— **生产形态**装配（显式 `IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy`，使 `build_authz` 走 `SessionTokenResolver` + `AccountsPolicy`）、内存账户后端、TTL 3600s / 续期窗口 600s；
  - `locked_accounts_app` —— 同上并启用**账户级锁定阈值 = 3**（AC-IB-29-01 锁定回归）；
  - 环境变量经 `monkeypatch` **全程保持**（`load_account_settings()` 在**请求期**读取；若装配后即还原，请求期将回落默认值、测试失真 —— 此为本轮修正的一个夹具缺陷，见报告 §18.6）；
  - 助手 `login` / `bearer` / `change_password`（**只**经 `Authorization: Bearer` 头，绝不进查询串）。
- **覆盖率目标（沿用 §6）**：单元 ≥ 80%、集成 ≥ 90%、E2E 关键路径 100%。

### 18.2 测试用例清单（新增）

**（A）单元层（UNIT）—— `tests/unit/test_accounts_unit_r13.py`（12 条）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-UNIT-083 | US-IB-25 | AC-IB-25-01 | UNIT | 令牌原语：不透明、唯一、服务端只存 sha256 摘要（原文不入库） |
| TC-UNIT-084 | US-IB-22/23 | AC-IB-22-01、AC-IB-23-01、AC-IB-23-02 | UNIT | `MemoryAccountStore` 建户语义 + 1:1 绑定（ops 无项目即拒） |
| TC-UNIT-085 | US-IB-22 | AC-IB-22-03 | UNIT | 口令只落 bcrypt 摘要（`$2…`），永不落明文 |
| TC-UNIT-086 | US-IB-25 | AC-IB-25-01、AC-IB-25-02 | UNIT | 会话签发 / 解析 / 过期 / 撤销语义 |
| TC-UNIT-087 | US-IB-25 | AC-IB-25-03 | UNIT | 续期：`expires_at` 前滑、**`issued_at` 不变**（滑动窗口，不延长绝对寿命） |
| TC-UNIT-088 | US-IB-22/23 | AC-IB-23-03 | UNIT | `revoke_sessions_for_user`：全撤 / 保留当前（改密撤其余会话） |
| TC-UNIT-089 | US-IB-22 | AC-IB-22-01 | UNIT | `seed_default_admin` 幂等且不覆盖既有口令；首登置 `must_change_password` |
| TC-UNIT-090 | US-IB-27/24/23 | AC-IB-27-01、AC-IB-24-03、AC-IB-23-03、AC-IB-27-03 | UNIT | `SessionTokenResolver` fail-closed + 角色 + 全局哨兵 `"*"` + **无授权方法**（零第二真源） |
| TC-UNIT-091 | US-IB-22 | AC-IB-22-02 | UNIT | 口令强度策略边界 |
| TC-UNIT-092 | US-IB-27/29 | AC-IB-27-01、AC-IB-29-01、AC-IB-29-02 | UNIT | `AccountsPolicy` / `LoginThrottle` / `build_throttle` / `audit` 签名（审计不含凭据字段） |
| TC-UNIT-093 | US-IB-23/25 | AC-IB-23-01、AC-IB-23-02、AC-IB-25-01 | UNIT | `SqliteAccountStore` 真实往返 + CHECK 约束（1:1 绑定） |
| TC-UNIT-094 | US-IB-27 | AC-IB-27-02、AC-IB-27-03 | UNIT | `build_authz` 缺策略 → `StartupError`（fail-closed）+ 策略模块加载 |

**（B）集成层（INT）—— `tests/integration/test_accounts_int_r13.py`（15 条）+ `tests/integration/test_accounts_deploy_int_r13.py`（3 条）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-INT-105 | US-IB-21/25 | AC-IB-21-01、AC-IB-25-04 | INT | 登录成功签发令牌、响应**不回显凭据** |
| TC-INT-106 | US-IB-21 | AC-IB-21-02 | INT | 未知账户与错口令返回**逐字相同** 401（防枚举），不签发令牌 |
| TC-INT-107 | US-IB-22 | AC-IB-22-01、AC-IB-22-02 | INT | 首登受限会话：仅白名单（me / change-password / logout）放行，其余端点 403 `password_change_required` |
| TC-INT-108 | US-IB-22/25 | AC-IB-22-02、AC-IB-25-01 | INT | 改密强度校验 + 改密后**撤销其余会话** |
| TC-INT-109 | US-IB-25 | AC-IB-25-01、AC-IB-25-03 | INT | 有效令牌校验 / 登出撤销 / 临近过期续期 |
| TC-INT-110 | US-IB-25 | AC-IB-25-02 | INT | 过期令牌访问受保护接口 → 401 |
| TC-INT-111 | US-IB-23 | AC-IB-23-01、AC-IB-23-02、AC-IB-23-03 | INT | 账户 CRUD（仅 admin）+ 绑定 + 停用后不得登录 |
| TC-INT-112 | US-IB-23 | AC-IB-23-04 | INT | ops（非 admin）执行账户管理 → 403 |
| TC-INT-113 | US-IB-24 | AC-IB-24-01、AC-IB-24-02、AC-IB-24-03 | INT | 项目内全功能（上传）/ 跨项目 403 / admin 全局放行 |
| TC-INT-114 | US-IB-23 | AC-IB-23-03 | INT | 已停用账户登录 → 统一 401 |
| TC-INT-115 | US-IB-21 | AC-IB-21-04 | INT | `?token=` / `?access_token=` 在**所有**端点 → 400 `token_in_query_forbidden` |
| TC-INT-116 | US-IB-25 | AC-IB-25-04 | INT | 登录 / me / accounts / files 响应**零 `Set-Cookie`** |
| TC-INT-117 | US-IB-21/27 | AC-IB-21-03、AC-IB-27-01 | INT | 离线令牌（`EnvTokenResolver`）**不得**触达账户管理面 → 403 |
| TC-INT-118 | US-IB-29 | AC-IB-29-01 | INT | **账户维度**锁定：连续失败达阈值后即使口令正确亦拒 |
| TC-INT-119 | US-IB-29 | AC-IB-29-01 | INT | **来源 IP 维度**限速 → 期望 429。**本用例暴露实现缺陷 DEFECT-R13-01（当前恒 401，429 分支不可达）** → 见报告 §18.6 |
| TC-INT-120 | US-IB-28 | AC-IB-28-01、AC-IB-28-02 | INT | nginx TLS 模板：`listen 443 ssl` + 证书占位符 + 回环 `127.0.0.1:18080` + `Authorization` 透传 + `proxy_buffering off` + **零证书材料**；HTTP 块仅跳转 |
| TC-INT-121 | US-IB-28/27 | REQ-NFR-IB-15、AC-IB-27-02 | INT | R13 九键登记于唯一真源 `IB_RUNTIME_ENV_KEYS` 且不混入冻结的 `IB_ENV_KEYS`；`env.example` 仅占位符；迁移 003 摘要列 + CHECK；检查清单 [B15]~[B20] |
| TC-INT-122 | US-IB-28 | REQ-FUNC-IB-30 | INT | 迁移 003 与运行时 `ensure_schema()` **列级单源一致**（`PRAGMA table_info` 比对） |

**（C）E2E 层（关键路径）—— `tests/e2e/test_accounts_journeys_r13.py`（2 条）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-E2E-020 | US-IB-21 + 22 + 23 + 24 + 25 | AC-IB-21-01、AC-IB-22-01/02、AC-IB-23-01/03、AC-IB-24-01/02 | E2E | 完整旅程：admin 首登 → 改密前 403 → 改密 → 建 ops(p_alpha) → ops 首登改密 → 项目内上传 201 → 跨项目 403 → 登出 401 → 停用后拒登 |
| TC-E2E-021 | US-IB-21 | AC-IB-21-03、AC-IB-21-04 | E2E | 无粘贴令牌旁路旅程：各视图端点 `?token=` 一律 400、登录仅 JSON 体、全响应零 Cookie |

**（D）前端冒烟层（FE，独立层）—— `src/frontend/tests/frontend.smoke.test.js` 追加（7 条，层内合计 13）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-FE-007 | US-IB-21 | AC-IB-21-03 | FE | `App.vue` 不再有「粘贴访问令牌」入口（结构性判据：无 `<input>` / 无 `setToken` / 无 `v-model`） |
| TC-FE-008 | US-IB-21 | AC-IB-21-03 | FE | `main.ts` 不再从 URL 读令牌；全局 401 接会话层；挂载路由 |
| TC-FE-009 | US-IB-21 | AC-IB-21-01、AC-IB-21-02 | FE | 登录页结构（用户名 + 口令）+ **统一失败文案**，不提示账户是否存在 |
| TC-FE-010 | US-IB-22/23 | AC-IB-22-01、AC-IB-23-04 | FE | 路由守卫：hash 模式 + 未登录→登录 + 改密态→改密页 + `requiresAdmin` 以 `isAdmin` 判定 |
| TC-FE-011 | US-IB-26 | AC-IB-26-01、AC-IB-26-02、AC-IB-26-03 | FE | 控制台外壳：左 `<aside>` + 右 `<main>` + 主题切换 + `requiresAdmin` 过滤导航 + 中文角色文案 |
| TC-FE-012 | US-IB-25 | AC-IB-25-04 | FE | 令牌只经 `sessionStorage` + `Authorization: Bearer`；**无** `document.cookie` / `localStorage` |
| TC-FE-013 | US-IB-26 | AC-IB-26-04 | FE | R13 依赖（element-plus / vue-router）本地打包 + 锁同步 + 源码零 CDN |

### 18.3 AC ↔ TC 覆盖矩阵（US-IB-21 ~ US-IB-29）

| AC-ID | 覆盖 TC | 结论 |
|-------|---------|------|
| AC-IB-21-01 | TC-INT-105、TC-E2E-020、TC-FE-009 | 覆盖 |
| AC-IB-21-02 | TC-INT-106、TC-FE-009 | 覆盖（时延侧信道见 §18.4） |
| AC-IB-21-03 | TC-INT-117、TC-E2E-021、TC-FE-007、TC-FE-008 | 覆盖 |
| AC-IB-21-04 | TC-INT-115、TC-E2E-021 | 覆盖 |
| AC-IB-22-01 | TC-UNIT-084、TC-UNIT-089、TC-INT-107、TC-E2E-020、TC-FE-010 | 覆盖 |
| AC-IB-22-02 | TC-UNIT-091、TC-INT-107、TC-INT-108 | 覆盖 |
| AC-IB-22-03 | TC-UNIT-085 | 覆盖（接口/存储面；日志文件面见 §18.4） |
| AC-IB-23-01 | TC-UNIT-084、TC-INT-111、TC-E2E-020 | 覆盖 |
| AC-IB-23-02 | TC-UNIT-084、TC-UNIT-093、TC-INT-111 | 覆盖 |
| AC-IB-23-03 | TC-UNIT-088、TC-INT-111、TC-INT-114、TC-E2E-020 | 覆盖 |
| AC-IB-23-04 | TC-INT-112、TC-FE-010 | 覆盖 |
| AC-IB-24-01 | TC-INT-113、TC-E2E-020 | 覆盖 |
| AC-IB-24-02 | TC-INT-113、TC-E2E-020 | 覆盖 |
| AC-IB-24-03 | TC-UNIT-090、TC-INT-113 | 覆盖 |
| AC-IB-25-01 | TC-UNIT-083、TC-UNIT-086、TC-UNIT-093、TC-INT-105、TC-INT-109 | 覆盖 |
| AC-IB-25-02 | TC-UNIT-086、TC-INT-110 | 覆盖 |
| AC-IB-25-03 | TC-UNIT-087、TC-INT-109 | 覆盖 |
| AC-IB-25-04 | TC-INT-105、TC-INT-116、TC-FE-012 | 覆盖 |
| AC-IB-26-01 | TC-FE-011 | 覆盖（源码结构层；运行期呈递见 §18.4） |
| AC-IB-26-02 | TC-FE-011 | 覆盖（源码结构层） |
| AC-IB-26-03 | TC-FE-011 | 覆盖（源码结构层） |
| AC-IB-26-04 | TC-FE-013（+ 既有 TC-FE-005） | 覆盖 |
| AC-IB-27-01 | TC-UNIT-090、TC-UNIT-092、TC-INT-117 | 覆盖 |
| AC-IB-27-02 | TC-UNIT-094 | 覆盖 |
| AC-IB-27-03 | TC-UNIT-090、TC-UNIT-094 | 覆盖 |
| AC-IB-28-01 | TC-INT-120 | 覆盖（静态模板；运行期握手见 §18.4） |
| AC-IB-28-02 | TC-INT-120 | 覆盖（静态模板） |
| AC-IB-29-01 | TC-UNIT-092、TC-INT-118、**TC-INT-119（FAIL）** | 部分覆盖：**账户维度 PASS；来源 IP 维度 FAIL → DEFECT-R13-01** |
| AC-IB-29-02 | TC-UNIT-092 | 覆盖（签名层不含凭据字段） |

- **US 级覆盖**：US-IB-21 ~ US-IB-29 **9/9 每故事均有 ≥1 用例**。

### 18.4 不可测试项与残余（如实登记）

| AC-ID / 项 | 已覆盖部分 | **残余（未断言）子句** | 理由 / 去向 |
|-----------|-----------|----------------------|------------|
| AC-IB-26-01/02/03 | 布局 / 主题切换 / 中文的**源码结构**判据（TC-FE-011） | 浏览器内**运行期渲染与交互**（真实点击切换、视觉排版） | 离线无自动化浏览器环境（沿用 §5/§16.5 口径）；属前端运行期，登记待前端轮（报告 §18.6） |
| AC-IB-28-01 | nginx TLS **模板**静态断言（TC-INT-120） | **运行期**真实 TLS 握手 / 证书链校验 | 离线无 nginx / 无证书；属部署面运行期（GROUP_E），本轮不阻塞 |
| AC-IB-22-03（日志面） | 存储层无明文（TC-UNIT-085）+ 接口响应无凭据回显（TC-INT-105） | **日志文件**级明文扫描 | 属证据流程（`groupd_credscan`）而非 pytest 用例；日志纪律另由凭据扫描证据留档 |
| AC-IB-21-02（时延侧信道） | 统一**文案**已断言（TC-INT-106） | 响应**时延**是否泄露账户存在性 | 离线 / 单机无法确定性断言 → 记为**残余风险**，不臆造 PASS |
| REQ-FUNC-IB-30（单源一致性，语句级） | 列级一致已断言（TC-INT-122） | 迁移 003 与运行时 DDL 的**语句级字节**一致 | 机器可断言的列级已覆盖；语句级字节一致留待后续轮 |

### 18.5 门控与度量口径（R13）

- **度量定义**：`total = pass + fail + skip + blocked`（精确等式）；`通过率 = pass / (pass + fail)`（skip / blocked **不计入分母**）。
- **门控**：unit **≥ 80%** → 才可执行 integration；integration **≥ 90%** → 才可执行 e2e；E2E **关键路径 100%**。
- **零 masking 纪律**：**0 skip / 0 xfail**；未执行不得记 PASS；`TC-INT-119` 为**真实执行后失败**，作为缺陷证据保留为 **FAIL**，**不以 skip / xfail 掩蔽**。
- **结论数值**（详见 `docs/test_report.md` §18.1）：unit **95/95 = 100%**、integration **122/123 = 99.19%**、e2e **21/21 = 100%**（关键路径 100%）。

### 18.6 计数基线与 +7 对账（如实登记）

- **R13 前基线**：`python -m pytest tests -q` = **207 passed**（EXIT 0）；分层 unit **83** / integration **105** / e2e **19**。
- **R12 门控（GR-D-009）登记基线**：**200**（unit 76 / integration 105 / e2e 19）。
- **+7 差值来源（对账结论）**：**非集合计数错误**，全部落在**单元层**，来自 `tests/unit/test_llm_tool_loop.py` 新增的 **7 条用例**（TC-UNIT-076 ~ TC-UNIT-082），由 commit **`fa0a7a4`（"fix(llm): 实现完整工具调用循环，修复聊天检索不落地的根因"）**引入 —— 属**基线记录之后**由 developer 侧提交新增，未被 R12 门控登记。
- **`tests/**` 归属观察**：`git status --short tests/` 在 R13 起始快照为空，即 **GROUP_C 的 R13 增量未新增 / 未改动任何 `tests/**` 文件**（`tests/` 全程为 GROUP_D 领地）；但历史上 developer 提交（`fa0a7a4`、`9b04b20`）曾**直接增改 `tests/**`**（即上述 +7 来源）—— 建议 PM 在流程上明确 `tests/**` 的写权边界。
- **R13 后目标基线**：**239**（unit **95** / integration **123** / e2e **21**），较 207 增 32（本轮新增：unit 12 + integration 18 + e2e 2 = 32）；前端冒烟层 6 → **13**，**仍自立一层、不计入 239**。

---

## §19 R14 增量（REV-14：R13 回归缺陷修复的独立测试补测与验证）

> 触发：**REV-14**（R13 回归缺陷修复：全局管理员「当前项目」选择与 `X-IB-Project` 传播）。上游 GROUP_C 实现门控 **GR-C-010 = PASS_WITH_CONDITIONS**。
> 调用 ID：**INV-GROUP-D-INTELBASE-014**。本轮**独立复核 + 补测**：新增 Python **3 条**（TC-INT-126 ~ 128）+ 前端 **4 条**（用例 18 ~ 21）；并把 GROUP_C R14 组的 **3 条由撞号 TC-INT-120 ~ 122 更正为 TC-INT-123 ~ 125**（恢复「编号唯一、只增不改」）。
> 硬约束：**未改 `src/**`**、**未 commit / push / 部署**、**未触网**、**未触碰目标机 192.168.31.133**；测试代码与夹具内**无任何真实凭据**（口令仍为占位替身值）。

### 19.1 测试策略与范围（R14）

- **范围（in-scope）**
  - **`GET /api/projects`（IFC-IB-333）授权口径**：admin 见全部 / ops 仅见自身 / 未认证 `401` / `?token=`·`?access_token=` 一律 `4xx` / 零 `Set-Cookie` / 非 `GET` 一律 `405`。
  - **`X-IB-Project` 头契约（IFC-IB-334，加成式扩展既有 `AuthMiddleware`，其代码零改动）**：admin 选定项目后项目级端点解 fail-closed（`/api/config/definition` 无头 `503` → 带头 `200`）；**未选项目仍 fail-closed**；未知项目名不校验存在性（仍 `503`）；ops 跨项目 `403 project_mismatch`；ops 绑定**未登记**项目时刻 fail-closed。
  - **前端 `projectContext`（IFC-IB-335）**：`load` / `select` / `clear` / `headerValue`；ops 结构上不可切换；`load` 失败 / 结果集为空 ⇒ `current = null`（不注入头，fail-closed）；admin 单项目预选；`select` 白名单。
  - **`client.ts headers()` 单一注入点（IFC-IB-336）**：`current` 非空 ⇒ 注入 `X-IB-Project`、为空 ⇒ 不注入；SSE 路径（`chatStream` / `chatResume`）同经 `headers()`；调用点 `extra` **不得**覆盖 provider 值；provider 抛错 ⇒ 不注入。
- **范围（out-of-scope）**：**真实浏览器**下 `el-select` 交互与 `<router-view :key>` 重挂载的**运行期**行为（见 §19.4 **R14-L-01**）；真实 TLS 握手；外部网络 / 真实 Qdrant / DeepSeek / bge-m3（离线约束）。
- **测试环境**：Python 3.14.6 / pytest 9.1.1 / Django 6.0.6；**内存账户存储** + Django test Client（进程内，不触网）；前端 `node --test`（Node **v24.18.0**，支持 `.ts` 类型擦除导入）。
- **覆盖率目标（沿用 §6）**：单元 ≥ 80%、集成 ≥ 90%、E2E 关键路径 100%。

### 19.2 测试用例清单（R14）

**（A）集成层（INT）—— `tests/integration/test_project_context_int_r14.py`（6 条：TC-INT-123 ~ 128）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-INT-123 | US-IB-24 | AC-IB-24-03 | INT | `/api/projects` **非项目级端点**：admin 未选定项目也 `200` 返回**全部**项目；未认证 `401`；`?token=`/`?access_token=` `400`；零 `Set-Cookie`；条目字段集固定 `{project_id,name,is_current}` |
| TC-INT-124 | US-IB-24 | AC-IB-24-03 | INT | admin 未选 ⇒ `/api/config/definition` `503`（**未选项目即不泄露**）；带头选 `p_alpha` ⇒ `200`（**R13 回归缺陷修复的直接证据**）；未知 `p_ghost` ⇒ `503`；`is_current` 反映**本请求**的 effective_project |
| TC-INT-125 | US-IB-24 | AC-IB-24-02 | INT | ops 列表**恒 1 项**（自身，`is_current=True`，结构上不可切换）；跨项目头 ⇒ `403 project_mismatch`；自身 / 缺省 ⇒ 放行 |
| TC-INT-126 | US-IB-24 | AC-IB-24-03 | INT | **方法纪律**：`POST`/`PUT`/`DELETE`/`PATCH` ⇒ `405 method_not_allowed`（admin 与 ops 同此）、零 `Set-Cookie`；`GET` 仍 `200`（此前该 `405` 分支无任何用例触达） |
| TC-INT-127 | US-IB-24 | AC-IB-24-02 | INT | ops 绑定**未登记**项目 ⇒ 列表**为空**（**不臆造、不回落枚举他项目**）；其项目级端点 `503`；声明他项目仍 `403`（边界不因自身未登记而放宽） |
| TC-INT-128 | US-IB-24 | AC-IB-24-03 | INT | 列表按 `project_id` **升序**稳定；`X-IB-Project` 首尾空白**归一**（`"  p_alpha  "` ≡ `"p_alpha"`）；未知头值全 `is_current=False` 且项目级 `503` |

> **编号更正（R14-DEF-01）**：TC-INT-123 ~ 125 为 GROUP_C 于本文件最初提交的 3 条（原编号 120 ~ 122），因其与 R13 已登记并占用的 `tests/integration/test_accounts_deploy_int_r13.py`（TC-INT-120 nginx TLS 模板 / TC-INT-121 运行时键登记 / TC-INT-122 迁移列级一致，见 §18.2~18.3）**撞号**，本轮更正为 123 ~ 125（**仅改名，断言与计数不变**）。详见 `docs/test_report.md` §19.5。

**（B）前端冒烟层（FE，独立层）—— `src/frontend/tests/frontend.smoke.test.js` 用例 14 ~ 21（层内合计 21）**

| TC-ID | 所属 US | 关联 AC | 级别 | 描述 |
|-------|--------|--------|------|------|
| TC-FE-014 | US-IB-24 | AC-IB-24-03 | FE | 用例 14（结构）：`X-IB-Project` 字面量**只**出现在 `stores/project.ts`（单一取值出口）；`client.ts` 不得含该字面量 |
| TC-FE-015 | US-IB-24 | AC-IB-24-03 | FE | 用例 15（结构）：SSE 调用点（`chatStream`/`chatResume`）同经 `this.headers()`，不重复拼头 |
| TC-FE-016 | US-IB-24 | AC-IB-24-03 | FE | 用例 16（结构）：控制台 `el-select` 选择器 + `<router-view :key>`（切换即重置项目内视图态）+ `env.ts` 接线 |
| TC-FE-017 | US-IB-24 | AC-IB-24-03 | FE | 用例 17（**行为**）：`headers()` 依 `current` 注入 / 不注入（含 SSE 头集合）+ ops `select` 为 no-op |
| TC-FE-018 | US-IB-24 | AC-IB-24-03 | FE | 用例 18（**行为**）：`load` **失败** ⇒ `current=null`、`available=[]`、记录 `error`，**不注入头**（fail-closed） |
| TC-FE-019 | US-IB-24 | AC-IB-24-03 | FE | 用例 19（**行为**）：admin 结果集**恰 1 项** ⇒ **预选**并仍显式发送请求头；`select` 只接受 `available` 中的 id（拒不可见 / 空白） |
| TC-FE-020 | US-IB-24 | AC-IB-24-02 | FE | 用例 20（**行为**）：ops 结果集**为空** ⇒ `current=null`（**不臆造、不注入头**） |
| TC-FE-021 | US-IB-24 | AC-IB-24-03 | FE | 用例 21（**行为**）：项目头值**只**来自 provider（调用点 `extra` 不能覆盖）；provider 抛错 ⇒ 不注入（不炸 `headers()`） |

> **说明**：用例 14 ~ 17 为 GROUP_C 于本文件最初追加的 4 条；本轮（INV-GROUP-D-INTELBASE-014）将其**正式登记**为 TC-FE-014 ~ 017，并**新增** 18 ~ 21（TC-FE-018 ~ 021）。前端层**自立一层、不并入 Python 计数**。

### 19.3 AC ↔ TC 覆盖矩阵（R14）

| AC-ID / 依据 | 覆盖 TC | 结论 |
|-------------|---------|------|
| **AC-IB-24-03**（admin 全局可访问任一项目） | TC-INT-123、TC-INT-124、TC-INT-126、TC-INT-128、TC-FE-014 ~ 019、TC-FE-021 | 覆盖 |
| **AC-IB-24-02**（ops 跨项目 403） | TC-INT-125、TC-INT-127、TC-FE-020 | 覆盖 |
| **REQ-FUNC-IB-31**（账户 : 项目 = 1:1；admin 全局） | TC-INT-125、TC-INT-127 | 覆盖 |
| **REQ-FUNC-IB-23**（多项目隔离 fail-closed） | TC-INT-124、TC-INT-127 | 覆盖 |
| **REQ-FUNC-IB-32**（角色与项目边界） | TC-INT-125、TC-INT-127 | 覆盖 |

- **OPEN ITEM（需求侧缺口，按纪律不发明 AC）**：`architecture_design.md` §10.1 R14 行登记「项目选择 UX + `GET /api/projects`」**无独立 REQ / AC**；在获得新 AC 前，本计划按设计口径**映射到既有 AC**（AC-IB-24-03 / AC-IB-24-02 / REQ-FUNC-IB-31 / REQ-FUNC-IB-23），**未新增 AC**。

### 19.4 不可测试项与残余（R14-L-01 处置）

| 项 | 已覆盖部分 | 残余（未断言） | 处置与理由 |
|----|-----------|---------------|-----------|
| **R14-L-01**：真实浏览器 `el-select` 端到端交互 + `<router-view :key>` 重挂载的**运行期**行为 | **行为层**已真跑：项目头依 `current` 注入/不注入（含 SSE 头集合）、ops 不可切换、`load` 失败/空集 fail-closed、单项目预选（TC-FE-017 ~ 021）；**结构层**已断言选择器与 `:key` 存在（TC-FE-016）；**服务端**已断言越权 `403` 与 `ops` 仅见自身（TC-INT-125/127） | 浏览器内真实点击 `el-select`、下拉展开、切换后组件**真实重挂载**的 DOM 现象 | **接受行为层覆盖**：安全相关不变量（单一注入点、ops 不可切换、fail-closed）已在**模块行为层 + 服务端**双重真跑覆盖，浏览器渲染属前端运行期；按 §5 / §18.4 既有口径，**无自动化浏览器环境**（离线约束），故**登记为 not-verifiable（残余）**，**不引入**浏览器自动化 / 网络依赖。**

### 19.5 门控与度量口径（R14）

- **度量定义**：`total = pass + fail + skip + blocked`（精确等式）；`通过率 = pass / (pass + fail)`（skip / blocked **不计入分母**）。
- **门控**：unit **≥ 80%** → 才可执行 integration；integration **≥ 90%** → 才可执行 e2e；E2E **关键路径 100%**。
- **零 masking 纪律**：**0 skip / 0 xfail / 0 blocked**；未执行不得记 PASS。
- **结论数值**（详见 `docs/test_report.md` §19.1）：unit **95/95 = 100%**、integration **129/129 = 100%**、e2e **21/21 = 100%**（关键路径 100%）；前端 **21/21**（独立层）。

### 19.6 计数基线与算术对账（R14）

- **本轮起始基线（INV-GROUP-D-INTELBASE-014 执行前）**：`python -m pytest tests -q` = **242 passed**（EXIT 0）；分层 unit **95** / integration **126** / e2e **21**（integration 126 **已含** GROUP_C 的 R14 用例 TC-INT-120 ~ 122 共 3 条）；前端冒烟 **17/17**；`selfcheck.py` **47/47**。
- **本轮净增**：integration **+3**（TC-INT-126 ~ 128）→ **129**；前端 **+4**（用例 18 ~ 21）→ **21**；unit / e2e / selfcheck **不变**。
- **编号更正（计数中性）**：TC-INT-120 ~ 122 → **TC-INT-123 ~ 125**（仅改名，不增删用例，**不改变计数**）。
- **本轮后基线**：**245**（unit **95** / integration **129** / e2e **21**）；前端冒烟 **21**（独立层，不计入 245）。
- **算术**：`95 + 129 + 21 = 245` ✓；`129 = 129 + 0 + 0 + 0` ✓。
- **`tests/**` 写权说明（如实登记）**：本轮新增 / 正式化**仅**落在 `tests/integration/test_project_context_int_r14.py` 与 `src/frontend/tests/frontend.smoke.test.js`；**未改** `src/scripts/selfcheck.py`（属 `src/**`，只读）；**未改**任何既有编号（105 ~ 122）与既有断言。

---

## §20 R16-2 增量（REV-16-2：专家提示词主/兜底分层 + 工具授权勾选与工具参数可配 + FreeArk 严格对齐 + 保存即重启生效）

> 触发：**REV-16-2**（专家提示词分层 / 工具参数可配 / FreeArk 硬改名 / 生效口径 = 保存即落盘、重启重装配）。上游 GROUP_C 实现门控 **GR-C-011 = PASS_WITH_CONDITIONS**（0 CRITICAL）。
> 调用 ID：**INV-GROUP_D-INTELBASE-015**。本轮**独立复核 + 补测**：新增 Python **24 条**（unit 14：TC-UNIT-109 ~ 122；integration 7：TC-INT-134 ~ 140；e2e 3：TC-E2E-022 ~ 024）+ 前端 **1 条**（用例 27 / TC-FE-023）。
> 硬约束：**未改 `src/**`**（只读）、**未 commit / push / stage**、**未触网**、FreeArk 仓库**只读**、无 Docker / PyMuPDF、`langchain-openai < 0.3`；测试代码内**无任何真实凭据**（离线令牌为占位替身值）。

### 20.1 测试策略与范围（R16-2）

- **范围（in-scope）**
  - **提示词分层语义（ADR-29 / IFC-IB-343，REQ-FUNC-IB-37/38）**：优先级 `main_file > fallback_file > definition_doc_fallback`；`effective_prompt` **恒非空**（三层皆空 → `PromptNotFoundError`）；`resolved_from` 可观测（供界面回显）。
  - **独立 markdown 目录契约（[ARCH-ASSUMPTION-A10] / IFC-IB-345，ADR-15-R1）**：根键 `IB_EXPERT_PROMPT_DIR`；树 `<root>/<project_id>/<expert_name>/{main.md|fallback.md}`；子目录名 **= 专家 `name`**；`main.md` **可缺**、`fallback.md` **必需**；原子写（tmp + `os.replace`）；`..` 穿越拒绝；孤儿 / 命名不符 / 缺兜底检出；**目录不存在 = 合法空**、**存在但非目录 = `DependencyUnavailableError`**。
  - **工具授权勾选 + 工具参数可配（ADR-30 / IFC-IB-346/350）**：勾选**只作用于既有工具集**（不新增工具本体）；`ToolParamSpec` 由既有工具 JSON Schema **派生**；参数注入经 `functools.partial` 且**调用方显式实参优先**；**跨工具参数名隔离**（限定名 `<tool>.<param>`）；越界 / 类型 / 未知 / 未授权带参 → 拒绝；`param_values` 参与语义哈希与可编辑白名单。
  - **两域装配闸门（ADR-16 / IFC-IB-353）**：`admit(doc, store)` 签名**冻结**；`admit_two_domains` 聚合 `store.validate ∪ validate_prompt_directory ∪ validate_tool_params`，任一非空即拒绝装配；`ValidationReport` **无** `force/ignore/warn_only`。
  - **FreeArk 严格对齐 + 硬改名（ADR-31 / IFC-IB-337~342，REQ-FUNC-IB-42）**：`freeark-expert`（系统管家）/ `inspection-expert`（巡检诊断）/ `sanheng-knowledge`（三恒知识）；旧 slug / 旧 cn_label 在 `src/`、`tests/` **归零**（唯一豁免 = selfcheck 反向断言与编排过渡并集）；`AGGREGATION_FORBIDDEN_LABELS` = **派生只读视图**（结构 ∪ 旧 ∪ 新 ∪ `cn_map`）。
  - **生效口径（ADR-32 / C-IB-40 / REQ-FUNC-IB-40）**：保存 = **原子落盘**；**无**运行期热重载；**不重编译编排图**（`deps.orchestrator_for(p) is deps.orchestrator_for(p)`）；重启后重装配方生效。
  - **前端配置页（IFC-IB-354）**：提示词分层编辑器（主/兜底）、工具授权 checkbox + 工具参数表单（按 `ToolParamSpec` 派生控件）、主缺失 → `resolvedFrom` 显示兜底、「保存成功；重启 `ib-web` / `ib-worker` 后生效」强制文案、**无** reload/hotReload/rebuildGraph 入口。
- **范围（out-of-scope）**：真实浏览器渲染；真实 `ib-web` / `ib-worker` 双进程重启（离线以「新进程视角重装载 + 重装配」模拟，见 §20.4）；FreeArk 仓库写入检测（跨仓只读事实）；真实 Qdrant / DeepSeek / bge-m3（离线）。
- **测试环境**：Python 3.14.6 / pytest 9.1.1 / Django 6.0.6（内存 prompt store + `tmp_path` 文件 store + Django test Client，进程内不触网）；前端 `node --test`（Node v24.18.0）。
- **覆盖率目标（沿用 §6）**：单元 ≥ 80%、集成 ≥ 90%、E2E 关键路径 100%。

### 20.2 测试用例清单（R16-2）

**（A）单元层（UNIT）—— GROUP_C 组 `tests/unit/test_prompt_layers_r16.py`（14 条；**本计划赋号** TC-UNIT-095 ~ 108）**

| TC-ID | 关联 AC | 描述 |
|-------|---------|------|
| TC-UNIT-095 | AC-IB-30-06 | 分层优先级 main>fallback>doc；三层皆空 → `PromptNotFoundError`（`effective_prompt` 恒非空） |
| TC-UNIT-096 | AC-IB-30-02 | `prompt_content_hash` 语义稳定（同内容同哈希） |
| TC-UNIT-097 | AC-IB-33-01 | 目录**不存在** → 合法空（首次运行），非错误 |
| TC-UNIT-098 | AC-IB-33-01 | 孤儿 / 命名不符 / 缺兜底检出 |
| TC-UNIT-099 | AC-IB-33-01 | 子目录名 ≠ 专家 name → `prompt_naming_mismatch` |
| TC-UNIT-100 | AC-IB-30-04 | 保存冲突（错误 `expected_hash`）+ 空兜底拒绝（InMemory 变体） |
| TC-UNIT-101 | AC-IB-30-04 | 保存冲突 + 空兜底拒绝（Fs 变体；参数化） |
| TC-UNIT-102 | AC-IB-33-01 | Fs 原子写 + `layout()` 契约 |
| TC-UNIT-103 | AC-IB-30-04 | 目录穿越 `expert_name` 拒绝 |
| TC-UNIT-104 | AC-IB-31-03 | `validate_tool_params` 五类错误（未知/未授权/枚举/类型/越界） |
| TC-UNIT-105 | AC-IB-31-04 | 规格派生 + 授权绑定 + 范围绑定 + 调用方显式实参优先 |
| TC-UNIT-106 | AC-IB-31-03 | 未登记参数 / 未授权工具带参拒绝 |
| TC-UNIT-107 | AC-IB-34-01 | `derive_prompt_layers` 按专家 name join + 注入 |
| TC-UNIT-108 | AC-IB-30-06 | 无提示词文件 → 退回文档兜底 |

**（B）单元层（UNIT）—— 测试工程师独立补充 `tests/unit/test_prompt_tool_config_unit_r16d.py`（14 条：TC-UNIT-109 ~ 122）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-UNIT-109 | US-IB-34 | AC-IB-34-01/02 | `forbidden_labels(cn_map)` 派生只读视图：过渡并集（旧∪新 5 标签）+ 结构词 + cn_map 取值；去重 / 顺序稳定；兼容常量 = 结构 ∪ 过渡 |
| TC-UNIT-110 | US-IB-30 | AC-IB-30-04 | `ValidationReport` 字段集**恰** `{ok, errors}`（无 force/ignore/warn_only 等绕过字段） |
| TC-UNIT-111 | US-IB-30 | AC-IB-30-04 | `admit` 签名**冻结** `{doc, store}`；`admit_two_domains` 存在且含 `prompt_refs`/`tool_specs` 且无绕过参数 |
| TC-UNIT-112 | US-IB-30/31 | AC-IB-30-04/31-03 | 两域闸门拒绝：孤儿 / 缺兜底 / 未知参数 / 越界 / 未授权带参（逐类断言错误码） |
| TC-UNIT-113 | US-IB-30 | AC-IB-30-06 | 两域闸门合法通过 → 跨域派生视图，生效提示词恒非空（退回文档兜底） |
| TC-UNIT-114 | US-IB-31 | AC-IB-31-04 | **跨工具参数名隔离**：两台工具共享裸 `top_k`，限定名互不串味；调用方显式实参优先；`_bare_param`/`_param_belongs` 直证 |
| TC-UNIT-115 | US-IB-33 | AC-IB-33-01/02 | `prompt_domain_enabled()` 默认开；`false/0/off` 关；`1/true/yes/on` 开 |
| TC-UNIT-116 | US-IB-33 | AC-IB-33-01 | 目录装载：base 存在但**非目录** → `DependencyUnavailableError`；不存在 → 合法空 |
| TC-UNIT-117 | US-IB-33 | AC-IB-33-01 | Fs store **事务性**：冲突不落地、无 `.tmp` 残留、空兜底不改既有文件、成功替换、穿越拒绝 |
| TC-UNIT-118 | US-IB-30/31 | AC-IB-30-02/31-02/31-04 | `param_values` 进语义哈希 + 进可编辑白名单；JSON 往返保真；旧文档（无 `param_values`）向后兼容 |
| TC-UNIT-119 | US-IB-34 | AC-IB-34-01/02/04 | 注册表对齐：names/cn_map/default_expert；旧 slug 彻底消失；`is_data_expert` 语义随名迁移；兜底恒非空 |
| TC-UNIT-120 | US-IB-30 | AC-IB-30-06 | `ref.exists=True` 但文件实际缺失 → 退回文档兜底（`main_prompt=None`） |
| TC-UNIT-121 | US-IB-30 | AC-IB-30-03 | 仅编辑主层，兜底层哈希不变（分层并存不互相覆盖） |
| TC-UNIT-122 | US-IB-34 | AC-IB-34-01/02 | **仓库级证据**：`src/`、`tests/` 中旧 slug / 旧 cn_label 归零（豁免站点 = selfcheck 反向断言 + 编排过渡并集，且豁免非空洞） |

**（C）集成层（INT）—— GROUP_C 组 `tests/integration/test_prompt_config_r16.py`（5 条；**本计划赋号** TC-INT-129 ~ 133）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-INT-129 | US-IB-30 | AC-IB-30-06 | 装配序列注入每项目 prompt store + 跨域派生 bundles；注入 `ib.experts` 全局 |
| TC-INT-130 | US-IB-30/31 | AC-IB-30-05 | `GET /api/config/prompts` 回执契约：`{experts,tool_param_specs,available_tools,layout,config_key_names}`；**只登记键名 / 不出正文 / 不回显令牌** |
| TC-INT-131 | US-IB-30 | AC-IB-30-01/04/06 | 单层 GET/PUT：404 / 200 保存 / 回读一致 / 冲突 409 / 空兜底 400 / 未知专家 404 / 缺令牌 4xx |
| TC-INT-132 | US-IB-30 | AC-IB-30-04 | 端点族**不接受** `?token=`（中间件先行拒绝） |
| TC-INT-133 | US-IB-32 | AC-IB-32-01/03 | 保存**不重建编排图**（`orchestrator_for` 同一实例，ADR-32 / C-IB-40） |

**（D）集成层（INT）—— 测试工程师独立补充 `tests/integration/test_prompt_tool_config_int_r16d.py`（7 条：TC-INT-134 ~ 140）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-INT-134 | US-IB-33 | AC-IB-33-02 | `IB_VISUAL_CONFIG_ENABLED=false` → 提示词端点族**整体 404**（明确 not_found，不静默成功） |
| TC-INT-135 | US-IB-30 | AC-IB-30-01/02/06 | 仅存兜底层 → 列表 `main.exists=False`、`fallback.exists=True`；单层读主 404 / 兜底 200 + 正文；派生生效提示词恒非空 |
| TC-INT-136 | US-IB-31 | AC-IB-31-01/04 | **唯一登记点**同源：`known_tool_names()==('search_knowledge',)`、`known_tool_param_specs()` 与端点回执一致 |
| TC-INT-137 | US-IB-30/31 | AC-IB-30-04/31-03 | 真实 deps 上 `admit_two_domains`：非法参数拒绝（`tool_param_unknown`）；合法文档通过并派生 |
| TC-INT-138 | US-IB-31 | AC-IB-31-03 | 定义文档保存拒绝「引用不存在的工具」（400 `tool_grant_tool_unknown`）且**既有在用配置逐位不变** |
| **TC-INT-139** | US-IB-30 | **AC-IB-30-04** | **[DEFECT-R16-02，如实失败]** 保存非法工具参数应 400 且既有配置不变 —— 实测 200 且配置被改写 |
| **TC-INT-140** | US-IB-31 | **AC-IB-31-02/31-04** | **[DEFECT-R16-01，如实失败]** 定义文档 GET 应回读 `tool_grants[].param_values`（往返不丢参）—— 实测字段缺失 |

**（E）E2E 关键路径（E2E）—— 测试工程师独立补充 `tests/e2e/test_config_restart_effect_r16.py`（3 条：TC-E2E-022 ~ 024）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-E2E-022 | US-IB-32/33 | AC-IB-32-01/03 + 33-01/03 | HTTP 保存主提示词（Fs 原子落盘）→ 保存不重建图 → 「重启」新 store 读盘 + 重装载 + 重装配 → 新配置生效（`resolved_from=main_file`） |
| TC-E2E-023 | US-IB-31/30 | AC-IB-31-03 + 30-04 | 提交越界工具授权 → 400 且既有配置不变；装配期闸门**类型层无绕过**（签名冻结） |
| TC-E2E-024 | US-IB-34 | AC-IB-34-01/02/04 | demo 示例项目默认专家集与 FreeArk 严格对齐（专家名 + cn_label + 工具名）；端点回执与注册表同源；`config.example.json` 锚点 = `demo` |

**（F）前端冒烟层（FE，独立层）—— `src/frontend/tests/frontend.smoke.test.js` 用例 22 ~ 27（层内合计 27）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-FE-020* | US-IB-30 | AC-IB-30-01/06 | 用例 22（结构）：分层编辑器（`PROMPT_LAYERS` / `savePromptLayer`）+ `resolvedFrom()` + 回退可见文案「主提示词缺失，当前生效 = 兜底」 |
| TC-FE-021* | US-IB-32 | AC-IB-32-03 | 用例 23（结构）：强制文案「保存成功；重启 `ib-web` / `ib-worker` 后生效」+「不热重载」+ 无 reload/hotReload/rebuildGraph |
| TC-FE-022** | US-IB-31 | AC-IB-31-01/04 | 用例 24（结构）：`grantChecklist` / `toggleTool` / `paramsForTool` + `available_tools: string[]` 类型契约 |
| （用例 25 / 26） | US-IB-30 | AC-IB-30-02 | 提示词域独立草稿 / 哈希（`promptHashes`/`promptTexts`/409）；视图零 `localStorage`/`IndexedDB` |
| **TC-FE-023** | US-IB-31 | AC-IB-31-04 | 用例 27（**本代理新增**）：工具参数表单由 `tool_param_specs` 派生（`spec.minimum/maximum/choices`）+ 限定名 `startsWith(\`${tool}.\`)` 过滤 + 写入 `grant.param_values` + 白名单 `canEdit('tool_grants[].param_values')` + 客户端类型 `tool_param_specs` / `param_values?` |

> \* 用例 22 / 23 为 GROUP_C 于 `frontend.smoke.test.js` 追加的 R16 结构断言，本计划正式登记。
> \** 前端层**自立一层、不并入 Python 计数**；编号沿用「用例号」并另行给出 TC-FE 编号。

### 20.3 AC ↔ TC 覆盖矩阵（R16-2；逐 US 逐 AC）

| US | AC-ID | 覆盖 TC | 结论 |
|----|-------|---------|------|
| US-IB-30 | AC-IB-30-01（编辑保存被接受） | TC-INT-131、TC-INT-135、TC-FE-020 | 覆盖 |
| US-IB-30 | AC-IB-30-02（重新读取一致，写单一真源） | TC-INT-131、TC-INT-135、TC-UNIT-096、TC-UNIT-118 | 覆盖 |
| US-IB-30 | AC-IB-30-03（主/兜底分层并存，不互相覆盖） | TC-UNIT-121 | 覆盖 |
| US-IB-30 | AC-IB-30-04（保存不合法被拒 + 既有配置不变） | TC-UNIT-110/111/112/117、TC-INT-131/137/138、TC-INT-139（**缺陷**） | **部分覆盖（缺陷）** |
| US-IB-30 | AC-IB-30-05（页面与文档同源，无第二真源） | TC-INT-130、TC-E2E-024 | 覆盖 |
| US-IB-30 | AC-IB-30-06（主缺失回退兜底不空） | TC-UNIT-095/108/113/120、TC-INT-129/135、TC-E2E-022、TC-FE-020 | 覆盖 |
| US-IB-31 | AC-IB-31-01（勾选保存被接受） | TC-INT-131、TC-INT-136、TC-FE-022 | 覆盖 |
| US-IB-31 | AC-IB-31-02（重新读取一致） | TC-UNIT-118、TC-INT-140（**缺陷**） | **部分覆盖（缺陷）** |
| US-IB-31 | AC-IB-31-03（越界/不存在工具拒绝 + 既有配置不变） | TC-UNIT-104/106/112、TC-INT-131/137/138、TC-E2E-023 | 覆盖 |
| US-IB-31 | AC-IB-31-04（工具参数随授权一并保存） | TC-UNIT-105/114/118、TC-INT-136、TC-FE-022 | 覆盖 |
| US-IB-32 | AC-IB-32-01（未重启用旧配置） | TC-INT-133、TC-E2E-022（②同一实例） | 覆盖 |
| US-IB-32 | AC-IB-32-02（生效记录可查询：谁/何时/改了哪些字段/结果） | — | **未覆盖（GAP-R16-04）** |
| US-IB-32 | AC-IB-32-03（重启后使用新配置） | TC-INT-133、TC-E2E-022（③） | 覆盖 |
| US-IB-32 | AC-IB-32-04（保存失败 → 既有配置，fail-safe） | TC-INT-138、TC-E2E-023 | 覆盖 |
| US-IB-32 | AC-IB-32-05（ib-web / ib-worker 双进程重启均生效） | — | **离线不可验证（见 §20.4）** |
| US-IB-33 | AC-IB-33-01（已启用 → 写入文件持久保留） | TC-UNIT-097/098/099/102/116/117、TC-E2E-022（①落盘） | 覆盖 |
| US-IB-33 | AC-IB-33-02（未启用 → 明确提示仅内存 / 不跨重启 / 项目级作用域） | TC-INT-134（部分：端点族关闭语义） | **部分覆盖（GAP-R16-03）** |
| US-IB-33 | AC-IB-33-03（重启后配置不变） | TC-E2E-022（③新 store 读盘） | 覆盖 |
| US-IB-34 | AC-IB-34-01（逐字段严格一致，含 name/cn_label） | TC-UNIT-109/119/122、TC-E2E-024 | 覆盖 |
| US-IB-34 | AC-IB-34-02（100% 对齐核验，工具名对齐） | TC-UNIT-109/119/122、TC-E2E-024 | 覆盖 |
| US-IB-34 | AC-IB-34-03（FreeArk 未被修改，只读） | — | **离线不可验证（见 §20.4）** |
| US-IB-34 | AC-IB-34-04（示例项目 = demo，默认专家集） | TC-E2E-024 | 覆盖 |

- **结论**：US-IB-30 ~ US-IB-34 **全部有覆盖**；其中 2 个 AC（AC-IB-30-04 / AC-IB-31-02）因 **DEFECT-R16-01 / R16-02** 判为「部分覆盖（缺陷）」，2 个 AC（AC-IB-32-02 / AC-IB-33-02）**实现缺失**（GAP-R16-03 / R16-04），1 个 AC（AC-IB-32-05）与 AC-IB-34-03 **离线不可验证**。

### 20.4 不可测试项与覆盖缺口（R16-2）

| 项 | 已覆盖部分 | 残余（未断言） | 处置与理由 |
|----|-----------|---------------|-----------|
| **AC-IB-32-05**：`ib-web` / `ib-worker` 两进程手工重启后均用新配置 | **单进程「重启 = 重装配」语义**已真跑（TC-E2E-022 ③）；持久化载体两进程**共享同一文件目录**（FsExpertPromptStore 无进程私有态）已在 TC-UNIT-117 / TC-E2E-022 覆盖 | 真实两进程编排（systemd 重启顺序、worker 侧装配） | **离线不可验证**：无进程编排环境（离线约束）；按 §5 口径登记，**不引入**进程级自动化依赖。 |
| **AC-IB-34-03**：FreeArk 仓库未被修改（全程只读） | `src/` / `tests/` 内旧标识归零（TC-UNIT-122、TC-E2E-024）间接佐证「比对未反写本仓」 | 跨仓只读事实（FreeArk 文件 mtime / 哈希未变） | **离线不可验证**（参考仓为外部只读路径，本代理仅只读访问，不写入、不留痕）。 |
| **AC-IB-32-02**：生效记录「可查询」（谁 / 何时 / 改了哪些字段 / 结果） | `log_event("definition_config","saved",project_id=…)` 写日志（非查询接口，且不含 actor / 变更字段） | 任何**可查询**的变更记录接口 / 结构 | **GAP-R16-04（实现缺失）**：全仓 grep 未发现配置变更历史接口 / 结构；**不虚构接口**去断言 —— 登记为缺口，路由 PM / developer。 |
| **AC-IB-33-02**：未启用 `IB_DEFINITION_DOC_PATH` → **明确提示**「配置仅内存生效、不跨重启保留」 | `IB_VISUAL_CONFIG_ENABLED` 关闭时端点族 404 语义（TC-INT-134） | 用户可见的「仅内存 / 不跨重启」文案（后端回执或前端页面） | **GAP-R16-03（实现缺失）**：全仓 grep 未发现该文案（`src/**`、前端视图均无）；**不虚构字段名**去断言 —— 登记为缺口，路由 PM / developer。 |

### 20.5 门控与度量口径（R16-2）

- **度量定义**：`total = pass + fail + skip + blocked`（精确等式）；`通过率 = pass / (pass + fail)`（skip / blocked **不计入分母**）。
- **门控**：unit **≥ 80%** → 才可执行 integration；integration **≥ 90%** → 才可执行 e2e；E2E **关键路径 100%**。
- **零 masking 纪律**：**0 skip / 0 xfail / 0 blocked**；未执行不得记 PASS。
- **结论数值**（详见 `docs/test_report.md` §20）：
  - unit **132 / 132 = 100.0%**（阈值 80%）→ **PASSED**
  - integration **139 / 141 = 98.58%**（阈值 90%）→ **PASSED**（2 条如实失败 = DEFECT-R16-01 / R16-02）
  - e2e **24 / 24 = 100%**；关键路径（Must Have：US-IB-30 ~ 34）**100%**
  - 前端冒烟 **27 / 27**（独立层）
  - 合计 **295 / 297 passed**（297 = 132 unit + 141 integration + 24 e2e）

### 20.6 计数基线与算术对账（R16-2）

- **本轮起始基线（INV-GROUP-D-INTELBASE-015 执行前，即 GROUP_C R16 落地后）**：`python -m pytest tests -q` = **273 passed**（unit **118** / integration **134** / e2e **21**）；`selfcheck.py` **50/50**；前端冒烟 **26/26**；`vue-tsc --noEmit` EXIT 0。
- **本轮净增**：unit **+14**（TC-UNIT-109 ~ 122）→ **132**；integration **+7**（TC-INT-134 ~ 140）→ **141**；e2e **+3**（TC-E2E-022 ~ 024）→ **24**；前端 **+1**（用例 27）→ **27**；`selfcheck.py` **不变（50/50）**。
- **本轮后基线**：**297**（unit **132** / integration **141** / e2e **24**）；前端冒烟 **27**（独立层，不计入 297）。
- **算术**：`132 + 141 + 24 = 297` ✓；`141 = 139 + 2 + 0 + 0` ✓；`132 = 132 + 0 + 0 + 0` ✓；`24 = 24 + 0 + 0 + 0` ✓。
- **对账观察（如实登记，非本轮引入）**：§19 登记 R14 后基线为 **245**（unit 95 / integration 129 / e2e 21），但**实测 R16 起始前**为 **254**（273 − GROUP_C R16 的 19 条）—— 差值 **+9** 落在 **R15 增量**（`test_stream_session_lifecycle_*_r11/r12.py` 等由 developer 侧提交、未经 GROUP_D 计划登记）的 unit/integration 用例，**非本轮计数错误**；建议 PM 在流程上补登 R15 增量的 TC 编号。
- **`tests/**` 写权说明（如实登记）**：本轮新增**仅**落在 `tests/unit/test_prompt_tool_config_unit_r16d.py`、`tests/integration/test_prompt_tool_config_int_r16d.py`、`tests/e2e/test_config_restart_effect_r16.py` 与 `src/frontend/tests/frontend.smoke.test.js`（用例 27）；**未改** `src/**`（含 `src/scripts/selfcheck.py`，只读）；**未改**任何既有编号（UNIT 095 ~ 108 / INT 129 ~ 133 为**赋号**，不改 GROUP_C 代码）。

### 20.7 缺陷登记（路由 software-developer）

| ID | 严重度 | 关联 AC | 证据 TC | 说明 |
|----|--------|---------|---------|------|
| **DEFECT-R16-01** | MAJOR | AC-IB-31-02 / 31-04 | TC-INT-140（失败） | `src/ibweb/serializers.py:195-196` `_ToolGrantSpecSerializer._fields = {"expert_name","tool_names"}` **遗漏 `param_values`** → `GET /api/config/definition` 不回读工具参数；「GET 草稿 → PUT 保存」一次往返即**静默清空**已配置参数（界面无法回显 / 无法保留） |
| **DEFECT-R16-02** | MAJOR | AC-IB-30-04 | TC-INT-139（失败） | 定义文档保存路径仅调 `store.validate`（校验工具名，**不校验工具参数**）；`validate_tool_params` 只在装配期（`admit_two_domains`）生效 → 非法参数保存**返回 200 且改写既有配置**，直至下次重启装配才拒绝（**违背 fail-safe**：配置被写入「下次装配必失败」的状态） |
| **GAP-R16-03** | MAJOR | AC-IB-33-02 | 无（未实现） | 「配置仅内存生效、不跨重启保留」明确提示在 `src/**` 与前端视图**均不存在**（全仓 grep 为空）；`IB_DEFINITION_DOC_PATH` 未配置时用户无任何提示 |
| **GAP-R16-04** | MAJOR | AC-IB-32-02 | 无（未实现） | 无**可查询**的配置生效记录（变更历史）接口 / 结构；`log_event` 仅写日志且不含「谁 / 改了哪些字段」 |

> **修复边界**：上表缺陷的修复属 **software-developer** 职责；本代理**只报告、不改 `src/`**。修复后须由 GROUP_D 复跑 `TC-INT-139` / `TC-INT-140` 并复核 `config.example.json` / 文案注入点。

---

## §21 R16-4 增量（REV-16-4：DEFECT-R16-01 / R16-02 修复 + GAP-R16-03 / R16-04 落地；独立复跑与阶段门控）

> 触发：**REV-16-4** —— R16-2 登记的 2 个 MAJOR 实现缺陷（DEFECT-R16-01 / R16-02）**已修复**、2 个 MAJOR 覆盖缺口（GAP-R16-03 / R16-04）**已实现**；本轮为 GROUP_D **整套复跑 + 强制负例 + 覆盖率回补**。
> 调用 ID：**INV-GROUP_D-INTELBASE-016**（R16-4 增量首跑）+ **INV-GROUP_D-INTELBASE-017**（**DEFECT-R16-4-01 修复后的整套复跑**，本节最终数值以此为准）。上游门控：GR-A-009 = PASS、GR-B-009 = PASS、GR-C-012 = PASS_WITH_CONDITIONS。
> 硬约束：**未改 `src/**`**（只读）；**未 commit / push / deploy**（PHASE_11 冻结）；FreeArk 只读；未触网；无 Docker / PyMuPDF；`langchain-openai < 0.3`；测试代码内无真实凭据（离线令牌为占位值）。

### 21.1 本轮覆盖的四处变更（逐条溯源）

| # | 变更（REV-16-4） | 关联 AC | 覆盖用例 |
|---|-----------------|---------|---------|
| 1 | **DEFECT-R16-01 修复**：`src/ibweb/serializers.py::_ToolGrantSpecSerializer` 手写 `to_representation`，保留 `param_values`（保序 `[{"name","value"},…]`） | AC-IB-31-02 / 31-04 | TC-INT-140（R16-2 缺陷用例，**本轮 PASS**）、TC-INT-141 |
| 2 | **DEFECT-R16-02 修复**：新增合成纯函数 `validate_definition_full`（IFC-IB-355 = IFC-IB-290 ∪ IFC-IB-346），保存路径（`views.py`）与装配路径（`composition.py::admit_two_domains`）**共用同一校验入口** → 非法工具参数保存 **400** 且在用配置**逐位不变**（fail-safe） | AC-IB-30-04 | TC-INT-139（R16-2 缺陷用例，**本轮 PASS**）、**TC-INT-141（强制负例）**、TC-INT-146、TC-UNIT-123 |
| 3 | **GAP-R16-03 实现**：`StorageState`（IFC-IB-361）+ `GET /api/config/storage-state`（IFC-IB-362）+ 前端非静默提示「配置仅内存生效、不跨重启保留」（IFC-IB-363） | AC-IB-33-02 | TC-INT-142、TC-UNIT-126、**TC-FE-024**（源码结构层；前端渲染期子句见 §21.7） |
| 4 | **GAP-R16-04 实现**：`ConfigAuditEntry`（IFC-IB-356）+ 端口 `ConfigAuditStore`（IFC-IB-357，**恰** `record` / `list_by_project`，无 update / delete）+ `SqliteConfigAuditStore`（IFC-IB-358）+ 迁移 `004_config_audit.sql` + `record_config_audit`（IFC-IB-360）+ `GET /api/config/audit`（IFC-IB-359） | AC-IB-32-02 | TC-INT-143 / 144 / 145、TC-UNIT-124 / 125 |

### 21.2 测试用例清单（R16-4 新增；本代理独立编写）

**（A）单元层（UNIT）—— `tests/unit/test_config_audit_rev16_4_unit.py`（4 条：TC-UNIT-123 ~ 126）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| TC-UNIT-123 | US-IB-30 | AC-IB-30-04 | `validate_definition_full` = 定义文档域 ∪ 工具参数域，**固定顺序**合并；纯函数（无 I/O）；`ValidationReport` 字段集恰 `{ok, errors}`（ADR-16 无旁路） |
| TC-UNIT-124 | US-IB-32 | AC-IB-32-02 | 审计存储 Memory / Sqlite 两实现语义对齐：**只追加**、按项目过滤、稳定升序、`limit` / `offset` 分页；`changed_field_names` / `detail_code` 保真 |
| TC-UNIT-125 | US-IB-32 | AC-IB-32-02 | 端口 / 实现**类型层无** `update` / `delete`；`ConfigAuditEntry` 字段集不含任何承载「取值 / 凭据」的字段（SC-3） |
| TC-UNIT-126 | US-IB-33 | AC-IB-33-02 | `StorageState` 取值域 `{memory,file}` + 字段集；离线装配 = memory/memory 且两键均未配置（= 「仅内存生效、不跨重启保留」） |

**（B）集成层（INT）—— `tests/integration/test_config_rev16_4_int.py`（7 条：TC-INT-141 ~ 147）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| **TC-INT-141** | US-IB-30 | **AC-IB-30-04** | **[强制负例 / fail-safe]** 携带**非法工具参数**的 PUT → **400**；且**随后 GET** 同一配置读回**保存前**取值（在用配置未被半写入覆盖）；对照：合法参数 PUT → 200 |
| TC-INT-142 | US-IB-33 | AC-IB-33-02 | `GET /api/config/storage-state` → 200，**字段白名单**恰四键、不回显任何键值 / 路径；离线 = memory/memory + 未配置；与装配结果直读一致 |
| TC-INT-143 | US-IB-32 | AC-IB-32-02 | `GET /api/config/audit` 记录**成功**保存：`result=saved`、含「谁 / 何时 / 改了哪些字段」、字段白名单、**不回显任何取值** |
| TC-INT-144 | US-IB-32 | AC-IB-32-02 | 审计记录**失败**保存：`result=rejected`、`detail_code` 只含错误码（如 `tool_grant_tool_unknown`） |
| TC-INT-145 | US-IB-32 | AC-IB-32-02 | 只读纪律：端口类型层无 update / delete；两端点仅 GET（POST → 405）；不接受 `?token=`（→ 400，IC-IB-01） |
| TC-INT-146 | US-IB-30/31 | AC-IB-30-04 / 31-03 | **单一校验入口**：同一非法工具参数文档，保存路径（400 `tool_param_unknown`）与装配路径（`admit_two_domains` 同码）判据一致 |
| **TC-INT-147** | US-IB-32 | **AC-IB-32-02 / 32-04** | **[DEFECT-R16-4-01 已修复闭合 —— 复跑 INV-017 PASS]** 审计写失败**非致命**契约（`record_config_audit`「永不抛、发 WARN」）：首跑（INV-016）在「审计存储缺失」与「审计存储写错」两情形均抛 `NameError`（如实失败）；**software-developer INV-GROUP_C-INTELBASE-017 修复后复跑 PASS** |

**（C）前端冒烟层（FE，独立层）—— `src/frontend/tests/frontend.smoke.test.js` 用例 28（层内合计 28）**

| TC-ID | 所属 US | 关联 AC | 描述 |
|-------|--------|--------|------|
| **TC-FE-024** | US-IB-33 | AC-IB-33-02 | 用例 28（**本代理新增，源码结构层**）：`ConfigPage.vue` 含 `loadStorageState(` / `storageState()` / `memoryNotice` / `memoryDomains`，显式渲染**非静默**文案 `配置**仅内存生效、不跨重启保留**`，存储态读取失败走 `storageBanner`（不静默当作文件态），且视图**不引入** `reload` / `hotReload` / `rebuildGraph` / `scheduleRebuild` 热重载入口；`client.ts` 声明 `StorageState` 类型与 `storageState(): Promise<StorageState>`（路由 `/api/config/storage-state`）、`ConfigAuditEntry` 类型与 `configAudit()` 契约（IFC-IB-361 / 362 / 356 / 359） |

### 21.3 AC ↔ TC 覆盖矩阵（R16-4；仅列受影响 AC）

| US | AC-ID | R16-2 结论 | R16-4 结论 | 覆盖 TC（R16-4 后） |
|----|-------|-----------|-----------|--------------------|
| US-IB-30 | AC-IB-30-04（保存不合法被拒 + 既有配置不变） | 部分覆盖（缺陷） | **覆盖（完整）** —— DEFECT-R16-02 已修复 | TC-UNIT-110/111/112/123/117、TC-INT-131/137/138/**139**/**141**/**146** |
| US-IB-31 | AC-IB-31-02（重新读取一致） | 部分覆盖（缺陷） | **覆盖（完整）** —— DEFECT-R16-01 已修复 | TC-UNIT-118、TC-INT-**140** |
| US-IB-31 | AC-IB-31-04（工具参数随授权一并保存） | 覆盖 | **覆盖（完整）** | TC-UNIT-105/114/118、TC-INT-136、TC-FE-022、TC-INT-**140**/**141** |
| US-IB-32 | AC-IB-32-02（生效记录可查询：谁/何时/改了哪些字段/结果） | **未覆盖（GAP-R16-04）** | **覆盖（GAP-R16-04 已实现）**；残余见 §21.6 | TC-UNIT-**124**/**125**、TC-INT-**143**/**144**/**145** |
| US-IB-33 | AC-IB-33-02（未启用 → 明确提示仅内存 / 不跨重启 / 项目级作用域） | 部分覆盖（GAP-R16-03） | **覆盖（GAP-R16-03 已实现）**；前端渲染期残余见 §21.7 | TC-INT-134、TC-INT-**142**、TC-UNIT-**126**、**TC-FE-024** |

- **结论**：R16-2 的 2 个「部分覆盖（缺陷）」AC **转为完整覆盖**；2 个「未覆盖 / 部分覆盖（缺口）」AC **转为覆盖**。新增 **12** 条用例（unit 4 / integration 7 / 前端 1）；首跑 **11 PASS / 1 FAIL（DEFECT-R16-4-01 如实失败）**，**复跑（INV-017）后 12 PASS / 0 FAIL（缺陷闭合）**。

### 21.4 覆盖率目标与门控（沿用 §6，**未降低阈值**）

| 级别 | 门控阈值 | 说明 |
|------|---------|------|
| 单元测试 | 通过率 ≥ **80%** 方可进入集成测试 | 通过率 = `pass / (pass + fail)`，skip / blocked 不计入分母 |
| 集成测试 | 通过率 ≥ **90%** 方可进入 E2E 测试 | 同上 |
| E2E / 关键路径 | 关键路径（Must Have US）覆盖率 **100%** | 关键路径 US-IB-30 ~ 34 及其他 Must Have |

**零 masking 纪律**：**0 skip / 0 xfail / 0 blocked**；未执行不得记 PASS；失败**不得**转 skip / xfail。PM 未在本轮 `special_instructions` 中覆盖阈值，故采用默认值。

### 21.5 门控与度量口径（R16-4）

- **度量定义**：`total = pass + fail + skip + blocked`（精确等式）；`通过率 = pass / (pass + fail)`。
- **结论数值**（详见 `docs/test_report.md` §21；**复跑 INV-017 口径**）：
  - unit **136 / 136 = 100.0%**（阈值 80%）→ **PASSED**
  - integration **148 / 148 = 100.0%**（阈值 90%）→ **PASSED**（首跑 147 / 148 = 99.32% 含 1 条如实失败 = DEFECT-R16-4-01；修复后复跑全绿）
  - e2e **24 / 24 = 100%**；关键路径 **100%**
  - 前端冒烟 **28 / 28**（独立层，含 **TC-FE-024**）；`vue-tsc` EXIT 0
  - 合计 **308 / 308 passed**（308 = 136 unit + 148 integration + 24 e2e；**0 fail / 0 skip / 0 blocked**，EXIT 0）

### 21.6 计数基线与算术对账（R16-4）

- **本轮起始基线（INV-GROUP_D-INTELBASE-016 执行前，即 REV-16-4 落地后）**：`python -m pytest tests -q` = **297 passed**（unit **132** / integration **141** / e2e **24**）—— R16-2 的 2 条缺陷用例 **已全部转 PASS**；前端冒烟 **27/27**；`selfcheck.py` **50/50**；`compileall` EXIT 0；`vue-tsc` EXIT 0。
- **本轮净增**：unit **+4**（TC-UNIT-123 ~ 126）→ **136**；integration **+7**（TC-INT-141 ~ 147）→ **148**；e2e **±0** → **24**；前端 **+1**（TC-FE-024）→ **28**；`selfcheck.py` **不变（50/50）**。
- **本轮后基线**：**308**（unit **136** / integration **148** / e2e **24**）；前端冒烟 **28**（独立层，不计入 308）。
- **算术（复跑 INV-017 口径）**：`136 + 148 + 24 = 308` ✓；`136 = 136 + 0 + 0 + 0` ✓；`148 = 148 + 0 + 0 + 0` ✓；`24 = 24 + 0 + 0 + 0` ✓。（首跑 INV-016 为 `148 = 147 + 1 + 0 + 0`，唯一 FAIL = TC-INT-147。）
- **回归判定**：R16-2 既有 **297** 条 + R16-4 新增 **11** 条在复跑中**零失败**（**308 / 308 全 PASS，0 回归**）；首跑唯一 FAIL（本轮新增 TC-INT-147）**已由 INV-GROUP_C-INTELBASE-017 修复并复跑闭合**。
- **`tests/**` 写权说明（如实登记）**：本轮新增**仅**落在 `tests/unit/test_config_audit_rev16_4_unit.py`、`tests/integration/test_config_rev16_4_int.py` 与 `src/frontend/tests/frontend.smoke.test.js`（追加用例 28 / TC-FE-024，既有 27 例未改）；**未改** `src/**`（只读）；**未改**任何既有 Python 编号或用例。

### 21.7 不可测试项与残余（R16-4）

| 项 | 已覆盖部分 | 残余（未断言） | 处置与理由 |
|----|-----------|---------------|-----------|
| **AC-IB-33-02** 前端**渲染期**文案子句 | 服务端 `StorageState`（TC-INT-142 / TC-UNIT-126）+ 前端源码结构断言（**TC-FE-024**：`StorageState` 类型 / `storageState()` 客户端方法 / `memoryDomains` / 非静默文案 / `storageBanner` fail-closed / 无热重载入口） | 真实浏览器挂载后**实际渲染**的通知文案 | **离线不可验证**：无浏览器运行环境（同 §5 既有口径），登记为残余。 |
| **AC-IB-32-02** 审计**跨进程重启**持久性 | `SqliteConfigAuditStore` 的写入 / 回放（TC-UNIT-124，真实 `tmp_path` SQLite）；迁移 `004` 的 DDL 单源 | `ib-web` / `ib-worker` 双进程重启后的实际可查询性 | **离线不可验证**（无进程编排）；以 `ensure_schema` 幂等建表 + store 单测为准。 |
| **AC-IB-32-05 / AC-IB-34-03** | 同 §20.4 | 同 §20.4（双进程重启 / 跨仓只读事实） | **离线不可验证**（不变）。 |

### 21.8 缺陷登记（路由 software-developer）

| ID | 严重度 | 关联 AC | 证据 TC | 说明 |
|----|--------|---------|---------|------|
| ~~DEFECT-R16-4-01~~ | MAJOR → **CLOSED** | AC-IB-32-02 / 32-04 | TC-INT-147（首跑如实失败 → **复跑 INV-017 PASS**） | 首跑（INV-016）：`src/ibweb/composition.py::_warn_audit_write_failed`（:968）引用模块级 `log_event`，而 `log_event` 在本模块**仅**以函数内局部导入引入（:449 / :1130）→ 调用即 `NameError`。后果：**「审计写失败非致命但不静默（发 `WARN config_audit_write_failed`）」的 ADR-34 / IFC-IB-360 契约未被满足** —— 当 `deps.config_audit_store is None` 或 `store.record(...)` 抛错时，`record_config_audit` **不返回**而是抛 `NameError`，逸出至保存路径 `_put_definition_config`（:990）后无捕获 → **已成功落盘的保存会向客户端回 500**。**修复（software-developer INV-GROUP_C-INTELBASE-017）**：`_warn_audit_write_failed` 改函数内局部导入 `log_event` + 整段 `try/except Exception: pass` 兜底。**本代理复跑（INV-GROUP_D-INTELBASE-017）确认 TC-INT-147 PASS → 缺陷闭合。** |

> **复核边界（已完成）**：DEFECT-R16-4-01 已由 software-developer 修复，并由 GROUP_D 经 **INV-GROUP_D-INTELBASE-017** 复跑 **TC-INT-147**（FAIL → PASS）确认闭合，`docs/test_report.md` §21 已回填。其余 REV-16-4 变更已由本轮用例覆盖且全绿（**308 / 308**）。

---

## §22 REV-17 增量（提示词兜底层重定位：测试规划；追加，不改写 §1~§21）

**设计侧口径**：`docs/architecture_design.md` **1.9.0/REV-17**（ADR-36 / ADR-15-R2 / §2.0.8）+ `docs/module_design.md` **1.9.0/REV-17**（IFC-IB-364 / IFC-IB-365 / §2.2.8）。**触发输入** = 用户 2026-10-07 请求与七项裁决（见 `docs/phase_status.md` 审计日志 REV-17 条）；`docs/implementation_plan.md` **2.12.0/REV-17** §24。

### 22.1 测试目标（本轮三条，都是「此前没有覆盖面」的）

| # | 目标 | 为何此前无覆盖面 |
|---|------|------------------|
| T1 | **system 位真的生效**：合并后的生效提示词必须进 `build_expert(system_prompt=...)`，human 位只留用户问题本身 | 此前它被拼进 human 前缀，system 位恒为代码内置兜底 —— **配置页编辑的 markdown 主提示词从未成为系统提示**，且没有任何用例断言过 system 位的内容 |
| T2 | **兜底恒非空由结构保证**：`main.md` / `fallback.md` 两层皆缺时回落 `BUILTIN_FALLBACK_DEFAULT`；且新专家（不在 `_DEFAULT_SPECS`）也能保存并装配 | 旧口径下这条路是死的（保存期缺兜底 400；写文件 404），故不存在「新增专家」的用例 |
| T3 | **保存期 ↔ 装配期同一校验入口**：同一份非法文档，两条路径回执**逐条同序、同码、同路径** | 提示词域此前**只在装配期**查，故「页面上存得下、重启装配才炸」是可能的（ADR-33 的漏洞），无对拍用例 |

**另附两条只读契约断言**：`GET /api/config/prompts` 每位专家带只读 `builtin_fallback` 且**顶层键集不变**（5 键）；写入口仍**只有** `main` / `fallback` 两层（不存在写内置兜底的端点）。

### 22.2 用例规划（三层归属 + 覆盖目标）

| 层 | 文件 | 用例数 | 覆盖 |
|----|------|--------|------|
| unit | `tests/unit/test_prompt_system_slot_r17.py`（**新建**） | **13** | T1（system 位 / 空串与空白回落 / 裸 client 防护）、T2（内置兜底全函数性 / 上界断言）、legacy 键分级处置、`_clients` 上界 = 专家数 + 3、定义文档不再要求兜底字段、离线替身无 `IB_DEFINITION_DOC_PATH` |
| integration | `tests/integration/test_prompt_config_r17_int.py`（**新建**） | **6** | T3（对拍同序同条 / fail-safe 不半写）、T2（新专家保存 + 装配 + `resolved_from == builtin_fallback`）、反证（孤儿文件仍拒）、只读回显契约、写入口纪律 |
| 前端冒烟 | `src/frontend/tests/frontend.smoke.test.js`（**追加 1 例**） | **+1（28 → 29）** | 定义文档域不再有提示词编辑入口；内置兜底只读回显（正文来自后端回执、控件 `readonly`）；回退链第三值 `builtin_fallback`；`client.ts` 契约（删 `fallback_prompt`、增 `builtin_fallback`） |
| 自检 | `src/scripts/selfcheck.py`（**追加 1 项**） | **50/50 → 51/51** | `r17_build_expert_system_slot`：`build_expert` 签名含 keyword-only `system_prompt`（**防契约漂移被静默降级掩盖**）+ system 位真的生效 |

**强制纪律（沿用既有）**：不得调低阈值、不得把失败改写成 skip 或 xfail；必须同时有**正向**（新专家可存可装）与**反向**（越域仍拒、非法文档不半写、孤儿文件不进配置）用例。

### 22.3 通过标准（沿用 REQ-NFR + 门控）

| 层 | 门槛 | 本轮实测 |
|----|------|----------|
| unit | ≥ 80% | **149/149 = 100%** |
| integration | ≥ 90% | **154/154 = 100%** |
| e2e 关键路径 | 100% | **24/24 = 100%** |
| 前端冒烟（独立层） | 全绿 | **29/29** |
| 自检 | 全通过 | **51/51** |
| 回归 | 基线零回退 | **REV-16-4 基线 308 → 327，零回归** |

**算术自洽**：149 + 154 + 24 = **327**（前端 29 为独立层，不并入 327）。**零 skip / 零 xfail / 零 blocked**。

### 22.4 本地不可验证项（如实登记，不阻断）

| # | 项 | 为何本地不可验 | 处置 |
|---|----|----------------|------|
| 1 | 生产重启后的真实装配（`{"outcome": "succeeded", "stage": "startup"}` 出现、`path_not_configured_using_in_memory_default` 不出现） | 需目标机 + 用户手工重启 | 部署阶段实测 |
| 2 | 生产现存定义文档的 legacy 键实际取值 | 需读目标机文件（本阶段禁写操作） | 运维侧只读核对；「不同」则按迁移目标落 `fallback.md` |
| 3 | 开着配置页的旧会话首次保存的 409 发生率 | 需真实前端会话 | 前端已有处理（`ConfigPage.vue`）；登记为交付注意 |


---

## §23 REV-18 增量（系统管理三分 + 项目 CRUD + 唯一运维账号 + LLM Key 管理 + 项目域资料上传：测试规划；追加，不改写 §1~§22）

**设计侧口径**：`docs/architecture_design.md` **1.10.2/REV-18-R2**（ADR-37 ~ ADR-42、ADR-21-R1）+ `docs/module_design.md` **1.10.2/REV-18-R2**（IFC-IB-366 ~ 377；端口 17 → 19）+ `docs/requirements_spec.md` **1.10.0/REV-18-2**（§2.11 / §2.11.1 / §6.0 DR-21）+ `docs/implementation_plan.md` **2.13.0/REV-18**（§25）。**调用**：`INV-GROUP_D-INTELBASE-019`（2026-10-07）。**七条口径为「用户已裁决」**（OQ-IB-25 ~ OQ-IB-31），本代理**不得改判**。

### 23.1 测试范围

**纳入（in-scope）**：REV-18 新增 / 变更的端点与界面契约 —— 项目注册表 CRUD + 软删（ADR-37）；运维账号 CRUD 扩展 + 顺序依赖 + 删除保护（ADR-40）；LLM Key 管理（DB 单行表 + 掩码 + 审计纪律 + 未配置态启动语义；ADR-38 / ADR-39）；项目域资料上传与 `kb_default` 前向迁移（ADR-41）；系统管理三分 IA 与服务端授权解耦（ADR-42）；`users.project_id` 无唯一约束（OQ-IB-28 零迁移）。**沿用既有覆盖**：TC-INT-148 ~ 153（GROUP_C 实现期落地）与前端 30 ~ 34。

**不纳入（out-of-scope）**：物理级联硬删（**OOS-19**）；每项目独立 Key / 多供应商（**OOS-18**）；运行期热重载（**OOS-16** 维持）；生产环境重启与首次环境变量配置（**须由用户执行**，本代理不 SSH 目标机）。

### 23.2 用例规划（三层归属 + 覆盖目标）

| 层 | 文件 | 用例数 | 覆盖 |
|----|------|--------|------|
| unit | `tests/unit/test_rev18_system_mgmt_unit.py`（**新建**，8 例） | **+8** | `LlmKeyStatus` 类型层无明文 + 掩码长度无关（TC-UNIT-R18-001）；`llm_key` 单行表 `CHECK(id=1)` + 006 快照单源（002）；`LlmKeyStore` 端口形状 + 双实现语义一致 + 覆盖单行（003）；项目注册表软删 / seed 幂等 / 端口形状（004）；注册表双实现一致（005）；**005 迁移单源 + `kb_default` 前向迁移幂等**（006）；**ADR-39 Option C 启动语义**（007）；**`users.project_id` 无 UNIQUE**（008） |
| integration | `tests/integration/test_rev18_system_management_extra_int.py`（**新建**，9 例） | **+9** | 1:N 多账号（TC-INT-154）；**422 先于 400/409 的错误码顺序**（155）；软删项目**不级联账号**（156）；软删项目**数据保留**（157）；未配置态 `masked == ""`（158）；**审计只记 outcome**（159）；**任何响应体（含错误体）不含明文**（160）；**D-R18-01 边界**（161）；**资料列表项目域隔离**（162） |
| 前端冒烟 | `src/frontend/tests/frontend.smoke.test.js`（**追加 1 例**） | **+1（34 → 35）** | 35：`LlmKeyStatus` 类型层不含明文字段 + 「资料管理」(files) **保持独立顶级**、不并入系统管理三子域（OQ-IB-31 ④） |
| 自检 | `src/scripts/selfcheck.py` | **51/51（不变）** | 既有 `r13_deploy_discipline` / `r14_project_context` 等已含 REV-18 迁移（005/006）与键名登记检查 |

**强制纪律（沿用既有）**：不得调低阈值、不得把失败改写成 skip / xfail、不得删除既有用例；必须同时有**正向**与**反向 / 对照**（TC-INT-155 的 400 / 409 对照、TC-INT-161 的已登记项目对照、TC-INT-159 的「事件仍在」正向断言）。

### 23.3 AC ↔ TC 追溯矩阵（REV-18 逐 US 逐 AC）

| US | AC | 主要 TC | 层 |
|----|----|---------|----|
| US-IB-35 | AC-IB-35-01 | 前端 30 / 31 | FE |
| US-IB-35 | AC-IB-35-02 | TC-INT-149（projects）/ TC-INT-153（llm-key）/ TC-INT-112（accounts） | INT |
| US-IB-36 | AC-IB-36-01 | TC-INT-148 / TC-INT-151 | INT |
| US-IB-36 | AC-IB-36-02 | TC-INT-148 | INT |
| US-IB-36 | AC-IB-36-03 | TC-INT-148（二次确认 400 / 软删 200）/ **TC-INT-157**（数据保留）/ TC-INT-156 | INT |
| US-IB-36 | AC-IB-36-04 | TC-INT-149 | INT |
| US-IB-37 | AC-IB-37-01 | TC-INT-151 | INT |
| US-IB-37 | AC-IB-37-02 | TC-INT-151 / **TC-INT-155** | INT |
| US-IB-37 | AC-IB-37-03 | **TC-INT-154** / **TC-UNIT-R18-008** | INT + UNIT |
| US-IB-37 | AC-IB-37-04 | TC-INT-112 | INT |
| US-IB-38 | AC-IB-38-01 | TC-INT-154 / R13 既有账户列表用例 | INT |
| US-IB-38 | AC-IB-38-02 | TC-INT-150 | INT |
| US-IB-38 | AC-IB-38-03 | TC-INT-150（409 / 400 / 200）/ **TC-INT-156**（不随项目级联） | INT |
| US-IB-38 | AC-IB-38-04 | TC-INT-112 | INT |
| US-IB-39 | AC-IB-39-01 | TC-INT-152 / **TC-INT-158** / **TC-UNIT-R18-001** / 前端 33 / 35 | INT + UNIT + FE |
| US-IB-39 | AC-IB-39-02 | TC-INT-152 / **TC-UNIT-R18-002** / **TC-UNIT-R18-003** / **TC-UNIT-R18-007** / 前端 33 | INT + UNIT + FE |
| US-IB-39 | AC-IB-39-03 | TC-INT-152 / **TC-INT-159** / **TC-INT-160** / **TC-UNIT-R18-001** / 前端 35 | INT + UNIT + FE |
| US-IB-39 | AC-IB-39-04 | TC-INT-153 | INT |
| US-IB-40 | AC-IB-40-01 | TC-INT-035 / **TC-INT-162** / 前端 32 | INT + FE |
| US-IB-40 | AC-IB-40-02 | TC-INT-035b / **TC-INT-161** | INT |
| US-IB-40 | AC-IB-40-03 | **TC-INT-162** / 前端 32 | INT + FE |
| US-IB-40 | AC-IB-40-04 | **TC-UNIT-R18-006** | UNIT |

**覆盖结论**：US-IB-35 ~ US-IB-40 全部 6 个 US、22 组 AC **均有至少一条 TC**（无悬空 AC）。

### 23.4 门控阈值与判定口径

| 层 | 阈值 | 通过率口径 |
|----|------|-----------|
| unit | ≥ **80%** | `pass / (pass + fail)`；skip / blocked **不入分母** |
| integration | ≥ **90%** | 同上 |
| e2e 关键路径 | **100%** | Must Have 故事的 E2E 用例全绿 |
| 前端冒烟（独立层） | 全绿 | 不并入 Python 三层算术 |
| metrics 算术 | 精确等式 | `total = pass + fail + skip + block`；百分比 = `pass/(pass+fail)` |

**串行门控（强制）**：unit 达标方可跑 integration；integration 达标方可跑 e2e。**本轮零 skip / 零 xfail / 零 blocked**，故不涉及分母争议。

### 23.5 施工前置与不可验证子句

| # | 项 | 类型 | 处置 |
|---|----|------|------|
| 1 | AC-IB-38-03 的「**禁止删除最后一个管理员**」作为**独立**分支 | `[NOT_TESTABLE — v1 单管理员]` | v1 恰有一个 `admin`（`POST /api/accounts` 仅接受 `role=ops`，否则 400），故「最后一个管理员」与「admin」在实现上**同一分支**（`target.role == "admin"` → 409），无法构造「删除两个管理员之一」的独立场景；已由 TC-INT-150 覆盖该分支 |
| 2 | AC-IB-39-02 的「服务**重启**后生效」运行期实测 | `[DEPLOY_REQUIRED]` | 需目标机 + **用户手工重启**（本代理与协调者均不执行）；离线内存替身无法模拟跨装配的 Key 持久化 |
| 3 | AC-IB-39-02 的「承载库文件 **0600** 且属主对齐服务账号」 | `[DEPLOY_REQUIRED]` | 需真机 POSIX 权限位与部署身份核对（检查清单 **B22**）；本代理不 SSH 目标机 |
| 4 | AC-IB-39-03 的「Key **不进 git / 不进命令行与 shell history**」 | `[PARTIAL]` | 静态可核证据（`env.example` 占位符、仓库内无真实 Key 字面量）；shell history 与生产凭据系统属部署期核对（**B23**） |
| 5 | ADR-39 Option C 的「LLM 路径**调用期** fail-closed 错误文本不含 Key 信息」 | `[PARTIAL]` | 离线装配 `llm.backend=fake`，无「真实缺 Key 的 LLM 调用路径」；本轮覆盖 **config 层「缺 Key 非致命」**（TC-UNIT-R18-007）与 **未登记项目检索 fail-closed 文本**（TC-INT-161）；真实缺 Key 调用需 `openai_compatible` 后端且**不触网**，本地不可验 |
| 6 | TBD-T26 / TBD-T27 的容量 / 时延 / 权限真机结论 | `[DEPLOY_REQUIRED]` | 架构侧明确「未经实测前不得给出容量 / 时延结论」；本轮不臆造 |

### 23.6 D-R18-01：按裁决属**预期行为**（非缺陷，不写为待修项）

运行期经 `POST /api/projects` 新建的项目：**可建账号、可被 `GET /api/projects` 枚举**；但**检索 / 上传须等「配置侧登记 + 由用户手工重启服务」后才完全可用**（`load_project_record` 对不在配置文件中的项目抛 `ConfigError` 类错误；`kb_id ≡ project_id` 时上传路径拿不到归属登记）。用户已明确接受此能力边界 —— 登记为 **ADR-32 在项目维度的自然延伸**（交付边界），**不得计为缺陷或待修项**。TC-INT-161 断言的是**清晰的边界错误**（`scope_violation` / `startup_error`，均带可读消息），**不是**崩溃、也不是静默的错误结果。
