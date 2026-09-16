#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
p = subprocess.run(["fdfind", "-t", "f", "-e", "db", "--exclude", "node_modules",
                    os.path.expanduser("~")],
                   capture_output=True, text=True, timeout=120)
rows = []
total = 0
for line in p.stdout.splitlines():
    try:
        sz = os.path.getsize(line); total += sz
        rows.append({"path": line, "bytes": sz})
    except Exception:
        pass
rows.sort(key=lambda r: -r["bytes"])
out = {"count": len(rows), "total_bytes": total, "top10": rows[:10]}
json.dump(out, open(R + "/rounds/r6_dbsweep.json", "w"), indent=1)
print("db files=%d total_bytes=%d" % (len(rows), total))
PYEOF
