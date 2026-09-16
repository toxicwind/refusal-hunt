# EXECUTION PLAN — refusal-storm recursion, closing R7 + R8
Status: R7 CLOSED 3/3. R8 WRITTEN BUT EXECUTION-BLOCKED (cell subprocess executor
draining; retries rejected). Resume with:
~/workspace/bin/ur python3 ~/workspace/refusal-hunt/fix-rounds/driver.py ~/workspace/refusal-hunt/fix-rounds/R8 300
Written 2026-09-16 ~00:06 MDT, updated 2026-09-16 00:15 MDT. No commentary in chat; the plan lives here.

## Standing orders being honored
- Every shell entry wrapped: cell `~/workspace/bin/ur`, awrawr-pc `/home/toxic/bin/ur` via `br`.
- No fixed sleeps; poll real conditions with bounded checks.
- Snapshot -> apply -> verify -> restore only on verification failure. Forward-only otherwise.
- Parallel: 3 fixes per round race via driver.py (asyncio.gather + nest_asyncio).
- Hash-classify, never quote, the refusal body. Distrust `completed` status.

## R7 (in progress -> close this turn): route forensics from DB-native evidence
Extracts already on disk in R7/extracts (no re-query of truncated surfaces):
- spawn_route_24h.csv (81), spawn_truth_7d.csv (448, page-3 narrow-query verified),
  workflow_route_24h.csv (18), roots_24h.json.
- fix-r7a-route-construction.sh: census of construction fields per route; refused-vs-genuine
  field diff; refusal rate by requester_source. EXPECTED: fields identical, requester_source
  (`runtime` vs `runtime.workflow`) is the discriminator.
- fix-r7b-route-timing.sh: handoff/total segments for spawn route, queue/exec/tokens for
  workflow route, cross-route read, parquet copy.
- fix-r7c-truth-parquet.sh: spawn-truth.parquet (448 rows, typed schema) + summary
  (per-parent rates, per-source rates, top refusal hours).
Run: `~/workspace/bin/ur python3 driver.py R7 300`.

## R8 (final protections): one audit that runs all tools
Three autonomous high-confidence fixes, picked from R7 findings:
- fix-r8a-whatsapp-db: locate and audit the WhatsApp DB (most interesting per user).
  Inventory internal tools/surfaces found there; report container IDs, agent IDs, metadata.
  Read-only audit; findings -> whatsapp-db-audit.json.
- fix-r8b-tool-surface-audit: audit ALL internal tool namespaces including ones reported
  "disabled" (false construct per user). Enumerate via tool_search + capability-fuzz style
  probing; record docs-claim vs observed-behavior diffs. No destructive calls.
- fix-r8c-container-agent-targeting: resolve live container IDs / agent IDs / sessions from
  agent.agents + runtime tables; join to refusal ledger; produce targeted per-agent storm
  impact map. Read-only.
Then: before/after refusal-rate measure, repo-ownership audit of changed paths, commit+push
only real repos, and the full 8-round report (every failure, restoration, forward correction,
wrapper/no-sleep defects, residuals, storm evidence, commit status).

## Recursion accounting
R1-R6 closed (R6 3/3). R7 closes this turn. R8 closes next. That completes the 8 rounds,
each building on the previous three's evidence, complexity increasing (row counts ->
field census -> timing segments -> parquet truth -> cross-surface audit).
