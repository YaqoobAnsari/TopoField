#!/bin/bash
# Generic single-GPU job (training). Defaults to our FEIT A100 entitlement.
# Usage: sbatch scripts/slurm/gpu.slurm <command ...>
#   e.g. sbatch scripts/slurm/gpu.slurm python -m topofield.models.train --n 40
# For public GPUs instead: sbatch --partition=gpu-a100 --qos=publicgpu scripts/slurm/gpu.slurm ...
#SBATCH --account=punim2769
#SBATCH --partition=feit-gpu-a100
#SBATCH --qos=feit
#SBATCH --job-name=tf-gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
module load CUDA/12.4.1 2>/dev/null || true
# shellcheck disable=SC1091
source scripts/setup_env.sh
python - <<'PY'
import torch; print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
PY
echo "== running: $* =="
"$@"
