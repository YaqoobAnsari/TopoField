# TopoField

**Hierarchical Directed Graph representations of institutional buildings for physical field inference.**
Target venue: CVPR 2026 (ICLR 2026 alternate). See [`docs/research_plan_final.md`](docs/research_plan_final.md) for the full plan.

Every published floorplan-understanding system is built for residential-scale
buildings (5–25 rooms). Institutional buildings — hospitals, campuses, large
offices — have 100+ heterogeneous rooms organized into functional hierarchies
with access-directed circulation. TopoField introduces a representation, a task
family, and a benchmark for exactly that regime.

## The three claims
- **C1 — Representation.** The **HDG**: a functional-hierarchical, access-directed,
  typed graph built from 2D drawings. Containment hierarchy
  (room ⊂ corridor ⊂ zone ⊂ wing ⊂ building) + a cross-cutting typed
  physical-adjacency layer with directed access edges.
- **C2 — Task family.** One shared encoder, three arms:
  - **Task L** — indoor localization prior into F3Loc, on public benchmarks (real pose GT).
  - **Task T** — thermal field inference from topology alone (EnergyPlus-supervised).
  - **Task E** — egress / crowd-flow structure (evacuation-sim-supervised).
- **C3 — Benchmark.** **InstBuild**: the first institutional-scale floorplan
  benchmark (30–50 buildings, 100+ rooms each) with HDG annotations + simulation labels.

## The HDG in one glance
```
HDG = (V, E_c, E_a, L, tau, delta, X)
  L      : V -> {0 building, 1 wing/zone, 2 corridor, 3 room}
  E_c    : containment (forest); L(parent) = L(child) - 1
  E_a    : physical adjacency at levels {2,3}; may cross the hierarchy
  tau    : E_a -> {wall-adjacent, door-connected, corridor-link}
  delta  : E_a -> {bidirectional, forward, backward}   (access direction)
  X      : node attributes (room type/area/…, corridor length, zone function…)
```
The contract is [`schemas/hdg.schema.json`](schemas/hdg.schema.json). The canonical
worked example is [`tests/fixtures/hospital_toy.json`](tests/fixtures/hospital_toy.json).

## Repository layout
```
docs/        research plan, setup guide, HDG prose spec, ADRs (decisions/)
schemas/     hdg.schema.json — the machine-checkable contract
src/topofield/
  graph/     HDG data structure, validation (schema + invariants), stats   [implemented]
  metrics/   §11 metrics — topology + fields implemented; recon/loc stubbed [partial]
  extraction/ simulation/ models/ tasks/ eval/                              [scoped stubs]
tests/       fixtures/ + schema/structure/metric tests (the law)
configs/     one YAML per experiment (Hydra/OmegaConf)
scripts/     setup_env.sh, smoke.sh, run_baseline.sh, launch_train.sh, run_lobo.sh
third_party/ cloned baselines, pinned by commit (e.g. tesseract); PATCHES.md logs every touch
results/     curated, tracked results (tables + small figures); heavy artifacts stay in outputs/
data/        gitignored; MANIFEST.md is the committed index
.claude/     custom slash commands + permission/hook guardrails
```

## Quickstart (Spartan / UniMelb HPC)
```bash
module load Miniforge3/24.7.1-2
mamba env create -f environment.yml     # env created at project envs dir (off HOME quota)
conda activate topofield
# returning sessions / Slurm jobs: `source scripts/setup_env.sh` does modules +
# activate + pins all caches to project storage (never HOME — see ADR 0003).

pytest -q                               # fixture + schema + metric tests
topofield validate tests/fixtures/hospital_toy.json
topofield stats    tests/fixtures/hospital_toy.json
scripts/smoke.sh                        # tiny end-to-end sanity loop
```
GPU work additionally needs `module load CUDA/12.4.1`. Baseline reconstruction /
simulation stacks live in their own quarantined envs — see `third_party/<name>/ENV.md`
and run them via `scripts/run_baseline.sh`, never in the core env.

## Status
**Scaffold complete** — repo skeleton, HDG schema + `topofield validate` CLI,
canonical fixture with passing tests (`pytest` green, ruff + pyright clean), conda
env (torch 2.5.1+cu121 + PyG), storage discipline (ADR 0003), and `.claude`
guardrails.

**Phase 0 in progress** — the raster-lane backbone
[Tesseract2](https://github.com/YaqoobAnsari/Tesseract2) is cloned (pinned) and
analyzed: it supplies room/corridor/door extraction + a React/Cytoscape UI, and we
extend it into an HDG producer. See
[`docs/phase0/tesseract_analysis.md`](docs/phase0/tesseract_analysis.md). Next:
implement `src/topofield/extraction/tesseract_adapter.py` (Tesseract→HDG) behind a
schema-validated unit test, then run the §7 extraction / physics-signal gates.

## For agents
Read [`CLAUDE.md`](CLAUDE.md) first — it lists the non-negotiable invariants.
