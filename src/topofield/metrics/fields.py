"""Physical-field metrics (docs/research_plan_final.md §11.3, §11.3c).

Task T (thermal) and Task E (egress) share ranking / clustering-agreement
metrics. Thin, well-tested wrappers over scipy/scikit-learn so the definitions
live in one place and never get re-derived ad hoc in notebooks (setup guide §6).
"""

from __future__ import annotations

from collections.abc import Sequence


def thermal_zone_ari(pred_labels: Sequence[int], gt_labels: Sequence[int]) -> float:
    """Adjusted Rand Index of predicted vs simulation thermal zones (§11.3).
    Headline metric for H3 (ARI > 0.4; random ~ 0.1)."""
    from sklearn.metrics import adjusted_rand_score

    return float(adjusted_rand_score(gt_labels, pred_labels))


def thermal_zone_nmi(pred_labels: Sequence[int], gt_labels: Sequence[int]) -> float:
    """Normalized Mutual Information of predicted vs simulation zones (§11.3)."""
    from sklearn.metrics import normalized_mutual_info_score

    return float(normalized_mutual_info_score(gt_labels, pred_labels))


def rank_spearman(pred: Sequence[float], gt: Sequence[float]) -> float:
    """Spearman rho for temperature ordering / corridor egress-load ranking
    (§11.3, §11.3c)."""
    from scipy.stats import spearmanr

    # .statistic exists at runtime; scipy's type stubs omit it (attr-defined).
    return float(spearmanr(pred, gt).statistic)  # type: ignore[attr-defined]


def betweenness_pearson(pred: Sequence[float], gt: Sequence[float]) -> float:
    """Pearson r for the corridor-betweenness sanity head (§8 head 6, §11.2)."""
    from scipy.stats import pearsonr

    # .statistic exists at runtime; scipy's type stubs omit it (attr-defined).
    return float(pearsonr(pred, gt).statistic)  # type: ignore[attr-defined]


def bottleneck_precision_at_k(
    pred_ranking: Sequence[str], gt_bottlenecks: Sequence[str], k: int
) -> float:
    """precision@k for egress bottleneck identification (§11.3c)."""
    if k <= 0:
        raise ValueError("k must be positive")
    topk = list(pred_ranking)[:k]
    gt = set(gt_bottlenecks)
    if not topk:
        return 0.0
    return sum(1 for n in topk if n in gt) / len(topk)
