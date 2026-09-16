#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
agg = json.load(open(R + "/rounds/w2_aggregates.json"))
assert agg["n"] == len(rows) == 127, agg["n"]
assert sum(p["n"] for p in agg["by_parent"]) == 127
assert agg["refused"] == sum(1 for r in rows if r["fr_md5"] == "b4aefd29108f232f9c0d5a4b030215c1")
print("AGGREGATES_OK refused=%d rate=%.4f" % (agg["refused"], agg["refusal_rate"]))
PYEOF
