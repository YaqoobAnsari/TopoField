"""HDG -> tensors for the graph models (plan §8).

Builds per-graph tensors (no PyG Batch — graphs are small and processed one at a
time, which keeps the hierarchical pooling correct and simple):

  x          [N, F]  node features (level one-hot, geometry, degree, type one-hot)
  edge_index [2, E]  DIRECTED E_a (delta: bidirectional->both, forward->s->t, ...)
  edge_attr  [E, 3]  tau one-hot
  level      [N]     node level 0..3
  parent_idx [N]     containment parent index (-1 for roots)
  room_mask  [N]     True for level-3 rooms
  y          [N]     per-room target (others 0); see targets.py callers

Direction lives in edge_index (so flipping a delta changes the graph — the basis
of the direction-sensitivity test).
"""

from __future__ import annotations

from typing import Any

import torch

ROOM_TYPES = [
    "icu_room",
    "isolation_room",
    "nurse_station",
    "patient_room",
    "treatment_room",
    "operating_room",
    "prep_room",
    "recovery_room",
    "scrub_room",
    "imaging_room",
    "lab",
    "exam_room",
    "reading_room",
    "office",
    "meeting_room",
    "records",
    "reception",
    "consult_room",
    "waiting_room",
]
_EXTRA = ["corridor", "wing", "building", "unknown"]
TYPE_VOCAB = ROOM_TYPES + _EXTRA
_TYPE_IDX = {t: i for i, t in enumerate(TYPE_VOCAB)}
_TAU = ["wall-adjacent", "door-connected", "corridor-link"]
_TAU_IDX = {t: i for i, t in enumerate(_TAU)}

NUM_NODE_FEATURES = 4 + 5 + 1 + len(TYPE_VOCAB)  # level(4)+geom(5)+deg(1)+type
NUM_EDGE_FEATURES = len(_TAU)


def _type_token(node: dict[str, Any]) -> str:
    lvl = node["level"]
    if lvl == 3:
        return node.get("attrs", {}).get("type", "unknown")
    return {2: "corridor", 1: "wing", 0: "building"}[lvl]


def build_graph_tensors(graph: dict[str, Any]) -> dict[str, torch.Tensor]:
    nodes = graph["nodes"]
    ids = [n["id"] for n in nodes]
    idx = {nid: i for i, nid in enumerate(ids)}
    n = len(nodes)

    level = torch.tensor([nd["level"] for nd in nodes], dtype=torch.long)
    parent = torch.full((n,), -1, dtype=torch.long)
    for e in graph["containment_edges"]:
        parent[idx[e["target"]]] = idx[e["source"]]

    # directed E_a from delta + tau one-hot edge features
    src, dst, eattr = [], [], []
    for e in graph["adjacency_edges"]:
        s, t = idx[e["source"]], idx[e["target"]]
        d = e.get("delta", "bidirectional")
        pairs = []
        if d in ("bidirectional", "forward"):
            pairs.append((s, t))
        if d in ("bidirectional", "backward"):
            pairs.append((t, s))
        oh = [0.0, 0.0, 0.0]
        oh[_TAU_IDX.get(e["tau"], 0)] = 1.0
        for a, b in pairs:
            src.append(a)
            dst.append(b)
            eattr.append(oh)
    edge_index = (
        torch.tensor([src, dst], dtype=torch.long) if src else torch.zeros((2, 0), dtype=torch.long)
    )
    edge_attr = (
        torch.tensor(eattr, dtype=torch.float) if eattr else torch.zeros((0, NUM_EDGE_FEATURES))
    )

    deg = torch.zeros(n)
    if edge_index.numel():
        ones = torch.ones(edge_index.size(1))
        deg.scatter_add_(0, edge_index[1], ones)

    x = torch.zeros((n, NUM_NODE_FEATURES))
    for i, nd in enumerate(nodes):
        a = nd.get("attrs", {})
        x[i, nd["level"]] = 1.0  # level one-hot [0:4]
        x[i, 4] = a.get("area", 0.0) / 50.0
        x[i, 5] = a.get("aspect_ratio", 0.0)
        x[i, 6] = a.get("perimeter", 0.0) / 50.0
        c = a.get("centroid", [0.5, 0.5])
        x[i, 7], x[i, 8] = c[0], c[1]
        x[i, 9] = deg[i] / 10.0
        x[i, 10 + _TYPE_IDX.get(_type_token(nd), _TYPE_IDX["unknown"])] = 1.0

    room_mask = level == 3
    return {
        "x": x,
        "edge_index": edge_index,
        "edge_attr": edge_attr,
        "level": level,
        "parent_idx": parent,
        "room_mask": room_mask,
        "ids": ids,  # type: ignore[dict-item]
    }
