"""Data generation and loading.

`synthetic` produces institutional-scale HDGs procedurally. These are for METHOD
DEVELOPMENT and PRETRAINING ONLY (plan §6.5) — they are never the real InstBuild
benchmark and are never used for evaluation claims. Every generated graph is
stamped as synthetic in its metadata.
"""

from .dataset import (
    HDGDataset,
    building_id_of,
    group_by_building,
    load_hdg_dir,
    lobo_splits,
)
from .synthetic import generate_corpus, generate_hdg

__all__ = [
    "generate_hdg",
    "generate_corpus",
    "HDGDataset",
    "load_hdg_dir",
    "lobo_splits",
    "group_by_building",
    "building_id_of",
]
