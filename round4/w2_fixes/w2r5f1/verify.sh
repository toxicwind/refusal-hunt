#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_hatch_surface.json"))
assert d["verdict"] == "hatch_daemon_surface_unreachable_from_cell", d
assert "listeners" in d["evidence"], d
print("HATCH_SURFACE_OK")
PYEOF
