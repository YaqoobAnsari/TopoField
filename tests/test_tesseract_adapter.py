"""Tesseract BuildingGraph -> HDG adapter (Phase 0 raster lane)."""

import json
from pathlib import Path

import pytest

from topofield.extraction.tesseract_adapter import tesseract_json_to_hdg
from topofield.graph import HDG, validate

# A small hand-built Tesseract-format graph exercising the tricky transforms.
TOY_TESS = {
    "nodes": [
        {"id": "room_1", "type": "room", "position": [10, 10], "pixels": 1200},
        {"id": "room_2", "type": "room", "position": [10, 50]},
        {"id": "corridor_main_1", "type": "corridor", "position": [50, 30]},
        {"id": "r2c_door_1", "type": "door", "position": [30, 10]},
        {"id": "exit_door_1", "type": "door", "position": [10, 90]},
        {"id": "outside_1", "type": "outside", "position": [10, 120]},
    ],
    "edges": [
        {"source": "room_1", "target": "r2c_door_1", "weight": 1},
        {"source": "corridor_main_1", "target": "r2c_door_1", "weight": 1},
        {"source": "room_2", "target": "exit_door_1", "weight": 1},
        {"source": "exit_door_1", "target": "outside_1", "weight": 1},
        {"source": "room_2", "target": "corridor_main_1", "weight": 1},
    ],
}


def _attrs(hdg, nid):
    return next(n["attrs"] for n in hdg["nodes"] if n["id"] == nid)


def test_toy_adapter_is_valid_and_well_formed():
    hdg = tesseract_json_to_hdg(TOY_TESS, building_id="toy")
    assert validate(hdg).ok
    h = HDG.from_dict(hdg)
    assert len(h.nodes_at_level(0)) == 1  # building
    assert len(h.nodes_at_level(1)) == 1  # placeholder wing
    assert len(h.nodes_at_level(2)) == 1  # corridor
    assert len(h.nodes_at_level(3)) == 2  # rooms
    # doors + outside are gone
    ids = h.node_ids
    assert "r2c_door_1" not in ids and "exit_door_1" not in ids and "outside_1" not in ids


def test_door_collapses_to_typed_edge():
    hdg = tesseract_json_to_hdg(TOY_TESS, building_id="toy")
    ea = {frozenset((e["source"], e["target"])): e for e in hdg["adjacency_edges"]}
    door_edge = ea[frozenset(("room_1", "corridor_main_1"))]
    assert door_edge["tau"] == "door-connected"
    assert door_edge.get("door_class") == "r2c"
    # direct room->corridor connectivity becomes a corridor-link
    assert ea[frozenset(("room_2", "corridor_main_1"))]["tau"] == "corridor-link"


def test_outside_dropped_marks_exterior_access():
    hdg = tesseract_json_to_hdg(TOY_TESS, building_id="toy")
    assert _attrs(hdg, "room_2").get("exterior_access") is True  # reached outside via exit door
    assert "exterior_access" not in _attrs(hdg, "room_1")


def test_area_taken_from_pixels_only_when_present():
    hdg = tesseract_json_to_hdg(TOY_TESS, building_id="toy")
    assert _attrs(hdg, "room_1")["area"] == 1200.0  # had pixels
    assert "area" not in _attrs(hdg, "room_2")  # never fabricated


def test_degenerate_no_corridor_synthesizes_hub():
    tess = {
        "nodes": [
            {"id": "room_1", "type": "room", "position": [0, 0]},
            {"id": "room_2", "type": "room", "position": [10, 10]},
        ],
        "edges": [{"source": "room_1", "target": "room_2", "weight": 1}],
    }
    hdg = tesseract_json_to_hdg(tess, building_id="degenerate")
    assert validate(hdg).ok
    assert any(n["id"] == "corridor_default" and n["level"] == 2 for n in hdg["nodes"])


_REAL = (
    Path(__file__).parents[1] / "third_party/tesseract/Results/Json/file_6/file_6_post_pruning.json"
)


@pytest.mark.skipif(not _REAL.exists(), reason="Tesseract clone/sample not present")
def test_real_tesseract_sample_converts_and_validates():
    tess = json.loads(_REAL.read_text())
    hdg = tesseract_json_to_hdg(tess, building_id="file_6")
    assert validate(hdg).ok
    h = HDG.from_dict(hdg)
    # sample had room:4, corridor:37, door:3 (doors collapse; no outside)
    assert len(h.nodes_at_level(3)) == 4
    assert len(h.nodes_at_level(2)) == 37
    assert len(h.nodes_at_level(1)) == 1
