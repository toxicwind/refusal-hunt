# LANE 2 — fake-completed spawn audit (re-run by sorry-watchdog fix loop, spawn-819)

- 7-day census: 769 completed spawns with final_response; 121 refused = 15.7% (md5 digest match)
- worst parents (refused/total):
  7240686c-d790-463d-bad2-c969fc65885e: 30/258 = 11.6%
  802811a3-2226-42dd-b347-9754def28d22: 21/63 = 33.3%
  ff521137-c3c1-4121-9f11-8bbc2420ff24: 19/26 = 73.1%
  ac045111-1a54-4758-932c-daefccee45e8: 11/16 = 68.8%
  58246538-8068-45cc-80bd-3837e3558cbd: 11/77 = 14.3%
  0783c1d6-9cdb-422f-9195-d9ff9d48cdf8: 10/13 = 76.9%
- time clustering (last 3 days, 6h blocks): refusals concentrate in storm blocks:
  2026-09-14T06:00:00+00:00: 1/101 = 1.0%
  2026-09-14T12:00:00+00:00: 0/36 = 0.0%
  2026-09-14T18:00:00+00:00: 0/96 = 0.0%
  2026-09-15T00:00:00+00:00: 5/108 = 4.6%
  2026-09-15T06:00:00+00:00: 19/21 = 90.5%
  2026-09-16T00:00:00+00:00: 33/51 = 64.7%
  2026-09-16T06:00:00+00:00: 45/236 = 19.1%
  2026-09-16T12:00:00+00:00: 2/55 = 3.6%
  2026-09-16T18:00:00+00:00: 7/52 = 13.5%
  2026-09-17T00:00:00+00:00: 0/1 = 0.0%
  2026-09-17T06:00:00+00:00: 9/12 = 75.0%
- high-refusal blocks (>=50%): 2026-09-15T06:00:00+00:00, 2026-09-16T00:00:00+00:00, 2026-09-17T06:00:00+00:00
- content cut: refused prompts median length 2438 chars vs genuine 7154 (sampled n=14/14);
  refused set includes BOTH autonomy-forensics prompts AND plain 'Workflow Agent Output Contract' workflow prompts;
  genuine set is dominated by the same workflow-contract prompts -> refusal does NOT separate on autonomy/security tokens,
  nor on prompt length (refused shorter on median). Verdict: TIME-clustering dominates; content is a weak/nonexistent signal.

confidence: 90 (counts are full 7-day census; content cut is a 50/50 sample)

## timings (ms)
- tables: 10
- persist: 6
