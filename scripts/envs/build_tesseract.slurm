#!/bin/bash
# Build the Tesseract env (raster-lane backbone) + fetch model weights to PROJECT
# storage. CPU job (Tesseract runs CPU torch per its README).
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-tesseract
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
# storage discipline (ADR 0003) — never HOME
export XDG_CACHE_HOME=/data/gpfs/projects/punim2769/cache
export HF_HOME=$XDG_CACHE_HOME/huggingface
export TORCH_HOME=$XDG_CACHE_HOME/torch
export PIP_CACHE_DIR=$XDG_CACHE_HOME/pip
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
mamba create -y -n tesseract python=3.12
conda activate tesseract
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r third_party/tesseract/requirements.txt
echo "== fetching Tesseract weights to \$HF_HOME =="
cd third_party/tesseract && python download_weights.py || echo "WARN: weight download failed (retry/inspect)"
python -c "import torch, cv2; print('tesseract env OK, torch', torch.__version__)"
echo "BUILD OK: tesseract"
