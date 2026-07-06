#!/usr/bin/env python3
"""PostToolUse advisory: validate any *.hdg.json that was just written.

Best-effort and non-blocking (always exits 0): a completed write is not undone,
but an invalid graph is surfaced to the agent immediately. Uses `topofield` from
PATH, falling back to the known project env; silently skips if neither is present
(e.g. the hook shell has no env activated).
"""
import json
import os
import shutil
import subprocess
import sys

_ENV_FALLBACK = "/data/gpfs/projects/punim2769/envs/topofield/bin/topofield"


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    path = (data.get("tool_input", {}) or {}).get("file_path", "")
    if not path.endswith(".hdg.json"):
        sys.exit(0)

    exe = shutil.which("topofield")
    if not exe and os.path.exists(_ENV_FALLBACK):
        exe = _ENV_FALLBACK
    if not exe:
        sys.exit(0)  # no validator available in this shell; skip quietly

    try:
        r = subprocess.run(
            [exe, "validate", path], capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            sys.stderr.write(f"HDG validation FAILED for {path}:\n{r.stdout}{r.stderr}\n")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
