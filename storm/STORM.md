# STORM.md — Status: WIP

Active incident doc, not a postmortem. Updated as the storm moves.

## Policy

- Echo preserved. Every occurrence is its own row. Deduplication never applies to event rows — only to storage compression. A digest census is aggregation and is labeled as such.
- Full bodies. No truncation. No grep-snippet conclusions. Hash is the verdict (`md5(final_response)`), never `status`.
- `refresh.py`: row identity only; echo is never suppressed.

## Lanes (concept → actual artifact)

- lane-0 raw input capture → session JSONLs, verbatim. No filtering, no redaction.
- lane-1 transport capture → pcap/websocket where reachable. NOTE: serving layer unreachable from this container (verified 2026-09-16); untruncated capture from here is not currently possible. Truncation here is a known gap, not a defect in procedure.
- lane-2 classifier observation → `ledger/anomalies.parquet` (zstd), `sorry-audit/LATEST.json`. Every decline event: UTC timestamp, session id, digest, length, classification, retry outcome. Append-only.
- lane-3 token accounting → per-agent/per-turn/per-tool; tiktoken `cl100k_base` measured columns, flattened. No aggregation that loses the row.
- lane-4 orchestrator state → scheduler jobs/runs, watchdog heartbeats, launcher state.
- lane-5 subagent output → raw delivery packages preserved; blake3 manifest where produced. No paraphrase.
- lane-6 final delivery → analyst register, raw format. Correlated generator code shipped with every artifact (PNG proof rule).

Existing lane material: `storm-lanes/` (lane1–lane8 extracts), `storm/storm_analysis.parquet`, `storm/burst_analysis` outputs.

## Known failure modes

- Dedupe creeping into analysis through aggregation (census labeled, rows kept).
- Summarization of subagent output through well-intentioned cleanup.
- `status=completed` trusted as success — red herring; hash is the verdict.
- Scheduled-task `succeeded` with skip summaries — classify from `result_summary`, never status alone.
- Compaction/checkpoint re-seeding canned bodies into fresh context.
- Client echo replaying refused turns as new user messages (preserved as rows, not collapsed).

## WIP

- Lane-1 untruncated transport capture: blocked from container; route via awrawr-pc unproven.
- Five consecutive literal-Android/main acceptance cycles: open.
- Serving-path repair, reboot-persistent: unproven.
