# Autonomous work log

Yaqoob authorized an autonomous session (2026-07-06): "finish the project and
ensure we get results publishable in CVPR ... innovate and improve ... Do not
fabricate false results." This log records every autonomous decision so it can be
audited on return.

## Integrity contract (self-imposed, non-negotiable)
- **No fabricated results.** Every number in `results/` comes from code that
  actually ran, on stated data, at stated scale, with the seed recorded.
- **Synthetic is labeled synthetic.** Generated graphs and surrogate physics are
  method-development / pretraining aids (plan §6.5) and are NEVER presented as the
  real InstBuild benchmark or as final evaluation.
- **Preliminary is labeled preliminary.** Signals on synthetic/silver data are
  feasibility evidence for hypotheses, not the paper's real-data claims.
- **Honest scope.** A finished CVPR paper needs InstBuild (human annotation),
  EnergyPlus/JuPedSim campaigns, baseline reproduction, and multi-GPU LOBO — these
  cannot be truthfully completed autonomously. I build the real core, produce
  honest preliminary signal, and queue the heavy campaigns.

## Environment facts (verified this session)
- Slurm: account `punim2769`; GPU partitions `gpu-a100`, `gpu-h100`, `gpu-l40s`
  (+ `-short`/`-preempt`); CPU `sapphire`/`cascade`. Login node has NO GPU.
- Project storage: 198 GB free at `/data/gpfs/projects/punim2769`.
- Core env: torch 2.5.1+cu121, PyG 2.6.1 (GCN/GAT/Transformer/Hetero conv OK).
- Policy: shared login node — light CPU only here; heavy compute via `sbatch`.

## Plan for this session (real, verifiable)
1. Synthetic institutional-scale HDG generator (schema-valid; labeled synthetic).
2. RC-network thermal surrogate (real linear physics) → silver thermal labels.
3. Experiment-2 feasibility (plan §7): ARI/NMI of thermal clustering vs functional
   zones → real number for the H3 gate (on synthetic; caveated).
4. HDG encoder + flat baselines (PyG) + fixture tests (shape / permutation-
   invariance / direction-sensitivity).
5. Preliminary H4 signal: hierarchy vs flat on silver thermal labels (Slurm if
   heavy; CPU-smoke otherwise).
6. LOBO + statistical-protocol harness (code + tests).
7. Honest results report + README updates; commit/push each milestone.

## Decisions & results (appended as they happen)
- (init) Log created; plan above.

### Milestone 1 — synthetic generator + RC thermal surrogate + Experiment 2 (real, preliminary)
- Built `topofield.data.synthetic` (institutional HDGs, ~116 rooms, schema-valid,
  deterministic, stamped synthetic), `topofield.simulation.rc_thermal` (linear RC
  surrogate; calibrated for physical realism — ~12 °C interior spread, τ≈5 h; not
  tuned to ARI), and `topofield.eval.experiment2` (H3 gate + §10.D controls).
- **Result (30 synthetic buildings, seed0=0), `results/phase0/experiment2/`:**
  - thermal (ours) ARI **0.471 ± 0.101**, NMI 0.607 — clears H3 target (>0.4) and
    the §7 gate (>0.25).
  - Controls: spatial(centroid) 0.317, room-type 0.141, random 0.003. Thermal
    beats spatial by ~0.15 and room-type by ~0.33 (Wilcoxon vs random & vs spatial
    p≈2e-9). So the signal is not merely distance or type.
  - louvain(graph) 0.992 — near-perfect, but PARTLY BY CONSTRUCTION: synthetic
    wings are near-separate graph components. Honest caveat recorded.
- **Honest scope:** synthetic + surrogate ⇒ feasibility evidence for H3, NOT a
  real-data result. Wings here are spatial, so this does not settle
  functional-vs-geometric (H4b); that needs real InstBuild or a non-contiguous-zone
  generator. Calibration was for physical realism; ARI was stable across the
  calibration range (0.36→0.48→0.47), i.e. not a tuning artifact.
- Repo green: 32 tests pass, ruff + pyright clean.

### Milestone 2 — HDG encoder + flat baseline + H4 ablation (real training, HONEST NEGATIVE)
- Built `models.data` (HDG→tensors, directed E_a per delta), `models.encoders`
  (`HDGNet` flat/hier — parameter-matched; only pooling differs), `models.train`
  (H4 ablation on the silver thermal field). Model invariants pinned by tests:
  shape, budget parity, permutation-equivariance, direction-sensitivity.
- **Result (`results/phase3/hierarchy_ablation/`, 30 train / 10 test, 3 seeds):**
  flat 0.892 ± 0.003 vs hier 0.889 ± 0.016 test Spearman ρ; Δρ≈0, Wilcoxon p=0.75.
  **HONEST NEGATIVE: hierarchy did not beat flat on this task/scale.** Reported as-is
  (not spun). Likely: local thermal field + ~120-node graphs + a flat baseline that
  already has global pooling → the §5 long-range/oversquashing regime isn't stressed.
  Does not refute plan-H4 (real-data thermal ARI); flags the need for a harder test.
- Decision: further training goes to Slurm (login-node CPU GAT run took 8 min).
  Next predefined experiment: fix shallow depth, sweep scale, test if Δ(hier−flat)
  grows with diameter. Queued, not yet run.
- Repo green: 35 tests, ruff + pyright clean.

### Interruption — Yaqoob returned; paused autonomous loop to report status.

### Milestone 3 — baselines, adapter, annotation tool, HDG ingestion, real-image pipeline
- Baselines: 9 cloned+pinned; envs BUILT via Slurm: f3loc, laser, roomformer (CUDA
  ops compiled), raster-to-graph, polyroom. HEAT/floor-sp blocked (old torch/sm_80).
- Tesseract→HDG adapter (tested on real sample); schema ADR 0004 (area optional,
  door_class). Annotation tool: engine (8 tested ops) + FastAPI (verified) + Cytoscape
  UI (no nav; zone/tau/delta). HDG ingestion: data/dataset.py (HDGDataset, LOBO),
  extraction/batch.py, models/train --data-dir. 60 tests, ruff+pyright clean.
- Real-image pipeline + dataset-download jobs scripted and submitted.

### BLOCKER — project inode (file-count) quota hit (docs/hpc_quota.md)
- /data/gpfs/projects/punim2769 at ~470k/500k FILES (94%) while only 63% space.
  build-tesseract + build-house_diffusion FAILED (Disk quota exceeded = inodes);
  extract-real auto-cancelled; downloads cancelled (extraction would blow budget).
- Cleanup (conda clean/pip purge) recovered only ~2.3k files; removing 2 failed
  partial envs freed ~28k (now ~30k headroom). Cannot be fixed by cleanup — the
  inodes ARE the conda envs. Scratch has 1.6B inodes but no writable punim2769
  allocation exists. NEEDS: inode quota increase OR scratch allocation (admin) OR
  Apptainer containers (self-service). Paused to get Yaqoob's decision.
