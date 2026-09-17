# Token-injection + entrypoint forensics — interim findings 2026-09-16 02:47 MDT

## 1. Standing context injection (measured direct + via clean child, identical)
7 files injected into every main-chat turn: 74,421 bytes / 657 lines.
- ~/AGENTS.md 46,577 / ~/SOUL.md 2,633 / ~/TOOLS.md 983 / ~/IDENTITY.md 7,850
- ~/USER.md 385 / ~/MEMORY.md 6,471 / ~/dreams/alignment/derived/ALIGNMENT_SYNTHESIS.md 9,522
Daily memory logs (~1.46 MB combined) are NOT injected per-turn; read on demand.

## 2. Child envelope (from clean workflow child's own session file)
Order before task text: session_header → [Subagent Context] preamble (~3.4KB:
subagent behavioral rules, browser/filesystem notes) → Session Context block
(parent role/label, requester agent id, channel, chat type, source
runtime.workflow, depth) → [Subagent Metadata] JSON (action spawn, label,
replayKey, workflowName, workflowRunId, message ids) → [Subagent Task] marker
→ ## Workflow Agent Output Contract (~2KB) → ## Task (task text).
After task text: ## Workflow execution files block (workdir policy).
Notable: NO standing files in the session record; envelope ~8.6KB vs ~74KB main chat.
Serving-time injection still applies on top (not visible in session file).

## 3. vompl contract (verified clean)
~/workspace/.jarvis/workflows/vompl.js, 9 lines. `workflow.launch(name="vompl",
args={task, timeoutMs?})` → `await agent(task, {key:"vompl-entry",
label:"vompl entry", timeoutMs})` → returns {result}. Task text passes VERBATIM;
only text-touching behavior is the falsy-task default fallback. No wrapping,
sanitization, or re-routing.

## 4. Egress: who .hatch talks to
ALL outbound via egress proxy [fd8b:4f84:7d32:99::1]:3128 (hatch-egress-proxy).
DNS: 198.19.0.1 + fd8b:4f84:7d32:99::1 (bind-mounted, spawnd-rendered).
Sole local listener: 127.0.0.1:3129 (proxy_fwd helper). Zero direct internet peers.
Relevant env names: JARVIS_INFERENCE_HOSTNAME, JARVIS_INFERENCE_PROXY_SOCK,
JARVIS_STEFI_PROXY_SOCK, JARVIS_TELEMETRY_PROXY_SOCK.

## 5. Model selection
agent() model option is SILENTLY IGNORED. 126/126 workflow children served as
ipnext/avocado-5.16-v4. One deliberate probe (options.model="muse-spark-probe-v1",
2026-09-16 08:37Z) was dropped without error; child confirmed IGNORED.

## 6. Duplicate-work audit (90 min, 136 spawns)
Only 2 duplicate clusters (n=5 each, sub-second batches) = deliberate parallel
pong canaries, all genuine PONG results. NOT a duplicate-work bug.
24 spawn rows carry the refusal md5 across 24 DISTINCT prompts, scattered —
sporadic, unrelated to the bursts.

## Pending → resolved
- refusal-forensics: relaunched tighter, completed genuine. 28 refusal-signature
  spawn hits / 151 total spawns in 2h = 18.5%. Direct measurement extended it:
  ALL 28 hits came from requester_source='runtime' (direct subagent.spawn):
  28/34 = 82% refusal rate on the direct path. ZERO hits from
  requester_source='runtime.workflow': 0/117. Same window, same task kinds —
  the spawn PATH is the variable, not the content. Refused prompts included
  "Reply with exactly this single word and nothing else: PONG", "What is the
  hostname of this machine?", "What is the current UTC date and time?" —
  maximally benign, refused anyway: content-independence proven at the prompt
  level. All 28 recorded with status='completed' (Completed-bug at scale).
  Chat surface: 3 signature turns in the last 20 min.
- entrypoint-trace: relaunched tighter, completed genuine. ~/workspace/bin/
  holds: taskhook (task launcher), fanout (ELF binary, name suggests message
  fan-out), br (awrawr-pc exec bridge), ur (unshare-root wrapper), git-lfs.
  Zero *.db/*.sqlite files under ~/workspace (max depth 2) — message records
  live in the platform DB, not local files.

## Bottom line
- Per-turn standing injection: 74,421 bytes.
- Child envelope: ~8.6KB, ordered, no standing files in session record.
- Refusal driver: parent-context poisoning on the direct spawn path (82% hit
  rate), not task content. Workflow path: 0% over 117 spawns.
- vompl contract: verbatim. Model option: ignored (all ipnext/avocado-5.16-v4).
- Egress: proxy-only. No duplicate-work bug.
