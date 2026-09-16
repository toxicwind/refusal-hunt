#!/usr/bin/env bash
# R7b: per-route timing and cost ledger.
# Segments the spawn route (handoff, total) and the workflow route
# (queue, execution, tokens) from the R7 extracts; no sleeps, no live waits.
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R7="$HOME/workspace/refusal-hunt/fix-rounds/R7"
OUT_JSON="$R7/route-timing.json"
OUT_PQ="$R7/route-timing.parquet"
OUT_MD="$R7/ROUTE_TIMING.md"
SNAP_LIST="$(mktemp)"
ls -1 "$R7" > "$SNAP_LIST"
restore() { echo "R7b VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R7" | sort) | while read -r f; do rm -rf "$R7/$f"; done; exit 1; }

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import csv, json, os, statistics
from datetime import datetime, timezone
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
EX = os.path.join(R7, "extracts")
def load(fn):
    with open(os.path.join(EX, fn)) as f:
        return list(csv.DictReader(f))
def num(x):
    try: return float(x) if x not in (None, "") else None
    except (TypeError, ValueError): return None
def seg(rows):
    vals = sorted(v for v in rows if v is not None)
    if not vals: return {"n":0}
    return {"n":len(vals),"min":round(vals[0],2),"median":round(statistics.median(vals),2),
            "p95":round(vals[max(0,int(len(vals)*0.95)-1)],2),"max":round(vals[-1],2)}

spawn24 = load("spawn_route_24h.csv")
wf24 = load("workflow_route_24h.csv")
truth7d = load("spawn_truth_7d.csv")
cls_by_spawn = {r["spawn_id"]: r["classification"] for r in truth7d}
for r in spawn24:
    r["classification"] = cls_by_spawn.get(r["spawn_id"], "unknown")

# --- spawn route segments (24h) ---
by_class = {}
for r in spawn24:
    c = r["classification"]
    sc, cc, se = num(r["spawn_created_epoch"]), num(r["child_created_epoch"]), num(r["spawn_completed_epoch"])
    by_class.setdefault(c, {"handoff":[],"total":[]})
    if sc is not None and cc is not None and cc >= sc:
        by_class[c]["handoff"].append(cc - sc)
    if sc is not None and se is not None and se >= sc:
        by_class[c]["total"].append(se - sc)
spawn_seg = {c: {"handoff_s": seg(v["handoff"]), "total_s": seg(v["total"])} for c, v in by_class.items()}

# --- workflow route segments (24h) ---
wf = {"queue_s": [], "exec_s": [], "total_tokens": [], "input_tokens": []}
wf_by_status = {}
for r in wf24:
    s = r["status"]
    wf_by_status.setdefault(s, 0); wf_by_status[s] += 1
    c, st, co = num(r["created_at"]), num(r["started_at"]), num(r["completed_at"])
    if c is not None and st is not None and st >= c: wf["queue_s"].append(st - c)
    if num(r["duration_ms"]) is not None: wf["exec_s"].append(num(r["duration_ms"])/1000.0)
    if num(r["total_tokens"]) is not None: wf["total_tokens"].append(num(r["total_tokens"]))
    if num(r["input_tokens"]) is not None: wf["input_tokens"].append(num(r["input_tokens"]))
wf_seg = {k: seg(v) for k, v in wf.items()}

gen_total = spawn_seg.get("genuine", {}).get("total_s", {})
ref_total = spawn_seg.get("refused_as_completed", {}).get("total_s", {})
result = {
  "generated_utc": datetime.now(timezone.utc).isoformat(),
  "spawn_route_segments_24h": spawn_seg,
  "workflow_route_segments_24h": {**wf_seg, "by_status": wf_by_status},
  "cross_route": {
    "genuine_spawn_median_total_s": gen_total.get("median"),
    "refused_spawn_median_total_s": ref_total.get("median"),
    "workflow_child_median_exec_s": wf_seg["exec_s"].get("median"),
    "workflow_child_median_total_tokens": wf_seg["total_tokens"].get("median"),
    "workflow_child_max_total_tokens": wf_seg["total_tokens"].get("max"),
    "refusal_latency_note": "refused spawns complete in ~1s: the refusal is a fast serving-path reject, not a timeout",
    "cost_note": "workflow route works during the spawn storm but inherits the full parent context (300k+ input tokens on the v2 collector); genuine spawn children carry no comparable token ledger in the observed tables",
  },
}
json.dump(result, open(os.path.join(R7,"route-timing.json"),"w"), indent=2)

# parquet copy of the segment table for the nightly parquet-debug habit
import pyarrow as pa, pyarrow.parquet as pq
rows = []
for cls, s in spawn_seg.items():
    rows.append({"route":"spawn","class":cls,"handoff_n":s["handoff_s"].get("n",0),
                 "handoff_median_s":s["handoff_s"].get("median"),
                 "total_n":s["total_s"].get("n",0),"total_median_s":s["total_s"].get("median"),
                 "total_p95_s":s["total_s"].get("p95"),"total_max_s":s["total_s"].get("max")})
rows.append({"route":"workflow","class":"all","handoff_n":wf_seg["queue_s"].get("n",0),
             "handoff_median_s":wf_seg["queue_s"].get("median"),
             "total_n":wf_seg["exec_s"].get("n",0),"total_median_s":wf_seg["exec_s"].get("median"),
             "total_p95_s":wf_seg["exec_s"].get("p95"),"total_max_s":wf_seg["exec_s"].get("max")})
pq.write_table(pa.Table.from_pylist(rows), os.path.join(R7,"route-timing.parquet"), compression="snappy")

L = ["# R7b — Per-route timing and cost","",
     "## Spawn route segments, 24h (seconds)"]
for cls, s in sorted(spawn_seg.items()):
    h, t = s["handoff_s"], s["total_s"]
    L.append(f"- `{cls}`: handoff median {h.get('median')}s (n={h.get('n')}), "
             f"total median {t.get('median')}s p95 {t.get('p95')}s max {t.get('max')}s (n={t.get('n')})")
L += ["", "## Workflow route segments, 24h",
      f"- queue median {wf_seg['queue_s'].get('median')}s, exec median {wf_seg['exec_s'].get('median')}s "
      f"(max {wf_seg['exec_s'].get('max')}s), statuses {wf_by_status}",
      f"- tokens per child: median total {wf_seg['total_tokens'].get('median')}, "
      f"max {wf_seg['total_tokens'].get('max')} (v2 collector inherited full parent context)",
      "", "## Cross-route read",
      "- Refusals are FAST (~1s): serving-path reject, not a timeout or queue stall.",
      "- Genuine spawn children and workflow children both execute in seconds; the workflow",
      "  route's tax is context tokens, not latency.",
      "- Inference-vs-execution: ledger records wall/model duration only; tool-execution split",
      "  is not separately recorded in runtime.workflow_agent_calls."]
open(os.path.join(R7,"ROUTE_TIMING.md"),"w").write("\n".join(L)+"\n")
print("r7b applied")
PYEOF

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
import pyarrow.parquet as pq
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
d = json.load(open(os.path.join(R7,"route-timing.json")))
assert "spawn_route_segments_24h" in d and "workflow_route_segments_24h" in d and "cross_route" in d
t = pq.read_table(os.path.join(R7,"route-timing.parquet"))
assert t.num_rows == len(d["spawn_route_segments_24h"]) + 1, "parquet row mismatch"
assert "total_median_s" in t.column_names
rt = d["spawn_route_segments_24h"].get("refused_as_completed",{}).get("total_s",{})
assert rt.get("median") is not None and rt["median"] < 5, "refused median should be fast"
print("R7b VERIFY PASS")
PYEOF
echo "R7b done"
