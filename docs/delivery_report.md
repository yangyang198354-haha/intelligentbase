---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-DR-001 |
| 标题 | intelligentbase 智能知识库基座 —— 项目交付报告（REV-14 增量） |
| 产出代理 | pm-orchestrator |
| 调用 ID | REV-14：部分流程（PARTIAL_FLOW）—— INV-GROUP_B-INTELBASE-008 / INV-GROUP_C-INTELBASE-014 / INV-GROUP_D-INTELBASE-014 / INV-GROUP_E-INTELBASE-005（校验：INV-GROUP_C-VERIFY-REV14）；承 REV-13：INV-GROUP_A-005 / INV-GROUP_B-007 / INV-GROUP_C-012+013 / INV-GROUP_D-012+013 / INV-GROUP_E-004 |
| 项目 | intelligentbase |
| 阶段 | REV-14 PARTIAL_FLOW（回归缺陷修复）：GROUP_B → GROUP_C → GROUP_D → GROUP_E（PHASE_10 仅计划层）；承 REV-13 FULL_FLOW |
| 版本 | 1.1.0（REV-14 增量，2026-10-06；承接 1.0.0/REV-13） |
| status | FINAL（PM 交付报告；PHASE_11 生产部署**未执行**，按用户指令冻结待 CONFIRM） |
| 创建日期 | 2026-10-06 |
| 更新日期 | 2026-10-06 |
| 权威状态文件 | `docs/phase_status.md`（唯一权威；本报告为其摘要视图） |
---

# intelligentbase 项目交付报告（REV-13 / REV-14 增量）

## 项目概览
- **项目名**：intelligentbase（通用 RAG + 多智能体知识库基座）
- **本轮特性（REV-13）**：把既有简陋 Web 前端重构为「Claude 风格、可商用」Web；内建「用户名密码登录 + 多项目运维账户」体系（替代粘贴服务令牌）。
- **工作流模式**：FULL_FLOW（新特性轮，GROUP_A→B→C→D→E 串行逐组门控）。工作区根元素 `phase_status` 仍标注 `flow_mode="PARTIAL_FLOW" start_group="GROUP_A" end_group="GROUP_E"`——**观察项**：其语义等价于全流程 A→E，但与本轮 FULL_FLOW 表述不一致，建议后续统一（见「需用户裁定」第 6 项）。
- **开始 / 完成时间**：2026-10-06 / 2026-10-06
- **最终状态**：**DELIVERED_WITH_ISSUES** —— 全流程 11 个阶段中 PHASE_01~10 均已通过门控（PHASE_10 为计划层），**PHASE_11 生产部署按用户指令冻结未执行**；存在若干待用户裁定项与承前遗留项（见下）。

## 阶段执行摘要
| 阶段组 | 阶段 | 负责代理 | 状态 | 本轮门控决策 | 重试 | 完成时间 |
|-------|------|---------|------|-------------|------|---------|
| GROUP_A | PHASE_01 需求规格 + PHASE_02 用户故事 | requirement-analyst | **APPROVED** | GR-A-005 = PASS_WITH_CONDITIONS（REV-13 增量：REQ-FUNC-IB-28~36 + REQ-NFR-IB-15~18 + US-IB-21~29） | 0 | 2026-10-06 |
| GROUP_B | PHASE_03 架构 + PHASE_04 模块设计 + PHASE_04b 技术选型 | system-architect | **APPROVED** | GR-B-006 = PASS_WITH_CONDITIONS（ADR-18~27 + IFC-IB-309~332 + AccountStore 第 15 端口；条件 CRED-01 非阻塞） | 1 | 2026-10-06 |
| GROUP_C | PHASE_05 实现计划 + PHASE_06 代码 + PHASE_06b 代码评审 | software-developer | **APPROVED** | GR-C-009 = PASS_WITH_CONDITIONS（认证/会话/账户/前端实现，CRITICAL 0）；回修 INV-GROUP_C-INTELBASE-013（DEFECT-R13-01）经独立复跑闭合 | — | 2026-10-06 |
| GROUP_D | PHASE_07 测试计划 + PHASE_08 测试报告 + PHASE_09 用例实现 | test-engineer | **APPROVED** | GR-D-010 = PASS_WITH_CONDITIONS（condition_1 = DEFECT-R13-01 已修复并独立复跑闭合） | 0 | 2026-10-06 |
| GROUP_E | PHASE_10 CI/CD 与部署计划 | devops-engineer | **APPROVED（计划层）** | GR-E-004 = PASS_WITH_CONDITIONS（deployment_plan 1.2.0/R13 + cicd_pipeline 1.2.0/R13 + ci.yml 增量） | 0 | 2026-10-06 |
| GROUP_E | PHASE_11 生产部署 | devops-engineer | **PENDING（冻结）** | 未门控——须用户明确 `PRODUCTION_DEPLOY_CONFIRM` | — | — |

## 质量指标汇总（修复后 · 独立复跑实测）
| 指标 | 值 | 目标 | 达标 |
|-----|---|------|-----|
| 单元测试通过率 | **95 / 95 = 100%** | ≥ 80% | ✓ |
| 集成测试通过率 | **123 / 123 = 100%**（DEFECT-R13-01 修复后） | ≥ 90% | ✓ |
| E2E 关键路径 | **21 / 21 = 100%**；关键路径 US 覆盖 100% | 100% | ✓ |
| 全量 Python 用例 | **239 / 239**（unit 95 + integration 123 + e2e 21），0 fail / 0 skip / 0 xfail | — | ✓ |
| 前端冒烟（独立层） | **13 / 13**（`node --test`，含 TC-FE-007~013） | — | ✓ |
| 用例覆盖 US | US-IB-21~29 **9/9** 均有用户故事级用例 | 全覆盖 | ✓ |
| Code Review CRITICAL | **0** | 0 | ✓ |
| compileall / selfcheck | EXIT=0 / 45-45 通过 | — | ✓ |
| **CI（GitHub Actions `build & test` Python 3.12）** | 工作流已更新并含 REV-13 测试与迁移门；**尚未实测触发**（阻塞于 B-01，见下） | 全绿 | ⏳ 待确认 |

## REV-13 需求与实现覆盖
- **需求**：新增 REQ-FUNC-IB-28~36（9 条）+ REQ-NFR-IB-15~18（4 条）+ C-IB-09 + DR-09~17 + OQ-IB-09~15；功能需求 27 → **36**，非功能 14 → **18**；`[INFERRED]` 功能需求 1 条（REQ-FUNC-IB-36，1/36 ≈ 2.8% ≤ 10% 上限）。
- **架构**：新增 ADR-18~27（账户/会话落点、不透明服务端会话令牌**无 Cookie**、bcrypt 与首登强制改密、账户↔项目 1:1、与 `AuthzPolicy` 端口协作、前端重构与路由、粘贴令牌入口废除、HTTPS、迁移/种子/回滚、登录限速与审计）；新增类型化接口 IFC-IB-309~332；`AccountStore` 为第 15 个端口（13 方法）。零新模块（仍 26）、零新依赖边。
- **实现**：后端账户/会话子系统（`src/ib/core/accounts.py`、`src/ib/ledger/accounts.py`：bcrypt + SqliteAccountStore/MemoryAccountStore + seed_default_admin；`src/ibweb/accounts/{policy,throttle}.py`；`src/ibweb/{authz,views,urls,composition}.py`）；迁移 `src/deploy/migrations/003_accounts.sql`；前端 Element Plus（**本地打包，无 CDN**）+ vue-router + Claude 主题（左导航+右内容、暗/亮、中文），移除粘贴令牌入口。
- **测试**：新增 UNIT 12 / INT 18 / E2E 2 / 前端 7；Python 基线 200 → **239**。

## 交付物清单
| 文件路径 | 生成代理 | 最终版本 | 状态 |
|---------|---------|---------|------|
| `docs/requirements_spec.md` | requirement-analyst | 1.4.0 / REV-13 | APPROVED |
| `docs/user_stories.md` | requirement-analyst | 1.4.0 / REV-13 | APPROVED |
| `docs/architecture_design.md` | system-architect | 1.6.0 / REV-14（ADR-28） | APPROVED（文件头 status 仍 `DRAFT_FOR_GATE_REVIEW`，偏差 D-01，见遗留） |
| `docs/module_design.md` | system-architect | 1.6.0 / REV-14（IFC-IB-333~336） | APPROVED（同上） |
| `docs/tech_stack.md` | system-architect | 1.4.0 / REV-14（NO_CHANGE） | APPROVED（同上） |
| `docs/implementation_plan.md` | software-developer | 2.9.0 / REV-14（§21） | APPROVED |
| `docs/code_review_report.md` | software-developer | REV-14（§18；CRITICAL 0 / MAJOR 0 / MINOR 0） | APPROVED |
| `src/ib/core/{accounts,ports,types}.py`、`src/ib/config/__init__.py`、`src/ib/ledger/{accounts,schema}.py` | software-developer | REV-13 | 已实现 |
| `src/ibweb/accounts/{__init__,policy,throttle}.py`、`src/ibweb/{authz,views,urls,composition}.py` | software-developer | REV-13 | 已实现 |
| `src/deploy/migrations/003_accounts.sql` | software-developer | REV-13 | 已实现 |
| `src/deploy/nginx/intelligentbase.conf.example` | software-developer | REV-13 | 已实现 |
| `src/deploy/{env.example,checklists.txt}`、`src/scripts/selfcheck.py`、`src/requirements.txt`（+bcrypt） | software-developer | REV-13 | 已实现 |
| `src/frontend/**`（router / layouts / stores / views / styles / api / Element Plus 本地依赖） | software-developer | REV-13 | 已实现 |
| `docs/test_plan.md` | test-engineer | 1.9.0 / REV-14（§19） | APPROVED |
| `docs/test_report.md` | test-engineer | 1.10.0 / REV-14（§19） | APPROVED |
| `tests/{unit,integration,e2e}/*_r13.py`、`tests/conftest.py`、`src/frontend/tests/frontend.smoke.test.js` | test-engineer | REV-13 | 已实现 |
| `tests/integration/test_project_context_int_r14.py`（TC-INT-123~128）、`src/frontend/tests/frontend.smoke.test.js`（TC-FE-014~021） | test-engineer | REV-14 | 已实现 |
| `docs/deployment_plan.md` | devops-engineer | 1.3.0 / REV-14（§14） | APPROVED（仅计划层） |
| `docs/cicd_pipeline.md` | devops-engineer | 1.3.0 / REV-14 | APPROVED（仅计划层） |
| `.github/workflows/ci.yml` | devops-engineer | REV-14（注释层） | 已更新（Python 3.12，15 steps） |
| `src/frontend/src/stores/project.ts`（新）、`src/frontend/src/api/client.ts`、`app/env.ts`、`layouts/ConsoleLayout.vue`、`main.ts`、`src/ibweb/{views,urls}.py` | software-developer | REV-14 | 已实现 |
| `docs/phase_status.md` | pm-orchestrator | REV-14 | 权威状态文件 |

## 遗留问题
| 问题 | 来源阶段 | 严重级别 | 建议处理 |
|------|---------|---------|---------|
| DEFECT-R13-01 来源 IP 维度登录限速未生效 | GROUP_D 发现 / GROUP_C 修复 | MEDIUM | **已修复并闭合**（INV-GROUP_C-INTELBASE-013 + 独立复跑 INV-GROUP_C-VERIFY-REV13-1） |
| bcrypt pin 漂移（MINOR-R13-03）：CI/开发机实测 5.0.0 ≠ pin `>=4,<5` | GROUP_E | MEDIUM | **需用户裁定**（见下第 1 项） |
| FND-GROUP-D-03（MAJOR）承前未闭合 | GROUP_D | MAJOR | PHASE_11 前置；建议部署前修复或书面接受风险 |
| 偏差 D-01：GROUP_B 三文档 `<file_header><status>` 仍 `DRAFT_FOR_GATE_REVIEW` | GROUP_B | MINOR | 自 R1 起承前，历轮判「以 phase_status.md 为权威、不阻塞」；PHASE_11 前可回写 |
| `test_report.md` §18 同源副本（修复前快照）与现代状态差异 | GROUP_D | MINOR | **已闭合**：INV-GROUP_D-INTELBASE-013 追加 §18.11（修复后 239/239 复跑）+ file_header 升 1.9.1、§18 status → APPROVED |
| `tests/integration/test_accounts_int_r13.py` 注释陈旧（称「当前实现缺陷」） | GROUP_D | MINOR | **已闭合**：同一补丁刷新注释为「回归守卫（已修复）」；86 断言/15 用例编号未动 |
| TC-INT-119 断言失败消息字符串仍含历史措辞（属 assert 组成部分） | GROUP_D | INFO | 按「禁改断言」约束未触碰；仅用例失败时显示，不影响当前全绿；可后续窗口刷新 |
| CRED-01：未跟踪工作包 `docs/rev13_auth_ui_apply_package.md` 仍含默认口令明文 | GROUP_B | HIGH（仅提交前） | **提交前必须脱敏或删除**（不得随提交入库；该文件不在交付物清单内） |
| 开发机 Python 3.14.6（越 tech_stack 约束）/ `langchain-openai` 1.3.3（越冻结 pin） | 环境 | MEDIUM | 须在 CI / 目标机以合规版本真跑一次方为闭合 |
| 3 项 not-verified（真实 bge-m3 / onnxruntime / Qdrant / OCR 等本机不可验） | GROUP_D | INFO | 部署阶段按 `src/deploy/checklists.txt` 归档证据闭合 |

## 关键权衡与建议（PM 不代裁，供用户决策）
1. **bcrypt pin 漂移（推荐：落地 4.x 守住 pin）**。CI/开发机曾实测装到 `bcrypt 5.0.0`，与 `requirements.txt` 的 `>=4,<5` 不符；cicd 已加版本门，**在 CI 会阻断**。建议目标机/CI 显式安装 4.x（保守、与 pin 一致）；若采用放宽 pin 至允许 5.x，需先确认本实现仅用 `hashpw/gensalt/checkpw` 兼容子集的结论成立。
2. **「账户锁定优先于 IP 限速」判定顺序（推荐：接受）**。修复时为同时保住既有 TC-INT-118（锁定账户返回**统一 401**、不泄露锁定状态）与新增 TC-INT-119（IP 维度 429），必须确定顺序，代理选定「先判账户锁定、仅未锁定才走 IP 滑动窗口」。该选择与 `LoginThrottle` 既有设计一致、变更面最小，且不改变任何用户可见需求（失败 → 429；锁定账户 → 401）；代理已在 `implementation_plan.md §20.2` / `code_review_report.md §17.5` 登记备选方案。属**行为细节知悉项**，建议接受。
3. **REQ-FUNC-IB-36（`[INFERRED]`，登录失败限速）归属（推荐：确认纳入）**。该条为唯一 `[INFERRED]` 需求（占比 2.8%，合规）。因其为安全相关且实现/测试/部署计划均已就位，建议确认纳入 v1；若裁定剔除，需同步回收限速器相关实现、用例与部署项。
4. **会话续期无绝对上限（OBS-R13-02，推荐：加绝对生命周期上限）**。当前仅滑动续期，AC 未要求上限（OQ-IB-09）。建议补一个绝对最长生命周期（超期强制重登）以降低令牌长期有效风险。
5. **CRED-01（推荐：提交前脱敏）**。`docs/rev13_auth_ui_apply_package.md` 属未跟踪工作包、非交付物，但含默认口令明文；若连同提交将违反凭据纪律。建议删除或替换为 `<REPLACE_ME>` 后再提交。
6. **CI 触发与提交授权（需明确授权）**。代码与测试均在工作区**未提交**；CI（`build & test` Python 3.12）须在 commit + push 后才会实测运行。PM 无提交权限且按纪律不代为提交——是否提交/推送由用户决定。

## 开放问题（PASS_WITH_CONDITIONS 的未决条件项）
- `[ARCH-ASSUMPTION-A9]`：会话 TTL / 续期窗口 / bcrypt cost / 登录失败阈值与锁定秒数的具体取值待确认（部署前须在目标机实测 TBD-T22）。
- OQ-IB-09 / OQ-IB-11 / OQ-IB-12 / OQ-IB-13：会话续期绝对上限 / 密码策略 / 登录限速策略待用户裁定。
- C-01：目标机 DNS / 防火墙对外端口（80/443）未定，影响 nginx HTTPS 对外形态。
- 偏差 D-01（文件头 status）承前未闭合。

## REV-14 增量交付（回归缺陷修复轮 · PARTIAL_FLOW）

### 缺陷
R13 交付后回归：**全局管理员**（`users.project_id IS NULL` ⇒ `AuthzContext.project_id == GLOBAL_PROJECT`（`"*"`））因项目级端点对哨兵 fail-closed 而**无法使用任何项目级页面**（问答 / 文件管理 / 索引重建 / 可视化配置）；前端从不发送 `X-IB-Project`，且不存在「列出项目」的端点 ⇒ 管理员对唯一全局角色实际不可用。根因链（哨兵恰是唯一出口、而出口未被暴露）由用户侧先行诊断并对目标机实测佐证，本轮不重复定位。

### 设计决策（REV-14 / ADR-28）
**ADR-28 = Option B（显式选择 + 传播）**——全局 admin 显式选择「当前项目」，前端在**单一注入点**把它作为 `X-IB-Project` 头随**所有项目级请求（含 SSE）**发出；`ops` 账户的项目边界由账户承载，**结构上不可切换**；未选定项目时**不伪造头**，保持后端 fail-closed（未选项目即不泄露）。Option A（服务端隐式默认）被吸收为前端「单项目预选」便利；Option C（哨兵→并集/故障开放）与 Option D（绑定 admin 到单项目）被拒。

### 变更增量
- **后端**：新增非项目级端点 `GET /api/projects`（IFC-IB-333）——数据源 = 组合根 `Deps.projects`；admin 见全部、ops 仅自身（恒 1 项）；未确定项目的全局主体亦返回 200（fail-closed 的唯一引导出口）；`?token=` 仍 4xx、零 Set-Cookie。**零新表 / 零 ORM / 零迁移 / 零新依赖 / 零新 env 键。**
- **前端**：新增 `src/frontend/src/stores/project.ts`（IFC-IB-335）；`client.ts` `headers()` 单点注入 `X-IB-Project`（IFC-IB-336，自动覆盖 `chatStream` / `chatResume` 两处 SSE）；控制台项目选择器（仅 admin 可改选）+ `<router-view :key>` 视图态重置 + 401 清空。
- **契约**：新增 IFC-IB-333~336（纯追加）；`IFC-IB-001~332` 未改；`src/ibweb/authz.py` 零改动（头语义为 R13 既有）；模块仍 26 / 端口仍 15。

### 门控（均 PASS_WITH_CONDITIONS）
| 阶段组 | 门控 | 结论 |
|-------|------|------|
| GROUP_B | GR-B-007 | PASS_WITH_CONDITIONS（ADR-28 4 方案；IFC-IB-333~336；无环、零新模块/端口/边；条件 CRED-01） |
| GROUP_C | GR-C-010 | PASS_WITH_CONDITIONS（26/26 模块已实现 / CRITICAL 0；独立只读 verifier 五组全 CONFIRMED、零 REFUTED） |
| GROUP_D | GR-D-011 | PASS_WITH_CONDITIONS（unit 100% / integration 100% / E2E 100% / 算术一致；新增 Python 3 + 前端 4） |
| GROUP_E | GR-E-005 | PASS_WITH_CONDITIONS（仅 PHASE_10 计划层：零迁移 / 每步有回滚 / 验证覆盖；PHASE_11 冻结） |

### 质量指标（独立实跑实测）
| 指标 | 值 | 目标 | 达标 |
|-----|---|------|-----|
| 单元测试通过率 | 95 / 95 = **100%** | ≥80% | ✓ |
| 集成测试通过率 | 129 / 129 = **100%** | ≥90% | ✓ |
| E2E 关键路径 | 21 / 21 = **100%** | 100% | ✓ |
| 全量 Python 用例 | **245 / 245**（unit 95 + integration 129 + e2e 21），0 fail / 0 skip | — | ✓ |
| 前端冒烟（独立层） | **21 / 21**（`node --test`，含 TC-FE-014~021） | — | ✓ |
| selfcheck / compileall / typecheck | 47/47 / EXIT=0 / EXIT=0 | — | ✓ |
| Code Review CRITICAL | **0** | 0 | ✓ |

### 第 1 步交付物（本轮）
`docs/architecture_design.md` 1.6.0/REV-14（ADR-28）、`docs/module_design.md` 1.6.0/REV-14（IFC-IB-333~336）、`docs/tech_stack.md` 1.4.0/REV-14（NO_CHANGE）、`docs/implementation_plan.md` 2.9.0/REV-14、`docs/code_review_report.md` §18、`docs/test_plan.md` 1.9.0/REV-14、`docs/test_report.md` 1.10.0/REV-14、`docs/deployment_plan.md` 1.3.0/REV-14、`docs/cicd_pipeline.md` 1.3.0/REV-14、`.github/workflows/ci.yml`（注释层）；代码 `src/frontend/src/stores/project.ts`（新）+ `client.ts` / `app/env.ts` / `ConsoleLayout.vue` / `main.ts` + `src/ibweb/{views,urls}.py`；测试 `tests/integration/test_project_context_int_r14.py` + 前端冒烟用例。

### 需用户裁定 / 知悉
1. **CRED-01（提交前必办，自 GR-B-007 结转）**：R14 改动集（含未跟踪工作包 `docs/rev14_project_context_apply_package.md`）仍在工作区未提交；**提交时不得把未跟踪工作包按原样纳入**（脱敏或删除）。PM 无提交权限，按纪律不代为提交。
2. **实测口径更正**：原缺陷表述「项目级页面全部 503」不完全准确——实测未选项目的 admin 命中 `/api/config/definition` = **503**、`/api/files` GET = **200（items 空）**、`/api/chat/stream` 与 `/api/rebuild` = **500**（`orchestrator_for` 抛 `StartupError`，`views.error_response` 把 IbError 统一映射 500）。**fail-closed 仍成立**（不返回任何项目数据），**非 R14 引入**（R13 既有）。
3. **R14-OBS-01（LOW）**：`client.ts` `headers()` 的「extra 不覆盖项目头」不变式仅在 provider 非空时成立；建议实现侧显式剔除 extra 中的 `X-IB-Project`（非本轮）。
4. **R14-OBS-03（LOW，与 R14 无关）**：`GET /api/files?status=<非法值>` 返回 500 而非 400。
5. **R14-L-01（not-verifiable）**：真实浏览器 `el-select` 端到端交互在离线层不可验证；已由行为层真跑（TC-FE-017~021）+ 结构断言（TC-FE-016）覆盖安全相关不变量，浏览器渲染/交互现象登记为残余不可验证项。
6. **OPEN ITEM**：`GET /api/projects` 与项目选择 UX 无独立 REQ/AC，本轮映射既有 AC-IB-24-02/03 / REQ-FUNC-IB-31/IB-23（**不发明需求**）。
7. **PHASE_11 解冻**：生产部署须用户明确下达 `PRODUCTION_DEPLOY_CONFIRM=true`（当次有效）；承前 P0 前置（B-01 git 仓库/remote 等）与 B-04/FND-GROUP-D-03、B-05/B-06 待闭合。

## 最终状态
**DELIVERED_WITH_ISSUES** —— REV-14（回归缺陷修复轮，PARTIAL_FLOW：GROUP_B → C → D → E）四组门控全部通过（GR-B-007 / GR-C-010 / GR-D-011 / GR-E-005，均为 PASS_WITH_CONDITIONS），REV-14 的设计、实现、测试与部署计划均已交付且经独立只读复核与独立实跑证实（Python 245/245 + 前端 21/21）；**PHASE_11 生产部署按用户指令冻结未执行**。承载前遗留项（bcrypt pin / `[INFERRED]` 需求 / TTL 阈值 / 偏差 D-01 / FND-GROUP-D-03 / 环境版本）并新增本轮开放项（CRED-01 提交前脱敏、R14-OBS-01/02/03、R14-L-01），故判 DELIVERED_WITH_ISSUES 而非 DELIVERED。

---

# REV-20 收口段（2026-10-17）

> **注**：本文件 file_header 仍标注 REV-14（历史增量）—— REV-16 ~ REV-20 的增量未逐轮回写本摘要视图。
> **权威状态一律以 `docs/phase_status.md` 为准**（见 GR-A-012 / GR-B-012 / GR-C-016 / GR-D-018 / GR-E-008）。

## §R20.1 交付范围与依据

用户诉求（2026-10-17，REV-20）：① 默认 `kb-agent` 按 agent-builder 意见优化；② 删除代码里的提示词，改为新建项目目录默认落盘并使其工作；③ 取消默认三专家机制（新建项目只有一个通用 `kb-agent`）。

依据：`requirements_spec.md` / `user_stories.md`（1.12.0 / REV-20；OQ-IB-41=B / 42=B / 43=C / 44=C / 45=C / 46=B / 47=C / 48=C；约束 C-IB-52）+ `architecture_design.md`（1.12.0 / REV-20，ADR-48 ~ 51）+ `module_design.md`（1.12.0 / REV-20，IFC-IB-389 ~ 392）。

## §R20.2 交付物（提交引用）

| 类别 | 内容 | 提交 |
|------|------|------|
| 代码 | `ib/experts`（安全网 + 三专家退役）、`ib/config/prompts`（两层 fail-closed + `kb_agent_seed_prompt`）、`ib/config/definition`（legacy 键一律 fail-closed）、`ib/core/{ports,types}`、`ibweb/composition`（创建期落盘 + 回填迁移 + `prompt_source` 日志）、`ibweb/views`、`ib/observability`、`ib/llm`、`ib/orchestration`、`ib/streaming` | `ea51c97` |
| 资产 | `src/ib/expert_seeds/kb-agent.md`（9 层架构提示词种子，8514B） | `ea51c97` |
| 脚本 | `src/scripts/backfill_prompts.py`（IFC-IB-391 入口，用户手工执行） | `ea51c97` |
| 清单 | `src/deploy/checklists.txt` 新增 **[B26]**（签署行 → `B1–B26`） | `ea51c97` |
| 前端 | `client.ts`（删 `builtin_fallback`）/ `ConfigPage.vue`（删内置兜底回显 + 回退链第三值 → `prompt_missing`）/ `frontend.smoke.test.js`（第 29 例翻转） | `ea51c97` |
| 测试 | 16 个既有测试文件 + `src/scripts/selfcheck.py` 按新契约逐条改写 | `ea51c97` |
| 文档 | 需求 / 架构 / 模块 / 实现计划（§27）/ phase_status（GR-C-016 / GR-D-018 / GR-E-008） | `ea51c97` / `18d1bb5` |
| 本段 | `docs/delivery_report.md` 追加 REV-20 收口段 | 见本次收口提交 |

## §R20.3 契约翻转清单（八条）

1. 「两层皆缺」由「回落代码内置兜底」→ **`PromptNotFoundError(code="prompt_missing")` fail-closed**；
2. `resolved_from` 值域由 `{main_file, fallback_file, builtin_fallback}` → **`{main_file, fallback_file}`**；
3. 内置注册表由三对齐专家 → **唯一通用 `kb-agent`**（`builtin_expert_registry()` ≡ `builtin_default_registry()`，`demo` 亦改 kb-agent）；
4. legacy `experts[].fallback_prompt` 由「与内置逐字比对后分级」→ **一律 fail-closed**；
5. `GET /api/config/prompts` 专家条目键集由 `{name, cn_label, layers, builtin_fallback}` → **`{name, cn_label, layers}`**；
6. 新增专家由「无需提示词文件即可保存 / 装配」→ **必须先在项目提示词目录落盘 `main.md` / `fallback.md`**；
7. `migrate_expert_history` 的 `experts` 默认值 → **空元组**（迁移口径停用，显式传参能力保留）；
8. `fallback_prompts()` / `ExpertSpec.fallback_prompt` **去驱动化**（恒空串，不参与运行期取值）。

## §R20.4 验证证据

### 本机（提交前）
```
python -m pytest tests -q        →  403 passed / 2 skipped / 0 failed（收集 405）
python src/scripts/selfcheck.py  →  52/52 通过（EXIT 0）
node --test frontend.smoke…      →  35 pass / 0 fail
```
逐层：unit 169/169 = **100.00%**（2 skipped 为既有）、integration 186/186 = **100.00%**、e2e 27/27（关键路径）**100%**。被退役符号（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `DEMO_EXPERT_NAMES` / `_DEFAULT_SPECS`）全仓**零引用**。

### 生产（192.168.31.133）
| 断言 | 结果 |
|------|------|
| `ActiveState` / `SubState` | ib-web = active / running；ib-worker = active / running（ib-embed 未触碰） |
| `NRestarts` | ib-web = **0**；ib-worker = **0** |
| journal | `Started ib-web.service`；`{"stage": "startup", "outcome": "succeeded"}` |
| `GET /healthz/deps` / `GET /healthz` | **200** / **200**（qdrant ok / embed ok / llm ok / egress 已声明） |
| 来源可核验（IFC-IB-392） | ib-web 与 ib-worker 各一条 `{"stage": "prompt_source", "outcome": "resolved_from", "expert": "kb-agent", "source": "main_file"}` |
| 端到端（OQ-IB-45=C） | **用户 UI 复核通过**：项目 `New` 提问命中已上传资料、答复带引用来源 |

## §R20.5 生产部署执行记录

1. **备份（回滚点）**：`/root/ib-rev20-backup_20261017_153448/`（`/var/lib/intelligentbase` 全量 tar 341KB + `ib-web.env` + `config.json`）。
2. **只读检查结论**：注册表**仅 `New` 为 `active`**（`demo` / `Freeark` 均 `disabled`，不参与装配）；`IB_EXPERT_PROMPT_DIR=/var/lib/intelligentbase/prompts` 与 `IB_DEFINITION_DOC_PATH=/var/lib/intelligentbase` 为不同值；`IB_EXPERT_PROMPT_ENABLED` 未设 → 默认**启用**（fs 模式）。唯一硬阻塞 = `New` 的定义文档列 `kb-agent` 但 `prompts/New/kb-agent/` 为空。
3. **停服窗口（一次收敛）**：`git pull`（→ 代码面 `ea51c97`）→ `systemctl stop ib-web ib-worker` → 回填 → `systemctl start ib-web ib-worker`。
4. **回填**：`sudo -u ib-web … backfill_prompts.py --prompt-root /var/lib/intelligentbase/prompts --projects New` → `New: created`；产物 `prompts/New/kb-agent/main.md`（8514B，`0640 ib-web:ib`）。**以服务账号执行是必须的**（`_atomic_write` 经 `mkstemp` 0600；以 root 执行会写出 `root:ib 0600` → 服务读不到）。
5. **刻意未做**：未对 `demo` / `Freeark` 回填提示词（二者 `disabled` 且文档不含 `kb-agent`，写入即成孤儿文件 → 日后启用即 fail-fast）。
6. **收尾纪律**：临时授权 `/etc/sudoers.d/90-ib-temp` 与 `/tmp` 检查脚本已删除；未读取 / 未回显任何口令或 Key 字面量；未 push 任何生产侧改动。

## §R20.6 回滚方案

```
sudo tar -C /var/lib -xzf /root/ib-rev20-backup_20261017_153448/intelligentbase.tar.gz
sudo chown -R ib-web:ib /var/lib/intelligentbase
git -C /opt/intelligentbase checkout 8b5755f
sudo systemctl restart ib-web ib-worker
```

## §R20.7 开放项与残留风险（均非阻塞）

1. **`demo` 项目**：仍为 FreeArk 三专家 + 带 legacy `fallback_prompt` 键（OQ-IB-47=C 要求「demo 改 kb-agent」）。因其 `disabled` 不参与装配，当前无运行期影响。**若日后启用**，须先 ① 迁移三个 `fallback_prompt` 文本为提示词目录文件；② 专家集改为 `kb-agent`（或落盘其提示词文件），否则启动即 `ConfigError` / `prompt_missing`。
2. **`ib-worker.env` 未设 `IB_DEFINITION_DOC_PATH`**：worker 启动打 `path_not_configured_using_in_memory_default`（warning 级）并使用内存默认定义文档；既有常态，不影响其取用 fs 提示词与开工。
3. **新增专家工作流已变更**：现在必须先落盘提示词文件再登记专家（代码兜底不再兜底），属 ADR-48 的**预期从严**行为。

## §R20.8 门控汇总

| 阶段 | 门控 | 结论 |
|------|------|------|
| GROUP_A | GR-A-012 | PASS（八处 OQ 裁决闭合） |
| GROUP_B | GR-B-012 | PASS_WITH_CONDITIONS（ADR-48 ~ 51 + IFC-IB-389 ~ 392） |
| GROUP_C | GR-C-016 | PASS_WITH_CONDITIONS（实现 + 八条契约翻转 + 3 处计划外必要增量） |
| GROUP_D | GR-D-018 | PASS_WITH_CONDITIONS（403 passed / 2 skipped，三层 100%） |
| GROUP_E | GR-E-008 | **PASS**（部署已执行 + 用户 UI 验收通过；唯一条件已闭合） |

## §R20.9 最终状态（REV-20）

**DELIVERED** —— REV-20 三组门控（GR-B-012 / GR-C-016 / GR-D-018）与 GROUP_E 部署门控（GR-E-008，条件闭合后升为 PASS）全部通过；代码、资产、脚本、清单、前端、测试与文档全部落地并推送（`ea51c97` / `18d1bb5`）；**生产部署已执行并通过严格断言，端到端问答已由用户 UI 复核验收**；PHASE_11 由冻结转为 **APPROVED**。残留开放项 3 条（`demo` 启用前置、worker env 现状、新增专家工作流从严）均为**非阻塞且有明确处置办法**。


---

# REV-20 收口段（2026-10-17）

> **注**：本文件 file_header 仍标注 REV-14（历史增量）—— REV-16 ~ REV-20 的增量未逐轮回写本摘要视图。
> **权威状态一律以 `docs/phase_status.md` 为准**（见 GR-A-012 / GR-B-012 / GR-C-016 / GR-D-018 / GR-E-008）。

## §R20.1 交付范围与依据

用户诉求（2026-10-17，REV-20）：① 默认 `kb-agent` 按 agent-builder 意见优化；② 删除代码里的提示词，改为新建项目目录默认落盘并使其工作；③ 取消默认三专家机制（新建项目只有一个通用 `kb-agent`）。

依据：`requirements_spec.md` / `user_stories.md`（1.12.0 / REV-20；OQ-IB-41=B / 42=B / 43=C / 44=C / 45=C / 46=B / 47=C / 48=C；约束 C-IB-52）+ `architecture_design.md`（1.12.0 / REV-20，ADR-48 ~ 51）+ `module_design.md`（1.12.0 / REV-20，IFC-IB-389 ~ 392）。

## §R20.2 交付物（提交引用）

| 类别 | 内容 | 提交 |
|------|------|------|
| 代码 | `ib/experts`（安全网 + 三专家退役）、`ib/config/prompts`（两层 fail-closed + `kb_agent_seed_prompt`）、`ib/config/definition`（legacy 键一律 fail-closed）、`ib/core/{ports,types}`、`ibweb/composition`（创建期落盘 + 回填迁移 + `prompt_source` 日志）、`ibweb/views`、`ib/observability`、`ib/llm`、`ib/orchestration`、`ib/streaming` | `ea51c97` |
| 资产 | `src/ib/expert_seeds/kb-agent.md`（9 层架构提示词种子，8514B） | `ea51c97` |
| 脚本 | `src/scripts/backfill_prompts.py`（IFC-IB-391 入口，用户手工执行） | `ea51c97` |
| 清单 | `src/deploy/checklists.txt` 新增 **[B26]**（签署行 → `B1–B26`） | `ea51c97` |
| 前端 | `client.ts`（删 `builtin_fallback`）/ `ConfigPage.vue`（删内置兜底回显 + 回退链第三值 → `prompt_missing`）/ `frontend.smoke.test.js`（第 29 例翻转） | `ea51c97` |
| 测试 | 16 个既有测试文件 + `src/scripts/selfcheck.py` 按新契约逐条改写 | `ea51c97` |
| 文档 | 需求 / 架构 / 模块 / 实现计划（§27）/ phase_status（GR-C-016 / GR-D-018 / GR-E-008） | `ea51c97` / `18d1bb5` |
| 本段 | `docs/delivery_report.md` 追加 REV-20 收口段 | 见本次收口提交 |

## §R20.3 契约翻转清单（八条）

1. 「两层皆缺」由「回落代码内置兜底」→ **`PromptNotFoundError(code="prompt_missing")` fail-closed**；
2. `resolved_from` 值域由 `{main_file, fallback_file, builtin_fallback}` → **`{main_file, fallback_file}`**；
3. 内置注册表由三对齐专家 → **唯一通用 `kb-agent`**（`builtin_expert_registry()` ≡ `builtin_default_registry()`，`demo` 亦改 kb-agent）；
4. legacy `experts[].fallback_prompt` 由「与内置逐字比对后分级」→ **一律 fail-closed**；
5. `GET /api/config/prompts` 专家条目键集由 `{name, cn_label, layers, builtin_fallback}` → **`{name, cn_label, layers}`**；
6. 新增专家由「无需提示词文件即可保存 / 装配」→ **必须先在项目提示词目录落盘 `main.md` / `fallback.md`**；
7. `migrate_expert_history` 的 `experts` 默认值 → **空元组**（迁移口径停用，显式传参能力保留）；
8. `fallback_prompts()` / `ExpertSpec.fallback_prompt` **去驱动化**（恒空串，不参与运行期取值）。

## §R20.4 验证证据

### 本机（提交前）
```
python -m pytest tests -q        →  403 passed / 2 skipped / 0 failed（收集 405）
python src/scripts/selfcheck.py  →  52/52 通过（EXIT 0）
node --test frontend.smoke…      →  35 pass / 0 fail
```
逐层：unit 169/169 = **100.00%**（2 skipped 为既有）、integration 186/186 = **100.00%**、e2e 27/27（关键路径）**100%**。被退役符号（`BUILTIN_FALLBACK_DEFAULT` / `BUILTIN_FALLBACKS` / `DEMO_EXPERT_NAMES` / `_DEFAULT_SPECS`）全仓**零引用**。

### 生产（192.168.31.133）
| 断言 | 结果 |
|------|------|
| `ActiveState` / `SubState` | ib-web = active / running；ib-worker = active / running（ib-embed 未触碰） |
| `NRestarts` | ib-web = **0**；ib-worker = **0** |
| journal | `Started ib-web.service`；`{"stage": "startup", "outcome": "succeeded"}` |
| `GET /healthz/deps` / `GET /healthz` | **200** / **200**（qdrant ok / embed ok / llm ok / egress 已声明） |
| 来源可核验（IFC-IB-392） | ib-web 与 ib-worker 各一条 `{"stage": "prompt_source", "outcome": "resolved_from", "expert": "kb-agent", "source": "main_file"}` |
| 端到端（OQ-IB-45=C） | **用户 UI 复核通过**：项目 `New` 提问命中已上传资料、答复带引用来源 |

## §R20.5 生产部署执行记录

1. **备份（回滚点）**：`/root/ib-rev20-backup_20261017_153448/`（`/var/lib/intelligentbase` 全量 tar 341KB + `ib-web.env` + `config.json`）。
2. **只读检查结论**：注册表**仅 `New` 为 `active`**（`demo` / `Freeark` 均 `disabled`，不参与装配）；`IB_EXPERT_PROMPT_DIR=/var/lib/intelligentbase/prompts` 与 `IB_DEFINITION_DOC_PATH=/var/lib/intelligentbase` 为不同值；`IB_EXPERT_PROMPT_ENABLED` 未设 → 默认**启用**（fs 模式）。唯一硬阻塞 = `New` 的定义文档列 `kb-agent` 但 `prompts/New/kb-agent/` 为空。
3. **停服窗口（一次收敛）**：`git pull`（→ 代码面 `ea51c97`）→ `systemctl stop ib-web ib-worker` → 回填 → `systemctl start ib-web ib-worker`。
4. **回填**：`sudo -u ib-web … backfill_prompts.py --prompt-root /var/lib/intelligentbase/prompts --projects New` → `New: created`；产物 `prompts/New/kb-agent/main.md`（8514B，`0640 ib-web:ib`）。**以服务账号执行是必须的**（`_atomic_write` 经 `mkstemp` 0600；以 root 执行会写出 `root:ib 0600` → 服务读不到）。
5. **刻意未做**：未对 `demo` / `Freeark` 回填提示词（二者 `disabled` 且文档不含 `kb-agent`，写入即成孤儿文件 → 日后启用即 fail-fast）。
6. **收尾纪律**：临时授权 `/etc/sudoers.d/90-ib-temp` 与 `/tmp` 检查脚本已删除；未读取 / 未回显任何口令或 Key 字面量；未 push 任何生产侧改动。

## §R20.6 回滚方案

```
sudo tar -C /var/lib -xzf /root/ib-rev20-backup_20261017_153448/intelligentbase.tar.gz
sudo chown -R ib-web:ib /var/lib/intelligentbase
git -C /opt/intelligentbase checkout 8b5755f
sudo systemctl restart ib-web ib-worker
```

## §R20.7 开放项与残留风险（均非阻塞）

1. **`demo` 项目**：仍为 FreeArk 三专家 + 带 legacy `fallback_prompt` 键（OQ-IB-47=C 要求「demo 改 kb-agent」）。因其 `disabled` 不参与装配，当前无运行期影响。**若日后启用**，须先 ① 迁移三个 `fallback_prompt` 文本为提示词目录文件；② 专家集改为 `kb-agent`（或落盘其提示词文件），否则启动即 `ConfigError` / `prompt_missing`。
2. **`ib-worker.env` 未设 `IB_DEFINITION_DOC_PATH`**：worker 启动打 `path_not_configured_using_in_memory_default`（warning 级）并使用内存默认定义文档；既有常态，不影响其取用 fs 提示词与开工。
3. **新增专家工作流已变更**：现在必须先落盘提示词文件再登记专家（代码兜底不再兜底），属 ADR-48 的**预期从严**行为。

## §R20.8 门控汇总

| 阶段 | 门控 | 结论 |
|------|------|------|
| GROUP_A | GR-A-012 | PASS（八处 OQ 裁决闭合） |
| GROUP_B | GR-B-012 | PASS_WITH_CONDITIONS（ADR-48 ~ 51 + IFC-IB-389 ~ 392） |
| GROUP_C | GR-C-016 | PASS_WITH_CONDITIONS（实现 + 八条契约翻转 + 3 处计划外必要增量） |
| GROUP_D | GR-D-018 | PASS_WITH_CONDITIONS（403 passed / 2 skipped，三层 100%） |
| GROUP_E | GR-E-008 | **PASS**（部署已执行 + 用户 UI 验收通过；唯一条件已闭合） |

## §R20.9 最终状态（REV-20）

**DELIVERED** —— REV-20 三组门控（GR-B-012 / GR-C-016 / GR-D-018）与 GROUP_E 部署门控（GR-E-008，条件闭合后升为 PASS）全部通过；代码、资产、脚本、清单、前端、测试与文档全部落地并推送（`ea51c97` / `18d1bb5`）；**生产部署已执行并通过严格断言，端到端问答已由用户 UI 复核验收**；PHASE_11 由冻结转为 **APPROVED**。残留开放项 3 条（`demo` 启用前置、worker env 现状、新增专家工作流从严）均为**非阻塞且有明确处置办法**。


---

# §R21 REV-21 交付报告（可视化配置「编排图」实显项目已配置的专家）

> 追加式；不影响上文历史结论。日期 2026-10-17。用户诉求：「可视化配置的编排图要实际抵显示配置的专家。不能用一个"expert" 代替」；用户裁决「全部按推荐（A）」，并授权「commit + push 然后部署」。

## §R21.1 需求与设计要点

- **问题**：编排图由定义文档 `orchestration` 派生，而**定义文档与运行期 LangGraph 均以单一结构节点 `expert` 表达全部专家**（运行期由 `_fan_out` 以 `Send("expert", …)` 扇出同名节点多实例），故界面专家方块**恒为字面量 `expert`**，与项目实际专家集无关。
- **决定（ADR-52）**：改动面收在**显示投影层**（Option A；B 前端层展开 / C 定义文档承载 / D 运行期多节点 均**已评估未采纳** —— C 违反 OQ-IB-52=A 与 C-IB-56①，D 违反 C-IB-54）。
- **契约（IFC-IB-393 / 394）**：① `definition_derived_summary` 按 `view.experts` **逐专家展开** `nodes` / `conditional_edges` / `edges`，并新增 `derived.experts`（`name`/`cn_label`/`is_default`）；② 前端节点标签取 `cn_label`、专家节点加 `graph-expert` class 与图例、**仍只读**。
- **纪律**：**未动**运行期编排拓扑、`derive()`、`DerivedView`、定义文档 schema ⇒ **既有定义文档零迁移**；信封顶层键与 `config_key_names` 不变；撞名结构节点 / `START` / `END` ⇒ **显式报错（不静默改名）**；无新第三方依赖。
- **变更面**：源码 4 文件（`src/ibweb/serializers.py` / `src/ibweb/views.py` / `ConfigPage.vue` / `api/client.ts`）+ 测试（新增 unit 19 / integration 4 / e2e 2 / 前端 5）+ 文档 12 份（含检查清单新增 `[B27]`）。本地实跑：pytest **428 passed / 2 skipped**、selfcheck **52/52**、前端 **40/40**、typecheck / build EXIT 0。

## §R21.2 门控汇总

| 阶段 | 门控 | 结论 |
|------|------|------|
| GROUP_A | GR-A-013 | **PASS**（OQ-IB-49 ~ OQ-IB-56 全部采纳推荐默认 A；条件闭合） |
| GROUP_B | GR-B-013 | PASS_WITH_CONDITIONS（ADR-52 + §2.0.12 + IFC-IB-393/394） |
| GROUP_C | GR-C-017 | PASS_WITH_CONDITIONS（CRITICAL 0 / MAJOR 0） |
| GROUP_D | GR-D-019 | **PASS**（12 组 AC 全覆盖；三层 100%/100%/100%） |
| GROUP_E（PHASE_10） | GR-E-009 | PASS_WITH_CONDITIONS（仅计划） |
| GROUP_E（PHASE_11） | GR-E-010 | PASS_WITH_CONDITIONS（**部署已执行 + 严格断言通过**；条件 = 用户 UI 复核） |

## §R21.3 生产部署执行记录（2026-10-17）

- **提交**：`7bfdf3f`（父 `bc0ef6d`），已 push `origin/main`（经本机 SOCKS5 代理 `127.0.0.1:10808`；HTTP 代理模式报 TLS eof，改 `socks5h://` 成功）。
- **DEPLOY-041**：`/opt/intelligentbase` `git pull` → HEAD = **7bfdf3f**；REV-21 代码在树（`_expand_expert_nodes` / `DerivedExpertEntry` / `graph-expert` grep 命中）。
- **DEPLOY-043**：`src/frontend` `npm ci` + `npm run build` 成功 → `rsync -a --delete dist/ /var/www/intelligentbase/`（产物 19:49，asset 哈希更新，`vendor-flow` 保留）。
- **DEPLOY-042**：`sudo -n systemctl restart ib-web`、`sudo -n systemctl restart ib-worker`（**须逐条命令**；免密 sudoers 只匹配单条 unit）→ `rc=0`。
- **DEPLOY-044 严格断言（全 PASS）**：三单元 `active` + `running` + `NRestarts=0`；`/healthz=200`、`/healthz/deps=200`；`GET /api/config/definition` = **401**（路由存活、鉴权正常）；`startup` 命中 16 行、`prompt_source` 命中（ib-web 2 / ib-worker 1）⇒ REV-20 来源可核验未被破坏。
- **回滚锚点**：代码 = `git checkout bc0ef6d` + 重启两单元；前端 = **旧产物未备份**（`/var/www` 不可写致同级 `cp` 失败）⇒ 回退代码后重新 `npm ci && npm run build` 并发布（git 可完整重建）。**如实登记**。
- **边界**：**无 schema 迁移 / 无数据变更 / 无新 env 键**；未读取或回显凭据；未用临时 sudo 授权文件。

## §R21.4 最终状态（REV-21）

**DELIVERED** —— 用户 **2026-10-17 UI 复核「确认无误」**：可视化配置页的编排图**逐专家成节点**、**不再只有一个 `expert` 方块**（AC-IB-51-01 ~ 51-03 视觉观感已由用户确认）。代码已推送（`7bfdf3f` / `c815aa6`）、生产已部署并通过全部严格断言；**GR-E-010 唯一条件闭合 ⇒ 升为 PASS**，**PHASE_11 = APPROVED**（已执行 + 已验收）。REV-21 全流程（GROUP_A → GROUP_E）收口。

> **残留开放项（非阻塞，承前）**：① `demo` 仍为三专家 + legacy `fallback_prompt`（disabled，启用前须先迁移）；② `ib-worker.env` 未设 `IB_DEFINITION_DOC_PATH`（既有常态）；③ `deployment_plan.md` 未补登 REV-20 部署步骤（本轮自 DEPLOY-041 续编号）；④ 前端旧 dist 未备份（回滚依赖 git 重建）。
