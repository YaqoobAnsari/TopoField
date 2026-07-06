# 0001 — Record architecture decisions in ADRs
- Status: accepted
- Date: 2026-07-06
- Context: TopoField runs several parallel tracks (extraction, simulation, three
  task arms), potentially across parallel Claude Code sessions/worktrees. Without
  a durable record, irreversible choices (schema shape, split policy, injection
  points) get silently re-decided and drift apart.
- Decision: Every irreversible or hard-to-reverse choice is recorded as a numbered
  ADR under `docs/decisions/`. The HDG schema may change *only* via an ADR.
- Consequences: A small per-decision writing cost buys a single source of truth
  that any session can ground itself in. ADRs are append-only: superseded, never
  deleted.
