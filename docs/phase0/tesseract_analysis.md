# Phase 0 — Tesseract2 analysis & HDG integration plan

**Repo:** https://github.com/YaqoobAnsari/Tesseract2
**Pinned commit:** `24074a4a1c80d76eb09a0900cea4c5054c32e538` (2026-07-06)
**Clone:** `third_party/tesseract/` (gitignored; reproduce from the pinned commit)
**Provenance:** this is our own tool — Tesseract++ (Ansari et al., SIGSPATIAL
2025), the Lane-4 raster-lane backbone in `research_plan_final.md §2`. Live demo:
HF Space `yansari/Tesseract`.

## Verdict
**Yes — Tesseract2 contains the core code the Phase-0 raster lane needs**, and its
React/Cytoscape + FastAPI web app is a strong footing for the §6.4 review/annotation
UI. It produces a *flat, typed, navigable* graph; the HDG work is a well-scoped
**extension** on top (functional hierarchy + directed access + wall-adjacency +
schema conformance). This matches the plan exactly: Tesseract is both our
**backbone** and a **baseline** (§10.B). Turning the extension into a reusable
"floorplan → HDG" toolkit (as Yaqoob proposed) is a credible secondary contribution.

## What the pipeline does (single floor)
Entry point: `Main.py::make_graph(image_name, floor_id, progress_callback)` →
returns a `BuildingGraph` and writes JSON + plots. Stages:
1. **Text detection** — CRAFT (`Models/Text_Models/craft.py`, `refinenet.py`,
   `text_bboxer.py`) finds text boxes; OCR/interpretation
   (`Models/Interpreter/text_interpreter.py`) labels rooms/corridors/outdoors/
   transitions (stairs/elevators). → gives us **room type labels** (HDG `X.type`).
2. **Region extraction** — `utils/connectivity.py` builds wall masks, color masks,
   grows corridor/outdoor regions.
3. **Room segmentation** — `utils/floodfill.py` flood-fills rooms, proposes
   subnodes, computes seeds; `utils/Improve.py::pixelwise_areas` gives room areas.
4. **Door pipeline** — Faster R-CNN (`Models/Door_Models/door_bboxer.py`) detects
   doors; `Improve.classify_doors` types them **room-to-corridor (r2c),
   room-to-room (r2r), exit**.
5. **Graph construction** — `utils/graph.py::BuildingGraph` assembles typed nodes +
   edges; connectivity/funneling ensures every room subnode reaches a corridor door.
6. **Export** — `BuildingGraph.save_to_json()` + plot variants; timing in
   `utils/compute_time_eval.py` (image-area-vs-time, nodes before/after pruning —
   this is the **scaling evaluation** the paper reports and our Phase-0 timing gate).

Multi-floor: `MultiFloor.py` (+ multi-floor fns in `Main.py`) merges per-floor
graphs and connects **transition** nodes across floors via a text mapping file
(`mappings/*.txt`), with adjacency/one-to-one validation.

## Tesseract's graph model vs our HDG
`BuildingGraph` (`utils/graph.py`), built on networkx:
- `node_types = {room, door, corridor, outside, transition}`
- `add_node(id, type, position=[x,y], pixels=<area>, floor_id)`; `add_edge(u, v, weight)` (**undirected**)
- `save_to_json()` → `{"nodes":[{id,type,position,floor,...}], "edges":[...]}`
- Sample node: `{"id":"room_1","type":"room","position":[379,107],"floor":"Ground_Floor"}`

Mapping onto HDG (`schemas/hdg.schema.json`, §4.3):

| HDG element | Tesseract provides | Gap to close |
|---|---|---|
| L3 room node | ✅ `room` nodes; `position`→centroid, `pixels`→area | compute `aspect_ratio`, `perimeter`; normalize centroid; carry `type` from interpreter |
| L2 corridor node | ✅ `corridor` (main/connect) nodes | `length`, `connected_room_count` |
| L1 zone/wing | ❌ absent | **add** functional hierarchy (annotation + heuristics) |
| L0 building | ⚠️ implicit (floor/multi-floor) | **add** explicit building root |
| E_c containment (forest) | ❌ flat graph | **add** room⊂corridor-cluster⊂zone⊂wing⊂building |
| E_a `tau` | ⚠️ door edges typed r2c/r2r/exit; corridor links | map door→`door-connected`, corridor→`corridor-link`; **add** `wall-adjacent` (non-door shared walls) |
| E_a `delta` | ❌ undirected | **add** access direction (badge/one-way) |
| doors, transitions | modelled as **nodes** | **collapse** door-nodes into typed `door-connected` edges; transitions → inter-floor structure |

**Key transformation:** HDG treats a door as an *edge type* between the room and
corridor it joins, not a node. The adapter therefore contracts each `door` node
(and its two incident edges) into a single `room↔corridor` (or `room↔room`)
adjacency edge with `tau=door-connected`, preserving the r2c/r2r/exit typing.

## Integration plan (what we build on top)
Seam captured as a stub today: `src/topofield/extraction/tesseract_adapter.py`.
1. **HDG adapter** — `BuildingGraph` JSON → HDG dict, then
   `topofield.graph.validate.validate()`. Deterministic; unit-tested against a
   Tesseract sample and the schema. *(next Phase-0 task)*
2. **Functional hierarchy (E_c)** — heuristic seed (corridor-cluster from corridor
   connectivity; zone/wing from text + spatial grouping) + human review.
3. **Directed access (`delta`)** — annotation for access-controlled doors; target
   ≥300 directed edges corpus-wide (§6.2).
4. **Wall-adjacency (`tau=wall-adjacent`)** — derive room–room shared-wall pairs
   from segmentation masks (not just doors).
5. **Review/annotation UI** — extend the existing React + Cytoscape frontend
   (`utils/app_utils/frontend/`) with lasso-group-into-zone and edge-direction
   toggles → this *is* the §6.4 review UI (≤5-day budget). FastAPI backend
   (`app.py`) already exposes `/api/process`, `/api/cached-result`, sessions.

## Environment (quarantined — never the core env)
Per README: **Python 3.12 + CPU torch 2.9.1**, plus CRAFT/Faster-R-CNN, `lmdb`,
`python-Levenshtein`, `fuzzywuzzy`, `scikit-image`, `fastapi`. This conflicts with
the core env (py3.11 / torch 2.5.1+cu121), so it gets its own conda env
`tesseract` (recipe: `third_party/tesseract/ENV.md`). Model weights download via
`download_weights.py` from HF `yansari/Tesseract` → **project storage**
(`Model_weights/` on the project disk / `$HF_HOME`), never HOME (ADR 0003).

## Reproduce-first gate (§4)
Before any modification, reproduce Tesseract's published behaviour on its own
sample inputs (`Input_Images/`) and record numbers in `third_party/PATCHES.md`:
run `make_graph` on a sample, confirm node/edge counts + the timing/scaling curve,
and diff against the committed `Results/`. Only then start the adapter.

## Risks / notes
- Large git history (172 MB, mostly image history) — clone is heavy but one-off;
  kept out of our repo (gitignored).
- Doors/transitions-as-nodes means the adapter must be careful not to drop
  connectivity when contracting (guarantee: every room subnode still reaches a
  corridor after contraction).
- Tesseract's `outside` node has no HDG analogue at leaf level — map to building
  exterior context or drop, decided in the adapter ADR when we build it.
