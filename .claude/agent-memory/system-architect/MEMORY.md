# system-architect 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-system-architect/knowledge_base/，含 kb_full_r7 / kb_full_r18 分卷）迁移并按协议 §M 重新蒸馏；明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。

## 已验证
- [M-SA-001] 易变外部依赖一律"窄端口 + 生产适配器 + 内存替身"，同一套端口一致性测试跑两者；承载隔离语义的参数（scope）不设默认值；端口方法集不随需求改，新能力走实现侧扩展；形态开关新增取值（如 http|inproc|fake）时只扩值域、不改键名与默认值，所有形态过同一套一致性测试 — conf 0.8 · 证据 GR-B-002（Django 换框架时端口层零改动） · 首见 2026-09-25 · 命中 7
- [M-SA-002] 本项目 ADR 修订惯例：已锁定选型不在 ADR 里重新论证，ADR 决策下沉到"落地方式"做 ≥2 方案；选型被用户改动时保留原 ADR、追加 `ADR-NN-R1` 修订节并写"结论以 R1 为准"；每轮附全部 ADR 的影响复核表（受影响 / 不受影响 / 待裁决逐条写） — conf 0.8 · 证据 GR-B-002 / GR-B-003 · 首见 2026-09-25 · 命中 6
- [M-SA-003] 无环证明 = 模块编号即拓扑序，每条边 w(A)>w(B)。新工件被低编号模块（如组合根 MOD-IB-23）依赖时不得新开更高编号模块（MOD-IB-27 因此被否），应并入既有模块或把端口下沉到 MOD-IB-01；新服务模块最强论据是"无入边"。v1 只有四个 systemd 单元（ADR-03），新增单元需回 PM — conf 0.8 · 证据 GR-B-003（R7） · 首见 2026-09-25 · 命中 6
- [M-SA-004] 许可登记要含传递依赖（torch/transformers 等逐条、标条件性采纳）；PDF 文本提取与页面渲染是两种能力，渲染用 pypdfium2 — conf 0.8 · 证据 tech_stack.md 许可台账 · 首见 2026-09-25 · 命中 6
- [M-SA-005] 降级契约：`degraded` + `degrade_reason` 枚举 + `elapsed_ms` + `candidate_count`；"依赖故障"与"空结果"取值必须不同；写路径（台账、原文件）fail-closed，读路径依赖 fail-open；WSGI 容量耗尽归 fail-closed 快速 503；增强项不新增 degrade_reason；台账与向量库故障已拆为 LEDGER_UNAVAILABLE / vectorstore_unavailable 两域 — conf 0.8 · 证据 GR-B-002 / commit 8b5755f（ADR-13-R19） · 首见 2026-09-25 · 命中 6
- [M-SA-006] 流式选 SSE（StreamingHttpResponse + 同步 WSGI），凭据只走请求头/体，**全部端点**禁 `?token=`；长连接并发上限 ≈ worker 数，超限快速失败、禁止无界排队；非流式端点不计入 SSE 容量预算 — conf 0.8 · 证据 GR-B-002（ADR-03-R1 / TBD-T15） · 首见 2026-09-25 · 命中 5
- [M-SA-007] 多项目隔离：collection 名只由 `CollectionResolver.resolve(scope)` 单点产生；payload 冗余写项目标识且查询 filter 恒含它（命名错误降级为"查不到"而非泄漏）；新增端点（含只读）一律带 scope，"不存在"与"不属于你"返回同一状态码 — conf 0.8 · 证据 GR-B-002 · 首见 2026-09-25 · 命中 6
- [M-SA-008] 性能未实测时用 `[ESTIMATE]` / `[TBD-Tn]` / `[ARCH-ASSUMPTION-An]` 三类标记；TBD 编号只增不改，悬空引用补定义，暂无内容写"预留未分配"；不得用开发机数据代替目标机 — conf 0.8 · 证据 GR-B-002 · 首见 2026-09-25 · 命中 6
- [M-SA-009] 目标机为较老 x86_64 CPU：onnxruntime / torch wheel 按 AVX2 编译，缺 AVX2 会 SIGILL（进程级、不可捕获、绕过全部降级、开发机测不出）；须目标机最小探针（真 import + 一次真实推理）；OCR 与 embedding 同链路合并评估；长批推理顶爆内存也曾致崩溃，ib-embed 单次库调用批上限 `INFERENCE_SUB_BATCH=4` — conf 0.8 · 证据 TBD-T18 / commit 8b5755f · 首见 2026-09-26 · 命中 2
- [M-SA-010] ib-embed 服务端契约以 docs/ib_embed_service_contract.md 为唯一权威，module_design 只放摘要；错误码不变式：4xx/409 重试无用、5xx 可重试，禁止 200 + 部分结果；客户端已落盘的事实（读 `vectors`、`/embed` 路径）登记为服务端义务，不重新设计 — conf 0.6 · 证据 GR-B（R2，MOD-IB-26） · 首见 2026-09-26 · 命中 1
- [M-SA-011] "不允许的开关"做成类型层事实：`ValidationReport` 只含 ok/errors、无 force/ignore；装配序列首步 `admit` 闸门，失败拒绝启动；装配期 fail-closed 与运行期读 fail-closed 是两个失败面、不冲突 — conf 0.6 · 证据 ADR-16 · 首见 2026-09-27 · 命中 1
- [M-SA-012] 首启死锁：凭据存 DB 且只能经 Web 界面写入，而启动校验缺凭据即 fail-fast → 永远起不来。处置：仅该凭据放宽为"未配置态"，功能路径调用期 fail-closed（错误不含凭据信息），其余必填项仍 fail-fast；供给序登记 OPEN ITEM 交裁 — conf 0.6 · 证据 ADR-39 · 首见 2026-10-07 · 命中 1
- [M-SA-013] 删除且需可恢复、零迁移时：复用既有 status 枚举的 `disabled` 做软删；二次确认 `confirm_*` 不一致 400；"最后一个 admin"类跨行保护放服务层返回 409；不物理级联 — conf 0.6 · 证据 R18（ADR-40 附近） · 首见 2026-10-07 · 命中 1
- [M-SA-014] 新裁决与既有 ADR 表述存在语义张力（如 ADR-21"1:1"vs 1:N 裁决）时，不改写既有 ADR/REQ，复核表判"待裁决"，登记 OPEN ITEM 写明两种解读的影响 — conf 0.6 · 证据 OI-1 · 首见 2026-10-07 · 命中 1
- [M-SA-015] 已批准需求的前置条件尚未落地时，默认判"可登记前置条件，本轮继续"：写进架构假设表 + 开放问题 + "施工前置条件 ≠ 覆盖缺口"声明；只有需求明写阻塞才 BLOCKED — conf 0.6 · 证据 ARCH-ASSUMPTION-A7 · 首见 2026-09-27 · 命中 1
- [M-SA-017] 裁决让既有事实陈述变假时，即使无新依赖也做最小订正（只改那一句及直接衍生句），tech_stack 取补丁位（如 1.4.0→1.4.1） — conf 0.6 · 证据 R18 tech_stack 1.4.1 · 首见 2026-10-07 · 命中 1
- [M-SA-018] 运行期新建项目不在 cfg.projects（ADR-37 之后项目取自注册表）：涉及项目维度的设计要以台账/注册表为准、config 仅回退，并保证"创建即可用"（ADR-45） — conf 0.8 · 证据 commit 8b5755f / 23a7470 · 首见 2026-10-17 · 命中 2
- [M-SA-019] 外部工具与热生效编译快照的衔接：快照只决定"LLM 看得到什么"，"能不能调"每次调用读台账准入（无缓存）；复审通过后 `runtime_cache.refresh_async` 刷新可见内容；悬空授权在 compile 前剔除，避免失效授权使发布失败 — conf 0.8 · 证据 ADR-R29-09 / GR-B-001 / composition.py:691 · 首见 2026-11-05 · 命中 2
- [M-SA-020] 新增工具命名先查"首个点切分"类解析点（`_owner_tool`、selfcheck `split(".")[0]`）：外部工具用无点保留前缀名（`mcp__x__y`）作注册名、点号仅作展示别名，外部规格排除在全局 `known_tool_param_specs()` 之外，既有断言不改 — conf 0.8 · 证据 ADR-R29-02 / GR-B-001 / mcp/rules.py:55 · 首见 2026-11-05 · 命中 2
- [M-SA-021] 评估"引入第三方协议 SDK"先看三点：同步/异步模型、HTTP 层能否注入钉 IP 连接（SSRF）、传递依赖体量；MCP 官方 `mcp` 2.x 以 asyncio 为主且依赖面大，故选自写最小同步客户端 + 端口隔离 — conf 0.6 · 证据 ADR-R29-03/06、GR-B-001/002 · 首见 2026-11-05 · 命中 2
- [M-SA-022] "已是传递依赖"只对声明它的环境成立：用 `pypi.org/pypi/<包>/<版本>/json` 取固定区间两端核依赖链，并注明开发 venv / requirements-offline.txt 可能没有（cryptography 经 pdfminer.six 只在生产 venv 是传递依赖，对其余环境是新增） — conf 0.8 · 证据 GR-B-001-F02→GR-B-002 SATISFIED / A-R29-3 · 首见 2026-11-05 · 命中 2
- [M-SA-023] 生产有、开发机缺的可选依赖：库内延迟导入 + 仅离线可构造的端口替身（工厂放组合根以免成环）+ 真实实现契约测试用 importorskip + CI 作业级 `IB_REQUIRE_CRYPTO=1` 使缺包即失败而非 skip — conf 0.8 · 证据 ADR-R29-17 / ci.yml:54 / GR-C-003 条件(1) / GR-D-003-F03（本机 6 SKIP） · 首见 2026-11-05 · 命中 2
- [M-SA-024] 官方规范 schema 页超过 WebFetch 单次窗口，字段定义常在后半段，需 offset 续取并逐字引用；MCP ToolAnnotations 缺省 destructiveHint=true、readOnlyHint=false，故仅显式 destructiveHint=true 推定 side_effect、永不推定 read_only（mcp/rules.py:178） — conf 0.6 · 证据 GR-B-002 / IFC-R29-013 · 首见 2026-11-05 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-SA-001] 需要"旧版持续可检索、新版成功后一次性切换"时，不要在向量库里翻转可见性（非原子且要新端口方法）：新版写成隐藏的修订行，台账单事务晋升，检索对命中做"台账存活过滤 + 当前名称/路径回填"；重命名/移动因此零向量操作 — 自记 2026-10-24 · 证据 docs/sdlc/intelligentbase/architecture_design.md ADR-004/005（设计阶段，待实现验证）
- [P-SA-002] "单次 N 个文件 × 单文件上限"与单请求体上限冲突时，用"清单计划 + 逐文件 PUT 的批次会话"替代调高 nginx/Django 上限：免用户 reload nginx、失败按文件隔离；总大小上限用服务端比对"实际≤声明、声明和≤上限"保证，无需额外计数器 — 自记 2026-10-24 · 证据 architecture_design.md ADR-003（待验证）
- [P-SA-003] 唯一性靠"应用侧 casefold 键列 + 部分唯一索引 + BEGIN IMMEDIATE 内先检后写"；SQLite NOCASE 只折叠 ASCII；历史重名行回填时给后到者的键追加 doc_id 后缀而不改显示名，且回填必须先于唯一索引创建 — 自记 2026-10-24 · 证据 architecture_design.md ADR-002/009（待验证）
- [P-SA-004] 设计"热生效/按角色权限"前先读运行期实绑：本项目 `bind_tools` 把项目授权并集发给每个专家、运行期仍读进程级 `ib.experts` 全局（首个项目覆盖），保存期校验过的"按专家授权"并未在运行期强制；先核实再写需求覆盖 — 自记 2026-10-27 · 证据 composition.py:340、tools/__init__.py:364-411、orchestration/__init__.py:1115（待验证）
- [P-SA-005] LangGraph 自由 DAG 的"汇聚=等全部实际被激活上游"：不用 `add_edge([..])`（未激活分支会死等）也不依赖 `defer`（版本区间内未核实），改用"最长路径分层 + 跨层边插中继节点"，使每条边恰跨一个超步；须有真实 langgraph 的契约测试 — 自记 2026-10-27 · 证据 architecture_design.md ADR-57（设计阶段，待实现验证）
- [P-SA-006] 云端外发边界做成类型层事实：载荷由固定字段的 dataclass 构造（无会话/资料正文/账号字段）+ 唯一出站函数 + 先写审计后发送（审计失败不发送）+ selfcheck 禁止该包 import 检索/向量/blob — 自记 2026-10-27 · 证据 architecture_design.md ADR-65（待验证）
- [P-SA-007] 前端无挂载环境时，把删除/确认/撤销决策抽成"仅 import type + 必要时 ./graphModel"的纯 TS 模块，供 node:test 用 transpileModule + data: URL 加载（相对导入需替换说明符，含 `vue` 的 store 无法这样加载，只做源码断言）；撤销用"整份草稿快照 + 当前快照===删除后快照"判有效，免逐入口清除 — 自记 2026-10-31 · 证据 architecture_design.md ADR-R27-02/03（设计阶段，待实现验证）
- [P-SA-008] 设计"删除 X"类 UI 前先核服务端保存路径对关联文件的真实处置（本项目 publish.py:333-335 删被移除专家的提示词层文件，版本快照可回滚），据此定确认文案，而不是改服务端语义 — 自记 2026-10-31 · 证据 module_design.md §GR-A-001(a)（待验证）
- [P-SA-009] 本项目 route 节点在候选集内几乎必有命中（IntentRouter 兜底到默认/首个候选，intent.py:367-373），`__else__` 只在候选空/异常时出现；要"不委托"的旁路必须用显式回合状态（route_skip）让 make_route 直选 `__else__`，不能指望分类器自然落到 else — 自记 2026-11-02 · 证据 architecture_design.md ADR-R28-01（待验证）
- [P-SA-010] `_strip_internal_labels` 对终稿做全文子串删除所有专家 cn_label（orchestration/__init__.py:1325）；新增"面向用户的出口专家"时须把它自己的标签从清洗集剔除，否则"顾问"等常用词被删字；`_aggregate` 单叶子直通，所以出口 agent 成为唯一叶子即可避免二次改写 — 自记 2026-11-02 · 证据 ADR-R28-01（待验证）
- [P-SA-011] 工具参数机制里配置值是 partial 默认值、LLM 同名实参优先，且 properties 会原样发给 LLM（tools/__init__.py:463、llm/__init__.py:596）；超时/名单/上限这类"平台限制"必须走 ToolSpec 新增的 config_parameters + "配置胜出"包装，否则模型可覆盖 — 自记 2026-11-02 · 证据 ADR-R28-06（待验证）
- [P-SA-012] 用户否决"失败回退展示子 agent 原答"时：让汇总节点自己在失败路径产出一个非降级的致歉结果（并写 outputs），则上游不再是叶子、"默认专家直答"安全网也不会触发，无需改 _collect；致歉文案做成不可配置常量（配置内容无法证明不含内部名） — 自记 2026-11-02 · 证据 architecture_design.md ADR-R28-09 v1.1.0（设计阶段，待实现验证）
- [P-SA-013] 复用 LLM Key 去调同一服务方的其他端点：Key 解析点只有一个（DB 优先 → 兼容 env 回退，装配期读一次），生效语义是"保存 + 重启"，所以不做搜索单独热读；端点写成常量（不留 BASE_URL 键，Key 只会发往固定主机）并校验 LLM base_url 主机，防止把别家 Key 发给该服务方；同时删掉第二份密钥键 — 自记 2026-11-03 · 证据 architecture_design.md ADR-R28-11（设计阶段，待实现验证）
- [P-SA-014] 比较"服务端抓取 API vs 本地抓取"先拿响应字段对既有需求逐条核：DeepSeek Fetch 响应无最终网址、404 把五类失败合一、重定向与内网处置资料未写，这些缺口直接决定方案；资料没写的安全行为不能用"保守缺省"代替证据 — 自记 2026-11-03 · 证据 architecture_design.md ADR-R28-12（待验证）
- [P-SA-015] 用户裁决要求"确认某 ADR 与新裁决一致"时必须对照已落地实现：本轮 ADR-R28-09 文字写"联网结果也抽保护片段"，而 dag.py:348-360 早已按裁决只核被委托产出；以 R1 订正文档而不是改代码，并在复核表标"受影响" — 自记 2026-11-03 · 证据 architecture_design.md ADR-R28-09-R1（待验证）
