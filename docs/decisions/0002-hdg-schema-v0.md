# 0002 — HDG schema v0.1 and the two-layer validator
- Status: accepted
- Date: 2026-07-06
- Context: The HDG is the contract that lets extraction, annotation, simulation,
  and models be built in parallel without integration drift (setup guide §3). It
  must be machine-checkable, but some invariants (containment forest,
  level-adjacency, endpoint levels, dangling references) are relational and cannot
  be expressed in JSON Schema.
- Decision: Ship `schemas/hdg.schema.json` (Draft 2020-12) as v0.1 encoding
  structure, level/tau/delta enums, and per-level required attributes. Enforce the
  relational invariants in `src/topofield/graph/validate.py`. `topofield validate`
  runs BOTH layers; producers validate on write, consumers on read. Level map is
  `{0 building, 1 wing/zone, 2 corridor, 3 room}`; `tau ∈ {wall-adjacent,
  door-connected, corridor-link}`; `delta ∈ {bidirectional, forward, backward}`;
  E_a endpoints restricted to levels {2,3}.
- Consequences: Any format change is an ADR + schema bump + fixture/test update,
  in that order. Room `type`/`area` and zone `function_label` are required, so
  extraction lanes must populate them (or emit explicit placeholders) to pass
  validation. Chosen enum spellings (hyphenated tau) are now load-bearing across
  the codebase and the fixture.
