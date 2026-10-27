# requirement-analyst 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-requirement-analyst/knowledge_base/）迁移并按协议 §M 重新蒸馏；FreeArk 项目的条目未迁移。明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。

## 已验证
- [M-RA-002] 用户只给规模/算力档位、未给数值时，不编造性能指标：AC 改写为"在目标机以该量级实测校准后确定"，校准前标未验收；目标机硬件未实测一律记 TBD — conf 0.6 · 证据 INTELBASE-FINALIZE-1（requirements_spec 决策记录 DR-03 附近） · 首见 2026-09-25 · 命中 1
- [M-RA-003] 覆盖缺口补全：既有 REQ 有来源但无 US/AC 承接时，只补 US/AC，不新增 REQ、不改该 REQ 描述，并声明计数不变；涉及既有测试用例归属错误时只在 notes 登记正确归属，不改 test_plan.md — conf 0.6 · 证据 REV-11（US-IB-19/20） · 首见 2026-09-27 · 命中 1
- [M-RA-004] 用户裁决调研"候选点"后，规范化重述为 REQ + G/W/T AC + 新 OOS 行（排除项落进范围外表），不照抄候选文案；用户裁决"纳入 v1"的条目一律 Must Have，分析师自行评定的在 notes 注明 — conf 0.6 · 证据 REV-06（REQ-FUNC-IB-25~27、OOS-10） · 首见 2026-09-27 · 命中 1
- [M-RA-005] 新增 REQ 会让下游文档中的"N 条 REQ-FUNC"计数过期（module_design、implementation_plan 等）：不改他人文件，在 notes 逐条写"文件:行 旧值→新值"，并提示测试计划可能要补新 US 覆盖 — conf 0.6 · 证据 REV-06 · 首见 2026-09-27 · 命中 1
- [M-RA-007] 可视化配置的需求边界：声明式定义先于 UI；UI 只是定义文档的视图（双向 round-trip、非第二真源）；可编辑对象限于节点参数与专家集合，不含运行期增删图节点（LangGraph 图是编译期结构）；配置校验在装配期 fail-fast — conf 0.6 · 证据 GR-A-002 / REQ-FUNC-IB-25~27 · 首见 2026-09-27 · 命中 1
- [M-RA-008] 故事点占位 `[INFERRED — 待开发团队评估]` 属格式字段，不计入需求推断占比；文档中写明该口径，避免门控误判 — conf 0.6 · 证据 INTELBASE-FINALIZE-1 · 首见 2026-09-25 · 命中 1

## 用户偏好与禁止项
- [M-RA-101] 需求定稿 8 项决策与 REV-06"UI 可视化配置纳入 v1"已由用户拍板（见 docs/requirements_spec.md 决策记录），不要重复提问或重新论证；"禁 Docker"是用户推翻分析师推荐的结果 — 来源：用户裁决 2026-09-25 / 2026-09-27

## 待验证
- [P-RA-001] 增量需求含"覆盖/更新/版本"类能力时，先检索基线"范围外"表（本项目基线 docs/requirements_spec.md OOS-07 排除了"同名文档覆盖"），冲突就在本增量约束里登记"取代"关系，基线正文不改 — 自记 2026-10-24 · 证据 intelligentbase-GROUP_A-002（C-06）
- [P-RA-002] 用户用一句"按推荐"关闭一批开放问题后，每条决定都要落到具体 REQ 描述和至少一条可测 AC（含数字/文案示例），并保留"已决问题"表记录答复与落点，不要只改状态 — 自记 2026-10-24 · 证据 intelligentbase-GROUP_A-002（CL-008）
- [P-RA-003] 用户推翻既有裁决时，单设"取代登记"表：被取代条目 | 原口径 | 新口径 | 取代程度（完全/部分/撤销/继承）| 新落点；一条旧决定常牵出多条（需求、OOS、C、DR、旧故事 AC），逐个 grep 出来，旧文档正文不动 — 自记 2026-10-27 · 证据 intelligentbase-GROUP_A-001（REV-26 热生效 + 自由 DAG 推翻 REQ-FUNC-IB-40 / OOS-12 / OOS-16 / OOS-21 / C-IB-40）
- [P-RA-004] "现有能力 vs 诉求"对照表的"不能做什么"必须有代码证据（如 grep 无 tooltip / 事件处理、props 为 false、GET 与 PUT 的权限差异），不凭印象；读权限与写权限分开写 — 自记 2026-10-27 · 证据 intelligentbase-GROUP_A-001（requirements_spec 现状对照表）
- [P-RA-005] 热生效 / 自由编辑类需求的风险清单（保存前校验、进行中会话、版本与回滚、并发冲突、越权、提示词注入、存量项目升级）各落成带可测指标的 NFUNC；业界证据：Copilot Studio 新内容仅对新会话生效，Dify / n8n 文档未说明进行中会话处理 — 自记 2026-10-27 · 证据 agent_orchestration_benchmark.md §3
- [P-RA-006] "AI 生成配置 / agent"类需求拆成：生成 / 适配项目（只取既有工具、范围、白名单取值，越界项进"适配说明"）/ 自评（固定维度、同输入同分）/ 草案确认才生效 / 外发边界；外发边界用植入标记串（canary）在出站载荷中命中数 = 0 来度量，不写"不含敏感数据"这类不可测句 — 自记 2026-10-27 · 证据 intelligentbase-GROUP_A-002（REQ-FUNC-018~022、REQ-NFUNC-014）
