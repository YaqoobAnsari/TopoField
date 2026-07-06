"""Topology metrics (docs/research_plan_final.md §11.2).

These score the structural understanding that flat polygon outputs cannot:
containment recovery, edge typing, access direction, and adjacency edit distance.
Definitions here are the law (CLAUDE.md); tests/test_metrics.py pins them.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _undirected_key(e: dict[str, Any]) -> frozenset[str]:
    return frozenset((e["source"], e["target"]))


def _prf(pred: set, gt: set) -> tuple[float, float, float]:
    tp = len(pred & gt)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gt) if gt else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def hierarchy_recovery_f1(
    pred_containment: Iterable[dict[str, Any]],
    gt_containment: Iterable[dict[str, Any]],
) -> float:
    """F1 over directed containment (parent->child) edges (§11.2, Family-1).

    Identity property: hierarchy_recovery_f1(E_c, E_c) == 1.0.
    """
    pred = {(e["source"], e["target"]) for e in pred_containment}
    gt = {(e["source"], e["target"]) for e in gt_containment}
    return _prf(pred, gt)[2]


def edge_type_accuracy(
    pred_adjacency: Iterable[dict[str, Any]],
    gt_adjacency: Iterable[dict[str, Any]],
) -> float:
    """Accuracy of tau over adjacency edges present in both graphs (§11.2).

    Edges are matched undirected by endpoint pair. Edges missing from either side
    are not scored here (that is hierarchy/adjacency recovery's job).
    """
    pred = {_undirected_key(e): e["tau"] for e in pred_adjacency}
    gt = {_undirected_key(e): e["tau"] for e in gt_adjacency}
    shared = pred.keys() & gt.keys()
    if not shared:
        return 0.0
    correct = sum(1 for k in shared if pred[k] == gt[k])
    return correct / len(shared)


def direction_accuracy(
    pred_adjacency: Iterable[dict[str, Any]],
    gt_adjacency: Iterable[dict[str, Any]],
) -> float:
    """Accuracy of delta on the access-controlled subset (§11.2).

    Scored only over GT edges whose delta != 'bidirectional' — the rare, load-
    bearing directed class. Returns 1.0 if there are no directed GT edges.
    """
    pred = {_undirected_key(e): e.get("delta", "bidirectional") for e in pred_adjacency}
    directed_gt = {
        _undirected_key(e): e.get("delta", "bidirectional")
        for e in gt_adjacency
        if e.get("delta", "bidirectional") != "bidirectional"
    }
    if not directed_gt:
        return 1.0
    correct = sum(1 for k, v in directed_gt.items() if pred.get(k) == v)
    return correct / len(directed_gt)


def adjacency_ged(pred_graph, gt_graph, timeout: float = 10.0) -> float | None:
    """Graph Edit Distance between predicted and GT adjacency graphs (§11.2).

    Wraps networkx; GED is NP-hard, so this is meant for the small per-floor
    graphs in this project. Returns None if no result within `timeout` seconds.
    Pass networkx Graph objects (e.g. HDG.to_adjacency_graph()).
    """
    import networkx as nx

    return nx.graph_edit_distance(pred_graph, gt_graph, timeout=timeout)
