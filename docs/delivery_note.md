# 交付说明 — v1.2.0 增量：智能体框架通用化

| 项 | 值 |
|---|---|
| 文档 | 交付说明（非门控产物） |
| 日期 | 2026-09-27 |
| 增量范围 | REV-06 ~ REV-09（需求 → 架构 → 模块设计 → 实现 → 测试） |
| 结论 | GROUP_A/B/C/D 全部 APPROVED；PHASE_11 生产部署冻结 |

---

## 1. 交付目标

把基于 LangGraph 的智能体框架从「**专家写死、UI 诉求无 REQ 承接**」推进到：

> **声明式定义（专家 / 路由 / 编排 / 工具授权）+ 装配期 fail-fast 校验 + 可视化配置正式需求**，并全链贯通到架构、设计、实现与测试。

对应三条用户诉求：① 智能体按项目定义；② 可配置分工/路由/汇聚流程；③ 定义过程可 UI 可视化配置。

## 2. 交付物清单

| 阶段 | 产物 | 版本 | 关键变化 |
|---|---|---|---|
| 调研 | `docs/agent_platform_research.md` | RESEARCH-INTELBASE-001 | 9 个开源项目官方文档分析，映射 G1~G8 缺口 |
| 需求 | `docs/requirements_spec.md` | 1.1.0 → **1.2.0** | +3 REQ（IB-25/26/27），+1 OOS-10；REQ-FUNC 24→27 |
| 需求 | `docs/user_stories.md` | 1.1.0 → **1.2.0** | +2 US（US-IB-17/18），12 组验收标准 |
| 架构/设计 | `docs/architecture_design.md` / `module_design.md` / `tech_stack.md` | → **1.3.0** | 纳入 IB-25/26/27；MOD-IB-02 定义数据层 |
| 实现 | `src/ib/config/definition.py`（MOD-IB-02） | 新增 | 定义文档数据层（见 §5） |
| 实现计划 | `docs/implementation_plan.md` | → **2.4.0** | 旧计数「24」全链订正 |
| 评审 | `docs/code_review_report.md` | → R8 | CRITICAL 0/0 |
| 测试 | `docs/test_plan.md` / `test_report.md` | → **1.4.0** / **1.5.0** | 用例 149 → **171** |

## 3. 新增需求（REQ-FUNC-IB-25/26/27）

| REQ | 标题 | 一句话 |
|---|---|---|
| REQ-FUNC-IB-25 | 可视化配置界面 | 定义文档的**图形视图**，与文档**双向同源**（不是第二真源） |
| REQ-FUNC-IB-26 | 可视化可编辑边界 | 仅编辑**节点参数与专家集合**；拓扑（节点/边/条件边）永久不可编辑 |
| REQ-FUNC-IB-27 | 完备性校验 + fail-fast | 非法配置**装配期拒绝启动**，无「带病继续」开关 |

## 4. 核心架构决策（可直接复用）

1. **定义文档 = 唯一真源（ADR-15）**：专家 / 路由 / 编排 / 工具授权收敛为一份 `DefinitionDocument`；可视化视图**不得**另存一份数据。
2. **fail-fast 不可绕过（ADR-16）**：`ValidationReport` 字段集**不含** `force` / `ignore` / `warn_only`——「带病继续」在类型层就无法表达。
3. **可编辑白名单（REQ-FUNC-IB-26）**：拓扑字段（`orchestration.nodes` / `conditional_edges` 等）进入 `NON_EDITABLE_FIELDS`，永久不可编辑。
4. **按项目配置的正规路径**：LangGraph `context_schema` + `Runtime.context`（已弃用 `config_schema`），挂载点为 `orchestrator_for(project_id)`。
5. **handoff 三护栏**（若后续实现 G2）：往返上限 + 敏感工具强制批准 + 保留非 handoff 的正常回答出路（呼应「绝不无人应答」）。

## 5. 实现要点（MOD-IB-02 定义文档数据层）

`src/ib/config/definition.py` —— 只允许 stdlib + `ib.core`（framework-free）：

- **能力面**：装载（load）/ 完备性校验（validate）/ 只读派生（derive）/ 原子写回（save）/ 可编辑白名单（editable_field_whitelist）。
- **校验 11 项**（`validate()`，纯函数）：含本轮补齐的「跨专家路由关键词撞车」（大小写不敏感，`expert_keyword_collision`）与「cn_label 唯一性」（`expert_cn_label_duplicate`）。
- **契约**：`SUPPORTED_SCHEMA_VERSION = 1`，`DEFAULT_MAX_EXPERT_STEPS = 8`。
- **接入面**：`PUT /api/config/definition`（非法配置 → 400 逐条回执，不静默生效）；`src/scripts/selfcheck.py`。

> 说明：REQ-FUNC-IB-25 的「UI 可视化界面」本身是**正式需求（已写验收标准）**，属演进路线 P3，本增量**尚未实现前端**——先落数据层与校验，再落可视化（先定义数据化、后可视化，避免画布成为第二真源）。

## 6. 质量与测试

| 指标 | 结果 |
|---|---|
| 测试用例 | 149 → **171**（unit 67 / integration 88 / e2e 16） |
| 全量执行 | `pytest tests -q` **171 passed EXIT=0** |
| 自检 | `selfcheck.py` **31/31** |
| 缺陷 FND-R7-01 | **CLOSED_VERIFIED** |
| flaky 测试 FLAKE-IB-01 | **MITIGATED**（连接级异常 ≤3 次有界重试，结构+行为双证据证明不吞断言） |

## 7. 门控记录

| 门控 | 阶段 | 结论 |
|---|---|---|
| GR-A-002 / GR-A-003 | 需求 | PASS_WITH_CONDITIONS |
| GR-B-004 | 架构 | PASS |
| GR-C-005 / GR-C-006 | 模块设计/实现 | PASS / PASS_WITH_CONDITIONS |
| GR-D-004 / GR-D-005 / GR-D-006 | 测试 | 均 PASS_WITH_CONDITIONS |

## 8. 遗留与后续

- **PHASE_11 生产部署冻结**：须用户明确下达 `PRODUCTION_DEPLOY_CONFIRM`，且先闭合前置项 B-01/02/03/05/06、F-1 等。
- **UI 可视化（REQ-FUNC-IB-25）**：P3 待建，前置 P0/P1 已完成。
- **已知 MINOR**：`implementation_plan.md` L810 内嵌行号陈旧；3 项 open_item（0 字节证据 log / 范围外挂账 / 未提交弱证据限制）。
- **范围外已登记**：专家内关键词重复校验（BLK-R8-02，现由 `experts.validate_specs` 兜底）。

## 9. 演进路线（业界调研结论落地）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 声明式定义 + 启动期注入，复用 `install`/`validate_specs` | ✅ 本增量完成（定义数据层） |
| P1 | 提示外置 + G2（handoff 实现或删除）+ 专家表按项目生效 | 部分（数据层就绪） |
| P2 | 语义路由范例 + 金标集阈值校准 + 路由决策落盘 | 未开始 |
| P3 | UI 可视化（REQ-FUNC-IB-25） | 未开始（需求已就绪） |
