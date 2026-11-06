<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-06T21:42:57+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>requirements_spec.md</file><file>user_stories.md</file><file>architecture_design.md</file><file>module_design.md</file><file>tech_stack.md</file><file>implementation_plan.md</file><file>code_review_report.md</file><file>test_plan.md</file><file>unit_test_report.md</file><file>integration_test_report.md</file><file>e2e_test_report.md</file><file>cicd_pipeline.md</file><file>deployment_plan.md</file></input_files>
  <phase>PHASE_01,PHASE_02,PHASE_03,PHASE_04,PHASE_05,PHASE_06,PHASE_07,PHASE_08,PHASE_09,PHASE_10,PHASE_11a</phase>
  <status>DRAFT</status>
</file_header>

# REV-29 交付报告：Agent 工具调用的 MCP 适配

## 项目概览
- 需求一句话：给 agent 工具调用加 MCP 适配，对标 MCP 业务流程，支持外部工具的登记、变更、删除、查询，并做好安全控制和调用管理。
- 模式：INCREMENTAL，基线 HEAD b4fa3a3；画像 1.1.0（APPROVED）。
- 起止：2026-11-05T10:43:45+08:00 → 2026-11-06T21:42:57+08:00。
- 最终状态：**DELIVERED_WITH_ISSUES**。已完成到 E1 部署计划，E2 未授权（子代理模式止于 E1）。另有人工验证项、开放条件和本机未执行的 Fernet 契约用例。

## 阶段执行摘要
| GROUP | 阶段 | 代理 | 状态 | 门控（最后一次） | 重试 | 回流 | 完成时间 |
|---|---|---|---|---|---|---|---|
| A | PHASE_01-02 | requirement-analyst | APPROVED（3.0.0） | GR-A-003 PASS_WITH_CONDITIONS | 0 | — | 2026-11-06T21:10 |
| B | PHASE_03-04 | system-architect | APPROVED（2.0.0） | GR-B-002 PASS_WITH_CONDITIONS | 0 | — | 2026-11-05T15:24 |
| C | PHASE_05-06 | software-developer | APPROVED（4.0.0） | GR-C-006 PASS_WITH_CONDITIONS | 2 | 3 | 2026-11-06T21:24 |
| D | PHASE_07-09 | test-engineer | APPROVED（2.0.0） | GR-D-004 PASS_WITH_CONDITIONS | 0 | 3（第 3 轮由用户经 CP-002 Q1=A 额外授权） | 2026-11-06T21:33 |
| E1 | PHASE_10-11a | devops-engineer | APPROVED（2.0.0） | GR-E1-002 PASS_WITH_CONDITIONS | 0 | — | 2026-11-06T21:42 |
| E2 | PHASE_11b | devops-engineer | NOT_AUTHORIZED | — | — | — | — |

进度：11/12 阶段完成，PHASE_11b 未执行。

## 质量指标（baseline 模式；数值来自 PM 亲自复跑，GR-D-004，2026-11-06）
| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 单元：相对基线新增失败 | 0（1091 passed / 6 skipped） | 0 | 是 |
| 集成：相对基线新增失败 | 0（578 passed） | 0 | 是 |
| E2E critical path 通过率 | 11/11 = 1.00；Must Have 覆盖 23/23（替代口径：HTTP/SSE 多步旅程） | 1.00 | 是 |
| 代码评审未解决 CRITICAL | 0 | 0 | 是 |
| 全量回归新增失败 | 0（1761 passed / 6 skipped；基线 REV-28 1358 passed） | 0 | 是 |
| selfcheck | 76/77（core_framework_free 为基线既有，开发机 sitecustomize 引起） | 零新增 | 是 |
| 前端 npm test | 180/180 | 零新增 | 是 |

6 个 SKIP 都是 Fernet 契约用例：本机未装 cryptography。CI 设了 IB_REQUIRE_CRYPTO=1，会强制运行这些用例，但 CI 还没跑过。

## 交付物清单
| 文件 | 生成代理 | 最终版本 | 状态 |
|---|---|---|---|
| requirements_spec.md / user_stories.md | requirement-analyst | 3.0.0 | APPROVED |
| architecture_design.md / module_design.md / tech_stack.md | system-architect | 2.0.0 | APPROVED |
| implementation_plan.md / code_review_report.md | software-developer | 4.0.0 | APPROVED |
| test_plan.md / unit_test_report.md / integration_test_report.md / e2e_test_report.md | test-engineer | 2.0.0 | APPROVED |
| cicd_pipeline.md / deployment_plan.md | devops-engineer | 2.0.0 | APPROVED |
| pm_escalation_GROUP_D_20261105T2341.md | pm-orchestrator | 0.1.0 | DRAFT（上报已由 CP-002 处置） |
| archive/rev28/ | pm-orchestrator | REV-28 全套 | SUPERSEDED（归档） |

代码改动全部未提交，需主会话经用户确认后再提交。清单以 `git status --short` 为准，主要包括：
- 新增：src/ib/mcp/、src/ib/ledger/mcp_store.py、src/ibweb/mcp_views.py、src/deploy/migrations/010_mcp.sql、src/frontend/src/views/McpServersPage.vue、src/frontend/src/utils/、tests 下的 R29 测试文件
- 修改：src/ib/**、src/ibweb/**、src/frontend/**、src/deploy/checklists.txt、src/deploy/env.example、src/requirements*.txt、.github/workflows/ci.yml，以及各 agent 记忆
- docs/sdlc/intelligentbase/deployment_report.md 含用户 REV-28 的未提交改动，本轮没有动过（md5 5ea46a67…）

## 遗留问题
| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| 本机未执行真实 Fernet、HTTPS 流式、真实 MCP Server 互通、浏览器交互 | GR-D-004-F02 | MAJOR | 依靠 CI（IB_REQUIRE_CRYPTO=1）和部署后人工验证 MV-01~10 |
| DEF-R29-008 只在离线装配下验证过，没有起真实 ib-worker 进程验证 | GR-E1-002 / 计划 :352 | MINOR | 部署时可选择授权 DEPLOY-006b，在真实进程上验证 |
| AC-026-03 的 Given 写"项目配置者"，实际指 manage 档（read_audit） | GR-A-003-F01 | MINOR | 下次需求修订时改措辞（测试已按 manage 档验证） |
| checklists.txt [B30](2) 仍写"先 pip install"（OI-7）；e2e_test_report 的 MV-10 原文仍是 comm 方法 | GR-C-006-F03 / GR-E1-002-F02 | MINOR | 下一轮同步；部署以 deployment_plan 2.0.0 为准 |
| manage.py runserver 不再启动 MCP supervisor | GR-C-006-F02 / CR-015 | MINOR | 只影响开发期，接受 |
| V-13 用线程数差分判定，属启发式 | GR-E1-002-F01 | MINOR | 差分不符时先排查，不直接判定复发 |
| 缺陷回流做了 3 轮，超过规则上限 2 | CP-002 Q1=A | — | 第 3 轮由用户额外授权，不属于覆盖门控 |
| OVERRIDDEN 记录 | — | — | 无 |
| PM 代答待确认 | — | — | 无（本轮全部澄清均来自用户答复，经主会话转述） |

## 待人工验证
引用 e2e_test_report.md「人工验证清单」MV-01~MV-10，排期见 deployment_plan.md「人工验证 MV-01~MV-10 排期」：
- Stage 1（首次部署后）：MV-05（V-11）、MV-10（V-13）、MV-01 页面部分
- Stage 2：接入真实 MCP Server 后的完整流程

critical path 中待人工验证 0 条。critical path 用替代口径，浏览器交互项不计入 critical path。

## 开放 conditions
- GR-E1-002 条件：
  1. 主会话提交、推送后 CI 全绿，其中 Fernet 用例须 passed 且无 skipped，据此确定 DEPLOY_COMMIT
  2. 用户按 DEPLOY-001 写入 IB_MCP_SECRET_KEY
  3. 用户决定是否授权 DEPLOY-006b
  4. E2 须在主会话中由用户本轮授权
- GR-A-003 条件中"AC-026-03 措辞修订"一项仍开放；验证部分已由 GR-D-004 闭合。
- REV-28 遗留：GR-E2-001 条件（V-04、V-10、Stage 1 人工验收）尚未闭合，REV-28 的交付报告与蒸馏也未执行。按 CP-001 Q7=A，等用户告知后再补。

## 部署
- 计划：docs/sdlc/intelligentbase/deployment_plan.md 2.0.0
  - 目标环境 production，策略 recreate
  - 部署步骤：DEPLOY-001~005，只重启 ib-web；DEPLOY-006 不执行；可选 006b、007
  - 9 处标了 MANUAL_ROLLBACK_REQUIRED：迁移 010 的 DROP、主密钥、依赖等
- E2：未执行（NOT_AUTHORIZED）。

## 安全事件摘要
无。子代理均未报告 security_events；本轮的部署授权转述按规则记为 DEPLOY_AUTH 审计（E2 保持未授权）。
