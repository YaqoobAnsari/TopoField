#!/usr/bin/env bash
# Launch a training run DETACHED, then end session involvement (setup guide §6).
# Prefers Slurm (sbatch) on Spartan; falls back to nohup. Always smoke-tests the
# config on CPU first unless SKIP_SMOKE=1.
#
# Usage: scripts/launch_train.sh <config.yaml> [extra hydra overrides...]
set -euo pipefail

CONFIG="${1:?usage: launch_train.sh <config.yaml> [overrides...]}"
shift || true
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="outputs/${STAMP}"
mkdir -p "$RUN_DIR"

# TODO(phase-3): replace with the real training entrypoint, e.g.
#   TRAIN_CMD=(python -m topofield.tasks.train --config "$CONFIG" "$@")
TRAIN_CMD=(python -m topofield.tasks.train --config "$CONFIG" "$@")

if [[ "${SKIP_SMOKE:-0}" != "1" ]]; then
  echo "== smoke (--smoke, CPU) before real launch =="
  "${TRAIN_CMD[@]}" --smoke || { echo "smoke failed — not launching" >&2; exit 1; }
fi

if command -v sbatch >/dev/null 2>&1; then
  echo "== submitting via Slurm =="
  echo "NOT IMPLEMENTED: write $ROOT/scripts/train.slurm and: sbatch scripts/train.slurm $CONFIG $*"
  echo "Then monitor with squeue/sacct — do NOT keep an agent session open babysitting it."
  exit 2
else
  echo "== no sbatch; launching detached with nohup =="
  echo "NOT IMPLEMENTED: nohup ${TRAIN_CMD[*]} > $RUN_DIR/train.log 2>&1 &"
  exit 2
fi
