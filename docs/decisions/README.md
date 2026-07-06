# Architecture Decision Records (ADRs)

One file per **irreversible or hard-to-reverse** choice. The HDG schema, the
encoder architecture, the F3Loc injection point, dataset split policy, and
anything that would be expensive to undo mid-project belong here.

## Why
`CLAUDE.md` states: *"Change the schema only via docs/decisions/."* An ADR is the
record of *why* a decision was made, what was considered, and what it commits us
to — so a future session (human or agent) does not silently re-decide it.

## Format
Copy an existing file. Keep it short:

```
# NNNN — Title
- Status: proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD
- Context: what forces the decision
- Decision: what we chose
- Consequences: what this commits us to / what it rules out
```

Number sequentially (`0001`, `0002`, …). Never delete an ADR; supersede it.

## Index
- [0001](0001-record-architecture-decisions.md) — Record architecture decisions in ADRs
- [0002](0002-hdg-schema-v0.md) — HDG schema v0.1 and the two-layer validator
- [0003](0003-storage-policy.md) — Datasets and heavy downloads on project storage, never HOME
