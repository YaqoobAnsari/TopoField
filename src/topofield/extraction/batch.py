"""Batch-convert a directory of Tesseract result graphs into an HDG corpus.

Finds Tesseract `*_post_pruning.json` graphs (the pruned, final graphs), runs the
adapter on each, and writes schema-valid `<name>.hdg.json` files. Used by the
real-image pipeline (scripts/pipeline/extract_real_images.slurm) to turn the 35
Input_Images floorplans into real HDG scaffolds for the annotation tool + models.
"""

from __future__ import annotations

import json
from pathlib import Path

from .tesseract_adapter import tesseract_json_to_hdg


def convert_tesseract_results(
    results_dir: str | Path,
    out_dir: str | Path,
    source_commit: str | None = None,
    pattern: str = "**/*_post_pruning.json",
) -> list[Path]:
    results_dir = Path(results_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for jf in sorted(results_dir.glob(pattern)):
        name = jf.parent.name or jf.stem
        try:
            tess = json.loads(jf.read_text(encoding="utf-8"))
            hdg = tesseract_json_to_hdg(tess, building_id=name, source_commit=source_commit)
        except Exception as exc:  # noqa: BLE001 - report + skip bad graphs, keep going
            print(f"SKIP {name}: {exc}")
            continue
        p = out / f"{name}.hdg.json"
        p.write_text(json.dumps(hdg, indent=2), encoding="utf-8")
        written.append(p)
        print(f"OK   {name} -> {p.name}")
    return written


def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Tesseract results dir -> HDG corpus")
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-commit", default=None)
    args = ap.parse_args()
    written = convert_tesseract_results(args.results_dir, args.out, args.source_commit)
    print(f"wrote {len(written)} HDG files to {args.out}")


if __name__ == "__main__":
    _main()
