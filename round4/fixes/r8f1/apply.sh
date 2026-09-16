#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
agg = json.load(open(R + "/input/spawn_aggregates.json"))["by_parent"]
consts = json.load(open(R + "/input/constants.json"))["bars"]
n = sum(r["n"] for r in agg); refused = sum(r["refused"] for r in agg)
rate = 1 - refused / n
out = {"n": n, "refused": refused, "success_rate": round(rate, 4),
       "bar": consts["spawn_success_rate"],
       "verdict": "PASS" if rate >= consts["spawn_success_rate"] else "FAIL",
       "note": "Chris's bar: 'not successful until you can consistently spawn subagents'"}
json.dump(out, open(R + "/rounds/r8_acceptance.json", "w"), indent=1)
print(out)
PYEOF
