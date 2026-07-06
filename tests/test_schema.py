"""The schema + semantic validator are the contract. These tests pin it."""

from topofield.graph import validate, validate_file


def test_fixture_is_valid(toy_path):
    result = validate_file(toy_path)
    assert result.ok, result.errors


def test_bad_tau_is_schema_error(toy_graph):
    toy_graph["adjacency_edges"][0]["tau"] = "teleporter"
    result = validate(toy_graph)
    assert not result.ok
    assert any("tau" in e or "teleporter" in e for e in result.schema_errors)


def test_missing_room_type_is_schema_error(toy_graph):
    # A level-3 room requires `type` (area is optional per ADR 0004).
    for n in toy_graph["nodes"]:
        if n["id"] == "icu_1":
            del n["attrs"]["type"]
    result = validate(toy_graph)
    assert not result.ok
    assert result.schema_errors


def test_room_without_area_is_valid(toy_graph):
    # ADR 0004: extraction output may omit area; still schema-valid.
    for n in toy_graph["nodes"]:
        if n["id"] == "icu_1":
            del n["attrs"]["area"]
    assert validate(toy_graph).ok


def test_dangling_edge_is_semantic_error(toy_graph):
    toy_graph["adjacency_edges"].append(
        {"source": "nurse", "target": "ghost_room", "tau": "door-connected"}
    )
    result = validate(toy_graph)
    assert not result.ok
    assert any("unknown node" in e for e in result.semantic_errors)


def test_containment_level_skip_is_semantic_error(toy_graph):
    # hospital(L0) -> corr_a(L2) skips a level; L(parent) must equal L(child)-1.
    toy_graph["containment_edges"].append({"source": "hospital", "target": "corr_a"})
    result = validate(toy_graph)
    assert not result.ok
    assert any("level-adjacency" in e for e in result.semantic_errors)


def test_multiple_parents_breaks_forest(toy_graph):
    # Give icu_1 a second parent -> no longer a forest.
    toy_graph["containment_edges"].append({"source": "corr_b", "target": "icu_1"})
    result = validate(toy_graph)
    assert not result.ok
    assert any("multiple parents" in e or "forest" in e for e in result.semantic_errors)


def test_adjacency_endpoint_level_enforced(toy_graph):
    # An adjacency edge onto a level-1 wing is illegal (E_a endpoints in {2,3}).
    toy_graph["adjacency_edges"].append(
        {"source": "corr_a", "target": "icu_wing", "tau": "corridor-link"}
    )
    result = validate(toy_graph)
    assert not result.ok
    assert any("levels {2,3}" in e or "L1" in e for e in result.semantic_errors)
