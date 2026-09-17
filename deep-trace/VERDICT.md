# Deep-trace verdict: does PostgreSQL observe the safety decision point?

Date: 2026-09-17 ~10:05 UTC. Evidence: `refusal-events-24h.parquet` (200 rows, zstd, no verbatim bodies).

## Short answer

**No. The DB is complete and faithful, but we are not MITMing the decision tier.**
PostgreSQL observes the refusal *injection* with perfect fidelity — every event,
timestamp, agent, request lineage — and records **zero bytes of the decision
itself**. The verdict happens upstream; the DB only ever sees the substitution.

## The DB is NOT failing

Verified 2026-09-17 ~10:00-10:05 UTC via `muse.db` (internal DB tool):

- All 4 deep-trace refusals (agents a33aeb6f, 5c646ea5, d68b5afe, 943af97a,
  10:00:18-10:00:21 UTC) are present as message rows AND event rows, with
  matching agent IDs, shared root `req:fallback:4ed66600-b32b-437f-bb43-01f6ff3baeeb`,
  payload lengths, and timestamps.
- 41 messages with the 384-char digest (md5 b4aefd29108f232f9c0d5a4b030215c1)
  in the trailing 24h; every one joined to its event row. No orphans observed.
- The full lifecycle is visible: context-inheritance events (12,582-byte
  payloads, eseq 33669-33672, 10:00:18.792-10:00:19.842) followed ~2s later by
  the 707-byte refusal injections (eseq 33674-33677, 10:00:20.680-10:00:21.804).
- `agent.subagent_spawns` for all 4 refused agents: status='completed',
  final_response = 384-char canned body (digest-verified), created->completed
  in 2-3s, deferred_terminal_status NULL. The Completed-bug is confirmed at
  the spawn-record layer, not just the agent-status layer.

## What the refusal payload actually contains (full, untruncated)

Dumped in full via `muse.db` (eseq 33677). Fields:

- `channel_context`: chat_kind, device_id (9d61bc1f6c96ea07 — the Android device),
  event_kind, originating_channel=main, require_mention
- `content`: the canned body (digest/length only, never quoted)
- `message_id`, `metadata: {context_seq: 4359, message_kind: "message"}`,
  `role: "assistant"`, `source: "runtime"`

What is **absent**: no score, no classifier name/version, no model or tier
marker, no policy label, no decision timestamp, no reason code. Nothing that
distinguishes "a model refused" from "a gate substituted the body".

The 96-char main-lane variant additionally carries `"status": "completed"`,
`started_at_ms`, `can_broadcast_share: true` — the shape of a completed model
turn, wrapped by runtime. The 384-char subagent variant carries no status field
and is stored as role='system' while its payload claims role='assistant'.

## Corrections to earlier hypotheses

1. **provider_message_id NULL is NOT distinctive.** 1,854 assistant messages in
   24h; 0 have a provider message ID. The column is simply never populated in
   this DB. It cannot prove a model was or wasn't consulted.
2. **agent.token_usage cannot test "no model was consulted."** Zero rows in the
   trailing 24h for ALL agents — including C and D, which did verified real
   tool work. The table is unpopulated in this window; absence means nothing.
3. **No classifier table exists.** Full schema grep (195 tables): the only
   "verdict"/"policy" tables are `feed.prompt_scope_verdict` (singleton row,
   feed prompt scoping) and `ideas.explore_policy` — both unrelated to safety.
   There is no moderation/classifier/safety/gateway table anywhere in the
   exposed schema.

## What the DB *does* give us (the real MITM surface)

The DB is a perfect downstream observer of the substitution, which makes it a
usable black-box probe of the gate:

- `metadata.context_seq` pinpoints the exact context sequence where the gate
  fired (4359 for the whole 4-copy cohort).
- Inherited-context events carry the full parent context payloads; combined
  with session-file digests they identify exactly what content the gate saw.
- Request lineage (`req:fallback:*` roots) groups correlated outcomes:
  4/4 refused sharing one root vs 2/2 split in the 09:52 cohort with
  byte-identical inherited context. Sibling outcomes correlate by fallback
  batch — the gate's verdict is per-request-context, stochastic, not
  content-deterministic.
- Spawn->refusal latency: 2-3s, consistent with an inline gate on the spawn
  path, not an async moderation callback.

## Conclusion

PostgreSQL is a faithful ledger of refusal *effects*, not a window into the
decision. The audit was targeting the persistence tier; the decision tier sits
upstream (serving path, unreachable from this container:
`/run/hatch/{proxy,sentinel,safety}` absent). The productive MITM is the one we
already run: controlled black-box probing — vary inherited context, measure
refusal rate per fallback root, correlate via context_seq — because the gate's
transfer function is the only observable we have, and the DB records it
completely.
