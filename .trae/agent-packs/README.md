# SDLC 智能体套件 · TRAE 注册与验收

本目录是 `.claude/agents/` 下 SDLC 多智能体套件在 **TRAE** 中的等价复刻产物：
把 Claude Code 专有的 7 个 agent 转写成「注册包」（可直接粘贴进 TRAE 智能体管理面板的提示词 + 配置表），
并配套一套**文件可加载**的 TRAE Skills（见 `.trae/skills/`）。

两条可用路径（互为补充，可只用其一）：

| 路径 | 载体 | 能力 | 生效时机 |
|---|---|---|---|
| **A. Skills**（主，立即可用） | `.trae/skills/sdlc-*` | 主 Agent 按需 `Skill` 调用，等价还原「PM 编排 + 各角色按阶段执行」 | 新会话自动加载 |
| **B. 智能体注册包**（辅，原生 Subagent） | 本目录 `0N-*.md` | 录入面板后，主 Agent 按 `description` 自动委派子智能体 | 录入后即时可用 |

> 平台约束（复刻方案已记录）：TRAE 的「智能体」只可由 **UI 面板创建**，工作区内不存在文件定义，
> 因此本目录提供 **注册包** 供手动录入，而**不能**由脚本程序化注册。

---

## 一、路径 B：把 7 个智能体录入 TRAE

对 `01-pm-orchestrator.md` … `07-agent-builder.md` 逐个执行：

1. 打开 TRAE **智能体管理面板**（侧栏「智能体」→ 管理/新建）。
2. 点击 **新建智能体**。
3. 按该文件顶部 `## 配置` 表中的 **名称 / 描述 / 工具集 / 模型** 逐字段填写。
4. 把该文件 `## 提示词` 标题**下方**的全部内容，**逐字粘贴**到面板的「提示词」输入框。
5. 打开 **「可被其他智能体调用」** 开关 —— 除 `01-pm-orchestrator`（顶层主控，保持关闭）外，
   `02`~`07` 全部**开启**，使其成为可被委派的 Subagent。
6. 保存。

录入完成后核对：面板中应存在 7 个智能体，名称分别为
`sdlc-orchestrator` / `sdlc-requirement-analyst` / `sdlc-system-architect` /
`sdlc-software-developer` / `sdlc-test-engineer` / `sdlc-devops-engineer` / `sdlc-agent-builder`。

---

## 二、路径 A：Skills（无需录入，随仓库生效）

`SKILL.md` 位于 `.trae/skills/<名称>/SKILL.md`，会话启动时加载。使用方式：
以 `Skill` 工具调用 `sdlc-orchestrator`（主控），由它按阶段调用其余 `sdlc-*` 技能。

如需**跨项目**使用，把整个 `sdlc-*` 目录复制到全局技能目录：

```powershell
Copy-Item -Recurse -Force ".trae\skills\sdlc-*" "$env:USERPROFILE\.trae-cn\skills\"
```

---

## 三、运行级端到端验收（FULL_FLOW 实测，须在新会话执行）

> 受约束：新增 skill 在**会话启动时**加载，本产物无法在「创建它的同一会话」内即时调用 —— 端到端实测必须新开会话。

**步骤**

1. **新开一个 TRAE 会话**（使新建 skill / 已录入智能体生效）。
2. 触发主控：调用 Skill `sdlc-orchestrator`（或对已录入的 `sdlc-orchestrator` 智能体下达指令）。
3. 给它一个**一次性小需求**做 FULL_FLOW，例如：
   「实现一个命令行 TODO 工具，支持增/删/查/标记完成，数据存本地 JSON 文件。」
4. 按门控节奏逐阶段确认（PM 会在每个阶段组结束时给出 `gate_review`，等待你 PASS/FAIL）。

**判据（逐项核对，全部满足即验收通过）**

| # | 判据 |
|---|---|
| 1 | `docs/phase_status.md` 已生成，且 `PHASE_01`…`PHASE_11` 均有状态记录 |
| 2 | 各阶段产物落盘：`requirements_spec.md`、`user_stories.md`、`architecture_design.md`、`module_design.md`、`tech_stack.md`、`implementation_plan.md`、`code_review_report.md`、`test_plan.md`、`test_report.md`、`cicd_pipeline.md`、`deployment_plan.md` |
| 3 | 每个阶段组均写入 `gate_review` 记录，`gate_decision ∈ {PASS, PASS_WITH_CONDITIONS, FAIL}` |
| 4 | 进入 GROUP_E 生产部署前，PM **先向用户请求授权**，拿到确认后才注入 `PRODUCTION_DEPLOY_CONFIRM=true` |
| 5 | 结束时生成 `docs/delivery_report.md`，覆盖所有已执行阶段的结果与质量指标 |
| 6 | 产品产出物（需求→架构→代码→测试→部署）内部 ID 可追溯（`REQ-*` / `US-*` / `AC-*` / `ADR-*` / `MOD-*` / `IFC-*` / `TC-*`） |

**退路**：若某阶段 FAIL，PM 应按规定重试（≤2 次）后上报用户，不自行臆断；如需局部重跑，可改用 PARTIAL_FLOW，指定 `start_group`/`end_group`。

---

## 四、产物级自动校验（可随时运行）

```powershell
python -m pytest tests/agents -q
```

该校验对 8 个 `SKILL.md`、7 个注册包、6 组知识库做结构契约断言（frontmatter 合法、阶段/门控覆盖、
产出文件声明、ID 约定、知识库齐备、无旧路径残留）。
