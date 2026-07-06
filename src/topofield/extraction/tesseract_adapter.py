"""Tesseract BuildingGraph -> HDG adapter (Phase 0 raster lane) — STUB.

Analysis + full mapping: docs/phase0/tesseract_analysis.md.

Tesseract (third_party/tesseract, pinned commit 24074a4a) emits a flat, typed,
navigable graph:
    {"nodes": [{"id","type","position":[x,y],"floor",...}], "edges": [...]}
with node types {room, door, corridor, outside, transition} and UNDIRECTED edges.

This adapter converts that into a schema-valid HDG dict (schemas/hdg.schema.json).
The core, non-obvious transformation:

  * HDG models a DOOR as an edge TYPE (tau=door-connected) between the room and
    corridor it joins — NOT as a node. So each Tesseract `door` node and its two
    incident edges are CONTRACTED into one adjacency edge with tau=door-connected
    (preserving r2c/r2r/exit typing), never dropping connectivity.
  * room -> level 3 (attrs.type from the interpreter; area from `pixels`;
    centroid from normalized `position`; aspect_ratio/perimeter computed).
  * corridor -> level 2 (length, connected_room_count).
  * transition (stairs/elevator) -> inter-floor structure (multi-floor).
  * outside -> building-exterior context (mapping decided in the adapter ADR).

What Tesseract does NOT provide and this lane must add downstream (not here):
  * functional hierarchy E_c (zone/wing/building) — annotation + heuristics
  * directed access delta — annotation
  * tau=wall-adjacent (non-door shared walls) — from segmentation masks

Output MUST pass topofield.graph.validate.validate() before it is written or used.
"""

from __future__ import annotations

from typing import Any

# Tesseract door classes -> retained as edge metadata when contracting door nodes.
DOOR_CLASS_R2C = "r2c"  # room-to-corridor
DOOR_CLASS_R2R = "r2r"  # room-to-room
DOOR_CLASS_EXIT = "exit"


def tesseract_json_to_hdg(building_graph: dict[str, Any]) -> dict[str, Any]:
    """Convert a Tesseract BuildingGraph JSON into a (schema-valid) HDG dict.

    Not yet implemented — see docs/phase0/tesseract_analysis.md for the mapping
    table. Implementing this (with a unit test against a Tesseract sample output
    and schema validation) is the next Phase-0 task.
    """
    raise NotImplementedError(
        "Phase-0 next task: implement the Tesseract->HDG contraction "
        "(door nodes -> tau=door-connected edges; room/corridor -> L3/L2; add "
        "attrs; validate). See docs/phase0/tesseract_analysis.md."
    )
