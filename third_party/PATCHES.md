# third_party patches log

`third_party/` is read-only in spirit (CLAUDE.md). Baselines are cloned and
**pinned by upstream commit**, and their published home-benchmark numbers are
reproduced *before* any change (setup guide §4). Every modification to
third-party code is logged here with rationale — nothing is silently edited.

For each baseline, first record where it came from:

## tesseract  (raster-lane backbone AND §10.B baseline)
- Upstream: https://github.com/YaqoobAnsari/Tesseract2
- Pinned commit: `24074a4a1c80d76eb09a0900cea4c5054c32e538`  (cloned 2026-07-06)
- Env: see `third_party/tesseract/ENV.md`  (Python 3.12, torch 2.9.1 CPU — quarantined)
- Analysis + integration plan: `docs/phase0/tesseract_analysis.md`
- Reproduced home numbers: _TODO (reproduce-first gate §4): run `make_graph` on a
  sample in `Input_Images/`, confirm node/edge counts + timing/scaling curve vs the
  committed `Results/`, record here before any modification._

### Patches
| Date | File:line | Change | Why | By |
|---|---|---|---|---|
| — | — | none yet | integration is via `src/topofield/extraction/tesseract_adapter.py` (our side), not upstream edits | — |

## <template for next baseline>
- Upstream: <repo url>
- Pinned commit: <full sha>  (also goes in the paper's reproducibility statement)
- Env: see `third_party/<baseline-name>/ENV.md`
- Reproduced home numbers: <metric = value, dataset, date>  (e.g. F3Loc 36.6% recall@1m Gibson-f)

Rule of thumb: the *only* acceptable patches are (a) integration seams we own
(e.g. the single F3Loc prior-injection point) and (b) unavoidable build/env
fixes. Refactors, reformatting, and "improvements" are not patches — do not make
them.
