"""TopoField — Hierarchical Directed Graph representations of institutional
buildings for physical field inference (CVPR 2026).

See docs/research_plan_final.md for the full plan and CLAUDE.md for the
non-negotiable invariants. The public surface intentionally starts small: the
HDG contract (topofield.graph) is the thing everything else is built against.
"""

__version__ = "0.1.0"

from . import graph  # noqa: F401  (re-export the contract package)

__all__ = ["graph", "__version__"]
