#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_acceptance.json"))
assert d["verdict"] in ("PASS", "FAIL"), d
assert d["recent10"]["n"] == 10
print("ACCEPTANCE", d["verdict"], "overall=%.4f recent10=%.4f" % (d["success_rate"], d["recent10"]["success_rate"]))
PYEOF
