# HDG Annotator

A focused web tool to turn an extracted HDG scaffold into a fully-specified HDG:
draw **functional zones** (E_c), set **edge types** (τ), and set **access
direction** (δ). It deliberately has **no navigation/routing** (no start/end,
no shortest paths) — it *creates graphs*. The connectivity metric
(navigational completeness — pairwise room-connection coverage, no start/end) is
kept and shown live.

## Architecture
- **Engine** (`src/topofield/annotator/operations.py`) — pure, validated HDG edits.
  Zoning rewires containment (E_c) only; physical adjacency (E_a) is never touched.
  Every op returns a schema-valid HDG or raises — the UI can't build an invalid graph.
  Fully unit-tested (`tests/test_annotator_ops.py`).
- **Backend** (`src/topofield/annotator/app.py`) — FastAPI, stateless transform
  service (`/api/extract`, `/api/op`, `/api/validate`, `/api/example`). Tested via
  `tests/test_annotator_api.py`.
- **Frontend** (`src/topofield/annotator/static/`) — vanilla + Cytoscape (CDN), no
  build step. Box-select rooms → assign zone; tap an edge → set τ / δ; export HDG.

## Pipeline
Tesseract floorplan → `tesseract_json_to_hdg` (adapter) → **annotate zones +
direction here** → validated HDG. (Tesseract extraction runs in its own env, §baselines.)

## Install + verify (Slurm)
```bash
sbatch scripts/envs/install_annotator.slurm     # pip install .[annotator] + run API tests
```

## Run the UI (interactive Slurm node + SSH tunnel)
```bash
# on a login shell:
sinteractive --account=punim2769 --partition=sapphire --time=2:00:00 --cpus-per-task=4
# on the allocated node:
source scripts/setup_env.sh
uvicorn topofield.annotator.app:app --host 0.0.0.0 --port 8000
# from your laptop: ssh -L 8000:<node>:8000 spartan ; then open http://localhost:8000
```
