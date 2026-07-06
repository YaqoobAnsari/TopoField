#!/bin/bash
# Real-image pipeline: Tesseract (Apptainer container) on Input_Images/ -> adapter
# -> real HDG corpus. Submit AFTER build-c-tesseract (--dependency=afterok:<jobid>).
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
ROOT="$PWD"
mkdir -p outputs/slurm data/instbuild_real/graphs
PROJ=/data/gpfs/projects/punim2769
export XDG_CACHE_HOME=$PROJ/cache HF_HOME=$PROJ/cache/huggingface TORCH_HOME=$PROJ/cache/torch
SIF="$ROOT/containers/tesseract.sif"

module load GCCcore/13.3.0
module load Apptainer/1.4.5

echo "== 1) Tesseract model weights (in container) =="
apptainer exec --bind "$PROJ" --env HF_HOME="$HF_HOME" "$SIF" \
    bash -lc "cd '$ROOT/third_party/tesseract' && python download_weights.py" || echo "WARN: weights"

echo "== 2) Tesseract extraction on Input_Images (in container) =="
shopt -s nullglob
for img in "$ROOT"/third_party/tesseract/Input_Images/*.png; do
  base="$(basename "$img")"
  echo "-- $base"
  apptainer exec --bind "$PROJ" --env HF_HOME="$HF_HOME",TORCH_HOME="$TORCH_HOME" "$SIF" \
      bash -lc "cd '$ROOT/third_party/tesseract' && python -u Main.py '$base'" \
    || echo "WARN: Tesseract failed on $base"
done

echo "== 3) Adapter: Tesseract results -> HDG corpus (topofield env) =="
module load Miniforge3/24.7.1-2
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate topofield
COMMIT="$(git -C third_party/tesseract rev-parse HEAD 2>/dev/null || echo unknown)"
python -m topofield.extraction.batch \
    --results-dir third_party/tesseract/Results/Json \
    --out data/instbuild_real/graphs --source-commit "$COMMIT"

echo "== 4) Validate + summarize =="
python - <<'PY'
from topofield.data import HDGDataset
ds = HDGDataset("data/instbuild_real/graphs")
print(f"real HDG corpus: {len(ds)} graphs, {ds.num_buildings()} buildings")
for g in ds.graphs[:8]:
    print(f"  {g['metadata']['building_id']}: {sum(1 for n in g['nodes'] if n['level']==3)} rooms")
PY
echo "EXTRACT-REAL OK"
