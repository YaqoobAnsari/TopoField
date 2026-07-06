#!/bin/bash
# Download CubiCasa5K (free, ~4.5 GB) to PROJECT storage (never HOME).
# Silver corpus source (residential; §9). CPU job.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=dl-cubicasa5k
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm data/public/cubicasa5k
DEST=data/public/cubicasa5k
URL="https://zenodo.org/records/2613548/files/cubicasa5k.zip?download=1"
echo "== downloading CubiCasa5K to $DEST =="
wget -c --tries=3 -O "$DEST/cubicasa5k.zip" "$URL"
echo "== extracting =="
cd "$DEST" && unzip -q -o cubicasa5k.zip && rm -f cubicasa5k.zip
echo "DOWNLOAD OK: cubicasa5k -> $(du -sh . | cut -f1)"
