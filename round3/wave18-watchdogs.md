# Wave 18 — watchdog liveness + persistence (2026-09-16 09:10 UTC)

## Liveness
- Detector crons all enabled: `gate-probe-minimal` (1h), `gate-clear-watch` (15m), `service-restart-watchdog` (1m), `fleet-snapshot-5m` (5m), `squawk-ws-client-watchdog` (1m), `heartbeat` (30m).
- **Gate still CLOSED as of 02:28 MDT (08:28 UTC):** last 5 runs of `gate-probe-minimal` and last 5 of `gate-clear-watch` are all `status=succeeded` with `result_summary` = safety-review-skipped. The watchdogs are defined but cannot execute while the gate is closed — the tripwire cannot trip.
- The in-cell watchdogs (`service-restart-watchdog`, `squawk-ws-client-watchdog`) are user task-mode jobs, so they are equally gated. The only ungated liveness paths remain the awrawr-pc pitchfork `sorry-watchdog` (inotify-driven, pc-side) and the sovereign fleet job runner.

## Reboot persistence
- All cron definitions are files under `~/workspace/cron.d/` and `~/workspace/goals/*/crons/` — durable workspace state, survives container reboot, covered by the daily cell backup.
- Scheduler runtime state is platform-side; no user action can make a definition more persistent than the workspace files already are.

## Fixed sleeps in owned code
- None found. `~/workspace/bin/taskhook` documents "No fixed sleeps anywhere. Timeouts are fail-fast ceilings." No owned script uses `sleep N`. Nothing to replace.
