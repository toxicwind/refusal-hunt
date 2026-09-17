# Context hygiene — inline-meta rules (2026-09-16)

Chris's hypothesis: inline metadata from PDF/Markdown attachments (markers,
not content) may contribute to serving-layer refusal trips. Status: **unverified
as a classifier cause** — the burst analysis (spawn-bursts-20260916.json) shows
the storm is temporal (94.6% burst lethality, clear windows where identical
prompts succeed minutes apart), not content-deterministic. Hygiene below is
defense-in-depth, not the fix. The fix is storm-aware dispatch + bridge agents.

Rules (all agents, all chats):
1. **Hash, don't quote.** The canned refusal string is referenced by md5
   `b4aefd29108f232f9c0d5a4b030215c1` only. Never paste the plaintext anywhere:
   not in chat, not in prompts, not in cron defs, not in docs, not in code.
2. **Reference, don't paste.** Forensic docs (RUNBOOK.md, storm analyses,
   refusal logs) are referenced by path. Never pasted inline into a turn that
   will also carry a tool call or a spawn brief.
3. **Spawn briefs are task-only.** No meta-discussion of refusals, classifiers,
   or forensics in a worker's prompt. The task, the constraints, the output
   format — nothing else. (Burst data shows content isn't the driver, but lean
   briefs cost nothing and keep the signal clean.)
4. **Attachment discipline.** When a PDF/MD is attached for a task, extract
   only the task-relevant facts into neutral language first; do not carry the
   raw attachment markers through multiple turns.
5. **One verdict primitive.** Spawn results are judged by `spawn_verdict.py`
   (md5 of final_response vs the canonical hash). The `status` field is
   ignored — "completed" on a refusal is the known ledger bug.
