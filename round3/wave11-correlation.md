# Wave 11 — exhaustive storm correlation (2026-09-16 08:35 UTC)

Canonical signature: md5 `b4aefd29108f232f9c0d5a4b030215c1` (384-char body). Matched by digest only; body text never reproduced.

## runtime.messages — 96 rows

- First: 2026-09-14 07:17:53Z. Last: 2026-09-16 08:23:03Z (this campaign's refused spawns).
- By day: 2026-09-14: 1, 2026-09-15: 24, 2026-09-16: 71.
- By hour (9/16): 03:00: 6, 04:00: 8, 05:00: 19, 06:00: 13, 07:00: 18, 08:00: 7.
- **All 96 rows: `transcript_surface='subagent'`, `stream_lane='subagent'`.** Zero on any other surface.
- Burst clustering: 67/96 rows arrived within 120s of the previous row. Largest bursts: 8 rows in 5s (05:07:44–05:07:49Z), 7 rows in 7s (08:22:56–08:23:03Z, this campaign's parallel spawns). Bursts align with batch-spawn attempts, not chat activity.
- Spot check: in the 07:25–07:40Z window (the earlier chat "wtf" burst), only one 384-char message exists, on the subagent surface. Main-chat refusals do not persist in the canonical 384-char form.

## agent.subagent_spawns — 96 rows (1:1 with messages)

- First: epoch 1789370272 = 2026-09-14 07:17:52Z. Last: epoch 1789546982 = 2026-09-16 08:23:02Z.
- By day: 9/14: 1, 9/15: 24, 9/16: 71 — identical split to messages.
- By parent_agent_id (top): 7240686c: 25, ff521137: 19, 58246538: 11, 802811a3: 10, 0783c1d6: 10, ac045111: 9, f99a2d06: 4, 6f8a9be7: 4, 0693e1c3: 3, 5a4f76c0: 1.
- Includes spawn_ids 515–521 (this campaign, 08:22:56–08:23:03Z), all `status='completed'`.

## Interpretation

The canonical signature is a **spawn-handoff artifact exclusively**: every occurrence is a refused subagent spawn recorded on the subagent surface, 1:1 with a spawn row. It does not appear in main-chat message bodies in this form. The storm's observable footprint is the spawn layer, and the `completed` status on all 96 spawn rows is the projection bug wearing a pass.
