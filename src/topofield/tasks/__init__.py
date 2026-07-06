"""Task heads on the shared encoder (the backbone claim is literal).

Plan: docs/research_plan_final.md §8 (heads), §12 (hypotheses).
  taskT — thermal zoning (ARI/NMI) + temperature rank (Spearman)
  taskE — corridor egress-load ranking + bottleneck top-k
  taskL — observation<->node compatibility prior into frozen F3Loc (§7 Phase 3-L)
Shared/diagnostic heads: corridor-betweenness regression, room-type, hierarchy
recovery.

Not yet implemented — this is a scoped placeholder.
"""
