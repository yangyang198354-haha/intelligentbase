"""SDLC 智能体套件（TRAE 复刻）产物级契约测试。

对应《TRAE智能体套件复刻方案》交付物 1（Skills）与交付物 2（注册包）的结构契约，
即方案「验证方式 1」的自动化部分。运行：

    python -m pytest tests/agents -q

断言全部基于**已落盘产物**的静态事实，不启动服务、不联网。
"""

from __future__ import annotations

import re

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
