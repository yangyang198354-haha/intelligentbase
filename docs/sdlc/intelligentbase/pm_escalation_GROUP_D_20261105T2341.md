<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-05T23:41:28+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>deployment_plan.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09,PHASE_11a</phase>
  <status>DRAFT</status>
</file_header>

# PM 上报：REV-29 缺陷回流已用尽，GROUP_E1 发现新的产品缺陷 DEF-R29-008

## 背景
- 缺陷回流已做满 2 轮（GR-D-001 → GR-C-004 → GR-D-002 → GR-C-005 → GR-D-003），DEF-R29-002~007 全部修复，PM 已复跑验证：pytest 1718 passed / 6 skipped，selfcheck 76/77（只有既有失败 core_framework_free），前端 180/180。
- GROUP_E1（intelligentbase-R29-GROUP_E1-001）编写部署计划时发现一个新的产品缺陷，经 PM 核对属实。按 pm-orchestrator §4 规则 6 与协议 §H，不再自行开第 3 轮回流，交用户决定。

## DEF-R29-008（MAJOR）：ib-worker 进程也会启动 MCP supervisor
- 调用链（PM 已读代码核实）：`src/ibweb/worker.py:47-51` `_setup_django()` → `django.setup()` → `src/ibweb/apps.py:49` `composition.build_deps()` → `src/ibweb/composition.py:1631-1633` `deps.mcp.supervisor.start()`。
- 设计口径：supervisor 只在 ib-web 进程内运行（module_design.md:866；composition.py:1631 的注释也是这么写的）。
- ib-worker 从不调用编排或工具（grep `run_dag|run_tool_loop|orchestration` src/ibweb/worker.py 无结果），不需要 MCP。
- 影响：ib-worker 下次重启（包括主机重启）后，会对已登记的 Server 重复做健康探测、周期复核和长连接监听。ib-worker.env 里没有 IB_MCP_SECRET_KEY，带凭证的 Server 在 worker 侧会一直鉴权失败，可能把健康状态和审计写进共享台账，与 ib-web 的结果互相覆盖。
- 本轮部署计划不重启 ib-worker（DEPLOY-006 写为"不执行"），所以部署当时不会触发，但隐患一直存在。

## 可选操作（对应 CP-002 Q1）
- A【推荐】额外授权 1 轮缺陷回流：由 software-developer 做最小修复（只在 ib-web 进程启动 supervisor，例如由 wsgi 或显式进程标志控制），test-engineer 补一对用例（worker 装配时 supervisor 不启动；ib-web 装配时启动），devops-engineer 增量更新部署计划。
- B 不改代码，靠运维规避：由用户在 `/etc/intelligentbase/ib-worker.env` 加 `IB_MCP_ENABLED=0`（worker 侧 MCP 整体关闭），部署计划增加这一步和对应核验。
- C 接受风险，按现有计划部署，把 DEF-R29-008 作为遗留缺陷（不推荐）。
- D 终止本轮。

## 附：最后一次相关 agent_response 摘要
devops-engineer E1-001：status=SUCCESS；deployment_plan 1.0.0 / cicd_pipeline 1.0.0（PM 门控 GR-E1-001 后批准）；开放问题 OI-1 即本缺陷；OI-2/OI-3：checklists.txt 中 B30 的命令与 SKILL.md 冲突（npm ci、env 读取未加 sudo），计划已改用正确写法，交付物本身待修正。
