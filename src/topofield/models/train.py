"""Hierarchy ablation (H4): flat vs hierarchical HDG encoder on the silver thermal
field, split by building (LOBO-style).

Task: predict the per-room thermal field (RC-surrogate mean temperature, z-scored
per building) from the HDG. Same backbone / budget / schedule for both variants;
only the pooling differs. Metric: per-building Spearman rho (temperature ranking,
plan §11.3) + MAE on the z-scored field.

INTEGRITY: synthetic graphs + surrogate labels — a preliminary method-development
signal for H4, not a real-data result. Numbers come from real training runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ..data.synthetic import generate_hdg
from ..simulation.rc_thermal import simulate_thermal
from .data import build_graph_tensors
from .encoders import HDGNet

torch.set_num_threads(1)  # be a good citizen on the shared login node


def _prepare(n_buildings: int, n_wings: int, seed0: int) -> list[dict[str, Any]]:
    data = []
    for k in range(n_buildings):
        g = generate_hdg(seed=seed0 + k, n_wings=n_wings)
        sim = simulate_thermal(g)
        t = build_graph_tensors(g)
        room_ids = [nid for nid, r in zip(t["ids"], t["room_mask"].tolist(), strict=False) if r]
        temp = torch.tensor([sim["mean_temp"][nid] for nid in room_ids])
        z = (temp - temp.mean()) / (temp.std() + 1e-6)
        y = torch.zeros(len(t["ids"]))
        y[t["room_mask"]] = z
        t["y"] = y
        data.append(t)
    return data


def _spearman(pred: torch.Tensor, target: torch.Tensor) -> float:
    from scipy.stats import spearmanr

    return float(spearmanr(pred.numpy(), target.numpy()).statistic)  # type: ignore[attr-defined]


def _train_eval(train, test, pool, seed, epochs, hidden, layers, lr) -> dict[str, float]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = HDGNet(pool=pool, hidden=hidden, layers=layers)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    lossf = torch.nn.MSELoss()

    model.train()
    for _ in range(epochs):
        for g in train:
            opt.zero_grad()
            pred = model(g)
            m = g["room_mask"]
            loss = lossf(pred[m], g["y"][m])
            loss.backward()
            opt.step()

    model.eval()
    rhos, maes = [], []
    with torch.no_grad():
        for g in test:
            m = g["room_mask"]
            pred = model(g)[m]
            tgt = g["y"][m]
            rhos.append(_spearman(pred, tgt))
            maes.append(float((pred - tgt).abs().mean()))
    return {"spearman": float(np.mean(rhos)), "mae": float(np.mean(maes))}


def run(
    n_buildings: int = 40,
    n_wings: int = 4,
    seed0: int = 0,
    n_test: int = 10,
    epochs: int = 120,
    hidden: int = 64,
    layers: int = 3,
    lr: float = 5e-3,
    seeds: tuple[int, ...] = (0, 1, 2),
    out_dir: str | Path = "results/phase3/hierarchy_ablation",
) -> dict[str, Any]:
    data = _prepare(n_buildings, n_wings, seed0)
    train, test = data[:-n_test], data[-n_test:]
    results: dict[str, list[dict[str, float]]] = {"flat": [], "hier": []}
    for seed in seeds:
        for pool in ("flat", "hier"):
            results[pool].append(_train_eval(train, test, pool, seed, epochs, hidden, layers, lr))

    def agg(pool, key):
        vals = [r[key] for r in results[pool]]
        return float(np.mean(vals)), float(np.std(vals))

    from scipy.stats import wilcoxon

    fh = [
        (results["hier"][i]["spearman"] - results["flat"][i]["spearman"]) for i in range(len(seeds))
    ]
    try:
        if len(seeds) >= 3:
            p = float(wilcoxon(fh).pvalue)  # type: ignore[attr-defined]
        else:
            p = float("nan")
    except ValueError:
        p = float("nan")

    out = {
        "experiment": "H4_hierarchy_ablation_thermal_rank",
        "integrity": "SYNTHETIC graphs + RC-surrogate labels; preliminary H4 signal, "
        "not a real-data result. Same backbone/budget/schedule; only pooling differs.",
        "config": {
            "n_train": len(train),
            "n_test": len(test),
            "epochs": epochs,
            "hidden": hidden,
            "layers": layers,
            "lr": lr,
            "seeds": list(seeds),
        },
        "flat": {
            "spearman": agg("flat", "spearman"),
            "mae": agg("flat", "mae"),
            "runs": results["flat"],
        },
        "hier": {
            "spearman": agg("hier", "spearman"),
            "mae": agg("hier", "mae"),
            "runs": results["hier"],
        },
        "hier_minus_flat_spearman_by_seed": fh,
        "wilcoxon_p": p,
    }
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (outp / "summary.md").write_text(_summary(out), encoding="utf-8")
    return out


def _summary(out: dict[str, Any]) -> str:
    f, h = out["flat"], out["hier"]
    delta = h["spearman"][0] - f["spearman"][0]
    p = out["wilcoxon_p"]
    significant = isinstance(p, float) and p == p and p < 0.05  # p==p filters NaN
    if significant and delta > 0:
        finding = f"FINDING: hierarchy helps (Δρ={delta:+.3f}, p={p:.3g})."
    elif significant and delta < 0:
        finding = f"FINDING: hierarchy hurts here (Δρ={delta:+.3f}, p={p:.3g})."
    else:
        finding = (
            f"FINDING (honest negative): no significant difference between hierarchical "
            f"and flat pooling on this task/scale (Δρ={delta:+.3f}, p={p}). At ~120-node "
            f"graphs with a fairly local thermal field, a 3-layer GAT + global pooling "
            f"already saturates; the §5 oversquashing benefit of hierarchy is predicted "
            f"for longer-range tasks / larger graphs / shallower models — untested here."
        )

    def sp(v):
        return f"{v[0]:.3f} ± {v[1]:.3f}"

    deltas = [round(x, 3) for x in out["hier_minus_flat_spearman_by_seed"]]
    return "\n".join(
        [
            "# H4 — hierarchy vs flat on the silver thermal field (SYNTHETIC, preliminary)",
            "",
            "> INTEGRITY: " + out["integrity"],
            "",
            f"Config: {out['config']}",
            "",
            "| variant | test Spearman ρ (mean±std) | test MAE (z) |",
            "|---|---|---|",
            f"| flat (global pool) | {sp(f['spearman'])} | {f['mae'][0]:.3f} |",
            f"| hier (E_c pool) | {sp(h['spearman'])} | {h['mae'][0]:.3f} |",
            "",
            f"Δ(hier−flat) Spearman by seed: {deltas}; Wilcoxon p={p}.",
            "",
            "**" + finding + "**",
            "",
            "Same backbone, depth, budget, and schedule — the only difference is hierarchical "
            "(E_c) vs flat global pooling. Next: scale-dependence (does the gap grow with "
            "graph diameter at fixed shallow depth?) and, ultimately, real InstBuild.",
        ]
    )


def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="H4 hierarchy ablation on silver thermal field")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--wings", type=int, default=4)
    ap.add_argument("--n-test", type=int, default=10)
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--smoke", action="store_true", help="tiny run (CPU, fast)")
    ap.add_argument("--out", default="results/phase3/hierarchy_ablation")
    args = ap.parse_args()
    if args.smoke:
        out = run(n_buildings=6, n_wings=3, n_test=2, epochs=5, seeds=(0,), out_dir=args.out)
    else:
        out = run(
            n_buildings=args.n,
            n_wings=args.wings,
            n_test=args.n_test,
            epochs=args.epochs,
            seeds=tuple(args.seeds),
            out_dir=args.out,
        )
    print(
        json.dumps(
            {
                "flat": out["flat"]["spearman"],
                "hier": out["hier"]["spearman"],
                "wilcoxon_p": out["wilcoxon_p"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _main()
