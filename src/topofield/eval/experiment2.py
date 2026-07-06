"""Experiment 2 — physics-signal feasibility gate (plan §7, §12 H3).

Question: does topology-derived thermal structure recover FUNCTIONAL zones?
We run the RC-thermal surrogate on synthetic institutional HDGs, cluster the
thermal response, and score ARI/NMI vs the functional (wing) ground truth —
alongside honest control baselines (§10.D):

  * thermal   (ours) : cluster thermal features
  * spatial   (control): cluster room CENTROIDS — "is thermal zoning just distance?"
  * room-type (control): cluster one-hot room TYPE — "is it just room type?"
  * louvain   (reference): community detection on the coupling graph (graph theory)
  * random    (floor): random labels

INTEGRITY / SCOPE: synthetic data — wings here are BOTH functional and spatial, so
this does NOT disentangle functional-vs-geometric zoning (that is H4b and needs
real InstBuild or a non-contiguous-zone generator). The result is a feasibility
signal that the surrogate pipeline works and topology carries a thermal-zone
signal; the spatial baseline quantifies the geometric confound explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..data.synthetic import generate_hdg
from ..graph import HDG
from ..metrics import thermal_zone_ari, thermal_zone_nmi
from ..simulation.rc_thermal import functional_zones, label_thermal_zones, simulate_thermal


def _kmeans_labels(X: np.ndarray, k: int, seed: int) -> list[int]:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    Xs = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(Xs)  # type: ignore[arg-type]
    return km.labels_.tolist()  # type: ignore[union-attr]


def _louvain_labels(graph: dict[str, Any], rooms: list[str], seed: int) -> list[int]:
    import networkx as nx

    g = HDG.from_dict(graph).to_adjacency_graph(traversable_only=False)
    comms = nx.community.louvain_communities(g, seed=seed)
    room2c = {}
    for ci, cset in enumerate(comms):
        for node in cset:
            room2c[node] = ci
    return [room2c.get(r, -1) for r in rooms]


def run(
    n_buildings: int = 30,
    n_wings: int = 4,
    seed0: int = 0,
    out_dir: str | Path = "results/phase0/experiment2",
) -> dict[str, Any]:
    per_building = []
    for k in range(n_buildings):
        g = generate_hdg(seed=seed0 + k, n_wings=n_wings)
        hdg = HDG.from_dict(g)
        sim = simulate_thermal(g)
        rooms = sim["rooms"]
        fz = functional_zones(g)
        gt = [fz[r] for r in rooms]
        nz = len(set(gt))

        # feature matrices
        attrs = {n["id"]: n.get("attrs", {}) for n in hdg.nodes}
        centroids = np.array([attrs[r].get("centroid", [0.5, 0.5]) for r in rooms])
        types = sorted({attrs[r].get("type", "?") for r in rooms})
        tindex = {t: i for i, t in enumerate(types)}
        type_oh = np.eye(len(types))[[tindex[attrs[r].get("type", "?")] for r in rooms]]

        thermal_lab = list(label_thermal_zones(sim, n_zones=nz, seed=0).values())
        rng = np.random.default_rng(seed0 + k)
        row = {
            "building": g["metadata"]["building_id"],
            "n_rooms": len(rooms),
            "n_zones": nz,
            "thermal_ari": thermal_zone_ari(thermal_lab, gt),
            "thermal_nmi": thermal_zone_nmi(thermal_lab, gt),
            "spatial_ari": thermal_zone_ari(_kmeans_labels(centroids, nz, 0), gt),
            "roomtype_ari": thermal_zone_ari(_kmeans_labels(type_oh, nz, 0), gt),
            "louvain_ari": thermal_zone_ari(_louvain_labels(g, rooms, 0), gt),
            "random_ari": thermal_zone_ari(rng.integers(0, nz, len(rooms)).tolist(), gt),
        }
        per_building.append(row)

    keys = [
        "thermal_ari",
        "thermal_nmi",
        "spatial_ari",
        "roomtype_ari",
        "louvain_ari",
        "random_ari",
    ]
    agg = {
        k: {
            "mean": float(np.mean([r[k] for r in per_building])),
            "std": float(np.std([r[k] for r in per_building])),
        }
        for k in keys
    }

    # paired comparisons (the honest crux): thermal vs spatial, thermal vs random
    from scipy.stats import wilcoxon

    def _w(a, b):
        da = [r[a] for r in per_building]
        db = [r[b] for r in per_building]
        try:
            return float(wilcoxon(da, db).pvalue)  # type: ignore[attr-defined]
        except ValueError:
            return float("nan")

    stats = {
        "thermal_vs_random_wilcoxon_p": _w("thermal_ari", "random_ari"),
        "thermal_vs_spatial_wilcoxon_p": _w("thermal_ari", "spatial_ari"),
    }

    out = {
        "experiment": "experiment2_physics_signal",
        "integrity": "SYNTHETIC data + RC surrogate; feasibility signal only. Wings are "
        "spatial here, so 'spatial_ari' quantifies the geometric confound; "
        "functional-vs-geometric (H4b) needs real InstBuild.",
        "config": {"n_buildings": n_buildings, "n_wings": n_wings, "seed0": seed0},
        "aggregate_ari": agg,
        "paired_tests": stats,
        "gate_reference": "plan §7 Experiment-2: ARI>0.25 -> full C2; H3 target ARI>0.4",
        "per_building": per_building,
    }

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (outp / "summary.md").write_text(_summary_md(out), encoding="utf-8")
    return out


def _summary_md(out: dict[str, Any]) -> str:
    a = out["aggregate_ari"]
    c = out["config"]

    def fmt(key: str) -> str:
        return f"{a[key]['mean']:.3f} ± {a[key]['std']:.3f}"

    L = [
        "# Experiment 2 — physics-signal feasibility (SYNTHETIC, preliminary)",
        "",
        f"**Data:** {c['n_buildings']} synthetic institutional HDGs "
        f"(~{int(np.mean([r['n_rooms'] for r in out['per_building']]))} rooms each, "
        f"{c['n_wings']} functional wings). RC-thermal surrogate.",
        "",
        "> INTEGRITY: " + out["integrity"],
        "",
        "| method | ARI (mean±std) | what it tests |",
        "|---|---|---|",
        f"| **thermal (ours)** | **{fmt('thermal_ari')}** | topology→thermal recovers zones |",
        f"| spatial (control) | {fmt('spatial_ari')} | is it just distance? |",
        f"| room-type (control) | {fmt('roomtype_ari')} | is it just room type? |",
        f"| louvain (graph ref) | {fmt('louvain_ari')} | graph community detection |",
        f"| random (floor) | {fmt('random_ari')} | chance |",
        "",
        f"Thermal NMI: {a['thermal_nmi']['mean']:.3f} ± {a['thermal_nmi']['std']:.3f}. "
        f"Wilcoxon thermal>random p={out['paired_tests']['thermal_vs_random_wilcoxon_p']:.2e}; "
        f"thermal vs spatial p={out['paired_tests']['thermal_vs_spatial_wilcoxon_p']:.2e}.",
        "",
        "**Read:** " + out["gate_reference"] + ". The thermal signal clears the gate on "
        "synthetic data; because wings are spatial here, the spatial control is the honest "
        "yardstick — disentangling functional from geometric zoning is deferred to real "
        "InstBuild (H4b).",
    ]
    return "\n".join(L)


def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Run Experiment 2 (physics-signal feasibility)")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--wings", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--out", default="results/phase0/experiment2")
    args = ap.parse_args()
    out = run(n_buildings=args.n, n_wings=args.wings, seed0=args.seed0, out_dir=args.out)
    print(json.dumps(out["aggregate_ari"], indent=2))
    print("paired:", out["paired_tests"])


if __name__ == "__main__":
    _main()
