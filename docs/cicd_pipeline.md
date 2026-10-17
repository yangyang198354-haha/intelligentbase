<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-CICD-001 |
| 标题 | intelligentbase 智能知识库基座 —— CI/CD 流水线定义 |
| 产出代理 | devops-engineer (author_agent) |
| 调用 ID | INV-GROUP_E-INTELBASE-010（**REV-21 增量**，*编号为拟、以 PM 派发为准*；前序 -009 / -007 / -006 / -005 / -004 / -002 / -003） |
| 项目 | intelligentbase |
| 阶段 | GROUP_E / PHASE_10（部署计划配套；**仅定义，不执行**） |
| revision | **REV-21**（可视化配置「编排图」实显项目已配置的专家 —— 后端**显示投影层展开**（`_expand_expert_nodes` / `definition_derived_summary` 新增 `experts` 键，IFC-IB-393）+ 前端**渲染契约**（`ConfigPage.vue` 标签取 `cn_label` / `graph-expert` class / **仍只读**，IFC-IB-394；`client.ts` 新增 `DerivedExpertEntry`；ADR-52）；**无 SQL / schema 迁移、无新第三方依赖、无新 env 键、无新增模块 / 端口 / 依赖边、无 unit / nginx 站点改动**；含测试增量（unit +19 / integration +4 / e2e +2 / 前端用例 36~40）；**无新 SQL 迁移**（承前结转 R18 缺口 `005`/`006` 不变）。前序 REV-19 = 每项目专家集隔离（`ExpertRegistryView` / `resolve_expert_registry`，IFC-IB-379/380/381）/ 定义文档**目录化**（`IB_DEFINITION_DOC_PATH` 语义 **文件 → 目录**，C-IB-46，IFC-IB-383/384，ADR-44）/ 新项目创建期种子（IFC-IB-385）/ 三专家属 `demo`（C-IB-47，IFC-IB-386）/ 前端项目域闭环（IFC-IB-387） |
| 版本 | **1.6.0**（REV-21 增量；同步 REV-21 测试基线 Python **采集 430** = unit **190** / integration **190** / e2e **29**（另 `tests/agents` **21**）（**本机 Windows 实测 428 passed / 2 skipped**，2 项为 POSIX 权限位语义平台性跳过）/ 前端 **40**（**本机 `npm test` 40/40**，`typecheck` / `build` EXIT 0）/ selfcheck **52/52**） |
| status | **REVISED_PENDING_REVIEW**（**1.6.0/REV-21 待 PM 门控**；**前序 1.5.1/REV-19；1.5.0 已经 GR-E-007 = PASS_WITH_CONDITIONS（PHASE_10 计划层），1.5.1 为用户裁决回填轮、未过门控**）。前序：**APPROVED**（**GR-E-006 = PASS_WITH_CONDITIONS**，经协调者独立核验并由用户 2026-10-07 接受；GR-E-005 对 1.3.0/REV-14 有效、GR-E-004 对 1.2.0/REV-13 有效、GR-E-003 对 1.1.1/R10 有效、GR-E-002 对 1.1.0 有效、GR-E-001 对 R4 前版本有效）。**GR-E-006 协调者复核订正**：§2 后「R18 基线同步说明」的 REV-18 前端增量由 `+14` 改为 `+6`（29 → 35；原值算术有误）。§9.2 基线表本即正确（35/35），未改 |
| 创建日期 | 2026-09-26 |
| 更新日期 | 2026-10-17（REV-21 增量） |
| 凭据纪律 | 本文件不含任何真实凭据；CI 凭据一律经 CI secret / 环境变量注入，不入仓库 |
| 前置 | **git 仓库与 remote 尚未建立**（见 `deployment_plan.md` §1.1 B-01）——本流水线在其闭合前**无法被触发** |

> 本文件是 `docs/deployment_plan.md` 的配套。**工具链均取自 `src/` 既有交付物**，未虚构工具：pytest（`tests/`）、`scripts/selfcheck.py`（离线自检）、`manage.py check`、`src/frontend` 的 `npm run build` 与 `npm test`（Node 20 内置 `node:test`）、`src/requirements*.txt`、`src/deploy/migrations/*.sql`、`src/deploy/checklists.txt`。
> **本基座禁 Docker**（DR-03）——CI 使用**裸 runner / 虚拟环境**，不使用容器镜像作为交付物（见 §5）。
> **REV-13 增量声明（前轮，INV-GROUP_E-INTELBASE-004）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未 commit / push**；**未触发 PHASE_11**。R13 增量见 **§2 阶段表基线修正 / §3 硬门 / §3.2 迁移门 / §7 端到端问答 smoke**；工作流落地文件 `.github/workflows/ci.yml` **已在仓库存在**并增量更新（见 §8）。
>
> **REV-14 增量声明（前轮，INV-GROUP_E-INTELBASE-005）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push**；**未触发 PHASE_11**（该轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**）。
> **R14 变更面对 CI 的影响**：R14 为**纯代码增量**（后端新增 `GET /api/projects`、前端 `projectContext` store + `client.ts` 单点注入 `X-IB-Project`）——**无迁移、无新依赖、无新 env 键、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **245** = unit 95 / integration 129 / e2e 21；前端冒烟 **21**；selfcheck **47/47**）与 ② **版本标识升位**。CI 命令本身**计数无关**（`pytest tests/unit -q` 对 239 与 245 同样判「全绿」），故 R14 对 CI 是**标签/注释层同步**，**不新增 / 不删除任何 step**。工作流落地 `.github/workflows/ci.yml` 同步其**注释基线标签**（见 §8）。

> **REV-18 增量声明（本轮，INV-GROUP_E-INTELBASE-006）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未触发 PHASE_11**（本轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**）。**本轮仅更新两个文档**（本文件 `cicd_pipeline.md` 1.3.0 → **1.4.0/REV-18** 与 `docs/deployment_plan.md` 1.3.0 → **1.4.0/REV-18**），**未改 `.github/workflows/ci.yml`**（R18 无 CI 逻辑改动，仅**如实登记** §3.2 迁移门未覆盖 `005`/`006`）。R18 增量见 **§2 基线同步 / §3 版本门 / §3.2 迁移门登记 / §5 矩阵 / §7 smoke / §8 工作流 / §9 增量节**。
> **R18 变更面对 CI 的影响（关键）**：R18 为**代码 + 2 迁移 + 2 env 键**增量（项目注册表 CRUD / 唯一运维账号 / LLM Key 管理（载体 = DB）/ 项目域资料上传 `kb_id ≡ project_id` 推导），**零新第三方依赖（`tech_stack.md` NO_CHANGE）、零新增模块（仍 26）、零新增依赖边、无 unit / nginx 站点改动、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **351** = unit **157** / integration **170** / e2e **24**，0 skip/xfail；前端冒烟 **35**；selfcheck **51/51**）与 ② **版本标识升位**。**须如实登记**：R18 的两个新迁移 `005_projects.sql` / `006_llm_key.sql` **未纳入 §3.2 迁移门**（该门当前**只覆盖 `003_accounts.sql`**）——这是**本轮已知的 CI 覆盖缺口**（见 §3.2 / §9.3），**不得**当作「已覆盖」隐性略过。**本代理未改 `.github/workflows/ci.yml`**（超出本轮授权面），建议随下轮授权扩展。

> **REV-19 增量声明（本轮，INV-GROUP_E-INTELBASE-007）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未触发 PHASE_11**（本轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**，PHASE_11 保持冻结）。**本轮仅更新两个文档**（本文件 `cicd_pipeline.md` 1.4.0 → **1.5.0/REV-19** 与 `docs/deployment_plan.md` 1.4.0 → **1.5.0/REV-19**），**未改 `.github/workflows/ci.yml`**（R19 无 CI 逻辑改动）。R19 增量见 **§2 基线同步 / §3 版本门 / §3.2 迁移门登记 / §5 矩阵 / §7 smoke / §8 工作流 / §10 增量节**。
> **R19 变更面对 CI 的影响（关键）**：R19 为**纯代码 + 契约增量**（每项目专家集隔离 / 定义文档目录化 / 新项目创建期种子 / 三专家属 `demo` / 前端项目域闭环），**零新第三方依赖（`tech_stack.md` NO_CHANGE，维持 1.4.1/REV-18）、零新增模块（仍 26）、零新增端口（仍 19）、零新增依赖边、零新 env 键、零新 SQL 迁移（无新 `.sql`）、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **382** = unit **174** / integration **181** / e2e **27**；**本机 Windows 实测 380 passed / 2 skipped**，2 项为 `tests/unit/test_rev18_system_mgmt_unit.py` 的 **POSIX 权限位语义**在 Windows 平台性跳过——**非失败、非 xfail**，于 CI（ubuntu-24.04）应实跑；前端冒烟 **35**（**计数未变**）；selfcheck **52/52**）与 ② **版本标识升位**。**须如实登记**：① R19 **无新 SQL 迁移**，§3.2 迁移门**无新增缺口**，但**承前结转 R18 的缺口**（`005`/`006` 仍未纳入，见 §3.2 / §10.3）；② R19 的 **C-IB-46 定义文档目录化迁移** 是**文件级迁移（非 SQL）**，**CI 不可测**（须部署后由用户手工执行，见 `deployment_plan.md` §16）；③ **前端从未实跑构建**（承 `GR-C-014.condition_3`）——CI 阶段 9 与部署面是**首次实跑**的落点（见 §2 阶段 9 / §10.6）。**本代理未改 `.github/workflows/ci.yml`**（超出本轮授权面）。

> **REV-21 增量声明（本轮，INV-GROUP_E-INTELBASE-010，拟）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未触发 PHASE_11**（本轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**，须用户当次授权）。**本轮仅更新两个文档**（本文件 `cicd_pipeline.md` 1.5.1 → **1.6.0/REV-21** 与 `docs/deployment_plan.md` 1.5.1 → **1.6.0/REV-21**），**未改 `.github/workflows/ci.yml`**（R21 无 CI 逻辑改动，仅同步基线标签与如实登记迁移门）。R21 增量见 **§2 基线同步 / §3 版本门 / §3.2 迁移门登记 / §7 smoke / §8 工作流 / §11 增量节**。
> **R21 变更面对 CI 的影响（关键）**：R21 为**纯代码 + 前端渲染契约增量**（编排图专家节点实显：显示投影层展开 `_expand_expert_nodes` + `derived.experts` 键 + 前端标签取 `cn_label` / `graph-expert` class / **仍只读**），**零新第三方依赖（`tech_stack.md` NO_CHANGE，维持 1.4.1/REV-18）、零新增模块（仍 26）、零新增端口（仍 19）、零新增依赖边、零新 env 键、零新 SQL 迁移、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **采集 430 = 428 passed / 2 skipped / 0 failed**；分层 unit **190** / integration **190** / e2e **29**（另 `tests/agents` **21**）；**2 skip 为 `tests/unit/test_rev18_system_mgmt_unit.py` 的 POSIX 权限位语义**在 Windows 平台性跳过——**非失败、非 xfail、非本轮引入**，于 CI（ubuntu-24.04）应实跑；前端冒烟 **40**（**R21 新增用例 36~40**）；selfcheck **52/52**）与 ② **版本标识升位**。**须如实登记**：① R21 **无新 SQL 迁移**，§3.2 迁移门**无新增缺口**，**承前结转** R18 缺口（`005` / `006` 仍未纳入，见 §3.2 / §11.3）；② CI 阶段 9（`npm ci && npm run build && npm test`）**已含前端构建 + 测试**，R21 仅**同步计数**（35 → **40**）；目标机首跑风险（Node 版本差）见 `deployment_plan.md` §17。**本代理未改 `.github/workflows/ci.yml`**（超出本轮授权面）。

## 1. 流水线概览

```
[Source] → [Config+Schema] → [Unit] → [Integration] → [E2E] → [Version-Gate] → [Frontend Build+Test] → [Package Artifact]
                 │                                                                              │
                 └────────────────── 任一失败 → Abort & Notify（不进入后续阶段）────────────┘
```

**触发条件**：
- `push` 到 `main`（沿用 FreeArk 纪律：直接提交 main，不开分支+PR）→ 跑**全量**。
- `pull_request`（若未来启用）→ 跑**全量**。
- 手动触发（`workflow_dispatch`）→ 供 PHASE_11 部署前复跑。

## 2. 阶段定义表

| # | 阶段 | 触发条件 | 命令（**均取自既有交付物**） | 成功标准 | 失败处理 |
|---|------|----------|------------------------------|----------|----------|
| 1 | **Source** | push / PR | `git checkout` / `git fetch` | 拉取成功 | abort & notify |
| 2 | **Config + Schema Check** | 前阶段成功 | `python -m compileall -q src` + **迁移/模式检查**（见 §3.2） | 两者 exit 0 | abort & notify |
| 3 | **Unit** | 前阶段成功 | `python -m pytest tests/unit -q` | **全通过**（**基线 190**，**R21**：188 passed / 2 skipped（**Windows 平台性 POSIX 权限位**，CI 应 190 passed）；R19 为 174，R18 为 157，R14 为 95） | abort & notify |
| 4 | **Integration** | 前阶段成功 | `python -m pytest tests/integration -q` | **全通过**（**基线 190/190 = 100%**，**R21**；R19 为 181，R18 为 170，R14 为 129） | abort & notify |
| 5 | **E2E** | 前阶段成功 | `python -m pytest tests/e2e -q` | **全通过**（**基线 29/29 = 100%**，**R21**；R19 为 27，R18 为 24；含**端到端问答 smoke**，见 §7） | abort & notify |
| 6 | **Full Suite + Coverage** | 前阶段成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | **采集 430 / 428 passed / 2 skipped / 0 failed**（**R21** 基线 = unit 190 + integration 190 + e2e 29 + `tests/agents` 21；**2 skip 为 Windows 平台性 POSIX 权限位断言**，CI（ubuntu）应实跑）；覆盖率 **仅记录不设门** | abort & notify |
| 7 | **Offline Selfcheck** | 前阶段成功 | `python src/scripts/selfcheck.py` | 全 `PASS`，exit 0（任一 `FAIL` 非零退出；**R19 后 52/52**） | abort & notify |
| 8 | **Version Gate** | 前阶段成功 | 见 §3 | 全部断言通过 | abort & notify |
| 9 | **Frontend Build + Test** | 前阶段成功 | `cd src/frontend && npm ci && npm run build && npm test` | `vue-tsc --noEmit` 零错 + `vite build` 成功 + **前端冒烟测试（`node:test`）40/40 全通过**（**R21**：新增用例 36~40；R19 为 35，R18 为 35，R14 为 21） | abort & notify |
| 10 | **Package Artifact** | 前阶段成功 | 归档 `src/frontend/dist/` + 记录 `git rev-parse HEAD` | 产物归档、commit 可追溯 | abort & notify |

> **R13 基线修正说明（关键）**：本表旧值（unit 55 / integration 69→73 / e2e 14 / full 142 / 前端 6）**已作废**。**以实测为准**：全量 Python 用例 **239**（unit **95** / integration **123** / e2e **21**），**0 skip / 0 xfail**；前端冒烟层 **13**（**独立一层，不并入 239 算术**——跨运行时 / 跨框架）。**依据**：`docs/phase_status.md`（REV-13，GROUP_D **GR-D-010 APPROVED，condition_1「DEFECT-R13-01 已修复并独立复跑闭合」**）+ `docs/test_report.md` 1.9.0 §18（collect 口径 239；其文件副本仍记 238 pass / 1 fail，系**闭合后未回写**的同源副本，**以 phase_status 闭合结论为准**）。
> **阶段2 说明（R13 增量）**：阶段2 在 `compileall` 之外追加 **迁移/模式检查**（§3.2）——校验 `src/deploy/migrations/003_accounts.sql` 语法合法且**幂等可重放**（对齐 checklists B20），并复核其与 `ib/ledger/schema.py::account_ddl_script()` **单源一致**。

> **R14 基线同步说明（本轮，关键）**：R14（R13 回归缺陷修复）新增 Python **3** 条（`tests/integration/test_project_context_int_r14.py`，TC-INT-126~128）+ 前端 **4** 条（`frontend.smoke.test.js` 用例 18~21）；integration **126 → 129**、前端冒烟 **17 → 21**，unit（95）/ e2e（21）不变 → **全量 Python 242 → 245**。**依据**：`docs/test_report.md` **1.10.0 / §19**（`245/245` 全绿、`0 skip/xfail/blocked`、EXIT=0；前端 `21/21`；`selfcheck.py` `47/47`）+ `docs/phase_status.md` **GR-D-011 = PASS_WITH_CONDITIONS**（四项数值 PASS 标准 SATISFIED）。**备注**：R14 用例撞号（GROUP_C 的 TC-INT-120~122 与 R13 既有占号冲突）已由 test-engineer 更正为 **TC-INT-123~125**（**计数中性**，见 test_report §19.5 R14-DEF-01）；既有编号 105~122 **一字未动**。R14 对 CI 为**标签层同步**——命令计数无关，**不新增 / 不删除 step**。

> **R18 基线同步说明（本轮，关键）**：R18（系统管理三分 + 项目 CRUD 软删 + 顺序依赖 + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）相对 **REV-17**（327 = unit 149 / integration 154 / e2e 24）新增 **unit +8 / integration +16 / e2e +0 = Python 全量 +24**，前端冒烟 **+6**（29 → **35**）。**分层实测（`pytest -q --collect-only` 逐层）**：`tests/unit` = **157**、`tests/integration` = **170**、`tests/e2e` = **24** ⇒ 157 + 170 + 24 = **351** ✓。**依据**：`docs/test_report.md` **1.14.0 / §23**（`351/351` 全绿、`0 skip / 0 xfail / 0 blocked`、EXIT=0，`docs/evidence/groupd_r18_pytest_final.log`）+ `docs/phase_status.md` **GR-D-015 = PASS_WITH_CONDITIONS**（用户 2026-10-07 接受，四项数值 PASS 标准 SATISFIED）。**R18 测试文件**：新建 `tests/unit/test_rev18_system_mgmt_unit.py`（TC-UNIT-R18-001~008）+ `tests/integration/test_rev18_system_management_int.py`（GROUP_C 首跑 TC-INT-148~153）+ `tests/integration/test_rev18_system_management_extra_int.py`（TC-INT-154~162，补 HTTP 契约缺口）；前端冒烟 `src/frontend/tests/frontend.smoke.test.js` 追加**第 35 例**（既有 34 例未改）。**selfcheck** `51/51`（**R17 起即 51**，R18 **未新增**自检项，命令不变）。**备注**：R18 用例**未撞号**（R14-DEF-01 的撞号问题本轮未复现）；**e2e 层计数不变**（R18 的 e2e 相关断言在 `tests/e2e/test_user_journeys.py` 内**增强既有 TC-E2E-001** —— 断言上传 `kb_id ≡ project_id` 推导，**计数中性**）。R18 对 CI 为**标签层同步 + 一迁移门如实登记**——命令计数无关，**不新增 / 不删除 step**。

> **R19 基线同步说明（本轮，关键）**：R19（每项目专家集隔离 / 定义文档目录化 / 新项目创建期种子 / 三专家属 `demo` / 前端项目域闭环）相对 **REV-18**（351 = unit 157 / integration 170 / e2e 24）新增 **unit +17 / integration +11 / e2e +3 = Python 全量 +31**，前端冒烟 **±0**（35 不变），selfcheck **+1**（51 → **52**，新增 `r19_project_expert_isolation`）。**分层实测（`pytest -q --collect-only` 逐层，独立复跑）**：`tests/unit` = **174**、`tests/integration` = **181**、`tests/e2e` = **27** ⇒ 174 + 181 + 27 = **382** ✓；`pytest tests -q` 实测 **380 passed / 2 skipped / 0 failed**（68.4s）。**R19 测试文件**：新建 `tests/unit/test_rev19_expert_isolation_unit.py` + `tests/integration/test_rev19_project_expert_isolation_int.py` + `tests/e2e/test_rev19_project_expert_journeys.py`（**前端冒烟未新增用例**——IFC-IB-387 项目域闭环为**零代码**，用例数不变，**本轮亦未实跑 `npm`**）。**2 skip 的如实登记**：均为 `tests/unit/test_rev18_system_mgmt_unit.py`（L445 / L476）的 **POSIX 权限位语义**断言 ——「Windows 的 `chmod` 表达不了 0660」与「`_harden_file_permissions` 在 Windows 直接返回」，属**平台性跳过**（**非失败、非 xfail、非 REV-19 引入**），于 CI（ubuntu-24.04）应**实跑**（届时为 382 passed）。**依据**：`docs/test_report.md` **1.15.0 / §24**（REV-19，INV-GROUP_D-INTELBASE-020：改动后 **379 passed / 1 failed / 2 skipped**，唯一 FAIL = **TC-INT-R19-006**（DEFECT-R19-D-01），自报判定 PARTIAL_SUCCESS）+ `docs/phase_status.md` **GR-D-016 / GR-D-017**（REV-19 GROUP_D 门控）+ **GR-C-015**（DEFECT-R19-D-01 **已闭合**：专家域 fail-closed 补 `log_event(expert_domain, …)` + `LOG_FIELDS` 加 `reason` 键，PHASE_06 v2.15.0）；**本轮独立复跑（缺陷闭合后，2026-10-11）**：`pytest tests -q` → **380 passed / 2 skipped / 0 failed**（382 collected，68.4s）+ `selfcheck.py` → **52/52**。**据此基线取「缺陷闭合后」值 = 382 collected / 380 passed / 2 skipped / 0 failed**，与 test_report §24 的 379/1fail/2skip 之差恰为**已闭合的 DEFECT-R19-D-01**（1 条由 FAIL 转 PASS）。R19 对 CI 为**标签层同步**（无迁移门增量、无版本门增量）——命令计数无关，**不新增 / 不删除 step**。

> **R21 基线同步说明（本轮，关键）**：R21（编排图专家节点实显：显示投影层展开 + 前端渲染契约）相对 **REV-19 / R21 改动前实测**新增 **unit +19 / integration +4 / e2e +2 = Python 全量 +25**，前端冒烟 **+5**（35 → **40**，用例 36~40），selfcheck **±0**（52/52，命令不变）。**分层实测（`pytest -q --collect-only` 逐层，本轮复跑）**：`tests/unit` = **190**、`tests/integration` = **190**、`tests/e2e` = **29**、`tests/agents` = **21** ⇒ 190 + 190 + 29 + 21 = **430** ✓；`pytest tests -q` 实测 **428 passed / 2 skipped / 0 failed**。**R21 测试文件**：新建 `tests/unit/test_orchestration_expert_nodes_r21.py`（+19，含冲突负例 `pytest.raises(ConfigError)`）、`tests/integration/test_definition_config_rev21_int.py`（+4）、`tests/e2e/test_rev21_expert_graph_journeys.py`（+2）；`tests/integration/test_definition_config_r7.py` **仅追加断言**；`src/frontend/tests/frontend.smoke.test.js` 追加**用例 36~40**（既有 35 例未改）。**2 skip 的如实登记**：均为 `tests/unit/test_rev18_system_mgmt_unit.py` 的 **POSIX 权限位语义**断言 —— **平台性跳过**（**非失败、非 xfail、非本轮引入**），于 CI（ubuntu-24.04）应**实跑**（届时为 430 passed / 0 skipped）。**依据**：`docs/test_report.md` REV-21 / §25 + `docs/phase_status.md` **GR-D-019 = PASS**（finding_6 记「全量 428 passed / 2 skipped / 0 failed EXIT 0，基线 403 + 2；selfcheck 52/52；前端 `npm test` 40/40、`typecheck` / `build` EXIT 0」）。R21 对 CI 为**标签层同步**（无迁移门增量、无版本门增量）——命令计数无关，**不新增 / 不删除 step**。

> **阶段9 说明（R10 增量）**：阶段9 在 `npm run build` **之后**追加 `npm test`——前端冒烟测试（`src/frontend/tests/frontend.smoke.test.js`，Node 20 内置 `node:test`，**零新增依赖**）。其**必须在 build 之后**运行：用例 6 断言 `dist/` 构建产物内容，属「先建后测」的前置条件顺序。该测试含「`package-lock.json` 与 `package.json` 同步」回归闸——正是 R10 中 `npm ci` 因锁失同步而 `EUSAGE` 失败的根因守卫；接入流水线后该回归守卫方具备**强制力**（此前仅本地可跑）。

> **测试纪律（来源 `CLAUDE.md` / tech_stack §1）**：所有测试必须**离线**跑（`IB_OFFLINE_MODE=1`；外部依赖一律替身）；**严禁连接任何生产 / 外部数据库**；测试使用 SQLite 内存库。CI runner 无须网络访问外部服务（仅需 PyPI / npm registry）。

## 3. 版本门（Version Gate，**硬断言**）

| 断言 | 命令 | 判据 | 依据 |
|------|------|------|------|
| `langchain-openai < 0.3` | `python -c "import importlib.metadata as m; print(m.version('langchain-openai'))"` | **< 0.3** | 冻结决策 ⑤；0.3.x 删 `_convert_chunk_to_generation_chunk` 致流式断流 |
| **禁 PyMuPDF / fitz** | `python -c "import importlib.util as u; print(u.find_spec('fitz'), u.find_spec('pymupdf'))"` | **两者均 None** | ADR-06 / 冻结决策 ④ |
| **禁 Docker** | `command -v docker`（应为空）+ 仓库内无 `Dockerfile`/`docker-compose*` | 无命中 | DR-03 |
| Python 版本 | `python -V` | `>=3.11,<3.14`（CI 目标 **3.12**） | tech_stack §1 |
| 无 `pytest`+`unittest` 混杂误用 | 测试命令统一 pytest | 与实际套件一致 | tech_stack「测试框架」行 |
| `langchain-core` 区间 | `python -c "import importlib.metadata as m; print(m.version('langchain-core'))"` | **`>=0.3,<2.0`** | 冻结决策 ⑤ / `requirements.txt` |
| **`bcrypt` 区间**（R13） | `python -c "import importlib.metadata as m; print(m.version('bcrypt'))"` | **`>=4,<5`** | DR-11 / IFC-IB-311 / `requirements.txt`（对齐 `phase_status` MINOR-R13-03） |
| **前端零运行时 CDN**（R13） | 前端冒烟用例（**R21 后共 40 例**；R19 为 35，R18 为 35，R14 为 21）：源码与 `dist/` 无外网引用 | 零外网引用 | DR-13 / AC-IB-17-06；`tech_stack` §4.5 |
| **凭据零命中**（R13） | `git grep -nE 'IB_DEFAULT_ADMIN_PASSWORD=' -- . \| grep -v REPLACE_ME`（期望空）+ `scripts/selfcheck.py` 的 `deploy_templates_have_no_secrets` | **零命中** | C-IB-09 / REQ-NFR-IB-15 / checklists B19 |

> 版本门是**部署路径与本地一致性**的守卫——`ibweb/composition.py` 在**装配期**也会对 `langchain-openai` 做 fail-fast 断言（test_report DEV-02 已实测该断言触发），CI 版本门是其**上游更早的一道**。
>
> **`bcrypt` 门（R13）**：`requirements.txt` 与 `requirements-offline.txt` 均 pin `bcrypt>=4,<5`；CI 经 `requirements-offline.txt` 安装，故断言在 CI 直接可判。**注意**：CI 基线（如 GitHub runner / 本机）曾实测装到 **5.0.0** —— 若断言失败即**阻断**，这正是本门的意义（部署前须把目标机落到 4.x 或由 PM 裁决放宽 pin，见 `deployment_plan.md` §1.3 R13-D1）。

### 3.1 部署前硬门（PHASE_11 前置；非构建期）

> 下列门在**部署前**（**非**每次 push 的构建期）执行；任一不过则**不得进入部署**（abort & notify，不跳过）。

| # | 硬门 | 命令 | 判据 | 依据 |
|---|------|------|------|------|
| **D-1** | **ib-embed 依赖锁定回填** | 目标机 `sudo /opt/ib-embed/venv/bin/pip freeze > /opt/intelligentbase/requirements-embed.lock.txt`，并**回填部署记录** | 装出的**精确版本**（非区间）落档；`src/requirements-embed.txt` 的**区间不得当锁定值上线** | deployment_plan §1.1 B-05 / §4.2；`src/requirements-embed.txt`「版本 pin 的诚实性说明」 |
| **D-2** | **nginx 配置语法门** | `sudo nginx -t` | **exit 0**（配置语法合法）；**之后**方可 `systemctl reload nginx` | deployment_plan §7.5（C-02）/ §10.1 DEPLOY-009 |
| **D-3** | **SSE 不缓冲复验** | `grep -n "proxy_buffering off" /etc/nginx/sites-available/intelligentbase` | 命中（SSE 段缺此项 = 流式功能**静默失效**） | deployment_plan §7.5 / §7.5.1；`ib/streaming/__init__.py`（`X-Accel-Buffering: no` 为必需） |
| **D-4** | **账户迁移幂等复验**（R13） | 目标机 `python -m ibweb.bootstrap --ensure-schema` **连跑两次** | 两次均 exit 0；`users`/`sessions` 存在且无重复 | deployment_plan §13.2；checklists **B20** |
| **D-5** | **HTTPS 生效 + 零 Cookie**（R13） | `curl` 探测 `http(s)://<host>/healthz` 与各端点 `Set-Cookie` | http = 301（或 444）/ https = 200；**零 `Set-Cookie`** | deployment_plan §13.4 / §13.5；checklists **B15 / B16** |
| **D-6** | **令牌纪律复验**（R13） | 各端点附 `?token=` / 检查 `Authorization` 透传 | `?token=` **全 4xx**；`Authorization: Bearer` 可用 | deployment_plan §13.5；checklists **B17**；DR-10 |

> **D-4~D-6 理由（R13）**：账户 / 会话 / HTTPS 是 R13 新增的**生产可用性前提**。迁移不幂等 → 重启即失败；HTTPS 未生效 / 出现 Cookie → 传输层契约破坏；`?token=` 未拒 → 令牌进访问日志（FreeArk 实际泄露史）。三者均为**部署后不可静默接受**的硬门。

> **D-1 理由**：`src/requirements-embed.txt` 明确其版本 pin 是**保守区间、不是锁定值**；上线前必须用目标机 `pip freeze` 回填精确版本，否则「部署记录里的版本」与「真实装到的版本」不可对账（区间当作锁定值是典型的**假锁定**）。
> **D-2 理由**：nginx 站点变更若带语法错误直接 `reload`，会让对外服务**立即不可用**；`nginx -t` 是 reload 的**硬前置**。**D-3** 是 C-02 引入的 SSE 正确性门（缺 `proxy_buffering off` 时问答被缓冲、首字节永不外发）。

### 3.2 迁移 / 模式门（Schema Gate，**构建期**；R13 增量）

> 与阶段 2 并跑。校验手写 scoped 迁移 **语法合法 + 幂等可重放 + 与代码单源一致**（对齐 checklists **B20**）。仅用标准库（runner 无需 `sqlite3` CLI）。

```bash
# 1) 003_accounts.sql：语法合法 + 幂等重放（CREATE ... IF NOT EXISTS）
python - <<'PY'
import sqlite3, pathlib
sql = pathlib.Path("src/deploy/migrations/003_accounts.sql").read_text(encoding="utf-8")
con = sqlite3.connect(":memory:")
con.executescript(sql)                 # 首次应用
con.executescript(sql)                 # 幂等重放（无副作用即通过）
names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
assert {"users", "sessions"} <= names, names
print("PASS: 003_accounts.sql 语法合法且幂等")
PY

# 2) 单源一致：迁移快照 == 代码生成器（ib/ledger/schema.py::account_ddl_script()）
#    注：快照按可读性重排过缩进，故折叠空白后再比对（不做逐字缩进断言）。
python -c "import sys; sys.path.insert(0,'src'); from ib.ledger.schema import account_ddl_script; import pathlib; snap=pathlib.Path('src/deploy/migrations/003_accounts.sql').read_text('utf-8'); norm=lambda s:''.join(s.split()); assert norm(account_ddl_script()) in norm(snap), '003 与代码生成器不一致'; print('PASS: 单源一致')"
```

> **判据**：两步均 exit 0。**失败处理 = abort & notify**（迁移不可重放 / 与代码漂移，直接阻断，不得跳过）。
>
> **为何 CI 可判**：`003_accounts.sql` 是 `ib/ledger/schema.py::account_ddl_script()` 的**增量快照**（单源不变）；本门把「迁移快照与代码漂移」这一典型静默缺陷变成**构建期显式失败**。

> **R18 增量登记（如实，不隐）**：R18 新增的 `src/deploy/migrations/005_projects.sql`（项目注册表 + `kb_default` 前向数据迁移）与 `006_llm_key.sql`（LLM Key 单行表）**当前未纳入本迁移门** —— 本门脚本**只覆盖 `003_accounts.sql`**，`.github/workflows/ci.yml` 阶段 2 的迁移检查**同样只校验 `003`**。这是**本轮已知的 CI 覆盖缺口**，**不得**当作「已覆盖」隐性略过（本代理**未改** `ci.yml`，见 §9.3）。**为何本轮不就地扩展**：① 改本门脚本与 `.github/workflows/ci.yml` **超出本轮授权面**（本轮只改两文档）；② `005` 的可重放门**需先应用 001 基座 DDL**（`kbs` 表由 `001` 建）方可 `executescript` 重放 —— 直接把 `005` 丢进 `:memory:` 会因缺 `kbs` 失败；`006` 无此依赖（纯 `CREATE TABLE IF NOT EXISTS`）。**建议（下轮授权）**：把 `005`/`006` 纳入本门（判据 = `schema.py::ensure_schema()` 于 `:memory:` 连跑两次 exit 0 + `kb_default` 归零 + `llm_key` 单行表存在），并同步 `ci.yml` 阶段 2。**同源登记**：`deployment_plan.md` §15.2 / §15.9。

> **R19 增量登记（如实，不隐）**：REV-19 **不新增任何 SQL 迁移**（ADR-43 明确「**零新增表 / 列**」；定义文档目录化 = **文件级迁移**，非 schema 变更，见 `deployment_plan.md` §16.2）。故**本迁移门无新增缺口**（门仍只覆盖 `003_accounts.sql`）。**但须显式声明两点**：① **承前结转 R18 的缺口** —— `005_projects.sql` / `006_llm_key.sql` **仍未纳入**本门（见上一条 R18 登记与 §9.3），R19 **未消、也未改**该缺口（本代理**未改** `ci.yml`，超本轮授权面）；② **R19 的 C-IB-46 文件级迁移 CI 不可测** —— `migrate_legacy_definition_file`（IFC-IB-384）作用于**生产文件系统**（`/var/lib/intelligentbase/definition.json` → `<dir>/demo.json`），**不属 schema 门、不属测试套件**，其验证**只能部署后**由用户手工执行并留证（checklists **B24**；`deployment_plan.md` §16.3 / §16.5）。**结论：迁移门命令逐字不变（无 step 改动）；R19 不引入新的 CI 可判迁移，仅结转 R18 缺口 + 登记一项 CI 不可测的文件级迁移。**

## 4. Artifact 管理规则

- **命名格式**：`ib-<git-short-sha>-<CI-run-id>`；内含 `dist/`（前端静态产物）+ `HEAD` 文件（commit 全哈希）。
- **存储位置**：CI 制品库（**须确认可达**；见 deployment_plan §1.1 B-03）。
- **晋升条件**：全 10 阶段**绿色**才产出制品；**staging → prod 的「晋升」不在此流水线内**——本基座用「`git pull` + systemd 重启」交付（ADR-03），CI 制品**仅作前端 `dist/` 与可追溯凭据**，**不得**以制品分发替代 `git pull`（冻结决策 ⑧ 禁逐文件上传）。
- **保留**：至少保留最近 30 个制品。

## 5. 环境配置矩阵

| 配置项 | CI / Dev | Staging | Prod（`192.168.31.133`） |
|--------|----------|---------|--------------------------|
| 运行形态 | 裸 runner / venv（**无 Docker**） | venv | venv + systemd（**4 自研 unit**）+ **系统 nginx**（反代 / 静态前端；见 `deployment_plan.md` §7.5 / C-02） |
| 向量库 | `InMemoryVectorStore`（替身） | 真实 Qdrant（如启用） | 真实 Qdrant（`.deb` 裸装，**仅回环**） |
| Embedding | `FakeEmbedder` / `inproc` | `ib-embed`（真实 bge-m3） | `ib-embed`（真实 bge-m3，**CPU-only**） |
| LLM | `FakeLlmProvider` / `StubLlmProvider` | DeepSeek（测试 key） | DeepSeek（真实，**数据外发已在配置层声明**） |
| OCR | `NullOcrEngine` / 不装 | rapidocr（真装） | rapidocr + onnxruntime（**CPU 版**） |
| 台账 | SQLite 内存 / 临时文件 | SQLite | SQLite WAL（`/var/lib/intelligentbase/ledger/`） |
| `IB_OFFLINE_MODE` | `1` | `0` | **`0`（生产必须为 0；`1` 会全切替身，知识库永远为空却「看起来正常」）** |
| **账户 / 会话**（R13） | `MemoryAccountStore`（`IB_ACCOUNT_BACKEND=memory`，离线替身） | `sqlite` | **`sqlite`**（复用同一 SQLite 台账文件；误设 `memory` 表现为「重启即要重建账户」） |
| **项目注册表**（R18） | `memory` 替身（`IB_PROJECT_REGISTRY_BACKEND=memory`） | `sqlite` | **`sqlite`**（复用同一台账库文件 `projects` 表；误设 `memory` 表现为「项目全部消失、账号绑定失效」，**而非报错**——**两键均有默认值 `sqlite`，无缺失失败模式**） |
| **LLM Key 载体**（R18） | `memory` 替身（`IB_LLM_KEY_BACKEND=memory`） | `sqlite` | **`sqlite`**（复用同一台账库文件 `llm_key` 单行表；**本键只选后端、不承载 Key 值** —— Key 取值**只经 `PUT /api/llm-key`** 写入 DB，**绝不进 `.env` / git / 命令行**，见 checklists B22/B23） |
| **定义文档载体**（R19） | `memory` 替身（`IB_DEFINITION_DOC_PATH` 未配置 → `InMemoryDefinitionDocumentStore` + WARN `path_not_configured_using_in_memory_default`） | `file` | **`file`**（本地**目录根** `<dir>/<project_id>.json`，一项目一文件；`IB_DEFINITION_DOC_PATH` 语义 = **目录根**、**键名不变**）。**误留旧「文件路径」值 → 装配期 fail-closed**（可读 `ConfigError`，**非静默降级为空文档**），见 `deployment_plan.md` §16.3 |
| **每项目专家集**（R19） | 装配期派生只读视图 `ExpertRegistryView`（真源 = 定义文档 + 提示词目录；**非端口、非存储**；进程级 `EXPERT_SPECS` 降级为内置默认单例兜底） | 同左 | 同左（`resolve_expert_registry` fail-closed：默认专家缺失 / 非唯一 / 专家集为空 → 报错，**无跨项目回退**） |
| **认证载体**（R13） | 测试替身（离线令牌） | `Authorization: Bearer`（**无 Cookie**） | `Authorization: Bearer`；**`IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy`**（或接入方模块；未配置 → 启动失败） |
| **HTTPS / TLS 终止**（R13） | 不涉及（本地 http） | 内网自签 / CA（可选） | **nginx `443 ssl`（TLSv1.2/1.3）+ `80→301`**；证书 / 私钥**不进仓库**（私钥 0600） |
| 凭据 | CI secret / 环境变量 | 环境变量 | `EnvironmentFile` 0600（**不入 git**；含 `IB_DEFAULT_ADMIN_PASSWORD`，全占位符） |

## 6. 阶段命令的失败处理策略（**总则**）

- **一律 abort-and-notify，不跳过、不 continue-on-error**。
- **禁止**任何「跳过失败继续部署」的策略（违反冻结决策与硬约束）。
- 重试：**仅**允许对**瞬时网络**类操作（如 `npm ci` / `pip install`）设**有限重试**（≤ 2），不对测试/门禁设自动重试（避免掩盖真失败）。

---

## 7. 端到端问答 smoke（**提问 → 检索 → 作答**；用户期望项，R13 核对并登记）

> **需求**：CI 必须具备一条**提问 → 检索 → 作答**的端到端冒烟项。**核对结论：已存在**于 E2E 层（阶段 5 自动覆盖），本轮**明确登记**如下。

| 项 | 值 |
|----|-----|
| **用例** | `tests/e2e/test_user_journeys.py::test_TC_E2E_001_import_then_rag_answer`（US-IB-01 导入 + **US-IB-08 带来源的检索增强回答**，关键路径） |
| **覆盖链路** | 上传文档 → worker 处理至 `indexed` → **检索命中该文档**（`degraded=False`，`hits` 含 `doc_id`）→ **SSE 问答**（`/api/chat/stream?q=…`）产出 `event: content` + `event: done` |
| **运行位置** | 阶段 5（`python -m pytest tests/e2e -q`）—— **其余 20 条 E2E 一并跑**；阶段 6 全量再覆盖一次 |
| **判据** | 全通过（**R21 后：采集 430 / 428 passed / 2 skipped / 0 failed**，2 skip 为 Windows 平台性 POSIX 权限位断言；R19 为 `382`，R18 为 `351/351`）；**离线跑**（`IB_OFFLINE_MODE=1`，LLM / 向量库 / Embedding 用替身） |
| **R13 附加** | R13 E2E（`tests/e2e/test_accounts_journeys_r13.py`：TC-E2E-020 管理员→运维台全账户旅程 / TC-E2E-021 零粘贴令牌旁路）**同为关键路径**，阶段 5 一并覆盖 |
| **R14 附加** | **R14 回归修复的 CI 层守卫**在**集成层**（阶段 4）：`tests/integration/test_project_context_int_r14.py`（TC-INT-123~128：`GET /api/projects` 授权口径 / admin 选项目后 `/api/config/definition` 503→200 / ops 跨项目 403 / 未知头 fail-closed / 写方法 405）+ **前端层**（阶段 9；TC-FE-018~021：注入 fail-closed / 单项目预选 / ops 不可切换 / provider 优先）。**提示**：真实浏览器端到端（admin 于 UI 选项目）由 `deployment_plan.md` §14.5 **V14-9** 在**部署后**覆盖，**不在 CI 内**（CI 不触网、不装浏览器） |
| **R18 附加** | **R18 的 e2e 层断言增强既有 TC-E2E-001**（`tests/e2e/test_user_journeys.py`）：断言 HTTP 上传落库 **`kb_id ≡ project_id` 推导**（IFC-IB-375 / ADR-41），**计数中性**。R18 **新端点契约**的 CI 守卫在**集成层**（阶段 4）：`tests/integration/test_rev18_system_management_int.py`（TC-INT-148~153）+ `tests/integration/test_rev18_system_management_extra_int.py`（TC-INT-154~162：1:N 多账号 / **422 先于 400·409 的错误码判定顺序** / 项目软删不级联账号·保留账本 / 未配置态 `masked == ""` / **审计只记 outcome 不含密钥** / **任何响应体（含错误体）不含明文** / D-R18-01 边界清晰）；**前端层**（阶段 9，第 35 例）核对三子域 IA + 「资料管理」(files) **保持独立顶级**。**提示**：真实 **LLM Key 提交与重启生效**由 `deployment_plan.md` §15.3 **DEPLOY-031** / §15.8 在**部署后**覆盖，**不在 CI 内**（CI 不触网、不含真实凭据） |

| **R19 附加** | **R19 的 e2e 层**新增 `tests/e2e/test_rev19_project_expert_journeys.py`（**每项目专家集隔离 + 定义文档目录化 + 新项目种子**的端到端旅程；阶段 5 一并跑）。**R19 的集成层**新增 `tests/integration/test_rev19_project_expert_isolation_int.py`（**每项目专家集隔离契约**；阶段 4）。**提示**：真实三项由 `deployment_plan.md` **§16** 在**部署后**覆盖，**不在 CI 内**——① **C-IB-46 定义文档目录化迁移**（§16.3 DEPLOY-037，用户手工执行，CI 无生产文件系统）；② **C-IB-47 三专家历史迁移**（§16.4，**当前无持久化迁移对象、为前向条款**）；③ **前端构建首次实跑**（`npm run typecheck && npm test && npm run build`，§16.3 DEPLOY-034） |

> **纪律**：本 smoke 为**离线替身**冒烟（验证编排与端到端链路**接线正确**），**不是**真实 DeepSeek 调用。真实云端调用属**部署后**冒烟（`deployment_plan.md` §9 / checklists B7），**不在 CI 内**（CI 不触网、不外发数据）。

| **R21 附加** | **R21 的编排图专家节点实显**在 **unit 层**新增 `tests/unit/test_orchestration_expert_nodes_r21.py`（**展开规则 + 冲突负例 `pytest.raises(ConfigError)`**；阶段 3）；**集成层**新增 `tests/integration/test_definition_config_rev21_int.py`（**`GET /api/config/definition` 信封：`derived.nodes` 逐专家展开 / 不含字面量 `expert` / `derived.experts` 3 键 / 顶层键未增**；阶段 4）；**e2e 层**新增 `tests/e2e/test_rev21_expert_graph_journeys.py`（端到端旅程；阶段 5）；**前端层**新增冒烟**用例 36~40**（`cn_label` / `graph-expert` / **仍只读** / `DerivedExpertEntry` 类型契约；阶段 9）。**提示**：真实浏览器**渲染与拖拽**（`AC-IB-54-01` / `AC-IB-52-03`）为 **[NOT_TESTABLE]**（离线无浏览器），「保存并经服务重启后生效」（`AC-IB-52-01` / `52-02`）为 **[DEPLOY_REQUIRED]** —— 均在**部署后**由 `deployment_plan.md` **§17.5 V21-7 / §17.7 AC-R21-C/D** 覆盖，**不在 CI 内** |

## 8. 工作流落地（GitHub Actions，**增量更新**）

> **平台已选定**：GitHub Actions（`.github/workflows/ci.yml` **已存在于仓库**）。本轮为**增量更新**（非新建）：**未 commit / push**。

| 项 | 值 |
|----|-----|
| 文件 | `.github/workflows/ci.yml` |
| Runner | `ubuntu-24.04`；**Python 3.12**（`actions/setup-python@v5`）；**Node 20**（`actions/setup-node@v4`） |
| 触发 | `push` main / `pull_request` main / `workflow_dispatch`（供 PHASE_11 部署前复跑） |
| 能力映射 | **build & test（Python 3.12）覆盖 REV-13 / REV-14 / REV-18 测试**：阶段 3/4/5/6 直接跑 `tests/{unit,integration,e2e}` → 自动纳入 R13 用例（`tests/**/*_r13.py`）、**R14 用例**（`tests/integration/test_project_context_int_r14.py`，TC-INT-123~128）与 **R18 用例**（`tests/unit/test_rev18_system_mgmt_unit.py`，TC-UNIT-R18-001~008；`tests/integration/test_rev18_system_management_int.py` + `_extra_int.py`，TC-INT-148~162）；阶段 9 跑前端 `npm ci && npm run build && npm test` → 纳入 R13 前端冒烟 7 例（TC-FE-007~013）、**R14 前端冒烟 4 例（TC-FE-018~021）** 与 **R18 前端冒烟（第 35 例）** |
| **R13 增量更新** | ① **阶段2**：新增 **Schema/迁移检查** step（§3.2 脚本，纯标准库）；② **基线标签修正**（unit 95 / integration 123 / e2e 21 / full 239 / 前端 13）；③ `bcrypt` 经 `requirements-offline.txt` **已在安装步骤内**（`bcrypt>=4,<5`），无需额外 step；④ **硬门**保持（禁 Docker / 禁 PyMuPDF / `langchain-openai<0.3` 与 `langchain-core>=0.3,<2.0` / Python 范围 / 仓库无容器交付物）；⑤ **凭据零命中**由阶段 7 `selfcheck.py`（`deploy_templates_have_no_secrets`）承担 |
| **R14 增量更新** | **标签/注释层同步（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（integration 123 → **129**、full 239 → **245**、前端 13 → **21**；unit 95 / e2e 21 不变）；② 阶段 7 `selfcheck.py` 现覆盖 **47/47**（含 R14 两条：`r14_project_context` 端点授权口径 + `r14_frontend_project_discipline` 单点注入 / SSE 覆盖；**计数无关**，命令不变）；③ R14 **无迁移 / 无新依赖** → **阶段2 的迁移门脚本不变**（`003_accounts.sql` 仍为唯一迁移快照）；④ R14 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变** |
| **R18 增量更新**（本轮） | **标签/注释层同步 + 一迁移门如实登记（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（unit 95 → **157**、integration 129 → **170**、e2e 21 → **24**、full 245 → **351**、前端 21 → **35**）；② 阶段 7 `selfcheck.py` 现为 **51/51**（**计数无关**，命令不变；R17 起即 51，R18 未新增自检项）；③ **⚠ R18 的 `005_projects.sql` / `006_llm_key.sql` 未纳入阶段 2 迁移门**（该门**只覆盖 `003_accounts.sql`）—— **本轮已知 CI 覆盖缺口**；**本代理未改 `.github/workflows/ci.yml`**（超本轮授权面），建议随下轮授权扩展（详见 §3.2 / §9.3）；④ R18 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变**（含 **`bcrypt>=4,<5` 门**保留，见 §3 / §9.4） |
| **R19 增量更新**（本轮） | **标签/注释层同步（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（unit 157 → **174**、integration 170 → **181**、e2e 24 → **27**、full 351 → **采集 382 / 380 passed / 2 skipped**、前端 **35 不变**）；② 阶段 7 `selfcheck.py` 现为 **52/52**（含 R19 新增 `r19_project_expert_isolation`；**计数无关**，命令不变）；③ R19 **无新 SQL 迁移** → **阶段2 的迁移门脚本不变**（`003_accounts.sql` 仍为唯一迁移快照；**承前结转 R18 缺口** `005`/`006`，见 §3.2 / §10.3）；④ R19 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变**（含 **`bcrypt>=4,<5` 门**保留，见 §3 / §10.4）；⑥ 能力映射自动纳入 R19 用例（阶段 3 `tests/unit/test_rev19_expert_isolation_unit.py`；阶段 4 `tests/integration/test_rev19_project_expert_isolation_int.py`；阶段 5 `tests/e2e/test_rev19_project_expert_journeys.py`），**无需改 `ci.yml`** |
| **R21 增量更新**（本轮） | **标签/注释层同步（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（unit 174 → **190**、integration 181 → **190**、e2e 27 → **29**、full 382 → **采集 430 / 428 passed / 2 skipped**、前端 **35 → 40**）；② 阶段 7 `selfcheck.py` 仍为 **52/52**（**计数无关**，命令不变）；③ R21 **无新 SQL 迁移** → **阶段2 的迁移门脚本不变**（`003_accounts.sql` 仍为唯一迁移快照；**承前结转** R18 缺口 `005` / `006`，见 §3.2 / §11.3）；④ R21 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变**（含 **`bcrypt>=4,<5` 门**保留）；⑥ 能力映射自动纳入 R21 用例（阶段 3 `tests/unit/test_orchestration_expert_nodes_r21.py`；阶段 4 `tests/integration/test_definition_config_rev21_int.py`；阶段 5 `tests/e2e/test_rev21_expert_graph_journeys.py`；阶段 9 前端用例 36~40），**无需改 `ci.yml`** |
| 纪律 | 任一 step 失败即 **abort**（原生 fail-fast，后续 step 自动跳过）；**不** `continue-on-error` |

> **注**：CI 的「禁 Docker」判据**只**校验「仓库不含 `Dockerfile` / `docker-compose*`」（GitHub 托管 runner 自带 docker CLI，`command -v docker` 会恒假阳性）；目标机的 `command -v docker` 空判据属**部署机硬门**，不在 CI。

---

## 9. REV-18 增量节（系统管理三分 / 项目 CRUD 软删 / LLM Key 管理（载体 = DB）/ 项目域资料上传）

> 本节为 **REV-18 增量**（INV-GROUP_E-INTELBASE-006）。**仅定义，未执行**；**未连接、未触碰目标机**。配套部署面见 `deployment_plan.md` **§15**；本节与 §2 / §3 / §3.2 / §5 / §7 / §8 的 R18 增量补注**同源一致**。

### 9.1 R18 对 CI 的净影响（结论：**零 step 改动**）

| 维度 | R18 值 | 对 CI 的影响 |
|------|--------|--------------|
| **阶段结构** | 10 阶段**不变** | **不新增 / 不删除 step** |
| **硬门集合** | **不变**（含 **`bcrypt>=4,<5` 门保留**） | 版本门命令逐字不变 |
| **测试基线** | Python **351** = unit 157 / integration 170 / e2e 24；前端 **35**；selfcheck **51** | **标签/注释层同步**（命令**计数无关**） |
| **迁移** | 新增 `005_projects.sql` / `006_llm_key.sql` | **⚠ 未纳入阶段 2 迁移门**（见 §9.3，**缺口登记**） |
| **第三方依赖** | **零新增**（`tech_stack.md` NO_CHANGE；复用 stdlib `sqlite3`） | 阶段 2 / 9 安装步骤**不变** |
| **锁文件** | `package.json` / `package-lock.json` **零改动** | 阶段 9 `npm ci` 锁同步回归闸**不受影响** |
| **env 键** | **+2**（`IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND`，**均有默认值 `sqlite`、无缺失失败模式**，**不进** `IB_ENV_KEYS` 核心装配开关） | 对 CI **无影响**（CI 用离线内存替身） |
| **模块 / 端口 / 依赖边** | 模块**仍 26**；端口 17 → **19**；**零新增依赖边** | 对 CI **无影响** |

### 9.2 基线（R18 口径）

```
[Source] → [Config+Schema] → [Unit 157] → [Integration 170] → [E2E 24] → [Full 351] → [Selfcheck 51] → [Version-Gate] → [Frontend 35] → [Artifact]
```

| 层 | R18 基线 | 依据 |
|----|----------|------|
| Python 全量 | **351/351**（unit **157** / integration **170** / e2e **24**），0 skip/xfail/blocked | `test_report.md` 1.14.0 §23（`groupd_r18_pytest_final.log`） |
| 前端冒烟（独立层） | **35/35** | 同上（`frontend.smoke.test.js`，第 35 例 R18 新增） |
| 离线自检 | **51/51** | 同上（`groupd_r18_selfcheck_final.log`；R17 起即 51） |

### 9.3 已知缺口：迁移门未覆盖 `005` / `006`（**如实登记**）

- 阶段 2 的迁移门脚本（§3.2）**只覆盖 `003_accounts.sql`**；`.github/workflows/ci.yml` 阶段 2 的迁移检查**同样只校验 `003`**。
- **R18 的 `005_projects.sql` / `006_llm_key.sql` 未被该门覆盖** —— 这是**本轮已知的 CI 覆盖缺口**，**不得**当作「已覆盖」。
- **为何不就地扩展**：① 改本门脚本与 `ci.yml` **超出本轮授权面**（本代理本轮只改 `docs/deployment_plan.md` / `docs/cicd_pipeline.md`）；② `005` 的可重放门**需先应用 001 基座 DDL**（`kbs` 表由 `001` 建），直接 `executescript('005')` 于 `:memory:` 会因缺 `kbs` 失败。
- **建议（下轮授权）**：判据 = `schema.py::ensure_schema()` 于 `:memory:` **连跑两次 exit 0** + `SELECT COUNT(*) FROM documents WHERE kb_id='kb_default'` = 0 + `llm_key` 单行表存在；并同步 `ci.yml` 阶段 2。
- **同源登记**：`deployment_plan.md` §15.2 / §15.9。

### 9.4 版本门集合（R18 复核：**不变**）

§3 的硬断言**逐条保留**：`langchain-openai < 0.3`、**禁 PyMuPDF / fitz**、**禁 Docker**、Python `>=3.11,<3.14`、`langchain-core >=0.3,<2.0`、**`bcrypt >=4,<5`（保留）**、**前端零运行时 CDN**（R18 后共 **35** 例）、**凭据零命中**。R18 **未新增、未删除**任何版本门；`bcrypt` 门因 `requirements*.txt` **零改动**而继续有效。

### 9.5 R18 相关测试文件（CI 覆盖映射）

| 文件 | 层 | 阶段 | 用例 |
|------|-----|------|------|
| `tests/unit/test_rev18_system_mgmt_unit.py` | unit | 阶段 3 | TC-UNIT-R18-001~008（`LlmKeyStatus` 无明文字段 / `llm_key` 单行表 + 006 单源 / `LlmKeyStore` 双实现一致 / 项目注册表软删·seed·端口形状 / **005 单源 + `kb_default` 前向迁移幂等** / **ADR-39 Option C 启动语义** / `users.project_id` 无 UNIQUE） |
| `tests/integration/test_rev18_system_management_int.py` | integration | 阶段 4 | GROUP_C 首跑 TC-INT-148~153 |
| `tests/integration/test_rev18_system_management_extra_int.py` | integration | 阶段 4 | TC-INT-154~162（1:N 多账号 / 422 先于 400·409 / 软删不级联·保留账本 / 未配置态 `masked==""` / 审计不含密钥 / 错误体不含明文 / D-R18-01 边界 / 资料项目域隔离） |
| `tests/e2e/test_user_journeys.py`（**增强既有 TC-E2E-001**） | e2e | 阶段 5 | 上传落库 **`kb_id ≡ project_id` 推导**（计数中性） |
| `src/frontend/tests/frontend.smoke.test.js`（**追加第 35 例**） | 前端 | 阶段 9 | `LlmKeyStatus` 无明文字段 + `files` 保持独立顶级（ADR-42） |

### 9.6 未在 CI 内、须**部署后**覆盖的 R18 项

| 项 | 归属 |
|----|------|
| **LLM Key 提交（`PUT /api/llm-key`）+ 重启生效**（`configured=true` / 启动日志 `llm_configured=true`） | `deployment_plan.md` §15.3 DEPLOY-031 / §15.8 |
| **承载库文件 0660（组 `ib` 共享）+ 属主对齐服务账号**（checklists B22；`0600 → 0660` 见 DEFECT-R18-01；WAL 边车 `-wal` / `-shm` 同判据见 DEFECT-R18-02） | `deployment_plan.md` §15.8 |
| **Key 不进 git / 不进 shell history / 不进命令行**（checklists B23） | `deployment_plan.md` §15.8 |
| **ADR-39 调用期 fail-closed 文本**（缺 Key 非致命 + 其余必需项仍 fail-fast） | `deployment_plan.md` §15.7 / §15.8 |
| **`005` 迁移在既有生产库上的实际行为**（CI 只在 `:memory:` 跑，不跑真机库） | `deployment_plan.md` §15.2 / §15.3 DEPLOY-024~025 |
| **`TBD-T26` / `TBD-T27` 容量 / 时延真机结论** | `deployment_plan.md` §15.8（**未实测前不得给结论**） |

---


## 10. REV-19 增量节（每项目专家集隔离 / 定义文档目录化 / 新项目创建期种子 / 三专家属 `demo` / 前端项目域闭环）

> 本节为 **REV-19 增量**（INV-GROUP_E-INTELBASE-007）。**仅定义，未执行**；**未连接、未触碰目标机**。配套部署面见 `deployment_plan.md` **§16**；本节与 §2 / §3 / §3.2 / §5 / §7 / §8 的 R19 增量补注**同源一致**。

### 10.1 R19 对 CI 的净影响（结论：**零 step 改动**）

| 维度 | R19 值 | 对 CI 的影响 |
|------|--------|--------------|
| **阶段结构** | 10 阶段**不变** | **不新增 / 不删除 step** |
| **硬门集合** | **不变**（含 **`bcrypt>=4,<5` 门保留**） | 版本门命令逐字不变 |
| **测试基线** | Python **382** = unit 174 / integration 181 / e2e 27（**380 passed / 2 skipped**）；前端 **35**（计数未变）；selfcheck **52** | **标签/注释层同步**（命令**计数无关**） |
| **迁移** | **零新增**（无新 `.sql`；定义文档目录化 = **文件级迁移**，非 schema） | 迁移门**不变**；**承前结转** R18 缺口（`005`/`006`） |
| **第三方依赖** | **零新增**（`tech_stack.md` NO_CHANGE，维持 1.4.1/REV-18；复用 stdlib `os`/`json`） | 阶段 2 / 9 安装步骤**不变** |
| **锁文件** | `package.json` / `package-lock.json` **零改动** | 阶段 9 `npm ci` 锁同步回归闸**不受影响** |
| **env 键** | **零新增** | 对 CI **无影响** |
| **模块 / 端口 / 依赖边** | 模块**仍 26**；端口**仍 19**；**零新增依赖边** | 对 CI **无影响** |
| **前端** | IFC-IB-387 **零代码**（复用既有 `projectContext` / `client.ts`） | 前端用例数**不变**（35）；**首次实跑**落点在阶段 9 与部署面 |

> **禁 Docker 复核**：REV-19 **未引入任何容器化**，本文件**无任何 Docker step**（DR-03 冻结决策②/⑦不变）。

### 10.2 基线（R19 口径）

```
[Source] → [Config+Schema] → [Unit 174] → [Integration 181] → [E2E 27] → [Full 382] → [Selfcheck 52] → [Version-Gate] → [Frontend 35] → [Artifact]
```

| 层 | R19 基线 | 依据 |
|----|----------|------|
| Python 全量 | 采集 **382**；**380 passed / 2 skipped / 0 failed**（unit **174** / integration **181** / e2e **27**） | `test_report.md` **1.15.0 §24**（379 passed / 1 failed / 2 skipped = DEFECT-R19-D-01）+ `phase_status` **GR-D-016 / GR-D-017** + **GR-C-015**（缺陷已闭合）；**本轮独立复跑**（`pytest tests -q`，68.4s；`--collect-only` 逐层） |
| 前端冒烟（独立层） | **35/35**（**本轮未实跑 `npm`**） | 用例计数（`frontend.smoke.test.js` 35 例）；承 `GR-C-014.condition_3`（前端零代码、构建本轮未执行） |
| 离线自检 | **52/52** | `test_report.md` §24 / `phase_status`（`selfcheck 52/52`）；**本轮独立复跑**（`python src/scripts/selfcheck.py`；含 `r19_project_expert_isolation`） |

> **2 skip 口径**：均为 `tests/unit/test_rev18_system_mgmt_unit.py`（L445 / L476）的 **POSIX 权限位语义**断言，Windows 平台性跳过（**非失败 / 非 xfail / 非 R19 引入**）；CI（ubuntu-24.04）应实跑。

### 10.3 迁移门：R19 **零新增缺口**，**承前结转** R18 缺口（**如实登记**）

- REV-19 **不新增 SQL 迁移** —— ADR-43 明确「零新增表 / 列」；因此**阶段 2 迁移门命令逐字不变**。
- **承前结转**：R18 的 `005_projects.sql` / `006_llm_key.sql` **仍未纳入**迁移门（该门只覆盖 `003_accounts.sql`）—— R19 **未消、未改**该缺口（本代理未改 `ci.yml`，超授权面）。**建议仍同上轮**：判据 = `schema.py::ensure_schema()` 于 `:memory:` 连跑两次 exit 0 + `kb_default` 归零 + `llm_key` 单行表存在，并同步 `ci.yml` 阶段 2。
- **R19 新增的 CI 不可测项**：C-IB-46 **定义文档目录化迁移**（`migrate_legacy_definition_file`）作用于**生产文件系统**，**不属 schema 门、不属测试套件** —— 只能部署后由用户手工执行并留证（checklists **B24**；`deployment_plan.md` §16.3 / §16.5）。
- **同源登记**：`deployment_plan.md` §16.2 / §16.6。

### 10.4 版本门集合（R19 复核：**不变**）

§3 的硬断言**逐条保留**：`langchain-openai < 0.3`、**禁 PyMuPDF / fitz**、**禁 Docker**、Python `>=3.11,<3.14`、`langchain-core >=0.3,<2.0`、**`bcrypt >=4,<5`（保留）**、**前端零运行时 CDN**（R19 后仍 **35** 例）、**凭据零命中**。R19 **未新增、未删除**任何版本门。

### 10.5 R19 相关测试文件（CI 覆盖映射）

| 文件 | 层 | 阶段 | 覆盖 |
|------|-----|------|------|
| `tests/unit/test_rev19_expert_isolation_unit.py` | unit | 阶段 3 | 每项目专家集隔离（`ExpertRegistryView` / `resolve_expert_registry` fail-closed / `builtin_default_registry` 单例）+ 定义文档目录化（`_path_for`）+ `migrate_expert_history` 幂等 / 归属判据 |
| `tests/integration/test_rev19_project_expert_isolation_int.py` | integration | 阶段 4 | 项目域隔离契约（跨项目无回退 / 未登记项目 fail-closed / 种子差异） |
| `tests/e2e/test_rev19_project_expert_journeys.py` | e2e | 阶段 5 | 每项目专家集 / 目录化 / 新项目种子的端到端旅程 |

### 10.6 未在 CI 内、须**部署后**覆盖的 R19 项

| 项 | 归属 |
|----|------|
| **C-IB-46 定义文档目录化迁移**（`/var/lib/intelligentbase/definition.json` → `<dir>/demo.json`，用户手工执行 + 先备份 + 失败回滚） | `deployment_plan.md` §16.3 DEPLOY-037 / §16.4 |
| **C-IB-47 三专家历史迁移**（**当前无持久化迁移对象，前向条款**；不得写成可执行步骤） | `deployment_plan.md` §16.4 / §16.6 |
| **前端构建首次实跑**（`npm run typecheck` / `npm test` / `npm run build`；产物落 `/var/www/intelligentbase/`，**改前端不重启服务**） | `deployment_plan.md` §16.3 DEPLOY-034 / DEPLOY-035 / §16.5 |
| **服务重启判定**（仅后端 Python 变 → 重启 `ib-web`（必要时 `ib-worker` / `ib-embed`）；纯前端静态 → **不重启**） | `deployment_plan.md` §16.3 DEPLOY-039 / §16.5 |
| **装配期 fail-closed 文本**（旧「文件」值 → 可读 `ConfigError`，非静默空文档） | `deployment_plan.md` §16.5 |

### 10.7 2026-10-11 用户裁决回填轮（**文书回填 + 交付物订正；对 CI 净影响 = 零**）

> 本轮为**文书回填轮**（非门控变更轮）：在 REV-19 门控（GR-E-007）之后，按用户 2026-10-11 裁决对若干**已批准文书**做**追加式**回填与交付物订正。本文件版本 1.5.0 → **1.5.1**。

| 维度 | 本轮内容 | 对 CI 的影响 |
|------|----------|--------------|
| **净影响** | **无 step 增删、无基线变更、无门集合变更** | **零** —— CI 定义逻辑**逐字不变** |
| **文档面** | `checklists.txt` B24/B25 追加式订正；`deployment_plan.md` §1.1 / §16.3 / §16.4 追加式回填；本文件 1.5.0 → **1.5.1** | 均为**注释 / 文档层**，不触及任何 CI step |
| **未改** | `.github/workflows/ci.yml`（本轮**未碰**） | 流水线**行为不变** |

- **解析口径如实登记**：本文件**不使用** `phase_status.md` 那类 **XML `file_header`**，而是 **HTML 注释头部（`<!-- ... -->`）+ Markdown 元数据表**；故 **`xml.etree.ElementTree` 解析不适用于本文件**（本文件**不编造** XML 判据）。本文件的一致性以 **Markdown 表结构**与**版本历史表行数**为据。
- **边界**：本轮**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 写操作 / 迁移；**未 commit / push / `git add`**；**未触发 PHASE_11**。

---

## 11. REV-21 增量节（可视化配置「编排图」实显项目已配置的专家 —— 显示投影层展开 + 前端渲染契约）

> 本节为 **REV-21 增量**（INV-GROUP_E-INTELBASE-010，拟）。**仅定义，未执行**；**未连接、未触碰目标机**。配套部署面见 `deployment_plan.md` **§17**；本节与 §2 / §3 / §3.2 / §7 / §8 的 R21 增量补注**同源一致**。

### 11.1 R21 对 CI 的净影响（结论：**零 step 改动**）

| 维度 | R21 值 | 对 CI 的影响 |
|------|--------|--------------|
| **阶段结构** | 10 阶段**不变** | **不新增 / 不删除 step** |
| **硬门集合** | **不变**（含 **`bcrypt>=4,<5` 门保留**） | 版本门命令逐字不变 |
| **测试基线** | Python **采集 430 = 428 passed / 2 skipped / 0 failed**（unit **190** / integration **190** / e2e **29** / `tests/agents` **21**）；前端 **40**；selfcheck **52** | **标签/注释层同步**（命令**计数无关**） |
| **迁移** | **零新增**（无新 `.sql`） | 迁移门**不变**；**承前结转** R18 缺口（`005` / `006`） |
| **第三方依赖** | **零新增**（`tech_stack.md` NO_CHANGE，维持 1.4.1/REV-18） | 阶段 2 / 9 安装步骤**不变** |
| **锁文件** | `package.json` / `package-lock.json` **零改动** | 阶段 9 `npm ci` 锁同步回归闸**不受影响** |
| **env 键** | **零新增** | 对 CI **无影响** |
| **模块 / 端口 / 依赖边** | 模块**仍 26**；端口**仍 19**；**零新增依赖边** | 对 CI **无影响** |
| **运行期拓扑** | **未改**（C-IB-54；展开仅在显示投影层） | 对 CI **无影响** |

> **禁 Docker 复核**：REV-21 **未引入任何容器化**，本文件**无任何 Docker step**（DR-03 冻结决策②/⑦不变）。

### 11.2 基线（R21 口径）

```
[Source] → [Config+Schema] → [Unit 190] → [Integration 190] → [E2E 29] → [Full 430] → [Selfcheck 52] → [Version-Gate] → [Frontend 40] → [Artifact]
```

| 层 | R21 基线 | 依据 |
|----|----------|------|
| Python 全量 | **采集 430**；**428 passed / 2 skipped / 0 failed**（unit **190** / integration **190** / e2e **29** / `tests/agents` **21**） | `docs/test_report.md` REV-21 / §25 + `phase_status` **GR-D-019**（finding_6：428 passed / 2 skipped / 0 failed，基线 403 + 2）；**本轮独立复跑**（`pytest tests -q`；`--collect-only` 逐层） |
| 前端冒烟（独立层） | **40/40** | `frontend.smoke.test.js`（**用例 36~40 为 R21 新增**；R19 为 35）；test_report §25 |
| 离线自检 | **52/52** | `docs/test_report.md` §25 / `phase_status`（`selfcheck 52/52`；命令不变） |

> **2 skip 口径**：均为 `tests/unit/test_rev18_system_mgmt_unit.py` 的 **POSIX 权限位语义**断言，Windows 平台性跳过（**非失败 / 非 xfail / 非本轮引入**）；CI（ubuntu-24.04）应实跑（届时 430 passed / 0 skipped）。

### 11.3 迁移门：R21 **零新增缺口**，**承前结转** R18 缺口（**如实登记**）

- REV-21 **不新增 SQL 迁移** —— 显示投影层展开与前端渲染均为**纯代码**（ADR-52 未引入任何表 / 列）；因此**阶段 2 迁移门命令逐字不变**（`003_accounts.sql` 仍为唯一迁移快照）。
- **承前结转**：R18 的 `005_projects.sql` / `006_llm_key.sql` **仍未纳入**迁移门 —— R21 **未消、也未改**该缺口（本代理未改 `ci.yml`，超授权面）。**建议仍同上轮**：判据 = `schema.py::ensure_schema()` 于 `:memory:` 连跑两次 exit 0 + `kb_default` 归零 + `llm_key` 单行表存在，并同步 `ci.yml` 阶段 2。
- **同源登记**：`deployment_plan.md` §17.2 / §17.8。

### 11.4 版本门集合（R21 复核：**不变**）

§3 的硬断言**逐条保留**：`langchain-openai < 0.3`、**禁 PyMuPDF / fitz**、**禁 Docker**、Python `>=3.11,<3.14`、`langchain-core >=0.3,<2.0`、**`bcrypt >=4,<5`**、**前端零运行时 CDN**（R21 后共 **40** 例）、**凭据零命中**。R21 **未新增、未删除**任何版本门。

### 11.5 R21 相关测试文件（CI 覆盖映射）

| 文件 | 层 | 阶段 | 覆盖 |
|------|-----|------|------|
| `tests/unit/test_orchestration_expert_nodes_r21.py` | unit | 阶段 3 | `_expand_expert_nodes` 展开规则（结构节点保留 / 占位节点逐专家原位展开 / 条件边仍 1 条 / 普通边逐专家镜像 / 节点唯一）+ **冲突负例**（专家名 ∈ {route, general, gate, aggregate} ∪ {START, END} ⇒ `ConfigError`） |
| `tests/integration/test_definition_config_rev21_int.py` | integration | 阶段 4 | `GET /api/config/definition` 信封（`derived.nodes` 逐专家展开 / **不含字面量 `expert`** / `derived.experts` 3 键 / **顶层键未增**） |
| `tests/e2e/test_rev21_expert_graph_journeys.py` | e2e | 阶段 5 | 编排图专家节点实显的端到端旅程 |
| `tests/integration/test_definition_config_r7.py`（**仅追加断言**） | integration | 阶段 4 | R7 既有契约 + R21 **追加**断言（**原断言未动**） |
| `src/frontend/tests/frontend.smoke.test.js`（用例 **36~40**） | 前端 | 阶段 9 | `cn_label` 标签 / `graph-expert` 视觉可区分 / **仍只读** / `DerivedExpertEntry` 类型契约 / 前端**不自展开**占位节点 |

### 11.6 未在 CI 内、须**部署后**覆盖的 R21 项

| 项 | 归属 |
|----|------|
| **真实浏览器渲染 / 拖拽连线视觉观感**（`AC-IB-54-01` / `AC-IB-52-03`，`[NOT_TESTABLE]`） | `deployment_plan.md` §17.5 **V21-7** / §17.7 **AC-R21-C** |
| **「保存并经服务重启后生效」**（`AC-IB-52-01` / `52-02`，`[DEPLOY_REQUIRED]`） | `deployment_plan.md` §17.7 **AC-R21-D** |
| **后端重启 + 编排图专家节点实显**（`GET /api/config/definition` 的 `derived.*` 实测） | `deployment_plan.md` §17.3 **DEPLOY-042** / §17.5 **V21-1 / V21-2 / V21-3** |
| **前端重建 + `dist/` 发布**（目标机首跑；改前端不重启） | `deployment_plan.md` §17.3 **DEPLOY-043** / §17.5 **V21-4** |
| **目标机首跑风险**（Node 版本差：CI Node 20 vs 生产 node v22；锁漂移） | `deployment_plan.md` §17.6 **R-21-2** |

---

## 附：自检声明

- 本流水线**未执行**，为**定义**；CI 平台具体实现 = **GitHub Actions**（`.github/workflows/ci.yml` 已存在并本轮增量更新，见 §8）。
- 所有命令均引用 `src/` 既有交付物，**未编造**工具或测试路径。
- 含**禁 Docker / 禁 PyMuPDF / `langchain-openai<0.3`** 三条硬门，另加 **`langchain-core>=0.3,<2.0` / `bcrypt>=4,<5` / 前端零运行时 CDN / 凭据零命中** 与 **迁移幂等门**，与本项目冻结决策对齐。
- 本文件**不含任何真实凭据**。
- **REV-13 增量边界（前轮，INV-GROUP_E-INTELBASE-004）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH；**未 commit / push**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md`；**未触发 PHASE_11**。该轮仅更新本文件与 `.github/workflows/ci.yml`（CI/CD 配置）。
- **REV-14 增量边界（前轮，INV-GROUP_E-INTELBASE-005）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**，且该轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**。该轮仅更新本文件（1.2.0 → **1.3.0/REV-14**）、`docs/deployment_plan.md` 与 `.github/workflows/ci.yml` 的**注释基线标签**（纯注释，不改 step 逻辑）。
- **REV-18 增量边界（本轮，INV-GROUP_E-INTELBASE-006）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R18 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**，且**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**。本轮仅更新**两个文档**（本文件 1.3.0 → **1.4.0/REV-18** 与 `docs/deployment_plan.md` 1.3.0 → **1.4.0/REV-18**），**未改 `ci.yml`**（R18 无 CI 逻辑改动，仅**如实登记** §3.2/§9.3 迁移门未覆盖 `005`/`006`）。
- **REV-19 增量边界（本轮，INV-GROUP_E-INTELBASE-007）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R19 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**，且**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**（PHASE_11 保持冻结）。本轮**仅更新两个文档**（本文件 1.4.0 → **1.5.0/REV-19** 与 `docs/deployment_plan.md` 1.4.0 → **1.5.0/REV-19**），**未改 `ci.yml`**（R19 无 CI 逻辑改动，仅**如实登记** §3.2 / §10.3 承前结转 R18 缺口 + C-IB-46 文件级迁移 CI 不可测）。**本文件为本轮 CI 视角下唯一运行过的动作 = 只读引用 + 独立复跑 `pytest` / `selfcheck` 以核实基线数字**（R19**未触发**、也未新增任何 CI step）。
- **REV-21 增量边界（本轮，INV-GROUP_E-INTELBASE-010，拟）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R21 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未跑 Docker**（忠实 DR-03）。**未触发 PHASE_11**，且**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**（本代理**未**、也**不得**自赋）。本轮**仅更新两个文档**（本文件 1.5.1 → **1.6.0/REV-21** 与 `docs/deployment_plan.md` 1.5.1 → **1.6.0/REV-21**），另**新增** `src/deploy/checklists.txt` 条目（**仅新增、不改既有条目**）。**本文件为本轮 CI 视角下唯一运行过的动作 = 只读引用 + 独立复跑 `pytest` / `selfcheck` 以核实基线数字**（R21 **未触发**、也未新增任何 CI step）。

---

## 修订记录（Revision History）

| 版本 | 轮次 | 日期 | 调用 ID | 变更摘要 | 依据事实 |
|------|------|------|---------|----------|----------|
| 1.0.0 | PHASE_10 首版 | 2026-09-26 | INV-GROUP_E-INTELBASE-001 | 首版（GR-E-001 = PASS_WITH_CONDITIONS，**对该 R4 前版本有效**） | 既有交付物（pytest / selfcheck / Requirements / frontend build / checklists） |
| 1.1.0 | GROUP_E / R4（REV-04-3） | 2026-09-26 | INV-GROUP_E-INTELBASE-002 | **最小修订**：新增 §3.1「部署前硬门」D-1（ib-embed 依赖 `pip freeze` 回填锁定）/ D-2（`nginx -t` 语法门）/ D-3（SSE `proxy_buffering off` 复验）；§5 矩阵「Prod 运行形态」补系统 nginx；其余不动 | `src/requirements-embed.txt`「区间非锁定值」；`deployment_plan.md` §7.5（C-02）/ §4.2 |
| 1.1.1 | GROUP_E / R10（REV-10-2） | 2026-09-27 | INV-GROUP_E-INTELBASE-003 | **最小修订**：阶段9 定义更新为「`vue-tsc` 零错 + `vite build` + 前端冒烟测试（`node:test`）」——命令追加 `npm test`（与 `.github/workflows/ci.yml` 阶段9 逐字同步）；§1 概览补「Build+Test」；新增阶段9 说明（先建后测顺序理由 + 锁同步回归闸的强制力）；其余不动 | GR-C-007 / R10：`src/frontend/package.json` 新增 `"test": "node --test"`、`src/frontend/tests/frontend.smoke.test.js`（6 例）；协调者裁决「阶段9 接入 `npm test`」 |
| **1.2.0** | **GROUP_E / REV-13** | **2026-10-06** | **INV-GROUP_E-INTELBASE-004** | **REV-13 增量**：① header 补 revision=REV-13 / 上游输入；新增「REV-13 增量声明」；② **§2 阶段表基线修正**（旧 55/69/14/142/前端 6 → **unit 95 / integration 123 / e2e 21 / full 239 / 前端 13**，0 skip/xfail；依据 phase_status GR-D-010 闭合 + test_report §18 collect 口径）；阶段2 扩展为 **Config + Schema Check**；③ **§3 版本门**补 `langchain-core` / **`bcrypt>=4,<5`** / 前端零 CDN / 凭据零命中 四行；④ 新增 **§3.2 迁移/模式门**（003_accounts.sql 语法 + 幂等 + 与代码生成器单源一致，纯标准库）；⑤ **§3.1 部署前硬门**补 **D-4 / D-5 / D-6**（迁移幂等 / HTTPS+零 Cookie / 令牌纪律）；⑥ §5 矩阵补 R13 行（账户/会话、认证载体、HTTPS/TLS）；⑦ 新增 **§7 端到端问答 smoke**（登记 TC-E2E-001 提问→检索→作答）；⑧ 新增 **§8 工作流落地**（GitHub Actions `ci.yml` 增量更新映射）；status → REVISED_PENDING_REVIEW | `docs/phase_status.md`（GR-B-006 / GR-C-009 / GR-D-010）；`docs/test_report.md` 1.9.0 §18；`src/deploy/migrations/003_accounts.sql`；`src/requirements.txt`（`bcrypt>=4,<5`）；`src/requirements-offline.txt`；`tests/e2e/test_user_journeys.py`（TC-E2E-001）；`tests/e2e/test_accounts_journeys_r13.py`；`src/frontend/tests/frontend.smoke.test.js`（13 例）；`.github/workflows/ci.yml` |
| **1.3.0** | **GROUP_E / REV-14** | **2026-10-06** | **INV-GROUP_E-INTELBASE-005** | **REV-14 增量（标签/注释层同步，不新增 / 不删除 step）**：① header 补 revision=REV-14 / 版本 1.2.0→**1.3.0**；新增「REV-14 增量声明 + R14 变更面对 CI 的影响」；② **§2 阶段表基线同步**（integration 123 → **129**、full 239 → **245**、前端 13 → **21**；unit 95 / e2e 21 不变）+ 新增「R14 基线同步说明」（含 R14-DEF-01 撞号更正计数中性说明）；③ §3 版本门「前端零运行时 CDN」行注更新为 R14 后 21 例；④ §7 端到端 smoke 判据改 `245/245` + 新增「R14 附加」（CI 层守卫在集成/前端层；真实浏览器端到端属部署后 V14-9，不在 CI）；⑤ §8 工作流落地「能力映射」补 R14 用例 + 新增「R14 增量更新」行（基线标签 / selfcheck 47 / 无迁移→迁移门不变 / 无锁改动→锁同步闸不受影响 / 硬门集合不变）；⑥ 附自检补 R14 边界；status → REVISED_PENDING_REVIEW（待 GR-E-005） | `docs/test_report.md` 1.10.0/R14 §19（Python 245 = unit 95 + integration 129 + e2e 21；前端 21；selfcheck 47/47）；`docs/phase_status.md` GR-D-011；`docs/deployment_plan.md` 1.3.0/REV-14 §14；`tests/integration/test_project_context_int_r14.py`（TC-INT-123~128）；`src/frontend/tests/frontend.smoke.test.js`（21 例）；`src/scripts/selfcheck.py`（47/47） |
| **1.4.0** | **GROUP_E / REV-18** | **2026-10-07** | **INV-GROUP_E-INTELBASE-006** | **REV-18 增量（标签层同步 + 一迁移门如实登记，不新增 / 不删除 step）**：① header 补 revision=REV-18 / 版本 1.3.0→**1.4.0**；新增「REV-18 增量声明 + R18 变更面对 CI 的影响」；② **§2 阶段表基线同步**（unit 95 → **157**、integration 129 → **170**、e2e 21 → **24**、full 245 → **351**、前端 21 → **35**）+ 新增「R18 基线同步说明」（分层实测 157+170+24=351；R18 测试文件清单；e2e 计数中性说明）；③ §3 版本门「前端零运行时 CDN」行注更新为 R18 后 35 例（版本门集合**不变**，**`bcrypt` 门保留**）；④ **§3.2 迁移门新增「R18 增量登记」**（`005`/`006` **未纳入**，如实登记缺口）；⑤ §5 矩阵补 R18 两行（项目注册表 / LLM Key 载体）；⑥ §7 端到端 smoke 判据改 `351/351` + 新增「R18 附加」；⑦ §8 工作流落地「能力映射」补 R18 用例 + 新增「R18 增量更新」行；⑧ **新增 §9 REV-18 增量节**（9.1 净影响 / 9.2 基线 / **9.3 已知缺口：迁移门未覆盖 `005`/`006`** / 9.4 版本门集合不变 / 9.5 测试文件映射 / 9.6 须部署后覆盖项）；⑨ 附自检补 R18 边界；status → REVISED_PENDING_REVIEW（待 GR-E-006） | `docs/test_report.md` 1.14.0/REV-18 §23（Python **351** = unit 157 + integration 170 + e2e 24，0 skip/xfail，`groupd_r18_pytest_final.log`；前端 **35**；selfcheck **51/51**，`groupd_r18_selfcheck_final.log`）；`docs/phase_status.md` GR-D-015（用户 2026-10-07 接受）；`docs/deployment_plan.md` 1.4.0/REV-18 §15；`tests/unit/test_rev18_system_mgmt_unit.py`（TC-UNIT-R18-001~008）；`tests/integration/test_rev18_system_management_int.py`（TC-INT-148~153）+ `test_rev18_system_management_extra_int.py`（TC-INT-154~162）；`src/frontend/tests/frontend.smoke.test.js`（35 例）；`src/deploy/migrations/{005_projects,006_llm_key}.sql`；`.github/workflows/ci.yml`（**未改**，仅登记 §3.2 迁移门未覆盖 `005`/`006`） |
| **1.5.0** | **GROUP_E / REV-19** | **2026-10-11** | **INV-GROUP_E-INTELBASE-007** | **REV-19 增量（标签层同步，不新增 / 不删除 step）**：① header 补 revision=REV-19 / 版本 1.4.0→**1.5.0**；新增「REV-19 增量声明 + R19 变更面对 CI 的影响」；② **§2 阶段表基线同步**（unit 157 → **174**、integration 170 → **181**、e2e 24 → **27**、full 351 → **采集 382 / 380 passed / 2 skipped**、前端 **35 不变**）+ 新增「R19 基线同步说明」（分层实测 174+181+27=382；R19 测试文件清单；**2 skip 为 Windows 平台性 POSIX 权限位断言，如实登记**；前端未新增用例且本轮未实跑）；③ §3 版本门「前端零运行时 CDN」行注更新为 R19 后仍 35 例（版本门集合**不变**，**`bcrypt` 门保留**）；④ **§3.2 迁移门新增「R19 增量登记」**（**零新增缺口** + **承前结转 R18 缺口** + **C-IB-46 文件级迁移 CI 不可测**）；⑤ §5 矩阵补 R19 两行（定义文档载体 / 每项目专家集）；⑥ §7 端到端 smoke 判据改 `382`（380 passed / 2 skipped）+ 新增「R19 附加」；⑦ §8 工作流落地新增「R19 增量更新」行；⑧ **新增 §10 REV-19 增量节**（10.1 净影响 / 10.2 基线 / 10.3 迁移门：零新增缺口 + 结转 / 10.4 版本门集合不变 / 10.5 测试文件映射 / 10.6 须部署后覆盖项）；⑨ 附自检补 R19 边界；status → REVISED_PENDING_REVIEW（待 GR-E-007） | `docs/deployment_plan.md` 1.5.0/REV-19 §16；`src/ib/config/definition.py`（`FileDefinitionDocumentStore._path_for` / `migrate_legacy_definition_file`）；`src/ib/experts/__init__.py`（`ExpertRegistryView` / `resolve_expert_registry` / `builtin_default_registry`）；`src/ib/streaming/__init__.py`（`migrate_expert_history`）；`src/deploy/checklists.txt`（**B24 / B25**）；`tests/{unit,integration,e2e}/test_rev19_*`；`docs/rev19_groupb_apply_package*.md`（ADR-43~47 / IFC-IB-378~388）；`docs/test_report.md` **1.15.0 / §24**（REV-19：379 passed / 1 failed / 2 skipped，TC-INT-R19-006 = DEFECT-R19-D-01）+ `docs/phase_status.md` **GR-B-011 / GR-C-014 / GR-C-015 / GR-D-016 / GR-D-017**（REV-19 四组门控；DEFECT-R19-D-01 已闭合）；**本轮独立复跑** `pytest tests -q`（380 passed / 2 skipped / 0 failed，382 collected）+ `src/scripts/selfcheck.py`（52/52） |
| **1.5.1** | **2026-10-11 用户裁决回填轮** | **2026-10-11** | **（非代理调用；PM 文书回填）** | **文书回填 + 交付物订正（对 CI 净影响 = 零）**：版本 1.5.0 → **1.5.1**；新增 §10.7 记录本轮；**未改** `.github/workflows/ci.yml`（无 step / 基线 / 门集合变更）；本文件用 HTML 注释头部 + Markdown 元数据表（**非 XML `file_header`**，ET 解析不适用）。 | 用户 2026-10-11 裁决（GR-E-007 open_item 回填 + `checklists.txt` B24/B25 订正 + `deployment_plan.md` §1.1 / §16.3 / §16.4 回填）；`docs/phase_status.md`（GR-E-007 追加） |
| **1.6.0** | **GROUP_E / REV-21** | **2026-10-17** | **INV-GROUP_E-INTELBASE-010（拟）** | **REV-21 增量（标签层同步，不新增 / 不删除 step）**：① header 补 revision=REV-21 / 版本 1.5.1→**1.6.0**；新增「REV-21 增量声明 + R21 变更面对 CI 的影响」；② **§2 阶段表基线同步**（unit 174 → **190**、integration 181 → **190**、e2e 27 → **29**、full 382 → **采集 430 / 428 passed / 2 skipped**、前端 35 → **40**）+ 新增「R21 基线同步说明」（分层实测 190+190+29+21=430；R21 测试文件清单；**2 skip 为 Windows 平台性 POSIX 权限位断言，如实登记**）；③ §3 版本门「前端零运行时 CDN」行注更新为 R21 后 40 例（版本门集合**不变**，**`bcrypt` 门保留**）；④ §7 端到端 smoke 判据改 `430`（428 passed / 2 skipped）+ 新增「R21 附加」；⑤ §8 工作流落地新增「R21 增量更新」行（含 CI 阶段 9 已含 `npm ci && npm run build && npm test`、仅**同步计数**）；⑥ **新增 §11 REV-21 增量节**（11.1 净影响 / 11.2 基线 / 11.3 迁移门：零新增缺口 + 承前结转 R18 缺口 / 11.4 版本门集合不变 / 11.5 测试文件映射 / 11.6 须部署后覆盖项）；⑦ 附自检补 R21 边界；status → REVISED_PENDING_REVIEW（待 PM 门控） | `docs/deployment_plan.md` 1.6.0/REV-21 §17；`architecture_design.md` 1.13.0/REV-21（ADR-52）；`module_design.md` 1.13.0/REV-21（IFC-IB-393 / 394）；`tech_stack.md` 1.4.1/REV-18（NO_CHANGE）；`src/ibweb/serializers.py`（`_expand_expert_nodes` / `definition_derived_summary`）；`src/frontend/src/views/ConfigPage.vue`、`src/frontend/src/api/client.ts`；`tests/{unit,integration,e2e}/test_*r21*` + `tests/integration/test_definition_config_r7.py`（仅追加断言）+ `src/frontend/tests/frontend.smoke.test.js`（用例 36~40）；`docs/test_report.md` REV-21 / §25 + `docs/phase_status.md` **GR-D-019 = PASS**；**本轮独立复跑** `pytest tests -q`（428 passed / 2 skipped / 0 failed，430 collected）+ `--collect-only` 逐层（190/190/29/21） |

> 本文件为**定义**，**未执行**；不含任何真实凭据。**1.2.0（REV-13）未连接、未触碰目标机，未 commit / push，未触发 PHASE_11**。
> **1.3.0（REV-14）边界（INV-GROUP_E-INTELBASE-005）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` / `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**（`special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`）。
> **1.4.0（REV-18）本轮边界（INV-GROUP_E-INTELBASE-006）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R18 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**（`special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`，PHASE_11 保持冻结）。本轮**仅改两个文档**：本文件（1.3.0 → **1.4.0/REV-18**）与 `docs/deployment_plan.md`（1.3.0 → **1.4.0/REV-18**）。
> **1.5.0（REV-19）本轮边界（INV-GROUP_E-INTELBASE-007）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R19 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**，**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**（PHASE_11 保持冻结）。本轮**仅改两个文档**（本文件 / `docs/deployment_plan.md`，均 1.4.0 → **1.5.0/REV-19**），**未改 `.github/workflows/ci.yml`**（R19 无 CI 逻辑改动，仅如实登记 §3.2 / §10.3）。**唯一实际运行动作 = 只读复跑 `pytest` / `selfcheck` 以核实基线数字**（不构成 CI step 增删）。
> **1.5.1（2026-10-11 用户裁决回填轮）边界（PM 文书回填，非代理调用）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 写操作 / 迁移 / `scp` / `pscp` / `rsync`；**未 commit / push / `git add`**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源文档 / `.github/workflows/ci.yml`；**未触发 PHASE_11**、**未自赋 `PRODUCTION_DEPLOY_CONFIRM`**。本轮（回填轮）**本文件仅做文书回填**（1.5.0 → **1.5.1**：header 版本 + §10.7 + 版本历史行），**对 CI 净影响 = 零**。
> **1.6.0（REV-21）本轮边界（INV-GROUP_E-INTELBASE-010，拟）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移 / `scp` / `pscp` / `rsync`；**未 commit / push / `git add`**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源文档 / `.github/workflows/ci.yml`；**未跑 Docker**；**未触发 PHASE_11**、**未自赋 `PRODUCTION_DEPLOY_CONFIRM`**。本轮**仅更新两个文档**（本文件 / `docs/deployment_plan.md`，均 1.5.1 → **1.6.0/REV-21**），另**新增** `src/deploy/checklists.txt` 条目（**仅新增**）。**本文件为本轮 CI 视角下唯一运行过的动作 = 只读引用 + 独立复跑 `pytest` / `selfcheck` 以核实基线数字**（R21 **未触发**、也未新增任何 CI step）。
