#!/usr/bin/env bash
# Uniform baseline runner. Claude Code invokes baselines ONLY through this, so
# env activation and quarantine live in one place (setup guide §4). Baselines
# never run in the core topofield env.
#
# Usage: scripts/run_baseline.sh <name> <input_dir> <output_dir>
set -euo pipefail

NAME="${1:?usage: run_baseline.sh <name> <input_dir> <output_dir>}"
INPUT_DIR="${2:?missing <input_dir>}"
OUTPUT_DIR="${3:?missing <output_dir>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_DIR="$ROOT/third_party/$NAME"

if [[ ! -d "$BASELINE_DIR" ]]; then
  echo "error: $BASELINE_DIR not found. Clone the baseline (pinned commit) and add ENV.md." >&2
  exit 1
fi
if [[ ! -f "$BASELINE_DIR/ENV.md" ]]; then
  echo "error: $BASELINE_DIR/ENV.md missing — document the upstream commit + env first (§4)." >&2
  exit 1
fi

# TODO(phase-1): dispatch to the baseline's container/env. Pattern:
#   - read env spec from $BASELINE_DIR/ENV.md
#   - module load Apptainer && apptainer exec <img> ...   (or conda activate <baseline-env>)
#   - mount $INPUT_DIR ro, $OUTPUT_DIR rw; no network (baselines get local mounts only)
echo "NOT IMPLEMENTED: run '$NAME' on '$INPUT_DIR' -> '$OUTPUT_DIR'"
echo "Wire this up in Phase 1 once the first baseline is cloned + reproduced."
exit 2
