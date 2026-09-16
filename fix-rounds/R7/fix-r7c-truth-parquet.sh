#!/usr/bin/env bash
# R7c: durable parquet truth dataset of 7d spawn classifications.
# Materializes spawn_truth_7d.csv -> spawn-truth.parquet (pyarrow/snappy) plus
# a summary with per-parent rates, per-source rates, and storm windows.
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R7="$HOME/workspace/refusal-hunt/fix-rounds/R7"
OUT_PQ="$R7/spawn-truth.parquet"
OUT_JSON="$R7/spawn-truth-summary.json"
SNAP_LIST="$(mktemp)"
ls -1 "$R7" > "$SNAP_LIST"
restore() { echo "R7c VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R7" | sort) | while read -r f; do rm -rf "$R7/$f"; done; exit 1; }

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import csv, json, os
from datetime import datetime, timezone
import pyarrow as pa, pyarrow.parquet as pq
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
EX = os.path.join(R7, "extracts")
with open(os.path.join(EX, "spawn_truth_7d.csv")) as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 448, f"expected 448 rows, got {len(rows)}"

def iv(x):
    try: return int(x) if x not in (None, "") else None
    except (TypeError, ValueError): return None

pylist = []
for r in rows:
    pylist.append({
        "spawn_id": iv(r["spawn_id"]),
        "parent_agent_id": r["parent_agent_id"],
        "child_agent_id": r["child_agent_id"],
        "created_at": iv(r["created_at"]),
        "completed_at": iv(r["completed_at"]),
        "status": r["status"],
        "requester_source": r["requester_source"],
        "agent_type": r["agent_type"],
        "child_depth": iv(r["child_depth"]),
        "model": r["model"],
        "classification": r["classification"],
    })
table = pa.table({
    "spawn_id": pa.array([p["spawn_id"] for p in pylist], type=pa.int64()),
    "parent_agent_id": pa.array([p["parent_agent_id"] for p in pylist], type=pa.string()),
    "child_agent_id": pa.array([p["child_agent_id"] for p in pylist], type=pa.string()),
    "created_at": pa.array([p["created_at"] for p in pylist], type=pa.int64()),
    "completed_at": pa.array([p["completed_at"] for p in pylist], type=pa.int64()),
    "status": pa.array([p["status"] for p in pylist], type=pa.string()),
    "requester_source": pa.array([p["requester_source"] for p in pylist], type=pa.string()),
    "child_depth": pa.array([p["child_depth"] for p in pylist], type=pa.int64()),
    "model": pa.array([p["model"] for p in pylist], type=pa.string()),
    "classification": pa.array([p["classification"] for p in pylist], type=pa.string()),
})
pq.write_table(table, os.path.join(R7, "spawn-truth.parquet"), compression="snappy")

# summary
from collections import Counter, defaultdict
cls_counts = Counter(p["classification"] for p in pylist)
src = defaultdict(Counter)
for p in pylist: src[p["requester_source"] or "NULL"][p["classification"]] += 1
src_rates = {s: {"total": sum(c.values()), "refused": c["refused_as_completed"],
                 "rate": round(c["refused_as_completed"]/sum(c.values()), 4)} for s, c in src.items()}
par = defaultdict(Counter)
for p in pylist: par[(p["parent_agent_id"] or "NULL")[:8]][p["classification"]] += 1
top_parents = sorted(par.items(), key=lambda kv: -kv[1]["refused_as_completed"])[:12]
top_parents = [{"parent": k, "total": sum(v.values()), "refused": v["refused_as_completed"],
                "rate": round(v["refused_as_completed"]/sum(v.values()), 4)} for k, v in top_parents]
# storm windows: refusals per UTC hour
hours = Counter()
for p in pylist:
    if p["classification"] == "refused_as_completed" and p["created_at"]:
        h = datetime.fromtimestamp(p["created_at"], tz=timezone.utc).strftime("%Y-%m-%dT%H")
        hours[h] += 1
top_hours = sorted(hours.items(), key=lambda kv: -kv[1])[:8]
summary = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "rows": len(pylist),
    "spawn_id_range": [min(p["spawn_id"] for p in pylist), max(p["spawn_id"] for p in pylist)],
    "classification_counts": dict(cls_counts),
    "refusal_rate_by_requester_source": src_rates,
    "top_refusing_parents": top_parents,
    "top_refusal_hours_utc": [{"hour": h, "refusals": n} for h, n in top_hours],
    "provenance": "agent.subagent_spawns 7d window, md5(final_response) classified; "
                  "pages 1-2 via db tool saved JSON, page 3 (spawns 404-451) narrow-query verified "
                  "against transcription; gaps at spawn_ids 228,229,232 predate window or deleted",
    "schema": [f.name for f in table.schema],
}
json.dump(summary, open(os.path.join(R7, "spawn-truth-summary.json"), "w"), indent=2)
print("r7c applied: spawn-truth.parquet + summary")
PYEOF

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
import pyarrow.parquet as pq
from collections import Counter
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
t = pq.read_table(os.path.join(R7, "spawn-truth.parquet"))
assert t.num_rows == 448, f"parquet rows {t.num_rows} != 448"
need = {"spawn_id","parent_agent_id","child_agent_id","created_at","completed_at",
        "status","requester_source","child_depth","model","classification"}
assert need <= set(t.column_names), f"schema missing: {need - set(t.column_names)}"
s = json.load(open(os.path.join(R7, "spawn-truth-summary.json")))
assert s["rows"] == 448
cc = Counter(t.column("classification").to_pylist())
assert sum(cc.values()) == 448
for k, v in s["classification_counts"].items():
    assert cc[k] == v, f"summary/parquet mismatch on {k}"
assert len(set(t.column("spawn_id").to_pylist())) == 448, "dup spawn_id in parquet"
print("R7c VERIFY PASS")
PYEOF
echo "R7c done"
