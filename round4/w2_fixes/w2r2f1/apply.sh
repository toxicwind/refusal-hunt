#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
src = json.load(open(R + "/input/constants.json"))["gate_export"]
rows = json.load(open(os.path.expanduser(src)))["result"]["rows"]
per_job = {}
for r in rows:
    j = r["job_id"]; d = per_job.setdefault(j, {"n": 0, "skipped": 0})
    d["n"] += 1
    if "did not pass the scheduled-task safety review" in (r.get("res") or ""):
        d["skipped"] += 1
n = len(rows); skipped = sum(d["skipped"] for d in per_job.values())
out = {"window_rows": n, "skipped": skipped, "skip_rate": round(skipped / n, 4) if n else 0,
       "per_job": per_job, "first_ts": min(r["scheduled_for_utc"] for r in rows),
       "last_ts": max(r["scheduled_for_utc"] for r in rows)}
json.dump(out, open(R + "/rounds/w2_gate.json", "w"), indent=1)
print("skip_rate=%.4f rows=%d" % (out["skip_rate"], n))
PYEOF
