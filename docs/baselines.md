# Baseline suite — setup status

All baselines are cloned (shallow, pinned) under `third_party/<name>/` (gitignored)
and run in **quarantined per-baseline conda envs**, built via **Slurm** (never the
login node). Reproduce-first (§4) is a gate per baseline before any comparison.

## Hardware constraint (important)
Our GPUs are **A100 (sm_80)**, H100 (sm_90), L40S (sm_89). A CUDA arch needs a
matching torch build:
- torch ≥1.7+cu110 → runs on **A100** (sm_80). Use `--partition=feit-gpu-a100 --qos=feit`.
- H100/L40S need torch ≥2.0/cu118 → only our own modern-torch code, not old baselines.
- **torch ≤1.6 (HEAT 1.5.1, Floor-SP 0.4) cannot run on any of our GPUs** → CPU-only
  or a port; flagged below.

## Status table
| baseline | role | repo (pinned commit) | py / torch / cuda | GPU ok? | build | status |
|---|---|---|---|---|---|---|
| **tesseract** | raster→graph backbone + baseline | YaqoobAnsari/Tesseract2 `24074a4` | 3.12 / 2.9 CPU | n/a (CPU) | conda | cloned ✓ (analysis done) |
| **f3loc** ★ | Task-L anchor (CVPR24) | felix-ch/f3loc `9e8027d` | 3.8 / conda cudatk11.3 | A100 ✓ | `env create -f environment.yml` | **build submitted** |
| **roomformer** ★ | reconstruction (CVPR23) | ywyue/RoomFormer `e88a7e3` | 3.8 / 1.9.0+cu111 | A100 ✓ | pip + compile deformable/diff_ras ops (GPU) | **build submitted** |
| **raster-to-graph** | extraction (EG24) | SizheHu/Raster-to-Graph `04f14b3` | 3.7 / 1.9.1+cu111 | A100 ✓ | pip | script ready |
| **laser** | Task-L point-set (CVPR22) | zillow/laser `dd0b584` | / 1.7.1+cu110 | A100 ✓ | pip | script ready |
| **house_diffusion** | flat-graph gen (CVPR23) | aminshabani/house_diffusion `083c9c5` | / 2.0 | A100/H100 ✓ | pip -e . | script ready |
| **polyroom** | reconstruction (ECCV24) | 3dv-casia/PolyRoom `5521f39` | 3.8 / 1.9+cu111 + Mask2Former/detectron2/mmcv | A100 ✓ | pip + detectron2 + ops (hard) | scripted, HARD |
| **heat** | reconstruction (CVPR22) | woodfrog/heat `3bb8fd8` | / 1.5.1 | ✗ sm_80 | needs torch port or CPU | **blocked (old torch)** |
| **floor-sp** | non-neural reference (ICCV19) | woodfrog/floor-sp `cad3943` | 3.5 / 0.4.0 | ✗ | CPU-only (mostly shortest-path) | **deferred (ancient)** |

Not yet cloned (no/unconfirmed public code): **Raster2Seq** (arXiv 2602.09016 — monitor;
reimplement decoder if unreleased), **CAGE** (pending), **FRI-Net** (check), **Semantic Rays**
(arXiv 2507.09291 — check release; reproduce flat-label prior in our pipeline regardless),
**LaLaLoc++** (cite numbers minimum). Representation baselines (GCN/GAT/GraphSAGE, RGCN/HGT,
GraphGPS) are **implemented by us in PyG**, not external installs.

## How to build / run
- Build a baseline env: `sbatch scripts/envs/build_<name>.slurm` (writes to
  `/data/gpfs/projects/punim2769/envs/<name>`). Check: `squeue -u $USER`,
  logs under `outputs/slurm/`.
- Run a baseline: `scripts/run_baseline.sh <name> <in> <out>` (once env + ENV.md exist).
- Reproduce-first before comparison; record numbers in `third_party/PATCHES.md`.

## Reproduce targets (record when hit)
- RoomFormer: Room F1 on Structured3D (its home benchmark).
- F3Loc: 36.6% recall@1m on Gibson-f; 22.4% @1m on Structured3D.
