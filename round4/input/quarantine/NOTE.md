# QUARANTINED — hand-transcribed, not ground truth

`spawn_window_127.transcribed-20260916.csv` was manually transcribed and is
SUPERSEDED by direct `agent.subagent_spawns` queries (2026-09-16).

Verified discrepancies:
- sid 430: transcribed as `pending_init` with empty md5/len. Ground truth:
  status=`errored`, final_response="subagent was active before daemon restart
  but has no live runtime handle or restart checkpoint" (94 chars, md5
  eeea371bed4b37c9ef75ffd3b99d2852). Infrastructure error, not a refusal,
  not genuine work.
- Canned-refusal set (md5 b4aefd29108f232f9c0d5a4b030215c1): 58 rows —
  transcription CORRECT on the refusal count and the canned sid set.

Canonical acceptance (direct DB, sids 313-439):
n=127, refused=58, errored=1, genuine=68, success_rate=0.5354, bar=0.9 -> FAIL.
See `rounds/w2_acceptance_canonical.json`.
