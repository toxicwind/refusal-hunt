#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
agg = json.load(open(R + "/input/spawn_aggregates.json"))["by_parent"]
n = sum(r["n"] for r in agg); refused = sum(r["refused"] for r in agg)
rate = refused / n if n else 0
per_parent = {r["parent"][:8]: {"n": r["n"], "refused": r["refused"],
              "rate": round(r["refused"]/r["n"], 3)} for r in agg}
out = {"window": "spawn_id>312", "n": n, "refused": refused,
       "overall_rate": round(rate, 4), "storm_active": rate > 0.25,
       "per_parent": per_parent,
       "max_parent": max(per_parent.items(), key=lambda kv: kv[1]["rate"])[0]}
json.dump(out, open(R + "/rounds/r2_storm.json", "w"), indent=1)
print("storm_rate=%.4f n=%d" % (rate, n))
PYEOF
