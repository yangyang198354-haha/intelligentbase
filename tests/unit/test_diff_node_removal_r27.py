"""[REV-27 / GROUP_D] 服务端差异清单对“删除节点”的输出契约（前端 publishDiff.formatDiffLine 的输入形态）。

溯源：US-011（AC-011-01 差异含被删节点及其相连边的删除项；AC-011-02 净变化为零不产生差异）。
层级：单元（纯函数，无 I/O）。后端本轮未改动，本文件只锁定既有行为，作为前端“中文节点类型”展示的数据前提。
"""

from __future__ import annotations

from dataclasses import replace

from config_r26_support import expert, make_v2_document

from ib.config.versioning import build_snapshot, diff_snapshots
from ib.core import PromptLayers


def _snap(graph_edit=None):
    experts = (expert("a", default=True), expert("b"))
    doc = make_v2_document("p", experts)
    if graph_edit is not None:
        doc = make_v2_document("p", experts, graph_edit(doc.graph))
    return build_snapshot(doc, {e.name: PromptLayers(f"{e.name} 主提示词", None) for e in experts})


def test_TC_UNIT_R27_001_removed_node_item_carries_kind_and_each_touching_edge_is_listed():
    """AC-011-01：删除节点 b → node_removed(b, before=节点类型, after=None)，且其相连边各有 1 条 edge_removed。"""
    base = _snap()
    touching = sorted(e.id for e in base.definition.graph.edges if "b" in (e.source, e.target))
    assert touching, "夹具应含与 b 相连的边"

    def drop_b(g):
        return replace(
            g,
            nodes=tuple(n for n in g.nodes if n.id != "b"),
            edges=tuple(e for e in g.edges if "b" not in (e.source, e.target)),
        )

    items = diff_snapshots(base, _snap(drop_b))
    removed = [i for i in items if i.kind == "node_removed"]
    assert [(i.object_id, i.before, i.after) for i in removed] == [("b", "agent", None)]
    assert sorted(i.object_id for i in items if i.kind == "edge_removed") == touching
    assert not [i for i in items if i.kind == "node_added"]


def test_TC_UNIT_R27_002_identical_graph_has_no_diff_items():
    """AC-011-02：新增又删除（净变化为零）→ 图与基线相同 → 差异清单为空。"""
    assert diff_snapshots(_snap(), _snap()) == ()
