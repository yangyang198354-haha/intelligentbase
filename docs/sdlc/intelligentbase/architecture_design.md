<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-27T00:42:15+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>user_stories.md</file>
    <file>agent_orchestration_benchmark.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计（REV-26 增量）— 可视化配置：热生效 / 自由 DAG 画布 / 版本化 / 三档权限 / Agent Builder

**范围与基线**：本文件只写 REV-26 增量。现有设计基线 `docs/architecture_design.md`（1894 行，只读不改，下称"基线"）与 `docs/module_design.md`（只读）继续有效，凡未在 §6 登记为"取代 / 修订"的基线 ADR 与约束一律沿用。已批准需求 = 同目录 `requirements_spec.md` 2.0.0 与 `user_stories.md` 2.0.0；调研 = `agent_orchestration_benchmark.md` 2.0.0。
**编号**：本轮 ADR 从 **ADR-53** 接续（基线最后为 ADR-52）；模块 / 接口在 `module_design.md` 中记为 `MOD-R26-NN` / `IFC-R26-NNN`（避免与基线 `MOD-IB-NN` / `IFC-IB-NNN` 混淆）；新 TBD 从 **TBD-T32** 接续（基线最后为 TBD-T31）。基线条目引用时保留其原编号。
**GR-A-002-F01 处置**：requirements_spec 中 OQ-R26-13 / C-R26-11 把"不得含资料正文以外的敏感数据"标注为用户原话，实为 PM 转述；其内容（外发禁止项）已由用户确认为 OQ-R26-13=A，本文件按 A 执行（ADR-65），不再追溯原话归属。

---

## 1. 架构概览

### 1.1 本次改动在现有系统中的位置

REV-26 推翻基线三条长期口径（CL-003 用户裁决）：① 保存后须重启才生效（ADR-32 / C-IB-40 / OOS-16）；② 编排拓扑运行期不可编辑、图编译一次常驻（基线 §6、ADR-14 约束③、ADR-15-R1 规则⑦、ADR-52）；③ 单一默认编排流（OOS-21）。同时补齐基线没有的四块能力：版本化与回滚、三档账号权限、按资料目录的运行时知识范围、Agent Builder（云端 LLM 生成 / 自评 / 优化）与保存前试运行。

改动落在六个层面，**不新增 systemd 单元、不新增第三方依赖、不引入 Redis / Channels / 容器**：

| 层面 | 现状（已核实，见 §1.2） | REV-26 之后 |
|---|---|---|
| 配置载体 | 定义文档目录 `<IB_DEFINITION_DOC_PATH>/<project>.json` + 提示词目录 `<IB_EXPERT_PROMPT_DIR>/<project>/<expert>/{main,fallback}.md`，两域分别写 | 两域文件**仍是**持久化真源；新增台账表 `config_versions` / `config_head` 作"提交记录 + 历史快照"，一次保存 = 一个版本（ADR-55） |
| 运行期装配 | `Deps.orchestrator_for` 每项目缓存一个 `Orchestrator`，进程级 `ib.experts` 全局被"首个项目"覆盖 | 每项目一份**不可变** `CompiledProjectConfig`，提问时租用；台账 head 指针驱动换版（ADR-53 / 54） |
| 图 | 固定拓扑 `route → expert×N / general → gate → aggregate` | 定义文档 schema v2 的 `graph`（受限节点集）编译为 LangGraph；v1 文档读时规范化为同一路径（ADR-56 / 57 / 58） |
| 权限 | `admin` / `ops(manager)` 二元；写配置 = `can_manage` | 配置三档 view / edit / manage（`users.config_level`）；运行期按 agent 强制工具与目录范围（ADR-60 / 61 / 62） |
| 审计 | `config_audit` 只记字段名，无版本，不限期 | 同表扩列（版本前后 / 对象清单），保留 1 年，外发审计同表（ADR-67） |
| Builder / 试运行 | 无 | `ib.builder`（单点外发 + 规则化自评）与草稿编译试运行（ADR-63~66） |

### 1.2 现状核实表（一手读码；"事实 → 设计影响"）

| # | 事实（文件:行） | 设计影响 |
|---|---|---|
| F-1 | 问答只在 `ib-web` 进程：`deps.orchestrator_for` 的调用点仅 `src/ibweb/views.py:639`（`chat_stream_endpoint`）与 `:746`（`chat_resume_endpoint`）；`src/ibweb/worker.py` 不引用编排器 | 需要收敛的"承载进程"实际只有 `ib-web`；但设计不得依赖"单进程"（`requirements.txt:17` 把 Gunicorn 作备选），故用台账指针（ADR-53） |
| F-2 | `ib-web.service`：`waitress-serve --threads=8`，`MemoryMax=1024M`，`ExecStartPre=... --ensure-schema` | 单进程 8 线程；编译快照与 SSE 容量要在 1 GiB 内；迁移随重启自动应用 |
| F-3 | 运行期仍读进程级全局：`_run_expert` 用 `ib.experts.get`（`src/ib/orchestration/__init__.py:1115`），`_prompt_of` 用 `prompt_bundles()`（`:724-742`），`_expand_plan` 用 `default_expert()` / `delegating_experts()`（`:609`），聚合清洗用 `cn_map()`（`:175-182`）；装配期把**首个项目**的派生结果写进全局（`src/ibweb/composition.py:839-840` 调用，`_inject_prompt_bundles` / `_inject_derived_experts` 定义在 `:1777` / `:1792`） | 多项目下后装配项目的提示词 / 专家表实际取自首个项目，热换版前必须让运行期只读快照（ADR-54） |
| F-4 | `Deps.bind_tools` 取项目全部授权的并集（`build_authorized_tools` 对同名工具只绑一次，`src/ib/tools/__init__.py:364-411`），再对**每个专家**发同一份工具列表（`composition.py:340` `tools_by_expert={name: bound_tools ...}`） | **今天按专家的工具授权与参数在运行期并未被强制**（只在保存期校验）；REQ-FUNC-009 / REQ-NFUNC-007 要求 100% 命中，须改为按 agent 绑定（ADR-61） |
| F-5 | `RetrievalService.search` 向向量库传 `PointFilter(project_id, kb_ids, doc_ids=None)`（`src/ib/retrieval/__init__.py:97` 起）；`PointFilter.doc_ids` 已在内存实现与 Qdrant 适配器贯通（`src/ib/vectorstore/__init__.py:193-226`、`:368-381` `_build_filter` 的 `MatchAny`、`:485-505`）；payload 无目录字段，目录 `folder_id` 只在台账 `documents` 表（`src/ib/ledger/schema.py:441` `FOLDER_TREE_ADDED_COLUMNS`），树存储 `EntryTreeStore` 有 `list_subtree_folders` / `list_subtree_documents` / `resolve_live`（`src/ib/ledger/tree.py:110-182`） | 检索层**能**按资料目录过滤：目录 → 台账解析 doc_id 集合 → `PointFilter.doc_ids`（ADR-62），不改向量 payload，不触发向量重写 |
| F-6 | 语义路由示例句取自 `IB_EXEMPLARS_DIR/<project>.exemplars.json`（`composition.py:1859-1881`），定义文档 `experts[].exemplars` 只在种子构造时读该文件（`:1447-1453`） | 热生效要让"示例句"随版本变化，编译快照须以版本内 `exemplars` 为准（文件仅作种子来源）；记为现状缺口并随 ADR-54 修正 |
| F-7 | `OpenAiCompatibleProvider._clients` 按 `(temperature, system_prompt)` 缓存且无上界（`src/ib/llm/__init__.py:162`、`:241-272`），ADR-36 决定 4 以"缓存上界 = 专家数 + 3"为可测断言 | 每次换提示词版本都会产生新键；须改为有界 LRU 并修订该断言（ADR-54） |
| F-8 | `PUT /api/config/definition` 拒绝拓扑变更（`non_editable_changes`，`src/ib/config/definition.py:206-230`；`NON_EDITABLE_FIELDS` `:77-90`），保存后只刷新进程内 `deps.definitions` / `derived_views`（`views.py:998-1005`）；前端提示"重启后生效"（`ConfigPage.vue:675-676`） | 白名单、校验入口与前端提示须随 CL-003 改写（ADR-56 / 58；测试清单见 §6.3） |
| F-9 | 账号角色 `users.role CHECK IN ('admin','ops')` 且 ops 必绑定单项目（`schema.py:206-226`）；`effective_roles`：ops → `("manager",)`（`ibweb/accounts/__init__.py:156-163`）；`AccountsPolicy.can_manage` = admin 或 manager（`ibweb/accounts/policy.py:50-54`）；定义文档 GET 不要求 manage、PUT 要求（`views.py:884-889`、`:917`） | 三档用"每账号一列 + roles 令牌 + 纯函数"承载，不改 `AuthzPolicy` 端口（ADR-60） |
| F-10 | `config_audit` 的 `result CHECK IN ('saved','rejected')`，字段只含字段名（`schema.py:293-310`）；`ConfigAuditStore` 端口刻意无 update / delete（ADR-34） | 扩列 + 新动作名复用结果取值域；1 年保留经**独立维护端口**删除，不破坏"无删除入口"（ADR-67） |
| F-11 | 会话态 `MemorySessionStore`（进程内，`composition.py:_assemble` 的 `sessions = MemorySessionStore(...)`）；确认门挂起态存 `SessionState.gate`（`types.py:812`、`orchestration/__init__.py:543` `_persist_gate`） | 挂起会话要钉版本：`SessionState` 追加 `config_version`；重启丢失仍 fail-closed（ADR-17 不变） |
| F-12 | 条件边今天不是运行期结构：`_compile_graph` 硬编码 5 个节点（`orchestration/__init__.py:1091-1102`），路由判定在图外（`Orchestrator._decide`，`:714`） | DAG 编译需新增编译器；路由节点要能在图内调用路由器（ADR-57） |
| F-13 | `@vue-flow/core` 1.48.2（MIT，`package-lock.json`）已含 `nodeMouseEnter` / `edgeMouseEnter` / `connect` / `nodeDragStop` / `isValidConnection` / `nodesChange` / `edgesChange` 事件（`node_modules/@vue-flow/core/dist` 类型声明实测）；`ConfigPage.vue:757-759` 把拖拽 / 连线 / 选中全部禁用 | 前端**无需新增依赖**（ADR-69） |
| F-14 | nginx 示例 `location /api/` 已按 SSE 设置（`proxy_buffering off` / `gzip off` / `proxy_read_timeout 300s`，`nginx/intelligentbase.conf.example:120-146`），`client_max_body_size 64m`；Django `DATA_UPLOAD_MAX_MEMORY_SIZE = 64MiB`（`settings.py:118`） | 试运行 SSE 与发布请求体不需要改 nginx / 设置；仍在应用层限制请求体 |
| F-15 | `run_tool_loop(prompt, tools, *, max_iterations=4)`（`llm/__init__.py:477`）；LLM 调用了未绑定的工具名时只回"未知工具，忽略该调用"（`:511-515`），不留记录 | 按 agent 工具边界的"拒绝并记录"（AC-009-02）需在此处追加回调（ADR-61）；"最大专家步数"可映射为该参数（OQ-R26-A05） |
| F-16 | 现有代码中不存在对"提示词单层长度"的上限（`grep` 无命中；INF-4 同） | 新增 `PROMPT_LAYER_MAX_CHARS` 校验（20000，占位，ADR-68） |

### 1.3 关键质量属性（引 REQ-NFUNC）

| 属性 | 目标 | 架构手段 |
|---|---|---|
| 时效 REQ-NFUNC-001 / 004 | 保存成功后 ≤5 s（INF-3 占位）新提问用新版本；多进程一致 | 台账 head 指针 + 提问前 1 s 节流比对 + 保存进程立即换版（ADR-53） |
| 原子 / 失败安全 REQ-NFUNC-002 | 要么整体生效要么不生效；失败时旧版继续服务 | 发布前预编译；WAL 式提交记录 + 恢复回滚；换版 = 原子换引用（ADR-54 / 55） |
| 进行中会话 REQ-NFUNC-003 / FUNC-015 | 每次提问绑定开始时刻版本 | 请求持有 `RuntimeLease`（不可变快照引用）；挂起会话存 `config_version`（ADR-54） |
| 并发 REQ-NFUNC-005 | 后保存者不得静默覆盖 | `base_version` 乐观 CAS + 冲突回执 + 草稿副本（ADR-59） |
| 审计 REQ-NFUNC-006 | 不可改、1 年、含版本前后 | 扩 `config_audit`；独立保留端口（ADR-67） |
| 越权 REQ-NFUNC-007 | 服务端判定；运行期按 agent 强制 | 三档纯函数 + 按 agent 绑定工具与 `doc_scope`（ADR-60 / 61 / 62） |
| 内容安全 REQ-NFUNC-008 | 提示词 / Builder 产出不可信 | 授权只取自配置不取自文本；Builder 产出经规则适配器；前端纯文本渲染（ADR-63 / 69） |
| 可测 REQ-NFUNC-013 | 图校验 / 版本比较 / 权限判定离线单测 | 三者均为 framework-free 纯函数（`ib.config.graph` / `versioning` / `access`） |
| 外发 REQ-NFUNC-014 / 015 | 白名单 + 审计 + 降级 + 时限 | 单点 `EgressGuard`（ADR-65）；`ib.builder` 不得 import 检索 / 向量 / blob（自检规则） |
| 兜底 REQ-NFUNC-010 | 永不无应答；运行防失控 | 图校验"默认专家可达" + 运行期安全网（图无输出则默认专家）+ 步数 / 迭代上限（ADR-57） |
| 存量 REQ-NFUNC-012 | 旧项目不改文件、行为一致 | 读时规范化、首存升级、哈希稳定规则（ADR-58 / 68） |

### 1.4 运行期数据流（文字图）

```
提问:  HTTP(SSE) ─▶ chat_stream_endpoint ─▶ ProjectRuntimeCache.acquire(project)
         │  (≤1 次/秒/项目) SELECT published_version FROM config_head ─ 与当前快照版本比对
         │     相同 ─▶ 返回当前 CompiledProjectConfig (RuntimeLease)
         │     不同 ─▶ 后台单飞编译新快照；本次仍用旧快照；编译成功 ─▶ 原子换引用
         ▼
       Orchestrator(runtime=lease.compiled).run()  ── 全程只读这份快照（注册表 / 提示词 / 工具绑定 / 图 / 路由器）

保存:  POST /api/config/publish ─▶ 鉴权(edit) ─▶ 校验(图+两域+长度) ─▶ 差异/冲突(CAS on base_version)
         ─▶ 预编译(失败则 4xx/5xx，不落盘) ─▶ BEGIN IMMEDIATE: 写 pending 版本行(含完整快照)
         ─▶ 写提示词文件(变更层) ─▶ 写定义文档(最后) ─▶ COMMIT: published_version=N+1 + 审计 + 修剪
         ─▶ 本进程立即换引用；其它进程 ≤1 s 内由 head 比对发现
         任一步失败 ─▶ 依快照 N 还原文件、pending 标 aborted、旧版继续服务
```

---

## 2. 部署视图

仅使用画像 P7 中存在的环境与运行单元；**无新增 systemd 单元**（ADR-03 / 画像 P7 四单元固定）。

| 组件 | 运行单元 | 环境 | REV-26 变化 |
|---|---|---|---|
| Django 视图 / 发布服务 / 运行时缓存 / Builder / 试运行 | `ib-web`（Waitress 单进程 8 线程） | dev（离线替身）/ CI / production | 代码与迁移随 `git pull` + 重启；后台编译与 Builder 调用用进程内小线程池（非新单元） |
| 保留清理（审计 1 年、版本 50 个、评审缓存） | `ib-worker`（既有循环增加一步维护） | 同上 | 仅代码变更；不新增实例（P8 禁多实例） |
| 台账 SQLite（新增 5 张表 + 2 处扩列） | 与现有台账同一文件，随 `ib-web` 的 `ExecStartPre --ensure-schema` 应用 | production | 迁移 008，幂等 |
| 定义文档目录 / 提示词目录 | 现有本地目录（`/var/lib/intelligentbase/...`） | production | 布局不变；v1 文档首次保存时升级为 v2（不批量改写） |
| 前端静态产物 | 目标机 `npm run build` → web root | production | 无新依赖，重新构建发布 |
| nginx | 现有反代 | production | **无需修改**（`/api/` 已满足 SSE，F-14） |
| Qdrant / `ib-embed` | 既有 | production | 不改（目录范围过滤用既有 `doc_ids` 条件；示例句向量沿用 `ib-embed` 冷路径） |

**上线本身仍需一次重启**：本轮改动代码、schema（008）与前端，`ib-web` 与 `ib-worker` 各重启一次（`sudo -n systemctl restart` 仅这两项免密，画像 P7）；此后配置变更不再需要重启。

---

## 3. ADR

> 记法：Status 全部为 `Proposed`（本轮新提出，待门控）；Type 为 `decision` 或 `constraint-driven`。`[ESTIMATE]` = 无实测的估计，`[ASSUMPTION]` = 无需求依据 / 无法核实的假设（汇总见 §7）。`[WEB: URL，日期]` = 网页事实。

### ADR-53: 热生效的跨进程收敛机制（台账 head 指针 + 提问前比对）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-014、REQ-NFUNC-001（≤5 s，INF-3）、REQ-NFUNC-004（所有承载进程收敛到同一版本）、C-R26-02（禁 Redis / Channels / 新单元）、C-R26-03。事实 F-1 / F-2：今天只有 `ib-web` 承载问答且是单进程多线程，但 Gunicorn 多进程是文档化的备选，不应把正确性绑在"单进程"上。
- Options:
  - A. 保存进程原地替换 + 其余进程靠重启（SIGHUP / `systemctl restart`）：优—零新机制；缺—与 CL-003"无需重启"直接冲突，且重启会中断进行中的 SSE。
  - B. Redis pub/sub 或 Channels group 广播：优—即时；缺—画像 P8 禁用，新增组成面。
  - C. 台账新增 `config_head(project_id, published_version, pending_version, updated_at)`；每次提问前读一次 head（按项目 1 s 节流），与进程内快照版本比对，不一致则后台单飞编译并原子换引用；保存进程在提交后立即换引用 ← **选定**。
  - D. 监听两域文件（inotify / mtime 轮询）：优—不依赖台账；缺—跨文件非原子（可能读到半个版本）、无版本号概念、无法表达"回滚到 N"。
  - E. 进程间内部 HTTP 通知：优—比轮询快；缺—新增内部认证面与失败重试，单进程场景无收益。
- Decision: 选 C。`HeadProbe` 对 `config_head` 做主键点查（WAL 下不阻塞写者），节流间隔键名 `IB_CONFIG_HEAD_CHECK_INTERVAL_S`（默认 1.0，仅键名，不入响应体）。收敛上界 `T ≤ 节流间隔 + T_编译 + T_换引用`；换引用是单次引用赋值（原子）。后台编译用 `ib-web` 进程内单线程池（非新运行单元）。编译失败：旧快照继续服务，指数退避重试（5 s 起，上限 60 s），状态经 `GET /api/config/status` 暴露 `apply_state ∈ {ok, applying, apply_failed}`。`ib-worker` 不承载问答（F-1），无需热换版客户端；它只执行维护步骤（ADR-67）。
- Consequences:
  - 正向：无新单元 / 依赖；任意进程数下正确；保存进程读己之写即时；符合 REQ-NFUNC-004 的"版本号一致"可抽样验证。
  - 负向：每项目每秒至多一次台账点查；非保存进程最长落后一个节流间隔 + 编译时间（INF-3 在目标机实测，TBD-T32）；后台编译占用 `ib-web` CPU / 内存（`MemoryMax=1024M`，TBD-T37）。

### ADR-54: 不可变编译快照与"每次提问绑定开始时刻版本"（取代"图编译一次常驻"）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-015、REQ-NFUNC-002 / 003 / 004、REQ-NFUNC-010。事实 F-3（运行期读进程级全局、首个项目覆盖）、F-6（示例句来自环境目录文件）、F-7（LLM 客户端缓存无界）、F-11（挂起会话态在进程内）。基线 ADR-32 / §6 "图编译一次常驻、运行期不得改变拓扑"被 CL-003 推翻；ADR-43 ⑥"装配期把首个项目写入全局"是 F-3 的来源。
- Options:
  - A. 原地改常驻 `Orchestrator` 与 `ib.experts` 全局：优—改动小；缺—读写竞态，进行中回答会混用新旧节点 / 提示词（违反 REQ-NFUNC-003），且多项目互相覆盖。
  - B. 每次提问现编译：优—无缓存一致性问题；缺—每问都要重建 LangGraph 与路由器（含示例句向量化，经 `ib-embed` 冷路径，秒级）。
  - C. `CompiledProjectConfig`（frozen 值对象：版本号、专家注册表视图、每专家提示词包、每 agent 的工具绑定与目录范围、编译后的 LangGraph、路由器与示例句向量）+ 进程内 `ProjectRuntimeCache`（原子换引用）+ 请求租约 ← **选定**。
  - D. 双槽 active / standby 切换：优—回退快；缺—是 C 的子集，对"挂起会话钉旧版"无帮助。
- Decision: 选 C。① 运行期（`Orchestrator._run_expert` / `_prompt_of` / `_expand_plan` / 聚合清洗）只读本快照，**不再读 `ib.experts` 进程级全局**（全局仅保留给离线 / 未注入快照的旧调用，参数缺省即旧行为，append-only）；② 请求开始时 `acquire(project_id)` 取得快照引用并贯穿整次回答，故换版不影响进行中回答；③ 缓存保留当前版 + 最近 2 个旧版 + 被挂起会话钉住的版本，被挤出后按版本号从台账快照重编译（超出 50 个保留版本则 fail-closed 409）；④ 示例句以版本内 `experts[].exemplars` 为准（F-6 的环境目录文件降为种子来源）；示例句向量按文本哈希进程级缓存，换版只重算变更部分；⑤ `OpenAiCompatibleProvider._clients` 改为有界 LRU（键名 `IB_LLM_CLIENT_CACHE_MAX`，默认 128），ADR-36 决定 4 的"上界 = 专家数 + 3"可测断言改为"上界 = 配置上限且仅装配期常量入键"；⑥ 每次回答的运行记录携带 `config_version`：结构化日志 `chat.started` / `chat.completed` 字段 + `CompletionPayload.config_version`（追加字段，默认 0）。
- Consequences:
  - 正向：进行中回答单一版本（REQ-NFUNC-003）；挂起会话恢复沿用挂起版本（AC-015-03，被删除的 agent 仍在旧快照里）；多项目互不覆盖（顺带修正 F-3 现存偏差）。
  - 负向：内存多驻留最多约 3–5 份快照（示例句向量为主，TBD-T37）；`Orchestrator` 构造改为"带 runtime 的可选形参"，既有单测需覆盖两条路径；基线 ADR-36 决定 4 与 ADR-43 ⑥ 的表述被修订（§6）。

### ADR-55: 两域"一次保存 = 一个版本"的存储与一致性（文件仍为真源 + 台账提交记录）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-014 / 017、REQ-NFUNC-002 / 005、C-R26-04（结构域真源 = 定义文档，提示词域真源 = 提示词目录；画布不得有独立持久化）、基线 ADR-15-R1 / R2 / ADR-36（各域单一可写载体）。两域是不同路径下的多个文件，文件系统无法一次原子提交多文件。
- Options:
  - A. 只加版本号指针，仍按旧序写各文件：优—最简；缺—崩溃时两域可能对不上，无回滚依据，无历史。
  - B. 台账作为配置真源（快照即读源），文件仅导出：优—事务原子；缺—违反 C-R26-04 与 ADR-15-R1 / R2 / REQ-FUNC-IB-41（用户要的 markdown 文件态），重新引入"第二真源"。
  - C. 文件仍为真源；台账 `config_versions` 保存每次保存的**完整快照**并充当**提交记录（WAL）**，`config_head.published_version` 是唯一的"已发布"指针 ← **选定**。
  - D. 版本化目录 + 符号链接原子切换：优—天然原子；缺—要重排两个环境变量指向的现有目录（ADR-44 / A10 布局），需要用户手工迁移生产数据，违反 REQ-NFUNC-012"不静默改写"的精神。
- Decision: 选 C。发布协议（`ConfigPublishService.publish`）：
  1. 鉴权 edit 档；解析请求；校验（图 + 两域 + 长度，纯函数，与装配同一入口）；
  2. `base_version == head.published_version` 否则 409 冲突回执（ADR-59）；`pending_version` 非空且未陈旧 → 409 `config_busy`；
  3. 与 head 快照做 `diff_snapshots`；无变更 → 422 `no_changes`，不产生版本；
  4. **预编译**（真 LangGraph 编译 + 示例句向量），失败 → 返回 `apply_failed`，**不落盘**；
  5. `BEGIN IMMEDIATE`：再次核对 head；插入 `config_versions(version=N+1, status='pending', 完整快照, manifest_hash)`；置 `pending_version`；提交；
  6. 写变更的提示词层文件，最后写定义文档（各自既有原子替换）；
  7. `BEGIN IMMEDIATE`：版本行置 `published`、`published_version=N+1`、清 `pending_version`、写审计、修剪超出 50 个的最旧版本；提交；
  8. 本进程换引用并返回。
  任一步失败：依 head 快照 N 还原文件（幂等），把 pending 版本标 `aborted`，响应错误，旧版继续服务。**恢复**：任一进程发现 `pending_version` 且 `updated_at` 超过 `PENDING_STALE_S`（默认 30 s）→ 用同样的"还原 + aborted"处理（对 `pending_version` 做 CAS，只有一个进程执行）。**漂移**：每次编译时计算文件 `manifest_hash` 并与 head 版本行比对；不一致（有人绕过系统直接改文件）→ 以 head **快照**编译（被审计过的版本，避免未经校验的手改静默上线，对齐 ADR-16），状态暴露 `drift=true` 并在 UI 提示；`POST /api/config/adopt-drift`（manage 档）把当前文件状态校验后记为新版本。快照作读源仅有三种情形：漂移、挂起会话钉旧版、回滚预览。**回滚** = 以目标版本快照为内容走同一协议产生新版本（`kind='rollback'`）。**内存态**（定义 / 提示词存储为内存实现，ADR-35 的 `memory`）使用内存版本存储，语义相同。
- Consequences:
  - 正向：保持两域真源与 markdown 文件态；崩溃 / 部分写入有确定的回滚终态；历史、差异、回滚、审计共用同一份快照；发布协议是单一入口，旧 `PUT definition` / `PUT prompts` 退化为它的包装（IFC-R26-086）。
  - 负向：台账存完整快照（最坏每版约 2–6 MB，保留 50 版；[ESTIMATE]，TBD-T33 实测）；发布耗时含预编译与双文件写；手工改文件会被判为漂移（有意取舍）；基线 ADR-15-R1 规则⑦"生效口径 = 保存 + 重启"与 ADR-32 被取代（§6）。

### ADR-56: 定义文档 schema v2 的图结构与受限节点集

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-006 / 011 / 012 / 013、C-R26-05（默认专家恰好一个、条件边显式分支映射）、OOS-R26-04（无代码 / 表达式节点）、OOS-R26-08（无环）、INF-1（位置随配置保存）。F-8：现 schema 的 `orchestration.nodes` 是字符串元组，只能表达基线固定图。
- Options:
  - A. 扩展 `orchestration`（`nodes: tuple[str]`、`edges`、`conditional_edges`）并附坐标：优—改动小；缺—节点没有类型与参数位，汇聚 / 确认 / 条件谓词无处安放；旧的"单 `expert` 占位节点"与新逐专家节点混用语义含糊。
  - B. 新增顶层 `graph`（带类型的节点 + 边 + 坐标），schema_version 升为 2 ← **选定**。
  - C. 采用外部 DSL（LangGraph JSON 导出 / Dify DSL）：优—生态现成；缺—引入任意字段 / 代码节点的攻击面，违反 OOS-R26-04，且不受本项目校验器约束。
- Decision: 选 B。`graph` 数据格式（示意，字段与限制见 `module_design.md` IFC-R26-001）：

```json
{
  "schema_version": 2,
  "graph": {
    "nodes": [
      {"id": "START", "kind": "start", "x": 0, "y": 0},
      {"id": "route-1", "kind": "route", "x": 200, "y": 0},
      {"id": "kb-agent", "kind": "agent", "expert": "kb-agent", "input_mode": "query_only", "x": 400, "y": 0},
      {"id": "join-1", "kind": "join", "x": 600, "y": 0},
      {"id": "END", "kind": "end", "x": 800, "y": 0}
    ],
    "edges": [
      {"id": "e1", "source": "START", "target": "route-1"},
      {"id": "e2", "source": "route-1", "target": "kb-agent", "branch_key": "kb-agent"},
      {"id": "e3", "source": "route-1", "target": "kb-agent", "branch_key": "__else__"}
    ]
  }
}
```

  节点种类恰为 `start / end / route / agent / condition / join / confirm`；`agent.id` 恒等于其 `expert` 名（沿用 ADR-52 决定 1 "节点 id = 专家 name"，故同一专家在图中至多一个节点）；结构节点 id 匹配 `^[a-z0-9][a-z0-9_-]{0,47}$` 且不得与专家名、`START` / `END` / `__else__`、前缀 `__relay__` 冲突；边为 `always`（无 `branch_key`）或 `branch`（`route` / `condition` 出边，须含且仅含一个 `__else__`）；图上限 60 节点 / 200 边 `[ASSUMPTION]`（INF-5 的 30/60 的 2 倍裕度）。`orchestration` 字段在 v2 文档中缺省为空，由 `graph` 派生显示（ADR-52 的投影规则仅对 v1 文档保留）。校验 `validate_graph` 为纯函数（REQ-NFUNC-013），逐条返回 `ValidationErrorItem(path, code, message)`，错误码清单见 `module_design.md` IFC-R26-010。
- Consequences:
  - 正向：类型化节点便于校验与渲染；坐标进文档满足 REQ-FUNC-012；`ValidationReport` 仍无 force / ignore（类型层事实不变）。
  - 负向：`DefinitionDocument` 增 `graph` 字段（可空，旧构造点不受影响）；`editable_field_whitelist` / `NON_EDITABLE_FIELDS` / `non_editable_changes` 对 v2 改写；基线 ADR-14 约束③、ADR-15-R1 的"拓扑不可编辑"、ADR-52 对 v2 文档被取代（§6）。

### ADR-57: 自由 DAG → LangGraph 的编译与运行语义（层归一化 + 中继节点）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-006 / 011 / 013、C-R26-12（生成物"可运行在 LangGraph 可编排"）、OQ-R26-02=A（汇聚 = 等全部**实际被激活**的上游）、REQ-NFUNC-010。事实 F-12：现图硬编码；路由在图外。LangGraph 语义（官方文档）：节点在"收到任一入边消息"时变为 active，同一超步并行运行，条件边可返回节点名列表在下一超步并行运行 [WEB: https://docs.langchain.com/oss/python/langgraph/graph-api，2026-10-27]。
- Options:
  - A. 沿用单 `expert` 节点 + `Send` 扇出：优—现状可运行；缺—无法表达任意 DAG / 汇聚 / 条件。
  - B. `add_edge([a, b], join)` 的"等待全部入边"写法：优—原生；缺—若某上游分支未被激活，汇聚永不触发（死等），与 OQ-R26-02=A 相反。
  - C. 节点 `defer` 选项：优—可能支持"延迟到本轮结束"；缺—官方页未覆盖、版本区间（`langgraph>=0.2,<2.0`）内是否可用无法核实，不作依赖。
  - D. 自写执行器，不用 LangGraph：优—语义完全可控；缺—违反 C-R26-12 与"保留 LangGraph 编排"的既有栈。
  - E. **层归一化**：按最长路径给每个节点定层；跨多层的边插入无操作中继节点，使每条边恰好跨一个超步；于是任一节点的全部可能上游都在同一超步完成，汇聚在"本超步实际被触发的上游"全部完成后恰好运行一次 ← **选定**。
- Decision: 选 E，编译器 `compile_dag(graph, runtime)`（纯结构转换 + 注入的节点闭包，业务零依赖，ADR-09）：
  1. `layerize_graph`（纯函数）：Kahn 拓扑 + 最长路径定层，产出 `RelayPlan`（中继节点 id 形如 `__relay__{edge_id}_{k}`）；
  2. 节点语义：`agent` = 构造该 agent 的 system 提示词（取自快照）+ 其专属工具 / 目录范围，执行 `run_tool_loop(max_iterations=该 agent 的 max_steps)`；`input_mode='with_upstream'` 时把最近已激活上游 agent 的输出作为只读"上游材料"段追加到 **human** 位（不进 system、不提升权限，REQ-NFUNC-008）；`route` = 以出边目标为候选集调用 `IntentRouter.classify_experts(..., restrict_to=候选)`，命中集合激活对应 `branch_key` 出边，无命中走 `__else__`；`condition` = 枚举谓词（`keyword` / `upstream_degraded`，无表达式，OQ-R26-A03），按声明顺序首个命中，否则 `__else__`；`join` = 透传（已激活上游输出并入状态）；`confirm` = 以 `interrupt_before` + 进程内检查点挂起（`MemorySaver`），沿用 ADR-17 的呈递 / 恢复 / 丢失即 fail-closed 语义，话术取节点参数 `message`（≤200 字，由配置者提供，骨架不生成）；
  3. 状态：`outputs`（节点 id → 文本，字典合并 reducer）、`trace`（`operator.add` 的节点执行记录，用于"未激活"对账与运行记录）、`expert_results`（沿用）；
  4. 终稿：对"无已激活 agent 后继"的叶子 agent 输出做既有 `Orchestrator._aggregate`（含禁止暴露内部分工的确定性清洗，AC-IB-09-03）；
  5. 步数：`route.max_expert_steps` 保持图级上限——单个 `route` 命中的 agent 数超过上限时走隐式 `general`（与旧 `_fan_out` 一致，保证存量等价）；整次回答已执行 agent 数达上限后，后续 agent 节点记 `skipped_step_cap`，无任何输出时落到安全网；
  6. 安全网：图执行结束无任何可用输出 → 直接用快照里的默认专家作答 → 仍失败则 `general` 文本，"绝不无人应答"为运行期结构事实，不只依赖静态"默认专家可达"校验；
  7. v2 文档上 `expert_handoff_enabled` 不生效（交接由边表达）；应急开关 `IB_GRAPH_RUNTIME=dag|legacy`（默认 `dag`；`legacy` 仅保留旧固定图作回退与等价性测试基准，只增取值域不改键名，M-SA-001）。
- Consequences:
  - 正向：汇聚语义与 OQ-R26-02=A 精确一致且不依赖 LangGraph 未核实特性；`layerize_graph` / `validate_graph` 可离线穷举单测；与旧图在规范化后同一运行路径（ADR-58）。
  - 负向：中继节点增加少量无操作超步（每超步毫秒级 `[ESTIMATE]`）；节点数上界受 ADR-56 限制；`interrupt_before` / `MemorySaver` / "收到任一入边消息即 active"在 `langgraph` 1.x 与 0.2 的行为须以契约测试固化（`[ASSUMPTION]`，版本区间未在本机安装验证，见 TBD-T34）；人工确认的挂起态随进程丢失即 fail-closed（OQ-R26-A06）。

### ADR-58: 存量项目（schema v1）的读时规范化与首存升级

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-012、C-R26-10（既有落盘物不得静默改写）、US-020。生产定义文档是 v1（`orchestration.nodes` = `route / expert / general / gate / aggregate`，`_definition_document_from_specs`，`composition.py:1430-1498`）。
- Options:
  - A. 启动期批量把 v1 文件改写为 v2：优—之后只剩一种格式；缺—违反"不静默改写"，且需要用户手工迁移 / 备份流程。
  - B. 读时在内存规范化为等价的默认 `GraphSpec`，首次保存才写 v2 ← **选定**。
  - C. 长期并存两种运行路径且永不升级：优—零迁移；缺—两套执行路径永久并存。
- Decision: 选 B。`canonical_graph_from_experts(experts, default_expert)`（纯函数）：`START → route → 每个启用的专家(agent, query_only) → END`，route 的 `__else__` 指向默认专家；v1 文档的 `orchestration` 字段只用于显示（保持 ADR-52 投影）。v1 项目没有版本行，head 视为"虚拟版本 0"，`published_version` 缺省按 0 处理；**首次发布**在同一事务内先写 `version=1`（`kind='baseline'`，actor=`system`，内容 = 规范化后的原状快照，作为可回滚目标），再写用户的 `version=2`（OQ-R26-A07 记录该编号口径）。语义哈希稳定规则：新增字段**仅在取非默认值时**进入 `_semantic_payload`，使存量文档 `content_hash` 不变（避免 ADR-15-R2 那种"全体哈希换一次"）。等价性由金标测试把关：同一批固定提问在 `IB_GRAPH_RUNTIME=legacy` 与 `dag` 下的路由结果与答复专家集合一致率须 100%（REQ-NFUNC-012）；上线动作不触碰任何既有定义文档 / 提示词文件（文件哈希前后一致）。
- Consequences:
  - 正向：零迁移、零手工步骤、可立即回退（`IB_GRAPH_RUNTIME=legacy` + 重启）；存量项目首存即得可回滚基线。
  - 负向：旧固定图代码路径需保留至少一个版本周期；规范化图与旧图的等价依赖金标测试而非证明；首存一次写入两个版本（编号口径需用户确认）。

### ADR-59: 并发冲突（乐观 CAS 版本）与草稿副本

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-005、OQ-R26-09=B（拒绝 + 重新载入 + 可另存草稿副本，不加编辑锁）、US-018；基线 `PUT definition` 的 409 以语义哈希判定（`views.py:979-993`）。草稿副本是用户显式要求的持久化，须与基线 ADR-14"视图零持久化"（不得用 localStorage / IndexedDB / 独立后端表作**载入源**）协调。
- Options:
  - A. 编辑锁 / 租约：已被用户裁决排除。
  - B. 请求携带 `base_version`；服务端在提交事务内比较 head，不等则 409 并附冲突回执（三方比较 base 快照 / head / 提交内容，列出两边都改动的对象）；草稿副本存服务端 `config_drafts`（每账号每项目至多 10 个，单个 ≤1 MiB）← **选定**。
  - C. 后写覆盖：违反 REQ-NFUNC-005。
- Decision: 选 B。冲突回执 `ConflictReceipt(base_version, head_version, conflicts: tuple[ConflictItem(kind, object_id, fields)], base_available: bool)`；`base_version` 已被修剪（超出 50 个保留版本）时 `base_available=false`，`conflicts` 退化为"全部对象"。不做自动合并（OQ-R26-09 未要求）。草稿副本**不是载入源**：只在用户显式"载入草稿"时回填编辑器，运行期与发布路径从不读取它，故不构成第二真源；删除随保存者自行操作。
- Consequences:
  - 正向：兑现"不静默覆盖"；回执可测（AC-018-01）；与 ADR-14 的零持久化原则兼容（草稿是显式的用户副本，非视图缓存）。
  - 负向：并发编辑同一版本的两人，后保存者必须重新载入后手工合并；新增 `config_drafts` 一表与配额。

### ADR-60: 配置访问三档（view / edit / manage）映射到现有账号与项目授权

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-010、OQ-R26-06=A、OQ-R26-07=A、REQ-NFUNC-007；事实 F-9：ops 绑定单项目、`AuthzPolicy` 只有 `can_manage` / `can_query`。
- Options:
  - A. `users` 增一列 `config_level`（仅对 ops 有意义，admin 恒 manage）；`effective_roles` 追加令牌 `cfg:<level>`；纯函数 `config_level_of(AuthzContext)` ← **选定**。
  - B. 新表 `project_grants(user_id, project_id, level)`：优—可一人多项目；缺—与 ADR-21-R1（N:1，一账号一项目）冲突，徒增一张表与 join。
  - C. 复用 `admin` / `manager` 二元并把"查看"视为只能问答：优—零改动；缺—无"编辑 vs 管理"之分，不满足 OQ-R26-06=A。
- Decision: 选 A，不改 `AuthzPolicy` 端口（IFC-IB-032 / 033 不动；ADR-22 的"单一授权真源"口径保持——令牌由同一 `SessionTokenResolver` 产出，不存在第二套判定）。端点最低档位：读（GET definition / prompts / versions / status / diff 预览 / 草稿列表）= view；校验、发布、预览、草稿保存、试运行、Builder 全部入口 = edit；回滚、采纳漂移、授予档位、读审计 = manage。`PUT /api/config/access/{user_id}` 允许 manage 档在**本项目**内调整其他账号的档位（不得改角色 / 项目 / 创建账号，账号 CRUD 仍 admin 专属）；每次变更写审计（action `access.grant`）。存量 ops 账号迁移默认 `manage`（= 与今天"能写配置"等价，不回退能力），新建账号接口必须显式给出档位（OQ-R26-A01）。非 accounts 策略（离线 `AllowAllPolicy`）下无令牌的 `manager` / `admin` 角色按 `manage` 处理。view 档的 ops 账号仍保留其资料库管理能力（`can_manage` 未变，ASSUMPTION A-R26-06）。
- Consequences:
  - 正向：改动面小；判定是离线可测纯函数；不破坏 ADR-22。
  - 负向：`users` 新增列（迁移 008 的 ALTER，幂等）；"一人多项目"仍不支持（沿用 ADR-21-R1）；view 档能否继续管理资料属于产品语义，已登记假设。

### ADR-61: agent 运行时工具与参数的按专家强制（修正"项目并集"现状）

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-007 / 009(a)、REQ-NFUNC-007 / 008、基线 ADR-30（工具授权最小化 + 参数可配）。事实 F-4：运行期今天把项目授权并集发给每个专家；F-15：LLM 调用未绑定工具名时被静默忽略。
- 约束来源与被排除方案：需求要求"未授予的工具即使被提示词或用户输入要求也不得访问，且 100% 命中"（REQ-NFUNC-007 度量）；ADR-30 已定"最小授权"。被排除：① 仅靠提示词约束工具使用（REQ-NFUNC-008 明令授权不得取决于文本）；② 继续项目级并集（违反 REQ-FUNC-009）。
- Decision: 编译快照时按 agent 调用 `build_agent_tools(grant, registry, specs, scope, knowledge)`（只用**该 agent 自己的** `ToolGrantSpec` 与参数、再 `bind_scope`）；`tools_by_expert` 由此构造；agent 的 function-calling 只暴露这些 schema。`run_tool_loop` 追加关键字 `on_unauthorized: Callable[[str], None] | None` 与 `max_iterations`（沿用既有形参，由 agent 的 `max_steps` 给定）：模型给出未绑定的工具名时调用回调，运行时记录一条 `tool_rejected`（结构化日志 + 运行记录，不含参数值），并回给模型"未授权"。工具参数与目录范围作为不可见闭包注入（不出现在 LLM 看到的 `parameters` schema 中）。
- Consequences:
  - 正向：AC-009-02 可断言；per-agent 参数（`top_k` 等）首次真正按专家生效；与 ADR-09（骨架业务零依赖）一致——编排层只拿到已绑定的无参工具。
  - 负向：行为变更（此前"同名工具首个授权的参数赢"）可能改变既有项目的检索条数，需在发布说明列出并由金标用例覆盖；`run_tool_loop` 签名追加可选关键字（既有调用不受影响）。

### ADR-62: 知识范围（资料目录）在检索层的过滤方式

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-009(b)、OQ-R26-05=B、US-009、AC-009-01 / 03、REQ-NFUNC-007。需求要求"架构阶段须确认检索侧能否按目录过滤，不能则回议"。事实 F-5：能。
- Options:
  - A. 入库时把 `folder_id` 写进向量 payload 并在 Qdrant 按 payload 过滤：优—单次查询精确；缺—移动 / 重命名目录需要批量改向量 payload，违背 REV-25"移动 / 改名零向量操作"（P-SA-001），且历史点要回填。
  - B. 查询时由台账把"目录子树"解析为 `doc_id` 集合，作为 `PointFilter.doc_ids` 传入（向量库两种实现均已支持）← **选定**。
  - C. 不预过滤，召回后用 `entry_resolver` 按目录后过滤：优—改动最小；缺—被范围外文档挤占候选后 `top_k` 不足（假阴性），且范围外片段已被取回内存。
- Decision: 选 B。`KnowledgeScope(mode: Literal['all','folders'], folder_ids: tuple[str, ...])`：`all` = 不加 doc 条件（存量默认）；`folders` 且 `folder_ids` 为空 = 0 命中且**不查询向量库**，返回既有 `EMPTY_HINT`（AC-009-03）；否则 `DocScopeResolver.live_doc_ids(project_id, folder_ids, limit)` 在台账一次递归查询得到"子树内存活且已索引文档"的 id 集合（新增端口方法，落点 `ib.ledger.tree`），经 `RetrievalService.search(..., doc_scope=...)` 构造 `PointFilter(project_id, kb_ids, doc_ids=...)`；`project_id` 恒在（FM-1 不变）。目录以 `folder_id` 引用（改名 / 移动稳定）；子树在**查询时**解析，故之后新增的文件自动纳入；引用的目录被删除 → 该引用解析为空（fail-closed），保存期另有"目录存在"校验。集合超过 `DOC_SCOPE_MAX_IDS`（默认 5000，键名 `IB_DOC_SCOPE_MAX_IDS`）时改用 C 的"过取 + 后过滤"并记 `doc_scope_overflow` 日志（TBD-T35 在目标机量化阈值）。目录集合解析结果按 `(project, folder_ids)` 在进程内缓存 ≤5 s（`[ESTIMATE]`），避免每次工具调用都做递归查询。
- Consequences:
  - 正向：不改向量 payload、不回填、不触发重建；目录改名 / 移动零向量操作；范围内召回数量正确。
  - 负向：每次受限检索多一次台账查询（缓存缓解）；`doc_ids` 条件很大时 Qdrant 过滤成本上升（TBD-T35）；`search` 新增可选关键字，既有调用不变。

### ADR-63: Agent Builder 的生成 / 适配 / 优化管线（云端 DeepSeek，langchain-openai <0.3）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-018 / 019 / 020 / 021 / 022、REQ-NFUNC-008 / 014 / 015、C-R26-11 / 12；用户原话（CL-005）：生成"可运行在 langgraph 可编排、适配所在项目的工具 / 权限 / 参数 / 要求"的 agent。约束：`langchain-openai>=0.2,<0.3`（P8）；Builder 产出一律是草案，不得有未经确认上线的路径（REQ-FUNC-021）。
- Options:
  - A. 一次自由文本生成 + 正则抽取：优—简单；缺—字段缺失 / 格式漂移无法稳定处理。
  - B. 提示词内约束 JSON 输出 + 容错解析 + **规则适配器**（越界项移入适配说明）← **选定**。
  - C. 原生 function-calling / `response_format` 严格模式：优—结构更稳；缺—在 `langchain-openai<0.3` 与 DeepSeek 上的行为未核实，不作依赖；保留为升级路径。
- Decision: 选 B。管线 `generate(requirement)`：① 校验输入（非空、≤`BUILDER_REQUIREMENT_MAX_CHARS`=2000 字、秘钥模式扫描）；② `EgressGuard.build_payload` 构造白名单载荷（ADR-65）；③ 单次 LLM 调用（经 provider 的实现侧方法 `complete(system, user, *, temperature=0)`；端口方法集不变，M-SA-001），系统指令来自仓库种子资产 `src/ib/builder/assets/*.md`（可审阅、可 diff，沿用 ADR-49 先例），要求输出 JSON（含 `requirement_summary`）；④ 容错解析；⑤ `adapt_draft`（纯函数）：工具只取项目既有工具（不存在 → 移除并记适配说明）、目录名映射到项目存在的 `folder_id`（不存在 / 非本项目 → 移除）、工具参数与 `max_steps` 越界 → 调整为默认值并记说明、name / 中文标签与现有 agent 重复 → 标红要求改名（不覆盖）、检索类 agent 的主提示词缺 REQ-FUNC-IB-56 三项 → 记说明（并由自评扣分）、含业务专有词（FreeArk 等）→ 记说明；⑥ 返回 `AgentDraft + AdaptationNote[] + Evaluation`。`optimize(draft)` 单轮：服务端重新评审、携带扣分清单再调用一次 LLM、再 `adapt_draft`、返回修订草案 + 前后分数 + 字段级差异；不自动循环。`review_existing(expert)`：载荷仅含被选 agent 的提示词与配置，结果是字段级补丁建议，由用户逐项采纳到画布草稿，**服务端不写任何配置**。全部入口无任何落盘 / 发布路径（REQ-FUNC-021 的"含不经界面的直接调用"成立：Builder 服务对 `ConfigPublishService` 无依赖，类型层即无法发布）。LLM 不可用（未配置 Key / 网络 / 超时 / 被拒）→ 统一 `BuilderUnavailable(reason)`，返回可读错误 + 错误码，手工方式（空白表单 / 克隆）不经过 Builder，不受影响；单次请求总时限 60 s（INF-6）由进程内小线程池 + `future.result(timeout)` 强制，线程池满返回 429 `builder_busy`。
- Consequences:
  - 正向：生成物的合法性由确定性规则保证，不信任模型输出（REQ-NFUNC-008）；LLM 可替换（只有 `complete` 一个调用点）；离线可用替身测试（`FakeLlmProvider` 增加 `complete`）。
  - 负向：JSON 约束靠提示词，偶发格式错误需要重试 / 报错（单次重试一次，计入 60 s）；提示词资产与 `rubric` 须同版本演进；超时线程无法被强制终止，只能靠底层 HTTP 超时回收（占线程池名额至多 60 s）。

### ADR-64: 自评维度、规则化与"同输入同分"的复现策略

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-020、OQ-R26-14=A（五维 20/25/15/25/15，<60 不合格 / 60–89 合格 / ≥90 优秀；可规则化的必须规则化，语义类若用 LLM 须做到重复评审一致，做不到则回议）、US-026、参照 `.claude/agents/agent-builder.md:29,48-90`（固定维度、每条扣分有证据、同文本同分）。
- Options:
  - A. 全部由 LLM 打分：优—覆盖语义；缺—DeepSeek 无可保证的确定性（服务端无 seed 承诺），违反"同输入同分"。
  - B. 规则项（确定性函数）+ 少量 LLM 布尔判定项，LLM 判定按"内容哈希"持久化缓存，重复评审命中缓存 ← **选定**。
  - C. 仅规则项：优—完全可复现；缺—评不了提示词语义（OQ-R26-14 的选项 C）。
- Decision: 选 B，rubric 版本 `r26.1`（五维满分 20 / 25 / 15 / 25 / 15，合计 100）：D1 完整性与格式、D2 项目适配度（以适配说明为证据）、D3 路由质量、D5 安全与约束 **全部规则判定**；D4 提示词质量中 19 分由规则判定（引用来源 / 无命中诚实应答 / 工具使用契约三项用固定词表 + 结构检查；无业务专有词；长度区间），**仅 6 分**为三条 LLM 布尔判定（与需求角色一致 / 无自相矛盾 / 无与护栏冲突指令，各 2 分，要求引用原文片段作证据）。每条扣分记录 `(dimension, check_id, field, points, evidence)`，没有证据的扣分不产生。LLM 判定项：temperature=0、布尔输出、结果按 `sha256(规范化草案 ‖ 项目配置指纹 ‖ rubric 版本 ‖ 模型标识)` 写入 `builder_eval_cache`（仅保存完整覆盖的结果），再评审先读缓存。**必须明说的限制**：模型本身不保证确定性——"同输入同分"在缓存有效期内由缓存保证（保留 90 天或 2000 条，维护步骤清理），缓存失效后的首次重评可能在这 6 分上出现差异；LLM 不可用时评审降级为"仅规则项"，结果带 `coverage='rules_only'` 标记且不入缓存。该限制作为 OQ-R26-A04 交用户 / PM 确认（备选：仅规则项 / LLM 项仅作提示不计分）。
- Consequences:
  - 正向：94% 的分值完全确定；扣分有证据；评审可离线单测；LLM 故障不阻断评审。
  - 负向：词表规则有误判 / 漏判（只是"检查项存在性"的近似，不评语义优劣）；缓存新增一表与维护；与 OQ-R26-14 的"回议"条款存在残余——需用户确认接受上述残余风险。

### ADR-65: Builder 外发白名单的强制点与审计

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-014、REQ-NFUNC-006、C-R26-11、OQ-R26-13=A、US-030（载荷字段 100% 属白名单；`CANARY-DOC-001` / `CANARY-SESSION-001` 命中 0；每次外发恰 1 条审计；审计无需求原文）。
- Options:
  - A. 各调用点自行裁剪：优—灵活；缺—遗漏一处即外泄。
  - B. 在 HTTP 客户端层拦截：优—覆盖面全；缺—不了解业务语义，无法按"字段类别"判定。
  - C. 唯一出站函数 + 类型化载荷构造器：载荷由 `OutboundPayload` 的固定字段按类别逐一构造（需求 / 修改意见原文、项目配置摘要、被选 agent 配置），**类型里没有**会话、资料正文、账号、审计、其他项目的字段；出站前做秘钥模式扫描与大小上限；**先写审计、后发送**（审计写失败 → 不发送，fail-closed）← **选定**。
- Decision: 选 C。`ib.builder.egress.EgressGuard.send(kind, payload) -> str` 是 Builder 访问 LLM 的**唯一**入口；`ib.builder` 包不得 import `ib.retrieval` / `ib.vectorstore` / `ib.blob` / `ib.streaming` 会话类（`scripts/selfcheck.py` 新增 `builder_no_data_imports` 与 `builder_single_egress` 两条静态规则，对齐既有 `ib_embed_isolation` 做法）。审计复用 `config_audit`（action `builder.egress`，`object_summary` 只含 `{kind, field_categories[], payload_bytes}`，不含需求原文与提示词）。白名单类别：`requirement_text`、`project_digest`（现有 agent 的 name / 中文标签 / 关键词 / 示例句，工具名与参数声明，资料目录名称——最多 200 个、不含文件名与正文，项目约束摘要）、`selected_agent`（仅 optimize / review_existing）。载荷上限 64 KiB，超出先裁剪示例句再裁剪 agent 列表。用户输入中疑似秘钥（`sk-` / `ghp_` / `AKIA` / `-----BEGIN` / `password=` 等）→ 拒绝并返回 `egress_secret_detected`（不回显命中内容）。
- Consequences:
  - 正向：白名单是类型层事实而非纪律；审计与发送不可分离；可用 canary 测试对出站载荷做字节级断言。
  - 负向：新增数据类别须改类型与审计枚举（有意的摩擦）；资料目录名称属用户数据（OQ-R26-13=A 已接受），目录名里的敏感字样会被外发。

### ADR-66: 保存前试运行（草稿配置独立运行，不影响线上）

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-023（Should）、US-029、REQ-NFUNC-007、C-R26-02（SSE 容量）。
- Options:
  - A. 为草稿临时创建影子项目：优—复用全部装配；缺—污染项目注册表 / 台账 / 向量 collection 前缀断言，清理复杂。
  - B. 请求携带草稿，服务端把它编译成一次性 `CompiledProjectConfig`（不写任何配置、不进缓存主表），独立的试运行会话存储，`POST` + SSE 返回 ← **选定**。
  - C. 在线上图上加版本参数切换：优—省编译；缺—草稿不在台账里，线上缓存无法承载未发布版本，且易被误当线上版本。
- Decision: 选 B。`TrialRunner.run(draft, query, ctx)`：先走与发布相同的全量校验（环 / 不可达等逐条错误，校验失败不调用 LLM，REQ-FUNC-023）；编译产物放入独立 `TrialCache`（键 = 草稿规范化哈希，LRU 4，TTL 10 min），会话用独立的 `MemorySessionStore` 实例与 `trial:` 前缀会话键，不出现在正式会话列表；运行记录带 `trial=true` 且 `config_version` 记为 `-1`；工具与目录范围按**草稿内**配置强制（只读检索工具，无副作用）。容量：同一项目同时至多 1 个试运行、全进程至多 2 个，超出快速 429（占用 SSE 线程预算，M-SA-006）；每账号每 10 分钟至多 20 轮 `[ESTIMATE]`。
- Consequences:
  - 正向：对线上零影响（不读不写线上缓存与会话）；与正式运行共用同一编译器，试得准。
  - 负向：每次草稿变化需重编译（有 LRU 缓解）；试运行消耗云端 LLM 额度与 SSE 线程；草稿体积上限 1 MiB。

### ADR-67: 审计扩展与保留（1 年 / 50 版本）

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-006、REQ-FUNC-017、OQ-R26-08=B；基线 ADR-34 / A11（审计只增不删、保留待定）；F-10。
- Options:
  - A. 新建 `config_audit_v2` 等新表：优—结构干净；缺—两张审计表并存、既有端点要双读。
  - B. `config_audit` 迁移 008 追加三列（`version_before` / `version_after` / `object_summary`），新动作名 `config.publish` / `config.rollback` / `config.adopt_drift` / `access.grant` / `builder.egress` 复用 `result ∈ {saved, rejected}` ← **选定**。
  - C. 版本信息只放 `config_versions`，审计不变：优—零改表；缺—REQ-NFUNC-006 要求审计记录本身含前后版本号与对象清单。
- Decision: 选 B。`ConfigAuditStore` 端口（只读 + 追加，IFC-IB-357）**保持无 delete**；保留清理由独立的 `ConfigAuditRetention.purge_before(cutoff_iso) -> int` 端口承担，仅注入 `ib-worker` 的维护步骤，HTTP 层不持有；同一维护步骤修剪 `config_versions`（每项目保留最近 50 个、保留 head 与 pending）、过期草稿（30 天）与评审缓存。审计内容不含提示词全文与凭据（只含字段名、对象 id、版本号、哈希 / 长度）。
- Consequences:
  - 正向：一处查询看到全部配置类事件；"无删除入口"在类型层仍成立（删除端口不暴露给 Web）。
  - 负向：`config_audit` 增列需要 ALTER（`ensure_schema` 已有探测补列先例）；审计在 1 年边界处会被维护步骤物理删除（需求明确为 1 年）。

### ADR-68: 专家规格扩展（停用 / 步数 / 知识范围）与语义哈希稳定规则

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-005 / 008 / 009 / 019、OQ-R26-11=A / OQ-R26-12=A、REQ-NFUNC-012；`ExpertSpecInput`（`types.py:930`）只有 7 个字段；`_semantic_payload`（`definition.py:99`）决定 `content_hash`。
- Options:
  - A. 在 `ExpertSpecInput` 末尾追加带默认值字段：`status: Literal['active','disabled']='active'`、`max_steps: int | None=None`、`knowledge_scope: KnowledgeScope=ALL`；`_semantic_payload` 对"取默认值"的新字段**省略**，保证存量哈希不变 ← **选定**。
  - B. 另设顶层 `agent_settings` 数组按 name 关联：优—不碰 `ExpertSpecInput`；缺—同一 agent 的数据拆在两处，校验与差异更复杂。
  - C. 放进图节点参数：优—与图一起；缺—工具 / 范围是专家属性而非节点属性（同一专家换位置不应改权限）。
- Decision: 选 A。停用 = `status='disabled'`：保留在 `experts[]`（名称 / 标签保留、历史可显示），不进运行期注册表与图，默认专家不可停用（校验）；`max_steps` ∈ [1, 8]（OQ-R26-A05：该 agent 单次执行的工具调用轮数上限，默认 4）；`PROMPT_LAYER_MAX_CHARS = 20000`（INF-4 占位）；`keywords` ≤20 条、`exemplars` ≤10 条 `[ASSUMPTION]`。`validate` 追加对应校验码；`editable_field_whitelist` 追加新字段。
- Consequences:
  - 正向：一个 agent 的全部属性仍在 `experts[]` 一处；存量文档哈希不变（乐观并发不会因升级而集体 409）。
  - 负向：`ExpertSpecInput` 与 `document_from_json` / `document_to_json` 同步改；`ExpertSpec`（运行期类型）不必改，快照另带 `AgentRuntimeSpec`。

### ADR-69: 前端组件拆分与依赖（constraint-driven）

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-001 / 002 / 003 / 004 / 011 / 012 / 016 / 017、REQ-NFUNC-008 / 009 / 011。画像 P6 / P8：前端无 axios、无 CDN、HTTP 只经 `src/frontend/src/api/client.ts`、新增依赖须论证许可证与离线可用性；hash 路由。
- 约束来源与被排除方案：被排除——引入新的图 / 布局库（如 dagre / elkjs / 另一画布框架）：现有 `@vue-flow/core` 1.48.2（MIT，F-13）已提供悬停 / 拖拽 / 连线 / 变更事件，分层布局沿用既有 `layeredPositions`；引入新依赖要核实传递依赖许可并增加体积（TBD-T20 / T23），无必要。被排除——直接 `v-html` 渲染提示词（违反 REQ-NFUNC-008，一律文本插值）。
- Decision: 零新增前端依赖；`ConfigPage.vue`（1289 行）收敛为页面壳，拆分为：`FlowCanvas`（画布 + 节点面板 + 连线校验 `isValidConnection`）、`NodeHoverCard` / `EdgeHoverCard`（只读摘要，纯文本）、`AgentDetailPanel`（提示词 / 路由 / 工具 / 参数 / 知识范围）、`PublishDialog`（差异确认）、`ConflictDialog`（冲突回执 + 放弃 / 另存草稿）、`VersionHistory`（列表 + 差异 + 回滚）、`TrialPanel`、`BuilderDrawer`（手工 / 克隆 / AI 生成 / 评审优化）、状态集中在 Pinia-free 的轻量 `configDraft` store（沿用现有 `stores/*.ts` 的手写 store 风格）。前端预校验仅为体验，服务端为唯一裁决者；节点 / 边 / 提示词一律文本插值。
- Consequences:
  - 正向：无供应链 / 体积 / 离线性新风险；组件可用 `node:test` 对纯模型函数（悬停卡片模型、图→表单映射）做冒烟。
  - 负向：画布交互量大（拖拽 / 连线 / 脏标记 / 撤销缺省不做），30 节点 / 60 边下的 300 ms 悬停指标需目标浏览器实测（TBD-T36）；`ConfigPage.vue` 大改，既有冒烟断言需随之更新。

---

## 4. 需求→ADR 追踪（摘要）

| REQ | 主要 ADR |
|---|---|
| REQ-FUNC-001 / 002 / 003 | ADR-69（卡片 / 面板 / 草稿联动）、ADR-56（数据来源） |
| REQ-FUNC-004 / 018~022 | ADR-63 / 64 / 65 |
| REQ-FUNC-005 / 008 | ADR-68 |
| REQ-FUNC-006 / 011 / 012 / 013 | ADR-56 / 57 |
| REQ-FUNC-007 / 009 | ADR-61 / 62 |
| REQ-FUNC-010 | ADR-60 |
| REQ-FUNC-014 / 015 / 017 | ADR-53 / 54 / 55 |
| REQ-FUNC-016 | ADR-55（`diff_snapshots`）、ADR-69（PublishDialog） |
| REQ-FUNC-023 | ADR-66 |
| REQ-NFUNC-001~004 | ADR-53 / 54 / 55 |
| REQ-NFUNC-005 | ADR-59 |
| REQ-NFUNC-006 | ADR-67 |
| REQ-NFUNC-007 / 008 / 011 | ADR-60 / 61 / 62 / 63 / 69 |
| REQ-NFUNC-009 | ADR-69、§8 INF 口径 |
| REQ-NFUNC-010 | ADR-57 |
| REQ-NFUNC-012 | ADR-58 / 68 |
| REQ-NFUNC-013 | ADR-56（纯函数）、ADR-60、ADR-55（`diff_snapshots`） |
| REQ-NFUNC-014 / 015 | ADR-63 / 65 |

---

## 5. 与既有长期约束的核对（门控自查）

| 约束 | 核对结果 |
|---|---|
| 禁 Docker / 容器化 | 无涉及 |
| 不引入 Channels / Redis | 收敛机制用台账点查（ADR-53）；试运行沿用原生 SSE |
| 单实例 `ib-worker`，不新增 systemd 单元 | 维护步骤并入既有 worker 循环；后台编译 / Builder 线程池在 `ib-web` 进程内 |
| `langchain-openai <0.3` | 不变；Builder 不依赖 `response_format` / 严格结构化输出（ADR-63 Option C 仅作升级路径） |
| 禁 PyMuPDF | 无涉及 |
| `ib.*` 不得 import `ib_embed` | 无涉及；`ib.builder` 另加两条静态规则 |
| 前端无 axios、无 CDN，HTTP 只经 `client.ts` | ADR-69 零新增依赖；试运行 SSE 沿用 `fetch + ReadableStream` |
| 迁移按画像 P6 | 迁移 008 手写，与 `schema.py` 生成器逐字一致、幂等、带回滚说明（`module_design.md` §数据迁移） |
| 凭据不入库 | 外发白名单禁凭据；审计 / 快照不含凭据；LLM Key 仍只在 `llm_key` 表（ADR-38） |

---

## 6. 对基线 ADR / 约束的取代与修订登记

### 6.1 逐条登记（基线正文不改，以本表为准）

| 基线条目 | 处置 | 本轮依据 | 说明 |
|---|---|---|---|
| ADR-32 配置生效口径（保存 + 重启）；C-IB-40；OOS-16；DR-19 A-1 / A-6 | **Superseded by ADR-53 / 54 / 55** | CL-003、REQ-FUNC-014、C-R26-03 | 热生效；"重启后生效"类提示与断言全部改为"保存成功即生效" |
| 基线 §6"图编译一次常驻，运行期不得由任何图外输入改变拓扑" | **Superseded by ADR-54 / 57** | CL-003、REQ-FUNC-011 | 图随版本换新；单个版本内的拓扑仍不可变（快照不可变） |
| ADR-14 约束③（不得提供运行期增删图节点 / 改拓扑入口）；REQ-FUNC-IB-26 ② | **Superseded by ADR-56 / 57**（约束①②保留） | 同上 | "视图零持久化 + 白名单制"保留；草稿副本是显式用户副本，见 ADR-59 |
| ADR-15-R1 规则⑦（生效口径 = 保存 + 重启）及"派生视图仅装配期构造" | **Superseded by ADR-54 / 55**（规则①~⑥保留） | 同上 | 两域各自唯一可写载体不变 |
| ADR-15-R2 / ADR-36（提示词唯一可写载体 + system 位通道） | **Accepted（沿用）**；ADR-36 决定 4 的缓存上界断言 **Amended by ADR-54 ⑤** | F-7 | 通道矫正与"空串传 None"守卫保留 |
| ADR-16 装配期完备性校验与 fail-fast | **Accepted + 口径补注** | ADR-56 | 校验入口扩展为 `validate_two_domains` ∪ `validate_graph`；保存期 / 发布期 / 装配期同一入口（ADR-33 精神）；仍无 force / ignore |
| ADR-17 确认中间态 | **Accepted + 口径补注** | ADR-57 | `confirm` 节点复用其 fail-closed 语义；`SessionState` 追加 `config_version` |
| ADR-30 工具授权最小化 | **Accepted + 口径补注** | ADR-61 | 授权终于在运行期按专家强制（修正 F-4） |
| ADR-33 保存期单校验入口 | **Accepted + 口径补注** | ADR-56 | 入口增加 `validate_graph` 分支 |
| ADR-34 / A11 审计只读、保留待定 | **Amended by ADR-67** | REQ-NFUNC-006、OQ-R26-08=B | 保留 1 年；增版本列；删除经独立维护端口 |
| ADR-35 storage-state | **口径补注** | ADR-55 | 内存态使用内存版本存储，横幅提示不变 |
| ADR-43 每项目专家注册表 | **Amended by ADR-54** | F-3 | ⑥"装配期取首个项目写全局"在运行期路径退役（离线兼容保留） |
| ADR-45 创建期默认种子 | **口径补注** | ADR-58 | 新项目种子 = 规范化默认图（v1 / v2 皆可），首存才产生版本 |
| ADR-47 专家域 fail-closed | **口径补注** | ADR-54 | 编译失败：保持旧快照继续服务（读路径 fail-open 于旧版），首次冷编译失败仍 fail-closed |
| ADR-52 专家节点实显（显示投影） | **Superseded for v2 documents by ADR-56**；v1 文档仍沿用 | OQ-IB-56 被 CL-003 推翻 | 图上节点 / 边即编排的真实结构；专家节点来自专家集合这一条继承（REQ-FUNC-IB-60） |
| OOS-12 / OOS-21 / OOS-24 的编辑部分；C-IB-54 / C-IB-56① | **撤销（登记于 requirements_spec §取代登记）** | CL-003 | — |
| ADR-08 LLM 外发边界 | **口径补注** | ADR-65 | 新增 Builder 类外发，与现有问答同供应商、同口径；外发声明 `describe_egress` 须补 Builder 类别 |
| ADR-11 / ADR-11-R1 SSE 与容量 | **口径补注** | ADR-66 | 试运行是第二类 SSE 长连接，纳入同一 worker 容量预算（M-SA-006） |
| ADR-60 以外的 ADR-21 / 21-R1 / 22 | **口径补注** | ADR-60 | 账号↔项目 N:1 与单一授权真源不变；`users` 增一列 |

### 6.2 影响复核表（基线 ADR 全量逐条；复核口径：ADR-14~17、29~39、43~52 已通读；其余按标题与 Context 抽查，抽查项标 †）

| ADR | 结论 | 说明 |
|---|---|---|
| 01 向量库抽象 †| 不受影响且是应用 | 使用既有 `PointFilter.doc_ids`，端口方法集不变 |
| 02 embedding 形态 † | 不受影响 | 示例句向量经既有冷路径 |
| 03 部署形态（四单元）| 不受影响 | 未新增单元；上线需 ib-web / ib-worker 各重启一次 |
| 04 / 04-R1 多项目隔离 | 口径补注 | `Scope` / collection / FM-1 不变；项目内新增"目录范围"为 agent 级收窄，只会比项目范围更严 |
| 05 原文件持久化 † | 不受影响 | — |
| 06 PDF 许可（禁 PyMuPDF）| 不受影响 | 无新依赖 |
| 07 / 07-R1 台账存储 | 口径补注 | 同一 SQLite、同一手写迁移机制，新增 5 表 2 扩列；仍不用 Django ORM |
| 08 LLM 外发边界 | 口径补注 | 见 6.1 |
| 09 编排骨架业务零依赖 | 不受影响且是应用 | DAG 编译器只拿注入的闭包 / 注册表，不含业务语义 |
| 10 异步入库 † | 不受影响 | — |
| 11 / 11-R1 Web 栈与 SSE | 口径补注 | 见 6.1；`?token=` 纪律对全部新端点有效 |
| 12 OCR † | 不受影响 | — |
| 13 / 13-R2 / 13-R19 检索结果契约 | 不受影响且是应用 | 空范围（0 命中，不查库）与依赖故障（degraded）仍可区分；不新增 `DegradeReason` |
| 14 编辑模型 | 修订（约束③被取代） | 见 6.1 |
| 15 / 15-R1 / 15-R2 | 修订（规则⑦被取代，其余保留） | 见 6.1 |
| 16 装配期 fail-fast | 口径补注 | 见 6.1 |
| 17 确认中间态 | 口径补注 | 见 6.1 |
| 18~20、23~25、27 账户 / 会话 / 口令 / 前端重构 / HTTPS / 限速 † | 不受影响 | — |
| 21 / 21-R1 / 22 账号↔项目、授权真源 | 口径补注 | 见 6.1 |
| 26 迁移 / 种子 / 回滚策略 | 不受影响且是应用 | 迁移 008 沿用同一机制 |
| 28 项目上下文 `X-IB-Project` | 不受影响 | 新端点同样只认服务端结论的项目 |
| 29 提示词主 / 兜底分层 | 不受影响 | 两层合并规则不变 |
| 30 工具授权 | 口径补注 | 见 6.1 |
| 31 FreeArk 对齐（已被 ADR-50 退役）| 不受影响（已退役）| — |
| 32 生效口径 | 取代 | 见 6.1 |
| 33 / 34 / 35 | 口径补注 / 修订 / 口径补注 | 见 6.1 |
| 36 兜底重定位 | 沿用（决定 4 修订）| 见 6.1 |
| 37 项目注册表 | 不受影响 | `reload_projects` 清运行时缓存即可 |
| 38 / 39 LLM Key | 口径补注 | Builder 与问答共用同一 Key；未配置时 `BuilderUnavailable`，不影响启动 |
| 40 账号 CRUD | 口径补注 | 创建账号接口增 `config_level`（必填） |
| 41 `kb_id` 推导 † | 不受影响 | — |
| 42 管理三分（UI 分组非权限）| 不受影响且是应用 | 三档同样由服务端判定 |
| 43 每项目专家注册表 | 修订 | 见 6.1 |
| 44 定义文档目录化 | 不受影响 | 目录布局不变 |
| 45 创建期种子 | 口径补注 | 见 6.1 |
| 46 三专家历史迁移（已退役）| 不受影响（已退役）| — |
| 47 专家域 fail-closed | 口径补注 | 见 6.1 |
| 48 / 49 / 50 / 51 | 不受影响 | 提示词两层 / 种子 / 回填不变；Builder 生成的提示词不写种子资产 |
| 52 专家节点实显 | 取代（仅 v2）| 见 6.1 |

### 6.3 随取代而需要重新基线的既有测试 / 断言（交 GROUP_C / D，PM 知悉）

| 文件 | 断言内容 | 处置 |
|---|---|---|
| `tests/e2e/test_config_restart_effect_r16.py` | "重启后生效"（C-IB-40） | 改为热生效断言 |
| `tests/unit/test_definition_data_layer_r7.py`、`tests/integration/test_definition_config_r7.py` | 拓扑不可编辑 / `field_not_editable` | v1 路径保留；v2 路径新增用例 |
| `tests/unit/test_orchestration_expert_nodes_r21.py`、`tests/e2e/test_rev21_expert_graph_journeys.py` | 显示投影的单 `expert` 展开 | 仅 v1 文档适用，保留 |
| `tests/unit/test_orchestration_edges_consistency.py` | 文档边 ↔ 运行期边一致 | v1 / legacy 路径适用，v2 改为"graph ↔ 编译图一致" |
| `src/frontend/tests/frontend.smoke.test.js` | `ConfigPage` 只读 / "重启后生效"文案 | 随组件拆分更新 |
| `src/scripts/selfcheck.py` | `field_not_editable` 等 | 同步更新；新增 builder 静态规则 |

---

## 7. 开放问题 / ASSUMPTION

> 仍无法替用户决定的产品语义，给出 2–4 个选项并标推荐。均**不阻塞**架构与模块设计：设计中的字段已为每个选项留位，只改默认值或开关。

| ID | 问题 | 选项 | 推荐 | 影响 |
|---|---|---|---|---|
| OQ-R26-A01 | 存量 ops 账号上线时的配置档位 | A) 全部 `manage`（等价今天"能写"）；B) 全部 `edit`（不含回滚 / 授权）；C) 全部 `view`（须管理员逐个授权） | **A** | 迁移 008 的列默认值（`DEFAULT 'manage'`）；C 最安全但上线即影响现有运维 |
| OQ-R26-A02 | agent 之间是否传递输出（数据流语义） | A) 仅控制流：每个 agent 只见用户问题；B) 下游 agent 可见已激活上游 agent 输出（作为"上游材料"，只读、位于 human 位）；C) 逐 agent 可选 | **B**（默认 `with_upstream`；规范化的存量图为 `query_only`，行为不变） | `AgentNodeSpec.input_mode` 默认值；A 下链式 DAG 仅表示顺序 |
| OQ-R26-A03 | `condition` 节点可用的判定谓词集合 | A) `keyword`（按配置关键词匹配用户问题）+ `upstream_degraded`；B) 仅 `keyword`；C) A + 路由层级（`route_tier`） | **A** | 谓词枚举与校验码；无表达式 / 代码节点不变 |
| OQ-R26-A04 | 自评中 LLM 判定项（占 6 分）的复现承诺 | A) 保留，靠持久化缓存保证"缓存期内同分"，缓存失效后可能微差；B) 仅规则项（满分重新分配，完全确定）；C) LLM 项仅作提示、不计分 | **A**（须用户接受残余风险）；若不接受则 **B** | rubric 分值表与缓存表；OQ-R26-14 的"做不到则回议"即此项 |
| OQ-R26-A05 | 单 agent"最大专家步数"的含义 | A) 该 agent 单次执行的工具调用轮数上限（默认 4，范围 1–8），与图级 `route.max_expert_steps`（单次回答命中的 agent 数上限）并存；B) 仅保留图级上限，隐藏 agent 级参数 | **A** | `run_tool_loop(max_iterations)`；AC-008-01 / AC-021-02 的可测口径 |
| OQ-R26-A06 | `confirm`（人工确认）节点挂起态是否要跨重启保留 | A) 进程内，重启丢失即 fail-closed（沿用 ADR-17 / A8）；B) 持久化到台账 | **A** | 与 `IB_SESSION_PERSISTENCE_POLICY` 一致；B 需新表与恢复协议 |
| OQ-R26-A07 | v1 项目首次保存的版本编号 | A) 先写基线版本 1（系统）再写用户版本 2；B) 只写用户版本 1（无基线可回滚）| **A** | US-020 AC-03 "第 1 个版本内容与升级前行为等价"取 A 的读法；B 无法回滚到升级前 |

**ASSUMPTION（无需求依据或无法核实，已在相应 ADR 中标注）**：

| ID | 假设 | 若不成立 |
|---|---|---|
| A-R26-01 | `langgraph` 在 `>=0.2,<2.0` 区间内：节点"收到任一入边消息即 active、同一超步合并执行一次"，且 `interrupt_before` + `MemorySaver` 可用（本机未安装，官方文档页只覆盖前半，见 ADR-57） | 契约测试失败即回到 ADR-57 Option E 之外的备选（自写层调度仍用 LangGraph 节点），或把 `confirm` 节点降级为 v1 不可用（TBD-T34） |
| A-R26-02 | 图规模上限 60 节点 / 200 边、keywords ≤20、exemplars ≤10 | 校验码里的数值改常量即可 |
| A-R26-03 | DeepSeek 在提示词约束下能稳定产出可解析 JSON（未核实 `response_format` 支持，ADR-63） | 增加重试 / 改用 Option C 升级路径 |
| A-R26-04 | `PROMPT_LAYER_MAX_CHARS=20000` 仅是存储 / 交互上界，不保证模型上下文装得下（INF-4） | 目标机按所用模型的上下文窗口重定（TBD-T33） |
| A-R26-05 | 项目内没有目录级访问控制：任一已授权账号都能看到全部资料目录，故 REQ-FUNC-019(b)"发起账号有权访问的目录" = 项目内全部目录 | 若日后引入目录 ACL，`BuilderService` 的目录列表来源改为带 ACL 的查询 |
| A-R26-06 | view 档 ops 账号保留资料库管理能力（`can_manage` 未变） | 产品另行裁决 |

---

## 8. INF-1~6 占位数值的校准口径与新增 TBD

> 纪律沿用基线 §9：目标机数据不得用开发机外推；开发机只做"口径与上界的可复现测量"。

| INF | 开发机可测的口径（离线替身，`IB_OFFLINE_MODE=1`） | 目标机实测（部署阶段校准，列入 TBD） |
|---|---|---|
| INF-1 位置随配置保存 | 往返测试：保存含坐标的文档 → 重新载入坐标逐位一致；仅改位置的发布不改变路由结果（金标 20 题） | 无需目标机数值 |
| INF-2 差异确认 | `diff_snapshots` 对各类变更的清单完整性单测 | — |
| INF-3 热生效 ≤5 s | 公式 `T ≤ 节流间隔 + T_编译 + T_换引用`；开发机用 `FakeEmbedder` 测 30 节点图的 `T_编译`（p50/p95，≥50 次）并核验"节流 1 s + 编译 ≤ 1 s"裕度；两线程模拟"保存进程 / 另一进程"收敛时间 | **TBD-T32**：目标机含真实 `ib-embed` 示例句冷路径的 `T_编译`；100 次抽样提问版本号一致性（AC-014-04）；探针脚本 `src/scripts/hot_effect_probe.py`（只读，部署后运行，输出收敛时间分布） |
| INF-4 提示词 20000 字符 | 测量：最坏发布体积（50 专家 × 2 层 × 20000 全中文字符 ≈ 6 MB UTF-8）下的校验耗时、快照写入耗时、`config_versions` 单版本体积 | **TBD-T33**：目标机 SQLite 写入耗时与 50 版本占盘；所用 DeepSeek 模型上下文窗口与 20000 字符中文提示词的 token 数（决定是否下调上限） |
| INF-5 30 节点 / 60 边 / 300 ms / 2 s | `validate_graph` + `layerize_graph` 在 30/60 与上限 60/200 的耗时（纯函数，目标 ≪ 2 s）；前端纯模型函数（悬停卡片模型、图→表单映射）用 `node:test` 度量 | **TBD-T36**：目标浏览器上悬停出现时延与拖拽帧率（人工 + 浏览器 Performance 记录）；与基线 TBD-T20 / T31 合并观测 |
| INF-6 Builder 60 s | 用"慢响应替身"验证：超时路径在 60 s 内返回、线程池满返回 429；预算拆分 生成 ≤40 s + LLM 判定 ≤12 s + 规则 ≤1 s | **TBD-T38**：真实 DeepSeek 下生成 / 判定调用的时延分布（≥20 次，p95）；据此校准 60 s 与单次重试策略 |

**新增 TBD 汇总**（接续基线 TBD-T31）：

| 编号 | 待测指标 | 关联 |
|---|---|---|
| TBD-T32 | 热生效收敛时延与版本一致性（含冷路径编译） | REQ-NFUNC-001 / 004；ADR-53 |
| TBD-T33 | 快照体积 / 写入耗时 / 提示词 token 上界 | INF-4；ADR-55 / 68 |
| TBD-T34 | `langgraph` 契约测试：超步合并、`interrupt_before` + `MemorySaver`、版本区间（在真实依赖环境，非开发机缺依赖时标 BLOCKED） | ADR-57；A-R26-01 |
| TBD-T35 | `doc_ids` 过滤的集合大小阈值与 Qdrant 过滤开销、`DOC_SCOPE_MAX_IDS` 校准 | ADR-62 |
| TBD-T36 | 画布交互性能（30/60 与上限图） | INF-5；ADR-69 |
| TBD-T37 | `ib-web` 内存：多份编译快照 + 示例句向量 + 后台编译峰值（`MemoryMax=1024M`） | ADR-54 |
| TBD-T38 | Builder 时延分布与重试策略 | INF-6；ADR-63 |
| TBD-T39 | SSE 线程预算：试运行 + 正式问答并发下的 503 / 429 行为（延续基线 TBD-T15） | ADR-66 |

---

## 9. 自检声明

- 每个 ADR 含 Status（均为 Proposed）、Type、REQ 引用；decision 型 ≥2 个候选并逐项对比；constraint-driven 型（ADR-61、ADR-69）写明约束来源与被排除方案。共 17 条：decision 15、constraint-driven 2。
- 引用的现有代码均经 `git grep` / 读码核实（§1.2 逐条给出 文件:行 或符号）；网页事实标注 `[WEB: URL，访问日期]`。
- 画像 P8 禁用项：无 Docker、无 Channels / Redis、无新增 systemd 单元、`langchain-openai <0.3` 保持、无 PyMuPDF、`ib.*` 不 import `ib_embed`、前端无 axios / CDN；部署视图只含画像 P7 中存在的环境（dev / CI / production，无 staging）。
- 本文件无函数体与示例实现；JSON 片段仅为数据格式示意。
- 性能与规模数值全部标 `[ESTIMATE]` / `[ASSUMPTION]` / TBD，未用开发机数据代替目标机。
