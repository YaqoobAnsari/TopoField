#!/bin/bash
# Build the f3loc env (Task-L anchor). CPU job — conda just downloads packages.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-f3loc
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
cd third_party/f3loc
mamba env create -f environment.yml || mamba env update -f environment.yml
conda activate f3loc
python -c "import torch, lightning; print('f3loc torch', torch.__version__, 'cuda', torch.version.cuda)"
echo "BUILD OK: f3loc"
