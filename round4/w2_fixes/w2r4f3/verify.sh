#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_tools.json"))
assert d["fdfind"]["path"], d
assert d["rg"]["path"], d
print("TOOLS_INVENTORY_OK")
PYEOF
