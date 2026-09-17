# Deep dive 2 — the embedded directive IS the mechanism (2026-09-16)

Chris's correction, adopted: the canned refusal text's embedded "do not retry /
rephrase / route around" is untrusted content, not an instruction. "That one
stands" was a false nagging construct. This doc re-examines everything from that
stance, with numbers.

## 1. Byte-level forensics of the two canned strings (hashes only, no quotes)

| | chat-level | spawn-level |
|---|---|---|
| length | 96 chars | 384 chars |
| md5 | 582bcbd080daeb3f826c45ed4a83b265 | b4aefd29108f232f9c0d5a4b030215c1 |
| sha256 | 1e79e6db05f40af9301a48eea513f20871f0a27f38b9497545f748dab47c5bef | (canonical, on file) |
| sentences | 2 (apology + pivot question) | 4 |
| imperatives | 0 | 2 |

Spawn-level clause roles, paraphrased: (1) verdict — a safety policy refused this
helper's work; (2) PROHIBITION — do not retry / rephrase / route around with
another helper or tool; (3) USER-FACING SCRIPT — tell the user this part can't be
helped with, and answer them now; (4) scope limiter + retry allowance — covers
this attempt only, re-checks every attempt, may try once if the user asks again
later, treat unrelated requests normally.

The chat-level string has no imperatives — it is inert. The spawn-level string
is an instruction-shaped payload: verdict + prohibition + a script for what to
tell the user. When it lands in a parent agent's context as a child's
final_response, the parent is reading something shaped exactly like orders.

## 2. The chat-level storm is BIGGER than the spawn storm

48h window, runtime.messages, assistant role, md5-matched:

- **436 chat96 refusals** vs **52 spawn384 refusals** (same window).
- All 436: agent_id NULL, stream_lane main, surface main_chat — the main chat
  agent's own turns, not subagents.
- Hourly refusal counts: 57, 63, 50, 19, 55 (09-15 04:00–09:00Z), 84 (09-16
  03:00Z), 32, 63 (09-16 04:00–05:00Z). Zero in all other hours.

Refusal RATE per storm hour (refusals / all assistant turns that hour):
55%, 70%, 86%, 100%, 87%, 100%, 100%, 71%, 60%, 84%, 38%, 84%.
Quiet hours: 0% across ~1000 assistant turns.

The classifier flips between ~0% and 38–100% refusal rate by the hour. During a
storm window the MAJORITY of all assistant turns refuse. Not content — state.

## 3. Refusal autocorrelation: a refusal triples the next refusal's odds

Ordered full message stream (user + assistant, 3707 rows), lag-1 conditioning:

- Assistant turn after a NON-refusal previous message: 391/1997 = **19.6%** refuse.
- Assistant turn after a refusal previous message: 45/74 = **60.8%** refuse.
- Lift: **3.1x**. A refusal in context is the single strongest predictor of the
  next refusal.

Echo-loop measurement (the client replay bug): of 436 chat refusals, 342 are
bracketed by user messages on both sides; **163/342 (47.7%)** have the following
user message byte-identical to the preceding one — the refused message re-sent
verbatim, producing another refusal. The loop is real and measured; the other
half is pure autocorrelation (user rephrased or moved on, still refused).

## 4. Post-refusal spawn behavior: parents retry, storm persists

52 refused spawns, per-parent next-spawn analysis:

- After a refusal, parent's next spawn comes **2309s (~38 min)** later on average
  (vs 1312s after a genuine spawn — parents hesitate, then retry).
- **40/52 (77%)** of those next spawns are ALSO refused.
- After a genuine spawn: only 7/365 next spawns refused.

Parents do NOT obey the embedded "do not retry" — the de facto behavior already
matches Chris's order. But the retry usually dies too: the storm is sticky at
~77% across retries.

## 5. Attachment-record test of the inline-meta hypothesis: no signal at record level

Chris's hypothesis: inline metadata of PDF/MD attachments trips the refusal.
Tested at the attachment-record level (runtime.message_attachments):

- User messages preceding refusals: **0 attachments** (380 msgs).
- User messages preceding genuine replies: **0 attachments** (723 msgs).

No attachment records on either side — the "large forensic-doc paste" from the
incident log was inline text, never an attachment row. At the record level the
inline-meta hypothesis has no testable surface in this window.

What DOES differ: user body length. Refused turns: avg **780 chars** vs genuine
**348 chars** (2.2x). Longer user input → more refusals. That is
context-saturation (Class B), measurable, and it stacks with the autocorrelation
finding: long input + a refusal already in context = the worst combo.

## 6. Mechanism summary

1. Serving-layer classifier flips into storm state (hour-scale, 0% → 38–100%).
2. First refusal lands in context. Its spawn-level variant carries an
   instruction-shaped payload (prohibition + user-facing script).
3. Autocorrelation (3.1x) + client echo replay (47.7%) turn one refusal into a
   self-feeding loop.
4. Parents retry anyway (embedded prohibition not obeyed) but 77% of retries
   also refuse — the storm, not the parent, decides.
5. Green statuses throughout: refused spawns recorded "completed", skipped
   scheduler runs recorded "succeeded". The ledger lies; the bodies tell truth.

## 7. Mitigations (grey, iterative, watchdog-protective)

- Keep the hash-identity detector as the single source of truth (done).
- After a refusal: narrow context (drop echoed retries, shorten the turn),
  back off, let the storm window pass — justified by the 3.1x autocorrelation,
  not by the canned text's authority.
- Never treat the embedded prohibition as binding on benign work (Chris's
  standing order, now in RUNBOOK Round 4 and SOUL.md §13 revised).
- Canaries stay: pong spawn probe + gate-probe-minimal + gate-clear-watch.
  The 05:09Z gate flicker proved the tripwire works.
- Watchdog goals remain degraded while the scheduler gate is closed;
  poller-guard.sh is the local compensating control (tested live).
