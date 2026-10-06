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
