"""单元测试层 5/N —— R7 定义文档数据层（IFC-IB-288~292；纯函数，离线可跑）。

文件：`tests/unit/test_definition_data_layer_r7.py`（跨模块用例见
`tests/integration/test_definition_config_r7.py`；两文件**基名不同**以免 pytest 模块名撞车）。

覆盖用户故事：**US-IB-17**（可视化配置 / 定义文档单一真源）、**US-IB-18**（非法配置装配期拒绝）。
对应验收标准：AC-IB-17-02、AC-IB-17-04、AC-IB-18-01、AC-IB-18-02、AC-IB-18-03、AC-IB-18-04、AC-IB-18-05。

分层依据（test_plan §2）：本文件只调用 `ib.config.definition` 的**纯函数**
（`validate` / `derive` / `semantic_hash` / `editable_field_whitelist` / `non_editable_changes` /
`document_to_json` / `document_from_json`）与 `ib.core` 的 frozen 数据结构 —— 单模块、无 I/O，
故为**单元级**。跨模块（存储端口 / 装配闸门 / HTTP 端点）用例见
`tests/integration/test_definition_config_r7.py`（基名不同，避免 pytest 模块名冲突）。

纪律：测试代码不含任何真实 token/key/密码；所有「凭据」均为环境变量占位符或显式标注的假值。
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
from dataclasses import replace

from ib.config import (
    NON_EDITABLE_FIELDS,
    build_definition_document,
    derive,
    document_from_json,
    document_to_json,
    editable_field_whitelist,
    non_editable_changes,
    semantic_hash,
    validate,
)
from ib.core import (
    ConditionalEdgeSpec,
    EdgeSpec,
    ExpertSpecInput,
    OrchestrationSpecInput,
    RouteSpecInput,
    ToolGrantSpec,
    ValidationErrorItem,
    ValidationReport,
)

#: 已知工具注册表（离线替身；与装配期 `_known_tool_names()` 语义一致的最小集）。
KNOWN_TOOLS = frozenset({"search_knowledge"})


# --------------------------------------------------------------------------- #
# 构造助手（每个用例独立构造，避免共享可变状态）
# --------------------------------------------------------------------------- #


def _expert(
    name: str,
    cn_label: str | None = None,
    keywords: tuple[str, ...] | None = None,
    *,
    is_default: bool = False,
) -> ExpertSpecInput:
    """构造一位专家（**关键词 / 标签随 name 派生**，R8 起两位专家互不撞车）。

    R8 说明：`validate` 于 R8 纯追加两项装配期校验（跨专家关键词撞车 / `cn_label` 唯一性），
    故**合法基线**要求每位专家的 `keywords` 与 `cn_label` 互异。此处以 `name` 派生默认值
    （`keywords=(f"k{name}",)`、`cn_label=f"标签{name}"`）—— 仅为**夹具数据**变更，
    不改变任何断言语义（既有断言仍表达「基线合法 → ok is True / errors == ()」）。
    需要显式覆盖的用例（如「cn_label 空」）按原样传入 `cn_label=...`。
    """
    return ExpertSpecInput(
        name=name,
        cn_label=f"标签{name}" if cn_label is None else cn_label,
        keywords=(f"k{name}",) if keywords is None else keywords,
        exemplars=(),
        is_data_expert=False,
        is_delegating=False,
        is_default=is_default,
    )


def _doc(**overrides):
    """一份**合法**的定义文档（默认两位专家、恰一个默认专家）。"""
    base = dict(
        project_id="p1",
        experts=(_expert("a", is_default=True), _expert("b")),
        route=RouteSpecInput(tau=0.65, margin=0.05, max_expert_steps=8, default_expert="a"),
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec(from_node="route", branch_map=(("a", "a"),)),),
        ),
        tool_grants=(ToolGrantSpec(expert_name="a", tool_names=("search_knowledge",)),),
    )
    base.update(overrides)
    return build_definition_document(**base)


def _codes(report: ValidationReport) -> set[str]:
    return {item.code for item in report.errors}


# --------------------------------------------------------------------------- #
# TC-UNIT-056 —— AC-IB-18-05：校验逻辑 framework-free 且为纯函数
# --------------------------------------------------------------------------- #


def test_TC_UNIT_056_validate_is_framework_free_and_pure():
    """[TC-UNIT-056] US-IB-18 / AC-IB-18-05：`validate`/`derive` 可在**无编排框架**环境加载与单测。

    正向断言三条：
      1. 在**干净解释器**里 import `ib.config.definition` 成功，且 `sys.modules` 中不出现
         django / DRF / langchain / langgraph —— 被测模块的加载不依赖编排框架；
      2. 纯函数：同输入同输出（`validate` / `semantic_hash` / `derive` 三次调用相等）；
      3. 校验结果与「环境中是否存在某凭据键」无关（不读环境，不产生副作用）。
    """
    src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
    probe = (
        "import sys; sys.path.insert(0, r'{src}');\n"
        "import ib.config.definition as d;\n"
        "bad = sorted(m for m in sys.modules "
        "if m.split('.')[0] in ('django', 'rest_framework', 'langchain', 'langgraph'));\n"
        "print('MODULES=' + ','.join(bad));\n"
        "print('HAS_VALIDATE=' + str(hasattr(d, 'validate')))\n"
    ).format(src=src)
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUTF8": "1", "IB_OFFLINE_MODE": "1"},
    )
    assert proc.returncode == 0, f"框架无关加载失败：{proc.stderr}"
    assert "MODULES=" in proc.stdout
    assert proc.stdout.strip().splitlines()[0] == "MODULES=", (
        f"定义层加载引入了编排框架：{proc.stdout}"
    )
    assert "HAS_VALIDATE=True" in proc.stdout

    doc = _doc()
    first = validate(doc, known_tools=KNOWN_TOOLS)
    assert first == validate(doc, known_tools=KNOWN_TOOLS) == validate(doc, known_tools=KNOWN_TOOLS)
    assert semantic_hash(doc) == semantic_hash(doc) and derive(doc) == derive(doc)
    assert first.ok is True and first.errors == ()


# --------------------------------------------------------------------------- #
# TC-UNIT-057 —— AC-IB-18-02 / AC-IB-18-03：非法项逐类被拒绝且可定位
# --------------------------------------------------------------------------- #


def test_TC_UNIT_057_each_illegal_category_is_rejected_with_locator():
    """[TC-UNIT-057] US-IB-18 / AC-IB-18-02：各类非法定义均被拒绝，错误**定位到具体条目/键**。

    AC-IB-18-02 枚举的非法类别（除「路由关键词撞车」外，逐类正向覆盖，见报告 FND-R7-01）：
      必填项缺失 / 专家标识重复 / 默认专家缺失或不止一个 / 工具授权引用不存在的工具 /
      路由阈值越界 / 条件边分支映射缺失。
    """
    cases = {
        "专家标识重复": (_doc(experts=(_expert("a", is_default=True), _expert("a"))), "expert_name_duplicate"),
        "默认专家缺失": (
            _doc(
                experts=(_expert("a"), _expert("b")),
                route=RouteSpecInput(0.65, 0.05, 8, "a"),
            ),
            "expert_default_count",
        ),
        "默认专家不止一个": (
            _doc(experts=(_expert("a", is_default=True), _expert("b", is_default=True))),
            "expert_default_count",
        ),
        "工具授权引用不存在的工具": (
            _doc(tool_grants=(ToolGrantSpec("a", ("ghost-tool",)),)),
            "tool_grant_tool_unknown",
        ),
        "工具授权指向未知专家": (
            _doc(tool_grants=(ToolGrantSpec("ghost", ("search_knowledge",)),)),
            "tool_grant_expert_unknown",
        ),
        "路由阈值越界": (
            _doc(route=RouteSpecInput(1.5, 0.05, 8, "a")),
            "route_threshold_out_of_range",
        ),
        "边界参数越界(max_expert_steps=0)": (
            _doc(route=RouteSpecInput(0.65, 0.05, 0, "a")),
            "route_threshold_out_of_range",
        ),
        "条件边分支映射缺失": (
            _doc(
                orchestration=OrchestrationSpecInput(
                    nodes=("route", "a", "b"),
                    conditional_edges=(ConditionalEdgeSpec("route", ()),),
                )
            ),
            "conditional_edge_branch_map_empty",
        ),
        "条件边端点不存在": (
            _doc(
                orchestration=OrchestrationSpecInput(
                    nodes=("route", "a", "b"),
                    conditional_edges=(ConditionalEdgeSpec("route", (("a", "ghost"),)),),
                )
            ),
            "conditional_edge_node_unknown",
        ),
        "普通边端点不存在": (
            _doc(
                orchestration=OrchestrationSpecInput(
                    nodes=("route", "a", "b"),
                    conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
                    edges=(EdgeSpec("a", "ghost"),),
                )
            ),
            "orchestration_edge_node_unknown",
        ),
        "普通边自环": (
            _doc(
                orchestration=OrchestrationSpecInput(
                    nodes=("route", "a", "b"),
                    conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
                    edges=(EdgeSpec("a", "a"),),
                )
            ),
            "orchestration_edge_self_loop",
        ),
        "普通边重复": (
            _doc(
                orchestration=OrchestrationSpecInput(
                    nodes=("route", "a", "b"),
                    conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
                    edges=(EdgeSpec("a", "b"), EdgeSpec("a", "b")),
                )
            ),
            "orchestration_edge_duplicate",
        ),
        "默认专家不在专家集合内": (
            _doc(route=RouteSpecInput(0.65, 0.05, 8, "ghost")),
            "route_default_unknown",
        ),
        "必填项缺失(cn_label 空)": (
            _doc(experts=(_expert("a", cn_label="  ", is_default=True), _expert("b"))),
            "expert_text_missing",
        ),
        "专家集合为空": (_doc(experts=()), "experts_empty"),
    }
    for label, (doc, expected_code) in cases.items():
        report = validate(doc, known_tools=KNOWN_TOOLS)
        assert report.ok is False, f"{label}：非法定义竟通过校验"
        assert expected_code in _codes(report), f"{label}：未产出 {expected_code}，实际 {_codes(report)}"
        # 可读定位：每条错误都带非空的 path / code / message
        for item in report.errors:
            assert item.path and item.code and item.message, f"{label}：错误项缺少定位信息 {item}"

    # content_hash 缺失 / schema 版本不受支持 / project_id 空（服务端管理字段亦参与校验）
    assert "content_hash_missing" in _codes(validate(replace(_doc(), content_hash="")))
    assert "schema_version_unsupported" in _codes(validate(replace(_doc(), schema_version=99)))
    assert "project_id_missing" in _codes(validate(replace(_doc(), project_id="")))

    # 合法样例（含边界取值 tau=0.0 / 1.0）通过
    assert validate(_doc(route=RouteSpecInput(0.0, 0.0, 1, "a"))).ok is True
    assert validate(_doc(route=RouteSpecInput(1.0, 1.0, 8, "a"))).ok is True

    # `START`/`END` 是**保留合成端点**：作为普通边端点合法（它们不进 `nodes`），
    # 但作为**条件边分支目标**非法 —— 条件边必须落到真实节点。
    spine = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
            edges=(EdgeSpec("START", "route"), EdgeSpec("a", "END")),
        )
    )
    assert validate(spine, known_tools=KNOWN_TOOLS).ok is True, _codes(validate(spine, known_tools=KNOWN_TOOLS))

    reserved_as_branch_target = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "START"),)),),
        )
    )
    assert "conditional_edge_node_unknown" in _codes(
        validate(reserved_as_branch_target, known_tools=KNOWN_TOOLS)
    )


# --------------------------------------------------------------------------- #
# TC-UNIT-058 —— AC-IB-17-02：往返（round-trip）语义等价，无漂移
# --------------------------------------------------------------------------- #


def test_TC_UNIT_058_roundtrip_is_semantically_equivalent():
    """[TC-UNIT-058] US-IB-17 / AC-IB-17-02：文档 → JSON → 文档 往返**语义等价**，逐项无增删改。

    对应 AC：「不做任何修改直接回写得到 D′，D′ 与 D 语义等价；逐项比对可编辑对象，
    无新增、无丢失、无静默改写」。
    """
    original = _doc()
    text = document_to_json(original)
    reloaded = document_from_json("p1", text)

    assert semantic_hash(reloaded) == semantic_hash(original), "往返产生了语义漂移"
    assert document_to_json(reloaded) == document_to_json(original), "往返后序列化不逐字一致"
    assert reloaded.project_id == original.project_id == "p1"
    assert reloaded.schema_version == original.schema_version

    # 逐项比对可编辑对象：无新增、无丢失、无静默改写
    assert len(reloaded.experts) == len(original.experts)
    for got, want in zip(reloaded.experts, original.experts):
        assert got.name == want.name and got.cn_label == want.cn_label
        assert tuple(got.keywords) == tuple(want.keywords)
        assert tuple(got.exemplars) == tuple(want.exemplars)
        assert got.is_data_expert == want.is_data_expert
        assert got.is_delegating == want.is_delegating
        assert got.is_default == want.is_default
        assert got.is_delegating == want.is_delegating
        assert got.is_default == want.is_default
    assert reloaded.route == original.route
    assert tuple(reloaded.orchestration.nodes) == tuple(original.orchestration.nodes)
    assert tuple(reloaded.orchestration.conditional_edges) == tuple(original.orchestration.conditional_edges)
    assert tuple(reloaded.orchestration.edges) == tuple(original.orchestration.edges)
    assert tuple(reloaded.tool_grants) == tuple(original.tool_grants)

    # 普通边**非空**时同样逐项无漂移（默认基线的 `edges=()` 会掩盖重建函数的漏解析）
    with_edges = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
            edges=(EdgeSpec("START", "route"), EdgeSpec("a", "END")),
        )
    )
    edged = document_from_json("p1", document_to_json(with_edges))
    assert tuple(edged.orchestration.edges) == (EdgeSpec("START", "route"), EdgeSpec("a", "END"))
    assert document_to_json(edged) == document_to_json(with_edges), "普通边往返后序列化不逐字一致"
    assert semantic_hash(edged) == semantic_hash(with_edges)

    # 同一文档只差一条普通边 → 语义哈希**必须不同**。
    # 否则 `_semantic_payload` 漏收 `edges`，乐观并发对边改动无感（正确性 bug）。
    fewer_edges = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
            edges=(EdgeSpec("START", "route"),),
        )
    )
    assert semantic_hash(with_edges) != semantic_hash(fewer_edges)

    # 往返幂等：再走一轮仍等价
    assert semantic_hash(document_from_json("p1", document_to_json(reloaded))) == semantic_hash(original)

    # 语义哈希与 updated_at（非语义内容）无关
    assert semantic_hash(original) == semantic_hash(replace(original, updated_at="2026-09-27T00:00:00Z"))


# --------------------------------------------------------------------------- #
# TC-UNIT-059 —— AC-IB-17-04：白名单制；图拓扑不可编辑
# --------------------------------------------------------------------------- #


def test_TC_UNIT_059_whitelist_excludes_topology_and_non_editable_changes_detects_it():
    """[TC-UNIT-059] US-IB-17 / AC-IB-17-04：可编辑白名单含「节点参数 + 专家集合」，**不含拓扑**。

    对应 AC：「界面不提供运行期增删图节点或改变编排图拓扑的能力；清单之外的字段不被界面写入」。
    """
    whitelist = editable_field_whitelist()
    assert isinstance(whitelist, frozenset)
    for editable in ("experts", "experts[].cn_label", "route.tau", "route.default_expert", "tool_grants"):
        assert editable in whitelist, f"白名单缺可编辑项 {editable}"

    for forbidden in ("orchestration", "orchestration.nodes", "orchestration.conditional_edges",
                       "orchestration.edges", "schema_version", "project_id"):
        assert forbidden not in whitelist, f"拓扑/归属类字段不得进入可编辑白名单：{forbidden}"

    # 不可编辑清单与白名单互斥（白名单的补集）
    assert NON_EDITABLE_FIELDS.isdisjoint(whitelist), "不可编辑清单与白名单出现交集"

    current = _doc()

    # 拓扑变更（新增节点）→ 检出 field_not_editable 且指向 orchestration
    topology_changed = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b", "evil"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
        )
    )
    items = non_editable_changes(current, topology_changed)
    assert any(i.code == "field_not_editable" and i.path == "orchestration" for i in items), items

    # 拓扑变更（**只**改普通边，节点与条件边都不变）→ 同样检出且指向 orchestration。
    # 这条拦住「只比 nodes/conditional_edges 就算完」的半吊子实现。
    edges_changed = _doc(
        orchestration=OrchestrationSpecInput(
            nodes=("route", "a", "b"),
            conditional_edges=(ConditionalEdgeSpec("route", (("a", "a"),)),),
            edges=(EdgeSpec("START", "b"),),
        )
    )
    edge_items = non_editable_changes(current, edges_changed)
    assert any(i.code == "field_not_editable" and i.path == "orchestration" for i in edge_items), edge_items

    # project_id / schema_version 变更 → 同样被检出
    assert any(i.path == "project_id" for i in non_editable_changes(current, replace(current, project_id="p9")))
    assert any(
        i.path == "schema_version" for i in non_editable_changes(current, replace(current, schema_version=99))
    )

    # 白名单内变更（tau / 新增专家 / 工具授权）**不**算违规 → 界面可写
    assert non_editable_changes(current, _doc(route=RouteSpecInput(0.7, 0.05, 8, "a"))) == ()
    assert non_editable_changes(
        current, _doc(experts=(_expert("a", is_default=True), _expert("b"), _expert("c")))
    ) == ()
    assert non_editable_changes(current, current) == ()


# --------------------------------------------------------------------------- #
# TC-UNIT-060 —— AC-IB-18-04 / AC-IB-18-02：错误体不回显凭据值；无「强制继续」类型通道
# --------------------------------------------------------------------------- #


def test_TC_UNIT_060_errors_carry_locators_without_credential_values():
    """[TC-UNIT-060] US-IB-18 / AC-IB-18-04 + AC-IB-18-02：错误信息只出 `path/code/message`，
    不含任何凭据值；`ValidationReport` 在**类型层**就无 force / ignore / warn_only。

    对应 AC-IB-18-04：「错误信息指明非法项名（不回显其值），错误信息、日志与界面提示中均不含凭据值」；
    AC-IB-18-02：「系统不提供『强制继续 / 忽略错误』开关」。
    """
    # 类型层事实：字段集是刻意的（无「带病继续」的表达能力）
    assert set(ValidationReport.__dataclass_fields__) == {"ok", "errors"}
    assert set(ValidationErrorItem.__dataclass_fields__) == {"path", "code", "message"}
    for banned in ("force", "ignore", "warn_only"):
        assert banned not in ValidationReport.__dataclass_fields__, f"ValidationReport 竟有 {banned} 字段"

    # 定义文档只出现**键名**（其值一律经环境变量注入；此处仅放占位符，非真实凭据）
    key_name = "IB_R7_PLACEHOLDER_KEY"
    sentinel_value = "r7-placeholder-not-a-real-credential"
    doc = _doc(
        experts=(
            # REV-17（ADR-36）：`fallback_prompt` 已从 ExpertSpecInput 移除，故把
            # 「不得回显的敏感样值」放进同样自由文本的 `keywords`（本用例的意图是
            # 「文档里的任意文本都不会被错误体回显」，与承载它的具体字段无关）。
            ExpertSpecInput(
                name="a",
                cn_label="标签",
                keywords=(f"凭据请经环境变量 {key_name} 注入（定义文档只出现键名）",),
                exemplars=(),
                is_data_expert=False,
                is_delegating=False,
                is_default=True,
            ),
            _expert("b", cn_label="   "),  # 故意制造一条错误（cn_label 空）以便检视错误体
        )
    )

    previous = os.environ.get(key_name)
    os.environ[key_name] = sentinel_value
    try:
        with_env = validate(doc, known_tools=KNOWN_TOOLS)
    finally:
        if previous is None:
            os.environ.pop(key_name, None)
        else:
            os.environ[key_name] = previous
    without_env = validate(doc, known_tools=KNOWN_TOOLS)

    assert with_env.ok is False and without_env.ok is False
    # 校验结果与环境中是否存在该凭据键完全无关（校验器不读环境、不回显值）
    assert with_env == without_env
    rendered = repr(with_env) + "".join(i.message + i.path for i in with_env.errors)
    assert sentinel_value not in rendered, "错误体回显了凭据值"
    assert key_name in rendered or any(i.path.startswith("experts[") for i in with_env.errors)
    for item in with_env.errors:
        assert item.message and item.path and item.code


# --------------------------------------------------------------------------- #
# TC-UNIT-061 —— AC-IB-18-01 / AC-IB-18-03：合法即通过；默认专家不变量不可绕过
# --------------------------------------------------------------------------- #


def test_TC_UNIT_061_valid_passes_and_default_expert_invariant_is_not_bypassable():
    """[TC-UNIT-061] US-IB-18 / AC-IB-18-01 + AC-IB-18-03：合法定义通过并派生出装配所需视图；
    「默认专家恰好一个」的约束**不可被绕过**（无强制继续入口）。

    对应 AC-IB-18-03：「试图移除默认专家或使其不唯一 → 校验拒绝；该约束不可被配置或界面绕过」。
    """
    good = _doc()
    report = validate(good, known_tools=KNOWN_TOOLS)
    assert report.ok is True and report.errors == ()

    view = derive(good)
    assert [e.name for e in view.experts] == ["a", "b"]
    assert view.capability_digest and "search_knowledge" in view.capability_digest
    assert tuple(view.graph_config.nodes) == ("route", "a", "b")
    assert view.experts[0].is_default is True

    # 不变量不可绕过：无论其余字段多「合法」，默认专家 0 个 / ≥2 个一律拒绝
    zero_default = _doc(experts=(_expert("a"), _expert("b")))
    two_default = _doc(experts=(_expert("a", is_default=True), _expert("b", is_default=True)))
    for label, doc in (("移除默认专家", zero_default), ("默认专家不唯一", two_default)):
        bad = validate(doc, known_tools=KNOWN_TOOLS)
        assert bad.ok is False, f"{label}竟通过校验"
        assert "expert_default_count" in _codes(bad)

    # 无「强制继续」签名通道：validate / admit 均不接受 force/ignore/warn_only 参数
    assert set(inspect.signature(validate).parameters) == {"doc", "known_tools"}
    from ibweb.composition import admit

    assert set(inspect.signature(admit).parameters) == {"doc", "store"}
