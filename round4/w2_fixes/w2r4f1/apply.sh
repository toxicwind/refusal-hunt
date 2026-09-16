#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
info = subprocess.run(["pip", "show", "nest_asyncio"], capture_output=True, text=True).stdout
ver = loc = "unknown"
for line in info.splitlines():
    if line.startswith("Version:"):
        ver = line.split(":", 1)[1].strip()
    if line.startswith("Location:"):
        loc = line.split(":", 1)[1].strip()
out = {"package": "nest_asyncio", "version": ver, "location": loc,
       "note": "Chris said 'nested_async'; correct PyPI name is nest_asyncio (nested_async/nested-async 404)"}
json.dump(out, open(R + "/rounds/w2_nest.json", "w"), indent=1)
print(out)
PYEOF
