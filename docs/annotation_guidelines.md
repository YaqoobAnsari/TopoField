# InstBuild annotation guidelines (Phase-1 deliverable — DRAFT)

Status: **placeholder**. This document is a Phase-1 deliverable
(`research_plan_final.md §7`, §6.3). It must be written and stabilized on the
5-building dual-annotated κ subset *before* full annotation begins, so that
ambiguous guideline definitions are caught early rather than contaminating the
corpus.

Fill in, per the review-UI workflow (§6.4):

## Step 1 — Room correction (30–90 min/building)
- When to merge/split auto-extracted rooms; handling of alcoves, double-height
  spaces, thresholds.

## Step 2 — Edge typing (15–30 min/building)
- `wall-adjacent` vs `door-connected` vs `corridor-link` decision rules.
- Openings that are not doors (pass-throughs, windows) — what counts.

## Step 3 — Hierarchy + direction (60–120 min/building)
- Zone/department boundaries: functional, not merely geometric. Guidance for
  wards, compartments, mixed-use corridors.
- When an adjacency is `forward`/`backward` (access control, one-way egress) vs
  `bidirectional`.
- Target ≥300 directed-access edges corpus-wide (the rare class); flag them.

## Agreement protocol
- Cohen's κ measured on the 5-building dual-annotated subset; report per step.
- Disagreement resolution procedure and guideline-update log.

## Privacy
- Redact identifying text (building/occupant names) — this is a pipeline stage
  with tests, not a manual step (§5).
