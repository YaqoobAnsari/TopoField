"""Procedural institutional-scale HDG generator.

WHY THIS EXISTS: the real InstBuild benchmark (human-annotated institutional
buildings) does not exist yet and cannot be created without annotation labor. To
develop and stress-test the HDG stack at institutional scale NOW, we generate
synthetic buildings with a plausible functional hierarchy, typed/directed
adjacency, and geometry. Plan §6.5 explicitly permits synthetic composition for
PRETRAINING / method development, never for evaluation.

INTEGRITY: every graph is stamped `synthetic: true` in metadata. Do not use these
for any evaluation claim. Real numbers on real data come from InstBuild.

Output is always schema-valid (topofield.graph.validate.validate passes). The
functional-zone ground truth for a room is its level-1 (wing) ancestor via E_c.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

# Wing function -> plausible room-type palette (weighted by first entries).
FUNCTIONS: dict[str, list[str]] = {
    "ICU": ["icu_room", "icu_room", "isolation_room", "nurse_station"],
    "Ward": ["patient_room", "patient_room", "patient_room", "nurse_station", "treatment_room"],
    "Surgery": ["operating_room", "prep_room", "recovery_room", "scrub_room"],
    "Diagnostics": ["imaging_room", "lab", "exam_room", "reading_room"],
    "Admin": ["office", "office", "meeting_room", "records", "reception"],
    "Outpatient": ["consult_room", "exam_room", "waiting_room", "office"],
}

# Sensitive room types whose corridor door is often access-controlled (directed).
ACCESS_CONTROLLED = {"isolation_room", "operating_room", "records", "imaging_room", "icu_room"}

# Rough per-type floor area (m^2) means; sampled with jitter.
_AREA_MEAN = {
    "icu_room": 28,
    "isolation_room": 26,
    "nurse_station": 22,
    "patient_room": 24,
    "treatment_room": 30,
    "operating_room": 45,
    "prep_room": 20,
    "recovery_room": 26,
    "scrub_room": 12,
    "imaging_room": 40,
    "lab": 35,
    "exam_room": 16,
    "reading_room": 18,
    "office": 15,
    "meeting_room": 28,
    "records": 20,
    "reception": 24,
    "consult_room": 16,
    "waiting_room": 40,
}


def _room_geometry(rng: random.Random, room_type: str, cx: float, cy: float) -> dict[str, Any]:
    area = max(6.0, rng.gauss(_AREA_MEAN.get(room_type, 20), 3.0))
    aspect = rng.uniform(1.0, 1.8)
    h = math.sqrt(area / aspect)
    w = aspect * h
    perimeter = 2 * (w + h)
    return {
        "type": room_type,
        "area": round(area, 2),
        "aspect_ratio": round(aspect, 3),
        "perimeter": round(perimeter, 2),
        "centroid": [round(cx, 4), round(cy, 4)],
    }


def generate_hdg(
    seed: int,
    n_wings: int = 4,
    rooms_per_wing: tuple[int, int] = (24, 34),
    cross_wing_doors: int = 3,
    directed_fraction: float = 0.15,
    building_id: str | None = None,
) -> dict[str, Any]:
    """Generate one schema-valid synthetic institutional HDG.

    Layout: wings are vertical bands across the unit square; each wing has a
    central corridor with rooms stacked on both sides (outer rooms sit near the
    building envelope, which the thermal surrogate reads as exterior exposure).
    """
    rng = random.Random(seed)
    bid = building_id or f"synthetic_{seed:04d}"

    functions = rng.sample(list(FUNCTIONS), k=min(n_wings, len(FUNCTIONS)))
    while len(functions) < n_wings:  # allow repeats if more wings than functions
        functions.append(rng.choice(list(FUNCTIONS)))

    nodes: list[dict[str, Any]] = [{"id": "building", "level": 0, "attrs": {"name": bid}}]
    containment: list[dict[str, Any]] = []
    adjacency: list[dict[str, Any]] = []
    rooms_by_wing: dict[int, list[str]] = {}

    band_w = 1.0 / n_wings
    for w, func in enumerate(functions):
        wing_id, corr_id = f"wing_{w}", f"corr_{w}"
        n_rooms = rng.randint(*rooms_per_wing)
        rooms_by_wing[w] = []

        # geometry band for this wing
        wx0 = w * band_w
        per_side = math.ceil(n_rooms / 2)
        room_h = 0.9 / per_side

        prev_by_side: dict[int, str | None] = {0: None, 1: None}
        for i in range(n_rooms):
            side, row = i % 2, i // 2
            cx = wx0 + band_w * (0.22 if side == 0 else 0.78)
            cy = 0.05 + (row + 0.5) * room_h
            rtype = rng.choice(FUNCTIONS[func])
            rid = f"r_{w}_{i}"
            nodes.append({"id": rid, "level": 3, "attrs": _room_geometry(rng, rtype, cx, cy)})
            containment.append({"source": corr_id, "target": rid})
            rooms_by_wing[w].append(rid)
            # door to the corridor — access-controlled (directed) for sensitive rooms
            if rtype in ACCESS_CONTROLLED and rng.random() < directed_fraction * 2.5:
                door_delta = rng.choice(["forward", "backward"])
            else:
                door_delta = "bidirectional"
            adjacency.append(
                {"source": rid, "target": corr_id, "tau": "door-connected", "delta": door_delta}
            )
            # wall-adjacency to the previous room on the same side (shares a wall)
            if prev_by_side[side] is not None:
                adjacency.append(
                    {
                        "source": prev_by_side[side],
                        "target": rid,
                        "tau": "wall-adjacent",
                        "delta": "bidirectional",
                    }
                )
            prev_by_side[side] = rid

        # corridor + wing nodes
        wing_area = round(sum(n["attrs"]["area"] for n in nodes if n["id"] in rooms_by_wing[w]), 1)
        nodes.append(
            {
                "id": corr_id,
                "level": 2,
                "attrs": {"length": round(0.9 * 30, 1), "connected_room_count": n_rooms},
            }
        )
        nodes.append(
            {
                "id": wing_id,
                "level": 1,
                "attrs": {
                    "function_label": func,
                    "aggregate_area": wing_area,
                    "room_count": n_rooms,
                },
            }
        )
        containment.append({"source": "building", "target": wing_id})
        containment.append({"source": wing_id, "target": corr_id})

    # cross-wing doors (the edges a tree cannot hold); some access-controlled
    for _ in range(cross_wing_doors):
        if n_wings < 2:
            break
        wa, wb = rng.sample(range(n_wings), 2)
        ra, rb = rng.choice(rooms_by_wing[wa]), rng.choice(rooms_by_wing[wb])
        delta = "forward" if rng.random() < directed_fraction else "bidirectional"
        adjacency.append({"source": ra, "target": rb, "tau": "door-connected", "delta": delta})

    return {
        "version": "0.1",
        "metadata": {
            "generated_by": "topofield.data.synthetic v0.1",
            "source": "procedural",
            "building_id": bid,
            "synthetic": True,
            "seed": seed,
            "notes": "SYNTHETIC — method development / pretraining only (plan §6.5). "
            "NOT real InstBuild; never used for evaluation claims.",
        },
        "nodes": nodes,
        "containment_edges": containment,
        "adjacency_edges": adjacency,
    }


def generate_corpus(
    out_dir: str | Path, n_buildings: int = 30, seed0: int = 0, **kwargs: Any
) -> list[Path]:
    """Generate and validate a corpus of synthetic HDGs written as *.hdg.json."""
    from ..graph.validate import validate  # local import to keep module light

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for k in range(n_buildings):
        g = generate_hdg(seed=seed0 + k, **kwargs)
        result = validate(g)
        if not result.ok:
            raise RuntimeError(f"generated graph {k} failed validation: {result.errors[:3]}")
        p = out / f"{g['metadata']['building_id']}.hdg.json"
        p.write_text(json.dumps(g, indent=2), encoding="utf-8")
        paths.append(p)
    return paths


def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Generate a synthetic institutional HDG corpus")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--n", type=int, default=30, help="number of buildings")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--wings", type=int, default=4)
    args = ap.parse_args()
    paths = generate_corpus(args.out, n_buildings=args.n, seed0=args.seed0, n_wings=args.wings)
    total_rooms = 0
    for p in paths:
        total_rooms += sum(1 for n in json.loads(p.read_text())["nodes"] if n["level"] == 3)
    print(f"wrote {len(paths)} graphs to {args.out}; ~{total_rooms // len(paths)} rooms/bldg avg")


if __name__ == "__main__":
    _main()
