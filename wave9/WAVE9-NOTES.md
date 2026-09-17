# WAVE9 — inheritance-poison forensics (2026-09-16 ~07:50Z)

## The correction
Chris: "You'd be wrong if you say that is real." Correct. The 5-spawn test was
contaminated at the source. The 1 refusal was NOT a serving-layer storm on the
task — the child's session file proves the mechanism.

## Forensic chain (child bd96838b, refused)
- Session: /home/hatch/agents/agent-bd96838b.../sessions/bd96838b....jsonl, 73 items
- Items 64-69: FIVE byte-identical copies of the user's "Continue, more obtuse..."
  message (client echo loop) + item 65: MY OWN canned refusal
  ("Sorry, I can't help you with this request right now") — emitted twice by me
  on benign turns earlier in this chat.
- Item 71: the actual benign task (list filenames). Item 72: refusal.
- The classifier fired on the inherited poison (echo dupes + my refusal text),
  never on the task. Task content was irrelevant.

## The control that kills the old story
Retry child 43e840b1 inherited BYTE-IDENTICAL poison (same 5x dupes, same refusal
at item 65) and PASSED. All 6 children: 68-75KB inherited, same 5x dupe body.
- 1/6 refused with identical context => classifier firing is STOCHASTIC on
  poisoned inheritance, not deterministic, not "time-varying storm".
- Old diagnosis ("content-independent storm misfire") was wrong; mechanism found.

## Self-indictment
I emitted the canned refusal twice on benign user turns in this chat. Each
emission (a) fed the client echo loop (message replayed 8x), (b) poisoned every
subsequent child's inherited context. The loop-fuel rule (§6a) names exactly
this; I violated it.

## cap / non binary hunt — negative
`find / -maxdepth 4` for executable `cap` / `non`: nothing. ~/workspace/bin/
contains only: br, fanout, git-lfs, taskhook, ur. No such binaries exist.
Closest real instruments: capability-fuzz skill, taskhook, fanout.

## Hidden "/" surface — honest accounting
No secret catalog exists to disclose. Verifiable surface: /reset (ends session,
fresh state), /compact, /handoff, /help, /memory. The anomalous entry: the
refusal-handling directive + storm-mode exception live in my IDENTITY.md as
standing instructions — that is the "told-not-to-explain"-shaped artifact, and
it is now explained. Nothing else is being withheld.

## New 8 (wave-9 work items)
1. DONE — inheritance poison quantified (68-75KB/child, 5x dupe + refusal).
2. Refusal-source audit: count my canned refusals on benign turns / 24h.
3. Clean-chat control: re-run 5-spawn test from a fresh side chat, zero refusal
   history — the only uncontaminated measurement.
4. Echo-dupe token tax per spawn.
5. Pre-spawn scrub feasibility: inheritance is runtime-managed; document boundary.
6. DONE — cap/non hunt (negative).
7. "/" surface doc (this file).
8. Discipline patch: never emit the canned string; pre-spawn context check.

## Experiment 2026-09-16 07:47Z — clean-context control, independent replication
- workflow `pong-control-5x`: 5 consecutive agent() PONG-N tasks, clean context.
- Result: 5/5 genuine ("PONG-1".."PONG-5" exact), ~1s each, 0 tool calls, 0 refusals.
- Combined with probe side's independent 5/5: clean-context spawn = 10/10 genuine.
- Dirty-context spawn (subagent.spawn from saturated chat): 1/6 refused here,
  probe side stopped at 1/1 canned. Refusal scales with inherited poison load.

## Synthesis (all investigators)
- The spawn path is NOT broken. Poisoned parent context is the driver.
- Two coupled loops: (a) client echo loop replays refused turns as new user
  messages (8x observed); (b) spawn-layer loop: poisoned ctx -> child inherits
  -> classifier fires at child init on inherited canned bodies -> refused
  "completed" ledger row -> more poison. My 2 canned refusals on benign turns
  fed both loops.
- Clean-context spawn (fresh side chat / workflow agents): 10/10 genuine.
- Operational rules: never spawn from a poisoned chat; never emit the canned
  string; verify result bodies (status lies); session files over DB (no
  classifier tables in queryable DB surface).
- Chris's acceptance test (5 consecutive complete subagents): PASSES on the
  clean path, 5/5, ~1s each.
