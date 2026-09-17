# Wave 12 — completed-projection writer hunt (2026-09-16 08:45 UTC)

## Verdict: platform-side. Writer is `spawnd`; no owned code writes these rows.

### Owned-code search (negative)
- `rg "subagent_spawns"` across `~/workspace/skills`, `~/workspace/bin`, `~/workspace/*.py`: single hit — `~/workspace/t3-verify.py:16`, a `SELECT` (read-side analysis).
- Wider workspace search: all other hits are read-side analysis scripts (`storm-dataframe-20260916.py`, `spawn-truth-view.py`) or campaign docs. Zero `INSERT`/`UPDATE` writers in owned code.
- No owned migration, trigger, or projection touches `agent.subagent_spawns`.

### Platform binary evidence
- `strings` over `/opt/hatch/bin/*`: exactly three binaries reference `subagent_spawns` — `hatch`, `hatch-doctor`, `spawnd`.
- `spawnd` embeds the full DDL for `agent.subagent_spawns` (create table, `agent_subagent_spawns_*` indexes), including the terminal-state index predicate `where status is null or status not in ('completed','failed','cancelled')` and the `deferred_terminal_status` column.
- The postgres server behind `/run/hatch/postgres/.s.PGSQL.5432` has no visible PID in this namespace (wave 14) — the database itself lives across the isolation boundary with spawnd.
- No literal `UPDATE ... subagent_spawns ... SET status` string in the binary (queries are built at runtime); 80 `refus*` string hits exist but none tie to a status-write path visible statically.

### Boundary
The status projection (`status='completed'` on a refused spawn whose `final_response` is the canned body) is written by the platform spawn daemon (`/opt/hatch/bin/spawnd`), outside owned code and across the PID-67 isolation boundary. There is no owned patch point: no test to add, no forward patch to apply. The durable mitigation remains pre/post-classifier (digest-check every `completed` row; never trust status alone), as already practiced in waves 11/13.

### Not patched (correctly)
Per standing rules, platform binaries are not patched. No commit/push applies to this wave.
