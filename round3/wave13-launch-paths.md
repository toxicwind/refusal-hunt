# Wave 13 — launch-path comparison (2026-09-16 08:23 UTC)

Same benign task class (reply with an exact nonce string) through three launch paths, same minute.

| Path | Mechanism | Nonce | Result | Time |
|---|---|---|---|---|
| A | clean workflow child (`workflow.launch_async` + `agent()`) | WAVE13-PONG-a1b2c3 | genuine, exact echo | 1.34s |
| B | ordinary `subagent.spawn` | WAVE13-PONG-d4e5f6 | refused at init, storm signature | n/a |
| C | fleet job via `~/workspace/bin/taskhook run` | WAVE13-PONG-g7h8i9 | genuine, exact echo | 133ms |

## Refusal classification (path B)

- Handoff text md5: `b4aefd29108f232f9c0d5a4b030215c1` — canonical storm signature (384 chars).
- Ledger rows: `agent.subagent_spawns` spawn_ids 515–521 (7 rows: this probe + waves 10, 11, 12, 14, 15, 16 workers), all `status='completed'`, all final_response digest `b4aefd29108f232f9c0d5a4b030215c1`, length 384.
- Refusal window: 08:22:56–08:23:03Z, 7/7 ordinary spawns refused at init.
- Paths A and C executed genuinely inside the same window.

## Interpretation

Cleanest A/B yet: ordinary-spawn path refused while workflow-child and fleet-job paths served the same benign task class in the same minute. The spawn-layer refusal is path-specific, not task-specific. `completed` status on refused rows confirmed again — never trust it; always check the digest.
