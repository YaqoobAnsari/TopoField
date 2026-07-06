# HDG format — prose specification

This is the human-readable companion to `schemas/hdg.schema.json` (the
machine-checkable contract) and `src/topofield/graph/validate.py` (the relational
validator). The formal definition is `research_plan_final.md §4.3`; this document
says what each field means and which rules live in which layer.

## File shape
An HDG is a single JSON object:

| key | required | meaning |
|---|---|---|
| `version` | yes | schema version this graph targets (e.g. `"0.1"`). |
| `metadata` | no | provenance stamp (`generated_by`, `source`, `commit`, `date`, `building_id`, `notes`). Every derived artifact should carry one. |
| `nodes` | yes | list of nodes (≥1). |
| `containment_edges` | yes | Family 1 (E_c): parent→child. |
| `adjacency_edges` | yes | Family 2 (E_a): typed physical adjacency. |

## Nodes and levels
Each node has `id` (unique string), `level` (`L`), and `attrs`.

```
L : V -> {0 building, 1 wing/zone, 2 corridor, 3 room}
```

Required attributes per level (enforced by the JSON Schema):
- **Room (L3):** `type`, `area` required; `aspect_ratio`, `perimeter`, `centroid` (normalized `[x,y]`) recommended.
- **Corridor (L2):** `length`, `connected_room_count` recommended (none required).
- **Zone/Wing (L1):** `function_label` required; `aggregate_area`, `room_count` recommended.
- **Building (L0):** free-form (e.g. `name`).

## Two edge families
**Family 1 — Containment (E_c).** `{source, target}` meaning *source contains target*.
- Level-adjacent: `L(source) = L(target) - 1`.
- Forms a **forest**: every node has at most one parent; no cycles.

**Family 2 — Adjacency (E_a).** `{source, target, tau, delta?}`.
- Endpoints live at levels **{2,3}** (corridors and rooms) and MAY cross the hierarchy.
- `tau ∈ {wall-adjacent, door-connected, corridor-link}` — the physical relation type.
- `delta ∈ {bidirectional, forward, backward}` — access direction. `forward` = source→target,
  `backward` = target→source. Absent ⇒ treated as `bidirectional`.

### Traversability vs adjacency
A `wall-adjacent` edge is a real adjacency but **not** a path: you cannot walk (or
push air/heat by a door) through a wall. Circulation-based quantities
(betweenness, diameter) therefore run on the *traversable* subgraph
(`door-connected` + `corridor-link`); see `HDG.to_adjacency_graph(traversable_only=True)`.

## Which layer enforces which rule
JSON Schema (`schemas/hdg.schema.json`) can only check local structure. Everything
relational is in `validate.py`. Both must pass.

| Rule | Enforced by |
|---|---|
| field presence, types, enums (`level`, `tau`, `delta`) | schema |
| per-level required attributes | schema |
| edge endpoints reference existing nodes | validator |
| `L(parent) = L(child) - 1` | validator |
| containment is a forest (≤1 parent, no cycles) | validator |
| adjacency endpoints at levels {2,3} | validator |

## Note on the canonical fixture's betweenness
The setup guide sketches the property *"betweenness of Corridor A > any room."*
The canonical §4.2 example deliberately includes a **cross-wing Nurse↔Records door**,
which makes Nurse Station an articulation point with betweenness *equal to* Corridor A.
That is the representation's whole point — the cross-hierarchy edge is load-bearing
(heat/traffic use it). So the pinned tests assert the true, meaningful properties:
Corridor A outranks the *ordinary* rooms it serves and is a maximum-betweenness node,
and removing the cross-door collapses Nurse & Records betweenness to zero
(`tests/test_hdg.py::test_cross_door_is_load_bearing`).
