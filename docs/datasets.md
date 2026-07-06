# Datasets — download status & locations

All datasets live on **PROJECT storage, never HOME** (ADR 0003). Downloads run on
Slurm (never the login node). Framework caches → `/data/gpfs/projects/punim2769/cache`.

| dataset | role | location (project storage) | how | status |
|---|---|---|---|---|
| **InstBuild-real (ours)** | real HDGs from the 35 `Input_Images` floorplans | `data/instbuild_real/graphs/*.hdg.json` | `scripts/pipeline/extract_real_images.slurm` (Tesseract → adapter) | **job queued** (afterok build-tesseract) |
| **CubiCasa5K** | silver corpus (residential); Raster2Seq comparison | `data/public/cubicasa5k/` | `scripts/data/download_cubicasa5k.slurm` (Zenodo, ~4.5 GB) | **downloading** |
| **F3Loc Gibson** | Task-L eval (recall@X); F3Loc reproduce | `third_party/f3loc/data/` + `logs/` (ckpts) | `scripts/data/download_f3loc_data.slurm` (ETH libdrive + gdrive) | **downloading** |
| Structured3D | reconstruction baselines + silver thermal | _form-gated_ → `data/public/structured3d/` | manual: register at structured3d-dataset.org; RoomFormer-preproc on HF | **pending (manual)** |
| MSD | closest-complexity contrast; silver | `data/public/msd/` | free: data.4tu.nl / github caspervanengelenburg/msd | pending |
| ZInD | Task-L eval (Semantic Rays) | `data/public/zind/` | request via Zillow GitHub | pending |
| ArchCAD-400K | institutional structure pretrain | `$HF_HOME` / `data/public/archcad/` | HF `ArchiAI-LAB/ArchCAD` (40 K live) | pending |
| FloorPlanCAD | institutional symbol pretrain | `data/public/floorplancad/` | form: floorplancad.github.io | pending |

## Notes
- **Form-gated** sets (Structured3D, FloorPlanCAD, ZInD) cannot be auto-downloaded;
  they need a one-time manual registration, then a Slurm `wget`/`gdown` job to
  project storage. Do NOT place them in HOME.
- Once a download completes, record it in `data/MANIFEST.md` (committed index) with
  a checksum for anything hand-verified.
- Silver labels (thermal/egress) are generated from these by our pipeline, not
  downloaded — see `topofield.simulation`.

## Ingestion
Any directory of `*.hdg.json` is consumed by `topofield.data.HDGDataset` (validated
load) with `lobo_splits` for Leave-One-Building-Out. Real HDGs from the pipeline
feed both the annotation tool and `topofield.models.train --data-dir ...`.
