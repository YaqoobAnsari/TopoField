---
description: Validate every HDG in a directory against schema + invariants and report violations
argument-hint: <dir>
allowed-tools: Bash(topofield:*), Bash(find:*), Glob, Read
---
Validate all HDG graphs under `$1`.

1. Find every `*.hdg.json` (and `*.json` under a `graphs/` folder) beneath `$1`,
   scoped narrowly to that path (do NOT recurse across /data broadly).
2. Run `topofield validate` on them.
3. Report a table: file, OK/FAIL, and for failures the first few schema/semantic
   errors. Summarize counts. Do not modify any file.
