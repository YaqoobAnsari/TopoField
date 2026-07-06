"""Phase 2 simulation labeling: graph -> physical labels (provenance-stamped).

Plan: docs/research_plan_final.md §7 (Phase 2), §3.5.
Wrap each simulator as a pure function (graph-in, labels-out):
  * EnergyPlus / bim2sim  (IFC lane)  -> thermal zones, temperature ranks
  * RC-network surrogate  (raster lane) -> validated against the E+ subset
  * JuPedSim / Vadere     (egress)     -> corridor load ranks, bottlenecks
These run in QUARANTINED environments (setup guide §4), invoked via
scripts/run_baseline.sh — never in the core env.

Not yet implemented — this is a scoped placeholder.
"""
