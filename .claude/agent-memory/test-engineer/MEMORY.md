# test-engineer 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-test-engineer/knowledge_base/）迁移并按协议 §M 重新蒸馏；明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。

## 已验证
- [M-TE-001] 分层用例数用 `python -m pytest tests/<层> --collect-only -q | grep -cE '::'` 独立实测，不从全量日志反推；前端冒烟与 selfcheck 是独立层，不并入 Python 三层的算术 — conf 0.8 · 证据 GR-D（R8 / REV-18） · 首见 2026-09 · 命中 3
- [M-TE-002] FLAKE-IB-01：Windows 下 tests/integration/test_ib_embed_wire.py 回环偶发 WinError 10053/10054。治理只在传输助手 `_request_bounded` 对 (ConnectionAbortedError, ConnectionResetError) 有界重试，不碰断言、不 skip；前提是被重试用例幂等（`fail_next_load` 为持续失败）；状态只能标 MITIGATED，不能标 CLOSED — conf 0.8 · 证据 FLAKE-IB-01 · 首见 2026-09 · 命中 2
- [M-TE-003] 上游纯追加新校验后正向基线用例成批失败：先判"夹具陈旧"（只改夹具数据，断言语义不动）还是真实回归（BLOCKED 上报） — conf 0.6 · 证据 D-R8-01 · 首见 2026-09 · 命中 1
- [M-TE-004] 判定 FND 缺陷 CLOSED_VERIFIED 要覆盖三层：纯函数单元边界、跨模块接缝（闸门/端点）、selfcheck 对应项；先读 developer 已写用例，只补缺口 — conf 0.6 · 证据 FND-R7-01 · 首见 2026-09 · 命中 1
- [M-TE-005] 前端没有组件挂载框架，契约断言做法：读源码 → stripComments → 非贪婪正则抽 `export type X = {...}` 或数组字面量；只用来锁"类型无明文字段""导航分组"这类结构事实 — conf 0.8 · 证据 REV-18 前端第 35 例 / KE-DEV-017 同源 · 首见 2026-10 · 命中 2
- [M-TE-006] DDL 按业务域分常量：users/accounts 在 `ACCOUNT_DDL_STATEMENTS`（`DDL_STATEMENTS` 不含 users，`next(...)` 会 StopIteration）；项目表用 `project_registry_ddl_script()`，LLM Key 用 `llm_key_ddl_script()`；迁移幂等验证 = 对 schema 连续 executescript 两次、快照一致 — conf 0.8 · 证据 TC-UNIT-R18-008 · 首见 2026-10-07 · 命中 2
- [M-TE-007] 已知但本轮不修的缺陷用"缺陷冻结"：断言当前坏行为 + 守卫串（修复后会响亮失败），同时登记缺陷；不要 skip、不要放宽断言 — conf 0.6 · 证据 FND-GROUP-D-01（TC-INT-009/041/061） · 首见 2026-09-26 · 命中 1
- [M-TE-009] 运行期新建项目（POST /api/projects）现在应"创建即可用"（ADR-45）：上传与检索都必须成功；旧口径"新建项目上传 403 属交付边界"已被 23a7470 推翻，TC-INT-161 已改 — conf 0.6 · 证据 commit 23a7470 / TC-INT-R19-012 · 首见 2026-10-17 · 命中 1

## 用户偏好与禁止项

## 待验证
