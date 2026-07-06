"""Ingest HDGs from disk and split them for training/evaluation.

`HDGDataset` loads a directory of `*.hdg.json` (validating each), exposes the
graphs, and derives building ids for LOBO. `lobo_splits` yields Leave-One-Building-
Out folds — split by BUILDING, never by floor (plan §11.5). This is the layer that
turns a corpus (synthetic OR real, from the Tesseract adapter + annotation tool)
into something the models/eval consume.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..graph.validate import validate


def building_id_of(graph: dict[str, Any], fallback: str = "") -> str:
    """Building identity for LOBO = metadata.building_id (floors of one building
    share it), else the L0 building node's name, else a fallback."""
    md = graph.get("metadata", {}) or {}
    if md.get("building_id"):
        return str(md["building_id"])
    for n in graph.get("nodes", []):
        if n.get("level") == 0:
            return str(n.get("attrs", {}).get("name", fallback))
    return fallback


def load_hdg_dir(
    root: str | Path, validate_each: bool = True, pattern: str = "**/*.hdg.json"
) -> list[dict[str, Any]]:
    graphs: list[dict[str, Any]] = []
    for p in sorted(Path(root).glob(pattern)):
        g = json.loads(p.read_text(encoding="utf-8"))
        if validate_each:
            r = validate(g)
            if not r.ok:
                raise ValueError(f"{p} is not a valid HDG: {r.errors[:3]}")
        g.setdefault("metadata", {}).setdefault("building_id", building_id_of(g, p.stem))
        graphs.append(g)
    return graphs


def group_by_building(graphs: list[dict[str, Any]]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, g in enumerate(graphs):
        groups[building_id_of(g, str(i))].append(i)
    return dict(groups)


def lobo_splits(
    graphs: list[dict[str, Any]],
) -> Iterator[tuple[str, list[int], list[int]]]:
    """Yield (held_out_building, train_indices, test_indices) — one fold per
    building. All floors of the held-out building go to test."""
    groups = group_by_building(graphs)
    for building in sorted(groups):
        test = groups[building]
        test_set = set(test)
        train = [i for i in range(len(graphs)) if i not in test_set]
        yield building, train, test


class HDGDataset:
    """A validated, indexable corpus of HDGs loaded from a directory."""

    def __init__(
        self, root: str | Path, validate_each: bool = True, pattern: str = "**/*.hdg.json"
    ):
        self.root = Path(root)
        self.graphs = load_hdg_dir(root, validate_each=validate_each, pattern=pattern)

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, i: int) -> dict[str, Any]:
        return self.graphs[i]

    @property
    def building_ids(self) -> list[str]:
        return [building_id_of(g, str(i)) for i, g in enumerate(self.graphs)]

    def num_buildings(self) -> int:
        return len(group_by_building(self.graphs))

    def to_tensors(self, i: int) -> dict[str, Any]:
        """Feature tensors for graph i (lazy import so the loader stays torch-free)."""
        from ..models.data import build_graph_tensors

        return build_graph_tensors(self.graphs[i])

    def lobo_splits(self) -> Iterator[tuple[str, list[int], list[int]]]:
        return lobo_splits(self.graphs)
