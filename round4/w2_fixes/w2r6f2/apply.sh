#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
rate = json.load(open(R + "/rounds/w2_aggregates.json"))["refusal_rate"]
hot = rate > 0.6
cfg = {"min_interval_s": 180 if hot else 90,
       "max_parallel": 1 if hot else 2,
       "measured_rate": rate,
       "reason": "rate>0.6 hot throttle" if hot else "moderate rate, standard throttle",
       "wave": 2}
json.dump(cfg, open(R + "/spawn_throttle.json", "w"), indent=1)
print("throttle v2:", cfg)
PYEOF
