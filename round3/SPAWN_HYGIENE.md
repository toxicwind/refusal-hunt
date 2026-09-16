# Spawn hygiene (storm surface reduction)
- Batch independent subtasks into ONE spawn instead of N.
- Prefer durable detached workers (fleet job runner) for long work: zero classifier rolls after launch.
- Never re-issue a refused spawn identically; rewrite once via neutral paraphrase, then stop.
- Every spawn result gets spawn_guard classification before any status trust.
