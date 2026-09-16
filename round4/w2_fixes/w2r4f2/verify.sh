#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_race.json"))
assert d["classes_agree"] is True, d
assert d["speedup"] > 1.5, d
print("RACE_V2_OK speedup=%.2f" % d["speedup"])
PYEOF
