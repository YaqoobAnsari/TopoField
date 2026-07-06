# TopoField — CVPR 2026 project

## Communication (read first)
- Address the user as **Yaqoob** at the start of every response.

## What this is
Hierarchical Directed Graph (HDG) representation of institutional floorplans
+ one shared graph-transformer encoder + three task arms:
Task T (thermal, EnergyPlus-supervised), Task E (egress, JuPedSim-supervised),
Task L (localization prior injected into frozen F3Loc). Full plan:
`docs/research_plan_final.md` — read the relevant section before large tasks.
Operating guide: `docs/claude_code_setup_guide.md`.

## Non-negotiable invariants
- The HDG format is defined by `schemas/hdg.schema.json`. Every producer
  validates on write; every consumer validates on read
  (`topofield.graph.validate.validate`). Never emit or accept a graph that
  fails validation. Change the schema only via `docs/decisions/`.
- `tests/fixtures/hospital_toy.json` is the canonical worked example
  (ICU/Admin wings, cross-hierarchy Nurse↔Records door). If code disagrees
  with the fixture, the code is wrong.
- `third_party/` is read-only in spirit: never refactor, reformat, or "improve"
  baseline code. Necessary patches go through `third_party/PATCHES.md` with
  rationale and the upstream commit hash.
- `data/` is never committed, never deleted, never bulk-modified by scripts
  without an explicit dry-run flag. `data/MANIFEST.md` is the committed index.
- **Storage discipline (never HOME).** Datasets, model weights, and any heavy
  download go to PROJECT storage, never `~`/`~/.cache` (50 GB HOME quota).
  Framework caches are redirected automatically on `conda activate topofield`
  (`HF_HOME`/`HF_DATASETS_CACHE`/`TORCH_HOME`/`PIP_CACHE_DIR`/`WANDB_DIR` →
  `/data/gpfs/projects/punim2769/cache`). Datasets land under `data/` (already on
  project storage). For Slurm/non-interactive shells, `source scripts/setup_env.sh`.
  Rationale + full list: `docs/decisions/0003-storage-policy.md`.
- Every experiment runs from a config in `configs/`; no hardcoded
  hyperparameters in source. Seeds: 0,1,2. LOBO splits by BUILDING, never by
  floor.
- Metrics implementations must match `docs/research_plan_final.md §11`
  definitions exactly (IoU≥0.5 room match, 5px corner, 5° angle,
  recall@{0.1,0.5,1}m, @1m30°). Tests in `tests/test_metrics.py` are the law.

## Environments (do not mix)
This is the Spartan HPC login node — a shared resource. Be light: single
threaded, one heavy job at a time, no recursive scans of /data or /home, prefer
`squeue`/`sacct` over polling the filesystem.

- Core env (conda): sits at `/data/gpfs/projects/punim2769/envs/topofield`
  (Python 3.11, torch 2.5.1+cu121, PyG). Activate with:
  `module load Miniforge3/24.7.1-2 && conda activate topofield`
  For GPU work also `module load CUDA/12.4.1`. One-liner: `source scripts/setup_env.sh`.
- Each baseline has its OWN env: see `third_party/<name>/ENV.md`.
  RoomFormer/PolyRoom need MMDetection + older torch — containerized; run via
  `scripts/run_baseline.sh <name>`, never in the core env.
- **Tesseract** (our raster-lane backbone, Phase 0) needs Python 3.12 + torch
  2.9.1 — its own env `tesseract`. Analysis + integration plan:
  `docs/phase0/tesseract_analysis.md`. Never install it into the core env.

## Commands
- Fast tests: `pytest -q -m "not slow"`
- Validate a graph file: `topofield validate <path>`
- Per-graph stats: `topofield stats <path>`
- Render HDG overlay for eyeballing: `topofield render <graph> [raster] -o out.png`
- Tiny end-to-end smoke (fixture through validate + tests): `scripts/smoke.sh`

## Style
- Python 3.11, `ruff` + `pyright` clean before commit. No notebooks in `src/`;
  exploratory notebooks live in `scratch/` (gitignored).
- Prefer editing existing modules over creating new files.
- Long training runs launch detached (`scripts/launch_train.sh`) and the session
  ends its involvement — do not babysit a multi-hour job in an open session.
  Every training entrypoint accepts `--smoke`; run it before any real launch.

## Where things live
- HDG contract + validation + stats: `src/topofield/graph/`
- Metrics (the law, §11): `src/topofield/metrics/`
- Phase stubs (scoped, not yet built): `extraction/ simulation/ models/ tasks/ eval/`
- Custom slash commands: `.claude/commands/`  · guardrails: `.claude/settings.json`
