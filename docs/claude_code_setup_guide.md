# Building TopoField with Claude Code — Setup & Operating Guide

This guide assumes the finalized research plan (research_plan_final.md) and maps it onto a concrete Claude Code working setup. The organizing principle throughout: **Claude Code performs best when the repository itself encodes the project's truth** — schemas, fixtures, conventions, and verification loops — so that any session, fresh or resumed, can ground itself without you re-explaining the project.

---

## 1. Repository layout — one monorepo, hard boundaries

```
topofield/
├── CLAUDE.md                     # root context file (draft in §2)
├── docs/
│   ├── research_plan_final.md    # THE plan — Claude reads this, always current
│   ├── explanation.md            # concept explanations
│   ├── hdg_schema.md             # prose spec of the HDG format
│   └── decisions/                # ADRs: one file per irreversible choice
├── schemas/
│   └── hdg.schema.json           # machine-checkable HDG JSON Schema (§3)
├── src/topofield/
│   ├── extraction/               # Phase 0: raster/vector/IFC lanes
│   ├── graph/                    # HDG construction, validation, stats
│   ├── simulation/               # EnergyPlus, RC-network, JuPedSim wrappers
│   ├── models/                   # encoder, heads, baselines-we-train
│   ├── tasks/                    # taskT thermal, taskE egress, taskL loc
│   ├── metrics/                  # ARI/NMI, GED, SSIG, recall@X, all of §11
│   └── eval/                     # LOBO harness, statistical protocol
├── third_party/                  # cloned baselines, PINNED — see §4
│   ├── roomformer/  heat/  polyroom/  f3loc/  tesseract/ ...
│   └── PATCHES.md                # every modification to third-party code, logged
├── configs/                      # Hydra/OmegaConf configs, one per experiment
├── tests/
│   ├── fixtures/hospital_toy.json  # §4.2 worked example as executable truth
│   └── ...
├── scripts/                      # launch_train.sh, run_lobo.sh, etc.
├── data/                         # .gitignored; symlink to storage
└── .claude/
    ├── commands/                 # custom slash commands (§7)
    └── settings.json             # permissions & hooks (§8)
```

Why this shape matters for Claude Code specifically: the agent navigates by directory semantics. When extraction, metrics, and third-party code are cleanly separated, a session scoped to "fix the GED metric" never wanders into MMDetection internals. `third_party/` being explicitly outside `src/` also stops Claude from "helpfully" refactoring baseline code whose exact behavior you need preserved for fair comparison.

---

## 2. CLAUDE.md — the single highest-leverage file

Root `CLAUDE.md` draft (adapt, keep under ~150 lines; Claude reads it every session):

```markdown
# TopoField — CVPR 2026 project

## What this is
Hierarchical Directed Graph (HDG) representation of institutional floorplans
+ one shared graph-transformer encoder + three task arms:
Task T (thermal, EnergyPlus-supervised), Task E (egress, JuPedSim-supervised),
Task L (localization prior injected into frozen F3Loc). Full plan:
docs/research_plan_final.md — read the relevant section before large tasks.

## Non-negotiable invariants
- The HDG format is defined by schemas/hdg.schema.json. Every producer
  validates on write; every consumer validates on read. Never emit or accept
  a graph that fails validation. Change the schema only via docs/decisions/.
- tests/fixtures/hospital_toy.json is the canonical worked example
  (ICU/Admin wings, cross-hierarchy Nurse↔Records door). If code disagrees
  with the fixture, the code is wrong.
- third_party/ is read-only in spirit: never refactor, reformat, or "improve"
  baseline code. Necessary patches go through PATCHES.md with rationale.
- data/ is never committed, never deleted, never bulk-modified by scripts
  without an explicit dry-run flag.
- Every experiment runs from a config in configs/; no hardcoded
  hyperparameters in source. Seeds: 0,1,2. LOBO splits by BUILDING, never
  by floor.
- Metrics implementations must match docs/research_plan_final.md §11
  definitions exactly (IoU≥0.5 room match, 5px corner, 5° angle,
  recall@{0.1,0.5,1}m, @1m30°). Tests in tests/test_metrics.py are the law.

## Environments (do not mix)
- Core: `uv run` in repo root (Python 3.11, PyG, PyTorch pinned in
  pyproject.toml)
- Each baseline has its own env: see third_party/<name>/ENV.md.
  RoomFormer/PolyRoom need MMDetection + older torch — containerized;
  run via scripts/run_baseline.sh <name>, never in the core env.

## Commands
- Fast tests: `uv run pytest -x -q tests/ -m "not slow"`
- Full validation of a graph file: `uv run topofield validate <path>`
- Render HDG overlay for eyeballing: `uv run topofield render <graph> <raster>`
- Tiny end-to-end smoke (fixture through all heads): `scripts/smoke.sh`

## Style
- Python 3.11, ruff + pyright clean before commit. No notebooks in src/;
  exploratory notebooks live in scratch/ (gitignored).
- Prefer editing existing modules over creating new files.
```

Add small per-directory `CLAUDE.md` files only where local gotchas exist (e.g., `third_party/f3loc/CLAUDE.md`: "reproduce paper numbers FIRST — Gibson-f 36.6% recall@1m — before any modification; our only change is the prior injection point at <file:line>").

---

## 3. The HDG schema and the toy fixture — executable ground truth

Do these two things before any other code, because everything else composes against them:

**`schemas/hdg.schema.json`** — a JSON Schema encoding §4.3 exactly: node levels {0,1,2,3}; `E_c` level-adjacency constraint; `E_a` endpoint levels {2,3}; `tau` enum {wall-adjacent, door-connected, corridor-link}; `delta` enum {bidirectional, forward, backward}; required node attributes per level. Ship a `topofield validate` CLI. This is the contract that lets extraction, annotation UI, simulation, and models be built in parallel — including by parallel Claude Code sessions — without integration drift.

**`tests/fixtures/hospital_toy.json`** — the §4.2 worked example, hand-written: 10 nodes, 9 containment edges, 7 adjacency edges including the cross-hierarchy Nurse↔Records door. Its known properties become assertions: tree validity of E_c, the cross-hierarchy edge surviving round-trips, betweenness of Corridor A > any room, hierarchy-recovery F1 = 1.0 on itself. Every metric, every encoder forward pass, every renderer gets a fixture test. Claude Code's effectiveness scales directly with feedback-loop speed — this fixture makes the loop sub-second.

---

## 4. Environments: quarantine the baselines

The single most predictable source of wasted agent-hours in this project is dependency hell across research baselines. RoomFormer/PolyRoom (MMDetection stack, older CUDA/torch), HEAT, F3Loc, HouseDiffusion, Tesseract each have incompatible pins. Rules:

- Core project: `uv` with a fully pinned `pyproject.toml` + lockfile.
- Each baseline: its own container (Dockerfile per baseline in `third_party/<name>/`) or at minimum its own uv/conda env, documented in `ENV.md` with the exact commit hash of the upstream repo. The commit hash goes in the paper's reproducibility statement — record it on day one.
- A uniform runner: `scripts/run_baseline.sh <name> <input_dir> <output_dir>` that hides env activation. Claude Code should invoke baselines only through this — put that in CLAUDE.md.
- Reproduce each baseline's **published numbers on its home benchmark before touching anything else** (RoomFormer on Structured3D, F3Loc on Gibson-f). Make this a checklist item per baseline; it's the difference between "our comparison is trustworthy" and weeks of ambiguous debugging.

---

## 5. Data discipline

- `data/` layout mirroring the plan: `data/instbuild/{raw,extracted,graphs,labels}/building_<id>/`, `data/public/{structured3d,msd,cubicasa,...}`, `data/silver_labels/`. All gitignored; a `data/MANIFEST.md` (committed) lists what exists, where it came from, checksums for anything hand-verified.
- Gold annotations are precious: the review-UI output directory gets backed up automatically (hook, §8) and is never a write target for any pipeline script.
- Every derived artifact records provenance in-file: `{"generated_by": "extraction v0.3", "source": "...", "commit": "...", "date": ...}`. When a graph looks wrong in week 14, this field is the difference between a 5-minute and a 5-hour investigation.
- Privacy: the redaction pass (building/occupant names) is a pipeline stage with its own tests, not a manual step — reviewers and release both depend on it.

---

## 6. Experiment workflow

- Hydra (or plain OmegaConf) configs; one YAML per experiment under `configs/`, named `taskT_full_hdg_s3dsilver.yaml`-style. The ablation grid of §11.4 is literally a directory of configs differing in single flags (`hierarchy: false`, `symmetrize_delta: true`). Claude Code generates and audits these well *because* they're declarative.
- Tracking: wandb or a plain CSV+tensorboard combo; every run logs config hash, git commit, seed, and dataset manifest checksum. The §11.5 statistical protocol (3 seeds × ≥30 LOBO folds, Wilcoxon+Holm) is implemented once as `src/topofield/eval/protocol.py` and never ad-hoc'd in notebooks.
- Long training runs: Claude Code launches them detached (`scripts/launch_train.sh` → nohup/tmux/slurm), then *ends its involvement*. Checkpoint+resume must work (test it deliberately by killing a run). A separate short session later reads the logs and summarizes. Do not keep an agent session open babysitting a 6-hour job — it burns context for nothing.
- Smoke mode: every training entrypoint accepts `--smoke` (fixture-scale data, 2 steps, CPU-ok). Claude Code should run smoke before every real launch; put that rule in CLAUDE.md.

---

## 7. Claude Code operating practices for this project

**Session scoping.** One session ≈ one module or one experiment question. Good: "implement GED per §11.2 with fixture tests." Bad: "work on Phase 1." Use `/clear` between unrelated tasks; long mixed sessions degrade precisely the careful-detail work (metric definitions, schema constraints) this project lives on.

**Plan mode for anything structural.** Schema changes, encoder architecture, the F3Loc injection point: enter plan mode, have it read the relevant plan sections (`docs/research_plan_final.md §8`, the F3Loc paper notes), approve the plan, then execute. For research code, the plan review catches "it decided to symmetrize the graph for convenience"-class errors before they're buried in a diff.

**Parallel tracks via git worktrees.** The plan explicitly runs Phase 3 core, 3-L, and 3-E in parallel. Mirror that: three worktrees (`../topofield-taskL`, etc.), each with its own Claude Code session. The shared schema + fixture (§3) is what keeps them integrable. Merge through PRs you actually read.

**Subagents for bounded searches.** "Find every place the adjacency matrix gets symmetrized in third_party/f3loc" or "audit all configs for seed handling" are ideal subagent tasks — they keep exploration out of your main session's context.

**Custom slash commands** (`.claude/commands/`): encode your rituals once —
- `/validate-graphs <dir>` → run schema validation + stats over a graph directory, report violations
- `/repro-check <baseline>` → run the baseline's home-benchmark reproduction and diff against recorded published numbers
- `/ablation-status` → tabulate which §11.4 grid cells have completed runs (reads wandb/CSV)
- `/paper-claims` → grep results tables against the hypothesis thresholds (H3 ARI>0.4, H7 deltas...) and report pass/fail

**Docs as first-class context.** Keep the research plan, metric definitions, and per-baseline notes in `docs/`; tell Claude to read the specific section rather than pasting content into prompts. When the plan changes, change the file — not the folklore.

---

## 8. Permissions and hooks — guardrails that match the risks

In `.claude/settings.json`:
- **Deny** by default: `rm -rf`, any write under `data/instbuild/raw/`, any write under `data/**/annotations/` from non-UI processes, network calls in third_party runs (baseline containers get local mounts only).
- **Allow** without prompting: pytest, ruff, pyright, `topofield validate/render`, git status/diff/log, reads everywhere.
- **Hooks:** pre-tool-use hook blocking edits to `third_party/**` unless the session has touched `PATCHES.md` in the same task; post-write hook auto-running `topofield validate` on any `*.hdg.json` written; a hook that snapshots the annotations directory daily.

These aren't bureaucracy — they encode the two unrecoverable failure modes (corrupted gold annotations, silently modified baselines) so the agent physically cannot commit them.

---

## 9. Phase-by-phase: what to set up before pointing Claude Code at it

**Phase 0 (gates).** Before the session: one building's raster in `data/instbuild/raw/`, Tesseract + Raster-to-Graph cloned & env'd, schema + fixture done. Ask for: the extraction lane wired to the runner script, `topofield render` overlays for eyeballing, and a timing log — the gate numbers (≥80% recall, ≤4h human) come from artifacts, not vibes.

**Phase 1 (corpus).** The review UI is a ≤5-day build: scope it in plan mode as "thin web UI over hdg.schema.json outputs" and hold the line against feature creep — Claude Code will happily build you an annotation platform if you let it. κ computation is a metrics-module function with fixture tests, written before dual annotation starts.

**Phase 2 (simulation).** Wrap EnergyPlus/bim2sim and JuPedSim as pure functions: graph-in, labels-out, provenance-stamped. The RC-network surrogate is core code (needs tests against the E+ subset per the plan); the wrappers are glue.

**Phase 3 (models).** Encoder first against the fixture (shape tests, permutation-invariance test, direction-sensitivity test: flipping a delta must change outputs). Then HGT/GraphGPS baselines from PyG — these are also your encoder's sanity anchor: if GraphGPS matches full HDG on the fixture-scale tasks, you want to know in week 9, not week 16.

**Phase 3-L.** The one modification to F3Loc lives behind a single, documented injection point. Reproduce-first rule applies with force here; the Week-12 gate is a `/repro-check`-style command comparing HDG-prior vs flat-prior recall on the validation split.

**Phase 4–5.** The LOBO harness and stats protocol already exist (§6); evaluation is config sweeps + the `/ablation-status` and `/paper-claims` commands. Tables for the paper are generated by scripts from tracked results — never hand-transcribed.

---

## 10. The compact checklist

Day 0–2: repo skeleton · root CLAUDE.md · hdg.schema.json + validate CLI · hospital_toy.json + fixture tests · uv lock · .claude/settings.json guardrails
Week 1: baseline clones pinned w/ ENV.md + Dockerfiles · run_baseline.sh · reproduce RoomFormer + F3Loc home numbers · data/ layout + MANIFEST
Ongoing: one-session-one-question · plan mode for structural work · worktrees for the three arms · smoke before launch · detach long runs · provenance on every artifact · PATCHES.md for any third-party touch · results→tables via scripts only
