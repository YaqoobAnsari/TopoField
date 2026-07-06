#!/bin/bash
# Build PolyRoom env (reconstruction, ECCV24; Mask2Former/detectron2 + deformable
# ops). HARD / best-effort — likely needs iteration. GPU job (compiles ops on A100).
#SBATCH --account=punim2769
#SBATCH --partition=feit-gpu-a100
#SBATCH --qos=feit
#SBATCH --job-name=build-polyroom
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
mamba create -y -n polyroom python=3.8
conda activate polyroom
pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 \
    -f https://download.pytorch.org/whl/torch_stable.html
pip install -r third_party/polyroom/requirements.txt || echo "WARN: requirements had issues"
# detectron2 built for torch1.9/cu111
python -m pip install "detectron2 @ git+https://github.com/facebookresearch/detectron2.git" \
    || echo "WARN: detectron2 build failed — pin a compatible commit"
module load CUDA/11.8.0
export TORCH_CUDA_ARCH_LIST="8.0"
OPS=$(find third_party/polyroom -name make.sh -path '*ops*' | head -1 || true)
if [ -n "${OPS:-}" ]; then echo "compiling ops: $OPS"; (cd "$(dirname "$OPS")" && sh make.sh) || echo "WARN: ops build failed"; fi
python -c "import torch; print('polyroom torch', torch.__version__, 'cuda', torch.cuda.is_available())"
echo "BUILD DONE: polyroom (HARD — verify detectron2 + ops from the log)"
