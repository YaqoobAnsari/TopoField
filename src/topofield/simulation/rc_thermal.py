"""RC-network thermal surrogate (plan §7 Experiment 2, §3.5).

A genuine linear lumped-capacitance thermal model over an HDG. It is the raster-
lane surrogate the plan specifies: nodes = rooms (+ corridors as thermal hubs),
inter-node conductance proportional to shared coupling modulated by edge type,
capacitance proportional to area, diurnal exterior forcing on envelope rooms.

Governing equation (per thermal node i):
    C_i dT_i/dt = sum_j G_ij (T_j - T_i) + Gext_i (T_out(t) - T_i) + q_i(t)
=>  dT/dt = C^{-1} ( -(L + diag(Gext)) T + Gext * T_out(t) + q(t) )
with L the type-weighted graph Laplacian of the traversable/coupling edges.

This is a SURROGATE. Absolute parameters are nominal (documented); the physics —
coupling topology, thermal mass, envelope exposure — is real. On the real
InstBuild corpus this is replaced/validated by EnergyPlus (plan §7 Phase 2). Every
output is provenance-stamped. Numbers derived from it are labeled surrogate.

INTEGRITY: results are real outputs of this model on the given graph; they are not
claimed to be EnergyPlus-accurate and are not a real-benchmark result.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..graph import HDG

# Nominal parameters (documented; calibrated for physical realism: a few-K
# interior spread and hour-scale time constants tau = C/G ~ 5 h). Relative
# structure — coupling topology, mass, envelope exposure — is what carries signal.
DEFAULTS = {
    "C_per_area": 12.0,  # Wh/K per m^2 (thermal mass); 25 m^2 room -> 300 Wh/K
    "C_corridor": 800.0,  # Wh/K lumped corridor mass
    "G_door": 60.0,  # W/K coupling across a door / corridor link (air exchange)
    "G_wall": 25.0,  # W/K coupling across a shared wall (conduction)
    "G_ext": 50.0,  # W/K envelope coupling for exterior rooms
    "T_mean": 15.0,  # deg C outdoor daily mean
    "T_amp": 8.0,  # deg C outdoor daily amplitude
    "boundary_margin": 0.07,  # normalized distance to envelope => "exterior"
    "days": 5,
    "dt_h": 0.5,
}

_G_BY_TAU = {"door-connected": "G_door", "corridor-link": "G_door", "wall-adjacent": "G_wall"}

# Nominal internal gains (W) by room type — modest free-running equipment/occupancy
# loads (a secondary perturbation; envelope + coupling topology dominate).
_GAIN = {
    "icu_room": 150,
    "isolation_room": 120,
    "operating_room": 300,
    "imaging_room": 220,
    "lab": 200,
    "patient_room": 90,
    "office": 70,
    "meeting_room": 110,
    "waiting_room": 130,
}
_GAIN_DEFAULT = 60


def _is_exterior(centroid: list[float] | None, margin: float) -> bool:
    if not centroid:
        return False
    x, y = centroid
    return x < margin or x > 1 - margin or y < margin or y > 1 - margin


def simulate_thermal(graph: dict[str, Any], params: dict | None = None) -> dict[str, Any]:
    """Integrate the RC network; return per-room temperature features + provenance.

    Thermal nodes = rooms (L3) and corridors (L2). Returns, for each ROOM:
    mean temperature and a 3-D feature (mean, daily amplitude, phase-of-peak).
    """
    from scipy.integrate import solve_ivp

    p = {**DEFAULTS, **(params or {})}
    hdg = HDG.from_dict(graph)
    lvl = hdg.level

    # thermal node set: rooms + corridors
    therm = [n for n in hdg.nodes if n["level"] in (2, 3)]
    ids = [n["id"] for n in therm]
    idx = {nid: i for i, nid in enumerate(ids)}
    n = len(ids)

    # corridor centroids = mean of contained room centroids (for completeness)
    room_children: dict[str, list[str]] = {}
    for e in hdg.containment_edges:
        room_children.setdefault(e["source"], []).append(e["target"])

    C = np.zeros(n)
    Gext = np.zeros(n)
    gain = np.zeros(n)
    for node in therm:
        i = idx[node["id"]]
        a = node.get("attrs", {})
        if node["level"] == 3:
            C[i] = max(1.0, p["C_per_area"] * a.get("area", 20.0))
            if _is_exterior(a.get("centroid"), p["boundary_margin"]):
                Gext[i] = p["G_ext"]
            gain[i] = _GAIN.get(a.get("type", ""), _GAIN_DEFAULT)
        else:  # corridor
            C[i] = p["C_corridor"]
            gain[i] = 100.0

    # type-weighted conductance (symmetric)
    G = np.zeros((n, n))
    for e in hdg.adjacency_edges:
        s, t = e["source"], e["target"]
        if s in idx and t in idx:
            g = p[_G_BY_TAU.get(e["tau"], "G_wall")]
            G[idx[s], idx[t]] += g
            G[idx[t], idx[s]] += g

    L = np.diag(G.sum(axis=1)) - G
    M = L + np.diag(Gext)
    Cinv = 1.0 / C

    def T_out(t_h: float) -> float:
        return p["T_mean"] - p["T_amp"] * np.cos(2 * np.pi * t_h / 24.0)

    def occ(t_h: float) -> float:  # daytime occupancy fraction
        h = t_h % 24.0
        return 0.15 + 0.85 * max(0.0, np.sin(np.pi * (h - 7) / 12.0)) if 7 <= h <= 19 else 0.15

    def rhs(t_h, T):
        b = Gext * T_out(t_h) + gain * occ(t_h)  # both terms in W (Gext[W/K]*K, gain[W])
        return Cinv * (-M @ T + b)

    t_end = p["days"] * 24.0
    t_eval = np.arange(0, t_end + 1e-9, p["dt_h"])
    T0 = np.full(n, p["T_mean"])
    sol = solve_ivp(rhs, (0, t_end), T0, t_eval=t_eval, method="LSODA", rtol=1e-6, atol=1e-6)
    Temp = sol.y  # (n, timesteps)

    # analyze the last full day
    last_day = t_eval >= (t_end - 24.0)
    Td = Temp[:, last_day]
    td = t_eval[last_day]
    mean_t = Td.mean(axis=1)
    amp_t = (Td.max(axis=1) - Td.min(axis=1)) / 2.0
    phase_t = td[np.argmax(Td, axis=1)] % 24.0

    rooms = [nid for nid in ids if lvl[nid] == 3]
    features = {
        nid: [float(mean_t[idx[nid]]), float(amp_t[idx[nid]]), float(phase_t[idx[nid]])]
        for nid in rooms
    }
    mean_temp = {nid: float(mean_t[idx[nid]]) for nid in rooms}

    return {
        "provenance": {
            "generated_by": "topofield.simulation.rc_thermal v0.1",
            "model": "linear lumped-capacitance RC network (surrogate, nominal params)",
            "source_building": graph.get("metadata", {}).get("building_id"),
            "params": {k: p[k] for k in ("G_door", "G_wall", "G_ext", "T_mean", "T_amp", "days")},
            "note": "SURROGATE physics; not EnergyPlus-accurate; not a benchmark result.",
        },
        "rooms": rooms,
        "mean_temp": mean_temp,
        "features": features,
        "integration_ok": bool(sol.success),
    }


def label_thermal_zones(sim: dict[str, Any], n_zones: int, seed: int = 0) -> dict[str, int]:
    """Cluster room thermal features into n_zones (standardized KMeans)."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    rooms = sim["rooms"]
    X = np.array([sim["features"][r] for r in rooms])
    Xs = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=n_zones, random_state=seed, n_init=10).fit(Xs)  # type: ignore[arg-type]
    return {r: int(c) for r, c in zip(rooms, km.labels_, strict=False)}  # type: ignore[arg-type]


def functional_zones(graph: dict[str, Any]) -> dict[str, int]:
    """Ground-truth functional zone per room = its level-1 (wing) ancestor via E_c."""
    hdg = HDG.from_dict(graph)
    parent = {e["target"]: e["source"] for e in hdg.containment_edges}
    lvl = hdg.level
    wings = sorted({nid for nid in hdg.node_ids if lvl[nid] == 1})
    wing_idx = {w: i for i, w in enumerate(wings)}
    out: dict[str, int] = {}
    for nid in hdg.node_ids:
        if lvl[nid] != 3:
            continue
        cur = nid
        while cur in parent and lvl[cur] > 1:
            cur = parent[cur]
        out[nid] = wing_idx.get(cur, -1)
    return out
