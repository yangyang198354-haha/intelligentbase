# kb-curator 项目记忆 — intelligentbase

## 已验证
- [M-KC-001] 本项目旧版（TRAE 套件）知识库位于 .trae/skills/*/knowledge_base/，已于 2026-10-24 全部审阅并迁移到各 agent 记忆（迁移日志 project_workspace/_kb_distillation/log.md）；之后不再作为输入，除非用户要求复查 — conf 0.6 · 证据 distill_20261024T1624.md · 首见 2026-10-24 · 命中 1
- [M-KC-002] 旧 kb_full.xml 有 4 份不是合法 XML（devops、requirement-analyst、system-architect 主卷与 r18 卷），需要读取时按 `<knowledge_entry>` 正则抽取，不要依赖 XML 解析 — conf 0.6 · 证据 本次迁移实测 · 首见 2026-10-24 · 命中 1

## 用户偏好与禁止项

## 待验证
