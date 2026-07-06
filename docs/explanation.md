# TopoField — concepts, in plain terms

A short conceptual orientation. For the authoritative version, read
`research_plan_final.md`; this file explains the *why* so a newcomer (or a fresh
agent session) can build intuition fast.

## Why a new representation?
A building has **two** relational structures at once, and each alone is
insufficient:

1. **How it is organized** — an is-part-of tree: a room belongs to a corridor
   cluster, which belongs to a zone/department, a wing, the building. This is how
   buildings are *designed and operated* (wards, fire compartments, access
   regimes). A pure tree, however, cannot represent a door between two
   departments.
2. **How it is physically connected** — room-to-room and room-to-corridor
   adjacencies from shared geometry, typed (shared wall vs door vs corridor) and
   sometimes directional (badge-controlled / one-way). A pure flat graph, however,
   cannot represent that eight ICU rooms form one controlled ward.

The **HDG** carries both on one node set: a containment forest (`E_c`) plus a
typed, partly-directed adjacency layer (`E_a`). Robotics 3D-scene-graph work
converged on the same containment+peer pattern from sensor streams — we build it
from *drawings*, make the hierarchy *functional* (departments, not just floors),
and use it for *physical inference*, at *institutional scale*.

## Why topology might predict physics (the C2 bet)
Mechanistically: inter-room heat exchange is mediated by shared walls and doors
(exactly `E_a` and its types); HVAC zoning groups rooms by proximity and function
(≈ `E_a` membership); evacuation load concentrates on high-betweenness,
capacity-limited corridors (pure graph theory). None of these need a sensor at
inference time. The open question is *effect size*, which the ablation grid
(§11.4) measures — Experiment 2 (§7) is the gate that decides how big a bet C2 is.

## Why hierarchy and direction, theoretically
Flat message-passing provably suffers oversquashing and oversmoothing, both
worsening with graph diameter; a 120-room plan has a diameter far larger than a
5-room one. A hierarchy provides logarithmic-length shortcut paths (and, unlike
learned pooling, semantically meaningful ones). Directionality provably raises
expressiveness over symmetrized graphs — and access-controlled doors are
functionally asymmetric, so symmetrizing them destroys information. Theory
licenses the *design direction*; it does not predict effect sizes. Label:
theory-guided experimentation.

## The three arms, and why they are deliberately different
- **Task L (localization)** anchors the project to *external* benchmarks with
  *real* ground truth (camera poses) and recognized CVPR/ECCV baselines (F3Loc,
  LASER). Published work already shows flat semantics double F3Loc's recall; our
  hierarchical/typed prior is the natural continuation. This repairs the "private
  benchmark" and "circular simulation" objections in one move.
- **Task T (thermal)** is the novel, unclaimed bet: physics from topology alone.
- **Task E (egress)** is the task-family demonstration whose zeroth-order theory
  (corridor betweenness) is computable from the HDG directly — so the learned head
  has a built-in "is learning adding anything over graph theory?" baseline.

Three deep arms beat five shallow ones — rescue/crowd-ops are future work.

## The canonical example to keep in your head
ICU Wing ⊃ Corridor A ⊃ {ICU-1, ICU-2, Nurse Station};
Admin Wing ⊃ Corridor B ⊃ {Office, Records}; **plus a direct door
Nurse Station ↔ Records, across wings.** That one cross-hierarchy door is the
edge a tree cannot hold and that heat and foot traffic actually use. It lives in
`tests/fixtures/hospital_toy.json` and its properties are pinned by tests.
