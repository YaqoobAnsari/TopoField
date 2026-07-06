#!/bin/bash
# Build LASER env (Task-L point-set baseline). torch 1.7.1+cu110 -> A100 (sm_80). CPU build.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-laser
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
mamba create -y -n laser python=3.8
conda activate laser
pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 \
    -f https://download.pytorch.org/whl/torch_stable.html
pip install -r third_party/laser/requirements.txt
python -c "import torch; print('laser torch', torch.__version__)"
echo "BUILD OK: laser"
