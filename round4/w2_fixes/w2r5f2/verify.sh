#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_jarvis_catalog.json"))
tc = d["vars"].get("JARVIS_TRACE_CONTEXT")
assert tc and isinstance(tc["keys"], list) and "agent_id" in tc["keys"], d
print("JARVIS_CATALOG_OK", len(d["vars"]), "vars")
PYEOF
