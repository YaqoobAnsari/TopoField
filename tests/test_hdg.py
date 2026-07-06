"""Structural truths of the canonical hospital toy (docs/research_plan_final.md §4.2).

If code disagrees with these, the code is wrong (CLAUDE.md).
"""

import pytest

from topofield.graph import HDG


def _level1_ancestor(hdg: HDG, node: str) -> str:
    """Walk containment parents up to the wing/zone (level 1)."""
    parent = {e["target"]: e["source"] for e in hdg.containment_edges}
    cur = node
    while cur in parent and hdg.level[cur] > 1:
        cur = parent[cur]
    return cur


def test_counts(toy_graph):
    hdg = HDG.from_dict(toy_graph)
    assert len(hdg.nodes) == 10
    assert len(hdg.containment_edges) == 9
    assert len(hdg.adjacency_edges) == 7


def test_level_distribution(toy_graph):
    hdg = HDG.from_dict(toy_graph)
    assert len(hdg.nodes_at_level(0)) == 1  # hospital
    assert len(hdg.nodes_at_level(1)) == 2  # wings
    assert len(hdg.nodes_at_level(2)) == 2  # corridors
    assert len(hdg.nodes_at_level(3)) == 5  # rooms


def test_cross_hierarchy_door_exists(toy_graph):
    """Nurse<->Records is a door across wings — the edge a tree cannot hold."""
    hdg = HDG.from_dict(toy_graph)
    pairs = {frozenset((e["source"], e["target"])) for e in hdg.adjacency_edges}
    assert frozenset(("nurse", "records")) in pairs
    assert _level1_ancestor(hdg, "nurse") == "icu_wing"
    assert _level1_ancestor(hdg, "records") == "admin_wing"
    assert _level1_ancestor(hdg, "nurse") != _level1_ancestor(hdg, "records")


def test_cross_hierarchy_door_is_directed(toy_graph):
    """The badge-controlled door is a directed (forward) access edge."""
    hdg = HDG.from_dict(toy_graph)
    edge = next(
        e for e in hdg.adjacency_edges if {e["source"], e["target"]} == {"nurse", "records"}
    )
    assert hdg.delta_of(edge) == "forward"
    assert edge["source"] == "nurse" and edge["target"] == "records"


def test_wall_edge_is_not_traversable(toy_graph):
    """icu_1<->icu_2 is wall-adjacent: present in E_a but not in the circulation graph."""
    hdg = HDG.from_dict(toy_graph)
    full = hdg.to_adjacency_graph(traversable_only=False)
    trav = hdg.to_adjacency_graph(traversable_only=True)
    assert full.has_edge("icu_1", "icu_2")
    assert not trav.has_edge("icu_1", "icu_2")


def test_corridor_a_is_a_betweenness_hub(toy_graph):
    """Corridor A outranks the ordinary rooms it serves and is a max-betweenness node."""
    hdg = HDG.from_dict(toy_graph)
    bt = hdg.betweenness()  # circulation graph (wall edges excluded)
    for room in ("icu_1", "icu_2", "office"):
        assert bt["corr_a"] > bt[room]
    assert bt["corr_a"] == pytest.approx(max(bt.values()))


def test_cross_door_is_load_bearing(toy_graph):
    """Removing the cross-wing door collapses Nurse & Records betweenness to 0 —
    quantifying why the cross-hierarchy edge matters (heat/traffic use it)."""
    hdg = HDG.from_dict(toy_graph)
    bt_with = hdg.betweenness()
    assert bt_with["nurse"] > 0
    assert bt_with["records"] > 0

    without = {
        **toy_graph,
        "adjacency_edges": [
            e
            for e in toy_graph["adjacency_edges"]
            if {e["source"], e["target"]} != {"nurse", "records"}
        ],
    }
    bt_without = HDG.from_dict(without).betweenness()
    assert bt_without["nurse"] == pytest.approx(0.0)
    assert bt_without["records"] == pytest.approx(0.0)


def test_stats_shape(toy_graph):
    stats = HDG.from_dict(toy_graph).stats()
    assert stats["num_nodes"] == 10
    assert stats["num_containment_edges"] == 9
    assert stats["num_adjacency_edges"] == 7
    assert stats["hierarchy_depth"] == 3  # hospital -> wing -> corridor -> room
