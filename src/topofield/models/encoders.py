"""HDG encoder + flat baseline (plan §8, §10.B, §11.4).

Both variants share an identical GATv2 backbone over the directed E_a graph and an
identical context->head. The ONLY difference is the pooling path:

  * pool="flat" : context = global mean/max over the graph (no hierarchy)
  * pool="hier" : context = parent-subtree mean (functional zone) + root (building)
                  pooled along the E_c containment tree

Pooling is PARAMETER-FREE, so the two variants have the same parameter budget and
the comparison isolates "does functional hierarchy help" (H4), consistent with the
oversquashing motivation in §5. Direction lives in edge_index, so flipping a delta
changes the output (direction-sensitivity test in tests/test_models.py).
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import GATv2Conv

from .data import NUM_EDGE_FEATURES, NUM_NODE_FEATURES


def _subtree_mean(h: torch.Tensor, level: torch.Tensor, parent: torch.Tensor) -> torch.Tensor:
    """Parameter-free bottom-up subtree mean per node along the containment tree."""
    n = h.size(0)
    sub_sum = h.clone()
    sub_cnt = torch.ones(n, 1, device=h.device)
    for lvl in (3, 2, 1):
        mask = (level == lvl) & (parent >= 0)
        if mask.any():
            p = parent[mask]
            sub_sum.index_add_(0, p, sub_sum[mask].clone())
            sub_cnt.index_add_(0, p, sub_cnt[mask].clone())
    return sub_sum / sub_cnt.clamp(min=1.0)


class HDGNet(nn.Module):
    def __init__(self, pool: str = "hier", hidden: int = 64, layers: int = 3, heads: int = 4):
        super().__init__()
        assert pool in ("flat", "hier")
        self.pool = pool
        self.convs = nn.ModuleList()
        in_dim = NUM_NODE_FEATURES
        for _ in range(layers):
            self.convs.append(
                GATv2Conv(in_dim, hidden, heads=heads, edge_dim=NUM_EDGE_FEATURES, concat=False)
            )
            in_dim = hidden
        self.context = nn.Linear(2 * hidden, hidden)
        self.head = nn.Sequential(nn.Linear(2 * hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, g: dict) -> torch.Tensor:
        x, ei, ea = g["x"], g["edge_index"], g["edge_attr"]
        h = x
        for conv in self.convs:
            h = F.relu(conv(h, ei, ea))

        if self.pool == "flat":
            gmean = h.mean(dim=0, keepdim=True).expand_as(h)
            gmax = h.max(dim=0, keepdim=True).values.expand_as(h)
            ctx_raw = torch.cat([gmean, gmax], dim=1)
        else:
            level, parent = g["level"], g["parent_idx"]
            p = _subtree_mean(h, level, parent)
            parent_ctx = torch.where((parent >= 0).unsqueeze(1), p[parent.clamp(min=0)], p)
            root = (level == 0).nonzero(as_tuple=True)[0]
            root_ctx = (
                p[root[0]].unsqueeze(0).expand_as(h)
                if root.numel()
                else p.mean(0, keepdim=True).expand_as(h)
            )
            ctx_raw = torch.cat([parent_ctx, root_ctx], dim=1)

        ctx = F.relu(self.context(ctx_raw))
        out = self.head(torch.cat([h, ctx], dim=1)).squeeze(-1)
        return out  # per-node scalar; caller reads room_mask


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
