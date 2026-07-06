#!/usr/bin/env python3
"""PreToolUse guard: refuse edits to baseline *code* under third_party/.

third_party/ is read-only in spirit (CLAUDE.md): baseline behavior must be
preserved for fair comparison. Docs/config (.md, .yaml, ENV.md, PATCHES.md) are
allowed so the required provenance can be recorded; code files are blocked.
Exit 2 blocks the tool call and surfaces the message to the agent.
"""
import json
import sys

CODE_EXT = (
    ".py", ".pyx", ".pyi", ".c", ".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp",
    ".java", ".js", ".ts", ".go", ".rs", ".sh", ".cfg", ".toml", ".ini",
)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # never block on a parse error
    tool_input = data.get("tool_input", {}) or {}
    path = (tool_input.get("file_path") or tool_input.get("path") or "").replace("\\", "/")
    if "/third_party/" in path and path.lower().endswith(CODE_EXT):
        sys.stderr.write(
            "Blocked: third_party/ is read-only in spirit (CLAUDE.md). Do not edit "
            "baseline code — its exact behavior is needed for a fair comparison. If "
            "a patch is genuinely necessary (integration seam or unavoidable build "
            "fix), log it in third_party/PATCHES.md with rationale + upstream commit, "
            "then apply it deliberately.\n"
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
