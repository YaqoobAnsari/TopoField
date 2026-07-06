# Phase 3 (preliminary, synthetic) — encoder results

All results here are on **synthetic HDGs + RC-surrogate labels** — method-development
signal, not real-data claims (see `docs/AUTONOMOUS_LOG.md`).

## hierarchy_ablation/ — H4: does functional hierarchy help?
Flat vs hierarchical HDG encoder predicting the surrogate thermal field, identical
backbone/budget/schedule, split by building.

**Honest negative:** flat 0.892 ± 0.003 vs hier 0.889 ± 0.016 Spearman ρ
(Δρ ≈ 0, Wilcoxon p = 0.75). Hierarchical pooling did **not** beat flat global
pooling on this task/scale.

Why this is plausible (not a bug):
- The surrogate thermal field is fairly **local** (diffusion → neighbouring rooms
  similar), so a 3-layer GAT already reaches ρ ≈ 0.89 — near a ceiling.
- The flat baseline already has **global** mean/max pooling, so it is not context-
  starved; the hierarchy's advantage is structured long-range shortcuts (§5
  oversquashing), which this local task at ~120 nodes does not stress.

This does **not** refute the plan's H4 (which is about thermal-zone ARI at
institutional scale on real data). It is a caution flag: the hierarchy benefit must
be demonstrated where theory predicts it — larger graphs, longer-range targets,
shallower models — and ultimately on real InstBuild.

**Next (predefined hypothesis, avoids cherry-picking):** hold model depth fixed and
shallow, sweep building scale (diameter), and test whether Δ(hier−flat) *grows with
scale*. Queue as a Slurm job (GPU) rather than the login node.
