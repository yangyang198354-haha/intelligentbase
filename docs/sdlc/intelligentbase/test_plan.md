<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-27T16:13:50+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>user_stories.md</file>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>phase_status.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划（REV-26 增量：可视化配置 / 热生效 / 自由 DAG / Agent Builder / 三档权限）

## 测试策略

- **被测改动**：GROUP_C 交付的 MOD-R26-01~22（ib/core/graph、ib/config/{graph,access,versioning,definition v2}、ib/ledger/config_versions、ib/runtime/{compile,cache,trial}、ib/orchestration/dag、ib/builder/*、ib/confsvc/*、ibweb/{config_views,builder_views,worker 维护}、迁移 008、前端 components/config/*）。范围：US-001~030（Must 24 / Should 6）全部 AC。
- **范围外 / 无法在本环境验证**：浏览器内真实交互（拖拽、悬停、连线、只读档的实际渲染）——本机无无头浏览器（`which chromium/google-chrome/firefox` 无结果，node_modules 无 playwright/puppeteer/cypress），且不得新增依赖；热生效 5 s、悬停 300 ms、30 节点 2 s 保存校验、Builder 60 s 超时的**真实时限**、真实 DeepSeek 路径（TBD-T32/T36）。这些在 e2e_test_report「未验证」小节逐条列出，**不记 PASS**。
- **环境**：解释器 `/root/.venvs/intelligentbase/bin/python`（pytest 9.1.1），`PYTHONPATH=src`，仓库根；`tests/conftest.py` 导入期设离线环境（`IB_OFFLINE_MODE=1`、`IB_CONFIG_SOURCE=dict`）；SQLite 用 pytest `tmp_path` 临时文件或内存；LLM 为 `FakeLlmProvider`（`complete_output` 脚本化）；不连 Qdrant、DeepSeek、ib-embed 或外网。前端 Node `node:test`。
- **判定模式**：INCREMENTAL → baseline（零新增失败；新写用例全部通过；critical path 覆盖 1.00）。**基线**（PM 实测，GROUP_C 门控后）：unit 314 / integration 232 / e2e 45 / agents 15 passed，前端 57/57，selfcheck 57/58（唯一失败 `core_framework_free`：解释器 `sitecustomize`，HEAD 同样失败，既有）。
- **分层**（画像 P4：按目录）：unit = 单模块、外部依赖替身；integration = 跨模块或真实框架组件（LangGraph、sqlite、Django 视图层、真实入库/检索管线）；e2e = 多步完整旅程（Django 测试客户端 + 真实账户体系）。前端为独立层（`src/frontend/tests/config_studio_r26.test.js`，node:test）。
- **新增文件**（基名全局唯一，`_r26`）：公共助手 `tests/config_r26_support.py`；unit 12 个、integration 9 个（含 0.2.0 复测文件；另含 GROUP_C 的契约测试 `test_langgraph_contract_r26.py` 7 例，计入基线 232）、e2e 2 个、前端 1 个。E-005/E-006 另覆盖 US-001/002/004/006/007/009/011/013/021/025/026/030 的多步旅程。
- **纪律**：未修改任何产品代码；无 skip / xfail / deselect / collect_ignore / addopts；monkeypatch 仅用于外部依赖边界（`ib.llm._make_langchain_client` 网络客户端工厂、LLM 替身实例方法的观测包装），不用于替换被测逻辑。
- **缺陷冻结**（记忆 M-TE-007）：0.1.0 对 TC-INT-R26-024 / 059 / 098 采用。0.2.0：024 / 059 随 DEF-R26-001/002 修复改为 AC 断言（并补 TC-INT-R26-150~156）；098 经 PM 裁决（DEF-R26-003 关闭）即规格。

## AC 映射

用例 ID 简写：`U-nnn` = TC-UNIT-R26-nnn，`I-nnn` = TC-INT-R26-nnn，`E-nnn` = TC-E2E-R26-nnn，`F-nnn` = TC-FE-R26-nnn。全部为**新写**（位置见下“用例位置索引”）。「未验」= 该 AC 的浏览器内/目标机部分无法在本环境验证，已另列。

| US | AC | 用例 | 级别 | 预期（要点） | 备注 |
|---|---|---|---|---|---|
| US-001 | 001-01 | F-001；I-058 | FE/INT | 卡片含中文标签、name、默认标记、工具、主提示词存在与前 120 字符 | 300 ms 出现时限：未验 |
| | 001-02 | F-003 | FE | route 卡片四项参数 | |
| | 001-03 | F-002；I-057 | FE/INT | 无工具显示“无”；响应无凭据 | |
| | 001-04 | F-004 | FE | 条件边卡片分支键与“否则” | |
| US-002 | 002-01/02 | I-058 | INT | 提示词全文与存储逐字一致；仅 fallback 时主层 404、兜底可读 | |
| | 002-03 | I-070；F-022 | INT/FE | 查看档可读；写接口 403；面板输入全部 disabled | |
| | 002-04 | I-076 | INT | 他项目账号 403，响应不含专家名 | |
| US-003 | 003-01~03 | F-010；F-024 | FE | 默认标记/未保存/放弃/重新载入确认（源码+模型层） | 1 s 内联动、真实点击：未验 |
| US-004 | 004-01 | I-099；I-041；I-109 | INT | 手工草稿 → 校验 → 保存生效，agent 可用 | 画布出现节点：未验 |
| | 004-02 | U-089 | UNIT | 主提示词缺失被拒（prompt_missing） | |
| | 004-03 | I-092；U-185 | INT/UNIT | name 重复被拒/标记 | 中文标签重复的保存期校验无专用用例（见缺口） |
| | 004-04 | I-070；F-027 | INT/FE | 编辑以下 403 | |
| | 004-05 | — | — | 克隆流程在前端组装 | 未验（无浏览器） |
| | 004-06 | I-092 | INT | 与源 agent 同名被拒 | |
| US-005 | 005-01 | U-135；I-049 | UNIT/INT | 删除 agent 清提示词、版本可回看 | 历史会话显示名：未验 |
| | 005-02 | I-046 | INT | 删除/停用默认专家被拒 | |
| | 005-03 | F-008 | FE | “将同时删除 N 条边”的边数与连带删除 | |
| US-006 | 006-01 | I-041 | INT | 关键词命中路由到 billing-agent | |
| | 006-02 | U-007/008；I-044 | UNIT/INT | 缺 `__else__` 被拒并指出节点 | |
| | 006-03 | U-067；I-045 | UNIT/INT | tau=-1 → route.tau 路径 | temperature 入口见 US-021 |
| | 006-04 | U-068；I-045 | UNIT/INT | 关键词撞车指出两个专家 | |
| US-007 | 007-01 | I-148；U-153 | INT/UNIT | top_k 授权后仅该 agent 生效 | |
| | 007-02 | U-069；I-045 | UNIT/INT | 越界 400 指出字段，在用不变 | |
| | 007-03 | U-154 | UNIT | 授权不存在的工具被拒 | “无新增工具入口”界面：未验 |
| US-008 | 008-01 | U-157；I-023；I-147 | UNIT/INT | 工具轮数/图步数上限生效；缺省 4 | |
| | 008-02 | U-066；I-045 | UNIT/INT | max_steps ≤0 被拒 | |
| US-009 | 009-01 | U-160；I-145 | UNIT/INT | 目录范围内检索不越界（真实台账目录树 + 向量库） | |
| | 009-02 | U-155；I-147 | UNIT/INT | 未授权工具调用被拒并记录；agent 只拿到自己的工具 | |
| | 009-03 | U-161；I-146 | UNIT/INT | 空范围 0 命中、不查向量库 | |
| | 009-04 | I-070；F-022 | INT/FE | 保存接口 403 | |
| US-010 | 010-01 | I-070 | INT | 查看档读 200、写 403 含所需档位 | |
| | 010-02 | I-073 | INT | 管理档改档位，审计含目标/前后档位/时间，生效 | |
| | 010-03 | I-076 | INT | 无授权账号 403 | |
| | 010-04 | I-075；E-004 | INT/E2E | 跨项目写不触及项目 B | |
| US-011 | 011-01/02 | F-009；F-006 | FE | 位置回写/连线预校验（模型层） | 真实拖拽/连线/删除键：未验 |
| | 011-03 | U-010；I-020 | UNIT/INT | 汇聚合法并可运行 | |
| | 011-04 | I-070；F-021 | INT/FE | 只读档不可拖拽/连线（源码） | 实际渲染：未验 |
| | 011-05 | I-020 | INT | 只激活 A：汇聚不等 B，恰好 1 次，B 未激活 | |
| | 011-06 | F-005；U-013 | FE/UNIT | 仅受限节点集 | |
| US-012 | 012-01 | I-052；F-009 | INT/FE | 位置保存后一致 | |
| | 012-02 | I-052 | INT | 20/20 路由结果一致 | |
| US-013 | 013-01 | U-002；I-043 | UNIT/INT | 环 → 400，环上节点 | |
| | 013-02/03 | U-003/004；I-044 | UNIT/INT | 不可达/无路径 | |
| | 013-04 | U-005/006 | UNIT | 默认专家不可达 | |
| | 013-05 | I-043 | INT | 绕过界面同样 400 | |
| | 013-06 | U-001；I-041 | UNIT/INT | 合法图 200 含新版本号 | |
| US-014 | 014-01 | I-001；I-041 | INT | 保存后新提问绑定新版本（无重启） | 5 s 时限：未验（目标机） |
| | 014-02 | I-001 | INT | 新关键词路由到新 agent | |
| | 014-03 | U-126；I-007 | UNIT/INT | 应用失败仍按旧版，状态含错误码 | |
| | 014-04 | I-005 | INT | 两个独立缓存（模拟两进程）收敛，100 次一致 | 真实多进程：未验 |
| | 014-05 | I-041；F-026 | INT/FE | 响应无“重启”，显示已生效 | |
| US-015 | 015-01/02 | I-002 | INT | 进行中回答绑定开始版本；下次用新版 | |
| | 015-03 | I-003；I-027 | INT | 挂起后新版本生效，恢复仍按原版本 | |
| US-016 | 016-01~03 | I-042；U-082/084；F-023/024 | INT/UNIT/FE | 差异清单、取消不提交、无变更 422 | |
| US-017 | 017-01 | I-049；U-100 | INT/UNIT | 历史含版本号/保存人/时间/摘要 | |
| | 017-02 | I-049；U-130；E-001 | INT/UNIT/E2E | 回滚产生新版本、内容一致、审计 | |
| | 017-03 | I-050；I-071 | INT | 编辑档 403 提示 manage | |
| | 017-04 | U-106；I-124 | UNIT/INT | 保留 50，最旧不可回滚 | |
| US-018 | 018-01 | I-047/048；U-101/122；E-002 | INT/UNIT/E2E | 陈旧基线 409 回执含冲突对象，甲未被覆盖 | |
| | 018-02/03 | F-025；I-053；E-002 | FE/INT/E2E | 重新载入/另存草稿副本 | 界面点击：未验 |
| US-019 | 019-01 | I-076 | INT | 跨项目读全部 403，不泄露 | |
| | 019-02 | F-020；I-107 | FE/INT | 无 v-html，响应为 JSON 字面量 | 页面无弹窗：未验 |
| | 019-03 | I-057 | INT | 凭据扫描命中 0 | |
| | 019-04 | U-089；I-045 | UNIT/INT | >20000 被拒含字段与上限 | |
| US-020 | 020-01 | I-130 | INT | dag 与 legacy 20/20 一致 | |
| | 020-02 | I-131；U-060/061 | INT/UNIT | 定义文件字节/哈希零改写；哈希逐位不变 | |
| | 020-03 | I-051；U-103/120；E-003 | INT/UNIT/E2E | 首次保存先存基线 v1 再存 v2 | |
| US-021 | 021-01 | I-010；I-026 | INT | 无命中走默认专家；全降级仍有应答 | |
| | 021-02 | I-023；I-024；I-150~153 | INT | 串行链与并行超步执行数严格 ≤ 上限；预算充足不过度截断；未激活分支不占步数（DEF-R26-001 FIXED） | |
| | 021-03 | I-059；I-154~156 | INT | 任意位置（含 graph.nodes[]）temperature → 400 validation_error + field_not_editable；去掉后 200；rejected 审计；不产生版本（DEF-R26-002 FIXED；PM 裁决口径） | |
| US-022 | 022-01/02 | U-014/015 | UNIT | 校验规模上限与 31 节点/58 边校验耗时 <2 s（离线下界） | 悬停 300 ms、拖拽流畅、目标机 2 s：未验 |
| US-023 | 023-01 | I-054；U-108 | INT/UNIT | 成功保存审计字段齐全 | |
| | 023-02 | I-054 | INT | 失败 rejected 含错误码，不含正文 | |
| | 023-03/04 | I-055；I-126 | INT | 修改/删除 405；非管理 403；Web 无删除句柄 | |
| | 023-05 | I-056；I-124 | INT | 364 天仍可查；366 天被维护清理 | |
| US-024 | 024-01 | I-090 | INT | 生成完整草案、不落盘、版本不变 | |
| | 024-02 | I-109；E-001 | INT/E2E | 保存后含关键词的提问路由到该 agent | “加入画布”点击：未验 |
| | 024-03 | U-185；I-092 | UNIT/INT | name 冲突标记 | |
| | 024-04 | U-186/187 | UNIT | 三项条款检测；业务专有词拦截 | LLM 是否真会生成条款：目标机 |
| | 024-05 | U-186；I-103 | UNIT/INT | 缺条款 → 适配说明 + 扣分 | |
| | 024-06 | I-094 | INT | 查看档 403，出站 0 | |
| | 024-07 | I-095；U-219 | INT/UNIT | 空需求 400，出站 0 | |
| US-025 | 025-01~03 | U-181~183；I-091 | UNIT/INT | 不存在工具/目录移除；越界值调整 | 实际工具声明 top_k∈[1,50] 无默认，越界值被移除而非“调为默认 5”（OBS-R26-02） |
| | 025-04 | U-184 | UNIT | 范围内取值保留 | “最多检索 3 条”由生成器理解，离线不可测（部分） |
| | 025-05 | I-092/093 | INT | 重名/不存在工具直接保存 400 | |
| US-026 | 026-01~05 | U-192~198；I-101/103/104/105 | UNIT/INT | 总分/等级/维度和=100、扣分带证据、10 次同分、单轮优化 | |
| US-027 | 027-01/03 | I-090 | INT | 生成不写任何东西 | |
| | 027-02/04 | I-109；E-001；F-023 | INT/E2E/FE | 差异清单后确认才生效；用户文本为准 | |
| US-028 | 028-01/02 | I-106 | INT | 评分+修订提案；已发布配置/版本不变 | 差异项逐个采纳的界面：未验 |
| | 028-03 | I-097 | INT | CANARY-PROMPT-002 命中 0 | |
| | 028-04 | I-094 | INT | 查看档 403，出站 0 | |
| US-029 | 029-01~03 | I-140/141/142 | INT | 草稿路由、不污染正式、含环 400 且无 LLM 调用 | |
| | 029-04 | I-145 | INT | 试运行/运行时范围过滤 | |
| | 029-05 | I-070 | INT | 查看档 403 | |
| US-030 | 030-01 | I-097；U-211/212 | INT/UNIT | CANARY 命中 0、凭据扫描 0、字段属白名单 | |
| | 030-02 | I-098 | INT | 每次外发各 1 条审计（generate + judge 共 2 条）；DEF-R26-003 PM 裁决关闭，AC-030-02 待下次 GROUP_A 改措辞 | 即规格 |
| | 030-03 | I-099 | INT | 未配置 Key 可读错误，手工创建仍可用 | |
| | 030-04 | I-100；U-216 | INT/UNIT | 超时结束且手工可用 | 60 s 取值已断言，真实 60 s：未验 |
| | 030-05 | I-091；I-107；F-020 | INT/FE | 越权项被移除；`<script>` 原样文本 | |

**补充专项**（任务书第一.5 条 / CR-001/006）：审计与发布同事务 → U-109/U-128/I-124（审计写失败则发布不生效）；CAS 陈旧基线 → U-101/U-122/I-047；v1 首存基线 → U-103/U-120/I-051；回滚 → U-130/I-049；档位 403 与跨项目 → I-070/071/075/076/E-004；按 agent 工具授权 → U-150~157/I-147；目录范围不越界 → U-160~166/I-145；Builder 外发白名单 → U-210~220/I-097；自评同输入同分 → U-194/I-101；条件分支无代码执行 → U-040~045/I-021；CR-001 边界 → I-024；迁移 008 单源/幂等 → I-120~123；worker 维护 → I-124/125。

## 用例位置索引

- unit（195）：`tests/unit/test_graph_validate_r26.py`(34)、`test_graph_layerize_r26.py`(6)、`test_condition_eval_r26.py`(6)、`test_config_access_r26.py`(9)、`test_definition_v2_r26.py`(15)、`test_config_diff_conflict_r26.py`(11)、`test_config_version_store_r26.py`(33)、`test_publish_protocol_r26.py`(22)、`test_agent_tools_enforce_r26.py`(8)、`test_doc_scope_filter_r26.py`(9)、`test_builder_adapt_rubric_r26.py`(24)、`test_builder_egress_r26.py`(18)。
- integration（101 新写 + 7 契约；含 0.2.0 复测补充 `test_defect_retest_r26.py`(7)，TC-INT-R26-150~156）：`tests/integration/test_hot_effect_r26.py`(10)、`test_dag_execution_r26.py`(9)、`test_config_publish_api_r26.py`(23)、`test_config_access_api_r26.py`(10)、`test_builder_api_r26.py`(21)、`test_trial_api_r26.py`(11)、`test_config_schema_migration_r26.py`(7)、`test_legacy_equivalence_r26.py`(3)；契约 `test_langgraph_contract_r26.py`(7，GROUP_C 交付，计入基线)。
- e2e（6）：`tests/e2e/test_config_journeys_r26.py`（E-001~004：Builder→热生效→回滚、并发冲突、旧项目升级与回基线、权限与跨项目）、`tests/e2e/test_config_journeys2_r26.py`（E-005 编排编辑旅程、E-006 Builder 安全旅程）。critical path 旅程所覆盖的 Must 故事见 e2e_test_report。
- 前端（20）：`src/frontend/tests/config_studio_r26.test.js`。
- 公共助手：`tests/config_r26_support.py`。

## 测试数据需求

- 全部为运行期内联构造（专家/图/文档/资料文本由测试代码生成，资料文件经真实入库管线写入内存台账，目录“产品手册”“内部制度”由 `put_file(rel_dirs=…)` 创建）。账户口令为测试占位值（`Api.USER_PW` 等，非生产凭据）；占位 Key 串 `sk-…PLACEHOLDER…` 仅用于验证拦截。无持久化数据，无需唯一化。
- `[DATA_REQUIRED]`：目标机真实 DeepSeek Key 与真实 SQLite 版本（TBD-T32/T36、`ALTER TABLE … DROP COLUMN` 需 ≥3.35）——离线无法提供，列入上线验证项。

## 不可测项

| AC | 原因 |
|---|---|
| AC-003-01~03（US-003，Must） | 全部为浏览器内交互；critical path 0.96 的唯一缺口，待用户裁决；推荐方案“上线后人工浏览器验收”，清单见 e2e_test_report 文末 |
| AC-001-01 / AC-022-01 的 300 ms 出现时限 | `[INFERRED]` 占位阈值，需浏览器 + 目标机实测；且前端当前无延迟逻辑可测（`NodeHoverCard` 为即时显示） |
| AC-014-01 / AC-017-02 的 5 秒热生效时限 | 需目标机多进程实测（`hot_effect_probe.py` 为上线探针）；离线仅验证版本切换逻辑 |
| AC-022-02 的拖拽 10 节点、2 s 服务端校验（目标机） | 浏览器交互 + 目标机性能；离线仅验证纯函数校验耗时下界 |
| AC-030-04 的真实 60 s 超时 | 真实时限；离线以缩短时限验证逻辑，默认值 60.0 已断言 |
| AC-003-01、AC-004-05、AC-011-01/02 的真实点击与 AC-018-02、AC-028-01/02 的界面采纳、AC-019-02 的“无弹窗” | 无可用无头浏览器，且不得新增依赖；仅模型层/源码结构覆盖，记“未验证” |
