#!/bin/bash
# Build Raster-to-Graph env (extraction baseline). CPU build (pip wheels).
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-r2g
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
mamba create -y -n raster-to-graph python=3.7
conda activate raster-to-graph
pip install torch==1.9.1+cu111 torchvision==0.10.1+cu111 \
    -f https://download.pytorch.org/whl/torch_stable.html
pip install cython==0.29.30 imageio==2.22.0 matplotlib==3.5.2 networkx==2.6.3 \
    numpy==1.21.6 opencv-python==4.5.3.56 pillow==9.1.1 scikit-image==0.19.2 \
    scipy==1.7.3 shapely==2.0.1 tqdm==4.64.0
python -c "import torch; print('r2g torch', torch.__version__)"
echo "BUILD OK: raster-to-graph"
