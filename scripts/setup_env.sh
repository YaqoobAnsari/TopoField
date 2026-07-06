#!/usr/bin/env bash
# Source this to get a fully configured TopoField shell (interactive OR Slurm):
#   source scripts/setup_env.sh
#
# It loads the cluster modules, activates the core conda env, and — per
# docs/decisions/0003-storage-policy.md — pins every framework cache to PROJECT
# storage so nothing heavy ever touches HOME. Safe to source repeatedly.

# --- project storage roots (never HOME) --------------------------------------
export TOPOFIELD_ROOT="/data/gpfs/projects/punim2769/TopoField"
export TOPOFIELD_CACHE="/data/gpfs/projects/punim2769/cache"
export TOPOFIELD_DATA="${TOPOFIELD_ROOT}/data"

export XDG_CACHE_HOME="${TOPOFIELD_CACHE}"
export HF_HOME="${TOPOFIELD_CACHE}/huggingface"
export HF_DATASETS_CACHE="${TOPOFIELD_CACHE}/huggingface/datasets"
export HUGGINGFACE_HUB_CACHE="${TOPOFIELD_CACHE}/huggingface/hub"
export TORCH_HOME="${TOPOFIELD_CACHE}/torch"
export PIP_CACHE_DIR="${TOPOFIELD_CACHE}/pip"
export WANDB_DIR="${TOPOFIELD_CACHE}/wandb"
export WANDB_CACHE_DIR="${TOPOFIELD_CACHE}/wandb/cache"
mkdir -p "$HF_DATASETS_CACHE" "$HUGGINGFACE_HUB_CACHE" "$TORCH_HOME" "$PIP_CACHE_DIR" "$WANDB_CACHE_DIR"

# --- modules + conda env ------------------------------------------------------
module load Miniforge3/24.7.1-2 2>/dev/null
# module load CUDA/12.4.1        # uncomment for GPU work
if command -v conda >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate topofield
fi

echo "TopoField env ready. caches -> ${TOPOFIELD_CACHE} ; data -> ${TOPOFIELD_DATA}"
