#!/bin/bash
# Generic CPU job (env builds, extraction, RC-sim, clustering, evaluation).
# Usage: sbatch scripts/slurm/cpu.slurm <command ...>
#   e.g. sbatch scripts/slurm/cpu.slurm python -m topofield.eval.experiment2 --n 30
#SBATCH --account=punim2769
#SBATCH --partition=sapphire
#SBATCH --qos=normal
#SBATCH --job-name=tf-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=outputs/slurm/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-/data/gpfs/projects/punim2769/TopoField}"
mkdir -p outputs/slurm
# shellcheck disable=SC1091
source scripts/setup_env.sh
echo "== running: $* =="
"$@"
