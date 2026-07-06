---
description: Tabulate which §11.4 ablation-grid cells have completed runs
argument-hint: "[results-dir]"
allowed-tools: Read, Glob, Bash(cat:*), Bash(ls:*)
---
Report the status of the §11.4 ablation grid.

Grid conditions: full HDG · no hierarchy · no direction · no edge types ·
no node attributes · geometry-only · geometric-hierarchy-only — crossed with the
task heads (T, E, L) and 3 seeds.

1. Read completed runs from the tracking store (wandb export or the CSV in
   `${1:-outputs}`), matching config hashes to grid cells.
2. Print a grid: rows = conditions, cols = tasks; each cell shows seeds done (n/3)
   or blank. Call out missing cells and any config that ran with a non-standard seed.
