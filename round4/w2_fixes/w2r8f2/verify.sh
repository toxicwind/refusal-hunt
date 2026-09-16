#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_rollback_audit.json"))
assert d["clean"] is True, d["residues"]
print("ROLLBACK_AUDIT_OK clean")
PYEOF
