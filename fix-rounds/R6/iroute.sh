#!/usr/bin/env bash
# iroute <parent_agent_id> -> prints refusal rate from identity-router.json, or UNKNOWN
set -u
J=~/workspace/refusal-hunt/fix-rounds/R6/identity-router.json
python3 - "$J" "${1:-}" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1])); want = sys.argv[2]
for p in d["by_parent"]:
    if p["parent"] == want or p["parent"].startswith(want):
        print("refusal_rate=%.3f total=%d refused=%d" % (p["rate"], p["total"], p["refused"]))
        sys.exit(0)
print("UNKNOWN")
PYEOF
