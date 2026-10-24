"""SDLC 智能体套件（TRAE 版 v3.5.1）产物级契约测试。

断言对象是**已落盘的 TRAE 产物**：
  - `.trae/skills/sdlc-*/SKILL.md`（9 个技能）
  - `.trae/agent-packs/*.md`（8 个单文件注册包 + README）
  - `.trae/sdlc/`（画像模板、suite_config、通用知识库、记忆种子、hook 等效脚本）

运行：`python -m pytest tests/agents -q`

全部为静态事实或进程内编译检查：不启动服务、不联网、不执行业务代码。

注意：本目录**刻意不放 conftest.py** —— 全仓 `pytest tests` 收集时，任何名为
conftest.py 的模块都会在 sys.modules 中以裸名 "conftest" 注册并互相覆盖，
tests/conftest.py（e2e/integration 以 `from conftest import ...` 依赖）必须唯一。
故夹具直接内联于本文件。
"""

from __future__ import annotations

import io
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TRAE_DIR = REPO_ROOT / ".trae"
SKILLS_DIR = TRAE_DIR / "skills"
PACKS_DIR = TRAE_DIR / "agent-packs"
RUNTIME_DIR = TRAE_DIR / "sdlc"

EXPECTED_SKILLS = (
    "sdlc-orchestrator",
    "sdlc-shared-protocol",
    "sdlc-requirement-analyst",
    "sdlc-system-architect",
    "sdlc-software-developer",
    "sdlc-test-engineer",
    "sdlc-devops-engineer",
    "sdlc-kb-curator",
    "sdlc-agent-builder",
)

EXPECTED_PACKS = (
    "01-pm-orchestrator.md",
    "02-requirement-analyst.md",
    "03-system-architect.md",
    "04-software-developer.md",
    "05-test-engineer.md",
    "06-devops-engineer.md",
    "07-agent-builder.md",
    "08-kb-curator.md",
)

PACK_TO_SKILL = {
    "01-pm-orchestrator.md": "sdlc-orchestrator",
    "02-requirement-analyst.md": "sdlc-requirement-analyst",
    "03-system-architect.md": "sdlc-system-architect",
    "04-software-developer.md": "sdlc-software-developer",
    "05-test-engineer.md": "sdlc-test-engineer",
    "06-devops-engineer.md": "sdlc-devops-engineer",
    "07-agent-builder.md": "sdlc-agent-builder",
    "08-kb-curator.md": "sdlc-kb-curator",
}

# 角色 skill → 其声明拥有的产出文件名（协议 §A 写权限表对应的产物）
ROLE_OUTPUT_FILES = {
    "sdlc-orchestrator": ("phase_status.md", "delivery_report.md"),
    "sdlc-requirement-analyst": ("requirements_spec.md", "user_stories.md"),
    "sdlc-system-architect": ("architecture_design.md", "module_design.md", "tech_stack.md"),
    "sdlc-software-developer": ("implementation_plan.md", "code_review_report.md"),
    "sdlc-test-engineer": ("test_plan.md",),
    "sdlc-devops-engineer": ("cicd_pipeline.md", "deployment_plan.md", "deployment_report.md"),
}

HOOK_SCRIPTS = ("sdlc_preflight.py", "kb_inbox.py", "webfetch_guard.py")


def read(path: pathlib.Path) -> str:
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:].lstrip("\n")


def skill_text(name: str) -> str:
    return read(SKILLS_DIR / name / "SKILL.md")


# --------------------------------------------------------------------------- #
# 技能结构
# --------------------------------------------------------------------------- #
def test_expected_skills_present() -> None:
    actual = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    missing = set(EXPECTED_SKILLS) - actual
    assert not missing, f"缺少技能目录：{sorted(missing)}"


def test_skill_frontmatter_name_matches_directory() -> None:
    for name in EXPECTED_SKILLS:
        text = skill_text(name)
        head, body = split_frontmatter(text)
        assert head, f"{name} 缺少 frontmatter"
        assert re.search(rf"^name:\s*{re.escape(name)}\s*$", head, re.M), (
            f"{name} frontmatter 的 name 与目录名不一致"
        )
        assert re.search(r"^description:\s*\S", head, re.M), f"{name} 缺少 description"
        assert body.strip(), f"{name} 正文为空"


def test_no_claude_invocation_residue() -> None:
    """正文里不得残留 Claude 的调用语法（来源注释行与映射说明允许保留）。"""
    patterns = ("claude --agent", "subagent_type", ".claude/agents/", ".claude/hooks/",
                ".claude/agent-memory/")
    for name in EXPECTED_SKILLS:
        text = skill_text(name)
        text = re.sub(r"^>.*复刻自.*$", "", text, flags=re.M)
        hits = [p for p in patterns if p in text]
        assert not hits, f"{name} 残留 Claude 调用语法：{hits}"


def test_orchestrator_declares_all_groups() -> None:
    text = skill_text("sdlc-orchestrator")
    for group in ("GROUP_A", "GROUP_B", "GROUP_C", "GROUP_D", "GROUP_E1", "GROUP_E2", "GROUP_Z"):
        assert group in text, f"编排器缺少阶段组 {group}"


def test_shared_protocol_phase_table_complete() -> None:
    text = skill_text("sdlc-shared-protocol")
    phases = [f"PHASE_{i:02d}" for i in range(1, 11)]
    phases += ["PHASE_11a", "PHASE_11b", "PHASE_12"]
    for phase in phases:
        assert phase in text, f"共享协议缺少阶段 {phase}"


def test_shared_protocol_sections_present() -> None:
    text = skill_text("sdlc-shared-protocol")
    for section in "ABCDEFGIJKLMN":
        assert f"## {section}." in text, f"共享协议缺少 §{section}"


def test_trae_runtime_paths_documented() -> None:
    orch = skill_text("sdlc-orchestrator")
    proto = skill_text("sdlc-shared-protocol")
    for needle in (".trae/sdlc/project_profile.md", ".trae/sdlc/agent-memory/",
                   ".trae/sdlc/scripts/"):
        assert needle in orch, f"编排器未引用运行时路径 {needle}"
    for needle in ("## N. TRAE 运行适配", ".trae/sdlc/scripts/sdlc_preflight.py",
                   ".trae/sdlc/scripts/kb_inbox.py", ".trae/sdlc/scripts/webfetch_guard.py"):
        assert needle in proto, f"协议 §N 缺少 {needle}"


def test_hook_equivalents_referenced_by_orchestrator() -> None:
    text = skill_text("sdlc-orchestrator")
    for script in HOOK_SCRIPTS:
        assert script in text, f"编排器未引用 hook 等效脚本 {script}"


def test_role_output_ownership_declared() -> None:
    for name, files in ROLE_OUTPUT_FILES.items():
        text = skill_text(name)
        for filename in files:
            assert filename in text, f"{name} 未声明其产出文件 {filename}"


def test_phase_status_xml_check_documented() -> None:
    text = skill_text("sdlc-shared-protocol")
    assert "ElementTree" in text, "协议 §N/§G 未给出 phase_status XML 校验命令"


# --------------------------------------------------------------------------- #
# 注册包（单文件）与技能正文一致性
# --------------------------------------------------------------------------- #
def test_agent_packs_present() -> None:
    for pack in EXPECTED_PACKS:
        assert (PACKS_DIR / pack).is_file(), f"缺少注册包 {pack}"
    assert (PACKS_DIR / "README.md").is_file(), "缺少注册包 README.md"


def test_pack_body_matches_skill() -> None:
    for pack, skill in PACK_TO_SKILL.items():
        pack_text = read(PACKS_DIR / pack)
        assert "agent-pack:" in pack_text.splitlines()[0], f"{pack} 缺少生成标记"
        anchor = "> 在 TRAE 中优先直接加载"
        idx = pack_text.find(anchor)
        assert idx != -1, f"{pack} 缺少使用说明段落"
        body_start = pack_text.find("\n\n", idx)
        assert body_start != -1, f"{pack} 使用说明后缺少空行"
        pack_body = pack_text[body_start + 2:].strip()

        _, skill_body = split_frontmatter(skill_text(skill))
        assert pack_body == skill_body.strip(), f"{pack} 正文与 {skill} 不一致"


def test_pack_readme_lists_all_packs() -> None:
    text = read(PACKS_DIR / "README.md")
    for pack in EXPECTED_PACKS:
        assert pack in text, f"注册包 README 未列出 {pack}"


# --------------------------------------------------------------------------- #
# 运行时资产与脚本
# --------------------------------------------------------------------------- #
def test_runtime_assets_present() -> None:
    required = [
        RUNTIME_DIR / "project_profile.template.md",
        RUNTIME_DIR / "suite_config.md",
        RUNTIME_DIR / "knowledge_base" / "README.md",
    ]
    for path in required:
        assert path.is_file(), f"缺少运行时文件 {path.relative_to(REPO_ROOT)}"

    for agent in ("pm-orchestrator", "requirement-analyst", "system-architect",
                  "software-developer", "test-engineer", "devops-engineer",
                  "kb-curator", "agent-builder"):
        assert (RUNTIME_DIR / "agent-memory" / agent / "MEMORY.md").is_file(), (
            f"缺少记忆种子 agent-memory/{agent}/MEMORY.md"
        )
        assert (RUNTIME_DIR / "knowledge_base" / "generic" / f"{agent}.md").is_file(), (
            f"缺少通用知识库 generic/{agent}.md"
        )

    for script in HOOK_SCRIPTS + ("suite_selftest.py", "port_from_claude.py", "seed_memory.py"):
        path = RUNTIME_DIR / "scripts" / script
        assert path.is_file(), f"缺少脚本 {script}"
        compile(read(path), str(path), "exec")


def test_suite_config_maps_hooks() -> None:
    text = read(RUNTIME_DIR / "suite_config.md")
    for needle in ("sdlc_preflight.py", "kb_inbox.py", "webfetch_guard.py",
                   "SubagentStop", "PreToolUse"):
        assert needle in text, f"suite_config.md 未登记 {needle}"
