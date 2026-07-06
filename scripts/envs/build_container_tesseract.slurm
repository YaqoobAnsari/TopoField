#!/bin/bash
# Build the Tesseract Apptainer image (inode-frugal: 1 .sif on project storage).
# The build sandbox + docker layer cache go to NODE-LOCAL /tmp, so the build does
# not consume the project's file-count quota. CPU job.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=build-c-tesseract
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm containers

module load GCCcore/13.3.0
module load Apptainer/1.4.5

# keep ALL build scratch on node-local disk (has its own inodes)
export APPTAINER_TMPDIR="/tmp/${USER}/apptainer_tmp"
export APPTAINER_CACHEDIR="/tmp/${USER}/apptainer_cache"
mkdir -p "$APPTAINER_TMPDIR" "$APPTAINER_CACHEDIR"

echo "== building containers/tesseract.sif =="
apptainer build --fakeroot --force containers/tesseract.sif containers/tesseract.def

echo "== verify =="
apptainer exec containers/tesseract.sif \
    python -c "import torch, cv2; print('OK torch', torch.__version__, 'cv2', cv2.__version__)"
ls -lh containers/tesseract.sif
echo "BUILD OK: tesseract.sif (single file)"
