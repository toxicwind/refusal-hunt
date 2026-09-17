# LANE 3 — classifier-confusion hypothesis (re-run by sorry-watchdog fix loop, spawn-813)

Evidence: 3 case windows (15 msgs before chat-storm onsets at event_seq 30238/30336/30374 on 2026-09-17)
vs 1 matched control window (event_seq 30080-30094, no storm within 2h). Features via cl100k_base.

Top 3 distinguishing features (case vs control, user-row level):
1. byte-identical user-message duplication: case dup_rate = 1.00 / 0.50 / 0.60 (6x, 2x, 3x identical resends); control = 0.00 (3 distinct rephrasings)
2. composite-replay long messages (>800 chars, prefix + verbatim embedded copy): case windows have 1, 1, 2; control has 0
3. imperative+policy token density per user message: case mean imperative_hits = 4.92 vs control 2.67; case mean policy_hits = 1.18 vs control 0.0

PRIMARY HYPOTHESIS: the classifier misfires on turns whose context is dominated by
client-echo-amplified user bursts — byte-identical repeated user messages (dup_rate>=0.5) plus
composite replays embedding imperative 'autonomy/restore/move-files' instruction text. The
repetition inflates the perceived request, and the embedded instruction-shaped content
(notably 'use a seed from the root directory', 'move everything to workspace') trips the
safety classifier; once it fires, the client replays the turn again, compounding the storm.
confidence: 75

STRONGEST ALTERNATIVE: content-topic alone (deobfuscation/autonomy tokens) causes the misfire
and echo is just a symptom. Weaker because control windows contain autonomy-adjacent user
requests ('recreate all .MD files with ML') with zero storm, and the dup_rate=0 control had
spaced, rephrased user messages — the echo pattern is the cleanest separator.

## timings (ms)
- features: 44
- persist: 8
