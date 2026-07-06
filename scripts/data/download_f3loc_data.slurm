#!/bin/bash
# Download F3Loc Gibson Floorplan Localization Dataset + checkpoints (Task-L anchor)
# to PROJECT storage (never HOME). CPU job.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=dl-f3loc
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm third_party/f3loc/data third_party/f3loc/logs
export XDG_CACHE_HOME=/data/gpfs/projects/punim2769/cache
export PIP_CACHE_DIR=$XDG_CACHE_HOME/pip
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate f3loc
pip install -q gdown

echo "== dataset (ETH libdrive public share) =="
wget -c --tries=3 -O third_party/f3loc/data/gibson_floorplan_localization.zip \
    "https://libdrive.ethz.ch/index.php/s/dvKdj8WhmZuIaNw/download" \
  && (cd third_party/f3loc/data && unzip -q -o gibson_floorplan_localization.zip && rm -f gibson_floorplan_localization.zip) \
  || echo "WARN: dataset download/extract failed (check share URL)"

echo "== checkpoints (Google Drive folder) =="
gdown --folder "https://drive.google.com/drive/folders/1-TDlM9hjeODizeebgfPx7zWez0XPYCKm" \
    -O third_party/f3loc/logs || echo "WARN: checkpoint download failed (Drive quota?)"

echo "DOWNLOAD OK: f3loc data -> $(du -sh third_party/f3loc/data 2>/dev/null | cut -f1)"
