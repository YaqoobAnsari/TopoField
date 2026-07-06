"""HDG data structure and derived quantities.

The Hierarchical Directed Graph (HDG) is defined formally in
docs/research_plan_final.md §4.3 and specified in prose in docs/hdg_schema.md.
The machine-checkable contract is schemas/hdg.schema.json.

This module is deliberately dependency-light: loading and iterating an HDG needs
only the standard library. networkx is imported lazily inside the functions that
need it (stats, betweenness) so that `topofield validate` works in minimal envs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Enum vocabularies mirrored from schemas/hdg.schema.json. Keep in sync via
# docs/decisions/ if these ever change.
LEVELS = {0: "building", 1: "wing/zone", 2: "corridor", 3: "room"}
TAU = ("wall-adjacent", "door-connected", "corridor-link")
DELTA = ("bidirectional", "forward", "backward")

# Adjacency types a person/heat/air can actually pass through. A shared wall is
# an adjacency but NOT a traversal path — this distinction matters for
# betweenness-as-circulation (see betweenness()).
TRAVERSABLE_TAU = ("door-connected", "corridor-link")


def load_hdg(path: str | Path) -> dict[str, Any]:
    """Read an HDG JSON file into a plain dict. Does not validate — call
    topofield.graph.validate.validate() for that."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class HDG:
    """Thin, validated-by-convention wrapper over the raw HDG dict.

    Construct with HDG.from_dict / HDG.from_file. This class does NOT re-validate;
    it assumes the payload already passed topofield.graph.validate.validate().
    """

    raw: dict[str, Any]

    # --- constructors ---------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HDG:
        return cls(raw=data)

    @classmethod
    def from_file(cls, path: str | Path) -> HDG:
        return cls(raw=load_hdg(path))

    # --- basic accessors ------------------------------------------------
    @property
    def version(self) -> str:
        return self.raw.get("version", "")

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return self.raw.get("nodes", [])

    @property
    def containment_edges(self) -> list[dict[str, Any]]:
        return self.raw.get("containment_edges", [])

    @property
    def adjacency_edges(self) -> list[dict[str, Any]]:
        return self.raw.get("adjacency_edges", [])

    @property
    def node_ids(self) -> set[str]:
        return {n["id"] for n in self.nodes}

    @property
    def level(self) -> dict[str, int]:
        """The level map L: node id -> {0,1,2,3}."""
        return {n["id"]: n["level"] for n in self.nodes}

    def nodes_at_level(self, level: int) -> list[str]:
        return [n["id"] for n in self.nodes if n["level"] == level]

    def delta_of(self, edge: dict[str, Any]) -> str:
        """Access direction of an adjacency edge, defaulting to bidirectional."""
        return edge.get("delta", "bidirectional")

    # --- networkx views -------------------------------------------------
    def to_containment_digraph(self):
        """Family-1 (E_c) as a directed graph: parent -> child."""
        import networkx as nx

        g = nx.DiGraph()
        for n in self.nodes:
            g.add_node(n["id"], level=n["level"], **n.get("attrs", {}))
        for e in self.containment_edges:
            g.add_edge(e["source"], e["target"])
        return g

    def to_adjacency_graph(self, traversable_only: bool = False):
        """Family-2 (E_a) as an undirected graph.

        traversable_only=True drops wall-adjacent edges, leaving only paths a
        person / air / heat-via-door can pass through — the correct graph for
        circulation betweenness. Access direction (delta) is ignored here; use
        to_adjacency_digraph() when direction matters.
        """
        import networkx as nx

        g = nx.Graph()
        for n in self.nodes:
            g.add_node(n["id"], level=n["level"], **n.get("attrs", {}))
        for e in self.adjacency_edges:
            if traversable_only and e["tau"] not in TRAVERSABLE_TAU:
                continue
            g.add_edge(e["source"], e["target"], tau=e["tau"], delta=self.delta_of(e))
        return g

    def to_adjacency_digraph(self, traversable_only: bool = False):
        """Family-2 (E_a) as a directed graph honouring delta.

        bidirectional -> both arcs; forward -> source->target; backward ->
        target->source.
        """
        import networkx as nx

        g = nx.DiGraph()
        for n in self.nodes:
            g.add_node(n["id"], level=n["level"], **n.get("attrs", {}))
        for e in self.adjacency_edges:
            if traversable_only and e["tau"] not in TRAVERSABLE_TAU:
                continue
            s, t, d = e["source"], e["target"], self.delta_of(e)
            attrs = {"tau": e["tau"], "delta": d}
            if d in ("bidirectional", "forward"):
                g.add_edge(s, t, **attrs)
            if d in ("bidirectional", "backward"):
                g.add_edge(t, s, **attrs)
        return g

    # --- derived quantities --------------------------------------------
    def betweenness(self, traversable_only: bool = True) -> dict[str, float]:
        """Node betweenness centrality on the (undirected) adjacency graph.

        Defaults to the traversable subgraph (wall-adjacent edges excluded),
        which is the circulation-centrality reading used throughout the project:
        corridors that carry cross-zone traffic score highest. Note that a
        cross-hierarchy door (e.g. the canonical Nurse<->Records edge) can lift
        a room's betweenness to corridor level — that is the representation's
        point, not an artefact.
        """
        import networkx as nx

        return nx.betweenness_centrality(self.to_adjacency_graph(traversable_only))

    def stats(self) -> dict[str, Any]:
        """Per-graph statistics for the paper's complexity table (§4.3, §11.5)."""
        import networkx as nx

        level_counts = {LEVELS[k]: len(self.nodes_at_level(k)) for k in sorted(LEVELS)}
        adj = self.to_adjacency_graph(traversable_only=False)
        degrees = [d for _, d in adj.degree()]
        cont = self.to_containment_digraph()

        # Hierarchy depth = longest root-to-leaf chain in the containment forest.
        depth = 0
        roots = [n for n in cont.nodes if cont.in_degree(n) == 0]
        for r in roots:
            if cont.number_of_nodes():
                lengths = nx.single_source_shortest_path_length(cont, r)
                depth = max(depth, max(lengths.values()) if lengths else 0)

        # Diameter over the traversable circulation graph's largest component.
        trav = self.to_adjacency_graph(traversable_only=True)
        diameter: int | None = None
        if trav.number_of_nodes():
            comps = list(nx.connected_components(trav))
            if comps:
                largest = trav.subgraph(max(comps, key=len))
                if largest.number_of_nodes() > 1:
                    diameter = nx.diameter(largest)
                else:
                    diameter = 0

        return {
            "num_nodes": len(self.nodes),
            "nodes_by_level": level_counts,
            "num_containment_edges": len(self.containment_edges),
            "num_adjacency_edges": len(self.adjacency_edges),
            "hierarchy_depth": depth,
            "circulation_diameter": diameter,
            "degree_min": min(degrees) if degrees else 0,
            "degree_max": max(degrees) if degrees else 0,
            "degree_mean": round(sum(degrees) / len(degrees), 3) if degrees else 0.0,
        }
