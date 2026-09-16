#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os, glob
R = os.environ["ROUND4_ROOT"]
rows = []
for p in sorted(glob.glob(R + "/rounds/round*.json")):
    d = json.load(open(p))
    for f in d["fixes"]:
        rows.append((d["round"], f["id"], f["status"], f["ms"]))
h = ["<html><head><title>round4 dashboard</title></head><body>",
     "<h1>8 rounds x 3 fixes - refusal-hunt round4</h1>",
     "<table border=1><tr><th>round</th><th>fix</th><th>status</th><th>ms</th></tr>"]
for r in rows:
    h.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % r)
h.append("</table>")
for name in ["r2_storm.json", "r2_gate.json", "r4_gate_timeline.json",
             "r4_coverage.json", "r7_race.json", "r8_acceptance.json"]:
    p = R + "/rounds/" + name
    if os.path.exists(p):
        h.append("<h2>%s</h2><pre>%s</pre>" % (name, json.dumps(json.load(open(p)), indent=1)))
h.append("</body></html>")
open(R + "/dashboard.html", "w").write("\n".join(h))
print("dashboard rows=%d" % len(rows))
PYEOF
