"""RC thermal surrogate: integrates, returns per-room outputs, and carries signal."""

import pytest

from topofield.data.synthetic import generate_hdg
from topofield.metrics import thermal_zone_ari
from topofield.simulation.rc_thermal import (
    functional_zones,
    label_thermal_zones,
    simulate_thermal,
)


def test_simulates_on_fixture(toy_graph):
    sim = simulate_thermal(toy_graph, params={"days": 2})
    assert sim["integration_ok"]
    rooms = [n["id"] for n in toy_graph["nodes"] if n["level"] == 3]
    assert set(sim["rooms"]) == set(rooms)
    assert all(len(v) == 3 for v in sim["features"].values())  # (mean, amp, phase)


def test_functional_zones_match_wings():
    g = generate_hdg(seed=0, n_wings=4)
    fz = functional_zones(g)
    n_wings = sum(1 for n in g["nodes"] if n["level"] == 1)
    assert len(set(fz.values())) == n_wings
    assert all(0 <= z < n_wings for z in fz.values())


@pytest.mark.slow
def test_thermal_signal_beats_chance():
    """Smoke, not a claim: the surrogate produces a thermal-zone signal well above
    random on a synthetic building (robust across the calibration range)."""
    g = generate_hdg(seed=0, n_wings=4)
    sim = simulate_thermal(g)
    fz = functional_zones(g)
    gt = [fz[r] for r in sim["rooms"]]
    nz = len(set(gt))
    pred = list(label_thermal_zones(sim, n_zones=nz, seed=0).values())
    assert thermal_zone_ari(pred, gt) > 0.15
