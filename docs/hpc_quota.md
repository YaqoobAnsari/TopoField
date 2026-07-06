# HPC storage constraint — inode (file-count) quota

**Blocker (2026-07-06):** `/data/gpfs/projects/punim2769` is at its **file-count
quota**, not its space quota:

```
punim2769: 321 GB / 502 GB (63% space)  BUT  ~470,000 / 500,000 files (94% inodes)
```

Conda envs are inode-heavy (~50–150k small files EACH). With 6 envs
(`topofield`, `f3loc`, `laser`, `roomformer`, `raster-to-graph`, `polyroom`,
+ the sibling `thermotwin`) plus caches and data, we are near the 500k file limit.
`conda clean` / `pip purge` only recovered ~2.3k files because the inodes ARE the
envs (mostly hard-linked, in use). This **cannot be fixed by cleanup**.

## Impact
- `build-tesseract` and `build-house_diffusion` FAILED with `Disk quota exceeded`
  (inodes). `extract-real` (real-image pipeline) was auto-cancelled (dependency).
- Dataset downloads were cancelled — extracting them (CubiCasa5K ~20k files,
  Gibson many) would blow the remaining budget.
- We freed ~28k inodes by removing the two failed partial envs; ~30k headroom now.

## Fix — needs one of (in preference order)
1. **Request an inode quota increase** for `/data/gpfs/projects/punim2769`
   (e.g. 500k → 3–5 M files). Simplest, keeps everything in place.
2. **Request a scratch project allocation** `/data/scratch/projects/punim2769`
   (scratch has 1.6 B inodes). Put envs + datasets there (purged after inactivity,
   so not for irreplaceable gold data).
3. **Containerize baselines with Apptainer** — each baseline env becomes ONE `.sif`
   file instead of ~50k files. Fits the current quota; more work but self-service.
   Spartan provides Apptainer; `.sif` images can be built from the per-baseline
   recipes in `scripts/envs/`.

### Draft request to Spartan HPC support (for options 1/2)
> Project punim2769 has hit the file-count quota (500,000 inodes) on
> /data/gpfs/projects/punim2769 while only using 63% of the space quota. We run
> multiple deep-learning baseline conda environments for a CVPR project and need
> headroom. Could you either (a) increase the inode quota to ~3–5 million, or
> (b) create a scratch project allocation /data/scratch/projects/punim2769 we can
> write to? Thank you.

## Storage discipline reminder (ADR 0003)
Datasets + heavy artifacts go to project/scratch storage, never HOME. Framework
caches already redirect to `/data/gpfs/projects/punim2769/cache`.
