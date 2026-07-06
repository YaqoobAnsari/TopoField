#!/usr/bin/env bash
# Leave-One-Building-Out evaluation sweep (setup guide §6, plan §11.5).
# Splits by BUILDING, never by floor; 3 seeds; paired Wilcoxon + Holm across the
# ablation family. The protocol is implemented ONCE in src/topofield/eval/ and
# invoked here — never ad hoc in notebooks.
#
# Usage: scripts/run_lobo.sh <config.yaml>
set -euo pipefail

CONFIG="${1:?usage: run_lobo.sh <config.yaml>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# TODO(phase-4): python -m topofield.eval.lobo --config "$CONFIG" --seeds 0 1 2
echo "NOT IMPLEMENTED: LOBO sweep for $CONFIG"
echo "Implement in src/topofield/eval/ then wire here; results -> tables via scripts only."
exit 2
