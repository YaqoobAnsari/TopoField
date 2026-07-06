"""Reconstruction metrics (docs/research_plan_final.md §11.1) — STUBS.

Community-standard precision/recall/F1 with IoU>=0.5 room match, 5 px corner,
5 deg angle; Room Recall reported as a function of building size (the scale
exhibit). These require pixel/polygon ground truth (Phase 1 corpus + baseline
outputs) that does not exist yet, so they are intentionally unimplemented.

When implemented, pin them in tests/test_metrics.py against a small labelled
fixture, exactly as the topology metrics are pinned today.
"""

from __future__ import annotations

_ROOM_IOU_THRESHOLD = 0.5
_CORNER_PX_THRESHOLD = 5.0
_ANGLE_DEG_THRESHOLD = 5.0


def room_prf(*args, **kwargs):
    raise NotImplementedError(
        "Reconstruction metrics land in Phase 4 (§11.1). Thresholds fixed: "
        f"IoU>={_ROOM_IOU_THRESHOLD}, corner {_CORNER_PX_THRESHOLD}px, "
        f"angle {_ANGLE_DEG_THRESHOLD}deg."
    )
