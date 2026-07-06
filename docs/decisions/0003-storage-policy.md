# 0003 — Datasets and heavy downloads live on project storage, never HOME
- Status: accepted
- Date: 2026-07-06
- Context: HOME (`/home/yansari`) has a 50 GB quota; public datasets alone dwarf it
  (Structured3D ~196 GB, ArchCAD, ZInD panos, model weights). ML frameworks
  default their caches to `~/.cache` (HuggingFace, torch) which silently fills
  HOME and breaks jobs. Project storage on `punim2769` is the correct home for
  all heavy artifacts.
- Decision: Nothing heavy is ever written to `~` or `~/.cache`. Concretely:
  - **Datasets** land under `data/` (already on project storage), indexed in
    `data/MANIFEST.md`. Very large public corpora may live in a shared project
    area and be symlinked into `data/`, with the real path recorded in MANIFEST.
  - **Model weights** go to project storage (e.g. baseline `Model_weights/` dirs
    on the project disk, or `data/`), never HOME.
  - **Framework caches** are redirected to `/data/gpfs/projects/punim2769/cache`
    via environment variables, bound to the conda env so they apply on every
    `conda activate topofield`:
    `XDG_CACHE_HOME`, `HF_HOME`, `HF_DATASETS_CACHE`, `HUGGINGFACE_HUB_CACHE`,
    `TORCH_HOME`, `PIP_CACHE_DIR`, `WANDB_DIR`, `WANDB_CACHE_DIR`.
  - For Slurm / non-interactive shells (which do not source the login profile),
    `source scripts/setup_env.sh` sets the same variables.
- Consequences: Downloads must target `data/` or `$XDG_CACHE_HOME`; scripts that
  download must not default to HOME or CWD-relative paths outside the project.
  The env-var bindings are set with `conda env config vars set ... -n topofield`
  and must be re-applied if the env is recreated (they are also in
  `scripts/setup_env.sh` and `environment.yml` guidance). Verified 2026-07-06:
  HOME at 3 GB/50 GB; caches already resolving to the project `cache/` dir.
