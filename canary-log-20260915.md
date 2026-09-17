
## 2026-09-15 23:0x MDT — ledger audit (24h window, sids 371-413)
- 43 spawns: 36 refused (84%) with canonical md5 b4aefd29108f232f9c0d5a4b030215c1,
  7 genuine. Refusals cluster in bursts: 371-374, 377-401 (25 straight), 408-413.
- Genuine: 375 (Madeon AXS recheck), 376 (refusal-resilience runbook),
  402-406 (FIVE pong canaries, resp "pong" md5 6fdb087aa3fbfbcb8287a593a0919e61),
  407 (muse-doc summary).
- New shape: pong canaries 402-406 SUCCEEDED mid-storm, then refusals resumed at
  408. Storm is intermittent, not blanket — matches the 03:52Z memory entry.
- New canary aa8d95da spawned this session; result pending delivery.

## 2026-09-15 23:1x MDT — deep-analysis window (pyarrow 25.0.1, ipython installed)
- Diurnal storm window found: refusal rate by hour (MDT) — 21:00 13%, 22:00 70%,
  00:00 70%, 01:00 40%, 02:00-20:00 0%. Storm is time-boxed late-evening, not random.
- Latency split is mechanical, zero overlap: refused n=33 (min 0s, med 1s, p95 3s,
  max 4s) vs genuine n=363 (min 8s, med 337s, p95 3242s, max 10940s).
  Completed-bug classifier: status=completed AND secs<=4 AND fr_len=384.
- Scheduler gate FLAPPING, not blanket: gate-probe-minimal executed probe-ok at
  22:39 (manual) and 22:47 (scheduled); all 40 runs 23:06-23:08 across 10 job ids
  skipped again. Per-job, time-varying.
- Watchdog: supervisor (gate-proof detached loop) live since 23:06, poller writing,
  boot id matches. Gap found: cell-boot-resume.sh does not restart the supervisor,
  so next cell death drops watchdog cover again (1m cron still gated).

## 2026-09-15 23:2x MDT — storm still live (direct ledger read)
- Fresh rows sids 413-424 (all within ~05:07-05:11Z): 12/12 REFUSED, canonical
  md5 b4aefd29108f232f9c0d5a4b030215c1, 384 chars, 1-6s durations, ledger
  status "completed" on every row. Includes pong canaries 413, 423, 424
  (trivial "reply: pong" probes) and the t1-t8 batch 414-421 (all 8 tasks
  refused pre-execution).
- Canary aa8d95da: RESOLVED (was marked LOST, corrected 23:25 MDT). The result
  arrived as a delayed subagent handoff: the spawn completed 2026-09-16T05:07:17Z
  with a canned refusal of the benign probe (ledger row never materialized, which
  is why the prompt/metadata search found nothing). So it was never lost — it
  was refused pre-execution, same as sids 413-424. Lesson stands: canary IDs must
  be embedded in the spawn prompt text to survive as ledger evidence.
- Diurnal pattern from 23:1x entry CONFIRMED by independent hourly dataframe
  (storm-dataframe-20260916.py): storm hours are 22:00 (09-14), 00:00-01:00
  (09-15), 21:00-23:00 (09-15) MDT; 16 quiet hours carried 352 genuine spawns
  with 0 refusals. "30h continuous" narrative corrected: two bursts separated
  by ~20h of zero spawn activity.
- spawn-truth-view.py verified on sids 413-424: 12/12 reclassified REFUSED.
  Its single-line-JSON parse bug fixed (was misreading {"rows":[...]} as JSONL).
