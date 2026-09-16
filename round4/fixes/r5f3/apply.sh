#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
links = {
    "canary-feed.sh": "~/workspace/refusal-hunt/canary-feed.sh",
    "bridge-xfer": "~/workspace/skills/awrawr-mcp/bin/xfer.py",
    "bridge-exec": "~/workspace/skills/awrawr-mcp/bin/exec.py",
    "spawn_guard": "~/workspace/refusal-hunt/round3/spawn_guard.py",
    "supervisor": "~/workspace/watchdog-supervisor.sh",
}
out = {}
for name, p in links.items():
    p = os.path.expanduser(p)
    out[name] = {"exists": os.path.exists(p), "executable": os.access(p, os.X_OK)}
json.dump(out, open(R + "/rounds/r5_chain.json", "w"), indent=1)
print(json.dumps(out, indent=1))
PYEOF
