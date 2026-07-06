"""Metric definitions are the law (§11). Identity + sensitivity properties."""

import pytest

from topofield.metrics import (
    bottleneck_precision_at_k,
    direction_accuracy,
    edge_type_accuracy,
    hierarchy_recovery_f1,
    rank_spearman,
    thermal_zone_ari,
    thermal_zone_nmi,
)


# --- topology (§11.2) ---------------------------------------------------
def test_hierarchy_recovery_identity(toy_graph):
    ec = toy_graph["containment_edges"]
    assert hierarchy_recovery_f1(ec, ec) == pytest.approx(1.0)


def test_hierarchy_recovery_penalises_missing_and_wrong(toy_graph):
    ec = toy_graph["containment_edges"]
    partial = ec[:-1]  # drop one edge -> recall < 1
    assert hierarchy_recovery_f1(partial, ec) < 1.0


def test_edge_type_accuracy_identity(toy_graph):
    ea = toy_graph["adjacency_edges"]
    assert edge_type_accuracy(ea, ea) == pytest.approx(1.0)


def test_edge_type_accuracy_detects_flip(toy_graph):
    ea = toy_graph["adjacency_edges"]
    pred = [dict(e) for e in ea]
    pred[0]["tau"] = "corridor-link"  # was wall-adjacent
    assert edge_type_accuracy(pred, ea) < 1.0


def test_direction_accuracy_identity(toy_graph):
    ea = toy_graph["adjacency_edges"]
    assert direction_accuracy(ea, ea) == pytest.approx(1.0)


def test_direction_accuracy_catches_reversed_access(toy_graph):
    ea = toy_graph["adjacency_edges"]
    pred = [dict(e) for e in ea]
    for e in pred:
        if {e["source"], e["target"]} == {"nurse", "records"}:
            e["delta"] = "backward"  # reversed the badge-controlled door
    # Only one directed GT edge; getting it wrong -> 0.
    assert direction_accuracy(pred, ea) == pytest.approx(0.0)


# --- fields (§11.3, §11.3c) --------------------------------------------
def test_thermal_ari_perfect_and_relabel_invariant():
    gt = [0, 0, 1, 1, 2, 2]
    perfect = [5, 5, 9, 9, 3, 3]  # same partition, different label ids
    assert thermal_zone_ari(perfect, gt) == pytest.approx(1.0)
    assert thermal_zone_nmi(perfect, gt) == pytest.approx(1.0)


def test_rank_spearman_monotonic():
    gt = [1.0, 2.0, 3.0, 4.0]
    assert rank_spearman([10, 20, 30, 40], gt) == pytest.approx(1.0)
    assert rank_spearman([40, 30, 20, 10], gt) == pytest.approx(-1.0)


def test_bottleneck_precision_at_k():
    ranking = ["corr_a", "corr_b", "nurse", "office"]
    gt = ["corr_a", "corr_b"]
    assert bottleneck_precision_at_k(ranking, gt, k=2) == pytest.approx(1.0)
    assert bottleneck_precision_at_k(ranking, gt, k=4) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        bottleneck_precision_at_k(ranking, gt, k=0)
