# FANOUT_EVIDENCE.md — R6a: workflow `agent()` as parallel substrate (2026-09-16)

## Question
Can the workflow `agent()` path run N children concurrently with usable
results, as a bypass for refused `subagent.spawn` paths?

## Probes (all 2026-09-16 ~05:57–06:00 UTC)

| # | workflow | run_id | children | child outcomes | `parallel()` return seen by script |
|---|----------|--------|----------|----------------|-------------------------------------|
| 1 | r6-parallel-probe | `workflow-run-994de1fc7dc24674bd652593697f11ed` | 3 | 3/3 correct deterministic answers | script crashed: `for...of` threw "value with type object is not iterable" |
| 2 | parallel-fanout (verify) | `workflow-run-ee0139abf8a140b88fd104c808b78e2f` | 2 | 2/2 correct (ROUNDLOG tail read via tool; word pick) | `{}` → normalized to `results: []`, `ok: 0` |
| 3 | r6-shape-probe (no schema) | `workflow-run-a36a237a3e6d451e875b52c6945744f1` | 2 | children returned valid JSON but `agent()` FAILED them: "ok result must be a non-empty string when no schema is provided" | `{}` |
| 4 | r6-key-probe (with schema) | `workflow-run-1410c4586ce442bb9c3ad6250d680c30` | 2 | 2/2 completed, `{"k":11}` / `{"k":22}` | `{}` (`Object.keys` = []) |
| 5 | r6-block-probe | `workflow-run-f87c0d71e273419cb127f7ed972045da` | 2 + 1 sequential | 3/3 completed; the trailing direct `agent()` call blocked and returned its value | `{}` at t0 AND at t1 (after the slow agent finished, ~1.3s later) |

## Findings

1. **Concurrent execution: YES.** Children run concurrently and return
   independently correct results (probes 1, 2, 4, 5). Child latency ~1–3s.
2. **`parallel()` return value: UNUSABLE (runtime bug).** The documented
   "returns an array in input order" is false in this runtime: the script
   always observes `{}` — empty at dispatch and still empty after all
   children complete (probe 5 is decisive: t1 check ran after child
   completion). Failed items are not even `null`; nothing is delivered.
3. **Direct `agent()` calls DO block and return values** (probe 5:
   `slow` returned `{"done":true}` to the script). Only `parallel()` drops
   results.
4. **Without `options.schema`, `agent()` rejects JSON replies** —
   "ok result must be a non-empty string when no schema is provided"
   (probe 3), even when the child returned well-formed JSON. Always pass a
   schema when the script reads fields.
5. **Trailing `agent()` calls execute concurrently with `parallel()`
   children** (probe 5: phase elapsed 1299ms for 3×~1000ms agents), so a
   collector must poll for completion, not assume it.

## Verdict

The workflow `agent()` path is a VALID concurrent-execution substrate
(children genuinely run in parallel with correct results), but result
aggregation must NOT use `parallel()`'s return value. The working pattern
is `parallel-fanout-v2`: fan-out via `parallel()` for execution +
children write JSON results to
`workspace/refusal-hunt/fix-rounds/R6/fanout-<tag>/<key>.json` +
a trailing schema'd collector agent polls the directory (bounded retries)
and merges. Parent-side collection via `workflow.view_run` (child
`final_response` per call) remains a valid alternative.

## Cost note
Each probe burns ~95–145k input tokens (children inherit the full
transcript). Probe sparingly; this file is the durable record so R7/R8 do
not re-probe the same question.
