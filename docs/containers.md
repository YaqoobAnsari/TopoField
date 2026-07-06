# Baseline containers (Apptainer) — inode-frugal envs

**Why:** the project is inode-constrained (`docs/hpc_quota.md`). A conda env is
~50k small files; an Apptainer `.sif` image is **one file**. Containerizing
baselines keeps us under the file-count quota.

**Key trick:** build with the sandbox + docker cache on **node-local `/tmp`** (its
own inodes), so only the final 1-file `.sif` lands on project storage:
```
export APPTAINER_TMPDIR=/tmp/$USER/apptainer_tmp
export APPTAINER_CACHEDIR=/tmp/$USER/apptainer_cache
```

Apptainer on Spartan needs its toolchain first, and runs on compute nodes:
```
module load GCCcore/13.3.0 && module load Apptainer/1.4.5
```

## Tesseract (built first — unblocks the real-image pipeline)
- Definition: `containers/tesseract.def` (Python env only; Tesseract code + weights
  stay on disk, bind-mounted at run time).
- Build: `sbatch scripts/envs/build_container_tesseract.slurm` -> `containers/tesseract.sif`.
- Run: `apptainer exec --bind /data/gpfs/projects/punim2769 containers/tesseract.sif \
    bash -lc "cd third_party/tesseract && python Main.py '<img>.png'"`.
- The real-image pipeline (`scripts/pipeline/extract_real_images.slurm`) uses it.

## Migrating the other baselines (follow-up)
The conda envs `f3loc`, `laser`, `roomformer`, `raster-to-graph`, `polyroom` each
cost ~50k inodes. To reclaim them, containerize from the same recipes in
`scripts/envs/build_*.slurm` (GPU images need `--nv` at run time) and then
`conda env remove` the conda version. Do this once the quota picture is settled.

`.sif` images are NOT committed (large binaries); the `.def` recipes are.
