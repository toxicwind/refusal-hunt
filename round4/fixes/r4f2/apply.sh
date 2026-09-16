#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
src = json.load(open(R + "/input/constants.json"))["gate_export"]
rows = json.load(open(os.path.expanduser(src)))["result"]["rows"]
non_skip = [r for r in rows if "did not pass the scheduled-task safety review" not in (r.get("res") or "")]
first = min(r["scheduled_for_utc"] for r in rows)
last = max(r["scheduled_for_utc"] for r in rows)
out = {"continuous_skip": len(non_skip) == 0,
       "non_skip_count": len(non_skip),
       "first_ts": first, "last_ts": last,
       "duration_h": round((last - first) / 3600, 2),
       "window_rows": len(rows)}
json.dump(out, open(R + "/rounds/r4_gate_timeline.json", "w"), indent=1)
print("timeline:", out)
PYEOF
