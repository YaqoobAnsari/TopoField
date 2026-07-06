---
description: Reproduce a baseline's home-benchmark numbers and diff against the recorded published values
argument-hint: <baseline>
allowed-tools: Bash(scripts/run_baseline.sh:*), Read, Grep
---
Reproduce baseline `$1` on its home benchmark and check it matches published numbers.

1. Read `third_party/$1/ENV.md` for the upstream commit, env, and the expected
   published metrics (e.g. F3Loc 36.6% recall@1m on Gibson-f; RoomFormer on Structured3D).
2. Run the baseline via `scripts/run_baseline.sh $1 ...` on its home benchmark.
3. Diff obtained vs published; flag any gap. Reproduce-first is a hard gate
   (setup guide §4) — a baseline is not trustworthy for comparison until this passes.
4. Record the reproduced numbers + date in `third_party/PATCHES.md`.
