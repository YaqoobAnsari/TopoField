"""HDG encoder invariants (plan §8): shape, budget parity, permutation-equivariance,
direction-sensitivity. These are correctness properties, not performance claims."""

import random

import torch

from topofield.data.synthetic import generate_hdg
from topofield.models.data import build_graph_tensors
from topofield.models.encoders import HDGNet, count_params


def _run(model, graph):
    t = build_graph_tensors(graph)
    with torch.no_grad():
        out = model(t)
    return {nid: float(out[i]) for i, nid in enumerate(t["ids"])}


def test_output_shape_and_budget_parity():
    g = generate_hdg(seed=0, n_wings=3)
    t = build_graph_tensors(g)
    torch.manual_seed(0)
    flat = HDGNet(pool="flat")
    torch.manual_seed(0)
    hier = HDGNet(pool="hier")
    with torch.no_grad():
        out = hier(t)
    assert out.shape[0] == len(g["nodes"])
    # parameter-free pooling => identical budgets (fair ablation)
    assert count_params(flat) == count_params(hier)


def test_permutation_equivariance():
    g = generate_hdg(seed=2, n_wings=3)
    order = list(range(len(g["nodes"])))
    random.Random(1).shuffle(order)
    g2 = {**g, "nodes": [g["nodes"][i] for i in order]}
    torch.manual_seed(0)
    model = HDGNet(pool="hier").eval()
    a, b = _run(model, g), _run(model, g2)
    for nid in a:
        assert abs(a[nid] - b[nid]) < 1e-4, f"not equivariant at {nid}"


def test_direction_sensitivity(toy_graph):
    """Flipping a directed access edge (nurse->records) must change outputs."""
    torch.manual_seed(0)
    model = HDGNet(pool="hier").eval()
    base = _run(model, toy_graph)
    flipped = {
        **toy_graph,
        "adjacency_edges": [
            {**e, "delta": "backward"} if {e["source"], e["target"]} == {"nurse", "records"} else e
            for e in toy_graph["adjacency_edges"]
        ],
    }
    other = _run(model, flipped)
    assert any(abs(base[nid] - other[nid]) > 1e-5 for nid in base), "model ignored edge direction"
