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

## 用户偏好与禁止项

## 待验证
