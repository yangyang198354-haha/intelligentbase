"""SDLC 智能体套件（TRAE 复刻）产物级契约测试。

对应《TRAE智能体套件复刻方案》交付物 1（Skills）与交付物 2（注册包）的结构契约，
即方案「验证方式 1」的自动化部分。运行：

    python -m pytest tests/agents -q

断言全部基于**已落盘产物**的静态事实，不启动服务、不联网。

注意：本目录**刻意不放 conftest.py** —— 全仓 `pytest tests` 收集时，任何名为
conftest.py 的模块都会在 sys.modules 中以裸名 "conftest" 注册并互相覆盖，
tests/conftest.py（e2e/integration 以 `from conftest import ...` 依赖）必须唯一。
故夹具直接内联于本文件。
"""

from __future__ import annotations

import pathlib
import re

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

#: skill 名 → 承载同一提示词正文的注册包（双源同步的唯一事实对照表）。
#: `sdlc-shared-protocol` 是只读参考协议，无对应注册包。
SKILL_PACK_PAIRS = {
    "sdlc-orchestrator": "01-pm-orchestrator.md",
    "sdlc-requirement-analyst": "02-requirement-analyst.md",
    "sdlc-system-architect": "03-system-architect.md",
    "sdlc-software-developer": "04-software-developer.md",
    "sdlc-test-engineer": "05-test-engineer.md",
    "sdlc-devops-engineer": "06-devops-engineer.md",
    "sdlc-agent-builder": "07-agent-builder.md",
}

#: 提示词正文的统一起始锚点。
PROMPT_TAG = "<generated_agent_prompt>"


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


# --------------------------------------------------------------------------- #
# 交付物 1：TRAE Skills（.trae/skills/sdlc-*/SKILL.md）
# --------------------------------------------------------------------------- #


def test_skill_files_exist(skills_dir, expected_skills):
    """8 个 skill 目录下均存在 SKILL.md。"""
    for name in expected_skills:
        path = skills_dir / name / "SKILL.md"
        assert path.is_file(), f"缺少 SKILL.md：{path}"


def test_frontmatter_valid(skill_texts, expected_skills, frontmatter_parser):
    """frontmatter 合法：name == 目录名、description 非空、无 Claude 专有字段残留。"""
    for name in expected_skills:
        fm = frontmatter_parser(skill_texts[name])
        assert fm.get("name") == name, f"{name} 的 frontmatter.name 与目录名不一致"
        assert fm.get("description", "").strip(), f"{name} 的 description 为空"
        for forbidden in ("tools", "model", "color"):
            assert forbidden not in fm, f"{name} 残留 Claude 专有 frontmatter 字段：{forbidden}"


def test_orchestrator_covers_full_lifecycle(skill_texts):
    """主控正文覆盖 5 个阶段组、门控与生产部署授权规则。

    注：主控以「组」为单位编排，阶段用紧凑区间记法（如 `GROUP_A (PHASE_01+02)`）；
    11 个阶段的逐条枚举由共享协议承载（见 test_shared_protocol_phase_table_complete）。
    """
    text = skill_texts["sdlc-orchestrator"]
    for g in "ABCDE":
        assert f"GROUP_{g}" in text, f"主控缺少阶段组 GROUP_{g}"
    assert "PRODUCTION_DEPLOY_CONFIRM" in text, "主控缺少生产部署授权信号"
    assert "FULL_FLOW" in text and "PARTIAL_FLOW" in text, "主控缺少两种工作模式定义"
    assert "gate_review" in text, "主控缺少门控评审记录约定"
    assert "PASS" in text and "FAIL" in text, "主控缺少门控判定值"


def test_shared_protocol_phase_table_complete(skill_texts):
    """共享协议逐条枚举 11 个阶段（PHASE_01 … PHASE_11）。"""
    text = skill_texts["sdlc-shared-protocol"]
    for n in range(1, 12):
        assert re.search(rf"PHASE_{n:02d}\b", text), f"共享协议缺少阶段 PHASE_{n:02d}"


def test_orchestrator_registers_all_role_skills(skill_texts):
    """主控的注册表列出全部 5 个角色 skill，形成可编排的闭环。"""
    text = skill_texts["sdlc-orchestrator"]
    for role_skill in (
        "sdlc-requirement-analyst",
        "sdlc-system-architect",
        "sdlc-software-developer",
        "sdlc-test-engineer",
        "sdlc-devops-engineer",
    ):
        assert role_skill in text, f"主控注册表缺少角色 skill：{role_skill}"


def test_shared_protocol_sections_complete(skill_texts):
    """共享协议齐备 A–K 全部章节。"""
    text = skill_texts["sdlc-shared-protocol"]
    for letter in "ABCDEFGHIJK":
        assert re.search(rf"^## {letter}\. ", text, re.M), f"共享协议缺少章节 {letter}"


def test_shared_protocol_id_conventions(skill_texts):
    """共享协议给出全套 ID 命名约定（供各角色统一引用）。"""
    text = skill_texts["sdlc-shared-protocol"]
    for token in (
        "REQ-FUNC-NNN",
        "REQ-NFUNC-NNN",
        "US-NNN",
        "AC-NNN-NN",
        "ADR-NNN",
        "MOD-NNN",
        "IFC-NNN",
        "TC-UNIT-NNN",
    ):
        assert token in text, f"共享协议缺少 ID 约定：{token}"


def test_role_skills_declare_owned_outputs(skill_texts, role_output_files):
    """每个角色 skill 声明其拥有的产出文件（与目录约定一致）。"""
    for skill, files in role_output_files.items():
        text = skill_texts[skill]
        for filename in files:
            assert filename in text, f"{skill} 未声明产出文件：{filename}"


# --------------------------------------------------------------------------- #
# 知识库（.trae/skills/sdlc-*/knowledge_base/）
# --------------------------------------------------------------------------- #


def test_knowledge_bases_complete(skills_dir, kb_skills, kb_required_files):
    """6 组知识库目录齐备，且每组的 3 个必需文件均存在且非空。"""
    for skill in kb_skills:
        kb = skills_dir / skill / "knowledge_base"
        assert kb.is_dir(), f"{skill} 缺少 knowledge_base 目录"
        for filename in kb_required_files:
            path = kb / filename
            assert path.is_file(), f"{skill} 知识库缺文件：{filename}"
            assert path.stat().st_size > 0, f"{skill} 知识库文件为空：{filename}"


def test_kb_dir_set_matches_spec(skills_dir, kb_skills):
    """拥有知识库的场景**恰好**是规定的 6 个（shared-protocol / agent-builder 不建 KB）。"""
    present = {
        child.name
        for child in skills_dir.iterdir()
        if child.is_dir() and (child / "knowledge_base").is_dir()
    }
    assert present == set(kb_skills), f"知识库目录集合与预期不符：{sorted(present)}"


def test_no_stale_claude_kb_paths(skill_texts, pack_texts):
    """全仓产物无遗留 Claude 侧 KB 硬编码路径（防漏改导致运行时找不到库）。"""
    combined = {**{f"{k}/SKILL.md": v for k, v in skill_texts.items()}, **pack_texts}
    for name, text in combined.items():
        assert ".claude/agents/knowledge_base" not in text, f"{name} 残留旧 KB 路径引用"


# --------------------------------------------------------------------------- #
# 防回归：TRAE 平台适配残留（第二轮优化后须保持零匹配）
# --------------------------------------------------------------------------- #


def test_no_platform_assumption_residue(skill_texts, pack_texts):
    """全部 SKILL.md 与注册包不含 Claude 平台假设残留。"""
    combined = {**{f"{k}/SKILL.md": v for k, v in skill_texts.items()}, **pack_texts}
    for name, text in combined.items():
        assert "temperature:" not in text, f"{name} 残留 API 采样参数 temperature:"
        assert "top_p" not in text, f"{name} 残留 API 采样参数 top_p"
        assert "sdlc-agent_builder" not in text, f"{name} 残留下划线 KB 路径 sdlc-agent_builder"
        assert "Edit, Bash" not in text, f"{name} 残留 Claude 工具集表述 Edit, Bash"


def test_agent_builder_output_spec_platform_neutral(skill_texts):
    """agent-builder 的输出规格不得再将产物导向「Claude 中使用」。"""
    text = skill_texts["sdlc-agent-builder"]
    assert "Claude 中使用" not in text, "agent-builder 输出规格仍导向 Claude"


def test_kb_persistence_lazy_load_declared(skill_texts, kb_skills):
    """每个 KB-owning skill 的持久化协议均声明 kb_full.xml 懒加载（防整库灌入主上下文）。"""
    for skill in kb_skills:
        assert "不整体加载" in skill_texts[skill], (
            f"{skill} 的 KB 持久化协议缺少「不整体加载」懒加载声明"
        )


def test_skill_pack_prompt_body_parity(skill_texts, pack_texts):
    """SKILL.md 与对应注册包的提示词正文逐字一致（消除双源人工同步漂移）。

    两侧均自 `<generated_agent_prompt>` 起至文件末尾承载同一份提示词正文；
    比较前折叠空白（仅归一换行/缩进）。任一单侧改动而未同步另一侧即失败，
    使「人工 discipline」升级为机器门。
    """
    def body(text: str) -> str:
        idx = text.find(PROMPT_TAG)
        assert idx >= 0, f"缺少提示词起始锚点 {PROMPT_TAG}"
        return re.sub(r"\s+", " ", text[idx:]).strip()

    for skill, pack in SKILL_PACK_PAIRS.items():
        assert body(skill_texts[skill]) == body(pack_texts[pack]), (
            f"{skill} 与 {pack} 的提示词正文不一致（双源漂移）："
            "修改任一侧后必须同步另一侧"
        )


def test_tool_registry_populated(skill_texts):
    """7 个可执行 skill 的 <tool_registry> 均至少注册 1 个工具（防空壳回潮）。

    注：`sdlc-shared-protocol` 为只读参考协议，不含 tool_execution_layer，故不在检查范围。
    """
    for skill in SKILL_PACK_PAIRS:
        m = re.search(r"<tool_registry>(.*?)</tool_registry>", skill_texts[skill], re.S)
        assert m, f"{skill} 缺少 <tool_registry> 块"
        assert re.search(r"<tool\s+name=", m.group(1)), (
            f"{skill} 的 <tool_registry> 是空壳（只含格式注释，未注册任何工具）"
        )


# --------------------------------------------------------------------------- #
# 交付物 2：智能体注册包（.trae/agent-packs/）
# --------------------------------------------------------------------------- #


def test_packs_have_complete_config_block(pack_texts):
    """7 个注册包均含完整「配置」表（5 个字段齐全）。"""
    fields = ("名称", "描述", "工具集", "模型", "可被其他智能体调用")
    for name, text in pack_texts.items():
        for field in fields:
            assert re.search(rf"^\| {re.escape(field)} \|", text, re.M), (
                f"{name} 配置块缺少字段：{field}"
            )


def test_pack_agent_names_match_skill_spec(pack_texts, expected_skills):
    """每个注册包声明的「名称」都对应一个已交付的 skill，且 7 者互异。

    注：`sdlc-shared-protocol` 是只读共享协议（无独立智能体），故注册包为 7 个而非 8 个。
    """
    names = []
    for filename, text in pack_texts.items():
        m = re.search(r"^\| 名称 \| (\S+) \|", text, re.M)
        assert m, f"{filename} 未找到「名称」配置行"
        names.append(m.group(1))
        assert m.group(1) in expected_skills, f"{filename} 的名称不在 skill 清单：{m.group(1)}"
    assert len(set(names)) == len(pack_texts), f"注册包名称存在重复：{names}"
    assert "sdlc-shared-protocol" not in names, "共享协议不应有独立注册包"


def test_orchestrator_pack_is_top_level_only(pack_texts):
    """主控注册包不设为可委派子智能体（顶层唯一入口）。"""
    text = pack_texts["01-pm-orchestrator.md"]
    assert re.search(r"^\| 可被其他智能体调用 \| 否", text, re.M), (
        "主控注册包应标注「否（顶层主控）」"
    )


def test_role_packs_are_delegable(pack_texts):
    """5 个角色注册包 + agent-builder 均应开启「可被其他智能体调用」。"""
    for filename in (
        "02-requirement-analyst.md",
        "03-system-architect.md",
        "04-software-developer.md",
        "05-test-engineer.md",
        "06-devops-engineer.md",
        "07-agent-builder.md",
    ):
        text = pack_texts[filename]
        assert re.search(r"^\| 可被其他智能体调用 \| 是", text, re.M), (
            f"{filename} 应开启「可被其他智能体调用」"
        )


def test_packs_embed_full_prompt(pack_texts):
    """每个注册包在「提示词」标题后内嵌了可粘贴的完整提示词正文（非空且含角色块）。"""
    for filename, text in pack_texts.items():
        assert "## 提示词" in text, f"{filename} 缺少「提示词」小节"
        body = text.split("## 提示词", 1)[1]
        assert "<generated_agent_prompt>" in body, f"{filename} 提示词正文缺少 <generated_agent_prompt>"
        assert len(body.strip()) > 500, f"{filename} 提示词正文过短"
