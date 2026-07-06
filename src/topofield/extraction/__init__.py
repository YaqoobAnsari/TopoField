"""Phase 0 extraction lanes: raster / vector / IFC -> HDG.

Plan: docs/research_plan_final.md §7 (Phase 0/1), Lane 4 (§2).
Backbone: Tesseract (SIGSPATIAL 2025) for the raster room+connectivity step,
then a typed-adjacency pass (Chen & Stouffs logic) and a hierarchy layer.
Every lane MUST emit graphs that pass topofield.graph.validate.validate().

Not yet implemented — this is a scoped placeholder.
"""
