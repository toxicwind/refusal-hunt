# Fix rounds rollback log

Started 2026-09-16T05:52Z. Every fix: snapshot -> apply -> verify -> rollback on fail.

## 2026-09-16T05:51:18Z UTC - round R1: 2/3 PASS in 35.4s (parallel, nest_asyncio=False)
- fix-R1a-sleep-event-waits.sh: PASS (rc=0, 35.4s)
- fix-R1b-fleet-backoff-directive.sh: FAIL (rc=1, 3.0s)
- fix-R1c-canary-refire.sh: PASS (rc=0, 2.5s)

## 2026-09-16T05:54:25Z UTC - round R2: 3/3 PASS in 1.9s (parallel, nest_asyncio=True)
- fix-R2a.sh: PASS (rc=0, 1.9s)
- fix-R2b.sh: PASS (rc=0, 0.2s)
- fix-R2c.sh: PASS (rc=0, 0.1s)

## 2026-09-16T05:54:51Z UTC - round R3: 1/3 PASS in 0.3s (parallel, nest_asyncio=True)
- fix-R3a.sh: FAIL (rc=1, 0.3s)
- fix-R3b.sh: PASS (rc=0, 0.0s)
- fix-R3c.sh: FAIL (rc=1, 0.0s)

## 2026-09-16T05:55:18Z UTC - round R4: 2/3 PASS in 0.3s (parallel, nest_asyncio=True)
- fix-R4a.sh: FAIL (rc=1, 0.3s)
- fix-R4b.sh: PASS (rc=0, 0.1s)
- fix-R4c.sh: PASS (rc=0, 0.1s)

## 2026-09-16T05:55:43Z UTC - round R5: 3/3 PASS in 0.6s (parallel, nest_asyncio=True)
- fix-R5a.sh: PASS (rc=0, 0.4s)
- fix-R5b.sh: PASS (rc=0, 0.0s)
- fix-R5c.sh: PASS (rc=0, 0.6s)

## 2026-09-16T06:00:49Z UTC - round R6: 2/3 PASS in 6.2s (parallel, nest_asyncio=True)
- fix-r6a-workflow-fanout.sh: FAIL (rc=1, 0.3s)
- fix-r6b-identity-router.sh: PASS (rc=0, 0.2s)
- fix-r6c-orchestrator-race.sh: PASS (rc=0, 6.2s)

## 2026-09-16T06:01:31Z UTC - round R6 forward-fix: 3/3 PASS
- fix-r6a-workflow-fanout.sh: initial FAIL was a bad verify (node --check rejects the workflow DSL top-level return); fixed verify to DSL-wrap before node --check. Re-ran: PASS (template parses, 5-probe evidence verified). parallel-fanout-v2 registered as saved workflow; live validation run workflow-run-728e2579ed634d69b1ad9621c6231f10 in flight.
- fix-r6b-identity-router.sh: PASS (rc=0) — identity-router.json, fleet 65/53, 8 parents, verdict NO_CLEAN_IDENTITY.
- fix-r6c-orchestrator-race.sh: PASS after fixing br invocation (br is bash, was mis-called via python3) and pip index arg loop. Full survey: anyio/trio/uvloop installable; awrawr-pc has GNU parallel 20260722 + go1.26.5; remote GNU parallel 3-leg 102ms. Race winner flipped run-to-run (processes then threads, margins <0.2s) — no dominant orchestrator; asyncio stays the pragmatic default, fanout binary the zero-dep portable option.

## 2026-09-16T06:03:08Z UTC - round R6 CLOSED: 3/3 PASS (all verified)
- R6a parallel-fanout-v2: clean end-to-end validation run workflow-run-f2811569471a496097f175446f0e0f67 COMPLETED — 2/2 fan-out children concurrent (alpha 2s, beta 6s), both correct, both wrote JSON files, collector polled and merged ok=2/total=2. Earlier v2verify run showed 1/2 only because the test prompt forbade tool use (test-design flaw, not template defect).
- R6b identity-router.json: fleet 65 spawns / 53 refused across 8 parents, verdict NO_CLEAN_IDENTITY — confirms storm is platform-wide, not parent-specific.
- R6c orchestrator race: winner flips run-to-run (processes 1.149s, then threads 1.535s; margins <0.2s) — no dominant orchestrator; asyncio stays the pragmatic default, compiled fanout binary the zero-dep portable option. Full survey: anyio/trio/uvloop installable; awrawr-pc GNU parallel 20260722 + go1.26.5; remote GNU parallel 3-leg 102ms.
- Process defects this round: (1) R6a initial FAIL was a bad verify (node --check rejects workflow-DSL top-level return) — fixed forward with DSL-wrap. (2) R6c mis-invoked br via python3 (it is bash) — fixed forward. (3) A shell wait loop used fixed sleep 3 — violates no-sleep rule; poll run status via workflow.view_run instead.
- Storm rate: 05:45 bucket final 89 refusals; 06:00 bucket 8 in first ~3 min (~2.7/min vs 5.9/min peak) — still elevated, declining.

## 2026-09-16T06:05:41Z UTC - round R7: 1/3 PASS in 1.6s (parallel, nest_asyncio=True)
- fix-r7a-route-construction.sh: FAIL (rc=1, 0.1s)
- fix-r7b-route-timing.sh: FAIL (rc=1, 0.1s)
- fix-r7c-truth-parquet.sh: PASS (rc=0, 1.6s)

## 2026-09-16T06:05:48Z UTC - round R7: 3/3 PASS in 1.9s (parallel, nest_asyncio=True)
- fix-r7a-route-construction.sh: PASS (rc=0, 0.3s)
- fix-r7b-route-timing.sh: PASS (rc=0, 1.9s)
- fix-r7c-truth-parquet.sh: PASS (rc=0, 1.8s)

## 2026-09-16T06:12:00Z UTC - round R7: 3/3 PASS in 1.9s (parallel, nest_asyncio=True)
- fix-r7a-route-construction.sh: PASS after forward correction (initial FAIL: KeyError 'classification' - spawn_route_24h.csv lacks the column; fixed by joining classification from spawn_truth_7d.csv on spawn_id). Finding: refused vs genuine construction IDENTICAL (zero field diffs); discriminator is requester_source: runtime 59/430 refused (13.7%), runtime.workflow 0/18 refused.
- fix-r7b-route-timing.sh: PASS after same forward correction. Refused spawns complete in ~1s (serving-path reject, not timeout). Workflow children: exec median seconds, token-heavy (max 308k total tokens on v2 collector).
- fix-r7c-truth-parquet.sh: PASS first try. spawn-truth.parquet 448 rows, typed schema, round-trip verified.
## 2026-09-16T06:15:00Z UTC - round R8: WRITTEN, execution BLOCKED
- fix-r8a-whatsapp-surface.sh, fix-r8b-tool-surface.sh, fix-r8c-agent-targeting.sh written to R8/ with extracts (namespace-probe.json: 27/27 namespaces load, 159 functions; agent-inventory.json: 6 live agents incl. stuck pending_init cee558b1).
- Driver invocation rejected: cell subprocess executor is draining ("rejecting new subprocess start"), persistent across retries. No exec, no br, no driver possible in this cell.
- Resume: ~/workspace/bin/ur python3 ~/workspace/refusal-hunt/fix-rounds/driver.py ~/workspace/refusal-hunt/fix-rounds/R8 300

## 2026-09-16T06:08:53Z UTC - round R8: 3/3 PASS in 8.2s (parallel, nest_asyncio=False)
- fix-r8a-whatsapp-surface.sh: PASS (rc=0, 8.2s)
- fix-r8b-tool-surface.sh: PASS (rc=0, 0.4s)
- fix-r8c-agent-targeting.sh: PASS (rc=0, 5.2s)
