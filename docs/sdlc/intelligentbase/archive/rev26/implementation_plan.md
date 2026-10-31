<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-10-27T15:37:00+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>user_stories.md</file>
    <file>agent_orchestration_benchmark.md</file>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>tech_stack.md</file>
    <file>phase_status.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

## 0.3.0 增补（第 3 次 GROUP_C 调用，仅 CR-012）

**范围**：让 Must 故事 US-010 在界面上端到端可用；后端与 `client.getAccess/putAccess/createAccount(config_level)` 已就绪，本次**未改任何后端文件**。上文“仍未完成”中的“账号档位管理界面、账号创建页档位选择”两项自本版起已完成，§6 余项①作废。

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-R26-20 | src/frontend/src/components/config/AccessPanel.vue | 新建 | client.getAccess/putAccess | M | 本项目账号列表 + 档位下拉（查看/编辑/管理）；改后调 putAccess 并无论成败重新拉取；409 提示“最后一个管理档”；非管理档只显示说明、不发请求 | DONE |
| 2 | MOD-R26-21 | src/frontend/src/views/ConfigStudio.vue | 修改 | 1 | L | 右栏新增“权限管理”页签，仅 `level === 'manage'`（admin 恒 manage）渲染 | DONE |
| 3 | MOD-R26-21 | src/frontend/src/views/AccountsPage.vue | 修改 | client.createAccount | L | 新建账户加“配置档位”选择，默认 manage，随请求提交 `config_level`；列表增“配置档位”列（admin 显示“全部”） | DONE |
| 4 | — | src/frontend/tests/frontend.smoke.test.js | 修改 | 1~3 | L | 追加 54/55/56 三条 node:test（既有 54 条 → 现 57 条，均通过） | DONE |

**入口可达性**：导航“可视化配置”→ ConfigHub →“编排画布”→ 右栏“权限管理”页签（路由无新增）；账号创建走“系统管理 → 账户管理 → 新建账户”。
**AC-010-02 审计**：已核对后端——`config_views._access_put` 与 `views.py` 账号创建（非 manage 档）均经 `set_config_level(..., audit=ConfigAuditEntry(action="access.grant", actor, object_summary=user/from/to, timestamp))` 与档位变更同事务写入；前端不重复写审计，只在修改后刷新显示。
**查看档只读核对（AC-010-01 / AC-011-04）**：`readonly = level==='view'` 已贯通 FlowCanvas（不可拖拽/连线/删除键）、NodePalette（隐藏）、AgentDetailPanel（全部控件 disabled、提示词 readonly、保存区隐藏）、ConfigStudio（隐藏 Builder/保存/试运行页签）；无缺口，新增冒烟 56 固化。
**[ASSUMPTION]** 档位管理界面放在编排画布页签而非“系统管理”页：GET/PUT `/api/config/access` 要求 manage 档且只列本项目账号，与配置区的项目上下文一致；admin 全局管理仍可在账户管理页创建时选档位（编辑已有账号的档位走权限管理页签）。
**架构偏差**：无。

# 实现计划（REV-26 增量，第 2 次 GROUP_C 调用，0.2.0）— 状态：PARTIAL_SUCCESS（Must 主链路端到端可用）

> 0.1.0（第 1 次调用）完成后端库层；**本次（0.2.0）补齐**：Orchestrator 接入 DAG（MOD-10）、运行时缓存 / 试运行（MOD-12）、组合根装配与版本绑定（MOD-14）、配置与 Builder HTTP 端点（MOD-15/16）、worker 维护（MOD-17）、前端 MOD-18~21（含导航入口）、探针 / env 键名（MOD-22 余项）、CR-009（审计并入发布事务）、CR-002（装配期 recover）。
> 端到端已用离线驱动实跑验证：读状态 → 校验 → 差异预览 → 发布（v1 项目先存升级前基线 v1 再存 v2）→ 并发冲突 409 → 新提问立即绑定新版本 → 含环图 400 → 试运行（done 带 `config_version:-1`）→ 回滚 → 审计齐全；审计写失败 → 发布整体失败（503 `apply_failed`）、文件还原、无 pending 残留。
> **仍未完成（诚实列出，见 §6）**：配置页的“账号档位管理”前端界面（后端 `GET/PUT /api/config/access` 与 `client.putAccess` 已就绪）、账号创建页的档位选择、条件分支 / 汇聚的画布内逐项编辑体验较简、`ci.yml` 迁移检查加 008（E1 待办）；新增模块的专属 pytest 属 GROUP_D。未用占位或桩冒充完成。

## 1. GR-B-001 首步：LangGraph 契约测试（假设 A-R26-01）

- 文件：`tests/integration/test_langgraph_contract_r26.py`（7 个用例）。环境：`/root/.venvs/intelligentbase/bin/python`（langgraph 1.2.17、langgraph-checkpoint 4.3.0）。
- 结果：`7 passed in 0.46s`。**契约成立，未回退 GROUP_B。** 固化的行为：
  1. 层归一化后（边均跨 1 层，必要处插中继），汇聚节点在两个同超步上游完成后恰好运行一次；
  2. 只激活一路上游时汇聚节点不死等、也恰好运行一次（逐条 `add_edge`，不用列表形式的等待全部入边）；
  3. 一条长路径 + 一条经中继补层的短路径同时激活时，汇聚节点晚于两者、恰好一次；
  4. 条件边返回节点名列表时，下一超步并行运行且共享 reducer 键不丢数据；
  5. `interrupt_before` + `MemorySaver`：在 confirm 节点之前挂起，`invoke(None, cfg)` 续跑；
  6. 换一个新的 `MemorySaver`（= 进程重启）后旧线程无挂起态（A06 "重启后 fail-closed" 的前提）；
  7. **反证用例**：不做层归一化（边跨层不等）时汇聚节点被触发两次——这就是 ADR-57 选择方案 E 的依据。
- 附带发现：检查点里存放自定义 dataclass 会触发 LangGraph 的 "Deserializing unregistered type … will be blocked in a future version" 告警，故 `dag.py` 的状态只放原语 `dict`。

## 2. 实现概览

- 22 个 MOD：**完全完成 10 个**（01、02、03、04、05、06、07、08、09、11），**部分完成 3 个**（10、13 的库层、22），**未开始 8 个**（12、14~21 中除 13 外的全部；见 §6）。
- 新建 11 个源文件 + 1 个迁移 + 1 个契约测试；修改 20 个既有文件（含 2 个既有测试的最小调整，§5）。
- 实现顺序遵循 module_design 拓扑序：01 → 02/03 → 04 → 05 → 06 → 07/08/09 → 10(dag) → 11 → 13 → 22。
- 用户对架构开放问题的裁决（CL-007）落点：A01 `users.config_level` 默认 `manage`（迁移 + `ensure_schema` 补列）；A02 `with_upstream` 的"上游材料"只进 human 位；A03 谓词仅 `keyword` / `upstream_degraded`；A04 `rubric.py` 94 规则分 + 6 LLM 分，`BuilderEvalCache` 持久化（先写者赢），`coverage` / `cache_hit` 如实标注；A05 `max_steps` 1..8 默认 4，经 `run_tool_loop(max_iterations)`；A06 confirm 挂起态仅在 `MemorySaver`；A07 `begin_publish` 在虚拟 head=0 时同事务先写 v1 基线再写 v2。

## 3. 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | 契约 | tests/integration/test_langgraph_contract_r26.py | 新建 | — | M | A-R26-01 契约测试（§1） | DONE |
| 2 | 01 | src/ib/core/graph.py | 新建 | — | L | GraphSpec / GraphNode / GraphEdge / ConditionPredicate 与常量 | DONE |
| 3 | 01 | src/ib/core/types.py | 修改 | graph.py | M | ExpertSpecInput 追加 status / max_steps / knowledge_scope；DefinitionDocument.graph；SessionState / CompletionPayload.config_version；UserRecord.config_level；ConfigAuditEntry 三个追加字段；版本 / 差异 / 冲突 / ProjectRuntimeView / AgentRuntime 值对象（全部带默认值，既有构造点不变） | DONE |
| 4 | 01 | src/ib/core/ports.py、src/ib/core/__init__.py | 修改 | types.py | M | 新端口 ConfigVersionStore / ConfigDraftStore / ConfigAuditRetention / DocScopeResolver / BuilderEvalCache / AccountConfigLevelStore 及 NewVersion / BeginResult / DraftRecord；`ConfigAuditStore.list_by_project` 追加可选 `action`；汇总导出 | DONE |
| 5 | 02 | src/ib/config/graph.py | 新建 | 01 | H | `validate_graph`（IFC-R26-010 全部 33 个错误码）、`canonical_graph_from_experts`、`layerize_graph`、`evaluate_condition` | DONE |
| 6 | 03 | src/ib/config/access.py | 新建 | 01 | L | 三档纯函数、`REQUIRED_LEVEL` 表、令牌 `cfg:<level>` | DONE |
| 7 | 04 | src/ib/config/definition.py | 修改 | 01, 02 | H | schema v1/v2 载入 / 序列化；v2 校验分支（`_validate_v2_extras` + `validate_graph`）；白名单追加 6 项；`non_editable_changes` 允许 1→2；`upgrade_to_v2`；哈希"仅非默认值才进载荷"（存量文档哈希逐位不变）；`validate_two_domains(known_folder_ids=)` | DONE |
| 8 | 04 | src/ib/config/prompts.py | 修改 | 04 | L | 已停用专家不要求提示词（`prompt_missing` 只对启用专家） | DONE |
| 9 | 05 | src/ib/config/versioning.py | 新建 | 01, 02, 04 | H | 快照 / 清单哈希 / 序列化、`diff_snapshots`（17 种差异）、`summarize_diff`、`detect_conflicts`、`validate_prompt_texts`；另加 `prompt_refs_of_snapshot`（让保存路径与装配路径共用 `validate_two_domains`） | DONE |
| 10 | 06 | src/ib/ledger/schema.py | 修改 | 01 | M | `CONFIG_VERSION_DDL_STATEMENTS`、`USERS_ADDED_COLUMNS`、`CONFIG_AUDIT_ADDED_COLUMNS`、`config_versions_ddl_script()`、`missing_config_version_columns()`、`ensure_schema` 补列后建表（幂等） | DONE |
| 11 | 06/22 | src/deploy/migrations/008_config_versions.sql | 新建 | 10 | L | 见 §4 | DONE |
| 12 | 06 | src/ib/ledger/config_versions.py | 新建 | 10 | H | `Sqlite/Memory ConfigVersionStore`（`begin_publish` 在 `BEGIN IMMEDIATE` 内 CAS、v1 基线同事务、`commit` 内修剪、`claim_stale_pending` CAS）、草稿存储（owner 隔离 / 配额 / 1 MiB）、评审缓存、三个工厂 | DONE |
| 13 | 06 | src/ib/ledger/config_audit.py | 修改 | 10 | M | 三个新列读写、`list_by_project(action=)`、`purge_before`（保留期删除，仅供 worker 注入） | DONE |
| 14 | 06 | src/ib/ledger/accounts.py | 修改 | 10 | M | `config_level` 读写；`AccountConfigLevelStore` 三方法（两实现） | DONE |
| 15 | 06 | src/ib/ledger/tree.py、src/ib/ledger/__init__.py | 修改 | 10 | M | `live_doc_ids_in_subtrees`（`_TreeLogic` 后端无关）、`TreeDocScopeResolver`、懒导出 | DONE |
| 16 | 07 | src/ib/tools/__init__.py | 修改 | 01 | M | `build_agent_tools`（只用该 agent 自己的授权；`knowledge` 以 partial 闭包注入，不进工具 JSON Schema） | DONE |
| 17 | 07 | src/ibweb/composition.py | 修改 | 16 | L | `_search_tool` 追加可选 `knowledge`（`None` 时逐位旧行为） | DONE |
| 18 | 08 | src/ib/llm/__init__.py | 修改 | 01 | M | `_clients` 改有界 LRU（`client_cache_max`）；`run_tool_loop(on_unauthorized=)`；`complete()`（OpenAI 兼容 / Fake / Unconfigured） | DONE |
| 19 | 09 | src/ib/retrieval/__init__.py | 修改 | 01 | H | `search` / `search_as_tool` 追加 `knowledge`；空范围 0 命中且不查向量库、`degraded=False`；解析器故障 → `LEDGER_UNAVAILABLE`；5 s 缓存；`PointFilter.doc_ids` | DONE |
| 20 | 09 | src/ib/routing/intent.py | 修改 | 01 | M | `classify_experts(restrict_to=)`：候选与默认回落都限制在集合内 | DONE |
| 21 | 10 | src/ib/observability/__init__.py | 修改 | — | L | `LOG_FIELDS` 精确追加 `node_id`、`config_version`（M-SD-001 做法） | DONE |
| 22 | 10 | src/ib/orchestration/dag.py | 新建 | 01, 02 | H | `compile_dag` / `run_dag` / `resume_dag`：层归一化 + 中继、route / condition / agent / join / confirm、with_upstream、步数上限、安全网、`chat.node` 结构化日志 | DONE（独立可用；**未接入 Orchestrator**，见 §6） |
| 23 | 11 | src/ib/builder/{types,egress,adapt,rubric,service}.py、__init__.py、assets/{generate,judge,optimize}.md | 新建 | 01, 02, 04, 05 | H | 生成 / 适配 / 自评 / 优化 / 评审已有 agent；`EgressGuard` 单点外发（载荷白名单、秘钥拦截、审计先行、60 s 限时、线程池满 → busy） | DONE |
| 24 | 13 | src/ib/confsvc/{__init__,publish,drafts}.py | 新建 | 01, 02, 04, 05 | H | `ConfigPublishService`（preview / publish / rollback / adopt_drift / recover，ADR-55 协议）与 `ConfigDraftService` | DONE（库层；无 HTTP / 无装配） |
| 25 | 22 | src/scripts/selfcheck.py | 修改 | 06, 02, 11 | M | 新增 4 项：`config_versions_schema_single_source`、`graph_validate_offline`、`builder_no_data_imports`、`builder_single_egress` | DONE |
| 26 | 22 | src/deploy/checklists.txt | 修改 | — | L | 新增 `[B29]` 及签署行（`B1–B27` 原文保留，不破坏既有断言） | DONE |

## 4. 迁移

- `src/deploy/migrations/008_config_versions.sql`：四张新表（`config_versions` / `config_head` / `config_drafts` / `builder_eval_cache`）+ 两个索引，与 `ib.ledger.schema.config_versions_ddl_script()` 去空白后逐字一致（单源），全部 `IF NOT EXISTS`，已验证重放两遍幂等；头注释含回滚说明与 `MANUAL_ROLLBACK_REQUIRED`（DROP 类语句只在注释里，`DROP COLUMN` 需 SQLite ≥ 3.35，目标机版本未知，已在 `[B29]` 写明部署前核对）。
- 新列（`users.config_level`、`config_audit.version_before/version_after/object_summary`）按 007 的先例由 `ensure_schema` 以 `PRAGMA table_info` 探测后 `ALTER TABLE ADD COLUMN`，**不在 008 快照里**（头注释已声明）。已验证：新库、老库形态（001 + 003 + 004）各跑 `ensure_schema` 两遍结构一致；老库里已存在的 ops 账号补列后为 `manage`。
- 001~007 未改。可逆性：代码回退可运行（旧代码按命名列查询）；撤销新结构为 `MANUAL_ROLLBACK_REQUIRED`，v2 文档在旧代码下不可读，须从 v1 基线版本还原（`[B29]`）。
- **E1 待办（不由本组改）**：`.github/workflows/ci.yml` 迁移检查段需新增 008 的"语法 / 两次重放 / 与 `config_versions_ddl_script()` 单源 / 老库形态"断言（本组已把等价断言写进 `selfcheck.py::config_versions_schema_single_source`）。

## 5. GR-B-001 条件 2：须重新基线的既有测试（architecture_design §6.3）

| §6.3 列出的文件 | 本次是否修改 | 说明 |
|---|---|---|
| `tests/e2e/test_config_restart_effect_r16.py` | 否 | 其断言"重启后生效"对应取代登记项 REQ-FUNC-IB-40 / C-IB-40，只有在 MOD-R26-14 / 15（热生效写路径）落地后才会失效；本次未改写路径，该用例仍通过（e2e 45 passed）。**留待续调用与 GROUP_D 重新基线。** |
| `tests/unit/test_definition_data_layer_r7.py`、`tests/integration/test_definition_config_r7.py` | 否 | v1 路径逐位保留（`non_editable_changes` 对 v1→v1 仍拒绝拓扑变更；v1 校验项、顺序、错误码未改），用例全部通过；v2 新用例属 test-engineer。 |
| `tests/unit/test_orchestration_expert_nodes_r21.py`、`tests/e2e/test_rev21_expert_graph_journeys.py`、`tests/unit/test_orchestration_edges_consistency.py` | 否 | 仅 v1 / legacy 路径适用（本次保留），均通过。 |
| `src/frontend/tests/frontend.smoke.test.js` | 否 | 未改前端。 |
| `src/scripts/selfcheck.py` | 是 | 只追加 4 个新检查（含 builder 静态规则）；既有检查未改。 |

本次**被迫**调整的两个既有测试（不在 §6.3 清单内；原因都是"对表 / 字段集做精确断言"，REV-26 按设计向这些结构追加字段）：

1. `tests/unit/test_config_audit_rev16_4_unit.py::test_TC_UNIT_125`：`ConfigAuditEntry` 字段集的精确断言，追加 `version_before` / `version_after` / `object_summary` 三个名字。对应 REQ-NFUNC-006 / IFC-R26-054（审计扩列）。该用例"无 update/delete、无取值/凭据字段"的两条值无关断言未动。
2. `tests/integration/test_accounts_deploy_int_r13.py::test_TC_INT_122`：`users` 运行时列 == 003 迁移列，改为"003 列 + `USERS_ADDED_COLUMNS`（`config_level`）"。对应 IFC-R26-052 / OQ-R26-A01；只放行这一批已登记的追加列，其余漂移仍会失败。

未放宽无关断言，未删除 / skip / xfail 任何用例。

## 5b. 第 2 次调用新增改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|
| 27 | 06/13 CR-009 | src/ib/ledger/config_audit.py、config_versions.py、accounts.py；src/ib/core/ports.py；src/ib/confsvc/publish.py | 修改 | M | `insert_audit_row(connection, entry)`；`commit_publish(..., audit=)` 与 `set_config_level(..., audit=)` 把审计行并入**同一事务**（SQLite：同连接同事务；内存替身：审计 sink 先写、写失败不翻状态）；`publish` 不再“提交后尽力而为”写审计，审计写失败 → 提交整体回滚 → 还原文件并 abort → `apply_failed`；校验失败 / 冲突的 `rejected` 审计补齐（detail 只含错误码）。`PublishRequest` 追加 `audit_action/audit_fields`；`ConfigPublishService` 追加只读 `candidate()/validate()` | DONE |
| 28 | 10 | src/ib/orchestration/__init__.py、src/ib/streaming/__init__.py | 修改 | H | `Orchestrator(view=, dag=)`、`build_graph(view=, dag=)`；DAG 路径 `_run_dag_turn`（confirm 挂起落 `SessionState.gate` + `config_version`，恢复走 `resume_dag`）；`_expand_plan/_prompt_of/_decide/_run_expert/_strip` 在有 view 时读视图；`_compile_graph` 改名 `_compile_legacy_graph` 并保留旧名别名；`completion_payload_json` 仅在 `config_version≠0` 时多一键 | DONE |
| 29 | 12 | src/ib/runtime/{__init__,compile,cache,trial}.py | 新建 | H | `compile_project_config`（v1 读时 canonical 化、按 agent 绑定工具 / 步数 / 知识范围、示例句向量缓存）；`ProjectRuntimeCache`（head 探测节流、单飞后台编译、原子换引用、钉旧版、冷启动 fail-closed、失败退避 5→60 s）；`TrialRunner`（独立会话存储、并发 / 频率限流、清单哈希 TTL 缓存） | DONE |
| 30 | 14 | src/ibweb/composition.py、views.py、accounts/__init__.py、serializers.py、urls.py | 修改 | H | `Deps` 新字段 + `runtime_for`（租约）+ `orchestrator_for` 薄包装 + 热登记项目回落旧路径；`_install_config_runtime`（版本 / 草稿 / 缓存存储、`RuntimeDeps`、发布服务、Builder、试运行、**装配期对每个项目 `recover`**=CR-002）；检索接 `TreeDocScopeResolver`；`chat_stream/resume` 取租约并钉版本（恢复按 `state.config_version`，过期 409 `config_version_expired`）；旧 `PUT definition/prompts` 退化为发布包装；`effective_roles` 追加 `cfg:<level>`；账号创建 `config_level`；审计端点需 manage 档并支持 `action` 过滤与新字段 | DONE |
| 31 | 15 | src/ibweb/config_views.py（+ urls） | 新建 | H | status / definition(扩展) / catalog / validate / preview / publish / versions(+detail,diff) / rollback / adopt-drift / drafts / access / trial(SSE)；档位 403 带 `required_level`；错误集中映射 | DONE |
| 32 | 16 | src/ibweb/builder_views.py（+ urls） | 新建 | M | draft / evaluate / optimize / review-existing；先判档位再进服务（403 时出站载荷 0）；错误码 `builder_unavailable/busy/timeout/egress_rejected`；扣分项带 `llm_judged` 标注（A04） | DONE |
| 33 | 17 | src/ibweb/worker.py | 修改 | M | `run_maintenance`（版本修剪 / 草稿过期 / 评审缓存 / 审计 1 年 `purge_before`），每小时至多一次 | DONE |
| 34 | 18~21 | src/frontend/src/api/{client.ts,builderTypes.ts}；stores/configDraft.ts；components/config/{graphModel.ts,FlowCanvas,NodePalette,NodeHoverCard,AgentDetailPanel,PublishDialog,ConflictDialog,VersionHistory,TrialPanel,BuilderDrawer,BuilderEvalView}.vue；views/{ConfigStudio,ConfigHub}.vue；router/index.ts | 新建/修改 | H | 动态图（悬停卡片、拖拽、连线、删边、受限节点面板）、详情面板（提示词全文 / 工具 / 参数 / 知识范围 / 步数 / 默认 / 删除）、保存并生效（差异预览 → 确认 → 发布；冲突 → 重新载入 / 草稿副本）、版本历史 / 回滚、试运行、Builder 四入口；**导航**：既有侧栏“可视化配置”(`/config`) → `ConfigHub`（默认“编排画布”） | DONE（见 §6 余项） |
| 35 | 22 | src/scripts/hot_effect_probe.py；src/deploy/env.example；src/ib/config/__init__.py（`IB_RUNTIME_ENV_KEYS` 登记 4 键）；src/ib/llm（`IB_LLM_CLIENT_CACHE_MAX` 接线） | 新建/修改 | L | 只读探针（令牌仅环境变量）；4 个可选键名 | DONE |
| 36 | — | ConfigPage.vue 文案 | 修改 | L | 去掉“重启后生效 / 不热重载”（AC-014-05）；旧页保留为 v1 项目的“传统表单”页签 | DONE |

## 5c. 第 2 次调用对既有测试的重新基线（逐条对应取代登记，只改被取代需求直接相关的断言）

| 测试（文件::用例） | 改了什么 | 对应取代 / 变更依据 |
|---|---|---|
| tests/e2e/test_rev19_project_expert_journeys.py::test_TC_E2E_R19_003 | “保存后编排器对象不变（须重启）”改为“保存后已热生效（对象已换、版本 = 2）”；第 ③ 步“重启读回”不变 | CL-003 取代 REQ-FUNC-IB-40 / C-IB-40 / OOS-16（ADR-32）；architecture_design §6.3 |
| tests/integration/test_prompt_config_r16.py::test_TC_INT_R16_prompt_save_does_not_rebuild_graph | `before is after` → `before is not after` | 同上 |
| tests/integration/test_definition_config_r7.py::test_TC_INT_084 | GET 顶层键集 + `version/level/graph`；PUT 响应键集 + `version` | IFC-R26-141 / 132（REQ-FUNC-001/014） |
| tests/integration/test_definition_config_rev21_int.py::test_TC_INT_R21_001 | GET 顶层键集 + `version/level/graph`（derived 键集未动） | IFC-R26-141 |
| tests/integration/test_config_rev16_4_int.py::test_TC_INT_143 | 审计项键集 7 → 10（+`version_before/version_after/object_summary`） | IFC-R26-054 / 153，REQ-NFUNC-006 |
| tests/unit/test_accounts_unit_r13.py::test_TC_UNIT_090 | ops 角色 `("manager",)` → `("manager","cfg:manage")`（2 处） | IFC-R26-133，REQ-FUNC-010，A01 |
| tests/unit/test_config_audit_rev16_4_unit.py::test_TC_UNIT_125 、tests/integration/test_accounts_deploy_int_r13.py::test_TC_INT_122 | 第 1 次调用已调整（见 §5） | IFC-R26-054 / 052 |
| src/frontend/tests/frontend.smoke.test.js 用例 23 | “保存成功；重启…后生效 / 不热重载”改为“保存成功，已生效（无需重启）且不得再要求重启” | CL-003 取代 REQ-FUNC-IB-40 / C-IB-40；AC-014-05 |
| src/scripts/selfcheck.py（definition_config 端点项） | 键集断言同 TC_INT_084 | IFC-R26-141 / 132 |

其余 §6.3 所列文件：`test_config_restart_effect_r16.py`（断言“重启后读回新值”仍真，未改）、`test_orchestration_expert_nodes_r21.py` / `test_rev21_expert_graph_journeys.py` / `test_orchestration_edges_consistency.py`（v1 / legacy 路径，未改且通过）。frontend 用例 4 / 38（“编排图只读”）仍通过：它们断言的是 `ConfigPage.vue`（旧页，保留为 v1 项目的只读预览 + 传统表单）；新画布在 `FlowCanvas.vue`，由新增用例 49 断言“只读档不可拖拽 / 连线”。**未删除 / skip / xfail 任何用例；前端新增用例 46~53（8 个），前端 46 → 54。**

## 6. 未完成 / 续调用清单（0.1.0 原表；0.2.0 状态见下方“0.2.0 更新”）

**0.2.0 更新**：10 ✔、12 ✔、13 装配 ✔、14 ✔、15 ✔、16 ✔、17 ✔、18~21 ✔（余项见下）、22 余项 ✔（`ci.yml` 迁移检查加 008 仍为 E1 待办）。**余项（后续）**：① 配置页“账号档位管理”界面与账号创建页档位选择（后端与 client 方法已有）；② 条件分支 / 汇聚 / 确认节点的画布内逐项编辑较简（可编辑谓词与确认话术，分支键与边的对应靠用户在面板输入）；③ 新建 agent 加入画布后**不自动接线**（OQ-R26-16=A），用户须连入路由与结束节点，否则保存时按 `graph_unreachable_from_start` 被拒；④ 画布性能（30 节点 / 60 边）与热生效 5 s 未在目标机实测（TBD-T32/T36）。

### 0.1.0 原表

| MOD | 状态 | 缺口 | 影响的故事 |
|---|---|---|---|
| 10（Orchestrator 接入） | 部分 | `Orchestrator.__init__` / `build_graph` 追加 `view` / `dag`；`view` 给定时 `_run_expert` / `_prompt_of` / `_expand_plan` / `_active_forbidden_labels` 改读 view；`_compile_graph` 重命名 `_compile_legacy_graph`；`IB_GRAPH_RUNTIME` 开关；`CompletionPayload.config_version` / `SessionState.config_version` 的填充与恢复；`confirmation_required` 事件与 `_persist_gate` 对接 `DagOutcome.suspended_at` | US-011/014/015/021 |
| 12 | **未开始** | `ib/runtime/{compile,cache,trial}.py`：`compile_project_config`、`ProjectRuntimeCache`（head 探测节流、单飞后台编译、原子换引用、钉旧版、冷启动 fail-closed）、`TrialRunner` | US-014/015/029 |
| 13（装配） | 库层完成 | 与 12 / 14 的装配（`precompile` / `on_published` / `validator` 回调的真实实现） | US-014/016/017/018/020 |
| 14 | **未开始** | `Deps` 新字段、`runtime_for`、聊天端点版本绑定（IFC-R26-131）、旧 PUT 退化为发布包装（IFC-R26-132）、`effective_roles` 令牌 + `POST /api/accounts` 的 `config_level`、`_assemble` 装配与 `recover`、`describe_egress` 追加 builder 类别、`known_folder_ids` 的真实来源 | 全部 |
| 15 | **未开始** | `config_views.py` 及 `urls.py`（IFC-R26-140~153） | US-001/010/013~018/029 |
| 16 | **未开始** | `builder_views.py`（IFC-R26-160~163）：`BuilderService` 已就绪，缺 HTTP | US-024~028/030 |
| 17 | **未开始** | `worker.py::run_maintenance`：`SqliteConfigVersionStore.prune_all` / `purge_older_than` / `purge` / `SqliteConfigAuditStore.purge_before` 已就绪 | US-017/023 |
| 18~21 | **未开始** | 前端全部（client.ts、configDraft store、画布 / 悬停 / 详情 / 发布 / 版本 / 试运行 / Builder 组件、ConfigPage 壳与**导航入口可达**）；前端测试基线 46/46 未动 | US-001~008/011/012/014~018/022/024~030 |
| 22（余项） | 部分 | `src/scripts/hot_effect_probe.py`（IFC-R26-190）；`env.example` 登记 4 个可选键名；`ci.yml` 为 E1 待办 | NFUNC-001/004 |

建议续调用顺序：10（Orchestrator 接入）→ 12 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 余项。**Must 故事的端到端链路（US-014 热生效、US-011 自由 DAG、US-010 三档）至少需要 10 + 12 + 14 + 15 + 18~21。**

## 7. 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `ib.ledger.config_versions` 惰性导入 `ib.config.versioning`（快照序列化与清单哈希） | module_design MOD-06 依赖栏仅写 01 | 版本存储必须序列化快照；纯函数模块只依赖 `ib.core`，惰性导入无环 | 层间多一条 ledger → config 的单向边；无循环 |
| `ib.orchestration.dag` 依赖 `ib.config.graph`（`layerize_graph` / `evaluate_condition`） | MOD-10 依赖 01, 02 | 即设计所写（MOD-02 的纯函数）；记录以便复核 ADR-09"骨架业务零依赖"——`ib.config` 非业务层，未引入业务词 | 无 |
| `begin_publish` 遇到 pending（含已陈旧）一律回 `busy`，`stale_after_s` 只用于 `claim_stale_pending` | IFC-R26-050 | 陈旧 pending 意味着文件可能半写，必须先 `recover`（还原文件）再放行，不能在事务里直接放行 | `ConfigPublishService._apply` 在遇 pending 时先调 `recover`；崩溃后第一次保存会先做恢复 |
| 检索范围解析被截断（超 `IB_DOC_SCOPE_MAX_IDS`）时：不加 `doc_ids`、候选 ×2，并以**已解析（截断后）的 id 集合**做后过滤 | IFC-R26-080 写的是"按 `resolve_live` 的目录后过滤" | `resolve_live` 只给存活与展示路径，无法在后过滤时判断目录归属；用截断集合后过滤保证绝不返回范围外资料（可能漏召回） | 超大范围下召回可能偏少；记 `doc_scope_overflow` 日志；TBD-T35 在目标机量化 |
| 自评所用"适配说明"一律由最终草案重新计算 | IFC-R26-104 `evaluate(project, actor, draft)` 无说明参数 | 保证同一草案在 `generate` 结果与再次 `/evaluate` 里得分一致（"同输入同分"）；返回给用户的适配说明仍是本次实际移除 / 调整清单 | D2 的扣分只反映草案里**残留**的冲突，被适配器移除的内容不再扣分 |

### 7b. 第 2 次调用新增偏差（需 PM 知悉）

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `POST /api/accounts` 的 `config_level` 为**可选**，缺省 `manage` | IFC-R26-133 写“必填，缺省 400” | 既有大量调用方 / 测试不带该字段；缺省 manage = 存量 ops 账号的 A01 口径；显式给出非法值仍 400；非 manage 时同事务写审计 | 前端账号页尚未加选择器（余项①） |
| 正式回答的 `done` 事件**不带** `config_version`（仅试运行带 -1）；绑定版本记在日志 `chat.started/completed` 的 `config_version` | IFC-R26-091（`CompletionPayload.config_version` 填 view.version） | 保持既有 SSE 线上契约逐字节不变（`test_TC_INT_039` 断言 done 数据为空） | AC-014-01/004 的“运行记录版本号”以结构化日志为准；GROUP_D 据此断言 |
| `Deps` 不含 `audit_retention` 字段；`run_maintenance` 直接用 `config_audit_store.purge_before` | module_design MOD-14 `Deps.audit_retention` | Web 层无任何删除审计的路由，仅 worker 调用；少一个全局可达的删除句柄 | 无 |
| 新增 `GET /api/config/catalog`（工具 / 参数规格 / 资料目录 / agent 摘要） | IFC-R26-141 把这些放在 definition 响应里 | 既有契约测试对 definition 顶层 / derived 键集做精确断言，只追加设计规定的 `version/level/graph` | 前端多一次读取；无安全影响 |
| `ConfigPage.vue` 未收敛为页面壳，保留为 v1 项目的“传统表单”页签；新页壳为 `ConfigHub` + `ConfigStudio` | module_design MOD-21 | 旧页承载大量既有冒烟断言（提示词分层 / 工具参数 / 存储态等），整体改写会放宽或删除断言 | v2 项目隐藏该页签；GROUP_D 重新基线后可退役旧页 |
| `ConfigVersionStore.commit_publish` / `AccountConfigLevelStore.set_config_level` 追加可选关键字 `audit` | IFC-R26-004 方法签名 | CR-009（PM 裁决：审计并入同事务）；端口同步改签名（selfcheck `port_conformance` 通过） | 内存替身需注入审计 sink，否则拒绝带审计的提交（fail-closed） |

## 8. 开放问题 / ASSUMPTION

- `[ASSUMPTION]` 评分用适配说明的口径见 §7 最后一行；若 GROUP_B / 产品希望对"模型幻觉出不存在的工具"扣分，需让 `AgentDraft` 或 `generate` 返回值携带原始说明（接口变更）。
- `[ASSUMPTION]` `ConflictReceipt` 由 `detect_conflicts` 返回时 `base_version` / `head_version` 为 -1，由 `ConfigPublishService` 用真实版本号 `replace` 补全。
- `[ASSUMPTION]` 草稿名 1..60 字符、每人每项目 ≤10、单个 ≤1 MiB 在存储层强制（错误以 `ValidationError(field="draft_quota")` 抛出，HTTP 层映射 400 `draft_quota`）。
- `[ASSUMPTION]` `rollback` 到 v1 基线会把定义文档写回 v1 格式（允许降级写回，这是回滚的目的）；`non_editable_changes` 的"v2 不得降级"只约束编辑保存路径，不约束回滚。
- ~~`[ASSUMPTION]` 审计写入在发布 commit 之后为尽力而为~~ → **已按 PM 裁决 CR-009 改为同事务**（见 §5b 序号 27；审计写失败 ⇒ 发布整体失败）。被拒绝 / 失败的保存的 `rejected` 审计仍为尽力而为（该次操作没有产生生效变更），失败不遮盖原始错误。
- `[ASSUMPTION]` 草稿“另存为副本”的内容含提示词全文，存于台账 `config_drafts`（仅本人可读，30 天过期）。
- `[ASSUMPTION]` 旧端点 `PUT /api/config/prompts/{expert}/{layer}` 的 `expected_hash` 冲突分支沿用 `save_layer` 的回执形状；写入走发布协议（产生新版本）。
- TODO(IFC-R26-111)：`ConfigSourceLoader` 的真实适配器（`definition_store` + `prompt_store` → `ConfigSnapshot`，v1 先 canonical 规范化）随 MOD-R26-12 / 14 实现；`confsvc` 目前只依赖其 `load_files` 鸭子类型。

## 9. 自验证（实际输出见 code_review_report.md §自验证结果）

0.1.0：`compileall` 通过；unit 314 / integration 232 / e2e 45 / 前端 46；selfcheck 57/58。
**0.2.0（本次，解释器 `/root/.venvs/intelligentbase/bin/python`，`PYTHONPATH=src`）**：`COMPILE_OK`；`314 passed in 18.51s`（unit）；`232 passed in 87.24s (0:01:27)`（integration）；`45 passed in 10.47s`（e2e）；selfcheck `自检结果：57/58 通过`（唯一失败 `core_framework_free … sitecustomize`，HEAD 基线同样失败，非回归）；前端 `npm run build` 成功（`vue-tsc --noEmit && vite build`，`✓ built in 25.33s`），`npm test`：`# tests 54 / # pass 54 / # fail 0`（基线 46 + 新增 8）。

## 10. GR-D-001 缺陷修复（1.1.0 DRAFT，仅 DEF-R26-001 / DEF-R26-002；DEF-R26-003 PM 裁决保留实现，未动）

| 序号 | MOD | 文件 | 新建/修改 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|
| 1 | MOD-R26-10 | src/ib/orchestration/dag.py | 修改 | M | `make_agent` 新增 `_superstep_rank`：由快照（trace + choices + 计划入边）确定性推出本超步同层活跃 agent，按图内顺序排号；`已执行数 + 序号 >= 上限` → `skipped_step_cap`。无共享可变状态，检查点安全；串行链（序号恒 0）与 route 命中数超限行为不变 | DONE |
| 2 | MOD-IB-02 | src/ib/config/definition.py | 修改 | L | 新增纯函数 `submitted_temperature_items(raw)`：检查请求体原始 dict 的顶层 / route / experts[] / graph.nodes[] 是否带 temperature，逐处返回 `field_not_editable`（含位置 path）。`document_from_json`（读存量文档、legacy 键处置）未改 | DONE |
| 3 | 视图 | src/ibweb/views.py | 修改 | L | 旧 PUT 在非编辑字段检查前调用该函数 → 400 + rejected 审计；`_audit_definition_save` 加可选 `action` 参数（默认值不变） | DONE |
| 4 | 视图 | src/ibweb/config_views.py | 修改 | L | `_publish_request`（validate / preview / publish / drafts 共用）同样拒绝，写 `config.publish` rejected 审计，抛 `PublishError("validation_error", items=…)` 沿用既有 400 映射 | DONE |
| 5 | 测试 | tests/integration/test_dag_execution_r26.py、test_config_publish_api_r26.py | 修改 | L | 仅冻结用例 TC-INT-R26-024（断言执行数 == 上限 2、c2/c3 为 skipped_step_cap）、TC-INT-R26-059（断言 400 field_not_editable，覆盖旧 PUT 与新发布端点，版本仍为 0） | DONE |

- 迁移：无。架构偏差：无。
- [ASSUMPTION] 错误响应沿用既有口径：HTTP 400，`error.code="validation_error"`，`error.items[].code="field_not_editable"`、`items[].path` 指明位置（如 `route.temperature`、`experts[0].temperature`、`temperature`）。如要求顶层 code 亦为 `field_not_editable`，需 PM 裁决。
- [ASSUMPTION] 被截并行分支按图内节点顺序保留靠前者（确定性）；temperature 扫描范围限于顶层 / route / experts[] / graph.nodes[]，不递归工具参数值。
- 自验证见 code_review_report.md §GR-D-001 缺陷修复。
