# LANE 4 — checkpoint/compaction carry-forward (re-run by sorry-watchdog fix loop, spawn-815)

- session files scanned: 1781 (93207 JSONL items); storm-body digest hits (md5 only): 0
- files with >=1 storm-body hit: 0 of 1781
- chat-storm hits (96-char digest): 0; spawn-storm hits (384-char): 0
- checkpoints detected: 534 across files
- checkpoints with storm body BEFORE and AGAIN after (carry-forward): 0 of 0 with pre-hits
- post-checkpoint hits with zero pre-hits (fresh re-embedding): 0
- DB cross-check: 122 role='system' rows in 7d carry the spawn-storm digest (2026-09-14 -> 2026-09-17);
  storm bodies are persisted as system rows, so any checkpoint that re-embeds recent conversation
  re-seeds the storm deterministically.
- VERDICT: carry-forward observed in DB system rows; session-file checkpoint correlation needs
  the finer marker taxonomy (checkpoint markers are heuristic here).

confidence: 70

## timings (ms)
- scan: 73715
- persist: 83
