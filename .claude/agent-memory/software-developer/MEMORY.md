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
