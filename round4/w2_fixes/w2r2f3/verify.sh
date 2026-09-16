#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_gate_timeline.json"))
assert d["skip_fraction"] > 0.95, d
assert d["non_skip_count"] <= 2, d
print("TIMELINE_V2_OK", d["skip_fraction"])
PYEOF
