"""Tesseract BuildingGraph -> HDG adapter (Phase 0 raster lane).

Analysis + design: docs/phase0/tesseract_analysis.md.

Tesseract (third_party/tesseract, pinned) emits a flat, typed, navigable graph:
    {"nodes": [{"id","type","position":[x,y],...}], "edges": [{"source","target",...}]}
node types {room, corridor, door, outside, transition}, UNDIRECTED edges; the door
class is encoded in the door id (`r2c_door_*`, `r2r_door_*`, `exit_door_*`).

This adapter converts that into a schema-valid HDG (schemas/hdg.schema.json):
  * door node + its incident edges  -> a single typed adjacency edge
    (tau="door-connected", door_class kept as metadata) between the room/corridor
    it joins — HDG models a door as an edge TYPE, not a node.
  * room / transition -> level 3 ; corridor -> level 2.
  * outside -> dropped; rooms/corridors that reached outside (directly or via an
    exit door) get attrs.exterior_access = true (useful for thermal exposure).
  * containment (E_c) -> a VALID scaffold: building(0) -> one placeholder wing(1,
    function_label="unassigned") -> corridors(2) -> rooms(3). The REAL functional
    hierarchy (zones/wings) and access DIRECTION are added by the annotation tool.

What this adapter deliberately does NOT invent (integrity):
  * room `area` is only set if Tesseract provided it (`pixels`/`area`); otherwise
    omitted (ADR 0004) — never fabricated.
  * `tau="wall-adjacent"` is not produced (Tesseract gives connectivity only);
    added later from segmentation.
  * all `delta` are bidirectional (direction is an annotation).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

_KEEP_TYPES = ("room", "corridor", "transition")


def _door_class(door_id: str) -> str:
    d = door_id.lower()
    for prefix in ("r2c", "r2r", "exit"):
        if d.startswith(prefix) or f"{prefix}_door" in d:
            return prefix
    return "door"


def _transition_type(node_id: str) -> str:
    d = node_id.lower()
    if "stair" in d:
        return "stairs"
    if "elev" in d or "lift" in d:
        return "elevator"
    return "transition"


def _normalize_positions(
    positions: dict[str, list[float] | None], image_size: tuple[float, float] | None
) -> dict[str, list[float]]:
    pts = {i: p for i, p in positions.items() if p}
    if not pts:
        return {}
    if image_size:
        w, h = image_size
        return {
            i: [min(1.0, max(0.0, p[0] / w)), min(1.0, max(0.0, p[1] / h))] for i, p in pts.items()
        }
    xs = [p[0] for p in pts.values()]
    ys = [p[1] for p in pts.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    dx, dy = (x1 - x0) or 1.0, (y1 - y0) or 1.0
    return {i: [(p[0] - x0) / dx, (p[1] - y0) / dy] for i, p in pts.items()}


def _tau_for(ta: str, tb: str) -> str:
    # corridor involved -> corridor-link; otherwise room/transition pair -> door-connected
    return "corridor-link" if ("corridor" in (ta, tb)) else "door-connected"


def tesseract_json_to_hdg(
    building_graph: dict[str, Any],
    image_size: tuple[float, float] | None = None,
    building_id: str = "building",
    floor: str | None = None,
    source_commit: str | None = None,
    validate_output: bool = True,
) -> dict[str, Any]:
    """Convert a Tesseract BuildingGraph JSON into a schema-valid HDG dict."""
    nodes = building_graph.get("nodes", [])
    edges = building_graph.get("edges", [])
    by_id = {n["id"]: n for n in nodes}
    type_of = {n["id"]: (n.get("type") or "") for n in nodes}

    adj: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in by_id and t in by_id:
            adj[s].add(t)
            adj[t].add(s)

    outside_ids = {i for i, ty in type_of.items() if ty == "outside"}
    door_ids = {i for i, ty in type_of.items() if ty == "door"}
    doors_to_outside = {d for d in door_ids if adj[d] & outside_ids}

    exterior: set[str] = set()
    for i in by_id:
        if type_of[i] in _KEEP_TYPES and (adj[i] & outside_ids or adj[i] & doors_to_outside):
            exterior.add(i)

    kept = [i for i in by_id if type_of[i] in _KEEP_TYPES]
    kept_set = set(kept)
    centroid = _normalize_positions({i: by_id[i].get("position") for i in by_id}, image_size)

    # --- adjacency edges (E_a) ---
    ea: dict[frozenset[str], dict[str, Any]] = {}

    def add_ea(a: str, b: str, tau: str, **meta: Any) -> None:
        if a == b or a not in kept_set or b not in kept_set:
            return
        ea.setdefault(frozenset((a, b)), {"tau": tau, **meta})

    for d in door_ids:  # collapse door nodes into typed edges
        nbrs = [x for x in adj[d] if x in kept_set]
        dc = _door_class(d)
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                add_ea(nbrs[i], nbrs[j], "door-connected", door_class=dc)

    for e in edges:  # remaining direct (non-door, non-outside) connectivity
        s, t = e.get("source"), e.get("target")
        if s in kept_set and t in kept_set:
            add_ea(s, t, _tau_for(type_of[s], type_of[t]))

    # --- containment (E_c) scaffold ---
    corridors = [i for i in kept if type_of[i] == "corridor"]
    leaves = [i for i in kept if type_of[i] in ("room", "transition")]
    if not corridors:  # degenerate floor with no corridor: synthesize one hub
        corridors = ["corridor_default"]
        centroid.setdefault("corridor_default", [0.5, 0.5])

    def _parent_corridor(leaf: str) -> str:
        connected = sorted(c for c in corridors if frozenset((leaf, c)) in ea)
        if connected:
            return connected[0]
        lc = centroid.get(leaf, [0.5, 0.5])  # else nearest corridor by centroid
        return min(
            corridors,
            key=lambda c: (
                (centroid.get(c, [0.5, 0.5])[0] - lc[0]) ** 2
                + (centroid.get(c, [0.5, 0.5])[1] - lc[1]) ** 2
            ),
        )

    parent_of = {leaf: _parent_corridor(leaf) for leaf in leaves}

    # --- assemble HDG ---
    hdg_nodes: list[dict[str, Any]] = [
        {
            "id": "building",
            "level": 0,
            "attrs": {"name": building_id, **({"floor": floor} if floor else {})},
        },
        {
            "id": "wing_default",
            "level": 1,
            "attrs": {"function_label": "unassigned", "room_count": len(leaves)},
        },
    ]
    for c in corridors:
        cattrs: dict[str, Any] = {}
        if c in centroid:
            cattrs["centroid"] = [round(centroid[c][0], 4), round(centroid[c][1], 4)]
        cattrs["connected_room_count"] = sum(1 for leaf in leaves if parent_of[leaf] == c)
        if c in exterior:
            cattrs["exterior_access"] = True
        hdg_nodes.append({"id": c, "level": 2, "attrs": cattrs})
    for leaf in leaves:
        src_node = by_id.get(leaf, {})
        rtype = "room" if type_of.get(leaf) == "room" else _transition_type(leaf)
        rattrs: dict[str, Any] = {"type": rtype}
        if leaf in centroid:
            rattrs["centroid"] = [round(centroid[leaf][0], 4), round(centroid[leaf][1], 4)]
        area = src_node.get("area") or src_node.get("pixels")
        if isinstance(area, (int, float)) and area > 0:
            rattrs["area"] = float(area)
        if leaf in exterior:
            rattrs["exterior_access"] = True
        hdg_nodes.append({"id": leaf, "level": 3, "attrs": rattrs})

    containment = [{"source": "building", "target": "wing_default"}]
    containment += [{"source": "wing_default", "target": c} for c in corridors]
    containment += [{"source": parent_of[leaf], "target": leaf} for leaf in leaves]

    adjacency = []
    for pair, meta in ea.items():
        a, b = sorted(pair)
        adjacency.append({"source": a, "target": b, "delta": "bidirectional", **meta})

    hdg = {
        "version": "0.1",
        "metadata": {
            "generated_by": "topofield.extraction.tesseract_adapter v0.1",
            "source": "tesseract",
            "source_commit": source_commit,
            "building_id": building_id,
            "floor": floor,
            "note": "Extraction scaffold: single placeholder wing 'unassigned' (real "
            "functional zones + access direction are added by the annotation tool); "
            "no wall-adjacent edges (connectivity only); centroids min-max normalized "
            "unless image_size given; area present only if Tesseract provided it.",
        },
        "nodes": hdg_nodes,
        "containment_edges": containment,
        "adjacency_edges": adjacency,
    }

    if validate_output:
        from ..graph.validate import validate

        result = validate(hdg)
        if not result.ok:
            raise ValueError(f"adapter produced an invalid HDG: {result.errors[:5]}")
    return hdg
