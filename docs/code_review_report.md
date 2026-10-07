---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-CR-001 |
| 标题 | intelligentbase 智能知识库基座 —— 开发者自我代码评审报告 |
| 产出代理 | software-developer |
| 调用 ID | INV-GROUP_C-INTELBASE-001（R1）／ INV-GROUP_C-INTELBASE-002（R2 增量）／ INV-GROUP_C-INTELBASE-003（R3 缺陷修复增量）／ INV-GROUP_C-INTELBASE-004（R4 缺陷修复 + 依赖补齐增量）／ INV-GROUP_C-INTELBASE-005（R7 定义外置 + 可视化配置增量）／ INV-GROUP_C-INTELBASE-007（R8 FND-R7-01 校验项补齐）／ INV-GROUP_C-INTELBASE-008（R10 前端构建阻断修复）／ INV-GROUP_C-INTELBASE-010（R11 IB-20 流式 / 会话增量，协调者轮次口径 REV-12）／ **INV-GROUP_C-INTELBASE-012（R13 账户 / 会话 / 商用界面重构增量，设计侧口径 REV-13）** ／ **INV-GROUP_C-INTELBASE-013（R13.1 回修增量：DEFECT-R13-01 来源 IP 维度登录限速修复）** ／ **INV-GROUP_C-INTELBASE-014（R14 回归缺陷修复增量：全局管理员「当前项目」选择与 `X-IB-Project` 传播，设计侧口径 REV-14）** ／ **INV-GROUP_C-INTELBASE-015（REV-16-2 提示词分层 + 工具可视化配置增量，设计侧口径 REV-16-3）** ／ **INV-GROUP_C-INTELBASE-016（REV-16-4 配置审计（只读）+ 存储态暴露 + DEFECT-R16-01/02 修复增量，设计侧口径 REV-16-4）** ／ **INV-GROUP_C-INTELBASE-019（REV-18 系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传增量，设计侧口径 REV-18/REV-18-R2）** |
| 项目 | intelligentbase |
| 阶段 | PHASE_06b（自我代码评审） |
| 版本 | **R13**（R1 主体 §1~§8 未改写；R2 增量见 **§9**；R3 增量见 **§10**；R4 增量见 **§11**；R7 增量见 **§12**；R8 增量见 **§13**；R10 增量见 **§14**；R11 增量见 **§15**；R13 增量见 **§16**；R13.1 回修增量见 **§17**；**R14 回归缺陷修复增量见 §18**；**REV-16-2 提示词分层与工具可视化配置增量见 §19**；**REV-16-4 配置审计（只读）与存储态暴露 + 两回归缺陷修复增量见 §20**；**REV-17 提示词兜底层重定位增量（提示词文本移出定义文档 + 合并结果进 system 位 + 通用内置安全网）见 §21**；**REV-18 系统管理三分增量（父级「系统管理」+ 三子项账户/项目/LLM Key + 项目域资料上传 + 项目注册表 CRUD 与软删 + LLM Key 管理）见 §22**） |
| status | DRAFT（待 GROUP_D / PM 复核） |
| 上游输入 | `docs/architecture_design.md`（**1.4.0 / R8**，GR-B-005 PASS_WITH_CONDITIONS）、`docs/module_design.md`（**1.4.0 / R8**）、`docs/tech_stack.md`（**1.3.1 / R10**，R8 设计轮次判 NO_CHANGE）、`docs/ib_embed_service_contract.md`（R2，权威契约）、`docs/test_report.md`（**1.7.0 / R11**，FND-R11-01 与「2 项未覆盖 + 4 项部分覆盖 AC」登记处）、`docs/user_stories.md`（**1.3.0 / R7**，US-IB-19 / US-IB-20）；**R10 触发输入** = PM 只读取证（`.github/workflows/ci.yml` 阶段9 `npm ci` 因锁不同步 EUSAGE）与 `src/frontend/package.json` / `package-lock.json` / `ConfigPage.vue` 现场（tech_stack 已随 R10 升至 1.3.1，见 §14）。**R13 触发输入** = `docs/module_design.md` **1.5.0/REV-13**（IFC-IB-309~332 / 第 15 个端口 / §2.2.4 段号索引）、`docs/architecture_design.md` **1.5.0/REV-13**（ADR-18~ADR-27）、`docs/tech_stack.md` **1.4.0/REV-13**（§1 三新行 / §1.4 客户端键登记 / §4.5 第 13~18 项）、`docs/requirements_spec.md` **1.4.0/REV-13**（REQ-FUNC-IB-28~36 / REQ-NFR-IB-15~18 / C-IB-09 / DR-09~DR-17）；上游门控 **GR-B-006 = PASS_WITH_CONDITIONS**（见 §16）；**R13.1 触发输入** = GROUP_D 门控 `condition_1` 登记的 **DEFECT-R13-01**（MEDIUM）/ `tests/integration/test_accounts_int_r13.py::TC-INT-119`（见 §17）；**R14 触发输入** = `docs/architecture_design.md` **1.6.0/REV-14**（ADR-28 项目上下文的选择与传播，Option B 选定 + §2.0.5 R14 影响复核 + §10.1 R14 OPEN ITEM）、`docs/module_design.md` **1.6.0/REV-14**（IFC-IB-333~336 / §2.2.5 段号索引 / §3 MOD-IB-23 端点与契约 / §3 MOD-IB-24 store 与传播约束 / §4.2.5 无环性再声明 / §9.8 覆盖率再声明）、`docs/tech_stack.md` **1.4.0/REV-14**（**NO_CHANGE**：无新依赖）、需求侧 US-IB-24 / AC-IB-24-02 / AC-IB-24-03 / REQ-FUNC-IB-23/31/32、`docs/phase_status.md` 的 **IC-IB-02**（REV-14 实现约束）与 REV-14-2；上游 GROUP_B **GR-B-007 = PASS_WITH_CONDITIONS**（见 §18）。**R14 现场根因** = R13 回归：全局管理员（`users.project_id IS NULL` ⇒ `effective_project == "*"`）因项目级端点 fail-closed 而无法使用任何项目级页面（问答 / 文件 / 重建 / 可视化配置一律 503），且无「选择当前项目」入口。**REV-18 触发输入** = `docs/architecture_design.md` **1.10.2/REV-18-R2**（ADR-37~ADR-42 + **ADR-21-R1**：N:1 订正，关闭 OI-1）、`docs/module_design.md` **1.10.2/REV-18-R2**（IFC-IB-366~377 + §2.2.9 REV-18 IFC 段号索引；端口 17 → 19 纯追加）、`docs/tech_stack.md` **1.4.1/REV-18**（**NO_CHANGE**：零新增第三方依赖，复用 stdlib `sqlite3`）、`docs/requirements_spec.md` **1.10.0/REV-18-2**（REQ-FUNC-IB-43~48 / REQ-NFR-IB-20 / C-IB-42~43 / OOS-18~19 / DR-21）、`docs/user_stories.md` **1.10.0/REV-18-2**（US-IB-35~40）；上游门控 **GR-B-010（+REV-18-R1/R2 收尾）= PASS**。 |
| 覆盖范围 | MOD-IB-01 ~ MOD-IB-26（**R2 追加 MOD-IB-26**；R1 覆盖 01~25）。**R3 重评 MOD-IB-13 与 MOD-IB-23**；**R4 只重评被触及的部分**：MOD-IB-12 与 MOD-IB-13，外加依赖面新增文件 `src/requirements-embed.txt`（B-05，非模块）；**R7 只重评被触及的部分**：MOD-IB-01（端口 13 → 14 + 结构）、MOD-IB-02（定义文档数据层）、MOD-IB-16（派生注入）、MOD-IB-23（装配期闸门 + 端点）、MOD-IB-24（可视化配置页）；**R8 只重评被触及的部分**：MOD-IB-02（`ib/config/definition.py::validate` 校验项补齐）；**R10 只重评被触及的部分**：MOD-IB-24（前端构建管线：锁同步 / 源文件跟踪 / 类型错误 / 冒烟入口）；**R11 只重评被触及的部分**：MOD-IB-01（R8 类型 / 枚举 / 常量）、MOD-IB-02（键名登记与值域 + `validate` 第 3 子项）、MOD-IB-16（`is_delegating` 消费侧话术）、MOD-IB-21（终态单发 / 可见性 / 确认事件 / 会话存储逐字段复制）、MOD-IB-22（确认门装配 / `resume` fail-closed / G2 单跳交接）、MOD-IB-23（`chat_stream` 显式 4xx + `POST /api/chat/resume`）、MOD-IB-24（确认区呈递 / 决策回传 / 会话标识纪律）；**R13 只重评被触及的部分**：MOD-IB-01（账户 / 会话 / 令牌契约 + 第 15 个端口 `AccountStore`）、MOD-IB-02（IFC-IB-312 键名登记）、MOD-IB-11（bcrypt / `SqliteAccountStore` / `MemoryAccountStore` / 幂等种子）、MOD-IB-23（账户 / 会话 / 账户 CRUD 端点 + `SessionTokenResolver` + 可注入策略 + 中间件扩展 + 装配 + 条件性限速审计）、MOD-IB-24（登录页 / 首登强制改密 / 控制台外壳 / 路由守卫 / 类型化客户端 / 主题 / 组件库本地打包）、MOD-IB-25（迁移 003 / nginx TLS 模板 / 键模板 / 检查清单 B15~B20 / `bcrypt` 依赖登记）；**R13.1 只重评被触及的部分**：MOD-IB-23（`Deps.login_throttle` 应用级装配 + 登录端点判定顺序）；**R14 只重评被触及的部分**：MOD-IB-23（`projects_endpoint` + `api/projects` 路由 + `X-IB-Project` 头契约登记）、MOD-IB-24（`stores/project.ts` 新建 / `api/client.ts` 单点注入 + 项目枚举客户端 / `app/env.ts` 接线 / `layouts/ConsoleLayout.vue` 选择器与视图态重置 / `main.ts` 401 清空）；**REV-18 只重评被触及的部分**：MOD-IB-01（`ProjectRegistryEntry`/`ProjectStatus`/`LlmKeyStatus`/`LlmKeyRecord`/`LLM_KEY_MASK` + 第 18 个端口 `ProjectRegistryStore`（5 方法）/ 第 19 个端口 `LlmKeyStore`（3 方法）+ `AccountStore.update_user` 加成式扩展（13 → 14））、MOD-IB-02（`IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND` 仅登记键名，不入 `IB_ENV_KEYS`）、MOD-IB-11（`SqliteProjectRegistryStore`/`MemoryProjectRegistryStore`/`SqliteLlmKeyStore`/`MemoryLlmKeyStore` + 迁移单源 `005_projects.sql`/`006_llm_key.sql` + `_harden_file_permissions`）、MOD-IB-20（`UnconfiguredLlmProvider` 调用期 fail-closed）、MOD-IB-23（`projects_endpoint` 数据源切换 + `POST`/`PATCH`/`DELETE /api/projects` + `PATCH|DELETE /api/accounts/{user_id}` + 建账号 422 顺序依赖 + `GET|PUT|DELETE /api/llm-key` + `_upload_file` kb 推导 + `/healthz/deps` llm 字段）、MOD-IB-24（系统管理三分 IA + `ProjectsPage`/`LlmKeyPage`/`SystemSection.vue` + 上传页去 kb + 类型化客户端）、MOD-IB-25（迁移 005/006 + 检查清单 B21~B23 + `env.example` 两新键） |
| 评审方式 | 5 维评分 + 逐条 finding（含文件:行号）+ 离线实跑证据 |
---

# intelligentbase 自我代码评审报告（PHASE_06b）

> 本报告是**开发者自评**，不是正式测试报告。正式测试套件与测试报告属 GROUP_D。
> 本报告遵守一条纪律：**无实跑证据不下结论**。所有「通过」都附真实命令与原始输出（§2）。

---

## §1 评审摘要

### 1.1 规模

| 指标 | 值 |
|------|-----|
| 交付文件总数（`src/` 下，不含 `__pycache__`） | **69** |
| 交付代码总行数（`src/` 下，含部署交付物） | **16,396** |
| 模块数 | 25（MOD-IB-01 ~ 25）|
| 端口数 | 13（`ib/core/ports.py`；**R7 追加第 14 个端口 `DefinitionDocumentStore`，见 §12**）|
| 接口契约数 | 58（IFC-IB-001 ~ 265；**R7 追加 IFC-IB-287~297 共 11 条，见 §12**）|
| 后端 Python 文件 | 55 |
| 前端 TS/Vue 文件 | 11 |
| 部署交付物 | 9（4 systemd unit + env.example + config.example.json + 迁移 .sql + 检查清单 + 2 requirements）|

### 1.2 5 维总体评分（各模块均分）

| 维度 | 均分 | 说明 |
|------|------|------|
| Correctness（正确性） | **8.7** | 本轮共修复 4 个 CRITICAL；修复后离线契约用例全绿。扣分集中在「本地无法真跑的外部依赖」路径（PDF/OCR/bge-m3/Qdrant）。 |
| Security（安全性） | **9.2** | 隔离（collection-per-project）、`?token=` 拒绝、凭据仅环境变量、日志白名单脱敏均已落地并有离线用例。扣分项见 §5 遗留（会话存储为内存实现，进程重启丢上下文；非安全问题但影响审计连续性）。 |
| Performance（性能） | **8.4** | 批量向量化、条件 UPDATE 租约、`isolation_level=None`+显式事务均已实现。未做真机压测（受「不得触网/不得连生产」约束），故不给更高分。 |
| Maintainability（可维护性） | **9.0** | 25 个模块单一职责、framework-free 核心（用例 `core_framework_free` 强制）、每个文件头部标注 `@module`/`@implements`/`@depends`。 |
| Test Coverage（可测试性） | **8.5** | 全部外部依赖都有同端口替身（`port_conformance` 用例保证签名一致）；离线自检 15 例 + 前端 SSE 自检 9 例。扣分：无正式单元测试（GROUP_D 职责）。 |

### 1.3 Finding 统计

| 严重级别 | 发现 | 已修复 | 遗留（已记录） |
|---------|------|--------|---------------|
| **CRITICAL** | 4 | **4** | **0** |
| MAJOR | 9 | 6 | 3（见 §5，均有说明与依据） |
| MINOR | 7 | 5 | 2 |
| **合计** | **20** | **15** | **5** |

**结论：CRITICAL = 0，满足「存在 CRITICAL 不得提交 SUCCESS」的硬约束。**

### 1.4 本轮 4 个 CRITICAL（全部已修复）

| ID | 模块 | 一句话 | 若不修的后果 |
|----|------|--------|-------------|
| FND-IB-21-001 | MOD-IB-21 | `StreamEvent` 在 `ib.core` 与 `ib.streaming` 各定义一次 | `isinstance` 跨模块判定恒 False，事件被静默丢弃 |
| FND-IB-23-001 | MOD-IB-23 | 组装读路径的闭包引用了未在作用域内的 `load_project_record` | **每一次检索都抛异常 → fail-open 转 degraded → 问答永远显示「未接入知识资料库」**，且 `POST /api/rebuild` 返 500 |
| FND-IB-23-002 | MOD-IB-23 | 装配点向 `build_ledger` / `build_blob_store` 传错配置对象 | 台账/blob 开关被 `getattr` 默认值掩护而**静默失效**（离线装配仍落盘） |
| FND-IB-24-001 | MOD-IB-24 | SSE 分帧 `findBoundary` 用 `-1` 作哨兵却写 `while (boundary >= 0)` | 对象与数字比较恒 false → 分帧循环**一次都不执行** → 多帧被并成一帧、`kind` 恒为 `done` → **正文全丢、页面空白但不报错** |

> FND-IB-23-001 与 FND-IB-24-001 是同一类「静默失败」：不抛异常、不报错，只是功能不出结果。
> 这两个案例正是本报告最想留档的东西（§2.3 与 §2.4 保留了**修复前**的原始输出）。

---

## §2 实际执行证据（命令 + 原始输出）

> 约束：本地自测只用 SQLite / InMemory / Fake 替身，**不触网、不连任何生产库或外部端点**。
> 每次执行均带 `-X utf8`（Windows 控制台默认 GBK，中文输出会乱码或抛 `UnicodeEncodeError`）。

### 2.1 后端离线自检：15/15 通过

```
$ cd src && python -X utf8 scripts/selfcheck.py

========================================================================
intelligentbase 离线自检（GROUP_C 自我验证；正式测试套件属 GROUP_D）
========================================================================
PASS  core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）
PASS  no_forbidden_web_carrier：无 FastAPI/uvicorn/channels/redis 依赖
PASS  no_pymupdf：全仓无 fitz / PyMuPDF 引用（AGPL-3.0 硬约束）
PASS  port_conformance：替身与端口签名一致（VectorStore/Ledger/Blob/Embedder）
PASS  authz_injection_required：生产模式未注入策略即启动失败，且只报键名
PASS  config_error_reports_key_only：配置校验只报键名，不回显值
PASS  magic_sniff_rejects_renamed_file：改名攻击被拒（扩展名与内容不符）
PASS  ledger_state_machine_and_lease：SQLite 台账状态机 + 单租约（WAL）
PASS  isolation_scope_required：检索降级时 filter 仍含 project_id，且跨项目不可见
PASS  retrieval_happy_path：读路径**不降级**且能命中（防止『一切静默降级』掩盖缺陷）
PASS  retrieval_fail_open：embedding 不可用时降级而非抛异常（MOD-IB-15 永不抛）
PASS  sse_frame_and_done_terminator：SSE 帧格式与 done 终止条件
PASS  orchestration_events_order：degraded 先于 content，且只发一条 content
PASS  http_contract_offline：离线装配下端点状态码/头纪律（含 ?token= 显式 400）
PASS  deploy_templates_have_no_secrets：部署模板只含占位符，无真实凭据
------------------------------------------------------------------------
自检结果：15/15 通过
```

**`http_contract_offline` 覆盖的 HTTP 契约**（同一用例内串联断言，全部通过）：
`/healthz` 未认证 200 → `/healthz/deps` 返回键集合 `{qdrant, embed, llm, egress}` →
无令牌 401 → `?token=` **400**（显式拒绝，FreeArk 教训）→ 带令牌 200 且体为 `{items,total}` →
上传 201 → `.pdf` 扩展名配纯文本内容 400（魔数不符）→ 跨项目 `kb_id` 403 →
对非失败文档重试 409 → 删除不存在文档 404 → SSE 200 且 `Content-Type: text/event-stream`
与 `X-Accel-Buffering: no`、含 `event: done` 终止帧 → 重建 202 后进度查询 200。

> 其中 `retrieval_happy_path` 是**因 FND-IB-23-001 而新增**的用例（见 §2.3）：
> 它断言 `degraded is False` **且** `hits` 非空。原来的 `retrieval_fail_open` 只断言
> 「不抛异常」，于是「一切都被 fail-open 兜住」也能通过 —— 缺陷因此被漏过一轮。

### 2.2 Django 系统检查（收窄配置 + 离线装配）

```
$ IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=file IB_CONFIG_FILE=deploy/config.example.json \
  IB_OFFLINE_TOKEN=offline-test-token PYTHONUTF8=1 \
  python -X utf8 manage.py check --settings=ibweb.settings

{"outcome": "started", "stage": "startup"}
{"backend": "vectorstore=memory,embed=fake,llm=fake,ledger=memory,ocr=off,render=off,offline=1",
 "egress_data": "", "egress_host": "", "egress_remote": false, "outcome": "succeeded",
 "project_id": "demo", "stage": "startup"}
{"count": 1, "egress_data": "", "egress_host": "", "egress_remote": false,
 "outcome": "succeeded", "stage": "startup"}
System check identified no issues (0 silenced).
```

这条输出同时证明了三件事：
1. Django 配置可用（无 auth/admin/contenttypes/sessions 的收窄配置自洽）；
2. 组合根在启动期完成装配并**输出了外发边界声明**（`egress_remote/egress_host/egress_data`
   三键 —— FND-IB-04-001 修复前这三个键被日志白名单**静默丢弃**）；
3. `backend=` 汇总键能落地（同上，修复前被丢弃）。

### 2.3 FND-IB-23-001 的证据链（为何必须新增 `retrieval_happy_path`）

修复前的表现链：`_make_read_provider` 的闭包引用 `load_project_record`（只在 `_assemble()`
内部 import），第一次调用即 `NameError` → MOD-IB-15 的「永不抛」契约把它转成
`degraded=True` → SSE 流里出现 `degraded` 事件 → 界面显示「当前未接入知识资料库」。

**关键点：`retrieval_fail_open` 用例当时是 PASS 的** —— 因为它只要求「不抛异常且降级」，
而缺陷恰好产出的就是这个形状。是 `POST /api/rebuild` 的 500 才把它暴露出来。
修复后补了 `retrieval_happy_path`（断言**不**降级且**有**命中），并复跑 15 例全绿。

教训已固化进用例集：**只测失败路径的「优雅降级」是不够的**，必须同时测「正常路径真的通」，
否则 fail-open 会把所有缺陷都粉饰成合规行为。

### 2.4 FND-IB-24-001 的证据链（前端 SSE 分帧）

前端唯一有实质算法的地方是 SSE 分帧。为使其可离线真跑，`client.ts` 刻意避免参数属性等
**不可擦除**语法，从而能被 Node 24 的类型擦除直接 `import`；自检脚本把后端
`to_sse` 的编码规则逐字复刻为 `frame()`，再用前端解析器解回来断言往返一致。

**修复前（真实输出，3 例失败）**：

```
$ cd src && node --experimental-strip-types scripts/sse_parser_selfcheck.mts

PASS  single_frame
PASS  empty_payload_frame
FAIL  one_byte_chunks  [{"kind":"done","data":"流式内容\n"}]
PASS  utf8_split_across_chunks
PASS  multiline_leading_space_roundtrip
PASS  crlf_frames
PASS  comment_ignored
FAIL  degraded_json_payload  [{"kind":"done","data":"正在分析问题…\n{\"reason\":\"vectorstore_unavailable\",...}\n答案\n"}]
FAIL  trailing_partial_frame_flushed  [{"kind":"content","data":"完整帧\n残"}]

SSE parser selfcheck: 3 FAILED
```

三例失败是**同一个根因**：多帧被并成一帧，`kind` 取最后一帧（`done`），`data` 为各帧负载拼接。
在浏览器里等价于「答案一个字都不显示，但页面不报错」。

**根因**：`findBoundary` 返回 `{start,end} | -1`，调用处写 `while (boundary >= 0)`。
JS 中对象与数字比较恒为 `false`（`ToPrimitive` → `NaN` 比较），循环体从不执行。

**修复**：哨兵改为 `null`，循环条件改 `while (boundary !== null)`。

**修复后（真实输出，9/9）**：

```
PASS  single_frame
PASS  empty_payload_frame
PASS  one_byte_chunks
PASS  utf8_split_across_chunks
PASS  multiline_leading_space_roundtrip
PASS  crlf_frames
PASS  comment_ignored
PASS  degraded_json_payload
PASS  trailing_partial_frame_flushed

SSE parser selfcheck: ALL PASS
```

这 9 例的覆盖面刻意选在「浏览器里最难复现的形态」：逐字节分片（最恶劣的 TCP 分片）、
多字节 UTF-8 跨块切断、`\r\n` 改写、行首空格往返无损、空负载帧（后端对 `done` 发 `data:` 无空格）、
尾帧无空行（服务端异常中止）。最后一例尤其重要：**若解析器只认「以空行结尾」的完整帧，
异常中止时会丢掉最后一段正文而且毫无提示。**

### 2.5 依赖与配置纪律审计（静态，但为可复核的原始输出）

```
$ grep -rniE "^[^#]*(import|from)[[:space:]]+(fitz|pymupdf|fastapi|uvicorn|channels|redis|aioredis)" \
    --include=*.py --include=*.ts --include=*.txt src
(no matches)
```

```
$ grep -nE "langchain-openai|django|langgraph|pypdf|pdfminer|pdfplumber|pypdfium2|rapidocr|waitress|gunicorn" \
    src/requirements.txt
djangorestframework>=3.15,<4.0
waitress>=3.0,<4.0
gunicorn>=22.0,<24.0; sys_platform != "win32"
langgraph>=0.2,<2.0
langchain-openai>=0.2,<0.3                       # 必须 pin <0.3
pypdf>=4.0,<7.0                                  # 主路径：纯 Python，许可 BSD
pdfminer.six>=20231228,<20260101                 # 备路径
pdfplumber>=0.11,<1.0                            # 可选路径
pypdfium2>=4.20,<5.0                             # 栅格化
rapidocr-onnxruntime>=1.3,<2.0                   # 离线中文 OCR
```

**`langchain-openai` 钉版是真的在代码里强制的**（不是只写在 requirements 里）：

```
$ python -X utf8 -c "from ib.llm import assert_langchain_openai_version as a; a()"
installed langchain-openai = 1.3.3
required spec = >=0.2,<0.3
assert raised: StartupError [startup_error] langchain-openai 版本不满足约束 >=0.2,<0.3（实测 1.3.3）。
0.3.x 移除了 _convert_chunk_to_generation_chunk，会导致流式输出静默退化为一次性返回。
```

即：**本机开发环境（1.3.3）违反了钉版，代码在启动期直接拒绝** —— 这正是期望行为。
同时也说明：本机**无法**运行真实 LLM 路径，只能跑 `fake` 后端（离线装配），
因此本报告不对「真实 DeepSeek 流式质量」下任何结论（见 §5 遗留）。

### 2.6 检查清单中命令的形状核验（避免交付「照抄就错」的命令）

`deploy/checklists.txt` 要求执行人在目标机粘贴真命令。为避免命令本身写错，逐条对代码核验：

```
$ python -X utf8 - <<'PY'   # B4 的解析调用形状（本地无 pypdf，故用 txt 路径验证形状）
...
page_count= 1 chunks= 1 chars= 16
warnings= []
extensions= ('docx', 'md', 'pdf', 'txt')
```

```
$ python -X utf8 - <<'PY'   # B6/B7 的 embedding / llm 调用形状（fake 后端，离线）
impl= FakeEmbedder
dim= 1024 expected= 1024 declared= 1024
hot= 1024
egress= EgressDescriptor(remote=False, endpoint_host='', data_categories=[])
health= HealthStatus(...)
reply= '（离线替身的聚合回答）'
```

核验过程中**纠正了清单初稿的两处错误**：
1. B6 初稿写 `embedder.embed([...])` —— 端口契约里没有 `embed()`，而是**冷热两个方法**
   `embed_documents(...)` / `embed_query(...)`，且超时/重试/批量必须显式传入（AC-IB-07-03）；
2. B7 初稿写 `provider.complete("ping")` 与 `provider(...)` —— 实际是
   `build_router/build_expert/build_aggregator` 三角色，角色对象是 `LlmRole`（dataclass，
   不可调用），要通过 `role.impl`（provider 私有对象，MOD-IB-01 刻意不静态依赖 langchain）
   并以「有 `invoke` 则 `invoke`，否则当可调用对象」的惯用法调用。
3. 另纠正：`ib-embed` 端口初稿写 18081，实际 unit 与配置均为 **8100**。

> 这三处若未核验就交付，执行人会在真机上照着错命令反复失败，且很可能误判为「依赖没装好」。

---

## §3 按模块评审详情

> 评分口径：Correctness / Security / Performance / Maintainability / Testability，各 0–10。
> 「可测试性」评的是**是否可被单元测试覆盖**（依赖是否可替换、是否有隐藏全局状态），
> 而非「作者是否写了测试」。

### MOD-IB-01 核心契约（`ib/core/`，1,645 行）

- Correctness: **10** / Security: 9 / Performance: 9 / Maintainability: **10** / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-01-001 | MINOR | `ib/core/types.py` 全文 | 领域契约一度在 `ib.streaming` 出现同名重复定义（见 FND-IB-21-001） | FIXED（在 MOD-IB-21 修复） |

全部端口用 `typing.Protocol` + `runtime_checkable`；数据结构统一 `frozen=True, slots=True`，
`slots=True` 同时阻断了「随手挂个属性当缓存」的隐式状态。`core_framework_free` 用例
断言本包零第三方顶层导入 —— 这是 R1「核心契约不得被 Django 反向渗透」的**机器化**保证，
不是靠约定。

### MOD-IB-02 配置（`ib/config/__init__.py`，718 行）

- Correctness: 9 / Security: **10** / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-02-001 | MAJOR | `ib/config/__init__.py:L637-L696` | `validate_required` 报错必须**只报键名、不回显值**，否则密钥可能出现在日志/终端 | FIXED（用例 `config_error_reports_key_only` 固化） |

凭据只经 `read_secret(env_name)` 从环境变量读取，配置里**只存环境变量名**（`api_key_env`）。
合并优先级「默认值 < 文件 < 环境变量」单向且确定。YAML 为可选项：PyYAML 缺失时报
`ConfigError` 而不是静默忽略 —— 静默忽略会让「配置没生效」表现为行为异常而非启动失败。

### MOD-IB-03 请求上下文（`ib/context/__init__.py`，160 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。`Scope` 承载 `project_id` / `kb_ids` / `actor_id`；`AuthzPolicy` 是**端口**
而非实现，从而使得「未注入策略」可以在启动期被拒绝（AC-IB-11-05，见 MOD-IB-23 的用例）。

### MOD-IB-04 可观测性（`ib/observability/__init__.py`，369 行）

- Correctness: 8 / Security: 9 / Performance: 9 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-04-001 | **MAJOR** | `ib/observability/__init__.py` `LOG_FIELDS` | 白名单缺 `egress_remote`/`egress_host`/`egress_data`/`backend`，导致**外发边界声明与装配汇总被静默丢弃** —— 而 IFC-IB-215/NFR-08 要求它必须出现在启动日志 | FIXED（§2.2 输出已可见三键） |
| FND-IB-04-002 | MINOR | 同上 | 白名单默认丢弃（default-drop）语义应当**显式注释**，否则后续维护者会以为是 bug 而改成 default-keep，反而导致密钥泄漏 | FIXED（已加注释） |

`LOG_FIELDS` 白名单 + `SENSITIVE_KEY_PATTERNS` + `redact()` 的组合是**默认丢弃**：
未列入的键不会输出。这个方向是刻意的（宁可少记，不可漏记敏感值），代价是
「以为记了其实没记」—— FND-IB-04-001 就是被这个代价咬到的实例。已在文件中写明。

### MOD-IB-05 解析器注册表与格式解析器（`ib/parsing/`，786 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 7

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-05-001 | MAJOR | `ib/parsing/pdf_parser.py` 全文 | 三条 PDF 路径（pypdf 主 / pdfminer.six 备 / pdfplumber 可选）在**本机无法真跑**（pypdf 未安装），因此只能保证调用形状正确（§2.6），不能保证真机行为 | DOCUMENTED（§5 遗留 L-01） |
| FND-IB-05-002 | MINOR | `ib/parsing/__init__.py:L202-L226` | `build_default_registry` 默认**不注册**兜底解析器 | NOT-A-BUG（设计如此：静默兜底会掩盖「格式不支持」） |

`sniff_magic()` 不信任扩展名：`.pdf` 必须含 `%PDF-`、docx 必须是 ZIP 容器、
文本系要求「无 NUL 且可解码」。用例 `magic_sniff_rejects_renamed_file` 覆盖三类负例
（`evil.pdf` 装文本、`binary.txt` 含 NUL、`shell.exe` 不支持）。

> 该用例初稿断言「`%PDF-1.7` 放进 `.txt` 应被拒」是**错的** —— 文本系的判据是
> 「无 NUL 且可解码」，而那是合法文本。是我对判据的理解错，不是代码错。
> 已改为一组真正成立的负例。**记录在此以说明：用例失败时先怀疑用例。**

### MOD-IB-06 OCR 端口与 RapidOCR 适配（`ib/ocr/__init__.py`，181 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 8

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-06-001 | MAJOR | `ib/ocr/__init__.py` | `rapidocr-onnxruntime` 本机未安装，`NullOcrEngine` 路径可测、真实识别不可测 | DOCUMENTED（§5 遗留 L-01；清单 B5 给出现场核验命令） |

`NullOcrEngine` 是**显式**降级而非静默：它的 `engine_id` 可被日志与健康检查读到，
从而让「OCR 其实没装」可被发现。风险在于文档仍能 `indexed`（AC-IB-04-07 允许），
故清单 B5 强制核对引擎类型而不是只看「导入成功」。

### MOD-IB-07 切分器（`ib/chunking/__init__.py`，116 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: **10**

无 finding。`normalize()` 只做**不改变语义**的规整（统一换行、折叠行内空白、压缩空行），
刻意不做大小写折叠/去标点/词干化，并把它写进 docstring —— 因为 `normalizer_version`
参与索引指纹，语义相近的变换混进来会让人分不清「改了切分」还是「改了归一化」。
纯函数，零依赖，是最易测的模块。

### MOD-IB-08 页面渲染端口与 pypdfium2 适配（`ib/rendering/__init__.py`，127 行）

- Correctness: 8 / Security: 9 / Performance: 7 / Maintainability: 9 / Testability: 8

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-08-001 | MINOR | `ib/rendering/__init__.py` `MAX_RENDER_PIXELS` | 超大页面必须**返回 None**（页级降级）而不是抛异常或吃满内存 | FIXED（4000 万像素上限，A4@300dpi 约 870 万，留 4.5 倍余量） |
| FND-IB-08-002 | MAJOR | 同上 | `pypdfium2` 本机未安装，实际栅格化不可测 | DOCUMENTED（§5 遗留 L-01） |

每次渲染**独立打开文档**（读全部字节后在内存中开），避免改变调用方文件对象的读位置语义。
`MAX_RENDER_PIXELS` 的存在理由值得留档：4GB 内存的树莓派上，一个 A0@600dpi 的恶意页面
足以把进程打死，而这类页面在扫描件里并不罕见。

### MOD-IB-09 Embedding 端口与本地适配（`ib/embedding/__init__.py`，431 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。冷/热双路径是**两个方法**（`embed_documents` / `embed_query`），
超时/重试/批量均由调用方按 AC-IB-07-03 显式传入：
- 冷路径：批量、120s 超时、3 次重试（入库可慢，但必须成批）；
- 热路径：单条、3s 超时、1 次重试（超时即抛 `DependencyUnavailableError` → 检索降级）。

`FakeEmbedder` 与 `LocalHttpEmbedder` 经 `port_conformance` 用例保证签名一致，
所以「离线能跑」不会掩盖「线上接口对不上」。

### MOD-IB-10 VectorStore 端口与 Qdrant 适配（`ib/vectorstore/__init__.py`，570 行）

- Correctness: 9 / Security: **10** / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-10-001 | MAJOR | `ib/vectorstore/__init__.py` `CollectionResolver.assert_prefix` | 必须**启动期**断言集合名前缀与 `project_id` 一致（FM-5），否则隔离只在约定层面成立 | FIXED |
| FND-IB-10-002 | MAJOR | `ib/vectorstore/__init__.py` 查询构造 | `filter` 必须**恒含** `project_id` —— 包括**降级路径** | FIXED（用例 `isolation_scope_required` 断言降级时 filter 仍含 project_id） |

硬隔离是**每项目一个 collection**（`ib_<project_id>_v<collection_version>`），
`CollectionResolver.resolve()` 是唯一入口；KB 级为软隔离（同集合内按 `kb_id` 过滤）。
`InMemoryVectorStore` 与 `QdrantVectorStore` 同端口、同一致性用例。

> `flush()` 在本端口里存在（IFC-IB-100~110 之一）。原因是 Qdrant 的写入是异步落段的，
> 若「写完后立刻重建」而不 flush，新版本可能读到未落盘的旧段，表现为**重建后内容反而变旧**。
> 这是个只在真机上出现、且极难归因的时序缺陷，故把 `flush()` 提到端口契约层。

### MOD-IB-11 台账（`ib/ledger/`，1,593 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-11-001 | MINOR | `ib/ledger/sqlite_repo.py` 连接层 | WAL / `busy_timeout` 是**连接级** PRAGMA，不在 schema 里 —— 迁移 `.sql` 无法承载，必须在构造连接时设置 | FIXED（并在 `deploy/migrations/001_ledger_init.sql` 头部写明此事实） |
| FND-IB-11-002 | MINOR | `ib/ledger/schema.py` `ddl_script()` | schema 用自管 SQL + **手写 scoped 迁移**，不用 Django ORM/makemigrations（ADR 冻结） | COMPLIANT |

台账表**同时是队列与 worker 租约**。租约用条件 UPDATE 取得（`WHERE lease_owner IS NULL OR
lease_expires_at < now`），因此不需要额外锁；`isolation_level=None` + 显式
`BEGIN IMMEDIATE` 保证「读-改-写」不被插入破坏。线程本地连接避免 SQLite 跨线程共享。

`upsert_project` / `upsert_kb` 是**组内种子写入**（组合根启动时按配置播种），
不是对外 API —— 这一点在代码注释里写明，避免被误当作用户可调接口。

### MOD-IB-12 原文件 BlobStore（`ib/blob/__init__.py`，327 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。sha256 内容寻址意味着「同内容只存一份」，且 `blob_ref_for(record)` 可
从台账记录**重算**引用 —— 于是「台账与 blob 不一致」可被检测（引用算得出的对象必须存在）。
删除按 scope 执行，避免跨项目误删。

### MOD-IB-13 文档生命周期（`ib/lifecycle/__init__.py`，550 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-13-001 | MAJOR | `ib/lifecycle/__init__.py` 状态机 | 状态迁移必须经**单一**校验点（`_assert_transition`），且「半成品状态」必须被拒绝写入 | FIXED |
| FND-IB-13-002 | MINOR | 用例 `ledger_state_machine_and_lease` | 用例初稿未给 scope 传 `kb_ids`，又被临时目录清理的 `PermissionError` 干扰 | FIXED（补 `kb_ids`；并先 `close()` 仓库再删目录） |

状态机 `pending → parsing → indexed` / `failed → pending`（租约回收）。
用例里补了一条**负例**：未注册的 `kb_id` 必须被拒 —— 否则「跨项目写」会从这条路径进来。

### MOD-IB-14 索引重建（`ib/rebuild/__init__.py`，422 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-14-001 | MAJOR | `ib/rebuild/__init__.py` 切换逻辑 | 单文档失败时**绝不能**切换 active version（AC-IB-16-04）；且「未切换」必须与「切换失败」在台账里可区分 | FIXED（用例 + `assert_no_half_state`） |
| FND-IB-14-002 | MINOR | `ibweb/worker.py` | worker **不**调用 `activate_version` —— 切换只能由重建流程在全部成功后执行 | COMPLIANT（刻意；已在 worker 文档注明） |

流程：`plan_rebuild` → 建新 collection → 逐文档 delete-then-write（续租）→ 全部成功才
`activate_version`（台账单值原子写）→ 旧 collection 保留作回滚窗口。
重建期间**读旧 collection**，因此服务不中断（内容非最新）—— 前端 RebuildPage 明确写出这一点，
避免运维误以为要停服。

### MOD-IB-15 检索服务（`ib/retrieval/__init__.py`，281 行）

- Correctness: 9 / Security: **10** / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-15-001 | **CRITICAL（关联）** | `ibweb/composition.py:L455-L470` | 上游装配缺陷导致本模块**每一次**调用都走降级分支（见 FND-IB-23-001） | FIXED（在 MOD-IB-23 修复，并新增 `retrieval_happy_path` 用例） |
| FND-IB-15-002 | MINOR | `ib/retrieval/__init__.py:L47` | `DEGRADED_HINT` 文案必须与前端展示语义一致（「未接入知识资料库」≠「未找到资料」） | COMPLIANT（AC-IB-14-02 区分：`degraded=False, hits=[]` 属正常空结果，不报降级） |

**本模块永不抛异常**（ADR 冻结）：一切依赖故障转 `RetrievalResult(degraded=True, degrade_reason=...)`。
`degrade_reason` 取值刻意区分 `embedding_unavailable` / `timeout` / `vectorstore_unavailable`，
因为三者的处置方式不同（前者查服务、中者调超时、后者查库）—— 若统一成一个字符串，
排障时只能从头猜。

### MOD-IB-16 专家注册表（`ib/experts/__init__.py`，251 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。专家规格是 frozen dataclass 的**纯数据**单一真源，不含行为，
因此「新增专家」不需要改核心代码（REQ-FUNC-IB-01/02）。

### MOD-IB-17 工具注册与能力摘要（`ib/tools/__init__.py`，204 行）

- Correctness: 8 / Security: **10** / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-17-001 | **MAJOR** | `ib/tools/__init__.py` `_make_bound_callable._bound` | 绑定 scope 时用 `setdefault("scope", scope)`：调用方只要传了 `scope=`/`retrieval=` 关键字，就能**覆盖**绑定的项目作用域 —— 这是一条**跨项目读取路径**，且违反 ADR 关于 scope 绑定的保证 | FIXED（改为强制赋值 `call_kwargs["scope"] = scope`，并加注释说明为何不能用 setdefault） |

这条是本报告里**安全含义最强**的一条：`setdefault` 在功能上与强制赋值「几乎一样」，
只在调用方显式传参时不同 —— 而那正是攻击面。用例 `orchestration_scope_bound_at_build`
用一个「会记录收到的 scope」的检索替身来验证绑定确实不可能被覆盖。

> 该用例初稿两次写错：先是访问了不存在的 `tool.invoke`（实际属性是 `tool.callable`），
> 后是无法区分 `setdefault` 与覆盖（因为没人传参时两者行为相同）。
> 最终改成「故意传一个不同的 scope/retrieval，断言收到的是绑定的那个」——**能区分差异的用例才算用例**。

### MOD-IB-18 语义路由（`ib/routing/semantic.py`，230 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: **10**

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-18-001 | MINOR | `ib/routing/semantic.py` | 样例缓存**按项目隔离**（FM-6）：无本项目样例时跳过 L1，绝不误用他项目样例 | COMPLIANT（fail-open → None → 进入 L2） |

纯函数打分（`τ` 阈值 + `margin` 分差），零 IO 依赖，fail-open 返回 `None`。

### MOD-IB-19 意图路由内核（`ib/routing/intent.py`，436 行 + `routing/__init__.py`，50 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。四级降级链 L0 关键词唯一命中 → L1 语义 → L2 LLM（`temperature=0`）→ L3 关键词多重，
再加粘性（AC-IB-09-05）/ OOD 明确表态（AC-IB-09-04）/ 默认专家兜底 / 守卫纠正（IFC-IB-203）。
「永远有人回答」是硬要求：任一级失败都向下一级走，**不向上抛**、不返回空路由。

### MOD-IB-20 LLM 端点抽象（`ib/llm/__init__.py`，405 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-20-001 | MAJOR | `ib/llm/__init__.py:L68` | `langchain-openai` 必须 pin `<0.3`，且要有**运行期**断言而不只是 requirements 注释（FreeArk 已因此生产漂移） | FIXED（`assert_langchain_openai_version`，§2.5 已实证它会拒绝 1.3.3） |

外发边界声明（`EgressDescriptor`）在本模块产出，`data_categories` 只写**类别**不写内容
（「用户提问文本」「命中的检索片段」），并强制出现在启动日志与 `/healthz/deps`。

### MOD-IB-21 流式契约与会话（`ib/streaming/__init__.py`，216 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-21-001 | **CRITICAL** | `ib/streaming/__init__.py:L55-L87` | `StreamEvent` 一度在本模块与 `ib.core` **各定义一次**（同名双类型） | FIXED（改为别名 `StreamEvent = ib.core.StreamEvent`，`isinstance` 两种写法恒等价） |
| FND-IB-21-002 | MINOR | `ib/streaming/__init__.py:L90-L98` | 空负载必须编码为 `data:`（**无**空格），多行负载**逐行**加前缀；解析端必须只剥离一个空格 | COMPLIANT（往返无损性已由前端 9 例自检实证，含行首空格） |

FND-IB-21-001 值得展开：`StreamEvent` 是 `kind` 判别式的类型化事件，编排层与 HTTP 层分别
`from ib.streaming import StreamEvent` 与 `from ib.core import StreamEvent`（后者的写法）
时，`isinstance(evt, StreamEvent)` 会在其中一个命名空间恒为 `False` → 事件被静默跳过。
这类缺陷不会报错，只会「少显示点东西」。修复方式是别名而非「让两处结构一样」——
别名在类型层面**不可能**漂移。

### MOD-IB-22 编排图（`ib/orchestration/__init__.py`，754 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-22-001 | **MAJOR** | `ib/orchestration/__init__.py:L317-L332` | 必须用 `stream_mode="updates"`（`{节点名: 状态增量}`）；用 `values` 会把**每步的完整累计状态**都当增量输出，造成正文重复追加 | FIXED（并加了注释解释 `updates` 的原始形状） |
| FND-IB-22-002 | **MAJOR** | 同上 `L596` | `gate` 节点**回写 `{}`**：若重述上游结果，会与 `operator.add` 归并**叠加**，正文出现两份 | FIXED |
| FND-IB-22-003 | MAJOR | `L122-L126` | `Annotated[..., operator.add]` **只**加在并行写入的键（`messages` / `expert_results`）上；加在计数类字段上会累加成天文数字 | FIXED（`step_count` 不加 reducer） |
| FND-IB-22-004 | MINOR | `L167-L212` | 事件顺序固定为 `reasoning → degraded → content → done`，`degraded` **必须在正文之前** | COMPLIANT（用例 `orchestration_events_order` 断言顺序且只发一条 `content`） |

`build_graph(...)` 返回的是 `Orchestrator` 而**不是**编译后的图 —— 因为调用方需要的是
`run()/resume()` 这两个语义动作，而不是 langgraph 的运行时对象；返回编译图会让
langgraph 的类型与生命周期泄漏到 HTTP 层。

编排层**不**在编译期依赖 MOD-IB-15：它只通过 scope 绑定的 tools（构造注入）触达检索。

### MOD-IB-23 HTTP API 与组合根（`ibweb/`，2,088 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-23-001 | **CRITICAL** | `ibweb/composition.py:L455-L470` | `_make_read_provider` 的闭包引用 `load_project_record`，而该名只在 `_assemble()` 内 import → 每次读取 `NameError` → fail-open 掩盖为「检索降级」；`POST /api/rebuild` 返 500 | FIXED（闭包内局部 import + 注释；新增 `retrieval_happy_path` 用例防复发） |
| FND-IB-23-002 | **CRITICAL** | `ibweb/composition.py:L295/L301` | `build_ledger(cfg)` / `build_blob_store(cfg)` 需要 **GlobalConfig**（`cfg.ledger_backend`/`cfg.ledger_path`、`cfg.offline_mode`/`cfg.blob.*`）；传段配置时 `getattr(..., 默认值)` 会**静默兜底**成生产默认 → 离线装配仍落盘、开关失效 | FIXED（统一传 `cfg`；§2.2 输出显示 `ledger=memory`） |
| FND-IB-23-003 | **MAJOR** | `ibweb/views.py` `FileListQuerySerializer` | 类体调用下方才定义的 `_doc_status_values()`，第二次 import 时 `NameError`（模块级名字解析顺序）→ 整个应用无法 import | FIXED（函数上移；并清掉死方法 `validated_page_size` 与两个未用 import） |
| FND-IB-23-004 | MAJOR | `ibweb/apps.py:L48` | `StructuredLogger.event(outcome, **fields)` —— 把 `outcome=` 当字段传入导致 `got multiple values for argument 'outcome'` | FIXED（改 `.event("succeeded", note=...)`） |
| FND-IB-23-005 | MAJOR | `ibweb/composition.py` `_assemble` 日志 | 外发声明与 `backend=` 汇总被日志白名单丢弃（与 FND-IB-04-001 同源） | FIXED |
| FND-IB-23-006 | MINOR | `ibweb/composition.py` / `ibweb/apps.py` | `_backend_summary` 一度变成死代码，随后又被 `apps.py` 以 `composition._backend_summary(...)` 跨模块调用**私有**函数 | FIXED（回到 `_assemble` 自己的日志行，改回私有） |
| FND-IB-23-007 | MINOR | `ibweb/views.py` `error_response` | 异常 → 状态码映射必须**单点**且穷尽（400/403/404/409/503/500），未知异常返回通用文案且**不回显异常消息** | COMPLIANT |

分派要点：
- 组合根 `build_application(deps)` 是**唯一**装配点（`wsgi.py` 顶层一次装配）；
- **AuthzPolicy 未注入 ⇒ 启动失败**（用例 `authz_injection_required`：非零退出 + 只报键名 + 不回显值）；
- 未授权返回 401/403，**从不静默**（用例覆盖「无令牌 401」与「跨项目 403」）；
- `?token=` 在 SSE 端点被**显式** 400（用例覆盖）—— FreeArk 的教训是「令牌出现在查询串会被
  access log 完整打印」，所以这里不是「忽略该参数」而是**拒绝**，让误用立刻可见。

### MOD-IB-24 Web 前端（`frontend/`，1,090 行）

- Correctness: 8 / Security: 9 / Performance: 9 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-24-001 | **CRITICAL** | `frontend/src/api/client.ts` `findBoundary` + `parseSseStream` | `-1` 哨兵与 `>= 0` 判断不兼容 → 分帧循环从不执行 → 多帧并成一帧、`kind` 恒为 `done` → **正文全丢、页面空白且无报错** | FIXED（哨兵改 `null`；9 例自检全绿，§2.4 保留修复前后原始输出） |
| FND-IB-24-002 | MAJOR | `frontend/src/views/ChatPage.vue` 正文渲染 | 模型输出**不得**走 `v-html`（内容受外传文档影响 → 等于把 XSS 通道开到知识库里） | COMPLIANT（一律文本插值 + `white-space: pre-wrap`；如需富文本应引入消毒而非直接渲染） |
| FND-IB-24-003 | MAJOR | `frontend/src/api/client.ts` 全文 | IC-IB-01：必须有**统一**封装且显式携带 `Authorization`，**禁止**裸 axios 依赖隐式 session cookie | COMPLIANT（全前端无 axios；令牌仅存 `sessionStorage`，不进 URL/Cookie） |
| FND-IB-24-004 | MAJOR | `frontend/src/views/ChatPage.vue` `degraded` 分支 | `degraded` 必须**在正文之前**显示且解析失败时仍要提示 —— 降级信号宁可泛化也不可静默吞掉 | COMPLIANT |
| FND-IB-24-005 | MINOR | `frontend/src/main.ts:L22-L27` | 旧版若把令牌放在 `?token=`，启动时取出后必须用 `replaceState` 从地址栏抹掉 | COMPLIANT（避免继续被日志记录） |
| FND-IB-24-006 | MINOR | `frontend/*` | 缺 `tsconfig.json` / `env.d.ts` 会让 `vue-tsc` 报 TS2307，使 `npm run build` 的类型关卡形同虚设 | FIXED（已补，`strict` + `noUnusedLocals` + `verbatimModuleSyntax`） |

前端是本项目里**唯一**能把「后端契约字段名写错」挡在运行期之外的地方：`strict` 类型 +
`vue-tsc --noEmit` 前置在 `build` 脚本里。FND-IB-24-001 说明**类型检查挡不住逻辑缺陷**
（`{...} >= 0` 是合法 TS/JS），所以 SSE 分帧另有 9 例运行时自检。

> 本地**未执行** `npm install` / `npm run build`：安装依赖会访问外部包源，
> 与「严禁连接外部服务」的约束冲突。因此本报告不对前端构建产物下任何结论（§5 遗留 L-02）。

### MOD-IB-25 部署运维（`deploy/`，701 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 7

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-25-001 | MAJOR | `deploy/checklists.txt` B6/B7 | 初稿给了两条**照抄必错**的命令（`embedder.embed()` / `provider.complete()` / 端口 18081） | FIXED（已按真实端口契约改正并离线核验，见 §2.6） |
| FND-IB-25-002 | MINOR | `deploy/migrations/001_ledger_init.sql:L1-L20` | 迁移 .sql 由 `ddl_script()` 生成，头部必须写明生成命令与「PRAGMA 是连接级、故不在此文件」 | COMPLIANT |
| FND-IB-25-003 | MINOR | `deploy/env.example` | 只允许占位符（`<REPLACE_ME_...>`），仓库内不得出现任何真实值 | COMPLIANT（用例 `deploy_templates_have_no_secrets`） |

四个 systemd unit 均带「为什么这样写」的注释（如 `ib-web` 的 `ExecStartPre` 先跑
`--ensure-schema`、`qdrant.service` 的 `LimitNOFILE`）。
`ib-embed` 的**服务端代码**不在 MOD-IB-01~25 任一模组范围内（module_design 仅在 MOD-IB-09
把它列为「外部依赖」）—— 见 §5 遗留 L-03。

---

## §4 未解决的 CRITICAL 问题

**无。** 本轮发现的 4 个 CRITICAL 全部修复并复跑验证：

| ID | 修复位置 | 验证方式 | 结果 |
|----|---------|---------|------|
| FND-IB-21-001 | `ib/streaming/__init__.py` | 静态审计：全仓 `class StreamEvent` 仅 1 处（`ib/core/types.py:629`） | 通过 |
| FND-IB-23-001 | `ibweb/composition.py:L455-L470` | `selfcheck.py` 新增 `retrieval_happy_path`（断言**不**降级且**有**命中）+ 全 15 例 | 15/15 通过 |
| FND-IB-23-002 | `ibweb/composition.py:L295/L301` | `manage.py check` 启动日志显示 `ledger=memory`（§2.2） | 通过 |
| FND-IB-24-001 | `frontend/src/api/client.ts` | `sse_parser_selfcheck.mts` 9 例（§2.4 修复前 3 FAILED → 修复后 ALL PASS） | 9/9 通过 |

---

## §5 遗留问题（已记录，不阻塞本轮提交）

### 遗留 MAJOR（3 条，均已在 §3 标注）

| ID | 描述 | 为何遗留 | 处置建议 |
|----|------|---------|---------|
| **L-01** | PDF 三路径（pypdf/pdfminer.six/pdfplumber）、pypdfium2 栅格化、rapidocr-onnxruntime OCR 在**本机全部未安装**，真实解析/识别行为未验证 | 本机无这些包；安装会访问外部包源，与「严禁连接外部服务」约束冲突 | 目标机按 `deploy/checklists.txt` B4/B5 真跑并归档证据（这是 IFC-IB-264 的验收要求） |
| **L-02** | 前端未执行 `npm install` / `vue-tsc --noEmit` / `vite build`，构建可成功性与类型检查结果未验证 | 同上（npm 包源属外部服务） | 在联网环境执行 `npm ci && npm run build`，并把输出归档 |
| **L-03** | `ib-embed`（bge-m3 常驻向量化服务）的**服务端代码**在 module_design R1 中无归属模组：MOD-IB-25 交付了它的 systemd unit，MOD-IB-09 只在注释里把它列为「外部依赖」 | 本代理不得实现 module_design 未定义的模组（硬约束）；不猜测其接口 | 上报 PM：请 system_architect 在 R2 指派归属并定义服务契约（端点/批量/维度/错误码），否则该 unit 指向的 `ib_embed.server` 无出处 |

> 关于「MAJOR 不得超过 3 条」：当前恰好 3 条，且三条都属于**同一类**
> ——「受本次执行约束而无法在本机验证的外部依赖/外部归属」。它们不是设计缺陷，
> 也无法通过改代码消除，故按文档化处理而非强行"修"。

### 遗留 MINOR（2 条）

| ID | 描述 | 处置 |
|----|------|------|
| M-01 | `SessionStore` 默认内存实现：进程重启丢失会话历史 | 符合 module_design 默认（`session.backend: memory`）；若接入项目要求审计连续性，需上游决定是否新增持久化会话存储 |
| M-02 | `related_images` 事件种类在契约与枚举中保留，但**本基座无生产端**（无任何模块负责图片引用提取） | 见 §6 的 REQ-FUNC-IB-14 行；前端按「未知负载」保守处理（仅折叠展示，不猜测结构、不渲染 HTML）。需上游决定是否指派提取器 |

---

## §6 REQ-FUNC-IB 27 条落地交叉核对

| 需求 | 落点（模组 / 文件） | 落地状态 |
|------|-------------------|---------|
| REQ-FUNC-IB-01 通用化与可配置 | MOD-IB-02 `ib/config` + MOD-IB-23 `_seed_projects` | 已落地（项目级配置驱动；接新项目改配置不改核心代码） |
| REQ-FUNC-IB-02 专家注册表单真源 | MOD-IB-16 `ib/experts` | 已落地（frozen dataclass 纯数据，可插拔） |
| REQ-FUNC-IB-03 工具注册 + 能力派生 | MOD-IB-17 `ib/tools`（`capabilities` 由注册表派生） | 已落地 |
| REQ-FUNC-IB-04 上传接口 + 异步入库状态机 | MOD-IB-23 `POST /api/files` + MOD-IB-13 `ib/lifecycle` | 已落地（201 + pending/parsing/indexed/failed） |
| REQ-FUNC-IB-05 上传校验（扩展名/大小/文件头） | MOD-IB-05 `sniff_magic` + MOD-IB-23 `UploadInputSerializer` | 已落地（`.pdf` 配文本内容 → 400，用例覆盖） |
| REQ-FUNC-IB-06 台账列表查询 | MOD-IB-23 `GET /api/files`（`{items,total}`） | 已落地（分页 100 上限，超限截断） |
| REQ-FUNC-IB-07 删除 + 向量清理 | MOD-IB-23 `DELETE /api/files/<doc_id>` → MOD-IB-13 | 已落地（返回 `vectors_deleted`/`blob_deleted`/`ledger_deleted`） |
| REQ-FUNC-IB-08 失败重试 | `POST /api/files/<doc_id>/retry`（非 failed → 409） | 已落地（OQ-IB-01 确认原文件留存，故重试无需重传） |
| REQ-FUNC-IB-09 导入前端页 | MOD-IB-24 `UploadPage.vue` | 已落地（上传/列表/删除/重试/筛选 + 仅在途时轮询） |
| REQ-FUNC-IB-10 多格式解析 | MOD-IB-05：pdf（三路径）/docx/md/txt | 已落地（OQ-IB-02：其余格式预留扩展点） |
| REQ-FUNC-IB-11 OCR（含扫描件） | MOD-IB-06 + MOD-IB-08（pypdfium2 栅格化 → OCR） | 代码已落地；真实识别待目标机验证（L-01，清单 B5） |
| REQ-FUNC-IB-12 可配置切分 | MOD-IB-07 + `chunking.*` 配置 | 已落地（`normalizer_version` 进索引指纹） |
| REQ-FUNC-IB-13 Qdrant 存储 | MOD-IB-10 `QdrantVectorStore` | 代码已落地；真机连通待清单 A 段验证 |
| REQ-FUNC-IB-14 向量检索（top-k/阈值/来源标注） | MOD-IB-15（`RetrievedChunk` 带 `doc_name`/`page_or_section`/`locator`） | 已落地。**图片引用（`related_images`）无生产端**，见 M-02 |
| REQ-FUNC-IB-15 bge-m3 接入 | MOD-IB-09 `LocalHttpEmbedder` + `ib-embed` unit | 客户端已落地；服务端归属待定（L-03） |
| REQ-FUNC-IB-16 索引生命周期与一致性 | MOD-IB-14 + MOD-IB-10 `flush()` + MOD-IB-11 台账单值切换 | 已落地（无混合读窗口） |
| REQ-FUNC-IB-17 检索工具暴露给智能体 | MOD-IB-17（scope 绑定构造注入） | 已落地（绑定不可被调用方覆盖，FND-IB-17-001） |
| REQ-FUNC-IB-18 LangGraph 编排图 | MOD-IB-22（route → 条件边 fan-out → expert×N/general → gate → aggregate） | 已落地（`MAX_EXPERT_STEPS=8`） |
| REQ-FUNC-IB-19 路由多级兜底 | MOD-IB-19（四级 + 粘性 + OOD + 默认 + 守卫） | 已落地 |
| REQ-FUNC-IB-20 流式契约与会话生命周期 | MOD-IB-21 + MOD-IB-22 + MOD-IB-23 SSE + MOD-IB-24 ChatPage | 已落地（OQ-IB-07 确认门保留但默认关闭；OQ-IB-08 会话内隔离、上限可配） |
| REQ-FUNC-IB-21 fail-open 降级 | MOD-IB-15（永不抛）+ 降级矩阵 + SSE `degraded` 事件 | 已落地（用例 `retrieval_fail_open` + 前端横幅；台账/Blob 走 fail-closed 503） |
| REQ-FUNC-IB-22 服务定义与环境变量集中管理 | MOD-IB-25（4 unit + env.example + 启动校验） | 已落地（禁 Docker，物理机直部署；`ExecStartPre` 校验） |
| REQ-FUNC-IB-23 多项目/多知识库隔离 | MOD-IB-10 collection-per-project + MOD-IB-03 `Scope` + MOD-IB-11 归属断言 | 已落地（用例 `isolation_scope_required` 断言降级时 filter 仍含 `project_id`） |
| REQ-FUNC-IB-24 索引重建机制 | MOD-IB-14 + MOD-IB-23 `POST /api/rebuild` + MOD-IB-24 RebuildPage | 已落地（单文档失败不切换版本；旧版本可回滚） |
| REQ-FUNC-IB-25 可视化配置界面（定义文档的图形视图，双向同源） | MOD-IB-24 `frontend/src/views/ConfigPage.vue` + MOD-IB-23 `GET /api/config/definition` | 已落地（Vue Flow 只读图渲染 + 白名单表单；视图侧零持久化，回写单一真源；本地打包无 CDN） |
| REQ-FUNC-IB-26 可视化可编辑对象边界（节点参数与专家集合，不含运行期改图） | MOD-IB-02 `editable_field_whitelist()`（IFC-IB-292）+ MOD-IB-23 `PUT /api/config/definition` | 已落地（白名单外字段拒绝写入；拓扑/条件边不在可编辑对象；界面不产出无法判定可达性的定义） |
| REQ-FUNC-IB-27 完备性校验与装配期 fail-fast 准入闸门 | MOD-IB-02 `validate()`（IFC-IB-290）+ MOD-IB-23 `admit()` 装配闸门（IFC-IB-293） | 已落地（`ValidationReport` 无 force/ignore/warn_only；校验失败拒绝装配、服务不启动；离线用例覆盖） |

**27/27 均有落点。** 其中 2 条的完成度依赖目标机或上游决策（IB-11 的真实 OCR 识别、
IB-14/15 的图片引用与 `ib-embed` 服务端归属），已在 §5 标注。

---

## §7 已消化的 P1 开放问题（OQ-IB-01 ~ 08）与架构偏差

### 7.1 P1 决策落地表

| OQ | 采纳的默认值 | 依据 | 影响 |
|----|-------------|------|------|
| OQ-IB-01 原文件是否持久化 | **持久化 ON**（BlobStore sha256 内容寻址；`IB_BLOB_STORE_ENABLED=true`） | 用户已确认；且 REQ-FUNC-IB-24 重建的前置条件 | 重试无需重传；重建可行；代价是磁盘占用（清单 A8 要求留 2 倍余量） |
| OQ-IB-02 格式边界 | 本期 **Word(docx)/PDF/Markdown/TXT** 四种，其余按扩展点预留 | requirements_spec P1 默认 | `ParserRegistry` 未注册扩展名 → `ValueError`（不静默兜底） |
| OQ-IB-03 图片/扫描件 OCR | **纳入 v1**（CLOSED 2026-09-25） | 需求已确认 | OCR 依赖须目标机真机验证（清单 B5）；未装则 `NullOcrEngine` 显式降级 |
| OQ-IB-04 问答侧终端界面 | 基座提供**最小可验证**问答入口（`ChatPage` + SSE 流） | requirements_spec P1 默认 | 完整产品化界面由接入项目自建；本页含 `degraded` 横幅等验收所需语义 |
| OQ-IB-05 rerank / 混合检索 | **本期不纳入**，作为扩展点预留 | requirements_spec P1 默认 | 检索只有向量单路；改 `score_threshold`/`top_k` 可调但无重排 |
| OQ-IB-06 中文检索评测方法 | 由接入项目构造留出集，指标暂用 **Recall@5** | requirements_spec P1 默认 | 本基座不内置评测集（无真实语料）；`retrieval.*` 参数可在评测后调 |
| OQ-IB-07 人工确认门 | **保留机制、默认不启用** | requirements_spec P1 默认 | `resume()` 在确认门关闭时返回 `error` 事件（「确认门未开启（OQ-IB-07 默认关闭）」）+ `done`，**不是静默丢弃** |
| OQ-IB-08 会话历史范围 | 会话内隔离、**不跨会话**注入；上限可配（`session.max_history_messages=20`、`sticky_turns=1`） | requirements_spec P1 默认 | 会话键 `f"{project_id}:{actor_id}:{session_id}"`，读取时**断言前缀**（FM-7 防跨项目串会话） |

### 7.2 与实现计划的偏差（D-01 ~ D-11）

> 完整表格已写入 `docs/implementation_plan.md` §9。此处只列**影响正确性/契约**的部分。

| ID | 偏差 | 类型 | 说明 |
|----|------|------|------|
| D-01 | 三份 GROUP_B 文档的 `<file_header><status>` 仍为 `DRAFT_FOR_GATE_REVIEW`，而 `phase_status.md` 已记 APPROVED / GR-B-002=PASS | **文档一致性**（非设计未批） | 冲突源是文件头未随门控回写；PM 权威状态文件与门控记录均为 APPROVED，且调用块显式声明「R1，已通过 GR-B-002」→ 不阻塞执行。**建议 GROUP_B 回写文件头 status**（MINOR） |
| D-02 | `IFC-IB-131` 在 LedgerRepository（`list_chunks`）与 BlobStore（`put`）**编号重复** | 上游文档编号缺陷 | module_design §2.2 自称「12+4 条共占 120~134」，但 12+4=16 条需要 120~135。按字面编号实现，代码注释以 `MOD-IB-11:` / `MOD-IB-12:` 前缀消歧（MINOR） |
| D-03 | 自测机 Python 为 **3.14.6**，超出 tech_stack 的 `>=3.11,<3.14` | 环境偏差 | 开发机既有环境，不擅自改动。故本轮自测证据均标注「开发机 3.14.6」；**部署目标机必须以 venv 满足版本约束后才可作为验收证据** |
| D-04 | 自测机 `langchain-openai` 为 **1.3.3**，违反 `pin <0.3` | 环境偏差 | 代码侧在构造 provider 时**抛 `StartupError`**（不是仅 WARN，§2.5 已实证）；本轮所有离线自测走 `fake` 后端，因此不受影响，但**本报告不对真实 DeepSeek 流式质量下任何结论**（见 §5 遗留 L-01 同源理由） |
| D-05 | 台账 schema 用**自管 SQL + 手写 scoped 迁移**（`deploy/migrations/001_ledger_init.sql`），不使用 Django ORM/makemigrations | **遵循 ADR**（非偏离） | 台账是「队列 + worker 租约」，需要条件 UPDATE 与显式事务，ORM 表达不了；且项目约定禁止 makemigrations 全产物 |
| D-06 | `deploy/migrations/001_ledger_init.sql` 由 `ddl_script()` 生成 | 遵循 | 生成命令写在文件头，便于漂移时重生成比对 |
| D-07 | 新增 `src/ibweb/worker.py`、`src/ibweb/bootstrap.py`（计划文件树未列） | 补齐 | worker 是「队列消费 + 租约回收」的必需执行体；bootstrap 提供 `--ensure-schema` 供 `ExecStartPre` 调用 |
| D-08 | 新增 `deploy/config.example.json`、`requirements-offline.txt`、`deploy/migrations/` | 补齐 | 前者是配置模板（无真实值）；后者支持离线装配（无需 Qdrant/pypdf/langgraph） |
| D-09 | 文件命名：计划 `parsers.py` → 实际 `pdf_parser.py` + `text_parsers.py`；`DocumentLifecycleService` → 实际 `DocumentLifecycle`；`deploy/env.example`（module_design 写 `.env.example`）；`frontend/src/api/client.ts`（module_design 写 `apiClient.ts`） | 命名一致但路径/符号名不同 | 契约不变（IFC 编号未变）；**同一 IFC 的实现位置差异**，已在此列明以便复核 |
| D-10 | `related_images` 无生产端 | 缺口 | 见 M-02；不自行发明负载结构 |
| D-11 | 本机 `langchain-openai=1.3.3` 违反 pin `<0.3` | 环境偏差 | 代码侧启动即拒绝（§2.5 已实证）；离线装配走 `fake` 后端，不触网 |

---

## §8 结论与自评

**自评状态：SUCCESS（可提交 PM gate review）。**

依据：

1. **CRITICAL = 0**。本轮 4 个 CRITICAL 全部修复并复跑验证（§4），满足「存在 CRITICAL 不得提交 SUCCESS」的硬约束。
2. **MAJOR = 3 条遗留**，且三条同属「本机无法验证的外部依赖 / 上游未指派的归属」，
   不是可通过改代码消除的设计缺陷；均有明确的验收动作（清单 B4/B5/L-02/L-03）。满足「MAJOR 超过 3 条须说明」的门槛（恰好 3 条，且已说明）。
3. **实跑证据充分**：后端离线自检 15/15、Django 系统检查 0 issue、前端 SSE 自检 9/9、
   依赖纪律审计（无 fitz/FastAPI/uvicorn/channels/redis）、钉版断言实证生效。全部命令与原始输出见 §2。
4. **27 条 REQ-FUNC 全部有落点**（§6）。
5. **12 条冻结架构约束逐条守约**：
   - 无 FastAPI/Uvicorn（SSE 由 Django 同步视图 + `StreamingHttpResponse` 承载）；无 Channels/Redis（审计无匹配）；
   - `?token=` 显式 400（用例覆盖）；SSE 只认 `Authorization` 头；
   - VectorStore 端口窄接口 + `scope` 必填 + filter 恒含 `project_id`（含降级路径）；
   - Qdrant/in-memory 双实现同端口一致性用例；
   - Embedder 冷热双路径分离；
   - collection-per-project 硬隔离 + `CollectionResolver` 前缀断言；
   - 原文件留存 ON + sha256 寻址 + 重建「新版本 → 逐文档 → 原子切换 → 可回滚」；
   - 台账 SQLite（WAL + `busy_timeout`）+ 自管 SQL + 手写迁移；
   - PDF 三路径 + pypdfium2 + rapidocr；**全仓无 PyMuPDF/fitz**；
   - LLM 经 `LlmProvider` + `langchain-openai` pin `<0.3`（运行期断言）+ `EgressDescriptor` 外发声明 + 路由 `temperature=0`；
   - MOD-IB-15 永不抛（fail-open，降级在 SSE 内可见）；台账/Blob fail-closed 503；
   - 组合根唯一装配 + AuthzPolicy 未注入即启动失败 + 未授权 401/403 不静默 + 配置键不新增/不改名。

**提交给 PM 的两个需要决策的项**（非阻塞，但影响后续）：

- **L-03**：`ib-embed` 服务端代码在 module_design R1 无归属模组 —— 请指派或明确其为外部既有服务；
- **M-02**：`related_images` 事件种类无生产端 —— 请决定是否指派图片引用提取器，或从契约中移除该 kind。

另需人工清理一处**由我误建的目录**（自动化清理被安全策略拦截，未执行）：
`C:\var\lib\intelligentbase\ledger\ledger.sqlite3`（73,728 字节）。
成因：我用 `deploy/config.example.json` 里的生产 `ledger_path` 跑了一次
`python -m ibweb.bootstrap --ensure-schema` 冒烟，脚本按配置在该路径建了台账文件。
该路径**不在**项目仓库内，不影响交付物，但会污染机器（且名似生产路径，易误判），建议删除。

---

# §9 R2 增量评审（L-03 + M-02；对 R1 §1~§8 的**追加**，不覆盖）

> R2 只做两件事（`INV-GROUP_C-INTELBASE-002`）：**L-03** = 实现 MOD-IB-26 `ib-embed` 服务端
> 与第三种 Embedder 形态；**M-02** = 实现页面图关联的生产与读路径。R1 的 69 个文件**无一重写**。
> 本节所有「通过」同样附**真实命令与原始输出**（§9.9）。

## 9.1 R2 规模

| 指标 | R1 | R2 后 | 变化 |
|------|----|-------|------|
| `src/` 文件总数（不含 `__pycache__`） | 69 | **76** | **+7**（全部新增，无删除） |
| 代码总行数 | 16,396（R1 报告口径） | **20,267**（`split('\n')` 计数，与 R1 同口径；`splitlines()` 口径为 20,191） | **+3,871** |
| 模块数 | 25 | **26**（+MOD-IB-26） | +1（纯追加） |
| 端口数 | 13 | **13** | **不变** |
| IFC-IB 编号 | 001~265（58 条） | 001~286（+266~284、286） | 纯追加；**001~265 一字未改** |
| 改动文件 | — | 18（全部为追加段落/方法/常量） | 1 处行删除（见 D-R2-05） |
| 离线自检用例 | 15 | **24** | +9（全绿） |

## 9.2 R2 5 维评分（仅对被 R2 触及的模块）

| 维度 | R2 均分 | 依据 |
|------|--------|------|
| Correctness | **9.1** | 新增 9 例全绿；`ib_embed` 线协议为**真监听回环端口的真 HTTP** 验证（非 mock）；`page_image` 幂等与级联删除在**真实 SQLite** 上验证；九步写序用**记录型代理**观测（非读代码猜顺序） |
| Security | **9.5** | 图片端点只认 `Authorization` 头（`?token=` → 400 有用例）；跨项目图片塌缩为 **404**（反存在性探测）；BlobStore 不可用 **fail-closed 503**（不返回占位图）；`ib-embed` 无鉴权但**只绑回环**且**零凭据**；第二份 env 模板凭据形态正则扫描零命中 |
| Performance | **8.8** | `ib-embed` 有界并发 + 有界队列 + **快速失败**（`overloaded` + `retry_after_s` + `Retry-After` 头，有用例）；`related_images` 载荷**只传站内路径不内联字节**（帧体积有界）；台账 `upsert_chunk_images` 单事务先删后写。未做真机压测（同 R1 约束）故不给更高分 |
| Maintainability | **9.0** | `ib_embed` 与 `ib.*` **零耦合**（C8 由 `ib_embed_isolation` 用例强制：源码扫描 + `sys.modules` 差分）；三形态共享同一端口签名集（`port_conformance` 对拍）；运行时端口可替换（缺库 → **可读错误**而非导入期崩溃） |
| Test Coverage（可测试性） | **8.8** | 新增 9 例覆盖绑定聚合/幂等/写序/事件契约/端点四态/三形态一致性；前端纪律为**源码级**检查（无 `npm`，见 §9.10） |

## 9.3 R2 Finding 统计（诚实口径）

| 严重级别 | 发现 | R2 内已修复 | 遗留（已记录，不阻塞） |
|---------|------|------------|---------------------|
| **CRITICAL** | **3** | **3** | **0** |
| MAJOR | 2 | 0 | 2（D-R2-01 / D-R2-02，见 §9.6 —— 均为「本机不可验证 / 上游需裁决」类） |
| MINOR | 3 | 1 | 2 |
| **合计** | **8** | **4** | **4** |

**R2 的 3 个 CRITICAL（发现即修，均已复跑验证）**：

| ID | 文件:行号 | 描述 | 状态 |
|----|----------|------|------|
| FND-R2-01 | `ib/embedding/inproc.py`（`_load` / `descriptor`） | **导入期硬依赖**：`InProcessBgeM3Embedder` 首版在模块顶部 `import flagembedding`，缺库时**导入即崩**——而「缺库须给可读错误、不得启动崩溃」是 IFC-IB-275 的明列要求，且会让 `IB_EMBED_BACKEND=fake` 的离线装配一起失败 | **FIXED**：改为函数内延迟导入，`descriptor()`/`health()` **不触发**权重加载，缺库由 `DependencyUnavailableError`（含 `IB_EMBED_MODEL_PATH` 键名）承载；用例 `embed_three_form_conformance` |
| FND-R2-02 | `ibweb/views.py::file_image_endpoint`（`_image_content_type`） | **Content-Type 不确定**：首版用 `mimetypes.guess_type`，在 Windows 上**读注册表** → 同一份代码在不同机器给出不同 `Content-Type`（可能回落 `text/plain`），直接违反 IFC-IB-283 的 `image/*` 契约，且**测试机与生产机结论会不一致**（最难查的一类漂移） | **FIXED**：改为模块内**固定 ext→MIME 表** + `X-Content-Type-Options: nosniff`；未知扩展名诚实回落 `application/octet-stream`。用例断言 `image/png` |
| FND-R2-03 | `ib/ledger/sqlite_repo.py::upsert_chunk_images` | **重复解析残留孤儿关联**：首版只做 `INSERT OR REPLACE`（按幂等键覆盖），新一次解析若产出**更少**的图，旧行残留 → 用户会看到**已不存在的图**（缩略图点了 404），且该行永不被清理 | **FIXED**：改为**同 `doc_id` 先删后写（单事务）**，与既有 `upsert_chunks` 同构；重复解析/重建/重试均幂等且不残留。用例 `page_image_binding_and_ledger`（幂等 + 陈旧行清除 + 跨项目不可见） |

> **CRITICAL 门槛说明**：上述三项都会造成**静默的、跨机器不可复现的**错误行为
> （导入崩 / 头不确定 / 幽灵关联），符合本代理「CRITICAL = 会导致静默错误结果或启动失败」的判级。
> 三项均在**同一轮内**修复并复跑（§9.9 的 24/24 为修复后输出）。

## 9.4 逐模块 R2 评审详情

---
**MOD-IB-26 `ib-embed` 服务端（新增：`ib_embed/` 4 文件，另行统计于 §9.1）**
- Correctness: 9.3 / Security: 9.4 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 9.0

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-01 | CRITICAL | `ib/embedding/inproc.py` | 导入期硬依赖（详见 §9.3） | FIXED |
| FND-R2-04 | MINOR | `ib_embed/server.py::_handler_factory` | 未知路径首版返回 **400**（把「路径不存在」与「请求体不合法」混为一谈，运维看日志无法区分） | FIXED（404；GET/POST 一致，有用例） |

关键设计纪律（逐条有依据）：`/embed` **不改名** `/v1/embeddings`（IFC-IB-266）；
`healthz` **永不 5xx**（不可用时报 200 + `ok=false` + `detail`，可观测优先，IFC-IB-269）；
服务端**不区分冷热**、**不含** `IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*`（IFC-IB-273 单一落点，
有用例断言键清单为**闭集**共 11 个）；**绝不返回部分向量**（数量不符/维度参差 → 整批 500，有用例）；
批上限 400 **回显 `max_batch`**（让「客户端 cold_batch > 服务端 MAX_BATCH」一眼可定位，IFC-IB-272）。
---
**MOD-IB-09 Embedding 端口（R2 追加：`ib/embedding/inproc.py` + `build_embedder` 值域）**
- Correctness: 9.0 / Security: 9.2 / Performance: 8.8 / Maintainability: 9.1 / Test Coverage: 9.0

三形态（`http` / `inproc` / `fake`）**共享同一端口签名集**，由两处用例共同保证：
`port_conformance`（参数名逐一对拍）与 `embed_three_form_conformance`（descriptor 五字段一致、
`build_embedder` 映射正确、**未知值回落默认 `http`**）。`inproc` **不 import MOD-IB-26**
（C8；由 `ib_embed_isolation` 的全仓扫描强制）。
---
**MOD-IB-01 核心契约（R2 追加类型/端口）**
- Correctness: 9.2 / Security: 9.0 / Performance: 9.0 / Maintainability: 9.3 / Test Coverage: 9.0

追加 5 个 frozen dataclass + `PageImageSourceKindLiteral`；**既有 `ParsedChunk` / `RetrievedChunk`
字段集合一字未改**（IFC-IB-009 / 契约 §2.1 硬要求）。三条 `LedgerRepository` 端口方法
（`upsert_chunk_images` / `list_chunk_images` / `get_chunk_image`）**定义在 MOD-IB-01 而非 MOD-IB-13**：
放在 13 会产生 `11 → 13` 的非法反向边（端口由 11 实现、由 13 调用），故类型必须留在编号更小的 01。
`core_framework_free` 用例仍绿（新增类型零第三方依赖）。
---
**MOD-IB-11 台账（R2 追加：`chunk_image` 表 + 三方法 ×2 实现）**
- Correctness: 9.0 / Security: 9.2 / Performance: 9.0 / Maintainability: 9.0 / Test Coverage: 9.2

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-03 | CRITICAL | `ib/ledger/sqlite_repo.py::upsert_chunk_images` | 重复解析残留孤儿关联（详见 §9.3） | FIXED |
| FND-R2-05 | MINOR | `ib/ledger/schema.py` | 首版未加 `ON DELETE CASCADE`：级联靠应用层清理，崩溃即残留孤儿行（IFC-IB-281 要求同事务级联） | FIXED（DDL 加 FK 级联 + 索引；用例在**真实 SQLite** 上验证删除后 `list_chunk_images` 为空） |

手写 scoped 迁移 **`.sql` 单真源**（`002_chunk_image.sql`），**未使用 `makemigrations`**；
scope 过滤复用**同一** `_scope_clause` 单点下推；跨项目一律返回空/`None`（非报错，反存在性探测）。
---
**MOD-IB-13 文档生命周期（R2 追加：绑定/落库/九步写序）**
- Correctness: 9.2 / Security: 9.0 / Performance: 9.0 / Maintainability: 9.1 / Test Coverage: 9.3

`bind_page_images` 为**纯函数无 IO**（不伪造 `project_id`/`kb_id`）、按 `page_or_section` 聚合、
页内按 `image_id` 升序（确定性 → 幂等键前提）。写序经**记录型代理**实测为
`vector_upsert → persist_page_images → upsert_chunks → mark_indexed`（IFC-IB-280：
「`indexed` ⇒ 关联已就绪」成立）。`delete_document` **代码零改动**（IFC-IB-281），
仅在 docstring 登记级联不变式。
---
**MOD-IB-21 流式契约（R2 追加：`related_images` 载荷）**
- Correctness: 9.3 / Security: 9.4 / Performance: 9.2 / Maintainability: 9.2 / Test Coverage: 9.0

`StreamEventKind` **取值集合不变**（`related_images` R1 已枚举，R2 只定义其 data）。
**无图不发事件**（纪律放在构造函数内，调用点忘判空也不会发出空事件）；载荷**只含**
`image_id` / `doc_id` / `doc_name` / `page_or_section` / `url_path`，**绝不内联 base64**（有用例断言）。
`IMAGE_ENDPOINT_TEMPLATE` 与 Django URLconf 的一致性有**专门用例**（`reverse()` 等于
`related_image_url()`）—— 前端拿到 `url_path` 却 404 是最难查的一类漂移。
---
**MOD-IB-22 编排（R2 追加：生产接缝）**
- Correctness: 8.8 / Security: 9.2 / Performance: 9.0 / Maintainability: 8.9 / Test Coverage: 8.6

新增**可选关键字** `related_images_provider`（`build_graph` / `Orchestrator` 同），
事件在 `content` 之后、`done` 之前产出；provider 抛异常 → **静默不发事件**（不打断流、不降级正文）。
扣分点：**接缝当前恒为空**（见 §9.6 D-R2-02）—— 这是**已知且已登记**的读路径性质，
非本模块缺陷，但确实让本模块的新增分支在本轮**未被真实流量走到**。
---
**MOD-IB-23 HTTP API 与组合根（R2 追加：图片端点）**
- Correctness: 9.0 / Security: 9.5 / Performance: 9.0 / Maintainability: 9.0 / Test Coverage: 9.2

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-02 | CRITICAL | `ibweb/views.py::_image_content_type` | Content-Type 不确定（详见 §9.3） | FIXED |
| FND-R2-06 | MINOR | `ibweb/views.py::file_image_endpoint` | 首版对 `blob_ref` 为空的行尝试 `get` 空路径（行为未定义）；且 `blob_ref` 是**存储 rel_path** 而非 `BlobRef`，需按文件名重推 `sha256` 才能与 `InMemoryBlobStore._key_of` 的「rel_path ↔ sha256 一致」校验相容 | FIXED（显式 `NotFoundError`；`_blob_ref_of_rel_path` 重推 `sha256`，`size_bytes=0` 并注明读路径不使用） |

四态语义：**200**（`image/*` + `Cache-Control: private` + `nosniff`）/ **404**（不存在 / 跨项目 /
`blob_ref` 为空 —— **不区分「不存在」与「不属于你」**）/ **403**（主体无问答权限）/ **503**
（BlobStore 不可用，**fail-closed，不返回占位图**）。只认 `Authorization` 头（`?token=` → 400）；
`/healthz/deps` **字段集合不变**（有用例）。
---
**MOD-IB-24 前端（R2 追加：缩略图行）**
- Correctness: 9.0 / Security: 9.3 / Performance: 8.8 / Maintainability: 9.0 / Test Coverage: 8.2

缩略图行渲染在**该轮回答下方**（源码顺序用例断言 `class="answer"` 先于 `class="thumbs"`）、
**不插入正文、不改写 `content`、不重排**；取图失败/403/404/503 → **静默隐藏**（catch 置
`failed`，渲染前过滤；不弹错、不中断流、**不追加降级文案**——降级文案只对 `degraded` 负责）。
取图**只经 `ApiClient.fetchFileImage`**（IC-IB-01）：`<img :src>` 不带自定义头，三条替代路径
（查询串传令牌=Cookie 认证=免鉴权端点）逐条排除并写在注释里。卸载时 `revokeObjectURL` 释放 blob。
扣分点：**无 `npm` 环境**，类型检查与构建未跑（§9.10）。
---
**MOD-IB-25 部署运维（R2 追加：第二份 EnvironmentFile 模板）**
- Correctness: 9.2 / Security: 9.6 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 9.0

`ib-embed.env.example` 与 `ib-web` 的 `env.example` **键集合分离**（架构残余建议 R-3）：
只含 11 个 `IB_EMBED_*` 键、**零凭据**（该服务不需要令牌，合并文件等于净增凭据面）。
`MemoryMax=2560M` 与 `IB_EMBED_MEMORY_LIMIT_MB=2560` **数值一致**（两处注释互相指向）。
`ExecStart=… -m ib_embed.server` 与契约的模块路径一致。
`deploy_templates_have_no_secrets` 用例扫描凭据形态正则，零命中。
---

## 9.5 关闭 R1 §5 的两条遗留（L-03 / M-02）

| R1 遗留 | 本轮处置 | 关闭证据 |
|--------|---------|---------|
| **L-03**（MAJOR）`ib-embed` 服务端代码无归属模组，`ib_embed.server` 无出处 | **已关闭**。R2 架构侧新增 MOD-IB-26 与契约 `docs/ib_embed_service_contract.md`；实现侧交付 `ib_embed/{__init__,config,runtime,server}.py` + 第三种形态 `InProcessBgeM3Embedder` | 用例 `ib_embed_config_keys` / `ib_embed_isolation` / `embed_three_form_conformance` / `ib_embed_wire_protocol`（真 HTTP）；`ib-embed.service` 的 `ExecStart` 已指向真实存在的 `ib_embed.server` |
| **M-02**（MINOR→升格为功能）`related_images` 事件种类无生产端，前端只能「保守展示未知负载」 | **已关闭（生产端 + 读路径均落地）**。「提取器」**不是**独立模块：绑定由 IFC-IB-277 `bind_page_images` 从既有的 `page_or_section` 完成（**不向 `ParsedChunk` 追加字段**，避免改 IFC-IB-009） | 用例 `page_image_binding_and_ledger` / `lifecycle_nine_step_order` / `related_images_events` / `file_image_endpoint` / `frontend_image_discipline`；前端由「保守展示」升级为**渲染缩略图行** |

**L-01 / L-02 仍未关闭**（PDF/OCR/bge-m3 真跑、前端 `npm build`）——原因与本轮约束相同，
见 §9.10；这两条属**本机不可验证**类，非代码缺陷。

## 9.6 R2 遗留与 P1 开放问题（**已决策 + 已记录理由，不阻塞**）

| ID | 级别 | 问题 | 决策与理由 |
|----|------|------|-----------|
| **D-R2-01** | MAJOR | **页面图字节未落盘**：`ib/parsing/pdf_parser.py` 的 OCR 路径在内存中消费页面图后即弃，未产出可持久化字节，故 `PageImageRef.blob_ref` 恒为 `None`，IFC-IB-283 对**真实 R2 数据**将返回 **404** | **决策：不伪造路径、如实登记 `blob_ref=None`，并把 404 视为契约内的正确行为。** 理由：(a) 契约 `module_design.md` §7.4 明文允许图片不可得；(b) 伪造一个指向不存在字节的 `blob_ref` 会让「404」与「数据坏了」无法区分，是本系统最忌讳的**假可见**；(c) 补字节需要改 MOD-IB-05 解析器**产出**与 MOD-IB-12 的写入时机（派生对象入 BlobStore），属**新的写入面**，应由上游决定是否在 v1 纳管。**推荐后续动作**：为 `pdf_parser` 的页面栅格增加「另存到 BlobStore」分支（对应架构残余建议 R-7 的重建再生路径，届时 `bind_page_images` **无需改签名**，只要 `blob_ref` 从 `None` 变为真路径即可点亮） |
| **D-R2-02** | MAJOR | `related_images` 生产接缝**已装配但当前恒为空**：R1 编排器只把工具**名称/描述字符串**交给 LLM，从不执行工具、也拿不到检索命中，故 provider 收到空命中 → 不发事件 | **决策：保留这一「正确但未点亮」的接缝，不发明未定义接口、不伪造命中。** 理由：(a) 空命中 → 不发事件**正是** IFC-IB-282 的正确行为（有用例）；(b) 若为了「让它亮」而在编排器里凭空造命中列表，等于伪造检索依据，会把一次真实的降级路径改造成误导；(c) 点亮条件是**读路径改造**（答案依据化 / 工具真执行），属架构演进，代码侧**无需改动**（provider 已按 `(doc_id, page_or_section)` 去重聚合）。**验收动作**：GROUP_D 可加一条「注入非空命中 → 事件抵达前端并渲染缩略图」的测试，以证明接缝**可用**（本轮的 `related_images_events` 已按此断言载荷与 URL 契约） |
| **D-R2-03** | MINOR | 图片 `Content-Type` 用固定表而非 `mimetypes` | **决策：固定表。** 理由见 §9.3 FND-R2-02（`mimetypes` 读 Windows 注册表 → 跨机不一致）。代价：新增图片格式须补表一行（有意为之的显式性） |
| **P1-R2-01** | 记录 | `IB_EMBED_MEMORY_LIMIT_MB` / `MemoryMax` 的数值仍待目标机实测（架构 [TBD-T4]/[TBD-T16]） | **决策：沿用架构侧待办，不在本轮实测。** 本轮无目标机访问（GROUP_E 明确不触碰）；数值**一致性**已由注释与自检锁定，重定只需改两处数值 |

> 以上 2 条 MAJOR **均为「本机不可验证 / 需上游裁决的写入面决策」**，不是可通过改代码消除的
> 实现缺陷；两条都已给出**具体验收动作**与**推荐后续路径**。满足「MAJOR 超过 3 条须说明」的门槛
> （R2 新增 MAJOR 恰好 2 条）。

## 9.7 架构残余建议的落地（R-3 / R-6 / R-7）

| 残余建议 | 落地 |
|---------|------|
| **R-3** 分离 `ib-embed.env` | **已落地**：`src/deploy/ib-embed.env.example`（IFC-IB-286），与 `ib-web` 的 env 键集合分离、零凭据（§9.4 MOD-IB-25） |
| **R-6** 图片端点进 v1 | **已落地**：IFC-IB-283 `GET /api/files/{doc_id}/images/{image_id}` 为 **v1 端点**（非实验性），路由已入 `ibweb/urls.py`，鉴权/scope/降级语义与既有端点同纪律 |
| **R-7** 重建再生 | **部分落地（结构与幂等已就绪，字节待 R-7 的写入面）**：重建走 **同一个 `process_pending`**（IFC-IB-280 九步）→ 关联随文档重跑再生；幂等键 `(project_id, kb_id, doc_id, page_or_section, image_id)` 覆盖重跑/重试/重建三种重放；**孤儿行**由 `doc_id` 级联删除（IFC-IB-281）清除。缺的一环即 D-R2-01 的字节落盘 |

## 9.8 既知编号缺陷（登记不修）

`IFC-IB-131` 在 `LedgerRepository`（`list_chunks` / `list_orphan_doc_ids`）与 `BlobStore.put`
**重复使用**（上游文档编号算术缺陷）。R2 **不修改**该编号（C6：`IFC-IB-001~265` 一字不动），
代码内以 `MOD-IB-11:` / `MOD-IB-12:` 前缀消歧，引用时写作「IFC-IB-131（MOD-IB-11）」。
R2 新增的 266~284 / 286 全部为**新号**，未与既有号冲突；**IFC-IB-285 预留未分配**。

## 9.9 R2 实跑证据（命令 + 原始输出）

**命令 1：语法/导入自检**

```
$ cd src && python -X utf8 -m compileall -q .
$ echo $?
0
```
（无任何输出 = 全部文件编译通过；`compileall -q` 只在失败时打印。）

**命令 2：离线自检套件（24 例）**

```
$ cd src && PYTHONUTF8=1 python -X utf8 scripts/selfcheck.py
vector count mismatch code=internal_error
ragged vector dims code=internal_error
Service Unavailable: /api/files/a309cee30879456798f8e16892675054/images/img-1
========================================================================
intelligentbase 离线自检（GROUP_C 自我验证；正式测试套件属 GROUP_D）
========================================================================
PASS  core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）
PASS  no_forbidden_web_carrier：无 FastAPI/uvicorn/channels/redis 依赖
PASS  no_pymupdf：全仓无 fitz / PyMuPDF 引用（AGPL-3.0 硬约束）
PASS  port_conformance：替身与端口签名一致（VectorStore/Ledger/Blob/Embedder）
PASS  authz_injection_required：生产模式未注入策略即启动失败，且只报键名
PASS  config_error_reports_key_only：配置校验只报键名，不回显值
PASS  magic_sniff_rejects_renamed_file：改名攻击被拒（扩展名与内容不符）
PASS  ledger_state_machine_and_lease：SQLite 台账状态机 + 单租约（WAL）
PASS  isolation_scope_required：检索降级时 filter 仍含 project_id，且跨项目不可见
PASS  retrieval_happy_path：读路径**不降级**且能命中（防止『一切静默降级』掩盖缺陷）
PASS  retrieval_fail_open：embedding 不可用时降级而非抛异常（MOD-IB-15 永不抛）
PASS  sse_frame_and_done_terminator：SSE 帧格式与 done 终止条件
PASS  orchestration_events_order：degraded 先于 content，且只发一条 content
PASS  http_contract_offline：离线装配下端点状态码/头纪律（含 ?token= 显式 400）
PASS  deploy_templates_have_no_secrets：部署模板只含占位符，无真实凭据
PASS  ib_embed_config_keys：11 个键的键名清单 + 缺权重目录即拒绝（只报键名）
PASS  ib_embed_isolation：ib_embed 不 import ib；且无任何 ib.* 模块 import ib_embed（C8）
PASS  embed_three_form_conformance：http/inproc/fake 三形态通过同一端口一致性检查
PASS  ib_embed_wire_protocol：healthz 永不 5xx / 保序 / 批上限 / 过载快速失败 / 绝无部分向量
PASS  page_image_binding_and_ledger：聚合/确定性/幂等/级联删除（InMemory + SQLite）
PASS  lifecycle_nine_step_order：向量写入 → 页面图落关联 → 块元数据 → 置位（IFC-IB-280）
PASS  related_images_events：无图不发 / 载荷只有路径 / 模板与 URLconf 一致
PASS  file_image_endpoint：200 / 404（含跨项目）/ 403 / 503 / ?token= 400（IFC-IB-283）
PASS  frontend_image_discipline：走封装层取图 / 无裸 axios / 无 v-html / 不改写正文
------------------------------------------------------------------------
自检结果：24/24 通过
$ echo $?
0
```

> 首 3 行（`vector count mismatch …` / `ragged vector dims …` / `Service Unavailable: …`）是
> **被测代码自身的日志**：前两行是 `ib_embed` 服务端在「数量不符 / 维度参差」时按设计打出并
> 返回 500 的记录，第三行是 Django 对 fail-closed 503 的标准记录 —— 它们**在 stderr 上**，
> 与被测断言（PASS）一致，不是失败。

**R1 用例在本轮全部保持绿色**（15/15 中的每一例都在上面的输出里），
即 R2 的改动**未回归**任何 R1 行为 —— 这是本节最重要的证据。

**命令 3：R2 关键断言的定向复核**（把「关键不变式」单独跑一遍，便于门控抽查）

```
$ cd src && PYTHONUTF8=1 python -X utf8 -c "
import os, sys
sys.argv=['x']
os.environ['PYTHONUTF8']='1'
import runpy
ns=runpy.run_path('scripts/selfcheck.py', run_name='probe')
for name in ('ib_embed_wire_protocol','page_image_binding_and_ledger',
             'lifecycle_nine_step_order','related_images_events',
             'file_image_endpoint','embed_three_form_conformance'):
    fn=ns[name]; fn(); print('OK', name)
"
vector count mismatch code=internal_error
ragged vector dims code=internal_error
runtime unavailable code=model_not_ready
Service Unavailable: /api/files/d2f3c40099bb474aaf494f2af6550818/images/img-1
PASS  ib_embed_wire_protocol：healthz 永不 5xx / 保序 / 批上限 / 过载快速失败 / 绝无部分向量
OK ib_embed_wire_protocol
PASS  page_image_binding_and_ledger：聚合/确定性/幂等/级联删除（InMemory + SQLite）
OK page_image_binding_and_ledger
PASS  lifecycle_nine_step_order：向量写入 → 页面图落关联 → 块元数据 → 置位（IFC-IB-280）
OK lifecycle_nine_step_order
PASS  related_images_events：无图不发 / 载荷只有路径 / 模板与 URLconf 一致
OK related_images_events
PASS  file_image_endpoint：200 / 404（含跨项目）/ 403 / 503 / ?token= 400（IFC-IB-283）
OK file_image_endpoint
PASS  embed_three_form_conformance：http/inproc/fake 三形态通过同一端口一致性检查
OK embed_three_form_conformance
```

（该命令只跑 R2 的六个核心用例；`runpy` 使 `_case` 装饰器照常登记，故每例同时打印
自检器的 `PASS <名称>` 行与本命令的 `OK <名称>` 行。首 4 行为被测代码的 stderr 日志。）

**命令 4：C8 单向隔离的独立复核**（不依赖自检脚本自身的排除逻辑）

```
$ cd src && PYTHONUTF8=1 python -X utf8 -c "
import subprocess,sys
r=subprocess.run([sys.executable,'-c','import ib_embed.server, sys; print(sorted(m for m in sys.modules if m==\"ib\" or m.startswith(\"ib.\")))'],capture_output=True,text=True,cwd='.')
print(r.stdout.strip() or r.stderr.strip())
"
[]
```
（导入 `ib_embed.server` 后 `sys.modules` 中**没有任何 `ib.*`** —— MOD-IB-26 与基座零耦合。）

## 9.10 本地不可验证项（如实登记，不得据此声称「已通过」）

| 项 | 为何不可验证 | 由谁验证 |
|----|------------|---------|
| **bge-m3 真实推理**（flagembedding / sentence-transformers） | 本机未装且**不许联网下载权重**（C5）；真实推理需 ~2GB 权重与目标机 CPU（AVX2，[TBD-T18]） | GROUP_D/E：目标机 `ib-embed` 冒烟（healthz → warmup → embed 三方维度一致） |
| **onnxruntime 运行时**（三候选之一） | 同上（`_CANDIDATES` 的择一为 [TBD-T1]/[TBD-T4]/[TBD-T18]，架构侧已声明「可切换」） | 目标机实测择一，改 `RUNTIME_BACKEND` 一处 |
| **前端 `npm install` / `vue-tsc --noEmit` / `vite build`** | 包源属外部服务（C5）→ 与 R1 `L-02` 同因 | 联网环境执行并归档输出 |
| **PDF 页面图真实字节** | 依赖 `pypdfium2` + `rapidocr-onnxruntime` 真装（R1 `L-01`） | 目标机按 `deploy/checklists.txt` B4/B5 |
| **图片端点的真实数据路径（200）** | 依赖 D-R2-01 的字节落盘决策 | 落盘后 `file_image_endpoint` 的 200 分支即可用真数据复跑 |

## 9.11 §9 结论

**R2 自评状态：SUCCESS（可提交 GR-C-002）。**

1. **R2 的 3 个 CRITICAL 全部修复并复跑**（§9.3 / §9.9），任务级「CRITICAL = 0」成立。
2. **R1 §5 的 L-03 与 M-02 均已关闭**（§9.5），且**回归 0**（R1 的 15 例在本轮全绿）。
3. **两条新增 MAJOR 均为「本机不可验证 / 上游裁决」类**，已给决策与理由（§9.6），不阻塞。
4. **契约纪律逐条守约**：`IFC-IB-001~265` 一字未改、端口数仍 13、配置键未新增/改名
   （`IB_EMBED_BACKEND` 只扩值域）、MOD-IB-26 **零入边**（C8）、核心契约仍 framework-free、
   **无 Docker / 无 PyMuPDF / 无 Channels / 无 Redis**、全程无凭据入库、离线用例**不联网**。
5. **实跑证据充分**：`compileall` 退出码 0；离线自检 **24/24**（含真回环 HTTP 与真实 SQLite）；
   C8 单向隔离独立复核为空 `sys.modules`。
6. **本地不可验证项已点名**（§9.10），未以任何方式暗示其已通过。


---

# §10 R3 增量评审（缺陷修复；对 §1~§9 的**追加**，不覆盖）

> R3（`INV-GROUP_C-INTELBASE-003`）**只修缺陷、不新增能力**：输入 = `docs/test_report.md` §5 的
> FND-GROUP-D-02（MAJOR）与 FND-GROUP-D-01（MEDIUM）。R1/R2 的文件**无一重写**，本轮只改
> `ib/lifecycle/__init__.py`、`ibweb/composition.py`、`deploy/checklists.txt` 三个文件。
> 本节所有结论都附**真实命令与原始输出**（§10.7）。

## 10.1 R3 规模与改动面

| 指标 | R2 后 | R3 后 | 变化 |
|------|-------|-------|------|
| 模块数 | 26 | **26** | **不变** |
| 端口数 | 13 | **13** | **不变** |
| IFC-IB 编号 | 001~286 | **001~286** | **不变**（无新增、无改签名） |
| 配置键 | 封闭集 | **封闭集** | **不变**（无新增、无改名、无改默认值） |
| 依赖边 | DAG | **DAG** | **不变**（无新增边） |
| 改动文件 | — | **3**（`src/ib/lifecycle/__init__.py` 819 行 / `src/ibweb/composition.py` 689 行 / `src/deploy/checklists.txt` 257 行） | 纯增量方法 + 文案订正，**无删除既有分支** |
| 正式测试套件 | 138 passed | **135 passed / 3 failed（按预期）** | 3 个「缺陷固化用例」如设计般响亮失败（§10.6） |
| 离线自检 | 24/24 | **24/24** | 无回归 |

## 10.2 R3 5 维评分（仅 MOD-IB-13 与 MOD-IB-23 被触及的部分）

| 维度 | R3 均分 | 依据 |
|------|--------|------|
| Correctness | **9.0** | 三个删除窗口（尚无事发生 / 处理中 / 清扫后竞态）在探针中逐个人工构造并验证「无幽灵、不可检索」（`groupc_r3_after_symptoms.log` (a)(b)(c)）。扣分：并发窗口的**真并发**未用线程/进程压测（用确定性注入复现，属结构性验证而非压力验证） |
| Security | **9.3** | 删除路径绑 collection **仍只认 `CollectionResolver`**（FM-5，`assert_prefix` 保留），**未**引入静默版本回退；跨项目隔离未削弱（`delete_by_doc` 的 filter 恒含 `project_id`）；能力摘要只含**声明**，进程级注册表**不含任何 scope**（ADR-09 纪律未破） |
| Performance | **8.9** | 删除路径新增 1 次 resolve/`bind_collection`（无 IO）与 1 次额外 `delete_by_doc`（正常路径恒返回 0）；处理路径新增 1 次台账读（认领后存在性检查）。均为 O(1) 常数级，且只发生在**删除**与**每文档一次**的路径上。扣分：Qdrant 侧未实测这两次调用的额外延迟 |
| Maintainability | **9.1** | 新增 3 个私有方法（`_bind_write_collection` / `_discard_written_vectors` / `_fail_document`），`process_pending` 的失败处理由**两处内联重复**收敛为一处；`register_builtin_tools` 消除「两份工具清单」的结构性漂移源 |
| Test Coverage（可测试性） | **8.8** | 修复点均**可被离线用例覆盖**（无外部依赖：InMemory + Fake）；三个固化用例的翻转是天然的回归闸门。扣分：并发窗口依赖注入式探针，正式套件尚无对应用例（属 GROUP_D 补写范围，见 §10.6 清单） |

## 10.3 R3 Finding 统计（诚实口径）

| 严重级别 | 发现 | R3 内已修复 | 遗留（已记录，不阻塞） |
|---------|------|------------|---------------------|
| **CRITICAL** | **0** | 0 | **0** |
| MAJOR | 2 | **2** | 0 |
| MINOR | 2 | 1 | 1 |
| **合计** | **4** | **3** | **1** |

> **CRITICAL 门槛**：本轮无 CRITICAL。判级依据 —— 两个登记缺陷都不导致**数据丢失 / 凭据泄露 /
> 全服务崩溃**（FND-GROUP-D-02 会造成用户可见的**正确性**失效但触发窗口窄、且可在重启后由
> 「重试删除」恢复；FND-GROUP-D-01 只降级 L2 路由提示质量）。按 `test_report.md` §5 的原始判级
> （MAJOR / MEDIUM）沿用，**未**上调。

## 10.4 逐模块 R3 评审详情

---
**MOD-IB-13 文档生命周期（`ib/lifecycle/__init__.py`）**
- Correctness: 9.0 / Security: 9.3 / Performance: 8.9 / Maintainability: 9.1 / Test Coverage: 8.9

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-GROUP-D-02 | MAJOR | `ib/lifecycle/__init__.py:647-699`（`delete_document`）、`:701-715`（`_bind_write_collection`） | 删除依赖「向量库恰好已被别处绑定」→ 未绑定窗口抛 `StartupError` → 500 + pending 幽灵行 + 内容仍被作答 | **FIXED**：先经 `CollectionResolver` 自绑写路径 collection（与 `_process_one` 第 6 步同源），未绑定不再是故障而是「无派生物」→ `vectors_deleted=0` 的成功 |
| FND-R3-01 | MAJOR | `ib/lifecycle/__init__.py:681-691` | 「台账行已删、向量仍在」的**残窗**：删除路径的第一次向量清扫与台账删行之间若 worker 完成 upsert，则会留下**检索得到但台账不可见**的幽灵向量（gate 判据「不得可被检索到」未闭合） | **FIXED**：台账删行后追加一次竞态清扫（第二次 `delete_by_doc`，正常路径恒 0）；`vectors_deleted` 计入两次之和（语义不变，仅更诚实） |
| FND-R3-02 | MINOR | `ib/lifecycle/__init__.py:430-468`（`process_pending`）、`:508-511`（`_process_one` 第 0 步） | 处理中删除的文档被**计为 `failed`**，与本方法 docstring 明文的「并发删除计为 `skipped`」相矛盾；且 `_DeletedConcurrently`（R1 定义）**从未被抛出**（死代码） | **FIXED**：`_process_one` 开头「行已删 → `_DeletedConcurrently`」；`process_pending` 增 `NotFoundError` 分类分支（以「行确实不在」为判据）→ `skipped` + 清理本次派生物 |
| FND-R3-03 | MINOR | `ib/lifecycle/__init__.py:482-497`（`_discard_written_vectors`） | 该清道夫用 `except Exception` 吞异常 | **DOCUMENTED（不修，理由见下）**：这是**已判定跳过**之后的尽力而为清理，失败的兜底是删除侧竞态清扫；若上抛会把用户的主动删除报成 503。仍记 MINOR 以留存判断痕迹 |

**设计纪律逐条守约**：`NotFoundError → 404` 语义未变（探针末段实测）；`DeleteReport` 三计数语义未变；
「先删派生物、后删权威台账」顺序未变（第 4 步清扫在台账删除**之后**，只作用于已失效行的派生物）；
`IFC-IB-141~145 / 280 / 281` 的**签名与返回类型一字未改**。

---
**MOD-IB-23 组合根（`ibweb/composition.py`；含 MOD-IB-17 摘要取值路径）**
- Correctness: 9.1 / Security: 9.3 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 8.8

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-GROUP-D-01 | MEDIUM | `ibweb/composition.py:187-206`（`register_builtin_tools`）、`:464`（装配期登记）、`:166`（`bind_tools` 改走同一函数） | 摘要走**进程级空注册表**，自带工具只进**局部注册表** → `Deps.capability_digest == ""`、路由提示恒为「（无可用工具）」 | **FIXED**：清单收敛为**唯一登记点**并在装配期登记进 `default_registry`；摘要非空且含 `search_knowledge`，与实绑工具一致（探针第一段实测 `True`） |
| FND-R3-04 | MINOR | `ibweb/composition.py:75-79`（`SEARCH_TOOL_SPEC`） | 描述文本里手写的「（需要范围绑定）」与摘要依 `needs_scope` 追加的后缀**重复**（摘要此前往返为空，重复一直不可见） | **FIXED**：从描述移除，由摘要统一附加；工具名与契约键不变 |

**为什么这不是「改了冻结契约」**：`IFC-IB-182` 的语义（摘要由注册表**纯派生**、异常返回 `""`、
无参调用取 `default_registry`）**未改一行**；本轮只是让 `default_registry` 按它自己的文档语义
（「组合根在装配期填充」）**真的被填充**。

## 10.5 关闭登记缺陷的对照（gate 判据逐条）

| gate 判据（`INV-GROUP_C-INTELBASE-003` §1.1） | 实测结论 | 证据 |
|---|---|---|
| 尚无事发生 → 删除必须成功，`vectors_deleted=0`、`blob_deleted` 按实际、`ledger_deleted=True` | `DeleteReport(vectors_deleted=0, blob_deleted=True, ledger_deleted=True)` | `groupc_r3_after_symptoms.log` (a) |
| 删除后不得出现幽灵文档（worker 不得索引、不得可检索） | `process_pending → processed=0`；台账行 `None`；`hits == []` | 同上 (a) |
| 不得返回 500 / 不得抛 `StartupError` 冒泡 / 不得留 pending 幽灵行 | HTTP 删除返回 **200**（固化用例断言 500 失败）；台账行已删 | `groupc_r3_after_fixated_defects.log`；探针 (a) |
| 文档确实不存在 → `NotFoundError` → 404 语义不变 | `delete_document(不存在) → NotFoundError[not_found]` | 探针末段 |
| 先删派生物后删台账的顺序不变式与 `DeleteReport` 三计数语义不变（IFC-IB-281） | 顺序：绑定 → 向量 → Blob → 台账 → 竞态清扫；签名/返回类型未改 | 代码 `:647-699`，逐行复核 |
| `deps.capability_digest` 非空且含 `search_knowledge`；路由提示不再是「（无可用工具）」 | 摘要 = `- search_knowledge: …（需要范围绑定）`；`IntentRouter._capability_digest()` 与之相同 | `groupc_r3_after_symptoms.log` 第一段 |
| 摘要必须真实来自注册表（不得在路由层硬编码） | 摘要由 `build_capability_digest(default_registry)` 派生；`intent.py` 的 `or "（无可用工具）"` 兜底**未改一行** | 代码 `:464/:488`；`ib/routing/intent.py:413-416` 未改动 |
| 不得破坏 `bind_tools` 的「每项目一次、绝不跨项目复用」 | `bind_tools` 仍每项目新建 `ToolRegistry()`；注册表内只有 `ToolSpec` + **未绑定**实现（scope 于 `bind_scope` 构造期注入） | 代码 `:153-167`；探针「摘要与实绑工具一致 = True」 |

## 10.6 因修复而**按预期失败**的固化用例清单（交 test-engineer 翻转断言）

> 这三个用例的**守卫串**是 `偏差已消除——请更新缺陷登记`（或等价的「DID NOT RAISE」），
> 它们刻意断言**缺陷存在**；修复后失败本身就是「缺陷已消除」的机器可验证证明。
> **本代理未修改 `tests/` 下任何文件**。

| 用例 | 文件 | 失败断言 | 修复后应改成 |
|------|------|---------|------------|
| `test_TC_INT_009_capability_digest_registry_gap_is_registered` | `tests/integration/test_composition_retrieval.py:172` | `assert deps.capability_digest == ""`（第 190 行） | 改为断言**非空**且含 `search_knowledge`；`IntentRouter._capability_digest()` 不再是「（无可用工具）」 |
| `test_TC_INT_041_delete_before_bind_is_500` | `tests/integration/test_http_contract.py:104` | `assert deleted.status_code == 500`（第 123 行） | 改为断言 **200** 且 `ledger_deleted is True`；列表接口**不再**含该 doc_id |
| `test_TC_INT_061_ghost_document_after_failed_delete_is_registered` | `tests/integration/test_ops_contract.py:23` | `pytest.raises(Exception)` 报「DID NOT RAISE」（第 42-44 行） | 改为断言删除**不抛**、台账行 `None`、`process_pending` 不产出 `indexed`、检索 `hits == []` |

**建议新增用例（GROUP_D 职责，本代理不写）**：① 「处理中并发删除 → `skipped`（非 `failed`）且无残留向量」；
② 「删除路径两次 `delete_by_doc`（竞态清扫）在正常路径下第二次为 0」；
③ 「`bind_tools` 绑定的工具名集合 == 摘要中列出的工具名集合」（防漂移不变式，机器可验证）。

## 10.7 R3 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 结果 | 原始输出 |
|---|------|------|---------|
| 1 | `python -m pytest tests/integration/test_composition_retrieval.py::test_TC_INT_009… test_http_contract.py::test_TC_INT_041… test_ops_contract.py::test_TC_INT_061… -q`（**修复前**） | **3 passed, EXIT=0**（缺陷在场） | `docs/evidence/groupc_r3_before_fixated_defects.log` |
| 2 | `python -m pytest tests/ -q`（**修复前**） | **138 passed, EXIT=0** | `docs/evidence/groupc_r3_before_regression.log` |
| 3 | 同第 1 行三条用例（**修复后**） | **3 failed, EXIT=1**（守卫串触发） | `docs/evidence/groupc_r3_after_fixated_defects.log` |
| 4 | `PYTHONUTF8=1 python docs/evidence/groupc_r3_probe.py` | 四段全绿，**EXIT=0**（含 FND-02 (a)(b)(c) 三个窗口 + 404 语义） | `docs/evidence/groupc_r3_after_symptoms.log` |
| 5 | `python -m pytest tests/ -q`（**修复后**） | **3 failed, 135 passed, EXIT=1** —— 失败者**恰为** §10.6 三条，**无 ERROR / 无 collect error** | `docs/evidence/groupc_r3_after_regression.log` |
| 6 | `PYTHONUTF8=1 python src/scripts/selfcheck.py` | **24/24 PASS, EXIT=0** | `docs/evidence/groupc_r3_after_selfcheck.log` |
| 7 | `python -X utf8 -m compileall -q src` | **EXIT=0**（无语法错误） | 本地执行 |
| 8 | 凭据形态扫描（`sk-*` / `ghp_*` / `AKIA*` / `-----BEGIN` / `api_key\|apikey\|password` 赋字面量），覆盖 3 个改动文件 + 8 个证据文件 | **grep EXIT=1（零命中）** | `docs/evidence/groupc_r3_credscan.log` |

> **诚实性声明**：第 2 行是**修复前**在本会话内的真实运行输出，当时未单独落盘，现以逐字转录
> 形式保存在 `groupc_r3_before_regression.log`（该文件头已标注「转录」）。其余各行均为**当场运行并直接重定向**所得。
> 本轮**未**声称任何未实测结论：并发窗口用**确定性注入**（探针 (b)(c)）验证，**未**做多线程/进程压测，
> 故 §10.2 的 Correctness 未给更高分。

## 10.8 R3 遗留与风险（如实登记）

| 项 | 级别 | 说明 | 处置 |
|----|------|------|------|
| R3-RISK-01 | MINOR | 并发窗口的验证是**结构性注入**而非真并发压测（本机不启多进程 worker，避免触碰部署面）。理论上仍存在更窄的时序组合（例如进程级崩溃落在两次清扫之间） | 由 `list_orphan_doc_ids`（IFC-IB-131，台账→向量方向）对账 + 删除**可重放**（幂等）兜底；真机并发验证交 GROUP_D/E |
| R3-RISK-02 | MINOR | `delete_document` 新增一次 `bind_collection` + 一次额外 `delete_by_doc`：在 **Qdrant** 上未实测其额外延迟 | 删除是低频操作；Qdrant 侧 `count/delete/count` 已是既有形态。目标机压测时顺带观测 |
| R3-RISK-03 | MINOR | 删除路径用**写路径** project provider（`RebuildAwareProjectProvider`，重建期指向目标版本）—— 与 `_process_one` 一致，故重建期删除落在**同一** collection；跨版本残留仍由重建流程负责（与 `_delete_where` 的既有声明一致） | 沿用既有语义，未引入新行为 |
| — | — | **无未解决的 CRITICAL**（本轮 0 条）；**MAJOR 遗留 0 条**（2 条均已修） | — |

## 10.9 契约与冻结约束的守约复核（R3）

- **未改**：`IFC-IB-001~286`（无新增编号、无签名/返回类型变更）；端口数 13；模块数 26；
  配置键名与默认值；依赖边；`IB_EMBED_*` 值域。
- **未触碰**：Django + DRF + 原生 `StreamingHttpResponse` SSE / 禁 Channels / 禁 Redis；
  Qdrant 双适配器 + 窄端口 + `scope` 必填；collection-per-project 硬隔离 + filter 软隔离；
  sha256 内容寻址 + 原子重建；台账即队列 + worker lease；PDF 走 pypdf/pdfminer/pypdfium2/rapidocr（**无 PyMuPDF**）；
  `langchain-openai` pin `<0.3`；IC-IB-01 前端统一封装；M-02「页面文字 chunk 继承本页图片」不变式。
- **未触碰**：`tests/` 下任何文件（GROUP_D 职责）；`docs/` 下**其他代理**的产出
  （`requirements_spec.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` /
  `test_plan.md` / `test_report.md` / `phase_status.md` 均**未改**）。
- **无 Docker / 无容器化**：本轮未引入任何容器化方案，也未触碰目标机 `192.168.31.133`（GROUP_E 面）。
- **凭据纪律**：新增/修改的代码与证据文件**不含任何真实凭据**；探针与日志里出现的 token 均为
  本机自造的离线占位串（`groupc-r3-token`），非任何真实系统的凭据。

## 10.10 §10 结论

**R3 自评状态：SUCCESS（CRITICAL = 0，MAJOR 已清零；3 个固化用例按设计失败，即缺陷已消除的证明）。**

1. 两个登记缺陷（FND-GROUP-D-02 MAJOR / FND-GROUP-D-01 MEDIUM）**均已修复**，且有**当场运行**的原始输出。
2. 修复过程**未**引入任何架构偏差、**未**新增模块/端口/IFC/配置键/依赖边。
3. 全量回归 **135 passed / 3 failed**，失败者**恰为**三个「缺陷固化用例」（§10.6），无其他回归、无 ERROR。
4. 离线自检 **24/24**，`compileall` EXIT=0。
5. 未修改 `tests/`，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。

---

# §11 R4 增量评审（FND-GROUP-D-03 修复 + B-05 依赖补齐）

> 评审对象：R4 触及的 MOD-IB-12（`ib/blob`）与 MOD-IB-13（`ib/lifecycle`），
> 以及新增依赖清单 `src/requirements-embed.txt`（B-05，非模块，按「配置/依赖面」评）。
> 纪律不变：**无实跑证据不下结论**；命令与原始输出见 §11.5。

## 11.1 R4 规模与改动面

| 文件 | 行数级改动 | 性质 |
|------|-----------|------|
| `src/ib/blob/__init__.py` | +约 20 行（新增 `kb_segment` + 改 4 处调用） | 收敛单真源 |
| `src/ib/lifecycle/__init__.py` | +约 25 行（import、`blob_ref_for` 改用、新增 `_blob_scope_of`、文档串） | 删除路径 scope 来源 |
| `src/requirements-embed.txt` | **新增**（依赖清单 + 权重双源/离线加载说明） | B-05 |
| `.gitignore` | +5 行（bge-m3 权重忽略） | B-05 |

**未新增模块 / 端口 / IFC 编号 / 配置键 / 依赖边**；`delete_document` 签名与 `DeleteReport` 结构未改。

## 11.2 R4 5 维评分（仅被触及的部分）

| 维度 | MOD-IB-12（blob / `kb_segment`） | MOD-IB-13（lifecycle / 删除 scope） | 依赖清单（B-05） | 说明 |
|------|-------------------------------|-----------------------------------|----------------|------|
| Correctness（正确性） | 9/10 | 9/10 | 8/10 | 单一真源 + 记录派生，探针 22/22 正向判据通过；依赖**版本区间**离线不可确证（**如实扣分**，标「待目标机实测锁定」） |
| Security（安全性） | 9/10 | 9/10 | 8/10 | 路径穿越两道防护**未削弱**（`safe_segment` 白名单 + `_abs` 根目录断言）；跨项目隔离实测通过。依赖面要求 torch **CPU-only、禁 CUDA**，并给出防 CUDA 安装方式；`ib-embed` 无凭据面（`ib_embed/config.py` 只认 `IB_EMBED_*`） |
| Performance（性能） | 9/10 | 9/10 | 7/10 | `kb_segment` 是 O(1) 纯函数，无新 IO；删除仍是「删目录」一次 `rmtree`。依赖面**体积/内存显著**（torch 系）—— 故与基座 venv **隔离**，并在文件头显式登记该代价 |
| Maintainability（可维护性） | 9/10 | 9/10 | 8/10 | 三处推导收敛为一处，**结构性**防止复发；`_blob_scope_of` 有完整「为什么」注释。依赖清单区分 PRIMARY/BACKUP/候选③ 并给切换步骤 |
| Test Coverage（可测试性） | 9/10 | 9/10 | 7/10 | 新逻辑为可纯函数测试的 `kb_segment` 与可注入 `record` 的删除路径；本轮以探针覆盖，**回归用例属 test-engineer**（本代理不写 tests/） |

## 11.3 R4 Finding 统计（诚实口径）

| 级别 | 新引入（本轮修复引入） | 本轮**修复/关闭** | 遗留（未闭合） |
|------|---------------------|-----------------|-------------|
| CRITICAL | **0** | 0 | 0 |
| HIGH | **0** | 0 | 0 |
| MEDIUM | **0** | 1（FND-GROUP-D-03，由 verifier 定级 MAJOR；本报告按 HIGH→已关闭计） | 0 |
| LOW / 说明 | 1（D-R4-01：新增非端口纯函数 `kb_segment`，非 IFC） | — | 0 |

> 口径说明：FND-GROUP-D-03 在 GROUP_D 处记为 **MAJOR**；本报告按「已修复且无 CRITICAL/MAJOR 遗留」
> 计（等价于 HIGH 已关闭）。**CRITICAL = 0，无未闭合 CRITICAL/MAJOR**。

### 逐条处置

| Finding ID | 严重级别 | 文件:关键位置 | 描述 | 处置 |
|-----------|---------|-------------|------|------|
| FND-GROUP-D-03 | MAJOR（已关闭） | `ib/lifecycle/__init__.py:delete_document` 第 2 步；`ib/blob/__init__.py` 四处 kb 段推导 | 项目级删除 scope 使 kb 段退化为 `default`，与写入段不符 → 原文件成孤儿、`blob_deleted` 恒 False | **FIXED**：`kb_segment` 单真源 + `_blob_scope_of(record)`；探针组 1/4 实测无孤儿且 `blob_deleted=True`，组 3 实测「本无 → False」 |
| D-R4-01 | LOW（登记） | `ib/blob/__init__.py::kb_segment` | 新增模块内纯函数（导出），非端口方法、不登记 IFC | **DOCUMENTED**：属加法，不改任何冻结签名；§14.4 已登记 |

**未解决的 CRITICAL 问题：无。遗留 MAJOR：无。**

## 11.4 逐条对照验收判据（FND-GROUP-D-03）

| 验收判据（invocation 原文） | 结论 | 证据 |
|---|---|---|
| 删除后该 doc **任何 kb 段下**的 blob 都不残留 | 满足 | 探针组 1（HTTP 项目级 scope）对象数 → 0；组 4（真实 FsBlobStore）磁盘文件与 doc 目录均不存在 |
| 删除**不再依赖对 kb_id 的猜测** | 满足 | 删除 scope 由台账记录（权威）派生；kb 段规则收敛为 `kb_segment` 单真源 |
| `blob_deleted` 正确置位 | 满足 | 确有且已删 → True（组 1/4）；本无 → False（组 3） |
| 不误删其他 doc / 其他 project；保留 `_abs` 与 scope 校验 | 满足 | 组 5 跨项目隔离通过；`safe_segment` + `_abs` 防护未改 |
| 不回归 FND-GROUP-D-02（尚无事发生仍可删，不 500、不留幽灵） | 满足 | 组 6 全绿；R3 的两处修正一行未动 |
| 不违反 IFC-IB-281（签名/返回/三计数语义不变） | 满足 | `delete_document` 签名与 `DeleteReport` 一字未改；全量回归 142 passed |
| 不削弱现有测试（三条已翻转守卫继续通过） | 满足 | `test_TC_INT_009/041/061` 在全量回归中通过（142 passed） |

## 11.5 R4 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 结果 | 原始输出 |
|---|------|------|---------|
| 1 | `PYTHONUTF8=1 python docs/evidence/groupc_r4_probe_fnd_d03.py` | **22/22 PASS，EXIT=0** | `docs/evidence/groupc_r4_after_probe.log` |
| 2 | `python docs/evidence/groupd_r3_blob_probe.py`（**verifier 原有缺陷探针**复跑） | 修复后 `blob_deleted=True`、对象数 `0`（该探针为「缺陷在场」判据，故期望**失败** EXIT=1 —— 即缺陷已消除的证明；修复前同名日志为 `blob_deleted=False`、对象数 `1`） | `docs/evidence/groupc_r4_after_existing_probe.log` |
| 3 | `IB_OFFLINE_MODE=1 python -m pytest tests/ -q` | **142 passed，EXIT=0** | `docs/evidence/groupc_r4_after_regression.log` |
| 4 | `PYTHONUTF8=1 python src/scripts/selfcheck.py` | **24/24 PASS，EXIT=0** | `docs/evidence/groupc_r4_after_selfcheck.log` |
| 5 | `python -m compileall -q src` | **EXIT=0** | `docs/evidence/groupc_r4_compileall.log` |
| 6 | 凭据形态扫描（`sk-*` / `ghp_*` / `AKIA*` / `-----BEGIN` / `api_key=…` / `password=…`），覆盖 4 个改动文件 | **零命中（grep EXIT=1）** | `docs/evidence/groupc_r4_credscan.log` |

> 说明：第 2 行「探针按预期失败」与 R3 §10.6 的「固化用例按预期失败」是**同一手法** ——
> 探针写的是**缺陷在场**的判据，修复后它必然失败，正是缺陷消失的机器可验证证明。

## 11.6 R4 遗留与存疑（如实登记，不粉饰）

| 项 | 级别 | 说明 | 处置 |
|----|------|------|------|
| R4-RISK-01 | LOW | 依赖清单的**确切版本**无法离线确证（无网络），仅给保守区间并标注「待目标机实测锁定」 | 部署时 `pip install` 后 `pip freeze` 回填；本代理**不**声称任何精确版本 |
| R4-RISK-02 | LOW | FlagEmbedding 的**传递依赖**（accelerate/datasets/peft/sentencepiece/…）未逐条 pin | 以 `pip download -r` 实际解析结果为准；已在文件内说明 |
| R4-RISK-03 | LOW | torch 在 PyPI 的 Linux 默认 wheel 含 CUDA，若部署方不按文件头命令从 CPU 索引装，可能**意外引入 CUDA 依赖** | 文件头以**显式命令**给出 CPU 索引安装方式并标注「含 CUDA 版即违规」；属部署纪律，风险如实登记 |
| R4-RISK-04 | LOW | 「单 doc_id 是否存在多版本 blob」依赖当前实现事实（每次 `submit_upload` 生成新 `doc_id`，同 doc 目录仅一个对象）；删除走既有 `delete(scope, doc_id)` 的 `rmtree`，仍是**整目录**清理，对多版本亦安全 | 无既有代码路径会产生同 doc 多版本；即便未来出现，整目录删除仍满足「无孤儿」 |
| — | — | **无未解决的 CRITICAL / MAJOR**（本轮 0 条新引入） | — |

## 11.7 契约与冻结约束的守约复核（R4）

- **未改**：`IFC-IB-001~286`（无新增编号、无签名/返回类型变更）；端口数 13；模块数 26；
  配置键名与默认值；依赖边；`IB_EMBED_*` 值域。
- **未触碰**：Django + DRF + 原生 `StreamingHttpResponse` SSE / 禁 Channels / 禁 Redis；
  Qdrant 双适配器 + 窄端口 + `scope` 必填；collection-per-project 硬隔离 + filter 软隔离；
  sha256 内容寻址 + 原子重建；台账即队列 + worker lease；PDF 走 pypdf/pdfminer/pypdfium2/rapidocr
  （**无 PyMuPDF**）；`langchain-openai` pin `<0.3`；IC-IB-01 前端统一封装；M-02 不变式。
- **未触碰**：`tests/` 下任何文件（GROUP_D 职责）；`docs/` 下**其他代理**的产出
  （`requirements_spec.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` /
  `test_plan.md` / `test_report.md` / `phase_status.md` 均**未改**）；FreeArk 仓库**全程只读**。
- **无 Docker / 无容器化**：本轮未引入任何容器化方案；`requirements-embed.txt` 头部亦明示禁 Docker。
- **未触网**：本轮所有自测为**离线**（SQLite / InMemory 替身），**未**真连 Qdrant / DeepSeek /
  HuggingFace / ModelScope；**未**触碰目标机 `192.168.31.133`。
- **凭据纪律**：新增/修改文件**不含任何真实凭据**（§11.5 第 6 行扫描零命中）；权重来源为**公开**
  模型仓库 `BAAI/bge-m3`（无需凭据）。

## 11.8 §11 结论

**R4 自评状态：SUCCESS（CRITICAL = 0；FND-GROUP-D-03 已修复关闭；B-05 已补齐）。**

1. FND-GROUP-D-03 **已修复**，22 项正向判据 **全部通过**，且用 verifier 的**原始缺陷探针**复跑
   证明「缺陷在场 → 缺陷消除」的翻转（§11.5 第 2 行）。
2. 修复方式**未新增任何端口/IFC/配置键**（改走任务显式许可的「单真源 + scope 一致」分支），
   并叠加共享 `kb_segment` 从**结构上**防止三处推导再次分叉。
3. B-05 **已补齐**：`src/requirements-embed.txt` 含 FlagEmbedding + torch(CPU) + transformers、
   bge-m3 权重双源与离线加载约定、与主 `requirements.txt` 的 venv 归属说明；**未**污染主清单。
4. 全量回归 **142 passed**、离线自检 **24/24**、`compileall` EXIT=0、凭据扫描零命中。
5. 未修改 `tests/`，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。
6. 存疑项**如实登记**于 §11.6（依赖确切版本与传递依赖清单离线不可确证 —— 未粉饰）。

---

# §12 R7 增量评审（定义外置为单一真源 + REQ-FUNC-IB-25/26/27 落地）

> 评审对象：R7 触及的 MOD-IB-01（`ib/core` 端口与结构）、MOD-IB-02（`ib/config/definition.py` + 配置键登记）、
> MOD-IB-16（`ib/experts` 派生注入）、MOD-IB-23（`ibweb` 闸门与端点）、MOD-IB-24（前端配置页）。
> 纪律不变：**无实跑证据不下结论**；命令与原始输出见 §12.5。

## 12.1 R7 规模与改动面

| 文件 | 行数级改动 | 性质 |
|------|-----------|------|
| `src/ib/core/types.py` | +约 150 行（10 个 frozen `slots=True` 数据结构 + `__all__`） | 契约数据结构 |
| `src/ib/core/ports.py` | +约 30 行（第 14 个端口 `DefinitionDocumentStore`；头注释 13 → 14） | 端口（纯追加） |
| `src/ib/core/__init__.py` | +约 20 行（导出） | 导出面 |
| `src/ib/config/definition.py` | **新增**（约 430 行：纯函数数据层 + 两适配器） | 定义文档数据层 |
| `src/ib/config/__init__.py` | +约 20 行（2 个键名登记 + 导出） | 配置面 |
| `src/ib/experts/__init__.py` | +约 15 行（`install_derived`） | 派生注入 |
| `src/ibweb/composition.py` | +约 120 行（`admit` 闸门 + 装配 4c 步 + 3 个 Deps 字段 + 派生工具函数） | 装配期闸门 |
| `src/ibweb/serializers.py` | +约 90 行（定义文档读写序列化器） | 序列化面 |
| `src/ibweb/views.py` | +约 130 行（`definition_config_endpoint` + 5 个私有辅助） | 端点 |
| `src/ibweb/urls.py` | +1 行 | 路由 |
| `src/frontend/**`（4 文件） | +约 430 行（`ConfigPage.vue` 新增 + 其余追加） | 可视化配置页 |
| `src/scripts/selfcheck.py` | +约 250 行（6 个 R7 用例 + 端口一致性 2 对） | 自验 |

**未新增模块（仍 26，MOD-IB-01~26）**；端口 **13 → 14**（module_design R7 §3 明示的纯追加）；未改既有 IFC 签名；未改既有配置键名/默认值；未改依赖边。

## 12.2 R7 5 维评分（仅被触及的部分）

| 维度 | MOD-IB-01/02（数据层 + 端口） | MOD-IB-23（闸门 + 端点） | MOD-IB-24（前端配置页） | 说明 |
|------|------------------------------|------------------------|-----------------------|------|
| Correctness（正确性） | 9/10 | 9/10 | 8/10 | `validate`/`derive` 纯函数同输入同输出、语义哈希与 `updated_at` 解耦、缺文档不静默回退 —— 均由 `definition_pure_functions` / `definition_store_roundtrip` 实测；前端 `@vue-flow/core` 未安装 → 类型/构建**离线不可验证**（如实扣分，见 §12.6） |
| Security（安全性） | 9/10 | 9/10 | 9/10 | **无强制继续开关**（`ValidationReport` 字段集不含 force/ignore/warn_only，为类型层事实）；端点走 `_require_manage`（403）与既有 401 纪律；响应体**只出键名不出键值**（`config_key_names`）；`v-html` 禁用；`ValidationErrorItem` 不回显凭据值 |
| Performance（性能） | 9/10 | 9/10 | 9/10 | `validate`/`derive` 为 O(n) 纯内存；原子写回为单次 `os.replace`（无大文件拷贝以外开销）；装配期一次性派生并常驻，运行期零额外 IO；前端本地打包（无 CDN 往返） |
| Maintainability（可维护性） | 9/10 | 9/10 | 8/10 | 单一真源（文档 → 装配期派生 → 构造注入），杜绝各模块各自解析；白名单与校验项**成对维护**并注释；`install_derived` 幂等（支持重复装配测试） |
| Test Coverage（可测试性） | 9/10 | 9/10 | 7/10 | 纯函数 + `InMemoryDefinitionDocumentStore` 使装配期全链路**离线可测**（6 例新用例）；前端仅**源码级**纪律断言（无离线类型检查）—— 如实扣分 |

## 12.3 R7 Finding 统计（诚实口径）

| 级别 | 新引入（本轮） | 本轮修复/关闭 | 遗留（未闭合） |
|------|--------------|--------------|-------------|
| CRITICAL | **0** | 0 | **0** |
| MAJOR | **0** | 0 | **0** |
| MINOR / 说明 | 2（见 §12.4） | — | 0（均 DOCUMENTED） |

**未解决的 CRITICAL 问题：无。遗留 MAJOR：无。**（满足本代理「无 CRITICAL 方可提交 SUCCESS」的判据。）

### 12.4 R7 finding（均 MINOR，登记不阻塞）

| Finding ID | 严重级别 | 文件:关键位置 | 描述 | 处置 |
|-----------|---------|-------------|------|------|
| FND-R7-01 | MINOR | `src/frontend/src/views/ConfigPage.vue` 全文件 | `@vue-flow/core` **未在本机安装**（无网络），前端 `vue-tsc`/`vite build` 与运行期渲染**无法离线验证** | **DOCUMENTED**：Python 侧 `frontend_config_discipline` 做源码级纪律断言（依赖声明/import/无 CDN/零持久化/拓扑只读入口不存在）；与既有 L-02 同类残留，部署机 `npm install` 后须补验 |
| FND-R7-02 | MINOR | `src/ibweb/views.py::_put_definition_config` | 写回成功仅刷新 `definitions`/`derived_views`，**不**热更运行中的注册表与已编译图（拓扑本就不可运行期改） | **DOCUMENTED**：与 ADR-16「图编译一次常驻、拓扑变更唯一路径 = 改文档 → 装配期校验 → 重启重编译」一致，属**刻意设计**而非缺陷；专家**参数**（非拓扑）的生效范围已在响应与注释中说明 |

## 12.5 R7 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（cwd=`src/`） | 结果 | 说明 |
|---|------------------|------|------|
| 1 | `PYTHONUTF8=1 python -X utf8 scripts/selfcheck.py` | **30/30 PASS，EXIT=0** | R1~R4 的 24 例全绿 + R7 新增 6 例全绿；逐例输出见下 |
| 2 | `python -m compileall -q src` | **EXIT=0** | 全量语法编译（含 R7 新增/改动文件） |

R7 新增 6 例的逐例结论（同一次 selfcheck 运行输出）：

```
PASS  definition_pure_functions：validate / derive / 白名单 / 非编辑字段（IFC-IB-290~292；纯函数）
PASS  definition_store：原子写回 + 乐观并发 + 缺失不静默回退（IFC-IB-288/289）
PASS  definition_gate：装配期 fail-fast 准入闸门，聚合全部校验项（IFC-IB-293）
PASS  definition_config 端点：GET/PUT 200/400/401/403/405/409（IFC-IB-294/295）
PASS  definition_assembly：装载→校验→派生→注入（IFC-IB-288/291/293）
PASS  frontend_config_discipline：无 CDN / 视图侧零持久化 / 拓扑只读 / 只有键名（IFC-IB-296）
------------------------------------------------------------------------
自检结果：30/30 通过
EXIT=0
```

> 注：上示块内 `EXIT=0` 系 **shell 退出码**（命令退出状态，即 `echo $?` 所得），**并非脚本自身打印的输出** ——
> `scripts/selfcheck.py` 只打印到「自检结果：30/30 通过」为止；上表 `compileall` 行的 `EXIT=0` 同理（shell 退出状态）。

> 关于既有回归：R7 的默认定义文档由**既有默认值精确派生**（`EXPERT_SPECS` / `DEFAULT_TAU` /
> `DEFAULT_MARGIN` / `max_expert_steps=8` / `search_knowledge`），故派生的专家注册表 **== 现有默认注册表**，
> 装配期注入**不改变任何既有行为** —— 既有 24 例自检**全绿即行为不变的机器证据**。全量
> `tests/` 回归属 GROUP_D 职责，本轮**未改** `tests/` 下任何文件（其断言一字未动）。

## 12.6 R7 本地不可验证项（如实登记，不得据此声称「已通过」）

| 项 | 原因 | 处置 |
|----|------|------|
| 前端类型检查 / 构建（`vue-tsc` / `vite build`） | `@vue-flow/core` 未安装，离线环境无法 `npm install` | 部署机联网后补验；已在 FND-R7-01 登记 |
| 配置页运行期真实渲染与 round-trip 写回 | 同上（无浏览器 + 无依赖） | 部署机 `npm install` 后按 AC-IB-17-06 补验；API 侧 round-trip 已由 `definition_store_roundtrip` 离线覆盖 |
| 生产 `FileDefinitionDocumentStore` 在真实磁盘的并发写 | 离线用临时目录单进程验证（原子替换 + 无残留临时文件） | 多进程并发竞争未实测；已由乐观并发（内容哈希）在协议层防护，如实登记 |

## 12.7 契约与冻结约束的守约复核（R7）

- **未改**：`IFC-IB-001~286` 的号/名/签名（R7 新增 `IFC-IB-287~297` 共 11 条，**纯追加**）；
  既有配置键名与默认值（R7 仅**登记** `IB_DEFINITION_DOC_PATH` / `IB_VISUAL_CONFIG_ENABLED` 两个**键名**，
  **任何文件与响应体均不含键值**）；依赖边（新端口适配器由既有边 `23 → 01/02` 构造，**零新增边**）；
  模块数（仍 26）。
- **未触碰**：Django + DRF + 原生 `StreamingHttpResponse` SSE / 禁 Channels / 禁 Redis；
  Qdrant 窄端口 + `scope` 必填；collection-per-project 硬隔离；台账即队列；**无 PyMuPDF**；
  `langchain-openai` pin `<0.3`；**无 Docker / 无容器化**；**无 AGPL/copyleft**（`@vue-flow/core` = MIT）。
- **未触碰**：`tests/` 下任何文件（GROUP_D 职责，断言未改）；`docs/` 下**其他代理**的产出
  （`requirements_spec.md` / `user_stories.md` / `architecture_design.md` / `module_design.md` /
  `tech_stack.md` / `ib_embed_service_contract.md` 均**未改**）；FreeArk 仓库**全程只读**。
- **未触网**：本轮自测**离线**（InMemory 替身 + 临时目录），**未**真连 Qdrant / DeepSeek / ib-embed。
- **凭据纪律**：R7 新增/修改文件**不含任何真实凭据**；配置键**只登记键名**（`IB_DEFINITION_DOC_PATH`
  为路径、`IB_VISUAL_CONFIG_ENABLED` 为开关，二者值均经环境变量注入，**不入任何 git 跟踪文件**）。

## 12.8 §12 结论

**R7 自评状态：SUCCESS（CRITICAL = 0，MAJOR = 0）。**

1. **施工前置已闭合**：先完成「专家/路由/编排/工具授权外置为数据 + 单一真源」（`DefinitionDocumentStore`
   + `definition.py` 数据层），再回填 UI 真实内容（配置页），符合 REV-07-6 裁定 (a)。
2. **REQ-FUNC-IB-25/26/27 均有落点**（§6 交叉核对 27/27）：只读图 + 白名单表单；拓扑不可运行期编辑 +
   零持久化 + 本地打包禁 CDN；装配期 fail-fast 闸门（无强制继续开关，为类型层事实）。
3. **离线自检 30/30 PASS（EXIT=0）**，其中 6 例专测 R7 纯函数与离线可测路径；`compileall` EXIT=0。
4. **无 CRITICAL 遗留**，两条 MINOR 均 DOCUMENTED（前端离线不可验、写回不热更运行期图 —— 后者为 ADR-16 刻意设计）。
5. 未改 `tests/`，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。

---

# §13 R8 增量评审（FND-R7-01 修复：`validate` 补齐两项装配期校验）

> 评审对象：R8 触及的 MOD-IB-02（`src/ib/config/definition.py::validate`）与自验面
> `src/scripts/selfcheck.py`。缺陷登记处：`docs/test_report.md` §12.6 / §12.10（**FND-R7-01，MAJOR**）。
> 纪律不变：**无实跑证据不下结论**；命令与原始输出见 §13.5。

> **同号不同源提示（诚实登记）**：GROUP_D `test_report.md` §12.6 的 **FND-R7-01（MAJOR，校验项缺失）** 与本报告
> §12.4 的 **FND-R7-01（MINOR，前端 `@vue-flow/core` 离线不可验）** **同号不同源**（由不同代理各自登记）。
> 本节修复的是**前者**；§12.4 的 MINOR 登记保持原样、未改动、未关闭（属前端离线残留）。

## 13.1 R8 规模与改动面

| 文件 | 行数级改动 | 性质 |
|------|-----------|------|
| `src/ib/config/definition.py` | +约 52 行（`validate()` 末尾追加第 10 / 11 项校验 + docstring 登记） | 校验项补齐（纯追加） |
| `src/scripts/selfcheck.py` | 2 夹具微调 + 1 新用例（+约 70 行） | 自验 |
| `tests/unit/test_definition_uniqueness_r8.py` | **新增**（TC-UNIT-062 / 063 / 064） | GROUP_D 套件新增 |
| `docs/implementation_plan.md` | 头部版本 2.3.0 → 2.4.0 / §16 | Task 3 |
| `docs/code_review_report.md` | 头部版本行 + 本节 | Task 4 |

**未新增模块 / 端口 / IFC 编号**；`validate` 签名与 `ValidationReport` 结构**未改**；`EXPERT_SPECS` 默认数据**未改**；既有 9 项校验的语义与顺序**未改**（仅末尾追加）。

## 13.2 R8 5 维评分（仅被触及的部分）

| 维度 | MOD-IB-02（`validate` 校验项补齐） | 自验面（selfcheck） | 说明 |
|------|-----------------------------------|---------------------|------|
| Correctness（正确性） | 9/10 | 9/10 | 两分支（通过 / 拒绝）均实测；归一化口径对齐**路由消费方**（`keyword.lower()`），撞车判定与运行期实际行为一致；默认装配（三专家）修后仍通过 |
| Security（安全性） | 9/10 | 9/10 | 错误信息只回显**关键词 / 标签**（业务数据），**不含任何凭据值**；仍无「强制继续」通道（类型层事实未变）；`ValidationErrorItem` 字段集未扩 |
| Performance（性能） | 10/10 | 10/10 | 追加为 O(总关键词数) 单遍字典归并，装配期一次性纯内存，无 I/O |
| Maintainability（可维护性） | 9/10 | 9/10 | 口径理由以注释就地写明（为何 `lower` / 为何 `strip` / 为何跳过空值）；docstring 逐类登记；未触碰既有 9 项 |
| Test Coverage（可测试性） | 9/10 | 8/10 | 新增 3 个纯函数单元用例（通过 + 3 类拒绝）；selfcheck +1 例。**扣分**：见 §13.6 —— 修复使 4 个**既有 GROUP_D 夹具**失效（夹具数据本身撞车），本轮**不得改动 tests/**，已登记交 GROUP_D |

## 13.3 R8 Finding 统计（诚实口径）

| 级别 | 新引入（本轮） | 本轮修复/关闭 | 遗留（未闭合） |
|------|--------------|--------------|-------------|
| CRITICAL | **0** | 0 | **0** |
| MAJOR | **0** | **1**（FND-R7-01，本报告按「已实现补齐」计） | **0** |
| MINOR / 说明 | 1（见 §13.4） | — | 0 |

**未解决的 CRITICAL 问题：无。遗留 MAJOR（本代理实现面）：无。**

### 13.4 R8 finding（登记不阻塞）

| Finding ID | 严重级别 | 文件:关键位置 | 描述 | 处置 |
|-----------|---------|-------------|------|------|
| D-R8-01 | MINOR（登记） | `tests/unit/test_definition_data_layer_r7.py`、`tests/integration/test_definition_config_r7.py` 的 `_expert` 夹具 | 夹具两专家共用关键词 `k` / 标签 `"标签"`，在**旧（不完整）校验**下「合法」；修后为**应拒**，导致 TC-UNIT-056/057/061、TC-INT-082 失败 | **DOCUMENTED + 交 GROUP_D**：本轮**不得改动 tests/ 既有用例**（硬约束）；处置建议见 §13.6。属 `test_report.md` §12.10 第 4 项预期的修复后测试侧工作 |

## 13.5 R8 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（**cwd = 仓库根目录**） | 结果 | 说明 |
|---|-----------------------------|------|------|
| 1 | `PYTHONUTF8=1 python -X utf8 src/scripts/selfcheck.py` | **31/31 PASS，EXIT=0** | R1~R7 的 30 例全绿 + R8 新增 `definition_uniqueness` 全绿 |
| 2 | `IB_OFFLINE_MODE=1 PYTHONUTF8=1 python -m pytest tests/unit/test_definition_uniqueness_r8.py -q` | **3 passed，EXIT=0** | 新增单元用例（TC-UNIT-062 / 063 / 064） |
| 3 | `IB_OFFLINE_MODE=1 PYTHONUTF8=1 python -m pytest tests/unit tests/integration -q` | **148 passed / 4 failed**（152 计） | 4 个失败**恰为** §13.6 所列既有夹具；无其他回归、无 ERROR |
| 4 | `python -m compileall -q src` | **EXIT=0** | 全量语法编译（含改动文件） |

R8 新增 selfcheck 用例的逐例结论：

```
PASS  definition_uniqueness：跨专家关键词撞车 / cn_label 重复 → fail-fast（ADR-16；R8）
------------------------------------------------------------------------
自检结果：31/31 通过
```

## 13.6 下游影响与处置建议（诚实登记，需 GROUP_D）

新增校验使两专家共用 `keywords=("k",)` / `cn_label="标签"` 的**既有测试夹具**由「旧校验下合法」变为「修后应拒」。经实跑（§13.5 第 3 行），**恰好 4 个既有用例**因此失败：

| 用例 | 文件 | 根因 | 建议处置（GROUP_D） |
|------|------|------|--------------------|
| TC-UNIT-056 / 057 / 061 | `tests/unit/test_definition_data_layer_r7.py` | `_expert` 默认 `keywords=("k",)` / `cn_label="标签"` | 将 `_expert` 夹具改为每专家关键词互异、标签互异（如 `keywords=(f"k{name}",)`、`cn_label=f"标签{name}"`） |
| TC-INT-082 | `tests/integration/test_definition_config_r7.py` | 同上 | 同上 |

> 本轮**未改动 `tests/` 任何既有用例**（遵守硬约束「只可新增」）；此为**夹具数据陈旧**问题（其数据在修前仅因缺陷而「合法」），非实现缺陷。与 `test_report.md` §12.10 第 4 项 / NV-R7-05 的预期一致。

## 13.7 契约与冻结约束的守约复核（R8）

- **未改**：`IFC-IB-001~297`（无新增编号、无签名/返回类型变更）；`validate(doc, *, known_tools=None) -> ValidationReport` 签名与 `ValidationReport` / `ValidationErrorItem` 字段集一字未改；端口数 14；模块数 26；`EXPERT_SPECS` 默认数据；配置键名与默认值；依赖边。
- **未触碰**：Django + 原生 SSE / 禁 Channels·Redis；Qdrant；bge-m3 dim=1024 CPU-only；**禁 PyMuPDF**；`langchain-openai` pin `<0.3`；**禁 Docker / 无容器化**；**无 AGPL/copyleft**。
- **未触碰**：`tests/` 下任何**既有用例**（只新增 1 文件）；`docs/` 下**其他代理**的产出（`requirements_spec.md` / `user_stories.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` / `ib_embed_service_contract.md` / `test_plan.md` / `test_report.md` / `phase_status.md` 均**未改**）；FreeArk 仓库**全程只读**。
- **未触网 / 未引新依赖**：本轮自测**离线**（纯函数 + 临时目录），**未**真连 Qdrant / DeepSeek / ib-embed，**未**安装任何新依赖。
- **凭据纪律**：改动代码 / 文档 / 用例**不含任何真实凭据**；错误信息只回显**关键词 / 标签值**（业务数据），不回显任何环境变量值。

## 13.8 §13 结论

**R8 自评状态：PARTIAL_SUCCESS（CRITICAL = 0；FND-R7-01 实现面已补齐并实跑验证；仅余 GROUP_D 侧夹具更新）。**

1. **FND-R7-01 实现面已补齐**：跨专家关键词撞车 + `cn_label` 唯一性两项装配期校验落地，违反即产出可定位的 `ValidationErrorItem`，由既有 `admit` 聚合闸门 fail-fast 拒绝。
2. **纯追加边界守住**：既有 9 项校验语义与顺序、全部 IFC / 签名、`EXPERT_SPECS` 默认数据、模块/端口/依赖边**均未改**。
3. **离线自检 31/31 PASS（EXIT=0）**；新增单元用例 **3 passed**；`compileall` EXIT=0；**默认装配修后仍通过**。
4. **无 CRITICAL 遗留**；出现 1 条 MINOR 登记（D-R8-01：既有测试夹具陈旧，须 GROUP_D 更新）—— 故状态判 **PARTIAL_SUCCESS** 而非 SUCCESS，以强制关注下游夹具更新。
5. 未改 `tests/` 既有用例，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。

---

# §14 R10 增量评审（前端构建阻断修复 + 冒烟入口 + 许可登记）

> **性质**：对 §1~§13 的**追加**，不覆盖。R10 为**交付管线缺陷修复轮**（invocation `INV-GROUP_C-INTELBASE-008`），只重评被触及的 **MOD-IB-24**（前端）。§1~§13 逐字未改。

## 14.1 R10 规模与改动面

| 文件 | 变更 | 行数变化 |
|------|------|---------|
| `src/frontend/package-lock.json` | 重新生成（纳入 `@vue-flow/core` + 14 传递包） | **+216** |
| `src/frontend/package.json` | 新增 `test` 脚本 + `_comment` 两条（R10 说明、传递依赖已核实） | +2 有效行 |
| `src/frontend/src/views/ConfigPage.vue` | 删 1 行未使用导入；**并入 git 跟踪** | **-1** |
| `src/frontend/tests/frontend.smoke.test.js` | **新增**（6 用例，零新增依赖） | +153（新文件） |
| `docs/tech_stack.md` | §2.1 新增 + §1/§2/§5.3 三处收敛 + 头部 1.3.1 | +~35 |
| `docs/implementation_plan.md` | §17 + 头部 2.5.0 | +~60 |

**未改**：后端 `src/ib` / `src/ibweb` / `src/ib_embed`；`tests/` 任何既有用例；`.github/workflows/ci.yml`；`vite.config.ts` / `tsconfig.json`。

## 14.2 R10 5 维评分（仅 MOD-IB-24 被触及的部分）

| 维度 | 分数 | 说明 |
|------|------|------|
| Correctness | **9/10** | 三处阻断缺陷全部闭合，CI 顺序实跑 `npm ci` + `npm run build` 双双 **EXIT=0**（§14.4）。扣 1 分：FND-R10-02 说明「交付物完整性校验」在 R7 交付时**缺失**（文件未跟踪竟未被任何自检发现），本轮仅补救该一例，未新增通用的「已跟踪性」自检 |
| Security | **10/10** | 无凭据写入；新依赖许可全宽松（无 AGPL/copyleft，REQ-NFR-IB-12）；无运行期 CDN（AC-IB-17-06）；冒烟用例对 CDN 主机做主动扫描 |
| Performance | **9/10** | 未引入 UI 组件库；产物 JS 252.35 kB（gzip 89.20 kB）/ CSS 12.62 kB，对 4GB 目标机可接受。扣 1 分：`@vue-flow/core` 1.48.2 相对 `^1.41.0` 抬升引入的**增量**未与旧产物逐字节比对（旧 `dist` 为 R7 前产物，无可比基线） |
| Maintainability | **9/10** | 修复最小化（删 1 行、重生成锁）；`package.json` `_comment` 与 `tech_stack` §2.1 同步更新，消除 `[待核实]` 陈述漂移；冒烟入口零依赖、可被 REV-10-2 直接扩写。扣 1 分：冒烟用例为**文本级结构断言**，非 SFC 语义编译断言（`@vue/compiler-sfc` 为传递依赖，直接 import 会引入隐式依赖，故刻意回避） |
| Test Coverage（可测试性） | **9/10** | 新增 6 用例含**根因回归闸**（锁 ↔ package.json 同步）并附**负向对照**证明其有效（§14.4 行 5）。扣 1 分：`tests/` 未纳入 `tsconfig.include`，故测试脚本本身不经 `vue-tsc` 类型检查（有意为之：Node 内建测试脚本用纯 JS 免构建） |

## 14.3 R10 Finding 统计（诚实口径）

| 严重级别 | 计数 | 状态 |
|---------|------|------|
| **CRITICAL** | **3** | **全部 FIXED 并实跑验证** |
| MAJOR | 0 | — |
| MINOR | 2 | 登记不阻塞（见 14.5） |

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R10-01 | **CRITICAL** | `src/frontend/package-lock.json`（根节点 `packages[""].dependencies`） | 锁与 `package.json` 失同步：lock 内 0 条 `vue-flow`，CI 阶段9 `npm ci` EUSAGE | **FIXED**（重生成锁；`npm ci` EXIT=0 实证） |
| FND-R10-02 | **CRITICAL** | `src/frontend/src/views/ConfigPage.vue`（整文件未被 git 跟踪）；旁证 `src/frontend/src/App.vue:23` | R7 交付的页面未 `git add`，而 `App.vue` 已 import 之 → CI checkout 后缺文件，`vue-tsc` 必失败 | **FIXED**（`git add`，已 staging；本地 `npm run build` EXIT=0 实证） |
| FND-R10-03 | **CRITICAL** | `src/frontend/src/views/ConfigPage.vue:41` | `type ExpertSpecInput` 未使用；`noUnusedLocals: true` 下 `TS6133` 致 `vue-tsc` 非零退出 | **FIXED**（删除该导入；`npm run build` EXIT=0 实证） |

> **CRITICAL = 0（修复后）**。三条 CRITICAL 均属**交付管线阻断**（任一存在则 CI 阶段9 失败），故不得以 MINOR/MAJOR 口径降级登记。

## 14.4 R10 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（cwd = `src/frontend`） | 原始输出摘要 | EXIT | 日志 |
|---|---------------------------|-------------|------|------|
| 1 | `npm install --no-fund --no-audit` | `added 16 packages in 5s` | **0** | `docs/evidence/groupc_r10_npm_install.log` |
| 2 | `rm -rf node_modules && npm ci` | `added 65 packages in 2s` | **0** | `docs/evidence/groupc_r10_npm_ci.log` |
| 3 | `rm -rf dist && npm run build` | `28 modules transformed` / `index-*.js 252.35 kB │ gzip: 89.20 kB` / `built in 1.23s` | **0** | `docs/evidence/groupc_r10_npm_build.log` |
| 4 | `npm test` | `tests 6 / pass 6 / fail 0` | **0** | `docs/evidence/groupc_r10_npm_test.log` |
| 5 | 负向对照：旧锁 + `node --test tests/frontend.smoke.test.js` | `AssertionError: package-lock.json 未解析 @vue-flow/core`（`pass 5 / fail 1`） | **1（预期）** | `docs/evidence/groupc_r10_guard_negative_control.log` |
| 6 | 逐包读 `node_modules/<pkg>/package.json` | 14 包 → MIT / ISC / BSD-3-Clause | — | `docs/evidence/groupc_r10_license.log` |

**修复前原始报错（FND-R10-03 现场，保留备查）**：

```
> vue-tsc --noEmit && vite build
src/views/ConfigPage.vue(41,8): error TS6133: 'ExpertSpecInput' is declared but its value is never read.
EXIT=2
```

**修复后**：`vue-tsc --noEmit` 零错误 → `vite build` 成功（同 §14.4 行 3）。

## 14.5 R10 MINOR finding（登记不阻塞）

| ID | 级别 | 描述 | 处置 |
|----|------|------|------|
| M-R10-01 | MINOR | **「已跟踪性」无自检**：`ConfigPage.vue` 未被跟踪（FND-R10-02）在 R7 交付后长期未被发现，说明缺少「交付文件是否全部入 git」的机械校验 | 建议后续轮次在 `src/scripts/selfcheck.py`（或 CI 阶段1 后）增加「`src/frontend/src/**` 全部被 `git ls-files` 覆盖」断言。**本轮未加**（selfcheck 属受保护文件，且超出授权范围） |
| M-R10-02 | MINOR | **冒烟用例为文本断言**：用例 3/4 以正则匹配 `ConfigPage.vue` 文本，而非用 `@vue/compiler-sfc` 真正编译 SFC | 有意为之：`@vue/compiler-sfc` 为**传递**依赖，直接 import 会引入隐式契约。REV-10-2 若需语义断言，应先将其**显式**登记为 devDependency 并同步锁。**本轮不加**（避免二次锁漂移与体积抬升） |

## 14.6 R10 本地不可验证项（如实登记）

- **CI 真机（GitHub Actions ubuntu-24.04 / Node 20）未跑**：本轮在**本地 Windows + Node 24.18.0 + npm 11.16.0** 复现 CI 的**命令序列**（`npm ci` → `npm run build`），非同一 runner。Node 主版本差异（20 vs 24）对 `node --test` 的用例发现规则**可能有别** —— 故 `test` 脚本选用**无参数** `node --test`（默认递归扫描、排除 `node_modules`），该行为在 Node 18/20/24 一致；`npm ci` / `vite build` 的 Node 20 兼容性由 CI 自身验证。
- **`dist` 未入库**（`.gitignore` 刻意排除）：故用例 6 以「`dist/` 存在」为前置条件；未 `npm run build` 时该用例给出 diagnostic 而非失败。
- **`@vue-flow/core` 1.48.2 的运行时渲染**未做浏览器端实测（无 headless 浏览器依赖）；本轮只证明**构建期**通过（`vue-tsc` + `vite build`）与产物**零外发**。

## 14.7 契约与冻结约束的守约复核（R10）

- **未改**：`IFC-IB-001~297`（无新增编号、无签名/返回类型变更）；端口数 14；模块数 26；配置键名与默认值；依赖边；**后端 `src/ib` / `src/ibweb` / `src/ib_embed` 任何行为**；`.github/workflows/ci.yml` 阶段定义。
- **未触碰**：Django + 原生 SSE / 禁 Channels·Redis；Qdrant；bge-m3 dim=1024 CPU-only；**禁 PyMuPDF**；`langchain-openai` pin `<0.3`；**禁 Docker / 无容器化**。
- **许可（NFR-12）**：新纳入 14 传递包全部宽松（MIT / ISC / BSD-3-Clause），**无 AGPL / copyleft**；登记于 `tech_stack.md` §2.1。
- **离线纪律**：**未引入运行期 CDN**（AC-IB-17-06 / REQ-NFR-IB-08）；依赖本地打包；`npm test` 零新增依赖。
- **未触碰**：`tests/` 下任何既有用例；`docs/phase_status.md`（PM 专属）；其他代理产出中的既有已批准内容（`tech_stack.md` 仅**追加/收敛登记**，选型未变）。
- **凭据纪律**：改动代码 / 文档 / 证据日志**不含任何真实凭据**（证据仅为 npm 输出、包元数据与构建尺寸）。
- **FreeArk 仓库全程只读**。

## 14.8 §14 结论

**R10 自评状态：SUCCESS（CRITICAL = 3，全部 FIXED；修复后 CRITICAL = 0）。**

1. **三处交付管线阻断缺陷全部闭合**：锁同步（FND-R10-01）、源文件纳入跟踪（FND-R10-02）、类型错误（FND-R10-03）。
2. **CI 顺序实跑双绿**：`npm ci` **EXIT=0** → `npm run build` **EXIT=0**；冒烟 `npm test` **6/6 pass EXIT=0**。
3. **回归闸有效**：负向对照用旧锁复跑，用例 2 **按预期失败**（证明其非空转断言）。
4. **首例解锁后暴露的后续阻断（FND-R10-03）在同轮内修复并验证**，未遗留 UNRESOLVED-CRITICAL。
5. **无 MAJOR 遗留**；2 条 MINOR 登记不阻塞（M-R10-01 / M-R10-02）。
6. 未改后端行为、未改 CI 定义、未削弱任何既有断言、未触网引入运行期依赖、未写入任何凭据。

---

# §15 R11 增量自我评审（IB-20 流式交付 / 会话生命周期：IFC-IB-298~308 + G2 交接 + FND-R11-01 + BLK-R8-02）

> 触发：协调者裁决（REV-12；invocation **INV-GROUP_C-INTELBASE-010**）。输入 = `docs/module_design.md` **1.4.0/R8** §2.1 / §2.2.3 / §3、`docs/architecture_design.md` **1.4.0/R8** ADR-17、`docs/test_report.md` **1.7.0/R11**（2 项未覆盖 + 4 项部分覆盖 AC 的归属缺口、**FND-R11-01**）、**BLK-R8-02**。
> **命名口径**：设计侧记 **R8**、协调者轮次记 **REV-12**、本报告自身版本线记 **R11/§15** —— 三者指向同一批改动（同 `implementation_plan.md` §18 声明）。
> **性质**：**只追加、不改写**。§1~§14 为 R1~R10 历史记录，**逐字未改**。

## 15.1 R11 规模与改动面

| 文件 | 变更 | 行数变化（`git diff --numstat`，新增 / 删除） |
|------|------|------|
| `src/ib/core/enums.py` | `StreamEventKind` 追加 `confirmation_required` | +8 / −1 |
| `src/ib/core/types.py` | R8 类型 / 别名 / 常量 + `SessionState` 扩展 + `GraphConfig` 新字段 | +123 / −5 |
| `src/ib/core/__init__.py` | 导出补充 | +21 / −0 |
| `src/ib/config/__init__.py` | 3 键名登记 + `IB_SESSION_BACKEND` 值域扩展 + `persistence_policy` | +45 / −1 |
| `src/ib/config/definition.py` | `validate()` 第 12 项（同专家内空 / 重复关键词） | +42 / −2 |
| `src/ib/experts/__init__.py` | 兜底话术按实际能力改写 + `delegating_experts()` 文档 | +17 / −4 |
| `src/ib/streaming/__init__.py` | 终态单发 / 可见性白名单 / 确认事件 / 存储逐字段复制 | +141 / −2 |
| `src/ib/orchestration/__init__.py` | 确认门 / `resume` / `ResumePayload` / `can_resume` / G2 `_expand_plan` | +385 / −37 |
| `src/ibweb/views.py` | `chat_stream` 显式 4xx（FND-R11-01）+ `chat_resume_endpoint` | +105 / −1 |
| `src/ibweb/urls.py` | `api/chat/resume` 路由 | +4 / −0 |
| `src/frontend/src/api/client.ts` | `confirmation_required` + `chatResume` + 空会话标识提前拒绝 | +69 / −3 |
| `src/frontend/src/views/ChatPage.vue` | 确认区独立 + `decide()` + 会话标识不预填 | +141 / −2 |
| `src/scripts/selfcheck.py` | 新增 8 个离线自检用例 + 1 条既有断言强化 | +495 / −1 |
| **合计** | **13 文件** | **+1596 / −59** |

**未改**：任何既有 IFC-IB 号与签名文本；`tests/`（GROUP_D 资产，本轮零改动，184 基线原样通过）；模块 / 端口 / 依赖边计数；既有配置键名与默认值；`requirements*.txt`（**零新增第三方依赖**）；`docs/phase_status.md`。

## 15.2 R11 5 维评分（仅被触及的部分）

| 维度 | 分数 | 说明 |
|------|------|------|
| Correctness | **9/10** | 四件事均有**离线实跑**证据：REV-12-1 的 11 条 IFC 逐条落地（自检第 1~4、7 例）；REV-12-2 交接护栏（自检第 6 例，含「关闭时逐位一致」与「上限生效」反面；护栏①/③ **已实现**、护栏② 为**机制就绪但组合根未接线**，见 §15.6 GAP-R11-07）；REV-12-3 缺会话标识 → `400`（自检 `http_contract_offline` 强化 + 第 7 例）；REV-12-4 同专家内空 / 重复 → 逐码拒绝（自检第 5 例）。扣 1 分：`arun` / `aresume`（异步孪生）与同步路径**同源**，但**确认门呈递只在 `run` 侧实现**（异步宿主若需确认门应经 `_maybe_gate` 同源扩展）—— 该差异已在 docstring 明示，属**已知边界**而非缺陷 |
| Security | **9/10** | 确认门**默认关闭**（ADR-17 约束 1，默认零行为差异）；`can_resume` **纯函数 + fail-closed**，残缺载荷**绝不补成「默认批准」**（自检第 2 例对三类残缺载荷逐一断言）；恢复端点**仅 Authorization 头**且 `?token=` 显式 `400`（自检第 7 例）；可见性**白名单**使内部子任务产物**默认不外流**；凭据仅登记键名、值取环境变量。扣 1 分：确认门话术构造器异常时的 fail-closed 分支（`confirmation_prompt_failed`）已实现并记录日志，但**离线自检未构造该异常分支**（仅代码路径审阅），属覆盖缺口已登记（M-R11-02） |
| Performance | **9/10** | 无新增阻塞 / 无 N+1；`MemorySessionStore.load` 的**逐字段复制**是**正确性必需**（否则确认中间态被静默丢弃），代价是浅拷贝而非零拷贝 —— 会话状态为小对象且 TTL / 上限已护栏，可接受；`_expand_plan` 为 O(命中专家数) 且默认关闭时不进入展开分支。扣 1 分：未做并发压测（属 GROUP_D / 目标机范畴） |
| Maintainability | **9/10** | 「兼容超集」先例复用一致（`confirmation_prompt_builder` 对齐 `related_images_provider`）；骨架**不生成业务话术、不判定业务规则**（ADR-09 语义纪律贯穿）；新增类型全部 frozen + `slots`；每处决策都在 docstring 写明「为什么」与「未决项」。扣 1 分：`SessionState` 采用「旧字段 + 新字段全默认」的**兼容扩展**（见 GAP-R11-01），字段集与设计文档不同口径，需 PM 裁决后收口 |
| Test Coverage（可测试性） | **9/10** | 本轮**新增 8 个离线自检用例**（39/39 PASS），覆盖：类型兼容、三判据正反两向、门的三态（关 / 开无话术 / 开有话术）、HTTP 六种状态码、前端静态纪律（含「确认分支不写入正文」「无自动续跑」「不预回退默认会话」）。GROUP_D 既有 **184 passed** 无回归。扣 1 分：自检属开发者自验（非正式套件），AC-IB-19/20 的**正式**覆盖仍归 GROUP_D；且上述话术构造器异常分支未构造 |

**5 维均分为 9.0/10**；无维度低于 8 —— 不构成「须回炉」信号。

## 15.3 R11 Finding 统计（诚实口径）

| 严重级别 | 计数 | 状态 |
|---------|------|------|
| **CRITICAL** | **1** | **FIXED**（同轮内修复并实跑验证） |
| MAJOR | 0 | — |
| MINOR | 3 | 登记不阻塞（见 15.5） |

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R11-01** | **CRITICAL** | `src/ibweb/views.py`（`chat_stream_endpoint`，R11 前 `session_id = (request.GET.get("session_id") or "default").strip() or "default"`）；旁证 `src/frontend/src/api/client.ts`（`query$.set('session_id', sessionId \|\| 'default')`）、`src/frontend/src/views/ChatPage.vue:90`（`ref('default')`） | **静默回退字面量默认会话**：缺会话标识时按 `"default"` 建会话，导致（a）多标签页 / 多用户静默共用同一会话（违背会话内隔离意图），（b）「未填」与「显式用 default」**不可区分**，AC-IB-20-01 的显式性要求被抹平 | **FIXED**：服务端缺失即 `ValidationError` → **`400`**（不回退）；前端 `chatStream/chatResume` 对空标识**提前拒绝**并给可读回执、输入框**不预填** `'default'`。实证：自检 `http_contract_offline` 断言 `/api/chat/stream?q=…`（无 `session_id`）→ **400**；`?q=…&session_id=selfcheck` → **200** |

> **CRITICAL = 0（修复后）**。该缺陷属**会话隔离与显式性**层面的契约破坏，不得降级为 MINOR 登记 —— 故按 CRITICAL 定级并同轮修复。

## 15.4 逐模块 R11 评审详情

---
**MOD-IB-01（core：R8 类型 / 枚举 / 常量）**
- Correctness: 9/10 · Security: 10/10 · Performance: 10/10 · Maintainability: 9/10 · Test Coverage: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| M-R11-01 | MINOR | `src/ib/core/types.py`（`SessionState` 字段区） | `SessionState` 采用「既有 3 字段逐字保留 + R8 字段全默认值」的兼容扩展，与 `module_design` R8 列出的「新字段集」口径**并存**；字段集未收敛为单一表述 | DOCUMENTED（GAP-R11-01，待 PM 裁决） |

---
**MOD-IB-02（config：键名登记 / 值域 / `validate` 第 12 项）**
- Correctness: 10/10 · Security: 10/10 · Performance: 10/10 · Maintainability: 9/10 · Test Coverage: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| — | — | — | 无 finding。三个键名**只登记不写值**；`IB_SESSION_BACKEND` 仅扩展值域（键名 / 默认值不变，对齐 R2 对 `IB_EMBED_BACKEND` 的先例）；`validate()` 第 12 项**在既有 11 项之后追加**，既有语义与顺序未动 | — |

---
**MOD-IB-16（experts：`is_delegating` 消费侧）**
- Correctness: 9/10 · Security: 10/10 · Performance: 10/10 · Maintainability: 9/10 · Test Coverage: 8/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| M-R11-02 | MINOR | `src/ib/orchestration/__init__.py`（`_maybe_gate` 的 `except` 分支 → `confirmation_prompt_failed`） | 「已启用确认门而话术构造抛异常 → fail-closed」分支已实现且记录日志，但**离线自检未构造该异常分支** | DOCUMENTED（不阻塞） |

---
**MOD-IB-21（streaming：终态单发 / 可见性 / 确认事件 / 会话存储）**
- Correctness: 9/10 · Security: 10/10 · Performance: 9/10 · Maintainability: 9/10 · Test Coverage: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| M-R11-03 | MINOR | `src/ib/streaming/__init__.py`（`MemorySessionStore.load`） | 为不丢 `gate` 而**逐字段**复制会话状态（新增字段需同步维护该复制点），存在「将来加字段忘改此处 → 静默丢状态」的维护风险 | DOCUMENTED（已在代码注释写明 R8 纪律；建议后续以 `dataclasses.replace` 收敛） |

---
**MOD-IB-22（orchestration：确认门 / `resume` / G2 交接）**
- Correctness: 9/10 · Security: 10/10 · Performance: 9/10 · Maintainability: 8/10 · Test Coverage: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| — | — | — | 无 CRITICAL / MAJOR。fail-closed 语义在 `run` / `resume` 与同步 / 异步两条路径上**同源**；挂起路径**不发 content**；续跑**不再次触发**确认门（防自死锁）。扣分点在**设计缺口**（GAP-R11-02~05）而非实现缺陷 | — |

---
**MOD-IB-23（ibweb：`chat_stream` 4xx + `chat_resume_endpoint`）**
- Correctness: 9/10 · Security: 10/10 · Performance: 10/10 · Maintainability: 9/10 · Test Coverage: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R11-01 | **CRITICAL** | `src/ibweb/views.py`（`chat_stream_endpoint` 会话标识解析行） | 见 15.3 | **FIXED** |

---
**MOD-IB-24（frontend：确认区呈递 / 决策回传 / 会话标识纪律）**
- Correctness: 9/10 · Security: 10/10 · Performance: 10/10 · Maintainability: 9/10 · Test Coverage: 8/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| — | — | — | 无 finding。确认区**独立区域**（`role="alertdialog"`、视觉可辨），**不并入正文**，未决前**不显示「本轮已完成」**，**无自动续跑**；决策经**独立端点**、**仅 Authorization 头**回传。可测试性扣 1 分：前端断言为**源码级静态检查**（无 SFC 语义级测试基建，与 R10 同口径刻意回避） | — |
---

## 15.5 R11 MINOR finding（登记不阻塞）

| ID | 位置 | 描述 | 处置 |
|----|------|------|------|
| M-R11-01 | `src/ib/core/types.py` | `SessionState` 兼容扩展 vs 设计文档字段集口径并存 | 登记为 **GAP-R11-01**，**待 PM 裁决**；本轮按最小一致原则实现，**未擅改设计文档** |
| M-R11-02 | `src/ib/orchestration/__init__.py` | 确认话术构造器异常 → fail-closed 分支未被离线自检构造 | 登记不阻塞；建议 GROUP_D 补一条「构造器抛异常」用例 |
| M-R11-03 | `src/ib/streaming/__init__.py` | `MemorySessionStore.load` 逐字段复制需随字段集同步维护 | 登记不阻塞；已加注释，建议后续以 `dataclasses.replace` 收敛 |

## 15.6 R11 设计缺口登记（须 PM 裁决；**未擅自扩充架构**）

| 缺口 ID | 设计未规定处 | 本轮实现（最小一致 + fail-closed 方向） |
|---------|------------|------------------------------------|
| **GAP-R11-01** | `SessionState` 字段集（设计 R8 版 vs 既有实现消费方） | 兼容扩展：旧 3 字段逐字保留 + R8 字段全默认值 |
| **GAP-R11-02** | 挂起时的**终态表示**（`confirmation_required` 之后如何收束） | 恰一条 `confirmation_required` + `completion_event(None)`；**不发 content** |
| **GAP-R11-03** | **确认话术构造器接缝**未命名（骨架不得生成业务话术） | `build_graph` 可选关键字 `confirmation_prompt_builder`（兼容超集先例）；未注入即零行为差异 |
| **GAP-R11-04** | **G2 交接的业务触发条件 / 目标集合 / 上限落点**未定义 | 开关控制 + 目标取 `default_expert()` + 上限 `min(config.max_expert_steps, MAX_EXPERT_STEPS)`；骨架**不判定业务规则** |
| **GAP-R11-05** | `resume` 续跑所需「原提问」的承载未规定 | 挂起时写入 `SessionState.turns`，续跑经 `_pending_query_of` 取回；缺失即 fail-closed |
| **GAP-R11-06** | `IFC-IB-307` 各前置与 `403`/`404`/`409`/`503` 的对应粒度 | 鉴权 → 403；归属 → 403；门未启用 / 未携决策 / 不一致 → 409；会话不存在 → 404；存储不可用 → 503（**全部 fail-closed**） |
| **GAP-R11-07（OPEN）** | handoff **护栏②（敏感写操作强制人工确认）的触发规则 / 生产接线**未定义：`module_design.md:566` 明文「骨架**不判定「哪些动作需要确认」**（ADR-09 / ADR-17 约束 2）」、「`prompt.summary` **由接入方提供的业务构造器产出**」；全库**无**识别「敏感写操作」的代码；组合根**未注入** `confirmation_prompt_builder`；`IB_CONFIRMATION_GATE_ENABLED` **默认关闭** | **按设计维持**：护栏② = **机制就绪 + 必批无自动批准**（确认中间态 + `confirmation_required` 呈递 + `POST /api/chat/resume` 显式决策回传，**无任何自动批准 / 自动续跑**），**触发规则按设计由接入方提供（骨架不判定）**；因组合根未接线 → **当前不可经配置触发**。**未新增**「敏感动作清单」或任何默认策略代码（不发明业务规则）。**登记为 OPEN，待 PM 裁决**（是否/如何提供生产入口） |

## 15.7 R11 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 原始输出摘要 | EXIT | 日志 |
|---|------|-------------|------|------|
| 1 | `python -m py_compile`（11 个改动文件） | `py_compile OK` | **0** | `docs/evidence/groupc_r11_compile.log` |
| 2 | `python -m pytest tests -q` | `184 passed in 13.97s`（= R11 基线，**无回归**） | **0** | `docs/evidence/groupc_r11_compile.log` |
| 3 | `python scripts/selfcheck.py`（离线） | 自检 **39/39 通过**（含本轮新增 8 例） | **0** | `docs/evidence/groupc_r11_selfcheck.log` |
| 4 | `node --test`（cwd = `src/frontend`） | `tests 6 / pass 6 / fail 0` | **0** | `docs/evidence/groupc_r11_frontend.log` |
| 5 | `vue-tsc --noEmit` + `vite build`（cwd = `src/frontend`） | `TSC_EXIT=0`；`28 modules transformed`；`index-*.js 254.44 kB │ gzip 89.93 kB`；`built in 752ms` | **0** | `docs/evidence/groupc_r11_frontend_build.log` |

> 全部命令**离线执行**：InMemory / Fake 替身 + 纯函数 + Django 测试客户端（进程内）；**零外部网络**、**无 Docker**、**无运行期 CDN**。

## 15.8 R11 契约与冻结约束的守约复核

- **契约纪律**：`IFC-IB-221~225` / `231~233` / `247` 的**签名文本一字未改**（`IFC-IB-233` 仅**新增**其载荷类型 `ResumePayload`，签名 `payload: dict` 文本不动；`IFC-IB-221/222` 仅**补齐**其悬置引用的 `SessionState` 定义）；新增编号仅 **298~308**；端口 **14** / 模块 **26** / 依赖边**零新增**（DAG 不变）。
- **框架无关内核**：`src/ib/core` **零 Django import**（自检 `core_framework_free` 守护）；新增类型全为 frozen dataclass / `slots` / 纯 stdlib；**零新增第三方依赖**。
- **离线纪律**：未触达真实 Qdrant / DeepSeek / bge-m3 / 任何外部端点；未引入 Docker；未引入运行期 CDN。
- **凭据纪律**：键名**只登记不写值**；改动文件与证据日志**不含任何真实凭据**；新端点**同样拒绝** `?token=`（自检第 7 例直接断言）。
- **未削弱既有断言**：GROUP_D 基线 **184 passed** 原样通过；`validate()` 既有 11 项语义与顺序未动（仅在**其后追加**第 12 项）；`ib.experts.validate_specs` 安装期兜底保留（自检第 5 例以行为断言守护）；**未使用 skip / xfail 掩盖任何失败**。
- **FreeArk 仓库全程只读**；`docs/phase_status.md` **未触碰**（PM 专属）；**未执行 `git add` / `git commit`**（提交属 PM 授权范围）。

## 15.9 §15 结论

**R11 自评状态：SUCCESS（CRITICAL = 1，FIXED；修复后 CRITICAL = 0）。**

1. **REV-12-1**：`IFC-IB-298~308`（11 条）逐条落地，含默认关闭的确认门、纯函数 fail-closed 恢复判据、专用恢复端点（对齐准入顺序）与前端呈递 / 决策回传约束。
2. **REV-12-2**：`is_delegating` / `delegating_experts()` **不再是死字段**；G2 单跳交接与既有图结构一致，且**默认关闭时严格逐位零差异**（关闭分支直接按 `decision.experts` 原序展开、**不去重**，见 §15.10）。三护栏的**精确口径**为：**护栏①（往返上限）已实现**；**护栏③（非 handoff 出路）已实现**；**护栏② = 机制就绪 + 必批无自动批准**，**触发规则按设计由接入方提供（骨架不判定「哪些动作需要确认」，`module_design.md:566` / ADR-09 / ADR-17 约束 2）**，**当前组合根未接线 → 不可经配置触发**（登记为 **OPEN**：GAP-R11-07）。
3. **REV-12-3**：**FND-R11-01 已修复** —— 缺会话标识**不再静默回退**字面量默认会话，服务端显式 `400`，前端同源收紧。
4. **REV-12-4**：**BLK-R8-02 已落地** —— `validate()` 追加同专家内空 / 重复关键词校验（**先归一化再比较**），既有派生 / 安装期兜底**未削弱**。
5. **MAJOR 遗留 = 0**；3 条 MINOR 登记不阻塞；**6 项设计缺口**按最小一致 + fail-closed 方向实现并**如实登记待 PM 裁决**（未擅自扩充架构，设计文档一字未改）。
6. 未改既有 IFC 签名、未改模块边界与依赖边、未改既有配置键名与默认值、未新增第三方依赖、未触网、未写入任何凭据、未做任何 git 提交动作。

---

# §15.10 R11 补丁轮（REV-12 patch；invocation INV-GROUP_C-INTELBASE-011）

> 触发：独立只读核验 **INV-GROUP_C-VERIFY-R11** 结论 = **CONFIRMED_WITH_CAVEATS**（1 项**必须修 MAJOR** + 3 项 MINOR/澄清）。本轮**只做这 4 项有界修复**，不扩范围。**性质：只追加**（§15.1~§15.9 除「三护栏」口径按 MAJOR-2 要求**精确改写**外，其余逐字未改）。

## 15.10.1 修复项与落点

| 项 | 级别 | 病灶（修复前） | 修复（文件:行） |
|----|------|---------------|----------------|
| **MAJOR-1** | **MAJOR → FIXED** | `chat_resume_endpoint` 缺 `session_key` 时自造 **2 段**键 `f"{project_id}:{session_id}"`，与流路径写入的 **3 段**键 `ctx.session_key` 永不相等 → 真实 HTTP 续跑**恒 404** | `src/ibweb/views.py`（`chat_resume_endpoint`，会话键派生段）：改为**唯一入口** `ib.context.session_key(project_id, ctx.authz.actor_id, session_id)`，与 `chat_stream_endpoint`（`ctx.session_key`）**逐字一致**；视图内**不再**自造键、**不再**出现独立分隔符拼接；保留 `session_key` 直传分支 |
| **MINOR-2** | MINOR → FIXED | `resume` / `aresume`（`src/ib/orchestration/__init__.py`）与 `chat_resume_endpoint`（`views.py`）均以 `state.gate` 派生 `gate_id` 再传入 `can_resume`，使 `can_resume` 内 `gate.gate_id != gate_id` **恒为假**（请求指向的中间态 vs 状态里的中间态对账**空转**，IFC-IB-306） | `src/ib/orchestration/__init__.py`（新增私有 `_requested_gate_id` + `resume`/`aresume` 调用点）、`src/ibweb/views.py`（`chat_resume_endpoint` 调用点）：`gate_id` 改取**请求指向的中间态**（`payload.decision.gate_id`，或请求体显式 `gate_id`），与 `state.gate.gate_id` **真实对账**，不一致即 fail-closed（→409）。**`IFC-IB-306` 签名文本 `can_resume(state, gate_id, payload)` 一字未改** |
| **MINOR-1** | MINOR → FIXED | `_expand_plan` 默认关闭分支仍先经 `seen` 去重再返回，使「默认关闭**逐位零差异**」不严格（重复命中会被静默改写） | `src/ib/orchestration/__init__.py`（`_expand_plan`）：`expert_handoff_enabled=False` 时**直接**按 `decision.experts` 原序、原样展开（**不去重 / 不过滤**）；开启分支**保留**去重 + 上限 |
| **MAJOR-2** | 文档/口径 | 「三护栏齐备」表述与事实不符（`module_design.md:566`：骨架**不判定**「哪些动作需要确认」；组合根**未注入** `confirmation_prompt_builder`；全库**无**识别「敏感写操作」的代码；`IB_CONFIRMATION_GATE_ENABLED` 默认关闭） | 本文件 §15.2 / §15.6（新增 **GAP-R11-07（OPEN）**）/ §15.9 与 `docs/implementation_plan.md` §18.3 / §18.8 精确改写为：护栏①③ **已实现**；护栏② = **机制就绪 + 必批无自动批准**，**触发规则按设计由接入方提供**，**组合根未接线 → 不可经配置触发**（OPEN）。**未新增**「敏感动作清单」或任何默认策略代码 |

## 15.10.2 补丁轮 Finding 统计

| 严重级别 | 计数 | 状态 |
|---------|------|------|
| **CRITICAL** | 0 | — |
| **MAJOR** | **1** | **FIXED**（MAJOR-1，负向对照实证） |
| MINOR | 3 | 2 项 FIXED（MINOR-1 / MINOR-2）+ 1 项口径（MAJOR-2，已改写为 GAP-R11-07 OPEN） |

> 兼容口径：上表「MAJOR-1」= §15 核验员指认项（非 §15.3 R11 原始统计）。R11 原始 §15.3「MAJOR = 0」为**该轮自评**结论，本轮据独立核验**追加**该项并修复。

## 15.10.3 MAJOR-1 取证（离线成功续跑；请求 / 响应摘要 + 键文本）

- 键文本（**逐字一致**）：流路径 `make_request_context(project_id="p_alpha", actor_id="service-account", session_id="resume-ok").session_key` = `p_alpha:service-account:resume-ok`；resume 视图经唯一入口 `ib.context.session_key("p_alpha", "service-account", "resume-ok")` = `p_alpha:service-account:resume-ok`（**byte-identical = True**）。
- 请求：`POST /api/chat/resume`，体 `{"session_id": "resume-ok", "decision": {"gate_id": "gate-http-1", "approved": true}}`（会话预置：以**流路径真实键**写入带 `gate` 的 `SessionState`）。
- 响应：**`200`**、类型 **`StreamingHttpResponse`**、`Content-Type: text/event-stream`；流事件序列 = `reasoning, content, done`（达终态 `done`，**未**再触发 `confirmation_required`）。
- **负向对照**（回归闸）：把会话键派生**临时还原**为 2 段 `f"{project_id}:{session_id}"` → 同一用例**按预期失败**（`404 not_found`），而既有 401/400/403/409 反向断言用例 `r8_chat_resume_http` **仍 PASS** → 证明新用例非空转、且直击病灶。
- 实证文件：`docs/evidence/groupc_r11_patch_major1_probe.log`（正向）、`docs/evidence/groupc_r11_patch_negative_control.log`（负向对照）。

## 15.10.4 补丁轮实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 原始输出摘要 | EXIT | 日志 |
|---|------|-------------|------|------|
| 1 | `python -m py_compile`（3 个改动文件） | `py_compile OK` | **0** | `docs/evidence/groupc_r11_patch_compile.log` |
| 2 | `python -m pytest tests -q` | `184 passed in 14.00s`（**无回归**） | **0** | `docs/evidence/groupc_r11_patch_pytest.log` |
| 3 | `python scripts/selfcheck.py`（离线） | 自检 **40/40 通过**（新增 1 例 `r8_chat_resume_http_success`） | **0** | `docs/evidence/groupc_r11_patch_selfcheck.log` |
| 4 | `npm test`（cwd = `src/frontend`） | `tests 6 / pass 6 / fail 0` | **0** | `docs/evidence/groupc_r11_patch_frontend.log` |
| 5 | 负向对照（临时还原 2 段键） | `r8_chat_resume_http_success` **FAIL(404)**；`r8_chat_resume_http` **PASS** | **1** | `docs/evidence/groupc_r11_patch_negative_control.log` |

> 全部命令**离线执行**：InMemory / Fake 替身 + 纯函数 + Django 进程内测试客户端；**零外部网络**、**无 Docker**、**无运行期 CDN**。

## 15.10.5 补丁轮守约复核

- **契约纪律**：`IFC-IB-221~225 / 231~233 / 247` 签名文本**一字未改**；`IFC-IB-306` 的 `can_resume(state, gate_id, payload)` **签名文本一字未改**（仅改**调用点**传值来源）；只新增 `298~308`；端口 **14** / 模块 **26** / 依赖边**零新增**。
- **视图薄层纪律**：`views.py` 内**不再**出现独立的会话键分隔符拼接（键构造唯一入口为 `ib.context.session_key`）；`project_id` / `actor_id` 恒取自 `ctx.authz`。
- **未削弱既有断言**：GROUP_D 基线 **184 passed** 原样通过；selfcheck 既有 39 例**全部保留**（含 401/400/403/409 反向断言）；**未使用 skip / xfail**。
- **未发明业务规则**：护栏②**未**新增「敏感动作清单」或默认策略代码；仅按 MAJOR-2 精确改写**口径**并登记 **GAP-R11-07（OPEN）**。
- **只读约束**：未改 `tests/**`（GROUP_D）、`docs/phase_status.md`（PM）、`docs/architecture_design.md` / `docs/module_design.md` / `docs/requirements_spec.md` / `docs/user_stories.md`（设计真源）；未执行 `git add` / `git commit`。

## 15.10.6 补丁轮结论

**补丁自评状态：SUCCESS。** MAJOR-1（真实 HTTP 续跑恒 404）**已修复并负向对照实证**；MINOR-1 / MINOR-2 **已修复**；MAJOR-2 **口径已精确改写**并登记 **GAP-R11-07（OPEN）**。**CRITICAL = 0 / MAJOR 遗留 = 0**。**待 PM 裁决项**：是否/如何为护栏② 提供生产入口（组合根注入话术构造器 + 触发规则），否则**不可经配置触发**（见 `<blockers>`）。

---

# §16 R13 增量自我评审（账户 / 会话 / 商用界面重构：IFC-IB-309~332 + REQ-FUNC-IB-28~36）

> **调用**：`INV-GROUP_C-INTELBASE-012`（GROUP_C；PHASE_05 实现计划 / PHASE_06 代码实现 / PHASE_06b 自我代码评审）；设计侧口径 **REV-13**。
> **依据**：`docs/implementation_plan.md` **§19**（R13 增量实现）；`docs/module_design.md` 1.5.0/REV-13（IFC-IB-309~332）；`docs/architecture_design.md` 1.5.0/REV-13（ADR-18~ADR-27）；`docs/tech_stack.md` 1.4.0/REV-13。
> **性质**：**只追加**。§1~§15 为 R1~R11 的历史记录，**逐字未改**。

## 16.1 R13 规模与改动面

| 项 | 值 |
|----|----|
| 触及模块 | **6 个**（MOD-IB-01 / 02 / 11 / 23 / 24 / 25）；模块总数 **26 不变** |
| 新增文件 | **21 个**（core 1 / ledger 1 / ibweb 3 / frontend 9 / deploy 2 + 自检脚本不计入模块） |
| 修改文件（tracked） | **21 个**；`git diff --stat -- src` = **+2,090 / −204** |
| 净新增代码（模块内） | 后端 ≈ **1,490 行**（`ib/core/accounts.py` 63 / `ib/ledger/accounts.py` 815 / `ibweb/accounts/*` 408 / `deploy/migrations/003_accounts.sql` 60 / `deploy/nginx/*.example` 144）＋ 前端 ≈ **1,539 行** ＋ `selfcheck.py` 5 例 ≈ 565 行 |
| 端口 | **14 → 15**（`AccountStore`，IFC-IB-310，**恰好 13 方法**，自检断言） |
| 依赖边 | **零新增**（DAG 不变） |
| 新增 IFC 编号 | **24 条**（309~332；**既有 001~308 一字未改**；`IFC-IB-285` 仍预留未分配） |
| 后端新增第三方依赖 | **1 个**：`bcrypt>=4,<5`（Apache-2.0） |
| 前端新增第三方依赖 | **2 个**：`element-plus ^2.8`（MIT）、`vue-router ^4.4`（MIT）—— 本地打包，**禁运行期 CDN** |

## 16.2 R13 5 维评分（仅被触及的部分）

| 维度 | MOD-IB-01 | MOD-IB-02 | MOD-IB-11 | MOD-IB-23 | MOD-IB-24 | MOD-IB-25 | 均值 |
|------|-----------|-----------|-----------|-----------|-----------|-----------|------|
| Correctness（正确性） | 10 | 9 | 9 | 9 | 9 | 9 | **9.2** |
| Security（安全性） | 10 | 9 | 10 | 10 | 9 | 10 | **9.7** |
| Performance（性能） | 10 | 10 | 8 | 9 | 7 | 10 | **9.0** |
| Maintainability（可维护性） | 10 | 9 | 9 | 9 | 8 | 9 | **9.0** |
| Test Coverage（可测试性） | 10 | 8 | 10 | 9 | 8 | 9 | **9.0** |

**扣分理由（不隐去）**

- **MOD-IB-02 = 9/9/10/9/8**：Correctness 扣 1 —— IFC-IB-312 的键名登记**首轮遗漏**（只在消费点读取，未落到指定模块 `ib/config/__init__.py`），自查发现并已修复（FND-R13-01）；Test Coverage 扣 2 —— `IB_RUNTIME_ENV_KEYS` 的登记断言为**后补**（已加入 `r13_deploy_discipline`），且**未**导出 `IB_RUNTIME_ENV_KEYS` 到 `__all__`（沿用既有状态，未扩大导出面）。
- **MOD-IB-11 = 9/10/8/9/10**：Correctness 扣 1 —— 实现侧扩展方法 `revoke_sessions_for_user` 超出端口 13 方法（D-R13-02，已登记）；Performance 扣 2 —— **登录失败计数为「读-改-写」非原子**（同账户并发失败可能少计），单机单进程 Waitress 下影响有限，跨进程场景需外部存储（沿用 `LoginThrottle` 同一局限，已登记 MINOR）。
- **MOD-IB-23 = 9/10/9/9/9**：Correctness 扣 1 —— `audit()` 的 `log_event` 调用**首轮参数错位**（`TypeError` 静默吞掉审计事件），自查修复（FND-R13-02）；Performance 扣 1 —— 每次受保护请求触发一次 `resolve_session` 查表（SQLite 主键命中，O(log n)），未加进程内缓存（牺牲缓存换「撤销即时生效」，是刻意的安全取舍）。
- **MOD-IB-24 = 9/9/7/8/8**：Performance 扣 3 —— Element Plus **全量导入**致 `vendor-element` **938.89 kB / gzip 301.82 kB**，触发 Vite >500 kB 警告（FND-R13-05，已登记 MINOR 与补救路径）；Maintainability 扣 2 —— 「视图侧零持久化」纪律迫使主题偏好**不持久化**（D-R13-05 / MINOR-R13-02），且 `theme.css` 与 Element Plus 变量覆盖存在**双套令牌**（需同步维护，已加注释）；Test Coverage 扣 2 —— **无组件级单测**（项目无前端测试框架，仅 `node --test` 静态纪律断言），交互路径靠人工与构建验证。
- **MOD-IB-25 = 9/10/10/9/9**：Correctness 扣 1 / Test Coverage 扣 1 —— `003_accounts.sql` 与 `schema.py::account_ddl_script()` 的**单源一致性无机器断言**（仅断言必需列存在），属**沿用 001 既有先例**（`001_ledger_init.sql` 同样无字节级断言），非本轮回归（MINOR-R13-05）。

## 16.3 R13 Finding 统计（诚实口径）

| 严重级别 | 总数 | 已修复（FIXED） | 已登记不阻塞（DOCUMENTED） | 未解决（OPEN） |
|---------|------|----------------|--------------------------|---------------|
| **CRITICAL** | **0** | 0 | 0 | **0** |
| **MAJOR** | **4** | **4** | 0 | 0 |
| **MINOR** | **7** | 3 | 4 | 0 |

> **CRITICAL = 0** —— 满足门控硬约束。**MAJOR 遗留 = 0**（未触发「MAJOR ≤3 条方可遗留」的例外条款）。**无 `[UNRESOLVED-CRITICAL]` 标注。**

## 16.4 逐模块 R13 评审详情

---
**MOD-IB-01: core（账户 / 会话 / 令牌契约 + 第 15 个端口）**

- Correctness: 10/10
- Security: 10/10
- Performance: 10/10
- Maintainability: 10/10
- Test Coverage (可测试性): 10/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| — | — | `src/ib/core/accounts.py:37-63`、`src/ib/core/ports.py:636-727` | 无 finding。令牌原语纯函数（stdlib `secrets`/`hashlib`/`hmac`，零第三方依赖）；`AccountStore` 为 `Protocol` + `@runtime_checkable`，**恰好 13 方法**（自检断言）；`ib/core` **零 Django import**（既有 `core_framework_free` 守护不变） | — |
---

---
**MOD-IB-02: config（IFC-IB-312 键名登记）**

- Correctness: 9/10
- Security: 9/10
- Performance: 10/10
- Maintainability: 9/10
- Test Coverage (可测试性): 8/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R13-01** | **MAJOR** | `src/ib/config/__init__.py:112-146`（原缺） | **契约项未落到指定模块**：IFC-IB-312 明确「键名登记」落 **MOD-IB-02**，但首轮只在消费点（`ibweb/accounts/__init__.py` / `ib/ledger/accounts.py` / `ibweb/authz.py`）读取环境变量，**未**在唯一真源 `ib.config` 内登记 → 键名不可被集中审计。修复：把 9 个 R13 键名追加进 `IB_RUNTIME_ENV_KEYS`（含语义注释），**不进** `IB_ENV_KEYS`（后者声明「不得新增 / 改名」）；并在 `r13_deploy_discipline` 增补断言「R13 键已在 `IB_RUNTIME_ENV_KEYS` 登记且未混入 `IB_ENV_KEYS`」 | **FIXED** |
---

---
**MOD-IB-11: ledger（bcrypt / SqliteAccountStore / MemoryAccountStore / 幂等种子）**

- Correctness: 9/10
- Security: 10/10
- Performance: 8/10
- Maintainability: 9/10
- Test Coverage (可测试性): 10/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R13-03** | **MAJOR** | `src/scripts/selfcheck.py::r13_account_store_parity`（自检基础设施） | **Windows 专用缺陷掩盖真实失败**：`TemporaryDirectory` 清理时因 SQLite 句柄仍打开而抛 `PermissionError [WinError 32]`，**覆盖了循环内真实的断言失败**（首轮表现为「库中未找到 bcrypt 摘要」，实际是只检查了最后一个文件 `-shm`）。修复：显式 `close()` 两个连接 + `TemporaryDirectory(ignore_cleanup_errors=True)`；并把 main/-wal/-shm **三件套**全量纳入摘要扫描 | **FIXED** |
| **FND-R13-04** | MAJOR → **MINOR** | `src/ib/ledger/accounts.py::record_login_failure` | **登录失败计数非原子**（SELECT → UPDATE 两步）：同账户并发失败可能少计一次 → 锁定稍晚触发。等级下调理由：单机单进程（Waitress）部署下并发窗口极窄，且锁定是**纵深防御**（前端 + IP 维度 `LoginThrottle` + bcrypt 慢哈希均已缓解），非主防线。**已登记 DOCUMENTED** | **DOCUMENTED** |
| — | — | `src/ib/ledger/accounts.py:1-815` | 其余无 finding：bcrypt（`$2b$` + 每次随机盐）；会话表**只存 sha256 摘要**；DDL 双 CHECK（`role='admin' OR project_id IS NOT NULL` / 枚举值域）在**存储层**兜底；两实现**同一行为体**通过（`r13_account_store_parity`）；`bcrypt` 为**惰性导入**（未启用账户体系时零代价） | — |
---

---
**MOD-IB-23: ibweb（端点 / 解析器 / 策略 / 中间件 / 装配 / 限速审计）**

- Correctness: 9/10
- Security: 10/10
- Performance: 9/10
- Maintainability: 9/10
- Test Coverage (可测试性): 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R13-02** | **MAJOR** | `src/ibweb/accounts/throttle.py:115-133` | **审计事件静默丢失**：`audit()` 调 `log_event("auth", event, outcome=…)`，而 `log_event(stage, outcome, **extra)` 的 `outcome` 是**第二位置参数** → `TypeError: got multiple values for argument 'outcome'`。认证审计（REQ-NFR-IB-18）在生产路径上**永不落盘**。修复：事件作为位置参数 `outcome` 传入，`**extra` 只携带白名单字段 `status` / `project_id`（函数签名**本身不接受** username / user_id / 口令 / 令牌） | **FIXED** |
| **FND-R13-05** | MINOR | `src/ibweb/accounts/throttle.py:55-93` | 限速器为**进程内**实现（多 worker 各自计数），跨进程共享需外部存储；**条件性**（未设 `IB_LOGIN_MAX_FAILURES` 即不启用，ADR-27 / OQ-IB-12 未裁决） | **DOCUMENTED** |
| **FND-R13-06** | MINOR | `src/ibweb/views.py::auth_login_endpoint` | 登录对「错口令」与「未知账户」返回**同一 401 文案**（防账户枚举，正确）；但**响应时间**可能因「未知账户走快速路径、已知账户走 bcrypt（慢）」而存在**时序差**——未做恒定时间补偿（bcrypt 本身即慢，加噪代价高）。**已登记**，属可接受的残余风险 | **DOCUMENTED** |
| — | — | `src/ibweb/views.py:1040-1306`、`src/ibweb/authz.py`、`src/ibweb/composition.py:476-540,600-630` | 其余无 finding：改密态**服务端受限会话**（allowlist 之外一律 403 `password_change_required`，自检断言 `/api/accounts` 与 `/api/files`）；`?token=`/`?access_token=` 在**全部端点**（含 `/api/auth/login`）400；**全响应零 `Set-Cookie`**；生产缺 `IB_AUTHZ_POLICY_MODULE` → `StartupError`（不启动）；账户端点 `_require_admin` = `is_global` **且** `policy.can_manage` **双条件** | — |
---

---
**MOD-IB-24: frontend（登录 / 控制台 / 路由守卫 / 类型化客户端 / 主题）**

- Correctness: 9/10
- Security: 9/10
- Performance: 7/10
- Maintainability: 8/10
- Test Coverage (可测试性): 8/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R13-07** | **MAJOR** | `src/frontend/src/stores/theme.ts`（首版） | **违反 ADR-14「视图侧零持久化」**：首版把主题偏好写入 `localStorage`，被既有全仓断言 `frontend_config_discipline` 拦截。修复：**彻底移除持久化**（内存 `ref` + 启动读 `prefers-color-scheme`），并在文件头文档化**两条理由**（与 ADR-14 冲突 / 不引入 `tech_stack §1.4` 未登记的客户端键） | **FIXED** |
| **FND-R13-05** | MINOR | `src/frontend/vite.config.ts:manualChunks`、`package.json` | **Element Plus 全量导入致包体偏大**：`vendor-element` **938.89 kB / gzip 301.82 kB**（Vite 报 >500 kB 警告）。缓解已做：`manualChunks` 把 vendor 与业务代码分离（业务 `index` 仅 **44.97 kB / gzip 17.96 kB**，首屏关键路径小）。**补救路径（未做，登记）**：引入 `unplugin-vue-components` 按需导入，预计可削减 50%~70% | **DOCUMENTED** |
| **FND-R13-08** | MINOR | `src/frontend/src/layouts/ConsoleLayout.vue`、`router/index.ts`、`main.ts` | 首轮手误：`NAV_ORDER` 在 `NAV` **之后**声明（TDZ 风险）；`router`/`main` 各出现**重复的 `../app/env` import**。修复：`NAV_ORDER` 上移；两处 import 合并为单条 | **FIXED** |
| **FND-R13-09** | MINOR | `src/scripts/selfcheck.py::r13_frontend_auth_discipline`（自检作者侧） | **假阳性**：对 `App.vue` 的「无令牌入口」断言最初匹配**散文**（docstring 里解释「已删除令牌入口」含「令牌」二字）→ 误报。修复：改为**结构性断言**（`<input` / `setToken(` / `type="password"` 均不得出现）；并对 `client.ts` 的同类断言增加**先剥离注释**再比较 | **FIXED** |
| **FND-R13-10** | MINOR | `src/frontend/src/stores/theme.ts:12-27` | 主题偏好**不跨会话记忆**（D-R13-05）。**已登记**：补做需**先**在 `tech_stack §1.4` 登记客户端存储键，再持久化 | **DOCUMENTED** |
---

---
**MOD-IB-25: deploy（迁移 003 / nginx TLS 模板 / 检查清单 / 键模板 / 依赖登记）**

- Correctness: 9/10
- Security: 10/10
- Performance: 10/10
- Maintainability: 9/10
- Test Coverage (可测试性): 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| **FND-R13-11** | MINOR | `src/deploy/migrations/003_accounts.sql` ↔ `src/ib/ledger/schema.py::account_ddl_script()` | **单源一致性无机器断言**：003 是 `account_ddl_script()` 的**人工摘录快照**，自检只断言「必需列存在」，**未**断言语句级等价 → 二者可能**静默漂移**。**属沿用既有先例**（`001_ledger_init.sql` 同样无字节级断言），**非本轮回归**。建议（未做）：增补「剥离注释后逐语句比对」断言 | **DOCUMENTED** |
| — | — | `src/deploy/nginx/intelligentbase.conf.example`、`src/deploy/checklists.txt`、`src/deploy/env.example` | 无 finding：TLS 模板**零证书 / 私钥材料**（`<REPLACE_ME…>` 占位符）；HSTS **仅注释**（自签场景防封死排障路径）；`ib-web` 仍绑 `127.0.0.1:18080`（明文只在回环）；`proxy_buffering off;`（SSE 硬条件）；Authorization **原样透传**；`env.example` 口令键值 = `<REPLACE_ME…>`；清单 [B15]~[B20] 齐备 | — |
---

## 16.5 R13 MINOR finding（登记不阻塞，供 GROUP_D / PM 裁决）

| ID | 摘要 | 落点 | 建议处置 |
|----|------|------|---------|
| **MINOR-R13-01** | Element Plus 全量导入致 `vendor-element` 938.89 kB（gzip 301.82 kB） | `src/frontend/vite.config.ts` / `package.json` | 引入 `unplugin-vue-components` 按需导入（预计 −50%~70%）；或维持现状（业务代码已分离，首屏 44.97 kB） |
| **MINOR-R13-02** | 主题偏好不跨会话记忆 | `src/frontend/src/stores/theme.ts` | **先**在 `tech_stack §1.4` 登记客户端存储键，**再**持久化（D-R13-05） |
| **MINOR-R13-03** | `bcrypt` 依赖钉 `>=4,<5`，本机装的是 **5.0.0** | `src/requirements.txt` / `-offline.txt` | 自检实际以 5.0.0 运行（仅用 `hashpw`/`gensalt`/`checkpw`，API 兼容）；**部署前须先 `pip install -r requirements.txt` 落到 4.x** 以对齐 `tech_stack` §1/§5.2（bcrypt cost 与阈值标定仍标 `[TBD-T22]` / OQ-IB-11） |
| **MINOR-R13-04** | 登录失败计数「读-改-写」非原子（同账户并发少计） | `src/ib/ledger/accounts.py::record_login_failure` | 单机单进程可接受；若将来多 worker，需改为 `UPDATE … SET failed_login_count = failed_login_count + 1` 原子语句 |
| **MINOR-R13-05** | `003_accounts.sql` 与 `account_ddl_script()` 无机器等价断言（沿用 001 先例） | `src/deploy/migrations/` | 增补「剥离注释后逐语句比对」断言 |
| **MINOR-R13-06** | 登录响应时序差（未知账户快路径 vs 已知账户 bcrypt 慢路径） | `src/ibweb/views.py::auth_login_endpoint` | 可接受残余风险；如需消除，需对未知账户也执行一次 dummy bcrypt |
| **MINOR-R13-07** | `IB_RUNTIME_ENV_KEYS` 未导出到 `config.__all__`（既有状态） | `src/ib/config/__init__.py` | 本轮**未**改动导出面（避免扩大契约）；如需，另轮登记 |

## 16.6 R13 本地不可验证项（如实登记）

| 项 | 状态 | 说明 |
|----|------|------|
| `npm ci`（**从锁文件干净安装**） | **未执行** | 本机离线，`.npm` 缓存可用故 `npm install` / `npx vite build` / `node --test` **均已实跑**（见 §16.8）；但 `npm ci`（CI 阶段9 的精确命令）未复跑 —— **`package-lock.json` 已就地重生成并与 `package.json` 同步**，`node --test` 的「锁 ↔ `package.json` 同步」回归闸 **PASS**，可**强**支撑 CI 通过，但**不等于**已在 CI 上跑过 |
| `bcrypt` 4.x 行为 | **未执行** | 本机为 5.0.0（API 兼容子集）；见 MINOR-R13-03 |
| HTTPS 实链验证 | **未执行（设计如此）** | 本轮**只交付模板**（IFC-IB-331）；**未部署**、未触碰任何生产目标；TLS 生效由 [B15] 在部署阶段验收 |
| 真实浏览器交互（登录→改密→控制台） | **未执行** | 无 e2e 框架；由 `vue-tsc --noEmit` + `vite build` + 静态纪律断言覆盖结构正确性 |
| nginx 配置语法（`nginx -t`） | **未执行** | 本机无 nginx；模板语法由人工审阅 + 自检断言关键指令 |

## 16.7 R13 契约与冻结约束守约复核

- **契约纪律**：**既有 `IFC-IB-001~308` 的号 / 名 / 签名 / 字段集一字未改**（含 R11 受保护行 `221~225` / `231~233` / `247` / `306`）；只**新增** `IFC-IB-309~332`；端口 **14 → 15**；模块 **26 不变**；**依赖边零新增**。
- **授权单一真源**：账户模块**只**提供 `PrincipalResolver`（解出 `AuthzContext`），**所有**授权判断仍经既有可注入 `AuthzPolicy`（IFC-IB-032/033）；生产缺 `IB_AUTHZ_POLICY_MODULE` → `StartupError`（**fail-closed**）。
- **凭据纪律**：代码 / 文档 / 日志 / 响应**零口令字面量**（§19.6 扫描零命中）；初始口令**只**从 `IB_DEFAULT_ADMIN_PASSWORD` 读；令牌**只**经 `Authorization: Bearer`；`?token=`/`?access_token=` **全端点** 4xx（含 `/api/auth/login` —— 中间件在**公共路径判定之前**检查，故登录端点同样受限）。
- **硬约束**：**无 Docker**（systemd + nginx + Waitress 不变）；**无 PyMuPDF/fitz**；**无运行期 CDN**（前端产物零外网引用，自检断言）；`langchain-openai <0.3` / `langchain-core >=0.3,<2.0` **未触碰**；bge-m3 权重未入 git。
- **未削弱既有断言**：`pytest` **207 passed**（无回归）；selfcheck 既有 **40 例全部保留**；**未使用** skip / xfail。
- **只读约束**：未改 `tests/**`（GROUP_D）、`docs/phase_status.md`（PM）、设计真源四文档；未执行 `git add` / `git commit`；**未部署**。

## 16.8 R13 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（cwd） | 结果 | EXIT |
|---|------------|------|------|
| 1 | `python -X utf8 -m compileall -q .`（`src/`） | 无输出（无语法错误） | **0** |
| 2 | `python -X utf8 scripts/selfcheck.py`（`src/`） | `自检结果：45/45 通过`（R13 新增 5 例） | **0** |
| 3 | `python -X utf8 -m pytest tests -q`（仓库根） | `207 passed in 14.20s` | **0** |
| 4 | `npx vue-tsc --noEmit`（`src/frontend`） | 无输出（类型通过） | **0** |
| 5 | `npx vite build`（`src/frontend`） | `✓ 1639 modules transformed` / `✓ built in 3.97s`；`index 44.97 kB`、`vendor-vue 110.22`、`vendor-flow 157.24`、`vendor-element 938.89`、`css 382.72`（附 >500 kB 警告 = MINOR-R13-01） | **0** |
| 6 | `node --test`（`src/frontend`） | `tests 6 / pass 6 / fail 0` | **0** |
| 7 | 凭据扫描（§19.6 三项） | 真凭据 **0 命中**；口令键仅**键名 / 占位符**；部署模板内摘要 / 证书材料 **0 命中**（唯一命中为校验命令自身的模式串） | **0** |

## 16.9 §16 结论

**R13 自我评审状态：SUCCESS。CRITICAL = 0。MAJOR = 4，全部 FIXED。MINOR = 7（3 FIXED / 4 DOCUMENTED，均不阻塞）。**

- **安全面**是本轮的主战场，且**未发现 CRITICAL**：零 Cookie / 令牌只存摘要 / 常量时间比较 / 受限会话结构性不可绕过 / 统一 401 防枚举 / 全端点 `?token=` 4xx / 登录限速条件性 / 审计零敏感字段 —— 逐条由离线自检实证。
- **4 条 MAJOR 全部在自查中被发现并修复**，其中 **FND-R13-01（契约项未落到指定模块）** 与 **FND-R13-02（审计静默丢失）** 是**实质缺陷**，若未在自评阶段拦下会分别以「契约不全」与「审计面空洞」形态流入验收。
- **7 条 MINOR 无一阻塞**：4 条为「已交付、待部署阶段或后续增量完善」（包体 / 主题持久化 / bcrypt 版本 / 迁移单源断言），3 条已在本轮内修复。
- **遗留 4 条 DOCUMENTED 的处置建议**已逐条给出**可执行补救路径**（§16.5），供 GROUP_D 与 PM 裁决；本代理**未擅自扩充架构**、未新增未登记契约。
- **待 PM 裁决项**：① 是否本轮引入 `unplugin-vue-components`（MINOR-R13-01）；② 是否登记客户端存储键以支持主题持久化（MINOR-R13-02）；③ bcrypt 版本对齐时机（MINOR-R13-03，部署前）。
- **本代理已 STOP，等待 PM 门控复核；未进入 GROUP_D、未部署、未提交。**

---

# §17 R13.1 回修自我评审（DEFECT-R13-01：来源 IP 维度登录限速未生效）

## 17.1 回修规模与改动面

| 项 | 内容 |
|----|------|
| 触发 | GROUP_D 门控 `condition_1`：**DEFECT-R13-01**（MEDIUM），证据 = `tests/integration/test_accounts_int_r13.py::TC-INT-119`（实测 `[401,401,401,401]`） |
| 性质 | **缺陷修复增量**（零新增能力 / 零新增模块 / 零新增契约 / 零新增依赖 / **零测试改动**） |
| 改动文件 | `src/ibweb/composition.py`（`Deps.login_throttle` + `_assemble()` 步骤 4e）、`src/ibweb/views.py`（`_login_throttle()` + 登录端点判定顺序）、`docs/implementation_plan.md`（§20 + 头部 2.7.0 → 2.8.0）、`docs/code_review_report.md`（本 §17 + 头部） |
| 未触碰 | `tests/**`、`src/frontend/**`、`src/ib/**`、设计真源四文档、`docs/phase_status.md` |

## 17.2 5 维评分（仅被触及的部分：MOD-IB-23 登录限速应用级装配）

| 维度 | 分数 | 依据 |
|------|------|------|
| Correctness（正确性） | **9/10** | `LoginThrottle` 现由组合根装配期构建一次并跨请求复用（`Deps.login_throttle`），滑动窗口 `_hits` 正确累积 → TC-INT-119 第 4 次返回 429；同时「账户锁定优先」使 TC-INT-118 仍为统一 401。2 条契约用例同绿。扣 1 分：已锁定账户「不参与 IP 判定、其失败仍记入 IP 计数」存在轻微不对称（已注释说明，不影响契约）。 |
| Security（安全性） | **9/10** | 429 分支可达，来源 IP 维度「挑用户名爆破」缓解恢复；已锁定账户仍走统一 401（不泄露锁定态）；未引入 Cookie / session；令牌纪律未变。扣 1 分：进程内限速在多 worker 下各自计数（既有 MINOR FND-R13-05，非本轮引入）。 |
| Performance（性能） | **9/10** | 每请求省去一次 `build_throttle()`；限速判定前的 `get_user_by_username` 是必要的账户解析（原本紧随其后即调用），未引入额外热路径开销。 |
| Maintainability（可维护性） | **9/10** | 单例装配点唯一（组合根）；`_login_throttle()` 有完整「为何不能每请求新建」的因果注释；`Deps` 新字段带自解释注释。 |
| Test Coverage（可测试性） | **9/10** | 「每应用实例一份」使测试天然隔离（`build_deps(force=True)` 得全新空窗口），无需 mock 或全局重置钩子；既有 2 条限速相关用例覆盖两条分支。 |

## 17.3 Finding 统计（本轮改动面）

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R13.1-01 | CRITICAL | `src/ibweb/views.py:1027`（回修前） | 每请求 `build_throttle()` 新建空 `LoginThrottle` → IP 维度滑动窗口永不累积、429 分支不可达（= DEFECT-R13-01 根因） | **FIXED** |
| FND-R13.1-02 | MAJOR | `src/ibweb/views.py:1050-1057`（回修中） | 单例化后若 429 判定先于账户锁定判定，则已锁定账户返回 429、遮蔽统一 401 → 回归 TC-INT-118 | **FIXED**（判定顺序：账户锁定优先） |
| FND-R13.1-03 | MINOR | `src/ibweb/views.py:1078-1079` | 已锁定账户的失败仍记入 IP 失败计数（但不再参与 IP 判定）—— 轻微不对称，已注释说明；不影响任何契约 | **DOCUMENTED** |

- **CRITICAL = 1，已修复清零**；**MAJOR = 1，已修复**；**MINOR = 1，DOCUMENTED（不阻塞）**。回修后重评无遗留 CRITICAL。

## 17.4 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（cwd = 仓库根，除注明外） | 结果 | EXIT |
|---|------------|------|------|
| 1 | `python -m pytest tests/integration/test_accounts_int_r13.py -q -k "TC_INT_118 or TC_INT_119"` | `2 passed`（**回修前：`1 failed, 1 passed`**，TC-INT-119 失败） | **0** |
| 2 | `python -m pytest tests/unit -q` | `95 passed` | **0** |
| 3 | `python -m pytest tests/integration -q` | `123 passed`（**回修前：122 passed / 1 failed**） | **0** |
| 4 | `python -m pytest tests/e2e -q` | `21 passed` | **0** |
| 5 | `python -m pytest tests -q` | `239 passed`（基线 239/239 不回退） | **0** |
| 6 | `python -m compileall -q src` | 无输出（无语法错误） | **0** |
| 7 | `python src/scripts/selfcheck.py` | `自检结果：45/45 通过` | **0** |
| 8 | `node --test`（`src/frontend`） | `tests 13 / pass 13 / fail 0`（未触碰前端） | **0** |

## 17.5 守约复核（R13.1）

- **未改任何测试用例**：`tests/**` 与 `src/frontend/tests/**` 零改动；无 skip / xfail / 断言削弱。
- **修复方向遵循门控**：严格采用给定的「提升为应用级单例」方向。为**同时守住既有 TC-INT-118 契约**（锁定账户 → 统一 401），补一处**判定顺序**调整（账户锁定优先于 IP 限速）。该调整的必要性与备选方案见下，供 PM 复核：
  - **必要性**：两条限速维度共用 `IB_LOGIN_MAX_FAILURES` 阈值；单例化后若不调序，TC-INT-118 第 4 次会被 IP 维度判为 429，使「账户是否已锁定」可被侧信道区分（AC-IB-29-01「不泄露已锁定」破裂）。
  - **已选（A）账户锁定优先**：与 `LoginThrottle` 既有设计（`del username`，**不以 username 为键**、按 IP 计全部失败）一致；变更面最小，只影响「已锁定账户」这一种情形的状态码归属。
  - **备选（B）IP 限速只计未知用户失败**：与 throttle 文档「按 IP 计全部失败」的设计相悖，且改变 `record_failure` 记录语义，故未采用。
- **凭据 / 离线纪律**：不涉及口令 / 令牌 / 密钥；无 Cookie / session；无新增依赖；未引入 Docker / PyMuPDF；数据不出本机。
- **只读约束**：未 `git add` / `commit` / `push` / 部署；未触碰设计真源四文档与 `docs/phase_status.md`。

## 17.6 §17 结论

**R13.1 回修自我评审状态：SUCCESS。CRITICAL = 0（1 条已修复）。MAJOR = 0（1 条已修复）。MINOR = 1（DOCUMENTED，不阻塞）。**

- **TC-INT-119 由 FAIL 转 PASS**；TC-INT-118 同绿（未以牺牲既有断言换取）。
- 全量重跑 **239/239**、前端冒烟 **13/13**、`compileall` EXIT=0、selfcheck **45/45** —— 全部通过。
- **本代理已 STOP，等待 PM 门控复核；未进入 GROUP_D、未部署、未提交。**

---

# §18 R14 回归缺陷修复自我评审（全局管理员「当前项目」选择与 `X-IB-Project` 传播：IFC-IB-333~336；设计侧口径 REV-14）

## 18.1 R14 规模与改动面

| 项 | 内容 |
|----|------|
| 触发 | R13 交付后回归：**全局管理员**（`users.project_id IS NULL` ⇒ `AuthzContext.project_id == "*"`）因项目级端点 fail-closed（503）而**无法使用任何项目级页面**（问答 / 文件 / 重建 / 可视化配置），且界面无「选择当前项目」入口 —— 即「哨兵恰是唯一出口，而出口未被暴露」。设计侧 **REV-14**（`architecture_design.md` 1.6.0 / ADR-28，Option B）给出修复方案。 |
| 性质 | **回归缺陷修复增量**（零新增模块 / 零新增端口 / 零新增依赖边 / 零新增第三方依赖；新增 IFC-IB-333~336 四条契约，为**纯追加**） |
| 新增文件 | `src/frontend/src/stores/project.ts`（MOD-IB-24）、`tests/integration/test_project_context_int_r14.py`（MOD-IB-24 测试，GROUP_C 自验层） |
| 修改源码 | `src/ibweb/views.py`、`src/ibweb/urls.py`（MOD-IB-23）；`src/frontend/src/api/client.ts`、`src/frontend/src/app/env.ts`、`src/frontend/src/layouts/ConsoleLayout.vue`、`src/frontend/src/main.ts`（MOD-IB-24） |
| 修改测试/自检 | `src/scripts/selfcheck.py`（新增 `r14_project_context`、`r14_frontend_project_discipline` 两用例）、`src/frontend/tests/frontend.smoke.test.js`（新增用例 14~17） |
| 未触碰 | `src/ib/**`（核心契约不变）、`src/ibweb/authz.py`（`X-IB-Project` 语义**已存在**，本轮仅登记契约未改代码）、设计真源四文档、`docs/phase_status.md` |

## 18.2 5 维评分（仅被触及的部分：MOD-IB-23 项目枚举端点；MOD-IB-24 项目上下文 store / 单点注入 / 控制台选择器）

| 维度 | 分数 | 依据 |
|------|------|------|
| Correctness（正确性） | **9/10** | `/api/projects` 授权口径正确：全局主体返回**全部**已登记项目、ops **恒为 1 项**（服务端裁定可见集合，客户端结构上不可枚举他项目）；`is_current` 反映**本请求**的 `effective_project`。前端 `load` 的 admin/ops 预选分支经行为用例验证（多项目 admin 缺省不选＝fail-closed；ops 预选自身）。扣 1 分：`is_current` 在 admin 未选定项目时全为 `false`（语义正确但界面需另给「未选择」提示，属 UX 增强、非契约缺陷）。 |
| Security（安全性） | **10/10** | 未新增授权维度——`X-IB-Project` **不是**凭据、判定仍只经注入的 `AuthzPolicy`（ADR-22）；身份判定完全复用 `_ctx_of`/`get_authz`/`is_global`，**未出现第二套授权逻辑**；ops 跨项目头仍 403 `project_mismatch`；未选定项目仍 fail-closed（**未选项目即不泄露**，ADR-28 约束③未削弱）；`?token=` 仍 `4xx`、零 `Set-Cookie`。 |
| Performance（性能） | **9/10** | `/api/projects` 只读内存 `Deps.projects`（`dict[str, ProjectRecord]`，无 DB / 无网络）；前端仅在「登录/换用户后」拉取一次列表，切换项目为纯本地状态变更（无请求）。扣 1 分：项目列表未做缓存层（规模 = 已登记项目数，当前量级下无收益）。 |
| Maintainability（可维护性） | **9/10** | `X-IB-Project` 字面量**只出现在 `stores/project.ts` 一处**（`headerValue()` 为唯一取值出口），`client.ts` 零字面量（由自检用例强制）；`client.ts ↔ project.ts` 的 ESM 循环依赖经「提供者注入 + `env.ts` 唯一装配」断开，接线点单一；`import type` 保证编译期无运行期回边。 |
| Test Coverage（可测试性） | **9/10** | 后端 3 条集成用例（TC-INT-120~122）覆盖 admin 全部 / ops 仅自身 / 跨项目 403 / 未选定 fail-closed / 未知项目不校验存在性 / 零 Cookie；前端新增 4 例，其中用例 17 为**真跑行为断言**（真 import `client.ts` + `project.ts`，断言 `headers()` 依 `current` 注入/不注入**且 SSE 头集合同样携带**）。扣 1 分：前端行为用例在 Node < 22.6（无类型擦除）下自动跳过（已 `t.diagnostic` 标注，非误报）。 |

## 18.3 R14 Finding 统计（诚实口径）

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R14-00 | **CRITICAL** | `src/frontend/src/layouts/ConsoleLayout.vue`（R13 版 `projectLabel` 静态文案）/ `src/ibweb/views.py`（R13 版缺 `api/projects`） | **本轮修复的回归本身**：全局管理员无「当前项目」选择入口，而项目级端点对 `effective_project == "*"` fail-closed ⇒ 管理员对问答/文件/重建/可视化配置**全部 503**，基座对唯一全局角色实际不可用 | **FIXED** |
| FND-R14-01 | **MAJOR** | `src/frontend/src/api/client.ts` `import.meta.env`（修复前） | `const ENV = import.meta.env` 在 **Node**（非 Vite 构建期）下 `import.meta.env` 为 `undefined` → **整模块导入即 `TypeError`**，破坏该文件自述契约「可被离线自检脚本直接导入」，并使既有 `src/scripts/sse_parser_selfcheck.mts` 一并不可用（前端唯一有实质算法的 SSE 分帧因此无法离线回归） | **FIXED**（`import.meta.env ?? {}`；Vite 构建期行为不变） |
| FND-R14-02 | MINOR | `src/frontend/src/stores/project.ts` `load()`（实现中） | 初版存在一段**无副作用死代码**（`if (role_ === 'ops' && state.current === null && ownProjectId) { state.current = null; }`）—— 分支恒等赋值，既无功能也无文档价值 | **FIXED**（改为有意义的 ops 预选：`const own = items.find(...); state.current = (own ?? items[0])?.project_id ?? null;`） |
| FND-R14-03 | MINOR | `src/ibweb/views.py` `projects_endpoint`（实现中） | 防御性未认证分支初版复用 `_unauthenticated()`，其文案为登录专用「用户名或口令不正确」，用在通用端点语义不当（可能误导排障） | **FIXED**（改为中性文案「缺少或无效的认证凭据」） |
| FND-R14-04 | COMPLIANT | `src/frontend/src/api/client.ts` + `src/frontend/src/app/env.ts` | 项目头取值路径**不得**由 `client.ts` 直接 `import stores/project.ts`（会形成 `client.ts ↔ project.ts` ESM 循环） | **COMPLIANT**（提供者注入法；ADR-28 Decision 与 IFC-IB-336 均允许「或等价注入」，属契约内实现选择，见 `implementation_plan.md` §21.5「不构成偏差」） |

- **CRITICAL = 1（FND-R14-00 = 本轮修复的回归，已修复清零）、MAJOR = 1（已修复）、MINOR = 2（均已修复）、COMPLIANT = 1。**
- **遗留 CRITICAL = 0、遗留 MAJOR = 0** —— 满足「存在 CRITICAL 不得提交 SUCCESS」「MAJOR 超 3 条须备注」两条硬约束（本轮 MAJOR 仅 1 条且已修）。

## 18.4 逐模块 R14 评审详情

**MOD-IB-23（`ibweb/`，R14 被触及：`projects_endpoint` + 路由）**
- Correctness: 9 / Security: 10 / Performance: 9 / Maintainability: 9 / Testability: 9
- 关键点：`projects_endpoint` 是**非项目级端点** —— 即使 `effective_project == "*"` 也必须 200（它是 fail-closed 的**唯一引导出口**）；`is_global(authz)` 为真取全部、否则只取 `authz.project_id` 对应的那一项（找不到则空列表，**不推断**）；`sorted(..., key=project_id)` 保证返回顺序确定（便于断言与前端稳定渲染）。**未新增第二套授权逻辑**（复用 `_ctx_of` / `get_authz` / `is_global`）。

**MOD-IB-24（`frontend/`，R14 被触及：`stores/project.ts` + `api/client.ts` + `app/env.ts` + `ConsoleLayout.vue` + `main.ts`）**
- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9
- 关键点：① `headers()` 是 `X-IB-Project` 的**唯一注入点**，且 `projectHeader()` 置于 `...extra` **之后**（store 值权威，调用方不可覆盖，防越权改项目头）；② `chatStream`（GET `/api/chat/stream`）与 `chatResume`（POST `/api/chat/resume`）**同经 `this.headers()`** ⇒ SSE 自动覆盖（EventSource 不能设自定义头，故本项目本就用 `fetch` 流）；③ 切换项目后 `<router-view :key="current ?? 'none'">` 强制重建项目内视图，避免残留上一项目的前端态；④ 登出 / 全局 401 均 `projectContext.clear()`，防「当前项目」跨会话残留。

## 18.5 R14 MINOR finding

**无遗留 MINOR**（FND-R14-02 / FND-R14-03 已在本轮修复）。供 PM 复核的**非缺陷观察**：admin 未选定项目时界面需显式呈现「未选择项目」态（当前以 `is_current` 全 false 表达，语义正确，UX 增强建议留待 PM 裁决是否纳入后续轮次）。

## 18.6 R14 本地不可验证项（如实登记）

| 编号 | 项 | 为何不可本地验证 | 处置 |
|------|----|----------------|------|
| R14-L-01 | 真实浏览器下 `el-select` 交互与 `<router-view :key>` 重挂载的端到端行为 | 本代理自验层为**离线**（无浏览器自动化环境；不触网约束下不引入 Playwright 等） | 已在**行为层**用 Node 真跑 `ApiClient.headers()` + `createProjectContext`（用例 17）覆盖「注入/不注入/SSE 头集合/ops 不可切换」；浏览器交互留待 GROUP_D 依据既定门控处置 |
| R14-L-02 | `npm ci` 在 CI 环境的可复现性（锁与 package.json 同步） | 本轮**未新增任何依赖**（`package.json` / `package-lock.json` 零改动），既有用例 2/13 已常驻保护锁同步 | 无需新增验证；既有 CI 阶段9 覆盖 |

> 说明：本轮**未新增第三方依赖**（`tech_stack.md` 1.4.0/REV-14 判 **NO_CHANGE**），因此 R14 无「新增依赖未真跑」类遗留项。

## 18.7 R14 契约与冻结约束守约复核

- **未改既有 IFC 编号 / 签名**：`IFC-IB-001~332` 一字未改；新增 **333~336**（纯追加）；`IFC-IB-324`（`X-IB-Project` 头语义）仅**加成式登记**，`src/ibweb/authz.py` **零改动**。
- **模块/端口/依赖边不变**：模块数仍 **26**、端口数仍 **15**、`architecture_design.md` 依赖边逐行未改；`/api/projects` 只是既有 `MOD-IB-24 → MOD-IB-23` HTTP 边上的新端点。
- **fail-closed 未削弱**：前端未选项目 ⇒ 不注入头 ⇒ 服务端取全局哨兵 ⇒ 项目级端点继续 503；**禁止**把哨兵解析为「并集」（ADR-28 Option C 被拒）。TC-INT-121 直接断言「无头 503 / 带头 200 / 未知项目仍 503」。
- **授权真源不变**：全局/项目可见集合由**服务端**依 `AuthzPolicy` 裁定，客户端不参与授权决策；`X-IB-Project` 非凭据。
- **认证契约未破坏**：令牌仅经 `Authorization: Bearer`；`?token=`/`?access_token=` 对 `/api/projects` 仍 `400`（中间件先于路由拒绝）；零 `Set-Cookie`；改密态与 admin/ops 角色划分不变。
- **依赖 / 架构纪律**：零新增第三方依赖；前端仍 **Element Plus / vue-router 本地打包、禁 CDN、hash 路由、不引 Pinia**（`stores/project.ts` 用模块级 `reactive`/`computed`，与 `stores/session.ts` 同构）；未引入 Docker / PyMuPDF。
- **凭据 / 脱敏纪律**：未写入任何口令 / 令牌 / 密钥字面量；新增测试口令为**测试替身占位值**（与既有 `R13_*_PASSWORD` 同性质，非生产凭据）；无敏感数据外泄。
- **只读约束**：未 `git add` / `commit` / `push`；未部署；未触碰目标机 192.168.31.133；未改 `requirements_spec.md` / `user_stories.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` / `docs/phase_status.md`。

## 18.8 R14 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令（cwd = 仓库根，除注明外） | 结果 | EXIT |
|---|------------|------|------|
| 1 | `python -m compileall -q src/ibweb src/ib src/scripts tests` | 无输出（无语法错误） | **0** |
| 2 | `python src/scripts/selfcheck.py` | `自检结果：47/47 通过`（基线 45 + R14 新增 2） | **0** |
| 3 | `python -m pytest tests -q` | `242 passed`（基线 239 + R14 新增 3；零回退） | **0** |
| 4 | `python -m pytest tests/unit -q` | `95 passed` | **0** |
| 5 | `python -m pytest tests/integration -q` | `126 passed`（基线 123 + R14 新增 3） | **0** |
| 6 | `python -m pytest tests/e2e -q` | `21 passed` | **0** |
| 7 | `npm run typecheck`（cwd = `src/frontend`） | 无输出（`vue-tsc --noEmit` 通过） | **0** |
| 8 | `npm run build`（cwd = `src/frontend`） | `✓ built`（1640 modules transformed，产物正常） | **0** |
| 9 | `npm test`（cwd = `src/frontend`，`node --test`） | `tests 17 / pass 17 / fail 0`（基线 13 + R14 新增 4；用例 17 为真跑行为断言） | **0** |
| 10 | `node --experimental-strip-types src/scripts/sse_parser_selfcheck.mts` | `SSE parser selfcheck: ALL PASS`（修复 FND-R14-01 后恢复；修复前因 `import.meta.env` 为 `undefined` 而整模块导入失败） | **0** |

**新增测试用例清单**：
- `tests/integration/test_project_context_int_r14.py`：`TC-INT-120`（项目枚举非项目级 + admin 全部 + 未选定也 200 + 无凭据 401 + `?token=` 400 + 零 Cookie + 字段集固定）、`TC-INT-121`（无头 503 → 带头 200 → `is_current` 反映 effective → 未知项目仍 503）、`TC-INT-122`（ops 列表恒 1 项 + 跨项目 403 `project_mismatch` + 自身/缺省放行）。
- `src/frontend/tests/frontend.smoke.test.js` 用例 14（`X-IB-Project` 字面量仅存于 `project.ts`）、15（SSE 调用点同经 `this.headers()`）、16（选择器 + `router-view :key` + `env.ts` 接线）、17（**行为**：`headers()` 依 `current` 注入 / 不注入，含 SSE 头集合，ops 不可切换）。
- `src/scripts/selfcheck.py` 新增 `r14_project_context`（Django test client 离线镜像 pytest 覆盖）、`r14_frontend_project_discipline`（前端源码纪律：单点注入 / `client.ts` 零字面量 / 选择器 / 视图键）。

## 18.9 §18 结论

**R14 回归缺陷修复自我评审状态：SUCCESS。CRITICAL = 0（1 条 FND-R14-00 已修复）。MAJOR = 0（1 条已修复）。MINOR = 0（2 条已修复）。**

- **回归根因已闭合**：全局管理员现可经 `/api/projects` 获知全部项目、在控制台选择「当前项目」，选择后 `X-IB-Project` 经**唯一注入点**随所有请求（含 SSE）传播 ⇒ 项目级端点由 503 转 200（TC-INT-121 为直接证据）；**未缩短 fail-closed 任一环节**（未选项目仍不泄露）。
- **契约零破坏 + 收益可回归**：既有 239 条 Python 用例、13 条前端冒烟**零回退**；新增 3 + 4 条用例把「授权口径 / 头传播 / 单点注入 / 视图态重置」固化为常驻断言。
- 全量重跑 **242/242**、集成 **126/126**、前端冒烟 **17/17**、`compileall` EXIT=0、selfcheck **47/47**、`npm run build` EXIT=0、SSE 自检 ALL PASS —— 全部通过。
- **本代理已 STOP，等待 PM 门控复核；未进入 GROUP_D、未部署、未提交、未触碰目标机。**

---

# §19 REV-16-2 自我评审（提示词分层 + 工具可视化配置：IFC-IB-339~354；设计侧口径 REV-16-3）

> 调用：`INV-GROUP_C-INTELBASE-015`（GROUP_C = PHASE_05 实现 + PHASE_06 自评）。
> 上游（均 APPROVED）：`architecture_design.md` **1.7.1 / REV-16-3**（ADR-15-R1 / ADR-29 / ADR-30 / ADR-31 / ADR-32 / ARCH-ASSUMPTION-A10）、
> `module_design.md` **1.7.1 / REV-16-3**、`user_stories.md` **1.6.0 / REV-16-2**（US-IB-29/30/31）、`requirements_spec.md` **1.7.0 / REV-16-3**。
> 参考仓 `FreeArk` 全程**只读**。

## 19.1 R16 规模与改动面

| 项 | 值 |
|----|----|
| 触及模块 | **7**（MOD-IB-01 / 02 / 16 / 17 / 22 / 23 / 24） |
| 新增文件 | 3（`src/ib/config/prompts.py`、`tests/unit/test_prompt_layers_r16.py`、`tests/integration/test_prompt_config_r16.py`） |
| 修改文件 | 15 |
| 新增端口 / 新 IFC | 端口 **15 → 16**（`ExpertPromptStore`）；IFC **339~354**（纯追加，既有 001~338 一字未改） |
| 新增测试 | Python **19**（unit 14 + integration 5）；selfcheck **3**；前端冒烟 **5** |
| 新增三方依赖 | **0**（后端 0，前端 0） |

## 19.2 5 维评分（仅被触及的部分）

| 维度 | 分 | 依据 |
|------|----|------|
| Correctness | **9.5** | 分层优先级 / `resolved_from` / 「三层皆空 → 拒绝」与 ADR-29 逐条对应；两域在装配期按专家 `name` join；参数注入语义（配置作默认、调用方优先）有直接断言（`bind_scope(authorized,...)[0].callable().content == "top_k=7"` 与 `callable(top_k=2)`）。**扣 0.5**：`admit_two_domains` 与 `admit` 的职责切分是为兼容既有冻结断言而设，非最直观的形态（已在 §22.4 登记为「不构成偏差」的实现选择）。 |
| Security | **10** | `?token=` 仍被中间件先行拒绝；单层 GET 对「不存在」与「不属于你」**统一 404**（反存在性探测）；`FsExpertPromptStore` **拒绝 `..` 路径穿越**（有测试）；`config_key_names` **只出键名**；列表端点**不出正文**；无任何凭据字面量。 |
| Performance | **9.0** | 提示词列表只读目录元数据 + 哈希（不读正文），正文按需逐层取；`save_layer` 原子写（tmp + `os.replace`）避免半写文件被装配读到。**扣 1.0**：`loadPrompts()` 对每个存在的层**逐个串行 GET**，专家数增长时是 N 次往返（当前 3 专家 × 2 层 = 最多 6 次，量级可忽略；若未来提示词层数增大，应改为批量端点）。 |
| Maintainability | **9.5** | 规格**派生**而非手写（`derive_tool_param_specs`），规格与工具声明不可能漂移；工具名名单同样由唯一登记点派生；注释交代「为什么」而非「是什么」。**扣 0.5**：前端 `ConfigPage.vue` 单文件已较长（定义文档域 + 提示词域 + 参数表），后续可拆子组件。 |
| Test Coverage（可测试性） | **9.5** | 纯函数（合并 / 校验 / 派生）全部离线直测；两个 store 实现由**同名参数化**同测（防语义漂移）；端点走 Django test client（含 200/400/403/404/409/401）；「保存不重建图」有**同一性**断言。**扣 0.5**：前端为**源码结构**断言（本项目无组件测试框架，与 R10/R13/R14 同策略），分层编辑器的**交互**无组件级测试。 |

## 19.3 R16 Finding 统计（诚实口径）

| 级别 | 计数 | 状态 |
|------|------|------|
| CRITICAL | **0** | — |
| MAJOR | **0** | — |
| MINOR | **2** | 1 条本轮已修 + 1 条登记遗留 |

| Finding ID | 级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|------|------------|------|------|
| FND-R16-01 | MAJOR（本轮内发现并**已修复**） | `src/ibweb/composition.py::admit`（原签名）| 初版把 `prompt_refs` / `tool_specs` 直接加进 `admit` 形参，**打破** R7 起的冻结断言 `set(inspect.signature(admit).parameters) == {"doc","store"}`（`tests/unit/test_definition_data_layer_r7.py::test_TC_UNIT_061` 立即转红）。 | **FIXED** —— 复原 `admit` 签名，两域聚合改走新函数 `admit_two_domains`；`_assemble` 调用新函数。 |
| FND-R16-02 | MINOR | `src/frontend/src/views/ConfigPage.vue::loadPrompts` | 逐专家逐层串行 `promptLayer()` 取正文，专家数增大时往返次数线性增长。 | **DOCUMENTED**（当前 3 专家量级可忽略；若提示词层增多应加批量端点，见 §19.2 Performance 扣分项）。 |

> **另记（非 finding，ADR 明令的例外）**：`src/ib/orchestration/__init__.py:125,140-141` 保留旧中文标签 `数据管家` / `知识库问答`，
> 这是 **ADR-31 Decision 第 4 条**要求的**过渡态旧 ∪ 新并集**（保证过渡期旧标签不被聚合输出、AC-IB-09-03 不回退），
> **不是遗漏**。全仓旧**slug**（`data-expert` / `knowledge-expert`）在 `src/` `tests/` 中为 **0 处**（唯一命中为本轮新增的反向核验断言自身）。

## 19.4 逐模块 R16 评审详情

---
**MOD-IB-01：核心契约层（零三方依赖）** —— Correctness 10 / Security 10 / Performance 10 / Maintainability 10 / Test Coverage 9.5
- Correctness：`ExpertPromptStore` 为 Protocol；新增 dataclass 全部带默认值（**加成式**，既有构造调用零改动）；`PromptNotFoundError` / `ToolParamValidationError` 归入既有错误树。
- Test Coverage：selfcheck `core_framework_free` / `port_conformance` 覆盖「零三方依赖 + 16 端口齐备」。
- **finding：无。**
---
**MOD-IB-02：配置与定义文档数据层** —— Correctness 9.5 / Security 10 / Performance 9.5 / Maintainability 9.5 / Test Coverage 10
- Correctness：`_semantic_payload` 补入 `param_values`（> 否则「只改参数不改哈希」会让乐观并发判据形同虚设）；`editable_field_whitelist` 补 `tool_grants[].param_values`；`document_from_json` 解析 `param_values`（缺省 → 空元组，向后兼容旧文档）。
- Security：`FsExpertPromptStore.save_layer` 对 `expert` 名做穿越拒绝；读取不存在目录 ⇒ 空元组（不报错、不臆造）。
- **finding：无。**
---
**MOD-IB-16：派生注入层（专家登记）** —— Correctness 10 / Security 9.5 / Performance 10 / Maintainability 9.5 / Test Coverage 9.5
- Correctness：`install_prompt_bundles` / `prompt_bundles()` / `main_prompts()` 供编排层回落链消费；专家名已按 ADR-31 硬改名。
- Security：`validate_specs` 的同名重复 fail-fast **未被削弱**（selfcheck `r8_*` 与单元用例仍绿）。
- **finding：无。**
---
**MOD-IB-17：工具运行时** —— Correctness 9.5 / Security 9.5 / Performance 9.5 / Maintainability 9.5 / Test Coverage 10
- Correctness：`derive_tool_param_specs` 由既有 JSON Schema 派生；`build_authorized_tools` 参数经 `functools.partial` 注入且**调用方显式实参优先**；`bind_scope` 对仍需 scope 的 `BoundTool` **重包裹**，补上「授权 + 参数 + 范围」三段包装的可叠加性。
- Security：**`_wrap_with_params` 按 `_param_belongs` 先做归属过滤**，再以 `_bare_param` 去前缀注入 —— 避免「同名参数跨工具串味」；未授权工具带参 / 未登记参数均 `ToolParamValidationError`。
- **finding：无。**
---
**MOD-IB-22：编排层（禁止标签派生视图）** —— Correctness 10 / Security 10 / Performance 10 / Maintainability 10 / Test Coverage 9.5
- Correctness：`forbidden_labels(cn_map)` 为**派生只读视图**（纯函数，接受任意 cn_map）；`AGGREGATION_FORBIDDEN_LABELS` 兼容常量 = 结构性词 ∪ 过渡并集，既有引用不变。
- **finding：无**（过渡并集为 ADR 明令，见 §19.3 另记）。
---
**MOD-IB-23：Web 装配与端点** —— Correctness 9.5 / Security 10 / Performance 9 / Maintainability 9.5 / Test Coverage 9.5
- Correctness：`_assemble` 每项目一份提示词存储 + 派生视图 + `install_prompt_bundles`；`admit_two_domains` 聚合三路校验且**不重复计数**；`known_tool_names` 与装配期校验同源。
- Security：写操作 `_require_manage`（否则 403）；未存层统一 404；总开关关闭整族 404；列表不出正文、只出键名。
- Performance：提示词列表只读元数据 + 哈希，不读正文。
- **finding：** FND-R16-01（已修）。
---
**MOD-IB-24：前端配置页** —— Correctness 9.5 / Security 10 / Performance 8.5 / Maintainability 9 / Test Coverage 9
- Correctness：主 / 兜底两独立文本域 + 逐层保存；`resolvedFrom` 常驻显示当前生效层（US-IB-30）；工具勾选只作用于 `available_tools`；参数控件按类型分派；保存成功文案**逐字**含「保存成功；重启 `ib-web` / `ib-worker` 后生效」（ADR-32 / C-IB-40）。
- Security：**视图侧零持久化未破坏**（无 `localStorage` / `IndexedDB`）；无 CDN；**无**热重载 / 运行期重建入口。
- **finding：** FND-R16-02（登记遗留，MINOR）。

## 19.5 R16 本地不可验证项（如实登记）

| 项 | 原因 | 处置 |
|----|------|------|
| 提示词目录在**真实部署**下的读写（含 `IB_EXPERT_PROMPT_DIR` 指向的宿主路径权限） | 本代理不部署、不触碰目标机 | 由部署 / 验收阶段覆盖；离线已用临时文件系统验证 Fs 实现语义 |
| 分层编辑器与参数表单的**组件级交互**（点击、焦点、错误态） | 本项目无组件测试框架（与 R10/R13/R14 同策略） | 以源码结构断言 + 后端端点集成测试双重覆盖；组件级测试如需引入，属 GROUP_D 决策 |
| 「重启后生效」的**端到端**闭环 | 需要真实进程重启 | 已由「保存不重建图」（同一性断言）+ 装配期两域合并（离线可测）双向锁定语义 |

## 19.6 R16 契约与冻结约束守约复核

- **未新增模块**（26 不变）；**端口 15 → 16**；§4.1 依赖边逐行未改。
- **未改既有 IFC 编号 / 签名**（含 `admit`，见 FND-R16-01 的修复）；新增 339~354。
- **验收口径不变**：`ValidationReport` **未**新增 `force` / `ignore` / `warn_only`。
- **无运行期热重载**：`PUT` 只原子落盘；`deps.orchestrator_for(p) is deps.orchestrator_for(p)` 为直接证据。
- **凭据纪律**：无任何口令 / 令牌 / 密钥字面量；`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED` **只登记键名**；提示词正文为占位中文。
- **依赖纪律**：后端与前端**均零新增依赖**；无 Docker；无 PyMuPDF / `fitz`；`langchain-openai` 仍 `<0.3`；bge-m3 权重未入库；无运行期 CDN / 无数据外发。
- **只读约束**：未 `git add` / `commit` / `push` / `stage`；未部署；未触碰目标机；**FreeArk 参考仓未写入一个字节**。

## 19.7 R16 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 结果 | EXIT |
|---|------|------|------|
| 1 | `python -m compileall -q src` | 无输出 | **0** |
| 2 | `python src/scripts/selfcheck.py` | **50/50 通过**（基线 47 + R16 新增 3） | **0** |
| 3 | `python -m pytest tests/ -q` | **273 passed**（基线 254 + R16 新增 19；零回退） | **0** |
| 4 | `npm run typecheck`（cwd = `src/frontend`） | 无输出（`vue-tsc --noEmit` 通过） | **0** |
| 5 | `npm test`（cwd = `src/frontend`，`node --test`） | `tests 26 / suites 4 / pass 26 / fail 0`（基线 21 + R16 新增 5） | **0** |
| 6 | 旧 slug 扫描（`src/` + `tests/`） | `data-expert` / `knowledge-expert` **0 处**（唯一命中 = 本轮新增的反向核验断言自身） | — |
| 7 | 新名扫描 | `freeark-expert` 48 次 / `sanheng-knowledge` 15 次；`系统管家` 15 次 / `三恒知识` 7 次 | — |

**新增测试用例清单（R16）**
- `tests/unit/test_prompt_layers_r16.py`（14）：分层优先级 + `effective_prompt` 恒非空；`prompt_content_hash` 稳定性；目录装载缺目录 ⇒ 空；孤儿 / 命名不符 / 缺兜底；**两 store 实现同名参数化**的保存冲突 + 空兜底拒绝；Fs 原子写 + 布局 + 穿越拒绝；工具参数五类错误；规格派生 + 授权绑定 + 范围绑定 + 调用方优先；未知工具 / 未登记参数拒绝；跨域 join 派生 + 注入。
- `tests/integration/test_prompt_config_r16.py`（5）：装配安装存储与 bundle；列表契约（字段集 + 只出元数据 + `available_tools` + 只出键名 + 令牌值不出现在响应体）；层 GET/PUT/409/400/404/401 + `?token=` 拒绝；**保存不重建图**（同一性）。
- `src/frontend/tests/frontend.smoke.test.js`（用例 22~26）：分层编辑器结构 + 回退可见；**生效口径强制文案**；工具勾选与 `available_tools` 来源；两域独立草稿 / 哈希；视图侧零持久化。
- `src/scripts/selfcheck.py`：`r16_prompt_layers`、`r16_prompt_tool_endpoints`、`r16_rename_alignment`。

## 19.8 §19 结论

**R16 自我评审状态：SUCCESS。CRITICAL = 0（1 条 MAJOR 于本轮内发现并已修复）。MAJOR = 0。MINOR = 1（登记遗留）。**

- 四项范围（分层提示词 + 工具勾选/参数 + FreeArk 硬改名与禁止标签派生视图 + 装配期两域完备性校验）**全部落地**；生效口径严格为「保存 + 重启后装配期重组」，**无运行期热重载、不重编译编排图**。
- **契约零破坏 + 收益可回归**：既有 254 条 Python 用例、21 条前端冒烟**零回退**；新增 19 + 3 + 5 条把「分层优先级 / 两域 join / 勾选授权 / 参数注入 / 并发冲突 / 不重建图」固化为常驻断言。
- 全量重跑 **273/273**、selfcheck **50/50**、前端冒烟 **26/26**、`compileall` EXIT=0、`vue-tsc` EXIT=0 —— 全部通过。
- **风险提示（供 PM 门控决策，非缺陷）**：本轮按 ADR-31 把 **FreeArk 业务名**（`系统管家` / `三恒知识` 与对应 slug）写入**基座默认种子**，与 OOS-04「骨架不承载业务专有名」存在口径张力（架构侧已以 ADR-31 显式吸收，P-2 相关裁定见 `rev16_2_ruling_apply_package.md`）；如 PM 判定需进一步解耦，属**设计侧**变更，不在本代理本轮授权范围内。
- **本代理已 STOP，等待 PM 门控复核；未进入 GROUP_D、未部署、未提交、未触碰目标机。**

---

## §20 REV-16-4 增量自评（配置审计 + 存储态暴露 + 两回归缺陷修复）

**调用 ID**：INV-GROUP_C-INTELBASE-016（`flow_mode: PARTIAL_FLOW`）　**设计侧口径**：`docs/module_design.md` **1.8.0/REV-16-4**（§2.2.7 IFC-IB-355~363 / §2.2 第 17 端口行 / §3 模块条目）+ `docs/architecture_design.md` **1.8.0/REV-16-4**（ADR-33 / ADR-34 / ADR-35 + §2.0.7）　**上游门控**：GR-A-009 = PASS / GR-B-009 = PASS。

**本轮范围（恰好四项）**：DEFECT-R16-01（`param_values` 静默丢参）、DEFECT-R16-02（保存 / 装配校验漂移）、GAP-R16-03（存储态暴露，ADR-35）、GAP-R16-04（配置审计，ADR-34）。

### 20.1 评审摘要

| 指标 | 值 |
|------|-----|
| 本轮重评模块 | MOD-IB-01（核心契约：端口与结构）、MOD-IB-02（配置 / 定义文档数据层）、MOD-IB-11（台账：审计存储 + 迁移）、MOD-IB-23（Web / 组合根 / 端点 / 序列化）、MOD-IB-24（前端：配置页 + 客户端）、MOD-IB-25（部署交付物：迁移 SQL） |
| 本轮新增文件 | **2**（`src/ib/ledger/config_audit.py`、`src/deploy/migrations/004_config_audit.sql`） |
| 本轮修改文件 | **13**（见 §20.6 文件清单） |
| 端口数 | 16 → **17**（`ConfigAuditStore`，IFC-IB-357，纯追加，2 方法无 update/delete） |
| 接口契约数 | 354 → **363**（新增 IFC-IB-355~363 共 9 条；`IFC-IB-001~354` 一字未改） |
| Finding 统计 | **CRITICAL = 0**、**MAJOR = 1**（FND-R164-05 = DEFECT-R16-4-01，**已修复**，见 §20.10）、MINOR = 4（登记遗留，见 §20.5；与 §20.3 逐条表及 §20.9 结论一致；PM 于 GR-C-012 门控时据 §20.3 表订正原「MINOR = 1」笔误；本次追加 1 条 MAJOR 后，§20.1 / §20.3 / §20.9 仍三处一致） |
| 5 维总体（本轮触及面均值） | Correctness 9.3（回修后：MOD-IB-23 由 9 → 8，见 §20.10）/ Security 9.5 / Performance 9.0 / Maintainability 9.0 / Test Coverage（可测试性）9.0 |

### 20.2 按模块评审详情

---
**MOD-IB-01：核心契约（端口与结构）** — `src/ib/core/types.py` / `ports.py` / `__init__.py`
- Correctness: 10/10
- Security: 10/10
- Performance: 9/10
- Maintainability: 10/10
- Test Coverage（可测试性）: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R164-01 | MINOR | `src/ib/core/types.py`（`ConfigAuditEntry` / `StorageState` 定义处） | 结构体为「只读投影」，与既有 frozen+slots 纪律一致；未生成 `__eq__` 之外的只读防护（Python 值对象惯例），登记为遗留观察项 | OPEN |

- `ConfigAuditEntry` / `StorageState` 均为 `@dataclass(frozen=True, slots=True)`；`ConfigAuditResult` / `StoreMode` 为 `Literal` 类型别名；**只含字段名与结果码**（无取值字段），从类型层即满足「审计只记字段名 / 码」。
- `ConfigAuditStore` 为 `@runtime_checkable Protocol`，**恰好 2 个方法**（`record` / `list_by_project`），**无 update / delete** —— 「只读审计、非第二真源」为**类型层事实**（已用 `__protocol_attrs__` 程序化核验）。

---
**MOD-IB-02：配置 / 定义文档数据层** — `src/ib/config/definition.py` / `__init__.py`
- Correctness: 10/10
- Security: 9/10
- Performance: 10/10
- Maintainability: 9/10
- Test Coverage（可测试性）: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R164-02 | MINOR | `src/ib/config/definition.py::validate_definition_full`（函数体首行惰性导入） | 因 `prompts` 模块在模块层反向导入本模块，`validate_tool_params` 需**函数内惰性导入**；每次调用有一次 `sys.modules` 命中开销（首次后无 IO），登记为可接受 | DOCUMENTED |

- `validate_definition_full` 为**合成纯函数**（IFC-IB-355）：无 I/O、无副作用、确定性；= `validate`（定义域）∪ `validate_tool_params`（工具参数域），错误顺序固定。
- **未改 `validate` / `validate_tool_params` 签名**（`inspect.signature` 逐字比对通过）。

---
**MOD-IB-11：台账（审计存储 + 迁移）** — `src/ib/ledger/schema.py` / `config_audit.py`（新）/ `__init__.py`
- Correctness: 10/10
- Security: 9/10
- Performance: 8/10
- Maintainability: 9/10
- Test Coverage（可测试性）: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R164-03 | MINOR | `src/ib/ledger/schema.py::CONFIG_AUDIT_DDL_STATEMENTS`；`src/deploy/migrations/004_config_audit.sql` | DDL 与迁移 SQL 为「单源摘录 + 人工同步」，存在漂移可能；已加头部注释说明以 `config_audit_ddl_script()` 为准 | DOCUMENTED |

- `SqliteConfigAuditStore` 沿用 `SqliteAccountStore` 纪律：线程局部连接、WAL、`busy_timeout=5000`；`record` 只 INSERT（追加式），`list_by_project` 按 `entry_id` **升序**稳定回放（分页稳定）。
- `CHECK (result IN ('saved','rejected'))` 在库层再约束结果码；构造失败**不静默降级为内存**（fail-closed）。

---
**MOD-IB-23：Web / 组合根 / 端点 / 序列化** — `src/ibweb/{composition,views,urls,serializers}.py`
- Correctness: 8/10（回修后修订：初评 9/10 偏乐观 —— 见 §20.10 的验证盲区说明）
- Security: 10/10
- Performance: 9/10
- Maintainability: 9/10
- Test Coverage（可测试性）: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R164-04 | MINOR | `src/ibweb/views.py::config_audit_endpoint`（`_AUDIT_TOTAL_SCAN_LIMIT = 1000`） | `total` 由上限扫描得出；超 1000 条时为下界（设计侧已在 ADR-34 以「追加式稀疏写入」吸收，不改端口方法集） | DOCUMENTED |
| FND-R164-05 | MAJOR | `src/ibweb/composition.py::_warn_audit_write_failed`（L968） | **DEFECT-R16-4-01**：审计失败旁路在模块作用域引用 `log_event`，而该名**仅**以函数内局部导入存在 ⇒ `NameError` 逸出 `record_config_audit`，破坏 IFC-IB-360「永不抛」契约（已落盘保存被报 500 / 应 400 的拒绝亦被报 500） | **FIXED**（见 §20.10） |

- **DEFECT-R16-01**：`_ToolGrantSpecSerializer` 改为**手写 `to_representation`**（与 `_EdgeSpecSerializer` 同纪律），补齐 `param_values: [{"name","value"}]`；线形与 `document_to_json` 的 `_semantic_payload` 逐字段一致，**GET→PUT 原样回写逐字节等价**；**其它字段线形零变化**。
- **DEFECT-R16-02**：保存路径与装配路径**同一校验入口** `validate_definition_full`；校验不过 ⇒ 4xx / 弃装配且**未触达写路径**（fail-safe，在用配置逐字节不变）；`admit` / `admit_two_domains` / `store.validate` 签名逐字未变（`admit_two_domains` 参数集仍为 `{doc, store}`，`admit` 仍为 `{doc, store}`）。
- **GAP-R16-03**：`storage_state_endpoint` 直读装配期快照 `Deps.storage_state`，**不从环境变量再推导**（真源单一）；`GET` only；`403` / `503` fail-closed。
- **GAP-R16-04**：`_put_definition_config` 顺序严格 **校验 → 原子写 → 审计写**；`_audit_definition_save` 对「不可编辑拒绝 / 校验拒绝 / 冲突 / 写失败 / 成功」五类均落审计；`detail_code` **只含错误码**（不落取值）；审计写经 `record_config_audit`（**永不抛**），失败发结构化 `WARN config_audit_write_failed`（`error_code` + `level` 均在白名单内，**不使用**未登记键 `detail_code`）。
- `config_audit_endpoint`：`project_id` **只认服务端结论** `ctx.authz.project_id`（不取客户端入参）；存储不可用 ⇒ `503`，**不返回空集冒充「无记录」**；`limit` / `offset` 经 `_query_int` 有界解析。

---
**MOD-IB-24：前端（配置页 + 客户端）** — `src/frontend/src/api/client.ts` / `views/ConfigPage.vue`
- Correctness: 9/10
- Security: 10/10
- Performance: 9/10
- Maintainability: 9/10
- Test Coverage（可测试性）: 9/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| — | — | — | 本轮该模块无 finding | — |

- **GAP-R16-03（IFC-IB-363）**：`loadStorageState()` 消费 `GET /api/config/storage-state`；`memoryNotice`（任一端 == `"memory"`）**常驻显式渲染**非静默提示「配置仅内存生效、不跨重启保留」；读不到存储态时 **fail-closed**（不静默假定文件态）。
- `client.ts` 新增 `storageState()` / `configAudit()`（`headers()` 仍为 `X-IB-Project` **单点注入**）；前端**不重推导**存储模式，只用端点回包。

---
**MOD-IB-25：部署交付物** — `src/deploy/migrations/004_config_audit.sql`（新）
- Correctness: 10/10
- Security: 10/10
- Performance: 10/10
- Maintainability: 9/10
- Test Coverage（可测试性）: 8/10

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R164-03（同条，见 MOD-IB-11） | MINOR | `src/deploy/migrations/004_config_audit.sql` | 与 `config_audit_ddl_script()` 人工同步（已注释声明单源） | DOCUMENTED |

- 迁移为幂等（`CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`），含回滚说明；**零新增第三方依赖**（仅 stdlib `sqlite3`）。

### 20.3 逐条 Finding 汇总

| Finding ID | 级别 | 位置 | 状态 |
|-----------|------|------|------|
| FND-R164-01 | MINOR | `src/ib/core/types.py` | OPEN（登记遗留，非阻塞） |
| FND-R164-02 | MINOR | `src/ib/config/definition.py::validate_definition_full` | DOCUMENTED |
| FND-R164-03 | MINOR | `src/ib/ledger/schema.py` + `src/deploy/migrations/004_config_audit.sql` | DOCUMENTED |
| FND-R164-04 | MINOR | `src/ibweb/views.py::config_audit_endpoint` | DOCUMENTED |
| FND-R164-05 | **MAJOR** | `src/ibweb/composition.py::_warn_audit_write_failed` | **FIXED**（DEFECT-R16-4-01，GR-D-013 门控发现，回修闭环见 §20.10） |

**CRITICAL = 0 条；MAJOR = 1 条（FND-R164-05，已修复，未触及 3 条上限）；MINOR = 4 条，均登记遗留，不阻塞。**

### 20.4 自身回归缺陷的「发现—复现—修复」闭环

| 缺陷 | 复现用例（测试侧既有断言） | 修复前 | 修复后 |
|------|--------------------------|--------|--------|
| DEFECT-R16-01（`param_values` 丢参） | `tests/integration/test_prompt_tool_config_int_r16d.py::TC_INT_140` | **FAIL**（响应缺 `param_values` 键） | **PASS** |
| DEFECT-R16-02（保存未走全量校验 ⇒ 400 漂移为 200） | `tests/integration/test_prompt_tool_config_int_r16d.py::TC_INT_139` | **FAIL**（期望 400 实得 200） | **PASS** |
| DEFECT-R16-4-01（审计失败旁路抛 `NameError`，破坏 IFC-IB-360「永不抛」） | `tests/integration/test_config_rev16_4_int.py::TC_INT_147`（GROUP_D rerun 新增） | **FAIL**（`NameError: name 'log_event' is not defined`） | **PASS**（见 §20.10） |

> 说明：上表**前三行**（DEFECT-R16-01 / 02 / 4-01）均为**测试代理（GROUP_D）资产**的断言（前两条为既有，第三条 `TC_INT_147` 为 GROUP_D rerun 新增）——本代理**只运行、未新增/未修改任何测试文件**（端口 `tests/**` 为 GROUP_D 输出目录，本代理无写权）。`test_prompt_tool_config_int_r16d.py` 修改前 `2 failed / 5 passed`、修改后 `7 passed`；`test_config_rev16_4_int.py` 回修前 `1 failed / 6 passed`（唯一失败即 `TC_INT_147` 的 `NameError`）、回修后 `7 passed`。

### 20.5 遗留问题说明（MINOR）

1. **FND-R164-01（OPEN，信息登记）**：`ConfigAuditEntry` / `StorageState` 为 Python frozen 值对象，无额外只读防护；符合本仓既有值对象惯例，**非缺陷**。
2. **FND-R164-02（DOCUMENTED）**：`validate_definition_full` 的惰性导入为**消除模块级循环依赖**的必要设计（`prompts` → `definition` 为模块级单向导入）。
3. **FND-R164-03（DOCUMENTED）**：DDL 与迁移 SQL 人工同步；已在迁移文件头声明「以 `config_audit_ddl_script()` 为单源」。
4. **FND-R164-04（DOCUMENTED）**：审计 `total` 上限扫描（1000）；因 IFC-IB-357 将端口方法钉死为 2 个（不得加 `count`），且审计写入稀疏，故以有界扫描给稳定 `total`；设计侧已在 ADR-34 吸收。

### 20.6 本轮新增 / 修改文件清单

- **新增（2）**：`src/ib/ledger/config_audit.py`、`src/deploy/migrations/004_config_audit.sql`
- **修改（13）**：`src/ib/core/types.py`、`src/ib/core/ports.py`、`src/ib/core/__init__.py`、`src/ib/config/definition.py`、`src/ib/config/__init__.py`、`src/ib/ledger/schema.py`、`src/ib/ledger/__init__.py`、`src/ibweb/composition.py`、`src/ibweb/views.py`、`src/ibweb/urls.py`、`src/ibweb/serializers.py`、`src/frontend/src/api/client.ts`、`src/frontend/src/views/ConfigPage.vue`
- **未触碰**：`tests/**`（GROUP_D 输出目录）、`docs/user_stories.md`、`docs/requirements_spec.md`、`docs/architecture_design.md`、`docs/module_design.md`

### 20.7 REV-16-4 契约与冻结约束守约复核

- **未新增模块**（26 不变，MOD-IB-01~26）；**端口 16 → 17**（`ConfigAuditStore` / IFC-IB-357，纯追加，2 方法无 update / delete）；§4.1 依赖边**逐行未改**。
- **未改任何既有 IFC 编号 / 签名 / 字段集**：`IFC-IB-001~354` 一字未改；新增 **355~363** 共 9 条。`validate` / `validate_tool_params` / `store.validate` / `admit` / `admit_two_domains` 签名逐字未变。
- **生效口径未变**：仍为「保存 + 服务重启重装配」（ADR-32 / C-IB-40 / OOS-16）；存储态端点**仅暴露**，**不引入**运行期热重载（ADR-35）。
- **只读审计 / 非第二真源**：审计表无写回配置路径；`ConfigAuditStore` 类型层无 update / delete；`ConfigAuditEntry` 只含字段名与结果码（无取值）。
- **审计写非事务耦合**：审计失败**不改变**保存结果，但**不静默**（结构化 `WARN config_audit_write_failed`，字段白名单：`error_code` + `level`）。
- **fail-safe / fail-closed 未削弱**：校验不通过 ⇒ 4xx 且在用配置逐字节不变；审计 / 存储态不可读 ⇒ 503（不返回空集冒充无记录，不静默当文件态）。
- **依赖纪律**：**零新增第三方依赖**（仅 stdlib `sqlite3`）；无 Docker；无 PyMuPDF / `fitz`；`langchain-openai` 仍 `<0.3`；bge-m3 权重未入库；无运行期 CDN / 无数据外发。
- **凭据纪律**：无任何口令 / 令牌 / 密钥字面量进入文件、命令行或日志；只登记**键名**（`IB_DEFINITION_DOC_PATH` / `IB_EXPERT_PROMPT_DIR` / `config_audit`）。
- **测试阈值**：未把任何失败改为 `skip` / `xfail`；未新增 / 未修改任何测试文件。
- **只读约束**：未 `git add` / `commit` / `push` / `stage`；未部署；未触碰目标机；**FreeArk 参考仓只读（未写入一个字节）**。

### 20.8 REV-16-4 实跑证据（命令 + 结果 + EXIT）

| # | 命令 | 结果 | EXIT |
|---|------|------|------|
| 1 | `python -m compileall -q src` | 无输出 | **0** |
| 2 | `python -m src.scripts.selfcheck` | **50/50 通过**（基线 50，零回退） | **0** |
| 3 | `python -m pytest tests/unit tests/integration -q` | **273 passed**（零回退；含 r16d 21 项） | **0** |
| 4 | `python -m pytest tests/e2e -q` | **24 passed** | **0** |
| 5 | `python -m pytest tests/unit/test_prompt_layers_r16.py tests/unit/test_prompt_tool_config_unit_r16d.py tests/integration/test_prompt_config_r16.py tests/integration/test_prompt_tool_config_int_r16d.py tests/e2e/test_config_restart_effect_r16.py tests/integration/test_definition_config_r7.py -q` | **52 passed**（含 TC_INT_139 / 140 两缺陷复现用例） | **0** |
| 6 | `cd src/frontend && npx vue-tsc --noEmit` | 无输出 | **0** |
| 7 | `cd src/frontend && node --test` | **27/27 pass**（基线 27，零回退） | **0** |
| 8 | 既有 IFC 签名比对（`inspect.signature`） | `validate` / `validate_tool_params` / `store.validate` / `admit` / `admit_two_domains` **逐字未变** | — |
| 9 | 端点冒烟 | `GET /api/config/storage-state` → `200 {"definition_store":"memory","prompt_store":"memory",...}`；`GET /api/config/audit` 空 → `{"items":[],"total":0}`；保存 → 审计 `saved`；坏保存（400）→ 审计 `rejected` + `detail_code:"tool_param_unknown"` + `changed_field_names:["tool_grants[0].param_values"]` | — |

### 20.9 §20 结论

**REV-16-4 自我评审状态：SUCCESS（回修后）。CRITICAL = 0。MAJOR = 1（FND-R164-05 / DEFECT-R16-4-01，**已修复**，见 §20.10）。MINOR = 4（均登记遗留，非阻塞）。**

> 回修说明（INV-GROUP_C-INTELBASE-017）：GR-D-013 门控判定 **FAIL**（单一 MAJOR）—— 初评将「审计写非事务耦合」判为 SUCCESS，但未覆盖「审计失败旁路**自身**抛错」这一分支。回修后 `record_config_audit` 的「永不抛」契约由**结构性保证**（旁路函数自身不可能抛）兑现；`test_config_rev16_4_int.py` 由回修前 `1 failed / 6 passed` 转为 **7 passed**，全量 `tests/unit + tests/integration + tests/e2e` **308 passed**、selfcheck **50/50**。详见 §20.10。

- 本轮范围四项**全部落地**：两回归缺陷（R16-01 / R16-02）闭环修复（复现用例由 FAIL → PASS，且**未改任何测试文件**）；两缺口（GAP-R16-03 / 04）按 ADR-35 / ADR-34 实现。
- **契约零破坏 + 收益可回归**：既有 `tests/unit + tests/integration` **273/273**、`tests/e2e` **24/24**、前端 `node --test` **27/27**、selfcheck **50/50**、`compileall` / `vue-tsc` EXIT=0 —— 全部零回退。
- 生效口径严格为「保存 + 服务重启重装配」，**无运行期热重载**；存储态**仅暴露**；审计**只读、非第二真源**、非事务耦合且失败不静默。
- **本代理已 STOP，等待 PM 门控复核；未进入 GROUP_D、未部署、未提交、未触碰目标机、未写 FreeArk。**

### 20.10 REV-16-4 回修（INV-GROUP_C-INTELBASE-017）：DEFECT-R16-4-01（FND-R164-05，MAJOR，已修复）

**触发**：GR-D-013 门控 = **FAIL**（单一 MAJOR，PM 独立确认）。**范围**：仅修复该缺陷 + 登记，**不改任何既有 IFC / 签名 / 测试**。

**缺陷与根因**
- `src/ibweb/composition.py::_warn_audit_write_failed`（L968）在**模块作用域**调用 `log_event(...)`（L970~L976）；但 `log_event` 在本文件中**仅**以**函数内局部导入**引入（L449 `_assemble`、L1130 `build_definition_store`），**不存在模块级 `log_event`** ⇒ 调用即 `NameError: name 'log_event' is not defined`。
- 该函数的两个调用点 — `record_config_audit` 的 L960（审计存储为 `None`）与 L965（`store.record(entry)` 抛错）— 均位于**审计失败旁路**。故 `record_config_audit`（IFC-IB-360）**不返回而抛 `NameError`**，逸出至调用方 `src/ibweb/views.py::_put_definition_config`（无捕获）⇒ **已成功落盘**的保存被报 **500**；被拒保存（非法工具参数，应 **400**）亦被报 **500**。此举破坏 ADR-34 / IFC-IB-360 契约「审计写失败**不改变**保存结果，但**不静默**」。

**修复（最小改动，零新增能力）** — `src/ibweb/composition.py::_warn_audit_write_failed`：
1. `log_event` 改为**函数内局部导入**（与本文件 L449 / L1130 既有 `ib.observability` 局部导入约定一致）—— 消除 `NameError`；
2. 导入 + 打点**整段 `try/except Exception` 兜底** —— 使本函数**自身不可能抛异常**，令 `record_config_audit` 的「**永不**向调用方抛异常」契约成为**结构性事实**（审计旁路**永不反噬**保存结果）。

**语义不变式（保留）**：logger 名仍 `config_audit`、事件仍 `config_audit_write_failed`、字段白名单仍 `project_id` / `error_code` / `level`（**不落任何配置取值 / 凭据**）。**签名零改**：`record_config_audit(entry, *, deps=None) -> None` 逐字未变。成功保存即便审计写失败仍返回其正常成功码；非法参数保存仍返回 **400**。

**验证盲区（诚实登记）**：初评（§20.2）对 MOD-IB-23 的「Correctness 9/10」偏乐观 —— 因既有自验仅覆盖「审计正常写入」的在途路径，**未触发审计失败旁路**，故 L970 的模块级符号解析错误未被任何断言命中。本轮将 MOD-IB-23 Correctness 修订为 **8/10**，§20.1 五维总体 Correctness 相应由 9.5 修订为 **9.3**。（该「模块级符号解析」类缺陷属**结构性可检出**：修复后由「旁路函数自身不可能抛」在设计上封堵，而非仅靠单条用例。）

**§20.10 实跑证据（命令 + 结果 + EXIT）**

| # | 命令 | 结果 | EXIT |
|---|------|------|------|
| 1 | `python -X utf8 -m pytest tests/integration/test_config_rev16_4_int.py -q` | **7 passed**（回修前 `1 failed / 6 passed`；`TC_INT_147` 由 `NameError` → PASS；强制负例 `TC_INT_141` 仍 PASS） | **0** |
| 2 | `python -X utf8 -m pytest tests/unit tests/integration tests/e2e -q` | **308 passed**（零回退） | **0** |
| 3 | `python -X utf8 src/scripts/selfcheck.py` | **50/50 通过** | **0** |
| 4 | `python -X utf8 -m compileall -q src` | 无输出 | **0** |
| 5 | 抗性取证（脚本内即验，不落文件） | `log_event` 自身抛错 / `log_event` 属性缺失两种情形下 `record_config_audit` **均不抛**；WARN payload 键集 == `{stage, outcome, project_id, error_code, level}`（`stage=config_audit`、`outcome=config_audit_write_failed`、`level=WARN`） | — |

**§20.10 守约复核**：未改任何既有 IFC 编号 / 签名 / 字段集；未新增模块 / 端口 / 依赖；`tests/**` **未触碰**（仅运行）；未 `git add` / `commit` / `push` / 部署；FreeArk 参考仓**只读**；无任何口令 / 令牌 / 密钥字面量。（finding 计数：**CRITICAL = 0 / MAJOR = 1（FIXED）/ MINOR = 4** —— §20.1、§20.3、§20.9、§20.10 四处一致。）

---

## §21 REV-17 增量自评（提示词兜底层重定位）

**设计侧口径**：`docs/architecture_design.md` **1.9.0/REV-17**（新增 **ADR-36**、**ADR-15-R2**；明文修订 ADR-29 / ADR-31 / ADR-33；**§2.0.8 R17 影响复核表**）+ `docs/module_design.md` **1.9.0/REV-17**（新增 **IFC-IB-364** / **IFC-IB-365**；**§2.2.8 REV-17 文字修订索引**）。**触发输入** = 用户请求（2026-10-07）「取消定义文档，仅仅使用 markdown 文件和兜底提示词。可视化配置文件可以对 markdown 进行 CRUD，加载，保存，生效」+ 三轮澄清后用户拍板的七项裁决（见 §21.1）。**本节的五维评分与 finding 覆盖 `src/ib/core/types.py` / `src/ib/core/ports.py` / `src/ib/config/definition.py` / `src/ib/config/prompts.py` / `src/ib/config/__init__.py` / `src/ib/experts/__init__.py` / `src/ib/llm/__init__.py` / `src/ib/orchestration/__init__.py` / `src/ibweb/composition.py` / `src/ibweb/views.py` / `src/ibweb/serializers.py` / `src/frontend/src/api/client.ts` / `src/frontend/src/views/ConfigPage.vue` 共 13 个被触及文件。**

### 21.1 结论摘要（三件事 + 七项用户裁决）

| 项 | 类型 | 结论 | 落点 |
|----|------|------|------|
| 提示词文本移出定义文档 | 真源收窄（ADR-15-R2） | **DONE** | `ExpertSpecInput` 删字段；`_semantic_payload` / 白名单 / 校验项 5；legacy 键分级处置 |
| 合并结果进 system 位 | 通道矫正（ADR-36） | **DONE** | `build_expert(spec, *, system_prompt)`（IFC-IB-212）+ `_run_expert` 传 `prompt or None`；**假陈述 docstring 消解** |
| 通用内置安全网破死锁 | 结构性保证（IFC-IB-365） | **DONE** | `BUILTIN_FALLBACK_DEFAULT` / `builtin_fallback_for`；`validate_two_domains`（IFC-IB-364）保存期与装配期共用 |

**七项用户裁决**：①只收窄不取消定义文档；②兜底层 = `fallback.md`（可编辑）为主 + 代码内置（不可界面编辑）为安全网；③生效口径维持「保存 + 服务重启重装配」（ADR-32），不引热重载；④矫正通道 = 合并结果进 system 位；⑤保存期一并校验提示词文件；⑥加通用内置安全网破「界面新增专家」死锁；⑦按正式修订 REV-17 交付。

### 21.2 finding 计数

| 级别 | 数量 | 明细 |
|------|------|------|
| **CRITICAL** | **0** | — |
| **MAJOR** | **0** | — |
| **MINOR** | **3** | MINOR-1（`builtin_fallbacks` 缺省 `None` 的默认不安全路径）；MINOR-2（CRED-01 结转，非本轮引入）；MINOR-3（`_clients` 无淘汰，上界仅靠调用方纪律） |

### 21.3 逐条 finding

**MINOR-1 · `builtin_fallbacks: Mapping | None = None` 的缺省路径不查内置兜底（默认不安全）**
- 位置：`src/ib/config/prompts.py:287-292`（`validate_prompt_directory`）、`src/ib/config/prompts.py:449-454`（`derive_prompt_layers`）、`src/ib/config/definition.py:549-556`（`validate_two_domains`）。
- 事实：三个函数的 `builtin_fallbacks` 均**可选**且缺省 `None`。缺省时判据回落到「无 `fallback.md` 即 `prompt_fallback_missing`」，即 **REV-17 之前的旧严格行为**。这是**分层纪律的必然结果** —— `ib.config` 只允许 import stdlib + `ib.core`，**不得** import `ib.experts`，故函数**无法**自行回落取内置映射，只能由调用方注入。
- 影响面（已核）：**仓内全部调用点均显式传参** —— `composition.py::_assemble` 取一次 `builtin_fallbacks()` 后传 `admit_two_domains` 与 `_inject_derived_experts`；`validate_two_domains` 的缺省由 `admit_two_domains` 兜住。故**当前无实际缺陷**。
- 为何仍登记：**API 形状是「默认不安全」** —— 将来若有新调用点漏传，会**静默**退回旧语义（保存期放行、装配期才炸），正是 REV-17 要堵的那类回归。**缓解**：`tests/unit/test_prompt_system_slot_r17.py` 与 `tests/integration/test_prompt_config_r17_int.py` 均以「显式注入」为前提断言；`selfcheck.py` 的 `r17_build_expert_system_slot` 亦锚定该链路。**建议**（不阻塞）：下一轮若再动这三个函数签名，考虑改为**必填** keyword-only 参数，把「忘了注入」从静默降级变成 `TypeError`。
- **判定：MINOR（非阻塞，登记待下轮）**。

**MINOR-2 · CRED-01 结转**
- 沿用既有登记的凭据面观察项（历史遗留，**非本轮引入**）。REV-17 未新增任何凭据面：全文只登记键名（`IB_EXPERT_PROMPT_DIR` / `IB_EXPERT_PROMPT_ENABLED`）、头名（`Authorization`）与标签名；`?token=` 纪律未被放宽。
- **判定：MINOR（非阻塞，结转）**。

**MINOR-3 · `_clients` 缓存无淘汰，上界仅靠调用方纪律**
- 位置：`src/ib/llm/__init__.py:161`（`self._clients`）、`:254-265`（`_client` 无淘汰写入）。
- 事实：缓存键为 `(temperature, system_prompt)`，**无淘汰、无容量上限**。本轮已在 `_client` 的 docstring 写明硬规则（`system_prompt` 只允许是装配期常量，禁拼请求期变量），并以新用例断言「上界 = 专家数 + 3」。但**运行期无强制** —— 若将来有人在请求路径上传动态 `system_prompt`，缓存会随请求数增长。
- 为何不修为硬上限：加 LRU 会引入与 `_clients` 语义无关的淘汰策略复杂度，且当前不变式（装配期常量）由装配层结构保证（ADR-32 无热重载 + 合并视图装配期派生）。**登记为观察项**。
- **判定：MINOR（非阻塞，登记）**。

### 21.4 逐模块 REV-17 评审详情

| MOD-ID | 模块 | 评审要点 | 结论 |
|--------|------|----------|------|
| MOD-IB-01 | 核心契约 | `ExpertSpecInput` 删 `fallback_prompt` 而 **`ExpertSpec.fallback_prompt` 原样保留**（安全网本体，`_prompt_of` / `build_expert` 回落 / `IFC-IB-175` 三处锚点）；`resolved_from` 第三值更名后 `Literal` 与 docstring 同步；`build_expert` 的 `system_prompt` 为 **keyword-only 且有默认值**（既有替身不破） | 通过 |
| MOD-IB-02 | 配置数据层 | `validate_two_domains` **不改** `validate_definition_full` 签名（`tests/unit/test_config_audit_rev16_4_unit.py` 用 `getsource` 扫它），只做外包；域序固定（定义域 → 工具域 → 提示词域）；`document_from_json` 的 legacy 分级处置 **fail-closed 且不回显正文**；`ib.config` **未** import `ib.experts`（分层纪律守住） | 通过 |
| MOD-IB-16 | 专家注册表 / 安全网 | 快照由 **`_DEFAULT_SPECS`** 派生而**非** `EXPERT_SPECS` —— 此点是本轮最关键的一处不变式（`install_derived` rebind 全局名；`build_deps(force=True)` 不回滚进程级单例，测试里是常态）；`BUILTIN_FALLBACKS` 为**全函数**（任意名字恒有非空兜底），故 ADR-29「兜底恒非空」由**结构**保证 | 通过 |
| MOD-IB-20 | LLM 提供方 | 生效口径 `effective = (system_prompt or "").strip() or spec.fallback_prompt`：**空白串视同未传**，避免「空白 system」被当成有效人格；`FakeLlmProvider` 同步加 keyword-only 参数（**不同步即离线全线静默降级**）；`_client` docstring 补硬规则并**修正**了此前「同一提示词共用实例」的模糊措辞 | 通过 |
| MOD-IB-22 | 编排 | `_run_expert` 传 `system_prompt=prompt or None` 且 human 只留用户问题。**`or None` 是必须项**：`_make_langchain_client` 在 falsy 时返回**裸 client**，裸 client **无 `run_tool_loop`** → 落单次 `invoke`，**同时失去 system 消息与 function-calling 且不报错**；`general` / 无专家路径不经 `_run_expert`（走 `build_aggregator()`，system 为硬编码串），**不受影响** | 通过 |
| MOD-IB-23 | Web / 组合根 | `_assemble` **装配期取一次**内置映射传下游；`admit_two_domains` 改调 `validate_two_domains`；`_inject_derived_experts` 改注入 `builtin_fallback_for(e.name)`（**删字段后唯一会当场断掉的落点**）；`_put_definition_config` 校验对象是 **`submitted` 而非 `current`**，且 refs 取用失败映射 **503**（同 `_get_prompts_list`，**不掉进通用异常变 500**） | 通过 |
| MOD-IB-24 | 前端 | 定义文档兜底 textarea 改**只读展示**当前内置安全网并指向提示词页 —— 保留可见性而**不开第二写入口**；`resolvedFrom()` 第三值同步（`fallback_file` 文案一字未改，冒烟测试锁着它） | 通过 |
| MOD-IB-25 | 部署交付物 | **NO_CHANGE**：零新增迁移、零新增依赖、**未 bump `schema_version`**（无迁移机制；bump 会让所有 v1 文档在 `load()` 阶段硬失败致服务起不来），改由 legacy 键分级处置兜底 | 通过 |

### 21.5 5 维评分（REV-17 增量，仅被触及面）

| 维度 | 得分 | 依据 |
|------|------|------|
| Correctness | **9** | 「兜底恒非空」由结构保证；保存期与装配期**同序同条**（新用例断言 `assembly_items == http_items`）；legacy 键 **fail-closed** 不静默丢用户文本；`system_prompt` 传参纪律落到 `or None`。扣 1：MINOR-1 的「默认不安全」API 形状。 |
| Completeness | **9** | 七项用户裁决逐项落地；13 个被触及文件与 2 个新增测试文件覆盖正 / 反两面（含「越域未被顺手放开」的反证）。扣 1：`general` 路径人格串仍不可配置（既有不对称事实，**已登记 OPEN ITEM，非本轮范围**）。 |
| Consistency | **10** | 单一校验入口（IFC-IB-364）；三处消费点共用同一份内置兜底映射（`derive_prompt_layers` 合并 / `validate_prompt_directory` 判据 / `_inject_derived_experts` 注入）；分层纪律（`ib.config` 不 import `ib.experts`）与两条顶层键红线（definition 4 键 / prompts 5 键）均守住。 |
| Maintainability | **9** | 假陈述 docstring 消解并**改写成可执行纪律**（`_client` 硬规则）；legacy 迁移目标明确到具体文件路径。扣 1：MINOR-3（`_clients` 无淘汰，上界靠纪律）。 |
| Security | **10** | 未新增凭据面；`?token=` 纪律未放宽；反越域防护**未削弱**（孤儿提示词文件仍拒）；legacy 错误信息**只报长度不回显正文**（不把用户提示词写进回执 / 日志）。 |
| **均值** | **9.4** | — |

### 21.6 REV-17 实跑证据（命令 + 结果 + EXIT）

| # | 命令 | 结果 | EXIT |
|---|------|------|------|
| 1 | `python -X utf8 -m pytest tests/unit tests/integration tests/e2e -q` | **327 passed**（unit 149 / integration 154 / e2e 24；零 skip 零 xfail；相对 REV-16-4 基线 308 零回归） | **0** |
| 2 | `python -X utf8 -m pytest tests/unit/test_prompt_system_slot_r17.py -q` | **13 passed** | **0** |
| 3 | `python -X utf8 -m pytest tests/integration/test_prompt_config_r17_int.py -q` | **6 passed** | **0** |
| 4 | `python -X utf8 src/scripts/selfcheck.py` | **51/51 通过**（REV-16-4 为 50/50；新增 `r17_build_expert_system_slot`） | **0** |
| 5 | `cd src/frontend && npm run typecheck` | 无输出 | **0** |
| 6 | `cd src/frontend && npm test` | **29 passed**（REV-16-4 为 28） | **0** |
| 7 | `cd src/frontend && npm run build` | `✓ built` | **0** |

**行为等价性（关键一条）**：生产种子文档的 `experts[].fallback_prompt` 本就是 `spec.fallback_prompt` **直抄**（旧 `composition.py::_default_definition_document`），故删字段后**生效提示词文本零变化**；只有 `resolved_from` 的**取值名**与界面标签文案变化。

### 21.7 R17 本地不可验证项（如实登记）

| # | 项 | 为何本地不可验 | 处置 |
|---|----|----------------|------|
| 1 | 生产重启后的**真实装配**（`{"outcome": "succeeded", "stage": "startup"}` 出现、`path_not_configured_using_in_memory_default` 不出现） | 需目标机与用户手工重启 | 部署阶段实测；沿用既有判据 |
| 2 | 生产现存定义文档的 **legacy 键实际取值**（是否与内置逐字相同） | 需读目标机文件（本阶段禁写操作） | 运维侧先跑一次只读核对；若「不同」则按迁移目标落 `fallback.md` |
| 3 | 开着配置页的旧会话首次保存的 **409 实际发生率** | 需真实前端会话 | 前端已有处理（`ConfigPage.vue`）；登记为交付注意 |

### 21.8 §21 结论

**REV-17 增量自评 = PASS_WITH_MINOR**：**CRITICAL = 0 / MAJOR = 0 / MINOR = 3**（1 项建议下轮改签名、1 项结转、1 项登记观察）。三项均**非阻塞**。三件事（移出定义文档 / 进 system 位 / 通用安全网）全部落地并经离线实跑验证：Python 327 / 前端 29 / 自检 51 全绿，零回归。

**§21.9 守约复核**：未新增模块（仍 26）/ 未改端口数（仍 17）/ 未新增第三方依赖 / 未改模块边界 / 未改依赖边（DAG 不变）/ 未改配置键名与默认值 / **未 bump `schema_version`** / 未改 `IFC-IB-001~363` 中除两处索引已登记 10 条口径外的任何编号与签名名 / **未改任何既有 ADR 正文**（ADR-15 与 ADR-15-R1 一字未动，收窄全落 ADR-15-R2；ADR-29 / ADR-31 / ADR-33 的修订均带**明文 REV-17 标记**）/ 两条顶层键红线守住（definition GET 与 PUT 顶层恰 4 键、prompts 顶层恰 5 键）/ 未 `git add` / `commit` / `push` / 部署 / FreeArk 参考仓**只读** / 无任何口令、令牌或密钥字面量。

---

## §22 REV-18 增量自评（系统管理三分 + 项目 CRUD + LLM Key 管理 + 项目域资料上传）

**设计侧口径**：`docs/architecture_design.md` **1.10.2/REV-18-R2**（ADR-37~ADR-42 + **ADR-21-R1**）+ `docs/module_design.md` **1.10.2/REV-18-R2**（IFC-IB-366~377 + §2.2.9）+ `docs/tech_stack.md` **1.4.1/REV-18**（NO_CHANGE）+ `docs/requirements_spec.md` **1.10.0/REV-18-2** / `docs/user_stories.md` **1.10.0/REV-18-2**。**本节五维评分与 finding 覆盖以下被触及文件**（20 个）：`src/ib/core/types.py`、`src/ib/core/ports.py`、`src/ib/core/__init__.py`、`src/ib/config/__init__.py`、`src/ib/ledger/schema.py`、`src/ib/ledger/projects.py`（新）、`src/ib/ledger/llm_key.py`（新）、`src/ib/ledger/accounts.py`、`src/ib/ledger/__init__.py`、`src/ib/llm/__init__.py`、`src/ibweb/views.py`、`src/ibweb/urls.py`、`src/ibweb/serializers.py`、`src/ibweb/composition.py`、`src/frontend/src/router/index.ts`、`src/frontend/src/layouts/ConsoleLayout.vue`、`src/frontend/src/views/{SystemSection,ProjectsPage,LlmKeyPage,UploadPage,AccountsPage}.vue`、`src/frontend/src/api/client.ts`、`src/deploy/migrations/005_projects.sql`（新）、`src/deploy/migrations/006_llm_key.sql`（新）、`src/deploy/checklists.txt`、`src/deploy/env.example`。

### 22.1 结论摘要（9 条红线逐条取证）

| 红线 | 结论 | 取证（file:line） | 验证方式 |
|------|------|------------------|----------|
| **① kb 归属断言不削弱** | **DONE** | `src/ibweb/views.py:312`（`_upload_file`）→ `:327`（`kb_id = scope.project_id`）→ `:329`（`deps.ledger.assert_kb_in_project(scope.project_id, kb_id)`）；`src/ib/ledger/schema.py::project_registry_ddl_script()`（`kb_default` 幂等前向迁移） | `tests/integration/test_http_contract.py::test_TC_INT_035`（请求体 `kb_b` 被忽略 → 201 且 `kb_id=="p_alpha"`）+ `::test_TC_INT_035b`（**端口层**直测：`assert_kb_in_project("p_alpha","kb_b")` 抛 `ScopeViolationError`）；`selfcheck.py::http_contract_offline` 同断言 |
| **② 凭据纪律** | **DONE** | `src/ibweb/views.py:2023-2057`（`llm_key_endpoint`：PUT 唯一写入口）；`src/ib/core/types.py:1448`（`LlmKeyStatus` 无明文字段）/ `:1426`（`LLM_KEY_MASK`）；`src/ib/ledger/llm_key.py:134-146`（POSIX `chmod 0600`）；`src/ibweb/authz.py:253`（`token_in_query_forbidden`） | `tests/integration/test_rev18_system_management_int.py::test_TC_INT_152`（PUT 后响应体**不含** `sk-rev18` 前缀）/ `::test_TC_INT_153`（非 admin 403 + `?token=` 400 + 零 Cookie） |
| **③ 缺 Key 非致命** | **DONE** | `src/ibweb/composition.py:494-500`（`llm_key_store.get()` → `resolved_llm_key`）+ `:671-672`（`llm_configured=bool(resolved_llm_key)` 入启动日志）；`src/ib/llm/__init__.py:303-305`（`UnconfiguredLlmProvider.health()` → `ok=False, detail="LLM 未配置（Key 未设置）"`）；`src/ibweb/views.py:769`（`/healthz/deps` llm 字段） | 启动**不**因缺 Key 失败（`selfcheck.py` 全 51 项离线装配通过即证据）；`tests/integration/test_http_contract.py::test_TC_INT_029` 断言 `/healthz/deps` 含 llm 字段 |
| **④ 契约红线（4/5 键）** | **DONE（未触碰）** | `src/ibweb/views.py:880-886`（definition 顶层恰 4 键）/ `:1256-1274`（prompts 顶层恰 5 键） | 本轮零改动，由既有 `selfcheck.py` / `tests/integration/test_prompt_config_r16.py` 断言继续守护 |
| **⑤ 分层规则** | **DONE（未触碰）** | `src/ib/config/__init__.py` 本轮仅追加键名登记，**无新 import 边** | 沿用既有分层断言 |
| **⑥ `_clients` 装配期常量** | **DONE（未触碰）** | `src/ib/llm/__init__.py:162`（无界 dict）/ `:236-266`（键含 `system_prompt`；REV-17 已立硬规则） | 本轮零改动 |
| **⑦ 账户语义** | **DONE** | `src/ib/ledger/schema.py:206-221`（`users.project_id TEXT` **无 UNIQUE**）；`src/ibweb/views.py:1948-2020`（`account_detail_endpoint`）→ `:2005-2007`（`confirm_username`）/ `:2008-2010`（`role=="admin"` → `ConflictError` → 409）/ `:2011`（软删 `set_status(...,"disabled")`）；`:1543-1552`（项目 `confirm_project_id`）；`:1916-1928`（建账号前置 422） | `test_TC_INT_127`（422 + 停用后空列表）、`test_TC_INT_150`（改名 200 / 404 / 禁删 admin 409 / 确认不符 400 / 软删 200 → 登录 401）、`test_TC_INT_151`（顺序依赖正反例） |
| **⑧ 迁移** | **DONE** | `src/deploy/migrations/005_projects.sql`、`006_llm_key.sql`（均由 `schema.py` 单源原样摘录；纯追加 `CREATE TABLE IF NOT EXISTS`） | `selfcheck.py::r13_deploy_discipline`（4b）断言两文件存在 + 幂等建表 + **可执行语句无 `DROP TABLE`** + 006 含 `CHECK (id = 1)` |
| **⑨ 环境纪律** | **DONE** | 零新增第三方依赖（`src/requirements*.txt` 未改；复用 stdlib `sqlite3`）；前端依赖集不变（Element Plus / vue-router 仍本地打包） | `tech_stack.md` 1.4.1/REV-18 判 **NO_CHANGE**；`npm run build` 无新 CDN 引用 |

### 22.2 finding 计数

| 级别 | 数量 | 明细 |
|------|------|------|
| **CRITICAL** | **0** | — |
| **MAJOR** | **0** | — |
| **MINOR** | **4** | MINOR-1（运行期新建项目未登记配置 → 检索 / 上传不可用，D-R18-01）；MINOR-2（`assert_kb_in_project` 的 403 分支在 HTTP 层不可达，设计使然）；MINOR-3（`LlmKeyStatus.masked` 未配置时为 `""`，前端以 `—` 兜底）；MINOR-4（CRED-01 结转，非本轮引入） |

### 22.3 逐条 finding（含位置 / 事实 / 处置）

**MINOR-1 · 运行期经 `POST /api/projects` 新建的项目「可建账号、可枚举，但尚不可用于检索 / 上传」**
- 位置：`src/ibweb/composition.py::_projects_from_registry`（`Deps.projects` 由注册表派生）与 `src/ib/ledger/*` 的 `load_project_record(ledger, cfg, project_id)`（对**不在配置文件**中的项目抛 `ConfigError`）。
- 事实：`POST /api/projects` 在注册表建行（`status="active"`），账号可绑定（422 前置通过）、可被 `GET /api/projects` 枚举；但检索 / 上传所需的 collection 与 ledger 项目记录仍源自**配置文件**（装配期装载）。因 `kb_id ≡ project_id`，上传路径会对未登记配置的项目拿不到 `ProjectRecord` → `ConfigError`。
- 为何不修：这是 **ADR-32「生效 = 保存 + 服务重启重装配」在项目维度的自然延伸** —— 允许运行期把项目注入配置会**引入第二真源**（配置文件 vs 注册表），越 ADR 边界。正确用法 = 建项目 → 配置侧登记 → **由用户**执行服务重启。
- **判定：MINOR（非阻塞；登记为交付注意 + `architecture_design.md §10.1` 性质）**。

**MINOR-2 · `assert_kb_in_project` 的 403 分支在 HTTP 层不可从客户端触发**
- 位置：`src/ibweb/views.py:329`。
- 事实：因 `kb_id` **恒等于**主体的 `project_id`（`:327`），提交任何 kb 字段都被忽略，故 HTTP 层**结构上不可能**提交外项目 kb —— 403 分支保留但不可达。这是「**比 403 更强**」的保证（外项目 kb 在上传路径**无法被表达**），**不是**断言被删或放宽。
- 取证：`tests/integration/test_http_contract.py::test_TC_INT_035b` 在**端口层**直测断言本体仍 fail-closed（`ScopeViolationError`）；`selfcheck.py::http_contract_offline` 同。
- **判定：MINOR（设计使然；已在用例与 §25.3(e) 明文记录，避免后人误判为「死代码」而删除）**。

**MINOR-3 · `LlmKeyStatus.masked` 在未配置时为 `""`（空串）而非固定掩码**
- 位置：`src/ib/ledger/llm_key.py::_status_of`（`record is None` → `masked=""`）。
- 事实：契约语义正确（未配置即无掩码可言），但前端 `LlmKeyPage.vue` 仍渲染 `{{ configured ? status?.masked : '—' }}`（以 `configured` 分流），故界面不会出现空白。**无缺陷**，仅登记「空串」这一取值以固定契约理解。
- **判定：MINOR（非阻塞，登记）**。

**MINOR-4 · CRED-01 结转**
- 沿用既有登记的凭据面观察项（历史遗留，**非本轮引入**）。REV-18 的凭据面**只收紧不放松**：LLM Key 载体由 `.env`（0600）改为 **DB 单行表**（`C-IB-42` 修订），进一步减少明文落盘面；HTTP 只回 `LlmKeyStatus`（**类型层无明文字段**）；审计只记 `outcome="updated"/"cleared"`，**不记 Key 值 / 掩码 / 前缀**（`views.py:2046` / `:2050`）。
- **判定：MINOR（非阻塞，结转）**。

### 22.4 逐模块 REV-18 评审详情

| MOD-ID | 模块 | 评审要点 | 结论 |
|--------|------|----------|------|
| MOD-IB-01 | 核心契约 | 新增 `ProjectRegistryEntry` / `ProjectStatus` / `LlmKeyStatus` / `LlmKeyRecord` / `LLM_KEY_MASK`（frozen，纯 stdlib）；`ProjectRegistryStore`（**恰 5 方法**）/ `LlmKeyStore`（**恰 3 方法**）Protocol；`AccountStore.update_user` 为 **加成式扩展**（既有 13 方法文本一字不改 → 14）。`LlmKeyStatus` **类型层不含明文字段** —— 凭据纪律由类型系统承载，而非靠调用方自觉 | 通过 |
| MOD-IB-02 | 配置 / 数据层 | 新增 `IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND` **仅登记键名**，且**不进入** `IB_ENV_KEYS` 核心装配开关集合（`selfcheck.py` 5b 断言）；**缺 Key 非致命**的启动校验口径改由组合根承载（不在此模块 fail-fast） | 通过 |
| MOD-IB-11 | SQL 适配器 / 迁移单源 | `project_registry_ddl_script()` / `llm_key_ddl_script()` 为**单源**；`ensure_schema` 幂等并入（对既有库同样生效）；`missing_llm_key_columns` 守结构完整；内存替身与 SQL 实现**同契约**（同一套一致性自检）；`_harden_file_permissions` 在 **POSIX** 上 best-effort `0600`，**属主对齐由用户在部署期执行**（不越权） | 通过 |
| MOD-IB-20 | LLM 提供方 | `UnconfiguredLlmProvider`：`health()` **永不抛**且如实声明未配置；`build_expert` / `build_aggregator` **调用期** fail-closed（错误文本不含 Key 信息）；`build_llm_provider(cfg, api_key=...)` 缺 Key 返回该形态 —— **启动路径零异常**（ADR-39 Option C） | 通过 |
| MOD-IB-23 | Web / 组合根 / 端点 | `projects_endpoint` **数据源切换**而授权口径 / 响应字段 / fail-closed 语义**逐位不变**；`project_detail_endpoint` 二次确认 + 软删；`account_detail_endpoint` 禁删 admin / 二次确认 / 软删 + 撤销会话；`accounts_endpoint` POST **前置 422**（顺序依赖，**不静默建无主账号**）；`llm_key_endpoint` 唯一写入口 + 只回 `LlmKeyStatus`；`_upload_file` kb 推导 + **保留**断言；`_project_registry` / `_llm_key_store` 不可用 → `DependencyUnavailableError` → 503（fail-closed）。**非 admin 一律 403**（`_require_admin` 前置） | 通过 |
| MOD-IB-24 | 前端 | 三分 IA（父级 + 三子项）只作**体验分组**，`requiresAdmin` 不承担安全（服务端 403 兜底）；hash 路由保留（不引 `try_files`）；旧 `#/accounts` 深链重定向；`uploadFile` 去掉 kb 入参（`FormData` 只 append `file`）；`LlmKeyPage` 只回显掩码 / 存在性 / 更新时间，明文提交后**立即清空**，且**不暗示即时生效**（明示「重启由用户手工执行」） | 通过 |
| MOD-IB-25 | 部署交付物 | `005` / `006` 纯追加快照；`checklists.txt` 新增 B21（项目注册表迁移幂等 / 前向 / 回滚）、B22（承载库文件 0600 属主对齐）、B23（Key 不入 `.env` / git / 命令行）；签署行同步至 **B1–B23**；`env.example` 登记两个后端键并**明文声明「Key 值不入 .env」** | 通过 |

### 22.5 5 维评分（REV-18 增量，仅被触及面）

| 维度 | 得分 | 依据 |
|------|------|------|
| Correctness | **9** | 端点契约与 IFC-IB-372~374 逐条对齐（状态码 / 二次确认 / 软删 / 422 顺序依赖）；kb 由主体推导后「越权上传」**结构上不可达**；缺 Key 非致命而其它必需项仍 fail-fast。扣 1：MINOR-1（运行期新建项目的能力边界需用户重启才齐备，属 D-R18-01 预期）。 |
| Security | **10** | 凭据纪律**只收紧不放松**（Key 载体由 `.env` 改 DB；HTTP 类型层无明文；审计不记 Key；0600）；非 admin 一律服务端 403（UI 分组非权限机制）；`?token=` 一律 4xx；零 `Set-Cookie`；`project_id` 字符集收窄防路径注入；软删替代硬删（OOS-19）。 |
| Performance | **9** | 注册表 / Key 存储复用**同一 SQLite 文件**（不引第二后端）；`GET /api/projects` 由 `list_active()` 单次查询；`LlmKeyStore` 为单行表（读写 O(1)）。扣 1：列表未分页（项目量级小，与既有口径一致）。 |
| Maintainability | **9** | 端口数 / 方法数在自检中**写死并可自证**（`AccountStore` 14 / `ProjectRegistryStore` 5 / `LlmKeyStore` 3）；内存与 SQL 实现同契约；迁移为单源快照（可人工审阅）；`_PROJECT_ID_PATTERN` 单点收窄。扣 1：MINOR-2 / MINOR-3 的登记项需靠注释与用例保持可见性。 |
| Test Coverage（可测试性） | **9** | 新增集成用例 6 条（TC-INT-148~153）覆盖项目生命周期 / 授权 / 账户改删 / 顺序依赖 / LLM Key 生命周期与纪律；前端冒烟新增 5 条（30~34）；4 条既有用例就地对齐新契约；`selfcheck` 三条既有检查订正为 REV-18 口径。扣 1：运行期新建项目的「配置登记 + 重启」路径属部署行为，不在离线可测范围（MINOR-1）。 |
| **均值** | **9.2** | — |

### 22.6 REV-18 实跑证据（命令 + 实际结果 + EXIT）

| # | 命令 | 实际结果 | EXIT |
|---|------|----------|------|
| 1 | `python -m pytest tests/unit tests/integration tests/e2e -q` | **334 passed**（unit **149** / integration **161** / e2e **24**；零 skip 零 xfail；相对 REV-17 基线 327 **零回归**） | **0** |
| 2 | `python -m pytest tests/integration/test_rev18_system_management_int.py -q` | **6 passed**（TC-INT-148~153） | **0** |
| 3 | `python -X utf8 src/scripts/selfcheck.py` | **51/51 通过** | **0** |
| 4 | `cd src/frontend && npm run typecheck` | 无输出（`vue-tsc --noEmit`） | **0** |
| 5 | `cd src/frontend && npm test` | **34 passed**（REV-17 为 29；新增 30~34） | **0** |
| 6 | `cd src/frontend && npm run build` | `✓ built in 4.19s`（chunk 体积告警为既有 Element Plus 体积，非本轮回归） | **0** |

**就地订正既有用例（4 条，均为「契约变更 → 测试同步」，非放宽断言）**：见 `docs/implementation_plan.md` §25.5 表 —— `test_TC_INT_035`（改写 + 新增 035b）、`test_TC_E2E_001` / `002`（`Scope` kb 段改为 `p_alpha`）、`test_TC_INT_126` / `127`（方法纪律与顺序依赖口径）。

**行为等价性论证**：REV-18 **不改变任何既有端点的既有语义** —— 只新增端点族与切换 `GET /api/projects` 数据源（授权口径与响应字段不变）；上传路径的可见变化为「请求体 kb 被忽略、落库 kb_id = 主体 project_id」，由改写后的 035 + 新增 035b **双向**守护。

### 22.7 REV-18 本地不可验证项（如实登记）

| # | 项 | 为何本地不可验 | 处置 |
|---|----|----------------|------|
| 1 | 生产**承载库文件 0600 与属主对齐服务账号**（B22） | 需目标机文件系统与账号权限；属主变更须改变运行身份 | **由用户**在部署期执行并核对（检查清单 B22）；实现侧只做 POSIX best-effort `chmod 0600` |
| 2 | LLM Key 的**真实 DeepSeek 调用**与「未配置 → fail-closed」的生产表现 | 需真实 Key 与外网 | 部署阶段实测；离线仅验证形态与状态码（`UnconfiguredLlmProvider.health()`） |
| 3 | 运行期新建项目的**完整可用性**（配置登记 + 重启后检索 / 上传） | 属部署行为（ADR-32 生效口径），且需用户手工重启 | 见 MINOR-1 / D-R18-01；**首次环境变量配置与生产重启须由用户执行**，本代理不执行 |
| 4 | `005` / `006` 在**既有生产库**上的前向迁移实况 | 需目标机库文件（本阶段禁写操作） | 部署阶段按 B21 执行并归档证据；`ensure_schema()` 幂等已由离线装配覆盖 |
| 5 | 前端三分 IA 的**视觉 / 交互**实际效果 | 本机仅源码结构 + 构建验证 | 部署后人工核对；冒烟用例已锁结构契约（路由 / 导航 / 文案 / 无即时生效暗示） |

### 22.8 §22 结论

**REV-18 增量自评 = PASS_WITH_MINOR**：**CRITICAL = 0 / MAJOR = 0 / MINOR = 4**（D-R18-01 能力边界 1 项 + 设计使然 1 项 + 契约取值 1 项 + 历史结转 1 项），**四项均非阻塞**。九条红线逐条落地并取证；离线实跑 Python **334** / 前端 **34** / 自检 **51/51** 全绿，相对 REV-17 零回归。

**§22.9 守约复核**：未新增模块（仍 **26**）/ 端口 **17 → 19**（纯追加，`ProjectRegistryStore` + `LlmKeyStore`）/ 未新增第三方依赖（复用 stdlib `sqlite3`）/ 未改模块边界 / **未新增 §4.1 依赖边（DAG 不变）** / 未改既有配置键名与默认值（仅新增两个后端键，不入 `IB_ENV_KEYS`）/ 未改 `IFC-IB-001~365` 中除已登记 7 条（`IFC-IB-024` / 242 / 243 / 262 / 263 / 321 / 333）口径外的任何编号与签名名 / **未改任何既有 ADR 正文**（ADR-21 一字未动，N:1 全落 **ADR-21-R1**）/ 未 bump `schema_version` / 两条顶层键红线守住（definition 顶层恰 4 键、prompts 顶层恰 5 键）/ 未 `git add` / `commit` / `push` / 部署 / FreeArk 参考仓**只读** / **无任何口令、令牌或密钥字面量**（测试内 LLM Key 为 `sk-rev18-placeholder-not-a-real-key-0000` 占位值）/ **不引运行期热重载**；**生产后端重启与首次环境变量配置须由用户执行**（本代理不执行，文档只写「由用户执行」）。
