#!/usr/bin/env bash
# Tiny end-to-end sanity loop: the fixture through validate + stats + the fast
# test suite. Sub-second; run it before trusting anything else in a session.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FIXTURE="tests/fixtures/hospital_toy.json"

echo "== topofield validate =="
if command -v topofield >/dev/null 2>&1; then
  topofield validate "$FIXTURE"
  echo "== topofield stats =="
  topofield stats "$FIXTURE"
else
  echo "topofield CLI not on PATH — activate the env:"
  echo "  module load Miniforge3/24.7.1-2 && conda activate topofield"
  exit 127
fi

echo "== pytest (fast) =="
pytest -q -m "not slow"

echo "== smoke OK =="
