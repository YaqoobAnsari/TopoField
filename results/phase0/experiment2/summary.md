# Experiment 2 — physics-signal feasibility (SYNTHETIC, preliminary)

**Data:** 30 synthetic institutional HDGs (~116 rooms each, 4 functional wings). RC-thermal surrogate.

> INTEGRITY: SYNTHETIC data + RC surrogate; feasibility signal only. Wings are spatial here, so 'spatial_ari' quantifies the geometric confound; functional-vs-geometric (H4b) needs real InstBuild.

| method | ARI (mean±std) | what it tests |
|---|---|---|
| **thermal (ours)** | **0.471 ± 0.101** | topology→thermal recovers zones |
| spatial (control) | 0.317 ± 0.002 | is it just distance? |
| room-type (control) | 0.141 ± 0.065 | is it just room type? |
| louvain (graph ref) | 0.992 ± 0.011 | graph community detection |
| random (floor) | 0.003 ± 0.015 | chance |

Thermal NMI: 0.607 ± 0.073. Wilcoxon thermal>random p=1.86e-09; thermal vs spatial p=1.86e-09.

**Read:** plan §7 Experiment-2: ARI>0.25 -> full C2; H3 target ARI>0.4. The thermal signal clears the gate on synthetic data; because wings are spatial here, the spatial control is the honest yardstick — disentangling functional from geometric zoning is deferred to real InstBuild (H4b).