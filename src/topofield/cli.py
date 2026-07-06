"""`topofield` command-line entrypoint.

Subcommands (setup guide §2 "Commands"):
  topofield validate <path...>   validate HDG file(s) against schema + invariants
  topofield stats <path>         print per-graph statistics (§4.3, §11.5)
  topofield render <graph> [raster] [-o out.png]   draw the HDG for eyeballing

Kept dependency-light: `validate` and `stats` need only jsonschema + networkx;
`render` imports matplotlib lazily so the rest works without it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .graph import HDG, validate_file


def _cmd_validate(args: argparse.Namespace) -> int:
    exit_code = 0
    for path in args.paths:
        result = validate_file(path)
        if result.ok:
            print(f"OK    {path}")
        else:
            exit_code = 1
            print(f"FAIL  {path}")
            for err in result.errors:
                print(f"        {err}")
    return exit_code


def _cmd_stats(args: argparse.Namespace) -> int:
    hdg = HDG.from_file(args.path)
    print(json.dumps(hdg.stats(), indent=2))
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("render requires matplotlib (pip install matplotlib)", file=sys.stderr)
        return 2

    hdg = HDG.from_file(args.graph)
    out = Path(args.out) if args.out else Path(args.graph).with_suffix(".png")

    fig, ax = plt.subplots(figsize=(8, 8))
    if args.raster:
        try:
            img = plt.imread(args.raster)
            ax.imshow(img, extent=(0, 1, 1, 0), alpha=0.6)
        except Exception as exc:  # noqa: BLE001 - eyeballing tool, never fatal
            print(f"warning: could not load raster {args.raster}: {exc}", file=sys.stderr)

    # Place rooms/corridors by normalized centroid where available; others get a
    # simple ring layout. This is a quick-look overlay, not a publication figure.
    pos: dict[str, tuple[float, float]] = {}
    for n in hdg.nodes:
        c = n.get("attrs", {}).get("centroid")
        if c:
            pos[n["id"]] = (c[0], c[1])
    import math

    unplaced = [n["id"] for n in hdg.nodes if n["id"] not in pos]
    for i, nid in enumerate(unplaced):
        ang = 2 * math.pi * i / max(1, len(unplaced))
        pos[nid] = (0.5 + 0.45 * math.cos(ang), 0.5 + 0.45 * math.sin(ang))

    tau_style = {"wall-adjacent": ":", "door-connected": "-", "corridor-link": "--"}
    for e in hdg.adjacency_edges:
        (x0, y0), (x1, y1) = pos[e["source"]], pos[e["target"]]
        ax.plot([x0, x1], [y0, y1], tau_style.get(e["tau"], "-"), color="tab:blue", lw=1.5)
    level_color = {0: "black", 1: "tab:red", 2: "tab:green", 3: "tab:orange"}
    for n in hdg.nodes:
        x, y = pos[n["id"]]
        ax.scatter([x], [y], s=120, color=level_color.get(n["level"], "gray"), zorder=3)
        ax.annotate(n["id"], (x, y), fontsize=8, xytext=(3, 3), textcoords="offset points")

    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.set_title(f"HDG overlay — {Path(args.graph).name}")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="topofield", description="TopoField HDG tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate HDG file(s) against schema + invariants")
    p_val.add_argument("paths", nargs="+", help="HDG JSON file(s)")
    p_val.set_defaults(func=_cmd_validate)

    p_stats = sub.add_parser("stats", help="print per-graph statistics")
    p_stats.add_argument("path", help="HDG JSON file")
    p_stats.set_defaults(func=_cmd_stats)

    p_render = sub.add_parser("render", help="render an HDG overlay to PNG")
    p_render.add_argument("graph", help="HDG JSON file")
    p_render.add_argument("raster", nargs="?", help="optional background raster image")
    p_render.add_argument("-o", "--out", help="output PNG path")
    p_render.set_defaults(func=_cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
