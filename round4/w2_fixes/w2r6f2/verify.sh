#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
rate = json.load(open(R + "/rounds/w2_aggregates.json"))["refusal_rate"]
cfg = json.load(open(R + "/spawn_throttle.json"))
want = 180 if rate > 0.6 else 90
assert cfg["min_interval_s"] == want, (cfg, rate)
assert cfg["wave"] == 2
print("THROTTLE_V2_OK", cfg)
PYEOF
