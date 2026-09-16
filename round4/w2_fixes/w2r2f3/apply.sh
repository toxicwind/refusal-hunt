#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
src = json.load(open(R + "/input/constants.json"))["gate_export"]
rows = json.load(open(os.path.expanduser(src)))["result"]["rows"]
non_skip = [r for r in rows if "did not pass the scheduled-task safety review" not in (r.get("res") or "")]
n = len(rows)
out = {"skip_fraction": round(1 - len(non_skip) / n, 4),
       "non_skip_count": len(non_skip),
       "non_skip_jobs": sorted(set(r["job_id"] for r in non_skip)),
       "first_ts": min(r["scheduled_for_utc"] for r in rows),
       "last_ts": max(r["scheduled_for_utc"] for r in rows),
       "window_rows": n}
json.dump(out, open(R + "/rounds/w2_gate_timeline.json", "w"), indent=1)
print(out)
PYEOF
