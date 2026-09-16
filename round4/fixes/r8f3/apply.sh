#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
sums = []
for line in open(R + "/rounds_results.jsonl"):
    d = json.loads(line)
    if d.get("type") == "round_summary":
        sums.append(d)
with open(R + "/ROUNDS_SUMMARY.md", "a") as md:
    md.write("\n## 8-round recursive fix run - 2026-09-16\n")
    md.write("Every command wrapped: unshare --user --map-root-user --mount (root in ns).\n\n")
    for s in sorted(sums, key=lambda x: x["round"]):
        md.write("- round%d: pass=%d rolled_back=%d skipped=%d (%dms)\n"
                 % (s["round"], s["pass"], s["rolled_back"], s["skipped"], s["round_ms"]))
    md.write("\nNext iterations: live 6-spawn acceptance trial; gate-clear detector; "
             "feed autonomy blocked on DB reachability from supervisor (muse.db is operator-only).\n")
print("runbook appended")
PYEOF
