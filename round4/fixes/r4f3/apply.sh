#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os, re
R = os.environ["ROUND4_ROOT"]
files = [os.path.expanduser("~/workspace/watchdog-supervisor.sh"),
         os.path.expanduser("~/workspace/service-health-poller.sh")]
out = {}
for p in files:
    hits = []
    if os.path.exists(p):
        for i, line in enumerate(open(p), 1):
            if re.search(r"(?<![a-z_])sleep\s+\d+", line):
                hits.append({"line": i, "text": line.strip()[:120]})
    out[os.path.basename(p)] = hits
json.dump(out, open(R + "/rounds/r4_sleep_audit.json", "w"), indent=1)
print("sleep hits:", {k: len(v) for k, v in out.items()})
PYEOF
