<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-27T16:12:56+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>test_plan.md</file>
    <file>unit_test_report.md</file>
    <file>module_design.md</file>
    <file>code_review_report.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（REV-26）

## 摘要

- 执行时间：2026-10-27T16:01~16:09+08:00（GR-D-001 缺陷回流复测，本报告最后一次整层执行）；环境：`/root/.venvs/intelligentbase/bin/python`（pytest 9.1.1），`PYTHONPATH=src`，仓库根，离线（内存/SQLite 临时库、FakeLlm、回环无外网）。
- 命令：`python -m pytest tests/integration -q`
- **新写用例**：total = pass + fail + skip + blocked + not_testable = 101 = 101 + 0 + 0 + 0 + 0；**整层**：total = 333 = 333 + 0 + 0 + 0 + 0（基线 232 = 225 + GROUP_C 契约 7；新写 101 = 0.1.0 的 94 + 复测补充 7）。
- 通过率 = pass/(pass+fail+blocked) = 333/333 = 1.00（新写 101/101 = 1.00）。
- 判定模式：INCREMENTAL / baseline。基线 232 passed → 既有 232 全部仍通过，**新增失败 0**，新写全部通过。
- **本层门控：PASSED**（测试工程师口径；最终门控由 PM 复跑裁决）。上一层（unit）门控 PASSED，故执行本层。
- **缺陷状态（0.2.0）**：DEF-R26-001、DEF-R26-002 已由开发修复，TC-INT-R26-024 / 059 已从“缺陷冻结”改为 AC 断言（见下“复核”），PASS 现在**代表 AC 满足**；DEF-R26-003 经 PM 裁决保留实现（每次外发各 1 条审计），TC-INT-R26-098 即规格，状态“PM 裁决关闭，AC-030-02 待下次 GROUP_A 改措辞”。
- 复测补充用例（新文件 `tests/integration/test_defect_retest_r26.py`，7 例，只加不删）：TC-INT-R26-150~156。

## 执行输出

```
$ PYTHONPATH=src python -m pytest tests/integration -q
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
......................................                                   [100%]
333 passed in 449.62s (0:07:29)
$ pytest tests/integration --collect-only -q | grep -c '::'   → 333   （其中 r26 文件 108 = 新写 101 + 契约 7）
```

用例级迭代记录（均为测试侧问题，已修，非产品缺陷）：曾因 ① 并行后台编译与断言的竞态（TC-INT-R26-005，改为轮询 `applied_version`）、② 对 v1 项目首次保存失败后 head 的预期（改为基线 v1，见观察 OBS-R26-03）、③ 对工具声明的假设（OBS-R26-02）、④ 查询串令牌的返回码（400 而非 401）调整断言；每个用例修改 ≤1 轮。

## 分项结果（按集成边界）

| 边界 | 文件（用例数） | 验证内容 | 结果 | 根因分类 |
|---|---|---|---|---|
| 运行时缓存 ↔ 编译 ↔ 版本存储 ↔ 发布服务（热生效） | test_hot_effect_r26.py (10) | 发布后新提问绑定新版本并路由到新 agent（每 agent 用自己的提示词）；进行中回答钉旧租约；挂起版本钉住可按原版本恢复；被修剪版本 `config_version_expired`；两个独立缓存（两“进程”）靠 head 探测收敛、100 次一致；单飞编译（门闩证明 6 线程只编译 1 次）；编译失败保留旧版+退避+状态含错误码；冷启动坏配置 fail-closed；冷启动发现文件漂移以 head 快照服务；无命中走默认专家 | 10 PASS | — |
| DAG ↔ LangGraph ↔ 路由器/LLM | test_dag_execution_r26.py (9) + test_defect_retest_r26.py 的 150~153 (4) | 汇聚只等被激活上游且恰好 1 次、B 未激活（AC-011-05）；条件分支不执行代码；with_upstream 材料只进用户位；串行链步数上限精确；**CR-001 并行超步边界实测**；route 命中超限隐式 general；全降级安全网；confirm 挂起/恢复；无检查点编译失败 | 13 PASS（TC-024 已改 AC 断言；150~153 为补充） | DEF-R26-001 FIXED，复测通过 |
| 视图层 ↔ 发布/版本/审计/草稿（配置 HTTP） | test_config_publish_api_r26.py (23) + test_defect_retest_r26.py 的 154~156 (3) | status/definition（v1 规范化只读）；热生效；预览差异；无变更 422；环/不可达/无路径/缺 else 400；字段级错误（tau/关键词撞车/max_steps/top_k/提示词 20000）；默认专家不可删/停；**陈旧基线 409 回执**；冲突对象；版本历史/详情/diff/回滚；v1 首存基线；仅布局保存且 20/20 路由一致；草稿 owner 隔离；审计 saved/rejected 无正文；审计 405/403/364 天；凭据扫描；卡片数据与提示词全文；**temperature 冻结**；旧 PUT 为发布包装 | 26 PASS（TC-059 已改 AC 断言；154~156 为补充） | DEF-R26-002 FIXED，复测通过 |
| 授权中间件 ↔ 账号档位 ↔ 视图层 | test_config_access_api_r26.py (10) | 查看档：读 200/写全 403（含 Builder、试运行、旧提示词保存）；编辑/查看不能用管理动作；管理档授予档位+审计+生效；最后一个管理档不可降级；**跨项目写不触及项目 B**；他项目账号读取 403 且不泄露名字；admin 恒 manage；缺省档位 manage；无令牌/伪造令牌/查询串令牌被拒 | 10 PASS | — |
| Builder 服务 ↔ EgressGuard ↔ 审计 ↔ 视图层 | test_builder_api_r26.py (21) | 完整草案且不落盘；适配移除/调整；重名；直接保存引用不存在工具 400；查看档 403 且出站 0；空需求 400 且出站 0；密钥拦截；**10 次生成+10 次优化+评审已有 agent 的出站载荷 canary 命中 0**；外发审计只记类别（**DEF-R26-003 冻结**）；未配置 Key；云端挂起→504 且手工可用；10 次评审同分+缓存；LLM 判定降级 rules_only；扣分带证据；单轮优化前后分；优化再引入坏工具被适配；评审已有 agent 不改配置；`<script>` 为 JSON 字面量；垃圾输出 503；用户文本为准 | 21 PASS（TC-098 = 规格） | DEF-R26-003 PM 裁决关闭 |
| 试运行 ↔ 编译 ↔ 隔离会话；运行时权限 ↔ 真实检索管线 | test_trial_api_r26.py (11) | 试运行用草稿、正式提问仍旧版；不进正式会话/不产生版本/仅 config.trial 审计；含环 400 且无 LLM 调用；并发 429；入参校验；**知识范围经真实台账目录树+向量库不越界**（成对正例与对照）；空范围 0 命中；每 agent 只拿自己的工具；top_k 仅对该 agent 生效 | 11 PASS | — |
| 迁移 008 ↔ sqlite ↔ ensure_schema；worker 维护 | test_config_schema_migration_r26.py (7) | 008 与 schema.py 逐字一致（单源）；迁移重放幂等；新库 ensure 两遍稳定；**老库形态补列**且存量 ops 账号为 manage、既有审计行保留；维护：保留 head+50、草稿过期、审计 364 天保留/366 天清理；一类失败不阻断其余；Web 层无审计删除句柄 | 7 PASS | — |
| 兼容：dag ↔ legacy 运行时 | test_legacy_equivalence_r26.py (3) | v1 多专家项目未重存：dag 与 legacy 对 20 个固定提问作答专家集合 20/20 一致且各 1 个完成事件；上线+提问+读配置后定义文件字节与 mtime 不变、不产生版本行；`IB_GRAPH_RUNTIME` 非法值启动失败不回显 | 3 PASS | — |
| 契约（GROUP_C 交付，计基线） | test_langgraph_contract_r26.py (7) | A-R26-01 LangGraph 超步合并/汇聚/interrupt_before | 7 PASS | — |

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 差异 |
|---|---|---|---|
| tests/integration passed | 232（225 + 契约 7） | 333 | +101（全部新写 `_r26`） |
| 失败 | 0 | 0 | 新增失败 0；既有失败 0 |

## 缺陷修复复核（GR-D-001 条件 1）

复核对象：开发对 `dag.py`（`_superstep_rank` / `make_agent`）、`definition.py`（`submitted_temperature_items`）、`views.py`（`_put_definition_config`）、`config_views.py`（`_publish_request`）的改动，及两个被改写的用例。

| 项 | 断言是否充分 | 补充 |
|---|---|---|
| TC-INT-R26-024（A05 / REQ-NFUNC-010 / AC-021-02，上限 2，1+3 并行） | 断言执行集合 == [x, c1]、LLM 调用 == 2、被截分支状态为 skipped_step_cap、仍有应答——覆盖主场景；但只测了一个参数点 | 补 TC-INT-R26-150（起点并行 3、上限 2 → 恰 2 个）、151（上限 8、1+3 → 全部执行，防过度截断）、152（上限 3、1+3 → 恰 3 个）、153（条件分支未激活者不占步数，记 skipped_inactive 而非 skipped_step_cap） |
| TC-INT-R26-059（AC-021-03；PM 裁决：顶层 error.code=validation_error + items[].code=field_not_editable 视为满足） | 覆盖 PUT 与 `/api/config/publish` 对 route / 顶层 / experts[] 三处 temperature；断言 400、code、path 后缀、版本仍 0、哈希不变、持久文档与 catalog 无 temperature——充分 | 补 TC-INT-R26-154（`graph.nodes[i]` 位置，publish / validate / preview 三入口，path 精确为 `graph.nodes[1].temperature`）、155（去掉 temperature 的同一请求体 200，证明 400 归因正确）、156（rejected 审计含 field_not_editable、不含 temperature 数值、不产生版本） |

复核结论：两处修复与 AC 口径一致，补充用例均首次运行即通过（7/7），未发现新缺陷。观察：preview / validate 遇 temperature 同样 400（开发已在 code_review_report 标注取舍），与 AC 不冲突。

DEF-R26-003：PM 裁决保留实现（每次外发各 1 条审计：generate + judge），TC-INT-R26-098 断言的 2 条审计即规格；报告状态改为“PM 裁决关闭，AC-030-02 待下次 GROUP_A 改措辞”，不再计为缺陷。

## 失败汇总（需路由给开发）

本层无失败，无待开发修复的缺陷（DEF-R26-001/002 FIXED 复测通过；DEF-R26-003 PM 裁决关闭）。
