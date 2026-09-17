# Wave 17 — WhatsApp/database correlation, schema-first (2026-09-16 09:05 UTC)

No message secrets or credentials touched. No message bodies read.

## Database side
- The `muse_db` schema guide contains **no WhatsApp tables** — WhatsApp state is not projected into the queryable ledger schemas.
- All 96 canonical storm-digest rows in `runtime.messages` sit on `transcript_surface='subagent'` (wave 11). Zero digest rows on any WhatsApp surface. The storm has no observable WhatsApp footprint.

## Channel side (`~/channels/whatsapp/`)
- `cursor.json`: `{"last_rowid":288,"stefi_next_seq_id":"289","stefi_last_local_rowid":288}`, updated 02:28 container-local (= 08:28 UTC) — the daemon is alive and polling within the last minutes.
- `wa_identity_sync.json` (7.5 KB, updated 02:30): identity sync state only, no message content.
- `store/`: empty — no local plaintext message archive.
- `/run/hatch/whatsapp-keyd/keyd.sock` exists (wave 14) with no visible owning PID — key daemon lives across the namespace boundary.

## Correlation result
The refusal storm and the WhatsApp channel are disjoint in the observable data: no shared tables, no digest rows on WhatsApp surfaces, no local message store to leak. WhatsApp daemon liveness confirmed independently via cursor advancement. Nothing to patch; nothing exposed.
