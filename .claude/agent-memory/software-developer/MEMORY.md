# software-developer 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-software-developer/knowledge_base/）迁移并按协议 §M 重新蒸馏；明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。

## 已验证
- [M-SD-001] `log_event(stage, outcome, **extra)`：outcome 是第二个位置参数，不要再放进 extra（TypeError 被上层吞掉 = 审计静默丢失）；extra 只带 `LOG_FIELDS` 白名单字段，白名单外静默丢弃，修复用精确加键名，不改成前缀/正则 — conf 0.8 · 证据 GR-C-015 / DEFECT-R19-D-01 · 首见 2026-10 · 命中 2
- [M-SD-002] IFC 指定了落点模块的契约要在该模块实现：新配置键名登记到 `ib/config` 的 `IB_RUNTIME_ENV_KEYS`，只在消费点 `os.environ.get` 不算实现；交付前逐条把 IFC 映射到文件 — conf 0.6 · 证据 IFC-IB-312（implementation_plan §19） · 首见 2026-10 · 命中 1
- [M-SD-003] 端口 Protocol 的方法集不改（如 AccountStore）；新内部能力加在具体实现上，内存替身提供同签名，偏差在 implementation_plan 偏差表登记（先例 `upsert_chunks`、`revoke_sessions_for_user`） — conf 0.6 · 证据 D-R13-02 · 首见 2026-10 · 命中 1
- [M-SD-004] 兼容扩展：新接缝用可选关键字参数、默认 None 与原行为逐字相同（先例 `related_images_provider`、`confirmation_prompt_builder`）；设计字段集与既有实现冲突时既有字段逐字保留、新字段给默认值，冲突登记为设计缺口交 PM — conf 0.8 · 证据 GAP-R11-01 / selfcheck 确认门断言 · 首见 2026-09-27 · 命中 2
- [M-SD-005] 已有一次性装配守卫（`_installed`）不放宽，另加独立幂等入口（先例 `install_derived`） — conf 0.6 · 证据 src/ib/experts/__init__.py · 首见 2026-09-27 · 命中 1
- [M-SD-006] 向校验器追加新校验用全新错误码（先例 `expert_keyword_duplicate`），追加在既有项之后；既有测试里有"某码不出现"的护栏，复用旧码会误伤；旧兜底 `validate_specs` 保留 — conf 0.6 · 证据 TC-UNIT-062/065 · 首见 2026-09-27 · 命中 1
- [M-SD-007] 恢复/续跑判定写成纯函数（`can_resume`）便于离线穷举；端点的全部前置检查在开流之前，失败显式 4xx/5xx，绝不退化为"新建会话重跑"；残缺载荷视为未携决策，不补成默认批准 — conf 0.6 · 证据 REV-11 selfcheck · 首见 2026-09-27 · 命中 1
- [M-SD-008] "退场旧标识 grep 归零"测试按子串匹配：注释里不要复述退场字面量；新默认值不要撞退场标签（内置 kb-agent 取"知识库助手"而非已退场的"知识库问答"） — conf 0.6 · 证据 ADR-31 · 首见 2026-10 · 命中 1
- [M-SD-009] Windows 上 TemporaryDirectory + SQLite：with 体内显式 close 连接并用 `ignore_cleanup_errors=True`，否则 WinError 32 会盖住真实断言失败；扫库要覆盖 main / -wal / -shm 三个文件 — conf 0.6 · 证据 r13_account_store_parity · 首见 2026-10 · 命中 1
- [M-SD-010] "某字符串不得出现"类源码纪律断言：先剥离注释，断言结构（`<input`、`setToken(`、`type="password"`）而非自然语言词 — conf 0.8 · 证据 REV-13 自检 / KE-TEST-007 同源 · 首见 2026-10 · 命中 2
- [M-SD-011] 前端 CI 失败常有多个独立根因（lock 未同步、文件未 git add、`noUnusedLocals` 报 TS6133）：修一处后跑完整流水线（npm ci → build → test）直到全绿 — conf 0.6 · 证据 R10 · 首见 2026-09 · 命中 1
- [M-SD-012] 前端测试入口保持 `node --test` 无参数：Node 24 传目录会 MODULE_NOT_FOUND，Node 20 不支持 glob；dist/ 不入库，内容断言以"目录存在"为前置 — conf 0.6 · 证据 R10 · 首见 2026-09 · 命中 1
- [M-SD-013] 锁文件完整性用 `npm ci` 证明；新回归断言要做负向对照（用 `git show HEAD:<旧 lock>` 跑一次应失败），证明不是空转断言 — conf 0.6 · 证据 R10 · 首见 2026-09 · 命中 1
- [M-SD-014] 前端传递依赖许可登记：实读 `node_modules/<pkg>/package.json` 与 LICENSE 文件，嵌套包按路径逐处登记，写解析到的精确版本 — conf 0.6 · 证据 tech_stack.md §2.1 · 首见 2026-09 · 命中 1
- [M-SD-015] 运行期新建项目不在 cfg.projects：读路径以台账/注册表为准、config 仅回退；新建项目须幂等补台账行（先 upsert_project 再 upsert_kb，顺序不可换），装配期与 reload_projects 各调一次 — conf 0.8 · 证据 commit 8b5755f / 23a7470 · 首见 2026-10-17 · 命中 2
- [M-SD-016] docs/ 文档 `<file_header>` 内禁裸 `<` `>`（写 `&lt;` `&gt;`）；改头后抽出该块用 `ET.fromstring` 校验；code_review_report 用 Markdown 表头时如实写"ET 解析不适用" — conf 0.8 · 证据 GR-C-002 / KE-PM-025 同源 · 首见 2026-09-26 · 命中 2
- [M-SD-017] src/deploy/checklists.txt 新增 `[Bn]` 检查项时，同步改 selfcheck 签署行断言（B1–Bn）；REV-21 漏改导致 selfcheck 51/52 — conf 0.6 · 证据 commit 4f4ad5e · 首见 2026-10-17 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-SD-001] 检索接入“台账存活过滤”后，凡是直接 upsert 向量点而不建台账行的夹具（selfcheck `isolation_scope_required` 的 d1）会被判不存活而召回 0；夹具需补一条存活台账行，并成对断言“全不存活=不降级且空 / 解析故障=LEDGER_UNAVAILABLE” — 自记 2026-10-24 · 证据 selfcheck retrieval_happy_path 改动前失败
- [P-SD-002] 给端口 Protocol 已有方法加可选关键字参数时，同步改 `ib/core/ports.py` 的签名，否则 selfcheck `port_conformance`（按参数名集合比对）会失败；新增响应键（如 doc_path）要同步 selfcheck/测试里按“精确键集”的断言 — 自记 2026-10-24 · 证据 list_documents(include_revisions)、related_images 键集
- [P-SD-004] 想验证“修复前行为”时，不要对工作区文件 `git stash`（会连同未提交的其他增量一并收走）；改用测试内 `monkeypatch` 把新增的模块级常量置回旧值重放 — 自记 2026-10-24 · 证据 DEF-R25-001 修复轮（REDIRECT_REBUILD_STATES）
- [P-SD-005] LangGraph 汇聚：边跨层不等时汇聚节点会被触发多次，必须“最长路径定层 + 跨层边插无操作中继”才恰好一次；检查点(MemorySaver)状态里放自定义 dataclass 会触发“Deserializing unregistered type”将被阻断的告警，状态只放原语 dict — 自记 2026-10-27 · 证据 tests/integration/test_langgraph_contract_r26.py（含反证用例）
- [P-SD-006] 给 ConfigAuditEntry / UserRecord / users 表这类已有“字段集或列集精确断言”的结构追加字段，会让 test_TC_UNIT_125、test_TC_INT_122 失败；追加前先 grep 这类断言，调整时只放行已登记的追加名（如 USERS_ADDED_COLUMNS） — 自记 2026-10-27 · 证据 REV-26 MOD-R26-06
- [P-SD-007] 测试里常用 `OpenAiCompatibleProvider.__new__` 绕过 `__init__` 并手设 `_clients={}`：给该类加新实例属性/改容器类型时用 getattr 默认值与 hasattr 兜底，否则 test_prompt_system_slot_r17 两例失败 — 自记 2026-10-27 · 证据 llm 有界 LRU 改动首轮失败
- [P-SD-008] 给组合根装配的服务传存储时用“按调用时解析”的代理（如 `_LiveDefinitionStore`）而非装配期捕获实例：离线/测试会整体替换 `deps.definition_store`，捕获旧实例会写到无人读取的存储 — 自记 2026-10-27 · 证据 REV-26 发布服务首轮 e2e 失败
- [P-SD-009] 版本时间戳必须与存储里 `_age_s` 解析格式一致（`utc_now_iso` 的 `Z` 定长）；格式不符会被判“永远陈旧”而误回收他人的 pending — 自记 2026-10-27 · 证据 ledger/config_versions.py `_age_s`
- [P-SD-010] 精确键集断言的既有契约测试（GET definition / 审计项 / SSE done 数据）在加字段前先 grep；能不动线上契约就不动（done 仅试运行带版本），必须动的逐条在计划里登记取代依据 — 自记 2026-10-27 · 证据 REV-26 重新基线 8 处
- [P-SD-003] 无 django/pytest 的机器上，可在 scratchpad 放 stub 的 rest_framework/django.http + 假 request 对象驱动视图函数做冒烟（不入库、不算测试），能抓出序列化/错误映射类缺陷；PUT multipart 解析等 Django 特有路径仍须标未验证 — 自记 2026-10-24 · 证据 library_views 冒烟
- [P-SD-011] 回合级上下文（预算 / 审计主体）若要被 `_execute_tool` 看门狗线程池里的工具读到，必须用 `contextvars` + `copy_context().run` 提交；`threading.local` 在池线程里不可见 — 自记 2026-11-02 · 证据 REV-28 联网路径冒烟（顾问节点内工具预算 / 私有语料可见）
- [P-SD-012] 新增依赖 `ledger_backend` 的存储构造器要“跟随台账后端 memory ⇒ 内存替身”（同 `build_config_audit_store`），否则离线夹具（`ledger_path=./var/ledger/…`）装配期 `unable to open database file` — 自记 2026-11-02 · 证据 REV-28 首轮全量 pytest ERROR（build_web_governance_store）
- [P-SD-014] stdlib urllib 要“不跟随重定向”：`build_opener()` 总会补默认 HTTPRedirectHandler，应手工 `OpenerDirector` 只加 Proxy/HTTP/HTTPS/HTTPDefaultErrorHandler/HTTPErrorProcessor，3xx 经 HTTPError 取 `.code`、不读错误体；用 `[type(h).__name__ for h in opener.handlers]` 核对无 Redirect 处理器 — 自记 2026-11-03 · 证据 REV-28 deepseek.py 回环冒烟
- [P-SD-015] 离线夹具（IB_OFFLINE_MODE=1）下 `_offline_view` 把搜索提供方整体置 fake，依赖“登记自定义提供方 + 非离线 Key 流向”的集成断言失效；Key→请求头→不入日志要直接用 `DeepSeekSearchProvider + FakeDeepSeekTransport.requests` 验证 — 自记 2026-11-03 · 证据 test_TC_INT_R28_223 改动
- [P-SD-013] 全局工具登记点新增工具会改变“可授权工具 / 参数规格”断言：先 grep `available_tools`、`known_tool_names`、`known_tool_param_specs` 的测试与 selfcheck（REV-28 共 4 处测试断言 + 2 处 selfcheck 断言），只放行新增前缀、保留 `search_knowledge.*` 精确断言 — 自记 2026-11-02 · 证据 REV-28 AQ3=A
