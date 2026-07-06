# Baseline env builds (Slurm)

Per-baseline conda envs are built on compute nodes, **never the login node**
(CLAUDE.md compute policy). Each `build_<name>.slurm` creates
`/data/gpfs/projects/punim2769/envs/<name>` and verifies the install.

```bash
sbatch scripts/envs/build_f3loc.slurm
squeue -u $USER                 # watch
tail -f outputs/slurm/build-f3loc-<jobid>.out
```

Status + hardware notes: `docs/baselines.md`. Pinned commits: same table.
CPU builds → `sapphire`; GPU builds that compile CUDA ops (RoomFormer) → `feit-gpu-a100`.
Old-torch baselines (≤1.6: HEAT, Floor-SP) cannot run on our sm_80+ GPUs — see baselines.md.

If a compute node lacks outbound network for package downloads, pre-stage wheels
into `$PIP_CACHE_DIR` / conda pkgs on a data-mover, or use the module proxy.
