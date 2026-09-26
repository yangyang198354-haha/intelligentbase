---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-TR-001 |
| 标题 | intelligentbase 智能知识库基座 —— 测试执行报告 |
| 产出代理 | sub_agent_test_engineer |
| 调用 ID | INV-GROUP_D-INTELBASE-001；**R3 增量 = INV-GROUP_D-INTELBASE-002**（见 §10） |
| 项目 | intelligentbase |
| 阶段 | GROUP_D / PHASE_08（测试执行）+ PHASE_09（测试用例实现）+ **R3 增量（缺陷回归与门控）** |
| 版本 | 1.1.0（R3 增量：142/142 通过；FND-GROUP-D-01/02 → CLOSED_VERIFIED；新登记 FND-GROUP-D-03 / FLAKE-IB-01） |
| status | §1~§9 APPROVED（GROUP_D 门控 GR-D-001 = PASS_WITH_CONDITIONS，2026-09-26）；§10（R3 增量）为追加节，请 PM 复核 |
| 创建日期 | 2026-09-26 |
| 上游输入 | `docs/test_plan.md`（1.1.0）、`docs/user_stories.md`（1.1.0 / APPROVED）、`src/**`（只读） |
| 证据留档 | `docs/evidence/groupd_{unit,integration,e2e,all,coverage,credscan,fnd01_repro,fnd02_repro,defect_repros}.log`；**R3 增量 = `groupd_r3_{unit,integration,e2e,all,collect,credscan,blob_probe,targeted}.log`** |
| 测试套件 | `tests/unit/**`（3 文件 / 55）、`tests/integration/**`（8 文件 / 73）、`tests/e2e/**`（1 文件 / 14）、`tests/conftest.py` |
---

# intelligentbase 测试执行报告（GROUP_D / PHASE_08+09）

> **纪律声明**：本报告所有「通过」均由**真实执行的命令 + 原始输出**支撑（命令与 exit code 见 §2）；
> 本机无法真跑的项一律登记为 **not-verified**（§6），**不暗示其已通过**；
> 未修改任何实现代码（`src/ib/**`、`src/ibweb/**`、`src/ib_embed/**` 全程只读）。
> 原始日志全部落盘 `docs/evidence/`，可逐条复核。

---

## §1 结论摘要

| 级别 | Total | Pass | Fail | Skip | Blocked | 通过率 | 门控阈值 | 门控结论 |
|------|-------|------|------|------|---------|--------|---------|---------|
| 单元（UNIT） | 55 | 55 | 0 | 0 | 0 | **100.0%** | ≥ 80% | **PASSED** |
| 集成（INT） | 69 | 69 | 0 | 0 | 0 | **100.0%** | ≥ 90% | **PASSED** |
| E2E | 14 | 14 | 0 | 0 | 0 | **100.0%** | 关键路径 100% | **PASSED** |
| **合计** | **138** | **138** | **0** | **0** | **0** | **100.0%** | — | **全部 PASSED** |

- **关键路径覆盖率**：12 / 12 Must Have US = **100%**（US-IB-01/02/03/04/06/07/08/09/10/11/12/14）。
- **可测 AC 覆盖率**：67 / 67 = **100%**（11 项 NOT_TESTABLE 见 §6，不计入）。
- **需求覆盖**：16 / 16 US 均有用户故事级（E2E）用例 —— 见 §4。
- **CRITICAL 缺陷**：**0**。
- **MAJOR 缺陷**：1（FND-GROUP-D-02，见 §5）—— **不阻断 GROUP_D 门控**，但须路由 developer 修复。
- **MEDIUM 缺陷**：1（FND-GROUP-D-01，见 §5）—— 不阻断门控。
- **登记行为（非缺陷）**：1（D-R2-02 生产 `related_images` 恒空）。

**门控结论：GROUP_D 通过。** 单元 100% ≥ 80%，集成 100% ≥ 90%，三条流水线门控全部满足；无 CRITICAL 缺陷。

---

## §2 原始执行证据（命令 + 原始输出 + exit code）

所有命令的工作目录为 `C:\Users\胖子熊\MyProject\intelligentbase`；环境：`PYTHONUTF8=1 IB_OFFLINE_MODE=1`（`tests/conftest.py` 导入期另行设定 `IB_CONFIG_SOURCE=dict` 等）。原始日志见 `docs/evidence/`。

### 2.1 单元测试

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/unit -q
.......................................................                  [100%]
55 passed in 0.08s
EXIT=0
```
留档：`docs/evidence/groupd_unit.log`

### 2.2 集成测试（仅在单元 100% ≥ 80% 后执行）

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/integration -q
.....................................................................    [100%]
69 passed in 13.47s
EXIT=0
```
留档：`docs/evidence/groupd_integration.log`

### 2.3 E2E 测试（仅在集成 100% ≥ 90% 后执行）

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/e2e -q
..............                                                           [100%]
14 passed in 0.60s
EXIT=0
```
留档：`docs/evidence/groupd_e2e.log`

### 2.4 全量套件

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests -q
........................................................................ [ 52%]
..................................................................       [100%]
138 passed in 13.67s
EXIT=0
```
留档：`docs/evidence/groupd_all.log`

### 2.5 覆盖率

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests \
    --cov=ib --cov=ibweb --cov=ib_embed --cov-report=term-missing -q
TOTAL                               5918   1933    67%
EXIT=0
```
留档：`docs/evidence/groupd_coverage.log`（逐模块明细见 §7）

### 2.6 凭据扫描（AC-IB-12-02）

```
$ grep -rInE "sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}" src tests docs | wc -l
0
命中数: 0
结论: ZERO_CREDENTIALS
```
留档：`docs/evidence/groupd_credscan.log`。测试代码中的令牌均为环境变量占位符（`IB_OFFLINE_TOKEN` 默认 `groupd-offline-token`），无真实 key/token/密码。

### 2.7 度量自洽校验

```
单元：total 55 = pass 55 + fail 0 + skip 0 + blocked 0   ✓
集成：total 69 = pass 69 + fail 0 + skip 0 + blocked 0   ✓
E2E ：total 14 = pass 14 + fail 0 + skip 0 + blocked 0   ✓
合计：total 138 = pass 138 + fail 0 + skip 0 + blocked 0 ✓
通过率：pass/(pass+fail) = 55/55 = 100.0% / 69/69 = 100.0% / 14/14 = 100.0%
```
**算术一致：精确等式成立，无四舍五入导致的不等式。**

---

## §3 按层分项结果

### 3.1 单元测试（55/55）

| 文件 | 用例数 | TC-ID 范围 | 结果 | 覆盖模块 |
|------|-------|-----------|------|---------|
| `tests/unit/test_core_config_chunk_parse_stream.py` | 23 | TC-UNIT-001 ~ 022b | 23 PASS | L0 枚举/类型/错误、配置解析与校验、切分、魔数、解析器、SSE 帧、会话、脱敏 |
| `tests/unit/test_routing_experts_tools.py` | 20 | TC-UNIT-023 ~ 042 | 20 PASS | L2 余弦/打分/路由、专家注册表、工具注册与作用域绑定 |
| `tests/unit/test_embed_ledger.py` | 12 | TC-UNIT-043 ~ 054 | 12 PASS | `ib_embed` 配置闭集、Fake/Inproc Embedder、描述子、SQLite 台账状态机/幂等/级联 |

### 3.2 集成测试（69/69）

| 文件 | 用例数 | TC-ID 范围 | 结果 | 集成边界 |
|------|-------|-----------|------|---------|
| `test_composition_retrieval.py` | 10 | TC-INT-001 ~ 009, 054 | 10 PASS | MOD-IB-23 组合根 ↔ MOD-IB-15 检索 ↔ MOD-IB-10 向量库 |
| `test_lifecycle_page_images.py` | 7 | TC-INT-010 ~ 016 | 7 PASS | MOD-IB-08 生命周期 ↔ 页面图关联 ↔ 台账 |
| `test_ib_embed_wire.py` | 12 | TC-INT-017 ~ 028 | 12 PASS | MOD-IB-26 线协议（真实回环 HTTP） |
| `test_http_contract.py` | 13 | TC-INT-029 ~ 041 | 13 PASS | MOD-IB-23 WSGI ↔ 鉴权中间件 ↔ 视图/序列化 |
| `test_orchestration_related_images.py` | 7 | TC-INT-042 ~ 048 | 7 PASS | MOD-IB-14 编排 ↔ `related_images` 接缝 |
| `test_embed_conformance.py` | 5 | TC-INT-049 ~ 053 | 5 PASS | 三形态 Embedder 一致性 + C8 零耦合 |
| `test_gaps_acceptance.py` | 7 | TC-INT-055 ~ 060 | 7 PASS | 校验边界 / 错误码 / 核心零业务耦合 / kb 软隔离 |
| `test_ops_contract.py` | 8 | TC-INT-061 ~ 068 | 8 PASS | 可观测性 / 降级事件 / 外发声明 / 向量库可替换 / 幽灵文档偏差 |

### 3.3 E2E / 关键路径（14/14）

| TC-ID | 关联 US | 关键路径 | 结果 |
|-------|--------|---------|------|
| TC-E2E-001 | US-IB-01, US-IB-08 | 是 | PASS |
| TC-E2E-002 | US-IB-02 | 是 | PASS |
| TC-E2E-003 | US-IB-03 | 是 | PASS |
| TC-E2E-004 | US-IB-09 | 是 | PASS |
| TC-E2E-005 | US-IB-10 | 是 | PASS |
| TC-E2E-006 | US-IB-11, US-IB-06 | 是 | PASS |
| TC-E2E-007 | US-IB-04, US-IB-05 | 是（US-04） | PASS |
| TC-E2E-008 | US-IB-13 | 否 | PASS |
| TC-E2E-009 | US-IB-14 | 是 | PASS |
| TC-E2E-010 | US-IB-12 | 是 | PASS |
| TC-E2E-011 | US-IB-16 | 否 | PASS |
| TC-E2E-012 | US-IB-15 | 否 | PASS |
| TC-E2E-013 | US-IB-04（M-02 读路径） | 否 | PASS |
| TC-E2E-014 | US-IB-07 | 是 | PASS |

---

## §4 US → 测试用例映射（需求覆盖结论）

**结论：16 / 16 用户故事均有用例覆盖；12 / 12 Must Have 用户故事均有 E2E 级用例。**

| US | 优先级 | 单元 | 集成 | E2E | 用户故事级(E2E)覆盖 |
|----|-------|------|------|-----|-------------------|
| US-IB-01 导入文档 | Must | 012, 012b | 033, 034, 055 | E2E-001 | ✅ |
| US-IB-02 诊断重试 | Must | 020 | 016, 057, 058b, 061 | E2E-002 | ✅ |
| US-IB-03 管理下架 | Must | 052, 053 | 014, 033, 058 | E2E-003 | ✅ |
| US-IB-04 多格式导入 | Must | 008, 013, 014, 015 | 010, 012, 013, 044, 046, 048, 056 | E2E-007, E2E-013 | ✅ |
| US-IB-05 切分策略 | Should | 008, 009, 010, 011 | — | E2E-007 | ✅ |
| US-IB-06 向量库 | Must | 052, 053, 054 | 003, 004, 054, 060, 068 | E2E-006 | ✅ |
| US-IB-07 embedding 接入 | Must | 043~051 | 017~028, 049~053, 062 | E2E-014 | ✅ |
| US-IB-08 带来源回答 | Must | 016, 017 | 003, 007, 039 | E2E-001 | ✅ |
| US-IB-09 多智能体融合 | Must | 023~036 | 042 | E2E-004 | ✅ |
| US-IB-10 注册扩展 | Must | 037~042 | 008, 009, 063 | E2E-005 | ✅ |
| US-IB-11 配置接入项目 | Must | 002, 003, 004, 005, 006, 007, 018, 022 | 001, 002, 004, 030, 032, 035, 053, 054, 059 | E2E-006 | ✅ |
| US-IB-12 部署启动纪律 | Must | 004, 005, 006 | 029, 064 | E2E-010 | ✅ |
| US-IB-13 运行状态 | Should | 001, 020, 021 | 065, 066, 067, 005, 006, 029 | E2E-008 | ✅ |
| US-IB-14 降级不中断 | Must | 001 | 005, 006, 047, 052, 066 | E2E-009 | ✅ |
| US-IB-15 离线替身 | Should | 001~042 | 003, 005, 006 | E2E-012 | ✅ |
| US-IB-16 索引重建 | Should | 011 | 010, 011, 015, 016, 054 | E2E-011 | ✅ |

> 逐条 AC 的覆盖矩阵见 `docs/test_plan.md` §4。

---

## §5 发现的缺陷与偏差

> **R3 增量说明（见 §10）**：本节 5.1 / 5.2 两缺陷已由 developer 修复并经本轮回归验证 **CLOSED_VERIFIED**；
> 其下「复现命令」引用的是**修复前的固化用例名**，该三用例已在 R3 增量中**翻转为正向守卫并改名**
> （`..._gap_is_registered` → `..._reflects_builtin_tools`；`..._is_500` → `..._succeeds`；
> `..._is_registered` → `..._leaves_no_ghost`）。本节保留为**历史记录**，不复写。

### 5.1 FND-GROUP-D-01 —— 能力摘要恒为空（MEDIUM，非阻断）—— **R3 已修复 → CLOSED_VERIFIED（见 §10.5）**

| 项 | 内容 |
|----|------|
| 现象 | 组合根装配的 `Deps.capability_digest` 恒为空串；L2 路由提示恒为「（无可用工具）」 |
| 复现命令 | `python -m pytest tests/integration/test_composition_retrieval.py::test_TC_INT_009_capability_digest_registry_gap_is_registered -q`（EXIT=0，PASS 即复现） |
| 原始输出 | `docs/evidence/groupd_fnd01_repro.log`：`deps.capability_digest = ''` / `router prompt = '（无可用工具）'` / `bind_tools(p_alpha) = ['search_knowledge']` |
| 根因（供 developer 定位） | 契约 IFC-IB-182 与 `ROUTER_PROMPT{capabilities}` 期望摘要由**注册表**派生；但 `composition.build_deps()` 用**模块级 `default_registry`**（空）构建摘要，而基座自带的 `search_knowledge` 只被注册进 `bind_tools()` 内的**局部** `ToolRegistry` —— 装配接线遗漏。反证：临时向 `default_registry` 注册任一工具，摘要立即非空（说明摘要函数本身正确）。 |
| 影响面 | 仅 L2 LLM 路由提示质量（工具能力对路由不可见）；L0/L1/L3/默认层不受影响 |
| 严重度判定 | **MEDIUM**（不泄露数据、不崩溃、功能可用性降级）；**不阻断** GROUP_D 门控 |
| 建议处置 | 路由 software_developer：在组合根把 `bind_tools` 所用注册表接入 `build_capability_digest`（或让 `default_registry` 承载自带工具） |
| 处置边界 | 测试侧**未修改实现**，仅固化现状并使反证可见 |

### 5.2 FND-GROUP-D-02 —— 未绑定 collection 前删除 → 500 且产生「幽灵文档」（MAJOR，非阻断）—— **R3 已修复 → CLOSED_VERIFIED（见 §10.5）**

| 项 | 内容 |
|----|------|
| 现象 | 对**尚未有任何处理/检索**的项目删除刚上传（pending）的文档 → `delete_document` 抛 `StartupError` → HTTP 500；台账行**未被删除**；随后 worker 照常处理 → 该文档变 `indexed` **且可被检索到**（用户以为删了，内容仍在作答） |
| 复现命令 1 | `python -m pytest tests/integration/test_http_contract.py::test_TC_INT_041_delete_before_bind_is_500 -q`（EXIT=0，PASS 即复现；同时捕获 `Internal Server Error: /api/files/<id>`） |
| 复现命令 2 | `python -m pytest tests/integration/test_ops_contract.py::test_TC_INT_061_ghost_document_after_failed_delete_is_registered -q`（EXIT=0，PASS 即复现幽灵复活） |
| 原始输出 | `docs/evidence/groupd_fnd02_repro.log`：`uploaded doc_id = af0c5fe0… status = pending` / `collection bound? = None` / `delete_document raised = StartupError - [startup_error] InMemoryVectorStore 未绑定 collection 名；必须由组合根经 bind_collection(...) 注入（FM-5）` / `ledger row after delete = ('af0c5fe0…', 'pending')`；`groupd_defect_repros.log` 含 `Internal Server Error` |
| 根因（供 developer 定位） | `delete_document` → `vectors.delete_by_doc` → `_require_collection` 抛 `StartupError`：组合根**从不**在启动期绑定 collection，仅在选择性地 `_process_one`/检索路径惰性绑定；故在「本项目尚无事发生」的窗口内删除即失败，且失败**未回滚/未标记**，pending 行残留 → 被 worker 认领并索引 |
| 触及 AC | AC-IB-03-02（删除应生效）、AC-IB-03-03（已删文档不得出现在检索）、AC-IB-02-04（处理中删除应安全） |
| 严重度判定 | **MAJOR（HIGH）** —— 非 CRITICAL（无数据丢失、无凭据泄露、无全服务崩溃、重启后可恢复），但会造成**用户可见的正确性失效**（删除静默失效 + 已删内容仍被作答）。触发窗口较窄（项目自服务启动后从未处理/检索过任何文档） |
| 建议处置 | 路由 software_developer：删除路径不应依赖「collection 已绑定」；未绑定时应视为「无向量可删」而成功后置台账删除（或启动期即绑定各项目 collection）。**建议在 GROUP_E 部署前修复** |
| 处置边界 | 测试侧**未修改实现**，仅固化现状 + 记录后果 |

### 5.3 D-R2-02 —— 生产 `related_images` 恒空（登记行为，**非缺陷**）

- 复现：`TC-INT-048`（PASS）。生产编排器 `_related_images_events()` 恒以**空命中元组** `()` 调 provider；上游 R1 编排器不执行工具、不收集命中，故生产路径永不出图 —— 这正是 IFC-IB-282「空载荷即不发事件」的**正确**行为。
- 同时**证明接缝可用**：`TC-INT-044`（映射半：非空命中 → 只含路径载荷）、`TC-INT-046`（发送半：非空载荷 → 事件在 content 后到达）、`TC-E2E-013`（端到端：路径 → 取图 200）。缺的是「上游把命中传进来」，不是「下游发不出事件」。
- 处置：**保留「正确但未点亮」接缝**；不视为缺陷。若后续要点亮，需 R2+ 在编排器执行工具并回传命中。

### 5.4 环境偏差（不属实现缺陷）

| ID | 偏差 | 观测证据 | 影响 |
|----|------|---------|------|
| DEV-01 | 开发机 Python 3.14.6，`tech_stack` 约束 `>=3.11,<3.14`（承 R1 D-03） | `python -V` → 3.14.6 | 全用例在 3.14.6 上真实跑通；**不得**据此断言生产 3.11~3.13 等价 |
| DEV-02 | 本机 `langchain-openai` 1.3.3，违反冻结 pin `>=0.2,<0.3` | 装配 `openai_compatible` 时抛 `StartupError: langchain-openai 版本不满足约束 >=0.2,<0.3（实测 1.3.3）` | 远程 LLM 全链路无法在本机装配；`describe_egress` 改以类级验证（TC-INT-064） |
| DEV-03 | `pypdf`/`pdfminer`/`pdfplumber`/`pypdfium2`/`rapidocr_onnxruntime`/`FlagEmbedding`/`sentence_transformers`/`qdrant_client` 未安装（`docx`、`onnxruntime` 可用） | 逐包 import 探测 | 直接导致 §6 的 PDF/OCR/Qdrant not-verified 项 |

---

## §6 not-verified 清单（本机无法真跑，**不得视为已通过**）

| # | 项目 | 不可验证原因 | 替代证据（仅证明结构，不等于该项通过） |
|---|------|-------------|--------------------------------------|
| NV-01 | 真实 **bge-m3** 推理（向量维度/语义质量） | 无模型权重、无 FlagEmbedding | 维度一致性与冷热口径用 Fake/Inproc 结构验证（TC-E2E-014、TC-INT-051） |
| NV-02 | **onnxruntime** 真实运行 | 未在本轮测试路径中启用真实推理 runtime | 仅 import 探测可用；无运行时断言 |
| NV-03 | **PDF 文本层**解析（AC-IB-04-02） | `pypdf`/`pdfminer`/`pdfplumber` 缺失 | `pdf_parser.py` 覆盖率 12%；无真实 PDF 用例 |
| NV-04 | **扫描页 / 内嵌图 OCR**（AC-IB-04-06/07、AC-IB-14-04） | `pypdfium2` + `rapidocr_onnxruntime` 缺失 | 仅覆盖「不可用时跳过 + WARNING」结构的降级分支 |
| NV-05 | 真实 **Qdrant** 写入/重启持久化（AC-IB-06-01/03） | 需部署实例（且禁 Docker） | InMemory 替身验证端口契约与隔离（TC-INT-054） |
| NV-06 | **目标机** bge-m3 推理延迟 / 千级文档 P95（AC-IB-07-05、AC-IB-08-04） | 需目标机实测校准 | 本机数据不可替代目标机数据 |
| NV-07 | 前端 `npm install` / `vue-tsc` / `vite build`、页面自动刷新（AC-IB-01-06） | 本轮无前端运行环境 | HTTP 契约以 Django test Client 覆盖服务端侧 |
| NV-08 | 部署：systemd 常驻/开机自启/原生依赖真装（AC-IB-12-01/04） | 属 GROUP_E，本轮**冻结** | **未触碰** GROUP_E 任何步骤 |

---

## §7 覆盖率摘要（辅助度量，非门控）

```
$ python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed --cov-report=term-missing -q
TOTAL                               5918   1933    67%
```

高覆盖（测试直击的核心逻辑）：

| 模块 | 覆盖 |
|------|------|
| `ib/core/{enums,ports}.py`、`ib/core/__init__.py` | 100% |
| `ib/core/types.py` | 99% |
| `ib/chunking/__init__.py` | 98% |
| `ib/retrieval/__init__.py` | 93% |
| `ib/embedding/__init__.py` | 88% |
| `ibweb/composition.py` | 87% |
| `ib/observability/__init__.py` | 80% |
| `ib/lifecycle/__init__.py` | 80% |
| `ib_embed/server.py` | 76% |
| `ibweb/views.py` | 83% |
| `ibweb/{serializers,urls}.py` | 100% |

低覆盖（**由依赖缺失或部署入口所致，非测试疏漏**）：

| 模块 | 覆盖 | 原因 |
|------|------|------|
| `ib/parsing/pdf_parser.py` | 12% | 缺 `pypdf`/`pdfium`（NV-03/04） |
| `ib/embedding/inproc.py` | 27% | 缺 FlagEmbedding 权重（NV-01） |
| `ib_embed/runtime.py` | 33% | 真实 onnxruntime 路径未启用（NV-02） |
| `ib/ocr/__init__.py` | 33% | 缺 rapidocr（NV-04） |
| `ib/rendering/__init__.py` | 28% | 缺 pdfium 渲染（NV-04） |
| `ib/vectorstore/__init__.py` | 46% | Qdrant 分支不可达（NV-05） |
| `ibweb/{bootstrap,worker,wsgi}.py` | 0% | 进程入口/部署载入路径（NV-08） |

---

## §8 交付物与自检

| 交付物 | 路径 | 状态 |
|--------|------|------|
| 测试计划 | `docs/test_plan.md` | ✅ WRITTEN |
| 单元测试代码 | `tests/unit/`（3 文件 / 55 用例） | ✅ 55 PASS |
| 集成测试代码 | `tests/integration/`（8 文件 / 69 用例） | ✅ 69 PASS |
| E2E 测试代码 | `tests/e2e/test_user_journeys.py`（14 用例） | ✅ 14 PASS |
| 公共夹具 | `tests/conftest.py` | ✅ |
| 原始证据 | `docs/evidence/groupd_*.log` | ✅ 9 份 |

**自检清单**

- [x] AC 溯源：全部 138 用例均可溯源至 `user_stories.md` 的 AC-IB-NN-NN（无幻觉用例）
- [x] 算术自洽：三层 `total = pass + fail + skip + blocked` 精确成立
- [x] 门控串行：单元 100%≥80% → 集成 100%≥90% → E2E，严格按序
- [x] 未修改实现：`src/**` 全程只读
- [x] 未触碰 GROUP_E：无任何部署步骤
- [x] 离线：无外部网络/生产库/真实服务连接
- [x] 凭据纪律：仓库扫描零命中；测试代码无真实凭据
- [x] not-verified 如实登记（8 项），未冒充通过

---

## §9 需 PM 路由的动作

| # | 动作 | 对象 | 优先级 |
|---|------|------|--------|
| 1 | 修复 FND-GROUP-D-02（删除不依赖 collection 绑定；未绑定应成功后置删台账或启动期绑定） | software_developer | **MAJOR — 建议 GROUP_E 前修** |
| 2 | 修复 FND-GROUP-D-01（组合根把 `bind_tools` 注册表接入 `build_capability_digest`） | software_developer | MEDIUM |
| 3 | 处理 DEV-02（对齐 `langchain-openai` pin）与 DEV-01（Python 版本漂移） | software_developer / 环境 | 视部署计划 |
| 4 | 补验 not-verified 项（NV-03/04/05/06）——需目标机与缺失依赖 | GROUP_E 或后续轮次 | 部署阶段 |
| 5 | GROUP_D 门控复核（结论：3 层全 PASS，0 CRITICAL） | PM | 本轮 |

---

# §10 R3 增量回归报告（`INV-GROUP_D-INTELBASE-002`；追加，不改写 §1~§9）

> **背景**：software-developer 完成 R3（`INV-GROUP_C-INTELBASE-003`）修复 `test_report.md §5` 登记的两个缺陷。
> 本轮为 GROUP_D 增量：翻转三个「缺陷固化用例」为正向守卫、补 R3 定向回归、补一条**真并发**用例、
> 重跑全量并执行串行通过率门控。`docs/test_plan.md` §9 为对应的计划侧增量。
> **纪律**：本轮**未修改任何 `src/**` 实现代码**（新增/修改仅 `tests/integration/*.py` 与 `docs/**`）；
> 所有「通过」均由**真实执行的命令 + 原始输出**支撑；本机不可真跑的项一律如实登记（见 §10.6）。

## §10.1 结论摘要

| 级别 | Total | Pass | Fail | Skip | Blocked | 通过率 | 门控阈值 | 门控结论 |
|------|-------|------|------|------|---------|--------|---------|---------|
| 单元（UNIT） | 55 | 55 | 0 | 0 | 0 | **100.0%** | ≥ 80% | **PASSED** |
| 集成（INT） | 73 | 73 | 0 | 0 | 0 | **100.0%** | ≥ 90% | **PASSED** |
| E2E | 14 | 14 | 0 | 0 | 0 | **100.0%** | 关键路径 100% | **PASSED** |
| **合计** | **142** | **142** | **0** | **0** | **0** | **100.0%** | — | **全部 PASSED** |

- **缺陷闭环**：FND-GROUP-D-01 → **CLOSED_VERIFIED**；FND-GROUP-D-02 → **CLOSED_VERIFIED**（证据见 §10.5）。
- **新发现缺陷**：1（FND-GROUP-D-03，MAJOR，**非 R3 引入**，见 §10.6）+ 1 项环境偶发（FLAKE-IB-01）。
- **用例总数**：138 → **142**（三个固化用例翻转 + 四个新增；无 skip / 无 xfail）。
- **CRITICAL 缺陷**：**0**。

## §10.2 三个「缺陷固化用例」的翻转结果

> 翻转前（developer 交付态）：三用例**如设计般失败**（守卫串 `偏差已消除——请更新缺陷登记` / `DID NOT RAISE`），
> 证据 `docs/evidence/groupc_r3_after_fixated_defects.log`（`3 failed`）。
> 翻转后（本轮）：三用例改为**正向断言修复后的真值**，全部 **PASS**。

| 原用例名（固化缺陷） | 新用例名（正向守卫） | 翻转后结果 |
|---|---|---|
| `..._capability_digest_registry_gap_is_registered` | `test_TC_INT_009_capability_digest_reflects_builtin_tools` | **PASS** |
| `..._delete_before_bind_is_500` | `test_TC_INT_041_delete_before_bind_succeeds` | **PASS** |
| `..._ghost_document_after_failed_delete_is_registered` | `test_TC_INT_061_delete_before_processing_leaves_no_ghost` | **PASS** |

原始输出（本轮，逐条）：

```
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest \
    tests/integration/test_composition_retrieval.py::test_TC_INT_009_capability_digest_reflects_builtin_tools \
    tests/integration/test_composition_retrieval.py::test_TC_INT_073_capability_digest_matches_bound_tools \
    tests/integration/test_http_contract.py::test_TC_INT_041_delete_before_bind_succeeds \
    tests/integration/test_ops_contract.py::test_TC_INT_061_delete_before_processing_leaves_no_ghost \
    tests/integration/test_ops_contract.py::test_TC_INT_069_delete_indexed_document_counts_and_orphan_reconciliation \
    tests/integration/test_ops_contract.py::test_TC_INT_070_deleted_document_stays_unretrievable_across_reprocess \
    tests/integration/test_ops_contract.py::test_TC_INT_071_concurrent_delete_during_processing_skips_without_residue -v
```

守卫串已随翻转移除；若两缺陷复发，三条用例将**响亮失败**（回归闸门有效）。
原始输出留档：`docs/evidence/groupd_r3_targeted.log`（`7 passed`，含三个翻转 + 四个新增）。

## §10.3 新增回归用例清单（TC ↔ AC）

| TC-ID | 关联 US | 关联 AC | 用例名 | 覆盖的 R3 行为 |
|-------|--------|--------|--------|---------------|
| TC-INT-069 | US-IB-03 | AC-IB-03-02 | `test_TC_INT_069_delete_indexed_document_counts_and_orphan_reconciliation` | 已索引文档删除的 `DeleteReport` 三计数；**两次向量清扫**（首次清全部、竞态清扫为 0）；列表/台账/切块/向量/对账五不变式 |
| TC-INT-070 | US-IB-03 | AC-IB-03-03 | `test_TC_INT_070_deleted_document_stays_unretrievable_across_reprocess` | 删除后不可检索；再跑 `process_pending` **不复活** |
| TC-INT-071 | US-IB-02 | AC-IB-02-04 | `test_TC_INT_071_concurrent_delete_during_processing_skips_without_residue` | **真并发（2 线程）**：处理中被删 → `skipped`（非 failed）、无未捕获异常、无残留 |
| TC-INT-073 | US-IB-10 | AC-IB-10-03 | `test_TC_INT_073_capability_digest_matches_bound_tools` | 防漂移不变式：绑定工具名集合 == 摘要工具名集合，跨项目一致 |

> **覆盖缺口判定（不凑数）**：三条 AC 已各有既有映射（AC-IB-03-02 ← TC-INT-033/014/E2E-003；AC-IB-03-03 ← TC-E2E-003/TC-INT-061；AC-IB-02-04 ← TC-INT-061）。新增用例填补的是**修复行为**缺口（三计数 / 第二次清扫为 0 / 重跑不复活 / 并发 `skipped` 分类），修复前这些正确行为不可断言，故属定向补充而非重复。
> **AC 归属订正**：任务书将「能力摘要路由提示可见性」记于 AC-IB-02-04；按 `user_stories.md` 原文该可见性属 **AC-IB-10-03**，AC-IB-02-04 实为「处理中删除安全退出」。本轮两条均已覆盖（TC-INT-073 / TC-INT-071）。

## §10.4 真并发/竞态用例结论（R3-RISK-01）

`TC-INT-071` 以**真线程**（`threading.Thread`）运行 `process_pending`；worker 进入 `embed_documents` 即阻塞，
主线程此刻执行 `delete_document`（worker 确处「处理中」），随后放行 worker。实测：

- worker 走完剩余步骤撞上「台账行已不存在」→ `process_pending` 分类为 **`skipped`**（`processed=1, skipped=1, failed=0, succeeded=0`）；
- worker 线程**无未捕获异常**（`errors == []`）；
- 最终 `get_document → None`、`vectors.count → 0`、检索 `[]`、`list_orphan_doc_ids → []`（无幽灵向量）。

**诚实边界**：闸门落在**依赖替身（embedder）**上，故交错**确定可复现**，但本轮**未做**多进程/多 worker 压测，
亦未构造「进程级崩溃落在两次清扫之间」的更窄时序。该残窗仍由 `list_orphan_doc_ids` 对账 + 删除幂等兜底；
developer 的确定性探针 `groupc_r3_after_symptoms.log` 用例 (c) 覆盖其因果链。「真多进程压测」留待目标机阶段，
**本报告不据此声称该窗口已被压力测试证明**（R3-RISK-01 保持 MINOR）。

## §10.5 两个登记缺陷的闭环结论

| 缺陷 | 原级别 | 状态 | 闭环证据（本轮真实执行） |
|------|--------|------|------------------------|
| FND-GROUP-D-01（能力摘要恒为空 / 路由提示「（无可用工具）」） | MEDIUM | **CLOSED_VERIFIED** | `TC-INT-009` PASS（摘要非空且含 `search_knowledge`；`IntentRouter._capability_digest()` ≠「（无可用工具）」）+ `TC-INT-073` PASS（摘要工具名集合 == 实绑工具名集合）。原始输出 `docs/evidence/groupd_r3_all.log`（142 passed） |
| FND-GROUP-D-02（未绑库前删除 → 500 + 幽灵文档） | MAJOR | **CLOSED_VERIFIED** | `TC-INT-041` PASS（HTTP 删除 200、`ledger_deleted=True`、`vectors_deleted=0`、列表消失、再删 404）+ `TC-INT-061` PASS（worker 不认领、检索为空、无残留）+ `TC-INT-070` PASS（重跑不复活）。原始输出同上 |

**判据逐条对照**（`INV-GROUP_C-INTELBASE-003` §1.1）：

| 判据 | 本轮验证 | 结论 |
|------|---------|------|
| 尚无事发生 → 删除成功，`vectors_deleted=0`、`ledger_deleted=True` | TC-INT-041 / TC-INT-061 | ✅ |
| 删除后无幽灵（worker 不索引、不可检索） | TC-INT-061 / TC-INT-070 | ✅ |
| 不返回 500 / 不抛 `StartupError` 冒泡 | TC-INT-041（200） | ✅ |
| 文档不存在 → `NotFoundError` → 404 语义不变 | TC-INT-041（再删 404）/ TC-INT-058 | ✅ |
| `DeleteReport` 三计数与「先删派生物后删台账」顺序不变 | TC-INT-069 / TC-INT-014 | ✅ |
| `capability_digest` 非空含 `search_knowledge`；路由提示不再「无可用工具」 | TC-INT-009 / TC-INT-073 | ✅ |

## §10.6 新发现缺陷（登记，**不改实现**）

| ID | 现象 | 级别 | 复现命令 | 根因定位（供 developer） |
|----|------|------|---------|------------------------|
| **FND-GROUP-D-03** | 生产 HTTP 删除路径下原文件字节**未被删除**：`DeleteReport.blob_deleted` 恒为 `False`，BlobStore 中的原文件成为**孤儿**（已删文档的原始内容仍留在磁盘/内存）。**非 R3 引入**，为既有行为；本轮因正向断言 `blob_deleted` 而暴露 | **MAJOR**（保留/隐私 + 磁盘泄漏；不影响检索正确性、不崩溃） | `PYTHONUTF8=1 IB_OFFLINE_MODE=1 python docs/evidence/groupd_r3_blob_probe.py` → `docs/evidence/groupd_r3_blob_probe.log`（`blob_deleted=False`，删除后 BlobStore 对象数仍为 1） | `ibweb/views.py::file_detail_endpoint` 用 `composition.resolve_scope(ctx)` 得到**项目级** `Scope(project_id=..., kb_ids=None)`；而上传时原文件按 **kb 级**路径落盘（`_scope_of(ctx, kb_id)`）。`InMemoryBlobStore`/`FsBlobStore` 的 `delete(scope, doc_id)` 以 `(project, kb, doc)` 为键 → `kb_ids=None` 时回退 `"default"`，与落盘 kb 不符 → 删到 0 个、对象残留。修法建议：删除时按**文档实际 kb** 构造删除 scope，或让 BlobStore 删除按 `(project_id, doc_id)` 匹配（不依赖 kb） |

> 处置边界：测试侧**未修改实现**。§10.2 的 `TC-INT-041` 只断言 `blob_deleted` 为布尔（**按实**，不主张其应为 True），
> 未以失败断言固化该缺陷 —— 缺陷存在性证明由上述独立探针承载（`docs/evidence/groupd_r3_blob_probe.log`）。

**环境偶发（非产品缺陷）**：

| ID | 现象 | 级别 | 观测 |
|----|------|------|------|
| FLAKE-IB-01 | `tests/integration/test_ib_embed_wire.py` 回环真 HTTP 用例偶发 `ConnectionAbortedError: [WinError 10053]` | MINOR（环境） | 本会话 9 次集成层运行命中 2 次（`TC-INT-027`/`TC-INT-025` 各一次）；**单文件单独运行 3/3 通过**；随后**全量套件 5/5 连续 142 passed**。与 R3 改动**无关**（本轮未触碰该文件） |

## §10.7 全量重跑：命令 + EXIT + 原始计数（串行门控）

按串行门控顺序（单元 → 集成 → E2E → 全量）真跑，原始日志落盘 `docs/evidence/`：

```
# ① 单元（门控 ≥80%）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/unit -q
.......................................................                  [100%]
55 passed in 0.09s
EXIT=0                                   → 通过率 55/55 = 100.0% ≥ 80%  → PASSED
留档：docs/evidence/groupd_r3_unit.log

# ② 集成（门控 ≥90%；仅在 ① PASSED 后执行）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/integration -q
........................................................................ [ 98%]
.                                                                        [100%]
73 passed in 13.71s
EXIT=0                                   → 通过率 73/73 = 100.0% ≥ 90%  → PASSED
留档：docs/evidence/groupd_r3_integration.log

# ③ E2E（仅在 ② PASSED 后执行）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/e2e -q
..............                                                           [100%]
14 passed in 0.60s
EXIT=0                                   → critical path 12/12 = 100%    → PASSED
留档：docs/evidence/groupd_r3_e2e.log

# ④ 全量
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/ -q
........................................................................ [ 50%]
......................................................................   [100%]
142 passed in 13.79s
EXIT=0
留档：docs/evidence/groupd_r3_all.log

# ⑤ 用例搜集计数（防收缩交叉核对）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/ --collect-only -q
142 tests collected in 0.03s
（各目录 def test_ 静态计数：unit 55 + integration 73 + e2e 14 = 142，与 collect-only 一致）
留档：docs/evidence/groupd_r3_collect.log
```

**度量自洽校验**：

```
单元：total 55  = pass 55  + fail 0 + skip 0 + blocked 0   ✓
集成：total 73  = pass 73  + fail 0 + skip 0 + blocked 0   ✓
E2E ：total 14  = pass 14  + fail 0 + skip 0 + blocked 0   ✓
合计：total 142 = pass 142 + fail 0 + skip 0 + blocked 0   ✓
通过率 = pass/(pass+fail)：55/55 = 73/73 = 14/14 = 100.0%
```
**算术一致：精确等式成立；0 skip / 0 xfail；无 `-k` / `--deselect` / `--ignore` / `addopts` 等收缩测试面的手段。**

## §10.8 门控逐条判定

| 门控项 | 阈值 | 实测 | 判定 | 证据 |
|--------|------|------|------|------|
| 单元通过率 | ≥ 80% | 100.0%（55/55） | **达标** | `groupd_r3_unit.log` |
| 集成通过率 | ≥ 90% | 100.0%（73/73） | **达标** | `groupd_r3_integration.log` |
| E2E 关键路径覆盖 | 100% | 12/12 Must Have US = 100% | **达标** | `groupd_r3_e2e.log`；§3.3 |
| 全部 US-* 有测试 | 16/16 | 16/16（E2E 级 16 条） | **达标** | §4 |
| 可测 AC 覆盖 | 100% | 67/67（11 项 NOT_TESTABLE 不计） | **达标** | `docs/test_plan.md` §4 |
| metrics 算术一致 | 精确等式 | 三层精确成立 | **达标** | §10.7 |
| 0 skip / 0 xfail | 必须 | 0 / 0 | **达标** | 全量日志 |
| 未改实现代码 | 必须 | `src/**` 只读 | **达标** | §10.9 |

**门控结论：三层全 PASSED，串行门控（单元→集成→E2E）严格按序满足。**

## §10.9 守约复核与交付物

- **未改实现**：`src/**` 全程只读（本轮 `find src -mmin` 与编译核对：仅 developer 于 07:54~08:02 的 R3 改动，本轮无新写入）；`compileall -q src` EXIT=0。
- **改动面**：`tests/integration/test_composition_retrieval.py`（翻转 009 + 新增 073）、`tests/integration/test_http_contract.py`（翻转 041）、`tests/integration/test_ops_contract.py`（翻转 061 + 新增 069/070/071）；`docs/test_plan.md`（1.1.0）、`docs/test_report.md`（1.1.0）、`docs/evidence/groupd_r3_*.log`。
- **未触碰**：FreeArk 仓库、目标机 `192.168.31.133`、任何远程主机；无 Docker；未改 `requirements`/配置/凭据。
- **离线**：全程 SQLite/InMemory；回环 HTTP 仅 `127.0.0.1`；无外部网络/生产库。
- **凭据纪律**：`tests/` + `docs/evidence/` 强凭据形态扫描 0 命中（`groupd_r3_credscan.log`）。
- **诚实性**：FLAKE-IB-01 与 R3-RISK-01 的边界均如实登记；未声称未实测结论。

## §10.10 需 PM 路由的动作（R3 增量）

| # | 动作 | 对象 | 优先级 |
|---|------|------|--------|
| 1 | FND-GROUP-D-01 / FND-GROUP-D-02 复核闭环（结论：CLOSED_VERIFIED） | PM | 本轮 |
| 2 | 处置 **FND-GROUP-D-03**（生产删除路径原文件字节未清理 → 孤儿 blob） | software_developer | **MAJOR — 建议 GROUP_E 前修** |
| 3 | 评估 FLAKE-IB-01（回环 wire 测试偶发）是否需测试侧对连接级错误做有限重试 | software_developer / test | MINOR |
| 4 | GROUP_D R3 增量门控复核（结论：142/142 = 100%，三层全 PASSED，0 CRITICAL） | PM | 本轮 |

---

# §11 R4 增量回归报告（`INV-GROUP_D-INTELBASE-003`；追加，不改写 §1~§10）

> **背景**：software-developer 完成 R4（`INV-GROUP_C-INTELBASE-004`）修复 §10.6 登记的 **FND-GROUP-D-03**
> （生产删除路径原文件字节成孤儿）。本轮为该缺陷补**真实、非空壳、突变敏感**的回归用例，
> 重跑全量套件并执行串行通过率门控。`docs/test_plan.md` §10 为对应的计划侧增量。
> **纪律**：本轮**未修改任何 `src/**` 实现代码**（新增/修改仅 `tests/**` 与 `docs/**`，另加 `docs/evidence/groupd_r4_*`）；
> 所有「通过」均由**真实执行的命令 + 原始输出**支撑；突变敏感性经**独立副本**实测（见 §11.4），
> 副本在验证后已删除，真实 `src/` 全程只读。

## §11.1 结论摘要

| 级别 | Total | Pass | Fail | Skip | Blocked | 通过率 | 门控阈值 | 门控结论 |
|------|-------|------|------|------|---------|--------|---------|---------|
| 单元（UNIT） | 56 | 56 | 0 | 0 | 0 | **100.0%** | ≥ 80% | **PASSED** |
| 集成（INT） | 78 | 78 | 0 | 0 | 0 | **100.0%** | ≥ 90% | **PASSED** |
| E2E | 14 | 14 | 0 | 0 | 0 | **100.0%** | 关键路径 100% | **PASSED** |
| **合计** | **148** | **148** | **0** | **0** | **0** | **100.0%** | — | **全部 PASSED** |

- **新增用例**：6 条（TC-UNIT-055、TC-INT-074/075/076/077/078）；**强化既有守卫** 2 条（TC-INT-041、TC-E2E-003）。
- **用例总数**：142 → **148**（单元 55 → 56、集成 73 → 78、E2E 14 不变）；**0 skip / 0 xfail**。
- **缺陷闭环**：FND-GROUP-D-03 → **CLOSED_VERIFIED**（证据见 §11.3）。
- **CRITICAL 缺陷**：**0**。
- **未闭合/存疑**：见 §11.8（诚实标注）。

## §11.2 新增/强化用例清单（TC ↔ AC）

| TC-ID | 文件 | 关联 US | 关联 AC | 断言要点 |
|-------|------|--------|--------|---------|
| TC-UNIT-055 | `tests/unit/test_blob_kb_segment.py` | US-IB-03 | AC-IB-03-02 | `kb_segment(None|"") == "default"`；`blob_ref_for` 读路径第 2 段 == `kb_segment(record.kb_id)`；`FsBlobStore._doc_dir` 写路径项目级/显式空 kb 段同目录；`_blob_scope_of` 由记录派生且与写路径同段 |
| TC-INT-074 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | kb 级上传 + 项目级 `resolve_scope` 删除：`blob_deleted=True`；**真实文件系统**上 `on_disk`/doc 目录/空 kb 目录均不存在；根下 0 文件 |
| TC-INT-075 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 真实 Django HTTP `DELETE /api/files/{id}` + 真实 `FsBlobStore`：201→1 文件→200 `blob_deleted=True`→存储根下 0 文件，台账行 None |
| TC-INT-076 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | `submit_upload(data=None)` → `content_sha256==""`、`blob_ref_for==None`；删除 `blob_deleted is False`、`ledger_deleted is True`、根下 0 文件 |
| TC-INT-077 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 删 p_alpha 的 doc 后，p_beta 的**同内容** blob 与**同 doc_id** blob 均仍在；p_beta 台账行未被误删 |
| TC-INT-078 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配项目级 scope 删除未处理文档：HTTP 200（非 500）、`vectors_deleted=0`、台账行 None、`process_pending` 不再认领 |
| TC-INT-041（强化） | `tests/integration/test_http_contract.py` | US-IB-03 | AC-IB-03-02/03-03 | 追加：`blob_deleted is True` 且 `blobs.exists(ref) is False`（原仅断言布尔） |
| TC-E2E-003（强化） | `tests/e2e/test_user_journeys.py` | US-IB-03 | AC-IB-03-02/03-03 | 旅程末尾追加：`blob_deleted is True` 且 `blobs.exists(blob_ref_for(record)) is False` |

> **覆盖缺口判定（不凑数）**：AC-IB-03-02 既有映射已含 TC-INT-033/014/041/069/E2E-003，AC-IB-03-03 含 TC-E2E-003/061/070。
> 新增用例填补的是 **FND-GROUP-D-03 修复行为**的缺口 —— 「原文件字节确实被清理」在修复前不可断言（恒 False），
> 「本无 blob 不虚报」「跨项目不误删」「磁盘级无孤儿」三条亦为修复后才成立的可观测真值，故属定向补充而非重复。

## §11.3 FND-GROUP-D-03 闭环结论（CLOSED_VERIFIED）

| 缺陷 | 原级别 | 状态 | 闭环证据（本轮真实执行） |
|------|--------|------|------------------------|
| FND-GROUP-D-03（生产 HTTP 删除路径原文件字节未清理 → 孤儿 blob，`blob_deleted` 恒 False） | MAJOR | **CLOSED_VERIFIED** | TC-INT-074/075（真实文件系统 + 真实 HTTP 路径：`blob_deleted=True` 且磁盘 0 残留）+ TC-INT-041/TC-E2E-003（强化后的正向守卫 PASS）+ TC-UNIT-055（单一真源不变式 PASS）。原始输出 `docs/evidence/groupd_r4_all.log`（148 passed） |

**判据逐条对照**（任务书 §required_new_tests）：

| 判据 | 本轮验证 | 结论 |
|------|---------|------|
| kb 级上传 → 项目级删除：磁盘无任何 blob 字节，`blob_deleted is True` | TC-INT-074（`FsBlobStore.root` 文件系统断言）/ TC-INT-075（真实 HTTP） | ✅ |
| 本无 blob（D-08 `content_sha256` 空）→ `blob_deleted is False`（不恒 True） | TC-INT-076 | ✅ |
| 跨项目不误删（同 doc_id / 同内容 blob 仍在） | TC-INT-077 | ✅ |
| 不回归 FND-GROUP-D-02：fresh 装配 + 项目级 scope 删除仍成功、无 500、无 pending 幽灵 | TC-INT-078（+ 既有 TC-INT-041） | ✅ |
| 复用 R3 探针构造方式，对同一条真实 HTTP 路径做断言（加分项） | TC-INT-075 | ✅ |

## §11.4 突变敏感性自证（新用例如何抓住回退）

在仓库**副本** `.r4_mutant_check/`（测试后已删除；真实 `src/` 全程只读）上施加两处回退并运行新用例 + 强化守卫：

| 突变 | 施加方式 | 结果 | 失败用例 |
|------|---------|------|---------|
| A：`_blob_scope_of` 回退为项目级（旧写法，即缺陷原状） | `return Scope(project_id=record.project_id)` | **6 failed / 2 passed** | TC-UNIT-055、TC-INT-074、TC-INT-075、TC-INT-077、TC-INT-041、TC-E2E-003 |
| B：`kb_segment` 回退为恒等（丢失「空/None → default」） | `return kb_id` | **1 failed / 5 passed** | TC-UNIT-055 |

- 突变 A 下仍通过的 2 条：TC-INT-076（本无 blob，语义上仍为 False）、TC-INT-078（FND-GROUP-D-02 守卫，与突变点无关）——符合预期。
- 突变 B 只命中 TC-UNIT-055：集成用例均为 kb 级上传（真实 kb 非空，`kb_segment` 恒等与否不影响）；`kb_segment` 的「空 → default」规则敏感度由单元级 TC-UNIT-055 承载，与 `_blob_scope_of` 的行为敏感度（集成级）合起来覆盖任务书要求的「两处回退都会失败」。
- 原始输出留档：`docs/evidence/groupd_r4_mutation.log`。

**诚实边界**：突变实验在**副本**上进行（非在真实 `src/` 上临时改再还原），故真实 `src/` 无任何瞬时改动；副本测试期间其 `sys.path` 指向副本自身的 `src/`（`tests/conftest.py` 以 `__file__` 相对定位），不存在「副本测试跑了真实 src」的串味。

## §11.5 全量重跑：命令 + EXIT + 原始计数（串行门控）

```
# ① 单元（门控 ≥80%）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/unit -q
........................................................                 [100%]
56 passed in 0.10s
EXIT=0                                   → 通过率 56/56 = 100.0% ≥ 80%  → PASSED
留档：docs/evidence/groupd_r4_unit.log

# ② 集成（门控 ≥90%；仅在 ① PASSED 后执行）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/integration -q
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 13.06s
EXIT=0                                   → 通过率 78/78 = 100.0% ≥ 90%  → PASSED
留档：docs/evidence/groupd_r4_integration.log

# ③ E2E（仅在 ② PASSED 后执行）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests/e2e -q
..............                                                           [100%]
14 passed in 0.64s
EXIT=0                                   → critical path 12/12 = 100%    → PASSED
留档：docs/evidence/groupd_r4_e2e.log

# ④ 全量
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests -q
........................................................................ [ 48%]
........................................................................ [ 97%]
....                                                                     [100%]
148 passed in 13.74s
EXIT=0
留档：docs/evidence/groupd_r4_all.log

# ⑤ 用例搜集计数（防收缩交叉核对）
$ PYTHONUTF8=1 IB_OFFLINE_MODE=1 python -m pytest tests --collect-only -q
148 tests collected in 0.07s
（各目录 def test_ 静态计数：unit 56 + integration 78 + e2e 14 = 148，与 collect-only 一致）
留档：docs/evidence/groupd_r4_collect.log
```

**度量自洽校验**：

```
单元：total 56  = pass 56  + fail 0 + skip 0 + blocked 0   ✓
集成：total 78  = pass 78  + fail 0 + skip 0 + blocked 0   ✓
E2E ：total 14  = pass 14  + fail 0 + skip 0 + blocked 0   ✓
合计：total 148 = pass 148 + fail 0 + skip 0 + blocked 0   ✓
通过率 = pass/(pass+fail)：56/56 = 78/78 = 14/14 = 100.0%
```
**算术一致：精确等式成立；0 skip / 0 xfail；无 pytest 配置文件（无 addopts）；未用 `-k` / `--deselect` / `--ignore` / `@pytest.mark.skip|xfail`。**

## §11.6 门控逐条判定

| 门控项 | 阈值 | 实测 | 判定 | 证据 |
|--------|------|------|------|------|
| 单元通过率 | ≥ 80% | 100.0%（56/56） | **达标** | `groupd_r4_unit.log` |
| 集成通过率 | ≥ 90% | 100.0%（78/78） | **达标** | `groupd_r4_integration.log` |
| E2E 关键路径覆盖 | 100% | 12/12 Must Have US = 100% | **达标** | `groupd_r4_e2e.log`；§3.3 |
| 全部 US-* 有测试 | 16/16 | 16/16（E2E 级 16 条，未变） | **达标** | §4 |
| 可测 AC 覆盖 | 100% | 67/67（11 项 NOT_TESTABLE 不计） | **达标** | `docs/test_plan.md` §4 |
| metrics 算术一致 | 精确等式 | 三层精确成立 | **达标** | §11.5 |
| 0 skip / 0 xfail | 必须 | 0 / 0 | **达标** | 全量日志 |
| 未改实现代码 | 必须 | `src/**` 只读 | **达标** | §11.7 |

**门控结论：三层全 PASSED，串行门控（单元→集成→E2E）严格按序满足。**

## §11.7 守约复核与交付物

- **未改实现**：`src/**` 全程只读（`find src -name '*.py' -newermt '2026-09-26 08:50'` 空集，即本轮无任何 `src` 写入）；未新增/删改配置文件。
- **改动面**：`tests/unit/test_blob_kb_segment.py`（新增）、`tests/integration/test_blob_delete_scope_r4.py`（新增）、`tests/integration/test_http_contract.py`（TC-INT-041 强化）、`tests/e2e/test_user_journeys.py`（TC-E2E-003 强化）；`docs/test_plan.md` §3/§4/§10、`docs/test_report.md` §11、`docs/evidence/groupd_r4_*.log`。
- **未触碰**：FreeArk 仓库（`C:\Users\胖子熊\MyProject\FreeArk` 全程只读）、目标机 `192.168.31.133`、任何远程主机；无 Docker。
- **离线**：全程 SQLite/InMemory/临时文件系统根；回环 HTTP 仅 `127.0.0.1`；**未连**任何生产库 / Qdrant / DeepSeek / HF / 外部服务。
- **凭据纪律**：`src` + `tests` + `docs`（排除 `docs/evidence`）强凭据形态扫描 0 命中（`groupd_r4_credscan.log`）。
- **测试面未收缩**：新增用例均为**真实断言**（文件系统级 / HTTP 级 / 台账级），无 skip/xfail，无 addopts，未排除任何现有用例；三条既有翻转守卫（TC-INT-009/041/061）**继续通过**。

## §11.8 未闭合/存疑（诚实标注）

| # | 事项 | 性质 | 处置 |
|---|------|------|------|
| 1 | TC-INT-075 的收尾断言「存储根下 0 文件」在**同一用例内独占临时根**成立；若未来在同根内并发上传其他文档，该断言需收窄为「按 doc_id 过滤」。当前用例独占 `tmp_path`，故断言正确且更强 | 测试设计边界，非缺陷 | 已在此标注；如需复用根再收窄 |
| 2 | FLAKE-IB-01（回环 wire 测试偶发 `WinError 10053`）：本轮 5 次集成层运行**未复现** | 既有 MINOR 环境偏差，**未关闭** | 保持登记，不据「未复现」声称已修复 |
| 3 | `_blob_scope_of` 为模块私有函数，TC-UNIT-055 以白盒方式直接调用以断言单一真源不变式 | 白盒测试选择 | 行为侧敏感度由集成级 TC-INT-074/075/077 兜底，非唯一依赖 |
| 4 | 生产目标机（树莓派 + 真实 Qdrant/MySQL）上的删除行为**未在本轮实测**（离线约束） | not-verified | 本报告**不声称**生产环境已验证；仅证离线等价路径 |

## §11.9 需 PM 路由的动作（R4 增量）

| # | 动作 | 对象 | 优先级 |
|---|------|------|--------|
| 1 | FND-GROUP-D-03 复核闭环（结论：CLOSED_VERIFIED；补验证据见 §11.3） | PM | 本轮 |
| 2 | GROUP_D R4 增量门控复核（结论：148/148 = 100%，三层全 PASSED，0 CRITICAL，0 skip） | PM | 本轮 |
| 3 | FLAKE-IB-01 是否需测试侧对连接级错误做有限重试（本轮未复现，仍未关闭） | software_developer / test | MINOR |
| 4 | §11.8 第 1 项：TC-INT-075 若后续并入共享根需收窄断言 | test | 低（信息项） |
