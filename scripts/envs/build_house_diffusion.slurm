#!/bin/bash
# Build house_diffusion env (flat-graph generation baseline). Best-effort: the repo
# pins a torch nightly; we install a stable torch 2.0 (cu118, sm_80/89/90 ok) and
# the package. CPU build (pip wheels). May need iteration — inspect the log.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-housediff
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
mamba create -y -n house_diffusion python=3.9
conda activate house_diffusion
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118
pip install blobfile tqdm numpy matplotlib opencv-python
pip install -e third_party/house_diffusion --no-deps
python -c "import torch, house_diffusion; print('house_diffusion torch', torch.__version__)"
echo "BUILD OK: house_diffusion (verify functionality separately)"
