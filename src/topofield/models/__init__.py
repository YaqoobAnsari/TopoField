"""Phase 3 models: the shared Hierarchical Heterogeneous Graph Transformer.

Plan: docs/research_plan_final.md §8.
One encoder (2-8M params): edge-typed + direction-aware message passing on E_a,
bottom-up pooling along E_c, cross-level attention, top-down broadcast. Plus the
representation baselines we train ourselves (GCN/GAT/SAGE, RGCN/HGT, GraphGPS,
Hydra-style geometric hierarchy) — §10.B.

First test target is the fixture: shape, permutation-invariance, and
direction-sensitivity (flipping a delta must change outputs).

Not yet implemented — this is a scoped placeholder.
"""
