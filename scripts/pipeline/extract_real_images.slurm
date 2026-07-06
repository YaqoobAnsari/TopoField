#!/bin/bash
# Real-image pipeline: run Tesseract on Input_Images/ -> adapter -> real HDG corpus.
# Submit AFTER build-tesseract (use --dependency=afterok:<jobid>). CPU job.
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=extract-real
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm data/instbuild_real/graphs
export XDG_CACHE_HOME=/data/gpfs/projects/punim2769/cache
export HF_HOME=$XDG_CACHE_HOME/huggingface
export TORCH_HOME=$XDG_CACHE_HOME/torch
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"

echo "== 1) Tesseract extraction (tesseract env) =="
conda activate tesseract
cd third_party/tesseract
shopt -s nullglob
for img in Input_Images/*.png; do
  base="$(basename "$img")"
  echo "-- $base"
  python -u Main.py "$base" || echo "WARN: Tesseract failed on $base"
done
cd ../..

echo "== 2) Adapter: Tesseract results -> HDG corpus (topofield env) =="
conda activate topofield
COMMIT="$(git -C third_party/tesseract rev-parse HEAD 2>/dev/null || echo unknown)"
python -m topofield.extraction.batch \
    --results-dir third_party/tesseract/Results/Json \
    --out data/instbuild_real/graphs \
    --source-commit "$COMMIT"

echo "== 3) Validate + summarize the real HDG corpus =="
python - <<'PY'
from topofield.data import HDGDataset
ds = HDGDataset("data/instbuild_real/graphs")
print(f"real HDG corpus: {len(ds)} graphs, {ds.num_buildings()} buildings")
for g in ds.graphs[:5]:
    rooms = sum(1 for n in g["nodes"] if n["level"] == 3)
    print(f"  {g['metadata']['building_id']}: {rooms} rooms")
PY
echo "EXTRACT-REAL OK"
