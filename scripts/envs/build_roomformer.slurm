#!/bin/bash
# Build RoomFormer env. GPU job — compiles deformable-attention + diff_ras CUDA ops.
# Targets A100 (sm_80); torch 1.9.0+cu111 supports sm_80.
#SBATCH --account=punim2769
#SBATCH --partition=feit-gpu-a100
#SBATCH --qos=feit
#SBATCH --job-name=build-roomformer
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
mamba create -y -n roomformer python=3.8
conda activate roomformer
pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 \
    -f https://download.pytorch.org/whl/torch_stable.html
pip install -r third_party/roomformer/requirements.txt
module load CUDA/11.8.0
export TORCH_CUDA_ARCH_LIST="8.0"   # A100
cd third_party/roomformer/models/ops && sh make.sh
cd ../../diff_ras && python setup.py build develop
python -c "import torch; print('roomformer torch', torch.__version__, 'cuda', torch.cuda.is_available())"
echo "BUILD OK: roomformer (ops compiled)"
