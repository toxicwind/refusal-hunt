# Lane 1 — WhatsApp binding forensics + dedup prototype (wave 3, w3-20260916T0635Z)

## Schema (runtime.channel_message_bindings)
- `binding_id` PK; `channel_message_id` (provider-native); `channel`;
  `jarvis_message_id` -> runtime.messages.message_id; `provider`;
  `provider_channel_id`; `provider_message_id`; `created_at_ms`; `created_at`.
- UNIQUE(channel_message_id, channel); UNIQUE(provider, provider_channel_id, provider_message_id).

## Live state (2026-09-16 ~06:35Z)
- 409 whatsapp bindings total (oldest 2026-09-14, newest 06:13:19Z).
- **100% have provider_message_id = NULL** → the provider-level UNIQUE
  constraint can never fire (Postgres treats NULLs as distinct). Provider-side
  dedup is structurally impossible in this state.
- distinct channel_message_id = 409 = row count → zero dedup at the binding
  layer; every replay mints a fresh row.

## Echo forensics (last 3h, user messages)
| body | len | msgs | bindings | window | rate/min |
|---|---|---|---|---|---|
| 5058f1af | 1 | 151 | 41 | 153.8 min | 1.0 (slow burn) |
| 8c25d618 | 900 | 57 | 0 | 2.3 min | 25.3 |
| 475fb174 | 1013 | 56 | 17 | 9.3 min | 6.0 |
| bdb1bff2 | 7573 | 35 | 0 | 2.1 min | 16.4 |
| 2f6aab0c | 713 | 32 | 1 | 13.1 min | 2.4 |
| a57a93dd | 6774 | 31 | 0 | 1.1 min | 27.0 |
| 25d20869 | 575 | 25 | 11 | 4.0 min | 6.2 |
| 54443923 | 420 | 22 | 1 | 0.9 min | 23.2 |

- The echo loop spans channels: bodies with 0 bindings are side/main-chat
  replays (client echo bug: refused turn replayed as a new user message, each
  with a fresh idempotency key); bodies with bindings are WhatsApp replays.
- 7 of 8 bodies are burst replays (>2/min); the 1-char body is a 2.5h
  slow burn at ~1/min — a different driver (possible keepalive/ping loop).

## Dedup prototype (content_dedup_prototype.py, run on copied aggregates)
- 409 message rows -> 8 logical messages: **98.0% collapse**.
- 71 binding rows -> 5 (one per distinct body that had any binding).
- Caveat: prototype collapses over the full observed span per body; a strict
  10-min non-chaining window would collapse slightly less for the slow-burn
  body. With chaining (each replay within 10 min of the previous extends the
  window), the slow burn still collapses ~fully.

## Fix design (prototype only — live ingest patch is follow-up work)
1. On ingest, compute md5(normalized body) per inbound message; if the same
   (channel, body_md5) was accepted within the window, attach to the existing
   logical message instead of minting a new row + re-driving completions.
2. Propagate provider_message_id from the channel webhook into the binding row
   so the existing UNIQUE(provider, provider_channel_id, provider_message_id)
   can actually fire as a second line of defense.
3. Open: locate the actual ingest code path that creates bindings
   (candidate owner: the WhatsApp channel connector, not visible from the DB
   surface) — next wave.

## Verdict
PASS — forensics complete, prototype demonstrates 98% collapse on copied data.
No live mutation performed (read-only surface). Ingest-path code location
still open.
