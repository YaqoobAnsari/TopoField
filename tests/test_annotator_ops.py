"""Annotation engine: tree-safe HDG edits that never produce an invalid graph."""

import pytest

from topofield.annotator import operations as ops
from topofield.extraction.tesseract_adapter import tesseract_json_to_hdg
from topofield.graph import validate
from topofield.metrics import navigational_completeness

# Two corridors, four rooms — a clean extraction scaffold to zone/edit.
_TESS = {
    "nodes": [
        {"id": "room_1", "type": "room", "position": [0, 0]},
        {"id": "room_2", "type": "room", "position": [0, 10]},
        {"id": "room_3", "type": "room", "position": [50, 0]},
        {"id": "room_4", "type": "room", "position": [50, 10]},
        {"id": "corridor_1", "type": "corridor", "position": [10, 5]},
        {"id": "corridor_2", "type": "corridor", "position": [60, 5]},
    ],
    "edges": [
        {"source": "room_1", "target": "corridor_1"},
        {"source": "room_2", "target": "corridor_1"},
        {"source": "room_3", "target": "corridor_2"},
        {"source": "room_4", "target": "corridor_2"},
        {"source": "corridor_1", "target": "corridor_2"},
    ],
}


@pytest.fixture
def base():
    return tesseract_json_to_hdg(_TESS, building_id="b")


def _parent(hdg, node):
    return {e["target"]: e["source"] for e in hdg["containment_edges"]}[node]


def _edge_set(hdg):
    return {frozenset((e["source"], e["target"])) for e in hdg["adjacency_edges"]}


def test_assign_rooms_to_zone_rewires_only_containment(base):
    before_edges = _edge_set(base)
    out = ops.assign_rooms_to_zone(base, ["room_1", "room_2"], "ICU")
    assert validate(out).ok
    # a new zone with the label now parents corridor_1
    zone = _parent(out, "corridor_1")
    assert any(n["id"] == zone and n["attrs"]["function_label"] == "ICU" for n in out["nodes"])
    assert _parent(out, "room_1") == "corridor_1"  # rooms follow their corridor
    # physical adjacency (E_a) is untouched by zoning
    assert _edge_set(out) == before_edges
    # original is not mutated
    assert not any(
        n["attrs"].get("function_label") == "ICU" for n in base["nodes"] if n["level"] == 1
    )


def test_empty_wing_pruned_after_all_corridors_rezoned(base):
    out = ops.assign_corridors_to_zone(base, ["corridor_1"], "ICU")
    out = ops.assign_corridors_to_zone(out, ["corridor_2"], "Admin")
    assert validate(out).ok
    assert not any(n["id"] == "wing_default" for n in out["nodes"])  # emptied -> pruned
    labels = {n["attrs"]["function_label"] for n in out["nodes"] if n["level"] == 1}
    assert labels == {"ICU", "Admin"}


def test_set_edge_type_and_reject_bad_tau(base):
    out = ops.set_edge_type(base, "corridor_1", "corridor_2", "door-connected")
    edge = next(
        e
        for e in out["adjacency_edges"]
        if {e["source"], e["target"]} == {"corridor_1", "corridor_2"}
    )
    assert edge["tau"] == "door-connected"
    with pytest.raises(ValueError):
        ops.set_edge_type(base, "corridor_1", "corridor_2", "teleporter")


def test_set_edge_direction_normalizes_endpoints(base):
    out = ops.set_edge_direction(base, "room_1", "corridor_1", "forward")
    edge = next(
        e for e in out["adjacency_edges"] if {e["source"], e["target"]} == {"room_1", "corridor_1"}
    )
    assert edge["source"] == "room_1" and edge["target"] == "corridor_1"
    assert edge["delta"] == "forward"
    with pytest.raises(ValueError):
        ops.set_edge_direction(base, "room_1", "corridor_1", "sideways")


def test_add_and_remove_adjacency(base):
    out = ops.add_adjacency(base, "room_1", "room_3", "wall-adjacent")
    assert frozenset(("room_1", "room_3")) in _edge_set(out)
    out2 = ops.remove_adjacency(out, "room_1", "room_3")
    assert frozenset(("room_1", "room_3")) not in _edge_set(out2)
    with pytest.raises(ValueError):
        ops.add_adjacency(base, "room_1", "building", "door-connected")  # bad endpoint level


def test_move_room_reparents(base):
    out = ops.move_room(base, "room_1", "corridor_2")
    assert _parent(out, "room_1") == "corridor_2"
    assert validate(out).ok


def test_apply_operation_dispatch(base):
    out = ops.apply_operation(
        base, "set_function_label", zone_id="wing_default", function_label="Mixed"
    )
    assert (
        next(n for n in out["nodes"] if n["id"] == "wing_default")["attrs"]["function_label"]
        == "Mixed"
    )
    with pytest.raises(ValueError):
        ops.apply_operation(base, "nonexistent_op")


def test_navigational_completeness(toy_graph):
    assert navigational_completeness(toy_graph) == pytest.approx(1.0)  # fully reachable
    disconnected = {
        **toy_graph,
        "adjacency_edges": [
            e
            for e in toy_graph["adjacency_edges"]
            if {e["source"], e["target"]} != {"nurse", "records"}
        ],
    }
    assert navigational_completeness(disconnected) < 1.0  # cross-wing link removed
