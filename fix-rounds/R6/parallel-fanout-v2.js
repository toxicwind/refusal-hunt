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
