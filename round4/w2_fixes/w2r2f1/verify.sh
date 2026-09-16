#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
d = json.load(open(R + "/rounds/w2_gate.json"))
assert d["skip_rate"] > 0.8, d
assert d["last_ts"] - d["first_ts"] > 300, d
assert d["window_rows"] >= 50, d
print("GATE_QUANT_V2_OK", d["skip_rate"])
PYEOF
