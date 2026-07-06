"""Pure, validated HDG editing operations (the annotation engine).

Every operation takes an HDG dict and returns a NEW, schema-valid HDG dict (deep
copy; originals are never mutated). Each ends with `_validated`, which runs the
two-layer validator and raises if the edit would break the contract — so the UI
can never persist an invalid graph.

Operation families:
  zoning (E_c only)      : assign_corridors_to_zone, assign_rooms_to_zone,
                           set_function_label
  physical edges (E_a)   : set_edge_type, set_edge_direction, add_adjacency,
                           remove_adjacency
  fixups                 : move_room (reparent a room under another corridor)
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from ..graph import DELTA, TAU, validate

HDGDict = dict[str, Any]


def _validated(hdg: HDGDict) -> HDGDict:
    result = validate(hdg)
    if not result.ok:
        raise ValueError(f"operation would produce an invalid HDG: {result.errors[:5]}")
    return hdg


def _index(hdg: HDGDict) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in hdg["nodes"]}


def _fresh_id(by_id: dict[str, Any], prefix: str) -> str:
    i = 1
    while f"{prefix}_{i}" in by_id:
        i += 1
    return f"{prefix}_{i}"


def _building_id(hdg: HDGDict) -> str:
    return next(n["id"] for n in hdg["nodes"] if n["level"] == 0)


def _prune_empty_wings(hdg: HDGDict) -> None:
    """Remove level-1 wings that no longer contain any corridor. Wings carry no E_a
    edges, so this is always safe (no dangling adjacency)."""
    by_id = _index(hdg)
    children: dict[str, list[str]] = defaultdict(list)
    for e in hdg["containment_edges"]:
        children[e["source"]].append(e["target"])
    empty = {
        i
        for i, n in by_id.items()
        if n["level"] == 1 and not any(by_id.get(t, {}).get("level") == 2 for t in children[i])
    }
    if empty:
        hdg["nodes"] = [n for n in hdg["nodes"] if n["id"] not in empty]
        hdg["containment_edges"] = [
            e
            for e in hdg["containment_edges"]
            if e["source"] not in empty and e["target"] not in empty
        ]


# --- zoning (E_c only) --------------------------------------------------
def assign_corridors_to_zone(
    hdg: HDGDict, corridor_ids: list[str], function_label: str, zone_id: str | None = None
) -> HDGDict:
    """Group corridors (and, with them, their rooms) into a functional zone (wing,
    level 1). Rewires containment only; adjacency is untouched."""
    hdg = deepcopy(hdg)
    by_id = _index(hdg)
    for c in corridor_ids:
        if c not in by_id or by_id[c]["level"] != 2:
            raise ValueError(f"'{c}' is not a corridor (level 2)")
    if not function_label:
        raise ValueError("function_label is required")

    if zone_id is None:
        zone_id = _fresh_id(by_id, "zone")
    if zone_id not in by_id:
        hdg["nodes"].append(
            {"id": zone_id, "level": 1, "attrs": {"function_label": function_label}}
        )
        hdg["containment_edges"].append({"source": _building_id(hdg), "target": zone_id})
    else:
        if by_id[zone_id]["level"] != 1:
            raise ValueError(f"'{zone_id}' exists but is not a zone/wing")
        by_id[zone_id]["attrs"]["function_label"] = function_label

    corridor_set = set(corridor_ids)
    level = {n["id"]: n["level"] for n in hdg["nodes"]}
    kept = [
        e
        for e in hdg["containment_edges"]
        if not (e["target"] in corridor_set and level.get(e["source"]) == 1)
    ]
    kept += [{"source": zone_id, "target": c} for c in corridor_ids]
    hdg["containment_edges"] = kept
    _prune_empty_wings(hdg)
    return _validated(hdg)


def assign_rooms_to_zone(
    hdg: HDGDict, room_ids: list[str], function_label: str, zone_id: str | None = None
) -> HDGDict:
    """Lasso rooms into a zone. Resolves each room to its containing corridor and
    assigns those corridors (whole-corridor granularity — the tree keeps one wing
    per corridor). Use move_room first to split a corridor across zones."""
    parent = {e["target"]: e["source"] for e in hdg["containment_edges"]}
    corridors = sorted({parent[r] for r in room_ids if r in parent})
    if not corridors:
        raise ValueError("no containing corridors found for the given rooms")
    return assign_corridors_to_zone(hdg, corridors, function_label, zone_id)


def set_function_label(hdg: HDGDict, zone_id: str, function_label: str) -> HDGDict:
    hdg = deepcopy(hdg)
    by_id = _index(hdg)
    if zone_id not in by_id or by_id[zone_id]["level"] != 1:
        raise ValueError(f"'{zone_id}' is not a zone/wing")
    if not function_label:
        raise ValueError("function_label is required")
    by_id[zone_id].setdefault("attrs", {})["function_label"] = function_label
    return _validated(hdg)


def move_room(hdg: HDGDict, room_id: str, corridor_id: str) -> HDGDict:
    """Reparent a room under a different corridor (fix extraction errors / split a
    corridor across zones)."""
    hdg = deepcopy(hdg)
    by_id = _index(hdg)
    if by_id.get(room_id, {}).get("level") != 3:
        raise ValueError(f"'{room_id}' is not a room")
    if by_id.get(corridor_id, {}).get("level") != 2:
        raise ValueError(f"'{corridor_id}' is not a corridor")
    ce = [e for e in hdg["containment_edges"] if e["target"] != room_id]
    ce.append({"source": corridor_id, "target": room_id})
    hdg["containment_edges"] = ce
    return _validated(hdg)


# --- physical edges (E_a) ----------------------------------------------
def _find_edge(hdg: HDGDict, u: str, v: str) -> dict[str, Any] | None:
    return next((e for e in hdg["adjacency_edges"] if {e["source"], e["target"]} == {u, v}), None)


def set_edge_type(hdg: HDGDict, u: str, v: str, tau: str) -> HDGDict:
    if tau not in TAU:
        raise ValueError(f"tau must be one of {TAU}")
    hdg = deepcopy(hdg)
    edge = _find_edge(hdg, u, v)
    if edge is None:
        raise ValueError(f"no adjacency edge between '{u}' and '{v}'")
    edge["tau"] = tau
    return _validated(hdg)


def set_edge_direction(hdg: HDGDict, source: str, target: str, delta: str) -> HDGDict:
    """Set access direction. delta='forward' means source->target (endpoints are
    normalized to the given (source, target))."""
    if delta not in DELTA:
        raise ValueError(f"delta must be one of {DELTA}")
    hdg = deepcopy(hdg)
    edge = _find_edge(hdg, source, target)
    if edge is None:
        raise ValueError(f"no adjacency edge between '{source}' and '{target}'")
    edge["source"], edge["target"], edge["delta"] = source, target, delta
    return _validated(hdg)


def add_adjacency(hdg: HDGDict, u: str, v: str, tau: str, delta: str = "bidirectional") -> HDGDict:
    if tau not in TAU:
        raise ValueError(f"tau must be one of {TAU}")
    hdg = deepcopy(hdg)
    by_id = _index(hdg)
    for x in (u, v):
        if by_id.get(x, {}).get("level") not in (2, 3):
            raise ValueError(f"adjacency endpoint '{x}' must be a corridor or room (level 2/3)")
    if _find_edge(hdg, u, v) is not None:
        raise ValueError(f"adjacency edge '{u}'-'{v}' already exists")
    hdg["adjacency_edges"].append({"source": u, "target": v, "tau": tau, "delta": delta})
    return _validated(hdg)


def remove_adjacency(hdg: HDGDict, u: str, v: str) -> HDGDict:
    hdg = deepcopy(hdg)
    before = len(hdg["adjacency_edges"])
    hdg["adjacency_edges"] = [
        e for e in hdg["adjacency_edges"] if {e["source"], e["target"]} != {u, v}
    ]
    if len(hdg["adjacency_edges"]) == before:
        raise ValueError(f"no adjacency edge between '{u}' and '{v}'")
    return _validated(hdg)


# Dispatch table for the API layer (name -> callable).
OPERATIONS = {
    "assign_corridors_to_zone": assign_corridors_to_zone,
    "assign_rooms_to_zone": assign_rooms_to_zone,
    "set_function_label": set_function_label,
    "move_room": move_room,
    "set_edge_type": set_edge_type,
    "set_edge_direction": set_edge_direction,
    "add_adjacency": add_adjacency,
    "remove_adjacency": remove_adjacency,
}


def apply_operation(hdg: HDGDict, name: str, **kwargs: Any) -> HDGDict:
    if name not in OPERATIONS:
        raise ValueError(f"unknown operation '{name}'")
    return OPERATIONS[name](hdg, **kwargs)
