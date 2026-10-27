# pm-orchestrator 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-orchestrator/knowledge_base/）迁移并按协议 §M 重新蒸馏；迁移明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。

## 已验证
- [M-PM-001] fail-open / 降级路径的用例必须与 happy-path 正例成对（正例断言"不降级且有命中"）：检索层曾把 NameError、KeyError 吞成 degraded，原降级用例照样 PASS。门控时确认反向正例存在（selfcheck `retrieval_happy_path` 即此用途） — conf 0.8 · 证据 GR-C-002 / commit 8b5755f · 首见 2026-09-26 · 命中 2
- [M-PM-002] 防注水检查（generic/pm-orchestrator.md）之外，本项目还要查"翻转忠实性"：缺陷冻结用例翻转为正向断言后，强度不得低于缺陷原描述（例：删除缺陷翻转后须同时断言 2xx、台账行消失、检索为空、再删 404） — conf 0.8 · 证据 GR-D-001 / GR-D-002 · 首见 2026-09-26 · 命中 2
- [M-PM-003] 断言 500 / 空串 / degraded 的用例先别判为写错：若带守卫串（如"偏差已消除——请更新缺陷登记"）且对应已登记缺陷，属"缺陷冻结"；无守卫串也无登记才追问是否断言退化 — conf 0.6 · 证据 GR-D-001 / FND-GROUP-D-01 · 首见 2026-09-26 · 命中 1
- [M-PM-004] "永不抛异常 / 审计失败非致命"类契约，必须存在覆盖该失败分支的用例，否则门控记为未证；函数内局部 import 导致的 NameError 曾因旁路分支无用例漏到 GROUP_D — conf 0.6 · 证据 TC-INT-147 · 首见 2026-10 · 命中 1
- [M-PM-005] 缺陷修复轮只改实现、不改测试断言（测试文件被改则不采信其转绿）；增量门控只 bump 实际改动层的版本，并把上游指向该缺陷的条件追加式改为 CLOSED — conf 0.6 · 证据 GR-C-015 / DEFECT-R19-D-01 · 首见 2026-10 · 命中 1
- [M-PM-006] 计划/设计修订后必须 grep 下游执行产物（src/deploy/checklists.txt、systemd unit、ci.yml）逐一同步，否则"计划改了、执行不变"；端口、路径、落点以 unit 文件为真源（18080 是 ib-web Waitress 回环口，nginx 对外端口不得复用） — conf 0.6 · 证据 GR-E-002 · 首见 2026-09 · 命中 1
- [M-PM-007] 历史报告正文里保留的旧结论是留痕不是缺陷；在用交付物（checklists、unit、env 模板、运维说明）里的陈旧描述才是缺陷；契约散文与字段级定义冲突时以字段级定义为准，登记散文缺陷 — conf 0.6 · 证据 GR-C-002 · 首见 2026-09-26 · 命中 1
- [M-PM-008] 改动全局计数 / 版本号 / status 后，全文 grep 旧值：现时态陈述就地同步，历史轮次陈述保留（必要时加"该轮口径"） — conf 0.6 · 证据 GR-A-005 · 首见 2026-09-27 · 命中 1
- [M-PM-009] docs/ 下设计/实现文档只有开头的 `<file_header>` 是 XML：校验时抽出该块单独解析（整文件解析在正文处失败属正常）；头内 rev-note 历史叙述常混入裸 `<` `>`（如 `bcrypt>=4,<5`），改头时连同既有文本一起扫 — conf 0.8 · 证据 GR-C-002 / KE-DEV-019 同源 · 首见 2026-09-26 · 命中 2
- [M-PM-010] 运行期新建项目（POST /api/projects）不在 cfg.projects：任何硬取 cfg.projects[pid] 或只按配置播种台账的路径都会坏（KeyError 被吞成降级 / 上传恒 403）。项目维度改动的门控要核对"台账/注册表为准、config 仅回退" — conf 0.8 · 证据 commit 8b5755f / 23a7470 · 首见 2026-10-17 · 命中 2
- [M-PM-011] 退役某机制后前端可能残留僵尸区块与自相矛盾文案（REV-20 退役"代码内置兜底"后配置页仍渲染该区块）；门控退役类改动时 grep 前端模板中的旧名称 — conf 0.6 · 证据 commit d46b181 / FND-REV24-01 · 首见 2026-10-17 · 命中 1
- [M-PM-012] "需求补充调研"类任务归 GROUP_A 增量：新建调研文档、不改 APPROVED 需求；对本项目只出"候选点"，用户裁决后再由 requirement-analyst 定向修订落为正式需求；"无对应 REQ"是需求级缺口，交用户裁决 — conf 0.6 · 证据 GR-A-002 · 首见 2026-09-27 · 命中 1
- [M-PM-013] selfcheck 的 stderr 里出现 `code=internal_error` / `Service Unavailable` 不一定是失败（被测代码故意走坏路径的设计内日志）；`2>/dev/null` 复跑后 PASS 行与总计不变即非失败 — conf 0.6 · 证据 GR-C-002 · 首见 2026-09-26 · 命中 1
- [M-PM-014] UI 可见改动部署后，以用户 UI 复核确认作为 E2 条件闭合依据（PASS_WITH_CONDITIONS → PASS） — conf 0.6 · 证据 GR-E-010 · 首见 2026-10-17 · 命中 1

## 用户偏好与禁止项
- [M-PM-101] 需求定稿 8 项决策（Qdrant、bge-m3、禁 Docker 全裸装、保留云端 DeepSeek、单实例多项目、支持索引重建、v1 含 OCR、PyMuPDF 不得以"内部使用"豁免）与 REV-06"UI 可视化配置纳入 v1"均已由用户拍板，不要重复询问；"禁 Docker"推翻了分析师的折中推荐 — 来源：用户裁决 2026-09-25 / 2026-09-27（docs/requirements_spec.md 决策记录）

## 待验证
- [P-PM-001] 缺陷修复改了被多处复用的判定函数（如 rebuild `_target_of`）时，门控须 grep 全部调用方评估副作用：扩大重定向状态集同时让 start_rebuild 在 succeeded 未激活时拒绝新重建 — 自记 2026-10-24 · 证据 GR-C-002-F01
- [P-PM-002] 新轮次（REV-NN）的调用号须带修订号前缀（intelligentbase-R26-GROUP_A-001），否则与上一轮收件箱 id 撞号、hook 记录无法区分 — 自记 2026-10-27 · 证据 GR-A-001/GR-A-002(REV-26)
- [P-PM-003] special_instructions 中把用户原话与 PM 转述分开标注；门控核对子代理标"用户原话"的引号内容确实出自用户消息 — 自记 2026-10-27 · 证据 GR-A-002-F01(REV-26)
