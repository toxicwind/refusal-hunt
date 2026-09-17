# Common-cause onset: storm + scheduler gate flipped in the same minute (2026-09-16)

Measured (ipython, ledger + scheduler.job_runs):

- Refusal-storm onset: sid 365, 2026-09-15 04:09:28Z (first canned refusal md5 b4aefd…).
- Scheduled-task safety-review first skip: 2026-09-15 04:08:27Z (fleet-snapshot-5m).
- Delta: **61 seconds**.
- Preceding event: platform scheduler restart/reattach window 2026-09-15 01:56–05:17Z
  (scheduler.events: reattached_after_restart / requeued_after_restart).

Inference: one platform-side event at ~04:08Z put BOTH gates in a bad state —
the spawn serving-path classifier (refusal storm, burst lethality 94.6%) and the
scheduled-task safety review (blanket skip of all user jobs). Not two independent
failures, and not caused by any of our edits (first cron mutation was 23.6h later).

Corroboration: 25 consecutive genuine spawns (sids 340–364) immediately before
04:09Z; zero genuine spawns in the 111 minutes after except a single sid 366.

Divergence note: the gates are not perfectly coupled NOW — today's spawn clear
window (402–407, 04:29–04:35Z) preceded the scheduler gate flicker-open
(04:39–05:02Z) by minutes. Common onset, independent recovery.

Operational consequence: neither gate is fixable from here (both platform-side).
The fleet posture stands: storm-aware dispatch (one canary before fan-out,
bridge agents during bursts), mechanical md5 verdicts, poller-guard.sh for
watchdog liveness independent of the gated scheduler.
