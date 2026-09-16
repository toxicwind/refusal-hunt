#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
agg = json.load(open(R + "/rounds/w2_aggregates.json"))
rate = 1 - agg["refused"] / agg["n"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
last10 = rows[-10:]
CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
ref10 = sum(1 for r in last10 if r["fr_md5"] == CANNED)
out = {"n": agg["n"], "refused": agg["refused"], "success_rate": round(rate, 4),
       "bar": 0.9, "verdict": "PASS" if rate >= 0.9 else "FAIL",
       "recent10": {"n": 10, "refused": ref10, "success_rate": round(1 - ref10 / 10, 4),
                    "sids": [r["sid"] for r in last10]},
       "note": "Chris's bar: 'not successful until you can consistently spawn subagents'"}
json.dump(out, open(R + "/rounds/w2_acceptance.json", "w"), indent=1)
print(out)
PYEOF
