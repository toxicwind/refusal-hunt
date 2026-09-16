#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
fixes = []
for l in open(R + "/rounds_results.jsonl"):
    d = json.loads(l)
    if d.get("wave") == 2 and d.get("id") and d.get("status"):
        fixes.append(d)
# dedupe by id: reruns supersede earlier attempts, latest row wins
latest = {}
for f in fixes:
    latest[f["id"]] = f
fixes = list(latest.values())
rounds = {}
for f in fixes:
    rounds.setdefault(f["round"], []).append(f["status"])
out = {"fixes": len(fixes),
       "by_round": {str(k): {"pass": v.count("pass"), "rolled_back": v.count("rolled_back"),
                             "skipped": v.count("skipped"), "blocked": v.count("blocked")}
                    for k, v in sorted(rounds.items())},
       "totals": {s: sum(1 for f in fixes if f["status"] == s)
                  for s in ("pass", "rolled_back", "skipped", "blocked")}}
json.dump(out, open(R + "/rounds/w2_summary.json", "w"), indent=1)
print(out)
PYEOF
