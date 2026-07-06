"""Two-layer HDG validation: JSON Schema + relational invariants.

Every producer validates on write; every consumer validates on read
(CLAUDE.md, non-negotiable invariant #1). Layer 1 is the JSON Schema in
schemas/hdg.schema.json (structure, enums, per-level required attributes).
Layer 2 enforces the relational invariants JSON Schema cannot express:

  * every edge endpoint references an existing node
  * containment is level-adjacent: L(parent) = L(child) - 1
  * containment forms a forest: each node has <= 1 parent, no cycles
  * adjacency endpoints live at levels {2, 3}
  * delta, if present, is a legal value (schema also checks this)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .hdg import DELTA, HDG

# schemas/hdg.schema.json relative to the repo root (…/src/topofield/graph/ -> up 3).
_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "hdg.schema.json"


@lru_cache(maxsize=1)
def load_schema(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _SCHEMA_PATH
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class ValidationResult:
    ok: bool
    schema_errors: list[str] = field(default_factory=list)
    semantic_errors: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        return self.schema_errors + self.semantic_errors

    def __bool__(self) -> bool:  # `if validate(...):`
        return self.ok


def validate_schema(graph: dict[str, Any]) -> list[str]:
    """Layer 1. Returns a list of human-readable error strings (empty == valid)."""
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - env guard
        raise RuntimeError(
            "jsonschema is required for HDG validation. Install the project env "
            "(environment.yml) or `pip install jsonschema`."
        ) from exc

    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(graph), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"[schema] {loc}: {err.message}")
    return errors


def validate_semantics(graph: dict[str, Any]) -> list[str]:
    """Layer 2. Relational invariants. Assumes basic structure (best-effort if not)."""
    errors: list[str] = []
    hdg = HDG.from_dict(graph)

    ids = hdg.node_ids
    if len(ids) != len(hdg.nodes):
        errors.append("[semantic] duplicate node ids present")
    level = hdg.level

    # Containment: endpoints exist, level-adjacency, forest property.
    parent_of: dict[str, str] = {}
    for e in hdg.containment_edges:
        s, t = e.get("source"), e.get("target")
        if s not in ids or t not in ids:
            errors.append(f"[semantic] containment edge references unknown node: {s} -> {t}")
            continue
        if level[s] != level[t] - 1:
            errors.append(
                f"[semantic] containment {s}(L{level[s]}) -> {t}(L{level[t]}) "
                f"violates level-adjacency L(parent)=L(child)-1"
            )
        if t in parent_of:
            errors.append(
                f"[semantic] node '{t}' has multiple parents "
                f"('{parent_of[t]}' and '{s}') — containment must be a forest"
            )
        else:
            parent_of[t] = s

    # Cycle check on the containment relation.
    if _has_cycle(parent_of):
        errors.append("[semantic] containment edges contain a cycle — not a forest")

    # Adjacency: endpoints exist, live at levels {2,3}, legal delta.
    for e in hdg.adjacency_edges:
        s, t = e.get("source"), e.get("target")
        if s not in ids or t not in ids:
            errors.append(f"[semantic] adjacency edge references unknown node: {s} -> {t}")
            continue
        for endpoint in (s, t):
            if level[endpoint] not in (2, 3):
                errors.append(
                    f"[semantic] adjacency endpoint '{endpoint}' is at L{level[endpoint]}; "
                    f"E_a endpoints must be at levels {{2,3}}"
                )
        d = e.get("delta", "bidirectional")
        if d not in DELTA:
            errors.append(f"[semantic] adjacency edge {s}->{t} has illegal delta '{d}'")

    return errors


def _has_cycle(parent_of: dict[str, str]) -> bool:
    """Detect a cycle in a child->parent map (a forest has none)."""
    for start in parent_of:
        seen = set()
        cur: str | None = start
        while cur in parent_of:
            if cur in seen:
                return True
            seen.add(cur)
            cur = parent_of[cur]
    return False


def validate(graph: dict[str, Any]) -> ValidationResult:
    """Run both layers. Semantic checks run even if schema fails (best-effort),
    so a single report surfaces as many problems as possible."""
    schema_errors = validate_schema(graph)
    semantic_errors = validate_semantics(graph)
    return ValidationResult(
        ok=not (schema_errors or semantic_errors),
        schema_errors=schema_errors,
        semantic_errors=semantic_errors,
    )


def validate_file(path: str | Path) -> ValidationResult:
    with open(path, encoding="utf-8") as fh:
        return validate(json.load(fh))
