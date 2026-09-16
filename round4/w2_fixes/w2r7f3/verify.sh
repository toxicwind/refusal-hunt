#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
n = len(open(R + "/spawn_queue.jsonl").read().splitlines())
assert n == 6, n
cfg = json.load(open(R + "/spawn_throttle.json"))
assert cfg["min_interval_s"] in (90, 180), cfg
print("TRIAL_PREP_OK depth=6 throttle=%s" % cfg["min_interval_s"])
PYEOF
