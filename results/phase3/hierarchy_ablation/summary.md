# H4 — hierarchy vs flat on the silver thermal field (SYNTHETIC, preliminary)

> INTEGRITY: SYNTHETIC graphs + RC-surrogate labels; preliminary H4 signal, not a real-data result. Same backbone/budget/schedule; only pooling differs.

Config: {'n_train': 30, 'n_test': 10, 'epochs': 120, 'hidden': 64, 'layers': 3, 'lr': 0.005, 'seeds': [0, 1, 2]}

| variant | test Spearman ρ (mean±std) | test MAE (z) |
|---|---|---|
| flat (global pool) | 0.892 ± 0.003 | 0.155 |
| hier (E_c pool) | 0.889 ± 0.016 | 0.135 |

Δ(hier−flat) Spearman by seed: [-0.004, 0.014, -0.018]; Wilcoxon p=0.75.

**FINDING (honest negative): no significant difference between hierarchical and flat pooling on this task/scale (Δρ=-0.003, p=0.75). At ~120-node graphs with a fairly local thermal field, a 3-layer GAT + global pooling already saturates; the §5 oversquashing benefit of hierarchy is predicted for longer-range tasks / larger graphs / shallower models — untested here.**

Same backbone, depth, budget, and schedule — the only difference is hierarchical (E_c) vs flat global pooling. Next: scale-dependence (does the gap grow with graph diameter at fixed shallow depth?) and, ultimately, real InstBuild.