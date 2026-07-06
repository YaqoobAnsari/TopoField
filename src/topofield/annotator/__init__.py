"""HDG annotation engine + web tool.

The annotation tool turns an extracted HDG scaffold (from the Tesseract adapter)
into a fully-specified HDG: functional zones (E_c), edge types (tau), and access
direction (delta). Everything the UI can do is a pure, validated operation in
`operations` — so the graph edits are testable without a browser and can NEVER
produce an invalid HDG.

Design invariant: zoning rewires the containment tree (E_c) only; physical
adjacency (E_a) is never touched by zoning — the plan's two-families separation.
"""

from . import operations

__all__ = ["operations"]
