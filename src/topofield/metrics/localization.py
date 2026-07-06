"""Localization metrics (docs/research_plan_final.md §11.3b) — STUBS.

F3Loc / Semantic-Rays conventions adopted unchanged: recall @ {0.1, 0.5, 1} m,
recall @ 1 m + 30 deg, median localization error, sequence-mode filtered recall,
reported per dataset (Structured3D, ZInD, Gibson-f) on the published splits.
These need real camera poses (Task L, Phase 3-L) and so are unimplemented here;
we will reuse the F3Loc evaluation code where possible rather than re-derive it.
"""

from __future__ import annotations

_RECALL_THRESHOLDS_M = (0.1, 0.5, 1.0)
_ORIENTATION_THRESHOLD_DEG = 30.0


def recall_at(*args, **kwargs):
    raise NotImplementedError(
        "Localization metrics land in Phase 3-L (§11.3b): recall@"
        f"{_RECALL_THRESHOLDS_M}m and @1m-{_ORIENTATION_THRESHOLD_DEG}deg, "
        "computed via the F3Loc protocol."
    )
