# TRAE 智能体套件复刻方案

## Context（为什么做）

工作区 `.claude/agents/` 下存在一套完整的 SDLC 多智能体套件（7 个 agent + 共享协议 + 6 份知识库）：

| agent | 拥有阶段 | 产出文件 |
|---|---|---|
| pm-orchestrator | 编排 + 门控 | `docs/phase_status.md`、`docs/delivery_report.md` |
| requirement-analyst | PHASE_01-02 | `docs/requirements_spec.md`、`docs/user_stories.md` |
| system-architect | PHASE_03-04 | `docs/architecture_design.md`、`docs/module_design.md`、`docs/tech_stack.md` |
| software-developer | PHASE_05-06 | `docs/implementation_plan.md`、`src/**`、`docs/code_review_report.md` |
| test-engineer | PHASE_07-09 | `docs/test_plan.md`、`docs/test_report.md` |
| devops-engineer | PHASE_10-11 | `docs/cicd_pipeline.md`、`docs/deployment_plan.md`、`docs/deployment_report.md` |
| agent-builder | 元代理（生成/优化 agent） | — |

用户目标：**在 TRAE 中复刻一套可运行的等价套件，并全量测试验证其可行**。

## 关键事实与硬约束（勘查结论）

1. `.claude/agents/*.md` 是 **Claude Code 专有格式**：frontmatter 带 `tools` / `model` / `color`，编排依赖 Claude Code 的 `Agent` 工具（`subagent_type`）。TRAE 不能直接加载这 7 个文件。
2. TRAE 的**文件级可加载扩展点 = Skills**：全局位于 `~/.trae-cn/skills/<name>/SKILL.md`（已实测该目录与 `skill-config.json` 存在）；项目级位于 `.trae/skills/`（本方案的计划文件本身就落在 `.trae/documents/`，佐证 `.trae/` 是 TRAE 的项目配置目录）。
3. `SKILL.md` frontmatter 仅 `name` / `description` / `metadata` —— **没有 `tools` / `model` 字段**。因此原 frontmatter 的 `tools`/`model`/`color` 必须剥离，改由「智能体注册包」承载。
4. TRAE 的**智能体（Subagent）由 UI 面板创建**（开关「可被其他智能体调用」），工作区内**不存在**对应的文件定义 → **我无法程序化创建/注册 TRAE 智能体**，只能产出注册包供用户手动录入。
5. 新增 skill 在**会话启动时**加载 → 本次会话无法即时调用新建 skill，端到端跑通需**新会话**（或应用重启）。
6. 因此「全量测试」拆为两层，如实区分：
   - **产物级（本方案可自动跑通）**：契约/结构校验夹具（pytest）。
   - **运行级（需新会话 + 用户实测）**：文档化的端到端验收流程与判据。

## 方案总览（推荐：Skills 为主 + 智能体注册包为辅 + 契约测试夹具）

### 交付物 1：TRAE Skills 套件（主，文件可加载、会话内可调用）

落盘到工作区 `c:\Users\胖子熊\MyProject\intelligentbase\.trae\skills\`（项目级 skill，随仓库走），
并附一条「安装到全局」的命令（复制到 `~/.trae-cn/skills/` 供跨项目使用）。

```
.trae/skills/
├── sdlc-orchestrator/SKILL.md          # PM：阶段编排 + 门控 + phase_status + 升级/回滚
│   └── knowledge_base/{kb_index.md, kb_full.xml, kb_distillation_log.md}
├── sdlc-requirement-analyst/SKILL.md   # PHASE_01-02
│   └── knowledge_base/...
├── sdlc-system-architect/SKILL.md      # PHASE_03-04
├── sdlc-software-developer/SKILL.md    # PHASE_05-06
├── sdlc-test-engineer/SKILL.md         # PHASE_07-09
├── sdlc-devops-engineer/SKILL.md       # PHASE_10-11
├── sdlc-shared-protocol/SKILL.md       # 共享协议（Block A-K：目录/头/阶段/状态码/门控标准）
└── sdlc-agent-builder/SKILL.md         # 元代理：生成/优化 agent 提示词
```

**复用策略（关键，避免重写）**：每个 skill 的正文**直接搬运**对应 `.claude/agents/*.md` 的九层结构正文，
仅做三处机械变换：
1. frontmatter：删除 `tools`/`model`/`color`，保留 `name`（改为 `sdlc-*`）+ 中文 `description`。
2. KB 路径：`.claude/agents/knowledge_base/<dir>/` → 该 skill 目录下 `knowledge_base/`。
3. 工具语义映射：`Agent` 工具 / `sub_agent_invoke` → 「调用 `sdlc-*` skill」的指令（说明处标注机制差异）。

已有知识库内容（pm_orchestrator ~34 条、system_architect 已拆 r7/r18、其余 6~21 条）**原样迁移**。

### 交付物 2：智能体注册包（辅，解锁真正的 Subagent 编排）

```
.trae/agent-packs/
├── README.md                 # 录入步骤：智能体管理面板 → 新建 → 粘贴 → 开「可被其他智能体调用」
├── 01-pm-orchestrator.md     # 提示词正文 + 配置块（name/description/tools/model/可被调用）
├── 02-requirement-analyst.md
├── 03-system-architect.md
├── 04-software-developer.md
├── 05-test-engineer.md
├── 06-devops-engineer.md
└── 07-agent-builder.md
```

每个文件 = 可直接粘贴的提示词 + 一张 `配置` 表（工具集、模型、是否作为子智能体），
使 TRAE 的「主 Agent 按 description 自动委派 Subagent」机制可原生运行，等价还原 PM→子代理 编排。
`tools`/`model`/`color` 从原 frontmatter 转写到此配置表。

### 交付物 3：契约测试夹具（全量测试的自动化部分）

```
tests/agents/test_sdlc_suite_contract.py
tests/agents/conftest.py
```

断言项（对本轮产物做「全量」结构校验）：
- 8 个 `SKILL.md` 均存在、frontmatter 合法（`name` == 目录名、`description` 非空、无 `tools`/`model` 残留）。
- `sdlc-orchestrator` 正文覆盖：11 个 PHASE、5 个 GROUP、门控 PASS/FAIL 标准、升级（retry≥2）、`PRODUCTION_DEPLOY_CONFIRM` 用户授权规则。
- 每个角色 skill 声明其**拥有阶段**与**产出文件**，且与 `sdlc-shared-protocol` 的目录/编号约定（REQ-/US-/AC-/ADR-/MOD-/IFC-/TC-）一致。
- 6 组知识库目录齐备：`kb_index.md` / `kb_full.xml` / `kb_distillation_log.md` 均存在且非空。
- 全仓无遗留 `.claude/agents/` 硬编码引用（防漏改）。
- 注册包 7 个文件均含「配置」块且字段完整。

运行：`python -m pytest tests/agents -q`（新增目录，不影响既有 `tests/{unit,integration,e2e}`）。

### 交付物 4：运行级验收文档
在注册包 `README.md` 内附「端到端实测步骤 + 判据」：新开会话 → 触发 `sdlc-orchestrator` → 用一个一次性小需求跑 FULL_FLOW → 断言 `docs/phase_status.md` 生成、每阶段产物落盘、门控记录写入。此步**须由用户在新会话执行**（受约束 5）。

## 关键决策（需你确认）
- **形态**：推荐「Skills 为主 + 注册包为辅」双轨（Skills 立即可用，注册包解锁原生 Subagent 编排）。
  若只想要其一，可只做 Skills 或只做注册包。
- **安装位置**：默认落工作区 `.trae/skills/`（随仓库、不污染全局）；需要跨项目复用时再复制到 `~/.trae-cn/skills/`。

## 验证方式
1. `python -m pytest tests/agents -q` → 全绿（产物级可行性证明）。
2. `python -m pytest tests/unit tests/integration tests/e2e -q` → 确认未影响既有测试（基线 unit 157/2skip、integration 171、e2e 24）。
3. 人工抽查 1 个 skill 与对应注册包可粘贴性（可用性冒烟）。
4. （用户执行）新会话端到端 FULL_FLOW 实测，按 `README.md` 判据核对。

## 不做的事
- 不修改 `.claude/agents/` 原始文件（保留 Claude Code 侧可用）。
- 不尝试程序化注册 TRAE 智能体（平台不支持）。
- 不新增除上述三处外的目录；不引入依赖。
