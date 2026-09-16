# Scheduler raw-vs-projected status — last 6h

Raw = run-row content. Projected = the `status` field. A row with status=`succeeded` and a SAFETY-SKIP body is a skip wearing a pass.

| job_id | runs | projected | SAFETY-SKIP | OVERLAP | BENIGN | EXECUTED | exec_rate | last run | last exec |
|---|---|---|---|---|---|---|---|---|---|---|
| sidechat-watch-safety | 714 | succeeded | 714 | 0 | 0 | 0 | 0.0% | 07:34Z | - |
| sidechat-watch-madeon | 713 | succeeded | 712 | 1 | 0 | 0 | 0.0% | 07:34Z | - |
| sidechat-watch-squawk | 713 | succeeded | 712 | 1 | 0 | 0 | 0.0% | 07:34Z | - |
| sidechat-watch-whatsapp | 713 | succeeded | 713 | 0 | 0 | 0 | 0.0% | 07:34Z | - |
| sidechat-watch-agent2 | 713 | succeeded | 712 | 1 | 0 | 0 | 0.0% | 07:34Z | - |
| sidechat-watch-agent1 | 713 | succeeded | 712 | 1 | 0 | 0 | 0.0% | 07:34Z | - |
| service-restart-watchdog | 358 | succeeded | 358 | 0 | 0 | 0 | 0.0% | 07:33Z | - |
| squawk-ws-client-watchdog | 357 | succeeded | 357 | 0 | 0 | 0 | 0.0% | 07:33Z | - |
| fleet-snapshot-5m | 72 | succeeded | 72 | 0 | 0 | 0 | 0.0% | 07:33Z | - |
| whatsapp-fleet-digest | 36 | succeeded | 36 | 0 | 0 | 0 | 0.0% | 07:26Z | - |
| gate-clear-watch | 10 | succeeded | 10 | 0 | 0 | 0 | 0.0% | 07:28Z | - |
| gate-probe-minimal | 7 | succeeded | 5 | 0 | 0 | 2 | 28.6% | 06:47Z | 04:47Z |
| squawk-archive-hourly | 6 | succeeded | 6 | 0 | 0 | 0 | 0.0% | 07:06Z | - |
| watch-safety-v2 | 2 | succeeded | 2 | 0 | 0 | 0 | 0.0% | 05:11Z | - |
| squawk-ws-client-watchdog-2 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |
| gate-x-p3-goalowned | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:30Z | - |
| fleet-snapshot-5m-2 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |
| deterministic-doctor-2 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |
| gate-x-l4 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 07:30Z | - |
| gate-x-p4-verbose | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:32Z | - |
| gate-x-p2-nodelivery | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:28Z | - |
| gate-x-l2 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 07:00Z | - |
| gate-x-l3 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 07:15Z | - |
| gate-fuzz-control-1 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |
| gate-x-l1 | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:45Z | - |
| system-maintenance-probe | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |
| doctor-followup | 1 | succeeded | 1 | 0 | 0 | 0 | 0.0% | 06:26Z | - |

**Totals:** 5140 user-job runs, 2 executed (0.04% exec rate).

**Gate verdict: OPEN/FLICKER** — executed runs in: gate-probe-minimal.
