---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-TP-001 |
| 标题 | intelligentbase 智能知识库基座 —— 测试计划 |
| 产出代理 | test-engineer |
| 调用 ID | INV-GROUP_D-INTELBASE-007（R10 增量；原 INV-GROUP_D-INTELBASE-001 ~ -006） |
| 项目 | intelligentbase |
| 阶段 | GROUP_D / PHASE_07（测试计划）+ R7 增量（US-IB-17 / US-IB-18「UI 可视化配置」纳入测试范围）+ **R8 增量（FND-R7-01 修复回归：装配期唯一性校验）** + **R9 增量（FLAKE-IB-01 测试侧稳定性治理：连接级有界重试）** + **R10 增量（前端冒烟测试层正式化：`src/frontend/tests/frontend.smoke.test.js` 6 例纳入测试计划）** |
| 版本 | 1.5.1（R10 增量 + 修复：**Python 三层用例数不变 171**（unit 67 / integration 88 / e2e 16）；**新增「前端冒烟测试层」6 例**（TC-FE-001~006）自立一层、**不计入 171 的算术**；运行方式 `node --test`（Node 20 内置，零新增依赖），CI 接入 `.github/workflows/ci.yml` 阶段9（`npm ci && npm run build && npm test`）；**R10 修复（REV-10-2 续）**：TC-INT-086 末尾「磁盘不存在性」近似判定与 R10 `npm ci` 冲突 → 已改为**分发纪律（git 跟踪状态）**环境自适应判定（见 §14.5）<br>R9 = 1.4.0（用例数不变 171；传输助手有限有界重试；FLAKE-IB-01 → MITIGATED）<br>**版本线**：1.0.0(R1) → 1.1.0(R3) → 1.2.0(R7) → 1.3.0(R8) → 1.4.0(R9) → 1.5.0(R10) → **1.5.1(R10 修复)**；执行报告文件版本线另见 `docs/test_report.md` 1.6.1/R10） |
| status | DRAFT（待 PM 门控） |
| 创建日期 | 2026-09-26 |
| 更新日期 | 2026-09-27（R10 增量） |
| 上游输入 | `docs/user_stories.md`（**1.2.0 / APPROVED，18 US / 90 AC**）、`docs/requirements_spec.md`（**1.2.0 / APPROVED**，含 REQ-FUNC-IB-25/26/27）、`docs/implementation_plan.md`（**2.4.0 / R8**，GROUP_C 门控 GR-C-005 = R7_PASS；其文件头 `<status>` 字段仍为 DRAFT，以 `docs/phase_status.md` 为权威）、`docs/architecture_design.md`（**1.3.0 / R7**，ADR-16）/ `docs/module_design.md` / `docs/tech_stack.md`（均 **1.3.0 / R7**）、`docs/code_review_report.md`（R7 增量 §12）、`docs/cicd_pipeline.md`（**1.1.1 / R10**，阶段9 定义）、`src/ib/**` + `src/ibweb/**` + `src/ib_embed/**` + `src/frontend/**`（只读） |
| 下游产物 | `docs/test_report.md`（PHASE_08/09 执行报告；R7 增量见其 §12、R8 增量见其 §13、R9 增量见其 §14、R10 增量见其 §15） |
| 环境约束 | 全部测试离线可跑：SQLite/内存替身/临时文件系统；**严禁**连接生产库 / 真实 Qdrant / DeepSeek / bge-m3 真实服务 / 任何外部网络 |
| 凭据纪律 | 任何 secret 只经环境变量注入，测试代码与夹具中不含真实 token/key/密码 |
---

# intelligentbase 测试计划（GROUP_D / PHASE_07）

> 本计划是 GROUP_D 的测试总纲。测试用例**一律**溯源至 `user_stories.md` 的验收标准（AC-IB-NN-NN）；
> 无 AC 溯源的用例视为幻觉用例，不予收录。执行结果与原始输出见 `docs/test_report.md`。

---

## §1 测试策略

### 1.1 测试目标

| # | 目标 | 度量 |
|---|------|------|
| G1 | 用户故事级功能正确：**18** 个 US 的验收标准在离线装配下被真实执行验证 | 可测 AC 覆盖率 100%（79/79；11 项 NOT_TESTABLE 不计，见 §5） |
| G2 | 关键路径端到端可用：Must Have 故事的完整用户旅程跑通 | 关键路径 E2E 覆盖率 100%（**14/14** Must Have US，含 US-IB-17/18） |
| G3 | 依赖故障可降级不中断：检索 fail-open、台账/字节 fail-closed | 降级场景用例全绿 |
| G4 | 项目/知识库隔离：结构化（collection-per-project）+ 软隔离（filter）双重验证 | 隔离用例全绿 |
| G5 | 契约纪律：`?token=` 一律 400、令牌不进 URL、外发边界如实声明 | 契约用例全绿 |
| G6 | 定义文档单一真源：可视化编辑**只**写回定义文档，无第二副本；非法配置装配期 fail-fast | US-IB-17/18 用例全绿 + 装配闸门聚合校验项 |
| G7 | 可回归：所有结论由真实命令 + exit code 支撑，偏差可追溯 | 原始输出留档 `docs/evidence/` |

### 1.2 范围

**In-scope（可离线验证）**
- L0 核心类型/枚举/错误码/配置解析与校验/契约纪律
- L1 切分、解析（txt/md/docx）、魔数校验、SSE 帧、会话存储、脱敏
- L2 路由（意图/语义）、专家注册表、工具注册与作用域绑定、能力摘要
- L3 检索（fail-open）、向量库端口（替身）、embedding 三形态（含回环真 HTTP 对拍）
- L4 入库生命周期、页面图关联（M-02 写路径）、删除级联、重试状态机
- L5 WSGI HTTP 契约（Django test Client）、编排事件序列、`related_images` 接缝
- `ib_embed`（MOD-IB-26）线协议、11 键闭集配置、C8 零耦合

**Out-of-scope（本机不可验证，登记为 not-verified，见报告 §6）**
- 真实 bge-m3 推理 / 目标机推理延迟
- onnxruntime 真实运行、PDF 文本层与扫描件 OCR（依赖 `pypdf*` / `pypdfium2` / `rapidocr`，本机缺失）
- 真实 Qdrant 部署与重启持久化
- 前端 `npm install` / `vue-tsc` / `vite build`（无 node 工具链执行）
- 部署（systemd、开机自启）——属 GROUP_E，**本轮不触碰**

### 1.3 测试环境

| 项 | 值 |
|----|-----|
| 开发机 | Windows 11，Python **3.14.6**（见 §7 偏差 DEV-01） |
| 测试框架 | pytest 9.1.1 + pytest-cov 7.1.0 |
| Web 载体 | Django 6.0.6 + DRF 3.17.1（`ibweb.test_settings` 风格：SQLite/内存） |
| 离线开关 | `IB_OFFLINE_MODE=1`、`IB_CONFIG_SOURCE=dict`、`IB_OFFLINE_TOKEN`（测试占位符）、`IB_LOG_LEVEL=ERROR` |
| 替身 | InMemory 台账 / InMemory 向量库 / FakeEmbedder / FakeLlmProvider |
| 回环真 HTTP | `ib_embed.server` 起 `127.0.0.1:0`（本机 socket，无外部依赖） |
| 覆盖率 | coverage 7.15.0，`--cov=ib --cov=ibweb --cov=ib_embed` |

环境在 `tests/conftest.py` 导入期一次性设定，测试无需额外配置即可离线运行。

### 1.4 覆盖率目标与门控阈值

| 级别 | 默认门控阈值 | 说明 |
|------|-------------|------|
| 单元测试 | 通过率 ≥ **80%** 方可进入集成测试 | 通过率 = pass / (pass + fail)，skip/blocked 不计入分母 |
| 集成测试 | 通过率 ≥ **90%** 方可进入 E2E 测试 | 同上 |
| E2E / 关键路径 | 关键路径（Must Have US）覆盖率 **100%** | 关键路径 = US-IB-01/02/03/04/06/07/08/09/10/11/12/14 + **US-IB-17/18**（共 **14** 个 Must Have US） |

PM 未在本轮 `special_instructions` 中覆盖阈值，故采用默认值（与 `docs/module_design.md` §12 声明一致）。

---

## §2 测试级别分类规则

对每个 AC，按其 Given/When/Then 涉及的模块范围固定分类：

| 级别 | 判定规则 | TC 前缀 |
|------|---------|---------|
| 单元（UNIT） | Given/When/Then 仅涉及单个函数/方法/类/纯数据结构的行为 | `TC-UNIT-NNN` |
| 集成（INT） | 涉及两个及以上模块协作（或端口接缝、HTTP 契约、线协议） | `TC-INT-NNN` |
| E2E | 描述完整用户操作路径（入口 → 出口，一条旅程） | `TC-E2E-NNN` |

同一 AC 可被多级别用例覆盖；分类一经确定，全篇一致。

---

## §3 测试用例清单

共 **171** 个用例：单元 67 / 集成 88 / E2E 16。所有用例 ID、所属 US、关联 AC、前置、动作、预期如下。（R3 增量：§3.2 新增 TC-INT-069/070/071/073，并翻转 TC-INT-009/041/061 为正向回归守卫，详见 §9。R4 增量：新增 TC-UNIT-055 与 TC-INT-074~078，并强化既有守卫 TC-INT-041 / TC-E2E-003，详见 §10。**R7 增量**：新增 16 条（单元 TC-UNIT-056~061 / 集成 TC-INT-079~086 / E2E TC-E2E-015~016），落在 **§11**；另，任务书简报所称「148 例」与实测不符 —— 实测基线为 **149 例**，其中 `TC-INT-072`（`test_ops_contract.py`，R5/R6 重建修复轮引入、见 `docs/deployment_report.md`）此前未登记入本文件，本轮行 **诚实标注** 而不掩盖。**R8 增量**：登记 software-developer 交付的 TC-UNIT-062~064（3 条，此前未入册）+ 本代理新增 TC-UNIT-065/066、TC-INT-087（3 条），合计净增 **6** 条，落在 **§12**。）

### 3.1 单元测试（67）

文件：`tests/unit/test_core_config_chunk_parse_stream.py`（23）、`tests/unit/test_routing_experts_tools.py`（20）、`tests/unit/test_embed_ledger.py`（12）、`tests/unit/test_blob_kb_segment.py`（1）、`tests/unit/test_definition_data_layer_r7.py`（6，R7 新增）、`tests/unit/test_definition_uniqueness_r8.py`（3，R8 / software-developer 交付）、`tests/unit/test_definition_uniqueness_extra_r8.py`（2，R8 / test-engineer 补测）。

| TC-ID | 关联 US | 关联 AC | 前置 | 动作 | 预期结果 |
|-------|--------|--------|------|------|---------|
| TC-UNIT-001 | US-IB-13/14 | AC-IB-13-04/14-01 | 枚举定义 | 读各枚举的 wire 值 | 值与契约字符串一致，可 JSON 序列化 |
| TC-UNIT-002 | US-IB-11 | AC-IB-11-02 | Scope 类型 | 构造带/不带 project_id 的 Scope | 项目作用域为必填签名，缺失即拒 |
| TC-UNIT-003 | US-IB-11 | AC-IB-11-04 | 默认配置表 | 读取各项默认值 | 可变行为均有显式默认，无硬编码主机/端口 |
| TC-UNIT-004 | US-IB-11/12 | AC-IB-11-03/12-03 | 缺项/非法配置 | 校验配置 | 报错仅列**键名**，不含值/凭据 |
| TC-UNIT-005 | US-IB-11/12 | AC-IB-11-04/12-02 | secret 类键 | 读取 secret | 仅从环境变量取，未配置则报错不落默认 |
| TC-UNIT-006 | US-IB-11/12 | AC-IB-11-03/12-03 | 非法整型 env | 解析 | 抛错并指明键名 |
| TC-UNIT-007 | US-IB-11 | AC-IB-11-04 | 原始配置 | normalize | 语义保持（仅补齐默认，不改语义） |
| TC-UNIT-008 | US-IB-05/04 | AC-IB-05-01/04-03 | 长文本 | 切分 | 相邻块有重叠，无空块 |
| TC-UNIT-009 | US-IB-05 | AC-IB-05-01 | 非法块参数 | 切分 | 显式拒绝非法参数 |
| TC-UNIT-010 | US-IB-05 | AC-IB-05-01 | 多段文本 | 切分 | 保留溯源地标，丢弃空内容 |
| TC-UNIT-011 | US-IB-05/16 | AC-IB-05-02/03 | 已入库文档 | 改切分参数 | 仅新文档用新参数，旧文档不自动重切 |
| TC-UNIT-012 | US-IB-01 | AC-IB-01-04 | 正/负样本 | sniff_magic | 伪造扩展名被识破 |
| TC-UNIT-012b | US-IB-01 | AC-IB-01-04 | 多字节前缀截断 | sniff_magic | 截断的多字节序列不误拒 |
| TC-UNIT-013 | US-IB-04 | AC-IB-04-05 | 未注册扩展名 | 注册表解析 | 显式报错；新格式可注册 |
| TC-UNIT-014 | US-IB-04 | AC-IB-04-01/03 | Markdown 文档 | 解析 | 溯源地标可读（标题层级/段落序号） |
| TC-UNIT-015 | US-IB-04 | AC-IB-04-03 | 空文本 | 解析 | 记 WARNING，不崩 |
| TC-UNIT-016 | US-IB-08 | AC-IB-08-01 | 事件流 | 渲染 SSE 帧 | 帧格式合法，done 收尾 |
| TC-UNIT-017 | US-IB-08 | AC-IB-08-01 | StreamEvent 别名 | 比较 | 别名恒等（同一对象） |
| TC-UNIT-018 | US-IB-11 | AC-IB-11-02 | 两会话 | 会话存储 | 项目间会话隔离 |
| TC-UNIT-019 | US-IB-15 | AC-IB-15-01 | 空载荷 | 生成 related_images 事件 | 空即抑制，不发事件 |
| TC-UNIT-020 | US-IB-02/13 | AC-IB-02-01/13-04 | 含敏感键字段 | redact | 敏感键丢弃/掩码，日志无凭据 |
| TC-UNIT-021 | US-IB-13 | AC-IB-13-04 | 超长字符串 | redact | 截断，不长吐 |
| TC-UNIT-022 | US-IB-11 | AC-IB-11-02 | 会话键 | 断言前缀 | 非法前缀被拒 |
| TC-UNIT-023 | US-IB-07/08 | AC-IB-07-02 | 向量对 | cosine | 值域与性质正确（自相似=1、对称） |
| TC-UNIT-024 | US-IB-09 | AC-IB-09-02 | 专家分值 | score_experts | 取每专家最大命中分 |
| TC-UNIT-025 | US-IB-09 | AC-IB-09-01 | τ/边际参数 | decide | 单专家/多专家/空按阈值判定 |
| TC-UNIT-026 | US-IB-09 | AC-IB-09-01 | 语义路由 | SemanticRouter | 项目分区，故障 fail-open |
| TC-UNIT-027 | US-IB-15 | AC-IB-15-03 | 脏输出（围栏/散文/非法名/空数组） | 解析 | 提取合法专家；无合法则安全回退 |
| TC-UNIT-028 | US-IB-09 | AC-IB-09-05 | 带历史的查询 | current_query | 剥离历史取当前问句 |
| TC-UNIT-029 | US-IB-09 | AC-IB-09-01 | 单域问句 | 路由 | 恰一个专家，无额外分支 |
| TC-UNIT-030 | US-IB-09 | AC-IB-09-02 | 复合问句 | 路由 | 多专家并行候选（2~3） |
| TC-UNIT-031 | US-IB-09 | AC-IB-09-04 | 极端输入 | 路由 | 任何情况下不出现「无人应答」 |
| TC-UNIT-032 | US-IB-09 | AC-IB-09-04/06 | 域外问句 | 路由 | 转通用路径，不调工具 |
| TC-UNIT-033 | US-IB-09 | AC-IB-09-04 | 分类器故障 | 路由 | 确定性关键词回退，落默认专家 |
| TC-UNIT-034 | US-IB-09 | AC-IB-09-05 | 上一轮专家 | 路由 | 承接粘性专家 |
| TC-UNIT-035 | US-IB-09 | AC-IB-09-04 | 触发护栏的输入 | 路由 | 重路由至数据专家 |
| TC-UNIT-036 | US-IB-09 | AC-IB-09-07 | 同问句重复 | 路由 | 同输入同结果（确定性） |
| TC-UNIT-037 | US-IB-10 | AC-IB-10-01/02/04 | 专家注册表 | 加载与派生视图 | 派生视图自动含新专家，顺序稳定，缺提示文件走兜底 |
| TC-UNIT-038 | US-IB-10 | AC-IB-10-01/02 | 非法注册表 | validate_specs | 结构非法被拒（如多默认专家） |
| TC-UNIT-039 | US-IB-10 | AC-IB-10-01 | 不存在的专家 | get | 返回 None，不抛 |
| TC-UNIT-040 | US-IB-10 | AC-IB-10-03 | 已注册工具 | build_capability_digest | 摘要由名称+描述派生；空/异常返回空串不抛 |
| TC-UNIT-041 | US-IB-10/11 | AC-IB-10-03/11-06 | 已绑作用域工具 | 调用方传 scope 覆盖 | 绑定闭包忽略之（override 不可能） |
| TC-UNIT-042 | US-IB-10 | AC-IB-10-03 | 作用域参数 | bind_scope | 隐藏 scope 形参，不外泄 |
| TC-UNIT-043 | US-IB-07 | AC-IB-07-01 | ib_embed 配置 | 加载 | 仅消费 11 键闭集，未知键报错 |
| TC-UNIT-044 | US-IB-07 | AC-IB-07-01 | 缺 MODEL_PATH | 加载 | 键名级报错，不回显值 |
| TC-UNIT-045 | US-IB-07/12 | AC-IB-07-01/12-02 | ib_embed 配置 | 检查消费键与日志字段 | 只吃 `IB_EMBED_*`；日志无凭据、不含 model_path |
| TC-UNIT-046 | US-IB-07 | AC-IB-07-02 | FakeRuntime | 向量化 | 确定性、保序、归一化 |
| TC-UNIT-047 | US-IB-07 | AC-IB-07-01 | 加载失败 | FakeRuntime | 返回可读错误，不崩 |
| TC-UNIT-048 | US-IB-07 | AC-IB-07-02 | FakeEmbedder | 冷/热路径 | 同文自相似度 ≈ 1 |
| TC-UNIT-049 | US-IB-07 | AC-IB-07-01 | fake/inproc | descriptor | 恰五字段，字段集一致 |
| TC-UNIT-050 | US-IB-07 | AC-IB-07-01 | inproc 缺权重 | 构造 | DependencyUnavailableError 且点名 `IB_EMBED_MODEL_PATH` |
| TC-UNIT-051 | US-IB-07 | AC-IB-07-01 | 各 backend 值 | build_embedder | 值域 {http,inproc,fake}，未知回退 http |
| TC-UNIT-052 | US-IB-03/06 | AC-IB-03-02/06-04 | SQLite 台账 | 状态机/单租约/reap | 状态迁移合法，同时仅一租约，超时回收 |
| TC-UNIT-053 | US-IB-03/06 | AC-IB-03-02/06-04 | 图片关联行 | 幂等写/陈旧清理/级联 | 键幂等、陈旧行清理、删文档级联，跨项目不可见 |
| TC-UNIT-054 | US-IB-06 | AC-IB-06-01 | SQLite 连接 | PRAGMA | WAL + busy_timeout 生效 |
| TC-UNIT-055 | US-IB-03 | AC-IB-03-02 | `kb_segment` / `blob_ref_for` / `_blob_scope_of` | 校验规则与三处推导同源 | **（R4 新增）** `None`/`""` → `"default"`；写/读/删三路径落到同一 kb 段——FND-GROUP-D-03 单一真源不变式 |
| TC-UNIT-062 | US-IB-18 | AC-IB-18-02 | 两位专家（合法/撞词/大小写/空白/同专家内重复） | `validate` 判跨专家关键词撞车 | **（R8 登记）** 互不相交 → 通过；精确/大小写/空白重复 → `expert_keyword_collision` 且含冲突词与两专家名；同专家内重复不报 |
| TC-UNIT-063 | US-IB-18 | AC-IB-18-02 | 两位专家（合法/同标签/空白填充/空标签/大小写） | `validate` 判 `cn_label` 唯一 | **（R8 登记）** 互异 → 通过；精确/空白填充重复 → `expert_cn_label_duplicate`（`path=experts[b].cn_label`）；空标签由 `expert_text_missing` 承担；大小写不归一 |
| TC-UNIT-064 | US-IB-18 | AC-IB-18-02 | 默认注册表 + 默认派生文档 | 校验默认数据无撞车/无重标签 | **（R8 登记）** 默认 `keywords_map()`/`cn_map()` 无跨专家撞车、标签唯一；默认派生文档 `validate.ok is True` 且无误报（反向护栏） |
| TC-UNIT-065 | US-IB-18 | AC-IB-18-02 | 空/纯空白关键词；三名专家同词；大小写+空白叠加 | `validate` 关键词撞车的边界分支 | **（R8 新增）** 空/纯空白不误报；三名专家同词 → 2 条（首见者持有，`experts[b]/[c]` 各一）；叠加归一判撞车；精确 path `experts[b].keywords[<原样>]` |
| TC-UNIT-066 | US-IB-18 | AC-IB-18-02 | 三名专家同标签；全空白标签；同时撞词+同标签 | `validate` 标签唯一性的边界分支与两项独立性 | **（R8 新增）** 三名同标签 → 2 条且 path 归属正确；全空白跳过（交 `expert_text_missing`）；两项校验独立（两错误码并存） |

### 3.2 集成测试（88）

文件：`test_composition_retrieval.py`（11）、`test_lifecycle_page_images.py`（7）、`test_ib_embed_wire.py`（12）、`test_http_contract.py`（13）、`test_orchestration_related_images.py`（7）、`test_embed_conformance.py`（5）、`test_gaps_acceptance.py`（7）、`test_ops_contract.py`（**12**）、`test_blob_delete_scope_r4.py`（5）、`test_definition_config_r7.py`（**9**：R7 新增 8 + R8 新增 TC-INT-087）。

> **计数订正（诚实标注）**：`test_ops_contract.py` 实为 **12** 例（含 R5/R6 重建修复轮引入的 `TC-INT-072`，见 `docs/deployment_report.md` §… ），此前本计划记为 11 —— 导致「集成 78 / 合计 148」的旧计数比实测少 1。本轮以**实测**为准：基线 **149**（单元 56 / 集成 79 / E2E 14）。

| TC-ID | 关联 US | 关联 AC | 前置 | 动作 | 预期结果 |
|-------|--------|--------|------|------|---------|
| TC-INT-001 | US-IB-11 | AC-IB-11-01 | 组合根装配 | 检查各端口/项目/前缀/工具 | 端口齐备、前缀断言通过、未登记项目报 StartupError |
| TC-INT-002 | US-IB-11 | AC-IB-11-01 | 装配 | 取两项目编排器 | 同项目复用同一对象，不同项目不同 |
| TC-INT-003 | US-IB-01/06/08 | AC-IB-01-05/06-01/08-01 | 真实上传管线 | 上传→处理→检索 | 命中该文档且不降级 |
| TC-INT-004 | US-IB-06/11 | AC-IB-06-02/11-02 | 甲项目语料 | 乙项目检索 | 空命中（项目硬隔离） |
| TC-INT-005 | US-IB-14/07 | AC-IB-14-01/07-03 | embedder 故障 | 检索 | degraded 结果，reason=EMBEDDING_UNAVAILABLE，不抛 |
| TC-INT-006 | US-IB-14 | AC-IB-14-03 | 向量库故障 | 检索 | degraded，reason=VECTORSTORE_UNAVAILABLE，不抛 |
| TC-INT-007 | US-IB-08/14 | AC-IB-08-02/14-02 | 三态 | search_as_tool | 降级/空/命中均 ok=True |
| TC-INT-008 | US-IB-10 | AC-IB-10-03 | 绑定 p_beta 工具 | 调用方传 scope=p_alpha | 覆盖无效，不泄漏甲项目内容 |
| TC-INT-009 | US-IB-10 | AC-IB-10-03 | 组合根 | 读 capability_digest + 路由提示 | **（R3 翻转）** 摘要非空且含 `search_knowledge`；路由提示非「（无可用工具）」——FND-GROUP-D-01 回归守卫 |
| TC-INT-010 | US-IB-04/16 | AC-IB-04-06 | `_process_one` 记录代理 | 处理一份含图文档 | 写序：向量 → 页面图 → 块 → mark_indexed |
| TC-INT-011 | US-IB-16 | AC-IB-16-02 | 空队列 | process_pending | 无操作且报告状态正确 |
| TC-INT-012 | US-IB-04 | AC-IB-04-06 | 解析结果 | bind_page_images | 按页聚合，确定性输出 |
| TC-INT-013 | US-IB-04/03 | AC-IB-04-06/03-02 | 图片绑定 | persist_page_images | 幂等，陈旧行被清理 |
| TC-INT-014 | US-IB-03 | AC-IB-03-02 | 含图文档 | 删除 | 级联清理页面图与台账行 |
| TC-INT-015 | US-IB-14/16 | AC-IB-14-04/16-04 | 单文档失败 | 批处理 | 单文档失败不影响其他文档 |
| TC-INT-016 | US-IB-02/16 | AC-IB-02-02/16-02 | failed 文档 | 重试 | 仅 failed 可重试；重试幂等无重复块 |
| TC-INT-017 | US-IB-07 | AC-IB-07-01 | 回环 ib_embed 服务 | GET /healthz | 永不 5xx |
| TC-INT-018 | US-IB-07 | AC-IB-07-01 | 服务 | POST /embed | 保序，维度以服务端为准 |
| TC-INT-019 | US-IB-07 | AC-IB-07-01 | 超批上限 | POST /embed | 回显 max_batch 并拒绝超批 |
| TC-INT-020 | US-IB-07 | AC-IB-07-01 | 模型不匹配 | POST /embed | 409 |
| TC-INT-021 | US-IB-07/14 | AC-IB-07-01/14-01 | 未 ready | POST /embed | 503（不返回部分向量） |
| TC-INT-022 | US-IB-07 | AC-IB-07-01 | 非法请求体 | POST /embed | 400，且无部分结果 |
| TC-INT-023 | US-IB-07 | AC-IB-07-01 | 参差输出 | POST /embed | 500，且不返回部分向量 |
| TC-INT-024 | US-IB-07/13 | AC-IB-07-01/13-02 | 过载（并发 1/队列 0） | POST /embed | 503 + retry_after_s |
| TC-INT-025 | US-IB-07 | AC-IB-07-01 | 服务 | POST /warmup ×2 | 幂等 |
| TC-INT-026 | US-IB-07/14 | AC-IB-07-01/14-01 | 加载失败 | POST /warmup | 快速失败 500 |
| TC-INT-027 | US-IB-07 | AC-IB-07-01 | 服务 | GET /descriptor | 恰五字段 |
| TC-INT-028 | US-IB-07 | AC-IB-07-01 | 服务 | 未知路径 + 查询串 | 404；查询串被丢弃 |
| TC-INT-029 | US-IB-13/12 | AC-IB-13-02/12-05 | HTTP 客户端 | GET /healthz、/healthz/deps | 免鉴权 200；依赖健康与 egress.remote=False 如实 |
| TC-INT-030 | US-IB-11 | AC-IB-11-05 | 无/错令牌 | GET /api/files | 401，不静默通过 |
| TC-INT-031 | US-IB-11 | AC-IB-11-05 | 查询串含令牌 | 各端点 | 一律 400 `token_in_query_forbidden`（IC-IB-01） |
| TC-INT-032 | US-IB-11 | AC-IB-11-05 | X-IB-Project 不符 | GET /api/files | 403 `project_mismatch` |
| TC-INT-033 | US-IB-01/03 | AC-IB-01-01/03-01/03-02 | 上传件 | 上传→列表→删除 | 201/字段白名单/删除生效 |
| TC-INT-034 | US-IB-01 | AC-IB-01-02/01-04 | 伪造扩展名 | 上传 | 400，不落台账 |
| TC-INT-035 | US-IB-11/06 | AC-IB-11-05/06-02 | 他项目 kb_id | 上传 | 403，不留痕 |
| TC-INT-036 | US-IB-04/03 | AC-IB-04-06 | 有字节的图关联 | GET 图片 | 200 + 固定 MIME + nosniff + private cache |
| TC-INT-037 | US-IB-03/11 | AC-IB-03-03/11-02 | 图关联 | 多 404 变体（缺行/无字节/跨项目） | 一律 404，反存在性探测 |
| TC-INT-038 | US-IB-11 | AC-IB-11-05 | 图片端点 | `?token=` | 400 |
| TC-INT-039 | US-IB-08 | AC-IB-08-01 | SSE 端点 | 缺 q / 正常请求 | 400 / text/event-stream，事件序合法 |
| TC-INT-040 | US-IB-16 | AC-IB-16-01 | 重建端点 | POST /api/rebuild | 202 + job_id，进度可查 |
| TC-INT-041 | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配未绑库 | 上传后立即删除 | **（R3 翻转，R4 强化）** 200 且 `ledger_deleted=True`、`vectors_deleted=0`、`blob_deleted=True` 且原文件引用失效，列表消失，再删 404——FND-GROUP-D-02 + FND-GROUP-D-03 回归守卫 |
| TC-INT-042 | US-IB-09 | AC-IB-09-03 | 编排器 | 运行一次问答 | 事件序 reasoning→content→done，content 仅一条 |
| TC-INT-043 | US-IB-14 | AC-IB-14-01 | LLM 故障 | 运行问答 | degraded 早于 content，done 收尾 |
| TC-INT-044 | US-IB-04 | AC-IB-04-06 | 有图关联的命中 | 调 provider | 载荷只含站内路径，绝无 base64 |
| TC-INT-045 | US-IB-11 | AC-IB-11-02 | provider 作用域 | 跨项目命中 | None，不泄漏存在性 |
| TC-INT-046 | US-IB-04 | AC-IB-04-06 | 注入非空载荷 | 运行问答 | 事件在 content 后、done 前到达（接缝可用） |
| TC-INT-047 | US-IB-14 | AC-IB-14-01 | 空载荷 / provider 抛错 | 运行问答 | 不发事件、不中断（fail-open） |
| TC-INT-048 | US-IB-04 | AC-IB-04-06 | 生产编排器 + 库中有图 | 运行问答 | 固化 D-R2-02：生产恒不发图（登记行为，非缺陷） |
| TC-INT-049 | US-IB-07 | AC-IB-07-01 | 三 backend | build_embedder | 三形态同构描述子，方法齐备 |
| TC-INT-050 | US-IB-07 | AC-IB-07-01 | 干净解释器 | 导入 ib_embed 全模块 | 零 `ib.*` 耦合（C8） |
| TC-INT-051 | US-IB-07 | AC-IB-07-02 | 回环服务 | LocalHttpEmbedder 冷/热 | 保序、维度一致、冷热对齐、健康可读 |
| TC-INT-052 | US-IB-14 | AC-IB-14-01 | 不可达 base_url | embed_query | DependencyUnavailableError；health 不抛 |
| TC-INT-053 | US-IB-11 | AC-IB-11-03 | 非法 backend | 配置校验 | 值域闭集被拒 |
| TC-INT-054 | US-IB-06/16 | AC-IB-06-01/06-04/16-01 | 两项目 | count/清理/维度不变式 | 项目即 collection；按 scope 清理；换维度显式报错 |
| TC-INT-055 | US-IB-01 | AC-IB-01-03 | 超限文件 | validate_upload | ValidationError（含上限），不落台账 |
| TC-INT-056 | US-IB-04 | AC-IB-04-04 | `.xlsx` | validate_upload | 可读报错点名格式与支持清单，不落台账 |
| TC-INT-057 | US-IB-02 | AC-IB-02-03 | indexed 文档 | retry_document | ConflictError 回显当前状态，数据不变 |
| TC-INT-058 | US-IB-03 | AC-IB-03-04 | 不存在的 doc_id | HTTP 删除 | 404 `not_found` |
| TC-INT-058b | US-IB-02 | AC-IB-02-03 | indexed 文档 | HTTP 重试 | 409 `conflict` |
| TC-INT-059 | US-IB-11 | AC-IB-11-06 | 干净解释器 | 导入 ib.orchestration | 无 Django/DRF 业务载体耦合 |
| TC-INT-060 | US-IB-06 | AC-IB-06-02 | 同项目两 kb | 按 kb 作用域检索 | 互不可见（软隔离 filter） |
| TC-INT-061 | US-IB-02/03 | AC-IB-02-04/03-03 | 未绑库 fresh 装配 | 上传→删→ worker 处理 | **（R3 翻转）** 删除成功、台账行消失、worker 不认领、检索为空、无向量残留——FND-GROUP-D-02 回归守卫 |
| TC-INT-069 | US-IB-03 | AC-IB-03-02 | 已索引文档 | 删除并观测 `DeleteReport` 与清扫次数 | **（R3 新增）** 三计数语义 + 两次清扫（第二次为 0）+ 列表/台账/切块/向量/对账五不变式 |
| TC-INT-070 | US-IB-03 | AC-IB-03-03 | 已索引文档 | 删除 → 再跑 `process_pending` | **（R3 新增）** 删除后不可检索；重跑不复活（可见性权威 = 台账） |
| TC-INT-071 | US-IB-02 | AC-IB-02-04 | pending 文档 + 真并发（2 线程） | worker 处理中被删除 | **（R3 新增，真并发）** 计数为 `skipped`（非 failed），无未捕获异常，无残留 |
| TC-INT-073 | US-IB-10 | AC-IB-10-03 | 组合根 | 绑定工具名集合 vs 摘要工具名集合 | **（R3 新增）** 两集合逐名相等（防漂移不变式），跨项目一致 |
| TC-INT-062 | US-IB-07 | AC-IB-07-03 | 冷/热配置 | 读配置 + 驱动检索 | cold 超时/重试严格宽于 hot；查询走有界超时 |
| TC-INT-063 | US-IB-10 | AC-IB-10-05 | 专家注册表 | 读委派标记 + 步数上限 | 非委派专家不获子委托；深度有硬上限 |
| TC-INT-064 | US-IB-12 | AC-IB-12-05 | 离线/远程 LLM | describe_egress | 离线 remote=False；远程 remote=True + 端点 + 数据类别 |
| TC-INT-065 | US-IB-13 | AC-IB-13-01 | 内存日志 handler | log_event | JSON 行含阶段/结果/项目/文档/耗时/计数字段 |
| TC-INT-066 | US-IB-13/14 | AC-IB-13-02/14-01 | degrade sink | emit_degrade ×2 | sink 收到 (reason, stage)，可定位故障依赖 |
| TC-INT-067 | US-IB-13 | AC-IB-13-03 | 内存日志 handler | 运行期改级别 | 立即生效，无需改代码/重建 |
| TC-INT-068 | US-IB-06 | AC-IB-06-05 | 替身向量库 | 端口方法 + 上层链路 | 端口齐备，上传/入库/检索链路不改即可跑通 |
| TC-INT-074 | US-IB-03 | AC-IB-03-02 | kb 级上传 + 项目级 scope 删除（错配路径） | 删除并做**真实文件系统**断言 | **（R4 新增）** `blob_deleted=True`；`FsBlobStore.root` 下该 doc 字节/目录/空 kb 目录**全部不存在**——FND-GROUP-D-03 回归守卫 |
| TC-INT-075 | US-IB-03 | AC-IB-03-02 | 真实 Django HTTP DELETE + 真实 `FsBlobStore` | 上传→HTTP 删除→磁盘核验 | **（R4 新增）** `blob_deleted=True`；存储根下无任何残留文件（复用 R3 探针构造方式，同一条真实 HTTP 路径） |
| TC-INT-076 | US-IB-03 | AC-IB-03-02 | `data=None`（D-08，`content_sha256` 为空） | 删除并观 `blob_deleted` | **（R4 新增）** 本无原文件 → `blob_deleted is False`（**不得恒 True 掩盖**）；删除仍成功 |
| TC-INT-077 | US-IB-03 | AC-IB-03-02 | 跨项目：p_alpha / p_beta 同内容 + 同 doc_id | 删 p_alpha 的 doc | **（R4 新增）** p_beta 的同内容/同 doc_id blob **仍在**（不越界误删） |
| TC-INT-078 | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配 + 项目级 scope，未处理文档 | 上传→HTTP 删除→再跑 worker | **（R4 新增）** 200（无 500）、`vectors_deleted=0`、台账行消失、worker 不再认领（不回归 FND-GROUP-D-02） |
| TC-INT-087 | US-IB-18 | AC-IB-18-02/18-06 | 非法文档（撞词 + 同标签）+ 真实端点 | `admit` 闸门 + `PUT /api/config/definition` | **（R8 新增）** 装配闸门聚合拒绝（`validation_items` 含两新码且条数一致）；端点改 `cn_label`/`keywords` → 400 逐条回执两新码；非法配置不静默生效（`content_hash` 未变）——FND-R7-01 跨模块回归守卫 |

> **R7 集成用例明细**（TC-INT-079~086，8 条）不在本表重复列出，见 **§11.2**（R7 增量清单）；本表 TC-INT-087 为 R8 新增的跨模块接缝用例。

### 3.3 E2E / 关键路径（16）

文件：`tests/e2e/test_user_journeys.py`。关键路径以 Must Have 故事标注（R7 新增 TC-E2E-015/016）。

| TC-ID | 关联 US | 关联 AC | 旅程 | 预期结果 |
|-------|--------|--------|------|---------|
| TC-E2E-001（关键路径） | US-IB-01 + US-IB-08 | AC-IB-01-01/01-05/08-01 | HTTP 上传 → worker 处理 → 检索命中 → SSE 问答 | 201→indexed→命中→content+done |
| TC-E2E-002（关键路径） | US-IB-02 | AC-IB-02-01/02-02 | 依赖故障 → 失败可诊断 → 人工重试 → 恢复 | failed(error_code)→HTTP 重试 200→indexed |
| TC-E2E-003（关键路径） | US-IB-03 | AC-IB-03-02/03-03 | 入库 → 删除 → 再检索 | 删除 200，检索不再命中，台账行消失，**原文件字节亦清理（R4 强化）** |
| TC-E2E-004（关键路径） | US-IB-09 | AC-IB-09-02/09-03 | 复合问题 → 多专家 → 融合 | ≥2 专家，仅一条 content，done 收尾 |
| TC-E2E-005（关键路径） | US-IB-10 | AC-IB-10-01/10-03/10-04 | 注册新工具 → 能力摘要 → 立即绑定 | 摘要含新工具，绑定即用；内置注册表结构合法 |
| TC-E2E-006（关键路径） | US-IB-11 + US-IB-06 | AC-IB-11-01/11-02/06-02 | 两项目配置 → 各自入库 → 交叉检索 | 各见己方语料；乙项目看不到甲项目文档 |
| TC-E2E-007（关键路径） | US-IB-04 + US-IB-05 | AC-IB-04-01/04-03/05-02 | 多格式（md/txt/docx）导入 + 切分参数 | 均可达检索；docx 真实解析入库 |
| TC-E2E-008 | US-IB-13 | AC-IB-13-01/13-02 | 观察运行状态 | /healthz 与 /healthz/deps 反映各依赖 |
| TC-E2E-009（关键路径） | US-IB-14 | AC-IB-14-01 | LLM 依赖故障 → 降级不断流 | degraded 早于 content，仍出 done |
| TC-E2E-010（关键路径） | US-IB-12 | AC-IB-12-03 | 未配置项目 → 启动 | StartupError（fail-fast，不静默起服务） |
| TC-E2E-011 | US-IB-16 | AC-IB-16-01/16-04 | 重建索引旅程 | 202 → 进度 indexed ≥ 1 |
| TC-E2E-012 | US-IB-15 | AC-IB-15-01/15-04 | 离线替身装配 | 替身列齐备，egress.remote=False |
| TC-E2E-013 | US-IB-04 | AC-IB-04-06 | 图片接缝端到端 | 命中 → related_images 路径 → 按 url_path 取图 200 |
| TC-E2E-014（关键路径） | US-IB-07 | AC-IB-07-01/07-02 | embedding 接入端到端 | 维度一致、入库→检索通、冷热自相似≈1、无外发 |
| TC-E2E-015（关键路径，R7 新增） | US-IB-17 | AC-IB-17-01/17-02/17-03/17-04 | 打开配置页 → 编辑白名单字段保存 → 重载以文档为准无漂移 → 改拓扑被拒 → 他处改动后重载以文档为准、陈旧回写 409 | 写回唯一真源、无第二副本、往返无漂移、拓扑不可编辑、不反向覆盖 |
| TC-E2E-016（关键路径，R7 新增） | US-IB-18 | AC-IB-18-01/18-02/18-04/18-06 | 合法即装配且图编译一次常驻 → 非法提交 400 定位条目不静默生效 → 装配闸门聚合拒绝 → 缺失文档显式报错 | 装配期 fail-fast、聚合全部校验项、无强制继续、错误体无凭据值 |

---

## §4 AC → TC 覆盖矩阵（可测性判定）

> 判定口径：`Tested` = 有至少一条**真实执行**的 TC 覆盖；`NOT_TESTABLE` = 本机不可验证（原因见 §5）。
> 可测 AC：**79/79 = 100%**；不可测 AC：11（已登记，不参与通过率）；AC 总数 **90**（1.2.0 / 18 US）。
> R7 新增 12 组 AC（AC-IB-17-01~06、AC-IB-18-01~06）逐条映射见本表末与 §11.2；其中
> AC-IB-17-05 / AC-IB-17-06 为 `Tested（部分）`（服务端/源码级已覆盖，前端**运行期**子句离线不可验，见 §5 附表）。

| AC | 级别 | 覆盖 TC | 判定 |
|----|------|---------|------|
| AC-IB-01-01 | INT/E2E | TC-INT-033, TC-E2E-001 | Tested |
| AC-IB-01-02 | INT | TC-INT-034（服务端 4xx）；前端浏览器侧拦截属前端，未验证 | Tested（服务端部分） |
| AC-IB-01-03 | INT | TC-INT-055 | Tested |
| AC-IB-01-04 | UNIT/INT | TC-UNIT-012, TC-UNIT-012b, TC-INT-034 | Tested |
| AC-IB-01-05 | INT/E2E | TC-INT-003, TC-E2E-001 | Tested |
| AC-IB-01-06 | — | — | NOT_TESTABLE（页面自动刷新为纯前端行为，本轮无前端运行环境） |
| AC-IB-02-01 | UNIT/E2E | TC-UNIT-020, TC-E2E-002 | Tested |
| AC-IB-02-02 | INT/E2E | TC-INT-016, TC-E2E-002 | Tested |
| AC-IB-02-03 | INT | TC-INT-057, TC-INT-058b | Tested |
| AC-IB-02-04 | INT | TC-INT-061, TC-INT-071（R3 回归：处理中删除安全跳过 skipped） | Tested |
| AC-IB-03-01 | INT | TC-INT-033 | Tested |
| AC-IB-03-02 | INT/UNIT/E2E | TC-INT-033, TC-INT-014, TC-INT-041, TC-INT-069, TC-INT-074, TC-INT-075, TC-INT-076, TC-INT-077, TC-INT-078, TC-UNIT-055, TC-E2E-003 | Tested |
| AC-IB-03-03 | E2E/INT | TC-E2E-003, TC-INT-061, TC-INT-070, TC-INT-078 | Tested |
| AC-IB-03-04 | INT | TC-INT-058 | Tested |
| AC-IB-04-01 | E2E/UNIT | TC-E2E-007, TC-UNIT-014 | Tested |
| AC-IB-04-02 | — | — | NOT_TESTABLE（PDF 文本层解析需 pypdf/pdfminer，本机缺失） |
| AC-IB-04-03 | E2E/UNIT | TC-E2E-007, TC-UNIT-014, TC-UNIT-008 | Tested |
| AC-IB-04-04 | INT | TC-INT-056 | Tested |
| AC-IB-04-05 | UNIT | TC-UNIT-013 | Tested |
| AC-IB-04-06 | — | — | NOT_TESTABLE（扫描页 OCR 需 pypdfium2 + rapidocr，本机缺失） |
| AC-IB-04-07 | — | — | NOT_TESTABLE（图片 OCR 引擎缺失；仅降级跳过分支可测） |
| AC-IB-05-01 | UNIT | TC-UNIT-008, TC-UNIT-009, TC-UNIT-010 | Tested |
| AC-IB-05-02 | UNIT/E2E | TC-UNIT-011, TC-E2E-007 | Tested |
| AC-IB-05-03 | UNIT/E2E | TC-UNIT-011, TC-E2E-011 | Tested |
| AC-IB-06-01 | INT | TC-INT-003, TC-INT-054（结构等价于 InMemory；真实 Qdrant 未验证） | Tested（替身） |
| AC-IB-06-02 | INT/E2E | TC-INT-060, TC-INT-004, TC-E2E-006 | Tested |
| AC-IB-06-03 | — | — | NOT_TESTABLE（真实 Qdrant 重启持久化需部署，属 GROUP_E） |
| AC-IB-06-04 | INT | TC-INT-054, TC-INT-014 | Tested |
| AC-IB-06-05 | INT | TC-INT-068 | Tested |
| AC-IB-07-01 | E2E/INT | TC-E2E-014, TC-INT-049（维度一致 + 无云端调用；真实 bge-m3 推理未验证） | Tested（结构） |
| AC-IB-07-02 | UNIT/INT/E2E | TC-UNIT-048, TC-INT-051, TC-E2E-014 | Tested |
| AC-IB-07-03 | INT | TC-INT-062 | Tested |
| AC-IB-07-04 | — | — | NOT_TESTABLE（许可类型为文档性结论，无运行期可断言行为） |
| AC-IB-07-05 | — | — | NOT_TESTABLE（目标机推理延迟需目标机实测） |
| AC-IB-08-01 | INT/E2E | TC-INT-039, TC-E2E-001 | Tested |
| AC-IB-08-02 | INT | TC-INT-007 | Tested |
| AC-IB-08-03 | INT | TC-INT-003, TC-INT-005 | Tested |
| AC-IB-08-04 | — | — | NOT_TESTABLE（千级文档 P95 延迟需目标机实测校准） |
| AC-IB-09-01 | UNIT | TC-UNIT-029 | Tested |
| AC-IB-09-02 | UNIT/E2E | TC-UNIT-030, TC-E2E-004 | Tested |
| AC-IB-09-03 | E2E/INT | TC-E2E-004, TC-INT-042 | Tested |
| AC-IB-09-04 | UNIT | TC-UNIT-031, TC-UNIT-032, TC-UNIT-033 | Tested |
| AC-IB-09-05 | UNIT | TC-UNIT-034 | Tested |
| AC-IB-09-06 | UNIT | TC-UNIT-032 | Tested |
| AC-IB-09-07 | UNIT | TC-UNIT-036 | Tested |
| AC-IB-10-01 | UNIT/E2E | TC-UNIT-037, TC-E2E-005 | Tested |
| AC-IB-10-02 | UNIT | TC-UNIT-037, TC-UNIT-038 | Tested |
| AC-IB-10-03 | UNIT/INT/E2E | TC-UNIT-040, TC-E2E-005, TC-INT-009, TC-INT-073（R3 修复后：摘要非空且与实绑工具一致） | Tested |
| AC-IB-10-04 | UNIT/E2E | TC-UNIT-037, TC-E2E-005 | Tested |
| AC-IB-10-05 | INT | TC-INT-063 | Tested |
| AC-IB-11-01 | E2E/INT | TC-E2E-006, TC-INT-001 | Tested |
| AC-IB-11-02 | INT/E2E | TC-INT-004, TC-INT-054, TC-E2E-006 | Tested |
| AC-IB-11-03 | UNIT | TC-UNIT-004, TC-UNIT-006 | Tested |
| AC-IB-11-04 | UNIT | TC-UNIT-003, TC-UNIT-005 | Tested |
| AC-IB-11-05 | INT | TC-INT-030, TC-INT-032, TC-INT-035 | Tested |
| AC-IB-11-06 | INT | TC-INT-059 | Tested |
| AC-IB-12-01 | — | — | NOT_TESTABLE（systemd 常驻/自启属部署，GROUP_E 冻结） |
| AC-IB-12-02 | UNIT | TC-UNIT-005（secret 仅环境变量注入）；仓库凭据扫描见报告 §6 | Tested |
| AC-IB-12-03 | UNIT/E2E | TC-UNIT-004, TC-UNIT-006, TC-E2E-010 | Tested |
| AC-IB-12-04 | — | — | NOT_TESTABLE（目标机原生依赖真装真跑属部署） |
| AC-IB-12-05 | INT | TC-INT-064, TC-INT-029 | Tested |
| AC-IB-13-01 | INT | TC-INT-065 | Tested |
| AC-IB-13-02 | INT | TC-INT-066, TC-INT-005, TC-INT-006 | Tested |
| AC-IB-13-03 | INT | TC-INT-067 | Tested |
| AC-IB-13-04 | UNIT | TC-UNIT-020, TC-UNIT-021 | Tested |
| AC-IB-14-01 | INT/E2E | TC-INT-005, TC-E2E-009 | Tested |
| AC-IB-14-02 | INT | TC-INT-007 | Tested |
| AC-IB-14-03 | INT | TC-INT-006 | Tested |
| AC-IB-14-04 | — | — | NOT_TESTABLE（单图 OCR 失败分支需 OCR 引擎，本机缺失） |
| AC-IB-14-05 | INT/E2E | TC-E2E-012, TC-INT-005, TC-INT-006 | Tested |
| AC-IB-15-01 | E2E | TC-E2E-012, TC-E2E-009 | Tested |
| AC-IB-15-02 | UNIT | TC-UNIT-001 ~ TC-UNIT-042 | Tested |
| AC-IB-15-03 | UNIT | TC-UNIT-027 | Tested |
| AC-IB-15-04 | INT/E2E | TC-INT-003, TC-E2E-001 | Tested |
| AC-IB-16-01 | E2E/INT | TC-E2E-011, TC-INT-054 | Tested |
| AC-IB-16-02 | INT/E2E | TC-E2E-011, TC-INT-016 | Tested |
| AC-IB-16-03 | INT | TC-INT-054 | Tested |
| AC-IB-16-04 | INT/E2E | TC-INT-015, TC-E2E-011 | Tested |
| AC-IB-17-01 | INT/E2E | TC-INT-079, TC-INT-081, TC-INT-084, TC-E2E-015 | Tested |
| AC-IB-17-02 | UNIT/INT/E2E | TC-UNIT-058, TC-INT-080, TC-E2E-015 | Tested |
| AC-IB-17-03 | INT/E2E | TC-INT-081, TC-INT-084, TC-INT-086, TC-E2E-015 | Tested |
| AC-IB-17-04 | UNIT/INT | TC-UNIT-059, TC-INT-084, TC-INT-086, TC-E2E-015 | Tested |
| AC-IB-17-05 | UNIT/INT | TC-UNIT-060, TC-INT-084, TC-INT-086 | Tested（部分）——定义层/端点/源码级已覆盖；前端**渲染期**不回显子句属前端运行期，离线不可验（§5 附表） |
| AC-IB-17-06 | INT | TC-INT-086 | Tested（部分）——「数据不出本机 + 本地打包无 CDN」已覆盖；「**禁 Docker / 全物理机裸装**运行形态」属部署，本轮冻结（§5 附表） |
| AC-IB-18-01 | UNIT/INT/E2E | TC-UNIT-061, TC-INT-085, TC-E2E-016 | Tested |
| AC-IB-18-02 | UNIT/INT/E2E | TC-UNIT-057, TC-UNIT-062~066, TC-INT-082, TC-INT-087, TC-E2E-016 | **Tested（完整，R8 起）**——全部非法项（含「路由关键词撞车」`expert_keyword_collision` 与「cn_label 重复」`expert_cn_label_duplicate`）均被拒并定位；FND-R7-01 已修复 → CLOSED_VERIFIED（报告 §13.8） |
| AC-IB-18-03 | UNIT/E2E | TC-UNIT-057, TC-UNIT-061, TC-E2E-016 | Tested |
| AC-IB-18-04 | UNIT/INT | TC-UNIT-060, TC-INT-082, TC-INT-084, TC-E2E-016 | Tested |
| AC-IB-18-05 | UNIT | TC-UNIT-056 | Tested |
| AC-IB-18-06 | INT/E2E | TC-INT-082, TC-INT-083, TC-E2E-016 | Tested |

---

## §5 不可测试项（NOT_TESTABLE）

| AC-ID | 原因 | 影响 / 去向 |
|-------|------|------------|
| AC-IB-01-06 | 页面按周期自动刷新为纯前端行为，本轮无前端运行环境 | 前端构建/交互验证登记为 not-verified（报告 §6） |
| AC-IB-04-02 | PDF 文本层解析依赖 `pypdf`/`pdfminer.six`，本机均未安装 | 报告 §6 not-verified；PDF 相关代码覆盖率低（`pdf_parser.py` 12%） |
| AC-IB-04-06 | 扫描页整页渲染 OCR 依赖 `pypdfium2` + `rapidocr_onnxruntime`，本机缺失 | 同上 |
| AC-IB-04-07 | 图片 OCR 引擎缺失；仅「不可用时跳过 + WARNING」分支可测 | 同上 |
| AC-IB-06-03 | 真实 Qdrant 重启持久化需部署实例，属 GROUP_E | 报告 §6 not-verified |
| AC-IB-07-04 | 许可类型为文档性结论，无运行期可断言行为 | 由 `docs/tech_stack.md` §2 台账承载 |
| AC-IB-07-05 | 目标机 CPU 推理延迟需目标机以目标语料实测 | 报告 §6 not-verified；本机数据不可替代 |
| AC-IB-08-04 | 千级文档 P95 延迟需目标机实测校准 | 同上 |
| AC-IB-12-01 | systemd 常驻/开机自启属部署，GROUP_E 本轮冻结 | 报告 §6 not-verified；**不得触碰** |
| AC-IB-12-04 | 目标机原生依赖真装真跑属部署 | 同上 |
| AC-IB-14-04 | 单图 OCR 失败分支需 OCR 引擎，本机缺失 | 报告 §6 not-verified |

**合计**：**90** AC 中 11 项标注 NOT_TESTABLE（12.2%），其余 **79** 项均有用例覆盖
（其中 AC-IB-17-05 / AC-IB-17-06 为 `Tested（部分）`；**AC-IB-18-02 自 R8 起为 `Tested`（完整）**）。

### 5.1 R7 部分不可验证子句（**仍计入 79/79，不改变 NOT_TESTABLE 计数**；诚实标注）

| AC-ID | 已覆盖部分 | **不可验证**子句 | 理由 / 去向 |
|-------|-----------|----------------|------------|
| AC-IB-17-05 | 定义层「只出现键名不含凭据值」（TC-UNIT-060）、端点响应不含凭据值（TC-INT-084）、源码「只展示 `config_key_names`」（TC-INT-086） | 界面**渲染期**不回显、前端产物中不暴露凭据值 | 需前端运行期（浏览器挂载/交互），无自动化浏览器环境 → 报告 §6 NV-09 / §15.6 NV-R7-01 |
| AC-IB-17-06 | 「数据不出本机 + 依赖本地打包、运行期无 CDN」（TC-INT-086 源码级 + 定义层无网络调用） | 「可在**禁 Docker、全物理机直部署、组件裸装**形态下运行」 | 属部署形态，GROUP_E 本轮冻结（同 AC-IB-12-01/04 口径） |
| AC-IB-18-02 | 全部非法项均被拒并定位；无强制继续通道（TC-UNIT-057 / TC-UNIT-062~066 / TC-INT-082 / TC-INT-087 / TC-E2E-016） | **（R8 起无不可验证子句）** | 原第 7 类「路由关键词撞车」及第 8 类「`cn_label` 重复」已由 GROUP_C R8 补齐、经本轮回归 **CLOSED_VERIFIED**（报告 §13.8）→ 本行由 `Tested（部分）` 转 **`Tested`（完整）** |

---

## §6 门控与度量定义

| 度量 | 公式 | 门控 |
|------|------|------|
| 通过率 | `pass / (pass + fail) × 100%`（skip 与 blocked 不计入分母） | 单元 ≥ 80%；集成 ≥ 90% |
| 算术自洽 | `total = pass + fail + skip + blocked`（精确等式，无四舍五入） | 必须成立 |
| AC 覆盖率 | `已覆盖可测 AC / 可测 AC 总数` | 100% |
| 关键路径覆盖率 | `有 E2E 用例的 Must Have US / Must Have US 总数` | 100% |
| 计数方法 | pytest 原始输出（`docs/evidence/*.log`）逐条对应 TC-ID | 可追溯 |

---

## §7 已知环境偏差

| ID | 偏差 | 处置 |
|----|------|------|
| DEV-01 | 开发机 Python **3.14.6**，而 `docs/tech_stack.md` 约束为 `>=3.11,<3.14`（承 R1 偏差 D-03） | 登记；全部用例在 3.14.6 上真实跑通，但**不得**据此断言生产（3.11~3.13）行为等价 |
| DEV-02 | 本机 `langchain-openai` 1.3.3，违反 R1 冻结 pin `>=0.2,<0.3` | 远程 LLM 装配路径（`openai_compatible`）在本机被版本守卫拦下；`describe_egress` 于类级验证（TC-INT-064） |
| DEV-03 | `pypdf`/`pdfminer`/`pdfplumber`/`pypdfium2`/`rapidocr`/`FlagEmbedding`/`qdrant_client` 未安装（仅 `docx`、`onnxruntime` 可用） | 直接导致 §5 的 PDF/OCR/Qdrant not-verified 项 |
| **FLAKE-IB-01** | Windows 回环真 HTTP 偶发 `ConnectionAbortedError: [WinError 10053]`（`tests/integration/test_ib_embed_wire.py`，命中 **TC-INT-025** / **TC-INT-026** 的 `/warmup` 用例） | **MINOR（测试环境偶发，非产品缺陷）**。R8 实测：全量集成 14 次 / 4 次、单文件 8 次 / 1 次命中；每次命中后重跑即通过。登记保持 **OPEN**（**不**据「未复现」声称已修复）；缓解建议（测试侧连接级有界重试，**不放松断言**）见报告 §13.9，本轮**未实施**。<br>**R9 更新（INV-GROUP_D-INTELBASE-006）**：测试侧缓解建议**已实施**——`test_ib_embed_wire.py` 传输助手对 `ConnectionAbortedError`/`ConnectionResetError` 做**有限有界重试**（≤3 次尝试 + 0.05s 退避，**仅**连接级瞬态，**绝不**吞断言）；机制经探针确证（报告 §14.3），复跑单文件 10/10 绿、集成层 8/8 绿。状态 **OPEN → MITIGATED**（**不声称 CLOSED**，见报告 §14.5）。详细见 §13 |

---

## §8 与实施计划/模块设计的对照

- 模块覆盖：`implementation_plan.md` 声明 26 模块（MOD-IB-01~26）。本轮测试触达 MOD-IB-01~26 中除「纯部署 unit」（MOD-IB-25 systemd）外的全部；MOD-IB-26（`ib_embed`）以真实回环 HTTP 覆盖。**R7 增量**触达 MOD-IB-02（定义文档数据层）、MOD-IB-23（装配闸门 / 端点 / 组合根注入）、MOD-IB-24（可视化配置页，源码级）。
- 契约纪律：IC-IB-01（无裸 axios / 令牌不进 URL）→ TC-INT-031/038；C8（`ib_embed` 零耦合）→ TC-INT-050；`related_images`（IFC-IB-282）→ TC-UNIT-019 + TC-INT-044/046/047/048；**R7** IFC-IB-288~292（定义层）→ TC-UNIT-056~061 + TC-INT-079~081/083；IFC-IB-293（装配闸门）→ TC-INT-082；IFC-IB-294/295（端点）→ TC-INT-084；IFC-IB-296（视图侧纪律）→ TC-INT-086。
- 偏差登记：FND-GROUP-D-01（能力摘要恒空）、FND-GROUP-D-02（未绑库删除 500 + 幽灵文档）、D-R2-02（生产相关图恒空，登记行为）详见报告 §5；**R7 新发现 FND-R7-01（定义文档校验器未覆盖 ADR-16/REQ-FUNC-IB-27 ① 列举的两类校验项）详见报告 §12.6**。

---

## §9 R3 增量（缺陷回归与门控；追加，不改写 §1~§8）

> 触发：software-developer 完成 `INV-GROUP_C-INTELBASE-003`（R3 修复 FND-GROUP-D-02 / FND-GROUP-D-01）。
> 本轮为 **GROUP_D 增量**（`INV-GROUP_D-INTELBASE-002`）：翻转「缺陷固化用例」为正向守卫、补 R3 定向回归、
> 补一条**真并发**用例、重跑并执行串行通过率门控。**未修改任何 `src/**` 实现代码**。

### 9.1 三个「缺陷固化用例」→ 正向回归守卫（翻转）

| 原用例（固化缺陷） | 新用例（正向守卫） | 文件 | 断言要点 |
|---|---|---|---|
| `test_TC_INT_009_capability_digest_registry_gap_is_registered` | `test_TC_INT_009_capability_digest_reflects_builtin_tools` | `test_composition_retrieval.py` | `deps.capability_digest` 非空且含 `search_knowledge`；`IntentRouter._capability_digest()` ≠「（无可用工具）」且含 `search_knowledge` |
| `test_TC_INT_041_delete_before_bind_is_500` | `test_TC_INT_041_delete_before_bind_succeeds` | `test_http_contract.py` | DELETE → 200；`ledger_deleted=True`、`vectors_deleted=0`；列表消失；再删 404 |
| `test_TC_INT_061_ghost_document_after_failed_delete_is_registered` | `test_TC_INT_061_delete_before_processing_leaves_no_ghost` | `test_ops_contract.py` | 删不抛；`ledger_deleted=True`；台账行 `None`；worker 不认领（`processed=0`）；检索 `[]`；向量 0；对账干净 |

守卫串 `偏差已消除——请更新缺陷登记` / `DID NOT RAISE` **已随翻转移除**；若两缺陷复发，上述三用例将**响亮失败**。

### 9.2 新增回归用例（R3 行为定向）

| TC-ID | 文件 | 关联 AC | 覆盖的 R3 行为 |
|-------|------|---------|---------------|
| TC-INT-069 | `test_ops_contract.py` | AC-IB-03-02 | 已索引文档删除的 `DeleteReport` 三计数；删除路径**两次**向量清扫（首次清全部、竞态清扫为 0）；列表/台账/切块/向量/对账五不变式 |
| TC-INT-070 | `test_ops_contract.py` | AC-IB-03-03 | 删除后不可检索；再次 `process_pending` **不复活**（可见性权威 = 台账） |
| TC-INT-071 | `test_ops_contract.py` | AC-IB-02-04 | **真并发（2 线程）**：worker 处理中被删 → 计为 `skipped`（非 failed）、无未捕获异常、无残留向量 |
| TC-INT-073 | `test_composition_retrieval.py` | AC-IB-10-03 | 防漂移不变式：`bind_tools` 绑定工具名集合 == 摘要工具名集合，跨项目一致 |

**覆盖缺口说明（不凑数）**：三条 AC 在 §4 已有映射（AC-IB-03-02 ← TC-INT-033/014/E2E-003；AC-IB-03-03 ← TC-E2E-003/TC-INT-061；AC-IB-02-04 ← TC-INT-061）。新增用例填补的是**R3 修复行为**的缺口 —— 三计数与「第二次清扫为 0」、删除后重跑不复活、并发删除的 `skipped` 分类 —— 这些在修复前不存在可断言的正确行为，故非重复。
**AC 归属订正（诚实标注）**：任务书把「无可用工具/能力摘要路由提示可见性」记于 AC-IB-02-04；按 `user_stories.md` 原文，该可见性属 **AC-IB-10-03**，AC-IB-02-04 实为「处理中删除安全退出」。本轮**两条都已覆盖**（TC-INT-073 / TC-INT-071），避免因编号错配漏测。

### 9.3 真并发/竞态用例（对应 developer 登记的 R3-RISK-01）

TC-INT-071 用**真线程**（`threading.Thread`）跑 `process_pending`，并用**依赖替身（embedder）上的事件闸门**把交错窗口固定：

- worker 进入 `embed_documents` 即阻塞 → 主线程此刻执行 `delete_document`（此时 worker 确在「处理中」）→ 放行 worker；
- worker 走完剩余步骤撞上「台账行已不存在」→ 依 R3 的 `_DeletedConcurrently` / `NotFoundError` 分类分支计为 `skipped`，并 `_discard_written_vectors` 清掉本次写入的向量。

**诚实边界**：闸门落在**依赖替身**上（未改 SUT 逻辑），故交错可复现；本轮**未做**多进程/多 worker 压测，未构造「进程级崩溃落在两次清扫之间」的更窄时序 —— 该窗口仍由 `list_orphan_doc_ids` 对账 + 删除幂等兜底（developer 的确定性探针 `groupc_r3_probe.py` 用例 (c) 覆盖其因果链）。R3-RISK-01 的「真多进程压测」仍留待目标机阶段。

### 9.4 门控与覆盖复核

- 门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、算术自洽、可测 AC 100%、关键路径 100%）；执行结果见 `docs/test_report.md` §10。
- 用例总数 138 → **142**（集成 69 → 73）；`--collect-only` 计数与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r3_collect.log`）。
- §4 覆盖矩阵已同步更新 AC-IB-02-04 / AC-IB-03-02 / AC-IB-03-03 / AC-IB-10-03 四行。

### 9.5 本轮新发现缺陷（登记，不改实现）

| ID | 现象 | 级别 | 复现 | 处置 |
|----|------|------|------|------|
| FND-GROUP-D-03 | 生产 HTTP 删除路径（`resolve_scope` → 项目级 `Scope(kb_ids=None)`）下，原文件字节**未被删除**：`DeleteReport.blob_deleted` 恒为 `False`，BlobStore 中的原文件成为**孤儿**（磁盘/内存残留已删文档的原始内容） | MAJOR（保留/隐私 + 磁盘泄漏；非崩溃、不影响检索正确性） | `PYTHONUTF8=1 IB_OFFLINE_MODE=1 python docs/evidence/groupd_r3_blob_probe.py`（`docs/evidence/groupd_r3_blob_probe.log`） | 路由 software_developer：删除时按**文档所属 kb** 构造删除 scope（或 BlobStore 删除改为按 `project_id + doc_id` 匹配）。**测试侧未改实现** |
| FLAKE-IB-01 | `tests/integration/test_ib_embed_wire.py` 回环真 HTTP 用例**偶发** `ConnectionAbortedError: [WinError 10053]`（本会话 9 次集成层运行中出现 2 次，命中 `TC-INT-027` / `TC-INT-025` 各一次；单文件单独运行 3/3 通过；随后全量套件 5/5 连续通过） | MINOR（测试环境偶发，非产品缺陷；**与 R3 无关**） | 反复运行 `python -m pytest tests/integration -q` 观测 | 属 Windows 回环 socket 偶发；登记为环境偏差，不计入门控失败；如需根治可在测试侧对**连接级**错误做有限重试（不放松任何断言） |

---

## §10 R4 增量（FND-GROUP-D-03 回归与门控；追加，不改写 §1~§9）

> 触发：software-developer 完成 `INV-GROUP_C-INTELBASE-004`（R4 修复 FND-GROUP-D-03）。
> 本轮为 **GROUP_D R4 增量**（`INV-GROUP_D-INTELBASE-003`）：为已修缺陷补**真实、突变敏感**的回归用例，
> 重跑全量套件并执行串行通过率门控。**未修改任何 `src/**` 实现代码**（见 `docs/test_report.md` §11.9）。

### 10.1 被测修复（供用例溯源）

| 修复点 | 文件 | 语义 |
|--------|------|------|
| `kb_segment(kb_id)` | `src/ib/blob/__init__.py` | kb 存储段名的**唯一真源**：空串 / `None` → `"default"`；写（`FsBlobStore._doc_dir`/`InMemoryBlobStore`）、读（`blob_ref_for`）、删三处收敛为同一函数 |
| `_blob_scope_of(record)` | `src/ib/lifecycle/__init__.py` | `delete_document` 第 2 步改由**台账记录**派生删除 scope（携带真实 kb），不再沿用调用方传入的项目级 scope |

缺陷原状（`groupd_r3_blob_probe.py` 复现）：HTTP 删除经 `resolve_scope` 得项目级 `Scope(kb_ids=None)` →
`"default"` 段查找 → 删 0 个 → 原文件成孤儿且 `blob_deleted` 恒 `False`。

### 10.2 新增用例清单（TC ↔ AC）

| TC-ID | 文件 | 关联 US | 关联 AC | 覆盖的 R4 行为 |
|-------|------|--------|--------|---------------|
| TC-UNIT-055 | `tests/unit/test_blob_kb_segment.py` | US-IB-03 | AC-IB-03-02 | `kb_segment` 规则唯一（`None`/`""` → `"default"`）；写/读/删三路径落到同一 kb 段（单一真源不变式） |
| TC-INT-074 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | kb 级上传 + 项目级 scope 删除（错配路径）：`blob_deleted=True` 且**真实文件系统**上无残留字节/目录 |
| TC-INT-075 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 真实 Django HTTP `DELETE` + 真实 `FsBlobStore`：磁盘无任何残留文件 |
| TC-INT-076 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | `data=None`（D-08）本无 blob → `blob_deleted is False`（不得恒 True 掩盖） |
| TC-INT-077 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02 | 跨项目不误删（同内容 + 同 doc_id 两种构造） |
| TC-INT-078 | `tests/integration/test_blob_delete_scope_r4.py` | US-IB-03 | AC-IB-03-02/03-03 | fresh 装配 + 项目级 scope 删除未处理文档仍 200、不回归 FND-GROUP-D-02、无 pending 幽灵 |

### 10.3 既有守卫的 R4 强化

| 用例 | 文件 | 强化点 |
|------|------|--------|
| TC-INT-041 | `test_http_contract.py` | 由「`blob_deleted` 为布尔（按实）」强化为「`blob_deleted is True` 且原文件引用失效」——同一守卫现同时覆盖 FND-GROUP-D-02 与 FND-GROUP-D-03 |
| TC-E2E-003（关键路径） | `test_user_journeys.py` | 旅程末尾新增「原文件字节已清理」断言（`blob_deleted is True` 且 `blobs.exists(ref) is False`） |

### 10.4 突变敏感性自证（新用例如何抓住回退）

在**仓库副本**（`.r4_mutant_check/`，测试后已删除；真实 `src/` 全程只读）上施加两处回退：

| 突变 | 施加方式 | 结果 | 证据 |
|------|---------|------|------|
| A：`_blob_scope_of` 回退为项目级（旧写法） | `return Scope(project_id=record.project_id)` | **6 failed / 2 passed**：TC-UNIT-055、TC-INT-074、TC-INT-075、TC-INT-077、TC-INT-041、TC-E2E-003 失败 | `docs/evidence/groupd_r4_mutation.log` |
| B：`kb_segment` 回退为恒等（丢失 default 规则） | `return kb_id` | **1 failed / 5 passed**：TC-UNIT-055 失败 | 同上 |

- 突变 A 下仍通过的 2 条 = TC-INT-076（本无 blob → 仍为 False，符合预期语义）与 TC-INT-078（FND-GROUP-D-02 守卫，与被突变点无关）。
- 突变 B 只命中 TC-UNIT-055：集成用例均用 kb 级上传（`kb_segment("kb_a") == "kb_a"` 不受影响），故 `kb_segment` 规则敏感度由单元级 TC-UNIT-055 承载；`_blob_scope_of` 敏感度由 TC-INT-074/075/077 承载。二者合起来覆盖任务书要求的「两处回退都会失败」。

### 10.5 门控与覆盖复核

- 门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、算术自洽、可测 AC 100%、关键路径 100%）；执行结果见 `docs/test_report.md` §11。
- 用例总数 142 → **148**（单元 55 → 56、集成 73 → 78、E2E 14 不变）；`--collect-only` 计数与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r4_collect.log`）。
- §4 覆盖矩阵 AC-IB-03-02 / AC-IB-03-03 两行已同步更新。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未使用 `-k`/`--deselect`/`--ignore`。

---

## §11 R7 增量（US-IB-17 / US-IB-18「UI 可视化配置」纳入测试范围；追加，不改写 §9~§10）

> 触发：REV-07-4（源自协调者裁决第 3 项）—— GROUP_B R7（1.3.0，ADR-14/15/16、IFC-IB-287~297）与
> GROUP_C R7（`implementation_plan.md` 2.3.0/R7，§15）已把 REQ-FUNC-IB-25/26/27 落地为代码，
> 现将其对应的 **US-IB-17 / US-IB-18**（均 Must Have）纳入 GROUP_D 测试范围。
> 本轮为 **GROUP_D R7 增量**（`INV-GROUP_D-INTELBASE-004`）：补覆盖矩阵、实现并执行新增用例、
> 重跑串行通过率门控。**未修改任何 `src/**` 实现代码**（见报告 §12.8）。

### 11.1 施工顺序前置（US-IB-17/18 的落地前提）

US-IB-17 / US-IB-18 的落地**前置**是「专家 / 路由 / 编排 / 工具授权已**外置为数据**且为**单一真源**」
（REQ-FUNC-IB-01 / REQ-FUNC-IB-02 的实现落差，见 `docs/agent_platform_research.md` §3.3 P0）。
该落差已由 **`DefinitionDocumentStore` 端口（IFC-IB-287，第 14 端口）+ `src/ib/config/definition.py`**
（IFC-IB-288~292）闭合：可视化只写回定义文档，不存在第二真源；否则可视化会沦为第二真源（风险 R-1）。

**测试口径**：本轮为「定义外置」这一前置直接建立断言 —— 单一真源/原子写回（TC-INT-079）、
往返无漂移（TC-INT-080）、乐观并发拒绝静默覆盖（TC-INT-081）、装配期装载→准入→派生→注入（TC-INT-085）。
即：只有前置成立，US-IB-17 的「无第二副本」与 US-IB-18 的「装配期拒绝」才可被断言。

### 11.2 新增用例清单（TC ↔ US ↔ AC）

共新增 **16** 条（单元 6 / 集成 8 / E2E 2）。全部为**正向断言**；0 skip / 0 xfail / 无 monkeypatch 掩盖。

| TC-ID | 文件 :: 用例名 | US | AC | 断言要点 |
|-------|---------------|----|----|---------|
| TC-UNIT-056 | `tests/unit/test_definition_data_layer_r7.py::test_TC_UNIT_056_validate_is_framework_free_and_pure` | US-IB-18 | AC-IB-18-05 | 干净解释器 import 定义层且 `sys.modules` 无 django/DRF/langchain/langgraph；`validate`/`derive`/`semantic_hash` 纯函数（同输入同输出） |
| TC-UNIT-057 | `::test_TC_UNIT_057_each_illegal_category_is_rejected_with_locator` | US-IB-18 | AC-IB-18-02、18-03 | 12 类非法样例逐类被拒且产出预期 code + 非空 `path/code/message`；边界取值 0.0/1.0 通过 |
| TC-UNIT-058 | `::test_TC_UNIT_058_roundtrip_is_semantically_equivalent` | US-IB-17 | AC-IB-17-02 | 文档→JSON→文档语义等价、逐项无增删改、往返幂等、哈希与 `updated_at` 无关 |
| TC-UNIT-059 | `::test_TC_UNIT_059_whitelist_excludes_topology_and_non_editable_changes_detects_it` | US-IB-17 | AC-IB-17-04 | 白名单含「专家集合 + 节点参数」、不含拓扑/归属；拓扑变更检出 `field_not_editable`；白名单内变更不报 |
| TC-UNIT-060 | `::test_TC_UNIT_060_errors_carry_locators_without_credential_values` | US-IB-18 | AC-IB-18-04、18-02 | `ValidationReport` 字段恰 `{ok,errors}`（无 force/ignore/warn_only）；错误项恰 `{path,code,message}`；校验结果与环境凭据值无关、错误体无凭据值 |
| TC-UNIT-061 | `::test_TC_UNIT_061_valid_passes_and_default_expert_invariant_is_not_bypassable` | US-IB-18 | AC-IB-18-01、18-03 | 合法即通过并派生视图；默认专家 0 个/≥2 个一律拒；`validate`/`admit` 签名无强制继续参数 |
| TC-INT-079 | `tests/integration/test_definition_config_r7.py::test_TC_INT_079_definition_store_is_single_persistent_source` | US-IB-17 | AC-IB-17-01 | 写回后目录**恰一份**文件（无临时残留/无第二副本）；文件内容 == `document_to_json`；重载逐字一致 |
| TC-INT-080 | `::test_TC_INT_080_store_roundtrip_has_no_semantic_drift` | US-IB-17 | AC-IB-17-02 | 写入→重载→原样回写，语义哈希不变、逐项无增删改 |
| TC-INT-081 | `::test_TC_INT_081_document_is_authoritative_and_conflicts_are_rejected` | US-IB-17 | AC-IB-17-03、17-01 | 界面外改动以文档为准；陈旧基线回写 → `conflict=True` 且**不落盘**（含 `content_hash_conflict` 可读回执）；当前基线回写成功 |
| TC-INT-082 | `::test_TC_INT_082_admit_gate_rejects_aggregating_all_items` | US-IB-18 | AC-IB-18-06、18-02 | `admit` 拒绝装配 + **聚合全部**校验项（`validation_items` 条数与 code 集合与 `validate` 一致）；合法定义通过且派生确定性 |
| TC-INT-083 | `::test_TC_INT_083_missing_or_corrupt_document_never_silently_falls_back` | US-IB-18 | AC-IB-18-06、17-01 | 文件缺失/损坏/非对象 JSON、内存未登记项目/`missing` 标志 → 一律 `ConfigError`（不静默回退空文档） |
| TC-INT-084 | `::test_TC_INT_084_definition_endpoint_contract_matrix` | US-IB-17/18 | AC-IB-17-01/04/05、18-01/04 | `GET|PUT /api/config/definition` 状态码矩阵 200/400/401/403/405/409；写回后 GET 以文档为准且 `deps.definitions` 同步；响应不含凭据值、只登记键名 |
| TC-INT-085 | `::test_TC_INT_085_assembly_loads_admits_derives_and_injects` | US-IB-18 | AC-IB-18-01 | 装配装载两项目文档（对象不共享）、派生注册表 == 文档专家集、图配置取自文档、编排图**编译一次常驻**（同项目同一对象） |
| TC-INT-086 | `::test_TC_INT_086_view_side_discipline_is_source_level_only` | US-IB-17 | AC-IB-17-04/05/06 | 源码级：本地打包无 CDN、视图侧零持久化、拓扑只读（无增删节点/边入口）、仅展示键名、无 `v-html`；**分发纪律（R10 修复）**：断言 `src/frontend/node_modules/**` **未被 git 跟踪**（`git ls-files`，环境自适应、与磁盘是否已装依赖无关）——守护「前端依赖不随仓库分发」不变量 |
| TC-E2E-015（关键路径） | `tests/e2e/test_user_journeys.py::test_TC_E2E_015_visual_config_roundtrip_is_single_source` | US-IB-17 | AC-IB-17-01/02/03/04 | 完整旅程：读 → 编辑保存 → 重载无漂移 → 改拓扑被拒 → 他处改动后以文档为准、陈旧回写 409 且不覆盖 |
| TC-E2E-016（关键路径） | `::test_TC_E2E_016_invalid_config_refused_at_assembly` | US-IB-18 | AC-IB-18-01/02/04/06 | 完整旅程：合法即装配且图常驻 → 非法提交 400 定位且不静默生效 → 装配闸门聚合拒绝 → 缺失文档显式报错 → 错误体无凭据值 |

**覆盖缺口判定（不凑数）**：12 组 AC 此前在 §4 中**无任何映射**（US-IB-17/18 属 REV-06 新增诉求），
故新增 16 条均为**首次覆盖**而非重复。TC-UNIT-058 与 TC-INT-080 分属「纯函数往返」与「经存储往返」
两个不同语义面（后者含原子写回与乐观并发基线），非重复。

### 11.3 覆盖与计数复核

- 用例总数：**149 → 165**（单元 56 → 62、集成 79 → 87、E2E 14 → 16）。
  `--collect-only` 与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r7_collect.log`）。
- 全部 US：**18 / 18** 均有用户故事级（E2E）覆盖（新增 US-IB-17 → TC-E2E-015、US-IB-18 → TC-E2E-016）。
- 关键路径：**14 / 14** Must Have US = 100%（US-IB-17/18 均 Must Have）。
- 可测 AC：**79 / 79** = 100%（11 项 NOT_TESTABLE 见 §5；3 项 `Tested（部分）` 见 §5.1）。
- §4 覆盖矩阵已同步新增 AC-IB-17-01~06 / AC-IB-18-01~06 共 12 行。

### 11.4 门控与度量

门控定义沿用 §6（单元 ≥ 80%、集成 ≥ 90%、E2E 关键路径 100%、算术自洽、可测 AC 100%）；
执行结果（命令 + EXIT + 原始计数）见 `docs/test_report.md` **§12**。

---

## §12 R8 增量（FND-R7-01 修复回归：装配期唯一性校验；追加，不改写 §9~§11）

> 触发：REV-08-2（协调者裁决 A）—— GROUP_C R8（software-developer `INV-GROUP_C-INTELBASE-007`）在
> `src/ib/config/definition.py::validate()` **纯追加**两项装配期校验（跨专家关键词撞车 `expert_keyword_collision` /
> `cn_label` 唯一性 `expert_cn_label_duplicate`），即 **FND-R7-01（报告 §12.6，MAJOR）** 的修复。
> 本轮为 **GROUP_D R8 增量**（`INV-GROUP_D-INTELBASE-005`）：修复陈旧夹具、补测新校验、重跑串行门控、补全 FLAKE-IB-01 登记。
> **未修改任何 `src/**` 实现代码**（见报告 §13.11）。

### 12.1 被测修复（供用例溯源）

| 项 | 契约/来源 | 语义 |
|----|----------|------|
| 校验项 10 | ADR-16 / AC-IB-18-02 / REQ-FUNC-IB-27 ① | 跨专家**路由关键词撞车**：归一化 `strip().lower()`（对齐 `ib/routing/intent.py::_keyword_hits`），不同专家归一后同词 → `expert_keyword_collision`，`path=experts[<专家>].keywords[<原样词>]` |
| 校验项 11 | ADR-16 / AC-IB-18-02 | `cn_label` **唯一性**：去首尾空白后比较（界面不可见空白视为重复，大小写可见不归一）；重复 → `expert_cn_label_duplicate`，`path=experts[<专家>].cn_label`；空标签由既有第 5 项 `expert_text_missing` 承担 |
| 纯追加纪律 | 实现注释 L362~411 | 既有 1~9 类校验语义与顺序**一字未改**，新增项仅末尾追加 |

### 12.2 陈旧夹具修复（D-R8-01，仅改夹具数据、断言语义不变）

`tests/unit/test_definition_data_layer_r7.py` 与 `tests/integration/test_definition_config_r7.py` 的 `_expert` 夹具
原让两位专家**共用** `cn_label="标签"` / `keywords=("k",)`（修复前「仅因缺陷而合法」）；新增校验后该基线被判非法 →
**TC-UNIT-056/057/061、TC-INT-082** 四个**正向**「基线合法」用例转为失败。**判定：夹具陈旧，非真实回归。**
修法：`_expert` 默认值改为**随 name 派生**（`cn_label=f"标签{name}"`、`keywords=(f"k{name}",)`）；**未删除/削弱任何断言**。
（若修复时发现某失败实为真实回归，须立即 BLOCKED —— 本轮经逐条核验**无**此类情形。）

### 12.3 新增/补测用例清单（TC ↔ US ↔ AC）

| TC-ID | 文件 | US | AC | 断言要点 |
|-------|------|----|----|---------|
| TC-UNIT-062（R8 登记） | `tests/unit/test_definition_uniqueness_r8.py` | US-IB-18 | AC-IB-18-02 | 关键词撞车：通过 + 精确/大小写/空白重复 → 拒绝并定位；同专家内重复不报 |
| TC-UNIT-063（R8 登记） | 同上 | US-IB-18 | AC-IB-18-02 | `cn_label` 唯一：通过 + 精确/空白重复 → 拒绝（`path=experts[b].cn_label`）；空跳过；大小写不归一 |
| TC-UNIT-064（R8 登记） | 同上 | US-IB-18 | AC-IB-18-02 | 默认注册表无撞车/无重标签；默认派生文档 `validate.ok is True`（反向护栏） |
| TC-UNIT-065（R8 新增） | `tests/unit/test_definition_uniqueness_extra_r8.py` | US-IB-18 | AC-IB-18-02 | 空/纯空白关键词不误报；三名专家同词 → 2 条且 path 归属；大小写+空白叠加；精确 path |
| TC-UNIT-066（R8 新增） | 同上 | US-IB-18 | AC-IB-18-02 | 三名专家同标签 → 2 条且 path 归属；全空白跳过；两项校验独立（两错误码并存） |
| TC-INT-087（R8 新增） | `tests/integration/test_definition_config_r7.py` | US-IB-18 | AC-IB-18-02/18-06 | 跨模块接缝：`admit` 聚合拒绝（含两新码）；`PUT /api/config/definition` → 400 逐条回执两新码；非法配置不静默生效 |

**覆盖缺口判定（不凑数）**：TC-UNIT-062~064 已覆盖主路径（此前未入册，本轮**首次登记**）；本轮只补其空缺
（空关键词跳过 / 三名专家条数与归属 / 两项校验独立性）与**跨模块接缝**（`admit` + 端点），非重复。

### 12.4 覆盖与计数复核

- 用例总数：**165 → 171**（单元 62 → **67**、集成 87 → **88**、E2E 16 不变）；净增 6 = developer 交付 3 + 本代理新增 3。
  `--collect-only` 与各目录 `def test_` 静态计数交叉一致（`docs/evidence/groupd_r8_collect.log`，171 tests collected）。
- 覆盖矩阵：**AC-IB-18-02 由 `Tested（部分）` 转 `Tested`（完整）**；`AC-IB-18-06` 增加跨模块接缝证据。
  可测 AC **79/79**（不变）；全部 US **18/18**、关键路径 **14/14** Must Have US（不变）。
- **FND-R7-01 → CLOSED_VERIFIED**（判据逐条对照见报告 §13.8）。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未用 `-k`/`--deselect`/`--ignore`。

### 12.5 FLAKE-IB-01 登记补全（REV-08-2 第 4 项）

| 栏位 | 内容 |
|------|------|
| 触发条件 | Windows 11 + Python 3.14.6；`ib_embed.server` 以 `ThreadingHTTPServer`（HTTP/1.1 长连接）绑 `127.0.0.1:0` 起真实回环 HTTP；`/warmup` 用例每次新建并 shutdown server；**不可确定性复现** |
| 涉及用例 | `test_ib_embed_wire.py` 的 **TC-INT-025**（warmup 幂等）/ **TC-INT-026**（warmup 失败快速失败 500）——连接级抖动，非断言失败 |
| 稳定性证据 | R8 实测：全量集成 **14 次 / 4 次**命中（≈28.6%）；单文件 **8 次 / 1 次**命中（12.5%）；命中后**立即重跑即通过**。历史：R3 9/2、R4 5/0、R7 全量 0 命中。现场回溯留档 `docs/evidence/groupd_r8_flake_ib01_TC_INT_026.log` |
| 缓解建议（**本轮未实施**） | 在测试请求助手对**连接级异常**（`ConnectionAbortedError`/`ConnectionResetError`，WinError 10053/10054）做**有限有界重试**（≤3 次 + 短退避），**仅**重试连接/读取阶段，**绝不**吞掉断言失败或改写状态码断言；可选：`Connection: close` 或 POST 前 `/healthz` 就绪握手 |
| 处置边界 | **未**改动该测试文件（保留现场证据供 PM 裁决）；**未**改动任何 `src/**` |

### 12.6 门控与度量

门控定义沿用 §6；执行结果（命令 + EXIT + 原始计数；单元 67/67、集成 88/88、E2E 16/16、全量 171/171、
selfcheck 31/31）见 `docs/test_report.md` **§13**。

---

## §13 R9 增量（FLAKE-IB-01 测试侧稳定性治理：连接级有界重试；追加，不改写 §9~§12）

> 触发：**REV-09-1/2（协调者裁决 A）**——处置 **FLAKE-IB-01**（§7 登记，MINOR，测试环境偶发）：
> Windows 回环真 HTTP 偶发 `ConnectionAbortedError[WinError 10053]` / `ConnectionResetError[WinError 10054]`，
> 命中 `tests/integration/test_ib_embed_wire.py` 的 **TC-INT-025 / TC-INT-026**（`/warmup` 用例）。
> 本轮为 **GROUP_D R9 增量**（`INV-GROUP_D-INTELBASE-006`）：在**测试请求助手**内做**有限有界重试**，
> 重跑全量并复跑抖动靶点。**未修改任何 `src/**` 实现代码**（见报告 §14.7）。

### 13.1 治理措施（测试侧；断言语义零变更）

**唯一改动文件**：`tests/integration/test_ib_embed_wire.py`（`+48 / -10`）；改动**仅**在 `_Server.get` / `_Server.post`
共用的**传输助手**（引出 `_request_bounded`）；文件内 **12 条用例的 Setup/Action/Assertion 一字未动**。

| 项 | 设定 | 说明 |
|----|------|------|
| 重试对象 | `(ConnectionAbortedError, ConnectionResetError)` | **仅**这两类连接级瞬态异常（WinError 10053/10054） |
| 尝试上限 | `_MAX_ATTEMPTS = 3`（≤3 次尝试 = ≤2 次重试） | **有限有界**，绝不无限重试 |
| 退避 | `_RETRY_BACKOFF_S = 0.05`（秒） | 短退避 |
| 用尽后 | 裸 `raise` 原样抛出最后一次异常 | 失败**可观测**，绝不静默通过 |
| 明确排除 | `HTTPError`（4xx/5xx）**不重试**，状态码原样返回；`AssertionError` / 其他异常**不捕获** | **不**改写状态码/语义断言；**不**吞断言 |

**硬边界守约（对照 REV-09-1/2，逐条）**：

| 边界 | 实现 | 证据 |
|------|------|------|
| 仅重试连接建立/读取阶段的连接级瞬态 | 单一 `except _CONNECTION_LEVEL_ERRORS` 分支 | 探针 A（`attempts=3` 吸收） |
| 绝不吞断言失败 | 无 `except Exception` / 裸 `except`；`AssertionError` 非 `ConnectionError` 子类 | 探针 D（`attempts=1`，AssertionError 冒泡） |
| 不重写状态码/语义断言 | `except HTTPError` 原样返回 `exc.code` | 探针 E（500 原样） |
| 不得 skip/xfail/assert True 掩盖 | 全文件 0 skip / 0 xfail | 全量日志；`--collect-only` 171 |
| 计数用尽后原样抛出 | 裸 `raise` | 探针 C（`attempts=3`，`ConnectionResetError` 抛出） |

> 守约探针：`docs/evidence/groupd_r9_retry_probe.py` → `groupd_r9_retry_probe.log`（猴补 `urlopen` 直接驱动重试助手）。

### 13.2 FLAKE-IB-01 状态同步

| 栏位 | R8 | **R9（本轮）** |
|------|----|--------------|
| 状态 | OPEN | **MITIGATED**（测试侧治理已实施且机制经探针确证；**不声称 CLOSED**） |
| 治理 | 仅登记 + 缓解建议（未实施） | 传输助手**有界重试**已落地（≤3 次尝试 + 0.05s 退避） |
| 稳定性证据 | 全量集成 14/4 命中、单文件 8/1 命中 | 修复后：单文件 **10/10 绿**、集成层 **8/8 绿** |
| 诚实边界 | 不据「未复现」声称已修复 | 「零复发」无法用有限样本**确证**（8 次集成层全绿在 28.6% 基线下偶然概率 ≈6.8%）；若抖动持续超 3 次窗口，用例仍**响亮失败**（设计使然）→ 届时应升级为环境/产品根因排查 |

### 13.3 覆盖与计数复核

- 用例总数**不变**：**171**（unit 67 / integration 88 / e2e 16）——本轮为**治理 + 复跑**，不扩充/不收缩测试面。
- 可测 AC **79/79**、全部 US **18/18**、关键路径 **14/14** Must Have US（**均不变**）。
- 0 skip / 0 xfail；无 `pytest.ini`/`setup.cfg`/`pyproject.toml`/`tox.ini`（无 addopts）；未用 `-k`/`--deselect`/`--ignore`。

### 13.4 门控与度量

门控定义沿用 §6；执行结果（命令 + EXIT + 原始计数；单元 67/67、集成 88/88、E2E 16/16、全量 171/171、
selfcheck 31/31；含抖动靶点复跑）见 `docs/test_report.md` **§14**。

---

## §14 R10 增量（前端冒烟测试层正式化；追加，不改写 §9~§13）

> 触发：**REV-10-2**（协调者裁决「前端构建阻断修复轮」第 2 项）——GROUP_C R10（REV-10-1，software-developer
> `INV-GROUP_C-INTELBASE-008`）已消除前端构建阻断：`package-lock.json` 同步纳入 `@vue-flow/core`（锁定 1.48.2 / MIT）
> 及 14 个传递依赖、`ConfigPage.vue` 纳入版本控制、去除未用导入；并搭建前端冒烟测试入口
> `src/frontend/tests/frontend.smoke.test.js`（6 例，Node 20 内置 `node:test`，**零新增依赖**）。
> 本轮为 **GROUP_D R10 增量**（`INV-GROUP_D-INTELBASE-007`）：把该**前端冒烟层正式纳入测试计划**、建立溯源、复跑证据。
> **未修改任何 `src/**` 实现代码 / 未修改任何测试代码**（见报告 §15.8）。

### 14.1 前端冒烟测试层（新层，6 例；**独立计数，不并入 Python 171**）

前端冒烟测试文件 `src/frontend/tests/frontend.smoke.test.js`（`@module MOD-IB-24` / `@implements IFC-IB-296`）
由 software-developer 产出；**本层由 `test-engineer` 正式收录、逐条溯源并列入测试计划**（**未改写其任何断言**）。

| TC-ID | 用例（`it`）| 断言面 | US | AC 溯源 | NFR 溯源 | 判定 |
|-------|------------|--------|----|---------|---------|------|
| TC-FE-001 | package.json 声明 `@vue-flow/core`（+ `vue`）依赖 | 依赖声明（工程结构） | US-IB-17 | AC-IB-17-06（「本地打包」**前置**：依赖须为工程声明） | REQ-NFR-IB-12（依赖/许可台账以声明与锁为真源） | PASS |
| TC-FE-002 | `package-lock.json` 与 `package.json` 同步（根 deps 一致 + 传递闭包锁定） | 锁↔声明同步 | —（**工程不变量**；R10 根因守卫） | AC-IB-17-06（可 `npm ci` 复现的**本地打包**能力） | REQ-NFR-IB-08（离线/不外发前提） | PASS |
| TC-FE-003 | ConfigPage.vue 从本地包导入 Vue Flow 与样式（非 CDN） | 源码 import 本地包 + 基础/主题样式 | US-IB-17 | AC-IB-17-06 | REQ-FUNC-IB-25 | PASS |
| TC-FE-004 | 编排图只读不变量（`nodes-draggable=false` / `connectable=false`、无增删**图节点**入口） | 拓扑只读 | US-IB-17 | AC-IB-17-04（界面不提供运行期增删图节点 / 改变拓扑） | REQ-FUNC-IB-26 | PASS |
| TC-FE-005 | 源码与入口零外发 CDN 引用（5 类公网 CDN 主机名零命中） | 源码级不外发 | US-IB-17 | AC-IB-17-06 | REQ-NFR-IB-08 | PASS |
| TC-FE-006 | 构建产物存在且 `dist/index.html` 无绝对外链（**条件式**：`dist/` 存在方断言其内容） | 构建产物级不外发 | US-IB-17 | AC-IB-17-06（「本地打包」的**产物级**证据） | REQ-NFR-IB-08 | PASS |

**溯源说明（据实，不硬凑 AC）**：
- 与「配置页 / 依赖锁 / 本地打包」相关的断言落在 **AC-IB-17-04**（拓扑只读）与 **AC-IB-17-06**（本地打包、不外发）。
- **AC-IB-17-01/02/03**（单一真源 / 往返等价 / 以文档为准）与 **AC-IB-18-02**（装配期拒绝非法配置）**不由本层覆盖**
  —— 它们由 Python 层（TC-UNIT-057/058/062~066、TC-INT-079~087、TC-E2E-015/016）承担；本层**不重复、不替证**。
- **AC-IB-17-05**（凭据只出现键名、前端**渲染期**不回显）**本层不覆盖**（本层无任何凭据渲染断言），其判定**维持不变**（见 §14.3）。
- `REQ-NFR-IB-12`（许可）仅作**间接**溯源：TC-FE-002 的锁同步守卫使 `tech_stack.md` §2.1 登记的许可证集合与锁内实际集合一致
  （台账以锁为真源）；**许可类型本身为文档性结论**（同 AC-IB-07-04 / §5 口径，NOT_TESTABLE）。

### 14.2 运行方式与 CI 接入点

| 项 | 值 |
|----|----|
| 运行命令 | `cd src/frontend && npm test`（= `node --test`，Node 20 内置 `node:test`；**零新增依赖**） |
| 前置条件 | 用例 TC-FE-006 依赖 `dist/`（`npm run build` 产物）**存在**；不存在时以 `t.diagnostic(...)` 标注并**跳过产物断言**（属**前置条件判断**，非削弱断言）；CI 中因**先 build 后 test**，产物必然存在 |
| CI 接入 | `.github/workflows/ci.yml` **阶段9**：`working-directory: src/frontend` → `npm ci && npm run build && npm test`；与 `docs/cicd_pipeline.md` **1.1.1 / R10** 阶段9 定义逐字同步 |
| 守护的回归 | **锁同步**（`package-lock.json` ↔ `package.json`）—— 正是 R10 中 `npm ci` 因锁失同步 `EUSAGE` 失败的**根因守卫**；接入阶段9 后该守卫获**强制力**（此前仅开发机可跑） |

### 14.3 覆盖矩阵更新（仅列因本轮而**变**者）

| AC | 变更前（§4 / §5.1） | **变更后（R10）** | 依据 |
|----|--------------------|------------------|------|
| AC-IB-17-06 | `Tested（部分）`：源码级「本地打包 + 无 CDN」已覆盖；「**禁 Docker / 全物理机裸装**」属部署，冻结 | 维持 `Tested（部分）`，但「本地打包 + 无 CDN」子句的**验证面上移**：由「源码级」（TC-INT-086）扩为「**源码级 + 构建产物级**」（新增 TC-FE-001/003/005/006）；**仍未闭合**的仅剩「禁 Docker 裸装运行形态」（属 GROUP_E 部署，冻结） | 新增 TC-FE 层证据；`dist/index.html` 仅含相对 `/assets/*` 引用（实测） |
| AC-IB-17-05 | `Tested（部分）`：定义层/端点/源码级已覆盖；**前端渲染期不回显凭据**不可验 | **维持 `Tested（部分）`，判定不变**（TC-FE 层**无**凭据渲染断言，**不得**因新增前端层而升级） | 诚实边界：本层未断言凭据渲染 |
| AC-IB-17-04 | `Tested` | 维持 `Tested`（TC-FE-004 提供**前端源码级**只读拓扑佐证，属**补强**而非新覆盖判定） | — |
| AC-IB-18-02 | `Tested`（完整，R8 起） | **维持 `Tested`（完整）**；本层不涉及 | — |

> **诚实边界（构建 ≠ 渲染）**：R10 使 `npm ci` / `npm run build` **可执行并通过**（developer + 独立 verifier 亲跑，见报告 §15），
> 故「前端**构建可行性**」**不再**是 not-verified；但**浏览器内的实际渲染 / 交互**（Vue Flow 挂载画布）仍**无自动化执行环境**，
> 该子句**仍不可验**（报告 §6 NV-07 / §12.7 NV-R7-01 口径相应**收窄**，见报告 §15.6）。

### 14.4 计数口径（前端层与 Python 层**分列**）

- **Python 层（既有三层，算术不变）**：unit **67** + integration **88** + e2e **16** = **171**（本轮**不增删 / 不改名**）。
- **前端层（新层，独立计数）**：TC-FE-001 ~ TC-FE-006 = **6**。
- **口径纪律**：前端 6 例**不并入** Python 的 171 算术（跨运行时 / 跨测试框架，混算即口径污染）；两层各自独立给出门控结论。

### 14.5 门控与度量

- **前端层门控**：**6/6 = 100% PASSED**（本层阈值为「全通过」，与 E2E 关键路径同口径）。
- **Python 三层门控**：沿用 §6；执行结果（命令 + EXIT + 原始计数）见 `docs/test_report.md` **§15**。
- **本轮新发现 → 已修复（R10 修复，REV-10-2 续）**：Python 用例 **TC-INT-086** 原含「显式断言 `@vue-flow/core` **未安装**（磁盘不存在）」的
  边界固化语句（R7 期产物），与 R10 必需的 `npm ci` 冲突 —— **任何已装 `node_modules` 的树内该断言必失败**（曾复现 170 passed / 1 failed）。
  **修复机制**：将该「磁盘存在性」近似判定改为对**原始不变量**——「**前端依赖不随仓库分发**」——的正确、环境自适应判定：
  经 `subprocess` 调 `git ls-files -- src/frontend/node_modules`（**直接**查询入库状态，只读 git 索引、从不 stat 工作树），
  断言结果为空；**未装 / 已装但被 gitignore 均通过，被 `git add -f` 强加入库则失败**（不弱化、不 skip/xfail）。
  该用例为 **GROUP_D / PHASE_09 自有产物**（非 software-developer）。机制、两种磁盘态演示与**负向对照**证据见 `docs/test_report.md` §15.5 与 `docs/evidence/groupd_r10_tcint086_guard.log`。
  **复跑**：已装 `node_modules` 工作树 `python -m pytest tests -q` = **171 passed（EXIT=0）**；`tests/integration` = **88 passed**。
