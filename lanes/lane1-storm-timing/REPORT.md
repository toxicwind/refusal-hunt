# LANE 1 — storm timing census (re-run by sorry-watchdog fix loop, spawn-812)

- ledger rows: 1161 (0 with unparseable ts, excluded)
- groups (parent_agent_id, chat rows pooled): 11
- burst groups (>=5 rows in 10 min): 6
- inter-arrival within group: n=1079, median=6s, p90=117s, p99=5157s, max=71944s
- top 5 burst groups:
  0783c1d6-9cdb-422f-9195-d9ff9d48cdf8: 2026-09-16T05:07:43+00:00 -> 2026-09-16T05:07:43+00:00 n=5 digests=b4aefd29108f232f9c0d5a4b030215
  58246538-8068-45cc-80bd-3837e3558cbd: 2026-09-16T08:22:55+00:00 -> 2026-09-16T08:22:55+00:00 n=5 digests=b4aefd29108f232f9c0d5a4b030215
  5a4f76c0-e3a4-4069-ba6f-3113917102dc: 2026-09-16T22:57:06+00:00 -> 2026-09-16T22:57:06+00:00 n=5 digests=b4aefd29108f232f9c0d5a4b030215
  7240686c-d790-463d-bad2-c969fc65885e: 2026-09-16T06:31:57+00:00 -> 2026-09-16T06:31:57+00:00 n=5 digests=b4aefd29108f232f9c0d5a4b030215
  802811a3-2226-42dd-b347-9754def28d22: 2026-09-16T07:43:56+00:00 -> 2026-09-16T07:43:57+00:00 n=5 digests=b4aefd29108f232f9c0d5a4b030215
- hourly histogram (UTC hour -> rows):
  2026-09-15 10:00:00+00:00 -> 1
  2026-09-15 11:00:00+00:00 -> 1
  2026-09-15 19:00:00+00:00 -> 5
  2026-09-16 00:00:00+00:00 -> 20
  2026-09-16 01:00:00+00:00 -> 11
  2026-09-16 02:00:00+00:00 -> 26
  2026-09-16 03:00:00+00:00 -> 93
  2026-09-16 04:00:00+00:00 -> 39
  2026-09-16 05:00:00+00:00 -> 189
  2026-09-16 06:00:00+00:00 -> 166
  2026-09-16 07:00:00+00:00 -> 179
  2026-09-16 08:00:00+00:00 -> 108
  2026-09-16 09:00:00+00:00 -> 47
  2026-09-16 10:00:00+00:00 -> 96
  2026-09-16 11:00:00+00:00 -> 19
  2026-09-16 17:00:00+00:00 -> 8
  2026-09-16 22:00:00+00:00 -> 121
  2026-09-16 23:00:00+00:00 -> 31
  2026-09-17 06:00:00+00:00 -> 1

NOTE: pre-onset user-message window and scheduler-skip correlation are lane7/lane5 territory;
this lane delivers the timing ground truth. Storm rows are sub-second-interleaved bursts (median 1s),
i.e. classifier-fire-then-client-replay amplification, not independent onsets.

confidence: 85

## timings (ms)
- load: 52
- onsets: 42
- bursts: 23
- inter: 11
- persist: 9
