# 0004 — Room geometry (area) is recommended, not required
- Status: accepted
- Date: 2026-07-06
- Context: HDG v0.1 required room `area`. But extraction (Tesseract) produces a
  graph scaffold before geometry is finalized — the exported graph reliably has
  node `type` and pixel `position`, but NOT always `area`/`aspect_ratio`/
  `perimeter` (they depend on whether pixel-area was computed and exported). We
  need the Tesseract→HDG adapter to emit schema-valid graphs, and the annotation
  tool to load partial graphs that get enriched.
- Decision: At the room level (L3), only `type` is required. `area`,
  `aspect_ratio`, `perimeter`, `centroid` are recommended and still validated when
  present (`area` must be > 0, etc.). Downstream consumers that need `area` (e.g.
  the RC-thermal surrogate) default it explicitly (`attrs.get("area", …)`).
- Consequences: Extraction output validates without fabricating geometry (integrity:
  we never invent an area we did not measure). The canonical fixture and the
  synthetic generator still populate full geometry, so their tests are unchanged
  except `tests/test_schema.py`, which now checks that missing `type` (not `area`)
  is the schema error. When real scale/area is computed (pipeline or annotation),
  it is filled in and re-validated.
- Related (same extraction-driven refinement): `adjacency_edge` gains an optional
  `door_class` enum (`r2c`/`r2r`/`exit`/`door`) so the Tesseract→HDG adapter can
  carry the door classification onto the collapsed edge.
