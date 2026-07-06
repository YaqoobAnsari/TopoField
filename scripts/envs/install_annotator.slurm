#!/bin/bash
# Install the [annotator] extra (FastAPI/uvicorn/httpx) into the core topofield
# env and verify the annotator backend. CPU job (pure-python wheels).
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=install-annotator
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:40:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
# shellcheck disable=SC1091
source scripts/setup_env.sh
pip install -e ".[annotator]"
echo "== verifying annotator backend =="
python -m pytest tests/test_annotator_api.py tests/test_annotator_ops.py -q
echo "INSTALL+VERIFY OK: annotator"
