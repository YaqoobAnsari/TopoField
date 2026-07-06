"""Metrics — one implementation per definition, matching §11 exactly.

Implemented now (cheap, fixture-testable):
  topology.py : hierarchy_recovery_f1, edge_type_accuracy, direction_accuracy, adjacency_ged (§11.2)
  fields.py   : thermal_zone_ari/nmi, rank_spearman, betweenness_pearson,
                bottleneck_precision_at_k (§11.3, §11.3c)

Deferred until real data exists (see reconstruction.py, localization.py):
  reconstruction metrics (§11.1) need pixel/polygon GT;
  localization recall@X (§11.3b) needs camera poses.
"""

from .fields import (
    betweenness_pearson,
    bottleneck_precision_at_k,
    rank_spearman,
    thermal_zone_ari,
    thermal_zone_nmi,
)
from .topology import (
    adjacency_ged,
    direction_accuracy,
    edge_type_accuracy,
    hierarchy_recovery_f1,
)

__all__ = [
    "hierarchy_recovery_f1",
    "edge_type_accuracy",
    "direction_accuracy",
    "adjacency_ged",
    "thermal_zone_ari",
    "thermal_zone_nmi",
    "rank_spearman",
    "betweenness_pearson",
    "bottleneck_precision_at_k",
]
