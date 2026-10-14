"""SDLC 智能体套件（TRAE 复刻）契约测试夹具。

校验对象为本仓库 `.trae/` 下的 TRAE 复刻产物：
  * `.trae/skills/sdlc-*/SKILL.md`      —— 8 个 TRAE 可加载技能
  * `.trae/skills/sdlc-*/knowledge_base` —— 6 组持久化知识库
  * `.trae/agent-packs/*.md`            —— 7 个智能体注册包

本夹具只做**离线结构 / 契约校验**：不启动服务、不联网、不依赖 Django。
所有路径基于本文件位置推导（`tests/agents/conftest.py` → 上级两级为仓库根）。
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TRAE_DIR = REPO_ROOT / ".trae"
SKILLS_DIR = TRAE_DIR / "skills"
PACKS_DIR = TRAE_DIR / "agent-packs"

#: 期望的 8 个 skill（目录名必须 == frontmatter 的 name）。
EXPECTED_SKILLS = (
    "sdlc-orchestrator",
    "sdlc-requirement-analyst",
    "sdlc-system-architect",
    "sdlc-software-developer",
    "sdlc-test-engineer",
    "sdlc-devops-engineer",
    "sdlc-shared-protocol",
    "sdlc-agent-builder",
)

#: 角色 skill → 其**声明拥有**的产出文件（与 shared-protocol §A 目录约定一致）。
ROLE_OUTPUT_FILES = {
    "sdlc-orchestrator": ("phase_status.md", "delivery_report.md"),
    "sdlc-requirement-analyst": ("requirements_spec.md", "user_stories.md"),
    "sdlc-system-architect": ("architecture_design.md", "module_design.md", "tech_stack.md"),
    "sdlc-software-developer": ("implementation_plan.md", "code_review_report.md"),
    "sdlc-test-engineer": ("test_plan.md", "test_report.md"),
    "sdlc-devops-engineer": ("cicd_pipeline.md", "deployment_plan.md", "deployment_report.md"),
}

#: 拥有知识库的 6 个 skill（shared-protocol / agent-builder 为只读参考，无 KB）。
KB_SKILLS = (
    "sdlc-orchestrator",
    "sdlc-requirement-analyst",
    "sdlc-system-architect",
    "sdlc-software-developer",
    "sdlc-test-engineer",
    "sdlc-devops-engineer",
)

#: 每组知识库必须齐备且非空的文件。
KB_REQUIRED_FILES = ("kb_index.md", "kb_full.xml", "kb_distillation_log.md")

#: 7 个注册包文件名。
PACK_FILES = (
    "01-pm-orchestrator.md",
    "02-requirement-analyst.md",
    "03-system-architect.md",
    "04-software-developer.md",
    "05-test-engineer.md",
    "06-devops-engineer.md",
    "07-agent-builder.md",
)


def read_text(path: pathlib.Path) -> str:
    """以 UTF-8 读取文本（复刻产物全为中文 Markdown，无 BOM）。"""
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict:
    """解析 `---` 包裹的 YAML frontmatter 为扁平字典（仅键值行，够用即可）。

    本套件 frontmatter 只有 `name` / `description` 两个标量键，无需完整 YAML 解析；
    遇到非法结构直接抛 AssertionError，由用例给出可读定位。
    """
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "frontmatter 缺少起始分隔符 `---`"
    fm: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip()
    raise AssertionError("frontmatter 未闭合（缺少结束分隔符 `---`）")


# --------------------------------------------------------------------------- #
# 会话级夹具：把 spec 与产物一次性提供，避免用例各自重复读盘
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def skills_dir() -> pathlib.Path:
    return SKILLS_DIR


@pytest.fixture(scope="session")
def packs_dir() -> pathlib.Path:
    return PACKS_DIR


@pytest.fixture(scope="session")
def expected_skills() -> tuple:
    return EXPECTED_SKILLS


@pytest.fixture(scope="session")
def role_output_files() -> dict:
    return ROLE_OUTPUT_FILES


@pytest.fixture(scope="session")
def kb_skills() -> tuple:
    return KB_SKILLS


@pytest.fixture(scope="session")
def kb_required_files() -> tuple:
    return KB_REQUIRED_FILES


@pytest.fixture(scope="session")
def pack_files() -> tuple:
    return PACK_FILES


@pytest.fixture(scope="session")
def frontmatter_parser():
    return parse_frontmatter


@pytest.fixture(scope="session")
def skill_texts(skills_dir, expected_skills) -> dict:
    """skill 名 → SKILL.md 正文（缺文件即失败，尽早暴露）。"""
    out: dict = {}
    for name in expected_skills:
        path = skills_dir / name / "SKILL.md"
        assert path.is_file(), f"缺少 SKILL.md：{path}"
        out[name] = read_text(path)
    return out


@pytest.fixture(scope="session")
def pack_texts(packs_dir, pack_files) -> dict:
    """注册包文件名 → 正文。"""
    out: dict = {}
    for name in pack_files:
        path = packs_dir / name
        assert path.is_file(), f"缺少注册包：{path}"
        out[name] = read_text(path)
    return out
