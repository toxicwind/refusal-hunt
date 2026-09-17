# Debug state — parquet-first paradigm (Chris's order, 2026-09-15)

All refusal-hunt debug state lives in **parquet dataframes**, not in ad-hoc SQL pulls or chat memory.
Fast to read (32ms for 396 rows), typed, versioned, replayable.

## Files (`~/workspace/refusal-hunt/`)

| file | contents |
|---|---|
| `spawns.parquet` | spawn ledger extract: one row per `agent.subagent_spawns` row |
| `spawns.csv` | same data, human-diffable source of truth for appends |
| `timings.parquet` | every operation timed at **microsecond** resolution (`utime.py`) |
| `timings.jsonl` | append log feeding `timings.parquet` |
| `utime.py` | `now_us()`, `span(name, detail)` context manager, `log_event()` |
| `refresh.py` | `python3 refresh.py new_rows.csv` — keyed merge on `spawn_id` / rewrite `spawns.parquet` (snappy). Row identity only; echo is never suppressed |
| `analyze.py` | `python3 analyze.py [--report DIR]` — refusal stats, storm status, timing split, hourly table |
| `new_rows.csv` | staging for the next refresh (overwritten each cycle) |
| `nightly/` | dated reports from the nightly cron |

## `spawns.parquet` schema

`spawn_id, created_at, secs, status, agent_type, depth, prompt_len, fr_len, refused`

- `status`: 0=completed 1=errored — **red herring, never a verdict**
- `agent_type`: 0=null 1=browser_task 2=deep_research
- `refused`: 1 iff `md5(final_response) == b4aefd29108f232f9c0d5a4b030215c1` (hash only; never store/quote the string)
- Verdict rule: hash match = refused regardless of status. Different hash ≠ success — verify substance/artifacts.

## APIs available (verified live 2026-09-15)

- **pyarrow 25.0.1**: `pa`, `parquet`, `compute` (incl. `hash_*` kernels), `dataset`, `csv`, `json`, `feather`, `ipc`, `orc`, `fs`, `acero`
- **pandas 2.1.4** (pyarrow engine, snappy compression)
- **muse.db** (read-only SELECT; non-recursive CTEs only, name must start with `hatch_cte_`): relevant tables —
  `agent.subagent_spawns` (ledger), `agent.agents` (status/depth/model, join on child_agent_id),
  `agent.subagent_progress`, `agent.subagent_progress_tool_events`, `agent.subagent_progress_message_events`,
  `agent.subagent_monitor_decisions`, `agent.token_usage`, `scheduler.jobs`, `scheduler.job_runs`,
  `scheduler.job_definitions`, `agent.agent_ancestors`
- Allowed SQL functions include `md5`, `char_length`, `count`, `avg`, `min`, `max`, `date_trunc`, `time_bucket`.

## Refresh procedure (also what the nightly cron does)

1. `SELECT max(spawn_id) FROM parquet` (via pandas) → query `muse.db` for `agent.subagent_spawns` rows with greater `created_at`
2. Write compact rows to `new_rows.csv` (same schema; compute `refused` from the md5 at extraction)
3. `python3 refresh.py new_rows.csv`
4. `python3 analyze.py --report nightly/`

## Standing rules

- Time **everything** at microsecond resolution; log via `utime`.
- Never trust ledger `status`. Hash is the verdict.
- Patch forward only. No rollback.
