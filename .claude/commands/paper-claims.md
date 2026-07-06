---
description: Check results tables against the §12 hypothesis thresholds and report pass/fail
allowed-tools: Read, Glob, Grep
---
Check the current results against the §12 hypotheses and report pass/fail.

Read the generated results tables (never hand-transcribed) and evaluate each
falsifiable threshold, e.g.:
- H3: thermal ARI > 0.4 (random ~0.1)
- H4: functional hierarchy beats flat by > 10 ARI
- H7: HDG prior beats F3Loc-uniform AND flat room-label prior on recall@1m
- H8: learned egress ranking beats raw betweenness by > 0.1 Spearman; bottleneck P@5 > 0.6

For each hypothesis print: threshold, observed value, PASS/FAIL, and the source
table/row. Flag any claim asserted in prose (docs/) that the numbers do not support.
