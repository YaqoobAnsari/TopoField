"""Synthetic generator must emit schema-valid, deterministic, institutional-scale HDGs."""

from topofield.data.synthetic import generate_hdg
from topofield.graph import HDG, validate


def test_generated_graph_is_valid():
    g = generate_hdg(seed=0, n_wings=4)
    assert validate(g).ok


def test_generated_is_institutional_scale():
    g = generate_hdg(seed=1, n_wings=4)
    rooms = [n for n in g["nodes"] if n["level"] == 3]
    assert len(rooms) >= 80  # 100+ regime (4 wings x ~24-34 rooms)


def test_deterministic_by_seed():
    assert generate_hdg(seed=7, n_wings=3) == generate_hdg(seed=7, n_wings=3)
    assert generate_hdg(seed=7) != generate_hdg(seed=8)


def test_has_cross_wing_and_directed_edges():
    hdg = HDG.from_dict(generate_hdg(seed=0, n_wings=4))
    parent = {e["target"]: e["source"] for e in hdg.containment_edges}
    lvl = hdg.level

    def wing(n):
        cur = n
        while cur in parent and lvl[cur] > 1:
            cur = parent[cur]
        return cur

    cross = [
        e
        for e in hdg.adjacency_edges
        if lvl[e["source"]] == 3
        and lvl[e["target"]] == 3
        and wing(e["source"]) != wing(e["target"])
    ]
    assert cross, "expected at least one cross-wing door"

    # directed access edges appear across a small corpus (rare class, but present)
    directed_total = 0
    for s in range(10):
        gg = HDG.from_dict(generate_hdg(seed=s, n_wings=4))
        directed_total += sum(
            1 for e in gg.adjacency_edges if e.get("delta", "bidirectional") != "bidirectional"
        )
    assert directed_total > 0


def test_stamped_synthetic():
    g = generate_hdg(seed=0)
    assert g["metadata"]["synthetic"] is True
