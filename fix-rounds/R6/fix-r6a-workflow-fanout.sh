#!/usr/bin/env bash
# fix-r6a-workflow-fanout.sh — R6a: ship parallel-fanout-v2 (file-handoff collector)
# + FANOUT_EVIDENCE.md.
# Finding (5 probes, 2026-09-16): workflow agent() children execute CONCURRENTLY
# with correct results, but parallel()'s return value is unusable — the script
# always observes {} (documented "array in input order" is false in this
# runtime). Direct agent() calls DO block and return values. Without a schema,
# agent() rejects JSON replies. So v2 = parallel() for execution + children
# write JSON to fanout-<tag>/<key>.json + trailing collector agent merges.
# Additive only. Rollback: remove the two artifacts.
set -u
R=~/workspace/refusal-hunt/fix-rounds/R6
WFDIR=~/workspace/.jarvis/workflows
TPL=$R/parallel-fanout-v2.js
EV=$R/FANOUT_EVIDENCE.md
SNAP=$R/.snap-r6a

snapshot() {
  {
    echo "ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if test -f "$TPL"; then echo "tpl=$(sha256sum "$TPL" | cut -d' ' -f1)"; else echo "tpl=ABSENT"; fi
    if test -f "$EV"; then echo "ev=$(sha256sum "$EV" | cut -d' ' -f1)"; else echo "ev=ABSENT"; fi
    echo "workflows=$(ls "$WFDIR" 2>/dev/null | sort | tr '\n' ',' || echo NONE)"
  } > "$SNAP"
  echo "snapshot: $(cat "$SNAP" | tr '\n' ' ')"
}

write_tpl() {
  cat > "$TPL" <<'JSEOF'
export const meta = { name: "parallel-fanout-v2", description: "R6a: parallel fan-out with file-handoff result collection. parallel() executes children concurrently but its return value is unusable (runtime returns {} always; 5 probes 2026-09-16, see FANOUT_EVIDENCE.md). Children write JSON results to workspace/refusal-hunt/fix-rounds/R6/fanout-<tag>/<key>.json; a trailing collector agent merges them.", phases: ["fanout", "collect"] };

const inputs = args ?? {};
const items = Array.isArray(inputs.items) ? inputs.items : [];
const tag = inputs.tag || "untagged";
const outDir = "workspace/refusal-hunt/fix-rounds/R6/fanout-" + tag;
const keys = items.map(function (it) { return it.key; }).join(", ");

const itemSchema = { type: "object", properties: { key: { type: "string" }, ok: { type: "boolean" }, detail: { type: "string" } }, required: ["key", "ok"] };

phase("fanout");
const thunks = items.map(function (it) {
  return function () {
    return agent(
      "STRICT OUTPUT CONTRACT: reply with ONLY one JSON line and nothing else: " +
      "{\"status\":\"ok\",\"result\":{\"key\":\"" + it.key + "\",\"ok\":true,\"detail\":\"<one-line summary of what you did and the key evidence>\"}}. " +
      "Task: " + it.prompt + " " +
      "Then, using your file-write tool, write the inner result object (exactly {\"key\":...,\"ok\":...,\"detail\":...}) as JSON to " +
      outDir + "/" + it.key + ".json (create directories as needed). Both the reply and the file write are required.",
      { key: "fanout-" + tag + "-" + it.key, label: it.label || it.key, schema: itemSchema, timeoutMs: inputs.timeoutMs || 300000, phase: "fanout" });
  };
});
// NOTE: parallel() return deliberately ignored — runtime bug: it yields {} always,
// never the child results (probed 2026-09-16). Children run concurrently regardless.
parallel(thunks, { concurrency: inputs.concurrency || items.length || 1 });
log("fanout dispatched tag=" + tag + " n=" + items.length + " (parallel() return ignored: runtime bug, see FANOUT_EVIDENCE.md)");

phase("collect");
// The collector may start while fan-out children are still running (observed:
// trailing agent() calls execute concurrently with parallel() children), so it
// polls the result directory with bounded retries instead of assuming completion.
const mergeSchema = {
  type: "object",
  properties: {
    tag: { type: "string" },
    ok: { type: "number" },
    total: { type: "number" },
    results: { type: "array", items: { type: "object", properties: { key: { type: "string" }, ok: { type: "boolean" }, detail: { type: "string" } }, required: ["key", "ok"] } }
  },
  required: ["tag", "ok", "total", "results"]
};
const merged = agent(
  "You are the collector for parallel fan-out tag \"" + tag + "\". Expect " + items.length +
  " result files under " + outDir + "/ with keys: " + keys + ". " +
  "Poll with bounded retries (up to ~100s: re-list the directory each attempt, a few seconds apart — never sleep blindly) until every file exists with valid JSON {key,ok,detail}. " +
  "Reply with ONLY one JSON line: {\"status\":\"ok\",\"result\":{\"tag\":\"" + tag +
  "\",\"ok\":<number with ok true>,\"total\":" + items.length + ",\"results\":[<result objects in the key order above>]}}.",
  { key: "collect-" + tag, label: "fanout collector", schema: mergeSchema, timeoutMs: 180000, phase: "collect" });
log("collect done: " + merged.ok + "/" + merged.total + " ok");

return { message: "parallel fan-out complete (v2 file-handoff)", tag: tag, ok: merged.ok, total: merged.total, results: merged.results };
JSEOF
}

write_ev() {
  cat > "$EV" <<'MDEOF'
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
MDEOF
}

apply() { write_tpl; write_ev; echo "applied: $TPL + $EV"; }

verify() {
  test -f "$TPL" || { echo "missing $TPL"; return 1; }
  test -f "$EV" || { echo "missing $EV"; return 1; }
  grep -q 'parallel-fanout-v2' "$TPL" || return 1
  grep -q 'parallel() return ignored' "$TPL" || return 1
  grep -q 'fanout-<tag>' "$TPL" || return 1
  grep -q 'export const meta' "$TPL" || return 1
  grep -q 'workflow-run-f87c0d71e273419cb127f7ed972045da' "$EV" || return 1
  grep -q 'workflow-run-994de1fc7dc24674bd652593697f11ed' "$EV" || return 1
  if command -v node >/dev/null 2>&1; then
    # Workflow DSL allows top-level return; plain node --check rejects it.
    # Strip the single-line export header and wrap the body in a function.
    python3 - "$TPL" <<'PYEOF'
import sys
src = open(sys.argv[1]).read()
body = "".join(l for l in src.splitlines(keepends=True) if not l.startswith("export const meta"))
open("/tmp/r6a-check.mjs", "w").write("async function __wf_main(){\n" + body + "\n}\n")
print("dsl-wrapped for syntax check")
PYEOF
    node --check /tmp/r6a-check.mjs \
      && echo "node --check: template parses (DSL-wrapped)" || { echo "node --check FAILED"; return 1; }
  else
    echo "node absent: skipped parse check"
  fi
  echo "R6a artifacts verified: template + 5-probe evidence"
}

rollback() {
  tpl0=$(grep '^tpl=' "$SNAP" 2>/dev/null | cut -d= -f2 || echo ABSENT)
  ev0=$(grep '^ev=' "$SNAP" 2>/dev/null | cut -d= -f2 || echo ABSENT)
  if [ "$tpl0" = "ABSENT" ]; then rm -f "$TPL"; fi
  if [ "$ev0" = "ABSENT" ]; then rm -f "$EV"; fi
  rm -f "$SNAP" /tmp/r6a-check.mjs
  echo "rolled back"
}

case "${1:-run}" in
  run) snapshot && apply && (verify || { echo "VERIFY FAILED — rolling back"; rollback; exit 1; }) && echo "R6a PASS" ;;
  rollback) rollback ;;
  *) echo "usage: $0 [run|rollback]"; exit 2 ;;
esac
