# data/ MANIFEST

`data/` is gitignored and lives on project storage; **this file is the committed
index of what exists, where it came from, and its integrity** (setup guide §5).
Add a row when a dataset lands. Record checksums for anything hand-verified.

> **Storage rule (ADR 0003):** datasets, weights, and heavy downloads go to
> project storage, never HOME. Datasets → here (`data/`); framework caches →
> `/data/gpfs/projects/punim2769/cache` (auto on `conda activate topofield`).
> Baseline weights (e.g. Tesseract) → the project disk, never `~`.

## Layout (create on demand)
```
data/
  instbuild/{raw,extracted,graphs,labels}/building_<id>/   # ours (gold)
  public/{structured3d,cubicasa5k,msd,zind,gibson_f,...}/   # downloaded
  silver_labels/                                            # simulation-derived
```
Rules: `instbuild/raw/` is never a write target for pipeline scripts; gold
annotation output is backed up and never overwritten; every derived artifact
carries an in-file provenance stamp.

## Inventory
| Path | Source | Regime | Role | Checksum / notes | Added |
|---|---|---|---|---|---|
| _(none yet)_ | | | | | |

## Release / permissions
Track per-building release permission here (§7 privacy pass). Buildings without
permission stay train-only holdout, disclosed in the paper.
