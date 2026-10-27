<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-27T16:12:56+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>test_plan.md</file>
    <file>module_design.md</file>
    <file>user_stories.md</file>
    <file>code_review_report.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（REV-26）

## 摘要

- 执行时间：2026-10-27T16:01+08:00（GR-D-001 缺陷回流复测，本报告最后一次执行；0.2.0 仅刷新执行证据，单元用例未增删）；环境：`/root/.venvs/intelligentbase/bin/python`（pytest 9.1.1，Python 解释器同 PM 基线），`PYTHONPATH=src`，仓库根，离线（`IB_OFFLINE_MODE=1`）。
- 命令：`python -m pytest tests/unit -q`
- **新写用例**：total = pass + fail + skip + blocked + not_testable = 195 = 195 + 0 + 0 + 0 + 0；**整层**：total = 509 = 509 + 0 + 0 + 0 + 0（基线 314 + 新写 195）。
- 通过率 = pass/(pass+fail+blocked) = 509/509 = 1.00（新写 195/195 = 1.00）。
- 0.2.0 复测说明：产品代码在缺陷修复（DEF-R26-001/002，改动 dag.py、definition.py、views.py、config_views.py）后重跑，单元层 509 全部仍通过，无需新增单元用例（修复的行为由集成层 TC-INT-R26-024/059/150~156 断言）。
- 判定模式：INCREMENTAL / baseline（零新增失败、新写全部通过）。基线 314 passed → 本次既有 314 个全部仍通过，**新增失败 0**。
- **本层门控：PASSED**（测试工程师口径的执行结论；最终门控由 PM 复跑后裁决）。

## 执行输出

```
$ PYTHONPATH=src python -m pytest tests/unit -q
........................................................................ [ 99%]
.....                                                                    [100%]
509 passed in 23.31s
$ PYTHONPATH=src python -m pytest tests/unit --collect-only -q | grep -c '::'      → 509
$ … | grep '::' | grep -c r26                                                       → 195
```

执行过程中的一次失败（已在测试侧修复，不是产品缺陷）：首次整层运行出现 1 个失败 `test_prompt_tool_config_unit_r16d.py::test_TC_UNIT_122_repo_grep_zero_old_slugs_and_labels`——该既有用例做全仓“旧 cn_label 残留”扫描，命中了本人新写的 `test_config_publish_api_r26.py` 中的问答样例词（含已退役的旧标签字样）。根因分类：**测试问题**（新写测试用词）；已把样例词改为“知识库里的问题”，重跑后 509 passed。

## 分项结果（按模块）

| 模块 | 文件（用例数） | 覆盖要点 | AC | 结果 | 根因分类 |
|---|---|---|---|---|---|
| MOD-R26-02 图纯函数 | test_graph_validate_r26.py (34) | 18 类结构错误码矩阵、环节点列表、不可达/无路径/默认专家、`__else__`、汇聚入边、条件谓词规则、规模上限、31 节点/58 边校验耗时、错误消息不回显正文、确定性 | US-013、US-011、US-006、US-005、US-022 | 34 PASS | — |
| | test_graph_layerize_r26.py (6) | 每边恰好跨 1 层并插入中继、分支键只在第一跳、前置条件违反抛 ValueError、规范化默认图等价且可校验、位置只影响展示 | US-011、US-020、US-012 | 6 PASS | — |
| | test_condition_eval_r26.py (6) | 关键词（大小写/空白不敏感）、无命中走 `__else__`、声明序优先、upstream_degraded、代码样式文本只当字面量、空白关键词不匹配 | A03、US-011 | 6 PASS | — |
| MOD-R26-03 档位 | test_config_access_r26.py (9) | 动作→档位表精确、三档允许集、未知动作 fail-closed、admin/令牌/旧 manager 解析、形似令牌不抬权、授予须 manage 且同项目 | US-010/017/023 | 9 PASS | — |
| MOD-R26-04 定义文档 v2 | test_definition_v2_r26.py (15) | v1 哈希与 REV-25 口径逐位一致（独立重算）、v1 序列化无新键、v1→v2 往返、新键仅非默认值出现、位置变更改哈希、max_steps/默认专家停用/授权校验、tau、关键词撞车、top_k 越界、知识范围形态与目录存在性、non_editable 规则、白名单无 temperature | US-020/006/007/008/009/021 | 15 PASS | — |
| MOD-R26-05 版本化 | test_config_diff_conflict_r26.py (11) | 快照往返与清单哈希、差异（新增 agent/工具授权/参数/范围/停用/路由/布局）、提示词只给长度+哈希、三方冲突仅在双方触及同对象、基线被修剪退化、提示词文本校验（20000 边界）、摘要 ≤200 | US-016/018/012/019/017 | 11 PASS | — |
| MOD-R26-06 台账 | test_config_version_store_r26.py (33，SQLite 与内存各一套) | begin/commit/abort/claim_stale、CAS 陈旧基线、busy、A07 基线、修剪保留 50、prune_all、**审计同事务**与审计失败不生效、草稿 owner 隔离/配额/大小/名称、评审缓存先写者赢与清理 | US-014/017/018/020/023 | 33 PASS | — |
| MOD-R26-13 发布协议 | test_publish_protocol_r26.py (22) | 首次发布基线+审计、先写提示词后写定义、冲突回执、校验失败 rejected 审计只含码、提示词文本校验、no_changes、预编译失败、写文件失败还原（一次性故障注入）、**审计写失败 ⇒ 发布不生效**、换引用失败不回滚、回滚/回滚到基线、崩溃恢复/busy、删除 agent 清理提示词、预览/只读候选、采纳漂移、说明 ≤200 | US-014/016/017/018/020/023 | 22 PASS | — |
| MOD-R26-07/08 工具与 LLM | test_agent_tools_enforce_r26.py (8) | 无授权无工具、scope 闭包、知识范围闭包且不在 JSON Schema、参数注入、未知工具编译期拒绝、**未授权调用回调只传工具名且不执行**、回调异常不影响问答、max_iterations | US-009/007/008 | 8 PASS | —（观察 OBS-R26-01） |
| MOD-R26-09 检索/路由 | test_doc_scope_filter_r26.py (9) | 目录范围不越界（成对正例）、空范围 0 命中且不查向量库、范围内无存活文档、解析器故障 fail-closed 降级、截断后过滤不越界、mode=all 等价基线、project_id 恒在过滤、restrict_to、LLM 客户端有界 LRU | US-009/029/006/014 | 9 PASS | — |
| MOD-R26-11 Builder | test_builder_adapt_rubric_r26.py (24) | 适配（工具/目录移除、越界调整、重名标记、条款缺失、业务词、截断、容错解析）、自评（维度和=100、等级、证据、10 次同分、LLM 项仅带引用才扣分、缓存键） | US-024/025/026/030 | 24 PASS | — |
| | test_builder_egress_r26.py (18) | 载荷字段=白名单、canary/project_id 不出站、密钥模式拦截（含 8 种形态）、审计先行且只记类别、审计失败取消外发、超时、错误分类、线程池满、需求校验、载荷上限 | US-030/024/028 | 18 PASS | — |

逐条 TC 与 AC 的映射见 test_plan.md「AC 映射」。

## 与基线对比（baseline 模式）

| 项 | 基线（改动前） | 本次 | 差异 |
|---|---|---|---|
| tests/unit passed | 314 | 509 | +195（全部为新写 `_r26` 用例） |
| 失败 | 0 | 0 | 新增失败 0；既有失败 0 |

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 本层无产品缺陷导致的失败 | — | — |

附：单元层发现的**观察项**（不阻断，详见 e2e_test_report「缺陷与观察」）：OBS-R26-01 `build_agent_tools` 文档串称越界参数“编译期 fail-fast”，实测不抛（范围由保存路径的 `validate_tool_params` 拦截，TC-UNIT-R26-069、TC-UNIT-R26-153 如实记录）。
